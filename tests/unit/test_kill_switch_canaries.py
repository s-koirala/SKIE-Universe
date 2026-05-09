"""Unit tests for ADR-0017 §5 kill-switch backtest validation canary primitive.

Coverage:
- TradeLedgerEntry: basic construction.
- KillSwitchCanaryResult: dataclass.
- Per-K validators: K-1, K-2, K-3, K-4, K-5, K-6, K-7, K-8 (pass + violation cases).
- validate_kill_switches_per_fold: orchestration; deferred-metadata handling;
  pass/fail annotations.
"""

from __future__ import annotations

import pytest

from skie_ninja.backtest.kill_switch_canaries import (
    KillSwitchCanaryResult,
    TradeLedgerEntry,
    validate_k1_per_trade_stop,
    validate_k2_per_trade_time_stop,
    validate_k3_no_add_to_loser,
    validate_k4_per_symbol_position_cap,
    validate_k5_correlated_inventory_cap,
    validate_k6_daily_circuit_breaker,
    validate_k7_weekly_circuit_breaker,
    validate_k8_adverse_direction_filter,
    validate_kill_switches_per_fold,
)
from skie_ninja.backtest.stress_test import KillSwitchParams


def _make_entry(
    *,
    instrument: str = "ES",
    session_id: int = 0,
    week_id: int = 0,
    open_ns: int = 0,
    close_ns: int = 60_000_000_000,
    r_value: float = 0.5,
    position_size: int = 1,
    position_direction: int = 1,
    entry_bar_open_price: float = 5_000.0,
    fill_price: float = 5_000.0,
    atr_at_entry: float = 5.0,
    multiplier: float = 50.0,
    correlated_group: str | None = None,
    trigger_t_h_sign: int | None = None,
) -> TradeLedgerEntry:
    return TradeLedgerEntry(
        instrument=instrument,
        session_id=session_id,
        week_id=week_id,
        open_timestamp_ns=open_ns,
        close_timestamp_ns=close_ns,
        r_value=r_value,
        position_size=position_size,
        position_direction=position_direction,
        entry_bar_open_price=entry_bar_open_price,
        fill_price=fill_price,
        atr_at_entry=atr_at_entry,
        multiplier=multiplier,
        correlated_group=correlated_group,
        trigger_t_h_sign=trigger_t_h_sign,
    )


# ─── K-1 per-trade $-stop ────────────────────────────────────────────────────


def test_k1_passes_with_floored_losses() -> None:
    ledger = [_make_entry(r_value=-1.0), _make_entry(r_value=-0.99), _make_entry(r_value=0.5)]
    p, v = validate_k1_per_trade_stop(ledger, kill_switch_params=KillSwitchParams())
    assert p is True
    assert v == ()


def test_k1_fails_on_below_floor_loss() -> None:
    ledger = [_make_entry(r_value=-1.5), _make_entry(r_value=0.5)]
    p, v = validate_k1_per_trade_stop(ledger, kill_switch_params=KillSwitchParams())
    assert p is False
    assert v == (0,)


def test_k1_respects_custom_floor() -> None:
    k = KillSwitchParams(per_trade_stop_r=0.5)
    ledger = [_make_entry(r_value=-0.4), _make_entry(r_value=-0.6)]
    p, v = validate_k1_per_trade_stop(ledger, kill_switch_params=k)
    assert p is False
    assert v == (1,)


# ─── K-2 per-trade time-stop ─────────────────────────────────────────────────


def test_k2_passes_within_time_stop() -> None:
    # 30 min = 1.8e12 ns; trade at 1 min OK
    ledger = [_make_entry(r_value=-0.5, open_ns=0, close_ns=60_000_000_000)]
    p, v = validate_k2_per_trade_time_stop(ledger, per_trade_time_stop_min=30.0)
    assert p is True
    assert v == ()


def test_k2_fails_on_loser_exceeding_time_stop() -> None:
    # 60 min = 3.6e12 ns > 30 min threshold
    ledger = [_make_entry(r_value=-0.5, open_ns=0, close_ns=3_600_000_000_000)]
    p, v = validate_k2_per_trade_time_stop(ledger, per_trade_time_stop_min=30.0)
    assert p is False
    assert v == (0,)


def test_k2_exempts_winning_trades_from_time_stop() -> None:
    # Winner with same 60 min duration — exempt.
    ledger = [_make_entry(r_value=+0.5, open_ns=0, close_ns=3_600_000_000_000)]
    p, v = validate_k2_per_trade_time_stop(ledger, per_trade_time_stop_min=30.0)
    assert p is True
    assert v == ()


