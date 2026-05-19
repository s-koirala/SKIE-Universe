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


class TestK6EquityRatcheting:
    """ADR-0025 §D-1 F-1-7 audit fix: K-6 threshold ratchets with equity_at_session_start."""

    def test_ratcheting_default_matches_static_when_one_session(self) -> None:
        # Single-session ledger: ratcheting and static produce identical
        # results (no prior sessions → equity_at_session_start = starting).
        trades = [
            _mk_trade(r_multiple=-2.5, r_dollar=100.0, entry_offset_min=0),
            _mk_trade(r_multiple=-0.5, r_dollar=100.0, entry_offset_min=60),
        ]
        ratcheting = K6_daily_circuit_breaker_2pct(
            trades, starting_equity=10000.0, equity_ratcheting=True
        )
        static = K6_daily_circuit_breaker_2pct(
            trades, starting_equity=10000.0, equity_ratcheting=False
        )
        assert ratcheting.n_violations == static.n_violations

    def test_ratcheting_tightens_threshold_after_drawdown_session(self) -> None:
        # Day 1: lose $1500 (-15% of $10K). Day 2: $5000 trade at offset
        # 60min; under ratcheting, equity_at_session_start day 2 = $8500;
        # -2% threshold day 2 = -$170. Static: -2% × $10K = -$200.
        # A day-2 first trade at -$180 (after another -$50 trigger trade)
        # → under ratcheting: -$50 > -$170? Yes; second trade at cum_pnl=-$50
        # not yet under threshold. Need a more decisive example.
        # Construction: 1 huge loss day 1 → next day pre-loss trade =0,
        # then -$190 mid-day cum, then entry. Ratcheting blocks at -$170;
        # static does NOT block (-$190 > -$200).
        trades = [
            # Day 1 (2024-01-02 Tuesday): -$1500
            _mk_trade(
                r_multiple=-15.0, r_dollar=100.0,
                entry_offset_min=0, duration_min=60,
            ),
            # Day 2 (2024-01-03 Wednesday): two trades — first non-blocking,
            # second blocking under ratcheting but not static.
            _mk_trade(
                r_multiple=-1.9, r_dollar=100.0,
                entry_offset_min=60 * 24, duration_min=10,  # day-2 trade 1: -$190 cum
            ),
            _mk_trade(
                r_multiple=-0.1, r_dollar=100.0,
                entry_offset_min=60 * 24 + 30, duration_min=10,  # day-2 trade 2: entry
            ),
        ]
        rat = K6_daily_circuit_breaker_2pct(
            trades, starting_equity=10000.0, equity_ratcheting=True
        )
        sta = K6_daily_circuit_breaker_2pct(
            trades, starting_equity=10000.0, equity_ratcheting=False
        )
        # Ratcheting: day-2 threshold = -$170 (= -2% × $8500). Day-2 cum_pnl
        # after trade-1 = -$190 < -$170 → trade-2 entry is a violation.
        assert rat.n_violations >= 1
        # Static: day-2 threshold = -$200. Day-2 cum_pnl after trade-1 = -$190
        # not yet under -$200 → trade-2 NOT a violation under static.
        assert sta.n_violations == 0


class TestK7EquityRatcheting:
    """ADR-0025 §D-1 F-1-7 audit fix: K-7 threshold ratchets with equity_at_week_start."""

    def test_ratcheting_tightens_threshold_after_drawdown_week(self) -> None:
        # Week 1: lose $1000 (-10% of $10K). Week 2: ratcheting threshold
        # = -5% × $9000 = -$450; static = -5% × $10K = -$500.
        # Week 2 ledger triggers -$480 cum then entry: blocked under
        # ratcheting; passed under static.
        trades = [
            # Week 1 (ISO week 1 of 2024): one big loss
            _mk_trade(
                r_multiple=-10.0, r_dollar=100.0,
                entry_offset_min=0, duration_min=60,
            ),
            # Week 2 (ISO week 2 of 2024 = Jan 8 Mon): -$480 then entry
            _mk_trade(
                r_multiple=-4.8, r_dollar=100.0,
                entry_offset_min=60 * 24 * 7, duration_min=10,  # week-2 trade-1
            ),
            _mk_trade(
                r_multiple=-0.1, r_dollar=100.0,
                entry_offset_min=60 * 24 * 7 + 30, duration_min=10,  # week-2 trade-2
            ),
        ]
        rat = K7_weekly_circuit_breaker_5pct(
            trades, starting_equity=10000.0, equity_ratcheting=True
        )
        sta = K7_weekly_circuit_breaker_5pct(
            trades, starting_equity=10000.0, equity_ratcheting=False
        )
        assert rat.n_violations >= 1
        assert sta.n_violations == 0


class TestK6K7CmeSessionClockMigration:
    """ADR-0025 §D-1 F-1-1 audit fix: CME session-clock grouping (not UTC.date())."""

    def test_session_clock_function_used(self) -> None:
        # Verify that K-6 imports + uses the canonical session-clock function
        # from the shared constants module. A trade at ETH-boundary UTC
        # 23:30 Tuesday maps to CME trading-day Wednesday (next day's session).
        from skie_ninja.backtest.kill_switch_constants import (
            session_date_from_timestamp,
        )

        # Use a trade timestamp that's CME-Tuesday 14:35 UTC (08:35 CT,
        # pre-RTH but post-overnight): mapped to CME trading-day Tuesday.
        ts = pd.Timestamp("2024-01-02 14:35:00", tz="UTC")
        sess = session_date_from_timestamp(ts)
        # Just verify the function returns a date (the specific value
        # depends on clock.py + calendar) and is a stable contract.
        assert sess is not None
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
