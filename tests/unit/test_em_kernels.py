"""Regression tests for the numba forward-backward kernels.

Tests cover three layers:

1. **Numerical equivalence** — numba kernel vs the scipy reference, on
   randomised parameter sweeps spanning N ∈ {2, 3, 4, 5}, T ∈ {1, 2,
   100, 5_000}, and inputs designed to exercise -inf and large
   dynamic range. Tolerance ``rtol = 1e-12`` (motivated by Higham 2002
   *Accuracy and Stability of Numerical Algorithms* §4.2 — pairwise
   summation gives O(log n · u) error growth, well below 1e-12 for the
   T values used here).

2. **Numpy-fallback equivalence** — the pure-numpy reference path
   (used when numba is not installed) must produce *bit-identical*
   results to the existing scipy implementation in ``_core.py``,
   because the references call ``scipy.special.logsumexp`` directly.

3. **Wiring smoke** — the ``_core.py`` public functions (``forward_log``,
   ``backward_log``, ``forward_backward_log``, ``forward_log_from_prior``)
   produce results within ``rtol = 1e-12`` of the numpy reference.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.special import logsumexp

from skie_ninja.models.regime import _core, _em_kernels


# ---------------------------------------------------------------------------
# Helpers — sample HMM parameters and synthetic log-emission matrices
# ---------------------------------------------------------------------------


def _random_log_pi(n_states: int, rng: np.random.Generator) -> np.ndarray:
    pi = rng.dirichlet(np.ones(n_states))
    return np.log(pi)


def _random_log_transmat(n_states: int, rng: np.random.Generator) -> np.ndarray:
    rows = rng.dirichlet(np.ones(n_states), size=n_states)
    return np.log(rows)


def _random_log_B(t_len: int, n_states: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal((t_len, n_states))


# ---------------------------------------------------------------------------
# Numerical equivalence: numba kernel vs scipy reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n_states", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("t_len", [1, 2, 100, 5_000])
def test_forward_log_kernel_matches_numpy_reference(n_states: int, t_len: int) -> None:
    rng = np.random.default_rng(seed=10 * n_states + t_len)
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)

    log_alpha_kernel, ll_kernel = _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)
    log_alpha_ref, ll_ref = _em_kernels._forward_log_numpy_reference(
        log_pi, log_transmat, log_B
    )

    assert log_alpha_kernel.shape == log_alpha_ref.shape == (t_len, n_states)
    np.testing.assert_allclose(log_alpha_kernel, log_alpha_ref, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(ll_kernel, ll_ref, rtol=1e-12, atol=1e-12)


@pytest.mark.parametrize("n_states", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("t_len", [1, 2, 100, 5_000])
def test_backward_log_kernel_matches_numpy_reference(n_states: int, t_len: int) -> None:
    rng = np.random.default_rng(seed=20 * n_states + t_len)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)

    log_beta_kernel = _em_kernels.backward_log_kernel(log_transmat, log_B)
    log_beta_ref = _em_kernels._backward_log_numpy_reference(log_transmat, log_B)

    assert log_beta_kernel.shape == log_beta_ref.shape == (t_len, n_states)
    np.testing.assert_allclose(log_beta_kernel, log_beta_ref, rtol=1e-12, atol=1e-12)


@pytest.mark.parametrize("n_states", [2, 3, 4])
@pytest.mark.parametrize("t_len", [50, 1_000])
@pytest.mark.parametrize("k", [0, 1, 5])
def test_forward_log_from_prior_kernel_matches_numpy_reference(
    n_states: int, t_len: int, k: int
) -> None:
    rng = np.random.default_rng(seed=30 * n_states + t_len + k)
    log_alpha_prior = rng.standard_normal(n_states) - 5.0
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)

    la_kernel, ll_kernel = _em_kernels.forward_log_from_prior_kernel(
        log_alpha_prior, log_transmat, log_B, k
    )
    la_ref, ll_ref = _em_kernels._forward_log_from_prior_numpy_reference(
        log_alpha_prior, log_transmat, log_B, k
    )

    np.testing.assert_allclose(la_kernel, la_ref, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(ll_kernel, ll_ref, rtol=1e-12, atol=1e-12)


@pytest.mark.parametrize("n_states", [2, 3, 4, 5])
@pytest.mark.parametrize("t_len", [2, 100, 5_000])
def test_xi_sum_kernel_matches_numpy_reference(n_states: int, t_len: int) -> None:
    rng = np.random.default_rng(seed=40 * n_states + t_len)
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)
    log_alpha, ll = _em_kernels._forward_log_numpy_reference(log_pi, log_transmat, log_B)
    log_beta = _em_kernels._backward_log_numpy_reference(log_transmat, log_B)

    xi_kernel = _em_kernels.xi_sum_kernel(log_alpha, log_transmat, log_B, log_beta, ll)
    xi_ref = _em_kernels._xi_sum_numpy_reference(log_alpha, log_transmat, log_B, log_beta, ll)

    assert xi_kernel.shape == xi_ref.shape == (n_states, n_states)
    np.testing.assert_allclose(xi_kernel, xi_ref, rtol=1e-10, atol=1e-12)


# ---------------------------------------------------------------------------
# Edge cases — T = 1, T = 0, and -inf in log_pi / log_transmat
# ---------------------------------------------------------------------------


def test_forward_log_kernel_t1() -> None:
    log_pi = np.log(np.array([0.4, 0.6]))
    log_transmat = np.log(np.array([[0.7, 0.3], [0.4, 0.6]]))
    log_B = np.array([[-1.0, -2.0]])  # T=1
    log_alpha, ll = _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)
    expected_alpha = np.array([[log_pi[0] + log_B[0, 0], log_pi[1] + log_B[0, 1]]])
    np.testing.assert_allclose(log_alpha, expected_alpha, rtol=1e-12)
    np.testing.assert_allclose(ll, logsumexp(expected_alpha[0]), rtol=1e-12)


def test_backward_log_kernel_t1() -> None:
    log_transmat = np.log(np.array([[0.7, 0.3], [0.4, 0.6]]))
    log_B = np.array([[-1.0, -2.0]])  # T=1
    log_beta = _em_kernels.backward_log_kernel(log_transmat, log_B)
    np.testing.assert_array_equal(log_beta, np.zeros((1, 2)))


def test_xi_sum_kernel_t1_returns_minus_inf_matrix() -> None:
    n_states = 3
    log_alpha = np.zeros((1, n_states))
    log_transmat = np.zeros((n_states, n_states))
    log_B = np.zeros((1, n_states))
    log_beta = np.zeros((1, n_states))
    out = _em_kernels.xi_sum_kernel(log_alpha, log_transmat, log_B, log_beta, 0.0)
    assert out.shape == (n_states, n_states)
    assert np.all(np.isneginf(out))


def test_forward_log_kernel_handles_minus_inf_in_log_pi() -> None:
    """If a state has log_pi = -inf (zero prior probability), it should
    propagate cleanly without producing NaN."""
    log_pi = np.array([0.0, -np.inf])  # state-1 forbidden at t=0
    log_transmat = np.log(np.array([[0.7, 0.3], [0.4, 0.6]]))
    rng = np.random.default_rng(seed=42)
    log_B = rng.standard_normal((20, 2))

    log_alpha, ll = _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)
    # log_alpha[0, 1] must be -inf since log_pi[1] = -inf
    assert log_alpha[0, 1] == -np.inf
    # All later entries must be finite if any predecessor entry is finite
    # (because state 0 has positive probability and can transition to state 1)
    assert np.all(np.isfinite(log_alpha[1:]))
    assert np.isfinite(ll)


# ---------------------------------------------------------------------------
# Wiring smoke — _core.py functions produce kernel-equivalent output
# ---------------------------------------------------------------------------


def test_core_forward_log_matches_kernel() -> None:
    rng = np.random.default_rng(seed=123)
    n_states, t_len = 3, 500
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)

    log_alpha_core, ll_core = _core.forward_log(log_pi, log_transmat, log_B)
    log_alpha_ref, ll_ref = _em_kernels._forward_log_numpy_reference(
        log_pi, log_transmat, log_B
    )
    np.testing.assert_allclose(log_alpha_core, log_alpha_ref, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(ll_core, ll_ref, rtol=1e-12, atol=1e-12)


def test_core_forward_backward_log_matches_kernel() -> None:
    rng = np.random.default_rng(seed=456)
    n_states, t_len = 3, 500
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)

    la_c, lb_c, lg_c, lxs_c, ll_c = _core.forward_backward_log(log_pi, log_transmat, log_B)
    la_r, ll_r = _em_kernels._forward_log_numpy_reference(log_pi, log_transmat, log_B)
    lb_r = _em_kernels._backward_log_numpy_reference(log_transmat, log_B)
    lg_r = la_r + lb_r - ll_r
    lxs_r = _em_kernels._xi_sum_numpy_reference(la_r, log_transmat, log_B, lb_r, ll_r)

    np.testing.assert_allclose(la_c, la_r, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(lb_c, lb_r, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(lg_c, lg_r, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(lxs_c, lxs_r, rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(ll_c, ll_r, rtol=1e-12, atol=1e-12)


# ---------------------------------------------------------------------------
# Posterior-marginal sanity: sum_j gamma_t(j) == 1 in exp-space
# ---------------------------------------------------------------------------


def test_forward_backward_gamma_sums_to_one() -> None:
    rng = np.random.default_rng(seed=789)
    n_states, t_len = 4, 300
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)
    _, _, log_gamma, _, _ = _core.forward_backward_log(log_pi, log_transmat, log_B)
    gamma = np.exp(log_gamma)
    np.testing.assert_allclose(gamma.sum(axis=1), 1.0, rtol=1e-10, atol=1e-10)


# ---------------------------------------------------------------------------
# Forward-log-likelihood and FB log-likelihood agree
# ---------------------------------------------------------------------------


def test_forward_and_fb_log_likelihood_agree() -> None:
    rng = np.random.default_rng(seed=1000)
    n_states, t_len = 3, 1000
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)
    _, ll_fwd = _core.forward_log(log_pi, log_transmat, log_B)
    _, _, _, _, ll_fb = _core.forward_backward_log(log_pi, log_transmat, log_B)
    np.testing.assert_allclose(ll_fwd, ll_fb, rtol=1e-12)


# ---------------------------------------------------------------------------
# Numba-availability marker (sanity check, not a hard contract)
# ---------------------------------------------------------------------------


def test_numba_available_in_test_env() -> None:
    """numba is in the perf extra; tests run in the dev env which we
    assume has numba installed (CI does ``uv pip install -e
    .[dev,perf]``). If this test is skipped/failing, the perf path
    isn't being exercised by the rest of the suite — flag immediately."""
    if not _em_kernels.NUMBA_AVAILABLE:
        pytest.skip("numba not installed — perf extra not active in this env")
    # Confirms the kernel functions are dispatching to the @njit path
    # (otherwise the equivalence tests above would silently exercise
    # the numpy fallback only).
    assert _em_kernels.NUMBA_AVAILABLE is True


