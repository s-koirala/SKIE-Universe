"""Unit tests for the HMM numerical core (Cycle 3).

Coverage:

  - ``log_emission_matrix``: correctness on known Gaussian densities
    for each covariance parameterisation (spherical / diag / tied /
    full).
  - ``forward_log`` / ``backward_log``: hand-calculated 2-state toy;
    log-space result matches naive-space result on short sequences
    (numerical-equivalence gate).
  - ``forward_backward_log``: γ rows sum to 1; ξ sums match γ.
  - ``viterbi_log``: MAP path on a known toy matches manual
    enumeration.
  - ``baum_welch_em``: parameter recovery on synthetic Gaussian HMM
    with known params; monotone non-decreasing log-likelihood.
  - ``count_free_parameters`` / ``bic``: arithmetic correctness;
    BIC penalises the larger model when both fit equally well.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.special import logsumexp

from skie_ninja.models.regime._core import (
    HMMParams,
    backward_log,
    baum_welch_em,
    bic,
    count_free_parameters,
    forward_backward_log,
    forward_log,
    log_emission_matrix,
    viterbi_log,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _simulate_gaussian_hmm(
    *,
    t_len: int,
    pi: np.ndarray,
    transmat: np.ndarray,
    means: np.ndarray,
    variances_diag: np.ndarray,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Draw (states, observations) from a Gaussian HMM with diag covars."""
    rng = np.random.default_rng(seed)
    n_states = pi.size
    dim = means.shape[1]
    states = np.empty(t_len, dtype=np.int64)
    obs = np.empty((t_len, dim), dtype=np.float64)
    states[0] = rng.choice(n_states, p=pi)
    obs[0] = rng.normal(means[states[0]], np.sqrt(variances_diag[states[0]]))
    for t in range(1, t_len):
        states[t] = rng.choice(n_states, p=transmat[states[t - 1]])
        obs[t] = rng.normal(
            means[states[t]], np.sqrt(variances_diag[states[t]])
        )
    return states, obs


def _naive_forward(
    pi: np.ndarray, transmat: np.ndarray, emissions: np.ndarray
) -> tuple[np.ndarray, float]:
    """Unscaled forward recursion in probability space (small-T only).

    Used only as a reference on short, numerically-stable sequences
    to validate the log-space implementation.
    """
    t_len, n_states = emissions.shape
    alpha = np.empty((t_len, n_states), dtype=np.float64)
    alpha[0] = pi * emissions[0]
    for t in range(1, t_len):
        alpha[t] = emissions[t] * (alpha[t - 1] @ transmat)
    return alpha, float(alpha[-1].sum())


# ---------------------------------------------------------------------------
# log_emission_matrix
# ---------------------------------------------------------------------------


