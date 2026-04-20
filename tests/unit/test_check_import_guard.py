"""Unit tests for scripts/_hooks/check_import_guard.py (plan §7)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "_hooks" / "check_import_guard.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_import_guard", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_import_guard"] = mod
    spec.loader.exec_module(mod)
    return mod


check_import_guard = _load_module()


def _write(tmp_path: Path, relpath: str, src: str) -> Path:
    # Place file under a simulated repo layout so _in_scope matches on
    # the substring "src/skie_ninja/" etc.
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(src, encoding="utf-8")
    return p


OK_SRC = """
from skie_ninja.execution.router import GuardedRouter
from skie_ninja.execution.factory import make_dryrun

def build():
    return GuardedRouter(make_dryrun())
"""

BAD_IMPORT_SRC = """
from skie_ninja.execution.dryrun import DryRunRouter

def build():
    return DryRunRouter()
"""

BAD_DIRECT_CALL_SRC = """
import skie_ninja.execution.dryrun as d

def build():
    # bare call, no GuardedRouter wrap
    return d.NinjaTraderRouter()
"""

BAD_MIXED_SRC = """
from skie_ninja.execution.router import OrderRouter

def build() -> OrderRouter:
    return MCPRouter()
"""


@pytest.fixture()
def ok_file(tmp_path: Path) -> Path:
    return _write(tmp_path, "src/skie_ninja/strategy_a.py", OK_SRC)


@pytest.fixture()
def bad_import_file(tmp_path: Path) -> Path:
    return _write(tmp_path, "src/skie_ninja/bad_import.py", BAD_IMPORT_SRC)


@pytest.fixture()
def bad_direct_instantiation_file(tmp_path: Path) -> Path:
    return _write(tmp_path, "scripts/run_bad.py", BAD_DIRECT_CALL_SRC)


@pytest.fixture()
def bad_mixed_file(tmp_path: Path) -> Path:
    return _write(tmp_path, "notebooks/mixed.py", BAD_MIXED_SRC)


@pytest.fixture()
def out_of_scope_file(tmp_path: Path) -> Path:
    return _write(tmp_path, "tests/unit/irrelevant.py", BAD_IMPORT_SRC)


def test_ok_file_passes(ok_file: Path):
    assert check_import_guard.check_file(ok_file) == []


def test_bad_import_fails(bad_import_file: Path):
    errs = check_import_guard.check_file(bad_import_file)
    assert errs
    assert any("disallowed import" in e and "DryRunRouter" in e for e in errs)
    # Also: the unwrapped DryRunRouter() call is caught.
    assert any("raw router instantiation" in e and "DryRunRouter" in e for e in errs)


def test_bad_direct_instantiation_fails(bad_direct_instantiation_file: Path):
    errs = check_import_guard.check_file(bad_direct_instantiation_file)
    assert errs
    # bare-module import is flagged.
    assert any("disallowed" in e and "skie_ninja.execution.dryrun" in e for e in errs)
    # unwrapped NinjaTraderRouter() is flagged.
    assert any(
        "raw router instantiation" in e and "NinjaTraderRouter" in e for e in errs
    )


def test_bad_mixed_fails(bad_mixed_file: Path):
    errs = check_import_guard.check_file(bad_mixed_file)
    assert errs
    # importing OrderRouter from a raw router module is disallowed.
    assert any("OrderRouter" in e and "disallowed import" in e for e in errs)
    # unwrapped MCPRouter() is flagged.
    assert any("raw router instantiation" in e and "MCPRouter" in e for e in errs)


def test_out_of_scope_ignored(out_of_scope_file: Path):
    assert check_import_guard.check_file(out_of_scope_file) == []


def test_main_returns_nonzero_on_violations(bad_import_file: Path):
    rc = check_import_guard.main([str(bad_import_file)])
    assert rc == 1


def test_main_returns_zero_on_clean(ok_file: Path):
    rc = check_import_guard.main([str(ok_file)])
    assert rc == 0


def test_guarded_wrap_is_not_flagged(tmp_path: Path):
    # Wrapping a raw-router Call is allowed only if the raw class is not
    # itself imported from a raw router module. Here DryRunRouter is
    # produced by a locally defined factory; the Call is wrapped in
    # GuardedRouter(...) so the AST wrap-check exempts it.
    src = """
from skie_ninja.execution.router import GuardedRouter

def DryRunRouter():
    return object()

def f():
    return GuardedRouter(DryRunRouter())
"""
    p = _write(tmp_path, "src/skie_ninja/ok_wrap.py", src)
    assert check_import_guard.check_file(p) == []
