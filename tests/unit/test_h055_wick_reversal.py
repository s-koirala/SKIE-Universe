"""Unit tests for H055 wick-reversal-non-swing detector."""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.features.h055.wick_reversal import (
    SwingLevelMemory,
    WickReversalSetup,
    detect_wick_reversal_setups,
)


# ─── SwingLevelMemory ────────────────────────────────────────────────────────


def test_swing_memory_starts_empty() -> None:
    m = SwingLevelMemory()
    assert m.most_recent_swing_high is None
    assert m.most_recent_swing_low is None


def test_swing_memory_update_and_reset() -> None:
    m = SwingLevelMemory()
    m.update_swing_high(105.0, bar_index=10)
    m.update_swing_low(95.0, bar_index=15)
    assert m.most_recent_swing_high == 105.0
    assert m.most_recent_swing_high_bar == 10
    assert m.most_recent_swing_low == 95.0
    m.reset()
    assert m.most_recent_swing_high is None
    assert m.most_recent_swing_low is None


def test_swing_memory_rejects_nonpositive_levels() -> None:
    m = SwingLevelMemory()
    with pytest.raises(ValueError, match="swing high"):
        m.update_swing_high(0.0, bar_index=0)
    with pytest.raises(ValueError, match="swing low"):
        m.update_swing_low(-5.0, bar_index=0)


# ─── Long wick-reversal ──────────────────────────────────────────────────────


def test_long_wick_reversal_canonical_pattern() -> None:
    # Memory: most-recent swing-low at 100.0
    # Bar: open=101, low=98 (punctures swing-low), close=102 (closes above
    # swing-low), high=102.5
    # body = |102 - 101| = 1; lower_wick = min(101, 102) - 98 = 3
    # ratio = 3/1 = 3.0 >= θ_wick_min = 1.0 → setup fires
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=0)
    o = np.array([101.0])
    h = np.array([102.5])
    l = np.array([98.0])
    c = np.array([102.0])
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert len(setups) == 1
    s = setups[0]
    assert s.side == 1
    assert s.bar_index == 0
    assert s.swing_level == 100.0
    assert s.entry_limit_price == 98.0
    assert s.wick_to_body_ratio == pytest.approx(3.0)


def test_long_wick_reversal_close_breaks_through_returns_empty() -> None:
    # Bar's close is BELOW the swing-low → "close breaking through" rule
    # rejects the setup.
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=0)
    o = np.array([101.0])
    h = np.array([101.5])
    l = np.array([95.0])
    c = np.array([99.0])  # closes below swing-low
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert setups == []


def test_long_wick_reversal_no_puncture_returns_empty() -> None:
    # Bar's low does NOT puncture swing-low.
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=0)
    o = np.array([105.0])
    h = np.array([106.0])
    l = np.array([102.0])  # above swing-low
    c = np.array([105.5])
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert setups == []


def test_long_wick_reversal_below_theta_wick_returns_empty() -> None:
    # ratio = 1.0; θ_wick_min = 2.0 → fails gate.
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=0)
    # body = 1; lower_wick = 1; ratio = 1.0
    o = np.array([100.5])
    h = np.array([101.5])
    l = np.array([99.5])  # punctures
    c = np.array([101.5])  # body 1; closes above
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=2.0
    )
    assert setups == []


def test_long_wick_reversal_doji_skipped() -> None:
    # Body == 0 → doji; θ_wick undefined; setup skipped.
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=0)
    o = np.array([101.0])
    h = np.array([102.0])
    l = np.array([98.0])
    c = np.array([101.0])  # equal to open → doji
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert setups == []


def test_no_swing_low_in_memory_returns_empty() -> None:
    m = SwingLevelMemory()  # empty memory
    o = np.array([101.0])
    h = np.array([102.0])
    l = np.array([95.0])
    c = np.array([101.5])
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert setups == []


# ─── Short wick-reversal ─────────────────────────────────────────────────────


def test_short_wick_reversal_canonical_pattern() -> None:
    # Memory: most-recent swing-high at 110.0
    # Bar: open=109, high=113 (punctures), close=108, low=107.5
    # body = 1; upper_wick = 113 - 109 = 4; ratio = 4.0
    m = SwingLevelMemory()
    m.update_swing_high(110.0, bar_index=0)
    o = np.array([109.0])
    h = np.array([113.0])
    l = np.array([107.5])
    c = np.array([108.0])
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert len(setups) == 1
    s = setups[0]
    assert s.side == -1
    assert s.swing_level == 110.0
    assert s.entry_limit_price == 113.0
    assert s.wick_to_body_ratio == pytest.approx(4.0)


