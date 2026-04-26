---
name: H050 Cell I — Databento backfill runbook
description: Step-by-step authorization-gated procedure for backfilling ES + NQ 2015-2019 + NQ 2025 from Databento GLBX.MDP3 to close the H050 design.md §2 substrate gap. Round-1 documentation under audit-remediate-loop discipline; isolated-subagent verification deferred to main thread.
type: project
status: prepared, awaiting user authorization for paid Databento API call
created: 2026-04-24
hypothesis_id: H050
follow_up_id: P1-H050-DATA-COVERAGE
audience: skoir
---

# Runbook — H050 Cell I Databento backfill (2026-04-24)

## 0. Status and authorization gate

Status: **prepared, NOT executed.** The Databento API call is paid (account at sibling repo path, not in SKIE-Universe). This document is the runbook the user follows to authorize and execute the backfill; the agent that produced it explicitly did not place the paid call.

User-accepted Cell I disposition recorded 2026-04-24 per [memo_option-b-data-coverage_2026-04-24.md](memo_option-b-data-coverage_2026-04-24.md) §6 (Cell I = backfill substrate + run H050 as designed).

## 1. Scope

Backfill the H050 design.md §2 train-window substrate gap and the test-window NQ 2025 gap. The Stage A pull uses the sibling `download_historical_years` method, which iterates the four CME equity-index contract months `H, M, U, Z` per year using **contract-month-bounded windows** (not full calendar-year windows) — see §1.1 below for the intrinsic Dec 21-31 gap that follows from this design. Resulting per-year row counts have been verified empirically against the existing 2020-2024 substrate.

| Item | Symbol | Range | Approx rows | Approx CSV bytes |
|---|---|---|---|---|
| ES 2015 | ES | 2015-01-01 → ~2015-12-20 | ~340,000 | ~26 MB |
| ES 2016 | ES | 2016-01-01 → ~2016-12-20 | ~340,000 | ~26 MB |
| ES 2017 | ES | 2017-01-01 → ~2017-12-20 | ~340,000 | ~26 MB |
| ES 2018 | ES | 2018-01-01 → ~2018-12-20 | ~340,000 | ~26 MB |
| ES 2019 | ES | 2019-01-01 → ~2019-12-20 | ~340,000 | ~26 MB |
| NQ 2015 | NQ | 2015-01-01 → ~2015-12-20 | ~340,000 | ~26 MB |
| NQ 2016 | NQ | 2016-01-01 → ~2016-12-20 | ~340,000 | ~26 MB |
| NQ 2017 | NQ | 2017-01-01 → ~2017-12-20 | ~340,000 | ~26 MB |
| NQ 2018 | NQ | 2018-01-01 → ~2018-12-20 | ~340,000 | ~26 MB |
| NQ 2019 | NQ | 2019-01-01 → ~2019-12-20 | ~340,000 | ~26 MB |
| NQ 2025 | NQ | 2025-01-01 → ~2025-12-20 | ~360,000 | ~27 MB |
| **Total** | | | **~3.74M** | **~290 MB** |

Row densities are **empirically anchored** by the existing 2020-2024 substrate. Verbatim per-CSV inspection 2026-04-25 of `~/datasets/vendor_skie_ninja_legacy/raw_1min/`:

| File | Rows | First ts_event | Last ts_event |
|---|---|---|---|
| ES_2020_1min_databento.csv | 338,266 | 2020-01-01 23:00 UTC | 2020-12-18 14:29 UTC |
| ES_2021_1min_databento.csv | 340,377 | 2021-01-03 23:00 UTC | 2021-12-17 14:29 UTC |
| ES_2022_1min_databento.csv | 341,145 | 2022-01-02 23:00 UTC | 2022-12-16 14:29 UTC |
| ES_1min_databento.csv (2023+2024 combined) | 684,410 | 2023-01-02 23:00 UTC | 2024-12-19 23:59 UTC |
| ES_2025_1min_databento.csv | 326,475 | 2025-01-01 23:00 UTC | 2025-12-03 23:59 UTC (mtime 2024-12-04) |
| NQ_2020_1min_databento.csv | 337,408 | 2020-01-01 23:00 UTC | 2020-12-18 14:29 UTC |
| NQ_2021_1min_databento.csv | 340,313 | 2021-01-03 23:00 UTC | 2021-12-17 14:29 UTC |
| NQ_2022_1min_databento.csv | 341,080 | 2022-01-02 23:00 UTC | 2022-12-16 14:29 UTC |
| NQ_1min_databento.csv (2023+2024 combined) | 684,432 | 2023-01-02 23:00 UTC | 2024-12-19 23:59 UTC |

Mean per-year: ES≈340k, NQ≈340k (the two roots have very similar 1-min density — the prior estimate of "318k ES / 364k NQ" was a divisional artifact derived from combined-CSV row totals and is superseded). **Post-run row counts must be verified against the vendor-returned count, not these estimates.**

### 1.1 Intrinsic Dec 21-31 calendar-edge gap

The sibling `download_historical_years` method ([databento_downloader.py:240-246](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/src/python/data_collection/databento_downloader.py)) defines the December contract window as `('Z', '09-15', '12-20')`. Each calendar year therefore ends ~Dec 16-20 in the substrate, **not** Dec 31. This is empirically confirmed in the table above (ES_2022 last bar = 2022-12-16; combined ES_2023+2024 last = 2024-12-19).

