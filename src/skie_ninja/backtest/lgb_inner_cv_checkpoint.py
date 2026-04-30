"""Per-draw checkpoint cache for the H050 walk-forward inner-CV-LGB loop.

Each (cfg, draw) inner-CV-LGB result is pickled to
``<run_dir>/_lgb_inner_cv_checkpoints/<cfg_signature>/draw_<NNNN>.pkl``
immediately after the draw completes. On resume the cached draws are
reloaded directly, skipping re-execution of the LightGBM fit + predict
+ scoring per inner fold. The architectural goal is to bound work loss
on any external kill (OS reboot, BSOD, hardware) to **at most one draw**
of inner-CV-LGB rather than the full cfg's worth.

Motivation
----------

Per [docs/audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](../../../docs/audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md)
F-1 + F-3, the 2026-04-29 H050 prod-run-6 attempt-2 was killed by an
OS-initiated reboot at +49 min while inside cfg 12 fold 0 inner-CV-LGB
(NQ, ``train_size=2978358``, ``n_draws=200``, ``n_inner_folds=3``).
The cfg-checkpoint pattern (``cfg_checkpoint.py``, schema v1) bounds
work loss to one cfg, but a 6-hour cfg with 200 LGB draws × 3 inner
folds × ~2 sec/fit ≈ 20 minutes of in-flight work is lost on each
external kill. With the relaunch loop's per-attempt cap raised to
6 hr but no within-cfg checkpoint, the cumulative cost across multiple
external kills is unbounded.

This module mirrors ``cfg_checkpoint.py``'s schema + atomic-write +
provenance-drift + WARN-but-load contract per ADR-0011 §"Provenance
drift handling".

Schema and provenance
---------------------

Pickle protocol pinned to 5 (matches ``hmm_fit_cache.py`` + ``cfg_checkpoint.py``).
Payload records ``schema_version`` + ``git_head`` + ``producing_run_id``
+ ``python_version`` + ``numpy_version`` + ``cfg_signature`` +
``draw_idx`` + ``params`` (the LGB hyperparameters draw) + ``fold_loglosses``
+ ``fold_sharpes``. The ``check_provenance`` function returns mismatch
entries; the caller uses WARN-but-load semantics.

Cross-run resume
----------------

The orchestrator's ``--resume-cfg-checkpoint <prior_run_id>`` flag
already points the cfg-checkpoint loader at a prior run's checkpoint
directory; this module piggybacks on the same prior-run-id and
discovers per-draw checkpoints under the matching cfg subdirectory.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import platform
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


_PICKLE_PROTOCOL = 5
SCHEMA_VERSION = "lgb_inner_cv_checkpoint_v2_pickle5"
# v2 (2026-04-30): per-draw key extended to (cfg_signature, fold_id,
# draw_idx) per Round-1 audit R-1-1 critical finding; v1 collided
# across outer folds within one cfg and silently substituted prior-
# fold inner-CV outputs on resume. Filename now `fold_<NN>_draw_<NNNN>.pkl`.
_DRAW_FILENAME_RE = re.compile(r"^fold_(\d{2,4})_draw_(\d{4,6})\.pkl$")


def _capture_git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def lgb_inner_cv_checkpoint_root(run_dir: Path) -> Path:
    """Root directory under a run_id where per-cfg-per-draw pickles live."""
    return run_dir / "_lgb_inner_cv_checkpoints"


def lgb_inner_cv_cfg_dir(
    run_dir: Path, cfg_signature: str, lgb_seed: int | None = None
) -> Path:
    """Per-cfg subdirectory; one per (sym, cfg_idx, pt_sl, vb, vl[, lgb_seed]) tuple.

    The cfg_signature is the SHA256-hex of the canonical cfg key
    string (matches ``cfg_checkpoint.CfgKey.signature()``); 16 hex
    chars are used for the directory-name prefix.

    Round-1 audit Q-1-2 (cross-seed contamination): when ``lgb_seed`` is
    provided, the directory name is suffixed ``__seed_<seed>`` so two
    runs that differ only in lgb_seed do not share the same per-draw
    pickles (the cached params would belong to a different HP-draw
    stream). When ``lgb_seed`` is None (legacy callers), the directory
    is just the cfg-signature prefix.
    """
    base = cfg_signature[:16]
    if lgb_seed is not None:
        base = f"{base}__seed_{int(lgb_seed)}"
    return lgb_inner_cv_checkpoint_root(run_dir) / base


@dataclass(frozen=True)
class LgbDrawKey:
    """Identifier for one (cfg, fold_id, draw_idx) result.

    Round-1 audit R-1-1 (critical): fold_id is now part of the key
    because ``_inner_cv_select_hp`` is invoked once per outer fold and
    the per-draw payload is fold-specific. Without fold_id, successive
    folds within one cfg overwrote each other's pickles and resume
    silently substituted prior-fold data. Filename pattern is now
    ``fold_<NN>_draw_<NNNN>.pkl``.
    """

    cfg_signature: str  # full SHA256 hex from CfgKey.signature()
    fold_id: int  # 0-based outer-fold index from the walk-forward engine
    draw_idx: int  # 0-based per the orchestrator's enumerate(draws)

    def filename(self) -> str:
        # 2-digit fold padding (covers up to 99 outer folds; H050 expects
        # ~5-15) + 4-digit draw padding so listdir sorts (fold, draw).
        return f"fold_{self.fold_id:02d}_draw_{self.draw_idx:04d}.pkl"


def _payload(
    *,
    cfg_signature: str,
    fold_id: int,
    draw_idx: int,
    params: dict[str, Any],
    fold_loglosses: list[float],
    fold_sharpes: list[float],
    producing_run_id: str | None,
    lgb_seed: int | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "git_head": _capture_git_head(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pickle_protocol": _PICKLE_PROTOCOL,
        "producing_run_id": producing_run_id,
        "cfg_signature": cfg_signature,
        "fold_id": int(fold_id),
        "draw_idx": int(draw_idx),
        "lgb_seed": int(lgb_seed) if lgb_seed is not None else None,
        "params": dict(params),
        "fold_loglosses": [float(x) for x in fold_loglosses],
        "fold_sharpes": [float(x) for x in fold_sharpes],
    }


def save_draw_checkpoint(
    run_dir: Path,
    cfg_signature: str,
    fold_id: int,
    draw_idx: int,
    *,
    params: dict[str, Any],
    fold_loglosses: list[float],
    fold_sharpes: list[float],
    producing_run_id: str | None,
    lgb_seed: int | None = None,
) -> Path:
    """Atomic write of one (cfg, fold_id, draw_idx) record. Returns path.

    Atomic semantics match ``cfg_checkpoint.save_checkpoint``: write to
    temp + ``os.replace`` to final path. Parent directory auto-created.
    Raises only on programmer errors (pickling failure of a non-picklable
    object); ``OSError`` and ``PermissionError`` are NOT swallowed —
    callers should treat write failures as significant and let them bubble.

    Parent-dir fsync is intentionally NOT performed; on power loss
    between rename and journal flush the entry is missing-not-corrupt,
    matching the F-1-3 disposition in
    [audit_trail_2026-04-28_hmm-fit-cache-persist.md].
    """
    cfg_dir = lgb_inner_cv_cfg_dir(run_dir, cfg_signature, lgb_seed=lgb_seed)
    cfg_dir.mkdir(parents=True, exist_ok=True)
    path = cfg_dir / LgbDrawKey(
        cfg_signature=cfg_signature, fold_id=fold_id, draw_idx=draw_idx
    ).filename()
    tmp = path.parent / (path.name + ".tmp")
    payload = _payload(
        cfg_signature=cfg_signature,
        fold_id=fold_id,
        draw_idx=draw_idx,
        params=params,
        fold_loglosses=fold_loglosses,
        fold_sharpes=fold_sharpes,
        producing_run_id=producing_run_id,
        lgb_seed=lgb_seed,
    )
    with tmp.open("wb") as f:
        pickle.dump(payload, f, protocol=_PICKLE_PROTOCOL)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return path


def load_draw_checkpoint(path: Path) -> dict[str, Any]:
    """Load a single per-(cfg, fold, draw) pickle. Schema-version mismatch raises.

    Programmer-error pickling exceptions (e.g. ``pickle.UnpicklingError``)
    propagate; truncated-file ``EOFError`` propagates so callers can
    treat it as a corrupt-checkpoint signal (typically: skip, do not
    crash the run). ``discover_draws`` does that catch.
    """
    with path.open("rb") as f:
        payload = pickle.load(f)  # noqa: S301 — trusted local artifact
    got = payload.get("schema_version")
    if got != SCHEMA_VERSION:
        raise ValueError(
            f"lgb_inner_cv_checkpoint schema-version mismatch at {path}: "
            f"got {got!r}, expected {SCHEMA_VERSION!r}. "
            f"Stale artifacts must not be silently loaded; "
            f"delete the per-cfg directory or re-run from scratch."
        )
    return payload


def discover_draws(
    run_dir: Path,
    cfg_signature: str,
    *,
    lgb_seed: int | None = None,
) -> dict[tuple[int, int], dict[str, Any]]:
    """Enumerate all per-(fold_id, draw_idx) pickles under one cfg's subdirectory.

    Returns ``{(fold_id, draw_idx): payload}``. Skips:
    - non-pickle filenames (anything that doesn't match
      ``fold_NN_draw_NNNN.pkl``).
    - corrupt / truncated pickles (``EOFError``, ``pickle.UnpicklingError``).
    - schema-version mismatches (``ValueError`` from
      ``load_draw_checkpoint``).

    Skips are silent (returns the records that loaded cleanly); the
    caller can compare ``len(returned)`` against expected ``n_draws *
    n_outer_folds`` to detect partial coverage.

    Round-1 audit Q-1-1 fix: returned dict is sorted by (fold_id, draw_idx)
    so cache-population iteration order is deterministic across hosts.
    """
    cfg_dir = lgb_inner_cv_cfg_dir(run_dir, cfg_signature, lgb_seed=lgb_seed)
    if not cfg_dir.exists():
        return {}
    out: dict[tuple[int, int], dict[str, Any]] = {}
    for child in cfg_dir.iterdir():
        if not child.is_file():
            continue
        m = _DRAW_FILENAME_RE.match(child.name)
        if not m:
            continue
        try:
            payload = load_draw_checkpoint(child)
        except (OSError, EOFError, pickle.UnpicklingError, ValueError):
            continue
        fold_id = int(payload.get("fold_id", -1))
        draw_idx = int(payload.get("draw_idx", -1))
        if fold_id < 0 or draw_idx < 0:
            continue
        out[(fold_id, draw_idx)] = payload
    # Q-1-1: deterministic order for downstream consumers.
    return dict(sorted(out.items()))


def check_provenance(
    payload: dict[str, Any], *, current_git_head: str | None = None
) -> list[str]:
    """Return list of provenance-mismatch strings.

    WARN-but-load semantics per ADR-0011 §"Provenance drift handling":
    schema-version drift hard-errors at ``load_draw_checkpoint``;
    everything else is reported here for the caller to log without
    aborting. Mirrors ``cfg_checkpoint.check_provenance``.
    """
    mismatches: list[str] = []
    cur_py = platform.python_version()
    cur_np = np.__version__
    cur_git = current_git_head or _capture_git_head()
    if payload.get("python_version") != cur_py:
        mismatches.append(
            f"python_version mismatch: payload={payload.get('python_version')!r} current={cur_py!r}"
        )
    if payload.get("numpy_version") != cur_np:
        mismatches.append(
            f"numpy_version mismatch: payload={payload.get('numpy_version')!r} current={cur_np!r}"
        )
    if (
        cur_git != "unknown"
        and payload.get("git_head", "unknown") != "unknown"
        and payload.get("git_head") != cur_git
    ):
        mismatches.append(
            f"git_head mismatch: payload={payload.get('git_head')!r} current={cur_git!r}"
        )
    return mismatches


def cfg_signature_from_key_tuple(key: tuple[str, int, float, int, int]) -> str:
    """Derive a stable cfg_signature from the same fields cfg_checkpoint
    uses. Mirrors ``cfg_checkpoint.CfgKey.signature()`` semantics so a
    single (sym, cfg_idx, pt_sl, vb_seconds, vol_lookback) tuple yields
    the same hex on both sides.

    Matches the canonical-string format of ``CfgKey.signature``:
    ``"<SYM>|<idx>|<pt_sl:.10f>|<vb>|<vl>"`` (pipe-separated;
    .10f precision on ``pt_sl`` for floating-point stability across
    runs that pass the same numeric value via different code paths).
    SHA256-hexed.
    """
    sym, cfg_idx, pt_sl, vb, vl = key
    canonical = (
        f"{sym.upper()}|{int(cfg_idx)}|{float(pt_sl):.10f}|"
        f"{int(vb)}|{int(vl)}"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def merge_resume_into_current(
    *,
    prior_run_dir: Path | None,
    current_run_dir: Path,
    cfg_signature: str,
    lgb_seed: int | None = None,
) -> dict[tuple[int, int], dict[str, Any]]:
    """Combine cached draws from a prior_run_dir AND the current run_dir.

    The current run_dir is the authoritative source: if both directories
    have a pickle for the same (fold_id, draw_idx), the current-run-dir
    value wins. Prior-run-dir entries are loaded for cross-attempt
    resume when the orchestrator is launched with
    ``--resume-cfg-checkpoint <prior_run_id>``.

    Q-1-1 fix: returned dict is sorted by (fold_id, draw_idx) for
    determinism across hosts.
    """
    merged: dict[tuple[int, int], dict[str, Any]] = {}
    if prior_run_dir is not None:
        merged.update(discover_draws(prior_run_dir, cfg_signature, lgb_seed=lgb_seed))
    # Current run dir overrides prior on key conflict.
    merged.update(discover_draws(current_run_dir, cfg_signature, lgb_seed=lgb_seed))
    return dict(sorted(merged.items()))


def filter_draws_by_fold(
    cached: dict[tuple[int, int], dict[str, Any]], fold_id: int
) -> dict[int, dict[str, Any]]:
    """Project the (fold_id, draw_idx) → payload dict down to the
    draws belonging to one fold. Returns ``{draw_idx: payload}``.

    Round-1 R-1-1 fix: ``_inner_cv_select_hp`` is invoked once per
    outer fold; this helper projects the global cached dict to the
    fold-local view that the function consumes.
    """
    return {
        d_idx: payload
        for (f_id, d_idx), payload in cached.items()
        if f_id == int(fold_id)
    }


def is_complete(
    cached_draws: dict[tuple[int, int], dict[str, Any]],
    n_draws: int,
    n_outer_folds: int,
) -> bool:
    """True iff every (fold_id, draw_idx) in
    ``range(n_outer_folds) × range(n_draws)`` is present."""
    if not cached_draws:
        return False
    return all(
        (f, d) in cached_draws
        for f in range(n_outer_folds)
        for d in range(n_draws)
    )


def write_resume_telemetry(
    *,
    sym: str,
    cfg_idx: int,
    cfg_signature: str,
    fold_id: int,
    n_draws: int,
    cached_for_fold: dict[int, dict[str, Any]],
    provenance_drift_count: int,
) -> dict[str, Any]:
    """Build the structured telemetry record the orchestrator emits at
    INFO level on resume. ``cached_for_fold`` is the post-projection
    fold-local dict (use ``filter_draws_by_fold`` first)."""
    return {
        "module": "lgb_inner_cv_checkpoint",
        "sym": sym,
        "cfg_idx": int(cfg_idx),
        "cfg_signature_short": cfg_signature[:16],
        "fold_id": int(fold_id),
        "n_draws_total": int(n_draws),
        "n_draws_cached": int(len(cached_for_fold)),
        "n_draws_remaining": int(n_draws - len(cached_for_fold)),
        "provenance_drift_count": int(provenance_drift_count),
    }
