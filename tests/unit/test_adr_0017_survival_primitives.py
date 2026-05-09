"""Test stubs for ADR-0017 survival-constrained primitives.

All bodies pending BLOCKING-before-launch implementation per the
follow-ups enumerated in ADR-0017 §Follow-ups. Tests skip until the
primitives are implemented; this file locks the interface-import surface
so the test suite continues to collect without ImportError after the
ADR-0017 inference __init__.py amendment.
"""

from __future__ import annotations

import pytest


def test_calmar_primitives_exposed_at_inference_root() -> None:
    """ADR-0017 §2.2 Calmar primitives surfaced via skie_ninja.inference."""
    from skie_ninja.inference import (
        CalmarDifferentialCI,
        calmar_differential,
        calmar_differential_ci_stationary_bootstrap,
        calmar_ratio,
    )

    # callable contracts present
    assert callable(calmar_ratio)
    assert callable(calmar_differential)
    assert callable(calmar_differential_ci_stationary_bootstrap)
    # frozen dataclass contract present
    assert hasattr(CalmarDifferentialCI, "__dataclass_fields__")


def test_profit_factor_primitives_exposed_at_inference_root() -> None:
    """ADR-0017 §2.3 profit-factor primitives surfaced via skie_ninja.inference."""
    from skie_ninja.inference import (
        ProfitFactorDifferentialCI,
        profit_factor,
        profit_factor_differential,
        profit_factor_differential_ci_stationary_bootstrap,
    )

    assert callable(profit_factor)
    assert callable(profit_factor_differential)
    assert callable(profit_factor_differential_ci_stationary_bootstrap)
    assert hasattr(ProfitFactorDifferentialCI, "__dataclass_fields__")


def test_r_multiple_primitives_exposed_at_inference_root() -> None:
    """ADR-0017 §2.4 R-multiple primitives surfaced via skie_ninja.inference."""
    from skie_ninja.inference import (
        RMultipleMeanCI,
        r_multiple_distribution,
        r_multiple_from_trade,
        r_multiple_mean_ci_stationary_bootstrap,
    )

    assert callable(r_multiple_from_trade)
    assert callable(r_multiple_distribution)
    assert callable(r_multiple_mean_ci_stationary_bootstrap)
    assert hasattr(RMultipleMeanCI, "__dataclass_fields__")


def test_risk_of_ruin_primitives_exposed_at_inference_root() -> None:
    """ADR-0017 §4.2 risk-of-ruin primitive surfaced via skie_ninja.inference."""
    from skie_ninja.inference import (
        RiskOfRuinResult,
        probability_of_ruin_monte_carlo,
    )

    assert callable(probability_of_ruin_monte_carlo)
    assert hasattr(RiskOfRuinResult, "__dataclass_fields__")


def test_sizing_module_imports() -> None:
    """ADR-0017 §4.1 sizing sub-package is importable."""
    from skie_ninja.sizing import (
        compute_position_size,
        drawdown_constrained_kelly,
        kelly_fraction_from_r_multiples,
    )

    assert callable(kelly_fraction_from_r_multiples)
    assert callable(drawdown_constrained_kelly)
    assert callable(compute_position_size)


def test_calmar_ratio_basic() -> None:
    """Calmar ratio sanity smoke test (full coverage in test_calmar.py)."""
    import numpy as np

    from skie_ninja.inference import calmar_ratio

    # Strictly positive returns → MaxDD = 0 → Calmar = +inf
    log_returns = np.array([0.001] * 100)
    assert np.isposinf(calmar_ratio(log_returns))


def test_profit_factor_basic() -> None:
    """Profit factor sanity smoke test (full coverage in test_profit_factor.py)."""
    import numpy as np

    from skie_ninja.inference import profit_factor

    # Gross profit 300, gross loss 100 → PF = 3.0
    pnl = np.array([100.0, 200.0, -50.0, -50.0])
    assert profit_factor(pnl) == 3.0


def test_r_multiple_from_trade_basic() -> None:
    """R-multiple sanity smoke test (full coverage in test_r_multiple.py)."""
    from skie_ninja.inference import r_multiple_from_trade

    r = r_multiple_from_trade(
        500.0, stop_loss_distance=10.0, position_size=1, multiplier=50.0
    )
    assert r == 1.0


@pytest.mark.skip(reason="P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE pending (separate commit)")
def test_probability_of_ruin_basic() -> None:
    """Risk-of-ruin Monte Carlo. Pending implementation in next Phase L commit."""


@pytest.mark.skip(reason="P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE pending (separate commit)")
def test_compute_position_size_basic() -> None:
    """Position-sizing canonical computation. Pending implementation in next Phase L commit."""
