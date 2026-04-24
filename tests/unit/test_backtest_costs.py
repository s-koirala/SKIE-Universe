"""Unit tests for nt8_es_nq_rth_v1 cost model.

Fee constants verified against config/instruments.yaml (2026-04-15 snapshot):
  ES/NQ: commission $0.85 + exchange $1.18 + NFA $0.02 = $2.05/side
  ES tick value: $12.50; NQ tick value: $5.00
  ES multiplier: $50; NQ multiplier: $20
"""

import math
import pytest

from skie_ninja.backtest.costs.nt8_es_nq_rth_v1 import NT8EsNqRthV1CostModel


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def model() -> NT8EsNqRthV1CostModel:
    return NT8EsNqRthV1CostModel()


@pytest.fixture
def model_2x() -> NT8EsNqRthV1CostModel:
    return NT8EsNqRthV1CostModel(sensitivity_mult=2.0)


# ---------------------------------------------------------------------------
# round_trip_cost — ES
# ---------------------------------------------------------------------------

def test_es_1contract_default(model: NT8EsNqRthV1CostModel) -> None:
    # 2 sides × 1 contract × (2.05 fixed + 12.50 slip) = 2 × 14.55 = 29.10
    assert math.isclose(model.round_trip_cost("ES", 1), 29.10, rel_tol=1e-9)


def test_es_2contracts_default(model: NT8EsNqRthV1CostModel) -> None:
    # 2 × 2 × 14.55 = 58.20
    assert math.isclose(model.round_trip_cost("ES", 2), 58.20, rel_tol=1e-9)


def test_es_lowercase(model: NT8EsNqRthV1CostModel) -> None:
    assert math.isclose(model.round_trip_cost("es", 1), 29.10, rel_tol=1e-9)


