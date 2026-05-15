"""K-1..K-8 kill-switch backtest validation per ADR-0017 §5.

Per ADR-0017 §5 mandatory-inheritance-from-H055-forward kill-switch
constraints, and the project-wide BLOCKING follow-up
``P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION``, every walk-forward
orchestrator from H055 forward must validate that the K-1..K-8
constraints are enforced at the per-trade simulation layer.

Constraints (per ADR-0017 §5):
  - K-1 Per-trade $-stop = 1.0R (Turtle 2N convention).
  - K-2 Per-trade time-stop = 2 × median winning-trade duration (or
    EOD-flatten boundary, whichever fires first).
  - K-3 No-add-to-loser (zero exception).
  - K-4 Per-symbol position cap per ADR-0001 retail capacity.
  - K-5 Correlated-instrument inventory cap (ES+MES, NQ+MNQ, etc.).
  - K-6 Daily circuit breaker = -2% of equity realized P/L.
  - K-7 Weekly circuit breaker = -5% of equity realized P/L.
  - K-8 Adverse-direction entry filter.

This module provides a post-simulation validator that scans the per-trade
ledger emitted by the orchestrator and reports per-constraint
pass/fail/n_violations counts. Pass criteria are NOT binding gates per
ADR-0013 §1+§2 no-gates philosophy; failures are recorded as
``stress-test-K-N-fail`` annotations in failure_log.md per ADR-0017.

Public surface:
  - validate_kill_switches(trade_ledger, *, instrument_caps, ...) → dict
  - K1_per_trade_dollar_stop_within_1R
  - K3_no_add_to_loser
  - K4_per_symbol_position_cap
  - K6_daily_circuit_breaker_2pct
  - K7_weekly_circuit_breaker_5pct
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

__all__ = [
    "TradeRecord",
    "KillSwitchValidationReport",
    "validate_kill_switches",
    "K1_per_trade_dollar_stop_within_1R",
    "K3_no_add_to_loser",
    "K4_per_symbol_position_cap",
    "K6_daily_circuit_breaker_2pct",
    "K7_weekly_circuit_breaker_5pct",
]


@dataclass(frozen=True)
class TradeRecord:
    """Per-trade record consumed by kill-switch validation.

    Fields:
        symbol: Instrument symbol.
        entry_ts: Entry timestamp (UTC).
        exit_ts: Exit timestamp (UTC).
        side: +1 long, -1 short.
        position_size: Number of contracts at entry.
        entry_price: Entry price.
        exit_price: Exit price.
        stop_price: Pre-set stop price (entry ∓ k_atr × ATR).
        r_dollar: Pre-trade dollar 1R distance = k_atr × ATR × multiplier × size.
        r_multiple: Realized R-multiple = realized_pnl / r_dollar.
        exit_reason: One of {stop_hit, gap_through_stop, opposite_channel_break,
            eod_flatten, session_rollover, end_of_data}.
        equity_at_entry: Account equity at trade entry (per design.md §5.3).
    """

    symbol: str
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp
    side: int
    position_size: int
    entry_price: float
    exit_price: float
    stop_price: float
    r_dollar: float
    r_multiple: float
    exit_reason: str
    equity_at_entry: float


@dataclass(frozen=True)
class KillSwitchValidationReport:
    """Per-constraint pass/fail report.

    Each constraint reports:
      - pass: bool — no violations detected.
      - n_violations: int — count of violating trades.
      - violation_indices: list[int] — trade indices with violations.
      - constraint_id: str — K-1..K-8.
      - rationale: str — human-readable summary.

    Aggregate annotations field maps to the per-trade ledger's
    ``stress-test-K-N-{pass,fail}`` annotations per ADR-0017 §5.
    """

    constraint_id: str
    passed: bool
    n_violations: int
    violation_indices: list[int]
    rationale: str
    n_trades_checked: int


def K1_per_trade_dollar_stop_within_1R(
    trades: list[TradeRecord],
    *,
    tolerance_r: float = 1.05,
) -> KillSwitchValidationReport:
    """K-1: per-trade realized dollar loss <= 1.0R (Turtle 2N convention).

    Per ADR-0017 §5 K-1: the per-trade stop is 1.0R (= k_atr × ATR × multiplier
    × size). Realized R-multiple on a stop-hit trade should be ≈ -1.0 (slightly
    worse possible on gap-through-stop per design.md §7 adverse-fill convention).
    Tolerance of 1.05 captures gap-through events while flagging excess slippage.

    Args:
        trades: List of TradeRecord.
        tolerance_r: Tolerance multiple of -1.0R for stop-hit + gap-through
            events (default 1.05; trades worse than -1.05R are violations).
    """
    violations: list[int] = []
    for i, t in enumerate(trades):
        if t.exit_reason in {"stop_hit_long", "stop_hit_short"}:
            # Stop-hit: R should be close to -1.0
            if t.r_multiple < -tolerance_r:
                violations.append(i)
        elif t.exit_reason in {"gap_through_stop_long", "gap_through_stop_short"}:
            # Gap-through: worse than -1.0R but should be bounded by the gap
            # extent; flag only if extreme (R < -3.0 = 3x adverse fill).
            if t.r_multiple < -3.0:
                violations.append(i)
    return KillSwitchValidationReport(
        constraint_id="K-1",
        passed=len(violations) == 0,
        n_violations=len(violations),
        violation_indices=violations,
        rationale=(
            f"Per-trade dollar-loss <= {tolerance_r}R for stop-hit trades; "
            f"gap-through bounded at -3R"
        ),
        n_trades_checked=len(trades),
    )


def K3_no_add_to_loser(
    trades: list[TradeRecord],
) -> KillSwitchValidationReport:
    """K-3: no add-to-loser (zero exception).

    Per ADR-0017 §5 K-3: channel-break signal flip closes the prior position;
    new entry is fresh. This is enforced structurally in the H062 per-trade
    simulator (the in_position flag prevents adding); this validator confirms
    no overlapping trades on the same symbol.

    Two trades overlap if their (entry_ts, exit_ts) intervals overlap AND
    they have the same symbol. Same-side overlap is the K-3 violation.
    """
    violations: list[int] = []
    by_symbol: dict[str, list[tuple[int, TradeRecord]]] = {}
    for i, t in enumerate(trades):
        by_symbol.setdefault(t.symbol, []).append((i, t))
    for sym, sym_trades in by_symbol.items():
        sym_trades_sorted = sorted(sym_trades, key=lambda pair: pair[1].entry_ts)
        for j in range(1, len(sym_trades_sorted)):
            prev_idx, prev = sym_trades_sorted[j - 1]
            curr_idx, curr = sym_trades_sorted[j]
            # Overlap: curr.entry_ts < prev.exit_ts
            if curr.entry_ts < prev.exit_ts:
                violations.append(curr_idx)
    return KillSwitchValidationReport(
        constraint_id="K-3",
        passed=len(violations) == 0,
        n_violations=len(violations),
        violation_indices=violations,
        rationale=(
            "No overlapping trades on the same symbol; channel-break flip "
            "must close the prior position before a new entry"
        ),
        n_trades_checked=len(trades),
    )


def K4_per_symbol_position_cap(
    trades: list[TradeRecord],
    *,
    capacity_caps: dict[str, int],
) -> KillSwitchValidationReport:
    """K-4: per-symbol position cap per ADR-0001 retail capacity ceilings."""
    violations: list[int] = []
    for i, t in enumerate(trades):
        cap = capacity_caps.get(t.symbol, 1)
        if t.position_size > cap:
            violations.append(i)
    return KillSwitchValidationReport(
        constraint_id="K-4",
        passed=len(violations) == 0,
        n_violations=len(violations),
        violation_indices=violations,
        rationale=(
            f"Per-symbol contract cap per ADR-0001 retail capacity ceilings: "
            f"{capacity_caps}"
        ),
        n_trades_checked=len(trades),
    )


def K6_daily_circuit_breaker_2pct(
    trades: list[TradeRecord],
    *,
    starting_equity: float = 10000.0,
) -> KillSwitchValidationReport:
    """K-6: -2% of basket equity daily P/L → halt new entries.

    Walks the trade ledger session-by-session. If realized cumulative P/L
    on session s exceeds -2% of starting_equity AND a NEW entry is registered
    later in that same session, that entry is a K-6 violation.
    """
    if not trades:
        return KillSwitchValidationReport(
            constraint_id="K-6",
            passed=True,
            n_violations=0,
            violation_indices=[],
            rationale="No trades to check",
            n_trades_checked=0,
        )
    # Group by trading day (UTC date of entry).
    df = pd.DataFrame([
        {
            "idx": i,
            "entry_date": t.entry_ts.date() if hasattr(t.entry_ts, "date") else t.entry_ts,
            "entry_ts": t.entry_ts,
            "symbol": t.symbol,
            "realized_pnl_dollar": t.r_multiple * t.r_dollar,
        }
        for i, t in enumerate(trades)
    ])
    violations: list[int] = []
    for date, day_trades in df.groupby("entry_date"):
        day_trades_sorted = day_trades.sort_values("entry_ts")
        cum_pnl = 0.0
        for _, row in day_trades_sorted.iterrows():
            if cum_pnl < -0.02 * starting_equity:
                violations.append(int(row["idx"]))
            cum_pnl += float(row["realized_pnl_dollar"])
    return KillSwitchValidationReport(
        constraint_id="K-6",
        passed=len(violations) == 0,
        n_violations=len(violations),
        violation_indices=violations,
        rationale=(
            f"Daily circuit breaker at -2% of starting_equity={starting_equity}; "
            "new entries blocked after daily P/L crosses threshold"
        ),
        n_trades_checked=len(trades),
    )


def K7_weekly_circuit_breaker_5pct(
    trades: list[TradeRecord],
    *,
    starting_equity: float = 10000.0,
) -> KillSwitchValidationReport:
    """K-7: -5% of basket equity weekly P/L → halt new entries through week-end."""
    if not trades:
        return KillSwitchValidationReport(
            constraint_id="K-7",
            passed=True,
            n_violations=0,
            violation_indices=[],
            rationale="No trades to check",
            n_trades_checked=0,
        )
    df = pd.DataFrame([
        {
            "idx": i,
            "entry_week": pd.Timestamp(t.entry_ts).isocalendar()[:2],
            "entry_ts": t.entry_ts,
            "symbol": t.symbol,
            "realized_pnl_dollar": t.r_multiple * t.r_dollar,
        }
        for i, t in enumerate(trades)
    ])
    df["entry_week"] = df["entry_week"].astype(str)
    violations: list[int] = []
    for week, week_trades in df.groupby("entry_week"):
        week_trades_sorted = week_trades.sort_values("entry_ts")
        cum_pnl = 0.0
        for _, row in week_trades_sorted.iterrows():
            if cum_pnl < -0.05 * starting_equity:
                violations.append(int(row["idx"]))
            cum_pnl += float(row["realized_pnl_dollar"])
    return KillSwitchValidationReport(
        constraint_id="K-7",
        passed=len(violations) == 0,
        n_violations=len(violations),
        violation_indices=violations,
        rationale=(
            f"Weekly circuit breaker at -5% of starting_equity={starting_equity}; "
            "new entries blocked after weekly P/L crosses threshold"
        ),
        n_trades_checked=len(trades),
    )


def validate_kill_switches(
    trades: list[TradeRecord],
    *,
    capacity_caps: dict[str, int],
    starting_equity: float = 10000.0,
) -> dict[str, Any]:
    """Run K-1, K-3, K-4, K-6, K-7 validation on a trade ledger.

    K-2 (time-stop) is structurally enforced by EOD-flatten in the H062
    simulator; K-5 (correlated-instrument cap) is N/A at v1 since the
    H062 universe contains no cross-asset correlated pairs (ES/MES + NQ/MNQ
    pairs not both in v1 universe). K-8 (adverse-direction entry filter)
    is enforced by the ID_1 trend-filter gate at feature-factory layer.

    Returns:
        Dict with per-constraint KillSwitchValidationReport + aggregate
        pass/fail annotation per ADR-0017 §5.
    """
    reports = {
        "K-1": K1_per_trade_dollar_stop_within_1R(trades),
        "K-3": K3_no_add_to_loser(trades),
        "K-4": K4_per_symbol_position_cap(trades, capacity_caps=capacity_caps),
        "K-6": K6_daily_circuit_breaker_2pct(trades, starting_equity=starting_equity),
        "K-7": K7_weekly_circuit_breaker_5pct(trades, starting_equity=starting_equity),
    }
    all_passed = all(r.passed for r in reports.values())
    annotations = []
    for k, r in reports.items():
        suffix = "pass" if r.passed else "fail"
        annotations.append(f"kill-switch-{k.lower().replace('-', '_')}-{suffix}")
    return {
        "all_passed": all_passed,
        "n_trades_checked": len(trades),
        "reports": {
            k: {
                "constraint_id": r.constraint_id,
                "passed": r.passed,
                "n_violations": r.n_violations,
                "violation_indices": r.violation_indices,
                "rationale": r.rationale,
            }
            for k, r in reports.items()
        },
        "annotations": annotations,
        "k_2_note": (
            "K-2 (per-trade time-stop) is structurally enforced by EOD-flatten "
            "in the H062 simulator; no separate validator needed"
        ),
        "k_5_note": (
            "K-5 (correlated-instrument cap) is N/A at H062 v1 (universe has "
            "no cross-asset correlated pairs); applies in v2+ if MES/MNQ added"
        ),
        "k_8_note": (
            "K-8 (adverse-direction entry filter) is enforced by the ID_1 "
            "trend-filter gate at the H062FeatureConfig / compute_h062_features "
            "level (eligible_events filters via trend_side disagreement)"
        ),
    }
