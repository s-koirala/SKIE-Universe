---
name: H067 data requirements
description: Pre-registration dataset checksums and coverage bounds for H067 (binding at designed status; inherits H065 + H062 substrate)
type: project
hypothesis_id: H067
schema_version: 1
status: designed
created: 2026-05-19
---

# H067 — Data Requirements

Pre-registration companion to [design.md](design.md) §2 + §16. **Frozen at `designed` status concurrently with [design.md](design.md)** per the H050/H053/H054/H055/H060/H062/H065 atomic-snapshot-binding pattern.

## H067 substrate inheritance from H065 + H062

H067 is the N-lot cost-light genetic successor of [H065 v2 M_inf-SIL](../H065/design.md) per [design.md §1](design.md) + §17.1 genetic-successor cross-citation. The substrate is **identical to H065's universe restricted to SIL standalone** on the canonical post-Phase-O.10 main-HEAD substrate.

## Source dataset (v1 binding)

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23 + 2026-05-12 + 2026-05-15 (Phase O.3 2026-H1 extension); no redistribution; internal research use only. |
| Symbol at v1 | SIL.FUT (Micro Silver; COMEX-on-CME-Globex; 1000 troy oz; tick_size 0.005 → tick_value $5.00; front-month; Databento continuous series via parent-symbology). Coverage extends through 2026-05-15 OOS window per Phase O.3 + Phase O.10 backfill |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/SIL_*` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/symbol=SIL/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment ([López de Prado 2018, Wiley, ISBN-13 978-1119482086](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086), *practitioner*) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` |
| Binding `output_frame_sha256` (canonical post-Phase-O.10 main-HEAD) | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json); ingested via Path-C re-derivation 2026-05-18; run_id `38d63bdd2def4fa9804c78fbcb1a76ce`) |
| Substrate origin | Re-derived deterministically from raw_1min CSVs sourced from Databento extractions 2026-04-23 (initial), 2026-05-12 (Phase O.0 Stage A metals/energy expansion via [scripts/databento_extract_2026_h1.py](../../../scripts/databento_extract_2026_h1.py); $44.37 USD batch), 2026-05-15 (Phase O.3 H1-2026 extension; $4.61 USD batch). The substrate-vintage memo is at [docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md). |

## Sample window

Per [design.md §2](design.md):

| Window | Date range | Sessions (approx) |
|---|---|---|
| Calibration holdout | 2015-01-01 → 2019-12-31 | ~1,260 (5 years × 252) |
| IS | 2020-01-01 → 2023-12-31 | ~1,008 (4 years × 252) |
| OOS | 2024-01-01 → 2026-05-15 | ~615 (2.4 years × 252) |
| 2026-04-01 → 2026-05-15 sub-window | 2026-04-01 → 2026-05-15 | ~30 (~6 weeks) |

The H067 v1 OOS window is **identical to H065 v2** per the single-axis-genetic-cross discipline (N-lot is the cross axis; sample window is preserved infrastructure). The cell-grid sweep evaluates the H065 v2 M_inf-SIL parent cell modal feature configuration (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0) at `N ∈ {1, 2, 3, 4, 5}` × `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` × `cost_arm ∈ {A0_zero, A1_conservative_prior}` per [design.md §5](design.md).

## Per-partition SHA enumeration (deferred to v1 freeze + walk-forward orchestrator)

The SIL-only partition SHA enumeration is per ADR-0013 §3.1.1 + ADR-0014 §3.2 sidecar provenance binding. Per the H065 data_requirements.md retrofit precedent (`audit_trail_2026-05-18_phase-o-merge-audit.md` F-3), the per-partition SHA enumeration is captured at the walk-forward orchestrator's substrate-loader entry per `P1-H067-SUBSTRATE-PER-PARTITION-SHA-EMIT` (BLOCKING-BEFORE-V1-EMISSION; new follow-up registered per [design.md §11.2](design.md)).

The expected SIL partition count per the Phase O.0 + O.3 + O.10 substrate inventory: **≥ 11 partitions** spanning 2015-01-01 → 2026-05-15 (per CLAUDE.md Phase O.10 §"Substrate row counts" table: SIL 1,868,034 roll-adjusted rows × 5,425 sessions × ~344 bars/session ≈ matches). The exact partition file list + per-partition `output_frame_sha256` SHALL be captured in the v1 sidecar `dataset_checksums.per_partition` field at walk-forward emission time.

## Cross-hypothesis fit-set isolation

