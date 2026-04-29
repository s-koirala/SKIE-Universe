---
name: H058 data requirements
description: Pre-registration dataset checksums and coverage bounds for H058
type: project
hypothesis_id: H058
status: designed
created: 2026-04-27
---

# H058 — Data Requirements

Pre-registration companion to [design.md](design.md) §11. Frozen at the time the hypothesis moves to `status=running`. Any subsequent dataset update requires a successor hypothesis ID.

H058 inherits the H050 substrate verbatim — the TSFM context tensor in [design.md](design.md) §3 (`tsfm_context@b`) is derived bar-by-bar from the existing 1-min log-return series of the roll-adjusted ES + NQ continuous-contract dataset. **No new ingest dependency, no new external join.** Inheritance is bit-exact at the SHA256 level: any change to the H050 substrate invalidates this file and forces a successor hypothesis ID.

## Source dataset (inherited from H050)

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23; no redistribution; internal research use only. |
| Symbols | ES.FUT, NQ.FUT (front-month; Databento continuous series) |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment (López de Prado 2018, Wiley) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` v0.3.0 (commit `329fd1b`) |

## Coverage (inherited from H050)

| Field | Value |
|---|---|
| ES date range | 2015-01-01 → 2025-12-03 UTC |
| NQ date range | 2015-01-01 → 2025-12-19 UTC |
| Total rows (combined, roll-adjusted) | 7,354,066 |
| ES rows (sum of partitions, roll-adjusted) | 3,694,534 |
| NQ rows (sum of partitions, roll-adjusted) | 3,659,532 |

H058 train/val/test windows are identical to H050 ([design.md](design.md) §2):

- train: 2015-01-01 – 2022-12-31
- val: 2023-01-01 – 2023-12-31
- test: 2024-01-01 – 2025-12-31

Right-edge truncation (ES 2025 ends 28 calendar days short of 2025-12-31; NQ 2025 ends 12 calendar days short) per H050 §2 / `P1-DATABENTO-RIGHT-EDGE-EXTENSION` applies symmetrically. If the H058 disposition (per [design.md](design.md) §10) materially depends on the last 12-28 days of 2025, the disposition entry receives a `test-window-truncated` annotation.

**TSFM context-window left-edge constraint.** H058's TSFM context window is `context_length = 512` bars right-anchored at each decision bar. The earliest decision bar in any walk-forward training fold therefore requires a left-edge buffer of 512 prior bars from the substrate. The H050 substrate begins at 2015-01-01 UTC; the first H058 decision bar in the train window is at substrate position `≥ 512` (i.e., approximately 2015-01-02 13:00 UTC after accounting for non-trading hours). The walk-forward orchestrator enforces this via the per-fold canary in [design.md](design.md) §11.1 #2.

## Checksums — source CSV (raw tier, inherited from H050)

These are the CSV files as delivered by Databento, before any processing. Read from [data/processed/_provenance/vendor_legacy_1min_20260426.json](../../../data/processed/_provenance/vendor_legacy_1min_20260426.json) `dataset_checksums`. Inheritance is bit-exact from [H050/data_requirements.md](../H050/data_requirements.md).

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

Note: individual-year CSVs for ES_2023.csv, ES_2024.csv, NQ_2023.csv, NQ_2024.csv were not available as standalone files in the raw landing directory at snapshot time; they are covered by the combined `ES_1min_databento.csv` and `NQ_1min_databento.csv` checksums above.

## Checksums — processed parquet (roll-adjusted tier, inherited from H050)

Computed via `skie_ninja.utils.hashing.frame_sha256` with `sort_cols=["symbol", "ts_event"]` (canonical polars sort before hash). These are the binding dataset checksums for H058 reproducibility.

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

## Backbone-weights checksums (H058-specific, captured at run-time)

H058 introduces two backbone-weights dependencies that are **not** part of the H050 substrate. They are pre-registered by source URI + intended revision; the SHA256 of the local weights file is captured at run-time and recorded in the backbone sidecar JSON per [design.md](design.md) §11.

| Backbone | Source URI | Intended revision | SHA256 (run-time-captured) |
|---|---|---|---|
| TimesFM-2.5-200M | [hf://google/timesfm-2.5-200m-pytorch](https://huggingface.co/google/timesfm-2.5-200m-pytorch) | HF `main` at first run; pinned at run-time to the specific commit SHA shown in the sidecar | `<recorded at run-time in {run_id}_h054_timesfm.json:backbone_weights_sha256>` |
| Chronos-Bolt-base-205M | [hf://amazon/chronos-bolt-base](https://huggingface.co/amazon/chronos-bolt-base) | HF `main` at first run; pinned at run-time | `<recorded at run-time in {run_id}_h054_chronos.json:backbone_weights_sha256>` |

Backbone weights are **not** redistributed by this repo; they are downloaded on first run via `huggingface_hub` and cached under `~/.cache/huggingface/`. The SHA256 of the consumed local weights file is the binding artifact for H058 reproducibility (along with the LoRA adapter and head SHA256s captured per backbone sidecar).

## Pretraining-corpus contamination screen — initial pass (executed 2026-04-27)

Per [design.md](design.md) §8.3 and [Meyer, Kaltenpoth, Zalipski, Müller 2025, arxiv 2510.13654](https://arxiv.org/abs/2510.13654). Screen patterns:

```
{ '^ES', '^NQ', 'S&P 500', 'Nasdaq 100', 'e-mini', 'e-Mini',
  'equity index futures', 'CME front-month', 'GLBX.MDP3' }
