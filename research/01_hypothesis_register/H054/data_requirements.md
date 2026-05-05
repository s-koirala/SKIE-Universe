---
name: H054 data requirements
description: Pre-registration dataset checksums and coverage bounds for H054 (binding at designed status)
type: project
hypothesis_id: H054
status: designed  # Round-2+3 audit-remediate-loop ACCEPT 2026-05-05 concurrently with design.md
created: 2026-05-05
revised: 2026-05-05
---

# H054 — Data Requirements

Pre-registration companion to [design.md](design.md) §2 and §11. **Frozen at `designed` status concurrently with [design.md](design.md)** per the H050 + H053 atomic-snapshot-binding pattern (departs from H052a's binding-at-running pattern).

The roll-adjusted ES + NQ 1-min substrate is shared between H050, H053, and H054; the binding SHA256 table below is identical to [H050/data_requirements.md](../H050/data_requirements.md) and [H053/data_requirements_H053_2026-04-28.md](../H053/data_requirements_H053_2026-04-28.md) for the per-partition rows. H054's envelope uses the same 2015-01-01 → 2025-12-{03,20} substrate.

**H054 v1 sample-window partition (UPDATED 2026-05-05 Round-2 audit-remediate-loop per F-Q-1 + F-Q-6 fixes)**:
- IS: ES + NQ 2020-01-01 → 2023-06-30 (matches H052a IS+val EXACTLY)
- DELIBERATELY-UNUSED: 2023-07-01 → 2024-12-31 (the H052a OOS window — neither IS, nor val, nor test for H054 v1)
- OOS test: ES-only 2025-01-01 → 2025-12-03 (NQ 2025 EXCLUDED at v1 per F-Q-6 design-time-knowledge-contamination fix)

Any subsequent change to the H054 substrate requires either (a) a successor hypothesis ID, or (b) an addendum to this file with explicit revision-rationale and the new checksum table.

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
| VIX daily | FRED VIXCLS public CSV; ingest [src/skie_ninja/data/ingest/vix_daily.py](../../../src/skie_ninja/data/ingest/vix_daily.py) (commit `6e87a9d`); shared with H052a |

## Coverage

| Field | Value |
|---|---|
| ES date range | 2015-01-01 → 2025-12-03 UTC (last bar `ts_event`; right-edge envelope shortfall per `P1-DATABENTO-RIGHT-EDGE-EXTENSION`) |
| NQ date range | 2015-01-01 → 2025-12-19 UTC (last bar `ts_event`; Z-window-bounded per `download_historical_years` `('Z','09-15','12-20')`) |
| Total rows (combined, roll-adjusted) | 7,354,066 |
| ES rows (sum of partitions, roll-adjusted) | 3,694,534 |
| NQ rows (sum of partitions, roll-adjusted) | 3,659,532 |
| VIX daily rows (FRED VIXCLS) | ~9,200 (1990-01-02 onward) |

H054 design.md §2 envelope (post-Round-2 audit fix):
- IS (HMM fit + label-cfg search): 2020-01-01 → 2023-06-30 (≈878 RTH sessions per symbol; matches H052a IS+val EXACTLY)
- DELIBERATELY-UNUSED: 2023-07-01 → 2024-12-31 (the H052a OOS window; H054 v1 does NOT touch this data in any phase)
- OOS test (ES-only): 2025-01-01 → 2025-12-03 (≈230 RTH sessions; ES-only at v1 per F-Q-6)

The right-edge truncation (ES 2025 ends 28 calendar days short of 2025-12-31) is identical to H050+H053's and inherited by H054. If an H054 disposition under design.md §10 materially depends on the last 28 days of 2025, the disposition entry receives a `test-window-truncated` annotation.

## Checksums — processed parquet (roll-adjusted tier; binding for H054)

Computed via `skie_ninja.utils.hashing.frame_sha256` with `sort_cols=["symbol", "ts_event"]` (canonical polars sort before hash). Identical to H050 + H053 substrate; reproduced here for H054 frozen-snapshot binding.

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
| SHA256 | `0a0e9f252bcaa3f2f9ee2d0ef142e8fff88924aa6a2590d76e924dd50d6ab552` (per H052a ReproLog 2026-05-05) |
| Provenance | [data/processed/_provenance/vix_daily_20260505.json](../../../data/processed/_provenance/vix_daily_20260505.json) |
| Refresh policy | Re-pulled at H054 first `running` run; SHA256 must equal the value above (substrate-blind to VIX revisions per FRED `as_of` snapshotting). If mismatch, re-pull and re-pin under an addendum. |

## Hard-fail check at `running`

[design.md](design.md) §2 binds the running-time SHA256 to equal the `designed`-time SHA256 in this file (the Combined SHA256 row + the VIX daily SHA256). Mismatch on any partition or on the combined frame triggers `archive(null, data-violation)` per design.md §10 and halts the run before the first walk-forward fold is fit.

## H052a-OOS-isolation + H050-OOS-isolation properties (load-bearing for H054 v1)

UPDATED 2026-05-05 Round-2 audit-remediate-loop per F-Q-1 + F-Q-6 fixes — the previous "same-substrate-different-test-statistic" framing was insufficient; the load-bearing isolation is now achieved by EXCLUSION of overlapping windows from H054 v1, not by JUSTIFICATION of overlap.

The H054 v1 IS window (2020-01-01 → 2023-06-30) and OOS test window (ES-only 2025-01-01 → 2025-12-03) are jointly chosen to be DISJOINT from the test folds of all preceding hypotheses on this substrate.

| Hypothesis | Train / IS | Val | OOS test | Overlap with H054 v1 IS | Overlap with H054 v1 OOS (ES 2025) |
|---|---|---|---|---|---|
| H050 | 2020-2022 (5min and 1min ES+NQ) | (in-test) | ES 2024-01-01 → 2024-12-12 + NQ 2024-01-01 → 2025-12-11 | None | None (H050 ES test ends 2024-12-12; H050 NQ test extends into 2025 but NQ is excluded from H054 v1 OOS per F-Q-6) |
| H052a | 2020-01-01 → 2022-12-31 | 2023-01-01 → 2023-06-30 | 2023-07-01 → 2024-12-31 | **EXACT MATCH** to H054 IS by design (the F-Q-1 fix) | None (H052a OOS ends 2024-12-31) |
| H053 | 2015-2022 | 2023 | 2024-01-01 → 2025-12-{03,19} | None | **OVERLAPS Jan-Dec 2025**. H053 evaluates ElasticNet+LightGBM regression on multi-timeframe features; H054 v1 evaluates anti-gate first-hour ORB. Different signal class entirely; same-substrate-different-feature-vector-different-label per the load-bearing isolation framing. **Acknowledged double-dip risk**: the H054 author had visibility into H053 v3+v4 KPI report cards (emitted 2026-05-03) at H054 design-time; the design-time-knowledge contamination is bounded because H053's signal class (regression on 38 multi-timeframe features for raw 09:45→10:30 ET log-return predictand) is structurally distinct from H054 (binary HMM regime indicator × first-hour ORB long-only). Reported as `data-overlap-h053-acknowledged` annotation. |

**Load-bearing isolation properties for H054 v1**:

1. **H052a fit-set isolation**: H054 IS is EXACT-MATCH to H052a IS+val (deliberate). H054 OOS is EXCLUDED from any window H052a evaluated on (the 2023-07-01 → 2024-12-31 H052a OOS is DELIBERATELY-UNUSED). This eliminates the F-Q-1 leakage.

2. **H050 fit-set isolation**: H054 OOS (ES 2025-01-01 → 2025-12-03) is DISJOINT from H050 ES test fold (2024-01-01 → 2024-12-12). NQ is excluded entirely from H054 v1 to address the H050 NQ test overlap into 2025 (F-Q-6 fix).

3. **H053 fit-set partial-overlap acknowledgment**: H054 OOS overlaps H053 OOS on ES 2025; this is documented and reported as `data-overlap-h053-acknowledged` KPI annotation. The overlap is methodologically defensible under different-signal-class-on-shared-substrate framing but is acknowledged honestly rather than justified.

## Pre-IS sample (for §9 power calibration)

H054 design.md §9 power calibration uses the H052a OOS empirical Sharpe of the gated-out subset as the per-session SR pilot estimate (per-session SR ≈ 0.05-0.10 reconstructed from H052a KPI report card v1 §3 + §6 tables). The pilot calibration is **anchored on H052a OOS, not H054 OOS** — the pilot sample is the H052a OOS test fold (2023-H2 + 2024) which is DISJOINT from H054 OOS (2025) per the isolation property above. The pilot's use is for sample-size requirement estimation only; it does not enter the H054 test statistic.
