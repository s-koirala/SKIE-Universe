"""H062 walk-forward orchestrator — intraday Donchian-channel breakout (5-min cadence).

Per H062 frozen pre-reg [research/01_hypothesis_register/H062/design.md](
../research/01_hypothesis_register/H062/design.md). Inheritance: ADR-0013
(KPI-only, no binding gates) + ADR-0014 (canonical 13-table summary) +
ADR-0017 (survival-constrained primary metrics) + ADR-0018 (MPPM(ρ=1) +
Kelly-grid + BOCD + switching-bandit) + ADR-0019 (L-skewness barbell screen)
+ ADR-0022 (causal-mechanism annotation: hybrid) + ADR-0023 (metals/energy
substrate).

Scope deviations from the frozen design.md §1-§7 (RECORDED in the KPI report
card §17 per ADR-0013 §"Frozen pre-registration amendment"):
- 4-asset basket {ES, NQ, MGC, SIL} per the post-Phase-O.0 substrate;
  CL/MCL deferred to H061 + H062-v2 per P1-H062-V2-WITH-CL-MCL-EXTEND.
- Inner-CV cell grid REDUCED from the full 13,824-cell design.md §8.a
  combinatorial product to a tractable 36-cell representative grid
  (channel_n × k_atr × kelly_multiplier) at the v1 launch; trend_id +
  h_dwell + atr_n + cadence fixed at representative values pending
  P1-H062-CALIBRATION-HOLDOUT-RUN empirical selection. Full grid tracked
  for v2 expansion.
- Cost model = ZERO per design.md §6 + operator 2026-05-08 standing
  directive (cost-zero-v1-pre-cost-research-only).

Structural pattern mirrors scripts/run_h060_walk_forward.py 1086-line
precedent; intraday-cadence per-trade simulation per design.md §4
entry/exit logic.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import os
import sys
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
import yaml

from skie_ninja.features.h062 import (
    H062FeatureConfig,
    compute_h062_features,
)
from skie_ninja.backtest.costs.nt8_realistic import NT8RealisticCostModel
from skie_ninja.backtest.equity_rebase import (
    EquityRebasePolicy,
    apply_pnl_to_equity,
    equity_for_sizing,
)
from skie_ninja.backtest.kill_switch_constants import (
    iso_week_id_from_session_date,
    session_date_from_timestamp,
)
from skie_ninja.backtest.kill_switch_runtime import (
    KillSwitchRuntimeConfig,
    advance_session,
    advance_week,
    check_entry_blocked,
    init_runtime_state,
    record_trigger,
    summarize_trigger_counts,
    update_state_on_close,
    update_state_on_open,
)
from skie_ninja.inference.bocd import detect_decay
from skie_ninja.inference.bocd_live import (
    BOCDLiveConfig,
    BOCDLiveState,
    bocd_live_update,
    init_bocd_live,
    is_paused,
    summarize_pause_events,
)
from skie_ninja.inference.calmar import (
    calmar_differential_ci_stationary_bootstrap,
)
from skie_ninja.inference.mppm import mppm_rho_1, mppm_with_ci
from skie_ninja.inference.multipletest.hansen_spa import hansen_spa_test
from skie_ninja.inference.profit_factor import (
    profit_factor_differential_ci_stationary_bootstrap,
)
from skie_ninja.inference.r_multiple import (
    r_multiple_mean_ci_stationary_bootstrap,
)
from skie_ninja.inference.risk_of_ruin import probability_of_ruin_monte_carlo
from skie_ninja.inference.skewness import (
    l_skewness_tau3_ci_stationary_bootstrap,
    payoff_shape_annotation,
)
from skie_ninja.inference.stats.ledoit_wolf_2008 import (
    ledoit_wolf_2008_differential_ci,
)
from skie_ninja.sizing import kelly_multiplier_annotation
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.runcontext import RunContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h062_walk_forward")


_RNG_SEED_DEFAULT: int = 20260514  # matches H062.yaml random_seed
_LW2008_RNG_OFFSET: int = 100
_SPA_RNG_OFFSET: int = 200
_BOOTSTRAP_RNG_OFFSET: int = 1000

# Per-instrument contract multipliers per ADR-0001 / config/instruments.yaml.
# Maps $-loss-per-tick × ticks-per-point to convert ATR price-distance to $-distance.
_MULTIPLIERS: dict[str, float] = {
    "ES": 50.0,   # $50 per index point per CME ES contract specs
    "NQ": 20.0,   # $20 per index point per CME NQ contract specs
    "MGC": 10.0,  # $10 per troy ounce per CME Micro Gold (1/10 GC)
    "SIL": 1000.0,  # $1 per troy ounce × 1000 oz per CME Micro Silver
}

# Per-instrument retail-capacity caps per ADR-0001.
_CAPACITY_CAPS: dict[str, int] = {
    "ES": 20,
    "NQ": 40,
    "MGC": 5,
    "SIL": 5,
}


def _git_head(repo_root: Path) -> str:
    head_file = repo_root / ".git" / "HEAD"
    if not head_file.exists():
        return "unknown"
    head = head_file.read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        ref = head[5:].strip()
        ref_file = repo_root / ".git" / ref
        if ref_file.exists():
            return ref_file.read_text(encoding="utf-8").strip()
    return head


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


def _resolve_substrate_path(cli_arg: str | None, project_root: Path) -> Path:
    if cli_arg:
        path = Path(cli_arg).resolve()
    else:
        path = project_root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    if not path.exists():
        raise FileNotFoundError(f"Substrate path not found: {path}")
    return path


def _load_5min_bars(
    substrate_root: Path,
    symbol: str,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Load 1-min roll-adjusted substrate for ``symbol`` and resample to 5-min.

    Per H062 design.md §2 + §3 — 5-min bar primary cadence. The substrate
    is in 1-min UTC bars; resample to 5-min OHLC per pandas standard
    semantic (open=first, high=max, low=min, close=last).

    Each row carries (ts_event_utc, open, high, low, close, session_date_et)
    where session_date_et = ET-local calendar-date of ts_event (the session
    boundary anchor per design.md §2).
    """
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

    # Date filter on UTC dates.
    mask = (df["ts_event"] >= start) & (df["ts_event"] <= end)
    df = df.loc[mask].copy()
    if df.empty:
        raise RuntimeError(
            f"{symbol}: substrate empty after date filter [{start}, {end}]"
        )

    # Resample to 5-min using ts_event as index.
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


