---
id: ADR-0027
title: Operational discipline — INVESTIGATE-FAILURE-MODE follow-up class, grid-search axis budgets, empirical-before-amendment sequencing, genetic-successor discipline, soft time-budget split
status: accepted
date: 2026-05-19
deciders: skoir
supersedes: []
proposes_amendments_to:
  - ADR-0013 §"Research philosophy" — extends permanent-exploration with explicit `INVESTIGATE-FAILURE-MODE-*` follow-up class for catastrophic / surprising / null results approached with curiosity rather than archived; adds soft time-budget split guidance
  - ADR-0018 §D-2 Kelly multiplier grid + §D-4 switching-bandit — extends with project-wide cell-budget cap + walk-forward-window-as-bounded-explicit-set discipline + DSR-deflation activation aligned with existing project `dsr_activation_size` convention
  - CLAUDE.md §"Agentic Iteration" + §"Conventions" — adds INVESTIGATE-FAILURE-MODE taxonomy + grid-search axis discipline + empirical-before-amendment sequencing rule
preserves_immutability_of:
  - All hypothesis design.md §1-§7 (per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline)
  - All historical audit trails, ReproLogs, sidecars, KPI report cards, promotion logs, NinjaScript strategies, design.md §17 revision logs (per ADR-0013 §4.1 non-loss mandate)
  - ADR-0013 §1 stage-progression model + §4 non-loss mandate + §5 NinjaScript-terminus mandate (preserved unchanged; INVESTIGATE-FAILURE-MODE is additive — investigation outputs become inputs to subsequent stage transitions)
  - ADR-0018 §D-1 MPPM(ρ=1) as inner-CV fitness — preserved verbatim; §D-2 below pins the existing fitness rule, does not change it
  - ADR-0024 D-2 / D-3 / D-4 opt-in framing — preserved verbatim; the cell-budget cap is operator-tunable per §D-2, not mandatory
  - The CLAUDE.md user-global "Agentic Iteration (default pattern)" — preserved verbatim; the audit-remediate-loop 3-round cap remains in force; INVESTIGATE-FAILURE-MODE follow-ups invoke the loop with the standard cap
---

# ADR-0027 — Operational discipline: bounded failure investigation, grid-search axis budgets, empirical-before-amendment sequencing

## Context

### Why this ADR exists

