"""H062 C3 super-Kelly simulation on the 2026-Q1-Q2 OOS-only window.

Per operator 2026-05-15 directive: "how would C3 have performed the last
month and a half (april/may 2026)?" — the fresh Databento extraction
[scripts/databento_extract_2026_h1.py](databento_extract_2026_h1.py)
landed 2026-01-01 → 2026-05-15 across ES + NQ + MGC + SIL at $4.61 USD.

This script applies the C3 super-Kelly configuration from
[scripts/run_h062_aggressive_sizing_sweep.py](run_h062_aggressive_sizing_sweep.py)
(SweepConfig C3: km=2.0, 1% risk, current-equity rebase, no pyramid)
to the fresh OOS window only.

Window: 2026-04-01 → 2026-05-15 (~6 weeks; the "last month and a half"
the operator asked about).

Output: comparison sidecar at
``artifacts/runs/H062/c3_2026_q1q2_<ts>/sidecar.json`` + printed
per-symbol + basket-aggregate table.

PRE-COST research-only (per ADR-0023 v1 operator directive).

Caveat: a 6-week OOS window is a SHORT-SAMPLE point-estimate; cannot
be interpreted as repeatable. Per Lo 2002 / Bailey-Lopez de Prado 2014
DSR, single-sample 30-session Sharpe estimates are inferentially weak.
The result is operationally informative ("would I have made money in
April-May 2026?") but NOT statistically distinguishable from random.
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
import polars as pl

from skie_ninja.features.h062 import H062FeatureConfig

# Import the v2 simulator from the sweep script.
# Per Python 3.11 dataclass-module-resolution requirement, the module
# MUST be registered in sys.modules BEFORE exec_module runs so the
# @dataclass decorator can resolve type-hints via sys.modules[cls.__module__].
import importlib.util
spec = importlib.util.spec_from_file_location(
    "h062_sweep", str(_REPO_ROOT / "scripts" / "run_h062_aggressive_sizing_sweep.py")
)
_sweep_mod = importlib.util.module_from_spec(spec)
sys.modules["h062_sweep"] = _sweep_mod
spec.loader.exec_module(_sweep_mod)
SweepConfig = _sweep_mod.SweepConfig
_run_aggressive_simulation = _sweep_mod._run_aggressive_simulation
_load_5min_bars = _sweep_mod._load_5min_bars

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h062_c3_2026_q1q2")


C3 = SweepConfig(
    name="C3_superkelly",
    kelly_multiplier=2.0,
    risk_budget_pct=0.01,
    use_current_equity_rebase=True,
    enable_pyramiding=False,
    pyramid_max_units=1,
    pyramid_step_atr=0.0,
    description="C3: super-Kelly 2.0× + current-equity rebase",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H062 C3 on 2026-Q1-Q2")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--window-start", default="2026-04-01",
        help="OOS window start (default 2026-04-01 = 'last month and a half')",
    )
    parser.add_argument(
        "--window-end", default="2026-05-15",
        help="OOS window end (default 2026-05-15 = today)",
    )
    parser.add_argument(
        "--warm-up-start", default="2026-01-01",
        help="Warm-up window start (default 2026-01-01; allows channel + ATR to converge before the test slice)",
    )
    parser.add_argument(
        "--symbols", nargs="*", default=["ES", "NQ", "MGC", "SIL"],
    )
    args = parser.parse_args(argv)

    if args.substrate_path:
        substrate_root = Path(args.substrate_path).resolve()
    else:
        substrate_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"

    out_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else _REPO_ROOT / "artifacts" / "runs" / "H062"
            / f"c3_2026_q1q2_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    warm_start = pd.Timestamp(args.warm_up_start, tz="UTC")
    window_start = pd.Timestamp(args.window_start, tz="UTC")
    window_end = pd.Timestamp(args.window_end, tz="UTC")

    feat_cfg = H062FeatureConfig(
        channel_n=120,
        atr_n=14,
        h_dwell=5,
        trend_id="a_ts_mom",
        trend_id_lookback_l=60,
        trend_id_threshold=1.0,
    )
    k_atr = 2.0

    _log.info(
        "warm-up [%s -> %s); test [%s -> %s]",
        warm_start.date(), window_start.date(), window_start.date(), window_end.date(),
    )

    results = []
    for sym in args.symbols:
        _log.info("Loading %s...", sym)
        df_full = _load_5min_bars(substrate_root, sym, start=warm_start, end=window_end)
        n_total = len(df_full)
        _log.info("  %s: %d 5-min bars (%d sessions) over warm-up + test combined",
                  sym, n_total, df_full["session_date_et"].nunique())
        # Run on the combined warm-up + test slice; downstream sweep returns trade ledger
        # filterable by entry_session_date.
        sim = _run_aggressive_simulation(
            symbol=sym, df_5m=df_full, feature_config=feat_cfg, k_atr=k_atr,
            cfg=C3, starting_equity=10000.0,
        )
        # Filter trades to the test window only
        # The simulator doesn't expose trade list directly; we recompute by re-running
        # on just the test slice with same starting equity.
        # For the comparison, we report:
        # (a) full warm-up + test (above)
        # (b) test-only (below) — separate sim on test slice with $10k start
        df_test = df_full[df_full["ts_event"] >= window_start].reset_index(drop=True)
        if len(df_test) < 100:
            _log.warning("  %s: test slice too thin (%d bars); skip", sym, len(df_test))
            continue
        # Pass test slice with sufficient prior context: include last channel_n*2 bars
        # before window_start for proper channel + ATR initialization.
        warmup_bars = feat_cfg.channel_n + 100
        df_full_arr = df_full.reset_index(drop=True)
        test_first_idx = df_full_arr.index[df_full_arr["ts_event"] >= window_start].min()
        slice_start = max(0, test_first_idx - warmup_bars)
        df_test_with_warmup = df_full_arr.iloc[slice_start:].reset_index(drop=True)
        sim_test = _run_aggressive_simulation(
            symbol=sym, df_5m=df_test_with_warmup, feature_config=feat_cfg, k_atr=k_atr,
            cfg=C3, starting_equity=10000.0,
        )

        # Compute passive buy-and-hold over the test slice for benchmark
        df_test_clean = df_full[df_full["ts_event"] >= window_start].reset_index(drop=True)
        if len(df_test_clean) > 1:
            first_close = float(df_test_clean["close"].iloc[0])
            last_close = float(df_test_clean["close"].iloc[-1])
            passive_log_ret_total = float(np.log(last_close / first_close))
            passive_end_eq = 10000.0 * np.exp(passive_log_ret_total)
            passive_roi_pct = (passive_end_eq / 10000.0 - 1.0) * 100
        else:
            passive_end_eq = 10000.0
            passive_roi_pct = 0.0

        # Realized max-DD on the passive benchmark
        if len(df_test_clean) > 1:
            closes = df_test_clean["close"].to_numpy()
            log_rets = np.diff(np.log(closes))
            eq = 10000.0 * np.exp(np.cumsum(log_rets))
            eq_full = np.concatenate([[10000.0], eq])
            running_max = np.maximum.accumulate(eq_full)
            passive_dd = float(-((eq_full - running_max) / running_max).min())
        else:
            passive_dd = 0.0

        res = {
            "symbol": sym,
            "test_window_start": str(window_start),
            "test_window_end": str(window_end),
            "n_test_bars": len(df_test_clean),
            "n_test_sessions": int(df_test_clean["session_date_et"].nunique()),
            # ARM stats (test-only sim with warm-up bars for state init)
            "arm_end_equity": sim_test["realized_end_equity"],
            "arm_roi_pct": sim_test["realized_roi_pct"],
            "arm_max_dd_pct": sim_test["realized_max_dd_pct"],
            "arm_wins": sim_test["wins"],
            "arm_losses": sim_test["losses"],
            "arm_zeros": sim_test["zeros"],
            "arm_win_rate": sim_test["win_rate"],
            "arm_n_trades": sim_test["n_trades"],
            "arm_sr_ann": sim_test["sr_annualised_approx"],
            # PASSIVE benchmark
            "passive_end_equity": passive_end_eq,
            "passive_roi_pct": passive_roi_pct,
            "passive_max_dd_pct": passive_dd * 100,
            # Differential
            "arm_minus_passive_roi_pct": sim_test["realized_roi_pct"] - passive_roi_pct,
        }
        results.append(res)
        _log.info(
            "  %s: arm end=$%.0f (%+.1f%%) MaxDD=%.1f%% W/L/Z=%d/%d/%d  passive=$%.0f (%+.1f%%)",
            sym, res["arm_end_equity"], res["arm_roi_pct"], res["arm_max_dd_pct"],
            res["arm_wins"], res["arm_losses"], res["arm_zeros"],
            res["passive_end_equity"], res["passive_roi_pct"],
        )

    # Basket aggregate
    basket_arm = sum(r["arm_end_equity"] for r in results)
    basket_passive = sum(r["passive_end_equity"] for r in results)
    basket_start = 10000.0 * len(results)

    payload = {
        "hypothesis_id": "H062",
        "experiment": "c3_2026_q1q2_oos",
        "config": {
            "name": C3.name,
            "kelly_multiplier": C3.kelly_multiplier,
            "risk_budget_pct": C3.risk_budget_pct,
            "use_current_equity_rebase": C3.use_current_equity_rebase,
            "enable_pyramiding": C3.enable_pyramiding,
            "description": C3.description,
        },
        "feature_cell": {
            "channel_n": 120, "atr_n": 14, "h_dwell": 5,
            "trend_id": "a_ts_mom", "trend_id_lookback_l": 60,
            "trend_id_threshold": 1.0, "k_atr": k_atr,
        },
        "test_window": [str(window_start), str(window_end)],
        "warm_up_start": str(warm_start),
        "starting_equity_per_symbol": 10000.0,
        "per_symbol": results,
        "basket": {
            "arm_end_equity": basket_arm,
            "passive_end_equity": basket_passive,
            "starting": basket_start,
            "arm_roi_pct": (basket_arm / basket_start - 1.0) * 100,
            "passive_roi_pct": (basket_passive / basket_start - 1.0) * 100,
        },
        "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    sidecar_path = out_dir / "sidecar.json"
    sidecar_bytes = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.write_bytes(sidecar_bytes)
    sha = hashlib.sha256(sidecar_bytes).hexdigest()
    (out_dir / "sha256.txt").write_text(sha + "\n", encoding="utf-8")
    _log.info("sidecar=%s sha256=%s", sidecar_path, sha[:16])

    # Comparison print
    print()
    print("=" * 100)
    print(f"H062 C3 SUPER-KELLY — 2026 OOS WINDOW [{window_start.date()} -> {window_end.date()}]")
    print(f"sidecar: {sidecar_path}")
    print(f"sha256:  {sha}")
    print("=" * 100)
    print(f"{'symbol':<8} {'arm_end':>10} {'arm_roi':>10} {'arm_DD':>10} {'W/L/Z':>20} {'trades':>8} {'pass_end':>10} {'pass_roi':>10} {'arm-pass':>10}")
    print("-" * 100)
    for r in results:
        wlz = f"{r['arm_wins']}/{r['arm_losses']}/{r['arm_zeros']}"
        print(
            f"{r['symbol']:<8} ${r['arm_end_equity']:>8,.0f} {r['arm_roi_pct']:>+8.1f}% "
            f"{r['arm_max_dd_pct']:>+8.1f}% {wlz:>20} {r['arm_n_trades']:>8} "
            f"${r['passive_end_equity']:>8,.0f} {r['passive_roi_pct']:>+8.1f}% "
            f"{r['arm_minus_passive_roi_pct']:>+8.1f}pp"
        )
    print("-" * 100)
    bs = payload["basket"]
    print(
        f"BASKET   ${bs['arm_end_equity']:>8,.0f} {bs['arm_roi_pct']:>+8.1f}% "
        f"{'':>10} {'':>20} {'':>8} ${bs['passive_end_equity']:>8,.0f} "
        f"{bs['passive_roi_pct']:>+8.1f}% {bs['arm_roi_pct'] - bs['passive_roi_pct']:>+8.1f}pp"
    )
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
