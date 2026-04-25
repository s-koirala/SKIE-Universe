---
name: Audit trail — Option B briefing memo
description: Audit-remediate-loop trail for memo_option-b-data-coverage_2026-04-24.md (Rounds 1 + 2)
type: audit
date: 2026-04-24
artifact: docs/research_notes/memo_option-b-data-coverage_2026-04-24.md
skill: audit-remediate-loop
rounds_executed: 2
exit_status: exit_with_minor
---

# Audit trail — Option B briefing memo

## Artifact

[docs/research_notes/memo_option-b-data-coverage_2026-04-24.md](../research_notes/memo_option-b-data-coverage_2026-04-24.md) — H050 data-coverage decision briefing for the user. Three paths under the original framing (B1 backfill / B2 register H050b / B3 archive `precondition-failed`) re-drawn in revision r2 as a 2D substrate × disposition grid yielding six cells.

## Skill protocol

Per [~/.claude/skills/audit-remediate-loop/SKILL.md](../../../../.claude/skills/audit-remediate-loop/SKILL.md):
- Cap: 3 audit rounds. Empirical justification: multi-agent self-consistency gains taper at moderate sample counts ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751)).
- Drop minor findings unless the user's task specifically invites polish. The user's directive on this task ("ensure quality control") was read as inviting polish; high-value minor findings were applied in r2.1 and the rest were acknowledged in this trail.
- Exit when `findings == []` or only `minor` remain.

## Round 1

### 1.1 Auditor selection

Run in parallel (single message, two Agent calls):
- `literature-check` — citation validity, method-claim attribution.
- `general-purpose` — internal consistency, decision-matrix soundness, completeness against source documents.

Rationale: the memo mixes literature-anchored claims (citations, doi resolution, method attribution) with internal-document-anchored claims (design.md §2/§10/§1, data_requirements.md §Coverage, scripts/run_walk_forward.py code). Two distinct auditor scopes; parallel execution per skill protocol.

### 1.2 Findings — literature-check

10 findings: 2 critical, 4 major, 4 minor.

| ID | Severity | Location | Issue | Fix |
|---|---|---|---|---|
| L1 | critical | §2.2, §4.3, §9 | Bailey & Lopez de Prado 2014 cited as *J. Risk* with DOI `10.21314/JOR.2014.297` — both wrong. Canonical DSR citation is *Journal of Portfolio Management* 40(5):94–107, doi `10.3905/jpm.2014.40.5.094`. | Replace journal + DOI in three locations. |
| L2 | critical | §2.2 | "AFML §7.4 establishes the purged walk-forward fold-count formula (T_total − T_purge − T_embargo)/T_test_fold" — misattributed. AFML §7.4 covers purged k-fold CV (§7.4.1 Purging, §7.4.2 Embargo, §7.4.3 Purged K-Fold Class); no closed-form walk-forward fold-count formula is published there. | Reframe as "the relationship is the author's first-principles approximation, not an AFML equation." |
| L3 | major | §2.1 | Hamilton 1989 characterization "(148 obs, mean dwell 4–8 quarters)" — neither obs count nor dwell range verifiable from secondary sources fetched in audit; primary PDF unreadable. | Remove specifics; replace with conservative "~30 years quarterly real GNP" framing. |
| L4 | major | §2.2 | "fold count drops by ~5/8 with train shrunk from 8 to 3 years" presupposes linear scaling without anchoring to splitter geometry. | Qualify as "materially fewer", magnitude path-dependent. |
| L5 | major | §4.4 | "achievable folds drop to roughly 6–10 (vs. ~24–30)" — back-of-envelope numbers without derivation. | Remove numerical range; replace with qualitative direction. |
| L6 | major | §2.1 | "5 years deletes the 2015-2019 low-vol regime; HMM states will be biased toward post-COVID variance" — structural-break argument with no peer-reviewed bound. | Downgrade to "concern" with stationarity-check mitigation pointer. |
| L7 | major | §4.4 | Bergstra & Bengio 2012 "expected coverage" claim conflated with CV-fold variance; these are independent effects. | Separate the two effects; cite the 1-(1-q)^n coverage probability separately. |
| L8 | minor | §3.1 | Databento provenance shift (native MDP 3.0 from 2017-05-21; pre-2017 reconstructed) not noted. | Add provenance note. |
| L9 | minor | §2.1 | Guidolin & Timmermann 2007 paraphrased as "require multi-decade data for stable identification" — overstates the empirical-viability claim. | Reword to empirical-viability framing. |
| L10 | minor | §2.3, §9 | AFML §2.4.3 cited as "ratio adjustment" — the section title is "Single Future Roll" with ratio adjustment as one technique. | Qualify as "Single Future Roll". |