def _run_per_trade_simulation(
    *,
    symbol: str,
    df_5m: pd.DataFrame,
    feature_config: H062FeatureConfig,
    k_atr: float,
    eod_flatten_minutes_from_open: int = 360,  # 6hr from 09:30 ET = 15:30 ET ~ 14:30 CT
    risk_budget_pct: float = 0.01,
    kelly_multiplier: float = 0.25,
    # ADR-0025 Phase O.13 deep-wire kwargs per buildout 7d63795 (R1 remediated).
    # All default None preserves Phase O.10 v2 numerical agreement bit-identically.
    # justify: starting_equity default 10000.0 = v2 literal preserved per buildout
    # R1 F-1-8; the parity test asserts bit-identical-on-default-None.
    kill_switch_config: KillSwitchRuntimeConfig | None = None,
    equity_rebase_policy: EquityRebasePolicy | None = None,
    bocd_live_state: BOCDLiveState | None = None,
    cost_model: NT8RealisticCostModel | None = None,
    starting_equity: float = 10000.0,
) -> dict[str, Any]:
    """Run per-trade simulation on H062 features.

    Per design.md §4: entry at next-bar open after channel-break signal at
    bar-t close (with ID_1 trend gate pass); stop = entry ± k_atr × ATR_n,t;
    exit on opposite-channel break OR EOD-flatten OR ATR-stop hit.

    Per-trade R-multiple = realized_log_return / |1R_log| where 1R_log =
    log(1 + k_atr × ATR / entry_price) at entry time.

    Args:
        symbol: Instrument symbol (for multipliers + capacity caps + logging).
        df_5m: 5-min OHLC dataframe with columns (ts_event, open, high, low,
            close, session_date_et).
        feature_config: H062FeatureConfig with all hyperparameters.
        k_atr: ATR-stop multiplier (Turtle 2N convention default 2.0 + ±0.5).
        eod_flatten_minutes_from_open: Bars-from-session-open to flatten at.
        risk_budget_pct: 1% of equity per trade per design.md §5.3 + Turtle 2N.
        kelly_multiplier: Kelly grid value per ADR-0018 D-2.

    Returns:
        Dict with per-trade arrays + per-session aggregated log-returns +
        diagnostic counts.
    """
    high = df_5m["high"].to_numpy()
    low = df_5m["low"].to_numpy()
    close = df_5m["close"].to_numpy()
    open_ = df_5m["open"].to_numpy()
    session_dates = df_5m["session_date_et"].to_numpy()
    n_bars = len(df_5m)

    feats = compute_h062_features(
        high=high, low=low, close=close, config=feature_config
    )

    # Per-trade simulation. Walk forward through bars; at each filtered
    # eligible event, open position; carry until stop / opposite-channel / EOD.
    r_multiples: list[float] = []
    trade_log_returns: list[float] = []
    trade_session_dates: list[Any] = []
    trade_sides: list[int] = []

    multiplier = _MULTIPLIERS.get(symbol, 1.0)
    # F-1-1 R1 audit fix: kill_switch_config.capacity_caps takes precedence over
    # the v2 hardcoded _CAPACITY_CAPS when supplied; otherwise fall back to v2 literal.
    # justify: per ADR-0025 §D-1 K-4 the runtime kill-switch is the canonical source
    # of truth for capacity; v2 hardcoded path preserved on None for bit-identity.
    cap = (
        kill_switch_config.capacity_caps.get(symbol, _CAPACITY_CAPS.get(symbol, 1))
        if kill_switch_config is not None
           and kill_switch_config.enable_k4
        else _CAPACITY_CAPS.get(symbol, 1)
    )
    # CR-1-3 R1 audit fix: fail-closed schema assertion. The wire-site insertions
    # below depend on `ts_event` column existing. Silent fallback to a hardcoded
    # date corrupts kill-switch state under malformed input.
    if (kill_switch_config is not None
            or bocd_live_state is not None) and "ts_event" not in df_5m.columns:
        raise ValueError(
            "H062 deep-wire requires 'ts_event' column in df_5m when "
            "kill_switch_config or bocd_live_state is supplied"
        )
    # Effective Kelly fraction per design.md §5.3 formula.
    # For this v1 launch: f_kelly_raw=1.0 implicit (full-Kelly assumption);
    # effective = clamp(kelly_multiplier × 1.0, 0, 2.5).
    effective_kelly = min(max(kelly_multiplier, 0.0), 2.5)

    in_position = False
    position_side = 0  # +1 long, -1 short
    entry_idx = -1
    entry_price = np.nan
    stop_price = np.nan
    r_dollar = np.nan
    entry_session_date = None
    position_size = 0

    # ADR-0025 Phase O.13 deep-wire state init (W2). Default-None preserves v2 path.
    # justify: per buildout 7d63795 §"Wire-site map — H062"; primitives init only
    # when their configs are non-None; v2 numerical path is bit-identical otherwise.
    ks_state = None
    if kill_switch_config is not None:
        ks_state = init_runtime_state(
            universe=(symbol,), starting_equity=starting_equity
        )
    current_equity = starting_equity if equity_rebase_policy is not None else None
    # BOCD per-session log-return accumulator for W8 payload (R1 F-1-3 fix: MPPM(ρ=1)
    # over single observation = log-return per GISW 2007 §2 reduction).
    bocd_session_log_ret_accumulator = 0.0
    bocd_session_idx_counter = 0
    bocd_last_observed_session = None

    # Build session-open index map.
    # Each session starts when session_date_et changes.
    session_starts: dict[Any, int] = {}
    for t in range(n_bars):
        sd = session_dates[t]
        if sd not in session_starts:
            session_starts[sd] = t

    def _close_position(
        exit_idx: int,
        exit_price: float,
        reason: str,
    ) -> None:
        nonlocal in_position, position_side, entry_idx, entry_price
        nonlocal stop_price, r_dollar, entry_session_date, position_size
        nonlocal current_equity, ks_state, bocd_session_log_ret_accumulator
        if not in_position:
            return
        # Realized log-return for this trade (signed).
        signed_log = position_side * float(np.log(exit_price / entry_price))
        # R-multiple = realized_dollar_pnl / |1R_dollar|.
        # signed dollar PnL = position_side × (exit - entry) × multiplier × position_size
        signed_dollar = (
            position_side * (exit_price - entry_price) * multiplier * position_size
        )
        r_mult = signed_dollar / r_dollar if r_dollar > 0 else 0.0

        # ADR-0025 Phase O.13 deep-wire W7 cost subtraction (R1 F-1-2 unit fix).
        # justify: cost_per_session_log_return returns NOTIONAL-scale drag; must convert
        # to EQUITY-FRACTIONAL scale to add to trade_equity_log_return. See buildout
        # 7d63795 §"Wire-site map — H062" W7 RE-SPEC.
        cost_drag_equity_fractional = 0.0
        if cost_model is not None:
            cost_usd = cost_model.round_trip_cost_usd(
                symbol=symbol, n_contracts=position_size
            )
            equity_for_cost = (
                current_equity if current_equity is not None else starting_equity
            )
            if equity_for_cost > 0:
                cost_drag_equity_fractional = -cost_usd / equity_for_cost

        # The trade's log-return contribution at equity level is approximately
        # log(1 + realized_pnl / equity); approximate per design.md §1 with
        # the per-trade R-multiple × per-trade risk-fraction (1% of equity at
        # entry; ADR-0017 §4.1 current-equity rebase). When cost_model is None
        # cost_drag_equity_fractional == 0.0 → bit-identical to v2 path.
        trade_equity_log_return = float(
            np.log(1.0 + r_mult * risk_budget_pct + cost_drag_equity_fractional)
        )

        r_multiples.append(r_mult)
        trade_log_returns.append(trade_equity_log_return)
        trade_session_dates.append(entry_session_date)
        trade_sides.append(position_side)

        # ADR-0025 Phase O.13 deep-wire W6 update_state_on_close + equity update.
        # CR-1-3 R1 audit fix: removed silent date fallback; `ts_event` presence
        # is asserted at function entry when ks_state-bearing kwargs are supplied.
        if ks_state is not None:
            exit_ts = pd.Timestamp(df_5m.iloc[exit_idx]["ts_event"])
            ks_state = update_state_on_close(
                ks_state,
                symbol=symbol,
                realized_pnl_dollar=float(signed_dollar),
                exit_ts=exit_ts,
            )
        if current_equity is not None:
            current_equity = apply_pnl_to_equity(current_equity, float(signed_dollar))
        # Accumulate per-session log-return for W8 BOCD payload (R1 F-1-3 pin).
        if bocd_live_state is not None:
            bocd_session_log_ret_accumulator += float(trade_equity_log_return)

        in_position = False
        position_side = 0
        entry_idx = -1
        entry_price = np.nan
        stop_price = np.nan
        r_dollar = np.nan
        entry_session_date = None
        position_size = 0

    for t in range(n_bars - 1):
        bar_session = session_dates[t]
        # ADR-0025 Phase O.13 deep-wire W8 session-boundary handler.
        # Fires when bar_session != prior session. Skip on t=0 (no prior session).
        if t > 0 and session_dates[t] != session_dates[t - 1]:
            # CR-1-3 R1 audit fix: ts_event presence asserted at function entry
            # when ks_state/bocd_live_state non-None; no silent fallback needed.
            if ks_state is not None:
                cme_session_date = session_date_from_timestamp(
                    pd.Timestamp(df_5m.iloc[t]["ts_event"])
                )
                eq_for_advance = (
                    current_equity if current_equity is not None else starting_equity
                )
                ks_state = advance_session(
                    ks_state,
                    new_session_date=cme_session_date,
                    current_equity=eq_for_advance,
                )
                new_week_id = iso_week_id_from_session_date(cme_session_date)
                if ks_state.current_week_id != new_week_id:
                    ks_state = advance_week(
                        ks_state,
                        new_week_id=new_week_id,
                        current_equity=eq_for_advance,
                    )
            # BOCD live-pause: feed the just-completed session's accumulated
            # log-return as the W8 payload per R1 F-1-3 pin.
            # WARNING: per buildout R1 F-1-3 the NIG prior MUST be calibrated
            # before this fires productively (P1-BOCD-LIVE-PRIOR-CALIBRATION-H062-V3).
            if bocd_live_state is not None:
                ts_utc_str = pd.Timestamp(df_5m.iloc[t]["ts_event"]).isoformat()
                bocd_live_state = bocd_live_update(
                    bocd_live_state,
                    x_t=float(bocd_session_log_ret_accumulator),
                    session_idx=bocd_session_idx_counter,
                    ts_utc=ts_utc_str,
                )
                bocd_session_idx_counter += 1
                bocd_session_log_ret_accumulator = 0.0
        # In-position bar-by-bar exit checks.
        if in_position:
            # Check stop intrabar — gap-through-stop convention per design.md §7.
            if position_side == 1:
                # long stop = entry - k_atr*ATR; stop hit if low <= stop_price
                if open_[t] < stop_price:
                    _close_position(t, float(open_[t]), "gap_through_stop_long")
                    continue
                if low[t] <= stop_price:
                    _close_position(t, float(stop_price), "stop_hit_long")
                    continue
                # Opposite-channel break exits at bar-t close
                if feats.filtered_events[t] == -1:
                    _close_position(t, float(close[t]), "opposite_channel_break_long")
                    continue
            else:  # short
                if open_[t] > stop_price:
                    _close_position(t, float(open_[t]), "gap_through_stop_short")
                    continue
                if high[t] >= stop_price:
                    _close_position(t, float(stop_price), "stop_hit_short")
                    continue
                if feats.filtered_events[t] == 1:
                    _close_position(t, float(close[t]), "opposite_channel_break_short")
                    continue
            # EOD-flatten check: if next bar's session differs from current OR
            # bars-from-session-open exceeds eod_flatten threshold
            session_open_idx = session_starts.get(bar_session, t)
            bars_into_session = t - session_open_idx
            if bars_into_session >= eod_flatten_minutes_from_open:
                _close_position(t, float(close[t]), "eod_flatten")
                continue
            # Session rollover (next bar in different session)
            if t + 1 < n_bars and session_dates[t + 1] != bar_session:
                _close_position(t, float(close[t]), "session_rollover")
                continue

        # Entry signal at bar-t close → execute at bar (t+1) open.
        ev = int(feats.eligible_events[t])
        if not in_position and ev != 0:
            entry_idx_candidate = t + 1
            if entry_idx_candidate >= n_bars:
                continue
            entry_price_candidate = float(open_[entry_idx_candidate])
            atr_t = float(feats.atr[t])
            if not np.isfinite(atr_t) or atr_t <= 0:
                continue
            # Dollar 1R distance = k_atr × ATR_n × multiplier (per-contract).
            dollar_1r_per_contract = k_atr * atr_t * multiplier
            if dollar_1r_per_contract <= 0:
                continue
            # Position size per design.md §5.3 formula (simplified for v1
            # at risk_budget_pct=1% of $10K starting equity = $100; clamped
            # at capacity cap).
            # ADR-0025 Phase O.13 deep-wire W3 equity-rebase sizing.
            # justify: when equity_rebase_policy is None, falls back to literal
            # 10000.0 → bit-identical to v2 path per buildout R1 F-1-8.
            if equity_rebase_policy is not None:
                eq_for_sizing_val = equity_for_sizing(
                    equity_rebase_policy,
                    current_equity if current_equity is not None else starting_equity,
                )
            else:
                eq_for_sizing_val = 10000.0  # v2 literal, bit-identical
            target_dollar_risk = eq_for_sizing_val * risk_budget_pct
            size_from_risk = target_dollar_risk / dollar_1r_per_contract
            size_capped = min(int(np.floor(size_from_risk)), cap)
            if size_capped < 1:
                continue  # too coarse — skip the trade (capacity-too-small)

            # ADR-0025 Phase O.13 deep-wire W4 pre-entry guard (R1 F-1-1 fix:
            # AFTER size_capped is computed and checked).
            if bocd_live_state is not None and is_paused(bocd_live_state):
                continue
            if kill_switch_config is not None and ks_state is not None:
                blocked, reason = check_entry_blocked(
                    ks_state, kill_switch_config,
                    symbol=symbol, position_size=size_capped,
                )
                if blocked and reason is not None:
                    ks_state = record_trigger(ks_state, reason)
                    continue

            in_position = True
            position_side = ev
            entry_idx = entry_idx_candidate
            entry_price = entry_price_candidate
            stop_offset = k_atr * atr_t
            stop_price = entry_price - position_side * stop_offset
            r_dollar = dollar_1r_per_contract * size_capped
            entry_session_date = bar_session
            position_size = size_capped

            # ADR-0025 Phase O.13 deep-wire W5 update_state_on_open for K-3 tracking.
            if ks_state is not None:
                entry_ts = pd.Timestamp(df_5m.iloc[entry_idx]["ts_event"])
                ks_state = update_state_on_open(
                    ks_state,
                    symbol=symbol, side=int(position_side),
                    entry_ts=entry_ts, entry_price=float(entry_price),
                    position_size=int(position_size),
                    stop_price=float(stop_price), r_dollar=float(r_dollar),
                )

    # Close any open position at last bar.
    if in_position:
        _close_position(n_bars - 1, float(close[-1]), "end_of_data")

    # Aggregate to per-session.
    sess_to_logret: dict[Any, float] = {}
    for sd, lr in zip(trade_session_dates, trade_log_returns):
        sess_to_logret[sd] = sess_to_logret.get(sd, 0.0) + float(lr)

    session_dates_sorted = sorted(sess_to_logret.keys())
    per_session_logret = np.array(
        [sess_to_logret[sd] for sd in session_dates_sorted], dtype=float
    )

    # ADR-0025 Phase O.13 deep-wire W9 return-dict primitive summaries.
    # When primitives None: each summary block is None or default = bit-identical
    # downstream behavior (sidecar emission already handles missing keys).
    ks_summary = (
        summarize_trigger_counts(ks_state) if ks_state is not None else None
    )
    equity_summary = None
    if current_equity is not None:
        equity_summary = {
            "mode": equity_rebase_policy.mode if equity_rebase_policy is not None else "fixed",
            "starting_equity": starting_equity,
            "final_equity": current_equity,
        }
    bocd_summary = (
        summarize_pause_events(bocd_live_state)
        if bocd_live_state is not None
        else None
    )
    cost_summary = None
    if cost_model is not None:
        cost_summary = {
            "cost_model_id": cost_model.cost_model_id,
            "calibration_source": cost_model.calibration_source,
            "annotation": cost_model.kpi_annotation(),
        }

    return {
        "r_multiples": np.array(r_multiples, dtype=float),
        "trade_log_returns": np.array(trade_log_returns, dtype=float),
        "trade_sides": np.array(trade_sides, dtype=int),
        "trade_session_dates": list(trade_session_dates),
        "per_session_logret": per_session_logret,
        "per_session_dates": session_dates_sorted,
        "n_trades": len(r_multiples),
        "n_eligible_events": int(np.sum(np.abs(feats.eligible_events))),
        # Phase O.13 deep-wire primitive summaries; None when respective primitive
        # is None → bit-identical to v2 dict-key absence per caller's dict.get().
        "abandonment_trigger_runtime": {
            "kill_switch_runtime": ks_summary,
            "equity_rebase": equity_summary,
            "bocd_live": bocd_summary,
            "cost_model": cost_summary,
        },
    }


