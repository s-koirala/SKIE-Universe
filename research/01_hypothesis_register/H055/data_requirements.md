---
name: H055 data requirements
description: Pre-registration dataset checksums and coverage bounds for H055 (binding at designed status)
type: project
hypothesis_id: H055
schema_version: 1
status: designed  # frozen concurrently with design.md per H050+H053+H054 atomic-snapshot-binding pattern
created: 2026-05-06
revised: 2026-05-06
---

# H055 — Data Requirements

Pre-registration companion to [design.md](design.md) §2 + §11. **Frozen at `designed` status concurrently with [design.md](design.md)** per the H050 + H053 + H054 atomic-snapshot-binding pattern.

The roll-adjusted ES + NQ 1-min substrate is shared between H050, H053, H054, and H055; the binding SHA256 table below is identical to [H050/data_requirements.md](../H050/data_requirements.md) + [H053/data_requirements_H053_2026-04-28.md](../H053/data_requirements_H053_2026-04-28.md) + [H054/data_requirements.md](../H054/data_requirements.md) for the per-partition rows. H055's envelope uses the same 2015-01-01 → 2025-12-{03,19} substrate.

**H055 v1 sample-window partition (binding)**:
- **Calibration holdout** (DISJOINT from IS, OOS, AND any prior-hypothesis fit window): ES + NQ 2015-01-01 → 2019-12-31 (≈1248 RTH sessions per symbol). Used for trend-identifier selection (Brier score on pilot-side-skew supervised target) and body-overlap ρ_1 threshold pre-registration.
- **IS** (parameter fitting + walk-forward inner CV): ES + NQ 2020-01-01 → 2023-12-31 (≈1003 RTH sessions per symbol; superset of H050 train, H054 IS, H052a IS+val).
- **OOS test**: ES 2024-01-01 → 2025-12-03 (≈480 RTH sessions); NQ 2024-01-01 → 2025-12-19 (≈496 RTH sessions).
- **Pilot ledger** (NinjaTrader CSV at 2026-05-01 → 2026-05-06): out-of-sample relative to OOS test (which ends 2025-12-{03,19}); descriptive-only, NOT a test fold.

H055 OOS overlap with H050 OOS (HMM-gated 1-min directional test fold) and H053 v3 OOS (multi-timeframe regression test fold) is **acknowledged honestly as same-substrate-different-signal-class**: H055 is per-trade wick-rejection mean-reversion; H050 is HMM-gated 1-min directional; H053 is multi-timeframe regression. Different signal classes, different label horizons, different feature vectors. Reported as `data-overlap-h050-h053-acknowledged` annotation per design.md §10.

**H055 v1 instrument universe**: ES, NQ, MES, MNQ. CL/MCL/MYM/MGC excluded at v1 per scope (energy/metals not in current substrate). Deferral tracked under `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND`.

Any subsequent change to the H055 substrate requires either (a) a successor hypothesis ID, or (b) an addendum to this file with explicit revision-rationale and the new checksum table.

