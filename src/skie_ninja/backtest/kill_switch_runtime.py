"""Runtime kill-switch intervention per ADR-0025 §D-1.

Parallel to [kill_switch_validation.py](kill_switch_validation.py) (post-hoc
validator); this module hooks INTO the per-trade simulator to prevent K-3 / K-4
/ K-6 / K-7 violations at the entry layer. Shared K-1..K-8 thresholds + the
canonical CME session-clock function via the shared-constants module
[kill_switch_constants.py](kill_switch_constants.py).

Coverage at v1:
  - K-3: no add-to-loser (no overlapping same-symbol trades regardless of side).
  - K-4: per-symbol capacity cap per ADR-0001 retail capacity ceilings.
  - K-6: daily circuit breaker = -2% of equity_at_session_start (current-equity
    ratcheting per ADR-0025 §D-1 F-1-7 audit fix).
  - K-7: weekly circuit breaker = -5% of equity_at_week_start.

K-1 / K-2 / K-5 / K-8 are structurally enforced elsewhere (K-1 via the 1R stop
math; K-2 via EOD-flatten; K-5 N/A at the 4-symbol baskets — extension required
for H061-class baskets per `P1-KILL-SWITCH-RUNTIME-K5-CORRELATED-EXTEND`; K-8
via trend-filter gate).

Per ADR-0024 §D-2 the K-1..K-8 constraints are opt-in (not mandatory inheritance);
hypotheses invoke this module by passing a `KillSwitchRuntimeConfig` to the
per-trade simulator. KPI report card disclosure per ADR-0025 §D-5:
`kill-switch-active` if any K-N hook fired during simulation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any

import pandas as pd

from skie_ninja.backtest.kill_switch_constants import (
    K5_CORRELATED_PAIRS,
    K6_DAILY_DRAWDOWN_THRESHOLD,
    K7_WEEKLY_DRAWDOWN_THRESHOLD,
    iso_week_id_from_session_date,
    session_date_from_timestamp,
)

__all__ = [
    "KillSwitchRuntimeConfig",
    "KillSwitchRuntimeState",
    "OpenPositionRecord",
    "check_entry_blocked",
    "init_runtime_state",
    "update_state_on_open",
    "update_state_on_close",
    "advance_session",
    "advance_week",
    "validate_universe_for_k5",
    "summarize_trigger_counts",
]

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KillSwitchRuntimeConfig:
    """Opt-in per-constraint toggle per hypothesis design.md §11.1.

    All four K-N flags default to False. Operator declares which constraints
    the strategy invokes by passing `enable_k_N=True`; the runtime intervenes
    only on enabled constraints (KPI annotation `kill-switch-active` covers
    any subset of fired constraints).
    """

    enable_k3: bool = False
    enable_k4: bool = False
    enable_k6: bool = False
    enable_k7: bool = False
    capacity_caps: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class OpenPositionRecord:
    """Per-symbol open-position state required for K-3 enforcement.

    Per ADR-0025 §D-1 F-1-2 audit fix, K-3 enforcement requires knowing whether
    a position is already open on a symbol (regardless of side). This record
    is created in `update_state_on_open` and cleared in `update_state_on_close`.
    """

    symbol: str
    side: int
    entry_ts: pd.Timestamp
    entry_price: float
    position_size: int
    stop_price: float
    r_dollar: float


@dataclass(frozen=True)
class KillSwitchRuntimeState:
    """Immutable runtime state passed by reference through the per-trade sim.

    Fields:
        open_position_by_symbol: dict[symbol, OpenPositionRecord]; populated
            by update_state_on_open, cleared by update_state_on_close.
        daily_pnl_by_session_date: dict[CME session-date, cumulative-dollar-pnl];
            session-date computed via `session_date_from_timestamp` per the
            shared-constants module.
        weekly_pnl_by_week_id: dict[(iso_year, iso_week) of CME session-date,
            cumulative-dollar-pnl].
        current_session_date: CME session-date for the bar currently being
            processed; updated by `advance_session`.
        current_week_id: ISO-week tuple for the current session-date.
        equity_at_session_start: account equity at the start of the current
            CME session; recorded by `advance_session` and used as the K-6
            threshold denominator.
        equity_at_week_start: account equity at the start of the current ISO-
            week; recorded by `advance_week` and used as the K-7 threshold
            denominator.
        trigger_counts: dict[K-N constraint id, fire-count] for sidecar emission.
        universe: list of symbols in the active basket; validated at init for
            K-5 correlated-pair membership per F-1-6 audit fix.
    """

    open_position_by_symbol: dict[str, OpenPositionRecord]
    daily_pnl_by_session_date: dict[date, float]
    weekly_pnl_by_week_id: dict[tuple[int, int], float]
    current_session_date: date | None
    current_week_id: tuple[int, int] | None
    equity_at_session_start: float
    equity_at_week_start: float
    trigger_counts: dict[str, int]
    universe: tuple[str, ...]


def validate_universe_for_k5(universe: tuple[str, ...]) -> None:
    """Raise ValueError if `universe` contains any ADR-0017 §5 K-5 pair.

    Per ADR-0025 §D-1 F-1-6 audit fix, K-5 N/A is universe-conditional. The
    4-symbol baskets {ES, NQ, MGC, SIL} are clean (no correlated pairs); the
    future H061 universe adding full-size CL alongside MCL would trigger this
    guard. Tracked under `P1-KILL-SWITCH-RUNTIME-K5-CORRELATED-EXTEND`
    BLOCKING-BEFORE-H061-PROD-RUN.
    """
    symbols = frozenset(s.upper() for s in universe)
    for pair in K5_CORRELATED_PAIRS:
        if pair.issubset(symbols):
            raise ValueError(
                f"Kill-switch runtime universe {sorted(symbols)} contains "
                f"correlated pair {sorted(pair)} per ADR-0017 §5 K-5 taxonomy; "
                f"K-5 runtime coverage required (P1-KILL-SWITCH-RUNTIME-K5-CORRELATED-EXTEND)."
            )


def init_runtime_state(
    *,
    universe: tuple[str, ...],
    starting_equity: float,
) -> KillSwitchRuntimeState:
    """Initialise runtime state for a new simulation."""
    validate_universe_for_k5(universe)
    return KillSwitchRuntimeState(
        open_position_by_symbol={},
        daily_pnl_by_session_date={},
        weekly_pnl_by_week_id={},
        current_session_date=None,
        current_week_id=None,
        equity_at_session_start=float(starting_equity),
        equity_at_week_start=float(starting_equity),
        trigger_counts={"K-3": 0, "K-4": 0, "K-6": 0, "K-7": 0},
        universe=tuple(s.upper() for s in universe),
    )


def advance_session(
    state: KillSwitchRuntimeState,
    *,
    new_session_date: date,
    current_equity: float,
) -> KillSwitchRuntimeState:
    """Record session-start equity + reset daily accumulator on session-boundary."""
    new_daily = dict(state.daily_pnl_by_session_date)
    new_daily.setdefault(new_session_date, 0.0)
    return replace(
        state,
        current_session_date=new_session_date,
        equity_at_session_start=float(current_equity),
        daily_pnl_by_session_date=new_daily,
    )


def advance_week(
    state: KillSwitchRuntimeState,
    *,
    new_week_id: tuple[int, int],
    current_equity: float,
) -> KillSwitchRuntimeState:
    """Record week-start equity + reset weekly accumulator on ISO-week boundary."""
    new_weekly = dict(state.weekly_pnl_by_week_id)
    new_weekly.setdefault(new_week_id, 0.0)
    return replace(
        state,
        current_week_id=new_week_id,
        equity_at_week_start=float(current_equity),
        weekly_pnl_by_week_id=new_weekly,
    )


def check_entry_blocked(
    state: KillSwitchRuntimeState,
    config: KillSwitchRuntimeConfig,
    *,
    symbol: str,
    position_size: int,
) -> tuple[bool, str | None]:
    """Return (blocked, reason); orchestrator skips the entry if blocked.

    Order of K-N checks: K-3 (existing open position) → K-4 (capacity cap) →
    K-6 (daily breaker) → K-7 (weekly breaker). The first-firing constraint
    short-circuits; only its trigger is recorded.
    """
    sym = symbol.upper()

    if config.enable_k3 and sym in state.open_position_by_symbol:
        return True, "K-3"

    if config.enable_k4:
        cap = config.capacity_caps.get(sym, 1)
        if position_size > cap:
            return True, "K-4"

    if config.enable_k6 and state.current_session_date is not None:
        daily_pnl = state.daily_pnl_by_session_date.get(state.current_session_date, 0.0)
        # justify: K6_DAILY_DRAWDOWN_THRESHOLD = -0.02 per ADR-0017 §5 K-6 +
        # ADR-0025 §D-1 F-1-7 current-equity-ratcheting fix; threshold ratchets
        # with equity_at_session_start (NOT starting_equity).
        if daily_pnl < K6_DAILY_DRAWDOWN_THRESHOLD * state.equity_at_session_start:
            return True, "K-6"

    if config.enable_k7 and state.current_week_id is not None:
        weekly_pnl = state.weekly_pnl_by_week_id.get(state.current_week_id, 0.0)
        # justify: K7_WEEKLY_DRAWDOWN_THRESHOLD = -0.05 per ADR-0017 §5 K-7.
        if weekly_pnl < K7_WEEKLY_DRAWDOWN_THRESHOLD * state.equity_at_week_start:
            return True, "K-7"

    return False, None


def update_state_on_open(
    state: KillSwitchRuntimeState,
    *,
    symbol: str,
    side: int,
    entry_ts: pd.Timestamp,
    entry_price: float,
    position_size: int,
    stop_price: float,
    r_dollar: float,
) -> KillSwitchRuntimeState:
    """Register an open position; required for K-3 enforcement."""
    sym = symbol.upper()
    new_open = dict(state.open_position_by_symbol)
    new_open[sym] = OpenPositionRecord(
        symbol=sym,
        side=int(side),
        entry_ts=entry_ts,
        entry_price=float(entry_price),
        position_size=int(position_size),
        stop_price=float(stop_price),
        r_dollar=float(r_dollar),
    )
    return replace(state, open_position_by_symbol=new_open)


def update_state_on_close(
    state: KillSwitchRuntimeState,
    *,
    symbol: str,
    realized_pnl_dollar: float,
    exit_ts: pd.Timestamp,
) -> KillSwitchRuntimeState:
    """Clear open-position record + update daily / weekly P/L accumulators.

    The session-date + week-id of the exit timestamp are computed via the
    canonical CME session-clock; if the trade exits on a different CME session-
    date than where it opened, the realized P/L is attributed to the EXIT
    session per the existing post-hoc validator semantic.
    """
    sym = symbol.upper()
    new_open = dict(state.open_position_by_symbol)
    new_open.pop(sym, None)

    exit_session_date = session_date_from_timestamp(exit_ts)
    exit_week_id = iso_week_id_from_session_date(exit_session_date)

    new_daily = dict(state.daily_pnl_by_session_date)
    new_daily[exit_session_date] = (
        new_daily.get(exit_session_date, 0.0) + float(realized_pnl_dollar)
    )
    new_weekly = dict(state.weekly_pnl_by_week_id)
    new_weekly[exit_week_id] = (
        new_weekly.get(exit_week_id, 0.0) + float(realized_pnl_dollar)
    )

    return replace(
        state,
        open_position_by_symbol=new_open,
        daily_pnl_by_session_date=new_daily,
        weekly_pnl_by_week_id=new_weekly,
    )


def record_trigger(
    state: KillSwitchRuntimeState, constraint_id: str
) -> KillSwitchRuntimeState:
    """Increment trigger_counts[constraint_id] for sidecar emission."""
    new_counts = dict(state.trigger_counts)
    new_counts[constraint_id] = new_counts.get(constraint_id, 0) + 1
    return replace(state, trigger_counts=new_counts)


def summarize_trigger_counts(state: KillSwitchRuntimeState) -> dict[str, Any]:
    """Provenance summary for sidecar / KPI annotation per ADR-0025 §D-5."""
    total = sum(state.trigger_counts.values())
    return {
        "runtime_active": total > 0,
        "trigger_counts": dict(state.trigger_counts),
        "total_triggers": total,
        "annotation": "kill-switch-active" if total > 0 else "kill-switch-inactive",
    }
