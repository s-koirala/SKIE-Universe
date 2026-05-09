"""Calmar ratio + differential CI primitives — drawdown-aware reward-to-pain.

Per ADR-0017 §2.2 (corrected per Round-1 audit F-4/F-5/F-12):

    Calmar_i = (annualized_return_i − rf_i) / |MaxDD_i|        # per-arm Calmar
    calmar_differential = Calmar_arm − Calmar_bench            # difference-of-ratios

The differential statistic is a difference-of-ratios, NOT a ratio-of-difference;
each Calmar_i uses its OWN MaxDD_i denominator per the canonical Young 1991
formulation. The prior `(ret_arm − ret_bench) / max(|DD_arm|, |DD_bench|)`
formulation conflated the two (was a Round-1 audit F-4 finding); corrected here.

The CI primitive uses **paired-pairs** block-stationary-bootstrap: joint
`(r_arm_t, r_bench_t)` tuples are resampled with a shared block length
on the joint level series, preserving cross-arm dependence per the H053
Stage-2 paired-pairs primitive precedent at src/skie_ninja/inference/mediation.py.
Independent per-arm bootstraps (which would produce miscalibrated CI coverage
for the differential statistic) are explicitly forbidden — was a Round-1 audit
F-12 finding.

Block length selection per Politis-White 2004 Econometric Reviews 23(1):53-70
DOI 10.1081/ETC-120028836 + Patton-Politis-White 2009 Econometric Reviews
28(4):372-375 DOI 10.1080/07474930802459016 correction, applied to the joint
level series (not the differential — the level series may have residual
autocorrelation even when the differential is white).

Primary attribution (practitioner, trade-press, not peer-reviewed):
Young, T. W. 1991. "Calmar Ratio: A Smoother Tool." Futures 20(12), Oct 1991.

Closed-form MaxDD distribution for Brownian motion with drift = log-return
process of GBM (load-bearing primary source per Round-1 audit L-4 remediation):
Magdon-Ismail, M., Atiya, A. F., Pratap, A. & Abu-Mostafa, Y. S. 2004.
"On the maximum drawdown of a Brownian motion." J Applied Probability 41(1):147-161.

Companion practitioner summary:
Magdon-Ismail, M. & Atiya, A. F. 2004. "Maximum drawdown." Risk 17(10):99-102.

Implementation lands per `P1-CALMAR-DIFFERENTIAL-CI-IMPL`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §2.2).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "calmar_ratio",
    "calmar_differential",
    "CalmarDifferentialCI",
    "calmar_differential_ci_stationary_bootstrap",
]


@dataclass(frozen=True)
class CalmarDifferentialCI:
    """Paired-pairs stationary-bootstrap CI on the Calmar-differential statistic."""

    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence: float
    n_bootstrap: int
    block_length: int  # single shared block length on joint (r_arm, r_bench) tuples per F-12
    rng_seed: int
    calmar_arm: float
    calmar_bench: float


def calmar_ratio(
    log_returns: np.ndarray,
    *,
    annualization_factor: float = 252.0,
) -> float:
    """Calmar ratio = annualized_return / |MaxDD|.

    Args:
        log_returns: 1-D array of per-session log returns.
        annualization_factor: Sessions per year (default 252; project
            convention).

    Returns:
        Float; +inf if MaxDD = 0; -inf if cumulative return < 0 and MaxDD > 0.

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-CALMAR-DIFFERENTIAL-CI-IMPL`.
    """
    raise NotImplementedError(
        "P1-CALMAR-DIFFERENTIAL-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.2"
    )


def calmar_differential(
    log_returns_arm: np.ndarray,
    log_returns_bench: np.ndarray,
    *,
    annualization_factor: float = 252.0,
) -> float:
    """Calmar_arm − Calmar_bench (point estimate).

    Args:
        log_returns_arm: 1-D array of per-session log returns for the strategy arm.
        log_returns_bench: 1-D array of per-session log returns for the benchmark.
            Must have the same length as `log_returns_arm`.
        annualization_factor: Sessions per year (default 252).

    Returns:
        Float; the differential of the two Calmar ratios.

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-CALMAR-DIFFERENTIAL-CI-IMPL`.
    """
    raise NotImplementedError(
        "P1-CALMAR-DIFFERENTIAL-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.2"
    )


def calmar_differential_ci_stationary_bootstrap(
    log_returns_arm: np.ndarray,
    log_returns_bench: np.ndarray,
    *,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    rng_seed: int = 20260508,
    annualization_factor: float = 252.0,
) -> CalmarDifferentialCI:
    """Politis-Romano 1994 paired-pairs stationary-bootstrap CI on the Calmar-differential.

    Block length is selected per Politis-White 2004 + Patton-Politis-White 2009
    correction, applied to the JOINT (r_arm_t, r_bench_t) level series (NOT
    per-arm independently — independent per-arm bootstraps produce miscalibrated
    CI coverage on the differential statistic per Round-1 audit F-12 finding).
    The shared block length is then applied to paired-pairs joint-tuple
    resampling, preserving cross-arm dependence.
    Returns a `CalmarDifferentialCI` with point estimate + CI bounds + provenance.

    Args:
        log_returns_arm: 1-D per-session log returns for the strategy arm.
        log_returns_bench: 1-D per-session log returns for the benchmark.
            Must have the same length as `log_returns_arm`.
        n_bootstrap: Number of bootstrap replicates (default 1,000).
        confidence: Two-sided CI coverage (default 0.95).
        rng_seed: Deterministic RNG seed (default 20260508).
        annualization_factor: Sessions per year (default 252).

    Returns:
        CalmarDifferentialCI dataclass.

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-CALMAR-DIFFERENTIAL-CI-IMPL`.
    """
    raise NotImplementedError(
        "P1-CALMAR-DIFFERENTIAL-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.2"
    )