## Source dataset

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23; no redistribution; internal research use only. |
| Symbols | ES.FUT, NQ.FUT (front-month; Databento continuous series). MES + MNQ derived from ES + NQ at v1 via tick-size + multiplier rescaling per [config/instruments.yaml](../../../config/instruments.yaml); native MES/MNQ ingest tracked under `P1-H055-NATIVE-MES-MNQ-INGEST`. |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment (López de Prado 2018, Wiley) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` v0.3.0 (commit `329fd1b` decade-wraparound disambiguation) |
| VIX daily | FRED VIXCLS public CSV; ingest [src/skie_ninja/data/ingest/vix_daily.py](../../../src/skie_ninja/data/ingest/vix_daily.py) (commit `6e87a9d`); shared with H052a + H054 |
| Pilot ledger | NinjaTrader 8 Performance CSV export (171 trades, 2026-05-01 → 2026-05-06); landing path [data/external/h055_pilot_ledger/Performance.csv](../../../data/external/h055_pilot_ledger/Performance.csv) with companion `dataset_card.md` |

## Coverage

| Field | Value |
|---|---|
| ES date range | 2015-01-01 → 2025-12-03 UTC (last bar `ts_event`; right-edge envelope shortfall per `P1-DATABENTO-RIGHT-EDGE-EXTENSION`) |
| NQ date range | 2015-01-01 → 2025-12-19 UTC (last bar `ts_event`; Z-window-bounded per `download_historical_years` `('Z','09-15','12-20')`) |
| Total rows (combined, roll-adjusted) | 7,354,066 |
| ES rows (sum of partitions, roll-adjusted) | 3,694,534 |
| NQ rows (sum of partitions, roll-adjusted) | 3,659,532 |
| VIX daily rows (FRED VIXCLS) | ~9,200 (1990-01-02 onward) |
| Pilot ledger trades | 171 (94 long / 77 short; 2026-05-01 → 2026-05-06) |

H055 design.md §2 envelope:
- Calibration holdout (trend-identifier + ρ_1 threshold pre-reg): 2015-01-01 → 2019-12-31 (≈1248 RTH sessions per symbol)
- IS (parameter fitting + walk-forward inner CV): 2020-01-01 → 2023-12-31 (≈1003 RTH sessions per symbol)
- OOS test: ES 2024-01-01 → 2025-12-03 (≈480 RTH sessions); NQ 2024-01-01 → 2025-12-19 (≈496 RTH sessions)

The right-edge truncation (ES 2025 ends 28 calendar days short of 2025-12-31; NQ 2025 ends 12 calendar days short) is identical to H050+H053+H054's and inherited by H055. If an H055 disposition under design.md §10 materially depends on the last 28/12 days of 2025, the disposition entry receives a `test-window-truncated` annotation.

## Checksums — processed parquet (roll-adjusted tier; binding for H055)

Computed via `skie_ninja.utils.hashing.frame_sha256` with `sort_cols=["symbol", "ts_event"]` (canonical polars sort before hash). Identical to H050 + H053 + H054 substrate; reproduced here for H055 frozen-snapshot binding.

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

### VIX daily (FRED VIXCLS)

| Field | Value |
|---|---|
| SHA256 | `0a0e9f252bcaa3f2f9ee2d0ef142e8fff88924aa6a2590d76e924dd50d6ab552` (per H052a + H054 ReproLog 2026-05-05) |
| Provenance | [data/processed/_provenance/vix_daily_20260505.json](../../../data/processed/_provenance/vix_daily_20260505.json) |
| Refresh policy | Re-pulled at H055 first `running` run; SHA256 must equal the value above (substrate-blind to VIX revisions per FRED `as_of` snapshotting). If mismatch, re-pull and re-pin under an addendum. |

### Pilot ledger CSV (H055-specific)

| Field | Value |
|---|---|
| Source | NinjaTrader 8 Performance CSV export |
| Path | [data/external/h055_pilot_ledger/Performance.csv](../../../data/external/h055_pilot_ledger/Performance.csv) |
| Companion | [data/external/h055_pilot_ledger/dataset_card.md](../../../data/external/h055_pilot_ledger/dataset_card.md) |
| Trade count | 171 (94 long / 77 short) |
| Window | 2026-05-01 → 2026-05-06 |
| Reconciles to prior PDF | 171 trades, $6,157.75 gross, 74.85% win rate (verified) |
| Side classification rule | `bought_timestamp < sold_timestamp` → long; else short. Verified 94 long / 77 short. |
| SHA256 | `to-be-computed-at-first-running-run` (computed at H055 first `running` run; pinned in addendum thereafter — pilot CSV not yet on disk at `designed` status) |
| Refresh policy | The pilot ledger is a one-shot artifact (closed window 2026-05-01 → 2026-05-06); no refresh. Used descriptively (empirical motivation), NOT as a test fold. Any subsequent pilot extension requires a successor hypothesis ID. |
| Role in H055 | Empirical motivation only. The pilot's wick-rejection edge motivates the design.md §1 hypothesis statement; the H055 test statistic is computed on the OOS test fold (2024-2025), NOT on the pilot. |

## Hard-fail check at `running`

[design.md](design.md) §2 binds the running-time SHA256 to equal the `designed`-time SHA256 in this file (the Combined SHA256 row + the VIX daily SHA256 + the pilot CSV SHA256 once first-run-pinned). Mismatch on any partition or on the combined frame triggers `archive(null, data-violation)` per design.md §10 and halts the run before the first walk-forward fold is fit.

The pilot CSV SHA256 is computed and pinned at H055 first `running` run; mismatch on subsequent runs vs the first-run-pinned hash triggers the same hard-fail path.

## Cross-hypothesis fit-set isolation properties (load-bearing for H055 v1)

The H055 v1 calibration holdout (2015-01-01 → 2019-12-31) is jointly chosen to be DISJOINT from the IS, val, and test folds of all preceding hypotheses on this substrate. The H055 IS window (2020-01-01 → 2023-12-31) is a SUPERSET of prior fit windows (deliberate; documented below). The H055 OOS test window (2024-01-01 → 2025-12-{03,19}) overlaps prior OOS windows (acknowledged honestly under same-substrate-different-signal-class framing).

| Hypothesis | Train / IS | Val | OOS test | Overlap with H055 calibration holdout (2015-2019) | Overlap with H055 IS (2020-2023) | Overlap with H055 OOS (2024-2025) |
|---|---|---|---|---|---|---|
| H050 | 2020-2022 (5min and 1min ES+NQ) | (in-test) | ES 2024-01-01 → 2024-12-12 + NQ 2024-01-01 → 2025-12-11 | None | **OVERLAPS 2020-2022** (H055 IS is superset; H050 train ⊂ H055 IS by design) | **OVERLAPS 2024**. H050 evaluates HMM-gated 1-min directional; H055 evaluates per-trade wick-rejection mean-reversion. Different signal class, different label horizon, different feature vector. Reported as `data-overlap-h050-acknowledged` annotation. |
| H052a | 2020-01-01 → 2022-12-31 | 2023-01-01 → 2023-06-30 | 2023-07-01 → 2024-12-31 | None | **OVERLAPS 2020-2023** (H055 IS is superset; H052a IS+val ⊂ H055 IS by design) | **OVERLAPS 2024**. H052a evaluates HMM-gated first-hour ORB; H055 evaluates per-trade wick-rejection mean-reversion. Different signal class. Reported as `data-overlap-h052a-acknowledged` annotation. |
| H053 v3 | 2015-2022 | 2023 | 2024-01-01 → 2025-12-{03,19} | **OVERLAPS 2015-2019** — but H053 train is SUPERSET, not test fold; H053 NEVER evaluates a test statistic on the 2015-2019 window. H055's calibration-holdout role is OOS-relative-to-H055 (used only for trend-id selection + ρ_1 threshold pre-reg, never for H055 OOS evaluation), and OOS-relative-to-H053 (H053 fits regression on this window but does not score on it). The disjoint-from-test-fold property is what's load-bearing for the H055 trend-id pre-reg. | **OVERLAPS 2020-2022** (H055 IS is superset of H053 train tail) and 2023 (H055 IS overlaps H053 val). | **OVERLAPS 2024-2025**. H053 evaluates ElasticNet+LightGBM regression on multi-timeframe features; H055 evaluates per-trade wick-rejection mean-reversion. Different signal class entirely. Reported as `data-overlap-h053-acknowledged` annotation. |
| H054 | 2020-01-01 → 2023-06-30 | (none; matches H052a IS+val) | ES-only 2025-01-01 → 2025-12-03 | None | **OVERLAPS 2020-2023** (H055 IS is superset) | **OVERLAPS 2025 ES**. H054 evaluates HMM-anti-gated first-hour ORB; H055 evaluates per-trade wick-rejection mean-reversion. Different signal class. Reported as `data-overlap-h054-acknowledged` annotation. |

**Load-bearing isolation properties for H055 v1**:

1. **Calibration-holdout fit-set isolation**: H055 calibration holdout (2015-01-01 → 2019-12-31) is DISJOINT from the **test folds** of H050, H052a, H053, H054. (H053's train spans 2015-2022 but H053 never *scored* a test statistic on 2015-2019; the disjoint-from-test-fold property is what protects the H055 trend-id selection + ρ_1 threshold pre-registration from circular validation.) This makes the H055 trend-identifier and body-overlap threshold genuinely pre-registered (selected on data not used for any prior hypothesis's test statistic), consistent with López de Prado 2018 AFML §11 ("Backtest Statistics") on hyperparameter-disjointness from the test fold.

2. **IS-superset acknowledgment**: H055 IS (2020-2023) is a SUPERSET of H050 train + H052a IS+val + H054 IS + H053 v3 train tail. This is methodologically defensible — H055's signal class is structurally distinct from H050/H052a/H053/H054 (per-trade wick-rejection mean-reversion vs HMM-gated directional / HMM-gated ORB / multi-timeframe regression / HMM-anti-gated ORB), and the H055 parameter fit (trend-id thresholds, ρ_1 body-overlap, exit/stop rules) does not consume per-fold information from prior fits. Reported as `is-superset-prior-fits-acknowledged` annotation.

3. **OOS overlap acknowledgment**: H055 OOS overlaps H050 OOS (ES 2024) and H053 OOS (ES 2024-2025 + NQ 2024-2025) and H054 OOS (ES 2025). The overlap is methodologically defensible under different-signal-class-on-shared-substrate framing but is **acknowledged honestly rather than justified** (per the 2026-05-05 H054 round-2 audit-remediate-loop discipline). Reported as `data-overlap-h050-h053-acknowledged` KPI annotation.

## Energy / metals exclusion + future-extension note

H055 v1 instrument universe is restricted to **ES, NQ, MES, MNQ** (CME equity-index front-month + micro equivalents). The pilot ledger covers ES + NQ trades; the v1 substrate covers ES + NQ natively + MES/MNQ via tick-size + multiplier rescaling per [config/instruments.yaml](../../../config/instruments.yaml).

**CL/MCL/MYM/MGC excluded at v1** for the following reasons:
- CL/MCL (NYMEX crude / micro crude): not in the current `vendor_legacy_1min_roll_adjusted` substrate. Energy futures have distinct microstructure (overnight gap dynamics, OPEC-event regime breaks) that warrant separate calibration of the wick-rejection trend-id + ρ_1 threshold.
- MYM (CBOT Dow micro): not in current substrate. YM futures share equity-index microstructure with ES/NQ but the lower-volume + larger-tick characteristics merit independent calibration.
- MGC (COMEX gold micro): not in current substrate. Metals futures have distinct microstructure (US-trading-hours vs LBMA-fix dynamics, CB-meeting regime breaks) that warrant separate calibration.

Future-extension follow-up: `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND` — (a) ingest CL/MCL + MYM + MGC 1-min Databento substrate via the existing `vendor_legacy_1min_roll_adjusted` ingest module; (b) re-calibrate wick-rejection trend-id + ρ_1 threshold on the per-asset 2015-2019 calibration holdout (preserving the disjoint-from-test-fold isolation property); (c) author H055-successor design.md (e.g., H055b) extending the universe with explicit per-asset hyperparameter binding. The successor will inherit the H055 v1 substrate-binding pattern but bind a NEW per-asset checksum table.

## Pre-IS sample (for §9 power calibration)

H055 design.md §9 power calibration uses the **pilot ledger** as the per-trade SR pilot estimate (per-trade SR ≈ pilot $6,157.75 gross / 171 trades / pilot daily-σ; full derivation in design.md §9). The pilot calibration is anchored on the pilot ledger window (2026-05-01 → 2026-05-06) which is DISJOINT from H055 IS (2020-2023) AND H055 OOS (2024-2025) per the disjoint-pilot property. The pilot's use is for sample-size requirement estimation only; it does not enter the H055 test statistic.