This gap:
- **Applies symmetrically** to the existing 2020-2024 substrate and the new Cell I 2015-2019 / NQ 2025 backfill — Cell I does **not** introduce it.
- Is **intrinsic to the contract-month tuple**, not a vendor coverage limit. The Z (December) contract expires on the third Friday of December (per [CME ES product spec](https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.contractSpecs.html) — last trade day on the second business day before the third Friday); after expiry there is no equity-index front-month with positive volume until the next H (March) contract.
- **Is closeable** via a Z-window extension to `'12-31'` IF the user chooses to capture the brief no-front-month tail (sparse, non-trading-session bars). Tracked as new follow-up `P1-DATABENTO-DEC21-EXTENSION`.

The H050 walk-forward train and test windows therefore both terminate at ~Dec 20 of the closing year by substrate construction. design.md §2's nominal `2025-12-31` test-end is bounded above by this empirical reality. No change to the pre-reg envelope is implied; the operational truncation point is documented here for auditability.

## 2. Critical finding — existing CLI cannot reach Databento

### 2.1 Empirical evidence

The dry-run captured at Appendix A of this runbook shows that `python scripts/ingest.py --dataset vendor_legacy_1min --start 2015-01-01 --end 2019-12-31 --dry-run` accepts the arguments without error but reports it would process **only the existing 9 sibling-repo CSVs** (ES 2020-2025 + NQ 2020-2024). The `--start` and `--end` flags are accepted for CLI parity but do not parameterize the fetch — see [src/skie_ninja/data/ingest/vendor_legacy_1min.py:113](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) `del start, end  # unused; kept for IngestJob protocol parity`. Source-file selection is hard-coded in `_CANONICAL_SOURCES` ([src/skie_ninja/data/ingest/vendor_legacy_1min.py:71-81](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py)).

### 2.2 Implication

The existing SKIE-Universe `vendor_legacy_1min` ingest is a **CSV-copy adapter**, not a Databento API client. The Databento credentials and SDK live in the sibling repo at [C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\src\python\data_collection\databento_downloader.py](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/src/python/data_collection/databento_downloader.py) (verified 2026-04-24). Paid API access requires running that downloader with `DATABENTO_API_KEY` from [C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\config\api_keys.py](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/config/api_keys.py).

### 2.3 Two-stage execution path

Cell I therefore requires **two stages**:

