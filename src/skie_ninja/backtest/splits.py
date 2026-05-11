"""Walk-forward, purged-k-fold, and CPCV split generators.

All splitters operate on *positional* indices (integer row positions
into an ordered observation sequence). Time-based purge / embargo
windows are translated to positions by the caller — a hypothesis
harness mapping timestamps to row positions — and passed to the
splitter as integer counts. This keeps the splitter pure and
serializable; the *reason* purge and embargo exist (label overlap
and forward serial-correlation leakage) is enforced here via
explicit invariants, not via wall-clock arithmetic.

Authoritative sources
---------------------

- **Bergmeir, C., & Benítez, J. M. 2012.** "On the use of
  cross-validation for time series predictor evaluation". *Information
  Sciences* 191: 192-213.
  https://doi.org/10.1016/j.ins.2011.12.028
  Empirically evaluates CV variants on serially dependent
  time-series; the paper's actual recommendation is that **blocked**
  cross-validation is robust for many stationary/weakly-dependent
  ML settings — not that walk-forward strictly dominates k-fold.
  This module implements rolling-/expanding-origin walk-forward as
  one (conservative) instance of that blocked family; the purged
  k-fold and CPCV paths below carry the AFML label-overlap
  safeguards required when forward labels are used. The rolling-
  origin evaluation convention itself traces to Tashman 2000,
  "Out-of-sample tests of forecasting accuracy", *IJF* 16:437-450.

- **López de Prado, M. 2018.** *Advances in Financial Machine
  Learning*. Wiley. Chapter 7 "Cross-Validation in Finance"
  (§7.4.1 "Purging the training set", §7.4.2 "Embargo", §7.4.3
  "The Purged K-Fold Class") and Chapter 12 "Backtesting through
  Cross-Validation" (Combinatorial Purged Cross-Validation).
  Section numbers against the Wiley 2018 edition (ISBN
  978-1-119-48208-6) — Cycle 6 end-to-end review will reconcile
  against a physical copy.
  The purge window is driven by per-observation label horizon; the
  embargo parameter is distinct from the purge and applies only to
  the forward edge of each test fold into any training block that
  follows.

- **Cawley, G. C. & Talbot, N. L. C. 2010.** "On over-fitting in
  model selection and subsequent selection bias in performance
  evaluation". *JMLR* 11: 2079-2107.
  http://jmlr.org/papers/v11/cawley10a.html
  Documents the selection-bias inflation that occurs when a single
  held-out set is used for both hyperparameter tuning and
  performance estimation. Paired with
  **Varma, S. & Simon, R. 2006.** "Bias in error estimation when
  using cross-validation for model selection". *BMC Bioinformatics*
  7:91. https://doi.org/10.1186/1471-2105-7-91 — the canonical
  primary source for the rule that model selection must be
  performed INSIDE the outer fold. The engine consumes this design
  — see :mod:`skie_ninja.backtest.engine.walk_forward`.

Design notes
------------

- **No magic numbers.** Per CLAUDE.md §"Parameter & Prompt Selection",
  ``embargo`` is a caller-supplied integer (may be ``0``, must be
  passed). ``label_horizon`` is required. There is no project-wide
  default — the hypothesis pre-registration is the authoritative
  source.

- **Purge ≥ label horizon.** :meth:`SplitSpec.__post_init__` raises
  at construction time if ``purge_window < label_horizon``. This is
  leak canary (b) per the Cycle-4 spec and is non-negotiable.

- **CPCV status.** Scaffolding lands here because the combinatorial
  traversal fits inside the same :class:`SplitSpec` contract, but
  full path-reconstruction (AFML Chapter 12 "Combinatorial
  backtest paths") is tracked as ``P1-BACKTEST-CPCV``. The H050
  MVP-1 analysis uses purged walk-forward as primary per
  [plan/buildouts/tier2b_buildout_2026-04-23.md](../../plan/buildouts/tier2b_buildout_2026-04-23.md).
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Literal

SplitScheme = Literal[
    "walk_forward_rolling",
    "walk_forward_expanding",
    "purged_kfold",
    "cpcv",
]


@dataclass(frozen=True)
class Fold:
    """Positional boundaries for one fold of a :class:`SplitSpec`.

    All integer fields are row positions into an ordered observation
    sequence of length ``n_samples``. Ranges are **half-open**:
    ``[start, end)``. A zero-width range (``start == end``) is legal
    and indicates the region is absent for this fold (common for
    ``embargo`` on the final rolling fold, where nothing follows the
    test block).

    Fields
    ------
    fold_id
        Zero-indexed fold position. Unique within the parent
        :class:`SplitSpec`.
    train_start, train_end
        The effective training range **after** purge removal. For
        walk-forward schemes the purge carves from the *tail* of the
        contiguous training block; for purged-k-fold and CPCV, the
        training set is the union of multiple ranges — represented
        compactly by carrying ``purge_start`` / ``purge_end`` as the
        single purged interval. Multi-interval training sets use the
        ``train_segments`` field.
    test_start, test_end
        The test range — always a single contiguous half-open interval
        per fold for walk-forward and purged-k-fold. CPCV generalises
        ``test_segments`` similarly to ``train_segments``.
    purge_start, purge_end
        The half-open range removed from the training set to prevent
        label-window overlap into the test fold (AFML §7.4.1).
        Empty when ``purge_window == 0``.
    embargo_start, embargo_end
        The half-open range removed from any *following* training
        block to prevent forward serial-correlation leakage (AFML
        §7.4.2). Empty on the final fold of rolling schemes where no
        subsequent training block exists.
    train_segments, test_segments
        Non-empty tuple of half-open ``(start, end)`` intervals whose
        union is the effective training / test set. For single-block
        schemes both degenerate to ``((train_start, train_end),)``
        and ``((test_start, test_end),)`` respectively; these are
        written explicitly so downstream consumers (the engine, the
        run-ledger) never have to special-case CPCV.
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
    train_segments: tuple[tuple[int, int], ...]
    test_segments: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        # Range well-formedness — positions are non-negative, ranges
        # are half-open (start <= end). Zero-width allowed.
        for name, start, end in (
            ("train", self.train_start, self.train_end),
            ("test", self.test_start, self.test_end),
            ("purge", self.purge_start, self.purge_end),
            ("embargo", self.embargo_start, self.embargo_end),
        ):
            if start < 0 or end < 0 or end < start:
                raise ValueError(
                    f"Fold.{name}_start ({start}) / {name}_end ({end}) "
                    "must satisfy 0 <= start <= end."
                )
        if not self.train_segments:
            raise ValueError("Fold.train_segments must be non-empty.")
        if not self.test_segments:
            raise ValueError("Fold.test_segments must be non-empty.")

        # Segment well-formedness.
        _validate_segments(self.train_segments, "train_segments")
        _validate_segments(self.test_segments, "test_segments")

        # Train and test must be disjoint. This is the first-order
        # leak invariant (a train row that also appears in test is a
        # trivial look-ahead).
        if _segments_overlap(self.train_segments, self.test_segments):
            raise ValueError(
                f"Fold {self.fold_id}: train_segments and test_segments "
                "overlap — this is a direct look-ahead leak."
            )

    @property
    def n_train(self) -> int:
        return sum(end - start for start, end in self.train_segments)

    @property
    def n_test(self) -> int:
        return sum(end - start for start, end in self.test_segments)

    def train_indices(self) -> list[int]:
        """Materialise the effective training positions as a flat list.

        Order is by segment then by position within segment. Callers
        that need ``np.ndarray`` can ``np.asarray(fold.train_indices())``;
        this module keeps a pure-Python return to avoid pulling numpy
        into the splits layer.
        """
        return [i for start, end in self.train_segments for i in range(start, end)]

    def test_indices(self) -> list[int]:
        return [i for start, end in self.test_segments for i in range(start, end)]


