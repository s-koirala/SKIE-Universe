"""H065 TP-overlay sweep — H062 v1 + ATR-scaled profit-target grid.

Per H065 design.md §4 + §5: applies the canonical Turtle System 1/2 N-bar
Donchian-channel breakout signal (inherited from H062 verbatim) with the
addition of an ATR-scaled profit target at `entry ± M × k_atr × ATR_n,t`
for M ∈ {1.0, 1.5, 2.0, 2.5}. The M=∞ no-TP baseline is reported alongside
as the H062 v1 reference cell.

Sweep configurations:
    M_INF   (H062 baseline; no TP):                  TP disabled
    M_1.0   (TP at 1R; 1:1 risk:reward):              TP = entry ± 1.0 × k_atr × ATR
    M_1.5   (TP at 1.5R):                              TP = entry ± 1.5 × k_atr × ATR
    M_2.0   (TP at 2R; Faith 2007 "2N" anchor):       TP = entry ± 2.0 × k_atr × ATR
    M_2.5   (TP at 2.5R; upper bound of grid):         TP = entry ± 2.5 × k_atr × ATR

Per-trade exit precedence within a bar (PIT-resolved per design.md §4 + AFML
§13.3 *practitioner* conservative-bar-resolution convention):
    1. gap-through-stop at bar-t open
    2. stop hit during bar (low ≤ SL_long or high ≥ SL_short)
    3. TP hit during bar (high ≥ TP_long or low ≤ TP_short)
    4. opposite-channel break at bar close
    5. EOD-flatten / session-rollover

Stop-first convention: when bar's high+low both contain BOTH the stop AND
the TP, the bar resolves to stop-hit (conservative).

Kelly multiplier grid {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} per ADR-0018 D-2 +
ADR-0017 §4.1 current-equity rebase.

Single-cell representative feature grid (channel_n=120, k_atr=2.0, h_dwell=5,
atr_n=14, trend_id="a_ts_mom", L=60, τ=1.0) per H065 design.md §5 + §13 scope
deviation (full 55,296-cell grid deferred to `P1-H065-FULL-INNER-CV-GRID-V2`).

OOS window per H065 §2: per-symbol right-edges through 2026-05-15.
Mandatory sub-window: 2026-04-01 → 2026-05-15 reported alongside.

Output: comparison sidecar at
``artifacts/runs/H065/tp_overlay_sweep_<ts>/sweep_sidecar.json``
+ a printed KPI metrics table per H065 design.md §13 (the load-bearing
operator deliverable).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import polars as pl

from skie_ninja.features.h062 import H062FeatureConfig, compute_h062_features
from skie_ninja.inference.calmar import (
    calmar_differential_ci_stationary_bootstrap,
    calmar_ratio,
    max_drawdown_fraction,
)
from skie_ninja.inference.mppm import mppm_rho_1, mppm_with_ci
from skie_ninja.inference.profit_factor import (
    profit_factor,
    profit_factor_differential_ci_stationary_bootstrap,
)
from skie_ninja.inference.r_multiple import r_multiple_mean_ci_stationary_bootstrap
from skie_ninja.inference.skewness import (
    l_skewness_tau3,
    l_skewness_tau3_ci_stationary_bootstrap,
    payoff_shape_annotation,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h065_tp_overlay_sweep")


_MULTIPLIERS: dict[str, float] = {
    "ES": 50.0, "NQ": 20.0, "MGC": 10.0, "SIL": 1000.0,
}
_CAPACITY_CAPS: dict[str, int] = {
    "ES": 20, "NQ": 40, "MGC": 5, "SIL": 5,
}

# Sub-window cutoff for "2026-AprMay" mandatory reporting per H065 design.md §13.
_SUBWINDOW_START = pd.Timestamp("2026-04-01", tz="UTC").date()
_SUBWINDOW_END = pd.Timestamp("2026-05-15", tz="UTC").date()

# Bootstrap CI defaults (per H065 §12 reproducibility binding).
_RNG_SEED = 20260515
_N_BOOTSTRAP_CI = 1000
_ANNUALIZATION_FACTOR = 252.0  # sessions/yr for Calmar + Sharpe ann


@dataclass(frozen=True)
class TPOverlayConfig:
    """H065 TP-overlay configuration cell.

    M_inf is the H062 v1 no-TP baseline reference (M=inf disables TP fill check).
    use_current_equity_rebase: True = ADR-0017 §4.1 + ADR-0024 paradigm rebase
    on current equity (sizing shrinks as bankroll drops; matches H065 v1 spec);
    False = fixed-$10K rebase (matches H062 v1 baseline; for comparability).
    """
    name: str
    tp_multiplier_M: float  # +inf to disable TP
    kelly_multiplier: float
    risk_budget_pct: float
    use_current_equity_rebase: bool
    description: str

    @property
    def tp_enabled(self) -> bool:
        return np.isfinite(self.tp_multiplier_M)


def _build_sweep_configs(kelly_multiplier: float = 0.25) -> list[TPOverlayConfig]:
    """Construct the H065 v1 TP-overlay × Kelly sweep configurations.

    Per H065 design.md §5: M-grid {1.0, 1.5, 2.0, 2.5} + M=inf reference,
    Kelly-multiplier defaulting to 0.25 (matches H062 v1 modal cell).

    Two M=inf reference cells:
      - M_inf_h062_v1_fixed_rebase: replicates H062 v1 fixed-$10K rebase
        (for direct comparability with H062 v1 KPI report card numbers).
      - M_inf_h065_current_rebase: H065 v1 paradigm (ADR-0017 + ADR-0024
        current-equity rebase); load-bearing apples-to-apples comparison
        with the 4 M-grid cells which all use current-equity rebase.

    Returns 6 configs per Kelly cell (4 M cells + 2 M=inf reference cells).
    """
    return [
        TPOverlayConfig(
            name="M_inf_h062_v1_fixed_rebase",
            tp_multiplier_M=np.inf,
            kelly_multiplier=kelly_multiplier,
            risk_budget_pct=0.01,
            use_current_equity_rebase=False,
            description="M=inf no-TP H062 v1 fixed-$10K rebase reference",
        ),
        TPOverlayConfig(
            name="M_inf_h065_current_rebase",
            tp_multiplier_M=np.inf,
            kelly_multiplier=kelly_multiplier,
            risk_budget_pct=0.01,
            use_current_equity_rebase=True,
            description="M=inf no-TP H065 paradigm current-equity rebase",
        ),
        TPOverlayConfig(
            name="M_1.0",
            tp_multiplier_M=1.0,
            kelly_multiplier=kelly_multiplier,
            risk_budget_pct=0.01,
            use_current_equity_rebase=True,
            description="M=1.0 (1:1 risk:reward TP) + current-equity rebase",
        ),
        TPOverlayConfig(
            name="M_1.5",
            tp_multiplier_M=1.5,
            kelly_multiplier=kelly_multiplier,
            risk_budget_pct=0.01,
            use_current_equity_rebase=True,
            description="M=1.5 (1:1.5 risk:reward TP) + current-equity rebase",
        ),
        TPOverlayConfig(
            name="M_2.0",
            tp_multiplier_M=2.0,
            kelly_multiplier=kelly_multiplier,
            risk_budget_pct=0.01,
            use_current_equity_rebase=True,
            description="M=2.0 (1:2 risk:reward TP; Faith 2007 2N) + current-equity rebase",
        ),
        TPOverlayConfig(
            name="M_2.5",
            tp_multiplier_M=2.5,
            kelly_multiplier=kelly_multiplier,
            risk_budget_pct=0.01,
            use_current_equity_rebase=True,
            description="M=2.5 (1:2.5 risk:reward TP) + current-equity rebase",
        ),
    ]


@dataclass
class _Position:
    """In-position state. Single-unit per H065 v1 (no pyramiding)."""
    side: int  # +1 long, -1 short
    entry_price: float
    size: int
    stop_price: float
    tp_price: float  # +inf for long if TP disabled; -inf for short if TP disabled
    r_dollar: float  # |1R| dollar distance at entry
    entry_idx: int
    entry_session_date: object


def _load_5min_bars(
    substrate_root: Path,
    symbol: str,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    glob_pat = str(substrate_root / f"symbol={symbol}" / "year=*" / "part-*.parquet")
    lf = pl.scan_parquet(glob_pat).select(
        pl.col("ts_event"),
        pl.col("open"),
        pl.col("high"),
        pl.col("low"),
        pl.col("close"),
    )
    df = lf.collect().to_pandas()
    if df.empty:
        raise RuntimeError(f"{symbol}: empty substrate at {glob_pat}")
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df = df.sort_values("ts_event").reset_index(drop=True)
    mask = (df["ts_event"] >= start) & (df["ts_event"] <= end)
    df = df.loc[mask].copy()
    if df.empty:
        raise RuntimeError(f"{symbol}: substrate empty after filter")
    df = df.set_index("ts_event")
    df_5m = (
        df.resample("5min", label="right", closed="right")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        .dropna()
        .reset_index()
    )
    df_5m["session_date_et"] = (
        df_5m["ts_event"].dt.tz_convert("America/New_York").dt.date
    )
    return df_5m


def _run_tp_overlay_simulation(
    *,
    symbol: str,
    df_5m: pd.DataFrame,
    feature_config: H062FeatureConfig,
    k_atr: float,
    cfg: TPOverlayConfig,
    starting_equity: float = 10000.0,
    eod_flatten_minutes_from_open: int = 360,
) -> dict[str, Any]:
    """H065 simulator with TP-overlay + current-equity rebase.

    Per H065 design.md §4 exit-precedence within bar:
        1. gap-through-stop at bar-t open
        2. stop hit during bar
        3. TP hit during bar (NEW vs H062)
        4. opposite-channel break at bar close
        5. EOD-flatten / session-rollover

    Returns dict with per-trade log + per-session aggregate + metrics.
    """
    high = df_5m["high"].to_numpy()
    low = df_5m["low"].to_numpy()
    close = df_5m["close"].to_numpy()
    open_ = df_5m["open"].to_numpy()
    session_dates = df_5m["session_date_et"].to_numpy()
    ts_events = df_5m["ts_event"].to_numpy()
    n_bars = len(df_5m)

    feats = compute_h062_features(
        high=high, low=low, close=close, config=feature_config
    )

    multiplier = _MULTIPLIERS.get(symbol, 1.0)
    cap = _CAPACITY_CAPS.get(symbol, 1)

    equity = starting_equity
    trade_log: list[dict] = []
    equity_curve: list[float] = [starting_equity]
    n_ruin_events = 0

    session_starts: dict[object, int] = {}
    for t in range(n_bars):
        sd = session_dates[t]
        if sd not in session_starts:
            session_starts[sd] = t

    position: _Position | None = None

    def _close_position(
        exit_idx: int,
        exit_price: float,
        reason: str,
    ) -> None:
        nonlocal position, equity, n_ruin_events
        if position is None:
            return
        pnl = position.side * (exit_price - position.entry_price) * multiplier * position.size
        r_mult = pnl / position.r_dollar if position.r_dollar > 0 else 0.0
        equity += pnl
        equity_curve.append(equity)
        trade_log.append({
            "side": position.side,
            "entry_price": float(position.entry_price),
            "exit_price": float(exit_price),
            "size": int(position.size),
            "pnl": float(pnl),
            "r_dollar": float(position.r_dollar),
            "r_multiple": float(r_mult),
            "exit_reason": reason,
            "entry_session_date": position.entry_session_date,
            "exit_session_date": session_dates[exit_idx],
            "equity_post_trade": float(equity),
            "entry_idx": int(position.entry_idx),
            "exit_idx": int(exit_idx),
        })
        if equity < 0.5 * starting_equity:
            n_ruin_events += 1
        position = None

    def _check_stops_tp_exits(t: int) -> bool:
        """Returns True if position closed at bar t.

        Exit precedence per H065 design.md §4:
            1. gap-through-stop at open
            2. stop-hit during bar (low ≤ SL_long or high ≥ SL_short)
            3. TP-hit during bar (high ≥ TP_long or low ≤ TP_short)
            4. opposite-channel break at close
            5. EOD / session rollover at close

        Stop-first tie-breaking: when bar contains BOTH stop AND TP, resolves
        to stop-hit (conservative per AFML §13.3 *practitioner*).
        """
        nonlocal position
        if position is None:
            return False
        bar_session = session_dates[t]
        # 1. Gap-through-stop at open
        if position.side == 1:
            if open_[t] < position.stop_price:
                _close_position(t, float(open_[t]), "gap_through_stop_long")
                return True
            # 2. Stop hit during bar (low touches stop)
            if low[t] <= position.stop_price:
                _close_position(t, float(position.stop_price), "stop_hit_long")
                return True
            # 3. TP hit during bar (high touches TP) — only if TP enabled
            if np.isfinite(position.tp_price) and high[t] >= position.tp_price:
                _close_position(t, float(position.tp_price), "tp_hit_long")
                return True
        else:  # short
            if open_[t] > position.stop_price:
                _close_position(t, float(open_[t]), "gap_through_stop_short")
                return True
            if high[t] >= position.stop_price:
                _close_position(t, float(position.stop_price), "stop_hit_short")
                return True
            if np.isfinite(position.tp_price) and low[t] <= position.tp_price:
                _close_position(t, float(position.tp_price), "tp_hit_short")
                return True
        # 4. Opposite-channel break at close
        ev = int(feats.filtered_events[t])
        if (position.side == 1 and ev == -1) or (position.side == -1 and ev == 1):
            _close_position(t, float(close[t]), "opposite_channel_break")
            return True
        # 5. EOD flatten
        session_open_idx = session_starts.get(bar_session, t)
        if (t - session_open_idx) >= eod_flatten_minutes_from_open:
            _close_position(t, float(close[t]), "eod_flatten")
            return True
        # 6. Session rollover (next bar starts new session)
        if t + 1 < n_bars and session_dates[t + 1] != bar_session:
            _close_position(t, float(close[t]), "session_rollover")
            return True
        return False

    def _try_new_entry(t: int) -> None:
        nonlocal position
        if position is not None:
            return
        ev = int(feats.eligible_events[t])
        if ev == 0:
            return
        entry_idx_candidate = t + 1
        if entry_idx_candidate >= n_bars:
            return
        entry_price = float(open_[entry_idx_candidate])
        atr_t = float(feats.atr[t])
        if not np.isfinite(atr_t) or atr_t <= 0:
            return
        dollar_1r_per_contract = k_atr * atr_t * multiplier
        if dollar_1r_per_contract <= 0:
            return
        # Sizing per H062 v1 convention (line 357 of scripts/run_h062_walk_forward.py):
        # target_dollar_risk = equity × risk_budget_pct. At kelly_multiplier=0.25 the
        # H062 v1 simulator does NOT scale the dollar-risk-per-trade (kelly is a
        # hyperparameter at inner-CV selection only per the H062 v1 KPI report card
        # §"Scope deviations": "kelly_multiplier mode 0.25" annotation).
        #
        # H065 v1 distinguishes by `use_current_equity_rebase`:
        #   - False = fixed-equity ($10K baseline) sizing → matches H062 v1 verbatim;
        #             $100 per-trade $-risk regardless of bankroll drawdown.
        #   - True  = current-equity rebase per ADR-0017 §4.1 + ADR-0024 — $-risk
        #             scales with bankroll (sizing shrinks as bankroll drops).
        eq_for_sizing = equity if cfg.use_current_equity_rebase else starting_equity
        target_dollar_risk = eq_for_sizing * cfg.risk_budget_pct
        size_from_risk = target_dollar_risk / dollar_1r_per_contract
        size = int(np.floor(min(size_from_risk, cap)))
        if size < 1:
            return
        stop_price = entry_price - ev * (k_atr * atr_t)
        # TP price computation (NEW vs H062)
        if cfg.tp_enabled:
            tp_price = entry_price + ev * (cfg.tp_multiplier_M * k_atr * atr_t)
        else:
            tp_price = float("inf") if ev == 1 else float("-inf")
        bar_session = session_dates[t]
        position = _Position(
            side=ev,
            entry_price=entry_price,
            size=size,
            stop_price=stop_price,
            tp_price=tp_price,
            r_dollar=dollar_1r_per_contract * size,
            entry_idx=entry_idx_candidate,
            entry_session_date=bar_session,
        )

    for t in range(n_bars - 1):
        if position is not None:
            closed = _check_stops_tp_exits(t)
            if closed:
                continue
        else:
            _try_new_entry(t)

    if position is not None:
        _close_position(n_bars - 1, float(close[-1]), "end_of_data")

    # ---- Realized metrics ----
    eq_arr = np.array(equity_curve, dtype=float)
    realized_end = float(eq_arr[-1])
    running_max = np.maximum.accumulate(eq_arr)
    dd = (eq_arr - running_max) / running_max
    # Cap max_dd at 100% (full bankroll loss); negative-equity excursions are
    # operationally implausible since a real broker would liquidate. Track the
    # bankroll-blowup flag separately for diagnostic transparency.
    raw_max_dd_pct = float(-dd.min()) * 100 if dd.size > 0 else 0.0
    max_dd_pct = min(raw_max_dd_pct, 100.0)
    bankroll_blowup = bool((eq_arr < 0).any())
    if bankroll_blowup:
        _log.warning(
            "%s × %s: bankroll-blowup detected (min eq=$%.0f); MaxDD capped at 100%%",
            symbol, cfg.name, float(eq_arr.min()),
        )

    trade_pnls = np.array([t["pnl"] for t in trade_log])
    trade_rs = np.array([t["r_multiple"] for t in trade_log])
    wins = int((trade_pnls > 0).sum())
    losses = int((trade_pnls < 0).sum())
    zeros = int((trade_pnls == 0).sum())
    n_trades = len(trade_log)

    # ---- Per-session aggregated log-returns (for MPPM / Calmar / Sharpe) ----
    per_session_log_ret: dict[object, float] = {}
    eq_prev = starting_equity
    session_eq_at_close: dict[object, float] = {}
    for tr in trade_log:
        exit_sd = tr["exit_session_date"]
        if exit_sd not in session_eq_at_close or tr["exit_idx"] > session_eq_at_close.get(
            f"_max_idx_{exit_sd}", -1
        ):
            session_eq_at_close[exit_sd] = tr["equity_post_trade"]
            session_eq_at_close[f"_max_idx_{exit_sd}"] = tr["exit_idx"]
    # Construct chronological per-session list
    session_dates_unique = sorted({tr["exit_session_date"] for tr in trade_log})
    eq_prev = starting_equity
    session_pnl: list[float] = []
    session_log_ret: list[float] = []
    session_dates_ordered: list[object] = []
    for sd in session_dates_unique:
        eq_new = session_eq_at_close[sd]
        if eq_prev > 0 and eq_new > 0:
            slr = float(np.log(eq_new / eq_prev))
            spn = float(eq_new - eq_prev)
        else:
            slr = 0.0
            spn = 0.0
        session_log_ret.append(slr)
        session_pnl.append(spn)
        session_dates_ordered.append(sd)
        eq_prev = eq_new
    session_log_ret_arr = np.array(session_log_ret)
    session_pnl_arr = np.array(session_pnl)

    # ---- Sub-window: 2026-04-01 → 2026-05-15 ----
    def _to_date(d: object) -> object:
        """Normalize any date-like input to a python date for comparison."""
        if isinstance(d, _dt.date) and not isinstance(d, _dt.datetime):
            return d
        try:
            return pd.Timestamp(d).date()
        except Exception:
            return d

    sub_mask = [
        (_to_date(sd) >= _SUBWINDOW_START) and (_to_date(sd) <= _SUBWINDOW_END)
        for sd in session_dates_ordered
    ]
    sub_mask_arr = np.array(sub_mask, dtype=bool)
    if sub_mask_arr.size > 0 and session_log_ret_arr.size > 0:
        sub_session_log_ret = session_log_ret_arr[sub_mask_arr]
        sub_session_pnl = session_pnl_arr[sub_mask_arr]
    else:
        sub_session_log_ret = np.array([], dtype=float)
        sub_session_pnl = np.array([], dtype=float)

    # Sub-window realized end equity (chain from starting_equity through sub-trades)
    sub_trades = [tr for tr in trade_log
                  if _SUBWINDOW_START <= _to_date(tr["exit_session_date"]) <= _SUBWINDOW_END]
    if sub_trades:
        # Synthetic sub-window starting equity = first trade's pre-entry equity
        first_sub_idx = trade_log.index(sub_trades[0])
        sub_starting_eq = (
            trade_log[first_sub_idx - 1]["equity_post_trade"]
            if first_sub_idx > 0
            else starting_equity
        )
        sub_pnl_sum = sum(tr["pnl"] for tr in sub_trades)
        sub_realized_end = sub_starting_eq + sub_pnl_sum
        sub_realized_roi_pct = (sub_pnl_sum / sub_starting_eq) * 100 if sub_starting_eq > 0 else 0.0
        # Sub-window MaxDD from session-aggregated equity within window
        sub_eq_at_starts = sub_starting_eq + np.cumsum([tr["pnl"] for tr in sub_trades])
        sub_eq_full = np.concatenate([[sub_starting_eq], sub_eq_at_starts])
        sub_running_max = np.maximum.accumulate(sub_eq_full)
        sub_dd = (sub_eq_full - sub_running_max) / sub_running_max
        sub_max_dd_pct = float(-sub_dd.min()) * 100 if sub_dd.size > 0 else 0.0
        sub_wins = sum(1 for tr in sub_trades if tr["pnl"] > 0)
        sub_losses = sum(1 for tr in sub_trades if tr["pnl"] < 0)
        sub_zeros = sum(1 for tr in sub_trades if tr["pnl"] == 0)
    else:
        sub_starting_eq = starting_equity
        sub_realized_end = starting_equity
        sub_realized_roi_pct = 0.0
        sub_max_dd_pct = 0.0
        sub_wins = 0
        sub_losses = 0
        sub_zeros = 0

    # ---- MPPM(ρ=1) on per-session log-returns ----
    # Convert log-returns to simple returns for MPPM input (MPPM expects r_t > -1)
    if session_log_ret_arr.size >= 4:
        session_simple_returns = np.expm1(session_log_ret_arr)
        mppm_point = float(
            mppm_rho_1(session_simple_returns, risk_free=0.0, delta_t=1.0 / _ANNUALIZATION_FACTOR)
        )
        try:
            mppm_ci_result = mppm_with_ci(
                session_simple_returns,
                rho=1.0,
                risk_free=0.0,
                delta_t=1.0 / _ANNUALIZATION_FACTOR,
                n_bootstrap=_N_BOOTSTRAP_CI,
                rng_seed=_RNG_SEED,
            )
            mppm_ci_low = float(mppm_ci_result.ci_low)
            mppm_ci_high = float(mppm_ci_result.ci_high)
            mppm_excludes_zero = bool(mppm_ci_result.excludes_zero)
        except Exception as e:  # noqa: BLE001
            _log.warning("MPPM CI failed (%s): %s", symbol, e)
            mppm_ci_low = float("nan")
            mppm_ci_high = float("nan")
            mppm_excludes_zero = False
    else:
        mppm_point = float("nan")
        mppm_ci_low = float("nan")
        mppm_ci_high = float("nan")
        mppm_excludes_zero = False

    # ---- L-skewness τ_3 on per-trade R-multiples ----
    if trade_rs.size >= 4:
        tau3_point = float(l_skewness_tau3(trade_rs))
        try:
            tau3_ci = l_skewness_tau3_ci_stationary_bootstrap(
                trade_rs,
                n_bootstrap=_N_BOOTSTRAP_CI,
                rng_seed=_RNG_SEED + 1,
            )
            tau3_ci_low = float(tau3_ci.ci_low)
            tau3_ci_high = float(tau3_ci.ci_high)
            payoff_shape = payoff_shape_annotation(tau3_point, tau3_ci_low, tau3_ci_high)
        except Exception as e:  # noqa: BLE001
            _log.warning("L-skew CI failed (%s): %s", symbol, e)
            tau3_ci_low = float("nan")
            tau3_ci_high = float("nan")
            payoff_shape = "skew-undefined"
    else:
        tau3_point = float("nan")
        tau3_ci_low = float("nan")
        tau3_ci_high = float("nan")
        payoff_shape = "skew-undefined"

    # ---- R-multiple mean CI ----
    if trade_rs.size >= 4:
        try:
            r_ci = r_multiple_mean_ci_stationary_bootstrap(
                trade_rs,
                n_bootstrap=_N_BOOTSTRAP_CI,
                rng_seed=_RNG_SEED + 2,
            )
            r_mean = float(r_ci.point_estimate)
            r_ci_low = float(r_ci.ci_lower)
            r_ci_high = float(r_ci.ci_upper)
            r_excludes_zero = bool(r_ci.excludes_zero)
        except Exception as e:  # noqa: BLE001
            _log.warning("R-mult CI failed (%s): %s", symbol, e)
            r_mean = float(trade_rs.mean())
            r_ci_low = float("nan")
            r_ci_high = float("nan")
            r_excludes_zero = False
    else:
        r_mean = float(trade_rs.mean()) if trade_rs.size else 0.0
        r_ci_low = float("nan")
        r_ci_high = float("nan")
        r_excludes_zero = False

    # ---- Profit factor + Sharpe (annualised) ----
    pf = profit_factor(trade_pnls) if trade_pnls.size else 0.0

    # Sharpe (annualised) on per-session log-returns
    if session_log_ret_arr.size > 1 and session_log_ret_arr.std(ddof=1) > 0:
        sr_session = session_log_ret_arr.mean() / session_log_ret_arr.std(ddof=1)
        sr_annualised = sr_session * np.sqrt(_ANNUALIZATION_FACTOR)
    else:
        sr_annualised = float("nan")

    # Calmar (point estimate)
    if session_log_ret_arr.size >= 4:
        try:
            calmar = float(
                calmar_ratio(session_log_ret_arr, annualization_factor=_ANNUALIZATION_FACTOR)
            )
        except Exception:
            calmar = float("nan")
    else:
        calmar = float("nan")

    return {
        "symbol": symbol,
        "cfg_name": cfg.name,
        "tp_multiplier_M": cfg.tp_multiplier_M if cfg.tp_enabled else None,
        "kelly_multiplier": cfg.kelly_multiplier,
        # Full OOS realized
        "realized_end_equity": realized_end,
        "realized_roi_pct": (realized_end / starting_equity - 1.0) * 100,
        "realized_max_dd_pct": max_dd_pct,
        "raw_max_dd_pct": raw_max_dd_pct,
        "bankroll_blowup": bankroll_blowup,
        "wins": wins,
        "losses": losses,
        "zeros": zeros,
        "win_rate": wins / max(n_trades, 1),
        "n_trades": n_trades,
        "n_bars": n_bars,
        "sr_annualised": float(sr_annualised) if np.isfinite(sr_annualised) else None,
        "calmar": float(calmar) if np.isfinite(calmar) else None,
        "profit_factor": float(pf) if np.isfinite(pf) else None,
        "r_multiple_mean": r_mean,
        "r_multiple_mean_ci_low": r_ci_low,
        "r_multiple_mean_ci_high": r_ci_high,
        "r_multiple_mean_excludes_zero": r_excludes_zero,
        "mppm_rho1": mppm_point,
        "mppm_rho1_ci_low": mppm_ci_low,
        "mppm_rho1_ci_high": mppm_ci_high,
        "mppm_rho1_excludes_zero": mppm_excludes_zero,
        "l_skewness_tau3": tau3_point,
        "l_skewness_tau3_ci_low": tau3_ci_low,
        "l_skewness_tau3_ci_high": tau3_ci_high,
        "payoff_shape": payoff_shape,
        "n_ruin_events": n_ruin_events,
        # Sub-window 2026-04-01 → 2026-05-15
        "subwindow_starting_equity": sub_starting_eq,
        "subwindow_realized_end_equity": sub_realized_end,
        "subwindow_realized_roi_pct": sub_realized_roi_pct,
        "subwindow_realized_max_dd_pct": sub_max_dd_pct,
        "subwindow_wins": sub_wins,
        "subwindow_losses": sub_losses,
        "subwindow_zeros": sub_zeros,
        "subwindow_n_trades": len(sub_trades),
        # Per-session arrays for downstream basket-aggregation
        "session_log_returns": session_log_ret_arr.tolist(),
        "session_pnls": session_pnl_arr.tolist(),
        "session_dates": [str(sd) for sd in session_dates_ordered],
        # Exit-reason histogram for diagnostics
        "exit_reason_counts": _exit_reason_counts(trade_log),
    }


def _exit_reason_counts(trade_log: list[dict]) -> dict[str, int]:
    """Build histogram of exit reasons for diagnostic interpretation."""
    counts: dict[str, int] = {}
    for tr in trade_log:
        counts[tr["exit_reason"]] = counts.get(tr["exit_reason"], 0) + 1
    return counts


def _compute_basket_metrics(
    per_symbol_results: list[dict[str, Any]],
    cfg_name: str,
    starting_equity: float = 10000.0,
) -> dict[str, Any]:
    """Aggregate per-symbol results into a basket-level row per H065 §1.

    Basket = equal-weighted (1/N_symbols) per-session log-return aggregation
    across the 4 symbols. Per-symbol per-session log-returns are aligned on
    session_date_et; missing-symbol sessions are treated as zero log-return
    (no-trade session contributes zero to the basket's per-session sum).
    """
    relevant = [r for r in per_symbol_results if r["cfg_name"] == cfg_name]
    if not relevant:
        return {}

    # Union session dates across all symbols
    all_dates: set = set()
    for r in relevant:
        all_dates.update(r["session_dates"])
    all_dates_sorted = sorted(all_dates)

    # Build per-symbol session log-return lookup
    sym_lookup: dict[str, dict[str, float]] = {}
    for r in relevant:
        d = {sd: lr for sd, lr in zip(r["session_dates"], r["session_log_returns"], strict=True)}
        sym_lookup[r["symbol"]] = d

    # Per-session basket log-return = (1/N) sum of per-symbol log-returns (zero if missing)
    n_sym = len(relevant)
    basket_log_returns: list[float] = []
    for sd in all_dates_sorted:
        per_sym = [sym_lookup[r["symbol"]].get(sd, 0.0) for r in relevant]
        basket_log_returns.append(sum(per_sym) / n_sym)
    basket_log_ret_arr = np.array(basket_log_returns)

    # Equity curve from basket log-returns
    basket_eq = starting_equity * np.exp(np.cumsum(basket_log_ret_arr))
    basket_eq_full = np.concatenate([[starting_equity], basket_eq])
    basket_running_max = np.maximum.accumulate(basket_eq_full)
    basket_dd = (basket_eq_full - basket_running_max) / basket_running_max
    basket_max_dd_pct = float(-basket_dd.min()) * 100 if basket_dd.size > 0 else 0.0
    basket_end = float(basket_eq_full[-1])

    # Aggregate trade counts
    total_wins = sum(r["wins"] for r in relevant)
    total_losses = sum(r["losses"] for r in relevant)
    total_zeros = sum(r["zeros"] for r in relevant)
    total_trades = sum(r["n_trades"] for r in relevant)

    # Basket MPPM(ρ=1) + CI on basket per-session simple-returns
    basket_simple = np.expm1(basket_log_ret_arr)
    if basket_simple.size >= 4:
        mppm_b = float(
            mppm_rho_1(basket_simple, risk_free=0.0, delta_t=1.0 / _ANNUALIZATION_FACTOR)
        )
        try:
            mppm_ci_b = mppm_with_ci(
                basket_simple,
                rho=1.0,
                risk_free=0.0,
                delta_t=1.0 / _ANNUALIZATION_FACTOR,
                n_bootstrap=_N_BOOTSTRAP_CI,
                rng_seed=_RNG_SEED + 100,
            )
            mppm_b_low = float(mppm_ci_b.ci_low)
            mppm_b_high = float(mppm_ci_b.ci_high)
            mppm_b_excludes_zero = bool(mppm_ci_b.excludes_zero)
        except Exception as e:  # noqa: BLE001
            _log.warning("Basket MPPM CI failed for %s: %s", cfg_name, e)
            mppm_b_low = float("nan")
            mppm_b_high = float("nan")
            mppm_b_excludes_zero = False
    else:
        mppm_b = float("nan")
        mppm_b_low = float("nan")
        mppm_b_high = float("nan")
        mppm_b_excludes_zero = False

    # Basket Sharpe (annualised) on per-session log-returns
    if basket_log_ret_arr.size > 1 and basket_log_ret_arr.std(ddof=1) > 0:
        sr_sess = basket_log_ret_arr.mean() / basket_log_ret_arr.std(ddof=1)
        sr_ann_b = sr_sess * np.sqrt(_ANNUALIZATION_FACTOR)
    else:
        sr_ann_b = float("nan")

    # Basket Calmar
    if basket_log_ret_arr.size >= 4:
        try:
            calmar_b = float(
                calmar_ratio(basket_log_ret_arr, annualization_factor=_ANNUALIZATION_FACTOR)
            )
        except Exception:
            calmar_b = float("nan")
    else:
        calmar_b = float("nan")

    # Basket-level R-multiples = concatenated per-symbol per-trade R-multiples
    # weighted equally — operationally aggregated by simple concat (each symbol
    # contributes its raw R-mult sequence). This preserves per-trade granularity
    # without weighting basket-allocation differences.
    # We don't have per-trade R-multiples in per_symbol_results; reconstruct from
    # session counts is lossy. Defer to basket-level via session-aggregate.
    # For L-skew + R-mean at basket level: use the per-symbol-weighted-average
    # of point estimates (NOT bootstrap; bootstrap on basket aggregate is the
    # MPPM CI path above).
    sym_r_means = [r["r_multiple_mean"] for r in relevant]
    sym_taus = [r["l_skewness_tau3"] for r in relevant
                if r["l_skewness_tau3"] is not None and np.isfinite(r["l_skewness_tau3"])]
    basket_r_mean = float(np.mean(sym_r_means)) if sym_r_means else float("nan")
    basket_tau3 = float(np.mean(sym_taus)) if sym_taus else float("nan")

    # Profit factor (basket-level): aggregate per-session basket P/L
    sym_pf_pnls: list[list[float]] = []
    for r in relevant:
        # Per-symbol per-session $-P/L derived from session_log_returns × symbol_equity_basis
        # The per_symbol_results carry raw $-pnl arrays as well
        sym_pf_pnls.append(r["session_pnls"])
    # Build a basket per-session $-pnl: sum aligned-on-date with zero-fill
    sym_pnl_lookup: dict[str, dict[str, float]] = {}
    for r in relevant:
        d = {sd: pn for sd, pn in zip(r["session_dates"], r["session_pnls"], strict=True)}
        sym_pnl_lookup[r["symbol"]] = d
    basket_pnls: list[float] = []
    for sd in all_dates_sorted:
        per_sym_pnl = [sym_pnl_lookup[r["symbol"]].get(sd, 0.0) for r in relevant]
        basket_pnls.append(sum(per_sym_pnl) / n_sym)
    basket_pnls_arr = np.array(basket_pnls)
    pf_b = profit_factor(basket_pnls_arr) if basket_pnls_arr.size else 0.0

    # ---- Sub-window basket aggregation ----
    def _to_date_basket(d: object) -> object:
        if isinstance(d, _dt.date) and not isinstance(d, _dt.datetime):
            return d
        try:
            return pd.Timestamp(d).date()
        except Exception:
            return d

    sub_dates = [sd for sd in all_dates_sorted
                 if _SUBWINDOW_START <= _to_date_basket(sd) <= _SUBWINDOW_END]
    if sub_dates:
        # For each sub-date: average per-symbol log-return (treating missing as 0)
        sub_log_rets_list = []
        for sd in sub_dates:
            per_sym = [sym_lookup[r["symbol"]].get(sd, 0.0) for r in relevant]
            sub_log_rets_list.append(sum(per_sym) / n_sym)
        sub_log_rets = np.array(sub_log_rets_list)
        sub_basket_eq = starting_equity * np.exp(np.cumsum(sub_log_rets))
        sub_basket_eq_full = np.concatenate([[starting_equity], sub_basket_eq])
        sub_running_max_b = np.maximum.accumulate(sub_basket_eq_full)
        sub_dd_b = (sub_basket_eq_full - sub_running_max_b) / sub_running_max_b
        sub_max_dd_b_pct = float(-sub_dd_b.min()) * 100
        sub_end_b = float(sub_basket_eq_full[-1])
        sub_roi_b_pct = (sub_end_b / starting_equity - 1.0) * 100
    else:
        sub_max_dd_b_pct = 0.0
        sub_end_b = starting_equity
        sub_roi_b_pct = 0.0

    sub_wins_b = sum(r["subwindow_wins"] for r in relevant)
    sub_losses_b = sum(r["subwindow_losses"] for r in relevant)
    sub_zeros_b = sum(r["subwindow_zeros"] for r in relevant)
    sub_trades_b = sum(r["subwindow_n_trades"] for r in relevant)

    return {
        "cfg_name": cfg_name,
        "is_basket": True,
        "symbol": "BASKET",
        "tp_multiplier_M": relevant[0]["tp_multiplier_M"],
        "kelly_multiplier": relevant[0]["kelly_multiplier"],
        "realized_end_equity": basket_end,
        "realized_roi_pct": (basket_end / starting_equity - 1.0) * 100,
        "realized_max_dd_pct": basket_max_dd_pct,
        "wins": total_wins,
        "losses": total_losses,
        "zeros": total_zeros,
        "win_rate": total_wins / max(total_trades, 1),
        "n_trades": total_trades,
        "sr_annualised": float(sr_ann_b) if np.isfinite(sr_ann_b) else None,
        "calmar": float(calmar_b) if np.isfinite(calmar_b) else None,
        "profit_factor": float(pf_b) if np.isfinite(pf_b) else None,
        "r_multiple_mean": basket_r_mean,
        "mppm_rho1": mppm_b,
        "mppm_rho1_ci_low": mppm_b_low,
        "mppm_rho1_ci_high": mppm_b_high,
        "mppm_rho1_excludes_zero": mppm_b_excludes_zero,
        "l_skewness_tau3": basket_tau3,
        "subwindow_realized_end_equity": sub_end_b,
        "subwindow_realized_roi_pct": sub_roi_b_pct,
        "subwindow_realized_max_dd_pct": sub_max_dd_b_pct,
        "subwindow_wins": sub_wins_b,
        "subwindow_losses": sub_losses_b,
        "subwindow_zeros": sub_zeros_b,
        "subwindow_n_trades": sub_trades_b,
    }


def _format_kpi_table(rows: list[dict[str, Any]]) -> str:
    """Return the H065 §13 KPI metrics table as a printable string.

    Per H065 design.md §13 deliverable specification — the load-bearing
    operator-facing artifact.
    """
    lines: list[str] = []
    lines.append("=" * 240)
    lines.append("H065 TP-OVERLAY SWEEP — KPI METRICS TABLE (per design.md §13)")
    lines.append("=" * 240)
    hdr = (
        f"{'Config':<28} {'M':>6} {'Kelly':>6} {'Symbol':<8} "
        f"{'OOS_ROI%':>9} {'MaxDD%':>8} {'W/L/Z':>16} "
        f"{'Sharpe':>8} {'Calmar':>8} {'PF':>6} {'R_mean':>7} "
        f"{'MPPM_low':>9} {'MPPM_pt':>9} {'MPPM_hi':>9} {'tau3':>7} "
        f"{'n_trd':>7} "
        f"{'subROI%':>9} {'subDD%':>8}"
    )
    lines.append(hdr)
    lines.append("-" * 240)
    for r in rows:
        m_str = f"{r['tp_multiplier_M']:.1f}" if r['tp_multiplier_M'] is not None else "inf"
        k_str = f"{r['kelly_multiplier']:.2f}" if r.get('kelly_multiplier') else "n/a"
        sr_str = f"{r['sr_annualised']:.3f}" if r.get('sr_annualised') is not None else "n/a"
        calmar_str = f"{r['calmar']:.3f}" if r.get('calmar') is not None else "n/a"
        pf_str = f"{r['profit_factor']:.2f}" if r.get('profit_factor') is not None else "n/a"
        wlz = f"{r['wins']}/{r['losses']}/{r['zeros']}"
        line = (
            f"{r['cfg_name']:<28} {m_str:>6} {k_str:>6} {r['symbol']:<8} "
            f"{r['realized_roi_pct']:>+8.2f}% {r['realized_max_dd_pct']:>+7.2f}% "
            f"{wlz:>16} "
            f"{sr_str:>8} {calmar_str:>8} {pf_str:>6} {r['r_multiple_mean']:>+7.3f} "
            f"{r['mppm_rho1_ci_low']:>+9.3f} {r['mppm_rho1']:>+9.3f} {r['mppm_rho1_ci_high']:>+9.3f} "
            f"{r['l_skewness_tau3']:>+7.3f} "
            f"{r['n_trades']:>7} "
            f"{r['subwindow_realized_roi_pct']:>+8.2f}% {r['subwindow_realized_max_dd_pct']:>+7.2f}%"
        )
        lines.append(line)
    lines.append("=" * 240)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H065 TP-overlay sweep")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=["ES", "NQ", "MGC", "SIL"],
        help="Subset of symbols to sweep (default: all 4).",
    )
    parser.add_argument(
        "--kelly-multiplier",
        type=float,
        default=0.25,
        help="Kelly multiplier cell (default 0.25 = H062 v1 modal).",
    )
    parser.add_argument(
        "--end-date",
        default="2026-05-15",
        help="OOS test end date (UTC) ISO format (default 2026-05-15).",
    )
    args = parser.parse_args(argv)

    if args.substrate_path:
        substrate_root = Path(args.substrate_path).resolve()
    else:
        substrate_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"

    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else _REPO_ROOT / "artifacts" / "runs" / "H065"
            / f"tp_overlay_sweep_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    start = pd.Timestamp("2020-01-01", tz="UTC")
    end_master = pd.Timestamp(args.end_date, tz="UTC")
    end_per_symbol = {
        "ES":  end_master,
        "NQ":  end_master,
        "MGC": end_master,
        "SIL": end_master,
    }

    feat_cfg = H062FeatureConfig(
        channel_n=120,
        atr_n=14,
        h_dwell=5,
        trend_id="a_ts_mom",
        trend_id_lookback_l=60,
        trend_id_threshold=1.0,
    )
    k_atr = 2.0

    sweep_configs = _build_sweep_configs(kelly_multiplier=args.kelly_multiplier)

    per_symbol_results: list[dict[str, Any]] = []
    for sym in args.symbols:
        sym_end = end_per_symbol.get(sym, end_master)
        _log.info("Loading %s [%s → %s]...", sym, start.date(), sym_end.date())
        df_5m = _load_5min_bars(substrate_root, sym, start=start, end=sym_end)
        _log.info("  %s: %d 5-min bars (%d sessions)",
                  sym, len(df_5m), df_5m["session_date_et"].nunique())

        for cfg in sweep_configs:
            res = _run_tp_overlay_simulation(
                symbol=sym,
                df_5m=df_5m,
                feature_config=feat_cfg,
                k_atr=k_atr,
                cfg=cfg,
            )
            res["cfg_description"] = cfg.description
            per_symbol_results.append(res)
            _log.info(
                "  %s × %s: end=$%.0f (%+.2f%%) MaxDD=%.2f%% n_trades=%d r_mean=%+.3f tau3=%+.3f MPPM=%+.3f [%+.3f,%+.3f] %s",
                sym, cfg.name,
                res["realized_end_equity"], res["realized_roi_pct"], res["realized_max_dd_pct"],
                res["n_trades"], res["r_multiple_mean"], res["l_skewness_tau3"],
                res["mppm_rho1"], res["mppm_rho1_ci_low"], res["mppm_rho1_ci_high"],
                "EXCLUDES_ZERO_POS" if res["mppm_rho1_excludes_zero"] and res["mppm_rho1"] > 0 else "ci-covers-zero",
            )

    # Basket-level aggregations per config
    basket_rows: list[dict[str, Any]] = []
    for cfg in sweep_configs:
        basket_row = _compute_basket_metrics(per_symbol_results, cfg.name)
        if basket_row:
            basket_rows.append(basket_row)

    # ---- Print KPI metrics table per H065 §13 ----
    all_rows: list[dict[str, Any]] = []
    for cfg in sweep_configs:
        # Per-symbol rows for this config (sorted by symbol)
        sym_rows = sorted(
            [r for r in per_symbol_results if r["cfg_name"] == cfg.name],
            key=lambda r: r["symbol"],
        )
        all_rows.extend(sym_rows)
        # Basket row for this config
        for br in basket_rows:
            if br["cfg_name"] == cfg.name:
                all_rows.append(br)
                break

    kpi_table = _format_kpi_table(all_rows)
    print()
    print(kpi_table)
    print()

    # ---- Sidecar payload ----
    payload = {
        "hypothesis_id": "H065",
        "experiment": "tp_overlay_sweep_v1",
        "feature_cell": {
            "channel_n": feat_cfg.channel_n,
            "atr_n": feat_cfg.atr_n,
            "h_dwell": feat_cfg.h_dwell,
            "trend_id": feat_cfg.trend_id,
            "trend_id_lookback_l": feat_cfg.trend_id_lookback_l,
            "trend_id_threshold": feat_cfg.trend_id_threshold,
            "k_atr": k_atr,
        },
        "starting_equity": 10000.0,
        "annualization_factor": _ANNUALIZATION_FACTOR,
        "rng_seed": _RNG_SEED,
        "n_bootstrap_ci": _N_BOOTSTRAP_CI,
        "substrate_dataset_checksum": "b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce",
        "configurations": [
            {
                "name": c.name,
                "description": c.description,
                "tp_multiplier_M": c.tp_multiplier_M if c.tp_enabled else None,
                "kelly_multiplier": c.kelly_multiplier,
                "risk_budget_pct": c.risk_budget_pct,
                "use_current_equity_rebase": c.use_current_equity_rebase,
            } for c in sweep_configs
        ],
        "per_symbol_results": per_symbol_results,
        "basket_results": basket_rows,
        "kpi_table_text": kpi_table,
        "subwindow_definition": {
            "start": str(_SUBWINDOW_START),
            "end": str(_SUBWINDOW_END),
        },
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sweep_sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sweep_sha256.txt").write_text(sha + "\n", encoding="utf-8")
    (out_dir / "kpi_table.txt").write_text(kpi_table, encoding="utf-8")
    _log.info("sweep_sidecar=%s sha256=%s", sidecar_path, sha[:16])
    _log.info("kpi_table=%s", out_dir / "kpi_table.txt")
    print(f"sidecar: {sidecar_path}")
    print(f"sha256:  {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
