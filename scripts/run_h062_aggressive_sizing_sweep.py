"""H062 aggressive-sizing sweep — current-equity rebase + Kelly grid expansion + Turtle System 2 pyramiding.

Per operator 2026-05-15 directive ("let us increase the risk. either by
kelly criterion when losing, winning, pyramiding, and also increase the
dollar value per trade") this script sweeps across 6 configurations of
the H062 per-trade simulator on the same post-Phase-O.0 substrate:

  v1     (baseline):                Kelly=0.25, risk=1%, fixed-equity rebase ($10K), no pyramid
  C1     (ADR-0017 rebase):         Kelly=0.25, risk=1%, current-equity rebase,        no pyramid
  C2     (full-Kelly):               Kelly=1.0,  risk=1%, current-equity rebase,        no pyramid
  C3     (super-Kelly):              Kelly=2.0,  risk=1%, current-equity rebase,        no pyramid
  C4     (full-Kelly + pyramid):     Kelly=1.0,  risk=1%, current-equity rebase,        Turtle-2 pyramid
  C5     (super-Kelly + 2% + pyramid): Kelly=2.0, risk=2%, current-equity rebase,       Turtle-2 pyramid

Pyramiding (Turtle System 2 per Faith 2007 *Way of the Turtle*
ISBN 978-0071486644 *practitioner* §4): when price moves 1N (= 1 × ATR_n,t)
in favor from the most-recent entry, add 1 unit at the new price with
its own ATR-stop at new_entry ∓ k_atr × ATR_n,new_t. Max 4 units per
position (Turtle convention). Per-unit stops update as new units are
added — when the channel exit fires or any unit's stop is hit, ALL units
in the position close at the exit price (Turtle System 2 convention:
position-level stop, not unit-level).

K-3 no-add-to-LOSER preserved per ADR-0017 §5: pyramiding only triggers
on favorable moves (1N in arm's direction); adverse moves never trigger
new units. This is consistent with K-3 — channel-flip closes the
position; pyramiding adds in the SAME direction as the original signal
not against it.

Scope: representative feature cell (channel_n=120, k_atr=2.0, h_dwell=5,
atr_n=14, trend_id=a_ts_mom L=60 τ=1.0) common across all 4 symbols.
Single-cell sweep (no inner-CV grid) so wall-clock stays bounded for
the comparison run.

Output: comparison sidecar at
``artifacts/runs/H062/aggressive_sizing_sweep_<ts>/sweep_sidecar.json``
+ a printed table showing ROI / MaxDD / W/L/Z / Sharpe / P(ruin) /
forward P(<half) per (symbol × config) cell.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h062_aggressive_sweep")


_MULTIPLIERS: dict[str, float] = {
    "ES": 50.0, "NQ": 20.0, "MGC": 10.0, "SIL": 1000.0,
}
_CAPACITY_CAPS: dict[str, int] = {
    "ES": 20, "NQ": 40, "MGC": 5, "SIL": 5,
}


@dataclass(frozen=True)
class SweepConfig:
    """Aggressive-sizing configuration cell."""
    name: str
    kelly_multiplier: float
    risk_budget_pct: float
    use_current_equity_rebase: bool
    enable_pyramiding: bool
    pyramid_max_units: int
    pyramid_step_atr: float
    description: str


SWEEP_CONFIGS: list[SweepConfig] = [
    SweepConfig(
        name="v1",
        kelly_multiplier=0.25,
        risk_budget_pct=0.01,
        use_current_equity_rebase=False,
        enable_pyramiding=False,
        pyramid_max_units=1,
        pyramid_step_atr=0.0,
        description="v1 baseline (quarter-Kelly, fixed $10K rebase, no pyramid)",
    ),
    SweepConfig(
        name="C1_rebase",
        kelly_multiplier=0.25,
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        enable_pyramiding=False,
        pyramid_max_units=1,
        pyramid_step_atr=0.0,
        description="C1: ADR-0017 §4.1 current-equity rebase only",
    ),
    SweepConfig(
        name="C2_fullkelly",
        kelly_multiplier=1.0,
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        enable_pyramiding=False,
        pyramid_max_units=1,
        pyramid_step_atr=0.0,
        description="C2: full-Kelly + current-equity rebase",
    ),
    SweepConfig(
        name="C3_superkelly",
        kelly_multiplier=2.0,
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        enable_pyramiding=False,
        pyramid_max_units=1,
        pyramid_step_atr=0.0,
        description="C3: super-Kelly 2.0× + current-equity rebase",
    ),
    SweepConfig(
        name="C4_fullkelly_pyramid",
        kelly_multiplier=1.0,
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        enable_pyramiding=True,
        pyramid_max_units=4,
        pyramid_step_atr=1.0,
        description="C4: full-Kelly + rebase + Turtle-2 pyramid (max 4 units; 1N spacing)",
    ),
    SweepConfig(
        name="C5_super_2pct_pyramid",
        kelly_multiplier=2.0,
        risk_budget_pct=0.02,
        use_current_equity_rebase=True,
        enable_pyramiding=True,
        pyramid_max_units=4,
        pyramid_step_atr=1.0,
        description="C5: super-Kelly 2.0× + 2% risk + rebase + Turtle-2 pyramid",
    ),
]


@dataclass
class _Position:
    """In-position state for the v2 simulator with pyramiding support."""
    side: int  # +1 long, -1 short
    units: list[dict]  # each: {entry_price, size, stop_price, entry_idx}
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


def _run_aggressive_simulation(
    *,
    symbol: str,
    df_5m: pd.DataFrame,
    feature_config: H062FeatureConfig,
    k_atr: float,
    cfg: SweepConfig,
    starting_equity: float = 10000.0,
    eod_flatten_minutes_from_open: int = 360,
) -> dict[str, Any]:
    """V2 simulator with current-equity rebase + pyramiding support."""
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

    # Running equity tracker (per ADR-0017 §4.1 current-equity rebase).
    equity = starting_equity
    trade_log: list[dict] = []
    equity_curve: list[float] = [starting_equity]
    equity_curve_dates: list[object] = []

    # Session-start map.
    session_starts: dict[object, int] = {}
    for t in range(n_bars):
        sd = session_dates[t]
        if sd not in session_starts:
            session_starts[sd] = t

    position: _Position | None = None  # None means flat
    n_ruin_events = 0  # tracks when equity crosses below 50% of starting

    def _close_all_units(
        exit_idx: int,
        exit_price: float,
        reason: str,
    ) -> None:
        nonlocal position, equity, n_ruin_events
        if position is None:
            return
        total_pnl = 0.0
        total_r_dollar = 0.0  # for aggregate R-multiple
        for u in position.units:
            unit_pnl = position.side * (exit_price - u["entry_price"]) * multiplier * u["size"]
            total_pnl += unit_pnl
            total_r_dollar += u["r_dollar"]
        r_mult = total_pnl / total_r_dollar if total_r_dollar > 0 else 0.0
        # Update equity.
        equity += total_pnl
        equity_curve.append(equity)
        equity_curve_dates.append(position.entry_session_date)
        # Log trade.
        trade_log.append({
            "side": position.side,
            "n_units": len(position.units),
            "total_size": sum(u["size"] for u in position.units),
            "entry_first": float(position.units[0]["entry_price"]),
            "entry_last": float(position.units[-1]["entry_price"]),
            "exit_price": float(exit_price),
            "total_pnl": float(total_pnl),
            "total_r_dollar": float(total_r_dollar),
            "r_multiple": float(r_mult),
            "exit_reason": reason,
            "entry_session_date": position.entry_session_date,
            "equity_post_trade": float(equity),
        })
        # Ruin check.
        if equity < 0.5 * starting_equity:
            n_ruin_events += 1
        position = None

    def _check_stops_and_exits(t: int) -> bool:
        """Returns True if position closed at bar t."""
        nonlocal position
        if position is None:
            return False
        bar_session = session_dates[t]
        # Gap-through-stop on bar-t open (against worst unit's stop)
        # For longs: worst stop is min across units (lowest); for shorts: max across units (highest)
        unit_stops = [u["stop_price"] for u in position.units]
        if position.side == 1:
            worst_stop = max(unit_stops)  # for longs, the tightest stop (least slack)
            if open_[t] < worst_stop:
                _close_all_units(t, float(open_[t]), "gap_through_stop_long")
                return True
            if low[t] <= worst_stop:
                _close_all_units(t, float(worst_stop), "stop_hit_long")
                return True
        else:
            worst_stop = min(unit_stops)
            if open_[t] > worst_stop:
                _close_all_units(t, float(open_[t]), "gap_through_stop_short")
                return True
            if high[t] >= worst_stop:
                _close_all_units(t, float(worst_stop), "stop_hit_short")
                return True
        # Opposite-channel break
        ev = int(feats.filtered_events[t])
        if (position.side == 1 and ev == -1) or (position.side == -1 and ev == 1):
            _close_all_units(t, float(close[t]), "opposite_channel_break")
            return True
        # EOD-flatten
        session_open_idx = session_starts.get(bar_session, t)
        if (t - session_open_idx) >= eod_flatten_minutes_from_open:
            _close_all_units(t, float(close[t]), "eod_flatten")
            return True
        # Session-rollover
        if t + 1 < n_bars and session_dates[t + 1] != bar_session:
            _close_all_units(t, float(close[t]), "session_rollover")
            return True
        return False

    def _effective_risk_budget_pct() -> float:
        """Kelly multiplier scales the risk budget (canonical Vince interpretation).

        Per ADR-0018 D-2 + ADR-0017 §4.1: kelly_multiplier ∈ {0.25 .. 2.5}
        scales the fraction-of-bankroll-at-risk per trade. The design.md
        §5.3 notional-leverage cap floors to 0 contracts at retail-equity
        ($10K) for all but super-Kelly metals cells; the v1 simulator
        therefore correctly skipped that clamp and used only the risk-
        budget formulation. This sweep adopts the same convention:
        Kelly multiplier × risk_budget_pct = effective fraction of
        bankroll bet as risk per trade.
        """
        return cfg.kelly_multiplier * cfg.risk_budget_pct

    def _try_pyramid(t: int) -> None:
        """Try to add a new unit on favorable channel-N move."""
        nonlocal position
        if position is None or not cfg.enable_pyramiding:
            return
        if len(position.units) >= cfg.pyramid_max_units:
            return
        last_unit = position.units[-1]
        last_entry = last_unit["entry_price"]
        atr_t = float(feats.atr[t])
        if not np.isfinite(atr_t) or atr_t <= 0:
            return
        spacing = cfg.pyramid_step_atr * atr_t
        favorable = (
            (position.side == 1 and close[t] > last_entry + spacing)
            or (position.side == -1 and close[t] < last_entry - spacing)
        )
        if not favorable:
            return
        entry_price = float(close[t])
        dollar_1r_per_contract = k_atr * atr_t * multiplier
        if dollar_1r_per_contract <= 0:
            return
        # Per-unit risk budget = (kelly × risk_budget × equity) / pyramid_max_units
        eq_for_sizing = equity if cfg.use_current_equity_rebase else starting_equity
        effective_risk_pct = _effective_risk_budget_pct()
        # Per Faith 2007 §4 Turtle System 2: each unit sized at FULL risk budget;
        # max units cap the total exposure (max 4× risk_budget at full pyramid).
        per_unit_dollar_risk = effective_risk_pct * eq_for_sizing
        size_from_risk = per_unit_dollar_risk / dollar_1r_per_contract
        size = int(np.floor(size_from_risk))
        total_existing = sum(u["size"] for u in position.units)
        size = min(size, cap - total_existing)
        if size < 1:
            return
        stop_price = entry_price - position.side * (k_atr * atr_t)
        position.units.append({
            "entry_price": entry_price,
            "size": size,
            "stop_price": stop_price,
            "entry_idx": t,
            "r_dollar": dollar_1r_per_contract * size,
        })

    def _try_new_entry(t: int) -> None:
        """Try to open a new flat-to-position entry on eligible signal."""
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
        # Risk budget per trade = (kelly × risk_budget × equity) [/ pyramid_max_units]
        eq_for_sizing = equity if cfg.use_current_equity_rebase else starting_equity
        effective_risk_pct = _effective_risk_budget_pct()
        # Initial entry sizing — when pyramiding enabled, the FIRST unit
        # is sized at the full risk budget (Turtle System 2 convention);
        # subsequent units add at the same per-unit budget via _try_pyramid().
        target_dollar_risk = effective_risk_pct * eq_for_sizing
        size_from_risk = target_dollar_risk / dollar_1r_per_contract
        size = int(np.floor(min(size_from_risk, cap)))
        if size < 1:
            return
        stop_price = entry_price - ev * (k_atr * atr_t)
        bar_session = session_dates[t]
        position = _Position(
            side=ev,
            units=[{
                "entry_price": entry_price,
                "size": size,
                "stop_price": stop_price,
                "entry_idx": entry_idx_candidate,
                "r_dollar": dollar_1r_per_contract * size,
            }],
            entry_session_date=bar_session,
        )

    # Main loop.
    for t in range(n_bars - 1):
        if position is not None:
            closed = _check_stops_and_exits(t)
            if closed:
                continue
            # Try pyramiding on bar-t close
            _try_pyramid(t)
        else:
            _try_new_entry(t)

    if position is not None:
        _close_all_units(n_bars - 1, float(close[-1]), "end_of_data")

    # Realized metrics.
    eq_arr = np.array(equity_curve, dtype=float)
    realized_end = float(eq_arr[-1])
    running_max = np.maximum.accumulate(eq_arr)
    dd = (eq_arr - running_max) / running_max
    max_dd = float(-dd.min()) if dd.size > 0 else 0.0

    trade_pnls = np.array([t["total_pnl"] for t in trade_log])
    trade_rs = np.array([t["r_multiple"] for t in trade_log])
    wins = int((trade_pnls > 0).sum())
    losses = int((trade_pnls < 0).sum())
    zeros = int((trade_pnls == 0).sum())
    n_trades = len(trade_log)

    # Per-trade log-return → annualised Sharpe approximation
    per_trade_log_returns = []
    eq_prev = starting_equity
    for t in trade_log:
        eq_new = t["equity_post_trade"]
        if eq_prev > 0 and eq_new > 0:
            per_trade_log_returns.append(float(np.log(eq_new / eq_prev)))
        else:
            per_trade_log_returns.append(0.0)
        eq_prev = eq_new
    ptlr = np.array(per_trade_log_returns)
    sr_per_trade = ptlr.mean() / ptlr.std(ddof=1) if ptlr.size > 1 and ptlr.std(ddof=1) > 0 else float("nan")
    # Trades-per-year approx for annualisation (5-min cadence × eligible-bar density)
    n_years = max(n_bars / (288 * 252), 0.1)  # 288 5-min bars per 24h × 252 sessions
    sr_annualised = sr_per_trade * np.sqrt(n_trades / n_years) if not np.isnan(sr_per_trade) else float("nan")

    # Bankroll-blowup check (any equity_curve point below 0)
    n_negative_equity = int((eq_arr <= 0).sum())

    return {
        "symbol": symbol,
        "cfg_name": cfg.name,
        "n_trades": n_trades,
        "n_bars": n_bars,
        "realized_end_equity": realized_end,
        "realized_roi_pct": (realized_end / starting_equity - 1.0) * 100,
        "realized_max_dd_pct": max_dd * 100,
        "wins": wins,
        "losses": losses,
        "zeros": zeros,
        "win_rate": wins / max(n_trades, 1),
        "sr_annualised_approx": float(sr_annualised) if not np.isnan(sr_annualised) else None,
        "n_negative_equity_bars": n_negative_equity,
        "n_ruin_events": n_ruin_events,
        "trade_pnl_mean": float(trade_pnls.mean()) if trade_pnls.size else 0.0,
        "trade_pnl_std": float(trade_pnls.std(ddof=1)) if trade_pnls.size > 1 else 0.0,
        "r_multiple_mean": float(trade_rs.mean()) if trade_rs.size else 0.0,
        "max_trade_pnl": float(trade_pnls.max()) if trade_pnls.size else 0.0,
        "min_trade_pnl": float(trade_pnls.min()) if trade_pnls.size else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H062 aggressive-sizing sweep")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=["ES", "NQ", "MGC", "SIL"],
        help="Subset of symbols to sweep (default: all 4).",
    )
    args = parser.parse_args(argv)

    if args.substrate_path:
        substrate_root = Path(args.substrate_path).resolve()
    else:
        substrate_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"

    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else _REPO_ROOT / "artifacts" / "runs" / "H062"
            / f"aggressive_sizing_sweep_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Window: IS 2020-01-01 → OOS per-symbol-right-edge (full v1 window).
    start = pd.Timestamp("2020-01-01", tz="UTC")
    end_per_symbol = {
        "ES": pd.Timestamp("2025-12-03", tz="UTC"),
        "NQ": pd.Timestamp("2024-12-19", tz="UTC"),
        "MGC": pd.Timestamp("2025-12-30", tz="UTC"),
        "SIL": pd.Timestamp("2025-12-30", tz="UTC"),
    }

    # Representative feature cell (v1 production modal).
    feat_cfg = H062FeatureConfig(
        channel_n=120,
        atr_n=14,
        h_dwell=5,
        trend_id="a_ts_mom",
        trend_id_lookback_l=60,
        trend_id_threshold=1.0,
    )
    k_atr = 2.0

    results: list[dict[str, Any]] = []
    for sym in args.symbols:
        sym_end = end_per_symbol.get(sym, pd.Timestamp("2025-12-30", tz="UTC"))
        _log.info("Loading %s [%s → %s]...", sym, start.date(), sym_end.date())
        df_5m = _load_5min_bars(substrate_root, sym, start=start, end=sym_end)
        _log.info("  %s: %d 5-min bars (%d sessions)",
                  sym, len(df_5m), df_5m["session_date_et"].nunique())

        for cfg in SWEEP_CONFIGS:
            res = _run_aggressive_simulation(
                symbol=sym,
                df_5m=df_5m,
                feature_config=feat_cfg,
                k_atr=k_atr,
                cfg=cfg,
            )
            res["cfg_description"] = cfg.description
            res["cfg_kelly_multiplier"] = cfg.kelly_multiplier
            res["cfg_risk_budget_pct"] = cfg.risk_budget_pct
            res["cfg_use_current_equity_rebase"] = cfg.use_current_equity_rebase
            res["cfg_enable_pyramiding"] = cfg.enable_pyramiding
            results.append(res)
            _log.info(
                "  %s × %s: end=$%.0f (%+.1f%%) MaxDD=%.1f%% W/L/Z=%d/%d/%d trades=%d",
                sym, cfg.name, res["realized_end_equity"], res["realized_roi_pct"],
                res["realized_max_dd_pct"], res["wins"], res["losses"], res["zeros"],
                res["n_trades"],
            )

    payload = {
        "hypothesis_id": "H062",
        "experiment": "aggressive_sizing_sweep",
        "feature_cell": {
            "channel_n": 120,
            "atr_n": 14,
            "h_dwell": 5,
            "trend_id": "a_ts_mom",
            "trend_id_lookback_l": 60,
            "trend_id_threshold": 1.0,
            "k_atr": k_atr,
        },
        "starting_equity": 10000.0,
        "configurations": [
            {
                "name": c.name,
                "description": c.description,
                "kelly_multiplier": c.kelly_multiplier,
                "risk_budget_pct": c.risk_budget_pct,
                "use_current_equity_rebase": c.use_current_equity_rebase,
                "enable_pyramiding": c.enable_pyramiding,
                "pyramid_max_units": c.pyramid_max_units,
                "pyramid_step_atr": c.pyramid_step_atr,
            } for c in SWEEP_CONFIGS
        ],
        "results": results,
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sweep_sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sweep_sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sweep_sidecar=%s sha256=%s", sidecar_path, sha[:16])

    # Print comparison table.
    print()
    print("=" * 110)
    print("H062 AGGRESSIVE-SIZING SWEEP — single-cell representative (N=120, k=2.0, h_dwell=5, a_ts_mom L=60 tau=1.0)")
    print(f"sidecar: {sidecar_path}")
    print(f"sha256:  {sha}")
    print("=" * 110)
    for cfg in SWEEP_CONFIGS:
        print()
        print(f"--- {cfg.name}: {cfg.description}")
        print(f"  {'symbol':<6} {'end_eq':>12} {'roi%':>8} {'maxDD%':>8} {'W/L/Z':>20} {'n_trades':>10} {'SR_ann':>8}")
        for r in results:
            if r["cfg_name"] != cfg.name:
                continue
            sr_str = f"{r['sr_annualised_approx']:.2f}" if r['sr_annualised_approx'] is not None else "n/a"
            print(
                f"  {r['symbol']:<6} ${r['realized_end_equity']:>10,.0f} "
                f"{r['realized_roi_pct']:>+7.1f}% {r['realized_max_dd_pct']:>+7.1f}% "
                f"{r['wins']:>5}/{r['losses']:>5}/{r['zeros']:>3} "
                f"{r['n_trades']:>10} {sr_str:>8}"
            )
    print("=" * 110)
    return 0


if __name__ == "__main__":
    sys.exit(main())
