"""Databento extraction — ES + NQ pre-2020 backfill + NQ 2025 gap.

Per operator 2026-05-16 directive: backfill ES + NQ 2015-01-01 → 2019-12-31
(5 years) for full pre-COVID training symmetry with MGC + SIL, plus
NQ 2024-12-20 → 2025-12-31 (~1 year gap) to bring NQ to ES parity.

Estimated cost: ~$20-25 USD (within $30 tight ceiling per ADR-0023 §6).

Security: DATABENTO_API_KEY env-var-only. Never written to disk.
_fingerprint_api_key returns "<suppressed-for-security>". Mirrors
scripts/databento_extract_2026_h1.py pattern.

Output: CSVs in ~/datasets/vendor_skie_ninja_legacy/raw_1min/
following the {SYMBOL}_{YYYY}_1min_databento.csv naming convention
established at Phase O.0 Stage A.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

HOME = Path.home()
RAW_DIR = HOME / "datasets" / "vendor_skie_ninja_legacy" / "raw_1min"
RAW_DIR.mkdir(parents=True, exist_ok=True)

DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1m"
STYPE_IN = "parent"

# 6 extraction windows (per-year slicing per Phase O.0 ES naming convention)
EXTRACTIONS: list[dict[str, str]] = [
    {"symbol": "ES.FUT", "start": "2015-01-01", "end": "2015-12-31", "out_name": "ES_2015_1min_databento.csv"},
    {"symbol": "ES.FUT", "start": "2016-01-01", "end": "2016-12-31", "out_name": "ES_2016_1min_databento.csv"},
    {"symbol": "ES.FUT", "start": "2017-01-01", "end": "2017-12-31", "out_name": "ES_2017_1min_databento.csv"},
    {"symbol": "ES.FUT", "start": "2018-01-01", "end": "2018-12-31", "out_name": "ES_2018_1min_databento.csv"},
    {"symbol": "ES.FUT", "start": "2019-01-01", "end": "2019-12-31", "out_name": "ES_2019_1min_databento.csv"},
    {"symbol": "NQ.FUT", "start": "2015-01-01", "end": "2015-12-31", "out_name": "NQ_2015_1min_databento.csv"},
    {"symbol": "NQ.FUT", "start": "2016-01-01", "end": "2016-12-31", "out_name": "NQ_2016_1min_databento.csv"},
    {"symbol": "NQ.FUT", "start": "2017-01-01", "end": "2017-12-31", "out_name": "NQ_2017_1min_databento.csv"},
    {"symbol": "NQ.FUT", "start": "2018-01-01", "end": "2018-12-31", "out_name": "NQ_2018_1min_databento.csv"},
    {"symbol": "NQ.FUT", "start": "2019-01-01", "end": "2019-12-31", "out_name": "NQ_2019_1min_databento.csv"},
    {"symbol": "NQ.FUT", "start": "2025-01-01", "end": "2025-12-31", "out_name": "NQ_2025_1min_databento.csv"},
]


def _fingerprint_api_key(api_key: str) -> str:
    if not api_key:
        return "<missing>"
    return "<suppressed-for-security>"


def main() -> int:
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        print("[error] DATABENTO_API_KEY env var not set.", file=sys.stderr)
        return 2
    try:
        import databento as db  # noqa: PLC0415
    except ImportError:
        print("[error] databento SDK missing; run: uv pip install databento", file=sys.stderr)
        return 3

    sdk_version = getattr(db, "__version__", "unknown")
    print(f"[info] databento SDK version: {sdk_version}")
    print(f"[info] api_key fingerprint: {_fingerprint_api_key(api_key)}")
    print(f"[info] dataset={DATASET}, schema={SCHEMA}, stype_in={STYPE_IN}")
    print(f"[info] {len(EXTRACTIONS)} windows total")
    print()

    client = db.Historical(key=api_key)

    # Cost dossier
    total_cost = 0.0
    print(f"{'symbol':<10} {'window':<24} {'cost_usd':>10}")
    print("-" * 50)
    for spec in EXTRACTIONS:
        out_path = RAW_DIR / spec["out_name"]
        if out_path.exists():
            print(f"{spec['symbol']:<10} {spec['start']}-{spec['end']:<13} {'(exists)':>10}")
            continue
        try:
            cost = client.metadata.get_cost(
                dataset=DATASET, symbols=[spec["symbol"]], stype_in=STYPE_IN,
                schema=SCHEMA, start=spec["start"], end=spec["end"],
            )
            cost = float(cost)
            total_cost += cost
            print(f"{spec['symbol']:<10} {spec['start']}-{spec['end']:<13} ${cost:>9.4f}")
        except Exception as e:  # noqa: BLE001
            print(f"{spec['symbol']:<10} {spec['start']}-{spec['end']:<13} {'<ERROR>':>10}  // {e}")
            return 4
    print("-" * 50)
    print(f"{'TOTAL':<10} {'':<24} ${total_cost:>9.4f}  USD")
    print()
    if total_cost > 30.0:
        print(f"[error] cost ${total_cost:.4f} > $30 tight ceiling; aborting.", file=sys.stderr)
        return 5

    print(f"[info] cost OK; proceeding with extraction (${total_cost:.4f} USD)")
    print()
    extraction_summary: list[dict] = []
    for spec in EXTRACTIONS:
        out_path = RAW_DIR / spec["out_name"]
        if out_path.exists():
            print(f"[info] {spec['out_name']}: already exists; skipping")
            extraction_summary.append({"file": spec["out_name"], "skipped": True, "rows": None})
            continue
        print(f"[info] {spec['out_name']}: extracting...")
        t0 = time.time()
        try:
            data = client.timeseries.get_range(
                dataset=DATASET, symbols=[spec["symbol"]], stype_in=STYPE_IN,
                schema=SCHEMA, start=spec["start"], end=spec["end"],
            )
            df = data.to_df()
            elapsed = time.time() - t0
            df.to_csv(out_path, index=True)
            rows = len(df)
            print(f"[info]   {spec['out_name']}: {rows:,} rows in {elapsed:.1f}s -> {out_path}")
            extraction_summary.append({"file": spec["out_name"], "skipped": False, "rows": rows, "elapsed_s": elapsed})
        except Exception as e:  # noqa: BLE001
            print(f"[error] {spec['out_name']}: failed: {type(e).__name__}: {e}", file=sys.stderr)
            return 6

    print()
    print("=" * 60)
    print(f"EXTRACTION COMPLETE  total_cost_usd=${total_cost:.4f}")
    for row in extraction_summary:
        rows_str = f"{row['rows']:,}" if row.get('rows') is not None else "(skipped)"
        print(f"  {row['file']:<35} {rows_str}")
    print(f"  raw_dir: {RAW_DIR}")
    print()
    print("NEXT STEPS:")
    print("  1. Copy CSVs to sibling repo path:")
    print("     C:\\Users\\skoir\\Documents\\SKIE Enterprises\\SKIE-Ninja\\SKIE-Ninja-Project\\SKIE_Ninja\\data\\raw\\market\\")
    print("  2. Re-run scripts/ingest.py --dataset vendor_legacy_1min --start 2015-01-01 --end 2026-05-15")
    print("  3. Re-run scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2026-05-15")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
