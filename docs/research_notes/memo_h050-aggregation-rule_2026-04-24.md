---
name: H050 cross-symbol aggregation rule — resolution proposal
description: Resolves P1-H050-AGGREGATION-RULE pre-reg deviation surfaced by the Option-B briefing audit; recommends equal-weighted per-bar portfolio combination to produce the single OOS series on which T_H050 is computed. Decision-pending; user must accept/reject before Cell I backfill begins.
type: project
status: decision-pending
date: 2026-04-24
audience: skoir
revision: r4 (post-Round-3 audit; 3-round skill cap reached; 1 critical + 1 major + 6 minor Round-3 remediations applied)
---

# H050 cross-symbol aggregation rule — resolution proposal

## 0. Purpose

Resolve `P1-H050-AGGREGATION-RULE` (surfaced as a pre-reg deviation by the Option-B briefing audit-remediate-loop, [docs/research_notes/memo_option-b-data-coverage_2026-04-24.md](memo_option-b-data-coverage_2026-04-24.md) §11.1; promoted to a blocker in [project_blocking_followups.md](C:/Users/skoir/.claude/projects/C--Users-skoir-Documents-SKIE-Universe/memory/project_blocking_followups.md)).

Per `~/.claude/CLAUDE.md` evidence hierarchy + project [CLAUDE.md](../../CLAUDE.md) "longitudinal, exhaustive research program": the aggregation choice is a *pre-registration* decision, not a runtime choice. It must be locked **before** Cell I backfill begins; once the user has inspected the post-backfill substrate, any aggregation choice is post-hoc-contaminated.

This memo proposes a rule, anchors it in the Sharpe-ratio literature already cited by the project's inference primitives, and lays out the pre-reg-amendment mechanics so the user can either accept or substitute.

**Out-of-scope footnote (F-1-8 acknowledgement):** [research/01_hypothesis_register/H050/design.md:30](../../research/01_hypothesis_register/H050/design.md) binds the multiple-testing family to "Romano-Wolf step-down family (per [ADR-0003](../../docs/decisions/ADR-0003-spa-vs-romanowolf.md))" while [config/hypotheses/H050.yaml:33](../../config/hypotheses/H050.yaml) and [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) bind Hansen SPA. This is a pre-existing pre-reg artifact inconsistency outside the scope of the present aggregation-rule resolution, but tracked here as a follow-up `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` to be added to the blocking-followups inventory.

## 1. The ambiguity in design.md §1

[research/01_hypothesis_register/H050/design.md:30](../../research/01_hypothesis_register/H050/design.md) (binding):

> Test statistic: `T_H050 = SR_{filtered, gated} − SR_{filtered, unconditional}`, where both Sharpe ratios are computed on walk-forward OOS net-of-cost returns.

[research/01_hypothesis_register/H050/design.md:34](../../research/01_hypothesis_register/H050/design.md):

> Instruments: ES and NQ front-month per [config/instruments.yaml](../../config/instruments.yaml).

[config/hypotheses/H050.yaml:3](../../config/hypotheses/H050.yaml):

> universe: [ES, NQ]

What is **not** specified: when the universe is multi-symbol, how the per-symbol return streams combine into the single return series whose Sharpe is computed. Three reading-classes are admissible from the §1 text alone:

1. **Pooled-concatenation** — stack ES and NQ OOS net-return streams end-to-end.
2. **Per-bar portfolio combination** — at each bar, combine per-symbol returns into a portfolio per-bar return, weight scheme TBD.
3. **Per-symbol SR then aggregate** — compute `SR_ES_gated`, `SR_NQ_gated` separately, aggregate.

Each implies a different `T_H050` value and a different statistical-inference path.

## 2. The three families against the project's inference primitives

[src/skie_ninja/inference/stats/sharpe_ci.py](../../src/skie_ninja/inference/stats/sharpe_ci.py) implements four CI flavors (Lo 2002 iid, Lo 2002 Proposition 2 η(q), Lo 2002 HAC-adjusted, Opdyke 2007 Mertens-HAC). All four take a **single** return-series array `r` of length `T` and return a `SharpeCI`. None natively handle a multi-symbol matrix; the cross-symbol aggregation must occur upstream.

[src/skie_ninja/inference/multipletest/hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py) (Hansen 2005 SPA, [doi:10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063)) likewise expects single-series strategy returns per column of the strategy-universe matrix.

[Ledoit & Wolf 2008, *J. Empirical Finance* 15(5):850-859, doi:10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002) — pairwise SR comparison via studentized circular-block bootstrap — also operates on two single series.

So the inference machinery is single-series-input. Multi-symbol aggregation must be a *pre-step* that produces one series per side (gated and unconditional).

### 2.1 Family 1 — pooled-concatenation: REJECTED

Construct `r_gated_concat = [r_ES_gated[1..T_ES], r_NQ_gated[1..T_NQ]]` end-to-end into a single `(T_ES + T_NQ)`-length series, and similarly for unconditional.

**Why this fails:** the concatenated series is not the return process of any tradable strategy. No investor experiences ES returns through 2025-12-03 and *then* NQ returns from 2024-01-01. The implicit time-axis is incoherent. Sharpe of an incoherent series has no economic interpretation. The variance estimator collapses two independent processes into one as if they were a single sample, distorting both the point estimate and the HAC long-run-variance computation underpinning Opdyke 2007.

This family is rejected on theoretical grounds. No published practitioner reference treats pooled-concatenation as a portfolio Sharpe construction (a literature-check would not find a defensible citation). It is mentioned here only because §1's text *permits* this reading without ruling it out.

### 2.2 Family 2 — per-bar portfolio combination: PRIMARY CANDIDATE

At each bar `t`, define the portfolio per-bar return:

`r_p(t) = Σ_i w_i · r_i_strategy(t)`

where `i ∈ {ES, NQ}`, `r_i_strategy(t)` is the symbol-`i` strategy per-bar return at bar `t` (already inclusive of the position signal and net of costs), and `w_i` is a weight summing to 1 over active symbols at bar `t`.

The construction has two distinct heritage components, each cited separately to avoid the conflation flagged by the Round-1 audit (L-3):

