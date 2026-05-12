"""Inference sub-package — HAC, Sharpe CI, SPA, bootstrap, survival-constrained metrics.

Per ADR-0017 (2026-05-08), the survival-constrained metric primitives
(Calmar-differential, profit-factor-differential, R-multiple, risk-of-ruin)
are the load-bearing primary inferential layer; the Sharpe-family primitives
(LW2008, Hansen SPA) are preserved as secondary KPIs.
"""

from skie_ninja.inference.bocd import (
    BOCDState,
    bocd_run,
    bocd_update,
    changepoint_posterior,
    detect_decay,
    init_bocd,
)
from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    choose_block_length,
    politis_white_block_length,
    stationary_bootstrap,
    stationary_bootstrap_indices,
)
from skie_ninja.inference.calmar import (
    CalmarDifferentialCI,
    calmar_differential,
    calmar_differential_ci_stationary_bootstrap,
    calmar_ratio,
)
from skie_ninja.inference.mppm import (
    MPPMResult,
    mppm,
    mppm_rho_1,
    mppm_with_ci,
)
from skie_ninja.inference.multipletest import HansenSPAResult, hansen_spa_test
from skie_ninja.inference.profit_factor import (
    ProfitFactorDifferentialCI,
    profit_factor,
    profit_factor_differential,
    profit_factor_differential_ci_stationary_bootstrap,
)
from skie_ninja.inference.r_multiple import (
    RMultipleMeanCI,
    r_multiple_distribution,
    r_multiple_from_trade,
    r_multiple_mean_ci_stationary_bootstrap,
)
from skie_ninja.inference.risk_of_ruin import (
    RiskOfRuinResult,
    probability_of_ruin_monte_carlo,
)
from skie_ninja.inference.skewness import (
    LSkewnessTau3CI,
    l_moments_pwm,
    l_skewness_tau3,
    l_skewness_tau3_ci_stationary_bootstrap,
    payoff_shape_annotation,
)

__all__ = [
    "BOCDState",
    "BlockLengthSelection",
    "CalmarDifferentialCI",
    "HansenSPAResult",
    "LSkewnessTau3CI",
    "MPPMResult",
    "ProfitFactorDifferentialCI",
    "RMultipleMeanCI",
    "RiskOfRuinResult",
    "bocd_run",
    "bocd_update",
    "calmar_differential",
    "calmar_differential_ci_stationary_bootstrap",
    "calmar_ratio",
    "changepoint_posterior",
    "choose_block_length",
    "detect_decay",
    "hansen_spa_test",
    "init_bocd",
    "l_moments_pwm",
    "l_skewness_tau3",
    "l_skewness_tau3_ci_stationary_bootstrap",
    "mppm",
    "mppm_rho_1",
    "mppm_with_ci",
    "payoff_shape_annotation",
    "politis_white_block_length",
    "probability_of_ruin_monte_carlo",
    "profit_factor",
    "profit_factor_differential",
    "profit_factor_differential_ci_stationary_bootstrap",
    "r_multiple_distribution",
    "r_multiple_from_trade",
    "r_multiple_mean_ci_stationary_bootstrap",
    "stationary_bootstrap",
    "stationary_bootstrap_indices",
]
