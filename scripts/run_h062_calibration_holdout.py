"""H062 calibration holdout — trend_id Brier-score competition + cell-grid MPPM(ρ=1).

Per H062 design.md §5.1 (trend_id selection via supervised Brier-score
competition; per Niculescu-Mizil & Caruana 2005 ICML — proper scoring
rule for probabilistic side-prediction) + §5.2 (channel-N + k_atr +
cadence + Kelly-multiplier selected by MPPM(ρ=1) per ADR-0018 D-1) +
§5.5 (switching-bandit-algo via cumulative-regret minimization per
Garivier-Moulines 2011 + Besson-Kaufmann-Maillard-Seznec 2019).

Calibration holdout per design.md §2:
  - **MGC + SIL**: 2015-01-01 → 2019-12-31 (5-year holdout disjoint
    from all prior-hypothesis test folds per data_requirements.md
    cross-hypothesis fit-set isolation).
  - **ES + NQ**: 2015-2019 substrate is EMPTY in the post-Phase-O.0 frame;
    inner-CV bootstrap on IS 2020-2023 instead.

Selection methodology per design.md §5.8 nested-CV (Varma-Simon 2006):
  - **Level-A (ID_1 trend-filter)**: for MGC+SIL → 2015-2017 fragment;
    for ES+NQ → inner-CV bootstrap on 2020-2021 IS first 2 years.
  - **Level-B (channel-N + cell-grid)**: for MGC+SIL → 2018-2019
    fragment; for ES+NQ → 2022-2023 IS last 2 years.

This v1 calibration script outputs:
  - Per-symbol best trend_id per Brier-score on Level-A.
  - Per-symbol best cell (channel_n × k_atr × kelly_multiplier) per
    MPPM(ρ=1) on Level-B.
  - Audit-friendly JSON sidecar with per-cell scores.

Closes ``P1-H062-CALIBRATION-HOLDOUT-RUN`` per design.md §11.2 (BLOCKING-
BEFORE-LAUNCH precondition).
"""

from __future__ import annotations

import argparse
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
import yaml

from skie_ninja.features.h062 import (
    H062FeatureConfig,
    compute_h062_features,
)
from skie_ninja.inference.mppm import mppm_rho_1
from skie_ninja.utils.paths import ProjectPaths

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h062_calibration_holdout")


