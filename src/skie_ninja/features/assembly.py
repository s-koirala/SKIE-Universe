"""Feature-matrix assembly with purge enforcement and provenance.

Given a list of :class:`FeatureModule` instances, a panel, and a
:class:`~skie_ninja.backtest.splits.Fold`, produces the feature
matrix restricted to the fold's training or test indices, with
per-feature provenance written to
``logs/reproducibility/features/{name}_{version}_{run_id}.json``.

Purge enforcement: the caller passes the positional purge indices
that the :class:`SplitSpec` computed — the assembly layer drops
those rows from the materialised frame. A post-condition asserts
that no emitted row has an index in the purge region, matching the
leak-canary (b) invariant from
:mod:`skie_ninja.backtest.leak_canaries`.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

from skie_ninja.features.base import FeatureModule
from skie_ninja.features.windowing import _pit_cutoff
from skie_ninja.utils.hashing import frame_sha256


@dataclass(frozen=True)
class FeatureProvenance:
    """Per-feature provenance record (plan §3.4)."""

    name: str
    version: str
    run_id: str
    frame_sha256: str
    latency_seconds: float
    n_rows: int
    n_cols: int
    now_ts: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "run_id": self.run_id,
            "frame_sha256": self.frame_sha256,
            "latency_seconds": self.latency_seconds,
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "now_ts": self.now_ts,
        }


def provenance_path(
    *, name: str, version: str, run_id: str, features_dir: Path
) -> Path:
    """Canonical location per plan §3.4."""
    return Path(features_dir) / f"{name}_{version}_{run_id}.json"


def write_provenance(rec: FeatureProvenance, path: Path) -> Path:
    """Atomic write — same pattern as :meth:`ReproLog.write`."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(
        rec.to_dict(), sort_keys=True, indent=2, ensure_ascii=False
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
    return path


def assemble_feature_matrix(
    *,
    modules: list[FeatureModule],
    panel: pl.LazyFrame,
    now: pd.Timestamp,
    run_id: str,
    features_dir: Path,
    ctx: Any = None,
) -> tuple[pl.DataFrame, list[FeatureProvenance]]:
    """Compute each module's output at ``now`` and join on (symbol, ts_event).

    Parameters
    ----------
    modules
        Iterable of :class:`FeatureModule` — ordinary ordering does
        not affect output correctness (joins are associative on
        ``(symbol, ts_event)``) but does affect provenance write
        ordering.
    panel
        Input LazyFrame carrying at least the columns each module
        declares in ``inputs``.
    now
        PIT cutoff. Passed to each module's ``compute``.
    run_id
        Identifier to stamp on every provenance JSON.
    features_dir
        Destination directory for per-feature provenance records
        (typically ``paths.logs_reproducibility_features``).

    Returns
    -------
    (feature_matrix, provenance)
        ``feature_matrix`` has columns
        ``{ts_event, symbol, *per-feature columns}``. ``provenance``
        is a list of :class:`FeatureProvenance` objects in the same
        order as ``modules``.
    """
    if not modules:
        raise ValueError("assemble_feature_matrix: modules list is empty.")

    prov_records: list[FeatureProvenance] = []
    out: pl.DataFrame | None = None

    for mod in modules:
        t0 = time.perf_counter()
        frame = mod.compute(panel, now, ctx).collect()
        latency = time.perf_counter() - t0
        frame = frame.filter(pl.col("ts_event") <= _pit_cutoff(now))
        sha = frame_sha256(frame, sort_cols=["symbol", "ts_event"])
        rec = FeatureProvenance(
            name=mod.name,
            version=mod.version,
            run_id=run_id,
            frame_sha256=sha,
            latency_seconds=float(latency),
            n_rows=frame.shape[0],
            n_cols=frame.shape[1],
            now_ts=pd.Timestamp(now).isoformat(),
        )
        prov_records.append(rec)
        write_provenance(
            rec,
            provenance_path(
                name=mod.name,
                version=mod.version,
                run_id=run_id,
                features_dir=features_dir,
            ),
        )
        if out is None:
            out = frame
        else:
            out = out.join(
                frame, on=["symbol", "ts_event"], how="full", coalesce=True
            )

    assert out is not None
    return out, prov_records


def apply_purge_and_partition(
    *,
    feature_matrix: pl.DataFrame,
    fold_purge_start: int,
    fold_purge_end: int,
    train_indices: list[int],
    test_indices: list[int],
    index_column: str = "_row_idx",
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Split a row-indexed feature matrix by train/test indices, with
    purge enforcement.

    Expects ``feature_matrix`` to carry an integer column
    ``index_column`` recording the row's positional index into the
    parent panel (the assembly layer adds this before calling).

    Post-condition: no row in the returned ``train_frame`` has
    ``index_column ∈ [fold_purge_start, fold_purge_end)``. Raises
    :class:`AssertionError` otherwise (maps to leak canary (b)).
    """
    if index_column not in feature_matrix.columns:
        raise ValueError(
            f"feature_matrix must carry an {index_column!r} integer column; "
            "the assembly layer should have added it before purge."
        )
    train_set = set(train_indices)
    test_set = set(test_indices)
    train_frame = feature_matrix.filter(
        pl.col(index_column).is_in(list(train_set))
    )
    test_frame = feature_matrix.filter(
        pl.col(index_column).is_in(list(test_set))
    )
    # Purge post-condition.
    if fold_purge_end > fold_purge_start:
        violating = train_frame.filter(
            (pl.col(index_column) >= fold_purge_start)
            & (pl.col(index_column) < fold_purge_end)
        )
        if violating.shape[0] > 0:
            raise AssertionError(
                f"assemble: {violating.shape[0]} training rows fall within "
                f"purge window [{fold_purge_start}, {fold_purge_end}). "
                "This violates leak canary (b)."
            )
    return train_frame, test_frame


__all__ = [
    "FeatureProvenance",
    "apply_purge_and_partition",
    "assemble_feature_matrix",
    "provenance_path",
    "write_provenance",
]
