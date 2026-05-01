"""H053 Block D mediator tests — design.md §3.4 + §3.0 binding.

Verifies the four mediator features computed by
``src/skie_ninja/features/h053/mediator.py`` against:

  - **design.md §3.4** field semantics (m_return, m_log_range Garman-Klass,
    m_volume, m_ofi_tickrule).
  - **design.md §3.0** bar-edge convention (R1-R6) — concretely, the
    mediator block must read exactly the 15 bars timestamped
    {09:31..09:45 ET} per session and must reject 09:30 ET / 09:46+ ET bars.
  - **PIT discipline** — `compute(panel, now=...)` must read no bar
    timestamped > now.
  - **Lee-Ready 1991 §III.A** zero-Δclose sign-carry-forward + first-bar-
    sign-zero conventions.

Synthetic fixtures use a single ET session (2024-03-15, mid-March, no DST)
plus DST-awareness fixtures (post-spring-forward 2024-03-11; post-fall-back
2024-11-04) to cover the same parametrisation as the §3.0 regression gate.
"""

from __future__ import annotations

import math
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import polars as pl
import pytest

from skie_ninja.features.h053.mediator import H053Mediator

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def _bar_ts_utc(session_date: pd.Timestamp, hh: int, mm: int) -> pd.Timestamp:
    """Return UTC pd.Timestamp for the bar timestamped (hh:mm ET) on `session_date`."""
    et_dt = datetime.combine(session_date.date(), time(hh, mm), tzinfo=ET)
    return pd.Timestamp(et_dt).tz_convert(UTC)


def _make_panel(
    session_dates: list[pd.Timestamp],
    *,
    symbol: str = "ES",
    fill_outside_mediator: bool = True,
    overrides: dict | None = None,
) -> pl.DataFrame:
    """Build a synthetic 1-min OHLCV panel covering each session's
    [09:30 ET, 10:30 ET] window (61 bars per session: the 09:30 prior-bar
    reference + 15 mediator bars + 45 predictand-window bars).

    Default: open=close=mid, high=mid+0.25, low=mid-0.25, volume=100,
    with mid increasing by 0.25 per bar starting from 4500.0. This
    yields a strictly-monotone close-to-close so all OFI signs are +1
    (no zero-Δclose tie-break needed).

    `overrides` allows per-bar customisation: a dict of
    {(session_idx, hh, mm): {"open"=..., "high"=..., ...}} merges over
    the default OHLCV.
    """
    overrides = overrides or {}
    rows = []
    for session_idx, sd in enumerate(session_dates):
        # Per-session mid trajectory; reset start so different sessions don't
        # compound, simplifying overrides-based tests.
        mid_at_open = 4500.0 + 100.0 * session_idx
        for offset in range(61):
            hh, mm = 9 + (30 + offset) // 60, (30 + offset) % 60
            mid = mid_at_open + 0.25 * offset
            open_ = mid
            close_ = mid
            high_ = mid + 0.25
            low_ = mid - 0.25
            vol = 100.0

            if not fill_outside_mediator:
                # Skip bars outside the mediator window (used to test that
                # missing pre-09:31 bar gives sign=0 for the first mediator bar).
                if not (hh == 9 and 31 <= mm <= 45):
                    continue

            ovr = overrides.get((session_idx, hh, mm), {})
            row = {
                "ts_event": _bar_ts_utc(sd, hh, mm),
                "symbol": symbol,
                "open": ovr.get("open", open_),
                "high": ovr.get("high", high_),
                "low": ovr.get("low", low_),
                "close": ovr.get("close", close_),
                "volume": ovr.get("volume", vol),
            }
            rows.append(row)
    df = pl.DataFrame(rows)
    # Cast ts_event to UTC-tz Datetime to match vendor_legacy_1min_roll_adjusted schema
    df = df.with_columns(
        pl.col("ts_event").dt.replace_time_zone("UTC").cast(pl.Datetime("ns", "UTC"))
    )
    return df


# ---------------------------------------------------------------------------
# Field semantics — design.md §3.4
# ---------------------------------------------------------------------------


