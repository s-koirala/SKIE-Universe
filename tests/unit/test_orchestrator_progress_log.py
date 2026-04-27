"""Regression tests for P1-ORCHESTRATOR-PROGRESS-LOGGING.

The `_ProgressLog` helper in ``scripts/run_walk_forward.py`` emits
matched start/done INFO markers around the orchestrator's load-bearing
phases (``run``, ``symbol``, ``label-cfg``, ``fold-fit``, ``hmm-fit``,
``inner-cv-lgb``). These tests lock the message shape + elapsed-timing
behaviour into CI so a future drift cannot silently revert the
observability fix without a test failure.
"""

from __future__ import annotations

import importlib.util
import logging
import re
import sys
import time
from pathlib import Path

import pytest


def _load_orchestrator_module():
    """Load scripts/run_walk_forward.py as a module without invoking
    its CLI entrypoint. Reused by every test in this file. The module
    must be registered in sys.modules before exec_module so that
    dataclass introspection (which calls sys.modules[cls.__module__])
    can resolve the module's namespace."""
    name = "_run_walk_forward_for_test"
    spec = importlib.util.spec_from_file_location(
        name,
        Path(__file__).resolve().parents[2] / "scripts" / "run_walk_forward.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_MOD = _load_orchestrator_module()
_ProgressLog = _MOD._ProgressLog
_kv = _MOD._kv


@pytest.fixture(autouse=True)
def _reset_module_singleton_progress_t0() -> None:
    """Round-1 Q-1-2 / Q-1-5 + Round-2 Q-2-5: clear cross-test
    state from the module singletons. ``_PROGRESS._t0`` accumulates
    keys across in-process invocations; the four ``ContextVar``s in
    ``logging_setup`` (run_id / phase / hypothesis_id / git_head)
    likewise persist across tests after a `RunContext` enter without
    a matching exit-time reset. Clearing both defends against
    test-order-dependent failures."""
    _MOD._PROGRESS._t0.clear()
    from skie_ninja.utils.logging_setup import bind_context

    bind_context(run_id="", phase="", hypothesis_id="", git_head="")


class TestProgressLogHelper:
    def test_start_emits_info_record_with_phase_and_kv_context(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        log = logging.getLogger("test-progress-1")
        progress = _ProgressLog(log)
        with caplog.at_level(logging.INFO, logger="test-progress-1"):
            progress.start("symbol", sym="ES", n_folds=4)
        records = [r for r in caplog.records if r.name == "test-progress-1"]
        assert len(records) == 1
        msg = records[0].getMessage()
        assert "PROGRESS symbol start" in msg
        assert "sym=ES" in msg
        assert "n_folds=4" in msg

    def test_done_emits_elapsed_with_seconds_format(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        log = logging.getLogger("test-progress-2")
        progress = _ProgressLog(log)
        with caplog.at_level(logging.INFO, logger="test-progress-2"):
            progress.start("hmm-fit", sym="ES", fold_id=0)
            time.sleep(0.05)
            elapsed = progress.done("hmm-fit", sym="ES", fold_id=0, best_cov="diag")
        records = [r for r in caplog.records if r.name == "test-progress-2"]
        assert len(records) == 2
        assert "PROGRESS hmm-fit start" in records[0].getMessage()
        done_msg = records[1].getMessage()
        assert re.match(
            r"PROGRESS hmm-fit done elapsed=\d+\.\d{3}s \| sym=ES fold_id=0 best_cov=diag",
            done_msg,
        ), f"done message did not match expected shape: {done_msg!r}"
        assert elapsed >= 0.05

    def test_done_without_start_uses_zero_elapsed_safely(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        log = logging.getLogger("test-progress-3")
        progress = _ProgressLog(log)
        with caplog.at_level(logging.INFO, logger="test-progress-3"):
            elapsed = progress.done("orphan-phase", sym="ES")
        # The pop() default is time.perf_counter() — elapsed should be
        # essentially zero (no negative; small positive).
        assert 0.0 <= elapsed < 0.1
        records = [r for r in caplog.records if r.name == "test-progress-3"]
        assert len(records) == 1
        assert "PROGRESS orphan-phase done elapsed=" in records[0].getMessage()

    def test_repeated_start_overwrites_t0(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Re-entering the same phase before its done() restarts the
        timer — correct for the orchestrator's single-threaded
        sequential structure where nested phases use distinct names."""
        log = logging.getLogger("test-progress-4")
        progress = _ProgressLog(log)
        with caplog.at_level(logging.INFO, logger="test-progress-4"):
            progress.start("phase-A")
            time.sleep(0.10)  # would have been the elapsed if not overwritten
            progress.start("phase-A")  # restart
            time.sleep(0.02)
            elapsed = progress.done("phase-A")
        # Elapsed measures from the SECOND start, not the first.
        assert elapsed < 0.08, (
            f"elapsed should reflect the restart, not the original start; got {elapsed:.3f}s"
        )

    def test_kv_helper_serialisation(self) -> None:
        assert _kv({}) == ""
        assert _kv({"sym": "ES"}) == "sym=ES"
        assert _kv({"sym": "ES", "fold_id": 3}) == "sym=ES fold_id=3"
        # Insertion order preserved (Python 3.7+ dict semantics).
        assert _kv({"a": 1, "b": 2, "c": 3}) == "a=1 b=2 c=3"

    def test_kv_quotes_whitespace_containing_values(self) -> None:
        """Round-1 audit-remediate Q-1-4: values containing whitespace
        (e.g. ``str(tuple)``) are JSON-encoded so a downstream
        ``key=value`` parser can round-trip them."""
        assert _kv({"x": "no spaces"}) == 'x="no spaces"'
        # Tuples render with internal whitespace.
        assert _kv({"cfg": str((1.5, "vb", 30))}).startswith("cfg=\"(1.5, 'vb', 30)\"")


class TestProgressLogPhaseContextManager:
    """Round-2 — Q-1-1 fix: context manager emits start on enter,
    done on clean exit, and ``failed`` on exception. The exception
    is re-raised so the caller's error handling is unchanged."""

    def test_phase_emits_start_then_done_on_clean_exit(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        log = logging.getLogger("test-progress-cm-1")
        progress = _ProgressLog(log)
        with caplog.at_level(logging.INFO, logger="test-progress-cm-1"):
            with progress.phase("symbol", sym="ES") as ctx:
                ctx["n_folds"] = 4
        records = [r for r in caplog.records if r.name == "test-progress-cm-1"]
        assert len(records) == 2
        assert "PROGRESS symbol start" in records[0].getMessage()
        done_msg = records[1].getMessage()
        assert "PROGRESS symbol done elapsed=" in done_msg
        # Merged ctx: start kwargs (sym=ES) + body-mutated (n_folds=4).
        assert "sym=ES" in done_msg
        assert "n_folds=4" in done_msg

    def test_phase_emits_failed_on_exception_and_reraises(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        log = logging.getLogger("test-progress-cm-2")
        progress = _ProgressLog(log)
        with caplog.at_level(logging.INFO, logger="test-progress-cm-2"):
            with pytest.raises(ValueError, match="boom"):
                with progress.phase("fold-fit", sym="ES", fold_id=2):
                    raise ValueError("boom")
        records = [r for r in caplog.records if r.name == "test-progress-cm-2"]
        assert len(records) == 2
        assert "PROGRESS fold-fit start" in records[0].getMessage()
        failed_msg = records[1].getMessage()
        assert "PROGRESS fold-fit failed" in failed_msg
        assert "exc=ValueError" in failed_msg
        assert "elapsed=" in failed_msg
        # Start kwargs preserved on the failed line.
        assert "sym=ES" in failed_msg
        assert "fold_id=2" in failed_msg

    def test_phase_pops_t0_on_failed_so_no_orphan_leak(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Round-1 Q-1-2: an exception path must not leak the
        ``_t0`` entry; the singleton dict must be self-cleaning."""
        log = logging.getLogger("test-progress-cm-3")
        progress = _ProgressLog(log)
        with caplog.at_level(logging.INFO, logger="test-progress-cm-3"):
            with pytest.raises(RuntimeError):
                with progress.phase("hmm-fit", sym="NQ"):
                    raise RuntimeError
        assert "hmm-fit" not in progress._t0


class TestOrchestratorEmitsExpectedMarkerSequence:
    """Round-1 R-5: integration test asserting the orchestrator's
    smoke-mode dry-run emits the expected sequence of PROGRESS
    markers. Locks both the message shape AND the call-site coverage
    (a future refactor that drops a ``_PROGRESS.start("symbol", ...)``
    would fail this test)."""

    def test_smoke_dry_run_emits_full_marker_sequence(
        self, caplog: pytest.LogCaptureFixture, tmp_path
    ) -> None:
        config_path = (
            Path(__file__).resolve().parents[2]
            / "config"
            / "hypotheses"
            / "H050.yaml"
        )
        with caplog.at_level(logging.INFO):
            _MOD.run(
                [
                    "--hypothesis", "H050",
                    "--config", str(config_path),
                    "--dry-run",
                    "--smoke",
                    "--smoke-n", "2000",
                ]
            )
        msgs = [r.getMessage() for r in caplog.records]
        progress_msgs = [m for m in msgs if m.startswith("PROGRESS ")]
        # At minimum: run, symbol (×N for the universe), label-cfg
        # (≥1 cell), fold-fit (≥1), hmm-fit (≥1), inner-cv-lgb (≥1).
        for marker in (
            "PROGRESS run start",
            "PROGRESS symbol start",
            "PROGRESS label-cfg start",
            "PROGRESS label-cfg-loop-step start",
            "PROGRESS fold-fit start",
            "PROGRESS hmm-fit start",
            "PROGRESS inner-cv-lgb start",
            "PROGRESS run done",
        ):
            assert any(m.startswith(marker) for m in progress_msgs), (
                f"expected marker not emitted: {marker!r}; saw "
                f"{progress_msgs[:20]}"
            )

        # Round-2 audit-remediate Q-2-7: every start must have a
        # matching done OR failed. An orphan start indicates a phase
        # whose body raised mid-execution without try/except cover —
        # exactly the failure mode this patch is meant to make
        # observable.
        n_starts = sum(1 for m in progress_msgs if " start " in m or m.endswith(" start"))
        n_done_or_failed = sum(
            1 for m in progress_msgs if " done elapsed=" in m or " failed elapsed=" in m
        )
        assert n_starts == n_done_or_failed, (
            f"orphan PROGRESS start: {n_starts} starts vs "
            f"{n_done_or_failed} done/failed records. Sample messages: "
            f"{progress_msgs[:30]}"
        )
