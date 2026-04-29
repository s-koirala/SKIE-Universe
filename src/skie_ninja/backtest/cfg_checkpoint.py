"""Per-cfg checkpoint cache for the H050 walk-forward orchestrator.

Each label-cfg's candidate ``dict`` (produced by
``scripts/run_walk_forward.py:_run_symbol_label_cfg``) is pickled to
``<run_dir>/_cfg_checkpoints/<sym>__cfg_<idx>__pt_<pt_sl>__vb_<secs>__vl_<vl>.pkl``
immediately after the cfg completes. On resume the cached candidate
is reloaded directly, skipping re-execution of the inner-CV-LGB +
fold-fit + label-panel work entirely.

Motivation
----------

prod-run-4 and prod-run-5 each crashed with ``MemoryError`` near the
2-hour mark — Windows CRT heap address-space fragmentation after
many cfgs of polars→numpy conversions, LightGBM Booster lifecycles,
and HMM cache pickle loads. Per
[docs/audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md](../../../docs/audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md)
the explicit ``del`` + per-draw ``gc.collect()`` in
``_inner_cv_select_hp`` extended the crash threshold from cfg 20 to
cfg 24 but did not fully resolve it. This module bounds work loss
on a fragmentation-driven crash to **at most one cfg** instead of
the full run.

Schema and provenance
---------------------

Pickle protocol pinned to 5 (matches ``hmm_fit_cache.py``). Payload
records ``schema_version`` + ``git_head`` + ``producing_run_id`` +
``python_version`` + ``numpy_version`` + ``cfg_key_signature``. The
``check_provenance`` function returns mismatch entries; the caller
uses WARN-but-load semantics consistent with the HMM cache.

Cross-run resume
----------------

The orchestrator's ``--resume-cfg-checkpoint <prior_run_id>`` flag
points the loader at a prior run's ``_cfg_checkpoints`` directory.
The loader reads each pickle, validates schema + cfg-key, and
returns a ``dict[cfg_key, candidate]`` that the cfg loop consults
before invoking ``_run_symbol_label_cfg``. A cache hit short-circuits
the call.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


_PICKLE_PROTOCOL = 5
SCHEMA_VERSION = "cfg_checkpoint_v1_pickle5"


def _capture_git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
    except Exception:
        return "unknown"


def cfg_checkpoint_dir(run_dir: Path) -> Path:
    """Directory where a single run_id's per-cfg pickles live."""
    return run_dir / "_cfg_checkpoints"


