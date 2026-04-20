"""P0-7 acceptance: structured JSON logs with required context keys."""

from __future__ import annotations

import io
import json
import logging

from skie_ninja.utils.logging_setup import (
    JsonFormatter,
    _ContextFilter,
    bind_context,
    get_context,
    setup_logging,
)


def _capture(level: int = logging.INFO) -> tuple[logging.Logger, io.StringIO]:
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(_ContextFilter())
    log = logging.getLogger("skie.test")
    log.handlers.clear()
    log.addHandler(handler)
    log.setLevel(level)
    log.propagate = False
    return log, buf


def test_every_record_is_json_with_required_keys() -> None:
    bind_context(run_id="r1", phase="p0", hypothesis_id="H1", git_head="deadbeef")
    log, buf = _capture()
    log.info("hello")
    log.warning("world")
    for line in buf.getvalue().splitlines():
        rec = json.loads(line)
        for k in ("run_id", "phase", "hypothesis_id", "git_head"):
            assert k in rec
        assert rec["run_id"] == "r1"
        assert rec["git_head"] == "deadbeef"


def test_context_defaults_to_empty_strings() -> None:
    bind_context(run_id="", phase="", hypothesis_id="", git_head="")
    ctx = get_context()
    assert all(v == "" for v in ctx.values())


def test_setup_logging_idempotent() -> None:
    root = setup_logging(force=True)
    n = len(root.handlers)
    setup_logging()
    assert len(root.handlers) == n


def test_exception_info_serialized() -> None:
    log, buf = _capture()
    try:
        raise ValueError("boom")
    except ValueError:
        log.exception("failed")
    rec = json.loads(buf.getvalue().strip())
    assert "exc" in rec
    assert "ValueError" in rec["exc"]
