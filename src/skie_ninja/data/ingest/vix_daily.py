"""VIX daily close ingest from FRED VIXCLS series.

Per H052a frozen pre-reg [research/01_hypothesis_register/H052a/design.md](
../../../../research/01_hypothesis_register/H052a/design.md) §3 line 58:
"VIX daily level, as_of = T−1 close (CBOE). Joins on calendar date."

Source: CBOE Volatility Index (VIXCLS) via FRED public CSV endpoint.

  - FRED metadata: https://fred.stlouisfed.org/series/VIXCLS
  - Underlying: CBOE published index; FRED carries close-of-day from 1990-01-02 forward.
  - License: CBOE/FRED public data; no API key required for public CSV download.

Output schema (Parquet at ``data/processed/vix_daily/vix_daily.parquet``):

  - ``date`` : pl.Date (UTC normalised; CBOE close calendar date)
  - ``vix_close`` : pl.Float64 (VIX index close value)
  - ``source`` : pl.Utf8 ("FRED:VIXCLS")
  - ``ingested_at_utc`` : pl.Datetime("ns", "UTC")

Provenance JSON at ``data/processed/_provenance/vix_daily_<YYYYMMDD>.json``
records: source URL, sha256 of raw CSV, sha256 of output parquet, row
count, date range.

PIT: VIXCLS is a daily-close series (~16:15 ET CBOE close). At session T's
H052a entry timestamp (10:30 ET), the most recent observable VIX is from
T−1's close. The H052a feature factory ``compute_vix_daily_join`` joins
``T−1`` via ``pd.merge_asof(..., direction="backward")``.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import io
import json
import logging
from pathlib import Path
from typing import Any

import httpx
import polars as pl

from skie_ninja.utils.paths import ProjectPaths

_log = logging.getLogger(__name__)

_FRED_VIXCLS_CSV: str = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
)
_HTTP_TIMEOUT_SEC: int = 30


def fetch_vixcls_csv(*, url: str = _FRED_VIXCLS_CSV) -> bytes:
    """Fetch the FRED VIXCLS CSV. Returns the raw bytes."""
    with httpx.Client(timeout=_HTTP_TIMEOUT_SEC) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content


def parse_vixcls_csv(raw: bytes) -> pl.DataFrame:
    """Parse the FRED VIXCLS CSV into a polars DataFrame.

    FRED's CSV format: header row ``observation_date,VIXCLS`` followed by
    rows with date in ``YYYY-MM-DD`` and value (or ``.`` for missing).
    """
    df = pl.read_csv(io.BytesIO(raw))
    # Normalise column names: FRED used to emit `DATE` then `observation_date`.
    cols = df.columns
    date_col = next((c for c in cols if c.lower() in ("date", "observation_date")), cols[0])
    vix_col = next((c for c in cols if c.upper() == "VIXCLS"), cols[1])
    df = df.rename({date_col: "date", vix_col: "vix_close"})
    df = df.select(["date", "vix_close"])
    df = df.with_columns(
        pl.col("date").str.strptime(pl.Date, format="%Y-%m-%d", strict=False),
        pl.col("vix_close").cast(pl.Float64, strict=False),
    )
    df = df.drop_nulls()
    return df


def write_vix_daily_parquet(
    df: pl.DataFrame,
    *,
    paths: ProjectPaths | None = None,
    raw_csv_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Write the VIX daily DataFrame to Parquet + provenance JSON."""
    paths = paths or ProjectPaths.discover()
    out_dir = paths.root / "data" / "processed" / "vix_daily"
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = out_dir / "vix_daily.parquet"

    ingested_at = _dt.datetime.now(_dt.UTC)
    df_out = df.with_columns(
        pl.lit("FRED:VIXCLS").alias("source"),
        pl.lit(ingested_at).alias("ingested_at_utc"),
    )
    df_out.write_parquet(str(parquet_path), compression="snappy")
    output_sha = hashlib.sha256(parquet_path.read_bytes()).hexdigest()
    raw_sha = (
        hashlib.sha256(raw_csv_bytes).hexdigest() if raw_csv_bytes is not None else None
    )

    provenance_dir = paths.root / "data" / "processed" / "_provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    provenance_path = (
        provenance_dir / f"vix_daily_{ingested_at.strftime('%Y%m%d')}.json"
    )
    provenance = {
        "source_url": _FRED_VIXCLS_CSV,
        "raw_csv_sha256": raw_sha,
        "output_frame_sha256": output_sha,
        "n_rows": int(df_out.height),
        "date_min": str(df["date"].min()),
        "date_max": str(df["date"].max()),
        "ingested_at_utc": ingested_at.isoformat(),
        "output_parquet_path": str(parquet_path),
    }
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8"
    )
    return provenance


def load_vix_daily(paths: ProjectPaths | None = None) -> pl.DataFrame:
    """Load the VIX daily DataFrame from disk.

    Returns columns ``[date (Date), vix_close (Float64)]`` for downstream
    consumers (e.g., H052a feature factory ``compute_vix_daily_join``).
    Raises FileNotFoundError if the parquet does not exist.
    """
    paths = paths or ProjectPaths.discover()
    parquet_path = paths.root / "data" / "processed" / "vix_daily" / "vix_daily.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"VIX daily parquet not found at {parquet_path}. Run "
            f"`python -m skie_ninja.data.ingest.vix_daily` (or use the "
            f"ingest CLI) to fetch from FRED first."
        )
    df = pl.read_parquet(str(parquet_path))
    return df.select(["date", "vix_close"])


def ingest_vix_daily(*, paths: ProjectPaths | None = None) -> dict[str, Any]:
    """End-to-end: fetch FRED VIXCLS + parse + write parquet + provenance."""
    _log.info("Fetching FRED VIXCLS from %s", _FRED_VIXCLS_CSV)
    raw = fetch_vixcls_csv()
    df = parse_vixcls_csv(raw)
    _log.info("Parsed %d rows; date range %s → %s", df.height, df["date"].min(), df["date"].max())
    provenance = write_vix_daily_parquet(df, paths=paths, raw_csv_bytes=raw)
    _log.info("Wrote VIX daily parquet at %s", provenance["output_parquet_path"])
    return provenance


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ingest_vix_daily()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "fetch_vixcls_csv",
    "parse_vixcls_csv",
    "write_vix_daily_parquet",
    "load_vix_daily",
    "ingest_vix_daily",
]
