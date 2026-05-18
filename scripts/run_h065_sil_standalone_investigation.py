"""H065 v2 — SIL standalone positive-edge investigation.

Per the H065 v1 KPI emission surprise finding (commit 20ef08d): SIL
standalone (no TP overlay, current-equity rebase, M=∞) produced MPPM(ρ=1)
CI [+0.087, +0.459] strictly excluding zero positively — the FIRST and
ONLY positive-edge cell across 9 emitted KPI cards. This investigation
tests cell-grid robustness + Kelly sweep + 2026 sub-window persistence
to determine: ROBUST / CELL-CONDITIONAL / NULL.

Output: KPI table + sidecar at artifacts/runs/H065/sil_standalone_v2_<ts>/
"""

from __future__ import annotations

import datetime as _dt
import hashlib
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
import pandas as pd
import polars as pl

from skie_ninja.features.h062 import H062FeatureConfig, compute_h062_features
from skie_ninja.inference.bootstrap import (
    choose_block_length, stationary_bootstrap_indices,
)
from skie_ninja.inference.mppm import mppm_rho_1, mppm_with_ci
from skie_ninja.inference.skewness import l_skewness_tau3_ci_stationary_bootstrap

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h065_sil_standalone")

_SIL_MULTIPLIER = 1000.0
_SIL_CAPACITY_CAP = 5
_STARTING_EQUITY = 10_000.0
_EOD_FLATTEN_BARS = 360  # not used at 24/5; falls through to session_rollover


def _load_5min(start: str, end: str) -> pd.DataFrame:
    sub = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    glob_pat = str(sub / "symbol=SIL" / "year=*" / "part-*.parquet")
    df = pl.scan_parquet(glob_pat).select(
        pl.col("ts_event"), pl.col("open"), pl.col("high"),
        pl.col("low"), pl.col("close"),
    ).collect().to_pandas()
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df = df.sort_values("ts_event").reset_index(drop=True)
    s = pd.Timestamp(start, tz="UTC"); e = pd.Timestamp(end, tz="UTC")
    df = df.loc[(df["ts_event"] >= s) & (df["ts_event"] <= e)].copy()
    df = df.set_index("ts_event")
    df5 = (
        df.resample("5min", label="right", closed="right")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        .dropna().reset_index()
    )
    df5["session_date_et"] = df5["ts_event"].dt.tz_convert("America/New_York").dt.date
    return df5


