---
name: H068 data requirements
description: Pre-registration dataset checksums and coverage bounds for H068 (binding at designed status; inherits H065 + H062 substrate; ES-only universe)
type: project
hypothesis_id: H068
schema_version: 1
status: designed
created: 2026-05-19
---

# H068 — Data Requirements

Pre-registration companion to [design.md](design.md) §2 + §16. **Frozen at `designed` status concurrently with [design.md](design.md)** per the H050/H053/H054/H055/H060/H062/H065/H067 atomic-snapshot-binding pattern.

## H068 substrate inheritance from H065 + H062

H068 is the sub-1-tick-slip-empirical-sensitivity cost-light genetic successor of [H065 v2 M_inf_h062_v1_fixed-ES cell](../H065/design.md) per [design.md §1](design.md) + §17.1 genetic-successor cross-citation. The substrate is **identical to H065's universe restricted to ES standalone** on the canonical post-Phase-O.10 main-HEAD substrate.

## Source dataset (v1 binding)

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23 + 2026-05-12 + 2026-05-15 (Phase O.3 2026-H1 extension); no redistribution; internal research use only. |
| Symbol at v1 | ES.FUT (E-mini S&P 500; CME Globex; tick_size 0.25 → tick_value $12.50; multiplier $50/index point; front-month; Databento continuous series via parent-symbology). Coverage extends through 2026-05-15 OOS window per Phase O.3 + Phase O.10 backfill |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/ES_*` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/symbol=ES/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment ([López de Prado 2018, Wiley, ISBN-13 978-1119482086](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086), *practitioner*) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` |
| Binding `output_frame_sha256` (canonical post-Phase-O.10 main-HEAD) | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json); ingested via Path-C re-derivation 2026-05-18; run_id `38d63bdd2def4fa9804c78fbcb1a76ce`) |
| Substrate origin | Re-derived deterministically from raw_1min CSVs sourced from Databento extractions 2026-04-23 (initial), 2026-05-12 (Phase O.0 Stage A metals/energy expansion via [scripts/databento_extract_2026_h1.py](../../../scripts/databento_extract_2026_h1.py); $44.37 USD batch), 2026-05-15 (Phase O.3 H1-2026 extension; $4.61 USD batch). The substrate-vintage memo is at [docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md). |

## ES fee schedule (canonical; UNCHANGED through Phase O.16)

Per [config/instruments.yaml ES lines 49-51](../../../config/instruments.yaml):

| Fee component | Value | Source | Verified |
|---|---:|---|---|
| `commission_per_side_usd` | $0.85 | NinjaTrader Brokerage Unlimited, Q1-2026 published rate | retrieved 2026-04-15 (placeholder; broker-specific; pre-live `commission_reviewed_for_broker` binding required per audit F-2-17 in [research/03_audits/audit-round1-quant_2026-04-15.md](../../../research/03_audits/audit-round1-quant_2026-04-15.md)) |
| `exchange_fee_usd` | $1.18 | CME Individual Member Equity Index electronic, Schedule of Fees eff. 2024-02 | **PRIMARY-SOURCE-VERIFIED**; see https://www.cmegroup.com/company/clearing-fees.html |
| `nfa_fee_usd` | $0.02 | NFA Rulebook Section 13, eff. 2024-01-01 | **PRIMARY-SOURCE-VERIFIED** (unchanged since 2018-01-01; closes `P1-NFA-FEE-VERIFY-2026` per Phase O.16 inheritance) |

**ES fees were NOT in Phase O.16 scope**: the Phase O.16 metals/energy CME fee verification (closes `P1-METALS-ENERGY-CME-FEE-VERIFY` via Phase O.16 commits `31e7f69` + `9a3a512`) covered MGC + SIL + MCL only. ES exchange fee ($1.18/side) was already CME-verified effective 2024-02 at the Phase 0 instruments.yaml pre-registration time per the existing project audit trail. The H068 v1 substrate-validity is therefore NOT subject to the same fee-recalibration risk that affected H067 SIL ($0.45 → $1.00 = 122% increase per Phase O.16 verification).

