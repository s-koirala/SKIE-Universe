"""Unit tests for H055 swing-pivot setup detector."""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.features.h055.swing_pivot import (
    SwingPivotSetup,
    detect_long_swing_pivot_setups,
    detect_short_swing_pivot_setups,
    detect_swing_pivot_setups,
)


# ─── Long swing pivot ────────────────────────────────────────────────────────


def test_long_swing_pivot_canonical_pattern() -> None:
    # Lows: [10, 9, 8, 7, 8, 9] — bars 0-3 are 3 consecutive lower lows
    # ending at bar 3 (the swing low), followed by 2 higher lows at bars 4, 5.
    # Confirmation at bar 5.
    high = np.array([10.5, 9.5, 8.5, 7.5, 8.5, 9.5])
    low = np.array([10.0, 9.0, 8.0, 7.0, 8.0, 9.0])
    setups = detect_long_swing_pivot_setups(high, low, confirmation_window=5)
    assert len(setups) == 1
    assert setups[0].confirmation_bar == 5
    assert setups[0].swing_bar == 3
    assert setups[0].side == 1
    assert setups[0].entry_limit_price == 7.0


def test_long_swing_pivot_no_confirmation_returns_empty() -> None:
    # Lows continue lower; no 2 higher-lows emerge → no setup.
    low = np.array([10.0, 9.0, 8.0, 7.0, 6.0, 5.0])
    high = low + 0.5
    setups = detect_long_swing_pivot_setups(high, low, confirmation_window=2)
    assert setups == []


def test_long_swing_pivot_only_one_higher_low_returns_empty() -> None:
    # 3 lower-lows then 1 higher-low then back down → not confirmed.
    low = np.array([10.0, 9.0, 8.0, 7.0, 8.0, 6.0, 5.0])
    high = low + 0.5
    setups = detect_long_swing_pivot_setups(high, low, confirmation_window=3)
    assert setups == []


def test_long_swing_pivot_higher_lows_can_be_non_consecutive() -> None:
    # Lows: [10, 9, 8, 7, 6.5, 7.5, 8.5]
    # Two distinct swing-pivot patterns coexist:
    #   - Swing at bar 3 (lows [10>9>8>7]), with 2 higher-lows at bars 5+6
    #     (bar 4 = 6.5 is a LOWER low, NOT a higher low). Confirmation: bar 6.
    #   - Swing at bar 4 (lows [9>8>7>6.5]), with 2 higher-lows at bars 5+6.
    #     Confirmation: bar 6.
    # The detector emits BOTH — overlapping setups are valid. The orchestrator
    # decides post-hoc which to act on per design.md §4 entry rule (limit
    # order at the wick extreme of the swing-pivot bar).
    low = np.array([10.0, 9.0, 8.0, 7.0, 6.5, 7.5, 8.5])
    high = low + 0.5
    setups = detect_long_swing_pivot_setups(high, low, confirmation_window=5)
    assert len(setups) == 2
    confirmation_bars = sorted(s.confirmation_bar for s in setups)
    assert confirmation_bars == [6, 6]
    swing_bars = sorted(s.swing_bar for s in setups)
    assert swing_bars == [3, 4]
    entry_prices = sorted(s.entry_limit_price for s in setups)
    assert entry_prices == [6.5, 7.0]


def test_long_swing_pivot_validates_confirmation_window() -> None:
    high = np.array([10.5, 9.5, 8.5, 7.5])
    low = np.array([10.0, 9.0, 8.0, 7.0])
    with pytest.raises(ValueError, match="confirmation_window"):
        detect_long_swing_pivot_setups(high, low, confirmation_window=1)


def test_long_swing_pivot_rejects_shape_mismatch() -> None:
    high = np.array([10.0, 9.0, 8.0, 7.0])
    low = np.array([9.5, 8.5, 8.0])
    with pytest.raises(ValueError, match="shape mismatch"):
        detect_long_swing_pivot_setups(high, low)


