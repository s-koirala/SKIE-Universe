"""Unit tests for scripts/_hooks/check_repro_log.py (plan §9.1, §9.3)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "_hooks" / "check_repro_log.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_repro_log", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_repro_log"] = mod
    spec.loader.exec_module(mod)
    return mod


check_repro_log = _load_module()


def _valid_repro_dict() -> dict:
    return {
        "run_id": "01HXYZ",
        "phase": "P0",
        "hypothesis_id": "H-000",
        "timestamp_utc": "2026-04-15T12:00:00.000000+00:00",
        "git_head": "deadbeef",
        "pip_freeze_sha256": "a" * 64,
        "pip_freeze_path": "logs/reproducibility/env/abc.txt",
        "dataset_checksums": {"es_1m": "b" * 64},
        "rng_seed": 42,
        "model_hash": None,
        "config_resolved_sha256": "c" * 64,
        "host": {"os": "Linux 6.0", "python": "3.12.1", "cpu": "x86_64"},
        "env_id": "env-hash",
    }


def _notebook_with_output(text_plain: str) -> dict:
    return {
        "cells": [
            {
                "cell_type": "code",
                "source": ["from skie_ninja.utils.reproducibility import capture\n"],
                "outputs": [
                    {
                        "output_type": "execute_result",
                        "data": {"text/plain": text_plain},
                    }
                ],
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


@pytest.fixture()
def valid_notebook(tmp_path: Path) -> Path:
    nb = _notebook_with_output(json.dumps(_valid_repro_dict()))
    p = tmp_path / "valid.ipynb"
    p.write_text(json.dumps(nb), encoding="utf-8")
    return p


@pytest.fixture()
def missing_key_notebook(tmp_path: Path) -> Path:
    payload = _valid_repro_dict()
    del payload["rng_seed"]
    del payload["model_hash"]
    nb = _notebook_with_output(json.dumps(payload))
    p = tmp_path / "missing.ipynb"
    p.write_text(json.dumps(nb), encoding="utf-8")
    return p


@pytest.fixture()
def no_json_notebook(tmp_path: Path) -> Path:
    nb = _notebook_with_output("ReproLog(run_id='x', git_head='y')")
    p = tmp_path / "no_json.ipynb"
    p.write_text(json.dumps(nb), encoding="utf-8")
    return p


def test_valid_notebook_passes(valid_notebook: Path):
    errs = check_repro_log.check_notebook(valid_notebook)
    assert errs == []


def test_missing_keys_fails_with_precise_message(missing_key_notebook: Path):
    errs = check_repro_log.check_notebook(missing_key_notebook)
    assert len(errs) == 1
    msg = errs[0]
    assert "missing required field" in msg
    assert "rng_seed" in msg
    assert "model_hash" in msg


def test_no_json_dump_fails(no_json_notebook: Path):
    errs = check_repro_log.check_notebook(no_json_notebook)
    assert len(errs) == 1
    assert "no code-cell output contains a JSON-dict ReproLog" in errs[0]


def test_main_nonzero_on_failure(missing_key_notebook: Path):
    rc = check_repro_log.main([str(missing_key_notebook)])
    assert rc == 1


def test_main_zero_on_success(valid_notebook: Path):
    rc = check_repro_log.main([str(valid_notebook)])
    assert rc == 0
