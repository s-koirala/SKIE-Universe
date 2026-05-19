"""Unit tests for [src/skie_ninja/inference/bocd_live.py](../../src/skie_ninja/inference/bocd_live.py).

Per ADR-0025 §D-4 + F-1-4 (flap suppression + post-resume state) +
F-1-8 (UTC timestamps in pause-event log) audit fixes.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.inference.bocd_live import (
    BOCDLiveConfig,
    bocd_live_update,
    init_bocd_live,
    is_paused,
    manually_resume,
    summarize_pause_events,
)


class TestConfigValidation:
    def test_default_config_valid(self):
        BOCDLiveConfig()

    def test_invalid_hazard_rate_raises(self):
        with pytest.raises(ValueError):
            BOCDLiveConfig(hazard_rate=0)
        with pytest.raises(ValueError):
            BOCDLiveConfig(hazard_rate=2.0)

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            BOCDLiveConfig(window=1)

    def test_hysteresis_constraint(self):
        """re_entry_threshold must be strictly less than decay_threshold."""
        with pytest.raises(ValueError, match="hysteresis"):
            BOCDLiveConfig(decay_threshold=0.3, re_entry_threshold=0.5)
        with pytest.raises(ValueError, match="hysteresis"):
            BOCDLiveConfig(decay_threshold=0.3, re_entry_threshold=0.3)

    def test_min_pause_duration_positive(self):
        with pytest.raises(ValueError):
            BOCDLiveConfig(min_pause_duration_sessions=0)


class TestInit:
    def test_init_returns_active_state(self):
        config = BOCDLiveConfig()
        state = init_bocd_live(config)
        assert state.pause_active is False
        assert state.n_observed == 0
        assert state.pause_event_log == ()
        assert is_paused(state) is False


class TestPauseDetection:
    """F-1-4 + warmup-gate behavior."""

    def test_constant_signal_no_pause(self):
        """Constant input → posterior stays low → no pause."""
        config = BOCDLiveConfig(window=20, min_pause_duration_sessions=5)
        state = init_bocd_live(config)
        for i in range(50):
            state = bocd_live_update(
                state, x_t=0.0, session_idx=i, ts_utc=f"2025-06-{i+1:02d}T00:00:00Z"
            )
        # No change in signal → no pause expected.
        assert state.pause_active is False
        assert summarize_pause_events(state)["n_pause_events"] == 0

    def test_warmup_gate_blocks_early_detection(self):
        """First window/2 observations should not trigger pause regardless of signal."""
        # justify: matches batch primitive burn-in convention at bocd.py:354.
        config = BOCDLiveConfig(window=20, min_pause_duration_sessions=5)
        state = init_bocd_live(config)
        # Feed wildly noisy data for the first 5 observations (< window/2 = 10).
        for i in range(5):
            state = bocd_live_update(
                state,
                x_t=100.0 * ((-1) ** i),
                session_idx=i,
                ts_utc=f"2025-06-{i+1:02d}T00:00:00Z",
            )
        assert state.pause_active is False

    def test_regime_shift_triggers_pause(self):
        """Sharp regime shift after warmup → posterior crosses decay_threshold."""
        rng = np.random.default_rng(42)
        config = BOCDLiveConfig(
            window=20, min_pause_duration_sessions=5, decay_threshold=0.5
        )
        state = init_bocd_live(config)
        # 50 observations near mean 0.
        for i in range(50):
            state = bocd_live_update(
                state,
                x_t=float(rng.normal(0, 0.1)),
                session_idx=i,
                ts_utc=f"2025-06-15T00:00:{i:02d}Z",
            )
        # Sharp regime shift to mean +5; should detect.
        triggered = False
        for i in range(50, 80):
            state = bocd_live_update(
                state,
                x_t=float(rng.normal(5.0, 0.1)),
                session_idx=i,
                ts_utc=f"2025-06-15T01:00:{i-50:02d}Z",
            )
            if state.pause_active:
                triggered = True
                break
        assert triggered


class TestMinPauseDuration:
    """F-1-4 audit fix: hard floor on pause duration prevents flap."""

    def test_min_pause_duration_blocks_early_resume(self):
        rng = np.random.default_rng(42)
        config = BOCDLiveConfig(
            window=10,
            min_pause_duration_sessions=15,
            re_entry_threshold=0.10,
            decay_threshold=0.5,
        )
        state = init_bocd_live(config)
        # Trigger a pause.
        for i in range(15):
            state = bocd_live_update(
                state,
                x_t=float(rng.normal(0, 0.1)),
                session_idx=i,
                ts_utc=f"2025-06-15T00:00:{i:02d}Z",
            )
        for i in range(15, 40):
            state = bocd_live_update(
                state,
                x_t=float(rng.normal(5.0, 0.1)),
                session_idx=i,
                ts_utc=f"2025-06-15T01:00:{i-15:02d}Z",
            )
        # Now feed neutral signal — would normally drop posterior — but
        # min_pause_duration_sessions=15 blocks resume.
        if state.pause_active:
            entry_idx = state.pause_entered_session_idx
            for offset in range(5):  # < min_pause_duration
                state = bocd_live_update(
                    state,
                    x_t=0.0,
                    session_idx=40 + offset,
                    ts_utc=f"2025-06-15T02:00:{offset:02d}Z",
                )
            # Still paused — min_pause_duration not yet elapsed.
            assert state.pause_active


class TestReentryCriteria:
    def test_fixed_session_count_triggers_resume(self):
        rng = np.random.default_rng(42)
        config = BOCDLiveConfig(
            window=10,
            min_pause_duration_sessions=5,
            re_entry_criterion="fixed_session_count",
            re_entry_session_count=10,
            decay_threshold=0.5,
        )
        state = init_bocd_live(config)
        # Warmup + steady signal.
        for i in range(10):
            state = bocd_live_update(
                state,
                x_t=float(rng.normal(0, 0.1)),
                session_idx=i,
                ts_utc=f"2025-06-15T00:00:{i:02d}Z",
            )
        # Regime shift.
        for i in range(10, 30):
            state = bocd_live_update(
                state,
                x_t=float(rng.normal(5.0, 0.1)),
                session_idx=i,
                ts_utc=f"2025-06-15T01:00:{i-10:02d}Z",
            )
        # If paused, run 15 more sessions (exceeds re_entry_session_count=10).
        if state.pause_active:
            for i in range(30, 50):
                state = bocd_live_update(
                    state,
                    x_t=float(rng.normal(5.0, 0.1)),
                    session_idx=i,
                    ts_utc=f"2025-06-15T02:00:{i-30:02d}Z",
                )
                if not state.pause_active:
                    break
            assert not state.pause_active


class TestManualResume:
    def test_manual_resume_requires_manual_criterion(self):
        config = BOCDLiveConfig(re_entry_criterion="posterior_below_threshold")
        state = init_bocd_live(config)
        # Construct a paused state synthetically.
        from dataclasses import replace as dc_replace

        state = dc_replace(
            state, pause_active=True, sessions_since_pause=100
        )
        with pytest.raises(ValueError, match="manual"):
            manually_resume(state, session_idx=200, ts_utc="2025-06-15T00:00:00Z")

    def test_manual_resume_requires_min_pause_elapsed(self):
        from dataclasses import replace as dc_replace

        config = BOCDLiveConfig(
            re_entry_criterion="manual", min_pause_duration_sessions=10
        )
        state = init_bocd_live(config)
        state = dc_replace(
            state,
            pause_active=True,
            sessions_since_pause=5,
            pause_entered_session_idx=100,
            pause_entered_ts_utc="2025-06-15T00:00:00Z",
        )
        with pytest.raises(ValueError, match="min_pause_duration"):
            manually_resume(state, session_idx=200, ts_utc="2025-06-15T00:00:00Z")

    def test_manual_resume_records_event(self):
        from dataclasses import replace as dc_replace

        config = BOCDLiveConfig(
            re_entry_criterion="manual", min_pause_duration_sessions=5
        )
        state = init_bocd_live(config)
        state = dc_replace(
            state,
            pause_active=True,
            sessions_since_pause=10,
            pause_entered_session_idx=100,
            pause_entered_ts_utc="2025-06-15T00:00:00Z",
            pause_entered_posterior=0.8,
            last_observed_posterior=0.3,
        )
        resumed = manually_resume(
            state, session_idx=200, ts_utc="2025-06-15T05:00:00Z"
        )
        assert resumed.pause_active is False
        assert len(resumed.pause_event_log) == 1
        evt = resumed.pause_event_log[0]
        assert evt["pause_entered_session_idx"] == 100
        assert evt["pause_exited_session_idx"] == 200
        assert evt["re_entry_criterion"] == "manual"


class TestPauseEventLogStructure:
    """F-1-8 audit fix: dual session-idx + ts_utc encoding for replay-robustness."""

    def test_pause_event_carries_both_session_idx_and_ts_utc(self):
        from dataclasses import replace as dc_replace

        config = BOCDLiveConfig(
            re_entry_criterion="manual", min_pause_duration_sessions=5
        )
        state = init_bocd_live(config)
        state = dc_replace(
            state,
            pause_active=True,
            sessions_since_pause=10,
            pause_entered_session_idx=100,
            pause_entered_ts_utc="2025-06-15T00:00:00Z",
            pause_entered_posterior=0.8,
        )
        resumed = manually_resume(
            state, session_idx=200, ts_utc="2025-06-15T05:00:00Z"
        )
        evt = resumed.pause_event_log[0]
        # F-1-8: both encodings present.
        assert "pause_entered_session_idx" in evt
        assert "pause_entered_ts_utc" in evt
        assert "pause_exited_session_idx" in evt
        assert "pause_exited_ts_utc" in evt


class TestSummarize:
    def test_summary_clean(self):
        config = BOCDLiveConfig()
        state = init_bocd_live(config)
        summary = summarize_pause_events(state)
        assert summary["n_pause_events"] == 0
        assert summary["annotation"] == "bocd-live-active"

    def test_summary_with_completed_pause(self):
        from dataclasses import replace as dc_replace

        config = BOCDLiveConfig(
            re_entry_criterion="manual", min_pause_duration_sessions=5
        )
        state = init_bocd_live(config)
        state = dc_replace(
            state,
            pause_active=True,
            sessions_since_pause=10,
            pause_entered_session_idx=100,
            pause_entered_ts_utc="2025-06-15T00:00:00Z",
            pause_entered_posterior=0.8,
        )
        resumed = manually_resume(
            state, session_idx=200, ts_utc="2025-06-15T05:00:00Z"
        )
        summary = summarize_pause_events(resumed)
        assert summary["n_pause_events"] == 1
        assert summary["annotation"] == "bocd-live-pause"
        assert summary["total_sessions_paused"] == 10
        assert summary["longest_pause_run"] == 10


class TestStateImmutability:
    def test_update_returns_new_state(self):
        config = BOCDLiveConfig()
        state1 = init_bocd_live(config)
        state2 = bocd_live_update(
            state1, x_t=0.5, session_idx=0, ts_utc="2025-06-15T00:00:00Z"
        )
        assert state1 is not state2
        assert state1.n_observed == 0
        assert state2.n_observed == 1
