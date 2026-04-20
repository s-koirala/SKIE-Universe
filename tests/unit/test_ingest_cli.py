"""Unit tests for scripts/ingest.py CLI."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import polars as pl
import pytest

# Ensure src/ is importable.
_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "scripts"))

from skie_ninja.data.ingest._registry import INGEST_REGISTRY  # noqa: E402

if TYPE_CHECKING:
    from skie_ninja.utils.runcontext import RunContext


# -- Fake ingest job conforming to IngestJob protocol. -----------------------


@dataclass
class _FakeJob:
    name: str = "fake_dataset"
    version: str = "0.0.1"

    def __init__(self) -> None:
        self.fetch_calls: list[tuple[date, date]] = []
        self.parse_called = False
        self.validate_called = False
        self.write_called = False
        self.provenance_called = False

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        self.fetch_calls.append((start, end))
        return [Path("/tmp/fake_raw.csv")]

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        self.parse_called = True
        return pl.DataFrame({"a": [1]}).lazy()

    def validate(self, df: pl.LazyFrame) -> None:
        self.validate_called = True

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        self.write_called = True
        return Path("/tmp/fake_processed.parquet")

    def emit_provenance(
        self,
        ctx: RunContext,
        source_paths: list[Path],
        output_path: Path,
    ) -> Path:
        self.provenance_called = True
        return Path("/tmp/fake_provenance.json")


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture()
def _fake_registry(monkeypatch: pytest.MonkeyPatch) -> _FakeJob:
    """Inject a fake job into INGEST_REGISTRY under 'fomc_text'."""
    job = _FakeJob()
    job.name = "fomc_text"
    monkeypatch.setitem(INGEST_REGISTRY, "fomc_text", job)
    yield job
    # monkeypatch auto-restores.


@pytest.fixture(autouse=True)
def _patch_load_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent _load_registry from importing sibling modules that may not exist."""
    import ingest as ingest_mod

    monkeypatch.setattr(ingest_mod, "_load_registry", lambda: None)


# -- Tests -------------------------------------------------------------------


class TestDateParsing:
    def test_valid_date(self) -> None:
        from ingest import _parse_date

        assert _parse_date("2024-06-15") == date(2024, 6, 15)

    def test_invalid_date_raises(self) -> None:
        import argparse

        from ingest import _parse_date

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid date"):
            _parse_date("not-a-date")

    def test_wrong_format_raises(self) -> None:
        import argparse

        from ingest import _parse_date

        with pytest.raises(argparse.ArgumentTypeError):
            _parse_date("15/06/2024")


class TestUnknownDataset:
    def test_unknown_dataset_exits_nonzero(self) -> None:
        """--dataset must be one of the declared choices; argparse rejects unknowns."""
        from ingest import run

        # argparse itself raises SystemExit(2) for invalid choices.
        with pytest.raises(SystemExit) as exc_info:
            run(["--dataset", "unknown", "--start", "2024-01-01", "--end", "2024-12-31"])
        assert exc_info.value.code != 0


class TestDryRun:
    def test_dry_run_fetches_but_does_not_parse(
        self, _fake_registry: _FakeJob, tmp_path: Path
    ) -> None:
        from ingest import run

        job = _fake_registry

        # Patch RunContext to avoid side effects (repro-log writes, etc.)
        with patch("ingest.RunContext") as mock_rc_cls:
            mock_ctx = mock_rc_cls.return_value.__enter__.return_value
            mock_ctx.paths = None
            mock_ctx.log = None

            exit_code = run([
                "--dataset",
                "fomc_text",
                "--start",
                "2024-01-01",
                "--end",
                "2024-06-30",
                "--dry-run",
            ])

        assert exit_code == 0
        assert len(job.fetch_calls) == 1
        assert job.fetch_calls[0] == (date(2024, 1, 1), date(2024, 6, 30))
        assert not job.parse_called
        assert not job.validate_called
        assert not job.write_called
        assert not job.provenance_called


class TestStartAfterEnd:
    def test_start_after_end_returns_nonzero(self) -> None:
        from ingest import run

        # Need fomc_text in registry for the dataset check to pass.
        job = _FakeJob()
        job.name = "fomc_text"
        INGEST_REGISTRY["fomc_text"] = job
        try:
            exit_code = run([
                "--dataset",
                "fomc_text",
                "--start",
                "2025-12-31",
                "--end",
                "2024-01-01",
            ])
            assert exit_code != 0
        finally:
            INGEST_REGISTRY.pop("fomc_text", None)


class TestDatasetNotInRegistry:
    def test_registered_choice_but_not_in_registry(self) -> None:
        """es_tick is a valid argparse choice but has no registered job."""
        from ingest import run

        exit_code = run([
            "--dataset",
            "es_tick",
            "--start",
            "2024-01-01",
            "--end",
            "2024-12-31",
        ])
        assert exit_code == 1
