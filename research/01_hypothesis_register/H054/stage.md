---
hypothesis_id: H054
schema_version: stage_tracker_v1
created: 2026-05-05
---

# Stage Tracker — H054

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition.

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-05-05 | exploration-in-progress (sub: pre-reg-drafted) | design.md drafted; Phase 0 lit-check verdict literature-silent ([lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md)); Round-1 audit BLOCK (5 critical/major + 5 minor); Round-2 inline remediation (10/10 closed); Round-3 self-verification ACCEPT; design.md + data_requirements.md `status: draft` → `status: designed` | skoir | First H054 pre-registration; commit `66dab5d` (PR #3 merged 2026-05-05 21:26 UTC). Audit trail: [audit_trail_2026-05-05_h054-pre-reg.md](../../../docs/audits/audit_trail_2026-05-05_h054-pre-reg.md). |
| 2026-05-05 | exploration-in-progress (sub: phase-1-implementation + production-walk-forward) | Phase 1 deliverables: [config/hypotheses/H054.yaml](../../../config/hypotheses/H054.yaml) + [scripts/run_h054_walk_forward.py](../../../scripts/run_h054_walk_forward.py) (gate inverted; T_H054_b primary via Opdyke 2007 univariate CI; ES-only; AST parse OK) + [tests/integration/test_h054_pit.py](../../../tests/integration/test_h054_pit.py) 17/17 PASSED (4 BLOCKING follow-ups closed). Phase 2 production walk-forward run_id `dd916fc67b504c528fda7abbde6700f1` clean exit 0 at 17:01 CT (~7 min wall-clock). 1 build defect remediated inline at attempt-1 → attempt-2 (SharpeCI.point_estimate AttributeError; field is `sharpe`). | skoir | ReproLog at [logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json](../../../logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json); scientific_payload SHA `395dd008...`. |
| **2026-05-05** | **kpi-report-emitted** | **KPI report card [v1](H054_kpi_report_v1.md) emitted; ADR-0013 §3 + ADR-0014 §3.2 9-table format; orchestrator [scripts/run_h054_walk_forward.py](../../../scripts/run_h054_walk_forward.py); Phase 2 audit trail [audit_trail_2026-05-05_h054-phase-2.md](../../../docs/audits/audit_trail_2026-05-05_h054-phase-2.md)** | **skoir** | **First H054 KPI report card. Stage transition `exploration-in-progress` → `kpi-report-emitted` per ADR-0013 §1. All methodological-correctness annotations green or n/a. Performance KPIs: T_H054_b SR_anti_gated = +0.0362 per-session [-0.0327, +0.1050] Opdyke 2007 CI; CI covers zero (PRIMARY non-significant null). T_H054_a SR_anti_gated − SR_uncond = +0.0398 per-session [-0.0411, +0.1394] LW2008 CI; CI covers zero (SECONDARY non-significant null). Realized $10K +3.50% (anti-gated) vs -0.54% (unconditional); annualised SR +0.573 (anti-gated) vs -0.057 (uncond). Forward 252-session projection: anti-gated median $10,319 with P(loss)=29.24% vs uncond median $9,930 with P(loss)=52.50%. Anti-gate fired on 7/237 OOS sessions (2.95% trade rate; matches design.md §9.5 expectation-management note "structurally low-power; directional indicator + power-floor probe"). Point-positive AND directionally consistent with H052a-implied reading on every metric, but CIs cover zero at α=0.05. Per design.md §10 decision rule: non-significant null bucket; operator may reasonably decline NinjaScript progression OR pursue H054 v2 with pooled ES+NQ+MES+MNQ to accumulate n_anti to ≥174 sessions for adequate power.** |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original row stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Failure log: [failure_log.md](failure_log.md)
- KPI report card: [v1](H054_kpi_report_v1.md) (emitted 2026-05-05)
- Promotion logs: [../../../logs/promotions/](../../../logs/promotions/) (none yet for H054)
- Audit-remediate-loop trails:
  - [docs/audits/audit_trail_2026-05-05_h054-pre-reg.md](../../../docs/audits/audit_trail_2026-05-05_h054-pre-reg.md) (Pre-reg R1+R2+R3 ACCEPT)
  - [docs/audits/audit_trail_2026-05-05_h054-phase-2.md](../../../docs/audits/audit_trail_2026-05-05_h054-phase-2.md) (Phase 2 build-defect remediation + clean run; this commit)

## Next mandatory transitions (per ADR-0013 §5)

1. ~~`exploration-in-progress` → `kpi-report-emitted`~~: **CLOSED 2026-05-05** via KPI report card [v1](H054_kpi_report_v1.md) emission.
2. `kpi-report-emitted` → `ninjascript-implemented`: per ADR-0013 §5 mandatory in nominal flow; per the user's 2026-05-04 standing directive, this transition is **operator-discretionary upon review of v1 KPI report card values**. Bridge-mediated implementation per ADR-0013 §1.2 + ADR-0002 if undertaken (HMM forward filter at session-open requires Python inference at decision time per ADR-0005). Tracked under `P1-H054-NINJASCRIPT-IMPL`. Three options per H054_kpi_report_v1.md operator review section: (a) decline + record; (b) pursue v2 with pooled multi-instrument; (c) pursue bridge-mediated NinjaScript.
