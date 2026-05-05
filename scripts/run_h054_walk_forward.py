"""H054 walk-forward orchestrator (Stage-3).

Per H054 frozen pre-reg [research/01_hypothesis_register/H054/design.md](
../research/01_hypothesis_register/H054/design.md) — anti-gate first-hour
ORB on CME ES futures. Status: designed 2026-05-05 (Round-2+3 audit-
remediate-loop ACCEPT closing 5 critical/major + 5 minor R1 findings).

Distinguishing features vs H052a orchestrator:
- ES-only at v1 (NQ excluded per F-Q-6 design-time-knowledge fix)
- IS = 2020-01-01 -> 2023-06-30 (matches H052a IS+val EXACTLY per F-Q-1)
- OOS test = 2025-01-01 -> 2025-12-03 (fresh; ES-only)
- Stress-state identification: argmax of mu_rv (top-1 only; tie-break via
  lowest canonical state-index per F-Q-3 fix; design.md §5)
- Anti-gate trading rule: trade ORB on stress-state sessions ONLY
- PRIMARY test statistic T_H054_b = SR_anti_gated (univariate; absolute
  profitability standalone per F-Q-2 fix)
- SECONDARY informational T_H054_a = SR_anti_gated - SR_unconditional

Pipeline
--------

1. Open :class:`~skie_ninja.utils.runcontext.RunContext`; bind
   git_head + dataset_checksum + rng_seed.
2. Load roll-adjusted 1-min RTH+ETH ES/NQ substrate; load VIX daily.
3. Per (symbol, session): compute H052a HMM emission features per
   :func:`~skie_ninja.features.h052a.features.compute_h052a_features`
   (realized_vol, first_hour_sign, gap_size, dow_onehot, eth_pre_rth,
   vix_daily) at the 10:30 ET entry timestamp.
4. Per cfg in the 27-cell label grid (``pt_mult × sl_mult × vol_lookback``):
   compute UNCONDITIONAL ORB labels via
   :class:`~skie_ninja.features.labels.OpeningRangeBreakoutLabeller`.
5. Calendar-based train/test split per design.md §2:
   - Train: 2020-01-01 → 2022-12-31
   - Test:  2023-07-01 → 2024-12-31 (with val 2023-01-01 → 2023-06-30 as
     inner CV fold).
6. Inner CV on training fold: select best label cfg by SR_unconditional.
7. Fit Gaussian HMM on training-fold features (BIC + CV-LL selection per
   ADR-0005). Compute posterior at each test-fold session's 10:30 ET via
   the causal forward filter (`filter_states_from_prior` per ADR-0005).
8. Compute T_H054_b = SR_anti_gated (PRIMARY) on test fold via Opdyke 2007
   univariate Sharpe CI; T_H054_a = SR_anti_gated − SR_unconditional
   (SECONDARY) via LW2008 differential CI + Hansen SPA (M=1 degenerate
   per ADR-0008 + F-Q-5 fix).
9. Cost-aware per-session log-return drag via
   :class:`~skie_ninja.backtest.costs.futures_orb_v1.FuturesOrbV1CostModel`
   per design.md §7 + ADR-0013 §3.1 (F-CONV-2 log-return-drag rule).
10. Bootstrap forward projection (5,000 paths × 252 sessions; PW2004
    block-length on per-session strategy log returns) per ADR-0013 §3.1.
11. Write per-symbol metrics_summary.json + run-level scientific_payload
    SHA-bound to ReproLog model_hash per H050 F-R-1 + F-R-6 fixes.
12. Emit aggregate sidecar with §3.2 9-table summary inputs for the KPI
    report card writer.

Per ADR-0014 §3.2: every KPI report card MUST include a 9-table summary;
this orchestrator emits the per-symbol values consumed by that writer.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent  # paths-guard: allow (script-bootstrap)
_SRC_DIR = _REPO_ROOT / "src"  # paths-guard: allow (script-bootstrap)
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import polars as pl
import yaml

from skie_ninja.backtest.costs.futures_orb_v1 import FuturesOrbV1CostModel
from skie_ninja.data.ingest.vix_daily import load_vix_daily
from skie_ninja.features.h052a import compute_h052a_features
from skie_ninja.features.labels import (
    OpeningRangeBreakoutConfig,
    OpeningRangeBreakoutLabeller,
)
from skie_ninja.inference import choose_block_length, hansen_spa_test
from skie_ninja.inference.bootstrap import stationary_bootstrap_indices
from skie_ninja.inference.stats.ledoit_wolf_2008 import (
    ledoit_wolf_2008_differential_ci,
)
from skie_ninja.inference.stats.sharpe_ci import opdyke2007_ci
from skie_ninja.models.regime import GaussianHMM, select_gaussian_hmm
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.runcontext import RunContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h054_walk_forward")


_PROJECTION_N_PATHS: int = 5_000
_PROJECTION_N_SESSIONS: int = 252  # per ADR-0013 §3.1
_RNG_SEED_DEFAULT: int = 20260505  # design.md §11; justify: design-date YYYYMMDD per F-Q-8
# RNG offsets for downstream stochastic primitives. Per ADR-0013 §3.1
# "single rng_seed across all arms × symbols": all symbols + arms within a
# given primitive share the same seed; offsets disambiguate between
# primitives only.
_LW2008_RNG_OFFSET: int = 100
_SPA_RNG_OFFSET: int = 200
_BOOTSTRAP_RNG_OFFSET: int = 1000

# Sample-size floors for HMM fit + test inference. Per ADR-0005 adaptive-rule
# binding "mean within-state N > 30 · dim", a 9-feature 2-state HMM needs at
# least ~540 training observations to satisfy the dim-floor with both states
# populated; we use 60 sessions as a conservative lower bound (sufficient for
# d=9, n_states=2 only with multi-restart; raises if violated).
# # justify: ADR-0005 dim-floor with 2-state minimum + 5-restart cap on a
# 9-dim feature vector. Test floor 30 sessions: minimum sample for the
# annualised Sharpe estimator to be informative under Lo 2002 §3 (q=30 → 18%
# residual bias).
_MIN_TRAIN_SESSIONS: int = 60
_MIN_TEST_SESSIONS: int = 30


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


def _resolve_substrate_path(cli_arg: str | None, project_root: Path) -> Path:
    if cli_arg:
        path = Path(cli_arg).resolve()
    else:
        path = project_root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"
    if not path.exists():
        raise FileNotFoundError(f"Substrate path not found: {path}")
    return path


def _filter_rth(panel: pl.DataFrame, time_col: str = "ts_event") -> pl.DataFrame:
    """Filter to RTH-only (09:30-16:00 ET) per H052a design.md §2."""
    df = panel.to_pandas()
    ts_utc = pd.to_datetime(df[time_col])
    if ts_utc.dt.tz is None:
        ts_utc = ts_utc.dt.tz_localize("UTC")
    ts_et = ts_utc.dt.tz_convert("America/New_York")
    tod = ts_et.dt.strftime("%H:%M")
    mask = (tod >= "09:30") & (tod < "16:00")
    return pl.from_pandas(df.loc[mask].reset_index(drop=True))


def _atomic_write_text(path: Path, text: str) -> None:
    """Write text to ``path`` atomically via temp-file + ``os.replace``.

    Mirrors the H050 F-R-5 (Round-2 audit-remediate-loop 2026-05-03) helper.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


