"""H055 v2 — aggressive-sizing sweep on wick-rejection mean-reversion scalping.

Per operator 2026-05-15 directive ("Implement and run H055 v2 ... 5-config
sweep on wick-rejection setup signals; emit single KPI metrics table;
FULL OOS + 2026-04-01→2026-05-15 sub-window"), this script realises the
ADR-0017 + ADR-0018 + ADR-0024 high-risk-Kelly framework on top of the
H055 design.md §3 wick-rejection setup detectors (swing-pivot +
wick-reversal-non-swing per the H055 feature factory at
[src/skie_ninja/features/h055/](../src/skie_ninja/features/h055/)).

Structural template inheritance
-------------------------------

This script is a focused descendant of two prior simulators:
1. [scripts/run_h062_aggressive_sizing_sweep.py](run_h062_aggressive_sizing_sweep.py)
   — per-trade simulator with current-equity rebase + Kelly grid +
   Turtle-2 pyramiding (the structural skeleton for the per-trade
   evolution loop, K-3/K-4/K-6/K-7 kill switches, and configuration
   sweep tables).
2. [scripts/run_h062_c9_bocd_step_up.py](run_h062_c9_bocd_step_up.py)
   — BOCD-driven Kelly step-up state machine (the dense per-session
   MPPM construction + warmup gate + grid-consistent km navigation,
   per Round-1 audit C9-F-1 + F-2 + F-5 fixes 2026-05-15).

The H062 simulators evaluate channel-break entries; this H055 v2
simulator swaps the entry-signal generator to the H055 wick-rejection
setup family (`detect_wick_reversal_setups` + `detect_swing_pivot_setups`)
while preserving the same sizing + pyramiding + kill-switch architecture.

Exit rules (H055-design.md §4 + ADR-0017 §5)
--------------------------------------------

- **TP/SL**: ATR-scaled per setup: TP = entry ± α·ATR; SL = entry ∓ β·ATR.
- **Stop-loss hit on bar t**: close position at stop_price; reason=stop_hit.
- **Gap-through stop on bar-t open**: open beyond stop → close at open_t;
  reason=gap_through_stop (worst-case fill convention; pessimistic per
  López de Prado *AFML* §13.2 *practitioner*).
- **TP hit on bar t**: close at tp_price; reason=tp_hit.
- **Same-bar TP+SL**: pessimistic-fill convention → SL fills first.
- **EOD-flatten**: 15:55 ET hard close per H055 design.md §4 (subsumed
  by K-2 time-stop in the limit; retained as safety net).
- **Session-rollover**: any held position is flattened at session boundary.
- **K-6 daily breaker**: cease entries at -2% intra-session realized P/L.
- **K-7 weekly breaker**: cease entries at -5% intra-week realized P/L.

Sweep configurations (5 cells)
------------------------------

  v1     (baseline):     Kelly=0.25, risk=1%, FIXED-equity ($10K),
                         no pyramid, no BOCD
  C2     (full-Kelly):    Kelly=1.0,  risk=1%, current-equity rebase,
                         no pyramid, no BOCD
  C3     (super-Kelly):   Kelly=2.0,  risk=1%, current-equity rebase,
                         no pyramid, no BOCD
  C9     (BOCD-step-up):  Kelly start=1.5, grid {0.5..2.5},
                         risk=1%, current-equity rebase, no pyramid,
                         BOCD-driven step-up on dense per-session MPPM
  C5     (super-Kelly + pyramid): Kelly=2.0, risk=1%, current-equity
                         rebase, Turtle-2 pyramid (max 4 units; 1N
                         spacing), no BOCD

Per ADR-0017 §1 + ADR-0018 D-2 + ADR-0024:
- v1 is the baseline (NOT the "production v2"); it's preserved for the
  KPI metrics table operator-comparison row.
- C2/C3/C5 are aggressive-growth variants per ADR-0018.
- C9 is the BOCD-adaptive variant per ADR-0018 D-3 + D-4.

Output
------

- Per-symbol × per-config sweep_sidecar.json under
  ``artifacts/runs/H055/v2_sweep_<ts>/``.
- KPI metrics table printed to stdout AND written to KPI report card
  ``research/01_hypothesis_register/H055/H055_kpi_report_v1.md`` per
  ADR-0014 §3.2 13-table format.

Two reporting windows per configuration:
- FULL OOS = 2024-01-01 → 2026-05-15 (substrate right-edge)
- 2026-04-01 → 2026-05-15 SUB-WINDOW (recent realized OOS)

References
----------

- H055 design.md frozen pre-reg at `status: designed` 2026-05-06;
  this v2 sweep is research-only (operator-discretionary upon
  KPI-report presentation per ADR-0013 §1).
- Faith 2007 *Way of the Turtle* ISBN 978-0071486644 §4 (*practitioner*)
  pyramiding convention.
- Goetzmann-Ingersoll-Spiegel-Welch 2007 *RFS* 20(5):1503-1546
  DOI 10.1093/rfs/hhm025 MPPM(rho=1) primary fitness per ADR-0018 D-1.
- Adams-MacKay 2007 arXiv:0710.3742 BOCD primitive per ADR-0018 D-3.
- ADR-0017 §4.1 current-equity rebase + §5 K-1..K-8 kill switches.
- ADR-0024 (paradigm resolution) high-risk-Kelly canonical 2026-05-15.

Audit-remediate-loop discipline per Phase O.4 precedent
[docs/audits/audit_trail_2026-05-15_mpv1_c9_round1.md](../docs/audits/audit_trail_2026-05-15_mpv1_c9_round1.md).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
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

from skie_ninja.features.h055 import (
    H055FeatureConfig,
    compute_h055_features,
    emit_h055_setups,
)
from skie_ninja.inference.bocd import detect_decay
from skie_ninja.inference.calmar import (
    calmar_ratio,
    max_drawdown_fraction,
)
from skie_ninja.inference.mppm import mppm_rho_1
from skie_ninja.inference.profit_factor import profit_factor
from skie_ninja.inference.skewness import (
    l_skewness_tau3,
    payoff_shape_annotation,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h055_v2_sweep")


# CME front-month futures multipliers (USD per point) per
# [config/instruments.yaml](../config/instruments.yaml).
_MULTIPLIERS: dict[str, float] = {
    "ES": 50.0,   # E-mini S&P 500 ($50 per point)
    "NQ": 20.0,   # E-mini Nasdaq-100 ($20 per point)
    "MGC": 10.0,  # Micro Gold (10 troy oz × $1/$0.10 = $10 per $1 move)
    "SIL": 1000.0,  # Micro Silver (1000 troy oz × $1 = $1000 per $1 move)
}

# Per ADR-0001 retail-tier capacity ceilings + sibling micro mapping.
# {MGC, SIL} ceilings are operational placeholders; calibrated against
# post-paper-trade fill data under `P1-ADR-0001-METALS-ENERGY-CAPACITY-CALIBRATE`.
_CAPACITY_CAPS: dict[str, int] = {
    "ES": 20, "NQ": 40, "MGC": 5, "SIL": 5,
}


# ────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SweepConfig:
    """H055 v2 sizing configuration cell.

    Fields:
        name: short cell-label for the results table.
        kelly_multiplier: Kelly-fraction scalar per ADR-0018 D-2.
        risk_budget_pct: per-trade fraction-of-bankroll on 1R-stop scale
            (default 0.01 = 1% Turtle convention per Faith 2007 *practitioner*).
        use_current_equity_rebase: per ADR-0017 §4.1 — True rebases on
            current equity; False is v1-baseline fixed $10K.
        enable_pyramiding: Faith 2007 §4 Turtle System 2 pyramid; max
            `pyramid_max_units` at `pyramid_step_atr` × ATR spacing.
        enable_bocd: enables BOCD-driven Kelly-multiplier step-up state
            machine per ADR-0018 D-3 + D-4. When True, `kelly_multiplier`
            is the *starting* km; the state machine moves through the
            km_grid per session-boundary BOCD decisions.
        description: human-readable description for sidecar provenance.
    """

    name: str
    kelly_multiplier: float
    risk_budget_pct: float
    use_current_equity_rebase: bool
    enable_pyramiding: bool
    pyramid_max_units: int
    pyramid_step_atr: float
    enable_bocd: bool
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
        enable_bocd=False,
        description="v1 baseline (quarter-Kelly, fixed $10K rebase, no pyramid)",
    ),
    SweepConfig(
        name="C2_fullkelly",
        kelly_multiplier=1.0,
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        enable_pyramiding=False,
        pyramid_max_units=1,
        pyramid_step_atr=0.0,
        enable_bocd=False,
        description="C2: full-Kelly (km=1.0) + current-equity rebase",
    ),
    SweepConfig(
        name="C3_superkelly",
        kelly_multiplier=2.0,
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        enable_pyramiding=False,
        pyramid_max_units=1,
        pyramid_step_atr=0.0,
        enable_bocd=False,
        description="C3: super-Kelly km=2.0 + current-equity rebase",
    ),
    SweepConfig(
        name="C9_bocd_stepup",
        kelly_multiplier=1.5,  # starting km for BOCD state machine
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        enable_pyramiding=False,
        pyramid_max_units=1,
        pyramid_step_atr=0.0,
        enable_bocd=True,
        description="C9: BOCD-step-up (km_grid={0.5..2.5}; start=1.5; hazard=1/100)",
    ),
    SweepConfig(
        name="C5_super_pyramid",
        kelly_multiplier=2.0,
        risk_budget_pct=0.01,
        use_current_equity_rebase=True,
        enable_pyramiding=True,
        pyramid_max_units=4,
        pyramid_step_atr=1.0,
        enable_bocd=False,
        description="C5: super-Kelly km=2.0 + rebase + Turtle-2 pyramid (max 4; 1N)",
    ),
]


# BOCD state machine config (km_grid follows ADR-0018 D-2 grid {0.25..2.5}
# but C9 uses the dense {0.5, 1.0, 1.5, 2.0, 2.5} sub-grid per Phase O.4
# C9 reference implementation — these 5 cells are evenly spaced for
# unambiguous km_idx navigation).
@dataclass(frozen=True)
class BOCDConfig:
    """C9 BOCD-state-machine hyperparameters per ADR-0018 D-3.

    Per Phase O.4 Round-1 audit C9-F-1 + C9-F-2 fixes:
    - BOCD input is a DENSE per-session MPPM(rho=1) sequence (one value
      per session close), NOT a sparse subsample at step-check cadence.
    - Warmup gate blocks km step-ups until len(mppm_path) >= bocd_window
      (so BOCD's half-window burn-in has cleared).
    """

    km_grid: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 2.5)
    step_check_interval_sessions: int = 60  # H050+H060 default
    bocd_hazard_rate: float = 0.01  # ADR-0018 D-3 default 1/100
    bocd_window: int = 60  # Adams-MacKay 2007 §2.2 default
    bocd_threshold: float = 0.5  # ADR-0018 D-3 default
    rolling_mppm_window: int = 60  # GISW 2007 §2 + project convention


# ────────────────────────────────────────────────────────────────────────────
# C9 BOCD state machine (per-symbol)
# ────────────────────────────────────────────────────────────────────────────


class C9StateMachine:
    """Per-symbol BOCD-driven Kelly step-up state machine.

    Per Phase O.4 Round-1 audit C9-F-1 + F-2 + F-5 fixes:
    - F-1: BOCD is fed a DENSE per-session MPPM(rho=1) path.
    - F-2: Warmup gate prevents step-ups during BOCD burn-in.
    - F-5: km step-up + halve both navigate the discrete km_grid via index.
    """

    def __init__(self, km_start: float, cfg: BOCDConfig):
        try:
            self.km_idx = list(cfg.km_grid).index(km_start)
        except ValueError as exc:
            raise ValueError(
                f"km_start {km_start} must be a grid cell of {cfg.km_grid}"
            ) from exc
        self.cfg = cfg
        self.km = cfg.km_grid[self.km_idx]
        self.session_log_returns: list[float] = []
        # DENSE per-session MPPM path — append at every session close (per F-1)
        self.per_session_mppm_path: list[float] = []
        self.last_check_session_idx = 0
        self.step_history: list[dict[str, Any]] = []

    def on_session_close(self, session_arith_ret: float, session_date: Any) -> float:
        """Called at each session boundary. Returns current km.

        Args:
            session_arith_ret: per-session ARITHMETIC return r_t such that
                (1 + r_t) > 0 (matches mppm_rho_1 input contract per GISW 2007
                Theorem 1 + project F-1-9 audit fix 2026-05-15). Caller MUST
                pass arithmetic returns, NOT log returns.
            session_date: dating tag for step-history audit trail.
        """
        # Clamp at -0.99 to avoid (1 + r) <= 0 ruin event signaling NaN
        clamped = max(-0.99, float(session_arith_ret))
        self.session_log_returns.append(clamped)
        # F-1: append rolling MPPM at every session close once enough history.
        w = self.cfg.rolling_mppm_window
        n = len(self.session_log_returns)
        if n >= w:
            window_returns = np.array(self.session_log_returns[-w:])
            try:
                mppm_val = float(mppm_rho_1(window_returns, delta_t=1.0 / 252.0))
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
        """Run BOCD on dense per-session MPPM path; step km up or halve."""
        # F-2 warmup gate.
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
        # F-5: both step-up + halve navigate km_grid via index
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
            "mppm_window_last": float(self.per_session_mppm_path[-1]),
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


# ────────────────────────────────────────────────────────────────────────────
# Substrate loading
# ────────────────────────────────────────────────────────────────────────────


def _load_5min_bars(
    substrate_root: Path,
    symbol: str,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Load 1-min substrate for `symbol` over [start, end] and resample to 5-min.

    Returns a DataFrame with columns ts_event, open, high, low, close,
    session_date_et. 5-min resampling label='right' closed='right' matches
    the H062 sweep convention so wall-clock comparability is preserved.
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
    mask = (df["ts_event"] >= start) & (df["ts_event"] <= end)
    df = df.loc[mask].copy()
    if df.empty:
        raise RuntimeError(f"{symbol}: substrate empty after filter [{start}, {end}]")
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


# ────────────────────────────────────────────────────────────────────────────
# Per-trade simulator with sweep-config-driven sizing
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class _Position:
    """In-position state. Supports pyramiding via the `units` list."""
    side: int  # +1 long, -1 short
    units: list[dict[str, Any]]  # each {entry_price, size, stop_price, tp_price, r_dollar, entry_idx}
    entry_session_date: Any
    km_at_entry: float  # Kelly multiplier in force at entry (closure-state per C9-F-6)


def _run_simulation(
    *,
    symbol: str,
    df_5m: pd.DataFrame,
    feature_config: H055FeatureConfig,
    setups: list,
    setup_idx_by_bar: dict[int, list],
    cfg: SweepConfig,
    bocd_cfg: BOCDConfig,
    starting_equity: float = 10000.0,
    alpha_tp_mult: float = 2.0,  # H055 design.md §5.6 mid-grid
    beta_sl_mult: float = 1.5,    # H055 design.md §5.6 mid-grid
    k_swing_bars: int = 30,       # in 5-min bars = 2.5 hours
    k_atr_stop: float | None = None,
    rho_star: float = 0.0,        # PLACEHOLDER pending P1-H055-CALIBRATION-HOLDOUT-RUN
    daily_loss_breaker_pct: float = -0.02,   # K-6
    weekly_loss_breaker_pct: float = -0.05,  # K-7
) -> dict[str, Any]:
    """Run the per-trade simulator for one (symbol, config) cell.

    Walks 5-min bars chronologically; at each bar:
      1. Check any open position for stop / TP / time-stop / EOD / rollover.
      2. If pyramiding enabled (C5), check for favorable +1N move on
         most-recent unit's entry; add unit if eligible.
      3. If flat AND any new setup confirms at this bar AND passes gates,
         enter on bar t+1 open (PIT-safe causal fill).

    Returns a dict of realized + projected metrics for the cell.
    """
    high = df_5m["high"].to_numpy()
    low = df_5m["low"].to_numpy()
    close = df_5m["close"].to_numpy()
    open_ = df_5m["open"].to_numpy()
    session_dates = df_5m["session_date_et"].to_numpy()
    ts_event = df_5m["ts_event"].to_numpy()
    n_bars = len(df_5m)

    multiplier = _MULTIPLIERS.get(symbol, 1.0)
    cap = _CAPACITY_CAPS.get(symbol, 1)

    # Session-start map for EOD-flatten calculation.
    session_starts: dict[Any, int] = {}
    for t in range(n_bars):
        sd = session_dates[t]
        if sd not in session_starts:
            session_starts[sd] = t

    # K-7 weekly breaker: track per-ISO-week realized P/L.
    def _iso_week(sd: Any) -> tuple[int, int]:
        if hasattr(sd, "isocalendar"):
            iso = sd.isocalendar()
            return (iso[0], iso[1])
        return (0, 0)

    # ── State ──
    equity = starting_equity
    starting_equity_for_pct_calc = starting_equity
    position: _Position | None = None
    trades: list[dict[str, Any]] = []
    equity_curve: list[float] = [starting_equity]
    equity_curve_dates: list[Any] = []
    n_ruin_events = 0
    per_session_pnl: dict[Any, float] = {}
    per_week_pnl: dict[tuple[int, int], float] = {}

    # BOCD state machine for C9.
    sm: C9StateMachine | None = None
    if cfg.enable_bocd:
        sm = C9StateMachine(km_start=cfg.kelly_multiplier, cfg=bocd_cfg)

    last_session = None
    breaker_state_session: Any = None
    breaker_session_active = False
    breaker_state_week: tuple[int, int] = (0, 0)
    breaker_week_active = False

    def _close_all_units(
        exit_idx: int,
        exit_price: float,
        reason: str,
    ) -> None:
        """Close every unit in the current position at `exit_price`."""
        nonlocal position, equity, n_ruin_events
        if position is None:
            return
        total_pnl = 0.0
        total_r_dollar = 0.0
        for u in position.units:
            unit_pnl = position.side * (exit_price - u["entry_price"]) * multiplier * u["size"]
            total_pnl += unit_pnl
            total_r_dollar += u["r_dollar"]
        r_mult = total_pnl / total_r_dollar if total_r_dollar > 0 else 0.0
        equity += total_pnl
        # K-6/K-7 P/L accumulation.
        sd = position.entry_session_date
        per_session_pnl[sd] = per_session_pnl.get(sd, 0.0) + total_pnl
        wk = _iso_week(sd)
        per_week_pnl[wk] = per_week_pnl.get(wk, 0.0) + total_pnl

        equity_curve.append(equity)
        equity_curve_dates.append(position.entry_session_date)
        trades.append({
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
            "entry_session_date": str(position.entry_session_date),
            "exit_idx": int(exit_idx),
            "equity_post_trade": float(equity),
            "km_at_entry": float(position.km_at_entry),
        })
        if equity < 0.5 * starting_equity_for_pct_calc:
            n_ruin_events += 1
        position = None

    def _check_position_exits(t: int) -> bool:
        """Returns True if position closed at bar t."""
        nonlocal position
        if position is None:
            return False
        bar_session = session_dates[t]
        unit_stops = [u["stop_price"] for u in position.units]
        unit_tps = [u["tp_price"] for u in position.units]
        # Stop-loss: worst stop per side (tightest = least slack)
        if position.side == 1:
            worst_stop = max(unit_stops)
            best_tp = min(unit_tps)  # nearest TP for long
            # Gap-through stop
            if open_[t] < worst_stop:
                _close_all_units(t, float(open_[t]), "gap_through_stop_long")
                return True
            # Stop hit intrabar
            if low[t] <= worst_stop:
                # Pessimistic-fill (AFML §13.2): SL wins on same-bar collision
                _close_all_units(t, float(worst_stop), "stop_hit_long")
                return True
            # TP hit intrabar (no stop)
            if high[t] >= best_tp:
                _close_all_units(t, float(best_tp), "tp_hit_long")
                return True
        else:  # short
            worst_stop = min(unit_stops)
            best_tp = max(unit_tps)
            if open_[t] > worst_stop:
                _close_all_units(t, float(open_[t]), "gap_through_stop_short")
                return True
            if high[t] >= worst_stop:
                _close_all_units(t, float(worst_stop), "stop_hit_short")
                return True
            if low[t] <= best_tp:
                _close_all_units(t, float(best_tp), "tp_hit_short")
                return True
        # Time-stop: closing oldest unit's age
        oldest = min(u["entry_idx"] for u in position.units)
        if (t - oldest) >= k_swing_bars:
            _close_all_units(t, float(close[t]), "time_stop")
            return True
        # EOD-flatten (H055 design.md §4 hard close 15:55 ET ≈ 360 min into RTH)
        session_open_idx = session_starts.get(bar_session, t)
        # Use a 72 × 5-min-bar window from session open as 6 hr proxy
        # (RTH session = 6.5 hr; 78 5-min bars).
        if (t - session_open_idx) >= 78:
            _close_all_units(t, float(close[t]), "eod_flatten")
            return True
        # Session rollover
        if t + 1 < n_bars and session_dates[t + 1] != bar_session:
            _close_all_units(t, float(close[t]), "session_rollover")
            return True
        return False

    def _try_pyramid(t: int, atr_t: float) -> None:
        """Try to add a new unit on favorable +1N move (Faith 2007 §4)."""
        nonlocal position
        if position is None or not cfg.enable_pyramiding:
            return
        if len(position.units) >= cfg.pyramid_max_units:
            return
        if not np.isfinite(atr_t) or atr_t <= 0:
            return
        last_unit = position.units[-1]
        last_entry = last_unit["entry_price"]
        spacing = cfg.pyramid_step_atr * atr_t
        favorable = (
            (position.side == 1 and close[t] > last_entry + spacing)
            or (position.side == -1 and close[t] < last_entry - spacing)
        )
        if not favorable:
            return
        entry_price = float(close[t])
        beta_dollars_per_contract = beta_sl_mult * atr_t * multiplier
        if beta_dollars_per_contract <= 0:
            return
        # Per Faith 2007 §4: each unit sized at full risk budget.
        eq_for_sizing = equity if cfg.use_current_equity_rebase else starting_equity_for_pct_calc
        # K-1: per-trade $-stop = position-side × beta_sl × ATR (1.0R convention)
        # Per ADR-0018 D-2 + ADR-0017 §4.1: effective_risk = kelly_multiplier × risk_budget_pct.
        # For C9 use the state machine's current km; else use the static config value.
        current_km = sm.km if (sm is not None) else cfg.kelly_multiplier
        effective_risk_pct = current_km * cfg.risk_budget_pct
        per_unit_dollar_risk = effective_risk_pct * eq_for_sizing
        size_from_risk = per_unit_dollar_risk / beta_dollars_per_contract
        size = int(np.floor(size_from_risk))
        total_existing = sum(u["size"] for u in position.units)
        size = min(size, cap - total_existing)
        if size < 1:
            return
        stop_price = entry_price - position.side * (beta_sl_mult * atr_t)
        tp_price = entry_price + position.side * (alpha_tp_mult * atr_t)
        position.units.append({
            "entry_price": entry_price,
            "size": size,
            "stop_price": stop_price,
            "tp_price": tp_price,
            "entry_idx": t,
            "r_dollar": beta_dollars_per_contract * size,
        })

    def _try_new_entry_from_setup(t: int) -> None:
        """Try to open a flat→position entry on any setup confirmed at bar t."""
        nonlocal position
        if position is not None:
            return
        bar_session = session_dates[t]

        # K-6 daily breaker
        nonlocal breaker_state_session, breaker_session_active
        if breaker_state_session != bar_session:
            breaker_state_session = bar_session
            breaker_session_active = False
        if breaker_session_active:
            return
        # K-7 weekly breaker
        nonlocal breaker_state_week, breaker_week_active
        wk = _iso_week(bar_session)
        if breaker_state_week != wk:
            breaker_state_week = wk
            breaker_week_active = False
        if breaker_week_active:
            return

        eq_for_size = equity if cfg.use_current_equity_rebase else starting_equity_for_pct_calc

        # Iterate setups confirmed at this bar.
        for s in setup_idx_by_bar.get(t, []):
            # rho_star gate per H055 design.md §3 (PLACEHOLDER threshold).
            if not np.isfinite(s.rho_1_at_confirmation):
                continue
            if s.rho_1_at_confirmation < rho_star:
                continue
            # K-8 trend-filter gate: side must align with trend if trend signal is non-zero.
            if s.trend_side_at_confirmation != 0:
                if s.side * s.trend_side_at_confirmation <= 0:
                    continue
            # Sizing: per design.md §4 with ADR-0017 §4.1 current-equity rebase.
            atr_t = float(s.atr_n_at_confirmation)
            if not np.isfinite(atr_t) or atr_t <= 0:
                continue
            # Entry fill: simplified to next-bar open (PIT-safe causal).
            entry_idx = t + 1
            if entry_idx >= n_bars:
                continue
            entry_price = float(open_[entry_idx])
            beta_dollars_per_contract = beta_sl_mult * atr_t * multiplier
            if beta_dollars_per_contract <= 0:
                continue
            current_km = sm.km if (sm is not None) else cfg.kelly_multiplier
            effective_risk_pct = current_km * cfg.risk_budget_pct
            target_dollar_risk = effective_risk_pct * eq_for_size
            size_from_risk = target_dollar_risk / beta_dollars_per_contract
            size = int(np.floor(min(size_from_risk, cap)))
            if size < 1:
                continue
            stop_price = entry_price - s.side * (beta_sl_mult * atr_t)
            tp_price = entry_price + s.side * (alpha_tp_mult * atr_t)
            position = _Position(
                side=s.side,
                units=[{
                    "entry_price": entry_price,
                    "size": size,
                    "stop_price": stop_price,
                    "tp_price": tp_price,
                    "entry_idx": entry_idx,
                    "r_dollar": beta_dollars_per_contract * size,
                }],
                entry_session_date=bar_session,
                km_at_entry=current_km,
            )
            return  # only one position at a time

    # ── Main loop ──
    for t in range(n_bars - 1):
        bar_session = session_dates[t]
        # Session-boundary BOCD handler — pass ARITHMETIC per-session return
        # per F-1-9 audit fix (mppm_rho_1 internally applies log1p).
        if last_session is not None and bar_session != last_session and sm is not None:
            sess_lr_dollar = per_session_pnl.get(last_session, 0.0)
            # Per-session arithmetic return = (equity_end_of_session - equity_start) / equity_start
            # = sess_pnl / (equity_now - sess_pnl). Closure-state approximation:
            # tracks per-session-bracket return on session-start equity.
            denom = equity - sess_lr_dollar
            if denom > 0:
                sess_arith_ret = float(sess_lr_dollar / denom)
            else:
                sess_arith_ret = 0.0
            sm.on_session_close(sess_arith_ret, last_session)
        last_session = bar_session

        # Update breakers based on cumulative P/L
        wk = _iso_week(bar_session)
        sess_pnl = per_session_pnl.get(bar_session, 0.0)
        wk_pnl = per_week_pnl.get(wk, 0.0)
        denom_for_pct = equity if cfg.use_current_equity_rebase else starting_equity_for_pct_calc
        if not breaker_session_active and (sess_pnl / denom_for_pct) <= daily_loss_breaker_pct:
            breaker_session_active = True
        if not breaker_week_active and (wk_pnl / denom_for_pct) <= weekly_loss_breaker_pct:
            breaker_week_active = True

        if position is not None:
            closed = _check_position_exits(t)
            if closed:
                continue
            # Try pyramiding on bar-t close — use the most-recent ATR available
            # at bar t (we approximate via H055 features ATR series, but
            # for simplicity here we use last unit's r_dollar / multiplier /
            # beta_sl as the ATR proxy).
            last_u = position.units[-1]
            atr_proxy = last_u["r_dollar"] / max(beta_sl_mult * multiplier * last_u["size"], 1e-9)
            _try_pyramid(t, atr_proxy)
        else:
            _try_new_entry_from_setup(t)

    # Final close
    if position is not None:
        _close_all_units(n_bars - 1, float(close[-1]), "end_of_data")
    # Final BOCD session close — pass ARITHMETIC return per F-1-9 audit fix.
    if last_session is not None and sm is not None:
        sess_lr_dollar = per_session_pnl.get(last_session, 0.0)
        denom = equity - sess_lr_dollar
        if denom > 0:
            sess_arith_ret = float(sess_lr_dollar / denom)
        else:
            sess_arith_ret = 0.0
        sm.on_session_close(sess_arith_ret, last_session)

    # ── Realized metrics ──
    eq_arr = np.array(equity_curve, dtype=float)
    realized_end = float(eq_arr[-1])
    running_max = np.maximum.accumulate(eq_arr)
    safe_max = np.where(running_max > 0.0, running_max, 1.0)
    dd = (eq_arr - running_max) / safe_max
    max_dd = float(-dd.min()) if dd.size > 0 else 0.0

    trade_pnls = np.array([t["total_pnl"] for t in trades])
    trade_rs = np.array([t["r_multiple"] for t in trades])
    wins = int((trade_pnls > 0).sum())
    losses = int((trade_pnls < 0).sum())
    zeros = int((trade_pnls == 0).sum())
    n_trades = len(trades)

    # Per-trade log return → annualised Sharpe approximation.
    per_trade_log_returns = []
    eq_prev = starting_equity_for_pct_calc
    for t in trades:
        eq_new = t["equity_post_trade"]
        if eq_prev > 0 and eq_new > 0:
            per_trade_log_returns.append(float(np.log(eq_new / eq_prev)))
        else:
            per_trade_log_returns.append(0.0)
        eq_prev = eq_new
    ptlr = np.array(per_trade_log_returns)
    sr_per_trade = (
        ptlr.mean() / ptlr.std(ddof=1)
        if ptlr.size > 1 and ptlr.std(ddof=1) > 0 else float("nan")
    )
    # Approximate trades-per-year for annualisation:
    # n_bars / (78 × 252) where 78 = 5-min bars per RTH session
    n_years = max(n_bars / (78 * 252), 0.1)
    sr_annualised = (
        sr_per_trade * np.sqrt(n_trades / n_years)
        if not np.isnan(sr_per_trade) else float("nan")
    )

    # ADR-0017 §1 primary metrics on per-session returns.
    # Per `mppm_rho_1` docstring (and GISW 2007 Theorem 1), the input must be
    # ARITHMETIC returns r_t such that (1 + r_t) > 0; the primitive internally
    # applies log1p (do not pre-log). Compute per-session log returns SEPARATELY
    # for the Calmar/annualised calc (which works in log-space additively per
    # the project convention).
    per_session_arith_returns = []  # arithmetic; for MPPM
    per_session_log_returns = []    # log; for Calmar additivity
    sessions_seen = list(per_session_pnl.keys())
    sessions_seen.sort()
    running_eq = starting_equity_for_pct_calc
    for sd in sessions_seen:
        pnl = per_session_pnl[sd]
        if running_eq > 0 and (running_eq + pnl) > 0:
            arith = float((running_eq + pnl) / running_eq - 1.0)
            log_ret = float(np.log((running_eq + pnl) / running_eq))
        else:
            # Ruin: cap at -0.99 (per mppm_rho_1's (1 + r) > 0 invariant)
            arith = -0.99
            log_ret = float(np.log(0.01))
        per_session_arith_returns.append(arith)
        per_session_log_returns.append(log_ret)
        running_eq += pnl

    psr_arith = np.array(per_session_arith_returns)
    psr_log = np.array(per_session_log_returns)
    # MPPM(rho=1) via project canonical primitive — pass ARITHMETIC returns
    # per F-1-9 R1 audit fix (mppm_rho_1 applies log1p internally).
    try:
        mppm_value = (
            float(mppm_rho_1(psr_arith, delta_t=1.0 / 252.0))
            if psr_arith.size >= 2 else float("nan")
        )
    except (ValueError, FloatingPointError):
        mppm_value = float("nan")

    # Calmar (annualised log-return / max DD)
    if psr_log.size > 0:
        ann_log_ret = float(psr_log.sum() * (252.0 / max(psr_log.size, 1)))
    else:
        ann_log_ret = float("nan")
    calmar = (
        ann_log_ret / max_dd if (max_dd > 0 and np.isfinite(ann_log_ret))
        else float("nan")
    )

    # Profit factor
    try:
        pf = float(profit_factor(trade_pnls)) if trade_pnls.size > 0 else float("nan")
    except (ValueError, FloatingPointError, ZeroDivisionError):
        pf = float("nan")

    # R-multiple mean
    r_mean = float(trade_rs.mean()) if trade_rs.size > 0 else float("nan")

    # L-skewness on per-trade R-multiple distribution
    try:
        l_skew = float(l_skewness_tau3(trade_rs)) if trade_rs.size >= 4 else float("nan")
    except (ValueError, FloatingPointError):
        l_skew = float("nan")

    return {
        "symbol": symbol,
        "cfg_name": cfg.name,
        "n_trades": n_trades,
        "n_bars": n_bars,
        "realized_end_equity": realized_end,
        "realized_roi_pct": (realized_end / starting_equity_for_pct_calc - 1.0) * 100,
        "realized_max_dd_pct": max_dd * 100,
        "wins": wins,
        "losses": losses,
        "zeros": zeros,
        "win_rate": wins / max(n_trades, 1),
        "sr_annualised_approx": float(sr_annualised) if not np.isnan(sr_annualised) else None,
        "mppm_rho_1_annualised": mppm_value,
        "calmar": calmar,
        "profit_factor": pf,
        "r_multiple_mean": r_mean,
        "l_skewness_tau3": l_skew,
        "ann_log_return": ann_log_ret,
        "n_ruin_events": n_ruin_events,
        "trade_pnl_mean": float(trade_pnls.mean()) if trade_pnls.size else 0.0,
        "trade_pnl_std": float(trade_pnls.std(ddof=1)) if trade_pnls.size > 1 else 0.0,
        "trades": trades,
        "equity_curve": eq_arr.tolist(),
        "per_session_pnl": {str(k): v for k, v in per_session_pnl.items()},
        "per_session_log_returns": per_session_log_returns,
        "bocd_step_history": (sm.step_history if sm is not None else []),
        "km_terminal": (sm.km if sm is not None else cfg.kelly_multiplier),
        "n_km_step_ups": (
            sum(1 for h in sm.step_history if h["action"] == "step_up")
            if sm is not None else 0
        ),
        "n_km_halves": (
            sum(1 for h in sm.step_history if h["action"] == "halve")
            if sm is not None else 0
        ),
    }


# ────────────────────────────────────────────────────────────────────────────
# Reporting helpers
# ────────────────────────────────────────────────────────────────────────────


def _subwindow_metrics(
    result: dict[str, Any],
    *,
    sub_start_iso: str,
    sub_end_iso: str,
) -> dict[str, Any]:
    """Compute realized ROI + MaxDD on trades within [sub_start, sub_end]."""
    sub_start = pd.Timestamp(sub_start_iso, tz="UTC").date()
    sub_end = pd.Timestamp(sub_end_iso, tz="UTC").date()
    trades_sub: list[dict[str, Any]] = []
    for t in result["trades"]:
        try:
            sd_obj = datetime.fromisoformat(t["entry_session_date"]).date()
        except (ValueError, TypeError):
            continue
        if sub_start <= sd_obj <= sub_end:
            trades_sub.append(t)
    if not trades_sub:
        return {
            "n_trades_sub": 0,
            "sub_roi_pct": 0.0,
            "sub_max_dd_pct": 0.0,
            "sub_wins": 0,
            "sub_losses": 0,
            "sub_zeros": 0,
        }
    # Reconstruct equity curve in the sub-window. Start at the equity
    # *at entry of the first sub-window trade* (i.e., equity_post_trade
    # of the trade immediately before).
    starting_eq_sub = 10000.0  # match v1 baseline
    # Find prior-trade equity:
    first_sub_idx = result["trades"].index(trades_sub[0])
    if first_sub_idx > 0:
        starting_eq_sub = float(result["trades"][first_sub_idx - 1]["equity_post_trade"])
    eq_curve = [starting_eq_sub]
    for t in trades_sub:
        eq_curve.append(float(t["equity_post_trade"]))
    eq_arr = np.array(eq_curve, dtype=float)
    end_eq = float(eq_arr[-1])
    pnls = np.array([t["total_pnl"] for t in trades_sub])
    wins = int((pnls > 0).sum())
    losses = int((pnls < 0).sum())
    zeros = int((pnls == 0).sum())
    running_max = np.maximum.accumulate(eq_arr)
    safe_max = np.where(running_max > 0.0, running_max, 1.0)
    dd = (eq_arr - running_max) / safe_max
    max_dd_sub = float(-dd.min()) if dd.size > 0 else 0.0
    roi_sub = (end_eq / starting_eq_sub - 1.0) * 100 if starting_eq_sub > 0 else 0.0
    return {
        "n_trades_sub": len(trades_sub),
        "sub_starting_eq": starting_eq_sub,
        "sub_end_eq": end_eq,
        "sub_roi_pct": roi_sub,
        "sub_max_dd_pct": max_dd_sub * 100,
        "sub_wins": wins,
        "sub_losses": losses,
        "sub_zeros": zeros,
    }


def _format_kpi_row(
    *,
    cfg_name: str,
    symbol: str,
    res: dict[str, Any],
    sub: dict[str, Any],
) -> str:
    """One row of the KPI metrics table."""
    sr_str = (
        f"{res['sr_annualised_approx']:+.2f}"
        if res['sr_annualised_approx'] is not None else "n/a"
    )
    mppm_str = (
        f"{res['mppm_rho_1_annualised']:+.3f}"
        if np.isfinite(res['mppm_rho_1_annualised']) else "n/a"
    )
    calmar_str = (
        f"{res['calmar']:+.3f}"
        if np.isfinite(res['calmar']) else "n/a"
    )
    pf_str = (
        f"{res['profit_factor']:.2f}"
        if np.isfinite(res['profit_factor']) else "n/a"
    )
    r_mean_str = (
        f"{res['r_multiple_mean']:+.3f}"
        if np.isfinite(res['r_multiple_mean']) else "n/a"
    )
    lskew_str = (
        f"{res['l_skewness_tau3']:+.3f}"
        if np.isfinite(res['l_skewness_tau3']) else "n/a"
    )
    return (
        f"| {cfg_name:<18} | {symbol:<6} | "
        f"{res['realized_roi_pct']:>+8.1f}% | {res['realized_max_dd_pct']:>+7.1f}% | "
        f"{res['wins']:>4}/{res['losses']:>4}/{res['zeros']:>3} | "
        f"{sr_str:>8} | {calmar_str:>8} | {pf_str:>6} | "
        f"{r_mean_str:>8} | {mppm_str:>8} | {lskew_str:>8} | "
        f"{res['n_trades']:>7} | "
        f"{sub.get('sub_roi_pct', 0.0):>+8.1f}% | "
        f"{sub.get('sub_max_dd_pct', 0.0):>+7.1f}% |"
    )


def _basket_aggregate_row(
    cfg_name: str,
    per_symbol_results: list[dict[str, Any]],
    per_symbol_sub_metrics: list[dict[str, Any]],
) -> str:
    """Compute basket-aggregate row (equal-dollar at $10k per symbol)."""
    n_sym = len(per_symbol_results)
    basket_start = 10000.0 * n_sym
    basket_end = sum(r["realized_end_equity"] for r in per_symbol_results)
    basket_roi = (basket_end / basket_start - 1.0) * 100 if basket_start > 0 else 0.0
    sub_start = 10000.0 * n_sym  # simplification; assume equal allocation at sub start
    sub_end = sum(
        s.get("sub_end_eq", s.get("sub_starting_eq", 10000.0))
        for s in per_symbol_sub_metrics
    )
    sub_start_sum = sum(
        s.get("sub_starting_eq", 10000.0) for s in per_symbol_sub_metrics
    )
    sub_roi = (sub_end / sub_start_sum - 1.0) * 100 if sub_start_sum > 0 else 0.0
    wins = sum(r["wins"] for r in per_symbol_results)
    losses = sum(r["losses"] for r in per_symbol_results)
    zeros = sum(r["zeros"] for r in per_symbol_results)
    n_trades = sum(r["n_trades"] for r in per_symbol_results)
    return (
        f"| {cfg_name + ' BASKET':<18} | {'4-sym':<6} | "
        f"{basket_roi:>+8.1f}% | {'—':>7} | "
        f"{wins:>4}/{losses:>4}/{zeros:>3} | "
        f"{'—':>8} | {'—':>8} | {'—':>6} | "
        f"{'—':>8} | {'—':>8} | {'—':>8} | "
        f"{n_trades:>7} | {sub_roi:>+8.1f}% | {'—':>7} |"
    )


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H055 v2 aggressive-sizing sweep")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--symbols", nargs="*",
        default=["ES", "NQ", "MGC", "SIL"],
        help="Subset of symbols to sweep (default: 4-symbol basket)",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="Smoke mode: limit each symbol to 100k bars for fast end-to-end "
             "validation. Do NOT use for production KPI emission.",
    )
    parser.add_argument(
        "--full-oos-start", type=str, default="2024-01-01",
        help="Start of FULL OOS window (default 2024-01-01).",
    )
    parser.add_argument(
        "--substrate-end", type=str, default="2026-05-15",
        help="Substrate right-edge (default 2026-05-15).",
    )
    parser.add_argument(
        "--sub-start", type=str, default="2026-04-01",
        help="Start of sub-window (default 2026-04-01).",
    )
    parser.add_argument(
        "--sub-end", type=str, default="2026-05-15",
        help="End of sub-window (default 2026-05-15).",
    )
    parser.add_argument(
        "--rho-star", type=float, default=0.0,
        help="rho_1 admit threshold (PLACEHOLDER per design.md §5.2; "
             "default 0.0 = no gate; calibration-holdout binding under "
             "P1-H055-CALIBRATION-HOLDOUT-RUN).",
    )
    args = parser.parse_args(argv)

    if args.substrate_path:
        substrate_root = Path(args.substrate_path).resolve()
    else:
        substrate_root = (
            _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
        )

    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else _REPO_ROOT / "artifacts" / "runs" / "H055"
            / f"v2_sweep_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Window setup ──
    start = pd.Timestamp(args.full_oos_start, tz="UTC")
    end = pd.Timestamp(args.substrate_end, tz="UTC") + pd.Timedelta(hours=23, minutes=59)
    sub_start_iso = args.sub_start
    sub_end_iso = args.sub_end

    # ── Feature-config (uniform across all 4 symbols + 5 configs) ──
    # H055 design.md §5.6 mid-grid defaults:
    feat_cfg = H055FeatureConfig(
        trend_id_choice="a",  # TSMOM sign per MOP 2012 — robust default; rho rule deferred
        trend_id_lookback_l=60,
        tau_m=1.0,
        rho_window_n=10,
        atr_n=14,
        swing_confirmation_window=5,
        theta_wick_min=1.5,
        news_calendar_enabled=False,  # v2 sweep disables news exclusion for clean baseline
    )

    bocd_cfg = BOCDConfig()

    # ── Loop ──
    full_results: list[dict[str, Any]] = []
    sub_results: list[dict[str, Any]] = []

    for sym in args.symbols:
        _log.info("Loading %s [%s -> %s]...", sym, start.date(), end.date())
        df_5m = _load_5min_bars(substrate_root, sym, start=start, end=end)
        if args.smoke:
            df_5m = df_5m.head(100000)
            _log.info("  smoke mode: truncated to %d bars", len(df_5m))
        _log.info(
            "  %s: %d 5-min bars (%d sessions)",
            sym, len(df_5m), df_5m["session_date_et"].nunique(),
        )

        # ── Feature factory + setup detection (once per symbol) ──
        ts_event_list = list(df_5m["ts_event"].dt.to_pydatetime())
        features = compute_h055_features(
            open_prices=df_5m["open"].to_numpy(),
            high=df_5m["high"].to_numpy(),
            low=df_5m["low"].to_numpy(),
            close=df_5m["close"].to_numpy(),
            bar_timestamps_utc=ts_event_list,
            config=feat_cfg,
        )
        setups = emit_h055_setups(
            open_prices=df_5m["open"].to_numpy(),
            high=df_5m["high"].to_numpy(),
            low=df_5m["low"].to_numpy(),
            close=df_5m["close"].to_numpy(),
            config=feat_cfg,
            bar_features=features,
        )
        _log.info("  %s: detected %d setups", sym, len(setups))

        # Index setups by confirmation_bar for fast lookup.
        setup_idx_by_bar: dict[int, list] = {}
        for s in setups:
            setup_idx_by_bar.setdefault(s.confirmation_bar, []).append(s)

        for cfg in SWEEP_CONFIGS:
            res = _run_simulation(
                symbol=sym,
                df_5m=df_5m,
                feature_config=feat_cfg,
                setups=setups,
                setup_idx_by_bar=setup_idx_by_bar,
                cfg=cfg,
                bocd_cfg=bocd_cfg,
                rho_star=args.rho_star,
            )
            sub = _subwindow_metrics(
                res, sub_start_iso=sub_start_iso, sub_end_iso=sub_end_iso,
            )
            res["sub_window"] = sub
            res["cfg_description"] = cfg.description
            res["cfg_kelly_multiplier"] = cfg.kelly_multiplier
            res["cfg_risk_budget_pct"] = cfg.risk_budget_pct
            res["cfg_use_current_equity_rebase"] = cfg.use_current_equity_rebase
            res["cfg_enable_pyramiding"] = cfg.enable_pyramiding
            res["cfg_enable_bocd"] = cfg.enable_bocd
            full_results.append(res)
            _log.info(
                "  %s × %s: end=$%.0f (%+.1f%%) MaxDD=%.1f%% W/L/Z=%d/%d/%d trades=%d "
                "MPPM=%+.3f Calmar=%+.3f sub=%+.1f%% (%d trades)",
                sym, cfg.name, res["realized_end_equity"], res["realized_roi_pct"],
                res["realized_max_dd_pct"], res["wins"], res["losses"], res["zeros"],
                res["n_trades"], res["mppm_rho_1_annualised"], res["calmar"],
                sub.get("sub_roi_pct", 0.0), sub.get("n_trades_sub", 0),
            )

    # ── Provenance: git head + substrate SHA ──
    try:
        git_head = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        git_head = "unknown"
    # Read substrate provenance for SHA — glob most-recent provenance JSON.
    substrate_sha = "unknown"
    prov_glob = sorted(
        (_REPO_ROOT / "data" / "processed" / "_provenance").glob(
            "vendor_legacy_1min_roll_adjusted_*.json"
        )
    )
    if prov_glob:
        try:
            prov_data = json.loads(prov_glob[-1].read_text(encoding="utf-8"))
            substrate_sha = prov_data.get("output_frame_sha256", "unknown")
        except Exception:  # noqa: BLE001
            pass

    # ── Sidecar payload ──
    payload = {
        "hypothesis_id": "H055",
        "version": "v2",
        "experiment": "v2_aggressive_sizing_sweep",
        "git_head": git_head,
        "substrate": {
            "root": str(substrate_root),
            "output_frame_sha256": substrate_sha,
            "window_full_oos": [str(start), str(end)],
            "window_sub": [sub_start_iso, sub_end_iso],
        },
        "feature_config": {
            "trend_id_choice": feat_cfg.trend_id_choice,
            "trend_id_lookback_l": feat_cfg.trend_id_lookback_l,
            "tau_m": feat_cfg.tau_m,
            "rho_window_n": feat_cfg.rho_window_n,
            "atr_n": feat_cfg.atr_n,
            "swing_confirmation_window": feat_cfg.swing_confirmation_window,
            "theta_wick_min": feat_cfg.theta_wick_min,
        },
        "tp_sl_config": {
            "alpha_tp_mult": 2.0,
            "beta_sl_mult": 1.5,
            "k_swing_bars_5min": 30,
        },
        "bocd_config": {
            "km_grid": list(bocd_cfg.km_grid),
            "step_check_interval_sessions": bocd_cfg.step_check_interval_sessions,
            "bocd_hazard_rate": bocd_cfg.bocd_hazard_rate,
            "bocd_window": bocd_cfg.bocd_window,
            "bocd_threshold": bocd_cfg.bocd_threshold,
            "rolling_mppm_window": bocd_cfg.rolling_mppm_window,
        },
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
                "enable_bocd": c.enable_bocd,
            } for c in SWEEP_CONFIGS
        ],
        "kill_switches": {
            "K1_per_trade_stop": "1.0R = beta_sl × ATR × multiplier × position_size",
            "K3_no_add_to_loser": True,
            "K4_capacity_caps": _CAPACITY_CAPS,
            "K6_daily_loss_breaker_pct": -0.02,
            "K7_weekly_loss_breaker_pct": -0.05,
            "K8_trend_filter_gate": "side × trend_side_at_confirmation must be > 0 for entry",
        },
        "results": full_results,
        "rho_star_at_run": float(args.rho_star),
        "smoke_mode": bool(args.smoke),
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }

    # Strip heavy nested lists from sidecar (keep summary fields)
    light_payload = json.loads(json.dumps(payload, default=str))
    for r in light_payload["results"]:
        # Reduce nested-list bulk
        r.pop("trades", None)
        r.pop("equity_curve", None)
        r.pop("per_session_pnl", None)
        r.pop("per_session_log_returns", None)
        # Keep bocd_step_history limited
        if len(r.get("bocd_step_history", [])) > 50:
            r["bocd_step_history_n"] = len(r["bocd_step_history"])
            r["bocd_step_history"] = r["bocd_step_history"][:20] + r["bocd_step_history"][-20:]
    sidecar_path = out_dir / "sweep_sidecar.json"
    sidecar_bytes = json.dumps(light_payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sweep_sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sweep_sidecar=%s sha256=%s", sidecar_path, sha[:16])

    # ── KPI table ──
    # Reconfigure stdout to UTF-8 so unicode-safe symbols print correctly on
    # Windows cp1252 default encoding.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    print()
    header = (
        "=" * 200 + "\n"
        "H055 v2 -- AGGRESSIVE-SIZING SWEEP ON WICK-REJECTION SETUPS\n"
        f"FULL OOS: {args.full_oos_start} -> {args.substrate_end}; "
        f"SUB-WINDOW: {sub_start_iso} -> {sub_end_iso}\n"
        f"feature cell: trend_id={feat_cfg.trend_id_choice} L={feat_cfg.trend_id_lookback_l} tau_m={feat_cfg.tau_m}, "
        f"rho_n={feat_cfg.rho_window_n}, atr_n={feat_cfg.atr_n}, "
        f"theta_wick_min={feat_cfg.theta_wick_min}, swing_window={feat_cfg.swing_confirmation_window}; "
        "alpha_tp_mult=2.0, beta_sl_mult=1.5; rho_star=0.0 (PLACEHOLDER)\n"
        f"sidecar: {sidecar_path}  sha256: {sha[:16]}\n"
        "=" * 200
    )
    print(header)
    print(
        f"| {'Config':<18} | {'Symbol':<6} | {'OOS_ROI%':>9} | {'MaxDD%':>8} | "
        f"{'W/L/Z':>13} | {'SR_ann':>8} | {'Calmar':>8} | {'PF':>6} | "
        f"{'R_mean':>8} | {'MPPM':>8} | {'L_skew':>8} | {'n_trades':>8} | "
        f"{'Sub_ROI%':>9} | {'SubDD%':>7} |"
    )
    print(
        f"|{'-' * 20}|{'-' * 8}|{'-' * 11}|{'-' * 10}|"
        f"{'-' * 15}|{'-' * 10}|{'-' * 10}|{'-' * 8}|"
        f"{'-' * 10}|{'-' * 10}|{'-' * 10}|{'-' * 10}|"
        f"{'-' * 11}|{'-' * 9}|"
    )

    for cfg in SWEEP_CONFIGS:
        sym_results = [r for r in full_results if r["cfg_name"] == cfg.name]
        sym_subs = [r["sub_window"] for r in sym_results]
        for r in sym_results:
            print(_format_kpi_row(
                cfg_name=cfg.name, symbol=r["symbol"], res=r, sub=r["sub_window"],
            ))
        print(_basket_aggregate_row(cfg.name, sym_results, sym_subs))
        print(
            f"|{'-' * 20}|{'-' * 8}|{'-' * 11}|{'-' * 10}|"
            f"{'-' * 15}|{'-' * 10}|{'-' * 10}|{'-' * 8}|"
            f"{'-' * 10}|{'-' * 10}|{'-' * 10}|{'-' * 10}|"
            f"{'-' * 11}|{'-' * 9}|"
        )
    print("=" * 200)

    # Also write the table as markdown alongside the sidecar
    table_md_path = out_dir / "kpi_metrics_table.md"
    with table_md_path.open("w", encoding="utf-8") as f:
        f.write("# H055 v2 — KPI Metrics Table\n\n")
        f.write(f"FULL OOS: {args.full_oos_start} → {args.substrate_end}; "
                f"SUB-WINDOW: {sub_start_iso} → {sub_end_iso}\n\n")
        f.write(f"Substrate SHA: `{substrate_sha[:16]}...`  Git HEAD: `{git_head[:12]}`\n\n")
        f.write("| Config | Symbol | OOS ROI% | MaxDD% | W/L/Z | SR_ann | Calmar | PF | "
                "R_mean | MPPM | L_skew | n_trades | Sub ROI% | Sub DD% |\n")
        f.write("|---|---|---:|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for cfg in SWEEP_CONFIGS:
            sym_results = [r for r in full_results if r["cfg_name"] == cfg.name]
            sym_subs = [r["sub_window"] for r in sym_results]
            for r in sym_results:
                row = _format_kpi_row(
                    cfg_name=cfg.name, symbol=r["symbol"], res=r, sub=r["sub_window"],
                )
                f.write(row + "\n")
            f.write(_basket_aggregate_row(cfg.name, sym_results, sym_subs) + "\n")
    _log.info("kpi_table_md=%s", table_md_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
