"""Unit tests for K-1..K-8 kill-switch backtest validation.

Per P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION (BLOCKING-BEFORE-NEXT-
NEW-HYPOTHESIS-LAUNCH per ADR-0017 §5).

Tests cover:
  - K-1: per-trade dollar-stop within 1.0R tolerance.
  - K-3: no add-to-loser (overlapping same-symbol trades).
  - K-4: per-symbol position cap.
  - K-6: daily circuit breaker -2% threshold.
  - K-7: weekly circuit breaker -5% threshold.
  - validate_kill_switches: aggregate validator.
"""

from __future__ import annotations

import pandas as pd
import pytest

from skie_ninja.backtest.kill_switch_validation import (
    K1_per_trade_dollar_stop_within_1R,
    K3_no_add_to_loser,
    K4_per_symbol_position_cap,
    K6_daily_circuit_breaker_2pct,
    K7_weekly_circuit_breaker_5pct,
    TradeRecord,
    validate_kill_switches,
)


def _mk_trade(
    symbol: str = "ES",
    side: int = 1,
    position_size: int = 1,
    r_multiple: float = 0.5,
    r_dollar: float = 100.0,
    exit_reason: str = "opposite_channel_break_long",
    entry_offset_min: int = 0,
    duration_min: int = 60,
) -> TradeRecord:
    base = pd.Timestamp("2024-01-02 14:35:00", tz="UTC")
    entry_ts = base + pd.Timedelta(minutes=entry_offset_min)
    exit_ts = entry_ts + pd.Timedelta(minutes=duration_min)
    return TradeRecord(
        symbol=symbol,
        entry_ts=entry_ts,
        exit_ts=exit_ts,
        side=side,
        position_size=position_size,
        entry_price=100.0,
        exit_price=100.0 + r_multiple * 2.0 * side,
        stop_price=100.0 - 2.0 * side,
        r_dollar=r_dollar,
        r_multiple=r_multiple,
        exit_reason=exit_reason,
        equity_at_entry=10000.0,
    )


class TestK1DollarStopWithin1R:
    def test_stop_hit_at_minus_1r_passes(self) -> None:
        trades = [_mk_trade(r_multiple=-1.0, exit_reason="stop_hit_long")]
        rep = K1_per_trade_dollar_stop_within_1R(trades)
        assert rep.passed

    def test_stop_hit_worse_than_minus_105r_fails(self) -> None:
        trades = [_mk_trade(r_multiple=-1.5, exit_reason="stop_hit_long")]
        rep = K1_per_trade_dollar_stop_within_1R(trades)
        assert not rep.passed
        assert rep.n_violations == 1

    def test_gap_through_stop_at_minus_2r_passes(self) -> None:
        # Gap-through tolerance is 3.0R; -2.0R passes
        trades = [_mk_trade(r_multiple=-2.0, exit_reason="gap_through_stop_long")]
        rep = K1_per_trade_dollar_stop_within_1R(trades)
        assert rep.passed

    def test_gap_through_at_minus_4r_fails(self) -> None:
        trades = [_mk_trade(r_multiple=-4.0, exit_reason="gap_through_stop_long")]
        rep = K1_per_trade_dollar_stop_within_1R(trades)
        assert not rep.passed

    def test_winner_trades_dont_trigger(self) -> None:
        trades = [_mk_trade(r_multiple=2.5, exit_reason="opposite_channel_break_long")]
        rep = K1_per_trade_dollar_stop_within_1R(trades)
        assert rep.passed


class TestK3NoAddToLoser:
    def test_non_overlapping_trades_pass(self) -> None:
        trades = [
            _mk_trade(symbol="ES", entry_offset_min=0, duration_min=10),
            _mk_trade(symbol="ES", entry_offset_min=20, duration_min=10),
        ]
        rep = K3_no_add_to_loser(trades)
        assert rep.passed

    def test_overlapping_same_symbol_fails(self) -> None:
        trades = [
            _mk_trade(symbol="ES", entry_offset_min=0, duration_min=30),
            _mk_trade(symbol="ES", entry_offset_min=10, duration_min=10),
        ]
        rep = K3_no_add_to_loser(trades)
        assert not rep.passed

    def test_overlapping_different_symbols_pass(self) -> None:
        trades = [
            _mk_trade(symbol="ES", entry_offset_min=0, duration_min=30),
            _mk_trade(symbol="NQ", entry_offset_min=10, duration_min=10),
        ]
        rep = K3_no_add_to_loser(trades)
        assert rep.passed


