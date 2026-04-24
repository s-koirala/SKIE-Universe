"""Data ingest CLI entry point (plan section 2.3).

Usage:
    python scripts/ingest.py --dataset fomc_text --start 2020-01-01 --end 2024-12-31
    python scripts/ingest.py --dataset macro_surprise --start 2023-01-01 --end 2024-06-30 --dry-run

Idempotent: re-run overwrites only if source SHA256 changed (unless --force).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, date, datetime
from pathlib import Path

# Script-bootstrap sys.path shim so the script works before
# `uv pip install -e .` has been run.
_SCRIPT_DIR = Path(__file__).resolve().parent  # paths-guard: allow (script bootstrap)
sys.path.insert(0, str(_SCRIPT_DIR.parent / "src"))

import polars as pl  # noqa: E402

from skie_ninja.data.ingest import INGEST_REGISTRY  # noqa: E402
from skie_ninja.data.validation.distribution import check_distribution_stability  # noqa: E402
from skie_ninja.data.validation.schema import (  # noqa: E402
    FomcTextSchema,
    MacroSurpriseSchema,
    VendorLegacy1minRollAdjustedSchema,
    VendorLegacy1minSchema,
)
from skie_ninja.utils.hashing import file_sha256  # noqa: E402
from skie_ninja.utils.logging_setup import setup_logging  # noqa: E402
from skie_ninja.utils.paths import ProjectPaths  # noqa: E402
from skie_ninja.utils.runcontext import RunContext  # noqa: E402

_log = logging.getLogger(__name__)

# Dataset choices. es_tick is a stub for future use.
_DATASET_CHOICES = (
    "fomc_text",
    "macro_surprise",
    "es_tick",
    "vendor_legacy_1min",
    "vendor_legacy_1min_roll_adjusted",
)


def _parse_date(value: str) -> date:
    """Parse an ISO-8601 date string (YYYY-MM-DD)."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date {value!r}; expected YYYY-MM-DD."
        ) from exc


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ingest.py",
        description="Fetch, parse, validate, and write processed ingest datasets.",
    )
    p.add_argument(
        "--dataset",
        required=True,
        choices=_DATASET_CHOICES,
        help="Dataset to ingest.",
    )
    p.add_argument(
        "--start",
        required=True,
        type=_parse_date,
        help="Start date (YYYY-MM-DD), inclusive.",
    )
    p.add_argument(
        "--end",
        required=True,
        type=_parse_date,
        help="End date (YYYY-MM-DD), inclusive.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Enumerate what would be fetched/written without side effects.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite processed output even if source SHA256 is unchanged.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for RunContext (default: 42).",
    )
    return p


def _load_registry() -> None:
    """Import concrete ingest modules so they self-register.

    Sibling agents own these modules; we import defensively and log
    any that are not yet available.
    """
    _module_map = {
        "fomc_text": "skie_ninja.data.ingest.fomc_text",
        "macro_surprise": "skie_ninja.data.ingest.macro_surprise",
        "vendor_legacy_1min": "skie_ninja.data.ingest.vendor_legacy_1min",
        "vendor_legacy_1min_roll_adjusted": "skie_ninja.data.ingest.vendor_legacy_1min_roll_adjusted",
    }
    import importlib

    for name, mod_path in _module_map.items():
        try:
            importlib.import_module(mod_path)
        except ImportError:
            _log.debug("Ingest module %s not yet available (%s).", name, mod_path)


_SCHEMA_MAP: dict[str, type] = {
    "fomc_text": FomcTextSchema,
    "macro_surprise": MacroSurpriseSchema,
    "vendor_legacy_1min": VendorLegacy1minSchema,
    "vendor_legacy_1min_roll_adjusted": VendorLegacy1minRollAdjustedSchema,
}


def _source_unchanged(
    dataset: str,
    raw_paths: list[Path],
    paths: ProjectPaths,
) -> bool:
    """Return True if raw-file checksums match the existing provenance record."""
    raw_checksums: dict[str, str] = {}
    for rp in raw_paths:
        if rp.is_file():
            raw_checksums[rp.as_posix()] = file_sha256(rp)

    today_str = datetime.now(tz=UTC).strftime("%Y%m%d")  # UTC to match provenance filename
    prov_path = paths.data_processed / "_provenance" / f"{dataset}_{today_str}.json"
    if not prov_path.is_file():
        return False
    try:
        existing_prov = json.loads(prov_path.read_text(encoding="utf-8"))
        return raw_checksums == existing_prov.get("source_checksums", {})
    except (json.JSONDecodeError, KeyError):
        _log.debug("Could not read existing provenance at %s; proceeding.", prov_path)
        return False