- **Stage A (sibling repo, paid)**: pull ES 2015-2019, NQ 2015-2019, NQ 2025 via sibling `databento_downloader.py`, landing CSVs in `C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\data\raw\market\`.
- **Stage B (SKIE-Universe, no API call)**: extend `_CANONICAL_SOURCES` in [src/skie_ninja/data/ingest/vendor_legacy_1min.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) with the new files, re-run `python scripts/ingest.py --dataset vendor_legacy_1min`, then re-run the roll-adjusted derivative.

Stage A is the paid step. Stage B is local-only and idempotent (SHA256-keyed).

### 2.4 Out-of-scope alternative considered and rejected

A SKIE-Universe-direct Databento ingest module (new `IngestJob` adapter wrapping `databento.Historical`) would eliminate the cross-repo dependency. It is out of scope for this preparation deliverable — the user's task explicitly forbids modifying [src/](../../src/) source. Tracked as a new follow-up `P1-H050-DATABENTO-DIRECT-INGEST` if the user later prefers to consolidate the pull inside SKIE-Universe.

## 3. Pre-execution checklist

Before Stage A, verify each item below. A single missing item should abort the run.

- [ ] **Sibling repo Databento client present**: `python -c "import databento; print(databento.__version__)"` succeeds in the sibling repo's venv.
- [ ] **API key resolves**: `python -c "import sys; sys.path.insert(0, r'C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\config'); from api_keys import DATABENTO_API_KEY; print(bool(DATABENTO_API_KEY))"` prints `True`.
- [ ] **Account credit balance**: log into [databento.com](https://databento.com) account dashboard; confirm available credits exceed the cost-estimate ceiling reported in §5 below. Per [docs/research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md](memo_h050-cell-i-cost-estimate_2026-04-24.md) the empirically-anchored estimate is in the low-USD-tens range; verify against the user's actual billing.
- [ ] **Disk space — sibling repo raw CSV landing**: ~290 MB free at `C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\data\raw\market\`. Verified 2026-04-24: `C:` drive has 396 GB free.
- [ ] **Disk space — SKIE-Universe shared raw cache**: ~290 MB free at `C:\Users\skoir\datasets\vendor_skie_ninja_legacy\raw_1min\` (will hold the same CSVs after Stage B copy). Same drive as above; satisfied.
- [ ] **Disk space — SKIE-Universe processed parquet**: ~150 MB free at `data/processed/vendor_legacy_1min/` (parquet compresses ~2x vs CSV). Same drive; satisfied.
- [ ] **Disk space — roll-adjusted parquet**: ~150 MB at `data/processed/vendor_legacy_1min_roll_adjusted/`. Same drive; satisfied.
- [ ] **Worktree-local processed parquet exists or is acceptable to re-materialize**: dry-run captured 2026-04-24 in this runbook §A.2 shows `data/processed/vendor_legacy_1min/` is **absent** in this worktree. The roll-adjusted job FAIL-FASTs without it. Plan to re-run `vendor_legacy_1min` after Stage A and before the roll-adjusted derivative.
- [ ] **Cost-estimate ceiling acknowledged**: see §5 + the cost-estimate memo. The user authorizes a ceiling figure (e.g., $30 USD) that the runbook will not exceed without re-authorization.
- [ ] **No conflicting Cycle 6 in-progress jobs**: check that no other agent is currently writing to `data/processed/_provenance/`, `data/processed/vendor_legacy_1min*/`, or `logs/reproducibility/`.
- [ ] **Git working tree clean or stashed**: backfill changes to `_CANONICAL_SOURCES` and `data_requirements.md` should land in a single, reviewable commit; conflicting uncommitted changes risk accidental coupling.

## 4. Symbol convention

Sibling `databento_downloader.py` uses raw contract codes (e.g., `ESH3` for ES March 2023). The `download_historical_years` method (lines 223-268) iterates over the four CME equity-index contract months `H, M, U, Z` (March/June/September/December) per year. **Single-digit-year suffix** mapping for 2015-2019 and 2025:

| Year | H (Mar) | M (Jun) | U (Sep) | Z (Dec) |
|---|---|---|---|---|
| 2015 | ESH5 / NQH5 | ESM5 / NQM5 | ESU5 / NQU5 | ESZ5 / NQZ5 |
| 2016 | ESH6 / NQH6 | ESM6 / NQM6 | ESU6 / NQU6 | ESZ6 / NQZ6 |
| 2017 | ESH7 / NQH7 | ESM7 / NQM7 | ESU7 / NQU7 | ESZ7 / NQZ7 |
| 2018 | ESH8 / NQH8 | ESM8 / NQM8 | ESU8 / NQU8 | ESZ8 / NQZ8 |
| 2019 | ESH9 / NQH9 | ESM9 / NQM9 | ESU9 / NQU9 | ESZ9 / NQZ9 |
| 2025 | (ES has) | (ES has) | (ES has) | (ES has) — only **NQ** missing |

Single-digit-year-suffix collision risk: ESH5 is ambiguous between 2015 and 2025 in the bare contract code. The two relevant sibling-repo code paths use **different windowing schemes**, both collision-safe but for distinct reasons:

- `download_historical_years` (the actual Stage A pull, [databento_downloader.py:223-268](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/src/python/data_collection/databento_downloader.py)) passes **contract-month-bounded windows** — for ESH5 in year=2015 the window is `2015-01-01 → 2015-03-17` (the H contract's `('H', '01-01', '03-17')` tuple). Collision with the 2025-active ESH5 is impossible because the requested 2015-Q1 window does not overlap any 2025-active contract.
- `estimate_cost_for_years` ([databento_downloader.py:270-293](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/src/python/data_collection/databento_downloader.py)) uses **full-year windows** `f"{year}-01-01" → f"{year}-12-31"`. In practice a 2015-active contract cannot deliver 2025 bars (and vice versa), so the cost estimate is also collision-safe; the divergent windowing here is purely an API ergonomics choice (cost queries are cheap).

Operational mitigation: the §6.3 per-CSV first/last `ts_event` year check is the gate. Confirm the timestamp envelope falls in the requested calendar year with no cross-year leak before merging.

## 5. Cost estimate (binding rule = live API call)

Per [memo_h050-cell-i-cost-estimate_2026-04-24.md](memo_h050-cell-i-cost-estimate_2026-04-24.md):

- **Binding figure**: the **live `client.metadata.get_cost(...)` total** from Stage A step §6.1 is the *only* authorization-binding cost. It is computed per-tuple `(dataset, symbols, schema, start, end)` and prints with no API charge.
- **Indicative anchor (NOT binding)**: the sibling-repo `databento_downloader.py:363` `already_spent: float = 3.17` is a hard-coded function default — a developer-recorded prior expense from 2023-2024 ES+NQ pulls, **not** a billing record retrieved from the Databento account dashboard. Do not treat it as a cost-prediction anchor for this run; treat it only as evidence that "11 symbol-years of OHLCV-1m" is in the low-USD-tens order of magnitude.
- **Authorization ceiling (user-chosen budget)**: recommended **$30 USD**. This is a user-set cap, not a vendor-derived multiple. The operational rule: after Stage A §6.1 prints the live `metadata.get_cost` total `T_live`, abort if `T_live > $30 USD`; otherwise the user authorizes spending up to **2 × T_live** (a recommended floor that absorbs any vendor revisions or rounding between the cost-estimate call and the actual download).

Pricing unit per [Databento pricing page](https://databento.com/pricing) (fetched 2026-04-24): "billed for every outbound byte of data at the moment it is sent out on our network" — per-GB of uncompressed binary, not per-row. The `metadata.get_cost` API returns a figure formatted as USD by the sibling downloader; the unit interpretation residual risk is documented in §12 item 1.

## 6. Stage A — paid Databento pull (user authorizes and runs)

Run from the **sibling repo** Python environment (where `databento` SDK is installed and `api_keys.py` is reachable on `sys.path`). The user must authorize each `get_cost`/download pair.

### 6.1 Cost estimate (no charge yet)

```bash
cd "C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja"
python -c "
import sys
sys.path.insert(0, r'src/python/data_collection')
sys.path.insert(0, r'config')
from databento_downloader import DatabentoDownloader
d = DatabentoDownloader()
total = 0.0
years_es = [2015, 2016, 2017, 2018, 2019]
years_nq = [2015, 2016, 2017, 2018, 2019, 2025]
for instrument, years in (('ES', years_es), ('NQ', years_nq)):
    cost = d.estimate_cost_for_years(instrument, years, 'ohlcv-1m')
    print(f'{instrument} {years}: \${cost:.4f}')
    total += cost
print(f'TOTAL CELL I COST ESTIMATE: \${total:.4f}')
"
```

User reviews the printed total `T_live`:
1. If `T_live > $30 USD` (the §5 ceiling), abort and re-authorize.
2. Otherwise, record `T_live` as the **binding cost record** for this Cell I run (per follow-up `P1-H050-CELL-I-LIVE-COST-CAPTURE`).
3. The user authorizes spending up to **2 × T_live** in §6.2 to absorb any vendor revisions between the estimate call and the actual download.

### 6.2 Per-symbol-year pulls (paid)

```bash
cd "C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja"
python -c "
import sys
sys.path.insert(0, r'src/python/data_collection')
sys.path.insert(0, r'config')
from databento_downloader import DatabentoDownloader
d = DatabentoDownloader()

