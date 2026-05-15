"""Unit tests for H062 Donchian channel + first-fire detector.

Per H062 design.md §3 — close-to-close N-bar Donchian channel per
Faith 2007 *Way of the Turtle* (*practitioner*; ISBN 978-0071486644)
+ first-fire H_dwell re-arm filter.

Test classes:
  - TestDonchianChannel: PIT semantic, channel bounds, init mask.
  - TestDonchianBreakoutEvents: raw event detector edge cases.
  - TestFirstFireFilter: H_dwell re-arm logic, per-side independence.
  - TestPITCausality: regression test that channel uses only [t-N, t-1]
    closes for the bar-t channel value (no look-ahead via bar-t close).
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.features.h062.donchian import (
    DonchianChannel,
    donchian_breakout_events,
    donchian_channel,
    first_fire_filter,
)


class TestDonchianChannel:
    def test_channel_high_low_at_first_init_bar(self) -> None:
        # close = [10, 11, 12, 13, 14, 15] with N=3
        # at t=3, channel = max(close[0:3]) = 12, min = 10
        close = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
        ch = donchian_channel(close, channel_n=3)
        assert ch.is_initialized[2] is np.False_ or ch.is_initialized[2] == False  # noqa: E712
        assert ch.is_initialized[3] is np.True_ or ch.is_initialized[3] == True  # noqa: E712
        assert ch.channel_high[3] == 12.0
        assert ch.channel_low[3] == 10.0
        assert ch.channel_high[4] == 13.0
        assert ch.channel_low[4] == 11.0

    def test_channel_undefined_before_init(self) -> None:
        close = np.arange(20.0)
        ch = donchian_channel(close, channel_n=5)
        # channel undefined for t < 5
        assert np.all(np.isnan(ch.channel_high[:5]))
        assert np.all(np.isnan(ch.channel_low[:5]))
        # channel defined for t >= 5
        assert np.all(np.isfinite(ch.channel_high[5:]))
        assert np.all(np.isfinite(ch.channel_low[5:]))

    def test_channel_n_equals_one_uses_prior_bar(self) -> None:
        # N=1: channel_high[t] = close[t-1]
        close = np.array([5.0, 7.0, 3.0, 9.0, 2.0])
        ch = donchian_channel(close, channel_n=1)
        np.testing.assert_array_equal(ch.channel_high[1:], close[:-1])
        np.testing.assert_array_equal(ch.channel_low[1:], close[:-1])

    def test_channel_n_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="channel_n must be"):
            donchian_channel(np.arange(10.0), channel_n=0)

    def test_empty_close_raises(self) -> None:
        with pytest.raises(ValueError, match="empty close"):
            donchian_channel(np.array([]), channel_n=5)

    def test_channel_matches_naive_loop(self) -> None:
        # Brute-force reference: for each t, max/min of close[t-N:t]
        rng = np.random.default_rng(20260515)
        close = rng.normal(100.0, 1.0, 100).cumsum()
        N = 7
        ch = donchian_channel(close, channel_n=N)
        for t in range(N, len(close)):
            expected_high = close[t - N : t].max()
            expected_low = close[t - N : t].min()
            assert np.isclose(ch.channel_high[t], expected_high), f"t={t}"
            assert np.isclose(ch.channel_low[t], expected_low), f"t={t}"


class TestDonchianBreakoutEvents:
    def test_long_event_when_close_above_channel_high(self) -> None:
        close = np.array([10.0, 11.0, 12.0, 15.0])  # close[3] > max([10,11,12])=12
        ch = donchian_channel(close, channel_n=3)
        events = donchian_breakout_events(close, ch)
        assert events[3] == 1

    def test_short_event_when_close_below_channel_low(self) -> None:
        close = np.array([10.0, 11.0, 12.0, 5.0])  # close[3] < min([10,11,12])=10
        ch = donchian_channel(close, channel_n=3)
        events = donchian_breakout_events(close, ch)
        assert events[3] == -1

    def test_no_event_when_close_inside_channel(self) -> None:
        close = np.array([10.0, 11.0, 12.0, 11.5])
        ch = donchian_channel(close, channel_n=3)
        events = donchian_breakout_events(close, ch)
        assert events[3] == 0

    def test_no_event_before_channel_init(self) -> None:
        close = np.arange(10.0)
        ch = donchian_channel(close, channel_n=5)
        events = donchian_breakout_events(close, ch)
        # No event possible before init (channel is NaN)
        assert np.all(events[:5] == 0)

    def test_equal_to_channel_high_is_no_event(self) -> None:
        # strict-inequality semantic per design.md §3 channel-break definition
        close = np.array([10.0, 11.0, 12.0, 12.0])
        ch = donchian_channel(close, channel_n=3)
        events = donchian_breakout_events(close, ch)
        assert events[3] == 0  # equal -- not > channel_high


class TestFirstFireFilter:
    def test_first_fire_passes(self) -> None:
        raw = np.array([0, 0, 1, 0, 0], dtype=np.int8)
        f = first_fire_filter(raw, h_dwell=2)
        assert f.tolist() == [0, 0, 1, 0, 0]

    def test_second_consecutive_long_suppressed_within_dwell(self) -> None:
        raw = np.array([1, 1, 0, 0], dtype=np.int8)
        f = first_fire_filter(raw, h_dwell=2)
        # raw[0]=1 fires; raw[1]=1 within h_dwell=2 suppressed.
        assert f.tolist() == [1, 0, 0, 0]

    def test_long_re_arms_after_h_dwell(self) -> None:
        # h_dwell=2: re-arm after 2-bar gap (i.e., gap > h_dwell required)
        raw = np.array([1, 0, 0, 1], dtype=np.int8)
        f = first_fire_filter(raw, h_dwell=2)
        # raw[0]=1 fires (t=0, last_long_fire=0); raw[3]=1 at t=3 -> 3 - 0 = 3 > 2, fires
        assert f.tolist() == [1, 0, 0, 1]

    def test_long_does_not_re_arm_at_exactly_h_dwell_gap(self) -> None:
        # The semantic is "no fire in past H_dwell bars"; gap == h_dwell suppresses
        raw = np.array([1, 0, 1, 0], dtype=np.int8)
        f = first_fire_filter(raw, h_dwell=2)
        # raw[2]=1 at t=2, t - last_long_fire(0) = 2; 2 > 2 is False -> suppressed
        assert f.tolist() == [1, 0, 0, 0]

    def test_short_fires_independently_of_long(self) -> None:
        # Long fire does not suppress short on opposite-side event
        raw = np.array([1, -1, 0, 0], dtype=np.int8)
        f = first_fire_filter(raw, h_dwell=5)
        assert f.tolist() == [1, -1, 0, 0]

    def test_h_dwell_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="h_dwell must be"):
            first_fire_filter(np.array([0], dtype=np.int8), h_dwell=0)

    def test_long_short_alternating_within_dwell(self) -> None:
        # Both sides should fire (opposite-side independence)
        raw = np.array([1, -1, 1, -1], dtype=np.int8)
        f = first_fire_filter(raw, h_dwell=10)
        # First long fires (t=0); first short fires (t=1); next long suppressed
        # (t - last_long_fire(0) = 2 <= 10); next short suppressed
        # (t - last_short_fire(1) = 2 <= 10).
        assert f.tolist() == [1, -1, 0, 0]


class TestPITCausality:
    """Regression test: channel at bar t depends only on closes [t-N, t-1].

    PIT-causal semantic per design.md §7 + López de Prado 2018 *AFML* §13:
    the bar-t channel is the max/min of the N most-recent CONFIRMED prior
    closes; the bar-t close itself is NOT in the channel computation.
    """

    def test_modifying_future_close_does_not_change_past_channel(self) -> None:
        close_v1 = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
        close_v2 = close_v1.copy()
        close_v2[5] = 999.0  # mutate future bar
        close_v2[6] = -999.0
        ch_v1 = donchian_channel(close_v1, channel_n=3)
        ch_v2 = donchian_channel(close_v2, channel_n=3)
        # Channel at t=3 uses close[0..2]; bars 5, 6 mutated; t=3 should match.
        assert ch_v1.channel_high[3] == ch_v2.channel_high[3]
        assert ch_v1.channel_high[4] == ch_v2.channel_high[4]
        # Channel at t=5 uses close[2..4]; bars 5, 6 still future from t=5;
        # so channel_high[5] is robust to mutations at 5, 6.
        assert ch_v1.channel_high[5] == ch_v2.channel_high[5]

    def test_channel_at_t_uses_close_up_to_t_minus_one_not_t(self) -> None:
        # Construct closes where close[t] is a global max but channel at t
        # must NOT include close[t].
        close = np.array([10.0, 11.0, 12.0, 100.0])  # close[3]=100 is max
        ch = donchian_channel(close, channel_n=3)
        # channel_high[3] = max(close[0:3]) = 12 (NOT 100, which is close[3])
        assert ch.channel_high[3] == 12.0
        # Breakout event at bar 3: close[3]=100 > channel_high[3]=12 -> long fire
        events = donchian_breakout_events(close, ch)
        assert events[3] == 1
