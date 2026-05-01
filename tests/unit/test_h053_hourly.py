"""H053 Block B hourly-timeframe feature tests — design.md §3.2.

Verifies the 27 features:
  - hourly_returns_lag_1..24 (24 lag features)
  - prior_session_vwap_dev
  - overnight_return
  - pre_open_return

Synthetic fixture: 1-min bars at every clock-minute 00:00..23:59 ET on
each session date, with the 17:00-18:00 ET CME maintenance halt
excluded (no bars at timestamps 17:01..18:00). Bar OHLC walks
deterministically so closed-form values are computable for the most-
recent session.
"""

from __future__ import annotations

import math
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import polars as pl
import pytest

from skie_ninja.features.h053.hourly import H053Hourly

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def _bar_ts_utc(session_date: pd.Timestamp, hh: int, mm: int) -> pd.Timestamp:
    et_dt = datetime.combine(session_date.date(), time(hh, mm), tzinfo=ET)
    return pd.Timestamp(et_dt).tz_convert(UTC)


def _gen_session_dates(n: int, start: str = "2024-03-04") -> list[pd.Timestamp]:
    """Generate `n` consecutive weekdays from `start`."""
    out: list[pd.Timestamp] = []
    cur = pd.Timestamp(start)
    while len(out) < n:
        if cur.weekday() < 5:
            out.append(cur)
        cur = cur + timedelta(days=1)
    return out


def _is_halt_bar(hh: int, mm: int) -> bool:
    """Bar at timestamp HH:MM ET covers [HH:MM-1, HH:MM) ET. The halt is
    17:00-18:00 ET so bars covering those minutes (timestamps 17:01..18:00)
    are excluded.
    """
    if hh == 17 and 1 <= mm <= 59:
        return True
    if hh == 18 and mm == 0:
        return True
    return False


def _make_full_panel(
    session_dates: list[pd.Timestamp],
    *,
    symbol: str = "ES",
    base_close: float = 4500.0,
    close_step: float = 0.001,
) -> pl.DataFrame:
    """Synthesize a 1-min OHLCV panel covering every minute 00:00..23:59
    ET on each session, excluding the halt hour. Closes walk
    monotonically by `close_step` per emitted bar.
    """
    rows: list[dict] = []
    minute_index = 0
    for sd in session_dates:
        for total_min in range(24 * 60):
            bar_hh = total_min // 60
            bar_mm = total_min % 60
            if _is_halt_bar(bar_hh, bar_mm):
                continue
            close = base_close + close_step * minute_index
            open_ = close - close_step
            high = max(open_, close) + 0.05
            low = min(open_, close) - 0.05
            rows.append(
                {
                    "ts_event": _bar_ts_utc(sd, bar_hh, bar_mm),
                    "symbol": symbol,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 100.0,
                }
            )
            minute_index += 1
    df = pl.DataFrame(rows)
    df = df.with_columns(
        pl.col("ts_event").dt.replace_time_zone("UTC").cast(pl.Datetime("ns", "UTC"))
    )
    return df


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------


class TestOutputSchema:
    def test_schema_has_29_columns(self):
        feature = H053Hourly()
        cols = [f.name for f in feature.output_schema]
        assert len(cols) == 29  # ts_event + symbol + 24 lag + 3 single-value
        assert cols[0] == "ts_event"
        assert cols[1] == "symbol"
        assert cols[-3:] == [
            "prior_session_vwap_dev",
            "overnight_return",
            "pre_open_return",
        ]

    def test_lag_columns_in_expected_order(self):
        feature = H053Hourly()
        cols = [f.name for f in feature.output_schema]
        lag_cols = [c for c in cols if c.startswith("hourly_returns_lag_")]
        assert lag_cols == [f"hourly_returns_lag_{k}" for k in range(1, 25)]

    def test_all_features_non_nullable(self):
        feature = H053Hourly()
        non_null = [
            f.name for f in feature.output_schema if not f.nullable
        ]
        # All 29 fields are non-nullable per design contract
        assert len(non_null) == 29


# ---------------------------------------------------------------------------
# Per-session output structure
# ---------------------------------------------------------------------------


class TestPerSessionStructure:
    def test_minimal_panel_produces_at_least_one_row(self):
        """5 sessions of full coverage → enough history for the most
        recent sessions to have lag_24 (24h back).
        """
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        assert len(out) > 0

    def test_ts_event_anchors_at_0931_et(self):
        """Output ts_event must be the 09:31 ET bar timestamp (per
        module docstring: latest input bar across all 4 feature families).
        """
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        for ts in out["ts_event"].to_list():
            ts_et = pd.Timestamp(ts).tz_convert("America/New_York")
            assert ts_et.time() == time(9, 31)

    def test_one_row_per_session_post_warmup(self):
        """After warmup (lag_24 requires ≥24 hourly closes), each
        session in the panel produces at most 1 row per symbol.
        """
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        # Group by session date, verify one row per session
        out_dates = [
            pd.Timestamp(t).tz_convert("America/New_York").date()
            for t in out["ts_event"].to_list()
        ]
        assert len(out_dates) == len(set(out_dates))


# ---------------------------------------------------------------------------
# Single-value features — closed-form on monotonic synthetic close
# ---------------------------------------------------------------------------


