"""Unit tests for the H055 §4 news-calendar module.

Coverage:
- NewsRelease dataclass: validation, immutability.
- NewsCalendar: is_in_news_window, get_active_release, multi-release overlap,
  edge of window, payload_sha256 reproducibility.
- static_h055_window_calendar: coverage of 2020-2025 window; expected counts.
- merge_calendars: dedup by (indicator_id, timestamp).
- API loaders: NotImplementedError + clear follow-up cross-link.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from skie_ninja.utils.news_calendar import (
    DEFAULT_WINDOW_MINUTES,
    NewsCalendar,
    NewsRelease,
    load_bls_calendar,
    load_fomc_calendar_from_fred,
    merge_calendars,
    static_h055_window_calendar,
)

ET = ZoneInfo("America/New_York")
UTC = timezone.utc


# ─── NewsRelease ─────────────────────────────────────────────────────────────


def test_news_release_construction_valid() -> None:
    r = NewsRelease(
        indicator_id="FOMC",
        release_timestamp_utc=datetime(2024, 6, 12, 18, 0, tzinfo=UTC),
        window_minutes=15,
    )
    assert r.indicator_id == "FOMC"
    assert r.window_minutes == 15
    assert r.provenance == "unspecified"


def test_news_release_rejects_unknown_indicator_id() -> None:
    with pytest.raises(ValueError, match="indicator_id"):
        NewsRelease(
            indicator_id="GDP",
            release_timestamp_utc=datetime(2024, 1, 1, tzinfo=UTC),
            window_minutes=10,
        )


def test_news_release_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="window_minutes"):
        NewsRelease(
            indicator_id="FOMC",
            release_timestamp_utc=datetime(2024, 1, 1, tzinfo=UTC),
            window_minutes=0,
        )


def test_news_release_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        NewsRelease(
            indicator_id="FOMC",
            release_timestamp_utc=datetime(2024, 1, 1),  # naive
            window_minutes=15,
        )


def test_news_release_immutable() -> None:
    r = NewsRelease(
        indicator_id="FOMC",
        release_timestamp_utc=datetime(2024, 1, 1, tzinfo=UTC),
        window_minutes=15,
    )
    with pytest.raises(Exception):
        r.window_minutes = 30  # type: ignore[misc]


# ─── DEFAULT_WINDOW_MINUTES ──────────────────────────────────────────────────


def test_default_windows_match_design_md_section_4() -> None:
    # Per H055 design.md §4 (Lucca-Moench 2015 binding):
    assert DEFAULT_WINDOW_MINUTES == {"FOMC": 15, "NFP": 5, "CPI": 5}


# ─── NewsCalendar ────────────────────────────────────────────────────────────


def test_news_calendar_empty_returns_no_active_release() -> None:
    cal = NewsCalendar(releases=())
    ts = datetime(2024, 6, 12, 18, 0, tzinfo=UTC)
    assert cal.is_in_news_window(ts) is False
    assert cal.get_active_release(ts) is None


def test_news_calendar_inside_window_returns_release() -> None:
    release = NewsRelease(
        indicator_id="FOMC",
        release_timestamp_utc=datetime(2024, 6, 12, 18, 0, tzinfo=UTC),
        window_minutes=15,
    )
    cal = NewsCalendar(releases=(release,))

    # 5 minutes before release: inside ±15 window
    ts = datetime(2024, 6, 12, 17, 55, tzinfo=UTC)
    assert cal.is_in_news_window(ts) is True
    assert cal.get_active_release(ts) == release


def test_news_calendar_at_exact_release_timestamp() -> None:
    release = NewsRelease(
        indicator_id="FOMC",
        release_timestamp_utc=datetime(2024, 6, 12, 18, 0, tzinfo=UTC),
        window_minutes=15,
    )
    cal = NewsCalendar(releases=(release,))
    assert cal.is_in_news_window(release.release_timestamp_utc) is True


def test_news_calendar_at_window_boundary_inclusive() -> None:
    release = NewsRelease(
        indicator_id="FOMC",
        release_timestamp_utc=datetime(2024, 6, 12, 18, 0, tzinfo=UTC),
        window_minutes=15,
    )
    cal = NewsCalendar(releases=(release,))
    # Exactly 15 minutes after: inside (inclusive boundary)
    ts = datetime(2024, 6, 12, 18, 15, tzinfo=UTC)
    assert cal.is_in_news_window(ts) is True


def test_news_calendar_outside_window_returns_none() -> None:
    release = NewsRelease(
        indicator_id="NFP",
        release_timestamp_utc=datetime(2024, 6, 7, 12, 30, tzinfo=UTC),  # 08:30 ET = 12:30 UTC summer
        window_minutes=5,
    )
    cal = NewsCalendar(releases=(release,))

    # 10 minutes before: outside ±5 window
    ts = datetime(2024, 6, 7, 12, 20, tzinfo=UTC)
    assert cal.is_in_news_window(ts) is False
    assert cal.get_active_release(ts) is None


def test_news_calendar_rejects_naive_query() -> None:
    cal = NewsCalendar(releases=())
    with pytest.raises(ValueError, match="timezone-aware"):
        cal.is_in_news_window(datetime(2024, 6, 12))  # naive


def test_news_calendar_overlapping_windows_returns_closest() -> None:
    # Two releases coincidentally close (e.g., NFP + CPI on same day).
    nfp = NewsRelease(
        indicator_id="NFP",
        release_timestamp_utc=datetime(2024, 6, 7, 12, 30, tzinfo=UTC),
        window_minutes=5,
    )
    cpi = NewsRelease(
        indicator_id="CPI",
        release_timestamp_utc=datetime(2024, 6, 7, 12, 32, tzinfo=UTC),
        window_minutes=5,
    )
    cal = NewsCalendar(releases=(nfp, cpi))
    # Probe at 12:31 UTC: closer to NFP (1 min away) than CPI (1 min away too).
    # Tie-break by closer center; if equal, NFP wins (sort order).
    ts = datetime(2024, 6, 7, 12, 31, tzinfo=UTC)
    active = cal.get_active_release(ts)
    assert active is not None
    # 12:31 is 1 min after NFP center, 1 min before CPI center → equal distance;
    # NewsCalendar's iteration finds NFP first by sort order.
    assert active.indicator_id == "NFP"

    # Probe further: 12:33 is 3 min after NFP, 1 min after CPI → CPI is closer.
    ts2 = datetime(2024, 6, 7, 12, 33, tzinfo=UTC)
    active2 = cal.get_active_release(ts2)
    assert active2 is not None
    assert active2.indicator_id == "CPI"


def test_news_calendar_sorted_by_timestamp() -> None:
    # Construct out-of-order; verify internal sort.
    r1 = NewsRelease(
        indicator_id="NFP",
        release_timestamp_utc=datetime(2024, 6, 7, 12, 30, tzinfo=UTC),
        window_minutes=5,
    )
    r2 = NewsRelease(
        indicator_id="FOMC",
        release_timestamp_utc=datetime(2024, 1, 31, 19, 0, tzinfo=UTC),
        window_minutes=15,
    )
    cal = NewsCalendar(releases=(r1, r2))
    # First release after sort should be r2 (Jan) before r1 (Jun)
    assert cal.releases[0].release_timestamp_utc < cal.releases[1].release_timestamp_utc


def test_news_calendar_sha256_reproducible() -> None:
    a = NewsCalendar(releases=tuple(static_h055_window_calendar()))
    b = NewsCalendar(releases=tuple(static_h055_window_calendar()))
    assert a.payload_sha256() == b.payload_sha256()
    assert len(a.payload_sha256()) == 64  # SHA256 hex length


def test_news_calendar_sha256_changes_under_release_modification() -> None:
    base = NewsCalendar(releases=tuple(static_h055_window_calendar()))
    extended_releases = tuple(static_h055_window_calendar()) + (
        NewsRelease(
            indicator_id="FOMC",
            release_timestamp_utc=datetime(2026, 1, 28, 19, 0, tzinfo=UTC),
            window_minutes=15,
            provenance="extension-test",
        ),
    )
    extended = NewsCalendar(releases=extended_releases)
    assert base.payload_sha256() != extended.payload_sha256()


# ─── static_h055_window_calendar ─────────────────────────────────────────────


def test_static_calendar_covers_h055_window() -> None:
    releases = static_h055_window_calendar()
    # Coverage: 6 years × 8 FOMC + 12 NFP + 12 CPI = 192 expected.
    assert len(releases) == 6 * (8 + 12 + 12)


def test_static_calendar_indicator_counts() -> None:
    releases = static_h055_window_calendar()
    counts = {"FOMC": 0, "NFP": 0, "CPI": 0}
    for r in releases:
        counts[r.indicator_id] += 1
    assert counts == {"FOMC": 6 * 8, "NFP": 6 * 12, "CPI": 6 * 12}


def test_static_calendar_provenance_tagged_preliminary() -> None:
    releases = static_h055_window_calendar()
    for r in releases:
        assert r.provenance == "static-h055-curation-2026-05-09-PRELIMINARY"


def test_static_calendar_releases_within_h055_window() -> None:
    releases = static_h055_window_calendar()
    earliest = min(r.release_timestamp_utc for r in releases)
    latest = max(r.release_timestamp_utc for r in releases)
    assert earliest.year == 2020
    assert latest.year == 2025


def test_static_calendar_fomc_release_at_14_00_et() -> None:
    # Spot-check: FOMC press release scheduled at 14:00 ET. Pick a
    # standard-time meeting (Jan 29, 2025 — winter, EST = UTC-5):
    cal = NewsCalendar.from_static_h055_window()
    target_release = next(
        r for r in cal.releases
        if r.indicator_id == "FOMC"
        and r.release_timestamp_utc.year == 2025
        and r.release_timestamp_utc.month == 1
    )
    # 14:00 ET in January = 19:00 UTC (EST = UTC-5)
    et_local = target_release.release_timestamp_utc.astimezone(ET)
    assert et_local.hour == 14 and et_local.minute == 0


def test_static_calendar_bls_release_at_08_30_et() -> None:
    # Spot-check: NFP/CPI release at 08:30 ET.
    cal = NewsCalendar.from_static_h055_window()
    target = next(
        r for r in cal.releases
        if r.indicator_id == "NFP" and r.release_timestamp_utc.year == 2025
    )
    et_local = target.release_timestamp_utc.astimezone(ET)
    assert et_local.hour == 8 and et_local.minute == 30


# ─── merge_calendars ─────────────────────────────────────────────────────────


def test_merge_calendars_dedups_by_indicator_and_timestamp() -> None:
    r = NewsRelease(
        indicator_id="FOMC",
        release_timestamp_utc=datetime(2024, 6, 12, 18, 0, tzinfo=UTC),
        window_minutes=15,
    )
    merged = merge_calendars([r], [r], [r])
    assert merged.n_releases() == 1


def test_merge_calendars_combines_disjoint_sources() -> None:
    fomc = NewsRelease(
        indicator_id="FOMC",
        release_timestamp_utc=datetime(2024, 6, 12, 18, 0, tzinfo=UTC),
        window_minutes=15,
    )
    nfp = NewsRelease(
        indicator_id="NFP",
        release_timestamp_utc=datetime(2024, 6, 7, 12, 30, tzinfo=UTC),
        window_minutes=5,
    )
    merged = merge_calendars([fomc], [nfp])
    assert merged.n_releases() == 2


# ─── Edge cases on the static calendar ───────────────────────────────────────


def test_static_calendar_h055_window_end_to_end() -> None:
    cal = NewsCalendar.from_static_h055_window()
    # A real FOMC date: 2024-06-12, 14:00 ET = 18:00 UTC (summer DST).
    inside_fomc_window = datetime(2024, 6, 12, 18, 5, tzinfo=UTC)
    outside_window = datetime(2024, 6, 12, 19, 0, tzinfo=UTC)  # 1 hour after
    assert cal.is_in_news_window(inside_fomc_window) is True
    assert cal.is_in_news_window(outside_window) is False


def test_static_calendar_dst_transition_window() -> None:
    cal = NewsCalendar.from_static_h055_window()
    # A real winter-period FOMC: 2025-01-29, 14:00 EST = 19:00 UTC.
    winter_fomc_inside = datetime(2025, 1, 29, 19, 5, tzinfo=UTC)
    assert cal.is_in_news_window(winter_fomc_inside) is True
    # Same calendar wall-clock (19:05 UTC) one day BEFORE: outside window.
    outside_winter = datetime(2025, 1, 28, 19, 5, tzinfo=UTC)
    assert cal.is_in_news_window(outside_winter) is False


# ─── API loaders ─────────────────────────────────────────────────────────────


def test_load_fomc_from_fred_pending_follow_up() -> None:
    with pytest.raises(NotImplementedError, match="P1-NEWS-CALENDAR-API-LOADERS"):
        load_fomc_calendar_from_fred()


def test_load_bls_pending_follow_up() -> None:
    with pytest.raises(NotImplementedError, match="P1-NEWS-CALENDAR-API-LOADERS"):
        load_bls_calendar(indicator_id="NFP", start_year=2020, end_year=2025)
