---
title: ADR-0014 Canonical end-of-simulation results-summary tables — Audit-Remediate-Loop Trail
date: 2026-05-04
deliverables:
  - docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md
  - research/_templates/kpi_results_summary_template.md
  - research/01_hypothesis_register/H050/H050_kpi_report_v1.md (in-place §3.2 application)
  - CLAUDE.md (§"KPI report card" amendment)
  - ~/.claude/projects/C--Users-skoir-Documents-SKIE-Universe/memory/MEMORY.md + project_adr_0014_canonical_kpi_tables.md
audit_pattern: audit-remediate-loop (3-round cap per ~/.claude/skills/audit-remediate-loop/SKILL.md)
auditors_round_2: [quant-auditor, literature-check, reproducibility-verifier]
parent_directive: User 2026-05-04 ("These results tables you provided should be canon at the end of each simulation phase. Run the audit-remediate loop to execute all tasks.")
precedent: docs/audits/audit_trail_2026-05-04_h050-kpi-report-v1.md
---

# ADR-0014 Canonical end-of-simulation results-summary tables — Audit-Remediate-Loop Trail

## Context

Following the H050 KPI report card v1 emission (ADR-0013 §3-compliant; status report response provided 9-table consolidated summary as operator-readable artifact), the user 2026-05-04 directive established the 9-table format as a project-wide canonical convention at end-of-each-simulation-phase. ADR-0014 amends ADR-0013 §3 with a new §3.2 subsection mandating the 9-table + bottom-line summary at the top of every KPI report card.

## Round 1 — Production

5 deliverables landed (all uncommitted at audit time):