class TestK4PositionCap:
    def test_within_cap_passes(self) -> None:
        trades = [_mk_trade(symbol="ES", position_size=15)]
        rep = K4_per_symbol_position_cap(trades, capacity_caps={"ES": 20})
        assert rep.passed

    def test_exceeds_cap_fails(self) -> None:
        trades = [_mk_trade(symbol="ES", position_size=25)]
        rep = K4_per_symbol_position_cap(trades, capacity_caps={"ES": 20})
        assert not rep.passed


class TestK6DailyCircuitBreaker:
    def test_modest_daily_loss_passes(self) -> None:
        trades = [
            _mk_trade(r_multiple=-0.5, r_dollar=100.0, entry_offset_min=0),  # -$50
            _mk_trade(r_multiple=-0.5, r_dollar=100.0, entry_offset_min=60),  # -$50; cum -$100 = -1%
        ]
        rep = K6_daily_circuit_breaker_2pct(trades, starting_equity=10000.0)
        assert rep.passed

    def test_daily_loss_above_2pct_with_subsequent_entry_fails(self) -> None:
        trades = [
            _mk_trade(r_multiple=-2.5, r_dollar=100.0, entry_offset_min=0),  # -$250 = -2.5%
            _mk_trade(r_multiple=-0.5, r_dollar=100.0, entry_offset_min=60),  # entry AFTER threshold
        ]
        rep = K6_daily_circuit_breaker_2pct(trades, starting_equity=10000.0)
        assert not rep.passed
        assert rep.n_violations == 1


class TestK7WeeklyCircuitBreaker:
    def test_modest_weekly_loss_passes(self) -> None:
        trades = [
            _mk_trade(r_multiple=-1.0, r_dollar=100.0, entry_offset_min=0),
            _mk_trade(r_multiple=-1.0, r_dollar=100.0, entry_offset_min=60 * 24),
        ]
        rep = K7_weekly_circuit_breaker_5pct(trades, starting_equity=10000.0)
        assert rep.passed

    def test_weekly_loss_above_5pct_with_subsequent_entry_fails(self) -> None:
        # Single trade hitting -6% in one week, then next entry violates K-7
        trades = [
            _mk_trade(r_multiple=-6.0, r_dollar=100.0, entry_offset_min=0),  # -$600 = -6%
            _mk_trade(r_multiple=-0.5, r_dollar=100.0, entry_offset_min=60 * 24),  # next-day entry
        ]
        rep = K7_weekly_circuit_breaker_5pct(trades, starting_equity=10000.0)
        assert not rep.passed


class TestValidateKillSwitchesAggregate:
    def test_clean_ledger_all_pass(self) -> None:
        trades = [
            _mk_trade(r_multiple=0.5, entry_offset_min=0, duration_min=10),
            _mk_trade(r_multiple=-0.5, entry_offset_min=20, duration_min=10),
            _mk_trade(r_multiple=1.5, entry_offset_min=40, duration_min=10),
        ]
        result = validate_kill_switches(
            trades, capacity_caps={"ES": 20}, starting_equity=10000.0
        )
        assert result["all_passed"] is True
        assert result["n_trades_checked"] == 3
        assert "k_2_note" in result
        assert "k_5_note" in result
        assert "k_8_note" in result

    def test_violation_aggregates_correctly(self) -> None:
        trades = [
            _mk_trade(r_multiple=-1.5, exit_reason="stop_hit_long"),  # K-1 violation
        ]
        result = validate_kill_switches(
            trades, capacity_caps={"ES": 20}, starting_equity=10000.0
        )
        assert result["all_passed"] is False
        # K-1 should be the violator
        assert result["reports"]["K-1"]["n_violations"] == 1
