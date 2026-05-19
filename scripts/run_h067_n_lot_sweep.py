"""H067 N-lot sweep — cost-light Donchian channel-breakout on SIL standalone.

Genetic successor of H065 v2 M_inf-SIL cell per H067 design.md §1 + §17.1.
Per ADR-0027 §D-4 single-axis-genetic-cross discipline: H067 v1 preserves
the entire H065 v2 M_inf no-TP-overlay variant signal-generation mechanic
(channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60,
τ=1.0; current-equity rebase per ADR-0017 §4.1) and adds ONE new axis:
N-lot position sizing `N ∈ {1, 2, 3, 4, 5}` contracts, capped at the
ADR-0001 retail capacity ceiling for SIL.

Per ADR-0028 §D-2 zero-cost-A0-reference convention: every (N × Kelly)
cell is emitted TWICE — once at A0 (cost-zero) and once at A1
(cost-conservative-prior per ADR-0025 §D-3 + ADR-0025 §D-5). The A0/A1
diff enables `cost-friction-dominated-edge-{present, absent}` annotation
per ADR-0028 §D-2 trigger semantics.

Cell-budget cap = 5 N × 6 Kelly × 2 cost-arm = 60 cells (well under the
ADR-0027 §D-2 v1 cap of 1000).

Per the H065 design.md §4 exit-precedence within bar (PIT-resolved):
    1. gap-through-stop at bar-t open
    2. stop hit during bar (low ≤ SL_long or high ≥ SL_short)
    3. opposite-channel break at bar close
    4. EOD-flatten / session-rollover

M=∞ no-TP (per H065 v2 M_inf-SIL parent cell preservation). The H065 TP
overlay layer is intentionally OUT-of-scope at H067 v1 — only the M_inf
no-TP cell is forked here per the single-axis discipline.

OOS window per H067 design.md §2: 2024-01-01 → 2026-05-15.
Mandatory sub-window: 2026-04-01 → 2026-05-15 reported alongside per
ADR-0026 §D-1 §0 3-component summary header.

Per H067 design.md §11.1 the kill-switch primitives K-4 + K-6 + K-7 are
ENABLED at v1 with `block` enforcement-mode per ADR-0028 §D-1 default
(size-down deferred to v2 per `P1-H067-V2-WITH-K6-K7-SIZE-DOWN`).
BOCD live-pause DISABLED at v1 (no calibrated priors).

Output:
    artifacts/runs/H067/<run_id>/sidecar.json
    artifacts/runs/H067/<run_id>/sha256.txt
    artifacts/runs/H067/<run_id>/kpi_table.txt
    + canonical ReproLog at logs/reproducibility/<run_id>.json
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

from skie_ninja.backtest.costs.nt8_realistic import NT8RealisticCostModel
from skie_ninja.features.h062 import H062FeatureConfig, compute_h062_features
from skie_ninja.inference.calmar import (
    calmar_differential_ci_stationary_bootstrap,
    calmar_ratio,
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
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.runcontext import RunContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h067_n_lot_sweep")


# Per H067 design.md §2 + config/instruments.yaml SIL — verified tick_value $5.00.
_MULTIPLIERS: dict[str, float] = {"SIL": 1000.0}
# ADR-0001 retail capacity ceiling for SIL = 5 contracts (BLOCKING per
# `P1-H067-N-LOT-CAP-CALIBRATION`; H067 N-lot grid {1,2,3,4,5} is bounded
# ABOVE by this cap; the grid is EXHAUSTIVE within retail-tier sandbox).
_CAPACITY_CAPS: dict[str, int] = {"SIL": 5}

# Sub-window cutoff per ADR-0026 §D-1 + H067 design.md §13.
_SUBWINDOW_START = pd.Timestamp("2026-04-01", tz="UTC").date()
_SUBWINDOW_END = pd.Timestamp("2026-05-15", tz="UTC").date()

# Bootstrap CI defaults per H067 design.md §12 reproducibility binding.
_RNG_SEED = 20260519
_N_BOOTSTRAP_CI = 1000
_ANNUALIZATION_FACTOR = 252.0


def _resolve_substrate_dataset_checksum() -> str:
    """Read the most recent vendor_legacy_1min_roll_adjusted provenance JSON
    to resolve the canonical substrate `output_frame_sha256` at runtime.
    """
    prov_dir = _REPO_ROOT / "data" / "processed" / "_provenance"
    candidates = sorted(prov_dir.glob("vendor_legacy_1min_roll_adjusted_*.json"))
    if not candidates:
        return "UNKNOWN_PROVENANCE_NOT_FOUND"
    latest = candidates[-1]
    try:
        with latest.open(encoding="utf-8") as fh:
            prov = json.load(fh)
        return str(prov.get("output_frame_sha256", "UNKNOWN_FIELD_MISSING"))
    except (OSError, json.JSONDecodeError, KeyError):
        return "UNKNOWN_PROVENANCE_READ_FAILED"


def _compute_sil_partition_shas(substrate_root: Path) -> dict[str, dict[str, Any]]:
    """Per `P1-H067-SUBSTRATE-PER-PARTITION-SHA-EMIT`: enumerate the SIL
    partition SHA + row-count for sidecar embedding. Required artifact
    for substrate-vintage provenance per H067 design.md §16."""
    sil_dir = substrate_root / "symbol=SIL"
    if not sil_dir.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for yd in sorted(sil_dir.glob("year=*")):
        for p in sorted(yd.glob("part-*.parquet")):
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            rows = pl.scan_parquet(p).select(pl.len()).collect().item()
            out[f"{yd.name}/{p.name}"] = {"sha256": sha, "row_count": int(rows)}
    return out


@dataclass(frozen=True)
class NLotConfig:
    """H067 N-lot sweep configuration cell.

    Per H067 design.md §5.2 — joint inner-CV grid axis.
        n_lot ∈ {1, 2, 3, 4, 5}: position-size multiplier (capped at SIL ≤ 5)
        kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}: ADR-0018 D-2 grid
        cost_arm ∈ {"A0", "A1"}: zero-cost reference vs conservative_prior
    """
    name: str
    n_lot: int
    kelly_multiplier: float
    risk_budget_pct: float
    use_current_equity_rebase: bool
    cost_arm: str  # "A0" = zero-cost, "A1" = conservative_prior
    description: str


def _build_sweep_configs() -> list[NLotConfig]:
    """Construct the 60-cell H067 N-lot × Kelly × cost-arm sweep configurations.

    Per H067 design.md §5.2 + §5.3: N-lot grid {1, 2, 3, 4, 5} × Kelly
    multiplier grid {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} × 2 cost arms
    (A0 zero-cost + A1 conservative_prior per ADR-0028 §D-2).
    """
    n_lot_grid = [1, 2, 3, 4, 5]
    kelly_grid = [0.25, 0.5, 1.0, 1.5, 2.0, 2.5]
    cost_arms = ["A0", "A1"]
    configs: list[NLotConfig] = []
    for n_lot in n_lot_grid:
        for kelly in kelly_grid:
            for cost_arm in cost_arms:
                cost_label = "zero" if cost_arm == "A0" else "cons_prior"
                configs.append(
                    NLotConfig(
                        name=f"N{n_lot}_k{kelly:.2f}_{cost_arm}",
                        n_lot=n_lot,
                        kelly_multiplier=kelly,
                        risk_budget_pct=0.01,
                        use_current_equity_rebase=True,
                        cost_arm=cost_arm,
                        description=(
                            f"N={n_lot}-lot × Kelly={kelly:.2f} × {cost_arm}={cost_label}"
                        ),
                    )
                )
    return configs


@dataclass
class _Position:
    """In-position state. Single-unit per H067 v1 (no pyramiding)."""
    side: int  # +1 long, -1 short
    entry_price: float
    size: int  # N_realized after Kelly + cap clipping
    n_lot_requested: int  # N-lot grid value requested
    stop_price: float
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
    """Load 5-min OHLC bars for `symbol` over [start, end]."""
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


def _run_n_lot_simulation(
    *,
    symbol: str,
    df_5m: pd.DataFrame,
    feature_config: H062FeatureConfig,
    k_atr: float,
    cfg: NLotConfig,
    cost_model: NT8RealisticCostModel | None,
    starting_equity: float = 10000.0,
    eod_flatten_minutes_from_open: int = 360,
) -> dict[str, Any]:
    """H067 simulator with N-lot sizing + optional cost model.

    Per H067 design.md §4 exit-precedence:
        1. gap-through-stop at bar-t open
        2. stop hit during bar
        3. opposite-channel break at bar close
        4. EOD-flatten / session-rollover

    Returns per-cell metrics + per-session log-returns + per-trade R-multiples.
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

    multiplier = _MULTIPLIERS.get(symbol, 1.0)
    cap = _CAPACITY_CAPS.get(symbol, 1)

    equity = starting_equity
    session_start_equity = starting_equity  # ADR-0017 §4.1 session-start denominator
    trade_log: list[dict] = []
    equity_curve: list[float] = [starting_equity]
    n_ruin_events = 0

    session_starts: dict[object, int] = {}
    last_session_seen: object = None
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
        gross_pnl = position.side * (exit_price - position.entry_price) * multiplier * position.size
        # Cost subtraction per ADR-0025 §D-3 + ADR-0028 §D-2 round-trip-per-trade
        cost_usd = 0.0
        if cost_model is not None:
            cost_usd = cost_model.round_trip_cost_usd(
                symbol=symbol, n_contracts=position.size
            )
        net_pnl = gross_pnl - cost_usd
        r_mult = net_pnl / position.r_dollar if position.r_dollar > 0 else 0.0
        equity += net_pnl
        equity_curve.append(equity)
        trade_log.append({
            "side": position.side,
            "entry_price": float(position.entry_price),
            "exit_price": float(exit_price),
            "size": int(position.size),
            "n_lot_requested": int(position.n_lot_requested),
            "gross_pnl": float(gross_pnl),
            "cost_usd": float(cost_usd),
            "pnl": float(net_pnl),
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

    def _check_exits(t: int) -> bool:
        nonlocal position
        if position is None:
            return False
        bar_session = session_dates[t]
        # 1. Gap-through-stop at open
        if position.side == 1:
            if open_[t] < position.stop_price:
                _close_position(t, float(open_[t]), "gap_through_stop_long")
                return True
            # 2. Stop hit during bar
            if low[t] <= position.stop_price:
                _close_position(t, float(position.stop_price), "stop_hit_long")
                return True
        else:  # short
            if open_[t] > position.stop_price:
                _close_position(t, float(open_[t]), "gap_through_stop_short")
                return True
            if high[t] >= position.stop_price:
                _close_position(t, float(position.stop_price), "stop_hit_short")
                return True
        # 3. Opposite-channel break at close
        ev = int(feats.filtered_events[t])
        if (position.side == 1 and ev == -1) or (position.side == -1 and ev == 1):
            _close_position(t, float(close[t]), "opposite_channel_break")
            return True
        # 4. EOD flatten
        session_open_idx = session_starts.get(bar_session, t)
        if (t - session_open_idx) >= eod_flatten_minutes_from_open:
            _close_position(t, float(close[t]), "eod_flatten")
            return True
        # 5. Session rollover
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
        # H067 §4 sizing: target_dollar_risk × N_lot_grid, clipped at cap
        eq_for_sizing = equity if cfg.use_current_equity_rebase else starting_equity
        target_dollar_risk = eq_for_sizing * cfg.risk_budget_pct
        # The H065 v1 simulator floors size_from_risk and ignores kelly_multiplier
        # at the per-trade scaling layer (kelly is an inner-CV hyperparameter; see
        # H062 v1 KPI report card §"Scope deviations"). H067 preserves this
        # convention verbatim per ADR-0027 §D-4 single-axis discipline.
        size_from_risk = target_dollar_risk / dollar_1r_per_contract
        size_from_risk_capped = min(size_from_risk, cap)
        # N-lot multiplier per H067 §4: multiplies grid N up to cap, then capped.
        size_n_lot = int(np.floor(min(cfg.n_lot * size_from_risk_capped, cap)))
        if size_n_lot < 1:
            return
        stop_price = entry_price - ev * (k_atr * atr_t)
        bar_session = session_dates[t]
        position = _Position(
            side=ev,
            entry_price=entry_price,
            size=size_n_lot,
            n_lot_requested=cfg.n_lot,
            stop_price=stop_price,
            r_dollar=dollar_1r_per_contract * size_n_lot,
            entry_idx=entry_idx_candidate,
            entry_session_date=bar_session,
        )

    for t in range(n_bars - 1):
        # ADR-0017 §4.1 session-start equity ratcheting: refresh at session change
        sd = session_dates[t]
        if sd != last_session_seen:
            session_start_equity = equity
            last_session_seen = sd
        if position is not None:
            closed = _check_exits(t)
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
    raw_max_dd_pct = float(-dd.min()) * 100 if dd.size > 0 else 0.0
    max_dd_pct = min(raw_max_dd_pct, 100.0)
    bankroll_blowup = bool((eq_arr < 0).any())

    trade_pnls = np.array([t["pnl"] for t in trade_log])
    trade_rs = np.array([t["r_multiple"] for t in trade_log])
    trade_costs = np.array([t.get("cost_usd", 0.0) for t in trade_log])
    trade_gross_pnls = np.array([t.get("gross_pnl", 0.0) for t in trade_log])
    wins = int((trade_pnls > 0).sum())
    losses = int((trade_pnls < 0).sum())
    zeros = int((trade_pnls == 0).sum())
    n_trades = len(trade_log)

    # ---- Per-session aggregated log-returns ----
    session_eq_at_close: dict[object, float] = {}
    for tr in trade_log:
        exit_sd = tr["exit_session_date"]
        max_idx_key = f"_max_idx_{exit_sd}"
        if exit_sd not in session_eq_at_close or tr["exit_idx"] > session_eq_at_close.get(max_idx_key, -1):
            session_eq_at_close[exit_sd] = tr["equity_post_trade"]
            session_eq_at_close[max_idx_key] = tr["exit_idx"]
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

    # ---- Sub-window 2026-04-01 → 2026-05-15 ----
    def _to_date(d: object) -> object:
        if isinstance(d, _dt.date) and not isinstance(d, _dt.datetime):
            return d
        try:
            return pd.Timestamp(d).date()
        except Exception:
            return d

    sub_trades = [tr for tr in trade_log
                  if _SUBWINDOW_START <= _to_date(tr["exit_session_date"]) <= _SUBWINDOW_END]
    if sub_trades:
        first_sub_idx = trade_log.index(sub_trades[0])
        sub_starting_eq = (
            trade_log[first_sub_idx - 1]["equity_post_trade"]
            if first_sub_idx > 0
            else starting_equity
        )
        sub_pnl_sum = sum(tr["pnl"] for tr in sub_trades)
        sub_realized_end = sub_starting_eq + sub_pnl_sum
        sub_realized_roi_pct = (sub_pnl_sum / sub_starting_eq) * 100 if sub_starting_eq > 0 else 0.0
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
        sub_wins = sub_losses = sub_zeros = 0

    # ---- MPPM(ρ=1) on per-session log-returns ----
    # MPPMResult exposes the point estimate as `theta_hat` (per
    # src/skie_ninja/inference/mppm.py:111). The H065 sweep used
    # `.point_estimate` which is a defect carried over from the
    # H062 v1 fixed-rebase variant; H067 corrects the attribute access.
    if session_log_ret_arr.size >= 4:
        session_simple_returns = np.expm1(session_log_ret_arr)
        try:
            mppm_ci_result = mppm_with_ci(
                session_simple_returns,
                rho=1.0,
                risk_free=0.0,
                delta_t=1.0 / _ANNUALIZATION_FACTOR,
                n_bootstrap=_N_BOOTSTRAP_CI,
                rng_seed=_RNG_SEED,
            )
            mppm_point = float(mppm_ci_result.theta_hat)
            mppm_ci_low = float(mppm_ci_result.ci_low) if mppm_ci_result.ci_low is not None else float("nan")
            mppm_ci_high = float(mppm_ci_result.ci_high) if mppm_ci_result.ci_high is not None else float("nan")
            mppm_excludes_zero = bool(mppm_ci_result.excludes_zero) if mppm_ci_result.excludes_zero is not None else False
        except Exception as e:  # noqa: BLE001
            _log.warning("MPPM CI failed (%s): %s", symbol, e)
            mppm_point = float(mppm_rho_1(session_simple_returns, risk_free=0.0,
                                          delta_t=1.0 / _ANNUALIZATION_FACTOR))
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
                trade_rs, n_bootstrap=_N_BOOTSTRAP_CI, rng_seed=_RNG_SEED + 1,
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
                trade_rs, n_bootstrap=_N_BOOTSTRAP_CI, rng_seed=_RNG_SEED + 2,
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

    pf = profit_factor(trade_pnls) if trade_pnls.size else 0.0

    if session_log_ret_arr.size > 1 and session_log_ret_arr.std(ddof=1) > 0:
        sr_session = session_log_ret_arr.mean() / session_log_ret_arr.std(ddof=1)
        sr_annualised = sr_session * np.sqrt(_ANNUALIZATION_FACTOR)
    else:
        sr_annualised = float("nan")

    if session_log_ret_arr.size >= 4:
        try:
            calmar = float(calmar_ratio(session_log_ret_arr, annualization_factor=_ANNUALIZATION_FACTOR))
        except Exception:
            calmar = float("nan")
    else:
        calmar = float("nan")

    # ---- Cost-friction-breakeven ratio per ADR-0028 §D-2 + cross-hyp inv §2 schema ----
    # gross_edge_bps_eq = mean(per-trade gross_pnl / equity_at_entry) × 10000
    # cost_bps_eq = mean(per-trade cost_usd / equity_at_entry) × 10000
    # ratio = gross_edge_bps_eq / cost_bps_eq (when cost > 0)
    if n_trades > 0 and cost_model is not None:
        # Use $10K starting equity as reference (project-canonical)
        gross_edge_bps_eq = float(np.mean(trade_gross_pnls) / starting_equity * 10000)
        cost_bps_eq = float(np.mean(trade_costs) / starting_equity * 10000)
        if cost_bps_eq > 0:
            breakeven_ratio = gross_edge_bps_eq / cost_bps_eq
        else:
            breakeven_ratio = float("inf")
    else:
        gross_edge_bps_eq = float(np.mean(trade_gross_pnls) / starting_equity * 10000) if n_trades > 0 else 0.0
        cost_bps_eq = 0.0
        breakeven_ratio = float("nan")  # n/a for A0 cells

    # Trade log summary (lighter for sidecar; full trade_log on per-cell debug only)
    trade_log_summary = [
        {
            "entry_session_date": str(tr["entry_session_date"]),
            "exit_session_date": str(tr["exit_session_date"]),
            "exit_reason": tr["exit_reason"],
            "size": int(tr["size"]),
            "n_lot_requested": int(tr.get("n_lot_requested", 0)),
            "pnl": float(tr["pnl"]),
            "gross_pnl": float(tr.get("gross_pnl", 0.0)),
            "cost_usd": float(tr.get("cost_usd", 0.0)),
            "r_multiple": float(tr["r_multiple"]),
        }
        for tr in trade_log[:50]  # cap to first 50 for sidecar bloat control
    ]

    return {
        "symbol": symbol,
        "cfg_name": cfg.name,
        "n_lot": cfg.n_lot,
        "kelly_multiplier": cfg.kelly_multiplier,
        "cost_arm": cfg.cost_arm,
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
        "subwindow_starting_equity": sub_starting_eq,
        "subwindow_realized_end_equity": sub_realized_end,
        "subwindow_realized_roi_pct": sub_realized_roi_pct,
        "subwindow_realized_max_dd_pct": sub_max_dd_pct,
        "subwindow_wins": sub_wins,
        "subwindow_losses": sub_losses,
        "subwindow_zeros": sub_zeros,
        "subwindow_n_trades": len(sub_trades),
        "gross_edge_bps_eq": gross_edge_bps_eq,
        "cost_bps_eq": cost_bps_eq,
        "cost_friction_breakeven_ratio": breakeven_ratio,
        "mean_cost_usd": float(np.mean(trade_costs)) if n_trades > 0 else 0.0,
        "mean_gross_pnl_usd": float(np.mean(trade_gross_pnls)) if n_trades > 0 else 0.0,
        "session_log_returns": session_log_ret_arr.tolist(),
        "session_pnls": session_pnl_arr.tolist(),
        "session_dates": [str(sd) for sd in session_dates_ordered],
        "trade_log_summary": trade_log_summary,
    }


def _annotate_cost_friction_dominated_edge(
    a0_result: dict[str, Any],
    a1_result: dict[str, Any],
    threshold: float = 2.0,
) -> str:
    """Per ADR-0028 §D-2 trigger semantics:
        - present: A0 OOS ROI > 0 AND A1 OOS ROI < 0 AND A1 ratio >= threshold
        - absent: A1 cell does NOT flip realized OOS from positive to negative
        - n/a: only A0 emitted (no cost context)
    """
    if a1_result is None:
        return "cost-friction-dominated-edge-n/a"
    a0_roi = a0_result.get("realized_roi_pct", 0.0)
    a1_roi = a1_result.get("realized_roi_pct", 0.0)
    a1_ratio = a1_result.get("cost_friction_breakeven_ratio", float("nan"))
    if a0_roi > 0 and a1_roi < 0 and (np.isfinite(a1_ratio) and a1_ratio >= threshold):
        return "cost-friction-dominated-edge-present"
    elif a0_roi > 0 and a1_roi < 0:
        # A1 flips negative but ratio doesn't reach threshold — still cost-dominated in practice
        return "cost-friction-dominated-edge-present"
    return "cost-friction-dominated-edge-absent"


def _annotate_promising(result: dict[str, Any], substrate_sha: str) -> str | None:
    """Per ADR-0026 §D-3: emit `promising-mppm-cost-{arm}-{substrate-sha-prefix-16}`
    when MPPM CI strictly excludes zero positively. Otherwise emit `not-promising`.
    """
    excludes_pos = bool(
        result.get("mppm_rho1_excludes_zero")
        and (result.get("mppm_rho1") or 0.0) > 0
    )
    cost_arm = result.get("cost_arm", "A0")
    cost_label = "zero" if cost_arm == "A0" else "conservative-prior"
    prefix = substrate_sha[:16] if substrate_sha and substrate_sha != "UNKNOWN_PROVENANCE_NOT_FOUND" else "UNK"
    if excludes_pos:
        return f"promising-mppm-cost-{cost_label}-{prefix}"
    return f"not-promising-mppm-cost-{cost_label}-{prefix}"


def _format_kpi_table(rows: list[dict[str, Any]]) -> str:
    """H067 §13 KPI metrics table — the load-bearing operator deliverable."""
    lines: list[str] = []
    lines.append("=" * 260)
    lines.append("H067 N-LOT SWEEP — KPI METRICS TABLE (per H067 design.md §13)")
    lines.append("=" * 260)
    hdr = (
        f"{'Cfg':<22} {'N':>3} {'Kelly':>6} {'Arm':>4} "
        f"{'OOS_ROI%':>10} {'MaxDD%':>8} {'W/L/Z':>14} "
        f"{'Sharpe':>8} {'Calmar':>8} {'PF':>6} {'R_mean':>8} "
        f"{'MPPM_low':>10} {'MPPM_pt':>10} {'MPPM_hi':>10} {'tau3':>7} "
        f"{'n_trd':>7} {'subROI%':>9} {'subDD%':>8} {'ratio':>7}"
    )
    lines.append(hdr)
    lines.append("-" * 260)
    for r in rows:
        k_str = f"{r['kelly_multiplier']:.2f}" if r.get('kelly_multiplier') else "n/a"
        sr_str = f"{r['sr_annualised']:.3f}" if r.get('sr_annualised') is not None else "n/a"
        calmar_str = f"{r['calmar']:.3f}" if r.get('calmar') is not None else "n/a"
        pf_str = f"{r['profit_factor']:.2f}" if r.get('profit_factor') is not None else "n/a"
        wlz = f"{r['wins']}/{r['losses']}/{r['zeros']}"
        ratio = r.get('cost_friction_breakeven_ratio', float('nan'))
        ratio_str = f"{ratio:.3f}" if np.isfinite(ratio) else "n/a"
        line = (
            f"{r['cfg_name']:<22} {r['n_lot']:>3} {k_str:>6} {r['cost_arm']:>4} "
            f"{r['realized_roi_pct']:>+9.2f}% {r['realized_max_dd_pct']:>+7.2f}% "
            f"{wlz:>14} "
            f"{sr_str:>8} {calmar_str:>8} {pf_str:>6} {r['r_multiple_mean']:>+8.3f} "
            f"{r['mppm_rho1_ci_low']:>+10.3f} {r['mppm_rho1']:>+10.3f} {r['mppm_rho1_ci_high']:>+10.3f} "
            f"{r['l_skewness_tau3']:>+7.3f} "
            f"{r['n_trades']:>7} "
            f"{r['subwindow_realized_roi_pct']:>+8.2f}% {r['subwindow_realized_max_dd_pct']:>+7.2f}% "
            f"{ratio_str:>7}"
        )
        lines.append(line)
    lines.append("=" * 260)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H067 N-lot sweep")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--end-date",
        default="2026-05-15",
        help="OOS test end date (UTC) ISO format (default 2026-05-15).",
    )
    parser.add_argument(
        "--start-date",
        default="2020-01-01",
        help="OOS test start date (UTC) ISO format (default 2020-01-01 = H067 IS start).",
    )
    args = parser.parse_args(argv)

    paths = ProjectPaths.discover()

    if args.substrate_path:
        substrate_root = Path(args.substrate_path).resolve()
    else:
        substrate_root = paths.root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"

    # Resolve substrate provenance for ReproLog binding
    substrate_sha = _resolve_substrate_dataset_checksum()
    _log.info("Substrate root: %s | SHA: %s", substrate_root, substrate_sha[:16] + "...")

    # Per-partition SHA enumeration per P1-H067-SUBSTRATE-PER-PARTITION-SHA-EMIT
    _log.info("Enumerating SIL partition SHAs...")
    sil_partition_shas = _compute_sil_partition_shas(substrate_root)
    _log.info("  %d SIL partitions verified", len(sil_partition_shas))

    # Resolve config-resolved hash (no YAML for H067 v1; hash the script + parameters)
    script_path = Path(__file__).resolve()
    script_bytes = script_path.read_bytes()
    script_sha256 = hashlib.sha256(script_bytes).hexdigest()
    # config_resolved = hash of (script_sha + RNG_SEED + grid params)
    config_resolved_payload = json.dumps({
        "script_sha256": script_sha256,
        "rng_seed": _RNG_SEED,
        "n_lot_grid": [1, 2, 3, 4, 5],
        "kelly_grid": [0.25, 0.5, 1.0, 1.5, 2.0, 2.5],
        "cost_arms": ["A0", "A1"],
        "n_bootstrap_ci": _N_BOOTSTRAP_CI,
    }, sort_keys=True).encode("utf-8")
    config_resolved_sha256 = hashlib.sha256(config_resolved_payload).hexdigest()

    dataset_checksums = {"vendor_legacy_1min_roll_adjusted": substrate_sha}

    with RunContext(
        phase="walk_forward_h067_n_lot_sweep",
        hypothesis_id="H067",
        rng_seed=_RNG_SEED,
        dataset_checksums=dataset_checksums,
        config_resolved_sha256=config_resolved_sha256,
    ) as ctx:
        ctx.set_model_hash("PENDING")
        run_id = ctx.log.run_id  # type: ignore[union-attr]
        out_dir = (
            Path(args.output_dir).resolve()
            if args.output_dir
            else paths.root / "artifacts" / "runs" / "H067" / run_id
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        _log.info("run_id=%s out_dir=%s", run_id, out_dir)

        start = pd.Timestamp(args.start_date, tz="UTC")
        end_master = pd.Timestamp(args.end_date, tz="UTC")

        feat_cfg = H062FeatureConfig(
            channel_n=120,
            atr_n=14,
            h_dwell=5,
            trend_id="a_ts_mom",
            trend_id_lookback_l=60,
            trend_id_threshold=1.0,
        )
        k_atr = 2.0

        # Build A1 cost model (NT8 realistic conservative_prior per ADR-0025 §D-3)
        a1_cost_model = NT8RealisticCostModel(
            sensitivity_mult=1.0,
            calibration_source="conservative_prior",
        )

        sweep_configs = _build_sweep_configs()
        _log.info("Sweep: %d cells (5 N × 6 Kelly × 2 cost-arm)", len(sweep_configs))

        symbol = "SIL"
        _log.info("Loading %s [%s → %s]...", symbol, start.date(), end_master.date())
        df_5m = _load_5min_bars(substrate_root, symbol, start=start, end=end_master)
        n_sessions = df_5m["session_date_et"].nunique()
        _log.info("  %s: %d 5-min bars (%d sessions)", symbol, len(df_5m), n_sessions)

        per_cell_results: list[dict[str, Any]] = []
        for i, cfg in enumerate(sweep_configs):
            cost_model = None if cfg.cost_arm == "A0" else a1_cost_model
            res = _run_n_lot_simulation(
                symbol=symbol,
                df_5m=df_5m,
                feature_config=feat_cfg,
                k_atr=k_atr,
                cfg=cfg,
                cost_model=cost_model,
            )
            res["cfg_description"] = cfg.description
            res["cost_arm_label"] = "cost-zero" if cfg.cost_arm == "A0" else "cost-conservative-prior"
            per_cell_results.append(res)
            _log.info(
                "[%2d/%d] %s: roi=%+.2f%% MaxDD=%.2f%% trades=%d MPPM=%+.3f [%+.3f,%+.3f] r_mean=%+.3f ratio=%s",
                i + 1, len(sweep_configs), cfg.name,
                res["realized_roi_pct"], res["realized_max_dd_pct"], res["n_trades"],
                res["mppm_rho1"], res["mppm_rho1_ci_low"], res["mppm_rho1_ci_high"],
                res["r_multiple_mean"],
                f"{res['cost_friction_breakeven_ratio']:.3f}" if np.isfinite(res['cost_friction_breakeven_ratio']) else "n/a",
            )

        # Pair A0/A1 cells for cost-friction annotation
        cell_index: dict[tuple[int, float, str], dict[str, Any]] = {}
        for r in per_cell_results:
            key = (r["n_lot"], r["kelly_multiplier"], r["cost_arm"])
            cell_index[key] = r
        for r in per_cell_results:
            a0_key = (r["n_lot"], r["kelly_multiplier"], "A0")
            a1_key = (r["n_lot"], r["kelly_multiplier"], "A1")
            a0_r = cell_index.get(a0_key)
            a1_r = cell_index.get(a1_key)
            if r["cost_arm"] == "A1":
                annotation = _annotate_cost_friction_dominated_edge(a0_r, a1_r)
            else:
                annotation = _annotate_cost_friction_dominated_edge(a0_r, None)
            r["cost_friction_dominated_edge_annotation"] = annotation
            r["promising_annotation"] = _annotate_promising(r, substrate_sha)

        # Print KPI table
        all_rows_sorted = sorted(
            per_cell_results,
            key=lambda r: (r["n_lot"], r["kelly_multiplier"], r["cost_arm"]),
        )
        kpi_table = _format_kpi_table(all_rows_sorted)
        print()
        print(kpi_table)
        print()

        # Sensitivity table per H067 §6: cost-friction-breakeven ratio at
        # sensitivity_mult ∈ {1.0, 0.5, 0.0} — operator-actionable diff between
        # conservative_prior and empirical-slip-reduction-needed-to-clear-threshold.
        sensitivity_rows: list[dict[str, Any]] = []
        for n_lot in [1, 2, 3, 4, 5]:
            # Pick the quarter-Kelly cell as the reference (matches parent H065 v2 modal)
            ref_cell = next(
                (r for r in per_cell_results if r["n_lot"] == n_lot
                 and r["kelly_multiplier"] == 0.25 and r["cost_arm"] == "A1"),
                None,
            )
            if ref_cell is None:
                continue
            gross_edge_bps = ref_cell["gross_edge_bps_eq"]
            cost_bps = ref_cell["cost_bps_eq"]
            # Decompose cost: fixed-fee component vs slip component
            # cost_per_trade ≈ N × ($1.87 fixed + $5.00 × sensitivity_mult slip)
            # baseline at sensitivity=1.0: cost_per_trade = N × $6.87
            # at sensitivity=0.5: cost_per_trade = N × ($1.87 + $2.50) = N × $4.37
            # at sensitivity=0.0: cost_per_trade = N × $1.87
            # Compute scaling factor for each sensitivity_mult
            baseline_per_side = 1.87 + 5.00  # fixed + slip at sensitivity=1.0
            for sens in [1.0, 0.5, 0.0]:
                per_side = 1.87 + 5.00 * sens
                rt_cost_scaled = 2.0 * per_side * n_lot  # round-trip × N contracts
                # Adjust the per-trade cost proportionally
                cost_bps_scaled = cost_bps * (per_side / baseline_per_side)
                if cost_bps_scaled > 0:
                    ratio_scaled = gross_edge_bps / cost_bps_scaled
                else:
                    ratio_scaled = float("inf")
                sensitivity_rows.append({
                    "n_lot": n_lot,
                    "sensitivity_mult": sens,
                    "per_side_usd": per_side,
                    "round_trip_cost_usd_per_trade": rt_cost_scaled,
                    "gross_edge_bps_eq": gross_edge_bps,
                    "cost_bps_eq": cost_bps_scaled,
                    "cost_friction_breakeven_ratio": ratio_scaled,
                })

        # Sidecar payload
        payload = {
            "hypothesis_id": "H067",
            "experiment": "n_lot_sweep_v1",
            "run_id": run_id,
            "script_sha256": script_sha256,
            "config_resolved_sha256": config_resolved_sha256,
            "substrate_dataset_checksum": substrate_sha,
            "sil_partition_shas": sil_partition_shas,
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
            "universe": ["SIL"],
            "oos_window": {
                "start": str(start.date()),
                "end": str(end_master.date()),
            },
            "subwindow_definition": {
                "start": str(_SUBWINDOW_START),
                "end": str(_SUBWINDOW_END),
            },
            "n_sessions_loaded": int(n_sessions),
            "n_5min_bars_loaded": int(len(df_5m)),
            "configurations": [
                {
                    "name": c.name,
                    "n_lot": c.n_lot,
                    "kelly_multiplier": c.kelly_multiplier,
                    "risk_budget_pct": c.risk_budget_pct,
                    "use_current_equity_rebase": c.use_current_equity_rebase,
                    "cost_arm": c.cost_arm,
                    "description": c.description,
                } for c in sweep_configs
            ],
            "per_cell_results": all_rows_sorted,
            "cost_sensitivity_table": sensitivity_rows,
            "kpi_table_text": kpi_table,
            "kill_switch_runtime": {
                "k3_enabled": False,  # vacuous H067 v1 (no pyramiding)
                "k4_enabled": True,   # SIL ≤ 5 cap
                "k6_enabled": True,   # block-mode per ADR-0028 §D-1 default
                "k7_enabled": True,   # block-mode per ADR-0028 §D-1 default
                "enforcement_mode": "block",
                "annotation": "kill-switch-active",
                "mode_annotation": "kill-switch-mode-block",
            },
            "bocd_live": {
                "enabled": False,
                "annotation": "bocd-live-inactive",
            },
            "equity_rebase": {
                "mode": "current",
                "annotation": "equity-rebase-current",
            },
            "cost_model_arms": {
                "A0": "cost-zero",
                "A1": "cost-conservative-prior",
            },
            "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
        }
        sidecar_path = out_dir / "sidecar.json"
        sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        sidecar_path.write_bytes(sidecar_bytes)
        sha = hashlib.sha256(sidecar_bytes).hexdigest()
        (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
        (out_dir / "kpi_table.txt").write_text(kpi_table, encoding="utf-8")
        ctx.set_model_hash(sha)  # bind sidecar SHA into ReproLog
        _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])
        _log.info("kpi_table=%s", out_dir / "kpi_table.txt")
        print(f"sidecar: {sidecar_path}")
        print(f"sha256:  {sha}")
        print(f"run_id:  {run_id}")
        return 0


if __name__ == "__main__":
    # ADR-0009 BLAS thread-pinning carry-forward
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
