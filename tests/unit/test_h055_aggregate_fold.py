"""Unit tests for the H055 orchestrator's _aggregate_fold function.

Verifies that _aggregate_fold correctly computes the ADR-0017 §1
inference layer (R-mult CI, forward projection, risk-of-ruin) when
n_trades >= 4, and falls back gracefully when n_trades < 4.

Independent of substrate-load + feature factory; tests the aggregation
+ inference logic in isolation.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from run_h055_walk_forward import _aggregate_fold  # noqa: E402

from skie_ninja.backtest.per_trade_simulator import (  # noqa: E402
    EntryConfig,
    ExitReason,
    TradeResult,
)


def _make_trade(
    *,
    confirmation_bar: int = 0,
    fill_bar: int = 1,
    side: int = 1,
    realized_pnl: float = 100.0,
    r_multiple: float = 1.0,
    one_r: float = 100.0,
) -> TradeResult:
    return TradeResult(
        confirmation_bar=confirmation_bar,
        side=side,
        entry_limit_price=5000.0,
        atr_n_at_entry=5.0,
        fill_bar=fill_bar,
        fill_price=5000.0,
        exit_bar=fill_bar + 5,
        exit_price=5000.0 + realized_pnl / 50.0,  # $50 multiplier
        exit_reason=ExitReason.PROFIT_TARGET if realized_pnl > 0 else ExitReason.STOP_LOSS,
        tp_price=5010.0,
        sl_price=4995.0,
        realized_pnl_dollars=realized_pnl,
        r_multiple=r_multiple,
        one_r_dollars=one_r,
        position_size=1,
        multiplier=50.0,
    )


def test_aggregate_fold_with_n_trades_below_inference_threshold() -> None:
    """n_filled < 4 → inference fields are None (graceful fallback)."""
    trades = [_make_trade() for _ in range(2)]
    fold = _aggregate_fold(
        symbol="ES", n_bars=1000, setups=[], gated_setups=[], trades=trades,
        starting_equity=10_000.0,
    )
    assert fold.n_trades_filled == 2
    assert fold.r_mult_ci_lower is None
    assert fold.r_mult_ci_upper is None
    assert fold.forward_terminal_q05 is None
    assert fold.risk_of_ruin is None


def test_aggregate_fold_winning_strategy_emits_inference_fields() -> None:
    """20 winning trades → R-mult CI populated; forward projection runs."""
    trades = [
        _make_trade(realized_pnl=100.0, r_multiple=1.0) for _ in range(20)
    ]
    fold = _aggregate_fold(
        symbol="ES", n_bars=1000, setups=[], gated_setups=[], trades=trades,
        starting_equity=10_000.0, n_forward_paths=200, n_bootstrap_ci=100,
    )
    assert fold.n_trades_filled == 20
    # All winners → R-mult mean = +1.0
    assert fold.r_multiple_mean == 1.0
    assert fold.r_mult_ci_lower is not None
    assert fold.r_mult_ci_upper is not None
    # CI is degenerate around 1.0 (zero variance)
    assert fold.r_mult_ci_lower == fold.r_mult_ci_upper == 1.0
    # Forward projection populated
    assert fold.forward_terminal_q05 is not None
    assert fold.forward_terminal_median is not None
    assert fold.forward_terminal_q05 > 10_000.0  # all winners → equity grows
    assert fold.forward_p_loss is not None
    assert fold.forward_p_loss == 0.0  # all winners → P(loss) = 0
    assert fold.risk_of_ruin is not None
    assert fold.risk_of_ruin < 0.05  # winning strategy → low ruin


def test_aggregate_fold_losing_strategy_high_p_loss() -> None:
    """20 losing trades → P(loss) ≈ 1.0; forward terminal < starting."""
    trades = [
        _make_trade(realized_pnl=-100.0, r_multiple=-1.0) for _ in range(20)
    ]
    fold = _aggregate_fold(
        symbol="ES", n_bars=1000, setups=[], gated_setups=[], trades=trades,
        starting_equity=10_000.0, n_forward_paths=200, n_bootstrap_ci=100,
    )
    assert fold.r_multiple_mean == -1.0
    assert fold.forward_p_loss is not None
    assert fold.forward_p_loss == 1.0  # all losers → P(loss) = 1
    assert fold.forward_terminal_median is not None
    assert fold.forward_terminal_median < 10_000.0


def test_aggregate_fold_mixed_strategy_realistic() -> None:
    """60% winners +1R, 40% losers -1R, shuffled iid → +0.2R mean expected.

    Note on bootstrap CI behavior: stationary bootstrap with PW2004 block-
    length selection correctly widens CI for autocorrelated sequences
    (e.g., a 60-winners-then-40-losers block-shaped sequence has large
    autocorrelation; PW2004 selects a long block; the CI widens to honor
    the lower effective sample size). Shuffling decorrelates → CI tightens.
    The inference primitives are working correctly under either regime.
    """
    import numpy as np

    n = 100
    rng = np.random.default_rng(42)
    # Build shuffled sequence so the bootstrap sees iid data.
    pnls = np.array([100.0] * 60 + [-100.0] * 40)
    rng.shuffle(pnls)
    trades = [
        _make_trade(realized_pnl=float(p), r_multiple=p / 100.0)
        for p in pnls
    ]
    fold = _aggregate_fold(
        symbol="ES", n_bars=1000, setups=[], gated_setups=[], trades=trades,
        starting_equity=10_000.0, n_forward_paths=500, n_bootstrap_ci=500,
    )
    # Mean R should be +0.2 (60 × +1 + 40 × -1) / 100
    assert fold.r_multiple_mean == 0.2
    assert fold.r_mult_ci_lower is not None
    assert fold.r_mult_ci_upper is not None
    # CI is symmetric-ish around 0.2; both bounds should be finite
    assert np.isfinite(fold.r_mult_ci_lower)
    assert np.isfinite(fold.r_mult_ci_upper)
    assert fold.r_mult_ci_lower < fold.r_multiple_mean < fold.r_mult_ci_upper
    # Forward projection: expected positive drift; P(loss) < 0.5
    assert fold.forward_p_loss is not None
    assert fold.forward_p_loss < 0.5


def test_aggregate_fold_calmar_computation() -> None:
    """Verify Calmar = ann_return / max(|max_dd|, eps)."""
    # 5 winners then 5 losers — net zero PnL but max-DD will be observable
    trades = (
        [_make_trade(realized_pnl=200.0, r_multiple=2.0) for _ in range(5)]
        + [_make_trade(realized_pnl=-200.0, r_multiple=-2.0) for _ in range(5)]
    )
    fold = _aggregate_fold(
        symbol="ES", n_bars=1950, setups=[], gated_setups=[], trades=trades,  # 1950/390=5 sessions
        starting_equity=10_000.0, n_forward_paths=200, n_bootstrap_ci=100,
    )
    # End equity = 10_000 (5 wins of +200 = +1000; 5 losses of -200 = -1000)
    assert fold.realized_end_equity == 10_000.0
    assert fold.ann_return == 0.0  # zero return → Calmar should be 0
    # Max-DD: peak at $11,000 (after 5 wins); trough at $10,000 (after 5 losses)
    # → max_dd = (10000 - 11000) / 11000 ≈ -0.0909
    assert fold.max_dd == pytest.approx(-0.0909, abs=1e-3)
    # Calmar = 0 / 0.0909 = 0
    assert fold.calmar == 0.0


def test_aggregate_fold_profit_factor_n_a_when_no_trades() -> None:
    """0 trades → profit_factor None."""
    fold = _aggregate_fold(
        symbol="ES", n_bars=100, setups=[], gated_setups=[], trades=[],
        starting_equity=10_000.0,
    )
    assert fold.n_trades_filled == 0
    assert fold.profit_factor_value is None
    assert fold.r_multiple_mean == 0.0


import pytest  # noqa: E402  (used in test_aggregate_fold_calmar_computation)
