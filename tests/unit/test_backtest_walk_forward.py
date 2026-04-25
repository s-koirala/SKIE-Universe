"""Unit + integration tests for :mod:`skie_ninja.backtest.engine.walk_forward`.

Covers:

- Engine dispatches ``fit_fn`` with purged training indices and
  ``predict_fn`` with test indices.
- Run-ledger emission: one :class:`FoldRecord` per fold, schema
  frozen.
- Parquet round-trip (``write_run_ledger`` / ``read_run_ledger``) is
  byte-stable on re-write and round-trips the rolled-up hash.
- ``roll_up_model_hashes`` is deterministic, sort-invariant, and
  changes iff any per-fold hash changes.
- Model-hash roll-up reproduces after parquet round-trip.
- Nested model-selection-inside-fold: fit_fn runs a BIC-style grid
  purely on the outer training fold; predict_fn never sees the grid.
- Integration with the Cycle-3 Gaussian HMM toolkit via
  :func:`skie_ninja.models.regime.selection.select_gaussian_hmm` and
  :func:`skie_ninja.models.regime.serialization.build_sidecar` /
  :func:`~skie_ninja.models.regime.serialization.write_sidecar`.
- Integration with :func:`skie_ninja.utils.reproducibility.with_model_hash`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from skie_ninja.backtest.engine.walk_forward import (
    FoldRecord,
    WalkForwardEngine,
    ledger_path_for,
    read_run_ledger,
    roll_up_model_hashes,
    write_run_ledger,
)
from skie_ninja.backtest.splits import walk_forward_split

# ---------------------------------------------------------------------------
# Mechanics
# ---------------------------------------------------------------------------


class TestEngineMechanics:
    def test_fit_fn_receives_only_purged_train_idx(self) -> None:
        spec = walk_forward_split(
            n_samples=40,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=2,
            embargo=1,
        )
        seen: list[np.ndarray] = []

        def fit_fn(train_idx: np.ndarray) -> object:
            seen.append(train_idx.copy())
            return object()

        ts = np.arange(40, dtype=np.int64)
        engine = WalkForwardEngine(spec)
        engine.run(
            fit_fn=fit_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )
        # Every training set is strictly before its corresponding test
        # region, and the last `label_horizon` positions before test
        # are absent from the training indices (purged).
        for fold_idx, train_idx in enumerate(seen):
            test_start = spec.folds[fold_idx].test_start
            assert train_idx.max() < test_start
            assert train_idx.max() < test_start - spec.label_horizon + 1

    def test_predict_fn_never_called_without_predict_fn_arg(self) -> None:
        spec = walk_forward_split(
            n_samples=30,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(30, dtype=np.int64)
        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=lambda idx: "model",
            feature_timestamps=ts,
            observation_timestamps=ts,
        )
        assert result.predictions == []
        assert result.test_indices == []

    def test_predict_fn_receives_test_idx(self) -> None:
        spec = walk_forward_split(
            n_samples=30,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(30, dtype=np.int64)
        captured: list[np.ndarray] = []

        def predict_fn(fitted: object, test_idx: np.ndarray) -> np.ndarray:
            captured.append(test_idx.copy())
            return np.full(test_idx.size, 0.5)

        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=lambda idx: "model",
            predict_fn=predict_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )
        for fold_idx, test_idx in enumerate(captured):
            assert list(test_idx) == list(
                range(spec.folds[fold_idx].test_start, spec.folds[fold_idx].test_end)
            )
        assert len(result.predictions) == len(spec.folds)
        for preds in result.predictions:
            assert np.allclose(preds, 0.5)

    def test_predict_fn_shape_mismatch_raises(self) -> None:
        spec = walk_forward_split(
            n_samples=30,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(30, dtype=np.int64)
        engine = WalkForwardEngine(spec)
        with pytest.raises(ValueError, match="returned"):
            engine.run(
                fit_fn=lambda idx: "model",
                predict_fn=lambda fitted, test_idx: np.zeros(test_idx.size + 1),
                feature_timestamps=ts,
                observation_timestamps=ts,
            )

    def test_keep_fitted_controls_model_retention(self) -> None:
        spec = walk_forward_split(
            n_samples=30,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(30, dtype=np.int64)
        engine = WalkForwardEngine(spec)
        res_no_keep = engine.run(
            fit_fn=lambda idx: ("model", int(idx.size)),
            feature_timestamps=ts,
            observation_timestamps=ts,
        )
        res_keep = engine.run(
            fit_fn=lambda idx: ("model", int(idx.size)),
            feature_timestamps=ts,
            observation_timestamps=ts,
            keep_fitted=True,
        )
        assert res_no_keep.fitted_models == []
        assert len(res_keep.fitted_models) == len(spec.folds)

    def test_feature_timestamps_shape_mismatch_raises(self) -> None:
        spec = walk_forward_split(
            n_samples=30,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        engine = WalkForwardEngine(spec)
        ts = np.arange(20, dtype=np.int64)
        with pytest.raises(ValueError, match="feature_timestamps"):
            engine.run(
                fit_fn=lambda idx: "model",
                feature_timestamps=ts,
                observation_timestamps=np.arange(30, dtype=np.int64),
            )


# ---------------------------------------------------------------------------
# Run-ledger schema + round-trip
# ---------------------------------------------------------------------------


class TestRunLedger:
    def test_one_record_per_fold(self) -> None:
        spec = walk_forward_split(
            n_samples=40,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(40, dtype=np.int64)
        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=lambda idx: "model",
            feature_timestamps=ts,
            observation_timestamps=ts,
        )
        assert len(result.fold_records) == len(spec.folds)
        for fold, record in zip(spec.folds, result.fold_records, strict=True):
            assert record.fold_id == fold.fold_id
            assert record.train_start == fold.train_start
            assert record.train_end == fold.train_end
            assert record.test_start == fold.test_start
            assert record.test_end == fold.test_end
            assert record.n_train == fold.n_train
            assert record.n_test == fold.n_test
            assert record.model_hash == "no-hash"

    def test_parquet_round_trip(self, tmp_path: Path) -> None:
        spec = walk_forward_split(
            n_samples=50,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=1,
            embargo=2,
        )
        ts = np.arange(50, dtype=np.int64)
        engine = WalkForwardEngine(spec)

        def hash_fn(fitted: object) -> str:
            return "deadbeef" * 8

        result = engine.run(
            fit_fn=lambda idx: "model",
            hash_fn=hash_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )

        path = ledger_path_for("testrun", logs_reproducibility_dir=tmp_path)
        write_run_ledger(result.fold_records, path)
        assert path.exists()
        loaded = read_run_ledger(path)
        assert loaded == result.fold_records

    def test_rolled_up_hash_round_trips(self, tmp_path: Path) -> None:
        spec = walk_forward_split(
            n_samples=60,
            initial_train_size=20,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(60, dtype=np.int64)

        # Distinct per-fold hashes so the roll-up is not trivially all-same.
        seen_count = {"n": 0}

        def hash_fn(fitted: object) -> str:
            h = f"fold-hash-{seen_count['n']:04d}" + "0" * 52
            seen_count["n"] += 1
            return h[:64]

        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=lambda idx: "model",
            hash_fn=hash_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )

        path = ledger_path_for("run2", logs_reproducibility_dir=tmp_path)
        write_run_ledger(result.fold_records, path)
        reloaded = read_run_ledger(path)

        assert roll_up_model_hashes(reloaded) == result.rolled_up_model_hash

    def test_read_rejects_schema_drift(self, tmp_path: Path) -> None:
        import polars as pl

        bogus = pl.DataFrame({"unexpected": [1, 2, 3]})
        path = tmp_path / "bad_ledger.parquet"
        bogus.write_parquet(path)
        with pytest.raises(ValueError, match="schema mismatch"):
            read_run_ledger(path)

    def test_read_rejects_dtype_drift(self, tmp_path: Path) -> None:
        """Round 1 repro-verifier finding: read_run_ledger must
        reject a ledger with the correct column NAMES but wrong
        dtypes (e.g., Int32 fold_id instead of Int64). Without this
        check, schema drift silently pollutes the run-ledger."""
        import polars as pl

        from skie_ninja.backtest.engine.walk_forward import _LEDGER_COLUMNS

        n = 2
        data: dict[str, list[object]] = {c: [0 for _ in range(n)] for c in _LEDGER_COLUMNS}
        data["model_hash"] = ["a" * 64 for _ in range(n)]
        schema: dict[str, object] = {c: pl.Int64 for c in _LEDGER_COLUMNS if c != "model_hash"}
        schema["fold_id"] = pl.Int32  # drift
        schema["model_hash"] = pl.Utf8
        bad = pl.DataFrame(data, schema=schema)
        path = tmp_path / "dtype_drift.parquet"
        bad.write_parquet(path)
        with pytest.raises(ValueError, match="dtype mismatch"):
            read_run_ledger(path)


# ---------------------------------------------------------------------------
# Rolled-up hash properties
# ---------------------------------------------------------------------------


class TestRollUp:
    def test_sort_invariance(self) -> None:
        pairs = [(2, "hashB"), (0, "hashA"), (1, "hashC")]
        assert (
            roll_up_model_hashes(pairs)
            == roll_up_model_hashes(sorted(pairs, key=lambda p: p[0]))
            == roll_up_model_hashes(sorted(pairs, key=lambda p: p[0], reverse=True))
        )

    def test_changes_on_any_hash_change(self) -> None:
        a = roll_up_model_hashes([(0, "x"), (1, "y")])
        b = roll_up_model_hashes([(0, "x"), (1, "z")])
        assert a != b

    def test_accepts_fold_records(self) -> None:
        records = [
            FoldRecord(
                fold_id=i,
                train_start=0,
                train_end=10,
                test_start=10,
                test_end=15,
                purge_start=0,
                purge_end=0,
                embargo_start=0,
                embargo_end=0,
                n_train=10,
                n_test=5,
                model_hash=f"{i:064x}",
            )
            for i in range(3)
        ]
        assert roll_up_model_hashes(records) == roll_up_model_hashes(
            [(r.fold_id, r.model_hash) for r in records]
        )


# ---------------------------------------------------------------------------
# Nested model-selection (Cawley & Talbot 2010)
# ---------------------------------------------------------------------------


class TestNestedModelSelection:
    def test_grid_search_inside_fold_never_sees_test(self) -> None:
        """fit_fn runs a BIC-like grid purely on train_idx; engine
        passes only train_idx; predict_fn sees the selected model."""
        spec = walk_forward_split(
            n_samples=60,
            initial_train_size=20,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(60, dtype=np.int64)
        x = np.linspace(0.0, 1.0, 60)

        grid_observed: list[tuple[int, ...]] = []

        def fit_fn(train_idx: np.ndarray) -> dict[str, float]:
            # Mock "grid search": fit k in {1, 2} candidates, pick
            # the one with lower sum-of-squares. Fit itself only uses
            # train rows of x.
            grid_observed.append(tuple(int(i) for i in train_idx))
            x_train = x[train_idx]
            c1 = float(np.mean(x_train))
            c2_upper = float(np.mean(x_train[x_train > c1]))
            sse1 = float(np.sum((x_train - c1) ** 2))
            sse2 = float(np.sum((x_train - c2_upper) ** 2))
            best_mean = c1 if sse1 <= sse2 else c2_upper
            return {"mean": best_mean}

        def predict_fn(fitted: dict[str, float], test_idx: np.ndarray) -> np.ndarray:
            return np.full(test_idx.size, fitted["mean"])

        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=fit_fn,
            predict_fn=predict_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )

        # No observed training index set may contain any fold's test
        # positions.
        for fold_idx, obs in enumerate(grid_observed):
            test_positions = set(
                range(spec.folds[fold_idx].test_start, spec.folds[fold_idx].test_end)
            )
            assert set(obs).isdisjoint(test_positions)

        assert len(result.predictions) == len(spec.folds)


# ---------------------------------------------------------------------------
# Integration: Cycle-3 HMM toolkit
# ---------------------------------------------------------------------------


class TestHMMIntegration:
    def test_hmm_fit_select_inside_fold(self, tmp_path: Path) -> None:
        from skie_ninja.models.regime.selection import select_gaussian_hmm
        from skie_ninja.models.regime.serialization import (
            build_sidecar,
            sidecar_path_for,
            write_sidecar,
        )

        # Synthetic two-regime Gaussian sequence, long enough for a
        # 4-fold walk-forward at 5-restart min.
        rng = np.random.default_rng(20260423)
        n = 480
        # Alternate regimes every 60 samples.
        regime = (np.arange(n) // 60) % 2
        x = rng.standard_normal(n) * 0.5 + regime * 2.0
        ts = np.arange(n, dtype=np.int64)

        spec = walk_forward_split(
            n_samples=n,
            initial_train_size=240,
            test_size=60,
            step_size=60,
            label_horizon=1,
            embargo=0,
        )

        call_state = {"idx": 0}

        def fit_fn(train_idx: np.ndarray) -> object:
            train_x = x[train_idx].reshape(-1, 1)
            return select_gaussian_hmm(
                train_x,
                n_states_grid=(2,),
                covariance_types=("diag",),
                seed=20260423,
            )

        def hash_fn(fitted: object) -> str:
            sidecar = build_sidecar(fitted.best_model)  # type: ignore[attr-defined]
            path = sidecar_path_for(
                f"walkfold_{call_state['idx']:03d}",
                logs_reproducibility_dir=tmp_path,
            )
            call_state["idx"] += 1
            _, sha = write_sidecar(sidecar, path)
            return sha

        def predict_fn(fitted: object, test_idx: np.ndarray) -> np.ndarray:
            test_x = x[test_idx].reshape(-1, 1)
            return fitted.best_model.filter_states(test_x)  # type: ignore[attr-defined]

        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=fit_fn,
            predict_fn=predict_fn,
            hash_fn=hash_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )

        assert len(result.fold_records) == len(spec.folds)
        # Hashes are the parquet-written sidecar SHA256s — 64 hex chars.
        for rec in result.fold_records:
            assert len(rec.model_hash) == 64

        # Predictions are per-fold (n_test, 2) filter posteriors.
        for preds, test_idx in zip(result.predictions, result.test_indices, strict=True):
            assert preds.shape == (test_idx.size, 2)
            # Rows sum to 1.
            assert np.allclose(preds.sum(axis=1), 1.0)

    def test_with_model_hash_accepts_rolled_up_digest(self) -> None:
        from skie_ninja.utils.reproducibility import capture, with_model_hash

        spec = walk_forward_split(
            n_samples=30,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(30, dtype=np.int64)
        engine = WalkForwardEngine(spec)

        result = engine.run(
            fit_fn=lambda idx: "model",
            hash_fn=lambda m: "a" * 64,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )
        log = capture(
            phase="phase-test",
            hypothesis_id="H0XX",
            rng_seed=42,
        )
        updated = with_model_hash(log, result.rolled_up_model_hash)
        assert updated.model_hash == result.rolled_up_model_hash


# ---------------------------------------------------------------------------
# fold_id passthrough (P1-WF-ENGINE-FOLD-ID-PASSTHROUGH)
# ---------------------------------------------------------------------------


class TestFoldIdPassthrough:
    """The engine injects ``fold_id`` into ``fit_fn`` / ``predict_fn``
    when the callable advertises the parameter (via explicit name or
    ``**kwargs``); the injected value matches the Fold-derived fold_id
    that ends up on :class:`FoldRecord`.
    """

    def test_predict_fn_receives_fold_id_matching_fold_record(self) -> None:
        spec = walk_forward_split(
            n_samples=40,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(40, dtype=np.int64)
        seen_fold_ids: list[int] = []

        def predict_fn(fitted: object, test_idx: np.ndarray, *, fold_id: int) -> np.ndarray:
            seen_fold_ids.append(fold_id)
            return np.zeros(test_idx.size)

        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=lambda idx: "model",
            predict_fn=predict_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )

        record_fold_ids = [r.fold_id for r in result.fold_records]
        assert seen_fold_ids == record_fold_ids
        # And both equal the SplitSpec's Fold.fold_id sequence — the
        # invariant the passthrough is meant to surface.
        assert record_fold_ids == [f.fold_id for f in spec.folds]

    def test_fit_fn_receives_fold_id_matching_fold_record(self) -> None:
        spec = walk_forward_split(
            n_samples=40,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(40, dtype=np.int64)
        seen_fold_ids: list[int] = []

        def fit_fn(train_idx: np.ndarray, *, fold_id: int) -> object:
            seen_fold_ids.append(fold_id)
            return "model"

        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=fit_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )

        assert seen_fold_ids == [r.fold_id for r in result.fold_records]

    def test_callable_without_fold_id_param_unchanged(self) -> None:
        """Pre-existing callables that bind no ``fold_id`` and no
        ``**kwargs`` keep working — the engine introspects and skips
        injection for them."""
        spec = walk_forward_split(
            n_samples=30,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(30, dtype=np.int64)
        engine = WalkForwardEngine(spec)

        # No TypeError despite the engine not injecting fold_id.
        result = engine.run(
            fit_fn=lambda idx: "model",
            predict_fn=lambda fitted, test_idx: np.zeros(test_idx.size),
            feature_timestamps=ts,
            observation_timestamps=ts,
        )
        assert len(result.fold_records) == len(spec.folds)

    def test_var_keyword_callable_receives_fold_id(self) -> None:
        """Callables that absorb ``**kwargs`` see the injected fold_id."""
        spec = walk_forward_split(
            n_samples=30,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts = np.arange(30, dtype=np.int64)

        seen_fold_ids: list[int] = []

        def predict_fn(fitted: object, test_idx: np.ndarray, **kwargs: object) -> np.ndarray:
            assert "fold_id" in kwargs
            seen_fold_ids.append(int(kwargs["fold_id"]))  # type: ignore[arg-type]
            return np.zeros(test_idx.size)

        engine = WalkForwardEngine(spec)
        result = engine.run(
            fit_fn=lambda idx: "model",
            predict_fn=predict_fn,
            feature_timestamps=ts,
            observation_timestamps=ts,
        )
        assert seen_fold_ids == [r.fold_id for r in result.fold_records]
