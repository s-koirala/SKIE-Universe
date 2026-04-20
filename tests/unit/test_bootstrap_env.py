"""Unit tests for scripts/bootstrap_env.py (plan §P0-8)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "bootstrap_env.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("bootstrap_env", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bootstrap_env"] = mod
    spec.loader.exec_module(mod)
    return mod


bootstrap_env = _load_module()


def test_current_interpreter_is_inside_band():
    # Current interpreter must satisfy the pyproject band; the check
    # itself should not raise under the project's uv-provisioned env.
    bootstrap_env._check_python()


@pytest.mark.parametrize(
    "spoofed",
    [
        (3, 10, 18, "final", 0),  # below band
        (3, 13, 0, "final", 0),  # at exclusive upper bound
        (3, 14, 2, "final", 0),  # above band
        (2, 7, 18, "final", 0),  # legacy
    ],
)
def test_out_of_band_python_exits_nonzero(spoofed):
    with pytest.raises(SystemExit) as exc:
        bootstrap_env._check_python(version_info=spoofed)
    assert exc.value.code != 0


@pytest.mark.parametrize(
    "spoofed",
    [
        (3, 11, 0, "final", 0),
        (3, 11, 9, "final", 0),
        (3, 12, 0, "final", 0),
        (3, 12, 5, "final", 0),
    ],
)
def test_in_band_python_ok(spoofed):
    bootstrap_env._check_python(version_info=spoofed)


def test_run_via_monkeypatch_writes_and_is_idempotent(tmp_path, monkeypatch):
    # Redirect the script's output directory to a tmp path and stub the
    # subprocess-touching helpers so the test is hermetic.
    monkeypatch.setattr(bootstrap_env, "REPRO_DIR", tmp_path)
    monkeypatch.setattr(
        bootstrap_env, "_target_path", lambda today=None: tmp_path / "env_TEST.json"
    )
    monkeypatch.setattr(bootstrap_env, "_which_uv", lambda: "/stub/uv")
    monkeypatch.setattr(bootstrap_env, "_uv_version", lambda: "uv 0.4.18")
    monkeypatch.setattr(bootstrap_env, "_uv_pip_freeze", lambda: "numpy==2.1.0\n")
    monkeypatch.setattr(bootstrap_env, "_git_head", lambda: "deadbeef" * 5)

    rc1 = bootstrap_env.run([])
    assert rc1 == 0
    target = tmp_path / "env_TEST.json"
    assert target.exists()
    payload1 = json.loads(target.read_text(encoding="utf-8"))
    for key in (
        "python_version",
        "uv_version",
        "os",
        "cpu",
        "pip_freeze_sha256",
        "git_head",
        "timestamp_utc",
    ):
        assert key in payload1

    # Second run with same underlying state: file must remain identical.
    mtime_before = target.stat().st_mtime_ns
    rc2 = bootstrap_env.run([])
    assert rc2 == 0
    mtime_after = target.stat().st_mtime_ns
    assert mtime_before == mtime_after, "idempotent run should not rewrite file"


def test_print_only_does_not_write(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(bootstrap_env, "REPRO_DIR", tmp_path)
    monkeypatch.setattr(
        bootstrap_env, "_target_path", lambda today=None: tmp_path / "env_TEST.json"
    )
    monkeypatch.setattr(bootstrap_env, "_which_uv", lambda: "/stub/uv")
    monkeypatch.setattr(bootstrap_env, "_uv_version", lambda: "uv 0.4.18")
    monkeypatch.setattr(bootstrap_env, "_uv_pip_freeze", lambda: "numpy==2.1.0\n")
    monkeypatch.setattr(bootstrap_env, "_git_head", lambda: "abc123")

    rc = bootstrap_env.run(["--print-only"])
    assert rc == 0
    assert not (tmp_path / "env_TEST.json").exists()
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["git_head"] == "abc123"
    # Microsecond-resolution UTC timestamp per plan §9.3 (matches
    # ReproLog.capture in src/skie_ninja/utils/reproducibility.py).
    ts = payload["timestamp_utc"]
    # ISO-8601 with microseconds: has a '.' before the offset and 6 digits.
    assert "." in ts, ts
    frac = ts.split(".", 1)[1]
    # Strip timezone suffix (e.g. '+00:00').
    for sep in ("+", "-", "Z"):
        if sep in frac:
            frac = frac.split(sep, 1)[0]
            break
    microsecond_digits = 6  # ISO-8601 microsecond fractional-second field width
    assert len(frac) == microsecond_digits, (
        f"expected microsecond precision, got {payload['timestamp_utc']!r}"
    )
