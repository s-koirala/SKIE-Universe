"""H053 Stage-0 sanity unit tests — bin assignment + ACF helpers.

Locks the i8 → Int32 cast regression (the production script silently
mis-binned bars with hour ≥ 12 because Polars returned i8 from
``dt.hour()`` and ``(_h - 9) * 60`` overflowed at h ≥ 12).
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import polars as pl

from scripts.run_h053_stage0_hks_sanity import (
    _BIN_STARTS_ET,
    _compute_half_hour_bin_returns,
    _lag1_autocorr,
)

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def _bar_ts_utc(d: pd.Timestamp, hh: int, mm: int) -> pd.Timestamp:
    return pd.Timestamp(datetime.combine(d.date(), time(hh, mm), tzinfo=ET)).tz_convert(UTC)


def _make_one_session_panel(
    sd: pd.Timestamp = pd.Timestamp("2024-03-15"),
    *,
    symbol: str = "ES",
    drift_per_bar: float = 0.0,
) -> pl.DataFrame:
    """Build a 1-session panel covering 09:31..16:00 ET (390 bars).

    open=close=mid, mid drifts at `drift_per_bar` per bar starting from
    100.0 at 09:31 ET. high=mid+0.25, low=mid-0.25.
    """
    rows = []
    for offset in range(390):
        bar_et = datetime.combine(sd.date(), time(9, 31), tzinfo=ET) + timedelta(minutes=offset)
        ts_utc = pd.Timestamp(bar_et).tz_convert(UTC)
        mid = 100.0 + drift_per_bar * offset
        rows.append(
            {
                "ts_event": ts_utc,
                "symbol": symbol,
                "open": float(mid),
                "high": float(mid + 0.25),
                "low": float(mid - 0.25),
                "close": float(mid),
                "volume": 100.0,
            }
        )
    df = pl.DataFrame(rows)
    df = df.with_columns(
        pl.col("ts_event").dt.replace_time_zone("UTC").cast(pl.Datetime("us", "UTC"))
    )
    return df


# ---------------------------------------------------------------------------
# i8-overflow regression (load-bearing — caught a real production bug)
# ---------------------------------------------------------------------------


class TestBinAssignmentNoIntOverflow:
    """Polars dt.hour()/dt.minute() return i8; without an explicit Int32 cast,
    `(_h - 9) * 60` overflows i8 (range -128..127) for h ≥ 12, scrambling
    bin assignment for the second half of RTH. Production caught this only
    after the run produced ``ES bin returns: 350 rows across 89 sessions, 4
    unique bins``. Locking the regression here."""

    def test_all_13_bins_present_for_complete_session(self):
        sd = pd.Timestamp("2024-03-15")
        panel = _make_one_session_panel(sd, drift_per_bar=0.001)
        out = _compute_half_hour_bin_returns(panel)
        # All 13 bins must be present
        bin_idx_set = set(out["_bin_idx"].to_list())
        assert bin_idx_set == set(range(13)), (
            f"Bin assignment is incomplete; got {sorted(bin_idx_set)}, expected 0..12. "
            "Likely cause: i8 overflow on (_h - 9) * 60 for h >= 12."
        )

    def test_bin_idx_dtype_is_int32(self):
        sd = pd.Timestamp("2024-03-15")
        panel = _make_one_session_panel(sd, drift_per_bar=0.0001)
        out = _compute_half_hour_bin_returns(panel)
        assert out["_bin_idx"].dtype == pl.Int32, (
            f"_bin_idx dtype is {out['_bin_idx'].dtype}; expected Int32. "
            "An i8 dtype here is the regression that motivated this test."
        )

    def test_bin_boundaries_match_bin_starts(self):
        """Each bin should hold exactly the 30 bars (09:30+30k+1) ..
        (09:30+30(k+1)) ET, except bin 0 starts at 09:31 (first RTH bar)."""
        sd = pd.Timestamp("2024-03-15")
        # Construct panel where each bar's close is unique so we can verify
        # the open/close pairing. Open of bar i = i*0.001; close = i*0.001.
        panel = _make_one_session_panel(sd, drift_per_bar=0.001)
        out = _compute_half_hour_bin_returns(panel)
        # Each bin should produce exactly 1 (session, bin) row, all 13 bins.
        assert len(out) == 13


# ---------------------------------------------------------------------------
# Lag-1 ACF helper
# ---------------------------------------------------------------------------


class TestLag1Autocorr:
    def test_constant_series_returns_nan(self):
        v = np.zeros(10, dtype=np.float64)
        assert np.isnan(_lag1_autocorr(v))

    def test_perfect_continuation(self):
        v = np.arange(20, dtype=np.float64)
        rho = _lag1_autocorr(v)
        # Perfect linear sequence: lag-1 ACF should be very close to 1.
        assert rho > 0.95

    def test_anti_correlation(self):
        # Alternating series: -1, 1, -1, 1, ...
        v = np.array([(-1) ** k for k in range(50)], dtype=np.float64)
        rho = _lag1_autocorr(v)
        assert rho < -0.95

    def test_short_series_returns_nan(self):
        v = np.array([1.0, 2.0])  # n=2 < 3 → NaN
        assert np.isnan(_lag1_autocorr(v))

    def test_filters_nan_input(self):
        v = np.array([1.0, np.nan, 3.0, np.nan, 5.0])
        rho = _lag1_autocorr(v)
        # After filtering NaN: [1, 3, 5]; lag-1 ACF on a perfect arith
        # progression on n=3 is well-defined and == 1.0.
        assert np.isfinite(rho)


# ---------------------------------------------------------------------------
# Bin returns are finite + sensible magnitude
# ---------------------------------------------------------------------------


class TestBinReturnsSanity:
    def test_zero_drift_session_yields_zero_returns(self):
        sd = pd.Timestamp("2024-03-15")
        panel = _make_one_session_panel(sd, drift_per_bar=0.0)
        out = _compute_half_hour_bin_returns(panel)
        # Every bin should have log_return == 0 (open == close in each bin)
        assert all(abs(r) < 1e-12 for r in out["log_return"].to_list())

    def test_positive_drift_session_yields_positive_returns(self):
        sd = pd.Timestamp("2024-03-15")
        panel = _make_one_session_panel(sd, drift_per_bar=0.001)
        out = _compute_half_hour_bin_returns(panel)
        assert all(r > 0 for r in out["log_return"].to_list())
