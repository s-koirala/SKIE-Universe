"""Regenerate BEST_OOS.md from the per-hypothesis KPI report card data.

Per ADR-0024 D-8 (2026-05-15), every push regenerates BEST_OOS.md to
showcase the strongest realized-OOS performer across emitted KPI report
cards. Mechanism is the pre-push hook at .githooks/pre-push.

Source of truth: research/01_hypothesis_register/_oos_showcase_data.yaml.
The YAML is the machine-readable cache of the per-card markdown bodies
(which are themselves frozen at emission per ADR-0013 §4.1 non-loss).

Ranking primary: realized OOS end-equity-percent on the strongest cell.
Ranking primary will cut over to MPPM(ρ=1) per ADR-0018 D-1 once that
fitness is uniformly reported across all hypotheses, tracked under
P1-BEST-OOS-MPPM-RANKING-CUTOVER.

Invocation:
    uv run python scripts/showcase_best_oos.py

The script is idempotent: it overwrites BEST_OOS.md unconditionally.
It does NOT modify the underlying _oos_showcase_data.yaml or any KPI
report card. Exit code 0 on success, 1 on parse error.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "PyYAML is required. Run `uv pip install pyyaml` or ensure it is "
        "in the project's [dev] extras.\n"
    )
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent  # paths-guard: allow (script-bootstrap; deterministic anchor for the showcase generator invoked from `uv run python` or the pre-push hook)
DATA_PATH = REPO_ROOT / "research" / "01_hypothesis_register" / "_oos_showcase_data.yaml"
OUTPUT_PATH = REPO_ROOT / "BEST_OOS.md"

_VALID_PARADIGMS = frozenset({
    "adr-0017-survival",
    "adr-0024-aggressive-growth",
    "hybrid",
})


@dataclass(frozen=True)
class Card:
    """One emitted KPI report card row from the YAML data file.

    Fields mirror the YAML schema documented in _oos_showcase_data.yaml.
    See ADR-0024 D-8 for the schema-as-source-of-truth contract.
    """

    hypothesis_id: str
    version: int
    date: str
    report_card_path: str
    run_id: str | None
    paradigm: str
    hypothesis_of_record_arm: str
    strongest_cell: str
    strongest_cell_pct: float | None
    strongest_cell_max_dd_pct: float | None
    hypothesis_of_record_arm_pct: float | None
    oos_sessions: int | None
    p_loss_pct: float | None
    mppm_rho1_point: float | None
    mppm_rho1_ci_low: float | None
    mppm_rho1_ci_high: float | None
    sharpe_ann_strongest_cell: float | None
    primary_annotations: list[str]
    cost_model: str | None
    superseded_by: str | None


def _load_cards(path: Path) -> list[Card]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "cards" not in raw:
        raise ValueError(
            f"{path} must be a YAML mapping with a top-level `cards` list"
        )
    cards: list[Card] = []
    for i, entry in enumerate(raw["cards"]):
        if not isinstance(entry, dict):
            raise ValueError(f"{path} entry {i} is not a mapping")
        try:
            cards.append(
                Card(
                    hypothesis_id=str(entry["hypothesis_id"]),
                    version=int(entry["version"]),
                    date=str(entry["date"]),
                    report_card_path=str(entry["report_card_path"]),
                    run_id=entry.get("run_id"),
                    paradigm=str(entry["paradigm"]),
                    hypothesis_of_record_arm=str(entry["hypothesis_of_record_arm"]),
                    strongest_cell=str(entry["strongest_cell"]),
                    strongest_cell_pct=_maybe_float(
                        entry.get("realized", {}).get("strongest_cell_pct")
                    ),
                    strongest_cell_max_dd_pct=_maybe_float(
                        entry.get("realized", {}).get("strongest_cell_max_dd_pct")
                    ),
                    hypothesis_of_record_arm_pct=_maybe_float(
                        entry.get("realized", {}).get("hypothesis_of_record_arm_pct")
                    ),
                    oos_sessions=_maybe_int(
                        entry.get("realized", {}).get("oos_sessions")
                    ),
                    p_loss_pct=_maybe_float(
                        entry.get("forward_projection", {}).get("p_loss_pct")
                    ),
                    mppm_rho1_point=_maybe_float(
                        entry.get("fitness", {}).get("mppm_rho1_point")
                    ),
                    mppm_rho1_ci_low=_maybe_float(
                        entry.get("fitness", {}).get("mppm_rho1_ci_low")
                    ),
                    mppm_rho1_ci_high=_maybe_float(
                        entry.get("fitness", {}).get("mppm_rho1_ci_high")
                    ),
                    sharpe_ann_strongest_cell=_maybe_float(
                        entry.get("fitness", {}).get("sharpe_ann_strongest_cell")
                    ),
                    primary_annotations=list(entry.get("primary_annotations", [])),
                    cost_model=entry.get("cost_model"),
                    superseded_by=entry.get("superseded_by"),
                )
            )
        except KeyError as exc:
            raise ValueError(
                f"{path} entry {i} missing required key {exc.args[0]}"
            ) from exc
    for c in cards:
        if c.paradigm not in _VALID_PARADIGMS:
            raise ValueError(
                f"{path}: card {c.hypothesis_id} v{c.version} has paradigm "
                f"{c.paradigm!r}; expected one of {sorted(_VALID_PARADIGMS)}"
            )
    return cards


def _maybe_float(v: Any) -> float | None:
    if v is None:
        return None
    return float(v)


def _maybe_int(v: Any) -> int | None:
    if v is None:
        return None
    return int(v)


def _fmt_pct(v: float | None) -> str:
    if v is None:
        return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.2f}%"


def _fmt_float(v: float | None, prec: int = 4) -> str:
    if v is None:
        return "—"
    return f"{v:+.{prec}f}"


def _fmt_int(v: int | None) -> str:
    if v is None:
        return "—"
    return f"{v:,}"


def _live_cards(cards: list[Card]) -> list[Card]:
    """Drop superseded cards from the ranking, preserve in history."""
    return [c for c in cards if c.superseded_by is None]


def _rank_key(c: Card) -> tuple[float, str, int]:
    """Ranking primary: realized OOS strongest-cell pct.

    Returned tuple is consumed by sorted(..., key=_rank_key, reverse=True),
    so all three fields sort descending: pct (high first), hypothesis_id
    (Z-to-A; tie-break is deterministic but alphabetically reversed —
    cosmetic given the small card set), version (newer first).

    Cards without a numeric strongest_cell_pct sort last (-inf).

    Per ADR-0024 D-8 + P1-BEST-OOS-MPPM-RANKING-CUTOVER, the primary
    cuts over to MPPM(ρ=1) once uniformly reported. The cutover branch
    is not yet implemented (deferred follow-up); current behavior returns
    realized-OOS-strongest-cell-pct unconditionally.
    """
    pct = c.strongest_cell_pct if c.strongest_cell_pct is not None else float("-inf")
    return (pct, c.hypothesis_id, c.version)


def _render_top_performer(top: Card) -> str:
    lines: list[str] = []
    lines.append(f"## Top OOS performer — {top.hypothesis_id} v{top.version}")
    lines.append("")
    lines.append(
        f"**[{top.hypothesis_id}]({top.report_card_path})** "
        f"emitted {top.date} (run_id `{(top.run_id or '—')[:16]}...`); "
        f"paradigm `{top.paradigm}`."
    )
    lines.append("")
    lines.append(f"- **Hypothesis-of-record arm**: {top.hypothesis_of_record_arm}")
    lines.append(f"- **Strongest cell**: {top.strongest_cell}")
    pct = _fmt_pct(top.strongest_cell_pct)
    dd = (
        f"{top.strongest_cell_max_dd_pct:.2f}%"
        if top.strongest_cell_max_dd_pct is not None
        else "—"
    )
    sess = _fmt_int(top.oos_sessions)
    lines.append(
        f"- **Realized OOS (strongest cell)**: $10,000 → "
        f"**{pct}** over {sess} sessions; max-DD {dd}"
    )
    if top.sharpe_ann_strongest_cell is not None:
        lines.append(
            f"- **Annualized Sharpe (strongest cell)**: "
            f"{top.sharpe_ann_strongest_cell:+.3f}"
        )
    if top.mppm_rho1_point is not None:
        ci_low = (
            f"{top.mppm_rho1_ci_low:+.4f}" if top.mppm_rho1_ci_low is not None else "—"
        )
        ci_high = (
            f"{top.mppm_rho1_ci_high:+.4f}"
            if top.mppm_rho1_ci_high is not None
            else "—"
        )
        lines.append(
            f"- **MPPM(ρ=1)**: {top.mppm_rho1_point:+.4f} [{ci_low}, {ci_high}]"
        )
    if top.p_loss_pct is not None:
        lines.append(
            f"- **Forward 252-session P(loss)**: {top.p_loss_pct:.2f}%"
        )
    if top.cost_model:
        lines.append(f"- **Cost model**: `{top.cost_model}`")
    if top.primary_annotations:
        lines.append("")
        lines.append("**KPI annotations**: " + " · ".join(
            f"`{a}`" for a in top.primary_annotations
        ))
    return "\n".join(lines) + "\n"


def _render_table(ranked: list[Card]) -> str:
    rows = ["| Rank | Hypothesis | Ver | Strongest cell | Strongest OOS | Max-DD | HoR arm OOS | OOS sess | Fwd P(loss) | Paradigm |"]
    rows.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---|")
    for i, c in enumerate(ranked, start=1):
        rows.append(
            "| {rank} | [{hid}]({path}) | v{ver} | {cell} | {pct} | {dd} | {hor} | {sess} | {pl} | `{para}` |".format(
                rank=i,
                hid=c.hypothesis_id,
                path=c.report_card_path,
                ver=c.version,
                cell=c.strongest_cell,
                pct=_fmt_pct(c.strongest_cell_pct),
                dd=(
                    f"{c.strongest_cell_max_dd_pct:.2f}%"
                    if c.strongest_cell_max_dd_pct is not None
                    else "—"
                ),
                hor=_fmt_pct(c.hypothesis_of_record_arm_pct),
                sess=_fmt_int(c.oos_sessions),
                pl=(f"{c.p_loss_pct:.2f}%" if c.p_loss_pct is not None else "—"),
                para=c.paradigm,
            )
        )
    return "\n".join(rows) + "\n"


def _render_superseded(superseded: list[Card]) -> str:
    if not superseded:
        return ""
    lines = [
        "## Superseded KPI report cards (preserved per ADR-0013 §4.1 non-loss)",
        "",
        "| Hypothesis | Version | Date | Superseded by |",
        "|---|---:|---|---|",
    ]
    for c in superseded:
        lines.append(
            f"| [{c.hypothesis_id}]({c.report_card_path}) | v{c.version} | "
            f"{c.date} | `{c.superseded_by}` |"
        )
    return "\n".join(lines) + "\n"


def render(cards: list[Card], regenerated_at: str) -> str:
    live = _live_cards(cards)
    ranked = sorted(live, key=_rank_key, reverse=True)
    superseded = [c for c in cards if c.superseded_by is not None]

    parts: list[str] = []
    parts.append("# Best Out-of-Sample Results — Showcase\n")
    parts.append(
        "> Auto-generated by [scripts/showcase_best_oos.py](scripts/showcase_best_oos.py) "
        "on every push per [ADR-0024](docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) "
        "D-8. Source: [research/01_hypothesis_register/_oos_showcase_data.yaml](research/01_hypothesis_register/_oos_showcase_data.yaml). "
        "Ranking primary: realized OOS strongest-cell return percent. Cuts over to "
        "MPPM(ρ=1) per [ADR-0018](docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) "
        "D-1 once uniformly reported (`P1-BEST-OOS-MPPM-RANKING-CUTOVER`).\n"
    )
    parts.append(f"_Last regenerated: {regenerated_at}_\n")

    parts.append(
        "## Disclosure\n\n"
        "Each row reports the **strongest cell** in the hypothesis's KPI report card "
        "alongside the **hypothesis-of-record arm**. These may differ: the "
        "hypothesis-of-record is the §1 H_1 pre-registered subject; the strongest cell "
        "is the empirically-best cell from the same run (frequently a within-strategy "
        "comparator or a literature-replication arm). Per [ADR-0022](docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) "
        "§1.3, strategy-quality signals beyond raw realized-OOS percent are surfaced "
        "in the per-card causal-mechanism annotation.\n\n"
        "Per [ADR-0018](docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) "
        "§Context (Lo 2004 AMH framing), strategy decay is the null; realized OOS in "
        "any given window is one path-realization and should be interpreted alongside "
        "the forward-projection P(loss) column and the MPPM(ρ=1) CI when reported.\n"
    )

    if ranked and ranked[0].strongest_cell_pct is not None:
        parts.append(_render_top_performer(ranked[0]))
        parts.append("")

    parts.append("## All emitted KPI report cards (ranked)\n")
    parts.append(_render_table(ranked))

    if superseded:
        parts.append("")
        parts.append(_render_superseded(superseded))

    parts.append("")
    parts.append(
        "## See also\n\n"
        "- [research/01_hypothesis_register/RESULTS_INDEX.md](research/01_hypothesis_register/RESULTS_INDEX.md) — "
        "full KPI report card index with methodology annotations.\n"
        "- [research/01_hypothesis_register/INDEX.md](research/01_hypothesis_register/INDEX.md) — "
        "per-hypothesis stage dashboard.\n"
        "- [docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md](docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) — "
        "the paradigm-resolution ADR mandating this artifact.\n"
        "- [hypothesis_backlog.md](hypothesis_backlog.md) — project-canonical hypothesis register.\n"
    )

    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    if not DATA_PATH.exists():
        sys.stderr.write(f"Data file not found: {DATA_PATH}\n")
        return 1
    try:
        cards = _load_cards(DATA_PATH)
    except (yaml.YAMLError, ValueError) as exc:
        sys.stderr.write(f"Failed to parse {DATA_PATH}: {exc}\n")
        return 1
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = render(cards, timestamp)
    OUTPUT_PATH.write_text(body, encoding="utf-8", newline="\n")
    sys.stdout.write(
        f"Regenerated {OUTPUT_PATH.relative_to(REPO_ROOT)} "
        f"({len(cards)} cards, {len(_live_cards(cards))} live)\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