@dataclass(frozen=True)
class CfgKey:
    """Canonical cfg identity used as the cache lookup key.

    The orchestrator iterates over a deterministic cartesian product
    ``label_grid = [(pt_sl, vertical_barrier, volatility_lookback), ...]``
    per symbol (see [research/01_hypothesis_register/H050/design.md](../../../research/01_hypothesis_register/H050/design.md)
    §4 "Triple-barrier 27-cell CV"). The cfg key tuple covers every
    dimension that varies between cfgs.
    """

    sym: str
    cfg_idx: int  # 1-based per the orchestrator's enumerate()
    pt_sl: float
    vertical_barrier_seconds: int
    volatility_lookback: int

    def filename_stem(self) -> str:
        # 4-digit cfg padding so listdir sorts numerically.
        return (
            f"{self.sym.upper()}__cfg_{self.cfg_idx:04d}"
            f"__pt_{self.pt_sl:.2f}"
            f"__vb_{self.vertical_barrier_seconds:06d}"
            f"__vl_{self.volatility_lookback:04d}"
        )

    def signature(self) -> str:
        """SHA256 of the canonical key tuple. Used in payload to detect
        filename-vs-payload drift (e.g. a hand-edited filename)."""
        canonical = (
            f"{self.sym.upper()}|{self.cfg_idx}|{self.pt_sl:.10f}|"
            f"{self.vertical_barrier_seconds}|{self.volatility_lookback}"
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def cfg_checkpoint_path(run_dir: Path, key: CfgKey) -> Path:
    """Canonical pickle path for a single cfg checkpoint."""
    return cfg_checkpoint_dir(run_dir) / f"{key.filename_stem()}.pkl"


def save_checkpoint(
    *,
    run_dir: Path,
    key: CfgKey,
    candidate: dict[str, Any],
    producing_run_id: str | None = None,
    git_head: str | None = None,
) -> Path:
    """Atomic pickle write of one cfg's candidate result.

    Atomic via tmp + fsync + rename. Returns the absolute path.
    Best-effort: callers should swallow OSError so a checkpoint write
    failure never aborts the run (the cfg's result is still in memory
    and will reach the parent's candidate_runs list).
    """
    cdir = cfg_checkpoint_dir(run_dir)
    cdir.mkdir(parents=True, exist_ok=True)
    path = cfg_checkpoint_path(run_dir, key)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "pickle_protocol": _PICKLE_PROTOCOL,
        "git_head": git_head if git_head is not None else _capture_git_head(),
        "producing_run_id": producing_run_id,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "cfg_key": dataclass_to_dict(key),
        "cfg_key_signature": key.signature(),
        "candidate": candidate,
    }
    tmp = path.parent / (path.name + ".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(payload, f, protocol=_PICKLE_PROTOCOL)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)
    return path


def dataclass_to_dict(key: CfgKey) -> dict[str, Any]:
    """Stable dict form of a CfgKey for the pickle payload (avoids
    dataclass-class-identity coupling on load)."""
    return {
        "sym": key.sym,
        "cfg_idx": key.cfg_idx,
        "pt_sl": float(key.pt_sl),
        "vertical_barrier_seconds": int(key.vertical_barrier_seconds),
        "volatility_lookback": int(key.volatility_lookback),
    }


def load_checkpoint(path: Path) -> dict[str, Any]:
    """Load a checkpoint pickle and validate its schema version.

    Raises ``ValueError`` on schema mismatch; raises
    ``FileNotFoundError`` if path does not exist.
    """
    with open(path, "rb") as f:
        payload = pickle.load(f)
    got = payload.get("schema_version")
    if got != SCHEMA_VERSION:
        raise ValueError(
            f"Cfg checkpoint schema-version mismatch at {path}: "
            f"got {got!r}, expected {SCHEMA_VERSION!r}."
        )
    return payload


def discover_checkpoints(
    run_dir: Path,
) -> dict[tuple[str, int, float, int, int], dict[str, Any]]:
    """Enumerate all checkpoints in a run directory's checkpoint dir.

    Returns a mapping ``cfg_key_tuple → payload``. Used by the
    orchestrator's resume path to short-circuit ``_run_symbol_label_cfg``
    calls when a checkpoint exists for the cfg.
    """
    cdir = cfg_checkpoint_dir(run_dir)
    if not cdir.exists():
        return {}
    out: dict[tuple[str, int, float, int, int], dict[str, Any]] = {}
    for p in sorted(cdir.glob("*.pkl")):
        try:
            payload = load_checkpoint(p)
        except (OSError, pickle.PickleError, ValueError, EOFError):
            # EOFError from truncated pickle (e.g. crash mid-write
            # before fsync); pickle.PickleError covers UnpicklingError;
            # ValueError covers schema-version mismatch.
            continue
        ck = payload.get("cfg_key", {})
        try:
            key_tuple = (
                str(ck["sym"]).upper(),
                int(ck["cfg_idx"]),
                float(ck["pt_sl"]),
                int(ck["vertical_barrier_seconds"]),
                int(ck["volatility_lookback"]),
            )
        except (KeyError, ValueError, TypeError):
            continue
        out[key_tuple] = payload
    return out


def check_provenance(
    payload: dict[str, Any],
    *,
    current_git_head: str | None = None,
) -> list[str]:
    """Compare payload's env-provenance fields to the current
    environment. Returns mismatch strings (empty = no drift).
    Caller uses WARN-but-load semantics consistent with hmm_fit_cache."""
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


__all__ = [
    "SCHEMA_VERSION",
    "CfgKey",
    "cfg_checkpoint_dir",
    "cfg_checkpoint_path",
    "save_checkpoint",
    "load_checkpoint",
    "discover_checkpoints",
    "check_provenance",
]
