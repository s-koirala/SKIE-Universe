"""Disk-persistent HMM-fit cache (P1-HMM-FIT-CACHE-PERSIST).

Per [ADR-0010 Layer 3](../../../docs/decisions/ADR-0010-multi-hour-run-process-protection.md)
+ the H050 prod-run-3 timing data (2026-04-27: a single HMM cold-fit at
T=3M / min_restarts=5 took 11.2 hours), the in-memory HMM-fit cache in
[scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py)
loses all expensive computation if the orchestrator process dies for
any reason (BSOD, hardware power loss, user kill, supervisor max-runtime
cap). This module persists each cold-fit result to disk atomically as
soon as it completes, so a relaunch can repopulate the cache and skip
the recomputation.

Storage layout::

    artifacts/runs/H050/<run_id>/_hmm_cache/
        <sym>__fold_<fold_id>__lh_<label_horizon>.pkl

Each pickle file carries a ``schema_version`` tag (encoding the pickle
protocol version) plus environment-provenance fields (git HEAD,
producing run_id, Python version, numpy version) so a resumed run can
detect cross-version drift and surface a WARNING.

Resume mechanics:

  - During a fresh run (no ``--resume-hmm-cache`` flag): the orchestrator
    writes one pickle per cold-fit completion under the new run_id's
    cache dir. No reads.
  - During a resumed run (``--resume-hmm-cache <prior_run_id>``): at
    symbol-start, the orchestrator scans the prior run_id's cache dir
    for ``<sym>__*.pkl`` artifacts, deserialises each, and pre-populates
    the in-memory cache dict. Subsequent cache-misses continue to write
    new pickles under the **new** run_id (each run_id stays
    self-contained for audit; resumed compute is shared across runs).

Round-1 audit-remediate fixes (2026-04-28):

- **F-1-1 / R-1**: persist ``git_head``, ``producing_run_id``,
  ``python_version``, ``numpy_version``, ``pickle_protocol`` so a
  cross-HEAD or cross-env relaunch is detectable. WARN-but-load on
  mismatch (a fit produced under different code/numpy is
  mathematically valid; correctness depends on whether the operator
  accepts the version-drift risk).
- **F-1-4**: every numpy array in the payload is materialised through
  ``np.ascontiguousarray`` before pickling so two runs that produce
  identical fits also produce byte-identical pickles. Defends the
  `--no-hmm-cache` byte-identical-output regression contract.
- **F-1-7**: pickle protocol pinned to 5 (max for Python 3.8+; project
  requires-python = ">=3.11,<3.13"). HIGHEST_PROTOCOL would silently
  drift on a Python 3.13 upgrade.
"""

from __future__ import annotations

import os
import pickle
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from skie_ninja.models.regime.hmm import GaussianHMM


# Pickle protocol pinned to 5. Supported by Python >= 3.8; this project's
# requires-python band is ">=3.11,<3.13" so 5 is the max that all
# permitted Python versions can read AND write. Encoded in
# SCHEMA_VERSION so a future bump is unambiguous.
_PICKLE_PROTOCOL = 5

SCHEMA_VERSION = "hmm_fit_cache_v2_pickle5"


def _capture_git_head() -> str:
    """Best-effort `git rev-parse HEAD`. Returns ``"unknown"`` on any
    failure so the cache write does not fail just because we can't
    introspect the env."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
    except Exception:
        return "unknown"


def fit_cache_dir(run_dir: Path) -> Path:
    """Directory where a single run_id's HMM-fit pickles live."""
    return run_dir / "_hmm_cache"


def fit_cache_path(
    run_dir: Path, sym: str, fold_id: int, label_horizon: int
) -> Path:
    """Canonical pickle path for a single (sym, fold_id, label_horizon)
    cache entry. Symbols are uppercased to defend against case drift;
    fold_id and label_horizon are zero-padded so directory listings sort
    in numeric order."""
    fname = f"{sym.upper()}__fold_{fold_id:03d}__lh_{label_horizon:04d}.pkl"
    return fit_cache_dir(run_dir) / fname


def _ensure_contiguous_params(hmm: GaussianHMM) -> Any:
    """F-1-4: rebuild HMMParams with every numpy array passed through
    ``np.ascontiguousarray`` so the pickle bytes are determined by
    array dtype + shape + values only, not memory layout. Two runs
    that produce identical fits produce byte-identical pickles."""
    if hmm.params_ is None:
        raise ValueError("Cannot serialise un-fitted HMM (params_ is None).")
    # Local import to avoid module-load-time circular: HMMParams lives in
    # the regime _core module which hmm.py imports from.
    from skie_ninja.models.regime._core import HMMParams

    return HMMParams(
        log_pi=np.ascontiguousarray(hmm.params_.log_pi),
        log_transmat=np.ascontiguousarray(hmm.params_.log_transmat),
        means=np.ascontiguousarray(hmm.params_.means),
        covars=np.ascontiguousarray(hmm.params_.covars),
        covariance_type=hmm.params_.covariance_type,
    )


