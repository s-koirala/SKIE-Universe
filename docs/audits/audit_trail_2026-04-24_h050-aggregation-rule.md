---
name: H050 cross-symbol aggregation rule — audit trail
description: 3-round audit-remediate trail for the H050 aggregation-rule resolution memo (P1-H050-AGGREGATION-RULE pre-reg deviation), produced under the audit-remediate-loop skill (3-round cap)
type: project
status: closed
date: 2026-04-24
rounds: 3 (cap reached)
verdict: proceed-to-user-decision-with-documented-residuals
---

# H050 cross-symbol aggregation rule — audit trail

Audit trail for [docs/research_notes/memo_h050-aggregation-rule_2026-04-24.md](../research_notes/memo_h050-aggregation-rule_2026-04-24.md), which resolves `P1-H050-AGGREGATION-RULE` — the pre-reg deviation surfaced by the Option-B briefing audit-remediate-loop ([memo_option-b-data-coverage_2026-04-24.md](../research_notes/memo_option-b-data-coverage_2026-04-24.md) §11.1) regarding cross-symbol return aggregation when [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml) `universe = [ES, NQ]` but [research/01_hypothesis_register/H050/design.md:30](../../research/01_hypothesis_register/H050/design.md) §1 names a single test statistic `T_H050` without specifying multi-symbol combination semantics.

The memo recommends sub-rule 2a (equal-weighted constant 0.5/0.5 in return space) + sub-rule 3.3a (hold inactive in cash) + Path A (addendum file) as the default-recommendation bundle, anchored in Markowitz 1952 / Sharpe 1966 / Lo 2002 / Opdyke 2007 / Ledoit-Wolf 2008 / Bailey-LdP 2014 DSR.

This audit trail records all 3 rounds of audit-remediate per the [audit-remediate-loop skill](C:/Users/skoir/.claude/skills/audit-remediate-loop). Cap reached; residuals surfaced rather than silently iterated.

## Deliverable

- [docs/research_notes/memo_h050-aggregation-rule_2026-04-24.md](../research_notes/memo_h050-aggregation-rule_2026-04-24.md) (revision r4 at end of Round 3)

## Round 1 (r0 → r2 remediation)

**Auditors**: `quant-auditor` (recommendation-vs-implementation surface §3, §5) + `literature-check` (Sharpe 1966 / Sharpe 1994 / Lo 2002 / Opdyke 2007 / Ledoit-Wolf 2008 / Wright-Yam-Yung 2014 citation chain) — run in parallel per skill protocol.