# ES 2015-2019: one CSV per year, per the existing _CANONICAL_SOURCES naming
for year in [2015, 2016, 2017, 2018, 2019]:
    df = d.download_historical_years('ES', [year], 'ohlcv-1m')
    if len(df) > 0:
        out = d.data_dir / f'ES_{year}_1min_databento.csv'
        df.to_csv(out)
        print(f'WROTE {out} rows={len(df)}')

# NQ 2015-2019, 2025
for year in [2015, 2016, 2017, 2018, 2019, 2025]:
    df = d.download_historical_years('NQ', [year], 'ohlcv-1m')
    if len(df) > 0:
        out = d.data_dir / f'NQ_{year}_1min_databento.csv'
        df.to_csv(out)
        print(f'WROTE {out} rows={len(df)}')
"
```

Expected post-run state: 11 new CSV files at `C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\data\raw\market\` matching the table in §1.

### 6.3 Stage A verification

```bash
cd "C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\data\raw\market"
ls -la ES_201[5-9]_1min_databento.csv NQ_201[5-9]_1min_databento.csv NQ_2025_1min_databento.csv
```

11 files expected. If any are missing, the corresponding `download_historical_years` call returned an empty DataFrame; check the sibling-repo log for HTTP errors before re-running that single year (idempotent — Databento bills only on actual byte delivery).

### 6.4 NQ 2025 vs ES 2025 currency check (post-pull)

The existing ES 2025 CSV has mtime 2024-12-04 (last bar 2025-12-03 — see §1 table). A fresh NQ 2025 pull on the Stage A date will deliver bars through approximately the current Z (December) contract's last trade day (≈Dec 20 of the calendar year), which is **further forward** than the existing ES 2025. After Stage A, verify symmetric coverage by inspecting first/last `ts_event` per CSV:

```bash
cd "C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\inspiring-franklin-13a1f1"
uv run python -c "
import polars as pl
from pathlib import Path
src = Path(r'C:/Users/skoir/datasets/vendor_skie_ninja_legacy/raw_1min')
for f in ['ES_2025_1min_databento.csv', 'NQ_2025_1min_databento.csv']:
    p = src / f
    if not p.exists():
        print(f'{f}: MISSING'); continue
    df = pl.scan_csv(p).select(pl.col('ts_event').str.to_datetime(time_unit='us', time_zone='UTC')).collect()
    print(f'{f}: rows={df.height:,} first={df[\"ts_event\"].min()} last={df[\"ts_event\"].max()}')
"
```

Operational rule: if `last_ts(NQ 2025) <= last_ts(ES 2025)`, the NQ 2025 pull silently truncated. Re-fetch with `metadata.get_cost` re-checked. **Recommended**: opportunistically refresh ES 2025 in the same Stage A by adding `ES_2025_1min_databento.csv` to the sibling-repo download script's pull list — at incremental cost (only the new bars 2025-12-04 onward are billed), this restores ES/NQ end-date symmetry.

## 7. Stage B — SKIE-Universe import (local, no API call)

### 7.1 Inject Cell I sources via YAML manifest (preferred)

Stage B uses the `--sources-yaml` flag wired through [scripts/ingest.py](../../scripts/ingest.py), which accepts a YAML manifest and loads the entries via [load_sources_yaml](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) — appended to `_CANONICAL_SOURCES` at runtime. **No source-file edit is required.**

Create the YAML manifest under [config/](../../config/) (suggested filename `cell_i_sources.yaml`):

```yaml
sources:
  - {symbol: ES, coverage: backfill_2015, filename: ES_2015_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2016, filename: ES_2016_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2017, filename: ES_2017_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2018, filename: ES_2018_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2019, filename: ES_2019_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2015, filename: NQ_2015_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2016, filename: NQ_2016_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2017, filename: NQ_2017_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2018, filename: NQ_2018_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2019, filename: NQ_2019_1min_databento.csv}
  - {symbol: NQ, coverage: forward_2025, filename: NQ_2025_1min_databento.csv}
```

Schema is enforced by [load_sources_yaml](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py): `sources` must be a list of mappings with required keys `{symbol, coverage, filename}`; `symbol ∈ {ES, NQ, MES, MNQ}`; `filename` must end in `.csv` and be unique within the YAML; collisions with `_CANONICAL_SOURCES` are dropped (canonical wins). Regression test coverage: [tests/unit/test_ingest_vendor_legacy_sources.py](../../tests/unit/test_ingest_vendor_legacy_sources.py) (16 cases including the Cell-I 11-entry case).

**Fallback only** — manual `_CANONICAL_SOURCES` edit: if the YAML path is unavailable for any reason, the edit at [src/skie_ninja/data/ingest/vendor_legacy_1min.py:71-81](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) inserting the same 11 `_SourceFile` lines is the manual equivalent. Avoid this path; prefer the YAML.

### 7.2 Re-run raw 1-min ingest with YAML manifest

```bash
cd "C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\inspiring-franklin-13a1f1"
uv run python scripts/ingest.py \
    --dataset vendor_legacy_1min \
    --start 2015-01-01 --end 2025-12-31 \
    --sources-yaml config/cell_i_sources.yaml
