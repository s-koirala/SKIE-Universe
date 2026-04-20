"""Unit tests for the macroeconomic surprise ingest pipeline.

Tests ALFRED JSON parsing, SPF CSV parsing, and surprise z-score
computation using vendored fixtures. No network calls.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from skie_ninja.data.ingest.macro_surprise import (
    compute_forecast_error_std,
    compute_spf_consensus,
    compute_surprise_z,
    parse_alfred_json,
    parse_spf_csv,
)

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

# Expected row counts from vendored fixtures.
_PAYEMS_FIXTURE_ROWS = 3
_PAYEMS_FIRST_VALUE = 157304.0
_SINGLE_VALID_ROW = 1
_KNOWN_ACTUAL = 200.0
_KNOWN_MEDIAN = 180.0
_KNOWN_STD = 15.0
_KNOWN_Z = (_KNOWN_ACTUAL - _KNOWN_MEDIAN) / _KNOWN_STD  # 1.333...
_SPF_N_FORECASTERS = 5
_MISSING_VALUE_VALID = 100.5


# ---------------------------------------------------------------------------
# ALFRED JSON parsing
# ---------------------------------------------------------------------------


class TestParseAlfredJson:
    """Tests for parse_alfred_json with vendored PAYEMS fixture."""

    @pytest.fixture()
    def payems_path(self) -> Path:
        return _FIXTURES / "alfred_payems_sample.json"

    def test_returns_list_of_dicts(self, payems_path: Path) -> None:
        rows = parse_alfred_json(payems_path)
        assert isinstance(rows, list)
        assert len(rows) == _PAYEMS_FIXTURE_ROWS

    def test_keys_present(self, payems_path: Path) -> None:
        rows = parse_alfred_json(payems_path)
        for row in rows:
            assert "obs_date" in row
            assert "value" in row
            assert "realtime_start" in row

    def test_values_are_float(self, payems_path: Path) -> None:
        rows = parse_alfred_json(payems_path)
        for row in rows:
            assert isinstance(row["value"], float)

    def test_first_observation(self, payems_path: Path) -> None:
        rows = parse_alfred_json(payems_path)
        assert rows[0]["obs_date"] == "2023-12-01"
        assert rows[0]["value"] == _PAYEMS_FIRST_VALUE
        assert rows[0]["realtime_start"] == "2024-01-05"

    def test_missing_value_skipped(self, tmp_path: Path) -> None:
        """FRED uses '.' for missing values; these should be dropped."""
        payload = {
            "observations": [
                {
                    "realtime_start": "2024-01-05",
                    "realtime_end": "2024-02-01",
                    "date": "2023-12-01",
                    "value": ".",
                },
                {
                    "realtime_start": "2024-02-02",
                    "realtime_end": "2024-03-07",
                    "date": "2024-01-01",
                    "value": "100.5",
                },
            ]
        }
        p = tmp_path / "test.json"
        p.write_text(json.dumps(payload))
        rows = parse_alfred_json(p)
        assert len(rows) == _SINGLE_VALID_ROW
        assert rows[0]["value"] == _MISSING_VALUE_VALID


# ---------------------------------------------------------------------------
# SPF CSV parsing
# ---------------------------------------------------------------------------


class TestParseSPFCsv:
    """Tests for parse_spf_csv with vendored fixture."""

    @pytest.fixture()
    def spf_path(self) -> Path:
        return _FIXTURES / "spf_individual_sample.csv"

    def test_returns_dataframe(self, spf_path: Path) -> None:
        df = parse_spf_csv(spf_path)
        assert isinstance(df, pl.DataFrame)

    def test_columns(self, spf_path: Path) -> None:
        df = parse_spf_csv(spf_path)
        assert set(df.columns) == {
            "forecast_date",
            "indicator",
            "forecaster_id",
            "value",
        }

    def test_non_empty(self, spf_path: Path) -> None:
        df = parse_spf_csv(spf_path)
        assert df.height > 0

    def test_indicator_extracted_from_filename(self, spf_path: Path) -> None:
        df = parse_spf_csv(spf_path)
        indicators = df["indicator"].unique().to_list()
        assert len(indicators) == _SINGLE_VALID_ROW
        assert indicators[0] == "spf_individual_sample"


class TestComputeSPFConsensus:
    """Tests for compute_spf_consensus."""

    def test_median_and_std(self) -> None:
        df = pl.DataFrame(
            {
                "forecast_date": [
                    date(2024, 1, 1),
                    date(2024, 1, 1),
                    date(2024, 1, 1),
                    date(2024, 1, 1),
                    date(2024, 1, 1),
                ],
                "indicator": ["UNEMP"] * _SPF_N_FORECASTERS,
                "forecaster_id": ["1", "2", "3", "4", "5"],
                "value": [3.6, 3.7, 3.8, 3.9, 4.0],
            }
        )
        consensus = compute_spf_consensus(df)
        assert consensus.height == _SINGLE_VALID_ROW
        row = consensus.row(0, named=True)
        assert row["consensus_median"] == pytest.approx(3.8, abs=1e-9)
        assert row["std_consensus"] > 0
        assert row["n_forecasters"] == _SPF_N_FORECASTERS

    def test_empty_input(self) -> None:
        df = pl.DataFrame(
            schema={
                "forecast_date": pl.Date,
                "indicator": pl.Utf8,
                "forecaster_id": pl.Utf8,
                "value": pl.Float64,
            }
        )
        consensus = compute_spf_consensus(df)
        assert consensus.height == 0


# ---------------------------------------------------------------------------
# Surprise z-score
# ---------------------------------------------------------------------------


class TestSurpriseZ:
    """Tests for compute_surprise_z."""

    def test_known_value(self) -> None:
        """Known example: actual=200, median=180, std=15 -> z=1.333."""
        z = compute_surprise_z(_KNOWN_ACTUAL, _KNOWN_MEDIAN, _KNOWN_STD)
        assert z == pytest.approx(_KNOWN_Z, abs=1e-9)

    def test_negative_surprise(self) -> None:
        z = compute_surprise_z(170.0, _KNOWN_MEDIAN, _KNOWN_STD)
        assert z is not None
        assert z < 0

    def test_zero_surprise(self) -> None:
        z = compute_surprise_z(_KNOWN_MEDIAN, _KNOWN_MEDIAN, _KNOWN_STD)
        assert z == pytest.approx(0.0)

    def test_none_when_median_missing(self) -> None:
        assert compute_surprise_z(_KNOWN_ACTUAL, None, _KNOWN_STD) is None

    def test_none_when_std_missing(self) -> None:
        assert compute_surprise_z(_KNOWN_ACTUAL, _KNOWN_MEDIAN, None) is None

    def test_none_when_std_zero(self) -> None:
        assert compute_surprise_z(_KNOWN_ACTUAL, _KNOWN_MEDIAN, 0.0) is None


# ---------------------------------------------------------------------------
# Forecast-error std proxy (ABDV 2003)
# ---------------------------------------------------------------------------

_FE_WINDOW = 10
_FE_WARMUP_WINDOW = 20
_FE_N_OBS = 50
_FE_WARMUP_N = 60


class TestForecastErrorStd:
    """Tests for compute_forecast_error_std."""

    def test_returns_columns(self) -> None:
        dates = [
            date(2020, 1, 1) + timedelta(days=30 * i)
            for i in range(_FE_N_OBS)
        ]
        df = pl.DataFrame(
            {
                "obs_date": dates,
                "indicator": ["PAYEMS"] * _FE_N_OBS,
                "value": list(range(_FE_N_OBS)),
            }
        )
        result = compute_forecast_error_std(df, window_q=_FE_WINDOW)
        assert set(result.columns) == {
            "obs_date",
            "indicator",
            "forecast_error_std",
        }

    def test_empty_input(self) -> None:
        df = pl.DataFrame(
            schema={
                "obs_date": pl.Date,
                "indicator": pl.Utf8,
                "value": pl.Float64,
            }
        )
        result = compute_forecast_error_std(df)
        assert result.height == 0

    def test_std_positive_after_warmup(self) -> None:
        rng = np.random.default_rng(42)
        dates = [
            date(2015, 1, 1) + timedelta(days=30 * i)
            for i in range(_FE_WARMUP_N)
        ]
        values = (100 + rng.standard_normal(_FE_WARMUP_N) * 5).tolist()
        df = pl.DataFrame(
            {
                "obs_date": dates,
                "indicator": ["TEST"] * _FE_WARMUP_N,
                "value": values,
            }
        )
        result = compute_forecast_error_std(df, window_q=_FE_WARMUP_WINDOW)
        # After warmup, std should be positive
        non_null = result.filter(
            pl.col("forecast_error_std").is_not_null()
        )
        assert non_null.height > 0
        assert all(
            v > 0 for v in non_null["forecast_error_std"].to_list()
        )