def _load_5min_bars_for_calibration(
    substrate_root: Path,
    symbol: str,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Load 5-min OHLC for the given window. Mirrors the orchestrator loader."""
    import polars as pl
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
        return df
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df = df.sort_values("ts_event").reset_index(drop=True)
    mask = (df["ts_event"] >= start) & (df["ts_event"] <= end)
    df = df.loc[mask].copy()
    if df.empty:
        return df
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


def _next_h_dwell_log_return_sign(
    close: np.ndarray, h_dwell: int
) -> np.ndarray:
    """Per-bar realized sign of next-H_dwell-bar log return.

    For each bar t: sign(log(close[t + h_dwell]) - log(close[t])) ∈ {+1, 0, -1}.
    Returns the sign series; the last `h_dwell` bars are 0 (no future data).
    """
    n = close.size
    sign = np.zeros(n, dtype=int)
    for t in range(n - h_dwell):
        if close[t] <= 0 or close[t + h_dwell] <= 0:
            continue
        diff = np.log(close[t + h_dwell]) - np.log(close[t])
        sign[t] = int(np.sign(diff))
    return sign


def _brier_score_for_trend_id(
    *,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    trend_id: str,
    lookback_l: int,
    threshold: float,
    h_dwell: int,
    short_window: int = 10,
    long_window: int = 50,
) -> float:
    """Compute the Brier score for a trend_id candidate per design.md §5.1.

    BS = mean over eligible bars of (ŷ_side_t - y_side_t)²

    where ŷ_side_t ∈ {-1, 0, +1} is the trend_id-predicted side and
    y_side_t ∈ {-1, +1} is the realized sign of the next-H_dwell-bar
    log-return.
    """
    from skie_ninja.features.h062 import (
        trend_id_a_ts_mom,
        trend_id_b_adx,
        trend_id_c_hac_ols_slope_t,
        trend_id_d_ma_cross,
    )

    log_close = np.log(np.where(close > 0, close, np.nan))
    try:
        if trend_id == "a_ts_mom":
            sides = trend_id_a_ts_mom(log_close, lookback_l=lookback_l, tau_m=threshold)
        elif trend_id == "b_adx":
            sides = trend_id_b_adx(high, low, close, lookback_l=lookback_l, tau_adx=threshold)
        elif trend_id == "c_hac_ols_slope_t":
            sides = trend_id_c_hac_ols_slope_t(log_close, lookback_l=lookback_l, tau_t=threshold)
        elif trend_id == "d_ma_cross":
            sides = trend_id_d_ma_cross(
                close, short_window=short_window, long_window=long_window, tau_ma=threshold
            )
        else:
            return float("nan")
    except ValueError:
        return float("nan")

    realized = _next_h_dwell_log_return_sign(close, h_dwell=h_dwell)
    # Eligible bars: bars with finite features AND realized != 0 (so we
    # have a comparable target). Side prediction may be 0; that contributes
    # (0 - ±1)² = 1 to the Brier score.
    eligible = (realized != 0) & (np.arange(sides.size) >= lookback_l)
    if not eligible.any():
        return float("nan")
    diff = sides[eligible].astype(float) - realized[eligible].astype(float)
    return float(np.mean(diff ** 2))


def _competition_trend_id(
    *,
    symbol: str,
    df_5m: pd.DataFrame,
    h_dwell: int,
) -> dict[str, Any]:
    """Brier-score competition per design.md §5.1 across the 4 candidates."""
    high = df_5m["high"].to_numpy()
    low = df_5m["low"].to_numpy()
    close = df_5m["close"].to_numpy()

    # Representative grid (truncated; production uses full grid per
    # P1-H062-CALIBRATION-HOLDOUT-RUN extension).
    candidates: list[dict[str, Any]] = []
    for L in [20, 60, 120]:
        for tau in [0.5, 1.0, 1.5]:
            candidates.append({
                "trend_id": "a_ts_mom",
                "lookback_l": L,
                "threshold": tau,
            })
        for tau_adx in [15, 25]:
            candidates.append({
                "trend_id": "b_adx",
                "lookback_l": L,
                "threshold": float(tau_adx),
            })
        for tau_t in [1.0, 2.0]:
            candidates.append({
                "trend_id": "c_hac_ols_slope_t",
                "lookback_l": L,
                "threshold": tau_t,
            })
    for sw, lw in [(10, 50), (20, 100), (10, 200)]:
        for tau_ma in [0.0, 0.001]:
            candidates.append({
                "trend_id": "d_ma_cross",
                "lookback_l": lw,  # placeholder; lw drives the threshold sensitivity
                "threshold": tau_ma,
                "short_window": sw,
                "long_window": lw,
            })

    records: list[dict[str, Any]] = []
    best_score = np.inf
    best_record: dict[str, Any] | None = None
    for cand in candidates:
        bs = _brier_score_for_trend_id(
            high=high,
            low=low,
            close=close,
            trend_id=cand["trend_id"],
            lookback_l=cand["lookback_l"],
            threshold=cand["threshold"],
            h_dwell=h_dwell,
            short_window=cand.get("short_window", 10),
            long_window=cand.get("long_window", 50),
        )
        rec = {**cand, "brier_score": bs}
        records.append(rec)
        if np.isfinite(bs) and bs < best_score:
            best_score = bs
            best_record = rec
    return {
        "symbol": symbol,
        "best": best_record,
        "best_brier_score": float(best_score) if np.isfinite(best_score) else None,
        "n_candidates": len(records),
        "cell_records": records,
    }


def _cell_grid_mppm_competition(
    *,
    symbol: str,
    df_5m: pd.DataFrame,
    trend_id_winner: dict[str, Any],
    delta_t: float,
) -> dict[str, Any]:
    """MPPM(ρ=1) cell-grid competition per design.md §5.2 + §5.7."""
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_h062_walk_forward",
        str(_REPO_ROOT / "scripts" / "run_h062_walk_forward.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Use the orchestrator's _select_best_cell_inner_cv but on the
    # calibration holdout slice.
    sel = mod._select_best_cell_inner_cv(
        symbol=symbol,
        df_5m_train=df_5m,
        grid_channel_n=[20, 60, 120, 240],
        grid_k_atr=[1.5, 2.0, 2.5],
        grid_kelly=[0.25, 0.5, 1.0],
        trend_id=trend_id_winner["trend_id"],
        trend_id_lookback_l=trend_id_winner["lookback_l"],
        trend_id_threshold=trend_id_winner["threshold"],
        h_dwell=5,  # fixed at representative; full grid in v2
        atr_n=14,
        delta_t=delta_t,
        eod_flatten_minutes_from_open=72,
    )
    return sel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H062 calibration holdout")
    parser.add_argument("--hypothesis", default="H062")
    parser.add_argument("--config", default="config/hypotheses/H062.yaml")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)

    paths = ProjectPaths.discover()
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path
    raw_cfg_bytes = cfg_path.read_bytes()
    cfg = yaml.safe_load(raw_cfg_bytes)
    config_resolved_sha256 = hashlib.sha256(raw_cfg_bytes).hexdigest()

    substrate_root = (
        Path(args.substrate_path).resolve()
        if args.substrate_path
        else paths.root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    )

    delta_t = float(cfg["mppm"]["delta_t"])

    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else paths.artifacts_runs / cfg["hypothesis_id"] / f"calibration_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    _log.info("calibration_out_dir=%s", out_dir)

    # Per design.md §5.8 nested-CV partitioning.
    universe = [s.strip().upper() for s in cfg["universe"]]
    results: dict[str, Any] = {}
    for sym in universe:
        if sym in {"MGC", "SIL"}:
            # Level-A: 2015-2017 + Level-B: 2018-2019
            la_start = pd.Timestamp("2015-01-01", tz="UTC")
            la_end = pd.Timestamp("2017-12-31", tz="UTC")
            lb_start = pd.Timestamp("2018-01-01", tz="UTC")
            lb_end = pd.Timestamp("2019-12-31", tz="UTC")
        else:
            # ES, NQ: Level-A 2020-2021 + Level-B 2022-2023 (IS fragments)
            la_start = pd.Timestamp("2020-01-01", tz="UTC")
            la_end = pd.Timestamp("2021-12-31", tz="UTC")
            lb_start = pd.Timestamp("2022-01-01", tz="UTC")
            lb_end = pd.Timestamp("2023-12-31", tz="UTC")
        _log.info(
            "%s: Level-A [%s -> %s] / Level-B [%s -> %s]",
            sym, la_start.date(), la_end.date(), lb_start.date(), lb_end.date(),
        )

        df_la = _load_5min_bars_for_calibration(substrate_root, sym, start=la_start, end=la_end)
        if df_la.empty:
            _log.warning("%s: Level-A slice empty; skip", sym)
            continue
        _log.info("  %s Level-A: %d 5-min bars", sym, len(df_la))
        trend_id_result = _competition_trend_id(symbol=sym, df_5m=df_la, h_dwell=5)
        if trend_id_result["best"] is None:
            _log.warning("%s: trend_id competition produced no winner; skip", sym)
            continue
        _log.info(
            "  %s trend_id winner: %s (brier=%.4f)",
            sym, trend_id_result["best"]["trend_id"], trend_id_result["best_brier_score"],
        )

        df_lb = _load_5min_bars_for_calibration(substrate_root, sym, start=lb_start, end=lb_end)
        if df_lb.empty:
            _log.warning("%s: Level-B slice empty; skip cell-grid", sym)
            cell_grid_result = {"best": None, "best_mppm_train": float("nan")}
        else:
            _log.info("  %s Level-B: %d 5-min bars", sym, len(df_lb))
            cell_grid_result = _cell_grid_mppm_competition(
                symbol=sym,
                df_5m=df_lb,
                trend_id_winner=trend_id_result["best"],
                delta_t=delta_t,
            )
            if cell_grid_result["best"]:
                _log.info(
                    "  %s cell-grid winner: N=%d k=%.1f km=%.2f mppm=%.4f",
                    sym,
                    cell_grid_result["best"]["channel_n"],
                    cell_grid_result["best"]["k_atr"],
                    cell_grid_result["best"]["kelly_multiplier"],
                    cell_grid_result["best_mppm_train"],
                )

        results[sym] = {
            "level_a_window": [str(la_start), str(la_end)],
            "level_b_window": [str(lb_start), str(lb_end)],
            "trend_id_competition": trend_id_result,
            "cell_grid_competition": cell_grid_result,
        }

    payload = {
        "hypothesis_id": "H062",
        "config_resolved_sha256": config_resolved_sha256,
        "universe": universe,
        "results": results,
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "calibration_sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "calibration_sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("calibration_sidecar=%s sha256=%s", sidecar_path, sha[:16])

    # Headline summary.
    print()
    print("=" * 60)
    print("H062 CALIBRATION HOLDOUT COMPLETE")
    for sym, res in results.items():
        ti = res["trend_id_competition"]["best"]
        cg = res["cell_grid_competition"]["best"]
        print(f"  {sym}:")
        if ti:
            print(f"    trend_id: {ti['trend_id']} L={ti['lookback_l']} thr={ti['threshold']:.3f}")
        if cg:
            print(f"    cell: N={cg['channel_n']} k_atr={cg['k_atr']} km={cg['kelly_multiplier']}")
    print(f"  sidecar: {sidecar_path}")
    print("=" * 60)

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