```

Existing 9 CSVs are SHA256-skipped (idempotent); 11 new CSVs are copied + parsed + validated + partitioned + provenance-emitted. Expected output:

- `Loaded 11 extra source(s) from config/cell_i_sources.yaml; total canonical sources=20.`
- `Fetch summary: 11 copied, 9 unchanged, 20 total canonical sources`

### 7.3 Re-run roll-adjusted derivative

```bash
uv run python scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2025-12-31 --force
```

`--force` is required because the roll history extends with 5 new years on each symbol; the derivative SHA changes for **every** historical bar (per [memo_option-b-data-coverage_2026-04-24.md](memo_option-b-data-coverage_2026-04-24.md) §2.3 — adjustment factors are full-sample). Existing per-partition checksums in [research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) §"Per-partition" are **all invalidated** by this run.

## 8. Post-ingest verification

### 8.1 Partition presence

```bash
cd "C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\inspiring-franklin-13a1f1"
ls data/processed/vendor_legacy_1min/symbol=ES/year=*/part-0000.parquet | wc -l
ls data/processed/vendor_legacy_1min/symbol=NQ/year=*/part-0000.parquet | wc -l
ls data/processed/vendor_legacy_1min_roll_adjusted/symbol=ES/year=*/part-0000.parquet | wc -l
ls data/processed/vendor_legacy_1min_roll_adjusted/symbol=NQ/year=*/part-0000.parquet | wc -l
```

Expected: ES=11 (2015-2025 inclusive), NQ=11 (2015-2025 inclusive) for both raw and roll-adjusted.

### 8.2 Row-count sanity check

```bash
uv run python -c "
import polars as pl
from pathlib import Path
root = Path('data/processed/vendor_legacy_1min_roll_adjusted')
for sym in ['ES', 'NQ']:
    for p in sorted(root.glob(f'symbol={sym}/year=*/part-0000.parquet')):
        n = pl.read_parquet(p).height
        print(f'{p.parent.parent.name}/{p.parent.name}: rows={n:>8,}')
"
```

Expected per-year row counts (full-day 1-min bars including ETH; the substrate carries ETH+RTH and the H050 RTH filter applies downstream):

- ES per full year (2015-2019): ~340k (matches the empirical 2020-2024 baseline; mean 340k, range 338k-341k)
- NQ per full year (2015-2019): ~340k (matches the empirical 2020-2024 baseline; mean 340k, range 337k-341k)
- ES 2025 (truncated to ~2025-12-03 unless refreshed per §6.4): ~326k
- NQ 2025 (truncated to ~2025-12-20 by Z-window): ~360k

Discrepancies > 5% from the empirical baseline (`|actual - 340,000| / 340,000 > 0.05` for full-year ES/NQ partitions) trigger investigation: calendar-edge errors, holiday miscounting, or vendor revisions.

### 8.3 Schema check

```bash
uv run python -c "
import pyarrow.parquet as pq
from pathlib import Path
for p in Path('data/processed/vendor_legacy_1min_roll_adjusted').rglob('part-0000.parquet'):
    schema = pq.read_schema(p)
    cols = [f.name for f in schema]
    expected = {'ts_event','open','high','low','close','volume','symbol','front_contract_symbol','adjustment_factor','unadjusted_close','roll_flag'}
    missing = expected - set(cols)
    if missing:
        print(f'MISSING in {p}: {missing}')
        break
else:
    print('All partitions schema-conformant.')
"
```

### 8.4 Frame-level SHA256 freeze

```bash
uv run python -c "
import polars as pl
from skie_ninja.utils.hashing import frame_sha256
combined = pl.scan_parquet('data/processed/vendor_legacy_1min_roll_adjusted/**/*.parquet').sort(['symbol','ts_event']).collect()
print(f'Combined rows: {combined.height:,}')
print(f'Combined SHA256: {frame_sha256(combined, sort_cols=[\"symbol\",\"ts_event\"])}')
for sym in ['ES','NQ']:
    for yr in range(2015, 2026):
        try:
            f = pl.read_parquet(f'data/processed/vendor_legacy_1min_roll_adjusted/symbol={sym}/year={yr}/part-0000.parquet')
            print(f'{sym} {yr} rows={f.height:>8,} sha={frame_sha256(f, sort_cols=[\"symbol\",\"ts_event\"])}')
        except FileNotFoundError:
            pass
"
```

Capture this output. The Combined SHA256 + the 22 per-partition SHA256s replace the current frozen table in [data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) §"Per-partition".

### 8.5 RTH bar density check

H050 design.md §2 specifies **RTH only** (08:30–15:15 CT, per [config/instruments.yaml](../../config/instruments.yaml) `session_rth`). RTH = 6 hr 45 min × 60 = 405 min/day. Approx 252 trading days/year × 405 = 102,060 RTH bars/year — but the substrate carries ETH+RTH, with H050 RTH filter applied downstream in the feature factory. Sanity gate is the *full-day* row count (~340k/yr for ES and NQ per the empirical baseline in §8.2); RTH-only sub-counts emerge after the H050 feature factory's session filter.

### 8.6 Calendar-edge gate — expected vs actual unique trading dates

For each `(symbol, year)` partition, compute the expected number of CME equity-index futures trading dates in the calendar year (or year-truncated-to-Z-window per §1.1) and compare against the actual count of unique dates in `ts_event`. Flag any partition where `|expected − actual| > 1 day`.

```bash
cd "C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\inspiring-franklin-13a1f1"
uv run python -c "
import polars as pl
import pandas_market_calendars as mcal
from datetime import date
from pathlib import Path

cme = mcal.get_calendar('CME_Equity')
nyse = mcal.get_calendar('NYSE')
root = Path('data/processed/vendor_legacy_1min_roll_adjusted')
year_z_end = '12-20'  # Z (December) contract last-trade window per databento_downloader.py:245