class TestLogEmissionMatrix:
    def test_diag_matches_univariate_normal_pdf(self) -> None:
        """Univariate: log N(x; μ, σ²) agrees with scipy.stats.norm.logpdf."""
        from scipy.stats import norm

        x = np.linspace(-3, 3, 7).reshape(-1, 1)
        means = np.array([[0.0], [1.5]])
        covars = np.array([[1.0], [0.5]])  # variances
        log_B = log_emission_matrix(x, means, covars, "diag")
        expected_0 = norm.logpdf(x[:, 0], loc=0.0, scale=1.0)
        expected_1 = norm.logpdf(x[:, 0], loc=1.5, scale=np.sqrt(0.5))
        np.testing.assert_allclose(log_B[:, 0], expected_0, atol=1e-12)
        np.testing.assert_allclose(log_B[:, 1], expected_1, atol=1e-12)

    def test_spherical_equals_diag_when_all_diag_equal(self) -> None:
        """Diag covars with all dims equal ≡ spherical by definition."""
        x = np.random.default_rng(0).normal(size=(20, 3))
        means = np.array([[0.0, 0.0, 0.0], [2.0, -1.0, 0.5]])
        var = 0.75
        diag_covars = np.full((2, 3), var)
        spherical_covars = np.array([var, var])
        log_B_diag = log_emission_matrix(x, means, diag_covars, "diag")
        log_B_sph = log_emission_matrix(x, means, spherical_covars, "spherical")
        np.testing.assert_allclose(log_B_diag, log_B_sph, atol=1e-12)

    def test_full_equals_diag_when_covar_is_diagonal(self) -> None:
        """Full covar with off-diagonals zero ≡ diag by construction."""
        x = np.random.default_rng(1).normal(size=(15, 2))
        means = np.array([[0.0, 0.0], [1.0, -1.0]])
        diag_covars = np.array([[1.0, 2.0], [0.5, 1.5]])
        full_covars = np.stack(
            [np.diag(diag_covars[i]) for i in range(2)]
        )
        log_B_diag = log_emission_matrix(x, means, diag_covars, "diag")
        log_B_full = log_emission_matrix(x, means, full_covars, "full")
        np.testing.assert_allclose(log_B_diag, log_B_full, atol=1e-10)

    def test_d1_full_equals_diag_bit_exact(self) -> None:
        """P1-HMM-FULL-COV-1DIM-REDUNDANT regression.

        At d=1, the `full` and `diag` paths must produce *bit-exact*
        identical log-densities (not merely up to round-off). This is
        the load-bearing claim of the model-class deduplication
        in select_gaussian_hmm; future drift in either code path
        would silently invalidate the optimisation.
        """
        rng = np.random.default_rng(2026)
        for t_len, n_states in [(50, 2), (500, 3), (5_000, 2)]:
            x = rng.standard_normal((t_len, 1)).astype(np.float64)
            means = rng.standard_normal((n_states, 1)).astype(np.float64) * 0.1
            var = np.full((n_states, 1), 1.0, dtype=np.float64)
            cov_full = var.reshape(n_states, 1, 1).copy()
            log_B_diag = log_emission_matrix(x, means, var, "diag")
            log_B_full = log_emission_matrix(x, means, cov_full, "full")
            assert np.array_equal(log_B_diag, log_B_full), (
                f"d=1 full/diag log-density not bit-exact at "
                f"(T={t_len}, N={n_states}): max-abs-diff="
                f"{np.max(np.abs(log_B_diag - log_B_full))}"
            )

    def test_d1_spherical_equals_diag_bit_exact(self) -> None:
        """At d=1, `spherical` and `diag` are also model-class equivalent."""
        rng = np.random.default_rng(2026)
        x = rng.standard_normal((500, 1)).astype(np.float64)
        means = rng.standard_normal((3, 1)).astype(np.float64) * 0.1
        var = np.array([[0.5], [1.0], [2.0]], dtype=np.float64)
        sph = var.reshape(-1).copy()  # (N,)
        log_B_diag = log_emission_matrix(x, means, var, "diag")
        log_B_sph = log_emission_matrix(x, means, sph, "spherical")
        assert np.array_equal(log_B_diag, log_B_sph)

    def test_tied_matches_full_when_states_share_covar(self) -> None:
        x = np.random.default_rng(2).normal(size=(10, 2))
        means = np.array([[0.0, 0.0], [1.0, 1.0]])
        shared = np.array([[1.0, 0.3], [0.3, 1.0]])
        tied_covars = shared
        full_covars = np.stack([shared, shared])
        log_B_tied = log_emission_matrix(x, means, tied_covars, "tied")
        log_B_full = log_emission_matrix(x, means, full_covars, "full")
        np.testing.assert_allclose(log_B_tied, log_B_full, atol=1e-10)

    def test_rejects_non_finite_input(self) -> None:
        x = np.array([[0.0], [np.nan]])
        means = np.array([[0.0]])
        covars = np.array([[1.0]])
        with pytest.raises(ValueError, match="NaN or inf"):
            log_emission_matrix(x, means, covars, "diag")

    def test_rejects_non_psd_full_covariance(self) -> None:
        x = np.array([[0.0, 0.0]])
        means = np.array([[0.0, 0.0]])
        # Not PSD: negative eigenvalue.
        bad = np.array([[[1.0, 2.0], [2.0, 1.0]]])
        with pytest.raises(ValueError, match="not positive-definite"):
            log_emission_matrix(x, means, bad, "full")


# ---------------------------------------------------------------------------
# Forward / backward
# ---------------------------------------------------------------------------


