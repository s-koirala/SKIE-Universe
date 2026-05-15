---
name: H062 data requirements
description: Pre-registration dataset checksums and coverage bounds for H062 (binding at designed status)
type: project
hypothesis_id: H062
schema_version: 1
status: designed  # frozen concurrently with design.md per H050 + H053 + H054 + H055 + H060 atomic-snapshot-binding pattern
created: 2026-05-14
revised: 2026-05-14
---

# H062 — Data Requirements

Pre-registration companion to [design.md](design.md) §2 + §11. **Frozen at `designed` status concurrently with [design.md](design.md)** per the H050/H053/H054/H055/H060 atomic-snapshot-binding pattern.

The roll-adjusted post-Phase-O.0 substrate is shared between H060 and H062; the binding `output_frame_sha256` and per-partition SHAs below are sourced verbatim from the on-disk provenance JSON at [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json). **Substrate SHA correction vs CLAUDE.md Phase O.0 ledger entry**: the CLAUDE.md ledger asserts a combined SHA `242aaa280b216f45edc3b9d9de9630f52f71206eea7832c1cb0470296190f46f`; the actual provenance file reports `output_frame_sha256 = 1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959`. H062 binds to the **verified provenance SHA `1247dc7e...`**; the CLAUDE.md ledger reconciliation is tracked under new follow-up `P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE`.

