---
hypothesis_id: H065
schema_version: stage_tracker_v1
created: 2026-05-15
---

# Stage Tracker — H065

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
| 2026-05-15 | exploration-in-progress | design.md frozen at status=designed; commit pending | skoir | initial pre-registration; TP-overlay extension of H062 v1; M-grid {1.0, 1.5, 2.0, 2.5}; per CLAUDE.md Phase O.5 ledger + audit trail [docs/audits/audit_trail_2026-05-15_h065_v1.md](../../../docs/audits/audit_trail_2026-05-15_h065_v1.md) |
| 2026-05-15 | kpi-report-emitted | [H065_kpi_report_v1.md](H065_kpi_report_v1.md) emitted; sidecar [artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/sweep_sidecar.json](../../../artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/sweep_sidecar.json) with sha256=`ea12473729264d25d009834c537cb6f657d51c15a1a4f9bca9cb24496798d60d`; run_id `tp_overlay_sweep_20260516T030515Z` | skoir | first H065 TP-overlay sweep; 16-cell representative grid (M × Kelly × symbol); basket-level H_1 **null** on all M ∈ {1.0, 1.5, 2.0, 2.5} (MPPM CIs cover zero AND M=1.0 inverts skew direction); SIL M=∞ fixed-rebase produces strongest single-cell outcome (+446% ROI, MPPM CI [+0.087, +0.459] EXCLUDES ZERO POS, MaxDD 25%); NQ structurally infeasible at $10K starting equity; per CLAUDE.md Phase O.5 ledger + audit trail [docs/audits/audit_trail_2026-05-15_h065_v1.md](../../../docs/audits/audit_trail_2026-05-15_h065_v1.md) Round-1 verdict ACCEPT-WITH-RESIDUALS |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report cards: `H065_kpi_report_v{N}.md`
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/)
