---
hypothesis_id: H067
schema_version: failure_log_v1
created: 2026-05-19
---

# Failure Log — H067

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.2, this is an **append-only** chronological record of every external kill, build defect, run failure, and operator override on this hypothesis. Entries cannot be removed; corrections produce additional rows annotated `superseded by entry_id N`.

Categories:
- `external-kill` — Windows reboot, OOM, manual interrupt, supervisor cap exceeded
- `build-defect` — caught in audit-remediate-loop with finding ID + commit-of-fix
- `run-failure` — run did not produce a complete sidecar; cause documented
- `operator-override` — operator promoted past a methodological-correctness annotation (per ADR-0013 §2.1) with explicit acknowledgment that all KPIs are upper bounds
- `superseded` — corrects a prior entry; original retained verbatim

| entry_id | timestamp_ct | category | run_id_or_commit | finding_id_or_diagnosis_link | resolution_commit_or_followup | superseded_by | notes |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-19 17:39 CT | build-defect | pre-launch attempt-1 (no run_id; aborted at __main__ gate) | BLAS env-var transmission via Windows `set` did not carry to subprocess invocation; first launch raised RuntimeError at the ADR-0009 BLAS-pinning gate | inline-fixed by switching to POSIX-style `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` env prefix per Bash tool convention | null | no artifacts written; orchestrator exited at gate before RunContext entered |
| 2 | 2026-05-19 17:50 CT | build-defect | bba003j97 (background task; first 7 cells completed before kill) | MPPMResult attribute access defect — `mppm_ci_result.point_estimate` does not exist on the dataclass; correct field is `theta_hat` per src/skie_ninja/inference/mppm.py:111. Defect inherited from H065 sweep script (the H065 fork base also has the wrong attribute reference; only the H065 exception fallback path masked it). MPPM CI bounds reported as NaN in first 7 cells. | inline-fixed in scripts/run_h067_n_lot_sweep.py before second launch; defect logged as new cross-hypothesis follow-up `P1-H065-SWEEP-MPPM-ATTRIBUTE-FIX` (BLOCKING-BEFORE-NEXT-H065-V3-RUN) | null | run aborted at cell 7/60 to avoid emitting NaN-MPPM-CI KPI; full sweep relaunched after fix |

## Cross-references

- Stage tracker: [stage.md](stage.md)
- KPI report cards: `H067_kpi_report_v{N}.md`
- Audit-remediate-loop trails: `../../../docs/audits/audit_trail_YYYY-MM-DD_*.md`
- Promotion logs: `../../../logs/promotions/`

## Append discipline

- New entries APPEND to the table; existing rows are immutable.
- Corrections produce a new row with `category=superseded` and `superseded_by` pointing to the corrected entry; the original row's `superseded_by` field is updated to point to the corrector (this is the ONLY exception to immutability and is enforced by the pre-commit guard treating supersession-only column changes as append-equivalent).
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
