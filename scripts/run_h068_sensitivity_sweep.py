"""H068 slip-sensitivity sweep — H065 v2 M_inf-ES parent cell + sub-1-tick slip cost-model axis.

Per H068 design.md §1 + §5 + §6: applies the canonical Donchian-channel breakout
signal preserved verbatim from H062 + H065 v2 (channel_n=120, k_atr=2.0,
atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; no TP overlay, i.e. M=∞)
on ES standalone, with sub-1-tick slip empirical sensitivity sweep
`sensitivity_mult ∈ {0.25, 0.5, 1.0}` ticks as the primary cost-reduction axis.
ADR-0028 §D-2 two-cost-arm emission: A0 zero-cost reference + A1
`nt8_realistic_v1(sensitivity_mult=*)` conservative-prior at each cell.

Cell-budget per design.md §5 cell-grid:
    sensitivity_mult ∈ {0.25, 0.5, 1.0}              # 3 slip cells
    kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}  # 6 Kelly cells
    cost_arm        ∈ {A0_zero, A1_conservative_prior}  # 2 cost arms
    = 36 cells (one symbol = ES)
Well under the ADR-0027 §D-2 v1 cap of 1000.

Per-trade exit precedence within a bar (PIT-resolved per H062 + H065 §4):
    1. gap-through-stop at bar-t open
    2. stop hit during bar (low ≤ SL_long or high ≥ SL_short)
    3. opposite-channel break at bar close
    4. EOD-flatten / session-rollover
(NO TP step — M=∞ per H065 v2 M_inf_h062_v1_fixed-ES parent cell preservation.)

Cost-model integration (design.md §6):
    A0 (zero-cost): no cost subtraction; per-trade pnl == gross pnl.
    A1 (conservative-prior, sensitivity_mult parameterised): cost subtracted
        from per-trade gross pnl on close. Cost computed via
        `nt8_realistic.NT8RealisticCostModel.round_trip_cost_usd(symbol="ES",
        n_contracts=position.size)` per ADR-0025 §D-3 API contract.

ES fee schedule at sensitivity_mult cells (UNCHANGED from pre-Phase-O.16 per
[config/instruments.yaml line 50]; CME-verified effective 2024-02):
    sensitivity_mult=1.0 (baseline):   fixed $2.05/side × 2 + slip $12.50/side × 2 = $29.10/rt
    sensitivity_mult=0.5 (mid):        fixed $2.05/side × 2 + slip  $6.25/side × 2 = $16.60/rt (-43%)
    sensitivity_mult=0.25 (aggressive):fixed $2.05/side × 2 + slip  $3.125/side × 2 = $10.35/rt (-64%)

Per H068 design.md §1.4: cost-friction-breakeven ratio rises from 1.27 at the
baseline to ~2.22 at sensitivity_mult=0.5 (JUST CROSSES the ADR-0028 §D-2
cost-friction-dominated-edge-present threshold) and ~3.56 at
sensitivity_mult=0.25. The H_1 question is whether the realized OOS ratio
matches this pre-empirical structural prediction.

Outputs:
    artifacts/runs/H068/<run_id>/sidecar.json — comparison sidecar with all 36
        cell rows + 3 per-slip-cell aggregate annotations + per-partition SHAs.
    logs/reproducibility/<run_id>.json — 13-field ReproLog per ADR-0017 §3.

Per-cell metric panel per ADR-0014 §3.2 + ADR-0028 §D-2 trigger semantics +
ADR-0026 §D-3 promising-* annotation.

Per ADR-0027 §D-2: cell-budget 36 << 1000 cap.

Per H068 design.md §11.1: K-4 + K-6 + K-7 enabled at v1 in block-mode (Task #20
finding that size-down doesn't recover cost-dominated catastrophes); K-3
vacuous at 1-lot v1 sizing; K-5 N/A (ES standalone; no MES in H068 universe).

Per H068 design.md §11.2 `P1-H068-N-MIN-TRADES-GUARD`: cells with n_trades < 50
post-cost-light-filtering emit `power-margin-low` annotation per ADR-0014
§3.2 Table 8 + flag the cell in the per-slip-Pareto-front aggregation.
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
_log = logging.getLogger("h068_sensitivity_sweep")


# justify: ES multiplier per CME ES product spec ($50/point); single-symbol
# H068 v1 per design.md §2 universe binding.
_ES_MULTIPLIER: float = 50.0

# justify: ES retail-tier capacity ceiling per ADR-0001 + H062/H065 design.md
# §11.1 K-4 binding; v1 uses Kelly-derived sizing typically <20 so cap is
# informational. Block-mode per H068 design.md §11.1 ADR-0028 §D-1 default.
_ES_CAPACITY_CAP: int = 20

# Sub-window cutoff for "2026-AprMay" mandatory reporting per ADR-0026 §D-1 §0
# 3-component summary header component 2.
_SUBWINDOW_START = pd.Timestamp("2026-04-01", tz="UTC").date()
_SUBWINDOW_END = pd.Timestamp("2026-05-15", tz="UTC").date()

# justify: bootstrap CI defaults per H068 design.md §12 reproducibility binding +
# RNG seed 20260519 per design.md §12 + project-canonical 252 sessions/year +
# 1000 bootstrap replicates per H062 v1 + H065 v2 precedent.
_RNG_SEED = 20260519
_N_BOOTSTRAP_CI = 1000
_ANNUALIZATION_FACTOR = 252.0

# H068 v1 cell-grid per design.md §5
_SLIP_CELLS: tuple[float, ...] = (0.25, 0.5, 1.0)
_KELLY_CELLS: tuple[float, ...] = (0.25, 0.5, 1.0, 1.5, 2.0, 2.5)
_COST_ARMS: tuple[str, ...] = ("A0_zero", "A1_conservative_prior")

# justify: per H068 design.md §9 + §11.2 `P1-H068-N-MIN-TRADES-GUARD` —
# Tharp 1998 *practitioner* n ≥ 30 threshold for R-multiple-distribution CI;
# H068 sets the n_min_trades guard at 50 to ensure tractable inferential power.
_N_MIN_TRADES_GUARD: int = 50

# justify: ADR-0028 §D-2 cost-friction-dominated-edge-present ratio threshold;
# pre-empirical predictions in H068 design.md §1.4: at sensitivity_mult=0.5
# ratio ≈ 2.22 just crosses; at sensitivity_mult=0.25 ratio ≈ 3.56 well above.
_COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD: float = 2.0


def _resolve_substrate_dataset_checksum() -> str:
    """Read the most recent vendor_legacy_1min_roll_adjusted provenance JSON.

    Per H065 v2 corrigendum precedent — sidecar `substrate_dataset_checksum`
    must always match the substrate the sweep actually consumed.
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


