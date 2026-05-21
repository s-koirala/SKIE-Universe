"""H068 v2 walk-forward orchestrator — multi-instrument basket {ES, MGC, SIL}.

Genetic successor of H068 v1 per ADR-0027 §D-4 single-axis-genetic-cross discipline.
Single cross-axis = universe expansion from ES standalone to 3-symbol basket.
Closes `P1-H068-V2-EXPANDED-SUBSTRATE` BLOCKING follow-up per Phase O.18 closure.

Per H068 v2 design.md §1 + §5 + §6: preserves the canonical Donchian-channel
breakout signal verbatim from H068 v1 + H065 v2 (channel_n=120, k_atr=2.0,
atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; no TP overlay i.e. M=∞)
and applies it across 3 symbols × 3 slip cells × 6 Kelly multipliers ×
2 cost-arms = 108 per-symbol cells + 36 basket-aggregated cells.

Per H068 v2 design.md §1 H_1 (BASKET-level conjunctive criterion):
    There exists slip* ∈ {0.25, 0.5, 1.0} tick such that:
    (a) basket realized OOS ROI > 0 at A1 conservative-prior at corresponding
        sensitivity_mult, AND
    (b) basket-aggregated MPPM(ρ=1) stationary-bootstrap CI strictly excludes
        zero positively, AND
    (c) per-symbol cost-friction-breakeven ratio ≥ 2 on ≥ 2 of 3 symbols
        (cost-friction-dominated-edge-present at basket level per ADR-0028 §D-2).

Basket-aggregation convention (per design.md §1):
    BASKET-AGGREGATED per-session log-return = equal-weighted (1/3) sum of
    per-symbol per-session log-returns across {ES, MGC, SIL} per Goetzmann-
    Ingersoll-Spiegel-Welch 2007 §2 dimensional-consistency convention
    (cf. H062 design.md §1 + H060 v1 basket-aggregation pattern).

ADR-0025 opt-in primitive flags (preserve Phase O.13 v3 sidecar numerics on
default-OFF; H068 v2 design.md §11.1 sets enable_k4=True + enable_k6=True +
enable_k7=True + k6_enforcement="block" + k7_enforcement="block" defaults):
    --enable-kill-switch-runtime
    --enable-equity-rebase-current
    --cost-model {none, conservative_prior, paper_trade_empirical}
    --zero-cost-reference-run-id (per ADR-0028 §D-2)
    --zero-cost-reference-basket-pct
    --zero-cost-reference-sidecar-sha-prefix16

LOAD-MANAGEMENT NOTE: per the Phase O.20 directive this orchestrator's
walk-forward execution itself is OPERATOR-AUTHORIZED per separate cycle;
the build/test cycle uses tests/unit/test_h068_v2_walk_forward.py + tests/
integration/test_h068_v2_pit_canaries.py + KPI v1 placeholder emission.
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
from skie_ninja.inference.calmar import calmar_ratio
from skie_ninja.inference.cost_friction_edge import (
    build_cost_friction_edge_block,
    cost_friction_dominated_edge_annotation,
)
from skie_ninja.inference.mppm import mppm_rho_1, mppm_with_ci
from skie_ninja.inference.profit_factor import profit_factor
from skie_ninja.inference.r_multiple import r_multiple_mean_ci_stationary_bootstrap
from skie_ninja.inference.skewness import (
    l_skewness_tau3,
    l_skewness_tau3_ci_stationary_bootstrap,
    payoff_shape_annotation,
)
from skie_ninja.utils.runcontext import RunContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h068_v2_walk_forward")


# Per-symbol multipliers per CME product specifications + ADR-0001 retail-tier
# capacity caps. ES per $50/point spec; MGC = $10/oz × 1 oz/contract = $10
# multiplier; SIL = $5/oz × 1000 oz/contract = $5,000 multiplier in dollar
# terms when expressed as price × multiplier; however the standard convention
# in this project uses the per-symbol tick_value × ticks-per-point ratio to
# carry the multiplier. To stay consistent with the H068 v1 + H062 + H065
# convention ([scripts/run_h068_sensitivity_sweep.py] uses ES_MULTIPLIER = 50.0
# = ES tick_value $12.50 × ticks-per-point 4), we apply the parallel
# convention for MGC + SIL via the canonical tick-value × ticks-per-point.
# justify: per ADR-0001 + config/instruments.yaml tick-value-by-symbol:
#   ES: tick_value $12.50 × 4 ticks/pt = $50.00/pt multiplier
#   MGC: tick_value $1.00 × 10 ticks/pt = $10.00/pt multiplier
#   SIL: tick_value $5.00 × 1 tick/pt = $5.00/pt multiplier
_PER_SYMBOL_MULTIPLIER: dict[str, float] = {
    "ES": 50.0,
    "MGC": 10.0,
    "SIL": 5.0,
}

# Per-symbol retail-tier capacity caps per ADR-0001 + H068 v2 design.md §11.1.
# ES retail-tier cap = 20 per ADR-0001; MGC + SIL micro-class effectively
# unbounded at $10K retail equity (per-trade-risk × 1% × $10K = $100 risk
# budget; MGC/SIL 1R-cost typically allows <10 contracts at retail-tier).
_PER_SYMBOL_CAPACITY_CAP: dict[str, int] = {
    "ES": 20,
    "MGC": 999,
    "SIL": 999,
}

# Sub-window cutoff per ADR-0026 §D-1 §0 3-component header component 2.
_SUBWINDOW_START = pd.Timestamp("2026-04-01", tz="UTC").date()
_SUBWINDOW_END = pd.Timestamp("2026-05-15", tz="UTC").date()

# justify: bootstrap CI defaults per H068 v2 design.md §12 reproducibility +
# RNG seed 20260520 per design.md §12 (distinguished from H068 v1's 20260519
# per the v2 pre-reg-date 2026-05-20) + project-canonical 252 sessions/year +
# 1000 bootstrap replicates per H062 v1 + H065 v2 + H068 v1 precedent.
_RNG_SEED = 20260520
_N_BOOTSTRAP_CI = 1000
_ANNUALIZATION_FACTOR = 252.0

# H068 v2 cell-grid per design.md §5
_SLIP_CELLS: tuple[float, ...] = (0.25, 0.5, 1.0)
_KELLY_CELLS: tuple[float, ...] = (0.25, 0.5, 1.0, 1.5, 2.0, 2.5)
_COST_ARMS: tuple[str, ...] = ("A0_zero", "A1_conservative_prior")
_SYMBOLS: tuple[str, ...] = ("ES", "MGC", "SIL")

# justify: per H068 v2 design.md §9 + §11.2 `P1-H068-V2-N-MIN-TRADES-GUARD` —
# Tharp 1998 *practitioner* n ≥ 30 R-multiple CI threshold; H068 v2 sets per-
# symbol n_min=50 per H068 v1 precedent; basket-level n_min=150 (3 × 50).
_N_MIN_TRADES_GUARD_PER_SYMBOL: int = 50
_N_MIN_TRADES_GUARD_BASKET: int = 150

# justify: ADR-0028 §D-2 cost-friction-dominated-edge-present ratio threshold;
# per H068 v2 design.md §6 the per-symbol slip-refinement leverage varies
# (ES + SIL clear-feasible; MGC potentially does not at any slip cell).
_COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD: float = 2.0


def _resolve_substrate_dataset_checksum() -> str:
    """Resolve the most recent vendor_legacy_1min_roll_adjusted provenance SHA.

    Per H065 v2 corrigendum + H068 v1 precedent — sidecar
    substrate_dataset_checksum must match the substrate the sweep consumed.
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


