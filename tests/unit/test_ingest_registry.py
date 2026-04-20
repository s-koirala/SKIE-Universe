"""Tests for the ingest registry and IngestJob protocol conformance."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl
import pytest

from skie_ninja.data.ingest import INGEST_REGISTRY, IngestJob, register
from skie_ninja.utils.runcontext import RunContext

# ---------------------------------------------------------------------------
# Dummy IngestJob implementation for protocol conformance testing
# ---------------------------------------------------------------------------


class _DummyJob:
    """Minimal IngestJob conformant implementation."""

    name: str = "dummy_test"
    version: str = "0.1.0"

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        return []

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        return pl.LazyFrame()

    def validate(self, df: pl.LazyFrame) -> None:
        pass

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        return Path("out.parquet")

    def emit_provenance(
        self, ctx: RunContext, source_paths: list[Path], output_path: Path
    ) -> Path:
        return Path("prov.json")


class _NonConformant:
    """Missing required methods — should fail isinstance check."""

    name: str = "bad"
    version: str = "0.0.0"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIngestJobProtocol:
    def test_dummy_satisfies_protocol(self) -> None:
        assert isinstance(_DummyJob(), IngestJob)

    def test_non_conformant_rejected(self) -> None:
        assert not isinstance(_NonConformant(), IngestJob)


class TestRegister:
    def setup_method(self) -> None:
        # Isolate registry state per test.
        self._snapshot = dict(INGEST_REGISTRY)

    def teardown_method(self) -> None:
        INGEST_REGISTRY.clear()
        INGEST_REGISTRY.update(self._snapshot)

    def test_register_adds_to_registry(self) -> None:
        job = _DummyJob()
        register(job)
        assert INGEST_REGISTRY["dummy_test"] is job

    def test_duplicate_name_raises(self) -> None:
        register(_DummyJob())
        with pytest.raises(ValueError, match="Duplicate ingest job name"):
            register(_DummyJob())

    def test_non_conformant_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="IngestJob protocol"):
            register(_NonConformant())  # type: ignore[arg-type]
