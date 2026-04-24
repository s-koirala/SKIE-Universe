"""Unit tests for :mod:`skie_ninja.backtest.splits`.

Covers:

- Walk-forward rolling / expanding fold-boundary arithmetic.
- Purge window ≥ label horizon enforcement (leak canary (b) at the
  :class:`SplitSpec` layer).
- Embargo applied to subsequent training blocks; zero-embargo legal.
- Purged k-fold (AFML §7.4.3) both-sides purge + forward-only embargo.
- CPCV combination count and at-least-one-fold production.
- Range arithmetic helpers.
"""

from __future__ import annotations

import math

import pytest

from skie_ninja.backtest.splits import (
    Fold,
    SplitSpec,
    _subtract_ranges,
    _union_ranges,
    cpcv_combination_count,
    cpcv_split,
    purged_kfold_split,
    walk_forward_split,
)

# ---------------------------------------------------------------------------
# Walk-forward rolling
# ---------------------------------------------------------------------------


class TestWalkForwardRolling:
    def test_rolling_basic_shape(self) -> None:
        spec = walk_forward_split(
            n_samples=100,
            initial_train_size=40,
            test_size=10,
            step_size=10,
            label_horizon=2,
            embargo=0,
            mode="rolling",
        )
        assert spec.scheme == "walk_forward_rolling"
        # origins at 40, 50, 60, 70, 80, 90 — 6 folds since 90+10 <= 100.
        assert len(spec.folds) == 6
        for fold in spec.folds:
            assert fold.test_end - fold.test_start == 10
            # train block contiguous (single segment before embargo
            # surgery; embargo=0 here so still one segment).
            assert len(fold.train_segments) == 1

    def test_rolling_train_block_rolls_with_origin(self) -> None:
        spec = walk_forward_split(
            n_samples=60,
            initial_train_size=20,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
            mode="rolling",
        )
        # Fold 0: train [0,20), test [20,25); Fold 1: train [5,25), test [25,30)
        assert spec.folds[0].train_start == 0
        assert spec.folds[0].train_end == 20
        assert spec.folds[1].train_start == 5
        assert spec.folds[1].train_end == 25

    def test_rolling_purge_removes_tail_of_train(self) -> None:
        spec = walk_forward_split(
            n_samples=60,
            initial_train_size=20,
            test_size=5,
            step_size=5,
            label_horizon=3,
            embargo=0,
            mode="rolling",
        )
        fold0 = spec.folds[0]
        assert fold0.train_start == 0
        # Purge removes last 3 positions of [0,20) → effective [0,17).
        assert fold0.train_end == 17
        assert fold0.purge_start == 17
        assert fold0.purge_end == 20

    def test_rolling_embargo_carves_next_fold(self) -> None:
        """Per AFML §7.4.2 the embargo is a per-fold band applied
        only to the NEXT fold's training. Round 1 F-1-4 corrected
        the implementation: prior-fold embargo does NOT accumulate
        across all downstream folds. This test verifies the
        immediately-prior embargo still carves when step_size >
        test_size creates a gap such that the next training window
        overlaps the prior embargo.
        """
        spec = walk_forward_split(
            n_samples=60,
            initial_train_size=20,
            test_size=5,
            step_size=10,
            label_horizon=0,
            embargo=2,
            mode="rolling",
        )
        # Fold 0: train [0,20), test [20,25), embargo [25,27)
        # Fold 1 origin=30: rolling train = [10,30); prior embargo
        # [25,27) overlaps → train_segments = ((10,25),(27,30)).
        fold1 = spec.folds[1]
        assert fold1.train_segments == ((10, 25), (27, 30))

    def test_rolling_embargo_does_not_accumulate_across_folds(self) -> None:
        """Round 1 F-1-4 regression: fold k should not inherit
        embargo bands from folds 0..k-2, only from fold k-1."""
        spec = walk_forward_split(
            n_samples=100,
            initial_train_size=20,
            test_size=5,
            step_size=10,
            label_horizon=0,
            embargo=2,
            mode="rolling",
        )
        # Fold 2 origin=40: rolling train [20,40). Fold 1's embargo
        # is [35,37) (test [30,35)). Fold 0's embargo [25,27) must
        # NOT be carved out — that's the pre-remediation bug.
        fold2 = spec.folds[2]
        # Exactly one carve-out: the segments include [20,35) and
        # [37,40), but NOT a hole at [25,27).
        positions_in_train = {
            p
            for start, end in fold2.train_segments
            for p in range(start, end)
        }
        assert 25 in positions_in_train and 26 in positions_in_train
        assert 35 not in positions_in_train and 36 not in positions_in_train

    def test_rolling_max_folds_caps_generation(self) -> None:
        spec = walk_forward_split(
            n_samples=1000,
            initial_train_size=100,
            test_size=10,
            step_size=10,
            label_horizon=0,
            embargo=0,
            max_folds=3,
        )
        assert len(spec.folds) == 3

    def test_rolling_insufficient_span_raises(self) -> None:
        with pytest.raises(ValueError, match="zero folds"):
            walk_forward_split(
                n_samples=5,
                initial_train_size=10,
                test_size=1,
                step_size=1,
                label_horizon=0,
                embargo=0,
            )

    def test_rolling_purge_greater_than_train_block_raises(self) -> None:
        with pytest.raises(ValueError, match="Either reduce label_horizon"):
            walk_forward_split(
                n_samples=60,
                initial_train_size=5,
                test_size=5,
                step_size=5,
                label_horizon=10,
                embargo=0,
            )

    def test_rolling_fold_ids_contiguous(self) -> None:
        spec = walk_forward_split(
            n_samples=100,
            initial_train_size=30,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
        )
        assert [f.fold_id for f in spec.folds] == list(range(len(spec.folds)))

    def test_rolling_train_test_disjoint(self) -> None:
        spec = walk_forward_split(
            n_samples=80,
            initial_train_size=20,
            test_size=5,
            step_size=5,
            label_horizon=1,
            embargo=1,
        )
        for fold in spec.folds:
            train = set(fold.train_indices())
            test = set(fold.test_indices())
            assert train.isdisjoint(test), (
                f"Fold {fold.fold_id} train/test overlap: "
                f"{sorted(train & test)[:5]}"
            )


