"""Tests for src/skie_ninja/backtest/costs/h053_cost_c.py per plan v3-r3 §B."""

from __future__ import annotations

import math

import pytest

from skie_ninja.backtest.costs.h053_cost_c import H053CostC, derive_cost_c


class TestH053CostCArithmetic:
    """Plan v3-r3 §B Round-1 plan-audit F-1-1 closure: cost-c is 1.06 / 0.35 bps, NOT 10.6 / 3.5."""

    def test_es_round_trip_usd_at_1_tick(self):
        c = H053CostC(symbol="ES", reference_price=5500.0, sensitivity_mult=1.0)
        assert c.round_trip_usd() == pytest.approx(29.10, abs=1e-9)

    def test_nq_round_trip_usd_at_1_tick(self):
        c = H053CostC(symbol="NQ", reference_price=20000.0, sensitivity_mult=1.0)
        assert c.round_trip_usd() == pytest.approx(14.10, abs=1e-9)

    def test_es_notional_at_5500(self):
        c = H053CostC(symbol="ES", reference_price=5500.0)
        assert c.notional_usd() == pytest.approx(275000.0, abs=1e-9)

    def test_nq_notional_at_20000(self):
        c = H053CostC(symbol="NQ", reference_price=20000.0)
        assert c.notional_usd() == pytest.approx(400000.0, abs=1e-9)

    def test_es_c_bps_1_tick_is_1_06_not_10_6(self):
        """Round-1 plan-audit F-1-1 anchor: 29.10 / 275000 * 1e4 ≈ 1.058 bps, NOT 10.58."""
        c = H053CostC(symbol="ES", reference_price=5500.0, sensitivity_mult=1.0)
        assert c.c_bps() == pytest.approx(1.058, abs=0.01)
        assert c.c_bps() < 2.0  # binding upper bound: NOT 10x

    def test_nq_c_bps_1_tick_is_0_35_not_3_5(self):
        c = H053CostC(symbol="NQ", reference_price=20000.0, sensitivity_mult=1.0)
        assert c.c_bps() == pytest.approx(0.353, abs=0.01)
        assert c.c_bps() < 1.0  # binding upper bound: NOT 10x

    def test_es_c_bps_2_tick_sensitivity(self):
        c = H053CostC(symbol="ES", reference_price=5500.0, sensitivity_mult=2.0)
        # 2 * (0.85 + 1.18 + 0.02 + 25.00) = 54.10; 54.10 / 275000 * 1e4 = 1.967
        assert c.c_bps() == pytest.approx(1.967, abs=0.01)

    def test_nq_c_bps_2_tick_sensitivity(self):
        c = H053CostC(symbol="NQ", reference_price=20000.0, sensitivity_mult=2.0)
        # 2 * (0.85 + 1.18 + 0.02 + 10.00) = 24.10; 24.10 / 400000 * 1e4 = 0.6025
        assert c.c_bps() == pytest.approx(0.602, abs=0.01)

    def test_c_log_return_consistency(self):
        c = H053CostC(symbol="ES", reference_price=5500.0)
        assert c.c_log_return() == pytest.approx(c.c_bps() * 1e-4, abs=1e-12)

    def test_invalid_symbol_raises(self):
        with pytest.raises(ValueError):
            H053CostC(symbol="UNKNOWN", reference_price=100.0).notional_usd()


class TestDeriveCostCSensitivityLadder:
    def test_default_returns_1_tick_and_2_tick(self):
        ladder = derive_cost_c("ES", 5500.0)
        assert set(ladder.keys()) == {"1-tick", "2-tick"}

    def test_1_tick_lt_2_tick(self):
        ladder = derive_cost_c("NQ", 20000.0)
        assert ladder["1-tick"].c_bps() < ladder["2-tick"].c_bps()
