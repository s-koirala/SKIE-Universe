---
id: ADR-0022
title: Mandatory causal-mechanism vs correlation-only annotation in every pre-registered design.md
status: proposed
date: 2026-05-12
supersedes: none
amends: ADR-0013 §3 (KPI report card structure), ADR-0017 §3 (promotion-decision-rule), ADR-0018 (BOCD decay-detector priors)
---

## Context

The first three production walk-forward runs to emit KPI report cards under ADR-0013 + ADR-0017 produced a point-estimate ordering that is consistent with — but not yet inferentially powered by — a causal-vs-correlation gradient in the underlying alpha hypothesis:

| Hypothesis | Alpha mechanism as written in §1 | Realized OOS (best arm × symbol) | T_H CI vs zero |
|---|---|---|---|
| H050 | HMM identifies states with positive empirical return mean in training; gating is the new content | -81% (ES gated) / -84% (NQ gated) | excludes zero negatively |
| H052a | First-hour ORB on CME futures gated by HMM regime state | NQ unconditional +10.61% / gated near-flat | covers zero (non-significant null) |
| H053 | Multi-timeframe regression with explicit opening-bar mediation | NQ LightGBM +10.8% / max-DD 3.7% | "marginal" (Sharpe; Path B leakage-clean) |

H050's mechanism, as written, identifies no market participant, no specific behavior, no incentive, and no time-of-day trigger — the HMM is a statistical decomposition that finds states with positive empirical return mean in the training window. Nothing in the design.md anchors *why* those states should continue to have positive return mean out-of-sample. The catastrophic OOS is consistent with the absence of such an anchor: a correlation-only signal has no theoretical commitment that survives regime change.

H052a's underlying ORB is partially causally identified. Crabel 1990 (*practitioner*) and [Holmberg-Lönnbark-Lundström 2013 *Finance Research Letters* 10(1):27-33](https://doi.org/10.1016/j.frl.2012.09.001) attribute first-hour range expansion to overnight-information-discovery + opening-auction-induced volume clustering; this is a specific behavioral mechanism with identifiable participants (overnight-information-receiving traders releasing positions into the morning auction) and a specific time-of-day trigger (09:30 ET CME open). The HMM regime gate stacked on top of that mechanism is correlation-only — the unconditional arm's empirical strength and the gated arm's flat performance are consistent with the causal layer carrying the signal and the correlation layer adding noise.

H053's design.md §1 already invokes [Imai-Keele-Tingley 2010 *Psychological Methods*](https://doi.org/10.1037/a0020761) mediation, naming the opening-15-min mediator as the proposed causal channel between multi-timeframe state and the 09:45→10:30 ET predictand. The design.md §1 critical interpretive note explicitly admits sequential ignorability is heroic at 1-min-bar futures grain — but the act of writing the mediator down forces the design to enumerate *who* trades during the opening 15 min, *what* opening-auction inventory imbalance they discharge, *why* the post-auction 45 min reabsorbs that imbalance, and *when* the mechanism is expected to operate (RTH only, no FOMC days). H053 is the only one of the three that meets the four-field specification this ADR mandates below.

n=3 hypotheses is not inferentially powered to establish that causal-mechanism status predicts OOS robustness — but the qualitative ordering motivates a discipline that **forces every future hypothesis to declare its claim type at pre-registration time**, so that the inferential test of "do causal-mechanism strategies outperform correlation-only strategies in OOS-vs-IS-Sharpe degradation" can be run on a growing sample as the hypothesis register accumulates.

