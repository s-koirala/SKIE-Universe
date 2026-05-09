"""Calmar ratio + differential CI primitives — drawdown-aware reward-to-pain.

Per ADR-0017 §2.2 (corrected per Round-1 audit F-4/F-5/F-12):

    Calmar_i = annualized_arithmetic_return_i / |MaxDD_i|        # per-arm Calmar
    calmar_differential = Calmar_arm − Calmar_bench               # difference-of-ratios

The differential statistic is a difference-of-ratios, NOT a ratio-of-difference;
each Calmar_i uses its OWN MaxDD_i denominator per the canonical Young 1991
formulation. The prior `(ret_arm − ret_bench) / max(|DD_arm|, |DD_bench|)`
formulation conflated the two (was a Round-1 audit F-4 finding); corrected here.

The CI primitive uses **paired-pairs** block-stationary-bootstrap: joint
`(r_arm_t, r_bench_t)` tuples are resampled with a shared block length on
the joint level series, preserving cross-arm dependence. Independent
per-arm bootstraps (which would produce miscalibrated CI coverage for
the differential statistic) are explicitly forbidden — was a Round-1
audit F-12 finding. The paired-pairs joint-tuple design follows the
Ledoit-Wolf 2008 *J Empirical Finance* 15:850-859 paired-comparison
convention as implemented in the project's H053 mediation primitive.

Block-length selection per Politis-White 2004 + Patton-Politis-White 2009
correction, applied to the joint level series (not the differential — the
level series may have residual autocorrelation even when the differential
is white). The joint-series selection uses `choose_block_length` which
returns the **max-over-per-arm** of PW2004 selections — this is an
**operational choice** consistent with conservative-block reasoning;
PW 2004 specifies per-column selection but does NOT explicitly prescribe
an aggregation rule (per Round-1 audit L-10 verification gap; tracked
under `P1-PW2004-MULTIVARIATE-MAX-RULE-VERIFY`).

Primary attribution (practitioner, trade-press, not peer-reviewed):
Young, T. W. 1991. "Calmar Ratio: A Smoother Tool." Futures 20(12), Oct 1991.

Closed-form MaxDD distribution for Brownian motion with drift (= log-return
process of GBM; load-bearing primary source per Round-1 audit L-4 remediation):
Magdon-Ismail, M., Atiya, A. F., Pratap, A. & Abu-Mostafa, Y. S. 2004.
"On the maximum drawdown of a Brownian motion." J Applied Probability 41(1):147-161.

Companion practitioner summary:
Magdon-Ismail, M. & Atiya, A. F. 2004. "Maximum drawdown." Risk 17(10):99-102.

Implementation per `P1-CALMAR-DIFFERENTIAL-CI-IMPL` (BLOCKING-BEFORE-NEXT-NEW-
HYPOTHESIS-LAUNCH per ADR-0017 §2.2).
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
    "CalmarDifferentialCI",
    "calmar_differential",
    "calmar_differential_ci_stationary_bootstrap",
    "calmar_ratio",
    "max_drawdown_fraction",
]

# A small numerical floor on |MaxDD| to avoid division-by-zero on
# strictly-monotonic-up series. Float64 ULP scaled to a typical
# equity fraction.
_MAXDD_FLOOR = 1e-12


@dataclass(frozen=True)
class CalmarDifferentialCI:
    """Paired-pairs stationary-bootstrap CI on the Calmar-differential statistic.

    Provenance fields (per Round-1 audit F-6):
    - block_length_method: "politis_white_2004" (auto-selected via PW2004 on
      joint level series) or "operator_supplied" (caller passed block_length=N).
    - inf_filter_retained_fraction: ratio of finite-Calmar bootstrap replicates
      retained / total replicates; per Round-1 audit F-2 audit-trail surfaced.
      Values < 0.9 indicate the input series produced many monotonic-up
      bootstrap subsamples (zero MaxDD → infinite Calmar) and the CI is
      computed on a degraded sample — operator should review.

    Degenerate-input handling (per Round-1 audit F-1): if either input series
    has zero MaxDD (strictly-monotonic) at point-estimate time, both calmar_arm
    and calmar_bench may be infinite; the CI returns NaN bounds with
    n_bootstrap = 0 sentinel, mirroring the profit-factor primitive's
    degenerate-input handling. Callers should check `np.isfinite(calmar_arm)`
    and `np.isfinite(calmar_bench)` before interpreting `point_estimate`.
    """

    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence: float
    n_bootstrap: int
    block_length: float  # single shared block length on joint (r_arm, r_bench) tuples per F-12
    rng_seed: int
    calmar_arm: float
    calmar_bench: float
    excludes_zero: bool
    block_length_method: str = "politis_white_2004"
    inf_filter_retained_fraction: float = 1.0


def max_drawdown_fraction(log_returns: npt.ArrayLike) -> float:
    """Maximum drawdown as a positive fraction of equity.

    The equity curve starts at 1.0 at t=−1 (pre-first-bar baseline) and
    evolves as `E_t = exp(cumsum(log_returns))` for t = 0, 1, ..., n−1.
    Prepending the baseline 1.0 ensures a single-loss series registers
    drawdown from the initial peak (otherwise, `np.maximum.accumulate`
    starts at the first observed equity, missing the drawdown from the
    pre-first-bar baseline). Returns `−min_t d_t` where
    `d_t = (E_t − P_t) / P_t` (≤ 0) and `P_t = max_{s≤t} E_s`. Returns
    0.0 for a strictly-monotonic-up series and for an empty input.

    Args:
        log_returns: 1-D array of per-session log returns.

    Returns:
        Float in [0, 1]; the maximum-drawdown fraction (positive).
    """
    r = np.asarray(log_returns, dtype=float).ravel()
    if r.size == 0:
        return 0.0
    # Prepend baseline equity 1.0 so single-loss bars register drawdown
    # from the pre-first-bar peak.
    equity = np.concatenate(([1.0], np.exp(np.cumsum(r))))
    running_peak = np.maximum.accumulate(equity)
    # running_peak always ≥ 1.0 by construction; guard for completeness.
    running_peak = np.where(running_peak <= 0.0, _MAXDD_FLOOR, running_peak)
    dd = (equity - running_peak) / running_peak
    return float(-dd.min())  # dd ≤ 0; -min(dd) ≥ 0


def calmar_ratio(
    log_returns: npt.ArrayLike,
    *,
    annualization_factor: float = 252.0,
    risk_free_rate: float = 0.0,
) -> float:
    """Calmar ratio = (annualized_arithmetic_return − rf) / |MaxDD|.

    Per Young 1991 *Futures* magazine (*practitioner*) the canonical Calmar
    formulation uses arithmetic annualized return in the numerator; consistent
    with the |MaxDD| denominator (also a fraction of equity).

    Args:
        log_returns: 1-D array of per-session log returns.
        annualization_factor: Sessions per year (default 252; project convention).
        risk_free_rate: Annual risk-free rate as a fraction (default 0.0;
            project convention is to report Calmar without rf-subtraction
            for cross-strategy comparability, matching the H050/H053 KPI
            report cards' Sharpe convention).

    Returns:
        Float; +inf if |MaxDD| is below the numerical floor (strictly-up series);
        the Calmar ratio otherwise. Negative if the cumulative return is negative
        and MaxDD > 0.
    """
    r = np.asarray(log_returns, dtype=float).ravel()
    if r.size == 0:
        return 0.0
    annualized_arithmetic_return = float(np.exp(r.mean() * annualization_factor) - 1.0)
    max_dd = max_drawdown_fraction(r)
    if max_dd <= _MAXDD_FLOOR:
        return float("inf") if annualized_arithmetic_return > 0 else float("-inf") if annualized_arithmetic_return < 0 else 0.0
    return (annualized_arithmetic_return - float(risk_free_rate)) / max_dd


def calmar_differential(
    log_returns_arm: npt.ArrayLike,
    log_returns_bench: npt.ArrayLike,
    *,
    annualization_factor: float = 252.0,
    risk_free_rate: float = 0.0,
) -> float:
    """Calmar_arm − Calmar_bench (point estimate; difference-of-ratios)."""
    arm = np.asarray(log_returns_arm, dtype=float).ravel()
    bench = np.asarray(log_returns_bench, dtype=float).ravel()
    if arm.shape != bench.shape:
        raise ValueError(
            f"log_returns_arm and log_returns_bench must align; "
            f"got {arm.shape} vs {bench.shape}."
        )
    c_arm = calmar_ratio(arm, annualization_factor=annualization_factor, risk_free_rate=risk_free_rate)
    c_bench = calmar_ratio(bench, annualization_factor=annualization_factor, risk_free_rate=risk_free_rate)
    return c_arm - c_bench


def calmar_differential_ci_stationary_bootstrap(
    log_returns_arm: npt.ArrayLike,
    log_returns_bench: npt.ArrayLike,
    *,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    rng_seed: int = 20260508,
    annualization_factor: float = 252.0,
    risk_free_rate: float = 0.0,
    block_length: float | None = None,
) -> CalmarDifferentialCI:
    """Politis-Romano 1994 paired-pairs stationary-bootstrap CI on the Calmar-differential.

    Block length is selected per Politis-White 2004 + Patton-Politis-White 2009
    correction, applied to the JOINT (r_arm_t, r_bench_t) level series via
    `choose_block_length` (which returns max-over-per-arm per the PW 2004
    multivariate recommendation). The shared block length is then applied
    to paired-pairs joint-tuple resampling, preserving cross-arm dependence.

    Independent per-arm bootstraps (which would produce miscalibrated CI
    coverage on the differential statistic) are explicitly forbidden per
    Round-1 audit F-12 finding.

    Args:
        log_returns_arm: 1-D per-session log returns for the strategy arm.
        log_returns_bench: 1-D per-session log returns for the benchmark.
            Must have the same length as log_returns_arm.
        n_bootstrap: Number of bootstrap replicates (default 1,000).
        confidence: Two-sided CI coverage in (0, 1) (default 0.95).
        rng_seed: Deterministic RNG seed (default 20260508).
        annualization_factor: Sessions per year (default 252).
        risk_free_rate: Annual risk-free rate (default 0.0).
        block_length: Optional explicit block length; if None, auto-selected.

    Returns:
        CalmarDifferentialCI dataclass.
    """
    arm = np.asarray(log_returns_arm, dtype=float).ravel()
    bench = np.asarray(log_returns_bench, dtype=float).ravel()
    if arm.shape != bench.shape:
        raise ValueError(
            f"log_returns_arm and log_returns_bench must align; "
            f"got {arm.shape} vs {bench.shape}."
        )
    n = arm.size
    if n < 4:
        raise ValueError(f"log_returns require n >= 4 sessions, got {n}.")
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

    c_arm_point = calmar_ratio(
        arm, annualization_factor=annualization_factor, risk_free_rate=risk_free_rate
    )
    c_bench_point = calmar_ratio(
        bench, annualization_factor=annualization_factor, risk_free_rate=risk_free_rate
    )

    # Per Round-1 audit F-1: degenerate-input handling. If either per-arm
    # Calmar is non-finite at point-estimate time (zero MaxDD on the
    # input series), the differential is undefined and the bootstrap CI
    # returns NaN with sentinel n_bootstrap=0. Mirrors the profit-factor
    # primitive's degenerate-input branch.
    if not (np.isfinite(c_arm_point) and np.isfinite(c_bench_point)):
        return CalmarDifferentialCI(
            point_estimate=float("nan"),
            ci_lower=float("nan"),
            ci_upper=float("nan"),
            confidence=confidence,
            n_bootstrap=0,
            block_length=bl,
            rng_seed=rng_seed,
            calmar_arm=c_arm_point,
            calmar_bench=c_bench_point,
            excludes_zero=False,
            block_length_method=bl_method,
            inf_filter_retained_fraction=0.0,
        )

    point = c_arm_point - c_bench_point

    rng = np.random.default_rng(rng_seed)
    boot_diffs = np.empty(n_bootstrap, dtype=float)
    finite_count = 0
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n=n, block_length=bl, rng=rng)
        c_arm_b = calmar_ratio(
            arm[idx], annualization_factor=annualization_factor, risk_free_rate=risk_free_rate
        )
        c_bench_b = calmar_ratio(
            bench[idx], annualization_factor=annualization_factor, risk_free_rate=risk_free_rate
        )
        diff_b = c_arm_b - c_bench_b
        if np.isfinite(diff_b):
            boot_diffs[finite_count] = diff_b
            finite_count += 1

    retained_fraction = float(finite_count) / float(n_bootstrap)

    if finite_count < 10:
        return CalmarDifferentialCI(
            point_estimate=point,
            ci_lower=float("nan"),
            ci_upper=float("nan"),
            confidence=confidence,
            n_bootstrap=finite_count,
            block_length=bl,
            rng_seed=rng_seed,
            calmar_arm=c_arm_point,
            calmar_bench=c_bench_point,
            excludes_zero=False,
            block_length_method=bl_method,
            inf_filter_retained_fraction=retained_fraction,
        )

    boot_finite = boot_diffs[:finite_count]
    alpha = 1.0 - confidence
    lo = float(np.quantile(boot_finite, alpha / 2.0))
    hi = float(np.quantile(boot_finite, 1.0 - alpha / 2.0))

    return CalmarDifferentialCI(
        point_estimate=point,
        ci_lower=lo,
        ci_upper=hi,
        confidence=confidence,
        n_bootstrap=finite_count,
        block_length=bl,
        rng_seed=rng_seed,
        calmar_arm=c_arm_point,
        calmar_bench=c_bench_point,
        excludes_zero=(lo > 0.0 or hi < 0.0),
        block_length_method=bl_method,
        inf_filter_retained_fraction=retained_fraction,
    )
