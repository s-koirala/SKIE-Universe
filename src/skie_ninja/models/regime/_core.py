"""Numerical core of the Gaussian HMM: log-space forward-backward + Baum-Welch EM.

This module is the stateless numerical substrate; the user-facing
:class:`skie_ninja.models.regime.hmm.GaussianHMM` class wraps these
functions with validation, persistence, and anti-look-ahead guards.

Numerical strategy
------------------

All recursions run in log-space using ``scipy.special.logsumexp`` to
avoid underflow on long sequences. This is the modern alternative to
Rabiner's 1989 scaling-factor approach (Rabiner §V.A), and is the form
used in Bishop 2006 PRML §13.2.4. Equivalence with naive-space
forward-backward on short numerically-stable sequences is a unit-test
acceptance gate.

References
----------

  - Rabiner, L. R. 1989. "A Tutorial on Hidden Markov Models and
    Selected Applications in Speech Recognition". *Proceedings of the
    IEEE* 77(2): 257-286. https://doi.org/10.1109/5.18626
  - Baum, L. E., Petrie, T., Soules, G., & Weiss, N. 1970. "A
    Maximization Technique Occurring in the Statistical Analysis of
    Probabilistic Functions of Markov Chains". *Annals of Mathematical
    Statistics* 41(1): 164-171.
    https://doi.org/10.1214/aoms/1177697196
  - Bishop, C. M. 2006. *Pattern Recognition and Machine Learning*,
    §13.2. Springer. ISBN 978-0-387-31073-2.
  - Viterbi, A. J. 1967. "Error bounds for convolutional codes and an
    asymptotically optimum decoding algorithm". *IEEE Transactions on
    Information Theory* 13(2): 260-269.
    https://doi.org/10.1109/TIT.1967.1054010

Scope note
----------

The API here is intentionally narrow:

  - ``log_emission_matrix`` — (T, N) log-emission-density matrix for
    Gaussian emissions under one of four covariance structures.
  - ``forward_log`` — log α_t(i) and total log-likelihood.
  - ``backward_log`` — log β_t(i).
  - ``forward_backward_log`` — posteriors γ, ξ.
  - ``baum_welch_em`` — EM loop returning fitted parameters and a
    log-likelihood trace.
  - ``viterbi_log`` — full-sequence MAP decoding. Package-private by
    convention: train-time diagnostic only. Deploy-time state inference
    is the causal forward filter in :mod:`..hmm`.

Callers must not use ``viterbi_log`` to generate deploy-time features
— it consumes the full sequence and therefore violates the project's
no-look-ahead invariant (project CLAUDE.md "Time-series integrity").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.special import logsumexp

CovarianceType = Literal["spherical", "diag", "tied", "full"]

# Floor applied to diagonal variance entries during the M-step to
# prevent singular covariance collapse (Rabiner 1989 §V.B note on
# "too few observations in some states"). Value chosen as a small
# multiple of float64 machine epsilon; propagated as an explicit
# caller parameter so it is logged, not hardcoded.
_DEFAULT_MIN_VAR = float(np.finfo(np.float64).eps) * 1e3

# Default EM convergence tolerance on per-sample log-likelihood delta.
# Pre-registered by ADR-0005; the module exposes it as a parameter,
# not a magic number — callers override via ``em_tol``. Value here
# is used only when the caller passes None.
_DEFAULT_EM_TOL = 1e-4

# Default EM iteration ceiling. Serves as a safety bound; well-posed
# fits converge in ~30 iterations on non-pathological data. Caller
# supplies via ``max_iter``.
_DEFAULT_MAX_ITER = 200


@dataclass(frozen=True)
class HMMParams:
    """Frozen record of a fitted Gaussian HMM's parameters.

    The combination ``(log_pi, log_transmat, means, covars,
    covariance_type)`` fully defines the generative model. All
    downstream hashing, serialization, and filtering reads these
    fields; no other state is carried forward from the EM loop.
    """

    log_pi: np.ndarray          # (N,) log initial-state probabilities
    log_transmat: np.ndarray    # (N, N) row-stochastic log transitions
    means: np.ndarray           # (N, d) emission means
    covars: np.ndarray          # shape depends on covariance_type:
                                #   spherical : (N,)
                                #   diag      : (N, d)
                                #   tied      : (d, d)
                                #   full      : (N, d, d)
    covariance_type: CovarianceType

    def n_states(self) -> int:
        return int(self.log_pi.shape[0])

    def dim(self) -> int:
        return int(self.means.shape[1])


@dataclass(frozen=True)
class BaumWelchResult:
    """What the EM loop returns. Carries convergence metadata for logs."""

    params: HMMParams
    log_likelihood: float
    log_likelihood_trace: np.ndarray      # (n_iter,) per-iteration total LL
    n_iter: int
    converged: bool
    covariance_floor: float               # variance floor actually used
    # F-1-5: record dead-state events across iterations (states whose
    # total responsibility Σ_t γ_t(i) fell below 1 in a given iter).
    # A zero count signals a clean fit; non-zero signals the caller
    # should consider reducing n_states or widening the data window.
    dead_state_events: int = 0
    # F-1-4: count of iterations where a tied/full ridge was needed
    # to restore positive-definiteness. Zero = MLE-clean; positive =
    # regularised — disclose in sidecar.
    pd_ridge_events: int = 0


# ---------------------------------------------------------------------------
# Emission log-densities
# ---------------------------------------------------------------------------


def log_emission_matrix(
    x: npt.NDArray[np.float64],
    means: npt.NDArray[np.float64],
    covars: npt.NDArray[np.float64],
    covariance_type: CovarianceType,
) -> np.ndarray:
    """Compute the (T, N) matrix of log Gaussian emission densities.

    Parameters
    ----------
    x
        (T, d) observations. Must be finite.
    means
        (N, d) emission means.
    covars
        State-conditional covariance. Shape depends on
        ``covariance_type``:
        - ``spherical``: (N,)            — scalar variance per state
        - ``diag``:      (N, d)          — diagonal entries per state
        - ``tied``:      (d, d)          — one covariance shared across states
        - ``full``:      (N, d, d)       — full covariance per state
    covariance_type
        Selects the parameterization of ``covars``.

    Returns
    -------
    log_B
        (T, N) matrix with entries ``log N(x_t | μ_i, Σ_i)``.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    if x.ndim != 2:
        raise ValueError(
            f"x must be 1-D or 2-D (T,d); got shape {x.shape!r}."
        )
    if not np.all(np.isfinite(x)):
        raise ValueError("Observations contain NaN or inf.")

    t_len, dim = x.shape
    n_states = means.shape[0]
    if means.shape != (n_states, dim):
        raise ValueError(
            f"means shape {means.shape} does not match (N, d) = "
            f"({n_states}, {dim})."
        )

    # Route by covariance type. Each branch computes log N via the
    # standard multivariate Gaussian log-density:
    #   log N(x | μ, Σ) = -0.5 * (d log(2π) + log|Σ| + (x-μ)^T Σ^{-1} (x-μ))
    const_term = -0.5 * dim * np.log(2.0 * np.pi)

    if covariance_type == "spherical":
        if covars.shape != (n_states,):
            raise ValueError(
                f"spherical covars shape {covars.shape} != (N,) = ({n_states},)"
            )
        if np.any(covars <= 0):
            raise ValueError("spherical covars must be strictly positive.")
        log_B = np.empty((t_len, n_states), dtype=np.float64)
        for i in range(n_states):
            diff = x - means[i]                              # (T, d)
            sq = np.einsum("td,td->t", diff, diff)           # (T,)
            sigma2 = float(covars[i])
            log_det = dim * np.log(sigma2)
            log_B[:, i] = const_term - 0.5 * (log_det + sq / sigma2)
        return log_B

    if covariance_type == "diag":
        if covars.shape != (n_states, dim):
            raise ValueError(
                f"diag covars shape {covars.shape} != (N, d) = "
                f"({n_states}, {dim})."
            )
        if np.any(covars <= 0):
            raise ValueError("diag covars must be strictly positive.")
        log_B = np.empty((t_len, n_states), dtype=np.float64)
        for i in range(n_states):
            diff = x - means[i]                              # (T, d)
            var = covars[i]                                  # (d,)
            log_det = np.sum(np.log(var))
            sq = np.sum(diff * diff / var, axis=1)           # (T,)
            log_B[:, i] = const_term - 0.5 * (log_det + sq)
        return log_B

    if covariance_type == "tied":
        if covars.shape != (dim, dim):
            raise ValueError(
                f"tied covars shape {covars.shape} != (d, d) = "
                f"({dim}, {dim})."
            )
        # Cholesky for numerical stability over direct inversion.
        try:
            L = np.linalg.cholesky(covars)
        except np.linalg.LinAlgError as exc:
            raise ValueError(
                "tied covariance is not positive-definite."
            ) from exc
        log_det = 2.0 * np.sum(np.log(np.diag(L)))
        log_B = np.empty((t_len, n_states), dtype=np.float64)
        for i in range(n_states):
            diff = x - means[i]                              # (T, d)
            # solve L z = diff^T  →  z = L^{-1} diff^T; Mahal = ||z||^2
            z = np.linalg.solve(L, diff.T).T                 # (T, d)
            sq = np.einsum("td,td->t", z, z)
            log_B[:, i] = const_term - 0.5 * (log_det + sq)
        return log_B

    if covariance_type == "full":
        if covars.shape != (n_states, dim, dim):
            raise ValueError(
                f"full covars shape {covars.shape} != (N, d, d) = "
                f"({n_states}, {dim}, {dim})."
            )
        log_B = np.empty((t_len, n_states), dtype=np.float64)
        for i in range(n_states):
            try:
                L = np.linalg.cholesky(covars[i])
            except np.linalg.LinAlgError as exc:
                raise ValueError(
                    f"full covariance for state {i} is not "
                    "positive-definite."
                ) from exc
            log_det = 2.0 * np.sum(np.log(np.diag(L)))
            diff = x - means[i]
            z = np.linalg.solve(L, diff.T).T
            sq = np.einsum("td,td->t", z, z)
            log_B[:, i] = const_term - 0.5 * (log_det + sq)
        return log_B

    raise ValueError(f"Unknown covariance_type {covariance_type!r}.")