**Findings (10 quant + 8 lit-check; consolidated):**

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| F-1-1 | major | §3.2 capacity-ceiling arithmetic mis-stated 1:1 contracts as 0.5/0.5 notional; correct is 0.36/0.64; 20:40 capacity is 0.22/0.78. | Remediated §3.2 item 5. |
| F-1-2 | major | §3.4 framed unconditional benchmark as "fully invested at all bars"; positions actually take values in `{-1, 0, +1}` per `np.sign(2.0 * p - 1.0)` mapping. | Remediated §3.3 + §3.4 with explicit position-value framing. |
| F-1-3 | major | §5 implementation surface too thin — orchestrator-alignment, cost-deduction-ordering, config-schema, per-symbol fit/predict + alignment unspecified. | Remediated §5 (rewrote into 5 sub-sections); added `P1-H050-DUAL-SYMBOL-ORCHESTRATOR` follow-up. |
| F-1-4 | major | §4.1 Path A presented as low-cost option without articulating eligibility criteria; risks becoming a free-floating pre-reg escape hatch. | Remediated §4.1.1 with two-part eligibility test (genuine ambiguity + no substrate-conditioned selection); cited Bailey-LdP 2014 DSR + AFML §11/§15. |
| F-1-5 | major | §3.2 conflated "rule substrate-independence" with "selection substrate-independence"; rule is parameter-free but the *choice* of 2a from {2a-2d} is being made post-substrate-inspection. | Remediated §3.2 item 1 with selection-HARK note + cross-link to §4.1.1. |
| F-1-6 | minor | §2.3 Family 3 point-estimate equivalence (3a ≡ 3b) does not imply equivalent inference; small-sample CI properties differ. | Remediated §2.3 with sampling-distribution note. |
| F-1-7 | minor | §6 silent on cross-fold concatenation non-stationarity assumption. | Remediated §6 fourth bullet; added `P1-CYCLE6-FOLD-STATIONARITY` follow-up. |
| F-1-8 | minor | §0 silent on the existing pre-reg artifact inconsistency between design.md (Romano-Wolf) and H050.yaml/run_walk_forward.py (Hansen SPA). | Remediated §0 out-of-scope footnote; added `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` follow-up. |
| F-1-9 | minor | §6 silent on per-symbol gating-frequency asymmetry under 3.3a. | Remediated §6 fifth bullet with diagnostic recommendation. |
| L-1 | critical | r0 §2.3 cited a J. Banking & Finance DOI (10.1016/j.jbankfin.2014.06.026) for Wright-Yam-Yung 2014 — that DOI resolves to an unrelated paper. | Remediated: dropped spurious DOI from §2.3 and §8 references. |
| L-2 | critical | r0 §8 references gave J. Risk DOI as 10.21314/JOR.2014.286 (off-by-3); correct DOI is 10.21314/JOR.2014.289. | Remediated §8 references. |
| L-3 (R1) | major | r0 §2.2 cited Sharpe 1966 + Sharpe 1994 jointly for portfolio-Sharpe construction; Sharpe 1994 explicitly disclaims SR for single-investment-return; the construction's heritage is Markowitz 1952 (per-bar weighted sum) + Sharpe 1966 / Lo 2002 (SR of single series). | Remediated §2.2 (split heritage citations); §3.2 item 3 (corrected attribution); §8 references (added Markowitz 1952; reframed Sharpe 1994 inclusion as for `T_H050` differential context only). |
| L-4 (R1) | major | r0 §3.1 wording "Politis-Romano stationary bootstrap (their primary recommendation; circular-block is a secondary variant)" was implementation-specific and risked over-claiming Ledoit-Wolf's footprint. | Remediated §3.1 alignment with literature-check phrasing. |
| L-5 | major | ADR-0005 silent on cross-fold HMM warm-start / state-threading; not in scope of this memo but flagged as supporting evidence for `P1-HMM-FOLD-WARM-START` blocker (Option B work). | Acknowledged in Round-1 audit trail; out-of-scope for this memo. |
| L-6 | major | r0 §3.2 item 4 over-stated "cross-correlation absorption" as automatic in Opdyke 2007's HAC formula; absorption happens at the portfolio-construction step, not within Opdyke. | Remediated §3.2 item 4 with portfolio-variance identity and explicit ordering. |
| L-7 | minor | r0 §8 references missing Politis-Romano 1994 (the actual stationary-bootstrap paper invoked by Ledoit-Wolf 2008). | Remediated §8 Tier-1 references (added Politis-Romano 1994 + Politis-White 2004). |
| L-8 | minor | r0 §3.2 item 5 implicit scale-invariance of SR under positive scalar capital base unverified. | Remediated §3.2 item 5 with explicit `SR(c·r) = sign(c)·SR(r)` verification. |
| Lit-completeness | minor | Tier-2 practitioner cross-check (Pav 2024 SharpeR vignette) not cited. | Remediated §8 Tier-2 references. |

**Disposition summary**: 2 critical (DOIs) + 6 major (F-1-1 through F-1-5, L-3, L-4, L-6) + 9 minor remediated. 1 major (L-5) acknowledged as out-of-scope (tracked under Option B `P1-HMM-FOLD-WARM-START` blocker). All `critical` fixes complete by end of Round 1; no `critical` residuals.

## Round 2 (r2 → r3 remediation)

**Auditors**: `quant-auditor` (verify Round-1 remediations + new defects) + `literature-check` (verify Round-1 citation corrections + Round-2 reference additions) — run in parallel.

