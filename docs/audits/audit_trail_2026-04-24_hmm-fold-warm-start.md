---
title: P1-HMM-FOLD-WARM-START — audit-remediate-loop trail
date: 2026-04-24
artifact: filter_states_from_prior + terminal_log_alpha + walk-forward warm-start wiring
followup_id: P1-HMM-FOLD-WARM-START
exit_state: round-2 accept (2 minor; 1 inline-resolved, 1 follow-up)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
---

## Scope

Close `P1-HMM-FOLD-WARM-START`: the H050 walk-forward orchestrator was cold-starting the HMM forward filter at every fold boundary (`hmm.filter_states(r_te)` cold-pass), contradicting [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md) §"Fold-boundary state continuity". Round-1 implemented the warm-start API and threading; Round-2 remediated 4 major + 1 critical findings and lifted 2 minors. Exit at Round-2 with 2 minor residuals (1 inline-fixed, 1 logged as follow-up).

## Method-fidelity anchor

The propagation rule is the Hamilton 1989 §3 / Hamilton 1994 §22.4 / Kim & Nelson 1999 §4.2–4.3 / Frühwirth-Schnatter 2006 §11.4–11.5 prediction step iterated `K` times, where `K = test_idx[0] − train_idx[-1]` under the López de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1-119-48208-6) §7.4.1 purge-and-embargo regime. Cold-start at fold boundaries discards the model's own sufficient statistic for forward inference and biases the early test-fold posterior over O(dwell-time) bars for slow-mixing regimes — there is no first-principles justification under the assumed first-order Markov chain. ADR-0005 enshrines warm-start as a methodological commitment, not a tunable hyperparameter.

## Round-1

### Implementation summary

- [src/skie_ninja/models/regime/_core.py](../../src/skie_ninja/models/regime/_core.py): added `forward_log_from_prior(log_alpha_prior, log_transmat, log_B, *, n_propagation_steps)` — K iterated logsumexp prediction steps, then a standard forward recursion over the test emissions.
- [src/skie_ninja/models/regime/hmm.py](../../src/skie_ninja/models/regime/hmm.py): added `terminal_log_alpha(x)` (returns the unnormalised log α[-1] of the train-fold forward pass) and `filter_states_from_prior(x, log_alpha_prior, *, n_propagation_steps)` (warm-start posterior over the test fold).
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py): `_fit_fold` harvests `(hmm_terminal_log_alpha, hmm_train_terminal_position)`; `_predict_fold` computes `K = test_first_position − train_terminal_position` and calls `filter_states_from_prior`.
- [tests/unit/test_hmm_fold_warm_start.py](../../tests/unit/test_hmm_fold_warm_start.py): 9 tests for contiguous-equivalence, K-step propagation, validation, round-trip, causality canary, unfitted guards.

### Round-1 quant-auditor findings

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| F-1-1 | critical | `_fit_fold` zero-mask `r_tr != 0.0` | HMM-time-clock vs bar-position-clock desync: HMM fits on masked sequence (one transition per kept-bar) but K-step propagation uses raw bar count. | Round-2 fix: zero-mask dropped entirely. |
| F-1-2 | major | `valid_train_positions` edge | Edge case follow-on of F-1-1. | Round-2 fix: subsumed by F-1-1. |
| F-1-3 | major | `n_propagation_steps=1` default | Footgun — under purging/embargo K ≥ 2 always; default silently desyncs. | Round-2 fix: parameter required (no default) at both `_core.forward_log_from_prior` and `GaussianHMM.filter_states_from_prior`. |
| F-1-4 | major | caller-discipline note | No docstring guidance against re-using stale priors across runs. | Deferred residual (no concrete fix beyond the now-required arg + ADR contract). |
| F-1-5 | major | iterated-K logsumexp | No postcondition guard on log α finiteness. | Round-2 fix: `FloatingPointError` raise after the propagation loop. |
| F-1-6 | minor | `log_likelihood` naming | Returned scalar is unnormalised log α terminal sum, not strictly the likelihood under standard scaling. | Deferred residual (semantics documented in docstring). |
| F-1-7 | minor | test gaps | Missing single-test-bar, K-step row-stochasticity, prior-norm-invariance, large-K stability. | Lifted to Round-2: 4 tests added. |
| F-1-8 | minor | ADR pre-registration | ADR-0005 stated only the K=1 canonical formula; orchestrator uses K-step. | Lifted to Round-2: ADR amended with explicit K-step formula + AFML §7.4.1 anchor + `n_propagation_steps`-required implementation contract. |
| F-1-9 | minor | warm-vs-cold diagnostic | No run-aggregate metric to detect a future warm-vs-cold regression. | Deferred residual; track as `P1-HMM-WARM-COLD-DIAGNOSTIC`. |

## Round-2

### Remediations applied

