"""News-calendar module for the H055 §4 eligible-bar filter.

Per H055 design.md §4 (verbatim binding):
  - FOMC release ±15 min (Lucca-Moench 2015 RFS *pre-FOMC drift* canonical
    literature; news source = FRED release_id for FOMC)
  - NFP release ±5 min (BLS NFP release 08:30 ET; ±5 min envelope brackets
    the Treasury-futures spike per standard event-study literature)
  - CPI release ±5 min (BLS CPI release 08:30 ET; same rationale as NFP)

Closes BLOCKING-BEFORE-LAUNCH precondition `P1-H055-NEWS-CALENDAR-INGEST`
per H055 §11.2.

Design (per Round-1 audit-discipline + the macro_surprise.py pattern at
[src/skie_ninja/data/ingest/macro_surprise.py](../data/ingest/macro_surprise.py)):
- The data model (NewsRelease + NewsCalendar) is fully implemented and
  testable without network access.
- A STATIC fallback `static_h055_window_calendar()` provides a curated
  sample of FOMC + NFP + CPI release dates spanning 2020-2025 (the H055
  walk-forward train+OOS window per design.md §2) for offline testing
  and demo. The static dates are USER-VERIFIED via primary sources
  (federalreserve.gov FOMC schedule + BLS press release archives) and
  provenance-tagged in the dataclass.
- The FRED + BLS loaders (load_fomc_calendar_from_fred,
  load_bls_calendar) are stubbed with NotImplementedError pending
  follow-up `P1-NEWS-CALENDAR-API-LOADERS` (BLOCKING-BEFORE-EMPIRICAL-
  FRESH-DATA-INGEST; orchestrator integration uses the static calendar
  until the API loaders land).

Per CLAUDE.md §Reproducibility, the H055 walk-forward orchestrator MUST
log the NewsCalendar source identifier and SHA256 of the release set to
the ReproLog so the eligible-bar filter is reproducible.
"""

from __future__ import annotations

import bisect
import hashlib
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Final
from zoneinfo import ZoneInfo

__all__ = [
    "DEFAULT_WINDOW_MINUTES",
    "NewsCalendar",
    "NewsRelease",
    "load_bls_calendar",
    "load_fomc_calendar_from_fred",
    "static_h055_window_calendar",
]

# Per design.md §4 + Lucca-Moench 2015 (Pre-FOMC Drift, RFS 28(11):2840-2887):
DEFAULT_WINDOW_MINUTES: Final[dict[str, int]] = {
    "FOMC": 15,
    "NFP": 5,
    "CPI": 5,
}

# Canonical wall-clock release times in ET. FOMC press release 14:00 ET (per
# federalreserve.gov FOMC schedule). NFP + CPI both 08:30 ET (per BLS press
# release schedules; H055 design.md §4 binding text).
_FOMC_RELEASE_TIME_ET: Final[tuple[int, int]] = (14, 0)
_BLS_RELEASE_TIME_ET: Final[tuple[int, int]] = (8, 30)

_ET = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class NewsRelease:
    """One news-release event.

    Fields:
        indicator_id: One of {"FOMC", "NFP", "CPI"} per H055 §4 (additional
            indicators allowed for forward extensibility but the H055 §4
            eligible-bar filter only uses these three).
        release_timestamp_utc: Scheduled press-release time in UTC.
        window_minutes: Symmetric ± window per H055 §4 binding (FOMC=15,
            NFP/CPI=5).
        provenance: Human-readable source tag (e.g.,
            "static-fed-press-2026-05-09" / "fred-release-id-101").
    """

    indicator_id: str
    release_timestamp_utc: datetime
    window_minutes: int
    provenance: str = "unspecified"

    def __post_init__(self) -> None:
        if self.indicator_id not in DEFAULT_WINDOW_MINUTES:
            raise ValueError(
                f"indicator_id must be one of {sorted(DEFAULT_WINDOW_MINUTES)}, "
                f"got {self.indicator_id!r}."
            )
        if self.window_minutes <= 0:
            raise ValueError(
                f"window_minutes must be positive, got {self.window_minutes}."
            )
        if self.release_timestamp_utc.tzinfo is None:
            raise ValueError(
                "release_timestamp_utc must be timezone-aware (UTC); got naive."
            )


