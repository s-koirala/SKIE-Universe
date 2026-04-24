"""Leak-canary unit tests.

Every canary here MUST catch an injected leak. A dead canary (one
that silently passes with the leak present) is a failed cycle per
the Cycle-4 spec.

The three canaries:

  (a) Future-return feature in a training row —
      :func:`assert_fold_boundary_invariant`.
  (b) Label horizon exceeds purge window — at
      :class:`SplitSpec` construction and via
      :func:`assert_purge_covers_label_horizon`.
  (c) Fit call consumes test-fold observations — via
      :class:`FitCallObserver`, including an end-to-end case where
      an HMM fit path is monkey-patched to peek at test data.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.backtest.engine.walk_forward import WalkForwardEngine
from skie_ninja.backtest.leak_canaries import (
    FitCallObserver,
    LookAheadLeakError,
    TracingArray,
    assert_fold_boundary_invariant,
    assert_purge_covers_label_horizon,
)
from skie_ninja.backtest.splits import Fold, SplitSpec, walk_forward_split

# ---------------------------------------------------------------------------
# Canary (a): future-return feature in training row
# ---------------------------------------------------------------------------


class TestFutureReturnFeatureCanary:
    @staticmethod
    def _fold() -> Fold:
        return Fold(
            fold_id=0,
            train_start=0,
            train_end=10,
            test_start=10,
            test_end=15,
            purge_start=10,
            purge_end=10,
            embargo_start=15,
            embargo_end=15,
            train_segments=((0, 10),),
            test_segments=((10, 15),),
        )

    def test_no_leak_passes(self) -> None:
        ts = np.arange(15, dtype=np.int64)
        assert_fold_boundary_invariant(
            self._fold(),
            feature_timestamps=ts,
            observation_timestamps=ts,
        )

    def test_future_feature_in_train_raises(self) -> None:
        """Inject a feature computed from the test region into a
        training row. The invariant must raise."""
        observation_ts = np.arange(15, dtype=np.int64)
        feature_ts = observation_ts.copy()
        # Row 3 is a train row; claim its feature was computed at
        # timestamp 12 (inside the test region). Pure look-ahead.
        feature_ts[3] = 12
        with pytest.raises(LookAheadLeakError, match="leak canary .a."):
            assert_fold_boundary_invariant(
                self._fold(),
                feature_timestamps=feature_ts,
                observation_timestamps=observation_ts,
            )

    def test_equal_to_boundary_raises(self) -> None:
        """Feature timestamp equal to the test-start boundary is a
        leak — it consumed observation 10 which is test row 0."""
        observation_ts = np.arange(15, dtype=np.int64)
        feature_ts = observation_ts.copy()
        feature_ts[5] = 10
        with pytest.raises(LookAheadLeakError):
            assert_fold_boundary_invariant(
                self._fold(),
                feature_timestamps=feature_ts,
                observation_timestamps=observation_ts,
            )

    def test_shape_mismatch_raises_valueerror(self) -> None:
        observation_ts = np.arange(15, dtype=np.int64)
        feature_ts = np.arange(12, dtype=np.int64)
        with pytest.raises(ValueError, match="shape"):
            assert_fold_boundary_invariant(
                self._fold(),
                feature_timestamps=feature_ts,
                observation_timestamps=observation_ts,
            )

    def test_dtype_mismatch_raises_valueerror(self) -> None:
        observation_ts = np.arange(15, dtype=np.int64)
        feature_ts = observation_ts.astype(np.float64)
        with pytest.raises(ValueError, match="dtype"):
            assert_fold_boundary_invariant(
                self._fold(),
                feature_timestamps=feature_ts,
                observation_timestamps=observation_ts,
            )

    def test_engine_halts_on_injected_leak(self) -> None:
        """End-to-end: inject a leaking feature timestamp and confirm
        the engine raises before fit_fn is ever called."""
        spec = walk_forward_split(
            n_samples=40,
            initial_train_size=10,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        ts_obs = np.arange(40, dtype=np.int64)
        ts_feat = ts_obs.copy()
        ts_feat[5] = 50  # training row carrying a far-future timestamp

        fit_called = {"count": 0}

        def fit_fn(train_idx: np.ndarray) -> object:
            fit_called["count"] += 1
            return "model"

        engine = WalkForwardEngine(spec)
        with pytest.raises(LookAheadLeakError):
            engine.run(
                fit_fn=fit_fn,
                feature_timestamps=ts_feat,
                observation_timestamps=ts_obs,
            )
        assert fit_called["count"] == 0


# ---------------------------------------------------------------------------
# Canary (b): label horizon exceeds purge window
# ---------------------------------------------------------------------------


class TestLabelHorizonPurgeCanary:
    def test_direct_helper_passes_when_covered(self) -> None:
        assert_purge_covers_label_horizon(purge_window=5, label_horizon=5)

    def test_direct_helper_raises_when_under_covered(self) -> None:
        with pytest.raises(LookAheadLeakError, match="leak canary .b."):
            assert_purge_covers_label_horizon(purge_window=3, label_horizon=5)

    def test_splitspec_raises_at_construction(self) -> None:
        # Build a fold by-hand so the SplitSpec's own check fires
        # rather than the walk_forward generator's.
        fold = Fold(
            fold_id=0,
            train_start=0,
            train_end=10,
            test_start=10,
            test_end=15,
            purge_start=10,
            purge_end=10,
            embargo_start=15,
            embargo_end=15,
            train_segments=((0, 10),),
            test_segments=((10, 15),),
        )
        with pytest.raises(ValueError, match="leak canary"):
            SplitSpec(
                folds=(fold,),
                n_samples=100,
                label_horizon=5,
                purge_window=2,
                embargo=0,
                scheme="walk_forward_rolling",
            )

    def test_negative_values_rejected(self) -> None:
        with pytest.raises(ValueError, match="purge_window must be >= 0"):
            assert_purge_covers_label_horizon(purge_window=-1, label_horizon=0)
        with pytest.raises(ValueError, match="label_horizon must be >= 0"):
            assert_purge_covers_label_horizon(purge_window=0, label_horizon=-1)


# ---------------------------------------------------------------------------
# Canary (c): fit consumes test-fold observations
# ---------------------------------------------------------------------------


class TestFitCallObserverCanary:
    def test_honest_fit_no_leak(self) -> None:
        fold = Fold(
            fold_id=0,
            train_start=0,
            train_end=10,
            test_start=10,
            test_end=15,
            purge_start=10,
            purge_end=10,
            embargo_start=15,
            embargo_end=15,
            train_segments=((0, 10),),
            test_segments=((10, 15),),
        )

        def fit_fn(train_idx: np.ndarray) -> object:
            return "model"

        observer = FitCallObserver(fit_fn=fit_fn)
        observer(np.asarray(fold.train_indices(), dtype=np.int64))
        assert observer.leaked_positions(fold) == set()

    def test_leaky_fit_caught(self) -> None:
        """Simulate a fit call that peeks at test observations."""
        fold = Fold(
            fold_id=0,
            train_start=0,
            train_end=10,
            test_start=10,
            test_end=15,
            purge_start=10,
            purge_end=10,
            embargo_start=15,
            embargo_end=15,
            train_segments=((0, 10),),
            test_segments=((10, 15),),
        )
        leaky_indices = np.arange(0, 13, dtype=np.int64)  # includes 10, 11, 12

        def fit_fn(train_idx: np.ndarray) -> object:
            return "model"

        observer = FitCallObserver(fit_fn=fit_fn)
        observer(leaky_indices)
        assert observer.leaked_positions(fold) == {10, 11, 12}

    def test_non_monotone_observation_timestamps_raise(self) -> None:
        """Round 1 F-1-3: canary (a)'s scalar boundary comparison is
        only valid on non-decreasing observation timestamps. A
        permuted / session-reset array must surface as ValueError,
        not silently mask a leak."""
        fold = Fold(
            fold_id=0,
            train_start=0,
            train_end=10,
            test_start=10,
            test_end=15,
            purge_start=10,
            purge_end=10,
            embargo_start=15,
            embargo_end=15,
            train_segments=((0, 10),),
            test_segments=((10, 15),),
        )
        observation_ts = np.arange(15, dtype=np.int64)
        observation_ts[7] = 20  # break monotonicity
        with pytest.raises(ValueError, match="monotonically"):
            assert_fold_boundary_invariant(
                fold,
                feature_timestamps=observation_ts,
                observation_timestamps=observation_ts,
            )

    def test_hmm_monkeypatch_integration(self) -> None:
        """End-to-end canary: wrap a ``GaussianHMM.fit`` call with a
        :class:`FitCallObserver`. A mis-implemented fit path that
        slices an observation sequence including test-region positions
        is caught because the observer records exactly which indices
        the (wrapped) fit consumed; intersecting that record with the
        fold's test positions must be non-empty, proving the canary
        fires."""
        from skie_ninja.models.regime.hmm import GaussianHMM

        fold = Fold(
            fold_id=0,
            train_start=0,
            train_end=100,
            test_start=100,
            test_end=130,
            purge_start=100,
            purge_end=100,
            embargo_start=130,
            embargo_end=130,
            train_segments=((0, 100),),
            test_segments=((100, 130),),
        )

        rng = np.random.default_rng(42)
        x = rng.standard_normal((200, 1))

        # The wrapped fit takes the *effective* indices (what the
        # fitter will actually touch) and runs the HMM on that slice.
        # A correctly-implemented harness would pass train-only
        # indices here; a leaky one accidentally passes a wider slice.
        # The observer does not trust the declaration — it records
        # whatever arrived and the test asserts the intersection with
        # the fold's test positions.
        def fit_with_slice(effective_idx: np.ndarray) -> GaussianHMM:
            model = GaussianHMM(n_states=2, covariance_type="diag")
            model.fit(x[effective_idx], seed=0, min_restarts=5, max_restarts=5)
            return model

        observer = FitCallObserver(fit_fn=fit_with_slice)
        # Leaky slice: [0, 120) — 20 test positions leaked in.
        observer(np.arange(0, 120, dtype=np.int64))
        assert observer.leaked_positions(fold) == set(range(100, 120))


# ---------------------------------------------------------------------------
# Canary (c), capability-proxy form: TracingArray catches a fit that
# peeks past its declared train_idx — the attack FitCallObserver alone
# cannot see (Round 1 F-1-1).
# ---------------------------------------------------------------------------


class TestTracingArrayCanary:
    @staticmethod
    def _fold() -> Fold:
        return Fold(
            fold_id=0,
            train_start=0,
            train_end=10,
            test_start=10,
            test_end=15,
            purge_start=10,
            purge_end=10,
            embargo_start=15,
            embargo_end=15,
            train_segments=((0, 10),),
            test_segments=((10, 15),),
        )

    def test_honest_fit_no_leak(self) -> None:
        fold = self._fold()
        x = np.arange(15 * 2, dtype=np.float64).reshape(15, 2)
        traced = TracingArray(x)

        def honest_fit(train_idx: np.ndarray) -> np.ndarray:
            rows = traced[train_idx]
            return rows.mean(axis=0)

        honest_fit(np.arange(10, dtype=np.int64))
        assert traced.leaked_positions(fold) == set()

    def test_internal_peek_is_caught(self) -> None:
        """A fit_fn that IGNORES its declared train_idx and slices
        the full array via a bare `x[:]` is invisible to
        FitCallObserver but must be caught by TracingArray."""
        fold = self._fold()
        x = np.arange(15 * 2, dtype=np.float64).reshape(15, 2)
        traced = TracingArray(x)

        def leaky_fit(train_idx: np.ndarray) -> np.ndarray:
            # The "declared" train_idx is clean [0,10); but the
            # fit secretly reads the whole array, touching the
            # test rows [10,15). FitCallObserver would see only
            # train_idx and miss this.
            rows = traced[:]
            return rows.mean(axis=0)

        observer = FitCallObserver(fit_fn=leaky_fit)
        observer(np.arange(10, dtype=np.int64))
        # FitCallObserver misses it:
        assert observer.leaked_positions(fold) == set()
        # TracingArray catches it:
        assert traced.leaked_positions(fold) == set(range(10, 15))

    def test_integer_fancy_index_journaled(self) -> None:
        fold = self._fold()
        x = np.arange(15, dtype=np.float64)
        traced = TracingArray(x)
        _ = traced[np.array([0, 1, 12, 13], dtype=np.int64)]
        assert traced.leaked_positions(fold) == {12, 13}

    def test_boolean_mask_journaled(self) -> None:
        fold = self._fold()
        x = np.arange(15, dtype=np.float64)
        traced = TracingArray(x)
        mask = np.zeros(15, dtype=bool)
        mask[11] = True
        mask[14] = True
        _ = traced[mask]
        assert traced.leaked_positions(fold) == {11, 14}

    def test_np_asarray_is_conservative(self) -> None:
        """A `np.asarray(traced)` leaks the entire axis-0 — the
        proxy journals the whole range so the canary fires."""
        fold = self._fold()
        x = np.arange(15, dtype=np.float64)
        traced = TracingArray(x)
        _ = np.asarray(traced)
        assert traced.leaked_positions(fold) == set(range(10, 15))

    def test_unsupported_key_raises(self) -> None:
        x = np.arange(15, dtype=np.float64)
        traced = TracingArray(x)
        with pytest.raises(LookAheadLeakError, match="canary .c."):
            _ = traced["a string"]

    def test_mismatched_boolean_mask_raises(self) -> None:
        x = np.arange(15, dtype=np.float64)
        traced = TracingArray(x)
        bad = np.zeros(10, dtype=bool)
        with pytest.raises(LookAheadLeakError, match="boolean mask"):
            _ = traced[bad]
