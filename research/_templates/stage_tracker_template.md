---
hypothesis_id: H{NNN}
schema_version: stage_tracker_v1
created: YYYY-MM-DD
---

# Stage Tracker — H{NNN}

Per [ADR-0013](../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition. The current stage of the strategy is the most recent row's `stage` value.

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
| YYYY-MM-DD | exploration-in-progress | design.md frozen at status=designed; commit {sha} | skoir | initial pre-registration |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report cards: `{HID}_kpi_report_v{N}.md`
- Promotion logs: [../../logs/promotions/](../../logs/promotions/)
