"""Pandera + pydantic schemas for ingested datasets (plan section 2.1).

Schemas enforce column types, value constraints, and uniqueness
invariants. They are invoked by each ``IngestJob.validate`` method
before data reaches ``data/processed/``.

Pandera-polars is used for DataFrame-level validation; pydantic
models provide row-level typing for use in tests and documentation.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

import pandera.polars as pa
import polars as pl
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FomcDocType(StrEnum):
    """Allowed FOMC document types."""

    statement = "statement"
    minutes = "minutes"
    press_conference = "press_conference"


# ---------------------------------------------------------------------------
# Pydantic row models (documentation + test fixtures)
# ---------------------------------------------------------------------------


class FomcTextRow(BaseModel):
    """Single FOMC text record."""

    release_ts_utc: datetime
    embargo_ts_utc: datetime
    doc_type: FomcDocType
    sha256: str
    raw_path: str
    text_normalized: str


class MacroSurpriseRow(BaseModel):
    """Single macro-surprise record."""

    release_date: date
    release_ts_utc: datetime
    event_id: str
    indicator: str
    actual: float
    consensus_median: float | None = None
    std_consensus: float | None = None
    surprise_z: float | None = None
    source: str
    vintage_date: date


# ---------------------------------------------------------------------------
# Pandera-polars schemas
# ---------------------------------------------------------------------------


class FomcTextSchema(pa.DataFrameModel):
    """Schema for ``data/processed/fomc_text/``."""

    release_ts_utc: pl.Datetime(time_zone="UTC") = pa.Field(nullable=False)
    embargo_ts_utc: pl.Datetime(time_zone="UTC") = pa.Field(nullable=False)
    doc_type: pl.Utf8 = pa.Field(
        nullable=False,
        isin=[e.value for e in FomcDocType],
    )
    sha256: pl.Utf8 = pa.Field(nullable=False)
    raw_path: pl.Utf8 = pa.Field(nullable=False)
    text_normalized: pl.Utf8 = pa.Field(nullable=False)

    class Config:
        """Enforce no duplicate (release_ts_utc, doc_type) pairs."""

        unique = ["release_ts_utc", "doc_type"]
        strict = True


class EsTickSchema(pa.DataFrameModel):
    """Schema for ``data/processed/es_tick/`` (plan §2.1).

    Stub awaiting Databento ingest module. Constraints per plan:
    - monotonic ``ts_event_ns``
    - ``price > 0``
    - ``size > 0``
    - unique ``(ts_event_ns, sequence)``
    """

    ts_event_ns: pl.Int64 = pa.Field(nullable=False)
    ts_recv_ns: pl.Int64 = pa.Field(nullable=False)
    price: pl.Float64 = pa.Field(nullable=False, gt=0)
    size: pl.Int64 = pa.Field(nullable=False, gt=0)
    side: pl.Utf8 = pa.Field(nullable=True)
    aggressor: pl.Utf8 = pa.Field(nullable=True)
    sequence: pl.Int64 = pa.Field(nullable=False)
    symbol: pl.Utf8 = pa.Field(nullable=False)
    contract_month: pl.Utf8 = pa.Field(nullable=False)

    class Config:
        """Enforce monotonic ts_event_ns and unique (ts_event_ns, sequence)."""

        unique = ["ts_event_ns", "sequence"]
        ordered = True
        strict = True


class MacroSurpriseSchema(pa.DataFrameModel):
    """Schema for ``data/processed/macro_surprise/``."""

    release_date: pl.Date = pa.Field(nullable=False)
    release_ts_utc: pl.Datetime(time_zone="UTC") = pa.Field(nullable=False)
    event_id: pl.Utf8 = pa.Field(nullable=False)
    indicator: pl.Utf8 = pa.Field(nullable=False)
    actual: pl.Float64 = pa.Field(nullable=False)
    consensus_median: pl.Float64 = pa.Field(nullable=True)
    std_consensus: pl.Float64 = pa.Field(nullable=True)
    surprise_z: pl.Float64 = pa.Field(nullable=True)
    source: pl.Utf8 = pa.Field(nullable=False)
    vintage_date: pl.Date = pa.Field(nullable=False)

    class Config:
        """Enforce no duplicate (release_date, event_id) pairs."""

        unique = ["release_date", "event_id"]
        strict = True
