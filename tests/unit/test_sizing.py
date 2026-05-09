"""Unit tests for ADR-0017 §4.1 survival-constrained sizing primitive.

Coverage:
- kelly_fraction_from_r_multiples: Vince 1990 optimal-f on canonical
  cases (positive-edge, negative-edge, no-loser, no-winner); empty input
  raises; mean-≤-0 returns 0.
- drawdown_constrained_kelly: bisection-by-grid finds largest f satisfying
  P(MaxDD ≤ target) ≥ confidence; deterministic; monotonicity; returns 0
  when no positive edge.
- compute_position_size: §4.1 worked-example unit-checks (ES + MES at $10K
  bankroll); error paths; capacity ceiling binding.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.sizing import (
    compute_position_size,
    drawdown_constrained_kelly,
    kelly_fraction_from_r_multiples,
)


# ---------------------------------------------------------------------------
# kelly_fraction_from_r_multiples
# ---------------------------------------------------------------------------


def test_kelly_fraction_positive_edge_returns_positive() -> None:
    """Positive-edge R-multiple distribution → optimal-f > 0.

    For 60% wins at +2R / 40% losses at -1R, the analytic optimal-f satisfies:
        dG/df = 0.6·2/(1+2f) − 0.4/(1−f) = 0
        ⟹ 1.2(1−f) = 0.4(1+2f)
        ⟹ 1.2 − 1.2f = 0.4 + 0.8f
        ⟹ f* = 0.8 / 2.0 = 0.40

    (The Round-1 audit F-5-1 finding's hand-computation was itself in error;
    the corrected analytic optimum is 0.40, which the implementation reaches.)
    """
    rm = np.array([2.0] * 60 + [-1.0] * 40)
    f = kelly_fraction_from_r_multiples(rm)
    assert 0.0 < f < 1.0
    # Analytic optimum 0.40; allow ±0.05 slack for finite-sample + scipy tolerance
    assert 0.35 < f < 0.45


def test_kelly_fraction_negative_edge_returns_zero() -> None:
    """Negative-edge R-multiple distribution → optimal-f = 0 (don't bet)."""
    rm = np.array([1.0] * 30 + [-1.0] * 70)  # mean R = -0.4
    f = kelly_fraction_from_r_multiples(rm)
    assert f == 0.0


def test_kelly_fraction_zero_edge_returns_zero() -> None:
    """Mean R = 0 (no edge) → optimal-f = 0."""
    rm = np.array([1.0, -1.0, 1.0, -1.0])  # mean exactly 0
    f = kelly_fraction_from_r_multiples(rm)
    assert f == 0.0


def test_kelly_fraction_no_losers_returns_one() -> None:
    """All R ≥ 0 (no losing trades) → unbounded TWR; return 1.0 (caller clamps)."""
    rm = np.array([1.0, 2.0, 0.5, 0.0])
    f = kelly_fraction_from_r_multiples(rm)
    assert f == 1.0


def test_kelly_fraction_empty_raises() -> None:
    with pytest.raises(ValueError, match="finite value"):
        kelly_fraction_from_r_multiples(np.array([]))


def test_kelly_fraction_all_nan_raises() -> None:
    with pytest.raises(ValueError, match="finite value"):
        kelly_fraction_from_r_multiples(np.array([np.nan, np.inf, -np.inf]))


def test_kelly_fraction_robust_to_extreme_loser() -> None:
    """A single -2R trade caps f_upper = 0.5 (1/|min(R)|); algorithm respects this."""
    rm = np.array([1.5, 1.0, 0.5, -2.0, 0.8])  # mean ≈ 0.36, min = -2.0
    f = kelly_fraction_from_r_multiples(rm)
    # Constraint: f < 0.5; optimal should be strictly below.
    assert 0.0 < f < 0.5


# ---------------------------------------------------------------------------
# drawdown_constrained_kelly
# ---------------------------------------------------------------------------


def test_drawdown_constrained_kelly_zero_edge_returns_zero() -> None:
    """No-edge distribution → no Kelly fraction is justifiable."""
    rm = np.array([1.0] * 50 + [-1.0] * 50)  # mean = 0
    f = drawdown_constrained_kelly(rm, n_paths=200, n_sessions=100)
    # Even f=0 trivially satisfies constraint (no trading → no DD); algorithm
    # finds best_f ≥ 0; with mean-zero, larger f means symmetric DD risk.
    # Accept any f in [0, 0.25] — but typically near 0 due to symmetric losses.
    assert 0.0 <= f <= 0.25


def test_drawdown_constrained_kelly_strong_edge_returns_capped() -> None:
    """Strong-edge distribution + lenient DD constraint → f near kelly_cap."""
    # 80% win at +2R, 20% loss at -1R → mean = 1.4
    rm = np.array([2.0] * 80 + [-1.0] * 20)
    f = drawdown_constrained_kelly(
        rm, max_dd_target=0.50, confidence=0.95, n_paths=500, n_sessions=100, kelly_cap=0.25
    )
    # Strong edge with lenient 50% DD constraint should allow near-cap f.
    assert f >= 0.10  # at least some sizing


def test_drawdown_constrained_kelly_strict_dd_returns_smaller() -> None:
    """Tightening DD target → smaller Kelly."""
    rm = np.array([2.0] * 60 + [-1.0] * 40)  # mean = 0.8
    f_lenient = drawdown_constrained_kelly(
        rm, max_dd_target=0.50, confidence=0.95, n_paths=500, n_sessions=100, rng_seed=42
    )
    f_strict = drawdown_constrained_kelly(
        rm, max_dd_target=0.10, confidence=0.95, n_paths=500, n_sessions=100, rng_seed=42
    )
    assert f_strict <= f_lenient


def test_drawdown_constrained_kelly_deterministic() -> None:
    rm = np.array([2.0] * 60 + [-1.0] * 40)
    a = drawdown_constrained_kelly(rm, n_paths=500, n_sessions=100, rng_seed=99)
    b = drawdown_constrained_kelly(rm, n_paths=500, n_sessions=100, rng_seed=99)
    assert a == b


def test_drawdown_constrained_kelly_invalid_max_dd_raises() -> None:
    rm = np.array([1.0, -0.5])
    with pytest.raises(ValueError, match="max_dd_target"):
        drawdown_constrained_kelly(rm, max_dd_target=1.5)


def test_drawdown_constrained_kelly_invalid_confidence_raises() -> None:
    rm = np.array([1.0, -0.5])
    with pytest.raises(ValueError, match="confidence"):
        drawdown_constrained_kelly(rm, confidence=0.0)


def test_drawdown_constrained_kelly_zero_cap_returns_zero() -> None:
    rm = np.array([1.0, -0.5])
    f = drawdown_constrained_kelly(rm, kelly_cap=0.0)
    assert f == 0.0


# ---------------------------------------------------------------------------
# compute_position_size
# ---------------------------------------------------------------------------


def test_compute_position_size_es_at_10k_bankroll_zero_contracts() -> None:
    """ADR-0017 §4.1 worked example: ES at $10K, multiplier=50 → 0 contracts.

    Risk-budget bound: 100 / (2 × 25 × 50) = 0.04 contracts.
    Kelly bound: 0.25 × 10000 / (5000 × 50) = 0.01 contracts.
    floor(min(0.04, 0.01, 20)) = 0.
    """
    n = compute_position_size(
        equity=10_000.0,
        atr=25.0,
        multiplier=50.0,
        entry_price=5000.0,
        kelly_fraction=0.25,
        capacity_ceiling=20,
    )
    assert n == 0


def test_compute_position_size_mes_at_10k_bankroll_zero_contracts() -> None:
    """MES at $10K: risk-budget=0.4 contracts, Kelly=0.1 contracts → 0."""
    n = compute_position_size(
        equity=10_000.0,
        atr=25.0,
        multiplier=5.0,
        entry_price=5000.0,
        kelly_fraction=0.25,
        capacity_ceiling=200,
    )
    assert n == 0


def test_compute_position_size_mes_at_50k_kelly_binds_zero() -> None:
    """MES at $50K: risk-budget=2 contracts, Kelly=0.5 contracts → 0 contracts (Kelly binds).

    Per Round-1 audit F-5-2: test renamed from `..._one_contract` → `..._kelly_binds_zero`
    to match the asserted outcome (n == 0; Kelly bound binds at 0.5 → floor = 0).
    """
    n = compute_position_size(
        equity=50_000.0,
        atr=25.0,
        multiplier=5.0,
        entry_price=5000.0,
        kelly_fraction=0.25,
        capacity_ceiling=200,
    )
    # Kelly bound = 0.25 × 50000 / (5000 × 5) = 12500/25000 = 0.5 → floor = 0
    assert n == 0


def test_compute_position_size_mes_at_100k_bankroll_one_contract() -> None:
    """MES at $100K: Kelly bound = 0.25*100000 / 25000 = 1.0 → 1 contract."""
    n = compute_position_size(
        equity=100_000.0,
        atr=25.0,
        multiplier=5.0,
        entry_price=5000.0,
        kelly_fraction=0.25,
        capacity_ceiling=200,
    )
    # Risk-budget bound = 1000/250 = 4.0 contracts; Kelly = 1.0 → floor = 1
    assert n == 1


def test_compute_position_size_capacity_ceiling_binds() -> None:
    """Capacity ceiling binds when both other bounds are larger.

    For ES at $10M equity with kelly_fraction=1.0:
    - risk-budget bound = 100,000 / 250 = 400 contracts
    - Kelly bound      = 1.0 × 10M / 25,000 = 400 contracts
    - capacity         = 200 contracts
    → min = 200; capacity binds.
    """
    n = compute_position_size(
        equity=10_000_000.0,
        atr=25.0,
        multiplier=5.0,
        entry_price=5000.0,
        kelly_fraction=1.0,
        capacity_ceiling=200,
    )
    assert n == 200


def test_compute_position_size_zero_kelly_returns_zero() -> None:
    """kelly_fraction=0 → Kelly bound = 0 → floor = 0."""
    n = compute_position_size(
        equity=100_000.0,
        atr=25.0,
        multiplier=5.0,
        entry_price=5000.0,
        kelly_fraction=0.0,
        capacity_ceiling=200,
    )
    assert n == 0


def test_compute_position_size_negative_equity_raises() -> None:
    with pytest.raises(ValueError, match="equity"):
        compute_position_size(
            equity=-100.0, atr=25.0, multiplier=5.0, entry_price=5000.0,
            kelly_fraction=0.25, capacity_ceiling=200,
        )


def test_compute_position_size_negative_atr_raises() -> None:
    with pytest.raises(ValueError, match="atr"):
        compute_position_size(
            equity=10_000.0, atr=-1.0, multiplier=5.0, entry_price=5000.0,
            kelly_fraction=0.25, capacity_ceiling=200,
        )


def test_compute_position_size_invalid_kelly_raises() -> None:
    with pytest.raises(ValueError, match="kelly_fraction"):
        compute_position_size(
            equity=10_000.0, atr=25.0, multiplier=5.0, entry_price=5000.0,
            kelly_fraction=1.5, capacity_ceiling=200,
        )


def test_compute_position_size_negative_capacity_raises() -> None:
    with pytest.raises(ValueError, match="capacity_ceiling"):
        compute_position_size(
            equity=10_000.0, atr=25.0, multiplier=5.0, entry_price=5000.0,
            kelly_fraction=0.25, capacity_ceiling=-1,
        )