**Round-trip cost at v1 cost-arm cells**:
- `sensitivity_mult = 1.0` (conservative_prior): per-side fixed $2.05 + per-side slip $12.50 = $14.55/side; round-trip $29.10/contract.
- `sensitivity_mult = 0.5` (mid empirical sensitivity): per-side fixed $2.05 + per-side slip $6.25 = $8.30/side; round-trip $16.60/contract.
- `sensitivity_mult = 0.25` (aggressive empirical sensitivity): per-side fixed $2.05 + per-side slip $3.125 = $5.175/side; round-trip $10.35/contract.

## Sample window

Per [design.md §2](design.md):

| Window | Date range | Sessions (approx) |
|---|---|---|
| Calibration holdout | 2020-01-01 → 2020-12-31 | ~252 (1 year × 252) |
| IS | 2021-01-01 → 2023-12-31 | ~756 (3 years × 252) |
| OOS | 2024-01-01 → 2026-05-15 | ~615 (2.4 years × 252) |
| 2026-04-01 → 2026-05-15 sub-window | 2026-04-01 → 2026-05-15 | ~30 (~6 weeks) |

The H068 v1 OOS window is **identical to H065 v2** per the single-axis-genetic-cross discipline (slip is the cross axis; sample window is preserved infrastructure). The cell-grid sweep evaluates the H065 v2 M_inf_h062_v1_fixed-ES parent cell modal feature configuration (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0) at `sensitivity_mult ∈ {1.0, 0.5, 0.25}` × `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` × `cost_arm ∈ {A0_zero, A1_conservative_prior_at_sensitivity_mult}` per [design.md §5](design.md).

**Calibration holdout truncation note**: ES substrate begins 2020-01-01 in the canonical post-Phase-O.10 substrate per CLAUDE.md Phase O.10 §"Substrate row counts" table (`ES 2,016,269 roll-adjusted rows; 2020-01-01 → 2025-12-03`). The 1-year calibration holdout (2020-01-01 → 2020-12-31) is shorter than H067 SIL's 5-year holdout (2015-2019) due to ES coverage starting later; the 3-year IS window (2021-2023) provides ample fold count for inner-CV cell selection per ADR-0027 §D-2 bounded set {63, 126, 252, 504}. The shorter calibration holdout is documented inline in design.md §2 with `# justify:` per the operator-discipline pre-flight arbitration-pre-emption pattern.

## Per-partition SHA enumeration (deferred to v1 freeze + walk-forward orchestrator)

The ES-only partition SHA enumeration is per ADR-0013 §3.1.1 + ADR-0014 §3.2 sidecar provenance binding. Per the H065 + H067 data_requirements.md retrofit precedent (`audit_trail_2026-05-18_phase-o-merge-audit.md` F-3), the per-partition SHA enumeration is captured at the walk-forward orchestrator's substrate-loader entry per `P1-H068-SUBSTRATE-PER-PARTITION-SHA-EMIT` (BLOCKING-BEFORE-V1-EMISSION; new follow-up registered per [design.md §11.2](design.md)).

The expected ES partition count per the Phase O.0 + O.3 + O.10 substrate inventory: **≥ 11 partitions** spanning 2020-01-01 → 2026-05-15 (per CLAUDE.md Phase O.10 §"Substrate row counts" table: ES 2,016,269 roll-adjusted rows × ~1,600 RTH sessions × ~1,260 bars/session ≈ matches at 1-min cadence). The exact partition file list + per-partition `output_frame_sha256` SHALL be captured in the v1 sidecar `dataset_checksums.per_partition` field at walk-forward emission time.

## Cross-hypothesis fit-set isolation

The H068 v1 OOS window 2024-01-01 → 2026-05-15 has **non-trivial overlap** with:
- H050 ES OOS (2024-01-01 → 2025-12-03; same substrate vintage `317429e4...`)
- H052a ES OOS (2024-01-01 → 2025-12-03; same substrate vintage)
- H053 ES OOS (2024-01-01 → 2025-12-03; same substrate vintage)
- H054 ES OOS (2024-01-01 → 2025-12-03; same substrate vintage)
- H055 v2 ES OOS (2024-01-01 → 2026-05-15; same substrate vintage)
- H060 v2 ES OOS (2024-01-01 → 2026-05-15; same substrate vintage)
- H062 v2 + v3 ES OOS (2024-01-01 → 2026-05-15; same substrate vintage)
- H065 v1 + v2 ES OOS (2024-01-01 → 2026-05-15; same substrate vintage)
- H067 ES OOS — n/a (H067 universe = SIL standalone; ES not in H067)

