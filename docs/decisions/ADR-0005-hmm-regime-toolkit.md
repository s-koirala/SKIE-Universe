---
id: ADR-0005
title: Hidden Markov Model regime-inference toolkit
status: proposed
date: 2026-04-20
decision-owner: Lead researcher
supersedes: none
related:
  - plan/implementation-plan_2026-04-15.md §3, §4, §5
  - docs/decisions/ADR-0003-spa-vs-romanowolf.md
  - docs/decisions/ADR-0004-alpha-and-power-defaults.md
---

# ADR-0005 — Hidden Markov Model regime-inference toolkit

## Status

Proposed. To be accepted after the first three HMM-using hypotheses (H050, H051, H052) pass the gate defined in [ADR-0003](ADR-0003-spa-vs-romanowolf.md) and the diagnostics protocol below.

## Context

A growing share of the hypothesis backlog conditions on an unobserved discrete state (volatility regime, liquidity regime, flow regime). The Hidden Markov Model (HMM) is the canonical estimator for this setting: a discrete latent Markov chain with observation-conditional emission densities. The estimation and decoding algorithms are standard:

- Forward-backward and Baum-Welch EM ([Baum, Petrie, Soules, Weiss 1970, Ann Math Stat](https://doi.org/10.1214/aoms/1177697196)).
- Viterbi MAP decoding ([Viterbi 1967, IEEE Trans Inf Theory](https://doi.org/10.1109/TIT.1967.1054010)).
- Tutorial reference ([Rabiner 1989, Proc IEEE](https://doi.org/10.1109/5.18626)).

Economic precedent for regime-switching in financial time series:

- Two-regime Markov switching for GNP growth ([Hamilton 1989, Econometrica](https://doi.org/10.2307/1912559)).
- Regime-switching asset-allocation improvements ([Guidolin & Timmermann 2007, "Asset allocation under multivariate regime switching," J. Economic Dynamics and Control 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004)).
- Momentum/regime coupling ([Ryou, Bae, Lee, Oh 2020, "Momentum Investment Strategy Using a Hidden Markov Model," Sustainability 12(17):7031](https://doi.org/10.3390/su12177031)).

Without a canonical project-level decision, each hypothesis author would pick `n_states`, covariance type, initialization, and diagnostics independently, producing non-comparable runs and violating the no-magic-numbers rule in [rules/quant-project.md](../../../.claude/rules/quant-project.md).

## Options

### A. Gaussian HMM via Baum-Welch EM + Viterbi (classical)

Pros:
- Estimation and decoding are textbook; mature implementations (`hmmlearn`, `pomegranate`) with property tests upstream.
- Well-understood failure modes: local optima, label switching, weak stationarity.
- BIC-based model selection has a formal basis for mixture-type models.

Cons:
- Point estimates of the transition matrix; no posterior uncertainty on state structure.
- Poor handling of heavy-tailed emissions without explicit mixture components.

### B. Variational Bayes HMM (VBHMM)

Pros:
- Posterior over state structure; automatic shrinkage on over-specified `n_states`.
- Natural fit with walk-forward model selection via marginal likelihood.

Cons:
- Harder to validate reproducibly; VB optimum is not the MAP/ML optimum; more moving parts in priors.

### C. Hidden Semi-Markov Model (HSMM)

Pros:
- Explicit duration distribution — relaxes the geometric dwell-time assumption of HMM, which is empirically violated in vol-regime data.

Cons:
- Substantially higher parameterization; more data-hungry; fewer validated open-source implementations.

### D. Neural state-space (Deep Markov, structured SSM)

Pros:
- Handles non-linear, non-Gaussian emissions; can ingest high-dimensional features directly.

Cons:
- Opaque; many magic numbers; validation against the no-look-ahead rule is nontrivial; out of scope for a retail-capacity research program at this stage.

## Decision (proposed)

Adopt **Option A** as the primary toolkit. Options B, C, D are conditional fallbacks triggered by specific diagnostic failures of A, not default choices:

- If the dwell-time distribution under A departs materially from geometric on the training fold (KS or Cramér–von Mises against fitted geometric, BH-adjusted), promote to C.
- If EM restarts converge to materially different transition matrices (operationalized as max pairwise Frobenius distance exceeding the BIC-difference bound across restarts), promote to B for shrinkage.
- D is deferred pending a separate ADR.

### Hyperparameter governance

No hand-tuned values. Every run selects:

- `n_states` search grid is per-hypothesis and bounded below by 2 (single-state is not a regime model) and above by the largest K such that mean within-state sample size exceeds 30 × dim(emission) on the training fold (rule of thumb for Gaussian mixture identifiability; cite [Celeux & Durand 2008, Computational Statistics 23(4):541–564](https://doi.org/10.1007/s00180-007-0097-1)). Selection within the grid via BIC on the training fold **plus** cross-validated held-out log-likelihood across walk-forward folds. Ties broken by parsimony.
- `covariance_type` over `{spherical, diag, tied, full}` via the same joint criterion.
- Initialization: k-means++ on emission features. Random-restart count is not fixed: restart until the top-two fitted log-likelihoods agree within ε, with ε = 2 × SE of EM log-likelihood on a bootstrap re-fit of the training fold. An **operational** minimum of 5 restarts is imposed as an engineering floor — this is a Cycle-3 implementation choice, **not** a value prescribed by published literature. [Biernacki, Celeux, Govaert 2003, Comp. Stat. Data Anal. 41(3–4):561–575](https://doi.org/10.1016/S0167-9473(02)00163-9) motivates *why* multi-start EM is required for Gaussian mixtures (local-optima prevalence) but does not prescribe a universal restart count; the figure 5 here is chosen to balance coverage against cost pending the bootstrap-ε adaptive rule (tracked as follow-up P1-HMM-ADAPTIVE-RESTART).
- HMM-specific model-selection reference ([Celeux & Durand 2008](https://doi.org/10.1007/s00180-007-0097-1)).
- `em_tol`, `max_iter`, `seed`: pre-registered at hypothesis design time; no post-hoc adjustment.

All selection happens **inside** the walk-forward train fold so no information leaks forward, per [plan §4.1](../../plan/implementation-plan_2026-04-15.md).

### Fold-boundary state continuity (filter warm-start)

When the causal forward filter is applied across walk-forward fold boundaries, the test fold's first observation is processed with the **train-fold terminal filtered posterior** as its prior, propagated one transition step. Cold-starting the recursion from `log_pi` at every fold boundary discards the model's own sufficient statistic for future-state inference and biases early-test-fold posteriors toward the prior over O(dwell-time) bars for slow-mixing regimes.

**Canonical formula (one-step, no purge/embargo).** For the filtered posterior `α_T(i) = P(s_T = i, y_{1:T} | θ)` at the terminal training bar `T_train` and test-fold first observation `o_{T_train+1}`:

```
log_alpha_test[0, j] = logsumexp_i (log_alpha_train[T_train, i] + log_a_ij) + log_b_j(o_{T_train+1})
```

This is one application of the standard forward recursion ([Rabiner 1989 §III.A forward variable, eq. ~18-21](https://doi.org/10.1109/5.18626); follow-up `P1-HMM-VERIFIED-EQ-NUMBERS` tracks direct PDF verification of equation numbers) from the train-terminal posterior into the test-first observation.

**K-step generalisation (purged/embargoed walk-forward CV).** Under the López de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1-119-48208-6) §7.4.1 purging-and-embargo rule, the test-fold first index is offset from the train-fold terminal index by `K = test_idx[0] − train_idx[-1]` bars, where `K = purge_window + 1 ≥ 2`. The latent chain advances `K` transition steps between the last conditioned-on observation and the first scored observation, so the propagation step iterates the Hamilton prediction `K` times before applying the test emission:

```
log_alpha_prop^{(0)}_j = log_alpha_train[T_train, j]
log_alpha_prop^{(k)}_j = logsumexp_i (log_alpha_prop^{(k-1)}_i + log_a_ij)         for k = 1, ..., K
log_alpha_test[0, j]   = log_alpha_prop^{(K)}_j + log_b_j(o_{test_idx[0]})
```

`K=1` recovers the canonical one-step formula above. The `K`-step rule is the same Hamilton 1989 §3 / Hamilton 1994 §22.4 prediction step iterated `K` times, which is the correct sufficient-statistic propagation under the assumed first-order Markov chain — equivalent to multiplying the filtered probability vector by `A^K`. The implementation supplies `K` as a required argument (no default) so the caller cannot silently desynchronise the HMM-time clock from the bar-index clock; `K=0` is permitted only for the contiguous-sequence case (no purge, no skipped bars).

**Why this is not leakage.** The walk-forward leakage rule prohibits use of *future* data, not of *past in-sample* data. The López de Prado 2018, *Advances in Financial Machine Learning* (Wiley, ISBN 978-1-119-48208-6) §7 purging-and-embargo definition — already adopted project-wide — defines leakage strictly in terms of train-set rows that overlap with test labels in the *forward* direction; passing the train-fold terminal `α_T_train` into the test fold uses no test-period information whatsoever. Discarding `α_T_train` is not a leakage fix; it is information loss against the assumed model.

**Anchoring on the Hamilton-filter prediction step.** The propagation rule is the standard out-of-sample prediction step in the regime-switching econometrics literature, derived in:

- [Hamilton 1989, *Econometrica* 57(2):357-384](https://doi.org/10.2307/1912559), §3 "Inference about the Unobserved State Variable" — the original derivation of the filtered probability propagation rule used here.
- Hamilton 1994, *Time Series Analysis* (Princeton University Press, ISBN 978-0-691-04289-3), Ch. 22 "Modeling Time Series with Changes in Regime", §22.4 "Time Series Models of Changes in Regime" — textbook restatement of the Hamilton 1989 filter and its forecast step.
- Kim & Nelson 1999, *State-Space Models with Regime Switching: Classical and Gibbs-Sampling Approaches with Applications* (MIT Press, ISBN 978-0-262-11238-3), §4.2–4.3 — Kim filter restatement; the terminal filtered posterior is the sufficient statistic for forward inference under the assumed model.
- Frühwirth-Schnatter 2006, *Finite Mixture and Markov Switching Models* (Springer, ISBN 978-0-387-32909-3), §11.4–11.5 — Bayesian restatement of the same propagation rule.

These references establish the propagation rule for the *single-sample* forecast step. Applying that same rule across walk-forward CV fold boundaries is a project-level methodological commitment derived from the rule, not a separately attested recommendation in the cited textbooks. We found no published source that recommends cold-start at fold boundaries in this setting; readers aware of one should open a follow-up issue.

**Cold-start variants are not adopted.** Two alternatives were considered and rejected:

1. *Cold-start from `log_pi`* (the trained initial distribution). Discards `α_T_train`; introduces O(dwell-time) warm-up bias on every test fold for slow-mixing regimes; no first-principles justification under the assumed model.
2. *Cold-start from the stationary distribution `π* = lim_{n→∞} A^n π_0`*. Slightly less biased than (1) under stationarity but still discards the conditioning on `y_{1:T_train}`; the regime-switching econometrics literature uses the stationary distribution only when no prior data is available (start of sample).

**The choice is methodological, not a tunable hyperparameter.** Grid-searching the boundary rule against held-out OOS performance would be data-dredging on a question the model definition answers ex ante; it would also break pre-registration discipline since the boundary rule is part of the model, not the hyperparameter set.

**Implementation contract.** A `filter_states_from_prior(x, log_alpha_prior, *, n_propagation_steps)` public method on `GaussianHMM` takes the train-fold terminal log α (harvested via `terminal_log_alpha`) and the K-step gap and seeds the test-fold recursion via the K-step formula above. `n_propagation_steps` is a required keyword argument with no default — preventing the silent K=1 desynchronisation hazard when the orchestrator purges or embargoes bars between train terminus and test inception. The orchestrator computes `K = test_idx[0] − train_idx[-1]` from the fold's positional indices (`train_idx`, `test_idx`) before each test-fold call. Tracked under follow-up `P1-HMM-FOLD-WARM-START`.

**Warm-vs-cold filter regression diagnostic.** A passive per-fold diagnostic at [src/skie_ninja/models/regime/diagnostics.py](../../src/skie_ninja/models/regime/diagnostics.py) records the divergence between the production warm-start posterior (`filter_states_from_prior`) and the cold-start regression baseline (`filter_states`) at every walk-forward fold boundary. Primary metric: Hellinger distance (Le Cam 1986 (general Hellinger / total variation reference; specific inequality used here is [Tsybakov 2009, *Introduction to Nonparametric Estimation*, Springer ISBN 978-0-387-79051-0, §2.4](https://doi.org/10.1007/b13794)); [Le Cam 1986, *Asymptotic Methods in Statistical Decision Theory*, Springer ISBN 978-1-4612-9343-3](https://doi.org/10.1007/978-1-4612-4946-7)) — bounded in [0, 1] under the `H = (1/√2)·||√p − √q||₂` normalisation, proper metric on the simplex, well-behaved under near-deterministic transitions where the symmetric Kullback–Leibler divergence ([Kullback & Leibler 1951, *Ann. Math. Stat.* 22(1):79-86](https://doi.org/10.1214/aoms/1177729694)) diverges. Secondary metric: total-variation distance, with the Tsybakov 2009 §2.4 envelope `H² ≤ TV ≤ H·√(2 − H²)` (substituted under bounded Hellinger normalisation) asserted as a per-fold sanity flag. Precise lemma / equation pinning within Tsybakov 2009 §2.4 deferred to follow-up `P1-HMM-WARM-COLD-TSYBAKOV-PIN-VERIFY`. Threshold rule: raw values published; no regression-detection threshold in this iteration (no published rule located in the cited sources for HMM warm-vs-cold filter divergence). Sidecar emitted at `logs/reproducibility/{run_id}_warm_cold_diagnostic.json` (`warm_cold_diagnostic_v1` schema); SHA256 combined with the per-fold ledger roll-up into `ReproLog.model_hash` via `with_model_hash`, so a future warm-cold regression flips the run-level hash. Diagnostic is causal (test-fold cold path consumes only test-fold observations; warm path consumes the train-terminal posterior which is itself a function of train observations only) and does not enter the model output, prediction vector, or trading signal. Tracked under follow-up `P1-HMM-WARM-COLD-DIAGNOSTIC`.

## Identifiability hazards and remediation

- **Label switching** ([Stephens 2000, JRSS B](https://doi.org/10.1111/1467-9868.00265)): states are only identified up to permutation. Remediation: post-hoc canonical ordering by emission-mean rank (or by emission-variance rank for vol-regime models); the canonicalization rule is pre-registered per hypothesis.
- **Local optima**: addressed by the adaptive k-means++ restart policy above.
- **Latent-chain stability / weak stationarity** of the latent chain is assumed by Baum-Welch. Tested via [Carrasco, Hu & Ploberger (2014), "Optimal test for Markov switching parameters," Econometrica 82(2):765–784](https://doi.org/10.3982/ECTA8204) optimal test against Markov-switching parameter instability; [Hansen (1992), "The likelihood ratio test under nonstandard conditions: Testing the Markov switching model of GNP," J. Applied Econometrics 7(S1):S61–S82](https://doi.org/10.1002/jae.3950070506) supLM as a complementary test. Rejection of the null at α=0.05 triggers either (a) HSMM fallback or (b) segment-wise refit per the hypothesis's pre-registered rule.
- **Regime-separation significance**: Monte-Carlo permutation test that shuffles the time index before refitting; report empirical p-value on the BIC difference between fitted and permuted fits.
- **Smoothing diagnostic**: Hamilton filter smoothed probabilities inspected for bi-modality and absence of knife-edge flipping.

## Integration with existing infrastructure

HMM-specific metadata is written to a sidecar file `logs/reproducibility/{run_id}_hmm_selection.json` with fields `{n_states, covariance_type, init_strategy, em_tol, max_iter, n_restarts, seed, transition_matrix_sha256, emission_means_sha256}`. The SHA256 of the sidecar file is stored in `ReproLog.model_hash`. **No change to the frozen `ReproLog` dataclass**; backward compatibility with pre-2026-04-20 logs preserved. `ReproLog` in [src/skie_ninja/utils/reproducibility.py](../../src/skie_ninja/utils/reproducibility.py) is `@dataclass(frozen=True)` and its `verify()` enforces byte-identity against a canonical serialization — extending the dataclass would break every existing log's round-trip.

Follow-up note: any future extension of `ReproLog` itself requires a `schema_version` field bump and a migration path for prior logs; not proposed in this ADR.

Every HMM-using hypothesis inherits this ADR by reference in its `citations` frontmatter.

## Consequences

- No change to the SPA gate ([ADR-0003](ADR-0003-spa-vs-romanowolf.md)) or to alpha/power defaults ([ADR-0004](ADR-0004-alpha-and-power-defaults.md)); HMM hypotheses enter the universe on the same terms as any other.
- New Tier 2b "regime/state" section in the hypothesis backlog ([plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md)); see [ADR-0006](ADR-0006-scope-extension-hmm-0dte.md).
- A single point of failure if the upstream HMM library regresses; mitigated by pinning and by the fallback options B/C/D above.

## References

- [Baum, Petrie, Soules, Weiss 1970, Ann. Math. Stat.](https://doi.org/10.1214/aoms/1177697196)
- [Viterbi 1967, IEEE Trans. Inf. Theory](https://doi.org/10.1109/TIT.1967.1054010)
- [Rabiner 1989, Proc. IEEE](https://doi.org/10.1109/5.18626)
- [Hamilton 1989, Econometrica](https://doi.org/10.2307/1912559)
- [Stephens 2000, JRSS B](https://doi.org/10.1111/1467-9868.00265)
- [Guidolin & Timmermann 2007, JEDC 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004)
- [Ryou, Bae, Lee, Oh 2020, Sustainability 12(17):7031](https://doi.org/10.3390/su12177031)
- [Biernacki, Celeux, Govaert 2003, Comp. Stat. Data Anal. 41(3–4):561–575](https://doi.org/10.1016/S0167-9473(02)00163-9)
- [Celeux & Durand 2008, Computational Statistics 23(4):541–564](https://doi.org/10.1007/s00180-007-0097-1)
- [Carrasco, Hu & Ploberger 2014, Econometrica 82(2):765–784](https://doi.org/10.3982/ECTA8204)
- [Hansen 1992, J. Applied Econometrics 7(S1):S61–S82](https://doi.org/10.1002/jae.3950070506)
- Chan 2013, *Algorithmic Trading: Winning Strategies and Their Rationale*, Wiley, ISBN 978-1118460146 (publisher-page ISBN confirmation pending).
- West & Harrison 1997, *Bayesian Forecasting and Dynamic Models*, 2nd ed., Springer, ISBN 978-0387947259 (publisher-page ISBN confirmation pending).
- Hamilton 1994, *Time Series Analysis*, Princeton University Press, ISBN 978-0-691-04289-3 (publisher-page ISBN confirmation pending). Ch. 22 "Modeling Time Series with Changes in Regime".
- Kim & Nelson 1999, *State-Space Models with Regime Switching: Classical and Gibbs-Sampling Approaches with Applications*, MIT Press, ISBN 978-0-262-11238-3 (publisher-page ISBN confirmation pending). §4.2–4.3.
- Frühwirth-Schnatter 2006, *Finite Mixture and Markov Switching Models*, Springer, ISBN 978-0-387-32909-3 (publisher-page ISBN confirmation pending). §11.4–11.5.
- [Le Cam 1986, *Asymptotic Methods in Statistical Decision Theory*, Springer-Verlag, ISBN 978-1-4612-9343-3](https://doi.org/10.1007/978-1-4612-4946-7) — general Hellinger / total variation reference (warm-vs-cold filter diagnostic); the specific inequality used at runtime is Tsybakov 2009 §2.4.
- [Tsybakov 2009, *Introduction to Nonparametric Estimation*, Springer, ISBN 978-0-387-79051-0, §2.4](https://doi.org/10.1007/b13794) — distances between distributions; primary anchor for the Hellinger / TV inequalities used in `le_cam_envelope_holds`. Precise lemma / equation pinning tracked under follow-up `P1-HMM-WARM-COLD-TSYBAKOV-PIN-VERIFY`.
- [Kullback & Leibler 1951, *Ann. Math. Stat.* 22(1):79-86](https://doi.org/10.1214/aoms/1177729694) — KL divergence (discussed and rejected as primary metric).
- [Cover & Thomas 2006, *Elements of Information Theory*, 2nd ed., Wiley, ISBN 978-0-471-24195-9, §2.3](https://doi.org/10.1002/047174882X) — KL divergence unboundedness rationale.
