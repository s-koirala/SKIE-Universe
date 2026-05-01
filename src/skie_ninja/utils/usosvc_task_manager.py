"""USOSvc reboot-task management — Layer 5 protection per ADR-0010.

Wraps the PowerShell helper at
[scripts/preflight/manage_usosvc_reboot_tasks.ps1](
../../scripts/preflight/manage_usosvc_reboot_tasks.ps1) so the supervisor
can disable / re-enable the USOSvc internal reboot tasks under
``\\Microsoft\\Windows\\UpdateOrchestrator\\`` for the duration of a
walk-forward run.

Per the H050 production-run post-mortem
([docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md §5.2](
../../../../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md)):
the reboot path on Windows-11 Home (the H050 host) is the internal UsoSvc
Task Scheduler tree (``Reboot_AC``, ``Reboot_Battery``,
``Universal Orchestrator Start``), NOT WUfB. Disabling these tasks for the
run window is the canonical mitigation; this module is the canonical
caller.

Usage from the supervisor (wired via ``scripts/supervised_run.py`` per
ADR-0010 §Layer 5):

    from skie_ninja.utils.usosvc_task_manager import disable_for_run, restore_after_run
    state_path = run_dir / "_usosvc_disable_state.json"
    result = disable_for_run(state_path)
    try:
        ... long-running compute ...
    finally:
        restore_after_run(state_path)

Cross-platform: on non-Windows hosts, all functions return a
``{"action": ..., "skipped": "non-windows"}`` envelope without invoking
the PS1 helper. The supervisor + tests can call them safely on Linux CI.

API scope (per Round-1 quant audit F-1-1 / F-1-9 remediation):
the wrapper does NOT expose ``task_patterns`` or ``task_folder``
overrides. The PS1 defaults are pinned at the canonical post-mortem §5.2
task set (``Reboot_AC``, ``Reboot_Battery``, ``Universal Orchestrator Start``).
Operators needing alternative task sets should invoke the PS1 directly.
This eliminates a PowerShell array-binding-via-argv hazard (where a
comma-joined string becomes a single-element array, silently disabling
nothing) and a subprocess-injection-vector (where unsanitised pattern
strings reach `cmd /c schtasks` via the PS1 helper).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skie_ninja.utils.paths import ProjectPaths

_log = logging.getLogger(__name__)

# Module-level constants
_PS1_RELATIVE_PATH = Path("scripts") / "preflight" / "manage_usosvc_reboot_tasks.ps1"

# justify: USOSvc Task Scheduler reboot tasks per Microsoft Update Orchestrator
# documentation + post-mortem §5.2. These are the canonical 3 tasks
# documented as the OS-initiated-reboot path on Windows-11 Home. Operators
# needing additional patterns should invoke the PS1 directly with an
# explicit ``-TaskPatterns`` argument; tracked under follow-up
# `P1-USOSVC-TASK-PATTERN-VERSION-DRIFT` if the canonical set changes.
_DEFAULT_TASK_PATTERNS: tuple[str, ...] = (
    "Reboot_AC",
    "Reboot_Battery",
    "Universal Orchestrator Start",
)
_DEFAULT_TASK_FOLDER: str = "\\Microsoft\\Windows\\UpdateOrchestrator\\"


@dataclass(frozen=True)
class USOSvcResult:
    """Result of a USOSvc-task-manager invocation."""

    action: str                # "List" | "Disable" | "Enable" | "skipped"
    ok: bool                   # True iff the helper exited 0
    exit_code: int             # PS1 exit code (0/1/2/3)
    skipped_reason: str | None = None   # populated when action="skipped"
    payload: dict[str, Any] | None = None
    stderr: str | None = None

    def needs_elevation(self) -> bool:
        return self.exit_code == 2


def _is_windows() -> bool:
    return sys.platform == "win32"


def _resolve_ps1_path(repo_root: Path | None = None) -> Path:
    """Resolve the absolute path of the PS1 helper.

    Tests pass ``repo_root`` explicitly; production callers omit it and
    rely on ``ProjectPaths.discover()`` per the project's paths-guard
    convention (file-based root resolution is the monopoly of
    utils/paths.py; verified by tests/unit/test_paths.py).
    """
    if repo_root is None:
        repo_root = ProjectPaths.discover().root
    return (repo_root / _PS1_RELATIVE_PATH).resolve()


def _invoke_ps1(
    action: str,
    *,
    state_path: Path | None = None,
    repo_root: Path | None = None,
    timeout_sec: int = 60,
) -> USOSvcResult:
    """Invoke the PS1 helper. On non-Windows, return a skipped envelope."""
    if not _is_windows():
        return USOSvcResult(
            action="skipped",
            ok=True,
            exit_code=0,
            skipped_reason="non-windows host",
        )
    ps1_path = _resolve_ps1_path(repo_root=repo_root)
    if not ps1_path.exists():
        return USOSvcResult(
            action=action,
            ok=False,
            exit_code=-1,
            stderr=f"PS1 helper not found at {ps1_path}",
        )
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", str(ps1_path),
        "-Action", action,
    ]
    if state_path is not None:
        cmd.extend(["-StatePath", str(state_path)])

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_sec, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return USOSvcResult(
            action=action,
            ok=False,
            exit_code=-1,
            stderr=f"Timeout after {timeout_sec}s: {exc}",
        )
    payload = None
    if proc.stdout:
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"raw_stdout": proc.stdout}
    return USOSvcResult(
        action=action,
        ok=(proc.returncode == 0),
        exit_code=proc.returncode,
        payload=payload,
        stderr=proc.stderr if proc.stderr else None,
    )


def list_tasks(*, repo_root: Path | None = None) -> USOSvcResult:
    """List the USOSvc reboot tasks. Read-only operation.

    Per ADR-0010 Layer 5 §"List subaction": no state change; safe to
    invoke at preflight time without the run window risk.
    """
    return _invoke_ps1("List", repo_root=repo_root)


def disable_for_run(
    state_path: Path,
    *,
    repo_root: Path | None = None,
) -> USOSvcResult:
    """Disable USOSvc reboot tasks; persist prior state to state_path.

    Per ADR-0010 Layer 5: must be paired with ``restore_after_run``
    (typically in a try/finally around the orchestrator's main body).
    Cross-platform-safe: on non-Windows hosts, returns the skipped
    envelope without creating the state file or invoking PS1.
    """
    if not _is_windows():
        return USOSvcResult(
            action="skipped",
            ok=True,
            exit_code=0,
            skipped_reason="non-windows host",
        )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    return _invoke_ps1(
        "Disable",
        state_path=state_path,
        repo_root=repo_root,
    )


def restore_after_run(
    state_path: Path,
    *,
    repo_root: Path | None = None,
) -> USOSvcResult:
    """Restore USOSvc reboot tasks to their pre-run state.

    Idempotent: safe to call even if disable_for_run failed mid-way.

    Per Round-1 quant audit F-1-2 fix: the non-Windows skip envelope
    is checked BEFORE the state-file existence guard so the supervisor's
    try/finally cleanup logs a consistent ``{action: 'skipped'}`` on
    Linux CI rather than spuriously raising "state path does not exist"
    when ``disable_for_run`` was a non-Windows no-op.

    On Windows: if state_path does not exist, returns ``ok=False`` with
    ``exit_code=3`` (the helper's no-state error).
    """
    if not _is_windows():
        return USOSvcResult(
            action="skipped",
            ok=True,
            exit_code=0,
            skipped_reason="non-windows host",
        )
    if not state_path.exists():
        return USOSvcResult(
            action="Enable",
            ok=False,
            exit_code=3,
            stderr=f"State path {state_path} does not exist; cannot restore.",
        )
    return _invoke_ps1(
        "Enable",
        state_path=state_path,
        repo_root=repo_root,
    )


__all__ = [
    "USOSvcResult",
    "disable_for_run",
    "list_tasks",
    "restore_after_run",
]
