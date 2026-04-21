"""Macroeconomic surprise ingest pipeline.

Fetches first-release vintages from ALFRED (Federal Reserve Bank of
St. Louis) and consensus forecasts from the Philadelphia Fed Survey of
Professional Forecasters (SPF). Computes surprise z-scores:

    surprise_z = (actual - consensus_median) / std_consensus

**Point-in-time guarantee**: only the first-release vintage from
ALFRED is used (``output_type=4``), never revised values. This ensures
any downstream feature computed at time *t* uses only information
available at *t*.

**Consensus dispersion**: for indicators covered by the SPF
(quarterly, individual-level responses), cross-sectional median and
standard deviation are computed from the distribution of forecaster
point estimates. For indicators without SPF coverage (monthly/weekly),
rolling historical forecast error standard deviation over a trailing
40-quarter window is used as proxy, following Andersen, Bollerslev,
Diebold & Vega (2003, "Micro Effects of Macro Announcements:
Real-Time Price Discovery in Foreign Exchange," *American Economic
Review* 93(1):38-62). The 40-quarter window (~10 years) is the
authors' recommendation for stable estimation of forecast-error
dispersion.

Data sources:
    - ALFRED API: https://fred.stlouisfed.org/docs/api/alfred/
    - Philadelphia Fed SPF: https://www.philadelphiafed.org/surveys-and-data/
      real-time-data-research/survey-of-professional-forecasters
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import polars as pl
import yaml

from skie_ninja.data.ingest._registry import register
from skie_ninja.data.validation.schema import MacroSurpriseSchema
from skie_ninja.utils.hashing import file_sha256
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.runcontext import RunContext

_log = logging.getLogger(__name__)

# ALFRED API base. The /alfred/ endpoints return vintage-dated
# observations (output_type=4 = initial release only; output_type=1
# would return all vintages active in the real-time period window).
_ALFRED_BASE = "https://api.stlouisfed.org/fred"

# Philadelphia Fed SPF individual-level CSV base URL.
_SPF_BASE = (
    "https://www.philadelphiafed.org/surveys-and-data/"
    "real-time-data-research/data-files/files"
)

# Trailing window (in quarters) for forecast-error std proxy.
# Per ABDV 2003, 40 quarters (~10 years) provides stable estimation.
_FORECAST_ERROR_WINDOW_Q = 40

# Request timeout for ALFRED API calls (seconds).
_HTTP_TIMEOUT_SEC = 30


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


def _load_indicator_config(paths: ProjectPaths | None = None) -> list[dict[str, Any]]:
    """Load ``config/macro_indicators.yaml`` and return the indicator list."""
    p = paths or ProjectPaths.discover()
    config_path = p.root / "config" / "macro_indicators.yaml"
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["indicators"]


# ---------------------------------------------------------------------------
# ALFRED fetch helpers
# ---------------------------------------------------------------------------


def _fred_api_key() -> str | None:
    return os.environ.get("FRED_API_KEY")


def fetch_alfred_series(
    series_id: str,
    start: date,
    end: date,
    *,
    api_key: str,
    dest_dir: Path,
) -> list[Path]:
    """Fetch first-release vintages from ALFRED for *series_id*.

    Calls the ``fred/series/observations`` endpoint with
    ``realtime_start`` / ``realtime_end`` set to the requested range
    and ``output_type=4`` (observations, initial release only) per
    the FRED enum documented at
    https://fred.stlouisfed.org/docs/api/fred/series_observations.html
    (output_type=1 = all vintages in window; output_type=4 = first
    release only — which is what this pipeline needs).

    Raw JSON responses are saved to
    ``dest_dir/{series_id}/vintage_{YYYYMMDD}.json``.

    Returns list of written file paths.
    """
    url = f"{_ALFRED_BASE}/series/observations"
    params: dict[str, str] = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "realtime_start": start.isoformat(),
        "realtime_end": end.isoformat(),
        "output_type": "4",  # initial release only per FRED series_observations enum
    }

    series_dir = dest_dir / series_id
    series_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    with httpx.Client(timeout=_HTTP_TIMEOUT_SEC) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()

    # Save full response keyed by the realtime_end date.
    out_path = series_dir / f"vintage_{end.strftime('%Y%m%d')}.json"
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    written.append(out_path)
    n_obs = len(payload.get("observations", []))
    _log.info("ALFRED %s: wrote %s (%d obs)", series_id, out_path, n_obs)
    return written


def parse_alfred_json(path: Path) -> list[dict[str, Any]]:
    """Parse a single ALFRED vintage JSON into a list of observation dicts.

    Each dict contains: date, value, realtime_start (first-release date).
    """
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    rows: list[dict[str, Any]] = []
    for obs in payload.get("observations", []):
        val_str = obs.get("value", ".")
        if val_str == ".":
            continue  # FRED uses "." for missing
        try:
            value = float(val_str)
        except (ValueError, TypeError):
            continue
        rows.append(
            {
                "obs_date": obs["date"],
                "value": value,
                "realtime_start": obs["realtime_start"],
            }
        )
    return rows


# ---------------------------------------------------------------------------
# SPF fetch / parse helpers
# ---------------------------------------------------------------------------

# Mapping from SPF variable names to download filenames. The SPF
# publishes individual-level responses as CSV files with these names.
_SPF_FILES: dict[str, str] = {
    "UNEMP": "Individual_UNEMP.csv",
    "CPI": "Individual_CPI.csv",
    "PCE": "Individual_PCECTPI.csv",
    "INDPROD": "Individual_INDPROD.csv",
    "RGDP": "Individual_RGDP.csv",
    "HOUSING": "Individual_HOUSING.csv",
}


def fetch_spf_files(dest_dir: Path) -> list[Path]:
    """Download SPF individual-level CSV files from Philadelphia Fed.

    Files are saved to *dest_dir*. Only downloads files that do not
    already exist (idempotent).

    Returns list of paths to downloaded/existing CSV files.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for var_name, filename in _SPF_FILES.items():
            out_path = dest_dir / filename
            if out_path.exists():
                _log.info("SPF %s: already exists at %s", var_name, out_path)
                paths.append(out_path)
                continue
            url = f"{_SPF_BASE}/{filename}"
            try:
                resp = client.get(url)
                resp.raise_for_status()
                out_path.write_bytes(resp.content)
                paths.append(out_path)
                _log.info("SPF %s: downloaded %s", var_name, out_path)
            except httpx.HTTPError as exc:
                _log.warning("SPF %s download failed: %s", var_name, exc)
    return paths


