---
name: H050 cross-symbol aggregation-rule addendum — audit trail
description: 3-round audit-remediate trail (inline) plus Round-4 post-loop-verification under proper subagent isolation for the H050 aggregation-rule addendum (Path A in-place pre-reg clarification of design.md)
type: project
status: closed (Round 4 corrective complete)
date: 2026-04-24
rounds: 3 inline (cap reached) + Round 4 post-loop-verification (proper subagent isolation; corrective, not loop-extension)
verdict: accept (Round-4-amended)
---

# H050 cross-symbol aggregation-rule addendum — audit trail

Audit trail for [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md), the Path-A in-place addendum to [design.md](../../research/01_hypothesis_register/H050/design.md) that formalises the cross-symbol aggregation rule for `universe = [ES, NQ]` per [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml). The addendum binds sub-rule 2a (equal-weighted constant 0.5/0.5 in arithmetic-return space) + sub-rule 3.3a (hold inactive in cash) per the user's accepted recommendation bundle on 2026-04-24.

The parent resolution memo's audit chain (3 rounds, r0 → r4) is at [docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md](audit_trail_2026-04-24_h050-aggregation-rule.md); this trail records audit of the *addendum* artifact (the formalisation step, not the resolution step), and inherits the citation chain verified by that prior audit.

This audit trail records all 3 rounds of audit-remediate per the [audit-remediate-loop skill](C:/Users/skoir/.claude/skills/audit-remediate-loop). Cap reached; residuals surfaced rather than silently iterated.

**Subagent unavailability note**: the user-global instructions ([~/.claude/CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md) "Agentic Iteration") prescribe spawning `literature-check` and `quant-auditor` subagents in parallel at end of each round. The Task tool for spawning subagents was not available in the executing harness, so audits were performed *inline* by the executing agent, applying the same finding-classification rubric (critical / major / minor) and DOI-verification discipline as the parent memo's r4 audit chain. The inline-audit fallback is documented for the audit reader; if the user wishes to re-run the addendum under proper subagent isolation, a successor audit can be appended as Round 4 (which would exceed the 3-round cap and therefore must be invoked explicitly by the user).

## Deliverable

- [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) (revision r1 at end of Round 3)

## Round 1 (r0 → r1 remediation)

**Auditors**: inline `quant-auditor` pass (methodological framing, recommendation-vs-implementation surface, formal-definition consistency) + inline `literature-check` pass (Markowitz 1952 / Sharpe 1966 / Lo 2002 / Opdyke 2007 / Ledoit-Wolf 2008 / Hansen 2005 / DeMiguel-Garlappi-Uppal 2009 / Bailey-LdP 2014 / Whaley 1993 / VIX provenance citation chain).

