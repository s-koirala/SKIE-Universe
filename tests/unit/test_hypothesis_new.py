"""P0-11 acceptance: scripts/hypothesis_new.py."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

import hypothesis_new  # noqa: E402

# Exit codes mirrored from hypothesis_new.main; named here to satisfy PLR2004.
_EXIT_OK = 0
_EXIT_VALIDATION = 2
_EXIT_DUPLICATE = 3


def _scaffold(tmp_path: Path) -> Path:
    """Copy the minimal fixture files the script expects into a tmp project root."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='tmp'\n", encoding="utf-8")
    for sub in (
        "docs/templates",
        "research/01_hypothesis_register",
        "plan",
    ):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    src_templates = _PROJECT_ROOT / "docs" / "templates"
    for fname in (
        "hypothesis_design.md",
        "hypothesis_config.yaml",
        "hypothesis_data_requirements.md",
    ):
        shutil.copy(src_templates / fname, tmp_path / "docs" / "templates" / fname)
    (tmp_path / "plan" / "hypothesis_backlog.md").write_text(
        "# Hypothesis Backlog\n", encoding="utf-8"
    )
    return tmp_path


def _run(tmp_path: Path, *extra: str, hid: str = "H999") -> int:
    argv = [
        hid,
        "--title",
        "Test hypothesis",
        "--tier",
        "1",
        "--citations",
        "doi:10.1000/xyz123,https://arxiv.org/abs/2511.00751",
        "--root",
        str(tmp_path),
        "--date",
        "2026-04-15",
        *extra,
    ]
    return hypothesis_new.main(argv)


def test_creates_all_four_files_and_backlog(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    rc = _run(tmp_path)
    assert rc == _EXIT_OK
    base = tmp_path / "research" / "01_hypothesis_register" / "H999"
    for fname in ("design.md", "config.yaml", "data_requirements.md", "README.md"):
        assert (base / fname).is_file(), fname
    backlog_text = (tmp_path / "hypothesis_backlog.md").read_text(
        encoding="utf-8"
    )
    assert "H999" in backlog_text
    assert "queued" in backlog_text


def test_backlog_append_is_idempotent(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    rc1 = _run(tmp_path)
    assert rc1 == _EXIT_OK
    # Second call must fail because the hypothesis directory already exists
    # (pre-registration immutability), and must NOT duplicate the backlog row.
    rc2 = _run(tmp_path)
    assert rc2 == _EXIT_DUPLICATE
    backlog_text = (tmp_path / "hypothesis_backlog.md").read_text(
        encoding="utf-8"
    )
    assert backlog_text.count("| H999 |") == 1

    # Direct idempotent append: call append twice without dir collision.
    spec = hypothesis_new.HypothesisSpec(
        hid="H998",
        title="t",
        tier=1,
        citations=("doi:10.1/x",),
        date="2026-04-15",
    )
    backlog = tmp_path / "hypothesis_backlog.md"
    assert hypothesis_new._append_backlog(backlog, spec) is True
    assert hypothesis_new._append_backlog(backlog, spec) is False
    assert backlog.read_text(encoding="utf-8").count("| H998 |") == 1


def test_rejects_duplicate_id(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    assert _run(tmp_path) == _EXIT_OK
    assert _run(tmp_path) == _EXIT_DUPLICATE


def test_rejects_invalid_tier(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    with pytest.raises(SystemExit):  # argparse choices error
        hypothesis_new.main(
            [
                "H999",
                "--title",
                "t",
                "--tier",
                "4",
                "--citations",
                "doi:10.1/x",
                "--root",
                str(tmp_path),
            ]
        )


def test_rejects_malformed_citation(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    rc = hypothesis_new.main(
        [
            "H999",
            "--title",
            "t",
            "--tier",
            "1",
            "--citations",
            "not-a-doi-or-url",
            "--root",
            str(tmp_path),
        ]
    )
    assert rc == _EXIT_VALIDATION


def test_rejects_malformed_hid(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    rc = hypothesis_new.main(
        [
            "H27",  # two digits, violates HID_PAD_WIDTH = 3
            "--title",
            "t",
            "--tier",
            "1",
            "--citations",
            "doi:10.1/x",
            "--root",
            str(tmp_path),
        ]
    )
    assert rc == _EXIT_VALIDATION
