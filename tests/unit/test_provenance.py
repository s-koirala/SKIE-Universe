"""Tests for provenance emission and round-trip read."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skie_ninja.data.provenance import ProvenanceRecord, emit_provenance, read_provenance
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.reproducibility import ReproLog


@pytest.fixture()
def tmp_project(tmp_path: Path) -> ProjectPaths:
    """Create a minimal project layout in a temp dir."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
    (tmp_path / "data" / "processed" / "_provenance").mkdir(parents=True)
    return ProjectPaths(root=tmp_path)


@pytest.fixture()
def sample_repro_log() -> ReproLog:
    return ReproLog(
        run_id="test-run-001",
        phase="ingest",
        hypothesis_id="H000",
        timestamp_utc="2026-04-15T12:00:00.000000+00:00",
        git_head="abc123",
        pip_freeze_sha256="def456",
        pip_freeze_path="logs/reproducibility/env/def456.txt",
        dataset_checksums={},
        rng_seed=42,
        model_hash=None,
        config_resolved_sha256=None,
        host={"os": "test", "python": "3.11.0", "cpu": "x86_64"},
        env_id="test-env",
    )


@pytest.fixture()
def sample_source_file(tmp_project: ProjectPaths) -> Path:
    """Create a small raw file to checksum."""
    raw_dir = tmp_project.root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    f = raw_dir / "sample.csv"
    f.write_text("a,b\n1,2\n", encoding="utf-8")
    return f


@pytest.fixture()
def sample_output_file(tmp_project: ProjectPaths) -> Path:
    """Create a small output file to checksum."""
    out = tmp_project.data_processed / "fomc_text" / "test.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"\x00\x01\x02")
    return out


class TestEmitProvenance:
    def test_round_trip(
        self,
        tmp_project: ProjectPaths,
        sample_repro_log: ReproLog,
        sample_source_file: Path,
        sample_output_file: Path,
    ) -> None:
        prov_path = emit_provenance(
            dataset="fomc_text",
            snapshot_date="20260415",
            vendor="fed_website",
            source_urls=["https://federalreserve.gov/fomc/2024-01-31.htm"],
            source_paths=[sample_source_file],
            output_path=sample_output_file,
            repro_log=sample_repro_log,
            paths=tmp_project,
        )

        assert prov_path.exists()
        assert prov_path.name == "fomc_text_20260415.json"

        record = read_provenance(prov_path)
        assert isinstance(record, ProvenanceRecord)
        assert record.dataset == "fomc_text"
        assert record.vendor == "fed_website"
        assert len(record.source_checksums) == 1
        assert record.output_checksum != ""
        assert record.repro_log["run_id"] == "test-run-001"

    def test_json_is_valid(
        self,
        tmp_project: ProjectPaths,
        sample_repro_log: ReproLog,
        sample_source_file: Path,
        sample_output_file: Path,
    ) -> None:
        prov_path = emit_provenance(
            dataset="macro_surprise",
            snapshot_date="20260415",
            vendor="bls",
            source_urls=[],
            source_paths=[sample_source_file],
            output_path=sample_output_file,
            repro_log=sample_repro_log,
            paths=tmp_project,
        )
        raw = prov_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert "dataset" in data
        assert "repro_log" in data
        # Verify sorted keys (canonical serialization).
        keys = list(data.keys())
        assert keys == sorted(keys)
