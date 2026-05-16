---
hypothesis_id: H055
schema_version: stage_tracker_v1
created: 2026-05-06
---

# Stage Tracker — H055

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition. The current stage of the strategy is the most recent row's `stage` value.

Stages (per ADR-0013 §1):
- `exploration-in-progress` — research / build cycles active
- `kpi-report-emitted` — full KPI report card v{N} published
- `ninjascript-implemented` — runnable C# strategy + Sim101 smoke-test record
- `ninjascript-blocked-by-non-amenable-substrate` — sub-stage per ADR-0013 §1.2 (NOT a terminal archive)
- `paper-trade-active` — running on NT8 paper account; 60-session-day clock engaged
- `paper-trade-evaluated` — clock complete; realized-vs-backtest Sharpe-within-CI observation recorded
- `live-promoted` — live capital deployed
- `retired` — strategy operator-retired (recorded, NOT deleted)

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-05-06 | exploration-in-progress | design.md frozen at status=designed; commit pending | skoir | initial pre-registration; 3-round audit-remediate-loop ACCEPT per [docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../../../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md) |
| 2026-05-15 | kpi-report-emitted | [H055_kpi_report_v1.md](H055_kpi_report_v1.md) emitted from v2 sweep (sidecar SHA `83cd09e88476b93d...`; git_head `07d58a42`); 5-config aggressive-sizing variant comparison on 4-symbol cross-futures basket | skoir | v1 KPI emission per ADR-0017 + ADR-0018 + ADR-0024 paradigm; substrate dataset_checksum `b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce`; 1-round audit-remediate-loop per [docs/audits/audit_trail_2026-05-15_h055_v2.md](../../../docs/audits/audit_trail_2026-05-15_h055_v2.md); strongest cell = MGC C9 BOCD step-up (MPPM=+0.185; Calmar=+0.861; OOS +58%); basket C9 +12.1% OOS / +2.5% sub-window — load-bearing variant for forward consideration |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report cards: `H055_kpi_report_v{N}.md`
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/)