@dataclass(frozen=True)
class SplitSpec:
    """Ordered collection of folds plus global-invariant metadata.

    Constructor-level invariants (``__post_init__``):

    1. ``purge_window >= label_horizon`` — leak canary (b). If the
       caller's label-closure horizon exceeds the purge window, AFML
       §7.4.1's purge is insufficient and training labels will overlap
       the test region. Raised as :class:`ValueError`.
    2. ``embargo >= 0`` — negative embargo is nonsense. Zero is legal
       but must be passed explicitly by the caller (CLAUDE.md
       §"Parameter & Prompt Selection").
    3. ``n_samples > 0`` and each fold's boundaries lie within
       ``[0, n_samples)``.
    4. Fold ids are contiguous ``0..len(folds)-1``.
    """

    folds: tuple[Fold, ...]
    n_samples: int
    label_horizon: int
    purge_window: int
    embargo: int
    scheme: SplitScheme

    def __post_init__(self) -> None:
        if self.n_samples <= 0:
            raise ValueError(f"n_samples must be > 0; got {self.n_samples}.")
        if self.label_horizon < 0:
            raise ValueError(
                f"label_horizon must be >= 0; got {self.label_horizon}. "
                "The caller is required to pre-register this value per "
                "CLAUDE.md §'Parameter & Prompt Selection'."
            )
        if self.embargo < 0:
            raise ValueError(
                f"embargo must be >= 0; got {self.embargo}. Zero is legal "
                "but must be passed explicitly by the caller."
            )
        if self.purge_window < 0:
            raise ValueError(
                f"purge_window must be >= 0; got {self.purge_window}."
            )
        # Leak canary (b): purge must cover the label horizon.
        if self.purge_window < self.label_horizon:
            raise ValueError(
                f"purge_window ({self.purge_window}) < label_horizon "
                f"({self.label_horizon}). AFML §7.4.1 requires the purge "
                "window to fully contain the label closure horizon, else "
                "training labels overlap the test region. This is leak "
                "canary (b)."
            )
        if not self.folds:
            raise ValueError("SplitSpec.folds must be non-empty.")
        for expected_id, fold in enumerate(self.folds):
            if fold.fold_id != expected_id:
                raise ValueError(
                    f"SplitSpec.folds[{expected_id}].fold_id = "
                    f"{fold.fold_id}; expected {expected_id}."
                )
            _check_fold_within_bounds(fold, self.n_samples)


