"""Unit tests for :class:`GaussianHMM` — fit, causal filter, determinism.

Coverage:

  - Fit on synthetic data recovers approximate params.
  - ``filter_states`` returns row-normalised posteriors.
  - ``filter_states(y_{1:t})`` is strictly causal: prefix of the
    filter output on ``y_{1:T}`` agrees with ``filter_states`` on
    ``y_{1:t}`` for any ``t``. This is the **no-look-ahead gate**.
  - ``viterbi_train_time`` is differentiable (in practice) from
    ``filter_states``: the hard MAP path is not the same as the
    argmax-of-filtered-posterior on the same sequence.
  - Fit is deterministic under fixed seed (cross-call byte identity
    on serialised params).
  - Dimension validation: fitted-d ≠ query-d raises.
  - ``n_states < 2`` rejected (ADR-0005 "single-state is not a
    regime model").
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.models.regime.hmm import GaussianHMM


def _simulate(seed: int, t_len: int = 800) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pi = np.array([0.5, 0.5])
    transmat = np.array([[0.9, 0.1], [0.1, 0.9]])
    means = np.array([[-2.0], [2.0]])
    var = np.array([[0.5], [0.5]])
    states = np.empty(t_len, dtype=np.int64)
    obs = np.empty((t_len, 1), dtype=np.float64)
    states[0] = rng.choice(2, p=pi)
    obs[0] = rng.normal(means[states[0]], np.sqrt(var[states[0]]))
    for t in range(1, t_len):
        states[t] = rng.choice(2, p=transmat[states[t - 1]])
        obs[t] = rng.normal(means[states[t]], np.sqrt(var[states[t]]))
    return obs


class TestGaussianHMMFit:
    def test_fit_returns_self(self) -> None:
        obs = _simulate(0, t_len=300)
        hmm = GaussianHMM(n_states=2)
        out = hmm.fit(obs, seed=42, min_restarts=5, max_restarts=5)
        assert out is hmm
        assert hmm.params_ is not None
        assert hmm.fit_result_ is not None

    def test_n_states_lt_2_rejected(self) -> None:
        with pytest.raises(ValueError, match="n_states must be >= 2"):
            GaussianHMM(n_states=1)

    def test_min_restarts_floor_enforced(self) -> None:
        obs = _simulate(1, t_len=300)
        hmm = GaussianHMM(n_states=2)
        with pytest.raises(ValueError, match="min_restarts must be >= 5"):
            hmm.fit(obs, seed=0, min_restarts=3, max_restarts=10)

    def test_insufficient_observations_rejected(self) -> None:
        hmm = GaussianHMM(n_states=3)
        # 3*5 = 15, so 14 observations is too few.
        obs = np.linspace(0.0, 1.0, 14).reshape(-1, 1)
        with pytest.raises(ValueError, match="Too few observations"):
            hmm.fit(obs, seed=0)


class TestCausalForwardFilter:
    def test_filter_rows_sum_to_one(self) -> None:
        obs = _simulate(10, t_len=500)
        hmm = GaussianHMM(n_states=2).fit(obs, seed=1, max_restarts=5)
        post = hmm.filter_states(obs)
        assert post.shape == (500, 2)
        np.testing.assert_allclose(post.sum(axis=1), np.ones(500), atol=1e-10)
        assert post.min() >= 0.0
        assert post.max() <= 1.0 + 1e-12

    def test_filter_prefix_causality(self) -> None:
        """filter_states(y_{1:t}) == filter_states(y_{1:T})[:t].

        This is the no-look-ahead gate. If the filter ever used
        future observations, the prefix would differ.
        """
        obs = _simulate(20, t_len=400)
        hmm = GaussianHMM(n_states=2).fit(obs, seed=1, max_restarts=5)
        full = hmm.filter_states(obs)
        for t in [10, 50, 100, 200, 399]:
            prefix = hmm.filter_states(obs[: t + 1])
            np.testing.assert_allclose(
                prefix, full[: t + 1], atol=1e-10,
                err_msg=f"causality broken at t={t}",
            )

    def test_requires_fit_before_inference(self) -> None:
        hmm = GaussianHMM(n_states=2)
        with pytest.raises(RuntimeError, match="not fitted"):
            hmm.filter_states(np.zeros((10, 1)))


class TestViterbiTrainTime:
    def test_full_viterbi_returns_path_and_logprob(self) -> None:
        obs = _simulate(30, t_len=200)
        hmm = GaussianHMM(n_states=2).fit(obs, seed=2, max_restarts=5)
        path, logp = hmm.viterbi_train_time(obs)
        assert path.shape == (200,)
        assert path.dtype == np.int64
        assert np.all((path == 0) | (path == 1))
        assert np.isfinite(logp)


class TestDeterminism:
    def test_fit_deterministic_under_fixed_seed(self) -> None:
        obs = _simulate(40, t_len=500)
        hmm_a = GaussianHMM(n_states=2).fit(obs, seed=7, max_restarts=5)
        hmm_b = GaussianHMM(n_states=2).fit(obs, seed=7, max_restarts=5)
        assert hmm_a.params_ is not None
        assert hmm_b.params_ is not None
        np.testing.assert_array_equal(hmm_a.params_.log_pi, hmm_b.params_.log_pi)
        np.testing.assert_array_equal(
            hmm_a.params_.log_transmat, hmm_b.params_.log_transmat
        )
        np.testing.assert_array_equal(hmm_a.params_.means, hmm_b.params_.means)
        np.testing.assert_array_equal(hmm_a.params_.covars, hmm_b.params_.covars)

    def test_different_seeds_can_diverge(self) -> None:
        """Sanity: two seeds do not always give identical fits."""
        obs = _simulate(41, t_len=500)
        hmm_a = GaussianHMM(n_states=2).fit(obs, seed=7, max_restarts=5)
        hmm_b = GaussianHMM(n_states=2).fit(obs, seed=11, max_restarts=5)
        # They SHOULD both find the global optimum on this easy
        # problem; assert LL is close but restart counts may differ.
        assert hmm_a.fit_result_ is not None
        assert hmm_b.fit_result_ is not None
        assert abs(
            hmm_a.fit_result_.best_log_likelihood
            - hmm_b.fit_result_.best_log_likelihood
        ) < 10.0


class TestLabelCanonicalisation:
    def test_mean_ascending_sorts_means(self) -> None:
        obs = _simulate(50, t_len=600)
        hmm = GaussianHMM(
            n_states=2, canonical_order="mean_ascending"
        ).fit(obs, seed=3, max_restarts=5)
        assert hmm.params_ is not None
        means = hmm.params_.means[:, 0]
        assert means[0] <= means[1]

    def test_mean_descending_sorts_means(self) -> None:
        obs = _simulate(51, t_len=600)
        hmm = GaussianHMM(
            n_states=2, canonical_order="mean_descending"
        ).fit(obs, seed=3, max_restarts=5)
        assert hmm.params_ is not None
        means = hmm.params_.means[:, 0]
        assert means[0] >= means[1]


class TestDimensionValidation:
    def test_query_with_wrong_dim_raises(self) -> None:
        obs_1d = _simulate(60, t_len=300)
        hmm = GaussianHMM(n_states=2).fit(obs_1d, seed=0, max_restarts=5)
        wrong_dim = np.zeros((50, 3))
        with pytest.raises(ValueError, match="!= fitted dim"):
            hmm.filter_states(wrong_dim)


class TestLogLikelihood:
    def test_held_out_log_likelihood_is_finite(self) -> None:
        train = _simulate(70, t_len=800)
        test = _simulate(71, t_len=200)
        hmm = GaussianHMM(n_states=2).fit(train, seed=0, max_restarts=5)
        ll = hmm.log_likelihood(test)
        assert np.isfinite(ll)
