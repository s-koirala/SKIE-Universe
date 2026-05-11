---
id: ADR-0003
title: SPA vs Romano-Wolf stepwise as primary multiple-testing control
status: proposed
date: 2026-04-15
decision-owner: Lead researcher
supersedes: none
related:
  - plan/buildouts/implementation-plan_2026-04-15.md §5
  - research/03_audits/audit-round1-quant_2026-04-15.md #7
---

# ADR-0003 — SPA vs Romano-Wolf stepwise

## Status

Proposed. To be accepted in Phase 1 after empirical comparison on the first 10 hypotheses through the gate.

## Context

The inference gate ([plan §5](../../plan/buildouts/implementation-plan_2026-04-15.md)) must control family-wise or false-discovery error across a growing universe of candidate strategies. Two candidate controls:

- **Hansen SPA** ([Hansen 2005](https://doi.org/10.1198/073500105000000063)): test-of-superior-predictive-ability requires a *common OOS sample* across all candidates. Sequentially appending new strategies with heterogeneous OOS violates the null construction: each new strategy has its own OOS window, and the SPA p-value becomes ill-defined unless historical strategies are re-run on the new common window.
- **Romano-Wolf stepwise** ([Romano-Wolf 2005 Econometrica](https://doi.org/10.1111/j.1468-0262.2005.00615.x)): step-down resampling method controlling FWER; more amenable to heterogeneous evaluation windows when paired with a block bootstrap accounting for serial dependence, though still assumes a comparable test statistic per hypothesis.

Audit item #7 in [audit-round1-quant_2026-04-15.md](../../research/03_audits/audit-round1-quant_2026-04-15.md) flagged this as a HIGH concern.

## Options

### A. Re-run all historical strategies on a common OOS on every universe append

Pros:
- Preserves SPA null-construction assumptions exactly.
- Universe-level p-value is statistically well-defined.

Cons:
- O(N) recompute cost at every append; scales poorly beyond 50 strategies.
- Requires snapshot-frozen code, data, and labels for every historical strategy (reproducibility load).
- Sensitive to OOS definition drift as new data accrue.

### B. Romano-Wolf stepwise as primary; SPA as diagnostic

Pros:
- Handles heterogeneous OOS more gracefully via studentized bootstrap on per-strategy statistics.
- Step-down structure gives per-hypothesis adjusted p-values, not just a universe-max statistic.
- Lower operational cost: no mandatory re-run on append.

Cons:
- FWER control under dependence between strategies relies on the block bootstrap choice (Politis-White 2004 optimal block length on the stacked residual matrix).
- Less established in the trading-strategy literature than SPA; harder to reference without caveat.

### C. Both, with explicit rules

Compute both `hansen_spa_pvalue` and `romano_wolf_pvalue` (already in `GateReport`). `passed` requires either to be below alpha, with BH q-value < 0.10 as the FDR backstop. Select Option A or Option B as *primary* based on:
- Size of snapshot at time of evaluation (A preferred for small N, B for large N).
- Heterogeneity of OOS windows (B preferred when >20% of candidates have non-overlapping OOS).

## Decision (proposed)

Adopt **Option C**: both tests computed always; Romano-Wolf as the *operational primary* once the universe exceeds ~20 strategies or heterogeneous-OOS share exceeds 20%. Below those thresholds, SPA remains primary and Option A (re-run on common OOS) is executed weekly via CI.

Final thresholds determined empirically in Phase 1 after the first 10 gate evaluations (bootstrap power comparison on synthetic alternatives).

## Consequences

- `GateReport.passed` logic ([§5](../../plan/buildouts/implementation-plan_2026-04-15.md)) already accepts `hansen_spa_pvalue < alpha OR romano_wolf_pvalue < alpha`; this ADR's acceptance only fixes which is "primary" for reporting.
- CI job `gate-snapshot` (§9.2) extended to trigger full re-run on common OOS when Option A is in force.
- BH q-value ([Benjamini-Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)) and Storey q-value ([Storey 2002](https://doi.org/10.1111/1467-9868.00346)) provide FDR backstop independent of A/B choice.

## References

- [Hansen 2005](https://doi.org/10.1198/073500105000000063)
- [White 2000](https://doi.org/10.1111/1468-0262.00152)
- [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x)
- [Benjamini-Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
- [Storey 2002](https://doi.org/10.1111/1467-9868.00346)
- [Politis-White 2004](https://doi.org/10.1081/ETC-120028836)
- [Harvey-Liu-Zhu 2016](https://doi.org/10.1093/rfs/hhv059)