def parse_spf_csv(path: Path) -> pl.DataFrame:
    """Parse an SPF individual-level CSV into a standardized DataFrame.

    Returns columns: forecast_date, indicator, forecaster_id, value.

    SPF CSV layout: rows are forecasters, columns are
    ``{VARIABLE}{YEAR}Q{QUARTER}`` forecasts. The first few columns
    are metadata (YEAR, QUARTER, ID). We melt to long format.
    """
    # Read raw; SPF files sometimes have ragged rows
    raw = pl.read_csv(path, infer_schema_length=0, truncate_ragged_lines=True)

    # Identify metadata columns (all-caps short names)
    meta_cols = []
    value_cols = []
    for c in raw.columns:
        c_up = c.strip().upper()
        if c_up in ("YEAR", "QUARTER", "ID"):
            meta_cols.append(c.strip())
            raw = raw.rename({c: c.strip()})
        else:
            value_cols.append(c)

    if not meta_cols or "YEAR" not in [m.upper() for m in meta_cols]:
        _log.warning("SPF CSV %s has unexpected columns: %s", path, raw.columns[:10])
        return pl.DataFrame(
            schema={
                "forecast_date": pl.Date,
                "indicator": pl.Utf8,
                "forecaster_id": pl.Utf8,
                "value": pl.Float64,
            }
        )

    # Normalize column names for metadata
    rename_map = {c: c.upper() for c in meta_cols}
    raw = raw.rename(rename_map)

    # Melt to long format
    melted = raw.unpivot(
        index=["YEAR", "QUARTER", "ID"],
        on=value_cols,
        variable_name="variable",
        value_name="raw_value",
    )

    # Extract indicator name from path stem
    indicator = path.stem.replace("Individual_", "")

    # Convert values to float, dropping non-numeric
    result = (
        melted.with_columns(
            pl.col("raw_value").cast(pl.Float64, strict=False).alias("value"),
            pl.col("YEAR").cast(pl.Int32, strict=False).alias("year"),
            pl.col("QUARTER").cast(pl.Int32, strict=False).alias("quarter"),
        )
        .filter(pl.col("value").is_not_null() & pl.col("year").is_not_null())
        .with_columns(
            # Construct forecast_date as first day of the forecast quarter
            (
                pl.concat_str(
                    [
                        pl.col("year").cast(pl.Utf8),
                        pl.lit("-"),
                        ((pl.col("quarter") - 1) * 3 + 1)
                        .cast(pl.Utf8)
                        .str.zfill(2),
                        pl.lit("-01"),
                    ]
                )
            )
            .str.to_date("%Y-%m-%d")
            .alias("forecast_date"),
            pl.lit(indicator).alias("indicator"),
            pl.col("ID").cast(pl.Utf8).alias("forecaster_id"),
        )
        .select("forecast_date", "indicator", "forecaster_id", "value")
    )
    return result