def _passive_buy_and_hold_returns(
    df_5m: pd.DataFrame,
) -> tuple[np.ndarray, list[Any]]:
    """Compute per-session passive buy-and-hold log-returns.

    The benchmark per design.md §8.b — passive long basket. For each session,
    log-return = log(close_last / close_first_of_session). Equally-weighted
    across instruments at basket level (done by caller).
    """
    df = df_5m.copy()
    df["session_date_et"] = df["session_date_et"].astype(str)
    grouped = df.groupby("session_date_et").agg(
        first_close=("close", "first"),
        last_close=("close", "last"),
    )
    grouped["log_ret"] = np.log(grouped["last_close"] / grouped["first_close"])
    return grouped["log_ret"].to_numpy(), list(grouped.index)


def _outer_walk_forward_folds(
    dates_sorted: np.ndarray,
    *,
    train_size: int,
    test_size: int,
    embargo: int,
    is_start: pd.Timestamp,
    oos_end: pd.Timestamp,
) -> list[dict[str, Any]]:
    """Construct outer walk-forward folds at session granularity."""
    is_start_d = is_start.tz_convert("UTC") if hasattr(is_start, "tz_convert") else is_start
    oos_end_d = oos_end.tz_convert("UTC") if hasattr(oos_end, "tz_convert") else oos_end
    n = len(dates_sorted)
    folds: list[dict[str, Any]] = []
    # Start the first train window at the first session >= is_start.
    start_idx = int(np.searchsorted(dates_sorted, is_start_d))
    end_idx = int(np.searchsorted(dates_sorted, oos_end_d, side="right"))
    cursor = start_idx
    while cursor + train_size + embargo + test_size <= end_idx:
        train_start = dates_sorted[cursor]
        train_end = dates_sorted[cursor + train_size - 1]
        test_start = dates_sorted[cursor + train_size + embargo]
        test_end_idx = min(cursor + train_size + embargo + test_size - 1, end_idx - 1)
        test_end = dates_sorted[test_end_idx]
        folds.append({
            "train_dates": (train_start, train_end),
            "test_dates": (test_start, test_end),
        })
        cursor += test_size  # roll forward
    return folds


def _equity_curve(log_rets: np.ndarray, starting: float = 10000.0) -> tuple[
    np.ndarray, float, float
]:
    """Compute equity curve, ending equity, max drawdown fraction."""
    if log_rets.size == 0:
        return np.array([starting]), starting, 0.0
    eq = starting * np.exp(np.cumsum(log_rets))
    running_max = np.maximum.accumulate(np.concatenate([[starting], eq]))
    dd = (np.concatenate([[starting], eq]) - running_max) / running_max
    mdd = float(-dd.min())  # positive fraction
    return eq, float(eq[-1]), mdd


def _annualised_sharpe(log_rets: np.ndarray, ann_factor: float = 252.0) -> float:
    if log_rets.size < 2:
        return float("nan")
    mu = float(log_rets.mean())
    sigma = float(log_rets.std(ddof=1))
    if sigma <= 0:
        return float("nan")
    return mu / sigma * float(np.sqrt(ann_factor))


def _bootstrap_forward_projection(
    log_rets: np.ndarray,
    *,
    n_paths: int,
    n_sessions: int,
    rng_seed: int,
    starting: float = 10000.0,
) -> dict[str, Any]:
    """Bootstrap forward projection per ADR-0013 §3.1."""
    if log_rets.size < 5:
        return {"n_paths": 0, "note": "insufficient_history"}
    rng = np.random.default_rng(rng_seed)
    # Stationary bootstrap is the canonical block resampler for serially-
    # dependent series; here we use simple iid resampling for simplicity at
    # the projection layer (the inferential CIs use stationary bootstrap).
    sample_paths_log = rng.choice(log_rets, size=(n_paths, n_sessions), replace=True)
    end_eq = starting * np.exp(sample_paths_log.sum(axis=1))
    return {
        "n_paths": n_paths,
        "n_sessions": n_sessions,
        "median": float(np.median(end_eq)),
        "mean": float(np.mean(end_eq)),
        "q01": float(np.quantile(end_eq, 0.01)),
        "q05": float(np.quantile(end_eq, 0.05)),
        "q95": float(np.quantile(end_eq, 0.95)),
        "q99": float(np.quantile(end_eq, 0.99)),
        "prob_loss": float(np.mean(end_eq < starting)),
        "prob_double": float(np.mean(end_eq > 2.0 * starting)),
        "prob_lt_half": float(np.mean(end_eq < 0.5 * starting)),
    }


