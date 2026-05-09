"""Profit factor + differential CI primitives.

Per ADR-0017 §2.3, profit_factor = gross_profit / gross_loss is operator-
intuitive, scale-invariant, and directly measures the symmetry of winning
vs losing dollar-flow.

Practitioner attribution (Round-1 audit L-2/L-6 remediation): the profit-factor
metric itself is a long-standing futures-trading practitioner convention
(TradeStation system-trading literature, 1980s; LeBeau, Lucas, Williams;
*practitioner-canonical*, multi-source). Tharp 1998 popularized the
`PF >= 1.5` operator-threshold convention as part of the R-multiple framework.

Tharp 1998 *Trade Your Way to Financial Freedom* 1st ed., McGraw-Hill,
ISBN 978-0070647626 (*practitioner*; corrected from the 2007 2nd ed. ISBN
978-0071478717 per Round-1 audit L-2 — the R-multiple framework was introduced
in the 1998 1st edition).

Inferential CI on the differential PF_arm − PF_bench via paired-pairs stationary-
bootstrap per Politis-Romano 1994 JASA 89(428):1303-1313 with Politis-White 2004 +
Patton-Politis-White 2009 corrected automatic block-length selection. The
paired-pairs joint-tuple design follows the Ledoit-Wolf 2008 *J Empirical Finance*
15:850-859 paired-comparison convention as implemented in the project's H053
mediation primitive. The joint-series block-length selection uses
`choose_block_length` which returns max-over-per-arm of PW2004 selections —
this is an **operational choice** consistent with conservative-block reasoning;
PW 2004 specifies per-column selection but does NOT explicitly prescribe an
aggregation rule (per Round-1 audit L-10 verification gap; tracked under
`P1-PW2004-MULTIVARIATE-MAX-RULE-VERIFY`).

**Default mode** (per Round-1 audit F-13 remediation): bootstrap at the
**per-session-aggregate level** (per-session signed P/L tuple `(arm_t, bench_t)`,
paired-pairs joint-tuple resampling). This is robust to intra-session trade
clustering present in high-frequency intraday strategies. Per-trade-level
bootstrap is a sensitivity exhibit subject to a low-clustering empirical caveat
tracked under follow-up `P1-PROFIT-FACTOR-PER-TRADE-CLUSTER-AUDIT`.

Implementation per `P1-PROFIT-FACTOR-CI-IMPL` (BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH
per ADR-0017 §2.3).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    choose_block_length,
    stationary_bootstrap_indices,
)

__all__ = [
    "ProfitFactorDifferentialCI",
    "profit_factor",
    "profit_factor_differential",
    "profit_factor_differential_ci_stationary_bootstrap",
]

# Sentinel for "no losing trades" — caller can detect via np.isinf().
# We use np.inf rather than a large finite cap because operators reading
# the KPI report card need to see "no losses" as a distinct outcome
# from "PF = 1e6". Bootstrap aggregation must filter inf before quantile.
_INF_PF = float("inf")


@dataclass(frozen=True)
class ProfitFactorDifferentialCI:
    """Paired-pairs stationary-bootstrap CI on the profit-factor-differential statistic.

    Per Round-2 audit N-2 remediation: the differential statistic
    PF_arm − PF_bench is bootstrapped via paired-pairs joint-tuple
    resampling (per-session signed-P/L tuples) with a shared block length
    on the joint series. The parallel reasoning to Calmar-differential
    applies: per-session signed P/L from arm vs bench are joint-cross-
    sectional, and independent per-arm block-length selection produces
    miscalibrated CI on the differential. The shared block-length design
    mirrors CalmarDifferentialCI.

    Provenance fields (per Round-1 audit F-6):
    - block_length_method: "politis_white_2004" or "operator_supplied".
    - inf_filter_retained_fraction: ratio of finite-PF bootstrap replicates
      retained / total replicates; values < 0.9 indicate the input
      produced many no-loser bootstrap subsamples (PF=+inf) and the CI is
      computed on a degraded sample. Per Round-1 audit F-2/F-5: this can
      bias the CI toward zero on near-monotonic-up arms — operator should
      review when retention < 0.9 and consider per-session-aggregate
      sensitivity per `P1-PROFIT-FACTOR-PER-TRADE-CLUSTER-AUDIT`.
    """

    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence: float
    n_bootstrap: int  # number of finite-PF bootstrap replicates retained after inf-filter
    block_length: float
    rng_seed: int
    pf_arm: float
    pf_bench: float
    excludes_zero: bool
    block_length_method: str = "politis_white_2004"
    inf_filter_retained_fraction: float = 1.0


def profit_factor(per_trade_pnl: npt.ArrayLike) -> float:
    """profit_factor = sum(pnl[pnl > 0]) / |sum(pnl[pnl < 0])|.

    Args:
        per_trade_pnl: 1-D array of per-trade or per-session signed P/L.
            Positive = winners, negative = losers, zero = breakeven.

    Returns:
        Float; +inf if no losing trades; 0.0 if no winning trades; standard
        ratio otherwise. Scale-invariant — multiplying all per_trade_pnl by
        a positive constant leaves PF unchanged.
    """
    p = np.asarray(per_trade_pnl, dtype=float).ravel()
    if p.size == 0:
        return 0.0
    gross_profit = float(p[p > 0].sum())
    gross_loss = float(-p[p < 0].sum())  # positive number (negation of negative-sum)
    if gross_loss <= 0.0:
        return _INF_PF if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def profit_factor_differential(
    per_trade_pnl_arm: npt.ArrayLike,
    per_trade_pnl_bench: npt.ArrayLike,
) -> float:
    """PF_arm − PF_bench (point estimate; difference-of-ratios).

    Inputs need not be aligned in length — point estimates are computed
    per-arm independently. The bootstrap CI primitive (below) DOES require
    aligned per-session inputs for paired-pairs joint-tuple resampling.
    """
    pf_a = profit_factor(per_trade_pnl_arm)
    pf_b = profit_factor(per_trade_pnl_bench)
    if not (np.isfinite(pf_a) and np.isfinite(pf_b)):
        # If either is inf (no losers), the differential is undefined for
        # operator-decision purposes. Return inf with the sign of the difference
        # so callers can detect via np.isinf().
        if np.isinf(pf_a) and not np.isinf(pf_b):
            return _INF_PF
        if np.isinf(pf_b) and not np.isinf(pf_a):
            return -_INF_PF
        return float("nan")  # both infinite — undefined sign
    return pf_a - pf_b


def profit_factor_differential_ci_stationary_bootstrap(
    session_pnl_arm: npt.ArrayLike,
    session_pnl_bench: npt.ArrayLike,
    *,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    rng_seed: int = 20260508,
    block_length: float | None = None,
) -> ProfitFactorDifferentialCI:
    """Politis-Romano 1994 paired-pairs stationary-bootstrap CI on the PF-differential.

    Inputs are **per-session signed P/L** for each arm — caller is responsible
    for pre-aggregating per-trade P/L into per-session totals. This is the
    robust default mode per Round-1 audit F-13 remediation; per-trade-level
    bootstrap is a sensitivity exhibit tracked under follow-up
    `P1-PROFIT-FACTOR-PER-TRADE-CLUSTER-AUDIT`.

    Block length is selected per Politis-White 2004 + Patton-Politis-White 2009
    correction on the JOINT (arm, bench) per-session level series, then applied
    as a shared block length to paired-pairs joint-tuple resampling.

    Bootstrap replicates that produce non-finite PF (no winners or no losers in
    the resampled subset) are filtered before percentile computation. If fewer
    than 10 finite replicates survive, CI is NaN (caller should detect via
    `n_bootstrap < 10`).

    Args:
        session_pnl_arm: 1-D array of per-session signed total P/L for arm
            (positive for net-winning sessions, negative for net-losing,
            zero for no-trade sessions).
        session_pnl_bench: 1-D array of per-session signed total P/L for bench.
            Must have the same length as session_pnl_arm.
        n_bootstrap: Number of bootstrap replicates (default 1,000).
        confidence: Two-sided CI coverage in (0, 1) (default 0.95).
        rng_seed: Deterministic RNG seed (default 20260508).
        block_length: Optional explicit block length; if None, auto-selected.

    Returns:
        ProfitFactorDifferentialCI dataclass.
    """
    arm = np.asarray(session_pnl_arm, dtype=float).ravel()
    bench = np.asarray(session_pnl_bench, dtype=float).ravel()
    if arm.shape != bench.shape:
        raise ValueError(
            f"session_pnl_arm and session_pnl_bench must align; "
            f"got {arm.shape} vs {bench.shape}."
        )
    n = arm.size
    if n < 4:
        raise ValueError(f"session_pnl arrays require n >= 4 sessions, got {n}.")
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}.")
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}.")

    # Block-length selection on joint level series. Per Round-1 audit L-10
    # remediation: choose_block_length returns max-over-per-arm of PW2004
    # selections; this is an operational choice (PW 2004 specifies per-column
    # selection but does NOT prescribe an aggregation rule per L-10
    # verification gap). Tracked under `P1-PW2004-MULTIVARIATE-MAX-RULE-VERIFY`.
    if block_length is None:
        joint = np.column_stack([arm, bench])
        sel: BlockLengthSelection = choose_block_length(joint, bootstrap_type="stationary")
        bl = float(sel.block_length)
        bl_method = "politis_white_2004"
    else:
        if block_length < 1.0:
            raise ValueError(f"block_length must be >= 1, got {block_length}.")
        bl = float(block_length)
        bl_method = "operator_supplied"

    pf_arm_point = profit_factor(arm)
    pf_bench_point = profit_factor(bench)
    if not (np.isfinite(pf_arm_point) and np.isfinite(pf_bench_point)):
        # Degenerate input — at least one arm has no losses (PF=+inf) or the
        # input is empty. Return point-only with NaN CI; caller can detect via
        # n_bootstrap=0 sentinel. Per Round-1 audit F-4 remediation: the
        # point_estimate uses signed-inf logic mirroring profit_factor_differential
        # (eliminated the dead-code conditional from the prior implementation).
        if np.isinf(pf_arm_point) and not np.isinf(pf_bench_point):
            point_estimate_degenerate: float = _INF_PF
        elif np.isinf(pf_bench_point) and not np.isinf(pf_arm_point):
            point_estimate_degenerate = -_INF_PF
        else:
            point_estimate_degenerate = float("nan")
        return ProfitFactorDifferentialCI(
            point_estimate=point_estimate_degenerate,
            ci_lower=float("nan"),
            ci_upper=float("nan"),
            confidence=confidence,
            n_bootstrap=0,
            block_length=bl,
            rng_seed=rng_seed,
            pf_arm=pf_arm_point,
            pf_bench=pf_bench_point,
            excludes_zero=False,
            block_length_method=bl_method,
            inf_filter_retained_fraction=0.0,
        )
    point = pf_arm_point - pf_bench_point

    rng = np.random.default_rng(rng_seed)
    boot_diffs = np.empty(n_bootstrap, dtype=float)
    finite_count = 0
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n=n, block_length=bl, rng=rng)
        pf_a_b = profit_factor(arm[idx])
        pf_b_b = profit_factor(bench[idx])
        if np.isfinite(pf_a_b) and np.isfinite(pf_b_b):
            boot_diffs[finite_count] = pf_a_b - pf_b_b
            finite_count += 1

    retained_fraction = float(finite_count) / float(n_bootstrap)

    if finite_count < 10:
        return ProfitFactorDifferentialCI(
            point_estimate=point,
            ci_lower=float("nan"),
            ci_upper=float("nan"),
            confidence=confidence,
            n_bootstrap=finite_count,
            block_length=bl,
            rng_seed=rng_seed,
            pf_arm=pf_arm_point,
            pf_bench=pf_bench_point,
            excludes_zero=False,
            block_length_method=bl_method,
            inf_filter_retained_fraction=retained_fraction,
        )

    boot_finite = boot_diffs[:finite_count]
    alpha = 1.0 - confidence
    lo = float(np.quantile(boot_finite, alpha / 2.0))
    hi = float(np.quantile(boot_finite, 1.0 - alpha / 2.0))

    return ProfitFactorDifferentialCI(
        point_estimate=point,
        ci_lower=lo,
        ci_upper=hi,
        confidence=confidence,
        n_bootstrap=finite_count,
        block_length=bl,
        rng_seed=rng_seed,
        pf_arm=pf_arm_point,
        pf_bench=pf_bench_point,
        excludes_zero=(lo > 0.0 or hi < 0.0),
        block_length_method=bl_method,
        inf_filter_retained_fraction=retained_fraction,
    )
