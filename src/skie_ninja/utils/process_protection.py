"""Process-level wake-lock for multi-hour runs (ADR-0010 Layer 1).

Per [ADR-0010](../../../docs/decisions/ADR-0010-multi-hour-run-process-protection.md),
multi-hour walk-forward runs on Windows must register themselves as
system-required workloads via the Win32 ``SetThreadExecutionState``
API so the OS power manager defers idle-driven actions (sleep,
Windows-Update reboot) for the lifetime of the process. The H050
prod-run-2 (2026-04-27) was killed by exactly this failure mode —
see [docs/audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](../../../docs/audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md).

The helper is a no-op on non-Windows hosts; the ``ctypes.windll``
import is guarded by ``sys.platform == "win32"`` so the module
imports cleanly on Linux / macOS.

Round-2 audit-remediate fixes (2026-04-27):

- **Q-1-1**: capture the previous execution state on first acquire and
  restore EXACTLY that state on final release, rather than unconditionally
  setting ``ES_CONTINUOUS``. Composes correctly under nested context
  managers via a refcount: outer acquire stores prev + sets system-required;
  inner acquire bumps refcount only (no syscall); inner release decrements
  refcount only; outer release restores prev.
- **Q-1-2**: drop ``ES_AWAYMODE_REQUIRED``. Per
  [Microsoft Docs](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)
  Remarks: "ES_AWAYMODE_REQUIRED should be used only when absolutely
  necessary by media-recording and media-distribution applications".
  A walk-forward orchestrator is neither. ``ES_SYSTEM_REQUIRED`` alone
  defers Windows-Update reboots; ``ES_AWAYMODE_REQUIRED`` adds Modern
  Standby suppression that can fail on Windows-11 SKUs where Away Mode
  is disabled by default.
"""

from __future__ import annotations

import logging
import sys
import threading
from contextlib import contextmanager
from typing import Iterator

_LOG = logging.getLogger(__name__)

# SetThreadExecutionState flags from winbase.h.
_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002

# Acquire flag set: continuous + system-required only.
# (ES_AWAYMODE_REQUIRED dropped per Q-1-2; ES_DISPLAY_REQUIRED
# intentionally NOT set so the display can sleep during a long run.)
_ACQUIRE_FLAGS = _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED

# Module-level state for refcount + saved prev. A simple Lock guards
# concurrent access; the orchestrator is single-threaded but tests may
# enter from threadpool fixtures.
_lock = threading.Lock()
_refcount: int = 0
_saved_prev: int | None = None


def _is_windows() -> bool:
    return sys.platform == "win32"


def _set_thread_execution_state(flags: int) -> int:
    """Internal: invoke SetThreadExecutionState; return the previous
    state (0 on syscall failure). Exists as a separate function so
    tests can mock it without re-mocking ``ctypes.windll``."""
    if not _is_windows():
        return 0
    import ctypes  # local import: no cost on non-Windows

    return int(ctypes.windll.kernel32.SetThreadExecutionState(flags))  # type: ignore[attr-defined]


def acquire_system_required_wakelock() -> bool:
    """Register the calling process as system-required on Windows so
    the OS does not idle-reboot, sleep, or hibernate while the
    process is running. Returns True on Windows when the syscall
    succeeded OR a wake-lock is already held by an outer caller; False
    on non-Windows hosts or if the syscall failed.

    Refcount semantics (Q-1-1 fix): nested acquire calls in the same
    process bump a refcount and do not re-issue the syscall. The
    previous state is captured on first acquire and restored on the
    matching final release.
    """
    global _refcount, _saved_prev
    if not _is_windows():
        _LOG.info("wakelock skipped: non-Windows platform (%s)", sys.platform)
        return False
    with _lock:
        if _refcount > 0:
            _refcount += 1
            _LOG.info("wakelock refcount bump (level=%d; no syscall)", _refcount)
            return True
        try:
            prev = _set_thread_execution_state(_ACQUIRE_FLAGS)
            if prev == 0:
                _LOG.warning("SetThreadExecutionState returned 0 (failure)")
                return False
            _saved_prev = prev
            _refcount = 1
            _LOG.info(
                "wakelock acquired: ES_CONTINUOUS|ES_SYSTEM_REQUIRED "
                "(flags=0x%08X, prev=0x%08X, refcount=%d)",
                _ACQUIRE_FLAGS,
                prev,
                _refcount,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("wakelock acquisition failed: %r", exc)
            return False


def release_system_required_wakelock() -> bool:
    """Decrement the wake-lock refcount. On the final release, restore
    the previous execution state captured at first acquire (Q-1-1 fix).
    Returns True on Windows when the refcount-decrement-or-syscall
    succeeded; False on non-Windows hosts, if no lock was held, or if
    the syscall failed.
    """
    global _refcount, _saved_prev
    if not _is_windows():
        return False
    with _lock:
        if _refcount == 0:
            _LOG.warning("wakelock release called with refcount=0; no-op")
            return False
        if _refcount > 1:
            _refcount -= 1
            _LOG.info("wakelock refcount decrement (level=%d; no syscall)", _refcount)
            return True
        # Final release: restore prev exactly.
        prev_to_restore = _saved_prev if _saved_prev is not None else _ES_CONTINUOUS
        try:
            result = _set_thread_execution_state(prev_to_restore)
            if result == 0:
                _LOG.warning("SetThreadExecutionState release returned 0 (failure)")
                _refcount = 0
                _saved_prev = None
                return False
            _LOG.info(
                "wakelock released: restored prev=0x%08X (refcount now 0)",
                prev_to_restore,
            )
            _refcount = 0
            _saved_prev = None
            return True
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("wakelock release failed: %r", exc)
            _refcount = 0
            _saved_prev = None
            return False


@contextmanager
def system_required_wakelock() -> Iterator[bool]:
    """Context-managed wake-lock: acquires on enter, releases on
    exit (whether by clean exit or exception). Composes correctly
    under nesting via the helper's refcount. Yields the boolean
    result of the acquisition syscall so callers can branch on
    whether protection is in effect.

    Per ADR-0010 the orchestrator's ``__main__`` block is the
    canonical use site.
    """
    acquired = acquire_system_required_wakelock()
    try:
        yield acquired
    finally:
        if acquired:
            release_system_required_wakelock()


def _reset_state_for_test() -> None:
    """Test-only helper: forcibly clear the refcount + saved prev so
    a fresh test starts from a known state. Not for production use."""
    global _refcount, _saved_prev
    with _lock:
        _refcount = 0
        _saved_prev = None


__all__ = [
    "acquire_system_required_wakelock",
    "release_system_required_wakelock",
    "system_required_wakelock",
]
