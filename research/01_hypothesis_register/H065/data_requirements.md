---
name: H065 data requirements
description: Pre-registration dataset checksums and coverage bounds for H065 (binding at designed status; inherits H062 substrate)
type: project
hypothesis_id: H065
schema_version: 1
status: designed
created: 2026-05-15
revised: 2026-05-18
---

# H065 — Data Requirements

Pre-registration companion to [design.md](design.md) §2 + §16. **Frozen at `designed` status concurrently with [design.md](design.md)** per the H050/H053/H054/H055/H060/H062 atomic-snapshot-binding pattern.

**Authoring note (2026-05-18 retrofit)**: this file is a post-emission retrofit closing the audit finding (`audit_trail_2026-05-18_phase-o-merge-audit.md` F-3) that H065 lacked the INDEX.md-mandated `data_requirements.md`. Substrate binding is documented from the H065 KPI report card v1 + sidecar + sibling worktree provenance; the operator's H065 v1 KPI emission was at `b93e544...` substrate (a sibling-worktree-only vintage; the canonical going-forward substrate on main HEAD is `317429e4...` per [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)).

## H065 substrate inheritance from H062

H065 is the TP-overlay extension of H062 v1 per [design.md §1](design.md). The substrate is **identical to H062's universe** (ES + NQ + MGC + SIL × 5-min cadence roll-adjusted) extended via the Phase O.3 2026-H1 backfill that landed mid-Phase-O. H065 v1 (emitted 2026-05-15 ~22 CT; run_id `tp_overlay_sweep_20260516T030515Z`) bound to substrate SHA `b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce` — the post-Phase-O.3 2026-H1-extension frame.

## Source dataset (v1 binding)

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m (one OHLCV row per 1-minute bar) |
| License | Databento End-User License Agreement (EULA). Verified 2026-04-23 + 2026-05-12; no redistribution; internal research use only. |
| Symbols | ES.FUT, NQ.FUT, MGC.FUT, SIL.FUT (front-month; Databento continuous series via parent-symbology). Coverage extends through 2026-05-15 OOS window per the Phase O.3 backfill |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment ([López de Prado 2018, Wiley, ISBN 978-1119482086](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086), *practitioner*) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` |
| v1 binding `output_frame_sha256` | `b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce` (sibling-worktree-only) |
| v2 going-forward `output_frame_sha256` | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.8 substrate on main HEAD; ingested 2026-05-18 via Path-C re-derivation; run_id `38d63bdd2def4fa9804c78fbcb1a76ce`) |

## Sample window

Per [design.md §2](design.md):

| Window | Date range | Sessions |
|---|---|---|
| IS (inherited from H062) | 2020-01-01 → 2023-12-31 | (per H062 v1 walk-forward) |
| OOS | 2024-01-01 → 2026-05-15 | (extends past H062 v1's 2025-12-30 OOS via Phase O.3 backfill) |

The H065 v1 OOS window extends 4.5 months past H062 v1's via the 2026-H1 Databento extraction. The TP-overlay sweep evaluates the H062 v1 baseline cell (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0) at M ∈ {1.0, 1.5, 2.0, 2.5, ∞} per [design.md §5](design.md).

## Cross-hypothesis fit-set isolation

The H065 v1 OOS window 2024-01-01 → 2026-05-15 has **non-trivial overlap** with:
- H050 OOS (2024-01-01 → 2025-12-{03,19})
- H053 OOS (2024-01-01 → 2025-12-{03,19})
- H062 v1 OOS (2024-01-01 → 2025-12-{03,30}; same substrate vintage)

Per [design.md §1](design.md) the H065 hypothesis is a TP-overlay variant of the H062 signal class; the OOS overlap is structurally consistent because the H062 + H065 use the SAME entry signal and differ only in trade-management (TP overlay). Cross-strategy meta-portfolio analyses spanning H050/H053/H062/H065 must account for OOS-window overlap; see [`research/01_meta_portfolio/MPV1/design.md`](../../01_meta_portfolio/MPV1/design.md) §2.4 arm-substrate-binding for the meta-portfolio treatment.

## Reproducibility

The H065 v1 ReproLog discipline is **incomplete** per audit finding R-1 in [`docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md`](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md): sweep sidecar carries 3 of 13 ReproLog schema fields; canonical 13-field ReproLog at `logs/reproducibility/{run_id}.json` is absent. Per H065 KPI v1 self-attested annotation `repro-log-incomplete` (honest). Full ReproLog retrofit tracked under `P1-H065-REPROLOG-WIRE` (BLOCKING-BEFORE-V2-EMISSION).

H065 v2 emission MUST bind to canonical substrate `317429e4...` AND wrap execution in `RunContext` to emit the canonical ReproLog. Tracked under `P1-H065-V2-RERUN-ON-CANONICAL-SUBSTRATE`.

## Cross-references

- Design: [design.md](design.md)
- Lit review: [lit_review_H065_2026-05-15.md](lit_review_H065_2026-05-15.md)
- KPI report card v1: [H065_kpi_report_v1.md](H065_kpi_report_v1.md)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Hsu-Kuan 2005 erratum: [`research/01_hypothesis_register/_erratum_hsu_kuan_2005_2026-05-18.md`](../_erratum_hsu_kuan_2005_2026-05-18.md)
- Substrate-vintage memo: [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)
- Audit trail: [`docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md`](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md)