for sym in ['ES', 'NQ']:
    for p in sorted(root.glob(f'symbol={sym}/year=*/part-0000.parquet')):
        df = pl.read_parquet(p, columns=['ts_event'])
        yr = int(p.parent.name.split('=')[1])
        end_date = f'{yr}-{year_z_end}'
        cme_days = cme.valid_days(start_date=f'{yr}-01-01', end_date=end_date)
        nyse_days = nyse.valid_days(start_date=f'{yr}-01-01', end_date=end_date)
        actual = df.select(pl.col('ts_event').dt.date()).unique().height
        cme_n = len(cme_days)
        nyse_n = len(nyse_days)
        expected = cme_n
        flag = 'OK' if abs(actual - expected) <= 1 else 'FLAG'
        print(f'{sym} {yr}: cme_days={cme_n} nyse_days={nyse_n} actual={actual} delta={actual-expected} [{flag}]')
"
```

Calendar source: [pandas_market_calendars](https://pandas-market-calendars.readthedocs.io/en/latest/usage.html) `valid_days()` for `CME_Equity` and `NYSE` calendars (per the WebFetch'd usage docs; primary source for `CME_Equity` calendar definition: [pandas_market_calendars source](https://github.com/rsheftel/pandas_market_calendars)). For environments without `pandas_market_calendars` available, [src/skie_ninja/utils/clock.py](../../src/skie_ninja/utils/clock.py) provides a CME session calendar that can be substituted.

**Specific dates that this gate must catch (non-exhaustive):**

- **2025-01-09 — Carter National Day of Mourning.** NYSE was closed in observance of President Carter's state funeral; CME equity-index futures observed an **early close at 13:15 CT** (per CME Group Notice; cross-check: [Wikipedia state-funeral entry](https://en.wikipedia.org/wiki/Death_and_state_funeral_of_Jimmy_Carter) confirms the National Day of Mourning declaration). The CME equity-index date is therefore present in the substrate but with a partial-session row count. **MUST NOT be silently dropped** — `pandas_market_calendars` `CME_Equity.valid_days('2025-01-09', '2025-01-09')` should return one entry. Verify with `pandas_market_calendars` `early_closes()` schedule.
- **2018-12-05 — Bush funeral.** Same pattern: NYSE closed; CME equity-index futures partial session.
- **Day-after-Thanksgiving** (every year): NYSE early close 13:00 ET; CME equity-index early close 12:15 CT.
- **Christmas Eve (Dec 24)** when on a weekday and not a Thursday-then-Christmas double-up: NYSE early close 13:00 ET; CME equity-index early close 12:15 CT.
- **Good Friday**: NYSE closed; CME equity-index closed.
- **CME Equity Holiday Calendar (canonical reference)**: [www.cmegroup.com/tools-information/holiday-calendar](https://www.cmegroup.com/tools-information/holiday-calendar.html) — annual notice with dated table of full closures and early closes.

The `pandas_market_calendars` calendar definitions encode these closures and partial sessions; relying on its `valid_days()` and `early_closes()` is the binding mechanism here. Discrepancies between actual and expected must be diagnosed before the run is treated as evidence-bar valid.

## 9. Manifest update

After §8 succeeds, edit [research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md):

1. Move the existing "Per-partition" SHA256 table to a new section "Pre-Cell-I checksums (superseded 2026-04-XX)" — preserve them for audit but mark superseded.
2. Replace the active "Per-partition" table with the §8.4 outputs.
3. Update the "Combined SHA256" to the §8.4 output.
4. Update §Coverage with new ES/NQ date ranges and total row counts.
5. Add a row in §Source dataset noting the Cell I backfill date and the resolution-memo link.
6. Append a CSV-tier checksum table for the 11 new CSVs (compute via `file_sha256` from the ingest provenance JSON written by step §7.2).

A "Pending Cell I backfill" placeholder section is prepared in this commit; see [data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) §"Pending Cell I backfill".

## 10. Rollback procedure

If Stage B partway-fails (e.g., parse error on a backfilled CSV, schema mismatch, OHLC violation):

1. Identify the staged-but-unpromoted partition under `data/processed/_staging/vendor_legacy_1min/`. The two-phase commit in [src/skie_ninja/data/ingest/vendor_legacy_1min.py:283-326](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) auto-cleans staging on failure; verify it's empty.
2. If the failure is in the roll-adjusted derivative, the prior good `vendor_legacy_1min_roll_adjusted/` partitions remain in place (the derivative has its own two-phase commit + pre-promotion rollback at [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py:507-573](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py)). Delete only the affected `_staging` subtree.
3. If the user wants to **completely** roll back to the pre-Cell-I substrate: `git restore src/skie_ninja/data/ingest/vendor_legacy_1min.py` (reverts `_CANONICAL_SOURCES`); delete `data/processed/vendor_legacy_1min/symbol={ES,NQ}/year={2015,2016,2017,2018,2019}/`; delete `data/processed/vendor_legacy_1min/symbol=NQ/year=2025/`; re-run the roll-adjusted derivative with `--force` to restore the old combined SHA.
4. Stage A (paid) is **never automatically rolled back** because the data has already been billed — the CSVs remain in the sibling repo as a dormant, paid asset.

## 11. Audit-remediate-loop discipline

- **Round 1 (this document)**: producer-agent self-audit applied inline. Unresolved items flagged below.
- **Round 2 (deferred to main thread)**: per the producer-agent task spec, isolated-subagent verification (parallel `quant-auditor` + `literature-check` + `reproducibility-verifier`) runs from main thread, NOT from the producer agent. The producer agent does not claim "Round 2 accept."
- **Audit trail**: [docs/audits/audit_trail_2026-04-24_h050-cell-i-runbook.md](../audits/audit_trail_2026-04-24_h050-cell-i-runbook.md).

## 12. Self-audit residual risk (Round 1)

Items the producer agent flagged but could not close inline:

1. **`metadata.get_cost` unit not directly verified from public Databento docs.** WebFetch returned navigation-only excerpts on 2026-04-24 for [databento.com/docs/api-reference-historical/metadata/get-cost](https://databento.com/docs/api-reference-historical/metadata/get-cost) and [databento.com/docs/standards-and-conventions/symbology](https://databento.com/docs/standards-and-conventions/symbology). The unit-of-cost claim ("returns USD pre-computed for the tuple") is anchored to the sibling-repo `databento_downloader.py` lines 41-60 docstring, not to a primary Databento doc. **User must verify** the §6.1 cost estimate output is denominated in USD before authorizing §6.2.
2. **NQ 2025 vendor coverage cutoff.** Whether Databento's NQ 2025 archive currently extends through 2025-12-03 (matching ES 2025) or further is not verified. The §1 estimate uses the ES 2025 cutoff as a proxy. Stage A `metadata.get_cost` output and the `download_historical_years` return-row count will reveal the actual coverage — read both before concluding the run.
3. **Pre-2017 reconstruction provenance shift.** Per [memo_option-b-data-coverage_2026-04-24.md](memo_option-b-data-coverage_2026-04-24.md) §3.1, native MDP 3.0 capture begins 2017-05-21; pre-2017 bars are reconstructed from CME legacy feeds. The `ohlcv-1m` schema is materially equivalent across the boundary, but the reconstruction provenance differs from the existing 2020+ substrate. The Stage B provenance JSON should record this shift explicitly under a new key (e.g., `reconstruction_window: "2015-01-01 to 2017-05-20"`) — currently the existing `vendor_legacy_1min` provenance schema does not have this field. Tracked as new follow-up `P1-VENDOR-LEGACY-RECONSTRUCTION-PROVENANCE`.
4. **Single-digit-year contract-code collision.** §4 above asserts Databento disambiguates `ESH5` between 2015 and 2025 by the date-range bound. This was inferred from the sibling downloader's `download_historical_years` per-year-bounded `start`/`end` calls — not directly verified against Databento symbology docs (WebFetch limitation per item 1). Stage A verification step §6.3 (per-CSV first/last `ts_event` falls in requested year) is the operational gate against undetected collision.
5. **Roll-adjusted SHA recomputation bound.** The full-sample-rescaling property (Cycle 1 `vendor_legacy_1min_roll_adjusted.py` v0.2.0 module docstring §"Point-in-time caveat") means the post-Cell-I combined SHA is **not** related by a simple delta to the pre-Cell-I `d2c4aa4e70c6badcb294d9bec64ee3fc5093ba9085082495f5031743943b9a2d`. This is expected; the data_requirements.md update in §9 freezes the new value as binding for future runs. Auditors reviewing reproducibility logs across the Cell-I cutover should expect a complete SHA discontinuity, not preservation.

## Appendix A — Dry-run captures (2026-04-24, 2026-04-25)

### A.1 `vendor_legacy_1min` dry-run for the 2015-2019 backfill window

Command executed verbatim:

```bash
cd "C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\inspiring-franklin-13a1f1"
uv run python scripts/ingest.py --dataset vendor_legacy_1min --start 2015-01-01 --end 2019-12-31 --dry-run
```

Output (structured JSON log, key lines):

```
"Ingest started: dataset=vendor_legacy_1min, start=2015-01-01, end=2019-12-31, dry_run=True, force=False"
"Unchanged (SHA match): ES_2020_1min_databento.csv"
"Unchanged (SHA match): ES_2021_1min_databento.csv"
"Unchanged (SHA match): ES_2022_1min_databento.csv"
"Unchanged (SHA match): ES_1min_databento.csv"
"Unchanged (SHA match): ES_2025_1min_databento.csv"
"Unchanged (SHA match): NQ_2020_1min_databento.csv"
"Unchanged (SHA match): NQ_2021_1min_databento.csv"
"Unchanged (SHA match): NQ_2022_1min_databento.csv"
"Unchanged (SHA match): NQ_1min_databento.csv"
"Fetch summary: 0 copied, 9 unchanged, 9 total canonical sources"
"Fetch returned 9 path(s)."
"[dry-run] Would process 9 file(s):"
"[dry-run]   C:\\Users\\skoir\\datasets\\vendor_skie_ninja_legacy\\raw_1min\\ES_2020_1min_databento.csv"
... (8 more existing files) ...
"[dry-run] Stopping before parse."
```

Conclusion (§2 above): the existing CLI accepts the 2015-2019 arguments without error but processes only the existing 9 sibling-repo CSVs. The `--start` / `--end` flags do not parameterize the fetch.

### A.2 `vendor_legacy_1min_roll_adjusted` dry-run for the full pre-reg envelope

Command executed verbatim:

```bash
uv run python scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2025-12-31 --dry-run
```

Output (key lines):

```
"Ingest started: dataset=vendor_legacy_1min_roll_adjusted, start=2015-01-01, end=2025-12-31, dry_run=True, force=False"
"Fetching raw data for vendor_legacy_1min_roll_adjusted [2015-01-01, 2025-12-31]."
Traceback (most recent call last):
  File ".../scripts/ingest.py", line 252, in run
    raw_paths = job.fetch(start, end, ctx)
  File ".../vendor_legacy_1min_roll_adjusted.py", line 304, in fetch
    raise FileNotFoundError(
FileNotFoundError: Source dataset root not found: data/processed/vendor_legacy_1min.
```

Conclusion: this worktree has no `data/processed/vendor_legacy_1min/` partitions — they were materialized in a different worktree (per [docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](../audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md) the prior run was 2026-04-23 17:29 CT). Stage B §7.2 must run before §7.3 even if no Cell I backfill happens, on this worktree.

### A.3 `vendor_legacy_1min` dry-run with `--sources-yaml` flag (Round-2, 2026-04-25)

After implementing the F-2-5 fix (`--sources-yaml` CLI flag + injectable constructor), the same backfill window was re-run with the YAML manifest:

```bash
cd "C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\inspiring-franklin-13a1f1"
cat > /tmp/cell_i_sources.yaml << 'EOF'
sources:
  - {symbol: ES, coverage: backfill_2015, filename: ES_2015_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2016, filename: ES_2016_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2017, filename: ES_2017_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2018, filename: ES_2018_1min_databento.csv}
  - {symbol: ES, coverage: backfill_2019, filename: ES_2019_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2015, filename: NQ_2015_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2016, filename: NQ_2016_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2017, filename: NQ_2017_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2018, filename: NQ_2018_1min_databento.csv}
  - {symbol: NQ, coverage: backfill_2019, filename: NQ_2019_1min_databento.csv}
  - {symbol: NQ, coverage: forward_2025, filename: NQ_2025_1min_databento.csv}
EOF

uv run python scripts/ingest.py --dataset vendor_legacy_1min \
    --start 2015-01-01 --end 2025-12-31 --dry-run \
    --sources-yaml /tmp/cell_i_sources.yaml
```

Output (key lines):

```
"Loaded 11 extra source(s) from /tmp/cell_i_sources.yaml; total canonical sources=20."
"Unchanged (SHA match): ES_2020_1min_databento.csv"
... (8 more existing files; 9 unchanged) ...
"Source missing: ...\\ES_2015_1min_databento.csv — symbol=ES coverage=backfill_2015 (skipping)"
... (10 more missing files; 11 missing in total per-spec — sibling repo has not yet pulled them) ...
"Fetch summary: 0 copied, 9 unchanged, 20 total canonical sources"
"[dry-run] Would process 9 file(s):"
... (9 existing CSVs listed) ...
"[dry-run] Stopping before parse."
```

Conclusion: the `--sources-yaml` path is wired correctly. The 11 Cell-I entries are loaded into the canonical list (from 9 → 20), and the `Source missing` errors confirm that those files are **expected** to be pulled by Stage A before this Stage B step succeeds. After Stage A completes, re-running this command without `--dry-run` will produce `Fetch summary: 11 copied, 9 unchanged, 20 total canonical sources`.

## Appendix B — Go / no-go command sequence

Once the user authorizes the paid run, this is the exact sequence:

```bash
# === STAGE A — sibling repo (paid) ===
cd "C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja"

# 1. Cost estimate (no charge)
python -c "
import sys; sys.path.insert(0, r'src/python/data_collection'); sys.path.insert(0, r'config')
from databento_downloader import DatabentoDownloader
d = DatabentoDownloader()
total = 0.0
for inst, yrs in (('ES', [2015,2016,2017,2018,2019]), ('NQ', [2015,2016,2017,2018,2019,2025])):
    c = d.estimate_cost_for_years(inst, yrs, 'ohlcv-1m'); total += c
    print(f'{inst} {yrs}: \${c:.4f}')
print(f'TOTAL: \${total:.4f}')
"
# >>> ABORT IF TOTAL > $30 USD <<<

# 2. Paid pulls
python -c "
import sys; sys.path.insert(0, r'src/python/data_collection'); sys.path.insert(0, r'config')
from databento_downloader import DatabentoDownloader
d = DatabentoDownloader()
for year in [2015,2016,2017,2018,2019]:
    df = d.download_historical_years('ES', [year], 'ohlcv-1m')
    if len(df): df.to_csv(d.data_dir / f'ES_{year}_1min_databento.csv'); print(f'ES {year}: {len(df)} rows')
for year in [2015,2016,2017,2018,2019,2025]:
    df = d.download_historical_years('NQ', [year], 'ohlcv-1m')
    if len(df): df.to_csv(d.data_dir / f'NQ_{year}_1min_databento.csv'); print(f'NQ {year}: {len(df)} rows')
"

# 3. Verify 11 new CSVs present
ls data/raw/market/ES_201[5-9]_1min_databento.csv data/raw/market/NQ_201[5-9]_1min_databento.csv data/raw/market/NQ_2025_1min_databento.csv

# === STAGE B — SKIE-Universe (no API call) ===
cd "C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\inspiring-franklin-13a1f1"

# 4. Create config/cell_i_sources.yaml per §7.1 (YAML manifest, not source edit)

# 5. Re-run raw 1-min ingest with --sources-yaml flag
uv run python scripts/ingest.py --dataset vendor_legacy_1min \
    --start 2015-01-01 --end 2025-12-31 \
    --sources-yaml config/cell_i_sources.yaml

# 6. Re-run roll-adjusted derivative (--force; full-sample rescaling)
uv run python scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2025-12-31 --force

# 7. Verification (per §8)
ls data/processed/vendor_legacy_1min_roll_adjusted/symbol=ES/year=*/part-0000.parquet | wc -l   # expect 11
ls data/processed/vendor_legacy_1min_roll_adjusted/symbol=NQ/year=*/part-0000.parquet | wc -l   # expect 11
uv run python -c "import polars as pl; from skie_ninja.utils.hashing import frame_sha256; c=pl.scan_parquet('data/processed/vendor_legacy_1min_roll_adjusted/**/*.parquet').sort(['symbol','ts_event']).collect(); print(c.height, frame_sha256(c, sort_cols=['symbol','ts_event']))"

# 8. Manifest update (per §9): edit research/01_hypothesis_register/H050/data_requirements.md

# 9. Single commit
cd "C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\inspiring-franklin-13a1f1"
git add config/cell_i_sources.yaml research/01_hypothesis_register/H050/data_requirements.md
git commit -m "data(h050): P1-H050-DATA-COVERAGE Cell I backfill — ES+NQ 2015-2019 + NQ 2025"
```

If any single step fails, abort and consult §10 rollback before retrying.
