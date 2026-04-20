"""Data provenance emission (plan section 2.1).

Writes ``data/processed/_provenance/{dataset}_{YYYYMMDD}.json`` after
a successful ingest run. The provenance record ties raw-file checksums
to the processing run's ``ReproLog`` so that any processed artifact
can be traced back to its exact inputs and code state.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from skie_ninja.utils.hashing import file_sha256
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.reproducibility import ReproLog


@dataclass(frozen=True)
class ProvenanceRecord:
    """Immutable provenance for one dataset-day."""

    dataset: str
    snapshot_date: str
    snapshot_ts_utc: str
    vendor: str
    source_urls: list[str]
    source_checksums: dict[str, str]
    output_path: str
    output_checksum: str
    repro_log: dict


def emit_provenance(
    *,
    dataset: str,
    snapshot_date: str,
    vendor: str,
    source_urls: list[str],
    source_paths: list[Path],
    output_path: Path,
    repro_log: ReproLog,
    paths: ProjectPaths | None = None,
) -> Path:
    """Write a provenance JSON and return its path.

    Parameters
    ----------
    dataset
        Logical dataset name (``es_tick``, ``macro_surprise``, ``fomc_text``).
    snapshot_date
        ``YYYYMMDD`` string for the data date.
    vendor
        Data vendor identifier.
    source_urls
        URLs or file URIs of the raw sources.
    source_paths
        Local paths to raw files; SHA-256 is computed for each.
    output_path
        Path to the processed output artifact.
    repro_log
        The ``ReproLog`` from the ingest run.
    paths
        Project paths resolver; auto-discovered if omitted.
    """
    paths = paths or ProjectPaths.discover()
    provenance_dir = paths.data_processed / "_provenance"
    paths.ensure(provenance_dir)

    source_checksums = {}
    for p in source_paths:
        if p.is_file():
            source_checksums[str(p)] = file_sha256(p)

    output_checksum = file_sha256(output_path) if output_path.is_file() else ""

    record = ProvenanceRecord(
        dataset=dataset,
        snapshot_date=snapshot_date,
        snapshot_ts_utc=datetime.now(UTC).isoformat(timespec="microseconds"),
        vendor=vendor,
        source_urls=source_urls,
        source_checksums=source_checksums,
        output_path=str(output_path),
        output_checksum=output_checksum,
        repro_log=repro_log.to_dict(),
    )

    out_file = provenance_dir / f"{dataset}_{snapshot_date}.json"
    payload = json.dumps(
        asdict(record), sort_keys=True, indent=2, ensure_ascii=False
    ).encode("utf-8")

    # Atomic write (same pattern as ReproLog.write).
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=str(provenance_dir),
        prefix=f".{out_file.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(payload)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, out_file)

    return out_file


def read_provenance(path: Path) -> ProvenanceRecord:
    """Deserialize a provenance JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ProvenanceRecord(**data)