class TestMediatorFields:
    def test_output_schema_has_six_columns(self):
        feature = H053Mediator()
        cols = [f.name for f in feature.output_schema]
        assert cols == [
            "ts_event",
            "symbol",
            "m_return",
            "m_log_range",
            "m_volume",
            "m_ofi_tickrule",
        ]

    def test_single_session_outputs_one_row_per_symbol(self):
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel([sd])
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        assert len(out) == 1
        assert out["symbol"][0] == "ES"

    def test_ts_event_anchors_at_0945_et(self):
        """§3.0 R4: output ts_event must be the 09:45 ET bar's UTC timestamp."""
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel([sd])
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        expected_utc = _bar_ts_utc(sd, 9, 45)
        got = out["ts_event"][0]
        assert got == expected_utc

    def test_m_return_equals_log_close_over_open(self):
        """§3.4: m_return = log(C_{09:45} / O_{09:30}) where O_{09:30}
        is the open of the 09:31 ET bar (per §3.0 R5).

        Synthetic: open of 09:31 bar = 4500.25 (mid_at_open + 0.25*1);
        close of 09:45 bar = 4500.0 + 0.25*15 = 4503.75.
        Expected m_return = log(4503.75 / 4500.25).
        """
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel([sd])
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        expected = math.log(4503.75 / 4500.25)
        assert math.isclose(out["m_return"][0], expected, rel_tol=1e-12)

    def test_m_volume_sums_15_bars(self):
        """§3.4: m_volume = Σ contract-volume over the 15 mediator bars.
        Synthetic: 15 bars × 100 contracts = 1500.
        """
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel([sd])
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        assert out["m_volume"][0] == 1500.0

    def test_m_log_range_garman_klass_aggregated_ohlc(self):
        """§3.4: m_log_range = GK(0.5·log(H/L)² − (2·ln2−1)·log(C/O)²)
        on aggregated 15-bar OHLC.

        Synthetic (mid increases 0.25/bar from 4500.0; high=mid+0.25,
        low=mid-0.25; bar i has hi/lo at mid_i ± 0.25):
          - 09:31 bar (i=1): mid=4500.25; high=4500.50, low=4500.00
          - 09:45 bar (i=15): mid=4503.75; high=4504.00, low=4503.50
          - aggregated H = 4504.00 (from i=15)
          - aggregated L = 4500.00 (from i=1)
          - aggregated O = open of 09:31 = mid_1 = 4500.25
          - aggregated C = close of 09:45 = mid_15 = 4503.75
        """
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel([sd])
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        H, L = 4504.00, 4500.00
        O, C = 4500.25, 4503.75
        expected = 0.5 * (math.log(H / L)) ** 2 - (2.0 * math.log(2) - 1.0) * (
            math.log(C / O)
        ) ** 2
        assert math.isclose(out["m_log_range"][0], expected, rel_tol=1e-12)

    def test_m_ofi_tickrule_all_positive_signs(self):
        """§3.4: m_ofi_tickrule = Σ sign(Δclose)·volume over 15 bars.
        Synthetic: close strictly increasing → all signs +1 → sum = 15·100 = 1500.
        """
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel([sd])
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        assert out["m_ofi_tickrule"][0] == 1500.0


# ---------------------------------------------------------------------------
# §3.0 R2-R5 bar-edge invariants
# ---------------------------------------------------------------------------


