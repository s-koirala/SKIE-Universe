---
hypothesis_id: H067
schema_version: stage_tracker_v1
created: 2026-05-19
---

# Stage Tracker — H067

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
| 2026-05-19 | exploration-in-progress | design.md frozen at status=designed; commit pending | skoir | initial pre-registration; N-lot cost-light genetic successor of H065 v2 M_inf-SIL cell per cross-hypothesis investigation 2026-05-19 §7.4 #1 candidacy; primary cost-reduction axis = N-lot position-size grid {1, 2, 3, 4, 5}; two-cost-arm emission (A0 zero-cost + A1 conservative_prior) per ADR-0028 §D-2; substrate `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`; audit trail [docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md](../../../docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md) |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report cards: `H067_kpi_report_v{N}.md`
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/)
