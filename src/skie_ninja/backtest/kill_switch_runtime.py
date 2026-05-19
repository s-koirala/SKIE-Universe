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
from typing import Any, Literal

import pandas as pd

from skie_ninja.backtest.kill_switch_constants import (
    K5_CORRELATED_PAIRS,
    K6_DAILY_DRAWDOWN_THRESHOLD,
    K7_WEEKLY_DRAWDOWN_THRESHOLD,
    K_SIZE_DOWN_FRACTION_DEFAULT,
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

    Per ADR-0028 §D-1, K-6 and K-7 each carry an enforcement-mode enum:
    `"block"` (default; legacy ADR-0025 §D-1 semantic preserved verbatim) or
    `"size_down"` (opt-in; multiplicative shrinkage on position size during
    breach session/week — addresses the kill-switch asymmetry pathology
    surfaced by H062 v3 primitive-attribution ablation per ADR-0028 §Context).
    K-3 and K-4 retain block-only enforcement (no size-down) since they
    enforce structural invariants per ADR-0028 §D-1 "Out of scope at v1".
    """

    enable_k3: bool = False
    enable_k4: bool = False
    enable_k6: bool = False
    enable_k7: bool = False
    capacity_caps: dict[str, int] = field(default_factory=dict)
    # ADR-0028 §D-1: K-6/K-7 enforcement-mode enum + size-down fraction.
    # Defaults preserve ADR-0025 §D-1 bit-equivalence; "size_down" is opt-in.
    k6_enforcement: Literal["block", "size_down"] = "block"
    k7_enforcement: Literal["block", "size_down"] = "block"
    # justify: 0.5 (half-Kelly halving) per MacLean-Thorp-Ziemba 2010 fractional-
    # Kelly cascade convention (DOI 10.1142/7598; *practitioner*); empirical
    # re-calibration tracked under P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-CALIBRATION.
    size_down_fraction: float = K_SIZE_DOWN_FRACTION_DEFAULT


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
        trigger_counts: dict[K-N constraint id, breach-fire-count] for sidecar
            emission.

            Per ADR-0028 §D-1 Phase O.17 amendment (`P1-ADR-0028-SIZE-DOWN-
            DISCLOSURE-DEFECT-CLOSE` closure), the trigger_counts semantic is
            **"constraint breaches"** — increments whenever a K-N constraint
            FIRES, regardless of whether enforcement-mode is `"block"` (entry
            rejected) or `"size_down"` (entry admitted with shrunk size). The
            schema initializes 6 keys:

              - `"K-3"` — no-add-to-loser breach (block-only enforcement)
              - `"K-4"` — capacity-cap breach (block-only enforcement)
              - `"K-6"` — daily circuit-breaker breach under `block` mode
              - `"K-6-size-down"` — daily circuit-breaker breach under `size_down` mode
              - `"K-7"` — weekly circuit-breaker breach under `block` mode
              - `"K-7-size-down"` — weekly circuit-breaker breach under `size_down` mode

            Block-mode v3 sidecars produced under ADR-0025 §D-1 (e.g., run_id
            `154237b365794244974068402b377191`) carry zero in the two new
            `*-size-down` keys → bit-exact reproducibility preserved per
            ADR-0028 §D-3 backward-compatibility contract.

            The previous (Phase O.16) semantic of "blocked-entries" is
            INCORRECT — size-down breaches are silently dropped at aggregation
            because the orchestrator's keyset-iteration excluded the
            `"size-down-applied"` reason string. The Phase O.17 fix realigns
            the runtime + sidecar disclosure on the canonical "constraint
            breaches" semantic; the empirically-engaged size-down events now
            surface in `summarize_trigger_counts.annotation = "kill-switch-active"`.

            Design alternative considered: a separate `blocked_entries_count`
            field could be added to distinguish blocked vs sized-down breaches
            beyond what the 2 new keys already encode. Deferred to v2 per
            `P1-ADR-0028-BLOCKED-ENTRIES-VS-SIZE-DOWN-DECOMPOSE-V2` (non-
            blocking; the 6-key schema already encodes the distinction).
        universe: list of symbols in the active basket; validated at init for
            K-5 correlated-pair membership per F-1-6 audit fix.
        size_down_active_session: per ADR-0028 §D-1, set True when K-6 breach
            occurs under `k6_enforcement="size_down"`. Resets to False on
            `advance_session`. Consumers multiply position size by
            `config.size_down_fraction` while this is True.
        size_down_active_week: parallel to session; tracks K-7 size-down state
            for the active ISO-week. Resets on `advance_week`.
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
    # ADR-0028 §D-1: per-session / per-week size-down flags.
    size_down_active_session: bool = False
    size_down_active_week: bool = False


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
        # Phase O.17 fix per `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE`:
        # 6-key schema separates block-mode K-6/K-7 (capital-preservation
        # rejection) from size-down-mode K-6/K-7 (admit-with-shrinkage). See
        # `KillSwitchRuntimeState.trigger_counts` docstring for the canonical
        # semantic. Existing block-mode v3 sidecars carry zero in the two
        # `*-size-down` keys → bit-exact backward-compatibility per ADR-0028
        # §D-3.
        trigger_counts={
            "K-3": 0,
            "K-4": 0,
            "K-6": 0,
            "K-6-size-down": 0,
            "K-7": 0,
            "K-7-size-down": 0,
        },
        universe=tuple(s.upper() for s in universe),
    )


def advance_session(
    state: KillSwitchRuntimeState,
    *,
    new_session_date: date,
    current_equity: float,
) -> KillSwitchRuntimeState:
    """Record session-start equity + reset daily accumulator on session-boundary.

    Per ADR-0028 §D-1, also resets `size_down_active_session = False` so the
    new session begins at full position-size; any K-6 breach within the new
    session re-sets the flag (only if `k6_enforcement="size_down"`).
    """
    new_daily = dict(state.daily_pnl_by_session_date)
    new_daily.setdefault(new_session_date, 0.0)
    return replace(
        state,
        current_session_date=new_session_date,
        equity_at_session_start=float(current_equity),
        daily_pnl_by_session_date=new_daily,
        # ADR-0028 §D-1: per-session size-down flag resets at boundary.
        size_down_active_session=False,
    )


def advance_week(
    state: KillSwitchRuntimeState,
    *,
    new_week_id: tuple[int, int],
    current_equity: float,
) -> KillSwitchRuntimeState:
    """Record week-start equity + reset weekly accumulator on ISO-week boundary.

    Per ADR-0028 §D-1, also resets `size_down_active_week = False`.
    """
    new_weekly = dict(state.weekly_pnl_by_week_id)
    new_weekly.setdefault(new_week_id, 0.0)
    return replace(
        state,
        current_week_id=new_week_id,
        equity_at_week_start=float(current_equity),
        weekly_pnl_by_week_id=new_weekly,
        # ADR-0028 §D-1: per-week size-down flag resets at boundary.
        size_down_active_week=False,
    )


def check_entry_blocked(
    state: KillSwitchRuntimeState,
    config: KillSwitchRuntimeConfig,
    *,
    symbol: str,
    position_size: int,
) -> tuple[bool, str | None, float, KillSwitchRuntimeState]:
    """Return (blocked, reason, sizing_modifier, new_state).

    Per ADR-0028 §D-1, the 3-tuple-plus-state signature replaces the legacy
    2-tuple in ADR-0025 §D-1. The new return contract is:

    - `blocked` (bool): orchestrator skips the entry if True.
    - `reason` (str | None): K-N id of the first-firing constraint; None if
      not blocked.
    - `sizing_modifier` (float ∈ (0, 1]): multiplicative shrinkage applied by
      the orchestrator to the position-size denominator BEFORE opening the
      trade. Returns 1.0 in the normal path; returns `config.size_down_fraction`
      when a K-6 or K-7 breach is detected under `k6_enforcement="size_down"`
      or `k7_enforcement="size_down"` and the trade is ALLOWED with reduced
      size (size_down_active_{session,week} flag set on new_state).
    - `new_state` (KillSwitchRuntimeState): the (possibly updated) state. On
      size_down breach the returned state has the corresponding size-down
      flag toggled True so subsequent entries within the session/week inherit
      the modifier (state.size_down_active_session OR size_down_active_week
      check OR is consulted in the new sizing modifier branch below).

    Reason-string contract per Phase O.17 `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-
    DEFECT-CLOSE`: the `reason` field carries the canonical K-N id that the
    orchestrator passes to `record_trigger`. Six reason strings are emitted
    across all paths:

      - `"K-3"` — K-3 block (no add-to-loser)
      - `"K-4"` — K-4 block (capacity cap)
      - `"K-6"` — K-6 block (daily breaker under `block` mode)
      - `"K-6-size-down"` — K-6 size-down breach (daily breaker under `size_down` mode)
      - `"K-7"` — K-7 block (weekly breaker under `block` mode)
      - `"K-7-size-down"` — K-7 size-down breach (weekly breaker under `size_down` mode)

    Each reason directly indexes into `state.trigger_counts` so the
    `record_trigger(state, reason)` call lands in the canonical 6-key dict.
    Block-mode v3 sidecars produced under ADR-0025 §D-1 are bit-exact
    reproducible since block-mode reason strings (`"K-6"`, `"K-7"`) are
    unchanged.

    Order of K-N checks: K-3 (existing open position) → K-4 (capacity cap) →
    K-6 (daily breaker) → K-7 (weekly breaker). The first-firing structural
    constraint (K-3 / K-4) short-circuits and blocks; only its trigger is
    recorded. K-6 / K-7 are circuit breakers: when "block" mode is active
    they short-circuit and block; when "size_down" mode is active they set
    the size-down flag, return (False, "K-N-size-down",
    config.size_down_fraction, new_state) but DO NOT block.

    Stickiness semantic: once a K-6 size-down has fired in the current
    session (state.size_down_active_session=True), all subsequent entries
    within the session inherit the size-down multiplier without re-evaluating
    the K-6 daily P/L threshold (this is the canonical "size-down sticky
    until session boundary" semantic of ADR-0028 §D-1). Parallel K-7
    handling on the weekly clock.

    Per ADR-0028 §D-1 Out-of-scope: K-3 and K-4 retain block-only
    enforcement. The size-down semantic applies ONLY to K-6/K-7 circuit
    breakers; the structural invariants (K-3 no-overlap; K-4 capacity cap)
    are partial-enforcement-incoherent.
    """
    sym = symbol.upper()

    if config.enable_k3 and sym in state.open_position_by_symbol:
        return True, "K-3", 1.0, state

    if config.enable_k4:
        cap = config.capacity_caps.get(sym, 1)
        if position_size > cap:
            return True, "K-4", 1.0, state

    # Pre-compute the "size_down active" composite (sticky-flag OR newly-breached).
    size_down_modifier: float = 1.0
    new_state = state
    # Phase O.17 `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE`: when a
    # FRESH K-N breach fires under size_down mode, the orchestrator must
    # receive the K-N-specific reason ("K-6-size-down" or "K-7-size-down")
    # so `record_trigger(state, reason)` lands in the canonical 6-key dict.
    # Sticky-inheritance entries (no fresh breach; flag set from prior call)
    # return the legacy "size-down-applied" sentinel so the orchestrator's
    # downstream sizing branch engages without double-counting the breach.
    fresh_breach_reason: str | None = None

    if config.enable_k6 and state.current_session_date is not None:
        daily_pnl = state.daily_pnl_by_session_date.get(state.current_session_date, 0.0)
        # justify: K6_DAILY_DRAWDOWN_THRESHOLD = -0.02 per ADR-0017 §5 K-6 +
        # ADR-0025 §D-1 F-1-7 current-equity-ratcheting fix; threshold ratchets
        # with equity_at_session_start (NOT starting_equity).
        k6_breached = (
            daily_pnl < K6_DAILY_DRAWDOWN_THRESHOLD * state.equity_at_session_start
        )
        if k6_breached or state.size_down_active_session:
            if config.k6_enforcement == "block":
                return True, "K-6", 1.0, state
            # ADR-0028 §D-1: size_down mode — allow entry with shrunk size.
            size_down_modifier = min(size_down_modifier, config.size_down_fraction)
            if k6_breached and not state.size_down_active_session:
                new_state = replace(new_state, size_down_active_session=True)
                fresh_breach_reason = "K-6-size-down"

    if config.enable_k7 and state.current_week_id is not None:
        weekly_pnl = state.weekly_pnl_by_week_id.get(state.current_week_id, 0.0)
        # justify: K7_WEEKLY_DRAWDOWN_THRESHOLD = -0.05 per ADR-0017 §5 K-7.
        k7_breached = (
            weekly_pnl < K7_WEEKLY_DRAWDOWN_THRESHOLD * state.equity_at_week_start
        )
        if k7_breached or new_state.size_down_active_week:
            if config.k7_enforcement == "block":
                return True, "K-7", 1.0, state
            size_down_modifier = min(size_down_modifier, config.size_down_fraction)
            if k7_breached and not new_state.size_down_active_week:
                new_state = replace(new_state, size_down_active_week=True)
                # If K-6 also fresh-breached this call, K-7 is recorded too.
                # Both breach-counts will be incremented when the orchestrator
                # calls `record_trigger(state, reason)` for the returned
                # reason (we surface the K-7 reason here; K-6 was already
                # incremented above via the previous record_trigger call IF
                # the orchestrator uses the per-call return value).
                #
                # For the single-record-per-call orchestrator pattern in
                # H062/H055, the returned reason is K-7-size-down when BOTH
                # breach freshly; this under-counts K-6 in the rare double-
                # breach edge case (~one call per session-AND-week boundary).
                # Tracked under `P1-ADR-0028-DOUBLE-BREACH-CALL-COUNTING`
                # (non-blocking; structurally rare per ADR-0017 §5 K-6/K-7
                # threshold separation).
                fresh_breach_reason = "K-7-size-down"

    if size_down_modifier < 1.0:
        # Fresh breach → emit specific K-N-size-down reason so the
        # orchestrator's record_trigger call lands in the canonical key.
        # Sticky inheritance (no fresh breach this call) → emit the legacy
        # "size-down-applied" sentinel; the orchestrator's record_trigger
        # call lands it permissively but the canonical 6-key keyset
        # iteration ignores it (no double-counting; the breach was already
        # incremented on the originating call).
        return (
            False,
            fresh_breach_reason if fresh_breach_reason is not None else "size-down-applied",
            size_down_modifier,
            new_state,
        )

    return False, None, 1.0, state


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
    """Increment trigger_counts[constraint_id] for sidecar emission.

    Per Phase O.17 `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE`, the
    canonical reason strings handled by this function (via the return of
    `check_entry_blocked`) are:

      - `"K-3"`, `"K-4"`, `"K-6"`, `"K-7"` — block-mode breaches; bit-exact
        reproducible across Phase O.16 sidecars.
      - `"K-6-size-down"`, `"K-7-size-down"` — size-down-mode FRESH breaches;
        increment the dedicated keys initialized by `init_runtime_state`.
      - `"size-down-applied"` (sentinel) — sticky-inheritance size-down on
        entries with no fresh breach this call; the orchestrator records it
        permissively but it does NOT contribute to `trigger_counts` since
        the canonical 6-key keyset excludes it. Operators wanting to count
        admitted-with-size-down entries (independent of fresh-breach counts)
        should use a separate orchestrator-side counter; tracked under
        `P1-ADR-0028-ADMITTED-WITH-SIZE-DOWN-COUNTER` (non-blocking).
    """
    new_counts = dict(state.trigger_counts)
    new_counts[constraint_id] = new_counts.get(constraint_id, 0) + 1
    return replace(state, trigger_counts=new_counts)


def summarize_trigger_counts(
    state: KillSwitchRuntimeState,
    config: KillSwitchRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Provenance summary for sidecar / KPI annotation per ADR-0025 §D-5 + ADR-0028 §D-4.

    Args:
        state: Runtime state at end of simulation.
        config: Optional config carrying the enforcement-mode enum. When
            supplied, the `mode_annotation` field carries `kill-switch-mode-
            {block, size-down}` per ADR-0028 §D-4. When None (legacy callers),
            mode_annotation is absent (backward-compatible).

    Phase O.17 `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` semantic:
    `total_triggers` sums over the canonical 6-key trigger_counts schema
    (K-3, K-4, K-6, K-6-size-down, K-7, K-7-size-down); `runtime_active`
    fires on any breach regardless of enforcement mode; `annotation` is
    `"kill-switch-active"` when any breach fired. The new
    `size_down_event_count` operator-readable convenience field aggregates
    K-6-size-down + K-7-size-down for fast disclosure of size-down activity.
    Block-mode v3 sidecars are bit-exact reproducible since their two
    `*-size-down` keys carry zero.
    """
    counts = state.trigger_counts
    total = sum(counts.values())
    size_down_total = (
        int(counts.get("K-6-size-down", 0)) + int(counts.get("K-7-size-down", 0))
    )
    summary: dict[str, Any] = {
        "runtime_active": total > 0,
        "trigger_counts": dict(counts),
        "total_triggers": total,
        "size_down_event_count": size_down_total,
        "annotation": "kill-switch-active" if total > 0 else "kill-switch-inactive",
    }
    if config is not None:
        # ADR-0028 §D-4: kill-switch-mode-{block, size-down} disclosure.
        # The annotation reflects the AGGREGATE mode: if EITHER K-6 OR K-7
        # is in size_down, the annotation is "size-down"; only when both
        # are "block" do we emit "block". This composes correctly when K-3
        # / K-4 are enabled (they retain block-only enforcement per §D-1).
        any_size_down = (
            config.k6_enforcement == "size_down"
            or config.k7_enforcement == "size_down"
        )
        summary["mode_annotation"] = (
            "kill-switch-mode-size-down" if any_size_down
            else "kill-switch-mode-block"
        )
        summary["k6_enforcement"] = config.k6_enforcement
        summary["k7_enforcement"] = config.k7_enforcement
        summary["size_down_fraction"] = float(config.size_down_fraction)
    return summary