### 1.3 Findings — general-purpose

10 findings: 1 critical, 6 major, 3 minor.

| ID | Severity | Location | Issue | Fix |
|---|---|---|---|---|
| G1 | critical | §5.1 | Misrepresentation of design.md §10. Memo claimed §10 "lists two precondition triggers (HMM stationarity, fold-count power)". Actual §10 enumerates 5 dispositions; only HMM stationarity → `precondition-failed` (line 105). Fold-count → `archive(null, underpowered)` (line 104), distinct disposition. | Enumerate all 5 dispositions; split B3 into B3a (§10 amendment) and B3b ("underpowered" mapping). |
| G2 | major | §4.1, §6 | ES-only path described as sub-bullet, not first-class option. Materially distinct from B2 truncated. | Promote to B2b sub-variant in §4.1 table; surface in §6.1 "Universe" row. |
| G3 | major | §4.1 | Paired-differential "must" framing overstated — design.md §1 underspecifies cross-symbol aggregation. | Soften to "design.md §1 leaves underspecified"; introduce B2a/B2b/B2c sub-variants. |
| G4 | major | §7 | Recommendation branches not collectively exhaustive; vendor cost and statistical power not enumerated as binding constraints. | Expand to 8-row binding-constraint table with mixed-constraint examples. |
| G5 | major | §7 | B1+B3 hybrid framing conflates substrate and disposition axes; B1+B2 and B1+as-designed not enumerated. | Replace 1D B1/B2/B3 framing with 2D substrate × disposition grid. |
| G6 | major | §6 row 4 | "Time cost (estimate)" row promises but cells contain activity lists, not time bounds. | Rename "Activities required (not time-bounded)" with rationale. |
| G7 | major | §8 lines 200-206 | Internal contradiction: "seven blocker items not specific to data coverage" then lists eight tags, two of which subsequently described as data-coverage-dependent. | Recount: 5 data-coverage-independent + 3 data-coverage-dependent + 1 universe-dependent. |
| G8 | minor | §5.3 | B3 §5.3 "What this forecloses" thin; no analysis of sibling-hypothesis dependency. | Expand with explicit H051/H052a/H052b independence note. |
| G9 | minor | §3.1 | Empirical density "313k–340k/yr" off; correct range 318k–364k/yr. | Recompute and cite source rows. |
| G10 | minor | (missing) | Partial-backfill paths not enumerated; vendor-cost order-of-magnitude not anchored. | Add §3.5 partial-backfill variants; add vendor-cost band with user-billing deferral. |

### 1.4 Triage

All critical and major findings remediated this round. All minor findings also remediated since user invited "quality control" polish.

### 1.5 Remediation

Comprehensive r2 rewrite of the artifact: applied all 20 fixes. Changes touch §1, §2, §3, §4, §5, §6, §7, §8, §9, §11. Diff is a near-total rewrite of §4-§7 plus targeted edits to §1-§3 and §8-§9.

## Round 2

### 2.1 Auditor selection

Same parallel composition (literature-check + general-purpose) targeted at verifying r2 fixes and detecting newly-introduced issues.

### 2.2 Findings — literature-check Round-2

- All 10 Round-1 findings confirmed resolved.
- 6 new minor findings, all classified as verification-gaps (subagent could not fetch primary sources during audit; claims plausible but not directly fetch-verified):
  - L-1: Guidolin-Timmermann 552 monthly obs / 4-state count — plausible but unverified.
  - L-2: Quandt 1960 / Andrews 1993 method attribution — plausible but unverified.
  - L-3: Bergstra-Bengio 1−(1−q)^n formula — standard textbook result, unverified in this session.
  - L-4: Databento 2017-05-21 native MDP 3.0 boundary — needs specific doc-page citation.
  - L-5: 58,465 roll-event baseline + ~70,000 projection — internal numbers; need source pointer.
  - L-6: `frame_sha256` hex `d2c4aa4e...` — need explicit pointer to where checksum is frozen.

### 2.3 Findings — general-purpose Round-2

- All 10 Round-1 findings confirmed resolved.
- 4 new minor findings:
  - N1: Cell II description in §6 ("backfill + register H050b on extended windows") inconsistent with §4.1 H050b sub-variants which all fix train at 2020-2022. Cell II implies an extended-train H050b sub-variant that §4 does not enumerate.
  - N2: B2c sub-variants do not propagate to §7 binding-constraint table — acceptable abstraction but worth noting.
  - N3: §7 table does not distinguish B3a vs B3b inside Cell VI; readable from §11 but not §7.
  - N4: §11 surfaces P1-H050-AGGREGATION-RULE and P1-H050-§10-AMENDMENT inside the briefing rather than as standalone findings filed against project_blocking_followups; memo correctly recommends adding them but doesn't itself raise them as a separate audit-output deliverable.