class TestBarEdgeConvention:
    def test_rejects_0930_bar_from_window(self):
        """§3.0 R5: no 09:30 ET bar in mediator window. The 09:30 ET data
        bar exists in the panel (used for OFI prior-close reference) but
        must NOT contribute to m_volume / m_return / m_log_range / m_ofi.

        Construct: synthetic 09:30 ET bar with anomalous huge volume
        (10_000) and extreme price (high=999_999). If the mediator
        accidentally includes it, m_volume jumps by 10_000 and m_log_range
        explodes. Expected m_volume = 1500 unchanged.
        """
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel(
            [sd],
            overrides={
                (0, 9, 30): {
                    "open": 999_999.0,
                    "high": 999_999.0,
                    "low": 999_999.0,
                    "close": 999_999.0,
                    "volume": 10_000.0,
                }
            },
        )
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        # m_volume must be unaffected by the 09:30 bar
        assert out["m_volume"][0] == 1500.0
        # m_log_range must be the GK on aggregated 15-bar OHLC, not 999_999
        assert out["m_log_range"][0] < 0.001  # well below any anomaly

    def test_rejects_0946_bar_from_window(self):
        """§3.0 R3: 09:46 ET bar belongs to the predictand window, NOT
        the mediator window. Construct: 09:46 ET bar with anomalous volume.
        Expected m_volume = 1500 unchanged.
        """
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel(
            [sd],
            overrides={
                (0, 9, 46): {
                    "open": 999_999.0,
                    "high": 999_999.0,
                    "low": 999_999.0,
                    "close": 999_999.0,
                    "volume": 10_000.0,
                }
            },
        )
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        assert out["m_volume"][0] == 1500.0

    def test_uses_open_of_0931_bar_for_O_0930_shorthand(self):
        """§3.0 R5: O_{09:30} = open of 09:31 ET bar. m_return baseline
        must trace to the 09:31 ET bar's open, NOT the 09:30 ET bar's open.

        Override the 09:31 ET bar's open to a sentinel value; m_return
        should reflect it.
        """
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel(
            [sd],
            overrides={
                (0, 9, 31): {"open": 4400.00},  # sentinel; default would be 4500.25
            },
        )
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        # m_return = log(close_0945 / open_0931) = log(4503.75 / 4400.00)
        expected = math.log(4503.75 / 4400.00)
        assert math.isclose(out["m_return"][0], expected, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# PIT discipline
# ---------------------------------------------------------------------------


class TestPITSafety:
    def test_now_at_0945_includes_session(self):
        """`now` set to exactly 09:45 ET should include the session."""
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel([sd])
        feature = H053Mediator()
        # now = 09:45 ET → bars with ts_event <= 09:45 ET (all 15 mediator bars)
        now = _bar_ts_utc(sd, 9, 45)
        out = feature.compute(panel.lazy(), now=now).collect()
        assert len(out) == 1

    def test_now_at_0944_excludes_session(self):
        """`now` set to 09:44 ET excludes the 09:45 ET bar; window has
        only 14 bars; session is rejected per the bar_count == 15 gate."""
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel([sd])
        feature = H053Mediator()
        now = _bar_ts_utc(sd, 9, 44)
        out = feature.compute(panel.lazy(), now=now).collect()
        assert len(out) == 0

    def test_future_bars_invisible_to_compute(self):
        """A panel containing future-timestamp bars (beyond `now`) must
        not affect output. Construct: panel for 2024-03-15 + 2024-03-18;
        now = 2024-03-15 23:59 UTC. Expect 1 row (only Friday's mediator).
        """
        sds = [pd.Timestamp("2024-03-15"), pd.Timestamp("2024-03-18")]
        panel = _make_panel(sds)
        feature = H053Mediator()
        now = pd.Timestamp("2024-03-15 23:59:00", tz="UTC")
        out = feature.compute(panel.lazy(), now=now).collect()
        assert len(out) == 1

    def test_pit_invariant_holds_under_filtering(self):
        """PIT property: compute(panel, now) == compute(panel.filter(ts<=now), now)
        for any reasonable `now` within the panel range.
        """
        sds = [pd.Timestamp("2024-03-15"), pd.Timestamp("2024-03-18")]
        panel = _make_panel(sds)
        feature = H053Mediator()
        now = _bar_ts_utc(sds[0], 9, 45) + timedelta(minutes=1)  # just after first session's mediator
        out_full = feature.compute(panel.lazy(), now=now).collect()
        filtered = panel.filter(pl.col("ts_event") <= now)
        out_filtered = feature.compute(filtered.lazy(), now=now).collect()
        assert out_full.equals(out_filtered)


# ---------------------------------------------------------------------------
# OFI tick-rule sign convention
# ---------------------------------------------------------------------------


class TestOFISignConvention:
    def test_zero_dclose_carries_previous_sign_forward(self):
        """Lee-Ready 1991 §III.A: zero Δclose at bar t → sign carries
        forward from last non-zero. Synthetic: 09:31 ET close jumps up
        (sign +1), 09:32 ET close stays flat (sign carries +1 forward),
        09:33+ continue increasing.

        With our default panel: all closes increase by 0.25/bar → all
        +1. Override 09:32 ET close to equal 09:31 ET close → 09:32
        sign should still be +1 (carried forward), not 0.
        """
        sd = pd.Timestamp("2024-03-15")
        panel = _make_panel(
            [sd],
            overrides={
                (0, 9, 32): {"close": 4500.25},  # same as 09:31 close
            },
        )
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        # All 15 signs still +1 → m_ofi_tickrule = 1500.0
        assert out["m_ofi_tickrule"][0] == 1500.0

    def test_negative_sign_subtracts(self):
        """Construct one negative-sign bar in the mediator window and
        verify it reduces m_ofi_tickrule by 200 (= 100 - (-100)).
        """
        sd = pd.Timestamp("2024-03-15")
        # Override 09:35 ET to drop close — gives sign -1 for that bar
        panel = _make_panel(
            [sd],
            overrides={
                (0, 9, 35): {"close": 4500.0},  # below 09:34 close (4500.0 + 0.25*4 = 4501.0)
                # 09:36 close goes back to 4501.5 (default mid + 0.25*6) → +1
            },
        )
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        # 14 bars +1 × 100 = +1400; 1 bar -1 × 100 = -100; net = 1300
        assert out["m_ofi_tickrule"][0] == 1300.0

    def test_first_bar_per_symbol_uses_prior_data_bar(self):
        """The 09:31 ET bar's sign uses close_{09:30 ET} as prior reference
        (the 09:30 ET data bar exists in the panel even though §3.0 R5
        excludes it from the mediator window). Verify by overriding
        09:30 ET close to match 09:31 ET close — sign at 09:31 should be
        zero (no prior non-zero sign in the panel for this bar's session).
        """
        sd = pd.Timestamp("2024-03-15")
        # Override 09:30 close to equal 09:31 close (4500.25)
        # → sign at 09:31 = 0 (no prior to carry forward; this is the first
        # bar in the panel for this symbol).
        panel = _make_panel(
            [sd],
            overrides={
                (0, 9, 30): {"close": 4500.25, "open": 4500.25, "high": 4500.25, "low": 4500.25},
            },
        )
        feature = H053Mediator()
        out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
        # Bar 09:31 has sign 0 (Δclose = 0 from 09:30 → 09:31, no prior to carry).
        # Bars 09:32..09:45 have sign +1 (close strictly increasing).
        # 14 × 100 = 1400.
        assert out["m_ofi_tickrule"][0] == 1400.0


# ---------------------------------------------------------------------------
# Multi-session + DST-awareness (matches bar-edge regression gate parametrisations)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "session_date",
    [
        pd.Timestamp("2024-03-15"),  # mid-march, no DST
        pd.Timestamp("2024-03-11"),  # post-spring-forward Mon
        pd.Timestamp("2024-11-04"),  # post-fall-back Mon
    ],
    ids=["mid-march", "post-spring-forward", "post-fall-back"],
)
def test_dst_aware_session_produces_correct_row(session_date):
    """The mediator must work correctly across DST transitions because
    the bar-set definitions in §3.0 are anchored in ET wall-clock, not
    UTC offset. Re-uses the bar-edge regression gate's parametrisation.
    """
    panel = _make_panel([session_date])
    feature = H053Mediator()
    out = feature.compute(panel.lazy(), now=session_date + timedelta(days=1)).collect()
    assert len(out) == 1
    # ts_event should be 09:45 ET converted to UTC. Verify by round-tripping.
    et_back = pd.Timestamp(out["ts_event"][0]).tz_convert("America/New_York")
    assert et_back.time() == time(9, 45)


