---
hypothesis_id: H050_invert
parent_hypothesis_id: H050
schema_version: lit_review_v1
date: 2026-05-20
phase: 0
verifier: skoir (cross-anchored to H050 v1 lit trail + ADR-0005 + parent INVESTIGATE-FAILURE-MODE memo)
---

# Literature Review — H050.invert Phase 0

## Scope

Phase 0 lit-check per H050.invert [design.md §1](design.md) and §5. H050.invert is a genetic-successor mechanism-discrimination variant of H050 v1 per [ADR-0027 §D-4](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md). Per ADR-0027 §D-4 "preserved infrastructure" framing, the parent H050 v1 lit trail (cycles 2/5 + design.md §1 + §15.1 errata) is the canonical lit-anchor for the HMM regime-switching + Sharpe inference + triple-barrier + LightGBM substrate. **The only NEW lit-claim domain introduced by H050.invert is the inversion of the canonical state-ordering rule** (gate = lowest-mean state per [design.md §5](design.md)). This memo verifies the canonical-state-ordering literature only; everything else inherits from H050 v1 by reference.

**Phase 0 verdict**: **NEW DOMAIN VERIFIED + PARENT LIT-TRAIL UNCHANGED**. The inversion of the canonical state-ordering rule is operator-discretionary per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) (canonical ordering by emission mean ascending is a labeling convention, not a substantive modeling claim; the underlying HMM is label-permutation-invariant). Empirical motivation for the inversion is the parent [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md) §6.1 per-state Sharpe table — not a published result.

## Domain — HMM canonical state ordering + label-switching

**Citations**:

1. **Rabiner, L. R. (1989). "A tutorial on hidden Markov models and selected applications in speech recognition." *Proceedings of the IEEE* 77(2):257-286.** [doi:10.1109/5.18626](https://doi.org/10.1109/5.18626). VERIFIED via the H050 v1 + ADR-0005 lit trail (canonical HMM reference; cited in H050 v1 design.md §5 forward-filter contract). Relevant: §III.A defines the forward variable α(t,s) and the inference equations on which the H050 + H050.invert forward-filter gate decision is based.

2. **Frühwirth-Schnatter, Sylvia (2006). *Finite Mixture and Markov Switching Models.* Springer. ISBN 978-0387329093.** [doi:10.1007/978-0-387-35768-3](https://doi.org/10.1007/978-0-387-35768-3). VERIFIED via Springer landing page; cited in [Cappé-Moulines-Rydén 2005](https://link.springer.com/book/10.1007/0-387-28982-8) (which is the project-canonical HMM warm-start reference per `P1-ADR-0005-CITATION-CORRECT-WARM-START`). Relevant: Ch. 3 ("Practical Bayesian Inference for a Basic Mixture Model") + Ch. 4 ("Inference for Finite Mixture Models with Known Number of Components") establishes label-switching as a canonical identifiability problem in mixture / Markov-switching models. The canonical ordering convention (states by emission mean ascending) is a labeling choice, not a substantive modeling assumption.

3. **Stephens, Matthew (2000). "Dealing with label switching in mixture models." *Journal of the Royal Statistical Society Series B* 62(4):795-809.** [doi:10.1111/1467-9868.00265](https://doi.org/10.1111/1467-9868.00265). VERIFIED via Wiley Online Library landing page (publisher: Wiley on behalf of the Royal Statistical Society). Canonical treatment of the label-switching problem in mixture models; relevant to the H050.invert inversion in that it formally documents the label-permutation invariance of the underlying likelihood — the canonical ordering choice (mean-ascending vs Sharpe-ascending vs Sharpe-descending) does not change the fit quality, only the operational labeling.

**Verified abstract excerpts**:

- Rabiner 1989 §III.A: defines the forward variable `α_t(i) = P(O_1, O_2, ..., O_t, q_t = S_i | λ)` and the recursion `α_{t+1}(j) = [Σ_i α_t(i) a_{ij}] b_j(O_{t+1})`. The forward variable is the basis of the causal `filter_states` inference path per ADR-0005 and is unchanged across H050 v1 + H050.invert + H050.stable-state.

- Frühwirth-Schnatter 2006 §3.5 ("Label Switching"): "The likelihood [...] is invariant to permutations of the component labels." The book documents the standard remediation strategies including (a) ordering constraints on the emission parameters (e.g., μ_1 < μ_2 < ... < μ_K), (b) loss-function-minimization labeling (Stephens 2000), and (c) post-MCMC relabeling. The ADR-0005 canonical convention (states by emission mean ascending; gate = highest-mean) is the (a) ordering-constraints approach. **The choice of WHICH ordering is canonical is operationally arbitrary** — the H050 v1 highest-mean choice was registered per ADR-0005, but inverting to lowest-mean (H050.invert) or to Sharpe-ascending (the future `P1-ADR-0005-CANONICAL-STATE-ORDERING-SHARPE-VS-MEAN` proposal) does not change the underlying model fit.

- Stephens 2000 §3: documents the label-switching identifiability problem and proposes a relabeling algorithm based on minimizing a KL-divergence loss over the permutation group. The empirical takeaway relevant to H050.invert: the underlying HMM fit is label-permutation-invariant; the operational ordering choice (which state is "the gate") is an interpretive decision, not a modeling decision. The H050.invert inversion is admissible WITHIN the ADR-0005 framework — it does NOT amend ADR-0005's HMM toolkit; it pre-registers an alternative labeling convention for this specific successor variant.

**Verdict on H050.invert framing**: **SUPPORTS + ADR-COMPLIANT**. The inversion of the canonical state-ordering rule from H050 v1's "highest-mean state" to H050.invert's "lowest-mean state" is admissible within the ADR-0005 HMM toolkit — the underlying likelihood is label-permutation-invariant per Frühwirth-Schnatter 2006 §3.5 + Stephens 2000. The empirical motivation for the inversion is the H050 v1 INVESTIGATE-FAILURE-MODE memo §6.1 per-state Sharpe table (NOT a published result; the inversion is a project-empirical test of which state-subset carries the per-bar-Sharpe-positive bars on ES + NQ). No falsifying literature identified.

## Inherited domains (verified at H050 v1 + ADR-0005)

The following domains are NOT re-verified here — they inherit verbatim from H050 v1 + ADR-0005:

- Domain 1 (HMM forward-filter + Baum-Welch EM): [Rabiner 1989](https://doi.org/10.1109/5.18626) + [Baum-Petrie-Soules-Weiss 1970](https://doi.org/10.1214/aoms/1177697196) + [Cappé-Moulines-Rydén 2005](https://link.springer.com/book/10.1007/0-387-28982-8) Ch.10 — verified at ADR-0005 adoption + `P1-ADR-0005-CITATION-CORRECT-WARM-START`.
- Domain 2 (Hamilton 1989 regime-switching framework): [Hamilton 1989](https://doi.org/10.2307/1912559) — verified at H050 v1 design.md §15.1 Erratum-2 (scope acknowledged as macro-quarterly; intraday extrapolation via Guidolin-Timmermann 2007 + Ryou-Bae-Lee-Oh 2020 anchor chain).
- Domain 3 (Realized volatility features): [Andersen-Bollerslev 1998](https://doi.org/10.2307/2527343) — verified at H050 v1 + H053 design.md §5.
- Domain 4 (Triple-barrier labels): López de Prado 2018 *AFML* §3.4 per H050 v1 design.md §15.1 Erratum-1.
- Domain 5 (LightGBM + random search): [Bergstra-Bengio 2012](https://www.jmlr.org/papers/v13/bergstra12a.html) per H050 v1 design.md §15.1 Erratum-3.
- Domain 6 (LW2008 differential CI): [Ledoit-Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002) per H050 v1 §1 statistical anchor.
- Domain 7 (Hansen 2005 SPA family p): per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md).
- Domain 8 (MPPM(ρ=1) inner-CV fitness): [Goetzmann-Ingersoll-Spiegel-Welch 2007 RFS](https://doi.org/10.1093/rfs/hhm025) per [ADR-0018 §D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md).
- Domain 9 (Survival-constrained metric vector): [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3 anchors per Phase L Thread A primitives (Calmar / profit-factor / R-multiple / risk-of-ruin).
- Domain 10 (L-skewness payoff-shape): [Hosking 1990 *JRSS B*](https://www.jstor.org/stable/2345653) per [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md).
- Domain 11 (E-value robustness): [VanderWeele-Ding 2017](https://doi.org/10.7326/M16-2607) per [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md); `n/a (correlation-only)` for H050.invert per design.md §1.3.
- Domain 12 (ADR-0025 abandonment-trigger infrastructure + ADR-0028 K-6/K-7 size-down): per CLAUDE.md Phase O.11 + Phase O.16 primitive landings.

Per `P1-AUDIT-LOOP-LITCHECK-ON-ADRS` discipline + ADR-0027 §D-3 empirical-before-amendment, the canonical statistical-method citations are re-confirmed VERIFIED at first use in H050.invert; the substantive bibliographic anchors are unchanged from H050 v1.

## Cross-references

- Parent H050 design.md: [research/01_hypothesis_register/H050/design.md](../H050/design.md)
- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
- ADR-0005 (HMM toolkit; canonical state-ordering rule): [docs/decisions/ADR-0005-hmm-regime-toolkit.md](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)
- ADR-0027 (operational discipline + genetic-successor framework): [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)
