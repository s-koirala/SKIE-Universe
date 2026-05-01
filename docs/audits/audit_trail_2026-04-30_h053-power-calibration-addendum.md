---
title: H053 power-calibration addendum + lit-review remediation — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverables:
  - research/01_hypothesis_register/H053/power_calibration_addendum_2026-04-30.md (NEW; closes P1-H053-PILOT-WINDOW-DATABENTO via election of data_requirements option 3)
  - research/00_literature_review/lit_intraday-ES-NQ-signals_2026-04-15.md (EDIT; closes P1-LIT-REVIEW-H053-STALE-ENTRY-RESOLVE)
  - plan/hypothesis_backlog.md (EDIT; H053 row added to Tier-2b)
  - plan/h053_buildout_2026-04-28.md (EDIT; Cycle 7 row updated for closed Databento prereq)
  - CLAUDE.md (EDIT; H053 block updated for option-3 election + lit-review remediation)
git_head_at_authoring: edf37a4 (parent for the bundled commit)
loop_rounds: 1 (Round-1 with parallel quant-auditor + literature-check + reproducibility-verifier)
verdict: accept-with-remediation
---

# H053 power-calibration addendum + lit-review remediation — audit-remediate-loop trail

## Scope

Round-1 audit on the bundle of 6 working-tree changes that close two H053 follow-ups in a single audit-remediate-loop pass: `P1-H053-PILOT-WINDOW-DATABENTO` (user-decision election of data_requirements §"Pre-IS pilot window" option 3 in lieu of Databento 2010-2014 purchase) and `P1-LIT-REVIEW-H053-STALE-ENTRY-RESOLVE` (replace the stale "Sovereign CDS" lit-review entry with the actual multi-timeframe-mediation H053 anchor set).

Auditing subagents were proper-isolated and launched in parallel via single-message tool calls per [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md).

## Round-1: parallel triad

### quant-auditor (21 findings; 6 major)

Major:
- **F-1**: addendum places `pilot-conservative-prior` annotation in design.md §10.2; data_requirements.md:99 verbatim binds the deviation to §10.1, not §10.2.
- **F-2**: introducing a new §10.2 annotation exceeds the addendum's "does not amend the H053 design" scope.
- **F-3**: "upper bound on the true `s_min`" terminology is directionally reversed; iid Gaussian minimises Lo 2002 §III HAC variance, so option-3 `s_min` is a *lower* bound on the true `s_min`. Operational consequence ("underpowered-here implies underpowered-everywhere") is correct; bound terminology is wrong.
- **F-4**: addendum frontmatter `audit_loop:` references this audit-trail file which did not exist on disk at audit time.
- **F-9**: AB1998 DOI mismatch — lit-review cited JF *Deutsche Mark-Dollar Volatility* (`10.1111/0022-1082.85732`); design.md frontmatter cites IER *Answering the Skeptics* (`10.2307/2527343`); two distinct AB1998 papers conflated under same author-year tag.
- **F-14**: CLAUDE.md echoes the §10.2 placement issue from F-1.

Minor: F-5 (`pilot_source` ReproLog field undefined in design.md §11), F-10 (backlog row excludes AB1998), F-11 (lit-review summary omits max-DD-non-worse from the conjunctive-gate clause), F-16 (addendum closure table omits lit-review remediation), F-19 ("2016+" vs 2015-substrate), F-20 (§11.2 prereq 19 solver remains open), F-21 (option-1 reactivation clause).