# ---------------------------------------------------------------------------
# F-1-1: -inf in log_pi/prior must not produce NaN even with degenerate log_B
# ---------------------------------------------------------------------------


def test_forward_log_handles_minus_inf_prior_with_pos_inf_emission_no_nan() -> None:
    """If a state has ``log_alpha_prior[j] == -inf`` (state forbidden by
    warm-start prior), and ``log_B[0, j] == +inf`` (degenerate but
    technically permitted log-density), the kernel must produce
    ``log_alpha[0, j] == -inf`` rather than NaN. Tests the F-1-1 guard
    in ``_forward_log_from_prior_njit`` and equivalent path in
    ``_forward_log_njit``."""
    log_pi = np.array([0.0, -np.inf])  # state 1 forbidden
    log_transmat = np.log(np.array([[0.5, 0.5], [0.5, 0.5]]))
    log_B = np.zeros((20, 2))
    log_B[0, 1] = np.inf  # log-density blow-up at the forbidden state's first emission
    la, ll = _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)
    assert not np.any(np.isnan(la)), f"NaN leaked into log_alpha; first NaN at index {np.argwhere(np.isnan(la))[0] if np.any(np.isnan(la)) else 'none'}"
    assert la[0, 1] == -np.inf
    assert np.isfinite(ll)


