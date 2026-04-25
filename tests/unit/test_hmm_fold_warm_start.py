"""Unit tests for the HMM walk-forward fold-boundary warm-start.

Coverage:

  - ``forward_log_from_prior`` reproduces the contiguous-sequence
    forward recursion when seeded from the terminal log α of the
    train fold (the ADR-0005 canonical formula).
  - K-step propagation matches K independent applications of the
    transition step.
  - Validation: prior-shape mismatch and negative ``n_propagation_steps``
    raise ``ValueError``.
  - ``GaussianHMM.terminal_log_alpha`` round-trips through
    ``filter_states_from_prior`` to reproduce ``filter_states`` on a
    contiguous sequence.
  - Causality canary: warm-started filter at index t depends only on
    test observations [0..t] given the prior.

References (ADR-0005 §"Fold-boundary state continuity"):

  - Hamilton 1989, Econometrica 57(2):357-384, §3.
  - Hamilton 1994, Time Series Analysis, §22.4.
  - Kim & Nelson 1999, §4.2-4.3.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.special import logsumexp

from skie_ninja.models.regime import GaussianHMM
from skie_ninja.models.regime._core import (
    forward_log,
    forward_log_from_prior,
    log_emission_matrix,
)


def _toy_params() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Two-state Gaussian HMM toy parameters."""
    log_pi = np.log(np.array([0.6, 0.4]))
    transmat = np.array([[0.9, 0.1], [0.2, 0.8]])
    log_transmat = np.log(transmat)
    means = np.array([[0.0], [3.0]])
    variances = np.array([[0.5], [0.5]])
    return log_pi, log_transmat, means, variances


def _draw(t_len: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=1.0, size=(t_len, 1))


# ---------------------------------------------------------------------------
# forward_log_from_prior — numerical equivalence with contiguous forward_log
# ---------------------------------------------------------------------------


def test_forward_log_from_prior_matches_contiguous_recursion() -> None:
    """Warm-starting the test fold reproduces the contiguous-sequence
    forward recursion exactly. ADR-0005 canonical-formula equivalence.
    """
    log_pi, log_transmat, means, variances = _toy_params()
    x_full = _draw(t_len=40, seed=17)
    t_train = 25
    x_train, x_test = x_full[:t_train], x_full[t_train:]

    log_b_full = log_emission_matrix(x_full, means, variances, "diag")
    log_alpha_full, _ = forward_log(log_pi, log_transmat, log_b_full)

    log_b_test = log_emission_matrix(x_test, means, variances, "diag")
    log_alpha_warm, _ = forward_log_from_prior(
        log_alpha_prior=log_alpha_full[t_train - 1],
        log_transmat=log_transmat,
        log_B=log_b_test,
        n_propagation_steps=1,
    )

    np.testing.assert_allclose(log_alpha_warm, log_alpha_full[t_train:], rtol=0, atol=1e-12)


def test_forward_log_from_prior_k_step_matches_repeated_propagation() -> None:
    """K transition steps internally equals K manual applications."""
    log_pi, log_transmat, means, variances = _toy_params()
    x_full = _draw(t_len=20, seed=23)
    t_train = 10
    K = 4

    log_b_full = log_emission_matrix(x_full, means, variances, "diag")
    log_alpha_full, _ = forward_log(log_pi, log_transmat, log_b_full)

    # Test fold starts at t_train + K (as if K bars were purged/embargoed).
    test_start = t_train + K
    x_test = x_full[test_start:]
    log_b_test = log_emission_matrix(x_test, means, variances, "diag")

    log_alpha_warm, _ = forward_log_from_prior(
        log_alpha_prior=log_alpha_full[t_train - 1],
        log_transmat=log_transmat,
        log_B=log_b_test,
        n_propagation_steps=K,
    )

    # Manual K-step propagation reference:
    prop = log_alpha_full[t_train - 1].copy()
    for _ in range(K):
        prop = logsumexp(prop[:, None] + log_transmat, axis=0)
    expected_first = log_b_test[0] + prop
    np.testing.assert_allclose(log_alpha_warm[0], expected_first, rtol=0, atol=1e-12)


def test_forward_log_from_prior_zero_steps_uses_prior_directly() -> None:
    """``n_propagation_steps=0`` skips propagation: log_alpha[0] = log_b[0] + prior."""
    log_pi, log_transmat, means, variances = _toy_params()
    x = _draw(t_len=8, seed=31)
    log_b = log_emission_matrix(x, means, variances, "diag")
    prior = np.array([-1.2, -0.5])
    log_alpha_warm, _ = forward_log_from_prior(
        log_alpha_prior=prior,
        log_transmat=log_transmat,
        log_B=log_b,
        n_propagation_steps=0,
    )
    np.testing.assert_allclose(log_alpha_warm[0], log_b[0] + prior, rtol=0, atol=1e-12)


