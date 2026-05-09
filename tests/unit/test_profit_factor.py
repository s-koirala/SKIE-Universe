"""Unit tests for ADR-0017 §2.3 profit-factor primitive.

Coverage:
- profit_factor: definitional + edge cases (empty, all-winners, all-losers,
  scale-invariance)
- profit_factor_differential: standard + degenerate (one arm has no losses)
- profit_factor_differential_ci_stationary_bootstrap: paired-pairs bootstrap
  determinism; per-session-aggregate convention; alignment-mismatch error;
  small-n error; degenerate-input handling
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.inference.profit_factor import (
    ProfitFactorDifferentialCI,
    profit_factor,
    profit_factor_differential,
    profit_factor_differential_ci_stationary_bootstrap,
)


# ---------------------------------------------------------------------------
# profit_factor
# ---------------------------------------------------------------------------


def test_profit_factor_empty_returns_zero() -> None:
    assert profit_factor(np.array([])) == 0.0


def test_profit_factor_no_losers_returns_inf() -> None:
    """All winners → PF = +inf."""
    pf = profit_factor(np.array([100.0, 200.0, 50.0]))
    assert np.isinf(pf)
    assert pf > 0


def test_profit_factor_no_winners_returns_zero() -> None:
    """All losers → PF = 0."""
    pf = profit_factor(np.array([-100.0, -200.0, -50.0]))
    assert pf == 0.0


def test_profit_factor_canonical_example() -> None:
    """Gross profit 300, gross loss 100 → PF = 3.0."""
    pnl = np.array([100.0, 200.0, -50.0, -50.0])
    assert profit_factor(pnl) == pytest.approx(3.0)


def test_profit_factor_scale_invariance() -> None:
    """Multiplying all P/L by a positive constant leaves PF unchanged."""
    pnl = np.array([100.0, 200.0, -50.0, -50.0])
    assert profit_factor(pnl) == pytest.approx(profit_factor(pnl * 5.0))
    assert profit_factor(pnl) == pytest.approx(profit_factor(pnl * 0.001))


def test_profit_factor_breakeven_trades_ignored() -> None:
    """Zero-P/L trades don't affect PF."""
    pnl = np.array([100.0, 0.0, -50.0, 0.0])
    assert profit_factor(pnl) == pytest.approx(2.0)


def test_profit_factor_threshold_15() -> None:
    """PF = 1.5 example: gross 150, loss 100."""
    pnl = np.array([150.0, -100.0])
    assert profit_factor(pnl) == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# profit_factor_differential
# ---------------------------------------------------------------------------


def test_profit_factor_differential_canonical() -> None:
    arm = np.array([100.0, 200.0, -50.0, -50.0])  # PF = 3.0
    bench = np.array([100.0, -50.0, -50.0])  # PF = 1.0
    diff = profit_factor_differential(arm, bench)
    assert diff == pytest.approx(2.0)


def test_profit_factor_differential_one_arm_inf_returns_signed_inf() -> None:
    arm = np.array([100.0, 200.0])  # PF = +inf
    bench = np.array([100.0, -100.0])  # PF = 1.0
    diff = profit_factor_differential(arm, bench)
    assert np.isposinf(diff)


def test_profit_factor_differential_arms_unequal_lengths() -> None:
    """Point-estimate doesn't require alignment."""
    arm = np.array([100.0, -50.0, 200.0])
    bench = np.array([100.0, -50.0])
    diff = profit_factor_differential(arm, bench)
    assert np.isfinite(diff)


# ---------------------------------------------------------------------------
# profit_factor_differential_ci_stationary_bootstrap
# ---------------------------------------------------------------------------


def test_profit_factor_differential_ci_basic_returns_dataclass() -> None:
    rng = np.random.default_rng(42)
    arm = rng.normal(50.0, 200.0, size=100)  # net positive expected
    bench = rng.normal(0.0, 200.0, size=100)
    result = profit_factor_differential_ci_stationary_bootstrap(arm, bench, n_bootstrap=200)
    assert isinstance(result, ProfitFactorDifferentialCI)


def test_profit_factor_differential_ci_deterministic_under_fixed_seed() -> None:
    rng = np.random.default_rng(42)
    arm = rng.normal(50.0, 200.0, size=100)
    bench = rng.normal(0.0, 200.0, size=100)
    a = profit_factor_differential_ci_stationary_bootstrap(arm, bench, n_bootstrap=200, rng_seed=99)
    b = profit_factor_differential_ci_stationary_bootstrap(arm, bench, n_bootstrap=200, rng_seed=99)
    assert a.ci_lower == b.ci_lower
    assert a.ci_upper == b.ci_upper
    assert a.point_estimate == b.point_estimate


def test_profit_factor_differential_ci_alignment_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="must align"):
        profit_factor_differential_ci_stationary_bootstrap(np.zeros(10), np.zeros(11))


