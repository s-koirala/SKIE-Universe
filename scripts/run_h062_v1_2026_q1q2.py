"""H062 v1 baseline on 2026-04-01 → 2026-05-15 OOS sub-window.

Scope: SUB-WINDOW DIAGNOSTIC. NOT a full KPI report card. ADR-0017 §3
primary metric vector + ADR-0018 D-1 MPPM(ρ=1) explicitly descoped
per N~21 sessions / N=37 trades below the Politis-White 2004 minimum-
block-length threshold for stationary-bootstrap CI; sidecar marks
`kpi_report_card: false`, `scope: subwindow_diagnostic`.

H062 v1 baseline = quarter-Kelly (km=0.25) channel-N=120 breakout. This
fills the gap surfaced by the user 2026-05-16 request "test all untested
hypotheses on 2026 data" — H062 v1 walk-forward was never extended past
2025-12-30 per its frozen pre-reg.

Methodology: warm-up from 2024-01-01 to populate ATR/Donchian state;
re-uses _run_per_trade_simulation primitive from scripts/run_h062_walk_
forward.py (frozen pre-reg implementation); filter per-trade ledger +
per-session log returns to 2026-04-01 → 2026-05-15. Output parallel to
run_h062_c9_2026_q1q2.py.

All 4 universe symbols ({ES, NQ, MGC, SIL}) emit a results row even when
the simulator returns an empty per-session series — explicit
`gated_out_reason` in those rows per R1 audit F-1-5.
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
    "wf", str(_REPO_ROOT / "scripts" / "run_h062_walk_forward.py"),
)
wf_mod = importlib.util.module_from_spec(spec)
sys.modules["wf"] = wf_mod
spec.loader.exec_module(wf_mod)
_load_5min_bars = wf_mod._load_5min_bars
_run_per_trade_simulation = wf_mod._run_per_trade_simulation

from skie_ninja.features.h062 import H062FeatureConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h062_v1_2026")

_STARTING_EQUITY_PER_SYMBOL = 10_000.0
_RNG_SEED = 20260516


def _git_head() -> str:
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _script_sha256(script_path: Path) -> str:
    import hashlib as _h
    return _h.sha256(script_path.read_bytes()).hexdigest()


def _substrate_sha() -> tuple[str, str]:
    p = _REPO_ROOT / "data" / "processed" / "_provenance" / "vendor_legacy_1min_roll_adjusted_20260516.json"
    if not p.exists():
        return "unknown", ""
    try:
        prov = json.loads(p.read_text(encoding="utf-8"))
        return str(prov.get("output_frame_sha256", "unknown")), str(p.relative_to(_REPO_ROOT))
    except Exception:  # noqa: BLE001
        return "unknown", str(p)


def main() -> int:
    sub_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    out_dir = (
        _REPO_ROOT / "artifacts" / "runs" / "H062"
        / f"v1_baseline_2026_q1q2_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    warmup_start = pd.Timestamp("2024-01-01", tz="UTC")
    subwin_start = pd.Timestamp("2026-04-01", tz="UTC")
    sym_ends = {
        "ES": pd.Timestamp("2026-06-30", tz="UTC"),
        "NQ": pd.Timestamp("2026-06-30", tz="UTC"),
        "MGC": pd.Timestamp("2026-06-30", tz="UTC"),
        "SIL": pd.Timestamp("2026-06-30", tz="UTC"),
    }

    feat_cfg = H062FeatureConfig(
        channel_n=120, atr_n=14, h_dwell=5,
        trend_id="a_ts_mom", trend_id_lookback_l=60, trend_id_threshold=1.0,
    )
    k_atr = 2.0
    kelly_multiplier = 0.25

    results: list[dict[str, Any]] = []
    for sym in ["ES", "NQ", "MGC", "SIL"]:
        sym_end = sym_ends[sym]
        _log.info("Loading %s [%s -> %s]...", sym, warmup_start.date(), sym_end.date())
        try:
            df5 = _load_5min_bars(sub_root, sym, start=warmup_start, end=sym_end)
        except RuntimeError as exc:
            _log.warning("  %s: load failed: %s; emit zero-row with reason", sym, exc)
            results.append({
                "symbol": sym, "n_sessions_subwin": 0, "subwin_end_equity": _STARTING_EQUITY_PER_SYMBOL,
                "subwin_roi_pct": 0.0, "subwin_max_dd_pct": 0.0,
                "subwin_n_trades": 0, "subwin_wins": 0, "subwin_losses": 0, "subwin_zeros": 0,
                "full_window_roi_pct": 0.0, "full_window_max_dd_pct": 0.0, "full_window_n_trades": 0,
                "gated_out_reason": f"data_load_failed: {exc}",
            })
            continue
        n_total = len(df5)
        _log.info("  %s: %d 5-min bars (%d sessions)", sym, n_total, df5["session_date_et"].nunique())

        try:
            sim = _run_per_trade_simulation(
                symbol=sym, df_5m=df5, feature_config=feat_cfg,
                k_atr=k_atr, kelly_multiplier=kelly_multiplier,
                risk_budget_pct=0.01,
            )
        except Exception as exc:  # noqa: BLE001
            _log.warning("  %s: simulation failed: %s; emit zero-row with reason", sym, exc)
            results.append({
                "symbol": sym, "n_sessions_subwin": 0, "subwin_end_equity": _STARTING_EQUITY_PER_SYMBOL,
                "subwin_roi_pct": 0.0, "subwin_max_dd_pct": 0.0,
                "subwin_n_trades": 0, "subwin_wins": 0, "subwin_losses": 0, "subwin_zeros": 0,
                "full_window_roi_pct": 0.0, "full_window_max_dd_pct": 0.0, "full_window_n_trades": 0,
                "gated_out_reason": f"simulation_failed: {exc}",
            })
            continue

        per_sess_lr_arr = sim.get("per_session_logret", None)
        per_sess_dates = sim.get("per_session_dates", [])
        if per_sess_lr_arr is None or len(per_sess_dates) == 0:
            _log.warning("  %s: empty per-session series; emit zero-row with reason", sym)
            results.append({
                "symbol": sym, "n_sessions_subwin": 0, "subwin_end_equity": _STARTING_EQUITY_PER_SYMBOL,
                "subwin_roi_pct": 0.0, "subwin_max_dd_pct": 0.0,
                "subwin_n_trades": 0, "subwin_wins": 0, "subwin_losses": 0, "subwin_zeros": 0,
                "full_window_roi_pct": 0.0, "full_window_max_dd_pct": 0.0, "full_window_n_trades": int(sim.get("n_trades", 0)),
                "gated_out_reason": "no_eligible_breakouts_full_window_or_kelly_size_floored",
            })
            continue

        subwin_items = []
        for sd, lr in zip(per_sess_dates, per_sess_lr_arr):
            try:
                sd_str = str(sd)
                sess_ts = pd.Timestamp(sd_str, tz="UTC") if "+" not in sd_str else pd.Timestamp(sd_str)
            except (ValueError, TypeError):
                continue
            if sess_ts >= subwin_start and sess_ts <= sym_end:
                subwin_items.append((sd_str, float(lr)))
        subwin_items.sort(key=lambda x: x[0])
        subwin_lr = np.array([v for _, v in subwin_items], dtype=float)

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

        # Count sub-window trades
        r_mults = sim.get("r_multiples", np.array([]))
        trade_sess_dates = sim.get("trade_session_dates", [])
        n_trades_full = int(sim.get("n_trades", len(r_mults)))
        n_trades_sub = 0
        sub_wins, sub_losses, sub_zeros = 0, 0, 0
        for i, sd in enumerate(trade_sess_dates):
            try:
                sd_str = str(sd)
                sd_ts = pd.Timestamp(sd_str, tz="UTC") if "+" not in sd_str else pd.Timestamp(sd_str)
            except (ValueError, TypeError):
                continue
            if sd_ts >= subwin_start and sd_ts <= sym_end:
                n_trades_sub += 1
                if i < len(r_mults):
                    r = float(r_mults[i])
                    if r > 0:
                        sub_wins += 1
                    elif r < 0:
                        sub_losses += 1
                    else:
                        sub_zeros += 1

        # Full-window ROI from full per-session series
        full_eq = [_STARTING_EQUITY_PER_SYMBOL]
        for lr in per_sess_lr_arr:
            full_eq.append(full_eq[-1] * float(np.exp(lr)))
        full_eqa = np.array(full_eq)
        if full_eqa.size > 1:
            rmax_full = np.maximum.accumulate(full_eqa)
            full_dd = float(-((full_eqa - rmax_full) / rmax_full).min())
        else:
            full_dd = 0.0
        full_roi = (float(full_eqa[-1]) / _STARTING_EQUITY_PER_SYMBOL - 1.0) * 100

        results.append({
            "symbol": sym,
            "n_sessions_subwin": len(subwin_lr),
            "subwin_end_equity": sub_end,
            "subwin_roi_pct": sub_roi,
            "subwin_max_dd_pct": sub_maxdd * 100,
            "subwin_n_trades": n_trades_sub,
            "subwin_wins": sub_wins,
            "subwin_losses": sub_losses,
            "subwin_zeros": sub_zeros,
            "full_window_roi_pct": full_roi,
            "full_window_max_dd_pct": full_dd * 100,
            "full_window_n_trades": n_trades_full,
            "gated_out_reason": None if n_trades_sub > 0 else "no_subwin_trades_full_window_present",
        })
        _log.info(
            "  %s: subwin ROI=%.2f%% MaxDD=%.2f%% n_sess=%d n_trades=%d W/L/Z=%d/%d/%d",
            sym, sub_roi, sub_maxdd*100, len(subwin_lr),
            n_trades_sub, sub_wins, sub_losses, sub_zeros,
        )

    if not results:
        _log.error("No results produced; aborting")
        return 1

    basket_subwin_end = sum(r["subwin_end_equity"] for r in results)
    # justify per R1 audit F-1-5: basket always denominated against full 4-symbol universe
    basket_start = _STARTING_EQUITY_PER_SYMBOL * 4
    basket_subwin_roi = (basket_subwin_end / basket_start - 1.0) * 100

    sub_sha, prov_path = _substrate_sha()
    script_path = Path(__file__).resolve()
    payload = {
        "experiment": "h062_v1_baseline_2026_q1q2_subwindow",
        "kpi_report_card": False,
        "scope": "subwindow_diagnostic",
        "descoped_kpis": {
            "reason": "sub-window N~21 sessions / ~37 trades below Politis-White 2004 minimum-block-length threshold for stationary-bootstrap CI",
            "authorized_by": "operator 2026-05-16",
            "refs": ["ADR-0013", "ADR-0017", "ADR-0018"],
            "missing": ["mppm_rho1_ci", "calmar_differential_ci", "profit_factor_ci",
                        "r_multiple_mean_ci", "terminal_wealth_q05", "probability_of_ruin",
                        "l_skewness_tau3", "forward_projection_252_session"],
        },
        "warm_up_start": str(warmup_start),
        "subwin_start": str(subwin_start),
        "subwin_end_per_symbol": {s: str(d) for s, d in sym_ends.items()},
        "feature_cell": {
            "channel_n": 120, "atr_n": 14, "h_dwell": 5,
            "trend_id": "a_ts_mom", "trend_id_lookback_l": 60,
            "trend_id_threshold": 1.0, "k_atr": k_atr,
            "kelly_multiplier": kelly_multiplier,
        },
        "provenance": {
            "git_head": _git_head(),
            "substrate_dataset_checksum": sub_sha,
            "substrate_provenance_path": prov_path,
            "producing_script_path": str(script_path.relative_to(_REPO_ROOT)),
            "producing_script_sha256": _script_sha256(script_path),
            "rng_seed": _RNG_SEED,
            "uses_production_primitive": "scripts/run_h062_walk_forward.py:_run_per_trade_simulation",
        },
        "per_symbol": results,
        "basket": {
            "starting_equity_total": basket_start,
            "end_equity_subwin": basket_subwin_end,
            "subwin_roi_pct": basket_subwin_roi,
            "n_symbols_active": len([r for r in results if r["n_sessions_subwin"] > 0]),
            "n_symbols_universe": 4,
        },
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }

    sb = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path = out_dir / "sidecar.json"
    sidecar_path.write_bytes(sb)
    sha = hashlib.sha256(sb).hexdigest()
    (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])

    print()
    print("=" * 80)
    print("H062 v1 BASELINE 2026-Q1-Q2 SUB-WINDOW (km=0.25 quarter-Kelly)")
    print("=" * 80)
    n_active = len([r for r in results if r["n_sessions_subwin"] > 0])
    print(f"basket(4 symbols): starting=${basket_start:,.0f} end=${basket_subwin_end:,.0f} ROI={basket_subwin_roi:+.2f}%  active_symbols={n_active}/4")
    print()
    print(f"{'sym':<5} {'n_sess':<7} {'sub_roi%':<10} {'sub_DD%':<8} {'n_trades':<9} {'W/L/Z':<11} {'full_ROI%':<10} {'full_DD%':<8} {'reason':<40}")
    for r in results:
        wlz = f"{r['subwin_wins']}/{r['subwin_losses']}/{r['subwin_zeros']}"
        reason = (r.get("gated_out_reason") or "")[:40]
        print(f"{r['symbol']:<5} {r['n_sessions_subwin']:<7} {r['subwin_roi_pct']:<+9.2f}% {r['subwin_max_dd_pct']:<7.2f}% {r['subwin_n_trades']:<9} {wlz:<11} {r['full_window_roi_pct']:<+9.2f}% {r['full_window_max_dd_pct']:<7.2f}% {reason:<40}")
    print("=" * 80)
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
