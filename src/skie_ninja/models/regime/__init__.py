"""Regime-inference models.

Public API:

  - :class:`GaussianHMM` — Gaussian HMM with causal forward-filter
    inference and train-time Viterbi diagnostic.
  - :func:`select_gaussian_hmm` — BIC-based grid search over
    ``(n_states, covariance_type)``.
  - :class:`HMMSidecar`, :func:`build_sidecar`, :func:`write_sidecar`,
    :func:`sidecar_path_for` — ADR-0005 reproducibility sidecar.

Anti-look-ahead invariant
-------------------------

The only state-inference method that may be called on live / deploy
observations is :meth:`GaussianHMM.filter_states`. The module also
exposes :meth:`GaussianHMM.viterbi_train_time` for training-time
diagnostics; downstream feature code must not call it.
"""

from skie_ninja.models.regime._core import (
    CovarianceType,
    HMMParams,
    bic,
    count_free_parameters,
)
from skie_ninja.models.regime.hmm import FitResult, GaussianHMM
from skie_ninja.models.regime.selection import (
    SelectionCandidate,
    SelectionResult,
    select_gaussian_hmm,
)
from skie_ninja.models.regime.serialization import (
    HMMSidecar,
    build_sidecar,
    sidecar_path_for,
    write_sidecar,
)

__all__ = [
    "CovarianceType",
    "FitResult",
    "GaussianHMM",
    "HMMParams",
    "HMMSidecar",
    "SelectionCandidate",
    "SelectionResult",
    "bic",
    "build_sidecar",
    "count_free_parameters",
    "select_gaussian_hmm",
    "sidecar_path_for",
    "write_sidecar",
]
