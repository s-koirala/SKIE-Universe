---
name: H050 data requirements
description: Pre-registration dataset checksums and coverage bounds for H050
type: project
hypothesis_id: H050
status: complete
created: 2026-04-24
---

# H050 — Data Requirements

Pre-registration companion to `design.md` §11.  Frozen at the time the
hypothesis moves to `status=running`.  Any subsequent dataset update requires
a successor hypothesis ID.

## Source dataset

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23; no redistribution; internal research use only. |
| Symbols | ES.FUT, NQ.FUT (front-month; Databento continuous series) |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment (López de Prado 2018, Wiley) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` v0.2.0 |

## Coverage

| Field | Value |
|---|---|
| ES date range | 2020-01-01 → 2025-12-03 UTC (last bar ts_event; ES_2025 file mtime 2024-12-04) |
| NQ date range | 2020-01-01 → 2024-12-19 UTC (last bar ts_event; corrected 2026-04-25 from prior "2024-12-31" — sibling `download_historical_years` Z-window terminates at 12-20 by construction) |
| Total rows (combined) | 3,703,359 |
| Roll events (roll_flag=True bars) | 58,465 |
| ES rows | 1,882,800 (approx; see per-file checksums) |
| NQ rows | 1,820,559 (approx; see per-file checksums) |

Note: train/val/test windows defined in `H050.yaml` are:
- train: 2015-01-01–2022-12-31 (source data begins 2020-01-01; train window
  is the design envelope; actual available training data is 2020-01-01–2022-12-31)
- val: 2023-01-01–2023-12-31
- test: 2024-01-01–2025-12-31

## Checksums — source CSV (raw tier)

These are the CSV files as delivered by Databento, before any processing.

| File | SHA256 |
|---|---|
| `ES_1min_databento.csv` | `6b8f37d1a14c99b64f4a3de7ed94b4bd289cc9eb681484a5e0433bb9d37b52a7` |
| `ES_2020.csv` | `acd772e8701a25d7bf045d1a39f6ec6ad7cbdc949d9c7b60952d5e2c68aa9b60` |
| `ES_2021.csv` | `b4749e434a10b7e2aeb6c4f211368eca980c76ab4a4b1c0dccd14282df63b467` |
| `ES_2022.csv` | `bc149f09a4da617d5677fb82da5e26f282c0503abbacfc55c20fe7ab03f28072` |
| `ES_2025.csv` | `58c12094be735c81c0de852b7dd52a47ab9f8d3ac626aa8223cafbd5cee4f0bc` |
| `NQ_1min_databento.csv` | `ad42b8641d7bf13211dda82bb400b5814461b95ac40227d0a25b7f0781e57d12` |
| `NQ_2020.csv` | `9da42fa2da4274ba8c7bcab39e3c7ac3342830be021b704ca3e9a8e26c2f8bc4` |
| `NQ_2021.csv` | `a13570aa9fc0935fa7b078a535c1defff4a71c8916ff39c2c9a888775ce21a81` |
| `NQ_2022.csv` | `5037d912fc0b6b8b31c067ad1867b4222bafdacaf19d48794860ebe500e5aeda` |

Note: individual-year CSVs for ES_2023.csv, ES_2024.csv, NQ_2023.csv,
NQ_2024.csv were not available as standalone files in the raw landing directory
at snapshot time; they are covered by the combined `ES_1min_databento.csv` and
`NQ_1min_databento.csv` checksums above.

## Checksums — processed parquet (roll-adjusted tier)

Computed via `skie_ninja.utils.hashing.frame_sha256` with
`sort_cols=["symbol", "ts_event"]` (canonical polars sort before hash).
These are the binding dataset checksums for H050 reproducibility.

### Combined frame

| Field | Value |
|---|---|
| Combined SHA256 | `d2c4aa4e70c6badcb294d9bec64ee3fc5093ba9085082495f5031743943b9a2d` |
| Rows | 3,703,359 |
| Computed | 2026-04-24 |

### Per-partition

| Partition | SHA256 |
|---|---|
| `symbol=ES/year=2020/part-0000.parquet` | `24c6a6bf88d90c8aaf950b56d453f79fba5ddc83fee8afd1f93b3cf435a352ef` |
| `symbol=ES/year=2021/part-0000.parquet` | `af7e75bbd9dd53f4845d8133d5e1130330a950bef1e180e4d0eaed3c4614276c` |
| `symbol=ES/year=2022/part-0000.parquet` | `17e2fca486e9802713f86be015956f315f0d06f2c1a5cedb2e351d815ca4cca4` |
| `symbol=ES/year=2023/part-0000.parquet` | `87f9bc734740069cb6ad997d7292526f4cac7d4910841204097a9b6b10233af7` |
| `symbol=ES/year=2024/part-0000.parquet` | `ca14cece2bff82b1a64b48ddef6f5b802aacc8e29b193b4245b2f1f61799e134` |
| `symbol=ES/year=2025/part-0000.parquet` | `0dc679b5010a5013c34aa6f723b6f4dd76d6b07fa39bf11660097cc38f79bbd1` |
| `symbol=NQ/year=2020/part-0000.parquet` | `143c62e39d62ee2953a8c64c5b1437c8b7600a53c7adb7253677297d858b3ab4` |
| `symbol=NQ/year=2021/part-0000.parquet` | `b9d3dd90cda5aadbf7db24c3339d36445123e148a82d2bd1be0218aef21c7518` |
| `symbol=NQ/year=2022/part-0000.parquet` | `faf8cf2acad31e5beb3a64466bc6962b758180d26193d62870679494d0913558` |
| `symbol=NQ/year=2023/part-0000.parquet` | `fa58a0bea546b6563ee2dcfb8a27125d891cbc8403887bdff80db4418dc65ed3` |
| `symbol=NQ/year=2024/part-0000.parquet` | `1e7b7c32b27d80d89f1b1c1d62b5554f6516163db8a4631934c0f4df08189952` |

## Pending Cell I backfill (status: prepared 2026-04-24, awaiting paid Databento API call)

User-accepted Cell I per [docs/research_notes/memo_option-b-data-coverage_2026-04-24.md](../../../docs/research_notes/memo_option-b-data-coverage_2026-04-24.md) §6: backfill ES + NQ 2015-2019 + NQ 2025 from Databento GLBX.MDP3 to close the design.md §2 substrate gap.

**Authorization status**: not yet executed. Runbook at [docs/research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md](../../../docs/research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md). Cost estimate at [docs/research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md](../../../docs/research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md).

The checksum tables in §"Source CSV (raw tier)" and §"Processed parquet (roll-adjusted tier)" above are **frozen against the current pre-Cell-I substrate** and bind any H050 walk-forward run executed against that substrate. They will be **superseded** in a single commit after the Cell I run completes; the pre-Cell-I tables will be retained under a new section "Pre-Cell-I checksums (superseded YYYY-MM-DD)" for audit.

### Expected new source CSVs (post-Cell I)

The 11 new CSVs below are loaded into the ingest job via the YAML-injectable `--sources-yaml config/cell_i_sources.yaml` flag (per runbook §7.1) — no source-file edit to `_CANONICAL_SOURCES` is required. Schema enforced by [load_sources_yaml](../../../src/skie_ninja/data/ingest/vendor_legacy_1min.py); regression-tested in [tests/unit/test_ingest_vendor_legacy_sources.py](../../../tests/unit/test_ingest_vendor_legacy_sources.py).

| File | Symbol | Year | SHA256 |
|---|---|---|---|
| `ES_2015_1min_databento.csv` | ES | 2015 | TBD at Stage A run |
| `ES_2016_1min_databento.csv` | ES | 2016 | TBD at Stage A run |
| `ES_2017_1min_databento.csv` | ES | 2017 | TBD at Stage A run |
| `ES_2018_1min_databento.csv` | ES | 2018 | TBD at Stage A run |
| `ES_2019_1min_databento.csv` | ES | 2019 | TBD at Stage A run |
| `NQ_2015_1min_databento.csv` | NQ | 2015 | TBD at Stage A run |
| `NQ_2016_1min_databento.csv` | NQ | 2016 | TBD at Stage A run |
| `NQ_2017_1min_databento.csv` | NQ | 2017 | TBD at Stage A run |
| `NQ_2018_1min_databento.csv` | NQ | 2018 | TBD at Stage A run |
| `NQ_2019_1min_databento.csv` | NQ | 2019 | TBD at Stage A run |
| `NQ_2025_1min_databento.csv` | NQ | 2025 | TBD at Stage A run |

### Expected new processed-parquet partitions (post-Cell I)

`vendor_legacy_1min` (raw front-month concatenation):

| Partition | SHA256 |
|---|---|
| `symbol=ES/year=2015/part-0000.parquet` | TBD |
| `symbol=ES/year=2016/part-0000.parquet` | TBD |
| `symbol=ES/year=2017/part-0000.parquet` | TBD |
| `symbol=ES/year=2018/part-0000.parquet` | TBD |
| `symbol=ES/year=2019/part-0000.parquet` | TBD |
| `symbol=NQ/year=2015/part-0000.parquet` | TBD |
| `symbol=NQ/year=2016/part-0000.parquet` | TBD |
| `symbol=NQ/year=2017/part-0000.parquet` | TBD |
| `symbol=NQ/year=2018/part-0000.parquet` | TBD |
| `symbol=NQ/year=2019/part-0000.parquet` | TBD |
| `symbol=NQ/year=2025/part-0000.parquet` | TBD |

`vendor_legacy_1min_roll_adjusted` (full re-derivation; **all 22 partitions change** due to full-sample multiplicative-ratio rescaling per [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) §"Point-in-time caveat"):

| Partition | Pre-Cell-I SHA256 | Post-Cell-I SHA256 |
|---|---|---|
| `symbol=ES/year=2015/part-0000.parquet` | (absent) | TBD |
| `symbol=ES/year=2016/part-0000.parquet` | (absent) | TBD |
| `symbol=ES/year=2017/part-0000.parquet` | (absent) | TBD |
| `symbol=ES/year=2018/part-0000.parquet` | (absent) | TBD |
| `symbol=ES/year=2019/part-0000.parquet` | (absent) | TBD |
| `symbol=ES/year=2020/part-0000.parquet` | `24c6a6bf88d90c8aaf950b56d453f79fba5ddc83fee8afd1f93b3cf435a352ef` | TBD |
| `symbol=ES/year=2021/part-0000.parquet` | `af7e75bbd9dd53f4845d8133d5e1130330a950bef1e180e4d0eaed3c4614276c` | TBD |
| `symbol=ES/year=2022/part-0000.parquet` | `17e2fca486e9802713f86be015956f315f0d06f2c1a5cedb2e351d815ca4cca4` | TBD |
| `symbol=ES/year=2023/part-0000.parquet` | `87f9bc734740069cb6ad997d7292526f4cac7d4910841204097a9b6b10233af7` | TBD |
| `symbol=ES/year=2024/part-0000.parquet` | `ca14cece2bff82b1a64b48ddef6f5b802aacc8e29b193b4245b2f1f61799e134` | TBD |
| `symbol=ES/year=2025/part-0000.parquet` | `0dc679b5010a5013c34aa6f723b6f4dd76d6b07fa39bf11660097cc38f79bbd1` | TBD |
| `symbol=NQ/year=2015/part-0000.parquet` | (absent) | TBD |
| `symbol=NQ/year=2016/part-0000.parquet` | (absent) | TBD |
| `symbol=NQ/year=2017/part-0000.parquet` | (absent) | TBD |
| `symbol=NQ/year=2018/part-0000.parquet` | (absent) | TBD |
| `symbol=NQ/year=2019/part-0000.parquet` | (absent) | TBD |
| `symbol=NQ/year=2020/part-0000.parquet` | `143c62e39d62ee2953a8c64c5b1437c8b7600a53c7adb7253677297d858b3ab4` | TBD |
| `symbol=NQ/year=2021/part-0000.parquet` | `b9d3dd90cda5aadbf7db24c3339d36445123e148a82d2bd1be0218aef21c7518` | TBD |
| `symbol=NQ/year=2022/part-0000.parquet` | `faf8cf2acad31e5beb3a64466bc6962b758180d26193d62870679494d0913558` | TBD |
| `symbol=NQ/year=2023/part-0000.parquet` | `fa58a0bea546b6563ee2dcfb8a27125d891cbc8403887bdff80db4418dc65ed3` | TBD |
| `symbol=NQ/year=2024/part-0000.parquet` | `1e7b7c32b27d80d89f1b1c1d62b5554f6516163db8a4631934c0f4df08189952` | TBD |
| `symbol=NQ/year=2025/part-0000.parquet` | (absent) | TBD |

Combined frame SHA256 (pre-Cell-I): `d2c4aa4e70c6badcb294d9bec64ee3fc5093ba9085082495f5031743943b9a2d` — also superseded.

### Expected Coverage update (post-Cell I)

Note on Dec 21-31 calendar-edge gap: the sibling `download_historical_years` Z-contract window is `('Z', '09-15', '12-20')` per [databento_downloader.py:245](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/src/python/data_collection/databento_downloader.py). All year-end timestamps therefore terminate ~Dec 16-20, **not** Dec 31. This is intrinsic to the contract-month tuple, applies symmetrically to existing 2020-2024 substrate and the new 2015-2019 + NQ 2025 backfill, and is not introduced by Cell I. Tracked as new follow-up `P1-DATABENTO-DEC21-EXTENSION` for an optional Z-window extension to capture the brief no-front-month tail.

| Field | Pre-Cell-I value | Expected post-Cell-I value |
|---|---|---|
| ES date range | 2020-01-01 → 2025-12-03 UTC | 2015-01-01 → 2025-12-03 UTC (or further forward if §6.4 ES 2025 refresh runs; bound by ~current-year-12-20) |
| NQ date range | 2020-01-01 → 2024-12-19 UTC | 2015-01-01 → ~2025-12-20 UTC (Z-window-bounded; verify against `metadata.get_cost` and post-Stage-A row count) |
| Total rows (combined) | 3,703,359 | ~7,440,000 (= 3,703,359 + ~3,740,000 Cell I expected, anchored on empirical 340k/yr ES and NQ; binding figure is the post-Stage-B verified row count) |

## OFI dependency note

Feature `ofi_tickrule@1.0` uses tick-rule proxy (Lee-Ready) as a fallback
because MBP-10 order book data is not yet available in this dataset.  The
tick-rule OFI is a directional approximation; see design.md §3 for the
dependency flag and upgrade path when MBP-10 is available.  This limitation
is pre-registered and does not invalidate H050 as designed.

## Provenance file

A machine-readable provenance record is written automatically by the ingest
pipeline at:
`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260424.json`
