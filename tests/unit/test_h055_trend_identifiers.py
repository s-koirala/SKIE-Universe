"""Unit tests for H055 Component 1 trend identifiers (a/b/c/d)."""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.features.h055.trend_identifiers import (
    trend_id_a_ts_mom,
    trend_id_b_adx,
    trend_id_c_hac_ols_slope_t,
    trend_id_d_ma_cross,
)


def _build_uptrend_log_prices(n: int = 100, drift: float = 0.001, sigma: float = 0.0001, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.normal(drift, sigma, n)) + 5.0  # log price near log(150)


def _build_downtrend_log_prices(n: int = 100, drift: float = -0.001, sigma: float = 0.0001, seed: int = 42) -> np.ndarray:
    return _build_uptrend_log_prices(n=n, drift=drift, sigma=sigma, seed=seed)


def _build_flat_log_prices(n: int = 100, sigma: float = 0.001, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.normal(0.0, sigma, n)) + 5.0


# ─── ID-a: TS-mom ────────────────────────────────────────────────────────────


def test_id_a_uptrend_returns_positive_side() -> None:
    p = _build_uptrend_log_prices(n=100)
    sides = trend_id_a_ts_mom(p, lookback_l=20, tau_m=1.0)
    assert sides.shape == (100,)
    # Most bars after lookback should detect the upward drift
    n_positive = (sides[20:] == 1).sum()
    n_negative = (sides[20:] == -1).sum()
    assert n_positive > n_negative


def test_id_a_downtrend_returns_negative_side() -> None:
    p = _build_downtrend_log_prices(n=100)
    sides = trend_id_a_ts_mom(p, lookback_l=20, tau_m=1.0)
    n_positive = (sides[20:] == 1).sum()
    n_negative = (sides[20:] == -1).sum()
    assert n_negative > n_positive


def test_id_a_flat_with_high_threshold_returns_zero() -> None:
    p = _build_flat_log_prices(n=100)
    sides = trend_id_a_ts_mom(p, lookback_l=20, tau_m=5.0)  # very high threshold
    # Most bars should be zero
    assert (sides == 0).sum() > 80


def test_id_a_validates_lookback() -> None:
    p = np.linspace(5.0, 5.5, 30)
    with pytest.raises(ValueError, match="lookback_l"):
        trend_id_a_ts_mom(p, lookback_l=0, tau_m=1.0)


def test_id_a_rejects_insufficient_history() -> None:
    p = np.linspace(5.0, 5.1, 10)
    with pytest.raises(ValueError, match="insufficient history"):
        trend_id_a_ts_mom(p, lookback_l=20, tau_m=1.0)


def test_id_a_pit_safe() -> None:
    p = _build_uptrend_log_prices(n=100)
    sides_full = trend_id_a_ts_mom(p, lookback_l=20, tau_m=1.0)
    for t_trunc in range(50, 100, 10):
        sides_trunc = trend_id_a_ts_mom(p[: t_trunc + 1], lookback_l=20, tau_m=1.0)
        np.testing.assert_array_equal(sides_trunc, sides_full[: t_trunc + 1])


# ─── ID-b: ADX ───────────────────────────────────────────────────────────────


def test_id_b_uptrend_detects_positive_side() -> None:
    rng = np.random.default_rng(42)
    n = 100
    drift = 0.5
    sigma = 0.1
    close = 100.0 + drift * np.arange(n) + rng.normal(0.0, sigma, n)
    high = close + np.abs(rng.normal(0.5, 0.2, n))
    low = close - np.abs(rng.normal(0.5, 0.2, n))
    sides = trend_id_b_adx(high, low, close, lookback_l=14, tau_adx=15.0)
    assert sides.shape == (n,)
    # ADX takes long to warm up; check the second half.
    n_positive = (sides[60:] == 1).sum()
    n_negative = (sides[60:] == -1).sum()
    assert n_positive > n_negative


def test_id_b_downtrend_detects_negative_side() -> None:
    rng = np.random.default_rng(42)
    n = 100
    drift = -0.5
    sigma = 0.1
    close = 100.0 + drift * np.arange(n) + rng.normal(0.0, sigma, n)
    high = close + np.abs(rng.normal(0.5, 0.2, n))
    low = close - np.abs(rng.normal(0.5, 0.2, n))
    sides = trend_id_b_adx(high, low, close, lookback_l=14, tau_adx=15.0)
    n_positive = (sides[60:] == 1).sum()
    n_negative = (sides[60:] == -1).sum()
    assert n_negative > n_positive


def test_id_b_validates_lookback() -> None:
    h = np.full(50, 100.0)
    l = np.full(50, 95.0)
    c = np.full(50, 97.0)
    with pytest.raises(ValueError, match="lookback_l"):
        trend_id_b_adx(h, l, c, lookback_l=1, tau_adx=20.0)


def test_id_b_rejects_insufficient_history() -> None:
    h = np.full(20, 100.0)
    l = np.full(20, 95.0)
    c = np.full(20, 97.0)
    with pytest.raises(ValueError, match="insufficient history"):
        trend_id_b_adx(h, l, c, lookback_l=14, tau_adx=20.0)


# ─── ID-c: HAC-OLS-slope-t ───────────────────────────────────────────────────