## Source dataset

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23 + 2026-05-12; no redistribution; internal research use only. |
| Symbols | ES.FUT, NQ.FUT, MGC.FUT, SIL.FUT (front-month; Databento continuous series via parent-symbology). Coverage per the provenance JSON below: ES + NQ from 2020-01-01 onward (no pre-2020 substrate in this combined frame); MGC + SIL from 2015-01-01 onward. |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment ([López de Prado 2018, Wiley, ISBN 978-1119482086](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086), *practitioner*) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` (Phase O.0 Stage B parameterized version per CLAUDE.md ledger; supports quarterly H/M/U/Z roll codes for ES/NQ and monthly F/G/H/J/K/M/N/Q/U/V/X/Z for MGC/SIL) |

## Coverage

| Symbol | First partition | Last partition | Year partitions present |
|---|---|---|---|
| ES | year=2020 | year=2025 | 2020, 2021, 2022, 2023, 2024, 2025 (6 partitions) |
| NQ | year=2020 | year=2024 | 2020, 2021, 2022, 2023, 2024 (5 partitions) |
| MGC | year=2015 | year=2025 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 (11 partitions) |
| SIL | year=2015 | year=2025 | 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 (11 partitions) |

Source: enumerated from `source_checksums` keys in [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json). Total = 6 + 5 + 11 + 11 = **33 partitions** for the H062 v1 universe (the broader 38-partition figure in CLAUDE.md Phase O.0 also includes MCL 2021-2025, NOT used by H062 v1).

**ES + NQ pre-2020 coverage gap**: the Phase O.0 Stage B re-ingest did not include ES + NQ partitions for years 2015-2019. These years exist in the pre-Phase-O.0 `b3ee230a...` H055 substrate-binding (H055 [data_requirements.md](../H055/data_requirements.md) §"Per-partition" table) but are NOT part of the post-Phase-O.0 combined substrate H062 binds. This is an INTENTIONAL choice mirroring [H060 design.md §2 line 60](../H060/design.md) — H062's calibration holdout role is supplemental at v1; ES + NQ trend-strength filter selection is performed via inner-CV on IS (2020-2023), NOT on the 2015-2019 calibration holdout.

## H062 sample-window partition (BINDING; pre-reg-frozen)

| Fold | Window | ES + NQ rows? | MGC + SIL rows? | Role |
|---|---|---|---|---|
| Calibration holdout | 2015-01-01 → 2019-12-31 | NO (no pre-2020 substrate in post-Phase-O.0 combined frame) | YES | Supplemental hyperparameter pre-registration on metals leg (channel-N + k_atr); equity-index parameters selected on IS inner-CV instead. Disjoint from any prior-hypothesis test fold per [H055 data_requirements.md cross-hypothesis fit-set isolation](../H055/data_requirements.md). |
| IS | 2020-01-01 → 2023-12-31 | YES | YES | Parameter fitting + walk-forward inner CV (4 years; matches H050 train + H055 IS window). |
| OOS test | 2024-01-01 → 2025-12-{03,19,30} | YES per right-edge | YES | Out-of-sample inference fold. Per-symbol right-edges: ES → 2025-12-03; NQ → 2024-12-19; MGC → 2025-12-30; SIL → 2025-12-30. Right-edge truncation per the post-Stage-B substrate envelope. |

H062 OOS overlaps the OOS test folds of H050 (ES + NQ 2024-2025), H052a (ES + NQ 2023-07 → 2024-12), H053 v3 + v4 (ES + NQ 2024-2025), H054 (ES 2025), H055 (ES + NQ 2024-2025), and H060 (ES + NQ + MGC + SIL 2024-2025). Same-substrate-different-signal-class framing per H055 data_requirements §"Cross-hypothesis fit-set isolation properties"; H062 is per-trade intraday Donchian-channel breakout (event-driven entry on N-bar channel breakout), structurally distinct from HMM-gated 1-min directional (H050), HMM-gated first-hour ORB (H052a), multi-timeframe regression (H053), HMM-anti-gated ORB (H054), per-trade wick-rejection mean-reversion (H055), and daily-cadence TSMOM monthly rebalance (H060). Reported as `data-overlap-h050-h052a-h053-h054-h055-h060-acknowledged` annotation per design.md §10.

Any subsequent change to the H062 substrate requires either (a) a successor hypothesis ID, or (b) an addendum to this file with explicit revision-rationale and the new checksum table.

## Checksums — processed parquet (roll-adjusted tier; binding for H062)

Computed via [src/skie_ninja/utils/hashing.py](../../../src/skie_ninja/utils/hashing.py) `frame_sha256` with `sort_cols=["symbol", "ts_event"]` (canonical polars sort before hash); per-partition values lifted verbatim from the 2026-05-12 provenance run.

### Combined frame (output_frame_sha256)

| Field | Value |
|---|---|
| `output_frame_sha256` | `1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959` |
| `source_dataset_frame_sha256` | `bb3c7358bbe106448564f9c8b6405435a71ed25a21c27ba649125512c81ef38e` |
| Run ID | `eab2e95a73e44e3886d5a802b13da6bd` |
| Timestamp (UTC) | 2026-05-12 21:27:40 |
| Provenance JSON | [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json) |
| Total partitions in provenance | 38 (incl. 5 MCL; H062 v1 binds 33 — MCL excluded) |
| Coverage (H062 universe) | ES 2020-2025 + NQ 2020-2024 + MGC 2015-2025 + SIL 2015-2025 |

The H062 v1 binding is the SUBSET of the 38-partition combined frame restricted to symbols {ES, NQ, MGC, SIL} (MCL deferred per ADR-0023 + H061 reservation). At first H062 production-run dispatch, the orchestrator re-computes a SHA over the 33-partition H062 universe using the same `frame_sha256(sort_cols=["symbol","ts_event"])` convention; this subset-SHA is pinned in an addendum to this file at first run per the H055 first-run-pinning pattern. Mismatch on any subsequent run triggers `archive(null, data-violation)` per design.md §10.

### Per-partition (source_checksums; pre-roll-adjustment raw layer; R1 F1-011 fix — full enumeration of 33 H062-universe partitions at `designed` freeze)

The 2026-05-12 provenance JSON reports SHAs at the pre-roll-adjusted `vendor_legacy_1min/` (raw-tier) layer, NOT the roll-adjusted output layer. The mapping below enumerates the raw-tier SHA per partition for ALL 33 H062-universe partitions (ES + NQ + MGC + SIL); the roll-adjusted per-partition SHA table is `to-be-computed-at-first-running-run` for the H062 v1 universe (subset of the 38-partition combined frame). The pre-Phase-O.0 H055 binding `b3ee230a...` for ES + NQ 2015-2025 is **NOT** the H062 substrate-binding — H062 explicitly uses the post-Phase-O.0 combined frame for symbol-class consistency with H060 + future metals/energy successors.

| Partition | Raw-tier SHA256 (from provenance source_checksums) |
|---|---|
| `symbol=ES/year=2020/part-0000.parquet` | `f7ca1f0f79780c3c3ef605be2e25a7687c9254be386292abfec38f5b90ff3135` |
| `symbol=ES/year=2021/part-0000.parquet` | `7e12361f8b32c4765829266e0c29018de3b38f7f1304d945006e5874a6ea8484` |
| `symbol=ES/year=2022/part-0000.parquet` | `882931ba9bb77dd049115e7f4d3275562423b1b38c60d4eea6cf8452932509a4` |
| `symbol=ES/year=2023/part-0000.parquet` | `868890f13064b56fd1d1f5107984d7fb12923707be2129c2eaf592dbbcff00ed` |
| `symbol=ES/year=2024/part-0000.parquet` | `6984059a5a5a61e4aa6b3a56ff4bacd476e437b238fa3c281d4cd64cdabc2025` |
| `symbol=ES/year=2025/part-0000.parquet` | `2c17021f8ecdf8e64120e0216fc59e3e802756c54e09f4b49607ccf2adfca0bd` |
| `symbol=NQ/year=2020/part-0000.parquet` | `8e12491812668ea5529d47f88293545a45a0d8d87db996ace5d7ae0dbbb95bad` |
| `symbol=NQ/year=2021/part-0000.parquet` | `701d2b8c13c0e746d3cac8cad6fbd05e178b672ca5c2218fbfb8939051dfab6c` |
| `symbol=NQ/year=2022/part-0000.parquet` | `cf8a37eb533459ea2d6b7ce0239c8c0af162e9e16d2658bc0b5141a7d827a946` |
| `symbol=NQ/year=2023/part-0000.parquet` | `173981a63165da0b46e1f7cb02e6ae028c815f6f4fd5d5d40d71b53948d8de7a` |
| `symbol=NQ/year=2024/part-0000.parquet` | `ebc7e3057af4184ae0e36baaf812a27e54a18cc4ed3b3a53369f4145cc9164a2` |
| `symbol=MGC/year=2015/part-0000.parquet` | `bd56b383572c1a07cf726285daaae0f76d89ad9d5bf4f451397c6a512d0c2a5d` |
| `symbol=MGC/year=2016/part-0000.parquet` | `78bb8a95fee8e48ac71c97f96475280dfa38affc5141f4e85e68582c1348e75d` |
| `symbol=MGC/year=2017/part-0000.parquet` | `eeca22d447d7a85d0e322e42b319006c366557ad06de3ba08d23b621a8b39b82` |
| `symbol=MGC/year=2018/part-0000.parquet` | `33e447da151e909fe8bf2fa8694c9ab814319aa33e3567c5a6ed2dd3c9a97d5e` |
| `symbol=MGC/year=2019/part-0000.parquet` | `ea6f76bd42eada73451b5cbb186ce8250f4697c0b3ab8bfd0145e5251869ad20` |
| `symbol=MGC/year=2020/part-0000.parquet` | `24998e352890f681d3020f477701af359f327dcddbdf17485b7a2ac7fcb9cc01` |
| `symbol=MGC/year=2021/part-0000.parquet` | `18bd7fd3e4cd22206954055bf553dc93425f64a0049539221496c6b6186ee1a2` |
| `symbol=MGC/year=2022/part-0000.parquet` | `7b1e00958eb288b8690e3bc4057260634b90aeb6cb6573c36df44b0514f82577` |
| `symbol=MGC/year=2023/part-0000.parquet` | `f3904bfc9f0feb5b8ba5975dbb3f658bd345211459643f556d4a91acd7d000d1` |
| `symbol=MGC/year=2024/part-0000.parquet` | `e93a97720caee777a97eaee4c7b933c11bf0b5ed32cf28b362d5b52c9b82af85` |
| `symbol=MGC/year=2025/part-0000.parquet` | `0dbf63e24d0c40e38101fb43bd69dbfaf98da775474460475ac3cae5d8758c18` |
| `symbol=SIL/year=2015/part-0000.parquet` | `983efa6494bc2f35112206eaa02a23008346ecfef7461825fd5a890fa0f096e6` |
| `symbol=SIL/year=2016/part-0000.parquet` | `4eb03aa788ecc463034d9e2f1893ea024734da6e6195b3c30986003e4bf7d83d` |
| `symbol=SIL/year=2017/part-0000.parquet` | `7171a52cb3dc02ca08581bc6633746a36b4fc0bcdcc7329e3d25eaff526e1cc6` |
| `symbol=SIL/year=2018/part-0000.parquet` | `0ea6080bab6a5558b3955c6b322312abcaf29c590c0d19e1d9d0f673be5b4a71` |
| `symbol=SIL/year=2019/part-0000.parquet` | `0d810871920811d3aef0b4164930cf9fac4bdf62c8df757d9652634417cb1b91` |
| `symbol=SIL/year=2020/part-0000.parquet` | `b2b122a86cba614b4bc8a23604f7ca6aa3e667f234f4178ce3a7339ea4423fb8` |
| `symbol=SIL/year=2021/part-0000.parquet` | `2604b54be97800bddf6958f5fe402c5d2d8560a88706af79d493f615fe3018fd` |
| `symbol=SIL/year=2022/part-0000.parquet` | `9bccbf2c0a517ec155fa80c0931fd9a8830699208d4b27b748370fae7e8fdc94` |
| `symbol=SIL/year=2023/part-0000.parquet` | `167806e6d330fb92972a98754603dffc6e2c1e91f54ecbef64c02ee96b633ea0` |
| `symbol=SIL/year=2024/part-0000.parquet` | `4e761c3d949685d4655ec98f3ee1380ea16ebae89bba6b921cd8a5bdbc10f24b` |
| `symbol=SIL/year=2025/part-0000.parquet` | `645931c1dae1ae5a58f8c992a81a44110a16574ac36e3054ee06d71b8227111c` |

### Pilot ledger

H062 has **no pilot ledger**. The hypothesis is a fresh pre-registration with no operator-manual discretionary baseline (distinguishing it from H055, where the pilot ledger drives Component 1 trend-gate selection). Power calibration per design.md §9 uses a pre-empirical simulation against synthetic Donchian-channel-breakout return distributions, NOT a pilot ledger.

## Hard-fail check at `running`

[design.md](design.md) §2 binds the running-time SHA256 to equal the `designed`-time SHA256 in this file (the post-running pinned H062-universe-subset SHA over the 33-partition H062 universe). Mismatch triggers `archive(null, data-violation)` per design.md §10 and halts the run before the first walk-forward fold is fit.

## Cross-hypothesis fit-set isolation properties (load-bearing for H062 v1)

The H062 v1 calibration holdout (2015-01-01 → 2019-12-31) is jointly chosen to be DISJOINT from the **test folds** of all preceding hypotheses on this substrate. The H062 IS window (2020-01-01 → 2023-12-31) is a SUPERSET of prior fit windows (deliberate; documented below). The H062 OOS test window overlaps prior OOS windows (acknowledged honestly under same-substrate-different-signal-class framing).

| Hypothesis | Train / IS | Val | OOS test | Overlap with H062 calibration holdout (2015-2019) | Overlap with H062 IS (2020-2023) | Overlap with H062 OOS (2024-2025) |
|---|---|---|---|---|---|---|
| H050 | 2020-2022 (ES + NQ) | (in-test) | 2024-2025 (ES + NQ) | None | **OVERLAPS 2020-2022** | **OVERLAPS 2024-2025**. H062 evaluates intraday Donchian-channel breakout. Different signal class than HMM-gated 1-min directional. Reported as `data-overlap-h050-acknowledged`. |
| H052a | 2020-2022 (ES + NQ) | 2023-H1 | 2023-H2 → 2024 (ES + NQ) | None | **OVERLAPS 2020-2023** | **OVERLAPS 2024**. Different signal class than HMM-gated first-hour ORB. Reported as `data-overlap-h052a-acknowledged`. |
| H053 v3 / v4 | 2015-2022 (ES + NQ) | 2023 | 2024-2025 (ES + NQ) | **OVERLAPS 2015-2019 on the pre-Phase-O.0 H055 substrate** — but H053 NEVER scored a test statistic on the 2015-2019 window; H053's calibration role is fit-only. H062's calibration-holdout role is OOS-relative-to-H062 (used only for metals-leg channel-N + k_atr pre-reg, never for H062 OOS evaluation). Disjoint-from-test-fold property holds. | **OVERLAPS 2020-2023** | **OVERLAPS 2024-2025**. Different signal class than multi-timeframe ElasticNet/LightGBM regression. Reported as `data-overlap-h053-acknowledged`. |
| H054 | 2020-2023 (ES + NQ) | (none) | ES 2025-01-01 → 2025-12-03 | None | **OVERLAPS 2020-2023** | **OVERLAPS 2025 ES**. Different signal class than HMM-anti-gated ORB. Reported as `data-overlap-h054-acknowledged`. |
| H055 | 2020-2023 (ES + NQ + MES + MNQ) | (in-IS) | 2024-2025 (ES + NQ + MES + MNQ) | **DISJOINT** (H055 calibration holdout is the same 2015-2019 window; H055 uses it for ID_1*_c selection on side-skew Brier, NOT as a test fold) | **OVERLAPS 2020-2023** (H062 IS superset) | **OVERLAPS 2024-2025**. Different signal class than per-trade wick-rejection mean-reversion. Reported as `data-overlap-h055-acknowledged`. |
| H060 | 2020-2023 ({ES, NQ, MGC, SIL}) | (in-IS) | 2024-2025 ({ES, NQ, MGC, SIL}) | **DISJOINT** for ES + NQ (both H060 and H062 have zero pre-2020 ES/NQ coverage in this substrate); **OVERLAPS for MGC + SIL** (both use 2015-2019 calibration holdout for metals-leg parameter pre-reg). H060 channel-N + k_atr is N/A — H060 is monthly-rebalance TSMOM not channel-breakout. H062's channel-N selection on calibration holdout does NOT leak into H060's signal. | **OVERLAPS 2020-2023** (both H060 IS and H062 IS share the same window) | **OVERLAPS 2024-2025**. Different signal class than daily-cadence TSMOM monthly rebalance. Reported as `data-overlap-h060-acknowledged`. |

**Load-bearing isolation properties for H062 v1**:

1. **Calibration-holdout fit-set isolation**: H062 calibration holdout (2015-01-01 → 2019-12-31, MGC + SIL only) is DISJOINT from the **test folds** of all preceding hypotheses. MGC + SIL data in this window has only been used by H060 (also calibration-holdout role; different signal mechanism) and never as a test fold. The disjoint-from-test-fold property holds.
2. **IS-superset acknowledgment**: H062 IS (2020-2023) is a SUPERSET of prior hypothesis IS windows. Per the H055 precedent, this is methodologically defensible — H062's signal class (intraday Donchian-channel breakout) is structurally distinct from all prior signal classes, and the H062 parameter fit (channel-N, k_atr, kelly_multiplier, trend-gate ID) does not consume per-fold information from prior fits. Reported as `is-superset-prior-fits-acknowledged` annotation.
3. **OOS overlap acknowledgment**: H062 OOS overlaps the OOS test folds of H050, H052a, H053, H054, H055, and H060. The overlap is methodologically defensible under different-signal-class-on-shared-substrate framing but is **acknowledged honestly rather than justified**. Reported as `data-overlap-h050-h052a-h053-h054-h055-h060-acknowledged` KPI annotation per design.md §10.

## Energy / metals coverage notes

H062 v1 universe is {ES, NQ, MGC, SIL}. Full-size NYMEX WTI Light Sweet Crude (CL) is deferred to **H061** per the H060 v2 substrate-extension cycle (CL extraction at ~$240 USD per the 2026-05-12 Databento cost-dossier exceeded the operator's $80 budget ceiling at Phase O.0). Micro WTI (MCL) is on disk in the post-Phase-O.0 substrate (2021-2025 partitions) but excluded from H062 v1 because the 2021-07-12 contract-inception date precludes the 2015-2019 calibration holdout for the metals/energy leg.

Future-extension follow-up: `P1-H062-V2-WITH-CL-MCL-EXTEND` — (a) extend universe with CL via the H061 substrate extraction; (b) re-calibrate channel-N + k_atr per Donchian asymmetry between equity-index and energy substrates on the per-asset calibration holdout (preserving the disjoint-from-test-fold isolation property where possible); (c) author H062-successor design.md (e.g., H062b) with the extended universe and a new substrate-binding addendum.

## Pre-IS sample (for §9 power calibration)

H062 design.md §9 power calibration uses a **synthetic-distribution Monte Carlo** anchored on the per-symbol bar-volatility empirical distribution from the 2015-2019 (MGC + SIL) and 2020-2023 IS (all four symbols) folds. Disjoint from OOS test fold (2024-2025) by construction. Pilot ledger absence per §"Pilot ledger" above. Full derivation in design.md §9 + the (deferred) `P1-H062-POWER-SIMULATION-EXECUTE` script.
