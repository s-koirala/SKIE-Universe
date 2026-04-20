"""Bootstrap & environment-audit script (plan §P0-8, §9.3).

Read-only checks:
  1. Active Python interpreter sits inside the project-supported band
     ``[3.11, 3.13)`` — matches ``requires-python`` in ``pyproject.toml``.
  2. ``uv`` is on PATH (the pinned project env manager, per CLAUDE.md).

Side effects:
  * Writes ``logs/reproducibility/env_{YYYYMMDD}.json`` with the fields
    listed in plan §9.3 host/env block. Idempotent for a given UTC day:
    if the file already exists and its content matches the freshly
    computed payload (modulo ``timestamp_utc``), it is not rewritten.

Exit codes:
  * 0 — all checks pass, audit file present/updated.
  * non-zero — any check failed; no audit file is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Script-bootstrap sys.path shim: this file is executed by operators
# *before* `uv pip install -e .` has succeeded (auditing the env that
# will later install the package). We therefore cannot rely on
# `skie_ninja` being importable yet, and must locate the project
# source directory ourselves with one carefully marked exception to
# the paths-guard rule.
_SCRIPT_DIR = Path(__file__).resolve().parent  # paths-guard: allow (script bootstrap)
sys.path.insert(0, str(_SCRIPT_DIR.parent / "src"))

from skie_ninja.utils.paths import ProjectPaths  # noqa: E402

# Python version band — sourced directly from pyproject ``requires-python``.
PY_MIN: tuple[int, int] = (3, 11)
PY_MAX_EXCLUSIVE: tuple[int, int] = (3, 13)

_PATHS: ProjectPaths = ProjectPaths.discover(_SCRIPT_DIR)
REPO_ROOT: Path = _PATHS.root
REPRO_DIR: Path = _PATHS.logs_reproducibility
TIMESTAMP_FIELD: str = "timestamp_utc"


def _check_python(version_info: tuple[int, int, int, str, int] | None = None) -> None:
    v = version_info or sys.version_info
    vt = (v[0], v[1])
    if not (PY_MIN <= vt < PY_MAX_EXCLUSIVE):
        raise SystemExit(
            f"[bootstrap_env] Python {v[0]}.{v[1]}.{v[2]} outside supported "
            f"band [{PY_MIN[0]}.{PY_MIN[1]}, {PY_MAX_EXCLUSIVE[0]}.{PY_MAX_EXCLUSIVE[1]}). "
            f"Use uv to provision a compatible interpreter."
        )


def _which_uv() -> str:
    path = shutil.which("uv")
    if path is None:
        raise SystemExit(
            "[bootstrap_env] `uv` not found on PATH. Install per "
            "https://docs.astral.sh/uv/ and retry."
        )
    return path


def _uv_version() -> str:
    out = subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True)
    return out.stdout.strip()


def _uv_pip_freeze() -> str:
    out = subprocess.run(["uv", "pip", "freeze"], check=True, capture_output=True, text=True)
    return out.stdout


def _git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_payload() -> dict[str, object]:
    freeze_text = _uv_pip_freeze()
    return {
        "python_version": platform.python_version(),
        "uv_version": _uv_version(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu": platform.processor() or platform.machine(),
        "pip_freeze_sha256": _sha256(freeze_text),
        "git_head": _git_head(),
        TIMESTAMP_FIELD: datetime.now(UTC).isoformat(timespec="microseconds"),
    }


def _strip_ts(payload: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in payload.items() if k != TIMESTAMP_FIELD}


def _target_path(today: str | None = None) -> Path:
    stamp = today or datetime.now(UTC).strftime("%Y%m%d")
    return REPRO_DIR / f"env_{stamp}.json"


def write_audit(payload: dict[str, object], target: Path) -> bool:
    """Return True if the file was written (or rewritten), False if skipped."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = None
        if isinstance(existing, dict) and _strip_ts(existing) == _strip_ts(payload):
            return False
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return True


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SKIE-Ninja env bootstrap audit.")
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Run checks and print the payload but do not write the audit file.",
    )
    args = parser.parse_args(argv)

    _check_python()
    _which_uv()
    payload = _build_payload()

    if args.print_only:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    target = _target_path()
    wrote = write_audit(payload, target)
    status = "wrote" if wrote else "unchanged"
    try:
        display = target.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        display = target.as_posix()
    print(f"[bootstrap_env] {status}: {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
