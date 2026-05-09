"""Unit tests for ADR-0017 §6 synthetic-failure-mode stress test primitive.

Coverage:
- KillSwitchParams: defaults, validation errors.
- TradeEvent: basic construction.
- simulate_equity_with_kill_switches: empty / winning / losing / K-6 / K-7 /
  halt-skip / cross-session interleaving / validation errors.
- _max_drawdown_fraction: edge cases.
- FM-1 death-by-thousand-cuts: vacuous pass / canonical pass / sum-preservation.
- FM-2 gap-overnight: default -3R / K-1 floor / validation.
- FM-3 news-spike: -2.5R / K-1 floor / validation.
- FM-4 latency-induced-bad-fill: surviving strategy / failing strategy / validation.
- FM-5 regime-change-mid-trade: midpoint break / explicit break / K-7 path.
- run_all_failure_mode_stress_tests: smoke test on synthetic input.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.backtest.stress_test import (
    KillSwitchParams,
    KillSwitchSimulationResult,
    StressTestResult,
    TradeEvent,
    _max_drawdown_fraction,
    fm_1_death_by_thousand_cuts,
    fm_2_gap_overnight,
    fm_3_news_spike,
    fm_4_latency_induced_bad_fill,
    fm_5_regime_change_mid_trade,
    run_all_failure_mode_stress_tests,
    simulate_equity_with_kill_switches,
)


# ─── KillSwitchParams ────────────────────────────────────────────────────────


def test_kill_switch_params_defaults_match_h055_section_11_1() -> None:
    k = KillSwitchParams()
    assert k.per_trade_stop_r == 1.0
    assert k.daily_circuit_breaker_fraction == -0.02
    assert k.weekly_circuit_breaker_fraction == -0.05


def test_kill_switch_params_rejects_nonpositive_per_trade_stop() -> None:
    with pytest.raises(ValueError, match="per_trade_stop_r"):
        KillSwitchParams(per_trade_stop_r=0.0)
    with pytest.raises(ValueError, match="per_trade_stop_r"):
        KillSwitchParams(per_trade_stop_r=-0.5)


def test_kill_switch_params_rejects_positive_daily_breaker() -> None:
    with pytest.raises(ValueError, match="daily_circuit_breaker_fraction"):
        KillSwitchParams(daily_circuit_breaker_fraction=0.0)
    with pytest.raises(ValueError, match="daily_circuit_breaker_fraction"):
        KillSwitchParams(daily_circuit_breaker_fraction=0.05)


def test_kill_switch_params_rejects_positive_weekly_breaker() -> None:
    with pytest.raises(ValueError, match="weekly_circuit_breaker_fraction"):
        KillSwitchParams(weekly_circuit_breaker_fraction=0.0)


def test_kill_switch_params_immutable_frozen() -> None:
    k = KillSwitchParams()
    with pytest.raises(Exception):
        k.per_trade_stop_r = 0.5  # type: ignore[misc]


# ─── TradeEvent ──────────────────────────────────────────────────────────────


def test_trade_event_construction() -> None:
    t = TradeEvent(r_value=0.5, session_id=3, week_id=0)
    assert t.r_value == 0.5
    assert t.session_id == 3
    assert t.week_id == 0


# ─── _max_drawdown_fraction ──────────────────────────────────────────────────


def test_max_drawdown_empty_curve_returns_zero() -> None:
    assert _max_drawdown_fraction(np.array([])) == 0.0


def test_max_drawdown_single_element_returns_zero() -> None:
    assert _max_drawdown_fraction(np.array([10_000.0])) == 0.0


def test_max_drawdown_monotone_increasing_returns_zero() -> None:
    curve = np.array([10_000.0, 10_500.0, 11_000.0, 11_500.0])
    assert _max_drawdown_fraction(curve) == 0.0


def test_max_drawdown_canonical() -> None:
    # Peak 12000, trough 9000 → max DD = -0.25
    curve = np.array([10_000.0, 12_000.0, 11_000.0, 9_000.0, 10_500.0])
    dd = _max_drawdown_fraction(curve)
    assert dd == pytest.approx(-0.25)


# ─── simulate_equity_with_kill_switches ──────────────────────────────────────


def test_simulator_empty_trades() -> None:
    res = simulate_equity_with_kill_switches([], starting_equity=10_000.0)
    assert isinstance(res, KillSwitchSimulationResult)
    assert res.equity_curve.shape == (1,)
    assert res.equity_curve[0] == 10_000.0
    assert res.realized_r_per_trade.shape == (0,)
    assert res.triggered_kill_switches == ()
    assert res.n_k1_fires == 0
    assert res.n_k6_fires == 0
    assert res.n_k7_fires == 0


def test_simulator_winning_strategy_no_kill_switches() -> None:
    trades = [TradeEvent(r_value=0.5, session_id=i, week_id=0) for i in range(20)]
    res = simulate_equity_with_kill_switches(trades, starting_equity=10_000.0)
    assert res.n_k1_fires == 0
    assert res.n_k6_fires == 0
    assert res.n_k7_fires == 0
    assert res.triggered_kill_switches == ()
    # 1% risk budget × 0.5R = 0.5% growth per trade compounded over 20 trades
    expected = 10_000.0 * (1.005 ** 20)
    assert res.equity_curve[-1] == pytest.approx(expected, rel=1e-9)


def test_simulator_k1_floor_clamps_below_negative_stop() -> None:
    # raw R = -3 → floored at -1R
    trades = [TradeEvent(r_value=-3.0, session_id=0, week_id=0)]
    res = simulate_equity_with_kill_switches(trades, starting_equity=10_000.0)
    assert res.realized_r_per_trade[0] == -1.0
    assert res.n_k1_fires == 1
    # PnL = -1.0 × 0.01 × 10000 = -100 → equity = 9900
    assert res.equity_curve[-1] == pytest.approx(9_900.0)


def test_simulator_k6_fires_on_session_loss_exceeding_2pct() -> None:
    # 3 losing -1R trades in same session: cumulative session PnL after each
    # trade: -100, -199, -297.01 (compounded). Threshold = -200 at session start
    # 10000 (i.e., -2% of 10000). K-6 should fire on trade 3.
    trades = [TradeEvent(r_value=-1.0, session_id=0, week_id=0) for _ in range(3)]
    res = simulate_equity_with_kill_switches(trades, starting_equity=10_000.0)
    assert res.n_k6_fires == 1
    assert 0 in res.halted_sessions
    assert "K-6" in res.triggered_kill_switches


def test_simulator_k6_halt_skips_subsequent_session_trades() -> None:
    # 3 -1R trades to trigger K-6 on session 0; then 2 more -1R trades in
    # same session 0 should be skipped.
    trades = [TradeEvent(r_value=-1.0, session_id=0, week_id=0) for _ in range(5)]
    res = simulate_equity_with_kill_switches(trades, starting_equity=10_000.0)
    assert res.n_trades_skipped == 2
    # Realized R for trades 3, 4 (post-halt) = 0.0
    assert res.realized_r_per_trade[3] == 0.0
    assert res.realized_r_per_trade[4] == 0.0


def test_simulator_k6_resets_across_sessions() -> None:
    # 2 -1R trades in session 0 (no K-6 yet — cumulative -200 = exactly -2%
    # threshold; using <= triggers at the boundary).
    # Then 2 winning trades in session 1 (different session_id).
    trades = [
        TradeEvent(r_value=-0.99, session_id=0, week_id=0),
        TradeEvent(r_value=-0.99, session_id=0, week_id=0),
        TradeEvent(r_value=0.5, session_id=1, week_id=0),
        TradeEvent(r_value=0.5, session_id=1, week_id=0),
    ]
    res = simulate_equity_with_kill_switches(trades, starting_equity=10_000.0)
    # Session 0 cumulative: -99 - ~98 = -197 at session-0 start equity 10000
    # Frac = -0.0197 > -0.02 → K-6 does NOT fire on session 0.
    assert res.n_k6_fires == 0
    # All 4 trades execute (no halt)
    assert res.n_trades_skipped == 0


def test_simulator_k7_fires_on_weekly_loss_exceeding_5pct() -> None:
    # Need cumulative weekly PnL ≤ -5% × week-start equity. With risk_budget_pct
    # = 0.01 and -1R losses → 1% loss per trade. To reach -5% weekly, need at
    # least 5 -1R trades. But K-6 will fire first within a session. So spread
    # losses across multiple sessions in same week.
    trades = [
        TradeEvent(r_value=-1.0, session_id=i, week_id=0) for i in range(6)
    ]
    res = simulate_equity_with_kill_switches(trades, starting_equity=10_000.0)
    assert res.n_k7_fires == 1
    assert 0 in res.halted_weeks
    assert "K-7" in res.triggered_kill_switches


def test_simulator_validates_starting_equity() -> None:
    with pytest.raises(ValueError, match="starting_equity"):
        simulate_equity_with_kill_switches([], starting_equity=0.0)
    with pytest.raises(ValueError, match="starting_equity"):
        simulate_equity_with_kill_switches([], starting_equity=-100.0)


def test_simulator_validates_risk_budget_pct() -> None:
    with pytest.raises(ValueError, match="risk_budget_pct"):
        simulate_equity_with_kill_switches([], risk_budget_pct=0.0)
    with pytest.raises(ValueError, match="risk_budget_pct"):
        simulate_equity_with_kill_switches([], risk_budget_pct=1.5)
    with pytest.raises(ValueError, match="risk_budget_pct"):
        simulate_equity_with_kill_switches([], risk_budget_pct=-0.01)


def test_simulator_post_floor_cost_applied_after_k1_floor() -> None:
    # Q-3 fix verification: cost is applied AFTER K-1 floor. A -3R raw event
    # is floored to -1R; with post_floor_cost_in_r=0.10, realised = -1.10R.
    trades = [TradeEvent(r_value=-3.0, session_id=0, week_id=0)]
    res = simulate_equity_with_kill_switches(
        trades, starting_equity=10_000.0, post_floor_cost_in_r=0.10
    )
    assert res.realized_r_per_trade[0] == pytest.approx(-1.10)
    assert res.n_k1_fires == 1
    # Realized PnL = -1.10R × 0.01 × 10000 = -110 → equity = 9890
    assert res.equity_curve[-1] == pytest.approx(9_890.0)


def test_simulator_post_floor_cost_zero_default_unchanged() -> None:
    trades = [TradeEvent(r_value=-3.0, session_id=0, week_id=0)]
    a = simulate_equity_with_kill_switches(trades, starting_equity=10_000.0)
    b = simulate_equity_with_kill_switches(
        trades, starting_equity=10_000.0, post_floor_cost_in_r=0.0
    )
    assert a.realized_r_per_trade[0] == b.realized_r_per_trade[0] == -1.0


def test_simulator_validates_negative_post_floor_cost() -> None:
    with pytest.raises(ValueError, match="post_floor_cost_in_r"):
        simulate_equity_with_kill_switches([], post_floor_cost_in_r=-0.05)


def test_simulator_current_equity_rebases_dollars_at_risk() -> None:
    # ADR-0017 §4.1 binding: dollars_at_risk = risk_budget_pct × CURRENT equity.
    # With initial equity 10000 and risk_budget_pct=0.01: first +1R trade
    # produces +$100 (PnL=1.0 × 0.01 × 10000=100), equity → 10100.
    # Second +1R trade produces +$101 (PnL=1.0 × 0.01 × 10100=101), equity → 10201.
    trades = [
        TradeEvent(r_value=1.0, session_id=0, week_id=0),
        TradeEvent(r_value=1.0, session_id=1, week_id=1),
    ]
    res = simulate_equity_with_kill_switches(trades, starting_equity=10_000.0)
    assert res.equity_curve[1] == pytest.approx(10_100.0)
    assert res.equity_curve[2] == pytest.approx(10_201.0)


# ─── FM-1 death-by-thousand-cuts ─────────────────────────────────────────────


def test_fm_1_returns_dataclass() -> None:
    trades = [TradeEvent(r_value=-1.0, session_id=i, week_id=0) for i in range(3)]
    res = fm_1_death_by_thousand_cuts(trades, starting_equity=10_000.0)
    assert isinstance(res, StressTestResult)
    assert res.fm_id == "FM-1"


def test_fm_1_vacuous_pass_when_no_session_loss_exceeds_2pct() -> None:
    # All winning trades → no K-6 trigger condition exists.
    trades = [TradeEvent(r_value=0.5, session_id=i, week_id=0) for i in range(10)]
    res = fm_1_death_by_thousand_cuts(trades, starting_equity=10_000.0)
    assert res.passed is True
    assert res.fm_specific["vacuous_pass"] is True
    assert res.fm_specific["n_k6_fires_post"] == 0


def test_fm_1_canonical_pass_when_k6_demonstrably_catches_damage() -> None:
    # 3 losing -1R trades in same session → K-6 fires on stressed sequence;
    # kill-switch-active terminal equity > no-kill-switch counterfactual.
    trades = [TradeEvent(r_value=-1.0, session_id=0, week_id=0) for _ in range(3)]
    res = fm_1_death_by_thousand_cuts(trades, cuts_multiplier=4)
    assert res.passed is True
    assert res.fm_specific["vacuous_pass"] is False
    assert res.fm_specific["k6_demonstrably_caught_damage"] is True
    assert res.fm_specific["n_k6_fires_post"] >= 1
    assert (
        res.post_stress_terminal_equity > res.fm_specific["no_kss_terminal_equity"]
    )


def test_fm_1_r_multiple_sum_preserved_with_compounding_discrepancy() -> None:
    # Single -1R loss in isolated session/week. No K-6 firing.
    # Per Q-6 fix: the substitution preserves R-multiple sums but $-loss
    # compounds with O(risk_budget_pct² × cuts) discrepancy. Pre = 9900;
    # post compounds 4 small losses at current-equity rebase.
    trades = [TradeEvent(r_value=-1.0, session_id=0, week_id=0)]
    res = fm_1_death_by_thousand_cuts(trades, cuts_multiplier=4, starting_equity=10_000.0)
    assert res.fm_specific["n_pre_stress_trades"] == 1
    assert res.fm_specific["n_post_stress_trades"] == 4
    assert res.pre_stress_terminal_equity == pytest.approx(9_900.0)
    expected = 10_000.0 * ((1.0 - 0.01 / 4) ** 4)
    assert res.post_stress_terminal_equity == pytest.approx(expected, rel=1e-6)
    # The discrepancy is in the conservative direction: post > pre (less damage).
    assert res.post_stress_terminal_equity > res.pre_stress_terminal_equity


def test_fm_1_cuts_multiplier_validation() -> None:
    with pytest.raises(ValueError, match="cuts_multiplier"):
        fm_1_death_by_thousand_cuts([], cuts_multiplier=0)
    with pytest.raises(ValueError, match="cuts_multiplier"):
        fm_1_death_by_thousand_cuts([], cuts_multiplier=-1)


def test_fm_1_cuts_multiplier_one_is_noop() -> None:
    trades = [
        TradeEvent(r_value=-0.5, session_id=0, week_id=0),
        TradeEvent(r_value=0.5, session_id=0, week_id=0),
    ]
    res = fm_1_death_by_thousand_cuts(trades, cuts_multiplier=1)
    assert res.fm_specific["n_pre_stress_trades"] == 2
    assert res.fm_specific["n_post_stress_trades"] == 2


# ─── FM-2 gap-overnight ──────────────────────────────────────────────────────


def test_fm_2_rth_only_exempt_default_passes_trivially() -> None:
    # H055 v1 is RTH-only per design.md §1; FM-2 is exempt by construction
    # per ADR-0017 §6 row 2 closing parenthetical.
    res = fm_2_gap_overnight(starting_equity=10_000.0)
    assert res.fm_id == "FM-2"
    assert res.passed is True
    assert res.fm_specific["exempt_reason"] == "rth-only-mandate"
    assert res.post_stress_terminal_equity == 10_000.0  # no equity event
    assert res.triggered_kill_switches == ()


def test_fm_2_overnight_strategy_passes_with_session_boundary_force_close() -> None:
    res = fm_2_gap_overnight(
        gap_size_in_r=-3.0,
        rth_only_exempt=False,
        session_boundary_mtm_force_close_R=-1.0,
    )
    assert res.passed is True
    assert res.fm_specific["force_close_fired"] is True
    assert res.fm_specific["realized_r_at_force_close"] == -1.0
    assert "session-boundary-MTM-force-close" in res.triggered_kill_switches
    # Realized loss = -1R × 0.01 × 10000 = -100 → equity = 9900
    assert res.post_stress_terminal_equity == pytest.approx(9_900.0)


def test_fm_2_overnight_strategy_requires_force_close_threshold() -> None:
    with pytest.raises(ValueError, match="session_boundary_mtm_force_close_R"):
        fm_2_gap_overnight(rth_only_exempt=False, gap_size_in_r=-3.0)


def test_fm_2_validates_positive_gap_size() -> None:
    with pytest.raises(ValueError, match="gap_size_in_r"):
        fm_2_gap_overnight(gap_size_in_r=2.0)


def test_fm_2_validates_gap_above_force_close_threshold_meaningless() -> None:
    # Overnight strategy: gap of -0.5 is above the force-close trigger -1.0
    # → force-close doesn't fire → test meaningless.
    with pytest.raises(ValueError, match="force-close"):
        fm_2_gap_overnight(
            gap_size_in_r=-0.5,
            rth_only_exempt=False,
            session_boundary_mtm_force_close_R=-1.0,
        )


def test_fm_2_validates_positive_force_close_threshold() -> None:
    with pytest.raises(ValueError, match="session_boundary_mtm_force_close_R"):
        fm_2_gap_overnight(
            gap_size_in_r=-3.0,
            rth_only_exempt=False,
            session_boundary_mtm_force_close_R=1.0,
        )


# ─── FM-3 news-spike ─────────────────────────────────────────────────────────


def test_fm_3_default_fails_when_orchestrator_filter_not_active() -> None:
    # Without news_calendar_filter_active=True, the AND-conjunction cannot
    # be satisfied at the primitive layer (path (a) is not verified).
    res = fm_3_news_spike(starting_equity=10_000.0)
    assert res.fm_id == "FM-3"
    assert res.passed is False
    assert res.fm_specific["condition_a_news_calendar_filter_active"] is False
    assert res.fm_specific["condition_b_k1_binds_counterfactual"] is True
    assert res.fm_specific["condition_a_orchestrator_coverage_required"] is True
    assert res.fm_specific["realized_r_at_spike"] == -1.0


def test_fm_3_passes_when_both_conditions_satisfied() -> None:
    # When the orchestrator layer has wired the news-calendar §4 eligible-bar
    # filter, the primitive can be told via news_calendar_filter_active=True.
    res = fm_3_news_spike(news_calendar_filter_active=True)
    assert res.passed is True
    assert res.fm_specific["condition_a_news_calendar_filter_active"] is True
    assert res.fm_specific["condition_b_k1_binds_counterfactual"] is True


def test_fm_3_validates_positive_spike_size() -> None:
    with pytest.raises(ValueError, match="spike_size_in_r"):
        fm_3_news_spike(spike_size_in_r=2.0)


def test_fm_3_validates_spike_above_k1_floor_meaningless() -> None:
    with pytest.raises(ValueError, match="K-1 floor"):
        fm_3_news_spike(spike_size_in_r=-0.5)


# ─── FM-4 latency-induced bad fill ───────────────────────────────────────────


def test_fm_4_strong_strategy_survives_default_cost_mult() -> None:
    # 100 winning +1R trades in 100 distinct sessions → strong positive edge.
    # Even with 2× cost = 0.10R per trade, net = +0.90R per trade → terminal
    # equity well above starting × 0.5.
    trades = [TradeEvent(r_value=1.0, session_id=i, week_id=i // 5) for i in range(100)]
    res = fm_4_latency_induced_bad_fill(trades, starting_equity=10_000.0)
    assert res.fm_id == "FM-4"
    assert res.passed is True
    assert res.post_stress_terminal_equity > 5_000.0


def test_fm_4_marginal_strategy_fails_with_elevated_cost() -> None:
    # 100 marginal +0.05R trades → net 0R after 2× × 0.05R cost. Equity
    # stays roughly flat. With 4× cost mult and 0.05R baseline cost,
    # extra cost = 0.20R per trade → net -0.15R → equity decays.
    # Drop below 0.5 × starting (= 5000) requires log-decay rate ≈ ln(0.5)/100
    # ≈ -0.0069 per trade, or per-trade R ≈ -0.69. Net R = -0.15 × 0.01 = -0.0015
    # per trade → 100 × -0.0015 = -15% (compounded) ≈ -14% terminal. Doesn't
    # cross -50%. So this test needs more aggressive parameters.
    trades = [TradeEvent(r_value=0.05, session_id=i, week_id=i // 5) for i in range(200)]
    res = fm_4_latency_induced_bad_fill(
        trades, cost_mult=10.0, cost_per_trade_in_r=0.5
    )
    # extra cost per trade = 5R. After K-1 floor each post-stress trade is
    # bounded at -1R. 200 × -1R × 0.01 = compound down 86%. → equity ~1400 < 5000.
    assert res.post_stress_terminal_equity < 5_000.0
    assert res.passed is False


def test_fm_4_validates_negative_cost_mult() -> None:
    with pytest.raises(ValueError, match="cost_mult"):
        fm_4_latency_induced_bad_fill([], cost_mult=-1.0)


def test_fm_4_validates_negative_cost_per_trade() -> None:
    with pytest.raises(ValueError, match="cost_per_trade_in_r"):
        fm_4_latency_induced_bad_fill([], cost_per_trade_in_r=-0.01)


def test_fm_4_validates_survival_threshold_range() -> None:
    with pytest.raises(ValueError, match="survival_threshold_fraction"):
        fm_4_latency_induced_bad_fill([], survival_threshold_fraction=0.0)
    with pytest.raises(ValueError, match="survival_threshold_fraction"):
        fm_4_latency_induced_bad_fill([], survival_threshold_fraction=1.5)


# ─── FM-5 regime-change-mid-trade ────────────────────────────────────────────


def test_fm_5_default_midpoint_break_fails_when_k7_does_not_fire() -> None:
    # Q-5 fix: pass criterion at primitive layer is K-7 fired. With +0.5R wins
    # pre-break and (0.5 - 0.5) = 0R post-break, no damage accumulates and K-7
    # has nothing to fire on; primitive-layer passed=False. Path (a)
    # regime-conditioning is deferred to orchestrator-layer per
    # P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION.
    trades = [
        TradeEvent(r_value=0.5, session_id=i, week_id=i // 5) for i in range(20)
    ]
    res = fm_5_regime_change_mid_trade(trades, starting_equity=10_000.0)
    assert res.fm_id == "FM-5"
    assert res.fm_specific["n_trades_pre_break"] == 10
    assert res.fm_specific["n_trades_post_break"] == 10
    assert res.passed is False
    assert res.fm_specific["k7_fired"] is False
    assert (
        res.fm_specific["path_a_regime_conditioning_orchestrator_coverage_required"]
        is True
    )


def test_fm_5_explicit_break_session() -> None:
    trades = [TradeEvent(r_value=0.5, session_id=i, week_id=i // 5) for i in range(20)]
    res = fm_5_regime_change_mid_trade(
        trades, regime_break_session=15, regime_break_severity=-0.3
    )
    # 15 trades pre-break, 5 trades post-break
    assert res.fm_specific["n_trades_pre_break"] == 15
    assert res.fm_specific["n_trades_post_break"] == 5
    assert res.fm_specific["regime_break_session"] == 15


def test_fm_5_fails_when_per_week_loss_falls_just_short_of_k7_threshold() -> None:
    # Substantive finding (NOT a simulator bug): with per-trade K-1 floor of
    # -1R and risk_budget_pct=0.01, 5 -1R trades per week produce
    # 1 - 0.99^5 ≈ -4.9% weekly drawdown — just above the K-7 -5% threshold.
    # K-7 does not fire within any single week, but cumulative damage across
    # 4 post-break weeks (0.99^20) ≈ -18.2%, well past the 5% damage envelope.
    # Stress test correctly returns passed=False (K-7 path b is unmet); the
    # cumulative damage is reported in fm_specific as informational.
    trades = [
        TradeEvent(r_value=0.0, session_id=i, week_id=i // 5) for i in range(40)
    ]
    res = fm_5_regime_change_mid_trade(
        trades, regime_break_severity=-1.5, regime_break_session=20
    )
    assert res.passed is False
    assert res.fm_specific["k7_fired"] is False
    assert res.fm_specific["cumulative_damage_fraction"] < -0.05


def test_fm_5_k7_path_passes_when_break_severe_enough_to_fire_k7() -> None:
    # Bumping risk_budget_pct to 0.02: each -1R trade = -2% of current equity.
    # 3 trades into a week of post-break -1R losses, cumulative weekly drawdown
    # crosses -5% → K-7 fires.
    trades = [
        TradeEvent(r_value=0.0, session_id=i, week_id=i // 5) for i in range(40)
    ]
    res = fm_5_regime_change_mid_trade(
        trades,
        regime_break_severity=-1.5,
        regime_break_session=20,
        risk_budget_pct=0.02,
    )
    assert res.fm_specific["k7_fired"] is True
    assert res.passed is True


def test_fm_5_validates_empty_trades() -> None:
    with pytest.raises(ValueError, match="trades must be non-empty"):
        fm_5_regime_change_mid_trade([])


def test_fm_5_validates_positive_severity() -> None:
    with pytest.raises(ValueError, match="regime_break_severity"):
        fm_5_regime_change_mid_trade(
            [TradeEvent(r_value=0.5, session_id=0, week_id=0)],
            regime_break_severity=0.5,
        )


# ─── run_all_failure_mode_stress_tests ───────────────────────────────────────


def test_run_all_returns_five_keys() -> None:
    rng = np.random.default_rng(42)
    # Synthetic +0.5R-mean strategy; 50 trades over 10 weeks
    trades = [
        TradeEvent(
            r_value=float(rng.normal(0.5, 1.0)),
            session_id=i,
            week_id=i // 5,
        )
        for i in range(50)
    ]
    results = run_all_failure_mode_stress_tests(trades, starting_equity=10_000.0)
    assert set(results.keys()) == {"FM-1", "FM-2", "FM-3", "FM-4", "FM-5"}
    for fm_id, result in results.items():
        assert isinstance(result, StressTestResult)
        assert result.fm_id == fm_id


def test_run_all_per_fm_kwargs_override() -> None:
    trades = [TradeEvent(r_value=0.1, session_id=i, week_id=i // 5) for i in range(20)]
    results = run_all_failure_mode_stress_tests(
        trades,
        fm_kwargs={
            "FM-1": {"cuts_multiplier": 8},
            "FM-2": {"gap_size_in_r": -5.0},
            "FM-3": {"spike_size_in_r": -10.0},
            "FM-4": {"cost_mult": 1.5},
            "FM-5": {"regime_break_severity": -0.2},
        },
    )
    assert results["FM-1"].fm_specific["cuts_multiplier"] == 8
    assert results["FM-2"].fm_specific["gap_size_in_r"] == -5.0
    assert results["FM-3"].fm_specific["spike_size_in_r"] == -10.0
    assert results["FM-4"].fm_specific["cost_mult"] == 1.5
    assert results["FM-5"].fm_specific["regime_break_severity"] == -0.2


def test_run_all_rejects_common_keys_in_fm_kwargs() -> None:
    # R-3 fix: caller cannot pass run_all-common keys via the per-FM nested dict.
    trades = [TradeEvent(r_value=0.0, session_id=0, week_id=0)]
    with pytest.raises(ValueError, match="run_all-common keys"):
        run_all_failure_mode_stress_tests(
            trades, fm_kwargs={"FM-1": {"rng_seed": 99}}
        )
    with pytest.raises(ValueError, match="run_all-common keys"):
        run_all_failure_mode_stress_tests(
            trades, fm_kwargs={"FM-2": {"starting_equity": 5_000.0}}
        )


def test_run_all_deterministic_under_fixed_seed() -> None:
    trades = [TradeEvent(r_value=0.1, session_id=i, week_id=i // 5) for i in range(50)]
    a = run_all_failure_mode_stress_tests(trades, rng_seed=42)
    b = run_all_failure_mode_stress_tests(trades, rng_seed=42)
    for fm_id in a:
        assert a[fm_id].passed == b[fm_id].passed
        assert a[fm_id].post_stress_terminal_equity == b[fm_id].post_stress_terminal_equity