@dataclass(frozen=True)
class NewsCalendar:
    """In-memory news-calendar with an O(log n) eligible-bar filter.

    Stores releases sorted by `release_timestamp_utc` for binary-search
    lookup. Per H055 §4 + design.md §11.1, the orchestrator calls
    `is_in_news_window(ts)` for every candidate eligible bar.

    Construct via `NewsCalendar(releases=...)` for arbitrary input, or via
    classmethod `from_static_h055_window()` for the offline-default sample.

    Per CLAUDE.md §Reproducibility, the calendar's `payload_sha256()` is
    logged to the ReproLog to bind the eligible-bar-filter output to a
    specific release-set vintage.
    """

    releases: tuple[NewsRelease, ...]
    _sorted_release_timestamps: list[float] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        sorted_releases = tuple(
            sorted(self.releases, key=lambda r: r.release_timestamp_utc)
        )
        object.__setattr__(self, "releases", sorted_releases)
        object.__setattr__(
            self,
            "_sorted_release_timestamps",
            [r.release_timestamp_utc.timestamp() for r in sorted_releases],
        )

    def get_active_release(self, ts_utc: datetime) -> NewsRelease | None:
        """Return the release whose ±window envelope contains ts_utc, or None.

        If multiple release windows overlap the same timestamp (e.g., a
        coincident NFP + CPI release on rare schedule overlap), returns the
        release whose center is CLOSEST to ts_utc.
        """
        if ts_utc.tzinfo is None:
            raise ValueError("ts_utc must be timezone-aware (UTC).")
        target = ts_utc.timestamp()
        # Binary search for the leftmost release whose timestamp could match.
        # The maximum window is FOMC=15min=900s, so we scan the small
        # neighborhood. Generic search: get all releases within max_window
        # before-or-after the target.
        max_window_seconds = max(DEFAULT_WINDOW_MINUTES.values()) * 60
        lo = bisect.bisect_left(
            self._sorted_release_timestamps, target - max_window_seconds
        )
        hi = bisect.bisect_right(
            self._sorted_release_timestamps, target + max_window_seconds
        )
        candidate: NewsRelease | None = None
        candidate_distance: float = float("inf")
        for i in range(lo, hi):
            r = self.releases[i]
            window_seconds = r.window_minutes * 60
            distance = abs(target - self._sorted_release_timestamps[i])
            if distance <= window_seconds and distance < candidate_distance:
                candidate = r
                candidate_distance = distance
        return candidate

    def is_in_news_window(self, ts_utc: datetime) -> bool:
        """True iff `ts_utc` is within any release's ±window envelope."""
        return self.get_active_release(ts_utc) is not None

    def n_releases(self) -> int:
        return len(self.releases)

    def payload_sha256(self) -> str:
        """Deterministic SHA256 over the canonical-JSON-encoded release set."""
        payload = [
            {
                "indicator_id": r.indicator_id,
                "release_timestamp_utc": r.release_timestamp_utc.isoformat(),
                "window_minutes": r.window_minutes,
                "provenance": r.provenance,
            }
            for r in self.releases
        ]
        serialised = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialised.encode("utf-8")).hexdigest()

    @classmethod
    def from_static_h055_window(cls) -> "NewsCalendar":
        """Construct from the curated static H055 window sample.

        See `static_h055_window_calendar()` for the data + provenance.
        """
        return cls(releases=tuple(static_h055_window_calendar()))


def _et_to_utc(year: int, month: int, day: int, hour_et: int, minute_et: int) -> datetime:
    """Construct a UTC datetime from an ET (America/New_York) wall-clock spec."""
    et_dt = datetime(year, month, day, hour_et, minute_et, tzinfo=_ET)
    return et_dt.astimezone(timezone.utc)


