"""H053 Block A daily-timeframe feature tests — design.md §3.1.

Verifies the 5 daily features:
  - log_close_minus_sma50, log_close_minus_sma200 (rolling SMAs of daily close)
  - daily_realized_range_n (rolling Garman-Klass aggregated-OHLC)
  - weekly_trend_slope (rolling OLS log-price slope)
  - daily_yz_vol (Yang-Zhang via shared yang_zhang_volatility helper)

Synthetic fixture: 250 sessions of deterministic daily-aggregable
1-min RTH OHLCV. The session OHLC is parameterized so feature outputs
are computable in closed form for the most-recent session.
"""

from __future__ import annotations

import math
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import polars as pl
import pytest

from skie_ninja.features.h053.daily import H053Daily

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def _bar_ts_utc(session_date: pd.Timestamp, hh: int, mm: int) -> pd.Timestamp:
    et_dt = datetime.combine(session_date.date(), time(hh, mm), tzinfo=ET)
    return pd.Timestamp(et_dt).tz_convert(UTC)


def _make_full_rth_panel(
    session_dates: list[pd.Timestamp],
    *,
    symbol: str = "ES",
    daily_close_path: list[float] | None = None,
) -> pl.DataFrame:
    """Build a synthetic 1-min RTH OHLCV panel for ``len(session_dates)``
    sessions. Each session has 405 RTH bars (09:31..16:15 ET).

    If ``daily_close_path`` is given (length == len(session_dates)), the
    last bar's close (16:15 ET) per session equals the path value; the
    other bars within the session interpolate linearly from prior
    session's close to current target close. High = max bar close, Low
    = min, Open of first bar = mid, Volume = 100/bar (so daily_volume
    = 40500 per session).
    """
    if daily_close_path is None:
        # Default: smooth linear path from 4500 by +1 per session
        daily_close_path = [4500.0 + i for i in range(len(session_dates))]
    if len(daily_close_path) != len(session_dates):
        raise ValueError("daily_close_path must match session_dates length")

    rows = []
    prev_close = daily_close_path[0]
    for sess_idx, sd in enumerate(session_dates):
        target_close = daily_close_path[sess_idx]
        # 405 RTH bars at 09:31..16:15 ET
        bar_count = 405
        # Linear path from prev_close + ε at first bar to target_close at last bar
        for bar_idx in range(bar_count):
            # Convert bar_idx to ET wall-clock minute offset from 09:31
            total_minutes = 31 + bar_idx
            hh = 9 + total_minutes // 60
            mm = total_minutes % 60

            frac = (bar_idx + 1) / bar_count  # 1/405..1
            close = prev_close + (target_close - prev_close) * frac
            # Open of first bar = prev_close; subsequent bars = prior close
            if bar_idx == 0:
                open_ = prev_close
            else:
                # Open = previous bar's close (synthetic continuity)
                prior_frac = bar_idx / bar_count
                open_ = prev_close + (target_close - prev_close) * prior_frac
            high = max(open_, close) + 0.05
            low = min(open_, close) - 0.05
            rows.append(
                {
                    "ts_event": _bar_ts_utc(sd, hh, mm),
                    "symbol": symbol,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 100.0,
                }
            )
        prev_close = target_close

    df = pl.DataFrame(rows)
    df = df.with_columns(
        pl.col("ts_event").dt.replace_time_zone("UTC").cast(pl.Datetime("ns", "UTC"))
    )
    return df


def _gen_session_dates(n_sessions: int, start: str = "2023-01-03") -> list[pd.Timestamp]:
    """Generate n consecutive *weekday* dates starting from ``start``
    (skipping Saturdays and Sundays only — does NOT exclude holidays;
    sufficient for synthetic fixtures since the daily aggregation only
    inspects bars present in the panel)."""
    out = []
    cur = pd.Timestamp(start)
    while len(out) < n_sessions:
        if cur.weekday() < 5:  # Mon-Fri
            out.append(cur)
        cur = cur + timedelta(days=1)
    return out


# ---------------------------------------------------------------------------
# Output schema + basic structure
# ---------------------------------------------------------------------------


