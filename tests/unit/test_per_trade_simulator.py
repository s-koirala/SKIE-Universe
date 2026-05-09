"""Unit tests for the per-trade backtest simulator."""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.backtest.per_trade_simulator import (
    EntryConfig,
    ExitReason,
    TradeResult,
    simulate_per_trade,
)


def _es_config(
    *,
    entry_limit_price: float = 5000.0,
    side: int = 1,
    confirmation_bar: int = 0,
    atr: float = 5.0,
    alpha: float = 2.0,
    beta: float = 1.0,
    k_swing: int = 5,
    hard_close: int | None = None,
) -> EntryConfig:
    return EntryConfig(
        entry_limit_price=entry_limit_price,
        side=side,
        confirmation_bar=confirmation_bar,
        atr_n_at_entry=atr,
        alpha_tp_mult=alpha,
        beta_sl_mult=beta,
        k_swing_bars=k_swing,
        position_size=1,
        multiplier=50.0,  # ES
        hard_close_bar=hard_close,
    )


# ─── Limit-fill window ──────────────────────────────────────────────────────


def test_long_limit_fills_when_price_reaches() -> None:
    # Entry limit at 5000; bar 1 has low=4998 → fill at 5000.
    h = np.array([5005.0, 5002.0, 5010.0])
    l = np.array([5001.0, 4998.0, 5005.0])
    c = np.array([5003.0, 5001.0, 5008.0])
    cfg = _es_config(entry_limit_price=5000.0, side=1, confirmation_bar=0, k_swing=3)
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.fill_bar == 1
    assert res.fill_price == 5000.0


def test_long_limit_never_fills_when_price_stays_above() -> None:
    h = np.array([5005.0, 5006.0, 5007.0])
    l = np.array([5001.0, 5002.0, 5003.0])
    c = np.array([5003.0, 5004.0, 5005.0])
    cfg = _es_config(entry_limit_price=4990.0, side=1, confirmation_bar=0, k_swing=3)
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.fill_bar is None
    assert res.exit_reason == ExitReason.NEVER_FILLED
    assert res.r_multiple == 0.0


def test_short_limit_fills_when_high_reaches() -> None:
    h = np.array([5001.0, 5005.0, 5002.0])  # bar 1 high=5005 reaches limit 5005
    l = np.array([4999.0, 5001.0, 4999.0])
    c = np.array([5000.0, 5003.0, 5000.0])
    cfg = _es_config(entry_limit_price=5005.0, side=-1, confirmation_bar=0, k_swing=3)
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.fill_bar == 1
    assert res.fill_price == 5005.0


# ─── TP / SL exit ────────────────────────────────────────────────────────────


def test_long_tp_exits_at_tp_price() -> None:
    # Fill at bar 0 at 5000; α=2 ATR=5 → TP=5010; SL=4995. Bar 1 high=5012 → TP hit.
    h = np.array([5001.0, 5012.0, 5005.0])
    l = np.array([4999.0, 4998.0, 5000.0])
    c = np.array([5000.0, 5010.0, 5003.0])
    cfg = _es_config(entry_limit_price=5000.0, side=1, confirmation_bar=0, k_swing=5)
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.fill_bar == 0
    assert res.exit_bar == 1
    assert res.exit_reason == ExitReason.PROFIT_TARGET
    assert res.exit_price == 5010.0
    # P&L = (5010 - 5000) × 1 × 1 × 50 = +500; 1R = 1 × 5 × 50 × 1 = 250 → R = +2.0
    assert res.r_multiple == pytest.approx(2.0)
    assert res.realized_pnl_dollars == pytest.approx(500.0)


def test_long_sl_exits_at_sl_price() -> None:
    # Fill at bar 0 at 5000; SL=4995. Bar 1 low=4990 → SL hit.
    h = np.array([5001.0, 5005.0, 5005.0])
    l = np.array([4999.0, 4990.0, 5000.0])
    c = np.array([5000.0, 4994.0, 5003.0])
    cfg = _es_config(entry_limit_price=5000.0, side=1, confirmation_bar=0, k_swing=5)
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.exit_bar == 1
    assert res.exit_reason == ExitReason.STOP_LOSS
    assert res.exit_price == 4995.0
    # R = (4995 - 5000) × 50 / (1 × 5 × 50) = -250/250 = -1.0
    assert res.r_multiple == pytest.approx(-1.0)


def test_long_both_tp_and_sl_in_same_bar_uses_pessimistic_sl() -> None:
    # AFML §13.2 pessimistic-fill convention: SL fills first when both reach.
    h = np.array([5001.0, 5012.0, 5005.0])
    l = np.array([4999.0, 4990.0, 5000.0])
    c = np.array([5000.0, 5008.0, 5003.0])
    cfg = _es_config(entry_limit_price=5000.0, side=1, confirmation_bar=0, k_swing=5)
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.exit_reason == ExitReason.STOP_LOSS
    assert res.exit_price == 4995.0  # SL = 5000 - 1×5
    assert res.r_multiple == pytest.approx(-1.0)


