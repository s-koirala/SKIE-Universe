---
hypothesis_id: H068_v2
schema_version: stage_tracker_v1
created: 2026-05-20
---

# Stage Tracker — H068 v2

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition. The current stage of the strategy is the most recent row's `stage` value.

Stages (per ADR-0013 §1):
- `exploration-in-progress` — research / build cycles active
- `kpi-report-emitted` — full KPI report card v{N} published
- `ninjascript-implemented` — runnable C# strategy + Sim101 smoke-test record
- `ninjascript-blocked-by-non-amenable-substrate` — sub-stage per ADR-0013 §1.2 (NOT a terminal archive)
- `paper-trade-active` — running on NT8 paper account; 60-session-day clock engaged
- `paper-trade-evaluated` — clock complete; realized-vs-backtest MPPM(ρ=1)-within-CI observation recorded
- `live-promoted` — live capital deployed
- `retired` — strategy operator-retired (recorded, NOT deleted)

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-05-20 | exploration-in-progress | design.md frozen at status=designed; commit pending | skoir | initial pre-registration; multi-instrument basket expansion of H068 v1 cost-light Donchian channel-breakout per ADR-0027 §D-4 single-axis-genetic-cross discipline; closes `P1-H068-V2-EXPANDED-SUBSTRATE` BLOCKING follow-up registered by Phase O.18 closure synthesis (CLAUDE.md commit `8434c37`); universe = 3-symbol basket {ES, MGC, SIL} on canonical post-Phase-O.10 substrate `317429e4...`; NQ deliberately omitted per retail-equity-floor empirical constraint; MNQ substitution deferred per `P1-H068-V2-MNQ-EXTENSION-V3`; expected basket n_trades ≈ 7,200 (~67× v1 ES-only n=108); inferential power-lift via Grinold 1989 √breadth multiplier; audit trail [docs/audits/audit_trail_2026-05-20_h068_v2_design.md](../../../docs/audits/audit_trail_2026-05-20_h068_v2_design.md) |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report cards: `H068_v2_kpi_report_v{N}.md`
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/)
- Parent stage tracker: [H068 v1 stage.md](../H068/stage.md)