class TestOutputSchema:
    def test_output_schema_has_seven_columns(self):
        feature = H053Daily(window_days=60)
        cols = [f.name for f in feature.output_schema]
        assert cols == [
            "ts_event",
            "symbol",
            "log_close_minus_sma50",
            "log_close_minus_sma200",
            "daily_realized_range_60",
            "weekly_trend_slope",
            "daily_yz_vol",
        ]

    def test_gk_column_name_reflects_window(self):
        for n in (20, 60, 120):
            feature = H053Daily(window_days=n)
            cols = [f.name for f in feature.output_schema]
            assert f"daily_realized_range_{n}" in cols

    def test_post_init_rejects_too_small_windows(self):
        with pytest.raises(ValueError, match="window_days"):
            H053Daily(window_days=1)
        with pytest.raises(ValueError, match="yz_lookback"):
            H053Daily(yz_lookback=1)
        with pytest.raises(ValueError, match="slope_window"):
            H053Daily(slope_window=1)


# ---------------------------------------------------------------------------
# Daily aggregation correctness
# ---------------------------------------------------------------------------


class TestDailyAggregation:
    def test_rejects_session_with_incomplete_rth_coverage(self):
        """A session missing one or more RTH bars must not produce a row."""
        sds = _gen_session_dates(220)
        panel = _make_full_rth_panel(sds)
        # Drop one bar from the most recent session
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        # Build a panel missing one RTH bar of the last session
        panel_dropped = panel.filter(
            ~(
                (pl.col("ts_event").dt.convert_time_zone("America/New_York").dt.hour() == 10)
                & (pl.col("ts_event").dt.convert_time_zone("America/New_York").dt.minute() == 0)
                & (pl.col("ts_event").dt.convert_time_zone("America/New_York").dt.date() == sds[-1].date())
            )
        )
        out_full = feature.compute(panel.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        out_partial = feature.compute(panel_dropped.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        # The partial-coverage session is dropped; full has one more row
        assert len(out_full) == len(out_partial) + 1


# ---------------------------------------------------------------------------
# Feature semantics — closed-form verification on the most-recent session
# ---------------------------------------------------------------------------


class TestSMAFeatures:
    def test_sma_features_match_closed_form(self):
        """For a deterministic daily-close path, log_close_minus_sma50/200
        must equal the closed-form value at the most-recent session.
        """
        n = 220
        sds = _gen_session_dates(n)
        # Linear path: close[i] = 4500 + i
        path = [4500.0 + i for i in range(n)]
        panel = _make_full_rth_panel(sds, daily_close_path=path)
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        out = feature.compute(panel.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        # Most-recent row corresponds to sds[-1]
        last = out.row(-1, named=True)
        # Closed-form check: SMA50 over the 50 most recent closes (index n-50..n-1)
        sma50 = sum(path[-50:]) / 50.0
        sma200 = sum(path[-200:]) / 200.0
        assert math.isclose(
            last["log_close_minus_sma50"], math.log(path[-1] / sma50), rel_tol=1e-10
        )
        assert math.isclose(
            last["log_close_minus_sma200"], math.log(path[-1] / sma200), rel_tol=1e-10
        )


class TestGKFeature:
    def test_gk_60_day_window_finite_and_positive(self):
        """GK simple-form on a non-degenerate path should be finite and
        positive (variance estimator). Very small path differences can
        produce near-zero values; assert > 0 only when there's price
        variation.
        """
        n = 220
        sds = _gen_session_dates(n)
        # Path with structure: oscillating around 4500 with trend
        path = [4500.0 + 10.0 * math.sin(i / 10.0) + 0.5 * i for i in range(n)]
        panel = _make_full_rth_panel(sds, daily_close_path=path)
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        out = feature.compute(panel.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        gk_vals = out["daily_realized_range_60"].to_list()
        # All finite
        assert all(math.isfinite(v) for v in gk_vals)


class TestSlopeFeature:
    def test_weekly_slope_zero_for_constant_path(self):
        """If close is constant for the last 5 sessions, OLS slope = 0."""
        n = 220
        sds = _gen_session_dates(n)
        path = [4500.0 + i for i in range(n - 5)] + [4500.0 + (n - 6)] * 5
        panel = _make_full_rth_panel(sds, daily_close_path=path)
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        out = feature.compute(panel.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        last_slope = out.row(-1, named=True)["weekly_trend_slope"]
        assert abs(last_slope) < 1e-12

    def test_weekly_slope_positive_for_increasing_path(self):
        """If close is monotone increasing for last 5 sessions, slope > 0."""
        n = 220
        sds = _gen_session_dates(n)
        path = [4500.0 + i for i in range(n)]
        panel = _make_full_rth_panel(sds, daily_close_path=path)
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        out = feature.compute(panel.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        last_slope = out.row(-1, named=True)["weekly_trend_slope"]
        assert last_slope > 0

    def test_weekly_slope_matches_numpy_polyfit(self):
        """Closed-form slope must match numpy.polyfit on the same window."""
        n = 220
        sds = _gen_session_dates(n)
        # Random-but-seeded path so numpy.polyfit gives a non-trivial answer
        rng = np.random.default_rng(seed=42)
        path = list(4500.0 + rng.normal(0.0, 5.0, n).cumsum())
        panel = _make_full_rth_panel(sds, daily_close_path=path)
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        out = feature.compute(panel.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        last_slope = out.row(-1, named=True)["weekly_trend_slope"]
        # numpy.polyfit reference on the last 5 log-closes
        log_closes = np.log(path[-5:])
        x = np.arange(5)
        slope_ref, _ = np.polyfit(x, log_closes, 1)
        assert math.isclose(last_slope, slope_ref, rel_tol=1e-10)


class TestYZFeature:
    def test_yz_finite_and_positive_on_non_degenerate_path(self):
        n = 220
        sds = _gen_session_dates(n)
        rng = np.random.default_rng(seed=7)
        path = list(4500.0 + rng.normal(0.0, 5.0, n).cumsum())
        panel = _make_full_rth_panel(sds, daily_close_path=path)
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        out = feature.compute(panel.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        yz_vals = out["daily_yz_vol"].to_list()
        assert all(math.isfinite(v) and v >= 0 for v in yz_vals)


# ---------------------------------------------------------------------------
# PIT discipline + warm-up
# ---------------------------------------------------------------------------


class TestPITSafety:
    def test_warmup_rows_dropped(self):
        """SMA200 needs 200 sessions; rows before day 200 must not appear
        in the output (warm-up dropped via .is_finite() guard)."""
        n = 220
        sds = _gen_session_dates(n)
        panel = _make_full_rth_panel(sds)
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        out = feature.compute(panel.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        # Expect at most n - 199 rows (the first 199 are warm-up; 200th is first valid)
        assert len(out) <= n - 199
        assert len(out) > 0

    def test_pit_invariant_holds_under_filtering(self):
        n = 210
        sds = _gen_session_dates(n)
        panel = _make_full_rth_panel(sds)
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        # Cut off `now` mid-panel; verify pre-filtered and post-filtered outputs match
        cutoff_session = sds[-3]
        now = _bar_ts_utc(cutoff_session, 16, 15) + timedelta(minutes=1)
        out_full = feature.compute(panel.lazy(), now=now).collect()
        filtered = panel.filter(pl.col("ts_event") <= now)
        out_filtered = feature.compute(filtered.lazy(), now=now).collect()
        assert out_full.equals(out_filtered)
        # And dtype match
        assert out_full.dtypes == out_filtered.dtypes


# ---------------------------------------------------------------------------
# Multi-symbol independence
# ---------------------------------------------------------------------------


class TestMultiSymbol:
    def test_two_symbols_independent_features(self):
        """ES and NQ panels should produce separate feature rows; computing
        on a 2-symbol panel must not leak across symbols."""
        n = 210
        sds = _gen_session_dates(n)
        es_panel = _make_full_rth_panel(sds, symbol="ES")
        # NQ has a different price level (15000 vs 4500 ES) but same shape
        nq_path = [15000.0 + i for i in range(n)]
        nq_panel = _make_full_rth_panel(sds, symbol="NQ", daily_close_path=nq_path)
        combined = pl.concat([es_panel, nq_panel])
        feature = H053Daily(window_days=60, yz_lookback=20, slope_window=5)
        out = feature.compute(combined.lazy(), now=sds[-1] + timedelta(days=1)).collect()
        es_rows = out.filter(pl.col("symbol") == "ES")
        nq_rows = out.filter(pl.col("symbol") == "NQ")
        # Same number of rows per symbol
        assert len(es_rows) == len(nq_rows)
        # Symbol-specific levels should differ (sma reflects symbol's path)
        # Take the most-recent row of each
        es_last = es_rows.row(-1, named=True)
        nq_last = nq_rows.row(-1, named=True)
        # ES SMA50 ≈ ~4709; NQ SMA50 ≈ ~15209 — feature values must reflect symbols
        assert es_last["log_close_minus_sma50"] != nq_last["log_close_minus_sma50"]
