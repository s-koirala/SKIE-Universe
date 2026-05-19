---
id: ADR-0026
title: Paradigm and reporting refinements — 3-component KPI summary header, succinct-communication carveout, promising-strategy triple
status: accepted
date: 2026-05-19
deciders: skoir
supersedes: []
proposes_amendments_to:
  - ADR-0014 §3.2 9-table format (extended to 12-table per ADR-0017 §3.2 then to 13-table per ADR-0019 §3) — prepended with a mandatory §0 3-component summary header (Full-OOS realized; 2026-OOS-onward sub-window; Forward 1-year bootstrap projection); the 13 tables are preserved verbatim and follow the §0 header
  - ADR-0017 §3 + ADR-0018 §D-1 — "promising" strategy assertions in KPI cards / audit trails / ledger entries MUST be qualified by the (KPI-vector, cost-model, substrate-vintage) triple; introduces `promising-*` annotation grammar
  - CLAUDE.md §"Communication" + §"KPI report card for every strategy" — annotation grammar extended; explicit verbosity carveout for mandatory artifacts
preserves_immutability_of:
  - All hypothesis design.md §1-§7 (per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline)
  - All historical audit trails, ReproLogs, sidecars, KPI report cards, promotion logs, NinjaScript strategies, design.md §17 revision logs (per ADR-0013 §4.1 non-loss mandate)
  - ADR-0014 §3.2 13-table grammar — preserved verbatim; the new §0 3-component header PRECEDES the existing 13 tables, does not replace any of them
  - ADR-0024 D-2 / D-3 / D-4 opt-in framing — preserved verbatim; reporting changes are orthogonal to the opt-in machinery
  - The CLAUDE.md user-global "high-density technical transfer; terminate at final requested material" directive — preserved; the carveout exempts MANDATORY artifact verbosity from the succinctness goal, not user-facing synthesis
---

# ADR-0026 — Paradigm and reporting refinements: 3-component KPI summary header, succinct-communication carveout, promising-strategy triple

## Context

### Why this ADR exists

The operator 2026-05-19 paradigm review surfaced four formalizations that the existing ADR-0013 / ADR-0014 / ADR-0017 / ADR-0018 / ADR-0024 stack does not directly cover. Two of those formalizations are reporting + communication concerns; ADR-0026 addresses them. The other two (failure-investigation discipline + grid-search axis budgets) are operational-discipline concerns addressed by the sibling [ADR-0027](ADR-0027-operational-discipline-bounded-exploration.md).

Three load-bearing empirical anchors motivate the reporting changes:

1. **The 2026 OOS sub-window is the operator-actionable forward-walk slice.** Per the operator's 2026-05-18 KPI-review directive ("ensure end report contains kpi tables and oos results for 2026"), and the Phase O.10 / Phase O.13 v3 emissions, the 2026-onward sub-window is being read as the canonical forward-walk evaluation by the operator. The ADR-0014 §3.2 13-table format embeds the 2026 sub-window into Table 6 (Forward 1-year bootstrap projection) — but the sub-window is a REALIZED forward-walk, not a bootstrap projection, and the conflation is misleading. A separate explicit summary component is the principled fix.

2. **The "promising" qualifier is unstable across paradigm versions.** Per CLAUDE.md §"Phase O.3" + §"Phase O.7" + §"Phase O.13": C3 super-Kelly produced +2,690% basket headline at Phase O.3 (zero-cost, fixed-cell); iter 4 km-era decomposition showed +208.8% concentrated in 7.2% of session-days (Phase O.7); cost-realistic v3 produced −99.9995% basket (Phase O.13). What looked "promising" under Phase O.3's KPI vector + cost model + substrate-snapshot was catastrophic under Phase O.13's. The operator's 2026-05-19 directive "doubling down on strategies that show promise" requires "promise" to be pinned to its evaluation triple to avoid doubling down on regime artifacts.

3. **Succinctness vs disclosure discipline tension.** Per the operator 2026-05-19 formalization #1 ("keeping responses succinct, to the point"), and the CLAUDE.md user-global "high-density technical transfer". This conflicts with the verbose-by-mandate artifacts: audit-remediate-loop findings tables (per SKILL.md), ReproLog 13-field schema, ADR-0014 13-table KPI cards, design.md §1-§17 full-section requirement, primary-source citation pinning per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` (recall the Phase N catches: Breiman 1996 *Annals* vs *Machine Learning*; Easley-LdP-O'Hara 2012 *RFS* vs *JPM*; Hsu-Kuan 2005 finding-direction inversion). Resolving this requires an explicit carveout.

