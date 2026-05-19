"""Unit tests for [src/skie_ninja/backtest/costs/nt8_realistic.py](../../src/skie_ninja/backtest/costs/nt8_realistic.py).

Per ADR-0025 §D-3 + F-1-5 audit fix.
"""

from __future__ import annotations

import math

import pytest

from skie_ninja.backtest.costs.nt8_realistic import (
    EmpiricalFeeOverride,
    NT8RealisticCostModel,
)


class TestCostModelConstruction:
    def test_default_construction(self):
        model = NT8RealisticCostModel()
        assert model.cost_model_id == "nt8_realistic_v1"
        assert model.sensitivity_mult == 1.0
        assert model.calibration_source == "conservative_prior"

    def test_invalid_sensitivity_mult_raises(self):
        with pytest.raises(ValueError):
            NT8RealisticCostModel(sensitivity_mult=0)
        with pytest.raises(ValueError):
            NT8RealisticCostModel(sensitivity_mult=-1.0)

    def test_paper_trade_empirical_requires_overrides(self):
        with pytest.raises(ValueError, match="paper_trade_empirical"):
            NT8RealisticCostModel(
                calibration_source="paper_trade_empirical",
                empirical_overrides={},
            )


class TestSymbolCoverage:
    @pytest.mark.parametrize(
        "symbol", ["ES", "NQ", "MES", "MNQ", "MGC", "SIL", "MCL"]
    )
    def test_all_symbols_supported(self, symbol):
        model = NT8RealisticCostModel()
        cost = model.round_trip_cost_usd(symbol, n_contracts=1)
        assert cost > 0

    def test_unknown_symbol_raises(self):
        model = NT8RealisticCostModel()
        with pytest.raises(ValueError, match="Symbol"):
            model.round_trip_cost_usd("UNKNOWN")


class TestRoundTripCostValues:
    def test_es_matches_legacy_nt8(self):
        """Parity with nt8_es_nq_rth_v1 for ES."""
        from skie_ninja.backtest.costs.nt8_es_nq_rth_v1 import NT8EsNqRthV1CostModel

        legacy = NT8EsNqRthV1CostModel()
        modern = NT8RealisticCostModel()
        assert modern.round_trip_cost_usd("ES") == legacy.round_trip_cost(
            "ES"
        )

    def test_nq_matches_legacy_nt8(self):
        from skie_ninja.backtest.costs.nt8_es_nq_rth_v1 import NT8EsNqRthV1CostModel

        legacy = NT8EsNqRthV1CostModel()
        modern = NT8RealisticCostModel()
        assert modern.round_trip_cost_usd("NQ") == legacy.round_trip_cost(
            "NQ"
        )

    def test_mgc_placeholder_cost_positive(self):
        # MGC fixed = 0.85 + 0.45 + 0.02 = 1.32 + slip 1.00 = 2.32/side; rt = 4.64
        model = NT8RealisticCostModel()
        cost = model.round_trip_cost_usd("MGC")
        assert math.isclose(cost, 2 * (1.32 + 1.00), abs_tol=1e-6)

    def test_n_contracts_scales_linearly(self):
        model = NT8RealisticCostModel()
        one_contract = model.round_trip_cost_usd("ES", n_contracts=1)
        five_contracts = model.round_trip_cost_usd("ES", n_contracts=5)
        assert math.isclose(five_contracts, 5 * one_contract)


class TestCostPerSessionLogReturn:
    def test_log_drag_negative(self):
        """log(1 - cost/notional) is negative for positive cost."""
        model = NT8RealisticCostModel()
        drag = model.cost_per_session_log_return(
            symbol="ES", entry_price=5000.0
        )
        assert drag < 0

    def test_zero_entry_price_raises(self):
        model = NT8RealisticCostModel()
        with pytest.raises(ValueError):
            model.cost_per_session_log_return(symbol="ES", entry_price=0.0)


class TestCostPerBarReturn:
    def test_zero_position_returns_zero(self):
        model = NT8RealisticCostModel()
        assert model.cost_per_bar_return("ES", position=0, price=5000.0) == 0.0

    def test_long_position_positive_drag(self):
        model = NT8RealisticCostModel()
        drag = model.cost_per_bar_return("ES", position=1, price=5000.0)
        assert drag > 0