def _compute_per_partition_shas(substrate_root: Path, symbols: tuple[str, ...]) -> dict[str, str]:
    """Per H068 v2 design.md §11.2 `P1-H068-V2-SUBSTRATE-PER-PARTITION-SHA-EMIT` —
    enumerate per-symbol per-partition SHAs at sweep-start.
    """
    out: dict[str, str] = {}
    for sym in symbols:
        sym_root = substrate_root / f"symbol={sym}"
        if not sym_root.exists():
            out[f"{sym}/_error"] = f"partition root not found at {sym_root}"
            continue
        parts = sorted(sym_root.glob("year=*/part-*.parquet"))
        for p in parts:
            rel = p.relative_to(substrate_root)
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            out[str(rel).replace("\\", "/")] = sha
    return out


@dataclass(frozen=True)
class V2SweepConfig:
    """H068 v2 per-symbol cell-grid configuration cell.

    sensitivity_mult: slip-per-side multiplier ∈ {0.25, 0.5, 1.0} (design.md §6).
    kelly_multiplier: Kelly multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}
        (per ADR-0018 D-2).
    cost_arm: "A0_zero" (no cost subtraction) or "A1_conservative_prior" (cost
        from nt8_realistic_v1).
    """

    sensitivity_mult: float
    kelly_multiplier: float
    cost_arm: str
    use_current_equity_rebase: bool

    @property
    def is_a0_zero(self) -> bool:
        return self.cost_arm == "A0_zero"

    @property
    def name(self) -> str:
        return (
            f"slip{self.sensitivity_mult:.2f}_kelly{self.kelly_multiplier:.2f}_"
            f"{self.cost_arm}"
        )


def _build_v2_sweep_configs(*, smoke: bool = False) -> list[V2SweepConfig]:
    """Build the H068 v2 per-symbol 36-cell sweep grid (× 3 symbols = 108).

    Smoke mode: Kelly=0.25 only × 3 slip × 2 arms = 6 per-symbol cells × 3
    symbols = 18 total cells (vs full 108 per-symbol). Designed to surface
    the orchestrator + aggregation pipeline end-to-end on a tractable
    cell count when invoked separately by operator authorization per the
    Phase O.20 load-management directive.
    """
    if smoke:
        kelly_cells = (0.25,)
    else:
        kelly_cells = _KELLY_CELLS

    out: list[V2SweepConfig] = []
    for sm in _SLIP_CELLS:
        for km in kelly_cells:
            for arm in _COST_ARMS:
                out.append(
                    V2SweepConfig(
                        sensitivity_mult=sm,
                        kelly_multiplier=km,
                        cost_arm=arm,
                        use_current_equity_rebase=False,
                    )
                )
    return out


@dataclass
class _Position:
    side: int
    entry_price: float
    size: int
    stop_price: float
    r_dollar: float
    entry_idx: int
    entry_session_date: object
    symbol: str