Per [design.md §1](design.md) the H068 hypothesis is a cost-light variant of the H065 v2 M_inf-ES signal class; the OOS overlap is structurally consistent because H062 + H065 + H068 use the SAME entry signal and differ only in cost-model parameters (H065 adds TP overlay; H068 adds sub-1-tick slip empirical sensitivity sweep). Cross-strategy meta-portfolio analyses spanning H050/H052a/H053/H054/H055/H060/H062/H065/H067/H068 must account for OOS-window overlap; see [`research/01_meta_portfolio/MPV1/design.md`](../../01_meta_portfolio/MPV1/design.md) §2.4 arm-substrate-binding for the meta-portfolio treatment.

## Substrate-vintage diff vs H065 v1

H065 v1 was bound to `b93e544...` (sibling-worktree-only substrate vintage; documented in [research/01_hypothesis_register/H065/data_requirements.md](../H065/data_requirements.md) §"Source dataset (v1 binding)"). H068 v1 binds to the **canonical post-Phase-O.10 main-HEAD substrate `317429e4...`** per the substrate-vintage-inventory memo. The two substrates differ in:
- 2026-04-15 → 2026-05-15 extension (Phase O.3 2026-H1 backfill captured at `b93e544...` AND `317429e4...`; both contain the extension)
- 2026-05-16+ extension via Phase O.10 re-derivation on main HEAD (captured at `317429e4...` ONLY; `b93e544...` lacks the post-2026-05-15 sessions)

Per the cross-hypothesis investigation 2026-05-19 addendum §3 row #1 the H065 v2 M_inf_h062_v1_fixed-ES ratio anchor (1.266) uses the v2-retroactive emission on canonical substrate `317429e4...`; H068 v1 inherits this anchor verbatim.

## Cost-model fee-vintage stability disclosure

Per the [cross-hypothesis investigation 2026-05-19 addendum §1](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md), ES exchange fees were NOT in Phase O.16 scope (already CME-verified effective 2024-02). The H068 v1 cost-friction-breakeven ratio (1.266 at `sensitivity_mult=1.0`) is therefore NOT subject to the same fee-recalibration risk that affected H067 SIL — there is NO impending fee-vintage re-verification expected that would shift the H068 baseline ratio. This is the structural reason H068 is empirically the #1 post-Phase-O.16 cost-light successor candidate per the addendum §3 re-ranking.

## Reproducibility

The H068 v1 ReproLog SHALL be **complete** per ADR-0017 §3 + ADR-0026 §D-2 mandatory-verbosity carveout. The walk-forward orchestrator MUST wrap execution in `RunContext` per [src/skie_ninja/utils/runcontext.py](../../../src/skie_ninja/utils/runcontext.py) to emit the canonical 13-field ReproLog at `logs/reproducibility/<run_id>.json`. Avoiding the H065 v1 retrofit pattern documented in [research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md](../H065/H065_kpi_report_v1_corrigendum_2026-05-18.md) is tracked under `P1-H068-REPROLOG-WIRE` (BLOCKING-BEFORE-V1-EMISSION).

## Cross-references

- Design: [design.md](design.md)
- Lit review: [lit_review_H068_2026-05-19.md](lit_review_H068_2026-05-19.md)
- KPI report card v0 (pre-emission skeleton): [H068_kpi_report_v0.md](H068_kpi_report_v0.md)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Parent hypothesis: [H065 design.md](../H065/design.md) + [H065 KPI v1](../H065/H065_kpi_report_v1.md) + [H065 KPI v2](../H065/H065_kpi_report_v2.md) + [H065 data_requirements.md](../H065/data_requirements.md)
- Sibling cost-light successor: [H067 design.md](../H067/design.md) + [H067 data_requirements.md](../H067/data_requirements.md)
- Grandparent hypothesis: [H062 design.md](../H062/design.md)
- Empirical anchor: [cross-hypothesis investigation 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md) + [addendum 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md)
- H062 v3 ablation precedent: [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- Substrate-vintage memo: [docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)
- Audit trail: [docs/audits/audit_trail_2026-05-19_h068-cost-light-h065-es-design.md](../../../docs/audits/audit_trail_2026-05-19_h068-cost-light-h065-es-design.md)
