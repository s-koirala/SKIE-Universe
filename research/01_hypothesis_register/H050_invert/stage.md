---
hypothesis_id: H050_invert
parent_hypothesis_id: H050
schema_version: stage_tracker_v1
created: 2026-05-20
---

# Stage Tracker — H050.invert

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition. The current stage of the strategy is the most recent row's `stage` value.

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-05-20 | exploration-in-progress | design.md frozen at status=designed; pre-reg per [design.md](design.md); genetic-successor cross-citation per ADR-0027 §D-4 in §17 | skoir | Initial pre-registration. Genetic successor to H050 v1 per ADR-0027 §D-4; tests H-b anti-selection sub-hypothesis via gate-state inversion (gate = lowest-mean state vs H050 v1's highest-mean). Paired with sibling [H050.stable-state](../H050_stable_state/design.md) for mechanism-discrimination. |
| 2026-05-20 | kpi-report-emitted | KPI report card v1 emitted in smoke mode per [H050_invert_kpi_report_v1.md](H050_invert_kpi_report_v1.md); orchestrator + tests + audit trail landed per [docs/audits/audit_trail_2026-05-20_h050_invert_orchestrator_smoke.md](../../../docs/audits/audit_trail_2026-05-20_h050_invert_orchestrator_smoke.md). Smoke run_id `29eac562e2354b91acdb0f65a7198b00` on canonical post-Phase-O.10 substrate `317429e4...`. | skoir | First KPI emission. Closes the H050.invert design.md §11.2 BLOCKING preconditions `P1-H050-INVERT-WALK-FORWARD-ORCHESTRATOR-IMPL` + `P1-H050-INVERT-LEAKAGE-CANARY-INTEGRATION-TEST` + `P1-H050-INVERT-PARITY-INVARIANT-TEST`. v1 is smoke-mode (1-cell label grid + 5 lgb draws + 2 inner CV folds); v2 reserved for full production walk-forward per `P1-H050-INVERT-KPI-V2-FULL-RUN`. Empirical-prediction discriminant per parent INVESTIGATE memo §7.3 will be readable post-smoke-completion via Tables 1-9 of the v1 KPI report card (population is a follow-up commit cycle gated on the smoke run's clean exit + sidecar SHA256 capture). |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Parent H050: [research/01_hypothesis_register/H050/stage.md](../H050/stage.md) (final stage: `kpi-report-emitted` 2026-05-04)
- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
- Sibling H050.stable-state: [research/01_hypothesis_register/H050_stable_state/stage.md](../H050_stable_state/stage.md)
- Failure log: [failure_log.md](failure_log.md)
- KPI report card: [H050_invert_kpi_report_v0.md](H050_invert_kpi_report_v0.md) (pre-emission v0 skeleton)
- Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-20_h050_successor_variants.md](../../../docs/audits/audit_trail_2026-05-20_h050_successor_variants.md)

## Next mandatory transitions (per ADR-0013 §5)

1. `exploration-in-progress` → `kpi-report-emitted`: BLOCKING preconditions per [design.md §11.2](design.md):
   - `P1-H050-INVERT-WALK-FORWARD-ORCHESTRATOR-IMPL` (orchestrator)
   - `P1-H050-INVERT-LEAKAGE-CANARY-INTEGRATION-TEST` (Cycle-4 leak canary)
   - `P1-H050-INVERT-PARITY-INVARIANT-TEST` (gate-label-swap parity to H050 v1)
2. `kpi-report-emitted` → `ninjascript-implemented`: mandatory per ADR-0013 §5; bridge-mediated per ADR-0013 §1.2 (HMM filter requires Python inference); operator-discretionary timing per the 2026-05-04 standing decline-ninjascript directive. Tracked under `P1-H050-INVERT-NINJASCRIPT-IMPL`.