def compute_spf_consensus(spf_df: pl.DataFrame) -> pl.DataFrame:
    """Compute consensus median and cross-sectional std from SPF data.

    Groups by (forecast_date, indicator), computes median and std
    of individual forecaster values.

    Returns columns: forecast_date, indicator, consensus_median,
    std_consensus, n_forecasters.
    """
    if spf_df.is_empty():
        return pl.DataFrame(
            schema={
                "forecast_date": pl.Date,
                "indicator": pl.Utf8,
                "consensus_median": pl.Float64,
                "std_consensus": pl.Float64,
                "n_forecasters": pl.UInt32,
            }
        )

    return (
        spf_df.group_by("forecast_date", "indicator")
        .agg(
            pl.col("value").median().alias("consensus_median"),
            # sample std (ddof=1) corrects for finite-forecaster bias;
            # SPF panel n=5-40 per variable-quarter.
            pl.col("value").std(ddof=1).alias("std_consensus"),
            pl.col("value").count().alias("n_forecasters"),
        )
        .sort("forecast_date", "indicator")
    )


# ---------------------------------------------------------------------------
# Forecast-error std proxy (ABDV 2003)
# ---------------------------------------------------------------------------


def compute_forecast_error_std(
    actuals: pl.DataFrame,
    *,
    window_q: int = _FORECAST_ERROR_WINDOW_Q,
) -> pl.DataFrame:
    """Rolling historical forecast error std as consensus dispersion proxy.

    For indicators without SPF coverage, we cannot compute
    cross-sectional std from individual forecasts. Instead, following
    Andersen, Bollerslev, Diebold & Vega (2003, AER 93(1):38-62),
    we use the rolling standard deviation of historical forecast
    errors (actual minus a naive forecast, here: the prior period
    actual) over a trailing window.

    The 40-quarter (~10-year) trailing window is per ABDV 2003.

    Parameters
    ----------
    actuals : pl.DataFrame
        Must have columns: obs_date (Date), indicator (Utf8), value (Float64).
    window_q : int
        Trailing window in observations (quarters for quarterly data,
        months for monthly). Default 40.

    Returns
    -------
    pl.DataFrame
        Columns: obs_date, indicator, forecast_error_std.
    """
    if actuals.is_empty():
        return pl.DataFrame(
            schema={
                "obs_date": pl.Date,
                "indicator": pl.Utf8,
                "forecast_error_std": pl.Float64,
            }
        )

    result = (
        actuals.sort("indicator", "obs_date")
        .with_columns(
            # Naive forecast: previous period's actual
            pl.col("value")
            .shift(1)
            .over("indicator")
            .alias("naive_forecast"),
        )
        .with_columns(
            (pl.col("value") - pl.col("naive_forecast")).alias("forecast_error"),
        )
        .with_columns(
            pl.col("forecast_error")
            # justify: min_samples=max(4, window_q // 4) — n>=4 ensures df>=3
            # for sample variance, which per Cochran (1953, "Sampling Techniques",
            # Wiley, ch. 2) avoids severe underestimation bias in variance
            # estimates from very small samples. SPF panel n=5-40 per
            # variable-quarter; window_q // 4 adapts to the window length.
            .rolling_std(window_size=window_q, min_samples=max(4, window_q // 4))
            .over("indicator")
            .alias("forecast_error_std"),
        )
        .select("obs_date", "indicator", "forecast_error_std")
    )
    return result


# ---------------------------------------------------------------------------
# Surprise z-score computation
# ---------------------------------------------------------------------------


def compute_surprise_z(
    actual: float,
    consensus_median: float | None,
    std_consensus: float | None,
) -> float | None:
    """Compute surprise z-score: (actual - consensus_median) / std_consensus.

    Returns None if consensus_median or std_consensus is None/zero.
    """
    if consensus_median is None or std_consensus is None:
        return None
    if std_consensus == 0.0:
        return None
    return (actual - consensus_median) / std_consensus


# ---------------------------------------------------------------------------
# MacroSurpriseIngestJob
# ---------------------------------------------------------------------------


class MacroSurpriseIngestJob:
    """Ingest job for macroeconomic surprise data.

    Satisfies the ``IngestJob`` protocol defined in ``_registry.py``.
    """

    name: str = "macro_surprise"
    version: str = "0.1.0"

    def __init__(self, paths: ProjectPaths | None = None) -> None:
        self._paths = paths or ProjectPaths.discover()
        self._indicators = _load_indicator_config(self._paths)
        self._spf_indicator_map: dict[str, str] = {}
        for ind in self._indicators:
            if ind.get("spf_coverage") and ind.get("spf_variable"):
                self._spf_indicator_map[ind["id"]] = ind["spf_variable"]

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        """Download ALFRED vintages and SPF CSVs for the date range.

        Skips ALFRED fetch if FRED_API_KEY is not set (logs a warning).
        SPF files are downloaded once and reused (idempotent).
        """
        all_paths: list[Path] = []

        # -- ALFRED --
        api_key = _fred_api_key()
        if api_key is None:
            _log.warning(
                "FRED_API_KEY not set; skipping ALFRED fetch. "
                "Set the env var to enable macro data download."
            )
        else:
            fred_dir = self._paths.ensure(self._paths.shared_fred)
            for ind in self._indicators:
                sid = ind["fred_series"]
                try:
                    paths = fetch_alfred_series(
                        sid, start, end, api_key=api_key, dest_dir=fred_dir
                    )
                    all_paths.extend(paths)
                except httpx.HTTPError as exc:
                    _log.error("ALFRED fetch failed for %s: %s", sid, exc)

        # -- SPF --
        spf_dir = self._paths.ensure(self._paths.shared_spf)
        try:
            spf_paths = fetch_spf_files(spf_dir)
            all_paths.extend(spf_paths)
        except httpx.HTTPError as exc:
            _log.error("SPF fetch failed: %s", exc)

        return all_paths

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        """Combine ALFRED actuals with SPF consensus to produce surprise data.

        For SPF-covered indicators: cross-sectional median and std
        from individual forecaster responses.

        For non-SPF indicators: rolling historical forecast error
        std as proxy per ABDV 2003.
        """
        # Separate raw paths by type
        alfred_paths = [p for p in raw_paths if p.suffix == ".json"]
        spf_paths = [p for p in raw_paths if p.suffix == ".csv"]

        # -- Parse ALFRED actuals --
        all_actuals: list[dict[str, Any]] = []
        indicator_map = {ind["fred_series"]: ind for ind in self._indicators}

        for path in alfred_paths:
            series_id = path.parent.name
            if series_id not in indicator_map:
                continue
            ind = indicator_map[series_id]
            obs_rows = parse_alfred_json(path)
            for row in obs_rows:
                release_time = ind.get("release_time_et", "08:30")
                hour, minute = (int(x) for x in release_time.split(":"))
                obs_date = date.fromisoformat(row["obs_date"])
                vintage_date = date.fromisoformat(row["realtime_start"])
                # Construct release_ts_utc from vintage_date + release_time_et.
                # DST-aware: construct tz-aware datetime in America/New_York,
                # then convert to UTC. Matches pattern in fomc_text.py.
                _et = ZoneInfo("America/New_York")
                release_local = datetime(
                    vintage_date.year,
                    vintage_date.month,
                    vintage_date.day,
                    hour,
                    minute,
                    tzinfo=_et,
                )
                release_ts = release_local.astimezone(UTC)
                all_actuals.append(
                    {
                        "release_date": vintage_date,
                        "release_ts_utc": release_ts,
                        # Key event by (indicator, obs_date) — one observation
                        # is one release. Using vintage_date would collide any
                        # time two obs_dates share a first-release date (e.g.
                        # weekly ICSA where multiple weekly obs can first-
                        # release on the same business day).
                        "event_id": f"{ind['id']}_{obs_date.isoformat()}",
                        "indicator": ind["id"],
                        "actual": row["value"],
                        "obs_date": obs_date,
                        "source": ind["source"],
                        "vintage_date": vintage_date,
                    }
                )

        if not all_actuals:
            return pl.DataFrame(
                schema={
                    "release_date": pl.Date,
                    "release_ts_utc": pl.Datetime("us", "UTC"),
                    "event_id": pl.Utf8,
                    "indicator": pl.Utf8,
                    "actual": pl.Float64,
                    "consensus_median": pl.Float64,
                    "std_consensus": pl.Float64,
                    "surprise_z": pl.Float64,
                    "source": pl.Utf8,
                    "vintage_date": pl.Date,
                }
            ).lazy()

        actuals_df = pl.DataFrame(all_actuals)

        # -- Parse SPF consensus --
        spf_frames: list[pl.DataFrame] = []
        for path in spf_paths:
            parsed = parse_spf_csv(path)
            if not parsed.is_empty():
                spf_frames.append(parsed)

        spf_consensus: pl.DataFrame | None = None
        if spf_frames:
            combined_spf = pl.concat(spf_frames)
            spf_consensus = compute_spf_consensus(combined_spf)

        # -- Compute forecast-error std for non-SPF indicators --
        non_spf_ids = {
            ind["id"]
            for ind in self._indicators
            if not ind.get("spf_coverage")
        }
        non_spf_actuals = actuals_df.filter(pl.col("indicator").is_in(list(non_spf_ids)))

        fe_std: pl.DataFrame | None = None
        if not non_spf_actuals.is_empty():
            fe_std_input = non_spf_actuals.select(
                pl.col("obs_date"),
                pl.col("indicator"),
                pl.col("actual").alias("value"),
            )
            fe_std = compute_forecast_error_std(fe_std_input)

        # -- Join consensus onto actuals --
        # Start with actuals_df
        result = actuals_df.clone()

        # Add consensus_median and std_consensus columns
        result = result.with_columns(
            pl.lit(None).cast(pl.Float64).alias("consensus_median"),
            pl.lit(None).cast(pl.Float64).alias("std_consensus"),
        )

        # For SPF-covered indicators, join consensus by matching
        # indicator -> spf_variable and obs_date -> forecast_date
        if spf_consensus is not None and not spf_consensus.is_empty():
            # Build reverse map: spf_variable -> fred_id
            spf_var_to_fred: dict[str, str] = {
                v: k for k, v in self._spf_indicator_map.items()
            }

            # Map SPF indicator names to FRED IDs in consensus df
            spf_with_fred_id = spf_consensus.with_columns(
                pl.col("indicator")
                .replace(spf_var_to_fred)
                .alias("fred_indicator"),
            )

            # Join on (indicator, obs_date ~ forecast_date)
            joined = result.join(
                spf_with_fred_id.select(
                    pl.col("fred_indicator").alias("_join_ind"),
                    pl.col("forecast_date").alias("_join_date"),
                    pl.col("consensus_median").alias("_spf_median"),
                    pl.col("std_consensus").alias("_spf_std"),
                ),
                left_on=["indicator", "obs_date"],
                right_on=["_join_ind", "_join_date"],
                how="left",
            )

            result = joined.with_columns(
                pl.coalesce("_spf_median", "consensus_median").alias("consensus_median"),
                pl.coalesce("_spf_std", "std_consensus").alias("std_consensus"),
            ).drop("_spf_median", "_spf_std")

        # For non-SPF indicators, use forecast-error std as proxy
        if fe_std is not None and not fe_std.is_empty():
            joined_fe = result.join(
                fe_std.select(
                    pl.col("obs_date").alias("_fe_date"),
                    pl.col("indicator").alias("_fe_ind"),
                    pl.col("forecast_error_std").alias("_fe_std"),
                ),
                left_on=["obs_date", "indicator"],
                right_on=["_fe_date", "_fe_ind"],
                how="left",
            )

            result = joined_fe.with_columns(
                pl.coalesce("_fe_std", "std_consensus").alias("std_consensus"),
            ).drop("_fe_std")

        # Guard against fan-out from upstream joins: SPF/FE-std join sources
        # can contain multiple rows per (indicator, obs_date) when consensus
        # aggregation emits more than one forecast vintage for an observation.
        # The event grain is (indicator, obs_date) — equivalently event_id —
        # so enforce uniqueness on event_id at the output boundary with a
        # deterministic tiebreak (keep first, maintain order).
        result = result.unique(
            subset=["event_id"], keep="first", maintain_order=True
        )

        # -- Compute surprise z-score --
        result = result.with_columns(
            pl.struct("actual", "consensus_median", "std_consensus")
            .map_elements(
                lambda s: compute_surprise_z(
                    s["actual"], s["consensus_median"], s["std_consensus"]
                ),
                return_dtype=pl.Float64,
            )
            .alias("surprise_z"),
        )

        # Select final columns in schema order
        result = result.select(
            "release_date",
            "release_ts_utc",
            "event_id",
            "indicator",
            "actual",
            "consensus_median",
            "std_consensus",
            "surprise_z",
            "source",
            "vintage_date",
        )

        # Cast release_ts_utc to timezone-aware datetime; also pin nullable
        # float columns to Float64 in case upstream joins produced all-null
        # columns with inferred Null dtype (polars collapses all-null Series
        # to dtype=Null, which trips the pandera Float64 schema check).
        result = result.with_columns(
            pl.col("release_ts_utc").cast(pl.Datetime("us", "UTC")),
            pl.col("consensus_median").cast(pl.Float64),
            pl.col("std_consensus").cast(pl.Float64),
            pl.col("surprise_z").cast(pl.Float64),
        )

        return result.lazy()

    def validate(self, df: pl.LazyFrame) -> None:
        """Validate against MacroSurpriseSchema (pandera-polars)."""
        MacroSurpriseSchema.validate(df.collect())

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        """Write validated data to partitioned parquet files.

        Layout: data/processed/macro_surprise/release_date=YYYY-MM-DD/
                event_id={indicator}_{vintage}.parquet

        Uses two-phase commit: write to _staging/, validate, rename
        to final location.
        """
        collected = df.collect()
        base_dir = ctx.paths.data_processed / "macro_surprise"
        staging_dir = ctx.paths.data_processed / "_staging" / "macro_surprise"
        staging_dir.mkdir(parents=True, exist_ok=True)

        written_paths: list[Path] = []

        for row in collected.iter_rows(named=True):
            rd = row["release_date"]
            eid = row["event_id"]
            partition_dir = base_dir / f"release_date={rd}"
            staging_partition = staging_dir / f"release_date={rd}"
            staging_partition.mkdir(parents=True, exist_ok=True)

            filename = f"event_id={eid}.parquet"
            staging_path = staging_partition / filename
            final_path = partition_dir / filename

            # Write single-row parquet to staging. Single-row frames with
            # all-null nullable columns collapse to dtype=Null on construction;
            # cast to the schema-declared Float64 to survive the parquet
            # round-trip and the per-row schema revalidation below.
            row_df = pl.DataFrame([row]).with_columns(
                pl.col("release_ts_utc").cast(pl.Datetime("us", "UTC")),
                pl.col("consensus_median").cast(pl.Float64),
                pl.col("std_consensus").cast(pl.Float64),
                pl.col("surprise_z").cast(pl.Float64),
            )
            row_df.write_parquet(staging_path)

            # Validate staging file
            try:
                check_df = pl.read_parquet(staging_path)
                MacroSurpriseSchema.validate(check_df)
            except Exception:
                staging_path.unlink(missing_ok=True)
                raise

            # Phase 2: rename to final
            partition_dir.mkdir(parents=True, exist_ok=True)
            staging_path.rename(final_path)
            written_paths.append(final_path)

        # Clean up staging
        _rm_empty_parents(staging_dir)

        if written_paths:
            _log.info(
                "Wrote %d macro surprise files to %s",
                len(written_paths),
                base_dir,
            )

        return base_dir

    def emit_provenance(
        self,
        ctx: RunContext,
        source_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Write provenance JSON for this ingest run."""
        prov_dir = ctx.paths.data_processed / "_provenance"
        prov_dir.mkdir(parents=True, exist_ok=True)

        today = date.today().isoformat().replace("-", "")
        prov_path = prov_dir / f"macro_surprise_{today}.json"

        source_checksums = {}
        for p in source_paths:
            if p.exists():
                source_checksums[str(p)] = file_sha256(p)

        prov = {
            "dataset": "macro_surprise",
            "version": self.version,
            "snapshot_ts_utc": datetime.now(UTC).isoformat(),
            "sources": {
                "alfred": {
                    "base_url": _ALFRED_BASE,
                    "series_ids": [
                        ind["fred_series"] for ind in self._indicators
                    ],
                },
                "spf": {
                    "base_url": _SPF_BASE,
                    "files": list(_SPF_FILES.values()),
                },
            },
            "source_checksums": source_checksums,
            "output_path": str(output_path),
            "run_id": ctx.log.run_id if ctx.log else "unknown",
            "git_head": ctx.log.git_head if ctx.log else "unknown",
        }

        prov_path.write_text(
            json.dumps(prov, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        _log.info("Provenance written to %s", prov_path)
        return prov_path


def _rm_empty_parents(path: Path) -> None:
    """Remove *path* and its empty ancestors up to data/processed."""
    try:
        for p in [path, *path.parents]:
            if p.name in ("processed", "data"):
                break
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
            else:
                break
    except OSError:
        pass


# Self-register at import time.
register(MacroSurpriseIngestJob())