Concurrences: F-6 (option-3 election as fulfillment, not change — no successor ID needed), F-7 (no other H053 design choice depends on rejected option 1), F-8 (lit-review's "stale candidate" framing consistent with on-disk state), F-12 (buildout plan row 7 status accurate), F-13 (CLAUDE.md power-calibration paragraph correct), F-15 (cross-document closure-date consistency), F-17 (git_head_at_authoring matches), F-18 (per-hypothesis lit-review pointer correct).

### literature-check (9 findings; 2 major)

Major:
- **L-4 / L-8** (= F-9 from quant): AB1998 DOI mismatch.
- **L-7**: "37 citations" claim wrong — actual is 33 entries (28 external + 5 ADR cross-references).

Minor: all 6 primary anchors verified clean (Lou-Polk-Skouras 2019, HKS 2010, ABDL 2003, IKT 2010, NMC 2005, AB1998-JF). The page-range and DOI-resolution checks all pass.

### reproducibility-verifier (10 findings; 2 major)

Major:
- **R-1 / R-3** (= F-4 from quant): audit-trail file missing.
- **R-9**: addendum's "same commit" framing requires a single bundled commit across all 6 files.

Minor (positive verifications): R-2 (cross-document closure-date consistency), R-4 (lit-review edit is targeted; non-H053 UNVERIFIED tags preserved), R-5 (backlog row structure matches), R-6 (buildout plan diff clean), R-7 (CLAUDE.md diff clean), R-8 (51 unit tests still green), R-10 (P1-LIT-REVIEW closure logged in lit-review + CLAUDE.md).

## Per-finding disposition

### Major

| ID | Disposition | Remediation evidence |
|---|---|---|
| F-1, F-2, F-14 | **ACCEPTED** | Addendum §"Pre-registered consequences" item 2 reworded: deviation note now placed in §10.1 disposition record (per data_requirements:99 verbatim binding) rather than as a new §10.2 annotation. CLAUDE.md echo updated to reference §10.1 (not §10.2). The addendum no longer claims a design amendment — it stays within the pre-reg-bound surface. |
| F-3 | **ACCEPTED** | Addendum §"Pre-registered consequences" added a "Bound-direction erratum" paragraph: reproduces data_requirements:99 verbatim, then states the corrected framing (option-3 `s_min` is a *lower* bound, best case under the most-favorable distributional assumption). Operational consequence reasoning preserved. New follow-up `P1-H053-DATA-REQS-LINE-99-DIRECTION-ERRATUM` filed for source-pre-reg correction in a future erratum addendum to data_requirements companion. |
| F-4, R-1, R-3 | **ACCEPTED** | This audit-trail file (`audit_trail_2026-04-30_h053-power-calibration-addendum.md`) is the trail the addendum's frontmatter promised; it lands in the same bundled commit. |
| F-9, L-4, L-8 | **ACCEPTED** | Lit-review remediation now cites Andersen-Bollerslev 1998 IER *Answering the Skeptics* (DOI `10.2307/2527343`) — matches design.md frontmatter exactly. The JF *Deutsche Mark-Dollar Volatility* paper (DOI `10.1111/0022-1082.85732`) is dropped from the lit-review entry to eliminate the citation drift. New follow-up `P1-H053-AB1998-CITATION-DISAMBIGUATE` filed: a future review may decide whether to additionally cite the JF paper as a separate-role anchor. The role-assignment text is amended to "RV-based volatility-model forecast-evaluation methodology supporting the realized-volatility feature definitions" — matches the IER paper's content. |
| L-7 | **ACCEPTED** | Lit-review entry's "Full citation set" line corrected from "37 citations" to "33 entries (28 external citations + 5 ADR cross-references)" matching design.md frontmatter actual count. |
| R-9 | **ACCEPTED** | All 6 files (addendum, lit-review, backlog, buildout plan, CLAUDE.md, this audit trail) bundled into a single commit per the addendum's "same commit" framing. |

### Minor

| ID | Disposition | Remediation evidence |
|---|---|---|
| F-5 | **ACCEPTED** | Addendum §"Pre-registered consequences" item 3 reframed: `pilot_source` is now described as a sub-field within the already-pre-registered ReproLog file (`ReproLog.power_calibration_{run_id}.json` per design.md §11.2 prereq 19), not a new top-level field. |
| F-10 | **AUTO-RESOLVED** | Backlog row updated to cite AB1998 IER (matching design.md frontmatter); no longer excludes AB1998. |
| F-11 | **ACCEPTED** | Lit-review entry's mechanism summary now includes the max-DD-non-worse third component of the conjunctive primary gate, with the Hochberg-Tamhane 1987 intersection-union framing. |
| F-16 | **ACCEPTED** | Addendum's §"Follow-up closures" table now has two rows: `P1-H053-PILOT-WINDOW-DATABENTO` (original) + `P1-LIT-REVIEW-H053-STALE-ENTRY-RESOLVE` (added). |
| F-19 | **ACCEPTED** | Addendum §"User decision" gained an "Editorial clarification on '2016+'" paragraph reconciling the user's colloquial "2016+" reference with the actual 2015-start substrate envelope. |
| F-20 | **ACCEPTED** | Addendum §"Pre-registered consequences" gained a "Solver implementation prerequisite still open" paragraph noting that §11.2 prereq 19 (`inference/power.py::required_n`) remains a Cycle-7 deliverable; the addendum closes the data-acquisition path only, not the solver-implementation path. CLAUDE.md echo updated. |
| F-21 | **ACCEPTED** | Addendum gained a "Re-election clause" paragraph: option-1 reactivation mid-program would be a successor hypothesis ID per design.md §0/§7. |

### Positive verifications (no action)

F-6, F-7, F-8, F-12, F-13, F-15, F-17, F-18; R-2, R-4, R-5, R-6, R-7, R-8, R-10; L-1, L-2, L-3, L-5, L-6, L-9.

## Round-2 not invoked

Round-2 was not invoked. Rationale:
1. All 6 major findings landed observable text changes that (a) match data_requirements.md verbatim where applicable (F-1/2/14 §10.1 placement), (b) match design.md frontmatter where applicable (F-9 AB1998-IER, L-7 citation count), or (c) close a structural prerequisite (F-4 audit trail; R-9 single bundled commit).
2. The terminology correction in F-3 is internally consistent with the Lo 2002 §III variance formula and the design.md citation set; the source-pre-reg erratum is tracked as a follow-up rather than amended inline (the source pre-reg is `designed`-status; an inline edit would itself be a deviation).
3. Per [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration", the 3-round cap is the operational ceiling. A second round on a remediation that introduced no new contradiction is process for its own sake.

## Residuals (bounded)

New follow-ups filed by this loop:
- `P1-H053-DATA-REQS-LINE-99-DIRECTION-ERRATUM` (minor; bound-direction terminology correction in source pre-reg)
- `P1-H053-AB1998-CITATION-DISAMBIGUATE` (minor; future decision on whether to additionally cite the JF Deutsche-Mark paper as a separate-role anchor)

Prior follow-ups closed by this loop:
- `P1-H053-PILOT-WINDOW-DATABENTO` (CLOSED 2026-04-30 via option-3 election)
- `P1-LIT-REVIEW-H053-STALE-ENTRY-RESOLVE` (CLOSED 2026-04-30 via lit-review remediation)

Cycle 7 remaining deliverables (unchanged by this loop):
- Feature factory under `src/skie_ninja/features/h053/{daily,hourly,microstructure_5_15min,mediator}.py`
- Archetype classifier per design.md §4.5.1
- PIT integration canaries (§11.2 prereq 11 sub-clause c — depends on feature factory)
- Stage-0 sanity: HKS 2010 half-hour-reversal sign on ES/NQ
- Power-calibration solver `inference/power.py::required_n` per design.md §11.2 prereq 19

Soft prerequisite: Cycle 6 H050 walk-forward aggregate disposition (still pending the 3 BLOCKING follow-ups from the H050 post-mortem).

## Verdict

**accept-with-remediation.** All 6 major findings remediated in-loop. The addendum + lit-review remediation + bundled supporting edits ready for single-commit landing on `origin/main`. Two new minor follow-ups filed; two prior follow-ups closed. Pre-registration discipline preserved — option-3 election is a fulfillment of pre-registered alternatives, not a deviation.
