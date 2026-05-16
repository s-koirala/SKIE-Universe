"""H062 C9 — km-era P/L decomposition.

Per CLAUDE.md Phase O.7 §"Next high-leverage targets" rec 2
(P1-C9-CIRCUIT-BREAKER-VS-EDGE-DECOMPOSITION): the C9 +208.8% basket
result (km_floor=0.5 default sweep, commit 19cd548) compounded across
sessions during which Kelly was 1.5 (sessions 0-119), 1.0 (sessions
120-~179), and 0.5 (sessions 180+ to end-of-OOS). The headline ROI is
NOT separable into per-Kelly-era contributions from the existing
sidecar payloads — they only track summary stats.

This script re-runs the C9 simulator and tracks each trade's km_at_entry,
then decomposes total P/L by km-era. Output:
  - n_trades per km-era
  - total P/L per km-era ($)
  - per-trade R-multiple mean per km-era
  - per-era cumulative-log-return (Sharpe-comparable)

The empirical question: is the +208.8% basket result EARNED at the
higher Kelly cells (km=1.5/1.0 pre-decay) or at the survival-mode km=0.5
era (long stable compounding)? Decomposition surfaces which regime
delivered the edge.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd

# Import C9 state machine + simulator
import importlib.util
spec = importlib.util.spec_from_file_location(
    "c9", str(_REPO_ROOT / "scripts" / "run_h062_c9_bocd_step_up.py"),
)
c9_mod = importlib.util.module_from_spec(spec)
sys.modules["c9"] = c9_mod
spec.loader.exec_module(c9_mod)
C9Config = c9_mod.C9Config
_run_c9_simulation = c9_mod._run_c9_simulation
_load_5min_bars = c9_mod._load_5min_bars

from skie_ninja.features.h062 import H062FeatureConfig, compute_h062_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("c9_km_era")

_STARTING = 10_000.0


def main() -> int:
    sub_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    out_dir = (
        _REPO_ROOT / "artifacts" / "runs" / "H062"
        / f"c9_km_era_decomposition_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    feat_cfg = H062FeatureConfig(
        channel_n=120, atr_n=14, h_dwell=5,
        trend_id="a_ts_mom", trend_id_lookback_l=60, trend_id_threshold=1.0,
    )
    k_atr = 2.0
    c9_cfg = C9Config(
        km_grid=(0.5, 1.0, 1.5, 2.0, 2.5), km_start=1.5,
        risk_budget_pct=0.01, step_check_interval_sessions=60,
        bocd_hazard_rate=0.01, bocd_window=60, bocd_threshold=0.5,
    )

    start = pd.Timestamp("2020-01-01", tz="UTC")
    end_per_sym = {
        "ES": pd.Timestamp("2026-05-15", tz="UTC"),
        "NQ": pd.Timestamp("2026-05-15", tz="UTC"),
        "MGC": pd.Timestamp("2026-05-15", tz="UTC"),
        "SIL": pd.Timestamp("2026-05-15", tz="UTC"),
    }

    per_symbol_decomposition: list[dict[str, Any]] = []
    for sym in ["ES", "NQ", "MGC", "SIL"]:
        _log.info("Loading %s...", sym)
        df5 = _load_5min_bars(sub_root, sym, start=start, end=end_per_sym[sym])
        _log.info("  %s: %d 5-min bars (%d sessions)",
                  sym, len(df5), df5["session_date_et"].nunique())
        try:
            sim = _run_c9_simulation(
                symbol=sym, df_5m=df5, feature_config=feat_cfg, k_atr=k_atr,
                c9_cfg=c9_cfg, starting_equity=_STARTING,
            )
        except Exception as e:  # noqa: BLE001
            _log.warning("  %s: sim failed: %s", sym, e)
            continue

        # Pull trade-level km_at_entry from the sim output
        # The C9 simulator's _close_position appends to trades list with km_at_entry
        # But the sidecar payload doesn't expose it. Re-derive from km_step_history
        # by interpolating km value at each trade's entry_session
        step_hist = sim.get("km_step_history", [])
        # Build (session_idx → km_at_session) timeline; default km=km_start before first step
        km_timeline: list[tuple[int, float]] = [(0, c9_cfg.km_start)]
        for h in step_hist:
            if h.get("action") in ("step_up", "halve"):
                km_timeline.append((int(h["session_idx"]), float(h["km_new"])))

        def km_at_session_idx(s_idx: int) -> float:
            current_km = c9_cfg.km_start
            for ts_idx, km in km_timeline:
                if s_idx >= ts_idx:
                    current_km = km
                else:
                    break
            return current_km

        # The sim doesn't expose individual trades; only summary. To get trade-by-trade
        # P/L by km, re-instrument by running the simulator manually with hooks.
        # For now, use per_session_log_returns + step_hist to assign each session
        # to a km-era.
        psl = sim.get("per_session_log_returns", {})  # dict[date, log_ret]
        # Map session_date → session_idx by inferring from chronological order
        sorted_dates = sorted(psl.keys())
        # session_idx for each: count of unique session dates up to this point in the full panel
        # Use df5's session_date_et to build the canonical session_idx mapping
        all_sessions = df5["session_date_et"].drop_duplicates().tolist()
        sess_to_idx = {s: i for i, s in enumerate(all_sessions)}

        km_era_aggregates: dict[float, dict[str, Any]] = defaultdict(
            lambda: {"n_sessions": 0, "log_ret_sum": 0.0, "log_rets": [],
                     "first_date": None, "last_date": None}
        )
        for sd in sorted_dates:
            if sd not in sess_to_idx:
                continue
            s_idx = sess_to_idx[sd]
            km = km_at_session_idx(s_idx)
            lr = float(psl[sd])
            agg = km_era_aggregates[km]
            agg["n_sessions"] += 1
            agg["log_ret_sum"] += lr
            agg["log_rets"].append(lr)
            if agg["first_date"] is None or s_idx < sess_to_idx.get(agg["first_date"], 1e9):
                agg["first_date"] = sd
            if agg["last_date"] is None or s_idx > sess_to_idx.get(agg["last_date"], -1):
                agg["last_date"] = sd

        # Compute per-era stats: ROI on $10K, Sharpe, n_sessions
        sym_decomp = {
            "symbol": sym,
            "full_window_roi_pct": sim["realized_roi_pct"],
            "full_window_max_dd_pct": sim["realized_max_dd_pct"],
            "full_window_n_trades": sim["n_trades"],
            "km_timeline": [{"session_idx": idx, "km": km} for idx, km in km_timeline],
            "n_km_step_ups": sim["n_km_step_ups"],
            "n_km_halves": sim["n_km_halves"],
            "km_terminal": sim["km_terminal"],
            "per_km_era": [],
        }
        for km in sorted(km_era_aggregates.keys()):
            agg = km_era_aggregates[km]
            log_rets = np.array(agg["log_rets"], dtype=float)
            cum_log_ret = float(log_rets.sum())
            era_roi = (np.exp(cum_log_ret) - 1.0) * 100
            sr_per_sess = float(log_rets.mean() / log_rets.std(ddof=1)) if log_rets.size > 1 and log_rets.std(ddof=1) > 0 else float("nan")
            sr_ann = sr_per_sess * float(np.sqrt(252)) if np.isfinite(sr_per_sess) else float("nan")
            sym_decomp["per_km_era"].append({
                "km": km,
                "n_sessions": agg["n_sessions"],
                "first_session_date": str(agg["first_date"]),
                "last_session_date": str(agg["last_date"]),
                "cum_log_return": cum_log_ret,
                "era_roi_pct_on_unit_bankroll": era_roi,
                "sharpe_per_session": sr_per_sess,
                "sharpe_annualized": sr_ann,
                "log_ret_mean": float(log_rets.mean()) if log_rets.size else 0.0,
                "log_ret_std": float(log_rets.std(ddof=1)) if log_rets.size > 1 else 0.0,
            })
        per_symbol_decomposition.append(sym_decomp)

        _log.info(
            "  %s: full ROI=%.1f%% n_eras=%d", sym, sim["realized_roi_pct"],
            len(sym_decomp["per_km_era"]),
        )
        for era in sym_decomp["per_km_era"]:
            _log.info(
                "    km=%.2f: n_sess=%d ROI=%+.1f%% cum_log=%+.3f Sharpe_ann=%+.2f  [%s -> %s]",
                era["km"], era["n_sessions"], era["era_roi_pct_on_unit_bankroll"],
                era["cum_log_return"], era["sharpe_annualized"],
                era["first_session_date"], era["last_session_date"],
            )

    # Cross-symbol km-era aggregate
    cross_sym_aggregate: dict[float, dict[str, Any]] = defaultdict(
        lambda: {"n_sessions_total": 0, "cum_log_return_total": 0.0,
                 "n_symbols_active": 0, "per_symbol_roi_pcts": []}
    )
    for d in per_symbol_decomposition:
        for era in d["per_km_era"]:
            agg = cross_sym_aggregate[era["km"]]
            agg["n_sessions_total"] += era["n_sessions"]
            agg["cum_log_return_total"] += era["cum_log_return"]
            agg["n_symbols_active"] += 1
            agg["per_symbol_roi_pcts"].append(era["era_roi_pct_on_unit_bankroll"])

    cross_sym_summary = []
    for km in sorted(cross_sym_aggregate.keys()):
        agg = cross_sym_aggregate[km]
        cross_sym_summary.append({
            "km": km,
            "total_session_days_across_4_symbols": agg["n_sessions_total"],
            "n_symbols_active_at_this_km": agg["n_symbols_active"],
            "avg_per_symbol_roi_pct": float(np.mean(agg["per_symbol_roi_pcts"])),
            "sum_cum_log_return_across_symbols": agg["cum_log_return_total"],
        })

    payload = {
        "experiment": "c9_km_era_decomposition",
        "feature_cell": {
            "channel_n": 120, "atr_n": 14, "h_dwell": 5,
            "trend_id": "a_ts_mom", "trend_id_lookback_l": 60,
            "trend_id_threshold": 1.0, "k_atr": k_atr,
        },
        "c9_config": {
            "km_grid": list(c9_cfg.km_grid), "km_start": c9_cfg.km_start,
            "risk_budget_pct": c9_cfg.risk_budget_pct,
        },
        "per_symbol_decomposition": per_symbol_decomposition,
        "cross_symbol_summary": cross_sym_summary,
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])

    print()
    print("=" * 110)
    print("H062 C9 km-ERA P/L DECOMPOSITION")
    print(f"  sidecar: {sidecar_path}")
    print(f"  sha256:  {sha}")
    print("=" * 110)
    print(f"{'symbol':<6} {'km':>5} {'n_sess':>8} {'era_ROI':>10} {'cum_log':>10} {'Sharpe_ann':>12} {'window'}")
    for d in per_symbol_decomposition:
        for era in d["per_km_era"]:
            wnd = f"{era['first_session_date'][:10]} -> {era['last_session_date'][:10]}"
            print(
                f"{d['symbol']:<6} {era['km']:>+4.2f} {era['n_sessions']:>8} "
                f"{era['era_roi_pct_on_unit_bankroll']:>+8.2f}% {era['cum_log_return']:>+9.3f} "
                f"{era['sharpe_annualized']:>+10.2f}  {wnd}"
            )
    print("-" * 110)
    print()
    print("CROSS-SYMBOL km-ERA SUMMARY:")
    print(f"{'km':>5} {'tot_session_days':>17} {'n_sym_active':>13} {'avg_per_sym_ROI':>16}")
    for s in cross_sym_summary:
        print(
            f"{s['km']:>+4.2f} {s['total_session_days_across_4_symbols']:>17} "
            f"{s['n_symbols_active_at_this_km']:>13} {s['avg_per_symbol_roi_pct']:>+14.2f}%"
        )
    print("=" * 110)
    return 0


if __name__ == "__main__":
    sys.exit(main())
