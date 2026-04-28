"""Regression tests for ADR-0010 Layer 4 — supervisor classification.

The supervisor at [scripts/supervised_run.py](../../scripts/supervised_run.py)
classifies orchestrator subprocess exits into one of:

  - ``clean_exit_success`` (rc=0 + ``PROGRESS run done``)
  - ``clean_exit_python_exception`` (rc != 0 + ``PROGRESS <phase> failed``)
  - ``external_kill_or_segfault`` (rc != 0 + no failed marker; orphan start)
  - ``ambiguous`` (rc=0 but no run done; or rc != 0 but neither)

These tests lock the classification matrix into CI so a future
refactor cannot silently change which condition the supervisor
treats as success.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_supervisor_module():
    name = "_supervised_run_for_test"
    spec = importlib.util.spec_from_file_location(
        name,
        Path(__file__).resolve().parents[2] / "scripts" / "supervised_run.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_MOD = _load_supervisor_module()
_classify_exit = _MOD._classify_exit


# Helper: shape of a typical PROGRESS line as it appears in the JSON log.
def _progress(msg: str) -> str:
    return f'{{"msg": "{msg}", "level": "INFO"}}'


class TestClassifyExit:
    def test_clean_success(self) -> None:
        lines = [
            _progress("PROGRESS run start | config=H050.yaml"),
            _progress("PROGRESS symbol start | sym=ES"),
            _progress("PROGRESS symbol done elapsed=42.000s | sym=ES"),
            _progress("PROGRESS run done elapsed=12345.0s | run_id=abc"),
        ]
        result = _classify_exit(rc=0, last_progress_lines=lines)
        assert result["classification"] == "clean_exit_success"
        assert result["rc"] == 0

    def test_python_exception(self) -> None:
        lines = [
            _progress("PROGRESS run start | config=H050.yaml"),
            _progress("PROGRESS symbol start | sym=ES"),
            _progress("PROGRESS hmm-fit start | sym=ES fold_id=0"),
            _progress("PROGRESS hmm-fit failed elapsed=5.0s exc=ValueError | sym=ES fold_id=0"),
            _progress("PROGRESS symbol failed elapsed=6.0s exc=ValueError | sym=ES"),
            _progress("PROGRESS run failed elapsed=7.0s exc=ValueError | config=H050.yaml"),
        ]
        result = _classify_exit(rc=1, last_progress_lines=lines)
        assert result["classification"] == "clean_exit_python_exception"
        assert "failed marker present" in result["note"]

    def test_external_kill(self) -> None:
        # The prod-run-2 failure mode: orphan starts, no done, no failed.
        lines = [
            _progress("PROGRESS run start | config=H050.yaml"),
            _progress("PROGRESS symbol start | sym=ES"),
            _progress("PROGRESS label-cfg start | sym=ES"),
            _progress("PROGRESS fold-fit start | sym=ES fold_id=0"),
            _progress("PROGRESS hmm-fit start | sym=ES fold_id=0"),
            # Process killed externally; no further lines.
        ]
        # On Windows external kill, exit code is typically negative or 1
        # depending on signal; non-zero is the only invariant.
        result = _classify_exit(rc=1, last_progress_lines=lines)
        assert result["classification"] == "external_kill_or_segfault"
        assert result["n_orphan_starts"] >= 1
        assert "Kernel-Power Event 109" in result["note"]
        assert "BugCheck" in result["note"]

    def test_ambiguous_rc_zero_no_done(self) -> None:
        # rc=0 but no run-done marker — uncommon; flag for inspection.
        lines = [
            _progress("PROGRESS run start | config=H050.yaml"),
            _progress("PROGRESS symbol start | sym=ES"),
        ]
        result = _classify_exit(rc=0, last_progress_lines=lines)
        assert result["classification"] == "ambiguous"

    def test_external_kill_orphan_count_correct(self) -> None:
        # 3 starts, 1 done → 2 orphans.
        lines = [
            _progress("PROGRESS run start | x=1"),
            _progress("PROGRESS symbol start | x=1"),
            _progress("PROGRESS symbol done elapsed=1.0s | x=1"),
            _progress("PROGRESS symbol start | x=2"),
            _progress("PROGRESS hmm-fit start | x=2 fold_id=0"),
        ]
        result = _classify_exit(rc=1, last_progress_lines=lines)
        assert result["classification"] == "external_kill_or_segfault"
        # Starts: run, symbol(x=1), symbol(x=2), hmm-fit = 4
        # Done/failed: symbol done(x=1) = 1
        # Orphans: 4 - 1 = 3
        assert result["n_orphan_starts"] == 3

    def test_empty_log_is_external_kill(self) -> None:
        # No PROGRESS lines at all (rare; would indicate stdout never
        # flushed) — classify as external kill, not ambiguous.
        result = _classify_exit(rc=1, last_progress_lines=[])
        assert result["classification"] == "external_kill_or_segfault"
        assert result["n_orphan_starts"] == 0


class TestPreflightHandling:
    """Verify the preflight wrapper handles missing scripts +
    PowerShell errors gracefully (Round-2 Q-1-4 + R-4)."""

    def test_run_preflight_returns_warn_on_missing_script_on_windows(
        self, tmp_path: Path
    ) -> None:
        # Q-1-4: missing script must NOT silently pass. Force Windows
        # path via the module's own `sys` import so the test runs on
        # any host.
        from unittest.mock import patch

        missing = tmp_path / "does_not_exist.ps1"
        with patch.object(_MOD.sys, "platform", "win32"):
            rc, payload = _MOD._run_preflight(missing)
        assert rc == 2
        assert payload is not None
        assert payload.get("status") == "warn"

    def test_run_preflight_skips_on_non_windows(self, tmp_path: Path) -> None:
        # R-4: non-Windows must return rc=0 + status=non-windows-skip.
        # Force the platform check to return non-Windows.
        from unittest.mock import patch

        # _run_preflight reads sys.platform directly via the module's
        # `sys` import. Patch it.
        with patch.object(_MOD.sys, "platform", "linux"):
            rc, payload = _MOD._run_preflight(tmp_path / "irrelevant.ps1")
        assert rc == 0
        assert payload is not None
        assert payload.get("status") == "non-windows-skip"


class TestResumeArgparseReject:
    """Round-2 Q-1-12: --resume now rejected at argparse time
    (SystemExit) so the operator gets an immediate error rather
    than a config-load failure or a NotImplementedError after
    other arg validation has run."""

    def test_orchestrator_resume_flag_rejected_at_argparse(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "_run_walk_forward_for_resume_test",
            Path(__file__).resolve().parents[2] / "scripts" / "run_walk_forward.py",
        )
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_run_walk_forward_for_resume_test"] = mod
        spec.loader.exec_module(mod)

        # argparse.error() raises SystemExit with rc=2.
        with pytest.raises(SystemExit) as exc_info:
            mod._parse_args(
                [
                    "--hypothesis", "H050",
                    "--config", "config/hypotheses/H050.yaml",
                    "--resume", "abc123",
                ]
            )
        # argparse.ArgumentParser.error sets rc=2 by convention.
        assert exc_info.value.code == 2

    def test_orchestrator_no_resume_flag_parses_cleanly(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "_run_walk_forward_for_no_resume_test",
            Path(__file__).resolve().parents[2] / "scripts" / "run_walk_forward.py",
        )
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_run_walk_forward_for_no_resume_test"] = mod
        spec.loader.exec_module(mod)

        args = mod._parse_args(
            [
                "--hypothesis", "H050",
                "--config", "config/hypotheses/H050.yaml",
            ]
        )
        assert args.resume is None


class TestSupervisorMaxRuntime:
    """Round-2 Q-1-3: --max-runtime-s caps the total wall-clock."""

    def test_default_max_runtime_is_36_hours(self) -> None:
        assert _MOD._DEFAULT_MAX_RUNTIME_S == 36.0 * 3600.0

    def test_supervisor_parser_accepts_max_runtime_flag(self) -> None:
        args = _MOD._parse_args(
            [
                "--hypothesis", "H050",
                "--config", "config/hypotheses/H050.yaml",
                "--max-runtime-s", "120",
            ]
        )
        assert args.max_runtime_s == 120.0


class TestSupervisorActiveHoursCheck:
    """Round-2 Q-1-5 + R-6: --expected-runtime-h is forwarded to
    the preflight."""

    def test_default_expected_runtime_is_22h(self) -> None:
        assert _MOD._DEFAULT_EXPECTED_RUNTIME_H == 22

    def test_supervisor_parser_accepts_expected_runtime_flag(self) -> None:
        args = _MOD._parse_args(
            [
                "--hypothesis", "H050",
                "--config", "config/hypotheses/H050.yaml",
                "--expected-runtime-h", "10",
            ]
        )
        assert args.expected_runtime_h == 10
