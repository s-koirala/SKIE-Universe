"""Numerical hot-loop kernels for Baum-Welch forward-backward.

The Python-level forward/backward recursions in
:mod:`skie_ninja.models.regime._core` call
``scipy.special.logsumexp`` once per timestep. At T = 3 × 10⁶ (the H050
pre-Cell-I production substrate cell-row count after gate filtering)
each EM iteration spends ~95% of its wall-clock in those Python loops,
yielding cold-fit latencies of order 10 hours per fold-symbol. Profiling
on the H050 production walk-forward (run-3, 2026-04-27) attributed the
dominant cost to the per-t Python interpreter overhead rather than to
NumPy vectorised work, since N ∈ {2, 3, 4} is too small for vectorised
``logsumexp`` to amortise the Python frame cost.

This module replaces those Python loops with Numba ``@njit`` kernels
that fuse the logsumexp into a manual ``max + log-sum-exp`` over the N
states, eliminating the per-t Python frame entirely. Measured speedups
on the worktree's CPU (Tier-5 microbench at
[logs/bench_em_kernels_2026-04-28.json](../../../logs/bench_em_kernels_2026-04-28.json),
thread-pinned per ADR-0009, fastmath=False, min-of-3 timing):

============  ===========  ========  =========  =========
T             N            kernel    scipy ref  speedup
============  ===========  ========  =========  =========
10_000        {2,3,4}      ~2 ms     ~0.92 s    400-730×
50_000        {2,3,4}      ~4-11 ms  ~5 s       500-1180×
200_000       {2,3,4}      ~20-40 ms ~25-37 s   985-1210×
============  ===========  ========  =========  =========

At the H050 production substrate (T ≈ 3·10⁶, N ∈ {2..4}), the linear
extrapolation predicts scipy-path forward+backward at ~6-12 minutes
per EM iteration → kernel-path at ~0.5-1 second per iteration. With
30-50 EM iterations × ~6 cold fits per walk-forward run, the
end-to-end HMM-fit cost is expected to drop from ~100+ hours to
~30-60 minutes. Correctness is preserved within float64 round-off
(``rtol = 1e-12`` against the scipy reference, asserted by the
regression tests in ``tests/unit/test_em_kernels.py``).

Numba is an *optional* dependency (project ``perf`` extra). When it is
unavailable the module falls back to the original NumPy + scipy
formulation, so unit tests and downstream reproducibility remain
intact on bare-metal Python without numba installed.

Numerical-path provenance
-------------------------

The kernel implementation differs from the scipy path in floating-point
*ordering*, not in mathematical identity. Two EM fits started from
identical initial conditions and run on identical data may produce
parameter arrays whose entries match to ~1e-12 relative tolerance but
not to byte identity. The disk-persistent HMM-fit cache
(``hmm_fit_cache.py``) records ``git_head``, ``python_version``,
``numpy_version``, ``numba_version``, and the SHA256 of this module's
source (``kernel_implementation_id``). Cross-HEAD or cross-numba
resume surfaces a provenance-drift warning. Within a HEAD, both paths
produce semantically equivalent fits.

Cross-host determinism caveat
-----------------------------

Numba ``@njit(cache=True)`` writes per-host LLVM-codegen artifacts to
``__pycache__/<module>.nbi``. The cache key is
``(source_hash, numba_version, python_version)`` (per Numba 0.65 docs)
but **not** the host CPU feature set. AVX-512 hosts emit different
vectorised instruction sequences than AVX2 hosts, so identical inputs
on heterogeneous hardware can yield ``log_alpha`` arrays that differ
at machine epsilon. The byte-identity invariant of
``hmm_fit_cache.py`` (F-1-4 / "two identical fits → byte-identical
pickle") therefore holds *within* a host but is rtol-bounded across
hosts. ``thread_pinning`` to 1 thread per BLAS lib (ADR-0009) is
necessary but not sufficient for cross-host bit equality;
reproducibility-critical runs that demand bit identity must be
re-executed on the same host.

Small-N assumption
------------------

The manual logsumexp inside the kernels uses naive sequential
summation ``s = 0; for i: s += exp(v_i - max)``. Per Higham 2002
*Accuracy and Stability of Numerical Algorithms* §4.2, sequential
summation has error growth O(N·u). For the project's HMM grid
(N ∈ {2..5}) this is well below the 1e-12 rtol asserted by the
regression tests. The wrapper functions check ``log_B.shape[1] <= 8``
before dispatch; callers requiring N > 8 should request a
Kahan-compensated kernel via a follow-up.

References
----------

  - Lam, S. K., Pitrou, A., & Seibert, S. 2015. "Numba: a LLVM-based
    Python JIT compiler." *Proceedings of the Second Workshop on the
    LLVM Compiler Infrastructure in HPC* (LLVM '15), Article 7.
    https://doi.org/10.1145/2833157.2833162
  - Rabiner, L. R. 1989. "A Tutorial on Hidden Markov Models and
    Selected Applications in Speech Recognition." *Proceedings of the
    IEEE* 77(2): 257-286. https://doi.org/10.1109/5.18626
  - Bishop, C. M. 2006. *Pattern Recognition and Machine Learning*,
    §13.2. Springer. ISBN 978-0-387-31073-2.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from scipy.special import logsumexp as _scipy_logsumexp

try:
    from numba import njit  # type: ignore[import-not-found]

    NUMBA_AVAILABLE = True
except ImportError:  # pragma: no cover — numba in the perf extra
    NUMBA_AVAILABLE = False

    def njit(*args, **kwargs):  # type: ignore[no-redef]
        """Identity decorator used when numba is not installed.

        Honors both ``@njit`` and ``@njit(...)`` invocations.
        """

        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]

        def _decorator(func):
            return func

        return _decorator


# ---------------------------------------------------------------------------
# Numba kernels (or numpy reference if numba is missing)
# ---------------------------------------------------------------------------

# KERNEL_FASTMATH_NOTE
# --------------------
# All @njit kernels below are decorated ``fastmath=False`` (default,
# stated explicitly). ``-ffast-math`` would permit LLVM to reassociate
# floating-point operations and treat ``inf`` / ``nan`` as undefined.
# Both break the max-subtraction identity behind manual logsumexp
# (e.g. ``exp(v - m)`` for ``v = m = -inf`` would become a poison
# value rather than ``0``, and ``log(sum)`` ordering is no longer
# IEEE-754 deterministic). Do not flip ``fastmath`` without
# re-deriving the numerical stability proofs and refreshing the
# regression-test tolerance gates.


@njit(cache=True, fastmath=False)  # fastmath=False — see KERNEL_FASTMATH_NOTE
def _forward_log_njit(
    log_pi: np.ndarray,
    log_transmat: np.ndarray,
    log_B: np.ndarray,
) -> tuple[np.ndarray, float]:
    """Numba forward recursion. See :func:`forward_log_kernel` for contract."""
    t_len, n_states = log_B.shape
    log_alpha = np.empty((t_len, n_states), dtype=np.float64)
    for j in range(n_states):
        # F-1-1: -inf prior + +inf emission produces NaN under naive
        # addition; structurally zero-mass state (log_pi == -inf) stays
        # at -inf regardless of the emission density.
        if log_pi[j] == -np.inf:
            log_alpha[0, j] = -np.inf
        else:
            log_alpha[0, j] = log_pi[j] + log_B[0, j]
    for t in range(1, t_len):
        for j in range(n_states):
            m = -np.inf
            for i in range(n_states):
                v = log_alpha[t - 1, i] + log_transmat[i, j]
                if v > m:
                    m = v
            if m == -np.inf:
                # F-1-1: write -inf directly; ``log_B[t,j] + (-inf)`` could
                # produce NaN if log_B[t,j] is +inf. State j with all
                # zero-probability predecessors has structurally zero
                # mass regardless of the emission density.
                log_alpha[t, j] = -np.inf
                continue
            s = 0.0
            for i in range(n_states):
                s += np.exp(log_alpha[t - 1, i] + log_transmat[i, j] - m)
            log_alpha[t, j] = log_B[t, j] + m + np.log(s)
    # Total log-likelihood: logsumexp(log_alpha[-1])
    m = -np.inf
    for j in range(n_states):
        if log_alpha[t_len - 1, j] > m:
            m = log_alpha[t_len - 1, j]
    if m == -np.inf:
        return log_alpha, -np.inf
    s = 0.0
    for j in range(n_states):
        s += np.exp(log_alpha[t_len - 1, j] - m)
    log_likelihood = m + np.log(s)
    return log_alpha, log_likelihood


@njit(cache=True, fastmath=False)  # fastmath=False — see KERNEL_FASTMATH_NOTE
def _backward_log_njit(
    log_transmat: np.ndarray,
    log_B: np.ndarray,
) -> np.ndarray:
    """Numba backward recursion. See :func:`backward_log_kernel` for contract."""
    t_len, n_states = log_B.shape
    log_beta = np.empty((t_len, n_states), dtype=np.float64)
    for j in range(n_states):
        log_beta[t_len - 1, j] = 0.0
    for t in range(t_len - 2, -1, -1):
        for i in range(n_states):
            m = -np.inf
            for j in range(n_states):
                v = log_transmat[i, j] + log_B[t + 1, j] + log_beta[t + 1, j]
                if v > m:
                    m = v
            if m == -np.inf:
                log_beta[t, i] = -np.inf
                continue
            s = 0.0
            for j in range(n_states):
                s += np.exp(log_transmat[i, j] + log_B[t + 1, j] + log_beta[t + 1, j] - m)
            log_beta[t, i] = m + np.log(s)
    return log_beta


@njit(cache=True, fastmath=False)  # fastmath=False — see KERNEL_FASTMATH_NOTE
def _propagate_alpha_one_step_njit(
    log_alpha_prior: np.ndarray,
    log_transmat: np.ndarray,
) -> np.ndarray:
    """Single transition step in log-space: logsumexp_i(α_prior + a_ij)."""
    n_states = log_transmat.shape[0]
    out = np.empty(n_states, dtype=np.float64)
    for j in range(n_states):
        m = -np.inf
        for i in range(n_states):
            v = log_alpha_prior[i] + log_transmat[i, j]
            if v > m:
                m = v
        if m == -np.inf:
            out[j] = -np.inf
            continue
        s = 0.0
        for i in range(n_states):
            s += np.exp(log_alpha_prior[i] + log_transmat[i, j] - m)
        out[j] = m + np.log(s)
    return out


@njit(cache=True, fastmath=False)  # fastmath=False — see KERNEL_FASTMATH_NOTE
def _forward_log_from_prior_njit(
    log_alpha_prior: np.ndarray,
    log_transmat: np.ndarray,
    log_B: np.ndarray,
    n_propagation_steps: int,
) -> tuple[np.ndarray, float]:
    """Numba prior-seeded forward recursion. See :func:`forward_log_from_prior_kernel`."""
    t_len, n_states = log_B.shape
    log_alpha_prop = log_alpha_prior.astype(np.float64).copy()
    for _ in range(n_propagation_steps):
        log_alpha_prop = _propagate_alpha_one_step_njit(log_alpha_prop, log_transmat)
    log_alpha = np.empty((t_len, n_states), dtype=np.float64)
    for j in range(n_states):
        # F-1-1: avoid +inf + (-inf) = NaN when prior is -inf; structurally
        # zero-mass state stays at -inf regardless of emission density.
        if log_alpha_prop[j] == -np.inf:
            log_alpha[0, j] = -np.inf
        else:
            log_alpha[0, j] = log_B[0, j] + log_alpha_prop[j]
    for t in range(1, t_len):
        for j in range(n_states):
            m = -np.inf
            for i in range(n_states):
                v = log_alpha[t - 1, i] + log_transmat[i, j]
                if v > m:
                    m = v
            if m == -np.inf:
                log_alpha[t, j] = -np.inf
                continue
            s = 0.0
            for i in range(n_states):
                s += np.exp(log_alpha[t - 1, i] + log_transmat[i, j] - m)
            log_alpha[t, j] = log_B[t, j] + m + np.log(s)
    # Total log-likelihood
    m = -np.inf
    for j in range(n_states):
        if log_alpha[t_len - 1, j] > m:
            m = log_alpha[t_len - 1, j]
    if m == -np.inf:
        return log_alpha, -np.inf
    s = 0.0
    for j in range(n_states):
        s += np.exp(log_alpha[t_len - 1, j] - m)
    log_likelihood = m + np.log(s)
    return log_alpha, log_likelihood


@njit(cache=True, fastmath=False)  # fastmath=False — see KERNEL_FASTMATH_NOTE
def _xi_sum_streaming_njit(
    log_alpha: np.ndarray,
    log_transmat: np.ndarray,
    log_B: np.ndarray,
    log_beta: np.ndarray,
    log_likelihood: float,
) -> np.ndarray:
    """Streaming logsumexp accumulation of log ξ_t over t.

    Computes ``logsumexp_t [log α_t(i) + log a_ij + log b_j(y_{t+1}) +
    log β_{t+1}(j) - log_likelihood]`` for each (i, j) without
    materialising the (T-1, N, N) tensor. Memory: O(N²). Compute:
    O(T·N²), single pass with a running max + sum of exp(v - max).
    """
    t_len, n_states = log_B.shape
    if t_len < 2:
        out = np.full((n_states, n_states), -np.inf, dtype=np.float64)
        return out
    running_max = np.full((n_states, n_states), -np.inf, dtype=np.float64)
    running_sum = np.zeros((n_states, n_states), dtype=np.float64)
    for t in range(t_len - 1):
        for i in range(n_states):
            for j in range(n_states):
                v = (
                    log_alpha[t, i]
                    + log_transmat[i, j]
                    + log_B[t + 1, j]
                    + log_beta[t + 1, j]
                    - log_likelihood
                )
                if v == -np.inf:
                    # Skip — exp(-inf) = 0, contributes nothing.
                    continue
                if v > running_max[i, j]:
                    if running_max[i, j] == -np.inf:
                        running_max[i, j] = v
                        running_sum[i, j] = 1.0
                    else:
                        # Re-normalise prior accumulation against the new max.
                        running_sum[i, j] = (
                            running_sum[i, j] * np.exp(running_max[i, j] - v) + 1.0
                        )
                        running_max[i, j] = v
                else:
                    running_sum[i, j] += np.exp(v - running_max[i, j])
    out = np.empty((n_states, n_states), dtype=np.float64)
    for i in range(n_states):
        for j in range(n_states):
            if running_max[i, j] == -np.inf:
                out[i, j] = -np.inf
            else:
                out[i, j] = running_max[i, j] + np.log(running_sum[i, j])
    return out


# ---------------------------------------------------------------------------
# Public kernel API (callers in _core.py use these names; the wrappers below
# guarantee contiguous float64 inputs so the @njit kernels see clean strides)
# ---------------------------------------------------------------------------

# Small-N gate (F-1-12). The naive sequential summation inside the @njit
# kernels has error growth O(N·u) per Higham 2002 §4.2; for N ≤ 8 this is
# < 8·2.2e-16·exp_magnitude_max which sits below the 1e-12 rtol asserted
# by the regression tests. Callers requesting N > MAX_KERNEL_N should
# request a Kahan-compensated kernel or fall through to the scipy path.
MAX_KERNEL_N = 8


def _check_small_n(n_states: int, fn_name: str) -> None:
    if n_states > MAX_KERNEL_N:
        raise ValueError(
            f"{fn_name}: kernel naive-summation accuracy is bounded by "
            f"O(N·u); refusing N={n_states} > MAX_KERNEL_N={MAX_KERNEL_N}. "
            "Open follow-up P1-EM-KERNELS-LARGE-N for Kahan-compensated kernel."
        )


def forward_log_kernel(
    log_pi: npt.NDArray[np.float64],
    log_transmat: npt.NDArray[np.float64],
    log_B: npt.NDArray[np.float64],
) -> tuple[np.ndarray, float]:
    """Compute (log α, log L) via the numba kernel (with numpy fallback).

    Equivalent to :func:`skie_ninja.models.regime._core.forward_log` up
    to floating-point summation order; ``rtol = 1e-12`` against the
    scipy reference is enforced by ``tests/unit/test_em_kernels.py``.
    """
    log_pi_c = np.ascontiguousarray(log_pi, dtype=np.float64)
    log_transmat_c = np.ascontiguousarray(log_transmat, dtype=np.float64)
    log_B_c = np.ascontiguousarray(log_B, dtype=np.float64)
    _check_small_n(int(log_B_c.shape[1]), "forward_log_kernel")
    if NUMBA_AVAILABLE:
        return _forward_log_njit(log_pi_c, log_transmat_c, log_B_c)
    return _forward_log_numpy_reference(log_pi_c, log_transmat_c, log_B_c)


def backward_log_kernel(
    log_transmat: npt.NDArray[np.float64],
    log_B: npt.NDArray[np.float64],
) -> np.ndarray:
    """Compute log β via the numba kernel (with numpy fallback)."""
    log_transmat_c = np.ascontiguousarray(log_transmat, dtype=np.float64)
    log_B_c = np.ascontiguousarray(log_B, dtype=np.float64)
    _check_small_n(int(log_B_c.shape[1]), "backward_log_kernel")
    if NUMBA_AVAILABLE:
        return _backward_log_njit(log_transmat_c, log_B_c)
    return _backward_log_numpy_reference(log_transmat_c, log_B_c)


def forward_log_from_prior_kernel(
    log_alpha_prior: npt.NDArray[np.float64],
    log_transmat: npt.NDArray[np.float64],
    log_B: npt.NDArray[np.float64],
    n_propagation_steps: int,
) -> tuple[np.ndarray, float]:
    """Compute prior-seeded (log α, log L) via the numba kernel."""
    if n_propagation_steps < 0:
        raise ValueError(
            f"n_propagation_steps must be >= 0; got {n_propagation_steps}."
        )
    log_alpha_prior_c = np.ascontiguousarray(log_alpha_prior, dtype=np.float64)
    log_transmat_c = np.ascontiguousarray(log_transmat, dtype=np.float64)
    log_B_c = np.ascontiguousarray(log_B, dtype=np.float64)
    _check_small_n(int(log_B_c.shape[1]), "forward_log_from_prior_kernel")
    if NUMBA_AVAILABLE:
        return _forward_log_from_prior_njit(
            log_alpha_prior_c,
            log_transmat_c,
            log_B_c,
            int(n_propagation_steps),
        )
    return _forward_log_from_prior_numpy_reference(
        log_alpha_prior_c,
        log_transmat_c,
        log_B_c,
        int(n_propagation_steps),
    )


def xi_sum_kernel(
    log_alpha: npt.NDArray[np.float64],
    log_transmat: npt.NDArray[np.float64],
    log_B: npt.NDArray[np.float64],
    log_beta: npt.NDArray[np.float64],
    log_likelihood: float,
) -> np.ndarray:
    """Streaming logsumexp_t of log ξ_t(i, j); avoids the (T-1, N, N) tensor."""
    log_alpha_c = np.ascontiguousarray(log_alpha, dtype=np.float64)
    log_transmat_c = np.ascontiguousarray(log_transmat, dtype=np.float64)
    log_B_c = np.ascontiguousarray(log_B, dtype=np.float64)
    log_beta_c = np.ascontiguousarray(log_beta, dtype=np.float64)
    _check_small_n(int(log_B_c.shape[1]), "xi_sum_kernel")
    if NUMBA_AVAILABLE:
        return _xi_sum_streaming_njit(
            log_alpha_c,
            log_transmat_c,
            log_B_c,
            log_beta_c,
            float(log_likelihood),
        )
    return _xi_sum_numpy_reference(
        log_alpha_c,
        log_transmat_c,
        log_B_c,
        log_beta_c,
        float(log_likelihood),
    )


# ---------------------------------------------------------------------------
# NumPy reference implementations (fallback when numba is unavailable; also
# used as the regression-test oracle for the numba paths)
# ---------------------------------------------------------------------------


def _forward_log_numpy_reference(
    log_pi: np.ndarray,
    log_transmat: np.ndarray,
    log_B: np.ndarray,
) -> tuple[np.ndarray, float]:
    t_len, n_states = log_B.shape
    log_alpha = np.empty((t_len, n_states), dtype=np.float64)
    log_alpha[0] = log_pi + log_B[0]
    for t in range(1, t_len):
        log_alpha[t] = log_B[t] + _scipy_logsumexp(
            log_alpha[t - 1][:, None] + log_transmat, axis=0
        )
    log_likelihood = float(_scipy_logsumexp(log_alpha[-1]))
    return log_alpha, log_likelihood


def _backward_log_numpy_reference(
    log_transmat: np.ndarray,
    log_B: np.ndarray,
) -> np.ndarray:
    t_len, n_states = log_B.shape
    log_beta = np.empty((t_len, n_states), dtype=np.float64)
    log_beta[-1] = 0.0
    for t in range(t_len - 2, -1, -1):
        log_beta[t] = _scipy_logsumexp(
            log_transmat + log_B[t + 1][None, :] + log_beta[t + 1][None, :],
            axis=1,
        )
    return log_beta


def _forward_log_from_prior_numpy_reference(
    log_alpha_prior: np.ndarray,
    log_transmat: np.ndarray,
    log_B: np.ndarray,
    n_propagation_steps: int,
) -> tuple[np.ndarray, float]:
    log_alpha_prop = log_alpha_prior
    for _ in range(n_propagation_steps):
        log_alpha_prop = _scipy_logsumexp(
            log_alpha_prop[:, None] + log_transmat, axis=0
        )
    t_len, n_states = log_B.shape
    log_alpha = np.empty((t_len, n_states), dtype=np.float64)
    log_alpha[0] = log_B[0] + log_alpha_prop
    for t in range(1, t_len):
        log_alpha[t] = log_B[t] + _scipy_logsumexp(
            log_alpha[t - 1][:, None] + log_transmat, axis=0
        )
    log_likelihood = float(_scipy_logsumexp(log_alpha[-1]))
    return log_alpha, log_likelihood


def _xi_sum_numpy_reference(
    log_alpha: np.ndarray,
    log_transmat: np.ndarray,
    log_B: np.ndarray,
    log_beta: np.ndarray,
    log_likelihood: float,
) -> np.ndarray:
    t_len, n_states = log_B.shape
    if t_len < 2:
        return np.full((n_states, n_states), -np.inf, dtype=np.float64)
    log_xi = (
        log_alpha[:-1, :, None]
        + log_transmat[None, :, :]
        + log_B[1:, None, :]
        + log_beta[1:, None, :]
        - log_likelihood
    )
    return _scipy_logsumexp(log_xi, axis=0)
