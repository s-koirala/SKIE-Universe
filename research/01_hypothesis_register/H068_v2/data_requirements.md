---
name: H068 v2 data requirements
description: Pre-registration dataset checksums and coverage bounds for H068 v2 (binding at designed status; inherits H068 v1 substrate; multi-instrument basket {ES, MGC, SIL} universe expansion)
type: project
hypothesis_id: H068_v2
schema_version: 1
status: designed
created: 2026-05-20
---

# H068 v2 — Data Requirements

Pre-registration companion to [design.md](design.md) §2 + §16. **Frozen at `designed` status concurrently with [design.md](design.md)** per the H050/H053/H054/H055/H060/H062/H065/H067/H068 atomic-snapshot-binding pattern.

## H068 v2 substrate inheritance from H068 v1 + Phase O.10 canonical re-derivation

H068 v2 is the multi-instrument basket expansion of [H068 v1](../H068/design.md) per [design.md §1](design.md) + §17.1 genetic-successor cross-citation. The substrate is **identical to H068 v1's canonical post-Phase-O.10 main-HEAD substrate expanded to 3 symbols** (ES + MGC + SIL); H068 v1 universe was ES-only.

## Source dataset (v2 binding)

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23 + 2026-05-12 + 2026-05-15 + 2026-05-18 (Phase O.10 Path-C re-derivation); no redistribution; internal research use only. |
| Symbols at v2 | ES.FUT (E-mini S&P 500) + MGC.FUT (Micro Gold) + SIL.FUT (Micro Silver); all CME Globex; Databento continuous series via parent-symbology. Coverage extends through 2026-05-15 per Phase O.3 + Phase O.10 backfill |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/{ES,MGC,SIL}_*` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/symbol={ES,MGC,SIL}/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment ([López de Prado 2018, Wiley, ISBN-13 978-1119482086](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086), *practitioner*) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` |
| Binding `output_frame_sha256` (canonical post-Phase-O.10 main-HEAD) | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json); ingested via Path-C re-derivation 2026-05-18; run_id `38d63bdd2def4fa9804c78fbcb1a76ce`) |
| Substrate origin | Re-derived deterministically from raw_1min CSVs sourced from Databento extractions 2026-04-23 (initial ES + NQ; pre-Phase-O.0), 2026-05-12 (Phase O.0 Stage A metals/energy expansion via [scripts/databento_extract_2026_h1.py](../../../scripts/databento_extract_2026_h1.py); $44.37 USD batch including MGC + SIL + MCL), 2026-05-15 (Phase O.3 H1-2026 extension; $4.61 USD batch). The substrate-vintage memo is at [docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md). |

## Per-symbol fee schedules

Per [config/instruments.yaml](../../../config/instruments.yaml) lines 49-51 (ES) + Phase O.16 commit `9a3a512` (MGC + SIL fee verification):

| Symbol | commission_per_side_usd | exchange_fee_usd | nfa_fee_usd | tick_value | tick_size | multiplier | Verified |
|---|---:|---:|---:|---:|---:|---:|---|
| ES | 0.85 | 1.18 | 0.02 | 12.50 | 0.25 | 50.00 | CME 2024-02 (pre-Phase-O.16; NOT in O.16 scope) |
| MGC | 0.85 | 1.45 | 0.02 | 1.00 | 0.10 | 10.00 | CME 2024-02 (verified Phase O.16) |
| SIL | 0.85 | 1.00 | 0.02 | 5.00 | 0.005 | 1000.00 | CME 2024-02 (verified Phase O.16) |

**Per-symbol round-trip cost at v2 cost-arm cells** (per side fixed = commission + exchange + nfa; per side slip = sensitivity_mult × tick_value; round-trip = 2 × per-side):

| Symbol | sensitivity_mult | Per-side fixed $ | Per-side slip $ | Total per side $ | Round-trip $ |
|---|---:|---:|---:|---:|---:|
| ES | 1.0 | 2.05 | 12.50 | 14.55 | 29.10 |
| ES | 0.5 | 2.05 | 6.25 | 8.30 | 16.60 |
| ES | 0.25 | 2.05 | 3.125 | 5.175 | 10.35 |
| MGC | 1.0 | 2.32 | 1.00 | 3.32 | 6.64 |
| MGC | 0.5 | 2.32 | 0.50 | 2.82 | 5.64 |
| MGC | 0.25 | 2.32 | 0.25 | 2.57 | 5.14 |
| SIL | 1.0 | 1.87 | 5.00 | 6.87 | 13.74 |
| SIL | 0.5 | 1.87 | 2.50 | 4.37 | 8.74 |
| SIL | 0.25 | 1.87 | 1.25 | 3.12 | 6.24 |

