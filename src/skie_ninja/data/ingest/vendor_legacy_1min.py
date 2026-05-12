"""Vendor-legacy 1-minute ES/NQ/MCL/MGC/SIL ingest (Databento via sibling repo).

Imports raw Databento 1-minute OHLCV CSVs for ES and NQ from the
sibling SKIE_Ninja research repo, plus the 2026-05-12 metals/energy
expansion (MCL/MGC/SIL per ADR-0023 + H060 successor track), into
SKIE-Universe's shared-data namespace + processed parquet tree.

Source files (canonical list):
  - ES_{2020,2021,2022,2025}_1min_databento.csv (OOS + forward test)
  - ES_1min_databento.csv                       (in-sample 2023–2024)
  - NQ_{2020,2021,2022}_1min_databento.csv      (OOS)
  - NQ_1min_databento.csv                       (in-sample 2023–2024)
  - MCL_1min_databento.csv                      (full 2015-2025; Stage-A 2026-05-12)
  - MGC_1min_databento.csv                      (full 2015-2025; Stage-A 2026-05-12)
  - SIL_1min_databento.csv                      (full 2015-2025; Stage-A 2026-05-12)

Metals/energy CSVs are single-file-per-symbol (Databento parent-symbology
pull) rather than the per-year sharding used for ES/NQ. The SHA256
idempotency guard treats them identically — each (filename, sha256) pair
is the unit of work.

Copy policy: SHA256-idempotent — re-runs skip files whose source
bytes are unchanged. Two-phase commit on the processed parquet tree
(staging → final rename).

Provenance: emits ``data/processed/_provenance/vendor_legacy_1min_{YYYYMMDD}.json``
with per-source SHA256 + reproducibility-log attachment.

Conforms to the ``IngestJob`` protocol defined in ``_registry.py``.

Vendor chain: Databento GLBX.MDP3 ``ohlcv-1m`` → sibling repo pull →
this import. License verified as of 2026-04-23 per
``~/datasets/vendor_skie_ninja_legacy/es_5min_features_2020_2025.provenance.json``.
"""

from __future__ import annotations

import contextlib
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import polars as pl
import yaml

from skie_ninja.data.ingest._registry import register
from skie_ninja.data.validation.schema import VendorLegacy1minSchema
from skie_ninja.utils.hashing import file_sha256
from skie_ninja.utils.runcontext import RunContext

_log = logging.getLogger(__name__)

# Canonical source root in the sibling repo. Overridable at
# construction time for testing.
_DEFAULT_SOURCE_ROOT = Path(
    r"C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project"
    r"\SKIE_Ninja\data\raw\market"
)

# Dataset name + version registered in INGEST_REGISTRY.
_DATASET_NAME = "vendor_legacy_1min"
_DATASET_VERSION = "0.1.0"


@dataclass(frozen=True)
class _SourceFile:
    """One source CSV with its symbol, coverage label, and filename."""

    symbol: str
    coverage: str  # "in_sample_2023_2024" | "oos_2020" | "oos_2021" | "oos_2022" | "forward_2025"
    filename: str


# Canonical list. ES has a 2025 forward-test file; NQ does not (sibling
# repo has not yet pulled NQ 2025 as of 2026-04-20). If NQ 2025 is
# added upstream, extend this list; the SHA256 idempotency guard means
# existing files will not be re-copied.
_CANONICAL_SOURCES: tuple[_SourceFile, ...] = (
    _SourceFile("ES", "oos_2020", "ES_2020_1min_databento.csv"),
    _SourceFile("ES", "oos_2021", "ES_2021_1min_databento.csv"),
    _SourceFile("ES", "oos_2022", "ES_2022_1min_databento.csv"),
    _SourceFile("ES", "in_sample_2023_2024", "ES_1min_databento.csv"),
    _SourceFile("ES", "forward_2025", "ES_2025_1min_databento.csv"),
    _SourceFile("NQ", "oos_2020", "NQ_2020_1min_databento.csv"),
    _SourceFile("NQ", "oos_2021", "NQ_2021_1min_databento.csv"),
    _SourceFile("NQ", "oos_2022", "NQ_2022_1min_databento.csv"),
    _SourceFile("NQ", "in_sample_2023_2024", "NQ_1min_databento.csv"),
    # Metals/energy expansion (ADR-0023 + H060). Stage-A 2026-05-12:
    # single-file-per-symbol full-window pull via Databento
    # parent-symbology covering 2015-01-01 -> 2025-12-31.
    _SourceFile("MCL", "full_2015_2025", "MCL_1min_databento.csv"),
    _SourceFile("MGC", "full_2015_2025", "MGC_1min_databento.csv"),
    _SourceFile("SIL", "full_2015_2025", "SIL_1min_databento.csv"),
)


