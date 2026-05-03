---
hypothesis_id: H050
schema_version: stage_tracker_v1
created: 2026-05-03
---

# Stage Tracker — H050

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition. The current stage of the strategy is the most recent row's `stage` value. Closes follow-up `P1-ADR-0013-H050-RETROACTIVE-RETAG-EXECUTE`.

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-04-20 | exploration-in-progress | design.md frozen at status=designed; pre-reg via [research/01_hypothesis_register/H050/design.md](design.md) (commit history) | skoir | Initial pre-registration (Tier 2b, ADR-0005 + ADR-0006 scope) |
| 2026-04-26 → 2026-04-29 | exploration-in-progress (sub: production-walk-forward-attempted) | 6 production walk-forward attempts; cumulative wall-clock ~35.2 hr; aggregate disposition artifacts written: zero. Per [memo_h050-prodrun-postmortem_2026-04-30.md](../../../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md) | skoir | Run 1 killed at +180min for diagnosis (HMM cold-fit stall); Runs 2-6 terminated externally (Windows Update auto-reboot, supervisor cap, OOM heap fragmentation, OS reboot bypass). Ledger preserved per ADR-0013 §4.1 non-loss. |
| 2026-04-30 | exploration-in-progress (sub: hardening-blocker-closures) | Post-mortem audit-remediate-loop: P1-PREFLIGHT-USOSVC-TASK-DISABLE + P1-ADR-0010-LAYER-1-FRAMING-CORRECT + P1-ADR-0010-LAYER-AMENDMENT closed (commit `ec11f3a`); P1-LGB-INNER-CV-RESULT-CHECKPOINT closed; P1-WAKE-LOCK-BYPASS-INVESTIGATION closed | skoir | Three layer-of-defense for multi-hour Windows runs landed; ADR-0010 §Layer 5 USOSvc gating; ADR-0011 production walk-forward runbook in force. |
| 2026-05-03 | exploration-in-progress (sub: adr-0013-retroactive-re-tag) | [ADR-0013 §"Retroactive re-tag"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) explicitly maps H050 → `exploration-in-progress`; commit `bab405e` (ADR-0013 + design.md §8 amendment banner + project-wide cascade) | skoir | Pre-mortem dispositions (none reached) re-tagged. The original `archive(null, ...)` paths from the pre-ADR-0012 disposition tree are dissolved per ADR-0013 §1; H050 progresses through ADR-0013's stage progression model. |
| 2026-05-03 | exploration-in-progress (sub: leakage-clean-refactor) | Round-1 audit-remediate-loop (parallel quant-auditor + literature-check + reproducibility-verifier); 4 critical + 10 major findings; Round-2 remediation closed all 14; Round-3 verification: see audit trail | skoir | Path B leakage-clean refactor mirroring H053 Path B precedent. Audit trail: [docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md). KPI report card emission deferred until production walk-forward completes on the post-Cell-I substrate. |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report card: NOT YET EMITTED (deferred until production walk-forward completes; tracked under `P1-H050-KPI-REPORT-V1-EMIT`)
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/) (none yet for H050)
- Audit-remediate-loop trails:
  - [docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md) (this commit; Path B leakage-clean refactor)
  - [docs/audits/audit_trail_2026-04-30_h050-prodrun-postmortem.md](../../../docs/audits/audit_trail_2026-04-30_h050-prodrun-postmortem.md) (post-mortem of 6 prod-run attempts)
  - [docs/audits/audit_trail_2026-04-30_h050-blocking-followups.md](../../../docs/audits/audit_trail_2026-04-30_h050-blocking-followups.md) (USOSvc + ADR-0010 framing closure)
- Frozen-pre-reg amendment trails:
  - [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](aggregation_rule_addendum_2026-04-24.md)
  - [research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md](hmm_covariance_d1_equivalence_addendum_2026-04-26.md)
  - [research/01_hypothesis_register/H050/purge_rule_addendum_2026-05-03.md](purge_rule_addendum_2026-05-03.md) (this commit; F-Q-2 closure)
  - [research/01_hypothesis_register/H050/embargo_pw2004_addendum_2026-05-03.md](embargo_pw2004_addendum_2026-05-03.md) (this commit; F-L-2 closure)

## Next mandatory transitions (per ADR-0013 §5)

1. `exploration-in-progress` → `kpi-report-emitted`: requires successful production walk-forward Stage-3 run on the post-Cell-I substrate + KPI report card v1 published per ADR-0013 §3 + §3.1. Tracked under `P1-H050-KPI-REPORT-V1-EMIT`.
2. `kpi-report-emitted` → `ninjascript-implemented`: mandatory for all strategies under ADR-0013 §5 regardless of KPI values. H050 must produce a NinjaScript C# implementation in [ninjascript/strategies/](../../../ninjascript/strategies/) per ADR-0013 §5.1; bridge-mediated implementation per ADR-0013 §1.2 (HMM filter requires Python inference). Tracked under `P1-H050-NINJASCRIPT-IMPL`.