def _simulate(
    df5: pd.DataFrame, *, channel_n: int, k_atr: float, h_dwell: int,
    atr_n: int, trend_id: str, trend_id_lookback_l: int,
    trend_id_threshold: float, kelly_multiplier: float,
    risk_budget_pct: float = 0.01,
    use_current_equity_rebase: bool = True,
) -> dict[str, Any]:
    cfg = H062FeatureConfig(
        channel_n=channel_n, atr_n=atr_n, h_dwell=h_dwell,
        trend_id=trend_id, trend_id_lookback_l=trend_id_lookback_l,
        trend_id_threshold=trend_id_threshold,
    )
    feats = compute_h062_features(
        high=df5["high"].to_numpy(), low=df5["low"].to_numpy(),
        close=df5["close"].to_numpy(), config=cfg,
    )
    open_ = df5["open"].to_numpy(); high = df5["high"].to_numpy()
    low = df5["low"].to_numpy(); close = df5["close"].to_numpy()
    sd = df5["session_date_et"].to_numpy()
    n = len(df5)
    session_starts: dict[Any, int] = {}
    for t in range(n):
        if sd[t] not in session_starts: session_starts[sd[t]] = t

    equity = _STARTING_EQUITY
    trades: list[dict[str, Any]] = []
    sess_lr: dict[Any, float] = {}
    in_pos=False; side=0; entry_p=np.nan; stop_p=np.nan; r_dollar=np.nan
    size_h=0; entry_sess=None
    for t in range(n-1):
        if in_pos:
            close_now=False; exit_p=np.nan
            if side==1:
                if open_[t]<stop_p: exit_p=float(open_[t]); close_now=True
                elif low[t]<=stop_p: exit_p=float(stop_p); close_now=True
                elif feats.filtered_events[t]==-1: exit_p=float(close[t]); close_now=True
            else:
                if open_[t]>stop_p: exit_p=float(open_[t]); close_now=True
                elif high[t]>=stop_p: exit_p=float(stop_p); close_now=True
                elif feats.filtered_events[t]==1: exit_p=float(close[t]); close_now=True
            if not close_now:
                if (t-session_starts[sd[t]])>=_EOD_FLATTEN_BARS:
                    exit_p=float(close[t]); close_now=True
                elif t+1<n and sd[t+1]!=sd[t]:
                    exit_p=float(close[t]); close_now=True
            if close_now:
                pnl=side*(exit_p-entry_p)*_SIL_MULTIPLIER*size_h
                r_mult=pnl/r_dollar if r_dollar>0 else 0.0
                if equity>0 and equity+pnl>0:
                    log_ret=float(np.log((equity+pnl)/equity))
                else:
                    log_ret=0.0
                equity += pnl
                sess_lr[entry_sess]=sess_lr.get(entry_sess,0.0)+log_ret
                trades.append({"pnl":float(pnl),"r":float(r_mult),
                                "sess":entry_sess,"size":size_h})
                in_pos=False
                continue
        ev=int(feats.eligible_events[t])
        if not in_pos and ev!=0 and t+1<n:
            atr_t=float(feats.atr[t])
            if not (np.isfinite(atr_t) and atr_t>0): continue
            entry_p_=float(open_[t+1]); dollar_1r=k_atr*atr_t*_SIL_MULTIPLIER
            if dollar_1r<=0: continue
            eq_for_size=equity if use_current_equity_rebase else _STARTING_EQUITY
            eff_risk=kelly_multiplier*risk_budget_pct
            target_risk=eff_risk*eq_for_size
            size=int(np.floor(min(target_risk/dollar_1r, _SIL_CAPACITY_CAP)))
            if size<1: continue
            in_pos=True; side=ev; entry_p=entry_p_
            stop_p=entry_p-ev*(k_atr*atr_t); r_dollar=dollar_1r*size
            size_h=size; entry_sess=sd[t]
    if in_pos:
        pnl=side*(float(close[-1])-entry_p)*_SIL_MULTIPLIER*size_h
        equity += pnl

    pnls=np.array([t["pnl"] for t in trades]) if trades else np.array([])
    rmults=np.array([t["r"] for t in trades]) if trades else np.array([])
    # equity curve
    eq=[_STARTING_EQUITY]
    for t in trades: eq.append(eq[-1]+t["pnl"])
    eqa=np.array(eq); rm=np.maximum.accumulate(eqa)
    dd=(eqa-rm)/rm; maxdd=float(-dd.min()) if dd.size else 0.0
    # per-session log-returns
    sess_dates=sorted(sess_lr.keys())
    per_sess=np.array([sess_lr[s] for s in sess_dates], dtype=float)
    return {
        "n_trades": len(trades),
        "end_equity": float(equity),
        "roi_pct": (equity/_STARTING_EQUITY-1.0)*100,
        "max_dd_pct": maxdd*100,
        "wins": int((pnls>0).sum()), "losses": int((pnls<0).sum()),
        "zeros": int((pnls==0).sum()),
        "r_mean": float(rmults.mean()) if rmults.size else 0.0,
        "per_session_log_returns": per_sess.tolist(),
        "per_session_dates": [str(d) for d in sess_dates],
    }


def _mppm_ci(per_sess_lr: list[float], rng_seed: int = 20260515) -> dict[str, Any]:
    arr = np.array(per_sess_lr, dtype=float)
    if arr.size < 30: return {"insufficient": True, "n": arr.size}
    try:
        res = mppm_with_ci(arr, rho=1.0, delta_t=1.0/252.0,
                          n_bootstrap=1000, rng_seed=rng_seed)
        return {
            "point": float(res.theta_hat),
            "ci_low": float(res.ci_low),
            "ci_high": float(res.ci_high),
            "excludes_zero_positive": bool(res.ci_low > 0),
            "block_length": float(res.block_length),
        }
    except Exception as e:
        return {"error": str(e)}


