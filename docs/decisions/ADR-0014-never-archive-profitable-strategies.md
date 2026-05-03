---
adr_number: ADR-0014
title: Never archive profitable strategies; disposition_class is a state, not an archive decision
status: Accepted
date: 2026-05-03
amends: ADR-0012 disposition-philosophy-aspirational-mvp
audit_trail: docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md (continued)
trigger: User directive 2026-05-03 ("make a note not to archive profitable strategies; we are here to innovate and to explore; we need to lower our threshold; we need to be slower on the archiving; we need to ensure future claude instances do not make the same mistake")
---

# ADR-0014 — Never archive profitable strategies; disposition_class is a state, not an archive decision

## Context

The H053 Stage-3 v3 binding disposition emitted `calibration-failed` on all 4 arms (per ADR-0012 §10.1 strict precedence + design.md §8.a binding gates). Downstream of that emission, this Claude instance authored a calibration-recovery diagnostic that recommended **"archive H053 fully under archive(calibration-failed)"** despite the operational performance being:

- **ES Arm 2 LightGBM**: +7.28% annualized return, Sharpe 1.49, Sortino 2.53, Calmar 1.48, max DD 4.9%, win rate 53.7%, profit factor 1.29 (gross); +2.90% annualized return / Sharpe 0.59 (net of 1-tick cost).
- **NQ Arm 2 LightGBM**: +6.71% annualized return, Sharpe 0.99, Sortino 1.57, Calmar 1.32, max DD 5.1%, win rate 51.6%, profit factor 1.18 (gross); +4.78% annualized return / Sharpe 0.70 (net).

Both strategies are profitable gross + net of cost. Treating "calibration-failed" as a license to archive a profitable strategy is wrong on three independent grounds:

1. **Policy**: ADR-0012 only defines `archive(complete; KPI report)` as an "archive" disposition. The other four disposition_class values (leakage-detected, reproducibility-incomplete, calibration-failed, prerequisite-not-met) are **states** indicating what's blocking promotion — they are NOT archive decisions. The label `archive(calibration-failed)` does not exist in ADR-0012; it was invented by the downstream interpretation.

2. **Philosophy**: CLAUDE.md §"Research philosophy" frames the project as longitudinal exhaustive exploration with the goal of bringing strategies to MVP "as fast as is consistent with methodological correctness". Archiving profitable strategies on a single methodological-gate failure trades exploration breadth for premature closure.

3. **User intent**: explicitly recorded 2026-05-03: "we are here to innovate and to explore; we need to lower our threshold; we need to be slower on the archiving."

## Decision

This ADR codifies four binding amendments to ADR-0012:

### 1. Vocabulary correction (binding clarification, not amendment)

The disposition_class values are **states**, not archive decisions. The ONLY archive labels are:
- `archive(complete; KPI report)` — passes Class A; paper-trade-eligible (per ADR-0012)
- `archive(null, <reason>)` — genuine signal absence with full evidence (per design.md §10.1)

The four other disposition_class values (`leakage-detected`, `reproducibility-incomplete`, `calibration-failed`, `prerequisite-not-met`) are remediation-pending states. **Future writing MUST NOT use "archive(<state>)" notation for non-archive states.** Use "<state>; remediation pending" or "<state>; under investigation."

### 2. Profitable-strategy override (NEVER ARCHIVE)

A strategy with **positive raw Sharpe at α=0.10 confidence on the OOS fold** SHALL NOT be archived under any disposition_class regardless of Class A gate failures. Definition:
- "Positive raw Sharpe at α=0.10": annualized Sharpe point estimate > 0 AND Lo 2002 / Opdyke 2007 lower CI bound > -0.5 (one-sided 90% confidence; not requiring exclusion of zero, which is too stringent for early-stage research).
- "Profitable": annualized return > 0% AND Sortino > 0 AND profit factor > 1.0.

