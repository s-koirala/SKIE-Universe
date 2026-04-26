"""Wiring-level verification for `P1-CYCLE6-REPRO-DATASET-CHECKSUM`.

The Cycle-6 follow-up was opened because all five Phase-A walk-forward
ReproLogs at the time of the pause memo carried ``dataset_checksums={}``.
Commit ``06f0402`` wired ``output_frame_sha256`` from the roll-adjusted
ingest provenance JSON into ``RunContext`` via
:func:`scripts.run_walk_forward._load_output_sha256`. This test exercises
that wiring end-to-end without running the full per-cfg label-grid +
WalkForwardEngine loop (which is currently expensive on real data;
runtime investigation is tracked under ``P1-H050-SMOKE-RUNTIME-INVESTIGATE``).

The test asserts:
  1. ``_load_output_sha256`` reads ``output_frame_sha256`` from the most
     recent provenance JSON under ``data/processed/_provenance/``.
  2. ``RunContext`` accepts the resulting checksum dict and persists
     it onto the emitted :class:`~skie_ninja.utils.reproducibility.ReproLog`.
  3. The on-disk ReproLog JSON contains the expected
     ``dataset_checksums`` entry; ``{}`` is no longer the contents.

Anchors the closure of ``P1-CYCLE6-REPRO-DATASET-CHECKSUM``: the wiring
is verified end-to-end at the abstraction layer that produced the
empty-dict regression. A successful end-to-end production walk-forward
run (post-Stage-A Cell I substrate completion) will further corroborate
under realistic data, but the wiring contract is closed by this gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.runcontext import RunContext

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

_PROVENANCE_KEY = "vendor_legacy_1min_roll_adjusted"
_SHA256_HEX_LEN = 64


def _load_output_sha256_via_orchestrator(paths: ProjectPaths) -> dict[str, str]:
    """Re-import the orchestrator helper.

    Inline import keeps test discovery from importing the orchestrator's
    heavy LightGBM / polars dependencies at collection time on machines
    without the full dev extras.
    """

    import run_walk_forward as orch  # type: ignore[import-not-found]  # noqa: PLC0415

    return orch._load_output_sha256(paths)


def test_load_output_sha256_reads_provenance_json_when_present(
    tmp_path: Path,
) -> None:
    """``_load_output_sha256`` returns the provenance ``output_frame_sha256``."""

    fake_root = tmp_path / "repo"
    provenance = fake_root / "data" / "processed" / "_provenance"
    provenance.mkdir(parents=True)
    expected_sha = "a" * 64
    payload = {
        "output_frame_sha256": expected_sha,
        "source_dataset_frame_sha256": "b" * 64,
    }
    (provenance / "vendor_legacy_1min_roll_adjusted_20260424.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    class _StubPaths:
        root = fake_root

    result = _load_output_sha256_via_orchestrator(_StubPaths())
    assert result == {_PROVENANCE_KEY: expected_sha}


def test_load_output_sha256_returns_empty_when_no_provenance(tmp_path: Path) -> None:
    """Missing provenance dir returns empty dict (dry-run / pre-ingest)."""

    fake_root = tmp_path / "repo"
    fake_root.mkdir()

    class _StubPaths:
        root = fake_root

    result = _load_output_sha256_via_orchestrator(_StubPaths())
    assert result == {}


def test_run_context_persists_dataset_checksums_into_repro_log(
    tmp_path: Path,
) -> None:
    """``RunContext`` writes ``dataset_checksums`` into the ReproLog JSON.

    Closes the substantive content of ``P1-CYCLE6-REPRO-DATASET-CHECKSUM``:
    the on-disk ReproLog must contain the wired checksums, not ``{}``.
    Inject a custom :class:`ProjectPaths` so the test does not write to
    the live ``logs/reproducibility/`` tree.
    """

    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "logs" / "reproducibility").mkdir(parents=True)
    test_paths = ProjectPaths(root=project_root)

    expected_sha = "c" * 64
    expected_checksums = {_PROVENANCE_KEY: expected_sha}

    with RunContext(
        phase="walk_forward",
        hypothesis_id="H050",
        rng_seed=2026,
        dataset_checksums=expected_checksums,
        config_resolved_sha256="d" * 64,
        paths=test_paths,
    ) as ctx:
        assert ctx.log is not None
        assert ctx.log.dataset_checksums == expected_checksums
        run_id = ctx.log.run_id

    log_path = project_root / "logs" / "reproducibility" / f"{run_id}.json"
    assert log_path.exists(), (
        f"RunContext did not write ReproLog at {log_path}; verify atomic-flush wiring."
    )

    on_disk = json.loads(log_path.read_text(encoding="utf-8"))
    assert on_disk["dataset_checksums"] == expected_checksums, (
        f"On-disk ReproLog dataset_checksums={on_disk['dataset_checksums']!r} "
        f"does not match expected {expected_checksums!r}; the "
        "P1-CYCLE6-REPRO-DATASET-CHECKSUM regression is open again."
    )


def test_repo_provenance_json_currently_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: the live repo's provenance file is readable.

    Closes the wiring contract: when the provenance file exists (post
    Cycle-1 ingest), the orchestrator's ``_load_output_sha256`` returns
    a populated dict that ``RunContext`` will persist. Skips when the
    provenance file is absent (e.g., fresh worktree before any ingest).
    """

    paths = ProjectPaths.discover()
    provenance_dir = paths.root / "data" / "processed" / "_provenance"
    if not provenance_dir.exists():
        pytest.skip(
            "Provenance dir absent on this worktree; ingest required before this gate can verify."
        )

    pattern = "vendor_legacy_1min_roll_adjusted_*.json"
    matches = sorted(provenance_dir.glob(pattern))
    if not matches:
        pytest.skip(
            "No roll-adjusted provenance JSON present on this worktree; "
            "run `python scripts/ingest.py --dataset "
            "vendor_legacy_1min_roll_adjusted ...` first."
        )

    latest = matches[-1]
    payload = json.loads(latest.read_text(encoding="utf-8"))
    assert "output_frame_sha256" in payload, (
        f"Provenance file {latest.name} missing `output_frame_sha256` field; "
        "Cycle-1 ingest contract regressed."
    )
    sha = payload["output_frame_sha256"]
    assert isinstance(sha, str) and len(sha) == _SHA256_HEX_LEN, (
        f"`output_frame_sha256` malformed: {sha!r}"
    )

    result = _load_output_sha256_via_orchestrator(paths)
    assert result == {_PROVENANCE_KEY: sha}, (
        f"Orchestrator's _load_output_sha256 returned {result!r}; "
        f"expected {{{_PROVENANCE_KEY!r}: {sha!r}}}."
    )
