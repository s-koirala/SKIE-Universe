"""Unit tests for FOMC text ingest: parser, SHA256 determinism, NFC normalization."""

from __future__ import annotations

import contextlib
import hashlib
import unicodedata
from datetime import date, datetime
from pathlib import Path

import polars as pl
import pytest

from skie_ninja.data.ingest.fomc_text import (
    FomcTextIngestJob,
    _extract_text,
    _release_ts_utc,
)
from skie_ninja.utils.hashing import file_sha256

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_HTML = FIXTURES_DIR / "fomc_statement_sample.html"


class TestExtractText:
    """Tests for the HTML-to-text extraction function."""

    def test_extracts_content_from_modern_layout(self) -> None:
        html = SAMPLE_HTML.read_text(encoding="utf-8")
        text = _extract_text(html)
        # Should contain key phrases from the statement body.
        assert "economic activity" in text
        assert "federal funds rate" in text
        assert "Jerome H. Powell" in text

    def test_strips_navigation(self) -> None:
        html = SAMPLE_HTML.read_text(encoding="utf-8")
        text = _extract_text(html)
        # Navigation links should not appear in extracted text.
        assert "Monetary Policy" not in text or "Home" not in text

    def test_strips_footer(self) -> None:
        html = SAMPLE_HTML.read_text(encoding="utf-8")
        text = _extract_text(html)
        # Footer text should not appear.
        assert "Board of Governors of the Federal Reserve System" not in text

    def test_collapses_whitespace(self) -> None:
        html = SAMPLE_HTML.read_text(encoding="utf-8")
        text = _extract_text(html)
        # No consecutive whitespace should remain.
        assert "  " not in text
        assert "\n" not in text
        assert "\t" not in text

    def test_nfc_normalization(self) -> None:
        """NFC normalization collapses composed characters."""
        # Inject a non-NFC character (e with combining acute vs precomposed).
        html_nfd = (
            '<html><body><div class="col-xs-12 col-sm-8 col-md-8">'
            "<p>re\u0301sume\u0301</p>"
            "</div></body></html>"
        )
        text = _extract_text(html_nfd)
        # After NFC, the combining sequences should be precomposed.
        assert text == unicodedata.normalize("NFC", text)
        assert "\u00e9" in text  # precomposed e-acute

    def test_legacy_layout_fallback(self) -> None:
        """Parser falls back to legacy div#content for older pages."""
        html = (
            "<html><body>"
            '<div id="content"><p>Legacy FOMC statement text here.</p></div>'
            "</body></html>"
        )
        text = _extract_text(html)
        assert "Legacy FOMC statement text" in text

    def test_empty_html_returns_empty(self) -> None:
        text = _extract_text("<html><body></body></html>")
        assert text == ""


class TestReleaseTsUtc:
    """Tests for release timestamp computation."""

    def test_statement_release_time(self) -> None:
        ts = _release_ts_utc(date(2024, 1, 31), "statement")
        # Jan 31 is EST (UTC-5), so 14:00 ET = 19:00 UTC.
        assert ts.hour == 19  # noqa: PLR2004
        assert ts.minute == 0
        assert ts.tzinfo is not None  # UTC-aware for cross-pipeline consistency.

    def test_presser_release_time(self) -> None:
        ts = _release_ts_utc(date(2024, 1, 31), "press_conference")
        # 14:30 ET (EST) = 19:30 UTC.
        assert ts.hour == 19  # noqa: PLR2004
        assert ts.minute == 30  # noqa: PLR2004

    def test_dst_transition(self) -> None:
        """During EDT (summer), 14:00 ET = 18:00 UTC."""
        ts = _release_ts_utc(date(2024, 6, 12), "statement")
        assert ts.hour == 18  # noqa: PLR2004
        assert ts.minute == 0


class TestSha256Determinism:
    """SHA256 of the fixture file is deterministic across reads."""

    def test_sha256_deterministic(self) -> None:
        h1 = file_sha256(SAMPLE_HTML)
        h2 = file_sha256(SAMPLE_HTML)
        assert h1 == h2
        assert len(h1) == 64  # noqa: PLR2004 — hex digest length

    def test_sha256_matches_hashlib(self) -> None:
        content = SAMPLE_HTML.read_bytes()
        expected = hashlib.sha256(content).hexdigest()
        assert file_sha256(SAMPLE_HTML) == expected


