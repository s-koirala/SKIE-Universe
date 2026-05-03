"""Tests for src/skie_ninja/inference/calibration.py per plan v3-r3 §B."""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.inference.calibration import (
    BSSResult,
    binary_brier_score,
    binary_brier_skill_score,
    binary_bss_bootstrap_ci,
    cost_aware_binary_bss_kpi,
    fit_beta_calibration,
    fit_calibrator,
    multinomial_brier_score,
    multinomial_bss_kpi,
    predict_beta_calibration,
    predict_calibrated,
    reliability_slope_bootstrap_ci,
    reliability_slope_point,
    select_calibrator,
)


@pytest.fixture
def rng():
    return np.random.default_rng(42)


class TestBinaryBrier:
    def test_perfect_forecast_zero_brier(self):
        p = np.array([1.0, 0.0, 1.0, 0.0])
        y = np.array([1, 0, 1, 0])
        assert binary_brier_score(p, y) == 0.0

    def test_constant_0_5_against_balanced_y(self):
        p = np.array([0.5] * 100)
        y = np.array([1, 0] * 50)
        # mean of (0.5 - y)^2 = 0.25
        assert binary_brier_score(p, y) == pytest.approx(0.25)

    def test_bss_zero_under_climatology_predictor(self):
        rng = np.random.default_rng(7)
        y = rng.integers(0, 2, size=200)
        p_clim = np.full(len(y), float(np.mean(y)))
        assert binary_brier_skill_score(p_clim, y) == pytest.approx(0.0, abs=1e-9)

    def test_bss_one_under_perfect_forecast(self):
        y = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        p_perfect = y.astype(float)
        assert binary_brier_skill_score(p_perfect, y) == pytest.approx(1.0)


class TestBinaryBSSBootstrapCI:
    def test_returns_BSSResult_with_ci_band(self, rng):
        y = rng.integers(0, 2, size=300)
        p = rng.uniform(0.0, 1.0, size=300)
        result = binary_bss_bootstrap_ci(p, y, n_bootstrap=200, rng=rng)
        assert isinstance(result, BSSResult)
        assert result.bss_ci_lower <= result.bss_point <= result.bss_ci_upper
        assert result.n_obs == 300
        assert result.n_bootstrap == 200

    def test_perfect_forecast_lower_ci_above_zero(self, rng):
        y = rng.integers(0, 2, size=300)
        p = y.astype(float)
        result = binary_bss_bootstrap_ci(p, y, n_bootstrap=200, rng=rng, block_length=2.0)
        assert result.binding_gate_passed
        assert result.bss_ci_lower > 0.0

    def test_random_forecast_ci_brackets_zero(self, rng):
        y = rng.integers(0, 2, size=200)
        p_random = rng.uniform(0.0, 1.0, size=200)
        result = binary_bss_bootstrap_ci(p_random, y, n_bootstrap=200, rng=rng, block_length=2.0)
        assert result.bss_ci_lower < 0.0  # random forecast worse than climatology
        assert not result.binding_gate_passed


class TestReliabilitySlope:
    def test_perfect_forecast_slope_one(self, rng):
        # Use fully-mixing forecasts so binning has dispersion
        n = 300
        p = rng.uniform(0.05, 0.95, size=n)
        y = (rng.uniform(0, 1, size=n) < p).astype(int)
        slope, intercept = reliability_slope_point(p, y, n_bins=10)
        # Bayes-rate forecasts should give slope ≈ 1.0
        assert 0.7 < slope < 1.3

    def test_constant_forecast_returns_unit_slope_default(self):
        # Degenerate input should return the no-skill no-bias reference (1, 0)
        slope, intercept = reliability_slope_point([0.5] * 100, [0, 1] * 50, n_bins=10)
        assert slope == 1.0
        assert intercept == 0.0

    def test_bootstrap_ci_covers_one_under_calibrated_forecast(self, rng):
        n = 400
        p = rng.uniform(0.05, 0.95, size=n)
        y = (rng.uniform(0, 1, size=n) < p).astype(int)
        result = reliability_slope_bootstrap_ci(p, y, n_bootstrap=200, n_bins=10, rng=rng, block_length=2.0)
        assert result.binding_gate_passed
        assert result.slope_ci_lower <= 1.0 <= result.slope_ci_upper


class TestMultinomialBrier:
    def test_perfect_forecast_zero(self):
        Y = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        P = Y.astype(float)
        assert multinomial_brier_score(P, Y) == 0.0

    def test_uniform_forecast_against_balanced_classes(self):
        Y = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]] * 10)
        P = np.full(Y.shape, 1.0 / 3.0)
        # mean of sum_k (1/3 - Y_k)^2 = (2/9 + 4/9 + 4/9 + ...)/9 ... compute:
        # (1 - 1/3)^2 + 2 * (0 - 1/3)^2 = 4/9 + 2/9 = 6/9 = 2/3
        assert multinomial_brier_score(P, Y) == pytest.approx(2.0 / 3.0, abs=1e-9)

    def test_kpi_returns_result_with_ci(self, rng):
        n, K = 200, 5
        P = rng.dirichlet([1.0] * K, size=n)
        labels = rng.integers(0, K, size=n)
        Y = np.eye(K)[labels]
        result = multinomial_bss_kpi(P, Y, n_bootstrap=200, rng=rng, block_length=2.0)
        assert result.bss_ci_lower <= result.bss_point <= result.bss_ci_upper
        assert result.k_cells == K


class TestCalibratorSelection:
    def test_isotonic_at_n_500(self):
        choice = select_calibrator(n_cal=500)
        assert choice.name == "isotonic"
        assert not choice.fallback_triggered

    def test_platt_fallback_at_n_499(self):
        choice = select_calibrator(n_cal=499)
        assert choice.name == "platt"
        assert choice.fallback_triggered

    def test_fit_predict_isotonic_round_trip(self, rng):
        n = 600
        raw = rng.uniform(0.0, 1.0, size=n)
        y = (rng.uniform(0, 1, size=n) < raw).astype(int)
        model = fit_calibrator(raw, y)
        p_calib = predict_calibrated(model, raw)
        assert len(p_calib) == n
        assert (p_calib >= 0.0).all() and (p_calib <= 1.0).all()


class TestBetaCalibrationKPI:
    def test_fit_returns_three_floats(self, rng):
        n = 300
        raw = rng.uniform(0.05, 0.95, size=n)
        y = (rng.uniform(0, 1, size=n) < raw).astype(int)
        a, b, c = fit_beta_calibration(raw, y)
        assert all(isinstance(x, float) for x in (a, b, c))

    def test_predict_returns_probabilities(self, rng):
        n = 200
        raw = rng.uniform(0.05, 0.95, size=n)
        y = (rng.uniform(0, 1, size=n) < raw).astype(int)
        a, b, c = fit_beta_calibration(raw, y)
        p_cal = predict_beta_calibration(raw, a, b, c)
        assert (p_cal >= 0.0).all() and (p_cal <= 1.0).all()


class TestCostAwareBinaryBSSKPI:
    def test_at_c_zero_matches_binary_bss(self, rng):
        n = 300
        y = rng.normal(0, 1, size=n)
        p = (y > 0).astype(float) * 0.7 + 0.15  # weakly informative
        result_c0 = cost_aware_binary_bss_kpi(p, y, cost_c=0.0, n_bootstrap=200, rng=rng, block_length=2.0)
        # Compare against direct binary BSS on y > 0
        d = (y > 0).astype(float)
        bss_direct = binary_brier_skill_score(p, d)
        assert result_c0.bss_point == pytest.approx(bss_direct, abs=1e-9)
