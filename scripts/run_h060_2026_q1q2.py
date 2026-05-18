"""H060 cross-futures TSMOM daily-cadence on 2026-04-01 → 2026-05-15.

Scope: SUB-WINDOW DIAGNOSTIC. NOT a full KPI report card. ADR-0017 §3
primary metric vector + ADR-0018 D-1 MPPM(ρ=1) explicitly descoped
per N=38 sessions below the Politis-White 2004 minimum-block-length
threshold for stationary-bootstrap CI; sidecar marks
`kpi_report_card: false`, `scope: subwindow_diagnostic`.

H060 (per design.md §1): equal-weight basket of {ES, NQ, MGC, SIL};
signal_{i,t} = sign(R_{i,t-252,t-1}) — 252-day prior-period return;
positions scaled to ex-ante 10% annualised vol via COM-60 EWMA;
monthly rebalance on close. The frozen pre-reg's OOS is 2024-01-01 →
2025-12-30; this script extends through 2026-05-15 to fill the
"untested on 2026" gap.

Methodology: load daily-close bars (downsampled from 1-min) per symbol
2020-2026; compute TSMOM signal at t using info available through
t-1; apply position_t to log_ret_t to produce strategy_log_ret_t;
filter results to 2026-04-01 → 2026-05-15 sub-window.

Daily-close caveat (per R1 audit F-1-3): daily resampling is by UTC
calendar day, NOT CME session-date (16:00 ET equity / 17:00 CT energy/
metals). For ES/NQ this is approximately correct (session-close 21:00-
22:00 UTC, same UTC day). For MGC/SIL 24/5 sessions the UTC-day cut may
split a session; this script accepts the approximation for sub-window
diagnostic purposes. Sidecar marks `daily_close_convention: utc_day`.

Passive benchmarks (per R1 audit F-1-1): TWO passive arms reported.
(a) `passive_vol_scaled` — sign frozen at +1, same vol-target × kelly
scaling as TSMOM; this is degenerate with TSMOM on a long-only window.
(b) `passive_raw_bh` — raw unscaled buy-and-hold log return on the
underlying close prices; the canonical comparison per MOP 2012 §3.2.

Reference: Moskowitz-Ooi-Pedersen 2012 JFE 104(2):228-250
DOI 10.1016/j.jfineco.2011.11.003.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h060_2026")

_STARTING_EQUITY_PER_SYMBOL = 10_000.0
_LOOKBACK = 252
_VOL_COM = 60
_VOL_TARGET = 0.10
_KELLY_MULTIPLIER = 0.25
_RNG_SEED = 20260516  # deterministic numeric simulator; reserved for downstream bootstrap CI primitives


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
    """Return (combined_sha_or_unknown, provenance_json_path)."""
    p = _REPO_ROOT / "data" / "processed" / "_provenance" / "vendor_legacy_1min_roll_adjusted_20260516.json"
    if not p.exists():
        return "unknown", ""
    try:
        prov = json.loads(p.read_text(encoding="utf-8"))
        return str(prov.get("output_frame_sha256", "unknown")), str(p.relative_to(_REPO_ROOT))
    except Exception:  # noqa: BLE001
        return "unknown", str(p)


def _load_daily_close(substrate_root: Path, sym: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    sym_root = substrate_root / f"symbol={sym}"
    if not sym_root.exists():
        raise RuntimeError(f"symbol partition {sym_root} missing")
    years = sorted(int(p.name.split("=")[1]) for p in sym_root.glob("year=*"))
    pieces = []
    for y in years:
        if y < start.year or y > end.year:
            continue
        year_root = sym_root / f"year={y}"
        for parquet in sorted(year_root.glob("*.parquet")):
            try:
                df = pl.read_parquet(parquet).select(["ts_event", "close"])
                pieces.append(df.to_pandas())
            except Exception as exc:  # noqa: BLE001
                _log.warning("  %s: %s read failed: %s; skip", sym, parquet.name, exc)
    if not pieces:
        raise RuntimeError(f"no parquet for {sym}")
    df = pd.concat(pieces).sort_values("ts_event")
    # Coerce ts_event to UTC datetime
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts_event"])
    df = df[(df["ts_event"] >= start) & (df["ts_event"] <= end)]
    # Daily-close = last bar of each calendar day in UTC
    df["date"] = df["ts_event"].dt.date
    daily = df.groupby("date", as_index=False).agg(close=("close", "last"), ts_event=("ts_event", "last"))
    daily["date"] = pd.to_datetime(daily["date"], utc=True)
    daily = daily.sort_values("date").reset_index(drop=True)
    return daily


def _compute_tsmom_log_returns(daily: pd.DataFrame, lookback: int = _LOOKBACK,
                                vol_com: int = _VOL_COM, vol_target: float = _VOL_TARGET,
                                kelly_multiplier: float = _KELLY_MULTIPLIER) -> pd.DataFrame:
    """Compute per-day strategy log-returns for the TSMOM arm.

    PIT-causal indexing: position_t built from signal_{t-1} (already-realised
    rolling-sum sign) and vol_ewma_{t-1} (already-realised EWMA std), applied
    to log_ret_t = log(close_t/close_{t-1}) which is the period return
    EARNED on day t conditional on the position established at t-1's close.

    Concretely:
      signal_{t-1} = sign(sum_{k=t-1-lookback..t-1} log_ret_k)
      vol_{t-1}    = annualised EWMA std through t-1
      position_{t-1} = signal_{t-1} × (vol_target / vol_{t-1}) × kelly_mult
      strategy_log_ret_t = position_{t-1} × log_ret_t
    """
    daily = daily.copy()
    daily["log_ret"] = np.log(daily["close"] / daily["close"].shift(1))
    daily["roll_sum"] = daily["log_ret"].rolling(lookback, min_periods=lookback).sum()
    daily["signal"] = np.sign(daily["roll_sum"].shift(1))  # signal_{t-1}; avoids look-ahead
    # justify: pd.ewm(adjust=False).std() biased estimator; MOP 2012 §3 does
    # not pin bias treatment; bias < 1% by t > vol_com per geometric weight
    # decay; non-blocking for sub-window diagnostic. Tracked as audit minor.
    daily["vol_ewma"] = daily["log_ret"].ewm(com=vol_com, adjust=False).std() * np.sqrt(252)
    daily["vol_ewma_lag"] = daily["vol_ewma"].shift(1)  # vol_{t-1}
    daily["position"] = daily["signal"] * (vol_target / daily["vol_ewma_lag"]) * kelly_multiplier
    daily["strategy_log_ret"] = daily["position"] * daily["log_ret"]
    return daily


def main() -> int:
    sub_root = _REPO_ROOT / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    out_dir = (
        _REPO_ROOT / "artifacts" / "runs" / "H060"
        / f"v1_2026_q1q2_{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    warmup_start = pd.Timestamp("2020-01-01", tz="UTC")
    subwin_start = pd.Timestamp("2026-04-01", tz="UTC")
    subwin_end = pd.Timestamp("2026-06-30", tz="UTC")
    full_end = pd.Timestamp("2026-06-30", tz="UTC")

    results: list[dict[str, Any]] = []
    basket_log_rets: list[pd.Series] = []
    for sym in ["ES", "NQ", "MGC", "SIL"]:
        _log.info("Loading %s daily-close [%s -> %s]...", sym, warmup_start.date(), full_end.date())
        try:
            daily = _load_daily_close(sub_root, sym, start=warmup_start, end=full_end)
        except RuntimeError as exc:
            _log.warning("  %s: load failed: %s; skip", sym, exc)
            continue
        _log.info("  %s: %d daily bars", sym, len(daily))
        df_sim = _compute_tsmom_log_returns(daily)
        # Signal distribution diagnostic (per R1 audit F-1-1)
        signal_counts = df_sim["signal"].dropna().value_counts().to_dict()
        signal_n_pos = int(signal_counts.get(1.0, 0))
        signal_n_neg = int(signal_counts.get(-1.0, 0))
        signal_n_zero = int(signal_counts.get(0.0, 0))
        # Sub-window signal distribution
        sub_mask_pre = (df_sim["date"] >= subwin_start) & (df_sim["date"] <= subwin_end)
        sub_signal_counts = df_sim.loc[sub_mask_pre, "signal"].dropna().value_counts().to_dict()
        sub_sig_n_pos = int(sub_signal_counts.get(1.0, 0))
        sub_sig_n_neg = int(sub_signal_counts.get(-1.0, 0))

        # Filter to sub-window
        sub_mask = sub_mask_pre
        sub_df = df_sim[sub_mask].copy()
        sub_lr = sub_df["strategy_log_ret"].dropna().to_numpy()
        # Build sub-window equity
        sub_eq = [_STARTING_EQUITY_PER_SYMBOL]
        for lr in sub_lr:
            sub_eq.append(sub_eq[-1] * float(np.exp(lr)))
        sub_eqa = np.array(sub_eq)
        if sub_eqa.size > 1:
            running_max = np.maximum.accumulate(sub_eqa)
            dd = (sub_eqa - running_max) / running_max
            sub_maxdd = float(-dd.min())
        else:
            sub_maxdd = 0.0
        sub_end_eq = float(sub_eqa[-1])
        sub_roi = (sub_end_eq / _STARTING_EQUITY_PER_SYMBOL - 1.0) * 100
        n_sess = int(np.isfinite(sub_lr).sum())
        n_wins = int((sub_lr > 0).sum())
        n_losses = int((sub_lr < 0).sum())
        n_zeros = int((sub_lr == 0).sum())
        # Passive vol-scaled arm = sign frozen +1 with SAME vol-scaling × kelly
        # (degenerate-by-construction with TSMOM on long-only windows; F-1-1)
        passive_vs_log_ret = (
            df_sim["log_ret"]
            * (_VOL_TARGET / df_sim["vol_ewma_lag"])
            * _KELLY_MULTIPLIER
        )
        sub_pvs_lr = passive_vs_log_ret[sub_mask].dropna().to_numpy()
        pvs_eq = [_STARTING_EQUITY_PER_SYMBOL]
        for lr in sub_pvs_lr:
            pvs_eq.append(pvs_eq[-1] * float(np.exp(lr)))
        pvs_eqa = np.array(pvs_eq)
        pvs_end_eq = float(pvs_eqa[-1])
        pvs_roi = (pvs_end_eq / _STARTING_EQUITY_PER_SYMBOL - 1.0) * 100
        if pvs_eqa.size > 1:
            rmax = np.maximum.accumulate(pvs_eqa)
            pvs_dd = float(-((pvs_eqa - rmax) / rmax).min())
        else:
            pvs_dd = 0.0

        # Passive raw buy-and-hold = unscaled log_ret on underlying (canonical
        # per MOP 2012 §3.2)
        sub_raw_lr = df_sim.loc[sub_mask, "log_ret"].dropna().to_numpy()
        raw_eq = [_STARTING_EQUITY_PER_SYMBOL]
        for lr in sub_raw_lr:
            raw_eq.append(raw_eq[-1] * float(np.exp(lr)))
        raw_eqa = np.array(raw_eq)
        raw_end_eq = float(raw_eqa[-1])
        raw_roi = (raw_end_eq / _STARTING_EQUITY_PER_SYMBOL - 1.0) * 100
        if raw_eqa.size > 1:
            rmax_raw = np.maximum.accumulate(raw_eqa)
            raw_dd = float(-((raw_eqa - rmax_raw) / rmax_raw).min())
        else:
            raw_dd = 0.0

        results.append({
            "symbol": sym,
            "n_sessions_subwin": n_sess,
            "subwin_end_equity": sub_end_eq,
            "subwin_roi_pct": sub_roi,
            "subwin_max_dd_pct": sub_maxdd * 100,
            "subwin_wins": n_wins,
            "subwin_losses": n_losses,
            "subwin_zeros": n_zeros,
            "passive_vol_scaled_subwin_roi_pct": pvs_roi,
            "passive_vol_scaled_subwin_max_dd_pct": pvs_dd * 100,
            "passive_raw_bh_subwin_roi_pct": raw_roi,
            "passive_raw_bh_subwin_max_dd_pct": raw_dd * 100,
            "signal_n_pos_full_window": signal_n_pos,
            "signal_n_neg_full_window": signal_n_neg,
            "signal_n_zero_full_window": signal_n_zero,
            "signal_n_pos_subwin": sub_sig_n_pos,
            "signal_n_neg_subwin": sub_sig_n_neg,
        })
        basket_log_rets.append(sub_df.set_index("date")["strategy_log_ret"])
        _log.info(
            "  %s: TSMOM ROI=%.2f%% DD=%.2f%% n_sess=%d  signal_subwin(+/-)=%d/%d  |  passive_vs ROI=%.2f%%  passive_raw_bh ROI=%.2f%%",
            sym, sub_roi, sub_maxdd*100, n_sess, sub_sig_n_pos, sub_sig_n_neg,
            pvs_roi, raw_roi,
        )

    if not results:
        _log.error("No results produced; aborting")
        return 1

    basket_subwin_end = sum(r["subwin_end_equity"] for r in results)
    basket_start = _STARTING_EQUITY_PER_SYMBOL * len(results)
    basket_subwin_roi = (basket_subwin_end / basket_start - 1.0) * 100

    # Equal-weight basket aggregate strategy log-return path
    if len(basket_log_rets) >= 1:
        basket_df = pd.concat(basket_log_rets, axis=1)
        basket_avg_lr = basket_df.mean(axis=1).dropna().to_numpy()
        basket_eq = [_STARTING_EQUITY_PER_SYMBOL]
        for lr in basket_avg_lr:
            basket_eq.append(basket_eq[-1] * float(np.exp(lr)))
        basket_eqa = np.array(basket_eq)
        if basket_eqa.size > 1:
            rmax = np.maximum.accumulate(basket_eqa)
            basket_dd = float(-((basket_eqa - rmax) / rmax).min())
        else:
            basket_dd = 0.0
        basket_eq_roi = (float(basket_eqa[-1]) / _STARTING_EQUITY_PER_SYMBOL - 1.0) * 100
    else:
        basket_dd = 0.0
        basket_eq_roi = 0.0

    sub_sha, prov_path = _substrate_sha()
    script_path = Path(__file__).resolve()
    payload = {
        "experiment": "h060_v1_2026_q1q2_subwindow",
        "kpi_report_card": False,
        "scope": "subwindow_diagnostic",
        "descoped_kpis": {
            "reason": "sub-window N~38 sessions insufficient for stationary-bootstrap CI per Politis-White 2004 minimum-block-length threshold",
            "authorized_by": "operator 2026-05-16",
            "refs": ["ADR-0013", "ADR-0017", "ADR-0018"],
            "missing": ["mppm_rho1_ci", "calmar_differential_ci", "profit_factor_ci",
                        "r_multiple_mean_ci", "terminal_wealth_q05", "probability_of_ruin",
                        "l_skewness_tau3", "forward_projection_252_session"],
        },
        "daily_close_convention": "utc_day",
        "daily_close_caveat": "Daily resampling is UTC-calendar-day, not CME session-date (16:00 ET / 17:00 CT). Approximate for ES/NQ; may split sessions for MGC/SIL 24/5. Tracked under R1 audit F-1-3.",
        "warm_up_start": str(warmup_start),
        "subwin_start": str(subwin_start),
        "subwin_end": str(subwin_end),
        "config": {
            "lookback": _LOOKBACK,
            "vol_com": _VOL_COM,
            "vol_target": _VOL_TARGET,
            "kelly_multiplier": _KELLY_MULTIPLIER,
            "rng_seed": _RNG_SEED,
        },
        "provenance": {
            "git_head": _git_head(),
            "substrate_dataset_checksum": sub_sha,
            "substrate_provenance_path": prov_path,
            "producing_script_path": str(script_path.relative_to(_REPO_ROOT)),
            "producing_script_sha256": _script_sha256(script_path),
            "rng_seed": _RNG_SEED,
        },
        "per_symbol": results,
        "basket": {
            "starting_equity_total": basket_start,
            "end_equity_subwin_sum_of_symbols": basket_subwin_end,
            "subwin_roi_pct_sum_of_symbols": basket_subwin_roi,
            "subwin_roi_pct_equal_weight_log_avg": basket_eq_roi,
            "subwin_max_dd_pct_equal_weight": basket_dd * 100,
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
    print("H060 CROSS-FUTURES TSMOM 2026-Q1-Q2 SUB-WINDOW (km=0.25, lookback=252)")
    print("=" * 80)
    print(f"basket(sum):  starting=${basket_start:,.0f} end=${basket_subwin_end:,.0f} ROI={basket_subwin_roi:+.2f}%")
    print(f"basket(EW log-avg): ROI={basket_eq_roi:+.2f}%  MaxDD={basket_dd*100:.2f}%")
    print()
    print(f"{'sym':<5} {'n_sess':<7} {'tsmom%':<9} {'tsmom_DD%':<10} {'pvs%':<8} {'p_raw%':<9} {'raw_DD%':<9} {'sig+/sig-':<10} {'W/L/Z':<11}")
    for r in results:
        wlz = f"{r['subwin_wins']}/{r['subwin_losses']}/{r['subwin_zeros']}"
        sig = f"{r['signal_n_pos_subwin']}/{r['signal_n_neg_subwin']}"
        print(f"{r['symbol']:<5} {r['n_sessions_subwin']:<7} {r['subwin_roi_pct']:<+8.2f}% {r['subwin_max_dd_pct']:<9.2f}% {r['passive_vol_scaled_subwin_roi_pct']:<+7.2f}% {r['passive_raw_bh_subwin_roi_pct']:<+8.2f}% {r['passive_raw_bh_subwin_max_dd_pct']:<8.2f}% {sig:<10} {wlz:<11}")
    print("=" * 80)
    print("pvs = passive vol-scaled (same scaling as TSMOM; degenerate with TSMOM on all-long-signal windows)")
    print("p_raw = passive RAW buy-and-hold (unscaled; canonical per MOP 2012 §3.2)")
    print("sig+/sig- = TSMOM signal distribution within sub-window (count of +1/-1 days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
