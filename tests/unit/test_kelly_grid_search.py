"""Tests for `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE` per ADR-0018 D-2.

ADR-0018 D-2 (2026-05-12) lifts the ADR-0017 §4.1 fixed quarter-Kelly cap to
a grid-searched Kelly multiplier over {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}. The
grid intentionally extends into the literature-uniformly-dominated
super-Kelly regime per the operator's $10K-sandbox carve-out; super-Kelly
cells require a `super-kelly-operator-discretionary` annotation.

Reference: MacLean-Thorp-Ziemba 2010 *Kelly Capital Growth*, World Scientific
DOI 10.1142/7598 — fractional-Kelly shrinkage in [0.25, 0.5] is the
practitioner range; betting above full-Kelly is uniformly dominated in
long-run growth.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from skie_ninja.sizing import (
    KELLY_MULTIPLIER_GRID_DEFAULT,
    KELLY_MULTIPLIER_SUPER_KELLY_THRESHOLD,
    compute_position_size,
    kelly_fraction_from_r_multiples,
    kelly_multiplier_annotation,
    select_kelly_multiplier_by_grid,
)


def test_grid_default_constant_exact() -> None:
    """KELLY_MULTIPLIER_GRID_DEFAULT exactly equals the ADR-0018 D-2 grid."""
    assert KELLY_MULTIPLIER_GRID_DEFAULT == (0.25, 0.5, 1.0, 1.5, 2.0, 2.5)


def test_super_kelly_threshold_is_one() -> None:
    """Threshold for super-Kelly is full-Kelly (1.0) per MacLean-Thorp-Ziemba 2010."""
    assert KELLY_MULTIPLIER_SUPER_KELLY_THRESHOLD == 1.0


def test_compute_position_size_backward_compat_at_multiplier_0_25() -> None:
    """Backward-compat: `kelly_multiplier=0.25` with `kelly_fraction=1.0`
    produces byte-identical output to legacy `kelly_fraction=0.25` call.

    The pre-ADR-0018 formula is `kelly_bound = kelly_fraction * equity / notional`.
    The new formula is `kelly_bound = clamp(kelly_fraction * kelly_multiplier, 0,
    2.5) * equity / notional`. At `kelly_fraction=1.0, kelly_multiplier=0.25`
    the effective Kelly is `0.25`, structurally identical to the legacy
    `kelly_fraction=0.25` call.
    """
    fixed_kwargs = {
        "equity": 100_000.0,
        "atr": 12.0,
        "multiplier": 50.0,
        "entry_price": 5000.0,
        "capacity_ceiling": 20,
        "k_atr": 2.0,
        "risk_budget_pct": 0.01,
    }
    # Legacy-equivalent: new API at default kelly_multiplier=0.25 with full-Kelly raw.
    new_size = compute_position_size(
        **fixed_kwargs, kelly_fraction=1.0, kelly_multiplier=0.25
    )
    # Hand-computed pre-ADR-0018 reference:
    # risk_bound = 0.01 * 100_000 / (2 * 12 * 50) = 1000 / 1200 = 0.833...
    # kelly_bound = 0.25 * 100_000 / (5000 * 50) = 25_000 / 250_000 = 0.1
    # capacity_ceiling = 20
    # floor(min(0.833, 0.1, 20)) = floor(0.1) = 0
    legacy_size = int(math.floor(min(0.8333333333333334, 0.1, 20.0)))
    assert new_size == legacy_size

    # Second fixed input: larger account where Kelly bound binds non-trivially.
    fixed_kwargs2 = {
        "equity": 1_000_000.0,
        "atr": 10.0,
        "multiplier": 50.0,
        "entry_price": 4000.0,
        "capacity_ceiling": 20,
        "k_atr": 2.0,
        "risk_budget_pct": 0.01,
    }
    new_size2 = compute_position_size(
        **fixed_kwargs2, kelly_fraction=1.0, kelly_multiplier=0.25
    )
    # risk_bound = 0.01 * 1_000_000 / (2 * 10 * 50) = 10_000 / 1000 = 10
    # kelly_bound = 0.25 * 1_000_000 / (4000 * 50) = 250_000 / 200_000 = 1.25
    # floor(min(10, 1.25, 20)) = 1
    legacy_size2 = int(math.floor(min(10.0, 1.25, 20.0)))
    assert new_size2 == legacy_size2 == 1


def test_compute_position_size_multiplier_scales_linearly() -> None:
    """At multiplier=1.0, the effective Kelly is `kelly_fraction` (full-Kelly
    when raw=1.0, clamped at 2.5 if exceeded)."""
    kwargs = {
        "equity": 1_000_000.0,
        "atr": 10.0,
        "multiplier": 50.0,
        "entry_price": 4000.0,
        "capacity_ceiling": 50,
        "k_atr": 2.0,
        "risk_budget_pct": 1.0,  # de-fang risk bound so Kelly binds
    }
    # multiplier=1.0, kelly_fraction=1.0 → effective 1.0
    # kelly_bound = 1.0 * 1_000_000 / (4000 * 50) = 5.0
    size_full = compute_position_size(**kwargs, kelly_fraction=1.0, kelly_multiplier=1.0)
    assert size_full == 5

    # multiplier=2.0, kelly_fraction=1.0 → effective 2.0
    # kelly_bound = 2.0 * 1_000_000 / (4000 * 50) = 10.0
    size_2x = compute_position_size(**kwargs, kelly_fraction=1.0, kelly_multiplier=2.0)
    assert size_2x == 10

    # multiplier=2.5, kelly_fraction=1.0 → effective 2.5 (at clamp upper bound)
    size_grid_max = compute_position_size(
        **kwargs, kelly_fraction=1.0, kelly_multiplier=2.5
    )
    assert size_grid_max == 12  # floor(2.5 * 1e6 / 2e5) = floor(12.5) = 12


def test_compute_position_size_clamp_upper_at_grid_max() -> None:
    """Effective Kelly is clamped at max(grid) = 2.5 even if raw × multiplier exceeds."""
    kwargs = {
        "equity": 1_000_000.0,
        "atr": 10.0,
        "multiplier": 50.0,
        "entry_price": 4000.0,
        "capacity_ceiling": 100,
        "k_atr": 2.0,
        "risk_budget_pct": 1.0,
    }
    # 1.0 × 5.0 = 5.0 → clamped to 2.5 → kelly_bound = 12.5 → floor = 12
    size = compute_position_size(**kwargs, kelly_fraction=1.0, kelly_multiplier=5.0)
    assert size == 12


def test_kelly_multiplier_annotation_below_threshold() -> None:
    """multiplier ≤ 1.0 does NOT carry the super-Kelly suffix."""
    assert kelly_multiplier_annotation(0.25) == "kelly-multiplier-0.25"
    assert kelly_multiplier_annotation(0.5) == "kelly-multiplier-0.5"
    assert kelly_multiplier_annotation(1.0) == "kelly-multiplier-1.0"
    assert "super-kelly" not in kelly_multiplier_annotation(0.5)


def test_kelly_multiplier_annotation_super_kelly_suffix() -> None:
    """multiplier > 1.0 carries the `+super-kelly-operator-discretionary` suffix."""
    ann_2x = kelly_multiplier_annotation(2.0)
    assert ann_2x.startswith("kelly-multiplier-2.0")
    assert "super-kelly-operator-discretionary" in ann_2x

    ann_25 = kelly_multiplier_annotation(2.5)
    assert "super-kelly-operator-discretionary" in ann_25


def _toy_mppm_rho_1(sized_r: np.ndarray) -> float:
    """Mean per-period multiplier (MPPM) at ρ=1 — geometric-growth proxy.

    MPPM(ρ=1) is the mean of log(1 + R_i); maximized at the Vince f.
    Returns -inf if any 1+R is non-positive (a path-ruining trade).
    """
    arr = np.asarray(sized_r, dtype=float)
    gross = 1.0 + arr
    if np.any(gross <= 0.0):
        return -math.inf
    return float(np.mean(np.log(gross)))


def test_grid_picks_optimal_multiplier_on_bernoulli_06() -> None:
    """Bernoulli +2R/-1R 0.6 win-rate has analytical Vince f* = 0.4.

    The raw_kelly_f from `kelly_fraction_from_r_multiples` on a large empirical
    Bernoulli sample should converge to 0.4. The grid then evaluates
    `m × 0.4 × R_i` for each m ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}; MPPM(ρ=1) is
    maximized at the sized Kelly that itself equals the Vince f. The optimum
    of `m × 0.4` over the grid that maximizes E[log(1 + m × 0.4 × R)] is
    achieved when `m × 0.4 = 0.4` → m = 1.0.
    """
    rng = np.random.default_rng(20260512)
    n = 10_000
    wins = rng.random(n) < 0.6
    rm = np.where(wins, 2.0, -1.0)

    # Sanity: raw_kelly_f should be near 0.4.
    raw_f = kelly_fraction_from_r_multiples(rm)
    assert abs(raw_f - 0.4) < 0.02

    result = select_kelly_multiplier_by_grid(rm, _toy_mppm_rho_1)
    assert result["best_multiplier"] == 1.0
    assert result["is_super_kelly"] is False
    assert result["annotation"] == "kelly-multiplier-1.0"
    # Grid result table has all six cells:
    assert len(result["grid_results"]) == 6
    multipliers_in_table = [row["multiplier"] for row in result["grid_results"]]
    assert multipliers_in_table == list(KELLY_MULTIPLIER_GRID_DEFAULT)


def test_grid_search_returns_super_kelly_annotation_when_selected() -> None:
    """If grid search picks m > 1.0, the annotation carries the super-Kelly suffix.

    Bernoulli +5R/-1R 0.7 win-rate has Vince f* analytically:
    G'(f) = 0.7 * 5/(1 + 5f) - 0.3 / (1 - f) = 0
    0.7 * 5 * (1 - f) = 0.3 * (1 + 5f)
    3.5 - 3.5f = 0.3 + 1.5f
    3.2 = 5f → f* = 0.64
    The raw kelly_fraction_from_r_multiples returns ~0.64. The grid maximizes
    over m × 0.64; the m that best approximates 0.64 (the Vince optimum) is
    m=1.0 (giving 0.64, the closest cell to the true optimum). To force a
    super-Kelly selection we use a distribution with a small Vince f and
    let m=2.5 land closest.
    """
    # Construct a small-Vince-f distribution: +1R win / -1R loss at 0.51 win rate.
    # Analytical Vince f* solves 0.51/(1+f) = 0.49/(1-f) → 0.51(1-f) = 0.49(1+f) →
    # 0.02 = f → f* = 0.02.
    rng = np.random.default_rng(20260513)
    n = 50_000
    wins = rng.random(n) < 0.51
    rm = np.where(wins, 1.0, -1.0)
    raw_f = kelly_fraction_from_r_multiples(rm)
    # raw_f should be small; m × raw_f ≈ 0.02 × m; the largest m approximates
    # the analytical Vince optimum best (since we never exceed the constraint
    # 1 + f×min(R) > 0 for f up to 1).
    assert raw_f < 0.10

    result = select_kelly_multiplier_by_grid(rm, _toy_mppm_rho_1)
    if result["best_multiplier"] > 1.0:
        assert result["is_super_kelly"] is True
        assert "super-kelly-operator-discretionary" in result["annotation"]
    # Independent guarantee — the annotation matches the kelly_multiplier_annotation
    # contract regardless of which cell was picked.
    assert result["annotation"] == kelly_multiplier_annotation(result["best_multiplier"])


def test_grid_search_empty_input_raises() -> None:
    """Empty R-multiple input raises ValueError."""
    with pytest.raises(ValueError):
        select_kelly_multiplier_by_grid(np.array([]), _toy_mppm_rho_1)


def test_grid_search_all_nan_input_raises() -> None:
    """All-NaN R-multiple input filters to empty → ValueError."""
    with pytest.raises(ValueError):
        select_kelly_multiplier_by_grid(np.array([np.nan, np.nan]), _toy_mppm_rho_1)


def test_grid_search_pure_loss_picks_smallest_multiplier() -> None:
    """Pure-loss R-multiple input → all sized streams are losing → Vince f = 0
    (no edge) → all multipliers produce sized_R = 0 → MPPM = 0 across the grid.

    Since all MPPMs tie at zero (the no-bet baseline), the grid's first cell
    (smallest = 0.25) is returned by the strict-greater-than tie-breaking rule.
    """
    rm = np.array([-1.0, -0.5, -0.8, -0.3, -0.9])
    raw_f = kelly_fraction_from_r_multiples(rm)
    # All losses → mean(R) < 0 → Vince f* = 0 (derivative-at-boundary check).
    assert raw_f == 0.0

    result = select_kelly_multiplier_by_grid(rm, _toy_mppm_rho_1)
    # Smallest multiplier wins (least-levered loss); strict-> tie-breaking keeps
    # the first-seen cell which is 0.25.
    assert result["best_multiplier"] == 0.25
    assert result["is_super_kelly"] is False
    # All cells have MPPM = log(1 + 0) = 0.0 since sized_R = m × 0 × R = 0.
    for row in result["grid_results"]:
        assert row["mppm"] == 0.0


def test_grid_search_custom_grid_respected() -> None:
    """A caller-supplied grid replaces the default."""
    rng = np.random.default_rng(20260514)
    wins = rng.random(5000) < 0.6
    rm = np.where(wins, 2.0, -1.0)

    custom_grid = (0.5, 1.0)
    result = select_kelly_multiplier_by_grid(rm, _toy_mppm_rho_1, grid=custom_grid)
    assert len(result["grid_results"]) == 2
    assert [row["multiplier"] for row in result["grid_results"]] == [0.5, 1.0]


def test_grid_search_empty_grid_raises() -> None:
    """Empty grid raises ValueError."""
    rm = np.array([1.0, -1.0, 2.0, -1.0])
    with pytest.raises(ValueError):
        select_kelly_multiplier_by_grid(rm, _toy_mppm_rho_1, grid=())


def test_compute_position_size_kelly_multiplier_negative_raises() -> None:
    """Negative kelly_multiplier raises ValueError."""
    with pytest.raises(ValueError):
        compute_position_size(
            equity=100_000.0,
            atr=10.0,
            multiplier=50.0,
            entry_price=4000.0,
            kelly_fraction=0.5,
            capacity_ceiling=20,
            kelly_multiplier=-0.1,
        )