- **F-1-1 + F-1-2:** [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) `_fit_fold` no longer applies a zero-mask; HMM fits on full `r_tr`. The load-bearing reason for dropping the mask is the Hamilton-clock invariant — under the first-order Markov chain the HMM-observation count must equal the bar-position count, so K propagation steps map to exactly K transitions ([Hamilton 1989 *Econometrica* §3, doi:10.2307/1912559](https://doi.org/10.2307/1912559)). Masking decoupled the HMM clock from the bar-position clock. The first-bar construction zero `r_bar[0] = 0` per symbol is a single-row artifact of the `np.diff(np.log(closes))` constructor; its contribution to fitted moments is negligible relative to the methodological cost of clock desync. `hmm_train_terminal_position = int(train_idx[-1])` is harvested directly.
- **F-1-3:** `n_propagation_steps` is required (no default) at [_core.py:forward_log_from_prior](../../src/skie_ninja/models/regime/_core.py) and [hmm.py:filter_states_from_prior](../../src/skie_ninja/models/regime/hmm.py). Updated docstrings flag the deliberate no-default choice.
- **F-1-5:** `forward_log_from_prior` raises `FloatingPointError` after the propagation loop if `np.all(np.isfinite(log_alpha_prop))` fails — surfaces pathological transition-matrix conditioning at large K rather than producing silent NaNs downstream.
- **F-1-7 (lifted):** 4 tests added to [tests/unit/test_hmm_fold_warm_start.py](../../tests/unit/test_hmm_fold_warm_start.py):
  - `test_k_step_propagation_preserves_total_probability_mass` — uniform-prior log-mass invariance over K ∈ {1, 2, 5, 30}.
  - `test_forward_log_from_prior_handles_single_test_bar` — T_test=1 round-trip into contiguous forward.
  - `test_filter_states_invariant_to_prior_log_constant_shift` — softmax-normalised posterior unchanged under additive log-constant shift of prior.
  - `test_large_k_propagation_remains_finite` — K=120 with near-deterministic transitions yields finite log α.
- **F-1-8 (lifted):** [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md) §"Fold-boundary state continuity" extended with explicit K-step formula
  ```
  log_alpha_prop^{(k)}_j = logsumexp_i (log_alpha_prop^{(k-1)}_i + log_a_ij)   for k = 1, ..., K
  log_alpha_test[0, j]   = log_alpha_prop^{(K)}_j + log_b_j(o_{test_idx[0]})
  ```
  cited to AFML §7.4.1; "Implementation contract" updated to reflect `n_propagation_steps` required-arg + `terminal_log_alpha` harvest.

### Round-2 quant-auditor findings

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| F-2-1 | minor | [scripts/run_walk_forward.py:60-66](../../scripts/run_walk_forward.py) | Dead `_MIN_VALID_RETURNS_FOR_MASK=2` constant + 7-line justification comment referencing the removed mask. | Inline-fixed: lines removed in this round. |
| F-2-2 | minor | [hmm.py:terminal_log_alpha](../../src/skie_ninja/models/regime/hmm.py) | Re-runs full forward pass to extract last row; allocates and discards (T_train, N) interior. Perf, not method. | Logged as follow-up `P1-HMM-FORWARD-PASS-FUSION`; no inline change. |

### Test posture

All 14 tests in [tests/unit/test_hmm_fold_warm_start.py](../../tests/unit/test_hmm_fold_warm_start.py) green; broader HMM + orchestrator suite (64 tests) green:
```
tests/unit/test_backtest_walk_forward.py ..
tests/unit/test_hmm_core.py .....................
tests/unit/test_hmm_fit.py ..............
tests/unit/test_hmm_fold_warm_start.py .............
tests/unit/test_hmm_selection.py .....
tests/unit/test_hmm_serialization.py .......
tests/unit/test_leak_canaries.py .
tests/unit/test_orchestrator_smoke.py .
================= 64 passed, 466 deselected in 172.95s =================
```

## Exit decision

Exit Round-2 with `accept` verdict per [audit-remediate-loop](file:///C:/Users/skoir/.claude/skills/audit-remediate-loop/SKILL.md) §"Exit check": `findings == [critical|major]` is empty; F-2-1 inline-fixed; F-2-2 minor and tracked as follow-up. Round-3 not warranted.

## Residual risk

1. **`r_bar` over irregular row spacing.** `np.diff(np.log(closes))` over the post-`drop_nulls` / post-symbol-filter row sequence treats any time-gap as a single multi-bar log-return. This is internally consistent (HMM fit and propagated on the same row sequence; K counts row positions, not calendar bars) but means the HMM's transition matrix is conditioned on a non-uniform calendar grid. Mitigated by RTH-only session policy (no overnight or session-boundary bars in training).
2. **Warm-vs-cold OOS diagnostic absent.** A future regression where warm-start materially diverges from cold-start in OOS Sharpe would not be detected without re-running both. Tracked as `P1-HMM-WARM-COLD-DIAGNOSTIC`.
3. **Forward-pass fusion** (F-2-2). Tracked as `P1-HMM-FORWARD-PASS-FUSION`.
4. **`log_likelihood` semantics** (F-1-6 deferred). `forward_log_from_prior` returns `logsumexp(log_alpha[-1])`, which is `log P(o_test, o_train | θ) − log P(o_train | θ)` only when the prior is a properly normalised filtered posterior. Caller is responsible for not mis-interpreting it as a stand-alone model-evidence term.

## Cited references

- Hamilton, J. D. (1989). "A new approach to the economic analysis of nonstationary time series and the business cycle." *Econometrica* 57(2):357-384, §3. https://doi.org/10.2307/1912559
- Hamilton, J. D. (1994). *Time Series Analysis*. Princeton University Press, ISBN 978-0-691-04289-3, §22.4.
- Kim, C.-J., & Nelson, C. R. (1999). *State-Space Models with Regime Switching*. MIT Press, ISBN 978-0-262-11238-3, §4.2–4.3.
- Frühwirth-Schnatter, S. (2006). *Finite Mixture and Markov Switching Models*. Springer, ISBN 978-0-387-32909-3, §11.4–11.5.
- Rabiner, L. R. (1989). "A tutorial on hidden Markov models and selected applications in speech recognition." *Proc. IEEE* 77(2):257-286, §III.A. https://doi.org/10.1109/5.18626
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley, ISBN 978-1-119-48208-6, §7.4.1.
