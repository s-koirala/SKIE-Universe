---
hypothesis_id: H050_stable_state
parent_hypothesis_id: H050
schema_version: failure_log_v1
created: 2026-05-20
---

# Failure Log — H050.stable-state

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.2, this is an **append-only** chronological record of every external kill, build defect, run failure, and operator override on this hypothesis.

Categories:
- `external-kill` — Windows reboot, OOM, manual interrupt, supervisor cap exceeded
- `build-defect` — caught in audit-remediate-loop with finding ID + commit-of-fix
- `run-failure` — run did not produce a complete sidecar
- `operator-override` — operator promoted past a methodological-correctness annotation
- `superseded` — corrects a prior entry; original retained verbatim

| entry_id | timestamp_ct | category | run_id_or_commit | finding_id_or_diagnosis_link | resolution_commit_or_followup | superseded_by | notes |
|---|---|---|---|---|---|---|---|

(No entries yet; this hypothesis is at `status: designed` per the [stage tracker](stage.md). Pre-launch BLOCKING preconditions per [design.md §11.2](design.md) MUST close before the first production walk-forward attempt.)

## Cross-references

- Stage tracker: [stage.md](stage.md)
- KPI report cards: `H050_stable_state_kpi_report_v{N}.md` (v0 pre-emission skeleton landed at this commit)
- Audit-remediate-loop trails: [docs/audits/audit_trail_2026-05-20_h050_successor_variants.md](../../../docs/audits/audit_trail_2026-05-20_h050_successor_variants.md)
- Promotion logs: `../../../logs/promotions/`
- Parent H050 failure log: [research/01_hypothesis_register/H050/failure_log.md](../H050/failure_log.md)

## Append discipline

- New entries APPEND to the table; existing rows are immutable.
- Corrections produce a new row with `category=superseded`.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
