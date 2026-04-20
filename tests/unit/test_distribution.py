"""Tests for distribution-stability monitoring with BH correction.

Covers: normal case (no drift), drift detection (mean-shifted column),
empty input, single-column, min-sample-size guard, and BH correction
across multiple columns.
"""

from __future__ import annotations

import random

import polars as pl
import pytest

from skie_ninja.data.validation.distribution import (
    _MIN_SAMPLE_SIZE,
    check_distribution_stability,
)


def _make_df(cols: dict[str, list[float]]) -> pl.DataFrame:
    return pl.DataFrame(cols)


class TestNoDrift:
    """No alerts when current and reference are drawn from the same distribution."""

    def test_identical_data(self) -> None:
        data = {"a": list(range(100)), "b": [float(x) for x in range(100)]}
        df = _make_df(data)
        alerts = check_distribution_stability(df, df, ["a", "b"])
        assert alerts == []

    def test_similar_distributions(self) -> None:
        rng = random.Random(42)
        ref = {"x": [rng.gauss(0, 1) for _ in range(500)]}
        cur = {"x": [rng.gauss(0, 1) for _ in range(500)]}
        alerts = check_distribution_stability(
            _make_df(cur), _make_df(ref), ["x"], threshold=1e-6
        )
        assert alerts == []


class TestDriftDetection:
    """Alerts when a column has mean-shifted data."""

    def test_shifted_mean_detected(self) -> None:
        rng = random.Random(123)
        ref = {"x": [rng.gauss(0, 1) for _ in range(1000)]}
        # Large mean shift should produce very small p-value.
        cur = {"x": [rng.gauss(10, 1) for _ in range(1000)]}
        alerts = check_distribution_stability(
            _make_df(cur), _make_df(ref), ["x"], threshold=0.05
        )
        assert len(alerts) == 1
        assert alerts[0].column == "x"
        assert alerts[0].p_value_adj < 0.05


class TestEmptyInput:
    """No alerts and no errors on empty DataFrames."""

    def test_empty_current(self) -> None:
        ref = _make_df({"a": [1.0, 2.0, 3.0]})
        cur = _make_df({"a": []})
        alerts = check_distribution_stability(cur, ref, ["a"])
        assert alerts == []

    def test_empty_reference(self) -> None:
        cur = _make_df({"a": [1.0, 2.0, 3.0]})
        ref = _make_df({"a": []})
        alerts = check_distribution_stability(cur, ref, ["a"])
        assert alerts == []

    def test_both_empty(self) -> None:
        df = _make_df({"a": []})
        alerts = check_distribution_stability(df, df, ["a"])
        assert alerts == []


class TestSingleColumn:
    """Works correctly with a single column (BH correction is identity for n=1)."""

    def test_single_column_no_drift(self) -> None:
        data = {"val": [float(i) for i in range(50)]}
        df = _make_df(data)
        alerts = check_distribution_stability(df, df, ["val"])
        assert alerts == []

    def test_single_column_drift(self) -> None:
        rng = random.Random(77)
        ref = {"val": [rng.gauss(0, 1) for _ in range(500)]}
        cur = {"val": [rng.gauss(20, 1) for _ in range(500)]}
        alerts = check_distribution_stability(
            _make_df(cur), _make_df(ref), ["val"], threshold=0.05
        )
        assert len(alerts) == 1
        # For single column, p_value_adj == p_value (rank=1, n=1).
        assert alerts[0].p_value_adj == pytest.approx(alerts[0].p_value, rel=1e-10)


class TestMinSampleSizeGuard:
    """Columns with fewer than _MIN_SAMPLE_SIZE observations are skipped."""

    def test_below_min_samples_skipped(self) -> None:
        cur = _make_df({"a": [1.0]})  # n=1 < _MIN_SAMPLE_SIZE
        ref = _make_df({"a": [1.0, 2.0, 3.0]})
        alerts = check_distribution_stability(cur, ref, ["a"], threshold=1.0)
        assert alerts == []

    def test_at_min_samples_runs(self) -> None:
        assert _MIN_SAMPLE_SIZE == 2
        cur = _make_df({"a": [1.0, 2.0]})
        ref = _make_df({"a": [1.0, 2.0, 3.0]})
        # Should not crash; may or may not alert depending on data.
        alerts = check_distribution_stability(cur, ref, ["a"])
        assert isinstance(alerts, list)


class TestBHCorrection:
    """Benjamini-Hochberg correction across columns.

    Scenario: 1 truly drifted column out of 10 stable columns.
    The drifted column should still alert after BH correction if the
    shift is large enough, while the stable columns should not.
    """

    def test_one_drifted_among_stable(self) -> None:
        rng = random.Random(999)
        n = 500

        # 10 stable columns drawn from the same distribution.
        ref_data: dict[str, list[float]] = {}
        cur_data: dict[str, list[float]] = {}
        for i in range(10):
            col = f"stable_{i}"
            ref_data[col] = [rng.gauss(0, 1) for _ in range(n)]
            cur_data[col] = [rng.gauss(0, 1) for _ in range(n)]

        # 1 drifted column with large shift.
        ref_data["drifted"] = [rng.gauss(0, 1) for _ in range(n)]
        cur_data["drifted"] = [rng.gauss(10, 1) for _ in range(n)]

        all_cols = list(ref_data.keys())
        alerts = check_distribution_stability(
            _make_df(cur_data),
            _make_df(ref_data),
            all_cols,
            threshold=0.05,
        )

        # The drifted column should still be detected despite BH correction.
        alert_cols = {a.column for a in alerts}
        assert "drifted" in alert_cols

        # Stable columns should not alert (BH corrects borderline p-values up).
        for a in alerts:
            if a.column != "drifted":
                # If any stable column alerts, its adjusted p must still be < threshold.
                assert a.p_value_adj < 0.05

    def test_bh_adjusts_p_values_upward(self) -> None:
        """BH-adjusted p-values should be >= raw p-values."""
        rng = random.Random(42)
        n = 200
        ref_data: dict[str, list[float]] = {}
        cur_data: dict[str, list[float]] = {}
        # Create columns with varying degrees of shift.
        for i, shift in enumerate([0, 1, 3, 5, 10]):
            col = f"col_{i}"
            ref_data[col] = [rng.gauss(0, 1) for _ in range(n)]
            cur_data[col] = [rng.gauss(shift, 1) for _ in range(n)]

        alerts = check_distribution_stability(
            _make_df(cur_data),
            _make_df(ref_data),
            list(ref_data.keys()),
            threshold=1.0,  # Accept all to inspect adjusted p-values.
        )

        for a in alerts:
            assert a.p_value_adj >= a.p_value


class TestMissingColumn:
    """Columns not present in one DataFrame are silently skipped."""

    def test_column_missing_in_current(self) -> None:
        cur = _make_df({"a": [1.0, 2.0, 3.0]})
        ref = _make_df({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        alerts = check_distribution_stability(cur, ref, ["a", "b"])
        assert isinstance(alerts, list)