# ─── K-3 no-add-to-loser ─────────────────────────────────────────────────────


def test_k3_passes_with_non_overlapping_trades() -> None:
    ledger = [
        _make_entry(open_ns=0, close_ns=60_000_000_000),
        _make_entry(open_ns=120_000_000_000, close_ns=180_000_000_000),
    ]
    p, v = validate_k3_no_add_to_loser(ledger)
    assert p is True
    assert v == ()


def test_k3_fails_on_overlapping_same_direction_same_instrument() -> None:
    # Both ES long positions overlapping
    ledger = [
        _make_entry(open_ns=0, close_ns=60_000_000_000, position_direction=1),
        _make_entry(open_ns=30_000_000_000, close_ns=90_000_000_000, position_direction=1),
    ]
    p, v = validate_k3_no_add_to_loser(ledger)
    assert p is False
    assert 1 in v


def test_k3_passes_on_different_instruments_overlap() -> None:
    ledger = [
        _make_entry(instrument="ES", open_ns=0, close_ns=60_000_000_000),
        _make_entry(instrument="NQ", open_ns=30_000_000_000, close_ns=90_000_000_000),
    ]
    p, v = validate_k3_no_add_to_loser(ledger)
    assert p is True


def test_k3_passes_on_opposite_direction_overlap() -> None:
    # Long + short overlap on same instrument — not "adding to loser"
    ledger = [
        _make_entry(open_ns=0, close_ns=60_000_000_000, position_direction=1),
        _make_entry(open_ns=30_000_000_000, close_ns=90_000_000_000, position_direction=-1),
    ]
    p, v = validate_k3_no_add_to_loser(ledger)
    assert p is True


# ─── K-4 per-symbol position cap ─────────────────────────────────────────────


def test_k4_passes_under_cap_running_position() -> None:
    # Single trade well under cap; running position never exceeds 10.
    ledger = [_make_entry(instrument="ES", position_size=10)]
    p, v = validate_k4_per_symbol_position_cap(ledger, per_symbol_caps={"ES": 20})
    assert p is True


def test_k4_fails_above_cap_single_trade() -> None:
    # Single trade > cap.
    ledger = [_make_entry(instrument="ES", position_size=25)]
    p, v = validate_k4_per_symbol_position_cap(ledger, per_symbol_caps={"ES": 20})
    assert p is False
    assert v == (0,)


def test_k4_fails_on_concurrent_positions_exceeding_running_cap() -> None:
    # Q-4 fix: K-4 is a running portfolio cap, NOT per-trade. Two overlapping
    # ES trades of 10 + 15 = 25 running position exceeds the 20 cap; the
    # SECOND trade is the trigger.
    bar_ns = 60_000_000_000
    ledger = [
        _make_entry(
            instrument="ES",
            position_size=10,
            open_ns=0,
            close_ns=10 * bar_ns,
        ),
        _make_entry(
            instrument="ES",
            position_size=15,
            open_ns=2 * bar_ns,
            close_ns=12 * bar_ns,
        ),
    ]
    p, v = validate_k4_per_symbol_position_cap(ledger, per_symbol_caps={"ES": 20})
    assert p is False
    assert v == (1,)


def test_k4_passes_when_overlapping_below_running_cap() -> None:
    # Two overlapping ES trades of 5 + 10 = 15 running, cap=20: pass.
    bar_ns = 60_000_000_000
    ledger = [
        _make_entry(instrument="ES", position_size=5, open_ns=0, close_ns=10 * bar_ns),
        _make_entry(instrument="ES", position_size=10, open_ns=2 * bar_ns, close_ns=12 * bar_ns),
    ]
    p, v = validate_k4_per_symbol_position_cap(ledger, per_symbol_caps={"ES": 20})
    assert p is True


def test_k4_skips_unknown_instrument() -> None:
    ledger = [_make_entry(instrument="UNKNOWN", position_size=99)]
    p, v = validate_k4_per_symbol_position_cap(ledger, per_symbol_caps={"ES": 20})
    assert p is True


# ─── K-5 correlated-instrument inventory cap ─────────────────────────────────


def test_k5_passes_under_group_cap() -> None:
    # ES at 5000 × 50 × 1 contract = $250K; cap = $1M
    ledger = [
        _make_entry(
            instrument="ES",
            position_size=1,
            multiplier=50.0,
            fill_price=5000.0,
            correlated_group="ES_MES",
        )
    ]
    p, v = validate_k5_correlated_inventory_cap(
        ledger, correlated_group_caps={"ES_MES": 1_000_000.0}
    )
    assert p is True


