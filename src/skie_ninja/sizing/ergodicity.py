"""Ergodicity-sanctioned sizing primitives — CPPI floor-ratchet + joint-Kelly.

Per ADR-0029 §D-3 (Thrust 2), these are the path-dependence mitigation levers
that resolve the super-Kelly lucky/unlucky problem. Ergodicity economics (Peters
2019 Nature Physics 15(12):1216-1221 DOI 10.1038/s41567-019-0732-0; Peters &
Gell-Mann 2016 Chaos 26(2):023103 DOI 10.1063/1.4940236) shows multiplicative
wealth is non-ergodic — the ensemble mean is NOT the time-average a single
operator experiences, and super-Kelly *reduces* the time-average growth while
inflating the ensemble mean. The route to durable aggressive upside is therefore
NOT higher leverage but (a) protecting the cushion above a ratcheting floor and
(b) splitting capital across concurrent de-correlated arms whose pooled P&L pulls
the realized path toward the ensemble.

1. CPPI floor-ratchet (Black & Jones 1987 J Portfolio Management 14(1):48-51 DOI
   10.3905/jpm.1987.409131; rigorous-frictions treatment Black & Perold 1992 J
   Economic Dynamics & Control 16(3-4):403-426 DOI 10.1016/0165-1889(92)90043-E;
   continuous cushion-proportional parent Grossman & Zhou 1993 Mathematical
   Finance 3(3):241-276 DOI 10.1111/j.1467-9965.1993.tb00044.x): risky exposure =
   multiplier × (equity − floor), with the floor ratcheted to a fraction of the
   running peak (locks in gains on new highs). Exposure → 0 as equity → floor.
   Black-Perold show the floor can gap through under discrete trading, so the
   floor is buffered above the ADR-0017 §4.2 ruin line via `min_floor`.

2. Joint simultaneous-bet Kelly (Kelly 1956 Bell System Technical Journal
   35(4):917-926 DOI 10.1002/j.1538-7305.1956.tb03809.x; Thorp chapters in
   MacLean-Thorp-Ziemba 2011 DOI 10.1142/7598): when M arms signal concurrently,
   the joint log-growth-optimal fractions are smaller than the standalone Kelly
   fractions and the total exposure is well below the naive sum — naive
   summation over-bets and re-introduces ruin. The pooled-arm variance reduction
   is the Peters & Adamou 2022 (Phil Trans R Soc A 380(2227):20200425 DOI
   10.1098/rsta.2020.0425) time-average-growth lift, conditional on the arms
   being de-correlated (gated by the cross-arm correlation matrix,
   `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE`).

All thresholds (CPPI floor_fraction + multiplier, joint-Kelly total-exposure cap)
are project-operational defaults flagged for empirical calibration on a pre-OOS
holdout per the no-magic-number rule (CLAUDE.md §"Parameter & Prompt Selection").

Implementation per `P1-CPPI-FLOOR-RATCHET-SIZING-PRIMITIVE` +
`P1-JOINT-KELLY-CONCURRENT-SIZING-PRIMITIVE` (ADR-0029 §D-3; Phase P buildout P-3).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy.optimize import minimize

__all__ = [
    "CPPIConfig",
    "CPPIResult",
    "JointKellyResult",
    "cppi_risk_overlay",
    "joint_kelly_fractions",
]

# Numerical floor keeping the log-growth argument positive at 1 + R @ f → 0.
_LOG_ARG_FLOOR = 1e-9
_REQUIRED_NDIM = 2  # returns_matrix must be (T, M)
_MIN_PERIODS = 2  # minimum rows for a per-period log-growth estimate
_RUIN_EPSILON = 1e-6  # min per-period gross 1 + R·f; no-ruin feasibility floor (F-1-1 audit)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CPPIConfig:
    """Constant-proportion-portfolio-insurance floor-ratchet configuration.

    Defaults are project-operational and calibration-pending (the buffer + m are
    set on a holdout per Black-Perold 1992's discrete-trade gap-through analysis):
    floor_fraction 0.80 locks in 80% of the running peak; multiplier 4.0 is the
    midpoint of the canonical CPPI m ∈ [3, 6] practitioner range. Calibration
    follow-up: `P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION`.
    """

    floor_fraction: float = 0.80  # justify: lock in 80% of peak; calibrate (see class docstring)
    multiplier: float = 4.0  # justify: CPPI m midpoint of [3,6]; calibrate (see class docstring)

    def __post_init__(self) -> None:
        if not (0.0 <= self.floor_fraction < 1.0):
            raise ValueError(f"floor_fraction must be in [0, 1), got {self.floor_fraction}.")
        if self.multiplier <= 0.0:
            raise ValueError(f"multiplier must be > 0, got {self.multiplier}.")


@dataclass(frozen=True)
class CPPIResult:
    """CPPI floor-ratchet sizing overlay at the current equity / running peak.

    Attributes:
        floor: The ratcheting protected floor (dollars) = max(floor_fraction ×
            running_peak, min_floor).
        cushion: max(0, equity − floor) (dollars).
        exposure_dollars: multiplier × cushion (the CPPI risky-exposure ceiling).
        sizing_scale: exposure_dollars / equity clipped to [0, 1] — a multiplicative
            de-risk factor for the closed loop (→ 0 as equity → floor). At a fresh
            peak it equals min(1, multiplier · (1 − floor_fraction)), reaching the
            1.0 cap only when multiplier >= 1/(1 − floor_fraction); under the
            defaults (m=4, floor_fraction=0.8) a fresh-peak scale is 0.8, not 1.0.
            Compose with the early-warning de-risk and the joint-Kelly fraction at
            the position-sizing layer.
    """

    floor: float
    cushion: float
    exposure_dollars: float
    sizing_scale: float


def cppi_risk_overlay(
    equity: float,
    running_peak_equity: float,
    config: CPPIConfig | None = None,
    *,
    min_floor: float | None = None,
) -> CPPIResult:
    """CPPI cushion-proportional sizing overlay with a peak-ratcheting floor.

    Args:
        equity: Current account equity (dollars; > 0).
        running_peak_equity: Highest equity observed to date (dollars; >= equity
            is typical but not required — a fresh peak equals current equity).
        config: CPPIConfig; defaults to project-operational defaults.
        min_floor: Optional absolute floor (dollars) the ratcheting floor may not
            fall below — set to a buffer above the ADR-0017 §4.2 ruin line (the
            project-canonical ruin threshold is 50% of starting bankroll per
            risk_of_ruin.py, so a recommended min_floor ≈ 0.55 × starting_equity)
            to absorb discrete-trade gap-through (Black-Perold 1992). When None the
            gap-through protection is OFF and only the ratcheting floor applies.

    Returns:
        CPPIResult with floor, cushion, exposure_dollars, and the [0, 1] sizing_scale.

    Raises:
        ValueError: if equity <= 0, running_peak_equity <= 0, or min_floor < 0.
    """
    cfg = config if config is not None else CPPIConfig()
    if equity <= 0.0:
        raise ValueError(f"equity must be positive, got {equity}.")
    if running_peak_equity <= 0.0:
        raise ValueError(f"running_peak_equity must be positive, got {running_peak_equity}.")
    if min_floor is not None and min_floor < 0.0:
        raise ValueError(f"min_floor must be non-negative, got {min_floor}.")

    floor = cfg.floor_fraction * float(running_peak_equity)
    if min_floor is not None:
        floor = max(floor, float(min_floor))
    cushion = max(0.0, float(equity) - floor)
    exposure_dollars = cfg.multiplier * cushion
    sizing_scale = min(1.0, exposure_dollars / float(equity))
    return CPPIResult(
        floor=floor,
        cushion=cushion,
        exposure_dollars=exposure_dollars,
        sizing_scale=sizing_scale,
    )


@dataclass(frozen=True)
class JointKellyResult:
    """Joint simultaneous-bet Kelly fractions across M concurrent arms.

    Attributes:
        fractions: 1-D array (M,) of per-arm log-growth-optimal bankroll fractions,
            each >= 0, summing to <= total_exposure_cap.
        total_fraction: sum(fractions).
        standalone_fractions: 1-D array (M,) of each arm's own single-arm Kelly
            fraction (capped at total_exposure_cap), for the over-bet diagnostic.
        sum_standalone_fractions: sum(standalone_fractions) — the naive sum the
            joint solution stays below for positively-correlated / independent arms.
        growth_rate: The joint log-growth rate G(f*) = mean log(1 + R @ f*) at the
            optimum (per-period; the time-average growth being maximized).
        total_exposure_cap: The cap on sum(fractions) that was enforced.
        n_arms: M.
        n_periods: T (rows of the returns matrix).
        converged: Whether the optimizer reported success.
        bankrupts_on_path: True if min_t(1 + R_t · f*) <= 0 — the position wipes out
            on at least one in-sample period, so the true time-average growth is
            -inf (growth_rate is then set to -inf). The no-ruin feasibility
            constraint should prevent this; the field is a safety annotation.
    """

    fractions: np.ndarray
    total_fraction: float
    standalone_fractions: np.ndarray
    sum_standalone_fractions: float
    growth_rate: float
    total_exposure_cap: float
    n_arms: int
    n_periods: int
    converged: bool
    bankrupts_on_path: bool


def _neg_log_growth(f: np.ndarray, returns_matrix: np.ndarray) -> float:
    """Negative per-period joint log-growth -(1/T) Σ_t log(1 + R_t · f).

    The objective both optimizers minimize; `growth_rate` negates it. The
    `_LOG_ARG_FLOOR` clamp keeps the value finite as 1 + R·f → 0 INSIDE the
    feasible set — it is a numerical guard, NOT a barrier substitute (no-ruin
    feasibility is enforced by the caller's constraint per the F-1-1 audit).
    """
    gross = np.maximum(1.0 + returns_matrix @ f, _LOG_ARG_FLOOR)
    return -float(np.mean(np.log(gross)))


def _single_arm_kelly(returns: np.ndarray, cap: float) -> float:
    """Single-arm Kelly fraction on a returns series, bounded to the no-ruin region.

    Maximizes mean(log(1 + f · r)) over f ∈ [0, f_upper] where f_upper = min(cap,
    (1 − _RUIN_EPSILON)/|min(r)|) keeps every period's gross positive (mirrors the
    f_upper = 1/|min(R)| constraint of `kelly_fraction_from_r_multiples`). Returns 0
    when the edge is non-positive (G'(0) = mean(r) <= 0 → f* = 0; the F-1-2 boundary)
    or on optimizer non-convergence (logged).
    """
    if returns.mean() <= 0.0:
        return 0.0
    min_r = float(returns.min())
    f_upper = cap if min_r >= 0.0 else min(cap, (1.0 - _RUIN_EPSILON) / abs(min_r))
    if f_upper <= 0.0:
        return 0.0
    res = minimize(
        _neg_log_growth,
        x0=np.array(
            [f_upper / 2.0]
        ),  # justify: interior warm-start; objective concave on [0, f_upper]
        args=(returns.reshape(-1, 1),),
        method="L-BFGS-B",
        bounds=[(0.0, f_upper)],
    )
    if not res.success:
        logger.warning("single-arm Kelly did not converge: %s; returning 0.0", res.message)
        return 0.0
    return float(np.asarray(res.x, dtype=float)[0])


def joint_kelly_fractions(
    returns_matrix: npt.ArrayLike,
    *,
    total_exposure_cap: float = 1.0,
    per_arm_cap: float | None = None,
) -> JointKellyResult:
    """Joint log-growth-optimal Kelly fractions for M concurrent arms (Kelly 1956).

    Solves max_f (1/T) Σ_t log(1 + R_t · f) subject to f >= 0, Σ f <=
    total_exposure_cap (optional per-arm cap), AND a per-period no-ruin constraint
    min_t(1 + R_t · f) >= _RUIN_EPSILON. On that no-ruin feasible region the
    objective is concave (log of an affine function of f, averaged), so the
    constrained optimum is global; without the no-ruin constraint the
    `_LOG_ARG_FLOOR` would let the optimizer return a guaranteed-bankrupt f (F-1-1
    audit). The joint fractions are smaller than the standalone Kelly fractions and
    the total stays below the naive sum for positively-correlated / independent
    arms — naive standalone × M summation over-bets and re-introduces ruin (per
    ADR-0029 §D-3.4). The total_exposure_cap is the hard survival cap (enforced
    exactly via post-solve renormalization).

    The Peters-Adamou 2022 time-average-growth lift from pooling is conditional on
    the arms being de-correlated; this primitive optimizes joint log-growth on
    whatever returns_matrix is passed (correctly down-weighting correlated arms) but
    does NOT itself verify de-correlation — that gate is
    `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE`.

    Args:
        returns_matrix: (T, M) array of per-period simple returns for the M
            concurrent arms (e.g., per-session strategy returns). T >= 2, M >= 1.
        total_exposure_cap: Cap on the sum of fractions (default 1.0 = full-Kelly
            total, the promotable ceiling per ADR-0029 §D-3.2; calibration-pending).
        per_arm_cap: Optional per-arm fraction cap (default total_exposure_cap).

    Returns:
        JointKellyResult with the joint fractions + standalone diagnostic + the
        joint growth rate.

    Raises:
        ValueError: if returns_matrix is not 2-D with T >= 2 and M >= 1, or
            total_exposure_cap <= 0, or per_arm_cap <= 0.
    """
    r = np.asarray(returns_matrix, dtype=float)
    if r.ndim != _REQUIRED_NDIM:
        raise ValueError(f"returns_matrix must be 2-D (T, M), got ndim={r.ndim}.")
    n_periods, n_arms = r.shape
    if n_periods < _MIN_PERIODS:
        raise ValueError(f"returns_matrix needs T >= 2 rows, got {n_periods}.")
    if n_arms < 1:
        raise ValueError(f"returns_matrix needs M >= 1 columns, got {n_arms}.")
    if total_exposure_cap <= 0.0:
        raise ValueError(f"total_exposure_cap must be > 0, got {total_exposure_cap}.")
    cap_arm = float(per_arm_cap) if per_arm_cap is not None else float(total_exposure_cap)
    if cap_arm <= 0.0:
        raise ValueError(f"per_arm_cap must be > 0, got {per_arm_cap}.")

    standalone = np.array([_single_arm_kelly(r[:, i], cap_arm) for i in range(n_arms)], dtype=float)

    # justify F-1-1 audit: the per-period no-ruin constraint min_t(1 + R·f) >=
    # _RUIN_EPSILON makes the feasible set the concave no-bankruptcy region; without
    # it the _LOG_ARG_FLOOR lets the optimizer return a guaranteed-bankrupt f.
    constraints = [
        {"type": "ineq", "fun": lambda f: total_exposure_cap - float(np.sum(f))},
        {"type": "ineq", "fun": lambda f: float(np.min(1.0 + r @ f)) - _RUIN_EPSILON},
    ]
    res = minimize(
        _neg_log_growth,
        # justify: interior warm-start at half the per-arm feasible bound; the
        # objective is concave on the no-ruin region so the optimum is x0-insensitive.
        x0=np.full(n_arms, min(cap_arm, total_exposure_cap / n_arms) / 2.0),
        args=(r,),
        method="SLSQP",
        bounds=[(0.0, cap_arm)] * n_arms,
        constraints=constraints,
    )
    if not res.success:
        logger.warning("joint Kelly did not converge: %s; returning zero fractions", res.message)
        fractions = np.zeros(n_arms)
    else:
        fractions = np.clip(np.asarray(res.x, dtype=float), 0.0, cap_arm)
        # F-1-5 audit: SLSQP satisfies Σf <= cap only to tolerance; renormalize so
        # the hard survival cap holds exactly.
        total = float(np.sum(fractions))
        if total > total_exposure_cap:
            fractions = fractions * (total_exposure_cap / total)

    # F-1-2 audit: a bankrupting f makes the true time-average growth -inf (the
    # _LOG_ARG_FLOOR would otherwise report a finite, positively-biased value).
    # growth_rate is recomputed at the CLIPPED fractions (not res.fun) so it matches
    # the returned fractions exactly.
    bankrupts_on_path = bool(np.min(1.0 + r @ fractions) <= 0.0)
    growth_rate = float("-inf") if bankrupts_on_path else -_neg_log_growth(fractions, r)

    return JointKellyResult(
        fractions=fractions,
        total_fraction=float(np.sum(fractions)),
        standalone_fractions=standalone,
        sum_standalone_fractions=float(np.sum(standalone)),
        growth_rate=growth_rate,
        total_exposure_cap=float(total_exposure_cap),
        n_arms=n_arms,
        n_periods=n_periods,
        converged=bool(res.success),
        bankrupts_on_path=bankrupts_on_path,
    )
