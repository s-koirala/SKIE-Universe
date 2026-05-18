---
hypothesis_id: H062
schema_version: failure_log_v1
created: 2026-05-14
---

# Failure Log — H062

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.2, this is an **append-only** chronological record of every external kill, build defect, run failure, and operator override on this hypothesis. Entries cannot be removed; corrections produce additional rows annotated `superseded by entry_id N`.

Categories:
- `external-kill` — Windows reboot, OOM, manual interrupt, supervisor cap exceeded
- `build-defect` — caught in audit-remediate-loop with finding ID + commit-of-fix
- `run-failure` — run did not produce a complete sidecar; cause documented
- `operator-override` — operator promoted past a methodological-correctness annotation (per ADR-0013 §2.1) with explicit acknowledgment that all KPIs are upper bounds
- `superseded` — corrects a prior entry; original retained verbatim

| entry_id | timestamp_ct | category | run_id_or_commit | finding_id_or_diagnosis_link | resolution_commit_or_followup | superseded_by | notes |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-15 ~14 CT | build-defect | Phase O.2 batch-1 → batch-3 | `audit_trail_2026-05-14_h062_intraday_donchian_design.md` | commits `8772e01` → `cc2d8a8` → `12c4316` | — | Multiple Polars schema MergeError on labels↔features `session_date_et` precision mismatch (μs vs ns); 4 fixes across batches; canonical resolution: normalise all H062 feature panels to `pl.Datetime("ns", "UTC")` at orchestrator join site |
| 2 | 2026-05-15 ~14 CT | build-defect | Phase O.2 batch-3 | (Round-1 audit inline) | commit `0aa9258` | — | `HMMParams.n_states` is a method, not attribute; orchestrator at `select_gaussian_hmm` invocation used `int(hmm.params_.n_states)` which raised TypeError; resolved via `selection.best_n_states` direct access |
| 3 | 2026-05-15 ~18 CT | build-defect | run_id `16cb68d997c148a2834aad21b73bfdb6` (post-run audit) | F-1-9 (H055 v2 audit; not caught in H062 launch-readiness audit) | follow-up `P1-H062-MPPM-DOUBLE-LOG-V2-FIX`; commit landed 2026-05-18 (this session) | — | MPPM double-log bug at orchestrator lines 553/866-868/919; mppm_rho_1 expects arithmetic returns r > -1 per GISW 2007 §2; orchestrator passed log-returns; biases by Jensen-gap (~+σ²/2/yr at typical σ). H062 v1 KPI numbers all biased; CI conclusion (covers zero) robust to fix |
| 4 | 2026-05-15 ~18 CT | build-defect | run_id `16cb68d997c148a2834aad21b73bfdb6` (post-run audit) | (R1 quant-auditor finding Q-2 from `audit_trail_2026-05-18_phase-o-merge-audit.md`) | commit landed 2026-05-18 (this session) | — | Inner-CV cell selection at `_select_best_cell_inner_cv` ran full-IS optimization not walk-forward; violated design.md §5.6+§5.7 frozen spec; 100% unanimous km=0.25 across 93/93 folds was canonical conservative-Kelly-bias signature under in-sample-noise minimization; resolved via walk-forward inner-fold partitioning (3 folds × 1-session embargo) |
| 5 | 2026-05-15 ~22 CT | run-failure | `aggressive_sizing_sweep_20260515T235648Z` + `c3_2026_q1q2` + `c9_*` + 10 other Phase O.3-O.9 sub-window runs | (R1 reproducibility-verifier finding R-3) | follow-up `P1-RUNCONTEXT-ENFORCE-ALL-WALK-FORWARD-SCRIPTS` | — | 13 ancillary H062 run directories lack canonical ReproLogs at `logs/reproducibility/{run_id}.json`; only sidecar.json present; ReproLog 13-field schema requirement bypassed for timestamp-format run_ids. Pre-commit guard at `scripts/_hooks/check_repro_log.py` does not fire on the ad-hoc pattern |
| 6 | 2026-05-18 ~17 CT | build-defect | run_id `e342a2c052cb4d8db9b379a23fc5d798` (post-fix smoke run) | (smoke-mode runtime artifact) | — | — | Smoke run produced two `kelly-multiplier-0.25` annotations in the methodological annotations string; an annotation-deduplication pass is recommended (`P1-H062-ANNOTATION-DEDUP`); cosmetic, not load-bearing |

## Cross-references

- Stage tracker: [stage.md](stage.md)
- KPI report cards: `H062_kpi_report_v{N}.md`
- Audit-remediate-loop trails: [../../../docs/audits/audit_trail_2026-05-14_h062_intraday_donchian_design.md](../../../docs/audits/audit_trail_2026-05-14_h062_intraday_donchian_design.md) (design pre-reg trail)
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/)

## Append discipline

- New entries APPEND to the table; existing rows are immutable.
- Corrections produce a new row with `category=superseded` and `superseded_by` pointing to the corrected entry; the original row's `superseded_by` field is updated to point to the corrector (this is the ONLY exception to immutability and is enforced by the pre-commit guard treating supersession-only column changes as append-equivalent).
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