**Per-symbol cost-reduction percentages at slip=0.5 vs slip=1.0 baseline**: ES −43% (round-trip $29.10 → $16.60); MGC −15% (round-trip $6.64 → $5.64); SIL −36% (round-trip $13.74 → $8.74). See [design.md §6](design.md) for the cross-symbol cost-reduction asymmetry analysis (slip refinement is most-impactful on ES; MGC has per-side-fixed-dominated cost structure → smaller leverage).

## Sample window

Per [design.md §2](design.md):

| Window | Date range | Sessions (approx) |
|---|---|---|
| Calibration holdout | 2020-01-01 → 2020-12-31 | ~252 (1 year × 252) |
| IS | 2021-01-01 → 2023-12-31 | ~756 (3 years × 252) |
| OOS | 2024-01-01 → 2026-05-15 | ~615 (2.4 years × 252) |
| 2026-04-01 → 2026-05-15 sub-window | 2026-04-01 → 2026-05-15 | ~30 (~6 weeks) |

The H068 v2 sample window is **identical to H068 v1** per the single-axis-genetic-cross discipline (universe is the cross axis; sample window is preserved infrastructure). The cell-grid sweep evaluates the H065 v2 M_inf_h062_v1_fixed-ES parent cell modal feature configuration (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0) at `sensitivity_mult ∈ {1.0, 0.5, 0.25}` × `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` × `cost_arm ∈ {A0_zero, A1_conservative_prior_at_sensitivity_mult}` PER SYMBOL across {ES, MGC, SIL} per [design.md §5](design.md).

**Calibration holdout truncation note**: ES substrate begins 2020-01-01 in the canonical post-Phase-O.10 substrate per CLAUDE.md Phase O.10 §"Substrate row counts" table. MGC + SIL have pre-2020 coverage (2015-01-01 → 2026-05-15 per Phase O.0 Stage A extraction) but the cross-symbol-comparability of the calibration window benefits from a uniform 2020-01-01 start; this constraint is preserved per ADR-0027 §D-2 bounded-set discipline + cross-symbol calibration-window-isolation invariant.

## Per-partition SHA enumeration (deferred to v2 freeze + walk-forward orchestrator)

Per ADR-0013 §3.1.1 + ADR-0014 §3.2 sidecar provenance binding. Per the H065 + H067 + H068 v1 data_requirements.md retrofit precedent (`audit_trail_2026-05-18_phase-o-merge-audit.md` F-3), the per-partition SHA enumeration is captured at the walk-forward orchestrator's substrate-loader entry per `P1-H068-V2-SUBSTRATE-PER-PARTITION-SHA-EMIT` (BLOCKING-BEFORE-V2-EMISSION; new follow-up registered per [design.md §11.2](design.md)).

Per-symbol expected partition count per the Phase O.0 + O.3 + O.10 substrate inventory:

| Symbol | Expected partitions | Years coverage |
|---|---:|---|
| ES | ≥ 12 (years 2015-2026; substrate effective start 2020-01-01) | 2020-01-01 → 2026-05-15 (effective; pre-2020 ES partitions exist but contain no roll-adjusted rows per provenance JSON) |
| MGC | ≥ 12 (years 2015-2026) | 2015-01-01 → 2026-05-15 |
| SIL | ≥ 12 (years 2015-2026) | 2015-01-01 → 2026-05-15 |

The exact partition file list + per-partition `output_frame_sha256` SHALL be captured in the v2 sidecar `dataset_checksums.per_partition` field at walk-forward emission time (per H068 v1 + H067 + H065 retrofit pattern).

## Cross-hypothesis fit-set isolation

The H068 v2 OOS window 2024-01-01 → 2026-05-15 has **non-trivial overlap** with:
- H050 ES OOS (2024-01-01 → 2025-12-03; same substrate vintage `317429e4...`; ES overlap)
- H052a ES OOS (2024-01-01 → 2025-12-03; ES overlap)
- H053 ES OOS (2024-01-01 → 2025-12-03; ES overlap)
- H054 ES OOS (2024-01-01 → 2025-12-03; ES overlap)
- H055 v2 ES + MGC + SIL OOS (2024-01-01 → 2026-05-15; full 3-symbol overlap)
- H060 v2 ES + MGC + SIL OOS (2024-01-01 → 2026-05-15; full 3-symbol overlap; basket-level)
- H062 v2 + v3 ES + MGC + SIL OOS (2024-01-01 → 2026-05-15; full 3-symbol overlap)
- H065 v1 + v2 ES + MGC + SIL OOS (2024-01-01 → 2026-05-15; full 3-symbol overlap)
- H067 ES OOS — n/a (H067 universe = SIL standalone; partial 1-symbol overlap on SIL)
- H068 v1 ES OOS (2024-01-01 → 2026-05-15; ES overlap; same substrate vintage and parent cell)