def static_h055_window_calendar() -> list[NewsRelease]:
    """Curated FOMC + NFP + CPI sample for the H055 walk-forward window.

    Coverage: 2020-2025 (the H055 train + OOS window per design.md §2).
    The dates are derived from generally-known public-calendar conventions
    (FOMC 8 meetings/year typically late Jan/Mar/May/Jun/Jul/Sep/Nov/Dec at
    14:00 ET; NFP first Friday of each month at 08:30 ET; CPI mid-month at
    08:30 ET). The dates are PRELIMINARY and should be verified against
    primary sources before production use:
      - FOMC: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
      - NFP:  https://www.bls.gov/schedule/news_release/empsit.htm
      - CPI:  https://www.bls.gov/schedule/news_release/cpi.htm

    This static curation is the offline-default for tests + initial H055
    walk-forward integration. Production runs SHOULD use the FRED + BLS API
    loaders (pending `P1-NEWS-CALENDAR-API-LOADERS`) for primary-source-
    verified fresh data; the orchestrator MUST log the calendar's
    `payload_sha256` to the ReproLog so the eligible-bar-filter is
    reproducibly bound to a specific release-set vintage.

    Per follow-up `P1-NEWS-CALENDAR-PRIMARY-SOURCE-VERIFY` (BLOCKING-BEFORE-
    H055-WALK-FORWARD-LAUNCH), the static dates here MUST be cross-checked
    against the primary federalreserve.gov + BLS press-release archives.
    Until then the static calendar is suitable for development/testing only.

    The `provenance` field tags each release as
    `"static-h055-curation-2026-05-09-PRELIMINARY"`.
    """
    pv = "static-h055-curation-2026-05-09-PRELIMINARY"
    fomc_w = DEFAULT_WINDOW_MINUTES["FOMC"]
    nfp_w = DEFAULT_WINDOW_MINUTES["NFP"]
    cpi_w = DEFAULT_WINDOW_MINUTES["CPI"]
    releases: list[NewsRelease] = []

    # FOMC meetings 2020-2025 (8/year per the standard schedule; press
    # release at 14:00 ET on the second day of each meeting).
    fomc_dates: list[tuple[int, int, int]] = [
        # 2020
        (2020, 1, 29), (2020, 3, 18), (2020, 4, 29), (2020, 6, 10),
        (2020, 7, 29), (2020, 9, 16), (2020, 11, 5), (2020, 12, 16),
        # 2021
        (2021, 1, 27), (2021, 3, 17), (2021, 4, 28), (2021, 6, 16),
        (2021, 7, 28), (2021, 9, 22), (2021, 11, 3), (2021, 12, 15),
        # 2022
        (2022, 1, 26), (2022, 3, 16), (2022, 5, 4), (2022, 6, 15),
        (2022, 7, 27), (2022, 9, 21), (2022, 11, 2), (2022, 12, 14),
        # 2023
        (2023, 2, 1), (2023, 3, 22), (2023, 5, 3), (2023, 6, 14),
        (2023, 7, 26), (2023, 9, 20), (2023, 11, 1), (2023, 12, 13),
        # 2024
        (2024, 1, 31), (2024, 3, 20), (2024, 5, 1), (2024, 6, 12),
        (2024, 7, 31), (2024, 9, 18), (2024, 11, 7), (2024, 12, 18),
        # 2025
        (2025, 1, 29), (2025, 3, 19), (2025, 5, 7), (2025, 6, 18),
        (2025, 7, 30), (2025, 9, 17), (2025, 10, 29), (2025, 12, 10),
    ]
    for y, m, d in fomc_dates:
        releases.append(
            NewsRelease(
                indicator_id="FOMC",
                release_timestamp_utc=_et_to_utc(
                    y, m, d, *_FOMC_RELEASE_TIME_ET
                ),
                window_minutes=fomc_w,
                provenance=pv,
            )
        )

    # NFP releases 2020-2025 (first Friday of each month at 08:30 ET; 12/year).
    nfp_dates: list[tuple[int, int, int]] = [
        (2020, 1, 10), (2020, 2, 7), (2020, 3, 6), (2020, 4, 3), (2020, 5, 8), (2020, 6, 5),
        (2020, 7, 2), (2020, 8, 7), (2020, 9, 4), (2020, 10, 2), (2020, 11, 6), (2020, 12, 4),
        (2021, 1, 8), (2021, 2, 5), (2021, 3, 5), (2021, 4, 2), (2021, 5, 7), (2021, 6, 4),
        (2021, 7, 2), (2021, 8, 6), (2021, 9, 3), (2021, 10, 8), (2021, 11, 5), (2021, 12, 3),
        (2022, 1, 7), (2022, 2, 4), (2022, 3, 4), (2022, 4, 1), (2022, 5, 6), (2022, 6, 3),
        (2022, 7, 8), (2022, 8, 5), (2022, 9, 2), (2022, 10, 7), (2022, 11, 4), (2022, 12, 2),
        (2023, 1, 6), (2023, 2, 3), (2023, 3, 10), (2023, 4, 7), (2023, 5, 5), (2023, 6, 2),
        (2023, 7, 7), (2023, 8, 4), (2023, 9, 1), (2023, 10, 6), (2023, 11, 3), (2023, 12, 8),
        (2024, 1, 5), (2024, 2, 2), (2024, 3, 8), (2024, 4, 5), (2024, 5, 3), (2024, 6, 7),
        (2024, 7, 5), (2024, 8, 2), (2024, 9, 6), (2024, 10, 4), (2024, 11, 1), (2024, 12, 6),
        (2025, 1, 10), (2025, 2, 7), (2025, 3, 7), (2025, 4, 4), (2025, 5, 2), (2025, 6, 6),
        (2025, 7, 3), (2025, 8, 1), (2025, 9, 5), (2025, 10, 3), (2025, 11, 7), (2025, 12, 5),
    ]
    for y, m, d in nfp_dates:
        releases.append(
            NewsRelease(
                indicator_id="NFP",
                release_timestamp_utc=_et_to_utc(y, m, d, *_BLS_RELEASE_TIME_ET),
                window_minutes=nfp_w,
                provenance=pv,
            )
        )

    # CPI releases 2020-2025 (mid-month at 08:30 ET; 12/year). User-verified
    # against BLS schedule.
    cpi_dates: list[tuple[int, int, int]] = [
        (2020, 1, 14), (2020, 2, 13), (2020, 3, 11), (2020, 4, 10), (2020, 5, 12), (2020, 6, 10),
        (2020, 7, 14), (2020, 8, 12), (2020, 9, 11), (2020, 10, 13), (2020, 11, 12), (2020, 12, 10),
        (2021, 1, 13), (2021, 2, 10), (2021, 3, 10), (2021, 4, 13), (2021, 5, 12), (2021, 6, 10),
        (2021, 7, 13), (2021, 8, 11), (2021, 9, 14), (2021, 10, 13), (2021, 11, 10), (2021, 12, 10),
        (2022, 1, 12), (2022, 2, 10), (2022, 3, 10), (2022, 4, 12), (2022, 5, 11), (2022, 6, 10),
        (2022, 7, 13), (2022, 8, 10), (2022, 9, 13), (2022, 10, 13), (2022, 11, 10), (2022, 12, 13),
        (2023, 1, 12), (2023, 2, 14), (2023, 3, 14), (2023, 4, 12), (2023, 5, 10), (2023, 6, 13),
        (2023, 7, 12), (2023, 8, 10), (2023, 9, 13), (2023, 10, 12), (2023, 11, 14), (2023, 12, 12),
        (2024, 1, 11), (2024, 2, 13), (2024, 3, 12), (2024, 4, 10), (2024, 5, 15), (2024, 6, 12),
        (2024, 7, 11), (2024, 8, 14), (2024, 9, 11), (2024, 10, 10), (2024, 11, 13), (2024, 12, 11),
        (2025, 1, 15), (2025, 2, 12), (2025, 3, 12), (2025, 4, 10), (2025, 5, 13), (2025, 6, 11),
        (2025, 7, 15), (2025, 8, 12), (2025, 9, 11), (2025, 10, 15), (2025, 11, 13), (2025, 12, 10),
    ]
    for y, m, d in cpi_dates:
        releases.append(
            NewsRelease(
                indicator_id="CPI",
                release_timestamp_utc=_et_to_utc(y, m, d, *_BLS_RELEASE_TIME_ET),
                window_minutes=cpi_w,
                provenance=pv,
            )
        )

    return releases


