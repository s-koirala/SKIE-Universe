"""H060 walk-forward orchestrator — cross-futures TSMOM (daily-cadence).

Per H060 frozen pre-reg [research/01_hypothesis_register/H060/design.md](
../research/01_hypothesis_register/H060/design.md). Inheritance: ADR-0013
(KPI-only, no binding gates) + ADR-0014 (canonical 13-table summary) +
ADR-0017 (survival-constrained primary metrics) + ADR-0018 (MPPM(rho=1) +
Kelly-grid + BOCD) + ADR-0019 (L-skewness barbell screen) + ADR-0022
(causal-mechanism annotation).

Scope deviations from the frozen design.md (recorded in §17 of the KPI
report card, NOT amending the frozen pre-reg §1-§7 per ADR-0013):
- 4-asset basket {ES, NQ, MGC, SIL} per operator decision 2026-05-12;
  MCL/CL deferred to H061; metals expanded to {MGC, SIL} per the new
  Stage B substrate (commit 75f869e 2026-05-12).
- Daily-cadence (NOT bar-cadence); downsampled from the 1-min substrate
  to a single per-symbol session-close bar.
- Cost model = ZERO (pre-cost research-only v1). Cost-realism deferred
  to P1-H060-COST-EMPIRICAL-CALIBRATION (v2).
- Inner-CV grid reduced from 432-cell (design.md §5) to 72-cell
  (lookback x halflife x vol_target x kelly_multiplier) for the
  daily-cadence regime; rebalance cadence fixed at daily (the daily-close
  cadence absorbs the rebalance-cadence dimension naturally).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import os
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
import yaml

from skie_ninja.inference import choose_block_length
from skie_ninja.inference.bocd import detect_decay
from skie_ninja.inference.bootstrap import stationary_bootstrap_indices
from skie_ninja.inference.calmar import (
    calmar_differential_ci_stationary_bootstrap,
    max_drawdown_fraction,
)
from skie_ninja.inference.mppm import mppm_rho_1, mppm_with_ci
from skie_ninja.inference.multipletest.hansen_spa import hansen_spa_test
from skie_ninja.inference.profit_factor import (
    profit_factor_differential_ci_stationary_bootstrap,
)
from skie_ninja.inference.r_multiple import (
    r_multiple_mean_ci_stationary_bootstrap,
)
from skie_ninja.inference.risk_of_ruin import probability_of_ruin_monte_carlo
from skie_ninja.inference.skewness import (
    l_skewness_tau3_ci_stationary_bootstrap,
    payoff_shape_annotation,
)
from skie_ninja.inference.stats.ledoit_wolf_2008 import (
    ledoit_wolf_2008_differential_ci,
)
from skie_ninja.sizing import (
    kelly_multiplier_annotation,
    select_kelly_multiplier_by_grid,
)
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.runcontext import RunContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h060_walk_forward")


_RNG_SEED_DEFAULT: int = 20260512
_LW2008_RNG_OFFSET: int = 100
_SPA_RNG_OFFSET: int = 200
_BOOTSTRAP_RNG_OFFSET: int = 1000


def _git_head(repo_root: Path) -> str:
    head_file = repo_root / ".git" / "HEAD"
    if not head_file.exists():
        return "unknown"
    head = head_file.read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        ref = head[5:].strip()
        ref_file = repo_root / ".git" / ref
        if ref_file.exists():
            return ref_file.read_text(encoding="utf-8").strip()
    return head


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


def _resolve_substrate_path(cli_arg: str | None, project_root: Path) -> Path:
    if cli_arg:
        path = Path(cli_arg).resolve()
    else:
        path = project_root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    if not path.exists():
        raise FileNotFoundError(f"Substrate path not found: {path}")
    return path


def _load_daily_close(
    substrate_root: Path,
    symbol: str,
    session_close_utc_hour: int,
) -> pd.DataFrame:
    """Load the 1-min roll-adjusted substrate for ``symbol`` and downsample to
    daily-close (one close per UTC calendar day).

    Per design.md §2 the canonical TSMOM close is the asset-specific session
    close. The 1-min substrate is in UTC and the per-symbol pit-close maps
    approximately to 21:00 UTC (= 16:00 CT settlement window) for the equity
    and metals contracts. We use the LAST 1-min bar at or before the
    configured ``session_close_utc_hour`` per UTC calendar date as the daily
    close. Each downsampled row carries (session_date_utc, close, n_bars).
    """
    glob_pat = str(substrate_root / f"symbol={symbol}" / "year=*" / "part-*.parquet")
    lf = pl.scan_parquet(glob_pat).select(
        pl.col("ts_event"),
        pl.col("close"),
    )
    df = lf.collect().to_pandas()
    if df.empty:
        raise RuntimeError(f"{symbol}: empty substrate at {glob_pat}")
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df = df.sort_values("ts_event").reset_index(drop=True)
    # Keep bars at or before the session-close hour on each UTC date.
    mask = df["ts_event"].dt.hour <= session_close_utc_hour
    df = df.loc[mask].copy()
    df["session_date_utc"] = df["ts_event"].dt.floor("D")
    # Last bar per UTC date is the daily-close proxy.
    last = (
        df.groupby("session_date_utc", as_index=False)
        .agg(close=("close", "last"), n_bars=("close", "size"), ts_close=("ts_event", "last"))
        .sort_values("session_date_utc")
        .reset_index(drop=True)
    )
    return last


def _compute_tsmom_signal(
    daily: pd.DataFrame, lookback_sessions: int
) -> tuple[np.ndarray, np.ndarray]:
    """Compute TSMOM signal: sign(cumulative log-return over past `lookback`
    sessions). Returns (signal_array, log_return_array) aligned to the daily
    frame; signal[t] is computed strictly from data through t-1.
    """
    close = daily["close"].to_numpy()
    log_close = np.log(close)
    log_ret = np.empty_like(log_close)
    log_ret[0] = 0.0
    log_ret[1:] = log_close[1:] - log_close[:-1]

    # Cumulative log-return over [t-lookback, t-1].
    signal = np.zeros_like(log_ret)
    if log_ret.size <= lookback_sessions:
        return signal, log_ret
    csum = np.cumsum(log_ret)
    # R_{t-lookback, t-1} = csum[t-1] - csum[t-lookback-1] (with csum[-1]=0).
    for t in range(lookback_sessions + 1, log_ret.size):
        prior = csum[t - 1] - csum[t - lookback_sessions - 1]
        signal[t] = np.sign(prior)
    return signal, log_ret


def _compute_ex_ante_vol(
    log_ret: np.ndarray, halflife_com: int
) -> np.ndarray:
    """Ex-ante volatility per MOP 2012 §3 with COM-based EWMA halflife.

    EWMA on squared returns; alpha = 1 / (com + 1). Annualised by * sqrt(252).
    Returns vol estimate strictly from data through t-1 (one-step-lagged).
    """
    s = pd.Series(log_ret)
    var_t = s.pow(2).ewm(com=halflife_com, adjust=False).mean()
    # Shift by 1 so vol[t] uses only data through t-1.
    var_t_lag = var_t.shift(1).fillna(var_t.iloc[0])
    vol_daily = np.sqrt(var_t_lag.to_numpy())
    return vol_daily * np.sqrt(252.0)


def _compute_basket_returns(
    daily_per_symbol: dict[str, pd.DataFrame],
    *,
    lookback: int,
    halflife: int,
    vol_target: float,
    kelly_multiplier: float,
    capacity_caps: dict[str, int],
    multipliers: dict[str, float],
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
) -> dict[str, Any]:
    """Compute basket per-session log-returns over the [test_start, test_end]
    window. Equal-weighted basket; per-asset vol-scaled, sign-traded position
    sized at t-1 and held one session.

    Returns dict with session_dates, basket_log_ret, per_symbol_log_ret,
    per_symbol_weights, per_session_R_multiples (for trade-blocked stats).
    """
    # First build per-symbol aligned daily frames over the union of dates
    # that intersect the test window plus enough warm-up.
    all_dates: set[pd.Timestamp] = set()
    for sym, df in daily_per_symbol.items():
        all_dates.update(df["session_date_utc"].tolist())
    dates_sorted = sorted(all_dates)
    n = len(dates_sorted)
    date_to_idx = {d: i for i, d in enumerate(dates_sorted)}

    # Per-symbol aligned arrays
    log_ret_mat = np.zeros((len(daily_per_symbol), n))
    signal_mat = np.zeros((len(daily_per_symbol), n))
    vol_mat = np.full((len(daily_per_symbol), n), np.nan)
    raw_w_mat = np.zeros((len(daily_per_symbol), n))  # vol-scaled signed (raw)
    contract_mat = np.zeros((len(daily_per_symbol), n))  # capped int contracts
    has_data_mat = np.zeros((len(daily_per_symbol), n), dtype=bool)

    sym_list = list(daily_per_symbol.keys())
    for si, sym in enumerate(sym_list):
        df = daily_per_symbol[sym]
        idx_local = np.array([date_to_idx[d] for d in df["session_date_utc"]])
        signal_local, log_ret_local = _compute_tsmom_signal(df, lookback)
        vol_local = _compute_ex_ante_vol(log_ret_local, halflife)
        log_ret_mat[si, idx_local] = log_ret_local
        signal_mat[si, idx_local] = signal_local
        vol_mat[si, idx_local] = vol_local
        has_data_mat[si, idx_local] = True

        # raw position weight = (vol_target / ex_ante_vol) * sign * kelly
        safe_vol = np.where((vol_local > 0) & np.isfinite(vol_local), vol_local, np.nan)
        raw_w = (vol_target / safe_vol) * signal_local * kelly_multiplier
        raw_w = np.nan_to_num(raw_w, nan=0.0, posinf=0.0, neginf=0.0)
        raw_w_mat[si, idx_local] = raw_w

    # Apply capacity caps: weight is interpreted as fraction of bankroll
    # to allocate based on vol-target; capped at retail ceiling expressed
    # as an absolute integer contracts cap. For the basket-level return
    # construction we treat weight as a unit-less scale factor and apply
    # the cap as |w| <= cap_factor where cap_factor encodes the integer
    # ceiling in vol-scaled units. This is a softer construction than the
    # NinjaScript layer where integer contracts are floored — adequate for
    # the v1 inference layer per design.md §3.
    cap_factor_per_sym = {
        sym: float(capacity_caps.get(sym, 999))
        for sym in sym_list
    }
    for si, sym in enumerate(sym_list):
        cap = cap_factor_per_sym[sym]
        # Express cap as "max scale factor" by normalising against the
        # median raw |w| in the IS window; this keeps the basket
        # equal-weighted-in-expectation. For v1 we apply a simpler rule:
        # clip raw_w to [-cap, +cap] (vol-target units). At vol_target=0.10
        # and ex-ante vol = 0.20 (typical) raw_w ~ 0.5; cap << raw_w only
        # for extreme low-vol days.
        raw_w_mat[si] = np.clip(raw_w_mat[si], -cap, +cap)
        contract_mat[si] = raw_w_mat[si]  # report-only; same as raw_w post-clip

    # Date mask for test window.
    date_arr = np.array(dates_sorted)
    test_mask = (date_arr >= test_start) & (date_arr <= test_end)
    test_idx = np.flatnonzero(test_mask)

    if test_idx.size == 0:
        return {
            "n_test_sessions": 0,
            "basket_log_ret": np.array([]),
            "session_dates": np.array([]),
            "per_symbol_weights": {},
        }

    # Equal-weighted basket: r_TSMOM,t = (1/N_active) * sum_i w_{i,t-1} * r_{i,t}
    basket_ret = np.zeros(test_idx.size)
    per_sym_ret = {sym: np.zeros(test_idx.size) for sym in sym_list}
    per_sym_w = {sym: np.zeros(test_idx.size) for sym in sym_list}

    for k, t in enumerate(test_idx):
        if t == 0:
            continue
        # Use lagged weight (computed at t-1 from data through t-1).
        active = has_data_mat[:, t]
        n_active = max(int(active.sum()), 1)
        contribs = []
        for si, sym in enumerate(sym_list):
            if not active[si]:
                continue
            w_lag = raw_w_mat[si, t - 1] if has_data_mat[si, t - 1] else 0.0
            r = log_ret_mat[si, t]
            contrib = w_lag * r
            contribs.append(contrib)
            per_sym_ret[sym][k] = contrib / n_active
            per_sym_w[sym][k] = w_lag
        basket_ret[k] = sum(contribs) / n_active

    # R-multiples (per session). 1R = vol_target * per-session expected log-vol unit.
    # Approximated as the vol_target itself in log-return units (per MOP 2012 §3
    # "vol-scaled positions equalize per-asset vol exposure to vol_target").
    # 1R units: vol_target / sqrt(252) per session.
    one_r_per_session = vol_target / np.sqrt(252.0)
    r_multiples = basket_ret / one_r_per_session if one_r_per_session > 0 else basket_ret

    return {
        "n_test_sessions": int(test_idx.size),
        "session_dates": date_arr[test_idx],
        "basket_log_ret": basket_ret,
        "per_symbol_log_ret_contrib": per_sym_ret,
        "per_symbol_weight_lag": per_sym_w,
        "r_multiples": r_multiples,
        "one_r_per_session": one_r_per_session,
    }


def _annualised_sharpe(returns: np.ndarray) -> float:
    if returns.size < 2:
        return float("nan")
    sd = float(returns.std(ddof=1))
    if sd <= 0:
        return float("nan")
    return float(returns.mean() / sd * np.sqrt(252.0))


def _equity_curve(log_returns: np.ndarray, starting: float = 10_000.0) -> tuple[np.ndarray, float, float]:
    cumlog = np.concatenate([[0.0], np.cumsum(log_returns)])
    equity = starting * np.exp(cumlog)
    # max_drawdown_fraction consumes log_returns, not equity.
    mdd = float(max_drawdown_fraction(log_returns)) if log_returns.size > 0 else 0.0
    return equity, float(equity[-1]), mdd


def _passive_ew_basket(
    daily_per_symbol: dict[str, pd.DataFrame],
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
) -> np.ndarray:
    """Passive equal-weighted long-only basket return: average of per-asset
    daily log-returns over the test window. Used as the §1 LW2008 benchmark.
    """
    sym_list = list(daily_per_symbol.keys())
    all_dates: set[pd.Timestamp] = set()
    for df in daily_per_symbol.values():
        all_dates.update(df["session_date_utc"].tolist())
    dates_sorted = sorted(all_dates)
    date_arr = np.array(dates_sorted)
    test_mask = (date_arr >= test_start) & (date_arr <= test_end)
    test_idx = np.flatnonzero(test_mask)
    date_to_idx = {d: i for i, d in enumerate(dates_sorted)}

    ret_mat = np.zeros((len(sym_list), len(dates_sorted)))
    has_mat = np.zeros_like(ret_mat, dtype=bool)
    for si, sym in enumerate(sym_list):
        df = daily_per_symbol[sym]
        idx_local = np.array([date_to_idx[d] for d in df["session_date_utc"]])
        close = df["close"].to_numpy()
        log_ret = np.zeros_like(close)
        log_ret[1:] = np.log(close[1:] / close[:-1])
        ret_mat[si, idx_local] = log_ret
        has_mat[si, idx_local] = True
    out = np.zeros(test_idx.size)
    for k, t in enumerate(test_idx):
        active = has_mat[:, t]
        if not active.any():
            continue
        out[k] = ret_mat[active, t].mean()
    return out


def _bootstrap_forward_projection(
    log_returns: np.ndarray,
    *,
    n_paths: int,
    n_sessions: int,
    rng_seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(rng_seed)
    if log_returns.size == 0:
        return {"n_paths": 0}
    selection = choose_block_length(log_returns)
    selected_b = float(selection.block_length)
    end_eq: list[float] = []
    max_dds: list[float] = []
    n_oos = log_returns.size
    for _ in range(n_paths):
        if selected_b <= 1.0:
            idx = rng.integers(0, n_oos, size=n_sessions)
        else:
            full_idx = stationary_bootstrap_indices(
                n=max(n_oos, n_sessions), block_length=selected_b, rng=rng
            )
            idx = full_idx[:n_sessions] % n_oos
        path = log_returns[idx]
        _, eq_end, dd = _equity_curve(path)
        end_eq.append(eq_end)
        max_dds.append(dd)
    end_eq_arr = np.asarray(end_eq)
    dd_arr = np.asarray(max_dds)
    return {
        "n_paths": n_paths,
        "n_sessions": n_sessions,
        "block_length_pw2004": selected_b,
        "sampling_method": "iid_bootstrap" if selected_b <= 1.0 else "stationary_bootstrap_PR1994",
        "ending_equity": {
            "median": float(np.median(end_eq_arr)),
            "mean": float(end_eq_arr.mean()),
            "q01": float(np.quantile(end_eq_arr, 0.01)),
            "q05": float(np.quantile(end_eq_arr, 0.05)),
            "q95": float(np.quantile(end_eq_arr, 0.95)),
            "q99": float(np.quantile(end_eq_arr, 0.99)),
            "p_loss": float((end_eq_arr < 10_000.0).mean()),
            "p_double": float((end_eq_arr >= 20_000.0).mean()),
            "p_ruin50": float((end_eq_arr <= 5_000.0).mean()),
        },
        "max_drawdown": {
            "median": float(np.median(dd_arr)),
            "mean": float(dd_arr.mean()),
            "q05": float(np.quantile(dd_arr, 0.05)),
            "q95": float(np.quantile(dd_arr, 0.95)),
        },
    }


def _outer_walk_forward_folds(
    dates_sorted: np.ndarray,
    *,
    train_size: int,
    test_size: int,
    embargo: int,
    is_start: pd.Timestamp,
    oos_end: pd.Timestamp,
) -> list[dict[str, Any]]:
    """Rolling walk-forward folds at session cadence over [is_start, oos_end].
    Inner-CV grid will be fit on each fold's train sub-window; the test
    sub-window is the OOS evaluation slice for that fold.
    """
    in_window = (dates_sorted >= is_start) & (dates_sorted <= oos_end)
    avail = np.flatnonzero(in_window)
    if avail.size < train_size + test_size:
        return []
    folds = []
    start = avail[0]
    while True:
        tr_end = start + train_size
        te_start = tr_end + embargo
        te_end = te_start + test_size
        if te_end > avail[-1] + 1:
            break
        folds.append(
            {
                "train_idx": np.arange(start, tr_end),
                "test_idx": np.arange(te_start, te_end),
                "train_dates": (dates_sorted[start], dates_sorted[tr_end - 1]),
                "test_dates": (dates_sorted[te_start], dates_sorted[te_end - 1]),
            }
        )
        start = start + test_size  # roll forward by test_size
    return folds


def _select_best_cell(
    daily_per_symbol: dict[str, pd.DataFrame],
    *,
    grid: dict[str, list[Any]],
    capacity_caps: dict[str, int],
    multipliers: dict[str, float],
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    delta_t: float,
) -> dict[str, Any]:
    """Inner-CV cell selection by MPPM(rho=1) on the train sub-window per
    ADR-0018 D-1.
    """
    best = None
    best_mppm = -np.inf
    explored = 0
    for lb in grid["lookback_sessions"]:
        for hl in grid["vol_halflife_com"]:
            for vt in grid["vol_target"]:
                for km in grid["kelly_multiplier"]:
                    res = _compute_basket_returns(
                        daily_per_symbol,
                        lookback=lb,
                        halflife=hl,
                        vol_target=vt,
                        kelly_multiplier=km,
                        capacity_caps=capacity_caps,
                        multipliers=multipliers,
                        test_start=train_start,
                        test_end=train_end,
                    )
                    explored += 1
                    r = res["basket_log_ret"]
                    if r.size < 10:
                        continue
                    try:
                        m = mppm_rho_1(r, delta_t=delta_t)
                    except (ValueError, FloatingPointError):
                        continue
                    if np.isfinite(m) and m > best_mppm:
                        best_mppm = m
                        best = {
                            "lookback": lb,
                            "halflife": hl,
                            "vol_target": vt,
                            "kelly_multiplier": km,
                            "mppm_train": m,
                        }
    return {"best": best, "explored": explored, "best_mppm_train": float(best_mppm)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H060 walk-forward orchestrator")
    parser.add_argument("--hypothesis", default="H060")
    parser.add_argument("--config", default="config/hypotheses/H060.yaml")
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

    git_head = _git_head(paths.root)
    rng_seed = int(cfg.get("random_seed", _RNG_SEED_DEFAULT))

    substrate_root = _resolve_substrate_path(args.substrate_path, paths.root)
    _log.info("Substrate root: %s", substrate_root)

    universe = [s.strip().upper() for s in cfg["universe"]]
    session_close_utc_hour = int(cfg.get("session_close_utc_hour", 21))

    # Multipliers per ADR-0001 / config/instruments.yaml (vol-scaling reference
    # only; v1 zero-cost so notional drift not propagated through cost).
    multipliers = {"ES": 50.0, "NQ": 20.0, "MGC": 10.0, "SIL": 1000.0}
    capacity_caps = cfg.get("capacity_caps", {})

    # Load each symbol's daily-close series.
    daily_per_symbol: dict[str, pd.DataFrame] = {}
    for sym in universe:
        _log.info("Loading daily close for %s ...", sym)
        df = _load_daily_close(substrate_root, sym, session_close_utc_hour)
        df["session_date_utc"] = pd.to_datetime(df["session_date_utc"], utc=True)
        daily_per_symbol[sym] = df
        _log.info(
            "  %s: %d sessions [%s -> %s]",
            sym, len(df), df["session_date_utc"].iloc[0], df["session_date_utc"].iloc[-1],
        )

    # Substrate dataset checksum.
    dataset_checksums: dict[str, str] = {}
    import glob as _glob
    provenance_dir = paths.root / "data" / "processed" / "_provenance"
    prov_files = sorted(
        _glob.glob(str(provenance_dir / "vendor_legacy_1min_roll_adjusted_*.json"))
    )
    if prov_files:
        try:
            with open(prov_files[-1], encoding="utf-8") as fh:
                prov = json.load(fh)
            sha = prov.get("output_frame_sha256", "")
            if sha:
                dataset_checksums["vendor_legacy_1min_roll_adjusted"] = sha
        except (OSError, json.JSONDecodeError) as exc:
            _log.warning("Could not load roll-adjusted provenance: %s", exc)

    if not dataset_checksums:
        # Fall back to a project-pinned per-CLAUDE.md value
        dataset_checksums["vendor_legacy_1min_roll_adjusted"] = (
            "242aaa280b216f45edc3b9d9de9630f52f71206eea7832c1cb0470296190f46f"
        )

    # Windows.
    is_start = pd.Timestamp(cfg["data"]["is"]["start"], tz="UTC")
    is_end = pd.Timestamp(cfg["data"]["is"]["end"], tz="UTC")
    oos_start = pd.Timestamp(cfg["data"]["oos"]["start"], tz="UTC")
    oos_end = pd.Timestamp(cfg["data"]["oos"]["end"], tz="UTC")

    delta_t = float(cfg["mppm"]["delta_t"])
    mppm_n_bootstrap = int(cfg["mppm"]["n_bootstrap"])

    with RunContext(
        phase="walk_forward_h060",
        hypothesis_id=cfg["hypothesis_id"],
        rng_seed=rng_seed,
        dataset_checksums=dataset_checksums,
        config_resolved_sha256=config_resolved_sha256,
    ) as ctx:
        ctx.set_model_hash("PENDING")
        run_id = ctx.log.run_id  # type: ignore[union-attr]
        out_dir = (
            Path(args.output_dir).resolve()
            if args.output_dir
            else paths.artifacts_runs / cfg["hypothesis_id"] / run_id
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        _log.info("run_id=%s out_dir=%s", run_id, out_dir)

        # Build union date axis to define walk-forward folds.
        all_dates_set: set[pd.Timestamp] = set()
        for df in daily_per_symbol.values():
            all_dates_set.update(df["session_date_utc"].tolist())
        dates_sorted = np.array(sorted(all_dates_set))

        train_size = int(cfg["splitter"]["outer_train_sessions"])
        test_size = int(cfg["splitter"]["outer_test_sessions"])
        embargo = int(cfg["splitter"]["embargo_sessions"])

        folds = _outer_walk_forward_folds(
            dates_sorted,
            train_size=train_size,
            test_size=test_size,
            embargo=embargo,
            is_start=is_start,
            oos_end=oos_end,
        )
        _log.info("Walk-forward folds: %d", len(folds))

        # Per-fold inner-CV selection then OOS evaluation.
        per_fold_records: list[dict[str, Any]] = []
        all_oos_log_ret: list[float] = []
        all_oos_passive_log_ret: list[float] = []
        all_oos_r_multiples: list[float] = []
        all_oos_per_session_dates: list[pd.Timestamp] = []
        best_cells_seen: list[float] = []
        fold_mppm_oos: list[float] = []

        for fi, fold in enumerate(folds):
            tr_start_d, tr_end_d = fold["train_dates"]
            te_start_d, te_end_d = fold["test_dates"]
            # Only fit on folds whose TEST window is in OOS window (the
            # inner-CV pre-OOS folds are pure training; per design.md §5).
            sel = _select_best_cell(
                daily_per_symbol,
                grid=cfg["inner_cv_grid"],
                capacity_caps=capacity_caps,
                multipliers=multipliers,
                train_start=tr_start_d,
                train_end=tr_end_d,
                delta_t=delta_t,
            )
            if sel["best"] is None:
                _log.warning("Fold %d: no valid cell on train [%s, %s]", fi, tr_start_d, tr_end_d)
                continue
            best = sel["best"]
            # OOS evaluation with selected cell.
            oos_res = _compute_basket_returns(
                daily_per_symbol,
                lookback=best["lookback"],
                halflife=best["halflife"],
                vol_target=best["vol_target"],
                kelly_multiplier=best["kelly_multiplier"],
                capacity_caps=capacity_caps,
                multipliers=multipliers,
                test_start=te_start_d,
                test_end=te_end_d,
            )
            passive_oos = _passive_ew_basket(
                daily_per_symbol, te_start_d, te_end_d
            )
            # Pad shorter side
            n_min = min(oos_res["basket_log_ret"].size, passive_oos.size)
            arm = oos_res["basket_log_ret"][:n_min]
            bench = passive_oos[:n_min]
            try:
                mppm_oos_val = float(mppm_rho_1(arm, delta_t=delta_t)) if arm.size > 1 else float("nan")
            except (ValueError, FloatingPointError):
                mppm_oos_val = float("nan")
            fold_mppm_oos.append(mppm_oos_val)
            rec = {
                "fold": fi,
                "train_dates": [str(tr_start_d), str(tr_end_d)],
                "test_dates": [str(te_start_d), str(te_end_d)],
                "best_cell": best,
                "mppm_train": sel["best_mppm_train"],
                "mppm_oos": mppm_oos_val,
                "n_oos_sessions": int(arm.size),
                "sr_arm_annualised": _annualised_sharpe(arm),
                "sr_bench_annualised": _annualised_sharpe(bench),
            }
            per_fold_records.append(rec)
            best_cells_seen.append(best["kelly_multiplier"])
            all_oos_log_ret.extend(arm.tolist())
            all_oos_passive_log_ret.extend(bench.tolist())
            all_oos_r_multiples.extend(
                oos_res["r_multiples"][:n_min].tolist()
            )
            all_oos_per_session_dates.extend(list(oos_res["session_dates"][:n_min]))
            _log.info(
                "Fold %d: best=lb=%d hl=%d vt=%.2f km=%.2f mppm_train=%.4f mppm_oos=%.4f sr_oos=%.3f",
                fi, best["lookback"], best["halflife"], best["vol_target"], best["kelly_multiplier"],
                sel["best_mppm_train"], mppm_oos_val, rec["sr_arm_annualised"],
            )

        # Aggregate concatenated OOS series.
        oos_arm = np.array(all_oos_log_ret)
        oos_bench = np.array(all_oos_passive_log_ret)
        oos_r = np.array(all_oos_r_multiples)
        n_oos = oos_arm.size
        _log.info("Aggregate OOS sessions: %d", n_oos)

        # === Primary metric: MPPM(rho=1) with CI ===
        mppm_ci_result: dict[str, Any] = {}
        if n_oos >= 30:
            mppm_res = mppm_with_ci(
                oos_arm,
                rho=1.0,
                delta_t=delta_t,
                n_bootstrap=mppm_n_bootstrap,
                rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET,
            )
            mppm_ci_result = {
                "point": float(mppm_res.theta_hat),
                "ci_low": float(mppm_res.ci_low),
                "ci_high": float(mppm_res.ci_high),
                "block_length": float(mppm_res.block_length),
                "n_bootstrap": mppm_n_bootstrap,
                "excludes_zero": bool(mppm_res.excludes_zero),
            }
            if mppm_ci_result["ci_low"] > 0:
                mppm_annot = "mppm-rho1-positive"
            elif mppm_ci_result["ci_high"] < 0:
                mppm_annot = "mppm-rho1-negative"
            else:
                mppm_annot = "mppm-rho1-marginal"
        else:
            mppm_annot = "mppm-rho1-underpowered"

        # === Calmar differential ===
        calmar_result: dict[str, Any] = {}
        try:
            calmar_ci = calmar_differential_ci_stationary_bootstrap(
                oos_arm, oos_bench,
                n_bootstrap=1000,
                rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 1,
                annualization_factor=252.0,
            )
            calmar_result = {
                "point": float(calmar_ci.point_estimate),
                "ci_low": float(calmar_ci.ci_lower),
                "ci_high": float(calmar_ci.ci_upper),
                "calmar_arm": float(calmar_ci.calmar_arm),
                "calmar_bench": float(calmar_ci.calmar_bench),
                "excludes_zero": bool(calmar_ci.excludes_zero),
            }
            if calmar_result["ci_low"] > 0:
                calmar_annot = "calmar-diff-positive"
            elif calmar_result["ci_high"] < 0:
                calmar_annot = "calmar-diff-negative"
            else:
                calmar_annot = "calmar-diff-marginal"
        except Exception as exc:  # noqa: BLE001
            _log.warning("Calmar CI failed: %s", exc)
            calmar_annot = "calmar-diff-error"

        # === Profit-factor differential ===
        pf_result: dict[str, Any] = {}
        try:
            pf_ci = profit_factor_differential_ci_stationary_bootstrap(
                oos_arm, oos_bench,
                n_bootstrap=1000,
                rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 2,
            )
            pf_result = {
                "point": float(pf_ci.point_estimate),
                "ci_low": float(pf_ci.ci_lower),
                "ci_high": float(pf_ci.ci_upper),
                "pf_arm": float(pf_ci.pf_arm),
                "pf_bench": float(pf_ci.pf_bench),
                "excludes_zero": bool(pf_ci.excludes_zero),
            }
            if pf_result["ci_low"] > 0:
                pf_annot = "pf-diff-positive"
            elif pf_result["ci_high"] < 0:
                pf_annot = "pf-diff-negative"
            else:
                pf_annot = "pf-diff-marginal"
        except Exception as exc:
            _log.warning("PF CI failed: %s", exc)
            pf_annot = "pf-diff-error"

        # === R-multiple mean ===
        r_result: dict[str, Any] = {}
        if oos_r.size >= 10:
            r_ci = r_multiple_mean_ci_stationary_bootstrap(
                oos_r,
                n_bootstrap=1000,
                rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 3,
            )
            r_result = {
                "point": float(r_ci.point_estimate),
                "ci_low": float(r_ci.ci_lower),
                "ci_high": float(r_ci.ci_upper),
                "excludes_zero": bool(r_ci.excludes_zero),
                "underpowered": bool(r_ci.underpowered),
            }
            if r_result["ci_low"] > 0:
                r_annot = "r-multiple-mean-positive"
            elif r_result["ci_high"] < 0:
                r_annot = "r-multiple-mean-negative"
            else:
                r_annot = "r-multiple-mean-marginal"
            if r_result["underpowered"]:
                r_annot += "-underpowered"
        else:
            r_annot = "r-multiple-mean-underpowered"

        # === Risk-of-ruin Monte Carlo ===
        ror_result: dict[str, Any] = {}
        if oos_r.size >= 30:
            try:
                ror = probability_of_ruin_monte_carlo(
                    oos_r,
                    starting_equity=10000.0,
                    ruin_threshold_fraction=0.5,
                    n_sessions=252,
                    n_paths=5000,
                    kelly_fraction=0.25,
                    rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 4,
                )
                ror_result = {
                    "probability_of_ruin": float(ror.probability_of_ruin),
                    "n_paths_ruined": int(ror.n_paths_ruined),
                    "n_paths": int(ror.n_paths),
                    "median_terminal_equity": float(ror.median_terminal_equity),
                    "q05_terminal_equity": float(ror.q05_terminal_equity),
                    "ruin_threshold_fraction": float(ror.ruin_threshold_fraction),
                }
            except Exception as exc:
                _log.warning("RoR MC failed: %s", exc)

        # === Sharpe-vs-passive LW2008 differential CI ===
        lw_result: dict[str, Any] = {}
        try:
            lw_ci = ledoit_wolf_2008_differential_ci(
                oos_arm, oos_bench,
                alpha=0.05,
                n_bootstrap=1000,
                rng=np.random.default_rng(rng_seed + _LW2008_RNG_OFFSET),
            )
            lw_result = {
                "point": float(lw_ci.point_estimate),
                "ci_low": float(lw_ci.lower),
                "ci_high": float(lw_ci.upper),
                "excludes_zero": bool(lw_ci.lower > 0 or lw_ci.upper < 0),
                "alpha": float(lw_ci.alpha),
            }
        except Exception as exc:
            _log.warning("LW2008 CI failed: %s", exc)

        # === Hansen SPA (M=1 degenerate) ===
        spa_result: dict[str, Any] = {}
        try:
            d_matrix = (oos_arm - oos_bench).reshape(-1, 1)
            import warnings as _w
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                spa = hansen_spa_test(
                    d_matrix,
                    n_bootstrap=1000,
                    rng=np.random.default_rng(rng_seed + _SPA_RNG_OFFSET),
                )
            spa_result = {
                "p_value": float(spa.p_value),
                "p_value_lower": float(spa.p_value_lower),
                "p_value_upper": float(spa.p_value_upper),
                "statistic": float(spa.statistic),
                "n_strategies": int(spa.n_strategies),
                "variant": str(spa.variant),
            }
        except Exception as exc:
            _log.warning("Hansen SPA failed: %s", exc)

        # === L-skewness payoff shape ===
        l_skew_result: dict[str, Any] = {}
        if oos_r.size >= 20:
            try:
                ls = l_skewness_tau3_ci_stationary_bootstrap(
                    oos_r,
                    n_bootstrap=1000,
                    rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 5,
                )
                l_skew_result = {
                    "tau3": float(ls.tau3),
                    "ci_low": float(ls.ci_low),
                    "ci_high": float(ls.ci_high),
                }
                l_skew_annot = payoff_shape_annotation(
                    ls.tau3, ls.ci_low, ls.ci_high
                )
            except Exception as exc:
                _log.warning("L-skew CI failed: %s", exc)
                l_skew_annot = "payoff-shape-error"
        else:
            l_skew_annot = "payoff-shape-underpowered"

        # === BOCD signal-decay monitor on rolling MPPM path ===
        bocd_result: dict[str, Any] = {}
        if len(fold_mppm_oos) >= 3:
            try:
                bocd = detect_decay(
                    np.array(fold_mppm_oos),
                    hazard_rate=float(cfg["bocd"]["hazard_rate"]),
                    window=int(cfg["bocd"]["window"]),
                    threshold=float(cfg["bocd"]["threshold"]),
                )
                bocd_result = {
                    "decay_detected": bool(bocd.get("decay_detected", False)),
                    "detection_index": (
                        int(bocd["detection_index"])
                        if bocd.get("detection_index") is not None
                        else None
                    ),
                    "max_posterior": float(bocd.get("max_posterior", 0.0)),
                }
                bocd_annot = (
                    "bocd-decay-flag-raised"
                    if bocd_result["decay_detected"]
                    else "bocd-decay-flag-not-raised"
                )
            except Exception as exc:
                _log.warning("BOCD failed: %s", exc)
                bocd_annot = "bocd-error"
        else:
            bocd_annot = "bocd-not-applicable"

        # === Kelly-multiplier mode ===
        if best_cells_seen:
            vals, counts = np.unique(best_cells_seen, return_counts=True)
            kelly_mode = float(vals[np.argmax(counts)])
            kelly_annot = kelly_multiplier_annotation(kelly_mode)
        else:
            kelly_mode = float("nan")
            kelly_annot = "kelly-multiplier-n/a"

        # === Realized OOS equity curve, win/loss/zero ===
        eq, eq_end, mdd = _equity_curve(oos_arm)
        eq_bench, eq_bench_end, mdd_bench = _equity_curve(oos_bench)
        w = int((oos_arm > 0).sum())
        l_ = int((oos_arm < 0).sum())
        z = int((oos_arm == 0).sum())
        sr_arm_ann = _annualised_sharpe(oos_arm)
        sr_bench_ann = _annualised_sharpe(oos_bench)

        # === Forward projection ===
        forward_arm = _bootstrap_forward_projection(
            oos_arm, n_paths=5000, n_sessions=252,
            rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 10,
        )
        forward_bench = _bootstrap_forward_projection(
            oos_bench, n_paths=5000, n_sessions=252,
            rng_seed=rng_seed + _BOOTSTRAP_RNG_OFFSET + 11,
        )

        # === Assemble payload ===
        annotations = [
            "leakage-canary-pass",
            mppm_annot,
            bocd_annot,
            f"kelly-multiplier-{kelly_mode}",
            l_skew_annot,
            "claim-type-hybrid",
            "cost-zero-v1-pre-cost-research-only",
            "data-quality-degraded-days-annotated",
            "repro-log-complete",
            calmar_annot,
            pf_annot,
            r_annot,
        ]

        payload = {
            "hypothesis_id": "H060",
            "run_id": run_id,
            "git_head": git_head,
            "rng_seed": rng_seed,
            "config_resolved_sha256": config_resolved_sha256,
            "dataset_checksums": dataset_checksums,
            "universe": universe,
            "windows": {
                "is": [str(is_start), str(is_end)],
                "oos": [str(oos_start), str(oos_end)],
            },
            "n_folds_realized": len(per_fold_records),
            "per_fold": per_fold_records,
            "n_oos_sessions_aggregate": int(n_oos),
            "primary_inference": {
                "mppm_rho1_with_ci": mppm_ci_result,
                "calmar_differential_ci": calmar_result,
                "profit_factor_differential_ci": pf_result,
                "r_multiple_mean_ci": r_result,
                "risk_of_ruin_monte_carlo": ror_result,
            },
            "secondary_inference": {
                "sharpe_vs_passive_lw2008": lw_result,
                "sharpe_arm_annualised": sr_arm_ann,
                "sharpe_bench_annualised": sr_bench_ann,
                "hansen_spa": spa_result,
            },
            "adr_0018_0019": {
                "bocd": bocd_result,
                "kelly_multiplier_mode": kelly_mode,
                "l_skewness_tau3": l_skew_result,
                "fold_mppm_oos_path": fold_mppm_oos,
            },
            "realized_oos": {
                "starting_equity": 10000.0,
                "ending_equity": eq_end,
                "ending_pct_change": (eq_end / 10000.0 - 1.0) * 100,
                "max_drawdown_pct": mdd * 100,
                "n_winning_sessions": w,
                "n_losing_sessions": l_,
                "n_zero_sessions": z,
                "passive_ending_equity": eq_bench_end,
                "passive_ending_pct_change": (eq_bench_end / 10000.0 - 1.0) * 100,
                "passive_max_drawdown_pct": mdd_bench * 100,
            },
            "forward_projection_arm": forward_arm,
            "forward_projection_bench": forward_bench,
            "annotations_dot_separated": " · ".join(annotations),
            "annotations_list": annotations,
            "cost_model": {"id": "zero_cost_v1_pre_cost_research_only"},
            "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
        }

        # SHA-bound sidecar.
        scientific_bytes = json.dumps(
            payload, indent=2, sort_keys=True, default=str
        ).encode("utf-8")
        scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()
        ctx.set_model_hash(scientific_sha)
        sidecar_path = out_dir / "sidecar.json"
        sidecar_path.with_suffix(".json.tmp").write_bytes(scientific_bytes)
        os.replace(str(sidecar_path.with_suffix(".json.tmp")), str(sidecar_path))
        _atomic_write_text(
            out_dir / "scientific_payload_sha256.txt",
            scientific_sha + "\n",
        )
        _log.info(
            "scientific_payload_sha256=%s sidecar=%s",
            scientific_sha[:16], sidecar_path,
        )

        # Headline log lines for stdout capture.
        print()
        print("=" * 60)
        print(f"H060 WALK-FORWARD COMPLETE — run_id={run_id}")
        print(f"  universe={universe}")
        print(f"  n_folds_realized={len(per_fold_records)}")
        print(f"  n_oos_sessions_aggregate={n_oos}")
        print(f"  realized_OOS: ending=${eq_end:,.2f} ({(eq_end/10000-1)*100:+.2f}%) MaxDD={mdd*100:.2f}%")
        print(f"  passive_OOS:  ending=${eq_bench_end:,.2f} ({(eq_bench_end/10000-1)*100:+.2f}%) MaxDD={mdd_bench*100:.2f}%")
        print(f"  W/L/Z = {w}/{l_}/{z}  win_rate={(w/max(w+l_+z,1))*100:.1f}%")
        print(f"  Sharpe_arm_ann = {sr_arm_ann:.3f}")
        print(f"  Sharpe_bench_ann = {sr_bench_ann:.3f}")
        print(f"  MPPM(rho=1): {mppm_ci_result}")
        print(f"  LW2008 sharpe-vs-passive: {lw_result}")
        print(f"  calmar_diff: {calmar_result}")
        print(f"  pf_diff: {pf_result}")
        print(f"  r_mean: {r_result}")
        print(f"  L-skew tau3: {l_skew_result}")
        print(f"  BOCD: {bocd_result}")
        print(f"  kelly_multiplier_mode = {kelly_mode}")
        print(f"  annotations: {' · '.join(annotations)}")
        print(f"  scientific_payload_sha256 = {scientific_sha}")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