A strategy meeting EITHER definition enters the **active-investigation** state instead of any archive state. The disposition_class still reports the binding gate failure (e.g., calibration-failed), but the operator-visible disposition is "active-investigation pending remediation of <gate>". Paper-trade promotion may proceed at operator discretion subject to a written gate-bypass justification recorded in the promotion log.

### 3. Disposition framework code change (mechanism enforcement)

`src/skie_ninja/inference/disposition.py` `compose_disposition` SHALL emit a new `lifecycle_state` field with three values:
- `archived` — only for `archive(complete)` and `archive(null, <reason>)` after explicit operator decision
- `active-investigation` — Class A gate(s) failed BUT raw Sharpe positive per §2 above
- `paper-trade-eligible` — all Class A gates pass

`paper_trade_eligible` boolean flag stays as-is (auto-eligibility under Class A pass + Sharpe-vs-passive + SPA + max-DD), but the new `lifecycle_state` field surfaces the never-archive-profitable invariant separately. The disposition class label remains for technical/audit purposes.

### 4. Operator-visible promotion path

When `lifecycle_state == "active-investigation"`, the promotion log SHALL include:
- The blocking Class A gate(s)
- Raw Sharpe + Sortino + max DD + profit factor (operator-decision inputs)
- Explicit prompt: "Operator may promote despite gate failure; record gate-bypass justification below."
- Suggested remediation steps for the blocking gate (deferred to operator)

## Future-Claude-instance binding guidance (NEVER violate)

**The following directives are binding on every Claude instance working on this project, in perpetuity until ADR-0014 is superseded by a successor ADR:**

1. **NEVER use the phrase "archive(<state>)" for non-archive states.** The state is `calibration-failed` or `leakage-detected` or similar — not "archive(calibration-failed)". Writing the latter conflates a remediable state with a closure decision.

2. **NEVER recommend archiving a profitable strategy.** If the strategy has positive raw Sharpe + positive return + profit factor > 1, it stays in active-investigation regardless of Class A gate status. Calibration / SPA / DSR failures are remediation tasks, not closure triggers.

3. **NEVER conflate `paper_trade_eligible = False` with "archived"**. The first means "auto-promotion blocked by gate; operator review required"; the second means "hypothesis closed; do not pursue further." Distinct decisions.

4. **DEFAULT to active-investigation, NOT to archive.** When in doubt about whether a strategy is "done", choose active-investigation. CLAUDE.md research philosophy is exhaustive longitudinal exploration; archive is the rare disposition reserved for genuine null evidence (clean methodology + clear signal absence) AND non-recoverable structural blockers.

5. **When emitting the disposition_class label**, include the lifecycle_state distinct from it. Disposition class is a technical-audit field; lifecycle_state is the operator-visible "is this hypothesis still alive?" answer.

6. **When you find yourself writing "archive H053 fully" or equivalent without explicit user direction**, stop. Either:
   - Re-read this ADR + ADR-0012 + CLAUDE.md §"Research philosophy" before proceeding, OR
   - Surface the question to the user with the operational performance numbers attached.

7. **The threshold for "profitable" is intentionally lower than statistical significance.** Annualized return > 0% + Sortino > 0 + profit factor > 1.0 is the floor. Strategies that pass this floor are kept alive even if their Sharpe-vs-passive paired CI does not exclude zero.

## Consequences

**Positive:**
- The H053 ES Arm 2 LightGBM strategy (annualized Sharpe 1.49, +7.3% return, 4.9% max DD) remains in active investigation rather than premature closure.
- Future Claude instances have a binding rule preventing the same conceptual error.
- The disposition framework's lifecycle_state field surfaces the "is it alive?" question separately from the technical disposition_class.
- Innovation budget is preserved: profitable strategies keep accumulating evidence rather than being shelved on first methodological hiccup.

**Negative:**
- More hypotheses stay in active-investigation, requiring more operator review. Operationally manageable because the operator review is exactly what should happen for profitable-but-uncalibrated strategies.
- The paper_trade_eligible auto-flag may become less informative if many strategies qualify for active-investigation without auto-promotion. Mitigated by the explicit operator-decision prompt in the promotion log.