def test_multi_session_one_row_per_session():
    sds = [pd.Timestamp("2024-03-15"), pd.Timestamp("2024-03-18")]
    panel = _make_panel(sds)
    feature = H053Mediator()
    out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-19")).collect()
    assert len(out) == 2
    # Sessions in chronological order
    et_dates = [
        pd.Timestamp(t).tz_convert("America/New_York").date() for t in out["ts_event"]
    ]
    assert et_dates == [sd.date() for sd in sds]


def test_incomplete_session_is_rejected():
    """A session with fewer than 15 mediator bars (e.g., data outage)
    must be excluded — design.md §3.4 binds the 4-feature vector to
    the 15-bar window; partial coverage is not a valid mediator.
    """
    sd = pd.Timestamp("2024-03-15")
    # Build a panel without the 09:31 bar — only 14 mediator bars present
    panel = _make_panel([sd], fill_outside_mediator=True)
    panel = panel.filter(
        ~(
            (pl.col("ts_event").dt.convert_time_zone("America/New_York").dt.hour() == 9)
            & (pl.col("ts_event").dt.convert_time_zone("America/New_York").dt.minute() == 31)
        )
    )
    feature = H053Mediator()
    out = feature.compute(panel.lazy(), now=pd.Timestamp("2024-03-16")).collect()
    assert len(out) == 0