# ---------------------------------------------------------------------------
# Walk-forward
# ---------------------------------------------------------------------------


def walk_forward_split(
    *,
    n_samples: int,
    initial_train_size: int,
    test_size: int,
    step_size: int,
    label_horizon: int,
    embargo: int,
    mode: Literal["rolling", "expanding"] = "rolling",
    purge_window: int | None = None,
    max_folds: int | None = None,
) -> SplitSpec:
    """Construct a rolling- or expanding-origin walk-forward split.

    Bergmeir-Benítez 2012 argues that time-ordered rolling-origin
    evaluation dominates random k-fold when the series is serially
    correlated. This function implements both the rolling and
    expanding variants; AFML §7.4 purge+embargo semantics are layered
    on top so that label overlap and serial-correlation leakage are
    suppressed.

    Parameters
    ----------
    n_samples
        Length of the ordered observation sequence.
    initial_train_size
        Number of observations in the first training block.
    test_size
        Number of observations in each test block.
    step_size
        Distance the walking origin advances between folds. Typically
        equal to ``test_size`` (disjoint test blocks) but callers may
        pre-register overlapping or sparser schedules; overlapping
        test blocks fail the :class:`Fold` disjoint-segments invariant
        via the engine-level check, not here.
    label_horizon
        Maximum number of future positions consumed by any single
        observation's label (e.g., a 5-bar forward return has
        ``label_horizon = 5``). Must satisfy
        ``label_horizon <= purge_window`` (default
        ``purge_window = label_horizon``).
    embargo
        Number of positions after the test block's trailing edge that
        must be excluded from any subsequent training block. AFML
        §7.4.2. Required — callers pass ``0`` explicitly to disable.
    mode
        ``"rolling"`` — training block slides forward with the origin;
        ``"expanding"`` — training block grows (start anchored at 0).
    purge_window
        Positions removed from the tail of the training block to
        suppress label overlap. Defaults to ``label_horizon``.
    max_folds
        Optional cap on number of folds generated; ``None`` means fill
        the available span. Useful for test suites that need a
        predictable fold count.
    """
    _require_positive(initial_train_size, "initial_train_size")
    _require_positive(test_size, "test_size")
    _require_positive(step_size, "step_size")
    if n_samples <= 0:
        raise ValueError(f"n_samples must be > 0; got {n_samples}.")

    resolved_purge = label_horizon if purge_window is None else purge_window

    folds: list[Fold] = []
    origin = initial_train_size
    fold_id = 0
    while origin + test_size <= n_samples:
        test_start = origin
        test_end = origin + test_size
        if mode == "rolling":
            raw_train_start = origin - initial_train_size
        elif mode == "expanding":
            raw_train_start = 0
        else:
            raise ValueError(
                f"mode must be 'rolling' or 'expanding'; got {mode!r}."
            )
        raw_train_end = origin  # [raw_train_start, raw_train_end) pre-purge

        # Purge: remove the last `resolved_purge` positions of the
        # training block. The purge region is
        # [purge_start, purge_end) = [raw_train_end - resolved_purge, raw_train_end).
        purge_start = max(raw_train_start, raw_train_end - resolved_purge)
        purge_end = raw_train_end
        effective_train_end = purge_start
        if effective_train_end <= raw_train_start:
            # The entire training block is purged — abandon this fold;
            # the harness cannot learn from zero observations. We
            # stop generation rather than silently emit a degenerate
            # fold, because this is usually a mis-configuration.
            raise ValueError(
                f"Fold {fold_id}: purge_window ({resolved_purge}) >= "
                f"training block size ({raw_train_end - raw_train_start}). "
                "Either reduce label_horizon or grow initial_train_size."
            )

        # Embargo boundaries are recorded for the run-ledger even
        # though in walk-forward the embargo affects the *next* fold's
        # training block; the engine applies it at fold iteration.
        embargo_start = test_end
        embargo_end = min(test_end + embargo, n_samples)

        folds.append(
            Fold(
                fold_id=fold_id,
                train_start=raw_train_start,
                train_end=effective_train_end,
                test_start=test_start,
                test_end=test_end,
                purge_start=purge_start,
                purge_end=purge_end,
                embargo_start=embargo_start,
                embargo_end=embargo_end,
                train_segments=((raw_train_start, effective_train_end),),
                test_segments=((test_start, test_end),),
            )
        )
        fold_id += 1
        if max_folds is not None and fold_id >= max_folds:
            break
        origin += step_size

    if not folds:
        raise ValueError(
            "walk_forward_split produced zero folds. Check that "
            f"initial_train_size ({initial_train_size}) + test_size "
            f"({test_size}) <= n_samples ({n_samples})."
        )

    # Apply embargo to subsequent training blocks, in-place over a
    # local copy (Fold is frozen). The embargo from fold k carves into
    # the leading edge of fold k+1's training block and onward within
    # its reach. Walk-forward rolling blocks are contiguous and
    # sequential, so only the immediate next fold's training can be
    # affected (unless step_size < test_size, which is a pre-registered
    # overlap case).
    embargoed = _apply_embargo_walk_forward(folds, embargo=embargo)

    scheme: SplitScheme = (
        "walk_forward_rolling" if mode == "rolling" else "walk_forward_expanding"
    )
    return SplitSpec(
        folds=tuple(embargoed),
        n_samples=n_samples,
        label_horizon=label_horizon,
        purge_window=resolved_purge,
        embargo=embargo,
        scheme=scheme,
    )


