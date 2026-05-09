"""Unit tests for H055 Component 2 body-overlap ρ_1."""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.features.h055.body_overlap import (
    body_interval,
    body_overlap_rho_1,
    pairwise_jaccard,
)


# ─── body_interval ───────────────────────────────────────────────────────────


def test_body_interval_bullish() -> None:
    # Bullish bar: open < close → interval = (open, close)
    assert body_interval(100.0, 105.0) == (100.0, 105.0)


def test_body_interval_bearish() -> None:
    assert body_interval(105.0, 100.0) == (100.0, 105.0)


def test_body_interval_doji() -> None:
    # open == close → zero-length body
    assert body_interval(100.0, 100.0) == (100.0, 100.0)


# ─── pairwise_jaccard ────────────────────────────────────────────────────────


def test_jaccard_identical_intervals_returns_one() -> None:
    assert pairwise_jaccard((100.0, 105.0), (100.0, 105.0)) == 1.0


def test_jaccard_disjoint_intervals_returns_zero() -> None:
    assert pairwise_jaccard((100.0, 105.0), (110.0, 115.0)) == 0.0


def test_jaccard_partial_overlap() -> None:
    # A = [100, 110], B = [105, 115]; intersection [105, 110] = 5; union [100, 115] = 15
    # Jaccard = 5/15 = 1/3
    assert pairwise_jaccard((100.0, 110.0), (105.0, 115.0)) == pytest.approx(1.0 / 3.0)


def test_jaccard_a_contains_b() -> None:
    # A = [100, 120], B = [105, 110]; intersection = B = 5; union = A = 20
    # Jaccard = 5/20 = 0.25
    assert pairwise_jaccard((100.0, 120.0), (105.0, 110.0)) == 0.25


def test_jaccard_zero_length_identical() -> None:
    # Both zero-length at same price → identical (degenerate Jaccard limit).
    assert pairwise_jaccard((100.0, 100.0), (100.0, 100.0)) == 1.0


def test_jaccard_zero_length_distinct() -> None:
    # Both zero-length at different prices → 0.
    assert pairwise_jaccard((100.0, 100.0), (101.0, 101.0)) == 0.0


def test_jaccard_rejects_inverted_interval() -> None:
    with pytest.raises(ValueError, match="low <= high"):
        pairwise_jaccard((105.0, 100.0), (100.0, 105.0))


# ─── body_overlap_rho_1 ──────────────────────────────────────────────────────


def test_rho_1_all_identical_bodies_returns_one() -> None:
    # 10 bars with identical bodies → ρ_1 = 1.0 for all eligible bars.
    o = np.full(10, 100.0)
    c = np.full(10, 105.0)
    rho = body_overlap_rho_1(o, c, window_n=5)
    assert np.all(np.isnan(rho[:4]))
    assert np.all(rho[4:] == pytest.approx(1.0))


def test_rho_1_all_disjoint_bodies_returns_zero() -> None:
    # Bodies sliding through disjoint price levels.
    o = np.array([100.0, 110.0, 120.0, 130.0, 140.0])
    c = np.array([105.0, 115.0, 125.0, 135.0, 145.0])
    rho = body_overlap_rho_1(o, c, window_n=5)
    assert rho[4] == 0.0


def test_rho_1_partial_overlap_canonical() -> None:
    # 2-bar window with 50% overlap. Bar 0: [100, 110]; bar 1: [105, 115].
    # ρ_1 with 1 pair = Jaccard([100, 110], [105, 115]) = 5/15 = 1/3.
    o = np.array([100.0, 105.0])
    c = np.array([110.0, 115.0])
    rho = body_overlap_rho_1(o, c, window_n=2)
    assert np.isnan(rho[0])
    assert rho[1] == pytest.approx(1.0 / 3.0)


def test_rho_1_in_zero_to_one_range() -> None:
    rng = np.random.default_rng(42)
    n_bars = 30
    o = 100.0 + np.cumsum(rng.normal(0.0, 0.5, n_bars))
    c = o + rng.normal(0.0, 0.3, n_bars)
    rho = body_overlap_rho_1(o, c, window_n=5)
    assert np.all((rho[4:] >= 0.0) & (rho[4:] <= 1.0))


def test_rho_1_pit_safe() -> None:
    # PIT property: ρ_1[t] depends only on bars [t-N+1, t]; truncating the
    # panel at any t and recomputing should give identical values for [0, t].
    rng = np.random.default_rng(42)
    n_bars = 30
    o = 100.0 + np.cumsum(rng.normal(0.0, 0.5, n_bars))
    c = o + rng.normal(0.0, 0.3, n_bars)
    rho_full = body_overlap_rho_1(o, c, window_n=5)
    for t_trunc in range(5, n_bars):
        rho_trunc = body_overlap_rho_1(o[: t_trunc + 1], c[: t_trunc + 1], window_n=5)
        np.testing.assert_allclose(
            rho_trunc[~np.isnan(rho_trunc)],
            rho_full[: t_trunc + 1][~np.isnan(rho_full[: t_trunc + 1])],
            rtol=1e-12,
        )


def test_rho_1_rejects_window_below_two() -> None:
    o = np.array([100.0, 105.0])
    c = np.array([105.0, 110.0])
    with pytest.raises(ValueError, match="window_n"):
        body_overlap_rho_1(o, c, window_n=1)


def test_rho_1_rejects_insufficient_history() -> None:
    o = np.array([100.0, 105.0])
    c = np.array([105.0, 110.0])
    with pytest.raises(ValueError, match="insufficient history"):
        body_overlap_rho_1(o, c, window_n=10)


def test_rho_1_rejects_shape_mismatch() -> None:
    o = np.array([100.0, 105.0, 110.0])
    c = np.array([105.0, 110.0])
    with pytest.raises(ValueError, match="shape mismatch"):
        body_overlap_rho_1(o, c, window_n=2)


def test_rho_1_pivot_search_domain_window_values() -> None:
    # H055 design.md §5.6 search domain: N ∈ {5, 7, 10, 14, 20}. Verify
    # each value runs without error on 25-bar panel.
    rng = np.random.default_rng(42)
    n_bars = 25
    o = 100.0 + np.cumsum(rng.normal(0.0, 0.5, n_bars))
    c = o + rng.normal(0.0, 0.3, n_bars)
    for window_n in (5, 7, 10, 14, 20):
        rho = body_overlap_rho_1(o, c, window_n=window_n)
        assert rho.shape == (n_bars,)
        assert np.all((rho[window_n - 1 :] >= 0.0) & (rho[window_n - 1 :] <= 1.0))