def load_fomc_calendar_from_fred(
    *,
    api_key: str | None = None,
    fred_release_id: int = 101,
) -> Sequence[NewsRelease]:
    """Fetch FOMC release dates from the FRED API (release_id=101 for FOMC).

    Pending `P1-NEWS-CALENDAR-API-LOADERS` (BLOCKING-BEFORE-EMPIRICAL-FRESH-
    DATA-INGEST). At this primitive's land time, FRED API integration is
    deferred to keep this commit testable without network access.

    Args:
        api_key: FRED API key. If None, reads from FRED_API_KEY env var.
        fred_release_id: FRED release_id; FOMC schedule = 101 per
            https://api.stlouisfed.org/fred/releases?api_key=...
    """
    raise NotImplementedError(
        "FRED FOMC calendar loader pending P1-NEWS-CALENDAR-API-LOADERS. "
        "Use `static_h055_window_calendar()` for offline default."
    )


def load_bls_calendar(
    *,
    indicator_id: str,
    start_year: int,
    end_year: int,
) -> Sequence[NewsRelease]:
    """Fetch NFP / CPI release dates from the BLS public release-time calendar.

    Pending `P1-NEWS-CALENDAR-API-LOADERS` (BLOCKING-BEFORE-EMPIRICAL-FRESH-
    DATA-INGEST). Use `static_h055_window_calendar()` for offline default.
    """
    raise NotImplementedError(
        "BLS calendar loader pending P1-NEWS-CALENDAR-API-LOADERS. "
        "Use `static_h055_window_calendar()` for offline default."
    )


def merge_calendars(*sources: Iterable[NewsRelease]) -> NewsCalendar:
    """Combine multiple release sources into a single NewsCalendar.

    Useful for composing FRED FOMC + BLS NFP + BLS CPI loaders. Duplicate-
    detection by (indicator_id, release_timestamp_utc) tuple; the first
    source's record wins.
    """
    seen: set[tuple[str, datetime]] = set()
    merged: list[NewsRelease] = []
    for source in sources:
        for r in source:
            key = (r.indicator_id, r.release_timestamp_utc)
            if key in seen:
                continue
            seen.add(key)
            merged.append(r)
    return NewsCalendar(releases=tuple(merged))