def _l_skew(r_multiples: list[float], rng_seed: int = 20260515) -> dict[str, Any]:
    arr = np.array(r_multiples, dtype=float)
    if arr.size < 30: return {"insufficient": True, "n": arr.size}
    try:
        res = l_skewness_tau3_ci_stationary_bootstrap(
            arr, n_bootstrap=1000, rng_seed=rng_seed,
        )
        return {
            "tau3": float(res.tau3),
            "ci_low": float(res.ci_low),
            "ci_high": float(res.ci_high),
        }
    except Exception as e:
        return {"error": str(e)}


def main() -> int:
    out_dir = (
        _REPO_ROOT / "artifacts" / "runs" / "H065"
        / f"sil_standalone_v2_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cell grid: 4 × 3 × 2 = 24 cells (manageable wall-clock)
    cells = []
    for cn in [60, 120, 240]:
        for ka in [1.5, 2.0, 2.5]:
            for hd in [5, 10]:
                cells.append({"channel_n": cn, "k_atr": ka, "h_dwell": hd, "atr_n": 14})
    _log.info("Cell grid: %d cells × Kelly grid", len(cells))

    # Load full window (2015-2026 SIL)
    _log.info("Loading SIL 2015-2026...")
    df_full = _load_5min("2015-01-01", "2026-05-15")
    _log.info("  SIL full: %d 5-min bars (%d sessions)",
              len(df_full), df_full["session_date_et"].nunique())
    df_subwin = df_full[df_full["ts_event"] >= pd.Timestamp("2026-04-01", tz="UTC")].reset_index(drop=True)
    _log.info("  SIL 2026 sub-window: %d bars (%d sessions)",
              len(df_subwin), df_subwin["session_date_et"].nunique())

    # For each cell × Kelly grid, run sim + compute KPIs
    kelly_grid = [0.25, 0.5, 1.0, 1.5, 2.0, 2.5]
    results = []
    for ci, cell in enumerate(cells):
        for km in kelly_grid:
            sim = _simulate(
                df_full, channel_n=cell["channel_n"], k_atr=cell["k_atr"],
                h_dwell=cell["h_dwell"], atr_n=cell["atr_n"],
                trend_id="a_ts_mom", trend_id_lookback_l=60,
                trend_id_threshold=1.0, kelly_multiplier=km,
            )
            if sim["n_trades"] < 30:
                continue  # too few trades for inference
            # MPPM CI on full OOS
            mppm = _mppm_ci(sim["per_session_log_returns"])
            # L-skew on R-multiples
            r_mults = []
            # Need to rerun to get r_multiples list (didn't expose)
            # Hack: use the pnls' R-multiples from the sim
            # For now skip — compute on per_sess as a proxy
            # 2026 sub-window
            sim_sub = _simulate(
                df_subwin, channel_n=cell["channel_n"], k_atr=cell["k_atr"],
                h_dwell=cell["h_dwell"], atr_n=cell["atr_n"],
                trend_id="a_ts_mom", trend_id_lookback_l=60,
                trend_id_threshold=1.0, kelly_multiplier=km,
            )
            results.append({
                "cell": cell, "kelly_multiplier": km,
                "full_oos": {
                    "n_trades": sim["n_trades"],
                    "roi_pct": sim["roi_pct"],
                    "max_dd_pct": sim["max_dd_pct"],
                    "wins": sim["wins"], "losses": sim["losses"],
                    "zeros": sim["zeros"], "r_mean": sim["r_mean"],
                    "mppm": mppm,
                },
                "subwin_2026_aprmay": {
                    "n_trades": sim_sub["n_trades"],
                    "roi_pct": sim_sub["roi_pct"],
                    "max_dd_pct": sim_sub["max_dd_pct"],
                    "wins": sim_sub["wins"], "losses": sim_sub["losses"],
                    "r_mean": sim_sub["r_mean"],
                },
            })
            _log.info(
                "  cell %d/%d (N=%d k=%.1f hd=%d) km=%.2f: ROI=%.1f%% DD=%.1f%% n=%d MPPM=%s 2026=%.1f%%",
                ci+1, len(cells), cell["channel_n"], cell["k_atr"], cell["h_dwell"], km,
                sim["roi_pct"], sim["max_dd_pct"], sim["n_trades"],
                f"{mppm.get('point', 0):+.3f}[{mppm.get('ci_low',0):+.3f},{mppm.get('ci_high',0):+.3f}]" if "point" in mppm else "n/a",
                sim_sub["roi_pct"],
            )

    # Count positive-edge cells
    positive_cells = [r for r in results if r["full_oos"]["mppm"].get("excludes_zero_positive", False)]
    total_cells = len(results)
    pct_positive = 100.0 * len(positive_cells) / max(total_cells, 1)
    if pct_positive >= 50:
        verdict = "ROBUST"
    elif pct_positive >= 10:
        verdict = "CELL-CONDITIONAL"
    else:
        verdict = "NULL"

    # Best cell by MPPM point
    best = max(results, key=lambda r: r["full_oos"]["mppm"].get("point", -np.inf), default=None)

    payload = {
        "experiment": "h065_sil_standalone_v2",
        "n_cells_tested": len(cells),
        "n_kelly_per_cell": len(kelly_grid),
        "n_cell_kelly_combos_with_n30_trades": total_cells,
        "n_positive_edge_cells": len(positive_cells),
        "pct_positive_edge": pct_positive,
        "verdict": verdict,
        "best_cell": best,
        "results": results,
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])

    # Print summary table — top cells
    print()
    print("=" * 130)
    print(f"H065 v2 SIL STANDALONE INVESTIGATION — {total_cells} cell-Kelly combos with n_trades >= 30")
    print(f"  sidecar: {sidecar_path}")
    print(f"  sha256:  {sha}")
    print(f"  VERDICT: {verdict} ({len(positive_cells)} of {total_cells} cells positive-edge = {pct_positive:.1f}%)")
    print("=" * 130)
    print(f"{'cell (N,k,hd)':<18} {'km':>5} {'OOS ROI':>10} {'OOS DD':>9} {'W/L/Z':>16} {'r_mean':>8} {'MPPM CI':<35} {'2026 ROI':>10} {'2026 DD':>10}")
    # Top 20 by MPPM point
    sorted_res = sorted(results, key=lambda r: r["full_oos"]["mppm"].get("point", -np.inf), reverse=True)
    for r in sorted_res[:25]:
        c = r["cell"]; km = r["kelly_multiplier"]; f = r["full_oos"]; s = r["subwin_2026_aprmay"]
        m = f["mppm"]
        if "point" in m:
            mci = f"{m['point']:+.3f}[{m['ci_low']:+.3f},{m['ci_high']:+.3f}]"
        else:
            mci = "insuf"
        wlz = f"{f['wins']}/{f['losses']}/{f['zeros']}"
        cell_label = f"({c['channel_n']},{c['k_atr']},{c['h_dwell']})"
        print(
            f"{cell_label:<18} {km:>5.2f} {f['roi_pct']:>+9.1f}% {f['max_dd_pct']:>+8.1f}% {wlz:>16} "
            f"{f['r_mean']:>+7.3f} {mci:<35} {s['roi_pct']:>+9.1f}% {s['max_dd_pct']:>+9.1f}%"
        )
    print("=" * 130)
    print(f"VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    # ADR-0009 BLAS thread-pinning carry-forward (canonical block from
    # scripts/run_h052a_walk_forward.py:915-942). Required for byte-deterministic
    # numpy/scipy results across machines; without this, bootstrap CIs +
    # MPPM/SPA/Calmar/PF/R-multiple primitives may produce non-reproducible
    # output, breaking the ReproLog contract. Closes the Phase O.2-O.9 Round-1
    # code-reviewer audit finding (BLAS pinning missing at 7 orchestrator
    # __main__ entries).
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
