---
hypothesis_id: H053
schema_version: failure_log_v1
created: 2026-05-03
---

# Failure Log — H053

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.2, this is an **append-only** chronological record of every external kill, build defect, run failure, and operator override on this hypothesis. Entries cannot be removed; corrections produce additional rows annotated `superseded by entry_id N`.

| entry_id | timestamp_ct | category | run_id_or_commit | finding_id_or_diagnosis_link | resolution_commit_or_followup | superseded_by | notes |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-03 15:35 | build-defect | (Stage-3 v3 first-run; uncommitted) | scripts/run_h053_stage3_v3.py initial invocation | (this commit) inline fix | — | `ModuleNotFoundError: No module named 'skie_ninja'` because fresh `.venv` lacks editable install + project uses src-layout without `[build-system]` declared in pyproject.toml. Fixed by adding `_REPO_ROOT / "src"` to sys.path in v3 bootstrap. Tracked under broader follow-up `P1-PYPROJECT-BUILD-SYSTEM-DECLARE`. |
| 2 | 2026-05-03 15:39 | build-defect | (Stage-3 v3 second-run; uncommitted) | substrate path resolution | (this commit) operator workaround via `--substrate-path` CLI flag | — | Substrate `data/processed/vendor_legacy_1min_roll_adjusted/` empty in `lucid-snyder-233c6c` worktree. Used `--substrate-path "C:/.../inspiring-franklin-13a1f1/data/processed/vendor_legacy_1min_roll_adjusted"` (sibling worktree). Tracked under `P1-H053-STAGE3-SUBSTRATE-CONFIG-PIN` for canonical substrate path resolution via `SKIE_SHARED_DATA` env var. |
| 3 | 2026-05-03 15:53 | build-defect | (Stage-3 v4 first-run; uncommitted) | LW2008 API field-name mismatch (audit-trail F-V3-5 closure) | (this commit) inline fix | — | `'DifferentialCIResult' object has no attribute 'delta_sharpe'`. The `ledoit_wolf_2008_differential_ci` returns `point_estimate`, `lower`, `upper` (not `delta_sharpe`, `ci_low`, `ci_high`). Fixed wrapper to read correct field names. Run-1 sidecar at `runs/h053/stage3_v4/d0ada892ca194becbcf7879f8b5a842b/sidecar.json` preserved per ADR-0013 §4.1 non-loss; v4 re-run at `fe051383e6c146bea93051b816c7e0a1` is the canonical Path B output. |
| 4 | 2026-05-01 (retroactive) | build-defect (substrate) | scripts/run_h053_stage3.py first-pass | Daily-block 405-bar gate ([P1-H053-DAILY-405-GATE-RECONCILE](../../../docs/decisions/ADR-0011-production-walkforward-runbook.md)) | commit `48f116a` | — | Strict `n_rth_bars == 405` gate dropped ~65% of pre-2022 sessions from H053 train fold (1971 → 178). Defect found post-Stage-3 first-pass; disposition reversed via commit `8c1de7c`. Resolved by relaxing gate to `>= 404` (commit `48f116a`) to accommodate pre-2022 vendor median of 404 bars/session. |

## Append discipline

- New entries APPEND to the table; existing rows are immutable.
- Corrections produce a new row with `category=superseded` and `superseded_by` pointing to the corrected entry; the original row's `superseded_by` field is updated to point to the corrector (this is the ONLY exception to immutability; enforced by the pre-commit guard treating supersession-only column changes as append-equivalent — implementation deferred per `P1-NON-LOSS-PRECOMMIT-GUARD-CALIBRATION`).
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Stage tracker: [stage.md](stage.md)
- KPI report cards: [v1](H053_kpi_report_v1.md), [v2](H053_kpi_report_v2.md)
- Audit-remediate-loop trails: [docs/audits/](../../../docs/audits/) (see stage.md for chronological list)
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/) (none yet for H053)
