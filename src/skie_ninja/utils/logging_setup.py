"""Structured JSON logging with context propagation.

Required context keys on every record (plan P0-7):
    run_id, phase, hypothesis_id, git_head.

Implemented via `contextvars` so async code and thread pools inherit
the binding. In an interactive TTY we additionally attach a `rich`
handler for readability; machine parsing always reads the JSON
handler's output.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

_CTX_RUN_ID: ContextVar[str] = ContextVar("skie_run_id", default="")
_CTX_PHASE: ContextVar[str] = ContextVar("skie_phase", default="")
_CTX_HYP: ContextVar[str] = ContextVar("skie_hypothesis_id", default="")
_CTX_GIT: ContextVar[str] = ContextVar("skie_git_head", default="")

_REQUIRED_KEYS = ("run_id", "phase", "hypothesis_id", "git_head")


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = _CTX_RUN_ID.get()
        record.phase = _CTX_PHASE.get()
        record.hypothesis_id = _CTX_HYP.get()
        record.git_head = _CTX_GIT.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "run_id": getattr(record, "run_id", ""),
            "phase": getattr(record, "phase", ""),
            "hypothesis_id": getattr(record, "hypothesis_id", ""),
            "git_head": getattr(record, "git_head", ""),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def bind_context(
    *,
    run_id: str | None = None,
    phase: str | None = None,
    hypothesis_id: str | None = None,
    git_head: str | None = None,
) -> None:
    if run_id is not None:
        _CTX_RUN_ID.set(run_id)
    if phase is not None:
        _CTX_PHASE.set(phase)
    if hypothesis_id is not None:
        _CTX_HYP.set(hypothesis_id)
    if git_head is not None:
        _CTX_GIT.set(git_head)


def get_context() -> dict[str, str]:
    return {
        "run_id": _CTX_RUN_ID.get(),
        "phase": _CTX_PHASE.get(),
        "hypothesis_id": _CTX_HYP.get(),
        "git_head": _CTX_GIT.get(),
    }


def setup_logging(level: int = logging.INFO, *, force: bool = False) -> logging.Logger:
    """Configure stdlib logging.

    - Machine stream (stdout) emits one JSON object per line.
    - If stderr is a TTY and `rich` is importable, a pretty handler
      is attached for developer ergonomics. Absence of `rich` or a
      non-TTY context silently skips the pretty handler.
    """
    root = logging.getLogger()
    if force:
        for h in list(root.handlers):
            root.removeHandler(h)

    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        json_handler = logging.StreamHandler(stream=sys.stdout)
        json_handler.setFormatter(JsonFormatter())
        json_handler.addFilter(_ContextFilter())
        root.addHandler(json_handler)

        if sys.stderr.isatty():
            try:
                from rich.logging import RichHandler

                rich_handler = RichHandler(rich_tracebacks=True, show_path=False)
                rich_handler.addFilter(_ContextFilter())
                root.addHandler(rich_handler)
            except ImportError:
                pass

    root.setLevel(level)
    return root


__all__ = [
    "bind_context",
    "get_context",
    "setup_logging",
    "JsonFormatter",
    "_REQUIRED_KEYS",
]
