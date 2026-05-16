"""H062 C9 — BOCD-triggered Kelly step-up sweep.

Per Phase O.3 high-risk-strategist 3-agent assessment (2026-05-15), C9
operationalises the [ADR-0018](../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md)
D-3 (BOCD signal-decay monitor) + D-4 (switching-bandit redirect)
paradigm at the position-sizing layer:

  Start km = km_start (default 1.5).
  Every `step_check_interval_sessions` sessions, evaluate BOCD on the
  rolling per-session MPPM(ρ=1) path:
    - If `decay-detected-no` (BOCD max-posterior < threshold) on the
      most-recent window → STEP UP to the next km in the grid
      (1.5 → 2.0 → 2.5).
    - If `decay-detected-yes` (BOCD max-posterior >= threshold) → HALVE
      km (clamped at km_min).
  Apply the current km to every NEW position entry.

References:
  - Adams-MacKay 2007 ([arXiv 0710.3742](https://arxiv.org/abs/0710.3742))
    Bayesian Online Change-point Detection primitive at
    [src/skie_ninja/inference/bocd.py](../src/skie_ninja/inference/bocd.py)
    per `P1-BOCD-DECAY-DETECTOR-PRIMITIVE` (closed Phase L commit `40fb53d`).
  - Goetzmann-Ingersoll-Spiegel-Welch 2007 *RFS* 20(5):1503-1546
    MPPM(ρ=1) fitness primitive at
    [src/skie_ninja/inference/mppm.py](../src/skie_ninja/inference/mppm.py).
  - Garivier-Moulines 2011 *ALT* LNCS 6925:174-188 D-UCB switching-bandit
    framework (this C9 is the per-fold variant: per-arm Kelly adapts;
    no cross-arm allocation here — that's MPV1's domain).

Scope: this is a single-symbol experiment with per-symbol BOCD on the
per-session MPPM path. Multi-symbol basket level BOCD aggregation
deferred to v2 per `P1-C9-MULTI-SYMBOL-BOCD-AGGREGATE`.

Output: sidecar at ``artifacts/runs/H062/c9_bocd_step_up_<ts>/sidecar.json``
+ printed per-symbol comparison: C9 vs C3 baseline + v1 baseline.
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
from skie_ninja.inference.bocd import detect_decay
from skie_ninja.inference.mppm import mppm_rho_1

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h062_c9")


_MULTIPLIERS: dict[str, float] = {"ES": 50.0, "NQ": 20.0, "MGC": 10.0, "SIL": 1000.0}
_CAPACITY_CAPS: dict[str, int] = {"ES": 20, "NQ": 40, "MGC": 5, "SIL": 5}


@dataclass(frozen=True)
class C9Config:
    """C9 BOCD-step-up sizing configuration.

    Fields:
        km_grid: Tuple of Kelly multipliers in step-up order.
        km_start: Starting Kelly cell.
        risk_budget_pct: Per-trade fraction of bankroll at risk (1% default).
        step_check_interval_sessions: Sessions between BOCD evaluations
            (default 60 per Adams-MacKay 2007 §2.2 + H050 + H060 default).
        bocd_hazard_rate: BOCD hazard rate (default 0.01 = 1/100).
        bocd_window: BOCD window size in observations (default 60).
        bocd_threshold: Posterior threshold for decay detection (default 0.5).
        rolling_mppm_window: Window for rolling MPPM evaluation (default 60
            sessions per Goetzmann-Ingersoll-Spiegel-Welch 2007 §2 + project
            convention).
        delta_t: MPPM Δt for per-session input series (default 1/252).
    """
    km_grid: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 2.5)
    km_start: float = 1.5
    risk_budget_pct: float = 0.01
    step_check_interval_sessions: int = 60
    bocd_hazard_rate: float = 0.01
    bocd_window: int = 60
    bocd_threshold: float = 0.5
    rolling_mppm_window: int = 60
    delta_t: float = 1.0 / 252.0


class C9StateMachine:
    """Per-symbol BOCD-driven Kelly step-up state machine.

    Per Round-1 audit F-1 + F-2 fixes:
    - F-1: BOCD is fed a DENSE per-session MPPM(rho=1) path (one MPPM
      observation per session close), NOT a sparse subsample at every
      step-check. Adams-MacKay 2007 §2 requires the full sequential
      observation stream.
    - F-2: A warmup gate prevents step-ups during BOCD burn-in: the
      step-up rule requires (a) dense MPPM path length >= window AND
      (b) BOCD post-burn-in posterior has been computed on a window
      where the half-window-burn-in has cleared.
    - F-5: km step-up + halve both navigate the discrete km_grid via
      index (no off-grid arithmetic).
    """

    def __init__(self, cfg: C9Config):
        self.cfg = cfg
        self.km_idx = list(cfg.km_grid).index(cfg.km_start)
        self.km = cfg.km_grid[self.km_idx]
        self.session_log_returns: list[float] = []
        # F-1 fix: DENSE per-session MPPM path — one observation per session
        # close (not one per step-check).
        self.per_session_mppm_path: list[float] = []
        self.last_check_session_idx = 0
        self.step_history: list[dict[str, Any]] = []

    def on_session_close(
        self, session_log_ret: float, session_date: Any
    ) -> float:
        """Called at each session boundary. Returns current km."""
        self.session_log_returns.append(float(session_log_ret))
        # F-1 fix: append rolling MPPM at EVERY session close once enough
        # history exists, so BOCD operates on a dense sequential stream.
        w = self.cfg.rolling_mppm_window
        n = len(self.session_log_returns)
        if n >= w:
            window_returns = np.array(self.session_log_returns[-w:])
            try:
                mppm_val = float(mppm_rho_1(window_returns, delta_t=self.cfg.delta_t))
                if np.isfinite(mppm_val):
                    self.per_session_mppm_path.append(mppm_val)
            except (ValueError, FloatingPointError) as exc:
                _log.warning(
                    "mppm_rho_1 failed at session_idx=%d: %s; skipping",
                    n, exc,
                )
        # Step-check at the configured cadence.
        if (n - self.last_check_session_idx) >= self.cfg.step_check_interval_sessions:
            self.last_check_session_idx = n
            self._evaluate_bocd_and_step(session_date)
        return self.km

    def _evaluate_bocd_and_step(self, session_date: Any) -> None:
        """Run BOCD on dense per-session MPPM path; step km up or halve.

        Per Round-1 F-2 fix: warmup gate requires post-burn-in BOCD
        history before step-up actions can fire — prevents the warmup
        "absence of evidence treated as evidence of no decay" failure mode.
        """
        # F-2 warmup gate: do not act until dense MPPM path has length
        # >= bocd_window (so BOCD's half-window burn-in has cleared and
        # the posterior series has real data-driven content).
        if len(self.per_session_mppm_path) < self.cfg.bocd_window:
            self.step_history.append({
                "session_idx": len(self.session_log_returns),
                "session_date": str(session_date),
                "mppm_path_n": len(self.per_session_mppm_path),
                "decay_detected": None,
                "max_posterior": None,
                "km_prev": self.km,
                "km_new": self.km,
                "action": "warmup_hold",
            })
            return

        try:
            bocd_result = detect_decay(
                np.array(self.per_session_mppm_path),
                hazard_rate=self.cfg.bocd_hazard_rate,
                window=self.cfg.bocd_window,
                threshold=self.cfg.bocd_threshold,
            )
        except Exception as exc:  # noqa: BLE001
            _log.warning(
                "detect_decay failed at session_idx=%d (mppm_path_n=%d): %s",
                len(self.session_log_returns),
                len(self.per_session_mppm_path),
                exc,
            )
            return

        decay_detected = bool(bocd_result.get("decay_detected", False))
        prev_km = self.km
        prev_km_idx = self.km_idx
        # F-5 fix: both step-up and halve navigate km_grid via index
        if decay_detected:
            new_idx = max(self.km_idx - 1, 0)
            action = "halve" if new_idx < self.km_idx else "hold_min"
        else:
            new_idx = min(self.km_idx + 1, len(self.cfg.km_grid) - 1)
            action = "step_up" if new_idx > self.km_idx else "hold_max"
        self.km_idx = new_idx
        self.km = self.cfg.km_grid[self.km_idx]

        self.step_history.append({
            "session_idx": len(self.session_log_returns),
            "session_date": str(session_date),
            "mppm_path_n": len(self.per_session_mppm_path),
            "mppm_window": float(self.per_session_mppm_path[-1]),
            "decay_detected": decay_detected,
            "max_posterior": (
                float(bocd_result.get("max_posterior", 0.0))
                if bocd_result.get("max_posterior") is not None
                else None
            ),
            "km_prev": prev_km,
            "km_prev_idx": prev_km_idx,
            "km_new": self.km,
            "km_new_idx": self.km_idx,
            "action": action,
        })


def _load_5min_bars(
    substrate_root: Path,
    symbol: str,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    glob_pat = str(substrate_root / f"symbol={symbol}" / "year=*" / "part-*.parquet")
    lf = pl.scan_parquet(glob_pat).select(
        pl.col("ts_event"), pl.col("open"), pl.col("high"),
        pl.col("low"), pl.col("close"),
    )
    df = lf.collect().to_pandas()
    if df.empty:
        raise RuntimeError(f"{symbol}: empty substrate at {glob_pat}")
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df = df.sort_values("ts_event").reset_index(drop=True)
    mask = (df["ts_event"] >= start) & (df["ts_event"] <= end)
    df = df.loc[mask].copy()
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


def _run_c9_simulation(
    *,
    symbol: str,
    df_5m: pd.DataFrame,
    feature_config: H062FeatureConfig,
    k_atr: float,
    c9_cfg: C9Config,
    starting_equity: float = 10000.0,
    eod_flatten_minutes_from_open: int = 360,
) -> dict[str, Any]:
    """C9 per-trade simulator with BOCD-driven km adaptation."""
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

    sm = C9StateMachine(c9_cfg)
    equity = starting_equity
    trades: list[dict[str, Any]] = []
    per_session_log_returns: dict[Any, float] = {}

    # Session-start map.
    session_starts: dict[Any, int] = {}
    for t in range(n_bars):
        sd = session_dates[t]
        if sd not in session_starts:
            session_starts[sd] = t

    # F-6 fix: km_at_entry is closure-state, not function-attribute. This
    # ensures per-trade audit-trail correctness: the recorded km matches
    # the km in effect AT THE TIME OF ENTRY, not the most-recent km.
    in_position = False
    pos_side = 0
    entry_price = np.nan
    stop_price = np.nan
    r_dollar = np.nan
    position_size = 0
    entry_session = None
    km_at_entry = c9_cfg.km_start

    def _close_position(exit_price: float, reason: str) -> None:
        nonlocal in_position, pos_side, entry_price, stop_price, r_dollar
        nonlocal position_size, entry_session, km_at_entry, equity
        if not in_position:
            return
        pnl_dollar = pos_side * (exit_price - entry_price) * multiplier * position_size
        r_mult = pnl_dollar / r_dollar if r_dollar > 0 else 0.0
        # Equity-level log return contribution
        if equity > 0 and equity + pnl_dollar > 0:
            log_ret = float(np.log((equity + pnl_dollar) / equity))
        else:
            log_ret = 0.0
        equity += pnl_dollar
        # F-4 partial fix: same-session entry/exit accumulation per GISW 2007
        # §II per-period convention. EOD-flatten + session-rollover enforce
        # same-session close by construction at this cadence.
        per_session_log_returns[entry_session] = (
            per_session_log_returns.get(entry_session, 0.0) + log_ret
        )
        trades.append({
            "side": pos_side, "entry_price": float(entry_price),
            "exit_price": float(exit_price), "pnl_dollar": float(pnl_dollar),
            "r_multiple": float(r_mult), "exit_reason": reason,
            "entry_session": entry_session, "size": position_size,
            "km_at_entry": float(km_at_entry),  # F-6 fix: closure state, not function attribute
            "equity_post": float(equity),
        })
        in_position = False
        pos_side = 0
        entry_price = np.nan
        stop_price = np.nan
        r_dollar = np.nan
        position_size = 0
        entry_session = None

    last_session = None
    for t in range(n_bars - 1):
        bar_session = session_dates[t]
        # Session boundary handler — feed accumulated session log return to BOCD
        if last_session is not None and bar_session != last_session:
            sess_lr = per_session_log_returns.get(last_session, 0.0)
            sm.on_session_close(sess_lr, last_session)
        last_session = bar_session

        if in_position:
            # Stop / opposite-channel / EOD checks
            if pos_side == 1:
                if open_[t] < stop_price:
                    _close_position(float(open_[t]), "gap_through_stop_long")
                    continue
                if low[t] <= stop_price:
                    _close_position(float(stop_price), "stop_hit_long")
                    continue
                if feats.filtered_events[t] == -1:
                    _close_position(float(close[t]), "opposite_channel_break")
                    continue
            else:
                if open_[t] > stop_price:
                    _close_position(float(open_[t]), "gap_through_stop_short")
                    continue
                if high[t] >= stop_price:
                    _close_position(float(stop_price), "stop_hit_short")
                    continue
                if feats.filtered_events[t] == 1:
                    _close_position(float(close[t]), "opposite_channel_break")
                    continue
            session_open_idx = session_starts.get(bar_session, t)
            if (t - session_open_idx) >= eod_flatten_minutes_from_open:
                _close_position(float(close[t]), "eod_flatten")
                continue
            if t + 1 < n_bars and session_dates[t + 1] != bar_session:
                _close_position(float(close[t]), "session_rollover")
                continue

        # Entry?
        ev = int(feats.eligible_events[t])
        if not in_position and ev != 0:
            entry_idx = t + 1
            if entry_idx >= n_bars:
                continue
            entry_p = float(open_[entry_idx])
            atr_t = float(feats.atr[t])
            if not np.isfinite(atr_t) or atr_t <= 0:
                continue
            dollar_1r = k_atr * atr_t * multiplier
            if dollar_1r <= 0:
                continue
            current_km = sm.km
            effective_risk_pct = current_km * c9_cfg.risk_budget_pct
            target_risk = effective_risk_pct * equity
            size = int(np.floor(min(target_risk / dollar_1r, cap)))
            if size < 1:
                continue
            in_position = True
            pos_side = ev
            entry_price = entry_p
            stop_price = entry_p - ev * (k_atr * atr_t)
            r_dollar = dollar_1r * size
            position_size = size
            entry_session = bar_session
            # F-6 fix: capture km in closure-state at entry time
            km_at_entry = current_km

    # Final close
    if last_session is not None:
        sess_lr = per_session_log_returns.get(last_session, 0.0)
        sm.on_session_close(sess_lr, last_session)
    if in_position:
        _close_position(float(close[-1]), "end_of_data")

    # Aggregate metrics
    n_trades = len(trades)
    pnls = np.array([t["pnl_dollar"] for t in trades])
    r_mults = np.array([t["r_multiple"] for t in trades])
    realized_end = equity
    # Equity curve from trades
    eq_curve = [starting_equity]
    eq = starting_equity
    for t in trades:
        eq = t["equity_post"]
        eq_curve.append(eq)
    eq_arr = np.array(eq_curve)
    running_max = np.maximum.accumulate(eq_arr)
    dd = (eq_arr - running_max) / running_max
    max_dd = float(-dd.min()) if dd.size > 0 else 0.0

    return {
        "symbol": symbol,
        "n_trades": n_trades,
        "realized_end_equity": realized_end,
        "realized_roi_pct": (realized_end / starting_equity - 1.0) * 100,
        "realized_max_dd_pct": max_dd * 100,
        "wins": int((pnls > 0).sum()),
        "losses": int((pnls < 0).sum()),
        "zeros": int((pnls == 0).sum()),
        "r_multiple_mean": float(r_mults.mean()) if r_mults.size else 0.0,
        "km_step_history": sm.step_history,
        "km_terminal": sm.km,
        "n_km_step_ups": sum(1 for h in sm.step_history if h["action"] == "step_up"),
        "n_km_halves": sum(1 for h in sm.step_history if h["action"] == "halve"),
        "n_km_holds_max": sum(1 for h in sm.step_history if h["action"] == "hold_max"),
        "per_session_mppm_path": sm.per_session_mppm_path,
        "per_session_log_returns": dict(per_session_log_returns),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H062 C9 BOCD-step-up sweep")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--symbols", nargs="*", default=["ES", "NQ", "MGC", "SIL"])
    parser.add_argument("--km-start", type=float, default=1.5)
    parser.add_argument("--bocd-hazard-rate", type=float, default=0.01)
    parser.add_argument("--bocd-threshold", type=float, default=0.5)
    parser.add_argument("--step-check-interval-sessions", type=int, default=60)
    args = parser.parse_args(argv)

    if args.substrate_path:
        substrate_root = Path(args.substrate_path).resolve()
    else:
        substrate_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"

    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else _REPO_ROOT / "artifacts" / "runs" / "H062"
            / f"c9_bocd_step_up_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    start = pd.Timestamp("2020-01-01", tz="UTC")
    end_per_symbol = {
        "ES": pd.Timestamp("2025-12-03", tz="UTC"),
        "NQ": pd.Timestamp("2024-12-19", tz="UTC"),
        "MGC": pd.Timestamp("2025-12-30", tz="UTC"),
        "SIL": pd.Timestamp("2025-12-30", tz="UTC"),
    }

    feat_cfg = H062FeatureConfig(
        channel_n=120, atr_n=14, h_dwell=5,
        trend_id="a_ts_mom", trend_id_lookback_l=60, trend_id_threshold=1.0,
    )
    k_atr = 2.0
    c9_cfg = C9Config(
        km_grid=(0.5, 1.0, 1.5, 2.0, 2.5),
        km_start=args.km_start,
        risk_budget_pct=0.01,
        step_check_interval_sessions=args.step_check_interval_sessions,
        bocd_hazard_rate=args.bocd_hazard_rate,
        bocd_threshold=args.bocd_threshold,
    )

    results: list[dict[str, Any]] = []
    for sym in args.symbols:
        sym_end = end_per_symbol.get(sym, pd.Timestamp("2025-12-30", tz="UTC"))
        _log.info("Loading %s [%s → %s]", sym, start.date(), sym_end.date())
        df_5m = _load_5min_bars(substrate_root, sym, start=start, end=sym_end)
        _log.info("  %s: %d 5-min bars (%d sessions)",
                  sym, len(df_5m), df_5m["session_date_et"].nunique())
        res = _run_c9_simulation(
            symbol=sym, df_5m=df_5m, feature_config=feat_cfg, k_atr=k_atr,
            c9_cfg=c9_cfg,
        )
        results.append(res)
        _log.info(
            "  %s: end=$%.0f (%+.1f%%) MaxDD=%.1f%% W/L/Z=%d/%d/%d trades=%d  km_step_ups=%d km_halves=%d km_terminal=%.2f",
            sym, res["realized_end_equity"], res["realized_roi_pct"],
            res["realized_max_dd_pct"], res["wins"], res["losses"], res["zeros"],
            res["n_trades"], res["n_km_step_ups"], res["n_km_halves"], res["km_terminal"],
        )

    basket_end = sum(r["realized_end_equity"] for r in results)
    basket_start = 10000.0 * len(results)
    basket_roi = (basket_end / basket_start - 1.0) * 100

    payload = {
        "experiment": "c9_bocd_step_up",
        "config": {
            "km_grid": list(c9_cfg.km_grid),
            "km_start": c9_cfg.km_start,
            "risk_budget_pct": c9_cfg.risk_budget_pct,
            "step_check_interval_sessions": c9_cfg.step_check_interval_sessions,
            "bocd_hazard_rate": c9_cfg.bocd_hazard_rate,
            "bocd_window": c9_cfg.bocd_window,
            "bocd_threshold": c9_cfg.bocd_threshold,
            "rolling_mppm_window": c9_cfg.rolling_mppm_window,
        },
        "feature_cell": {
            "channel_n": 120, "atr_n": 14, "h_dwell": 5,
            "trend_id": "a_ts_mom", "trend_id_lookback_l": 60,
            "trend_id_threshold": 1.0, "k_atr": k_atr,
        },
        "per_symbol": [
            {k: v for k, v in r.items()
             if k not in ["per_session_log_returns", "per_session_mppm_path"]}
            | {"per_session_mppm_n": len(r["per_session_mppm_path"])}
            for r in results
        ],
        "basket": {
            "starting_equity_total": basket_start,
            "end_equity_total": basket_end,
            "roi_pct": basket_roi,
        },
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])

    print()
    print("=" * 100)
    print("H062 C9 BOCD-STEP-UP — FULL 2020-2025 IS+OOS WINDOW")
    print(f"  km_grid={c9_cfg.km_grid}  km_start={c9_cfg.km_start}")
    print(f"  bocd: hazard_rate={c9_cfg.bocd_hazard_rate}, window={c9_cfg.bocd_window}, threshold={c9_cfg.bocd_threshold}")
    print(f"  step_check_interval_sessions={c9_cfg.step_check_interval_sessions}")
    print("=" * 100)
    print(f"{'symbol':<6} {'end_eq':>12} {'roi':>9} {'maxDD':>9} {'trades':>8} {'step_ups':>9} {'halves':>8} {'km_term':>8}")
    for r in results:
        print(
            f"{r['symbol']:<6} ${r['realized_end_equity']:>10,.0f} {r['realized_roi_pct']:>+7.1f}% "
            f"{r['realized_max_dd_pct']:>+7.1f}% {r['n_trades']:>8} "
            f"{r['n_km_step_ups']:>9} {r['n_km_halves']:>8} {r['km_terminal']:>+7.2f}"
        )
    print(f"BASKET ${basket_end:>10,.0f} {basket_roi:>+7.1f}% (vs C3 +2,690%; v1 -3.7%)")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
