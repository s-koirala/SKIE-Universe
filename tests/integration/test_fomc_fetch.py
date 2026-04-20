"""Integration test: fetch one real FOMC statement from federalreserve.gov.

Marked ``@pytest.mark.integration`` — hits the network. Not run in
default ``pytest`` invocation; requires ``-m integration``.

Tests the full fetch-parse-validate cycle for the 2024-01-31 FOMC
meeting statement.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from skie_ninja.data.ingest.fomc_text import (
    FomcTextIngestJob,
    _extract_text,
    _rate_limited_get,
)
from skie_ninja.utils.hashing import file_sha256

# Target: 2024-01-31 FOMC meeting — known to have a statement.
_TARGET_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20240131a.htm"
_TARGET_DATE = date(2024, 1, 31)


@pytest.mark.integration
class TestFomcFetchReal:
    """End-to-end fetch-parse-validate against the live Fed website."""

    @pytest.fixture()
    def job(self) -> FomcTextIngestJob:
        return FomcTextIngestJob()

    @pytest.fixture()
    def downloaded_html(self, tmp_path: Path) -> Path:
        """Fetch a single real statement HTML."""
        import httpx

        client = httpx.Client(
            headers={
                "User-Agent": (
                    "SKIE-Ninja-Intraday/0.1 (integration-test; "
                    "https://github.com/s-koirala; rate-limited)"
                ),
            },
        )
        last_req: list[float] = [0.0]
        try:
            resp = _rate_limited_get(client, _TARGET_URL, last_req)
        finally:
            client.close()

        stmt_dir = tmp_path / "statement"
        stmt_dir.mkdir()
        out = stmt_dir / "20240131.html"
        out.write_text(resp.text, encoding="utf-8")
        return out

    def test_fetch_and_parse_real_statement(
        self,
        job: FomcTextIngestJob,
        downloaded_html: Path,
    ) -> None:
        """Verify that a real Fed statement parses correctly."""
        html = downloaded_html.read_text(encoding="utf-8")
        text = _extract_text(html)

        # The 2024-01-31 statement is known to contain these phrases.
        assert "federal funds rate" in text.lower()
        assert len(text) > 500  # noqa: PLR2004 — statement is non-trivial

    def test_parse_produces_valid_schema(
        self,
        job: FomcTextIngestJob,
        downloaded_html: Path,
    ) -> None:
        """Full parse produces all required fields."""

        class _FakeCtx:
            paths = None

        lf = job.parse([downloaded_html], _FakeCtx())  # type: ignore[arg-type]
        df = lf.collect()

        assert df.height == 1
        row = df.row(0, named=True)
        assert row["doc_type"] == "statement"
        assert row["release_ts_utc"].date() == _TARGET_DATE
        assert len(row["sha256"]) == 64  # noqa: PLR2004
        assert len(row["text_normalized"]) > 500  # noqa: PLR2004

    def test_validate_passes_on_real_data(
        self,
        job: FomcTextIngestJob,
        downloaded_html: Path,
    ) -> None:
        """Validate does not raise on correctly parsed real data."""

        class _FakeCtx:
            paths = None

        lf = job.parse([downloaded_html], _FakeCtx())  # type: ignore[arg-type]
        # Should not raise.
        job.validate(lf)

    def test_sha256_is_deterministic_for_downloaded_file(
        self,
        downloaded_html: Path,
    ) -> None:
        h1 = file_sha256(downloaded_html)
        h2 = file_sha256(downloaded_html)
        assert h1 == h2