The discipline this ADR imports is not novel. The population-health-rules at `~/.claude/rules/population-health.md` already require DAG declaration before adjustment-set selection, back-door criterion application per [Pearl 2009](https://www.cambridge.org/9780521895606) (*practitioner*), and E-value sensitivity per [VanderWeele-Ding 2017](https://doi.org/10.7326/M16-2607) for every primary estimate. The quant-project rules at `~/.claude/rules/quant-project.md` currently do not invoke causal-inference machinery at all — alpha hypotheses are written as predictive feature → predictand associations with no required mechanism specification. ADR-0022 closes the gap.

[Athey-Imbens 2019 *Annual Review of Economics* 11:685-725](https://doi.org/10.1146/annurev-economics-080217-053433) argue that predictive ML alone is insufficient for policy-relevant inference because predictive accuracy in-distribution does not generalize to interventional or counterfactual questions. [Imbens-Rubin 2015](https://www.cambridge.org/9780521885881) (*practitioner*) and [Hernán-Robins 2020](https://www.hsph.harvard.edu/miguel-hernan/causal-inference-book/) (*practitioner*) supply the potential-outcomes machinery. [VanderWeele 2015](https://global.oup.com/academic/product/explanation-in-causal-inference-9780199325870) (*practitioner*) supplies the mediation-and-interaction extension that H053 implicitly imports. [López de Prado 2018 *AFML*](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) §§17-18 (*practitioner*) supplies structural-break (§17 "Structural Breaks": CUSUM + explosiveness tests) and information-theoretic (§18 "Entropy Features") machinery that this ADR interprets as carrying more causal content than purely statistical features; the causal-vs-predictive framing itself is the ADR's editorial gloss on those chapters' content, not a verbatim claim of LdP 2018.

## Decision

**§1.** Every pre-registered design.md from 2026-05-12 forward MUST contain a new subsection numbered §1.3 (slotting between §1 hypothesis statement and §1.4 universe-binding; if the design.md template numbers differ, the annotation slots immediately after the hypothesis-statement subsection and before any universe-binding subsection) titled "Causal-mechanism vs correlation-only annotation" with three required fields:

1. **Claim type**. Exactly one of three exclusive labels: `causal-mechanism`, `correlation-only`, or `hybrid` (causal-mechanism upstream + correlation-only refinement; the hybrid label is admissible only when the upstream and refinement layers are separable in §5 such that the upstream layer can be evaluated in isolation as a robustness exhibit).

2. **Mechanism description** (required for `causal-mechanism` and `hybrid`; forbidden for `correlation-only`). A 2-4 sentence specification of four fields:
   - *Who*: which market participants are proposed as the causal actors (e.g., "overnight-information-receiving asset managers", "opening-auction inventory-clearing market makers", "stop-running short-term liquidity providers").
   - *What*: which observable behavior the participants execute (e.g., "discharge accumulated overnight inventory into the 09:30-09:45 ET auction window").
   - *Why*: which incentive drives the behavior (e.g., "minimize overnight gap risk subject to fiduciary constraints requiring close-to-close benchmarking").
   - *When*: which time-of-day or regime conditions trigger the mechanism (e.g., "RTH session open only; suspended on FOMC days per Lucca-Moench 2015 pre-announcement drift").

Failure to specify all four fields = automatic downgrade to `correlation-only` at the audit-remediate-loop verification step (per the audit-discipline machinery already established in CLAUDE.md §Phase I H055 staging audit precedent).

3. **E-value or robustness anchor** (required for `causal-mechanism` and `hybrid`; forbidden for `correlation-only`). A primary-source citation justifying the proposed mechanism's robustness to confounding. Where the underlying observational design admits an E-value computation per [VanderWeele-Ding 2017](https://doi.org/10.7326/M16-2607), the E-value is reported as a point estimate with the unmeasured-confounder RR that would nullify the estimate. Where E-value is not computable (e.g., a strict causal-mechanism claim grounded in microstructural theory rather than an observational mediation), a primary-source citation to the canonical mechanism description is required, and the design.md §1.3 must state explicitly "E-value not computable; robustness rests on [citation]".

**§2.** The annotation is NOT a binding gate. ADR-0013 §"no binding gates" is preserved verbatim — correlation-only strategies still progress through every stage transition including `ninjascript-implemented`. The annotation is a KPI propagated to the KPI report card and a load-bearing input to the operator's promotion-decision-rule.

**§3.** A new column `presumed-shelf-life-{long,short}` is added to the operator's promotion-decision-rule under ADR-0017 §3, derived deterministically from the annotation:
- `causal-mechanism` → `presumed-shelf-life-long`
- `hybrid` → `presumed-shelf-life-long` (with the qualifier that the correlation-only refinement layer carries the shelf-life-short risk; tracked as an inline annotation in the report card)
- `correlation-only` → `presumed-shelf-life-short`

The column is informational at the promotion decision; it does not override the ADR-0017 four-metric Pareto-front operator review. It feeds into the BOCD decay-detector calibration under §5 below.

**§4.** A new KPI annotation `claim-type-{causal-mechanism,correlation-only,hybrid}` is added to every report card emitted from 2026-05-12 forward. Annotation grammar follows the existing ADR-0013 §B + ADR-0014 §3.2 dot-separated single-line conventions in the report card §"Methodological-correctness annotations" footer. The annotation propagates verbatim from the pre-reg §1.3 — it is not recomputed at report-card-emission time.

**§5.** Inner-CV hyperparameter selection MAY weight causal-mechanism strategies higher when MPPM(ρ=1) values (per ADR-0018) are tied within 1σ. The tiebreaker rule is exposed as a config-yaml flag `inner_cv_causal_tiebreaker: {enabled, disabled}` (default disabled at this ADR's adoption to preserve backward compatibility with frozen pre-regs; the flag is enabled per-hypothesis at pre-registration time only). When enabled and a tie within 1σ on MPPM occurs, the `causal-mechanism` arm is preferred over `hybrid`, and `hybrid` over `correlation-only`. MPPM remains the primary fitness criterion; this is a strict tiebreaker.

**§6.** The BOCD decay detector per ADR-0018 applies a *narrower* run-length prior to `correlation-only` strategies (faster decay-detection trigger; reflects the presumed-fragile prior) and a *wider* prior to `causal-mechanism` strategies (slower trigger; reflects the presumed-stable prior). `hybrid` strategies inherit the wider prior on the upstream causal layer and the narrower prior on the refinement layer; aggregation rule for the composite is deferred. Specific narrower/wider calibration is deferred to follow-up `P1-BOCD-CAUSAL-PRIOR-CALIBRATION`; until that follow-up lands, BOCD uses the existing ADR-0018 default prior for all strategies regardless of claim type.

## Consequences

**Positive.**

The annotation forces every pre-registered hypothesis to engage with the causal-vs-predictive distinction at design time, before substrate is touched. This eliminates the post-hoc rationalization pathology where a correlation-only signal is retroactively re-described as causal after positive backtest results arrive. The four-field specification (who/what/why/when) is operationalizable in the audit-remediate-loop at staging — auditors can verify each field against primary sources and downgrade non-compliant designs to `correlation-only`.

The annotation supplies a covariate for the longer-horizon meta-analysis question: do causal-mechanism strategies degrade less in OOS-vs-IS-Sharpe than correlation-only strategies? With n=3 hypotheses at adoption time the question is not powered; with the hypothesis register's expected growth rate (~6-8 hypotheses per quarter at current pace) the question becomes inferentially testable within 2-3 quarters.

The shelf-life column gives the operator an explicit prior on retirement timing per ADR-0013 §"retirement is a metadata transition", complementing the BOCD-derived posterior. Strategies labeled `correlation-only` at pre-reg time enter live with a documented expectation of shorter shelf-life, which protects against the loss-aversion pathology where strategies that should have been retired are held past their decay because the operator anchored on the in-sample evidence.

The H053 causal-mechanism annotation surfaces the existing latent causal discipline in that hypothesis as a load-bearing project-level artifact rather than a per-hypothesis idiosyncrasy.

**Negative.**

The annotation expands the audit-remediate-loop surface at staging. Audit-remediate-loops will need to verify primary-source claims for the *who/what/why/when* fields, which adds literature-check load. Followed disciplinarily, this is the intended effect; loosely applied, it becomes a checkbox the staging audit cannot meaningfully verify.

The `hybrid` label admits a continuum of mechanism-quality between pure-causal and pure-correlation; the binary downgrade rule (any field missing → correlation-only) loses gradient information. A follow-up could introduce a numeric mechanism-quality score, but the ADR adopts the discrete three-label scheme at outset to minimize gaming the score.

The BOCD prior narrowing for correlation-only strategies creates an asymmetric retirement-detection rate. A genuinely robust correlation-only signal would be retired faster than warranted by its true decay; this is conservative-by-design but accepts a known false-positive-retirement rate.

The ADR cannot retroactively force §1.3 annotations into frozen pre-regs without violating ADR-0013 §"Frozen pre-registration amendment §1-§7 immutability". The retroactive cascade per `P1-ADR-0022-DESIGN-MD-CASCADE` adds the annotation as a project-level addendum at the hypothesis-register-folder level (not as a §1.3 edit) for H050/H051/H052a/H052b/H053/H054/H055; the immutable §1 statement is preserved verbatim.

**Retroactive labels** (operator-confirmable; expressed as project-level addenda per the immutability constraint):

| Hypothesis | Initial claim-type label | Mechanism summary |
|---|---|---|
| H050 | `correlation-only` | HMM identifies positive-empirical-return states; no participant/behavior/incentive/timing chain specified |
| H051 | `hybrid` | Kalman pairs: basis-mean-reversion mechanism (causal upstream); HMM regime gate (correlation refinement) |
| H052a | `hybrid` | ORB: overnight-info-discovery + opening-auction mechanism (causal upstream); HMM gate (correlation refinement) |
| H052b | `hybrid` | Same as H052a transposed to QQQ 0DTE long-call overlay |
| H053 | `causal-mechanism` | Mediation framework explicitly tests opening-bar mediator causal chain (Imai-Keele-Tingley 2010) |
| H054 | `hybrid` | Anti-gated stress-state: behavioral-stress-amplification mechanism (causal upstream); gate-firing rule (correlation refinement) |
| H055 | `hybrid` | Wick-rejection: stop-run / accumulation mechanism (causal upstream); deterministic trend-strength gate (correlation refinement) |

**Follow-ups.**

- `P1-ADR-0022-DESIGN-MD-CASCADE`. Apply the project-level addenda for H050/H051/H052a/H052b/H053/H054/H055 with operator confirmation of each initial label. Non-blocking; can lag by one stage transition.
- `P1-BOCD-CAUSAL-PRIOR-CALIBRATION`. Empirically calibrate the narrower/wider run-length priors against historical decay events; until calibration lands, BOCD uses the ADR-0018 default prior for all strategies. Non-blocking for ADR-0022 adoption.
- `P1-CAUSAL-DAG-DESIGN-MD-TEMPLATE`. Extend [docs/templates/hypothesis_design.md](../templates/hypothesis_design.md) with a §1.3 stub matching this ADR's three-field specification + an optional §1.3.1 DAG declaration (dagitty syntax or text) for hypotheses where the back-door criterion is operationalizable. Blocking before next new pre-reg.
- `P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL`. Implement an E-value computation primitive at `src/skie_ninja/inference/causal/e_value.py` per VanderWeele-Ding 2017 §3 for futures-strategy applications where the observational design admits the construction. Non-blocking.
- `P1-CAUSAL-MECHANISM-FAILURE-MODE-TAXONOMY`. Build a taxonomy of failure modes specific to correlation-only strategies (regime change without participant change; participant change without regime change; cost-model drift; competition-driven decay) to inform the BOCD prior calibration. Non-blocking.
- `P1-QUANT-PROJECT-RULES-CAUSAL-IMPORT`. Amend `~/.claude/rules/quant-project.md` to mirror the population-health rules' causal-inference discipline: DAG declaration where operationalizable, back-door criterion for adjustment-set selection, E-value sensitivity for primary estimates. Blocking before next new pre-reg.

## References

- [Athey-Imbens 2019 *Annual Review of Economics* 11:685-725](https://doi.org/10.1146/annurev-economics-080217-053433) "Machine Learning Methods That Economists Should Know About" — ML + causal inference review; the "predictive ML alone is insufficient for interventional questions" framing.
- Crabel 1990 *Day Trading with Short-Term Price Patterns and Opening Range Breakout*. Traders Press. *Practitioner* — first-hour ORB mechanism.
- [Hernán-Robins 2020 *Causal Inference: What If*](https://www.hsph.harvard.edu/miguel-hernan/causal-inference-book/). Chapman & Hall, open-access manuscript. *Practitioner* — canonical modern potential-outcomes treatment.
- [Holmberg-Lönnbark-Lundström 2013 *Finance Research Letters* 10(1):27-33](https://doi.org/10.1016/j.frl.2012.09.001) "Assessing the profitability of intraday opening range breakout strategies" — opening-range overnight-information-discovery mechanism.
- [Imai-Keele-Tingley 2010 *Psychological Methods* 15(4):309-334](https://doi.org/10.1037/a0020761) — causal mediation; H053 anchor.
- [Imbens-Rubin 2015 *Causal Inference for Statistics, Social, and Biomedical Sciences*](https://www.cambridge.org/9780521885881). Cambridge UP. *Practitioner* — potential-outcomes foundation.
- [Lucca-Moench 2015 *J Finance* 70(1):329-371](https://doi.org/10.1111/jofi.12196) — FOMC pre-announcement drift; basis for FOMC-day suspension rule.
- [López de Prado 2018 *Advances in Financial Machine Learning*](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086). Wiley §§17-18. *Practitioner* — causal-vs-predictive distinction in financial ML.
- [Pearl 2009 *Causality: Models, Reasoning and Inference* 2nd ed.](https://www.cambridge.org/9780521895606). Cambridge UP. *Practitioner* — do-calculus and back-door criterion.
- [VanderWeele 2015 *Explanation in Causal Inference*](https://global.oup.com/academic/product/explanation-in-causal-inference-9780199325870). Oxford UP. *Practitioner* — mediation and interaction extension.
- [VanderWeele-Ding 2017 *Ann Intern Med* 167(4):268-274](https://doi.org/10.7326/M16-2607) — E-value sensitivity; canonical in population-health rules.
- [ADR-0013 permanent-exploration](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — no binding gates; immutability of §1-§7.
- [ADR-0017 survival-constrained optimization paradigm](ADR-0017-survival-constrained-optimization-paradigm.md) — promotion-decision-rule extended with shelf-life column.
- [ADR-0018 regime-conditional aggressive-growth paradigm](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — BOCD decay detector; prior-calibration entry-point for §6.
