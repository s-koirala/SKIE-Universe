"""FOMC text ingest pipeline.

Downloads, parses, validates, and writes FOMC statements, minutes, and
press-conference transcripts as normalized text in partitioned Parquet.

Conforms to the ``IngestJob`` protocol defined in ``_registry.py``
(plan section 2.1).

Data source: federalreserve.gov (public domain, 17 USC sec. 105).

URL patterns:
  - Statements:        /newsevents/pressreleases/monetary{YYYYMMDD}a.htm
  - Minutes:           /monetarypolicy/fomcminutes{YYYYMMDD}.htm
  - Press conferences: /monetarypolicy/fomcpresconf{YYYYMMDD}.htm

Release times (institutional schedule):
  - Statements:        14:00 ET on meeting day
  - Minutes:           14:00 ET (~3 weeks after meeting)
  - Press conferences: 14:30 ET on meeting day

Cross-validation reference:
  vtasca/fomc-statements-minutes (HuggingFace)
"""

from __future__ import annotations

import contextlib
import json
import logging
import re
import time
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
import polars as pl
from bs4 import BeautifulSoup

from skie_ninja.data.ingest._fomc_calendar import (
    FomcMeeting,
    scrape_fomc_calendar,
)
from skie_ninja.data.ingest._registry import register
from skie_ninja.utils.hashing import file_sha256
from skie_ninja.utils.runcontext import RunContext

_log = logging.getLogger(__name__)

# timezone.utc alias — UP017 wants datetime.UTC but that requires
# Python 3.12+; project targets 3.11+.
_UTC = timezone.utc  # noqa: UP017 — datetime.UTC requires Python 3.12; project targets 3.11

DocType = Literal["statement", "minutes", "press_conference"]

_FED_BASE = "https://www.federalreserve.gov"

# Rate-limit: 1 request/second — institutional courtesy.
# The Fed's robots.txt does not explicitly restrict these paths,
# but responsible scraping practice dictates conservative pacing.
_MIN_REQUEST_INTERVAL_S = 1.0
_MAX_RETRIES = 4
_BACKOFF_BASE_S = 2.0

# ET offsets (Eastern Time). During EDT (UTC-4) these shift by 1h;
# we use the standard release-time convention in US/Eastern and
# convert to UTC via zoneinfo for correctness across DST.
_STATEMENT_RELEASE_HOUR_ET = 14
_STATEMENT_RELEASE_MIN_ET = 0
_MINUTES_RELEASE_HOUR_ET = 14
_MINUTES_RELEASE_MIN_ET = 0
_PRESSER_RELEASE_HOUR_ET = 14
_PRESSER_RELEASE_MIN_ET = 30

# Content selectors for extracting main text from Fed HTML.
# Modern pages (roughly post-2015): main content in this column div.
_MODERN_CONTENT_SELECTOR = "div.col-xs-12.col-sm-8.col-md-8"
# Older pages use various containers; fallback to <div id="content">.
_LEGACY_CONTENT_IDS = ("content", "leftText", "article")

# Schema fields expected in the output LazyFrame.
_HTTP_NOT_FOUND = 404

_REQUIRED_FIELDS = frozenset(
    {
        "release_ts_utc",
        "embargo_ts_utc",
        "doc_type",
        "sha256",
        "raw_path",
        "text_normalized",
    }
)


def _release_ts_utc(meeting_date: date, doc_type: DocType) -> datetime:
    """Compute the UTC release timestamp for a document type.

    Uses ``zoneinfo`` for DST-correct ET-to-UTC conversion.
    """
    from zoneinfo import ZoneInfo

    et = ZoneInfo("America/New_York")
    if doc_type == "press_conference":
        hour, minute = _PRESSER_RELEASE_HOUR_ET, _PRESSER_RELEASE_MIN_ET
    elif doc_type == "minutes":
        hour, minute = _MINUTES_RELEASE_HOUR_ET, _MINUTES_RELEASE_MIN_ET
    else:
        hour, minute = _STATEMENT_RELEASE_HOUR_ET, _STATEMENT_RELEASE_MIN_ET

    local = datetime(
        meeting_date.year,
        meeting_date.month,
        meeting_date.day,
        hour,
        minute,
        tzinfo=et,
    )
    return local.astimezone(_UTC)


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
    raise RuntimeError("Exhausted retries")  # pragma: no cover