class TestForwardBackwardLog:
    def test_forward_hand_calculation_two_state(self) -> None:
        """Hand calc: 2 states, T=2, explicit arithmetic."""
        pi = np.array([0.6, 0.4])
        transmat = np.array([[0.7, 0.3], [0.4, 0.6]])
        emissions = np.array([[0.9, 0.1], [0.2, 0.8]])
        log_alpha_expected = np.empty((2, 2))
        log_alpha_expected[0] = [
            np.log(0.6 * 0.9),
            np.log(0.4 * 0.1),
        ]
        # α_2(0) = b_0(y_2)·(α_1(0)·a_00 + α_1(1)·a_10)
        a00 = 0.6 * 0.9 * 0.7 + 0.4 * 0.1 * 0.4
        a01 = 0.6 * 0.9 * 0.3 + 0.4 * 0.1 * 0.6
        log_alpha_expected[1] = [np.log(a00 * 0.2), np.log(a01 * 0.8)]

        log_alpha, log_ll = forward_log(
            np.log(pi), np.log(transmat), np.log(emissions)
        )
        np.testing.assert_allclose(log_alpha, log_alpha_expected, atol=1e-12)
        expected_ll = np.log(a00 * 0.2 + a01 * 0.8)
        assert log_ll == pytest.approx(expected_ll, abs=1e-12)

    def test_log_space_matches_naive_space_short_sequence(self) -> None:
        """Equivalence gate: log-space and naive-space agree on T=8."""
        rng = np.random.default_rng(42)
        n_states = 3
        t_len = 8
        pi = np.array([0.5, 0.3, 0.2])
        transmat = np.array(
            [[0.7, 0.2, 0.1], [0.1, 0.8, 0.1], [0.2, 0.3, 0.5]]
        )
        emissions = rng.uniform(0.1, 1.0, size=(t_len, n_states))
        # Rescale so rows are stable but not normalised (emissions are
        # densities, not probabilities).
        _, log_ll_log = forward_log(
            np.log(pi), np.log(transmat), np.log(emissions)
        )
        _, ll_naive = _naive_forward(pi, transmat, emissions)
        assert log_ll_log == pytest.approx(np.log(ll_naive), rel=1e-10)

    def test_backward_final_row_is_zero(self) -> None:
        transmat = np.array([[0.6, 0.4], [0.2, 0.8]])
        emissions = np.array([[0.3, 0.7], [0.6, 0.4], [0.5, 0.5]])
        log_beta = backward_log(np.log(transmat), np.log(emissions))
        np.testing.assert_allclose(log_beta[-1], np.zeros(2), atol=1e-12)

    def test_gamma_rows_sum_to_one(self) -> None:
        rng = np.random.default_rng(7)
        n_states = 3
        t_len = 20
        pi = rng.dirichlet(np.ones(n_states))
        transmat_rows = [rng.dirichlet(np.ones(n_states)) for _ in range(n_states)]
        transmat = np.stack(transmat_rows)
        emissions = rng.uniform(0.05, 1.0, size=(t_len, n_states))
        log_alpha, log_beta, log_gamma, log_xi_sum, log_ll = forward_backward_log(
            np.log(pi), np.log(transmat), np.log(emissions)
        )
        row_sums = np.exp(log_gamma).sum(axis=1)
        np.testing.assert_allclose(row_sums, np.ones(t_len), atol=1e-10)

    def test_xi_and_gamma_consistency(self) -> None:
        """Σ_j ξ_t(i,j) = γ_t(i) at each interior t."""
        rng = np.random.default_rng(13)
        pi = rng.dirichlet(np.ones(2))
        transmat = np.array([[0.6, 0.4], [0.3, 0.7]])
        emissions = rng.uniform(0.1, 1.0, size=(5, 2))
        # We need per-timestep ξ to verify; re-derive from α, β.
        log_alpha, log_beta, log_gamma, _, log_ll = forward_backward_log(
            np.log(pi), np.log(transmat), np.log(emissions)
        )
        log_xi_per_t = (
            log_alpha[:-1, :, None]
            + np.log(transmat)[None, :, :]
            + np.log(emissions[1:])[:, None, :]
            + log_beta[1:, None, :]
            - log_ll
        )
        xi_t = np.exp(log_xi_per_t)         # (T-1, 2, 2)
        gamma_t = np.exp(log_gamma)         # (T, 2)
        # Σ_j ξ_t(i,j) = γ_t(i) for t in 0..T-2.
        np.testing.assert_allclose(
            xi_t.sum(axis=2), gamma_t[:-1], atol=1e-10
        )