**Open:**
- The "α=0.10 confidence" threshold for "positive raw Sharpe" is a project convention; could be tightened or loosened. Default chosen because Lo 2002 §III HAC-Sharpe SE is wide at small n_oos, and α=0.05 (the Class B KPI default) is too stringent for early-stage research.
- Successor hypothesis IDs for amended-calibrator paths remain available per ADR-0012 §"Frozen pre-registration amendment" carve-out; this ADR does not change that procedure.

## H053 immediate consequences

The H053 v3 disposition stands as `calibration-failed` (technical disposition class), but the lifecycle_state is now `active-investigation` per §2 above. The "archive H053 fully" recommendation in the calibration diagnostic note is REVERSED. ES Arm 2 LightGBM and NQ Arm 2 LightGBM are eligible for operator promotion to paper-trade subject to gate-bypass justification.

The 5 remediation paths remain on the table:
1. **Promote to paper-trade despite calibration-failed** (operator gate-bypass with written justification per §4 above)
2. **Successor hypothesis with beta-as-binding calibrator** (per ADR-0012 §"Frozen pre-registration amendment" §1-§7 carve-out)
3. **Investigate Hansen SPA p-value** (ES p=0.12 may tighten with more OOS data as 2026 sessions accrue)
4. **Re-run with longer OOS window** as 2026 data becomes available (would tighten Sharpe CI)
5. **Drop the categorical-table user-facing deliverable** (the calibration-binding requirement comes from H053 design.md §8.a's bss_applicable=yes flag, which is set because the K×3 archetype-bias-target probability table is the user-facing product; if that table is dropped, calibration becomes Class B not Class A)

## Alternatives considered

1. **Keep the ADR-0012 strict precedence as-is.** Rejected — the user directive + the conceptual analysis above are decisive. The strict precedence works for design-time gate evaluation but the disposition framework needs a parallel lifecycle_state field for operator-visibility.
2. **Make calibration a Class B KPI globally** (instead of Class A binding). Rejected — calibration matters for hypotheses whose user-facing product is a probability table (H053's K×3 table). The fix is per-hypothesis applicability + lifecycle_state, not global downgrade.
3. **Require statistical significance for "profitable"** (e.g., Sharpe-vs-passive CI excludes zero at α=0.05). Rejected — too stringent for early-stage research; would archive too many hypotheses on n_oos ≈ 250-400 sample sizes.
4. **Allow "archive(calibration-failed)" as a valid label.** Rejected — it conflates state with archive decision; the linguistic precision matters for future Claude instance interpretation.

## References

- [ADR-0012 disposition-philosophy-aspirational-mvp](ADR-0012-disposition-philosophy-aspirational-mvp.md) (this ADR amends §10.1 disposition-class semantics + adds lifecycle_state)
- [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md) §8.a binding gates
- [docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md](../audits/audit_trail_2026-05-03_h053-stage3-v3.md) — H053 v3 audit trail
- [reports/h053/stage3_v3_full_disposition.md](../../reports/h053/stage3_v3_full_disposition.md) — H053 v3 disposition memo (to be updated per §H053 immediate consequences above)
- [docs/research_notes/note_h053-v3-es-arm2-calibration-diagnostic_2026-05-03.md](../research_notes/note_h053-v3-es-arm2-calibration-diagnostic_2026-05-03.md) — diagnostic that originally recommended archive (now REVERSED)
- [runs/h053/diagnostics/arm2_performance_2026-05-03.json](../../runs/h053/diagnostics/arm2_performance_2026-05-03.json) — performance dashboard data
- CLAUDE.md §"Research philosophy" + §"Aspirational-MVP framing"
- User directive 2026-05-03 (verbatim): "make a note not to archive profitable strategies; remember we are here to innovate and to explore. we need to lower our threshhold. we need to be slower on the archiving. we need to ensure future claude instances do not make the same mistake"