def _apply_embargo_walk_forward(
    folds: list[Fold], *, embargo: int
) -> list[Fold]:
    """Rewrite each fold's training segments to exclude the
    *immediately prior* fold's embargo region.

    AFML §7.4.2's embargo is defined per test set: ``h`` positions
    immediately after THIS fold's test block are excluded from any
    training observation that would otherwise follow. In a pure
    walk-forward scheme with ``step_size == test_size``, training
    sits strictly before the test block, so a fold's own embargo
    cannot affect its own training. It affects the next fold, when
    the next fold's (rolling) training window extends forward into
    the embargo band of its predecessor.

    An earlier implementation accumulated embargo ranges from all
    *prior* folds into every subsequent fold's training — a
    methodological over-reach per the Round 1 quant-auditor finding
    F-1-4: fold 0's embargo is about serial correlation between
    fold 0's test and observations that follow fold 0's test; it is
    not relevant to fold 2's test region several folds downstream.
    The corrected behaviour is to carry forward only the
    immediately prior fold's embargo band.
    """
    if embargo <= 0:
        return folds

    out: list[Fold] = []
    prior_embargo: tuple[int, int] | None = None
    for fold in folds:
        if prior_embargo is not None:
            prior_start, prior_end = prior_embargo
            if prior_end > prior_start:
                new_segments = _subtract_ranges(
                    fold.train_segments, [prior_embargo]
                )
            else:
                new_segments = list(fold.train_segments)
            if not new_segments:
                raise ValueError(
                    f"Fold {fold.fold_id}: embargo removed the entire "
                    "training set. Either reduce embargo or grow "
                    "initial_train_size."
                )
            first_start = new_segments[0][0]
            last_end = new_segments[-1][1]
            out.append(
                Fold(
                    fold_id=fold.fold_id,
                    train_start=first_start,
                    train_end=last_end,
                    test_start=fold.test_start,
                    test_end=fold.test_end,
                    purge_start=fold.purge_start,
                    purge_end=fold.purge_end,
                    embargo_start=fold.embargo_start,
                    embargo_end=fold.embargo_end,
                    train_segments=tuple(new_segments),
                    test_segments=fold.test_segments,
                )
            )
        else:
            out.append(fold)
        prior_embargo = (fold.embargo_start, fold.embargo_end)
    return out