def test_short_tp_exits_correctly() -> None:
    # Short fill at 5005; α=2 ATR=5 → TP=4995; SL=5010.
    # Bar 0 fills (high=5005); bar 1 low=4990 → TP=4995 hit.
    h = np.array([5005.0, 5000.0, 5005.0])
    l = np.array([5001.0, 4990.0, 5000.0])
    c = np.array([5003.0, 4995.0, 5003.0])
    cfg = _es_config(entry_limit_price=5005.0, side=-1, confirmation_bar=0, k_swing=5)
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.fill_bar == 0
    assert res.exit_bar == 1
    assert res.exit_reason == ExitReason.PROFIT_TARGET
    assert res.exit_price == 4995.0
    # R = (5005 - 4995) × 1 (-1 × -1) × 50 / (1 × 5 × 50) = 500/250 = +2.0
    assert res.r_multiple == pytest.approx(2.0)


# ─── Time stop ───────────────────────────────────────────────────────────────


def test_time_stop_exits_at_close_after_k_bars() -> None:
    # Fill at bar 0; k_swing=3; price never reaches TP or SL.
    # Time-stop hit at bar 0 + 3 = bar 3 (close=5001.5 after k=3 bars).
    h = np.array([5001.0, 5002.0, 5003.0, 5001.5, 5002.0])
    l = np.array([4999.0, 4999.5, 5000.0, 5000.0, 5001.0])
    c = np.array([5000.0, 5001.0, 5002.0, 5001.5, 5001.5])
    cfg = _es_config(entry_limit_price=5000.0, side=1, confirmation_bar=0, k_swing=3)
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.fill_bar == 0
    assert res.exit_bar == 3
    assert res.exit_reason == ExitReason.TIME_STOP
    assert res.exit_price == 5001.5


# ─── Hard close ──────────────────────────────────────────────────────────────


def test_hard_close_exits_before_time_stop_if_earlier() -> None:
    # k_swing=10 (no time-stop within panel), but hard_close at bar 2.
    h = np.array([5001.0, 5002.0, 5003.0, 5001.5])
    l = np.array([4999.0, 4999.5, 5000.0, 5000.0])
    c = np.array([5000.0, 5001.0, 5002.5, 5001.5])
    cfg = _es_config(
        entry_limit_price=5000.0, side=1, confirmation_bar=0, k_swing=10,
        hard_close=2,
    )
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.exit_bar == 2
    assert res.exit_reason == ExitReason.HARD_CLOSE
    assert res.exit_price == 5002.5


# ─── Validation ──────────────────────────────────────────────────────────────


def test_entry_config_rejects_zero_position_size() -> None:
    with pytest.raises(ValueError, match="position_size"):
        EntryConfig(
            entry_limit_price=5000.0, side=1, confirmation_bar=0,
            atr_n_at_entry=5.0, alpha_tp_mult=2.0, beta_sl_mult=1.0,
            k_swing_bars=5, position_size=0, multiplier=50.0,
        )


def test_entry_config_rejects_invalid_side() -> None:
    with pytest.raises(ValueError, match="side"):
        EntryConfig(
            entry_limit_price=5000.0, side=0, confirmation_bar=0,
            atr_n_at_entry=5.0, alpha_tp_mult=2.0, beta_sl_mult=1.0,
            k_swing_bars=5, position_size=1, multiplier=50.0,
        )


def test_entry_config_rejects_nonpositive_atr() -> None:
    with pytest.raises(ValueError, match="atr_n_at_entry"):
        EntryConfig(
            entry_limit_price=5000.0, side=1, confirmation_bar=0,
            atr_n_at_entry=0.0, alpha_tp_mult=2.0, beta_sl_mult=1.0,
            k_swing_bars=5, position_size=1, multiplier=50.0,
        )


# ─── R-multiple consistency ──────────────────────────────────────────────────


def test_r_multiple_matches_alpha_when_tp_hits_clean() -> None:
    # α=2.5; β=1.0; if TP hits cleanly: R = +α/β = +2.5
    h = np.array([5001.0, 5015.0])  # bar 1 high=5015 → TP=5012.5 hit cleanly
    l = np.array([4999.0, 5005.0])
    c = np.array([5000.0, 5010.0])
    cfg = _es_config(
        entry_limit_price=5000.0, side=1, confirmation_bar=0,
        atr=5.0, alpha=2.5, beta=1.0, k_swing=5,
    )
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.exit_reason == ExitReason.PROFIT_TARGET
    assert res.r_multiple == pytest.approx(2.5)


def test_r_multiple_minus_one_on_clean_sl_with_beta_one() -> None:
    h = np.array([5001.0, 5005.0])
    l = np.array([4999.0, 4990.0])  # bar 1 low=4990 → SL=4995 hit
    c = np.array([5000.0, 4992.0])
    cfg = _es_config(
        entry_limit_price=5000.0, side=1, confirmation_bar=0,
        atr=5.0, alpha=2.0, beta=1.0, k_swing=5,
    )
    res = simulate_per_trade(h, l, c, config=cfg)
    assert res.exit_reason == ExitReason.STOP_LOSS
    assert res.r_multiple == pytest.approx(-1.0)


# ─── Shape validation ────────────────────────────────────────────────────────


def test_simulate_rejects_shape_mismatch() -> None:
    h = np.array([1.0, 2.0])
    l = np.array([0.5, 1.5])
    c = np.array([1.0])
    cfg = _es_config()
    with pytest.raises(ValueError, match="shape mismatch"):
        simulate_per_trade(h, l, c, config=cfg)
