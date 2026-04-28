---
name: H053 data requirements
description: Pre-registration dataset checksums and coverage bounds for H053 (binding at designed status)
type: project
hypothesis_id: H053
status: designed
created: 2026-04-28
revised: 2026-04-28
---

# H053 — Data Requirements

Pre-registration companion to [design.md](design.md) §2 and §11. **Frozen at `designed` status on 2026-04-28**, not at the first `running` run — this departs from H052a's binding-at-running pattern and mirrors H050's post-Cell-I atomic re-freeze (commit `029f85d`) per the Round-1 quant-auditor finding on snapshot-binding integrity.

The roll-adjusted ES + NQ 1-min substrate is shared between H050 and H053; the binding SHA256 table below is identical to [H050/data_requirements.md](../H050/data_requirements.md) for the per-partition rows. H053's envelope uses the same 2015-01-01 → 2025-12-{03,20} train+val+test span as H050; H053's specific design.md §2 sample-window partition (IS 2015-2022, val 2023, OOS 2024-2025) lies fully inside the substrate (modulo the same 2025 right-edge truncation tracked under `P1-DATABENTO-RIGHT-EDGE-EXTENSION` and inherited by H053).

Any subsequent change to the H053 substrate requires either (a) a successor hypothesis ID, or (b) an addendum to this file with explicit revision-rationale and the new checksum table.

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
| ES date range | 2015-01-01 → 2025-12-03 UTC (last bar `ts_event`; substrate end-of-2025 truncation pre-disclosed in [H050 data_requirements.md](../H050/data_requirements.md) §Coverage; right-edge envelope shortfall per `P1-DATABENTO-RIGHT-EDGE-EXTENSION`) |
| NQ date range | 2015-01-01 → 2025-12-19 UTC (last bar `ts_event`; Z-window-bounded per `download_historical_years` `('Z','09-15','12-20')`) |
| Total rows (combined, roll-adjusted) | 7,354,066 |
| ES rows (sum of partitions, roll-adjusted) | 3,694,534 |
| NQ rows (sum of partitions, roll-adjusted) | 3,659,532 |

H053 design.md §2 envelope:
- IS / train: 2015-01-01–2022-12-31
- val: 2023-01-01–2023-12-31
- OOS / test: 2024-01-01–2025-12-{03 ES, 20 NQ}

The right-edge truncation (ES 2025 ends 28 calendar days short of 2025-12-31; NQ 2025 ends 12 calendar days short) is identical to H050's and inherited by H053. If an H053 disposition under [design.md](design.md) §10 materially depends on the last 12-28 days of 2025, the disposition entry receives a `test-window-truncated` annotation.

## Checksums — processed parquet (roll-adjusted tier; binding for H053)

Computed via `skie_ninja.utils.hashing.frame_sha256` with `sort_cols=["symbol", "ts_event"]` (canonical polars sort before hash). These are the binding dataset checksums for H053 reproducibility.

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

## Hard-fail check at `running`

[design.md](design.md) §2 binds the running-time SHA256 to equal the `designed`-time SHA256 in this file (the Combined SHA256 row above). Mismatch on any partition or on the combined frame triggers `archive(null, data-violation)` per design.md §10.1.1 and halts the run before the first walk-forward fold is fit.

## Pre-IS pilot window (for §9 power calibration)

[design.md](design.md) §9 power-calibration pins `ar1_rho_pilot` and `excess_kurtosis_pilot` from a pre-IS window outside the IS fold. Pilot window: 2010-01-01 → 2014-12-31. **The pilot window is NOT covered by the substrate above** (which starts 2015-01-01). Three options at running time, pre-registered here in priority order:

1. (Preferred) Acquire a pre-IS pilot window from Databento for ES + NQ 2010-2014 in a separate pull, with its own SHA256 captured to a successor `data_requirements_H053_pilot_*.md` companion. Cost estimate to be recorded under follow-up `P1-H053-PILOT-WINDOW-DATABENTO`.
2. (Fallback) Use the project's existing prototype-tier ES vendor-skie-ninja-legacy 5-min substrate (2020-2025) intersected with a pre-2015 prototype window if available; flag any pilot fitted from inside the IS fold as a deviation from this design.md and report `archive(null, pilot-from-IS-fold)` per §10.1 *if* `s_min` had to be IS-derived. (This fallback is documented as a contingency, not an admissible primary path.)
3. (Last resort) Pin `ar1_rho_pilot = 0.0` and `excess_kurtosis_pilot = 3.0` (Gaussian iid) and document the conservative-assumption deviation in §10.1 disposition. The result of `s_min` under this conservative assumption is an upper bound on the true `s_min` for power; an underpowered run under this prior is genuinely underpowered.

Option 1 is the binding pre-reg target; options 2 and 3 are contingency paths with explicit disposition annotations.