### Where this fits relative to ADR-0014 + ADR-0017 + ADR-0018

ADR-0014 (2026-05-04) mandated the 9-table results-summary format; ADR-0017 §3.2 (2026-05-08) extended to 12 tables (3a + 3b + 3c survival metrics); ADR-0019 §3 (2026-05-12) added Table 1c (L-skewness payoff-shape) bringing the canonical format to 13 tables. ADR-0026 extends that chain with a §0 3-component header PRECEDING the existing 13 tables; the 13 tables are preserved verbatim. The §0 header is operator-readable at-a-glance; the 13 tables are the load-bearing detail.

ADR-0017 (2026-05-08) elevated terminal-wealth-q05 / Calmar-differential / profit-factor / R-multiple-mean as primary inferential metrics. ADR-0018 (2026-05-12) added MPPM(ρ=1) as primary inner-CV fitness. ADR-0026 does NOT touch the inferential machinery; it adds a `promising-*` annotation that pins any "promising" assertion to the triple (KPI-vector, cost-model, substrate-vintage) so that genetic-successor decisions are reproducible against the qualifying conditions.

### Operator directive (2026-05-19)

> "(1) keeping responses succinct, to the point, (2) reporting KPIs that summarize hypotheses into 3 components: results for OOS 2026 (p/l, dd, winrate, etc.), (3) Exploring and diagnosing failures, (4) Emphasizing grid search for all metrics, including walk forward window, kelly, and any new approaches such as O.13, (5) Doubling down on strategies that show promise. Let us incorporate these via audit-remediate loop."

Formalizations #1 + #2 + #5 are reporting + communication concerns addressed by ADR-0026. Formalizations #3 + #4 are operational-discipline concerns addressed by [ADR-0027](ADR-0027-operational-discipline-bounded-exploration.md). The split is per the prior-message anticipation ("a single 7-component ADR will accumulate ~50+ R1 findings per the ADR-0017 / ADR-0018 precedent; recommend split").

## Decision

### D-1. 3-component canonical KPI summary header at the top of every KPI report card

Every KPI report card emitted from 2026-05-19 forward SHALL carry a §0 "3-component summary" section PRECEDING the ADR-0014 §3.2 13-table format. The §0 section consists of a single three-row table per arm × symbol + basket. **Column types**:

| # | Component | Window | P/L % | Max-DD % | Win rate (W/(W+L+Z)) | MPPM(ρ=1) point | Realized-OOS q05 equity | Forward q05 equity | N (sessions) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Realized OOS (full) | Substrate-inception → most-recent | float % | float % | float % | float (signed) | float $ | n/a | int |
| 2 | Realized OOS (2026-onward) | 2026-01-01 → most-recent | float % | float % | float % | float (signed) | float $ | n/a | int |
| 3 | Forward 1-year bootstrap | 252-session Monte Carlo per [ADR-0013 §3.1.1](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) | n/a | float % | n/a | float (signed) | n/a | float $ | n/a |

**Convention pins** (binding):