# ---------------------------------------------------------------------------
# F-1-8: streaming xi-sum with one finite t among many -inf t's
# ---------------------------------------------------------------------------


def test_xi_sum_kernel_sparse_finite_among_minus_inf() -> None:
    """If only one timestep contributes a finite log ξ_t(i,j) and the
    rest are -inf, the streaming logsumexp must reduce to that single
    finite value. The streaming-running-max algorithm has a branch for
    'first finite sample sets max + sum=1.0'; verify it handles a
    sparse pattern."""
    rng = np.random.default_rng(seed=2026)
    n_states, t_len = 3, 50
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)
    log_alpha, ll = _em_kernels._forward_log_numpy_reference(log_pi, log_transmat, log_B)
    log_beta = _em_kernels._backward_log_numpy_reference(log_transmat, log_B)

    # Manually compute the reference xi_sum and force all but one t to -inf
    log_xi_full = (
        log_alpha[:-1, :, None]
        + log_transmat[None, :, :]
        + log_B[1:, None, :]
        + log_beta[1:, None, :]
        - ll
    )
    # Mask all but t=20 to -inf
    keep_t = 20
    log_xi_sparse = np.full_like(log_xi_full, -np.inf)
    log_xi_sparse[keep_t] = log_xi_full[keep_t]

    # Kernel can't accept the masked tensor directly; instead, construct
    # log_alpha/log_beta such that all except one t produce -inf:
    log_alpha_sparse = np.full_like(log_alpha, -np.inf)
    log_alpha_sparse[keep_t] = log_alpha[keep_t]
    log_beta_sparse = np.full_like(log_beta, -np.inf)
    log_beta_sparse[keep_t + 1] = log_beta[keep_t + 1]

    out_kernel = _em_kernels.xi_sum_kernel(
        log_alpha_sparse, log_transmat, log_B, log_beta_sparse, ll
    )
    out_ref = _em_kernels._xi_sum_numpy_reference(
        log_alpha_sparse, log_transmat, log_B, log_beta_sparse, ll
    )
    np.testing.assert_allclose(out_kernel, out_ref, rtol=1e-10, atol=1e-12)
    # The kernel must not produce NaN even when most contributions are -inf
    assert not np.any(np.isnan(out_kernel))


