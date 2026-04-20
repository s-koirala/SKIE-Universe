---
name: Remediation round 1 — quant-auditor findings
description: Edits applied to plan/implementation-plan_2026-04-15.md in response to audit-round1-quant_2026-04-15.md
type: project
status: applied
date: 2026-04-15
round: 1
remediation-of: research/03_audits/audit-round1-quant_2026-04-15.md
---

# Remediation Round 1 — Quant-Auditor Findings

All three CRITICAL and all HIGH findings have been addressed in [plan/implementation-plan_2026-04-15.md](../../plan/implementation-plan_2026-04-15.md). MEDIUM items recorded as tracked open items; LOW items partially absorbed (ADR-0002 message count, leaked-feature canary, Harvey-Liu-Zhu haircut) and the remainder deferred.

## Changes applied

### CRITICAL

| # | Audit finding | Action in plan | Section |
|---|---|---|---|
| C-1 | FDR + Romano-Wolf missing | Added `romano_wolf_pvalue`, `bh_qvalue`, `storey_qvalue` to `GateReport`. Added Benjamini-Hochberg 1995, Storey 2002, Romano-Wolf 2005 citations. Rewrote `passed` logic: CI excludes 0 AND (SPA p<α OR Romano-Wolf p<α) AND BH q<0.10. | §5 |
| C-2 | Power analysis absent | New §5.1 "Pre-registration power calc" requires `power` block in each hypothesis `config.yaml`, AR(1) inflation `(1+2ρ/(1-ρ))` applied, Lo 2002 HAC-adjusted Sharpe variance formula. Gate rejects underpowered designs. | §5.1 |
| C-3 | Deflated Sharpe absent | Added `deflated_sharpe_ratio` and `psr_pvalue` fields with Bailey-Lopez de Prado 2014 citation. Required `passed` criterion when `universe_snapshot_size > 10`. | §5 |

### HIGH

| # | Audit finding | Action in plan | Section |
|---|---|---|---|
| H-4 | Embargo 1% / purge = label-horizon are arbitrary | Replaced with data-driven PACF-based embargo selection cross-checked against Politis-White 2004 optimal block length; purge restated as strict lower bound `purge >= max_label_horizon`. Both values logged to `ReproLog`. CPCV `n_groups` / `n_test_groups` parameterized. | §4.1 |
| H-5 | Cost-model 60/40 single split | Replaced with expanding-window walk-forward refit per calendar week; PIT calibration + pinball aggregated across folds. | §6.3 |
| H-6 | Pipeline-level leakage not closed | New §4.6 "Pipeline-level leakage test" — injects a feature whose mean depends on future data via scaler/encoder fit on full panel; asserts `LeakageDetected` before fit. Also new §4.5 "Leaked-feature canary" — future-return leaked feature must fail PIT + gate. | §4.5, §4.6 |
| H-7 | SPA common-OOS violation on append | New [ADR-0003](../../docs/decisions/ADR-0003-spa-vs-romanowolf.md) status=proposed documents Option A (re-run historical on common OOS) vs Option B (Romano-Wolf primary); Option C hybrid proposed, decision deferred to Phase 1. | ADR-0003 |
| H-8 | Lo 2002 inappropriate for intraday | Opdyke 2007 elevated to primary; studentized circular-block bootstrap added as tie-breaker; Lo 2002 retained as diagnostic-only and excluded from `passed` logic. Justification block references ρ₁∈[-0.08,-0.03] and heavy tails. | §5 |
| H-9 | √-impact misspecified at retail | Primary mean rewritten as linear-in-spread + latency-conditional: `a + b*spread_ticks + c*latency_ms + d*vol_realized_1m`. √(qty/ADV) retained only as regularized Bayesian prior with CV-selected σ²_prior. Tóth 2011 cited for misspecification context at `qty/ADV ≈ 1.3e-5`. | §6.2 |

### MEDIUM (tracked, not implemented)

New subsection "Open items for Phase 1" at the end of the plan lists audit items M-10 through M-16 (`GateReport` MaxDD/Ulcer/turnover/Calmar additions; magic-number empirical justification; `bootstrap_reps` MC-SE rationale; CPCV parameterization rationale capture; triple-barrier pre-registration; CME fee-tier documentation; MBP-10 depth schema).

### LOW items absorbed opportunistically

- L-19: Leaked-feature canary — implemented in §4.5.
- L-21: Harvey-Liu-Zhu 2016 haircut framework — required for final Sharpe reporting, added to §5.
- L-22: ADR-0002 latency study pushed to ≥10k messages per option — §1 P0-10 updated.

Remaining LOW items (L-17 Opdyke DOI cross-check, L-18 `StrategyUniverse` signed-hash / write-once ACL, L-20 SPA null-uniformity test with n≥10k or Anderson-Darling) are deferred.

## Sections edited, by line region (post-edit)

- §4.4–§4.6 (Training-harness acceptance + two new canaries).
- §4.1 (Splitter spec: data-driven embargo + purge bound + CPCV parameterization).
- §5 (`GateReport` dataclass, `passed` logic, Harvey-Liu-Zhu reporting, primary-CI justification).
- §5.1 (new: pre-registration power calc).
- §6.2 (slippage mean reformulated; √ prior demoted to regularized Bayesian).
- §6.3 (expanding-window walk-forward).
- §1 P0-10 (ADR-0002 ≥10k messages).
- Reference anchors list extended with BH, Storey, Romano-Wolf, Bailey-Lopez de Prado, Harvey-Liu-Zhu, ADR-0003.
- New section "Open items for Phase 1".

## New files

- [docs/decisions/ADR-0003-spa-vs-romanowolf.md](../../docs/decisions/ADR-0003-spa-vs-romanowolf.md) — status `proposed`.

## Still open

- ADR-0003 acceptance pending Phase-1 empirical comparison (first 10 gate evaluations).
- MEDIUM items 10–16 tracked but not implemented in this plan revision.
- LOW items L-17, L-18, L-20 deferred.

## Evidence / citations added

- [Benjamini-Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
- [Storey 2002](https://doi.org/10.1111/1467-9868.00346)
- [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x)
- [Bailey-Lopez de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094)
- [Harvey-Liu-Zhu 2016](https://doi.org/10.1093/rfs/hhv059)
- [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453) (retained, demoted to diagnostic + cited for power formula)
- [Tóth et al. 2011](https://arxiv.org/abs/1104.1694) (context for √-impact misspecification)