class TestWalkForwardExpanding:
    def test_expanding_train_start_anchored_at_zero(self) -> None:
        spec = walk_forward_split(
            n_samples=60,
            initial_train_size=20,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
            mode="expanding",
        )
        assert spec.scheme == "walk_forward_expanding"
        for fold in spec.folds:
            assert fold.train_segments[0][0] == 0

    def test_expanding_train_grows(self) -> None:
        spec = walk_forward_split(
            n_samples=60,
            initial_train_size=20,
            test_size=5,
            step_size=5,
            label_horizon=0,
            embargo=0,
            mode="expanding",
        )
        sizes = [f.n_train for f in spec.folds]
        assert sizes == sorted(sizes)
        assert sizes[-1] > sizes[0]

    def test_expanding_bad_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="mode must be"):
            walk_forward_split(
                n_samples=40,
                initial_train_size=10,
                test_size=5,
                step_size=5,
                label_horizon=0,
                embargo=0,
                mode="not-a-mode",  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# SplitSpec invariants (leak canary (b))
# ---------------------------------------------------------------------------


class TestSplitSpecInvariants:
    def test_purge_less_than_label_horizon_raises(self) -> None:
        with pytest.raises(ValueError, match="leak canary"):
            SplitSpec(
                folds=(_dummy_fold(),),
                n_samples=100,
                label_horizon=5,
                purge_window=3,
                embargo=0,
                scheme="walk_forward_rolling",
            )

    def test_negative_embargo_raises(self) -> None:
        with pytest.raises(ValueError, match="embargo must be >= 0"):
            SplitSpec(
                folds=(_dummy_fold(),),
                n_samples=100,
                label_horizon=0,
                purge_window=0,
                embargo=-1,
                scheme="walk_forward_rolling",
            )

    def test_zero_embargo_legal(self) -> None:
        spec = SplitSpec(
            folds=(_dummy_fold(),),
            n_samples=100,
            label_horizon=0,
            purge_window=0,
            embargo=0,
            scheme="walk_forward_rolling",
        )
        assert spec.embargo == 0

    def test_fold_ids_must_be_contiguous(self) -> None:
        bad_fold = Fold(
            fold_id=5,  # not zero
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
        with pytest.raises(ValueError, match="fold_id = 5; expected 0"):
            SplitSpec(
                folds=(bad_fold,),
                n_samples=100,
                label_horizon=0,
                purge_window=0,
                embargo=0,
                scheme="walk_forward_rolling",
            )

    def test_n_samples_non_positive_raises(self) -> None:
        with pytest.raises(ValueError, match="n_samples must be > 0"):
            SplitSpec(
                folds=(_dummy_fold(),),
                n_samples=0,
                label_horizon=0,
                purge_window=0,
                embargo=0,
                scheme="walk_forward_rolling",
            )


# ---------------------------------------------------------------------------
# Fold-level invariants
# ---------------------------------------------------------------------------


class TestFold:
    def test_train_test_overlap_raises(self) -> None:
        with pytest.raises(ValueError, match="direct look-ahead leak"):
            Fold(
                fold_id=0,
                train_start=0,
                train_end=20,
                test_start=10,
                test_end=25,
                purge_start=0,
                purge_end=0,
                embargo_start=0,
                embargo_end=0,
                train_segments=((0, 20),),
                test_segments=((10, 25),),
            )

    def test_n_train_n_test_match_segment_sum(self) -> None:
        f = Fold(
            fold_id=0,
            train_start=0,
            train_end=30,
            test_start=30,
            test_end=35,
            purge_start=0,
            purge_end=0,
            embargo_start=0,
            embargo_end=0,
            train_segments=((0, 10), (20, 30)),
            test_segments=((30, 35),),
        )
        assert f.n_train == 20
        assert f.n_test == 5

    def test_indices_flatten_segments(self) -> None:
        f = Fold(
            fold_id=0,
            train_start=0,
            train_end=8,
            test_start=8,
            test_end=10,
            purge_start=0,
            purge_end=0,
            embargo_start=0,
            embargo_end=0,
            train_segments=((0, 3), (5, 8)),
            test_segments=((8, 10),),
        )
        assert f.train_indices() == [0, 1, 2, 5, 6, 7]
        assert f.test_indices() == [8, 9]

    def test_malformed_range_raises(self) -> None:
        with pytest.raises(ValueError, match="train_start"):
            Fold(
                fold_id=0,
                train_start=10,
                train_end=5,  # reversed
                test_start=20,
                test_end=25,
                purge_start=0,
                purge_end=0,
                embargo_start=0,
                embargo_end=0,
                train_segments=((0, 5),),
                test_segments=((20, 25),),
            )


# ---------------------------------------------------------------------------
# Purged K-Fold (AFML §7.4.3)
# ---------------------------------------------------------------------------


class TestPurgedKFold:
    def test_basic_k_folds(self) -> None:
        spec = purged_kfold_split(
            n_samples=100,
            n_splits=5,
            label_horizon=2,
            embargo=1,
        )
        assert spec.scheme == "purged_kfold"
        assert len(spec.folds) == 5

    def test_even_block_partition(self) -> None:
        spec = purged_kfold_split(
            n_samples=100,
            n_splits=4,
            label_horizon=0,
            embargo=0,
        )
        # 100/4 = 25 per block exactly.
        for k, fold in enumerate(spec.folds):
            assert fold.test_start == 25 * k
            assert fold.test_end == 25 * (k + 1)

    def test_uneven_block_partition(self) -> None:
        spec = purged_kfold_split(
            n_samples=103,
            n_splits=5,
            label_horizon=0,
            embargo=0,
        )
        # 103 / 5 → blocks of [21, 21, 21, 20, 20] (remainder 3 to first 3)
        widths = [f.test_end - f.test_start for f in spec.folds]
        assert widths == [21, 21, 21, 20, 20]
        assert sum(widths) == 103

    def test_purge_removes_both_sides_of_test_block(self) -> None:
        spec = purged_kfold_split(
            n_samples=50,
            n_splits=5,
            label_horizon=2,
            embargo=0,
        )
        # Middle fold (k=2): test [20,30). Leading purge [18,20),
        # trailing purge [30,32). Train = [0,18) ∪ [32,50).
        fold2 = spec.folds[2]
        assert fold2.train_segments == ((0, 18), (32, 50))

    def test_embargo_applied_only_to_trailing_edge(self) -> None:
        spec = purged_kfold_split(
            n_samples=50,
            n_splits=5,
            label_horizon=0,
            embargo=3,
        )
        # k=2: test [20,30). Embargo [30,33) adds to the purge.
        # Train = [0,20) ∪ [33,50).
        fold2 = spec.folds[2]
        assert fold2.train_segments == ((0, 20), (33, 50))

    def test_k_one_rejected(self) -> None:
        with pytest.raises(ValueError, match="n_splits must be >= 2"):
            purged_kfold_split(
                n_samples=100,
                n_splits=1,
                label_horizon=0,
                embargo=0,
            )

    def test_leak_free_disjoint_train_test(self) -> None:
        spec = purged_kfold_split(
            n_samples=100,
            n_splits=5,
            label_horizon=3,
            embargo=2,
        )
        for fold in spec.folds:
            train = set(fold.train_indices())
            test = set(fold.test_indices())
            assert train.isdisjoint(test)
            # Purge band must also be disjoint from both.
            for i in range(fold.purge_start, fold.purge_end):
                assert i not in train


# ---------------------------------------------------------------------------
# CPCV
# ---------------------------------------------------------------------------


class TestCPCV:
    def test_combination_count_matches_math_comb(self) -> None:
        # Spot-check across a few sizes (and that the helper matches).
        for n, k in [(6, 2), (8, 3), (5, 1)]:
            assert cpcv_combination_count(n, k) == math.comb(n, k)

    def test_scaffold_emits_expected_number_of_folds(self) -> None:
        spec = cpcv_split(
            n_samples=100,
            n_groups=6,
            n_test_groups=2,
            label_horizon=1,
            embargo=0,
        )
        assert spec.scheme == "cpcv"
        # All C(6,2) = 15 combinations produce a valid fold for this
        # light-purge setup. If a combo wipes out training, it's skipped
        # — here none do.
        assert len(spec.folds) == 15

    def test_each_fold_train_test_disjoint(self) -> None:
        spec = cpcv_split(
            n_samples=80,
            n_groups=5,
            n_test_groups=2,
            label_horizon=0,
            embargo=0,
        )
        for fold in spec.folds:
            train = set(fold.train_indices())
            test = set(fold.test_indices())
            assert train.isdisjoint(test)

    def test_n_test_groups_ge_n_groups_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be <"):
            cpcv_split(
                n_samples=50,
                n_groups=4,
                n_test_groups=4,
                label_horizon=0,
                embargo=0,
            )


# ---------------------------------------------------------------------------
# Range arithmetic helpers
# ---------------------------------------------------------------------------


class TestRangeHelpers:
    def test_union_merges_overlap(self) -> None:
        assert _union_ranges([(0, 5), (3, 8)]) == [(0, 8)]

    def test_union_sorts_and_merges_adjacent(self) -> None:
        assert _union_ranges([(10, 12), (5, 7), (7, 10)]) == [(5, 12)]

    def test_union_drops_empty(self) -> None:
        assert _union_ranges([(5, 5), (3, 7)]) == [(3, 7)]

    def test_subtract_handles_full_coverage(self) -> None:
        assert _subtract_ranges(((0, 10),), [(0, 10)]) == []

    def test_subtract_handles_interior_hole(self) -> None:
        assert _subtract_ranges(((0, 10),), [(3, 5)]) == [(0, 3), (5, 10)]

    def test_subtract_chains_across_multiple_holes(self) -> None:
        assert _subtract_ranges(
            ((0, 20),), [(2, 4), (6, 8), (15, 17)]
        ) == [(0, 2), (4, 6), (8, 15), (17, 20)]

    def test_subtract_no_op_when_removals_disjoint(self) -> None:
        assert _subtract_ranges(((0, 10),), [(20, 30)]) == [(0, 10)]

    def test_subtract_multi_base_segments(self) -> None:
        # Two base segments; removal spans across their boundary.
        assert _subtract_ranges(((0, 5), (10, 20)), [(4, 12)]) == [
            (0, 4),
            (12, 20),
        ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dummy_fold() -> Fold:
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
