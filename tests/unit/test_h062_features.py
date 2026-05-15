"""Unit tests for H062 feature factory composition layer.

Per H062 design.md §3 + §5 — Donchian + ATR + ID_1 trend filter +
first-fire dwell composition.

Test classes:
  - TestH062FeatureConfig: config validation.
  - TestComputeH062Features: full feature stack shape + dtype + composition.
  - TestTrendIDGate: gate semantic on long/short entries.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.features.h062 import (
    H062FeatureConfig,
    H062Features,
    compute_h062_features,
)


@pytest.fixture
def synthetic_bars() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(20260515)
    n = 1000
    log_rets = rng.normal(0, 0.001, n).cumsum()
    close = 100.0 * np.exp(log_rets)
    high = close * (1.0 + np.abs(rng.normal(0, 0.0005, n)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.0005, n)))
    return {"high": high, "low": low, "close": close}


class TestH062FeatureConfig:
    def test_default_validation_passes(self) -> None:
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id="a_ts_mom",
            trend_id_lookback_l=20,
            trend_id_threshold=1.0,
        )
        assert cfg.channel_n == 20

    def test_unknown_trend_id_raises(self) -> None:
        with pytest.raises(ValueError, match="not in"):
            H062FeatureConfig(
                channel_n=20,
                atr_n=14,
                h_dwell=3,
                trend_id="z_unknown",
                trend_id_lookback_l=20,
                trend_id_threshold=1.0,
            )

    def test_ma_cross_requires_windows(self) -> None:
        with pytest.raises(ValueError, match="trend_id_short_window"):
            H062FeatureConfig(
                channel_n=20,
                atr_n=14,
                h_dwell=3,
                trend_id="d_ma_cross",
                trend_id_lookback_l=20,
                trend_id_threshold=0.0,
                trend_id_short_window=0,
                trend_id_long_window=20,
            )

    def test_ma_cross_long_must_exceed_short(self) -> None:
        with pytest.raises(ValueError, match="trend_id_long_window"):
            H062FeatureConfig(
                channel_n=20,
                atr_n=14,
                h_dwell=3,
                trend_id="d_ma_cross",
                trend_id_lookback_l=20,
                trend_id_threshold=0.0,
                trend_id_short_window=20,
                trend_id_long_window=10,
            )

    def test_invalid_channel_n_raises(self) -> None:
        with pytest.raises(ValueError, match="channel_n"):
            H062FeatureConfig(
                channel_n=0,
                atr_n=14,
                h_dwell=3,
                trend_id="a_ts_mom",
                trend_id_lookback_l=20,
                trend_id_threshold=1.0,
            )


class TestComputeH062Features:
    def test_returns_h062_features_object(
        self, synthetic_bars: dict[str, np.ndarray]
    ) -> None:
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id="a_ts_mom",
            trend_id_lookback_l=20,
            trend_id_threshold=1.0,
        )
        feats = compute_h062_features(
            high=synthetic_bars["high"],
            low=synthetic_bars["low"],
            close=synthetic_bars["close"],
            config=cfg,
        )
        assert isinstance(feats, H062Features)

    def test_all_arrays_same_length_as_close(
        self, synthetic_bars: dict[str, np.ndarray]
    ) -> None:
        n = synthetic_bars["close"].size
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id="a_ts_mom",
            trend_id_lookback_l=20,
            trend_id_threshold=1.0,
        )
        feats = compute_h062_features(**synthetic_bars, config=cfg)
        assert feats.channel.channel_high.shape == (n,)
        assert feats.channel.channel_low.shape == (n,)
        assert feats.atr.shape == (n,)
        assert feats.trend_side.shape == (n,)
        assert feats.raw_events.shape == (n,)
        assert feats.filtered_events.shape == (n,)
        assert feats.eligible_events.shape == (n,)

    def test_events_dtype_int8(
        self, synthetic_bars: dict[str, np.ndarray]
    ) -> None:
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id="a_ts_mom",
            trend_id_lookback_l=20,
            trend_id_threshold=1.0,
        )
        feats = compute_h062_features(**synthetic_bars, config=cfg)
        assert feats.raw_events.dtype == np.int8
        assert feats.filtered_events.dtype == np.int8
        assert feats.eligible_events.dtype == np.int8

    def test_shape_mismatch_raises(
        self, synthetic_bars: dict[str, np.ndarray]
    ) -> None:
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id="a_ts_mom",
            trend_id_lookback_l=20,
            trend_id_threshold=1.0,
        )
        with pytest.raises(ValueError, match="OHLC shape mismatch"):
            compute_h062_features(
                high=synthetic_bars["high"][:-1],
                low=synthetic_bars["low"],
                close=synthetic_bars["close"],
                config=cfg,
            )

    @pytest.mark.parametrize(
        "trend_id",
        ["a_ts_mom", "b_adx", "c_hac_ols_slope_t"],
    )
    def test_all_trend_id_families_run(
        self, synthetic_bars: dict[str, np.ndarray], trend_id: str
    ) -> None:
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id=trend_id,
            trend_id_lookback_l=20,
            trend_id_threshold=1.0,
        )
        feats = compute_h062_features(**synthetic_bars, config=cfg)
        assert feats.trend_side.shape[0] == synthetic_bars["close"].size

    def test_d_ma_cross_trend_id_runs(
        self, synthetic_bars: dict[str, np.ndarray]
    ) -> None:
        cfg = H062FeatureConfig(
            channel_n=20,
            atr_n=14,
            h_dwell=3,
            trend_id="d_ma_cross",
            trend_id_lookback_l=20,
            trend_id_threshold=0.0,
            trend_id_short_window=10,
            trend_id_long_window=50,
        )
        feats = compute_h062_features(**synthetic_bars, config=cfg)
        assert feats.trend_side.shape[0] == synthetic_bars["close"].size


class TestTrendIDGate:
    """Gate semantic: long entry requires trend_side ∈ {+1, 0}; short ∈ {-1, 0}."""

    def test_long_event_with_trend_minus_one_is_suppressed(
        self, synthetic_bars: dict[str, np.ndarray]
    ) -> None:
        # Force a long breakout and a -1 trend side via construction.
        # Simplest path: directly inspect the filter behavior.
        from skie_ninja.features.h062 import compute_h062_features
        cfg = H062FeatureConfig(
            channel_n=5,
            atr_n=5,
            h_dwell=1,
            trend_id="a_ts_mom",
            trend_id_lookback_l=10,
            trend_id_threshold=0.001,  # very-low threshold -> almost-always non-zero side
        )
        feats = compute_h062_features(**synthetic_bars, config=cfg)
        # For every bar where filtered_events != 0 and eligible_events == 0,
        # the trend side must disagree (long event with -1, or short with +1).
        n = synthetic_bars["close"].size
        for t in range(n):
            if feats.filtered_events[t] != feats.eligible_events[t]:
                fe = int(feats.filtered_events[t])
                ts = int(feats.trend_side[t])
                if fe == 1:
                    assert ts == -1, f"t={t}: long suppressed but trend_side={ts}"
                elif fe == -1:
                    assert ts == 1, f"t={t}: short suppressed but trend_side={ts}"

    def test_neutral_trend_admits_both_sides(self) -> None:
        # If trend_side[t] == 0, both long and short events pass through.
        # Construct trend filter with very-high threshold so all sides == 0.
        n = 200
        rng = np.random.default_rng(20260515)
        log_rets = rng.normal(0, 0.001, n).cumsum()
        close = 100.0 * np.exp(log_rets)
        high = close + 0.1
        low = close - 0.1
        cfg = H062FeatureConfig(
            channel_n=5,
            atr_n=5,
            h_dwell=1,
            trend_id="a_ts_mom",
            trend_id_lookback_l=10,
            trend_id_threshold=100.0,  # very high; trend never fires
        )
        feats = compute_h062_features(high=high, low=low, close=close, config=cfg)
        assert np.all(feats.trend_side == 0)
        # With trend_side all zero, filtered_events should equal eligible_events.
        np.testing.assert_array_equal(feats.filtered_events, feats.eligible_events)
