"""Regression tests for ``skie_ninja.backtest.cfg_checkpoint``.

Covers: round-trip pickle, schema-version gate, provenance drift
detection, atomic-write semantics (tmp + rename), discover_checkpoints
enumeration + filtering, and the WARN-but-load on git_head mismatch
contract.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pytest

from skie_ninja.backtest.cfg_checkpoint import (
    SCHEMA_VERSION,
    CfgKey,
    cfg_checkpoint_dir,
    cfg_checkpoint_path,
    check_provenance,
    discover_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture
def sample_key() -> CfgKey:
    return CfgKey(
        sym="ES",
        cfg_idx=7,
        pt_sl=1.5,
        vertical_barrier_seconds=3600,
        volatility_lookback=60,
    )


@pytest.fixture
def sample_candidate() -> dict:
    return {
        "fold_count": 6,
        "inner_cv_logloss_mean": 0.6926,
        "inner_cv_sharpe_mean": -0.0007,
        "best_params": {"max_depth": 7, "num_leaves": 31},
        "fold_predictions": np.array([0.51, 0.49, 0.52], dtype=np.float64),
    }


def test_cfgkey_filename_and_signature(sample_key: CfgKey) -> None:
    assert sample_key.filename_stem() == "ES__cfg_0007__pt_1.50__vb_003600__vl_0060"
    sig = sample_key.signature()
    assert isinstance(sig, str)
    assert len(sig) == 64  # SHA256 hex


def test_save_and_load_round_trip(
    tmp_path: Path,
    sample_key: CfgKey,
    sample_candidate: dict,
) -> None:
    path = save_checkpoint(
        run_dir=tmp_path,
        key=sample_key,
        candidate=sample_candidate,
        producing_run_id="abc123",
    )
    assert path.exists()
    assert path == cfg_checkpoint_path(tmp_path, sample_key)

    payload = load_checkpoint(path)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["pickle_protocol"] == 5
    assert payload["producing_run_id"] == "abc123"
    assert payload["cfg_key_signature"] == sample_key.signature()
    assert payload["candidate"]["best_params"]["max_depth"] == 7
    np.testing.assert_array_equal(
        payload["candidate"]["fold_predictions"],
        sample_candidate["fold_predictions"],
    )


def test_atomic_write_no_tmp_left_behind(
    tmp_path: Path,
    sample_key: CfgKey,
    sample_candidate: dict,
) -> None:
    save_checkpoint(run_dir=tmp_path, key=sample_key, candidate=sample_candidate)
    cdir = cfg_checkpoint_dir(tmp_path)
    files = list(cdir.iterdir())
    assert all(not f.name.endswith(".tmp") for f in files), (
        f"unexpected .tmp file in cache dir: {files}"
    )


def test_load_rejects_wrong_schema(tmp_path: Path, sample_key: CfgKey) -> None:
    bad_path = cfg_checkpoint_dir(tmp_path)
    bad_path.mkdir(parents=True)
    p = bad_path / f"{sample_key.filename_stem()}.pkl"
    with open(p, "wb") as f:
        pickle.dump({"schema_version": "v0_pickle3", "candidate": {}}, f, protocol=5)
    with pytest.raises(ValueError, match="schema-version mismatch"):
        load_checkpoint(p)


def test_discover_checkpoints_returns_keyed_payloads(
    tmp_path: Path, sample_candidate: dict
) -> None:
    keys = [
        CfgKey("ES", 1, 1.0, 1800, 20),
        CfgKey("ES", 2, 1.0, 1800, 60),
        CfgKey("NQ", 1, 1.5, 3600, 120),
    ]
    for k in keys:
        save_checkpoint(run_dir=tmp_path, key=k, candidate=sample_candidate)
    out = discover_checkpoints(tmp_path)
    assert len(out) == 3
    assert ("ES", 1, 1.0, 1800, 20) in out
    assert ("NQ", 1, 1.5, 3600, 120) in out


def test_discover_checkpoints_empty_dir_returns_empty(tmp_path: Path) -> None:
    assert discover_checkpoints(tmp_path) == {}


def test_discover_checkpoints_skips_corrupt_pickles(
    tmp_path: Path, sample_key: CfgKey, sample_candidate: dict
) -> None:
    # One valid + one truncated pickle
    save_checkpoint(run_dir=tmp_path, key=sample_key, candidate=sample_candidate)
    cdir = cfg_checkpoint_dir(tmp_path)
    bad = cdir / "ES__cfg_0099__pt_2.00__vb_007200__vl_0030.pkl"
    bad.write_bytes(b"\x80\x05")  # truncated pickle header
    out = discover_checkpoints(tmp_path)
    assert len(out) == 1
    assert ("ES", 7, 1.5, 3600, 60) in out


def test_check_provenance_no_drift(
    tmp_path: Path, sample_key: CfgKey, sample_candidate: dict
) -> None:
    p = save_checkpoint(run_dir=tmp_path, key=sample_key, candidate=sample_candidate)
    payload = load_checkpoint(p)
    assert check_provenance(payload) == []


def test_check_provenance_detects_python_drift(
    tmp_path: Path, sample_key: CfgKey, sample_candidate: dict
) -> None:
    p = save_checkpoint(run_dir=tmp_path, key=sample_key, candidate=sample_candidate)
    payload = load_checkpoint(p)
    payload["python_version"] = "9.99.99"
    mismatches = check_provenance(payload)
    assert any("python_version mismatch" in m for m in mismatches)


def test_check_provenance_detects_git_head_drift(
    tmp_path: Path, sample_key: CfgKey, sample_candidate: dict
) -> None:
    p = save_checkpoint(run_dir=tmp_path, key=sample_key, candidate=sample_candidate)
    payload = load_checkpoint(p)
    mismatches = check_provenance(payload, current_git_head="deadbeef" * 5)
    assert any("git_head mismatch" in m for m in mismatches)


def test_check_provenance_skips_unknown_git(
    tmp_path: Path, sample_key: CfgKey, sample_candidate: dict
) -> None:
    """When either side reports git_head=='unknown', the check skips
    git_head comparison (avoids false-positive drift in environments
    where ``git`` is not installed or the cwd is not a repo)."""
    p = save_checkpoint(
        run_dir=tmp_path,
        key=sample_key,
        candidate=sample_candidate,
        git_head="unknown",
    )
    payload = load_checkpoint(p)
    # Both sides "unknown": no mismatch
    mismatches = check_provenance(payload, current_git_head="unknown")
    assert all("git_head" not in m for m in mismatches)


def test_save_creates_parent_dir(tmp_path: Path, sample_key: CfgKey) -> None:
    """``save_checkpoint`` must create ``run_dir/_cfg_checkpoints/`` if
    it doesn't already exist (avoids requiring callers to set it up)."""
    nested = tmp_path / "newly_created" / "run_dir"
    save_checkpoint(run_dir=nested, key=sample_key, candidate={})
    assert (nested / "_cfg_checkpoints").is_dir()