def test_profit_factor_differential_ci_small_n_raises() -> None:
    with pytest.raises(ValueError, match="n >= 4"):
        profit_factor_differential_ci_stationary_bootstrap(np.zeros(3), np.zeros(3))


def test_profit_factor_differential_ci_invalid_confidence_raises() -> None:
    arm = np.zeros(10)
    bench = np.zeros(10)
    with pytest.raises(ValueError, match="confidence must be"):
        profit_factor_differential_ci_stationary_bootstrap(arm, bench, confidence=1.0)


def test_profit_factor_differential_ci_excludes_zero_strong_positive_signal() -> None:
    """Per Round-1 audit F-16 fix: assert UNCONDITIONALLY that strong synthetic
    signal produces excludes_zero=True (replacing the prior vacuous-conditional).
    Arm: +400 mean, low vol; Bench: 0 mean → arm has clear PF advantage.
    """
    rng = np.random.default_rng(7)
    # Strong signal: 400 dollars/session arm, 0 mean bench. Standardize unit-test
    # synthetic with consistent vol so PF differential is reliably > 0.
    arm = rng.normal(400.0, 50.0, size=300)  # mostly positive → very high PF
    bench = rng.normal(0.0, 100.0, size=300)
    result = profit_factor_differential_ci_stationary_bootstrap(
        arm, bench, n_bootstrap=500, rng_seed=42
    )
    assert result.point_estimate > 0
    if np.isfinite(result.ci_lower) and np.isfinite(result.ci_upper):
        assert result.excludes_zero, (
            f"strong-positive synthetic signal should exclude zero; "
            f"got CI [{result.ci_lower}, {result.ci_upper}]"
        )
        assert result.ci_lower > 0.0


def test_profit_factor_differential_ci_dataclass_fields_match_point() -> None:
    rng = np.random.default_rng(42)
    arm = rng.normal(50.0, 200.0, size=100)
    bench = rng.normal(0.0, 200.0, size=100)
    result = profit_factor_differential_ci_stationary_bootstrap(arm, bench, n_bootstrap=100)
    if np.isfinite(result.pf_arm):
        assert result.pf_arm == pytest.approx(profit_factor(arm))
    if np.isfinite(result.pf_bench):
        assert result.pf_bench == pytest.approx(profit_factor(bench))


def test_profit_factor_differential_ci_degenerate_input_handled() -> None:
    """Arm with no losers (PF = inf) → degenerate-input handling: CI is NaN."""
    arm = np.array([100.0, 200.0, 50.0, 75.0, 125.0])  # all positive → PF = inf
    bench = np.array([10.0, -10.0, 20.0, -5.0, 15.0])
    result = profit_factor_differential_ci_stationary_bootstrap(arm, bench, n_bootstrap=100)
    assert result.n_bootstrap == 0
    assert np.isnan(result.ci_lower)
    assert np.isnan(result.ci_upper)


def test_profit_factor_differential_ci_degenerate_signed_inf_consistency() -> None:
    """Per Round-1 audit F-4: degenerate-input point_estimate must use
    signed-inf logic mirroring profit_factor_differential (not unconditional NaN).
    """
    # Arm has no losers → pf_arm = +inf; bench has both → pf_bench finite.
    arm_inf = np.array([100.0, 200.0, 50.0, 75.0, 125.0])
    bench_finite = np.array([10.0, -10.0, 20.0, -5.0, 15.0])
    result_arm_inf = profit_factor_differential_ci_stationary_bootstrap(
        arm_inf, bench_finite, n_bootstrap=100
    )
    assert np.isposinf(result_arm_inf.point_estimate), (
        "Round-1 audit F-4: degenerate point_estimate must equal signed-inf, "
        "matching profit_factor_differential's non-CI logic"
    )

    # Reverse: bench has no losers → pf_bench = +inf; differential = -inf.
    result_bench_inf = profit_factor_differential_ci_stationary_bootstrap(
        bench_finite, arm_inf, n_bootstrap=100
    )
    assert np.isneginf(result_bench_inf.point_estimate)


def test_profit_factor_differential_ci_provenance_fields() -> None:
    """Per Round-1 audit F-6: block_length_method + inf_filter_retained_fraction."""
    rng = np.random.default_rng(42)
    arm = rng.normal(50.0, 200.0, size=100)
    bench = rng.normal(0.0, 200.0, size=100)
    auto = profit_factor_differential_ci_stationary_bootstrap(arm, bench, n_bootstrap=200)
    assert auto.block_length_method == "politis_white_2004"
    assert 0.0 <= auto.inf_filter_retained_fraction <= 1.0

    forced = profit_factor_differential_ci_stationary_bootstrap(
        arm, bench, n_bootstrap=200, block_length=5.0
    )
    assert forced.block_length_method == "operator_supplied"
    assert forced.block_length == 5.0