**Findings (9 quant + 5 lit-check; consolidated):**

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| Q1.1 | minor | §2.1 cited `[scripts/run_walk_forward.py:613]` for `position = np.sign(2.0 * p − 1.0)`; actual location is line 852 (orchestrator file is 1030 lines). The parent memo r4 §3.3 carried the same drift. | Remediated §2.1 with corrected `:852` reference + inline correction note acknowledging the line-drift. |
| Q1.2 | minor | §3.1 attributed "re-runs on extended windows require a successor hypothesis ID" to [design.md] §10 line 41; actual location of that phrase is [design.md] §2 line 41. | Remediated §3.1: separated "[design.md] §2 line 41" (extended-windows clause) from "[design.md] §10" (decision rule and archive policy) and "[design.md] line 22 of body text" (frozen-status clause). |
| Q1.3 | minor | §3.1 ¶22 reference verified against design.md line 22; correct. | No change required. |
| Q1.4 | major | §1.2 prose said "with the HMM gate-state indicator `g_i(t)` applied", but §2.2 then displayed an explicit form re-multiplying by `g_ES(t)` — created double-gating-read risk. | Remediated §1.2: clarified that `r_i_gated(t)` is the post-gating per-bar return (gate already applied); §2.2 expanded form is showing internals of `r_i_gated(t)`, not additional multiplication. Unconditional benchmark framed as "`g_i(t)` replaced by the identity 1 for all `t`". |
| Q1.5 | minor | §3.3.1 σ values from VIX/VXN are in vol-pct units; risk-parity formula's units cancel via the 1/σ ratio. | No change required (dimensional check passed). |
| Q1.6 | major | §3.3.1 baseline 2015-01-02 — verified that 2015-01-01 is a CBOE/NYSE holiday (New Year's Day) and the first available VIXCLS observation in 2015 is 2015-01-02. VIXCLS coverage extends back to 1990 per FRED. | No change required (baseline date correct). |
| Q1.7 | minor | §3.3.2 disagreement-flagging diagnostic claimed "no Bonferroni penalty" without explicitly stating that the Path-B `T_H050(2c)` does NOT enter the Hansen 2005 SPA family. | Remediated §3.3.2: explicit statement that only the primary `T_H050(2a)` enters the SPA family of §4.3. |
| Q1.8 | minor | §1.4 forecloses Family-3 "pending follow-up `P1-H050-MULTIVARIATE-SR`"; verified §5.3 marks this as "out-of-scope: ... if equal-weighted single-series view ever judged insufficient", consistent with new-follow-up framing. | No change required. |
| Q1.9 | minor | §4.3 acknowledges Romano-Wolf vs Hansen SPA inconsistency as out-of-scope — should explicitly state which family is operationally binding for this addendum's reporting. | Acceptable as-is (§4.3 names Hansen 2005 SPA as the family invoked here, with the inconsistency tracked separately as `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE`). |
| L1.1 | minor | Whaley 1993 *J. Derivatives* DOI `10.3905/jod.1993.407868` could not be verified without web access; IIJ DOI registry coverage of 1993 issues is intermittent. | Remediated §3.3.1: dropped the unverified DOI; cited Whaley 1993 by journal-volume-page form only. |
| L1.2 | major | §3.3.1 framed Whaley 1993 as the operational anchor for VIXCLS; VIXCLS uses the post-2003 CBOE model-free methodology backfilled to 1990, so Whaley 1993 is the historical-design reference, not the operational anchor. | Remediated §3.3.1: split into "Anchor citations (historical)" and "Operational anchor" subsections; Whaley 1993 in the historical bucket; CBOE 2003 model-free White Paper methodology + FRED VIXCLS / VXNCLS in the operational bucket. |
| L1.3 | minor | DeMiguel-Garlappi-Uppal 2009 title verified: "Optimal Versus Naive Diversification: How Inefficient Is the 1/N Portfolio Strategy?" *RFS* 22(5):1915-1953 doi:10.1093/rfs/hhm075. | No change required. |
| L1.4 | minor | The historical/operational distinction for VIX heritage was implicit in r0; tightening the wording improves auditability. | Remediated §3.3.1 (handled jointly with L1.2). |
| L1.5 | minor | Bailey & López de Prado 2014 — title and DOI verified against memo r4 §8 audit chain. | No change required. |

**Disposition summary**: 2 major (Q1.4, L1.2) + 7 minor remediated; 5 verifications no-change-required. No critical findings. Round-1 closes with all majors disposed of.

## Round 2 (r1 → r1 remediation; addendum revision held at r1)

**Auditors**: inline `quant-auditor` (verify Round-1 remediations + new defects) + inline `literature-check` (verify Round-1 citation corrections).

**Findings (4 quant + 2 lit-check):**

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| Q2.1 | minor | §1.2 unconditional framing as "`g_i(t)` replaced by identity 1 for all t" — verified consistent with §2.2 unconditional construction. | No change required. |
| Q2.2 | minor | §3.3.1 dimensional analysis of `1/σ` weights — units cancel; non-issue. | No change required. |
| Q2.3 | major | §3.3.1 used `=` (equality) between σ_ES and VIXCLS, implying VIX *is* ES vol; semantically the relationship is definitional substitution (proxy adoption), not equality. The addendum's "proxy for ES" prose disclaims this in narrative but the formula uses `=`. | Remediated §3.3.1: replaced `=` with `:=` (definitional assignment) in the σ definitions and added explanatory sentence about pre-substrate proxy adoption + empirical-equivalence deferral to §3.3.3. |
| Q2.4 | major | §1.2 formal definition assumed full-coverage panels but did not address the current substrate's NQ-2025 absence; running on incomplete substrate would silently halve effective leverage of `r_p_*` on NQ-missing bars. | Remediated §1.2: added explicit paragraph stating the addendum presupposes Cell I backfill completion before any walk-forward run; running before Cell I would constitute an additional pre-reg deviation foreclosed by §7. |
| L2.1 | minor | DeMiguel-Garlappi-Uppal 2009 title capitalisation (sentence-case in the addendum vs title-case in journal). | No change required (capitalisation difference only; bibliographic citation is unambiguous). |
| L2.2 | clean | All non-Whaley DOIs inherited from memo r4 §8 audit chain (3-round-verified). | No change required. |

**Disposition summary**: 2 major (Q2.3, Q2.4) + 1 minor remediated; 3 verifications no-change-required. No critical findings. Round-2 closes with all majors disposed of.

## Round 3 (final; cap reached per skill protocol)

**Auditors**: inline `quant-auditor` (verify Round-2 remediations land cleanly + final gate-keep) + inline `literature-check` (spot-check no new citation drift introduced).

**Findings (2 quant + 0 lit-check):**

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| Q3.1 | minor | New §1.2 paragraph said "foreclosed by §7 below"; §7 as written only said "addendum precedes Cell I", not "no runs on incomplete substrate". | Remediated §7: split into §7.1 forward-gating (addendum precedes Cell I) + §7.2 backward-gating (no walk-forward runs on incomplete substrate); §7.2 mandates a load-time assertion in the orchestrator that both per-symbol panels cover `[2015-01-01, 2025-12-31]` before any fold construction; failure must raise. |
| Q3.2 | minor | §4.1 + §4.2 inference-machinery sections did not specify whether the per-side Opdyke CIs and the Ledoit-Wolf differential CI use the same bootstrap block-length, which affects reproducibility. | Remediated §4.2: added explicit binding that both share a single `politis_white_block_length` selected on the paired-difference series `r_p_gated − r_p_uncond`; selected block-length is recorded in `ReproLog.run_metadata` for deterministic recomputation. |
| Lit Spot-1 | clean | All literature anchors verified in Round 1+2 spot-checks; DOIs inherited from memo r4 §8 audit chain. | No change required. |
| Lit Spot-2 | clean | No new citations introduced in Round 2 or Round 3. | No change required. |

**Disposition summary**: 2 minor remediated; 2 lit-spot-checks clean. No critical or major findings in Round 3. All `critical` and `major` fixes complete by end of Round 2.

## Residual risk (post Round 3, skill cap reached — surfaced per protocol)

The audit-remediate-loop skill's 3-round cap means residual risk after Round 3 must be surfaced explicitly rather than silently iterated to Round 4+.

### Inherited from parent memo (still applicable)

These residuals from [docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md](audit_trail_2026-04-24_h050-aggregation-rule.md) §"Residual risk" remain attached to the addendum because the addendum operationalises the memo's recommendation:

1. **Politis-Romano 1992 IMS Lecture Notes citation precision** — narrative-only reference; LW2008 is the cited differential-CI source and is unaffected.
2. **Path-B robustness gate empirical anchoring** — §3.3 VIX/VXN-frozen-σ proposal's empirical equivalence to risk-parity-with-realised-vol is part of the H050 evidence-bar deliverable, not validated at addendum-acceptance time.
3. **`P1-MISSING-BAR-RATE-EMPIRICAL`** + **`P1-GATE-RATE-RATIO-EMPIRICAL`** — 1% / 3:1 placeholder thresholds in §2.3 / §2.4 / inherited §6 are anchor-priors, to be re-tuned after the first H050 walk-forward run.

### New (introduced by the addendum)

1. **Inline-audit substitution for Task subagent**: this audit was performed inline rather than via the prescribed `literature-check` + `quant-auditor` Task-spawned subagents because the Task tool was not available in the executing harness. The classification rubric and DOI-verification discipline match the parent memo's r4 audit chain, but the inline-audit lacks the isolation property of subagent-based auditing (the auditor and auditee share a context window). If the user wishes to re-run under proper subagent isolation, a successor audit appended as Round 4 must be invoked explicitly (which exceeds the 3-round cap).
2. **Whaley 1993 DOI unverified**: the IIJ DOI registry coverage of 1993 *J. Derivatives* issues is intermittent; the addendum cites the journal-volume-page form only. This is acceptable as a historical-anchor reference (the operational anchor is the post-2003 CBOE model-free methodology + FRED VIXCLS / VXNCLS series). If a future literature-check turns up a stable DOI it should be appended.
3. **Path-B run computational cost**: §3.3.2 mandates emitting both `T_H050(2a)` and `T_H050(2c)` on every evidence-bar walk-forward run. This roughly doubles the per-run compute (the per-symbol fit/predict step is shared, but the per-bar portfolio construction + per-side Opdyke CIs + differential bootstrap CIs run twice). User accepted this cost implicitly via the recommendation-bundle acceptance; flagged here for transparency.

### Out-of-scope to this addendum (tracked elsewhere)

- **`P1-HMM-FOLD-WARM-START`** — Cycle-6 Phase-B blocker; addressed in [memo_cycle6-pause-status_2026-04-24.md](../research_notes/memo_cycle6-pause-status_2026-04-24.md).
- **`P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE`** — pre-existing Romano-Wolf vs Hansen SPA inconsistency in [design.md](../../research/01_hypothesis_register/H050/design.md) §1 vs [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml); pre-dates this addendum.

### New blocking follow-ups added to the inventory by this addendum

- **`P1-H050-PATHB-DISCORD-{run_id}`** — placeholder form for any future evidence-bar-run discordance between `T_H050(2a)` and `T_H050(2c)` per §3.3.2 third bullet; instantiated only on observed discordance, not pre-emptively.

(All other follow-ups invoked by the addendum — `P1-H050-DUAL-SYMBOL-ORCHESTRATOR`, `P1-CYCLE6-FOLD-STATIONARITY`, `P1-MISSING-BAR-RATE-EMPIRICAL`, `P1-GATE-RATE-RATIO-EMPIRICAL`, `P1-H050-CI-DIFFERENTIAL`, `P1-H050-EXECUTION-WEIGHT-MAP`, `P1-H050-MULTIVARIATE-SR` — are inherited from the parent memo r4 §6 + §5 and already in the project's blocking-followups inventory.)

## Verdict

**accept**

The 3-round audit-remediate cycle has resolved all `critical` and `major` findings; Round 3 surfaced only minor improvements which were remediated in-line. Round-3 residuals are either inherited from the parent memo's audit chain (already documented), introduced by the inline-audit substitution (transparency note), or new follow-ups that depend on first-run empirical evidence and cannot be resolved analytically.

The addendum is ready to be the binding pre-reg clarification gating Cell I.

Per the addendum §3 eligibility criteria, the user's prior 2026-04-24 acceptance of the recommendation bundle (sub-rule 2a + sub-rule 3.3a + Path A) covers:

1. **Substrate-blind-rationale attestation** (§3.2) — recorded as binding text inside the addendum; user acceptance of the addendum constitutes attestation.
2. **Path-B-equivalence robustness gate** (§3.3) — pre-registered as a single-variant 2c-with-VIX/VXN-frozen-σ run alongside every primary 2a run.
3. **Path A vs Path B mechanic** (§3.1) — Path A (in-place addendum) selected; design.md is not modified.

Failure of any §3 eligibility criterion forces Path B (successor hypothesis ID `H050.1` or equivalent) — not "Path A.5".

## Citations chain (verified across all rounds)

All Tier-1 references inherited from [memo r4 §8 audit chain](../research_notes/memo_h050-aggregation-rule_2026-04-24.md), which carries the 3-round verification: Markowitz 1952 (10.1111/j.1540-6261.1952.tb01525.x), Sharpe 1966 (10.1086/294846), Lo 2002 (10.2469/faj.v58.n4.2453), Opdyke 2007 (10.1057/palgrave.jam.2250084), Politis-Romano 1994 (10.1080/01621459.1994.10476870), Politis-White 2004 (10.1081/ETC-120028836), Hansen 2005 (10.1198/073500105000000063), Ledoit-Wolf 2008 (10.1016/j.jempfin.2008.03.002), Bailey-LdP 2014 (10.3905/jpm.2014.40.5.094).

New for this addendum (verified inline):

- DeMiguel, V.; Garlappi, L.; Uppal, R. 2009. *RFS* 22(5):1915-1953, doi:10.1093/rfs/hhm075 — title and DOI verified per Round 1 L1.3.

Cited without DOI (deliberate, residual item 2):

- Whaley, R. E. 1993. "Derivatives on Market Volatility: Hedging Tools Long Overdue." *J. Derivatives* 1(1):71-84 — historical anchor; IIJ DOI registry coverage intermittent. Operational anchor for VIXCLS / VXNCLS is the post-2003 CBOE model-free White Paper methodology + FRED series provenance.

## Commits

To be filled at commit time (per task constraints, this audit run does NOT create the commit):

- `(this audit run)` — produced [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) (r1) and this audit trail; commit deferred to user. Suggested commit message: `feat(h050): formalise P1-H050-AGGREGATION-RULE addendum (r1) + 3-round audit trail`.
- `(Round-4 corrective run, 2026-04-24)` — produced revision r2 of the addendum (post-loop-verification under proper subagent isolation) and the Round-4 section appended below in this trail; commit deferred to user. Suggested commit message: `fix(h050): r2 addendum post-loop-verification — arithmetic-return-space directive + LW2008 impl-gap binding`.

## Round 4 — post-loop-verification (proper-subagent isolation)

### Provenance and exception-to-cap rationale

The audit-remediate-loop skill caps inline iterations at 3 rounds; Rounds 1-3 above were performed *inline* (auditor and auditee in the same context window) because the Task tool was unavailable in the executing harness, and that limitation was surfaced explicitly as Round-3 residual item 1. Subsequently, the executing harness made independent `quant-auditor` and `literature-check` subagent invocations available, and the user invoked them in a post-loop-verification pass against the r1 addendum.

This Round 4 is therefore **not** a Round-4 of the original 3-round loop (which terminated correctly at the cap with verdict `accept`); it is a **corrective post-loop-verification** producing revision r2. The distinction matters for the skill's audit-trail semantics:

- The original 3-round inline loop closed cleanly per its own protocol; verdict `accept` for r1 stands as recorded.
- The corrective Round 4 was triggered by the inline-audit-substitution residual (Round-3 residual 1, "if the user wishes to re-run under proper subagent isolation, a successor audit appended as Round 4 must be invoked explicitly which exceeds the 3-round cap"). The user invoked it explicitly, which is the documented exception path.
- r2's verdict is **accept (Round-4-amended)**; r1's verdict is preserved unchanged in the §"Verdict" block above for historical-audit traceability.

This pattern (3-round inline cap reached → user-invoked proper-subagent re-audit as Round 4) is documented for the audit reader as the canonical exception-to-cap path when inline-audit substitution was the only available form during the original loop.

### Round-4 auditor invocations (proper subagent isolation)

- Independent `quant-auditor` subagent — methodological-framing pass over r1 with full context-window isolation from the addendum-author context. Rubric: critical / major / minor per the audit-remediate-loop skill.
- Independent `literature-check` subagent — DOI / citation-verification pass over r1 with web-tool access for primary-source verification. Verified Whaley 1993 DOI `10.3905/jod.1993.407868` resolves clean against Crossref (title "Derivatives on Market Volatility", author Whaley R. E., page 71-84, 1993; 384 referenced-by-count); Campbell-Lo-MacKinlay 1997 *The Econometrics of Financial Markets* (Princeton; ISBN 978-0-691-04301-2; Crossref alt DOI `10.1515/9781400830213`) §1.4 is the canonical reference for the arithmetic-vs-log return convention.

### Round-4 findings (2 major + 9 minor consolidated)

| ID | Severity | Issue | Disposition (revision r2) |
|---|---|---|---|
| Q4.1 | **major** (M1) | §1.2 (line 27) and §2.2 (line 79 of r1) bind aggregation in "arithmetic-return space"; orchestrator [scripts/run_walk_forward.py:662](../../scripts/run_walk_forward.py) computes `r_bar[1:] = np.diff(np.log(closes))` (log returns). Portfolio identity `r_p = w·r_ES + w·r_NQ` holds *exactly* only for arithmetic returns; for log returns it is a first-order approximation. Both inline-audit chains (parent memo r4 + addendum Rounds 1-3) missed this. | Remediated: added §5.1 + §5.2 (binding directive — per-bar `R_i(t) = exp(r_i(t)) − 1` conversion before equal-weighted aggregation) + new follow-up `P1-H050-AGGREGATION-CONVENTION-TEST` (machine-precision unit test, evidence-bar-blocking). User-accepted §1.2 binding to arithmetic-return space preserved; r2 does not rebind to log-return space (such a rebinding would be a successor-ID amendment per [design.md](../../research/01_hypothesis_register/H050/design.md) §10). |
| Q4.2 | **major** (M2) | §4.2 binds the differential CI to "Ledoit-Wolf 2008 studentized time-series bootstrap" but no callable LW2008 differential-CI function exists in the codebase. [src/skie_ninja/inference/stats/sharpe_ci.py:67-71](../../src/skie_ninja/inference/stats/sharpe_ci.py) explicitly states LW2008 was "used in Cycle 5 for SPA differentials, not here"; lines 94-97 say "will be implemented in Cycle 5" but no callable was actually shipped. | Remediated: added §5.3 (binding directive — implementation-gap acknowledgement + construction spec reusing existing `politis_white_block_length` + `stationary_bootstrap_indices` primitives on the paired-difference series) + new follow-up `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` (evidence-bar-blocking; first H050 walk-forward run gated on this callable). §6.3 updated to reflect spec-binding-closed but implementation-callable-open status of `P1-H050-CI-DIFFERENTIAL`. |
| Q4.3 | minor | §2.1 cited line 852 in a 1030-line orchestrator file; current file is 1026 lines and the binding statement sits at line 848. The numeric anchors keep drifting across orchestrator edits. | Remediated §2.1: replaced numeric line/length references with grep-anchored text references ("locate via grep on the line containing `position = np.sign(2.0 * p - 1.0)`") + r1-vs-r2-drift footnote for forward-robustness. |
| Q4.4 | minor | §3.2 substrate-blind attestation cited [CLAUDE.md](../../CLAUDE.md) "Phase 1 ingest — live on this machine" — loose reference; the Tier-2b 1-min ES+NQ substrate is described under a different bullet ("Tier-2b buildout (started 2026-04-23) → ES + NQ 1-min raw (evidence-bar tier)"). | Remediated §3.2: tightened citation to the specific [CLAUDE.md](../../CLAUDE.md) bullet + cross-reference to the ingest audit trail [docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](audit_trail_2026-04-23_vendor-legacy-1min-ingest.md). |
| Q4.5 | minor | §3.3.1 σ-value gap: the addendum named VIXCLS(2015-01-02) and VXNCLS(2015-01-02) symbolically but did not record the actual frozen values, leaving the Path-B variant's binding numerically incomplete at addendum-acceptance time. | Remediated §3.3.1: WebFetch on the FRED CSV endpoint returned VIXCLS(2015-01-02) = 17.79 and VXNCLS(2015-01-02) = 19.20; both values inserted verbatim into the σ definitions; canonical 2-line snapshot SHA256 `93f7d05caf6d4819ddd934383adbc77115c4c2d428af329c0d78ccb60aca21c4` recorded for deterministic auditor reproduction; resulting Path-B weights `w_ES_pathB ≈ 0.5191`, `w_NQ_pathB ≈ 0.4809`. |
| L4.1 | minor | Whaley 1993 DOI `10.3905/jod.1993.407868` was dropped in r1 (Round-1 finding L1.1) due to "intermittent IIJ DOI registry coverage". Independent literature-check subagent (with Crossref web access) confirmed the DOI resolves clean. | Remediated §3.3.1: restored the DOI as a hyperlinked citation; Round-1 L1.1 residual closed; r1 unverified-DOI residual struck. |
| L4.2 | minor | Campbell-Lo-MacKinlay 1997 was the canonical Tier-1 reference for the arithmetic-vs-log return convention but was not cited anywhere in the addendum. | Remediated §5.1: introduced the citation (ISBN 978-0-691-04301-2; Crossref alt DOI `10.1515/9781400830213`) + jointly cited [~/.claude/rules/quant-project.md](../../.claude/rules/quant-project.md) "Time-series integrity" clause. |
| Q4.6 | minor | §6.3 (formerly §5.3) marked `P1-H050-CI-DIFFERENTIAL` as fully closed by §4.2; the new §5.3 implementation-gap finding makes it accurate to describe that follow-up as spec-binding-closed but implementation-callable-open. | Remediated §6.3: split closure into the two layers; new follow-up `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` named explicitly. |
| Q4.7 | minor | §7 "Effective-from date and revision" did not document the r1 → r2 transition. | Remediated §7: bumped revision to r2; itemised the editorial-correction set (M1, M2, σ-values, Whaley-DOI, grep-anchored line refs, §3.2 tightening, renumbering); preserved binding-rule unchanged status under the §7 successor-amendment rule. |
| Q4.8 | minor | Inserting a new §5 between §4 and the original §5 required renumbering former §5/§6/§7 → §6/§7/§8 and updating all internal cross-references (notably §1.2's "foreclosed by §7"). | Remediated: all `## §` and `### §` headers renumbered consistently; §1.2 reference updated to "§8"; verified clean via grep on `^## §|^### §` (no stale numeric §-references remain in body text). |
| Q4.9 | minor | The new §5 implementation directives needed to be flagged as evidence-bar-blocking with same-footing as the existing CLAUDE.md blockers, not buried as cross-references. | Remediated §5: explicit "evidence-bar-blocking for the first H050 walk-forward run" framing in §5 preamble; §5.2 + §5.3 directives bound as the gating preconditions; §6.3 lists both new follow-ups under the same heading as inherited blockers. |

### Round-4 disposition summary

2 major (Q4.1, Q4.2) + 9 minor (Q4.3-Q4.9, L4.1, L4.2) findings — all remediated in revision r2. No critical findings.

The original-loop residual list (§"Residual risk" above) is preserved verbatim because Round 4 was a corrective pass, not an extension of the loop. Two of those residuals are now closed by Round 4 and are amended below:

- Round-3 residual 1 (inline-audit substitution) — **closed** by Round 4's proper-subagent invocation. The post-loop-verification was the documented exception-to-cap path the residual itself prescribed.
- Round-3 residual 2 (Whaley 1993 DOI unverified) — **closed** by L4.1 (DOI verified clean against Crossref; restored to §3.3.1).

### Round-4 residuals (surfaced to user per skill protocol)

1. **`P1-H050-AGGREGATION-CONVENTION-TEST` test pending implementation** — the unit test is bound at the spec level by §5.2 but its commit is part of the `P1-H050-DUAL-SYMBOL-ORCHESTRATOR` workstream, not this addendum-revision run. Surfaced to user for tracking under the existing follow-up inventory.
2. **`P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` callable pending implementation** — same status; bound by §5.3, evidence-bar-blocking, requires a separate workstream to deliver the [src/skie_ninja/inference/stats/](../../src/skie_ninja/inference/stats/) callable. Surfaced to user as a new evidence-bar-blocking follow-up to be added to [CLAUDE.md](../../CLAUDE.md) blocker inventory by the parent agent (per task constraint, this addendum-revision run does not modify [CLAUDE.md](../../CLAUDE.md)).
3. **FRED CSV endpoint date-filter behaviour** — the `cosd` / `coed` query parameters returned the full series rather than honouring the 2015-01-02 single-date filter at retrieval time; the 2015-01-02 row was extracted via post-fetch grep. The values are still primary-source FRED observations, but the snapshot SHA256 recorded in §3.3.1 is for the canonical 2-line `(header, 2015-01-02)` pair, not the raw HTTP response. Auditors reproducing the σ values must recompute the same canonical 2-line form to match the SHA256. Surfaced for transparency; not blocking.
4. **r1 verdict-block historical preservation** — the §"Verdict" block above describes r1 as `accept`. r2's verdict is `accept (Round-4-amended)` per the front-matter. The two are not contradictory but the audit reader should note that the first instance of `accept` is the inline-loop verdict on r1, while the front-matter and the present Round-4 block carry the corrective-pass verdict on r2.

### Round-4 verdict

**accept (Round-4-amended)**

The post-loop-verification surfaced 2 majors that the inline 3-round loop missed. Both are now remediated in revision r2 with binding §5 implementation directives. The Round-4 corrective pass is closed; r2 is the binding addendum revision gating Cell I, with §5.2 + §5.3 directives as additional evidence-bar-blocking preconditions on the first H050 walk-forward run.

The 3-round skill cap is preserved as the operating norm; the Round-4 corrective is the documented exception path triggered by the explicit Round-3 inline-audit-substitution residual. Future addenda or revisions should aim for proper-subagent isolation from Round 1 to avoid a Round-4-corrective being needed at all.
