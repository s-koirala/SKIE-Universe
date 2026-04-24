"""Walk-forward orchestration engine.

Consumes a :class:`skie_ninja.backtest.splits.SplitSpec`, a
caller-supplied ``fit_fn`` (where the
model-selection-inside-fold hook lives — Varma & Simon 2006;
Cawley & Talbot 2010), and an optional ``predict_fn`` that produces
per-fold out-of-sample predictions. Emits a compact run-ledger
(one row per fold) matching the Cycle-4 spec schema:

    fold_id, train_start, train_end, test_start, test_end,
    purge_start, purge_end, embargo_start, embargo_end,
    n_train, n_test, model_hash

plus a rolled-up model_hash over the per-fold sidecars — SHA256 of
the canonical concatenation ``"{fold_id}:{model_hash};"`` for all
folds sorted by ``fold_id``. That rolled-up hash is what the parent
:class:`~skie_ninja.utils.reproducibility.ReproLog` carries via
:func:`skie_ninja.utils.reproducibility.with_model_hash`.

References
----------

  - Varma, S. & Simon, R. 2006. "Bias in error estimation when
    using cross-validation for model selection". *BMC Bioinformatics*
    7:91. https://doi.org/10.1186/1471-2105-7-91
    Canonical primary source for the rule that model selection must
    be performed INSIDE the outer fold.
  - Cawley, G. C. & Talbot, N. L. C. 2010. "On over-fitting in
    model selection and subsequent selection bias in performance
    evaluation". *JMLR* 11: 2079-2107.
    http://jmlr.org/papers/v11/cawley10a.html
    Extends Varma & Simon with quantified selection-bias inflation.
    The engine does not itself perform model selection — the
    caller's ``fit_fn`` is the nested step. The engine's contribution
    is refusing to let the selection leak data through the fold
    boundary.

  - López de Prado, M. 2018. *AFML* §7.4. Purge + embargo semantics
    baked into the upstream :class:`SplitSpec`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from skie_ninja.backtest.leak_canaries import assert_fold_boundary_invariant
from skie_ninja.backtest.splits import Fold, SplitSpec


class FitFn(Protocol):
    """Callable signature for the per-fold fit step.

    Parameters
    ----------
    train_idx
        Integer positional indices into the full observation array.
        Already purged + embargoed by the splitter.
    *args, **kwargs
        Engine passes through positional and keyword args supplied
        to :meth:`WalkForwardEngine.run` unchanged. Typical usage:
        the caller supplies the full ``X`` / ``y`` arrays as keyword
        args, and the ``fit_fn`` slices them with ``train_idx``.

    Returns
    -------
    Any
        The fitted model or whatever ``predict_fn`` consumes. The
        engine is agnostic about the type.
    """

    def __call__(
        self, train_idx: np.ndarray, *args: Any, **kwargs: Any
    ) -> Any: ...


class PredictFn(Protocol):
    """Callable signature for the per-fold predict step."""

    def __call__(
        self,
        fitted: Any,
        test_idx: np.ndarray,
        *args: Any,
        **kwargs: Any,
    ) -> np.ndarray: ...


class HashFn(Protocol):
    """Callable that hashes a fitted object to its sidecar SHA256.

    Integration with the Cycle-3 HMM toolkit: pass
    ``lambda m: write_sidecar(build_sidecar(m), path)[1]`` so each
    fold produces a full HMM sidecar JSON whose SHA256 rolls into
    the engine ledger.
    """

    def __call__(self, fitted: Any) -> str: ...


@dataclass(frozen=True)
class FoldRecord:
    """One row of the run-ledger.

    Matches the Cycle-4 spec schema field-for-field. Stored here as
    a frozen dataclass to simplify round-trip against the parquet
    encoding in :func:`run_ledger_to_table` / :func:`run_ledger_from_table`.
    """

    fold_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    purge_start: int
    purge_end: int
    embargo_start: int
    embargo_end: int
    n_train: int
    n_test: int
    model_hash: str


@dataclass
class WalkForwardResult:
    """Aggregate engine output.

    Fields
    ------
    fold_records
        Per-fold ledger rows in ``fold_id`` order.
    rolled_up_model_hash
        SHA256 of the canonical serialisation
        ``"{fold_id}:{model_hash};"`` for all folds sorted by
        ``fold_id``. This is what
        :func:`skie_ninja.utils.reproducibility.with_model_hash`
        consumes.
    predictions
        List of numpy arrays, one per fold, each of shape
        ``(n_test_for_fold, ...)``.
    test_indices
        Integer indices each fold predicted on, so callers can align
        predictions back to the original observation sequence without
        re-deriving fold boundaries.
    fitted_models
        Optional list of fitted objects returned by ``fit_fn``,
        retained only when :meth:`WalkForwardEngine.run` is called
        with ``keep_fitted=True``. Default ``[]`` — models can be
        memory-heavy and most downstream flows only need predictions.
    """

    fold_records: list[FoldRecord]
    rolled_up_model_hash: str
    predictions: list[np.ndarray]
    test_indices: list[np.ndarray]
    fitted_models: list[Any] = field(default_factory=list)


class WalkForwardEngine:
    """Orchestrator over a :class:`SplitSpec`.

    Contract
    --------
    - Each fold's training block is passed to ``fit_fn`` **only after**
      :func:`assert_fold_boundary_invariant` succeeds. This is the
      engine-level manifestation of leak canary (a).
    - ``fit_fn`` is responsible for any nested model selection (BIC
      grid, CV grid, hyperparameter search). The engine does not
      inspect or replay that search — it only guarantees the training
      index set that feeds it is the purged+embargoed one.
    - ``predict_fn`` receives the fitted object plus the test indices;
      the engine never touches the test portion of any features
      during fit.
    - If ``hash_fn`` is supplied, the engine calls it on each fitted
      object and rolls the SHA256 digests into a single parent hash.

    Feature-timestamp gate
    ----------------------
    :meth:`run` requires ``feature_timestamps`` and
    ``observation_timestamps`` — both one-dimensional arrays of length
    ``split_spec.n_samples``. A caller that cannot produce
    ``feature_timestamps`` (because the feature matrix is not rendered
    at the ingest layer) must at minimum pass
    ``feature_timestamps = observation_timestamps``, which reduces
    the invariant to "observation timestamps are monotone". Passing
    stale / mislabelled timestamps in order to bypass the check
    defeats the purpose of the canary and is flagged in the Cycle-4
    audit trail as a misuse.
    """

    def __init__(self, split_spec: SplitSpec) -> None:
        self.split_spec = split_spec

    def run(
        self,
        *,
        fit_fn: FitFn,
        predict_fn: PredictFn | None = None,
        hash_fn: HashFn | None = None,
        feature_timestamps: np.ndarray,
        observation_timestamps: np.ndarray,
        keep_fitted: bool = False,
        fit_kwargs: dict[str, Any] | None = None,
        predict_kwargs: dict[str, Any] | None = None,
    ) -> WalkForwardResult:
        """Execute the walk-forward run.

        Parameters
        ----------
        fit_fn
            See :class:`FitFn`.
        predict_fn
            See :class:`PredictFn`. If ``None``, the engine skips
            prediction and returns an empty ``predictions`` list.
        hash_fn
            See :class:`HashFn`. If ``None``, per-fold model_hash
            entries are ``"no-hash"`` and the rolled-up hash is
            computed over those literal strings (still deterministic,
            but carries no model-identity information — useful for
            test runs that do not care about the ledger hash).
        feature_timestamps, observation_timestamps
            See class docstring. Both arrays must have length
            ``split_spec.n_samples``.
        keep_fitted
            If ``True``, retain each fitted object in the result.
            Default ``False`` (models may be memory-heavy).
        fit_kwargs, predict_kwargs
            Keyword arguments forwarded verbatim to ``fit_fn`` /
            ``predict_fn``. Positional ``train_idx`` / ``test_idx`` are
            always first; additional data arrays go here.
        """
        n = self.split_spec.n_samples
        if feature_timestamps.shape != (n,) or observation_timestamps.shape != (n,):
            raise ValueError(
                f"feature_timestamps and observation_timestamps must both "
                f"have shape ({n},); got {feature_timestamps.shape!r} and "
                f"{observation_timestamps.shape!r}."
            )

        fit_kwargs = dict(fit_kwargs or {})
        predict_kwargs = dict(predict_kwargs or {})

        fold_records: list[FoldRecord] = []
        predictions: list[np.ndarray] = []
        test_indices: list[np.ndarray] = []
        fitted_models: list[Any] = []
        per_fold_hashes: list[tuple[int, str]] = []

        for fold in self.split_spec.folds:
            # Leak canary (a) — before any compute.
            assert_fold_boundary_invariant(
                fold,
                feature_timestamps=feature_timestamps,
                observation_timestamps=observation_timestamps,
            )

            train_idx = np.asarray(fold.train_indices(), dtype=np.int64)
            test_idx = np.asarray(fold.test_indices(), dtype=np.int64)

            fitted = fit_fn(train_idx, **fit_kwargs)

            if predict_fn is not None:
                preds = predict_fn(fitted, test_idx, **predict_kwargs)
                preds_arr = np.asarray(preds)
                if preds_arr.shape[0] != test_idx.size:
                    raise ValueError(
                        f"Fold {fold.fold_id}: predict_fn returned "
                        f"{preds_arr.shape[0]} rows but test set has "
                        f"{test_idx.size}."
                    )
                predictions.append(preds_arr)
                test_indices.append(test_idx)

            model_hash = hash_fn(fitted) if hash_fn is not None else "no-hash"
            per_fold_hashes.append((fold.fold_id, model_hash))

            fold_records.append(_fold_record(fold, model_hash))

            if keep_fitted:
                fitted_models.append(fitted)

        rolled = roll_up_model_hashes(per_fold_hashes)

        return WalkForwardResult(
            fold_records=fold_records,
            rolled_up_model_hash=rolled,
            predictions=predictions,
            test_indices=test_indices,
            fitted_models=fitted_models,
        )


def roll_up_model_hashes(
    per_fold: list[tuple[int, str]] | list[FoldRecord]
) -> str:
    """Canonical rolled-up hash.

    ``per_fold`` may be either a list of ``(fold_id, hash)`` tuples
    or a list of :class:`FoldRecord`. Output is the SHA256 over the
    bytes ``f"{fold_id}:{hash};"`` for each entry, sorted by
    ``fold_id``. Sorting is explicit so re-ordering the input does
    not change the output.
    """
    pairs: list[tuple[int, str]] = []
    for item in per_fold:
        if isinstance(item, FoldRecord):
            pairs.append((item.fold_id, item.model_hash))
        else:
            pairs.append(item)
    pairs.sort(key=lambda p: p[0])
    h = hashlib.sha256()
    for fold_id, model_hash in pairs:
        h.update(f"{fold_id}:{model_hash};".encode())
    return h.hexdigest()


def _fold_record(fold: Fold, model_hash: str) -> FoldRecord:
    return FoldRecord(
        fold_id=fold.fold_id,
        train_start=fold.train_start,
        train_end=fold.train_end,
        test_start=fold.test_start,
        test_end=fold.test_end,
        purge_start=fold.purge_start,
        purge_end=fold.purge_end,
        embargo_start=fold.embargo_start,
        embargo_end=fold.embargo_end,
        n_train=fold.n_train,
        n_test=fold.n_test,
        model_hash=model_hash,
    )


# ---------------------------------------------------------------------------
# Parquet ledger round-trip
# ---------------------------------------------------------------------------

_LEDGER_COLUMNS: tuple[str, ...] = (
    "fold_id",
    "train_start",
    "train_end",
    "test_start",
    "test_end",
    "purge_start",
    "purge_end",
    "embargo_start",
    "embargo_end",
    "n_train",
    "n_test",
    "model_hash",
)


def write_run_ledger(
    records: list[FoldRecord],
    path: Path,
) -> Path:
    """Atomically write the run-ledger parquet under ``path``.

    Schema is fixed by :data:`_LEDGER_COLUMNS`. Written via polars
    (project-default tabular engine) with ``Int64`` positional
    columns and a ``Utf8`` ``model_hash``. Atomicity is provided by
    writing to a sibling ``.tmp`` path and ``os.replace``-ing —
    same pattern as
    :meth:`~skie_ninja.utils.reproducibility.ReproLog.write`.
    """
    import os

    import polars as pl

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "fold_id": [r.fold_id for r in records],
        "train_start": [r.train_start for r in records],
        "train_end": [r.train_end for r in records],
        "test_start": [r.test_start for r in records],
        "test_end": [r.test_end for r in records],
        "purge_start": [r.purge_start for r in records],
        "purge_end": [r.purge_end for r in records],
        "embargo_start": [r.embargo_start for r in records],
        "embargo_end": [r.embargo_end for r in records],
        "n_train": [r.n_train for r in records],
        "n_test": [r.n_test for r in records],
        "model_hash": [r.model_hash for r in records],
    }
    frame = pl.DataFrame(data, schema=_ledger_schema())

    tmp = path.with_suffix(path.suffix + ".tmp")
    frame.write_parquet(tmp)
    os.replace(tmp, path)
    return path


def read_run_ledger(path: Path) -> list[FoldRecord]:
    """Inverse of :func:`write_run_ledger`.

    Raises :class:`ValueError` if the on-disk column names or dtypes
    do not match :data:`_LEDGER_COLUMNS` / :func:`_ledger_schema` —
    silently accepting schema drift (column renames, Utf8→binary
    reshuffles, Int64→Int32 coercions) would let a future refactor
    break the rolled-up-hash round-trip without surfacing.
    """
    import polars as pl

    frame = pl.read_parquet(Path(path))
    if tuple(frame.columns) != _LEDGER_COLUMNS:
        raise ValueError(
            f"Run-ledger schema mismatch. Expected columns "
            f"{_LEDGER_COLUMNS!r}; got {tuple(frame.columns)!r}."
        )
    expected_schema = _ledger_schema()
    actual_schema = {name: frame.schema[name] for name in _LEDGER_COLUMNS}
    if actual_schema != expected_schema:
        raise ValueError(
            f"Run-ledger dtype mismatch. Expected {expected_schema!r}; "
            f"got {actual_schema!r}."
        )
    rows = frame.to_dicts()
    return [FoldRecord(**row) for row in rows]


def _ledger_schema() -> dict[str, Any]:
    """Canonical ``{column: polars-dtype}`` map for the run-ledger.

    Centralised so :func:`write_run_ledger` emits and
    :func:`read_run_ledger` validates against the same source of
    truth. Positional fields are ``Int64``; ``model_hash`` is
    ``Utf8``.
    """
    import polars as pl

    schema: dict[str, Any] = {c: pl.Int64 for c in _LEDGER_COLUMNS if c != "model_hash"}
    schema["model_hash"] = pl.Utf8
    return schema


def ledger_path_for(
    run_id: str, *, logs_reproducibility_dir: Path
) -> Path:
    """Canonical run-ledger location per the Cycle-4 spec.

    ``logs/reproducibility/{run_id}_walk_forward_folds.parquet``
    """
    return Path(logs_reproducibility_dir) / f"{run_id}_walk_forward_folds.parquet"


__all__ = [
    "FitFn",
    "FoldRecord",
    "HashFn",
    "PredictFn",
    "WalkForwardEngine",
    "WalkForwardResult",
    "ledger_path_for",
    "read_run_ledger",
    "roll_up_model_hashes",
    "write_run_ledger",
]