def test_short_wick_reversal_close_breaks_through_returns_empty() -> None:
    m = SwingLevelMemory()
    m.update_swing_high(110.0, bar_index=0)
    o = np.array([109.0])
    h = np.array([112.0])
    l = np.array([108.5])
    c = np.array([111.0])  # closes ABOVE swing-high
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert setups == []


# ─── Combined / multi-bar ────────────────────────────────────────────────────


def test_multi_bar_panel_emits_chronologically() -> None:
    # Bar 0: nothing happens (memory empty).
    # Bar 1: update memory swing_low to 100.0.
    # Bar 2: long wick-reversal (low=99, close=101, body=1, lower_wick=2, ratio=2.0).
    # Bar 3: nothing.
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=1)
    o = np.array([105.0, 105.0, 102.0, 105.0])
    h = np.array([106.0, 106.0, 103.0, 106.0])
    l = np.array([104.0, 104.0, 99.0, 104.5])
    c = np.array([105.5, 105.5, 103.0, 105.0])
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert len(setups) == 1
    assert setups[0].bar_index == 2
    assert setups[0].side == 1


def test_long_and_short_setups_can_coexist_on_different_bars() -> None:
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=0)
    m.update_swing_high(110.0, bar_index=0)
    # Bar 0: long wick-rev (low=98, close=102, open=101, body=1, lwick=3, ratio=3)
    # Bar 1: short wick-rev (open=109, high=113, close=108, low=107, body=1, uwick=4, ratio=4)
    o = np.array([101.0, 109.0])
    h = np.array([102.5, 113.0])
    l = np.array([98.0, 107.0])
    c = np.array([102.0, 108.0])
    setups = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    assert len(setups) == 2
    assert setups[0].side == 1 and setups[0].bar_index == 0
    assert setups[1].side == -1 and setups[1].bar_index == 1


# ─── Validation ──────────────────────────────────────────────────────────────


def test_rejects_negative_theta_wick() -> None:
    m = SwingLevelMemory()
    o = np.array([1.0])
    h = np.array([1.0])
    l = np.array([1.0])
    c = np.array([1.0])
    with pytest.raises(ValueError, match="theta_wick_min"):
        detect_wick_reversal_setups(o, h, l, c, swing_level_memory=m, theta_wick_min=-0.5)


def test_rejects_shape_mismatch() -> None:
    m = SwingLevelMemory()
    o = np.array([1.0, 2.0])
    h = np.array([1.5])
    l = np.array([0.5, 1.5])
    c = np.array([1.0, 2.0])
    with pytest.raises(ValueError, match="shape mismatch"):
        detect_wick_reversal_setups(o, h, l, c, swing_level_memory=m, theta_wick_min=1.0)


def test_search_domain_theta_wick_values() -> None:
    # H055 design.md §5.6: θ_wick ∈ [1.0, 4.0]. Verify each endpoint works.
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=0)
    o = np.array([101.0])
    h = np.array([102.0])
    l = np.array([98.0])
    c = np.array([102.0])
    # body = 1; lower_wick = 3; ratio = 3.0
    for theta in (1.0, 2.0, 3.0, 4.0):
        setups = detect_wick_reversal_setups(
            o, h, l, c, swing_level_memory=m, theta_wick_min=theta
        )
        if theta <= 3.0:
            assert len(setups) == 1
        else:
            assert setups == []


def test_pit_safe_bar_only_uses_current_bar_ohlc() -> None:
    # Detector reads current bar's OHLC + memory state at-of-bar-time.
    # Truncating the panel at bar t should produce the same setups for bars [0, t].
    m = SwingLevelMemory()
    m.update_swing_low(100.0, bar_index=0)
    o = np.array([101.0, 105.0, 102.0, 99.0])
    h = np.array([102.5, 106.0, 103.0, 100.5])
    l = np.array([98.0, 104.0, 99.0, 96.0])
    c = np.array([102.0, 105.5, 102.5, 99.5])  # bar 3 closes BELOW swing-low → not a setup
    full = detect_wick_reversal_setups(
        o, h, l, c, swing_level_memory=m, theta_wick_min=1.0
    )
    for t_trunc in range(1, 4):
        m_trunc = SwingLevelMemory()
        m_trunc.update_swing_low(100.0, bar_index=0)
        trunc = detect_wick_reversal_setups(
            o[: t_trunc + 1], h[: t_trunc + 1], l[: t_trunc + 1], c[: t_trunc + 1],
            swing_level_memory=m_trunc, theta_wick_min=1.0,
        )
        # All setups in `trunc` should be a prefix of `full` (chronological).
        assert [s.bar_index for s in trunc] == [
            s.bar_index for s in full if s.bar_index <= t_trunc
        ]