# ---------------------------------------------------------------------------
# Purged K-Fold (AFML §7.4.3)
# ---------------------------------------------------------------------------


def purged_kfold_split(
    *,
    n_samples: int,
    n_splits: int,
    label_horizon: int,
    embargo: int,
    purge_window: int | None = None,
) -> SplitSpec:
    """AFML §7.4.3 Purged K-Fold.

    The observation sequence is cut into ``n_splits`` contiguous
    blocks of (nearly) equal size. Fold k uses block k as the test
    set; the training set is the union of all other blocks, minus a
    purge band of width ``purge_window`` on **both edges** of the
    test block, plus an embargo band of width ``embargo`` on the
    *trailing* edge of the test block (the leading edge does not
    need embargo because there is no forward-looking feature into
    the past — the purge handles the label-horizon side).

    Parameters mirror :func:`walk_forward_split` where relevant.
    """
    _require_positive(n_splits, "n_splits")
    if n_splits < 2:
        raise ValueError(
            f"n_splits must be >= 2 for k-fold (got {n_splits}); use "
            "walk_forward_split for a single train/test cut."
        )
    if n_samples < n_splits:
        raise ValueError(
            f"n_samples ({n_samples}) < n_splits ({n_splits})."
        )

    resolved_purge = label_horizon if purge_window is None else purge_window

    # Block boundaries: even-partition with the remainder distributed
    # to the earliest blocks. np.array_split-style but pure Python.
    base = n_samples // n_splits
    rem = n_samples % n_splits
    boundaries: list[tuple[int, int]] = []
    cursor = 0
    for k in range(n_splits):
        width = base + (1 if k < rem else 0)
        boundaries.append((cursor, cursor + width))
        cursor += width

    folds: list[Fold] = []
    for k, (b_start, b_end) in enumerate(boundaries):
        test_segments: tuple[tuple[int, int], ...] = ((b_start, b_end),)

        # Purge on both sides of the test block, then embargo beyond
        # the trailing purge — matching the reference implementation
        # `mlfinlab.cross_validation.ml_get_train_times`, whose
        # construction extends the test interval's right edge by
        # `embargo` before applying the label-horizon purge so the
        # total trailing excluded band is
        # `[b_end, b_end + purge + embargo)`. See mlfinlab 1.6.0
        # `ml_get_train_times` and López de Prado 2018 Snippet 7.3.
        # Round-2 F-2-1 refactored this back from an earlier
        # overlap-style placement — the stacked form is what
        # downstream CPCV + PBO tooling in the sibling SKIE_Ninja
        # research repo consumes.
        excluded_from_train: list[tuple[int, int]] = [
            (max(0, b_start - resolved_purge), b_start),
            (b_end, min(n_samples, b_end + resolved_purge)),
        ]
        if embargo > 0:
            excluded_from_train.append(
                (
                    b_end + resolved_purge,
                    min(n_samples, b_end + resolved_purge + embargo),
                )
            )

        train_segments = _subtract_ranges(
            ((0, n_samples),),
            excluded_from_train + [(b_start, b_end)],
        )
        if not train_segments:
            raise ValueError(
                f"purged_kfold_split fold {k}: no training observations "
                "remain after purge+embargo. Reduce n_splits or purge_window."
            )

        # Compact single-interval purge for the run-ledger: we store
        # the *wider* side (the two purges may differ by one on the
        # boundary; picking the leading purge is canonical).
        purge_start = excluded_from_train[0][0]
        purge_end = excluded_from_train[0][1]
        # Embargo band sits past the trailing purge, per mlfinlab.
        # Clamp to `[0, n_samples]` so tail blocks don't produce
        # start > end.
        embargo_start = min(n_samples, b_end + resolved_purge)
        embargo_end = min(n_samples, b_end + resolved_purge + embargo)

        first_start = train_segments[0][0]
        last_end = train_segments[-1][1]

        folds.append(
            Fold(
                fold_id=k,
                train_start=first_start,
                train_end=last_end,
                test_start=b_start,
                test_end=b_end,
                purge_start=purge_start,
                purge_end=purge_end,
                embargo_start=embargo_start,
                embargo_end=embargo_end,
                train_segments=tuple(train_segments),
                test_segments=test_segments,
            )
        )

    return SplitSpec(
        folds=tuple(folds),
        n_samples=n_samples,
        label_horizon=label_horizon,
        purge_window=resolved_purge,
        embargo=embargo,
        scheme="purged_kfold",
    )


