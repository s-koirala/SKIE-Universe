"""Unit tests for the ergodicity-sizing primitives (ADR-0029 §D-3 / Phase P P-3).

CPPI floor-ratchet + joint simultaneous-bet Kelly. Deterministic RNG seeds.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.sizing.ergodicity import (
    CPPIConfig,
    CPPIResult,
    JointKellyResult,
    cppi_risk_overlay,
    joint_kelly_fractions,
)


class TestCPPI:
    def test_hand_computed_overlay(self) -> None:
        # equity 10k, peak 12k, floor_fraction 0.8 → floor 9600, cushion 400,
        # m=4 → exposure 1600, scale min(1, 1600/10000) = 0.16.
        cfg = CPPIConfig(floor_fraction=0.8, multiplier=4.0)
        result = cppi_risk_overlay(10_000.0, 12_000.0, cfg)
        assert isinstance(result, CPPIResult)
        assert result.floor == pytest.approx(9_600.0)
        assert result.cushion == pytest.approx(400.0)
        assert result.exposure_dollars == pytest.approx(1_600.0)
        assert result.sizing_scale == pytest.approx(0.16)

    def test_floor_ratchets_with_peak(self) -> None:
        cfg = CPPIConfig(floor_fraction=0.8, multiplier=4.0)
        low = cppi_risk_overlay(10_000.0, 10_000.0, cfg)
        high = cppi_risk_overlay(10_000.0, 15_000.0, cfg)
        assert high.floor > low.floor  # higher peak → higher locked-in floor

    def test_sizing_scale_capped_at_one(self) -> None:
        # fresh high (equity == peak) with a large multiplier → scale clipped to 1.
        cfg = CPPIConfig(floor_fraction=0.5, multiplier=10.0)
        result = cppi_risk_overlay(10_000.0, 10_000.0, cfg)
        assert result.sizing_scale == 1.0

    def test_sizing_scale_zero_at_floor(self) -> None:
        # equity exactly at the floor → cushion 0 → scale 0 (fully de-risked).
        cfg = CPPIConfig(floor_fraction=0.8, multiplier=4.0)
        result = cppi_risk_overlay(8_000.0, 10_000.0, cfg)  # floor = 8000 = equity
        assert result.cushion == pytest.approx(0.0)
        assert result.sizing_scale == 0.0

    def test_sizing_scale_decreases_toward_floor(self) -> None:
        cfg = CPPIConfig(floor_fraction=0.8, multiplier=4.0)
        peak = 10_000.0
        eqs = (9_500.0, 9_000.0, 8_500.0)
        scales = [cppi_risk_overlay(eq, peak, cfg).sizing_scale for eq in eqs]
        assert scales[0] > scales[1] > scales[2]

    def test_min_floor_buffer_applies(self) -> None:
        # early (low peak) the ratcheting floor is below the ruin buffer → buffer wins.
        cfg = CPPIConfig(floor_fraction=0.5, multiplier=4.0)
        result = cppi_risk_overlay(10_000.0, 10_000.0, cfg, min_floor=6_000.0)
        assert result.floor == pytest.approx(6_000.0)  # max(5000 ratchet, 6000 buffer)

    def test_default_config_constructs(self) -> None:
        result = cppi_risk_overlay(10_000.0, 10_000.0)
        assert 0.0 <= result.sizing_scale <= 1.0

    def test_invalid_equity_raises(self) -> None:
        with pytest.raises(ValueError, match="equity must be positive"):
            cppi_risk_overlay(0.0, 10_000.0)

    def test_invalid_peak_raises(self) -> None:
        with pytest.raises(ValueError, match="running_peak_equity must be positive"):
            cppi_risk_overlay(10_000.0, 0.0)

    def test_negative_min_floor_raises(self) -> None:
        with pytest.raises(ValueError, match="min_floor must be non-negative"):
            cppi_risk_overlay(10_000.0, 10_000.0, min_floor=-1.0)

    def test_floor_fraction_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="floor_fraction must be in"):
            CPPIConfig(floor_fraction=1.0)

    def test_multiplier_nonpositive_raises(self) -> None:
        with pytest.raises(ValueError, match="multiplier must be > 0"):
            CPPIConfig(multiplier=0.0)


class TestJointKelly:
    def test_single_arm_reduces_to_1d(self) -> None:
        rng = np.random.default_rng(0)
        # modest edge → interior optimum (Kelly < cap), so the M=1 reduction is
        # demonstrated at an interior point, not pinned to the cap (F-1-4 audit).
        returns = rng.normal(0.008, 0.12, size=(400, 1))
        result = joint_kelly_fractions(returns, total_exposure_cap=1.0)
        assert isinstance(result, JointKellyResult)
        assert result.n_arms == 1
        assert 0.0 < result.fractions[0] < 0.99  # interior, not cap-pinned
        assert result.fractions[0] == pytest.approx(result.standalone_fractions[0], abs=0.02)

    def test_total_respects_cap(self) -> None:
        rng = np.random.default_rng(1)
        # strong-edge arms whose unconstrained optimum would exceed the cap.
        returns = rng.normal(0.02, 0.03, size=(300, 3))
        result = joint_kelly_fractions(returns, total_exposure_cap=0.25)
        assert result.total_fraction <= 0.25 + 1e-6

    def test_correlated_arms_avoid_overbet(self) -> None:
        rng = np.random.default_rng(2)
        # modest edge + high per_arm_cap → interior standalone (NOT cap-saturated),
        # so the over-bet avoidance reflects de-correlation, not the cap (F-1-3 audit).
        base = rng.normal(0.008, 0.12, size=400)
        col1 = base
        col2 = base + rng.normal(0.0, 1e-3, size=400)  # near-identical (highly correlated)
        returns = np.column_stack([col1, col2])
        result = joint_kelly_fractions(returns, total_exposure_cap=5.0, per_arm_cap=5.0)
        assert result.standalone_fractions[0] < 4.9  # interior, not cap-pinned
        # two copies of ~one bet: joint total ≈ single-arm Kelly = half the naive sum.
        assert result.total_fraction < result.sum_standalone_fractions
        assert result.total_fraction == pytest.approx(
            result.sum_standalone_fractions / 2.0, rel=0.15
        )

    def test_fractions_nonnegative(self) -> None:
        rng = np.random.default_rng(3)
        returns = rng.normal(0.005, 0.04, size=(300, 4))
        result = joint_kelly_fractions(returns, total_exposure_cap=1.0)
        assert np.all(result.fractions >= 0.0)

    def test_negative_edge_arm_gets_zero(self) -> None:
        rng = np.random.default_rng(4)
        good = rng.normal(0.015, 0.04, size=300)
        bad = rng.normal(-0.015, 0.04, size=300)
        returns = np.column_stack([good, bad])
        result = joint_kelly_fractions(returns, total_exposure_cap=1.0)
        assert result.fractions[1] == pytest.approx(0.0, abs=1e-3)
        assert result.fractions[0] > 0.0

    def test_growth_rate_positive_for_positive_edge(self) -> None:
        rng = np.random.default_rng(5)
        returns = rng.normal(0.01, 0.04, size=(300, 2))
        result = joint_kelly_fractions(returns, total_exposure_cap=1.0)
        assert result.growth_rate > 0.0

    def test_per_arm_cap_binds(self) -> None:
        rng = np.random.default_rng(6)
        returns = rng.normal(0.03, 0.03, size=(300, 2))
        result = joint_kelly_fractions(returns, total_exposure_cap=2.0, per_arm_cap=0.1)
        assert np.all(result.fractions <= 0.1 + 1e-6)

    def test_one_d_input_raises(self) -> None:
        with pytest.raises(ValueError, match="must be 2-D"):
            joint_kelly_fractions(np.zeros(10), total_exposure_cap=1.0)

    def test_too_few_rows_raises(self) -> None:
        with pytest.raises(ValueError, match="T >= 2"):
            joint_kelly_fractions(np.zeros((1, 3)), total_exposure_cap=1.0)

    def test_nonpositive_cap_raises(self) -> None:
        with pytest.raises(ValueError, match="total_exposure_cap must be > 0"):
            joint_kelly_fractions(np.zeros((10, 2)), total_exposure_cap=0.0)

    def test_nonpositive_per_arm_cap_raises(self) -> None:
        with pytest.raises(ValueError, match="per_arm_cap must be > 0"):
            joint_kelly_fractions(np.zeros((10, 2)), total_exposure_cap=1.0, per_arm_cap=0.0)

    def test_no_ruin_constraint_prevents_bankrupting_fraction(self) -> None:
        # F-1-1/F-1-2 audit: an arm with a deep loss period + a high cap must NOT
        # return a fraction that bankrupts on the loss period (worst gross > 0).
        returns = np.array([[0.5], [0.5], [0.5], [0.5], [-0.95]])
        result = joint_kelly_fractions(returns, total_exposure_cap=5.0)
        worst_gross = float(np.min(1.0 + returns[:, 0] * result.fractions[0]))
        assert worst_gross > 0.0
        assert not result.bankrupts_on_path
        assert np.isfinite(result.growth_rate)

    def test_converged_and_not_bankrupt_on_happy_path(self) -> None:
        rng = np.random.default_rng(7)
        returns = rng.normal(0.01, 0.04, size=(300, 2))
        result = joint_kelly_fractions(returns, total_exposure_cap=1.0)
        assert result.converged is True
        assert result.bankrupts_on_path is False

    def test_growth_rate_nonpositive_for_no_edge(self) -> None:
        rng = np.random.default_rng(8)
        returns = rng.normal(-0.01, 0.04, size=(300, 2))  # both negative edge
        result = joint_kelly_fractions(returns, total_exposure_cap=1.0)
        assert result.total_fraction == pytest.approx(0.0, abs=0.01)
        assert result.growth_rate <= 1e-9

    def test_standalone_fractions_nonnegative(self) -> None:
        rng = np.random.default_rng(9)
        returns = rng.normal(0.005, 0.04, size=(300, 3))
        result = joint_kelly_fractions(returns, total_exposure_cap=1.0)
        assert np.all(result.standalone_fractions >= 0.0)
