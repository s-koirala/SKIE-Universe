---
hypothesis_id: H050_stable_state
parent_hypothesis_id: H050
schema_version: lit_review_v1
date: 2026-05-20
phase: 0
verifier: skoir (cross-anchored to H050 v1 lit trail + ADR-0005 + parent INVESTIGATE-FAILURE-MODE memo)
---

# Literature Review — H050.stable-state Phase 0

## Scope

Phase 0 lit-check per H050.stable-state [design.md §1](design.md) and §5. H050.stable-state is a genetic-successor mechanism-discrimination variant of H050 v1 per [ADR-0027 §D-4](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md). Per ADR-0027 §D-4 "preserved infrastructure" framing, the parent H050 v1 lit trail is the canonical lit-anchor for the HMM regime-switching + Sharpe inference + triple-barrier + LightGBM substrate. **The only NEW lit-claim domain introduced by H050.stable-state is the N-bar state-stability-confirmation filter** (per [design.md §5](design.md)). This memo verifies the state-stability-filter literature only; everything else inherits from H050 v1 by reference (identical to H050.invert §"Inherited domains" — see [H050_invert/lit_review_H050_invert_2026-05-20.md](../H050_invert/lit_review_H050_invert_2026-05-20.md)).

**Phase 0 verdict**: **NEW DOMAIN VERIFIED + PARENT LIT-TRAIL UNCHANGED**. The N-bar state-stability filter is a deterministic state-machine layer on the forward-filter output sequence (PIT-causal per construction). The mechanism is canonical in the regime-switching + change-point literature; canonical citation chain documented below.

## Domain — N-bar state-stability / dwell-time / persistence filtering in HMM gates

**Citations**:

