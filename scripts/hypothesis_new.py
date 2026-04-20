"""Create a new hypothesis folder under research/01_hypothesis_register/.

Usage:
    python scripts/hypothesis_new.py H027 \
        --title "CBOE COR regime gate" \
        --tier 3 \
        --citations doi:10.xxxx/yyyy,https://arxiv.org/abs/2604.01431

Spec: plan/implementation-plan_2026-04-15.md §10 (item P0-11).
- Copies docs/templates/{hypothesis_design.md, hypothesis_config.yaml,
  hypothesis_data_requirements.md} into research/01_hypothesis_register/{HID}/ and
  generates a README.md.
- Appends a `queued`-status row to plan/hypothesis_backlog.md (idempotent).
- Rejects existing IDs; validates tier in {1, 2, 3}; validates every citation parses as
  a DOI or URL.

No magic numbers: the only constants are
    HID_PAD_WIDTH = 3   # 3-digit zero-pad (H001..H999); plan §10 convention.
    VALID_TIERS   = {1, 2, 3}  # plan §10 tier taxonomy.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Script-bootstrap sys.path shim: script may be invoked before
# `uv pip install -e .` has been run, in which case `skie_ninja` is
# not yet importable. Insert `src/` ahead of site-packages with one
# explicit allowlist-marked line, keeping paths.py's grep-guard
# invariant intact for all other code.
_SCRIPT_DIR = Path(__file__).resolve().parent  # paths-guard: allow (script bootstrap)
sys.path.insert(0, str(_SCRIPT_DIR.parent / "src"))

from skie_ninja.utils.paths import ProjectPaths  # noqa: E402

# Constants. Both are explicitly documented conventions, not tunables.
HID_PAD_WIDTH = 3          # 3-digit zero-pad for hypothesis IDs (plan §10).
VALID_TIERS = frozenset({1, 2, 3})   # plan §10 tier taxonomy.

# Regexes used for citation validation. DOIs follow the CrossRef pattern
# `10.\d{4,9}/...`; URLs require a scheme of http or https. Both are standard
# and carry no tunable thresholds.
_DOI_PATTERN = re.compile(r"^doi:10\.\d{4,9}/\S+$", re.IGNORECASE)
_URL_PATTERN = re.compile(r"^https?://\S+$", re.IGNORECASE)

_BACKLOG_APPEND_MARKER = "<!-- hypothesis_new.py appended -->"


@dataclass(frozen=True)
class HypothesisSpec:
    hid: str
    title: str
    tier: int
    citations: tuple[str, ...]
    date: str


def _project_root(start: Path | None = None) -> Path:
    """Delegate to ProjectPaths so root discovery is single-sourced."""
    origin = start if start is not None else _SCRIPT_DIR
    return ProjectPaths.discover(origin).root


def _validate_hid(hid: str) -> str:
    if not re.fullmatch(rf"H\d{{{HID_PAD_WIDTH}}}", hid):
        raise ValueError(
            f"Hypothesis ID must match 'H' followed by {HID_PAD_WIDTH} digits "
            f"(e.g., H027); got {hid!r}."
        )
    return hid


def _validate_tier(tier: int) -> int:
    if tier not in VALID_TIERS:
        raise ValueError(f"Tier must be one of {sorted(VALID_TIERS)}; got {tier}.")
    return tier


def _validate_citation(c: str) -> str:
    c = c.strip()
    if not c:
        raise ValueError("Empty citation.")
    if _DOI_PATTERN.match(c) or _URL_PATTERN.match(c):
        return c
    raise ValueError(
        f"Citation {c!r} is neither a DOI (doi:10.xxxx/yyyy) nor an http(s) URL."
    )


def _parse_citations(raw: str) -> tuple[str, ...]:
    if not raw:
        return ()
    items = [_validate_citation(x) for x in raw.split(",") if x.strip()]
    return tuple(items)


def _render_template(text: str, spec: HypothesisSpec) -> str:
    cites_inline = ", ".join(spec.citations) if spec.citations else ""
    return (
        text.replace("{HID}", spec.hid)
        .replace("{TITLE}", spec.title)
        .replace("{TIER}", str(spec.tier))
        .replace("{DATE}", spec.date)
        .replace("{CITATIONS}", cites_inline)
    )


def _write_if_absent(path: Path, content: str) -> bool:
    """Write content to path unless path exists. Returns True iff written."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _append_backlog(backlog: Path, spec: HypothesisSpec) -> bool:
    """Append a queued entry for this hypothesis. Idempotent on repeated invocation."""
    marker = f"{_BACKLOG_APPEND_MARKER} {spec.hid}"
    existing = backlog.read_text(encoding="utf-8") if backlog.exists() else ""
    if marker in existing:
        return False
    cites_md = ", ".join(spec.citations) if spec.citations else "—"
    line = (
        f"\n{marker}\n"
        f"| {spec.hid} | {spec.title} | {cites_md} | queued |\n"
    )
    with backlog.open("a", encoding="utf-8") as f:
        f.write(line)
    return True


