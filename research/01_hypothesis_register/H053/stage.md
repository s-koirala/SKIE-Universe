---
hypothesis_id: H053
schema_version: stage_tracker_v1
created: 2026-05-03
---

# Stage Tracker — H053

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition. The current stage of the strategy is the most recent row's `stage` value.

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-04-28 | exploration-in-progress | design.md frozen at status=designed; commit 660c2ef ([dd491fb] design audit-remediate trail) | skoir | initial pre-registration via cherry-pick from sibling branch |
| 2026-05-01 | exploration-in-progress (sub: stage-1-kpi-recorded) | Stage-1 mediator-only run; sidecar 316266d848dadcbffa6 at runs/h053/stage1/...; commit 76599bd | skoir | original disposition `archive(null, descriptive-mediation-only)` re-tagged per ADR-0013 §"Retroactive re-tag" |
| 2026-05-01 | exploration-in-progress (sub: stage-2-kpi-recorded) | Stage-2 multi-tf+mediation run; sidecar a27a46de2bc18948f65; commit ee2eeaa | skoir | original disposition `descriptive-positive` re-tagged per ADR-0013 |
| 2026-05-01 | exploration-in-progress (sub: stage-3-first-pass-defective-substrate) | Stage-3 first-pass run; sidecar 6a001cf4a847c4d70; commit 28f93ec; provisional `archive(null)` reversed by 8c1de7c | skoir | Daily-405-gate truncation defect (only ~178 train sessions); pre-disposition reversal per ADR-0013 |
| 2026-05-03 | exploration-in-progress (sub: stage-3-v2-kpi-recorded) | Stage-3 v2 run; sidecar 0cd96f55ca78916257e; commit 221a635; KPI report card [v1](H053_kpi_report_v1.md) | skoir | original disposition `calibration-failed` (under ADR-0012); re-tagged `kpi-report-emitted` per ADR-0013 §"Retroactive re-tag" |
| 2026-05-03 | exploration-in-progress (sub: stage-3-v3-leakage-clean-attempt) | Stage-3 v3 Path B Round-1; sidecar 4cf291c036505f63f24; uncommitted (script untracked at run-time) | skoir | Round-1 audit BLOCK verdict (2 critical leakage residuals: F-V3-1 CPCV full-panel + F-V3-2 iso not pre-test causal). Sidecar preserved per ADR-0013 §4.1 non-loss; not promoted to v{N} kpi_report. |
| **2026-05-03** | **kpi-report-emitted** | **Stage-3 v4 Path B Round-2 + Round-3 verification (verdict ACCEPT); sidecar 4d5a826babf25cf2697; ReproLog at logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json; KPI report card [v2](H053_kpi_report_v2.md)** | **skoir** | **All 6 v3 audit findings closed (F-V3-1 OOS-only CPCV + F-V3-2 pre-test causal iso + F-V3-3 n_splits=5 + F-V3-4 embargo=4 + F-V3-5 LW2008 sharpe-vs-bench CI + F-V3-6 RunContext/ReproLog). Stage-3 v4 is the canonical leakage-clean H053 disposition.** |
| 2026-05-03 | kpi-report-emitted (sub: kpi-v3-with-projection) | KPI report card [v3](H053_kpi_report_v3.md) emitted; same v4 sidecar source; adds mandatory Realized-OOS + Forward-Projection block per ADR-0013 §3.1 amendment; simulation primitive at [scripts/simulate_h053_v4_10k_2026.py](../../../scripts/simulate_h053_v4_10k_2026.py); log at [logs/simulate_10k_2026.log](../../../logs/simulate_10k_2026.log) | skoir | Stage value unchanged (still `kpi-report-emitted`); v3 supersedes v2 substantively per ADR-0013 §3 versioning. v2 + v1 preserved verbatim per ADR-0013 §4.1 non-loss. |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report cards: [v1](H053_kpi_report_v1.md), [v2](H053_kpi_report_v2.md)
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/) (none yet for H053)
- Audit-remediate-loop trails:
  - [audit_trail_2026-04-28_h053-design.md](../../../docs/audits/audit_trail_2026-04-28_h053-design.md)
  - [audit_trail_2026-05-01_h053-disposition-reversal.md](../../../docs/audits/audit_trail_2026-05-01_h053-disposition-reversal.md)
  - [audit_trail_2026-05-03_h053-stage3-v2.md](../../../docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md)
  - [audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md) (this commit; consolidates Path B R1+R2+R3)

## Next mandatory transition (per ADR-0013 §5)

`kpi-report-emitted` → `ninjascript-implemented` is mandatory for all strategies under ADR-0013 §5 regardless of KPI values. H053 must produce a NinjaScript C# implementation in [ninjascript/strategies/](../../../ninjascript/strategies/) with §15 Sim101 smoke-test record per ADR-0013 §5.1. Tracked under follow-up `P1-H053-NINJASCRIPT-IMPL`.
