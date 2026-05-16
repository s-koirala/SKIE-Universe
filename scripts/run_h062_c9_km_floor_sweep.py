"""H062 C9 km_floor sweep — circuit-breaker vs edge trade-off.

Per docs/audits/audit_trail_2026-05-15_c9_2026_subwindow.md §8 rec 2:
test whether raising the C9 BOCD-halve floor from km=0.5 (current
default) to higher values (1.0, 1.5) keeps the strategy active during
the 2026 sub-window — trade-off: less de-risking on regime decay vs
more upside capture.

Three km_grid variants:
  G_default: (0.5, 1.0, 1.5, 2.0, 2.5)  km_floor=0.5
  G_floor1:  (1.0, 1.5, 2.0, 2.5)       km_floor=1.0
  G_floor1_5: (1.5, 2.0, 2.5)            km_floor=1.5

For each variant: run full 2020-2025 + 2026-04-01->2026-05-15 sub-window
per 4 symbols. Report basket-aggregate Pareto across variants.
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
_log = logging.getLogger("c9_km_floor")

_STARTING = 10_000.0


def main() -> int:
    sub_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    out_dir = (
        _REPO_ROOT / "artifacts" / "runs" / "H062"
        / f"c9_km_floor_sweep_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    start = pd.Timestamp("2020-01-01", tz="UTC")
    end_per_sym = {
        "ES": pd.Timestamp("2026-05-15", tz="UTC"),
        "NQ": pd.Timestamp("2026-05-15", tz="UTC"),
        "MGC": pd.Timestamp("2026-05-15", tz="UTC"),
        "SIL": pd.Timestamp("2026-05-15", tz="UTC"),
    }
    subwin_start = pd.Timestamp("2026-04-01", tz="UTC")

    feat_cfg = H062FeatureConfig(
        channel_n=120, atr_n=14, h_dwell=5,
        trend_id="a_ts_mom", trend_id_lookback_l=60, trend_id_threshold=1.0,
    )
    k_atr = 2.0

    floor_variants = {
        "default_floor_0.5": (0.5, 1.0, 1.5, 2.0, 2.5),
        "floor_1.0": (1.0, 1.5, 2.0, 2.5),
        "floor_1.5": (1.5, 2.0, 2.5),
    }

    all_results: list[dict[str, Any]] = []
    for variant_name, km_grid in floor_variants.items():
        _log.info("--- variant %s (km_grid=%s; km_start=1.5) ---", variant_name, km_grid)
        # km_start = 1.5 in all variants; clamp if not in grid
        km_start = 1.5 if 1.5 in km_grid else km_grid[0]
        c9_cfg = C9Config(
            km_grid=km_grid, km_start=km_start,
            risk_budget_pct=0.01,
            step_check_interval_sessions=60,
            bocd_hazard_rate=0.01, bocd_window=60, bocd_threshold=0.5,
        )
        for sym in ["ES", "NQ", "MGC", "SIL"]:
            try:
                df5 = _load_5min_bars(sub_root, sym, start=start, end=end_per_sym[sym])
            except Exception as e:  # noqa: BLE001
                _log.warning("  %s: load failed: %s", sym, e)
                continue
            try:
                sim = _run_c9_simulation(
                    symbol=sym, df_5m=df5, feature_config=feat_cfg,
                    k_atr=k_atr, c9_cfg=c9_cfg, starting_equity=_STARTING,
                )
            except Exception as e:  # noqa: BLE001
                _log.warning("  %s: sim failed: %s", sym, e)
                continue
            # Sub-window stats from per_session_log_returns
            psl = sim["per_session_log_returns"]
            sub_items = []
            for k, v in psl.items():
                try:
                    d = pd.Timestamp(str(k), tz="UTC")
                except (ValueError, TypeError):
                    continue
                if d >= subwin_start:
                    sub_items.append((str(k), float(v)))
            sub_items.sort(key=lambda x: x[0])
            sub_lr = np.array([v for _, v in sub_items], dtype=float)
            sub_eq = _STARTING * float(np.prod(np.exp(sub_lr))) if sub_lr.size else _STARTING
            sub_roi = (sub_eq / _STARTING - 1.0) * 100

            all_results.append({
                "variant": variant_name,
                "symbol": sym,
                "full_roi_pct": sim["realized_roi_pct"],
                "full_max_dd_pct": sim["realized_max_dd_pct"],
                "full_n_trades": sim["n_trades"],
                "full_wins": sim["wins"], "full_losses": sim["losses"],
                "full_r_mean": sim["r_multiple_mean"],
                "subwin_n_sessions": int(sub_lr.size),
                "subwin_roi_pct": sub_roi,
                "km_terminal": sim["km_terminal"],
                "n_km_step_ups": sim["n_km_step_ups"],
                "n_km_halves": sim["n_km_halves"],
            })
            _log.info(
                "  %s: full ROI=%.1f%% DD=%.1f%% trades=%d  subwin ROI=%.1f%% n_sess=%d  km_term=%.2f halves=%d",
                sym, sim["realized_roi_pct"], sim["realized_max_dd_pct"], sim["n_trades"],
                sub_roi, sub_lr.size, sim["km_terminal"], sim["n_km_halves"],
            )

    # Basket-aggregate per variant
    variant_basket: dict[str, dict[str, float]] = {}
    for v in floor_variants.keys():
        rows = [r for r in all_results if r["variant"] == v]
        if not rows: continue
        full_basket_end = sum(
            _STARTING * (1 + r["full_roi_pct"]/100) for r in rows
        )
        basket_start = _STARTING * len(rows)
        subwin_basket_end = sum(
            _STARTING * (1 + r["subwin_roi_pct"]/100) for r in rows
        )
        variant_basket[v] = {
            "n_symbols": len(rows),
            "full_basket_roi_pct": (full_basket_end / basket_start - 1) * 100,
            "subwin_basket_roi_pct": (subwin_basket_end / basket_start - 1) * 100,
            "avg_max_dd_pct": float(np.mean([r["full_max_dd_pct"] for r in rows])),
            "total_full_trades": sum(r["full_n_trades"] for r in rows),
            "total_subwin_sessions": sum(r["subwin_n_sessions"] for r in rows),
        }

    payload = {
        "experiment": "c9_km_floor_sweep",
        "feature_cell": {
            "channel_n": 120, "atr_n": 14, "h_dwell": 5,
            "trend_id": "a_ts_mom", "trend_id_lookback_l": 60,
            "trend_id_threshold": 1.0, "k_atr": k_atr,
        },
        "km_floor_variants": {n: list(g) for n, g in floor_variants.items()},
        "subwin_start": str(subwin_start),
        "results": all_results,
        "variant_basket_summary": variant_basket,
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
    print("H062 C9 KM-FLOOR SWEEP -- 2020-2025 full OOS + 2026-04-01 to 2026-05-15 sub-window")
    print(f"  sidecar: {sidecar_path}")
    print(f"  sha256:  {sha}")
    print("=" * 110)
    print(f"{'variant':<22} {'full_basket_roi':>17} {'subwin_basket_roi':>19} {'avg_MaxDD':>12} {'total_trades':>14}")
    for v, b in variant_basket.items():
        print(
            f"{v:<22} {b['full_basket_roi_pct']:>+15.1f}% {b['subwin_basket_roi_pct']:>+17.2f}% "
            f"{b['avg_max_dd_pct']:>+10.1f}% {b['total_full_trades']:>14}"
        )
    print()
    print("PER-SYMBOL DETAIL:")
    print(f"{'variant':<22} {'sym':<5} {'full_roi':>10} {'full_DD':>9} {'trades':>8} {'subwin_roi':>12} {'sub_sess':>9} {'km_term':>9} {'halves':>8}")
    for r in all_results:
        print(
            f"{r['variant']:<22} {r['symbol']:<5} {r['full_roi_pct']:>+8.1f}% "
            f"{r['full_max_dd_pct']:>+7.1f}% {r['full_n_trades']:>8} "
            f"{r['subwin_roi_pct']:>+10.2f}% {r['subwin_n_sessions']:>9} "
            f"{r['km_terminal']:>+8.2f} {r['n_km_halves']:>8}"
        )
    print("=" * 110)
    return 0


if __name__ == "__main__":
    sys.exit(main())
