"""Integration test: fetch one real ALFRED vintage for PAYEMS.

Requires ``FRED_API_KEY`` environment variable to be set. Skips
gracefully if absent. Marked ``@pytest.mark.integration`` so it
is excluded from default ``pytest`` runs.
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl
import pytest

from skie_ninja.data.ingest.macro_surprise import (
    fetch_alfred_series,
    parse_alfred_json,
)
from skie_ninja.data.validation.schema import MacroSurpriseSchema

_HAS_API_KEY = os.environ.get("FRED_API_KEY") is not None


@pytest.mark.integration
@pytest.mark.skipif(not _HAS_API_KEY, reason="FRED_API_KEY not set")
class TestAlfredFetchPayems:
    """Fetch one ALFRED vintage for PAYEMS and validate the parse."""

    def test_fetch_parse_validate(self, tmp_path: Path) -> None:
        api_key = os.environ["FRED_API_KEY"]
        start = date(2024, 1, 1)
        end = date(2024, 3, 31)

        paths = fetch_alfred_series(
            "PAYEMS",
            start,
            end,
            api_key=api_key,
            dest_dir=tmp_path,
        )
        assert len(paths) >= 1
        assert paths[0].exists()

        rows = parse_alfred_json(paths[0])
        assert len(rows) > 0

        # Verify the parsed data has the expected structure
        for row in rows:
            assert isinstance(row["value"], float)
            assert row["value"] > 0  # NFP always positive

        # Build a minimal MacroSurpriseSchema-compatible DataFrame
        # to verify schema compatibility
        records = []
        for row in rows:
            vintage = date.fromisoformat(row["realtime_start"])
            obs_d = date.fromisoformat(row["obs_date"])
            records.append(
                {
                    "release_date": vintage,
                    "release_ts_utc": datetime(
                        vintage.year,
                        vintage.month,
                        vintage.day,
                        13,
                        30,
                        tzinfo=UTC,
                    ),
                    "event_id": f"PAYEMS_{obs_d.isoformat()}",
                    "indicator": "PAYEMS",
                    "actual": row["value"],
                    "consensus_median": None,
                    "std_consensus": None,
                    "surprise_z": None,
                    "source": "BLS",
                    "vintage_date": vintage,
                }
            )

        df = pl.DataFrame(records).with_columns(
            pl.col("release_ts_utc").cast(pl.Datetime("us", "UTC")),
        )
        MacroSurpriseSchema.validate(df)
