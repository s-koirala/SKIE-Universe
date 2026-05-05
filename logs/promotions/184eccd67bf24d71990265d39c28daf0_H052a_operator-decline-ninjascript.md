---
schema_version: promotion_log_v1
hypothesis_id: H052a
run_id: 184eccd67bf24d71990265d39c28daf0
arm_id: all  # operator decision applies to all 4 (arm × symbol) cells
decision_type: stage-transition-decline
from_stage: kpi-report-emitted
to_stage: kpi-report-emitted  # stage unchanged; transition declined at operator discretion
operator: skoir
decision_date: 2026-05-05
git_head: c16b1ab*  # at decision time; updated on commit
---

# Operator Decision — H052a: Decline `kpi-report-emitted` → `ninjascript-implemented`

**Decision**: Operator declines the mandatory ADR-0013 §5 stage transition `kpi-report-emitted` → `ninjascript-implemented` for H052a. H052a remains at stage `kpi-report-emitted`; no NinjaScript C# implementation will be authored at this time.

**Authority**: Operator's standing directive of 2026-05-04, preserved verbatim in the conversation transcript that produced commit `244eea8` (H050 KPI report card v1 + ADR-0014):

> "The failure of profit and projected profit negates our need to move onto ninjascript implementation. This will be the user's discretion upon presentation of results in the canonical format."

This directive establishes that the `kpi-report-emitted` → `ninjascript-implemented` transition is **operator-discretionary upon review of the canonical 9-table KPI presentation**, not auto-mandated. Per ADR-0013 §5.3, every stage transition is operator-discretionary + decision-logged; per ADR-0013 §1 KPI-only philosophy, no KPI value forces or blocks any transition. Together these establish that an operator may decline the next mandatory transition; the decline is recorded here.

## KPI report card values reviewed at decision time

Reference: [research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md) (commit `c16b1ab`).

### Primary inference (T_H052a = SR_gated − SR_uncond per design.md §1)

| Symbol | T_H052a (per-sess) | LW2008 95% CI | Excludes zero | T_H052a annualised |
|---|---:|---|:--:|---:|
| ES | -0.01840 | [-0.06762, +0.02604] | NO | -0.292 |
| NQ | -0.03417 | [-0.12321, +0.00326] | NO (barely) | -0.542 |

### Realized OOS ($10k starting capital)

| Symbol | Arm | End equity | Δ pct | Max-DD |
|---|---|---:|---:|---:|
| ES | hmm_gated | $9,905.85 | -0.94% | 6.99% |
| ES | unconditional | $10,161.33 | +1.61% | 6.68% |
| NQ | hmm_gated | $10,338.73 | +3.39% | 11.83% |
| NQ | unconditional | **$11,061.27** | **+10.61%** | 7.95% |

### Forward 252-session projection ($10k start)

| Symbol | Arm | Median | P(loss) | P(double) |
|---|---|---:|---:|---:|
| ES | hmm_gated | $9,942.80 | 54.84% | 0% |
| ES | unconditional | $10,112.78 | 42.94% | 0% |
| NQ | hmm_gated | $10,244.36 | 37.12% | 0% |
| NQ | unconditional | **$10,729.27** | **18.56%** | 0% |

## Operator rationale

Per the standing directive's plain-text reading:

1. **Failure of profit on the gated arms.** Both ES and NQ HMM-gated arms produce realised OOS results that are at-or-near-flat ($9,906; $10,339 over 1.5-year OOS windows). Annualised Sharpe is negative on ES gated (-0.119) and weakly positive on NQ gated (+0.313). The gated arms do not clear a "definite-profit" bar — they are consistent with random-walk performance under the cost prior.

2. **Failure of projected profit on the gated arms.** Forward 252-session bootstrap: ES gated P(loss)=54.84%, NQ gated P(loss)=37.12%. Both are >>0% projected probability of net loss over a forward year. P(double)=0% on every cell — no realistic upside scenario reaches 2× starting capital.

3. **The hypothesis-of-record (T_H052a > 0) is NOT supported.** Point estimates negative on both symbols; LW2008 differential CIs cover zero on both → non-significant null. Per design.md §1's a-priori expectation, a null was the expected outcome — but a null is precisely a "failure" under the H_1-promotion frame.

