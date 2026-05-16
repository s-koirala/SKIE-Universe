"""H062 C9 BOCD-step-up on 2026-04-01 → 2026-05-15 OOS sub-window.

Per audit_trail_2026-05-15_h065_sil_standalone_v2.md §7 recommendation:
test whether the C9 +217.7% basket result (full 2020-2025 OOS;
artifacts/runs/H062/c9_bocd_step_up_20260516T013136Z/) holds on the
fresh 2026-04-01 → 2026-05-15 sub-window.

Methodology: load 2024-01-01 → 2026-05-15 per symbol (sufficient warm-up
for BOCD state machine + dense per-session MPPM path); run C9 simulator
from 2024 start; filter per-trade ledger to 2026-04-01 → 2026-05-15.

Comparison anchor: C3 super-Kelly on same sub-window produced -6.1%
basket per artifacts/runs/H062/c3_2026_q1q2_20260516T001902Z/. C9's
BOCD-driven de-risking SHOULD outperform on a decay regime — testable.
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

# Import C9 state machine from the production C9 script
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

from skie_ninja.features.h062 import H062FeatureConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h062_c9_2026")

_STARTING_EQUITY_PER_SYMBOL = 10_000.0


def main() -> int:
    sub_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    out_dir = (
        _REPO_ROOT / "artifacts" / "runs" / "H062"
        / f"c9_2026_q1q2_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Window: warm-up from 2024-01-01 (gives C9 BOCD ~500 sessions to converge)
    # then filter results to 2026-04-01 → 2026-05-15 sub-window
    warmup_start = pd.Timestamp("2024-01-01", tz="UTC")
    subwin_start = pd.Timestamp("2026-04-01", tz="UTC")
    subwin_end_per_sym = {
        "ES": pd.Timestamp("2025-12-03", tz="UTC"),  # ES substrate ends; effectively no 2026
        "NQ": pd.Timestamp("2024-12-19", tz="UTC"),  # NQ ends 2024-12; will have 2026-H1 from re-ingest
        "MGC": pd.Timestamp("2026-05-15", tz="UTC"),
        "SIL": pd.Timestamp("2026-05-15", tz="UTC"),
    }
    # ES + NQ have 2026-H1 data per the Phase O.3 extraction; right edges are:
    rerunpath_ends = {
        "ES": pd.Timestamp("2026-05-15", tz="UTC"),
        "NQ": pd.Timestamp("2026-05-15", tz="UTC"),
        "MGC": pd.Timestamp("2026-05-15", tz="UTC"),
        "SIL": pd.Timestamp("2026-05-15", tz="UTC"),
    }

    # Feature cell — v1 production representative
    feat_cfg = H062FeatureConfig(
        channel_n=120, atr_n=14, h_dwell=5,
        trend_id="a_ts_mom", trend_id_lookback_l=60, trend_id_threshold=1.0,
    )
    k_atr = 2.0
    c9_cfg = C9Config(
        km_grid=(0.5, 1.0, 1.5, 2.0, 2.5),
        km_start=1.5,
        risk_budget_pct=0.01,
        step_check_interval_sessions=60,
        bocd_hazard_rate=0.01,
        bocd_window=60,
        bocd_threshold=0.5,
    )

    results: list[dict[str, Any]] = []
    for sym in ["ES", "NQ", "MGC", "SIL"]:
        sym_end = rerunpath_ends.get(sym, pd.Timestamp("2026-05-15", tz="UTC"))
        _log.info("Loading %s [%s → %s]...", sym, warmup_start.date(), sym_end.date())
        try:
            df5 = _load_5min_bars(sub_root, sym, start=warmup_start, end=sym_end)
            n_total = len(df5)
            _log.info("  %s: %d 5-min bars (%d sessions warm-up + sub-window)",
                      sym, n_total, df5["session_date_et"].nunique())
        except RuntimeError as exc:
            _log.warning("  %s: load failed: %s; skip", sym, exc)
            continue

        # Run C9 on combined warm-up + sub-window
        try:
            sim = _run_c9_simulation(
                symbol=sym, df_5m=df5, feature_config=feat_cfg,
                k_atr=k_atr, c9_cfg=c9_cfg,
                starting_equity=_STARTING_EQUITY_PER_SYMBOL,
            )
        except Exception as exc:  # noqa: BLE001
            _log.warning("  %s: simulation failed: %s; skip", sym, exc)
            continue

        # Filter per-session log returns to 2026-04-01 → 2026-05-15
        per_sess_lr_full = sim["per_session_log_returns"]
        subwin_lr_items = []
        for sess_date_str, lr in per_sess_lr_full.items():
            try:
                sess_date = pd.Timestamp(str(sess_date_str), tz="UTC")
            except (ValueError, TypeError):
                continue
            if sess_date >= subwin_start and sess_date <= sym_end:
                subwin_lr_items.append((str(sess_date_str), float(lr)))
        subwin_lr_items.sort(key=lambda x: x[0])
        subwin_lr = np.array([v for _, v in subwin_lr_items], dtype=float)

        # Compute sub-window equity curve
        sub_eq = [_STARTING_EQUITY_PER_SYMBOL]
        for lr in subwin_lr:
            sub_eq.append(sub_eq[-1] * float(np.exp(lr)))
        sub_eqa = np.array(sub_eq)
        if sub_eqa.size > 1:
            running_max = np.maximum.accumulate(sub_eqa)
            dd = (sub_eqa - running_max) / running_max
            sub_maxdd = float(-dd.min())
        else:
            sub_maxdd = 0.0
        sub_end = float(sub_eqa[-1])
        sub_roi = (sub_end / _STARTING_EQUITY_PER_SYMBOL - 1.0) * 100

        # Step history during sub-window
        sub_step_hist = [
            h for h in sim["km_step_history"]
            if h.get("session_date") and pd.Timestamp(str(h["session_date"]), tz="UTC") >= subwin_start
        ]

        results.append({
            "symbol": sym,
            "n_sessions_subwin": len(subwin_lr),
            "subwin_end_equity": sub_end,
            "subwin_roi_pct": sub_roi,
            "subwin_max_dd_pct": sub_maxdd * 100,
            "km_terminal": sim["km_terminal"],
            "n_km_steps_in_subwin": len(sub_step_hist),
            "n_km_step_ups_total": sim["n_km_step_ups"],
            "n_km_halves_total": sim["n_km_halves"],
            "full_window_roi_pct": sim["realized_roi_pct"],
            "full_window_max_dd_pct": sim["realized_max_dd_pct"],
            "full_window_n_trades": sim["n_trades"],
        })
        _log.info(
            "  %s: subwin ROI=%.1f%% MaxDD=%.1f%% n_sess=%d  km_terminal=%.2f  full_window ROI=%.1f%% trades=%d",
            sym, sub_roi, sub_maxdd*100, len(subwin_lr),
            sim["km_terminal"], sim["realized_roi_pct"], sim["n_trades"],
        )

    if not results:
        _log.error("No results produced; aborting")
        return 1

    basket_subwin_end = sum(r["subwin_end_equity"] for r in results)
    basket_start = _STARTING_EQUITY_PER_SYMBOL * len(results)
    basket_subwin_roi = (basket_subwin_end / basket_start - 1.0) * 100

    payload = {
        "experiment": "c9_bocd_step_up_2026_q1q2_subwindow",
        "warm_up_start": str(warmup_start),
        "subwin_start": str(subwin_start),
        "subwin_end_per_symbol": {s: str(d) for s, d in rerunpath_ends.items()},
        "feature_cell": {
            "channel_n": 120, "atr_n": 14, "h_dwell": 5,
            "trend_id": "a_ts_mom", "trend_id_lookback_l": 60,
            "trend_id_threshold": 1.0, "k_atr": k_atr,
        },
        "c9_config": {
            "km_grid": list(c9_cfg.km_grid), "km_start": c9_cfg.km_start,
            "risk_budget_pct": c9_cfg.risk_budget_pct,
            "step_check_interval_sessions": c9_cfg.step_check_interval_sessions,
            "bocd_hazard_rate": c9_cfg.bocd_hazard_rate,
            "bocd_window": c9_cfg.bocd_window,
            "bocd_threshold": c9_cfg.bocd_threshold,
        },
        "per_symbol": results,
        "basket": {
            "starting_equity_total": basket_start,
            "end_equity_subwin": basket_subwin_end,
            "subwin_roi_pct": basket_subwin_roi,
        },
        "comparison_anchor_c3_2026_q1q2": -6.1,  # basket ROI from c3_2026_q1q2 run
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])

    print()
    print("=" * 100)
    print("H062 C9 BOCD-STEP-UP -- 2026-04-01 -> 2026-05-15 SUB-WINDOW")
    print(f"  warm-up: {warmup_start.date()} -> {subwin_start.date()} (initialize BOCD state machine)")
    print(f"  sub-window: {subwin_start.date()} -> 2026-05-15 (~30 sessions per symbol)")
    print(f"  sidecar:  {sidecar_path}")
    print(f"  sha256:   {sha}")
    print("=" * 100)
    print(f"{'symbol':<6} {'subwin_roi':>12} {'subwin_DD':>12} {'n_sess':>8} {'km_term':>9} {'full_roi':>12} {'full_DD':>10} {'n_trades':>10}")
    for r in results:
        print(
            f"{r['symbol']:<6} {r['subwin_roi_pct']:>+10.2f}% {r['subwin_max_dd_pct']:>+10.2f}% "
            f"{r['n_sessions_subwin']:>8} {r['km_terminal']:>+8.2f} "
            f"{r['full_window_roi_pct']:>+10.1f}% {r['full_window_max_dd_pct']:>+8.1f}% "
            f"{r['full_window_n_trades']:>10}"
        )
    print("-" * 100)
    print(f"BASKET subwin: ${basket_subwin_end:,.2f} ({basket_subwin_roi:+.2f}%)  "
          f"vs C3 subwin -6.1%  vs passive +11.8%")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