def _compute_per_partition_shas_es(substrate_root: Path) -> dict[str, str]:
    """Compute per-partition SHA256 for the ES roll-adjusted partitions.

    Per H068 design.md §11.2 `P1-H068-SUBSTRATE-PER-PARTITION-SHA-EMIT` —
    enumerate the per-ES-partition SHAs at orchestrator start to bind the
    H068 v1 emission to the exact substrate-state observed at sweep time.
    """
    es_root = substrate_root / "symbol=ES"
    if not es_root.exists():
        return {"_error": f"ES partition root not found at {es_root}"}
    parts = sorted(es_root.glob("year=*/part-*.parquet"))
    out: dict[str, str] = {}
    for p in parts:
        rel = p.relative_to(substrate_root)
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        out[str(rel).replace("\\", "/")] = sha
    return out


@dataclass(frozen=True)
class SensitivityConfig:
    """H068 cell-grid configuration cell.

    sensitivity_mult: slip-per-side multiplier ∈ {0.25, 0.5, 1.0} (design.md §6).
    kelly_multiplier: Kelly multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} (ADR-0018 D-2).
    cost_arm: "A0_zero" (no cost subtraction) or "A1_conservative_prior" (cost
        from `nt8_realistic_v1`).
    use_current_equity_rebase: False (H068 v1 preserves H062 v1 modal fixed-equity
        rebase per H065 v2 M_inf_h062_v1_fixed-ES anchor preservation; design.md §13
        "v1 reports fixed-equity rebase per H062 v1 modal").
    """

    sensitivity_mult: float
    kelly_multiplier: float
    cost_arm: str
    use_current_equity_rebase: bool

    @property
    def name(self) -> str:
        return (
            f"slip{self.sensitivity_mult:.2f}_kelly{self.kelly_multiplier:.2f}_{self.cost_arm}"
        )

    @property
    def is_a0_zero(self) -> bool:
        return self.cost_arm == "A0_zero"

    @property
    def description(self) -> str:
        slip_label = {0.25: "0.25-tick aggressive", 0.5: "0.5-tick mid", 1.0: "1.0-tick baseline"}.get(
            self.sensitivity_mult, f"{self.sensitivity_mult:.2f}-tick"
        )
        cost_label = "zero-cost reference" if self.is_a0_zero else "conservative-prior cost"
        return (
            f"sensitivity_mult={self.sensitivity_mult:.2f} ({slip_label}) × "
            f"kelly_mult={self.kelly_multiplier:.2f} × {cost_label}"
        )