# ---------------------------------------------------------------------------
# Viterbi
# ---------------------------------------------------------------------------


class TestViterbiLog:
    def test_matches_brute_force_on_tiny_sequence(self) -> None:
        """Enumerate all (2^T) state paths; Viterbi picks the argmax."""
        pi = np.array([0.5, 0.5])
        transmat = np.array([[0.8, 0.2], [0.3, 0.7]])
        emissions = np.array([[0.9, 0.2], [0.1, 0.9], [0.8, 0.1]])
        log_B = np.log(emissions)

        path, log_prob = viterbi_log(np.log(pi), np.log(transmat), log_B)

        best_logp = -np.inf
        best_path: list[int] = []
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    seq = [a, b, c]
                    logp = (
                        np.log(pi[a])
                        + log_B[0, a]
                        + np.log(transmat[a, b])
                        + log_B[1, b]
                        + np.log(transmat[b, c])
                        + log_B[2, c]
                    )
                    if logp > best_logp:
                        best_logp = float(logp)
                        best_path = seq
        np.testing.assert_array_equal(path, np.array(best_path, dtype=np.int64))
        assert log_prob == pytest.approx(best_logp, abs=1e-12)


# ---------------------------------------------------------------------------
# Baum-Welch EM
# ---------------------------------------------------------------------------


class TestBaumWelchEM:
    def test_monotone_non_decreasing_log_likelihood(self) -> None:
        """EM must not decrease LL (Baum et al. 1970). Allow float64 roundoff."""
        rng = np.random.default_rng(100)
        pi_true = np.array([0.6, 0.4])
        transmat_true = np.array([[0.9, 0.1], [0.2, 0.8]])
        means_true = np.array([[-1.0], [1.5]])
        var_true = np.array([[0.25], [0.5]])
        _, x = _simulate_gaussian_hmm(
            t_len=400,
            pi=pi_true,
            transmat=transmat_true,
            means=means_true,
            variances_diag=var_true,
            seed=101,
        )
        init = HMMParams(
            log_pi=np.log(np.array([0.5, 0.5])),
            log_transmat=np.log(np.array([[0.5, 0.5], [0.5, 0.5]])),
            means=np.array([[rng.normal(-0.5)], [rng.normal(0.5)]]),
            covars=np.array([[1.0], [1.0]]),
            covariance_type="diag",
        )
        res = baum_welch_em(x, initial_params=init, em_tol=1e-6, max_iter=200)
        diffs = np.diff(res.log_likelihood_trace)
        # Allow tiny negatives from float64 roundoff near the fixed point.
        assert float(diffs.min()) >= -1e-6
        assert res.n_iter > 1

    def test_parameter_recovery_two_state_diag(self) -> None:
        """With enough data, BW recovers the true means up to label swap."""
        pi_true = np.array([0.5, 0.5])
        transmat_true = np.array([[0.95, 0.05], [0.05, 0.95]])
        means_true = np.array([[-2.0], [2.0]])
        var_true = np.array([[0.5], [0.5]])
        _, x = _simulate_gaussian_hmm(
            t_len=5000,
            pi=pi_true,
            transmat=transmat_true,
            means=means_true,
            variances_diag=var_true,
            seed=42,
        )
        # Initial params seeded to break symmetry so EM does not need
        # multiple restarts in the unit test.
        init = HMMParams(
            log_pi=np.log(np.array([0.5, 0.5])),
            log_transmat=np.log(np.array([[0.9, 0.1], [0.1, 0.9]])),
            means=np.array([[-1.0], [1.0]]),
            covars=np.array([[1.0], [1.0]]),
            covariance_type="diag",
        )
        res = baum_welch_em(x, initial_params=init, em_tol=1e-6, max_iter=200)
        recovered = np.sort(res.params.means[:, 0])
        truth = np.sort(means_true[:, 0])
        # 5000 samples: expect mean recovery within ~0.1.
        np.testing.assert_allclose(recovered, truth, atol=0.15)

    def test_converged_flag_true_on_stationary_problem(self) -> None:
        """EM should flag converged when the tolerance is actually reached."""
        pi = np.array([0.5, 0.5])
        transmat = np.array([[0.9, 0.1], [0.1, 0.9]])
        means = np.array([[-3.0], [3.0]])
        var = np.array([[0.1], [0.1]])
        _, x = _simulate_gaussian_hmm(
            t_len=2000, pi=pi, transmat=transmat, means=means,
            variances_diag=var, seed=7,
        )
        init = HMMParams(
            log_pi=np.log(np.array([0.5, 0.5])),
            log_transmat=np.log(np.array([[0.8, 0.2], [0.2, 0.8]])),
            means=np.array([[-2.5], [2.5]]),
            covars=np.array([[1.0], [1.0]]),
            covariance_type="diag",
        )
        res = baum_welch_em(x, initial_params=init, em_tol=1e-6, max_iter=500)
        assert res.converged is True


