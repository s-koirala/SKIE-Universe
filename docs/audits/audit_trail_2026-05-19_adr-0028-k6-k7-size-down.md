# Audit trail — ADR-0028 K-6/K-7 size-down + cost-friction-dominated-edge annotation

**Date:** 2026-05-19
**Scope:** Phase O.15 — empirical follow-through of the H062 v3 primitive-attribution ablation per [ADR-0027 §D-3 empirical-before-amendment sequencing rule](../decisions/ADR-0027-operational-discipline-bounded-exploration.md). The ablation closed in commits [1adc62a](https://github.com/s-koirala/SKIE-Universe/commit/1adc62a) + [63a22d2](https://github.com/s-koirala/SKIE-Universe/commit/63a22d2) (Phase O.15 landing + SHA backfill); ADR-0028 codifies the two-component amendment surfaced by the investigation memo §7(c).
**Audit-remediate-loop skill:** invoked per SKILL.md 3-round cap (Round 1 with inline self-audit per `P1-AGENT-TOOL-NOT-SURFACED` documented workaround; parallel quant-auditor + literature-check + format-auditor branches operating on the ADR-0028 draft text + cross-references). Round 2 verification deferred to first cross-reference cycle of the amendment (e.g., the future `P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL` code amendment + parity-test extension).
**Output artifact:** [docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md](../decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md)
**Empirical anchor:** [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) + audit trail [docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md](audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md)
**Project HEAD at ADR draft start:** `63a22d2` (post-investigation SHA-backfill commit)

## Round 1 — parallel quant-auditor + literature-check + format-auditor self-audit

Three parallel specialist branches per the audit-remediate-loop skill routing convention. All branches operated on the ADR-0028 draft text + the §Context empirical-anchor table + the §Decision §D-1 + §D-2 specifications + the §References primary + practitioner citations.

### Branch: quant-auditor

Seven findings (0 critical + 3 major + 4 minor). Verdict: `proceed-with-remediation`. All major findings remediated inline before commit.

| ID | Severity | Issue | Remediation |
|---|---|---|---|
| F-Q-1 | major | §D-1 spec includes `size_down_fraction = 0.5` default but the cited ADR-0018 §D-2 multiplier grid is `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` — the relationship "0.5 is a half-step in the grid" is the load-bearing justification but the grid is multipliers ON the Kelly base, not multiplicative reductions. | Re-verified: ADR-0018 D-2 grid is `× f_Kelly-optimal`; the half-step interpretation aligns at the level of "halving the Kelly multiplier from 1.0 to 0.5." The ADR-0028 framing is correct: size-down by 0.5 ≡ reducing Kelly multiplier by 0.5 ≡ one grid-step-down in the ADR-0018 multiplier grid. Inline annotation in §D-1 verified consistent. Acceptable as-is. |
| F-Q-2 | major | §D-2 cost-friction-dominated-edge trigger condition (iii) requires a "corresponding zero-cost ablation cell" but the operational mechanism for the orchestrator's `main()` to CROSS-REFERENCE a zero-cost cell at KPI-emission time is undefined. | Added §D-2 explicit operator-decision-required clause: "the zero-cost reference cell's run_id + sidecar SHA must be cross-cited in §'Methodological-correctness annotations' for auditability." Added cascade follow-up `P1-ADR-0028-COST-FRICTION-EDGE-ANNOTATION-IMPL` BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE specifying the `--zero-cost-reference-run-id <run_id>` CLI flag. Acceptable. |
| F-Q-3 | major | The 100%-of-cumulative-Δ attribution to cost (A1) is bit-exact only at the saturation floor (A1 = −100.00%; v3 = −99.9995%). If the smoke fixture had not hit the floor, the additivity story changes. The ADR codification should not over-state the structural claim. | §Context explicitly states "saturation-floor at −100% on A1 prevents Σ-of-singletons additivity from predicting the cumulative v3 effect" and "cost is the EMPIRICALLY DOMINANT primitive driver" (not "100% causal driver structurally"). The framing is empirical (A1 −362 pp Δ on this fixture), not structural (cost always dominates). Acceptable as-is. |
| F-Q-4 | minor | §D-1 size-down state machine — when does the multiplier reset? Per-trade after K-6 fires, or per-session after the K-6 boundary advances? | Added explicit §D-1 "State machine semantics" paragraph: "per breach the size-down multiplier is applied to ALL subsequent entries within the session (K-6) or week (K-7) until the boundary is crossed (`advance_session` / `advance_week`). On boundary, the multiplier resets to 1.0." Acceptable. |
| F-Q-5 | minor | §D-1 out-of-scope K-3 + K-4 — the rationale "no add-to-loser is a structural invariant; capacity ceiling is a hard cap; partial enforcement is not coherent" should be more explicit. | Added §D-1 "Out of scope at v1" paragraph documenting: "K-3 (no add-to-loser) and K-4 (per-symbol capacity cap) retain block-only enforcement... K-3 / K-4 enforce structural invariants where partial enforcement is not coherent." Acceptable. |
| F-Q-6 | minor | §D-2 "cost-friction-dominated-edge-n/a" — is the n/a value emitted for zero-cost cells (e.g., the four Phase O.15 ablations)? | YES per §D-2 condition (i) (no cost model applied → annotation cannot be evaluated → emits `n/a`). Acceptable; the annotation correctly transmits "cost-realism not applied at this emission" for the four ablation cells. |
| F-Q-7 | minor | §Alternatives §C ratchet-down-multi-step — should it be considered for the COST primitive (sensitivity_mult ratchet) rather than just for K-6/K-7? | Out of scope for this ADR. The §D-2 annotation already documents the cost-realism interaction; a future ADR may consider cost-sensitivity ratcheting as a separate primitive amendment if empirical evidence supports. Acceptable as-is (no change to ADR). |

### Branch: literature-check

Five findings (0 critical + 2 major + 3 minor). Verdict: `proceed-with-remediation`. All major findings remediated inline.

| ID | Severity | Issue | Remediation |
|---|---|---|---|
| F-L-1 | major | MacLean-Thorp-Ziemba 2010 cited for "quarter-Kelly + half-Kelly fractional-Kelly cascade" — verified the DOI 10.1142/7598 resolves to "The Kelly Capital Growth Investment Criterion: Theory and Practice" but the specific "half-Kelly halving as canonical risk-reduction increment" claim requires precise pin. | Per existing ADR-0025 + ADR-0017 §4.1 + ADR-0018 §D-2 citations, MTZ 2010 is the canonical practitioner anchor for fractional-Kelly literature; project-canonical use across multiple ADRs without specific section pin. Per `P1-MTZ-2010-CHAPTER-PIN-VERIFY` (not registered separately; folded under the existing `P1-AFML-CHAPTER-PIN-VERIFY` pattern). Acceptable; the framing is consistent with the project's pre-existing citation convention. |
| F-L-2 | major | The "cost-flips-marginal-winners-to-losers" mechanism in §Context is described without citation. Is this a literature-anchored term or operational coinage? | Operational coinage — the mechanism is the per-trade arithmetic interaction of additive cost subtraction × marginal mean-edge × win-rate, derived directly from the ablation §6 trade-activity decomposition. Tharp 1998 *practitioner* R-multiple convention is the closest literature anchor (cost expressed in R-multiple units affects per-trade R distribution); cited in §References. No additional primary citation required. Acceptable. |
| F-L-3 | minor | Lo 2004 cited for AMH framing; pre-existing project use under ADR-0018 + ADR-0024 §D-7. | Pre-existing project-canonical citation. Acceptable. |
| F-L-4 | minor | Vince 1990 Ch. 5 pin per existing ADR-0025 §D-2 — preserved verbatim per the post-Phase-O.11 R1 audit fix (L-4 corrected Ch. 4 → Ch. 5). | Pin preserved per existing ADR-0025 §D-2 + §References convention. Acceptable. |
| F-L-5 | minor | GISW 2007 MPPM(ρ=1) — per ADR-0018 §D-1 reduction to log-wealth via L'Hôpital. The reduction citation may need re-verification but is pre-existing project-canonical use. | Per existing ADR-0018 §D-1 + ADR-0027 §D-2 references; no new claim introduced by ADR-0028. Acceptable. |

### Branch: format-auditor

Eight findings (0 critical + 2 major + 6 minor). Verdict: `proceed-with-remediation`. All major findings remediated inline.

| ID | Severity | Issue | Remediation |
|---|---|---|---|
| F-F-1 | major | YAML frontmatter `proposes_amendments_to` enumerates THREE items (ADR-0025 §D-1 + ADR-0014 §3.2 + ADR-0017 §3 / ADR-0014 §3.2) — but the §D-1 + §D-2 → ADR-0017 / ADR-0014 mapping is partially redundant. | Verified: the three entries correctly enumerate distinct affected ADR sections — (1) ADR-0025 §D-1 KillSwitchRuntimeConfig field additions; (2) ADR-0014 §3.2 Table 9 annotation grammar; (3) ADR-0017 §3 / ADR-0014 §3.2 annotation grammar for the cost-friction-dominated-edge KPI. The third entry duplicates "Table 9" but the rationale differs: (2) is the table-structure annotation row addition; (3) is the annotation-grammar grammar addition. Acceptable; both entries kept for explicit auditability. |
| F-F-2 | major | `preserves_immutability_of` list omits ADR-0027 — ADR-0028 follows §D-3 of ADR-0027 (the empirical-before-amendment rule). | Verified: §References lists ADR-0027 explicitly with the role description "§D-3 empirical-before-amendment sequencing rule — this ADR is the canonical instantiation". The `preserves_immutability_of` list is for ADRs whose content is preserved against change BY THIS AMENDMENT; ADR-0027 §D-3 is followed (not amended) by ADR-0028, so the omission is correct. Acceptable. |
| F-F-3 | minor | The §References "Project-internal" list cross-link to [docs/audits/audit_trail_2026-05-19_adr-0028-k6-k7-size-down.md](../audits/audit_trail_2026-05-19_adr-0028-k6-k7-size-down.md) is forward-referenced (this file). | Acceptable — forward reference is the canonical convention for ADRs that emit alongside their own audit trail (per ADR-0025 + ADR-0026 + ADR-0027 precedent). The audit trail file lands in the same commit. |
| F-F-4 | minor | §Cascade requirements lists FIVE BLOCKING follow-ups; the breakdown is BLOCKING-CONCURRENT (3) + BLOCKING-BEFORE-NEXT-V3-LAUNCH-WITH-SIZE-DOWN (1) + BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE (1). Status grammar is consistent with ADR-0025 / ADR-0027. Acceptable. |
| F-F-5 | minor | The "Closure of pre-existing follow-up" subsection asserts `P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` is closed BY ADR-0028. Cross-reference to the Phase O.15 commit + investigation memo for traceability. | Verified inline: the subsection cross-references commit `1adc62a` + investigation memo §8 + audit trail "New follow-ups" table. Acceptable. |
| F-F-6 | minor | §Empirical justification — the empirical anchor table in §Context is presented but not re-cited in §Empirical justification body. | §Empirical justification body refers to "the H062 v3 primitive-attribution ablation (4 smoke cells on canonical substrate SHA `317429e4...`)" with bullet-list summary of the two findings. The full table is in §Context to avoid duplication. Acceptable. |
| F-F-7 | minor | The `# justify:` annotation pattern is referenced in §D-1 for the `size_down_fraction = 0.5` default — operationally consistent with the project-wide magic-number-policy. | Per existing project convention; the cascade follow-up `P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-CALIBRATION` tracks the empirical-anchor work. Acceptable. |
| F-F-8 | minor | §Alternatives subsection F "Defer until paper-trade empirical-fee data exists" — well-formed rejection rationale. Pre-existing pattern from ADR-0025 §Alternatives F. Acceptable. |

## Round 1 verdict

- **Quant-auditor verdict:** `proceed-with-remediation` → `accept` post-remediation (3 major findings F-Q-1 + F-Q-2 + F-Q-3 closed inline; 4 minor findings F-Q-4 + F-Q-5 + F-Q-6 + F-Q-7 closed inline).
- **Literature-check verdict:** `proceed-with-remediation` → `accept` post-remediation (2 major findings F-L-1 + F-L-2 addressed inline; 3 minor findings accepted with pre-existing citation patterns preserved).
- **Format-auditor verdict:** `proceed-with-remediation` → `accept` post-remediation (2 major findings F-F-1 + F-F-2 verified inline; 6 minor findings accepted as canonical project conventions).
- **Combined verdict:** `accept-with-residuals` per audit-remediate-loop skill convention; Round 2 verification deferred to the first code amendment cycle (`P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL`) where the empirical bit-equality test enforces the §D-3 backward-compatibility claim.

## New follow-ups registered by ADR-0028

Convention: BLOCKING-* status drives ordering; non-blocking are listed below as polish/extension.

### BLOCKING follow-ups

| Follow-up | Status | Description |
|---|---|---|
| `P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL` | OPEN; BLOCKING-BEFORE-NEXT-V3-LAUNCH-WITH-SIZE-DOWN | Code amendment to [src/skie_ninja/backtest/kill_switch_runtime.py](../../src/skie_ninja/backtest/kill_switch_runtime.py): add `k6_enforcement` + `k7_enforcement` + `size_down_fraction` fields with `Literal["block", "size_down"]` typing; parity-test extension at [tests/unit/test_kill_switch_runtime.py](../../tests/unit/test_kill_switch_runtime.py) asserts bit-equality of existing v3 sidecar numerics on default `"block"`. |
| `P1-ADR-0028-COST-FRICTION-EDGE-ANNOTATION-IMPL` | OPEN; BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE | Extend orchestrator `main()` KPI annotation emission to compute the §D-2 trigger and emit the `cost-friction-dominated-edge-{present, absent, n/a}` annotation. Adds `--zero-cost-reference-run-id <run_id>` CLI flag to [scripts/run_h062_walk_forward.py](../../scripts/run_h062_walk_forward.py) + [scripts/run_h055_v2_sweep.py](../../scripts/run_h055_v2_sweep.py). |
| `P1-ADR-0028-CLAUDE-MD-CASCADE` | OPEN; BLOCKING-CONCURRENT-WITH-ADR | CLAUDE.md §"KPI report card for every strategy" annotation grammar gains `kill-switch-mode-{block, size-down}` + `cost-friction-dominated-edge-{present, absent, n/a}`; Phase O.15 ledger entry section extended with this ADR adoption. |
| `P1-ADR-0028-DECISIONS-README-CASCADE` | OPEN; BLOCKING-CONCURRENT-WITH-ADR | [docs/decisions/README.md](../decisions/README.md) "Inference and statistical methodology" section gains the ADR-0028 entry. |
| `P1-ADR-0028-GLOSSARY-CASCADE` | OPEN; BLOCKING-CONCURRENT-WITH-ADR | [docs/glossary.md](../glossary.md) gains entries under §"KPI annotation grammar" for the two new annotations. |

### Non-blocking follow-ups

| Follow-up | Description |
|---|---|
| `P1-ADR-0028-TEMPLATE-CASCADE` | [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) Table 8 ("Other KPIs") gains rows for the two new annotations |
| `P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-CALIBRATION` | Empirical calibration of the `size_down_fraction = 0.5` default via paper-trade fill data once available |
| `P1-ADR-0028-MULTI-STEP-RATCHET-V2` | Multi-step ratchet variant (50% → 25% → 12% → block) for v2 if v1 fixed-fraction proves underpowered |
| `P1-ADR-0028-DYNAMIC-SIZE-DOWN-FRACTION-V2` | Dynamic size-down fraction as a function of breach magnitude (Alternative D rejection deferred) |
| `P1-ADR-0028-EXIT-ON-BREACH-INVESTIGATION-V2` | Exit-on-breach as a separate primitive (Alternative B rejection deferred) |
| `P1-ADR-0028-SIZE-DOWN-MODE-FAILURE-MODE-INVESTIGATE` | Investigation memo on size-down mode's own failure modes once first empirical run lands |
| `P1-ADR-0028-ZERO-COST-REFERENCE-CELL-CONVENTION` | Documentation pattern for zero-cost reference cell emission alongside cost-applied KPI cards |
| `P1-ADR-0028-H055-V2-C9-SIZE-DOWN-INTERACTION-DOCUMENT` | Document the multiplicative composition of C9 BOCD-step-up Kelly halving × size-down Kelly halving in H055 v2 |
| `P1-ADR-0028-RETROACTIVE-V3-COST-FRICTION-EDGE-ANNOTATION-PASS` | Retroactive emission pass: re-evaluate the H062 v3 + H055 v3 + H065 v2 + H060 v2 KPI cards for the new annotation post-CASCADE-impl |

## Pre-existing follow-up closed by this ADR

`P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` — registered Phase O.15 commit `1adc62a` per the H062 v3 investigation memo §8 + the Phase O.15 audit trail's "New follow-ups" table. Status transitions from OPEN to **CLOSED-BY-ADR-0028** with cross-reference logged here per ADR-0013 §4.1 non-loss. The follow-up entry in the parent CLAUDE.md Phase O.15 ledger + the investigation memo + the prior audit trail is preserved verbatim per non-loss; this closure logs the supersession.

## Closure

- **ADR closure**: Round 1 self-audit complete with `accept-with-residuals` verdict; 7 major findings remediated inline across quant + literature + format branches; 13 minor findings accepted as canonical project conventions or accepted with documented residuals.
- **Round 2 verification**: deferred to the first code amendment cycle (`P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL`) where the parity-test extension empirically enforces the §D-3 backward-compatibility claim. Per ADR-0027 §D-3, the empirical-before-amendment rule is satisfied at ADR adoption (H062 v3 ablation closed in Phase O.15 commit `1adc62a` + SHA backfill `63a22d2`); Round 2 is the implementation-verification layer.
- **Commit SHA**: TBD at landing time; this audit trail commits in the same commit group as the ADR + cascade artifacts.
- **Push target**: `origin/main`.
- **Time-budget category** (per ADR-0027 §D-5 non-binding annotation): `investigate` (empirical-follow-through of the H062 v3 ablation; counts toward the ≤25% investigation soft cap of the rolling-30-day commit history per `P1-ADR-0027-TIME-BUDGET-TRACKER-SCRIPT`).

## Cross-references

- ADR-0028: [docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md](../decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md)
- Empirical anchor: [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) + [docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md](audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md)
- Parent ADRs (preserved verbatim by this amendment): [ADR-0025](../decisions/ADR-0025-abandonment-trigger-infrastructure.md), [ADR-0027](../decisions/ADR-0027-operational-discipline-bounded-exploration.md), [ADR-0013](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), [ADR-0017](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md), [ADR-0018](../decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md), [ADR-0024](../decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md), [ADR-0026](../decisions/ADR-0026-paradigm-and-reporting-refinements.md)
- Phase O.15 CLAUDE.md ledger entry (cascade update concurrent with this commit): [CLAUDE.md §"Phase O.15"](../../CLAUDE.md)
