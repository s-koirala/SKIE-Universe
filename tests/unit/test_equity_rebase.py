"""Unit tests for [src/skie_ninja/backtest/equity_rebase.py](../../src/skie_ninja/backtest/equity_rebase.py).

Per ADR-0025 §D-2 + F-1-3 audit fix.
"""

from __future__ import annotations

import pytest

from skie_ninja.backtest.equity_rebase import (
    EquityRebasePolicy,
    apply_pnl_to_equity,
    equity_for_sizing,
)


class TestEquityRebasePolicyValidation:
    def test_valid_construction(self):
        EquityRebasePolicy(
            mode="current", starting_equity=10_000.0, floor_equity_fraction=0.10
        )

    def test_invalid_starting_equity_raises(self):
        with pytest.raises(ValueError):
            EquityRebasePolicy(starting_equity=0)

    def test_invalid_floor_fraction_raises(self):
        with pytest.raises(ValueError):
            EquityRebasePolicy(floor_equity_fraction=1.5)
        with pytest.raises(ValueError):
            EquityRebasePolicy(floor_equity_fraction=-0.1)

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            EquityRebasePolicy(mode="other")


class TestFixedMode:
    def test_returns_starting_equity_always(self):
        policy = EquityRebasePolicy(mode="fixed", starting_equity=10_000.0)
        assert equity_for_sizing(policy, current_equity=5_000.0) == 10_000.0
        assert equity_for_sizing(policy, current_equity=50_000.0) == 10_000.0
        assert equity_for_sizing(policy, current_equity=0.0) == 10_000.0


class TestCurrentMode:
    def test_returns_current_above_floor(self):
        policy = EquityRebasePolicy(
            mode="current", starting_equity=10_000.0, floor_equity_fraction=0.10
        )
        assert equity_for_sizing(policy, current_equity=5_000.0) == 5_000.0
        assert equity_for_sizing(policy, current_equity=15_000.0) == 15_000.0

    def test_returns_floor_below_floor(self):
        # F-1-3 audit fix: documented operator-discretionary deviation from
        # strict Kelly at low-bankroll states; floors at 10% × starting.
        policy = EquityRebasePolicy(
            mode="current", starting_equity=10_000.0, floor_equity_fraction=0.10
        )
        assert equity_for_sizing(policy, current_equity=500.0) == 1_000.0
        assert equity_for_sizing(policy, current_equity=0.0) == 1_000.0
        assert equity_for_sizing(policy, current_equity=-500.0) == 1_000.0

    def test_zero_floor_disables(self):
        policy = EquityRebasePolicy(
            mode="current", starting_equity=10_000.0, floor_equity_fraction=0.0
        )
        assert equity_for_sizing(policy, current_equity=0.0) == 0.0


class TestMinOfCurrentAndStartingMode:
    """F-1-3 audit fix: Kelly-strict alternative."""

    def test_returns_starting_when_current_higher(self):
        policy = EquityRebasePolicy(
            mode="min_of_current_and_starting", starting_equity=10_000.0
        )
        assert equity_for_sizing(policy, current_equity=15_000.0) == 10_000.0

    def test_returns_current_when_starting_higher(self):
        policy = EquityRebasePolicy(
            mode="min_of_current_and_starting", starting_equity=10_000.0
        )
        assert equity_for_sizing(policy, current_equity=5_000.0) == 5_000.0

    def test_no_floor_below_zero(self):
        # Kelly-strict: bankrupted leg produces zero sizing per Vince 1990 Ch. 5.
        policy = EquityRebasePolicy(
            mode="min_of_current_and_starting", starting_equity=10_000.0
        )
        assert equity_for_sizing(policy, current_equity=0.0) == 0.0


class TestApplyPnlToEquity:
    def test_positive_pnl_increments(self):
        assert apply_pnl_to_equity(10_000.0, 150.0) == 10_150.0

    def test_negative_pnl_decrements(self):
        assert apply_pnl_to_equity(10_000.0, -200.0) == 9_800.0

    def test_floors_at_zero(self):
        """Vince 1990 *practitioner* Ch. 5 gambler's-ruin clamp."""
        assert apply_pnl_to_equity(100.0, -500.0) == 0.0
        assert apply_pnl_to_equity(0.0, -100.0) == 0.0