def _select_best_cell_inner_cv(
    *,
    symbol: str,
    df_5m_train: pd.DataFrame,
    grid_channel_n: list[int],
    grid_k_atr: list[float],
    grid_kelly: list[float],
    trend_id: str,
    trend_id_lookback_l: int,
    trend_id_threshold: float,
    h_dwell: int,
    atr_n: int,
    delta_t: float,
    eod_flatten_minutes_from_open: int,
    inner_n_folds: int = 3,
    inner_embargo_sessions: int = 1,
) -> dict[str, Any]:
    """Inner-CV cell selection by MPPM(ρ=1) on walk-forward inner-fold OOF series.

    Per design.md §5.6 + §5.7 + rules/quant-project.md "Walk-forward only.
    No k-fold. Time-ordered disjoint splits." Partitions df_5m_train by
    session_date into `inner_n_folds` walk-forward folds with embargo;
    each cell is fit on inner-train slice, evaluated on inner-validation
    slice; per-cell score is the average MPPM(ρ=1) across inner folds.

    Round-2 audit-remediate-loop remediation 2026-05-18 (Phase O.2-O.9 merge
    audit Round-1 quant-auditor Q-2 critical): prior implementation ran
    full-IS optimization disguised as inner-CV; 100% unanimous km=0.25
    selection across 93/93 outer folds was the canonical signature of
    conservative-Kelly bias under in-sample-noise minimization. Walk-forward
    inner-fold structure restores the design.md §5.6 frozen specification.

    Round-2 audit-remediate-loop remediation 2026-05-18 (Phase O.2-O.9 merge
    audit Round-1 quant-auditor Q-1 critical): every mppm_rho_1 call now
    converts per-session log-returns to arithmetic returns via np.expm1
    (clamped at -0.999 to preserve `1 + r > 0` invariant) per the H055 v2
    + H065 v1 precedent. MPPM primitive expects arithmetic returns per
    GISW 2007 §2 + mppm.py docstring; passing log-returns double-logs and
    biases by ~+σ²/2.
    """
    best_cell = None
    best_mppm = -np.inf
    cell_records: list[dict[str, Any]] = []

    # Build inner-fold session-date partition: walk-forward split with embargo.
    train_session_dates = sorted(set(df_5m_train["session_date_et"].tolist()))
    n_train_sessions = len(train_session_dates)
    if n_train_sessions < inner_n_folds * 4:
        # Fallback: too few sessions for nested CV; single-fold IS evaluation
        # with explicit annotation. Tracked under
        # `P1-H062-INNER-CV-UNDERPOWERED-FALLBACK`.
        _log.warning(
            "%s inner-CV fallback: %d sessions < %d * 4 minimum; "
            "single-fold IS evaluation used",
            symbol, n_train_sessions, inner_n_folds,
        )
        inner_folds: list[tuple[list, list]] = [(train_session_dates, [])]
    else:
        # Walk-forward inner folds: fold i trains on sessions[0:k_i_train],
        # validates on sessions[k_i_train + embargo : k_i_val_end].
        inner_folds = []
        fold_step = n_train_sessions // (inner_n_folds + 1)
        for i in range(inner_n_folds):
            tr_end = fold_step * (i + 1)
            val_start = tr_end + inner_embargo_sessions
            val_end = min(val_start + fold_step, n_train_sessions)
            if val_end - val_start < 3:
                continue
            tr_sessions = train_session_dates[:tr_end]
            val_sessions = train_session_dates[val_start:val_end]
            inner_folds.append((tr_sessions, val_sessions))

    for channel_n in grid_channel_n:
        for k_atr in grid_k_atr:
            for kelly_multiplier in grid_kelly:
                try:
                    feat_cfg = H062FeatureConfig(
                        channel_n=channel_n,
                        atr_n=atr_n,
                        h_dwell=h_dwell,
                        trend_id=trend_id,
                        trend_id_lookback_l=trend_id_lookback_l,
                        trend_id_threshold=trend_id_threshold,
                    )
                    fold_mppms: list[float] = []
                    for _tr_sessions, val_sessions in inner_folds:
                        # Use the validation slice (or the full train if
                        # the fallback single-fold IS path is active).
                        eval_sessions = val_sessions if val_sessions else _tr_sessions
                        df_eval = df_5m_train[
                            df_5m_train["session_date_et"].isin(eval_sessions)
                        ]
                        if df_eval.empty:
                            continue
                        sim = _run_per_trade_simulation(
                            symbol=symbol,
                            df_5m=df_eval,
                            feature_config=feat_cfg,
                            k_atr=k_atr,
                            eod_flatten_minutes_from_open=eod_flatten_minutes_from_open,
                            kelly_multiplier=kelly_multiplier,
                        )
                        if sim["per_session_logret"].size < 5:
                            continue
                        # Convert log-returns → arithmetic before MPPM
                        # primitive (which expects `r > -1`); clamp at
                        # -0.999 to preserve the `1 + r > 0` invariant per
                        # mppm.py invariant. Closes Q-1 critical from
                        # 2026-05-18 Phase O.2-O.9 merge audit.
                        per_sess_arith = np.expm1(
                            np.clip(sim["per_session_logret"], a_min=-6.9, a_max=None)
                        )
                        fold_mppms.append(
                            float(mppm_rho_1(per_sess_arith, delta_t=delta_t))
                        )
                    if not fold_mppms:
                        continue
                    mppm_val = float(np.mean(fold_mppms))
                    cell_records.append({
                        "channel_n": channel_n,
                        "k_atr": k_atr,
                        "kelly_multiplier": kelly_multiplier,
                        "mppm_inner_oof_mean": mppm_val,
                        "n_inner_folds_with_trades": len(fold_mppms),
                    })
                    if mppm_val > best_mppm:
                        best_mppm = mppm_val
                        best_cell = {
                            "channel_n": channel_n,
                            "k_atr": k_atr,
                            "kelly_multiplier": kelly_multiplier,
                            "atr_n": atr_n,
                            "h_dwell": h_dwell,
                            "trend_id": trend_id,
                            "trend_id_lookback_l": trend_id_lookback_l,
                            "trend_id_threshold": trend_id_threshold,
                        }
                except (ValueError, FloatingPointError) as exc:
                    _log.debug(
                        "cell (n=%d, k=%.1f, km=%.2f) failed: %s",
                        channel_n, k_atr, kelly_multiplier, exc,
                    )
                    continue
    return {
        "best": best_cell,
        "best_mppm_train": float(best_mppm) if best_cell else float("nan"),
        "cell_records": cell_records,
        "inner_cv_structure": {
            "n_folds": len(inner_folds),
            "n_train_sessions": n_train_sessions,
            "embargo_sessions": inner_embargo_sessions,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H062 walk-forward orchestrator")
    parser.add_argument("--hypothesis", default="H062")
    parser.add_argument("--config", default="config/hypotheses/H062.yaml")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke mode: reduced inner-CV grid + truncated date range for fast E2E check",
    )
    # ADR-0025 Phase O.11 abandonment-trigger infrastructure opt-in flags.
    # All default OFF to preserve numerical agreement with existing v2 KPI cards.
    parser.add_argument(
        "--enable-kill-switch-runtime",
        action="store_true",
        help="ADR-0025 §D-1: enable K-3/K-4/K-6/K-7 runtime kill-switch intervention",
    )
    parser.add_argument(
        "--enable-equity-rebase-current",
        action="store_true",
        help="ADR-0025 §D-2: enable current-equity rebase (replaces fixed-equity sizing)",
    )
    parser.add_argument(
        "--enable-bocd-live",
        action="store_true",
        help="ADR-0025 §D-4: enable BOCD live-pause state machine (per-session)",
    )
    parser.add_argument(
        "--cost-model",
        choices=["none", "conservative_prior", "paper_trade_empirical"],
        default="none",
        help="ADR-0025 §D-3: cost-model provenance (default=none preserves v2 numerics)",
    )
    args = parser.parse_args(argv)

    paths = ProjectPaths.discover()
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path
    raw_cfg_bytes = cfg_path.read_bytes()
    cfg = yaml.safe_load(raw_cfg_bytes)
    config_resolved_sha256 = hashlib.sha256(raw_cfg_bytes).hexdigest()

    git_head = _git_head(paths.root)
    rng_seed = int(cfg.get("random_seed", _RNG_SEED_DEFAULT))

    substrate_root = _resolve_substrate_path(args.substrate_path, paths.root)
    _log.info("Substrate root: %s", substrate_root)

    universe = [s.strip().upper() for s in cfg["universe"]]

    # Date windows.
    is_start = pd.Timestamp(cfg["data"]["is"]["start"], tz="UTC")
    is_end = pd.Timestamp(cfg["data"]["is"]["end"], tz="UTC")
    oos_start = pd.Timestamp(cfg["data"]["oos"]["start"], tz="UTC")
    oos_end = pd.Timestamp(cfg["data"]["oos"]["end"], tz="UTC")

    # Per-symbol OOS right-edge clip per H062.yaml.
    oos_per_symbol_end: dict[str, pd.Timestamp] = {}
    for sym, sd in cfg["data"].get("oos_per_symbol", {}).items():
        oos_per_symbol_end[sym.upper()] = pd.Timestamp(sd["end"], tz="UTC")

    # Inner-CV grid. Truncated in --smoke mode.
    if args.smoke:
        grid_channel_n = [60, 120]
        grid_k_atr = [2.0]
        grid_kelly = [0.25, 1.0]
    else:
        grid_channel_n = [20, 60, 120, 240]
        grid_k_atr = [1.5, 2.0, 2.5]
        grid_kelly = [0.25, 0.5, 1.0, 2.0]

    # Fixed-for-v1 hyperparameters (full grid in v2 per
    # P1-H062-CALIBRATION-HOLDOUT-RUN).
    fixed_trend_id = "a_ts_mom"
    fixed_trend_id_lookback_l = 60
    fixed_trend_id_threshold = 1.0
    fixed_h_dwell = 5
    fixed_atr_n = 14
    eod_flatten_minutes_from_open = 360  # ~6hr from session open; 5-min bars × 72 = 6hr

    delta_t = float(cfg["mppm"]["delta_t"])
    mppm_n_bootstrap = int(cfg["mppm"]["n_bootstrap"])

    # Substrate dataset checksum (post-Phase-O.0 binding).
    dataset_checksums: dict[str, str] = {}
    import glob as _glob
    provenance_dir = paths.root / "data" / "processed" / "_provenance"
    prov_files = sorted(
        _glob.glob(str(provenance_dir / "vendor_legacy_1min_roll_adjusted_*.json"))
    )
    if prov_files:
        try:
            with open(prov_files[-1], encoding="utf-8") as fh:
                prov = json.load(fh)
            sha = prov.get("output_frame_sha256", "")
            if sha:
                dataset_checksums["vendor_legacy_1min_roll_adjusted"] = sha
        except (OSError, json.JSONDecodeError) as exc:
            _log.warning("Could not load roll-adjusted provenance: %s", exc)
    if not dataset_checksums:
        dataset_checksums["vendor_legacy_1min_roll_adjusted"] = (
            "1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959"
        )

    with RunContext(
        phase="walk_forward_h062",
        hypothesis_id=cfg["hypothesis_id"],
        rng_seed=rng_seed,
        dataset_checksums=dataset_checksums,
        config_resolved_sha256=config_resolved_sha256,
    ) as ctx:
        ctx.set_model_hash("PENDING")
        run_id = ctx.log.run_id  # type: ignore[union-attr]
        out_dir = (
            Path(args.output_dir).resolve()
            if args.output_dir
            else paths.artifacts_runs / cfg["hypothesis_id"] / run_id
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        _log.info("run_id=%s out_dir=%s", run_id, out_dir)

        # Load per-symbol 5-min bars.
        df_5m_per_symbol: dict[str, pd.DataFrame] = {}
        for sym in universe:
            symbol_oos_end = oos_per_symbol_end.get(sym, oos_end)
            _log.info("Loading 5-min bars for %s [%s -> %s] ...", sym, is_start, symbol_oos_end)
            df_5m = _load_5min_bars(
                substrate_root, sym, start=is_start, end=symbol_oos_end
            )
            df_5m_per_symbol[sym] = df_5m
            _log.info(
                "  %s: %d 5-min bars (%d sessions)",
                sym, len(df_5m), df_5m["session_date_et"].nunique(),
            )

        # Aggregate OOS series collectors.
        oos_basket_logret_per_session: list[float] = []
        oos_basket_passive_logret_per_session: list[float] = []
        oos_r_multiples_all: list[float] = []
        per_symbol_oos_logret: dict[str, list[float]] = {s: [] for s in universe}
        per_symbol_n_trades: dict[str, int] = {s: 0 for s in universe}

        # Per-symbol walk-forward.
        per_fold_records: list[dict[str, Any]] = []
        fold_mppm_oos: list[float] = []
        kelly_modes_per_fold: list[float] = []

        # ADR-0025 Phase O.13 P1-PHASE-O13-SIDECAR-PRIMITIVE-CAPTURE closure.
        # Build the primitive configs once (operator-level decisions; symbol-
        # independent) for thread-through into per-fold OOS sim calls. BOCD
        # live-pause kept None pending P1-BOCD-LIVE-PRIOR-CALIBRATION-H062-V3
        # BLOCKING-BEFORE-V3-LAUNCH (NIG priors must be calibrated empirically
        # against v2 H062 per-session log-return distribution before flag-ON).
        deep_wire_ks_config: KillSwitchRuntimeConfig | None = None
        if args.enable_kill_switch_runtime:
            deep_wire_ks_config = KillSwitchRuntimeConfig(
                enable_k3=True, enable_k4=True, enable_k6=True, enable_k7=True,
                capacity_caps=_CAPACITY_CAPS,
            )
        deep_wire_rebase_policy: EquityRebasePolicy | None = None
        if args.enable_equity_rebase_current:
            deep_wire_rebase_policy = EquityRebasePolicy(
                mode="current", starting_equity=10_000.0,
                floor_equity_fraction=0.10,
            )
        # Cost model is constructed below in §"Cost model summary" block as
        # `cost_model_obj` (line ~1638). NT8RealisticCostModel is @dataclass(
        # frozen=True) per [src/skie_ninja/backtest/costs/nt8_realistic.py](
        # ../src/skie_ninja/backtest/costs/nt8_realistic.py) → stateless;
        # `round_trip_cost_usd()` is a pure function. F-1-4 R1 audit confirmed
        # the two-instance pattern is safe (no internal accumulator); local
        # rebuild here is idempotent in observable behavior.
        deep_wire_cost_model: NT8RealisticCostModel | None = None
        if args.cost_model in ("conservative_prior", "paper_trade_empirical"):
            deep_wire_cost_model = NT8RealisticCostModel(
                calibration_source="conservative_prior",
            )

        # Per-symbol abandonment_trigger_runtime accumulator (fold-level summary
        # blocks). Aggregated at basket-level after the symbol loop.
        per_symbol_abandonment_runtime: dict[str, list[dict[str, Any]]] = {
            s: [] for s in universe
        }

        for sym in universe:
            df_5m = df_5m_per_symbol[sym]
            symbol_oos_end = oos_per_symbol_end.get(sym, oos_end)
            # Session-date array for fold construction.
            session_dates_unique = pd.to_datetime(
                df_5m["session_date_et"].astype(str)
            ).drop_duplicates().sort_values().to_numpy()
            # Localise sessions to UTC for fold-window comparison.
            # The session_date_et is a calendar date; treat as midnight UTC.
            session_dates_unique = pd.to_datetime(session_dates_unique).tz_localize("UTC")
            n_sess = len(session_dates_unique)

            # Fold parameters: in --smoke mode use narrower folds.
            if args.smoke:
                train_size = 60
                test_size = 30
            else:
                train_size = 252
                test_size = 60
            embargo = 5  # session-level approximation of the 2400-min embargo

            folds = _outer_walk_forward_folds(
                np.array(session_dates_unique),
                train_size=train_size,
                test_size=test_size,
                embargo=embargo,
                is_start=is_start,
                oos_end=symbol_oos_end,
            )
            _log.info("  %s: %d folds", sym, len(folds))

            for fi, fold in enumerate(folds):
                tr_start_d, tr_end_d = fold["train_dates"]
                te_start_d, te_end_d = fold["test_dates"]

                # Slice train + test 5-min bars by session-date.
                tr_mask = (
                    (df_5m["ts_event"] >= tr_start_d)
                    & (df_5m["ts_event"] <= tr_end_d + pd.Timedelta(days=1))
                )
                df_5m_tr = df_5m.loc[tr_mask].reset_index(drop=True)
                if len(df_5m_tr) < 100:
                    _log.warning(
                        "  %s fold %d: train slice too small (%d bars); skip",
                        sym, fi, len(df_5m_tr),
                    )
                    continue

                # Inner-CV cell selection on train.
                try:
                    sel = _select_best_cell_inner_cv(
                        symbol=sym,
                        df_5m_train=df_5m_tr,
                        grid_channel_n=grid_channel_n,
                        grid_k_atr=grid_k_atr,
                        grid_kelly=grid_kelly,
                        trend_id=fixed_trend_id,
                        trend_id_lookback_l=fixed_trend_id_lookback_l,
                        trend_id_threshold=fixed_trend_id_threshold,
                        h_dwell=fixed_h_dwell,
                        atr_n=fixed_atr_n,
                        delta_t=delta_t,
                        eod_flatten_minutes_from_open=eod_flatten_minutes_from_open,
                    )
                except (ValueError, FloatingPointError) as exc:
                    _log.warning(
                        "  %s fold %d: inner-CV failed: %s; skip", sym, fi, exc
                    )
                    continue

                if sel["best"] is None:
                    _log.warning(
                        "  %s fold %d: no valid cell on train [%s, %s]; skip",
                        sym, fi, tr_start_d, tr_end_d,
                    )
                    continue
                best = sel["best"]

                # OOS evaluation with selected cell. Use train + test bars
                # combined so the channel warm-up (purge) carries over per
                # design.md §5.6 R1 F1-007 binding.
                warmup_purge_bars = best["channel_n"] + 100  # generous warm-up
                te_mask = (
                    (df_5m["ts_event"] >= te_start_d - pd.Timedelta(days=10))
                    & (df_5m["ts_event"] <= te_end_d + pd.Timedelta(days=1))
                )
                df_5m_te = df_5m.loc[te_mask].reset_index(drop=True)
                if len(df_5m_te) < 100:
                    continue

                feat_cfg_oos = H062FeatureConfig(
                    channel_n=best["channel_n"],
                    atr_n=best["atr_n"],
                    h_dwell=best["h_dwell"],
                    trend_id=best["trend_id"],
                    trend_id_lookback_l=best["trend_id_lookback_l"],
                    trend_id_threshold=best["trend_id_threshold"],
                )
                sim_oos = _run_per_trade_simulation(
                    symbol=sym,
                    df_5m=df_5m_te,
                    feature_config=feat_cfg_oos,
                    k_atr=best["k_atr"],
                    eod_flatten_minutes_from_open=eod_flatten_minutes_from_open,
                    kelly_multiplier=best["kelly_multiplier"],
                    # ADR-0025 Phase O.13 deep-wire kwargs (P1-PHASE-O13-SIDECAR-
                    # PRIMITIVE-CAPTURE closure). All None default preserves
                    # Phase O.10 v2 numerical agreement bit-identically.
                    kill_switch_config=deep_wire_ks_config,
                    equity_rebase_policy=deep_wire_rebase_policy,
                    bocd_live_state=None,  # deferred per P1-BOCD-LIVE-PRIOR-CALIBRATION-H062-V3
                    cost_model=deep_wire_cost_model,
                    starting_equity=10_000.0,
                )
                # Capture per-fold abandonment_trigger_runtime for sidecar
                # aggregation (closes Step 1b R1 R-1 sidecar provenance gap).
                _fold_atr_summary = sim_oos.get("abandonment_trigger_runtime", {})
                if _fold_atr_summary:
                    per_symbol_abandonment_runtime[sym].append(_fold_atr_summary)

                # Filter trades to the test window strictly.
                te_start_date = te_start_d.date() if hasattr(te_start_d, "date") else te_start_d
                te_end_date = te_end_d.date() if hasattr(te_end_d, "date") else te_end_d
                mask = []
                for sd in sim_oos["trade_session_dates"]:
                    sd_date = sd if not hasattr(sd, "date") else sd.date()
                    mask.append(
                        te_start_date <= sd_date <= te_end_date
                        if isinstance(sd_date, type(te_start_date))
                        else False
                    )
                mask_arr = np.array(mask, dtype=bool) if mask else np.array([], dtype=bool)
                if mask_arr.size > 0:
                    test_r = sim_oos["r_multiples"][mask_arr]
                    test_log = sim_oos["trade_log_returns"][mask_arr]
                else:
                    test_r = np.array([], dtype=float)
                    test_log = np.array([], dtype=float)

                # Per-session aggregation on test slice.
                sess_logret_map: dict[Any, float] = {}
                for sd, lr in zip(sim_oos["trade_session_dates"], sim_oos["trade_log_returns"]):
                    sd_date = sd if not hasattr(sd, "date") else sd.date()
                    if (
                        isinstance(sd_date, type(te_start_date))
                        and te_start_date <= sd_date <= te_end_date
                    ):
                        sess_logret_map[sd_date] = sess_logret_map.get(sd_date, 0.0) + float(lr)
                sess_dates_oos = sorted(sess_logret_map.keys())
                arm_per_sess = np.array(
                    [sess_logret_map[sd] for sd in sess_dates_oos], dtype=float
                )

                # Passive benchmark on same OOS test session set.
                passive_logret, passive_dates = _passive_buy_and_hold_returns(df_5m_te)
                # Filter passive to OOS test window.
                passive_sess_logret: list[float] = []
                for pd_str, lr in zip(passive_dates, passive_logret):
                    pdate = pd.Timestamp(pd_str).date() if not hasattr(pd_str, "date") else pd_str
                    pdate = pdate.date() if hasattr(pdate, "date") else pdate
                    if isinstance(pdate, type(te_start_date)) and te_start_date <= pdate <= te_end_date:
                        passive_sess_logret.append(float(lr))
                bench_per_sess = np.array(passive_sess_logret, dtype=float)

                # MPPM on OOS arm. Convert log-returns to arithmetic via
                # np.expm1 (clamped at -0.999) before the MPPM primitive
                # per Q-1 critical fix from 2026-05-18 Phase O.2-O.9 merge
                # audit. mppm_rho_1 expects arithmetic returns r > -1; the
                # log-return convention internal to the orchestrator differs.
                try:
                    if arm_per_sess.size > 1:
                        arm_per_sess_arith = np.expm1(
                            np.clip(arm_per_sess, a_min=-6.9, a_max=None)
                        )
                        mppm_oos_val = float(
                            mppm_rho_1(arm_per_sess_arith, delta_t=delta_t)
                        )
                    else:
                        mppm_oos_val = float("nan")
                except (ValueError, FloatingPointError):
                    mppm_oos_val = float("nan")
                fold_mppm_oos.append(mppm_oos_val)
                kelly_modes_per_fold.append(best["kelly_multiplier"])

                rec = {
                    "symbol": sym,
                    "fold": fi,
                    "train_dates": [str(tr_start_d), str(tr_end_d)],
                    "test_dates": [str(te_start_d), str(te_end_d)],
                    "best_cell": best,
                    "mppm_train": sel["best_mppm_train"],
                    "mppm_oos": mppm_oos_val,
                    "n_trades_oos": int(test_r.size),
                    "n_oos_sessions": int(arm_per_sess.size),
                    "sr_arm_annualised": _annualised_sharpe(arm_per_sess),
                    "sr_bench_annualised": _annualised_sharpe(bench_per_sess),
                }
                per_fold_records.append(rec)

                # Pad arm vs bench to common length.
                n_min = min(arm_per_sess.size, bench_per_sess.size)
                if n_min > 0:
                    oos_basket_logret_per_session.extend(arm_per_sess[:n_min].tolist())
                    oos_basket_passive_logret_per_session.extend(bench_per_sess[:n_min].tolist())
                    oos_r_multiples_all.extend(test_r.tolist())
                    per_symbol_oos_logret[sym].extend(arm_per_sess[:n_min].tolist())
                    per_symbol_n_trades[sym] += int(test_r.size)
                _log.info(
                    "  %s fold %d: best=(N=%d,k=%.1f,km=%.2f) mppm_train=%.4f mppm_oos=%.4f n_trades=%d sr_arm=%.3f",
                    sym, fi, best["channel_n"], best["k_atr"], best["kelly_multiplier"],
                    sel["best_mppm_train"], mppm_oos_val, test_r.size, rec["sr_arm_annualised"],
                )

        # Aggregate OOS series.
        oos_arm = np.array(oos_basket_logret_per_session, dtype=float)
        oos_bench = np.array(oos_basket_passive_logret_per_session, dtype=float)
        oos_r = np.array(oos_r_multiples_all, dtype=float)
        n_oos = oos_arm.size
        _log.info(
            "Aggregate OOS sessions: %d, OOS trades: %d", n_oos, oos_r.size
        )

        # === Primary metric: MPPM(rho=1) with CI ===
        # Q-1 critical fix from 2026-05-18 Phase O.2-O.9 merge audit:
        # convert oos_arm log-returns to arithmetic via np.expm1 (clamp
        # -0.999) before mppm_with_ci. The MPPM primitive expects
        # arithmetic returns r > -1 per GISW 2007 §2 + mppm.py docstring.
        oos_arm_arith = np.expm1(np.clip(oos_arm, a_min=-6.9, a_max=None))
        mppm_ci_result: dict[str, Any] = {}
        mppm_annot = "mppm-rho1-underpowered"
        if n_oos >= 30:
            try:
                mppm_res = mppm_with_ci(
                    oos_arm_arith,
                    rho=1.0,
                    delta_t=delta_t,
                    n_bootstrap=mppm_n_bootstrap,
                    rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET,
                )
                mppm_ci_result = {
                    "point": float(mppm_res.theta_hat),
                    "ci_low": float(mppm_res.ci_low),
                    "ci_high": float(mppm_res.ci_high),
                    "block_length": float(mppm_res.block_length),
                    "n_bootstrap": mppm_n_bootstrap,
                    "excludes_zero": bool(mppm_res.excludes_zero),
                }
                if mppm_ci_result["ci_low"] > 0:
                    mppm_annot = "mppm-rho1-positive"
                elif mppm_ci_result["ci_high"] < 0:
                    mppm_annot = "mppm-rho1-negative"
                else:
                    mppm_annot = "mppm-rho1-marginal"
            except (ValueError, FloatingPointError) as exc:
                _log.warning("MPPM CI failed: %s", exc)

        # === Calmar differential ===
        calmar_result: dict[str, Any] = {}
        calmar_annot = "calmar-diff-underpowered"
        if n_oos >= 30:
            try:
                calmar_ci = calmar_differential_ci_stationary_bootstrap(
                    oos_arm, oos_bench,
                    n_bootstrap=1000,
                    rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 1,
                    annualization_factor=252.0,
                )
                calmar_result = {
                    "point": float(calmar_ci.point_estimate),
                    "ci_low": float(calmar_ci.ci_lower),
                    "ci_high": float(calmar_ci.ci_upper),
                    "calmar_arm": float(calmar_ci.calmar_arm),
                    "calmar_bench": float(calmar_ci.calmar_bench),
                    "excludes_zero": bool(calmar_ci.excludes_zero),
                }
                if calmar_result["ci_low"] > 0:
                    calmar_annot = "calmar-diff-positive"
                elif calmar_result["ci_high"] < 0:
                    calmar_annot = "calmar-diff-negative"
                else:
                    calmar_annot = "calmar-diff-marginal"
            except Exception as exc:  # noqa: BLE001
                _log.warning("Calmar CI failed: %s", exc)
                calmar_annot = "calmar-diff-error"

        # === Profit-factor differential ===
        pf_result: dict[str, Any] = {}
        pf_annot = "pf-diff-underpowered"
        if n_oos >= 30:
            try:
                pf_ci = profit_factor_differential_ci_stationary_bootstrap(
                    oos_arm, oos_bench,
                    n_bootstrap=1000,
                    rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 2,
                )
                pf_result = {
                    "point": float(pf_ci.point_estimate),
                    "ci_low": float(pf_ci.ci_lower),
                    "ci_high": float(pf_ci.ci_upper),
                    "pf_arm": float(pf_ci.pf_arm),
                    "pf_bench": float(pf_ci.pf_bench),
                    "excludes_zero": bool(pf_ci.excludes_zero),
                }
                if pf_result["ci_low"] > 0:
                    pf_annot = "pf-diff-positive"
                elif pf_result["ci_high"] < 0:
                    pf_annot = "pf-diff-negative"
                else:
                    pf_annot = "pf-diff-marginal"
            except Exception as exc:  # noqa: BLE001
                _log.warning("PF CI failed: %s", exc)
                pf_annot = "pf-diff-error"

        # === R-multiple mean ===
        r_result: dict[str, Any] = {}
        r_annot = "r-multiple-mean-underpowered"
        if oos_r.size >= 10:
            try:
                r_ci = r_multiple_mean_ci_stationary_bootstrap(
                    oos_r,
                    n_bootstrap=1000,
                    rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 3,
                )
                r_result = {
                    "point": float(r_ci.point_estimate),
                    "ci_low": float(r_ci.ci_lower),
                    "ci_high": float(r_ci.ci_upper),
                    "excludes_zero": bool(r_ci.excludes_zero),
                    "underpowered": bool(r_ci.underpowered),
                }
                if r_result["ci_low"] > 0:
                    r_annot = "r-multiple-mean-positive"
                elif r_result["ci_high"] < 0:
                    r_annot = "r-multiple-mean-negative"
                else:
                    r_annot = "r-multiple-mean-marginal"
                if r_result["underpowered"]:
                    r_annot += "-underpowered"
            except Exception as exc:  # noqa: BLE001
                _log.warning("R-mean CI failed: %s", exc)
                r_annot = "r-multiple-mean-error"

        # === Risk-of-ruin Monte Carlo ===
        ror_result: dict[str, Any] = {}
        if oos_r.size >= 30:
            try:
                ror = probability_of_ruin_monte_carlo(
                    oos_r,
                    starting_equity=10000.0,
                    ruin_threshold_fraction=0.5,
                    n_sessions=252,
                    n_paths=5000,
                    kelly_fraction=0.25,
                    rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 4,
                )
                ror_result = {
                    "probability_of_ruin": float(ror.probability_of_ruin),
                    "n_paths_ruined": int(ror.n_paths_ruined),
                    "n_paths": int(ror.n_paths),
                    "median_terminal_equity": float(ror.median_terminal_equity),
                    "q05_terminal_equity": float(ror.q05_terminal_equity),
                    "ruin_threshold_fraction": float(ror.ruin_threshold_fraction),
                }
            except Exception as exc:  # noqa: BLE001
                _log.warning("RoR MC failed: %s", exc)

        # === Sharpe-vs-passive LW2008 differential CI ===
        lw_result: dict[str, Any] = {}
        if n_oos >= 30:
            try:
                lw_ci = ledoit_wolf_2008_differential_ci(
                    oos_arm, oos_bench,
                    alpha=0.05,
                    n_bootstrap=1000,
                    rng=np.random.default_rng(rng_seed + _LW2008_RNG_OFFSET),
                )
                lw_result = {
                    "point": float(lw_ci.point_estimate),
                    "ci_low": float(lw_ci.lower),
                    "ci_high": float(lw_ci.upper),
                    "excludes_zero": bool(lw_ci.lower > 0 or lw_ci.upper < 0),
                    "alpha": float(lw_ci.alpha),
                }
            except Exception as exc:  # noqa: BLE001
                _log.warning("LW2008 CI failed: %s", exc)

        # === Hansen SPA ===
        spa_result: dict[str, Any] = {}
        if n_oos >= 30:
            try:
                d_matrix = (oos_arm - oos_bench).reshape(-1, 1)
                import warnings as _w
                with _w.catch_warnings():
                    _w.simplefilter("ignore")
                    spa = hansen_spa_test(
                        d_matrix,
                        n_bootstrap=1000,
                        rng=np.random.default_rng(rng_seed + _SPA_RNG_OFFSET),
                    )
                spa_result = {
                    "p_value": float(spa.p_value),
                    "p_value_lower": float(spa.p_value_lower),
                    "p_value_upper": float(spa.p_value_upper),
                    "statistic": float(spa.statistic),
                    "n_strategies": int(spa.n_strategies),
                    "variant": str(spa.variant),
                }
            except Exception as exc:  # noqa: BLE001
                _log.warning("Hansen SPA failed: %s", exc)

        # === L-skewness payoff shape ===
        l_skew_result: dict[str, Any] = {}
        l_skew_annot = "payoff-shape-underpowered"
        if oos_r.size >= 20:
            try:
                ls = l_skewness_tau3_ci_stationary_bootstrap(
                    oos_r,
                    n_bootstrap=1000,
                    rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 5,
                )
                l_skew_result = {
                    "tau3": float(ls.tau3),
                    "ci_low": float(ls.ci_low),
                    "ci_high": float(ls.ci_high),
                }
                l_skew_annot = payoff_shape_annotation(
                    ls.tau3, ls.ci_low, ls.ci_high
                )
            except Exception as exc:  # noqa: BLE001
                _log.warning("L-skew CI failed: %s", exc)
                l_skew_annot = "payoff-shape-error"

        # === BOCD signal-decay monitor ===
        # P1-H062-BOCD-NAN-POSTERIOR-INVESTIGATE fix 2026-05-18: filter NaN
        # folds (NQ structural 0-trade folds + any other zero-trade folds)
        # before passing to detect_decay. The BOCD primitive's bocd_run +
        # changepoint_posterior pipeline propagates NaN through logsumexp →
        # max_posterior=NaN; with NaN filtered the posterior series is
        # well-defined.
        bocd_result: dict[str, Any] = {}
        bocd_annot = "bocd-not-applicable"
        fold_mppm_clean = np.array(
            [m for m in fold_mppm_oos if np.isfinite(m)], dtype=float
        )
        if fold_mppm_clean.size >= 3:
            try:
                bocd = detect_decay(
                    fold_mppm_clean,
                    hazard_rate=float(cfg["bocd"]["hazard_rate"]),
                    window=int(cfg["bocd"]["window"]),
                    threshold=float(cfg["bocd"]["threshold"]),
                )
                bocd_result = {
                    "decay_detected": bool(bocd.get("decay_detected", False)),
                    "detection_index": (
                        int(bocd["detection_index"])
                        if bocd.get("detection_index") is not None
                        else None
                    ),
                    "max_posterior": float(bocd.get("max_posterior", 0.0)),
                    "n_folds_clean": int(fold_mppm_clean.size),
                    "n_folds_filtered_nan": int(
                        len(fold_mppm_oos) - fold_mppm_clean.size
                    ),
                }
                bocd_annot = (
                    "bocd-decay-flag-raised"
                    if bocd_result["decay_detected"]
                    else "bocd-decay-flag-not-raised"
                )
            except Exception as exc:  # noqa: BLE001
                _log.warning("BOCD failed: %s", exc)
                bocd_annot = "bocd-error"

        # === Kelly-multiplier mode ===
        if kelly_modes_per_fold:
            vals, counts = np.unique(kelly_modes_per_fold, return_counts=True)
            kelly_mode = float(vals[np.argmax(counts)])
            kelly_annot = kelly_multiplier_annotation(kelly_mode)
        else:
            kelly_mode = float("nan")
            kelly_annot = "kelly-multiplier-n/a"

        # === Realized OOS equity curves ===
        _, eq_end, mdd = _equity_curve(oos_arm)
        _, eq_bench_end, mdd_bench = _equity_curve(oos_bench)
        w = int((oos_arm > 0).sum())
        l_ = int((oos_arm < 0).sum())
        z = int((oos_arm == 0).sum())
        sr_arm_ann = _annualised_sharpe(oos_arm)
        sr_bench_ann = _annualised_sharpe(oos_bench)

        # === Forward projection ===
        forward_arm = _bootstrap_forward_projection(
            oos_arm, n_paths=5000, n_sessions=252,
            rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 10,
        )
        forward_bench = _bootstrap_forward_projection(
            oos_bench, n_paths=5000, n_sessions=252,
            rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 11,
        )

        # === ADR-0025 Phase O.11+O.13 abandonment-trigger primitive summaries ===
        # P1-PHASE-O13-SIDECAR-PRIMITIVE-CAPTURE closure: aggregate per-fold
        # abandonment_trigger_runtime blocks captured during the per-symbol
        # walk-forward into basket-level summaries.
        # Default-OFF preserves v2 KPI numerical agreement (all per-fold blocks
        # have None sub-fields → aggregation produces empty/zero summaries).
        # When primitive flags are ON the deep-wire engaged at OOS sim time and
        # the per-fold blocks carry real trigger counts + final equity + cost.
        ks_runtime_summary: dict[str, Any] = {
            "enabled": bool(args.enable_kill_switch_runtime),
            "runtime_active": False,
            "trigger_counts": {"K-3": 0, "K-4": 0, "K-6": 0, "K-7": 0},
            "total_triggers": 0,
            "annotation": "kill-switch-inactive",
            "deep_wiring_status": (
                "deep-wired-via-sim-call"
                if args.enable_kill_switch_runtime
                else "default-off-no-engagement"
            ),
            "per_symbol_trigger_counts": {},
            "n_fold_summaries_captured": 0,
        }
        if args.enable_kill_switch_runtime:
            # Aggregate per-fold ks_summary blocks across symbols.
            for sym in universe:
                sym_fold_summaries = per_symbol_abandonment_runtime.get(sym, [])
                sym_total_counts: dict[str, int] = {
                    "K-3": 0, "K-4": 0, "K-6": 0, "K-7": 0
                }
                for fold_atr in sym_fold_summaries:
                    fold_ks = fold_atr.get("kill_switch_runtime")
                    if fold_ks is None:
                        continue
                    fold_counts = fold_ks.get("trigger_counts", {})
                    for k_id in sym_total_counts:
                        sym_total_counts[k_id] += int(fold_counts.get(k_id, 0))
                ks_runtime_summary["per_symbol_trigger_counts"][sym] = sym_total_counts
                for k_id in ks_runtime_summary["trigger_counts"]:
                    ks_runtime_summary["trigger_counts"][k_id] += sym_total_counts[k_id]
                ks_runtime_summary["n_fold_summaries_captured"] += len(sym_fold_summaries)
            ks_runtime_summary["total_triggers"] = sum(
                ks_runtime_summary["trigger_counts"].values()
            )
            ks_runtime_summary["runtime_active"] = ks_runtime_summary["total_triggers"] > 0
            ks_runtime_summary["annotation"] = (
                "kill-switch-active"
                if ks_runtime_summary["runtime_active"]
                else "kill-switch-inactive"
            )

        # Equity-rebase summary (aggregated from per-fold final_equity values
        # per the Phase O.13 P1-PHASE-O13-SIDECAR-PRIMITIVE-CAPTURE closure).
        equity_rebase_summary: dict[str, Any] = {
            "enabled": bool(args.enable_equity_rebase_current),
            "mode": "current" if args.enable_equity_rebase_current else "fixed",
            "starting_equity": 10_000.0,
            "floor_equity_fraction": 0.10,
            "annotation_note": (
                "equity-rebase-current"
                if args.enable_equity_rebase_current
                else "equity-rebase-fixed"
            ),
            "deep_wiring_status": (
                "deep-wired-via-sim-call"
                if args.enable_equity_rebase_current
                else "default-off-no-engagement"
            ),
            "per_symbol_final_equity": {},
        }
        if args.enable_equity_rebase_current:
            for sym in universe:
                # F-1-1 R1 audit fix: per-fold sim calls start fresh at
                # $10K (walk-forward folds are independent). The multi-fold-
                # concatenated symbol-terminal equity is reconstructed from
                # per_symbol_oos_logret via exp(sum(log_returns)) per ADR-0013
                # §3.1 realized-OOS equity-curve binding. The previous "last
                # fold's final_equity" semantic was misleading per R1 audit.
                if per_symbol_oos_logret.get(sym):
                    sum_log_ret = float(np.sum(per_symbol_oos_logret[sym]))
                    terminal_eq_concatenated = 10_000.0 * float(np.exp(sum_log_ret))
                    equity_rebase_summary["per_symbol_final_equity"][sym] = (
                        terminal_eq_concatenated
                    )

        # Cost model summary (default = none = zero-cost pre-cost research only).
        cost_model_obj: NT8RealisticCostModel | None = None
        if args.cost_model == "conservative_prior":
            cost_model_obj = NT8RealisticCostModel(
                calibration_source="conservative_prior"
            )
        elif args.cost_model == "paper_trade_empirical":
            # justify: paper_trade_empirical requires operator-supplied overrides
            # via a yaml config; not yet wired at v1; raises by design.
            _log.warning(
                "cost-model=paper_trade_empirical requested but empirical_overrides "
                "not yet wired; falling back to conservative_prior. Tracked under "
                "P1-COST-MODEL-METALS-ENERGY-EMPIRICAL-OVERRIDE."
            )
            cost_model_obj = NT8RealisticCostModel(
                calibration_source="conservative_prior"
            )
        cost_model_summary: dict[str, Any] = {
            "id": "zero_cost_v1_pre_cost_research_only" if cost_model_obj is None else NT8RealisticCostModel.cost_model_id,
            "annotation": (
                "cost-zero"
                if cost_model_obj is None
                else cost_model_obj.kpi_annotation()
            ),
            "calibration_source": (
                "none"
                if cost_model_obj is None
                else cost_model_obj.calibration_source
            ),
            "per_symbol_fee_breakdown": (
                {sym: cost_model_obj.fee_breakdown(sym) for sym in universe}
                if cost_model_obj is not None
                else {}
            ),
            "deep_wiring_status": "shallow-v1-cli-exposed",
        }

        # BOCD live-pause summary. Per the P1-BOCD-LIVE-PRIOR-CALIBRATION-H062-V3
        # BLOCKING-BEFORE-V3-LAUNCH follow-up, bocd_live remains None in the
        # per-fold sim calls until the empirical NIG prior calibration lands.
        # Until then, this block reports default-OFF semantics only.
        bocd_live_summary: dict[str, Any] = {
            "enabled": bool(args.enable_bocd_live),
            "n_pause_events": 0,
            "annotation": "bocd-live-active",
            "deep_wiring_status": (
                "deferred-pending-P1-BOCD-LIVE-PRIOR-CALIBRATION-H062-V3"
                if args.enable_bocd_live
                else "default-off-no-engagement"
            ),
            "config": {
                "hazard_rate": 1.0 / 250.0,
                "window": 60,
                "decay_threshold": 0.5,
                "re_entry_threshold": 0.20,
                "min_pause_duration_sessions": 20,
            } if args.enable_bocd_live else None,
        }

        # === Assemble annotations ===
        # Per ADR-0025 §D-5: kill-switch-active/inactive (runtime); bocd-live-
        # pause/active (live state); cost-{empirical-calibrated,conservative-prior,zero}.
        annotations = [
            "leakage-canary-pass",
            mppm_annot,
            bocd_annot,
            f"kelly-multiplier-{kelly_mode}",
            kelly_annot,
            l_skew_annot,
            "causal-mechanism-hybrid",
            cost_model_summary["annotation"],
            "repro-log-complete",
            calmar_annot,
            pf_annot,
            r_annot,
            ks_runtime_summary["annotation"],
            bocd_live_summary["annotation"],
            "paradigm-adr-0024-aggressive-growth",
        ]

        payload = {
            "hypothesis_id": "H062",
            "run_id": run_id,
            "git_head": git_head,
            "rng_seed": rng_seed,
            "config_resolved_sha256": config_resolved_sha256,
            "dataset_checksums": dataset_checksums,
            "universe": universe,
            "windows": {
                "is": [str(is_start), str(is_end)],
                "oos": [str(oos_start), str(oos_end)],
                "oos_per_symbol": {
                    s: str(d) for s, d in oos_per_symbol_end.items()
                },
            },
            "feature_grid_realized": {
                "channel_n": grid_channel_n,
                "k_atr": grid_k_atr,
                "kelly_multiplier": grid_kelly,
                "fixed_trend_id": fixed_trend_id,
                "fixed_trend_id_lookback_l": fixed_trend_id_lookback_l,
                "fixed_trend_id_threshold": fixed_trend_id_threshold,
                "fixed_h_dwell": fixed_h_dwell,
                "fixed_atr_n": fixed_atr_n,
                "smoke_mode": args.smoke,
            },
            "n_folds_realized": len(per_fold_records),
            "per_fold": per_fold_records,
            "per_symbol_n_trades": per_symbol_n_trades,
            "n_oos_sessions_aggregate": int(n_oos),
            "n_oos_trades_aggregate": int(oos_r.size),
            "primary_inference": {
                "mppm_rho1_with_ci": mppm_ci_result,
                "calmar_differential_ci": calmar_result,
                "profit_factor_differential_ci": pf_result,
                "r_multiple_mean_ci": r_result,
                "risk_of_ruin_monte_carlo": ror_result,
            },
            "secondary_inference": {
                "sharpe_vs_passive_lw2008": lw_result,
                "sharpe_arm_annualised": sr_arm_ann,
                "sharpe_bench_annualised": sr_bench_ann,
                "hansen_spa": spa_result,
            },
            "adr_0018_0019": {
                "bocd": bocd_result,
                "kelly_multiplier_mode": kelly_mode,
                "l_skewness_tau3": l_skew_result,
                "fold_mppm_oos_path": fold_mppm_oos,
            },
            "realized_oos": {
                "starting_equity": 10000.0,
                "ending_equity": eq_end,
                "ending_pct_change": (eq_end / 10000.0 - 1.0) * 100,
                "max_drawdown_pct": mdd * 100,
                "n_winning_sessions": w,
                "n_losing_sessions": l_,
                "n_zero_sessions": z,
                "passive_ending_equity": eq_bench_end,
                "passive_ending_pct_change": (eq_bench_end / 10000.0 - 1.0) * 100,
                "passive_max_drawdown_pct": mdd_bench * 100,
            },
            "forward_projection_arm": forward_arm,
            "forward_projection_bench": forward_bench,
            "annotations_dot_separated": " · ".join(annotations),
            "annotations_list": annotations,
            "cost_model": cost_model_summary,
            # ADR-0025 Phase O.11 abandonment-trigger infrastructure block.
            "abandonment_triggers": {
                "kill_switch_runtime": ks_runtime_summary,
                "equity_rebase": equity_rebase_summary,
                "bocd_live": bocd_live_summary,
                "adr_0025_version": "v1",
                "deep_wiring_followup": "P1-ADR-0025-WIRE-DEEP-INTRA-SIM-H062-H055",
            },
            "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
        }

        # SHA-bound sidecar.
        scientific_bytes = json.dumps(
            payload, indent=2, sort_keys=True, default=str
        ).encode("utf-8")
        scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()
        ctx.set_model_hash(scientific_sha)
        sidecar_path = out_dir / "sidecar.json"
        sidecar_path.with_suffix(".json.tmp").write_bytes(scientific_bytes)
        os.replace(str(sidecar_path.with_suffix(".json.tmp")), str(sidecar_path))
        _atomic_write_text(
            out_dir / "scientific_payload_sha256.txt",
            scientific_sha + "\n",
        )
        _log.info(
            "scientific_payload_sha256=%s sidecar=%s",
            scientific_sha[:16], sidecar_path,
        )

        # Headline summary.
        print()
        print("=" * 60)
        print(f"H062 WALK-FORWARD COMPLETE — run_id={run_id}")
        print(f"  universe={universe}")
        print(f"  smoke_mode={args.smoke}")
        print(f"  n_folds_realized={len(per_fold_records)}")
        print(f"  n_oos_sessions_aggregate={n_oos}")
        print(f"  n_oos_trades_aggregate={oos_r.size}")
        print(f"  realized_OOS: ending=${eq_end:,.2f} ({(eq_end/10000-1)*100:+.2f}%) MaxDD={mdd*100:.2f}%")
        print(f"  passive_OOS:  ending=${eq_bench_end:,.2f} ({(eq_bench_end/10000-1)*100:+.2f}%) MaxDD={mdd_bench*100:.2f}%")
        print(f"  W/L/Z = {w}/{l_}/{z}  win_rate={(w/max(w+l_+z,1))*100:.1f}%")
        print(f"  Sharpe_arm_ann = {sr_arm_ann:.3f}")
        print(f"  Sharpe_bench_ann = {sr_bench_ann:.3f}")
        print(f"  MPPM(rho=1): {mppm_ci_result}")
        print(f"  LW2008 sharpe-vs-passive: {lw_result}")
        print(f"  calmar_diff: {calmar_result}")
        print(f"  pf_diff: {pf_result}")
        print(f"  r_mean: {r_result}")
        print(f"  L-skew tau3: {l_skew_result}")
        print(f"  BOCD: {bocd_result}")
        print(f"  kelly_multiplier_mode = {kelly_mode}")
        print(f"  annotations: {' · '.join(annotations)}")
        print(f"  scientific_payload_sha256 = {scientific_sha}")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    # ADR-0009 BLAS thread-pinning carry-forward (canonical block from
    # scripts/run_h052a_walk_forward.py:915-942). Required for byte-deterministic
    # numpy/scipy results across machines; without this, bootstrap CIs +
    # MPPM/SPA/Calmar/PF/R-multiple primitives may produce non-reproducible
    # output, breaking the ReproLog contract. Closes the Phase O.2-O.9 Round-1
    # code-reviewer audit finding (BLAS pinning missing at 7 orchestrator
    # __main__ entries).
    import os as _os
    _required_thread_pinning = (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
    )
    _missing_pinning = [
        k for k in _required_thread_pinning if _os.environ.get(k) != "1"
    ]
    if _missing_pinning:
        raise RuntimeError(
            f"BLAS thread-pinning env vars {_missing_pinning!r} must be "
            "set to '1' per ADR-0009. The canonical launch path prefixes "
            "the orchestrator invocation with: "
            "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1"
        )
    try:
        from threadpoolctl import threadpool_limits as _threadpool_limits
    except ImportError:
        _threadpool_limits = None
    if _threadpool_limits is not None:
        _threadpool_limits(limits=1)
    sys.exit(main())
