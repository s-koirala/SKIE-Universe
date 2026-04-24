"""Model selection across ``(n_states, covariance_type)`` grids.

Cycle 3 scope: BIC (Schwarz 1978) on the training fold. The joint
BIC + walk-forward cross-validated log-likelihood rule mandated by
ADR-0005 requires the walk-forward engine (Cycle 4 deliverable) and
is tracked as ``P1-HMM-WFCV``. Until Cycle 4 lands, the selector
falls back to BIC-only — ADR-0005 explicitly calls BIC the primary
criterion with CV as a secondary tiebreaker.

References
----------

  - Schwarz, G. 1978. "Estimating the Dimension of a Model". *Annals
    of Statistics* 6(2): 461-464. https://doi.org/10.1214/aos/1176344136
  - Celeux, G. & Durand, J.-B. 2008. "Selecting hidden Markov model
    state number with cross-validated likelihood". *Computational
    Statistics* 23(4): 541-564. https://doi.org/10.1007/s00180-007-0097-1
  - Pohle, J., Langrock, R., van Beest, F. M., & Schmidt, N. M.
    2017. "Selecting the Number of States in Hidden Markov Models:
    Pragmatic Solutions Illustrated Using Animal Movement". *Journal
    of Agricultural, Biological and Environmental Statistics* 22(3):
    270-293. https://doi.org/10.1007/s13253-017-0283-8

Follow-ups (deferred, see audit trail)
--------------------------------------

  - ``P1-HMM-WFCV``: walk-forward-CV held-out log-likelihood scoring
    and BIC+CV joint selection (ADR-0005).
  - ``P1-HMM-ADAPTIVE-RESTART``: bootstrap-ε stopping rule.
  - ``P1-HMM-PERM-TEST``: permutation-based BIC-differential
    significance test.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from skie_ninja.models.regime._core import CovarianceType, bic
from skie_ninja.models.regime.hmm import GaussianHMM


@dataclass(frozen=True)
class SelectionCandidate:
    """Single grid-point fit record."""

    n_states: int
    covariance_type: CovarianceType
    log_likelihood: float
    bic: float
    n_restarts_used: int


@dataclass(frozen=True)
class SelectionResult:
    """Output of :func:`select_gaussian_hmm`.

    ``best_model`` is a fitted :class:`GaussianHMM` with the
    BIC-minimising ``(n_states, covariance_type)``.
    """

    best_model: GaussianHMM
    best_n_states: int
    best_covariance_type: CovarianceType
    candidates: tuple[SelectionCandidate, ...]
    criterion: str  # "bic" (Cycle 3) or "bic+wfcv" (after Cycle 4)


def select_gaussian_hmm(
    x: npt.NDArray[np.float64],
    *,
    n_states_grid: tuple[int, ...],
    covariance_types: tuple[CovarianceType, ...] = ("diag",),
    seed: int,
    em_tol: float | None = None,
    max_iter: int | None = None,
    min_var: float | None = None,
    min_restarts: int = 5,
    max_restarts: int = 20,
) -> SelectionResult:
    """Fit a grid of Gaussian HMMs and return the BIC-minimiser.

    Parameters
    ----------
    x
        (T, d) observations. Selection is performed on this single
        training fold — no walk-forward CV in Cycle 3 (see module
        docstring).
    n_states_grid
        Explicit grid of ``N`` values. ADR-0005 requires each entry
        bounded below by 2 and bounded above by the largest K such
        that ``mean within-state sample size > 30 · d``; the caller
        is responsible for that bound (the hypothesis pre-registration
        is where it should be recorded).
    covariance_types
        Tuple over ``{"spherical", "diag", "tied", "full"}``. Defaults
        to ``("diag",)`` — the single most-common choice for
        financial-return emissions. Broader grids cost more compute;
        callers should pre-register the grid.
    seed
        Master RNG seed. Per-grid-point RNG seeds are derived
        deterministically via ``SeedSequence.spawn`` so fit
        reproducibility is independent of grid iteration order.

    Returns
    -------
    :class:`SelectionResult`
        Carries the BIC-minimising fitted model plus the full grid
        of candidate scores for audit.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    if x_arr.ndim == 1:
        x_arr = x_arr.reshape(-1, 1)

    for n in n_states_grid:
        if n < 2:
            raise ValueError(
                f"n_states grid entries must be >= 2 (ADR-0005); got {n}."
            )

    ss = np.random.SeedSequence(int(seed))
    # SeedSequence.spawn gives independent substreams for each grid
    # point; the order-independence matters so re-ordering the grid
    # inputs in a pre-registration change does not change the fits.
    n_points = len(n_states_grid) * len(covariance_types)
    sub_seeds = ss.spawn(n_points)

    candidates: list[SelectionCandidate] = []
    best_model: GaussianHMM | None = None
    best_bic = np.inf
    best_n: int = -1
    best_cov: CovarianceType = covariance_types[0]

    idx = 0
    for n in n_states_grid:
        for cov in covariance_types:
            seed_i = int(sub_seeds[idx].generate_state(1)[0])
            idx += 1
            model = GaussianHMM(
                n_states=n,
                covariance_type=cov,
                em_tol=em_tol if em_tol is not None else GaussianHMM.em_tol,
                max_iter=max_iter if max_iter is not None else GaussianHMM.max_iter,
                min_var=min_var if min_var is not None else GaussianHMM.min_var,
            )
            model.fit(
                x_arr,
                seed=seed_i,
                min_restarts=min_restarts,
                max_restarts=max_restarts,
            )
            assert model.fit_result_ is not None
            ll = model.fit_result_.best_log_likelihood
            bic_score = bic(
                log_likelihood=ll,
                n_states=n,
                dim=x_arr.shape[1],
                covariance_type=cov,
                t_len=x_arr.shape[0],
            )
            candidates.append(
                SelectionCandidate(
                    n_states=n,
                    covariance_type=cov,
                    log_likelihood=ll,
                    bic=bic_score,
                    n_restarts_used=model.fit_result_.n_restarts_used,
                )
            )
            if bic_score < best_bic:
                best_bic = bic_score
                best_model = model
                best_n = n
                best_cov = cov

    assert best_model is not None
    return SelectionResult(
        best_model=best_model,
        best_n_states=best_n,
        best_covariance_type=best_cov,
        candidates=tuple(candidates),
        criterion="bic",
    )
