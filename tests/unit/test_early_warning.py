"""Unit tests for the leading early-warning detector primitive (ADR-0029 §D-2).

Per `P1-EARLY-WARNING-DETECTOR-PRIMITIVE` / Phase P buildout P-2. Synthetic
regime-shift fixtures with deterministic RNG seeds.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.inference.early_warning import (
    CriticalSlowingDownResult,
    CusumResult,
    DrawdownResult,
    EarlyWarningConfig,
    EarlyWarningSignal,
    critical_slowing_down,
    cusum_lower,
    drawdown_under_water,
    early_warning_update,
    evaluate_early_warning,
    evaluate_early_warning_path,
    init_early_warning,
)


class TestCriticalSlowingDown:
    def test_rising_variance_positive_tau(self) -> None:
        rng = np.random.default_rng(0)
        low = rng.normal(0.0, 0.01, size=120)
        high = rng.normal(0.0, 0.05, size=120)
        path = np.concatenate([low, high])
        result = critical_slowing_down(path, window=40)
        assert isinstance(result, CriticalSlowingDownResult)
        assert result.variance_tau > 0.5

    def test_stationary_variance_tau_does_not_fire(self) -> None:
        rng = np.random.default_rng(7)
        path = rng.normal(0.0, 0.01, size=240)
        result = critical_slowing_down(path, window=60)
        assert result.variance_tau < 0.5

    def test_rising_autocorrelation_positive_ar1_tau(self) -> None:
        rng = np.random.default_rng(3)
        iid = rng.normal(0.0, 1.0, size=120)
        ar = np.empty(120)
        ar[0] = 0.0
        for t in range(1, 120):
            ar[t] = 0.85 * ar[t - 1] + rng.normal(0.0, 1.0)
        path = np.concatenate([iid, ar])
        result = critical_slowing_down(path, window=40)
        assert result.ar1_tau > 0.0

    def test_constant_series_zero_tau(self) -> None:
        result = critical_slowing_down(np.full(100, 0.001), window=30)
        assert result.variance_tau == 0.0
        assert result.ar1_tau == 0.0

    def test_n_windows_correct(self) -> None:
        result = critical_slowing_down(np.arange(100, dtype=float), window=30)
        assert result.n_windows == 100 - 30 + 1

    def test_window_too_small_raises(self) -> None:
        with pytest.raises(ValueError, match="window must be >= 3"):
            critical_slowing_down(np.zeros(50), window=2)

    def test_path_shorter_than_window_raises(self) -> None:
        with pytest.raises(ValueError, match="at least window"):
            critical_slowing_down(np.zeros(10), window=30)


class TestCusumLower:
    def test_downward_shift_fires_after_shift(self) -> None:
        rng = np.random.default_rng(1)
        pre = rng.normal(0.0, 0.1, size=50)
        post = rng.normal(-1.0, 0.1, size=50)
        deviations = np.concatenate([pre, post])
        result = cusum_lower(deviations, k=0.5, h=5.0)
        assert isinstance(result, CusumResult)
        assert result.first_alarm_index >= 50
        assert result.max_statistic > 5.0

    def test_stationary_zero_mean_no_alarm(self) -> None:
        rng = np.random.default_rng(2)
        deviations = rng.normal(0.0, 0.1, size=200)
        result = cusum_lower(deviations, k=0.5, h=5.0)
        assert result.first_alarm_index == -1

    def test_upward_drift_no_lower_alarm(self) -> None:
        deviations = np.full(100, 0.5)
        result = cusum_lower(deviations, k=0.1, h=2.0)
        assert result.first_alarm_index == -1
        assert result.max_statistic == 0.0

    def test_statistic_nonnegative(self) -> None:
        rng = np.random.default_rng(5)
        result = cusum_lower(rng.normal(0, 1, 100), k=0.5, h=5.0)
        assert np.all(result.statistic >= 0.0)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            cusum_lower(np.array([]), k=0.5, h=5.0)

    def test_negative_k_raises(self) -> None:
        with pytest.raises(ValueError, match="k .* must be >= 0"):
            cusum_lower(np.zeros(10), k=-0.1, h=5.0)

    def test_nonpositive_h_raises(self) -> None:
        with pytest.raises(ValueError, match="h .* must be > 0"):
            cusum_lower(np.zeros(10), k=0.5, h=0.0)


class TestDrawdownUnderWater:
    def test_known_path_hand_computed(self) -> None:
        log_returns = np.array([0.1, 0.1, -0.3, -0.1, 0.05])
        result = drawdown_under_water(log_returns)
        assert isinstance(result, DrawdownResult)
        # cum-log = [0.1, 0.2, -0.1, -0.2, -0.15]; peak = 0.2; dd_log = [0,0,-0.3,-0.4,-0.35]
        assert result.max_drawdown_fraction == pytest.approx(np.expm1(-0.4))
        assert result.current_drawdown_fraction == pytest.approx(np.expm1(-0.35))
        np.testing.assert_array_equal(result.time_under_water, np.array([0, 0, 1, 2, 3]))
        assert result.max_time_under_water == 3
        assert result.current_time_under_water == 3

    def test_monotone_up_zero_drawdown(self) -> None:
        result = drawdown_under_water(np.full(50, 0.01))
        assert result.max_drawdown_fraction == pytest.approx(0.0)
        assert result.max_time_under_water == 0

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            drawdown_under_water(np.array([]))


class TestEarlyWarningComposite:
    def test_regime_shift_fires(self) -> None:
        rng = np.random.default_rng(11)
        good = rng.normal(0.002, 0.01, size=80)
        decay = rng.normal(-0.012, 0.03, size=80)
        signal = evaluate_early_warning_path(np.concatenate([good, decay]))
        assert isinstance(signal, EarlyWarningSignal)
        assert signal.fired
        assert signal.annotation == "early-warning-fired"
        assert "drawdown" in signal.fired_layers  # robust gating layer on a decaying path
        assert signal.derisk_multiplier == 0.5

    def test_stable_regime_does_not_fire(self) -> None:
        # frozen in-regime reference (closed-loop-correct: established at deployment)
        rng = np.random.default_rng(13)
        path = rng.normal(0.003, 0.005, size=200)
        signal = evaluate_early_warning_path(path, reference_mean=0.003, reference_sigma=0.005)
        assert not signal.fired
        assert signal.annotation == "early-warning-armed"
        assert signal.derisk_multiplier == 1.0

    def test_csd_variance_advisory_does_not_gate_by_default(self) -> None:
        # seed 13: overlapping-window variance τ exceeds the cutoff on iid noise
        # (the false-positive the advisory default guards against); must NOT gate.
        # Frozen reference isolates the CSD layer (suppresses the CUSUM tripwire).
        rng = np.random.default_rng(13)
        path = rng.normal(0.003, 0.005, size=200)
        signal = evaluate_early_warning_path(path, reference_mean=0.003, reference_sigma=0.005)
        assert signal.csd_variance_fired
        assert "csd_variance" not in signal.fired_layers
        assert not signal.fired

    def test_csd_variance_gates_when_advisory_disabled(self) -> None:
        rng = np.random.default_rng(13)
        path = rng.normal(0.003, 0.005, size=200)
        cfg = EarlyWarningConfig(csd_variance_advisory_only=False)
        signal = evaluate_early_warning_path(path, cfg)
        assert "csd_variance" in signal.fired_layers
        assert signal.fired

    def test_flat_pnl_does_not_false_fire_cusum(self) -> None:
        # F-1 audit regression: a numerically-flat path (σ≈1e-18 from float rounding)
        # must not blow up the standardized CUSUM and false-fire. n > reference_window.
        signal = evaluate_early_warning_path(np.full(100, 0.01))
        assert not signal.cusum_fired
        assert "cusum" not in signal.fired_layers
        assert not signal.fired

    def test_cusum_fires_on_sustained_decay(self) -> None:
        # F-2 audit regression: CUSUM must fire on a genuine downward shift below the
        # LEADING in-regime baseline (deterministic fixture; no RNG-stream dependence).
        baseline = np.tile([0.01, -0.01], 30)  # 60 sessions, mean ~0, sigma ~0.01
        decay = np.full(60, -0.02)  # sustained below the regime mean
        signal = evaluate_early_warning_path(np.concatenate([baseline, decay]))
        assert signal.cusum_fired
        assert "cusum" in signal.fired_layers

    def test_leading_window_fallback_is_tripwire(self) -> None:
        # No frozen reference: the leading-window mean is a noisy in-regime estimate,
        # so the uncalibrated CUSUM can trip on a stable series (tripwire mode). Cost
        # is bounded: the de-risk is PARTIAL (0.5), reversed if BOCD never confirms.
        rng = np.random.default_rng(13)
        path = rng.normal(0.003, 0.005, size=200)
        signal = evaluate_early_warning_path(path)
        assert signal.cusum_fired
        assert signal.derisk_multiplier == 0.5

    def test_frozen_reference_anchors_cusum(self) -> None:
        path = np.full(120, -0.01)
        fires = evaluate_early_warning_path(path, reference_mean=0.0, reference_sigma=0.005)
        assert fires.cusum_fired
        no_fire = evaluate_early_warning_path(path, reference_mean=-0.01, reference_sigma=0.005)
        assert not no_fire.cusum_fired

    def test_insufficient_data_not_armed(self) -> None:
        signal = evaluate_early_warning_path(np.array([0.01]))
        assert not signal.armed
        assert signal.annotation == "early-warning-n/a"
        assert signal.derisk_multiplier == 1.0

    def test_composite_drawdown_matches_batch_primitive(self) -> None:
        rng = np.random.default_rng(17)
        path = rng.normal(-0.005, 0.02, size=150)
        signal = evaluate_early_warning_path(path)
        dd = drawdown_under_water(path)
        assert signal.drawdown_fraction == pytest.approx(dd.current_drawdown_fraction)
        assert signal.time_under_water == dd.current_time_under_water

    def test_ar1_advisory_does_not_gate_by_default(self) -> None:
        rng = np.random.default_rng(19)
        iid = rng.normal(0.001, 0.005, size=80)
        ar = np.empty(120)
        ar[0] = 0.001
        for t in range(1, 120):
            ar[t] = 0.9 * (ar[t - 1] - 0.001) + 0.001 + rng.normal(0.0, 0.005)
        path = np.concatenate([iid, ar])
        signal = evaluate_early_warning_path(path)
        assert "csd_ar1" not in signal.fired_layers

    def test_ar1_gates_when_advisory_disabled(self) -> None:
        rng = np.random.default_rng(19)
        iid = rng.normal(0.0, 1.0, size=80)
        ar = np.empty(120)
        ar[0] = 0.0
        for t in range(1, 120):
            ar[t] = 0.9 * ar[t - 1] + rng.normal(0.0, 1.0)
        path = np.concatenate([iid, ar])
        cfg = EarlyWarningConfig(ar1_advisory_only=False, window=40, csd_ar1_tau_threshold=0.3)
        signal = evaluate_early_warning_path(path, cfg)
        result = critical_slowing_down(path, window=40)
        if result.ar1_tau >= 0.3:
            assert "csd_ar1" in signal.fired_layers
        else:
            assert "csd_ar1" not in signal.fired_layers


class TestStreamingParity:
    def test_streaming_equals_batch(self) -> None:
        rng = np.random.default_rng(23)
        path = rng.normal(-0.002, 0.02, size=180)
        batch = evaluate_early_warning_path(path)

        state = init_early_warning()
        for x_t in path:
            early_warning_update(state, float(x_t))
        streamed = evaluate_early_warning(state)

        assert streamed == batch  # full frozen-dataclass equality (all fields scalar/tuple)
        assert streamed.n_observed == path.size

    def test_update_increments_n_observed(self) -> None:
        state = init_early_warning()
        for i in range(5):
            early_warning_update(state, 0.01 * i)
        assert state.n_observed == 5
        assert len(state.path) == 5


class TestConfigValidation:
    def test_window_too_small_raises(self) -> None:
        with pytest.raises(ValueError, match="window must be >= 3"):
            EarlyWarningConfig(window=2)

    def test_derisk_fraction_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="derisk_fraction must be in"):
            EarlyWarningConfig(derisk_fraction=1.5)

    def test_nonpositive_h_sigma_raises(self) -> None:
        with pytest.raises(ValueError, match="cusum_h_sigma must be > 0"):
            EarlyWarningConfig(cusum_h_sigma=0.0)

    def test_negative_drawdown_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="drawdown_fraction_threshold must be > 0"):
            EarlyWarningConfig(drawdown_fraction_threshold=-0.1)

    def test_tuw_threshold_too_small_raises(self) -> None:
        with pytest.raises(ValueError, match="tuw_threshold must be >= 1"):
            EarlyWarningConfig(tuw_threshold=0)

    def test_defaults_construct(self) -> None:
        cfg = EarlyWarningConfig()
        assert cfg.window == 60
        assert cfg.derisk_fraction == 0.5
        assert cfg.ar1_advisory_only is True


class TestInit:
    def test_init_with_explicit_config(self) -> None:
        cfg = EarlyWarningConfig(window=30)
        state = init_early_warning(cfg)
        assert state.config is cfg
        assert state.n_observed == 0

    def test_init_default_config(self) -> None:
        state = init_early_warning()
        assert isinstance(state.config, EarlyWarningConfig)
        assert state.n_observed == 0
