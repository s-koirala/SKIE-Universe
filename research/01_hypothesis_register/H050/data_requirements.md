---
name: H050 data requirements
description: Pre-registration dataset checksums and coverage bounds for H050
type: project
hypothesis_id: H050
status: complete
created: 2026-04-24
revised: 2026-04-26
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
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` v0.3.0 (commit `329fd1b` decade-wraparound disambiguation) |

## Coverage

| Field | Value |
|---|---|
| ES date range | 2015-01-01 → 2025-12-03 UTC (last bar `ts_event`; substrate end-of-2025 truncation pre-disclosed in runbook §1.1; right-edge envelope shortfall per Round-2 finding F-PLV-1) |
| NQ date range | 2015-01-01 → 2025-12-19 UTC (last bar `ts_event`; Z-window-bounded per `download_historical_years` `('Z','09-15','12-20')`) |
| Total rows (combined, roll-adjusted) | 7,354,066 |
| ES rows (sum of partitions, roll-adjusted) | 3,694,534 |
| NQ rows (sum of partitions, roll-adjusted) | 3,659,532 |

Note: train/val/test windows defined in `H050.yaml` are:
- train: 2015-01-01–2022-12-31
- val: 2023-01-01–2023-12-31
- test: 2024-01-01–2025-12-31

**Coverage relative to design.md §2 envelope (post-Cell-I).** The substrate spans 2015-01-01 → 2025-12-03 (ES, last bar UTC) and 2015-01-01 → 2025-12-19 (NQ, last bar UTC). Train and val partitions are fully contained. The test partition (2024-01-01 → 2025-12-31) is covered everywhere except its right edge: ES 2025 ends 28 calendar days short of 2025-12-31; NQ 2025 ends 12 calendar days short. For non-2025 years the Z-window 12-21 → 12-31 truncation is harmless because the front-month rolls to the next-year H contract before year-end and no bars are lost from the continuous series; for the 2025 test partition (right edge of the strictly-held-out test set) the Dec-tail absence is unrecovered. The substrate as-is is what the production walk-forward will use; the truncation is a known calendar-edge limitation tracked under follow-up `P1-DATABENTO-RIGHT-EDGE-EXTENSION` (renames `P1-DATABENTO-DEC21-EXTENSION` to make the option-A path explicit) — an optional second incremental Databento pull would close the gap if user authorizes. If the upcoming walk-forward run lands a result whose disposition (per design.md §10) materially depends on the last 12-28 days of 2025, the disposition entry receives a `test-window-truncated` annotation and references this section.

Aggregation-rule binding: [aggregation_rule_addendum_2026-04-24.md](./aggregation_rule_addendum_2026-04-24.md) §3.2 substrate-blind constraint is now satisfiable (ES + NQ × 2015-2025 substrate covers the addendum's substrate-blind attestation requirement, modulo the right-edge truncation noted above and tracked under F-PLV-1).

## Checksums — source CSV (raw tier)

These are the CSV files as delivered by Databento, before any processing.
Read from [data/processed/_provenance/vendor_legacy_1min_20260426.json](../../../data/processed/_provenance/vendor_legacy_1min_20260426.json) `dataset_checksums`.

| File | SHA256 |
|---|---|
| `ES_1min_databento.csv` | `6b8f37d1a14c99b64f4a3de7ed94b4bd289cc9eb681484a5e0433bb9d37b52a7` |
| `ES_2015_1min_databento.csv` | `4dc3347d98ff85d461a7e1777665dbc10ed41b69e477deda5614c6aa97b8d031` |
| `ES_2016_1min_databento.csv` | `ee06ceb3db9bac268d546fed064f50fdc72cbae7b51cb33868bd63d301e2fb63` |
| `ES_2017_1min_databento.csv` | `f6367c5cd854b4120a987d82c5b12c11f07edbd13203f256ff97ef2b4c59b3b9` |
| `ES_2018_1min_databento.csv` | `152830311b605aa40225de8035d02a87094dce267233dab983930aa61801d743` |
| `ES_2019_1min_databento.csv` | `cf0212c98e6c4249a31ce3be765945500e2fcc456cdf5e3af294fcdcac7c1b9d` |
| `ES_2020_1min_databento.csv` | `acd772e8701a25d7bf045d1a39f6ec6ad7cbdc949d9c7b60952d5e2c68aa9b60` |
| `ES_2021_1min_databento.csv` | `b4749e434a10b7e2aeb6c4f211368eca980c76ab4a4b1c0dccd14282df63b467` |
| `ES_2022_1min_databento.csv` | `bc149f09a4da617d5677fb82da5e26f282c0503abbacfc55c20fe7ab03f28072` |
| `ES_2025_1min_databento.csv` | `58c12094be735c81c0de852b7dd52a47ab9f8d3ac626aa8223cafbd5cee4f0bc` |
| `NQ_1min_databento.csv` | `ad42b8641d7bf13211dda82bb400b5814461b95ac40227d0a25b7f0781e57d12` |
| `NQ_2015_1min_databento.csv` | `58161199d130300244cc069bb94b24f76dc55a45eb751fc17dd68c9eaab18507` |
| `NQ_2016_1min_databento.csv` | `985c9b5027afc95d92b6a34eb2d918a6fa2b348b6847a1a8ec324c337c861a81` |
| `NQ_2017_1min_databento.csv` | `1ce53479cae33ff6cfb6aa2f21d0f705376fbf77e03731b569149fecbb310653` |
| `NQ_2018_1min_databento.csv` | `26a67a6a4b0ef9313d7746af4eba75615bce347fc0f9d8c61d5ccbb818dd8936` |
| `NQ_2019_1min_databento.csv` | `f7ba52571a16205e3fc8cdaafce8711e850b232db0344c371ef336ef25dc5bdf` |
| `NQ_2020_1min_databento.csv` | `9da42fa2da4274ba8c7bcab39e3c7ac3342830be021b704ca3e9a8e26c2f8bc4` |
| `NQ_2021_1min_databento.csv` | `a13570aa9fc0935fa7b078a535c1defff4a71c8916ff39c2c9a888775ce21a81` |
| `NQ_2022_1min_databento.csv` | `5037d912fc0b6b8b31c067ad1867b4222bafdacaf19d48794860ebe500e5aeda` |
| `NQ_2025_1min_databento.csv` | `6e9c998d7dfb883c6cad29b955dd04937ece47d8b80fe0af6aca4f50c2bbb5e2` |

Note: individual-year CSVs for ES_2023.csv, ES_2024.csv, NQ_2023.csv, NQ_2024.csv
were not available as standalone files in the raw landing directory at snapshot
time; they are covered by the combined `ES_1min_databento.csv` and
`NQ_1min_databento.csv` checksums above.

## Checksums — processed parquet (roll-adjusted tier)

Computed via `skie_ninja.utils.hashing.frame_sha256` with
`sort_cols=["symbol", "ts_event"]` (canonical polars sort before hash).
These are the binding dataset checksums for H050 reproducibility.

### Combined frame

| Field | Value |
|---|---|
| Combined SHA256 | `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` |
| Rows | 7,354,066 |
| Computed | 2026-04-26 |
| Provenance | [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json) |

### Per-partition

| Partition | SHA256 |
|---|---|
| `symbol=ES/year=2015/part-0000.parquet` | `b499bb492dcdc9d562e3f5d65799ae10d4c9a1cff404c0a7491c58e7edaccfd5` |
| `symbol=ES/year=2016/part-0000.parquet` | `a384c0c225a43910c1a42910c4cfe291bc59c9b891f24f6b68f8bce6838ab1a5` |
| `symbol=ES/year=2017/part-0000.parquet` | `532b08fdf49f099526486e61b24f6fdcb924e2d0ed9af639d812860dda61a051` |
| `symbol=ES/year=2018/part-0000.parquet` | `d883cfd05855aa90a1c4d3dd2b5a235fda2e52231747883fffd22d8d573268cc` |
| `symbol=ES/year=2019/part-0000.parquet` | `c45f2f3fb723bf0764e0735bb25ba09d4115568069912a2711583cdf85070180` |
| `symbol=ES/year=2020/part-0000.parquet` | `da0485eb88564739859ab263cf0e64fe91257bb4416b33816eb77ed02c8b572a` |
| `symbol=ES/year=2021/part-0000.parquet` | `f5cf095df92ad587d3718e5a41d4c2d0d439d7843020254608cf941246f1d171` |
| `symbol=ES/year=2022/part-0000.parquet` | `cc0aa93b7ddccd7fe9fbbbe2c415c2d4a6fbf7c5d8067d34319f8fbdcf3b5f98` |
| `symbol=ES/year=2023/part-0000.parquet` | `ce5e599db6e8cb520fb257ac57512f294fff7d5e37e963d5692a9add701a2423` |
| `symbol=ES/year=2024/part-0000.parquet` | `a7d5fc06f215e190a863e5b49b1ea709a2f34e8f058056533103d676f1be2a9a` |
| `symbol=ES/year=2025/part-0000.parquet` | `4863284d4ebcff796e9c4fc2338e9ce643127710384998011876844e1fba798e` |
| `symbol=NQ/year=2015/part-0000.parquet` | `2ab474274660b1e7e70102e66fd1ec03835291ab6c47d46b28cddb37dde7a5b0` |
| `symbol=NQ/year=2016/part-0000.parquet` | `0743afa0825ee5c5aedf786b05d5a09c09955ad1113c153954459f278706192e` |
| `symbol=NQ/year=2017/part-0000.parquet` | `55b4e088b2b53cc7463d2bee8cd819b9300143915fcd3ed907105940e14938fe` |
| `symbol=NQ/year=2018/part-0000.parquet` | `7651addca845cd7689af2379d59c70168c8bb174be78df2f11549bd7b9a60467` |
| `symbol=NQ/year=2019/part-0000.parquet` | `c346a7d280c720888f88361db0ea76a6ab6b845c79b2d229c5ad8043578e5bea` |
| `symbol=NQ/year=2020/part-0000.parquet` | `e0c98ffbd5912daf890b51b46984355d6e2064da9406c39a96eae7026cab634e` |
| `symbol=NQ/year=2021/part-0000.parquet` | `268b522d54073c36871c4867089e23113d9322968b4a5f495fc20813395d3137` |
| `symbol=NQ/year=2022/part-0000.parquet` | `7cc3ca5a9e32759e796d7a59e1c2de017a9044e4afa545cc7017c665da7e5910` |
| `symbol=NQ/year=2023/part-0000.parquet` | `d419337c59f710c8ebcef89ad463e113b51113ebaeeca83e5dbbfba4e9cdc8f2` |
| `symbol=NQ/year=2024/part-0000.parquet` | `7694d6d5049f96b80031b98c4bb67f287553f321fbea245f24c34aa1f4d9911d` |
| `symbol=NQ/year=2025/part-0000.parquet` | `e90b614cfd2421a2c8f41244130c3a7dc805e40fc4dca16c6b1dfab08095acbc` |

## Cell I backfill — landed 2026-04-26

User-accepted Cell I per [docs/research_notes/memo_option-b-data-coverage_2026-04-24.md](../../../docs/research_notes/memo_option-b-data-coverage_2026-04-24.md) §6: ES + NQ 2015-2019 + NQ 2025 backfilled from Databento GLBX.MDP3 to close the design.md §2 substrate gap.

**Status**: landed.
- Substrate Stage A + Stage B executed — commit `3b00713`.
- Decade-wraparound contract-symbol-collision bug (exposed by the multi-decade substrate) fixed in commit `329fd1b` — module v0.2.0 → v0.3.0 with `contract_id_full` disambiguation; AFML §2.4.3 anchor invariant verified empirically (anchor=ESZ5_2025 / NQZ5_2025 at factor 1.0).
- Live `metadata.get_cost` figure recorded at $16.5171 USD (P1-H050-CELL-I-LIVE-COST-CAPTURE closed).
- Runbook: [docs/research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md](../../../docs/research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md).
- Cost estimate memo: [docs/research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md](../../../docs/research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md).

Note on Dec 21-31 calendar-edge gap: the sibling `download_historical_years` Z-contract window is `('Z', '09-15', '12-20')` per [databento_downloader.py:245](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/src/python/data_collection/databento_downloader.py). All year-end timestamps therefore terminate ~Dec 16-20, **not** Dec 31. This is intrinsic to the contract-month tuple, applies symmetrically to all 2015-2025 partitions, and is tracked under `P1-DATABENTO-DEC21-EXTENSION` for an optional Z-window extension.

## Pre-Cell-I checksums (superseded 2026-04-26)

The tables in this section are retained for audit trail. **Every prior `vendor_legacy_1min_roll_adjusted` SHA is invalidated by**:
1. The substrate extension to 2015-2025 inclusive (5 new years per symbol + NQ 2025), and
2. The v0.2.0 → v0.3.0 dataset version bump in commit `329fd1b` (`contract_id_full` disambiguation; full-sample multiplicative-ratio rescaling per the module's "Point-in-time caveat").

Both effects are independent — even partitions covering identical date ranges have different SHA256s post-Cell-I.

### Source CSV (raw tier) — pre-Cell-I

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

### Combined frame — pre-Cell-I

| Field | Value |
|---|---|
| Combined SHA256 | `d2c4aa4e70c6badcb294d9bec64ee3fc5093ba9085082495f5031743943b9a2d` |
| Rows | 3,703,359 |
| Computed | 2026-04-24 |

### Per-partition — pre-Cell-I

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

## OFI dependency note

Feature `ofi_tickrule@1.0` uses tick-rule proxy (Lee-Ready) as a fallback
because MBP-10 order book data is not yet available in this dataset.  The
tick-rule OFI is a directional approximation; see design.md §3 for the
dependency flag and upgrade path when MBP-10 is available.  This limitation
is pre-registered and does not invalidate H050 as designed.

## Provenance file

Machine-readable provenance records:
- `data/processed/_provenance/vendor_legacy_1min_20260426.json` (raw tier)
- `data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json` (roll-adjusted tier)
