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
