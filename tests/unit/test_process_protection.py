"""Regression tests for ADR-0010 Layer 1 — process-level wake-lock.

The wake-lock helper at [src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py)
wraps Win32 ``SetThreadExecutionState``. Tests mock the syscall via
the helper's internal ``_set_thread_execution_state`` shim so the
suite passes on both Windows and non-Windows hosts. The actual
syscall behaviour is exercised in the H050 prod-run-3 launch
(verified separately by ``powercfg /requests``).

Round-2 audit-remediate fixes covered here:

- Q-1-1: refcount + restore-prev semantics (nested context managers
  compose; first acquire stores prev; final release restores it).
- Q-1-2: ``ES_AWAYMODE_REQUIRED`` removed; flag is now
  ``ES_CONTINUOUS | ES_SYSTEM_REQUIRED`` = 0x80000001.
"""
from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

import skie_ninja.utils.process_protection as pp
from skie_ninja.utils.process_protection import (
    acquire_system_required_wakelock,
    release_system_required_wakelock,
    system_required_wakelock,
)


_ACQUIRE_FLAGS = 0x80000001  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED (Q-1-2)


@pytest.fixture(autouse=True)
def _reset_wakelock_state() -> None:
    """Each test starts with a clean refcount + saved_prev."""
    pp._reset_state_for_test()
    yield
    pp._reset_state_for_test()


class TestNonWindowsBehavior:
    """On non-Windows the helper must be a clean no-op (no syscall,
    no exception)."""

    def test_acquire_returns_false_on_non_windows(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=False):
            with caplog.at_level(logging.INFO):
                result = acquire_system_required_wakelock()
        assert result is False
        assert any("non-Windows platform" in r.getMessage() for r in caplog.records)

    def test_release_returns_false_on_non_windows(self) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=False):
            assert release_system_required_wakelock() is False

    def test_context_manager_yields_false_on_non_windows(self) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=False):
            with system_required_wakelock() as acquired:
                assert acquired is False


class TestWindowsBehavior:
    """Mock the SetThreadExecutionState shim to verify the flag set
    + the acquire/release sequence."""

    def test_acquire_calls_setthreadexecutionstate_with_correct_flags(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Returns the prev state (canonical Windows initial state).
        fake_prev = 0x80000000
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=fake_prev,
            ) as mock_stes:
                with caplog.at_level(logging.INFO):
                    result = acquire_system_required_wakelock()
        assert result is True
        # Q-1-2: flag is ES_CONTINUOUS | ES_SYSTEM_REQUIRED, NOT
        # including ES_AWAYMODE_REQUIRED.
        mock_stes.assert_called_once_with(_ACQUIRE_FLAGS)
        # Q-1-1: prev should have been captured.
        assert pp._saved_prev == fake_prev
        assert pp._refcount == 1
        assert any("wakelock acquired" in r.getMessage() for r in caplog.records)

    def test_release_restores_exact_prev_state(self) -> None:
        fake_prev = 0x80000020  # arbitrary non-trivial prev
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=fake_prev,
            ) as mock_stes:
                acquire_system_required_wakelock()
                release_system_required_wakelock()
        # Two calls: acquire (with ACQUIRE_FLAGS), release (with prev).
        assert mock_stes.call_count == 2
        assert mock_stes.call_args_list[0][0][0] == _ACQUIRE_FLAGS
        # Q-1-1: release restores the EXACT prev, not ES_CONTINUOUS only.
        assert mock_stes.call_args_list[1][0][0] == fake_prev
        assert pp._refcount == 0
        assert pp._saved_prev is None

    def test_acquire_returns_false_when_syscall_returns_zero(self) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=0,
            ):
                assert acquire_system_required_wakelock() is False
        # No state mutation on failure.
        assert pp._refcount == 0
        assert pp._saved_prev is None

    def test_acquire_returns_false_on_exception(self) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                side_effect=OSError("boom"),
            ):
                assert acquire_system_required_wakelock() is False

    def test_context_manager_releases_on_clean_exit(self) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=0x80000000,
            ) as mock_stes:
                with system_required_wakelock() as acquired:
                    assert acquired is True
        assert mock_stes.call_count == 2

    def test_context_manager_releases_on_exception(self) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=0x80000000,
            ) as mock_stes:
                with pytest.raises(RuntimeError, match="body raised"):
                    with system_required_wakelock():
                        raise RuntimeError("body raised")
        assert mock_stes.call_count == 2

    def test_context_manager_does_not_release_when_acquire_failed(self) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=0,
            ) as mock_stes:
                with system_required_wakelock() as acquired:
                    assert acquired is False
        assert mock_stes.call_count == 1

    def test_release_with_no_lock_held_is_noop_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=0x80000000,
            ) as mock_stes:
                with caplog.at_level(logging.WARNING):
                    result = release_system_required_wakelock()
        assert result is False
        assert mock_stes.call_count == 0
        assert any("refcount=0" in r.getMessage() for r in caplog.records)


class TestNestedComposition:
    """Q-1-1 fix: nested context managers compose correctly via
    refcount; only the outer-most release issues a syscall."""

    def test_nested_acquire_release_calls_syscall_twice_only(self) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=0x80000000,
            ) as mock_stes:
                with system_required_wakelock():
                    assert pp._refcount == 1
                    with system_required_wakelock():
                        assert pp._refcount == 2
                    assert pp._refcount == 1
                assert pp._refcount == 0
        # 2 syscalls: outer acquire + outer release. Inner acquire/release
        # are refcount-only.
        assert mock_stes.call_count == 2

    def test_nested_acquire_release_logs_refcount(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch("skie_ninja.utils.process_protection._is_windows", return_value=True):
            with patch(
                "skie_ninja.utils.process_protection._set_thread_execution_state",
                return_value=0x80000000,
            ):
                with caplog.at_level(logging.INFO):
                    with system_required_wakelock():
                        with system_required_wakelock():
                            with system_required_wakelock():
                                pass
        msgs = [r.getMessage() for r in caplog.records]
        assert any("refcount bump (level=2" in m for m in msgs)
        assert any("refcount bump (level=3" in m for m in msgs)
        assert any("refcount decrement (level=2" in m for m in msgs)
        assert any("refcount decrement (level=1" in m for m in msgs)


class TestFlagSetIsCorrect:
    """Q-1-2: explicit assertion that ES_AWAYMODE_REQUIRED is NOT set."""

    def test_acquire_flag_does_not_include_awaymode(self) -> None:
        ES_AWAYMODE_REQUIRED = 0x00000040
        assert (_ACQUIRE_FLAGS & ES_AWAYMODE_REQUIRED) == 0
        # Also confirm pp module agrees.
        assert (pp._ACQUIRE_FLAGS & ES_AWAYMODE_REQUIRED) == 0

    def test_acquire_flag_does_not_include_display_required(self) -> None:
        # Intentionally not set: display can sleep during a long run.
        ES_DISPLAY_REQUIRED = 0x00000002
        assert (_ACQUIRE_FLAGS & ES_DISPLAY_REQUIRED) == 0

    def test_acquire_flag_includes_continuous_and_system_required(self) -> None:
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        assert (_ACQUIRE_FLAGS & ES_CONTINUOUS) == ES_CONTINUOUS
        assert (_ACQUIRE_FLAGS & ES_SYSTEM_REQUIRED) == ES_SYSTEM_REQUIRED
