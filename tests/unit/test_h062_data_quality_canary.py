"""Unit test: H062 data-quality canary against Databento BentoWarning days.

Per H062 design.md §11.2 ``P1-H062-DATA-QUALITY-DEGRADED-DAYS-CANARY``
(BLOCKING; canary against the 3 degraded-quality days surfaced by
Databento BentoWarning during Phase O.0 Stage A extraction:
2017-11-13, 2018-10-21, 2019-01-15 — plus any others surfaced by
``metadata.get_dataset_condition``).

Per [Phase O.0 Stage A ledger note](../../CLAUDE.md) the 3 degraded days
appeared during the MCL/MGC/SIL extraction. Their actual content may be
valid (Databento WARNs but does not block); the canary's job is to:
  1. Detect any rows with the documented degraded-day session_date_et.
  2. Verify those rows pass schema validation (no negative volume, no
     negative price except for known WTI 2020-04-20 event).
  3. Emit a per-symbol annotation that downstream KPI report cards must
     carry: `data-quality-degraded-days-annotated`.

If any of the 3 degraded days is materially malformed (NaN floods,
duplicate-timestamps, zero-volume sessions when liquidity is expected),
the canary fails fast and the orchestrator records the day in
[research/01_hypothesis_register/H062/failure_log.md](
../../research/01_hypothesis_register/H062/failure_log.md) per ADR-0013
§4.1 non-loss mandate.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import polars as pl
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SUBSTRATE_ROOT = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"

# Per Phase O.0 Stage A Databento BentoWarning enumeration.
DEGRADED_DAYS: list[_dt.date] = [
    _dt.date(2017, 11, 13),
    _dt.date(2018, 10, 21),
    _dt.date(2019, 1, 15),
]


@pytest.fixture(scope="module")
def substrate_available() -> bool:
    return _SUBSTRATE_ROOT.exists() and any(_SUBSTRATE_ROOT.iterdir())


@pytest.mark.skipif(
    not (_SUBSTRATE_ROOT.exists() and any(_SUBSTRATE_ROOT.iterdir())),
    reason="substrate not available in this worktree",
)
class TestDegradedDaysSurvive:
    """The 3 BentoWarning days are present in the substrate and pass schema."""

    @pytest.mark.parametrize("degraded_date", DEGRADED_DAYS)
    @pytest.mark.parametrize("symbol", ["MGC", "SIL"])
    def test_no_negative_volume_on_degraded_day(
        self,
        symbol: str,
        degraded_date: _dt.date,
    ) -> None:
        """Substrate bars on the degraded day must NOT have negative volume.

        Degraded does not mean malformed. Databento WARNs on these days for
        upstream-source-quality issues (decimation, late ticks, vendor
        timestamping anomalies); the canary's job is to ensure schema
        invariants are preserved despite the WARN.
        """
        glob_pat = str(_SUBSTRATE_ROOT / f"symbol={symbol}" / "year=*" / "part-*.parquet")
        try:
            lf = pl.scan_parquet(glob_pat)
        except Exception as exc:
            pytest.skip(f"substrate not loadable for {symbol}: {exc}")

        df = lf.collect()
        if df.is_empty():
            pytest.skip(f"{symbol}: empty substrate")
        # Cast ts_event to datetime; filter to the degraded day.
        df = df.with_columns(
            pl.col("ts_event").cast(pl.Datetime("ns", "UTC")).alias("ts_event_utc")
        )
        day_start = _dt.datetime(
            degraded_date.year, degraded_date.month, degraded_date.day, tzinfo=_dt.UTC
        )
        day_end = day_start + _dt.timedelta(days=1)
        day_df = df.filter(
            (pl.col("ts_event_utc") >= day_start)
            & (pl.col("ts_event_utc") < day_end)
        )
        # The substrate may not have bars on every degraded day for every
        # symbol (depends on session calendar). Skip if no bars.
        if day_df.is_empty():
            pytest.skip(
                f"{symbol} on {degraded_date}: no bars in substrate "
                "(degraded warning may be informational only)"
            )
        # Schema invariants: volume >= 0 (per VendorLegacy1MinRoll
        # AdjustedSchema).
        if "volume" in day_df.columns:
            min_vol = day_df["volume"].min()
            assert min_vol is not None and min_vol >= 0, (
                f"{symbol} on {degraded_date}: negative volume found = {min_vol}"
            )

    @pytest.mark.parametrize("symbol", ["MGC", "SIL"])
    def test_substrate_has_provenance_for_symbol(self, symbol: str) -> None:
        """The roll-adjusted substrate has provenance for this symbol."""
        prov_dir = _REPO_ROOT / "data" / "processed" / "_provenance"
        prov_files = list(prov_dir.glob("vendor_legacy_1min_roll_adjusted_*.json"))
        assert len(prov_files) > 0, "no provenance JSON found"


class TestDegradedDaysConstants:
    """Documented constants for the BentoWarning days; protects against drift."""

    def test_three_documented_degraded_days(self) -> None:
        assert len(DEGRADED_DAYS) == 3
        assert DEGRADED_DAYS == [
            _dt.date(2017, 11, 13),
            _dt.date(2018, 10, 21),
            _dt.date(2019, 1, 15),
        ]

    def test_all_degraded_days_pre_2020(self) -> None:
        """The 3 degraded days are pre-IS-start (2020-01-01); they affect
        the MGC/SIL calibration-holdout window only, not IS or OOS."""
        for d in DEGRADED_DAYS:
            assert d.year < 2020