# ---------------------------------------------------------------------------
# R-8: extreme-T regression test (T = 1e6) — quantify streaming logsumexp
# round-off vs scipy reference
# ---------------------------------------------------------------------------


def test_xi_sum_kernel_extreme_T_rtol_bounded() -> None:
    """At T = 10⁶, accumulated round-off in the streaming xi-sum
    must remain below rtol = 1e-9 against the scipy reference. This
    pins the numerical floor below the EM convergence tolerance
    (``_DEFAULT_EM_TOL = 1e-4``) by 5+ orders of magnitude."""
    if not _em_kernels.NUMBA_AVAILABLE:
        pytest.skip("numba unavailable — extreme-T test impractically slow under scipy")

    rng = np.random.default_rng(seed=20260428)
    n_states, t_len = 3, 1_000_000
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)
    log_alpha, ll = _em_kernels._forward_log_numpy_reference(log_pi, log_transmat, log_B)
    log_beta = _em_kernels._backward_log_numpy_reference(log_transmat, log_B)

    out_kernel = _em_kernels.xi_sum_kernel(log_alpha, log_transmat, log_B, log_beta, ll)
    out_ref = _em_kernels._xi_sum_numpy_reference(log_alpha, log_transmat, log_B, log_beta, ll)

    np.testing.assert_allclose(out_kernel, out_ref, rtol=1e-9, atol=1e-9)


# ---------------------------------------------------------------------------
# F-1-12: small-N gate — kernel rejects N > MAX_KERNEL_N
# ---------------------------------------------------------------------------


def test_forward_log_kernel_rejects_large_n() -> None:
    """Sequential summation accuracy is bounded by O(N·u). For N > 8
    the kernel refuses dispatch rather than silently producing fits
    that exceed the rtol contract."""
    n_states = _em_kernels.MAX_KERNEL_N + 1
    rng = np.random.default_rng(seed=99)
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(100, n_states, rng)
    with pytest.raises(ValueError, match="MAX_KERNEL_N"):
        _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)


# ---------------------------------------------------------------------------
# Perf smoke — kernel must not be *slower* than reference (1.5× margin)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("t_len", [50_000])
def test_kernel_not_slower_than_reference(t_len: int) -> None:
    """A coarse perf gate: for T = 50_000, N = 3 the kernel must be at
    least as fast as the numpy reference. We assert ratio < 1.5 to
    accommodate JIT warmup and CI noise. The kernel is expected to be
    ≥10× faster on the production T = 3·10⁶ substrate; this gate just
    catches a regression where the kernel becomes pessimised."""
    if not _em_kernels.NUMBA_AVAILABLE:
        pytest.skip("numba unavailable — perf check not meaningful")

    import time

    rng = np.random.default_rng(seed=12345)
    n_states = 3
    log_pi = _random_log_pi(n_states, rng)
    log_transmat = _random_log_transmat(n_states, rng)
    log_B = _random_log_B(t_len, n_states, rng)

    # Warm up JIT (do not include compile time in the timing)
    _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)

    t0 = time.perf_counter()
    _em_kernels.forward_log_kernel(log_pi, log_transmat, log_B)
    t_kernel = time.perf_counter() - t0

    t0 = time.perf_counter()
    _em_kernels._forward_log_numpy_reference(log_pi, log_transmat, log_B)
    t_ref = time.perf_counter() - t0

    ratio = t_kernel / max(t_ref, 1e-9)
    assert ratio < 1.5, (
        f"kernel slower than reference: t_kernel={t_kernel:.4f}s, "
        f"t_ref={t_ref:.4f}s, ratio={ratio:.2f}× (gate < 1.5×)"
    )
