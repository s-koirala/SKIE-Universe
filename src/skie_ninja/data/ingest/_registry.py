"""Ingest job protocol and registry.

Defines the ``IngestJob`` protocol (plan section 2.1) and a global
``INGEST_REGISTRY`` dict keyed by ``IngestJob.name``.  Concrete jobs
(``fomc_text``, ``macro_surprise``, ``es_tick``) live in sibling
modules and self-register at import time via ``register()``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Protocol, runtime_checkable

import polars as pl

from skie_ninja.utils.runcontext import RunContext

# Global registry: name -> IngestJob instance.
INGEST_REGISTRY: dict[str, IngestJob] = {}


@runtime_checkable
class IngestJob(Protocol):
    """Contract every ingest adapter must satisfy (plan section 2.1)."""

    name: str
    version: str

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        """Download or locate raw files for the date range."""
        ...

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        """Parse raw files into a validated LazyFrame."""
        ...

    def validate(self, df: pl.LazyFrame) -> None:
        """Run schema + distribution checks; raise on failure."""
        ...

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        """Write validated data to ``data/processed/``."""
        ...

    def emit_provenance(
        self,
        ctx: RunContext,
        source_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Write provenance JSON; return the provenance file path."""
        ...


def register(job: IngestJob) -> None:
    """Add *job* to ``INGEST_REGISTRY``.

    Raises ``TypeError`` if *job* does not satisfy :class:`IngestJob`.
    Raises ``ValueError`` on duplicate name.
    """
    if not isinstance(job, IngestJob):
        raise TypeError(
            f"Expected an IngestJob protocol implementation, got {type(job).__name__}"
        )
    if job.name in INGEST_REGISTRY:
        raise ValueError(
            f"Duplicate ingest job name: {job.name!r} "
            f"(existing version {INGEST_REGISTRY[job.name].version}, "
            f"new version {job.version})"
        )
    INGEST_REGISTRY[job.name] = job