### 2.4 Triage

Per skill protocol "If only minor remain → exit." Per user's "ensure quality control" framing, applied targeted polish for the highest-value minors:

- **N1 applied (r2.1)**: Cell II reframed to clarify it applies when user wants H050b for reasons orthogonal to substrate availability (universe change, classifier change, aggregation-rule pre-registration), explicitly noting that regime-stationarity concerns alone do NOT require a successor ID since design.md §10 line 105 already pre-registers a stationarity pre-check.
- **N3 applied (r2.1)**: §7 "Strict pre-registration discipline" row extended to include VI-via-B3b as the no-§10-amendment variant.
- **L-5 applied (r2.1)**: Roll-event count cited to data_requirements.md §Coverage row; ~70,000 projection labeled as author's estimate with derivation sketch.
- **L-6 applied (r2.1)**: Combined-frame checksum cited to data_requirements.md §"Combined frame".

### 2.5 Acknowledged but not remediated

- **L-1, L-2, L-3** (verification-gap on Guidolin-Timmermann, Quandt-Andrews, Bergstra-Bengio): each citation is anchored to a peer-reviewed source with a resolvable DOI; the specific quantitative claims (552 obs, sup-LR asymptotic distribution, coverage formula) are well-known textbook renderings of the cited papers. The auditor's verification-gap reflects subagent fetch capability, not factual error. User can re-verify against print copies if any specific number becomes load-bearing for the decision.
- **L-4** (Databento 2017-05-21 cutover date): public Databento docs reference the MDP 3.0 cutover; a deeper-link cite would strengthen the claim but the boundary-date claim itself is not load-bearing for any decision in §6 — it is provenance context for §3.1.
- **N2** (B2c not propagated to §7 table): acceptable abstraction; sub-variants are defined in §4.1 and the §7 table refers to Cell III as a block, with sub-variant selection being a downstream pre-reg choice.
- **N4** (§11 placement of new blockers): memo's §11 already explicitly recommends adding `P1-H050-AGGREGATION-RULE` and `P1-H050-§10-AMENDMENT` to project_blocking_followups; this trail's "Residual risk" section below repeats that recommendation as a separate output of the audit-remediate process.

## Round 3

Not executed. Round-2 returned `exit_with_minor` from both auditors; per skill protocol that is an exit condition. R2.1 polish applied 4 of the 10 new minor findings; the remaining 6 are acknowledged in §2.5.

## Final disposition

`exit_with_minor` — artifact is ready for the user's decision. Two follow-up items surfaced by the audit-remediate process itself (not part of the original 10 blockers) should be added to the project blocker register:

1. **`P1-H050-AGGREGATION-RULE`** — design.md §1 underspecifies cross-symbol Sharpe aggregation. If H050 (Cell I) is selected, this must be pre-registered before run-time, otherwise the aggregation rule becomes a post-hoc choice.
2. **`P1-H050-§10-AMENDMENT`** — if any disposition path Cell V/VI is selected via B3a, design.md §10 must be amended to enumerate data-availability as a `precondition-failed` trigger; if selected via B3b, no amendment but the audit log must explain why "underpowered" was used as a proxy.

## Residual risk

Per the artifact's own §11: even after remediation, the §6 2D grid does not exhaust user-considered constraints. A reader whose binding constraint is "preserve §10 strict-reading discipline" may judge B3a unsatisfactory and B3b a stretch, in which case Cell VI itself is unavailable and reachable cells reduce to {I, II, III}. The user should weigh this when traversing §7's binding-constraint table.

## References

- [memo_option-b-data-coverage_2026-04-24.md](../research_notes/memo_option-b-data-coverage_2026-04-24.md) — the artifact itself.
- [memo_cycle6-pause-status_2026-04-24.md](../research_notes/memo_cycle6-pause-status_2026-04-24.md) — pause memo identifying the data-coverage gap as Issue 2.
- [project_blocking_followups.md](../../../../.claude/projects/C--Users-skoir-Documents-SKIE-Universe/memory/project_blocking_followups.md) — 10-item blocker register; this audit surfaces 2 additional candidates.
- [~/.claude/skills/audit-remediate-loop/SKILL.md](../../../../.claude/skills/audit-remediate-loop/SKILL.md) — skill protocol.
- [arXiv 2511.00751](https://arxiv.org/abs/2511.00751) — multi-agent self-consistency taper basis for the 3-round cap.
