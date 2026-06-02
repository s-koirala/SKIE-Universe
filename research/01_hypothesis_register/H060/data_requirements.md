---
name: H060 data requirements
description: Pre-registration dataset checksums and coverage bounds for H060
type: project
hypothesis_id: H060
status: designed
created: 2026-04-27
---

# H060 — Data Requirements

Pre-registration companion to `design.md` §11. Frozen at the time the hypothesis moves to `status=running`. Any subsequent dataset update requires a successor hypothesis ID.

H060 binds to the **identical H050 roll-adjusted substrate**. No new data ingest is required for H060. The H050 [data_requirements.md](../H050/data_requirements.md) is the canonical source of truth; this file mirrors the binding fields and surfaces the H060-specific deltas (input tensor schema, model-weight artifact path, sidecar contract).

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
| ES date range | 2015-01-01 → 2025-12-03 UTC (last bar `ts_event`) |
| NQ date range | 2015-01-01 → 2025-12-19 UTC (last bar `ts_event`) |
| Total rows (combined, roll-adjusted) | 7,354,066 |
| ES rows (sum of partitions, roll-adjusted) | 3,694,534 |
| NQ rows (sum of partitions, roll-adjusted) | 3,659,532 |

H060 train / val / test windows are identical to H050:

- train: 2015-01-01 – 2022-12-31
- val:   2023-01-01 – 2023-12-31
- test:  2024-01-01 – 2025-12-31

**Right-edge truncation**: ES 2025 ends 28 calendar days short of 2025-12-31; NQ 2025 ends 12 calendar days short. Identical to H050. Tracked under the H050 follow-up `P1-DATABENTO-RIGHT-EDGE-EXTENSION`. If H060's disposition (per design.md §10) materially depends on the last 12-28 days of 2025, the disposition entry receives a `test-window-truncated` annotation.

## Checksums — processed parquet (roll-adjusted tier)

H060 binds to the H050 combined frame SHA256. Per-partition checksums are reproduced from [H050/data_requirements.md](../H050/data_requirements.md) below for an audit-trail self-contained record; if a discrepancy ever surfaces between this file and the H050 file, the H050 file is authoritative.

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

## H060 input tensor specification

PatchTST consumes a 60-bar × 5-channel right-anchored window. The substrate fields used are:

| Channel | Source column (roll-adjusted parquet) | Pre-encoding transform |
|---|---|---|
| `open` | `open` | no per-fold z-score (per design.md §3.2 Option (a) Q-R1-14 remediation; rely on PatchTST encoder instance norm) |
| `high` | `high` | no per-fold z-score (per design.md §3.2 Option (a) Q-R1-14 remediation; rely on PatchTST encoder instance norm) |
| `low` | `low` | no per-fold z-score (per design.md §3.2 Option (a) Q-R1-14 remediation; rely on PatchTST encoder instance norm) |
| `close` | `close` | no per-fold z-score (per design.md §3.2 Option (a) Q-R1-14 remediation; rely on PatchTST encoder instance norm) |
| `volume` | `volume` | log1p, then per-fold z-score |

Window-construction is asserted PIT-safe by the canary suite at [tests/unit/test_h050_aggregation_convention.py](../../../tests/unit/test_h050_aggregation_convention.py) (extended for H060 per design.md §3.3). No new substrate is required; the input is a pure function of the H050-frozen partitions.

## Pretraining-corpus contamination

**By construction: zero.** H060 trains PatchTST from random initialisation on the H050 walk-forward training fold only. No pretrained checkpoint is loaded at any step. The reproducibility-verifier asserts `pretrained_checkpoint_loaded == false` for every fold sidecar (design.md §11.1 invariant 1).

This is the structural difference from H058 (TS foundation model + LoRA), and the reason H060 is included in the chart-reader hypothesis set despite the partial overlap with H058's transformer-class architecture.

## H060 model-artifact paths

| Artifact | Path | Notes |
|---|---|---|
| Per-fold PatchTST state dict | `logs/models/{run_id}_patchtst_fold{fold_id}.pt` | gitignored; SHA256 recorded in sidecar |
| H060 sidecar (per fold) | `logs/reproducibility/{run_id}_patchtst_h056_fold{fold_id}.json` | schema `patchtst_h056_v1` per design.md §11 |
| HMM selection sidecar (per fold) | `logs/reproducibility/{run_id}_hmm_selection_fold{fold_id}.json` | schema `hmm_sidecar_v1` per ADR-0005 |
| Run-level reproducibility log | `logs/reproducibility/{run_id}.json` | `model_hash` field combines weights + HMM sidecar + ledger roll-up |

## OFI dependency note

The HMM regime gate consumes the H050 microstructure-feature emissions, including `ofi_tickrule@1.0` (Lee-Ready tick-rule fallback). H060's PatchTST input tensor (raw OHLCV) does **not** consume OFI. The dependency note in [H050 data_requirements.md](../H050/data_requirements.md) §OFI dependency note carries forward to H060 only via the gate, and the upgrade path (MBP-10 ingest landing) is identical.

## Provenance file

Machine-readable provenance records (inherited from H050):
- `data/processed/_provenance/vendor_legacy_1min_20260426.json` (raw tier)
- `data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json` (roll-adjusted tier)
