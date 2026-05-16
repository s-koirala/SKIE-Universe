"""Surface 2026 sub-window per (cfg, symbol) from existing sidecars.

Reads the most recent sweep sidecars for H055 v2, H065 TP-overlay,
SIL-standalone, and C9 km_floor; emits a compact per-cfg per-symbol
table. No re-computation; pure tabulation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _read_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _h055_v2_table() -> None:
    p = REPO / "artifacts/runs/H055/v2_sweep_20260516T025924Z/sweep_sidecar.json"
    if not p.exists():
        print(f"[skip] H055 v2: {p} missing")
        return
    sc = _read_json(p)
    res = sc.get("results", [])
    print("\n" + "=" * 120)
    print("H055 v2 wick-rejection sweep — 2026-04-01 to 2026-05-15 sub-window per (cfg, symbol)")
    print("=" * 120)
    cols = ("cfg", "sym", "n_full", "roi_full%", "maxDD%", "n_sub", "sub_roi%", "sub_DD%", "sub_w/l/z", "sub_end_eq")
    fmt = "{:<8} {:<5} {:<7} {:>10} {:>9} {:<6} {:>9} {:>8} {:<14} {:>11}"
    print(fmt.format(*cols))
    print("-" * 120)
    for r in res:
        sw = r.get("sub_window") or {}
        wlz = f"{sw.get('sub_wins', 0)}/{sw.get('sub_losses', 0)}/{sw.get('sub_zeros', 0)}"
        roi_full = r.get("realized_roi_pct", 0.0)
        dd_full = r.get("realized_max_dd_pct", 0.0)
        end_eq = sw.get("sub_end_eq", 0.0) or 0.0
        print(fmt.format(
            r.get("cfg_name", ""),
            r.get("symbol", ""),
            r.get("n_trades", 0),
            f"{roi_full:+.2f}",
            f"{dd_full:.2f}",
            sw.get("n_trades_sub", 0),
            f"{sw.get('sub_roi_pct', 0.0):+.2f}",
            f"{sw.get('sub_max_dd_pct', 0.0):.2f}",
            wlz,
            f"${end_eq:,.0f}",
        ))


def _h065_tp_table() -> None:
    p = REPO / "artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/sweep_sidecar.json"
    if not p.exists():
        print(f"[skip] H065: {p} missing")
        return
    sc = _read_json(p)
    res = sc.get("per_symbol_results", [])
    print("\n" + "=" * 120)
    print("H065 TP-overlay sweep — 2026-04-01 to 2026-05-15 sub-window per (cfg, symbol)")
    print("=" * 120)
    cols = ("cfg", "sym", "M", "km", "n_full", "roi_full%", "maxDD%", "n_sub", "sub_roi%", "sub_DD%", "sub_w/l/z")
    fmt = "{:<10} {:<5} {:>5} {:>5} {:>7} {:>10} {:>9} {:<6} {:>9} {:>8} {:<14}"
    print(fmt.format(*cols))
    print("-" * 120)
    for r in res:
        wlz = f"{r.get('subwindow_wins', 0)}/{r.get('subwindow_losses', 0)}/{r.get('subwindow_zeros', 0)}"
        print(fmt.format(
            r.get("cfg_name", "")[:10],
            r.get("symbol", ""),
            f"{r.get('tp_multiplier_M', 0.0)}",
            f"{r.get('kelly_multiplier', 0.0)}",
            r.get("n_trades", 0),
            f"{r.get('realized_roi_pct', 0.0):+.2f}",
            f"{r.get('realized_max_dd_pct', 0.0):.2f}",
            r.get("subwindow_n_trades", 0),
            f"{r.get('subwindow_realized_roi_pct', 0.0):+.2f}",
            f"{r.get('subwindow_realized_max_dd_pct', 0.0):.2f}",
            wlz,
        ))


def _sil_standalone_table() -> None:
    candidates = sorted((REPO / "artifacts/runs/H065").glob("sil_standalone_v2_*/sweep_sidecar.json"))
    if not candidates:
        print("[skip] SIL-standalone: no sidecar")
        return
    p = candidates[-1]
    sc = _read_json(p)
    print("\n" + "=" * 120)
    print(f"SIL-standalone investigation — {p.parent.name}")
    print("=" * 120)
    res = sc.get("per_cell_results", sc.get("results", []))
    if not res:
        print("[skip] SIL: no per-cell results in sidecar")
        return
    top_keys = sorted(res[0].keys())[:20]
    print("first-row keys (head 20):", top_keys)
    print(f"n cells: {len(res)}")
    cols = ("idx", "cfg", "n_full", "roi_full%", "maxDD%", "n_sub", "sub_roi%", "sub_DD%")
    fmt = "{:<5} {:<32} {:>7} {:>10} {:>9} {:>6} {:>9} {:>8}"
    print(fmt.format(*cols))
    print("-" * 120)
    for i, r in enumerate(res[:10]):
        cfg = r.get("cfg_name", r.get("cfg", ""))
        sub = r.get("sub_window") or {}
        print(fmt.format(
            i,
            str(cfg)[:32],
            r.get("n_trades", 0),
            f"{r.get('realized_roi_pct', 0.0):+.2f}",
            f"{r.get('realized_max_dd_pct', 0.0):.2f}",
            sub.get("n_trades_sub", r.get("subwindow_n_trades", 0)),
            f"{sub.get('sub_roi_pct', r.get('subwindow_realized_roi_pct', 0.0)):+.2f}",
            f"{sub.get('sub_max_dd_pct', r.get('subwindow_realized_max_dd_pct', 0.0)):.2f}",
        ))
    print(f"... ({len(res) - 10} more rows omitted)")
    def _safe_sub_roi(r: dict) -> float:
        # Defensive against None values in either dict layer (R1 audit F-1-8)
        sub = r.get("sub_window") or {}
        v = sub.get("sub_roi_pct")
        if v is None:
            v = r.get("subwindow_realized_roi_pct")
        return float(v) if v is not None else 0.0
    pos = [r for r in res if _safe_sub_roi(r) > 0]
    print(f"n cells with positive 2026 sub-window ROI: {len(pos)}")
    if pos:
        pos_sorted = sorted(pos, key=_safe_sub_roi, reverse=True)
        print("top 5 by sub-window ROI:")
        for r in pos_sorted[:5]:
            cfg = r.get("cfg_name", r.get("cfg", ""))
            roi = _safe_sub_roi(r)
            print(f"  {str(cfg)[:32]:<32} sub_roi={roi:+.2f}%")


def _c9_km_floor_table() -> None:
    candidates = sorted((REPO / "artifacts/runs/H062").glob("c9_km_floor*/sweep_sidecar.json"))
    if not candidates:
        candidates = sorted((REPO / "artifacts/runs/H062").glob("c9_km*/sweep_sidecar.json"))
    if not candidates:
        candidates = sorted((REPO / "artifacts/runs").rglob("*c9*km*/sweep_sidecar.json"))
    if not candidates:
        print("[skip] C9 km_floor: no sidecar")
        return
    p = candidates[-1]
    sc = _read_json(p)
    print("\n" + "=" * 120)
    print(f"C9 km_floor sweep — {p.parent.name}")
    print("=" * 120)
    print("keys:", list(sc.keys())[:20])
    res = sc.get("results", sc.get("per_cfg_results", []))
    if not res:
        print("[skip] no results array")
        return
    print(f"n cfgs: {len(res)}")
    sample_keys = sorted(res[0].keys())[:25]
    print("first-row keys:", sample_keys)


def main() -> int:
    print("=" * 120)
    print("TABULATING 2026-Q2 SUB-WINDOW RESULTS FROM EXISTING SIDECARS")
    print("=" * 120)
    _h055_v2_table()
    _h065_tp_table()
    _sil_standalone_table()
    _c9_km_floor_table()
    return 0


if __name__ == "__main__":
    sys.exit(main())
