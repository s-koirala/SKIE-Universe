"""Pre-commit hook: enforce GuardedRouter-only router access (plan §7).

Scope — ANY Python file under one of::

    src/skie_ninja/
    scripts/
    notebooks/            (python files checked in alongside notebooks)

Inside scope, two violation classes are flagged (AST, no import execution):

(a) Importing any name other than ``GuardedRouter`` from one of the raw
    router modules::

        skie_ninja.execution.router
        skie_ninja.execution.dryrun
        skie_ninja.execution.nt_adapter
        skie_ninja.execution.mcp_adapter

    or binding such a module itself via ``import skie_ninja.execution.<mod>``.

(b) An ``ast.Call`` whose callable resolves by-name to one of
    ``DryRunRouter``, ``NinjaTraderRouter``, ``MCPRouter``, ``OrderRouter``
    and that call is NOT syntactically wrapped in ``GuardedRouter(...)``.
    "Syntactically wrapped" = the violating Call is itself an argument to
    an outer ``Call`` whose func is ``GuardedRouter``.

Exits non-zero with a precise per-violation message.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

RAW_ROUTER_MODULES: frozenset[str] = frozenset(
    {
        "skie_ninja.execution.router",
        "skie_ninja.execution.dryrun",
        "skie_ninja.execution.nt_adapter",
        "skie_ninja.execution.mcp_adapter",
    }
)
ALLOWED_NAME: str = "GuardedRouter"
RAW_ROUTER_CLASSES: frozenset[str] = frozenset(
    {"DryRunRouter", "NinjaTraderRouter", "MCPRouter", "OrderRouter"}
)
SCOPE_PREFIXES: tuple[str, ...] = (
    "src/skie_ninja/",
    "scripts/",
    "notebooks/",
)


def _normalize(p: Path) -> str:
    return p.as_posix()


def _in_scope(path: Path) -> bool:
    s = _normalize(path)
    return any(prefix in s for prefix in SCOPE_PREFIXES)


def _call_func_name(call: ast.Call) -> str | None:
    """Return the simple name of *call.func* if resolvable, else None."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _import_violations(path: Path, tree: ast.AST) -> list[str]:
    errs: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod not in RAW_ROUTER_MODULES:
                continue
            for alias in node.names:
                if alias.name != ALLOWED_NAME:
                    errs.append(
                        f"{path}:{node.lineno}: disallowed import "
                        f"`from {mod} import {alias.name}` "
                        f"(only {ALLOWED_NAME} may be imported from raw "
                        f"router modules)"
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in RAW_ROUTER_MODULES:
                    errs.append(
                        f"{path}:{node.lineno}: disallowed "
                        f"`import {alias.name}` (use "
                        f"`from skie_ninja.execution.router import "
                        f"{ALLOWED_NAME}` instead)"
                    )
    return errs


def _instantiation_violations(path: Path, tree: ast.AST) -> list[str]:
    """Flag raw-router Calls not wrapped in GuardedRouter(...).

    A Call is "wrapped" iff its immediate parent AST node is a Call whose
    func name resolves to ``GuardedRouter``. We walk the tree once to
    record parent Call edges, then emit a diagnostic for each offending
    Call that fails the wrap check.
    """
    parent_of: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_of[id(child)] = parent

    errs: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_func_name(node)
        if name not in RAW_ROUTER_CLASSES:
            continue
        parent = parent_of.get(id(node))
        wrapped = (
            isinstance(parent, ast.Call)
            and _call_func_name(parent) == ALLOWED_NAME
            and node in parent.args
        )
        if wrapped:
            continue
        errs.append(
            f"{path}:{node.lineno}: raw router instantiation `{name}(...)` "
            f"must be wrapped as `{ALLOWED_NAME}({name}(...))`"
        )
    return errs


def check_file(path: Path) -> list[str]:
    try:
        src = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: cannot read ({exc})"]
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        return [f"{path}: syntax error ({exc})"]

    if not _in_scope(path):
        return []
    return _import_violations(path, tree) + _instantiation_violations(path, tree)


def main(argv: list[str]) -> int:
    errors: list[str] = []
    for arg in argv:
        p = Path(arg)
        if p.suffix != ".py" or not p.is_file():
            continue
        errors.extend(check_file(p))
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