def test_long_swing_pivot_short_panel_returns_empty() -> None:
    high = np.array([10.0, 9.0])
    low = np.array([9.5, 8.5])
    setups = detect_long_swing_pivot_setups(high, low)
    assert setups == []


# ─── Short swing pivot ───────────────────────────────────────────────────────


def test_short_swing_pivot_canonical_pattern() -> None:
    # Highs: [10, 11, 12, 13, 12, 11] — 3 consecutive higher highs end at
    # bar 3 (swing high), 2 lower highs at bars 4, 5. Confirmation at bar 5.
    high = np.array([10.0, 11.0, 12.0, 13.0, 12.0, 11.0])
    low = high - 0.5
    setups = detect_short_swing_pivot_setups(high, low, confirmation_window=5)
    assert len(setups) == 1
    assert setups[0].confirmation_bar == 5
    assert setups[0].swing_bar == 3
    assert setups[0].side == -1
    assert setups[0].entry_limit_price == 13.0


def test_short_swing_pivot_no_confirmation() -> None:
    high = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    low = high - 0.5
    setups = detect_short_swing_pivot_setups(high, low, confirmation_window=2)
    assert setups == []


# ─── Combined detect_swing_pivot_setups ──────────────────────────────────────


def test_combined_returns_sorted_chronologically() -> None:
    # Two distinct setups: long at bars [0..5], short at bars [10..15]
    n = 16
    low = np.full(n, 5.0)
    high = np.full(n, 6.0)
    # Long pattern: lows 10/9/8/7 → 8/9 (confirmed at bar 5)
    low[0:6] = [10.0, 9.0, 8.0, 7.0, 8.0, 9.0]
    high[0:6] = [10.5, 9.5, 8.5, 7.5, 8.5, 9.5]
    # Short pattern at bars [10..15]: highs 10/11/12/13 → 12/11 (confirmed at bar 15)
    high[10:16] = [10.0, 11.0, 12.0, 13.0, 12.0, 11.0]
    low[10:16] = [9.5, 10.5, 11.5, 12.5, 11.5, 10.5]

    combined = detect_swing_pivot_setups(high, low, confirmation_window=5)
    assert len(combined) == 2
    assert combined[0].side == 1 and combined[0].confirmation_bar == 5
    assert combined[1].side == -1 and combined[1].confirmation_bar == 15


# ─── PIT-safety ──────────────────────────────────────────────────────────────


def test_setups_are_causally_pit_safe() -> None:
    # Detect setups on a panel; truncate at each confirmation_bar; verify
    # the truncated panel detects exactly the setups whose confirmation_bar
    # is <= truncation point. This validates that the detector confirms
    # at confirmation_bar (not earlier, not later).
    n = 20
    low = np.full(n, 5.0)
    high = np.full(n, 6.0)
    low[0:6] = [10.0, 9.0, 8.0, 7.0, 8.0, 9.0]
    high[0:6] = [10.5, 9.5, 8.5, 7.5, 8.5, 9.5]
    full_setups = detect_swing_pivot_setups(high, low, confirmation_window=5)
    assert len(full_setups) == 1
    confirmation_bar_full = full_setups[0].confirmation_bar

    # Truncate one bar before confirmation: should detect zero setups.
    setups_at_pre = detect_swing_pivot_setups(
        high[: confirmation_bar_full],
        low[: confirmation_bar_full],
        confirmation_window=5,
    )
    assert len(setups_at_pre) == 0

    # At exactly confirmation_bar (inclusive): should detect the setup.
    setups_at_confirm = detect_swing_pivot_setups(
        high[: confirmation_bar_full + 1],
        low[: confirmation_bar_full + 1],
        confirmation_window=5,
    )
    assert len(setups_at_confirm) == 1
    assert setups_at_confirm[0].confirmation_bar == confirmation_bar_full