def _post_write_validate(dataset: str, output_path: Path) -> None:
    """Read back processed parquet and run schema + distribution validation.

    Raises on failure (plan §2.4 — validate-data skill wiring).
    """
    schema_cls = _SCHEMA_MAP.get(dataset)
    if schema_cls is None or not output_path.is_dir():
        return

    parquet_files = list(output_path.rglob("*.parquet"))
    if not parquet_files:
        return

    readback = pl.concat([pl.read_parquet(pf) for pf in parquet_files])

    # Schema validation.
    schema_cls.validate(readback)
    _log.info("Post-write schema validation passed.")

    # Distribution validation: compare new batch against prior snapshot.
    # If no prior snapshot exists, skip (first ingest has no reference).
    prior_parquets = sorted(
        pf
        for pf in output_path.rglob("*.parquet")
        if pf not in set(parquet_files)
    )
    if not prior_parquets:
        _log.info("No prior snapshot for distribution comparison; skipping drift check.")
        return

    reference = pl.concat([pl.read_parquet(pf) for pf in prior_parquets])
    numeric_cols = [
        c
        for c, dt in zip(readback.columns, readback.dtypes, strict=True)
        if dt.is_numeric()
    ]
    ks_min_n = 2  # scipy.stats.ks_2samp requires n >= 2
    if numeric_cols and readback.height >= ks_min_n and reference.height >= ks_min_n:
        alerts = check_distribution_stability(readback, reference, numeric_cols)
        if alerts:
            for a in alerts:
                _log.warning(
                    "Distribution drift alert: col=%s, ks=%.4f, p_adj=%.2e",
                    a.column,
                    a.ks_statistic,
                    a.p_value_adj,
                )
    _log.info("Post-write distribution check complete.")


def run(argv: list[str] | None = None) -> int:  # noqa: PLR0911
    """CLI entry point. Returns POSIX exit code."""
    args = _build_parser().parse_args(argv)

    setup_logging()
    _load_registry()

    dataset: str = args.dataset
    start: date = args.start
    end: date = args.end
    dry_run: bool = args.dry_run
    force: bool = args.force
    seed: int = args.seed

    if start > end:
        _log.error("--start (%s) is after --end (%s).", start, end)
        return 1

    if dataset not in INGEST_REGISTRY:
        _log.error(
            "Dataset %r not found in INGEST_REGISTRY. "
            "Available: %s",
            dataset,
            ", ".join(sorted(INGEST_REGISTRY)) or "(none)",
        )
        return 1

    job = INGEST_REGISTRY[dataset]
    paths = ProjectPaths.discover(_SCRIPT_DIR)

    with RunContext(
        phase="ingest",
        hypothesis_id=f"ingest_{dataset}",
        rng_seed=seed,
        paths=paths,
    ) as ctx:
        _log.info(
            "Ingest started: dataset=%s, start=%s, end=%s, dry_run=%s, force=%s",
            dataset,
            start,
            end,
            dry_run,
            force,
        )

        # Step 1: fetch
        _log.info("Fetching raw data for %s [%s, %s].", dataset, start, end)
        raw_paths = job.fetch(start, end, ctx)
        _log.info("Fetch returned %d path(s).", len(raw_paths))

        if dry_run:
            _log.info("[dry-run] Would process %d file(s):", len(raw_paths))
            for p in raw_paths:
                _log.info("[dry-run]   %s", p)
            _log.info("[dry-run] Stopping before parse.")
            return 0

        # Idempotency: SHA256 change detection (plan §2.3).
        if not force and _source_unchanged(dataset, raw_paths, paths):
            _log.info(
                "Skipping %s: source checksums unchanged. Use --force to override.",
                dataset,
            )
            return 0

        # Step 2: parse
        _log.info("Parsing %d raw file(s).", len(raw_paths))
        lf = job.parse(raw_paths, ctx)

        # Step 3: validate
        _log.info("Validating parsed data.")
        try:
            job.validate(lf)
        except Exception as exc:
            _log.error("Validation failed: %s", exc)
            return 2

        # Step 4: write processed
        _log.info("Writing processed output.")
        output_path = job.write_processed(lf, ctx)
        _log.info("Processed data written to %s.", output_path)

        # Step 4b: post-write validation (plan §2.4 — validate-data skill wiring).
        _log.info("Running post-write validation on processed output.")
        try:
            _post_write_validate(dataset, output_path)
        except Exception as exc:
            _log.error("Post-write validation failed: %s", exc)
            return 3

        # Step 5: emit provenance
        _log.info("Emitting provenance record.")
        prov_path = job.emit_provenance(ctx, raw_paths, output_path)
        _log.info("Provenance written to %s.", prov_path)

    _log.info("Ingest complete: %s.", dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
