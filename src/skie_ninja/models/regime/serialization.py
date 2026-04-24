"""Sidecar JSON writer + ``ReproLog.model_hash`` integration.

ADR-0005 §"Integration with existing infrastructure" specifies:

    HMM-specific metadata is written to a sidecar file
    ``logs/reproducibility/{run_id}_hmm_selection.json`` with fields
    {n_states, covariance_type, init_strategy, em_tol, max_iter,
    n_restarts, seed, transition_matrix_sha256, emission_means_sha256}.
    The SHA256 of the sidecar file is stored in ``ReproLog.model_hash``.

This module implements that contract. The ``ReproLog`` dataclass is
frozen per ADR-0005 — we do NOT extend its fields; we only populate
``model_hash`` via :func:`skie_ninja.utils.reproducibility.with_model_hash`.

File write is atomic (same pattern as :meth:`ReproLog.write`) so
readers never observe a partial file.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skie_ninja.models.regime.hmm import FitResult, GaussianHMM
from skie_ninja.utils.hashing import file_sha256, model_sha256


@dataclass(frozen=True)
class HMMSidecar:
    """On-disk representation of an HMM selection / fit.

    Fields per ADR-0005 §"Integration with existing infrastructure".
    Covariance-type-specific fields (emission dimensions, covariance
    parameters) are included for reconstructability; they are not
    part of the ADR's required-field list but are needed for the
    CI ``repro-verify`` stage to reload the model and re-score a
    held-out fold.
    """

    n_states: int
    covariance_type: str
    init_strategy: str
    em_tol: float
    max_iter: int
    n_restarts: int
    seed: int
    transition_matrix_sha256: str
    emission_means_sha256: str
    # Bookkeeping fields (not load-bearing for ADR-0005 field list).
    dim: int
    covariance_floor: float
    best_log_likelihood: float
    converged_restarts: int
    schema_version: str = "hmm_sidecar_v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "n_states": self.n_states,
            "covariance_type": self.covariance_type,
            "init_strategy": self.init_strategy,
            "em_tol": self.em_tol,
            "max_iter": self.max_iter,
            "n_restarts": self.n_restarts,
            "seed": self.seed,
            "transition_matrix_sha256": self.transition_matrix_sha256,
            "emission_means_sha256": self.emission_means_sha256,
            "dim": self.dim,
            "covariance_floor": self.covariance_floor,
            "best_log_likelihood": self.best_log_likelihood,
            "converged_restarts": self.converged_restarts,
        }


def build_sidecar(model: GaussianHMM) -> HMMSidecar:
    """Build an :class:`HMMSidecar` from a fitted :class:`GaussianHMM`.

    Hashes of the transition matrix and emission means are computed
    via :func:`skie_ninja.utils.hashing.model_sha256` so they are
    stable across processes (set/dict iteration order is not a
    factor — both are numpy arrays).
    """
    if model.params_ is None or model.fit_result_ is None:
        raise RuntimeError("Cannot serialise an unfitted GaussianHMM.")
    # Hash the transition matrix (exponentiated to probability space
    # so a zero-log edge case does not confuse the hash consumer) and
    # the emission means as a canonical numpy array.
    fr: FitResult = model.fit_result_
    transmat = _to_probs(model.params_.log_transmat)
    return HMMSidecar(
        n_states=model.params_.n_states(),
        covariance_type=model.params_.covariance_type,
        init_strategy=fr.init_strategy,
        em_tol=fr.em_tol,
        max_iter=fr.max_iter,
        n_restarts=fr.n_restarts_used,
        seed=fr.seed,
        transition_matrix_sha256=model_sha256(transmat),
        emission_means_sha256=model_sha256(model.params_.means),
        dim=model.params_.dim(),
        covariance_floor=fr.covariance_floor,
        best_log_likelihood=fr.best_log_likelihood,
        converged_restarts=int(fr.per_restart_converged.sum()),
    )


def write_sidecar(sidecar: HMMSidecar, path: Path) -> tuple[Path, str]:
    """Atomically write the sidecar JSON and return ``(path, sha256)``.

    Same atomicity pattern as :meth:`ReproLog.write` — tempfile in
    target directory, ``fsync``, ``os.replace``. Readers never see a
    partial file.

    Returns
    -------
    (path, sha256)
        The resolved path on disk and the sha256 of the canonical
        serialization. The caller passes ``sha256`` into
        :func:`skie_ninja.utils.reproducibility.with_model_hash`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(
        sidecar.to_dict(), sort_keys=True, indent=2, ensure_ascii=False
    ).encode("utf-8")

    tmp = tempfile.NamedTemporaryFile(
        mode="wb",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
    finally:
        tmp.close()
    os.replace(tmp.name, path)
    return path, file_sha256(path)


def sidecar_path_for(
    run_id: str, *, logs_reproducibility_dir: Path
) -> Path:
    """Canonical sidecar location per ADR-0005.

    ``logs/reproducibility/{run_id}_hmm_selection.json``
    """
    return Path(logs_reproducibility_dir) / f"{run_id}_hmm_selection.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _to_probs(log_mat: Any) -> Any:
    import numpy as np
    return np.exp(log_mat)