# ---------------------------------------------------------------------------
# Combinatorial Purged CV — AFML Chapter 12 (SCAFFOLD)
# ---------------------------------------------------------------------------


def cpcv_split(
    *,
    n_samples: int,
    n_groups: int,
    n_test_groups: int,
    label_horizon: int,
    embargo: int,
    purge_window: int | None = None,
) -> SplitSpec:
    """Combinatorial Purged Cross-Validation (AFML Chapter 12) — scaffold.

    Partitions the sequence into ``n_groups`` contiguous blocks and
    generates every ``C(n_groups, n_test_groups)`` choice of test
    blocks. For each combination, the training set is the union of
    the remaining blocks, minus purge and embargo bands adjacent to
    *each* test block.

    Path reconstruction (AFML Chapter 12's main output — per-path backtest
    sequences that average out block-selection noise) is **not**
    implemented here; that is tracked as ``P1-BACKTEST-CPCV``. The
    MVP-1 H050 run uses purged walk-forward as primary, per
    [plan/buildouts/tier2b_buildout_2026-04-23.md](../../plan/buildouts/tier2b_buildout_2026-04-23.md).
    """
    _require_positive(n_groups, "n_groups")
    _require_positive(n_test_groups, "n_test_groups")
    if n_test_groups >= n_groups:
        raise ValueError(
            f"n_test_groups ({n_test_groups}) must be < n_groups "
            f"({n_groups}); otherwise the training set is empty."
        )
    if n_samples < n_groups:
        raise ValueError(
            f"n_samples ({n_samples}) < n_groups ({n_groups})."
        )

    resolved_purge = label_horizon if purge_window is None else purge_window

    base = n_samples // n_groups
    rem = n_samples % n_groups
    group_bounds: list[tuple[int, int]] = []
    cursor = 0
    for k in range(n_groups):
        width = base + (1 if k < rem else 0)
        group_bounds.append((cursor, cursor + width))
        cursor += width

    folds: list[Fold] = []
    fold_id = 0
    for combo in itertools.combinations(range(n_groups), n_test_groups):
        test_blocks = [group_bounds[k] for k in combo]
        # Purge + embargo bands around each test block. Embargo
        # sits past the trailing purge per mlfinlab
        # `ml_get_train_times` (see note in :func:`purged_kfold_split`).
        excluded: list[tuple[int, int]] = []
        for b_start, b_end in test_blocks:
            excluded.append(
                (max(0, b_start - resolved_purge), b_start)
            )
            excluded.append(
                (b_end, min(n_samples, b_end + resolved_purge))
            )
            if embargo > 0:
                excluded.append(
                    (
                        b_end + resolved_purge,
                        min(n_samples, b_end + resolved_purge + embargo),
                    )
                )

        test_segments = _union_ranges(test_blocks)
        train_segments = _subtract_ranges(
            ((0, n_samples),),
            list(test_segments) + excluded,
        )
        if not train_segments:
            continue  # combination exhausted the training set; skip

        # Canonical single-interval purge for run-ledger: first block's
        # leading purge.
        first_test_start = test_segments[0][0]
        last_test_end = test_segments[-1][1]
        purge_start = max(0, first_test_start - resolved_purge)
        purge_end = first_test_start
        embargo_start = min(n_samples, last_test_end + resolved_purge)
        embargo_end = min(n_samples, last_test_end + resolved_purge + embargo)

        first_train_start = train_segments[0][0]
        last_train_end = train_segments[-1][1]

        folds.append(
            Fold(
                fold_id=fold_id,
                train_start=first_train_start,
                train_end=last_train_end,
                test_start=first_test_start,
                test_end=last_test_end,
                purge_start=purge_start,
                purge_end=purge_end,
                embargo_start=embargo_start,
                embargo_end=embargo_end,
                train_segments=tuple(train_segments),
                test_segments=tuple(test_segments),
            )
        )
        fold_id += 1

    if not folds:
        raise ValueError(
            "cpcv_split produced zero folds. Check n_groups / n_test_groups "
            "against the purge/embargo budget."
        )

    return SplitSpec(
        folds=tuple(folds),
        n_samples=n_samples,
        label_horizon=label_horizon,
        purge_window=resolved_purge,
        embargo=embargo,
        scheme="cpcv",
    )


