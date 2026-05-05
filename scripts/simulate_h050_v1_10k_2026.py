"""H050 v1 — $10k starting capital simulation, 2026 projection.

Reads the canonical H050 production walk-forward run's per-symbol
``oos_returns.parquet`` (gated + unconditional + passive-long bar-level
log return series) and produces:

  1. Realized OOS equity curve from $10,000 at OOS-window start through
     OOS-window end (per ADR-0013 §3.1 item 1).
  2. 252-trading-day forward bootstrap projection via Politis-White 2004
     auto-block-length selection on the LEVEL series; iid bootstrap if
     the selected block length is 1.0 else stationary bootstrap (Politis-
     Romano 1994). Mirrors H053 v4 reference at
     ``scripts/simulate_h053_v4_10k_2026.py``.

H050 archetype per ADR-0013 §3.1.1 sizing-convention table:
  HMM-gated multi-bar intraday — per-state position multiplier ×
  100%-of-equity-when-active; equity unchanged when state-gated-out.
  The bar-level series in ``oos_returns.parquet`` already encodes
  this: zero return on gated-out bars (HMM forward-filter posterior
  places the modal state outside the high-mean state at that bar).

Bar-frequency calendar conversion: 1 trading year = 252 sessions ×
390 RTH bars/session (1-minute ES/NQ RTH) = 98,280 bars per session.
The forward projection sample size is therefore 98,280 bars, NOT 252
sessions — preserving ADR-0013 §3.1's "1 trading year" semantics
under the per-bar substrate frequency.

Per ADR-0013 §3.1 item 2 + Round-1 audit F-CONV-4 (preserved by H050
adaptation): single ``rng_seed`` across all arms × symbols; per-arm
offsets are FORBIDDEN. Seed is ``random_seed + 1000`` per H050.yaml
``random_seed: 20260420`` (post-F-R-2 fix). PW2004 block-length
selection runs on each arm's per-bar log-return LEVEL series
independently per F-CONV-3.

References
----------
- artifacts/runs/H050/31d23ecd8e3842dd8ebd5687ce9c91d5/{ES,NQ}/oos_returns.parquet
  (canonical H050 production walk-forward output; commit d8c6acd)
- research/01_hypothesis_register/H050/design.md §1 + §11
- docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md
  §3.1 (Realized-OOS + Forward-Projection mandate)
- scripts/simulate_h053_v4_10k_2026.py (reference implementation)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import polars as pl

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("simulate_h050_v1")

_STARTING_CAPITAL: float = 10_000.0
# 1 trading year of RTH 1-min bars = 252 sessions × 390 RTH bars/session
# (6.5 hours × 60 min/hour). Per ADR-0013 §3.1 item 2 "1 trading year"
# at the substrate frequency.
_RTH_BARS_PER_SESSION: int = 390
_PROJECTION_SESSIONS: int = 252
_PROJECTION_BARS: int = _PROJECTION_SESSIONS * _RTH_BARS_PER_SESSION  # 98,280

_N_BOOTSTRAP: int = 5_000
# H050.yaml random_seed: 20260420 (post-F-R-2 fix). Bootstrap offset
# +1000 per ADR-0013 §3.1 item 2 (single seed across all arms × symbols).
_H050_RANDOM_SEED: int = 20260420
_BOOTSTRAP_RNG_SEED: int = _H050_RANDOM_SEED + 1000  # 20261420

_DEFAULT_RUN_ID: str = "31d23ecd8e3842dd8ebd5687ce9c91d5"


def _max_drawdown_from_equity(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    return float(abs(dd.min()))


def _simulate_equity_curve(
    log_returns: np.ndarray, starting: float = _STARTING_CAPITAL
) -> tuple[np.ndarray, float, float]:
    cumlog = np.concatenate([[0.0], np.cumsum(log_returns)])
    equity = starting * np.exp(cumlog)
    return equity, float(equity[-1]), _max_drawdown_from_equity(equity)


def _bootstrap_projection(
    log_returns: np.ndarray,
    *,
    n_paths: int,
    n_bars: int,
    rng_seed: int,
) -> dict[str, Any]:
    """Per-bar bootstrap projection over n_bars (= 252 × 390 RTH bars by default).

    PW2004 block-length selection runs on the LEVEL series (per F-CONV-3
    H053 audit). iid bootstrap if selected block_length=1.0; otherwise
    stationary bootstrap (Politis-Romano 1994) with the selected length.
    """
    from skie_ninja.inference.bootstrap import (
        choose_block_length,
        stationary_bootstrap_indices,
    )

    rng = np.random.default_rng(rng_seed)
    n_oos = len(log_returns)
    block_length_selection = choose_block_length(log_returns)
    selected_b = float(block_length_selection.block_length)

    end_equities: list[float] = []
    max_dds: list[float] = []
    n_draw = max(n_oos, n_bars)
    for _ in range(n_paths):
        if selected_b <= 1.0:
            idx = rng.integers(0, n_oos, size=n_bars)
        else:
            full_idx = stationary_bootstrap_indices(
                n=n_draw,
                block_length=selected_b,
                rng=rng,
            )
            idx = (full_idx[:n_bars] % n_oos)
        path_returns = log_returns[idx]
        _, end_eq, max_dd = _simulate_equity_curve(path_returns)
        end_equities.append(end_eq)
        max_dds.append(max_dd)
    end_eq_arr = np.asarray(end_equities)
    max_dd_arr = np.asarray(max_dds)
    return {
        "n_paths": n_paths,
        "n_bars": n_bars,
        "n_sessions_equivalent": _PROJECTION_SESSIONS,
        "rth_bars_per_session": _RTH_BARS_PER_SESSION,
        "block_length_pw2004": selected_b,
        "block_length_method": "PW2004_on_level_series_per_F-CONV-3_H053_audit",
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


def _process_symbol(run_id: str, symbol: str) -> dict[str, Any]:
    parquet_path = (
        _REPO_ROOT
        / "artifacts"
        / "runs"
        / "H050"
        / run_id
        / symbol
        / "oos_returns.parquet"
    )
    _log.info("[%s] Loading %s", symbol, parquet_path)
    df = pl.read_parquet(str(parquet_path))
    gated = df["gated_return"].to_numpy()
    uncond = df["unconditional_return"].to_numpy()

    out: dict[str, Any] = {
        "symbol": symbol,
        "n_oos_bars": int(len(gated)),
        "n_oos_sessions_equivalent": float(len(gated)) / _RTH_BARS_PER_SESSION,
        "arms": {},
    }
    annualisation = np.sqrt(252.0 * _RTH_BARS_PER_SESSION)
    for arm_id, arm_ret in [
        ("hmm_gated", gated),
        ("unconditional", uncond),
    ]:
        equity, end_eq, max_dd = _simulate_equity_curve(arm_ret)
        sd = float(arm_ret.std(ddof=1))
        per_bar_sharpe = float(arm_ret.mean() / sd) if sd > 0 else float("nan")
        proj = _bootstrap_projection(
            arm_ret,
            n_paths=_N_BOOTSTRAP,
            n_bars=_PROJECTION_BARS,
            rng_seed=_BOOTSTRAP_RNG_SEED,
        )
        out["arms"][arm_id] = {
            "n_bars": int(len(arm_ret)),
            "mean_per_bar_log_return": float(arm_ret.mean()),
            "std_per_bar_log_return": sd,
            "per_bar_sharpe": per_bar_sharpe,
            "annualized_sharpe": (
                per_bar_sharpe * float(annualisation)
                if not np.isnan(per_bar_sharpe)
                else float("nan")
            ),
            "realized_oos": {
                "starting_equity": _STARTING_CAPITAL,
                "ending_equity": end_eq,
                "ending_pct_change": (end_eq / _STARTING_CAPITAL - 1.0) * 100,
                "max_drawdown_pct": max_dd * 100,
                "n_winning_bars": int((arm_ret > 0).sum()),
                "n_losing_bars": int((arm_ret < 0).sum()),
                "n_zero_bars": int((arm_ret == 0).sum()),
            },
            "projected_2026_98280bars": proj,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H050 v1 — $10k 2026 projection")
    parser.add_argument("--run-id", default=_DEFAULT_RUN_ID)
    parser.add_argument("--symbols", default="ES,NQ")
    parser.add_argument(
        "--output",
        default=str(_REPO_ROOT / "logs" / "simulate_h050_10k_2026.json"),
    )
    args = parser.parse_args(argv)

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    results: list[dict[str, Any]] = []
    for sym in symbols:
        results.append(_process_symbol(args.run_id, sym))

    out_payload = {
        "run_id": args.run_id,
        "rng_seed": _BOOTSTRAP_RNG_SEED,
        "n_bootstrap_paths": _N_BOOTSTRAP,
        "projection_horizon_bars": _PROJECTION_BARS,
        "projection_horizon_sessions": _PROJECTION_SESSIONS,
        "rth_bars_per_session": _RTH_BARS_PER_SESSION,
        "starting_capital": _STARTING_CAPITAL,
        "results": results,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out_payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    print()
    print("=" * 100)
    print(f"H050 v1 — $10,000 STARTING CAPITAL SIMULATION  |  run_id={args.run_id}")
    print(
        f"  Bootstrap: {_N_BOOTSTRAP:,} MC paths × {_PROJECTION_BARS:,} bars "
        f"(= {_PROJECTION_SESSIONS} sessions × {_RTH_BARS_PER_SESSION} RTH bars)"
    )
    print("=" * 100)
    for sym_result in results:
        sym = sym_result["symbol"]
        print(f"\n--- {sym} (n_oos_bars={sym_result['n_oos_bars']:,}) ---")
        for arm_id, arm in sym_result["arms"].items():
            r = arm["realized_oos"]
            p = arm["projected_2026_98280bars"]["ending_equity"]
            d = arm["projected_2026_98280bars"]["max_drawdown"]
            print(
                f"  {arm_id:14s}  ann_SR={arm['annualized_sharpe']:+.4f}  "
                f"realized: end=${r['ending_equity']:>9.2f}  "
                f"chg={r['ending_pct_change']:+.2f}%  max-DD={r['max_drawdown_pct']:.2f}%  "
                f"W/L/Z={r['n_winning_bars']:,}/{r['n_losing_bars']:,}/{r['n_zero_bars']:,}"
            )
            print(
                f"  {' ' * 14}  proj median=${p['median']:.2f}  q01=${p['q01']:.2f}  "
                f"q05=${p['q05']:.2f}  q95=${p['q95']:.2f}  q99=${p['q99']:.2f}  "
                f"P(loss)={p['p_loss']*100:.1f}%  P(<50%)={p['p_ruin50']*100:.1f}%  "
                f"DD median={d['median']*100:.2f}%  DD q95={d['q95']*100:.2f}%  "
                f"block_b={arm['projected_2026_98280bars']['block_length_pw2004']:.1f}"
            )

    _log.info("Wrote %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
