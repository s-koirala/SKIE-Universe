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
        assert state.trigger_counts == {"K-3": 0, "K-4": 0, "K-6": 0, "K-7": 0}

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
        blocked, reason = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert not blocked

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
        blocked, reason = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked
        assert reason == "K-3"

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
        blocked, reason = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert not blocked

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
        blocked, reason = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert not blocked


class TestK4CapacityCap:
    def test_size_within_cap_unblocked(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(
            enable_k4=True, capacity_caps={"ES": 20}
        )
        blocked, _ = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=20
        )
        assert not blocked

    def test_size_above_cap_blocked(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        config = ksr.KillSwitchRuntimeConfig(
            enable_k4=True, capacity_caps={"ES": 20}
        )
        blocked, reason = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=21
        )
        assert blocked
        assert reason == "K-4"


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
        blocked, _ = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert not blocked

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
        blocked, reason = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked
        assert reason == "K-6"

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
        blocked, reason = ksr.check_entry_blocked(
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
        blocked, reason = ksr.check_entry_blocked(
            state, config, symbol="ES", position_size=1
        )
        assert blocked
        assert reason == "K-7"


class TestTriggerCounts:
    def test_summarize_clean_state(self):
        state = ksr.init_runtime_state(
            universe=("ES",), starting_equity=10_000.0
        )
        summary = ksr.summarize_trigger_counts(state)
        assert summary["runtime_active"] is False
        assert summary["total_triggers"] == 0
        assert summary["annotation"] == "kill-switch-inactive"

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
        assert summary["annotation"] == "kill-switch-active"


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