- **Per-bar weighted-sum portfolio-return construction**: [Markowitz 1952, *J. Finance* 7(1):77-91, doi:10.1111/j.1540-6261.1952.tb01525.x](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) — portfolio expected return as the weighted sum of constituent returns, the foundational mean-variance framework on which any later portfolio-Sharpe analysis rests.
- **Sharpe ratio of the resulting single series**: [Sharpe 1966, *J. Business* 39(1):119-138, doi:10.1086/294846](https://doi.org/10.1086/294846) reward-to-variability ratio definition, with single-series asymptotic distribution per [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453) and HAC variant per [Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084).

Note: [Sharpe 1994, *JPM* 21(1):49-58, doi:10.3905/jpm.1994.409501](https://doi.org/10.3905/jpm.1994.409501) is *not* cited here because Sharpe 1994 frames the SR around a *differential* return (fund minus benchmark) and explicitly disclaims SR for "a single investment return" as a stand-alone object — its framing applies more directly to `T_H050` as a differential statistic than to the portfolio-Sharpe construction step (audit finding L-3).

Within Family 2, four weight sub-rules are admissible:

| Sub-rule | `w_i` | Substrate-dependence | Pre-reg compatibility |
|---|---|---|---|
| **2a — equal-weighted constant** | 0.5, 0.5 | None — constant | Substrate-independent; lockable at pre-reg |
| **2b — equal-contracts dollar-PnL-weighted** | `Notional_i / Σ_j Notional_j` per bar | Yes — depends on observed per-bar prices | Substrate-independent in the *rule*; weights are intra-run from public prices (not look-ahead) |
| **2c — equal-volatility (risk-parity)** | `(1/σ_i) / Σ_j (1/σ_j)`, σ from train fold | Yes — uses train-fold realized vol | Substrate-independent in the *rule*; weights are determined per-fold from train data (not look-ahead) |
| **2d — capacity-ceiling-proportional** | `(Cap_i × Multiplier_i × P_i) / Σ_j (...)` per bar | Yes — capacity ceilings from CLAUDE.md | Substrate-independent in the *rule*; ceilings are pre-reg constants |

All four are admissible *as a pre-reg rule*. Sub-rules 2b/2c/2d use observable prices/vol but the **rule** locking the weights to a substrate-independent function is itself substrate-independent.

### 2.3 Family 3 — per-symbol SR then aggregate

Compute `SR_ES_gated`, `SR_NQ_gated`, then aggregate. Two natural aggregations:

- **3a — mean of SRs**: `T_H050 = mean(SR_ES_gated, SR_NQ_gated) − mean(SR_ES_uncond, SR_NQ_uncond)`.
- **3b — mean of differential SRs**: `T_H050 = mean(SR_ES_gated − SR_ES_uncond, SR_NQ_gated − SR_NQ_uncond)`.

3a and 3b coincide at the **point-estimate level** by linearity of the mean: `mean(a,b) − mean(c,d) = mean(a−c, b−d)` for any four scalars. So 3a and 3b yield the same value of `T_H050`. Call this Family 3 = "mean-of-Sharpe-differentials".

**Sampling-distribution note (audit F-1-6):** point-estimate equivalence does NOT imply equivalent inference. The four scalars `(SR_ES_gated, SR_NQ_gated, SR_ES_uncond, SR_NQ_uncond)` are themselves estimators with joint covariance, and Sharpe is non-linear in returns; the CI on `mean(diffs)` has different small-sample properties than the CI on `diff(means)` once the underlying multi-symbol return matrix is treated rigorously. So 3a ≡ 3b at the value level, but the inference machinery still requires multivariate handling under either form.

**Why Family 3 is statistically harder:** the project's pre-reg single-series CI methods (Lo 2002 / Opdyke 2007) cover SR of a single return process. Opdyke 2007 also gives a *two-sample pairwise* SR-difference test (algebraically related to the difference-of-Sharpe-ratios value). Neither, however, provides a full multivariate vector-of-SRs CI for k≥2 strategies. The closest published machinery is:

- [Wright, Yam, Yung 2014, *J. Risk* 16(4):3-21, doi:10.21314/JOR.2014.289](https://doi.org/10.21314/JOR.2014.289) — multivariate Sharpe-ratio test (Hotelling-T²-style); heavy machinery, not in the project's inference layer. (DOI corrected per Round-1 audit L-2; the J. Banking & Finance citation in r0 was spurious — that DOI resolved to an unrelated paper, audit finding L-1.)
- Stationary-bootstrap CI on `mean(diff_ES, diff_NQ)` — already implementable via [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py) (Politis-White 2004), but pre-reg [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §8 specifies `opdyke2007_ci`, not bootstrap, as the binding gate.

Family 3 is admissible but creates a CI-machinery mismatch with the existing pre-reg gate. Adopting Family 3 implies *also* amending §8 to substitute the CI method. This compounds the pre-reg-amendment surface.

## 3. Recommendation: Family 2, Sub-rule 2a (equal-weighted constant)

### 3.1 The rule

For each OOS walk-forward fold, at each bar `t ∈ test_fold`, compute:

```
r_p_gated(t) = 0.5 × r_ES_gated(t) + 0.5 × r_NQ_gated(t)
r_p_uncond(t) = 0.5 × r_ES_uncond(t) + 0.5 × r_NQ_uncond(t)
```

where each per-symbol per-bar return is the symbol's strategy log-return at bar `t`, net of costs, with the gate-signal multiplier applied (1 if gated, 0 if not, for `r_*_gated`; signed direction for `r_*_uncond`).

Concatenate `r_p_gated` and `r_p_uncond` across all OOS folds into two single series each of length `T_oos = Σ_fold |test_fold|`.

`T_H050 = SR(r_p_gated) − SR(r_p_uncond)`, with both SRs computed via [opdyke2007_ci](../../src/skie_ninja/inference/stats/sharpe_ci.py) per design.md §8 and the differential CI per [Ledoit-Wolf 2008, *J. Empirical Finance* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) — studentized time-series bootstrap. The block-bootstrap variant (circular-block per Politis-Romano 1992 IMS Lecture Notes vs stationary per [Politis-Romano 1994, *JASA* 89(428):1303-1313](https://doi.org/10.1080/01621459.1994.10476870)) is bound by [rules/quant-project.md](../../.claude/rules/quant-project.md) "Inference" clause and the project's [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py) implementation, not asserted here as a literature-level primacy claim. Closes `P1-H050-CI-DIFFERENTIAL`. (Round-3 lit-check F-3-1 correction: prior r3 asserted Politis-Romano 1994 stationary bootstrap as LW2008's "primary recommendation" — primacy framing was unsupported by the LW2008 text. Block-variant choice is implementation-bound, not literature-bound.)

### 3.2 Why this rule

1. **Rule-substrate-independence** (the dominant constraint). Constant 0.5/0.5 weights do not depend on any observed price, vol, or return — the rule itself is parameter-free. **Selection-HARK note (audit F-1-5):** this does not eliminate the fact that the *choice* of 2a from the menu {2a, 2b, 2c, 2d} is being made post-substrate-inspection by the user. Mitigation: the substrate-agnostic prior of "no asymmetry information asserted at pre-reg" justifies equal weights as the conservative anchor; alternative anchors (e.g., risk-parity 2c with σ frozen from a pre-substrate public source like CBOE 5y vol) would also be defensible if a different prior were asserted, but require the user to commit to that prior and document the source. Selecting 2a is thus a pre-commitment to "no asymmetry" rather than a substrate-conditioned choice; the precedent applies only when the original §1 text genuinely admits multiple readings AND the disambiguating choice was demonstrably not influenced by post-pre-reg substrate inspection (see §4 Path A precedent-cost paragraph).
2. **Compatibility with existing pre-reg gates**. Both SRs are computed on a single return series, which is exactly what `opdyke2007_ci` and the Ledoit-Wolf 2008 differential bootstrap consume. No §8 amendment needed beyond the differential-statistic correction already tracked as `P1-H050-CI-DIFFERENTIAL`.
3. **Markowitz 1952 portfolio-return + Sharpe 1966/Lo 2002 canonicity**. The construction has two separable heritage components (per audit L-3): per-bar weighted-sum portfolio-return per Markowitz 1952; SR-of-single-series per Sharpe 1966 / Lo 2002 / Opdyke 2007. Equal-weighting is the canonical Markowitz portfolio when no asymmetry information is asserted at pre-reg.
4. **Cross-correlation absorption (refined per audit L-6)**. Once `r_p(t) = 0.5·r_ES(t) + 0.5·r_NQ(t)` is constructed, the resulting single series `r_p` is what the Opdyke Mertens-HAC variance estimator consumes; cross-asset covariance is automatically embedded into the (auto)covariance / long-run variance of `r_p` via the standard portfolio-variance identity `Var(r_p) = 0.25·Var(r_ES) + 0.25·Var(r_NQ) + 0.5·Cov(r_ES, r_NQ)`. The absorption happens at the **portfolio-construction step**, not within Opdyke's formula. A risk-parity (sub-rule 2c) or capacity-proportional (2d) weighting would import a substrate-derived parameter into the rule, raising the bar for "no arbitrary thresholds" (`~/.claude/CLAUDE.md`).
5. **Capacity-ceiling note (arithmetic corrected per audit F-1-1)**. Project [CLAUDE.md](../../CLAUDE.md) caps at "<= 20 ES contracts, <= 40 NQ" — a 1:2 contract-count asymmetry. At 2026-04-24 nominal prices (ES ~5000 × $50 = $250k notional/contract; NQ ~22000 × $20 = $440k notional/contract; multipliers per [config/instruments.yaml](../../config/instruments.yaml)):
   - **1:1 contract weighting** yields 250 / (250+440) ≈ 0.36 ES / 0.64 NQ in notional terms.
   - **20:40 capacity weighting** yields (20·250) / (20·250 + 40·440) = 5,000 / 22,600 ≈ 0.22 ES / 0.78 NQ in notional terms — even further from 0.5/0.5.

   Both notional splits are far from the 0.5/0.5 weighting that sub-rule 2a applies in **return space**. Sub-rule 2a is therefore an explicit choice to weight in *return space*, not notional space. This is defensible (returns are unit-free; SR(c·r) = sign(c)·SR(r) so SR is sign-preserving and scale-invariant for any positive scalar capital base — verified per audit L-8) but is a deliberate choice, not a corollary of the capacity ceiling. The execution-time mapping of return-space-equal-weights to integer-contract positions is a separate problem tracked under follow-up `P1-H050-EXECUTION-WEIGHT-MAP`.

### 3.3 Side-condition: handling of one-sided-gated bars

The unconditional and gated positions both take values in `{-1, 0, +1}` (long, flat, short) per the orchestrator's [scripts/run_walk_forward.py:613](../../scripts/run_walk_forward.py) `position = np.sign(2.0 * p - 1.0)` mapping; `np.sign(0)=0` so a flat bar arises whenever the LightGBM classifier emits exactly p=0.5. **Empirically rare but not measure-zero (audit F-2-4):** while continuous-density samplers would render exact-0.5 hits measure-zero, LightGBM tree outputs are *sums of leaf values* — a discrete (though dense) set — so exact-tie predictions can occur at non-trivial frequency under categorical features or small leaf counts. Recommendation: emit a runtime counter `flat_bars_count = (position == 0).sum()` to per-fold provenance; if `flat_bars_count / total_bars > 0.01` warn (the gate construction degrades to a partial-flat scheme rather than the assumed sign-mapping). Empirical monitoring, not a priori dismissal. The *gated* series additionally multiplies by a 0/1 HMM-state indicator, so a gated bar with no signal contribution arises either from a flat classifier prediction or from a non-favored HMM state.

Two sub-decisions for combining at a bar where ES and NQ may have different active states:

- **3.3a — Hold weights constant.** `r_p_gated(t) = 0.5 × r_ES_gated(t) + 0.5 × r_NQ_gated(t)`, where `r_i_gated(t)` is already zero whenever symbol `i`'s position at bar `t` is flat. This treats the inactive side as held in cash (zero return); the weights remain 0.5/0.5 throughout. Cleanest semantics; cash-position returns are well-defined.
- **3.3b — Renormalize weights.** When only ES has a non-zero position, `r_p_gated(t) = 1.0 × r_ES_gated(t)`. This treats the inactive side as not present in the portfolio.

3.3a is recommended. Reason: the comparison to the unconditional series is only meaningful if both gated and unconditional share the same time axis and weight schedule. Renormalizing under 3.3b makes the gated-vs-unconditional comparison dependent on simultaneous-gating frequency, which is a property the test should *measure*, not absorb into the construction.

### 3.4 The unconditional benchmark

Symmetric: `r_p_uncond(t) = 0.5 × r_ES_uncond(t) + 0.5 × r_NQ_uncond(t)`, where each `r_*_uncond` is the unconditional directional signal (LightGBM classifier output without HMM-state-gating), net of costs.

Audit F-1-2 correction: the unconditional benchmark is **not strictly fully invested at all bars** — it can take a flat (zero) position whenever the classifier emits exactly p=0.5. **As under §3.3 (audit F-2-4), exact-0.5 hits from LightGBM are empirically rare but not measure-zero** — LightGBM outputs are sums of leaf values over a discrete (though dense) set, so categorical features or small leaf counts can produce exact-tie predictions at non-trivial frequency. The symmetry between gated and unconditional follows from both having `position ∈ {-1, 0, +1}`, not from "both fully invested". 3.3a and 3.3b coincide for the unconditional side only when no symbol's classifier emits a flat prediction — which is the practical-but-not-formal default. The same `flat_bars_count` provenance counter recommended in §3.3 applies on the unconditional side; if `flat_bars_count_uncond / total_bars > 0.01` per fold, warn. (Round-3 quant F-3-6 correction: prior r3 carried "measure-zero in practice" wording from r0 in §3.4 inconsistently with the §3.3 F-2-4 correction; harmonized here.)

## 4. Pre-registration mechanics — amendment vs addendum

[research/01_hypothesis_register/H050/design.md:22](../../research/01_hypothesis_register/H050/design.md):

> This document is the pre-registration record for hypothesis H050. Frozen at `designed`; any change requires a new hypothesis ID.

Strict reading: any text edit to design.md after `status=designed` requires H050' (successor ID). Less-strict reading: a *clarification* that disambiguates an underspecified element without altering the binding statistic, universe, or windows is not a "change" in the design-frozen sense.

Two clean paths:

### 4.1 Path A — addendum file (preferred, minimal pre-reg surface)

Create [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) that:

1. Cites design.md §1 line 30 verbatim.
2. States: "This addendum disambiguates the cross-symbol aggregation rule, which §1 leaves underspecified for `universe = [ES, NQ]`. The rule binding for any H050 walk-forward run is sub-rule 2a (equal-weighted constant 0.5/0.5 in return space) per [memo_h050-aggregation-rule_2026-04-24.md](../../docs/research_notes/memo_h050-aggregation-rule_2026-04-24.md)."
3. Pins the dated trigger: "Surfaced by Option-B briefing audit (docs/audits/audit_trail_2026-04-24_option-b-briefing.md)."
4. Frozen at the same `designed` status as design.md once user accepts.

This path leaves design.md text untouched — the binding `T_H050 = SR_gated − SR_uncond` statement is preserved verbatim — and adds a clarification artifact that future auditors can find.

#### 4.1.1 Path A precedent-cost — eligibility (audit F-1-4)

Path A is **not** a free-floating "clarification" escape hatch from pre-registration. It is admissible only when **both** of the following hold:

1. **Genuine textual ambiguity**: the original §1 / §2 text admits multiple defensible readings without picking one. Established here for the cross-symbol aggregation question — design.md §1 line 30 names the statistic (`SR_gated − SR_uncond`) but is silent on multi-symbol combination, and design.md §2 line 34 lists `[ES, NQ]` without specifying combination semantics. A literal reading therefore has no unique referent for `r_t` when `t` indexes bars on two symbols simultaneously.
2. **No post-pre-reg substrate-conditioned selection**: the disambiguating choice was not influenced by inspection of the post-pre-reg substrate. This is the harder bar. Sub-rule 2a (equal-weighted constant 0.5/0.5) is the *only* admissible weighting under Path A because it is the unique substrate-independent choice from {2a, 2b, 2c, 2d}; sub-rules 2b/2c/2d use observable quantities and therefore inherit a substrate-inspection-conditioned-choice problem when selected post-substrate.

   **Tightened temporal predicate (audit F-2-2):** the ES+NQ 1-min Tier-2b substrate landed 2026-04-23 per project [CLAUDE.md](../../CLAUDE.md), one day before this memo (2026-04-24). The user has therefore had ≥1 day of substrate access *prior* to addendum acceptance. The "commit-before-Cell-I-backfill" check protects only against post-billing inspection, not against pre-ingest exploratory inspection of the already-landed Tier-2b substrate. Two mitigations apply jointly:

   a. **Substrate-blind-rationale attestation**: the user attests at addendum-acceptance time that no relative-behavior inspection of ES vs NQ (e.g., per-symbol Sharpe, per-symbol gating-rate, per-symbol vol/drift) was performed between 2026-04-23 ingest and addendum-acceptance. The recorded basis for sub-rule 2a is the substrate-blind prior of "no asymmetry information asserted at pre-reg" (§3.2 item 1). Any later inspection that violates this attestation must be disclosed in a successor-ID amendment.

   b. **Path-B equivalence robustness gate**: at evidence-bar-run time, the addendum-bound 2a result is reported alongside a Path-B-equivalent run under sub-rule 2c (risk-parity, σ frozen from a pre-substrate public source). Concrete σ source: per-symbol implied volatility tickers VIX (FRED `VIXCLS`, CBOE Volatility Index based on S&P 500 30-day implied vol — the relevant proxy for ES) and VXN (FRED `VXNCLS`, CBOE Nasdaq-100 Volatility Index — proxy for NQ), both pulled at a fixed pre-substrate date (e.g., 2015-01-01, the first day of the pre-reg train window) so the σ vector is independent of any post-pre-reg ES/NQ price observations. If the two runs disagree at the SR-CI level, the disagreement is itself a finding; if they agree, the addendum-bound 2a result stands as the primary. This robustness gate is operationally cheap (one re-run with different weight vector) and converts the unverifiable temporal claim into a falsifiable test. (Round-3 quant F-3-4 correction: prior r3 said "CBOE 5y rolling vol" without a concrete ticker — CBOE does not publish a "5y rolling vol" series; the operational anchors are VIXCLS / VXNCLS via FRED.)

If either criterion fails (or if the user declines the §2.2.b robustness gate), **Path B (successor hypothesis ID) is mandatory** — there is no "Path A.5" partial-precedent bypass. The López de Prado anti-overfitting/anti-HARK literature ([López de Prado 2018, *Advances in Financial Machine Learning*, Wiley, §11 "The Dangers of Backtesting", §12 "Backtesting through Cross-Validation", and §15 "Understanding Strategy Risk"](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086); see also [Bailey & López de Prado 2014 "The Deflated Sharpe Ratio", *JPM* 40(5):94-107, doi:10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094) on multiple-testing-after-data-inspection) is the relevant evidence base for this stricture: any strategy parameter selected after observing the data carries a multiple-testing penalty unless the selection rule itself was substrate-blind. (Round-3 lit-check L-3 correction: prior r3 cited "AFML §11.4" mis-titled as "Backtesting through cross-validation"; actual §11.4 title is "Backtesting Is Not a Research Tool" and the cross-validation chapter is §12.)

This Path A invocation passes criterion 1 textually and passes criterion 2 only conditional on the user-attestation + Path-B robustness-gate construction above. Future auditors can re-check by comparing the addendum's commit timestamp against the Cell I backfill timestamp; the aggregation-rule resolution must commit *before* Databento billing/ingest begins to maintain the temporal precedent. The robustness-gate result is part of the evidence-bar deliverable and itself committed under reproducibility provenance.

**Joint-clarification scope note (audit F-2-5)**: this addendum disambiguates BOTH the cross-symbol aggregation rule AND the differential-CI method (Ledoit-Wolf 2008 stationary-bootstrap CI on the differential, layered atop the design.md-§8-bound `opdyke2007_ci` per-side single-series CIs). The §8 binding on `opdyke2007_ci` is preserved for the per-side gated and unconditional series; the *additional* differential-CI method is the Path A clarification, not a §8 substitution. This re-tests cleanly under the §4.1.1 eligibility criteria above because the differential CI is the natural inferential complement to the differential test statistic `T_H050` already specified in §1, not a new statistic.

### 4.2 Path B — design.md §1 amendment + new hypothesis ID

Edit design.md §1 line 30 to add the aggregation rule explicitly, increment the hypothesis ID to H050' (or H050.1), and reference H050 as parent. Heavier procedurally; equivalent in scientific content.

Path A is cleaner if the user reads §22's "any change" as referring to changes in scope, universe, statistic, or windows — not to clarifications of underspecified mechanics. Path B is cleaner if the user reads §22 strictly. The choice is itself a meta-pre-reg-discipline decision and the user must make it.

## 5. Implementation surface

Resolution of P1-H050-AGGREGATION-RULE under sub-rule 2a + 3.3a is a non-trivial orchestrator change. The current [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) is symbol-scalar (loops `sym = "ES"` only — `P1-H050-UNIVERSE-ES-ONLY`). Phase-B implementation must satisfy the following alignment requirements (audit finding F-1-3):

### 5.1 Config schema additions (audit F-2-3 + F-2-8 reinforced)

- **[config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml)** — add an `aggregation` block at top level so the rule is visible in the reproducibility artifact. The block must include explicit version, weight-vector indexed by universe order, and a universe-cardinality assertion:

  ```yaml
  aggregation:
    schema_version: h050_aggregation_v1
    family: per_bar_portfolio
    weights_vector: [0.5, 0.5]         # explicit, indexed by `universe` order
    weights_label: equal                # human-readable; must be redundant with weights_vector
    mode: hold_inactive_in_cash         # 3.3a sub-decision
    universe_cardinality_expected: 2    # asserted at load-time against len(universe)
  ```

- **[scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) `RunConfig` dataclass** — bind `aggregation` to a **pydantic** `AggregationSpec` model with `extra='forbid'` (consistent with the [InstrumentSpec](../../src/skie_ninja/utils/instruments.py) pattern), not a `TypedDict`, so missing/unknown fields raise at load time rather than silently coercing. Required fields: `schema_version` (Literal, must match the version this orchestrator handles), `family`, `weights_vector` (list[float], must sum to 1.0 ± 1e-9), `weights_label`, `mode`, `universe_cardinality_expected`. Load-time validators MUST assert:
  1. `len(weights_vector) == len(universe)` — raises if the universe expands later (e.g., {ES, NQ, MES}) without an explicit addendum amendment of `weights_vector`. Closes the silent re-mapping foot-gun.
  2. `weights_label == "equal"` IFF `all(w == 1.0/len(universe) for w in weights_vector)` — defends against label/vector divergence under future edits.
  3. `abs(sum(weights_vector) - 1.0) < 1e-9` — non-negotiable.

  `load_config` failure to find the block, or any validator failure, must raise (no silent default — pre-registration discipline).

### 5.2 Per-symbol fit/predict + alignment (audit F-2-7 corrected)

Restructure the per-symbol loop so each fold yields **four** aligned per-bar return series:

1. For each `sym ∈ {ES, NQ}`: run feature assembly, HMM fit + filter_states, LightGBM fit, and prediction. Materialize `r_sym_gated[t]` and `r_sym_uncond[t]` per-bar in test-fold timestamps.
2. Form a shared `ts_event` index by **outer-join** of the two per-symbol DataFrames on `ts_event` (RTH-only restriction per design.md §2 line 36 already applies; both symbols nominally share the CME RTH calendar but the outer-join is the safer choice — it preserves any per-symbol-only bar that arises from holiday-half-day asymmetries, halts, or session-boundary edge cases that an inner-join would silently drop).
3. Bars present for one symbol but missing the other are filled with `r_missing_sym(t) := 0.0` for both gated and unconditional return columns. This implements 3.3a (hold inactive in cash) at the bar level. Document the per-symbol missing-bar count and missing-bar fraction `f_miss = missing_bars / total_bars` per fold in the run provenance; emit a structural-asymmetry **warn** if `f_miss > 0.01` per fold per symbol (the 1% anchor matches the §3.3 `flat_bars_count` threshold and aligns to the implicit "shared CME RTH calendar" prior — bars-missing-only-for-one-symbol exceeding 1% indicates non-trivial calendar / halt asymmetry that the user should inspect, not an a priori arbitrary threshold). The threshold is itself a placeholder anchor pending empirical calibration on real data; tracked under follow-up `P1-MISSING-BAR-RATE-EMPIRICAL`. (Round-3 quant F-3-2 correction: prior r3 forward-referenced "§6 fourth bullet" which covers stationarity diagnostics, not missing-bar threshold.)

### 5.3 Cost-deduction ordering (audit F-2-1 reframed)

**Per-symbol cost deduction is the canonical bookkeeping ordering.** The combined-then-deducted form is **algebraically equivalent** by linearity of expectation IFF the blended cost is correctly defined as the per-bar weighted sum:

```
0.5·(r_ES − c_ES) + 0.5·(r_NQ − c_NQ)
  ≡ 0.5·r_ES + 0.5·r_NQ − (0.5·c_ES + 0.5·c_NQ)
```

The argument for per-symbol-first ordering is **operational**, not algebraic:

1. **Bookkeeping clarity**: the NT8 cost model in [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) charges per-side per-contract with symbol-conditional multipliers (ES=50, NQ=20). Deducting per-symbol exposes the symbol-conditional fee structure to provenance and unit tests directly.
2. **Common-implementer-error guard**: a "blended_cost" deducted as a single scalar (e.g., averaged commission ignoring symbol-multiplier asymmetry) silently breaks the equivalence and yields wrong PnL. Per-symbol-first ordering removes the foot-gun.
3. **Diagnostic surface**: per-symbol cost-by-bar series is the input to capacity-cost analysis (e.g., `cost_ES / |Δpos_ES|·notional_ES`), which is part of evidence-bar reporting per [rules/quant-project.md](../../.claude/rules/quant-project.md) Reporting clause ("transaction cost model").

The two orderings are mathematically the same when correctly implemented; the canonical ordering is the one that makes the unit test layer auditable. Concretely:

```python
# CANONICAL (per-symbol cost first; recommended):
r_ES_gated_net = r_ES_gated_gross - cost_ES_per_bar
r_NQ_gated_net = r_NQ_gated_gross - cost_NQ_per_bar
r_p_gated = 0.5 * r_ES_gated_net + 0.5 * r_NQ_gated_net

# EQUIVALENT BUT FOOT-GUN (combine first, then deduct correctly weighted blend):
r_p_gated_gross = 0.5 * r_ES_gated_gross + 0.5 * r_NQ_gated_gross
blended_cost = 0.5 * cost_ES_per_bar + 0.5 * cost_NQ_per_bar  # MUST be weighted, not constant
r_p_gated = r_p_gated_gross - blended_cost
```

### 5.4 Concatenation across folds

After per-fold portfolio construction, concatenate `r_p_gated` and `r_p_uncond` across all OOS folds into two single series of total length `T_oos = Σ_fold |test_fold|`. These two single series feed [opdyke2007_ci](../../src/skie_ninja/inference/stats/sharpe_ci.py) and the Ledoit-Wolf 2008 differential bootstrap.

### 5.5 Non-orchestrator surfaces

- **[research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md)** — re-freeze `dataset_checksums` after Cell I backfill (independent of this resolution; tracked separately under P1-CYCLE6-REPRO-DATASET-CHECKSUM).
- **[src/skie_ninja/backtest/engine/walk_forward.py](../../src/skie_ninja/backtest/engine/walk_forward.py)** — no changes required; the engine is symbol-agnostic and the per-symbol loop happens above the engine call.
- **Provenance** — `ReproLog.run_metadata` must record the parsed `aggregation` block verbatim and the per-fold missing-bar counts from §5.2 step 3.

A new follow-up `P1-H050-DUAL-SYMBOL-ORCHESTRATOR` is added to track this (see [project_blocking_followups.md](C:/Users/skoir/.claude/projects/C--Users-skoir-Documents-SKIE-Universe/memory/project_blocking_followups.md)) — distinct from the bare P1-H050-UNIVERSE-ES-ONLY because the latter is a status flag, this one is the work-item with detailed acceptance criteria above.

## 6. What this forecloses

- **Family-3 multivariate Sharpe-test**: forecloses the Wright-Yam-Yung 2014 multivariate-T² path; not currently in the project's inference layer, so foreclosure cost is the marginal effort to plumb it later if the user judges the equal-weighted single-series view insufficient. Tracked as a Phase-1 follow-up `P1-H050-MULTIVARIATE-SR` (new) if the user wishes.
- **Risk-parity / capacity-proportional weighting (2c, 2d)**: foreclosed under the chosen rule. If the live-execution capital plan uses non-equal weights (likely, given the 2:1 capacity asymmetry), the *backtest* SR will not match the *live* SR even if both are in-sample-of-distribution. This is a known gap between research-Sharpe and execution-Sharpe; documented as a follow-up `P1-H050-EXECUTION-WEIGHT-MAP` (new) for the paper-trade phase.
- **Pooled-concatenation**: foreclosed (theoretically rejected; not a coherent portfolio construction).
- **Cross-fold concatenation stationarity (audit F-1-7 + F-2-6 decision rule added)**: §3.1 concatenates `r_p_gated` across all OOS folds into one length-`T_oos` series. The implicit assumption is that the concatenated series is stationary enough for the Opdyke 2007 Mertens-HAC variance estimator and Politis-White 2004 stationary bootstrap to be well-defined. Walk-forward folds have non-overlapping training and test windows so the per-fold parameter estimates differ; concatenation therefore stitches together returns generated under **different fitted models**. This is the standard walk-forward practice discussed in [López de Prado 2018, AFML §11 "The Dangers of Backtesting"](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) (which covers walk-forward, CV, and CPCV backtest paradigms) and is treated as a single-series inference target there, but the stationarity assumption is not formally tested. (Round-3 lit-check L-4 correction: prior r3 cited "AFML §7.4" — actual §7.4 is "The Purged K-Fold CV Class", not walk-forward concatenation; walk-forward is one of three paradigms discussed in Chapter 11.) **Decision rule (F-2-6 + F-3-5 refined):** add a fold-stationarity diagnostic to the run output: Augmented Dickey-Fuller (ADF, H0: unit root) and KPSS (H0: level-stationary) on each fold's `r_p_gated` and `r_p_uncond` separately; report per-fold p-values. The two tests have **opposite null hypotheses** so they form a confirmatory pair, not a single Bonferroni family — combining them under one Bonferroni alpha would conflate Type I error rates across reversed nulls. **Decoupled action thresholds** (Bonferroni applied within each test family separately):

- **ADF family**: alpha_ADF = 0.05 / (n_folds × 2 series) per family-wise error rate across all ADF tests in the run.
- **KPSS family**: alpha_KPSS = 0.05 / (n_folds × 2 series) per family-wise error rate across all KPSS tests in the run.

**Joint decision rule** (per fold per series, following the ADF+KPSS confirmatory-pair logic standard in time-series econometrics — see e.g. Kwiatkowski-Phillips-Schmidt-Shin 1992 or Hamilton 1994 *Time Series Analysis* §17 unit-root tests):

| ADF (rejects unit root at α_ADF?) | KPSS (rejects level-stationarity at α_KPSS?) | Conclusion | Action |
|---|---|---|---|
| Yes | No | Confidently stationary | Proceed |
| Yes | Yes | Mixed signal (possibly trend-stationary or fractional integration) | **Warn**; emit diagnostic |
| No | No | Mixed signal (low test power) | **Warn**; emit diagnostic |
| **No** | **Yes** | **Confidently non-stationary** | **Hard-stop** (concatenation is unsafe; non-recoverable error) |

Only the corner where ADF *fails to reject* unit-root AND KPSS *rejects* stationarity hard-stops; the other corners proceed with diagnostic warnings. Tracked as `P1-CYCLE6-FOLD-STATIONARITY`. (Round-3 quant F-3-5 correction: prior r3 lumped ADF and KPSS into one Bonferroni family and triggered hard-stop on ADF-alone — incorrect because ADF non-rejection is consistent with low power, not with confirmed non-stationarity.)
- **Per-symbol gating-frequency asymmetry (audit F-1-9 + F-2-6 decision rule added)**: under sub-rule 3.3a (hold inactive in cash) the gated portfolio's per-bar effective-leverage is `0.5 · I[ES gated active] + 0.5 · I[NQ gated active]`. If the HMM identifies the favored regime far more frequently for one symbol than the other (e.g., ES gates 30% of bars but NQ gates 8%), the gated portfolio is silently long-biased toward the more-frequently-active symbol. This asymmetry is invisible at the aggregate-Sharpe level but visible per-symbol. **Decision rule (F-2-6):** emit a per-symbol gate-firing-rate diagnostic (`gate_active_bars / total_bars`) in the run provenance for each fold. **Action threshold:** if the per-symbol firing-rate ratio exceeds 3:1 in any direction (i.e., one symbol's firing rate is more than 3× the other's), **warn** and emit a structural-asymmetry diagnostic — the rate-ratio bound is itself a Phase-1 follow-up that the user can re-tune empirically once the live run lands; 3:1 is a placeholder anchored in the implicit "no gross asymmetry" prior of sub-rule 2a, not an empirically calibrated threshold (follow-up `P1-GATE-RATE-RATIO-EMPIRICAL`). Tracked as part of `P1-H050-DUAL-SYMBOL-ORCHESTRATOR` acceptance criteria.

## 7. Audit-remediate trail

This memo is produced under the audit-remediate-loop skill (3-round cap per `~/.claude/CLAUDE.md`).

### Round 1 (r0 → r2 remediation; complete)

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
| L-3 | major | r0 §2.2 cited Sharpe 1966 + Sharpe 1994 jointly for portfolio-Sharpe construction; Sharpe 1994 explicitly disclaims SR for single-investment-return; the construction's heritage is Markowitz 1952 (per-bar weighted sum) + Sharpe 1966 / Lo 2002 (SR of single series). | Remediated §2.2 (split heritage citations); §3.2 item 3 (corrected attribution); §8 references (added Markowitz 1952; reframed Sharpe 1994 inclusion as for `T_H050` differential context only). |
| L-4 | major | r0 §3.1 wording "Politis-Romano stationary bootstrap (their primary recommendation; circular-block is a secondary variant)" was implementation-specific and risked over-claiming Ledoit-Wolf's footprint. | Remediated §3.1 alignment with literature-check phrasing. |
| L-5 | major | ADR-0005 silent on cross-fold HMM warm-start / state-threading; not in scope of this memo but flagged as supporting evidence for `P1-HMM-FOLD-WARM-START` blocker (Option B work). | Acknowledged in Round-1 audit trail; out-of-scope for this memo. |
| L-6 | major | r0 §3.2 item 4 over-stated "cross-correlation absorption" as automatic in Opdyke 2007's HAC formula; absorption happens at the portfolio-construction step, not within Opdyke. | Remediated §3.2 item 4 with portfolio-variance identity and explicit ordering. |
| L-7 | minor | r0 §8 references missing Politis-Romano 1994 (the actual stationary-bootstrap paper invoked by Ledoit-Wolf 2008). | Remediated §8 Tier-1 references (added Politis-Romano 1994 + Politis-White 2004). |
| L-8 | minor | r0 §3.2 item 5 implicit scale-invariance of SR under positive scalar capital base unverified. | Remediated §3.2 item 5 with explicit `SR(c·r) = sign(c)·SR(r)` verification. |
| Lit-completeness | minor | Tier-2 practitioner cross-check (Pav 2024 SharpeR vignette) not cited. | Remediated §8 Tier-2 references. |

**Disposition summary**: 2 critical (DOIs) + 6 major (F-1-1 through F-1-5, L-3, L-4, L-6) + 9 minor remediated. 1 major (L-5) acknowledged as out-of-scope (tracked under Option B `P1-HMM-FOLD-WARM-START` blocker). All `critical` fixes complete; no `critical` residuals.

### Round 2 (r2 → r3 remediation; complete)

**Auditors**: `quant-auditor` (verify Round-1 remediations + new defects) + `literature-check` (verify Round-1 citation corrections + Round-2 reference additions) — run in parallel.

**Findings (8 quant + 2 lit-check):**

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| F-2-1 | major | §5.3 cost-ordering claim was a straw-man: under linearity, per-symbol-cost-then-combine is *algebraically equivalent* to combine-then-deducted-with-correctly-weighted-blend. The argument for canonical ordering is operational/bookkeeping, not algebraic. | Remediated §5.3 (reframed as bookkeeping/canonical-ordering rationale; explicit equivalence shown; foot-gun clearly marked). |
| F-2-2 | major | §4.1.1 criterion 2 (no substrate-conditioned selection) unverifiable: ES+NQ Tier-2b substrate landed 2026-04-23, memo dated 2026-04-24 — user has had ≥1 day of substrate access. | Remediated §4.1.1 with (a) tightened temporal predicate + substrate-blind-rationale attestation, (b) Path-B-equivalence robustness gate at evidence-bar-run time (run 2c risk-parity with σ frozen from a pre-substrate public source as a robustness comparison). Converts unverifiable temporal claim into a falsifiable test. |
| F-2-3 | major | §5.1 config schema thin: no `schema_version`, no explicit `weights_vector`, no universe-cardinality assertion. Universe expansion (e.g., adding MES) would silently re-map "weights: equal" → 1/3 each. | Remediated §5.1: added `schema_version: h050_aggregation_v1`, `weights_vector: [0.5, 0.5]` indexed by universe order, `universe_cardinality_expected: 2`, plus three load-time validators (length match, label/vector consistency, sum=1). |
| F-2-4 | minor | §3.3 "measure-zero" claim ignored LightGBM leaf quantization. | Remediated §3.3: replaced with "empirically rare but not measure-zero"; added runtime `flat_bars_count` counter recommendation with 1% warning threshold. |
| F-2-5 | minor | §3.1 Ledoit-Wolf 2008 differential CI vs design.md §8 `opdyke2007_ci` binding — Path A's "no §8 substitution" precondition contestable. | Remediated §4.1.1 with joint-clarification scope note: differential CI is the natural inferential complement to the design.md-§1 differential statistic; per-side Opdyke binding preserved. |
| F-2-6 | minor | §6 stationarity + gating-asymmetry diagnostics had no decision rule. | Remediated §6: added Bonferroni-adjusted alpha + hard-stop/warn action thresholds for ADF/KPSS; added 3:1 firing-rate-ratio warn threshold (with `P1-GATE-RATE-RATIO-EMPIRICAL` follow-up to re-tune empirically). |
| F-2-7 | minor | §5.2 step 2 said "inner-join is a strict superset of trading-bar overlap" — wording slip; inner-join is the intersection. | Remediated §5.2: corrected to outer-join with explicit fill_null(0.0) on missing-symbol return columns; rationale aligned to 3.3a semantics. |
| F-2-8 | minor | §5.1 TypedDict provides no runtime validation. | Remediated §5.1: bound `AggregationSpec` to pydantic with `extra='forbid'` per InstrumentSpec pattern. |
| L-1 | minor | §8 Pav vignette title given as "SharpeR: A vignette"; actual is "Notes on the Sharpe ratio". Claim of "consolidation of Lo 2002 / Opdyke 2007 / Mertens 2002" overstated. | Remediated §8 references: corrected title; weakened claim to "covers Mertens and higher-order corrections; references Lo and Opdyke". |
| L-2 | minor | Mertens 2002 short-form title "Comments on variance of the IID estimator in Lo (2002)" missing word; full title is "Comments on the Correct Variance of Estimated Sharpe Ratios in Lo (2002, FAJ) When Returns Are IID". | Remediated §8 references: full title applied. |

**Disposition summary**: 3 major (F-2-1, F-2-2, F-2-3) + 7 minor (F-2-4 through F-2-8 + L-1 + L-2) — all remediated. No critical findings. Round-2 closes with all majors disposed of.

### Round 3 (final; cap reached per skill protocol)

**Auditors**: `quant-auditor` (verify F-2-1 through F-2-8 remediations land correctly; final gate-keep) + `literature-check` (verify L-1 + L-2 title corrections; spot-check no new citation drift introduced) — run in parallel.

**Findings (6 quant + 6 lit-check):**

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| L-3 | critical | r3 §4.1.1 cited "AFML §11.4 'Backtesting through cross-validation'" — actual §11.4 is "Backtesting Is Not a Research Tool"; the cross-validation chapter is §12 "Backtesting through Cross-Validation". | Remediated §4.1.1: §11.4 → §12; explicit Round-3 correction note inline. |
| L-4 | major | r3 §6 fourth bullet + §8 references cited "AFML §7.4" for walk-forward concatenation; §7.4 is "The Purged K-Fold CV Class", not walk-forward. Walk-forward is one of three paradigms in Chapter 11. | Remediated §6 fourth bullet (§7.4 → §11) and §8 Tier-2 references (replaced "§7.4 walk-forward concatenation" with §11/§12 paradigms framing); explicit Round-3 correction notes inline. |
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

**Residual risk surfaced (skill protocol — 3-round cap reached, must not iterate silently):**

- **Politis-Romano 1992 IMS Lecture Notes citation precision**: the project does not currently host a verified DOI for the IMS LN volume; the citation is narrative-only. If a future literature-check turns up a stable DOI it should be appended. This does not affect the load-bearing claim because LW2008 is the cited differential-CI source; the underlying block-bootstrap is implementation-bound to [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py).
- **Path-B robustness gate empirical anchoring**: the §4.1.1 sub-clause 2.b VIX/VXN-frozen-σ proposal is operationally cheap but its empirical equivalence to risk-parity-with-realized-vol has not been validated on real data; this is part of the H050 evidence-bar deliverable.
- **§6 ADF/KPSS Bonferroni decoupling power tradeoff**: decoupling the families correctly preserves Type I error control but accepts a lower power than a joint test would have at the same nominal alpha. Empirical validation deferred to first H050 walk-forward run; if the hard-stop is observed empirically, the user must judge whether the result is genuine non-stationarity or a power-control artifact.
- **`P1-MISSING-BAR-RATE-EMPIRICAL`** + **`P1-GATE-RATE-RATIO-EMPIRICAL`**: both 1% / 3:1 placeholder thresholds in §5.2 + §6 are anchor-priors, not empirically calibrated. Once the first H050 walk-forward lands, both should be re-tuned against the observed null distribution (e.g., bootstrap of randomized-gate runs).

Round-3 Final audit trail emitted at [docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md](../audits/audit_trail_2026-04-24_h050-aggregation-rule.md).

## 8. References

### Tier-1 (peer-reviewed)

- [Markowitz, H. 1952. "Portfolio Selection." *J. Finance* 7(1):77-91.](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) — foundational mean-variance framework; per-bar weighted-sum portfolio-return construction (§2.2 Family 2).
- [Sharpe, W. F. 1966. "Mutual Fund Performance." *J. Business* 39(1):119-138.](https://doi.org/10.1086/294846) — original reward-to-variability ratio definition (§2.2 Family 2).
- [Sharpe, W. F. 1994. "The Sharpe Ratio." *JPM* 21(1):49-58.](https://doi.org/10.3905/jpm.1994.409501) — included for completeness; explicitly *not* invoked here for the portfolio-Sharpe construction step (Sharpe 1994 frames SR as a differential-return statistic, applicable to `T_H050` the outer differential, not to the inner per-bar portfolio-Sharpe construction; see audit L-3).
- [Lo, A. W. 2002. "The Statistics of Sharpe Ratios." *Financial Analysts Journal* 58(4):36-52.](https://doi.org/10.2469/faj.v58.n4.2453) — Proposition 2 η(q) and HAC-adjusted single-series SR CI (§2 inference primitive).
- [Mertens, E. 2002. "Comments on the Correct Variance of Estimated Sharpe Ratios in Lo (2002, FAJ) When Returns Are IID." Working paper, U. Basel / WWZ.](https://ssrn.com/abstract=1019823) — non-iid variance correction; SSRN distinct from Opdyke 2007 (audit L-1; Round-2 L-2 title corrected).
- [Opdyke, J. D. 2007. "Comparing Sharpe ratios: So where are the p-values?" *J. Asset Management* 8(5):308-336.](https://doi.org/10.1057/palgrave.jam.2250084) — Mertens-HAC SR CI under stationary-ergodic returns; primary single-series CI per [src/skie_ninja/inference/stats/sharpe_ci.py](../../src/skie_ninja/inference/stats/sharpe_ci.py).
- [Politis, D. N. & Romano, J. P. 1994. "The Stationary Bootstrap." *J. American Statistical Association* 89(428):1303-1313.](https://doi.org/10.1080/01621459.1994.10476870) — primary stationary-bootstrap reference invoked by Ledoit-Wolf 2008 for differential SR CI.
- [Politis, D. N. & White, H. 2004. "Automatic block-length selection for the dependent bootstrap." *Econometric Reviews* 23(1):53-70.](https://doi.org/10.1081/ETC-120028836) — block-length selection used by [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py).
- [Hansen, P. R. 2005. "A Test for Superior Predictive Ability." *J. Business & Economic Statistics* 23(4):365-380.](https://doi.org/10.1198/073500105000000063) — multiple-strategy SPA test ([src/skie_ninja/inference/multipletest/hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py)).
- [Ledoit, O. & Wolf, M. 2008. "Robust performance hypothesis testing with the Sharpe ratio." *J. Empirical Finance* 15(5):850-859.](https://doi.org/10.1016/j.jempfin.2008.03.002) — studentized stationary-bootstrap CI for the *difference* of two Sharpe ratios; the canonical pairwise-SR CI invoked by [rules/quant-project.md](../../.claude/rules/quant-project.md) Inference clause and adopted here for `T_H050`.
- [Bailey, D. H. & López de Prado, M. 2014. "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality." *JPM* 40(5):94-107.](https://doi.org/10.3905/jpm.2014.40.5.094) — multiple-testing-after-data-inspection penalty; basis for §4.1.1 anti-HARK eligibility criterion.
- [Wright, J. A.; Yam, S. C. P.; Yung, S.-P. 2014. "A test for the equality of multiple Sharpe ratios." *J. Risk* 16(4):3-21.](https://doi.org/10.21314/JOR.2014.289) — multivariate SR test; foreclosed by sub-rule 2a but remains the reference for any future Family-3 work (DOI corrected per audit L-2; the J. Banking & Finance reference in r0 was spurious — that DOI resolved to an unrelated paper, audit L-1).

### Tier-2 (vetted technical reference)

- [Pav, S. E. 2024. "Notes on the Sharpe ratio." CRAN R package SharpeR (v1.4.0, 2024-12-18), vignette `SharpeRatio.pdf`.](https://cran.r-project.org/web/packages/SharpeR/vignettes/SharpeRatio.pdf) — covers Mertens and higher-order corrections; references Lo 2002 and Opdyke 2007. Useful practitioner cross-check against [src/skie_ninja/inference/stats/sharpe_ci.py](../../src/skie_ninja/inference/stats/sharpe_ci.py) numerical outputs (audit L-1 Round-2 title corrected).
- [López de Prado, M. 2018. *Advances in Financial Machine Learning*. Wiley.](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) — §11 "The Dangers of Backtesting" (walk-forward / CV / CPCV paradigms); §12 "Backtesting through Cross-Validation"; §15 "Understanding Strategy Risk". Tier-2 because not peer-reviewed in a journal sense; tier-1 is the cited Bailey-López de Prado 2014 *JPM* paper above. (Round-3 lit-check L-4 + L-3 correction: prior r3 incorrectly cited "§7.4 walk-forward concatenation"; §7.4 is "The Purged K-Fold CV Class".)

### Project artifacts

- [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md), [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml).
- [docs/research_notes/memo_option-b-data-coverage_2026-04-24.md](memo_option-b-data-coverage_2026-04-24.md) §11.1 — surfacing trigger.
- [src/skie_ninja/inference/stats/sharpe_ci.py](../../src/skie_ninja/inference/stats/sharpe_ci.py) — primitive constraint (single-series input).
- [rules/quant-project.md](../../.claude/rules/quant-project.md) — Inference clause (Lo 2002 / Opdyke 2007 / Ledoit-Wolf 2008 / Hansen 2005).
- [~/.claude/CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md) — evidence hierarchy, no-arbitrary-thresholds.

## 9. Decision surface

User must select:

1. **Aggregation family**: 2 (per-bar portfolio) — recommended; or 3 (per-symbol then aggregate); or substitute.
2. **Sub-rule within Family 2**: 2a (equal-weighted constant) — recommended; or 2b/2c/2d.
3. **One-sided-gated handling**: 3.3a (hold inactive in cash) — recommended; or 3.3b (renormalize).
4. **Pre-reg mechanics**: Path A (addendum file) — recommended; or Path B (design.md amendment + successor ID).

Default-recommendation bundle: **2a + 3.3a + Path A**.