def create_hypothesis(
    spec: HypothesisSpec,
    root: Path,
) -> dict[str, Path]:
    """Materialize hypothesis files under root. Returns dict of produced paths.

    Rejects existing hypothesis directory (to preserve pre-registration immutability).
    Backlog append is idempotent.
    """
    templates_dir = root / "docs" / "templates"
    design_tpl = (templates_dir / "hypothesis_design.md").read_text(encoding="utf-8")
    config_tpl = (templates_dir / "hypothesis_config.yaml").read_text(encoding="utf-8")
    data_tpl = (
        templates_dir / "hypothesis_data_requirements.md"
    ).read_text(encoding="utf-8")

    hypo_dir = root / "research" / "01_hypothesis_register" / spec.hid
    if hypo_dir.exists():
        raise FileExistsError(
            f"Hypothesis directory already exists: {hypo_dir}. "
            "Pre-registered hypotheses are immutable; pick a new ID."
        )

    design_path = hypo_dir / "design.md"
    config_path = hypo_dir / "config.yaml"
    data_path = hypo_dir / "data_requirements.md"
    readme_path = hypo_dir / "README.md"

    _write_if_absent(design_path, _render_template(design_tpl, spec))
    _write_if_absent(config_path, _render_template(config_tpl, spec))
    _write_if_absent(data_path, _render_template(data_tpl, spec))

    readme = (
        f"# {spec.hid} — {spec.title}\n\n"
        f"Tier {spec.tier}. Created {spec.date}. Status: queued.\n\n"
        f"- Design: [design.md](design.md)\n"
        f"- Config: [config.yaml](config.yaml)\n"
        f"- Data requirements: [data_requirements.md](data_requirements.md)\n\n"
        f"Primary citations: "
        f"{', '.join(spec.citations) if spec.citations else '(none)'}\n"
    )
    _write_if_absent(readme_path, readme)

    backlog = root / "plan" / "hypothesis_backlog.md"
    _append_backlog(backlog, spec)

    return {
        "design": design_path,
        "config": config_path,
        "data_requirements": data_path,
        "readme": readme_path,
        "backlog": backlog,
    }


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hypothesis_new.py",
        description=(
            "Create a new hypothesis folder and append a queued row to the backlog. "
            "See plan/implementation-plan_2026-04-15.md §10."
        ),
    )
    p.add_argument("hid", type=str, help="Hypothesis ID, e.g., H027.")
    p.add_argument("--title", required=True, type=str, help="Short descriptive title.")
    p.add_argument(
        "--tier",
        required=True,
        type=int,
        choices=sorted(VALID_TIERS),
        help="Tier classification (1 directional | 2 microstructure | 3 frontier).",
    )
    p.add_argument(
        "--citations",
        default="",
        type=str,
        help=(
            "Comma-separated citations; each must be a DOI (doi:10.xxxx/yyyy) or "
            "http(s) URL."
        ),
    )
    p.add_argument(
        "--root",
        default=None,
        type=Path,
        help="Project root override (default: discovered from pyproject.toml).",
    )
    p.add_argument(
        "--date",
        default=None,
        type=str,
        help="ISO date override (default: today UTC).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        hid = _validate_hid(args.hid)
        tier = _validate_tier(args.tier)
        citations = _parse_citations(args.citations)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    root = args.root.resolve() if args.root else _project_root()
    date = args.date or _dt.datetime.now(_dt.UTC).date().isoformat()
    spec = HypothesisSpec(
        hid=hid, title=args.title, tier=tier, citations=citations, date=date
    )

    try:
        paths = create_hypothesis(spec, root)
    except FileExistsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3

    print(f"created {spec.hid} at {paths['design'].parent}")
    print(f"backlog updated: {paths['backlog']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
