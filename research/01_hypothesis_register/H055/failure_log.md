---
hypothesis_id: H055
schema_version: failure_log_v1
created: 2026-05-06
---

# Failure Log — H055

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.2, this is an **append-only** chronological record of every external kill, build defect, run failure, and operator override on this hypothesis. Entries cannot be removed; corrections produce additional rows annotated `superseded by entry_id N`.

Categories:
- `external-kill` — Windows reboot, OOM, manual interrupt, supervisor cap exceeded
- `build-defect` — caught in audit-remediate-loop with finding ID + commit-of-fix
- `run-failure` — run did not produce a complete sidecar; cause documented
- `operator-override` — operator promoted past a methodological-correctness annotation (per ADR-0013 §2.1) with explicit acknowledgment that all KPIs are upper bounds
- `superseded` — corrects a prior entry; original retained verbatim

| entry_id | timestamp_ct | category | run_id_or_commit | finding_id_or_diagnosis_link | resolution_commit_or_followup | superseded_by | notes |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-15T21:50 | build-defect | scripts/run_h055_v2_sweep.py R1 | [docs/audits/audit_trail_2026-05-15_h055_v2.md](../../../docs/audits/audit_trail_2026-05-15_h055_v2.md) F-1-9 | remediated in same commit pre-emission | — | MPPM input semantic: log-returns passed to mppm_rho_1 which expects arithmetic; fixed in C9StateMachine.on_session_close + session-boundary handler + final close + per-session aggregation (split psr_arith from psr_log) |
| 2 | 2026-05-15T21:50 | build-defect | scripts/run_h055_v2_sweep.py R1 | F-1-2 | follow-up `P1-H055-LIMIT-FILL-WICK-EXTREME` (BLOCKING-BEFORE-PRODUCTION-WALK-FORWARD) | — | Entry-fill simplification: v1 enters at t+1 open instead of limit-at-wick-extreme per H055 design.md §4; documented as caveat in KPI v1 §Methodological caveats |
| 3 | 2026-05-15T21:50 | build-defect | scripts/run_h055_v2_sweep.py R1 | F-1-10 | remediated in same commit pre-emission | — | Provenance JSON path hard-coded to 20260516 date; replaced with glob-most-recent |
| 4 | 2026-05-15T21:50 | build-defect | scripts/run_h055_v2_sweep.py initial smoke | UnicodeEncodeError on stdout | remediated by sys.stdout.reconfigure(encoding="utf-8") + ASCII fallback for arrow glyphs | — | Windows cp1252 stdout encoding failed on `→`; fixed inline before production run |

## Cross-references

- Stage tracker: [stage.md](stage.md)
- KPI report cards: `H055_kpi_report_v{N}.md`
- Audit-remediate-loop trails: [../../../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../../../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md) (design pre-reg trail)
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/)

## Append discipline

- New entries APPEND to the table; existing rows are immutable.
- Corrections produce a new row with `category=superseded` and `superseded_by` pointing to the corrected entry; the original row's `superseded_by` field is updated to point to the corrector (this is the ONLY exception to immutability and is enforced by the pre-commit guard treating supersession-only column changes as append-equivalent).
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