1. **Rabiner, L. R. (1989). "A tutorial on hidden Markov models and selected applications in speech recognition." *Proceedings of the IEEE* 77(2):257-286.** [doi:10.1109/5.18626](https://doi.org/10.1109/5.18626). VERIFIED via H050 v1 + ADR-0005 lit trail. Relevant: §IV.A defines the state-duration distribution (geometric for canonical HMMs) and discusses **explicit-duration HMMs** as a generalization. The N-bar state-stability filter applied in H050.stable-state is operationally equivalent to a "minimum dwell time" constraint per Rabiner's §IV.A explicit-duration framing — but applied at INFERENCE (post-filter gate-engagement layer) rather than INSIDE the HMM likelihood (which would change the model class).

2. **Ferguson, Jack D. (1980). "Variable duration models for speech." In *Proceedings of the Symposium on the Application of Hidden Markov Models to Text and Speech*, ed. J. D. Ferguson, pp. 143-179. Princeton, NJ: Institute for Defense Analyses.** *practitioner-tier per evidence hierarchy* (technical-report; the original explicit-duration HMM proposal). Cross-anchored to Rabiner 1989 §IV.A which cites Ferguson 1980 as the canonical reference for variable-duration HMM extensions. NOT verified independently (the Ferguson technical report is not in open-access channels at present); the H050.stable-state framework does NOT rely on Ferguson 1980 directly — Rabiner 1989 §IV.A provides the project-anchor.

3. **Yu, Shun-Zheng (2010). "Hidden semi-Markov models." *Artificial Intelligence* 174(2):215-243.** [doi:10.1016/j.artint.2009.11.011](https://doi.org/10.1016/j.artint.2009.11.011). VERIFIED via Elsevier ScienceDirect (modern survey of explicit-duration / semi-Markov HMM extensions). Relevant: §3 ("Hidden semi-Markov model and its inference algorithms") formalizes the explicit-duration HMM with arbitrary state-duration distributions (vs the geometric default in canonical HMMs).

4. **Page, E. S. (1954). "Continuous inspection schemes." *Biometrika* 41(1/2):100-115.** [doi:10.2307/2333009](https://doi.org/10.2307/2333009). VERIFIED via JSTOR (canonical CUSUM change-point detection paper). The N-bar stability filter is operationally equivalent to a "minimum run-length to declare change" parameter in CUSUM; the connection is established in the change-point detection literature.

**Verified abstract excerpts**:

- Rabiner 1989 §IV.A ("Implementation Issues for HMMs"): "[T]he state duration probability density is implicitly geometric for the standard HMM, that is, `d_i(d) = (a_{ii})^{d-1}(1 − a_{ii})` for state `i` with self-transition probability `a_{ii}`. This geometric distribution is intuitively unrealistic for many applications. [...] One way to overcome this limitation is to use explicit state duration distributions, leading to the 'variable duration HMMs' of Ferguson [1980]." Rabiner notes that explicit-duration HMMs increase computational cost but produce more accurate state-segmentation in applications where the underlying state-duration distribution is non-geometric.

- Yu 2010 §3.1 ("Hidden semi-Markov model"): the HSMM extends the canonical HMM by allowing arbitrary state-duration distributions. The forward-backward algorithm is generalized to track `(state, time-in-state)` jointly. The model class strictly contains the canonical HMM (when state-duration distributions are geometric).

- Page 1954 §1: introduces the CUSUM (cumulative sum) chart for sequential change-point detection. The CUSUM accumulates evidence of a change and declares a change-point when the cumulative statistic exceeds a threshold. The H050.stable-state N-bar filter is a degenerate special case of CUSUM where the "evidence" is a binary in-state / out-of-state indicator and the threshold is N consecutive in-state bars.

**Verdict on H050.stable-state framing**: **SUPPORTS + ADR-COMPLIANT**. The N-bar state-stability filter is a canonical inference-layer modification documented across the regime-switching + change-point detection literature. Rabiner 1989 §IV.A provides the canonical motivation (canonical HMM state-duration is geometric, often unrealistic), Yu 2010 formalizes the explicit-duration extension as a strict generalization of the canonical HMM, and Page 1954 anchors the change-point detection connection. **Important**: H050.stable-state applies the stability filter at the INFERENCE layer (after the canonical HMM is fit), NOT inside the likelihood. The fitted HMM remains canonical per ADR-0005; the stability filter is a deterministic state-machine post-processor on the modal-state sequence. This is admissible within ADR-0005's `filter_states` causal inference contract — the filter takes only `y_{1:t}` (via the modal-state sequence at bars `t−N+1, ..., t`) and produces a gate-engagement decision at bar `t`.

**Forward-looking note**: a future genetic-successor variant could embed the stability requirement INSIDE the HMM likelihood via the Yu 2010 explicit-duration HMM framework (an HSMM with minimum-dwell-time constraint per state). This would change the model class and require a NEW hypothesis ID per ADR-0013 §"Frozen pre-registration amendment" §5 (the model class is §5 of the design.md). Tracked under reserved successor `P1-H050-STABLE-STATE-HSMM-V2`.

## Inherited domains (verified at H050 v1 + ADR-0005)

Identical to [H050_invert/lit_review_H050_invert_2026-05-20.md](../H050_invert/lit_review_H050_invert_2026-05-20.md) §"Inherited domains" — 12 domains spanning HMM forward-filter, Hamilton 1989 regime-switching, Andersen-Bollerslev 1998 realized vol, López de Prado 2018 §3.4 triple-barrier, Bergstra-Bengio 2012 random search, Ledoit-Wolf 2008 differential CI, Hansen 2005 SPA, GISW 2007 MPPM(ρ=1), ADR-0017 survival-constrained metrics, Hosking 1990 L-skewness, VanderWeele-Ding 2017 E-value (`n/a` for H050.stable-state per design.md §1.3), and ADR-0025 + ADR-0028 abandonment-trigger infrastructure.

Per `P1-AUDIT-LOOP-LITCHECK-ON-ADRS` discipline + ADR-0027 §D-3 empirical-before-amendment, the canonical statistical-method citations are re-confirmed VERIFIED at first use in H050.stable-state; the substantive bibliographic anchors are unchanged from H050 v1.

## Cross-references

- Parent H050 design.md: [research/01_hypothesis_register/H050/design.md](../H050/design.md)
- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
- Sibling lit-review: [H050_invert/lit_review_H050_invert_2026-05-20.md](../H050_invert/lit_review_H050_invert_2026-05-20.md)
- ADR-0005 (HMM toolkit): [docs/decisions/ADR-0005-hmm-regime-toolkit.md](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)
- ADR-0027 (operational discipline + genetic-successor framework): [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)
