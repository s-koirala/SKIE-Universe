"""Unit tests for ADR-0017 §2.4 R-multiple primitive.

Coverage:
- r_multiple_from_trade: definitional + edge cases (zero 1R → ValueError;
  signed P/L correctness; dimensional check vs hand-calc)
- r_multiple_distribution: vectorized correctness; length mismatch error
- r_multiple_mean_ci_stationary_bootstrap: point estimate; deterministic
  rng; CI coverage on synthetic data with known mean; excludes_zero /
  excludes_half flags; small-n error.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.inference.r_multiple import (
    RMultipleMeanCI,
    r_multiple_distribution,
    r_multiple_from_trade,
    r_multiple_mean_ci_stationary_bootstrap,
)


# ---------------------------------------------------------------------------
# r_multiple_from_trade
# ---------------------------------------------------------------------------


def test_r_multiple_from_trade_unit_winner() -> None:
    """A trade that closed at +1R returns R=1.0."""
    # ES 1 contract, stop at 10 points, multiplier 50 → 1R = $500
    # P/L of +$500 → R = 1.0
    r = r_multiple_from_trade(
        500.0, stop_loss_distance=10.0, position_size=1, multiplier=50.0
    )
    assert r == pytest.approx(1.0)


def test_r_multiple_from_trade_unit_loser() -> None:
    """A trade that closed at -1R returns R=-1.0."""
    r = r_multiple_from_trade(
        -500.0, stop_loss_distance=10.0, position_size=1, multiplier=50.0
    )
    assert r == pytest.approx(-1.0)


def test_r_multiple_from_trade_2r_winner() -> None:
    """A trade that closed at +2R returns R=2.0."""
    r = r_multiple_from_trade(
        1000.0, stop_loss_distance=10.0, position_size=1, multiplier=50.0
    )
    assert r == pytest.approx(2.0)


def test_r_multiple_from_trade_position_size_scaling() -> None:
    """Doubling position_size halves R for the same realized P/L."""
    r1 = r_multiple_from_trade(
        500.0, stop_loss_distance=10.0, position_size=1, multiplier=50.0
    )
    r2 = r_multiple_from_trade(
        500.0, stop_loss_distance=10.0, position_size=2, multiplier=50.0
    )
    assert r2 == pytest.approx(r1 / 2.0)


def test_r_multiple_from_trade_breakeven() -> None:
    """Zero realized P/L returns R=0."""
    r = r_multiple_from_trade(
        0.0, stop_loss_distance=10.0, position_size=1, multiplier=50.0
    )
    assert r == 0.0


def test_r_multiple_from_trade_zero_stop_raises() -> None:
    with pytest.raises(ValueError, match="non-positive"):
        r_multiple_from_trade(
            500.0, stop_loss_distance=0.0, position_size=1, multiplier=50.0
        )


def test_r_multiple_from_trade_zero_position_raises() -> None:
    with pytest.raises(ValueError, match="non-positive"):
        r_multiple_from_trade(
            500.0, stop_loss_distance=10.0, position_size=0, multiplier=50.0
        )


def test_r_multiple_from_trade_zero_multiplier_raises() -> None:
    with pytest.raises(ValueError, match="non-positive"):
        r_multiple_from_trade(
            500.0, stop_loss_distance=10.0, position_size=1, multiplier=0.0
        )


# ---------------------------------------------------------------------------
# r_multiple_distribution
# ---------------------------------------------------------------------------


def test_r_multiple_distribution_vectorized_matches_scalar() -> None:
    pnls = np.array([500.0, -500.0, 1000.0, 250.0])
    stops = np.array([10.0, 10.0, 10.0, 10.0])
    sizes = np.array([1, 1, 1, 1])
    expected = np.array([1.0, -1.0, 2.0, 0.5])
    result = r_multiple_distribution(pnls, stops, sizes, multiplier=50.0)
    np.testing.assert_allclose(result, expected)


def test_r_multiple_distribution_empty_input_returns_empty() -> None:
    result = r_multiple_distribution(np.array([]), np.array([]), np.array([]), multiplier=50.0)
    assert result.shape == (0,)


def test_r_multiple_distribution_length_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="Length mismatch"):
        r_multiple_distribution(
            np.array([1.0, 2.0]), np.array([10.0]), np.array([1, 1]), multiplier=50.0
        )


def test_r_multiple_distribution_zero_one_r_raises() -> None:
    with pytest.raises(ValueError, match="non-positive 1R"):
        r_multiple_distribution(
            np.array([500.0, 500.0]),
            np.array([10.0, 0.0]),  # second trade has zero stop
            np.array([1, 1]),
            multiplier=50.0,
        )


# ---------------------------------------------------------------------------
# r_multiple_mean_ci_stationary_bootstrap
# ---------------------------------------------------------------------------


def test_r_multiple_mean_ci_basic_returns_dataclass() -> None:
    rng = np.random.default_rng(42)
    rm = rng.normal(loc=0.5, scale=1.0, size=100)
    result = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=200)
    assert isinstance(result, RMultipleMeanCI)
    assert result.point_estimate == pytest.approx(rm.mean())
    assert result.ci_lower < result.ci_upper
    assert result.n_bootstrap == 200
    assert result.rng_seed == 20260508


def test_r_multiple_mean_ci_deterministic_under_fixed_seed() -> None:
    rng = np.random.default_rng(42)
    rm = rng.normal(loc=0.5, scale=1.0, size=100)
    a = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=200, rng_seed=99)
    b = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=200, rng_seed=99)
    assert a.ci_lower == b.ci_lower
    assert a.ci_upper == b.ci_upper


def test_r_multiple_mean_ci_excludes_zero_strong_positive_signal() -> None:
    """Mean R-multiple with mean=2.0 and small noise → CI should exclude zero."""
    rng = np.random.default_rng(123)
    rm = rng.normal(loc=2.0, scale=0.5, size=200)
    result = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=500)
    assert result.excludes_zero
    assert result.ci_lower > 0.0


def test_r_multiple_mean_ci_excludes_half_when_mean_is_one() -> None:
    """Mean R-multiple with mean=1.0 and small noise → CI should exclude 0.5."""
    rng = np.random.default_rng(123)
    rm = rng.normal(loc=1.0, scale=0.3, size=300)
    result = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=500)
    assert result.excludes_half  # mean is well above 0.5


def test_r_multiple_mean_ci_does_not_exclude_zero_under_null() -> None:
    """Mean R-multiple with mean=0 (null) → CI typically covers zero."""
    rng = np.random.default_rng(456)
    rm = rng.normal(loc=0.0, scale=1.0, size=200)
    result = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=500)
    assert not result.excludes_zero  # CI covers zero under the null


def test_r_multiple_mean_ci_small_n_raises() -> None:
    with pytest.raises(ValueError, match="n >= 4"):
        r_multiple_mean_ci_stationary_bootstrap(np.array([0.5, 1.0, -0.3]), n_bootstrap=100)


def test_r_multiple_mean_ci_invalid_confidence_raises() -> None:
    rm = np.array([0.5, 1.0, -0.3, 0.7, 1.5])
    with pytest.raises(ValueError, match="confidence must be"):
        r_multiple_mean_ci_stationary_bootstrap(rm, confidence=1.5)


def test_r_multiple_mean_ci_invalid_n_bootstrap_raises() -> None:
    rm = np.array([0.5, 1.0, -0.3, 0.7, 1.5])
    with pytest.raises(ValueError, match="n_bootstrap must be"):
        r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=0)


def test_r_multiple_mean_ci_provenance_fields() -> None:
    """Per Round-1 audit F-6: block_length_method exposed in dataclass."""
    rng = np.random.default_rng(42)
    rm = rng.normal(0.5, 1.0, size=100)
    auto = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=200)
    assert auto.block_length_method == "politis_white_2004"

    forced = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=200, block_length=3.0)
    assert forced.block_length_method == "operator_supplied"
    assert forced.block_length == 3.0


def test_r_multiple_mean_ci_underpowered_at_n_below_30() -> None:
    """Per Round-1 audit F-7: underpowered=True when n < 30 trades."""
    rng = np.random.default_rng(42)
    # n=20 trades — below the 30-trade operator-canonical threshold
    rm_small = rng.normal(0.5, 1.0, size=20)
    result_small = r_multiple_mean_ci_stationary_bootstrap(rm_small, n_bootstrap=200)
    assert result_small.underpowered is True

    # n=50 trades — above the threshold
    rm_large = rng.normal(0.5, 1.0, size=50)
    result_large = r_multiple_mean_ci_stationary_bootstrap(rm_large, n_bootstrap=200)
    assert result_large.underpowered is False


def test_r_multiple_mean_ci_n_29_is_underpowered() -> None:
    """Boundary check: n=29 → underpowered (strict <30 threshold)."""
    rng = np.random.default_rng(42)
    rm = rng.normal(0.5, 1.0, size=29)
    result = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=100)
    assert result.underpowered is True


def test_r_multiple_mean_ci_n_30_is_not_underpowered() -> None:
    """Boundary check: n=30 → not underpowered."""
    rng = np.random.default_rng(42)
    rm = rng.normal(0.5, 1.0, size=30)
    result = r_multiple_mean_ci_stationary_bootstrap(rm, n_bootstrap=100)
    assert result.underpowered is False
