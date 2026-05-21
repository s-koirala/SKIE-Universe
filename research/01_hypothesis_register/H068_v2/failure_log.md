---
hypothesis_id: H068_v2
schema_version: failure_log_v1
created: 2026-05-20
---

# Failure Log — H068 v2

Per [ADR-0013 §4.2](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) non-loss mandate. This is an **append-only** record of every:
- external kill (e.g., OS-induced reboot mid-run; Ctrl-C; SIGTERM)
- build defect (e.g., orchestrator crash; sidecar emission failure; schema-validation failure)
- run failure (e.g., HMM convergence failure; substrate-load failure; per-fold checkpoint corruption)
- operator override (e.g., manual cell-grid restriction; mid-run parameter modification)

per ADR-0013 §4.2 failure_log scope. Investigation closures + audit findings are NOT recorded here per the H062 + H055 INVESTIGATE-FAILURE-MODE memo conventions (those land at separate `INVESTIGATE-FAILURE-MODE-*` memo files).

## Entries

(none at v2 pre-registration; this file is initialized empty at `status: designed` per the H065/H067/H068 v1 precedent)

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Stage tracker: [stage.md](stage.md)
- KPI report cards: `H068_v2_kpi_report_v{N}.md`
- Design: [design.md](design.md)
- Parent failure log: [H068 v1 failure_log.md](../H068/failure_log.md)