# ---------------------------------------------------------------------------
# Forward / backward / forward-backward
# ---------------------------------------------------------------------------


def forward_log(
    log_pi: npt.NDArray[np.float64],
    log_transmat: npt.NDArray[np.float64],
    log_B: npt.NDArray[np.float64],
) -> tuple[np.ndarray, float]:
    """Log-space forward recursion.

    Computes ``log α_t(i) = log P(y_{1:t}, q_t = i | λ)`` and the
    total log-likelihood ``log P(y_{1:T} | λ) = logsumexp_i log α_T(i)``.

    Recursion (Rabiner 1989 §III.A "Forward procedure", in log-space):

        log α_1(i) = log π_i + log b_i(y_1)
        log α_t(j) = log b_j(y_t) + logsumexp_i [ log α_{t-1}(i) + log a_ij ]

    All arithmetic in log-space; no scaling factors needed.
    """
    log_B = np.asarray(log_B, dtype=np.float64)
    t_len, n_states = log_B.shape
    log_alpha = np.empty((t_len, n_states), dtype=np.float64)
    log_alpha[0] = log_pi + log_B[0]
    for t in range(1, t_len):
        # For each destination j, log α_t(j) = log b_j(y_t) +
        # logsumexp_i(log α_{t-1}(i) + log a_ij). Broadcasting:
        # log_alpha[t-1][:, None] + log_transmat  → (N_src, N_dst)
        log_alpha[t] = log_B[t] + logsumexp(
            log_alpha[t - 1][:, None] + log_transmat, axis=0
        )
    log_likelihood = float(logsumexp(log_alpha[-1]))
    return log_alpha, log_likelihood