def test_es_2x_sensitivity(model_2x: NT8EsNqRthV1CostModel) -> None:
    # 2 × 1 × (2.05 + 2 × 12.50) = 2 × 27.05 = 54.10
    assert math.isclose(model_2x.round_trip_cost("ES", 1), 54.10, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# round_trip_cost — NQ
# ---------------------------------------------------------------------------

def test_nq_1contract_default(model: NT8EsNqRthV1CostModel) -> None:
    # 2 × 1 × (2.05 + 5.00) = 2 × 7.05 = 14.10
    assert math.isclose(model.round_trip_cost("NQ", 1), 14.10, rel_tol=1e-9)


def test_nq_2x_sensitivity(model_2x: NT8EsNqRthV1CostModel) -> None:
    # 2 × 1 × (2.05 + 2 × 5.00) = 2 × 12.05 = 24.10
    assert math.isclose(model_2x.round_trip_cost("NQ", 1), 24.10, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# round_trip_cost — MES / MNQ
# ---------------------------------------------------------------------------

def test_mes_1contract(model: NT8EsNqRthV1CostModel) -> None:
    # fixed per side MES: 0.35 + 0.35 + 0.02 = 0.72; slip = 1.25
    # 2 × 1 × (0.72 + 1.25) = 2 × 1.97 = 3.94
    assert math.isclose(model.round_trip_cost("MES", 1), 3.94, rel_tol=1e-9)


def test_mnq_1contract(model: NT8EsNqRthV1CostModel) -> None:
    # fixed per side MNQ: 0.72; slip = 0.50
    # 2 × 1 × (0.72 + 0.50) = 2 × 1.22 = 2.44
    assert math.isclose(model.round_trip_cost("MNQ", 1), 2.44, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# cost_per_bar_return
# ---------------------------------------------------------------------------

def test_flat_position_zero_cost(model: NT8EsNqRthV1CostModel) -> None:
    assert model.cost_per_bar_return("ES", 0, 4500.0) == 0.0


def test_es_cost_per_bar_return_positive(model: NT8EsNqRthV1CostModel) -> None:
    cost_frac = model.cost_per_bar_return("ES", 1, 4500.0, n_contracts=1)
    # round_trip_cost = 29.10; notional = 4500 × 50 = 225000
    expected = 29.10 / 225_000.0
    assert math.isclose(cost_frac, expected, rel_tol=1e-9)
    assert cost_frac > 0


def test_nq_cost_per_bar_return_positive(model: NT8EsNqRthV1CostModel) -> None:
    cost_frac = model.cost_per_bar_return("NQ", -1, 15000.0, n_contracts=1)
    # round_trip_cost = 14.10; notional = 15000 × 20 = 300000
    expected = 14.10 / 300_000.0
    assert math.isclose(cost_frac, expected, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# fee_breakdown
# ---------------------------------------------------------------------------

def test_fee_breakdown_es_keys(model: NT8EsNqRthV1CostModel) -> None:
    bd = model.fee_breakdown("ES")
    required = {
        "commission_per_side",
        "exchange_fee_per_side",
        "nfa_fee_per_side",
        "slippage_prior_per_side",
        "total_per_side",
        "total_round_trip_1_contract",
    }
    assert required <= set(bd.keys())


def test_fee_breakdown_es_total_consistency(model: NT8EsNqRthV1CostModel) -> None:
    bd = model.fee_breakdown("ES")
    # total_per_side = commission + exchange + nfa + slippage
    expected_per_side = (
        bd["commission_per_side"]
        + bd["exchange_fee_per_side"]
        + bd["nfa_fee_per_side"]
        + bd["slippage_prior_per_side"]
    )
    assert math.isclose(bd["total_per_side"], expected_per_side, rel_tol=1e-9)
    assert math.isclose(
        bd["total_round_trip_1_contract"], 2 * expected_per_side, rel_tol=1e-9
    )


def test_fee_breakdown_nq_commission(model: NT8EsNqRthV1CostModel) -> None:
    bd = model.fee_breakdown("NQ")
    assert math.isclose(bd["commission_per_side"], 0.85, rel_tol=1e-9)
    assert math.isclose(bd["nfa_fee_per_side"], 0.02, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Validation / error paths
# ---------------------------------------------------------------------------

def test_unknown_symbol_raises(model: NT8EsNqRthV1CostModel) -> None:
    with pytest.raises(ValueError, match="not in NT8EsNqRthV1"):
        model.round_trip_cost("CL", 1)


def test_zero_contracts_raises(model: NT8EsNqRthV1CostModel) -> None:
    with pytest.raises(ValueError, match="n_contracts"):
        model.round_trip_cost("ES", 0)


def test_negative_contracts_raises(model: NT8EsNqRthV1CostModel) -> None:
    with pytest.raises(ValueError, match="n_contracts"):
        model.round_trip_cost("ES", -1)


def test_zero_sensitivity_mult_raises() -> None:
    with pytest.raises(ValueError, match="sensitivity_mult"):
        NT8EsNqRthV1CostModel(sensitivity_mult=0.0)


def test_negative_sensitivity_mult_raises() -> None:
    with pytest.raises(ValueError, match="sensitivity_mult"):
        NT8EsNqRthV1CostModel(sensitivity_mult=-1.0)


def test_zero_price_raises(model: NT8EsNqRthV1CostModel) -> None:
    with pytest.raises(ValueError, match="Notional"):
        model.cost_per_bar_return("ES", 1, 0.0)


# ---------------------------------------------------------------------------
# Model ID
# ---------------------------------------------------------------------------

def test_cost_model_id() -> None:
    assert NT8EsNqRthV1CostModel.cost_model_id == "nt8_es_nq_rth_v1"


# ---------------------------------------------------------------------------
# Frozen dataclass immutability
# ---------------------------------------------------------------------------

def test_frozen_immutable(model: NT8EsNqRthV1CostModel) -> None:
    with pytest.raises((TypeError, AttributeError)):
        model.sensitivity_mult = 3.0  # type: ignore[misc]
