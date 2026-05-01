"""Unit tests for the USOSvc task-manager wrapper.

Tests use ``unittest.mock.patch`` to stub out ``subprocess.run`` so they
pass on Linux/macOS CI. The PS1 helper itself is verified by the
operator smoke capture at ``logs/preflight/usosvc_helper_smoke_*.txt``
on the Windows host (Round-1 audit F-1-5 closure artifact).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from skie_ninja.utils.usosvc_task_manager import (
    USOSvcResult,
    _DEFAULT_TASK_FOLDER,
    _DEFAULT_TASK_PATTERNS,
    _resolve_ps1_path,
    disable_for_run,
    list_tasks,
    restore_after_run,
)


# ---------------------------------------------------------------------------
# Cross-platform skip envelope
# ---------------------------------------------------------------------------


class TestNonWindowsSkip:
    """On non-Windows hosts, all callers must return a skipped envelope
    without invoking the PS1 helper."""

    def test_list_tasks_skips_on_non_windows(self):
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=False):
            result = list_tasks()
        assert result.action == "skipped"
        assert result.ok is True
        assert result.skipped_reason == "non-windows host"

    def test_disable_for_run_skips_on_non_windows(self, tmp_path: Path):
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=False):
            result = disable_for_run(tmp_path / "state.json")
        assert result.action == "skipped"
        assert result.ok is True

    def test_disable_for_run_skip_does_not_create_state_file(self, tmp_path: Path):
        """F-1-2 fix: disable_for_run on non-Windows must NOT create the
        state file (mirrors the supervisor expectation that disable was
        a no-op skip)."""
        state = tmp_path / "newdir" / "state.json"
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=False):
            disable_for_run(state)
        assert not state.parent.exists()
        assert not state.exists()

    def test_restore_after_run_skips_on_non_windows_with_state_file(self, tmp_path: Path):
        state = tmp_path / "state.json"
        state.write_text("{}", encoding="utf-8")
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=False):
            result = restore_after_run(state)
        assert result.action == "skipped"
        assert result.ok is True

    def test_restore_after_run_skips_on_non_windows_without_state_file(
        self, tmp_path: Path
    ):
        """F-1-2 critical regression: cross-platform skip envelope must
        precede the state-existence check. If disable_for_run was a
        non-Windows no-op (no state file written), restore_after_run
        on the same non-Windows host must return skipped, NOT exit_code=3."""
        nonexistent = tmp_path / "missing.json"
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=False):
            result = restore_after_run(nonexistent)
        assert result.action == "skipped"
        assert result.ok is True
        assert result.skipped_reason == "non-windows host"


# ---------------------------------------------------------------------------
# Restore-without-state error path on Windows
# ---------------------------------------------------------------------------


class TestRestoreNoStateOnWindows:
    def test_restore_without_state_file_returns_exit_code_3_on_windows(
        self, tmp_path: Path
    ):
        nonexistent = tmp_path / "missing.json"
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=True):
            result = restore_after_run(nonexistent)
        assert result.ok is False
        assert result.exit_code == 3
        assert "does not exist" in (result.stderr or "")


# ---------------------------------------------------------------------------
# PS1 invocation (mocked subprocess) — Windows path only
# ---------------------------------------------------------------------------


class TestPS1InvocationMocked:
    """Mock subprocess.run + sys.platform to exercise the Windows path
    on a non-Windows runner."""

    def test_list_tasks_parses_json_payload(self, tmp_path: Path):
        fake_payload = {
            "action": "List",
            "task_folder": _DEFAULT_TASK_FOLDER,
            "patterns": list(_DEFAULT_TASK_PATTERNS),
            "tasks": [
                {"task_name": "Reboot_AC", "state": "Ready", "present": True},
                {"task_name": "Reboot_Battery", "state": "Disabled", "present": True},
            ],
            "ts": "2026-04-30T22:30:00-05:00",
        }
        mock_proc = MagicMock(returncode=0, stdout=json.dumps(fake_payload), stderr="")
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=True), \
             patch("skie_ninja.utils.usosvc_task_manager._resolve_ps1_path",
                   return_value=tmp_path / "fake.ps1"), \
             patch("subprocess.run", return_value=mock_proc) as run_mock:
            (tmp_path / "fake.ps1").write_text("# stub", encoding="utf-8")
            result = list_tasks(repo_root=tmp_path.parent)
        assert result.ok is True
        assert result.exit_code == 0
        assert result.action == "List"
        assert result.payload is not None
        assert len(result.payload["tasks"]) == 2
        # subprocess.run argv must contain '-Action' followed by 'List'
        called_cmd = run_mock.call_args.args[0]
        assert "List" in called_cmd
        # F-1-1 fix verification: no -TaskPatterns / -TaskFolder overrides
        # are passed from the wrapper; the PS1 default is the source of
        # truth (eliminates the comma-joined-string array-binding bug).
        assert "-TaskPatterns" not in called_cmd
        assert "-TaskFolder" not in called_cmd

    def test_disable_invokes_ps1_with_state_path_arg(self, tmp_path: Path):
        state = tmp_path / "state.json"
        fake_payload = {
            "action": "Disable",
            "task_folder": _DEFAULT_TASK_FOLDER,
            "any_failed": False,
            "needs_elevation": False,
            "ts": "2026-04-30T22:30:00-05:00",
        }
        mock_proc = MagicMock(returncode=0, stdout=json.dumps(fake_payload), stderr="")
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=True), \
             patch("skie_ninja.utils.usosvc_task_manager._resolve_ps1_path",
                   return_value=tmp_path / "fake.ps1"), \
             patch("subprocess.run", return_value=mock_proc) as run_mock:
            (tmp_path / "fake.ps1").write_text("# stub", encoding="utf-8")
            result = disable_for_run(state, repo_root=tmp_path.parent)
        assert result.ok
        assert result.action == "Disable"
        called_cmd = run_mock.call_args.args[0]
        assert "Disable" in called_cmd
        assert str(state) in called_cmd

    def test_disable_elevation_required_returns_exit_code_2(self, tmp_path: Path):
        state = tmp_path / "state.json"
        mock_proc = MagicMock(
            returncode=2,
            stdout=json.dumps({"any_failed": True, "needs_elevation": True}),
            stderr="",
        )
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=True), \
             patch("skie_ninja.utils.usosvc_task_manager._resolve_ps1_path",
                   return_value=tmp_path / "fake.ps1"), \
             patch("subprocess.run", return_value=mock_proc):
            (tmp_path / "fake.ps1").write_text("# stub", encoding="utf-8")
            result = disable_for_run(state, repo_root=tmp_path.parent)
        assert result.ok is False
        assert result.exit_code == 2
        assert result.needs_elevation()

    def test_disable_creates_state_path_parent_dir(self, tmp_path: Path):
        state = tmp_path / "newdir" / "deeper" / "state.json"
        assert not state.parent.exists()
        mock_proc = MagicMock(returncode=0, stdout="{}", stderr="")
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=True), \
             patch("skie_ninja.utils.usosvc_task_manager._resolve_ps1_path",
                   return_value=tmp_path / "fake.ps1"), \
             patch("subprocess.run", return_value=mock_proc):
            (tmp_path / "fake.ps1").write_text("# stub", encoding="utf-8")
            disable_for_run(state, repo_root=tmp_path.parent)
        assert state.parent.exists()

    def test_subprocess_timeout_returns_negative_exit_code(self, tmp_path: Path):
        """F-1-10 coverage: subprocess.TimeoutExpired branch."""
        import subprocess as sp
        state = tmp_path / "state.json"
        with patch("skie_ninja.utils.usosvc_task_manager._is_windows", return_value=True), \
             patch("skie_ninja.utils.usosvc_task_manager._resolve_ps1_path",
                   return_value=tmp_path / "fake.ps1"), \
             patch("subprocess.run", side_effect=sp.TimeoutExpired(cmd="x", timeout=60)):
            (tmp_path / "fake.ps1").write_text("# stub", encoding="utf-8")
            result = disable_for_run(state, repo_root=tmp_path.parent)
        assert result.ok is False
        assert result.exit_code == -1
        assert "Timeout" in (result.stderr or "")


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


class TestPS1PathResolution:
    def test_resolve_ps1_path_with_explicit_root(self, tmp_path: Path):
        path = _resolve_ps1_path(repo_root=tmp_path)
        assert path == (tmp_path / "scripts" / "preflight" / "manage_usosvc_reboot_tasks.ps1").resolve()

    def test_resolve_ps1_path_uses_project_paths_discover(self):
        """F-paths-guard fix: resolution goes through ProjectPaths.discover()
        rather than file-based __file__ walking."""
        path = _resolve_ps1_path()
        assert path.name == "manage_usosvc_reboot_tasks.ps1"
        assert path.parent.name == "preflight"
        # Sanity: the resolved path is under the repo root
        assert "scripts" in path.parts


# ---------------------------------------------------------------------------
# Default task patterns + folder are the canonical post-mortem §5.2 set
# ---------------------------------------------------------------------------


class TestDefaultTaskPatterns:
    def test_default_patterns_match_canonical_post_mortem_set(self):
        """F-1-4 fix: default patterns are the canonical 3 from
        post-mortem §5.2; extras (Schedule Reboot, Schedule Wakeup) are
        operator-supplied with documented rationale."""
        assert _DEFAULT_TASK_PATTERNS == (
            "Reboot_AC",
            "Reboot_Battery",
            "Universal Orchestrator Start",
        )

    def test_default_task_folder_is_update_orchestrator(self):
        assert _DEFAULT_TASK_FOLDER == "\\Microsoft\\Windows\\UpdateOrchestrator\\"
