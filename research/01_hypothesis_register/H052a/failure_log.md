---
hypothesis_id: H052a
schema_version: failure_log_v1
created: 2026-05-05
---

# Failure Log — H052a

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.2, this is an **append-only** chronological record of every external kill, build defect, run failure, and operator override on this hypothesis. Entries cannot be removed; corrections produce additional rows annotated `superseded by entry_id N`.

The 6 build-defect entries below are the Phase 2 remediation chain that preceded the first successful H052a production walk-forward (run_id `184eccd67bf24d71990265d39c28daf0`). Detail behind each entry is preserved in [audit_trail_2026-05-05_h052a-phase-2-build-defects.md](../../../docs/audits/audit_trail_2026-05-05_h052a-phase-2-build-defects.md).

| entry_id | timestamp_ct | category | run_id_or_commit | finding_id_or_diagnosis_link | resolution_commit_or_followup | superseded_by | notes |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-05 ~11:04 | build-defect (perf O(N²)) | (1st launch; aborted at +27 min) | Phase 2 audit-remediate-loop F-Q-1 | `583a4ee` | — | `OpeningRangeBreakoutLabeller` per-session boolean mask `(session_dates_et == session_date).to_numpy()` × 2710 sessions = O(N²) at 2710 × 2710 row-pair comparisons. Stalled progress at fold-fit phase. Fixed via `pd.factorize` + change-point boundaries → O(N) (smoke test on synthetic 3,900 bars: 0.045s). Dead `σ_annualised` computation removed. |
| 2 | 2026-05-05 ~11:08 | build-defect (dtype) | (2nd launch; aborted at startup) | Phase 2 audit-remediate-loop F-Q-2 | `27ed41d` | — | `pd.merge_asof` MergeError: `session_date_et` was μs-precision (Polars→pandas natural conversion) while VIX ingest produced ms-precision dates. Fixed by casting both `sess_df['session_date_et']` and `vix['date']` to `datetime64[ns, UTC]` in `compute_vix_daily_join`. |
| 3 | 2026-05-05 ~11:12 | build-defect (dtype) | (3rd launch; aborted at startup) | Phase 2 audit-remediate-loop F-Q-3 | `3f2330a` | — | `polars.join` SchemaError: 6 H052a feature panels' `session_date_et` columns had inconsistent precision (μs from `compute_first_hour_sign`, `compute_gap_size`, `compute_dow_onehot`, `compute_eth_pre_rth`, `compute_realized_vol_per_session`; ns from `compute_vix_daily_join` post-Entry-2 fix). Fixed by uniformly casting all 6 feature panels' `session_date_et` to `pl.Datetime("ns", "UTC")` before joining. |
| 4 | 2026-05-05 ~11:18 | build-defect (dtype) | (4th launch; aborted at startup) | Phase 2 audit-remediate-loop F-Q-4 | `20e6450` | — | Orchestrator labels↔features `polars.join` SchemaError: `OpeningRangeBreakoutLabeller` produced μs-precision `session_date_et` while `compute_h052a_features` (post-Entry-3 fix) produced ns-precision. Fixed by normalising both sides to `pl.Datetime("ns", "UTC")` in the orchestrator before join. |
| 5 | 2026-05-05 ~11:24 | build-defect (API) | (5th launch; aborted at HMM selection) | Phase 2 audit-remediate-loop F-Q-5 | `0aa9258` | — | TypeError: `int(hmm.params_.n_states)` — `n_states` is a method on `HMMParams` per [src/skie_ninja/models/regime/hmm.py](../../../src/skie_ninja/models/regime/hmm.py), NOT an attribute. Additionally `SelectionResult` exposes `best_n_states` and `best_covariance_type` (NOT `best_bic` directly). Fixed by calling `hmm.params_.n_states()` and using `selection.best_n_states` / `selection.best_covariance_type` for HMM-selection metadata. |
| 6 | 2026-05-05 11:31:04 → 11:44:43 | clean-completion | run_id `184eccd67bf24d71990265d39c28daf0` (commit `0aa9258`) | (KPI report card v1) | (this commit) [H052a_kpi_report_v1.md](H052a_kpi_report_v1.md) | — | 6th launch: clean exit 0 (~14 min wall-clock; both symbols ok). ES 27/27 cfgs + NQ 27/27 cfgs. ReproLog at [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../../../logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json); scientific_payload SHA `cca86b27...`. T_H052a < 0 in point estimate on both symbols, but LW2008 differential CI covers zero on both — non-significant null. NQ unconditional ORB is the single positive cell on every metric. |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `superseded_by` pointing to the correcting row; the original row stays with all original content.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Stage tracker: [stage.md](stage.md)
- KPI report card: [v1](H052a_kpi_report_v1.md)
- Audit-remediate-loop trails:
  - [docs/audits/audit_trail_2026-05-05_h052a-phase-2-build-defects.md](../../../docs/audits/audit_trail_2026-05-05_h052a-phase-2-build-defects.md) (Phase 2 build-defect remediation chain; entries 1-5)
  - [docs/audits/audit_trail_2026-05-04_h052a-phase-1-infrastructure.md](../../../docs/audits/audit_trail_2026-05-04_h052a-phase-1-infrastructure.md) (Phase 1 R2 ACCEPT)
  - [docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md](../../../docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md) (Phase 0 lit-check; R2 ACCEPT)
