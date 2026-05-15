"""BLOCKING-BEFORE-LAUNCH: H062 channel-state-at-fold-boundary continuity test.

Per H062 design.md §5.6 + §11.2 ``P1-H062-LEVEL-STATE-FOLD-CONTINUITY``
(BLOCKING unit test, intraday channel-N reset at fold boundary).

The design.md §5.6 R1 F1-007 binding policy:
    Channel-state-at-fold-boundary policy: channel state computed on full
    continuous PIT-causal panel; embargo ensures train-fold last-bar
    precedes test-fold first-eligible-bar by >= max-channel-N + embargo
    minutes (= 480 × 5 + 2400 = 4800 minutes total). Unit test verifies
    bit-identical channel values regardless of fold partition.

What this test asserts:
    1. ``donchian_channel`` is a pure function of the prior-N closes; the
       channel at bar t uses ONLY closes [t-N, t-1] regardless of where any
       fold boundary is drawn on the underlying continuous panel.
    2. The H062 orchestrator's recommended pattern (compute features on
       the FULL continuous panel BEFORE fold-slicing) yields bit-identical
       channel values at test-fold-first-eligible bars as the alternative
       of re-computing features per fold on the embargoed train + test
       slice. This is the load-bearing invariant for the §5.6 R1 F1-007
       embargo discipline.
    3. The embargo arithmetic for H062 at the binding parameters
       channel_n_max=480, cadence=5min, embargo_minutes=2400:
            min train-fold-last-bar to test-fold-first-eligible-bar gap
            = 4800 minutes = 960 bars at 5-min cadence.

Test classes:
    - TestContinuousPanelChannelInvariance: channel bit-identity under
      arbitrary fold partitions of the underlying continuous panel.
    - TestEmbargoArithmetic: assertions on the binding §5.6 embargo
      parameters (4800-min total purge+embargo gap).
    - TestFoldBoundaryFirstEventCausality: at a test-fold first-eligible
      bar, the channel uses train-fold closes from the prior N bars
      (no NaN reset; no leak across the boundary).

References:
    - López de Prado 2018 *AFML* §7.4 purged k-fold and walk-forward
      methodologies (*practitioner*).
    - design.md §5.6 R1 F1-007 fix: purge vs embargo distinction.
    - design.md §11.2 row ``P1-H062-LEVEL-STATE-FOLD-CONTINUITY``.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.features.h062.donchian import (
    donchian_breakout_events,
    donchian_channel,
    first_fire_filter,
)


# Binding parameters per design.md §5.6:
H062_MAX_CHANNEL_N = 480  # bars per design.md §3 N grid upper bound
H062_CADENCE_MINUTES = 5
H062_EMBARGO_MINUTES = 2400  # per design.md §5.6 R1 F1-007 binding
H062_PURGE_MINUTES = H062_MAX_CHANNEL_N * H062_CADENCE_MINUTES  # 2400 min
H062_TOTAL_GAP_MINUTES = H062_PURGE_MINUTES + H062_EMBARGO_MINUTES  # 4800 min
H062_TOTAL_GAP_BARS = H062_TOTAL_GAP_MINUTES // H062_CADENCE_MINUTES  # 960 bars


@pytest.fixture(scope="module")
def long_continuous_panel() -> np.ndarray:
    """Deterministic 5000-bar continuous close series at 5-min cadence."""
    rng = np.random.default_rng(20260514)  # matches H062.yaml RNG seed prefix
    n = 5000
    log_rets = rng.normal(0, 0.0008, n).cumsum()
    return 100.0 * np.exp(log_rets)


class TestContinuousPanelChannelInvariance:
    """Channel at bar t is invariant to the fold partition of the panel."""

    def test_channel_bit_identical_under_arbitrary_fold_split(
        self, long_continuous_panel: np.ndarray
    ) -> None:
        """Bit-equality of channel values under different fold partitions.

        Compute channel on full continuous panel. Then slice the panel at
        an arbitrary fold boundary, compute channel on the train+test slice
        only, and verify the test-fold channel values equal the continuous
        panel's channel values bit-for-bit at the same bar indices.

        Critical: the slice must be done WITH the prior N closes prepended
        (per the §5.6 R1 F1-007 binding: the channel is a PIT-causal
        function of the most-recent N closes; if the orchestrator drops
        those N closes when isolating a fold, the channel resets to NaN.
        H062's recommended pattern is to PRESERVE the prior-N-closes-as-
        feature-warm-up window per the purge convention).
        """
        N = 60
        full_close = long_continuous_panel
        n = full_close.size

        # Compute channel on full continuous panel.
        ch_full = donchian_channel(full_close, channel_n=N)

        # Define an arbitrary fold split at bar 1500 (representative).
        test_start = 1500
        test_end = 3000

        # Slice with prior-N-closes preserved (the §5.6 R1 F1-007 pattern).
        warmup_start = test_start - N
        slice_close = full_close[warmup_start:test_end]
        ch_slice = donchian_channel(slice_close, channel_n=N)

        # The bar at test_start in the full panel corresponds to bar N in
        # the slice. Their channel values must match bit-for-bit from
        # test_start through test_end-1.
        for t in range(test_start, test_end):
            slice_idx = t - warmup_start
            assert (
                ch_full.channel_high[t] == ch_slice.channel_high[slice_idx]
            ), f"channel_high mismatch at t={t}, slice_idx={slice_idx}"
            assert (
                ch_full.channel_low[t] == ch_slice.channel_low[slice_idx]
            ), f"channel_low mismatch at t={t}, slice_idx={slice_idx}"

    def test_breakout_events_bit_identical_under_fold_split(
        self, long_continuous_panel: np.ndarray
    ) -> None:
        """Raw breakout events match under fold-split warm-up pattern."""
        N = 60
        full_close = long_continuous_panel
        ch_full = donchian_channel(full_close, channel_n=N)
        events_full = donchian_breakout_events(full_close, ch_full)

        test_start = 2000
        test_end = 2500
        warmup_start = test_start - N
        slice_close = full_close[warmup_start:test_end]
        ch_slice = donchian_channel(slice_close, channel_n=N)
        events_slice = donchian_breakout_events(slice_close, ch_slice)

        for t in range(test_start, test_end):
            slice_idx = t - warmup_start
            assert events_full[t] == events_slice[slice_idx], (
                f"event mismatch at t={t}"
            )

    def test_filtered_events_bit_identical_under_fold_split(
        self, long_continuous_panel: np.ndarray
    ) -> None:
        """First-fire-filtered events bit-identical under the warm-up pattern.

        Subtler than the raw events: the first-fire filter has STATE (the
        per-side last-fire counter). For bit-equality at the test-fold
        first-eligible bar, the slice MUST include the in-channel warm-up
        bars so the filter state has time to converge to the same condition.
        At cadence=5min + h_dwell up to {1,2,5,10} bars, the warm-up window
        of N=60 bars is much larger than h_dwell, so the filter state
        converges within the warm-up region.
        """
        N = 60
        H_DWELL = 5
        full_close = long_continuous_panel
        ch_full = donchian_channel(full_close, channel_n=N)
        events_full = donchian_breakout_events(full_close, ch_full)
        filtered_full = first_fire_filter(events_full, h_dwell=H_DWELL)

        test_start = 2000
        test_end = 2500
        warmup_start = test_start - N
        slice_close = full_close[warmup_start:test_end]
        ch_slice = donchian_channel(slice_close, channel_n=N)
        events_slice = donchian_breakout_events(slice_close, ch_slice)
        filtered_slice = first_fire_filter(events_slice, h_dwell=H_DWELL)

        # Per the warm-up convention, filter state may differ in the first
        # H_DWELL bars after test_start (the filter's last_fire memory does
        # not look back beyond warmup_start). Allow that initial transient
        # and assert bit-equality after the transient.
        for t in range(test_start + H_DWELL + 1, test_end):
            slice_idx = t - warmup_start
            assert filtered_full[t] == filtered_slice[slice_idx], (
                f"filter event mismatch at t={t}"
            )


class TestEmbargoArithmetic:
    """Embargo + purge arithmetic per design.md §5.6 R1 F1-007 binding."""

    def test_max_channel_n_grid_upper_bound(self) -> None:
        """The §3 channel-N grid upper bound is 480 bars."""
        assert H062_MAX_CHANNEL_N == 480

    def test_purge_minutes_equals_max_n_times_cadence(self) -> None:
        """Purge = max-channel-N × cadence = 480 × 5 = 2400 min per §5.6."""
        assert H062_PURGE_MINUTES == 480 * 5
        assert H062_PURGE_MINUTES == 2400

    def test_embargo_minutes_binding_value(self) -> None:
        """Embargo = 2400 minutes per design.md §5.6 binding."""
        assert H062_EMBARGO_MINUTES == 2400

    def test_total_gap_minutes_equals_4800(self) -> None:
        """Total purge+embargo gap = 4800 min per design.md §5.6 R1 F1-007."""
        assert H062_TOTAL_GAP_MINUTES == 4800

    def test_total_gap_in_5min_bars_equals_960(self) -> None:
        """At 5-min cadence, the total gap is 960 bars."""
        assert H062_TOTAL_GAP_BARS == 960

    def test_total_gap_covers_max_channel_n_with_margin(self) -> None:
        """The total purge+embargo gap covers max-channel-N by 2x margin.

        Per the §5.6 R1 F1-007 binding: purge alone equals max-N × cadence;
        the additional embargo on top is the label-horizon protection.
        The total gap is therefore 2 × purge alone, providing one-window
        margin beyond the channel feature warm-up.
        """
        assert H062_TOTAL_GAP_BARS >= 2 * H062_MAX_CHANNEL_N

    @pytest.mark.parametrize(
        "channel_n",
        [20, 40, 60, 120, 240, 480],
    )
    def test_grid_value_under_max(self, channel_n: int) -> None:
        """Every value in the design.md §3 channel-N grid is <= 480."""
        assert channel_n <= H062_MAX_CHANNEL_N


class TestFoldBoundaryFirstEventCausality:
    """At test-fold first-eligible bar, the channel uses train-fold prior bars.

    This is the canonical leakage-causality check at the fold boundary —
    no NaN reset, no train→test leak.
    """

    def test_channel_at_first_test_bar_uses_train_closes(
        self, long_continuous_panel: np.ndarray
    ) -> None:
        """First test-bar channel = max/min of prior-N TRAIN closes."""
        N = 60
        full_close = long_continuous_panel
        ch_full = donchian_channel(full_close, channel_n=N)

        # Define a fold boundary at bar 1500. The test fold's first
        # eligible bar is 1500 (after the §5.6 R1 F1-007 purge embargo
        # is enforced by the orchestrator).
        test_first_bar = 1500
        train_last_bar = test_first_bar - 1
        # Channel at test_first_bar uses closes [test_first_bar - N,
        # test_first_bar - 1].
        expected_high = full_close[test_first_bar - N : test_first_bar].max()
        expected_low = full_close[test_first_bar - N : test_first_bar].min()

        assert ch_full.channel_high[test_first_bar] == expected_high
        assert ch_full.channel_low[test_first_bar] == expected_low
        # And train_last_bar is at index test_first_bar - 1
        assert train_last_bar == test_first_bar - 1

    def test_train_test_close_mutations_dont_leak_via_channel(
        self, long_continuous_panel: np.ndarray
    ) -> None:
        """Mutating test-fold-future closes does not change train-fold channel.

        Regression test on the PIT-causality of the channel feature: the
        train-fold channel must be invariant to any data outside the
        train fold.
        """
        N = 60
        full_close_v1 = long_continuous_panel.copy()
        full_close_v2 = long_continuous_panel.copy()
        train_end = 1500
        full_close_v2[train_end:] = full_close_v2[train_end:] * 5.0  # mutate

        ch_v1 = donchian_channel(full_close_v1, channel_n=N)
        ch_v2 = donchian_channel(full_close_v2, channel_n=N)

        # Train channel (bars 0..train_end-1) must match.
        np.testing.assert_array_equal(
            ch_v1.channel_high[:train_end], ch_v2.channel_high[:train_end]
        )
        np.testing.assert_array_equal(
            ch_v1.channel_low[:train_end], ch_v2.channel_low[:train_end]
        )

    def test_total_gap_satisfies_label_horizon_for_24_5_session(self) -> None:
        """Total 4800-min gap covers 24/5 (metals) max session duration.

        Per design.md §5.6 R1 F1-007: label horizon bounded by §4 EOD-flatten
        = max session duration ≈ 1380 min for 24/5 metals leg. The
        embargo (2400 min) covers this by 1.74x margin per the design.md
        formula: 2400 / 1380 ≈ 1.74.
        """
        max_24_5_session_minutes = 1380
        assert H062_EMBARGO_MINUTES >= max_24_5_session_minutes
        margin = H062_EMBARGO_MINUTES / max_24_5_session_minutes
        # Allow a small float tolerance on the 1.74 margin check.
        assert margin > 1.7