def cpcv_combination_count(n_groups: int, n_test_groups: int) -> int:
    """Expected number of combinations for :func:`cpcv_split`.

    Matches ``math.comb(n_groups, n_test_groups)``; exported as a
    named helper so test suites can assert coverage without reaching
    into ``math`` directly.
    """
    return math.comb(n_groups, n_test_groups)


# ---------------------------------------------------------------------------
# Range arithmetic helpers
# ---------------------------------------------------------------------------


def _validate_segments(segments: tuple[tuple[int, int], ...], name: str) -> None:
    prev_end: int | None = None
    for start, end in segments:
        if start < 0 or end < start:
            raise ValueError(
                f"Fold.{name} contains malformed range ({start}, {end})."
            )
        if prev_end is not None and start < prev_end:
            raise ValueError(
                f"Fold.{name} must be sorted and non-overlapping; "
                f"got {segments!r}."
            )
        prev_end = end


def _segments_overlap(
    a: tuple[tuple[int, int], ...],
    b: tuple[tuple[int, int], ...],
) -> bool:
    for a_start, a_end in a:
        for b_start, b_end in b:
            if a_start < b_end and b_start < a_end:
                return True
    return False


def _union_ranges(
    ranges: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Return the sorted union of half-open ranges, merging overlaps."""
    valid = [(s, e) for s, e in ranges if e > s]
    if not valid:
        return []
    valid.sort()
    out: list[tuple[int, int]] = [valid[0]]
    for start, end in valid[1:]:
        last_start, last_end = out[-1]
        if start <= last_end:
            out[-1] = (last_start, max(last_end, end))
        else:
            out.append((start, end))
    return out


def _subtract_ranges(
    base: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    removals: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Subtract the union of ``removals`` from each segment of ``base``.

    Runs O(n log n) for ``n = len(base) + len(removals)`` via sorted
    sweep. Returns a list of half-open ranges; empty if everything
    was removed.
    """
    removals_union = _union_ranges(list(removals))
    out: list[tuple[int, int]] = []
    for start, end in base:
        cur = start
        for r_start, r_end in removals_union:
            if r_end <= cur:
                continue
            if r_start >= end:
                break
            if r_start > cur:
                out.append((cur, min(r_start, end)))
            cur = max(cur, r_end)
            if cur >= end:
                break
        if cur < end:
            out.append((cur, end))
    return [(s, e) for s, e in out if e > s]


def _check_fold_within_bounds(fold: Fold, n_samples: int) -> None:
    for name, seg in (("train", fold.train_segments), ("test", fold.test_segments)):
        for start, end in seg:
            if start < 0 or end > n_samples:
                raise ValueError(
                    f"Fold {fold.fold_id}: {name} segment ({start}, {end}) "
                    f"out of bounds for n_samples={n_samples}."
                )


def _require_positive(value: int, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be > 0; got {value}.")
