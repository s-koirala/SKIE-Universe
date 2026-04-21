"""Tests for pandera-polars schemas (FOMC text + macro surprise)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandera.errors
import polars as pl
import pytest

from skie_ninja.data.validation.schema import FomcTextSchema, MacroSurpriseSchema

# ---------------------------------------------------------------------------
# FOMC text fixtures
# ---------------------------------------------------------------------------


def _valid_fomc_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "release_ts_utc": [
                datetime(2024, 1, 31, 19, 0, tzinfo=UTC),
                datetime(2024, 3, 20, 18, 0, tzinfo=UTC),
            ],
            "embargo_ts_utc": [
                datetime(2024, 1, 31, 14, 0, tzinfo=UTC),
                datetime(2024, 3, 20, 14, 0, tzinfo=UTC),
            ],
            "doc_type": ["statement", "minutes"],
            "sha256": ["a" * 64, "b" * 64],
            "raw_path": ["/data/raw/fomc/2024-01-31.html", "/data/raw/fomc/2024-03-20.html"],
            "text_normalized": ["The Committee decided...", "Minutes of the meeting..."],
        }
    )


def _invalid_fomc_doc_type() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "release_ts_utc": [datetime(2024, 1, 31, 19, 0, tzinfo=UTC)],
            "embargo_ts_utc": [datetime(2024, 1, 31, 14, 0, tzinfo=UTC)],
            "doc_type": ["speech"],  # invalid
            "sha256": ["a" * 64],
            "raw_path": ["/data/raw/fomc/2024-01-31.html"],
            "text_normalized": ["Some text"],
        }
    )


def _duplicate_fomc_df() -> pl.DataFrame:
    ts = datetime(2024, 1, 31, 19, 0, tzinfo=UTC)
    emb = datetime(2024, 1, 31, 14, 0, tzinfo=UTC)
    return pl.DataFrame(
        {
            "release_ts_utc": [ts, ts],
            "embargo_ts_utc": [emb, emb],
            "doc_type": ["statement", "statement"],  # duplicate (release_ts_utc, doc_type)
            "sha256": ["a" * 64, "b" * 64],
            "raw_path": ["/a.html", "/b.html"],
            "text_normalized": ["text1", "text2"],
        }
    )


# ---------------------------------------------------------------------------
# Macro surprise fixtures
# ---------------------------------------------------------------------------


def _valid_macro_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "release_date": [date(2024, 1, 5), date(2024, 2, 2)],
            "release_ts_utc": [
                datetime(2024, 1, 5, 13, 30, tzinfo=UTC),
                datetime(2024, 2, 2, 13, 30, tzinfo=UTC),
            ],
            "event_id": ["NFP_2024_01", "NFP_2024_02"],
            "indicator": ["nonfarm_payrolls", "nonfarm_payrolls"],
            "actual": [216.0, 353.0],
            "consensus_median": [175.0, 185.0],
            "std_consensus": [20.0, 25.0],
            "surprise_z": [2.05, 6.72],
            "source": ["BLS", "BLS"],
            "vintage_date": [date(2024, 1, 5), date(2024, 2, 2)],
        }
    )


def _invalid_macro_null_actual() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "release_date": [date(2024, 1, 5)],
            "release_ts_utc": [datetime(2024, 1, 5, 13, 30, tzinfo=UTC)],
            "event_id": ["NFP_2024_01"],
            "indicator": ["nonfarm_payrolls"],
            "actual": [None],
            "consensus_median": [175.0],
            "std_consensus": [20.0],
            "surprise_z": [2.05],
            "source": ["BLS"],
            "vintage_date": [date(2024, 1, 5)],
        },
        schema={
            "release_date": pl.Date,
            "release_ts_utc": pl.Datetime(time_zone="UTC"),
            "event_id": pl.Utf8,
            "indicator": pl.Utf8,
            "actual": pl.Float64,
            "consensus_median": pl.Float64,
            "std_consensus": pl.Float64,
            "surprise_z": pl.Float64,
            "source": pl.Utf8,
            "vintage_date": pl.Date,
        },
    )


def _duplicate_macro_df() -> pl.DataFrame:
    d = date(2024, 1, 5)
    ts = datetime(2024, 1, 5, 13, 30, tzinfo=UTC)
    return pl.DataFrame(
        {
            "release_date": [d, d],
            "release_ts_utc": [ts, ts],
            "event_id": ["NFP_2024_01", "NFP_2024_01"],  # duplicate
            "indicator": ["nonfarm_payrolls", "nonfarm_payrolls"],
            "actual": [216.0, 217.0],
            "consensus_median": [175.0, 175.0],
            "std_consensus": [20.0, 20.0],
            "surprise_z": [2.05, 2.1],
            "source": ["BLS", "BLS"],
            "vintage_date": [d, d],
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFomcTextSchema:
    def test_valid_passes(self) -> None:
        FomcTextSchema.validate(_valid_fomc_df())

    def test_invalid_doc_type_fails(self) -> None:
        with pytest.raises(pandera.errors.SchemaError):
            FomcTextSchema.validate(_invalid_fomc_doc_type())

    def test_duplicate_release_doc_type_fails(self) -> None:
        with pytest.raises(pandera.errors.SchemaError):
            FomcTextSchema.validate(_duplicate_fomc_df())

    def test_naive_datetime_rejected(self) -> None:
        # Regression: schema must require tz=UTC. A producer regression that
        # emits naive timestamps should fail validation, not silently pass.
        df = _valid_fomc_df().with_columns(
            pl.col("release_ts_utc").dt.replace_time_zone(None),
            pl.col("embargo_ts_utc").dt.replace_time_zone(None),
        )
        with pytest.raises(pandera.errors.SchemaError):
            FomcTextSchema.validate(df)


class TestMacroSurpriseSchema:
    def test_valid_passes(self) -> None:
        MacroSurpriseSchema.validate(_valid_macro_df())

    def test_null_actual_fails(self) -> None:
        with pytest.raises(pandera.errors.SchemaError):
            MacroSurpriseSchema.validate(_invalid_macro_null_actual())

    def test_duplicate_release_event_fails(self) -> None:
        with pytest.raises(pandera.errors.SchemaError):
            MacroSurpriseSchema.validate(_duplicate_macro_df())

    def test_naive_datetime_rejected(self) -> None:
        df = _valid_macro_df().with_columns(
            pl.col("release_ts_utc").dt.replace_time_zone(None),
        )
        with pytest.raises(pandera.errors.SchemaError):
            MacroSurpriseSchema.validate(df)

    def test_nullable_consensus_allowed(self) -> None:
        df = _valid_macro_df().with_columns(
            pl.lit(None).cast(pl.Float64).alias("consensus_median"),
            pl.lit(None).cast(pl.Float64).alias("std_consensus"),
            pl.lit(None).cast(pl.Float64).alias("surprise_z"),
        )
        MacroSurpriseSchema.validate(df)