def backward_log(
    log_transmat: npt.NDArray[np.float64],
    log_B: npt.NDArray[np.float64],
) -> np.ndarray:
    """Log-space backward recursion (Rabiner 1989 §III.A "Backward procedure", in log-space).

    Recursion:

        log β_T(i) = 0
        log β_t(i) = logsumexp_j [ log a_ij + log b_j(y_{t+1}) + log β_{t+1}(j) ]
    """
    log_B = np.asarray(log_B, dtype=np.float64)
    t_len, n_states = log_B.shape
    log_beta = np.empty((t_len, n_states), dtype=np.float64)
    log_beta[-1] = 0.0
    for t in range(t_len - 2, -1, -1):
        log_beta[t] = logsumexp(
            log_transmat + log_B[t + 1][None, :] + log_beta[t + 1][None, :],
            axis=1,
        )
    return log_beta


def forward_backward_log(
    log_pi: npt.NDArray[np.float64],
    log_transmat: npt.NDArray[np.float64],
    log_B: npt.NDArray[np.float64],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Run full forward-backward and return posteriors in log-space.

    Returns
    -------
    log_alpha
        (T, N) forward messages.
    log_beta
        (T, N) backward messages.
    log_gamma
        (T, N) state posteriors ``log P(q_t = i | y_{1:T})``.
    log_xi_sum
        (N, N) log of Σ_{t=1..T-1} P(q_t=i, q_{t+1}=j | y_{1:T});
        sufficient statistic for the M-step of the transition matrix.
        Returned in summed (rather than per-timestep) form to bound
        memory at O(N²) rather than O(T·N²).
    log_likelihood
        Scalar total log-likelihood.

    Implementation notes
    --------------------

    - γ and ξ are derived from α, β via the Rabiner 1989 §III.B
      posterior identities in log-space; per-timestep normalisation by
      ``log_likelihood`` guarantees each γ_t sums to exactly 1 in
      exp-space (up to logsumexp round-off).
    - ``log_xi_sum`` is the O(N²) sufficient statistic for the M-step
      transition update. We compute per-timestep ξ_t in log-space and
      logsumexp-accumulate across t, avoiding the need to materialise
      the full (T, N, N) tensor.
    """
    log_alpha, log_likelihood = forward_log(log_pi, log_transmat, log_B)
    log_beta = backward_log(log_transmat, log_B)

    log_gamma = log_alpha + log_beta - log_likelihood

    # ξ_t(i, j) ∝ α_t(i) · a_ij · b_j(y_{t+1}) · β_{t+1}(j)
    # Per-t log ξ_t(i,j) = log α_t(i) + log a_ij + log b_j(y_{t+1})
    #                      + log β_{t+1}(j) - log_likelihood
    t_len = log_B.shape[0]
    n_states = log_B.shape[1]
    # Build (T-1, N, N) in log-space and logsumexp over the t axis.
    log_xi = (
        log_alpha[:-1, :, None]
        + log_transmat[None, :, :]
        + log_B[1:, None, :]
        + log_beta[1:, None, :]
        - log_likelihood
    )
    # Guard: T=1 case — no transitions, return -inf matrix.
    if t_len < 2:
        log_xi_sum = np.full((n_states, n_states), -np.inf, dtype=np.float64)
    else:
        log_xi_sum = logsumexp(log_xi, axis=0)
    return log_alpha, log_beta, log_gamma, log_xi_sum, log_likelihood


# ---------------------------------------------------------------------------
# Viterbi (train-time MAP; NOT for deploy-time features — see module docstring)
# ---------------------------------------------------------------------------


def viterbi_log(
    log_pi: npt.NDArray[np.float64],
    log_transmat: npt.NDArray[np.float64],
    log_B: npt.NDArray[np.float64],
) -> tuple[np.ndarray, float]:
    """Full-sequence MAP state path (Viterbi 1967).

    Returns the (T,) integer state path and the log-probability of
    that path. Consumes the complete observation sequence and is
    therefore **non-causal** — train-time diagnostic only.

    Recursion:

        δ_1(i) = log π_i + log b_i(y_1)
        δ_t(j) = log b_j(y_t) + max_i [ δ_{t-1}(i) + log a_ij ]
        ψ_t(j) = argmax_i [ δ_{t-1}(i) + log a_ij ]
    """
    t_len, n_states = log_B.shape
    delta = np.empty((t_len, n_states), dtype=np.float64)
    psi = np.empty((t_len, n_states), dtype=np.int64)
    delta[0] = log_pi + log_B[0]
    psi[0] = 0
    for t in range(1, t_len):
        scores = delta[t - 1][:, None] + log_transmat     # (N_src, N_dst)
        psi[t] = np.argmax(scores, axis=0)
        delta[t] = log_B[t] + scores[psi[t], np.arange(n_states)]

    path = np.empty(t_len, dtype=np.int64)
    path[-1] = int(np.argmax(delta[-1]))
    log_prob = float(delta[-1, path[-1]])
    for t in range(t_len - 2, -1, -1):
        path[t] = psi[t + 1, path[t + 1]]
    return path, log_prob


# ---------------------------------------------------------------------------
# M-step helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _MStepDiagnostics:
    """Per-iteration M-step diagnostics propagated to the fit record."""

    dead_states: int      # states with Σ_t γ_t(i) < 1
    pd_ridge_applied: bool  # tied/full: True iff ridge was needed for PD


def _ensure_pd(
    mat: np.ndarray, min_var: float
) -> tuple[np.ndarray, bool]:
    """Return (mat_pd, ridge_applied). Add min_var·I only if needed.

    F-1-4: unconditionally adding ``min_var·I`` biases the MLE. We
    attempt a Cholesky on the raw MLE; if it fails (or the smallest
    eigenvalue is below ``min_var``), we add exactly enough ridge to
    restore PD and record that the floor activated.
    """
    dim = mat.shape[0]
    try:
        L = np.linalg.cholesky(mat)
        # Catch near-singular: smallest diagonal of L^2 ≈ smallest
        # eigenvalue lower bound; floor on that.
        if float(np.min(np.diag(L))) ** 2 < min_var:
            return mat + min_var * np.eye(dim), True
        return mat, False
    except np.linalg.LinAlgError:
        return mat + min_var * np.eye(dim), True


def _m_step_emissions(
    x: np.ndarray,
    log_gamma: np.ndarray,
    covariance_type: CovarianceType,
    min_var: float,
) -> tuple[np.ndarray, np.ndarray, _MStepDiagnostics]:
    """Compute maximum-likelihood Gaussian emission parameters.

    γ̂_t(i) = exp(log_gamma[t,i]) are state responsibilities. Standard
    Baum-Welch M-step updates (Rabiner 1989 §III.C "Solution to
    Problem 3" — re-estimation formulas — generalised to multivariate
    Gaussian; cf. Bishop 2006 §13.2.2):

        μ_i = Σ_t γ_t(i) x_t / Σ_t γ_t(i)
        Σ_i = Σ_t γ_t(i) (x_t - μ_i)(x_t - μ_i)^T / Σ_t γ_t(i)

    Variance floor ``min_var`` applied element-wise on diagonals (and
    spherical scalars) to prevent singular collapse. Full and tied
    covariances receive min_var · I added if the matrix becomes
    non-PD within the EM loop — a last-resort floor only (see note
    in module docstring).
    """
    gamma = np.exp(log_gamma)                        # (T, N)
    n_states = gamma.shape[1]
    dim = x.shape[1]

    # Normalise once; rows of (T, N) sum to 1 in exp-space but the
    # total weight per state is Σ_t γ_t(i).
    weight = gamma.sum(axis=0)                       # (N,)
    # F-1-5: a state with total responsibility < 1 is effectively
    # unused — EM cannot estimate it. Count such states and floor the
    # divisor so the M-step does not blow up. The caller surfaces the
    # count via BaumWelchResult.dead_state_events.
    dead_states = int(np.sum(weight < 1.0))
    safe_weight = np.maximum(weight, float(np.finfo(np.float64).tiny))

    # μ — shared across covariance types.
    means = (gamma.T @ x) / safe_weight[:, None]     # (N, d)

    if covariance_type == "spherical":
        # σ²_i = average squared deviation across dimensions.
        covars = np.empty(n_states, dtype=np.float64)
        for i in range(n_states):
            diff = x - means[i]
            sq = np.einsum("td,td->t", diff, diff)   # (T,)
            covars[i] = float((gamma[:, i] * sq).sum() / (safe_weight[i] * dim))
        covars = np.maximum(covars, min_var)
        return means, covars, _MStepDiagnostics(dead_states, False)

    if covariance_type == "diag":
        covars = np.empty((n_states, dim), dtype=np.float64)
        for i in range(n_states):
            diff = x - means[i]
            covars[i] = (gamma[:, i][:, None] * diff * diff).sum(axis=0) / safe_weight[i]
        covars = np.maximum(covars, min_var)
        return means, covars, _MStepDiagnostics(dead_states, False)

    if covariance_type == "tied":
        # Shared covariance across states.
        acc = np.zeros((dim, dim), dtype=np.float64)
        for i in range(n_states):
            diff = x - means[i]
            acc += (gamma[:, i][:, None] * diff).T @ diff
        total_weight = weight.sum()
        tied_cov = acc / max(total_weight, float(np.finfo(np.float64).tiny))
        # F-1-4: add ridge only if the raw MLE is not sufficiently PD.
        tied_cov, ridge = _ensure_pd(tied_cov, min_var)
        return means, tied_cov, _MStepDiagnostics(dead_states, ridge)

    if covariance_type == "full":
        covars = np.empty((n_states, dim, dim), dtype=np.float64)
        any_ridge = False
        for i in range(n_states):
            diff = x - means[i]
            raw = (gamma[:, i][:, None] * diff).T @ diff / safe_weight[i]
            # F-1-4: conditional ridge per state.
            fixed, ridge = _ensure_pd(raw, min_var)
            any_ridge = any_ridge or ridge
            covars[i] = fixed
        return means, covars, _MStepDiagnostics(dead_states, any_ridge)

    raise ValueError(f"Unknown covariance_type {covariance_type!r}.")


# ---------------------------------------------------------------------------
# Baum-Welch EM
# ---------------------------------------------------------------------------


def baum_welch_em(
    x: npt.NDArray[np.float64],
    *,
    initial_params: HMMParams,
    em_tol: float | None = None,
    max_iter: int | None = None,
    min_var: float | None = None,
) -> BaumWelchResult:
    """Baum-Welch EM with log-space forward-backward.

    Parameters
    ----------
    x
        (T, d) observations.
    initial_params
        Starting point for EM. The caller is responsible for choosing
        the initialization strategy (k-means++ warm start in this
        package; see :mod:`..hmm`).
    em_tol
        Convergence tolerance on per-sample log-likelihood delta. EM
        halts when ``(LL_new - LL_old) / T < em_tol`` for positive
        increments, or when LL decreases (numerical non-monotonicity
        — should not happen in exact arithmetic, but float64 round-off
        can nudge the LL sideways near the optimum).
    max_iter
        Hard iteration cap.
    min_var
        Variance floor for the M-step (see :func:`_m_step_emissions`).

    Returns
    -------
    :class:`BaumWelchResult`
        Fitted params, final log-likelihood, per-iteration LL trace,
        iteration count, convergence flag, and the covariance floor
        actually applied (propagated so the caller logs the value
        into the sidecar / ReproLog).
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    if not np.all(np.isfinite(x)):
        raise ValueError("baum_welch_em: observations contain NaN or inf.")

    tol = _DEFAULT_EM_TOL if em_tol is None else float(em_tol)
    max_it = _DEFAULT_MAX_ITER if max_iter is None else int(max_iter)
    # F-1-3: when caller does not supply min_var, derive a
    # scale-adaptive default as a small fraction of the smallest
    # per-dimension sample variance. eps·1e3 is too small for data on
    # scales ≫ 1; scaling by sample variance makes the floor
    # meaningful across arbitrary input scales.
    if min_var is None:
        sample_var = np.var(x, axis=0, ddof=0)
        scale = float(np.min(sample_var[sample_var > 0])) if np.any(sample_var > 0) else 1.0
        mvar = max(_DEFAULT_MIN_VAR, scale * 1e-6)
    else:
        mvar = float(min_var)
    if tol < 0:
        raise ValueError("em_tol must be non-negative.")
    if max_it < 1:
        raise ValueError("max_iter must be >= 1.")
    if mvar <= 0:
        raise ValueError("min_var must be strictly positive.")

    params = initial_params
    t_len = x.shape[0]
    ll_history: list[float] = []
    prev_ll = -np.inf
    converged = False
    dead_state_events = 0
    pd_ridge_events = 0

    for iteration in range(max_it):
        log_B = log_emission_matrix(
            x, params.means, params.covars, params.covariance_type
        )
        _, _, log_gamma, log_xi_sum, log_ll = forward_backward_log(
            params.log_pi, params.log_transmat, log_B
        )
        ll_history.append(log_ll)

        # Convergence check on per-sample LL delta. Checked BEFORE the
        # M-step so the returned params correspond to the reported LL.
        if iteration > 0:
            delta = (log_ll - prev_ll) / max(t_len, 1)
            # Allow tiny negative deltas from float64 roundoff; fail
            # hard only on sizeable decreases (would indicate a bug).
            if delta < -1e-6:
                raise RuntimeError(
                    f"Baum-Welch log-likelihood decreased by "
                    f"{-delta:.3e} at iter {iteration}; this should "
                    "not happen in exact arithmetic. Inspect inputs."
                )
            if abs(delta) < tol:
                converged = True
                break
        prev_ll = log_ll

        # F-1-1: on the final iteration we must NOT update params
        # after recording ``log_ll``, otherwise the returned params do
        # not correspond to ``ll_history[-1]``. Break out cleanly.
        if iteration == max_it - 1:
            break

        # ---- M-step ----
        # π_i = γ_1(i) → log π_i = log γ_1(i). Already normalised.
        new_log_pi = log_gamma[0].copy()

        # a_ij = exp(log ξ_sum[i,j] - log Σ_j' ξ_sum[i,j'])
        new_log_transmat = log_xi_sum - logsumexp(log_xi_sum, axis=1, keepdims=True)

        new_means, new_covars, diag = _m_step_emissions(
            x, log_gamma, params.covariance_type, mvar
        )
        if diag.dead_states > 0:
            dead_state_events += diag.dead_states
        if diag.pd_ridge_applied:
            pd_ridge_events += 1
        params = HMMParams(
            log_pi=new_log_pi,
            log_transmat=new_log_transmat,
            means=new_means,
            covars=new_covars,
            covariance_type=params.covariance_type,
        )

    return BaumWelchResult(
        params=params,
        log_likelihood=ll_history[-1],
        log_likelihood_trace=np.asarray(ll_history, dtype=np.float64),
        n_iter=len(ll_history),
        converged=converged,
        covariance_floor=mvar,
        dead_state_events=dead_state_events,
        pd_ridge_events=pd_ridge_events,
    )


# ---------------------------------------------------------------------------
# Parameter counting — inputs to BIC
# ---------------------------------------------------------------------------


def count_free_parameters(
    n_states: int,
    dim: int,
    covariance_type: CovarianceType,
) -> int:
    """Count free (identifiable) parameters of a Gaussian HMM.

    Used as the ``k`` in BIC = -2 log L + k log T (Schwarz 1978).
    Identifiability accounting:

      - Initial distribution: N probabilities summing to 1
        → ``N - 1`` free.
      - Transition matrix: N rows of N probabilities, each summing
        to 1 → ``N (N - 1)`` free.
      - Emission means: ``N d`` free.
      - Emission covariances, by type:
          spherical: N free (one scalar per state)
          diag    : N d free
          tied    : d(d+1)/2 free (one shared PD matrix)
          full    : N d(d+1)/2 free

    Rationale for this accounting: Celeux & Durand 2008 §3.1 and
    Rabiner 1989 §III.C.2 both use the (N-1) and N(N-1) simplex
    counts. The "label-switching" redundancy (Stephens 2000) is a
    non-identifiability of the *labelling*, not of the parameters
    themselves; BIC conventionally does not subtract for it.
    """
    if n_states < 1 or dim < 1:
        raise ValueError(f"n_states={n_states}, dim={dim}; both must be >= 1.")

    k_pi = n_states - 1
    k_trans = n_states * (n_states - 1)
    k_means = n_states * dim
    if covariance_type == "spherical":
        k_covar = n_states
    elif covariance_type == "diag":
        k_covar = n_states * dim
    elif covariance_type == "tied":
        k_covar = dim * (dim + 1) // 2
    elif covariance_type == "full":
        k_covar = n_states * dim * (dim + 1) // 2
    else:
        raise ValueError(f"Unknown covariance_type {covariance_type!r}.")
    return k_pi + k_trans + k_means + k_covar


def bic(
    log_likelihood: float,
    n_states: int,
    dim: int,
    covariance_type: CovarianceType,
    t_len: int,
) -> float:
    """Bayesian Information Criterion (Schwarz 1978).

    BIC = -2 log L + k log T. Lower is better; the minimiser over a
    model grid is the BIC-selected model. Sign convention matches
    Schwarz 1978 eq. 3; hmmlearn and most textbook presentations use
    this form.
    """
    if t_len < 1:
        raise ValueError("t_len must be >= 1.")
    k = count_free_parameters(n_states, dim, covariance_type)
    return -2.0 * log_likelihood + k * np.log(t_len)