def _walk_forward_inner_cv_folds(
    sessions_df: pd.DataFrame,
    *,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    n_folds: int = 3,
    purge_sessions: int = 1,
    embargo_sessions: int = 1,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Build inner walk-forward CV folds at session cadence over the train
    window per H052a design.md §6 + F-Q-5 fix (Round-2 audit-remediate-loop).

    Returns list of (inner_train_local_idx, inner_val_local_idx) tuples
    where indices are positions into ``sessions_df`` filtered to the train
    window. Mirrors the H050 walk_forward_split pattern at session cadence.

    Per AFML §7.4: purge = label-horizon (1 session for H052a daily-cleared);
    embargo = AFML §7.4.2 small-percentage (≈1 session at this cadence).
    """
    sd = sessions_df["session_date_et"].to_pandas()
    if sd.dt.tz is None:
        sd = sd.dt.tz_localize("UTC")
    train_mask = ((sd >= train_start) & (sd <= train_end)).to_numpy()
    train_local = np.flatnonzero(train_mask)
    n_train = train_local.size
    if n_train < (n_folds + 1) * 4:
        return []
    val_size = n_train // (n_folds + 2)
    initial_train = max(val_size, n_train - n_folds * val_size)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for k in range(n_folds):
        train_end_pos = initial_train + k * val_size
        val_start_pos = train_end_pos + purge_sessions + embargo_sessions
        val_end_pos = val_start_pos + val_size
        if val_end_pos > n_train:
            break
        inner_tr = train_local[:train_end_pos]
        inner_val = train_local[val_start_pos:val_end_pos]
        if inner_tr.size > 0 and inner_val.size > 0:
            folds.append((inner_tr, inner_val))
    return folds


def _calendar_split(
    sessions_df: pl.DataFrame,
    *,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    val_start: pd.Timestamp,
    val_end: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calendar-based train/val/test split mask on session_date_et.

    Returns (train_mask, val_mask, test_mask) as boolean numpy arrays.
    """
    sd = sessions_df["session_date_et"].to_pandas()
    if sd.dt.tz is None:
        sd = sd.dt.tz_localize("UTC")
    train = ((sd >= train_start) & (sd <= train_end)).to_numpy()
    val = ((sd >= val_start) & (sd <= val_end)).to_numpy()
    test = ((sd >= test_start) & (sd <= test_end)).to_numpy()
    return train, val, test


def _per_session_strategy_returns(
    *,
    pnl_log: np.ndarray,
    gate: np.ndarray | None,
    cost_log_drag: np.ndarray,
) -> np.ndarray:
    """Apply gate + cost to per-session log returns.

    - If `gate` is None: unconditional (all sessions traded).
    - If `gate[i] == 1`: trade session i; pnl = pnl_log[i] + cost_log_drag[i] (negative).
    - If `gate[i] == 0`: skip session i; pnl = 0.
    """
    if gate is None:
        return pnl_log + cost_log_drag
    out = np.zeros_like(pnl_log)
    out[gate == 1] = pnl_log[gate == 1] + cost_log_drag[gate == 1]
    return out


def _annualised_sharpe(returns: np.ndarray) -> float:
    """Annualised Sharpe of per-session log-returns (×√252)."""
    if returns.size < 2:
        return float("nan")
    sd = float(returns.std(ddof=1))
    if sd <= 0:
        return float("nan")
    return float(returns.mean() / sd * np.sqrt(252.0))


def _max_drawdown(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    return float(abs(dd.min())) if dd.size > 0 else 0.0


def _equity_curve(log_returns: np.ndarray, starting: float = 10_000.0) -> tuple[np.ndarray, float, float]:
    cumlog = np.concatenate([[0.0], np.cumsum(log_returns)])
    equity = starting * np.exp(cumlog)
    return equity, float(equity[-1]), _max_drawdown(equity)


def _bootstrap_forward_projection(
    log_returns: np.ndarray,
    *,
    n_paths: int,
    n_sessions: int,
    rng_seed: int,
) -> dict[str, Any]:
    """Per-session bootstrap projection over n_sessions.

    PW2004 block-length on the LEVEL series; iid if b≤1, else stationary
    bootstrap (Politis-Romano 1994).
    """
    rng = np.random.default_rng(rng_seed)
    if log_returns.size == 0:
        return {"n_paths": 0, "ending_equity": {}, "max_drawdown": {}}
    block_length_selection = choose_block_length(log_returns)
    selected_b = float(block_length_selection.block_length)
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


def _process_symbol(
    *,
    symbol: str,
    panel_sym: pl.DataFrame,
    vix_daily_pdf: pd.DataFrame,
    cfg: dict[str, Any],
    rng_seed: int,
    cost_model: FuturesOrbV1CostModel,
) -> dict[str, Any]:
    _log.info("[%s] starting", symbol)
    # F-Q-3 fix (Round-2 2026-05-04 critical): compute features on the FULL
    # panel (RTH + ETH) so eth_pre_rth has 06:00-09:29 ET ETH bars; filter to
    # RTH only when invoking the labeller (which expects 09:30-16:00 ET).
    full_panel = panel_sym
    rth_panel = _filter_rth(panel_sym)

    train_start = pd.Timestamp(cfg["data"]["train"]["start"], tz="UTC")
    train_end = pd.Timestamp(cfg["data"]["train"]["end"], tz="UTC") + pd.Timedelta(
        days=1
    ) - pd.Timedelta(nanoseconds=1)
    val_start = pd.Timestamp(cfg["data"]["val"]["start"], tz="UTC")
    val_end = pd.Timestamp(cfg["data"]["val"]["end"], tz="UTC") + pd.Timedelta(
        days=1
    ) - pd.Timedelta(nanoseconds=1)
    test_start = pd.Timestamp(cfg["data"]["test"]["start"], tz="UTC")
    test_end = pd.Timestamp(cfg["data"]["test"]["end"], tz="UTC") + pd.Timedelta(
        days=1
    ) - pd.Timedelta(nanoseconds=1)

    # F-Q-5 fix (Round-2 2026-05-04 major): walk-forward inner CV across the
    # train window (3 folds, purge=embargo=1 session per design.md §6 + AFML
    # §7.4.2). Replaces the prior single-val-split inner CV which was flagged
    # as a F-2-2 leakage-class analog (KFold-shuffle / single-realized-fold
    # selection on n≈125 sessions).
    pt_grid = cfg["labels"]["pt_mult_grid"]
    sl_grid = cfg["labels"]["sl_mult_grid"]
    vl_grid = cfg["labels"]["realized_vol_lookback_minutes_grid"]

    best_cfg: tuple[float, float, int] | None = None
    best_inner_sharpe = -float("inf")
    label_grid_log: list[dict[str, Any]] = []

    for pt in pt_grid:
        for sl in sl_grid:
            for vl in vl_grid:
                orb_cfg = OpeningRangeBreakoutConfig(
                    pt_mult=float(pt),
                    sl_mult=float(sl),
                    realized_vol_lookback_minutes=int(vl),
                    entry_time_et=cfg["labels"]["entry_time_et"],
                    time_stop_et=cfg["labels"]["time_stop_et"],
                    hard_close_et=cfg["labels"]["hard_close_et"],
                )
                labeller = OpeningRangeBreakoutLabeller(orb_cfg)
                labels = labeller.apply(rth_panel)
                if labels.height == 0:
                    continue
                lab_pdf = labels.to_pandas()
                lab_pdf["session_date_et"] = pd.to_datetime(
                    lab_pdf["session_date_et"]
                )
                if lab_pdf["session_date_et"].dt.tz is None:
                    lab_pdf["session_date_et"] = lab_pdf[
                        "session_date_et"
                    ].dt.tz_localize("UTC")
                lab_pdf = lab_pdf.sort_values("session_date_et").reset_index(drop=True)
                # Restrict to train window for inner CV.
                in_train = (
                    (lab_pdf["session_date_et"] >= train_start)
                    & (lab_pdf["session_date_et"] <= train_end)
                ).to_numpy()
                train_pdf = lab_pdf[in_train].reset_index(drop=True)
                folds = _walk_forward_inner_cv_folds(
                    pl.from_pandas(train_pdf),
                    train_start=train_start,
                    train_end=train_end,
                    n_folds=3,
                    purge_sessions=1,
                    embargo_sessions=1,
                )
                if not folds:
                    continue
                fold_srs: list[float] = []
                for _inner_tr_idx, inner_val_idx in folds:
                    val_returns = train_pdf.iloc[inner_val_idx]["pnl_log"].to_numpy()
                    val_entry_prices = train_pdf.iloc[inner_val_idx][
                        "entry_price"
                    ].to_numpy()
                    val_costs = np.array(
                        [
                            cost_model.cost_per_session_log_return(
                                symbol=symbol, entry_price=float(ep), n_contracts=1,
                            )
                            if np.isfinite(ep) and ep > 0
                            else 0.0
                            for ep in val_entry_prices
                        ]
                    )
                    val_net = val_returns + val_costs
                    fold_sr = _annualised_sharpe(val_net)
                    if np.isfinite(fold_sr):
                        fold_srs.append(float(fold_sr))
                if not fold_srs:
                    continue
                inner_sr = float(np.mean(fold_srs))
                label_grid_log.append(
                    {
                        "pt_mult": float(pt),
                        "sl_mult": float(sl),
                        "realized_vol_lookback_minutes": int(vl),
                        "n_inner_folds": len(folds),
                        "inner_cv_sharpe_unconditional_mean_across_folds": inner_sr,
                        "inner_cv_sharpe_unconditional_per_fold": fold_srs,
                    }
                )
                if inner_sr > best_inner_sharpe:
                    best_inner_sharpe = inner_sr
                    best_cfg = (float(pt), float(sl), int(vl))

    if best_cfg is None:
        _log.warning("[%s] no usable label cfg; aborting", symbol)
        return {
            "symbol": symbol,
            "status": "no_usable_label_cfg",
            "label_grid_log": label_grid_log,
        }
    pt_best, sl_best, vl_best = best_cfg
    _log.info(
        "[%s] best cfg: pt=%.2f sl=%.2f vol_lookback=%dm; inner-CV mean SR=%.4f",
        symbol, pt_best, sl_best, vl_best, best_inner_sharpe,
    )

    # Re-compute labels at best cfg over the RTH-filtered panel.
    orb_cfg_best = OpeningRangeBreakoutConfig(
        pt_mult=pt_best,
        sl_mult=sl_best,
        realized_vol_lookback_minutes=vl_best,
        entry_time_et=cfg["labels"]["entry_time_et"],
        time_stop_et=cfg["labels"]["time_stop_et"],
        hard_close_et=cfg["labels"]["hard_close_et"],
    )
    labeller_best = OpeningRangeBreakoutLabeller(orb_cfg_best)
    labels_best = labeller_best.apply(rth_panel)

    # F-Q-3 fix: compute features on FULL panel (RTH + ETH) so eth_pre_rth
    # has 06:00-09:29 ET ETH bars. The labeller's inner workings only needed
    # 09:30-16:00 ET RTH bars; the feature factory uses ETH for one feature.
    feature_panel = compute_h052a_features(
        full_panel,
        realized_vol_lookback_minutes=vl_best,
        vix_daily=vix_daily_pdf,
    )

    # Normalise session_date_et precision (post-stall fix #3 2026-05-05):
    # labeller output is μs precision; feature_panel is ns precision.
    # Polars `join` refuses cross-precision joins → cast both to ns first.
    _norm = pl.col("session_date_et").cast(pl.Datetime("ns", "UTC"))
    labels_best = labels_best.with_columns(_norm)
    feature_panel = feature_panel.with_columns(_norm)
    joined = labels_best.join(
        feature_panel, on=["symbol", "session_date_et"], how="inner"
    )
    j_pdf = joined.to_pandas()
    if j_pdf["session_date_et"].dt.tz is None:
        j_pdf["session_date_et"] = j_pdf["session_date_et"].dt.tz_localize("UTC")
    j_pdf = j_pdf.sort_values("session_date_et").reset_index(drop=True)

    # Train/test masks.
    train_mask = (
        (j_pdf["session_date_et"] >= train_start)
        & (j_pdf["session_date_et"] <= train_end)
    ).to_numpy()
    test_mask = (
        (j_pdf["session_date_et"] >= test_start)
        & (j_pdf["session_date_et"] <= test_end)
    ).to_numpy()

    feature_cols = [
        "realized_vol",
        "first_hour_sign",
        "gap_size",
        "dow_mon",
        "dow_tue",
        "dow_wed",
        "dow_thu",
        "eth_pre_rth",
        "vix_daily",
    ]
    X_full = j_pdf[feature_cols].to_numpy().astype(np.float64)
    y_pnl = j_pdf["pnl_log"].to_numpy().astype(np.float64)
    entry_price = j_pdf["entry_price"].to_numpy().astype(np.float64)

    # F-Q-8 fix (Round-2 2026-05-04 major): log NaN-drop counts per feature
    # column so calendar-asymmetric loss is auditable.
    nan_drop_per_col = {
        col: int(np.sum(~np.isfinite(j_pdf[col].to_numpy())))
        for col in feature_cols
    }
    nan_drop_pnl = int(np.sum(~np.isfinite(y_pnl)))
    nan_drop_entry = int(np.sum(~np.isfinite(entry_price)))
    finite_mask = np.isfinite(X_full).all(axis=1) & np.isfinite(y_pnl) & np.isfinite(entry_price)
    train_idx = np.flatnonzero(train_mask & finite_mask)
    test_idx = np.flatnonzero(test_mask & finite_mask)
    _log.info(
        "[%s] sessions: train=%d test=%d (after NaN-drop; nan_drop_per_col=%s; "
        "nan_drop_pnl=%d nan_drop_entry=%d)",
        symbol, train_idx.size, test_idx.size, nan_drop_per_col, nan_drop_pnl,
        nan_drop_entry,
    )
    # F-Q-9 fix: thresholds hoisted to module-level constants with justify.
    if train_idx.size < _MIN_TRAIN_SESSIONS or test_idx.size < _MIN_TEST_SESSIONS:
        _log.warning(
            "[%s] insufficient sessions for HMM fit + test inference; aborting "
            "(thresholds: train >= %d, test >= %d)",
            symbol, _MIN_TRAIN_SESSIONS, _MIN_TEST_SESSIONS,
        )
        return {
            "symbol": symbol,
            "status": "insufficient_sessions",
            "n_train": int(train_idx.size),
            "n_test": int(test_idx.size),
            "min_train_required": _MIN_TRAIN_SESSIONS,
            "min_test_required": _MIN_TEST_SESSIONS,
            "nan_drop_per_col": nan_drop_per_col,
            "best_label_cfg": {
                "pt_mult": pt_best, "sl_mult": sl_best,
                "realized_vol_lookback_minutes": vl_best,
            },
        }

    # Cost-aware per-session log-return drag.
    cost_log_drag = np.zeros_like(y_pnl)
    for i, ep in enumerate(entry_price):
        if np.isfinite(ep) and ep > 0:
            cost_log_drag[i] = cost_model.cost_per_session_log_return(
                symbol=symbol, entry_price=float(ep), n_contracts=1
            )

    # Fit HMM on training fold.
    X_train = X_full[train_idx]
    selection = select_gaussian_hmm(
        X_train,
        n_states_grid=tuple(cfg["hmm"]["n_states_grid"]),
        covariance_types=tuple(cfg["hmm"]["covariance_type"]),
        seed=int(rng_seed),
        min_restarts=5,
        max_restarts=10,
    )
    hmm: GaussianHMM = selection.best_model

    # H054 stress-state identification rule per design.md §5 (Round-2 audit
    # F-Q-3 fix): top-1 only, single-feature (realized_vol) dominance,
    # tie-breaking via lowest canonical state-index when |delta_mu_rv| < 1e-9
    # (Biernacki-Celeux-Govaert 2000 PAMI 22(7) label-switch canonicalisation
    # per ADR-0005). The "stress state" is the state with the HIGHEST mean
    # realized_vol emission — the H054-distinctive inversion of H052a.
    means = hmm.params_.means
    rv_col_idx = feature_cols.index("realized_vol")
    rv_means = means[:, rv_col_idx]
    # Argmax with explicit tie-break (np.argmax returns lowest-index on ties
    # by default which matches the F-Q-3 rule, but make it explicit).
    max_rv = float(np.max(rv_means))
    tie_mask = np.abs(rv_means - max_rv) < 1e-9
    stress_state = int(np.where(tie_mask)[0].min())
    _log.info(
        "[%s] HMM stress_state=%d (highest realized_vol emission mean per "
        "H054 design.md §5 stress-state identification rule, top-1 only, "
        "tie-break lowest-state-index)",
        symbol, stress_state,
    )

    # Apply ADR-0005-mandated causal warm-start forward filter to test fold,
    # propagating the train-terminal posterior (carried forward from H052a
    # F-Q-4 fix).
    X_test = X_full[test_idx]
    log_alpha_prior = hmm.terminal_log_alpha(X_train)
    n_propagation_steps = max(0, int(test_idx[0]) - int(train_idx[-1]) - 1)
    posteriors_test = hmm.filter_states_from_prior(
        X_test, log_alpha_prior, n_propagation_steps=n_propagation_steps,
    )
    state_test = posteriors_test.argmax(axis=1)
    # H054-distinctive: anti_gate fires on the STRESS state (the H052a-gated-
    # OUT sessions). This is the inverse of H052a's gate.
    anti_gate_test = (state_test == stress_state).astype(np.int64)

    # Per-session strategy returns on test fold.
    test_pnl = y_pnl[test_idx]
    test_cost = cost_log_drag[test_idx]
    uncond_returns = _per_session_strategy_returns(
        pnl_log=test_pnl, gate=None, cost_log_drag=test_cost,
    )
    anti_gated_returns = _per_session_strategy_returns(
        pnl_log=test_pnl, gate=anti_gate_test, cost_log_drag=test_cost,
    )

    # Sharpes (annualised x sqrt(252) per ADR-0013 §3.1.1 daily-cleared
    # session-cadence convention).
    sr_uncond = _annualised_sharpe(uncond_returns)
    sr_anti_gated = _annualised_sharpe(anti_gated_returns)
    t_h054_a = sr_anti_gated - sr_uncond  # SECONDARY informational
    # T_H054_b = SR_anti_gated is the PRIMARY inferential statistic per
    # design.md §1 (Round-2 F-Q-2 fix); evaluated below via Opdyke 2007
    # univariate Sharpe CI.

    # PRIMARY inference: T_H054_b = SR_anti_gated. Univariate Sharpe CI on the
    # anti-gated arm via Opdyke 2007 Mertens-HAC primary channel per
    # rules/quant-project.md + ADR-0008 single-strategy degenerate at v1.
    # H_0: SR_anti_gated <= 0; CI excluding zero on positive side supports H_1.
    try:
        opdyke_ci = opdyke2007_ci(
            anti_gated_returns,
            confidence_level=1.0 - cfg["gates"]["ledoit_wolf_2008_univariate_ci"]["alpha"],
            hac_adjust=True,
            bandwidth=None,
        )
        opdyke_lower = float(opdyke_ci.lower)
        opdyke_upper = float(opdyke_ci.upper)
        opdyke_point = float(opdyke_ci.sharpe)  # SharpeCI.sharpe = point estimate
    except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
        _log.warning("[%s] Opdyke 2007 univariate CI failed: %s", symbol, exc)
        opdyke_lower = float("nan")
        opdyke_upper = float("nan")
        opdyke_point = float(sr_anti_gated)

    # SECONDARY informational: T_H054_a = SR_anti_gated - SR_unconditional.
    # LW2008 differential CI per H052a F-Q-2 carry-forward.
    rng_lw = np.random.default_rng(int(rng_seed) + _LW2008_RNG_OFFSET)
    try:
        lw_ci = ledoit_wolf_2008_differential_ci(
            returns_a=anti_gated_returns,
            returns_b=uncond_returns,
            alpha=cfg["gates"]["ledoit_wolf_2008_differential_ci"]["alpha"],
            n_bootstrap=cfg["gates"]["ledoit_wolf_2008_differential_ci"]["n_bootstrap"],
            block_length=None,
            bandwidth=None,
            bandwidth_strategy=cfg["gates"]["ledoit_wolf_2008_differential_ci"][
                "bandwidth_strategy"
            ],
            rng=rng_lw,
        )
        lw_lower = float(lw_ci.lower)
        lw_upper = float(lw_ci.upper)
        lw_point = float(lw_ci.point_estimate)
    except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
        _log.warning("[%s] LW2008 differential CI failed: %s", symbol, exc)
        lw_lower = float("nan")
        lw_upper = float("nan")
        lw_point = t_h054_a

    # Hansen SPA M=1 degenerate per ADR-0008 (carry-forward H052a F-Q-1 API
    # fix). The relative-performance matrix is `(anti_gated - uncond)` per
    # the secondary T_H054_a framing.
    rng_spa = np.random.default_rng(int(rng_seed) + _SPA_RNG_OFFSET)
    d_matrix = (anti_gated_returns - uncond_returns).reshape(-1, 1)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spa = hansen_spa_test(
                d_matrix,
                n_bootstrap=cfg["gates"]["hansen_spa"]["n_bootstrap"],
                variant=cfg["gates"]["hansen_spa"].get("variant", "consistent"),
                omega_method=cfg["gates"]["hansen_spa"]["omega_method"],
                rng=rng_spa,
            )
        spa_p = float(spa.p_value)
        spa_stat = float(spa.statistic)
    except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
        _log.warning("[%s] Hansen SPA failed: %s", symbol, exc)
        spa_p = float("nan")
        spa_stat = float("nan")

    # Realized OOS equity curves.
    eq_uncond, eq_uncond_end, mdd_uncond = _equity_curve(uncond_returns)
    eq_anti, eq_anti_end, mdd_anti = _equity_curve(anti_gated_returns)

    # W/L/Z counts.
    def _wlz(r: np.ndarray) -> tuple[int, int, int]:
        return int((r > 0).sum()), int((r < 0).sum()), int((r == 0).sum())

    w_u, l_u, z_u = _wlz(uncond_returns)
    w_a, l_a, z_a = _wlz(anti_gated_returns)

    # Anti-gate trade counts (number of sessions where anti_gate fires =
    # actual entries; the "n_zero_sessions" above counts both zero-PnL trades
    # AND no-trade gated-out sessions, so report n_anti_trades separately for
    # power-margin analysis).
    n_anti_trades = int(anti_gate_test.sum())
    n_anti_no_trade = int((1 - anti_gate_test).sum())

    # Forward 1-yr projection.
    proj_uncond = _bootstrap_forward_projection(
        uncond_returns,
        n_paths=_PROJECTION_N_PATHS,
        n_sessions=_PROJECTION_N_SESSIONS,
        rng_seed=int(rng_seed) + _BOOTSTRAP_RNG_OFFSET,
    )
    proj_anti = _bootstrap_forward_projection(
        anti_gated_returns,
        n_paths=_PROJECTION_N_PATHS,
        n_sessions=_PROJECTION_N_SESSIONS,
        rng_seed=int(rng_seed) + _BOOTSTRAP_RNG_OFFSET,
    )

    return {
        "symbol": symbol,
        "status": "ok",
        "best_label_cfg": {
            "pt_mult": pt_best, "sl_mult": sl_best,
            "realized_vol_lookback_minutes": vl_best,
        },
        "label_grid_log": label_grid_log,
        "n_train_sessions": int(train_idx.size),
        "n_test_sessions": int(test_idx.size),
        "hmm": {
            "n_states": int(hmm.params_.n_states()),
            "covariance_type": str(hmm.params_.covariance_type),
            "stress_state": int(stress_state),
            "selected_n_states": int(selection.best_n_states),
            "selected_covariance_type": str(selection.best_covariance_type),
            "n_anti_trades": n_anti_trades,
            "n_anti_no_trade": n_anti_no_trade,
        },
        "performance": {
            "annualised_sharpe_unconditional": float(sr_uncond) if np.isfinite(sr_uncond) else None,
            "annualised_sharpe_anti_gated": float(sr_anti_gated) if np.isfinite(sr_anti_gated) else None,
            "t_h054_b_primary": {
                "test_statistic": "SR_anti_gated",
                "annualised_sharpe": float(sr_anti_gated) if np.isfinite(sr_anti_gated) else None,
                "opdyke2007_ci": {
                    "point_estimate": opdyke_point,
                    "lower": opdyke_lower,
                    "upper": opdyke_upper,
                    "alpha": cfg["gates"]["ledoit_wolf_2008_univariate_ci"]["alpha"],
                    "method": "opdyke2007_mertens_hac_approx",
                },
            },
            "t_h054_a_secondary": {
                "test_statistic": "SR_anti_gated - SR_unconditional",
                "annualised": float(t_h054_a) if np.isfinite(t_h054_a) else None,
                "lw2008_differential_ci": {
                    "point_estimate": lw_point,
                    "lower": lw_lower,
                    "upper": lw_upper,
                    "alpha": cfg["gates"]["ledoit_wolf_2008_differential_ci"]["alpha"],
                    "n_bootstrap": cfg["gates"]["ledoit_wolf_2008_differential_ci"]["n_bootstrap"],
                },
            },
            "hansen_spa_secondary_m1_degenerate": {
                "p_value": spa_p,
                "statistic": spa_stat,
                "n_bootstrap": cfg["gates"]["hansen_spa"]["n_bootstrap"],
                "omega_method": cfg["gates"]["hansen_spa"]["omega_method"],
                "note": "M=1 single-strategy degenerate per ADR-0008 + F-Q-5 fix; cross-hypothesis SPA at M=5 deferred to project-level ADR",
            },
        },
        "realized_oos": {
            "starting_equity": 10_000.0,
            "unconditional": {
                "ending_equity": eq_uncond_end,
                "ending_pct_change": (eq_uncond_end / 10_000.0 - 1.0) * 100,
                "max_drawdown_pct": mdd_uncond * 100,
                "n_winning_sessions": w_u,
                "n_losing_sessions": l_u,
                "n_zero_sessions": z_u,
            },
            "anti_gated": {
                "ending_equity": eq_anti_end,
                "ending_pct_change": (eq_anti_end / 10_000.0 - 1.0) * 100,
                "max_drawdown_pct": mdd_anti * 100,
                "n_winning_sessions": w_a,
                "n_losing_sessions": l_a,
                "n_zero_sessions": z_a,
                "n_anti_trades": n_anti_trades,
            },
        },
        "projection_2026_252sessions": {
            "unconditional": proj_uncond,
            "anti_gated": proj_anti,
        },
        "cost_model": {
            "cost_model_id": "futures_orb_v1",
            "sensitivity_mult": cost_model.sensitivity_mult,
            "fee_breakdown": cost_model.fee_breakdown(symbol),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H054 walk-forward orchestrator")
    parser.add_argument(
        "--config", default="config/hypotheses/H054.yaml", help="H054 YAML config path"
    )
    parser.add_argument("--substrate-path", default=None, help="Override substrate path")
    parser.add_argument("--symbols", default=None, help="Comma-separated symbol filter")
    parser.add_argument(
        "--output-dir", default=None, help="Override output dir (artifacts/runs/H054/<run_id>/)"
    )
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

    # Substrate dataset checksum from provenance JSON if present.
    dataset_checksums: dict[str, str] = {}
    provenance_dir = paths.root / "data" / "processed" / "_provenance"
    import glob as _glob
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

    # VIX daily checksum.
    vix_prov_files = sorted(_glob.glob(str(provenance_dir / "vix_daily_*.json")))
    if vix_prov_files:
        try:
            with open(vix_prov_files[-1], encoding="utf-8") as fh:
                vix_prov = json.load(fh)
            sha = vix_prov.get("output_frame_sha256", "")
            if sha:
                dataset_checksums["vix_daily"] = sha
        except (OSError, json.JSONDecodeError) as exc:
            _log.warning("Could not load VIX daily provenance: %s", exc)

    # Load VIX daily.
    try:
        vix_daily_pl = load_vix_daily(paths)
    except FileNotFoundError as exc:
        _log.error(
            "VIX daily not found. Run "
            "`uv run python -m skie_ninja.data.ingest.vix_daily` first. (%s)",
            exc,
        )
        return 2
    vix_daily_pdf = vix_daily_pl.to_pandas()

    # Cost model.
    cost_model = FuturesOrbV1CostModel(
        sensitivity_mult=float(cfg.get("cost_sensitivity_mult", 1.0))
    )

    universe = [s.strip().upper() for s in cfg["universe"]]
    if args.symbols:
        wanted = {s.strip().upper() for s in args.symbols.split(",")}
        universe = [s for s in universe if s in wanted]

    with RunContext(
        phase="walk_forward_h054",
        hypothesis_id=cfg["hypothesis_id"],
        rng_seed=rng_seed,
        dataset_checksums=dataset_checksums,
        config_resolved_sha256=config_resolved_sha256,
    ) as ctx:
        ctx.set_model_hash("PENDING")  # H050 F-R-7 fix
        run_id = ctx.log.run_id  # type: ignore[union-attr]
        out_dir = (
            Path(args.output_dir).resolve()
            if args.output_dir
            else paths.artifacts_runs / cfg["hypothesis_id"] / run_id
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        _log.info("run_id=%s out_dir=%s", run_id, out_dir)

        # Load substrate.
        panel = pl.read_parquet(str(substrate_root / "**" / "*.parquet"))
        _log.info("Substrate: %d rows", panel.height)

        per_symbol: dict[str, Any] = {}
        for sym in universe:
            panel_sym = panel.filter(pl.col("symbol") == sym)
            if panel_sym.height == 0:
                _log.warning("Symbol %s absent from panel; skipping", sym)
                per_symbol[sym] = {"symbol": sym, "status": "absent_from_panel"}
                continue
            per_symbol[sym] = _process_symbol(
                symbol=sym,
                panel_sym=panel_sym,
                vix_daily_pdf=vix_daily_pdf,
                cfg=cfg,
                rng_seed=rng_seed,
                cost_model=cost_model,
            )
            # R-3 fix: atomic write per H050 F-R-5 precedent.
            _atomic_write_text(
                out_dir / f"{sym}_metrics_summary.json",
                json.dumps(per_symbol[sym], indent=2, sort_keys=True, default=str),
            )

        # Run-level scientific payload SHA binding (H050 F-R-1 fix).
        scientific_payload = {
            "hypothesis_id": cfg["hypothesis_id"],
            "run_id": run_id,
            "git_head": git_head,
            "rng_seed": rng_seed,
            "per_symbol": per_symbol,
            "config_resolved_sha256": config_resolved_sha256,
            "dataset_checksums": dataset_checksums,
            "written_at_utc": _dt.datetime.now(_dt.UTC).isoformat(),
        }
        scientific_bytes = json.dumps(
            scientific_payload, indent=2, sort_keys=True, default=str
        ).encode("utf-8")
        scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()
        ctx.set_model_hash(scientific_sha)
        sidecar_path = out_dir / "sidecar.json"
        sidecar_path.with_suffix(".json.tmp").write_bytes(scientific_bytes)
        os.replace(str(sidecar_path.with_suffix(".json.tmp")), str(sidecar_path))
        # R-3 fix: atomic write for scientific_payload_sha256.txt.
        _atomic_write_text(
            out_dir / "scientific_payload_sha256.txt",
            scientific_sha + "\n",
        )
        _log.info(
            "scientific_payload_sha256=%s sidecar=%s", scientific_sha[:16], sidecar_path
        )

    return 0


if __name__ == "__main__":
    # R-1 fix (Round-2 2026-05-04 critical): BLAS thread-pinning carry-forward
    # from H050 F-R-3. Per ADR-0009 + canonical command, OMP=MKL=OPENBLAS=1
    # is required for HMM-fit determinism + multi-host reproducibility.
    # Without this, HMM EM produces non-byte-reproducible results across
    # machines, breaking the ReproLog contract.
    _required_thread_pinning = (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
    )
    _missing_pinning = [
        k for k in _required_thread_pinning if os.environ.get(k) != "1"
    ]
    if _missing_pinning:
        raise RuntimeError(
            f"BLAS thread-pinning env vars {_missing_pinning!r} must be "
            "set to '1' per ADR-0009 (BLAS thread pinning). The canonical "
            "launch path prefixes the orchestrator invocation with: "
            "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "
            "(closes follow-up P1-H054-BLAS-PIN-CARRY-FORWARD)."
        )
    try:
        from threadpoolctl import threadpool_limits as _threadpool_limits
    except ImportError:
        _threadpool_limits = None
    if _threadpool_limits is not None:
        _threadpool_limits(limits=1)

    raise SystemExit(main())