Per [design.md §1](design.md) the H068 v2 hypothesis is a multi-instrument expansion of the H068 v1 cost-light variant of the H065 v2 M_inf-ES signal class; the OOS overlap is structurally consistent because H062 + H065 + H068 v1 + H068 v2 use the SAME entry signal and differ only in cost-model parameters (H065 adds TP overlay; H068 v1 adds sub-1-tick slip empirical sensitivity sweep; H068 v2 adds multi-instrument basket aggregation). Cross-strategy meta-portfolio analyses spanning H050/H052a/H053/H054/H055/H060/H062/H065/H067/H068/H068 v2 must account for OOS-window overlap; see [`research/01_meta_portfolio/MPV1/design.md`](../../01_meta_portfolio/MPV1/design.md) §2.4 arm-substrate-binding for the meta-portfolio treatment.

## Substrate-vintage diff vs H068 v1

H068 v1 was bound to `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.10 main-HEAD substrate). H068 v2 binds to the **SAME canonical substrate** per the parent-cell preservation discipline; the only diff vs H068 v1 is the universe expansion (ES-only → 3-symbol basket). No new Databento extraction; no substrate re-derivation; deterministic per-symbol per-partition checksum match between H068 v1 (ES partitions) and H068 v2 (ES + MGC + SIL partitions) at the ES symbol-set.

Per the cross-hypothesis investigation 2026-05-19 addendum §3 row #1 the H065 v2 M_inf_h062_v1_fixed-ES ratio anchor (1.266) uses the v2-retroactive emission on canonical substrate `317429e4...`; H068 v1 inherits this anchor verbatim; H068 v2 inherits BOTH the H065 v2 ratio anchor AND the H068 v1 slip-sensitivity sweep result anchors (slip=0.5 ratio 2.278; slip=0.25 ratio 3.653).

## Cost-model fee-vintage stability disclosure

Per the [cross-hypothesis investigation 2026-05-19 addendum §1](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md):
- **ES exchange fees were NOT in Phase O.16 scope** (already CME-verified effective 2024-02 per [config/instruments.yaml ES line 50](../../../config/instruments.yaml)).
- **MGC + SIL exchange fees WERE in Phase O.16 scope** (verified Phase O.16 commit `9a3a512` per CLAUDE.md Phase O.16 ledger entry "P1-METALS-ENERGY-CME-FEE-VERIFY" closure).

The H068 v2 cost-friction-breakeven ratios at v2 emission are NOT subject to fee-recalibration risk — all 3 symbol fee schedules are CME-verified at the canonical effective-2024-02 vintage as of pre-reg landing date 2026-05-20.

## Reproducibility

The H068 v2 ReproLog SHALL be **complete** per ADR-0017 §3 + ADR-0026 §D-2 mandatory-verbosity carveout. The walk-forward orchestrator MUST wrap execution in `RunContext` per [src/skie_ninja/utils/runcontext.py](../../../src/skie_ninja/utils/runcontext.py) to emit the canonical 13-field ReproLog at `logs/reproducibility/<run_id>.json`. Avoiding the H065 v1 + H067 v1 + H068 v1 retrofit patterns is tracked under `P1-H068-V2-REPROLOG-WIRE` (BLOCKING-BEFORE-V2-EMISSION per design.md §11.2).

RNG seed at v2 = `20260520` (distinguished from H068 v1's `20260519` per ADR-0017 §3 fresh-seed convention + the pre-reg-date 2026-05-20).

## Cross-references

- Design: [design.md](design.md)
- Lit review: [lit_review_H068_v2_2026-05-20.md](lit_review_H068_v2_2026-05-20.md)
- KPI report card v0 (pre-emission skeleton): [H068_v2_kpi_report_v0.md](H068_v2_kpi_report_v0.md)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Parent hypothesis: [H068 v1 design.md](../H068/design.md) + [H068 v1 KPI v1](../H068/H068_kpi_report_v1.md) + [H068 v1 data_requirements.md](../H068/data_requirements.md)
- Sibling cost-light successor: [H067 design.md](../H067/design.md)
- Grandparent hypothesis: [H065 design.md](../H065/design.md) + [H065 KPI v2](../H065/H065_kpi_report_v2.md)
- Great-grandparent hypothesis: [H062 design.md](../H062/design.md) + [H062 v2 KPI v2](../H062/H062_kpi_report_v2.md) (per-symbol trade-frequency reference)
- Substrate-vintage memo: [docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)
- Audit trail: [docs/audits/audit_trail_2026-05-20_h068_v2_design.md](../../../docs/audits/audit_trail_2026-05-20_h068_v2_design.md)
- CLAUDE.md ledger: Phase O.18 closure synthesis (commit `8434c37` per CLAUDE.md "Phase O.18 closure synthesis — 6-parallel-agent campaign cross-task report 2026-05-19"): `P1-H068-V2-EXPANDED-SUBSTRATE` registered as the BLOCKING-BEFORE-V2-INFERENCE follow-up; this design.md + data_requirements.md are its closure deliverables.
