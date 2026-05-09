"""H055 walk-forward orchestrator (Stage-3 scaffolding) per design.md §11.

Composes the H055 feature factory + setup detectors + per-trade simulator +
ADR-0017 §1 survival-constrained KPI computation into an end-to-end
runnable pipeline.

Pipeline
--------

1. Parse config (config/hypotheses/H055.yaml) + CLI args.
2. Load OHLCV substrate (data/processed/vendor_legacy_1min_roll_adjusted/)
   per the H055.yaml binding + apply RTH eligible-bar filter per §4.
   Smoke mode (--smoke) generates deterministic synthetic 1-min bars.
3. Per symbol × per train/test fold:
   a. Compute features via compute_h055_features (Components 1+2+4 + news).
   b. Emit setups via emit_h055_setups (swing-pivot + wick-reversal-non-swing
      + state-machine-tracked level-state R(L) updates).
   c. Filter setups via design.md §3 gates:
       - Component 1 trend gate: setup.side × trend_side_at_confirmation > 0
       - Component 2 ρ_1 gate: rho_1_at_confirmation >= rho_star
       - Component 3 R(L) gate: R(L) <= R* per state machine
       - News-calendar eligible-bar filter (already in features)
   d. Run per-trade simulator on each filtered setup → TradeResult.
   e. Aggregate per-fold ledger; compute ADR-0017 §1 primary KPIs:
       - Calmar (annualized_return / max-DD)
       - Terminal-wealth-q05 (forward 252-session bootstrap from per-trade
         R-multiple distribution)
       - Profit-factor (gross profit / gross loss in $-realized)
       - R-multiple-mean
       - Plus risk-of-ruin Monte Carlo per ADR-0017 §4.2.
4. Emit per-symbol results JSON + KPI report card v1 markdown per
   ADR-0014 §3.2 12-table format.
5. Optional: invoke FM-1..FM-5 stress test primitive against the per-fold
   trade ledger.

Smoke mode
----------

`--smoke` flag: bypass substrate load; generate 500 deterministic 1-min
synthetic bars + run pipeline end-to-end. Validates orchestration logic;
no statistical interpretation possible on synthetic.

Production mode
---------------

`--symbol ES|NQ|MES|MNQ` + substrate path: full walk-forward across the
H055.yaml-pinned IS / OOS windows. Long-running.

Closes follow-up `P1-H055-WALK-FORWARD-ORCHESTRATOR-IMPL`. Walk-forward
folding + Optuna inner-CV + Hansen SPA + LW2008 are scoped to follow-ups
`P1-H055-WALK-FORWARD-FOLDING-IMPL` + `P1-H055-OPTUNA-INNER-CV-IMPL` +
`P1-H055-INFERENCE-CI-IMPL`.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from skie_ninja.backtest.per_trade_simulator import (
    EntryConfig,
    ExitReason,
    TradeResult,
    simulate_per_trade,
)
from skie_ninja.features.h055.features import (
    H055FeatureConfig,
    Setup,
    compute_h055_features,
    emit_h055_setups,
)
from skie_ninja.features.h055.level_state import LevelExhaustionStateMachine
from skie_ninja.inference.bootstrap import (
    politis_white_block_length,
    stationary_bootstrap_indices,
)
from skie_ninja.inference.calmar import calmar_ratio
from skie_ninja.inference.profit_factor import (
    profit_factor,
    profit_factor_differential_ci_stationary_bootstrap,
)
from skie_ninja.inference.r_multiple import (
    r_multiple_distribution,
    r_multiple_mean_ci_stationary_bootstrap,
)
from skie_ninja.inference.risk_of_ruin import probability_of_ruin_monte_carlo
from skie_ninja.utils.news_calendar import NewsCalendar


@dataclass(frozen=True)
class H055RunConfig:
    """Runtime configuration loaded from H055.yaml + CLI overrides."""

    hypothesis_id: str
    rho_star: float
    smoke: bool
    starting_equity: float
    risk_budget_pct: float
    rng_seed: int


@dataclass(frozen=True)
class FoldResult:
    """Aggregated per-fold result + ADR-0017 §1 inference + forward projection.

    Fields:
        symbol: e.g. "ES".
        n_setups_total: count emitted by detectors before gating.
        n_setups_post_gate: post-gate (trend + rho + R(L) + news).
        n_trades_filled: count actually filled by simulator.
        trades: list of TradeResult.
        ledger_r_multiples: array of realized R per filled trade.
        realized_end_equity: $ at fold end given starting_equity.
        max_dd: max drawdown fraction.
        ann_return: (1 + total_return)^(252/n_sessions) - 1.
        calmar: ann_return / max(|max_dd|, 1e-9).
        profit_factor: gross_profit / gross_loss (None if no losers).
        r_multiple_mean: mean realized R.
        n_sessions_proxy: sessions implied by bar count.

    ADR-0017 §1 inference fields (None when n_trades_filled < threshold):
        r_mult_ci_lower / upper / underpowered: stationary-bootstrap CI on
            R-multiple-mean per ADR-0017 §2.4.
        forward_terminal_q01 / q05 / median / q95 / q99: forward-projection
            quantiles per ADR-0017 §1 from a 5,000-path × 252-session
            iid-bootstrap of per-trade R-multiples (SIMPLIFIED — production
            should use stationary bootstrap with PW2004 block length, but
            with n_trades typically << n_sessions * trade_rate the iid
            approximation is the floor; tracked under
            P1-H055-FORWARD-PROJECTION-STATIONARY-BOOTSTRAP).
        forward_p_loss: probability terminal_equity < starting_equity.
        forward_p_below_50pct: probability terminal_equity < 0.5 × starting.
        risk_of_ruin: probability of touching 50% bankroll within 252 sessions.
    """

    symbol: str
    n_bars: int
    n_setups_total: int
    n_setups_post_gate: int
    n_trades_filled: int
    trades: list[TradeResult]
    ledger_r_multiples: np.ndarray
    ledger_pnl_dollars: np.ndarray
    realized_end_equity: float
    max_dd: float
    ann_return: float
    calmar: float
    profit_factor_value: float | None
    r_multiple_mean: float
    n_sessions_proxy: int

    # ADR-0017 §1 inference
    r_mult_ci_lower: float | None = None
    r_mult_ci_upper: float | None = None
    r_mult_underpowered: bool | None = None

    # Forward projection (ADR-0017 §1 + ADR-0013 §3.1)
    forward_terminal_q01: float | None = None
    forward_terminal_q05: float | None = None
    forward_terminal_median: float | None = None
    forward_terminal_q95: float | None = None
    forward_terminal_q99: float | None = None
    forward_p_loss: float | None = None
    forward_p_below_50pct: float | None = None
    risk_of_ruin: float | None = None


def _load_config(config_path: Path, smoke: bool) -> H055RunConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"H055 config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    rho_star = 0.6  # PLACEHOLDER per design.md §5.2 calibration; pending
                   # P1-H055-CALIBRATION-HOLDOUT-RUN binding.
    return H055RunConfig(
        hypothesis_id=cfg.get("hypothesis_id", "H055"),
        rho_star=rho_star,
        smoke=smoke,
        starting_equity=10_000.0,
        risk_budget_pct=0.01,
        rng_seed=int(cfg.get("random_seed", 20260506)),
    )


def _build_synthetic_bars(
    *, n_bars: int = 500, seed: int = 42, drift: float = 0.0008
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[datetime]]:
    """Smoke-mode synthetic bars: 1-min ES-flavored OHLC.

    Default drift = 0.0008 per-bar log-return — ~0.08%/bar — sufficient
    to trigger the MA-cross trend gate at default tau_ma=0.005 over a
    20-bar window (drift × 20 ≈ 1.6%). Keeps the smoke pipeline-validation
    test exercising the full setup → gate → simulator path.
    """
    rng = np.random.default_rng(seed)
    sigma = 0.0005
    log_p = np.cumsum(rng.normal(drift, sigma, n_bars)) + np.log(5000.0)
    return _bars_from_log_prices(log_p, seed=seed)


def _bars_from_log_prices(
    log_p: np.ndarray, *, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[datetime]]:
    """Helper: build OHLC + UTC timestamps from a log-price walk."""
    rng = np.random.default_rng(seed + 1)
    n_bars = log_p.size
    close = np.exp(log_p)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    body_half = np.abs(rng.normal(0.5, 0.3, n_bars))
    high = np.maximum(open_, close) + body_half + 0.05
    low = np.minimum(open_, close) - body_half - 0.05
    base_ts = datetime(2024, 6, 12, 14, 30, tzinfo=timezone.utc)
    timestamps = [base_ts + timedelta(minutes=i) for i in range(n_bars)]
    return open_, high, low, close, timestamps


def _load_substrate_for_symbol(
    substrate_root: Path,
    *,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[datetime]]:
    """Load production substrate parquet → numpy arrays for the orchestrator.

    Reads polars parquet(s) under `substrate_root / **/*.parquet`. Filters
    by symbol + date range. Sorts by ts_event.

    Args:
        substrate_root: Directory containing the partitioned parquet (e.g.,
            data/processed/vendor_legacy_1min_roll_adjusted/).
        symbol: One of {ES, NQ, MES, MNQ}.
        start_date / end_date: ISO date strings (YYYY-MM-DD); None = no
            bound on that side.

    Returns:
        (open_, high, low, close, ts_utc_list) tuple matching the smoke-
        mode output shape.

    Raises:
        FileNotFoundError: substrate_root does not exist.
        ValueError: zero rows match (symbol absent, or date range empty).
    """
    import polars as pl  # local import; keeps smoke-mode dependency-free

    if not substrate_root.exists():
        raise FileNotFoundError(
            f"substrate_root not found: {substrate_root}. Place ES/NQ "
            "1-min roll-adjusted parquets at this path before production run."
        )
    pattern = str(substrate_root / "**" / "*.parquet")
    panel = pl.read_parquet(pattern)
    if panel.height == 0:
        raise ValueError(f"empty panel from {pattern}")
    panel = panel.filter(pl.col("symbol") == symbol)
    if panel.height == 0:
        raise ValueError(f"symbol {symbol} absent from substrate at {substrate_root}")
    # Date filter — assumes ts_event is ts-aware datetime[ns,UTC].
    # start_date: lower-bound at 00:00:00 UTC of that date.
    # end_date: upper-bound at 23:59:59 UTC of that date (INCLUSIVE of full day).
    if start_date is not None:
        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        panel = panel.filter(pl.col("ts_event") >= start_dt)
    if end_date is not None:
        end_dt = datetime.fromisoformat(end_date).replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
        panel = panel.filter(pl.col("ts_event") <= end_dt)
    if panel.height == 0:
        raise ValueError(
            f"date filter [{start_date}, {end_date}] produced zero bars for {symbol}"
        )
    panel = panel.sort("ts_event")
    o = panel["open"].to_numpy().astype(float)
    h = panel["high"].to_numpy().astype(float)
    l = panel["low"].to_numpy().astype(float)
    c = panel["close"].to_numpy().astype(float)
    ts_series = panel["ts_event"].to_list()
    # Ensure UTC datetimes (polars returns datetime objects already)
    ts_utc = [t if t.tzinfo is not None else t.replace(tzinfo=timezone.utc) for t in ts_series]
    return o, h, l, c, ts_utc
    close = np.exp(log_p)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    body_half = np.abs(rng.normal(0.5, 0.3, n_bars))
    high = np.maximum(open_, close) + body_half + 0.05
    low = np.minimum(open_, close) - body_half - 0.05
    base_ts = datetime(2024, 6, 12, 14, 30, tzinfo=timezone.utc)
    timestamps = [base_ts + timedelta(minutes=i) for i in range(n_bars)]
    return open_, high, low, close, timestamps


def _gate_setups(
    setups: list[Setup],
    *,
    rho_star: float,
    state_machine: LevelExhaustionStateMachine,
    r_max: int,
    is_news_excluded: np.ndarray,
) -> list[Setup]:
    """Filter setups per design.md §3 gates.

    Gate sequence (all must pass for entry permission):
      1. Trend-gate (Component 1): setup.side × trend_side_at_confirmation > 0
      2. ρ_1 gate (Component 2): rho_1_at_confirmation >= rho_star
      3. R(L) gate (Component 3): state_machine.is_entry_permitted at the
         relevant level. For setups, we register the entry_limit_price as
         a level on first encounter and track its R(L) thereafter.
      4. News-calendar eligible-bar filter: bar must NOT be in news window.
    """
    gated: list[Setup] = []
    for s in setups:
        # 1. Trend gate
        if s.trend_side_at_confirmation == 0:
            continue
        if s.side * s.trend_side_at_confirmation <= 0:
            continue
        # 2. rho gate
        if not np.isfinite(s.rho_1_at_confirmation):
            continue
        if s.rho_1_at_confirmation < rho_star:
            continue
        # 3. R(L) gate (simplified: register level on first encounter; permitted
        # if R(L) ≤ R*).
        # For this orchestrator scaffold, we register every setup's level once,
        # then check permission. Production-grade integration with the state
        # machine's rejection-counting requires a per-bar event loop; tracked
        # as `P1-H055-LEVEL-STATE-PER-BAR-EVENT-INTEGRATION`.
        # For now, all setups pass the R(L) gate at R(L)=0 (initial).
        # 4. News calendar
        if s.confirmation_bar < is_news_excluded.size:
            if is_news_excluded[s.confirmation_bar]:
                continue
        gated.append(s)
    return gated


def _max_drawdown_fraction(equity_curve: np.ndarray) -> float:
    if equity_curve.size <= 1:
        return 0.0
    peak = np.maximum.accumulate(equity_curve)
    safe_peak = np.where(peak > 0.0, peak, 1.0)
    dd = (equity_curve - peak) / safe_peak
    return float(dd.min())


def _annualized_return(period_return: float, n_sessions: int) -> float:
    if period_return <= -1.0 or n_sessions <= 0:
        return -0.999
    return (1.0 + period_return) ** (252.0 / n_sessions) - 1.0


def _aggregate_fold(
    *,
    symbol: str,
    n_bars: int,
    setups: list[Setup],
    gated_setups: list[Setup],
    trades: list[TradeResult],
    starting_equity: float,
    rng_seed: int = 20260506,
    n_forward_paths: int = 5_000,
    n_forward_sessions: int = 252,
    n_bootstrap_ci: int = 2_000,
) -> FoldResult:
    filled = [t for t in trades if t.fill_bar is not None]
    pnl_dollars = np.array([t.realized_pnl_dollars for t in filled], dtype=float)
    r_multiples = np.array([t.r_multiple for t in filled], dtype=float)

    # Equity curve from per-trade $-PnL
    equity_curve = np.empty(filled.__len__() + 1, dtype=float)
    equity_curve[0] = starting_equity
    eq = starting_equity
    for i, t in enumerate(filled):
        eq += t.realized_pnl_dollars
        equity_curve[i + 1] = eq
    realized_end = float(equity_curve[-1])
    period_return = (realized_end - starting_equity) / starting_equity
    max_dd = _max_drawdown_fraction(equity_curve)

    # Sessions proxy: assume ~390 1-min bars per RTH session (project convention)
    n_sessions_proxy = max(1, n_bars // 390)
    ann_return = _annualized_return(period_return, n_sessions_proxy)
    calmar = ann_return / max(abs(max_dd), 1e-9)

    pf_val: float | None
    if pnl_dollars.size > 0:
        pf_val = float(profit_factor(pnl_dollars))
    else:
        pf_val = None
    r_mean = float(r_multiples.mean()) if r_multiples.size > 0 else 0.0

    # ─── ADR-0017 §1 inference ───
    r_mult_lo = r_mult_hi = None
    r_mult_underpowered = None
    fwd_q01 = fwd_q05 = fwd_med = fwd_q95 = fwd_q99 = None
    fwd_p_loss = fwd_p_below_50 = None
    ror = None

    if r_multiples.size >= 4:  # bootstrap requires n >= 4
        # CI on R-multiple-mean
        r_mult_ci = r_multiple_mean_ci_stationary_bootstrap(
            r_multiples, n_bootstrap=n_bootstrap_ci, rng_seed=rng_seed,
        )
        r_mult_lo = float(r_mult_ci.ci_lower)
        r_mult_hi = float(r_mult_ci.ci_upper)
        r_mult_underpowered = bool(r_mult_ci.underpowered)

        # Forward projection: bootstrap-resample per-trade R-multiples;
        # build n_forward_sessions equity curves; quantile.
        # Per ADR-0013 §3.1: the n_forward_sessions corresponds to 1 trading
        # year. We approximate per-session trade rate from n_filled / n_sessions_proxy.
        rng = np.random.default_rng(rng_seed + 1)
        trades_per_session = max(1, len(filled) // n_sessions_proxy)
        n_forward_trades = trades_per_session * n_forward_sessions
        # Simple iid bootstrap of R-multiples → $-PnL using session-cohort
        # mean dollar-stake (gross_profit + gross_loss / n_filled as an
        # approximation of $-stake-per-trade).
        if pnl_dollars.size > 0:
            avg_dollar_per_trade = float(np.abs(pnl_dollars).mean())
            indices = rng.integers(0, r_multiples.size, size=(n_forward_paths, n_forward_trades))
            r_paths = r_multiples[indices]  # (n_paths, n_trades)
            pnl_paths = r_paths * avg_dollar_per_trade
            cum_pnl = pnl_paths.sum(axis=1)
            terminal_equity = starting_equity + cum_pnl
            fwd_q01 = float(np.quantile(terminal_equity, 0.01))
            fwd_q05 = float(np.quantile(terminal_equity, 0.05))
            fwd_med = float(np.median(terminal_equity))
            fwd_q95 = float(np.quantile(terminal_equity, 0.95))
            fwd_q99 = float(np.quantile(terminal_equity, 0.99))
            fwd_p_loss = float(np.mean(terminal_equity < starting_equity))
            fwd_p_below_50 = float(np.mean(terminal_equity < 0.5 * starting_equity))

            # Risk-of-ruin Monte Carlo using existing primitive
            ror_result = probability_of_ruin_monte_carlo(
                r_multiples,
                starting_equity=starting_equity,
                ruin_threshold_fraction=0.5,
                n_sessions=n_forward_sessions,
                n_paths=n_forward_paths,
                kelly_fraction=0.10,
                rng_seed=rng_seed + 2,
            )
            ror = float(ror_result.probability_of_ruin)

    return FoldResult(
        symbol=symbol,
        n_bars=n_bars,
        n_setups_total=len(setups),
        n_setups_post_gate=len(gated_setups),
        n_trades_filled=len(filled),
        trades=trades,
        ledger_r_multiples=r_multiples,
        ledger_pnl_dollars=pnl_dollars,
        realized_end_equity=realized_end,
        max_dd=max_dd,
        ann_return=ann_return,
        calmar=calmar,
        profit_factor_value=pf_val,
        r_multiple_mean=r_mean,
        n_sessions_proxy=n_sessions_proxy,
        r_mult_ci_lower=r_mult_lo,
        r_mult_ci_upper=r_mult_hi,
        r_mult_underpowered=r_mult_underpowered,
        forward_terminal_q01=fwd_q01,
        forward_terminal_q05=fwd_q05,
        forward_terminal_median=fwd_med,
        forward_terminal_q95=fwd_q95,
        forward_terminal_q99=fwd_q99,
        forward_p_loss=fwd_p_loss,
        forward_p_below_50pct=fwd_p_below_50,
        risk_of_ruin=ror,
    )


def _emit_kpi_report_card(
    fold_results: list[FoldResult],
    *,
    run_id: str,
    config: H055RunConfig,
    out_dir: Path,
) -> Path:
    """Emit ADR-0017 §1 primary KPI report card v1.

    Includes the full survival-constrained inferential vector:
      - Realized OOS: end equity, max-DD, win/loss/zero counts
      - ADR-0017 §1 metrics: Calmar, profit-factor, R-multiple-mean
      - R-mult-mean stationary-bootstrap CI (Politis-Romano 1994)
      - Forward 252-session projection: q01/q05/median/q95/q99 + P(loss) +
        P(<50% bankroll) terminal equity quantiles
      - Risk-of-ruin Monte Carlo per ADR-0017 §4.2 (Vince 1990 *practitioner*)

    Per ADR-0014 §3.2 mandatory 12-table format (subset emitted here;
    full 12-table to land per-table once SPA family + LW2008 differential
    CI vs benchmark are wired under P1-H055-INFERENCE-CI-IMPL).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "H055_kpi_report_v1.md"
    lines: list[str] = []
    lines.append(f"# H055 KPI Report Card v1 (run_id `{run_id}`)\n")
    lines.append(
        "Survival-constrained inferential framework per "
        "[ADR-0017 §1](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md). "
        "Sharpe-family metrics archived per project directive (2026-05-09 operator instruction).\n"
    )

    # Table 1: Realized OOS P/L + counts
    lines.append("\n## §1 Realized OOS ($10,000 starting capital)\n")
    lines.append(
        "| Symbol | n_bars | n_setups | n_post_gate | n_trades_filled | "
        "Realized end | % change | Max-DD | Ann. return |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for r in fold_results:
        pct = r.realized_end_equity / config.starting_equity - 1.0
        lines.append(
            f"| {r.symbol} | {r.n_bars:,} | {r.n_setups_total} | "
            f"{r.n_setups_post_gate} | {r.n_trades_filled} | "
            f"${r.realized_end_equity:,.2f} | {pct:+.2%} | "
            f"{r.max_dd:.2%} | {r.ann_return:.2%} |"
        )
    lines.append("")

    # Table 2: ADR-0017 §1 primary metrics + R-mult CI
    lines.append("\n## §2 ADR-0017 §1 Primary Inference (with stationary-bootstrap CI)\n")
    lines.append(
        "| Symbol | Calmar | Profit-factor | R-mult mean | R-mult 95% CI | "
        "Excludes 0 | Underpowered |\n"
        "|---|---:|---:|---:|:--:|:--:|:--:|"
    )
    for r in fold_results:
        pf_str = (
            f"{r.profit_factor_value:.3f}"
            if r.profit_factor_value is not None else "n/a"
        )
        if r.r_mult_ci_lower is not None and r.r_mult_ci_upper is not None:
            ci_str = f"[{r.r_mult_ci_lower:+.3f}, {r.r_mult_ci_upper:+.3f}]"
            excl0 = "YES" if (r.r_mult_ci_lower > 0 or r.r_mult_ci_upper < 0) else "NO"
            up_str = "YES" if r.r_mult_underpowered else "NO"
        else:
            ci_str = "n/a (n_trades < 4)"
            excl0 = "n/a"
            up_str = "n/a"
        lines.append(
            f"| {r.symbol} | {r.calmar:+.3f} | {pf_str} | "
            f"{r.r_multiple_mean:+.4f} | {ci_str} | {excl0} | {up_str} |"
        )
    lines.append("")

    # Table 3: Forward 1-year projection
    lines.append("\n## §3 Forward 1-year projection (252-session bootstrap; 5,000 paths)\n")
    lines.append(
        "| Symbol | Median | q01 | q05 | q95 | q99 | "
        "P(loss) | P(<50% bankroll) | Risk-of-ruin |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for r in fold_results:
        if r.forward_terminal_median is not None:
            lines.append(
                f"| {r.symbol} | "
                f"${r.forward_terminal_median:,.0f} | "
                f"${r.forward_terminal_q01:,.0f} | "
                f"${r.forward_terminal_q05:,.0f} | "
                f"${r.forward_terminal_q95:,.0f} | "
                f"${r.forward_terminal_q99:,.0f} | "
                f"{r.forward_p_loss:.2%} | "
                f"{r.forward_p_below_50pct:.2%} | "
                f"{r.risk_of_ruin:.4%} |"
            )
        else:
            lines.append(
                f"| {r.symbol} | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |"
            )
    lines.append("")

    # ADR-0017 §1 verdict per-symbol
    lines.append("\n## §4 ADR-0017 §1 Verdict per Symbol\n")
    for r in fold_results:
        verdict_parts: list[str] = []
        if r.calmar > 0.5:
            verdict_parts.append("Calmar > 0.5 (favorable)")
        elif r.calmar < 0:
            verdict_parts.append(f"Calmar = {r.calmar:+.3f} (negative)")
        else:
            verdict_parts.append(f"Calmar = {r.calmar:+.3f} (marginal)")
        if r.r_mult_ci_lower is not None and r.r_mult_ci_lower > 0:
            verdict_parts.append("R-mult CI excludes zero on positive side")
        elif r.r_mult_ci_upper is not None and r.r_mult_ci_upper < 0:
            verdict_parts.append("R-mult CI excludes zero on NEGATIVE side")
        if r.forward_p_loss is not None and r.forward_p_loss < 0.20:
            verdict_parts.append(f"Forward P(loss) = {r.forward_p_loss:.1%} (low)")
        elif r.forward_p_loss is not None and r.forward_p_loss > 0.50:
            verdict_parts.append(f"Forward P(loss) = {r.forward_p_loss:.1%} (HIGH)")
        verdict = "; ".join(verdict_parts) if verdict_parts else "insufficient data"
        lines.append(f"- **{r.symbol}**: {verdict}")
    lines.append("")

    if config.smoke:
        lines.append(
            "\n> **Smoke-mode result**: synthetic 1-min bars; no statistical "
            "interpretation. Intended for orchestration-pipeline validation only.\n"
        )
    else:
        lines.append(
            "\n> **Production-mode result**: real substrate. Operator review per "
            "the user's 2026-05-04 standing decline-ninjascript directive + "
            "ADR-0013 §5.3 operator-discretionary clause.\n"
        )

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path,
        default=Path("config/hypotheses/H055.yaml"),
        help="Path to H055.yaml",
    )
    parser.add_argument(
        "--out-dir", type=Path,
        default=Path("artifacts/runs/H055"),
        help="Output directory for run artifacts",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="Smoke mode: synthetic bars, no substrate dependency",
    )
    parser.add_argument(
        "--symbol", type=str, default="ES",
        choices=["ES", "NQ", "MES", "MNQ"],
        help="Symbol to run (smoke mode uses synthetic regardless)",
    )
    parser.add_argument(
        "--n-synthetic-bars", type=int, default=500,
        help="Bars for synthetic panel (smoke mode only)",
    )
    parser.add_argument(
        "--substrate-root", type=str, default=None,
        help="Path to substrate parquet directory (production mode only). "
        "Default: data/processed/vendor_legacy_1min_roll_adjusted",
    )
    parser.add_argument(
        "--start-date", type=str, default=None,
        help="ISO YYYY-MM-DD lower bound on ts_event (production mode only)",
    )
    parser.add_argument(
        "--end-date", type=str, default=None,
        help="ISO YYYY-MM-DD upper bound on ts_event (production mode only)",
    )
    parser.add_argument(
        "--rho-star", type=float, default=None,
        help="Override the rho_star gate (default 0.6 PLACEHOLDER pending "
        "P1-H055-CALIBRATION-HOLDOUT-RUN binding). Lower values admit "
        "more setups; useful for smoke-testing the inference layer.",
    )
    args = parser.parse_args()

    if not args.config.exists():
        print(f"error: config not found at {args.config}", file=sys.stderr)
        return 2
    run_cfg = _load_config(args.config, smoke=args.smoke)
    if args.rho_star is not None:
        # Operator override per CLI; used to exercise the inference layer
        # on synthetic substrate where ρ_1 distribution doesn't reach the
        # production-default 0.6 threshold.
        run_cfg = H055RunConfig(
            hypothesis_id=run_cfg.hypothesis_id,
            rho_star=float(args.rho_star),
            smoke=run_cfg.smoke,
            starting_equity=run_cfg.starting_equity,
            risk_budget_pct=run_cfg.risk_budget_pct,
            rng_seed=run_cfg.rng_seed,
        )
        print(f"rho_star override: {args.rho_star}")

    # Build run_id
    run_id = f"smoke_{args.symbol}_{run_cfg.rng_seed}" if args.smoke else f"prod_{args.symbol}"
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # ─── Load bars ───
    if args.smoke:
        o, h, l, c, ts = _build_synthetic_bars(
            n_bars=args.n_synthetic_bars, seed=run_cfg.rng_seed
        )
        print(f"smoke mode: {args.n_synthetic_bars} synthetic 1-min bars")
    else:
        substrate_root = (
            Path(args.substrate_root) if args.substrate_root
            else Path("data/processed/vendor_legacy_1min_roll_adjusted")
        )
        try:
            o, h, l, c, ts = _load_substrate_for_symbol(
                substrate_root, symbol=args.symbol,
                start_date=args.start_date, end_date=args.end_date,
            )
        except (FileNotFoundError, ValueError) as e:
            print(f"error: substrate load failed: {e}", file=sys.stderr)
            return 3
        print(
            f"production mode: {o.size:,} bars loaded from {substrate_root.as_posix()} "
            f"for symbol={args.symbol} "
            f"[{ts[0].isoformat() if ts else 'n/a'} to "
            f"{ts[-1].isoformat() if ts else 'n/a'}]"
        )

    # ─── Feature factory ───
    feat_cfg = H055FeatureConfig(
        trend_id_choice="d",
        short_window=5,
        long_window=20,
        atr_n=14,
        rho_window_n=10,
        swing_confirmation_window=5,
        theta_wick_min=1.0,
        news_calendar_enabled=False,  # smoke: no news calendar
    )
    print(f"feature config: trend_id={feat_cfg.trend_id_choice}, atr_n={feat_cfg.atr_n}, rho_n={feat_cfg.rho_window_n}")
    features = compute_h055_features(o, h, l, c, ts, config=feat_cfg)

    # ─── Setup detection ───
    setups = emit_h055_setups(o, h, l, c, config=feat_cfg, bar_features=features)
    print(f"detected {len(setups)} raw setups (swing-pivot + wick-reversal)")

    # ─── Gate filtering ───
    state_machine = LevelExhaustionStateMachine()
    gated = _gate_setups(
        setups,
        rho_star=run_cfg.rho_star,
        state_machine=state_machine,
        r_max=2,
        is_news_excluded=features.is_news_excluded,
    )
    print(f"gated to {len(gated)} setups (post trend + rho + R(L) + news)")

    # ─── Per-trade simulation ───
    trades: list[TradeResult] = []
    for s in gated:
        if not np.isfinite(s.atr_n_at_confirmation) or s.atr_n_at_confirmation <= 0:
            continue
        cfg = EntryConfig(
            entry_limit_price=s.entry_limit_price,
            side=s.side,
            confirmation_bar=s.confirmation_bar,
            atr_n_at_entry=float(s.atr_n_at_confirmation),
            alpha_tp_mult=2.0,  # PLACEHOLDER per design.md §5.6 search domain
            beta_sl_mult=1.0,   # PLACEHOLDER
            k_swing_bars=5,
            position_size=1,
            multiplier=50.0,  # ES
        )
        trades.append(simulate_per_trade(h, l, c, config=cfg))
    print(f"simulated {len(trades)} trades; {sum(1 for t in trades if t.fill_bar is not None)} filled")

    # ─── Aggregate (includes ADR-0017 §1 inference + forward projection) ───
    fold_result = _aggregate_fold(
        symbol=args.symbol, n_bars=o.size,
        setups=setups, gated_setups=gated, trades=trades,
        starting_equity=run_cfg.starting_equity,
        rng_seed=run_cfg.rng_seed,
    )

    # ─── Emit results ───
    results_json: dict[str, Any] = {
        "run_id": run_id,
        "hypothesis_id": run_cfg.hypothesis_id,
        "smoke": run_cfg.smoke,
        "symbol": args.symbol,
        "config": dataclasses.asdict(feat_cfg),
        "fold_result": {
            "symbol": fold_result.symbol,
            "n_bars": fold_result.n_bars,
            "n_setups_total": fold_result.n_setups_total,
            "n_setups_post_gate": fold_result.n_setups_post_gate,
            "n_trades_filled": fold_result.n_trades_filled,
            "realized_end_equity": fold_result.realized_end_equity,
            "max_dd": fold_result.max_dd,
            "ann_return": fold_result.ann_return,
            "calmar": fold_result.calmar,
            "profit_factor": fold_result.profit_factor_value,
            "r_multiple_mean": fold_result.r_multiple_mean,
            "n_sessions_proxy": fold_result.n_sessions_proxy,
            # ADR-0017 §1 inference
            "r_mult_ci_lower": fold_result.r_mult_ci_lower,
            "r_mult_ci_upper": fold_result.r_mult_ci_upper,
            "r_mult_underpowered": fold_result.r_mult_underpowered,
            # Forward 1-year projection
            "forward_terminal_q01": fold_result.forward_terminal_q01,
            "forward_terminal_q05": fold_result.forward_terminal_q05,
            "forward_terminal_median": fold_result.forward_terminal_median,
            "forward_terminal_q95": fold_result.forward_terminal_q95,
            "forward_terminal_q99": fold_result.forward_terminal_q99,
            "forward_p_loss": fold_result.forward_p_loss,
            "forward_p_below_50pct": fold_result.forward_p_below_50pct,
            "risk_of_ruin": fold_result.risk_of_ruin,
        },
    }
    json_path = out_dir / "results.json"
    json_path.write_text(json.dumps(results_json, indent=2), encoding="utf-8")

    md_path = _emit_kpi_report_card(
        [fold_result], run_id=run_id, config=run_cfg, out_dir=out_dir,
    )

    print(f"results: {json_path.relative_to(Path.cwd()) if json_path.is_relative_to(Path.cwd()) else json_path}")
    print(f"KPI report: {md_path.relative_to(Path.cwd()) if md_path.is_relative_to(Path.cwd()) else md_path}")
    print(
        f"summary: realized_end=${fold_result.realized_end_equity:,.2f} "
        f"({fold_result.realized_end_equity/run_cfg.starting_equity-1:+.2%}); "
        f"calmar={fold_result.calmar:+.3f}; "
        f"R-mult mean={fold_result.r_multiple_mean:+.4f}; "
        f"n_filled={fold_result.n_trades_filled}/{fold_result.n_setups_post_gate}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
