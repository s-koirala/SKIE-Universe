"""Unit tests for H055 Component 4 ATR + Wilder smoothing.

Per H055 design.md §3 + §5.4 + Wilder 1978 *practitioner*.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.features.h055.atr import atr_wilder, true_range


def test_true_range_first_bar_is_high_minus_low() -> None:
    h = np.array([100.0])
    l = np.array([95.0])
    c = np.array([98.0])
    tr = true_range(h, l, c)
    assert tr.shape == (1,)
    assert tr[0] == 5.0


def test_true_range_uses_max_of_three_components() -> None:
    # Bar 0: h=100, l=95, c=99
    # Bar 1: h=102, l=98, c=101 → TR_1 = max(102-98, |102-99|, |98-99|) = max(4, 3, 1) = 4
    # Bar 2: h=99,  l=94, c=95  → TR_2 = max(99-94,  |99-101|, |94-101|) = max(5, 2, 7) = 7
    h = np.array([100.0, 102.0, 99.0])
    l = np.array([95.0, 98.0, 94.0])
    c = np.array([99.0, 101.0, 95.0])
    tr = true_range(h, l, c)
    assert tr[0] == 5.0
    assert tr[1] == 4.0
    assert tr[2] == 7.0


def test_true_range_validates_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="shape mismatch"):
        true_range(np.array([1.0, 2.0]), np.array([0.5]), np.array([1.5]))


def test_true_range_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        true_range(np.array([]), np.array([]), np.array([]))


def test_atr_wilder_seed_is_simple_mean_of_first_n_tr() -> None:
    # 14 identical bars: TR = h - l = 5 for each → ATR_14[13] = 5.
    h = np.full(14, 100.0)
    l = np.full(14, 95.0)
    c = np.full(14, 97.0)
    atr = atr_wilder(h, l, c, n=14)
    assert atr.shape == (14,)
    assert np.all(np.isnan(atr[:13]))
    assert atr[13] == pytest.approx(5.0)


def test_atr_wilder_recurrence_matches_closed_form() -> None:
    # Constant TR=5 for 20 bars, n=14: ATR stays at 5.0 throughout (steady state).
    h = np.full(20, 100.0)
    l = np.full(20, 95.0)
    c = np.full(20, 97.0)
    atr = atr_wilder(h, l, c, n=14)
    for t in range(13, 20):
        assert atr[t] == pytest.approx(5.0)


def test_atr_wilder_responds_to_changing_tr() -> None:
    # n=2; first 2 bars TR=10, then jump to TR=20.
    # ATR[1] = 10 (mean of TR[0], TR[1])
    # ATR[2] = 0.5*10 + 0.5*20 = 15
    # ATR[3] = 0.5*15 + 0.5*20 = 17.5
    h = np.array([10.0, 10.0, 20.0, 20.0])
    l = np.array([0.0, 0.0, 0.0, 0.0])
    c = np.array([5.0, 5.0, 10.0, 10.0])
    atr = atr_wilder(h, l, c, n=2)
    assert np.isnan(atr[0])
    assert atr[1] == pytest.approx(10.0)
    assert atr[2] == pytest.approx(15.0)
    assert atr[3] == pytest.approx(17.5)


def test_atr_wilder_rejects_n_below_one() -> None:
    h = np.array([1.0, 2.0])
    l = np.array([0.5, 1.0])
    c = np.array([0.7, 1.5])
    with pytest.raises(ValueError, match="n must be"):
        atr_wilder(h, l, c, n=0)


def test_atr_wilder_rejects_insufficient_history() -> None:
    h = np.array([1.0, 2.0])
    l = np.array([0.5, 1.0])
    c = np.array([0.7, 1.5])
    with pytest.raises(ValueError, match="insufficient history"):
        atr_wilder(h, l, c, n=14)


def test_atr_wilder_pit_safe_no_forward_leakage() -> None:
    # PIT-safe property: ATR[t] should depend only on bars [0, t].
    # Compute ATR on a panel, then truncate the panel and recompute; the
    # truncated panel's ATR series for indices [0, t_trunc] should equal
    # the full panel's first t_trunc + 1 entries.
    rng = np.random.default_rng(42)
    n_bars = 30
    h = 100.0 + np.cumsum(rng.normal(0.0, 0.5, n_bars))
    l = h - np.abs(rng.normal(2.0, 0.5, n_bars))
    c = (h + l) / 2.0 + rng.normal(0.0, 0.1, n_bars)

    atr_full = atr_wilder(h, l, c, n=14)
    for t_trunc in range(15, n_bars):
        atr_trunc = atr_wilder(h[: t_trunc + 1], l[: t_trunc + 1], c[: t_trunc + 1], n=14)
        np.testing.assert_allclose(atr_trunc, atr_full[: t_trunc + 1], rtol=1e-12)