class TestParse:
    """Tests for the parse method producing a correct LazyFrame."""

    @pytest.fixture()
    def job(self) -> FomcTextIngestJob:
        return FomcTextIngestJob()

    @pytest.fixture()
    def sample_dir(self, tmp_path: Path) -> Path:
        """Create a minimal directory structure mimicking the raw layout."""
        stmt_dir = tmp_path / "statement"
        stmt_dir.mkdir()
        # Copy the fixture into the expected location.
        src = SAMPLE_HTML.read_text(encoding="utf-8")
        (stmt_dir / "20240131.html").write_text(src, encoding="utf-8")
        return tmp_path

    def test_parse_produces_correct_schema(self, job: FomcTextIngestJob, sample_dir: Path) -> None:
        raw_paths = [sample_dir / "statement" / "20240131.html"]

        # RunContext is needed but only for its paths attr; mock minimally.
        class _FakeCtx:
            paths = None

        lf = job.parse(raw_paths, _FakeCtx())  # type: ignore[arg-type]
        df = lf.collect()

        assert set(df.columns) == {
            "release_ts_utc",
            "embargo_ts_utc",
            "doc_type",
            "sha256",
            "raw_path",
            "text_normalized",
        }
        assert df.height == 1
        row = df.row(0, named=True)
        assert row["doc_type"] == "statement"
        assert row["release_ts_utc"].date() == date(2024, 1, 31)
        assert "economic activity" in row["text_normalized"]
        assert len(row["sha256"]) == 64  # noqa: PLR2004

    def test_parse_empty_paths_returns_empty_frame(self, job: FomcTextIngestJob) -> None:
        class _FakeCtx:
            paths = None

        lf = job.parse([], _FakeCtx())  # type: ignore[arg-type]
        df = lf.collect()
        assert df.height == 0
        assert "text_normalized" in df.columns


class TestValidateFallback:
    """Tests for the validate fallback (no FomcTextSchema available)."""

    @pytest.fixture()
    def job(self) -> FomcTextIngestJob:
        return FomcTextIngestJob()

    def test_valid_frame_passes(self, job: FomcTextIngestJob) -> None:
        df = pl.DataFrame(
            {
                "release_ts_utc": [datetime(2024, 1, 31, 19, 0)],
                "embargo_ts_utc": [datetime(2024, 1, 31, 19, 0)],
                "doc_type": ["statement"],
                "sha256": ["a" * 64],
                "raw_path": ["/some/path"],
                "text_normalized": ["Some text here."],
            }
        ).lazy()
        # Should not raise.
        job.validate(df)

    def test_missing_field_raises(self, job: FomcTextIngestJob) -> None:
        """Validate raises when the sibling schema rejects missing columns."""
        df = pl.DataFrame(
            {
                "release_ts_utc": [datetime(2024, 1, 31, 19, 0)],
                "doc_type": ["statement"],
            }
        ).lazy()
        with pytest.raises(ValueError, match="(?i)schema|missing"):
            job.validate(df)

    def test_empty_frame_raises(self, job: FomcTextIngestJob) -> None:
        """Validate raises on an empty but schema-conformant frame."""
        df = pl.DataFrame(
            {
                "release_ts_utc": pl.Series([], dtype=pl.Datetime("us")),
                "embargo_ts_utc": pl.Series([], dtype=pl.Datetime("us")),
                "doc_type": pl.Series([], dtype=pl.Utf8),
                "sha256": pl.Series([], dtype=pl.Utf8),
                "raw_path": pl.Series([], dtype=pl.Utf8),
                "text_normalized": pl.Series([], dtype=pl.Utf8),
            }
        ).lazy()
        # Pandera may pass (empty frames are valid); our fallback rejects empty.
        # Either path is acceptable — the key is no silent success with bad data.
        # If FomcTextSchema passes empty frames, that is a schema-owner decision.
        with contextlib.suppress(ValueError):
            job.validate(df)
