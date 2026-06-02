"""Simultaneous multi-asset long/short portfolio construction (ADR-0020 orchestrator).

Unions K independent directional signals across multiple assets into ONE
concurrently-held book, joint-Kelly-sized (long/short via signed returns), with
per-instrument gross caps (ADR-0001 retail capacity + ADR-0017 §5 K-5
correlated-instrument budgets). This is the SIMULTANEOUS-portfolio paradigm —
hold many de-correlated bets at once so the realized path converges toward the
ensemble (the Peters & Adamou 2022 pooling lift, ADR-0029 §D-3.4) — complementary
to the SWITCHING meta-allocation (MPV2, which picks one arm per session).

Long/short is encoded in the RETURN stream, not in a signed fraction: a short bet
on asset j is `signal × asset_return_j` with signal = −1, so a profitable short
shows a POSITIVE directional return and `joint_kelly_fractions` (long-only on the
already-directional streams) allocates to it. No sizing-primitive change needed;
this reuses the audited `skie_ninja.sizing.ergodicity.joint_kelly_fractions`.

Primary citations:
- Kelly, J.L. 1956. Bell System Technical Journal 35(4):917-926. DOI
  10.1002/j.1538-7305.1956.tb03809.x (joint simultaneous-bet sizing).
- Peters, O. & Adamou, A. 2022. Phil. Trans. R. Soc. A 380(2227):20200425. DOI
  10.1098/rsta.2020.0425 (pooling de-correlated arms raises time-average growth).
- Grinold, R.C. 1989. J. Portfolio Management 15(3):30-37. DOI
  10.3905/jpm.1989.409211 (IR ≈ IC·√breadth — the breadth value of more bets).
- DeMiguel, Garlappi, Uppal 2009. Review of Financial Studies 22(5):1915-1953.
  DOI 10.1093/rfs/hhm075 (1/N benchmark).

Implementation per `P1-META-PORTFOLIO-ORCHESTRATOR-IMPL` (ADR-0020). The long/short
multi-asset extension of the arm-weighting framing is tracked under
`P1-ADR-0020-LONG-SHORT-MULTI-ASSET-AMENDMENT`. v2 refinements: simultaneous long/short
NETTING on the same instrument (vs the v1 gross-per-instrument cap)
`P1-PORTFOLIO-NET-LONG-SHORT-V2`; per-instrument caps INSIDE the joint-Kelly solve (vs
the v1 post-hoc throttle) `P1-PORTFOLIO-CONSTRAINED-JOINT-KELLY-V2`; continuous-conviction
signal semantics `P1-PORTFOLIO-CONTINUOUS-SIGNAL-CONVICTION`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from skie_ninja.sizing.ergodicity import joint_kelly_fractions

__all__ = [
    "PortfolioResult",
    "cap_by_instrument",
    "construct_portfolio",
    "directional_returns",
]

logger = logging.getLogger(__name__)

_LOG_ARG_FLOOR = 1e-9  # keep the book log-growth finite at 1 + r → 0
_REQUIRED_NDIM = 2


def directional_returns(
    signals: npt.ArrayLike,
    asset_returns: npt.ArrayLike,
) -> np.ndarray:
    """Union independent per-bet signals with asset returns (the long/short step).

    Element-wise `signal × asset_return`: a long bet (signal > 0) passes the asset
    return through; a short bet (signal < 0) negates it (a profitable short → a
    positive directional return); a flat bet (signal = 0) contributes 0.

    Args:
        signals: (T, K) per-bet per-session position direction. The SIGN encodes
            long (>0) / short (<0) / flat (0). **v1 recommends sign-only signals
            ({-1, 0, +1})**: conviction sizing is joint-Kelly's job (the fraction f),
            so a continuous magnitude here is a pre-Kelly leverage tilt Kelly partially
            re-optimizes — NOT a clean conviction weight (F-1-1 audit; continuous
            semantics tracked as `P1-PORTFOLIO-CONTINUOUS-SIGNAL-CONVICTION`). NOT
            clipped — the caller controls the convention.
        asset_returns: (T, K) per-bet per-session simple asset returns; must align
            with `signals`.

    Returns:
        (T, K) directional realized returns = signals * asset_returns.

    Raises:
        ValueError: if signals and asset_returns shapes differ or are not 2-D.
    """
    s = np.asarray(signals, dtype=float)
    r = np.asarray(asset_returns, dtype=float)
    if s.ndim != _REQUIRED_NDIM or r.ndim != _REQUIRED_NDIM:
        raise ValueError(f"signals and asset_returns must be 2-D (T, K); got {s.ndim}D, {r.ndim}D.")
    if s.shape != r.shape:
        raise ValueError(f"shape mismatch: signals {s.shape} != asset_returns {r.shape}.")
    return s * r


def cap_by_instrument(
    fractions: np.ndarray,
    instrument_ids: list[str],
    per_instrument_cap: float | dict[str, float],
) -> tuple[np.ndarray, dict[str, float], bool]:
    """Scale down per-instrument gross fractions exceeding the capacity cap.

    Each instrument's gross allocation = sum of its bets' fractions. When that
    exceeds the instrument's cap (ADR-0001 retail capacity / ADR-0017 §5 K-5
    correlated-instrument budget), all of that instrument's bets are scaled by
    cap/gross so the instrument total equals the cap (proportional throttle).

    The cap is on GROSS exposure (sum of bet fractions, all >= 0); since gross >= |net|,
    it is CONSERVATIVE — capacity is never under-stated (offsetting long/short arms on
    one instrument consume gross budget they don't net-use; true netting is
    `P1-PORTFOLIO-NET-LONG-SHORT-V2`). The cap is enforced in BANKROLL-FRACTION space,
    which equals the ADR-0017 §5.2 $-notional K-5 cap iff the input fractions are
    bankroll-notional-normalized (the joint-Kelly fractions are); the caller passes the
    fraction-space equivalent of the §5.2 notional cap.

    Args:
        fractions: (K,) joint-Kelly gross fractions (>= 0).
        instrument_ids: length-K instrument label per bet (bets sharing a label
            share a capacity budget — e.g. an ES-long and an ES-short bet, or
            CL + MCL per the K-5 correlated-pair taxonomy).
        per_instrument_cap: a single float applied to every instrument, or a dict
            {instrument_id: cap}; missing dict keys are uncapped.

    Returns:
        (capped_fractions, per_instrument_gross_after, any_cap_bound).

    Raises:
        ValueError: if len(instrument_ids) != len(fractions), or a cap is <= 0.
    """
    f = np.asarray(fractions, dtype=float).copy()
    if len(instrument_ids) != f.size:
        raise ValueError(f"instrument_ids length {len(instrument_ids)} != fractions {f.size}.")
    groups: dict[str, list[int]] = {}
    for i, inst in enumerate(instrument_ids):
        groups.setdefault(inst, []).append(i)
    any_bound = False
    for inst, idx in groups.items():
        # CR-1 audit: test against dict so an int / np.floating scalar cap is treated
        # as a uniform cap (isinstance(5, float) is False → would crash on .get()).
        cap = (
            per_instrument_cap.get(inst)
            if isinstance(per_instrument_cap, dict)
            else per_instrument_cap
        )
        if cap is None:
            continue
        if cap <= 0.0:
            raise ValueError(f"per_instrument_cap for {inst} must be > 0, got {cap}.")
        gross = float(f[idx].sum())
        if gross > cap:
            f[idx] *= cap / gross
            any_bound = True
    per_instrument_gross = {inst: float(f[idx].sum()) for inst, idx in groups.items()}
    return f, per_instrument_gross, any_bound


@dataclass(frozen=True)
class PortfolioResult:
    """Constructed simultaneous multi-asset book.

    Attributes:
        fractions: (K,) per-bet gross bankroll fractions (joint-Kelly, post per-
            instrument cap). The bet's long/short direction lives in its
            directional-return stream, not in the sign of the fraction.
        portfolio_returns: (T,) realized per-session book return = directional @ f.
        gross_exposure: sum(fractions) — total bankroll deployed across the book.
        per_instrument_gross: {instrument_id: summed gross fraction} (empty if no
            instrument_ids supplied).
        growth_rate: time-average (log) growth of the book per session — the
            ergodicity-relevant headline (ADR-0029 §D-3.1), NOT the ensemble mean.
            -inf if the book wipes out on any session; under an active per-instrument
            cap it is a LOWER BOUND on the constrained-optimal growth (post-hoc
            throttle, not a constrained joint-Kelly solve — F-1-3 audit).
        instrument_capped: True if any per-instrument cap bound (⇒ growth_rate is the
            post-hoc-capped lower bound, not the constrained optimum).
        converged: joint-Kelly optimizer convergence; False ⇒ fractions are all zero.
        bankrupts_on_path: True if min_t(1 + book_return) <= 0 (growth_rate then -inf).
        n_bets: K. n_periods: T.
    """

    fractions: np.ndarray
    portfolio_returns: np.ndarray
    gross_exposure: float
    per_instrument_gross: dict[str, float]
    growth_rate: float
    instrument_capped: bool
    converged: bool
    bankrupts_on_path: bool
    n_bets: int
    n_periods: int


def construct_portfolio(
    directional_return_matrix: npt.ArrayLike,
    *,
    total_exposure_cap: float = 1.0,
    per_bet_cap: float | None = None,
    instrument_ids: list[str] | None = None,
    per_instrument_cap: float | dict[str, float] | None = None,
) -> PortfolioResult:
    """Construct a joint-Kelly-sized simultaneous multi-asset long/short book.

    Pipeline: joint-Kelly-size the K directional-return streams (long/short already
    encoded in their signs) under a hard total-exposure cap → optionally throttle
    per-instrument gross to the capacity cap → realize the per-session book return.

    Args:
        directional_return_matrix: (T, K) directional realized returns (use
            `directional_returns(signals, asset_returns)` to build it).
        total_exposure_cap: cap on the sum of bet fractions (default 1.0 = full-
            Kelly total, the promotable ceiling per ADR-0029 §D-3.2).
        per_bet_cap: optional per-bet fraction cap (joint-Kelly per_arm_cap).
        instrument_ids: optional length-K instrument label per bet, for per-
            instrument capacity capping.
        per_instrument_cap: required iff instrument_ids is supplied — a float (one
            cap for all) or a {instrument_id: cap} dict.

    Returns:
        PortfolioResult.

    Raises:
        ValueError: if the matrix is not 2-D with K >= 1, or instrument_ids is
            supplied without per_instrument_cap (or with a length mismatch).
    """
    dr = np.asarray(directional_return_matrix, dtype=float)
    if dr.ndim != _REQUIRED_NDIM:
        raise ValueError(f"directional_return_matrix must be 2-D (T, K); got {dr.ndim}D.")
    t_periods, k_bets = dr.shape
    if k_bets < 1:
        raise ValueError(f"directional_return_matrix needs K >= 1 bets; got shape {dr.shape}.")
    if instrument_ids is not None and per_instrument_cap is None:
        raise ValueError("per_instrument_cap is required when instrument_ids is supplied.")

    jk = joint_kelly_fractions(dr, total_exposure_cap=total_exposure_cap, per_arm_cap=per_bet_cap)
    if not jk.converged:
        logger.warning("joint-Kelly did not converge; book fractions are zero.")
    fractions = jk.fractions.copy()

    per_instrument_gross: dict[str, float] = {}
    instrument_capped = False
    if instrument_ids is not None:
        # NOTE F-1-3 audit: this is a POST-HOC proportional throttle, not a constrained
        # joint-Kelly solve — freed capacity is NOT reallocated to un-capped instruments,
        # so under an active cap the book is growth-suboptimal vs the constrained optimum
        # (growth_rate is then a lower bound; see module docstring + the v2 follow-up).
        fractions, per_instrument_gross, instrument_capped = cap_by_instrument(
            fractions, instrument_ids, per_instrument_cap
        )

    portfolio_returns = dr @ fractions
    # F-1-2 audit: a book that wipes out on any in-sample session has true time-average
    # growth -inf; the _LOG_ARG_FLOOR would otherwise report a finite, positively-biased
    # value (mirrors the ergodicity.py joint-Kelly guard). Capping only scales groups
    # DOWN so it cannot introduce ruin, but a user total_exposure_cap > 1 can.
    bankrupts_on_path = bool(np.min(1.0 + portfolio_returns) <= 0.0)
    growth_rate = (
        float("-inf")
        if bankrupts_on_path
        else float(np.mean(np.log(np.maximum(1.0 + portfolio_returns, _LOG_ARG_FLOOR))))
    )
    return PortfolioResult(
        fractions=fractions,
        portfolio_returns=portfolio_returns,
        gross_exposure=float(fractions.sum()),
        per_instrument_gross=per_instrument_gross,
        growth_rate=growth_rate,
        instrument_capped=instrument_capped,
        converged=bool(jk.converged),
        bankrupts_on_path=bankrupts_on_path,
        n_bets=k_bets,
        n_periods=t_periods,
    )