def _extract_text(html: str) -> str:
    """Extract the main content text from Fed HTML.

    Strategy:
      1. Try the modern column selector (post-2015 redesign).
      2. Fall back to legacy container IDs (pre-2015).
      3. If neither found, fall back to <body>.
    Then: strip nav/header/footer elements, extract text, normalize.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove navigation, header, footer, script, style elements.
    for tag_name in ("nav", "header", "footer", "script", "style", "noscript"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Try modern selector.
    content = soup.select_one(_MODERN_CONTENT_SELECTOR)

    # Fall back to legacy IDs.
    if content is None:
        for cid in _LEGACY_CONTENT_IDS:
            content = soup.find("div", id=cid)
            if content is not None:
                break

    # Last resort: body.
    if content is None:
        content = soup.find("body")

    if content is None:
        return ""

    raw_text = content.get_text(separator=" ", strip=True)

    # Unicode NFC normalization.
    text = unicodedata.normalize("NFC", raw_text)

    # Collapse runs of whitespace to single spaces; strip leading/trailing.
    text = re.sub(r"\s+", " ", text).strip()

    return text


class FomcTextIngestJob:
    """FOMC text ingest job conforming to ``IngestJob`` protocol."""

    name: str = "fomc_text"
    version: str = "0.1.0"

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        """Scrape the FOMC calendar, then download raw HTML for each meeting.

        Raw HTML is saved to ``~/datasets/fomc_text/{doc_type}/{YYYYMMDD}.html``
        (the shared data directory). Downloads are idempotent: existing
        files with a matching SHA256 are skipped.

        Returns a list of all raw HTML paths (existing + newly downloaded).
        """
        paths = ctx.paths
        fomc_dir = paths.shared_fomc_text

        # Build the meeting-date index from the Fed calendar.
        calendar_cache = paths.data_raw / "fomc_calendar.json"
        paths.ensure(calendar_cache.parent)

        meetings = scrape_fomc_calendar(
            start_year=start.year,
            end_year=end.year,
            cache_path=calendar_cache,
        )

        # Filter to requested date range.
        meetings = [m for m in meetings if start <= m.meeting_date <= end]
        _log.info(
            "FOMC calendar: %d meetings in [%s, %s]",
            len(meetings),
            start.isoformat(),
            end.isoformat(),
        )

        raw_paths: list[Path] = []
        client = httpx.Client(
            headers={
                "User-Agent": (
                    "SKIE-Universe/0.1 (research; "
                    "https://github.com/s-koirala; rate-limited 1req/s)"
                ),
            },
        )
        last_req: list[float] = [0.0]

        try:
            for meeting in meetings:
                raw_paths.extend(self._fetch_meeting_docs(meeting, fomc_dir, client, last_req))
        finally:
            client.close()

        _log.info("Fetched %d raw FOMC documents", len(raw_paths))
        return raw_paths

    def _fetch_meeting_docs(
        self,
        meeting: FomcMeeting,
        fomc_dir: Path,
        client: httpx.Client,
        last_req: list[float],
    ) -> list[Path]:
        """Download statement, minutes, and press-conference for one meeting."""
        date_str = meeting.meeting_date.strftime("%Y%m%d")
        paths: list[Path] = []

        doc_urls: list[tuple[DocType, str | None]] = [
            ("statement", meeting.statement_url),
            ("minutes", meeting.minutes_url),
            ("press_conference", meeting.presser_url),
        ]

        for doc_type, url in doc_urls:
            if url is None:
                continue
            out_dir = fomc_dir / doc_type
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{date_str}.html"

            # Idempotent: skip if file already exists.
            if out_path.is_file():
                _log.debug("Skipping existing file: %s", out_path)
                paths.append(out_path)
                continue

            try:
                resp = _rate_limited_get(client, url, last_req)
                out_path.write_text(resp.text, encoding="utf-8")
                _log.info("Downloaded: %s -> %s", url, out_path)
                paths.append(out_path)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == _HTTP_NOT_FOUND:
                    _log.info(
                        "Not found (expected for some doc types): %s",
                        url,
                    )
                else:
                    _log.error("Failed to download %s: %s", url, exc)

        return paths

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        """Parse raw HTML files into a normalized text LazyFrame.

        Output schema (matches ``FomcTextSchema`` in validation/schema.py):
          - release_ts_utc: datetime (UTC, naive for Parquet compat)
          - embargo_ts_utc: datetime (same as release_ts_utc; FOMC
            texts have no pre-release embargo distinct from release)
          - doc_type: str (statement | minutes | press_conference)
          - sha256: str (hex digest of the raw HTML file)
          - raw_path: str (POSIX-style path to raw file)
          - text_normalized: str (NFC-normalized, whitespace-collapsed)
        """
        records: list[dict] = []

        for path in raw_paths:
            # Derive doc_type and meeting_date from path structure:
            #   fomc_text/{doc_type}/{YYYYMMDD}.html
            doc_type = path.parent.name
            stem = path.stem  # YYYYMMDD
            try:
                meeting_date = datetime.strptime(stem, "%Y%m%d").date()
            except ValueError:
                _log.warning("Skipping file with unparseable name: %s", path)
                continue

            if doc_type not in ("statement", "minutes", "press_conference"):
                _log.warning("Skipping file with unknown doc_type dir: %s", path)
                continue

            html = path.read_text(encoding="utf-8")
            text = _extract_text(html)

            if not text:
                _log.warning("Empty text after parsing: %s", path)
                continue

            release_ts = _release_ts_utc(meeting_date, doc_type)
            records.append(
                {
                    "release_ts_utc": release_ts,
                    "embargo_ts_utc": release_ts,
                    "doc_type": doc_type,
                    "sha256": file_sha256(path),
                    "raw_path": path.as_posix(),
                    "text_normalized": text,
                }
            )

        if not records:
            _log.warning("No records parsed from %d raw paths", len(raw_paths))
            return pl.LazyFrame(
                schema={
                    "release_ts_utc": pl.Datetime("us"),
                    "embargo_ts_utc": pl.Datetime("us"),
                    "doc_type": pl.Utf8,
                    "sha256": pl.Utf8,
                    "raw_path": pl.Utf8,
                    "text_normalized": pl.Utf8,
                }
            )

        df = pl.DataFrame(records)
        return df.lazy()

    def validate(self, df: pl.LazyFrame) -> None:
        """Validate the parsed LazyFrame against the FOMC text schema.

        Attempts to import ``FomcTextSchema`` from the sibling
        validation module. If that module is not yet created by the
        sibling agent, falls back to basic field-presence checks.
        """
        try:
            from skie_ninja.data.validation.schema import FomcTextSchema

            FomcTextSchema.validate(df)
            _log.info("Schema validation passed (FomcTextSchema)")
            return
        except ImportError:
            _log.info("FomcTextSchema not available; falling back to basic field checks")
        except Exception as exc:
            raise ValueError(f"Schema validation failed: {exc}") from exc

        # Fallback: basic field-presence check.
        collected = df.collect()
        present = set(collected.columns)
        missing = _REQUIRED_FIELDS - present
        if missing:
            raise ValueError(f"Missing required fields: {sorted(missing)}")

        # Basic non-empty check.
        if collected.height == 0:
            raise ValueError("Validated DataFrame is empty")

        # Check for null text.
        null_count = collected.select(pl.col("text_normalized").is_null().sum()).item()
        if null_count > 0:
            raise ValueError(f"Found {null_count} null text_normalized values")

        _log.info("Basic field-presence validation passed (%d rows)", collected.height)

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        """Write validated data to Hive-partitioned Parquet.

        Layout: ``data/processed/fomc_text/release_date=YYYY-MM-DD/
                 doc_type={statement|minutes|press_conference}.parquet``

        Two-phase commit: writes to ``_staging/``, renames on
        validation pass.
        """
        paths = ctx.paths
        base_dir = paths.data_processed / "fomc_text"
        staging_dir = paths.data_processed / "_staging" / "fomc_text"
        paths.ensure(staging_dir)

        collected = df.collect()

        # Write per-partition files.
        written_staging: list[tuple[Path, Path]] = []

        for row in collected.iter_rows(named=True):
            release_date = row["release_ts_utc"].date()
            doc_type = row["doc_type"]

            part_dir_final = base_dir / f"release_date={release_date}" / f"doc_type={doc_type}"
            part_dir_staging = staging_dir / f"release_date={release_date}" / f"doc_type={doc_type}"
            part_dir_staging.mkdir(parents=True, exist_ok=True)

            staging_path = part_dir_staging / "part-0000.parquet"
            final_path = part_dir_final / "part-0000.parquet"

            # Write single-row frame to staging.
            row_df = pl.DataFrame([row])
            row_df.write_parquet(staging_path)
            written_staging.append((staging_path, final_path))

        # Re-validate staged parquet files before promoting.
        from skie_ninja.data.validation.schema import FomcTextSchema

        for staging_path, _final_path in written_staging:
            try:
                check_df = pl.read_parquet(staging_path)
                FomcTextSchema.validate(check_df)
            except Exception:
                # Validation failed: clean up all staging files and raise.
                for sp, _fp in written_staging:
                    sp.unlink(missing_ok=True)
                _rmtree_empty(staging_dir)
                raise

        # Promote all staged files atomically (per-file rename).
        for staging_path, final_path in written_staging:
            final_path.parent.mkdir(parents=True, exist_ok=True)
            staging_path.replace(final_path)

        # Clean up staging dir.
        _rmtree_empty(staging_dir)

        _log.info(
            "Wrote %d partitions to %s",
            len(written_staging),
            base_dir,
        )
        return base_dir

    def emit_provenance(
        self,
        ctx: RunContext,
        source_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Write provenance JSON per plan section 2.1."""
        paths = ctx.paths
        prov_dir = paths.data_processed / "_provenance"
        paths.ensure(prov_dir)

        timestamp = datetime.now(tz=_UTC).isoformat()
        prov = {
            "dataset": self.name,
            "version": self.version,
            "vendor": "federalreserve.gov",
            "timestamp_utc": timestamp,
            "source_urls": [
                _FED_BASE + "/monetarypolicy/fomccalendars.htm",
                _FED_BASE + "/monetarypolicy/fomchistorical*.htm",
            ],
            "source_files": [
                {
                    "path": p.as_posix(),
                    "sha256": file_sha256(p),
                }
                for p in source_paths
            ],
            "output_path": output_path.as_posix(),
            "run_id": ctx.log.run_id if ctx.log else None,
            "repro_log": ctx.log.to_dict() if ctx.log else None,
        }

        date_str = datetime.now(tz=_UTC).strftime("%Y%m%d")
        prov_path = prov_dir / f"fomc_text_{date_str}.json"
        with prov_path.open("w", encoding="utf-8") as f:
            json.dump(prov, f, indent=2, sort_keys=True)

        _log.info("Wrote provenance: %s", prov_path)
        return prov_path


def _rmtree_empty(path: Path) -> None:
    """Remove a directory tree if all leaves are empty dirs."""
    if not path.is_dir():
        return
    for child in path.iterdir():
        if child.is_dir():
            _rmtree_empty(child)
    # Only remove if now empty.
    with contextlib.suppress(OSError):
        path.rmdir()


# Self-register at import time.
register(FomcTextIngestJob())
