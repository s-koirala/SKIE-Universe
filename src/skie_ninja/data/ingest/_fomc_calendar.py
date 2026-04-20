"""FOMC calendar scraper and meeting-date index builder.

Scrapes the Federal Reserve website for FOMC meeting dates and builds
a structured index mapping each meeting to its statement, minutes, and
press-conference URLs.

URL patterns (federalreserve.gov, public domain per 17 USC sec. 105):
  - Calendar (recent):  /monetarypolicy/fomccalendars.htm
  - Calendar (archive): /monetarypolicy/fomchistorical{YYYY}.htm
  - Statements:         /newsevents/pressreleases/monetary{YYYYMMDD}a.htm
  - Minutes:            /monetarypolicy/fomcminutes{YYYYMMDD}.htm
  - Press conferences:  /monetarypolicy/fomcpresconf{YYYYMMDD}.htm

Rate limit: 1 request/second with exponential backoff — institutional
courtesy; the Fed's robots.txt does not explicitly restrict these paths
but we rate-limit as a matter of good practice.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

_log = logging.getLogger(__name__)

_FED_BASE = "https://www.federalreserve.gov"

# Rate-limit: 1 request/second (courtesy; see module docstring).
_MIN_REQUEST_INTERVAL_S = 1.0

# Exponential backoff parameters for transient failures.
_MAX_RETRIES = 4
_BACKOFF_BASE_S = 2.0


@dataclass(frozen=True)
class FomcMeeting:
    """One FOMC meeting with known document URLs."""

    meeting_date: date
    statement_url: str | None = None
    minutes_url: str | None = None
    presser_url: str | None = None


def _rate_limited_get(
    client: httpx.Client,
    url: str,
    last_request_time: list[float],
) -> httpx.Response:
    """GET with rate-limiting and exponential backoff."""
    for attempt in range(_MAX_RETRIES + 1):
        elapsed = time.monotonic() - last_request_time[0]
        if elapsed < _MIN_REQUEST_INTERVAL_S:
            time.sleep(_MIN_REQUEST_INTERVAL_S - elapsed)
        try:
            resp = client.get(url, follow_redirects=True, timeout=30.0)
            last_request_time[0] = time.monotonic()
            resp.raise_for_status()
            return resp
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            if attempt == _MAX_RETRIES:
                raise
            wait = _BACKOFF_BASE_S ** (attempt + 1)
            _log.warning(
                "Request to %s failed (attempt %d/%d): %s — retrying in %.1fs",
                url,
                attempt + 1,
                _MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)
    # Unreachable, but satisfies type checker.
    raise RuntimeError("Exhausted retries")  # pragma: no cover


_HTTP_NOT_FOUND = 404

# URL-pattern regexes for document-type classification.
_URL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("statement", re.compile(r"/monetary(\d{8})a\.htm")),
    ("minutes", re.compile(r"/fomcminutes(\d{8})\.htm")),
    ("presser", re.compile(r"/fomcpresconf(\d{8})\.htm")),
]

# Month-name pattern for bare-date extraction (Strategy 2).
_DATE_RANGE_PATTERN = re.compile(
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2}(?:-\d{1,2})?,?\s+\d{4}"
)

_EXPECTED_DATE_PARTS = 2


def _extract_links(soup: BeautifulSoup, year: int) -> list[FomcMeeting]:
    """Strategy 1: extract meetings from hyperlink URL patterns."""
    doc_maps: dict[str, dict[str, str]] = {
        "statement": {},
        "minutes": {},
        "presser": {},
    }

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("/"):
            href = _FED_BASE + href
        for doc_key, pattern in _URL_PATTERNS:
            m = pattern.search(href)
            if m:
                doc_maps[doc_key][m.group(1)] = href
                break

    all_date_keys = sorted(
        set(doc_maps["statement"]) | set(doc_maps["minutes"]) | set(doc_maps["presser"])
    )

    meetings: list[FomcMeeting] = []
    for dk in all_date_keys:
        try:
            mt_date = datetime.strptime(dk, "%Y%m%d").date()
        except ValueError:
            continue
        if mt_date.year != year:
            continue
        meetings.append(
            FomcMeeting(
                meeting_date=mt_date,
                statement_url=doc_maps["statement"].get(dk),
                minutes_url=doc_maps["minutes"].get(dk),
                presser_url=doc_maps["presser"].get(dk),
            )
        )
    return meetings


def _extract_bare_dates(soup: BeautifulSoup, year: int) -> list[FomcMeeting]:
    """Strategy 2: construct URLs from bare meeting dates in page text."""
    text = soup.get_text()
    meetings: list[FomcMeeting] = []

    for match in _DATE_RANGE_PATTERN.finditer(text):
        raw = match.group()
        range_m = re.search(r"(\w+)\s+\d{1,2}-(\d{1,2}),?\s+(\d{4})", raw)
        if range_m:
            raw_clean = f"{range_m.group(1)} {range_m.group(2)}, {range_m.group(3)}"
        else:
            raw_clean = raw.replace(",", "").strip()
            parts = raw_clean.rsplit(" ", 1)
            if len(parts) == _EXPECTED_DATE_PARTS:
                raw_clean = f"{parts[0]}, {parts[1]}"

        try:
            mt_date = datetime.strptime(raw_clean.strip(), "%B %d, %Y").date()
        except ValueError:
            continue
        if mt_date.year != year:
            continue
        dk = mt_date.strftime("%Y%m%d")
        meetings.append(
            FomcMeeting(
                meeting_date=mt_date,
                statement_url=f"{_FED_BASE}/newsevents/pressreleases/monetary{dk}a.htm",
                minutes_url=f"{_FED_BASE}/monetarypolicy/fomcminutes{dk}.htm",
                presser_url=f"{_FED_BASE}/monetarypolicy/fomcpresconf{dk}.htm",
            )
        )
    return meetings


def _parse_calendar_page(html: str, year: int) -> list[FomcMeeting]:
    """Extract meeting dates and document URLs from a calendar page.

    Handles both modern (post-2015) and historical (pre-2015) Fed
    calendar HTML layouts. Strategy 1 extracts meetings from link URL
    patterns; Strategy 2 falls back to constructing URLs from bare
    date text in the page body.
    """
    soup = BeautifulSoup(html, "lxml")

    meetings = _extract_links(soup, year)
    if not meetings:
        meetings = _extract_bare_dates(soup, year)

    # Deduplicate by date, preserving first occurrence.
    seen: set[date] = set()
    deduped: list[FomcMeeting] = []
    for m in meetings:
        if m.meeting_date not in seen:
            seen.add(m.meeting_date)
            deduped.append(m)

    return sorted(deduped, key=lambda m: m.meeting_date)


def scrape_fomc_calendar(
    start_year: int,
    end_year: int,
    client: httpx.Client | None = None,
    cache_path: Path | None = None,
) -> list[FomcMeeting]:
    """Scrape the Fed FOMC calendar pages and return structured meetings.

    Parameters
    ----------
    start_year, end_year
        Inclusive year range to scrape.
    client
        Optional pre-configured httpx.Client. One is created if not
        provided.
    cache_path
        Path to a JSON cache file. If provided and the file exists, it
        is loaded instead of scraping. If provided and the file does
        not exist, the scraped results are written there.

    Returns
    -------
    list[FomcMeeting]
        Sorted by meeting_date ascending.
    """
    if cache_path and cache_path.is_file():
        _log.info("Loading FOMC calendar from cache: %s", cache_path)
        return _load_cache(cache_path)

    own_client = client is None
    if own_client:
        client = httpx.Client(
            headers={
                "User-Agent": (
                    "SKIE-Universe/0.1 (research; "
                    "https://github.com/s-koirala; rate-limited 1req/s)"
                ),
            },
        )
    assert client is not None  # noqa: S101 — type narrowing

    last_req: list[float] = [0.0]
    all_meetings: list[FomcMeeting] = []

    try:
        for year in range(start_year, end_year + 1):
            # Recent years: fomccalendars.htm covers a rolling window.
            # Historical: fomchistorical{YYYY}.htm
            # Try historical first (always one year); supplement with
            # current calendar for the most recent year.
            url = f"{_FED_BASE}/monetarypolicy/fomchistorical{year}.htm"
            _log.info("Fetching FOMC calendar for %d: %s", year, url)
            try:
                resp = _rate_limited_get(client, url, last_req)
                meetings = _parse_calendar_page(resp.text, year)
                all_meetings.extend(meetings)
                _log.info("Found %d meetings for %d via historical page", len(meetings), year)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == _HTTP_NOT_FOUND:
                    _log.info(
                        "Historical page not found for %d, trying current calendar",
                        year,
                    )
                else:
                    raise

            # For very recent years the historical page may not exist or
            # may be incomplete. Supplement from the current calendar.
            if year >= datetime.now().year - 1:
                cal_url = f"{_FED_BASE}/monetarypolicy/fomccalendars.htm"
                _log.info("Supplementing from current calendar: %s", cal_url)
                resp = _rate_limited_get(client, cal_url, last_req)
                cal_meetings = _parse_calendar_page(resp.text, year)
                existing_dates = {m.meeting_date for m in all_meetings}
                for m in cal_meetings:
                    if m.meeting_date not in existing_dates:
                        all_meetings.append(m)
                        existing_dates.add(m.meeting_date)
    finally:
        if own_client:
            client.close()

    all_meetings.sort(key=lambda m: m.meeting_date)

    if cache_path:
        _write_cache(cache_path, all_meetings)

    return all_meetings


def _load_cache(path: Path) -> list[FomcMeeting]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        FomcMeeting(
            meeting_date=date.fromisoformat(d["meeting_date"]),
            statement_url=d.get("statement_url"),
            minutes_url=d.get("minutes_url"),
            presser_url=d.get("presser_url"),
        )
        for d in data
    ]


def _write_cache(path: Path, meetings: list[FomcMeeting]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = []
    for m in meetings:
        d = asdict(m)
        d["meeting_date"] = m.meeting_date.isoformat()
        serializable.append(d)
    with path.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, sort_keys=True)
    _log.info("Wrote FOMC calendar cache: %s (%d meetings)", path, len(meetings))
