"""CME exchange-aware clock.

Implements P0-3 per plan/buildouts/implementation-plan_2026-04-15.md §P0-3.

Session taxonomy (four-category enum, exactly as specified):
    RTH  : 08:30-15:15 CT weekday, exchange open
    ETH  : Sun 17:00 CT through Fri 16:00 CT weekday hours outside RTH,
           excluding the daily 16:00-17:00 CT maintenance halt
    OVN  : Sunday pre-open and weekend ETH-equivalent ramp
           (CME Globex equity-index opens Sun 17:00 CT)
    HALT : daily 16:00-17:00 CT maintenance halt, full-day holidays,
           and early-close overhang

CME Globex equity-index futures trading hours reference:
    https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.contractSpecs.html
    https://www.cmegroup.com/trading-hours.html

Holiday calendar strategy:
    We rely on `pandas_market_calendars` with the "CME_Equity" calendar when
    available (maintained calendar sourced from the CME product calendar:
    https://www.cmegroup.com/tools-information/holiday-calendar.html).
    If `pandas_market_calendars` is not installed, we fall back to a hand-coded
    CME equity-index holiday / half-day set for 2024-2027, documented inline,
    which the user MUST refresh annually from the CME product calendar page.

CME equity-index full closures are limited to New Year's Day and Christmas
    (and extraordinary closures like 2025-01-09 Carter funeral). Most federal
    holidays (MLK, Presidents, Good Friday, Memorial, Juneteenth, July 4,
    Labor Day, Thanksgiving) are early-close days, NOT full closures.

Early-close convention (per CME equity-index calendar):
    - Good Friday: 08:15 CT close (no RTH session)
    - All other holiday-adjacent dates: 12:00 CT close

References:
    - CME Group holiday calendar (annual publication, user refresh each Dec)
      Snapshot retrieved 2026-04-15 from
      https://www.cmegroup.com/tools-information/holiday-calendar.html
      # TODO: refresh annually (Phase-1 follow-up P1-CAL-REFRESH)
    - pandas_market_calendars: Ryan Sheftel et al.,
      https://github.com/rsheftel/pandas_market_calendars
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal
from zoneinfo import ZoneInfo

import pandas as pd

CME_TZ = ZoneInfo("America/Chicago")

RTH_OPEN = time(8, 30)
RTH_CLOSE = time(15, 15)
ETH_OPEN = time(17, 0)  # daily reopen; Sunday is also 17:00 CT
ETH_CLOSE = time(16, 0)  # daily halt begins at 16:00
HALT_START = time(16, 0)
HALT_END = time(17, 0)

SessionLabel = Literal["RTH", "ETH", "OVN", "HALT"]


# ---------------------------------------------------------------------------
# Holiday / early-close tables.
# Hand-coded fallback sourced from the CME Group holiday calendar,
# https://www.cmegroup.com/tools-information/holiday-calendar.html
# User MUST refresh this table annually (see module docstring).
# ---------------------------------------------------------------------------

# Full-day equity-index futures closures (CME Equity).
# CME Globex equity-index futures are fully closed ONLY on New Year's Day,
# Christmas Day, and extraordinary closures. Most federal holidays are
# early-close days (see _EARLY_CLOSES_FALLBACK below).
# Source: pandas_market_calendars CME_Equity, cross-checked against
# https://www.cmegroup.com/tools-information/holiday-calendar.html
# Snapshot retrieved 2026-04-15.
_FULL_DAY_HOLIDAYS_FALLBACK: frozenset[date] = frozenset(
    {
        date(2024, 1, 1),   # New Year's Day
        date(2024, 12, 25),  # Christmas
        date(2025, 1, 1),   # New Year's Day
        date(2025, 1, 9),   # Carter funeral (extraordinary)
        date(2025, 12, 25),  # Christmas
        date(2026, 1, 1),   # New Year's Day
        date(2026, 12, 25),  # Christmas
        date(2027, 1, 1),   # New Year's Day
        date(2027, 12, 24),  # Christmas observed (Dec 25 is Saturday)
    }
)

# Early-close dates -> local CT close time for equity-index futures.
# Most federal holidays are early-close (12:00 CT), not full closure.
# Good Friday closes at 08:15 CT (no RTH session).
# Source: pandas_market_calendars CME_Equity, snapshot 2026-04-15.
_EARLY_CLOSES_FALLBACK: dict[date, time] = {
    # 2024
    date(2024, 1, 15): time(12, 0),   # MLK
    date(2024, 2, 19): time(12, 0),   # Presidents Day
    date(2024, 3, 29): time(8, 15),   # Good Friday
    date(2024, 5, 27): time(12, 0),   # Memorial Day
    date(2024, 6, 19): time(12, 0),   # Juneteenth
    date(2024, 7, 3): time(12, 0),    # July 3
    date(2024, 7, 4): time(12, 0),    # July 4
    date(2024, 9, 2): time(12, 0),    # Labor Day
    date(2024, 11, 28): time(12, 0),  # Thanksgiving
    date(2024, 11, 29): time(12, 0),  # Day after Thanksgiving
    date(2024, 12, 24): time(12, 0),  # Christmas Eve
    # 2025
    date(2025, 1, 20): time(12, 0),   # MLK
    date(2025, 2, 17): time(12, 0),   # Presidents Day
    date(2025, 4, 18): time(8, 15),   # Good Friday
    date(2025, 5, 26): time(12, 0),   # Memorial Day
    date(2025, 6, 19): time(12, 0),   # Juneteenth
    date(2025, 7, 3): time(12, 0),    # July 3
    date(2025, 7, 4): time(12, 0),    # July 4
    date(2025, 9, 1): time(12, 0),    # Labor Day
    date(2025, 11, 27): time(12, 0),  # Thanksgiving
    date(2025, 11, 28): time(12, 0),  # Day after Thanksgiving
    date(2025, 12, 24): time(12, 0),  # Christmas Eve
    # 2026
    date(2026, 1, 19): time(12, 0),   # MLK
    date(2026, 2, 16): time(12, 0),   # Presidents Day
    date(2026, 4, 3): time(8, 15),    # Good Friday
    date(2026, 5, 25): time(12, 0),   # Memorial Day
    date(2026, 6, 19): time(12, 0),   # Juneteenth
    date(2026, 7, 3): time(12, 0),    # July 4 observed (Sat)
    date(2026, 9, 7): time(12, 0),    # Labor Day
    date(2026, 11, 26): time(12, 0),  # Thanksgiving
    date(2026, 11, 27): time(12, 0),  # Day after Thanksgiving
    date(2026, 12, 24): time(12, 0),  # Christmas Eve
    # 2027
    date(2027, 1, 18): time(12, 0),   # MLK
    date(2027, 2, 15): time(12, 0),   # Presidents Day
    date(2027, 3, 26): time(8, 15),   # Good Friday
    date(2027, 5, 31): time(12, 0),   # Memorial Day
    date(2027, 6, 18): time(12, 0),   # Juneteenth observed
    date(2027, 7, 5): time(12, 0),    # July 4 observed (Sun)
    date(2027, 9, 6): time(12, 0),    # Labor Day
    date(2027, 11, 25): time(12, 0),  # Thanksgiving
    date(2027, 11, 26): time(12, 0),  # Day after Thanksgiving
}


def _load_market_calendar() -> tuple[frozenset[date], dict[date, time]]:
    """Attempt to load CME_Equity from pandas_market_calendars; fall back."""
    try:
        import pandas_market_calendars as mcal  # type: ignore[import-untyped]
    except ImportError:
        return _FULL_DAY_HOLIDAYS_FALLBACK, _EARLY_CLOSES_FALLBACK

    try:
        cal = mcal.get_calendar("CME_Equity")
    except Exception:
        return _FULL_DAY_HOLIDAYS_FALLBACK, _EARLY_CLOSES_FALLBACK

    start = pd.Timestamp("2024-01-01")
    end = pd.Timestamp("2028-01-01")
    sched = cal.schedule(start_date=start, end_date=end)
    # Full-day holidays = weekdays in range absent from schedule.
    all_weekdays = pd.bdate_range(start=start, end=end)
    trading_days = pd.DatetimeIndex(sched.index)
    holidays = frozenset(
        d.date() for d in all_weekdays.difference(trading_days)
    )
    # Early-closes: days where market_close-CT is earlier than 15:15 CT.
    early: dict[date, time] = {}
    for idx, row in sched.iterrows():
        close_ct = row["market_close"].tz_convert(CME_TZ)
        if close_ct.time() < RTH_CLOSE:
            early[idx.date()] = close_ct.time()
    # Merge fallback where library data missing the equity-index specific
    # 12:00/12:15 CT convention.
    merged = {**_EARLY_CLOSES_FALLBACK, **early}
    return holidays, merged


_FULL_DAY_HOLIDAYS, _EARLY_CLOSES = _load_market_calendar()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def to_exchange(ts: pd.Timestamp | datetime) -> pd.Timestamp:
    """Convert any timestamp (naive-UTC or tz-aware) to CME local time.

    Naive input is interpreted as UTC (consistent with vendor tick files
    that record `ts_event_ns` in epoch nanoseconds UTC).
    """
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return t.tz_convert(CME_TZ)


def _is_full_holiday(d: date) -> bool:
    return d in _FULL_DAY_HOLIDAYS


def session_of(ts: pd.Timestamp | datetime) -> SessionLabel:
    """Return session label for a timestamp.

    Guarantee (property-tested): returns 'RTH' only when converted
    CT-local time is Mon-Fri, not a holiday, not an early-close-overhang,
    and falls in [08:30, 15:15).
    """
    local = to_exchange(ts)
    d = local.date()
    wday = local.weekday()  # Mon=0..Sun=6
    t_local = local.time()

    if _is_full_holiday(d):
        return "HALT"

    # Saturday: exchange closed all day (between Fri 16:00 and Sun 17:00).
    if wday == 5:
        return "HALT"

    # Sunday: closed until 17:00 CT; 17:00-24:00 is the OVN open.
    if wday == 6:
        if t_local < ETH_OPEN:
            return "HALT"
        return "OVN"

    # Weekdays Mon-Fri.
    # Daily maintenance halt 16:00-17:00 CT applies Mon-Thu (reopens at 17:00).
    # On Friday the 16:00 CT close is the weekly close.
    if wday == 4 and t_local >= HALT_START:  # Friday after 16:00
        return "HALT"
    if HALT_START <= t_local < HALT_END:
        return "HALT"

    # Early close handling (e.g., 12:00 CT half-days).
    early_close = _EARLY_CLOSES.get(d)
    if early_close is not None and t_local >= early_close:
        return "HALT"

    # RTH window, weekday only, not a holiday/early-close overhang.
    if RTH_OPEN <= t_local < RTH_CLOSE:
        if early_close is not None and early_close <= RTH_OPEN:
            # Degenerate early close before RTH would have opened.
            return "HALT"
        return "RTH"

    # Monday pre-open: [00:00, 17:00 prev Sun means we are in Monday).
    # Monday 00:00-08:30 is continuation of Sunday's OVN ramp -> OVN.
    if wday == 0 and t_local < RTH_OPEN:
        return "OVN"

    # Otherwise weekday ETH: after RTH close (15:15-16:00) or after 17:00 reopen.
    return "ETH"


def trading_day(ts: pd.Timestamp | datetime) -> date:
    """Return CME trading-session date for a timestamp.

    Convention: overnight session (17:00 CT reopen onward) maps to the
    NEXT calendar trading day. This matches CME daily-settlement convention
    where trade date rolls at 17:00 CT.
    """
    local = to_exchange(ts)
    wday = local.weekday()
    t_local = local.time()

    # Sunday 17:00+ -> Monday trading day.
    if wday == 6 and t_local >= ETH_OPEN:
        return _advance_to_trading_day(local.date() + pd.Timedelta(days=1).to_pytimedelta())

    # Mon-Thu after 17:00 CT -> next calendar day's trading session.
    if wday in (0, 1, 2, 3) and t_local >= ETH_OPEN:
        return _advance_to_trading_day(local.date() + pd.Timedelta(days=1).to_pytimedelta())

    # Friday after 16:00 -> weekend, next trading day is Monday.
    if wday == 4 and t_local >= HALT_START:
        return _advance_to_trading_day(local.date() + pd.Timedelta(days=3).to_pytimedelta())

    # Saturday -> Monday.
    if wday == 5:
        return _advance_to_trading_day(local.date() + pd.Timedelta(days=2).to_pytimedelta())

    # Sunday pre-17:00 -> Monday.
    if wday == 6:
        return _advance_to_trading_day(local.date() + pd.Timedelta(days=1).to_pytimedelta())

    # Otherwise the current calendar date is the trading day.
    return _advance_to_trading_day(local.date())


def _advance_to_trading_day(d: date) -> date:
    """Skip forward over weekends and full-day holidays."""
    cur = d
    while cur.weekday() >= 5 or _is_full_holiday(cur):
        cur = cur + pd.Timedelta(days=1).to_pytimedelta()
    return cur


__all__ = [
    "CME_TZ",
    "SessionLabel",
    "session_of",
    "to_exchange",
    "trading_day",
]
