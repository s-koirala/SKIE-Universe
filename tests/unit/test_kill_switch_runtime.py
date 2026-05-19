"""Unit tests for [src/skie_ninja/backtest/kill_switch_runtime.py](../../src/skie_ninja/backtest/kill_switch_runtime.py).

Per ADR-0025 §D-1 + the Round 1 audit findings F-1-1 / F-1-2 / F-1-6 / F-1-7.
Includes the BLOCKING-CONCURRENT parity test
`P1-KILL-SWITCH-VALIDATOR-RUNTIME-PARITY-TEST` asserting the runtime module's
K-1..K-8 thresholds + tolerances match the post-hoc validator's via the shared
constants module.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from skie_ninja.backtest import kill_switch_constants as ksc
from skie_ninja.backtest import kill_switch_runtime as ksr
from skie_ninja.backtest import kill_switch_validation as ksv


class TestConstants:
    """K-1..K-8 thresholds + correlated-pair taxonomy."""

    def test_k1_stop_hit_tolerance_matches_validator(self):
        # Validator default at kill_switch_validation.py:116 = 1.05.
        # justify: parity-test for P1-KILL-SWITCH-VALIDATOR-RUNTIME-PARITY-TEST.
        assert ksc.K1_STOP_HIT_TOLERANCE_R == 1.05

    def test_k1_gap_through_tolerance_matches_validator(self):
        # Validator hardcoded gap-through cap at kill_switch_validation.py:138 = -3.0.
        assert ksc.K1_GAP_THROUGH_TOLERANCE_R == 3.0

    def test_k6_threshold_matches_validator(self):
        # Validator hardcoded daily threshold = -0.02 at kill_switch_validation.py:251.
        assert ksc.K6_DAILY_DRAWDOWN_THRESHOLD == -0.02

    def test_k7_threshold_matches_validator(self):
        # Validator hardcoded weekly threshold = -0.05 at kill_switch_validation.py:298.
        assert ksc.K7_WEEKLY_DRAWDOWN_THRESHOLD == -0.05

    def test_k5_taxonomy_covers_canonical_pairs(self):
        pairs = ksc.K5_CORRELATED_PAIRS
        assert frozenset({"ES", "MES"}) in pairs
        assert frozenset({"NQ", "MNQ"}) in pairs
        assert frozenset({"GC", "MGC"}) in pairs
        assert frozenset({"SI", "SIL"}) in pairs
        assert frozenset({"CL", "MCL"}) in pairs

    def test_session_date_function_delegates_to_clock(self):
        # F-1-1 audit fix: pin to CME session-clock, not UTC-naive .date().
        from skie_ninja.utils.clock import trading_day

        ts = pd.Timestamp("2025-06-16 15:00:00", tz="UTC")
        assert ksc.session_date_from_timestamp(ts) == trading_day(ts)

    def test_iso_week_id_from_session_date(self):
        from datetime import date

        d = date(2025, 6, 16)  # ISO week (2025, 24)
        iso_year, iso_week = ksc.iso_week_id_from_session_date(d)
        assert iso_year == 2025
        assert 1 <= iso_week <= 53


class TestUniverseValidationK5:
    """F-1-6 audit fix: K-5 N/A is universe-conditional."""

    def test_clean_universe_es_nq_mgc_sil_passes(self):
        # Canonical H062 v2 + H055 v2 universe.
        ksr.validate_universe_for_k5(("ES", "NQ", "MGC", "SIL"))

    def test_universe_with_es_and_mes_raises(self):
        with pytest.raises(ValueError, match="K-5"):
            ksr.validate_universe_for_k5(("ES", "MES", "NQ"))

    def test_universe_with_gc_and_mgc_raises(self):
        with pytest.raises(ValueError, match="K-5"):
            ksr.validate_universe_for_k5(("GC", "MGC", "SIL"))

    def test_universe_with_cl_and_mcl_raises(self):
        # H061 future universe per CLAUDE.md Phase O.0.
        with pytest.raises(ValueError, match="K-5"):
            ksr.validate_universe_for_k5(("CL", "MCL"))

    def test_universe_with_si_and_sil_raises(self):
        with pytest.raises(ValueError, match="K-5"):
            ksr.validate_universe_for_k5(("SI", "SIL"))

    def test_case_insensitivity(self):
        with pytest.raises(ValueError):
            ksr.validate_universe_for_k5(("es", "mes"))


class TestInitAndAdvance:
    def test_init_state_clean(self):
        state = ksr.init_runtime_state(
            universe=("ES", "NQ", "MGC", "SIL"), starting_equity=10_000.0
        )
        assert state.open_position_by_symbol == {}
        assert state.equity_at_session_start == 10_000.0
        assert state.current_session_date is None
        # Phase O.17 canonical 6-key schema per `P1-ADR-0028-SIZE-DOWN-
        # DISCLOSURE-DEFECT-CLOSE`: block-mode K-6/K-7 keys preserved
        # verbatim (block-mode v3 sidecars bit-exact reproducible);
        # K-6-size-down + K-7-size-down keys added for size-down mode.
        assert state.trigger_counts == {
            "K-3": 0,
            "K-4": 0,
            "K-6": 0,
            "K-6-size-down": 0,
            "K-7": 0,
            "K-7-size-down": 0,
        }

    def test_advance_session_sets_session_start_equity(self):
        from datetime import date

        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        state = ksr.advance_session(
            state, new_session_date=date(2025, 6, 16), current_equity=12_500.0
        )
        # F-1-7 audit fix: equity_at_session_start ratchets with current equity.
        assert state.equity_at_session_start == 12_500.0
        assert state.current_session_date == date(2025, 6, 16)
        assert state.daily_pnl_by_session_date[date(2025, 6, 16)] == 0.0

    def test_advance_week_sets_week_start_equity(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        state = ksr.advance_week(
            state, new_week_id=(2025, 24), current_equity=9_500.0
        )
        assert state.equity_at_week_start == 9_500.0
        assert state.current_week_id == (2025, 24)


class TestK3NoAddToLoser:
    """F-1-2 audit fix: K-3 requires open-position state."""

    def test_first_entry_unblocked(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k3=True)
        blocked, reason, sizing_modifier, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert not blocked
        assert sizing_modifier == 1.0

    def test_overlapping_entry_blocked_regardless_of_side(self):
        # F-1-2 fix: K-3 fires on same-symbol overlap regardless of side.
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k3=True)
        state = ksr.update_state_on_open(
            state,
            symbol="ES",
            side=1,
            entry_ts=pd.Timestamp("2025-06-16 14:00:00", tz="UTC"),
            entry_price=5000.0,
            position_size=1,
            stop_price=4990.0,
            r_dollar=500.0,
        )
        blocked, reason, sizing_modifier, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked
        assert reason == "K-3"
        assert sizing_modifier == 1.0

    def test_after_close_re_entry_unblocked(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k3=True)
        state = ksr.update_state_on_open(
            state,
            symbol="ES",
            side=1,
            entry_ts=pd.Timestamp("2025-06-16 14:00:00", tz="UTC"),
            entry_price=5000.0,
            position_size=1,
            stop_price=4990.0,
            r_dollar=500.0,
        )
        state = ksr.update_state_on_close(
            state,
            symbol="ES",
            realized_pnl_dollar=50.0,
            exit_ts=pd.Timestamp("2025-06-16 14:30:00", tz="UTC"),
        )
        blocked, reason, sizing_modifier, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert not blocked
        assert sizing_modifier == 1.0

    def test_k3_disabled_does_not_block(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k3=False)
        state = ksr.update_state_on_open(
            state,
            symbol="ES",
            side=1,
            entry_ts=pd.Timestamp("2025-06-16 14:00:00", tz="UTC"),
            entry_price=5000.0,
            position_size=1,
            stop_price=4990.0,
            r_dollar=500.0,
        )
        blocked, reason, sizing_modifier, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert not blocked
        assert sizing_modifier == 1.0


class TestK4CapacityCap:
    def test_size_within_cap_unblocked(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(
            enable_k4=True, capacity_caps={"ES": 20}
        )
        blocked, _, sizing_modifier, _state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=20
        )
        assert not blocked
        assert sizing_modifier == 1.0

    def test_size_above_cap_blocked(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(
            enable_k4=True, capacity_caps={"ES": 20}
        )
        blocked, reason, sizing_modifier, _state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=21
        )
        assert blocked
        assert reason == "K-4"
        # ADR-0028 §D-1: K-4 retains block-only; sizing_modifier is 1.0.
        assert sizing_modifier == 1.0


class TestK6DailyBreaker:
    """F-1-7 audit fix: current-equity ratcheting."""

    def test_under_threshold_unblocked(self):
        from datetime import date

        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        state = ksr.advance_session(
            state,
            new_session_date=date(2025, 6, 16),
            current_equity=10_000.0,
        )
        # Realised P/L -$150 = -1.5% of $10K (under -2% threshold).
        state = ksr.update_state_on_close(
            state,
            symbol="ES",
            realized_pnl_dollar=-150.0,
            exit_ts=pd.Timestamp("2025-06-16 14:30:00", tz="UTC"),
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k6=True)
        # Need to re-set current_session_date since update_on_close also routes by exit ts;
        # in our advance_session above we set 2025-06-16 explicitly, matches exit_ts trading_day.
        blocked, _, sizing_modifier, _state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert not blocked
        assert sizing_modifier == 1.0

    def test_over_threshold_blocked(self):
        from datetime import date

        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        state = ksr.advance_session(
            state,
            new_session_date=date(2025, 6, 16),
            current_equity=10_000.0,
        )
        # Realised P/L -$250 = -2.5% of $10K (over -2% threshold).
        state = ksr.update_state_on_close(
            state,
            symbol="ES",
            realized_pnl_dollar=-250.0,
            exit_ts=pd.Timestamp("2025-06-16 14:30:00", tz="UTC"),
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k6=True)
        blocked, reason, sizing_modifier, _state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked
        assert reason == "K-6"
        # Default k6_enforcement="block": sizing_modifier is 1.0 even on breach.
        assert sizing_modifier == 1.0

    def test_ratchets_with_session_start_equity(self):
        """F-1-7 fix: -2% of $5K starting-session equity = -$100 threshold."""
        from datetime import date

        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        # Session starts at $5K equity (post-drawdown).
        state = ksr.advance_session(
            state,
            new_session_date=date(2025, 6, 16),
            current_equity=5_000.0,
        )
        # Realised -$150 = -3% of $5K → over threshold (was -1.5% of starting).
        state = ksr.update_state_on_close(
            state,
            symbol="ES",
            realized_pnl_dollar=-150.0,
            exit_ts=pd.Timestamp("2025-06-16 14:30:00", tz="UTC"),
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k6=True)
        blocked, reason, _sizing, _state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked
        assert reason == "K-6"


class TestK7WeeklyBreaker:
    def test_over_threshold_blocked(self):
        from datetime import date

        # Derive the canonical week_id from the same session-date pipeline
        # that update_state_on_close uses, so advance_week + update_state_on_close
        # share the same dict key.
        sess_date = ksc.session_date_from_timestamp(
            pd.Timestamp("2025-06-16 14:30:00", tz="UTC")
        )
        week_id = ksc.iso_week_id_from_session_date(sess_date)

        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        state = ksr.advance_week(
            state, new_week_id=week_id, current_equity=10_000.0
        )
        state = ksr.update_state_on_close(
            state,
            symbol="ES",
            realized_pnl_dollar=-600.0,
            exit_ts=pd.Timestamp("2025-06-16 14:30:00", tz="UTC"),
        )
        state = ksr.advance_session(
            state, new_session_date=sess_date, current_equity=10_000.0,
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k7=True)
        blocked, reason, sizing_modifier, _state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked
        assert reason == "K-7"
        # Default k7_enforcement="block": sizing_modifier is 1.0 even on breach.
        assert sizing_modifier == 1.0


class TestTriggerCounts:
    def test_summarize_clean_state(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        summary = ksr.summarize_trigger_counts(state)
        assert summary["runtime_active"] is False
        assert summary["total_triggers"] == 0
        # Phase O.17: size_down_event_count field always present.
        assert summary["size_down_event_count"] == 0
        assert summary["annotation"] == "kill-switch-inactive"
        # Backward-compat: when config not supplied, mode_annotation absent.
        assert "mode_annotation" not in summary

    def test_summarize_after_trigger(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        state = ksr.record_trigger(state, "K-3")
        state = ksr.record_trigger(state, "K-3")
        state = ksr.record_trigger(state, "K-6")
        summary = ksr.summarize_trigger_counts(state)
        assert summary["runtime_active"] is True
        assert summary["total_triggers"] == 3
        assert summary["trigger_counts"]["K-3"] == 2
        assert summary["trigger_counts"]["K-6"] == 1
        # Block-mode-only triggers: size_down_event_count is 0.
        assert summary["size_down_event_count"] == 0
        assert summary["annotation"] == "kill-switch-active"

    def test_summarize_with_config_block_mode_annotation(self):
        # ADR-0028 §D-4: config-aware summary emits kill-switch-mode-block
        # when k6_enforcement="block" + k7_enforcement="block" (defaults).
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(enable_k6=True, enable_k7=True)
        summary = ksr.summarize_trigger_counts(state, config)
        assert summary["mode_annotation"] == "kill-switch-mode-block"
        assert summary["k6_enforcement"] == "block"
        assert summary["k7_enforcement"] == "block"
        assert summary["size_down_fraction"] == 0.5

    def test_summarize_with_config_size_down_k6(self):
        # ADR-0028 §D-4: aggregate annotation is "size-down" if EITHER K-6
        # or K-7 is in size_down mode.
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(
            enable_k6=True, enable_k7=True, k6_enforcement="size_down",
        )
        summary = ksr.summarize_trigger_counts(state, config)
        assert summary["mode_annotation"] == "kill-switch-mode-size-down"
        assert summary["k6_enforcement"] == "size_down"
        assert summary["k7_enforcement"] == "block"

    def test_summarize_with_config_size_down_both(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(
            enable_k6=True, enable_k7=True,
            k6_enforcement="size_down", k7_enforcement="size_down",
            size_down_fraction=0.25,
        )
        summary = ksr.summarize_trigger_counts(state, config)
        assert summary["mode_annotation"] == "kill-switch-mode-size-down"
        assert summary["size_down_fraction"] == 0.25


class TestSizeDownEnforcement:
    """ADR-0028 §D-1: K-6/K-7 size-down enforcement-mode enum."""

    def _build_breached_k6_state(self, current_equity: float = 10_000.0):
        """Helper: construct state with K-6 daily breach pre-registered."""
        from datetime import date

        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=current_equity
        )
        state = ksr.advance_session(
            state,
            new_session_date=date(2025, 6, 16),
            current_equity=current_equity,
        )
        # Realised -2.5% (over the -2% K-6 daily threshold).
        state = ksr.update_state_on_close(
            state, symbol="ES",
            realized_pnl_dollar=-0.025 * current_equity,
            exit_ts=pd.Timestamp("2025-06-16 14:30:00", tz="UTC"),
        )
        return state

    def _build_breached_k7_state(self, current_equity: float = 10_000.0):
        from datetime import date

        sess_date = ksc.session_date_from_timestamp(
            pd.Timestamp("2025-06-16 14:30:00", tz="UTC")
        )
        week_id = ksc.iso_week_id_from_session_date(sess_date)

        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=current_equity
        )
        state = ksr.advance_week(
            state, new_week_id=week_id, current_equity=current_equity
        )
        state = ksr.advance_session(
            state, new_session_date=sess_date, current_equity=current_equity
        )
        # Realised -6% weekly (over the -5% K-7 threshold).
        state = ksr.update_state_on_close(
            state, symbol="ES",
            realized_pnl_dollar=-0.06 * current_equity,
            exit_ts=pd.Timestamp("2025-06-16 14:30:00", tz="UTC"),
        )
        return state

    def test_default_block_mode_bit_exact_legacy_behavior(self):
        """Default `k6_enforcement="block"` must reproduce ADR-0025 §D-1 semantic.

        Construct an explicit K-6 breach scenario; verify the 4-tuple return
        carries `(True, "K-6", 1.0, state-unchanged-for-block-mode)`. This
        is the bit-exact equivalence test required by ADR-0028 §D-1 backward-
        compatibility contract.
        """
        state = self._build_breached_k6_state()
        config = ksr.KillSwitchRuntimeConfig(enable_k6=True)  # defaults to "block"

        blocked, reason, sizing_modifier, new_state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked is True
        assert reason == "K-6"
        assert sizing_modifier == 1.0
        # On "block" mode, size-down flag is NOT toggled (preserves legacy state).
        assert new_state.size_down_active_session is False

    def test_size_down_k6_returns_modifier(self):
        """K-6 breach under "size_down" mode returns (False, "K-6-size-down", 0.5).

        Phase O.17 `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` semantic:
        FRESH K-6 breach under size-down mode now emits reason `"K-6-size-down"`
        so the orchestrator's `record_trigger(state, reason)` call lands in
        the canonical 6-key dict. Prior to Phase O.17 the reason was the
        generic `"size-down-applied"` sentinel which was silently dropped
        by the orchestrator's keyset-iteration → sidecar-disclosure defect.
        """
        state = self._build_breached_k6_state()
        config = ksr.KillSwitchRuntimeConfig(
            enable_k6=True, k6_enforcement="size_down",
        )
        blocked, reason, sizing_modifier, new_state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked is False
        # Phase O.17: K-N-size-down specific reason emitted on FRESH breach.
        assert reason == "K-6-size-down"
        assert sizing_modifier == 0.5
        # ADR-0028 §D-1: size-down flag persists for the session.
        assert new_state.size_down_active_session is True
        assert new_state.size_down_active_week is False

    def test_size_down_k7_returns_modifier(self):
        """K-7 breach under "size_down" mode returns (False, "K-7-size-down", 0.5).

        Phase O.17: FRESH K-7 breach emits reason `"K-7-size-down"`.
        """
        state = self._build_breached_k7_state()
        config = ksr.KillSwitchRuntimeConfig(
            enable_k7=True, k7_enforcement="size_down",
        )
        blocked, reason, sizing_modifier, new_state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked is False
        # Phase O.17: K-N-size-down specific reason emitted on FRESH breach.
        assert reason == "K-7-size-down"
        assert sizing_modifier == 0.5
        assert new_state.size_down_active_week is True

    def test_size_down_custom_fraction(self):
        """Operator-supplied size_down_fraction is honored."""
        state = self._build_breached_k6_state()
        config = ksr.KillSwitchRuntimeConfig(
            enable_k6=True, k6_enforcement="size_down",
            size_down_fraction=0.25,
        )
        _, _, sizing_modifier, _ = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert sizing_modifier == 0.25

    def test_advance_session_resets_session_flag(self):
        """advance_session resets size_down_active_session to False."""
        from datetime import date

        state = self._build_breached_k6_state()
        # First trigger size-down to set the flag.
        config = ksr.KillSwitchRuntimeConfig(
            enable_k6=True, k6_enforcement="size_down",
        )
        _, _, _, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert state.size_down_active_session is True

        # Advance to next session → flag resets.
        state = ksr.advance_session(
            state, new_session_date=date(2025, 6, 17), current_equity=10_000.0
        )
        assert state.size_down_active_session is False

    def test_advance_week_resets_week_flag(self):
        """advance_week resets size_down_active_week to False."""
        state = self._build_breached_k7_state()
        config = ksr.KillSwitchRuntimeConfig(
            enable_k7=True, k7_enforcement="size_down",
        )
        _, _, _, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert state.size_down_active_week is True

        state = ksr.advance_week(
            state, new_week_id=(2025, 26), current_equity=10_000.0
        )
        assert state.size_down_active_week is False

    def test_size_down_sticky_within_session_no_breach(self):
        """Once size-down fires, all subsequent entries inherit modifier
        until session boundary even if breach 'resolves' on paper.
        """
        state = self._build_breached_k6_state()
        config = ksr.KillSwitchRuntimeConfig(
            enable_k6=True, k6_enforcement="size_down",
        )
        # First call sets the flag.
        _, _, m1, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert m1 == 0.5
        assert state.size_down_active_session is True

        # Simulate a recovering trade that mathematically returns daily
        # P/L above the K-6 threshold; the size-down flag must remain sticky
        # for the rest of the session per ADR-0028 §D-1 stickiness semantic.
        state = ksr.update_state_on_close(
            state, symbol="ES",
            realized_pnl_dollar=+500.0,  # net daily P/L now +$250
            exit_ts=pd.Timestamp("2025-06-16 15:00:00", tz="UTC"),
        )
        _, reason, m2, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert m2 == 0.5  # sticky
        assert reason == "size-down-applied"

    def test_k3_k4_retain_block_only_under_size_down_k6(self):
        """ADR-0028 §D-1 Out-of-scope: K-3 / K-4 retain block-only enforcement
        even when K-6 is in size_down mode.
        """
        state = self._build_breached_k6_state()
        # Open a position on ES so K-3 will block re-entry.
        state = ksr.update_state_on_open(
            state, symbol="ES", side=1,
            entry_ts=pd.Timestamp("2025-06-16 14:00:00", tz="UTC"),
            entry_price=5000.0, position_size=1,
            stop_price=4990.0, r_dollar=500.0,
        )
        config = ksr.KillSwitchRuntimeConfig(
            enable_k3=True, enable_k6=True, k6_enforcement="size_down",
        )
        # K-3 fires FIRST (structural invariant; precedes K-6 in order).
        blocked, reason, sizing_modifier, _ = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked is True
        assert reason == "K-3"
        assert sizing_modifier == 1.0  # K-3 retains block-only

    def test_size_down_k6_increments_trigger_counts(self):
        """Phase O.17 `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE`: a FRESH
        K-6 breach under size-down mode increments
        `state.trigger_counts["K-6-size-down"]` via the canonical orchestrator
        pattern (`record_trigger(state, reason)` with reason from
        `check_entry_blocked`); `summarize_trigger_counts.annotation` then
        returns `"kill-switch-active"` so the sidecar disclosure correctly
        reflects mechanism engagement.

        Pre-Phase-O.17 behaviour: reason was `"size-down-applied"` sentinel;
        `record_trigger` permissively added it as an extra key BUT the
        orchestrator's keyset-iteration dropped it at basket aggregation
        time → `runtime_active=false` + `annotation="kill-switch-inactive"`
        despite the size-down primitive having engaged.
        """
        state = self._build_breached_k6_state()
        config = ksr.KillSwitchRuntimeConfig(
            enable_k6=True, k6_enforcement="size_down",
        )
        _blocked, reason, _mod, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        # Phase O.17 contract: orchestrator records via the returned reason.
        state = ksr.record_trigger(state, reason)
        assert state.trigger_counts["K-6-size-down"] == 1
        # Block-mode K-6 unchanged at zero — bit-exact decomposition preserved.
        assert state.trigger_counts["K-6"] == 0

        summary = ksr.summarize_trigger_counts(state)
        assert summary["runtime_active"] is True
        assert summary["annotation"] == "kill-switch-active"
        assert summary["size_down_event_count"] == 1
        assert summary["total_triggers"] == 1

    def test_size_down_k7_increments_trigger_counts(self):
        """Symmetric: FRESH K-7 size-down breach increments
        `state.trigger_counts["K-7-size-down"]` and `kill-switch-active` fires.
        """
        state = self._build_breached_k7_state()
        config = ksr.KillSwitchRuntimeConfig(
            enable_k7=True, k7_enforcement="size_down",
        )
        _blocked, reason, _mod, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        state = ksr.record_trigger(state, reason)
        assert state.trigger_counts["K-7-size-down"] == 1
        assert state.trigger_counts["K-7"] == 0

        summary = ksr.summarize_trigger_counts(state)
        assert summary["runtime_active"] is True
        assert summary["annotation"] == "kill-switch-active"
        assert summary["size_down_event_count"] == 1

    def test_size_down_kill_switch_active_annotation_via_summary(self):
        """Annotation grammar verification: after a FRESH K-6 size-down
        breach + record_trigger landing in the canonical 6-key dict,
        `summarize_trigger_counts(state, config)` returns the orthogonal
        annotation pair:
          - `annotation = "kill-switch-active"` (ADR-0025 §D-5 runtime fire)
          - `mode_annotation = "kill-switch-mode-size-down"` (ADR-0028 §D-4 mode)
        These no longer contradict each other in size-down mode (pre-Phase-O.17
        bug: annotation was "kill-switch-inactive" + mode_annotation
        "kill-switch-mode-size-down" — operator-misleading).
        """
        state = self._build_breached_k6_state()
        config = ksr.KillSwitchRuntimeConfig(
            enable_k6=True, enable_k7=True, k6_enforcement="size_down",
        )
        _, reason, _, state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        state = ksr.record_trigger(state, reason)
        summary = ksr.summarize_trigger_counts(state, config)
        assert summary["annotation"] == "kill-switch-active"
        assert summary["mode_annotation"] == "kill-switch-mode-size-down"
        assert summary["k6_enforcement"] == "size_down"
        assert summary["k7_enforcement"] == "block"  # not enabled in size_down mode

    def test_block_mode_v3_sidecar_bit_exact_parity_invariant(self):
        """Load-bearing regression check: block-mode v3 sidecar at run_id
        `154237b365794244974068402b377191` carries non-zero counts in
        `trigger_counts.K-6` (4417) + `trigger_counts.K-7` (4428) and ZERO
        in `K-3` + `K-4` + (post-Phase-O.17) the two new `*-size-down` keys.
        The block-mode reason strings emitted by `check_entry_blocked` MUST
        remain `"K-6"` / `"K-7"` so the v3 sidecar reproduces bit-exactly
        when the post-Phase-O.17 primitive is invoked with default
        `k6_enforcement="block"` + `k7_enforcement="block"`.

        This test asserts the contract at the primitive layer; the actual
        v3 sidecar replay is verified by the full walk-forward determinism
        guarantees in the orchestrator + ReproLog binding.
        """
        # Build K-6 breach under block-mode default.
        state = self._build_breached_k6_state()
        config = ksr.KillSwitchRuntimeConfig(enable_k6=True)  # default "block"
        blocked, reason, sizing_modifier, _state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked is True
        # Phase O.17 contract: block-mode reason unchanged = "K-6".
        assert reason == "K-6"
        assert sizing_modifier == 1.0

        # Build K-7 breach under block-mode default.
        state = self._build_breached_k7_state()
        config = ksr.KillSwitchRuntimeConfig(enable_k7=True)  # default "block"
        blocked, reason, sizing_modifier, _state = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked is True
        # Phase O.17 contract: block-mode reason unchanged = "K-7".
        assert reason == "K-7"
        assert sizing_modifier == 1.0

    def test_validator_runtime_parity_unaffected_by_size_down(self):
        """ADR-0028 backward-compatibility: validator is post-hoc observation-
        only. The size-down mode emits sized-down trades which the validator
        sees as normal realized trades. No validator-side changes are required
        per the operator spec; this test asserts the parity invariant remains.

        Specifically: shared-constants module (K1, K6, K7 thresholds + the
        K-5 taxonomy) are unchanged by ADR-0028. Validator + runtime continue
        to read from the same source of truth.
        """
        from inspect import signature

        sig = signature(ksv.K1_per_trade_dollar_stop_within_1R)
        assert sig.parameters["tolerance_r"].default == ksc.K1_STOP_HIT_TOLERANCE_R
        assert ksc.K6_DAILY_DRAWDOWN_THRESHOLD == -0.02
        assert ksc.K7_WEEKLY_DRAWDOWN_THRESHOLD == -0.05
        # ADR-0028 §D-1 new constant (default size-down fraction).
        assert ksc.K_SIZE_DOWN_FRACTION_DEFAULT == 0.5


class TestParityWithValidator:
    """BLOCKING-CONCURRENT-WITH-ADR P1-KILL-SWITCH-VALIDATOR-RUNTIME-PARITY-TEST."""

    def test_k1_constants_shared(self):
        # Validator default at kill_switch_validation.py:116 = 1.05.
        # Runtime imports K1_STOP_HIT_TOLERANCE_R from constants.
        from inspect import signature

        sig = signature(ksv.K1_per_trade_dollar_stop_within_1R)
        validator_default = sig.parameters["tolerance_r"].default
        assert validator_default == ksc.K1_STOP_HIT_TOLERANCE_R

    def test_k5_taxonomy_covers_adr_0017(self):
        # ADR-0017 §5 K-5 lists ES/MES, NQ/MNQ, YM/MYM, GC/MGC, SI/SIL, CL/MCL.
        # Verify all 6 pairs in K5_CORRELATED_PAIRS.
        expected = {
            frozenset({"ES", "MES"}),
            frozenset({"NQ", "MNQ"}),
            frozenset({"YM", "MYM"}),
            frozenset({"GC", "MGC"}),
            frozenset({"SI", "SIL"}),
            frozenset({"CL", "MCL"}),
        }
        assert expected == set(ksc.K5_CORRELATED_PAIRS)
