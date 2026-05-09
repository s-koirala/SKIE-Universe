"""Per-trade backtest simulator for H055-class strategies per design.md §4.

Given a sequence of confirmed setups (swing-pivot or wick-reversal) + bar
OHLC panel + ATR series at entry-time + sizing inputs, simulates limit-
order entries, ATR-scaled TP/SL exits, time-stops, and hard-close exits,
producing per-trade outcomes with R-multiples + dollar P/L.

H055 design.md §4 entry/exit rules:
- **Entry**: limit order at `setup.entry_limit_price`; valid for k_swing bars
  starting at `setup.confirmation_bar`. Filled on first bar where:
    - long entry: bar.low <= entry_limit_price (price reaches the limit)
    - short entry: bar.high >= entry_limit_price
- **Profit target**: TP = entry ± α · ATR_n_at_entry
- **Stop**: SL = entry ∓ β · ATR_n_at_entry
- **Time stop**: k_swing bars after fill (vertical barrier).
- **Hard close**: configurable wall-clock (15:55 ET RTH; or session end ETH).
- **pt_sl**: both active; first-hit wins.
- **Both-TP-and-SL-in-same-bar**: pessimistic-fill convention — SL fills first
  per AFML §13.2 *practitioner* conservative-backtest rule.

Per-trade R-multiple per ADR-0017 §2.4:
    R = realized_pnl_dollars / |1R_dollars|
    1R_dollars = β · ATR_n_at_entry · multiplier × position_size

Implementation per `P1-H055-PER-TRADE-SIMULATOR-IMPL` (BLOCKING-BEFORE-
H055-WALK-FORWARD-LAUNCH).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

import numpy as np
import numpy.typing as npt

__all__ = [
    "EntryConfig",
    "ExitReason",
    "TradeResult",
    "simulate_per_trade",
]


# ─── Constants ───────────────────────────────────────────────────────────────


_LONG: Final[int] = 1
_SHORT: Final[int] = -1


# ─── Enums (string literals for JSON-friendliness) ───────────────────────────


class ExitReason:
    """Exit-reason taxonomy. Used as string literals in TradeResult.exit_reason.

    PROFIT_TARGET: TP price hit before SL or time-stop.
    STOP_LOSS: SL price hit before TP or time-stop.
    TIME_STOP: k_swing bars elapsed after fill without TP / SL hit.
    HARD_CLOSE: end-of-session reached (15:55 ET RTH / session-end ETH).
    NEVER_FILLED: limit order didn't get hit within k_swing bars from
        confirmation_bar; trade did not enter.
    """

    PROFIT_TARGET: Final[str] = "profit_target"
    STOP_LOSS: Final[str] = "stop_loss"
    TIME_STOP: Final[str] = "time_stop"
    HARD_CLOSE: Final[str] = "hard_close"
    NEVER_FILLED: Final[str] = "never_filled"


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EntryConfig:
    """Per-trade configuration (instance per setup).

    Args:
        entry_limit_price: Price at which the limit order is posted.
        side: +1 (long) or -1 (short).
        confirmation_bar: Bar index at which the setup was confirmed; limit
            is valid starting at this bar (per H055 design.md §4).
        atr_n_at_entry: ATR_n value at confirmation time; used to compute
            TP, SL, and 1R_dollars.
        alpha_tp_mult: TP = entry ± alpha · ATR_n; ∈ [0.5, 4.0] per §5.6.
        beta_sl_mult: SL = entry ∓ beta · ATR_n; ∈ [0.5, 3.0] per §5.6.
        k_swing_bars: Time-stop in bars (vertical barrier); also bounds the
            limit-order-fill window. ∈ {3, 5, 8, 13} per §5.6.
        position_size: Number of contracts.
        multiplier: Dollars per point (50 for ES, 5 for MES, etc.).
        hard_close_bar: Optional integer bar index of session-end hard close
            (e.g., the 15:55 ET RTH-mode bar). If the trade is still open at
            this bar, it is force-exited at that bar's close. None = no
            hard-close (ETH-mode).
    """

    entry_limit_price: float
    side: int
    confirmation_bar: int
    atr_n_at_entry: float
    alpha_tp_mult: float
    beta_sl_mult: float
    k_swing_bars: int
    position_size: int
    multiplier: float
    hard_close_bar: int | None = None

    def __post_init__(self) -> None:
        if self.side not in (_LONG, _SHORT):
            raise ValueError(f"side must be +1 or -1, got {self.side}")
        if self.entry_limit_price <= 0:
            raise ValueError(
                f"entry_limit_price must be positive, got {self.entry_limit_price}"
            )
        if self.atr_n_at_entry <= 0:
            raise ValueError(
                f"atr_n_at_entry must be positive, got {self.atr_n_at_entry}"
            )
        if self.alpha_tp_mult <= 0:
            raise ValueError(
                f"alpha_tp_mult must be positive, got {self.alpha_tp_mult}"
            )
        if self.beta_sl_mult <= 0:
            raise ValueError(
                f"beta_sl_mult must be positive, got {self.beta_sl_mult}"
            )
        if self.k_swing_bars < 1:
            raise ValueError(
                f"k_swing_bars must be >= 1, got {self.k_swing_bars}"
            )
        if self.position_size < 1:
            raise ValueError(
                f"position_size must be >= 1, got {self.position_size}"
            )
        if self.multiplier <= 0:
            raise ValueError(
                f"multiplier must be positive, got {self.multiplier}"
            )


@dataclass(frozen=True)
class TradeResult:
    """One completed trade (or never-filled non-trade).

    Fields:
        confirmation_bar: From the setup.
        side, entry_limit_price, atr_n_at_entry: From EntryConfig.
        fill_bar: Bar at which the limit order filled. None if never filled.
        fill_price: Filled price (typically equals entry_limit_price for a
            limit fill; in a wick-pierce-and-recover scenario it's the
            limit). None if never filled.
        exit_bar: Bar at which the trade exited. None if never filled.
        exit_price: Realized exit price.
        exit_reason: One of the ExitReason constants.
        tp_price, sl_price: Computed at fill time (±α/β · ATR_n).
        realized_pnl_dollars: (exit_price - fill_price) × side × position ×
            multiplier. Zero for never-filled trades.
        r_multiple: realized_pnl_dollars / one_r_dollars; 0 for never_filled.
        one_r_dollars: β · ATR_n_at_entry · multiplier × position_size.
    """

    confirmation_bar: int
    side: int
    entry_limit_price: float
    atr_n_at_entry: float
    fill_bar: int | None
    fill_price: float | None
    exit_bar: int | None
    exit_price: float | None
    exit_reason: str
    tp_price: float | None
    sl_price: float | None
    realized_pnl_dollars: float
    r_multiple: float
    one_r_dollars: float
    position_size: int = 1
    multiplier: float = 1.0


# ─── Simulator ───────────────────────────────────────────────────────────────


def _compute_tp_sl(
    fill_price: float, side: int, atr_n: float, alpha: float, beta: float
) -> tuple[float, float]:
    if side == _LONG:
        tp = fill_price + alpha * atr_n
        sl = fill_price - beta * atr_n
    else:
        tp = fill_price - alpha * atr_n
        sl = fill_price + beta * atr_n
    return tp, sl


def simulate_per_trade(
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    close: npt.ArrayLike,
    *,
    config: EntryConfig,
) -> TradeResult:
    """Simulate one trade given a setup + OHLC panel + EntryConfig.

    Steps:
    1. Limit-fill window: bars [confirmation_bar, confirmation_bar +
       k_swing_bars - 1]. For each bar, check whether price reaches
       entry_limit_price (long: low <= entry_limit_price; short: high >=
       entry_limit_price). If yes, fill at entry_limit_price.
    2. If never filled, return TradeResult with exit_reason=NEVER_FILLED.
    3. After fill, compute TP + SL.
    4. Exit window: from (fill_bar + 1) onward. For each bar:
       - If bar contains BOTH TP and SL (long: low <= sl AND high >= tp;
         short: high >= sl AND low <= tp): use **pessimistic-fill** SL-first
         convention per AFML §13.2.
       - If bar contains only TP: exit at TP price; reason=PROFIT_TARGET.
       - If bar contains only SL: exit at SL price; reason=STOP_LOSS.
    5. Time stop: if (current_bar - fill_bar) >= k_swing_bars, exit at the
       current bar's close; reason=TIME_STOP.
    6. Hard close: if hard_close_bar is set and current_bar >= hard_close_bar,
       exit at that bar's close; reason=HARD_CLOSE.

    Args:
        high, low, close: 1-D OHLC arrays for the full bar panel.
        config: EntryConfig with setup details + sizing + thresholds.

    Returns:
        TradeResult with all fields populated (None where not applicable).

    Raises:
        ValueError: shape mismatch on OHLC arrays.
    """
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    if not (h.shape == l.shape == c.shape):
        raise ValueError(
            f"shape mismatch: high {h.shape}, low {l.shape}, close {c.shape}"
        )
    n = h.size

    one_r_dollars = float(
        config.beta_sl_mult * config.atr_n_at_entry * config.multiplier
        * config.position_size
    )

    # ─── Limit-order fill window ────────────────────────────────────────
    fill_bar: int | None = None
    fill_price: float | None = None
    last_fill_window_bar = min(
        n - 1, config.confirmation_bar + config.k_swing_bars - 1
    )
    for t in range(config.confirmation_bar, last_fill_window_bar + 1):
        if t >= n:
            break
        if config.side == _LONG and l[t] <= config.entry_limit_price:
            fill_bar = t
            fill_price = config.entry_limit_price
            break
        if config.side == _SHORT and h[t] >= config.entry_limit_price:
            fill_bar = t
            fill_price = config.entry_limit_price
            break

    if fill_bar is None or fill_price is None:
        return TradeResult(
            confirmation_bar=config.confirmation_bar,
            side=config.side,
            entry_limit_price=config.entry_limit_price,
            atr_n_at_entry=config.atr_n_at_entry,
            fill_bar=None,
            fill_price=None,
            exit_bar=None,
            exit_price=None,
            exit_reason=ExitReason.NEVER_FILLED,
            tp_price=None,
            sl_price=None,
            realized_pnl_dollars=0.0,
            r_multiple=0.0,
            one_r_dollars=one_r_dollars,
            position_size=config.position_size,
            multiplier=config.multiplier,
        )

    tp, sl = _compute_tp_sl(
        fill_price, config.side, config.atr_n_at_entry,
        config.alpha_tp_mult, config.beta_sl_mult,
    )

    # ─── Exit window ─────────────────────────────────────────────────────
    time_stop_bar = fill_bar + config.k_swing_bars
    hc_bar = config.hard_close_bar
    exit_bar: int | None = None
    exit_price: float | None = None
    exit_reason: str = ""

    for t in range(fill_bar + 1, n):
        # Hard-close has priority if reached.
        if hc_bar is not None and t >= hc_bar:
            exit_bar = hc_bar
            exit_price = float(c[hc_bar]) if hc_bar < n else float(c[n - 1])
            exit_reason = ExitReason.HARD_CLOSE
            break

        # Time-stop (inclusive on the time_stop_bar itself).
        if t >= time_stop_bar:
            exit_bar = t
            exit_price = float(c[t])
            exit_reason = ExitReason.TIME_STOP
            break

        # TP / SL hit-detection.
        if config.side == _LONG:
            tp_hit = h[t] >= tp
            sl_hit = l[t] <= sl
        else:
            tp_hit = l[t] <= tp
            sl_hit = h[t] >= sl

        if tp_hit and sl_hit:
            # Pessimistic-fill convention: SL fills first.
            exit_bar = t
            exit_price = sl
            exit_reason = ExitReason.STOP_LOSS
            break
        if sl_hit:
            exit_bar = t
            exit_price = sl
            exit_reason = ExitReason.STOP_LOSS
            break
        if tp_hit:
            exit_bar = t
            exit_price = tp
            exit_reason = ExitReason.PROFIT_TARGET
            break

    if exit_bar is None or exit_price is None:
        # Ran off the end of the panel without exit.
        exit_bar = n - 1
        exit_price = float(c[n - 1])
        exit_reason = ExitReason.HARD_CLOSE  # treat panel-end as hard close

    realized_pnl_dollars = float(
        (exit_price - fill_price)
        * config.side
        * config.position_size
        * config.multiplier
    )
    r_multiple = realized_pnl_dollars / one_r_dollars if one_r_dollars > 0 else 0.0

    return TradeResult(
        confirmation_bar=config.confirmation_bar,
        side=config.side,
        entry_limit_price=config.entry_limit_price,
        atr_n_at_entry=config.atr_n_at_entry,
        fill_bar=fill_bar,
        fill_price=fill_price,
        exit_bar=exit_bar,
        exit_price=exit_price,
        exit_reason=exit_reason,
        tp_price=tp,
        sl_price=sl,
        realized_pnl_dollars=realized_pnl_dollars,
        r_multiple=r_multiple,
        one_r_dollars=one_r_dollars,
        position_size=config.position_size,
        multiplier=config.multiplier,
    )