class TestEmpiricalOverride:
    def test_override_replaces_conservative_prior(self):
        override = EmpiricalFeeOverride(
            fixed_per_side_usd=1.50,
            slip_per_side_usd=10.0,
            source="H062 paper-trade 2026-Q3",
            source_sha256="deadbeef" * 8,
            source_n_fills=500,
        )
        model = NT8RealisticCostModel(
            calibration_source="paper_trade_empirical",
            empirical_overrides={"ES": override},
        )
        cost = model.round_trip_cost_usd("ES")
        # 2 × (1.50 + 10.0) = 23.0 USD per round trip.
        assert math.isclose(cost, 23.0, abs_tol=1e-6)

    def test_sensitivity_mult_ignored_on_empirical_path(self):
        """F-1-5 audit fix: sensitivity_mult IGNORED when empirical override present."""
        override = EmpiricalFeeOverride(
            fixed_per_side_usd=1.50,
            slip_per_side_usd=10.0,
            source="paper-trade",
            source_sha256="x" * 64,
            source_n_fills=100,
        )
        model_1x = NT8RealisticCostModel(
            sensitivity_mult=1.0,
            calibration_source="paper_trade_empirical",
            empirical_overrides={"ES": override},
        )
        model_2x = NT8RealisticCostModel(
            sensitivity_mult=2.0,
            calibration_source="paper_trade_empirical",
            empirical_overrides={"ES": override},
        )
        # Both should produce identical cost — F-1-5 fix.
        assert model_1x.round_trip_cost_usd(
            "ES"
        ) == model_2x.round_trip_cost_usd("ES")

    def test_sensitivity_mult_applied_to_non_overridden_symbol(self):
        """Mixed: override for ES; sensitivity_mult still applies to NQ."""
        override = EmpiricalFeeOverride(
            fixed_per_side_usd=1.50,
            slip_per_side_usd=10.0,
            source="paper-trade",
            source_sha256="x" * 64,
            source_n_fills=100,
        )
        model_1x = NT8RealisticCostModel(
            sensitivity_mult=1.0,
            calibration_source="paper_trade_empirical",
            empirical_overrides={"ES": override},
        )
        model_2x = NT8RealisticCostModel(
            sensitivity_mult=2.0,
            calibration_source="paper_trade_empirical",
            empirical_overrides={"ES": override},
        )
        nq_1x = model_1x.round_trip_cost_usd("NQ")
        nq_2x = model_2x.round_trip_cost_usd("NQ")
        # NQ cost = 2 × (fixed + sensitivity_mult × slip); doubling sensitivity_mult
        # doubles only the slip component.
        # NQ fixed=2.05, slip=5.00; 1x rt=14.10, 2x rt=2×(2.05+10.0)=24.10
        assert math.isclose(nq_1x, 14.10, abs_tol=1e-6)
        assert math.isclose(nq_2x, 24.10, abs_tol=1e-6)

    def test_invalid_n_fills_raises(self):
        with pytest.raises(ValueError):
            EmpiricalFeeOverride(
                fixed_per_side_usd=1.0,
                slip_per_side_usd=1.0,
                source="x",
                source_sha256="x" * 64,
                source_n_fills=0,
            )


class TestFeeBreakdownProvenance:
    def test_es_verified_provenance(self):
        model = NT8RealisticCostModel()
        bd = model.fee_breakdown("ES")
        assert bd["provenance"] == "config_instruments_yaml_verified"

    def test_mgc_placeholder_provenance(self):
        model = NT8RealisticCostModel()
        bd = model.fee_breakdown("MGC")
        assert bd["provenance"] == "config_instruments_yaml_placeholder"

    def test_empirical_provenance(self):
        override = EmpiricalFeeOverride(
            fixed_per_side_usd=1.0,
            slip_per_side_usd=10.0,
            source="paper-trade",
            source_sha256="x" * 64,
            source_n_fills=100,
        )
        model = NT8RealisticCostModel(
            calibration_source="paper_trade_empirical",
            empirical_overrides={"ES": override},
        )
        bd = model.fee_breakdown("ES")
        assert bd["provenance"] == "paper_trade_empirical"
        assert bd["empirical_n_fills"] == 100


class TestKpiAnnotation:
    def test_conservative_prior_annotation(self):
        model = NT8RealisticCostModel()
        assert model.kpi_annotation() == "cost-conservative-prior"

    def test_empirical_annotation(self):
        override = EmpiricalFeeOverride(
            fixed_per_side_usd=1.0,
            slip_per_side_usd=10.0,
            source="paper-trade",
            source_sha256="x" * 64,
            source_n_fills=100,
        )
        model = NT8RealisticCostModel(
            calibration_source="paper_trade_empirical",
            empirical_overrides={"ES": override},
        )
        assert model.kpi_annotation() == "cost-empirical-calibrated"