def test_id_c_strong_uptrend_returns_positive_side() -> None:
    p = _build_uptrend_log_prices(n=100, drift=0.005, sigma=0.0001)
    sides = trend_id_c_hac_ols_slope_t(p, lookback_l=20, tau_t=2.0)
    n_positive = (sides[20:] == 1).sum()
    n_negative = (sides[20:] == -1).sum()
    assert n_positive > n_negative


def test_id_c_strong_downtrend_returns_negative_side() -> None:
    p = _build_downtrend_log_prices(n=100, drift=-0.005, sigma=0.0001)
    sides = trend_id_c_hac_ols_slope_t(p, lookback_l=20, tau_t=2.0)
    n_positive = (sides[20:] == 1).sum()
    n_negative = (sides[20:] == -1).sum()
    assert n_negative > n_positive


def test_id_c_flat_with_high_t_threshold_returns_zero() -> None:
    p = _build_flat_log_prices(n=100, sigma=0.001)
    sides = trend_id_c_hac_ols_slope_t(p, lookback_l=20, tau_t=10.0)  # very high
    assert (sides == 0).sum() > 80


def test_id_c_validates_lookback() -> None:
    p = np.linspace(5.0, 5.5, 30)
    with pytest.raises(ValueError, match="lookback_l"):
        trend_id_c_hac_ols_slope_t(p, lookback_l=4, tau_t=2.0)


def test_id_c_pit_safe() -> None:
    p = _build_uptrend_log_prices(n=100, drift=0.003)
    sides_full = trend_id_c_hac_ols_slope_t(p, lookback_l=20, tau_t=2.0)
    for t_trunc in range(50, 100, 10):
        sides_trunc = trend_id_c_hac_ols_slope_t(p[: t_trunc + 1], lookback_l=20, tau_t=2.0)
        np.testing.assert_array_equal(sides_trunc, sides_full[: t_trunc + 1])


# ─── ID-d: MA-cross ──────────────────────────────────────────────────────────


def test_id_d_strong_uptrend_returns_positive_side() -> None:
    p = _build_uptrend_log_prices(n=100, drift=0.005)
    close = np.exp(p)
    sides = trend_id_d_ma_cross(close, short_window=5, long_window=20, tau_ma=0.0)
    n_positive = (sides[20:] == 1).sum()
    n_negative = (sides[20:] == -1).sum()
    assert n_positive > n_negative


def test_id_d_with_zero_threshold_signals_at_every_crossover() -> None:
    # Ramping then declining series → MA-cross flips sign once.
    n = 60
    close = np.concatenate([
        np.linspace(100.0, 200.0, n // 2),
        np.linspace(200.0, 100.0, n // 2),
    ])
    sides = trend_id_d_ma_cross(close, short_window=5, long_window=15, tau_ma=0.0)
    # Some +1 in early phase, some -1 in late phase
    assert 1 in sides
    assert -1 in sides


def test_id_d_with_high_tau_ma_returns_mostly_zero() -> None:
    p = _build_flat_log_prices(n=100)
    close = np.exp(p)
    sides = trend_id_d_ma_cross(close, short_window=5, long_window=20, tau_ma=0.5)
    assert (sides == 0).sum() > 80


def test_id_d_validates_window_relation() -> None:
    p = np.linspace(5.0, 5.5, 50)
    with pytest.raises(ValueError, match="long_window"):
        trend_id_d_ma_cross(np.exp(p), short_window=20, long_window=10)


def test_id_d_validates_negative_tau() -> None:
    p = np.linspace(5.0, 5.5, 50)
    with pytest.raises(ValueError, match="tau_ma"):
        trend_id_d_ma_cross(np.exp(p), short_window=5, long_window=20, tau_ma=-0.1)


def test_id_d_pit_safe() -> None:
    p = _build_uptrend_log_prices(n=100, drift=0.003)
    close = np.exp(p)
    sides_full = trend_id_d_ma_cross(close, short_window=5, long_window=20)
    for t_trunc in range(40, 100, 10):
        sides_trunc = trend_id_d_ma_cross(close[: t_trunc + 1], short_window=5, long_window=20)
        np.testing.assert_array_equal(sides_trunc, sides_full[: t_trunc + 1])


# ─── Cross-identifier sanity ─────────────────────────────────────────────────


def test_all_identifiers_agree_on_strong_uptrend() -> None:
    # Strong uptrend should be detected by all 4 identifiers.
    rng = np.random.default_rng(42)
    n = 100
    drift = 0.005
    p = _build_uptrend_log_prices(n=n, drift=drift, sigma=0.0001)
    close = np.exp(p)
    high = close * (1.0 + np.abs(rng.normal(0.001, 0.0005, n)))
    low = close * (1.0 - np.abs(rng.normal(0.001, 0.0005, n)))

    sides_a = trend_id_a_ts_mom(p, lookback_l=20, tau_m=0.5)
    sides_b = trend_id_b_adx(high, low, close, lookback_l=14, tau_adx=15.0)
    sides_c = trend_id_c_hac_ols_slope_t(p, lookback_l=20, tau_t=2.0)
    sides_d = trend_id_d_ma_cross(close, short_window=5, long_window=20)

    # All should return mostly +1 in the second half (post-warmup).
    for name, sides in [("a", sides_a), ("b", sides_b), ("c", sides_c), ("d", sides_d)]:
        n_positive = (sides[60:] == 1).sum()
        n_negative = (sides[60:] == -1).sum()
        assert n_positive > n_negative, (
            f"identifier {name}: positive={n_positive}, negative={n_negative} on uptrend"
        )