def test_k5_fails_on_concurrent_group_exceedance() -> None:
    # Two ES at 5000 × 50 × 5 contracts = $1.25M each. Concurrent → $2.5M > $1M cap.
    ledger = [
        _make_entry(
            instrument="ES",
            position_size=5,
            multiplier=50.0,
            fill_price=5000.0,
            correlated_group="ES_MES",
            open_ns=0,
            close_ns=60_000_000_000,
        ),
        _make_entry(
            instrument="MES",
            position_size=50,
            multiplier=5.0,
            fill_price=5000.0,
            correlated_group="ES_MES",
            open_ns=30_000_000_000,
            close_ns=90_000_000_000,
        ),
    ]
    p, v = validate_k5_correlated_inventory_cap(
        ledger, correlated_group_caps={"ES_MES": 1_000_000.0}
    )
    assert p is False
    assert 1 in v  # The MES entry pushed running notional past cap


# ─── K-6 daily circuit breaker ───────────────────────────────────────────────


def test_k6_passes_with_no_session_breaches() -> None:
    ledger = [_make_entry(r_value=0.5, session_id=i, week_id=0) for i in range(5)]
    p, v = validate_k6_daily_circuit_breaker(ledger, kill_switch_params=KillSwitchParams())
    assert p is True


def test_k6_fails_when_strategy_trades_after_halt() -> None:
    # Q-1 fix: K-6 fires AT the breaching trade (trade 2, idx 2 in zero-indexed
    # terms). The 3rd, 4th trades (idx 3, 4) are the actual violations — they
    # were skipped by the simulator. Trades 0+1+2 executed legitimately.
    ledger = [
        _make_entry(r_value=-1.0, session_id=0, week_id=0),
        _make_entry(r_value=-1.0, session_id=0, week_id=0),
        _make_entry(r_value=-1.0, session_id=0, week_id=0),
        _make_entry(r_value=-0.5, session_id=0, week_id=0),
        _make_entry(r_value=-0.5, session_id=0, week_id=0),
    ]
    p, v = validate_k6_daily_circuit_breaker(ledger, kill_switch_params=KillSwitchParams())
    assert p is False
    # Exact-match: only post-halt trades (3, 4) flagged; pre-halt trades
    # (0, 1, 2) executed legitimately and are NOT flagged (Round-1 audit Q-1
    # exact-match assertion strengthening per the audit's recommendation).
    assert v == (3, 4)


# ─── K-7 weekly circuit breaker ──────────────────────────────────────────────


