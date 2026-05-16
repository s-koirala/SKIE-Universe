"""Databento extraction script — 2026-H1 fresh OOS window for H062.

Per operator 2026-05-15 authorization: extract ES + NQ + MGC + SIL × 2026-01-01 → 2026-05-15
at ``ohlcv-1m`` schema for fresh OOS window beyond the Phase O.0 Stage A substrate end
(2025-12-30 for metals; 2025-12-03 for ES; 2024-12-19 for NQ).

Security discipline (mirrors scripts/databento_metals_energy_cost_dossier.py
2026-05-12 operator-shared-key-in-chat-transcript incident hardening):
  - DATABENTO_API_KEY read from env var ONLY.
  - Key never written to disk, never logged, never echoed.
  - _fingerprint_api_key returns "<suppressed-for-security>" — even partial-
    key information (last-4-chars + length) suppressed to prevent any
    fragment from persisting to disk.
  - Output CSVs go to ~/datasets/vendor_skie_ninja_legacy/raw_1min/
    following the existing 2026 naming convention
    ``{SYMBOL}_2026H1_1min_databento.csv``.

After extraction, run scripts/ingest.py --dataset vendor_legacy_1min and
vendor_legacy_1min_roll_adjusted to materialize the appended substrate
partitions.

Operator-action follow-up: rotate the supplied API key post-use per the
established CLAUDE.md Phase O.0 P1-DATABENTO-KEY-ROTATE-POST-CHAT-EXPOSURE
discipline (second chat exposure event 2026-05-15).
"""

from __future__ import annotations

import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Output paths
HOME = Path.home()
RAW_DIR = HOME / "datasets" / "vendor_skie_ninja_legacy" / "raw_1min"
RAW_DIR.mkdir(parents=True, exist_ok=True)

DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1m"
STYPE_IN = "parent"

START = "2026-01-01"
END = "2026-05-15"

# Symbols + suffixes mirror Phase O.0 Stage A pattern.
SYMBOLS: list[dict[str, str]] = [
    {"symbol": "ES.FUT", "out_name": "ES_2026H1_1min_databento.csv"},
    {"symbol": "NQ.FUT", "out_name": "NQ_2026H1_1min_databento.csv"},
    {"symbol": "MGC.FUT", "out_name": "MGC_2026H1_1min_databento.csv"},
    {"symbol": "SIL.FUT", "out_name": "SIL_2026H1_1min_databento.csv"},
]


def _fingerprint_api_key(api_key: str) -> str:
    """Defanged fingerprint — even last-4 + length suppressed."""
    if not api_key:
        return "<missing>"
    return "<suppressed-for-security>"


def main() -> int:
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        print(
            "[error] DATABENTO_API_KEY env var not set.",
            file=sys.stderr,
        )
        return 2

    try:
        import databento as db  # noqa: PLC0415
    except ImportError:
        print(
            "[error] databento Python SDK not installed.\n"
            "  Run: uv pip install databento\n",
            file=sys.stderr,
        )
        return 3

    sdk_version = getattr(db, "__version__", "unknown")
    print(f"[info] databento SDK version: {sdk_version}")
    print(f"[info] api_key fingerprint: {_fingerprint_api_key(api_key)}")
    print(f"[info] dataset={DATASET}, schema={SCHEMA}, stype_in={STYPE_IN}")
    print(f"[info] window: {START} -> {END}")
    print(f"[info] raw_dir: {RAW_DIR}")
    print()

    client = db.Historical(key=api_key)

    # Step 1: cost dossier
    total_cost = 0.0
    print(f"{'symbol':<10} {'cost_usd':>10} {'description':<40}")
    print("-" * 70)
    for spec in SYMBOLS:
        try:
            cost = client.metadata.get_cost(
                dataset=DATASET,
                symbols=[spec["symbol"]],
                stype_in=STYPE_IN,
                schema=SCHEMA,
                start=START,
                end=END,
            )
            cost = float(cost)
            total_cost += cost
            print(f"{spec['symbol']:<10} ${cost:>9.4f}  {spec['out_name']}")
        except Exception as e:  # noqa: BLE001
            print(f"{spec['symbol']:<10} {'<ERROR>':>10}  {type(e).__name__}: {e}")
            return 4
    print("-" * 70)
    print(f"{'TOTAL':<10} ${total_cost:>9.4f}  USD")
    print()
    if total_cost > 30.0:
        print(f"[error] cost ${total_cost:.4f} > $30 tight ceiling; aborting.", file=sys.stderr)
        return 5

    # Step 2: extraction
    print(f"[info] cost OK; proceeding with extraction (${total_cost:.4f} USD)")
    print()
    extraction_summary: list[dict] = []
    for spec in SYMBOLS:
        out_path = RAW_DIR / spec["out_name"]
        if out_path.exists():
            print(f"[info] {spec['symbol']}: output already exists at {out_path}; skipping")
            extraction_summary.append({
                "symbol": spec["symbol"],
                "out_path": str(out_path),
                "skipped": True,
                "rows": None,
            })
            continue
        print(f"[info] {spec['symbol']}: extracting...")
        t0 = time.time()
        try:
            data = client.timeseries.get_range(
                dataset=DATASET,
                symbols=[spec["symbol"]],
                stype_in=STYPE_IN,
                schema=SCHEMA,
                start=START,
                end=END,
            )
            df = data.to_df()
            elapsed = time.time() - t0
            df.to_csv(out_path, index=True)  # index=True to preserve ts_event
            rows = len(df)
            print(f"[info]   {spec['symbol']}: {rows:,} rows in {elapsed:.1f}s -> {out_path}")
            extraction_summary.append({
                "symbol": spec["symbol"],
                "out_path": str(out_path),
                "skipped": False,
                "rows": rows,
                "elapsed_s": elapsed,
            })
        except Exception as e:  # noqa: BLE001
            print(f"[error] {spec['symbol']}: extraction failed: {type(e).__name__}: {e}", file=sys.stderr)
            return 6

    print()
    print("=" * 70)
    print(f"EXTRACTION COMPLETE")
    print(f"  total_cost_usd: ${total_cost:.4f}")
    print(f"  rows_per_symbol:")
    for row in extraction_summary:
        rows_str = f"{row['rows']:,}" if row['rows'] is not None else "(skipped; existed)"
        print(f"    {row['symbol']:<10} {rows_str}")
    print(f"  raw_dir: {RAW_DIR}")
    print(f"  NEXT: run `python scripts/ingest.py --dataset vendor_legacy_1min` and")
    print(f"        `python scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted`")
    print(f"        to materialize the appended substrate partitions.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
