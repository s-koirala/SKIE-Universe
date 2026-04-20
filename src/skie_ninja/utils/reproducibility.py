"""Reproducibility log.

Implements the JSON schema defined in
[plan/implementation-plan_2026-04-15.md §9.3]. Every run that writes
to `artifacts/` or `logs/` MUST emit one of these records so that
`scripts/verify_repro.py` (CI `repro-verify` stage) can re-execute
and assert byte equality on model hashes.

Field contract (§9.3):
    run_id, phase, hypothesis_id, timestamp_utc, git_head,
    pip_freeze_sha256, pip_freeze_path, dataset_checksums,
    rng_seed, model_hash, config_resolved_sha256, host, env_id.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from skie_ninja.utils.hashing import file_sha256
from skie_ninja.utils.paths import ProjectPaths

# Subprocess timeout for `git rev-parse` / `uv pip freeze`.
# Chosen to exceed the p99 wall time of both commands on a warm
# developer box (~2s observed) with margin for cold starts. Tunable
# via env var for constrained CI runners; not statistical.
_SUBPROCESS_TIMEOUT_SEC = int(os.environ.get("SKIE_SUBPROCESS_TIMEOUT_SEC", "30"))


@dataclass(frozen=True)
class ReproLog:
    run_id: str
    phase: str
    hypothesis_id: str
    timestamp_utc: str
    git_head: str
    pip_freeze_sha256: str
    pip_freeze_path: str
    dataset_checksums: dict[str, str]
    rng_seed: int
    model_hash: str | None
    config_resolved_sha256: str | None
    host: dict[str, str]
    env_id: str

    def to_dict(self) -> dict:
        return asdict(self)

    def write(self, path: Path) -> Path:
        """Atomically serialize this ReproLog to `path`.

        Write pattern: `NamedTemporaryFile` in the destination
        directory, `fsync`, then `os.replace` onto the target — this
        is atomic on POSIX and on Windows (MoveFileEx semantics per
        Python 3.3+ os.replace docs). Readers therefore never observe
        a partial file: either the previous version or the new
        version is visible.

        Limits: SIGKILL or `os._exit` terminate the process before
        `close`/`fsync` can run, so a crash strictly between the
        write and the rename may leave the tempfile on disk (the
        target is untouched). This is an accepted limitation of
        POSIX write semantics — no userspace pattern can defeat
        SIGKILL.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        data = json.dumps(
            payload, sort_keys=True, indent=2, ensure_ascii=False
        ).encode("utf-8")
        # Binary mode: Windows translates `\n` to `\r\n` in text mode,
        # which would break byte-identity checks against the canonical
        # serialization. `delete=False` so we can rename; `dir=path.parent`
        # keeps the rename same-filesystem (atomicity requirement).
        tmp = tempfile.NamedTemporaryFile(
            mode="wb",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        )
        try:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.replace(tmp.name, path)
        return path

    @staticmethod
    def read(path: Path) -> ReproLog:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return ReproLog(**payload)

    @staticmethod
    def verify(path: Path) -> bool:
        """Round-trip verification.

        Reads a ReproLog JSON, re-serializes with sorted keys, and
        compares against the on-disk bytes. Returns True iff the file
        is a canonical ReproLog serialization. Returns False on any
        construction error (missing fields, unknown fields, wrong
        types) so callers can treat corrupted logs as non-verifying
        rather than crashing.
        """
        try:
            on_disk = Path(path).read_text(encoding="utf-8")
            payload = json.loads(on_disk)
            parsed = ReproLog(**payload)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return False
        canonical = json.dumps(parsed.to_dict(), sort_keys=True, indent=2, ensure_ascii=False)
        return on_disk == canonical


def _git_head(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=_SUBPROCESS_TIMEOUT_SEC,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def _pip_freeze_bytes() -> bytes:
    # Prefer `uv pip freeze` per project tooling default; fall back
    # to `python -m pip freeze` so the capture succeeds in minimal
    # CI images where uv may be absent.
    for cmd in (["uv", "pip", "freeze"], [sys.executable, "-m", "pip", "freeze"]):
        try:
            out = subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                timeout=_SUBPROCESS_TIMEOUT_SEC,
            )
            return out.stdout
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return b""


def _host_info() -> dict[str, str]:
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "cpu": platform.machine(),
    }


def _posix(path: Path) -> str:
    return str(PurePosixPath(*Path(path).parts))


def _make_run_id() -> str:
    # ULID when available (lexicographically sortable, time-ordered);
    # uuid4 otherwise. Lexical-sort property is convenient for
    # on-disk log ordering but is not a correctness requirement, so
    # the fallback is acceptable.
    try:
        import ulid  # type: ignore

        return str(ulid.new())
    except ImportError:
        import uuid

        return uuid.uuid4().hex


def capture(
    *,
    phase: str,
    hypothesis_id: str,
    rng_seed: int,
    dataset_checksums: dict[str, str] | None = None,
    model_hash: str | None = None,
    config_resolved_sha256: str | None = None,
    env_id: str | None = None,
    paths: ProjectPaths | None = None,
    run_id: str | None = None,
) -> ReproLog:
    """Build a ReproLog from the current process state.

    Pure w.r.t. inputs given identical git/pip state — two successive
    calls differ only in `timestamp_utc` (and `run_id` if auto-made).
    """
    paths = paths or ProjectPaths.discover()
    paths.ensure(paths.logs_reproducibility_env)

    freeze_bytes = _pip_freeze_bytes()
    import hashlib

    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    freeze_path = paths.logs_reproducibility_env / f"{freeze_sha}.txt"
    if not freeze_path.exists():
        freeze_path.write_bytes(freeze_bytes)

    uv_lock = paths.root / "uv.lock"
    lock_id = file_sha256(uv_lock) if uv_lock.is_file() else "no-uv-lock"

    return ReproLog(
        run_id=run_id or _make_run_id(),
        phase=phase,
        hypothesis_id=hypothesis_id,
        timestamp_utc=datetime.now(UTC).isoformat(timespec="microseconds"),
        git_head=_git_head(paths.root),
        pip_freeze_sha256=freeze_sha,
        pip_freeze_path=_posix(freeze_path.relative_to(paths.root)),
        dataset_checksums=dict(dataset_checksums or {}),
        rng_seed=rng_seed,
        model_hash=model_hash,
        config_resolved_sha256=config_resolved_sha256,
        host=_host_info(),
        env_id=env_id or lock_id,
    )


def with_model_hash(log: ReproLog, model_hash: str) -> ReproLog:
    return replace(log, model_hash=model_hash)
