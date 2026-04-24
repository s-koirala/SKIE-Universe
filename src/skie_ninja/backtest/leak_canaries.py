"""Leak-canary suite for the walk-forward engine.

Three adversarial scenarios from the Cycle-4 specification:

  (a) **Future-return feature in a training row.** A row's
      ``feature_timestamp`` exceeds the test-fold start boundary —
      the feature was computed using information unavailable at the
      training cutoff. Caught by
      :func:`assert_fold_boundary_invariant`, called by the engine
      before each fold's ``fit_fn`` invocation.

  (b) **Label horizon exceeds purge window.** Detected at
      :class:`skie_ninja.backtest.splits.SplitSpec` construction
      (see ``SplitSpec.__post_init__`` in
      [src/skie_ninja/backtest/splits.py](splits.py)). Mirrored here
      via :func:`assert_purge_covers_label_horizon` so unit tests can
      exercise the invariant directly without constructing a full
      :class:`SplitSpec`.

  (c) **HMM fit consumes test-fold observations.** Caught by
      :class:`FitCallObserver`, a decorator wrapping a ``fit_fn``
      that records exactly which row positions were passed in. The
      integration test that monkey-patches an HMM's ``fit`` asserts
      the observed positions are a subset of the fold's train
      positions.

A dead canary — one that silently passes when the leak is injected —
is a failed cycle per the spec. Every canary here has a matching
unit test in [tests/unit/test_leak_canaries.py](../../tests/unit/test_leak_canaries.py)
that injects the leak and asserts the detector raises.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from skie_ninja.backtest.splits import Fold


class LookAheadLeakError(AssertionError):
    """Raised when a look-ahead invariant fails.

    Subclasses :class:`AssertionError` so existing pytest-style guards
    still surface, but the distinct type lets engine-level handlers
    distinguish a leak from an unrelated assertion.
    """


def assert_fold_boundary_invariant(
    fold: Fold,
    *,
    feature_timestamps: np.ndarray,
    observation_timestamps: np.ndarray,
) -> None:
    """Leak canary (a): feature-timestamp ≤ fold-boundary.

    ``feature_timestamps[i]`` is the wall-clock time at which row
    ``i``'s feature became computable (for forward-shift features,
    this is the close of the lookahead window; for same-bar features
    it equals ``observation_timestamps[i]``).

    The invariant: every row in the *training* fold has
    ``feature_timestamps[i] < observation_timestamps[test_start]``,
    i.e. the feature was computable strictly before the test region
    begins. Equality with the boundary is forbidden because a feature
    closing exactly at the boundary has consumed an observation from
    the test fold.

    Parameters
    ----------
    fold
        The fold whose training rows are to be checked.
    feature_timestamps, observation_timestamps
        One-dimensional arrays of length ``n_samples`` containing
        comparable timestamps. Typically ``int64`` nanoseconds or
        float seconds; any strict-total-order dtype works. Both
        arrays must share dtype and length.

    Raises
    ------
    LookAheadLeakError
        If any training-row feature timestamp is at or after the
        test region's start timestamp.
    ValueError
        On shape / dtype mismatch.
    """
    if feature_timestamps.shape != observation_timestamps.shape:
        raise ValueError(
            f"feature_timestamps.shape {feature_timestamps.shape} != "
            f"observation_timestamps.shape {observation_timestamps.shape}."
        )
    if feature_timestamps.ndim != 1:
        raise ValueError(
            f"feature_timestamps must be 1-D; got ndim={feature_timestamps.ndim}."
        )
    if feature_timestamps.dtype != observation_timestamps.dtype:
        raise ValueError(
            f"feature_timestamps.dtype {feature_timestamps.dtype} != "
            f"observation_timestamps.dtype {observation_timestamps.dtype}."
        )
    # The scalar boundary `observation_timestamps[test_idx.min()]`
    # only makes sense if observation timestamps are non-decreasing.
    # A permuted or session-reset array (e.g., concatenated RTH/ETH
    # blocks whose timestamps wrap) would render the comparison
    # meaningless. Enforce monotonicity explicitly so misuse surfaces
    # here rather than silently passing a leak through.
    if observation_timestamps.size > 1 and not np.all(
        np.diff(observation_timestamps) >= 0
    ):
        raise ValueError(
            "observation_timestamps must be monotonically non-decreasing; "
            "canary (a)'s scalar boundary comparison is only valid against "
            "an ordered series. Sort the observation array or partition "
            "the sessions (see CLAUDE.md §Session policy) before calling."
        )

    train_idx = np.asarray(fold.train_indices(), dtype=np.int64)
    if train_idx.size == 0:
        return  # empty training fold — vacuously safe
    test_idx = np.asarray(fold.test_indices(), dtype=np.int64)
    if test_idx.size == 0:
        raise ValueError(
            f"Fold {fold.fold_id} has no test observations; engine "
            "should not reach the invariant check."
        )

    boundary = observation_timestamps[test_idx.min()]
    violating = feature_timestamps[train_idx] >= boundary
    if violating.any():
        n_bad = int(violating.sum())
        first_bad_train_pos = int(train_idx[np.argmax(violating)])
        raise LookAheadLeakError(
            f"Fold {fold.fold_id}: {n_bad} training row(s) have "
            f"feature_timestamp >= test-region start "
            f"(first offender: train_idx={first_bad_train_pos}, "
            f"feature_ts={feature_timestamps[first_bad_train_pos]!r}, "
            f"boundary={boundary!r}). This is leak canary (a) per "
            "src/skie_ninja/backtest/leak_canaries.py."
        )


def assert_purge_covers_label_horizon(
    *, purge_window: int, label_horizon: int
) -> None:
    """Leak canary (b): purge ≥ label horizon (AFML §7.4.1).

    Mirrors :class:`SplitSpec` construction-time invariant so tests
    can exercise the boundary without building a full
    :class:`SplitSpec`.
    """
    if purge_window < 0:
        raise ValueError(f"purge_window must be >= 0; got {purge_window}.")
    if label_horizon < 0:
        raise ValueError(f"label_horizon must be >= 0; got {label_horizon}.")
    if purge_window < label_horizon:
        raise LookAheadLeakError(
            f"purge_window ({purge_window}) < label_horizon "
            f"({label_horizon}). AFML §7.4.1 requires purge to cover "
            "the full label closure horizon. This is leak canary (b)."
        )


@dataclass
class FitCallObserver:
    """Leak canary (c), declared-index form: record row positions
    passed to a ``fit_fn`` and assert they don't overlap the test
    fold.

    Wraps a user-supplied ``fit_fn`` and journals every integer
    position that arrives as its first positional argument. A
    test-fold leak is declared by checking
    :meth:`leaked_positions` against a :class:`Fold`.

    **Scope and limitation.** ``FitCallObserver`` only sees the
    indices the caller *hands to* ``fit_fn``. If ``fit_fn`` closes
    over a module-scoped feature matrix, or a helper inside
    ``fit_fn`` reaches past the provided indices, this observer is
    silent. To detect that stronger leak mode — data reads that
    bypass the declared index set — use :class:`TracingArray`: wrap
    the feature array once and pass the proxy into ``fit_fn`` via
    ``fit_kwargs``; its journal records every ``__getitem__`` access
    and :meth:`TracingArray.leaked_positions` catches internal peeks.

    Usage
    -----
    >>> observer = FitCallObserver(fit_fn=real_fit)
    >>> model = observer(train_idx, X)
    >>> assert observer.leaked_positions(fold) == set()
    """

    fit_fn: Any
    observed_positions: list[int] = field(default_factory=list)

    def __call__(self, train_idx: np.ndarray, *args: Any, **kwargs: Any) -> Any:
        self.observed_positions.extend(int(i) for i in np.asarray(train_idx))
        return self.fit_fn(train_idx, *args, **kwargs)

    def leaked_positions(self, fold: Fold) -> set[int]:
        """Return the intersection of ``observed_positions`` with the
        fold's *test* positions.

        A non-empty return is a leak. The engine-level integration
        test monkey-patches the HMM fit callable with a ``FitCallObserver``
        and asserts this returns the empty set.
        """
        test_positions = set(fold.test_indices())
        observed = set(self.observed_positions)
        return observed & test_positions


class TracingArray:
    """Leak canary (c), capability-proxy form: a numpy-array wrapper
    that journals every positional read.

    Motivating attack model: a ``fit_fn`` that *claims* to honour its
    ``train_idx`` argument but internally slices the underlying
    feature array by a different range — e.g., ``x[:]``,
    ``x[:test_end]``, or a module-level alias. :class:`FitCallObserver`
    cannot detect this because the declared ``train_idx`` looks
    clean. :class:`TracingArray` catches it by recording every
    integer position that passes through ``__getitem__``, regardless
    of how the caller obtained it.

    Threat model
    ------------
    The canary defends against *honest-but-bug-prone* ``fit_fn``
    implementations that accidentally read past their declared
    indices. It does NOT defend against an adversarial caller that
    extracts the underlying array via attribute access — the raw
    array is held in a single-underscore ``_array`` field as a
    convention-only private; nothing in Python prevents
    ``traced._array[:]`` from bypassing the journal. Per
    [Round 2 F-2-2](docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md)
    this is documented as out-of-scope; the Cycle-4 contract is
    mis-use detection, not sandboxing.

    Only one-dimensional reads are journaled explicitly; slices and
    advanced integer indexing along axis 0 are normalised to the
    equivalent set of positions. Boolean-mask reads and multi-axis
    fancy indexing fall back to journaling only the rows they
    touch (via ``np.nonzero`` for the boolean case); reads that
    cannot be resolved to a concrete set of axis-0 positions raise
    :class:`LookAheadLeakError` — the canary is deliberately
    conservative because silent failure is the failure mode the
    Cycle-4 spec rejects as a "dead canary".

    Usage
    -----
    >>> traced = TracingArray(np.asarray(features))
    >>> model = fit_fn(train_idx, x=traced)
    >>> assert traced.leaked_positions(fold) == set()
    """

    __slots__ = ("_array", "observed_positions")

    def __init__(self, array: np.ndarray) -> None:
        self._array = np.asarray(array)
        self.observed_positions: list[int] = []

    @property
    def shape(self) -> tuple[int, ...]:
        return self._array.shape

    @property
    def dtype(self) -> np.dtype[Any]:
        return self._array.dtype

    @property
    def ndim(self) -> int:
        return self._array.ndim

    def __len__(self) -> int:
        return int(self._array.shape[0])

    def __array__(
        self, dtype: Any = None, copy: bool | None = None
    ) -> np.ndarray:
        # A bare ``np.asarray(traced)`` leaks the entire axis-0 range.
        # Journal it conservatively — the whole axis becomes observed.
        # ``copy`` was added by NumPy 2.0 (NEP 51); accept it so
        # callers on numpy>=2 don't trip a TypeError masking the
        # journal event.
        self.observed_positions.extend(range(self._array.shape[0]))
        base = self._array if dtype is None else self._array.astype(dtype)
        if copy is True:
            return base.copy()
        return base

    def __getitem__(self, key: Any) -> np.ndarray:
        positions = self._positions_for_key(key)
        self.observed_positions.extend(positions)
        return self._array[key]

    def _positions_for_key(self, key: Any) -> list[int]:
        n = self._array.shape[0]
        # Multi-axis key: the first axis is what controls leakage into
        # rows; deeper axes are column-style reads that do not expose
        # unseen rows. Only the axis-0 component is journaled.
        if isinstance(key, tuple):
            if not key:
                return list(range(n))
            first = key[0]
            return self._positions_for_single_axis(first, n)
        return self._positions_for_single_axis(key, n)

    def _positions_for_single_axis(self, key: Any, n: int) -> list[int]:
        if isinstance(key, slice):
            return list(range(*key.indices(n)))
        if isinstance(key, (int, np.integer)):
            idx = int(key)
            if idx < 0:
                idx += n
            return [idx]
        if isinstance(key, np.ndarray):
            if key.dtype == np.bool_:
                if key.shape[0] != n:
                    raise LookAheadLeakError(
                        f"TracingArray boolean mask length {key.shape[0]} "
                        f"!= axis-0 length {n}; refusing to silently "
                        "drop positions (canary (c))."
                    )
                return np.nonzero(key)[0].astype(int).tolist()
            if np.issubdtype(key.dtype, np.integer):
                return [int(i) + (n if int(i) < 0 else 0) for i in key.ravel()]
        if isinstance(key, list):
            return self._positions_for_single_axis(np.asarray(key), n)
        if key is Ellipsis or key is None:
            return list(range(n))
        raise LookAheadLeakError(
            f"TracingArray: unsupported index key {key!r}; refusing to "
            "accept an index whose positional footprint cannot be "
            "resolved (canary (c) must not fail silent)."
        )

    def leaked_positions(self, fold: Fold) -> set[int]:
        """Return the intersection of observed positions with the
        fold's *test* positions. Non-empty == leak."""
        test_positions = set(fold.test_indices())
        return set(self.observed_positions) & test_positions