```

at frequency ≤ 1 day.

| Backbone | Surface inventory match | Status | Gating follow-up |
|---|---|---|---|
| TimesFM-2.5-200M | None (Wikimedia Pageviews + Google Trends + GiftEvalPretrain + synthetic per [HF model card](https://huggingface.co/google/timesfm-2.5-200m-pytorch)). GiftEvalPretrain component-level inventory not enumerated in the model card; Salesforce LOTSA parent project includes "economics" as a domain — must be inspected before declaring `clean`. | `unverified — partial` | `P1-H058-TIMESFM-GIFTEVAL-INSPECTION` |
| Chronos-Bolt-base-205M | None at the model-card level ("trained on nearly 100 billion time series observations"; specific datasets not enumerated in the [HF model card](https://huggingface.co/amazon/chronos-bolt-base); financial datasets explicitly not mentioned). Full dataset list per [Ansari et al. 2024 arxiv 2403.07815](https://arxiv.org/abs/2403.07815) appendix not fetched at full-text in this pre-reg session. | `unverified — appendix-pending` | `P1-H058-CHRONOS-APPENDIX-INSPECTION` |

**Both follow-ups must resolve to `clean` or `documented` before H058 transitions to `status=running`.** A `documented` outcome with a specific overlapping series at the target frequency triggers `archive(null, contaminated)` per [design.md](design.md) §10 for the affected backbone.

## OFI dependency note (inherited from H050)

Feature `ofi_tickrule@1.0` uses tick-rule proxy (Lee-Ready) as a fallback because MBP-10 order book data is not yet available in this dataset. The tick-rule OFI is a directional approximation; the limitation is pre-registered for H050 and inherited by H058 unchanged.

## Provenance file

Machine-readable provenance records (inherited from H050):

- `data/processed/_provenance/vendor_legacy_1min_20260426.json` (raw tier)
- `data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json` (roll-adjusted tier)

H058-specific provenance (run-time-emitted):

- `logs/reproducibility/{run_id}_h054_timesfm.json` (TimesFM-2.5 backbone sidecar; schema `h054_backbone_sidecar_v1` per [design.md](design.md) §11)
- `logs/reproducibility/{run_id}_h054_chronos.json` (Chronos-Bolt-base backbone sidecar; same schema)
- `logs/reproducibility/{run_id}_hmm_selection.json` (HMM sidecar per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md))