4. **The strongest cell (NQ unconditional ORB, +0.855 annualised SR) is NOT the H052a hypothesis-of-record.** It is a literature-replication artifact (Holmberg-Lönnbark-Lundström 2013; Tsai 2019; design.md §15.1 Erratum-2) that emerges as a side-effect of the H052a backtest's unconditional baseline. To promote the unconditional NQ ORB to NinjaScript would require its own pre-registered hypothesis ID with a fresh design.md (registered under follow-up `P1-H052C-NQ-UNCONDITIONAL-ORB-PRE-REG`).

5. **Cost-of-NinjaScript-implementation outweighs the research value at this KPI level.** Bridge-mediated NinjaScript per ADR-0013 §1.2 + ADR-0002 (HMM forward filter requires Python inference at decision time per ADR-0005) is materially more complex than pure-C# implementations (the H052a NinjaScript would be a thin client invoking a Python inference service over the bridge at 10:30 ET each session). The deployment-realistic test harness has marginal value on a non-significant-null hypothesis.

## Methodological-correctness acknowledgments

Per ADR-0013 §5.3, operator decisions on hypotheses with `leakage-canary-fail`, `repro-log-incomplete`, or `post-run-audit-fail` annotations require explicit operator acknowledgment of the methodological defect.

- `leakage-canary`: **pass** — no acknowledgment required.
- `repro-log`: **complete** — no acknowledgment required.
- `post-run-audit`: **pass** — no acknowledgment required.

All methodological-correctness annotations are green or n/a. No acknowledgment required.

## Non-loss preservation

Per ADR-0013 §4.1 non-loss mandate, this decision does NOT delete or modify any of:

- The H052a design.md (frozen at `status: designed`)
- The H052a §15.1 errata addendum (preserved per Path A frozen-pre-reg amendment discipline)
- The H052a KPI report card v1 (preserved verbatim under any future v2+ emission)
- The H052a stage.md tracker (this decision adds an APPEND-ONLY row)
- The H052a failure log (entries 1-6 preserved)
- The Phase 0 + Phase 1 + Phase 2 audit trails
- The canonical run artifacts (sidecar + ReproLog + per-symbol metrics + scientific_payload SHA)

The strategy is recorded, not retired. A future operator may reverse this decision at any time and authorize bridge-mediated NinjaScript implementation; the present decision is decision-of-record at this date and run_id, not a permanent terminal verdict.

## Cross-references

- KPI report card: [research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md)
- Stage tracker (with new APPEND row recording this decision): [research/01_hypothesis_register/H052a/stage.md](../../research/01_hypothesis_register/H052a/stage.md)
- Failure log: [research/01_hypothesis_register/H052a/failure_log.md](../../research/01_hypothesis_register/H052a/failure_log.md)
- Pre-registered design: [research/01_hypothesis_register/H052a/design.md](../../research/01_hypothesis_register/H052a/design.md)
- Phase 0 ORB lit-check audit: [docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md](../../docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md)
- Phase 1 infrastructure audit: [docs/audits/audit_trail_2026-05-04_h052a-phase-1-infrastructure.md](../../docs/audits/audit_trail_2026-05-04_h052a-phase-1-infrastructure.md)
- Phase 2 build-defect audit: [docs/audits/audit_trail_2026-05-05_h052a-phase-2-build-defects.md](../../docs/audits/audit_trail_2026-05-05_h052a-phase-2-build-defects.md)
- ReproLog: [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../reproducibility/184eccd67bf24d71990265d39c28daf0.json)

## Follow-ups registered by this decision

- `P1-H052C-NQ-UNCONDITIONAL-ORB-PRE-REG` — pre-register the unconditional NQ first-hour ORB as a standalone hypothesis with its own design.md (separate from H052a's HMM-gating hypothesis). Pure-C# implementable (no HMM); appropriate as a successor with its own pre-reg.
- `P1-H052A-OPERATOR-DECLINE-NINJASCRIPT-PROJECTWIDE-ADR` — consider formalizing the user's 2026-05-04 standing directive as a project-wide ADR amendment (the directive is currently preserved in conversation transcripts but not in an ADR; a future ADR could codify "operator may decline `kpi-report-emitted` → `ninjascript-implemented` upon canonical-format presentation, with this promotion-log pattern as the recording vehicle"). Non-blocking; the present decision is fully grounded in ADR-0013 §5.3 + §1 as written.