# ---------------------------------------------------------------------------
# BIC
# ---------------------------------------------------------------------------


class TestBIC:
    def test_parameter_count_diag(self) -> None:
        # N=3, d=2, diag: pi=2 + trans=6 + means=6 + covars=6 = 20
        assert count_free_parameters(3, 2, "diag") == 20

    def test_parameter_count_full(self) -> None:
        # N=2, d=3, full: pi=1 + trans=2 + means=6 + covars = 2 * 6 = 12 → 21
        assert count_free_parameters(2, 3, "full") == 21

    def test_parameter_count_tied(self) -> None:
        # N=4, d=2, tied: pi=3 + trans=12 + means=8 + covars=3 = 26
        assert count_free_parameters(4, 2, "tied") == 26

    def test_parameter_count_spherical(self) -> None:
        # N=5, d=4, spherical: pi=4 + trans=20 + means=20 + covars=5 = 49
        assert count_free_parameters(5, 4, "spherical") == 49

    def test_bic_penalises_larger_model_at_equal_ll(self) -> None:
        t = 500
        ll = -1000.0
        small = bic(ll, n_states=2, dim=1, covariance_type="diag", t_len=t)
        large = bic(ll, n_states=5, dim=1, covariance_type="diag", t_len=t)
        assert large > small

    def test_bic_formula(self) -> None:
        # BIC = -2 ln L + k ln T
        ll = -1234.5
        t = 300
        got = bic(ll, n_states=3, dim=2, covariance_type="diag", t_len=t)
        k = count_free_parameters(3, 2, "diag")
        expected = -2.0 * ll + k * np.log(t)
        assert got == pytest.approx(expected, abs=1e-12)

    def test_d1_param_count_equivalence_class(self) -> None:
        """P1-HMM-FULL-COV-1DIM-REDUNDANT regression.

        At d=1: spherical = N, diag = N*1 = N, full = N*1*(1+1)/2 = N.
        Only `tied` differs (1*(1+1)/2 = 1). The model-class
        deduplication in select_gaussian_hmm depends on this identity.
        """
        for n in (2, 3, 4, 5):
            k_sph = count_free_parameters(n, 1, "spherical")
            k_diag = count_free_parameters(n, 1, "diag")
            k_full = count_free_parameters(n, 1, "full")
            k_tied = count_free_parameters(n, 1, "tied")
            assert k_sph == k_diag == k_full, (
                f"d=1 cov-type k mismatch at N={n}: "
                f"spherical={k_sph}, diag={k_diag}, full={k_full}"
            )
            # tied at d=1 has fewer parameters (single shared scalar).
            assert k_tied < k_diag

    def test_d1_bic_equivalence_class(self) -> None:
        """At d=1, BIC must be identical across {spherical, diag, full}
        for any matching log-likelihood and T."""
        ll = -2500.0
        t_len = 5000
        for n in (2, 3):
            b_sph = bic(ll, n_states=n, dim=1, covariance_type="spherical", t_len=t_len)
            b_diag = bic(ll, n_states=n, dim=1, covariance_type="diag", t_len=t_len)
            b_full = bic(ll, n_states=n, dim=1, covariance_type="full", t_len=t_len)
            assert b_sph == b_diag == b_full
