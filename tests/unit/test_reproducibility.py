"""P0-1 acceptance: ReproLog dataclass + capture/write/read/verify."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.reproducibility import ReproLog, capture


def _paths(tmp_path: Path) -> ProjectPaths:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
    return ProjectPaths(root=tmp_path)


def test_reprolog_frozen() -> None:
    fields = {f.name for f in dataclasses.fields(ReproLog)}
    required = {
        "run_id",
        "phase",
        "hypothesis_id",
        "timestamp_utc",
        "git_head",
        "pip_freeze_sha256",
        "pip_freeze_path",
        "dataset_checksums",
        "rng_seed",
        "model_hash",
        "config_resolved_sha256",
        "host",
        "env_id",
    }
    assert required.issubset(fields)
    assert ReproLog.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_capture_populates_all_required(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    seed = 42
    log = capture(
        phase="phase_0",
        hypothesis_id="H000",
        rng_seed=seed,
        paths=p,
    )
    assert log.run_id
    assert log.phase == "phase_0"
    assert log.hypothesis_id == "H000"
    assert log.timestamp_utc
    assert log.git_head  # "unknown" acceptable in non-git tmp dir
    assert log.pip_freeze_sha256
    assert log.pip_freeze_path.startswith("logs/reproducibility/env/")
    assert log.rng_seed == seed
    assert isinstance(log.host, dict)
    assert log.env_id


def test_capture_is_pure_modulo_timestamp_and_runid(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    a = capture(phase="x", hypothesis_id="H1", rng_seed=1, paths=p)
    b = capture(phase="x", hypothesis_id="H1", rng_seed=1, paths=p)
    differ = {
        f.name
        for f in dataclasses.fields(ReproLog)
        if getattr(a, f.name) != getattr(b, f.name)
    }
    assert differ <= {"timestamp_utc", "run_id"}


def test_write_read_roundtrip(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    log = capture(phase="x", hypothesis_id="H1", rng_seed=1, paths=p)
    out = tmp_path / "logs" / "reproducibility" / f"{log.run_id}.json"
    log.write(out)
    round_tripped = ReproLog.read(out)
    assert round_tripped == log
    # verify() must return True for a freshly written log.
    assert ReproLog.verify(out) is True
    # Byte-identity: the on-disk file must equal the canonical
    # sorted-keys / indent-2 / UTF-8 JSON serialization exactly.
    expected_bytes = (
        json.dumps(log.to_dict(), sort_keys=True, indent=2, ensure_ascii=False)
    ).encode("utf-8")
    assert out.read_bytes() == expected_bytes


def test_verify_returns_false_on_missing_field(tmp_path: Path) -> None:
    # Corrupted payload missing a required schema field.
    payload = {
        "run_id": "abc",
        "phase": "x",
        "hypothesis_id": "H1",
        # intentionally missing timestamp_utc and others
    }
    p = tmp_path / "corrupt.json"
    p.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    assert ReproLog.verify(p) is False


def test_verify_returns_false_on_unknown_field(tmp_path: Path) -> None:
    # Payload carrying an extra field not in §9.3 schema (e.g., legacy
    # `extra` dict) must fail verification rather than crash.
    p = _paths(tmp_path)
    log = capture(phase="x", hypothesis_id="H1", rng_seed=1, paths=p)
    payload = log.to_dict()
    payload["rogue_field"] = "nope"
    out = tmp_path / "rogue.json"
    out.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    assert ReproLog.verify(out) is False


def test_verify_returns_false_on_malformed_json(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    assert ReproLog.verify(p) is False


def test_write_atomic_survives_exit_exception(tmp_path: Path) -> None:
    """F-2-8: atomicity — exception during __exit__ must still leave a
    verifiable ReproLog on disk."""
    from skie_ninja.utils.runcontext import RunContext

    p = _paths(tmp_path)
    with (
        pytest.raises(RuntimeError, match="boom"),
        RunContext(phase="x", hypothesis_id="H1", rng_seed=1, paths=p) as ctx,
    ):
        out_path = ctx.output_path
        raise RuntimeError("boom")

    assert out_path.is_file()
    assert ReproLog.verify(out_path) is True


def test_write_sorted_keys(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    log = capture(phase="x", hypothesis_id="H1", rng_seed=1, paths=p)
    out = tmp_path / "r.json"
    log.write(out)
    text = out.read_text(encoding="utf-8")
    parsed = json.loads(text)
    # Top-level keys must be sorted alphabetically on disk.
    keys_in_file = list(parsed.keys())
    # json.loads preserves insertion order from the file.
    assert keys_in_file == sorted(keys_in_file)


def test_pip_freeze_path_is_posix(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    log = capture(phase="x", hypothesis_id="H1", rng_seed=1, paths=p)
    assert "\\" not in log.pip_freeze_path
