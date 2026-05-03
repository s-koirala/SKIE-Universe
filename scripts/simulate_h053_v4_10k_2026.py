"""H053 Stage-3 v4 — $10k starting capital simulation, 2026 projection.

Uses the v4 OOS strategy returns (refit deterministically with seed=42) as
the empirical distribution; bootstrap-samples 252 sessions (= ~1 trading
year) to project a hypothetical 2026 equity curve from $10k starting capital.

Per ADR-0013 §1 KPI-only philosophy: this is a Monte Carlo projection
informed by the v4 OOS distribution, NOT a prediction. The v4 KPI report
card v2 establishes that all 4 (arm × symbol) cells have CI covering zero
on Sharpe-vs-passive — so the projected 2026 equity distribution will be
wide and crosses $10k on most arms.

Position-sizing convention (operationally simplest):
- equity_{t+1} = equity_t * exp(r_t) where r_t is the strategy LOG return
- This corresponds to a 100%-of-equity, no-leverage position per session
- Strategy log return r_t = sign(y_pred_t) * y_actual_t per H053 design.md §1
- Daily clearing (single 09:45→10:30 ET trade per session); no overnight risk

References
----------
- runs/h053/stage3_v4/fe051383e6c146bea93051b816c7e0a1/sidecar.json (canonical Path B output)
- research/01_hypothesis_register/H053/H053_kpi_report_v2.md
- ADR-0013 §1 KPI-only philosophy
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent  # paths-guard: allow (script-bootstrap)
_SRC_DIR = _REPO_ROOT / "src"  # paths-guard: allow (script-bootstrap)
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import polars as pl

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
from scripts.run_h053_stage3_v4 import (
    _fit_arm1_elasticnet_v4,
    _fit_arm2_lightgbm_v4,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("simulate_10k_2026")

_STARTING_CAPITAL: float = 10_000.0
_PROJECTION_SESSIONS: int = 252  # 1 trading year
_N_BOOTSTRAP: int = 5_000  # MC paths
_BOOTSTRAP_RNG_SEED: int = _STAGE3_RNG_SEED + 1000  # 1042


def _max_drawdown_from_equity(equity: np.ndarray) -> float:
    """Return the maximum drawdown as a fraction of peak equity."""
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    return float(abs(dd.min()))


def _simulate_equity_curve(
    log_returns: np.ndarray, starting: float = _STARTING_CAPITAL
) -> tuple[np.ndarray, float, float]:
    """Compute equity curve, ending equity, and max drawdown from log-return path."""
    cumlog = np.concatenate([[0.0], np.cumsum(log_returns)])
    equity = starting * np.exp(cumlog)
    return equity, float(equity[-1]), _max_drawdown_from_equity(equity)


def _bootstrap_2026_projection(
    log_returns: np.ndarray,
    *,
    n_paths: int,
    n_sessions: int,
    rng_seed: int,
) -> dict[str, Any]:
    """Bootstrap-sample n_sessions log-returns from log_returns; project equity curves.

    Per Round-1 audit F-CONV-3: select block-length via Politis-White 2004 on
    EACH ARM'S LEVEL series (not the strategy-minus-bench differential). When
    PW2004 selects block_length=1.0 the iid bootstrap is appropriate; otherwise
    Politis-Romano 1994 stationary bootstrap with the PW2004-selected length.

    Per Round-1 audit F-CONV-4: single rng_seed across all arms; per-arm offsets
    are FORBIDDEN.

    Per Round-1 audit F-CONV-7: report q01/q99 alongside q05/q95 so the
    operator can read the actual distribution shape when P(double)/P(<50%)
    degenerate to 0% (typical for low-vol intraday strategies at 252 sessions).
    """
    from skie_ninja.inference.bootstrap import (
        choose_block_length,
        stationary_bootstrap_indices,
    )

    rng = np.random.default_rng(rng_seed)
    n_oos = len(log_returns)
    # F-CONV-3 fix: PW2004 on the LEVEL series (not the differential).
    # `choose_block_length` defaults to bootstrap_type="stationary".
    block_length_selection = choose_block_length(log_returns)
    selected_b = float(block_length_selection.block_length)
    end_equities: list[float] = []
    max_dds: list[float] = []
    # `stationary_bootstrap_indices(n, ...)` returns n indices; we truncate to
    # n_sessions if n_oos > n_sessions, or we draw n_oos indices and reuse.
    # For n_sessions < n_oos: draw n_oos indices, take first n_sessions.
    # For n_sessions > n_oos: would need to draw more — n/a here (252 < 370).
    n_draw = max(n_oos, n_sessions)
    for _ in range(n_paths):
        if selected_b <= 1.0:
            # iid bootstrap (block_length=1 limit)
            idx = rng.integers(0, n_oos, size=n_sessions)
        else:
            # Politis-Romano 1994 stationary bootstrap
            full_idx = stationary_bootstrap_indices(
                n=n_draw,
                block_length=selected_b,
                rng=rng,
            )
            # Map to valid range [0, n_oos) via modulo (no-op when n_draw == n_oos)
            idx = (full_idx[:n_sessions] % n_oos)
        path_returns = log_returns[idx]
        _, end_eq, max_dd = _simulate_equity_curve(path_returns)
        end_equities.append(end_eq)
        max_dds.append(max_dd)
    end_eq_arr = np.asarray(end_equities)
    max_dd_arr = np.asarray(max_dds)
    return {
        "n_paths": n_paths,
        "n_sessions": n_sessions,
        "block_length_pw2004": selected_b,
        "block_length_method": "PW2004_on_level_series_per_F-CONV-3",
        "sampling_method": "iid_bootstrap" if selected_b <= 1.0 else "stationary_bootstrap_PR1994",
        "ending_equity": {
            "mean": float(end_eq_arr.mean()),
            "median": float(np.median(end_eq_arr)),
            "q01": float(np.quantile(end_eq_arr, 0.01)),
            "q05": float(np.quantile(end_eq_arr, 0.05)),
            "q25": float(np.quantile(end_eq_arr, 0.25)),
            "q75": float(np.quantile(end_eq_arr, 0.75)),
            "q95": float(np.quantile(end_eq_arr, 0.95)),
            "q99": float(np.quantile(end_eq_arr, 0.99)),
            "p_loss": float((end_eq_arr < _STARTING_CAPITAL).mean()),
            "p_double": float((end_eq_arr >= 2 * _STARTING_CAPITAL).mean()),
            "p_ruin50": float((end_eq_arr <= 0.5 * _STARTING_CAPITAL).mean()),
        },
        "max_drawdown": {
            "mean": float(max_dd_arr.mean()),
            "median": float(np.median(max_dd_arr)),
            "q05": float(np.quantile(max_dd_arr, 0.05)),
            "q95": float(np.quantile(max_dd_arr, 0.95)),
        },
    }


def _process_symbol(
    substrate_root: Path,
    symbol: str,
    oos_end,
) -> dict[str, Any]:
    _log.info("[%s] Loading substrate + features …", symbol)
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
        if c not in skip
        and not c.startswith("_")
        and not c.endswith("_right")
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

    _log.info("[%s] train=%d test=%d features=%d; refitting arms …", symbol, len(train), len(test), len(feature_cols))
    arm1, _ = _fit_arm1_elasticnet_v4(X_train, y_train)
    arm2, _ = _fit_arm2_lightgbm_v4(X_train, y_train)

    arm1_returns = _strategy_returns_from_pred(arm1.predict(X_test), y_test)
    arm2_returns = _strategy_returns_from_pred(arm2.predict(X_test), y_test)
    passive_returns = _passive_long_returns(y_test)

    out: dict[str, Any] = {
        "symbol": symbol,
        "n_oos_sessions": len(y_test),
        "oos_window": [str(test_dates[0]), str(test_dates[-1])],
        "arms": {},
    }

    for arm_id, arm_ret in [
        ("arm1_elasticnet", arm1_returns),
        ("arm2_lightgbm", arm2_returns),
        ("passive_long", passive_returns),
    ]:
        # Realized OOS equity curve from $10k start at OOS-window start
        equity, end_eq, max_dd = _simulate_equity_curve(arm_ret)
        # 2026 bootstrap projection (252 sessions sampled from OOS distribution).
        # F-CONV-4 fix: single rng_seed across all arms; per-arm offsets FORBIDDEN.
        proj = _bootstrap_2026_projection(
            arm_ret,
            n_paths=_N_BOOTSTRAP,
            n_sessions=_PROJECTION_SESSIONS,
            rng_seed=_BOOTSTRAP_RNG_SEED,
        )
        out["arms"][arm_id] = {
            "n_sessions": int(len(arm_ret)),
            "mean_per_session_log_return": float(arm_ret.mean()),
            "std_per_session_log_return": float(arm_ret.std(ddof=1)),
            "annualized_sharpe": float(arm_ret.mean() / arm_ret.std(ddof=1) * np.sqrt(252.0)) if arm_ret.std(ddof=1) > 0 else float("nan"),
            "realized_oos": {
                "starting_equity": _STARTING_CAPITAL,
                "ending_equity": end_eq,
                "ending_pct_change": (end_eq / _STARTING_CAPITAL - 1.0) * 100,
                "max_drawdown_pct": max_dd * 100,
                "n_winning_sessions": int((arm_ret > 0).sum()),
                "n_losing_sessions": int((arm_ret < 0).sum()),
                "n_zero_sessions": int((arm_ret == 0).sum()),
            },
            "projected_2026_252sessions": proj,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H053 v4 — $10k 2026 projection")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--symbols", default="ES,NQ")
    args = parser.parse_args(argv)

    substrate_root = _resolve_substrate_path(args.substrate_path)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    results: list[dict[str, Any]] = []
    for sym in symbols:
        oos_end = _OOS_END_ES if sym == "ES" else _OOS_END_NQ
        results.append(_process_symbol(substrate_root, sym, oos_end))

    # Print summary table
    print()
    print("=" * 100)
    print(f"H053 Stage-3 v4 — $10,000 STARTING CAPITAL SIMULATION  |  source: v4 OOS strategy returns")
    print(f"  Bootstrap: {_N_BOOTSTRAP:,} MC paths × {_PROJECTION_SESSIONS} sessions (= 1 trading year for 2026 projection)")
    print(f"  Position-sizing: 100%-of-equity per session, no leverage; equity_{{t+1}} = equity_t * exp(r_t)")
    print("=" * 100)
    for r in results:
        sym = r["symbol"]
        print(f"\n{sym}  (OOS: {r['oos_window'][0]} → {r['oos_window'][1]}; n_oos_sessions={r['n_oos_sessions']})")
        print("-" * 100)
        print(f"{'Arm':<22} {'OOS Sharpe':>12} {'Realized $':>14} {'Realized %':>12} {'Realized DD %':>15}  {'Win/Loss/Zero':>16}")
        for arm_id, ad in r["arms"].items():
            ro = ad["realized_oos"]
            print(
                f"{arm_id:<22} {ad['annualized_sharpe']:>12.3f} "
                f"${ro['ending_equity']:>13,.0f} {ro['ending_pct_change']:>+11.1f}% "
                f"{ro['max_drawdown_pct']:>14.1f}%  "
                f"{ro['n_winning_sessions']:>4}/{ro['n_losing_sessions']:<4}/{ro['n_zero_sessions']:<4}"
            )
        print()
        print(f"  2026 projection (bootstrap from OOS empirical distribution; 252 sessions = ~1 year):")
        print(f"  {'Arm':<22} {'Median $':>12} {'Mean $':>12} {'q01 $':>10} {'q05 $':>10} {'q95 $':>10} {'q99 $':>10}  {'P(loss)':>9} {'P(double)':>10} {'P(<50%)':>9}  {'block_b':>8}  {'method':>22}")
        for arm_id, ad in r["arms"].items():
            proj = ad["projected_2026_252sessions"]
            ee = proj["ending_equity"]
            print(
                f"  {arm_id:<22} ${ee['median']:>10,.0f}  ${ee['mean']:>10,.0f}  "
                f"${ee['q01']:>8,.0f}  ${ee['q05']:>8,.0f}  ${ee['q95']:>8,.0f}  ${ee['q99']:>8,.0f}  "
                f"{ee['p_loss']:>9.1%} {ee['p_double']:>10.1%} {ee['p_ruin50']:>9.1%}  "
                f"{proj['block_length_pw2004']:>8.2f}  {proj['sampling_method']:>22}"
            )
        print()
        print(f"  2026 max-drawdown projection (% peak-to-trough):")
        print(f"  {'Arm':<22} {'Median %':>10} {'Mean %':>10} {'q05 %':>10} {'q95 %':>10}")
        for arm_id, ad in r["arms"].items():
            dd = ad["projected_2026_252sessions"]["max_drawdown"]
            print(
                f"  {arm_id:<22} {dd['median']*100:>9.1f}% {dd['mean']*100:>9.1f}% "
                f"{dd['q05']*100:>9.1f}% {dd['q95']*100:>9.1f}%"
            )
    print()
    print("=" * 100)
    print("CAVEATS:")
    print("  - Per ADR-0013 §1, this is informational only; no gates fire on these projections.")
    print("  - Bootstrap uses OOS empirical distribution as a generative model — assumes 2026 mirrors 2024-2025.")
    print("  - Cost model NOT applied here (raw strategy log-returns); H053 NT8 RTH cost model would")
    print("    subtract per-session costs (commission + exchange fee + 1-2 tick slippage). Cost-floor")
    print("    sensitivity is a v2 KPI report card item; this projection is cost-free upper bound.")
    print("  - Position-sizing is 100%-of-equity per session; under realistic NinjaTrader execution,")
    print("    margin requirements + retail-size capacity ceiling per CLAUDE.md §Standing constraints")
    print("    would constrain the sizing.")
    print("  - The H053 v2 KPI report card flags BSS uniformly ≤ 0 + Sharpe-vs-passive CI uniformly")
    print("    crossing zero — this projection's ending-equity distribution reflects that uncertainty.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
