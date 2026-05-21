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
| 2026-05-18 | kpi-report-emitted (v2) | [H062_kpi_report_v2.md](H062_kpi_report_v2.md) emitted; sidecar [artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json](../../../artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json) with scientific_payload_sha256=`5f876797edfcabb5336581fce6b7d9f496fce00c29fc08f883256266eb70520f`; run_id `eb729b201595484594ce4c9ddde72d05` | skoir | v2 corrects v1 critical methodological defects (MPPM double-log + walk-forward inner-CV); MPPM(ρ=1) sign-flips +0.0950 [-0.343, +0.540]; realized OOS +217.57% vs passive +460.69%; max-DD 93.26% (catastrophic); τ_3 = +0.737; per Phase O.10 audit trail [docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md) |
| 2026-05-20 | kpi-report-emitted (v4) | [H062_kpi_report_v4.md](H062_kpi_report_v4.md) emitted; sidecar [artifacts/runs/H062/8df1ddc22b534561b68c65b2b29c2ee7/sidecar.json](../../../artifacts/runs/H062/8df1ddc22b534561b68c65b2b29c2ee7/sidecar.json) with scientific_payload_sha256=`8ef13dfbe95a309b2c981b3e387faeaf82f0970002ce993b8ca9c54fce232ab7`; run_id `8df1ddc22b534561b68c65b2b29c2ee7` | skoir | Phase O.20 first empirical emission of [ADR-0028 §D-2 `cost-friction-dominated-edge-present` annotation](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) via H062 v3 smoke fixture + zero-cost reference cell `5e52f0b7ddd94ecea3187566c0e255d0` (Phase O.15 A0 baseline +261.88%); cost-applied basket −99.9998%; MPPM(ρ=1)= −1.117 [−1.518, −0.688] CI excludes zero negatively; H_1 cleanly REJECTED; v3 smoke parity verified at structural fields + qualitative verdict (bootstrap CIs shift at rng-stream-precision per `P1-ADR-0028-COST-FRICTION-EDGE-RNG-STREAM-IMPACT`); audit trail [docs/audits/audit_trail_2026-05-20_adr-0028-first-cost-friction-edge-emission.md](../../../docs/audits/audit_trail_2026-05-20_adr-0028-first-cost-friction-edge-emission.md); closes `P1-ADR-0028-FIRST-COST-FRICTION-EDGE-EMPIRICAL-EMISSION` (BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE) |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report cards: `H062_kpi_report_v{N}.md`
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/)
