---
hypothesis_id: H050_stable_state
parent_hypothesis_id: H050
schema_version: stage_tracker_v1
created: 2026-05-20
---

# Stage Tracker — H050.stable-state

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition. The current stage of the strategy is the most recent row's `stage` value.

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-05-20 | exploration-in-progress | design.md frozen at status=designed; pre-reg per [design.md](design.md); genetic-successor cross-citation per ADR-0027 §D-4 in §17 | skoir | Initial pre-registration. Genetic successor to H050 v1 per ADR-0027 §D-4; tests H-c whipsaw sub-hypothesis via N-bar state-stability filter (N grid `{3, 5, 10, 20}` 1-min bars; H050 v1 §5 line 63 canonical highest-mean ordering preserved). Paired with sibling [H050.invert](../H050_invert/design.md) for mechanism-discrimination. |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Parent H050: [research/01_hypothesis_register/H050/stage.md](../H050/stage.md) (final stage: `kpi-report-emitted` 2026-05-04)
- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
- Sibling H050.invert: [research/01_hypothesis_register/H050_invert/stage.md](../H050_invert/stage.md)
- Failure log: [failure_log.md](failure_log.md)
- KPI report card: [H050_stable_state_kpi_report_v0.md](H050_stable_state_kpi_report_v0.md) (pre-emission v0 skeleton)
- Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-20_h050_successor_variants.md](../../../docs/audits/audit_trail_2026-05-20_h050_successor_variants.md)

## Next mandatory transitions (per ADR-0013 §5)

1. `exploration-in-progress` → `kpi-report-emitted`: BLOCKING preconditions per [design.md §11.2](design.md):
   - `P1-H050-STABLE-STATE-WALK-FORWARD-ORCHESTRATOR-IMPL` (orchestrator with per-N grid)
   - `P1-H050-STABLE-STATE-LEAKAGE-CANARY-INTEGRATION-TEST` (Cycle-4 leak canary)
   - `P1-H050-STABLE-STATE-FOLD-CONTINUITY-TEST` (counter reset / carry policy at fold boundaries)
2. `kpi-report-emitted` → `ninjascript-implemented`: mandatory per ADR-0013 §5; bridge-mediated per ADR-0013 §1.2 (HMM filter requires Python inference); operator-discretionary timing per the 2026-05-04 standing decline-ninjascript directive. Tracked under `P1-H050-STABLE-STATE-NINJASCRIPT-IMPL`.
