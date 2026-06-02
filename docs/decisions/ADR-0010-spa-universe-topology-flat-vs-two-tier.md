---
id: ADR-0010
title: SPA-universe topology — flat single-universe vs two-tier Family A / Family B
status: proposed
date: 2026-04-27
deciders: skoir
related: ADR-0003-spa-vs-romanowolf, ADR-0008-spa-omega-method, P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE
---

# ADR-0010 — SPA-universe topology: flat single-universe vs two-tier Family A / Family B

## Status

**Proposed (stub).** This ADR is opened in stub form to record the decision surface; full text + decision land in a follow-up commit after empirical evidence is gathered. Binding before any family-aggregate inference report (Hansen 2005 SPA p-value, Romano-Wolf step-down family-wise rejection set, etc.) is emitted as evidence-bar artefact. Not binding for any other operation.

## Context

The 2026-04-27 merge of sibling branch `claude/laughing-shamir-059944` into the chart-reader cohort branch surfaced a structural incompatibility between two independently-developed SPA-universe topologies:

### Topology 1 — Flat single-universe (sibling H053 + project precedent)

Per [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/) §1 + §10.1.5 (verbatim, frozen at `designed` 2026-04-28):

> `T_H053^{(arm)}` enters the project's Hansen SPA universe per ADR-0003 / ADR-0008 alongside H050/H051/H052a/H052b. Three slots (Arm 1, Arm 2, Arm 3) are pre-registered ex ante; arms whose §11 prerequisites fail to land before `running` consume their slot as `archive(null, prerequisite-not-met)` per §8, preserving family size at exactly 3.

All hypotheses (H050, H051, H052a, H052b, H053-arms-1/2/3, plus the chart-reader cohort post-renumber as H057+) enter a **single Hansen SPA universe** via `universe_snapshot_id`. H053 contributes 3 ex-ante slots; total `M = 1 + 1 + 1 + 1 + 3 + (chart-reader-M) ≥ 12` depending on how the chart-reader cohort is admitted under this topology. `omega_method = bootstrap` per [ADR-0008](ADR-0008-spa-omega-method.md) two-tier rule (`M ≥ 2`); shared bootstrap indices across all strategies preserve cross-sectional dependence per Hansen 2005 §3.

H050 enters this flat universe under its `H050.yaml` + `scripts/run_walk_forward.py` wiring (Hansen SPA), which is the wiring that has actually executed in the H050 production run-1 (audit trail [audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md)). The H050 design.md frozen pre-reg specifies Romano-Wolf step-down per [ADR-0003](ADR-0003-spa-vs-romanowolf.md), creating an internal inconsistency tracked under `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` — not yet adjudicated.

### Topology 2 — Two-tier Family A / Family B (chart-reader cohort)

Per [docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md](../research_notes/memo_chartreader-research-synthesis_2026-04-27.md) §6 (verbatim, post-Round-1 audit-remediation):

> **Family A** (regime-lift, frozen pre-reg): `{H050}` (M=1, `omega_method=hac` per ADR-0008 single-strategy degenerate handling; H050 stays under Romano-Wolf step-down per ADR-0003 per its frozen pre-reg).
> **Family B** (chart-reader cohort, model-class lift): `{H057, H058a, H058b, H059, H060}` (M=5, `omega_method=bootstrap`). H050 is the **baseline anchor only** — NOT a Family B member.

Test statistic per Family B arm: `T_arm = SR_arm_gated − SR_H050_gated`. The split was introduced by Round-1 quant-auditor finding Q-R1-1 + Q-R1-12 (chart-reader [audit_trail_2026-04-27_chartreader-hypothesis-package.md](../audits/audit_trail_2026-04-27_chartreader-hypothesis-package.md)) on the grounds that Hansen 2005 SPA composite null `H_0: max_k E[d_k] ≤ 0` requires comparable performance differentials across `k`; mixing within-arm (`gated − unconditional`) and cross-arm (`arm_gated − H050_gated`) statistics in a single family violates this, AND H050's frozen pre-reg specifies Romano-Wolf, not Hansen SPA.

Under this topology H051 / H052a / H052b / sibling H053 have **no declared home** — the synthesis memo §6 only covers H050 + chart-reader cohort.

### Why the topologies are incompatible

H050 cannot simultaneously (a) sit alone in Family A under Romano-Wolf step-down (Topology 2) AND (b) sit in a flat Hansen SPA universe alongside H051/H052a/H052b/H053-arms (Topology 1). Both branches added work that depends on different resolutions of `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE`; the merge surfaces the conflict but does not adjudicate it.

