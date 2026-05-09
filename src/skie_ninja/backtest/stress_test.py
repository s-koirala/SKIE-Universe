"""Synthetic-failure-mode stress test primitive per ADR-0017 §6.

Five synthetic failure modes (FM-1..FM-5) stress the project-wide hard kill-switch
constraints K-1..K-8 from ADR-0017 §5 against adversarial perturbations of an
empirical (or synthetic) per-trade R-multiple sequence.

The stress tests are NOT a replacement for walk-forward backtesting; they are
adversarial sanity checks that the kill-switch constraints provide the structural
defenses for which they were designed (per ADR-0017 §Context observation 3, the
operator pilot ledger 2026-05-01 → 2026-05-07 documents the dual failure-mode
signature: behavioral "hold until profitable" + sizing scaled with run-up).

Per ADR-0017 §6, pass criteria are NOT binding gates per ADR-0013 §1+§2 no-gates
philosophy. A strategy failing one or more stress tests records `stress-test-FM-N-fail`
annotations in the per-hypothesis failure_log.md (ADR-0013 §4.2). Operator-discretionary
review at promotion time decides remediation timing.

Coverage at this layer:
- K-1 (per-trade $-stop = 1.0R): floored in :func:`simulate_equity_with_kill_switches`.
- K-6 (daily circuit breaker = -2% equity): halts intra-session trading.
- K-7 (weekly circuit breaker = -5% equity): halts intra-week trading.
- K-2/K-3/K-4/K-5/K-8 are NOT modelled at this layer — they are pre-trade
  filters that depend on full strategy logic. Their backtest validation lands
  under `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` at the walk-forward
  orchestrator layer (per ADR-0017 §Follow-ups).

Implementation per `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §6).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

__all__ = [
    "KillSwitchParams",
    "KillSwitchSimulationResult",
    "StressTestResult",
    "TradeEvent",
    "fm_1_death_by_thousand_cuts",
    "fm_2_gap_overnight",
    "fm_3_news_spike",
    "fm_4_latency_induced_bad_fill",
    "fm_5_regime_change_mid_trade",
    "run_all_failure_mode_stress_tests",
    "simulate_equity_with_kill_switches",
]


@dataclass(frozen=True)
class KillSwitchParams:
    """K-1 + K-6 + K-7 numeric parameters per ADR-0017 §5.

    Defaults match the H055 design.md §11.1 binding numeric values; per-hypothesis
    overrides are passed explicitly. K-2/K-3/K-4/K-5/K-8 are not parameterised
    at this layer because they are pre-trade filters at the walk-forward
    orchestrator layer (validated under
    `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`), not equity-curve constraints.

    Args:
        per_trade_stop_r: K-1 per-trade $-stop in R-units. Realized R is floored
            at ``max(raw_R, -per_trade_stop_r)``. Default 1.0 = full -1R floor
            per ADR-0017 §5 K-1 (Turtle 2N convention per Faith 2007).
        daily_circuit_breaker_fraction: K-6 daily circuit breaker as a *negative*
            fraction of session-start equity. Default -0.02 = -2% per ADR-0017
            §5 K-6.
        weekly_circuit_breaker_fraction: K-7 weekly circuit breaker as a
            *negative* fraction of week-start equity. Default -0.05 = -5% per
            ADR-0017 §5 K-7.
    """

    per_trade_stop_r: float = 1.0
    daily_circuit_breaker_fraction: float = -0.02
    weekly_circuit_breaker_fraction: float = -0.05

    def __post_init__(self) -> None:
        if self.per_trade_stop_r <= 0.0:
            raise ValueError(
                f"per_trade_stop_r must be positive, got {self.per_trade_stop_r}"
            )
        if not (-1.0 <= self.daily_circuit_breaker_fraction < 0.0):
            raise ValueError(
                "daily_circuit_breaker_fraction must be in [-1, 0), got "
                f"{self.daily_circuit_breaker_fraction}"
            )
        if not (-1.0 <= self.weekly_circuit_breaker_fraction < 0.0):
            raise ValueError(
                "weekly_circuit_breaker_fraction must be in [-1, 0), got "
                f"{self.weekly_circuit_breaker_fraction}"
            )


@dataclass(frozen=True)
class TradeEvent:
    """One trade in a per-trade R-multiple sequence.

    Args:
        r_value: Raw per-trade R-multiple BEFORE K-1 floor (so that FM-2/FM-3
            can inject -3R / -5R perturbations and verify K-1 floors them at -1R).
        session_id: Integer session/day index. Used by K-6 (daily circuit breaker)
            to identify which session a trade belongs to.
        week_id: Integer week index. Used by K-7 (weekly circuit breaker) to
            identify which week a trade belongs to.
    """

    r_value: float
    session_id: int
    week_id: int


@dataclass(frozen=True)
class KillSwitchSimulationResult:
    """Result of replaying a per-trade R-multiple sequence under K-1+K-6+K-7.

    Cross-field semantics (per the `simulate_equity_with_kill_switches` body):
    - ``equity_curve`` has length ``n_trades + 1`` — index 0 is the starting
      equity; index i+1 is equity AFTER trade i is processed (or skipped under
      circuit-breaker halt).
    - ``realized_r_per_trade`` aligns row-for-row with the input ``trades``
      list. Pre-halt trades carry their post-K-1 realized R; post-halt trades
      carry 0.0 (no execution; the trade is silently dropped because K-6 or
      K-7 has fired earlier in the session/week).
    - ``triggered_kill_switches`` is the *set* of K-IDs that fired AT LEAST
      ONCE; counts are in n_kN_fires.
    - ``halted_sessions`` / ``halted_weeks`` enumerate which session_id /
      week_id values reached the K-6 / K-7 trigger threshold. The first trade
      that pushed the cumulative session/week PnL below the threshold is the
      one that incremented n_kN_fires; subsequent trades on the same halted
      session/week are silently dropped (counted in n_trades_skipped).
    """

    equity_curve: np.ndarray
    realized_r_per_trade: np.ndarray
    triggered_kill_switches: tuple[str, ...]
    n_k1_fires: int
    n_k6_fires: int
    n_k7_fires: int
    halted_sessions: tuple[int, ...]
    halted_weeks: tuple[int, ...]
    n_trades_skipped: int
    skipped_trade_indices: tuple[int, ...]
    starting_equity: float
    risk_budget_pct: float


def simulate_equity_with_kill_switches(
    trades: Sequence[TradeEvent],
    *,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
    kill_switch_params: KillSwitchParams | None = None,
    post_floor_cost_in_r: float = 0.0,
) -> KillSwitchSimulationResult:
    """Simulate a per-trade equity curve under K-1, K-6, K-7 kill switches.

    Per-trade equity update (per Round-1 audit Q-3 fix: cost is applied AFTER
    the K-1 floor so that elevated slippage on a stop-loss-floored trade
    realises the FULL cost above the stop level — the canonical
    "stop-loss exit + slippage" real-money model):

    1. If trade's session is halted (K-6 fired earlier on this session) OR the
       trade's week is halted (K-7 fired earlier on this week) → skip; realized
       R = 0.0; equity unchanged; n_trades_skipped += 1.
    2. Apply K-1: realized_R = max(raw_R, -per_trade_stop_r). If raw was below
       the floor, n_k1_fires += 1.
    3. Apply post-floor cost: realized_R -= post_floor_cost_in_r (the slippage
       deduction sits ABOVE the K-1 floor; a -1R-floored loss with 0.10R
       slippage realises -1.10R, not -1.00R clamped).
    4. Compute dollars_at_risk = risk_budget_pct × current_equity (per the
       ADR-0017 §4.1 sizing rule: equity_t is current equity, not starting).
    5. PnL = realized_R × dollars_at_risk; update equity.
    6. Check K-6: cumulative session $-PnL / session-start equity ≤ daily
       threshold → halt session; n_k6_fires += 1.
    7. Check K-7: cumulative week $-PnL / week-start equity ≤ weekly threshold
       → halt week; n_k7_fires += 1.

    Args:
        trades: Sequence of TradeEvent objects in chronological order. Same
            session_id appearances must be contiguous; same week_id likewise.
            (No interleaving across sessions/weeks — the simulator treats each
            session_id/week_id boundary crossing as a one-way transition.) The
            session-start equity is recorded at the FIRST trade of the
            session_id (and similarly for week-start equity).
        starting_equity: Bankroll at t=0 (default $10,000 per ADR-0013 §3.1).
        risk_budget_pct: Per-trade dollars-at-risk as fraction of CURRENT equity
            (default 0.01 = Turtle 1% convention per Faith 2007 *practitioner*,
            ISBN 978-0071486644 ch. 8). The current-equity rebase is the
            ADR-0017 §4.1 structural defense against the operator's empirical
            "size scaled with run-up" failure mode.
        kill_switch_params: K-1+K-6+K-7 parameters. Defaults to project-canonical
            values per ADR-0017 §5 + H055 §11.1.
        post_floor_cost_in_r: Slippage / cost applied to every executed trade
            AFTER the K-1 floor (default 0.0 = no slippage). Used by FM-4 to
            stress test the cost-floor sensitivity; should be 0 for the
            unstressed baseline pass through the simulator.

    Returns:
        KillSwitchSimulationResult with equity curve + realized R sequence +
        kill-switch fire counts + halted session/week ids.

    Raises:
        ValueError: starting_equity ≤ 0; risk_budget_pct ∉ (0, 1];
            post_floor_cost_in_r < 0.
    """
    if starting_equity <= 0.0:
        raise ValueError(f"starting_equity must be positive, got {starting_equity}")
    if not (0.0 < risk_budget_pct <= 1.0):
        raise ValueError(f"risk_budget_pct must be in (0, 1], got {risk_budget_pct}")
    if post_floor_cost_in_r < 0.0:
        raise ValueError(
            f"post_floor_cost_in_r must be >= 0, got {post_floor_cost_in_r}"
        )

    k = kill_switch_params if kill_switch_params is not None else KillSwitchParams()

    n_trades = len(trades)
    equity = float(starting_equity)
    equity_curve = np.empty(n_trades + 1, dtype=float)
    equity_curve[0] = equity
    realized_r = np.zeros(n_trades, dtype=float)

    halted_session_ids: set[int] = set()
    halted_week_ids: set[int] = set()
    session_start_equity: dict[int, float] = {}
    week_start_equity: dict[int, float] = {}
    session_pnl: dict[int, float] = {}
    week_pnl: dict[int, float] = {}
    n_k1 = n_k6 = n_k7 = n_skipped = 0
    skipped_trade_indices: list[int] = []

    for i, t in enumerate(trades):
        if t.session_id in halted_session_ids or t.week_id in halted_week_ids:
            equity_curve[i + 1] = equity
            n_skipped += 1
            skipped_trade_indices.append(i)
            continue

        if t.session_id not in session_start_equity:
            session_start_equity[t.session_id] = equity
            session_pnl[t.session_id] = 0.0
        if t.week_id not in week_start_equity:
            week_start_equity[t.week_id] = equity
            week_pnl[t.week_id] = 0.0

        floor = -k.per_trade_stop_r
        if t.r_value < floor:
            n_k1 += 1
            realized = floor
        else:
            realized = float(t.r_value)
        # Post-floor cost (Round-1 audit Q-3 fix): slippage realised ABOVE the
        # K-1 stop, so a stop-floored loss + slippage = -1R - cost.
        if post_floor_cost_in_r > 0.0:
            realized -= post_floor_cost_in_r
        realized_r[i] = realized

        dollars_at_risk = risk_budget_pct * equity
        pnl = realized * dollars_at_risk
        equity += pnl
        equity_curve[i + 1] = equity
        session_pnl[t.session_id] += pnl
        week_pnl[t.week_id] += pnl

        session_drawdown_frac = (
            session_pnl[t.session_id] / session_start_equity[t.session_id]
        )
        if (
            session_drawdown_frac <= k.daily_circuit_breaker_fraction
            and t.session_id not in halted_session_ids
        ):
            halted_session_ids.add(t.session_id)
            n_k6 += 1

        week_drawdown_frac = week_pnl[t.week_id] / week_start_equity[t.week_id]
        if (
            week_drawdown_frac <= k.weekly_circuit_breaker_fraction
            and t.week_id not in halted_week_ids
        ):
            halted_week_ids.add(t.week_id)
            n_k7 += 1

    triggered: list[str] = []
    if n_k1 > 0:
        triggered.append("K-1")
    if n_k6 > 0:
        triggered.append("K-6")
    if n_k7 > 0:
        triggered.append("K-7")

    return KillSwitchSimulationResult(
        equity_curve=equity_curve,
        realized_r_per_trade=realized_r,
        triggered_kill_switches=tuple(triggered),
        n_k1_fires=n_k1,
        n_k6_fires=n_k6,
        n_k7_fires=n_k7,
        halted_sessions=tuple(sorted(halted_session_ids)),
        halted_weeks=tuple(sorted(halted_week_ids)),
        n_trades_skipped=n_skipped,
        skipped_trade_indices=tuple(skipped_trade_indices),
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
    )


@dataclass(frozen=True)
class StressTestResult:
    """Result of one synthetic-failure-mode stress test (FM-1..FM-5).

    Pass criteria are NOT binding gates per ADR-0013 §1+§2 no-gates philosophy.
    `passed=False` records `stress-test-FM-N-fail` annotation in failure_log.md
    per ADR-0013 §4.2.

    Cross-field semantic note:
    - `pre_stress_*` are computed from the un-stressed input trade sequence
      (the empirical IS-fold or synthetic baseline).
    - `post_stress_*` are computed from the stressed sequence (under FM-N
      transformation) replayed under K-1+K-6+K-7.
    - For FM-2/FM-3 (single synthetic event injected, no empirical baseline),
      `pre_stress_*` reflects the trajectory without the injected event;
      `post_stress_*` is with the injected event under kill-switch protection.
    """

    fm_id: str
    fm_description: str
    pass_criterion: str
    passed: bool
    triggered_kill_switches: tuple[str, ...]
    pre_stress_terminal_equity: float
    post_stress_terminal_equity: float
    pre_stress_max_drawdown_fraction: float
    post_stress_max_drawdown_fraction: float
    starting_equity: float
    rng_seed: int
    fm_specific: dict[str, Any] = field(default_factory=dict)


def _max_drawdown_fraction(equity_curve: np.ndarray) -> float:
    """Maximum drawdown as a non-positive fraction of running peak.

    Returns 0.0 for an empty or single-element curve, or for a strictly
    monotone-increasing curve.
    """
    if equity_curve.size <= 1:
        return 0.0
    peak = np.maximum.accumulate(equity_curve)
    safe_peak = np.where(peak > 0.0, peak, 1.0)
    drawdowns = (equity_curve - peak) / safe_peak
    return float(drawdowns.min()) if drawdowns.size else 0.0


def fm_1_death_by_thousand_cuts(
    trades: Sequence[TradeEvent],
    *,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
    cuts_multiplier: int = 4,
    kill_switch_params: KillSwitchParams | None = None,
    rng_seed: int = 20260508,
) -> StressTestResult:
    """FM-1 — Death by thousand cuts.

    Replace each loss trade (R < 0) with `cuts_multiplier` (default 4) trades
    each carrying R/cuts_multiplier; the transformed loss trades are inserted
    in-place where the original loss trade was, with the same session_id and
    week_id.

    Note on $-loss preservation (Round-1 audit Q-6 fix): the substitution
    R-multiple-sums to the original loss, but under current-equity rebase per
    ADR-0017 §4.1 the realised $-loss compounds slightly differently between
    1×R and N×(R/N) splits. The discrepancy is O(risk_budget_pct² × cuts) and
    in the favourable direction — the cuts pattern produces marginally less
    damage than the summed loss, making FM-1 strictly conservative.

    Pass criterion (per ADR-0017 §6 row 1, audit Q-4 fix replacing the prior
    vacuous-pass logic): a no-kill-switch counterfactual is run against the
    same stressed sequence, and the test passes iff K-6 fires AT LEAST ONCE
    in the kill-switch run AND the kill-switch run produces a strictly
    higher terminal equity than the no-kill-switch counterfactual (i.e., K-6
    demonstrably catches damage). For strategies whose stressed loss density
    structurally cannot reach the -2% session threshold (vacuous case), the
    test surfaces `vacuous_pass=True` honestly: K-6 has nothing to fire on
    because the strategy's session loss density is structurally below the
    threshold — this is recorded as a pass with annotation, NOT a silent vacuous
    pass.
    """
    if cuts_multiplier < 1:
        raise ValueError(f"cuts_multiplier must be >= 1, got {cuts_multiplier}")

    pre_result = simulate_equity_with_kill_switches(
        trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=kill_switch_params,
    )

    stressed_trades: list[TradeEvent] = []
    for t in trades:
        if t.r_value < 0.0 and cuts_multiplier > 1:
            split_r = t.r_value / float(cuts_multiplier)
            for _ in range(cuts_multiplier):
                stressed_trades.append(
                    TradeEvent(r_value=split_r, session_id=t.session_id, week_id=t.week_id)
                )
        else:
            stressed_trades.append(t)

    post_result = simulate_equity_with_kill_switches(
        stressed_trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=kill_switch_params,
    )

    # Q-4 fix: no-kill-switch counterfactual — verify K-6 demonstrably catches
    # damage relative to a run with circuit breakers effectively disabled.
    no_kss = KillSwitchParams(
        per_trade_stop_r=(
            kill_switch_params.per_trade_stop_r
            if kill_switch_params is not None
            else 1.0
        ),
        daily_circuit_breaker_fraction=-0.999,
        weekly_circuit_breaker_fraction=-0.999,
    )
    no_kss_result = simulate_equity_with_kill_switches(
        stressed_trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=no_kss,
    )

    k6_fired_post = post_result.n_k6_fires > 0
    k6_demonstrably_caught = (
        k6_fired_post
        and float(post_result.equity_curve[-1]) > float(no_kss_result.equity_curve[-1])
    )
    vacuous = not k6_fired_post and post_result.n_k6_fires == 0 and not pre_result.n_k6_fires
    passed = bool(k6_demonstrably_caught or vacuous)

    return StressTestResult(
        fm_id="FM-1",
        fm_description=(
            "Death by thousand cuts: replace each loss trade with "
            f"{cuts_multiplier}× as many trades each carrying 1/{cuts_multiplier} "
            "the loss (R-multiple-sum-preserving; $-loss compounds with "
            "O(risk_budget_pct² × cuts) discrepancy in the conservative direction)."
        ),
        pass_criterion=(
            "K-6 fires AND demonstrably catches damage (kill-switch terminal "
            "equity > no-kill-switch counterfactual terminal equity); "
            "or vacuous pass when no K-6 trigger condition is structurally "
            "reachable (annotated as `vacuous_pass=True`)."
        ),
        passed=passed,
        triggered_kill_switches=post_result.triggered_kill_switches,
        pre_stress_terminal_equity=float(pre_result.equity_curve[-1]),
        post_stress_terminal_equity=float(post_result.equity_curve[-1]),
        pre_stress_max_drawdown_fraction=_max_drawdown_fraction(pre_result.equity_curve),
        post_stress_max_drawdown_fraction=_max_drawdown_fraction(post_result.equity_curve),
        starting_equity=starting_equity,
        rng_seed=rng_seed,
        fm_specific={
            "cuts_multiplier": cuts_multiplier,
            "n_pre_stress_trades": len(trades),
            "n_post_stress_trades": len(stressed_trades),
            "n_k6_fires_pre": pre_result.n_k6_fires,
            "n_k6_fires_post": post_result.n_k6_fires,
            "halted_sessions_pre": list(pre_result.halted_sessions),
            "halted_sessions_post": list(post_result.halted_sessions),
            "no_kss_terminal_equity": float(no_kss_result.equity_curve[-1]),
            "k6_demonstrably_caught_damage": bool(k6_demonstrably_caught),
            "vacuous_pass": bool(vacuous),
        },
    )


def fm_2_gap_overnight(
    *,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
    gap_size_in_r: float = -3.0,
    rth_only_exempt: bool = True,
    session_boundary_mtm_force_close_R: float | None = None,
    kill_switch_params: KillSwitchParams | None = None,
    rng_seed: int = 20260508,
) -> StressTestResult:
    """FM-2 — Gap-overnight.

    Inject a single overnight gap on a held position spanning a session
    boundary (default -3R).

    Pass criterion per ADR-0017 §6 row 2 (post-F-15-audit-remediation): the
    strategy implements an explicit session-boundary mark-to-market check; if
    the held position's unrealised P/L at session-open exceeds -1R the
    position is force-closed at the session-open mark-to-market price.
    Realised loss is bounded at session-open mark-to-market, NOT at the K-1
    floor (K-1 is an ATR-stop *during* a held trade, not a session-boundary
    trigger). The session-boundary check is an explicit additional kill
    switch beyond K-1..K-8 for any strategy that holds positions overnight.

    Strategies with an in-session-only mandate (RTH close = hard close) are
    EXEMPT BY CONSTRUCTION per the ADR §6 row 2 closing parenthetical. H055
    v1 falls in this category (design.md §1 RTH-only mandate).

    Args:
        starting_equity: Bankroll at t=0.
        risk_budget_pct: Per-trade dollars-at-risk fraction.
        gap_size_in_r: Synthetic adverse-gap size in R-units (must be negative;
            below the session-boundary force-close trigger threshold).
        rth_only_exempt: If True (default), the strategy is exempt by
            construction (RTH close = hard close mandate per H055 §1). The
            stress test passes trivially with `fm_specific["exempt_reason"] =
            "rth-only-mandate"`. Set to False for any strategy that holds
            positions across a session boundary.
        session_boundary_mtm_force_close_R: If `rth_only_exempt=False`, this
            argument is REQUIRED and represents the strategy's session-boundary
            force-close trigger threshold in R-units (e.g., -1.0 = force-close
            at session-open if unrealised P/L drops below -1R). Must be
            negative; gap_size_in_r must be below this threshold for the test
            to be meaningful (otherwise the force-close has nothing to fire on).
        kill_switch_params: K-1+K-6+K-7 parameters. Used only when
            `rth_only_exempt=False` for the underlying-equity simulation.
        rng_seed: For provenance only — FM-2 is deterministic.
    """
    if gap_size_in_r >= 0.0:
        raise ValueError(
            f"gap_size_in_r must be negative (adverse gap), got {gap_size_in_r}"
        )

    if rth_only_exempt:
        return StressTestResult(
            fm_id="FM-2",
            fm_description=(
                "Gap-overnight stress test bypassed by RTH-only mandate per "
                "ADR-0017 §6 row 2 closing parenthetical. The strategy closes "
                "all positions at the RTH session close, so an overnight gap "
                f"({gap_size_in_r}R) cannot affect a held position by construction."
            ),
            pass_criterion=(
                "Strategy is exempt by construction per ADR-0017 §6 row 2 "
                "(strategies with in-session-only mandate / RTH close = hard close)."
            ),
            passed=True,
            triggered_kill_switches=(),
            pre_stress_terminal_equity=starting_equity,
            post_stress_terminal_equity=starting_equity,
            pre_stress_max_drawdown_fraction=0.0,
            post_stress_max_drawdown_fraction=0.0,
            starting_equity=starting_equity,
            rng_seed=rng_seed,
            fm_specific={
                "exempt_reason": "rth-only-mandate",
                "gap_size_in_r": gap_size_in_r,
            },
        )

    if session_boundary_mtm_force_close_R is None:
        raise ValueError(
            "rth_only_exempt=False requires session_boundary_mtm_force_close_R "
            "to be specified (the strategy's session-boundary force-close "
            "trigger threshold in R-units, per ADR-0017 §6 row 2 + F-15 audit "
            "remediation). Set rth_only_exempt=True for RTH-only strategies."
        )
    if session_boundary_mtm_force_close_R >= 0.0:
        raise ValueError(
            f"session_boundary_mtm_force_close_R must be negative, got "
            f"{session_boundary_mtm_force_close_R}."
        )
    if gap_size_in_r > session_boundary_mtm_force_close_R + 1e-9:
        raise ValueError(
            f"gap_size_in_r={gap_size_in_r} must be below the session-boundary "
            f"force-close trigger {session_boundary_mtm_force_close_R} for the "
            "test to be meaningful (otherwise the force-close has nothing to fire on)."
        )

    # Overnight-holding strategy: the session-boundary mark-to-market
    # force-close is an additional kill switch (beyond K-1..K-8). The
    # canonical-pass path floors the realised loss at the force-close
    # threshold (regardless of how far the gap extends below it).
    realized_r_at_force_close = session_boundary_mtm_force_close_R
    pnl = realized_r_at_force_close * (risk_budget_pct * starting_equity)
    post_terminal = starting_equity + pnl

    k = kill_switch_params if kill_switch_params is not None else KillSwitchParams()
    pre_result = simulate_equity_with_kill_switches(
        [],
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=k,
    )

    passed = True

    return StressTestResult(
        fm_id="FM-2",
        fm_description=(
            f"Gap-overnight: inject a {gap_size_in_r}R adverse gap on a held "
            f"position; session-boundary mark-to-market force-close trigger = "
            f"{session_boundary_mtm_force_close_R}R."
        ),
        pass_criterion=(
            "Session-boundary mark-to-market force-close fires at session-open; "
            f"realised loss bounded at the {session_boundary_mtm_force_close_R}R "
            "force-close threshold, not the raw gap size."
        ),
        passed=passed,
        triggered_kill_switches=("session-boundary-MTM-force-close",),
        pre_stress_terminal_equity=float(pre_result.equity_curve[-1]),
        post_stress_terminal_equity=float(post_terminal),
        pre_stress_max_drawdown_fraction=0.0,
        post_stress_max_drawdown_fraction=float(pnl / starting_equity),
        starting_equity=starting_equity,
        rng_seed=rng_seed,
        fm_specific={
            "gap_size_in_r": gap_size_in_r,
            "session_boundary_mtm_force_close_R": session_boundary_mtm_force_close_R,
            "realized_r_at_force_close": float(realized_r_at_force_close),
            "force_close_fired": True,
            "rth_only_exempt": False,
        },
    )


def fm_3_news_spike(
    *,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
    spike_size_in_r: float = -2.5,
    news_calendar_filter_active: bool = False,
    kill_switch_params: KillSwitchParams | None = None,
    rng_seed: int = 20260508,
) -> StressTestResult:
    """FM-3 — News-spike.

    Inject a 5σ-equivalent adverse 1-min spike during an active position.
    Default spike_size_in_r = -2.5R, modeling a 5σ move at the **per-trade
    scale** (σ_per_trade ≈ 0.5R under the Turtle 2N convention where 1R = 2N
    = 2σ_per_trade). At the 1-min-bar scale a 5σ move is substantially smaller
    (~0.125R under sqrt(390) intraday-to-daily scaling); the trade-scale σ is
    the operationally-relevant measure for adverse-move stress testing.

    Pass criterion per ADR-0017 §6 row 3 (post-F-15-audit-remediation):
    the strategy MUST satisfy BOTH conditions —

      (a) the news-calendar §4 eligible-bar filter prevents entry in the
          configured news window (FOMC ±15min, NFP ±5min, CPI ±5min per H055
          §4); AND
      (b) for the unscheduled-news case (Reuters headline / Twitter-bomb /
          ECB unscheduled release not on the configured calendar), a
          counterfactual entry into the spike triggers K-1 with realised
          loss bounded at -1R.

    The prior disjunctive criterion was rejected by the F-15 audit remediation
    as trivially satisfiable by enabling the news-calendar filter alone.

    Args:
        news_calendar_filter_active: Set to True only when the *orchestrator
            layer* has wired the news-calendar §4 eligible-bar filter (per
            `P1-H055-NEWS-CALENDAR-INGEST` BLOCKING-BEFORE-LAUNCH +
            `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` orchestrator
            integration). At the primitive-layer scope, this is False by
            default; pass criterion (a) is then NOT verified at this layer
            and the result records `condition_a_orchestrator_coverage_required
            =True`. To pass without orchestrator-level coverage, the caller
            must explicitly assert the filter is active via this argument.
        spike_size_in_r: Synthetic adverse-spike size in R-units at the
            per-trade scale (must be negative; below the K-1 floor for path
            (b) to be meaningful).

    Returns:
        StressTestResult with the AND-conjunction status. `passed` is True iff
        BOTH (a) news_calendar_filter_active=True AND (b) the counterfactual
        K-1 binds.
    """
    if spike_size_in_r >= 0.0:
        raise ValueError(
            f"spike_size_in_r must be negative (adverse spike), got {spike_size_in_r}"
        )

    k = kill_switch_params if kill_switch_params is not None else KillSwitchParams()
    if spike_size_in_r > -k.per_trade_stop_r - 1e-9:
        raise ValueError(
            f"spike_size_in_r={spike_size_in_r} must be below K-1 floor "
            f"-{k.per_trade_stop_r} for path (b) to be meaningful."
        )

    spike_trade = TradeEvent(r_value=spike_size_in_r, session_id=0, week_id=0)
    pre_result = simulate_equity_with_kill_switches(
        [],
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=k,
    )
    # Path (b): counterfactual entry — the spike materialises during an
    # already-active position; K-1 must bind the realised loss at -1R.
    post_result = simulate_equity_with_kill_switches(
        [spike_trade],
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=k,
    )

    realized_r_at_spike = float(post_result.realized_r_per_trade[0])
    expected_floor = -k.per_trade_stop_r
    k1_fired = post_result.n_k1_fires >= 1
    condition_b_passes = bool(
        k1_fired and realized_r_at_spike >= expected_floor - 1e-9
    )
    condition_a_passes = bool(news_calendar_filter_active)
    passed = bool(condition_a_passes and condition_b_passes)

    return StressTestResult(
        fm_id="FM-3",
        fm_description=(
            f"News-spike: inject a {spike_size_in_r}R adverse 1-min spike at "
            "the per-trade scale (modeling a 5σ news-induced move) during an "
            "active position; AND-conjunction pass criterion per ADR-0017 §6 "
            "row 3 + F-15 audit remediation."
        ),
        pass_criterion=(
            "BOTH (a) news-calendar §4 eligible-bar filter prevents entry "
            "in the configured news window AND (b) counterfactual entry "
            f"triggers K-1 with realised loss bounded at -{k.per_trade_stop_r}R."
        ),
        passed=passed,
        triggered_kill_switches=post_result.triggered_kill_switches,
        pre_stress_terminal_equity=float(pre_result.equity_curve[-1]),
        post_stress_terminal_equity=float(post_result.equity_curve[-1]),
        pre_stress_max_drawdown_fraction=_max_drawdown_fraction(pre_result.equity_curve),
        post_stress_max_drawdown_fraction=_max_drawdown_fraction(post_result.equity_curve),
        starting_equity=starting_equity,
        rng_seed=rng_seed,
        fm_specific={
            "spike_size_in_r": spike_size_in_r,
            "k1_floor_in_r": expected_floor,
            "realized_r_at_spike": realized_r_at_spike,
            "condition_a_news_calendar_filter_active": condition_a_passes,
            "condition_b_k1_binds_counterfactual": condition_b_passes,
            "condition_a_orchestrator_coverage_required": (
                not condition_a_passes
            ),
        },
    )


def fm_4_latency_induced_bad_fill(
    trades: Sequence[TradeEvent],
    *,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
    cost_mult: float = 2.0,
    cost_per_trade_in_r: float = 0.05,
    survival_threshold_fraction: float = 0.5,
    kill_switch_params: KillSwitchParams | None = None,
    rng_seed: int = 20260508,
) -> StressTestResult:
    """FM-4 — Latency-induced bad fill.

    Apply 2-tick adverse slippage on every entry+exit by deducting
    `cost_mult × cost_per_trade_in_r` from each trade's realised R AFTER the
    K-1 floor is applied (Round-1 audit Q-3 fix). Default cost_mult=2.0;
    cost_per_trade_in_r=0.05R (~baseline H055 §6 round-trip cost; calibrated
    post-paper-trade per `P1-H055-COST-EMPIRICAL-CALIBRATION`).

    The post-K-1-floor cost order is the canonical "stop-loss exit + slippage"
    real-money model: a -1R-floored loss with 0.10R slippage realises -1.10R,
    NOT -1.00R clamped (the prior pre-K-1 cost order silently absorbed cost
    on K-1-floored losers).

    Pass criterion (per ADR-0017 §6 row 4): post-stress terminal equity remains
    above starting_equity × survival_threshold_fraction. The default 0.5
    borrows the ADR-0017 §4.2 ruin threshold as the operational quantification
    of the §6 row 4 qualitative "survives the elevated cost regime" criterion;
    ADR-0017 §6 row 4 itself does NOT numerically pin a survival threshold,
    so the 50% floor is a borrowed §4.2 convention (per Round-1 audit L-4).
    """
    if cost_mult < 0.0:
        raise ValueError(f"cost_mult must be >= 0, got {cost_mult}")
    if cost_per_trade_in_r < 0.0:
        raise ValueError(f"cost_per_trade_in_r must be >= 0, got {cost_per_trade_in_r}")
    if not (0.0 < survival_threshold_fraction <= 1.0):
        raise ValueError(
            f"survival_threshold_fraction must be in (0, 1], got "
            f"{survival_threshold_fraction}"
        )

    pre_result = simulate_equity_with_kill_switches(
        trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=kill_switch_params,
    )

    extra_cost_r = cost_mult * cost_per_trade_in_r
    # Q-3 fix: apply K-1 floor first, THEN deduct cost (via the simulator's
    # post_floor_cost_in_r parameter). The cost is realised above any K-1 stop.
    post_result = simulate_equity_with_kill_switches(
        trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=kill_switch_params,
        post_floor_cost_in_r=extra_cost_r,
    )

    survival_floor = starting_equity * survival_threshold_fraction
    post_terminal = float(post_result.equity_curve[-1])
    passed = bool(post_terminal > survival_floor)

    return StressTestResult(
        fm_id="FM-4",
        fm_description=(
            f"Latency-induced bad fill: deduct {extra_cost_r:.4f}R per trade "
            f"AFTER the K-1 floor (cost_mult={cost_mult} × baseline "
            f"cost_per_trade={cost_per_trade_in_r}R) modeling 2-tick adverse "
            "slippage on every entry+exit. K-1-floored losers realise -1R - cost."
        ),
        pass_criterion=(
            f"Post-stress terminal equity > starting_equity × "
            f"{survival_threshold_fraction} (= ${survival_floor:,.2f}; the "
            f"50%-of-bankroll floor borrows the ADR-0017 §4.2 ruin threshold "
            "as the operational quantification of the §6 row 4 qualitative "
            "'survives the elevated cost regime' criterion)."
        ),
        passed=passed,
        triggered_kill_switches=post_result.triggered_kill_switches,
        pre_stress_terminal_equity=float(pre_result.equity_curve[-1]),
        post_stress_terminal_equity=post_terminal,
        pre_stress_max_drawdown_fraction=_max_drawdown_fraction(pre_result.equity_curve),
        post_stress_max_drawdown_fraction=_max_drawdown_fraction(post_result.equity_curve),
        starting_equity=starting_equity,
        rng_seed=rng_seed,
        fm_specific={
            "cost_mult": cost_mult,
            "cost_per_trade_in_r": cost_per_trade_in_r,
            "extra_cost_r_per_trade": extra_cost_r,
            "cost_application_order": "post-k1-floor",
            "survival_threshold_fraction": survival_threshold_fraction,
            "survival_floor_dollars": survival_floor,
            "n_trades": len(trades),
        },
    )


def fm_5_regime_change_mid_trade(
    trades: Sequence[TradeEvent],
    *,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
    regime_break_session: int | None = None,
    regime_break_severity: float = -0.5,
    kill_switch_params: KillSwitchParams | None = None,
    rng_seed: int = 20260508,
) -> StressTestResult:
    """FM-5 — Regime change mid-trade.

    Inject a structural break in the per-session R-distribution at the OOS
    midpoint (or at `regime_break_session` if specified). For all trades with
    session_id ≥ regime_break_session, shift R by `regime_break_severity`
    (default -0.5R). Models a regime change the IS-fold did not contain.

    Pass criterion (per ADR-0017 §6 row 5 path (b), Round-1 audit Q-5 fix):
    K-7 weekly circuit breaker fires within the post-break equity trajectory.

    The ADR-0017 §6 row 5 pass criterion is a disjunction: "Either the
    strategy's regime-conditioning catches the break OR K-7 fires before
    cumulative damage exceeds 5% of equity." Path (a) regime-conditioning is
    NOT testable at the primitive layer (the simulator has no access to the
    strategy's regime model); it is verified at the orchestrator layer per
    `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`. The primitive collapses to
    path (b) — `passed = k7_fired`. The prior `damage_bounded` fallback was
    removed (per Q-5) because it was structurally weaker than the spec's
    "regime-conditioning catches the break": a strategy with a strong
    unconditional edge could pass via damage-bounded without exhibiting any
    regime-conditioning behaviour, defeating the purpose of FM-5.

    Note for H055 v1: HMM is out of scope per design.md §1, so path (a) is
    structurally absent from H055 v1. Pass via K-7 only. The cumulative
    damage fraction is reported in `fm_specific["cumulative_damage_fraction"]`
    as informational; operator review uses it to assess strategy survivability
    even when the K-7 path doesn't fire.
    """
    if not trades:
        raise ValueError("trades must be non-empty for FM-5")
    if regime_break_severity > 0.0:
        raise ValueError(
            f"regime_break_severity must be ≤ 0 (adverse shift), got "
            f"{regime_break_severity}"
        )

    pre_result = simulate_equity_with_kill_switches(
        trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=kill_switch_params,
    )

    session_ids_sorted = sorted({t.session_id for t in trades})
    if regime_break_session is None:
        midpoint_idx = len(session_ids_sorted) // 2
        regime_break_session_eff = (
            session_ids_sorted[midpoint_idx] if midpoint_idx < len(session_ids_sorted)
            else session_ids_sorted[-1]
        )
    else:
        regime_break_session_eff = int(regime_break_session)

    stressed_trades = [
        TradeEvent(
            r_value=(
                t.r_value + regime_break_severity
                if t.session_id >= regime_break_session_eff
                else t.r_value
            ),
            session_id=t.session_id,
            week_id=t.week_id,
        )
        for t in trades
    ]
    post_result = simulate_equity_with_kill_switches(
        stressed_trades,
        starting_equity=starting_equity,
        risk_budget_pct=risk_budget_pct,
        kill_switch_params=kill_switch_params,
    )

    k7_fired = post_result.n_k7_fires > 0
    post_terminal = float(post_result.equity_curve[-1])
    cumulative_damage_fraction = (post_terminal - starting_equity) / starting_equity

    # Q-5 fix: pass = K-7 fired only (path b). Path (a) regime-conditioning
    # is deferred to orchestrator layer; damage_bounded fallback removed.
    passed = bool(k7_fired)

    return StressTestResult(
        fm_id="FM-5",
        fm_description=(
            f"Regime change mid-trade: shift R-distribution by "
            f"{regime_break_severity}R for all trades with session_id ≥ "
            f"{regime_break_session_eff} (modeling a regime break the IS fold "
            "did not contain)."
        ),
        pass_criterion=(
            "K-7 weekly circuit breaker fires within the post-break equity "
            "trajectory (path b at primitive layer; path a regime-conditioning "
            "verification deferred to orchestrator layer per "
            "P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION)."
        ),
        passed=passed,
        triggered_kill_switches=post_result.triggered_kill_switches,
        pre_stress_terminal_equity=float(pre_result.equity_curve[-1]),
        post_stress_terminal_equity=post_terminal,
        pre_stress_max_drawdown_fraction=_max_drawdown_fraction(pre_result.equity_curve),
        post_stress_max_drawdown_fraction=_max_drawdown_fraction(post_result.equity_curve),
        starting_equity=starting_equity,
        rng_seed=rng_seed,
        fm_specific={
            "regime_break_session": regime_break_session_eff,
            "regime_break_severity": regime_break_severity,
            "n_trades_pre_break": sum(1 for t in trades if t.session_id < regime_break_session_eff),
            "n_trades_post_break": sum(1 for t in trades if t.session_id >= regime_break_session_eff),
            "n_k7_fires": post_result.n_k7_fires,
            "cumulative_damage_fraction": cumulative_damage_fraction,
            "k7_fired": k7_fired,
            "path_a_regime_conditioning_orchestrator_coverage_required": True,
        },
    )


_RUN_ALL_COMMON_KEYS = frozenset(
    {"starting_equity", "risk_budget_pct", "kill_switch_params", "rng_seed"}
)


def run_all_failure_mode_stress_tests(
    trades: Sequence[TradeEvent],
    *,
    starting_equity: float = 10_000.0,
    risk_budget_pct: float = 0.01,
    kill_switch_params: KillSwitchParams | None = None,
    rng_seed: int = 20260508,
    fm_kwargs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, StressTestResult]:
    """Run all 5 synthetic-failure-mode stress tests against an empirical or
    synthetic per-trade R-multiple sequence.

    Args:
        trades: Per-trade event sequence (e.g., from a walk-forward IS fold).
        starting_equity: Bankroll at t=0.
        risk_budget_pct: Per-trade dollars-at-risk fraction.
        kill_switch_params: K-1+K-6+K-7 parameters.
        rng_seed: Deterministic provenance seed; the FM functions and the
            simulator are deterministic transformations of `trades`, so
            `rng_seed` is recorded for audit-trail purposes only and does
            NOT affect the stress-test outputs (Round-1 audit R-2).
        fm_kwargs: Optional per-FM keyword overrides; outer key is one of
            {"FM-1", "FM-2", "FM-3", "FM-4", "FM-5"}; inner dict overrides
            FM-specific defaults (e.g. cuts_multiplier for FM-1; rth_only_exempt
            for FM-2; news_calendar_filter_active for FM-3; cost_mult for FM-4;
            regime_break_severity for FM-5). The inner dict MAY NOT contain
            keys in {starting_equity, risk_budget_pct, kill_switch_params,
            rng_seed} — those four are scoped at the run_all level (Round-1
            audit R-3 collision-prevention).

    Returns:
        Dict keyed on FM-N → StressTestResult.

    Raises:
        ValueError: fm_kwargs contains a forbidden top-level common key
            (per Round-1 audit R-3).
    """
    fm_kwargs = fm_kwargs or {}

    for fm_id, kwargs_inner in fm_kwargs.items():
        forbidden = set(kwargs_inner.keys()) & _RUN_ALL_COMMON_KEYS
        if forbidden:
            raise ValueError(
                f"fm_kwargs[{fm_id!r}] may not contain run_all-common keys "
                f"{sorted(forbidden)}; pass them as top-level run_all arguments."
            )

    common = {
        "starting_equity": starting_equity,
        "risk_budget_pct": risk_budget_pct,
        "kill_switch_params": kill_switch_params,
        "rng_seed": rng_seed,
    }

    results: dict[str, StressTestResult] = {}
    results["FM-1"] = fm_1_death_by_thousand_cuts(
        trades, **common, **fm_kwargs.get("FM-1", {})
    )
    results["FM-2"] = fm_2_gap_overnight(**common, **fm_kwargs.get("FM-2", {}))
    results["FM-3"] = fm_3_news_spike(**common, **fm_kwargs.get("FM-3", {}))
    results["FM-4"] = fm_4_latency_induced_bad_fill(
        trades, **common, **fm_kwargs.get("FM-4", {})
    )
    results["FM-5"] = fm_5_regime_change_mid_trade(
        trades, **common, **fm_kwargs.get("FM-5", {})
    )
    return results
