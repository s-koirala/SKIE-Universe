"""Kill-switch backtest validation canaries per ADR-0017 §5 + Cycle-4
leak-canary discipline (`P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`).

Validates K-1..K-8 hard kill-switch constraints against a per-fold strategy
trade ledger. Designed to be called from the walk-forward orchestrator's
post-fold hook (analogous to the Cycle-4 `assert_fold_boundary_invariant`
leak canary at [src/skie_ninja/backtest/leak_canaries.py](leak_canaries.py)).

Coverage at this layer:

| K-N | Validator | Status |
|---|---|---|
| K-1 | `validate_k1_per_trade_stop` | full (r_value floor) |
| K-2 | `validate_k2_per_trade_time_stop` | full (close - open vs threshold) |
| K-3 | `validate_k3_no_add_to_loser` | conservative (overlapping same-direction positions; ledger lacks per-tick mark-to-market for the strict "while in unrealized loss" check) |
| K-4 | `validate_k4_per_symbol_position_cap` | full (max position_size per instrument) |
| K-5 | `validate_k5_correlated_inventory_cap` | full (running peak group $-notional) |
| K-6 | `validate_k6_daily_circuit_breaker` | full (replay equity simulator; halts match) |
| K-7 | `validate_k7_weekly_circuit_breaker` | full (same; weekly aggregation) |
| K-8 | `validate_k8_adverse_direction_filter` | full (T_H sign + adverse-move predicate) |

Output: a `KillSwitchCanaryResult` per-fold with per-K pass/fail + offending
trade indices + summary annotation `kill-switch-canary-{pass,fail}` per
ADR-0017 §5. The annotation is recorded in the per-fold ReproLog and
surfaces in the KPI report card §"Methodological-correctness annotations"
per ADR-0014 §3.2 row 9.

Per ADR-0013 §1+§2, kill-switch-canary annotations are NOT binding gates;
operator-discretionary review at promotion time decides remediation timing.

Implementation per `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §5).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from skie_ninja.backtest.stress_test import (
    KillSwitchParams,
    TradeEvent,
    simulate_equity_with_kill_switches,
)

__all__ = [
    "KillSwitchCanaryResult",
    "TradeLedgerEntry",
    "validate_k1_per_trade_stop",
    "validate_k2_per_trade_time_stop",
    "validate_k3_no_add_to_loser",
    "validate_k4_per_symbol_position_cap",
    "validate_k5_correlated_inventory_cap",
    "validate_k6_daily_circuit_breaker",
    "validate_k7_weekly_circuit_breaker",
    "validate_k8_adverse_direction_filter",
    "validate_kill_switches_per_fold",
]


@dataclass(frozen=True)
class TradeLedgerEntry:
    """One executed trade in a per-fold strategy ledger.

    Fields needed for K-1..K-8 validation. Strategies that lack metadata for
    a particular K-N can pass `None`; the corresponding validator either
    emits a `metadata-deferred` annotation OR (for K-1, K-4, K-6, K-7 where
    the metadata is required) raises ValueError.

    Args:
        instrument: Instrument symbol (e.g., "ES", "MES", "NQ", "MNQ").
        session_id: Integer session/day index (calendar date as int).
        week_id: Integer week index.
        open_timestamp_ns: Trade-open timestamp (UTC ns) — for K-2.
        close_timestamp_ns: Trade-close timestamp (UTC ns) — for K-2 + K-3.
        r_value: Realized R-multiple (post-K-1-floor + post-cost).
        position_size: Number of contracts (positive integer; signed direction
            in `position_direction`).
        position_direction: +1 (long) or -1 (short).
        entry_bar_open_price: Price at the open of the entry bar — for K-8.
        fill_price: Realized entry fill price — for K-8.
        atr_at_entry: ATR_n at entry time — for K-8 adverse-move predicate.
        multiplier: Dollar multiplier per contract (e.g., 50 for ES, 5 for MES).
        correlated_group: Correlated-instrument group key (e.g., "ES_MES",
            "NQ_MNQ"); None if standalone.
        trigger_t_h_sign: Higher-TF trend gate sign at entry: +1, 0, -1; None
            if K-8 not applicable to this strategy.
    """

    instrument: str
    session_id: int
    week_id: int
    open_timestamp_ns: int
    close_timestamp_ns: int
    r_value: float
    position_size: int
    position_direction: int
    entry_bar_open_price: float
    fill_price: float
    atr_at_entry: float
    multiplier: float
    correlated_group: str | None = None
    trigger_t_h_sign: int | None = None


@dataclass(frozen=True)
class KillSwitchCanaryResult:
    """Per-fold kill-switch canary result.

    Fields:
        fold_id: The fold identifier.
        per_K_passed: Mapping K-N → bool indicating whether that K-N passed
            (defaults to True for deferred / n/a K-N — read in conjunction with
            `per_K_validated`).
        per_K_validated: Mapping K-N → bool indicating whether that K-N was
            actually validated (False for `deferred-...` or `n/a-...` metadata
            states). Round-1 audit Q-3 fix.
        per_K_violations: Mapping K-N → tuple of trade indices that violate.
        per_K_metadata: Mapping K-N → str diagnostic (e.g., "validated",
            "deferred-no-per_trade_time_stop_min-supplied",
            "n/a-no-trigger_t_h_sign-metadata").
        all_passed: True iff every K-N passed (does NOT distinguish validated
            vs deferred — see annotation grammar).
        annotation: 3-state grammar per Round-1 audit Q-3 fix:
            - "kill-switch-canary-pass": every K-N validated AND passed
            - "kill-switch-canary-fail": at least one validated K-N failed
            - "kill-switch-canary-partial": no K-N failed, but at least one
              K-N was deferred / n/a (the strategy's metadata is incomplete
              for full K-1..K-8 coverage; report card §Methodological-correctness
              annotations row 9 should display the per_K_validated map alongside
              the partial annotation per ADR-0014 §3.2).
    """

    fold_id: int
    per_K_passed: dict[str, bool]
    per_K_validated: dict[str, bool]
    per_K_violations: dict[str, tuple[int, ...]]
    per_K_metadata: dict[str, str]
    all_passed: bool
    annotation: str
    extra: dict[str, Any] = field(default_factory=dict)


def validate_k1_per_trade_stop(
    ledger: Sequence[TradeLedgerEntry],
    *,
    kill_switch_params: KillSwitchParams,
    tolerance: float = 1e-6,
) -> tuple[bool, tuple[int, ...]]:
    """Validate K-1 per-trade $-stop: every trade's r_value >= -per_trade_stop_r.

    Returns (passed, violation_indices).
    """
    floor = -kill_switch_params.per_trade_stop_r - tolerance
    violations = tuple(
        i for i, entry in enumerate(ledger) if entry.r_value < floor
    )
    return (not violations, violations)


def validate_k2_per_trade_time_stop(
    ledger: Sequence[TradeLedgerEntry],
    *,
    per_trade_time_stop_min: float,
    tolerance_ns: int = 60_000_000_000,  # 60 seconds in ns
) -> tuple[bool, tuple[int, ...]]:
    """Validate K-2 per-trade time-stop: every trade's duration <= per_trade_time_stop_min.

    Tolerance allows for end-of-bar fill rounding (default 60 seconds).
    Winning trades are exempt (the time-stop is a losing-trade truncation per
    ADR-0017 §5 K-2: "mechanical inverse of avg_losing_time = 3.65×
    avg_winning_time"); this validator therefore only checks losing trades.

    Returns (passed, violation_indices).
    """
    threshold_ns = int(per_trade_time_stop_min * 60 * 1_000_000_000) + tolerance_ns
    violations = tuple(
        i
        for i, entry in enumerate(ledger)
        if entry.r_value < 0.0
        and (entry.close_timestamp_ns - entry.open_timestamp_ns) > threshold_ns
    )
    return (not violations, violations)


def validate_k3_no_add_to_loser(
    ledger: Sequence[TradeLedgerEntry],
) -> tuple[bool, tuple[int, ...]]:
    """Validate K-3 no-add-to-loser: no second entry on same instrument while
    a position is open.

    Conservative implementation: flags any pair of trades on the same
    instrument whose temporal intervals overlap (open_a < open_b < close_a)
    with the same direction. This is stricter than the spec's "while in
    unrealized loss" — without per-tick mark-to-market data, we cannot
    distinguish "added to loser" from "added to winner" purely from the
    ledger. The strict-overlap-same-direction approximation flags both
    cases; a follow-up `P1-K3-MARK-TO-MARKET-AWARE-VALIDATOR` will refine
    this once the orchestrator emits per-trade peak-unrealized-PnL metadata.

    Returns (passed, violation_indices).
    """
    by_instrument: dict[str, list[tuple[int, TradeLedgerEntry]]] = {}
    for i, entry in enumerate(ledger):
        by_instrument.setdefault(entry.instrument, []).append((i, entry))

    violations: list[int] = []
    for trades in by_instrument.values():
        trades_sorted = sorted(trades, key=lambda t: t[1].open_timestamp_ns)
        for j in range(len(trades_sorted)):
            for k in range(j + 1, len(trades_sorted)):
                idx_j, entry_j = trades_sorted[j]
                idx_k, entry_k = trades_sorted[k]
                if entry_k.open_timestamp_ns >= entry_j.close_timestamp_ns:
                    break
                if entry_j.position_direction == entry_k.position_direction:
                    violations.append(idx_k)
    return (not violations, tuple(sorted(set(violations))))


def validate_k4_per_symbol_position_cap(
    ledger: Sequence[TradeLedgerEntry],
    *,
    per_symbol_caps: dict[str, int],
) -> tuple[bool, tuple[int, ...]]:
    """Validate K-4 per-symbol position cap: running portfolio position per
    instrument never exceeds the cap.

    Per Round-1 audit Q-4 fix: the cap is a portfolio-wide running limit
    ("≤ 20 ES contracts at any one time" per ADR-0001 + CLAUDE.md §Standing
    constraints + H055 §11.1), NOT a per-trade max. Two overlapping ES trades
    of 10 + 15 contracts each = 25 running portfolio position violates K-4
    even though each individual trade is within the cap.

    Walks open/close events sorted by timestamp per instrument; tracks running
    |position|; flags any open event that pushes the running position above
    the cap.

    Per ADR-0001 retail capacity ceiling: defaults {"ES": 20, "NQ": 40,
    "MES": 200, "MNQ": 400} per CLAUDE.md §Standing constraints + H055 §11.1
    line 310 (the canonical numeric source).

    Returns (passed, violation_indices).
    """
    by_instrument: dict[str, list[tuple[int, TradeLedgerEntry]]] = {}
    for i, entry in enumerate(ledger):
        if entry.instrument not in per_symbol_caps:
            continue
        by_instrument.setdefault(entry.instrument, []).append((i, entry))

    violations: list[int] = []
    for instrument, instrument_trades in by_instrument.items():
        cap = per_symbol_caps[instrument]
        events: list[tuple[int, str, int, int]] = []
        for idx, entry in instrument_trades:
            size = abs(entry.position_size)
            events.append((entry.open_timestamp_ns, "open", idx, size))
            events.append((entry.close_timestamp_ns, "close", idx, size))
        # Process closes before opens at the same timestamp so a close-and-
        # immediately-reopen pattern doesn't double-count.
        events.sort(key=lambda x: (x[0], 0 if x[1] == "close" else 1))

        running = 0
        for _, kind, idx, size in events:
            if kind == "open":
                running += size
                if running > cap:
                    violations.append(idx)
            else:
                running -= size
    return (not violations, tuple(sorted(set(violations))))


def validate_k5_correlated_inventory_cap(
    ledger: Sequence[TradeLedgerEntry],
    *,
    correlated_group_caps: dict[str, float],
) -> tuple[bool, tuple[int, ...]]:
    """Validate K-5 correlated-instrument inventory cap: aggregate per-group
    $-notional ≤ cap.

    Computes the running peak $-notional within each correlated group across
    overlapping trade intervals. ADR-0017 §5 K-5: "ES+MES share a budget;
    NQ+MNQ share a budget; aggregate per-group $-notional ≤ 1.0× the largest
    single-symbol cap in the group". Caller passes the cap dict keyed on the
    correlated_group field.

    The notional per trade is `|position_size| × multiplier × fill_price`.
    For overlapping trades within a group, the peak concurrent notional is
    flagged against the cap.

    Returns (passed, violation_indices) where violation_indices are the
    trade-indices whose entry pushed the running group notional above cap.
    """
    by_group: dict[str, list[tuple[int, TradeLedgerEntry]]] = {}
    for i, entry in enumerate(ledger):
        if entry.correlated_group is None:
            continue
        by_group.setdefault(entry.correlated_group, []).append((i, entry))

    violations: list[int] = []
    for group, group_trades in by_group.items():
        cap = correlated_group_caps.get(group)
        if cap is None:
            continue
        events: list[tuple[int, str, int, float]] = []
        for idx, entry in group_trades:
            notional = abs(entry.position_size) * entry.multiplier * entry.fill_price
            events.append((entry.open_timestamp_ns, "open", idx, notional))
            events.append((entry.close_timestamp_ns, "close", idx, notional))
        events.sort(key=lambda x: (x[0], 0 if x[1] == "close" else 1))

        running = 0.0
        for _, kind, idx, notional in events:
            if kind == "open":
                running += notional
                if running > cap:
                    violations.append(idx)
            else:
                running -= notional
    return (not violations, tuple(sorted(set(violations))))


def _ledger_to_trade_events(
    ledger: Sequence[TradeLedgerEntry],
) -> list[TradeEvent]:
    return [
        TradeEvent(
            r_value=entry.r_value,
            session_id=entry.session_id,
            week_id=entry.week_id,
        )
        for entry in ledger
    ]


def validate_k6_daily_circuit_breaker(
    ledger: Sequence[TradeLedgerEntry],
    *,
    kill_switch_params: KillSwitchParams,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
) -> tuple[bool, tuple[int, ...]]:
    """Validate K-6 daily circuit breaker: no trade should execute on a session
    after it has crossed the daily circuit-breaker threshold.

    Replays the per-trade R-multiple sequence through the equity simulator;
    violations are exactly the simulator's `skipped_trade_indices` filtered to
    daily (K-6) halts. The simulator halts AT the breaching trade — that
    trade's PnL is realised; only trades AFTER the breach are skipped and
    recorded as violations (Round-1 audit Q-1 fix: the prior "first-encounter"
    heuristic flagged pre-halt trades as false positives).

    Returns (passed, violation_indices) where violation_indices are the
    ledger positions whose execution should not have occurred (post-halt).
    """
    trades = _ledger_to_trade_events(ledger)
    sim = simulate_equity_with_kill_switches(
        trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=kill_switch_params,
    )
    halted_session_set = set(sim.halted_sessions)
    if not halted_session_set:
        return (True, ())
    halted_week_set = set(sim.halted_weeks)
    violations = tuple(
        i
        for i in sim.skipped_trade_indices
        if ledger[i].session_id in halted_session_set
        and ledger[i].week_id not in halted_week_set
    )
    daily_only_violations = tuple(
        i for i in sim.skipped_trade_indices
        if ledger[i].session_id in halted_session_set
    ) if not halted_week_set else violations
    return (not daily_only_violations, daily_only_violations)


def validate_k7_weekly_circuit_breaker(
    ledger: Sequence[TradeLedgerEntry],
    *,
    kill_switch_params: KillSwitchParams,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
) -> tuple[bool, tuple[int, ...]]:
    """Validate K-7 weekly circuit breaker: no trade should execute in a week
    after it has crossed the weekly circuit-breaker threshold.

    Same simulator-skipped-indices semantics as K-6 (Round-1 audit Q-2 fix).

    Returns (passed, violation_indices).
    """
    trades = _ledger_to_trade_events(ledger)
    sim = simulate_equity_with_kill_switches(
        trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=kill_switch_params,
    )
    halted_week_set = set(sim.halted_weeks)
    if not halted_week_set:
        return (True, ())
    violations = tuple(
        i for i in sim.skipped_trade_indices
        if ledger[i].week_id in halted_week_set
    )
    return (not violations, violations)


def validate_k8_adverse_direction_filter(
    ledger: Sequence[TradeLedgerEntry],
    *,
    adverse_atr_threshold: float = 0.5,
) -> tuple[bool, tuple[int, ...]]:
    """Validate K-8 adverse-direction entry filter: no entry where the trigger
    bar's higher-TF (T_H) trend gate sign disagrees with the entry direction
    AND price has moved adversely > 0.5 ATR from entry-bar open at fill time.

    Per ADR-0017 §5 K-8 (mechanical inverse of "averaging-down into a falling
    knife" pattern). A trade violates K-8 if BOTH:
      (a) trigger_t_h_sign × position_direction <= 0 (T_H disagrees), AND
      (b) (fill_price - entry_bar_open_price) × position_direction
          / atr_at_entry < -adverse_atr_threshold (adverse > 0.5 ATR).

    Trades with `trigger_t_h_sign=None` are skipped (K-8 not applicable to
    that strategy class).

    Returns (passed, violation_indices).
    """
    violations: list[int] = []
    for i, entry in enumerate(ledger):
        if entry.trigger_t_h_sign is None:
            continue
        if entry.atr_at_entry <= 0.0:
            continue
        condition_a = entry.trigger_t_h_sign * entry.position_direction <= 0
        adverse_move_in_atr = (
            (entry.fill_price - entry.entry_bar_open_price)
            * entry.position_direction
            / entry.atr_at_entry
        )
        condition_b = adverse_move_in_atr < -adverse_atr_threshold
        if condition_a and condition_b:
            violations.append(i)
    return (not violations, tuple(violations))


def validate_kill_switches_per_fold(
    fold_id: int,
    ledger: Sequence[TradeLedgerEntry],
    *,
    kill_switch_params: KillSwitchParams | None = None,
    per_symbol_caps: dict[str, int] | None = None,
    correlated_group_caps: dict[str, float] | None = None,
    per_trade_time_stop_min: float | None = None,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
    adverse_atr_threshold: float = 0.5,
) -> KillSwitchCanaryResult:
    """Run K-1..K-8 validators across a per-fold trade ledger.

    Per ADR-0017 §5 + Cycle-4 leak-canary discipline. Returns a structured
    KillSwitchCanaryResult per-fold with the summary annotation
    `kill-switch-canary-{pass,fail}` for the KPI report card §"Methodological-
    correctness annotations" (ADR-0014 §3.2 row 9).

    Args:
        fold_id: Walk-forward fold identifier.
        ledger: Per-fold trade ledger.
        kill_switch_params: K-1+K-6+K-7 numeric params (defaults to project-
            canonical per ADR-0017 §5).
        per_symbol_caps: K-4 per-instrument position caps (defaults to ADR-0001
            retail capacity ceilings: ES=20, NQ=40, MES=200, MNQ=400).
        correlated_group_caps: K-5 per-group $-notional caps. Optional; if
            absent, K-5 is skipped with metadata "deferred".
        per_trade_time_stop_min: K-2 per-trade time-stop in minutes. Optional;
            if absent, K-2 is skipped with metadata "deferred".
        starting_equity: For K-6 + K-7 simulator replay.
        risk_budget_pct: For K-6 + K-7 simulator replay.
        adverse_atr_threshold: K-8 adverse-move threshold (default 0.5 ATR per
            ADR-0017 §5 K-8).

    Returns:
        KillSwitchCanaryResult with per-K pass/fail + violations + summary
        annotation.
    """
    k = kill_switch_params if kill_switch_params is not None else KillSwitchParams()
    default_caps = {"ES": 20, "NQ": 40, "MES": 200, "MNQ": 400}
    caps = per_symbol_caps if per_symbol_caps is not None else default_caps

    per_K_passed: dict[str, bool] = {}
    per_K_validated: dict[str, bool] = {}
    per_K_violations: dict[str, tuple[int, ...]] = {}
    per_K_metadata: dict[str, str] = {}

    # K-1
    p1, v1 = validate_k1_per_trade_stop(ledger, kill_switch_params=k)
    per_K_passed["K-1"] = p1
    per_K_validated["K-1"] = True
    per_K_violations["K-1"] = v1
    per_K_metadata["K-1"] = "validated"

    # K-2
    if per_trade_time_stop_min is not None:
        p2, v2 = validate_k2_per_trade_time_stop(
            ledger, per_trade_time_stop_min=per_trade_time_stop_min
        )
        per_K_passed["K-2"] = p2
        per_K_validated["K-2"] = True
        per_K_violations["K-2"] = v2
        per_K_metadata["K-2"] = "validated"
    else:
        per_K_passed["K-2"] = True
        per_K_validated["K-2"] = False
        per_K_violations["K-2"] = ()
        per_K_metadata["K-2"] = (
            "deferred-no-per_trade_time_stop_min-supplied"
        )

    # K-3 (conservative)
    p3, v3 = validate_k3_no_add_to_loser(ledger)
    per_K_passed["K-3"] = p3
    per_K_validated["K-3"] = True
    per_K_violations["K-3"] = v3
    per_K_metadata["K-3"] = (
        "conservative-strict-overlap-same-direction-flag"
    )

    # K-4
    p4, v4 = validate_k4_per_symbol_position_cap(ledger, per_symbol_caps=caps)
    per_K_passed["K-4"] = p4
    per_K_validated["K-4"] = True
    per_K_violations["K-4"] = v4
    per_K_metadata["K-4"] = "validated"

    # K-5
    if correlated_group_caps is not None:
        p5, v5 = validate_k5_correlated_inventory_cap(
            ledger, correlated_group_caps=correlated_group_caps
        )
        per_K_passed["K-5"] = p5
        per_K_validated["K-5"] = True
        per_K_violations["K-5"] = v5
        per_K_metadata["K-5"] = "validated"
    else:
        per_K_passed["K-5"] = True
        per_K_validated["K-5"] = False
        per_K_violations["K-5"] = ()
        per_K_metadata["K-5"] = "deferred-no-correlated_group_caps-supplied"

    # K-6
    p6, v6 = validate_k6_daily_circuit_breaker(
        ledger,
        kill_switch_params=k,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
    )
    per_K_passed["K-6"] = p6
    per_K_validated["K-6"] = True
    per_K_violations["K-6"] = v6
    per_K_metadata["K-6"] = "validated"

    # K-7
    p7, v7 = validate_k7_weekly_circuit_breaker(
        ledger,
        kill_switch_params=k,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
    )
    per_K_passed["K-7"] = p7
    per_K_validated["K-7"] = True
    per_K_violations["K-7"] = v7
    per_K_metadata["K-7"] = "validated"

    # K-8
    has_t_h_metadata = any(entry.trigger_t_h_sign is not None for entry in ledger)
    if has_t_h_metadata:
        p8, v8 = validate_k8_adverse_direction_filter(
            ledger, adverse_atr_threshold=adverse_atr_threshold
        )
        per_K_passed["K-8"] = p8
        per_K_validated["K-8"] = True
        per_K_violations["K-8"] = v8
        per_K_metadata["K-8"] = "validated"
    else:
        per_K_passed["K-8"] = True
        per_K_validated["K-8"] = False
        per_K_violations["K-8"] = ()
        per_K_metadata["K-8"] = "n/a-no-trigger_t_h_sign-metadata"

    all_passed = all(per_K_passed.values())
    all_validated = all(per_K_validated.values())
    if not all_passed:
        annotation = "kill-switch-canary-fail"
    elif all_validated:
        annotation = "kill-switch-canary-pass"
    else:
        annotation = "kill-switch-canary-partial"

    return KillSwitchCanaryResult(
        fold_id=fold_id,
        per_K_passed=per_K_passed,
        per_K_validated=per_K_validated,
        per_K_violations=per_K_violations,
        per_K_metadata=per_K_metadata,
        all_passed=all_passed,
        annotation=annotation,
        extra={
            "n_trades": len(ledger),
            "starting_equity": starting_equity,
            "risk_budget_pct": risk_budget_pct,
        },
    )
