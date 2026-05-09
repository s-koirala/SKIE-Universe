"""ADR-0017 v2 dashboard: re-emit H050/H052a/H053/H054 OOS metrics under
survival-constrained primary inference + Pareto-front re-ranking.

Closes Layer 1 cascade per ADR-0017 §Follow-ups
(``P1-ADR-0017-KPI-REPORT-CARD-V2-CASCADE``):

- Re-derives Calmar = annualized_return / max(|MaxDD|, ε) per arm
- Computes Calmar-differential vs the §1-pinned benchmark per hypothesis
- Pulls terminal-wealth-q05 + P(loss) from existing forward-projection
  bootstraps in v1 KPI report cards (5,000 paths × 252 sessions)
- Re-ranks by ADR-0017 §1 primary inferential vector

Strictly post-processing — no walk-forward re-run. Source data:
- artifacts/runs/H052a/<run_id>/{ES,NQ}_metrics_summary.json
- artifacts/runs/H054/<run_id>/ES_metrics_summary.json
- runs/h053/stage3_v4/<run_id>/sidecar.json + H053_kpi_report_v3.md body
- research/01_hypothesis_register/H050/H050_kpi_report_v1.md body

Profit-factor + R-multiple-mean explicitly **n/a** for these hypotheses
per ADR-0017 §2.3 + §2.4 strategy-class taxonomy: H050/H052a/H053/H054
are per-bar (H050) or per-session (H052a/H053/H054) strategies; ADR-0017
§2.4 R-multiple definition requires a per-trade stop-loss-distance which
those classes do not have. Profit-factor would require per-session-or-
per-bar P/L stream which is not preserved in current summary artifacts
(deferred to ``P1-WALK-FORWARD-PER-TRADE-LEDGER-SCHEMA``).

For H055+ (per-trade strategy class), all 4 ADR-0017 primary metrics
will be computable from inception per design.md §1 binding under the
post-2026-05-08 paradigm.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

# All values below are EXTRACTED VERBATIM from the cited source artifacts.
# Provenance is recorded per-cell to enable post-hoc audit.

EPS_DD: Final[float] = 1e-9


@dataclass(frozen=True)
class ArmOOSData:
    """Realized OOS + forward-projection data for one (hypothesis, symbol, arm).

    Sourced from v1 KPI report cards + run-sidecar JSON; all fields extracted
    verbatim with provenance recorded in `source` field.
    """

    hypothesis: str
    symbol: str
    arm: str  # e.g., "hmm_gated", "unconditional", "anti_gated", "elasticnet", "lightgbm", "passive_long"
    role: str  # "PRIMARY" | "BENCHMARK" | "ALT" — per design.md §1 binding
    realized_end_equity: float  # $ at OOS-window-end ($10K starting)
    realized_pct_change: float  # decimal (-0.81 means -81%)
    realized_max_dd_pct: float  # absolute decimal (0.81 means 81%)
    n_oos_sessions: int  # for annualization
    forward_terminal_q05: float  # $ q05 ending equity from 252-sess bootstrap
    forward_terminal_median: float
    forward_p_loss: float  # decimal probability of loss over forward 252 sess
    forward_max_dd_q95: float | None = None  # q95 max-DD from forward bootstrap
    annualised_sharpe_realized: float | None = None  # legacy KPI for cross-comparison
    source: str = "unspecified"


@dataclass(frozen=True)
class V2Cell:
    """One v2 dashboard cell: arm + ADR-0017 metrics + benchmark differential."""

    hypothesis: str
    symbol: str
    arm: str
    role: str
    realized_end_equity: float
    realized_pct_change: float
    realized_max_dd_pct: float
    annualized_return: float
    calmar: float
    calmar_differential_vs_bench: float | None  # None if arm IS the benchmark
    terminal_wealth_q05: float
    forward_p_loss: float
    forward_max_dd_q95: float | None
    annualised_sharpe_realized: float | None
    pareto_dominated_by: list[str] = field(default_factory=list)


def _annualized_return(realized_pct_change: float, n_oos_sessions: int) -> float:
    """Compounded annualized return from period total return + n_sessions.

    Convention: 252 sessions = 1 trading year. annualised = (1 + r_total)^(252/n) - 1.

    For deeply negative returns where 1 + r_total < 0, this is undefined; clamp
    at -0.999 to preserve sign + avoid complex roots (catastrophic loss).
    """
    if realized_pct_change <= -1.0:
        return -0.999
    n_years = n_oos_sessions / 252.0
    if n_years <= 0:
        return realized_pct_change
    return (1.0 + realized_pct_change) ** (1.0 / n_years) - 1.0


def _calmar(ann_return: float, max_dd_pct: float) -> float:
    """Calmar = annualized_return / max(|MaxDD|, ε) per ADR-0017 §2.2."""
    return ann_return / max(abs(max_dd_pct), EPS_DD)


def compile_v2_dashboard() -> list[V2Cell]:
    """Emit the v2 dashboard for H050 + H052a + H053 + H054.

    Returns a flat list of V2Cell records, one per (hypothesis, symbol, arm).
    """
    arms: list[ArmOOSData] = []

    # ─── H050 ─────────────────────────────────────────────────────────────
    # Source: research/01_hypothesis_register/H050/H050_kpi_report_v1.md
    # OOS window: 2024-01-01 → 2025-12-03 ES; → 2025-12-19 NQ; ~2 years.
    # Per H050 v1 §"Realized OOS" + §"Forward 1-year projection" tables.
    H050_SRC = "research/01_hypothesis_register/H050/H050_kpi_report_v1.md (run_id 31d23ecd...)"
    H050_N_SESSIONS_ES = 504  # ~2 OOS years × 252
    H050_N_SESSIONS_NQ = 504
    arms += [
        ArmOOSData(
            hypothesis="H050", symbol="ES", arm="hmm_gated", role="PRIMARY",
            realized_end_equity=1898.23, realized_pct_change=-0.8102, realized_max_dd_pct=0.8112,
            n_oos_sessions=H050_N_SESSIONS_ES,
            forward_terminal_q05=5838.93, forward_terminal_median=6172.60,
            forward_p_loss=1.000, forward_max_dd_q95=0.4175,
            annualised_sharpe_realized=-14.28,
            source=H050_SRC,
        ),
        ArmOOSData(
            hypothesis="H050", symbol="ES", arm="unconditional", role="BENCHMARK",
            realized_end_equity=5630.64, realized_pct_change=-0.4369, realized_max_dd_pct=0.4502,
            n_oos_sessions=H050_N_SESSIONS_ES,
            forward_terminal_q05=7646.47, forward_terminal_median=8471.01,
            forward_p_loss=0.996, forward_max_dd_q95=0.2463,
            annualised_sharpe_realized=-2.63,
            source=H050_SRC,
        ),
        ArmOOSData(
            hypothesis="H050", symbol="NQ", arm="hmm_gated", role="PRIMARY",
            realized_end_equity=1580.46, realized_pct_change=-0.8420, realized_max_dd_pct=0.8436,
            n_oos_sessions=H050_N_SESSIONS_NQ,
            forward_terminal_q05=7181.29, forward_terminal_median=7642.81,
            forward_p_loss=1.000, forward_max_dd_q95=0.2852,
            annualised_sharpe_realized=-7.25,
            source=H050_SRC,
        ),
        ArmOOSData(
            hypothesis="H050", symbol="NQ", arm="unconditional", role="BENCHMARK",
            realized_end_equity=7440.31, realized_pct_change=-0.2560, realized_max_dd_pct=0.3505,
            n_oos_sessions=H050_N_SESSIONS_NQ,
            forward_terminal_q05=8003.69, forward_terminal_median=9596.62,
            forward_p_loss=0.649, forward_max_dd_q95=0.2392,
            annualised_sharpe_realized=-0.39,
            source=H050_SRC,
        ),
    ]

    # ─── H052a ────────────────────────────────────────────────────────────
    # Source: artifacts/runs/H052a/184eccd6.../{ES,NQ}_metrics_summary.json
    H052A_SRC_ES = "artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/ES_metrics_summary.json"
    H052A_SRC_NQ = "artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/NQ_metrics_summary.json"
    arms += [
        ArmOOSData(
            hypothesis="H052a", symbol="ES", arm="hmm_gated", role="PRIMARY",
            realized_end_equity=9905.847867642698, realized_pct_change=-0.009415213235730135,
            realized_max_dd_pct=0.06989532291735988,
            n_oos_sessions=371,
            forward_terminal_q05=9118.693274518331, forward_terminal_median=9942.802199425183,
            forward_p_loss=0.5484, forward_max_dd_q95=0.11220341747047914,
            annualised_sharpe_realized=-0.11901195965038112,
            source=H052A_SRC_ES,
        ),
        ArmOOSData(
            hypothesis="H052a", symbol="ES", arm="unconditional", role="BENCHMARK",
            realized_end_equity=10161.328648674535, realized_pct_change=0.016132864867453467,
            realized_max_dd_pct=0.06677651151808885,
            n_oos_sessions=371,
            forward_terminal_q05=9136.67, forward_terminal_median=10112.78,
            forward_p_loss=0.4294, forward_max_dd_q95=0.1189,
            annualised_sharpe_realized=0.17277932550288713,
            source=H052A_SRC_ES,
        ),
        ArmOOSData(
            hypothesis="H052a", symbol="NQ", arm="hmm_gated", role="PRIMARY",
            realized_end_equity=10338.73, realized_pct_change=0.0339,
            realized_max_dd_pct=0.1183,
            n_oos_sessions=369,
            forward_terminal_q05=9116.80, forward_terminal_median=10244.36,
            forward_p_loss=0.3712, forward_max_dd_q95=0.1312,
            annualised_sharpe_realized=0.313,
            source=H052A_SRC_NQ,
        ),
        ArmOOSData(
            hypothesis="H052a", symbol="NQ", arm="unconditional", role="BENCHMARK",
            realized_end_equity=11061.27, realized_pct_change=0.1061,
            realized_max_dd_pct=0.0795,
            n_oos_sessions=369,
            forward_terminal_q05=9442.41, forward_terminal_median=10729.27,
            forward_p_loss=0.1856, forward_max_dd_q95=0.1243,
            annualised_sharpe_realized=0.855,
            source=H052A_SRC_NQ,
        ),
    ]

    # ─── H053 v3/v4 ───────────────────────────────────────────────────────
    # Source: research/01_hypothesis_register/H053/H053_kpi_report_v3.md
    # benchmark = passive-long per design.md §1.
    H053_SRC = "research/01_hypothesis_register/H053/H053_kpi_report_v3.md (run_id fe051383...)"
    arms += [
        ArmOOSData(
            hypothesis="H053", symbol="ES", arm="elasticnet", role="ALT",
            realized_end_equity=9683.0, realized_pct_change=-0.032,
            realized_max_dd_pct=0.102,
            n_oos_sessions=367,
            forward_terminal_q05=8990.0, forward_terminal_median=9789.0,
            forward_p_loss=0.676, forward_max_dd_q95=0.118,
            annualised_sharpe_realized=-0.452,
            source=H053_SRC,
        ),
        ArmOOSData(
            hypothesis="H053", symbol="ES", arm="lightgbm", role="PRIMARY",
            realized_end_equity=10643.0, realized_pct_change=0.064,
            realized_max_dd_pct=0.045,
            n_oos_sessions=367,
            forward_terminal_q05=9636.0, forward_terminal_median=10434.0,
            forward_p_loss=0.188, forward_max_dd_q95=0.074,
            annualised_sharpe_realized=0.874,
            source=H053_SRC,
        ),
        ArmOOSData(
            hypothesis="H053", symbol="ES", arm="passive_long", role="BENCHMARK",
            realized_end_equity=9996.0, realized_pct_change=0.000,
            realized_max_dd_pct=0.072,
            n_oos_sessions=367,
            forward_terminal_q05=9226.0, forward_terminal_median=9993.0,
            forward_p_loss=0.507, forward_max_dd_q95=0.100,
            annualised_sharpe_realized=-0.005,
            source=H053_SRC,
        ),
        ArmOOSData(
            hypothesis="H053", symbol="NQ", arm="elasticnet", role="ALT",
            realized_end_equity=10617.0, realized_pct_change=0.062,
            realized_max_dd_pct=0.056,
            n_oos_sessions=372,
            forward_terminal_q05=9314.0, forward_terminal_median=10393.0,
            forward_p_loss=0.274, forward_max_dd_q95=0.113,
            annualised_sharpe_realized=0.596,
            source=H053_SRC,
        ),
        ArmOOSData(
            hypothesis="H053", symbol="NQ", arm="lightgbm", role="PRIMARY",
            realized_end_equity=11078.0, realized_pct_change=0.108,
            realized_max_dd_pct=0.037,
            n_oos_sessions=372,
            forward_terminal_q05=9569.0, forward_terminal_median=10699.0,
            forward_p_loss=0.157, forward_max_dd_q95=0.099,
            annualised_sharpe_realized=1.021,
            source=H053_SRC,
        ),
        ArmOOSData(
            hypothesis="H053", symbol="NQ", arm="passive_long", role="BENCHMARK",
            realized_end_equity=10129.0, realized_pct_change=0.013,
            realized_max_dd_pct=0.098,
            n_oos_sessions=372,
            forward_terminal_q05=9015.0, forward_terminal_median=10092.0,
            forward_p_loss=0.443, forward_max_dd_q95=0.132,
            annualised_sharpe_realized=0.128,
            source=H053_SRC,
        ),
    ]

    # ─── H054 ─────────────────────────────────────────────────────────────
    # Source: artifacts/runs/H054/dd916fc6.../ES_metrics_summary.json
    H054_SRC = "artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/ES_metrics_summary.json"
    arms += [
        ArmOOSData(
            hypothesis="H054", symbol="ES", arm="anti_gated", role="PRIMARY",
            realized_end_equity=10349.81, realized_pct_change=0.03498,
            realized_max_dd_pct=0.0319,
            n_oos_sessions=237,
            forward_terminal_q05=9402.22, forward_terminal_median=10319.37,
            forward_p_loss=0.2924, forward_max_dd_q95=0.0854,
            annualised_sharpe_realized=0.573,
            source=H054_SRC,
        ),
        ArmOOSData(
            hypothesis="H054", symbol="ES", arm="unconditional", role="BENCHMARK",
            realized_end_equity=9946.31, realized_pct_change=-0.00537,
            realized_max_dd_pct=0.0699,
            n_oos_sessions=237,
            forward_terminal_q05=8481.31, forward_terminal_median=9930.46,
            forward_p_loss=0.5250, forward_max_dd_q95=0.1928,
            annualised_sharpe_realized=-0.057,
            source=H054_SRC,
        ),
    ]

    # ─── Compute v2 cells ────────────────────────────────────────────────
    # Per-hypothesis benchmark = the arm with role="BENCHMARK" in (hypothesis, symbol).
    # H053 benchmark per design.md §1 = passive_long (arm).
    bench_by_h_sym: dict[tuple[str, str], ArmOOSData] = {}
    for a in arms:
        if a.role == "BENCHMARK":
            bench_by_h_sym[(a.hypothesis, a.symbol)] = a

    cells: list[V2Cell] = []
    for a in arms:
        ann_return = _annualized_return(a.realized_pct_change, a.n_oos_sessions)
        calmar = _calmar(ann_return, a.realized_max_dd_pct)
        bench = bench_by_h_sym.get((a.hypothesis, a.symbol))
        if bench is not None and a.arm != bench.arm:
            bench_ann = _annualized_return(bench.realized_pct_change, bench.n_oos_sessions)
            bench_calmar = _calmar(bench_ann, bench.realized_max_dd_pct)
            calmar_diff = calmar - bench_calmar
        else:
            calmar_diff = None
        cells.append(
            V2Cell(
                hypothesis=a.hypothesis, symbol=a.symbol, arm=a.arm, role=a.role,
                realized_end_equity=a.realized_end_equity,
                realized_pct_change=a.realized_pct_change,
                realized_max_dd_pct=a.realized_max_dd_pct,
                annualized_return=ann_return,
                calmar=calmar,
                calmar_differential_vs_bench=calmar_diff,
                terminal_wealth_q05=a.forward_terminal_q05,
                forward_p_loss=a.forward_p_loss,
                forward_max_dd_q95=a.forward_max_dd_q95,
                annualised_sharpe_realized=a.annualised_sharpe_realized,
            )
        )

    # ─── Pareto-front computation ────────────────────────────────────────
    # ADR-0017 §1 primary objectives (maximize all):
    #   - terminal_wealth_q05 (HIGHER = better)
    #   - calmar (HIGHER = better; negative is bad)
    # AND minimize:
    #   - forward_p_loss (LOWER = better)
    # Pareto-dominance over (terminal_wealth_q05, calmar, -p_loss).
    def dominates(a: V2Cell, b: V2Cell) -> bool:
        """a dominates b iff a is >= b on all 3 axes AND > on at least one."""
        ge_tw = a.terminal_wealth_q05 >= b.terminal_wealth_q05
        ge_calmar = a.calmar >= b.calmar
        le_ploss = a.forward_p_loss <= b.forward_p_loss
        gt_tw = a.terminal_wealth_q05 > b.terminal_wealth_q05
        gt_calmar = a.calmar > b.calmar
        lt_ploss = a.forward_p_loss < b.forward_p_loss
        return (ge_tw and ge_calmar and le_ploss) and (gt_tw or gt_calmar or lt_ploss)

    pareto_marked: list[V2Cell] = []
    for i, c in enumerate(cells):
        dominators: list[str] = []
        for j, d in enumerate(cells):
            if i == j:
                continue
            if dominates(d, c):
                dominators.append(f"{d.hypothesis}/{d.symbol}/{d.arm}")
        pareto_marked.append(
            V2Cell(
                hypothesis=c.hypothesis, symbol=c.symbol, arm=c.arm, role=c.role,
                realized_end_equity=c.realized_end_equity,
                realized_pct_change=c.realized_pct_change,
                realized_max_dd_pct=c.realized_max_dd_pct,
                annualized_return=c.annualized_return,
                calmar=c.calmar,
                calmar_differential_vs_bench=c.calmar_differential_vs_bench,
                terminal_wealth_q05=c.terminal_wealth_q05,
                forward_p_loss=c.forward_p_loss,
                forward_max_dd_q95=c.forward_max_dd_q95,
                annualised_sharpe_realized=c.annualised_sharpe_realized,
                pareto_dominated_by=dominators,
            )
        )

    return pareto_marked


def emit_dashboard_md(cells: list[V2Cell], out_path: Path) -> None:
    """Emit the consolidated v2 dashboard memo."""
    pareto_front = [c for c in cells if not c.pareto_dominated_by]
    pareto_dominated = [c for c in cells if c.pareto_dominated_by]
    sorted_pareto = sorted(
        pareto_front, key=lambda c: (-c.terminal_wealth_q05, c.forward_p_loss)
    )
    sorted_dominated = sorted(
        pareto_dominated, key=lambda c: (-c.terminal_wealth_q05, c.forward_p_loss)
    )

    md: list[str] = []
    md.append(
        "# ADR-0017 v2 OOS Dashboard — Survival-Constrained Re-ranking\n"
        "\n"
        "Re-emits H050/H052a/H053/H054 OOS metrics under the ADR-0017 §1 "
        "primary inferential vector (terminal-wealth-q05 + Calmar-differential "
        "+ forward P(loss)). Sharpe-family metrics are preserved as legacy "
        "secondary KPIs only per ADR-0017 §B + ADR-0013 §1-§7 frozen-pre-reg "
        "immutability.\n"
        "\n"
        "**Strictly post-processing** of existing v1 KPI artifacts; no walk-"
        "forward re-run was performed. Source per cell recorded in the script "
        "[scripts/emit_adr_0017_v2_dashboard.py](../../scripts/emit_adr_0017_v2_dashboard.py).\n"
        "\n"
        "## ADR-0017 §1 Primary Metrics — All Cells\n"
        "\n"
        "Calmar = annualized_return / max(|MaxDD|, ε); ε = 1e-9. "
        "Annualization: (1 + r_total)^(252/n_oos_sessions) − 1.\n"
        "\n"
        "| Hypothesis | Symbol | Arm | Role | Realized end ($10K start) | Max-DD | Calmar | "
        "Calmar-diff vs bench | Terminal-wealth-q05 | Forward P(loss) | Pareto |\n"
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|\n"
    )

    def cell_row(c: V2Cell, *, pareto_label: str) -> str:
        diff = (
            f"{c.calmar_differential_vs_bench:+.3f}"
            if c.calmar_differential_vs_bench is not None else "—"
        )
        return (
            f"| {c.hypothesis} | {c.symbol} | {c.arm} | {c.role} | "
            f"${c.realized_end_equity:,.0f} ({c.realized_pct_change:+.1%}) | "
            f"{c.realized_max_dd_pct:.1%} | {c.calmar:+.3f} | {diff} | "
            f"${c.terminal_wealth_q05:,.0f} | {c.forward_p_loss:.1%} | "
            f"{pareto_label} |"
        )

    for c in sorted(cells, key=lambda c: (c.hypothesis, c.symbol, c.arm)):
        label = "**FRONT**" if not c.pareto_dominated_by else f"dom by {len(c.pareto_dominated_by)}"
        md.append(cell_row(c, pareto_label=label))

    md.append("")
    md.append("## Pareto Front (no cell dominates these on terminal-wealth-q05 + Calmar + −P(loss))\n")
    md.append(
        "Sorted by terminal-wealth-q05 descending, then forward P(loss) ascending.\n"
    )
    md.append(
        "| Rank | Hypothesis | Symbol | Arm | Terminal-wealth-q05 | Calmar | "
        "Forward P(loss) | Realized end | Max-DD |\n"
        "|---:|---|---|---|---:|---:|---:|---:|---:|\n"
    )
    for i, c in enumerate(sorted_pareto, 1):
        md.append(
            f"| {i} | {c.hypothesis} | {c.symbol} | {c.arm} | "
            f"${c.terminal_wealth_q05:,.0f} | {c.calmar:+.3f} | "
            f"{c.forward_p_loss:.1%} | ${c.realized_end_equity:,.0f} | "
            f"{c.realized_max_dd_pct:.1%} |"
        )

    md.append("")
    md.append("## Dominated Cells (sorted by terminal-wealth-q05 desc)\n")
    md.append(
        "| Hypothesis | Symbol | Arm | Terminal-wealth-q05 | Calmar | "
        "Forward P(loss) | Dominated by |\n"
        "|---|---|---|---:|---:|---:|---|\n"
    )
    for c in sorted_dominated:
        dom = "; ".join(c.pareto_dominated_by[:3]) + (
            f" +{len(c.pareto_dominated_by) - 3} more"
            if len(c.pareto_dominated_by) > 3 else ""
        )
        md.append(
            f"| {c.hypothesis} | {c.symbol} | {c.arm} | "
            f"${c.terminal_wealth_q05:,.0f} | {c.calmar:+.3f} | "
            f"{c.forward_p_loss:.1%} | {dom} |"
        )

    md.append("")
    md.append("## ADR-0017 §1 Primary Verdict — Per Hypothesis\n")
    by_h: dict[str, list[V2Cell]] = {}
    for c in cells:
        by_h.setdefault(c.hypothesis, []).append(c)
    for h in sorted(by_h):
        cells_h = by_h[h]
        # Find primary arm and benchmark
        primary = next((c for c in cells_h if c.role == "PRIMARY"), None)
        bench = next((c for c in cells_h if c.role == "BENCHMARK"), None)
        md.append(f"### {h}\n")
        if primary is not None and bench is not None:
            md.append(
                f"- **Primary arm**: `{primary.arm}` — terminal-wealth-q05 = "
                f"${primary.terminal_wealth_q05:,.0f}; Calmar = {primary.calmar:+.3f}; "
                f"forward P(loss) = {primary.forward_p_loss:.1%}\n"
            )
            md.append(
                f"- **Benchmark**: `{bench.arm}` — terminal-wealth-q05 = "
                f"${bench.terminal_wealth_q05:,.0f}; Calmar = {bench.calmar:+.3f}; "
                f"forward P(loss) = {bench.forward_p_loss:.1%}\n"
            )
            calmar_diff = primary.calmar - bench.calmar
            tw_diff = primary.terminal_wealth_q05 - bench.terminal_wealth_q05
            ploss_diff = primary.forward_p_loss - bench.forward_p_loss
            md.append(
                f"- **Differential (primary − benchmark)**: ΔCalmar = "
                f"{calmar_diff:+.3f}; Δterminal-wealth-q05 = ${tw_diff:+,.0f}; "
                f"ΔP(loss) = {ploss_diff:+.1%}\n"
            )
            # Verdict
            verdict_signs = (
                int(calmar_diff > 0) + int(tw_diff > 0) + int(ploss_diff < 0)
            )
            if verdict_signs == 3:
                verdict = "**PRIMARY DOMINATES BENCHMARK** on all 3 axes"
            elif verdict_signs == 0:
                verdict = "**PRIMARY IS DOMINATED BY BENCHMARK** on all 3 axes"
            else:
                verdict = (
                    f"**MIXED** ({verdict_signs}/3 axes favor primary; "
                    "no Pareto verdict)"
                )
            md.append(f"- **ADR-0017 §1 verdict**: {verdict}\n")
        md.append("")

    md.append("## Profit-factor + R-multiple-mean (deferred per strategy class)\n")
    md.append(
        "Per ADR-0017 §2.3 + §2.4: **profit-factor** requires per-session-or-"
        "per-bar P/L stream; **R-multiple-mean** requires per-trade stop-loss-"
        "distance + position-size + multiplier (definition: "
        "`R = realized_pnl / (stop_distance × position_size × multiplier)`).\n"
        "\n"
        "- H050: per-bar HMM-gated; no per-trade stop → R-multiple structurally **n/a**. "
        "Profit-factor needs per-bar P/L stream (`oos_returns.parquet` not in worktree); "
        "tracked under `P1-WALK-FORWARD-PER-TRADE-LEDGER-SCHEMA`.\n"
        "- H052a / H054: per-session ORB; no per-trade stop in summary → R-multiple **n/a**. "
        "Profit-factor needs per-session P/L stream (not preserved in metrics_summary.json).\n"
        "- H053: per-session prediction → arm trade; no per-trade stop → R-multiple **n/a**. "
        "Profit-factor needs per-session P/L stream from sidecar; not yet exposed in "
        "scientific_payload.\n"
        "- H055+ (per-trade ATR-scaled TP/SL): all 4 ADR-0017 primary metrics computable "
        "from inception per design.md §1.\n"
        "\n"
        "Follow-up `P1-PER-SESSION-PNL-STREAM-EXPORT` (BLOCKING-BEFORE-FULL-V2-CASCADE): "
        "extend orchestrator outputs to preserve per-session P/L streams enabling "
        "profit-factor + period-Sharpe + arm-vs-bench distributional CI.\n"
    )

    md.append("\n## Methodological annotations\n")
    md.append(
        "- **Annualization**: realized period return → annualized via "
        "(1 + r)^(252/n_oos) − 1; clamped at −0.999 to preserve sign on "
        "catastrophic loss without complex roots.\n"
        "- **Calmar denominator**: max(|MaxDD|, 1e-9); ε per ADR-0017 §2.2.\n"
        "- **Forward projection**: 5,000 paths × 252 sessions; iid bootstrap "
        "where PW2004-selected block length = 1.0 else stationary bootstrap "
        "(Politis-Romano 1994). Per arm × symbol from existing v1 cards.\n"
        "- **Pareto-dominance**: arm a dominates arm b iff a ≥ b on "
        "(terminal-wealth-q05, Calmar) AND a ≤ b on forward P(loss), with "
        "strict inequality on at least one axis.\n"
        "- **Sharpe column omitted from primary table** per ADR-0017 §B; "
        "preserved per arm internally but not displayed in the operator-"
        "facing primary inferential view.\n"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(md))


def emit_dashboard_json(cells: list[V2Cell], out_path: Path) -> None:
    """Emit JSON sidecar with the same data for programmatic consumption."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "adr_0017_v2_dashboard_v1",
        "n_cells": len(cells),
        "cells": [
            {
                "hypothesis": c.hypothesis,
                "symbol": c.symbol,
                "arm": c.arm,
                "role": c.role,
                "realized_end_equity": c.realized_end_equity,
                "realized_pct_change": c.realized_pct_change,
                "realized_max_dd_pct": c.realized_max_dd_pct,
                "annualized_return": c.annualized_return,
                "calmar": c.calmar,
                "calmar_differential_vs_bench": c.calmar_differential_vs_bench,
                "terminal_wealth_q05": c.terminal_wealth_q05,
                "forward_p_loss": c.forward_p_loss,
                "forward_max_dd_q95": c.forward_max_dd_q95,
                "annualised_sharpe_realized_legacy": c.annualised_sharpe_realized,
                "pareto_dominated_by": c.pareto_dominated_by,
                "is_pareto_front": len(c.pareto_dominated_by) == 0,
            }
            for c in cells
        ],
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=2)


def main() -> int:
    cells = compile_v2_dashboard()
    project_root = Path(__file__).resolve().parents[1]
    md_path = project_root / "docs" / "research_notes" / "adr_0017_v2_oos_dashboard_2026-05-09.md"
    json_path = project_root / "docs" / "research_notes" / "adr_0017_v2_oos_dashboard_2026-05-09.json"
    emit_dashboard_md(cells, md_path)
    emit_dashboard_json(cells, json_path)
    print(f"Wrote {md_path.relative_to(project_root)}")
    print(f"Wrote {json_path.relative_to(project_root)}")
    print(f"Total cells: {len(cells)}")
    print(f"Pareto front: {sum(1 for c in cells if not c.pareto_dominated_by)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
