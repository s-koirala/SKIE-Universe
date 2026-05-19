"""Cost-realism investigation computation per ADR-0027 §D-1 INVESTIGATE-FAILURE-MODE.

Computes per-(hypothesis × symbol) cost-friction-breakeven ratios using the
conservative-prior cost model machinery from src/skie_ninja/backtest/costs/.

Three cost models are used by emitted KPIs:
  - nt8_es_nq_rth_v1     : ES/NQ/MES/MNQ bar-cadence cost
  - futures_orb_v1       : ES/NQ/MES/MNQ per-session ORB cost (H052a)
  - nt8_realistic_v1     : ES/NQ/MES/MNQ/MGC/SIL/MCL bar-cadence cost (ADR-0025)

Cost-friction-breakeven ratio definition (per task spec):
  ratio = realized_gross_per_trade_return_bps / round_trip_cost_bps

Where:
  - realized_gross_per_trade_return_bps = (realized_OOS_arm_pct/100) / n_trades * 10000
    (arithmetic average per-trade return as fraction of starting equity, in bps)
  - round_trip_cost_bps = round_trip_cost_USD / notional * 10000
    notional = entry_price_avg * multiplier * 1 contract (1-contract assumption per
    the conservative-prior config; v1 sizing at retail $10K floors to 1-2 contracts)

Classification per task spec §3-4:
  - ratio >= 2 AND zero-cost realized OOS > 0%   --> cost-friction-dominated-edge-present
  - ratio < 1 AND zero-cost OOS <= 0%             --> edge-absent
  - 1 <= ratio < 2 AND zero-cost OOS > 0%         --> marginal (under-strict-cost-bound)
  - no A0 zero-cost reference                     --> likely-* (pending-A0-verification)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

# ---------------------------------------------------------------------------
# Cost-model construction (per ADR-0017 §3 cost-machinery binding)
# ---------------------------------------------------------------------------
# Per src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py + nt8_realistic.py
# at sensitivity_mult=1.0 (default 1-tick prior):

ROUND_TRIP_COST_USD = {
    # ES/NQ: 2 * (2.05 fixed + 1.0 * tick_slip)
    "ES": 2 * (2.05 + 12.50),       # = $29.10 / 1 contract / round trip
    "NQ": 2 * (2.05 + 5.00),        # = $14.10
    "MES": 2 * (0.72 + 1.25),       # = $3.94
    "MNQ": 2 * (0.72 + 0.50),       # = $2.44
    "MGC": 2 * (1.32 + 1.00),       # = $4.64 (placeholder per P1-METALS-ENERGY-CME-FEE-VERIFY)
    "SIL": 2 * (1.32 + 5.00),       # = $12.64 (placeholder)
    "MCL": 2 * (1.37 + 1.00),       # = $4.74 (placeholder)
}

# Approximate notional at typical OOS-window-mid prices (per config/instruments.yaml
# multiplier × representative price; used for cost-as-bps-of-notional).
# Prices taken from approximate 2024-2025 mid-window levels.
REPRESENTATIVE_PRICE = {
    "ES": 5000.0,   # SPX 2024 ~5000
    "NQ": 18000.0,  # NDX 2024 ~18000
    "MES": 5000.0,
    "MNQ": 18000.0,
    "MGC": 2200.0,  # gold 2024 ~2200/oz
    "SIL": 27.0,    # silver 2024 ~27/oz
    "MCL": 75.0,    # WTI 2024 ~75
}

MULTIPLIER = {
    "ES": 50.0, "NQ": 20.0, "MES": 5.0, "MNQ": 2.0,
    "MGC": 10.0, "SIL": 1000.0, "MCL": 100.0,
}


def notional_usd(symbol: str, n_contracts: int = 1) -> float:
    return REPRESENTATIVE_PRICE[symbol] * MULTIPLIER[symbol] * n_contracts


def round_trip_cost_bps(symbol: str, n_contracts: int = 1) -> float:
    cost = ROUND_TRIP_COST_USD[symbol] * n_contracts
    nom = notional_usd(symbol, n_contracts)
    return cost / nom * 10000.0


@dataclass
class Cell:
    hypothesis: str
    symbol: str  # 'basket' for aggregate
    realized_oos_pct: float          # %
    n_trades: int
    zero_cost_reference_pct: float | None  # %; None when no A0 cell exists
    cost_model: str                  # cost-model id string
    n_oos_sessions: int | None = None
    notes: str = ""


def per_trade_return_bps_of_equity(roi_pct: float, n_trades: int) -> float | None:
    if n_trades <= 0:
        return None
    # arithmetic average per-trade return as fraction of starting equity, in bps
    return (roi_pct / 100.0) / n_trades * 10000.0


# Per ADR-0017 §4.1 sizing + design.md §5.3 retail $10K starting equity, kelly_multiplier 0.25,
# risk_budget 1% per trade. The position-size formula → typically 1-2 contracts.
# Leverage = notional / equity at typical 1-contract-position.
STARTING_EQUITY = 10000.0


def implied_leverage(symbol: str, n_contracts: int = 1) -> float:
    return notional_usd(symbol, n_contracts) / STARTING_EQUITY


def cost_bps_of_equity(symbol: str, n_contracts: int = 1) -> float:
    """Per-round-trip cost expressed as bps of $10K starting equity (not notional).

    This is the dimensionally-correct denominator for comparing against
    avg_per_trade_return_bps_of_equity. The implicit assumption is
    1-contract-position; ADR-0017 §4.1 + design.md §5.3 retail Kelly-0.25 + risk-1%
    typically floors size to 1 contract at $10K equity (ES particularly).
    """
    # cost ($) / equity ($) * 10000 = cost_bps_of_equity
    return ROUND_TRIP_COST_USD[symbol] * n_contracts / STARTING_EQUITY * 10000.0


def classify(cell: Cell) -> tuple[float | None, str]:
    """Returns (cost_friction_breakeven_ratio, classification)."""
    if cell.symbol in ("basket", "BASKET"):
        # basket-level cost cannot be assigned to a single symbol; use the
        # heaviest-weighted symbol's cost or skip; we report per-cell only
        return None, "basket-aggregate-skip-per-symbol-only"
    if cell.n_trades == 0:
        return None, "zero-trades-no-friction-applied"
    if cell.symbol not in ROUND_TRIP_COST_USD:
        return None, "no-cost-model-coverage"
    avg_per_trade_bps = per_trade_return_bps_of_equity(cell.realized_oos_pct, cell.n_trades)
    if avg_per_trade_bps is None:
        return None, "zero-trades-no-friction-applied"
    # DIMENSIONAL CORRECTION (per H062 v3 ablation A0/A1 verification 2026-05-19):
    # avg_per_trade_bps is bps-of-EQUITY; cost-per-rt is $-per-contract;
    # convert cost to bps-of-equity for apples-to-apples comparison.
    cost_bps_equity = cost_bps_of_equity(cell.symbol)
    # cost_friction_breakeven = gross-per-trade-return / cost-per-trade
    # If ratio >= 2: gross-edge is at least 2× round-trip-cost; strategy
    # produces edge that can comfortably absorb conservative-prior friction.
    # If 1 <= ratio < 2: gross-edge barely covers cost; marginal under realistic.
    # If ratio < 1: friction exceeds gross-edge; strategy is cost-friction-dominated.
    ratio = abs(avg_per_trade_bps) / cost_bps_equity if cost_bps_equity > 0 else float("inf")

    if cell.zero_cost_reference_pct is None:
        # Inference-only classification (no A0 reference)
        if ratio >= 2 and cell.realized_oos_pct > 0:
            return ratio, "likely-cost-friction-dominated-pending-A0-verification"
        if cell.realized_oos_pct <= 0:
            return ratio, "likely-edge-absent"
        return ratio, "likely-marginal-pending-A0"
    else:
        # Verified classification (A0 reference present)
        if cell.zero_cost_reference_pct > 0:
            if ratio >= 2:
                return ratio, "cost-friction-dominated-edge-present"
            if 1 <= ratio < 2:
                return ratio, "cost-friction-marginal-edge-present"
            return ratio, "edge-present-cost-light"
        else:
            return ratio, "edge-absent"


# ---------------------------------------------------------------------------
# Cell inventory (v(latest) per RESULTS_INDEX.md)
# ---------------------------------------------------------------------------

CELLS = [
    # H050 v1 — HMM-gated 1-min intraday ES/NQ (cost = NT8 RTH v1)
    # Sidecar absent in worktree; use KPI card §1 P/L table directly.
    Cell("H050 v1", "ES",  -81.02, 337837, None, "nt8_es_nq_rth_v1",
         866, notes="HMM-gated arm; sidecar absent; n_trades approx = OOS bars (multibar intraday)"),
    Cell("H050 v1", "NQ",  -84.20, 673274, None, "nt8_es_nq_rth_v1",
         1726, notes="HMM-gated arm; sidecar absent; n_trades approx = OOS bars"),
    # NOTE: H050's "n_trades" in the KPI card is bar-count not entry-count; the
    # strategy is bar-level holding so "per-trade" is per-bar. Cost per bar is
    # appropriate metric. This understates per-trade-edge significantly.
    # H050 v1 unconditional comparator
    Cell("H050 v1 (uncond)", "ES", -43.69, 337837, None, "nt8_es_nq_rth_v1",
         866, notes="unconditional reference; same bar-level convention"),
    Cell("H050 v1 (uncond)", "NQ", -25.60, 673274, None, "nt8_es_nq_rth_v1",
         1726, notes="unconditional reference"),

    # H052a v1 — HMM-gated first-hour ORB on ES/NQ (cost = futures_orb_v1)
    Cell("H052a v1", "ES",   -0.94, 371,    None, "futures_orb_v1",
         371, notes="gated arm; daily-cleared session-cadence"),
    Cell("H052a v1", "NQ",   +3.39, 369,    None, "futures_orb_v1",
         369, notes="gated arm; daily-cleared"),
    Cell("H052a v1 (uncond)", "ES",  +1.61, 371,    None, "futures_orb_v1",
         371, notes="unconditional ORB"),
    Cell("H052a v1 (uncond)", "NQ", +10.61, 369,    None, "futures_orb_v1",
         369, notes="unconditional ORB; literature-replication strongest cell"),

    # H053 v3 — multi-tf intraday 09:45→10:30 (cost = NT8 RTH v1; not applied at v3)
    Cell("H053 v3 LightGBM", "ES",  +6.40, 367, None, "nt8_es_nq_rth_v1",
         367, notes="LightGBM arm; session-cadence (1 entry/session) cost ≈ NT8 RTH"),
    Cell("H053 v3 LightGBM", "NQ", +10.80, 372, None, "nt8_es_nq_rth_v1",
         372, notes="LGBM strongest projected"),
    Cell("H053 v3 ElasticNet", "ES", -3.20, 367, None, "nt8_es_nq_rth_v1",
         367, notes="ElasticNet arm"),
    Cell("H053 v3 ElasticNet", "NQ", +6.20, 372, None, "nt8_es_nq_rth_v1",
         372, notes="ElasticNet"),
    # Passive-long bench for direct comparison
    Cell("H053 v3 passive", "ES",   0.0, 367, None, "nt8_es_nq_rth_v1",
         367, notes="passive long; one entry/exit per session"),
    Cell("H053 v3 passive", "NQ",  +1.30, 372, None, "nt8_es_nq_rth_v1",
         372, notes="passive long"),

    # H055 v2 — wick-reversal scalping (cost = nt8_realistic / NT8 RTH v1)
    # Reading from sweep_sidecar.json results — only documenting cells with n_trades > 0
    Cell("H055 v2 C2_fullkelly",   "ES",  -0.97,   641, None, "nt8_realistic_v1"),
    Cell("H055 v2 C3_superkelly",  "ES", +23.09,  3301, None, "nt8_realistic_v1"),
    Cell("H055 v2 C9_bocd_stepup", "ES",  -0.79,   653, None, "nt8_realistic_v1"),
    Cell("H055 v2 C5_super_pyramid","ES", -53.48,  706, None, "nt8_realistic_v1"),

    Cell("H055 v2 C2_fullkelly",   "NQ",  +0.89,    26, None, "nt8_realistic_v1"),
    Cell("H055 v2 C3_superkelly",  "NQ", -19.30,   530, None, "nt8_realistic_v1"),
    Cell("H055 v2 C9_bocd_stepup", "NQ",  -8.69,   249, None, "nt8_realistic_v1"),
    Cell("H055 v2 C5_super_pyramid","NQ", -14.30,  584, None, "nt8_realistic_v1"),

    Cell("H055 v2 v1baseline",     "MGC",  -1.22,  3622, None, "nt8_realistic_v1"),
    Cell("H055 v2 C2_fullkelly",   "MGC", +72.37, 10321, None, "nt8_realistic_v1"),
    Cell("H055 v2 C3_superkelly",  "MGC", +87.04,  7625, None, "nt8_realistic_v1"),
    Cell("H055 v2 C9_bocd_stepup", "MGC", +58.04,  9442, None, "nt8_realistic_v1"),
    Cell("H055 v2 C5_super_pyramid","MGC", +77.19,  7665, None, "nt8_realistic_v1"),

    Cell("H055 v2 v1baseline",     "SIL",  -1.21,   329, None, "nt8_realistic_v1"),
    Cell("H055 v2 C2_fullkelly",   "SIL",  +1.83,  5978, None, "nt8_realistic_v1"),
    Cell("H055 v2 C3_superkelly",  "SIL", -10.12,  4177, None, "nt8_realistic_v1"),
    Cell("H055 v2 C9_bocd_stepup", "SIL",  +7.23,  3959, None, "nt8_realistic_v1"),
    Cell("H055 v2 C5_super_pyramid","SIL", -46.58,  3509, None, "nt8_realistic_v1"),

    # H060 v2 — cross-futures TSMOM daily (cost = nt8_realistic_v1)
    # No per-symbol n_trades; basket-only realized; n_sessions = 1,260
    # TSMOM is daily-rebalance with low turnover; n_trades_per_symbol ≈ 12-24/year
    # over 5-year OOS window → 60-120 round-trips per symbol
    Cell("H060 v2 TSMOM", "basket", +68.75, 0, None, "nt8_realistic_v1",
         1260, notes="basket-aggregate only; per-symbol n_trades unavailable in sidecar"),

    # H062 v2 — intraday Donchian breakout
    # Critical: A0 (zero-cost) + A1 (cost-only) sidecars from Phase O.15 ablation
    # provide direct zero-cost reference. A0 ROI = +261.88% on 10,326 trades.
    # H062 v2 full-grid run was also zero-cost; v2 ROI = +217.57% on 9,653 trades.
    # Use A0 fixture as the zero-cost reference (matches v2 ablation pattern)
    Cell("H062 v2 (Phase-O.15 A0)", "ES",   None, 97, None, "nt8_realistic_v1",
         notes="zero-cost reference; per-symbol breakdown from A0 sidecar; ROI not separately stored per-symbol"),
    # H062 v2 main sidecar — per-symbol n_trades only (no per-symbol ROI)
    # Use the A0 zero-cost as the implicit reference for cost-attribution.
    # Per-symbol ROIs estimated via Phase O.13 H062 v3 ablation A0 per-symbol final equity:
    # A3 (equity-rebase-only, ROI variant): ES +21.4%; NQ 0% (no trades); MGC -11.4%; SIL +189.2%
    # NOTE: A3 reflects equity-rebase semantics not pure A0 — interpret carefully
    # For cost-friction analysis, the load-bearing reference is A0 cumulative basket = +261.88%
    # and A1 cumulative basket = -100% with IDENTICAL 10,326 trades.
    Cell("H062 v3 A0 (zero-cost basket)", "basket",
         +261.88, 10326, None, "(reference; basket aggregate)",
         notes="A0 zero-cost reference from Phase O.15 ablation; sidecar 5e52f0b7"),
    Cell("H062 v3 A1 (conservative-prior basket)", "basket",
         -99.99997, 10326, +261.88, "nt8_realistic_v1",
         notes="A1 cost-only with IDENTICAL trade set; load-bearing precedent"),

    # H065 v2 — TP-overlay on H062 (subset)
    # Per-cell from per_symbol_results — only cells with n_trades > 5 reported
    Cell("H065 v2 M_inf_h062_v1_fixed", "ES",   +40.54,  110, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_inf_h065_current",  "ES",   +54.37,  759, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_1.0",               "ES",    +8.18,  147, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_1.5",               "ES",   +18.15,  211, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_2.0",               "ES",    +2.23,  169, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_2.5",               "ES",    +3.35,  187, None, "nt8_realistic_v1"),

    Cell("H065 v2 M_inf_h062_v1_fixed", "MGC", +116.48, 5221, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_inf_h065_current",  "MGC",  -82.69, 3611, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_1.0",               "MGC",  +62.25, 9591, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_1.5",               "MGC",   -7.84, 7326, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_2.0",               "MGC",   -0.65, 7055, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_2.5",               "MGC",  -68.81, 5084, None, "nt8_realistic_v1"),

    Cell("H065 v2 M_inf_h062_v1_fixed", "SIL", +446.38, 4165, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_inf_h065_current",  "SIL", +734.68, 5600, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_1.0",               "SIL",  -62.71, 2993, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_1.5",               "SIL",  -58.26, 3015, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_2.0",               "SIL",  -36.26, 3859, None, "nt8_realistic_v1"),
    Cell("H065 v2 M_2.5",               "SIL",  -60.67, 3623, None, "nt8_realistic_v1"),
]

# ---------------------------------------------------------------------------
# Computation + output
# ---------------------------------------------------------------------------

def main():
    print("=" * 130)
    print("Cost-realism investigation per ADR-0027 §D-1")
    print("Per-cell cost-friction-breakeven analysis using conservative_prior cost models")
    print("=" * 130)
    print()
    print("Cost-per-round-trip (USD per 1 contract) under conservative_prior:")
    print(f"  {'Sym':4s}  {'Cost($)':>8s}  {'Notional($)':>12s}  {'cost_bps_notional':>17s}  {'cost_bps_equity':>15s}  Comment")
    for sym, cost in ROUND_TRIP_COST_USD.items():
        nom = notional_usd(sym, 1)
        bps_not = round_trip_cost_bps(sym, 1)
        bps_eq = cost_bps_of_equity(sym, 1)
        print(f"  {sym:4s}  {cost:>8.2f}  {nom:>12,.0f}  {bps_not:>17.3f}  {bps_eq:>15.3f}")
    print()
    print("Cost-bps-of-equity is the load-bearing denominator (avg-per-trade-return is bps-of-equity).")
    print()
    print(f"{'Hypothesis × Cell':<42s} {'Sym':<6s} {'OOS%':>8s} {'n_tr':>7s} {'avg_per_tr_bps_eq':>17s} {'cost_bps_eq':>13s} {'breakeven':>10s} {'A0 zero-cost%':>14s} {'classification':<46s}")
    print("-" * 165)
    rows = []
    for c in CELLS:
        if c.realized_oos_pct is None:
            continue  # skip "marker" cells
        ratio, cls = classify(c)
        avg_bps_eq = per_trade_return_bps_of_equity(c.realized_oos_pct, c.n_trades) if c.n_trades > 0 else None
        cost_bps_eq = cost_bps_of_equity(c.symbol) if c.symbol in ROUND_TRIP_COST_USD else None
        ratio_s = f"{ratio:8.3f}" if ratio is not None else "    n/a"
        avg_s = f"{avg_bps_eq:15.3f}" if avg_bps_eq is not None else "            n/a"
        cost_s = f"{cost_bps_eq:11.3f}" if cost_bps_eq is not None else "        n/a"
        roi_s = f"{c.realized_oos_pct:+7.2f}%"
        ref_s = f"{c.zero_cost_reference_pct:+7.2f}%" if c.zero_cost_reference_pct is not None else "          n/a"
        print(f"{c.hypothesis:<42s} {c.symbol:<6s} {roi_s:>8s} {c.n_trades:>7d} {avg_s:>17s} {cost_s:>13s} {ratio_s:>10s} {ref_s:>14s} {cls:<46s}")
        rows.append({
            "hypothesis": c.hypothesis,
            "symbol": c.symbol,
            "realized_oos_pct": c.realized_oos_pct,
            "n_trades": c.n_trades,
            "avg_per_trade_return_bps_of_equity": avg_bps_eq,
            "cost_per_round_trip_bps_of_equity": cost_bps_eq,
            "cost_friction_breakeven_ratio": ratio,
            "zero_cost_reference_pct": c.zero_cost_reference_pct,
            "classification": cls,
            "cost_model": c.cost_model,
            "notes": c.notes,
        })

    print()
    # Cost-friction-dominated cells (ratio >= 2 + positive realized; under either A0 inference or verified)
    print("=" * 130)
    print("Cells classified as cost-friction-dominated (ratio >= 2 + positive realized):")
    print("=" * 130)
    for r in rows:
        if r["cost_friction_breakeven_ratio"] is not None and r["realized_oos_pct"] > 0 and r["cost_friction_breakeven_ratio"] >= 2:
            print(f"  {r['hypothesis']:<42s} {r['symbol']:<6s} ratio={r['cost_friction_breakeven_ratio']:7.2f}  oos={r['realized_oos_pct']:+7.2f}%  {r['classification']}")
    print()
    # Ranking by ratio (descending = most resilient to cost; ascending = worst-friction-burden)
    print("=" * 130)
    print("Top-10 cells by cost-friction-breakeven ratio (descending; highest = most resilient under realistic cost):")
    print("=" * 130)
    sorted_rows = sorted(
        [r for r in rows if r["cost_friction_breakeven_ratio"] is not None],
        key=lambda x: x["cost_friction_breakeven_ratio"], reverse=True,
    )
    for i, r in enumerate(sorted_rows[:10], start=1):
        print(f"  {i:2d}. {r['hypothesis']:<42s} {r['symbol']:<6s} ratio={r['cost_friction_breakeven_ratio']:7.2f}  oos={r['realized_oos_pct']:+7.2f}%  n_tr={r['n_trades']:>6d}  {r['classification']}")
    print()
    # Bottom-10 cells by ratio (ascending = worst-friction-burden first)
    print("Bottom-10 cells by cost-friction-breakeven ratio (ascending; lowest = worst friction burden):")
    print("=" * 130)
    for i, r in enumerate(sorted_rows[-10:], start=1):
        print(f"  {i:2d}. {r['hypothesis']:<42s} {r['symbol']:<6s} ratio={r['cost_friction_breakeven_ratio']:7.2f}  oos={r['realized_oos_pct']:+7.2f}%  n_tr={r['n_trades']:>6d}  {r['classification']}")
    print()

    # Dump JSON for reproducibility
    out_path = Path("artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "schema_version": "cost_friction_breakeven_v1",
            "round_trip_cost_usd": ROUND_TRIP_COST_USD,
            "representative_price": REPRESENTATIVE_PRICE,
            "multiplier": MULTIPLIER,
            "rows": rows,
        }, f, indent=2)
    print(f"Wrote artifacts to {out_path}")


if __name__ == "__main__":
    main()