The H067 v1 OOS window 2024-01-01 → 2026-05-15 has **non-trivial overlap** with:
- H050 SIL OOS — n/a (H050 universe = ES + NQ; SIL not in H050)
- H053 SIL OOS — n/a (H053 universe = ES + NQ; SIL not in H053)
- H055 v2 SIL OOS (2024-01-01 → 2026-05-15; same substrate vintage `317429e4...`)
- H060 v2 SIL OOS (2024-01-01 → 2026-05-15; same substrate vintage)
- H062 v2 + v3 SIL OOS (2024-01-01 → 2026-05-15; same substrate vintage)
- H065 v1 + v2 SIL OOS (2024-01-01 → 2026-05-15; same substrate vintage)

Per [design.md §1](design.md) the H067 hypothesis is a cost-light variant of the H065 v2 M_inf-SIL signal class; the OOS overlap is structurally consistent because H062 + H065 + H067 use the SAME entry signal and differ only in trade-management (H065 adds TP overlay; H067 adds N-lot sizing). Cross-strategy meta-portfolio analyses spanning H050/H053/H055/H060/H062/H065/H067 must account for OOS-window overlap; see [`research/01_meta_portfolio/MPV1/design.md`](../../01_meta_portfolio/MPV1/design.md) §2.4 arm-substrate-binding for the meta-portfolio treatment.

## Substrate-vintage diff vs H065 v1

H065 v1 was bound to `b93e544...` (sibling-worktree-only substrate vintage; documented in [research/01_hypothesis_register/H065/data_requirements.md](../H065/data_requirements.md) §"Source dataset (v1 binding)"). H067 v1 binds to the **canonical post-Phase-O.10 main-HEAD substrate `317429e4...`** per the substrate-vintage-inventory memo. The two substrates differ in:
- 2026-04-15 → 2026-05-15 extension (Phase O.3 2026-H1 backfill captured at `b93e544...` AND `317429e4...`; both contain the extension)
- 2026-05-16+ extension via Phase O.10 re-derivation on main HEAD (captured at `317429e4...` ONLY; `b93e544...` lacks the post-2026-05-15 sessions)

Per the cross-hypothesis investigation 2026-05-19 §6.1 the H065 v2 M_inf-SIL ratio anchor (1.04) uses the v2-retroactive emission on canonical substrate `317429e4...`; H067 v1 inherits this anchor verbatim.

## Cost-model placeholder risk disclosure (per design.md §6 + §11.2)

Per [config/instruments.yaml SIL](../../../config/instruments.yaml) the SIL commission ($0.85/side) + exchange-fee ($0.45/side) figures are **project-operational PLACEHOLDERS** pending CME Energy/Metals fee schedule primary-source verification per `P1-METALS-ENERGY-CME-FEE-VERIFY`. The empirical realistic cost may be 20-50% **HIGHER** than placeholder. The H067 v1 cost-friction-breakeven ratio reported at v1 KPI emission is therefore an **OPTIMISTIC LOWER BOUND** on actual cost burden. The structural sensitivity of the v1 conclusion to placeholder under-statement is tracked under `P1-H067-METALS-COST-CALIBRATION` (BLOCKING-BEFORE-NEXT-V3-LAUNCH).

## Reproducibility

The H067 v1 ReproLog SHALL be **complete** per ADR-0017 §3 + ADR-0026 §D-2 mandatory-verbosity carveout. The walk-forward orchestrator MUST wrap execution in `RunContext` per [src/skie_ninja/utils/runcontext.py](../../../src/skie_ninja/utils/runcontext.py) to emit the canonical 13-field ReproLog at `logs/reproducibility/<run_id>.json`. Avoiding the H065 v1 retrofit pattern documented in [research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md](../H065/H065_kpi_report_v1_corrigendum_2026-05-18.md) is tracked under `P1-H067-REPROLOG-WIRE` (BLOCKING-BEFORE-V1-EMISSION).

## Cross-references

- Design: [design.md](design.md)
- Lit review: [lit_review_H067_2026-05-19.md](lit_review_H067_2026-05-19.md)
- KPI report card v0 (pre-emission skeleton): [H067_kpi_report_v0.md](H067_kpi_report_v0.md)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Parent hypothesis: [H065 design.md](../H065/design.md) + [H065 KPI v1](../H065/H065_kpi_report_v1.md) + [H065 KPI v2](../H065/H065_kpi_report_v2.md) + [H065 data_requirements.md](../H065/data_requirements.md)
- Grandparent hypothesis: [H062 design.md](../H062/design.md)
- Empirical anchor: [cross-hypothesis investigation 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md)
- H062 v3 ablation precedent: [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- Substrate-vintage memo: [docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)
- Audit trail: [docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md](../../../docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md)