def save_fit(
    *,
    run_dir: Path,
    sym: str,
    fold_id: int,
    label_horizon: int,
    hmm: GaussianHMM,
    regime_high_mean: int,
    hmm_terminal_log_alpha: np.ndarray,
    hmm_train_terminal_position: int,
    train_idx_len: int,
    train_idx_first: int,
    train_idx_last: int,
    producing_run_id: str | None = None,
    git_head: str | None = None,
) -> Path:
    """Atomic pickle write of an HMM fit + bookkeeping fields.

    The write is atomic via tmp-file + fsync + rename: a mid-write kill
    leaves no partial artifact. Returns the absolute path to the
    persisted pickle.

    Pickle protocol is pinned to 5 (binary, stable across Python
    3.11/3.12). Numpy arrays are forced contiguous to ensure
    byte-deterministic pickle output.
    """
    if hmm.params_ is None:
        raise ValueError(
            "Cannot save un-fitted HMM (params_ is None). "
            "Call select_gaussian_hmm/fit before save_fit."
        )

    cache_dir = fit_cache_dir(run_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = fit_cache_path(run_dir, sym, fold_id, label_horizon)

    contiguous_params = _ensure_contiguous_params(hmm)
    payload: dict[str, Any] = {
        # ---- schema + env coupling (F-1-1 / R-1) ----
        "schema_version": SCHEMA_VERSION,
        "pickle_protocol": _PICKLE_PROTOCOL,
        "git_head": git_head if git_head is not None else _capture_git_head(),
        "producing_run_id": producing_run_id,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        # ---- cache key ----
        "sym": str(sym).upper(),
        "fold_id": int(fold_id),
        "label_horizon": int(label_horizon),
        # ---- HMM model class hyperparams (for reconstruct) ----
        "hmm_n_states": int(hmm.n_states),
        "hmm_covariance_type": str(hmm.covariance_type),
        "hmm_em_tol": float(hmm.em_tol),
        "hmm_max_iter": int(hmm.max_iter),
        "hmm_min_var": float(hmm.min_var),
        "hmm_canonical_order": str(hmm.canonical_order),
        # ---- HMM fitted state ----
        "hmm_params": contiguous_params,
        "hmm_fit_result": hmm.fit_result_,  # FitResult dataclass; pickle-safe
        # ---- bookkeeping for orchestrator's _CachedHmmFit ----
        "regime_high_mean": int(regime_high_mean),
        "hmm_terminal_log_alpha": np.ascontiguousarray(hmm_terminal_log_alpha),
        "hmm_train_terminal_position": int(hmm_train_terminal_position),
        "train_idx_len": int(train_idx_len),
        "train_idx_first": int(train_idx_first),
        "train_idx_last": int(train_idx_last),
    }
    # F-1-4 atomic-write semantic: full filename + ".tmp" suffix (not
    # path.with_suffix which would replace the ".pkl" suffix).
    tmp = path.parent / (path.name + ".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(payload, f, protocol=_PICKLE_PROTOCOL)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)
    return path


def load_fit(path: Path) -> dict[str, Any]:
    """Load a persisted fit pickle and validate its schema version.

    Raises ``ValueError`` if the schema version does not match
    :data:`SCHEMA_VERSION` — a future schema change must reject stale
    artifacts rather than silently mis-reconstruct state.
    """
    with open(path, "rb") as f:
        payload = pickle.load(f)
    got = payload.get("schema_version")
    if got != SCHEMA_VERSION:
        raise ValueError(
            f"Cached fit schema-version mismatch at {path}: "
            f"got {got!r}, expected {SCHEMA_VERSION!r}. "
            f"Stale artifacts must not be silently loaded; delete the "
            f"cache directory or re-run from scratch."
        )
    return payload


def check_provenance(
    payload: dict[str, Any],
    *,
    current_git_head: str | None = None,
) -> list[str]:
    """Compare the payload's env-provenance fields against the current
    environment. Returns a list of human-readable mismatch strings (empty
    list = no drift). Caller decides whether to abort or WARN+continue;
    the canonical orchestrator path is to log a WARNING per mismatch
    and continue, since a fit produced under different code/numpy is
    still mathematically valid — the caller's responsibility is to
    surface the drift for audit."""
    mismatches: list[str] = []
    cur_git = current_git_head if current_git_head is not None else _capture_git_head()
    payload_git = payload.get("git_head", "unknown")
    if cur_git != payload_git and "unknown" not in (cur_git, payload_git):
        mismatches.append(
            f"git_head mismatch: producing={payload_git!r}, current={cur_git!r}"
        )
    cur_py = platform.python_version()
    payload_py = payload.get("python_version", "")
    if cur_py != payload_py:
        mismatches.append(
            f"python_version mismatch: producing={payload_py!r}, current={cur_py!r}"
        )
    cur_np = np.__version__
    payload_np = payload.get("numpy_version", "")
    if cur_np != payload_np:
        mismatches.append(
            f"numpy_version mismatch: producing={payload_np!r}, current={cur_np!r}"
        )
    return mismatches


def reconstruct_hmm(payload: dict[str, Any]) -> GaussianHMM:
    """Rebuild a fitted ``GaussianHMM`` from a loaded cache payload.

    The instance's ``params_`` and ``fit_result_`` are restored from the
    pickle so downstream consumers (``filter_states``, ``predict``,
    ``log_emission_matrix``-based scoring) see byte-identical state vs
    the original fit at fit time.
    """
    hmm = GaussianHMM(
        n_states=payload["hmm_n_states"],
        covariance_type=payload["hmm_covariance_type"],
        em_tol=payload["hmm_em_tol"],
        max_iter=payload["hmm_max_iter"],
        min_var=payload["hmm_min_var"],
        canonical_order=payload["hmm_canonical_order"],
    )
    hmm.params_ = payload["hmm_params"]
    if payload.get("hmm_fit_result") is not None:
        hmm.fit_result_ = payload["hmm_fit_result"]
    return hmm


@dataclass(frozen=True)
class CachedFitRecord:
    """Plain bag of fields the orchestrator wraps into its local
    ``_CachedHmmFit`` dataclass after :func:`load_and_reconstruct`.

    The contained ``hmm`` and ``hmm_terminal_log_alpha`` are intentionally
    NOT deep-copied; consumers must treat them as read-only. The
    dataclass is ``frozen=True`` to prevent reassignment of the field
    NAMES, but the underlying objects remain mutable in place — see
    R-5 Round-1 disposition.
    """

    sym: str
    fold_id: int
    label_horizon: int
    hmm: GaussianHMM
    regime_high_mean: int
    hmm_terminal_log_alpha: np.ndarray
    hmm_train_terminal_position: int
    train_idx_len: int
    train_idx_first: int
    train_idx_last: int
    # Provenance (read-only, for downstream audit):
    producing_run_id: str | None
    producing_git_head: str | None


def load_and_reconstruct(path: Path) -> CachedFitRecord:
    """Convenience: ``load_fit`` + ``reconstruct_hmm`` into a single
    ``CachedFitRecord``. The orchestrator wraps this into its local
    ``_CachedHmmFit`` dataclass at the call site."""
    payload = load_fit(path)
    hmm = reconstruct_hmm(payload)
    return CachedFitRecord(
        sym=payload["sym"],
        fold_id=int(payload["fold_id"]),
        label_horizon=int(payload["label_horizon"]),
        hmm=hmm,
        regime_high_mean=int(payload["regime_high_mean"]),
        hmm_terminal_log_alpha=np.ascontiguousarray(
            payload["hmm_terminal_log_alpha"]
        ),
        hmm_train_terminal_position=int(payload["hmm_train_terminal_position"]),
        train_idx_len=int(payload["train_idx_len"]),
        train_idx_first=int(payload["train_idx_first"]),
        train_idx_last=int(payload["train_idx_last"]),
        producing_run_id=payload.get("producing_run_id"),
        producing_git_head=payload.get("git_head"),
    )


def discover_cached_fits(run_dir: Path, sym: str) -> list[Path]:
    """List all cached-fit pickles for one symbol under one run_id, in
    deterministic (sorted) order. The glob matches the canonical
    filename schema strictly (``<SYM>__fold_NNN__lh_NNNN.pkl``) so
    sibling files (e.g. future sidecar artifacts) do not over-match
    (Round-1 F-1-12).
    """
    cache_dir = fit_cache_dir(run_dir)
    if not cache_dir.exists():
        return []
    return sorted(
        cache_dir.glob(f"{sym.upper()}__fold_???__lh_????.pkl")
    )


__all__ = [
    "SCHEMA_VERSION",
    "CachedFitRecord",
    "check_provenance",
    "discover_cached_fits",
    "fit_cache_dir",
    "fit_cache_path",
    "load_and_reconstruct",
    "load_fit",
    "reconstruct_hmm",
    "save_fit",
]