def _build_sweep_configs() -> list[SensitivityConfig]:
    """Build the H068 v1 36-cell sweep grid per design.md §5 + §6."""
    out: list[SensitivityConfig] = []
    for sm in _SLIP_CELLS:
        for km in _KELLY_CELLS:
            for arm in _COST_ARMS:
                out.append(
                    SensitivityConfig(
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


def _load_5min_bars_es(
    substrate_root: Path,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Load ES roll-adjusted bars, resample to 5-min per H062/H065 cadence."""
    glob_pat = str(substrate_root / "symbol=ES" / "year=*" / "part-*.parquet")
    lf = pl.scan_parquet(glob_pat).select(
        pl.col("ts_event"),
        pl.col("open"),
        pl.col("high"),
        pl.col("low"),
        pl.col("close"),
    )
    df = lf.collect().to_pandas()
    if df.empty:
        raise RuntimeError(f"ES: empty substrate at {glob_pat}")
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df = df.sort_values("ts_event").reset_index(drop=True)
    mask = (df["ts_event"] >= start) & (df["ts_event"] <= end)
    df = df.loc[mask].copy()
    if df.empty:
        raise RuntimeError("ES: substrate empty after filter")
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


def _run_sensitivity_simulation(
    *,
    df_5m: pd.DataFrame,
    feature_config: H062FeatureConfig,
    k_atr: float,
    cfg: SensitivityConfig,
    starting_equity: float = 10000.0,
    eod_flatten_minutes_from_open: int = 360,
) -> dict[str, Any]:
    """H068 simulator with slip-sensitivity cost-model integration.

    Per H068 design.md §4 exit precedence within bar (no TP step; M=∞):
        1. gap-through-stop at open
        2. stop-hit during bar (low ≤ SL_long or high ≥ SL_short)
        3. opposite-channel break at close
        4. EOD-flatten / session-rollover

    Cost-model integration per design.md §6:
        A0 (zero-cost): per-trade pnl = gross pnl, no subtraction.
        A1 (conservative-prior): per-trade pnl = gross pnl - cost via
            NT8RealisticCostModel(sensitivity_mult=cfg.sensitivity_mult)
            .round_trip_cost_usd(symbol="ES", n_contracts=size).

    Returns dict with per-trade log + per-session aggregate + metrics +
    K-6/K-7 trigger telemetry.
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

    cost_model: NT8RealisticCostModel | None = None
    if not cfg.is_a0_zero:
        cost_model = NT8RealisticCostModel(
            sensitivity_mult=cfg.sensitivity_mult,
            calibration_source="conservative_prior",
        )

    multiplier = _ES_MULTIPLIER
    cap = _ES_CAPACITY_CAP

    equity = starting_equity
    trade_log: list[dict] = []
    equity_curve: list[float] = [starting_equity]
    n_ruin_events = 0

    session_starts: dict[object, int] = {}
    for t in range(n_bars):
        sd = session_dates[t]
        if sd not in session_starts:
            session_starts[sd] = t

    # K-6/K-7 trigger counters per H068 design.md §11.1 block-mode default.
    # K-6: -2% of session-start equity → block new entries this session.
    # K-7: -5% of week-start equity → block new entries this week.
    # justify: ADR-0028 §D-1 default; Task #20 size-down empirical finding
    # confirms block-mode appropriate for cost-dominated trade families.
    k6_triggered_sessions: set[object] = set()
    k7_triggered_weeks: set[tuple[int, int]] = set()  # (year, iso_week)
    k6_trigger_count: int = 0
    k7_trigger_count: int = 0

    # Track session-start + week-start equity for K-6/K-7 evaluation.
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

    def _close_position(
        exit_idx: int,
        exit_price: float,
        reason: str,
    ) -> None:
        nonlocal position, equity, n_ruin_events
        if position is None:
            return
        gross_pnl = (
            position.side * (exit_price - position.entry_price)
            * multiplier * position.size
        )
        # Cost-arm subtraction per H068 design.md §6.
        if cost_model is not None:
            cost_usd = cost_model.round_trip_cost_usd("ES", n_contracts=position.size)
        else:
            cost_usd = 0.0
        net_pnl = gross_pnl - cost_usd
        r_mult = net_pnl / position.r_dollar if position.r_dollar > 0 else 0.0
        equity += net_pnl
        equity_curve.append(equity)
        trade_log.append({
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
        # Opposite-channel break at bar close (M=∞; no TP step)
        ev = int(feats.filtered_events[t])
        if (position.side == 1 and ev == -1) or (position.side == -1 and ev == 1):
            _close_position(t, float(close[t]), "opposite_channel_break")
            return True
        # EOD flatten / session-rollover
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

        # Track session-start + week-start equity for K-6/K-7.
        if bar_session not in session_start_equity:
            session_start_equity[bar_session] = equity
        wk = _iso_week_key(bar_session)
        if wk not in week_start_equity:
            week_start_equity[wk] = equity

        # K-6 block-mode (design.md §11.1): if -2% of session-start hit, skip.
        ss_eq = session_start_equity[bar_session]
        if ss_eq > 0 and (equity - ss_eq) / ss_eq <= -0.02:
            if bar_session not in k6_triggered_sessions:
                k6_triggered_sessions.add(bar_session)
                k6_trigger_count += 1
            return
        # K-7 block-mode: if -5% of week-start hit, skip.
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
        # H068 v1 fixed-equity rebase per H062 v1 modal (design.md §13 +
        # H065 v2 M_inf_h062_v1_fixed-ES anchor preservation).
        # justify: per H068 design.md §11.1 row "Equity rebase: FIXED-equity per
        # H065 v2 M_inf_h062_v1_fixed-ES parent cell preservation"; current-
        # equity rebase deferred to v3 per `P1-H068-V3-CURRENT-EQUITY-REBASE`.
        eq_for_sizing = starting_equity if not cfg.use_current_equity_rebase else equity
        # justify: risk_budget_pct = 0.01 per H062 v1 + H065 v2 modal; preserved
        # infrastructure per ADR-0027 §D-4 single-axis-genetic-cross discipline.
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
    for tr in trade_log:
        exit_sd = tr["exit_session_date"]
        if (
            exit_sd not in session_eq_at_close
            or tr["exit_idx"] > session_eq_at_close.get(f"_max_idx_{exit_sd}", -1)
        ):
            session_eq_at_close[exit_sd] = tr["equity_post_trade"]
            session_eq_at_close[f"_max_idx_{exit_sd}"] = tr["exit_idx"]
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

    # ---- Sub-window: 2026-04-01 → 2026-05-15 ----
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

    # ---- MPPM(ρ=1) on per-session log-returns ----
    if session_log_ret_arr.size >= 4:
        # justify: H062 v3 critical bug fix per Phase O.10 — mppm_rho_1 expects
        # simple returns r_t > -1; convert log-returns via expm1 (clipped to
        # avoid float overflow at catastrophic single-session log-ret values).
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
            _log.warning("MPPM point failed: %s", e)
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
            _log.warning("MPPM CI failed: %s", e)
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
            _log.warning("L-skew CI failed: %s", e)
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
            _log.warning("R-mult CI failed: %s", e)
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
            calmar = float(
                calmar_ratio(session_log_ret_arr, annualization_factor=_ANNUALIZATION_FACTOR)
            )
        except Exception:
            calmar = float("nan")
    else:
        calmar = float("nan")

    # ---- Aggregate cost telemetry ----
    total_cost_usd = float(sum(tr["cost_usd"] for tr in trade_log))
    total_gross_pnl = float(sum(tr["gross_pnl"] for tr in trade_log))
    total_net_pnl = float(sum(tr["pnl"] for tr in trade_log))

    # ---- Power-margin annotation ----
    underpowered = n_trades < _N_MIN_TRADES_GUARD
    power_annotation = (
        f"underpowered-n-trades-{n_trades}-below-50"
        if underpowered
        else "power-margin-ok"
    )

    return {
        "symbol": "ES",
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
        "total_cost_usd": total_cost_usd,
        "total_gross_pnl": total_gross_pnl,
        "total_net_pnl": total_net_pnl,
        # K-6/K-7 trigger telemetry (block-mode default per design.md §11.1)
        "k6_trigger_count": k6_trigger_count,
        "k7_trigger_count": k7_trigger_count,
        "k6_triggered_sessions": len(k6_triggered_sessions),
        "k7_triggered_weeks": len(k7_triggered_weeks),
        # Sub-window 2026-04-01 → 2026-05-15
        "subwindow_starting_equity": sub_starting_eq,
        "subwindow_realized_end_equity": sub_realized_end,
        "subwindow_realized_roi_pct": sub_realized_roi_pct,
        "subwindow_realized_max_dd_pct": sub_max_dd_pct,
        "subwindow_wins": sub_wins,
        "subwindow_losses": sub_losses,
        "subwindow_zeros": sub_zeros,
        "subwindow_n_trades": len(sub_trades),
        # Power annotation per design.md §11.2 P1-H068-N-MIN-TRADES-GUARD
        "underpowered": underpowered,
        "power_annotation": power_annotation,
        # Per-session arrays (for downstream MPV / meta-portfolio aggregation)
        "session_log_returns": session_log_ret_arr.tolist(),
        "session_pnls": session_pnl_arr.tolist(),
        "session_dates": [str(sd) for sd in session_dates_ordered],
    }


def _compute_cost_friction_breakeven_ratio_per_slip(
    rows: list[dict[str, Any]],
    sensitivity_mult: float,
) -> dict[str, Any]:
    """Per H068 design.md §6 + ADR-0028 §D-2 — cost-friction-breakeven ratio.

    Compares the A0 zero-cost reference to the A1 conservative-prior cell at
    the same (slip × Kelly) cell. Ratio = (A0 gross_edge_bps_eq) / (A1 cost_bps_eq).

    The cost-friction-dominated-edge annotation:
      - "cost-friction-dominated-edge-present" if A0 ROI > 0 AND A1 ROI < 0 AND ratio ≥ 2
      - "cost-friction-dominated-edge-absent" if A1 cell does NOT flip A0 sign
      - "cost-friction-dominated-edge-n/a" if A0 cell not emitted
    """
    a0_rows = [
        r for r in rows
        if r["sensitivity_mult"] == sensitivity_mult and r["cost_arm"] == "A0_zero"
    ]
    a1_rows = [
        r for r in rows
        if r["sensitivity_mult"] == sensitivity_mult and r["cost_arm"] == "A1_conservative_prior"
    ]
    # Pick the Kelly cell with most trades (modal selection for per-slip ratio)
    # justify: per H068 design.md §1.4 the cost-friction-breakeven ratio anchors
    # on the parent cell at quarter-Kelly (matches H065 v2 modal); we report
    # the modal Kelly cell as the load-bearing reference.
    if not a0_rows or not a1_rows:
        return {
            "sensitivity_mult": sensitivity_mult,
            "ratio": float("nan"),
            "edge_annotation": "cost-friction-dominated-edge-n/a",
        }
    # Find the quarter-Kelly Kelly=0.25 row (parent-modal reference) if exists
    def _find_modal(arm_rows: list[dict[str, Any]]) -> dict[str, Any]:
        for r in arm_rows:
            if r["kelly_multiplier"] == 0.25:
                return r
        return arm_rows[0]
    a0 = _find_modal(a0_rows)
    a1 = _find_modal(a1_rows)
    starting_equity = 10000.0
    # Per-trade gross-edge in bps-of-equity = total_gross_pnl / n_trades / starting_equity * 10000
    if a0["n_trades"] > 0:
        per_trade_gross_edge_bps_eq = (
            a0["total_gross_pnl"] / a0["n_trades"] / starting_equity * 10000
        )
    else:
        per_trade_gross_edge_bps_eq = float("nan")
    if a1["n_trades"] > 0:
        # cost per trade = total_cost_usd / n_trades
        per_trade_cost_bps_eq = (
            a1["total_cost_usd"] / a1["n_trades"] / starting_equity * 10000
        )
    else:
        per_trade_cost_bps_eq = float("nan")
    if per_trade_cost_bps_eq > 0 and np.isfinite(per_trade_cost_bps_eq):
        ratio = per_trade_gross_edge_bps_eq / per_trade_cost_bps_eq
    else:
        ratio = float("nan")
    # Annotation
    a0_roi = a0["realized_roi_pct"]
    a1_roi = a1["realized_roi_pct"]
    if a0_roi > 0 and a1_roi < 0 and np.isfinite(ratio) and ratio >= _COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD:
        edge_annotation = "cost-friction-dominated-edge-present"
    elif a0_roi <= 0 or (a0_roi > 0 and a1_roi >= 0):
        edge_annotation = "cost-friction-dominated-edge-absent"
    else:
        edge_annotation = "cost-friction-dominated-edge-marginal"
    return {
        "sensitivity_mult": sensitivity_mult,
        "kelly_multiplier_modal": a0["kelly_multiplier"],
        "a0_roi_pct": float(a0_roi),
        "a1_roi_pct": float(a1_roi),
        "a0_n_trades": int(a0["n_trades"]),
        "a1_n_trades": int(a1["n_trades"]),
        "per_trade_gross_edge_bps_eq": float(per_trade_gross_edge_bps_eq),
        "per_trade_cost_bps_eq": float(per_trade_cost_bps_eq),
        "ratio": float(ratio),
        "edge_annotation": edge_annotation,
        "crosses_threshold": bool(
            np.isfinite(ratio) and ratio >= _COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD
        ),
    }


def _format_kpi_table(rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("=" * 220)
    lines.append("H068 SLIP-SENSITIVITY SWEEP — KPI METRICS TABLE (per design.md §13)")
    lines.append("=" * 220)
    hdr = (
        f"{'Slip':>6} {'Kelly':>6} {'Arm':<22} "
        f"{'OOS_ROI%':>9} {'MaxDD%':>8} {'W/L/Z':>14} "
        f"{'Sharpe':>8} {'Calmar':>8} {'PF':>6} {'R_mean':>7} "
        f"{'MPPM_lo':>8} {'MPPM_pt':>8} {'MPPM_hi':>8} {'tau3':>7} "
        f"{'n_trd':>6} {'cost$':>10} "
        f"{'subROI%':>9} {'subDD%':>7} "
        f"{'K6':>4} {'K7':>4} {'pwr':>4}"
    )
    lines.append(hdr)
    lines.append("-" * 220)
    for r in rows:
        sr_str = f"{r['sr_annualised']:.3f}" if r.get('sr_annualised') is not None else "n/a"
        calmar_str = f"{r['calmar']:.3f}" if r.get('calmar') is not None else "n/a"
        pf_str = f"{r['profit_factor']:.2f}" if r.get('profit_factor') is not None else "n/a"
        wlz = f"{r['wins']}/{r['losses']}/{r['zeros']}"
        pwr = "LOW" if r['underpowered'] else "ok"
        line = (
            f"{r['sensitivity_mult']:>6.2f} {r['kelly_multiplier']:>6.2f} "
            f"{r['cost_arm']:<22} "
            f"{r['realized_roi_pct']:>+8.2f}% {r['realized_max_dd_pct']:>+7.2f}% "
            f"{wlz:>14} "
            f"{sr_str:>8} {calmar_str:>8} {pf_str:>6} {r['r_multiple_mean']:>+7.3f} "
            f"{r['mppm_rho1_ci_low']:>+8.3f} {r['mppm_rho1']:>+8.3f} {r['mppm_rho1_ci_high']:>+8.3f} "
            f"{r['l_skewness_tau3']:>+7.3f} "
            f"{r['n_trades']:>6} {r['total_cost_usd']:>10.2f} "
            f"{r['subwindow_realized_roi_pct']:>+8.2f}% {r['subwindow_realized_max_dd_pct']:>+6.2f}% "
            f"{r['k6_trigger_count']:>4} {r['k7_trigger_count']:>4} {pwr:>4}"
        )
        lines.append(line)
    lines.append("=" * 220)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H068 slip-sensitivity sweep")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--end-date",
        default="2026-05-15",
        help="OOS test end date (UTC) ISO format.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke mode: shortened cell-grid (1 Kelly × 3 slip × 2 arms = 6 cells).",
    )
    args = parser.parse_args(argv)

    if args.substrate_path:
        substrate_root = Path(args.substrate_path).resolve()
    else:
        substrate_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"

    substrate_sha = _resolve_substrate_dataset_checksum()
    per_partition_shas = _compute_per_partition_shas_es(substrate_root)

    # P1-H068-REPROLOG-WIRE: RunContext per ADR-0017 §3 + ADR-0026 §D-2.
    with RunContext(
        phase="walk_forward",
        hypothesis_id="H068",
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
            out_dir = _REPO_ROOT / "artifacts" / "runs" / "H068" / run_id
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

        _log.info("Loading ES [%s → %s]...", start.date(), end_master.date())
        df_5m = _load_5min_bars_es(substrate_root, start=start, end=end_master)
        _log.info(
            "  ES: %d 5-min bars (%d sessions)",
            len(df_5m),
            df_5m["session_date_et"].nunique(),
        )

        sweep_configs = _build_sweep_configs()
        if args.smoke:
            # Smoke mode: only Kelly=0.25 cell + all 3 slip × 2 arms = 6 cells
            sweep_configs = [c for c in sweep_configs if c.kelly_multiplier == 0.25]
        _log.info("Cell-grid: %d cells (smoke=%s)", len(sweep_configs), args.smoke)

        all_rows: list[dict[str, Any]] = []
        for cfg in sweep_configs:
            res = _run_sensitivity_simulation(
                df_5m=df_5m,
                feature_config=feat_cfg,
                k_atr=k_atr,
                cfg=cfg,
            )
            all_rows.append(res)
            mppm_excl = (
                "MPPM_EXCL_ZERO_POS"
                if res["mppm_rho1_excludes_zero"] and res["mppm_rho1"] > 0
                else ("ci-cov-zero" if not res["mppm_rho1_excludes_zero"] else "MPPM_EXCL_ZERO_NEG")
            )
            _log.info(
                "  slip=%.2f km=%.2f %s: end=$%.0f (%+.2f%%) MaxDD=%.2f%% trades=%d r=%.3f τ3=%+.3f MPPM=%+.3f[%+.3f,%+.3f] %s K6=%d K7=%d %s",
                cfg.sensitivity_mult, cfg.kelly_multiplier, cfg.cost_arm,
                res["realized_end_equity"], res["realized_roi_pct"], res["realized_max_dd_pct"],
                res["n_trades"], res["r_multiple_mean"], res["l_skewness_tau3"],
                res["mppm_rho1"], res["mppm_rho1_ci_low"], res["mppm_rho1_ci_high"],
                mppm_excl,
                res["k6_trigger_count"], res["k7_trigger_count"],
                res["power_annotation"],
            )

        # Per-slip cost-friction-breakeven ratio + edge-annotation
        breakeven_per_slip = [
            _compute_cost_friction_breakeven_ratio_per_slip(all_rows, sm)
            for sm in _SLIP_CELLS
        ]

        kpi_table = _format_kpi_table(all_rows)
        print()
        print(kpi_table)
        print()
        print("Cost-friction-breakeven ratio per slip cell (modal Kelly=0.25):")
        for be in breakeven_per_slip:
            print(
                f"  slip={be['sensitivity_mult']:.2f}: ratio={be.get('ratio', float('nan')):.3f} "
                f"A0_ROI={be.get('a0_roi_pct', 0):+.2f}%  A1_ROI={be.get('a1_roi_pct', 0):+.2f}%  "
                f"edge_annotation={be['edge_annotation']}"
            )
        print()

        # Pareto-front aggregation per design.md §13: for each slip cell,
        # examine the H_1 conjunctive criterion (realized ROI > 0 AND MPPM CI
        # excludes zero positively AND ratio ≥ 2).
        h_1_per_slip: list[dict[str, Any]] = []
        for sm in _SLIP_CELLS:
            be = next(b for b in breakeven_per_slip if b["sensitivity_mult"] == sm)
            # Modal Kelly=0.25 A1 row
            mod_a1 = next(
                (r for r in all_rows
                 if r["sensitivity_mult"] == sm
                 and r["cost_arm"] == "A1_conservative_prior"
                 and r["kelly_multiplier"] == 0.25), None
            )
            if mod_a1 is None:
                continue
            h_1_per_slip.append({
                "sensitivity_mult": sm,
                "kelly_multiplier": 0.25,
                "h_1_a_realized_roi_pct": float(mod_a1["realized_roi_pct"]),
                "h_1_a_meets": bool(mod_a1["realized_roi_pct"] > 0),
                "h_1_b_mppm_excludes_zero_pos": bool(
                    mod_a1["mppm_rho1_excludes_zero"] and mod_a1["mppm_rho1"] > 0
                ),
                "h_1_c_ratio_ge_2": bool(be.get("crosses_threshold", False)),
                "h_1_conjunctive_met": bool(
                    mod_a1["realized_roi_pct"] > 0
                    and mod_a1["mppm_rho1_excludes_zero"]
                    and mod_a1["mppm_rho1"] > 0
                    and be.get("crosses_threshold", False)
                ),
                "edge_annotation": be["edge_annotation"],
                "underpowered": bool(mod_a1["underpowered"]),
            })

        # Build the promising-* annotation per ADR-0026 §D-3 if any cell strictly
        # excludes zero positively at MPPM.
        promising_cells = [r for r in all_rows if r["mppm_rho1_excludes_zero"] and r["mppm_rho1"] > 0]
        if promising_cells:
            best = max(promising_cells, key=lambda r: r["mppm_rho1"])
            promising_annotation = (
                f"promising-mppm-cost-{best['cost_arm']}-{substrate_sha[:16]}-"
                f"slip{best['sensitivity_mult']:.2f}-km{best['kelly_multiplier']:.2f}"
            )
        else:
            promising_annotation = "promising-mppm-none"

        # Sidecar payload
        payload = {
            "hypothesis_id": "H068",
            "experiment": "slip_sensitivity_sweep_v1",
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
            "starting_equity": 10000.0,
            "annualization_factor": _ANNUALIZATION_FACTOR,
            "rng_seed": _RNG_SEED,
            "n_bootstrap_ci": _N_BOOTSTRAP_CI,
            "n_min_trades_guard": _N_MIN_TRADES_GUARD,
            "cost_friction_edge_present_ratio_threshold": _COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD,
            "substrate_dataset_checksum": substrate_sha,
            "substrate_per_partition_shas_es": per_partition_shas,
            "configurations": [
                {
                    "name": c.name,
                    "sensitivity_mult": c.sensitivity_mult,
                    "kelly_multiplier": c.kelly_multiplier,
                    "cost_arm": c.cost_arm,
                    "use_current_equity_rebase": c.use_current_equity_rebase,
                    "description": c.description,
                } for c in sweep_configs
            ],
            "per_cell_results": all_rows,
            "breakeven_per_slip": breakeven_per_slip,
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
        sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        sidecar_path.write_bytes(sidecar_bytes)
        sha = hashlib.sha256(sidecar_bytes).hexdigest()
        (out_dir / "scientific_payload_sha256.txt").write_text(sha + "\n", encoding="utf-8")
        (out_dir / "kpi_table.txt").write_text(kpi_table, encoding="utf-8")

        # Bind model_hash to scientific_payload_sha256 for ReproLog integrity
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
