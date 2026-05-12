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


class VendorLegacy1minSchema(pa.DataFrameModel):
    """Schema for ``data/processed/vendor_legacy_1min/`` (Databento-sourced
    ES/NQ 1-minute bars, imported from the sibling SKIE_Ninja research repo).

    Matches the Databento ``ohlcv-1m`` schema as emitted by
    ``databento_downloader.py`` in the sibling repo plus a normalized
    symbol column. Constraints:
    - ``ts_event`` is UTC-tz-aware (Databento emits UTC)
    - OHLC strictly positive
    - ``low <= min(open, close)`` and ``high >= max(open, close)``
      (enforced by data-level check, not type-level)
    - ``volume >= 0``
    - unique ``(symbol, ts_event)`` so there is exactly one bar per
      (instrument, minute)
    """

    ts_event: pl.Datetime(time_zone="UTC") = pa.Field(nullable=False)
    rtype: pl.Int64 = pa.Field(nullable=False)
    publisher_id: pl.Int64 = pa.Field(nullable=False)
    instrument_id: pl.Int64 = pa.Field(nullable=False)
    # Note: prices can be NEGATIVE for commodity futures during stress events.
    # Canonical example: WTI Light Sweet Crude (CL/MCL) settled at -$37.63 on
    # 2020-04-20 due to physical-delivery supply imbalance + Cushing storage
    # capacity exhaustion. Validation must accept negative prices to preserve
    # this historically real signal; the prior `gt=0` rule was equity-index
    # specific (equity-index prices are bounded below by zero by construction).
    # We retain a finite lower bound to catch obvious data corruption while
    # allowing the documented commodity-negative-price regime; -1000 USD is a
    # generous lower bound vs the -$37.63 historical extremum.
    open: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    high: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    low: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    close: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    volume: pl.Int64 = pa.Field(nullable=False, ge=0)
    # Contract-specific symbol from Databento (e.g., ESH0, NQM3).
    contract_symbol: pl.Utf8 = pa.Field(nullable=False)
    # Normalized root symbol — product-root prefix of contract_symbol
    # (2 chars for equity-index ES/NQ; 3 chars for micros MES/MNQ and
    # for H060 energy/metals MCL/MGC/SIL).
    symbol: pl.Utf8 = pa.Field(
        nullable=False,
        isin=["ES", "NQ", "MES", "MNQ", "MCL", "MGC", "SIL"],
    )

    class Config:
        """Uniqueness at the contract level: one bar per (contract, minute).

        ``(symbol, ts_event)`` intentionally *not* unique — during roll
        windows the same UTC minute can legitimately appear under two
        adjacent contract codes for the same root symbol.
        """

        unique = ["contract_symbol", "ts_event"]
        strict = True


class VendorLegacy1minRollAdjustedSchema(pa.DataFrameModel):
    """Schema for ``data/processed/vendor_legacy_1min_roll_adjusted/``.

    Continuous-contract derivative of ``vendor_legacy_1min``:
    successive front-month contracts stitched together with
    multiplicative ratio adjustment per de Prado 2018 *Advances in
    Financial Machine Learning* ch.2 **§2.4.3** ("Single Future Roll" —
    NOT §2.4.1 "The ETF Trick", which is a P&L-accumulation method
    for baskets/spreads), rolled on volume-crossover with persistence
    per [config/instruments.yaml](../../../../config/instruments.yaml)
    ``roll_rule``. Log-returns on the adjusted series are preserved
    across roll boundaries (that's the point of ratio adjustment).

    **Evidence-bar tier discrimination**: this table is evidence-bar
    eligible for *return-based* features only. Level columns
    (``open``, ``high``, ``low``, ``close``) are retrospectively
    rescaled by the full-sample roll history and are NOT
    point-in-time safe for walk-forward use without per-fold
    re-materialization. See the module-level docstring "Point-in-time
    caveat" section. The provenance JSON discriminates via
    ``evidence_bar_eligible_returns`` (True) vs
    ``evidence_bar_eligible_levels`` (False).

    Columns:

    - ``ts_event`` — UTC-tz-aware minute timestamp; monotonic per symbol.
    - ``open``, ``high``, ``low``, ``close`` — **ratio-adjusted** OHLC
      (multiplicative back-adjustment; latest contract has
      ``adjustment_factor == 1.0``). OHLC consistency preserved.
    - ``volume`` — NOT adjusted (a multiplicative price adjustment
      does not transform contract volume).
    - ``symbol`` — root (ES/NQ/MES/MNQ).
    - ``front_contract_symbol`` — the specific contract code (e.g.,
      ESH4) that was front-month at ``ts_event``. Exactly one
      front-month per (symbol, ts_event).
    - ``adjustment_factor`` — the cumulative multiplier applied to the
      raw prices of this row to produce the adjusted prices. ==1.0 for
      the most-recent contract; ==prod(ρ_k) across all rolls newer than
      this row's contract otherwise.
    - ``unadjusted_close`` — the raw close price for this bar (audit
      trail: ``adjusted_close == unadjusted_close * adjustment_factor``).
    - ``roll_flag`` — True on rows whose session is the first session
      where this row's contract became front-month (diagnostic — a roll
      boundary marker for downstream purge/embargo logic).
    """

    ts_event: pl.Datetime(time_zone="UTC") = pa.Field(nullable=False)
    # Allows commodity-stress negative prices per the WTI 2020-04-20 precedent
    # (cf. VendorLegacy1MinSchema docstring). adjustment_factor remains gt=0
    # since the multiplier is by construction positive; roll-adjusted prices
    # inherit the sign of the raw price.
    open: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    high: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    low: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    close: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    volume: pl.Int64 = pa.Field(nullable=False, ge=0)
    symbol: pl.Utf8 = pa.Field(
        nullable=False,
        isin=["ES", "NQ", "MES", "MNQ", "MCL", "MGC", "SIL"],
    )
    front_contract_symbol: pl.Utf8 = pa.Field(nullable=False)
    adjustment_factor: pl.Float64 = pa.Field(nullable=False, gt=0)
    unadjusted_close: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    roll_flag: pl.Boolean = pa.Field(nullable=False)

    class Config:
        """One front-month bar per (symbol, ts_event).

        Unlike ``VendorLegacy1minSchema`` (which allows concurrent
        contracts to coexist during roll windows), the roll-adjusted
        series is a single continuous front-month series per root
        symbol — so ``(symbol, ts_event)`` IS unique here.
        """

        unique = ["symbol", "ts_event"]
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