class TestSingleValueFeatures:
    def test_overnight_return_positive_on_monotonic_path(self):
        """O_{09:30 ET, t} > C_{16:00 ET, T-1} for monotonically rising
        synthetic close → overnight_return > 0.
        """
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        for v in out["overnight_return"].to_list():
            assert v > 0

    def test_pre_open_return_positive_on_monotonic_path(self):
        """O_{09:30 ET, t} > O_{06:00 ET, t} for monotonically rising
        within-day path → pre_open_return > 0.
        """
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        for v in out["pre_open_return"].to_list():
            assert v > 0

    def test_prior_session_vwap_dev_finite(self):
        """VWAP-dev is finite when both numerator and denominator are
        well-defined.
        """
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        for v in out["prior_session_vwap_dev"].to_list():
            assert math.isfinite(v)


# ---------------------------------------------------------------------------
# hourly_returns_lag_k features
# ---------------------------------------------------------------------------


class TestHourlyLagFeatures:
    def test_lag_1_is_finite_and_positive(self):
        """lag_1 = log(close_09:00 / close_08:00) > 0 on monotonic path."""
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        for v in out["hourly_returns_lag_1"].to_list():
            assert math.isfinite(v)
            assert v > 0  # monotonic synthetic close

    def test_all_24_lags_finite(self):
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        for k in range(1, 25):
            col = f"hourly_returns_lag_{k}"
            for v in out[col].to_list():
                assert math.isfinite(v), f"{col} contains non-finite value"

    def test_halt_hour_lag_returns_zero_via_forward_fill(self):
        """The 17:00→18:00 ET halt hour has no bars; the module forward-
        fills the 17:00 ET close to 18:00 ET so the 18:00 ET hourly
        return = log(close_18:00 / close_17:00) = log(1) = 0.

        Lag indexing from 09:00 ET anchor:
            lag_1 = 09:00 ET t row → 08:00→09:00 ET t hour return
            lag_k = shift(k-1) row → return at clock-hour (anchor − (k−1)h)

        Counting back: 09:00 ET t (lag_1) → 08:00 t → ... → 00:00 t (lag_10)
        → 23:00 t-1 (lag_11) → ... → 18:00 t-1 (lag_16) → 17:00 t-1 (lag_17).

        The 18:00 ET t-1 row's hourly_log_return is log(close_18:00_t-1 /
        close_17:00_t-1), which is the 17:00→18:00 hour = halt. After
        forward-fill of the missing 18:00 close from 17:00, this return
        equals log(1) = 0. So **lag_16** carries the halt-zero value.
        """
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        out = feature.compute(
            panel.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        for v in out["hourly_returns_lag_16"].to_list():
            assert abs(v) < 1e-9, (
                f"lag_16 (halt-hour return) should be ≈0 via forward-fill; got {v}"
            )
        # F-18: assert non-halt-adjacent lags are positive on monotonic
        # synthetic. The halt should affect ONLY lag_16; lag_15 (18:00
        # → 19:00 ET t-1, post-halt) and lag_17 (16:00 → 17:00 ET t-1,
        # pre-halt) are normal hourly returns over real bars.
        for v in out["hourly_returns_lag_15"].to_list():
            assert v > 0, f"lag_15 (post-halt) should be positive on monotonic; got {v}"
        for v in out["hourly_returns_lag_17"].to_list():
            assert v > 0, f"lag_17 (pre-halt) should be positive on monotonic; got {v}"


# ---------------------------------------------------------------------------
# PIT discipline
# ---------------------------------------------------------------------------


class TestPITSafety:
    def test_pit_invariant_holds_under_filtering(self):
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        cutoff_session = sds[3]
        now = _bar_ts_utc(cutoff_session, 9, 31) + timedelta(minutes=1)
        out_full = feature.compute(panel.lazy(), now=now).collect()
        filtered = panel.filter(pl.col("ts_event") <= now)
        out_filtered = feature.compute(filtered.lazy(), now=now).collect()
        assert out_full.equals(out_filtered)

    def test_future_bars_invisible(self):
        sds = _gen_session_dates(5)
        panel = _make_full_panel(sds)
        feature = H053Hourly()
        # now = end of session 2; only session 2's anchor and earlier visible
        now = _bar_ts_utc(sds[1], 23, 59)
        out = feature.compute(panel.lazy(), now=now).collect()
        # Output sessions must be ≤ session 2
        for ts in out["ts_event"].to_list():
            ts_et_date = pd.Timestamp(ts).tz_convert("America/New_York").date()
            assert ts_et_date <= sds[1].date()


# ---------------------------------------------------------------------------
# Multi-symbol independence
# ---------------------------------------------------------------------------


class TestMultiSymbol:
    def test_two_symbols_independent_rows(self):
        sds = _gen_session_dates(5)
        es_panel = _make_full_panel(sds, symbol="ES", base_close=4500.0)
        nq_panel = _make_full_panel(sds, symbol="NQ", base_close=15000.0)
        combined = pl.concat([es_panel, nq_panel])
        feature = H053Hourly()
        out = feature.compute(
            combined.lazy(), now=sds[-1] + timedelta(days=1)
        ).collect()
        es_rows = out.filter(pl.col("symbol") == "ES")
        nq_rows = out.filter(pl.col("symbol") == "NQ")
        assert len(es_rows) == len(nq_rows)
        assert len(es_rows) > 0