**Findings (8 quant + 2 lit-check):**

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| F-2-1 | major | §5.3 cost-ordering claim was a straw-man: under linearity, per-symbol-cost-then-combine is *algebraically equivalent* to combine-then-deducted-with-correctly-weighted-blend. The argument for canonical ordering is operational/bookkeeping, not algebraic. | Remediated §5.3 (reframed as bookkeeping/canonical-ordering rationale; explicit equivalence shown; foot-gun clearly marked). |
| F-2-2 | major | §4.1.1 criterion 2 (no substrate-conditioned selection) unverifiable: ES+NQ Tier-2b substrate landed 2026-04-23, memo dated 2026-04-24 — user has had ≥1 day of substrate access. | Remediated §4.1.1 with (a) tightened temporal predicate + substrate-blind-rationale attestation, (b) Path-B-equivalence robustness gate at evidence-bar-run time. Converts unverifiable temporal claim into a falsifiable test. |
| F-2-3 | major | §5.1 config schema thin: no `schema_version`, no explicit `weights_vector`, no universe-cardinality assertion. Universe expansion (e.g., adding MES) would silently re-map "weights: equal" → 1/3 each. | Remediated §5.1: added `schema_version: h050_aggregation_v1`, `weights_vector: [0.5, 0.5]` indexed by universe order, `universe_cardinality_expected: 2`, plus three load-time validators. |
| F-2-4 | minor | §3.3 "measure-zero" claim ignored LightGBM leaf quantization. | Remediated §3.3: replaced with "empirically rare but not measure-zero"; added runtime `flat_bars_count` counter recommendation with 1% warning threshold. |
| F-2-5 | minor | §3.1 Ledoit-Wolf 2008 differential CI vs design.md §8 `opdyke2007_ci` binding — Path A's "no §8 substitution" precondition contestable. | Remediated §4.1.1 with joint-clarification scope note. |
| F-2-6 | minor | §6 stationarity + gating-asymmetry diagnostics had no decision rule. | Remediated §6: added Bonferroni-adjusted alpha + hard-stop/warn action thresholds for ADF/KPSS; added 3:1 firing-rate-ratio warn threshold (with `P1-GATE-RATE-RATIO-EMPIRICAL` follow-up to re-tune empirically). |
| F-2-7 | minor | §5.2 step 2 said "inner-join is a strict superset of trading-bar overlap" — wording slip; inner-join is the intersection. | Remediated §5.2: corrected to outer-join with explicit fill_null(0.0) on missing-symbol return columns; rationale aligned to 3.3a semantics. |
| F-2-8 | minor | §5.1 TypedDict provides no runtime validation. | Remediated §5.1: bound `AggregationSpec` to pydantic with `extra='forbid'` per InstrumentSpec pattern. |
| L-1 (R2) | minor | §8 Pav vignette title given as "SharpeR: A vignette"; actual is "Notes on the Sharpe ratio". Claim of "consolidation of Lo 2002 / Opdyke 2007 / Mertens 2002" overstated. | Remediated §8 references: corrected title; weakened claim to "covers Mertens and higher-order corrections; references Lo and Opdyke". |
| L-2 (R2) | minor | Mertens 2002 short-form title "Comments on variance of the IID estimator in Lo (2002)" missing word; full title is "Comments on the Correct Variance of Estimated Sharpe Ratios in Lo (2002, FAJ) When Returns Are IID". | Remediated §8 references: full title applied. |

**Disposition summary**: 3 major (F-2-1, F-2-2, F-2-3) + 7 minor (F-2-4 through F-2-8 + L-1 + L-2) — all remediated. No critical findings. Round-2 closes with all majors disposed of.

## Round 3 (final; cap reached per skill protocol)

**Auditors**: `quant-auditor` (verify F-2-1 through F-2-8 remediations land correctly; final gate-keep) + `literature-check` (verify L-1 + L-2 title corrections; spot-check no new citation drift introduced) — run in parallel.

