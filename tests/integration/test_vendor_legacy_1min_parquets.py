"""Integration smoke-test: vendor_legacy_1min partitioned parquets.

Reads the real parquets emitted by ``python scripts/ingest.py --dataset
vendor_legacy_1min`` and asserts the year/symbol row counts fall inside
the Databento ohlcv-1m expected range (one 1-min bar per RTH+ETH
minute, ~350k bars/year accounting for weekends/holidays/session gaps).

Machine-local only — skip-if-missing so CI without the parquet tree
skips cleanly.

Closes audit-remediate F-2-7.
"""

from __future__ import annotations

import polars as pl
import pytest

from skie_ninja.data.validation.schema import VendorLegacy1minSchema
from skie_ninja.utils.paths import ProjectPaths

pytestmark = pytest.mark.integration

# Expected bar count per (symbol, year) partition. Derived from CME
# Globex session length: 23h/day × ~252 trading days × 60 = ~348k
# minutes; in practice ranges across 300k–360k due to holidays and
# half-day sessions. Bound generously so legitimate calendar variation
# does not trip the smoke test, while a corrupted/truncated partition
# (e.g., 100k rows) would.
_MIN_BARS_PER_YEAR = 300_000
_MAX_BARS_PER_YEAR = 400_000


@pytest.fixture(scope="module")
def base_dir():
    paths = ProjectPaths.discover()
    d = paths.data_processed / "vendor_legacy_1min"
    if not d.is_dir():
        pytest.skip(
            f"vendor_legacy_1min parquet tree absent at {d}; run "
            "`uv run python scripts/ingest.py --dataset vendor_legacy_1min "
            "--start 2020-01-01 --end 2025-12-31` to materialize."
        )
    return d


def test_expected_partition_structure(base_dir) -> None:
    """ES and NQ subdirs exist; every year dir has exactly one parquet."""
    es_dir = base_dir / "symbol=ES"
    nq_dir = base_dir / "symbol=NQ"
    assert es_dir.is_dir(), "symbol=ES partition missing"
    assert nq_dir.is_dir(), "symbol=NQ partition missing"

    for sym_dir in (es_dir, nq_dir):
        years = sorted(p.name for p in sym_dir.iterdir() if p.is_dir())
        assert years, f"{sym_dir} has no year partitions"
        for year_dir in sym_dir.iterdir():
            parts = list(year_dir.glob("*.parquet"))
            assert len(parts) == 1, (
                f"{year_dir} should have exactly one part file, got {len(parts)}"
            )


def test_per_partition_schema_and_row_count(base_dir) -> None:
    """Every partition schema-validates and has a plausible bar count."""
    for sym in ("ES", "NQ"):
        sym_dir = base_dir / f"symbol={sym}"
        for year_dir in sorted(sym_dir.iterdir()):
            part = next(year_dir.glob("*.parquet"))
            df = pl.read_parquet(part)
            VendorLegacy1minSchema.validate(df)
            assert _MIN_BARS_PER_YEAR <= df.height <= _MAX_BARS_PER_YEAR, (
                f"{sym} {year_dir.name}: "
                f"row count {df.height} outside plausible range "
                f"[{_MIN_BARS_PER_YEAR}, {_MAX_BARS_PER_YEAR}]"
            )


def test_ts_event_monotonic_per_contract_symbol(base_dir) -> None:
    """Within each contract_symbol, ts_event is strictly increasing.

    Look-ahead-free feature computation downstream assumes monotone
    time per instrument. This also catches accidental concatenation
    of overlapping year slices.
    """
    for sym in ("ES", "NQ"):
        sym_dir = base_dir / f"symbol={sym}"
        for year_dir in sorted(sym_dir.iterdir()):
            part = next(year_dir.glob("*.parquet"))
            df = pl.read_parquet(part).sort(["contract_symbol", "ts_event"])
            # strictly increasing within each contract_symbol
            diffs = (
                df.group_by("contract_symbol", maintain_order=True)
                .agg(
                    (pl.col("ts_event").diff() > 0).all().alias("strictly_inc")
                )
            )
            assert diffs["strictly_inc"].all(), (
                f"{sym} {year_dir.name}: non-monotonic ts_event "
                f"within a contract_symbol"
            )


def test_evidence_bar_eligibility_is_false_in_provenance(base_dir) -> None:
    """Provenance must not mark the raw tier evidence-bar eligible."""
    import json

    paths = ProjectPaths.discover()
    prov_files = sorted(
        (paths.data_processed / "_provenance").glob("vendor_legacy_1min_*.json")
    )
    if not prov_files:
        pytest.skip("No vendor_legacy_1min provenance file present.")
    payload = json.loads(prov_files[-1].read_text(encoding="utf-8"))
    assert payload["evidence_bar_eligible"] is False
    assert payload["tier"] == "raw"
    assert payload.get("roll_adjustment", "").startswith("none")
