"""Unit tests for the MPV2 closed-loop pipeline (Phase P P-1 + P-4 + P-5).

Validates the full reward-matrix → correlation → bandit-selection → closed-loop →
paired-bootstrap-CI path on a deterministic regime-structured synthetic fixture
(NO real market data; P-1 real-arm re-emission is the operator-authorized compute).
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from scripts.run_mpv2_closed_loop import (
    _disposition,
    _normalize_date_key,
    build_calendar_aligned_reward_matrix,
    build_reward_matrix_from_sidecars,
    closed_loop_equity,
    cross_arm_correlation,
    evaluate_simultaneous_pooling,
    extract_arm_dated_stream,
    extract_arm_per_session,
    paired_bootstrap_ci,
    run_pipeline,
    synthetic_regime_matrix,
)
from skie_ninja.inference.early_warning import EarlyWarningConfig
from skie_ninja.sizing.ergodicity import CPPIConfig

_SEED = 20260602


class TestPipeline:
    def test_runs_and_compounds(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)
        arm_ids = [f"a{i}" for i in range(m.shape[1])]
        result = run_pipeline(m, arm_ids, rng_seed=_SEED, starting_equity=10_000.0)
        for key in (
            "correlation",
            "selected_bandit",
            "closed_loop_final_equity_ensemble_caveat",
            "closed_loop_mppm_rho_1_time_average",
            "closed_loop_vs_1_over_N_sized",
            "closed_loop_vs_1_over_N_selection",
            "beat_both_conjunctive",
            "disposition",
        ):
            assert key in result
        # the switcher captures the rotating regime winner → compounds above the start.
        assert result["closed_loop_final_equity_ensemble_caveat"] > 10_000.0
        # B&H not supplied in this call → conjunctive verdict is UNDETERMINED (None).
        assert result["beat_both_conjunctive"] is None
        assert (
            result["n_sessions_calibration"] + result["n_sessions_evaluation"]
            == result["n_sessions_total"]
        )

    def test_calibration_fraction_out_of_range_raises(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)
        with pytest.raises(ValueError, match="calibration_fraction must be in"):
            run_pipeline(m, [f"a{i}" for i in range(m.shape[1])], calibration_fraction=1.0)

    def test_passive_long_length_mismatch_raises(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)
        with pytest.raises(ValueError, match="passive_long length"):
            run_pipeline(
                m,
                [f"a{i}" for i in range(m.shape[1])],
                passive_long=np.zeros(m.shape[0] - 5),
            )

    def test_buy_and_hold_path_yields_conjunctive_verdict(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)
        passive = m.mean(axis=1)  # equal-weight underlying as a passive proxy
        result = run_pipeline(m, [f"a{i}" for i in range(m.shape[1])], passive_long=passive)
        assert result["closed_loop_vs_buy_and_hold"] is not None
        assert isinstance(result["beat_both_conjunctive"], bool)  # determinate when B&H supplied
        assert result["disposition"] in {"beat-both-conjunctive", "beat-one", "null"}

    def test_selection_beats_1n_point_estimate(self) -> None:
        # mechanism (not a seed fluke): an ideal switcher on rotating-winner regimes
        # selects the regime winner > 1/N-of-the-time, so the raw-selection mean diff
        # vs 1/N is positive. The per-session CI may still cover zero (honest).
        m = synthetic_regime_matrix(rng_seed=_SEED)
        result = run_pipeline(m, [f"a{i}" for i in range(m.shape[1])], rng_seed=_SEED)
        assert result["closed_loop_vs_1_over_N_selection"]["mean_diff"] > 0.0

    def test_too_few_arms_raises(self) -> None:
        with pytest.raises(ValueError, match="need >= 2 arms"):
            run_pipeline(np.zeros((100, 1)), ["a0"], rng_seed=_SEED)


class TestCorrelation:
    def test_decorrelated_arms_breadth_near_n(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)
        corr = cross_arm_correlation(m)
        n = m.shape[1]
        assert np.array(corr["correlation_matrix"]).shape == (n, n)
        assert 1.0 < corr["effective_breadth"] <= n
        assert corr["max_abs_offdiag"] < 0.5  # synthetic arms are de-correlated

    def test_identical_arms_breadth_collapses_to_one(self) -> None:
        rng = np.random.default_rng(_SEED)
        col = rng.normal(0.0, 0.01, size=300)
        m = np.column_stack([col, col])  # perfectly correlated
        corr = cross_arm_correlation(m)
        assert corr["effective_breadth"] == pytest.approx(1.0, abs=1e-6)
        assert corr["max_abs_offdiag"] == pytest.approx(1.0, abs=1e-6)


class TestPairedBootstrapCI:
    def test_excludes_zero_on_clearly_positive_diff(self) -> None:
        diff = np.full(300, 0.01)
        ci = paired_bootstrap_ci(diff, rng_seed=_SEED)
        assert ci["excludes_zero_positive"]
        assert ci["ci_lower_one_sided"] > 0.0

    def test_covers_zero_on_zero_mean_noise(self) -> None:
        rng = np.random.default_rng(_SEED)
        diff = rng.normal(0.0, 0.02, size=300)
        ci = paired_bootstrap_ci(diff, rng_seed=_SEED)
        assert not ci["excludes_zero_positive"]


class TestRewardMatrixBuilder:
    def test_reads_per_session_field(self, tmp_path) -> None:
        for arm in ("h050", "h060"):
            (tmp_path / arm).mkdir()
            (tmp_path / arm / "sidecar.json").write_text(
                json.dumps({"per_session_logret_aggregate": [0.01, -0.02, 0.005, 0.0]})
            )
        paths = {"h050": "h050/sidecar.json", "h060": "h060/sidecar.json"}
        matrix, arm_ids = build_reward_matrix_from_sidecars(paths, tmp_path)
        assert matrix.shape == (4, 2)
        assert arm_ids == ["h050", "h060"]

    def test_missing_field_raises_p1_message(self, tmp_path) -> None:
        (tmp_path / "h050").mkdir()
        (tmp_path / "h050" / "sidecar.json").write_text(json.dumps({"other": 1}))
        with pytest.raises(ValueError, match="per_session_logret_aggregate"):
            build_reward_matrix_from_sidecars({"h050": "h050/sidecar.json"}, tmp_path)

    def test_missing_sidecar_raises(self, tmp_path) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            build_reward_matrix_from_sidecars({"h050": "absent/sidecar.json"}, tmp_path)


class TestPerSessionExtractor:
    def test_sidecar_source(self, tmp_path) -> None:
        (tmp_path / "s.json").write_text(
            json.dumps({"per_session_logret_aggregate": [0.01, -0.02, 0.0]})
        )
        out = extract_arm_per_session({"kind": "sidecar", "path": "s.json"}, tmp_path)
        np.testing.assert_allclose(out, [0.01, -0.02, 0.0])

    def test_parquet_source_concats_symbols(self, tmp_path) -> None:
        import polars as pl

        for sym, vals in (("ES", [0.01, -0.02]), ("NQ", [0.03, 0.0, -0.01])):
            (tmp_path / sym).mkdir()
            pl.DataFrame(
                {"gated_return": vals, "unconditional_return": [0.0] * len(vals)}
            ).write_parquet(tmp_path / sym / "oos_returns.parquet")
        out = extract_arm_per_session(
            {"kind": "parquet", "run_dir": ".", "symbols": ["ES", "NQ"], "column": "gated_return"},
            tmp_path,
        )
        np.testing.assert_allclose(
            out, [0.01, -0.02, 0.03, 0.0, -0.01]
        )  # ES then NQ, positional concat

    def test_unknown_kind_raises(self, tmp_path) -> None:
        with pytest.raises(ValueError, match="unknown spec kind"):
            extract_arm_per_session({"kind": "bogus"}, tmp_path)

    def test_sidecar_missing_field_raises(self, tmp_path) -> None:
        (tmp_path / "s.json").write_text(json.dumps({"other": 1}))
        with pytest.raises(ValueError, match="per_session_logret_aggregate"):
            extract_arm_per_session({"kind": "sidecar", "path": "s.json"}, tmp_path)

    def test_parquet_no_files_raises(self, tmp_path) -> None:
        with pytest.raises(ValueError, match="no per-symbol oos_returns"):
            extract_arm_per_session(
                {"kind": "parquet", "run_dir": ".", "column": "gated_return"}, tmp_path
            )

    def test_truncates_to_shortest_arm(self, tmp_path) -> None:
        (tmp_path / "h050").mkdir()
        (tmp_path / "h050" / "sidecar.json").write_text(
            json.dumps({"per_session_logret_aggregate": [0.01, -0.02, 0.005, 0.0]})
        )
        (tmp_path / "h060").mkdir()
        (tmp_path / "h060" / "sidecar.json").write_text(
            json.dumps({"per_session_logret_aggregate": [0.01, -0.02, 0.005, 0.0, 0.01, 0.0]})
        )
        paths = {"h050": "h050/sidecar.json", "h060": "h060/sidecar.json"}
        matrix, _ = build_reward_matrix_from_sidecars(paths, tmp_path)
        assert matrix.shape == (4, 2)  # truncated to the shorter arm


class TestDisposition:
    @staticmethod
    def _ci(excl: bool) -> dict:
        return {"excludes_zero_positive": excl}

    def test_beat_both_conjunctive(self) -> None:
        assert _disposition(self._ci(True), self._ci(True)) == "beat-both-conjunctive"

    def test_beat_one(self) -> None:
        assert _disposition(self._ci(True), self._ci(False)) == "beat-one"
        assert _disposition(self._ci(False), self._ci(True)) == "beat-one"

    def test_null(self) -> None:
        assert _disposition(self._ci(False), self._ci(False)) == "null"

    def test_bh_not_evaluated_is_undetermined(self) -> None:
        assert _disposition(self._ci(True), None) == "beat-1N-BH-not-evaluated"
        assert _disposition(self._ci(False), None) == "null-vs-1N-BH-not-evaluated"


class TestClosedLoop:
    @staticmethod
    def _configs() -> dict:
        return {"cppi_config": CPPIConfig(), "ew_config": EarlyWarningConfig()}

    def test_arm_choices_wrong_length_raises(self) -> None:
        with pytest.raises(ValueError, match="arm_choices length"):
            closed_loop_equity(
                np.zeros((10, 3)),
                np.zeros(5, dtype=int),
                reference_mean=0.0,
                reference_sigma=0.01,
                starting_equity=10_000.0,
                **self._configs(),
            )

    def test_arm_choices_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="index out of range"):
            closed_loop_equity(
                np.zeros((10, 3)),
                np.full(10, 5, dtype=int),
                reference_mean=0.0,
                reference_sigma=0.01,
                starting_equity=10_000.0,
                **self._configs(),
            )

    def test_sized_and_raw_streams_have_session_length(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)[:60]
        out = closed_loop_equity(
            m,
            np.zeros(60, dtype=int),
            reference_mean=0.0,
            reference_sigma=0.01,
            starting_equity=10_000.0,
            **self._configs(),
        )
        assert out["sized_returns"].shape == (60,)
        assert out["raw_selected_returns"].shape == (60,)


class TestNormalizeDateKey:
    def test_tz_aware_timestamp_string(self) -> None:
        assert _normalize_date_key("2020-12-23 00:00:00+00:00") == "2020-12-23"

    def test_plain_date_string(self) -> None:
        assert _normalize_date_key("2024-01-05") == "2024-01-05"


class TestExtractArmDatedStream:
    def _write(self, tmp_path, name, payload):
        p = tmp_path / name
        p.write_text(json.dumps(payload))
        return {"path": str(p.relative_to(tmp_path))}

    def test_prefers_mpv2_arm_stream(self, tmp_path) -> None:
        spec = self._write(
            tmp_path,
            "h062.json",
            {"mpv2_arm_stream": {"dates": ["2024-01-02", "2024-01-03"], "logret": [0.01, -0.02]}},
        )
        out = extract_arm_dated_stream(spec, tmp_path)
        assert out == {"2024-01-02": 0.01, "2024-01-03": -0.02}

    def test_falls_back_to_per_session_fields(self, tmp_path) -> None:
        spec = self._write(
            tmp_path,
            "h060.json",
            {
                "per_session_dates": ["2021-06-01 00:00:00+00:00", "2021-06-02 00:00:00+00:00"],
                "per_session_logret_aggregate": [0.005, 0.003],
            },
        )
        out = extract_arm_dated_stream(spec, tmp_path)
        assert out == {"2021-06-01": 0.005, "2021-06-02": 0.003}

    def test_duplicate_date_raises(self, tmp_path) -> None:
        spec = self._write(
            tmp_path,
            "dup.json",
            {"mpv2_arm_stream": {"dates": ["2024-01-02", "2024-01-02"], "logret": [0.01, 0.02]}},
        )
        with pytest.raises(ValueError, match="duplicate date key"):
            extract_arm_dated_stream(spec, tmp_path)

    def test_length_mismatch_raises(self, tmp_path) -> None:
        spec = self._write(
            tmp_path,
            "mm.json",
            {"mpv2_arm_stream": {"dates": ["2024-01-02"], "logret": [0.01, 0.02]}},
        )
        with pytest.raises(ValueError, match="length mismatch"):
            extract_arm_dated_stream(spec, tmp_path)

    def test_no_dated_stream_raises(self, tmp_path) -> None:
        spec = self._write(tmp_path, "bad.json", {"per_session_logret_aggregate": [0.01]})
        with pytest.raises(ValueError, match="no dated stream"):
            extract_arm_dated_stream(spec, tmp_path)


class TestCalendarAlign:
    def _arm(self, tmp_path, name, dates, logret):
        p = tmp_path / name
        p.write_text(json.dumps({"mpv2_arm_stream": {"dates": dates, "logret": logret}}))
        return {"path": str(p.relative_to(tmp_path))}

    def test_intersection_and_matrix(self, tmp_path) -> None:
        d = ["2024-01-02", "2024-01-03", "2024-01-04"]
        a = self._arm(tmp_path, "a.json", d, [0.1, 0.2, 0.3])
        b = self._arm(tmp_path, "b.json", d[1:] + ["2024-01-05"], [0.4, 0.5, 0.6])
        matrix, ids, dates = build_calendar_aligned_reward_matrix({"A": a, "B": b}, tmp_path)
        assert ids == ["A", "B"]
        assert dates == ["2024-01-03", "2024-01-04"]
        np.testing.assert_allclose(matrix, np.array([[0.2, 0.4], [0.3, 0.5]]))

    def test_empty_intersection_raises(self, tmp_path) -> None:
        a = self._arm(tmp_path, "a.json", ["2024-01-02"], [0.1])
        b = self._arm(tmp_path, "b.json", ["2025-06-01"], [0.4])
        with pytest.raises(ValueError, match="empty calendar-date intersection"):
            build_calendar_aligned_reward_matrix({"A": a, "B": b}, tmp_path)

    def test_too_few_arms_raises(self, tmp_path) -> None:
        a = self._arm(tmp_path, "a.json", ["2024-01-02"], [0.1])
        with pytest.raises(ValueError, match="need >="):
            build_calendar_aligned_reward_matrix({"A": a}, tmp_path)


class TestSimultaneousPooling:
    def test_keys_and_disposition(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)
        out = evaluate_simultaneous_pooling(m, rng_seed=_SEED)
        for k in (
            "joint_kelly_fractions",
            "pooled_mppm_rho_1_time_average",
            "one_over_n_mppm_rho_1_time_average",
            "pooled_vs_1_over_N",
            "disposition",
        ):
            assert k in out
        assert out["pooled_vs_buy_and_hold"] is None  # no passive supplied
        assert out["one_over_n_vs_buy_and_hold"] is None

    def test_causal_fractions_ignore_eval_tail(self) -> None:
        # Look-ahead invariant: fractions are fit on the calibration head only, so
        # perturbing the EVAL tail must NOT change them.
        m = synthetic_regime_matrix(rng_seed=_SEED)
        t_cal = int(m.shape[0] * 0.30)
        m2 = m.copy()
        m2[t_cal:] *= 3.0  # perturb only the eval tail
        f1 = evaluate_simultaneous_pooling(m, rng_seed=_SEED)["joint_kelly_fractions"]
        f2 = evaluate_simultaneous_pooling(m2, rng_seed=_SEED)["joint_kelly_fractions"]
        np.testing.assert_allclose(f1, f2)

    def test_passive_supplied_populates_bh_cis(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)
        passive = np.full(m.shape[0], 0.001)
        out = evaluate_simultaneous_pooling(m, passive_long=passive, rng_seed=_SEED)
        assert out["pooled_vs_buy_and_hold"] is not None
        assert out["one_over_n_vs_buy_and_hold"] is not None
        assert out["buy_and_hold_mppm_rho_1_time_average"] is not None

    def test_passive_length_mismatch_raises(self) -> None:
        m = synthetic_regime_matrix(rng_seed=_SEED)
        with pytest.raises(ValueError, match="passive_long length"):
            evaluate_simultaneous_pooling(m, passive_long=np.zeros(5), rng_seed=_SEED)