_VALID_SYMBOLS: frozenset[str] = frozenset(
    {"ES", "NQ", "MES", "MNQ", "MCL", "MGC", "SIL"}
)


def load_sources_yaml(yaml_path: Path) -> tuple[_SourceFile, ...]:
    """Load extra ``_SourceFile`` entries from a YAML manifest.

    Used by the ``--sources-yaml`` CLI flag to add Cell-I-style backfill
    files without editing ``_CANONICAL_SOURCES`` in source. The returned
    tuple is appended to ``_CANONICAL_SOURCES`` (existing files take
    precedence on filename collision).

    YAML schema (top-level ``sources`` list, each entry a 3-key map):

    .. code-block:: yaml

        sources:
          - symbol: ES          # ES, NQ, MES, MNQ
            coverage: backfill_2015
            filename: ES_2015_1min_databento.csv
          - symbol: NQ
            coverage: backfill_2015
            filename: NQ_2015_1min_databento.csv

    Raises
    ------
    FileNotFoundError
        If ``yaml_path`` does not exist.
    ValueError
        If the top-level key ``sources`` is missing, not a list, or any
        entry violates the schema (missing keys, unknown symbol, empty
        filename, duplicate filename within the YAML).
    """
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Sources YAML not found: {yaml_path}")

    with yaml_path.open(encoding="utf-8") as fh:
        payload: Any = yaml.safe_load(fh)

    if not isinstance(payload, dict) or "sources" not in payload:
        raise ValueError(
            f"Sources YAML {yaml_path} must have top-level key 'sources'."
        )
    raw_entries = payload["sources"]
    if not isinstance(raw_entries, list):
        raise ValueError(
            f"Sources YAML {yaml_path} 'sources' must be a list."
        )

    out: list[_SourceFile] = []
    seen_filenames: set[str] = set()
    required_keys = {"symbol", "coverage", "filename"}
    for i, entry in enumerate(raw_entries):
        if not isinstance(entry, dict):
            raise ValueError(
                f"Sources YAML {yaml_path} entry {i} must be a mapping."
            )
        missing = required_keys - set(entry.keys())
        if missing:
            raise ValueError(
                f"Sources YAML {yaml_path} entry {i} missing keys: "
                f"{sorted(missing)}"
            )
        symbol = str(entry["symbol"])
        coverage = str(entry["coverage"])
        filename = str(entry["filename"])
        if symbol not in _VALID_SYMBOLS:
            raise ValueError(
                f"Sources YAML {yaml_path} entry {i} symbol={symbol!r} "
                f"not in {sorted(_VALID_SYMBOLS)}."
            )
        if not filename or not filename.endswith(".csv"):
            raise ValueError(
                f"Sources YAML {yaml_path} entry {i} filename={filename!r} "
                "must be a non-empty .csv name."
            )
        if filename in seen_filenames:
            raise ValueError(
                f"Sources YAML {yaml_path} duplicate filename={filename!r} "
                f"at entry {i}."
            )
        seen_filenames.add(filename)
        out.append(_SourceFile(symbol=symbol, coverage=coverage, filename=filename))

    return tuple(out)


def merge_sources(
    canonical: tuple[_SourceFile, ...],
    extra: tuple[_SourceFile, ...],
) -> tuple[_SourceFile, ...]:
    """Append ``extra`` to ``canonical``, dropping filename collisions.

    Filename is the unique key. ``canonical`` entries take precedence;
    any ``extra`` entry whose filename already appears in ``canonical``
    is logged-and-dropped (idempotent re-runs of the same YAML do not
    duplicate sources).
    """
    canonical_files = {s.filename for s in canonical}
    deduped: list[_SourceFile] = list(canonical)
    for s in extra:
        if s.filename in canonical_files:
            _log.info(
                "Sources YAML entry shadowed by canonical: %s", s.filename
            )
            continue
        deduped.append(s)
        canonical_files.add(s.filename)
    return tuple(deduped)