The chart-reader cohort's contrast statistic `T_arm = SR_arm_gated − SR_H050_gated` is also not in canonical form for Topology 1 (Topology 1 expects per-strategy Sharpe vs a passive-long benchmark per H053 §1, not paired-cross-arm differentials).

## Decision (TBD)

To be filled in by the audit-remediated decision process. Three plausible resolutions:

1. **Adopt Topology 1 (flat universe)**, retire Topology 2. Requires:
   - Amending `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` resolution to "Hansen SPA wiring is canonical; design.md Romano-Wolf reference treated as documentation drift" — closes the H050 inconsistency in favor of the executed wiring.
   - Re-spec'ing the chart-reader cohort's test statistic from `T_arm = SR_arm_gated − SR_H050_gated` to per-strategy Sharpe vs passive-long benchmark to match Topology 1 form. This is a successor-ID action for H057-H060 (frozen-pre-reg violation otherwise).
   - Updating the chart-reader synthesis memo §6 + each H057-H060 §1 + §6 to declare Topology 1 entry, dropping Family A/B framing.

2. **Adopt Topology 2 (two-tier)**, retire Topology 1. Requires:
   - Amending `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` resolution to "Romano-Wolf is canonical; H050.yaml + run_walk_forward.py rewire to Romano-Wolf" — closes the H050 inconsistency in favor of the design.md pre-reg.
   - Re-spec'ing sibling H053 + H051 + H052a + H052b's SPA entry to either join Family A (regime-lift) or open a Family C (mediation-lift, Family D pairs-trade-lift, etc.). Each is a successor-ID action.
   - Updating sibling H053 design.md §1 + §10.1.5 to reflect the new family entry. Successor-ID required.

3. **Hybrid: flat universe is the canonical evaluation surface, Family A/B is a descriptive partition.** The chart-reader cohort retains its `T_arm = SR_arm_gated − SR_H050_gated` paired-differential statistic for descriptive reporting, but family-aggregate inference is computed on the flat universe with all hypotheses contributing per-strategy Sharpe vs passive-long. This requires substantial methodological work (the paired-differential statistic and the per-strategy-vs-benchmark statistic are different objects; a unified report needs an explicit reconciliation rule).

## Consequences (TBD)

To be filled in. Each resolution path has different consequences for:

- Successor-ID requirements across H050 / H051 / H052a / H052b / sibling-H053 / H057 / H058 / H059 / H060.
- Operational changes to `H050.yaml` and `scripts/run_walk_forward.py` (Topology 2 requires Romano-Wolf wiring).
- Rebuild of the cross-cutting `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` resolution path.
- Documentation cascade in CLAUDE.md, synthesis memo, sibling H053 docs, chart-reader cohort docs.

## References

- [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md) §1 + §10.1.5 (sibling, flat-universe topology).
- [docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md](../research_notes/memo_chartreader-research-synthesis_2026-04-27.md) §6 (chart-reader cohort, two-tier topology).
- [docs/research_notes/memo_branch-merge-decision_2026-04-27.md](../research_notes/memo_branch-merge-decision_2026-04-27.md) §10 question 2 (audit-remediated framing of the incompatibility).
- [docs/audits/audit_trail_2026-04-27_chartreader-hypothesis-package.md](../audits/audit_trail_2026-04-27_chartreader-hypothesis-package.md) Q-R1-1 + Q-R1-12 (origin of the two-tier framing).
- [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §1 (Romano-Wolf pre-reg per ADR-0003).
- [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) §4.3 (`P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` registration).
- [ADR-0003](ADR-0003-spa-vs-romanowolf.md) — SPA vs Romano-Wolf option-C ("both with explicit rules") which currently does not bind on this question.
- [ADR-0008](ADR-0008-spa-omega-method.md) — SPA omega method selection which assumes a single Hansen SPA universe.

## Related follow-ups

- **`P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE`** (open) — co-binding with this ADR; same underlying question framed from H050's vantage.
- **`P1-CHARTREADER-PER-ARM-POWER-CALC`** (open) — the per-arm power calculation depends on test-statistic form; topology choice changes the form.
- **`P1-H053-FILENAME-CONVENTION-NORMALISE`** (open) — sibling H053 file-naming deviation; not directly related to this ADR but tracked alongside the other H053-merge follow-ups.