- **Win rate column** is `W/(W+L+Z)` per ADR-0014 §3.2 Table 5 convention; Z = zero-P/L scratches. Components 1 + 2 only (n/a for Component 3 bootstrap).
- **Realized-OOS q05** (Components 1 + 2) is the 5th percentile of the per-session log-return distribution converted to ending-equity-fraction; **Forward q05** (Component 3) is the 5th percentile of the 5000-path × 252-session ending-equity distribution. The two q05 quantities are different statistical objects (in-sample percentile of realized log-returns vs out-of-sample percentile of forward-bootstrap ending equity); the column split prevents semantic conflation.
- **Per-symbol AND basket-aggregate rows are required** (so a 4-symbol basket emits 5 rows × 3 components = 15 rows in the §0 header).
- **N (sessions)** column reports per-symbol session-day count of the realized OOS window. Rows with `N < n_min_underpowered` SHALL carry an `underpowered-2026-subwindow` annotation (`# justify:` `n_min_underpowered = 30` default per [Lo 2002 *FAJ* 58(4):36-52](https://doi.org/10.2469/faj.v58.n4.2453) §III rough rule-of-thumb for Sharpe-CI minimum sample; empirical re-calibration tracked under `P1-ADR-0026-UNDERPOWERED-THRESHOLD-EMPIRICAL`).
- **Component 3 prerequisite**: forward-bootstrap requires per-session log-return persistence in the sidecar (the `per_session_logret_aggregate` field landed 2026-05-18 per CLAUDE.md §"Phase O.13 sidecar per-session-logret persistence closure"). For KPI cards re-emitted on sidecars WITHOUT this field (i.e., v1/v2 cards emitted before 2026-05-18), Component 3 row SHALL carry `component-3-deferred-pending-sidecar-persistence` annotation and the cells SHALL be marked `pending-rerun` rather than computed from a degenerate fallback.

**Component definitions** (binding):

- **Component 1 — Realized OOS (full)**: the full walk-forward OOS window from substrate inception through the most-recent test-fold-end per the design.md §2 window binding. This is the canonical "did the strategy work" question.
- **Component 2 — Realized OOS (2026-onward sub-window)**: the slice of Component 1's OOS series with `session_date >= 2026-01-01`. This is the canonical "what is the most recent forward-walk evidence" question — the operator's "2026 results" framing. Note: NOT a bootstrap projection; a realized sub-slice. Per-symbol substrate availability varies (NQ ends 2024-12-19; ES ends 2025-12-03; MGC/SIL extend to 2026-05-15+); rows for symbols with no 2026-onward data SHALL report `N=0` with `2026-subwindow-no-data` annotation.
- **Component 3 — Forward 1-year bootstrap projection**: per [ADR-0013 §3.1.1](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) mandate. 5,000 Monte Carlo paths × 252 sessions per arm; per-arm initial bankroll = $10,000. Distribution-summary metrics: median + q05 + q95 ending equity; P(loss) / P(double) / P(<50%); median max-DD.

**Replaces the ad-hoc 2026-sub-window section** at H055 v2 / H060 v2 / H062 v2 / H065 v2 KPI cards (which scattered 2026 data across Tables 1 + 1c + 8 + a free-form "End-of-simulation 2026 OOS results" subsection at variable positions). The §0 header is the single canonical location.

### D-2. Succinct-communication carveout — synthesis-succinct, mandatory-artifact-verbose

The CLAUDE.md user-global "high-density technical transfer; terminate at final requested material" is preserved unchanged. ADR-0026 adds an explicit carveout enumerating the artifact classes EXEMPT from synthesis-succinctness — i.e., classes that MUST satisfy their mandated verbosity even when total response length grows:

| Verbose-mandatory artifact class | Source mandate | Cannot be shorter than |
|---|---|---|
| Audit-remediate-loop findings tables | SKILL.md (audit-remediate-loop skill) | Per-finding row with: severity + branch + evidence + remediation disposition |
| ReproLog records | CLAUDE.md §"Reproducibility (hook-enforced)" + canonical 13-field schema | All 13 fields populated; absent = `null` not omitted |
| KPI report cards | ADR-0014 §3.2 + ADR-0026 §D-1 | §0 3-component header + 13 tables + §"Methodological-correctness annotations" + §"Bottom line" |
| Hypothesis design.md | ADR-0013 §"Frozen pre-registration" + per-hypothesis template | §1-§17 all sections present; §1-§7 immutable post-freeze |
| ADR full text | docs/decisions/README.md §"Conventions" | YAML frontmatter + Context + Decision + Alternatives + Consequences + References + Empirical justification |
| Primary-citation pinning | CLAUDE.md §"Evidence Hierarchy" | DOI / arXiv-ID / ISBN-13 + section/equation pin (or explicit `*-PIN-VERIFY` follow-up if deferred) |
| Per-hypothesis failure_log.md | ADR-0013 §4.2 | Per-event row with: timestamp + trigger + classification + resolution-disposition |

**Synthesis-succinct artifact classes** (where succinctness applies):

- Chat replies + executive summaries + end-of-turn reports
- CLAUDE.md ledger Phase entries (synthesize the per-commit detail; do NOT enumerate every finding — defer to the audit trail)
- `hypothesis_backlog.md` rows (one-line synopsis + cross-link to design.md)
- Operator-readable commit messages (Conventional Commits subject + body)
- Glossary entries
- README + INDEX + RESULTS_INDEX rows

**No artifact MAY be made shorter than what its template / ADR / schema mandates.** The carveout is one-way: succinct in synthesis, NEVER shorter than mandated in artifacts. This explicitly resolves the apparent tension between formalization #1 and the disclosure discipline maintained across Phase N / Phase O.10 / Phase O.13.

### D-3. "Promising" strategy assertions MUST be pinned to the (KPI-vector, cost-model, substrate-vintage) triple

Any artifact-resident assertion that a hypothesis / cell / arm is "promising" (or equivalent: "shows promise", "is a candidate for doubling down", "warrants successor pre-registration") SHALL be qualified by a triple specifying the evaluation conditions under which the assertion holds:

- **(a) KPI-vector**: which subset of the ADR-0017 + ADR-0018 metric universe drives the assertion. Examples: `mppm` (MPPM(ρ=1) point > 0 + CI excludes zero positively); `mppm+tw-q05` (MPPM positive AND terminal-wealth-q05 above starting bankroll); `realized-roi` (raw realized OOS % — deprecated as standalone qualifier but admissible as supporting evidence); `mppm+calmar-diff+payoff-shape` (MPPM positive AND Calmar-differential positive AND L-skewness τ_3 > 0).
- **(b) Cost-model**: per ADR-0025 §D-5 grammar. One of `cost-zero` / `cost-conservative-prior` / `cost-empirical-calibrated`. A `promising-*` assertion under `cost-zero` is structurally less informative than one under `cost-empirical-calibrated`.
- **(c) Substrate-vintage**: the canonical post-Phase-O.0 substrate SHA `317429e4...` is the project's current binding (per CLAUDE.md §"Phase O.10 extension"). Future substrate refreshes (e.g., Databento 2026-H2 pull) will produce new SHAs; the `promising-*` annotation pins to the SHA at evaluation time so cross-substrate-vintage comparisons remain transparent.

**Annotation format**: `promising-{kpi-vector-slug}-{cost-model-slug}-{substrate-sha-prefix-16}` (`# justify:` 16-char prefix aligns with CLAUDE.md substrate-reconciliation-memo convention; 8-char prefix avoided per format-audit FA-1-12 risk of git-style prefix collision on substrate inventory growth). Example: H055 v2 MGC C3 cell at Phase O.10 emission would be annotated `promising-mppm-cost-zero-317429e49ad63674` if it satisfies MPPM CI strictly positive at zero-cost on the post-Phase-O.0 substrate. A future v3 re-emission with cost-realistic operation might emit `not-promising-mppm-cost-conservative-prior-317429e49ad63674` for the same cell — the annotation transparently surfaces the cost-model-conditional reversal.

The annotation lives in the KPI report card §"Methodological-correctness annotations" line per ADR-0014 §3.2 Table 9 + ADR-0017 §3 + ADR-0018 §D-1 grammar. The KPI table column emission is in the §0 header of this ADR §D-1 (a `promising-*` summary column may be added per `P1-ADR-0026-V2-PROMISING-COLUMN`).

**Operator-readable interpretation**: when the operator's 2026-05-19 directive "doubling down on strategies that show promise" is operationalized, the input to the doubling-down decision is the set of cells / arms / hypotheses with at least one `promising-*` annotation under the **current paradigm version's** (KPI-vector, cost-model) pair. The substrate-vintage component allows the operator to filter by "evaluated on the same substrate as the current decision frame" vs "evaluated on an earlier substrate that may not generalize."

**Anti-pattern explicitly forbidden**: bare unconditioned "promising" assertions (e.g., "H062 v2 looks promising" without triple). Such assertions are R1-audit blockers under the new annotation grammar.

## Alternatives considered

### A. Add 2026 sub-window as a row in ADR-0014 Table 1 instead of a §0 header

Rejected. Table 1 is "P/L (realized OOS, $10K starting capital)" per ADR-0014 §3.2 Table 1; injecting a second time-window row conflates the per-symbol-per-arm matrix with the time-slicing dimension. The §0 3-component header is structurally clearer: three rows × symbols-as-columns is the natural format for time-slice × instrument matrices.

### B. Make the 2026 sub-window optional rather than mandatory at v1

Rejected. The operator's 2026-05-19 directive explicitly cites the 2026 sub-window as a canonical KPI component. Optionality would re-create the Phase O.10 / Phase O.13 inconsistency where each KPI card scattered 2026 data at variable positions.

### C. Use the `cost-zero` annotation alone to mark "promising" cells

Rejected. The operator empirically demonstrated across Phase O.3 → Phase O.7 → Phase O.13 that cost-model + substrate-vintage + KPI-vector are jointly necessary qualifiers. Reducing to one qualifier loses the load-bearing condition (e.g., a cell may be promising-MPPM but not promising-terminal-wealth-q05, and the operator's risk tolerance for that asymmetry varies).

### D. Defer the succinctness carveout to a CLAUDE.md edit without an ADR

Rejected. The carveout interacts with multiple project-level mandates (ADR-0014, ADR-0017, ADR-0018, SKILL.md audit-remediate-loop, ReproLog schema). An ADR is the canonical location; a CLAUDE.md edit alone would lack the explicit cross-reference to the mandated-verbose artifact classes.

### E. Strengthen "promising" to a binding promotion gate instead of an annotation

Rejected per ADR-0013 §1 + §2 no-binding-gates philosophy preserved by ADR-0024. The `promising-*` annotation is operator-readable input, not a gate.

## Consequences

### Adopted

- §0 3-component KPI summary header at the top of every KPI report card per §D-1.
- Succinct-communication carveout per §D-2.
- `promising-{kpi-vector-slug}-{cost-model-slug}-{substrate-sha-prefix-16}` annotation grammar per §D-3.

### Trade-offs accepted

- **Reporting verbosity increases.** Each KPI report card gains 3 rows × (n_symbols + 1) cells = e.g., 15 rows for a 4-symbol basket. Justified by the operator's explicit request for at-a-glance 2026 results.
- **Per-symbol substrate-end variance.** NQ has no 2026-onward data; ES has ~6 weeks; MGC/SIL have ~5 months. Component-2 row N(sessions) makes this transparent; the `underpowered-2026-subwindow` annotation surfaces low-N risk.
- **`promising-*` annotation increases citation-pinning surface area.** A future paradigm shift will require re-annotating prior KPI cards or accepting that annotations are point-in-time. Per ADR-0013 §4.1 non-loss, prior annotations stay verbatim; new annotations come in v(N+1) KPI re-emissions per `P1-ADR-0026-PROMISING-RETROACTIVE-CASCADE`.

### Residual risk

- **Component 2 is high-variance for short sub-windows.** N=30-60 sessions per the H055 / H062 / H065 patterns. The operator's previously-acknowledged concern (per the 2026-05-19 risk-anticipation exchange). Mitigated by the `underpowered-2026-subwindow` annotation and the operator-readable `N` column.
- **Component 2 ages.** By 2027 the "2026-onward" framing is stale; the project needs a rolling-window definition or explicit re-pegging cadence. Tracked under `P1-ADR-0026-COMPONENT-2-WINDOW-DEFINITION-ROLLING`.
- **"promising" triple does NOT prevent operator-overruled promotion.** Operator-discretionary promotion per ADR-0013 §5.3 stays in force; the annotation is operator-readable input only. Operator may still double down on a `not-promising-*` cell with explicit `# justify:` decision-log entry per ADR-0013 §1 stage-progression machinery.

### Cascade requirements

- **`P1-ADR-0026-TEMPLATE-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) extended with §0 3-component header preceding the 13-table format.
- **`P1-ADR-0026-CLAUDE-MD-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — CLAUDE.md §"Communication" gains the carveout; §"KPI report card for every strategy" gains the `promising-*` annotation grammar entry + the §0 header reference.
- **`P1-ADR-0026-DECISIONS-README-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — [docs/decisions/README.md](README.md) gains the ADR-0026 entry.
- **`P1-ADR-0026-GLOSSARY-CASCADE`** (non-blocking) — [docs/glossary.md](../glossary.md) gains entries for `promising-*`, `underpowered-2026-subwindow`, `2026-subwindow-no-data`.
- **`P1-ADR-0026-V3-KPI-CASCADE-H050-H052A-H053-H055-H060-H062-H065`** (non-blocking; sequenced per operator priority) — v3 KPI report card re-emissions on the existing 8 emitted cards with the §0 header populated. Per ADR-0013 §4.1 non-loss the prior v1/v2 emissions stay verbatim; v3 lands as new versioned successor.
- **`P1-ADR-0026-PROMISING-RETROACTIVE-CASCADE`** (non-blocking) — retroactive `promising-*` annotation on prior KPI cards where the triple is unambiguously reconstructable from the existing sidecar provenance.
- **`P1-ADR-0026-COMPONENT-2-WINDOW-DEFINITION-ROLLING`** (non-blocking; 2026-09-01 review) — define the rolling-window or re-peg cadence for Component 2 ahead of the 2027 calendar transition. **Automatic fallback**: if not landed by 2026-12-01, the §D-1 Component 2 window-definition automatically converts to most-recent-12-month-rolling with `component-2-window-auto-rebased` annotation on subsequent KPI cards (per F-1-17 R1 audit fix).
- **`P1-ADR-0026-UNDERPOWERED-THRESHOLD-EMPIRICAL`** (non-blocking) — empirical re-calibration of the `n_min_underpowered = 30` default against project-substrate-specific autocorrelation structure (per F-1-7 R1 audit fix; current default anchored to Lo 2002 §III rough rule-of-thumb but futures returns are autocorrelated so n_eff < N).
- **`P1-ADR-0026-SECTION-0-WIN-RATE-CROSS-CHECK`** (non-blocking) — regression test asserting §0 Component 1 + 2 Win-rate cells equal the body Table 5 cells (per F-1-15 R1 audit fix).
- **`P1-ADR-0026-V3-KPI-RERUN-FOR-COMPONENT-3`** (non-blocking) — for KPI cards emitted before 2026-05-18 (i.e., v1/v2 without `per_session_logret_aggregate` sidecar field), Component 3 row requires walk-forward re-run on the new orchestrator code (per F-1-11 R1 audit fix). Wall-clock-significant; sequenced per operator priority.

### BLOCKING follow-ups registered by ADR-0026

| Follow-up | Status | Description |
|---|---|---|
| `P1-ADR-0026-TEMPLATE-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | KPI results-summary template extension |
| `P1-ADR-0026-CLAUDE-MD-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | CLAUDE.md §"Communication" + §"KPI report card for every strategy" updates |
| `P1-ADR-0026-DECISIONS-README-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | ADR index entry |

### Non-blocking follow-ups

| Follow-up | Description |
|---|---|
| `P1-ADR-0026-GLOSSARY-CASCADE` | Glossary entries for new annotations |
| `P1-ADR-0026-V3-KPI-CASCADE-H050-H052A-H053-H055-H060-H062-H065` | Retroactive v3 KPI emission with §0 header on prior cards |
| `P1-ADR-0026-PROMISING-RETROACTIVE-CASCADE` | Retroactive `promising-*` annotation |
| `P1-ADR-0026-COMPONENT-2-WINDOW-DEFINITION-ROLLING` | Rolling-window definition for Component 2 ahead of 2027 |
| `P1-ADR-0026-V2-PROMISING-COLUMN` | Consider adding a `promising-*` column to the §0 3-component header in v2 |
| `P1-ADR-0026-UNDERPOWERED-THRESHOLD-EMPIRICAL` | Calibrate `n_min_underpowered` against substrate autocorrelation structure (per F-1-7) |
| `P1-ADR-0026-SECTION-0-WIN-RATE-CROSS-CHECK` | Regression test asserting §0 Win-rate cells match body Table 5 (per F-1-15) |
| `P1-ADR-0026-V3-KPI-RERUN-FOR-COMPONENT-3` | Walk-forward re-run for pre-2026-05-18 KPI cards to populate Component 3 (per F-1-11) |
| `P1-ADR-0026-V3-KPI-CASCADE-H051-H052B-NO-EMISSION` | Cascade vacuously satisfied for H051 + H052b (no v1/v2 emission predates ADR-0026 adoption); documented for completeness per F-1-19 |
| `P1-CLAUDE-MD-PRACTITIONER-TAG-FORMALIZE` | Add CLAUDE.md §"Practitioner-source-tag" section referenced by ADR-0025/0026/0027 (per FA-1-2; inherited from ADR-0025) |

## References

### Primary peer-reviewed sources

- Goetzmann, W., Ingersoll, J., Spiegel, M., & Welch, I. (2007). Portfolio performance manipulation and manipulation-proof performance measures. *Review of Financial Studies*, 20(5), 1503–1546. [DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025). (MPPM(ρ=1) — Component 1 + 2 + 3 of the §D-1 header use MPPM as the primary inferential metric per ADR-0018 §D-1.)
- Lo, A. W. (2002). The statistics of Sharpe ratios. *Financial Analysts Journal*, 58(4), 36–52. [DOI 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453). (Sharpe-CI minimum-sample analysis — anchor for the `n_min_underpowered = 30` default of the §D-1 `underpowered-2026-subwindow` annotation.)
- Lo, A. W. (2004). The Adaptive Markets Hypothesis: Market efficiency from an evolutionary perspective. *Journal of Portfolio Management*, 30(5), 15–29. [DOI 10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611). (AMH framing — the substrate-vintage qualifier of §D-3 is the operational instantiation of Lo 2004's "regime-conditional efficiency" insight: a strategy's promise is conditional on the regime under which it was evaluated.)

### Project-internal

- [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — §"Frozen pre-registration amendment" + §4.1 non-loss; §3.1.1 Forward 1-year bootstrap convention (Component 3 of §D-1).
- [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — 13-table results-summary format (preserved verbatim; §0 header prepends).
- [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) — primary metric vector (terminal-wealth-q05 in Component 1 + 2 + 3 of §D-1).
- [ADR-0018](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — MPPM(ρ=1) as primary inner-CV fitness (cited in §D-3 KPI-vector qualifier).
- [ADR-0024](ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) — opt-in framing for ADR-0017 §4.2 / §5 / §6 (preserved; reporting changes are orthogonal).
- [ADR-0025](ADR-0025-abandonment-trigger-infrastructure.md) — `cost-{empirical-calibrated, conservative-prior, zero}` annotation (cited in §D-3 cost-model qualifier).
- [ADR-0027](ADR-0027-operational-discipline-bounded-exploration.md) — sibling ADR; operational-discipline counterpart to ADR-0026's reporting-discipline focus.
- [CLAUDE.md](../../CLAUDE.md) §"Communication" + §"KPI report card for every strategy" — receives §D-2 carveout + §D-3 annotation grammar additions.
- [docs/audits/audit_trail_2026-05-19_adr-0026-adr-0027.md](../audits/audit_trail_2026-05-19_adr-0026-adr-0027.md) — this ADR's audit-remediate-loop trail (shared with ADR-0027).

## Empirical justification

The empirical basis is the conjunction of (a) operator 2026-05-18 + 2026-05-19 KPI-review directives explicitly requesting 2026 OOS as a canonical component; (b) Phase O.3 → Phase O.7 → Phase O.13 documented evidence that "promising" assertions un-pinned to the (KPI-vector, cost-model, substrate-vintage) triple are unstable across paradigm versions (C3 super-Kelly +2,690% headline collapsed under cost-realistic to −99.9995%); (c) the operator-acknowledged tension between succinctness directive (formalization #1) and the verbose-by-mandate artifact classes maintained across the Phase O audit-remediate-loop cycle. Each is independent evidence; together they constitute the load-bearing motivation for ADR-0026.

The CLAUDE.md user-global §"Evidence Hierarchy" is preserved unchanged. The §D-3 `promising-*` annotation grammar is structurally consistent with the existing ADR-0025 §D-5 disclosure-annotation grammar (`cost-*`, `kill-switch-*`, `bocd-live-*`) — annotation-driven operator-readable disclosure of evaluation conditions, not binding gates.

ADR-0026 is the canonical reference for the SKIE-Universe project's 2026-05-19+ reporting and communication discipline. It mandates the §0 3-component KPI summary header at the top of every KPI report card, formalizes the succinct-vs-verbose carveout per artifact class, and pins "promising" assertions to the (KPI-vector, cost-model, substrate-vintage) triple to make doubling-down decisions reproducible against the qualifying conditions.
