"""Unit tests for H055 feature factory composition."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from skie_ninja.features.h055.features import (
    BarFeatures,
    H055FeatureConfig,
    Setup,
    compute_h055_features,
    emit_h055_setups,
)
from skie_ninja.utils.news_calendar import NewsCalendar, NewsRelease

UTC = timezone.utc


def _synthetic_panel(n: int = 60, seed: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[datetime]]:
    """Build a deterministic synthetic OHLC panel + UTC bar timestamps (1-min bars).

    Returns (open, high, low, close, timestamps_utc).
    """
    rng = np.random.default_rng(seed)
    drift = 0.001
    sigma = 0.0001
    log_p = np.cumsum(rng.normal(drift, sigma, n)) + np.log(5000.0)
    close = np.exp(log_p)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    body_half = np.abs(rng.normal(0.5, 0.2, n))
    high = np.maximum(open_, close) + body_half + 0.1
    low = np.minimum(open_, close) - body_half - 0.1
    base_ts = datetime(2024, 6, 12, 14, 30, tzinfo=UTC)
    timestamps = [base_ts + timedelta(minutes=i) for i in range(n)]
    return open_, high, low, close, timestamps


def _empty_calendar() -> NewsCalendar:
    return NewsCalendar(releases=())


# ─── Configuration validation ────────────────────────────────────────────────


def test_config_rejects_unknown_trend_id() -> None:
    with pytest.raises(ValueError, match="trend_id_choice"):
        H055FeatureConfig(trend_id_choice="x")  # type: ignore[arg-type]


def test_config_rejects_invalid_atr_n() -> None:
    with pytest.raises(ValueError, match="atr_n"):
        H055FeatureConfig(atr_n=0)


def test_config_rejects_invalid_rho_window() -> None:
    with pytest.raises(ValueError, match="rho_window_n"):
        H055FeatureConfig(rho_window_n=1)


def test_config_rejects_negative_r_max() -> None:
    with pytest.raises(ValueError, match="r_max"):
        H055FeatureConfig(r_max=-1)


def test_config_rejects_negative_theta_wick() -> None:
    with pytest.raises(ValueError, match="theta_wick_min"):
        H055FeatureConfig(theta_wick_min=-0.5)


# ─── compute_h055_features ──────────────────────────────────────────────────


def test_compute_features_returns_bar_features_with_correct_shape() -> None:
    o, h, l, c, ts = _synthetic_panel(n=60)
    cfg = H055FeatureConfig(
        trend_id_choice="d", short_window=5, long_window=20,
        atr_n=14, rho_window_n=10, news_calendar_enabled=False,
    )
    features = compute_h055_features(o, h, l, c, ts, config=cfg)
    assert isinstance(features, BarFeatures)
    assert features.atr_n.shape == (60,)
    assert features.rho_1.shape == (60,)
    assert features.trend_side.shape == (60,)
    assert features.is_news_excluded.shape == (60,)


def test_compute_features_news_filter_excludes_in_window() -> None:
    o, h, l, c, ts = _synthetic_panel(n=60)
    # Calendar with one release at base + 30 minutes = 15:00 UTC
    base = ts[0]
    release_ts = base + timedelta(minutes=30)
    cal = NewsCalendar(
        releases=(NewsRelease(
            indicator_id="FOMC",
            release_timestamp_utc=release_ts,
            window_minutes=15,
        ),)
    )
    cfg = H055FeatureConfig(
        trend_id_choice="d", news_calendar_enabled=True, atr_n=14, rho_window_n=10,
    )
    features = compute_h055_features(o, h, l, c, ts, config=cfg, news_calendar=cal)
    # Bars at minutes 15-45 inclusive (relative to base) are within ±15 min
    # window of release at minute 30. Bar 15 is 15 min before, bar 45 is
    # 15 min after — both inclusive.
    assert features.is_news_excluded[15] is np.True_
    assert features.is_news_excluded[30] is np.True_
    assert features.is_news_excluded[45] is np.True_
    # Outside the window:
    assert features.is_news_excluded[14] is np.False_
    assert features.is_news_excluded[46] is np.False_


def test_compute_features_news_filter_disabled_returns_all_false() -> None:
    o, h, l, c, ts = _synthetic_panel(n=30)
    cfg = H055FeatureConfig(
        trend_id_choice="d", news_calendar_enabled=False, atr_n=14, rho_window_n=10,
    )
    features = compute_h055_features(o, h, l, c, ts, config=cfg)
    assert not features.is_news_excluded.any()


def test_compute_features_validates_news_calendar_required() -> None:
    o, h, l, c, ts = _synthetic_panel(n=30)
    cfg = H055FeatureConfig(
        trend_id_choice="d", news_calendar_enabled=True, atr_n=14, rho_window_n=10,
    )
    with pytest.raises(ValueError, match="news_calendar"):
        compute_h055_features(o, h, l, c, ts, config=cfg, news_calendar=None)


def test_compute_features_validates_timestamp_length() -> None:
    o, h, l, c, _ = _synthetic_panel(n=30)
    cfg = H055FeatureConfig(trend_id_choice="d", news_calendar_enabled=False)
    with pytest.raises(ValueError, match="bar_timestamps_utc length"):
        compute_h055_features(o, h, l, c, [datetime(2024, 1, 1, tzinfo=UTC)], config=cfg)


def test_compute_features_pit_safe_for_panel_truncation() -> None:
    o, h, l, c, ts = _synthetic_panel(n=60)
    cfg = H055FeatureConfig(
        trend_id_choice="d", short_window=5, long_window=20,
        atr_n=14, rho_window_n=10, news_calendar_enabled=False,
    )
    full = compute_h055_features(o, h, l, c, ts, config=cfg)
    for t_trunc in range(30, 60, 5):
        trunc = compute_h055_features(
            o[: t_trunc + 1], h[: t_trunc + 1], l[: t_trunc + 1], c[: t_trunc + 1],
            ts[: t_trunc + 1], config=cfg,
        )
        # ATR + ρ_1 + trend_side at index 0..t_trunc must be byte-equal
        # (within float tolerance) to the truncated computation.
        np.testing.assert_array_equal(trunc.trend_side, full.trend_side[: t_trunc + 1])
        # ATR may have NaN in the warm-up period; compare non-NaN entries.
        valid = ~np.isnan(full.atr_n[: t_trunc + 1])
        np.testing.assert_allclose(
            trunc.atr_n[valid], full.atr_n[: t_trunc + 1][valid], rtol=1e-12,
        )


# ─── emit_h055_setups ───────────────────────────────────────────────────────


def test_emit_setups_returns_list_of_setup_objects() -> None:
    o, h, l, c, ts = _synthetic_panel(n=60)
    cfg = H055FeatureConfig(
        trend_id_choice="d", swing_confirmation_window=5, theta_wick_min=1.0,
        atr_n=14, rho_window_n=10, news_calendar_enabled=False,
    )
    features = compute_h055_features(o, h, l, c, ts, config=cfg)
    setups = emit_h055_setups(o, h, l, c, config=cfg, bar_features=features)
    for s in setups:
        assert isinstance(s, Setup)
        assert s.kind in ("swing_pivot", "wick_reversal")
        assert s.side in (-1, 1)


def test_emit_setups_empty_panel_returns_empty() -> None:
    o = np.array([])
    h = np.array([])
    l = np.array([])
    c = np.array([])
    ts: list[datetime] = []
    cfg = H055FeatureConfig(
        trend_id_choice="d", swing_confirmation_window=5,
        atr_n=1, rho_window_n=2, news_calendar_enabled=False,
    )
    # compute_h055_features will raise on empty ATR; bypass and use a dummy.
    features = BarFeatures(
        atr_n=np.array([]), rho_1=np.array([]),
        trend_side=np.array([], dtype=int), is_news_excluded=np.array([], dtype=bool),
    )
    setups = emit_h055_setups(o, h, l, c, config=cfg, bar_features=features)
    assert setups == []


def test_emit_setups_chronologically_sorted() -> None:
    o, h, l, c, ts = _synthetic_panel(n=80)
    cfg = H055FeatureConfig(
        trend_id_choice="d", swing_confirmation_window=5, theta_wick_min=0.5,
        atr_n=14, rho_window_n=10, news_calendar_enabled=False,
    )
    features = compute_h055_features(o, h, l, c, ts, config=cfg)
    setups = emit_h055_setups(o, h, l, c, config=cfg, bar_features=features)
    confirmation_bars = [s.confirmation_bar for s in setups]
    assert confirmation_bars == sorted(confirmation_bars)


def test_emit_setups_canonical_swing_pivot_pattern() -> None:
    # Construct a pattern that is GUARANTEED to emit a long swing-pivot.
    # 3 lower lows ending at bar 3, then 2 higher lows at bars 4 + 5.
    n = 20
    o = np.full(n, 100.0)
    h = np.full(n, 101.0)
    l = np.full(n, 99.0)
    c = np.full(n, 100.5)
    # Override lows to create the 3-down-2-up pattern at bars [0..5]
    l[0:6] = [10.0, 9.0, 8.0, 7.0, 8.0, 9.0]
    h[0:6] = [11.0, 10.0, 9.0, 8.0, 9.0, 10.0]
    o[0:6] = [10.5, 9.5, 8.5, 7.5, 8.5, 9.5]
    c[0:6] = [10.5, 9.5, 8.5, 7.5, 8.5, 9.5]
    ts = [datetime(2024, 6, 12, 14, 30, tzinfo=UTC) + timedelta(minutes=i) for i in range(n)]
    cfg = H055FeatureConfig(
        trend_id_choice="d", swing_confirmation_window=5, theta_wick_min=999.0,  # disable wick-reversal
        atr_n=2, rho_window_n=3, short_window=2, long_window=4,
        news_calendar_enabled=False,
    )
    features = compute_h055_features(o, h, l, c, ts, config=cfg)
    setups = emit_h055_setups(o, h, l, c, config=cfg, bar_features=features)
    # Should have at least one long swing-pivot setup with confirmation_bar = 5
    swing_setups = [s for s in setups if s.kind == "swing_pivot" and s.side == 1]
    assert len(swing_setups) >= 1
    assert swing_setups[0].confirmation_bar == 5
    assert swing_setups[0].entry_limit_price == 7.0  # swing-low's low value


def test_emit_setups_includes_atr_and_rho_at_confirmation() -> None:
    o, h, l, c, ts = _synthetic_panel(n=60)
    cfg = H055FeatureConfig(
        trend_id_choice="d", swing_confirmation_window=5,
        atr_n=14, rho_window_n=10, news_calendar_enabled=False,
    )
    features = compute_h055_features(o, h, l, c, ts, config=cfg)
    setups = emit_h055_setups(o, h, l, c, config=cfg, bar_features=features)
    for s in setups:
        # ATR + ρ_1 at confirmation_bar should match features at that index
        # (within float tolerance, accounting for NaN)
        if s.confirmation_bar < features.atr_n.size:
            expected_atr = features.atr_n[s.confirmation_bar]
            if not np.isnan(expected_atr):
                assert s.atr_n_at_confirmation == pytest.approx(expected_atr)
            expected_rho = features.rho_1[s.confirmation_bar]
            if not np.isnan(expected_rho):
                assert s.rho_1_at_confirmation == pytest.approx(expected_rho)
            assert s.trend_side_at_confirmation == int(features.trend_side[s.confirmation_bar])
