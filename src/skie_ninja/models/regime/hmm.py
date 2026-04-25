"""User-facing Gaussian Hidden Markov Model.

Wraps the log-space numerical core in :mod:`._core` with:

  - k-means++ initialisation (sklearn).
  - Multi-restart EM with a fixed operational min-restart floor
    (ADR-0005 § "Hyperparameter governance"); the bootstrap-ε adaptive
    restart rule (tracked as Phase-1 follow-up
    ``P1-HMM-ADAPTIVE-RESTART``) is the principled replacement and is
    not yet implemented. The default floor of 5 is an operational
    choice balancing coverage against cost for Cycle 3 — not a value
    drawn from published literature. Biernacki, Celeux, Govaert 2003
    ("Choosing starting values …", CSDA 41) motivates *why* multiple
    starts matter but does not prescribe a universal count.
  - Post-fit label-switching canonicalisation by emission-mean rank
    (pre-registered per hypothesis; default ordering documented in
    :meth:`GaussianHMM.canonicalise`).
  - Three distinct state-inference entry points (all causal):
      * :meth:`GaussianHMM.filter_states` — causal forward filter
        seeded from the fitted ``log π``. Returns
        ``α_t = P(q_t = i | y_{1:t})``. Safe for feature generation
        under the project's no-look-ahead rule (CLAUDE.md "Time-series
        integrity").
      * :meth:`GaussianHMM.terminal_log_alpha` /
        :meth:`GaussianHMM.filter_states_from_prior` — warm-start
        variant for walk-forward CV fold boundaries (ADR-0005
        §"Fold-boundary state continuity"). The test fold's filter is
        seeded from the train-fold terminal ``log α`` propagated K
        transition steps, where K is the purge+embargo gap. Anchored
        on the Hamilton-filter prediction step (Hamilton 1989
        Econometrica §3; Hamilton 1994 §22.4; Kim & Nelson 1999
        §4.2-4.3).
      * :meth:`GaussianHMM.viterbi_train_time` — full-sequence MAP
        decoding via :func:`._core.viterbi_log`. Kept behind a
        deliberately verbose method name because misuse would break
        the no-look-ahead invariant. Downstream feature code must
        never call this.

References
----------

  - Rabiner, L. R. 1989. Proc. IEEE 77(2):257-286.
  - Baum, L. E., Petrie, T., Soules, G., Weiss, N. 1970. Ann. Math.
    Stat. 41(1):164-171.
  - Bishop, C. M. 2006. *Pattern Recognition and Machine Learning*,
    §13.2.
  - Biernacki, C., Celeux, G., Govaert, G. 2003. "Choosing starting
    values for the EM algorithm for getting the highest likelihood
    in multivariate Gaussian mixture models". *Computational
    Statistics & Data Analysis* 41(3-4): 561-575.
    https://doi.org/10.1016/S0167-9473(02)00163-9 — cited for the
    *motivation* that multi-start EM is required; does not prescribe
    the specific restart count used here.
  - Stephens, M. 2000. "Dealing with label switching in mixture
    models". *Journal of the Royal Statistical Society: Series B*
    62(4): 795-809. https://doi.org/10.1111/1467-9868.00265
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.special import logsumexp

from skie_ninja.models.regime._core import (
    BaumWelchResult,
    CovarianceType,
    HMMParams,
    _DEFAULT_EM_TOL,
    _DEFAULT_MAX_ITER,
    _DEFAULT_MIN_VAR,
    baum_welch_em,
    forward_log,
    forward_log_from_prior,
    log_emission_matrix,
    viterbi_log,
)

# Operational floor for random restarts under the Cycle-3 fixed-bracket
# policy. This is NOT drawn from published literature — it is an
# engineering choice (ADR-0005 §"Hyperparameter governance") that
# balances coverage against cost while the bootstrap-ε adaptive rule
# (P1-HMM-ADAPTIVE-RESTART) is pending. Cycle 3 uses a fixed bracket
# [min_restarts, max_restarts] with a simple early-exit when the top
# two log-likelihoods agree to within em_tol — a conservative proxy
# until the adaptive rule lands.
_MIN_RESTARTS_FLOOR = 5

CanonicalOrder = Literal["mean_ascending", "mean_descending"]


@dataclass(frozen=True)
class FitResult:
    """Outcome of a multi-restart EM fit.

    The selected (best-LL) params are stored on the wrapping
    :class:`GaussianHMM`; this record documents the fit process for
    the sidecar / audit trail.
    """

    best_log_likelihood: float
    n_restarts_used: int
    per_restart_log_likelihood: np.ndarray  # (n_restarts_used,)
    per_restart_n_iter: np.ndarray  # (n_restarts_used,)
    per_restart_converged: np.ndarray  # (n_restarts_used,) bool
    covariance_floor: float
    em_tol: float
    max_iter: int
    seed: int
    init_strategy: str


@dataclass
class GaussianHMM:
    """Fit-then-filter Gaussian HMM with explicit no-look-ahead guard.

    After :meth:`fit`, parameters are frozen on the instance. The
    public state-inference entry point is :meth:`filter_states`
    (causal forward filter). The full-sequence Viterbi decoder is
    available through the intentionally verbose
    :meth:`viterbi_train_time` method.

    Parameters
    ----------
    n_states
        Number of latent states. Must be >= 2 (ADR-0005 §
        "Hyperparameter governance" — single-state is not a regime
        model).
    covariance_type
        One of ``{"spherical", "diag", "tied", "full"}``.
    em_tol
        Convergence tolerance on per-sample log-likelihood delta.
    max_iter
        Hard EM iteration cap.
    min_var
        Variance floor for the M-step.
    canonical_order
        Post-fit relabel rule to canonicalise the label-switching
        identifiability (Stephens 2000). Two ordering rules are
        provided; more can be added as additional rules are
        pre-registered at hypothesis design time.
    """

    n_states: int
    covariance_type: CovarianceType = "diag"
    em_tol: float = _DEFAULT_EM_TOL
    max_iter: int = _DEFAULT_MAX_ITER
    min_var: float = _DEFAULT_MIN_VAR
    canonical_order: CanonicalOrder = "mean_ascending"

    params_: HMMParams | None = field(default=None, init=False)
    fit_result_: FitResult | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.n_states < 2:
            raise ValueError(f"n_states must be >= 2 (ADR-0005); got {self.n_states}.")

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    def fit(
        self,
        x: npt.ArrayLike,
        *,
        seed: int,
        min_restarts: int = _MIN_RESTARTS_FLOOR,
        max_restarts: int = 20,
        init_strategy: Literal["kmeans++"] = "kmeans++",
    ) -> GaussianHMM:
        """Multi-restart EM fit.

        Parameters
        ----------
        x
            (T, d) or (T,) observations.
        seed
            Master RNG seed. Restart-specific seeds are derived
            deterministically from this via :meth:`np.random.SeedSequence`
            so that a fixed ``seed`` yields identical fits across
            Python processes (subject to BLAS threading, which
            ``_core.baum_welch_em`` does not depend on for correctness).
        min_restarts
            Minimum number of random restarts. Floored at
            ``_MIN_RESTARTS_FLOOR`` (ADR-0005).
        max_restarts
            Upper bracket on restarts.
        init_strategy
            Currently only ``"kmeans++"``. Future additions will pass
            through as a ``Literal`` enlargement.
        """
        if min_restarts < _MIN_RESTARTS_FLOOR:
            raise ValueError(
                f"min_restarts must be >= {_MIN_RESTARTS_FLOOR} "
                f"(ADR-0005 operational floor — not a literature value); "
                f"got {min_restarts}."
            )
        if max_restarts < min_restarts:
            raise ValueError(f"max_restarts ({max_restarts}) < min_restarts ({min_restarts}).")

        x_arr = np.asarray(x, dtype=np.float64)
        if x_arr.ndim == 1:
            x_arr = x_arr.reshape(-1, 1)
        if x_arr.ndim != 2:
            raise ValueError(f"x must be 1-D or 2-D (T,d); got shape {x_arr.shape!r}.")
        if x_arr.shape[0] < self.n_states * 5:
            # Not a statistical test, just a pragmatic lower bound that
            # the caller can override by constructing an HMM with a
            # smaller n_states. Rabiner 1989 §V.B warns about
            # "insufficient training data" producing singular
            # covariances; a handful of observations per state is the
            # bare minimum.
            raise ValueError(
                f"Too few observations ({x_arr.shape[0]}) for n_states="
                f"{self.n_states}. Require at least 5·n_states; add "
                "data or reduce n_states."
            )

        ss = np.random.SeedSequence(int(seed))
        child_seeds = ss.generate_state(max_restarts)

        best: BaumWelchResult | None = None
        per_ll: list[float] = []
        per_iter: list[int] = []
        per_conv: list[bool] = []

        for r in range(max_restarts):
            init = _initial_params(
                x_arr,
                n_states=self.n_states,
                covariance_type=self.covariance_type,
                min_var=self.min_var,
                seed=int(child_seeds[r]),
                strategy=init_strategy,
            )
            res = baum_welch_em(
                x_arr,
                initial_params=init,
                em_tol=self.em_tol,
                max_iter=self.max_iter,
                min_var=self.min_var,
            )
            per_ll.append(res.log_likelihood)
            per_iter.append(res.n_iter)
            per_conv.append(res.converged)

            if best is None or res.log_likelihood > best.log_likelihood:
                best = res

            # Early-exit: we have at least ``min_restarts`` restarts
            # and the top two log-likelihoods agree to within em_tol.
            # This is a conservative proxy for the bootstrap-ε rule
            # in ADR-0005 (tracked as P1-HMM-ADAPTIVE-RESTART).
            if r + 1 >= min_restarts:
                sorted_ll = sorted(per_ll, reverse=True)
                if len(sorted_ll) >= 2 and abs(sorted_ll[0] - sorted_ll[1]) < self.em_tol:
                    break

        assert best is not None  # loop always runs at least once

        canonical_params = _canonicalise(best.params, self.canonical_order)
        self.params_ = canonical_params
        self.fit_result_ = FitResult(
            best_log_likelihood=best.log_likelihood,
            n_restarts_used=len(per_ll),
            per_restart_log_likelihood=np.asarray(per_ll, dtype=np.float64),
            per_restart_n_iter=np.asarray(per_iter, dtype=np.int64),
            per_restart_converged=np.asarray(per_conv, dtype=bool),
            covariance_floor=best.covariance_floor,
            em_tol=self.em_tol,
            max_iter=self.max_iter,
            seed=int(seed),
            init_strategy=init_strategy,
        )
        return self

    # ------------------------------------------------------------------
    # Causal inference — the public production entry point
    # ------------------------------------------------------------------

    def filter_states(self, x: npt.ArrayLike) -> np.ndarray:
        """Causal forward filter: ``P(q_t = i | y_{1:t})`` for each t.

        **This is the no-look-ahead deploy-time inference path.** At
        each t, the posterior state distribution depends only on
        observations up to and including t. Safe for generating
        features that the downstream backtest engine will consume.

        Implementation: run the log-space forward recursion; at each
        step normalise ``log α_t(i) - logsumexp_i log α_t(i)`` to
        obtain the filtered log-posterior. exp at the end.

        Returns
        -------
        (T, N) float array whose rows sum to 1.
        """
        self._require_fitted()
        assert self.params_ is not None
        x_arr = _coerce_obs(x, expect_dim=self.params_.dim())
        log_B = log_emission_matrix(
            x_arr,
            self.params_.means,
            self.params_.covars,
            self.params_.covariance_type,
        )
        log_alpha, _ = forward_log(self.params_.log_pi, self.params_.log_transmat, log_B)
        # Normalise each row: log_alpha[t] - logsumexp(log_alpha[t]).
        log_norm = logsumexp(log_alpha, axis=1, keepdims=True)
        return np.exp(log_alpha - log_norm)

    def terminal_log_alpha(self, x: npt.ArrayLike) -> np.ndarray:
        """Unnormalised log α_T after running the forward filter on ``x``.

        Returns the (N,) joint log-probability ``log P(s_T = i, y_{1:T} | λ)``
        at the final observation. Causal: depends only on ``y_{1:T}``.

        Used at walk-forward fold boundaries to harvest the train-fold
        terminal posterior for warm-start propagation into the test fold
        (ADR-0005 §"Fold-boundary state continuity"; see
        :meth:`filter_states_from_prior`).
        """
        self._require_fitted()
        assert self.params_ is not None
        x_arr = _coerce_obs(x, expect_dim=self.params_.dim())
        log_B = log_emission_matrix(
            x_arr,
            self.params_.means,
            self.params_.covars,
            self.params_.covariance_type,
        )
        log_alpha, _ = forward_log(self.params_.log_pi, self.params_.log_transmat, log_B)
        return log_alpha[-1].copy()

    def filter_states_from_prior(
        self,
        x: npt.ArrayLike,
        log_alpha_prior: npt.ArrayLike,
        *,
        n_propagation_steps: int,
    ) -> np.ndarray:
        """Causal forward filter seeded from a prior log α (warm-start).

        At walk-forward CV fold boundaries the train-fold terminal
        posterior `α(s_{T_train})` is the sufficient statistic for
        future-state inference (ADR-0005 §"Fold-boundary state
        continuity"; Hamilton 1989 Econometrica §3, Hamilton 1994 §22.4,
        Kim & Nelson 1999 §4.2-4.3, Frühwirth-Schnatter 2006 §11.4-11.5).
        Cold-starting from ``log_pi`` discards this statistic and
        introduces O(dwell-time) warm-up bias.

        Parameters
        ----------
        x
            (T, d) test-fold observations.
        log_alpha_prior
            (N,) train-fold terminal log α (e.g. from
            :meth:`terminal_log_alpha`). Unnormalised.
        n_propagation_steps
            Transition steps to apply before the first test emission.
            Required (no default): in walk-forward CV with non-zero
            purge_window the value differs from 1; silently defaulting
            would mask the gap. ``=1`` matches the no-purge canonical
            formula; ``>1`` accommodates purge+embargo gaps per López
            de Prado 2018 AFML §7.

        Notes
        -----
        This method returns only the row-normalised posterior over
        states. The underlying ``forward_log_from_prior`` also produces
        a scalar log-likelihood that is *conditional on the prior's
        normalisation constant* (i.e., ``log P(o_test, o_train | θ) −
        log P(o_train | θ)`` only when the prior is a properly
        normalised filtered posterior). Because :meth:`terminal_log_alpha`
        returns an unnormalised train-fold terminal log α, that scalar
        must not be interpreted as stand-alone model evidence or used
        in BIC/AIC-style cross-run comparisons without re-normalising
        the prior. References: Hamilton, J. D. (1994). *Time Series
        Analysis*. Princeton University Press, ISBN 978-0-691-04289-3,
        §22.4 (filter-step normalisation constants);
        Frühwirth-Schnatter, S. (2006). *Finite Mixture and Markov
        Switching Models*. Springer, ISBN 978-0-387-32909-3, §11.4-11.5
        (predictive vs marginal likelihood decomposition).
        """
        self._require_fitted()
        assert self.params_ is not None
        x_arr = _coerce_obs(x, expect_dim=self.params_.dim())
        log_B = log_emission_matrix(
            x_arr,
            self.params_.means,
            self.params_.covars,
            self.params_.covariance_type,
        )
        log_alpha, _ = forward_log_from_prior(
            np.asarray(log_alpha_prior, dtype=np.float64),
            self.params_.log_transmat,
            log_B,
            n_propagation_steps=n_propagation_steps,
        )
        log_norm = logsumexp(log_alpha, axis=1, keepdims=True)
        return np.exp(log_alpha - log_norm)

    def log_likelihood(self, x: npt.ArrayLike) -> float:
        """Total ``log P(y_{1:T} | λ)`` under the fitted model.

        Uses the forward recursion on the supplied sequence. Useful
        for held-out scoring (e.g., walk-forward CV in Cycle 4).
        """
        self._require_fitted()
        assert self.params_ is not None
        x_arr = _coerce_obs(x, expect_dim=self.params_.dim())
        log_B = log_emission_matrix(
            x_arr,
            self.params_.means,
            self.params_.covars,
            self.params_.covariance_type,
        )
        _, ll = forward_log(self.params_.log_pi, self.params_.log_transmat, log_B)
        return float(ll)

    # ------------------------------------------------------------------
    # Full-sequence Viterbi — train-time diagnostic only
    # ------------------------------------------------------------------

    def viterbi_train_time(self, x: npt.ArrayLike) -> tuple[np.ndarray, float]:
        """Full-sequence MAP state path. **Not for deployment features.**

        Consumes the entire sequence ``y_{1:T}`` — use only for
        training-time diagnostics (permutation tests against fitted
        state structure, dwell-time fits, regime-separation
        visualisations). Returns ``(path, log_prob)``.
        """
        self._require_fitted()
        assert self.params_ is not None
        x_arr = _coerce_obs(x, expect_dim=self.params_.dim())
        log_B = log_emission_matrix(
            x_arr,
            self.params_.means,
            self.params_.covars,
            self.params_.covariance_type,
        )
        return viterbi_log(self.params_.log_pi, self.params_.log_transmat, log_B)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _require_fitted(self) -> None:
        if self.params_ is None:
            raise RuntimeError("GaussianHMM not fitted. Call .fit() before inference.")


# ---------------------------------------------------------------------------
# Initialisation and canonicalisation
# ---------------------------------------------------------------------------


def _initial_params(
    x: np.ndarray,
    *,
    n_states: int,
    covariance_type: CovarianceType,
    min_var: float,
    seed: int,
    strategy: Literal["kmeans++"],
) -> HMMParams:
    """Construct an :class:`HMMParams` warm start.

    k-means++ (Arthur & Vassilvitskii 2007) seed selection via
    sklearn; cluster centres become initial emission means. State
    covariances are empirical within-cluster (with the same floor
    that the M-step uses). Initial π and transition matrix are
    built from hard-labelled empirical frequencies plus a small
    Dirichlet smoothing to avoid zeros.
    """
    if strategy != "kmeans++":
        raise ValueError(f"Unsupported init_strategy {strategy!r}.")

    from sklearn.cluster import KMeans

    kmeans = KMeans(
        n_clusters=n_states,
        init="k-means++",
        n_init=1,
        random_state=seed,
    )
    labels = kmeans.fit_predict(x)
    means = kmeans.cluster_centers_

    # Empirical within-cluster covariances under the chosen
    # parameterisation. These feed EM as warm starts; EM will refine.
    dim = x.shape[1]
    if covariance_type == "spherical":
        covars = np.empty(n_states, dtype=np.float64)
        for i in range(n_states):
            mask = labels == i
            if mask.sum() < 2:
                covars[i] = 1.0
            else:
                diff = x[mask] - means[i]
                covars[i] = float(np.mean(np.einsum("td,td->t", diff, diff))) / dim
        covars = np.maximum(covars, min_var)
    elif covariance_type == "diag":
        covars = np.empty((n_states, dim), dtype=np.float64)
        for i in range(n_states):
            mask = labels == i
            if mask.sum() < 2:
                covars[i] = 1.0
            else:
                covars[i] = np.var(x[mask], axis=0)
        covars = np.maximum(covars, min_var)
    elif covariance_type == "tied":
        total_diff_sq = np.zeros((dim, dim), dtype=np.float64)
        total_count = 0
        for i in range(n_states):
            mask = labels == i
            if mask.sum() < 2:
                continue
            d = x[mask] - means[i]
            total_diff_sq += d.T @ d
            total_count += int(mask.sum())
        if total_count == 0:
            covars = np.eye(dim)
        else:
            covars = total_diff_sq / total_count + min_var * np.eye(dim)
    elif covariance_type == "full":
        covars = np.empty((n_states, dim, dim), dtype=np.float64)
        for i in range(n_states):
            mask = labels == i
            if mask.sum() < 2:
                covars[i] = np.eye(dim)
            else:
                d = x[mask] - means[i]
                covars[i] = d.T @ d / int(mask.sum()) + min_var * np.eye(dim)
    else:
        raise ValueError(f"Unknown covariance_type {covariance_type!r}.")

    # Initial π from state frequencies with Dirichlet(1) smoothing so
    # no state starts at log(0).
    counts = np.bincount(labels, minlength=n_states).astype(np.float64) + 1.0
    pi = counts / counts.sum()

    # Initial transmat from empirical transitions of hard labels, with
    # row-wise Dirichlet(1) smoothing.
    transmat = np.ones((n_states, n_states), dtype=np.float64)
    for t in range(1, len(labels)):
        transmat[labels[t - 1], labels[t]] += 1
    transmat = transmat / transmat.sum(axis=1, keepdims=True)

    return HMMParams(
        log_pi=np.log(pi),
        log_transmat=np.log(transmat),
        means=means,
        covars=covars,
        covariance_type=covariance_type,
    )


def _canonicalise(params: HMMParams, order: CanonicalOrder) -> HMMParams:
    """Relabel states to break the label-switching symmetry.

    Ordering is done on the first emission dimension's mean
    (``means[:, 0]``). For multivariate emissions where a different
    canonicalisation is preferred (e.g., variance ordering for vol
    regimes), callers should override this post-fit in line with the
    pre-registered hypothesis rule — ADR-0005 §"Identifiability
    hazards and remediation".
    """
    if order == "mean_ascending":
        key = params.means[:, 0]
        perm = np.argsort(key)
    elif order == "mean_descending":
        key = params.means[:, 0]
        perm = np.argsort(-key)
    else:
        raise ValueError(f"Unknown canonical_order {order!r}.")

    inv = np.argsort(perm)  # not currently used, but useful for diagnostics
    del inv

    new_log_pi = params.log_pi[perm]
    new_log_transmat = params.log_transmat[perm][:, perm]
    new_means = params.means[perm]
    if params.covariance_type == "spherical":
        new_covars = params.covars[perm]
    elif params.covariance_type == "diag":
        new_covars = params.covars[perm]
    elif params.covariance_type == "tied":
        new_covars = params.covars  # shared; permutation is a no-op
    elif params.covariance_type == "full":
        new_covars = params.covars[perm]
    else:
        raise ValueError(f"Unknown covariance_type {params.covariance_type!r}.")

    return replace(
        params,
        log_pi=new_log_pi,
        log_transmat=new_log_transmat,
        means=new_means,
        covars=new_covars,
    )


def _coerce_obs(x: npt.ArrayLike, *, expect_dim: int) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError(f"observations must be 1-D or 2-D (T,d); got shape {arr.shape!r}.")
    if arr.shape[1] != expect_dim:
        raise ValueError(f"observation dim {arr.shape[1]} != fitted dim {expect_dim}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("observations contain NaN or inf.")
    return arr