def test_k7_passes_with_no_weekly_breaches() -> None:
    ledger = [_make_entry(r_value=0.5, session_id=i, week_id=i // 5) for i in range(20)]
    p, v = validate_k7_weekly_circuit_breaker(ledger, kill_switch_params=KillSwitchParams())
    assert p is True


def test_k7_fails_when_strategy_trades_after_weekly_halt() -> None:
    # Q-2 fix: K-7 fires AT the breaching trade. Trades 0-5 executed
    # legitimately; trades 6+7 (post-halt session 10, 11 same week 0) are the
    # actual violations.
    ledger = [
        _make_entry(r_value=-1.0, session_id=i, week_id=0) for i in range(6)
    ]
    ledger.append(_make_entry(r_value=-0.5, session_id=10, week_id=0))
    ledger.append(_make_entry(r_value=-0.5, session_id=11, week_id=0))
    p, v = validate_k7_weekly_circuit_breaker(ledger, kill_switch_params=KillSwitchParams())
    assert p is False
    # Exact-match: only trades 6, 7 are post-halt violations.
    assert v == (6, 7)


# ─── K-8 adverse-direction filter ────────────────────────────────────────────


def test_k8_passes_when_t_h_aligns_with_entry() -> None:
    ledger = [
        _make_entry(
            position_direction=1,
            trigger_t_h_sign=1,
            entry_bar_open_price=5_000.0,
            fill_price=4_999.0,  # slight adverse but T_H agrees
            atr_at_entry=5.0,
        )
    ]
    p, v = validate_k8_adverse_direction_filter(ledger)
    assert p is True


def test_k8_fails_on_t_h_disagree_plus_adverse_move() -> None:
    # Long entry, T_H sign=-1 (disagree), price moved -1 ATR adversely (-5)
    ledger = [
        _make_entry(
            position_direction=1,
            trigger_t_h_sign=-1,
            entry_bar_open_price=5_000.0,
            fill_price=4_995.0,
            atr_at_entry=5.0,
        )
    ]
    p, v = validate_k8_adverse_direction_filter(ledger)
    assert p is False
    assert v == (0,)


def test_k8_skips_when_t_h_metadata_absent() -> None:
    ledger = [_make_entry(trigger_t_h_sign=None)]
    p, v = validate_k8_adverse_direction_filter(ledger)
    assert p is True


# ─── validate_kill_switches_per_fold orchestration ───────────────────────────


def test_canary_partial_when_metadata_deferred() -> None:
    # Q-3 fix: minimal-metadata ledger triggers "partial" annotation, not "pass"
    # — K-2/K-5/K-8 are deferred or n/a without metadata.
    bar_ns = 60_000_000_000
    ledger = [
        _make_entry(
            r_value=0.5,
            session_id=i,
            week_id=i // 5,
            position_size=1,
            instrument="ES",
            open_ns=i * 2 * bar_ns,
            close_ns=(i * 2 + 1) * bar_ns,
        )
        for i in range(10)
    ]
    res = validate_kill_switches_per_fold(fold_id=0, ledger=ledger)
    assert isinstance(res, KillSwitchCanaryResult)
    assert res.all_passed is True
    # Without time-stop / group caps / T_H metadata, K-2/K-5/K-8 are deferred
    # → annotation is "partial", not "pass" (Q-3 fix).
    assert res.annotation == "kill-switch-canary-partial"
    assert res.per_K_validated["K-1"] is True
    assert res.per_K_validated["K-2"] is False  # deferred
    assert res.per_K_validated["K-3"] is True
    assert res.per_K_validated["K-4"] is True
    assert res.per_K_validated["K-5"] is False  # deferred
    assert res.per_K_validated["K-6"] is True
    assert res.per_K_validated["K-7"] is True
    assert res.per_K_validated["K-8"] is False  # n/a (no T_H)


def test_canary_fail_on_k1_violation() -> None:
    ledger = [_make_entry(r_value=-1.5)]
    res = validate_kill_switches_per_fold(fold_id=1, ledger=ledger)
    assert res.all_passed is False
    assert res.annotation == "kill-switch-canary-fail"
    assert res.per_K_passed["K-1"] is False
    assert 0 in res.per_K_violations["K-1"]


def test_canary_per_k_metadata_populated() -> None:
    ledger = [_make_entry()]
    res = validate_kill_switches_per_fold(fold_id=0, ledger=ledger)
    assert "K-1" in res.per_K_metadata
    assert res.per_K_metadata["K-1"] == "validated"
    assert res.per_K_metadata["K-2"].startswith("deferred")  # no time-stop supplied
    assert res.per_K_metadata["K-5"].startswith("deferred")  # no group caps
    assert res.per_K_metadata["K-8"] == "n/a-no-trigger_t_h_sign-metadata"


def test_canary_pass_when_full_metadata_validates_all_k() -> None:
    # All metadata present → K-1..K-8 fully validated → annotation "pass"
    # (Q-3 fix: distinguishes from "partial" when metadata is incomplete).
    ledger = [
        _make_entry(
            r_value=0.5,
            session_id=0,
            week_id=0,
            position_size=1,
            instrument="ES",
            multiplier=50.0,
            fill_price=5_000.0,
            correlated_group="ES_MES",
            trigger_t_h_sign=1,
        )
    ]
    res = validate_kill_switches_per_fold(
        fold_id=0,
        ledger=ledger,
        per_trade_time_stop_min=30.0,
        correlated_group_caps={"ES_MES": 10_000_000.0},
    )
    for k_id in ("K-1", "K-2", "K-3", "K-4", "K-5", "K-6", "K-7", "K-8"):
        assert k_id in res.per_K_metadata
        assert res.per_K_passed[k_id] is True
        assert res.per_K_validated[k_id] is True
    assert res.all_passed is True
    assert res.annotation == "kill-switch-canary-pass"


def test_canary_extra_field_records_provenance() -> None:
    ledger = [_make_entry(r_value=0.5)]
    res = validate_kill_switches_per_fold(fold_id=0, ledger=ledger)
    assert res.extra["n_trades"] == 1
    assert res.extra["starting_equity"] == 10_000.0
    assert res.extra["risk_budget_pct"] == 0.01
