"""Tests for triple-barrier labels and Yang-Zhang volatility."""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import pytest

from skie_ninja.features.labels import (
    TripleBarrierConfig,
    TripleBarrierLabeler,
    yang_zhang_volatility,
)


def _make_ohlc(close: np.ndarray, *, high_wing: float = 0.001, low_wing: float = 0.001) -> dict:
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1.0 + high_wing)
    low = np.minimum(open_, close) * (1.0 - low_wing)
    return {"open": open_, "high": high, "low": low, "close": close}


def test_yang_zhang_constant_series_gives_zero_vol() -> None:
    """If prices are constant, YZ vol is exactly zero (up to float
    tolerance) for any lookback — the log-ratios are all zero.
    """
    n = 100
    close = np.full(n, 100.0)
    ohlc = _make_ohlc(close, high_wing=0.0, low_wing=0.0)
    sigma = yang_zhang_volatility(
        open_=ohlc["open"],
        high=ohlc["high"],
        low=ohlc["low"],
        close=ohlc["close"],
        lookback=20,
    )
    # Valid values start at index 20 (lookback=20 requires 20 prior
    # overnight-return observations, which in turn requires a prior
    # close — so the first valid row is at index 20, not 19).
    np.testing.assert_allclose(sigma[20:], 0.0, atol=1e-12)


def test_yang_zhang_warmup_is_nan() -> None:
    n = 60
    rng = np.random.default_rng(0)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.001, size=n)))
    ohlc = _make_ohlc(close)
    sigma = yang_zhang_volatility(
        open_=ohlc["open"],
        high=ohlc["high"],
        low=ohlc["low"],
        close=ohlc["close"],
        lookback=20,
    )
    # The first valid row requires 20 overnight returns, which need a
    # prior close; indices 0..19 are NaN.
    assert np.isnan(sigma[:20]).all()
    assert np.all(np.isfinite(sigma[20:]))


def test_yang_zhang_rejects_small_lookback() -> None:
    with pytest.raises(ValueError, match="lookback"):
        yang_zhang_volatility(
            open_=np.arange(10.0),
            high=np.arange(10.0),
            low=np.arange(10.0),
            close=np.arange(10.0),
            lookback=1,
        )


def test_triple_barrier_hit_upper_label_plus_one() -> None:
    """Up-trending log-returns produce a +1 label on any row whose
    cumulative move within the vertical horizon exceeds the
    pt·σ barrier.

    Uses a drift plus small Gaussian noise so the YZ volatility is
    positive (and therefore the barriers are strictly between
    close prices); without noise the volatility estimator is
    identically zero and the labeller's guard returns 0.
    """
    rng = np.random.default_rng(2026)
    n = 200
    r = rng.normal(loc=0.002, scale=0.0005, size=n)  # strong up-drift + noise
    close = 100.0 * np.exp(np.cumsum(r))
    ohlc = _make_ohlc(close, high_wing=0.0, low_wing=0.0)
    ts = pd.date_range("2025-01-01", periods=n, freq="1min", tz="UTC")
    panel = pl.DataFrame(
        {
            "ts_event": ts,
            "symbol": ["ES"] * n,
            **ohlc,
        }
    )
    cfg = TripleBarrierConfig(
        pt_sl=(1.0, 1.0),
        vertical_barrier=pd.Timedelta(minutes=30),
        volatility_lookback=20,
    )
    labeler = TripleBarrierLabeler(cfg)
    labeled = labeler.apply(panel, symbol_col="symbol", time_col="ts_event")
    labels = labeled.get_column("label").to_numpy()
    # Pick a row well past warm-up, and well before the right edge
    # so the vertical window lives inside the series.
    assert labels[50] == 1


def test_triple_barrier_hit_lower_label_minus_one() -> None:
    rng = np.random.default_rng(2027)
    n = 200
    r = rng.normal(loc=-0.002, scale=0.0005, size=n)
    close = 100.0 * np.exp(np.cumsum(r))
    ohlc = _make_ohlc(close, high_wing=0.0, low_wing=0.0)
    ts = pd.date_range("2025-01-01", periods=n, freq="1min", tz="UTC")
    panel = pl.DataFrame(
        {
            "ts_event": ts,
            "symbol": ["ES"] * n,
            **ohlc,
        }
    )
    cfg = TripleBarrierConfig(
        pt_sl=(1.0, 1.0),
        vertical_barrier=pd.Timedelta(minutes=30),
        volatility_lookback=20,
    )
    labeler = TripleBarrierLabeler(cfg)
    labeled = labeler.apply(panel, symbol_col="symbol", time_col="ts_event")
    labels = labeled.get_column("label").to_numpy()
    assert labels[50] == -1


def test_label_horizon_bars_matches_vertical_barrier() -> None:
    cfg = TripleBarrierConfig(
        pt_sl=(1.0, 1.0),
        vertical_barrier=pd.Timedelta(minutes=60),
        volatility_lookback=20,
    )
    labeler = TripleBarrierLabeler(cfg)
    assert labeler.label_horizon_bars(pd.Timedelta(minutes=1)) == 60


def test_triple_barrier_rejects_bad_config() -> None:
    with pytest.raises(ValueError, match="pt_sl"):
        TripleBarrierLabeler(
            TripleBarrierConfig(
                pt_sl=(0.0, 1.0),
                vertical_barrier=pd.Timedelta(minutes=30),
                volatility_lookback=20,
            )
        )
    with pytest.raises(ValueError, match="vertical_barrier"):
        TripleBarrierLabeler(
            TripleBarrierConfig(
                pt_sl=(1.0, 1.0),
                vertical_barrier=pd.Timedelta(0),
                volatility_lookback=20,
            )
        )
    with pytest.raises(ValueError, match="volatility_lookback"):
        TripleBarrierLabeler(
            TripleBarrierConfig(
                pt_sl=(1.0, 1.0),
                vertical_barrier=pd.Timedelta(minutes=30),
                volatility_lookback=1,
            )
        )