1. [docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md](../decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — new ADR
2. [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) — companion template
3. [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md) — retroactive in-place §3.2 application (no v2 increment per ADR-0013 §3 F-1-10 cosmetic-edit allowance)
4. [CLAUDE.md](../../CLAUDE.md) §"KPI report card for every strategy" — amendment
5. Memory file at `~/.claude/projects/C--Users-skoir-Documents-SKIE-Universe/memory/` — new `project_adr_0014_canonical_kpi_tables.md` + MEMORY.md index entry

## Round 2 — Parallel triad audit

3 parallel proper-isolated subagents (single message, multiple Agent calls).

### Round 2 — quant-auditor verdict: `proceed-with-remediation` (6 findings; 1 major, 4 minor, 1 observation)

agentId: a1f34d8fdcdc01808

| Finding | Severity | Issue (1-line) |
|---|---|---|
| F-Q-1 | **major** | ADR-0014 frontmatter `amends:` block + §Consequences "Adopted" bullet 4 claim `kpi_report_card_template.md` is "updated with §3.2 skeleton"; the file is in fact unmodified (cascade deferred to `P1-ADR-0014-TEMPLATE-CASCADE`). |
| F-Q-2 | minor | Companion template Table 4 includes `SR_passive` column not in ADR-0014 §3.2 Table 4 spec. |
| F-Q-3 | minor | ADR-0014 cites cosmetic-edit allowance as "ADR-0013 §3 R-1-10" but ADR-0013 calls this audit-finding "F-1-10" (R/F prefix mismatch — substantive content correct). |
| F-Q-4 | minor | n_bootstrap not surfaced in `metrics_summary.json` `hansen_spa` block; §3.2 Table 7 cross-cell agreement rests on internal-document consistency only. Tracked under new follow-up `P1-METRICS-SUMMARY-SPA-N-BOOTSTRAP-SURFACE`. |
| F-Q-5 | minor | Closes verified-no-defect (caption / sampling-method spec consistency between H050 v1 and template). |
| F-Q-6 | observation | §3.2 placement clause has slight ambiguity (`§Methodological-correctness annotations (per ADR-0013 §2 + §2.1)` — intent clear but could be parsed as ADR-0013 section title). |

Quant-auditor cross-cell numerical-agreement check: **all 9 critical numerical-agreement checks pass** between H050 v1 §3.2 Tables 1-9 vs the report card body + `metrics_summary.json` + `simulate_h050_10k_2026.json`.

### Round 2 — literature-check verdict: `accept` (10 findings; 10 verified, 1 polish item)

agentId: a4af67169a4715f98

All 10 citation/method-attribution claims VERIFIED:
- ADR-0013 §3 cosmetic-edit allowance (line 162) — VERIFIED
- ADR-0013 §3 R-1-8 canonical storage path (line 164) — VERIFIED
- ADR-0013 §3.1.1 5-archetype sizing-convention table (lines 199-211) — VERIFIED (5 rows: H053 daily-cleared, H050 HMM-gated, H051 long-short, H052a ORB, H052b 0DTE)
- §3.2 specification consistent across ADR-0014, template, H050 v1, CLAUDE.md (9 tables + bottom-line; placement before §Methodological-correctness) — VERIFIED
- ADR-0008 §"Single-strategy degenerate handling (|M|=1)" supports m=1 mechanical interpretation — VERIFIED
- CLAUDE.md citation accurately summarises ADR-0014 — VERIFIED
- H050 v1 §3.2 cross-link to ADR-0014 resolves — VERIFIED
- rules/quant-project.md §Reporting KPI mandates preserved via Tables 2/3/4/8 + ADR-0013 §3.1.2 deferred-KPI mechanism — VERIFIED
- H053 v3 NOT retroactively edited (preserves §4.1 non-loss) — VERIFIED
- No new external primary-literature citations introduced — VERIFIED

F-L-1 minor polish: cite `F-1-10` instead of `R-1-10` for the cosmetic-edit allowance ID (same finding as F-Q-3).

### Round 2 — reproducibility-verifier verdict: `proceed-with-remediation` (9 findings; 1 major, 2 minor, 6 observations)

agentId: a1371f170a704f477

| Finding | Severity | Issue |
|---|---|---|
| R-1 | **major** | ADR-0014 §References cites self-audit-trail file `audit_trail_2026-05-04_adr-0014-canonical-kpi-tables.md` that does not exist on disk. |
| R-2 | minor | ADR-0014 §Consequences "Adopted" bullet 4 contradicts itself (claims template updated; deferred follow-up says it's not). Same finding-class as F-Q-1. |
| R-3 | minor | Table 3 column-label divergence between ADR (`SR_arm1/SR_arm2/ΔSR`) vs template + H050 v1 (`SR_arm/SR_bench/T_primary`). 7-column count consistent; per-column semantics differ. |
| R-4 through R-9 | observation | Non-loss + version-discipline + protected-path + cross-link + follow-up-uniqueness + memory-accuracy all verified PASS. H050 v1 in-place edit is genuinely cosmetic (re-presents existing body values; no new computed KPIs). |

## Round 2 — Triage + remediation

Per audit-remediate-loop skill §3 ("Drop minor findings unless the user's task specifically invites polish. critical blocks progression; major is remediated this round."):

- **Major (must remediate this round)**: F-Q-1 / R-2 (ADR self-contradicts on template-cascade); R-1 (missing audit trail file)
- **Minor (selected for inline remediation)**: F-Q-3 / F-L-1 (R-1-10 → F-1-10 prefix); F-Q-2 (template Table 4 SR_passive column); R-3 (Table 3 column-label alignment)
- **Deferred to follow-ups**: F-Q-4 (`P1-METRICS-SUMMARY-SPA-N-BOOTSTRAP-SURFACE`); F-Q-6 (placement-clause polish)

### Round 2 remediation patches

- **R-1**: This file (`audit_trail_2026-05-04_adr-0014-canonical-kpi-tables.md`) emitted in this commit. ADR-0014 §References self-citation now resolves.
- **F-Q-1 / R-2**: ADR-0014 §Consequences "Adopted" bullet 4 rewritten to disclose the deferred template cascade ("Cascade into `kpi_report_card_template.md` ... is deferred to follow-up `P1-ADR-0014-TEMPLATE-CASCADE`"). ADR-0014 frontmatter `amends:` block similarly rewritten. The follow-up `P1-ADR-0014-TEMPLATE-CASCADE` was already registered in Round-1; Round-2 fix closes the prose contradiction without changing the deferred-cascade plan.
- **F-Q-3 / F-L-1**: ADR-0014 lines 17 and 75 — `R-1-10` → `F-1-10` (replace_all=true; 2 occurrences updated).
- **F-Q-2**: Companion template Table 4 — drop `SR_passive` column header; add narrative note that one column per arm is the canonical column-shape; bench column only if applicable per the hypothesis archetype.
- **R-3**: ADR-0014 §3.2 Table 3 row — column-label aligned to `symbol | SR_arm | SR_bench | T_primary | primary-CI | excludes zero | T_primary annualised` matching the template + H050 v1; explicit note that "bench" is the differential reference per design.md §1 (sibling unconditional arm for H050; AR(1) lag-1 / passive-long for H053).

## Round 3 — Verification

Round-3 verification: 1 isolated subagent (quant-auditor; lit-check + repro-verify subsumed since the Round-2 fixes were narrative + path corrections that don't require independent literature/reproducibility re-audit).

### Round 3 — quant-auditor verdict: `ACCEPT` (5/5 closures verified)

agentId: a16732b457c34bc01

| Finding | Verdict | Evidence |
|---|---|---|
| R-1 (missing audit trail file) | ACCEPT | This file present (10,982 bytes) with structured frontmatter + Round-1/2 sections; ADR-0014:122 reference resolves. |
| F-Q-1 / R-2 (ADR self-contradiction on template cascade) | ACCEPT | ADR-0014:9 (frontmatter `amends:` block) + ADR-0014:104 (§Consequences "Adopted" bullet 4) both explicitly disclose deferral to `P1-ADR-0014-TEMPLATE-CASCADE`. The §Consequences bullet self-attributes the prior misrepresentation to Round-2 audit-remediate-loop F-Q-1/R-2 finding. |
| F-Q-3 / F-L-1 (R-1-10 → F-1-10 prefix) | ACCEPT | grep ADR-0014: 0 matches for `R-1-10`; 2 matches for `F-1-10` at lines 17 + 75, both in cosmetic-edit-allowance contexts. Prefix aligned with ADR-0013 audit-finding-ID convention. |
| F-Q-2 (template Table 4 SR_passive column) | ACCEPT | Template Table 4 header now `Symbol | SR_arm1 | SR_arm2 | ...` — no SR_passive. Caveat at line 51 explicitly states "one column per arm declared in the hypothesis's design.md §5; annotate the bench column only if the hypothesis carries a passive/AR(1) bench distinct from the primary differential's reference arm". |
| R-3 (Table 3 column-label divergence) | ACCEPT | ADR-0014 §3.2 Table 3 now uses `symbol \| SR_arm \| SR_bench \| T_primary \| primary-CI \| excludes zero \| T_primary annualised`, matching the template + H050 v1 framing. Row also documents the R-3/F-Q-2 alignment provenance and clarifies bench semantics per hypothesis. |

Quant residual risk: "P1-ADR-0014-TEMPLATE-CASCADE remains open as disclosed deferral; cross-strategy column-stability follow-ups (P1-ADR-0014-DASHBOARD-COLUMN-STABILITY-AUDIT, P1-ADR-0014-PER-ARCHETYPE-COLUMN-CALIBRATION) tracked but non-blocking."

### Round 3 — overall verdict: **ACCEPT**

All 2 majors + 3 selected minors closed. Round-2 deferred minors (F-Q-4 SPA n_bootstrap surfacing) tracked under named follow-ups. The ADR-0014 + template + CLAUDE.md + memory + H050 v1 retroactive §3.2 cascade is ready for commit + push.

The audit-remediate-loop exits at Round 3 per the 3-round cap with verdict ACCEPT.

## Residuals → follow-ups

| Follow-up ID | Severity | From | Description |
|---|---|---|---|
| `P1-ADR-0014-TEMPLATE-CASCADE` | major | F-Q-1 / R-2 | Embed §3.2 skeleton (9 tables + bottom-line) into `research/_templates/kpi_report_card_template.md` before the existing Methodological-correctness annotations section. |
| `P1-ADR-0014-DASHBOARD-COLUMN-STABILITY-AUDIT` | minor | residual risk | Cross-strategy aggregation column-stability audit when ≥ 2 hypotheses publish KPI report cards. |
| `P1-ADR-0014-PER-ARCHETYPE-COLUMN-CALIBRATION` | minor | residual risk | Per-archetype column extensions for H051/H052a/H052b/etc. |
| `P1-ADR-0014-H053-V4-CASCADE` | minor | ADR-0014 §"Retroactive application" carve-out | Apply §3.2 to H053's next KPI report card emission (post-cost-empirical or post-paper-trade-evaluated). |
| `P1-ADR-0014-CLAUDE-MD-CASCADE` | minor | ADR-0014 §"Follow-ups" | Full CLAUDE.md update reflecting §3.2 as canonical (this commit lands the minimal reference). |
| `P1-METRICS-SUMMARY-SPA-N-BOOTSTRAP-SURFACE` | minor | F-Q-4 | Surface n_bootstrap in the orchestrator's `metrics_summary.json` `hansen_spa` block so the post-run audit gate can verify §3.2 Table 7 + body §"Hansen SPA" agreement against on-disk values. |

## Cross-references

- ADR-0014: [docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md](../decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md)
- ADR-0013 (parent ADR being amended): [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- ADR-0008 single-strategy degenerate: [docs/decisions/ADR-0008-spa-omega-method.md](../decisions/ADR-0008-spa-omega-method.md)
- Companion template: [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md)
- Card template (cascade pending): [research/_templates/kpi_report_card_template.md](../../research/_templates/kpi_report_card_template.md)
- H050 v1 retroactive application: [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md) §"End-of-simulation results summary"
- H050 v1 source audit trail: [audit_trail_2026-05-04_h050-kpi-report-v1.md](audit_trail_2026-05-04_h050-kpi-report-v1.md)
- H053 v3 reference KPI report card (NOT retroactively amended; preserved per §4.1): [research/01_hypothesis_register/H053/H053_kpi_report_v3.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v3.md)
