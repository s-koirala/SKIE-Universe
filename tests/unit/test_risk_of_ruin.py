"""Unit tests for ADR-0017 §4.2 risk-of-ruin Monte Carlo primitive.

Coverage:
- probability_of_ruin_monte_carlo: deterministic seed; positive-edge low ruin;
  negative-edge high ruin; sizing_fn callable mode (§4.1) vs fixed-fraction
  legacy mode; provenance fields; error paths.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.inference.risk_of_ruin import (
    RiskOfRuinResult,
    probability_of_ruin_monte_carlo,
)


def test_probability_of_ruin_returns_dataclass() -> None:
    rm = np.array([2.0] * 60 + [-1.0] * 40)  # positive edge
    result = probability_of_ruin_monte_carlo(rm, n_paths=200, n_sessions=50, rng_seed=42)
    assert isinstance(result, RiskOfRuinResult)
    assert 0.0 <= result.probability_of_ruin <= 1.0
    assert result.ruin_threshold_fraction == 0.5
    assert result.n_paths == 200
    assert result.n_sessions == 50
    # n_paths_ruined ↔ probability_of_ruin consistency (avoid float-precision
    # round-down by comparing the ratio rather than int-casting):
    assert result.n_paths_ruined / result.n_paths == pytest.approx(result.probability_of_ruin)


def test_probability_of_ruin_deterministic_under_fixed_seed() -> None:
    rm = np.array([2.0] * 60 + [-1.0] * 40)
    a = probability_of_ruin_monte_carlo(rm, n_paths=200, n_sessions=50, rng_seed=99)
    b = probability_of_ruin_monte_carlo(rm, n_paths=200, n_sessions=50, rng_seed=99)
    assert a.probability_of_ruin == b.probability_of_ruin
    assert a.median_terminal_equity == b.median_terminal_equity
    assert a.q05_terminal_equity == b.q05_terminal_equity


def test_probability_of_ruin_strong_positive_edge_low_ruin() -> None:
    """Strong positive edge → low ruin probability (operator-canonical safety check)."""
    rm = np.array([3.0] * 70 + [-1.0] * 30)  # mean = 1.8
    result = probability_of_ruin_monte_carlo(
        rm, kelly_fraction=0.10, n_paths=500, n_sessions=100, rng_seed=42
    )
    # Strong edge + modest sizing → very low ruin probability
    assert result.probability_of_ruin < 0.05


def test_probability_of_ruin_negative_edge_high_ruin() -> None:
    """Negative-edge distribution → high ruin probability."""
    rm = np.array([1.0] * 30 + [-1.0] * 70)  # mean = -0.4
    result = probability_of_ruin_monte_carlo(
        rm, kelly_fraction=0.25, n_paths=500, n_sessions=252, rng_seed=42
    )
    # Negative edge with aggressive sizing → high ruin probability
    assert result.probability_of_ruin > 0.5


def test_probability_of_ruin_aggressive_sizing_increases_ruin() -> None:
    """Increasing kelly_fraction monotonically increases ruin probability under
    a positive-edge distribution (variance scales with f)."""
    rm = np.array([2.0] * 60 + [-1.0] * 40)
    low = probability_of_ruin_monte_carlo(
        rm, kelly_fraction=0.10, n_paths=500, n_sessions=100, rng_seed=42
    )
    high = probability_of_ruin_monte_carlo(
        rm, kelly_fraction=0.50, n_paths=500, n_sessions=100, rng_seed=42
    )
    # Higher Kelly → larger variance → higher ruin probability (in expectation)
    assert high.probability_of_ruin >= low.probability_of_ruin


def test_probability_of_ruin_sizing_fn_mode() -> None:
    """sizing_fn callable mode (§4.1) is invoked with current equity."""
    rm = np.array([2.0] * 60 + [-1.0] * 40)

    captured_equities: list[float] = []
    def sizing_fn(equity: float) -> float:
        captured_equities.append(equity)
        return 0.10 * equity  # 10% of current equity

    result = probability_of_ruin_monte_carlo(
        rm, sizing_fn=sizing_fn, n_paths=10, n_sessions=5, rng_seed=42
    )
    assert result.sizing_mode == "survival_constrained_4_1"
    # Sizing-fn was called n_paths × n_sessions times (or until ruin/exhaustion)
    assert len(captured_equities) > 0
    # First call should be with starting_equity = $10,000
    assert captured_equities[0] == pytest.approx(10_000.0)


def test_probability_of_ruin_default_mode_provenance() -> None:
    rm = np.array([2.0] * 60 + [-1.0] * 40)
    result = probability_of_ruin_monte_carlo(rm, n_paths=100, n_sessions=10, rng_seed=42)
    assert result.sizing_mode == "fixed_fraction_of_equity"


def test_probability_of_ruin_terminal_equity_quantiles_ordering() -> None:
    rm = np.array([2.0] * 60 + [-1.0] * 40)
    result = probability_of_ruin_monte_carlo(rm, n_paths=500, n_sessions=100, rng_seed=42)
    # Quantile ordering: q01 ≤ q05 ≤ median
    assert result.q01_terminal_equity <= result.q05_terminal_equity
    assert result.q05_terminal_equity <= result.median_terminal_equity


def test_probability_of_ruin_empty_raises() -> None:
    with pytest.raises(ValueError, match="finite value"):
        probability_of_ruin_monte_carlo(np.array([]))


def test_probability_of_ruin_invalid_starting_equity_raises() -> None:
    with pytest.raises(ValueError, match="starting_equity"):
        probability_of_ruin_monte_carlo(np.array([1.0, -0.5]), starting_equity=0.0)


def test_probability_of_ruin_invalid_threshold_raises() -> None:
    with pytest.raises(ValueError, match="ruin_threshold_fraction"):
        probability_of_ruin_monte_carlo(np.array([1.0, -0.5]), ruin_threshold_fraction=1.5)


def test_probability_of_ruin_invalid_n_sessions_raises() -> None:
    with pytest.raises(ValueError, match="n_sessions"):
        probability_of_ruin_monte_carlo(np.array([1.0, -0.5]), n_sessions=0)


def test_probability_of_ruin_invalid_n_paths_raises() -> None:
    with pytest.raises(ValueError, match="n_paths"):
        probability_of_ruin_monte_carlo(np.array([1.0, -0.5]), n_paths=0)


def test_probability_of_ruin_invalid_kelly_raises() -> None:
    with pytest.raises(ValueError, match="kelly_fraction"):
        probability_of_ruin_monte_carlo(np.array([1.0, -0.5]), kelly_fraction=1.5)


def test_probability_of_ruin_catastrophic_bet_floor_classifies_as_ruin() -> None:
    """Per Round-1 audit F-2-1: when kelly_fraction × |min(R)| > 1 (catastrophic-
    bet boundary), the equity floor at 1e-12 produces equity ≈ 0 which is below
    any reasonable ruin_threshold → these paths MUST be classified as ruined.
    """
    # min(R) = -2.0; kelly_fraction = 0.6 → kelly × |min(R)| = 1.2 > 1
    # → 1 + f·R_i can go to ≤ 0 on a -2R draw, simulating bankroll wipe.
    rm = np.array([2.0] * 60 + [-2.0] * 40)
    result = probability_of_ruin_monte_carlo(
        rm, kelly_fraction=0.6, n_paths=300, n_sessions=100, rng_seed=42
    )
    # Aggressive sizing on a heavy-tail loss distribution → essentially-certain ruin
    assert result.probability_of_ruin > 0.5


def test_probability_of_ruin_vectorized_default_mode_matches_loop_mode() -> None:
    """Per Round-1 audit F-4-1: vectorized default mode must produce identical
    P(ruin) to a Python-loop reference implementation under the same seed."""
    rm = np.array([2.0] * 60 + [-1.0] * 40)
    # Default mode = vectorized
    vectorized = probability_of_ruin_monte_carlo(
        rm, kelly_fraction=0.20, n_paths=200, n_sessions=50, rng_seed=42
    )
    # sizing_fn callable mode (forces Python loop) with equivalent fixed-fraction sizing
    loop_mode = probability_of_ruin_monte_carlo(
        rm, sizing_fn=lambda eq: 0.20 * eq, n_paths=200, n_sessions=50, rng_seed=42
    )
    # Both modes use the same seed → same RNG draws → same path_r matrix → same
    # per-trade R-multiples; same kelly_fraction × equity sizing logic; the
    # only difference is float-accumulation order (cumsum vs running sum).
    # For non-catastrophic-bet inputs (no `1 + f·R ≤ 0` events) the modes are
    # mathematically identical; tolerance tightened from `abs=0.01` to `abs=1e-9`
    # per Round-2 audit F-2-1 to catch silent divergence regressions.
    assert vectorized.probability_of_ruin == pytest.approx(loop_mode.probability_of_ruin, abs=1e-9)