**Findings (6 quant + 6 lit-check):**

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| L-3 (R3) | critical | r3 §4.1.1 cited "AFML §11.4 'Backtesting through cross-validation'" — actual §11.4 is "Backtesting Is Not a Research Tool"; the cross-validation chapter is §12 "Backtesting through Cross-Validation". | Remediated §4.1.1: §11.4 → §12; explicit Round-3 correction note inline. |
| L-4 (R3) | major | r3 §6 fourth bullet + §8 references cited "AFML §7.4" for walk-forward concatenation; §7.4 is "The Purged K-Fold CV Class", not walk-forward. Walk-forward is one of three paradigms in Chapter 11. | Remediated §6 fourth bullet (§7.4 → §11) and §8 Tier-2 references (replaced "§7.4 walk-forward concatenation" with §11/§12 paradigms framing); explicit Round-3 correction notes inline. |
| F-3-1 | minor | r3 §3.1 asserted Politis-Romano 1994 stationary bootstrap as LW2008's "primary recommendation" — primacy framing was unsupported by the LW2008 text; LW2008 §3 actually references both circular-block (1992) and stationary (1994) variants. | Remediated §3.1: removed primacy framing; bound block-variant choice to [rules/quant-project.md](../../.claude/rules/quant-project.md) and [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py) implementation rather than to a literature-level claim. |
| F-3-2 | minor | r3 §5.2 step 3 forward-referenced "§6 fourth bullet" for missing-bar Bonferroni-adjusted threshold; §6 fourth bullet covers fold-stationarity diagnostics, not missing-bar threshold. | Remediated §5.2 step 3: defined inline 1% missing-bar warn threshold (anchored to §3.3 `flat_bars_count` 1% threshold and "shared CME RTH calendar" prior); removed forward-reference; added `P1-MISSING-BAR-RATE-EMPIRICAL` follow-up. |
| F-3-3 | minor | r3 §3.2 item 5 SR scale-invariance verification given as `SR(c·r) = sign(c)·SR(r)` — correct for any non-zero scalar; no defect, restated for clarity. | No change required; flagged for reviewer transparency. |
| F-3-4 | minor | r3 §4.1.1 sub-clause 2.b cited "CBOE 5y rolling vol" without a concrete ticker — CBOE does not publish a "5y rolling vol" series; the operational anchors are VIX/VXN. | Remediated §4.1.1 sub-clause 2.b: replaced "CBOE 5y rolling vol" with VIXCLS (FRED) + VXNCLS (FRED) at fixed 2015-01-01 pre-substrate date (first day of pre-reg train window). |
| F-3-5 | minor | r3 §6 stationarity decision rule lumped ADF and KPSS into a single Bonferroni family with hard-stop on ADF-alone failure; the two tests have *opposite null hypotheses* and form a confirmatory pair, not a single family. ADF non-rejection is consistent with low test power, not with confirmed non-stationarity. | Remediated §6 fourth bullet: decoupled Bonferroni alphas (alpha_ADF + alpha_KPSS separately); 2x2 confirmatory-pair joint decision matrix; hard-stop only in the (No ADF rejection, Yes KPSS rejection) corner. Cited Kwiatkowski-Phillips-Schmidt-Shin 1992 + Hamilton 1994 §17 standard. |
| F-3-6 | minor | r3 §3.4 carried "exact-0.5 hits are measure-zero in practice" wording from r0 inconsistently with the §3.3 F-2-4 "empirically rare but not measure-zero" correction. | Remediated §3.4: harmonized with §3.3 F-2-4 correction; added unconditional-side `flat_bars_count_uncond` provenance counter recommendation. |
| Lit Spot-1 | minor | LW2008 differential-CI bootstrap variant is implementation-bound; literature-level claim downgraded per F-3-1. | Resolved as part of F-3-1. |
| Lit Spot-2 | minor | KPSS 1992 + Hamilton 1994 §17 cited narratively in §6 without DOIs; both are well-known textbook references. | Acceptable as narrative citations; both works are CRC-listed standard references. |
| Lit Spot-3 | minor | Politis-Romano 1992 IMS Lecture Notes citation is referenced narratively in §3.1 without a DOI (the IMS LN volume DOI is not stable across sources). | Acceptable as narrative reference; DOI for Politis-Romano 1994 *JASA* version retained as the canonical anchor. |
| Lit Spot-4 | minor | r3 Sharpe 1994 inclusion in §8 references — verified that the JPM 21(1) DOI 10.3905/jpm.1994.409501 resolves correctly. | No change required. |

**Disposition summary**: 1 critical (L-3) + 1 major (L-4) + 6 minor (F-3-1 through F-3-6) + 4 lit-spot-checks remediated or resolved as out-of-scope. All `critical` and `major` fixes complete by end of Round 3.

## Residual risk (post Round 3, skill cap reached — surfaced per protocol)

The audit-remediate-loop skill's 3-round cap means residual risk after Round 3 must be surfaced explicitly rather than silently iterated to Round 4+.

### Out-of-scope to this memo (tracked elsewhere)

- **`P1-HMM-FOLD-WARM-START`** (R1 L-5) — ADR-0005 cross-fold warm-start gap is a Cycle-6 Phase-B blocker, not an aggregation-rule issue; addressed in [memo_cycle6-pause-status_2026-04-24.md](../research_notes/memo_cycle6-pause-status_2026-04-24.md) and the [audit_trail_2026-04-24_cycle6-h050-feature-factory.md](audit_trail_2026-04-24_cycle6-h050-feature-factory.md).
- **`P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE`** (R1 F-1-8) — pre-existing inconsistency between design.md (Romano-Wolf) and H050.yaml/run_walk_forward.py (Hansen SPA); to be resolved as a separate pre-reg-discipline action.

### In-scope but unresolved (3-round cap)

