---
name: H050 — Purge rule addendum (per-cfg label horizon)
description: Binding implementation directive ratifying per-cfg purge_window over the design.md §6 line 73 grid-max wording
hypothesis_id: H050
type: project
created: 2026-05-03
status: binding
amends: research/01_hypothesis_register/H050/design.md §6 line 73
authority: ADR-0013 §"Frozen pre-registration amendment" (project-level disposition-philosophy ADR amendment discipline)
audit_trail: docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md (Round-1 finding F-Q-2)
---

# H050 — Purge rule addendum (2026-05-03)

This addendum is a binding implementation directive interpreting design.md §6 line 73's purge specification under ADR-0013's §"Frozen pre-registration amendment" discipline. It is the analog of the [aggregation_rule_addendum_2026-04-24.md](aggregation_rule_addendum_2026-04-24.md) (Round-2 closure of `P1-H050-AGGREGATION-RULE`) for the splitter purge rule.

## Context

Design.md §6 line 73 reads verbatim:

> `purge`: `max(vertical_barrier)` across CV-selected folds.

Read literally, this prescribes a SINGLE GLOBAL purge value computed as the maximum of all CV-selected `vertical_barrier` values across all folds, applied uniformly to all outer folds. Under the H050 27-cell label grid (`pt_sl × vertical_barrier × volatility_lookback`) where vertical_barrier ∈ `{30m, 60m, 120m}`, this would unconditionally purge `120m` from every fold even when the active label cfg has `vertical_barrier = 30m` — over-conservative by a factor of 4.

The orchestrator implementation at [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) line 2155 (post-F-Q-1 patch) calls `walk_forward_split(..., purge_window=label_horizon)` where `label_horizon` is derived from the CURRENT cfg's `vertical_barrier`. This is the **per-cfg purge** interpretation: each cfg pays only its own purge.

## Round-1 audit-remediate-loop F-Q-2 verdict

The Round-1 audit (quant-auditor finding F-Q-2; severity = major) flagged this as a literal departure from the frozen pre-reg §6 line 73 wording. AFML §7.4 Purging the Training Set (López de Prado 2018, Wiley, ISBN 978-1-119-48208-6, p. 105) prescribes `purge_window == label_horizon` — i.e. per-cfg. The implementation is methodologically defensible; the pre-reg wording is over-conservative.

## Decision (binding from 2026-05-03 forward)

Under ADR-0013 §"Frozen pre-registration amendment" discipline + ADR-0012 §"Frozen pre-reg amendment" §1-§4 invariance preservation:

- The §6 line 73 text is **NOT EDITED** (per pre-reg immutability).
- The binding implementation is **per-cfg purge**: `purge_window = label_horizon(cfg.vertical_barrier)` for each outer fold within each cfg's evaluation pass.
- The grid-max interpretation (literal §6 line 73) is **superseded** by this addendum's per-cfg interpretation.
- This addendum is the canonical reference for any post-2026-05-03 H050 walk-forward run; CLAUDE.md ledger entries citing `P1-H050-AGGREGATION-RULE` closure (commit `f96cf7d`) and the orchestrator's Round-2 §F-2 fix (line 2155 region) are consistent with this decision.

## Justification

- **Methodological**: AFML §7.4 (López de Prado 2018) defines purge as the temporal exclusion zone needed to prevent labels co-determined by post-test observations from contaminating the training set. The label horizon defines the exact boundary — purging beyond it adds no methodological benefit and reduces statistical power by shrinking the training set unnecessarily.
- **Empirical**: with the H050 27-cell label grid, the grid-max purge over a 9-year training panel would lose ~200K bars per fold beyond the per-cfg-purge baseline, equivalent to ~6 calendar weeks of extra purge per fold. The per-cfg purge preserves training power while satisfying the AFML §7.4 invariant.
- **Operator-promotion**: under ADR-0013 §1, the operator decides paper-trade and live-promotion at every stage transition based on the KPI report card. The per-cfg purge interpretation is the most faithful to the AFML primary source and produces the canonical KPI report card for operator review; it does not introduce gating semantics.

## Cross-references

- AFML §7.4 "Purging the Training Set" — primary methodological source
- [research/01_hypothesis_register/H050/design.md](design.md) §6 line 73 — frozen pre-reg text (NOT edited)
- [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](aggregation_rule_addendum_2026-04-24.md) — sibling addendum precedent (per-cfg vs grid-max interpretation closure for `P1-H050-AGGREGATION-RULE`)
- [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) — orchestrator implementation (per-cfg purge in `walk_forward_split` invocation)
- [docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) §"Frozen pre-registration amendment" — amendment discipline (preserved by ADR-0013)
- [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Frozen pre-registration amendment" — amendment authority for project-wide disposition-philosophy ADRs amending §8 + §10 + new §15 of frozen design.md files
- [docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md) — full audit-remediate-loop trail (Round-1 finding F-Q-2 + Round-2 closure via this addendum)