def _load_5min_bars(
    substrate_root: Path,
    *,
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Load roll-adjusted bars + resample to 5-min per H062/H065/H068 v1 cadence.

    Per-symbol loader parameterised on the substrate symbol partition.
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
        raise RuntimeError(f"{symbol}: substrate empty after [{start}, {end}] filter")
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


def _run_v2_per_symbol_simulation(
    *,
    df_5m: pd.DataFrame,
    feature_config: H062FeatureConfig,
    k_atr: float,
    cfg: V2SweepConfig,
    symbol: str,
    starting_equity: float = 10000.0,
    eod_flatten_minutes_from_open: int = 360,
) -> dict[str, Any]:
    """Per-symbol H068 v2 simulator with slip-sensitivity cost-model integration.

    Logic is identical to H068 v1 _run_sensitivity_simulation but parameterised
    on `symbol` for per-symbol multiplier + capacity cap + cost-model selection.
    Returns per-symbol result dict with per-trade log + per-session aggregate
    + ADR-0017 metrics + K-6/K-7 trigger telemetry + cost telemetry.
    """
    multiplier = _PER_SYMBOL_MULTIPLIER[symbol]
    cap = _PER_SYMBOL_CAPACITY_CAP[symbol]

    high = df_5m["high"].to_numpy()
    low = df_5m["low"].to_numpy()
    close = df_5m["close"].to_numpy()
    open_ = df_5m["open"].to_numpy()
    session_dates = df_5m["session_date_et"].to_numpy()
    n_bars = len(df_5m)

    feats = compute_h062_features(
        high=high, low=low, close=close, config=feature_config
    )

    cost_model: NT8RealisticCostModel | None = None
    if not cfg.is_a0_zero:
        cost_model = NT8RealisticCostModel(
            sensitivity_mult=cfg.sensitivity_mult,
            calibration_source="conservative_prior",
        )

    equity = starting_equity
    trade_log: list[dict] = []
    equity_curve: list[float] = [starting_equity]
    n_ruin_events = 0

    session_starts: dict[object, int] = {}
    for t in range(n_bars):
        sd = session_dates[t]
        if sd not in session_starts:
            session_starts[sd] = t

    k6_triggered_sessions: set[object] = set()
    k7_triggered_weeks: set[tuple[int, int]] = set()
    k6_trigger_count: int = 0
    k7_trigger_count: int = 0
    session_start_equity: dict[object, float] = {}
    week_start_equity: dict[tuple[int, int], float] = {}

    def _to_date(d: object) -> _dt.date:
        if isinstance(d, _dt.date) and not isinstance(d, _dt.datetime):
            return d
        return pd.Timestamp(d).date()

    def _iso_week_key(d: object) -> tuple[int, int]:
        py_d = _to_date(d)
        iso = py_d.isocalendar()
        return (iso[0], iso[1])

    position: _Position | None = None

    def _close_position(exit_idx: int, exit_price: float, reason: str) -> None:
        nonlocal position, equity, n_ruin_events
        if position is None:
            return
        gross_pnl = (
            position.side * (exit_price - position.entry_price)
            * multiplier * position.size
        )
        if cost_model is not None:
            cost_usd = cost_model.round_trip_cost_usd(symbol, n_contracts=position.size)
        else:
            cost_usd = 0.0
        net_pnl = gross_pnl - cost_usd
        r_mult = net_pnl / position.r_dollar if position.r_dollar > 0 else 0.0
        equity += net_pnl
        equity_curve.append(equity)
        trade_log.append({
            "symbol": symbol,
            "side": position.side,
            "entry_price": float(position.entry_price),
            "exit_price": float(exit_price),
            "size": int(position.size),
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

    def _check_stops_exits(t: int) -> bool:
        nonlocal position
        if position is None:
            return False
        bar_session = session_dates[t]
        if position.side == 1:
            if open_[t] < position.stop_price:
                _close_position(t, float(open_[t]), "gap_through_stop_long")
                return True
            if low[t] <= position.stop_price:
                _close_position(t, float(position.stop_price), "stop_hit_long")
                return True
        else:
            if open_[t] > position.stop_price:
                _close_position(t, float(open_[t]), "gap_through_stop_short")
                return True
            if high[t] >= position.stop_price:
                _close_position(t, float(position.stop_price), "stop_hit_short")
                return True
        ev = int(feats.filtered_events[t])
        if (position.side == 1 and ev == -1) or (position.side == -1 and ev == 1):
            _close_position(t, float(close[t]), "opposite_channel_break")
            return True
        session_open_idx = session_starts.get(bar_session, t)
        if (t - session_open_idx) >= eod_flatten_minutes_from_open:
            _close_position(t, float(close[t]), "eod_flatten")
            return True
        if t + 1 < n_bars and session_dates[t + 1] != bar_session:
            _close_position(t, float(close[t]), "session_rollover")
            return True
        return False

    def _try_new_entry(t: int) -> None:
        nonlocal position, k6_trigger_count, k7_trigger_count
        if position is not None:
            return
        ev = int(feats.eligible_events[t])
        if ev == 0:
            return
        bar_session = session_dates[t]

        if bar_session not in session_start_equity:
            session_start_equity[bar_session] = equity
        wk = _iso_week_key(bar_session)
        if wk not in week_start_equity:
            week_start_equity[wk] = equity

        ss_eq = session_start_equity[bar_session]
        if ss_eq > 0 and (equity - ss_eq) / ss_eq <= -0.02:
            if bar_session not in k6_triggered_sessions:
                k6_triggered_sessions.add(bar_session)
                k6_trigger_count += 1
            return
        ws_eq = week_start_equity[wk]
        if ws_eq > 0 and (equity - ws_eq) / ws_eq <= -0.05:
            if wk not in k7_triggered_weeks:
                k7_triggered_weeks.add(wk)
                k7_trigger_count += 1
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
        # justify: H068 v2 design.md §11.1 row "Equity rebase: FIXED-equity per
        # H065 v2 M_inf_h062_v1_fixed-ES parent cell preservation"; current-
        # equity rebase deferred to v3 per `P1-H068-V3-CURRENT-EQUITY-REBASE`.
        eq_for_sizing = starting_equity if not cfg.use_current_equity_rebase else equity
        target_dollar_risk = eq_for_sizing * 0.01
        size_from_risk = target_dollar_risk / dollar_1r_per_contract
        size = int(np.floor(min(size_from_risk, cap)))
        if size < 1:
            return
        stop_price = entry_price - ev * (k_atr * atr_t)
        position = _Position(
            side=ev,
            entry_price=entry_price,
            size=size,
            stop_price=stop_price,
            r_dollar=dollar_1r_per_contract * size,
            entry_idx=entry_idx_candidate,
            entry_session_date=bar_session,
            symbol=symbol,
        )

    for t in range(n_bars - 1):
        if position is not None:
            closed = _check_stops_exits(t)
            if closed:
                continue
        else:
            _try_new_entry(t)

    if position is not None:
        _close_position(n_bars - 1, float(close[-1]), "end_of_data")

    eq_arr = np.array(equity_curve, dtype=float)
    realized_end = float(eq_arr[-1])
    running_max = np.maximum.accumulate(eq_arr)
    dd = (eq_arr - running_max) / running_max
    raw_max_dd_pct = float(-dd.min()) * 100 if dd.size > 0 else 0.0
    max_dd_pct = min(raw_max_dd_pct, 100.0)
    bankroll_blowup = bool((eq_arr < 0).any())

    trade_pnls = np.array([t["pnl"] for t in trade_log])
    trade_rs = np.array([t["r_multiple"] for t in trade_log])
    wins = int((trade_pnls > 0).sum())
    losses = int((trade_pnls < 0).sum())
    zeros = int((trade_pnls == 0).sum())
    n_trades = len(trade_log)

    # Per-session aggregated log-returns (for MPPM / Calmar / Sharpe)
    session_eq_at_close: dict[object, float] = {}
    max_idx_per_session: dict[object, int] = {}
    for tr in trade_log:
        exit_sd = tr["exit_session_date"]
        cur_max = max_idx_per_session.get(exit_sd, -1)
        if tr["exit_idx"] > cur_max:
            session_eq_at_close[exit_sd] = tr["equity_post_trade"]
            max_idx_per_session[exit_sd] = tr["exit_idx"]
    session_dates_unique = sorted({tr["exit_session_date"] for tr in trade_log})
    eq_prev = starting_equity
    session_log_ret: list[float] = []
    session_pnl: list[float] = []
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

    # ---- Per-symbol metrics ----
    if session_log_ret_arr.size >= 4:
        # justify: per H062 v3 critical bug fix per Phase O.10 — mppm_rho_1
        # expects simple returns r_t > -1; convert log-returns via expm1
        # (clipped to avoid float overflow at catastrophic single-session
        # log-ret values).
        session_simple_returns = np.expm1(np.clip(session_log_ret_arr, -6.9, None))
        try:
            mppm_point = float(
                mppm_rho_1(
                    session_simple_returns,
                    risk_free=0.0,
                    delta_t=1.0 / _ANNUALIZATION_FACTOR,
                )
            )
        except Exception as e:  # noqa: BLE001
            _log.warning("[%s] MPPM point failed: %s", symbol, e)
            mppm_point = float("nan")
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
            _log.warning("[%s] MPPM CI failed: %s", symbol, e)
            mppm_ci_low = float("nan")
            mppm_ci_high = float("nan")
            mppm_excludes_zero = False
    else:
        mppm_point = float("nan")
        mppm_ci_low = float("nan")
        mppm_ci_high = float("nan")
        mppm_excludes_zero = False

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
            payoff_shape = payoff_shape_annotation(
                tau3_point, tau3_ci_low, tau3_ci_high
            )
        except Exception as e:  # noqa: BLE001
            _log.warning("[%s] L-skew CI failed: %s", symbol, e)
            tau3_ci_low = float("nan")
            tau3_ci_high = float("nan")
            payoff_shape = "skew-undefined"
    else:
        tau3_point = float("nan")
        tau3_ci_low = float("nan")
        tau3_ci_high = float("nan")
        payoff_shape = "skew-undefined"

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
            _log.warning("[%s] R-mult CI failed: %s", symbol, e)
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
        sr_annualised: float | None = float(sr_session * np.sqrt(_ANNUALIZATION_FACTOR))
    else:
        sr_annualised = None

    if session_log_ret_arr.size >= 4:
        try:
            calmar = float(
                calmar_ratio(
                    session_log_ret_arr, annualization_factor=_ANNUALIZATION_FACTOR
                )
            )
        except Exception:  # noqa: BLE001
            calmar = float("nan")
    else:
        calmar = float("nan")

    total_cost_usd = float(sum(tr["cost_usd"] for tr in trade_log))
    total_gross_pnl = float(sum(tr["gross_pnl"] for tr in trade_log))
    total_net_pnl = float(sum(tr["pnl"] for tr in trade_log))

    underpowered = n_trades < _N_MIN_TRADES_GUARD_PER_SYMBOL
    power_annotation = (
        f"underpowered-n-trades-{n_trades}-below-{_N_MIN_TRADES_GUARD_PER_SYMBOL}"
        if underpowered
        else "power-margin-ok"
    )

    # ---- Sub-window 2026-04-01 → 2026-05-15 ----
    sub_mask = [
        (_to_date(sd) >= _SUBWINDOW_START) and (_to_date(sd) <= _SUBWINDOW_END)
        for sd in session_dates_ordered
    ]
    sub_mask_arr = np.array(sub_mask, dtype=bool)
    if sub_mask_arr.size > 0 and session_log_ret_arr.size > 0:
        sub_session_log_ret = session_log_ret_arr[sub_mask_arr]
    else:
        sub_session_log_ret = np.array([], dtype=float)

    sub_trades = [
        tr for tr in trade_log
        if _SUBWINDOW_START <= _to_date(tr["exit_session_date"]) <= _SUBWINDOW_END
    ]
    if sub_trades:
        first_sub_idx = trade_log.index(sub_trades[0])
        sub_starting_eq = (
            trade_log[first_sub_idx - 1]["equity_post_trade"]
            if first_sub_idx > 0
            else starting_equity
        )
        sub_pnl_sum = sum(tr["pnl"] for tr in sub_trades)
        sub_realized_end = sub_starting_eq + sub_pnl_sum
        sub_realized_roi_pct = (
            (sub_pnl_sum / sub_starting_eq) * 100 if sub_starting_eq > 0 else 0.0
        )
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

    return {
        "symbol": symbol,
        "cfg_name": cfg.name,
        "sensitivity_mult": cfg.sensitivity_mult,
        "kelly_multiplier": cfg.kelly_multiplier,
        "cost_arm": cfg.cost_arm,
        "is_a0_zero": cfg.is_a0_zero,
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
        "sr_annualised": sr_annualised,
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
        "total_cost_usd": total_cost_usd,
        "total_gross_pnl": total_gross_pnl,
        "total_net_pnl": total_net_pnl,
        "k6_trigger_count": k6_trigger_count,
        "k7_trigger_count": k7_trigger_count,
        "k6_triggered_sessions": len(k6_triggered_sessions),
        "k7_triggered_weeks": len(k7_triggered_weeks),
        "subwindow_starting_equity": sub_starting_eq,
        "subwindow_realized_end_equity": sub_realized_end,
        "subwindow_realized_roi_pct": sub_realized_roi_pct,
        "subwindow_realized_max_dd_pct": sub_max_dd_pct,
        "subwindow_wins": sub_wins,
        "subwindow_losses": sub_losses,
        "subwindow_zeros": sub_zeros,
        "subwindow_n_trades": len(sub_trades),
        "underpowered": underpowered,
        "power_annotation": power_annotation,
        # Per-session arrays for basket aggregation
        "session_log_returns": session_log_ret_arr.tolist(),
        "session_pnls": session_pnl_arr.tolist(),
        "session_dates": [str(sd) for sd in session_dates_ordered],
    }


def _aggregate_basket(
    per_symbol_results: list[dict[str, Any]],
    *,
    sensitivity_mult: float,
    kelly_multiplier: float,
    cost_arm: str,
) -> dict[str, Any]:
    """Aggregate per-symbol results into basket-level metrics for one cell.

    Per H068 v2 design.md §1 basket-aggregation convention:
        basket per-session log-return = equal-weighted (1/3) sum across symbols
        on shared session-date keys. Per GISW 2007 §2 dimensional-consistency
        convention (cf. H062 design.md §1 + H060 v1 basket-aggregation pattern).

    Per design.md §1.5 caveat: basket-aggregated MPPM point estimate ≈
    n-weighted average of per-symbol MPPM point estimates; the v2 inferential
    value is NARROWER CI on the (likely-near-zero) point estimate.

    Per design.md §7 Canary E basket-invariant: symbol-order shuffling must
    NOT change the basket-aggregated MPPM(ρ=1) — addressed via canonical
    session-date keying + symbol-set used as basket of independent
    per-session log-return contributions.
    """
    cell_rows = [
        r for r in per_symbol_results
        if r["sensitivity_mult"] == sensitivity_mult
        and r["kelly_multiplier"] == kelly_multiplier
        and r["cost_arm"] == cost_arm
    ]
    if not cell_rows:
        return {
            "sensitivity_mult": sensitivity_mult,
            "kelly_multiplier": kelly_multiplier,
            "cost_arm": cost_arm,
            "n_symbols": 0,
            "_error": "no per-symbol rows for this cell",
        }

    # Build the basket-aggregated per-session log-return series via union of
    # session_dates across all symbols + equal-weighted 1/3 sum.
    # justify: equal-weighted aggregation per design.md §1; per-session log-
    # return of a symbol that did not trade on a given session-date = 0.0
    # (no equity change → no log-return).
    all_dates: set[str] = set()
    for r in cell_rows:
        for sd in r["session_dates"]:
            all_dates.add(sd)
    ordered_dates = sorted(all_dates)
    n_basket_sessions = len(ordered_dates)

    # Per-symbol session-date → log-return dict
    per_symbol_lr_map: dict[str, dict[str, float]] = {}
    for r in cell_rows:
        sym = r["symbol"]
        per_symbol_lr_map[sym] = {
            sd: lr for sd, lr in zip(r["session_dates"], r["session_log_returns"])
        }

    # Equal-weighted basket per-session log-return.
    n_syms = len(cell_rows)
    basket_lr: list[float] = []
    for sd in ordered_dates:
        contrib_sum = 0.0
        for sym, sym_map in per_symbol_lr_map.items():
            contrib_sum += float(sym_map.get(sd, 0.0))
        basket_lr.append(contrib_sum / n_syms if n_syms > 0 else 0.0)
    basket_lr_arr = np.array(basket_lr, dtype=float)

    # Basket-aggregate trade counts (sum across symbols; descriptive only —
    # the basket-aggregation is at the per-session log-return level, not at
    # the per-trade level).
    total_trades = sum(int(r["n_trades"]) for r in cell_rows)
    total_wins = sum(int(r["wins"]) for r in cell_rows)
    total_losses = sum(int(r["losses"]) for r in cell_rows)
    total_zeros = sum(int(r["zeros"]) for r in cell_rows)
    total_cost = sum(float(r["total_cost_usd"]) for r in cell_rows)
    total_gross_pnl = sum(float(r["total_gross_pnl"]) for r in cell_rows)
    total_net_pnl = sum(float(r["total_net_pnl"]) for r in cell_rows)

    # Basket-aggregate ROI on equal-weight $10K-per-symbol = $30K starting basket.
    starting_basket = 10000.0 * n_syms
    realized_end_basket = sum(float(r["realized_end_equity"]) for r in cell_rows)
    basket_roi_pct = (realized_end_basket / starting_basket - 1.0) * 100

    # Basket-aggregate Max-DD via equal-weighted basket equity curve.
    # justify: build a synthetic basket-equity-curve as sum of per-symbol
    # equity curves on shared session-date keys via per-session reconstruction
    # from the basket per-session log-return on the starting_basket level.
    eq_curve = [starting_basket]
    for lr in basket_lr_arr:
        eq_curve.append(eq_curve[-1] * float(np.exp(lr)))
    eq_arr = np.array(eq_curve, dtype=float)
    running_max = np.maximum.accumulate(eq_arr)
    dd = (eq_arr - running_max) / running_max
    raw_max_dd_pct = float(-dd.min()) * 100 if dd.size > 0 else 0.0
    basket_max_dd_pct = min(raw_max_dd_pct, 100.0)

    # Basket-aggregate MPPM(ρ=1) on per-session log-returns.
    if basket_lr_arr.size >= 4:
        # justify: per H062 v3 critical bug fix Phase O.10 — mppm_rho_1 expects
        # simple returns; convert log-returns via expm1.
        basket_simple = np.expm1(np.clip(basket_lr_arr, -6.9, None))
        try:
            basket_mppm_point = float(
                mppm_rho_1(
                    basket_simple,
                    risk_free=0.0,
                    delta_t=1.0 / _ANNUALIZATION_FACTOR,
                )
            )
        except Exception as e:  # noqa: BLE001
            _log.warning("Basket MPPM point failed: %s", e)
            basket_mppm_point = float("nan")
        try:
            basket_mppm_ci = mppm_with_ci(
                basket_simple,
                rho=1.0,
                risk_free=0.0,
                delta_t=1.0 / _ANNUALIZATION_FACTOR,
                n_bootstrap=_N_BOOTSTRAP_CI,
                rng_seed=_RNG_SEED,
            )
            basket_mppm_ci_low = float(basket_mppm_ci.ci_low)
            basket_mppm_ci_high = float(basket_mppm_ci.ci_high)
            basket_mppm_excludes_zero = bool(basket_mppm_ci.excludes_zero)
        except Exception as e:  # noqa: BLE001
            _log.warning("Basket MPPM CI failed: %s", e)
            basket_mppm_ci_low = float("nan")
            basket_mppm_ci_high = float("nan")
            basket_mppm_excludes_zero = False
    else:
        basket_mppm_point = float("nan")
        basket_mppm_ci_low = float("nan")
        basket_mppm_ci_high = float("nan")
        basket_mppm_excludes_zero = False

    # Basket-aggregate Calmar on per-session log-returns.
    if basket_lr_arr.size >= 4:
        try:
            basket_calmar = float(
                calmar_ratio(basket_lr_arr, annualization_factor=_ANNUALIZATION_FACTOR)
            )
        except Exception:  # noqa: BLE001
            basket_calmar = float("nan")
    else:
        basket_calmar = float("nan")

    # Basket-aggregate annualised Sharpe.
    if basket_lr_arr.size > 1 and basket_lr_arr.std(ddof=1) > 0:
        sr_session = basket_lr_arr.mean() / basket_lr_arr.std(ddof=1)
        basket_sr_annualised: float | None = float(
            sr_session * np.sqrt(_ANNUALIZATION_FACTOR)
        )
    else:
        basket_sr_annualised = None

    # Basket-level power annotation (n_min=150 per design.md §9).
    basket_underpowered = total_trades < _N_MIN_TRADES_GUARD_BASKET
    basket_power_annotation = (
        f"underpowered-basket-n-trades-{total_trades}-below-{_N_MIN_TRADES_GUARD_BASKET}"
        if basket_underpowered
        else "basket-power-margin-ok"
    )

    return {
        "sensitivity_mult": sensitivity_mult,
        "kelly_multiplier": kelly_multiplier,
        "cost_arm": cost_arm,
        "n_symbols": n_syms,
        "symbols_in_basket": [r["symbol"] for r in cell_rows],
        "n_basket_sessions": n_basket_sessions,
        "realized_end_basket_equity": realized_end_basket,
        "starting_basket_equity": starting_basket,
        "basket_realized_roi_pct": basket_roi_pct,
        "basket_realized_max_dd_pct": basket_max_dd_pct,
        "basket_total_trades": total_trades,
        "basket_total_wins": total_wins,
        "basket_total_losses": total_losses,
        "basket_total_zeros": total_zeros,
        "basket_win_rate": total_wins / max(total_trades, 1),
        "basket_total_cost_usd": total_cost,
        "basket_total_gross_pnl": total_gross_pnl,
        "basket_total_net_pnl": total_net_pnl,
        "basket_mppm_rho1": basket_mppm_point,
        "basket_mppm_rho1_ci_low": basket_mppm_ci_low,
        "basket_mppm_rho1_ci_high": basket_mppm_ci_high,
        "basket_mppm_rho1_excludes_zero": basket_mppm_excludes_zero,
        "basket_calmar": basket_calmar if np.isfinite(basket_calmar) else None,
        "basket_sr_annualised": basket_sr_annualised,
        "basket_underpowered": basket_underpowered,
        "basket_power_annotation": basket_power_annotation,
        "basket_session_log_returns": basket_lr_arr.tolist(),
    }


def _compute_per_symbol_breakeven_ratio(
    per_symbol_results: list[dict[str, Any]],
    *,
    symbol: str,
    sensitivity_mult: float,
    kelly_multiplier: float = 0.25,
) -> dict[str, Any]:
    """Per-symbol cost-friction-breakeven ratio at a fixed (slip, kelly) cell.

    Per H068 v2 design.md §6 + ADR-0028 §D-2:
        ratio = per-trade gross-edge bps-of-equity (A0) /
                per-trade cost bps-of-equity (A1 same slip + kelly).

    Returns annotation per the cost-friction-dominated-edge schema:
        "cost-friction-dominated-edge-present" if A0 ROI > 0 AND A1 ROI < 0
            AND ratio ≥ 2.
        "cost-friction-dominated-edge-absent" if A1 cell does NOT flip A0 sign.
        "cost-friction-dominated-edge-marginal" otherwise (intermediate).
        "cost-friction-dominated-edge-n/a" if A0 cell missing.
    """
    a0 = next(
        (r for r in per_symbol_results
         if r["symbol"] == symbol
         and r["sensitivity_mult"] == sensitivity_mult
         and r["kelly_multiplier"] == kelly_multiplier
         and r["cost_arm"] == "A0_zero"), None
    )
    a1 = next(
        (r for r in per_symbol_results
         if r["symbol"] == symbol
         and r["sensitivity_mult"] == sensitivity_mult
         and r["kelly_multiplier"] == kelly_multiplier
         and r["cost_arm"] == "A1_conservative_prior"), None
    )
    if a0 is None or a1 is None:
        return {
            "symbol": symbol,
            "sensitivity_mult": sensitivity_mult,
            "kelly_multiplier": kelly_multiplier,
            "ratio": float("nan"),
            "edge_annotation": "cost-friction-dominated-edge-n/a",
        }
    starting_equity = 10000.0
    if a0["n_trades"] > 0:
        per_trade_gross_edge_bps = (
            a0["total_gross_pnl"] / a0["n_trades"] / starting_equity * 10000
        )
    else:
        per_trade_gross_edge_bps = float("nan")
    if a1["n_trades"] > 0:
        per_trade_cost_bps = (
            a1["total_cost_usd"] / a1["n_trades"] / starting_equity * 10000
        )
    else:
        per_trade_cost_bps = float("nan")
    if per_trade_cost_bps > 0 and np.isfinite(per_trade_cost_bps):
        ratio = per_trade_gross_edge_bps / per_trade_cost_bps
    else:
        ratio = float("nan")
    a0_roi = a0["realized_roi_pct"]
    a1_roi = a1["realized_roi_pct"]
    if (
        a0_roi > 0 and a1_roi < 0
        and np.isfinite(ratio)
        and ratio >= _COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD
    ):
        edge_annotation = "cost-friction-dominated-edge-present"
    elif a0_roi <= 0 or (a0_roi > 0 and a1_roi >= 0):
        edge_annotation = "cost-friction-dominated-edge-absent"
    else:
        edge_annotation = "cost-friction-dominated-edge-marginal"
    return {
        "symbol": symbol,
        "sensitivity_mult": sensitivity_mult,
        "kelly_multiplier": kelly_multiplier,
        "a0_roi_pct": float(a0_roi),
        "a1_roi_pct": float(a1_roi),
        "a0_n_trades": int(a0["n_trades"]),
        "a1_n_trades": int(a1["n_trades"]),
        "per_trade_gross_edge_bps_eq": float(per_trade_gross_edge_bps),
        "per_trade_cost_bps_eq": float(per_trade_cost_bps),
        "ratio": float(ratio),
        "edge_annotation": edge_annotation,
        "crosses_threshold": bool(
            np.isfinite(ratio) and ratio >= _COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD
        ),
    }


def _evaluate_basket_h_1(
    per_symbol_results: list[dict[str, Any]],
    basket_results: list[dict[str, Any]],
    *,
    sensitivity_mult: float,
    kelly_multiplier: float = 0.25,
) -> dict[str, Any]:
    """Per-slip basket-level H_1 conjunctive criterion evaluation.

    Per H068 v2 design.md §1 H_1:
        (a) basket realized OOS ROI > 0 at A1 conservative-prior at
            corresponding sensitivity_mult
        (b) basket-aggregated MPPM(ρ=1) CI strictly excludes zero positively
        (c) per-symbol cost-friction-breakeven ratio ≥ 2 on ≥ 2 of 3 symbols
            (`cost-friction-dominated-edge-present` at basket level)
    """
    basket_a1 = next(
        (b for b in basket_results
         if b["sensitivity_mult"] == sensitivity_mult
         and b["kelly_multiplier"] == kelly_multiplier
         and b["cost_arm"] == "A1_conservative_prior"), None
    )
    if basket_a1 is None:
        return {
            "sensitivity_mult": sensitivity_mult,
            "kelly_multiplier": kelly_multiplier,
            "_error": "no basket A1 row at this cell",
        }
    # Per-symbol breakeven across the 3 symbols at this slip × kelly.
    per_sym_breakeven = [
        _compute_per_symbol_breakeven_ratio(
            per_symbol_results, symbol=sym,
            sensitivity_mult=sensitivity_mult,
            kelly_multiplier=kelly_multiplier,
        )
        for sym in _SYMBOLS
    ]
    n_clear_threshold = sum(1 for b in per_sym_breakeven if b.get("crosses_threshold", False))
    h_1_a = bool(basket_a1["basket_realized_roi_pct"] > 0)
    h_1_b = bool(
        basket_a1["basket_mppm_rho1_excludes_zero"]
        and basket_a1["basket_mppm_rho1"] > 0
    )
    h_1_c = bool(n_clear_threshold >= 2)
    h_1_conjunctive = h_1_a and h_1_b and h_1_c
    return {
        "sensitivity_mult": sensitivity_mult,
        "kelly_multiplier": kelly_multiplier,
        "h_1_a_basket_roi_pct": float(basket_a1["basket_realized_roi_pct"]),
        "h_1_a_meets": h_1_a,
        "h_1_b_basket_mppm_excludes_zero_pos": h_1_b,
        "h_1_c_n_symbols_clear_threshold": n_clear_threshold,
        "h_1_c_meets": h_1_c,
        "h_1_conjunctive_met": h_1_conjunctive,
        "per_symbol_breakeven": per_sym_breakeven,
    }


def _format_kpi_table(
    per_symbol_results: list[dict[str, Any]],
    basket_results: list[dict[str, Any]],
) -> str:
    """Two-section KPI table — per-symbol rows + basket-aggregated rows."""
    lines: list[str] = []
    lines.append("=" * 240)
    lines.append(
        "H068 v2 WALK-FORWARD — PER-SYMBOL + BASKET KPI METRICS TABLE "
        "(per design.md §13)"
    )
    lines.append("=" * 240)
    hdr = (
        f"{'Sym':<5} {'Slip':>6} {'Kelly':>6} {'Arm':<22} "
        f"{'OOS_ROI%':>9} {'MaxDD%':>8} {'W/L/Z':>14} "
        f"{'Sharpe':>8} {'Calmar':>8} {'PF':>6} {'R_mean':>7} "
        f"{'MPPM_lo':>8} {'MPPM_pt':>8} {'MPPM_hi':>8} {'tau3':>7} "
        f"{'n_trd':>6} {'cost$':>10} "
        f"{'subROI%':>9} {'subDD%':>7} "
        f"{'K6':>4} {'K7':>4} {'pwr':>4}"
    )
    lines.append("--- PER-SYMBOL ---")
    lines.append(hdr)
    lines.append("-" * 240)
    for r in per_symbol_results:
        sr_str = f"{r['sr_annualised']:.3f}" if r.get('sr_annualised') is not None else "n/a"
        calmar_str = f"{r['calmar']:.3f}" if r.get('calmar') is not None else "n/a"
        pf_str = f"{r['profit_factor']:.2f}" if r.get('profit_factor') is not None else "n/a"
        wlz = f"{r['wins']}/{r['losses']}/{r['zeros']}"
        pwr = "LOW" if r['underpowered'] else "ok"
        line = (
            f"{r['symbol']:<5} "
            f"{r['sensitivity_mult']:>6.2f} {r['kelly_multiplier']:>6.2f} "
            f"{r['cost_arm']:<22} "
            f"{r['realized_roi_pct']:>+8.2f}% {r['realized_max_dd_pct']:>+7.2f}% "
            f"{wlz:>14} "
            f"{sr_str:>8} {calmar_str:>8} {pf_str:>6} {r['r_multiple_mean']:>+7.3f} "
            f"{r['mppm_rho1_ci_low']:>+8.3f} {r['mppm_rho1']:>+8.3f} "
            f"{r['mppm_rho1_ci_high']:>+8.3f} "
            f"{r['l_skewness_tau3']:>+7.3f} "
            f"{r['n_trades']:>6} {r['total_cost_usd']:>10.2f} "
            f"{r['subwindow_realized_roi_pct']:>+8.2f}% "
            f"{r['subwindow_realized_max_dd_pct']:>+6.2f}% "
            f"{r['k6_trigger_count']:>4} {r['k7_trigger_count']:>4} {pwr:>4}"
        )
        lines.append(line)
    lines.append("--- BASKET-AGGREGATED ---")
    bhdr = (
        f"{'Slip':>6} {'Kelly':>6} {'Arm':<22} "
        f"{'B_ROI%':>9} {'B_MaxDD%':>9} {'B_W/L/Z':>16} "
        f"{'B_Sharpe':>10} {'B_Calmar':>10} "
        f"{'B_MPPM_lo':>10} {'B_MPPM_pt':>10} {'B_MPPM_hi':>10} "
        f"{'B_n_trd':>9} {'B_cost$':>12} {'pwr':>4}"
    )
    lines.append(bhdr)
    lines.append("-" * 240)
    for b in basket_results:
        b_sr = (
            f"{b['basket_sr_annualised']:.3f}"
            if b.get('basket_sr_annualised') is not None else "n/a"
        )
        b_calmar = (
            f"{b['basket_calmar']:.3f}"
            if b.get('basket_calmar') is not None else "n/a"
        )
        wlz = f"{b['basket_total_wins']}/{b['basket_total_losses']}/{b['basket_total_zeros']}"
        pwr = "LOW" if b['basket_underpowered'] else "ok"
        line = (
            f"{b['sensitivity_mult']:>6.2f} {b['kelly_multiplier']:>6.2f} "
            f"{b['cost_arm']:<22} "
            f"{b['basket_realized_roi_pct']:>+8.2f}% "
            f"{b['basket_realized_max_dd_pct']:>+8.2f}% "
            f"{wlz:>16} "
            f"{b_sr:>10} {b_calmar:>10} "
            f"{b['basket_mppm_rho1_ci_low']:>+10.3f} {b['basket_mppm_rho1']:>+10.3f} "
            f"{b['basket_mppm_rho1_ci_high']:>+10.3f} "
            f"{b['basket_total_trades']:>9} {b['basket_total_cost_usd']:>12.2f} "
            f"{pwr:>4}"
        )
        lines.append(line)
    lines.append("=" * 240)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="H068 v2 walk-forward orchestrator — 3-symbol basket {ES, MGC, SIL}",
    )
    parser.add_argument("--config", default=None, help="Path to H068_v2.yaml (informational; values inlined).")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--end-date",
        default="2026-05-15",
        help="OOS test end date (UTC) ISO format per design.md §2.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke mode: Kelly=0.25 only × 3 slip × 2 arms × 3 symbols = 18 cells.",
    )
    # ADR-0025 opt-in primitive flags per Phase O.13 deep-wire precedent.
    parser.add_argument(
        "--enable-kill-switch-runtime",
        action="store_true",
        help="ADR-0025 §D-1; default OFF preserves v2 numerical agreement.",
    )
    parser.add_argument(
        "--enable-equity-rebase-current",
        action="store_true",
        help="ADR-0025 §D-2; default OFF preserves H068 v2 fixed-equity parent-cell preservation.",
    )
    parser.add_argument(
        "--cost-model",
        choices=["none", "conservative_prior", "paper_trade_empirical"],
        default="none",
        help="ADR-0025 §D-3; H068 v2 sweep itself emits both A0 (cost-zero) + A1 cells; "
        "this flag forces a single cost-model on top of the sweep.",
    )
    parser.add_argument(
        "--zero-cost-reference-run-id",
        default=None,
        help="ADR-0028 §D-2 zero-cost reference cell run_id for cost-friction-edge annotation.",
    )
    parser.add_argument(
        "--zero-cost-reference-basket-pct",
        type=float,
        default=None,
        help="ADR-0028 §D-2 zero-cost reference basket ROI % for cost-friction-edge annotation.",
    )
    parser.add_argument(
        "--zero-cost-reference-sidecar-sha-prefix16",
        default=None,
        help="ADR-0028 §D-2 zero-cost reference sidecar SHA256 prefix-16 for provenance.",
    )
    args = parser.parse_args(argv)

    if args.substrate_path:
        substrate_root = Path(args.substrate_path).resolve()
    else:
        substrate_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"

    substrate_sha = _resolve_substrate_dataset_checksum()
    per_partition_shas = _compute_per_partition_shas(substrate_root, _SYMBOLS)

    # P1-H068-V2-REPROLOG-WIRE: RunContext per ADR-0017 §3 + ADR-0026 §D-2.
    with RunContext(
        phase="walk_forward",
        hypothesis_id="H068_v2",
        rng_seed=_RNG_SEED,
        dataset_checksums={
            "vendor_legacy_1min_roll_adjusted_output_frame_sha256": substrate_sha,
        },
        config_resolved_sha256=None,
    ) as ctx:
        assert ctx.log is not None
        run_id = ctx.log.run_id

        if args.output_dir:
            out_dir = Path(args.output_dir).resolve()
        else:
            out_dir = _REPO_ROOT / "artifacts" / "runs" / "H068_v2" / run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        start = pd.Timestamp("2020-01-01", tz="UTC")
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

        # Load all 3 symbols upfront.
        per_symbol_bars: dict[str, pd.DataFrame] = {}
        for sym in _SYMBOLS:
            _log.info("Loading %s [%s → %s]...", sym, start.date(), end_master.date())
            df_sym = _load_5min_bars(substrate_root, symbol=sym, start=start, end=end_master)
            _log.info(
                "  %s: %d 5-min bars (%d sessions)",
                sym, len(df_sym), df_sym["session_date_et"].nunique(),
            )
            per_symbol_bars[sym] = df_sym

        sweep_configs = _build_v2_sweep_configs(smoke=bool(args.smoke))
        _log.info(
            "Cell-grid: %d cells per symbol × %d symbols = %d total cells (smoke=%s)",
            len(sweep_configs), len(_SYMBOLS),
            len(sweep_configs) * len(_SYMBOLS), args.smoke,
        )

        per_symbol_results: list[dict[str, Any]] = []
        for sym in _SYMBOLS:
            df_5m = per_symbol_bars[sym]
            for cfg in sweep_configs:
                res = _run_v2_per_symbol_simulation(
                    df_5m=df_5m,
                    feature_config=feat_cfg,
                    k_atr=k_atr,
                    cfg=cfg,
                    symbol=sym,
                )
                per_symbol_results.append(res)
                _log.info(
                    "  %s slip=%.2f km=%.2f %s: end=$%.0f (%+.2f%%) MaxDD=%.2f%% "
                    "trades=%d r=%.3f τ3=%+.3f MPPM=%+.3f[%+.3f,%+.3f] K6=%d K7=%d %s",
                    sym, cfg.sensitivity_mult, cfg.kelly_multiplier, cfg.cost_arm,
                    res["realized_end_equity"], res["realized_roi_pct"],
                    res["realized_max_dd_pct"], res["n_trades"], res["r_multiple_mean"],
                    res["l_skewness_tau3"], res["mppm_rho1"],
                    res["mppm_rho1_ci_low"], res["mppm_rho1_ci_high"],
                    res["k6_trigger_count"], res["k7_trigger_count"],
                    res["power_annotation"],
                )

        # Aggregate to basket level per (slip × Kelly × cost_arm) cell.
        basket_results: list[dict[str, Any]] = []
        for sm in _SLIP_CELLS:
            for km in (_KELLY_CELLS if not args.smoke else (0.25,)):
                for arm in _COST_ARMS:
                    b = _aggregate_basket(
                        per_symbol_results,
                        sensitivity_mult=sm,
                        kelly_multiplier=km,
                        cost_arm=arm,
                    )
                    basket_results.append(b)
                    _log.info(
                        "  BASKET slip=%.2f km=%.2f %s: $%.0f (%+.2f%%) MaxDD=%.2f%% "
                        "trades=%d MPPM=%+.3f[%+.3f,%+.3f] %s",
                        sm, km, arm,
                        b.get("realized_end_basket_equity", 0.0),
                        b.get("basket_realized_roi_pct", 0.0),
                        b.get("basket_realized_max_dd_pct", 0.0),
                        b.get("basket_total_trades", 0),
                        b.get("basket_mppm_rho1", float("nan")),
                        b.get("basket_mppm_rho1_ci_low", float("nan")),
                        b.get("basket_mppm_rho1_ci_high", float("nan")),
                        b.get("basket_power_annotation", "n/a"),
                    )

        # Per-slip basket H_1 conjunctive evaluation (modal Kelly=0.25).
        h_1_per_slip = [
            _evaluate_basket_h_1(
                per_symbol_results, basket_results,
                sensitivity_mult=sm, kelly_multiplier=0.25,
            )
            for sm in _SLIP_CELLS
        ]

        # ADR-0028 §D-2 cost-friction-dominated-edge annotation at basket-level.
        if args.zero_cost_reference_basket_pct is not None:
            # Operator-supplied zero-cost reference.
            ref_basket_pct = float(args.zero_cost_reference_basket_pct)
            cost_arm_id = (
                "cost-conservative-prior" if args.cost_model == "conservative_prior"
                else ("cost-paper-trade-empirical" if args.cost_model == "paper_trade_empirical"
                      else "cost-zero")
            )
            # Pick the modal cell (slip=0.5, kelly=0.25, A1) as the "realized OOS"
            # anchor for the annotation; this is the parent-cell convention.
            modal_basket_a1 = next(
                (b for b in basket_results
                 if b["sensitivity_mult"] == 0.5
                 and b["kelly_multiplier"] == 0.25
                 and b["cost_arm"] == "A1_conservative_prior"),
                basket_results[0] if basket_results else None,
            )
            if modal_basket_a1 is not None:
                cfe = cost_friction_dominated_edge_annotation(
                    cost_model_annotation=cost_arm_id,
                    realized_oos_basket_pct=float(modal_basket_a1["basket_realized_roi_pct"]),
                    zero_cost_reference_cell={
                        "run_id": args.zero_cost_reference_run_id,
                        "basket_pct": ref_basket_pct,
                        "sidecar_sha_prefix16": args.zero_cost_reference_sidecar_sha_prefix16,
                    },
                )
                cost_friction_edge_block = build_cost_friction_edge_block(cfe)
            else:
                cost_friction_edge_block = {
                    "annotation": "cost-friction-dominated-edge-n/a",
                    "rationale": "no basket A1 cell available",
                }
        else:
            cost_friction_edge_block = {
                "annotation": "cost-friction-dominated-edge-n/a",
                "rationale": "no operator-supplied zero-cost reference cell",
            }

        # ---- promising-* annotation per ADR-0026 §D-3 ----
        promising_basket_cells = [
            b for b in basket_results
            if b.get("basket_mppm_rho1_excludes_zero", False)
            and b.get("basket_mppm_rho1", float("-inf")) > 0
        ]
        if promising_basket_cells:
            best = max(promising_basket_cells, key=lambda r: r["basket_mppm_rho1"])
            promising_annotation = (
                f"promising-basket-mppm-{best['cost_arm']}-{substrate_sha[:16]}-"
                f"slip{best['sensitivity_mult']:.2f}-km{best['kelly_multiplier']:.2f}"
            )
        else:
            promising_annotation = (
                f"not-promising-basket-mppm-cost-conservative-prior-{substrate_sha[:16]}"
            )

        kpi_table = _format_kpi_table(per_symbol_results, basket_results)
        print()
        print(kpi_table)
        print()
        print("Basket-level H_1 conjunctive criterion per slip cell (modal Kelly=0.25):")
        for h in h_1_per_slip:
            n_clear = h.get('h_1_c_n_symbols_clear_threshold', 0)
            verdict = "MET" if h.get('h_1_conjunctive_met', False) else "NOT-MET"
            print(
                f"  slip={h['sensitivity_mult']:.2f}: "
                f"a(ROI>0)={h.get('h_1_a_meets', False)} "
                f"b(MPPM-excl-zero-pos)={h.get('h_1_b_basket_mppm_excludes_zero_pos', False)} "
                f"c(≥2 of 3 ratio≥2)={h.get('h_1_c_meets', False)} "
                f"[{n_clear}/3] → {verdict}"
            )

        # Sidecar payload.
        payload = {
            "hypothesis_id": "H068_v2",
            "experiment": "walk_forward_basket_v1",
            "run_id": run_id,
            "smoke_mode": bool(args.smoke),
            "feature_cell": {
                "channel_n": feat_cfg.channel_n,
                "atr_n": feat_cfg.atr_n,
                "h_dwell": feat_cfg.h_dwell,
                "trend_id": feat_cfg.trend_id,
                "trend_id_lookback_l": feat_cfg.trend_id_lookback_l,
                "trend_id_threshold": feat_cfg.trend_id_threshold,
                "k_atr": k_atr,
            },
            "universe": list(_SYMBOLS),
            "per_symbol_multiplier": _PER_SYMBOL_MULTIPLIER,
            "per_symbol_capacity_cap": _PER_SYMBOL_CAPACITY_CAP,
            "starting_equity_per_symbol": 10000.0,
            "starting_equity_basket": 10000.0 * len(_SYMBOLS),
            "annualization_factor": _ANNUALIZATION_FACTOR,
            "rng_seed": _RNG_SEED,
            "n_bootstrap_ci": _N_BOOTSTRAP_CI,
            "n_min_trades_guard_per_symbol": _N_MIN_TRADES_GUARD_PER_SYMBOL,
            "n_min_trades_guard_basket": _N_MIN_TRADES_GUARD_BASKET,
            "cost_friction_edge_present_ratio_threshold": _COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD,
            "substrate_dataset_checksum": substrate_sha,
            "substrate_per_partition_shas": per_partition_shas,
            "abandonment_triggers_cli_flags": {
                "enable_kill_switch_runtime": bool(args.enable_kill_switch_runtime),
                "enable_equity_rebase_current": bool(args.enable_equity_rebase_current),
                "cost_model": args.cost_model,
            },
            "cost_friction_edge_basket_modal": cost_friction_edge_block,
            "configurations": [
                {
                    "name": c.name,
                    "sensitivity_mult": c.sensitivity_mult,
                    "kelly_multiplier": c.kelly_multiplier,
                    "cost_arm": c.cost_arm,
                    "use_current_equity_rebase": c.use_current_equity_rebase,
                } for c in sweep_configs
            ],
            "per_symbol_results": per_symbol_results,
            "basket_results": basket_results,
            "h_1_conjunctive_per_slip": h_1_per_slip,
            "promising_annotation": promising_annotation,
            "kill_switch_v1_enforcement_mode": "block",
            "kpi_table_text": kpi_table,
            "subwindow_definition": {
                "start": str(_SUBWINDOW_START),
                "end": str(_SUBWINDOW_END),
            },
            "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
        }
        sidecar_path = out_dir / "sidecar.json"
        sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode(
            "utf-8"
        )
        sidecar_path.write_bytes(sidecar_bytes)
        sha = hashlib.sha256(sidecar_bytes).hexdigest()
        (out_dir / "scientific_payload_sha256.txt").write_text(sha + "\n", encoding="utf-8")
        (out_dir / "kpi_table.txt").write_text(kpi_table, encoding="utf-8")

        ctx.set_model_hash(sha)

        _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])
        _log.info("kpi_table=%s", out_dir / "kpi_table.txt")
        print(f"sidecar: {sidecar_path}")
        print(f"sha256:  {sha}")
        print(f"run_id:  {run_id}")
        print(f"promising_annotation: {promising_annotation}")
    return 0


if __name__ == "__main__":
    # ADR-0009 BLAS thread-pinning carry-forward (canonical block from
    # scripts/run_h052a_walk_forward.py:915-942).
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
