---
hypothesis_id: H062
schema_version: stage_tracker_v1
created: 2026-05-14
---

# Stage Tracker — H062

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
| 2026-05-14 | exploration-in-progress | design.md frozen at status=designed; commit pending | skoir | initial pre-registration; 2-round audit-remediate-loop ACCEPT per [docs/audits/audit_trail_2026-05-14_h062_intraday_donchian_design.md](../../../docs/audits/audit_trail_2026-05-14_h062_intraday_donchian_design.md) |
| 2026-05-15 | kpi-report-emitted | [H062_kpi_report_v1.md](H062_kpi_report_v1.md) emitted; sidecar [artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json](../../../artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json) with scientific_payload_sha256=`fbd85226d304b7dacc1e2b2ef0f701be860a6ed8808a214a47031cfdd054612c`; run_id `16cb68d997c148a2834aad21b73bfdb6` | skoir | first production walk-forward; 93 folds × 2,944 OOS sessions × 8,270 trades; non-significant null (basket MPPM CI=[-0.599, +0.172] covers zero; all 4 ADR-0017 primary survival metrics marginal); skew-positive payoff τ_3=+0.740 confirms design.md §13 prediction; quarter-Kelly unanimous 93/93 folds; realized OOS +43.25% vs passive +304.47%; MaxDD 90.97% vs passive 39.74%; per CLAUDE.md Phase O.2 ledger + audit trail [docs/audits/audit_trail_2026-05-15_h062_launch_readiness.md](../../../docs/audits/audit_trail_2026-05-15_h062_launch_readiness.md) |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report cards: `H062_kpi_report_v{N}.md`
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/)