The operator 2026-05-19 paradigm review surfaced five formalizations. Two (#1 succinct comms, #2 3-component KPI, #5 promising-strategy pinning) are reporting-discipline concerns addressed by [ADR-0026](ADR-0026-paradigm-and-reporting-refinements.md). The remaining three (#3 explore-and-diagnose-failures, #4 grid-search-all-metrics, sequencing operator-intuitions through empirical decomposition before codification, and per-lineage time-budget split) are operational-discipline concerns addressed here.

Four load-bearing empirical anchors:

1. **Catastrophic results are currently treated as archive-candidates rather than investigation-candidates.** Per CLAUDE.md §"Phase E" (H050 −81/−84% gated arms; HMM gating actively harms directional signal) + §"Phase O.13" (H062 v3 −99.9995% basket under cost-realistic operation), the project's catastrophic outcomes are documented in audit trails + KPI cards but the WHY-CATASTROPHIC investigation cycle has not been formally executed. The operator 2026-05-19 directive ("instead of archiving or NULLing hypothesis that are 'catastrophic', perhaps we should approach them with curiosity") authorizes formalizing the investigation cycle as a new follow-up class.

2. **Grid-search over walk-forward window + Kelly + ADR-0025 primitive combinations is combinatorially unbounded if uncapped.** Per the prior-message anticipation: H062 v2 = 24+ hr at one walk-forward window. Grid-searching window × Kelly (6) × ADR-0025 primitives (2^4=16) × cells = 50-100× baseline compute. Per CLAUDE.md §"Phase O.13" the H062 v3 smoke compute was ~16 min on 4-cell grid; full-grid extension without budget cap projects to weeks of wall-clock per hypothesis. A project-wide cell-budget cap is required.

3. **Operator intuitions are valuable but not always empirically borne out at first cast.** Per the prior-message anticipation: the operator's "Phase O.13 v3 muted profits while drawdowns ran" intuition is testable via 3 ablations (cost-only, kill-switch-only, equity-rebase-only). The intuition may be partly correct (kill-switch asymmetry IS structural) and partly hindsight bias (cost-realistic may be the dominant driver). Codifying the intuition into an ADR amendment BEFORE the empirical decomposition runs would inherit an unverified prior into the formalization — the canonical pathology that `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` was registered to catch at the ledger layer (Phase O.10 R1 Hsu-Kuan 2005 finding-direction inversion was the same regression class).

4. **The project's hypothesis register grows monotonically; without explicit discipline, branching outpaces resolution.** Per [hypothesis_backlog.md](../../hypothesis_backlog.md): 60+ hypothesis IDs at adoption time (H050-H062 + H065-H066 emitted/queued; H100-H149 reserved per ADR-0021; H200-H249 reserved per Phase N memo). Per ADR-0013 §1 no-archive policy + ADR-0026 §D-3 genetic-successor framing, every emitted KPI may spawn N successors; every catastrophic result MAY spawn an investigation; every promising cell MAY spawn a doubling-down successor. Without per-lineage time-budget guidance, the backlog grows without bound.

### Where this fits relative to ADR-0013 + ADR-0018 + ADR-0024

ADR-0013 (2026-05-03) established permanent-exploration + no-archive + non-loss. ADR-0027 extends this by formalizing the INVESTIGATE-FAILURE-MODE class as a curiosity-driven branch of the hypothesis-tree — catastrophic results become investigation-inputs, not termini.

ADR-0018 (2026-05-12) established the Kelly multiplier grid + walk-forward + BOCD framework. ADR-0027 extends with axis-budget discipline: walk-forward window as bounded set, cell-budget cap, mandatory DSR deflation once realized cells > 1.

ADR-0024 (2026-05-15) demoted ADR-0017 §4.2 / §5 / §6 to opt-in. ADR-0027 preserves the opt-in framing; the §D-2 cell-budget cap is operator-tunable, not a binding gate.

### Operator directive (2026-05-19)

> "(3) Exploring and diagnosing failures, (4) Emphasizing grid search for all metrics, including walk forward window, kelly, and any new approaches such as O.13... Let us make our approach almost genetic: we take our hypotheses that are found to be most successful and keep approaching them from new angles. Additionally, instead of archiving or NULLing hypothesis that are 'catastrophic', perhaps we should approach them with curiosity."

Plus the prior-message anticipation re: empirical-before-amendment sequencing rule (operator endorsed: "this is good").

## Decision

### D-1. `INVESTIGATE-FAILURE-MODE-*` follow-up class

A new follow-up tag class distinct from the existing `P1-*` polish/extension class. Format: `INVESTIGATE-FAILURE-MODE-{slug}`. Every entry SHALL specify five mandatory fields:

- **(a) Hypothesis-of-investigation**: one-sentence statement of the empirical anomaly to be investigated. Example: "H062 v3 −99.9995% basket under cost-realistic + kill-switch-runtime operation: decompose cause by primitive engagement."
- **(b) Decomposition plan**: the specific ablation / mechanism-probe / cross-cell comparison to execute. Example: "3 ablations on existing v3 fixture: cost-only (kill-switch + equity-rebase OFF), kill-switch-only (cost + equity-rebase OFF), equity-rebase-only (cost + kill-switch OFF); report per-primitive contribution to the −99.9995% delta."
- **(c) Termination criterion**: explicit condition under which the investigation closes. Acceptable forms: (i) "close when {specific decomposition / ablation / mechanism-probe} completes"; (ii) "close when 3 rounds of audit-remediate-loop have been applied per SKILL.md 3-round cap"; (iii) "close when operator-discretionary verdict logged at [logs/promotions/...]"; (iv) "close when the underlying hypothesis-of-investigation is retired via ADR-0013 §1 stage transition" (e.g., a successor supersedes the investigation target); (v) "close when an upstream substrate change or paradigm shift makes the investigation moot" (e.g., post-substrate-refresh re-run that obsoletes the original finding) — entry MUST cross-reference the superseding ADR / substrate vintage. Investigations WITHOUT a termination criterion are R1-audit blockers.
- **(d) Wall-clock time budget (soft cap)**: rough estimate for project-priority planning. Example: "~2 hr per ablation × 3 = ~6 hr; cap at 8 hr." Soft cap; overrun is allowed but requires per-overrun `# justify:` annotation.
- **(e) Output artifact spec**: investigation outputs do NOT use ADR-0014 §3.2 13-table format (they are not KPI reports). Acceptable artifact classes: (i) **investigation-memo** at `research/_templates/investigation_memo_template.md` (new template; ~1-2 page synthesis of decomposition + finding + implication); (ii) **new hypothesis pre-registration successor** (when investigation surfaces a successor variant worth pre-registering); (iii) **ADR amendment** (when investigation surfaces a paradigm shift worth codifying). The default is investigation-memo unless (ii) or (iii) is explicitly motivated.

**Examples of high-value INVESTIGATE-FAILURE-MODE targets at adoption time**:

- `INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM`: why does HMM regime-gating actively HARM the directional signal on intraday large-cap futures (per CLAUDE.md §"Phase G" finding T_H050 = SR_gated − SR_uncond < 0 with LW2008 CI excluding zero negatively on BOTH ES + NQ)?
- `INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION`: decompose H062 v3 −99.9995% by primitive engagement (cost vs kill-switch vs equity-rebase ablation) per the operator 2026-05-19 intuition + the empirical-before-amendment sequencing rule of §D-3.
- `INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS`: why does MGC swing from +87.0% (C3) to −94% (C3 in some Phase O.7 sub-window slices) to +73.4% (C9 BOCD step-up) — what's the per-fold dependency on regime conditioning?

Investigation outputs are inputs to subsequent decisions: pre-register a successor; amend an ADR (per §D-3); update the hypothesis-of-record's failure_log.md per ADR-0013 §4.2; or log "investigation complete, no successor warranted" per ADR-0013 §1.

### D-2. Grid-search axis discipline

When grid-searching multiple axes (walk-forward window, Kelly multiplier, channel-N, ATR-n, ADR-0025 primitive on/off combinations, etc.), the following discipline applies:

- **Cell-budget cap per hypothesis lineage**: `cell_budget_cap_v1 = 1000` cells (operator-tunable per hypothesis with explicit `# justify:` annotation in design.md §5). `# justify:` operator-operational v1 default; caps overnight runs at ~10-20 hr wall-clock matching the [ADR-0011](ADR-0011-production-walkforward-runbook.md) supervised-relaunch-loop 6-hr-per-attempt × 3-4 attempts envelope. Per-cell wall-clock varies materially with substrate size + inner-CV configuration; empirical anchor pending `P1-ADR-0027-CELL-BUDGET-CAP-EMPIRICAL-CALIBRATION`.
- **Walk-forward window as bounded explicit set**: walk-forward window SHALL NOT be a free Optuna-tunable hyperparameter. It MUST come from a bounded set declared at design.md §5 freeze time. Canonical project-operational set: `{63, 126, 252, 504}` calendar sessions (`# justify:` quarterly / semi-annual / annual / biennial CME-trading-day decompositions; [Bergmeir-Benítez 2012](https://doi.org/10.1016/j.ins.2011.12.028) + [Tashman 2000](https://doi.org/10.1016/S0169-2070(00)00065-0) establish walk-forward CV validity in general but neither prescribes this specific set — literature-anchor extension tracked under `P1-ADR-0027-WALK-FORWARD-WINDOW-SET-EXTEND`). Hypotheses MAY declare a subset (e.g., H062 v3 declares `{252}` per the existing inner-CV pattern); they MAY NOT declare it as a free-tunable axis. Rationale: tuning the splitter window length against the same OOS evidence used to evaluate the strategy creates a nested-CV selection-bias risk per [Varma & Simon 2006 *BMC Bioinformatics* 7:91 DOI 10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91) + [Cawley & Talbot 2010 *JMLR* 11:2079-2107](https://www.jmlr.org/papers/v11/cawley10a.html). This is structurally distinct from the within-CV purging discipline of [López de Prado 2018 AFML](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) (*practitioner*) Ch. 7 (purging + embargo WITHIN a fixed splitter ≠ tuning the splitter; AFML Ch. 7 preserved verbatim).
- **Hansen SPA power-simulation K_max scaling**: for any walk-forward run with realized cells > 500, the power-simulation under `P1-H062-POWER-SIMULATION-EXECUTE` (and equivalents at H055 / H065) SHALL be re-executed at `K_max = max(500, realized_cell_count)` (`# justify:` ensures pre-registered power bound covers the realized family size — the SPA test itself uses realized family m by construction per [Hansen 2005 *JBES*](https://doi.org/10.1198/073500105000000063) §2; K_max is the project's PRE-REGISTRATION power-simulation parameter, not a runtime SPA family-wise-control parameter — the rule does not modify SPA mechanics).
- **DSR / PSR deflation REQUIRED when realized cell count ≥ `dsr_activation_size`** (per [config/gate.yaml](../../config/gate.yaml) project convention; currently 10): for multi-cell grid-searches whose realized cell count meets the activation threshold, DSR deflation per [Bailey-López de Prado 2014 *JPM*](https://doi.org/10.3905/jpm.2014.40.5.094) is required in the KPI report card §3.2 Table 7 alongside the SPA p-value. The `dsr-n/a (M < activation_size)` annotation applies below the threshold (preserves the H050 v1 + H052a v1 + H062 v2 precedent). `# justify:` align with existing project-canonical `dsr_activation_size` convention; deflation factor is empirically near-no-op below ~5-10 cells per `P1-DSR-ACTIVATION-SIZE-EMPIRICAL-CALIBRATION`. Per ADR-0024 §D-1 no-binding-gates preservation, "REQUIRED" applies to the KPI report card §"Methodological-correctness annotations" line, NOT to a promotion gate.
- **Inner-CV fitness metric** SHALL be MPPM(ρ=1) per ADR-0018 §D-1. Sharpe is forbidden as inner-CV fitness post-2026-05-12 per ADR-0018 acceptance.
- **ADR-0025 primitive combinations**: the 2^4=16 on/off combinations of (kill-switch-runtime, equity-rebase-current, BOCD-live, cost-model) are admissible as a grid axis BUT consume 16× the per-cell wall-clock budget. The operator-recommended default is the **2-cell baseline**: `(cost-zero, equity-fixed)` for v2-baseline-comparability + `(cost-conservative-prior, equity-current)` for promotion-decision evidence; kill-switch + BOCD-live remain fixed CLI flags per design.md §11.1 declaration. The other 14 combinations are admissible as opt-in sensitivity exhibits with explicit `# justify:` in design.md §5. `# justify:` per CLAUDE.md Phase O.13 H062 v3 empirical finding, only `(conservative_prior, current)` produces operator-actionable forward-projection P(loss) numbers; the other primitive combinations reproduce the v2 baseline or are diagnostic-only.

### D-3. Empirical-before-amendment sequencing rule

When an operator empirical intuition is surfaced as motivating an ADR amendment (e.g., "Phase O.13 v3 muted profits while drawdowns ran"), the following sequence is mandatory:

1. **Record the intuition** as a hypothesis in the audit-remediate-loop trail. The intuition is provisional until empirical decomposition validates it.
2. **Execute the empirical decomposition** (ablation, mechanism-probe, cross-cell comparison, or whatever specific test would discriminate the intuition from alternative explanations). Output: a finding statement of the form "decomposition X shows {result Y}, which {confirms / refutes / partially supports} the original intuition."
3. **Write the ADR amendment** AFTER the finding lands, codifying the EMPIRICAL result, not the pre-decomposition intuition. If the empirical finding refutes the intuition, the ADR amendment reflects the refutation (or no amendment is written).

**Exemption**: pure-policy or structural ADRs (e.g., ADR-0014 reporting format, ADR-0026 §D-2 succinctness carveout, this ADR-0027 §D-1 INVESTIGATE-FAILURE-MODE class) do NOT require empirical decomposition — they are operator-policy decisions, not empirically-motivated claims about market behavior. The rule applies specifically to ADR amendments that codify a claim about market / strategy / mechanism behavior (e.g., "K-6/K-7 should size-down rather than block-entries" is a behavioral claim that requires the v3 ablation).

**Pathology this rule prevents**: the Phase O.10 Hsu-Kuan 2005 finding-direction inversion class — codifying a stated belief without verifying the load-bearing empirical claim, then propagating the error through dependent artifacts.

### D-4. Genetic-successor discipline

When a hypothesis spawns a successor variant (H062 → H065 → H066, etc.) under the genetic-branching framing of the operator's 2026-05-19 directive, the successor design.md §17 revision log SHALL cite four mandatory fields:

- **Parent hypothesis ID + final stage**: e.g., "H062 v2 at `kpi-report-emitted` per Phase O.10."
- **Motivating KPI / annotation**: the specific KPI value or annotation in the parent that motivated the successor. Example: "H062 v2 L-skewness τ_3 = +0.74 with marginal mean-edge (MPPM CI [−0.34, +0.54]) motivates an ATR-scaled profit-target overlay successor to test whether bounding the right tail at integer R-multiples preserves the skew shape while improving mean-edge."
- **Genetic-cross**: what specifically changes from parent to successor. Single-axis change is canonical (e.g., "add ATR-scaled profit-target at M × k_atr × ATR_n for M ∈ {1.0, 1.5, 2.0, 2.5}"). Multi-axis changes require explicit `# justify:` annotation per axis.
- **Preserved infrastructure**: what stays from parent (substrate, inner-CV machinery, cost model, kill-switch config). Default: everything not in the "genetic-cross" field is preserved verbatim.

Successors are NOT amendments to the parent (per ADR-0013 §"Frozen pre-registration" §1-§7 immutability discipline). They are siblings in the hypothesis tree per ADR-0013 §4.1 non-loss. The parent's KPI cards stay verbatim; the successor's KPI cards are new versioned artifacts.

**Cross-reference**: the existing [plan/buildouts/h055_successor_tree_2026-05-06.md](../../plan/buildouts/h055_successor_tree_2026-05-06.md) + ADR-0015 component-stacking master architecture together define the genetic-successor tree at the level of multi-hypothesis lineages. ADR-0027 §D-4 formalizes the per-successor design.md §17 disclosure requirement so any future reader of a v(N+1) hypothesis can trace its parentage without external reconstruction.

### D-5. Soft per-lineage time-budget split

Operator-discretionary guidance, NOT hard gate. `# justify:` operator 2026-05-19 directive "Let us spend the majority of our time in the present"; soft directional split per ADR-0013 §1+§2 no-binding-gates preservation:

- **Majority (≥ 50%) of compute + research time** in present-tense exploration: new hypothesis pre-registrations, grid-search sweeps on most-recent paradigm, novel signal-class probes.
- **≤ 25% on `INVESTIGATE-FAILURE-MODE-*` follow-ups**: catastrophic-result decompositions, mechanism-probes, ablations. Allocated against the present-tense majority.
- **≤ 25% on doubling-down successors of already-emitted KPIs**: genetic-branching variants of `promising-*` annotated cells (per ADR-0026 §D-3). Allocated against the present-tense majority.

Per-commit annotation (non-binding): commits may carry a `time-budget: {present, investigate, successor}` trailer disclosing which category the work falls into. Tracker is operator-visible across the rolling 30-day commit history via a tracker script landing under `P1-ADR-0027-TIME-BUDGET-TRACKER-SCRIPT` (non-blocking; v1 mode is operator self-discipline with no automated enforcement — at the rolling-30-day-tracker landing the operator gains visibility but no hard cap). If `investigate` or `successor` exceeds 25%, the operator may rebalance allocations at the next session boundary.

**Rationale per the operator's 2026-05-19 directive**: "Let us spend the majority of our time in the present, hypothesizing, exploring, testing, and being inquisitive in a safe environment where high risk is feasible."

## Alternatives considered

### A. Make INVESTIGATE-FAILURE-MODE a sub-class of `P1-*` instead of a new tag class

Rejected. The existing `P1-*` class is polish/extension/cascade follow-ups — implementation work driven by audit findings. INVESTIGATE-FAILURE-MODE entries are research-design work — formulating hypotheses about WHY a catastrophic / surprising result occurred. The two classes have different output artifact types (`P1-*` → code + tests + design.md edits; INVESTIGATE-FAILURE-MODE → investigation-memos + potential new pre-registrations). Sharing a tag class would obscure the distinction.

### B. Make the cell-budget cap a binding gate rather than an operator-tunable parameter

Rejected per ADR-0013 §1 + §2 no-binding-gates philosophy preserved by ADR-0024. The cap is a SOFT default (1000); operator may override per hypothesis with `# justify:` annotation. Hard-gating would conflict with the no-binding-gates principle.

### C. Apply the empirical-before-amendment sequencing rule to ALL ADRs (not just behavior-claiming ones)

Rejected. Pure-policy ADRs (e.g., reporting format, communication discipline) are operator-decisions, not empirical claims. Requiring empirical decomposition for "the §0 KPI summary header is 3 components" would be a category error. The exemption per §D-3 is principled: the rule applies to ADRs that codify a CLAIM ABOUT MARKET / STRATEGY / MECHANISM BEHAVIOR.

### D. Set the time-budget split as a binding allocation per session

Rejected. Operator's 2026-05-19 framing was "majority of time in present" — directional guidance, not hard cap. Soft annotation + rolling 30-day tracker is the principled instantiation.

### E. Defer ADR-0027 until ADR-0026 is fully cascaded

Rejected. The operator's 2026-05-19 directive surfaced all five formalizations together; sibling ADR landing is the natural unit. Per the prior-message recommendation: "split into ADR-0026 (paradigm + reporting) and ADR-0027 (operational discipline)." Both land in the same commit group to preserve the integrated paradigm-resolution semantic.

## Consequences

### Adopted

- `INVESTIGATE-FAILURE-MODE-*` follow-up class per §D-1 with mandatory 5-field structure.
- Grid-search axis discipline per §D-2: cell-budget cap = 1000 cells; walk-forward window as bounded set; mandatory DSR deflation when realized cells > 1; MPPM(ρ=1) as canonical inner-CV fitness.
- Empirical-before-amendment sequencing rule per §D-3.
- Genetic-successor discipline per §D-4: design.md §17 four-field cross-citation requirement.
- Soft per-lineage time-budget split per §D-5: ≥50% present-tense; ≤25% investigate; ≤25% successor.

### KPI annotation grammar additions

Two new annotations extend the CLAUDE.md §"KPI report card for every strategy" grammar:

- `investigation-pending` / `investigation-active` / `investigation-complete-{outcome}` — INVESTIGATE-FAILURE-MODE lifecycle state for hypotheses that have entries in the new follow-up class. Outcomes: `successor-pre-registered`, `adr-amended`, `no-further-action`. Emitted in the KPI report card §"Methodological-correctness annotations" line.
- `cell-budget-{N}-of-{budget-cap}` — grid-search cell count vs cap disclosure. Emitted alongside the `dsr-positive / dsr-marginal / dsr-negative / dsr-n/a (M=1)` annotation per ADR-0014 §3.2.

### Trade-offs accepted

- **Cell-budget cap may bind on heavy grid sweeps.** A hypothesis declaring `{63, 126, 252, 504}` walk-forward windows × 6 Kelly multipliers × 4 channel-N × 3 ATR-n × 4 trend-IDs = 1152 cells exceeds the v1 cap of 1000. Operator override via `# justify:` annotation is admissible.
- **Walk-forward-window-as-bounded-set may feel restrictive.** Justified by the PIT-leakage-adjacency risk; the bounded set `{63, 126, 252, 504}` covers the published-research conventions. Project-specific extension may be added per `P1-ADR-0027-WALK-FORWARD-WINDOW-SET-EXTEND` with literature anchor.
- **Empirical-before-amendment sequencing rule slows ADR cadence.** Justified by the regression-class evidence (Phase O.10 Hsu-Kuan 2005 inversion; ledger-claim drift caught by `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE`). One round of empirical decomposition before ADR write is cheaper than re-doing the ADR after the inversion is caught.
- **Time-budget split is non-binding.** Pure operator discretion; the soft annotation is for visibility only.

### Residual risk

- **INVESTIGATE-FAILURE-MODE follow-ups may still drift without operator oversight.** Even with mandatory 5-field structure including termination criterion, an investigation can become "always one more ablation away from closing." Mitigated by `time_budget` soft cap per §D-1(d) + operator-visible commit-tag rolling tracker per §D-5.
- **Cell-budget cap may be circumvented by hypothesis-splitting** (e.g., split a 2000-cell hypothesis into H062-a with 1000 cells + H062-b with 1000 cells). Operator-discretionary at design.md freeze time. The cap is per LINEAGE not per HYPOTHESIS-ID; lineage tracking is informal at adoption time. Tracked under `P1-ADR-0027-LINEAGE-TRACKING-FORMAL`.
- **MPPM(ρ=1) as inner-CV fitness is the canonical project choice but is not universally optimal.** Per ADR-0018 §D-1 the rationale is the GISW 2007 manipulation-proof property + log-wealth equivalence at ρ=1. Hypotheses requiring alternative fitness (e.g., minimum-CVaR for tail-sensitive strategies) may declare alternative inner-CV fitness with explicit `# justify:` annotation; the existing ADR-0018 §D-1 grammar supports this carveout.
- **Genetic-successor discipline depends on operator's "promising" identification per ADR-0026 §D-3.** If "promising" annotations are sparse or substrate-vintage-stale, the successor tree may not branch productively. Mitigated by the §D-3 annotation pinning + retroactive cascade follow-up.

### Cascade requirements

- **`P1-ADR-0027-CLAUDE-MD-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — CLAUDE.md §"Agentic Iteration" gains the INVESTIGATE-FAILURE-MODE follow-up class entry; §"Conventions" gains the grid-search axis discipline summary; §"Research philosophy" gains the soft time-budget split.
- **`P1-ADR-0027-DECISIONS-README-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — [docs/decisions/README.md](README.md) gains the ADR-0027 entry.
- **`P1-ADR-0027-INVESTIGATION-MEMO-TEMPLATE`** (BLOCKING-CONCURRENT-WITH-ADR) — new template at [research/_templates/investigation_memo_template.md](../../research/_templates/investigation_memo_template.md).
- **`P1-ADR-0027-HYPOTHESIS-BACKLOG-INVESTIGATION-SECTION`** (non-blocking) — [hypothesis_backlog.md](../../hypothesis_backlog.md) gains a new section for `INVESTIGATE-FAILURE-MODE-*` entries.
- **`P1-ADR-0027-GLOSSARY-CASCADE`** (non-blocking) — [docs/glossary.md](../glossary.md) gains entries for `INVESTIGATE-FAILURE-MODE-*`, `investigation-{pending, active, complete-*}`, `cell-budget-{N}-of-{cap}`.

### BLOCKING follow-ups registered by ADR-0027

| Follow-up | Status | Description |
|---|---|---|
| `P1-ADR-0027-CLAUDE-MD-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | CLAUDE.md §"Agentic Iteration" + §"Conventions" + §"Research philosophy" updates |
| `P1-ADR-0027-DECISIONS-README-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | ADR index entry |
| `P1-ADR-0027-INVESTIGATION-MEMO-TEMPLATE` | BLOCKING-CONCURRENT-WITH-ADR | New template at `research/_templates/investigation_memo_template.md` |

### Non-blocking `P1-*` follow-ups

| Follow-up | Description |
|---|---|
| `P1-ADR-0027-HYPOTHESIS-BACKLOG-INVESTIGATION-SECTION` | Add `INVESTIGATE-FAILURE-MODE-*` section to `hypothesis_backlog.md` |
| `P1-ADR-0027-GLOSSARY-CASCADE` | Glossary entries for new annotations |
| `P1-ADR-0027-LINEAGE-TRACKING-FORMAL` | Formal lineage-tracking primitive (parent → successor graph) at `src/skie_ninja/utils/hypothesis_lineage.py` |
| `P1-ADR-0027-WALK-FORWARD-WINDOW-SET-EXTEND` | Project-specific extension of the `{63, 126, 252, 504}` canonical set with literature anchor |
| `P1-ADR-0027-CELL-BUDGET-CAP-EMPIRICAL-CALIBRATION` | Empirical re-calibration of the 1000-cell cap after the first few grid sweeps land |
| `P1-ADR-0027-TIME-BUDGET-TRACKER-SCRIPT` | Tracker script at `scripts/report_time_budget_30day.py` scanning commit trailers and emitting a status report; operator-visible v1 mode without hard enforcement (per F-1-14 R1 audit fix) |
| `P1-CLAUDE-MD-PRACTITIONER-TAG-FORMALIZE` | Add CLAUDE.md §"Practitioner-source-tag" section to formalize the `*practitioner*` italic suffix convention referenced by ADR-0025 / ADR-0026 / ADR-0027 (per FA-1-2 R1 audit fix; inherited defect from ADR-0025) |

### `INVESTIGATE-FAILURE-MODE-*` follow-ups registered at adoption time

| Follow-up | Description |
|---|---|
| `INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM` | Why does HMM regime-gating actively HARM the directional signal? |
| `INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION` | Decompose v3 −99.9995% by primitive engagement (cost vs kill-switch vs equity-rebase ablation) — load-bearing for any future `P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` per §D-3 empirical-before-amendment rule |
| `INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS` | Cross-cell + cross-Kelly MGC behavior decomposition |

## References

### Primary peer-reviewed sources

- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management*, 40(5), 94–107. [DOI 10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094). (DSR deflation — mandatory in §D-2 when realized cells > 1.)
- Bergmeir, C., & Benítez, J. M. (2012). On the use of cross-validation for time series predictor evaluation. *Information Sciences*, 191, 192–213. [DOI 10.1016/j.ins.2011.12.028](https://doi.org/10.1016/j.ins.2011.12.028). (Walk-forward CV validity in general; does NOT prescribe the specific bounded set `{63, 126, 252, 504}` cited in §D-2 — that mapping is project-operational per CME quarterly/semi-annual/annual/biennial decompositions.)
- Cawley, G. C., & Talbot, N. L. C. (2010). On over-fitting in model selection and subsequent selection bias in performance evaluation. *Journal of Machine Learning Research*, 11, 2079–2107. [JMLR open access](https://www.jmlr.org/papers/v11/cawley10a.html). (Nested-CV selection-bias risk — anchor for "tuning the splitter against the same OOS evidence" claim in §D-2.)
- Goetzmann, W., Ingersoll, J., Spiegel, M., & Welch, I. (2007). Portfolio performance manipulation and manipulation-proof performance measures. *Review of Financial Studies*, 20(5), 1503–1546. [DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025). (MPPM(ρ=1) — canonical inner-CV fitness per §D-2.)
- Hansen, P. R. (2005). A test for superior predictive ability. *Journal of Business & Economic Statistics*, 23(4), 365–380. [DOI 10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063). (SPA family-wise control — K_max scaling rule per §D-2.)
- Lo, A. W. (2004). The Adaptive Markets Hypothesis: Market efficiency from an evolutionary perspective. *Journal of Portfolio Management*, 30(5), 15–29. [DOI 10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611). (AMH framing — strategy decay is the null; investigation-with-curiosity per §D-1 is the operational instantiation of Lo 2004's "continuous innovation as evolutionary necessity" insight.)
- Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: an analysis and review. *International Journal of Forecasting*, 16(4), 437–450. [DOI 10.1016/S0169-2070(00)00065-0](https://doi.org/10.1016/S0169-2070(00)00065-0). (Rolling-origin evaluation taxonomy in general; does NOT prescribe the specific bounded set in §D-2 — see Bergmeir-Benítez 2012 note.)
- Varma, S., & Simon, R. (2006). Bias in error estimation when using cross-validation for model selection. *BMC Bioinformatics*, 7, 91. [DOI 10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91). (Nested-CV selection-bias risk — anchor for "tuning the splitter against the same OOS evidence" claim in §D-2 alongside Cawley & Talbot 2010.)

### Practitioner sources (tagged per CLAUDE.md §"Practitioner-source-tag" convention)

- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley, ISBN-13 978-1119482086. (*practitioner*) Ch. 7 "Cross-Validation in Finance" — purging + embargo discipline WITHIN a fixed splitter (preserved verbatim by §D-2 walk-forward-window-bounded-set rule). Distinct from the §D-2 nested-CV selection-bias claim which anchors on Cawley & Talbot 2010 + Varma & Simon 2006.

### Project-internal

- [ADR-0001](ADR-0001-project-scope.md) — retail capacity ceiling (cell-budget cap interacts with substrate compute).
- [ADR-0011](ADR-0011-production-walkforward-runbook.md) — supervised-relaunch-loop 6-hr-per-attempt convention (rationale for the 1000-cell cap default).
- [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — §"Research philosophy" + §4.1 non-loss + §"Frozen pre-registration amendment" (preserved verbatim; INVESTIGATE-FAILURE-MODE class extends this).
- [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — DSR / SPA annotation grammar in Table 7 + §"Methodological-correctness annotations" line.
- [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) — survival-constrained primary metric vector (preserved; §D-2 uses MPPM(ρ=1) as inner-CV fitness per ADR-0018 amendment).
- [ADR-0018](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — Kelly multiplier grid + BOCD + switching-bandit (§D-2 extends with axis budgets).
- [ADR-0021](ADR-0021-liquidity-provision-research-track-scoping.md) — H100-series reservation; relevant to lineage tracking per `P1-ADR-0027-LINEAGE-TRACKING-FORMAL`.
- [ADR-0024](ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) — opt-in framing (preserved; §D-2 cell-budget cap is operator-tunable, not binding).
- [ADR-0025](ADR-0025-abandonment-trigger-infrastructure.md) — primitive on/off combinations (referenced as one grid-search axis in §D-2).
- [ADR-0026](ADR-0026-paradigm-and-reporting-refinements.md) — sibling ADR; reporting-discipline counterpart.
- [plan/buildouts/h055_successor_tree_2026-05-06.md](../../plan/buildouts/h055_successor_tree_2026-05-06.md) — existing genetic-successor tree at multi-hypothesis-lineage level.
- [SKILL.md audit-remediate-loop](../../../../.claude/skills/audit-remediate-loop/SKILL.md) (project-local skill definition) — 3-round cap preserved verbatim; INVESTIGATE-FAILURE-MODE follow-ups invoke the loop with the standard cap.
- [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration" + §"Conventions" + §"Research philosophy" — receives §D-1 / §D-2 / §D-5 cascade.
- [docs/audits/audit_trail_2026-05-19_adr-0026-adr-0027.md](../audits/audit_trail_2026-05-19_adr-0026-adr-0027.md) — this ADR's audit-remediate-loop trail (shared with ADR-0026).

## Empirical justification

The empirical basis is the conjunction of (a) Phase E + Phase O.13 catastrophic results (H050 −81/−84%; H062 v3 −99.9995%) currently unaccompanied by formal investigation cycles per the operator 2026-05-19 directive; (b) the prior-message anticipated combinatorial explosion of grid-search across walk-forward window × Kelly multiplier × ADR-0025 primitive combinations × cells (50-100× baseline compute uncapped); (c) the Phase O.10 Hsu-Kuan 2005 finding-direction inversion + `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` precedent demonstrating the canonical regression class of codifying intuitions ahead of empirical decomposition; (d) the operator-stated 2026-05-19 framing "spend the majority of our time in the present" providing the time-budget split rationale. Each is independent evidence; together they constitute the load-bearing motivation for ADR-0027.

The CLAUDE.md user-global §"Evidence Hierarchy" is preserved unchanged. The §D-2 grid-search axis discipline draws from peer-reviewed primary sources (Bailey-López de Prado 2014 DSR; Cawley & Talbot 2010 + Varma & Simon 2006 nested-CV selection-bias risk; Bergmeir-Benítez 2012 + Tashman 2000 walk-forward CV validity; Hansen 2005 SPA mechanics; GISW 2007 MPPM) plus the practitioner anchor (López de Prado 2018 AFML Ch. 7 within-splitter purging — distinct from the nested-CV claim). The §D-1 INVESTIGATE-FAILURE-MODE class implements Lo 2004 AMH's "continuous innovation" insight at the project-process layer.

ADR-0027 is the canonical reference for the SKIE-Universe project's 2026-05-19+ operational discipline. It formalizes the INVESTIGATE-FAILURE-MODE follow-up class for curiosity-driven catastrophic-result decompositions; caps grid-search cell budgets at 1000 per hypothesis with mandatory DSR deflation; pins walk-forward window as a bounded explicit set to prevent PIT-leakage adjacency; sequences operator intuitions through empirical decomposition before ADR codification; formalizes genetic-successor design.md §17 cross-citation requirements; and adds a soft per-lineage time-budget split aligned with the operator's present-tense-exploration priority.
