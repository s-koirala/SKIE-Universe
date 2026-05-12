"""Unit + property tests for src/skie_ninja/utils/clock.py.

Covers:
  - DST transitions (2nd Sunday March, 1st Sunday November) 2025 + 2026.
  - Half-days (Thanksgiving Friday 12:00 CT; Christmas Eve 12:15 CT; July 3).
  - 2025-2026 full-day holidays.
  - Invariant: session_of never returns "RTH" outside 08:30-15:15 CT on weekdays.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from skie_ninja.utils.clock import (
    CME_TZ,
    RTH_CLOSE,
    RTH_OPEN,
    SessionKind,
    classify_energy_metals_session,
    is_energy_metals_session_active,
    session_of,
    to_exchange,
    trading_day,
)

UTC = ZoneInfo("UTC")


def _ct(y: int, m: int, d: int, hh: int, mm: int = 0) -> pd.Timestamp:
    return pd.Timestamp(datetime(y, m, d, hh, mm), tz=CME_TZ)


# -----------------------------------------------------------------------
# to_exchange
# -----------------------------------------------------------------------


def test_to_exchange_naive_is_utc() -> None:
    naive = pd.Timestamp("2026-03-02 14:30:00")  # noon-ish
    got = to_exchange(naive)
    assert got.tzinfo is not None
    # 14:30 UTC -> 08:30 CT (CST, before DST)
    assert got.hour == 8 and got.minute == 30


def test_to_exchange_tz_aware_roundtrip() -> None:
    t = pd.Timestamp("2026-07-15 18:00", tz="UTC")
    got = to_exchange(t)
    # Summer CDT = UTC-5 -> 13:00 CT
    assert got.hour == 13


# -----------------------------------------------------------------------
# session_of basic cases
# -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "ts,expected",
    [
        # Weekday RTH middle.
        (_ct(2026, 4, 15, 10, 0), "RTH"),
        # Just before RTH on a weekday.
        (_ct(2026, 4, 15, 8, 29), "ETH"),
        # RTH close boundary (15:15 is NOT RTH).
        (_ct(2026, 4, 15, 15, 15), "ETH"),
        # Pre-halt weekday.
        (_ct(2026, 4, 15, 15, 59), "ETH"),
        # Maintenance halt 16:00-17:00 CT weekday.
        (_ct(2026, 4, 15, 16, 30), "HALT"),
        # Reopen 17:00 CT weekday -> ETH.
        (_ct(2026, 4, 15, 17, 0), "ETH"),
        # Monday 03:00 CT -> OVN continuation of Sun-night open.
        (_ct(2026, 4, 13, 3, 0), "OVN"),
        # Sunday 16:00 CT -> HALT (pre-open).
        (_ct(2026, 4, 12, 16, 0), "HALT"),
        # Sunday 17:00 CT -> OVN (weekly reopen).
        (_ct(2026, 4, 12, 17, 0), "OVN"),
        # Saturday -> HALT.
        (_ct(2026, 4, 11, 12, 0), "HALT"),
        # Friday after 16:00 CT -> HALT (weekend).
        (_ct(2026, 4, 17, 16, 30), "HALT"),
    ],
)
def test_session_of_basic(ts: pd.Timestamp, expected: str) -> None:
    assert session_of(ts) == expected


# -----------------------------------------------------------------------
# Holidays / half-days
# -----------------------------------------------------------------------


def test_full_day_holiday_christmas_2025() -> None:
    # 2025-12-25 is a Thursday holiday.
    t = _ct(2025, 12, 25, 10, 0)
    assert session_of(t) == "HALT"


def test_full_day_holiday_new_years_2026() -> None:
    t = _ct(2026, 1, 1, 9, 0)
    assert session_of(t) == "HALT"


def test_thanksgiving_friday_2025_half_day() -> None:
    # 2025-11-28 close 12:00 CT.
    assert session_of(_ct(2025, 11, 28, 11, 59)) == "RTH"
    assert session_of(_ct(2025, 11, 28, 12, 0)) == "HALT"


def test_christmas_eve_2025_half_day() -> None:
    # 2025-12-24 Wed, close 12:00 CT per CME equity-index schedule.
    assert session_of(_ct(2025, 12, 24, 11, 59)) == "RTH"
    assert session_of(_ct(2025, 12, 24, 12, 0)) == "HALT"


def test_july3_2025_half_day() -> None:
    # 2025-07-03 Thu, close 12:00 CT.
    assert session_of(_ct(2025, 7, 3, 11, 59)) == "RTH"
    assert session_of(_ct(2025, 7, 3, 12, 0)) == "HALT"


def test_july4_2025_early_close() -> None:
    # 2025-07-04 Fri: CME equity futures OPEN with early close at 12:00 CT
    # (not a full holiday — only New Year's and Christmas are full closures).
    assert session_of(_ct(2025, 7, 4, 10, 0)) == "RTH"
    assert session_of(_ct(2025, 7, 4, 12, 0)) == "HALT"


# -----------------------------------------------------------------------
# DST transitions
# -----------------------------------------------------------------------


def test_dst_spring_forward_2026() -> None:
    # 2026-03-08 02:00 CST -> 03:00 CDT. Mon 2026-03-09 RTH still 08:30-15:15 CT.
    t = _ct(2026, 3, 9, 10, 0)
    assert session_of(t) == "RTH"


def test_dst_fall_back_2025() -> None:
    # 2025-11-02 02:00 CDT -> 01:00 CST. Next Monday 2025-11-03 RTH unchanged.
    t = _ct(2025, 11, 3, 10, 0)
    assert session_of(t) == "RTH"


# -----------------------------------------------------------------------
# trading_day
# -----------------------------------------------------------------------


def test_trading_day_daytime() -> None:
    assert trading_day(_ct(2026, 4, 15, 10, 0)) == date(2026, 4, 15)


def test_trading_day_overnight_rolls_forward() -> None:
    # Wed 17:30 CT -> Thu trading day.
    assert trading_day(_ct(2026, 4, 15, 17, 30)) == date(2026, 4, 16)


def test_trading_day_sunday_reopen() -> None:
    # Sun 17:30 CT -> Mon trading day.
    assert trading_day(_ct(2026, 4, 12, 17, 30)) == date(2026, 4, 13)


def test_trading_day_saturday_rolls_to_monday() -> None:
    assert trading_day(_ct(2026, 4, 11, 12, 0)) == date(2026, 4, 13)


def test_trading_day_skips_holiday() -> None:
    # Thu 2025-12-25 holiday; Wed 17:30 CT should map to Fri 2025-12-26.
    assert trading_day(_ct(2025, 12, 24, 17, 30)) == date(2025, 12, 26)


# -----------------------------------------------------------------------
# Property tests
# -----------------------------------------------------------------------

_START = datetime(2024, 1, 1, tzinfo=UTC)
_END = datetime(2027, 12, 31, tzinfo=UTC)
_SECONDS = int((_END - _START).total_seconds())


@given(offset_s=st.integers(min_value=0, max_value=_SECONDS))
@settings(max_examples=500, deadline=None)
def test_rth_only_inside_window(offset_s: int) -> None:
    """RTH is only ever returned inside [08:30, 15:15) CT on weekdays."""
    ts = pd.Timestamp(_START + timedelta(seconds=offset_s))
    label = session_of(ts)
    if label != "RTH":
        return
    local = to_exchange(ts)
    assert local.weekday() < 5
    assert RTH_OPEN <= local.time() < RTH_CLOSE


@given(offset_s=st.integers(min_value=0, max_value=_SECONDS))
@settings(max_examples=300, deadline=None)
def test_trading_day_is_weekday_non_holiday(offset_s: int) -> None:
    """trading_day always returns a weekday that is not a full-day holiday."""
    from skie_ninja.utils.clock import _FULL_DAY_HOLIDAYS  # noqa: PLC0415

    ts = pd.Timestamp(_START + timedelta(seconds=offset_s))
    td = trading_day(ts)
    assert td.weekday() < 5
    assert td not in _FULL_DAY_HOLIDAYS


@given(offset_s=st.integers(min_value=0, max_value=_SECONDS))
@settings(max_examples=200, deadline=None)
def test_session_label_always_valid(offset_s: int) -> None:
    ts = pd.Timestamp(_START + timedelta(seconds=offset_s))
    assert session_of(ts) in {"RTH", "ETH", "OVN", "HALT"}


# -----------------------------------------------------------------------
# Hand-coded vs pandas_market_calendars cross-check (F-2-5).
# Only runs when pandas_market_calendars is importable; skipped otherwise.
# -----------------------------------------------------------------------


def test_hand_coded_holidays_subset_of_mcal() -> None:
    """Fallback holiday/early-close tables must be a subset of mcal's CME_Equity
    schedule for 2024-2027. Divergences indicate a stale hand-coded snapshot.
    """
    mcal = pytest.importorskip("pandas_market_calendars")

    from skie_ninja.utils.clock import (  # noqa: PLC0415
        _EARLY_CLOSES_FALLBACK,
        _FULL_DAY_HOLIDAYS_FALLBACK,
        CME_TZ,
        RTH_CLOSE,
    )

    cal = mcal.get_calendar("CME_Equity")
    start = pd.Timestamp("2024-01-01")
    end = pd.Timestamp("2028-01-01")
    sched = cal.schedule(start_date=start, end_date=end)

    all_weekdays = pd.bdate_range(start=start, end=end)
    trading_days = pd.DatetimeIndex(sched.index)
    mcal_holidays = {d.date() for d in all_weekdays.difference(trading_days)}

    fallback_in_window = {
        d for d in _FULL_DAY_HOLIDAYS_FALLBACK if 2024 <= d.year <= 2027
    }
    divergent_holidays = fallback_in_window - mcal_holidays
    assert not divergent_holidays, (
        "Hand-coded _FULL_DAY_HOLIDAYS_FALLBACK contains dates NOT present in "
        f"pandas_market_calendars CME_Equity: {sorted(divergent_holidays)}. "
        "Refresh the snapshot against the CME holiday calendar."
    )

    mcal_early: dict = {}
    for idx, row in sched.iterrows():
        close_ct = row["market_close"].tz_convert(CME_TZ)
        if close_ct.time() < RTH_CLOSE:
            mcal_early[idx.date()] = close_ct.time()
    fallback_early_in_window = {
        d: t for d, t in _EARLY_CLOSES_FALLBACK.items() if 2024 <= d.year <= 2027
    }
    divergent_early = {
        d: t for d, t in fallback_early_in_window.items() if d not in mcal_early
    }
    assert not divergent_early, (
        "Hand-coded _EARLY_CLOSES_FALLBACK contains dates NOT present as "
        f"early-close sessions in pandas_market_calendars: {sorted(divergent_early)}. "
        "Refresh the snapshot against the CME holiday calendar."
    )


# -----------------------------------------------------------------------
# Energy / metals 24/5 session convention (H060 / ADR-0023 §Decision 3).
# Holiday-shortened sessions are NOT in v1 scope per the H060 brief;
# deferred to P1-CLOCK-ENERGY-METALS-HOLIDAY-CALENDAR.
# -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "ts,expected",
    [
        # Active session — Mon 09:30 CT.
        (_ct(2026, 4, 13, 9, 30), SessionKind.ACTIVE),
        # Maintenance break — Tue 16:30 CT (inside (16:00, 17:00) Mon-Thu).
        (_ct(2026, 4, 14, 16, 30), SessionKind.MAINTENANCE_BREAK),
        # Weekend closed — Sat 12:00 CT.
        (_ct(2026, 4, 11, 12, 0), SessionKind.WEEKEND_CLOSED),
        # Boundary 16:00 CT exactly (Tue close) — ACTIVE per closing-tick-inclusive.
        (_ct(2026, 4, 14, 16, 0), SessionKind.ACTIVE),
        # Boundary 17:00 CT exactly (Tue reopen) — ACTIVE per opening-tick-inclusive.
        (_ct(2026, 4, 14, 17, 0), SessionKind.ACTIVE),
        # Boundary 16:00:01 CT (Tue) — MAINTENANCE_BREAK (just past close).
        (_ct(2026, 4, 14, 16, 0) + pd.Timedelta(seconds=1), SessionKind.MAINTENANCE_BREAK),
        # Boundary 16:59:59 CT (Tue) — MAINTENANCE_BREAK (just before reopen).
        (_ct(2026, 4, 14, 17, 0) - pd.Timedelta(seconds=1), SessionKind.MAINTENANCE_BREAK),
        # Friday 16:00 CT exactly — ACTIVE (weekly close tick included).
        (_ct(2026, 4, 17, 16, 0), SessionKind.ACTIVE),
        # Friday 16:00:01 CT — WEEKEND_CLOSED (weekly close begins).
        (_ct(2026, 4, 17, 16, 0) + pd.Timedelta(seconds=1), SessionKind.WEEKEND_CLOSED),
        # Sunday 16:59 CT — WEEKEND_CLOSED (pre-reopen).
        (_ct(2026, 4, 12, 16, 59), SessionKind.WEEKEND_CLOSED),
        # Sunday 17:00 CT — ACTIVE (weekly reopen tick).
        (_ct(2026, 4, 12, 17, 0), SessionKind.ACTIVE),
        # Sunday 20:00 CT — ACTIVE (post-reopen Globus ramp).
        (_ct(2026, 4, 12, 20, 0), SessionKind.ACTIVE),
        # Monday 03:00 CT — ACTIVE (overnight ramp continuation).
        (_ct(2026, 4, 13, 3, 0), SessionKind.ACTIVE),
    ],
)
def test_classify_energy_metals_session(
    ts: pd.Timestamp, expected: SessionKind
) -> None:
    assert classify_energy_metals_session(ts) is expected


def test_is_energy_metals_session_active_matches_classifier() -> None:
    # ACTIVE.
    assert is_energy_metals_session_active(_ct(2026, 4, 13, 9, 30)) is True
    # MAINTENANCE_BREAK.
    assert is_energy_metals_session_active(_ct(2026, 4, 14, 16, 30)) is False
    # WEEKEND_CLOSED.
    assert is_energy_metals_session_active(_ct(2026, 4, 11, 12, 0)) is False


def test_energy_metals_dst_spring_forward_2024() -> None:
    # 2024-03-10 02:00 CST -> 03:00 CDT (US spring-forward).
    # The active session that began Fri 2024-03-08 17:00 CT (Sun-night reopen
    # at 17:00 CDT) must continue uninterrupted across the DST shift.
    # Sun 2024-03-10 18:30 CT (post-reopen, post-DST) -> ACTIVE.
    assert (
        classify_energy_metals_session(_ct(2024, 3, 10, 18, 30))
        is SessionKind.ACTIVE
    )
    # Mon 2024-03-11 02:30 CDT (deep overnight, post-DST) -> ACTIVE.
    assert (
        classify_energy_metals_session(_ct(2024, 3, 11, 2, 30))
        is SessionKind.ACTIVE
    )
    # Mon 2024-03-11 16:30 CDT (maintenance break, post-DST).
    assert (
        classify_energy_metals_session(_ct(2024, 3, 11, 16, 30))
        is SessionKind.MAINTENANCE_BREAK
    )


def test_energy_metals_dst_fall_back_2024() -> None:
    # 2024-11-03 02:00 CDT -> 01:00 CST (US fall-back).
    # Sun 2024-11-03 18:30 CT (post-reopen, post-DST) -> ACTIVE.
    assert (
        classify_energy_metals_session(_ct(2024, 11, 3, 18, 30))
        is SessionKind.ACTIVE
    )
    # Mon 2024-11-04 01:30 CST (deep overnight, post-DST) -> ACTIVE.
    assert (
        classify_energy_metals_session(_ct(2024, 11, 4, 1, 30))
        is SessionKind.ACTIVE
    )
    # Mon 2024-11-04 16:30 CST -> MAINTENANCE_BREAK.
    assert (
        classify_energy_metals_session(_ct(2024, 11, 4, 16, 30))
        is SessionKind.MAINTENANCE_BREAK
    )


def test_energy_metals_utc_input_handled() -> None:
    # 14:30 UTC on Mon 2026-04-13 = 09:30 CT (CDT in April) -> ACTIVE.
    ts = pd.Timestamp("2026-04-13 14:30", tz="UTC")
    assert classify_energy_metals_session(ts) is SessionKind.ACTIVE
    # 22:30 UTC on Mon 2026-04-13 = 17:30 CT -> ACTIVE (post-reopen).
    ts = pd.Timestamp("2026-04-13 22:30", tz="UTC")
    assert classify_energy_metals_session(ts) is SessionKind.ACTIVE


def test_energy_metals_naive_input_treated_as_utc() -> None:
    # Naive ts at 14:30 UTC on Mon 2026-04-13 -> 09:30 CDT -> ACTIVE.
    ts = pd.Timestamp("2026-04-13 14:30")
    assert classify_energy_metals_session(ts) is SessionKind.ACTIVE
