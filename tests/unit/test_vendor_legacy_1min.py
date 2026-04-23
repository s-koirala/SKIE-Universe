"""Unit tests for vendor_legacy_1min ingest job.

Exercises fetch (SHA256 idempotency), parse (UTC tz, schema coerce),
validate (schema + OHLC consistency), write_processed (partitioning +
two-phase commit), and emit_provenance (dataset_checksums wired into
RunContext). No network, no sibling-repo dependency — synthetic CSVs
under a tmp_path root.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from pathlib import Path

import pandera.errors
import polars as pl
import pytest

from skie_ninja.data.ingest.vendor_legacy_1min import (
    VendorLegacy1minIngestJob,
    _SourceFile,
)
from skie_ninja.data.validation.schema import VendorLegacy1minSchema

# ---------------------------------------------------------------------------
# Helpers: synthetic CSVs matching the Databento ohlcv-1m shape
# ---------------------------------------------------------------------------

_CSV_HEADER = (
    "ts_event,rtype,publisher_id,instrument_id,"
    "open,high,low,close,volume,symbol\n"
)


def _write_synthetic_csv(
    path: Path,
    *,
    symbol: str,
    n_bars: int = 5,
    base_price: float = 4000.0,
    contract_symbol: str | None = None,
) -> None:
    """Write an n-row CSV with monotonic timestamps and sane OHLC.

    ``symbol`` is the *root* (ES/NQ). ``contract_symbol`` is the raw
    Databento contract code (e.g., ``ESH4``) and defaults to
    ``{symbol}H4`` if omitted — matching what the real feed emits.
    """
    cs = contract_symbol if contract_symbol is not None else f"{symbol}H4"
    lines = [_CSV_HEADER]
    for i in range(n_bars):
        ts = f"2024-01-0{(i % 9) + 1} 13:{30 + i:02d}:00+00:00"
        o = base_price + i * 0.25
        h = o + 0.5
        low = o - 0.25
        c = o + 0.1
        lines.append(
            f"{ts},34,1,42,{o},{h},{low},{c},{100 + i * 10},{cs}\n"
        )
    path.write_text("".join(lines), encoding="utf-8")


class _FakeCtx:
    """Minimal RunContext-shaped stand-in for unit tests."""

    class _FakePaths:
        def __init__(self, root: Path) -> None:
            self._root = root
            (root / "data_processed").mkdir(parents=True, exist_ok=True)
            (root / "shared").mkdir(parents=True, exist_ok=True)

        @property
        def data_processed(self) -> Path:
            return self._root / "data_processed"

        @property
        def shared_vendor_skie_ninja_legacy(self) -> Path:
            return self._root / "shared"

        def ensure(self, p: Path) -> Path:
            p.mkdir(parents=True, exist_ok=True)
            return p

    def __init__(self, root: Path) -> None:
        self.paths = _FakeCtx._FakePaths(root)
        self.log = None
        self._checksums: dict[str, str] = {}

    def add_dataset_checksum(self, name: str, sha256: str) -> None:
        self._checksums[name] = sha256


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------


class TestFetch:
    def test_copies_canonical_sources(self, tmp_path: Path) -> None:
        src_root = tmp_path / "src"
        src_root.mkdir()
        _write_synthetic_csv(src_root / "ES_2020_1min_databento.csv", symbol="ES")
        _write_synthetic_csv(src_root / "NQ_2020_1min_databento.csv", symbol="NQ")

        job = VendorLegacy1minIngestJob(
            source_root=src_root,
            sources=(
                _SourceFile("ES", "oos_2020", "ES_2020_1min_databento.csv"),
                _SourceFile("NQ", "oos_2020", "NQ_2020_1min_databento.csv"),
            ),
        )
        ctx = _FakeCtx(tmp_path / "ctx")
        out = job.fetch(date(2020, 1, 1), date(2020, 12, 31), ctx)
        assert len(out) == 2  # noqa: PLR2004 — two sources configured above
        for p in out:
            assert p.is_file()
            assert p.parent.name == "raw_1min"

    def test_sha256_idempotent(self, tmp_path: Path) -> None:
        """Second call without changes should skip copy."""
        src_root = tmp_path / "src"
        src_root.mkdir()
        _write_synthetic_csv(src_root / "ES_2020_1min_databento.csv", symbol="ES")
        job = VendorLegacy1minIngestJob(
            source_root=src_root,
            sources=(_SourceFile("ES", "oos_2020", "ES_2020_1min_databento.csv"),),
        )
        ctx = _FakeCtx(tmp_path / "ctx")
        out1 = job.fetch(date(2020, 1, 1), date(2020, 12, 31), ctx)
        mtime1 = out1[0].stat().st_mtime_ns

        out2 = job.fetch(date(2020, 1, 1), date(2020, 12, 31), ctx)
        # Same path returned; file not rewritten (mtime unchanged).
        assert out2 == out1
        assert out2[0].stat().st_mtime_ns == mtime1

    def test_missing_source_logged_not_raised(
        self, tmp_path: Path, caplog
    ) -> None:
        """A missing upstream file is logged-and-continued, not fatal.

        Rationale: the canonical list is all-or-nothing *as specified*,
        but sibling-repo rolls can legitimately lag (e.g., 2025 NQ not
        yet pulled). Let the ingest complete what it can so downstream
        gets the partial but verifiable result.
        """
        src_root = tmp_path / "src"
        src_root.mkdir()
        # Deliberately do not create the file.
        job = VendorLegacy1minIngestJob(
            source_root=src_root,
            sources=(_SourceFile("NQ", "forward_2025", "NQ_2025_1min_databento.csv"),),
        )
        ctx = _FakeCtx(tmp_path / "ctx")
        with caplog.at_level(logging.ERROR):
            out = job.fetch(date(2025, 1, 1), date(2025, 12, 31), ctx)
        assert out == []
        assert any("Source missing" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------


class TestParse:
    def test_parse_yields_utc_tz_aware_ts_event(self, tmp_path: Path) -> None:
        src = tmp_path / "x.csv"
        _write_synthetic_csv(src, symbol="ES")
        job = VendorLegacy1minIngestJob()
        lf = job.parse([src], _FakeCtx(tmp_path / "ctx"))
        df = lf.collect()
        dt = df.schema["ts_event"]
        assert isinstance(dt, pl.Datetime)
        assert dt.time_zone == "UTC"

    def test_parse_empty_input_returns_empty_frame(self, tmp_path: Path) -> None:
        job = VendorLegacy1minIngestJob()
        df = job.parse([], _FakeCtx(tmp_path / "ctx")).collect()
        assert df.height == 0
        assert set(df.columns) == {
            "ts_event", "rtype", "publisher_id", "instrument_id",
            "open", "high", "low", "close", "volume",
            "contract_symbol", "symbol",
        }

    def test_parse_concatenates_multiple_files(self, tmp_path: Path) -> None:
        a = tmp_path / "a.csv"
        b = tmp_path / "b.csv"
        _write_synthetic_csv(a, symbol="ES", n_bars=3)
        _write_synthetic_csv(b, symbol="NQ", n_bars=4)
        job = VendorLegacy1minIngestJob()
        df = job.parse([a, b], _FakeCtx(tmp_path / "ctx")).collect()
        assert df.height == 3 + 4  # sum of n_bars across files
        assert set(df["symbol"].unique().to_list()) == {"ES", "NQ"}

    def test_parse_extracts_root_from_contract_symbol(
        self, tmp_path: Path
    ) -> None:
        """Raw CSV carries ESH4/NQM3; parse normalizes to root ES/NQ."""
        src = tmp_path / "es.csv"
        _write_synthetic_csv(src, symbol="ES", contract_symbol="ESH4")
        job = VendorLegacy1minIngestJob()
        df = job.parse([src], _FakeCtx(tmp_path / "ctx")).collect()
        assert df["contract_symbol"][0] == "ESH4"
        assert df["symbol"][0] == "ES"


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


class TestValidate:
    def _valid_frame(self) -> pl.LazyFrame:
        return pl.DataFrame({
            "ts_event": [
                datetime(2024, 1, 2, 13, 30, tzinfo=UTC),
                datetime(2024, 1, 2, 13, 31, tzinfo=UTC),
            ],
            "rtype": [34, 34],
            "publisher_id": [1, 1],
            "instrument_id": [42, 42],
            "open": [4000.0, 4000.5],
            "high": [4001.0, 4001.5],
            "low": [3999.5, 4000.0],
            "close": [4000.5, 4001.0],
            "volume": [100, 110],
            "contract_symbol": ["ESH4", "ESH4"],
            "symbol": ["ES", "ES"],
        }).lazy()

    def test_valid_passes(self, tmp_path: Path) -> None:
        VendorLegacy1minIngestJob().validate(self._valid_frame())

    def test_rejects_duplicate_symbol_ts(self, tmp_path: Path) -> None:
        df = self._valid_frame().collect()
        dup = pl.concat([df, df.head(1)])  # row 0 duplicated
        with pytest.raises(pandera.errors.SchemaError):
            VendorLegacy1minIngestJob().validate(dup.lazy())

    def test_rejects_ohlc_violation(self, tmp_path: Path) -> None:
        # high < open: violates OHLC consistency
        df = (
            self._valid_frame()
            .collect()
            .with_columns(pl.Series("high", [3990.0, 4001.5]))
        )
        with pytest.raises(ValueError, match="OHLC consistency"):
            VendorLegacy1minIngestJob().validate(df.lazy())

    def test_rejects_non_utc_ts_event(self, tmp_path: Path) -> None:
        df = self._valid_frame().with_columns(
            pl.col("ts_event").dt.replace_time_zone(None)
        )
        with pytest.raises(pandera.errors.SchemaError):
            VendorLegacy1minIngestJob().validate(df)

    def test_rejects_unknown_symbol(self, tmp_path: Path) -> None:
        df = self._valid_frame().with_columns(pl.lit("CL").alias("symbol"))
        with pytest.raises(pandera.errors.SchemaError):
            VendorLegacy1minIngestJob().validate(df)


# ---------------------------------------------------------------------------
# write_processed + emit_provenance
# ---------------------------------------------------------------------------


class TestWriteAndProvenance:
    def _valid_frame(self) -> pl.LazyFrame:
        return pl.DataFrame({
            "ts_event": [
                datetime(2024, 1, 2, 13, 30, tzinfo=UTC),
                datetime(2024, 2, 2, 13, 30, tzinfo=UTC),
                datetime(2024, 1, 2, 13, 30, tzinfo=UTC),  # NQ same ts as ES
            ],
            "rtype": [34, 34, 34],
            "publisher_id": [1, 1, 1],
            "instrument_id": [42, 42, 43],
            "open": [4000.0, 4010.0, 14000.0],
            "high": [4001.0, 4011.0, 14001.0],
            "low": [3999.5, 4009.5, 13999.5],
            "close": [4000.5, 4010.5, 14000.5],
            "volume": [100, 200, 300],
            "contract_symbol": ["ESH4", "ESH4", "NQH4"],
            "symbol": ["ES", "ES", "NQ"],
        }).lazy()

    def test_partitions_by_symbol_and_year(self, tmp_path: Path) -> None:
        ctx = _FakeCtx(tmp_path / "ctx")
        out_dir = VendorLegacy1minIngestJob().write_processed(
            self._valid_frame(), ctx
        )
        es_year = out_dir / "symbol=ES" / "year=2024" / "part-0000.parquet"
        nq_year = out_dir / "symbol=NQ" / "year=2024" / "part-0000.parquet"
        assert es_year.is_file()
        assert nq_year.is_file()
        # Re-read to confirm schema survives parquet round-trip.
        VendorLegacy1minSchema.validate(pl.read_parquet(es_year))
        VendorLegacy1minSchema.validate(pl.read_parquet(nq_year))

    def test_emit_provenance_populates_dataset_checksums(
        self, tmp_path: Path
    ) -> None:
        # Two source files; provenance should carry both SHA256s and
        # ctx.add_dataset_checksum should have been invoked for each.
        src_a = tmp_path / "a.csv"
        src_b = tmp_path / "b.csv"
        _write_synthetic_csv(src_a, symbol="ES")
        _write_synthetic_csv(src_b, symbol="NQ")

        ctx = _FakeCtx(tmp_path / "ctx")
        out_dir = ctx.paths.data_processed / "vendor_legacy_1min"
        prov = VendorLegacy1minIngestJob().emit_provenance(
            ctx, [src_a, src_b], out_dir
        )
        payload = __import__("json").loads(prov.read_text(encoding="utf-8"))
        assert set(payload["source_checksums"].keys()) == {
            "a.csv",
            "b.csv",
        }
        # Raw tier is NOT evidence-bar eligible: the underlying series
        # concatenates front-month contracts without roll adjustment.
        # A downstream roll-adjusted derivative is the evidence-bar
        # input. Audit-remediate F-2-3.
        assert payload["evidence_bar_eligible"] is False
        assert payload["tier"] == "raw"
        assert payload["roll_adjustment"].startswith("none")
        # ctx.add_dataset_checksum side-effect.
        assert ctx._checksums == payload["source_checksums"]
