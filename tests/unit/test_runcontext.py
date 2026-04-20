"""P0-12 acceptance: RunContext writes exactly one ReproLog, even on crash."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.reproducibility import ReproLog
from skie_ninja.utils.runcontext import RunContext


def _paths(tmp_path: Path) -> ProjectPaths:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
    return ProjectPaths(root=tmp_path)


def test_happy_path_writes_single_reprolog(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    with RunContext(phase="p0", hypothesis_id="H1", rng_seed=7, paths=p) as ctx:
        assert ctx.log is not None
        out = ctx.output_path
    assert out.is_file()
    ReproLog.verify(out)

    produced = list((tmp_path / "logs" / "reproducibility").glob("*.json"))
    assert len(produced) == 1


def test_crash_path_still_flushes(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    with (
        pytest.raises(RuntimeError),
        RunContext(phase="p0", hypothesis_id="H1", rng_seed=7, paths=p) as ctx,
    ):
        out = ctx.output_path
        raise RuntimeError("boom")
    assert out.is_file()


def test_seeds_python_random(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    with RunContext(phase="p0", hypothesis_id="H1", rng_seed=123, paths=p):
        a = [random.random() for _ in range(3)]
    with RunContext(phase="p0", hypothesis_id="H1", rng_seed=123, paths=p):
        b = [random.random() for _ in range(3)]
    assert a == b


def test_set_model_hash_and_dataset_checksum(tmp_path: Path) -> None:
    p = _paths(tmp_path)
    with RunContext(phase="p0", hypothesis_id="H1", rng_seed=1, paths=p) as ctx:
        ctx.set_model_hash("abc123")
        ctx.add_dataset_checksum("es_tick", "deadbeef")
        out = ctx.output_path
    log = ReproLog.read(out)
    assert log.model_hash == "abc123"
    assert log.dataset_checksums == {"es_tick": "deadbeef"}
