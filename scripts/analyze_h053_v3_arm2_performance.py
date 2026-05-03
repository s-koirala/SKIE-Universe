"""H053 v3 Arm 2 LightGBM — comprehensive performance dashboard for un-archive review.

Per user directive 2026-05-03 ("make a note not to archive profitable strategies;
unarchive; what do the profit margins, drawdowns, etc look like?"):
the v3 binding-disposition `calibration-failed` is being overridden because
the strategy is profitable on OOS. This script computes the
operationally-relevant performance metrics (drawdowns, win rate, profit factor,
Calmar, monthly breakdown, cost-adjusted Sharpe) for ES + NQ Arm 2 LightGBM.

Re-runs the v3 production fit (LightGBM with inner walk-forward CV
hyperparameter selection on full IS train; predicts OOS test). Strategy returns
= sign(prediction) * y_test (per-session log return at 09:45→10:30 ET).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# justify: ensure project root on sys.path  # paths-guard: allow (script-bootstrap)
_REPO_ROOT = Path(__file__).resolve().parent.parent  # paths-guard: allow (script-bootstrap)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import polars as pl

from skie_ninja.backtest.costs.h053_cost_c import H053CostC
from skie_ninja.inference.bootstrap import choose_block_length, stationary_bootstrap_indices
from skie_ninja.inference.stats.ledoit_wolf_2008 import ledoit_wolf_2008_differential_ci
from scripts.run_h053_stage3_full import (
    _IS_END,
    _IS_START,
    _OOS_END_ES,
    _OOS_END_NQ,
    _OOS_START,
    _STAGE3_RNG_SEED,
    _compute_features_per_session,
    _compute_predictand,
    _load_substrate,
    _passive_long_returns,
    _resolve_substrate_path,
    _strategy_returns_from_pred,
)
from scripts.run_h053_stage3_v3 import _fit_arm2_lightgbm_wf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h053_v3_perf")


def compute_drawdown_stats(returns: np.ndarray, dates: list) -> dict:
    """Compute max drawdown + its date range + duration in sessions."""
    cum = np.cumsum(returns)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    max_dd_value = float(np.max(dd))
    max_dd_idx = int(np.argmax(dd))
    # Find peak-before-trough index
    peak_idx = int(np.argmax(peak[:max_dd_idx + 1])) if max_dd_idx > 0 else 0
    # Recovery date = first index after trough where cum >= peak[max_dd_idx]
    recovery_idx = None
    for i in range(max_dd_idx + 1, len(cum)):
        if cum[i] >= peak[max_dd_idx]:
            recovery_idx = i
            break
    return {
        "max_dd_log_return": max_dd_value,
        "max_dd_bps": max_dd_value * 1e4,
        "peak_idx": peak_idx,
        "trough_idx": max_dd_idx,
        "recovery_idx": recovery_idx,
        "peak_date": str(dates[peak_idx]) if peak_idx < len(dates) else None,
        "trough_date": str(dates[max_dd_idx]) if max_dd_idx < len(dates) else None,
        "recovery_date": str(dates[recovery_idx]) if recovery_idx is not None else "NOT_RECOVERED",
        "drawdown_duration_sessions": (recovery_idx - peak_idx) if recovery_idx is not None else (len(cum) - peak_idx),
        "underwater_sessions": int(np.sum(dd > 0)),
    }


def compute_win_rate_metrics(returns: np.ndarray) -> dict:
    """Win rate + profit factor + consecutive runs."""
    n = len(returns)
    n_wins = int(np.sum(returns > 0))
    n_losses = int(np.sum(returns < 0))
    n_zeros = n - n_wins - n_losses
    sum_wins = float(np.sum(returns[returns > 0])) if n_wins > 0 else 0.0
    sum_losses = float(np.sum(returns[returns < 0])) if n_losses > 0 else 0.0
    profit_factor = abs(sum_wins / sum_losses) if sum_losses != 0 else float("inf")

    # Consecutive runs
    signs = np.sign(returns)
    max_win_streak = 0
    max_loss_streak = 0
    cur = 0
    for s in signs:
        if s > 0:
            cur = cur + 1 if cur >= 0 else 1
            max_win_streak = max(max_win_streak, cur)
        elif s < 0:
            cur = cur - 1 if cur <= 0 else -1
            max_loss_streak = max(max_loss_streak, abs(cur))
        else:
            cur = 0

    return {
        "n_sessions": n,
        "n_wins": n_wins,
        "n_losses": n_losses,
        "n_zeros": n_zeros,
        "win_rate": n_wins / n if n > 0 else 0.0,
        "loss_rate": n_losses / n if n > 0 else 0.0,
        "avg_win_bps": (sum_wins / n_wins * 1e4) if n_wins > 0 else 0.0,
        "avg_loss_bps": (sum_losses / n_losses * 1e4) if n_losses > 0 else 0.0,
        "profit_factor": profit_factor,
        "max_consecutive_wins": max_win_streak,
        "max_consecutive_losses": max_loss_streak,
    }


def compute_monthly_breakdown(returns: np.ndarray, dates) -> list[dict]:
    """Monthly P&L + win rate breakdown."""
    df = pl.DataFrame({
        "date": dates,
        "ret": returns,
    })
    monthly = (
        df.with_columns(pl.col("date").dt.strftime("%Y-%m").alias("ym"))
        .group_by("ym")
        .agg([
            pl.col("ret").sum().alias("total_log_return"),
            pl.col("ret").count().alias("n_sessions"),
            (pl.col("ret") > 0).sum().alias("n_wins"),
            pl.col("ret").mean().alias("mean_per_session"),
            pl.col("ret").std().alias("std_per_session"),
        ])
        .sort("ym")
    )
    out = []
    for row in monthly.iter_rows(named=True):
        out.append({
            "month": row["ym"],
            "total_log_return_bps": row["total_log_return"] * 1e4,
            "n_sessions": int(row["n_sessions"]),
            "n_wins": int(row["n_wins"]),
            "win_rate": row["n_wins"] / row["n_sessions"] if row["n_sessions"] > 0 else 0.0,
            "mean_bps": row["mean_per_session"] * 1e4 if row["mean_per_session"] else 0.0,
            "std_bps": row["std_per_session"] * 1e4 if row["std_per_session"] else 0.0,
        })
    return out


def compute_yearly_breakdown(returns: np.ndarray, dates) -> list[dict]:
    df = pl.DataFrame({"date": dates, "ret": returns})
    yearly = (
        df.with_columns(pl.col("date").dt.year().alias("yr"))
        .group_by("yr")
        .agg([
            pl.col("ret").sum().alias("total_log_return"),
            pl.col("ret").count().alias("n_sessions"),
            (pl.col("ret") > 0).sum().alias("n_wins"),
            pl.col("ret").mean().alias("mean_per_session"),
            pl.col("ret").std().alias("std_per_session"),
        ])
        .sort("yr")
    )
    out = []
    for row in yearly.iter_rows(named=True):
        mean = row["mean_per_session"] or 0.0
        std = row["std_per_session"] or 0.0
        out.append({
            "year": int(row["yr"]),
            "total_log_return": row["total_log_return"],
            "annualized_log_return_pct": row["total_log_return"] * 100,
            "n_sessions": int(row["n_sessions"]),
            "win_rate": row["n_wins"] / row["n_sessions"] if row["n_sessions"] > 0 else 0.0,
            "mean_per_session_bps": mean * 1e4,
            "std_per_session_bps": std * 1e4,
            "annualized_sharpe": (mean / std * np.sqrt(252)) if std > 1e-12 else 0.0,
        })
    return out


def compute_lo2002_sharpe_ci(returns: np.ndarray) -> dict:
    """Lo 2002 §III HAC-adjusted Sharpe + bootstrap CI per Opdyke 2007."""
    if len(returns) < 30:
        return {"sharpe_per_session": 0.0, "annualized_sharpe": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}
    mu = float(np.mean(returns))
    sigma = float(np.std(returns, ddof=1))
    sharpe = mu / sigma if sigma > 1e-12 else 0.0
    annualized = sharpe * np.sqrt(252)

    # Bootstrap CI on annualized Sharpe via paired stationary bootstrap
    rng = np.random.default_rng(_STAGE3_RNG_SEED + 999)
    sel = choose_block_length(returns, bootstrap_type="stationary")
    block_length = float(sel.block_length)
    n_boot = 2000
    boot = np.empty(n_boot)
    for b in range(n_boot):
        idx = stationary_bootstrap_indices(len(returns), block_length=block_length, rng=rng)
        rb = returns[idx]
        mu_b = float(np.mean(rb))
        sigma_b = float(np.std(rb, ddof=1))
        boot[b] = (mu_b / sigma_b * np.sqrt(252)) if sigma_b > 1e-12 else 0.0
    return {
        "sharpe_per_session": sharpe,
        "annualized_sharpe": annualized,
        "ci_lower": float(np.percentile(boot, 2.5)),
        "ci_upper": float(np.percentile(boot, 97.5)),
        "block_length": block_length,
        "n_bootstrap": n_boot,
    }


def compute_cost_adjusted(arm_returns: np.ndarray, symbol: str, reference_price: float) -> dict:
    """Net-of-cost performance: subtract round-trip cost-c per session (assuming 1 RT/session)."""
    cost = H053CostC(symbol=symbol, reference_price=reference_price, sensitivity_mult=1.0)
    cost_c = cost.c_log_return()  # per-session round-trip cost in log-return units
    net_returns = arm_returns - cost_c
    mu_net = float(np.mean(net_returns))
    sigma_net = float(np.std(net_returns, ddof=1))
    return {
        "cost_c_log_return": cost_c,
        "cost_c_bps": cost.c_bps(),
        "gross_mean_bps_per_session": float(np.mean(arm_returns)) * 1e4,
        "net_mean_bps_per_session": mu_net * 1e4,
        "net_annualized_return_pct": mu_net * 252 * 100,
        "net_annualized_sharpe": (mu_net / sigma_net * np.sqrt(252)) if sigma_net > 1e-12 else 0.0,
        "net_total_pnl_bps": float(np.sum(net_returns)) * 1e4,
        "gross_total_pnl_bps": float(np.sum(arm_returns)) * 1e4,
    }


def analyze_symbol(substrate_root: Path, symbol: str, oos_end) -> dict:
    _log.info("[%s] Loading substrate …", symbol)
    panel = _load_substrate(substrate_root, symbol)
    features = _compute_features_per_session(panel)
    target_dtype = pl.Datetime("ns", "UTC")
    features = features.with_columns(pl.col("ts_event").cast(target_dtype))
    predictand = _compute_predictand(panel).with_columns(pl.col("ts_event").cast(target_dtype))
    aligned = predictand.join(features, on=["symbol", "ts_event"], how="inner")
    train_filter = (pl.col("session_date_et") >= _IS_START) & (pl.col("session_date_et") <= _IS_END)
    test_filter = (pl.col("session_date_et") >= _OOS_START) & (pl.col("session_date_et") <= oos_end)
    skip = {"ts_event", "symbol", "session_date_et", "y", "c_0945", "c_1030"}
    feature_cols = [
        c for c in aligned.columns
        if c not in skip and not c.startswith("_") and not c.endswith("_right")
        and aligned[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
    ]
    aligned = aligned.with_columns(
        pl.fold(
            acc=pl.lit(True), function=lambda acc, x: acc & x.is_finite(),
            exprs=[pl.col(c) for c in feature_cols],
        ).alias("_ok")
    ).filter(pl.col("_ok")).drop("_ok")
    train = aligned.filter(train_filter).sort("session_date_et")
    test = aligned.filter(test_filter).sort("session_date_et")
    X_train = train.select(feature_cols).to_numpy()
    y_train = train["y"].to_numpy()
    X_test = test.select(feature_cols).to_numpy()
    y_test = test["y"].to_numpy()
    test_dates = test["session_date_et"].to_list()

    # Reference price from train fold
    train_session_dates = set(train["session_date_et"].to_list())
    panel_et = panel.with_columns(
        pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et")
    ).with_columns(
        pl.col("_ts_et").dt.date().alias("_sd"),
        pl.col("_ts_et").dt.hour().cast(pl.Int32).alias("_h"),
        pl.col("_ts_et").dt.minute().cast(pl.Int32).alias("_m"),
    )
    train_0945 = panel_et.filter(
        (pl.col("_h") == 9) & (pl.col("_m") == 45)
        & pl.col("_sd").is_in(list(train_session_dates))
    )
    reference_price = float(np.median(train_0945["close"].to_numpy())) if len(train_0945) > 0 else (5500.0 if symbol == "ES" else 20000.0)

    _log.info("[%s] Fitting Arm 2 LightGBM on full IS train (n=%d) …", symbol, len(X_train))
    arm, arm_meta = _fit_arm2_lightgbm_wf(X_train, y_train, inner_seed=_STAGE3_RNG_SEED)
    _log.info("[%s] LightGBM best cell: %s (CV R²=%.4f)", symbol, arm_meta["best_cell"], arm_meta["best_cv_r2"])

    pred = arm.predict(X_test)
    arm_returns = _strategy_returns_from_pred(pred, y_test)
    passive_returns = _passive_long_returns(y_test)

    sharpe_lo = compute_lo2002_sharpe_ci(arm_returns)
    sharpe_passive = compute_lo2002_sharpe_ci(passive_returns)
    win_metrics = compute_win_rate_metrics(arm_returns)
    dd = compute_drawdown_stats(arm_returns, test_dates)
    monthly = compute_monthly_breakdown(arm_returns, test_dates)
    yearly = compute_yearly_breakdown(arm_returns, test_dates)
    cost_adj = compute_cost_adjusted(arm_returns, symbol, reference_price)

    # vs passive paired Sharpe CI (LW2008)
    lw_vs_passive = ledoit_wolf_2008_differential_ci(
        arm_returns, passive_returns,
        n_bootstrap=2000, rng=np.random.default_rng(_STAGE3_RNG_SEED + 777),
    )

    # Calmar = annualized return / max DD
    annualized_return_pct = float(np.mean(arm_returns)) * 252 * 100
    calmar = annualized_return_pct / (dd["max_dd_bps"] * 1e-4 * 100) if dd["max_dd_bps"] > 0 else float("inf")

    # Sortino: downside-only volatility
    downside = arm_returns[arm_returns < 0]
    downside_std = float(np.std(downside, ddof=1)) if len(downside) > 1 else 0.0
    sortino = (np.mean(arm_returns) / downside_std * np.sqrt(252)) if downside_std > 1e-12 else float("inf")

    return {
        "symbol": symbol,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "test_window_dates": [str(test_dates[0]), str(test_dates[-1])],
        "lightgbm_best_cell": arm_meta["best_cell"],
        "lightgbm_best_cv_r2": float(arm_meta["best_cv_r2"]),
        "reference_price_train": reference_price,
        "performance": {
            "total_log_return": float(np.sum(arm_returns)),
            "total_log_return_bps": float(np.sum(arm_returns)) * 1e4,
            "mean_per_session_bps": float(np.mean(arm_returns)) * 1e4,
            "std_per_session_bps": float(np.std(arm_returns, ddof=1)) * 1e4,
            "annualized_return_pct": annualized_return_pct,
            "annualized_vol_pct": float(np.std(arm_returns, ddof=1)) * np.sqrt(252) * 100,
            "annualized_sharpe": sharpe_lo["annualized_sharpe"],
            "sharpe_ci_lower": sharpe_lo["ci_lower"],
            "sharpe_ci_upper": sharpe_lo["ci_upper"],
            "sortino_ratio_annualized": float(sortino),
            "calmar_ratio_annualized": float(calmar),
        },
        "drawdown": dd,
        "win_metrics": win_metrics,
        "vs_passive_LW2008": {
            "passive_annualized_sharpe": sharpe_passive["annualized_sharpe"],
            "differential_sharpe_point": float(lw_vs_passive.point_estimate),
            "differential_sharpe_lower": float(lw_vs_passive.lower),
            "differential_sharpe_upper": float(lw_vs_passive.upper),
            "differential_excludes_zero": (lw_vs_passive.lower > 0) or (lw_vs_passive.upper < 0),
        },
        "cost_adjusted_1tick": cost_adj,
        "monthly_breakdown": monthly,
        "yearly_breakdown": yearly,
    }


def main(substrate_path: str | None = None, out_path: str | None = None):
    substrate_root = _resolve_substrate_path(substrate_path)
    results = {
        "ES": analyze_symbol(substrate_root, "ES", _OOS_END_ES),
        "NQ": analyze_symbol(substrate_root, "NQ", _OOS_END_NQ),
    }
    serialised = json.dumps(results, indent=2, sort_keys=True, default=str)
    if out_path:
        Path(out_path).write_text(serialised, encoding="utf-8")
        _log.info("Performance dashboard written to %s", out_path)
    else:
        print(serialised)
    return results


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--substrate-path", default=None)
    p.add_argument("--out", default=None)
    args = p.parse_args()
    main(args.substrate_path, args.out)