def test_forward_log_from_prior_rejects_shape_mismatch() -> None:
    log_pi, log_transmat, means, variances = _toy_params()
    x = _draw(t_len=4, seed=7)
    log_b = log_emission_matrix(x, means, variances, "diag")
    with pytest.raises(ValueError, match="log_alpha_prior shape"):
        forward_log_from_prior(
            log_alpha_prior=np.zeros(3),
            log_transmat=log_transmat,
            log_B=log_b,
            n_propagation_steps=1,
        )


def test_forward_log_from_prior_rejects_negative_steps() -> None:
    log_pi, log_transmat, means, variances = _toy_params()
    x = _draw(t_len=4, seed=7)
    log_b = log_emission_matrix(x, means, variances, "diag")
    with pytest.raises(ValueError, match="n_propagation_steps"):
        forward_log_from_prior(
            log_alpha_prior=np.zeros(2),
            log_transmat=log_transmat,
            log_B=log_b,
            n_propagation_steps=-1,
        )


# ---------------------------------------------------------------------------
# GaussianHMM round-trip
# ---------------------------------------------------------------------------


def _fitted_two_state_hmm(seed: int = 42) -> tuple[GaussianHMM, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = 600
    state = np.zeros(n, dtype=np.int64)
    p_switch = 0.02
    for i in range(1, n):
        state[i] = state[i - 1] if rng.random() > p_switch else 1 - state[i - 1]
    means = np.array([0.0, 3.0])
    variances = np.array([0.4, 0.4])
    obs = rng.normal(loc=means[state], scale=np.sqrt(variances[state])).reshape(-1, 1)
    hmm = GaussianHMM(n_states=2, covariance_type="diag")
    hmm.fit(obs, seed=seed, min_restarts=5, max_restarts=5)
    return hmm, obs


def test_terminal_log_alpha_round_trips_to_filter_states() -> None:
    """``filter_states_from_prior`` seeded from a train fold's
    terminal log α reproduces ``filter_states`` on the contiguous
    sequence over the test slice. End-to-end ADR-0005 contract.
    """
    hmm, obs_full = _fitted_two_state_hmm()
    t_train = 400
    obs_train = obs_full[:t_train]
    obs_test = obs_full[t_train:]

    filter_full = hmm.filter_states(obs_full)
    prior = hmm.terminal_log_alpha(obs_train)
    filter_warm = hmm.filter_states_from_prior(
        obs_test, log_alpha_prior=prior, n_propagation_steps=1
    )

    np.testing.assert_allclose(filter_warm, filter_full[t_train:], rtol=0, atol=1e-10)


def test_filter_states_from_prior_causality_canary() -> None:
    """Result at index t depends only on test observations [0..t]
    given the prior — perturbing a future observation must not
    change earlier outputs.
    """
    hmm, obs_full = _fitted_two_state_hmm(seed=11)
    t_train = 300
    obs_train = obs_full[:t_train]
    obs_test = obs_full[t_train:].copy()
    prior = hmm.terminal_log_alpha(obs_train)
    baseline = hmm.filter_states_from_prior(
        obs_test, log_alpha_prior=prior, n_propagation_steps=1
    )

    obs_test_perturbed = obs_test.copy()
    perturb_idx = obs_test.shape[0] - 5
    obs_test_perturbed[perturb_idx, 0] += 50.0
    perturbed = hmm.filter_states_from_prior(
        obs_test_perturbed, log_alpha_prior=prior, n_propagation_steps=1
    )

    np.testing.assert_allclose(
        baseline[:perturb_idx], perturbed[:perturb_idx], rtol=0, atol=1e-12
    )
    assert not np.allclose(baseline[perturb_idx:], perturbed[perturb_idx:])


def test_filter_states_from_prior_rejects_unfitted() -> None:
    hmm = GaussianHMM(n_states=2, covariance_type="diag")
    with pytest.raises(RuntimeError, match="not fitted"):
        hmm.filter_states_from_prior(
            np.zeros((3, 1)), log_alpha_prior=np.zeros(2), n_propagation_steps=1
        )


def test_terminal_log_alpha_rejects_unfitted() -> None:
    hmm = GaussianHMM(n_states=2, covariance_type="diag")
    with pytest.raises(RuntimeError, match="not fitted"):
        hmm.terminal_log_alpha(np.zeros((3, 1)))


# ---------------------------------------------------------------------------
# F-1-7: structural / numerical invariants (Round-2 audit)
# ---------------------------------------------------------------------------


def test_k_step_propagation_preserves_total_probability_mass() -> None:
    """Row-stochastic Markov invariant: a normalised prior propagated K
    steps remains a probability distribution (sums to 1 in exp-space).
    Hamilton 1994 §22.4; Frühwirth-Schnatter 2006 §11.4.
    """
    log_pi, log_transmat, _, _ = _toy_params()
    n_states = log_pi.shape[0]
    log_prior_uniform = np.full(n_states, -np.log(n_states))
    np.testing.assert_allclose(logsumexp(log_prior_uniform), 0.0, atol=1e-12)

    for K in (1, 2, 5, 30):
        prop = log_prior_uniform.copy()
        for _ in range(K):
            prop = logsumexp(prop[:, None] + log_transmat, axis=0)
        np.testing.assert_allclose(logsumexp(prop), 0.0, atol=1e-10)


def test_forward_log_from_prior_handles_single_test_bar() -> None:
    """T_test=1 edge case: single test-bar fold yields log_alpha of
    shape (1, n_states) reproducing the contiguous-sequence forward
    pass over that single index when seeded from the immediate
    predecessor's filtered log α (K=1, no purge).
    """
    log_pi, log_transmat, means, variances = _toy_params()
    x_full = _draw(t_len=12, seed=53)
    t_train = 10
    x_test = x_full[t_train:t_train + 1]

    log_b_full = log_emission_matrix(x_full, means, variances, "diag")
    log_alpha_full, _ = forward_log(log_pi, log_transmat, log_b_full)

    log_b_test = log_emission_matrix(x_test, means, variances, "diag")
    log_alpha_warm, ll_warm = forward_log_from_prior(
        log_alpha_prior=log_alpha_full[t_train - 1],
        log_transmat=log_transmat,
        log_B=log_b_test,
        n_propagation_steps=1,
    )
    assert log_alpha_warm.shape == (1, log_pi.shape[0])
    np.testing.assert_allclose(
        log_alpha_warm[0], log_alpha_full[t_train], rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(ll_warm, logsumexp(log_alpha_warm[-1]), atol=1e-12)


def test_filter_states_invariant_to_prior_log_constant_shift() -> None:
    """Filter-state argmax is unchanged when the prior is shifted by an
    arbitrary additive constant in log-space (unnormalised log α is the
    canonical input — only argmax of softmax-normalised posterior is
    observable). Hamilton 1994 §22.4 normalisation invariance.
    """
    hmm, obs_full = _fitted_two_state_hmm(seed=19)
    t_train = 350
    obs_train = obs_full[:t_train]
    obs_test = obs_full[t_train:]

    prior = hmm.terminal_log_alpha(obs_train)
    prior_shifted = prior + 17.3

    posteriors = hmm.filter_states_from_prior(
        obs_test, log_alpha_prior=prior, n_propagation_steps=1
    )
    posteriors_shifted = hmm.filter_states_from_prior(
        obs_test, log_alpha_prior=prior_shifted, n_propagation_steps=1
    )
    # Softmax-normalised posteriors cancel the additive log-constant analytically;
    # residual differs only by float rounding in the logsumexp max-shift step.
    np.testing.assert_allclose(posteriors, posteriors_shifted, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(
        np.argmax(posteriors, axis=1), np.argmax(posteriors_shifted, axis=1)
    )


def test_large_k_propagation_remains_finite() -> None:
    """K=120 propagation under near-deterministic transitions yields
    finite log α throughout — guards against numerical-underflow drift
    in iterated logsumexp (F-1-5 postcondition complement).
    """
    log_pi = np.log(np.array([0.5, 0.5]))
    transmat = np.array([[0.99, 0.01], [0.01, 0.99]])
    log_transmat = np.log(transmat)
    means = np.array([[0.0], [3.0]])
    variances = np.array([[0.5], [0.5]])
    x = _draw(t_len=10, seed=71)
    log_b = log_emission_matrix(x, means, variances, "diag")
    prior = log_pi.copy()

    log_alpha_warm, ll_warm = forward_log_from_prior(
        log_alpha_prior=prior,
        log_transmat=log_transmat,
        log_B=log_b,
        n_propagation_steps=120,
    )
    assert np.all(np.isfinite(log_alpha_warm))
    assert np.isfinite(ll_warm)
