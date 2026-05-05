---
hypothesis_id: H054
schema_version: failure_log_v1
created: 2026-05-05
---

# Failure Log — H054

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.2, this is an **append-only** chronological record of every external kill, build defect, run failure, and operator override on this hypothesis.

| entry_id | timestamp_ct | category | run_id_or_commit | finding_id_or_diagnosis_link | resolution_commit_or_followup | superseded_by | notes |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-05 ~16:55 | build-defect (API) | run_id `39922391abf14fc6bd8d0f61a256b5d6` (1st attempt; aborted at Opdyke 2007 univariate CI) | Phase 2 audit-remediate-loop F-Q-1 | this commit | — | AttributeError: `'SharpeCI' object has no attribute 'point_estimate'`. The `SharpeCI` dataclass at [src/skie_ninja/inference/stats/sharpe_ci.py](../../../src/skie_ninja/inference/stats/sharpe_ci.py) exposes the point estimate as the field `sharpe`, NOT `point_estimate`. Fixed inline by changing `opdyke_ci.point_estimate` → `opdyke_ci.sharpe`. |
| 2 | 2026-05-05 16:55:18 → 17:01:59 | clean-completion | run_id `dd916fc67b504c528fda7abbde6700f1` (commit `66dab5d`) | (KPI report card v1) | (this commit) [H054_kpi_report_v1.md](H054_kpi_report_v1.md) | — | 2nd launch: clean exit 0 (~7 min wall-clock; ES-only). 27/27 cfgs evaluated; HMM (full, 3-state) selected; stress_state = 2 (highest realized_vol emission). Anti-gate fired on 7/237 OOS sessions (2.95% trade rate). T_H054_b PRIMARY: SR_anti_gated annualised +0.573, Opdyke 2007 95% CI per-session [-0.0327, +0.1050] (covers zero → non-significant null). T_H054_a SECONDARY: SR_anti − SR_uncond annualised +0.630, LW2008 CI per-session [-0.0411, +0.1394] (covers zero). Realized $10K +3.50% (anti) vs -0.54% (uncond). Forward 252-session: anti median $10,319 with P(loss)=29% vs uncond $9,930 with P(loss)=53%. ReproLog at [logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json](../../../logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json); scientific_payload SHA `395dd008...`. |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `superseded_by` pointing to the correcting row; the original row stays with all original content.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Stage tracker: [stage.md](stage.md)
- KPI report card: [v1](H054_kpi_report_v1.md)
- Audit-remediate-loop trails:
  - [docs/audits/audit_trail_2026-05-05_h054-pre-reg.md](../../../docs/audits/audit_trail_2026-05-05_h054-pre-reg.md) (Pre-reg; R3 ACCEPT)
  - [docs/audits/audit_trail_2026-05-05_h054-phase-2.md](../../../docs/audits/audit_trail_2026-05-05_h054-phase-2.md) (Phase 2 build-defect + clean run; entries 1-2)