1. **Politis-Romano 1992 IMS Lecture Notes citation precision (Lit Spot-3)**: the project does not currently host a verified DOI for the IMS LN volume; the citation is narrative-only. If a future literature-check turns up a stable DOI it should be appended. Does not affect the load-bearing claim because LW2008 is the cited differential-CI source; the underlying block-bootstrap is implementation-bound to [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py).
2. **Path-B robustness gate empirical anchoring (F-3-4 follow-on)**: the §4.1.1 sub-clause 2.b VIX/VXN-frozen-σ proposal is operationally cheap but its empirical equivalence to risk-parity-with-realized-vol has not been validated on real data; this is part of the H050 evidence-bar deliverable.
3. **§6 ADF/KPSS Bonferroni decoupling power tradeoff (F-3-5 follow-on)**: decoupling the families correctly preserves Type I error control but accepts a lower power than a joint test would have at the same nominal alpha. Empirical validation deferred to first H050 walk-forward run; if the hard-stop is observed empirically, the user must judge whether the result is genuine non-stationarity or a power-control artifact.
4. **`P1-MISSING-BAR-RATE-EMPIRICAL`** + **`P1-GATE-RATE-RATIO-EMPIRICAL`**: both 1% / 3:1 placeholder thresholds in §5.2 + §6 are anchor-priors, not empirically calibrated. Once the first H050 walk-forward lands, both should be re-tuned against the observed null distribution (e.g., bootstrap of randomized-gate runs).

### New blocking follow-ups added to the inventory

- **`P1-H050-DUAL-SYMBOL-ORCHESTRATOR`** — orchestrator restructure for per-symbol fit/predict + per-bar portfolio combination per memo §5; supersedes the bare `P1-H050-UNIVERSE-ES-ONLY` status flag.
- **`P1-CYCLE6-FOLD-STATIONARITY`** — ADF + KPSS confirmatory-pair decision matrix per §6; depends on `P1-H050-DUAL-SYMBOL-ORCHESTRATOR`.
- **`P1-MISSING-BAR-RATE-EMPIRICAL`** — empirical re-tuning of the 1% missing-bar threshold per §5.2.
- **`P1-GATE-RATE-RATIO-EMPIRICAL`** — empirical re-tuning of the 3:1 firing-rate-ratio threshold per §6.

(All four to be appended to [project_blocking_followups.md](C:/Users/skoir/.claude/projects/C--Users-skoir-Documents-SKIE-Universe/memory/project_blocking_followups.md) in the consolidation step.)

## Verdict

**proceed-to-user-decision-with-documented-residuals**

The 3-round audit-remediate cycle has resolved all `critical` and `major` findings. Remaining residuals are either out-of-scope (tracked in other audit trails) or empirical-calibration items that depend on the first H050 walk-forward run and cannot be resolved analytically.

The memo is ready for the user's accept/reject decision on the recommendation bundle (sub-rule 2a + sub-rule 3.3a + Path A). Per the memo §4.1.1 eligibility criteria, the user must additionally:

1. Attest to substrate-blind-rationale at addendum-acceptance time (§4.1.1 sub-clause 2.a).
2. Commit to the Path-B-equivalence robustness gate at evidence-bar-run time (§4.1.1 sub-clause 2.b, using VIXCLS + VXNCLS at 2015-01-01).
3. Sign off on Path A (addendum file) vs Path B (design.md amendment + successor ID) per §4.

Failure of either §4.1.1 criterion forces Path B (successor hypothesis ID) — not "Path A.5".

## Citations chain (verified across all rounds)

All Tier-1 and Tier-2 references in the memo §8 verified across Rounds 1-3 by `literature-check`. DOIs that resolved correctly at Round-3 spot-check: Markowitz 1952 (10.1111/j.1540-6261.1952.tb01525.x), Sharpe 1966 (10.1086/294846), Sharpe 1994 (10.3905/jpm.1994.409501), Lo 2002 (10.2469/faj.v58.n4.2453), Mertens 2002 (SSRN 1019823), Opdyke 2007 (10.1057/palgrave.jam.2250084), Politis-Romano 1994 (10.1080/01621459.1994.10476870), Politis-White 2004 (10.1081/ETC-120028836), Hansen 2005 (10.1198/073500105000000063), Ledoit-Wolf 2008 (10.1016/j.jempfin.2008.03.002), Bailey-LdP 2014 (10.3905/jpm.2014.40.5.094), Wright-Yam-Yung 2014 (10.21314/JOR.2014.289). DOIs that did *not* resolve and were dropped or replaced across the rounds: Wright-Yam-Yung 2014 spurious J. Banking & Finance DOI (R1 L-1); Wright-Yam-Yung 2014 off-by-3 J. Risk DOI (R1 L-2). DOIs explicitly *not* asserted because primary text was inaccessible: Politis-Romano 1992 IMS Lecture Notes (Round-3 Lit Spot-3 residual).

## Commits

To be filled at commit time:

- `(this commit)` — feat(h050): pre-reg P1-H050-AGGREGATION-RULE resolution memo + Round-3 audit trail

Branch: `claude/thirsty-hawking-472887`. Memo + trail land here; main fast-forwards.
