---
id: ADR-0014
title: Canonical end-of-simulation results-summary tables — KPI report card §3.2 mandate
status: accepted
date: 2026-05-04
deciders: skoir
amends:
  - ADR-0013 §3 (KPI report card canonical structure) — adds new §3.2 subsection "End-of-simulation results summary (operator-readable)" between §3.1 and the existing build/run-history section; preserves §3 + §3.1 + §3.1.1 + §3.1.2 verbatim
  - research/_templates/kpi_report_card_template.md — template will gain a new "End-of-simulation results summary" section block before the existing Methodological-correctness annotations table; deferred to follow-up `P1-ADR-0014-TEMPLATE-CASCADE` (the companion template `research/_templates/kpi_results_summary_template.md` ships in this commit and supplies the inline-able skeleton until the card-template cascade lands)
  - CLAUDE.md "KPI report card for every strategy" — adds reference to ADR-0014 + the canonical 9-table format
preserves_immutability_of:
  - ADR-0013 §1 stage progression model
  - ADR-0013 §2 KPI annotations table
  - ADR-0013 §3.1 (Realized-OOS + Forward-Projection mandate; the new §3.2 is a presentation layer over §3.1's data)
  - ADR-0013 §4 non-loss mandate
  - ADR-0013 §5 NinjaScript-mandate
  - All previously emitted KPI report cards (H053 v1+v2+v3) — those carry no §3.2 section; ADR-0014 is prospective from the next emission forward, with retroactive in-place application to H050 v1 explicitly permitted under §3 F-1-10 cosmetic-edit allowance (the section is a re-presentation of existing KPI values; no new informational content)
---

# ADR-0014 — Canonical end-of-simulation results-summary tables

## Context

Per ADR-0013 §3 the KPI report card is the artifact-of-record at every stage transition. The canonical structure (§3 lines 130-158) lists 7 mandatory sections: methodological-correctness annotations, performance KPIs, deferred-KPI follow-ups, §3.1 Realized-OOS + Forward-Projection block, build/run history, audit-remediate-loop trails, cross-references, versioning, operator review.

Operationally, when an operator reads the KPI report card to inform a stage transition decision (`kpi-report-emitted` → `ninjascript-implemented`; `paper-trade-active` → `live-promoted`), the load-bearing information is distributed across the §"Performance KPIs" mega-table + the §3.1 block's three tables (realized OOS / forward projection / forward max-DD). The H050 v1 emission demonstrated that:

- Performance KPIs are dispersed: T_H050 + LW2008 CI is in one table, annualised Sharpe is in a footnote, max-DD is in §3.1, W/L/Z is in §3.1, SPA p is in a third table.
- Bottom-line interpretation requires the operator to mentally aggregate across ~6 tables.
- Cross-strategy comparison (per `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD`) requires a uniform summary structure that varies in column ordering across hypotheses.

The user 2026-05-04 directive: "These results tables you provided should be canon at the end of each simulation phase" — establishes a project-wide convention that the 9-table consolidated summary used in the H050 v1 mid-emission status report is mandatory at the close of every simulation phase, every KPI report card emission, and every stage-transition operator-review artifact.

## Decision

### §3.2 (new) — End-of-simulation results-summary tables (MANDATORY)

Every KPI report card from 2026-05-04 forward MUST include a §"End-of-simulation results summary" section between the H1 / hypothesis preamble and §"Methodological-correctness annotations" (per ADR-0013 §2 + §2.1). The section consists of **9 mandatory tables + 1 mandatory prose paragraph**:

| # | Table | Required columns |
|---|---|---|
| 1 | **P/L (realized OOS, $10K starting capital)** | symbol \| arm \| end equity \| % change \| OOS bars (or sessions, depending on substrate cadence) \| OOS sessions equivalent |
| 2 | **Drawdown (realized + projected)** | symbol \| arm \| realized max-DD \| proj median DD \| proj q95 DD |
| 3 | **Sharpe — primary inference** | symbol \| SR_arm \| SR_bench \| T_primary (= SR_arm − SR_bench, the primary differential per design.md §1) \| primary-CI [low, high] (LW2008 or equivalent) \| excludes zero \| T_primary annualised. Note: "bench" is whichever sibling-arm or external benchmark serves as the differential reference per the hypothesis's design.md §1 — e.g., H050's SR_bench is the unconditional sibling arm; H053's SR_bench is the AR(1) lag-1 / passive-long bench. R-3 / F-Q-2 (Round-2 audit-remediate-loop 2026-05-04) alignment: column labels harmonised with the template + H050 v1 retroactive application. |
| 4 | **Annualised Sharpe** | symbol \| SR_arm (one column per arm; annualisation factor declared in caveat) |
| 5 | **Win/Loss/Zero counts + win rate** | symbol \| arm \| W \| L \| Z \| Win rate W/(W+L+Z) |
| 6 | **Forward 1-year projection** | symbol \| arm \| Median \| q01 \| q05 \| q95 \| q99 \| P(loss) \| P(double) \| P(<50%) |
| 7 | **Hansen SPA family p-value** | symbol \| T_SPA \| p-value \| n_bootstrap \| Annotation (with mechanical interpretation if degenerate) |
| 8 | **Other KPIs** | KPI name \| symbol values (one column per symbol) — best label cfg, n_folds (realized/expected), max-DD annotation, Sharpe-vs-{passive,unconditional,bench} annotation, cost model id, deferred-KPIs list |
| 9 | **Methodological-correctness annotations (one-line)** | dot-separated list of all ADR-0013 §2 annotations: `leakage-canary-{pass,fail}` · `bss-{...}` · `reliability-{...}` · `repro-log-{...}` · `dsr-{...}` · `post-run-audit-{...}` |

Plus **§"Bottom line"** — a prose paragraph (≤ 8 sentences) stating:

1. The strategy's primary inferential verdict (positive / null / negative) per the binding test statistic from design.md §1
2. The realized + projected $10K equity outcome (operator-readable phrasing)
3. The next mandatory stage transition per ADR-0013 §1 + §5
4. Cross-link to the full report card body (the 9 tables are a SUMMARY; the body retains the canonical detailed presentation per ADR-0013 §3 + §3.1)

### §3.2 — Placement and uniqueness

The §"End-of-simulation results summary" section is placed **immediately after the H1 + preamble, BEFORE §"Methodological-correctness annotations"**. The rationale: an operator opening the report card reads the 9-table summary first; the §3 + §3.1 detailed body provides the full provenance + caveats for the values that appear in the summary.

The 9 tables are a **re-presentation** of values already in the §"Performance KPIs" mega-table + §3.1 block. They MUST NOT introduce new KPI values that don't appear in the body; cross-cell numerical agreement is enforced by the post-run audit gate (per ADR-0013 §7.1) and verified at every audit-remediate-loop trail's R3 verification step.

### §3.2 — Cross-strategy comparability

The 9-table format is the canonical input to `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD` (existing follow-up). When ≥ 2 hypotheses have published KPI report cards, the dashboard aggregates the 9-table summaries across hypotheses by joining on symbol + arm + KPI name. ADR-0014 makes that aggregation column-stable.

### §3.2 — Bottom-line prose

The §"Bottom line" prose paragraph is the operator-promotion-decision-support artifact. It is written in the same neutral, evidence-anchored register as the report card body (per `~/.claude/CLAUDE.md` §Communication "no emojis, filler, hype"). The bottom-line MUST NOT editorialize beyond what the 9 tables support; if the operator's decision is "promote despite negative KPIs", the rationale belongs in `logs/promotions/{run_id}_{HID}_{arm_id}_promotion.md` per ADR-0013 §5.3, not in the bottom-line.

### §3.2 — Retroactive application to H050 v1

H050 KPI report card v1 (emitted 2026-05-04 02:40:59 CDT post-production-walk-forward; commit pending) is amended in-place to add the §"End-of-simulation results summary" section. Per ADR-0013 §3 F-1-10 cosmetic-edit allowance ("Cosmetic corrections (typo, formatting, link rewrite, broken-anchor fix) are permitted in-place via append-mode commit annotation; cosmetic edits do NOT require a version increment because no informational content is lost"), the new section is a re-presentation of existing values — no new KPI numeric value, no new annotation, no methodological-correctness banner change, no build/run history change. The retroactive application does NOT trigger a v2 increment.

H053 KPI report cards v1+v2+v3 (the precedent / reference KPI report cards) are NOT retroactively amended — they were emitted under the pre-ADR-0014 convention. Future H053 v4+ emissions (e.g., post-`P1-H053-COST-EMPIRICAL` calibration; post-paper-trade-evaluated transition) will include the §3.2 section.

## Alternatives considered

### A. Restructure the existing §"Performance KPIs" mega-table to absorb the 9-table format

Rejected. The §"Performance KPIs" table is per-KPI-per-row (one row per KPI like Sharpe-vs-passive, Sortino, etc.); the §3.2 tables are per-arm-per-row (one row per (symbol × arm)). The structural difference is load-bearing for cross-strategy aggregation. Keeping both views is simpler than designing a unified table that satisfies both reading patterns.

### B. Make the 9-table summary OPTIONAL

Rejected. The user 2026-05-04 directive is unambiguous ("should be canon at the end of each simulation phase"). Optional summaries would defeat the cross-strategy comparability goal.

### C. Add the summary tables to the body at the END of the report card (not the beginning)

Rejected. Operator review starts at the top of the report card; placing the summary at the end means the operator scrolls past 200+ lines of detailed tables before reaching the consolidated view. The user-facing artifact-of-record convention is "summary first, detail second".

### D. Defer §3.2 to a separate companion artifact (e.g., `H{NNN}_kpi_results_summary.md`)

Rejected. A separate file fragments the report card. ADR-0013 §3 R-1-8 binds the canonical storage location at `research/01_hypothesis_register/{HID}/{HID}_kpi_report_v{N}.md`; adding a sibling file would split the artifact-of-record across two paths.

## Consequences

### Adopted

- §3.2 (new) mandatory section with 9 tables + bottom-line prose at the top of every KPI report card from 2026-05-04 forward.
- H050 KPI report card v1 retroactively amended in-place.
- H053 v1+v2+v3 NOT retroactively amended (preserved verbatim per ADR-0013 §4.1 non-loss); H053 v4+ will follow ADR-0014.
- New companion template at `research/_templates/kpi_results_summary_template.md` provides the table-only skeleton for stand-alone summary use (e.g., status reports between full report card emissions). Cascade into `research/_templates/kpi_report_card_template.md` (embed the §3.2 skeleton block before the existing Methodological-correctness annotations section) is **deferred to follow-up** `P1-ADR-0014-TEMPLATE-CASCADE` per Round-2 audit-remediate-loop F-Q-1 / R-2 finding (the prior wording "updated with §3.2 skeleton" misrepresented the working-tree state at the ADR-0014 commit; corrected here to disclose the deferral).

### Trade-offs accepted

- **Redundancy at the report-card level**: the 9 tables re-present values from the body. Mitigated by the post-run audit gate enforcing cross-cell numerical agreement; the redundancy is a feature (operator-readable) not a defect.
- **Per-cycle audit cost**: every KPI report card emission now requires verification that §3.2 tables match §"Performance KPIs" + §3.1 body. Mitigated by the audit-remediate-loop pattern (the R3 verification triad already cross-checks these per F-Q-1 / F-Q-2 / F-R-8 verification patterns established in the H050 v1 + H053 Path B audits).

### Residual risk

- Cross-strategy aggregation under `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD` may surface column-shape inconsistencies as more hypotheses ship; tracked under `P1-ADR-0014-DASHBOARD-COLUMN-STABILITY-AUDIT`.
- The 9-table format is calibrated against H053 (daily-cleared) + H050 (HMM-gated multi-bar intraday) archetypes. Future hypotheses with different sizing conventions per ADR-0013 §3.1.1 (long-short pairs H051; first-hour ORB H052a; first-hour 0DTE long-call H052b) may require column extensions; tracked under `P1-ADR-0014-PER-ARCHETYPE-COLUMN-CALIBRATION`.

## References

- [ADR-0013 §3 + §3.1](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — KPI report card canonical structure + Realized-OOS + Forward-Projection mandate; ADR-0014 amends only via the new §3.2 subsection.
- [research/_templates/kpi_report_card_template.md](../../research/_templates/kpi_report_card_template.md) — template; ADR-0014 cascade adds §3.2 skeleton.
- [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) — new companion template (this commit).
- [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md) — first retroactive application of §3.2 (this commit).
- [docs/audits/audit_trail_2026-05-04_adr-0014-canonical-kpi-tables.md](../audits/audit_trail_2026-05-04_adr-0014-canonical-kpi-tables.md) — this ADR's audit-remediate-loop trail.

## Follow-ups

- `P1-ADR-0014-DASHBOARD-COLUMN-STABILITY-AUDIT` — cross-strategy aggregation column-stability audit when ≥ 2 hypotheses publish KPI report cards.
- `P1-ADR-0014-PER-ARCHETYPE-COLUMN-CALIBRATION` — per-archetype column extensions (H051 long-short, H052a/b ORB, H053 daily-cleared, H050 HMM-gated, etc.).
- `P1-ADR-0014-H053-V4-CASCADE` — apply §3.2 to H053's next KPI report card emission (e.g., post-cost-empirical or post-paper-trade-evaluated).
- `P1-ADR-0014-CLAUDE-MD-CASCADE` — full CLAUDE.md update reflecting §3.2 as canonical (this commit lands the minimal reference; full cascade is the follow-up if subsequent ADRs amend the structure).
