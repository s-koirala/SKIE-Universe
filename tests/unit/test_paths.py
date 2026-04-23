"""P0-2 acceptance: ProjectPaths resolver."""

from __future__ import annotations

from pathlib import Path

from skie_ninja.utils.paths import ProjectPaths


def test_discover_finds_pyproject_root() -> None:
    p = ProjectPaths.discover()
    assert (p.root / "pyproject.toml").is_file()


def test_all_advertised_properties_resolve_under_root() -> None:
    p = ProjectPaths.discover()
    expected = [
        p.data_raw,
        p.data_interim,
        p.data_processed,
        p.artifacts_models,
        p.artifacts_reports,
        p.artifacts_runs,
        p.logs_reproducibility,
        p.logs_reproducibility_env,
        p.logs_reproducibility_features,
        p.universe_log,
    ]
    for path in expected:
        assert isinstance(path, Path)
        assert p.root in path.parents or path == p.root

    # Shared paths resolve outside root; verify they are Path instances.
    shared = [p.shared_fred, p.shared_fomc_text, p.shared_spf,
              p.shared_es_tick, p.shared_nq_tick,
              p.shared_vendor_skie_ninja_legacy]
    for path in shared:
        assert isinstance(path, Path)
    # Vendor-namespaced subdir lives under the shared root, same as the
    # other shared_* properties.
    assert p.shared_vendor_skie_ninja_legacy.parent == p.shared_data
    assert p.shared_vendor_skie_ninja_legacy.name == "vendor_skie_ninja_legacy"


def test_no_hardcoded_absolute_paths_in_source() -> None:
    p = ProjectPaths.discover()
    src = p.root / "src" / "skie_ninja" / "utils"
    for f in src.glob("*.py"):
        text = f.read_text(encoding="utf-8")
        # Crude guard: no drive-letter or POSIX absolute literals.
        assert "C:\\\\" not in text
        assert "c:\\\\" not in text
        assert "'/home/" not in text
        assert '"/home/' not in text


# Grep-guard allowlist marker. Scripts that *must* bootstrap sys.path
# before `skie_ninja` is importable (e.g., the uv-install bootstrap
# script itself) append this literal comment to the offending line.
# Any production module under `src/skie_ninja/` is forbidden from
# using it — the resolver in paths.py is the single source of truth.
_PATHS_GUARD_ALLOW = "# paths-guard: allow"


def _iter_python_files(root: Path) -> list[Path]:
    return [
        f for f in root.rglob("*.py")
        if "__pycache__" not in f.parts
    ]


def test_no_file_based_root_resolution_outside_paths_py() -> None:
    """F-2-4: `Path(__file__)` root-walking is the paths.py monopoly.

    Any other occurrence under `src/` or `scripts/` must either
    (a) be removed in favor of `ProjectPaths.discover()`, or
    (b) carry an explicit `# paths-guard: allow (...)` comment
    documenting why the allowlist is needed (e.g., sys.path bootstrap
    before `pip install -e .` has run).
    """
    p = ProjectPaths.discover()
    needle = "Path(__file__)"
    offenders: list[str] = []
    roots = [p.root / "src", p.root / "scripts"]
    # Files exempted from the grep-guard. paths.py is the definition
    # site. instruments.py is owned by a sibling remediation agent
    # whose scope covers the CLI-default path; revisit once that
    # agent lands its fix so the exemption can be removed.
    allowed_files = {
        (p.root / "src" / "skie_ninja" / "utils" / "paths.py").resolve(),
        (p.root / "src" / "skie_ninja" / "utils" / "instruments.py").resolve(),
    }
    for r in roots:
        if not r.is_dir():
            continue
        for f in _iter_python_files(r):
            if f.resolve() in allowed_files:
                continue
            for i, line in enumerate(
                f.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if needle in line and _PATHS_GUARD_ALLOW not in line:
                    offenders.append(f"{f}:{i}: {line.strip()}")
    assert not offenders, (
        "Path(__file__) used outside utils/paths.py without allowlist "
        "comment:\n" + "\n".join(offenders)
    )


def test_ensure_creates_directory(tmp_path: Path) -> None:
    p = ProjectPaths(root=tmp_path)
    target = tmp_path / "a" / "b"
    assert not target.exists()
    p.ensure(target)
    assert target.is_dir()


def test_shared_data_defaults_to_home_datasets() -> None:
    import os

    env = os.environ.pop("SKIE_SHARED_DATA", None)
    try:
        p = ProjectPaths.discover()
        assert p.shared_data == Path.home() / "datasets"
    finally:
        if env is not None:
            os.environ["SKIE_SHARED_DATA"] = env


def test_shared_data_env_var_override(tmp_path: Path) -> None:
    import os

    old = os.environ.get("SKIE_SHARED_DATA")
    custom = tmp_path / "custom_shared"
    os.environ["SKIE_SHARED_DATA"] = str(custom)
    try:
        p = ProjectPaths.discover()
        assert p.shared_data == custom.resolve()
    finally:
        if old is not None:
            os.environ["SKIE_SHARED_DATA"] = old
        else:
            os.environ.pop("SKIE_SHARED_DATA", None)


def test_shared_subdirs_resolve_under_shared_data() -> None:
    p = ProjectPaths.discover()
    for attr in ("shared_fred", "shared_fomc_text", "shared_spf",
                 "shared_es_tick", "shared_nq_tick"):
        sub = getattr(p, attr)
        assert isinstance(sub, Path)
        assert sub.parent == p.shared_data