class VendorLegacy1minIngestJob:
    """Ingest job for vendor_skie_ninja_legacy ES/NQ 1-minute CSVs."""

    name: str = _DATASET_NAME
    version: str = _DATASET_VERSION

    def __init__(
        self,
        source_root: Path | None = None,
        sources: tuple[_SourceFile, ...] | None = None,
    ) -> None:
        self._source_root = Path(source_root) if source_root else _DEFAULT_SOURCE_ROOT
        self._sources = sources if sources is not None else _CANONICAL_SOURCES

    # ------------------------------------------------------------------
    # fetch: copy CSVs from sibling repo to shared-data raw cache
    # ------------------------------------------------------------------

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        """Copy any missing/changed source CSVs into the shared raw cache.

        The date range is accepted for CLI-parity but does not slice —
        the canonical file list is all-or-nothing (each file is one
        coverage slice already). Files whose source SHA256 matches the
        destination SHA256 are skipped (idempotent).

        Returns the list of destination paths that now carry the
        canonical bytes (whether freshly-copied or already-present).
        """
        del start, end  # unused; kept for IngestJob protocol parity
        dest_root = ctx.paths.shared_vendor_skie_ninja_legacy / "raw_1min"
        dest_root.mkdir(parents=True, exist_ok=True)

        out: list[Path] = []
        copied = 0
        skipped = 0

        for src_spec in self._sources:
            src = self._source_root / src_spec.filename
            if not src.is_file():
                # Upstream file missing — log-and-continue so a partial
                # import doesn't block the others. Emitted to ctx for
                # downstream dataset_checksums visibility.
                _log.error(
                    "Source missing: %s — symbol=%s coverage=%s (skipping)",
                    src,
                    src_spec.symbol,
                    src_spec.coverage,
                )
                continue

            dest = dest_root / src_spec.filename
            if dest.is_file():
                src_sha = file_sha256(src)
                dst_sha = file_sha256(dest)
                if src_sha == dst_sha:
                    skipped += 1
                    out.append(dest)
                    _log.info("Unchanged (SHA match): %s", dest.name)
                    continue

            shutil.copy2(src, dest)
            # Verify the copy independently.
            if file_sha256(dest) != file_sha256(src):
                raise RuntimeError(
                    f"SHA256 mismatch after copy: {src} -> {dest}"
                )
            copied += 1
            out.append(dest)
            _log.info(
                "Copied: %s -> %s (symbol=%s coverage=%s)",
                src.name,
                dest,
                src_spec.symbol,
                src_spec.coverage,
            )

        _log.info(
            "Fetch summary: %d copied, %d unchanged, %d total canonical sources",
            copied,
            skipped,
            len(self._sources),
        )
        return out

    # ------------------------------------------------------------------
    # parse: CSV -> LazyFrame (normalized schema, concatenated)
    # ------------------------------------------------------------------

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        """Read all raw CSVs and concatenate into one validated LazyFrame.

        Enforces UTC tz on ``ts_event`` and Float64/Int64 dtypes per
        ``VendorLegacy1minSchema``. Empty input yields an empty
        schema-conformant frame (contract-preserving).
        """
        del ctx  # unused
        if not raw_paths:
            return _empty_frame().lazy()

        frames: list[pl.LazyFrame] = []
        for rp in raw_paths:
            lf = (
                pl.scan_csv(rp, try_parse_dates=False)
                .with_columns(
                    # Databento emits ISO-8601 with "+00:00"; parse
                    # explicitly rather than letting try_parse_dates
                    # coerce to naive.
                    pl.col("ts_event").str.to_datetime(
                        time_unit="us", time_zone="UTC"
                    ),
                    pl.col("open").cast(pl.Float64),
                    pl.col("high").cast(pl.Float64),
                    pl.col("low").cast(pl.Float64),
                    pl.col("close").cast(pl.Float64),
                    pl.col("volume").cast(pl.Int64),
                    pl.col("rtype").cast(pl.Int64),
                    pl.col("publisher_id").cast(pl.Int64),
                    pl.col("instrument_id").cast(pl.Int64),
                    # Preserve the raw contract code (e.g., ESH0) and
                    # derive the root symbol. CME mini roots are 2 char
                    # (ES, NQ) but micros are 3 char (MES, MNQ, MCL, MGC,
                    # SIL); a naive first-2 slice corrupts MES → 'ME' and
                    # MCL → 'MC'. Explicit prefix mapping with 3-char
                    # branches FIRST (MES/MNQ/MCL/MGC/SIL) so the 2-char
                    # ES/NQ branches don't shadow them.
                    pl.col("symbol").cast(pl.Utf8).alias("contract_symbol"),
                    pl.when(pl.col("symbol").cast(pl.Utf8).str.starts_with("MES"))
                    .then(pl.lit("MES"))
                    .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("MNQ"))
                    .then(pl.lit("MNQ"))
                    .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("MCL"))
                    .then(pl.lit("MCL"))
                    .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("MGC"))
                    .then(pl.lit("MGC"))
                    .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("SIL"))
                    .then(pl.lit("SIL"))
                    .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("ES"))
                    .then(pl.lit("ES"))
                    .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("NQ"))
                    .then(pl.lit("NQ"))
                    .otherwise(pl.col("symbol").cast(pl.Utf8))
                    .alias("symbol"),
                )
            )
            frames.append(lf)

        # Concatenation across CSVs can interleave contract_symbols
        # non-monotonically (ESH0 2020 then ESM0 2020 appear in
        # separate files in practice, but the *concatenation order*
        # of the year files is not guaranteed to preserve
        # (contract_symbol, ts_event) monotonicity). Sort here so the
        # downstream validate() monotonicity check holds by
        # construction, not by input-file ordering luck.
        return pl.concat(frames, how="vertical").sort(
            ["contract_symbol", "ts_event"]
        )

    # ------------------------------------------------------------------
    # validate: schema + OHLC consistency
    # ------------------------------------------------------------------

    def validate(self, df: pl.LazyFrame) -> None:
        """Validate against VendorLegacy1minSchema + OHLC + monotonicity."""
        collected = df.collect()
        VendorLegacy1minSchema.validate(collected)

        # OHLC consistency: direct form matching the docstring. Catches
        # high < open/close/low and low > open/close/high.
        violations = collected.filter(
            (pl.col("low") > pl.col("open"))
            | (pl.col("low") > pl.col("close"))
            | (pl.col("low") > pl.col("high"))
            | (pl.col("high") < pl.col("open"))
            | (pl.col("high") < pl.col("close"))
        )
        if violations.height > 0:
            raise ValueError(
                f"OHLC consistency violated on {violations.height} rows; "
                f"first: {violations.head(1).to_dicts()}"
            )

        # Monotonicity within each contract_symbol: ts_event must be
        # non-decreasing. Required for look-ahead-free feature
        # computation downstream (rules/quant-project.md §Time-series
        # integrity). Schema declares unique (contract_symbol, ts_event)
        # which forbids equal timestamps, so non-decreasing ≡ strictly
        # increasing here.
        sort_check = collected.sort(["contract_symbol", "ts_event"])
        if not collected.equals(sort_check):
            raise ValueError(
                "ts_event is not monotonically increasing within each "
                "contract_symbol group; sort upstream before validation."
            )

        _log.info(
            "Schema + OHLC + monotonicity validation passed "
            "(rows=%d, symbols=%s)",
            collected.height,
            sorted(collected["symbol"].unique().to_list()),
        )

    # ------------------------------------------------------------------
    # write_processed: partitioned parquet under symbol/year
    # ------------------------------------------------------------------

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        """Write partitioned parquet: ``symbol={ES|NQ}/year={YYYY}/part-0000.parquet``.

        Two-phase commit: write to ``_staging``, validate each file,
        then rename to final location.
        """
        paths = ctx.paths
        base_dir = paths.data_processed / "vendor_legacy_1min"
        staging_dir = paths.data_processed / "_staging" / "vendor_legacy_1min"
        paths.ensure(staging_dir)

        collected = df.collect().with_columns(
            pl.col("ts_event").dt.year().alias("_year"),
        )

        staged: list[tuple[Path, Path]] = []
        for (symbol, year), part_df in collected.group_by(["symbol", "_year"]):
            part_out = part_df.drop("_year")
            part_dir_final = base_dir / f"symbol={symbol}" / f"year={year}"
            part_dir_stage = staging_dir / f"symbol={symbol}" / f"year={year}"
            part_dir_stage.mkdir(parents=True, exist_ok=True)
            staging_path = part_dir_stage / "part-0000.parquet"
            final_path = part_dir_final / "part-0000.parquet"
            part_out.write_parquet(staging_path)
            staged.append((staging_path, final_path))

        # Re-validate each staged file against the schema.
        for sp, _fp in staged:
            try:
                VendorLegacy1minSchema.validate(pl.read_parquet(sp))
            except Exception:
                for bad_sp, _bad_fp in staged:
                    bad_sp.unlink(missing_ok=True)
                _rmtree_empty(staging_dir)
                raise

        # Promote.
        for sp, fp in staged:
            fp.parent.mkdir(parents=True, exist_ok=True)
            sp.replace(fp)
        _rmtree_empty(staging_dir)

        _log.info("Wrote %d partitions to %s", len(staged), base_dir)
        return base_dir

    # ------------------------------------------------------------------
    # emit_provenance
    # ------------------------------------------------------------------

    def emit_provenance(
        self,
        ctx: RunContext,
        source_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Write provenance JSON with per-source SHA256 + repro-log attach."""
        prov_dir = ctx.paths.data_processed / "_provenance"
        ctx.paths.ensure(prov_dir)

        # Also populate RunContext.dataset_checksums so the ReproLog
        # carries the canonical hashes (closes the open follow-up from
        # the prior audit — previously the ReproLog's
        # dataset_checksums was empty for ingest runs). Duck-type
        # rather than suppress: a real RunContext that hasn't been
        # entered raises RuntimeError (not AttributeError), which a
        # suppress(AttributeError) would miss and silently drop.
        if hasattr(ctx, "add_dataset_checksum"):
            for sp in source_paths:
                ctx.add_dataset_checksum(sp.as_posix(), file_sha256(sp))

        timestamp = datetime.now(tz=UTC).isoformat()
        payload = {
            "dataset": self.name,
            "version": self.version,
            "vendor": "Databento GLBX.MDP3 ohlcv-1m (via sibling SKIE_Ninja repo)",
            "license_status": "verified",
            "tier": "raw",
            # evidence_bar_eligible intentionally False at raw tier: the
            # raw 1-min series concatenates successive front-month
            # contracts without roll adjustment, so returns computed on
            # this series cross uncompensated roll boundaries. The
            # futures analog of the "adjust for corporate actions
            # before return calc" requirement in rules/quant-project.md
            # §Time-series integrity. A downstream roll-adjusted
            # derivative dataset (calendar-rule or open-interest rule)
            # is the proper evidence-bar input.
            "evidence_bar_eligible": False,
            "roll_adjustment": "none (front-month concatenation only)",
            "timestamp_utc": timestamp,
            "source_root": self._source_root.as_posix(),
            # Key by absolute POSIX path to match the CLI's
            # _source_unchanged idempotency key in scripts/ingest.py
            # (F-1-6 of the 2026-04-23 Cycle-1 audit; fixes the
            # always-False dict-comparison that made the --force-less
            # short-circuit dead code). Forward-compatible: next run
            # emits matching keys and subsequent runs short-circuit.
            "source_checksums": {
                sp.as_posix(): file_sha256(sp) for sp in source_paths
            },
            "output_path": output_path.as_posix(),
            "run_id": ctx.log.run_id if ctx.log else None,
            "repro_log": ctx.log.to_dict() if ctx.log else None,
        }

        date_str = datetime.now(tz=UTC).strftime("%Y%m%d")
        prov_path = prov_dir / f"{self.name}_{date_str}.json"
        prov_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _log.info("Wrote provenance: %s", prov_path)
        return prov_path


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _empty_frame() -> pl.DataFrame:
    """Empty schema-conformant frame for the no-input path."""
    return pl.DataFrame(
        schema={
            "ts_event": pl.Datetime("us", "UTC"),
            "rtype": pl.Int64,
            "publisher_id": pl.Int64,
            "instrument_id": pl.Int64,
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume": pl.Int64,
            "contract_symbol": pl.Utf8,
            "symbol": pl.Utf8,
        }
    )


def _rmtree_empty(path: Path) -> None:
    """Remove a directory tree if all leaves are empty."""
    if not path.is_dir():
        return
    for child in path.iterdir():
        if child.is_dir():
            _rmtree_empty(child)
    with contextlib.suppress(OSError):
        path.rmdir()


# Self-register at import time.
register(VendorLegacy1minIngestJob())
