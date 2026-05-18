---
type: corrigendum
target: research/01_hypothesis_register/H055/H055_kpi_report_v1.md
date: 2026-05-18
trigger: post-merge audit-remediate-loop Round 1 reproducibility-verifier finding R-1 (critical)
parent_audit_trail: docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md
non_loss_disposition: v1 KPI report card preserved verbatim per ADR-0013 §4.1 non-loss. This corrigendum is the canonical correction-of-record for the specific annotation defect documented below.
---

# H055 KPI report card v1 — corrigendum addendum

## Defect

H055 KPI report card v1 (emitted 2026-05-15; run_id `v2_sweep_20260516T025924Z`) declares the methodological-correctness annotation `repro-log-present` in §4 (Methodological annotations summary).

The 2026-05-18 post-merge audit-remediate-loop Round 1 reproducibility-verifier (agent `ab3863740c443bcc5`) found this annotation **materially misleading**: the sweep emits a `sweep_sidecar.json` carrying only **2 of 13 ReproLog schema fields** (`git_head`, `hypothesis_id`); the canonical 13-field ReproLog at `logs/reproducibility/{run_id}.json` is **absent**. The sweep was not wrapped in `RunContext` — the canonical ReproLog emission path. The audit cross-referenced H065 v1's honest `repro-log-incomplete` self-attestation under identical infrastructure conditions.

## Corrected annotation

The correct annotation per ADR-0014 §3.2 methodological-correctness convention is:

> **`repro-log-incomplete`** — sweep sidecar `artifacts/runs/H055/v2_sweep_20260516T025924Z/sweep_sidecar.json` carries 2 of 13 ReproLog schema fields (`git_head`, `hypothesis_id`); 11 fields absent (`env_id`, `pip_freeze_sha256`, `pip_freeze_path`, `rng_seed` top-level, `model_hash`, `phase`, `timestamp_utc`, `host`, `config_resolved_sha256`, `dataset_checksums` top-level, `run_id` canonical 32-hex). Full ReproLog retrofit tracked under `P1-H055-REPROLOG-WIRE` (BLOCKING-BEFORE-V2-EMISSION).

## Scope

The numerical claims in H055 KPI v1 are NOT affected by this corrigendum:
- Table 3 MPPM(ρ=1) point estimates (MGC C3 +0.263, etc.) hold.
- Realized OOS basket figures (C2 +18.4%, C3 +19.7%, C9 +12.1%, etc.) hold.
- Sweep sidecar SHA256 (`83cd09e88476b93d...`) holds (computed deterministically from the on-disk sidecar).

What is corrected is **only the methodological-correctness annotation** — `repro-log-present` → `repro-log-incomplete`. Downstream consumers (e.g., the [`research/01_hypothesis_register/RESULTS_INDEX.md`](../RESULTS_INDEX.md) row for H055 v1) should reference this corrigendum and propagate the corrected annotation.

## Going-forward

`P1-H055-REPROLOG-WIRE` is **BLOCKING-BEFORE-V2-EMISSION**: the H055 v2 sweep MUST be wrapped in `RunContext` to emit the canonical 13-field ReproLog at `logs/reproducibility/{canonical_run_id}.json`. Same applies to H065 v2 (`P1-H065-REPROLOG-WIRE`) and MPV1 v2 (`P1-MPV1-REPROLOG-WIRE`).

## Cross-references

- Original v1 KPI: [`H055_kpi_report_v1.md`](H055_kpi_report_v1.md) (preserved verbatim per ADR-0013 §4.1)
- Parent audit trail: [`docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md`](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md)
- Substrate-locality reconciliation: [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md) (the H055 v1 substrate-locality drift is the related-but-distinct finding R-2 dispositioned under `P1-H055-V2-RERUN-ON-CANONICAL-SUBSTRATE`)
