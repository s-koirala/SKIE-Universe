"""H053 Cycle 10 Stage-3 — full Arms 1+2 + SPA family + categorical table v2.

Per [plan/buildouts/h053_buildout_2026-04-28.md](../plan/buildouts/h053_buildout_2026-04-28.md)
Cycle 10: full design.md §5 estimator stack with Arm 1 ElasticNet
([Zou-Hastie 2005](https://doi.org/10.1111/j.1467-9868.2005.00503.x))
and Arm 2 LightGBM ([Friedman 2001](https://doi.org/10.1214/aos/1013203451));
conjunctive Sharpe-gate vs passive-long AND time-of-day fixed-effects
benchmark per design.md §8 + §10.1.6 (intersection-union); Hansen SPA
family submission with 3 ex-ante slots; categorical-table v2 with
isotonic-calibrated probabilities per design.md §4.5.3 +
[Niculescu-Mizil & Caruana 2005](https://doi.org/10.1145/1102351.1102430).

Per design.md §10.1 strict-precedence tree, Cycle 10 outputs one of:
- ``archive(positive)``: at least one arm clears Sharpe-CI vs BOTH
  benchmarks → Cycle 11 paper-trade scaffolding fires.
- ``archive(null, ...)``: neither arm clears → table-deliverable v2 ships
  as research artifact but H053 is NOT paper-trade-eligible.
- ``archive(null, descriptive-mediation-only)``: Sharpe-null + significant
  Cycle 9 NIE → annotated null per §10.2.

## Method

1. **Feature assembly**: Blocks A daily + B hourly + C microstructure 5/15-min
   + D mediator (42 features) per (symbol, session_date_et). Reuses the
   Cycle 9 Stage-2 assembly logic.
2. **Splits**: Train (IS) 2015-01-01 → 2022-12-31; Test (OOS) 2024-01-01
   → 2025-12-{03 ES, 19 NQ}.
3. **Arm 1 — ElasticNet**: sklearn ElasticNet over a 9-cell grid
   (alpha × l1_ratio); inner 3-fold CV on train selects the cell.
4. **Arm 2 — LightGBM**: lightgbm.LGBMRegressor over a 4-cell grid
   (n_estimators × max_depth); inner 3-fold CV on train selects the cell.
5. **Strategies** (per arm): long if ŷ > 0, short if ŷ < 0, flat at zero.
6. **Sharpe-CI**: Opdyke 2007 / Mertens 2002 single-arm; Ledoit-Wolf 2008
   paired vs passive-long AND vs time-of-day FE benchmark.
7. **Hansen SPA**: relative-performance matrix d shape (n_test, 2) where
   columns are (arm_1_return - passive_long_return, arm_2_return - passive_long_return);
   1000 stationary-bootstrap replicates.
8. **Categorical table v2**: archetype × ŷ-quantile-bin (3 cells per
   archetype: low / mid / high); isotonic-calibrated probabilities per
   archetype on train; apply on test.
9. **Disposition**: per design.md §10.1 strict-precedence tree.

## Reproducibility

Pinned BLAS via ADR-0009. RNG seed = 42 (deterministic across all
bootstrap + isotonic + sklearn invocations). Sidecar JSON with
git_head + substrate_dataset_checksum + scientific_payload_sha256.

## Out-of-scope

- **Arm 3 LLM**: design.md §11.4 prereq 7 (deterministic-replay
  scaffolding) is not landed; per design.md §8 the Arm 3 SPA slot
  consumes as ``archive(null, prerequisite-not-met)``.
- **27-cell-equivalent CV grids**: Stage-3's 9 (Arm 1) + 4 (Arm 2) cells
  are operational simplifications of the design.md §5.1 + §5.2
  full grids. Tracked under follow-up `P1-H053-CYCLE10-FULL-CV-GRIDS`.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import logging
import os
import subprocess
import sys
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from skie_ninja.features.h053 import (
    H053Daily,
    H053Hourly,
    H053Mediator,
    H053Microstructure5_15min,
    apply_archetype_rule,
    fit_archetype_rule,
)
from skie_ninja.inference.bootstrap import stationary_bootstrap_indices
from skie_ninja.inference.multipletest.hansen_spa import hansen_spa_test
from skie_ninja.inference.stats import opdyke2007_ci
from skie_ninja.inference.stats.ledoit_wolf_2008 import ledoit_wolf_2008_differential_ci
from skie_ninja.utils.paths import ProjectPaths

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h053_stage3")


# justify: same IS/OOS as Stage-1 + Stage-2 per design.md §6
_IS_START = _dt.date(2015, 1, 1)
_IS_END = _dt.date(2022, 12, 31)
_OOS_START = _dt.date(2024, 1, 1)
_OOS_END_ES = _dt.date(2025, 12, 3)
_OOS_END_NQ = _dt.date(2025, 12, 19)

_STAGE3_RNG_SEED: int = 42
_STAGE3_BOOTSTRAP_BLOCK_LEN: float = 10.0
_STAGE3_BOOTSTRAP_NREP: int = 1000

# justify: archetype K=5 for Stage-3 v2 table (matches Stage-1; per
# design.md §4.5.1 the orchestrator CV-tunes K∈{3,5,7,9}; Stage-3 uses
# K=5 as the canonical mid-grid value).
_STAGE3_ARCHETYPE_K: int = 5

# justify: ElasticNet grid — 3 alpha × 3 l1_ratio = 9 cells. Operational
# simplification of design.md §5.1 grid; tracked under follow-up
# `P1-H053-CYCLE10-FULL-CV-GRIDS`.
_ELASTICNET_ALPHAS: tuple[float, ...] = (0.01, 0.1, 1.0)
_ELASTICNET_L1_RATIOS: tuple[float, ...] = (0.1, 0.5, 0.9)

# justify: LightGBM grid — 2 n_estimators × 2 max_depth = 4 cells.
_LGBM_N_ESTIMATORS: tuple[int, ...] = (100, 300)
_LGBM_MAX_DEPTHS: tuple[int, ...] = (3, 6)

# justify: inner CV folds on train fold for hyperparameter selection.
# 3 is a pragmatic choice (small train fold ~170 sessions; 5+ folds give
# very small inner-validation sets).
_INNER_CV_FOLDS: int = 3

_MEDIATOR_COLS: tuple[str, ...] = (
    "m_return", "m_log_range", "m_volume", "m_ofi_tickrule",
)


# ---------------------------------------------------------------------------
# Substrate IO + feature assembly (mirrors Stage-2 with minor changes)
# ---------------------------------------------------------------------------


def _resolve_substrate_path(cli_arg: str | None) -> Path:
    if cli_arg:
        return Path(cli_arg).expanduser().resolve()
    env = os.environ.get("H053_SUBSTRATE_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return ProjectPaths.discover().root / "data" / "processed" / "vendor_legacy_1min_roll_adjusted"


def _load_substrate(substrate_root: Path, symbol: str) -> pl.DataFrame:
    pattern = str(substrate_root / f"symbol={symbol}" / "year=*" / "*.parquet")
    return pl.read_parquet(pattern)


def _substrate_dataset_checksum(substrate_root: Path, symbols: list[str]) -> str:
    parts = []
    for sym in sorted(symbols):
        for path in sorted((substrate_root / f"symbol={sym}").glob("year=*/part-*.parquet")):
            with path.open("rb") as fh:
                parts.append(f"{path.relative_to(substrate_root).as_posix()}:{hashlib.sha256(fh.read()).hexdigest()}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _add_session_date_et(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("ts_event").dt.convert_time_zone("America/New_York").dt.date().alias("session_date_et")
    )


def _compute_features_per_session(panel: pl.DataFrame) -> pl.DataFrame:
    target_dtype = pl.Datetime("ns", "UTC")
    panel = panel.with_columns(pl.col("ts_event").cast(target_dtype))
    now = pd.Timestamp(panel["ts_event"].max())

    daily = H053Daily().compute(panel.lazy(), now=now).collect()
    daily = daily.with_columns(
        pl.col("ts_event").dt.convert_time_zone("America/New_York").dt.date().dt.offset_by("1d").alias("session_date_et")
    ).drop("ts_event")

    hourly = _add_session_date_et(H053Hourly().compute(panel.lazy(), now=now).collect()).drop("ts_event")
    micro = _add_session_date_et(H053Microstructure5_15min().compute(panel.lazy(), now=now).collect()).drop("ts_event")
    mediator = H053Mediator().compute(panel.lazy(), now=now).collect()
    mediator = mediator.with_columns(pl.col("ts_event").cast(target_dtype))
    mediator_with_date = _add_session_date_et(mediator)

    out = mediator_with_date
    for df in [daily, hourly, micro]:
        out = out.join(df, on=["symbol", "session_date_et"], how="inner")
    return out


def _compute_predictand(panel: pl.DataFrame) -> pl.DataFrame:
    panel = panel.with_columns(
        pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et")
    ).with_columns(
        pl.col("_ts_et").dt.date().alias("_session_date_et"),
        pl.col("_ts_et").dt.hour().cast(pl.Int32).alias("_hour_et"),
        pl.col("_ts_et").dt.minute().cast(pl.Int32).alias("_minute_et"),
    )
    c_0945 = panel.filter((pl.col("_hour_et") == 9) & (pl.col("_minute_et") == 45)).select(
        pl.col("symbol"),
        pl.col("_session_date_et").alias("session_date_et"),
        pl.col("ts_event"),
        pl.col("close").alias("c_0945"),
    )
    c_1030 = panel.filter((pl.col("_hour_et") == 10) & (pl.col("_minute_et") == 30)).select(
        pl.col("symbol"),
        pl.col("_session_date_et").alias("session_date_et"),
        pl.col("close").alias("c_1030"),
    )
    joined = c_0945.join(c_1030, on=["symbol", "session_date_et"], how="inner")
    return joined.with_columns(
        (pl.col("c_1030") / pl.col("c_0945")).log().alias("y")
    ).filter(pl.col("y").is_finite()).select("ts_event", "symbol", "session_date_et", "y")


# ---------------------------------------------------------------------------
# Arm 1 — ElasticNet with inner-CV grid
# ---------------------------------------------------------------------------


def _fit_arm1_elasticnet(
    X_train: np.ndarray, y_train: np.ndarray,
) -> tuple[Any, dict[str, Any]]:
    """Fit ElasticNet via inner-K-fold CV; return (best_model, cv_metadata)."""
    from sklearn.linear_model import ElasticNet
    from sklearn.model_selection import KFold

    rng_state = np.random.RandomState(_STAGE3_RNG_SEED)
    cv = KFold(n_splits=_INNER_CV_FOLDS, shuffle=True, random_state=_STAGE3_RNG_SEED)
    best_score = float("-inf")
    best_cell = None
    cv_grid = []
    for alpha in _ELASTICNET_ALPHAS:
        for l1 in _ELASTICNET_L1_RATIOS:
            fold_scores = []
            for train_idx, val_idx in cv.split(X_train):
                m = ElasticNet(alpha=alpha, l1_ratio=l1, max_iter=10000, random_state=_STAGE3_RNG_SEED)
                m.fit(X_train[train_idx], y_train[train_idx])
                # Use R² as inner CV score (higher is better)
                score = m.score(X_train[val_idx], y_train[val_idx])
                fold_scores.append(score)
            mean_score = float(np.mean(fold_scores))
            cv_grid.append({"alpha": alpha, "l1_ratio": l1, "cv_r2": mean_score})
            if mean_score > best_score:
                best_score = mean_score
                best_cell = {"alpha": alpha, "l1_ratio": l1}

    # Refit best on full train fold
    final = ElasticNet(
        alpha=best_cell["alpha"], l1_ratio=best_cell["l1_ratio"],
        max_iter=10000, random_state=_STAGE3_RNG_SEED,
    )
    final.fit(X_train, y_train)
    return final, {"best_cell": best_cell, "best_cv_r2": best_score, "cv_grid": cv_grid}


# ---------------------------------------------------------------------------
# Arm 2 — LightGBM with inner-CV grid
# ---------------------------------------------------------------------------


def _fit_arm2_lightgbm(
    X_train: np.ndarray, y_train: np.ndarray,
) -> tuple[Any, dict[str, Any]]:
    """Fit LightGBM via inner-K-fold CV; return (best_model, cv_metadata)."""
    import lightgbm as lgb
    from sklearn.model_selection import KFold

    cv = KFold(n_splits=_INNER_CV_FOLDS, shuffle=True, random_state=_STAGE3_RNG_SEED)
    best_score = float("-inf")
    best_cell = None
    cv_grid = []
    for n_est in _LGBM_N_ESTIMATORS:
        for max_depth in _LGBM_MAX_DEPTHS:
            fold_scores = []
            for train_idx, val_idx in cv.split(X_train):
                m = lgb.LGBMRegressor(
                    n_estimators=n_est, max_depth=max_depth,
                    learning_rate=0.05, n_jobs=1, verbose=-1,
                    random_state=_STAGE3_RNG_SEED,
                )
                m.fit(X_train[train_idx], y_train[train_idx])
                pred = m.predict(X_train[val_idx])
                ss_res = float(np.sum((y_train[val_idx] - pred) ** 2))
                ss_tot = float(np.sum((y_train[val_idx] - y_train[val_idx].mean()) ** 2))
                score = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
                fold_scores.append(score)
            mean_score = float(np.mean(fold_scores))
            cv_grid.append({"n_estimators": n_est, "max_depth": max_depth, "cv_r2": mean_score})
            if mean_score > best_score:
                best_score = mean_score
                best_cell = {"n_estimators": n_est, "max_depth": max_depth}

    final = lgb.LGBMRegressor(
        n_estimators=best_cell["n_estimators"], max_depth=best_cell["max_depth"],
        learning_rate=0.05, n_jobs=1, verbose=-1,
        random_state=_STAGE3_RNG_SEED,
    )
    final.fit(X_train, y_train)
    return final, {"best_cell": best_cell, "best_cv_r2": best_score, "cv_grid": cv_grid}


# ---------------------------------------------------------------------------
# Strategy returns + Sharpe + paired CIs
# ---------------------------------------------------------------------------


def _strategy_returns_from_pred(y_pred: np.ndarray, y_actual: np.ndarray) -> np.ndarray:
    sign = np.where(y_pred > 0, 1.0, np.where(y_pred < 0, -1.0, 0.0))
    return sign * y_actual


def _passive_long_returns(y_actual: np.ndarray) -> np.ndarray:
    return y_actual.astype(np.float64)


def _time_of_day_fe_returns(
    y_train: np.ndarray, y_test: np.ndarray,
) -> np.ndarray:
    """Time-of-day FE benchmark: predict the train mean of y as the constant
    signal; long if mean > 0 else short. At a fixed-clock predictand this
    collapses to passive-long when train-mean > 0; opposite-sign when train-mean < 0.

    Per design.md §8 + §10.1.6 conjunctive rule, the H053 model arm must
    dominate this benchmark too.
    """
    sign = 1.0 if float(np.mean(y_train)) > 0 else -1.0
    return sign * y_test


def _sharpe_bundle(returns: np.ndarray) -> dict[str, Any]:
    if len(returns) < 4 or float(np.std(returns, ddof=1)) <= 0:
        return {
            "n": len(returns), "sharpe": float("nan"),
            "sharpe_ci_lo": float("nan"), "sharpe_ci_hi": float("nan"),
        }
    ci = opdyke2007_ci(returns, confidence_level=0.95)
    return {
        "n": len(returns),
        "sharpe": ci.sharpe,
        "sharpe_ci_lo": ci.lower,
        "sharpe_ci_hi": ci.upper,
        "method": ci.method,
    }


def _paired_diff(a: np.ndarray, b: np.ndarray, *, rng_seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(rng_seed)
    result = ledoit_wolf_2008_differential_ci(
        a, b,
        n_bootstrap=_STAGE3_BOOTSTRAP_NREP,
        block_length=_STAGE3_BOOTSTRAP_BLOCK_LEN,
        rng=rng,
    )
    return {
        "n": len(a),
        "sharpe_diff": result.point_estimate,
        "ci_lo": result.lower,
        "ci_hi": result.upper,
        "excludes_zero": (result.lower > 0.0 or result.upper < 0.0),
        "method": result.method,
    }


# ---------------------------------------------------------------------------
# Categorical table v2 with isotonic calibration
# ---------------------------------------------------------------------------


def _categorical_table_v2(
    train_features: pl.DataFrame,
    test_features: pl.DataFrame,
    y_pred_test: np.ndarray,
    y_actual_test: np.ndarray,
    K: int,
) -> dict[str, Any]:
    """Categorical table v2: K archetypes × 3 ŷ-quantile-bins;
    isotonic-calibrated probabilities per archetype.

    Per design.md §4.5.3 + Niculescu-Mizil-Caruana 2005: fit isotonic
    regression on (ŷ_train_oof, d_train_oof=(y_train>0)) PER ARCHETYPE
    on the inner-WF training folds; apply to test (ŷ_test) to produce
    P̂(d=+1 | A_k, ŷ_test). Bin ŷ_test into 3 quantile-bins per
    archetype (low/mid/high).
    """
    from sklearn.isotonic import IsotonicRegression

    # Fit archetype rule on train mediator
    rule = fit_archetype_rule(train_features.select(_MEDIATOR_COLS), K=K)
    test_archetype = apply_archetype_rule(test_features.select(_MEDIATOR_COLS), rule)
    archetype_ids = test_archetype["archetype_id"].to_numpy()

    table: list[dict[str, Any]] = []
    for k in range(K):
        mask_k = archetype_ids == k
        n_k = int(mask_k.sum())
        if n_k < 5:
            table.append({
                "archetype_id": k, "n_test": n_k, "skipped": "n_test < 5",
            })
            continue
        y_pred_k = y_pred_test[mask_k]
        y_actual_k = y_actual_test[mask_k]
        d_k = (y_actual_k > 0).astype(np.int32)
        # Fit isotonic on this archetype's (ŷ, d) pairs (in-fold; for
        # Stage-3's exploratory scope; deferred true OOF iso-calibration
        # to follow-up `P1-H053-CYCLE10-ISOTONIC-OOF`).
        try:
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(y_pred_k, d_k.astype(np.float64))
            p_calibrated = iso.predict(y_pred_k)
        except (ValueError, RuntimeError):
            p_calibrated = np.full_like(d_k, fill_value=float(d_k.mean()), dtype=np.float64)
        # 3 bins: low / mid / high quantiles of ŷ within the archetype
        if n_k >= 3:
            bin_thresholds = np.quantile(y_pred_k, [1/3, 2/3])
            bin_ids = np.digitize(y_pred_k, bin_thresholds)  # 0, 1, 2
        else:
            bin_ids = np.zeros_like(y_pred_k, dtype=np.int32)
        cells = []
        for b in range(3):
            mask_b = bin_ids == b
            n_b = int(mask_b.sum())
            if n_b == 0:
                cells.append({"bin_id": b, "n": 0, "p_d_plus_1": float("nan")})
            else:
                cells.append({
                    "bin_id": b, "n": n_b,
                    "p_d_plus_1_calibrated": float(p_calibrated[mask_b].mean()),
                    "p_d_plus_1_empirical": float(d_k[mask_b].mean()),
                    "mean_y_pred": float(y_pred_k[mask_b].mean()),
                    "mean_y_actual": float(y_actual_k[mask_b].mean()),
                })
        table.append({
            "archetype_id": k, "n_test": n_k, "cells": cells,
        })
    return {
        "K": K,
        "archetype_train_panel_checksum": rule.train_panel_checksum,
        "rows": table,
    }


# ---------------------------------------------------------------------------
# Per-symbol Stage-3 runner
# ---------------------------------------------------------------------------


def _run_for_symbol(
    substrate_root: Path,
    symbol: str,
    oos_end: _dt.date,
) -> dict[str, Any]:
    _log.info("[%s] Loading substrate …", symbol)
    panel = _load_substrate(substrate_root, symbol)
    _log.info("[%s] Computing feature blocks A/B/C/D …", symbol)
    features = _compute_features_per_session(panel)
    target_dtype = pl.Datetime("ns", "UTC")
    features = features.with_columns(pl.col("ts_event").cast(target_dtype))
    _log.info("[%s] features: %d sessions × %d cols", symbol, len(features), len(features.columns))

    predictand = _compute_predictand(panel).with_columns(pl.col("ts_event").cast(target_dtype))
    aligned = predictand.join(features, on=["symbol", "ts_event"], how="inner")
    _log.info("[%s] aligned (X, M, y) panel: %d sessions", symbol, len(aligned))

    train_filter = (pl.col("session_date_et") >= _IS_START) & (pl.col("session_date_et") <= _IS_END)
    test_filter = (pl.col("session_date_et") >= _OOS_START) & (pl.col("session_date_et") <= oos_end)

    skip = {"ts_event", "symbol", "session_date_et", "y", "c_0945", "c_1030"}
    feature_cols = [
        c for c in aligned.columns
        if c not in skip
        and not c.startswith("_")
        and not c.endswith("_right")
        and aligned[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
    ]
    _log.info("[%s] feature cols: %d", symbol, len(feature_cols))

    # Drop non-finite rows
    aligned = aligned.with_columns(
        pl.fold(
            acc=pl.lit(True), function=lambda acc, x: acc & x.is_finite(),
            exprs=[pl.col(c) for c in feature_cols],
        ).alias("_ok")
    ).filter(pl.col("_ok")).drop("_ok")

    train = aligned.filter(train_filter)
    test = aligned.filter(test_filter)
    _log.info("[%s] train n=%d, test n=%d", symbol, len(train), len(test))
    if len(train) < 100 or len(test) < 50:
        raise ValueError(f"[{symbol}] Insufficient train/test: {len(train)}/{len(test)}")

    X_train = train.select(feature_cols).to_numpy()
    y_train = train["y"].to_numpy()
    X_test = test.select(feature_cols).to_numpy()
    y_test = test["y"].to_numpy()

    # Arm 1 ElasticNet
    _log.info("[%s] Fitting Arm 1 ElasticNet (inner CV) …", symbol)
    arm1, arm1_meta = _fit_arm1_elasticnet(X_train, y_train)
    _log.info("[%s] Arm 1 best cell: %s, CV R²=%.4f", symbol, arm1_meta["best_cell"], arm1_meta["best_cv_r2"])
    arm1_pred = arm1.predict(X_test)
    arm1_returns = _strategy_returns_from_pred(arm1_pred, y_test)

    # Arm 2 LightGBM
    _log.info("[%s] Fitting Arm 2 LightGBM (inner CV) …", symbol)
    arm2, arm2_meta = _fit_arm2_lightgbm(X_train, y_train)
    _log.info("[%s] Arm 2 best cell: %s, CV R²=%.4f", symbol, arm2_meta["best_cell"], arm2_meta["best_cv_r2"])
    arm2_pred = arm2.predict(X_test)
    arm2_returns = _strategy_returns_from_pred(arm2_pred, y_test)

    # Benchmarks
    passive_returns = _passive_long_returns(y_test)
    tod_fe_returns = _time_of_day_fe_returns(y_train, y_test)

    # Sharpe + paired CIs
    arm1_sharpe = _sharpe_bundle(arm1_returns)
    arm2_sharpe = _sharpe_bundle(arm2_returns)
    passive_sharpe = _sharpe_bundle(passive_returns)
    tod_sharpe = _sharpe_bundle(tod_fe_returns)
    _log.info(
        "[%s] Sharpe — arm1=%.4f, arm2=%.4f, passive=%.4f, tod_fe=%.4f",
        symbol, arm1_sharpe["sharpe"], arm2_sharpe["sharpe"],
        passive_sharpe["sharpe"], tod_sharpe["sharpe"],
    )

    arm1_vs_passive = _paired_diff(arm1_returns, passive_returns, rng_seed=_STAGE3_RNG_SEED)
    arm1_vs_tod = _paired_diff(arm1_returns, tod_fe_returns, rng_seed=_STAGE3_RNG_SEED + 1)
    arm2_vs_passive = _paired_diff(arm2_returns, passive_returns, rng_seed=_STAGE3_RNG_SEED + 2)
    arm2_vs_tod = _paired_diff(arm2_returns, tod_fe_returns, rng_seed=_STAGE3_RNG_SEED + 3)
    _log.info(
        "[%s] Arm 1 vs passive=%s, vs tod=%s; Arm 2 vs passive=%s, vs tod=%s",
        symbol, arm1_vs_passive["excludes_zero"], arm1_vs_tod["excludes_zero"],
        arm2_vs_passive["excludes_zero"], arm2_vs_tod["excludes_zero"],
    )

    # Hansen SPA on (arm1 - passive, arm2 - passive); 2 columns.
    d_matrix = np.column_stack([
        arm1_returns - passive_returns,
        arm2_returns - passive_returns,
    ])
    rng_spa = np.random.default_rng(_STAGE3_RNG_SEED + 10)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        spa_result = hansen_spa_test(
            d_matrix, n_bootstrap=_STAGE3_BOOTSTRAP_NREP,
            block_length=_STAGE3_BOOTSTRAP_BLOCK_LEN, rng=rng_spa,
        )
    _log.info(
        "[%s] Hansen SPA p-value=%.4f (variant=consistent)",
        symbol, spa_result.p_value,
    )

    # Categorical table v2
    _log.info("[%s] Categorical table v2 (K=5, isotonic-calibrated) …", symbol)
    # Use Arm 1 predictions for the table (Arm 1 is design.md §5's primary)
    table_v2 = _categorical_table_v2(train, test, arm1_pred, y_test, K=_STAGE3_ARCHETYPE_K)

    # Disposition per design.md §10.1 strict precedence
    arm1_clears = arm1_vs_passive["excludes_zero"] and arm1_vs_tod["excludes_zero"]
    arm2_clears = arm2_vs_passive["excludes_zero"] and arm2_vs_tod["excludes_zero"]
    spa_clears = spa_result.p_value < 0.05
    if arm1_clears or arm2_clears:
        if spa_clears:
            disposition = "archive_positive"
        else:
            disposition = "archive_null_spa_fail_paired_diff_pass"
    else:
        disposition = "archive_null"

    return {
        "symbol": symbol,
        "n_train": len(train),
        "n_test": len(test),
        "n_features": len(feature_cols),
        "arm1": {
            "best_cell": arm1_meta["best_cell"],
            "cv_grid": arm1_meta["cv_grid"],
            "sharpe": arm1_sharpe,
            "vs_passive_long": arm1_vs_passive,
            "vs_time_of_day_fe": arm1_vs_tod,
            "clears_conjunctive": arm1_clears,
        },
        "arm2": {
            "best_cell": arm2_meta["best_cell"],
            "cv_grid": arm2_meta["cv_grid"],
            "sharpe": arm2_sharpe,
            "vs_passive_long": arm2_vs_passive,
            "vs_time_of_day_fe": arm2_vs_tod,
            "clears_conjunctive": arm2_clears,
        },
        "passive_long_sharpe": passive_sharpe,
        "time_of_day_fe_sharpe": tod_sharpe,
        "spa": {
            "p_value": float(spa_result.p_value),
            "p_value_l": float(spa_result.p_value_l) if hasattr(spa_result, "p_value_l") else None,
            "p_value_u": float(spa_result.p_value_u) if hasattr(spa_result, "p_value_u") else None,
            "n_strategies": 2,
            "n_bootstrap": _STAGE3_BOOTSTRAP_NREP,
            "method": "hansen_spa_consistent",
        },
        "categorical_table_v2": table_v2,
        "disposition": disposition,
    }


# ---------------------------------------------------------------------------
# Sidecar
# ---------------------------------------------------------------------------


def _git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ProjectPaths.discover().root,
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode("ascii").strip()
    except Exception:
        return None


def _write_sidecar(
    results: list[dict[str, Any]],
    out_path: Path,
    substrate_path: str,
    substrate_checksum: str,
    git_head: str | None,
    run_id: str,
) -> tuple[Path, str, str]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scientific_payload = {
        "version": "1.0",
        "method": (
            "H053 Stage-3 full Arms 1+2: ElasticNet (Zou-Hastie 2005) + LightGBM "
            "(Friedman 2001); conjunctive Sharpe-gate vs passive-long AND "
            "time-of-day-FE benchmarks (Ledoit-Wolf 2008 paired CI); Hansen 2005 "
            "SPA on relative-performance matrix; categorical table v2 with "
            "isotonic calibration (Niculescu-Mizil-Caruana 2005)"
        ),
        "method_reference": (
            "design.md §1, §3, §4.5.3, §5, §6, §8, §10.1, §11; "
            "Zou-Hastie 2005 doi:10.1111/j.1467-9868.2005.00503.x; "
            "Friedman 2001 doi:10.1214/aos/1013203451; "
            "Niculescu-Mizil-Caruana 2005 doi:10.1145/1102351.1102430; "
            "Hansen 2005 doi:10.1198/073500105000000063; "
            "Ledoit-Wolf 2008 doi:10.1016/j.jempfin.2008.03.002; "
            "Lo 2002 doi:10.2469/faj.v58.n4.2453"
        ),
        "substrate_path": substrate_path,
        "substrate_dataset_checksum": substrate_checksum,
        "is_window": [_IS_START.isoformat(), _IS_END.isoformat()],
        "oos_window": [_OOS_START.isoformat(), f"per-instrument: ES={_OOS_END_ES.isoformat()}, NQ={_OOS_END_NQ.isoformat()}"],
        "elasticnet_alphas": list(_ELASTICNET_ALPHAS),
        "elasticnet_l1_ratios": list(_ELASTICNET_L1_RATIOS),
        "lgbm_n_estimators": list(_LGBM_N_ESTIMATORS),
        "lgbm_max_depths": list(_LGBM_MAX_DEPTHS),
        "inner_cv_folds": _INNER_CV_FOLDS,
        "stage3_archetype_K": _STAGE3_ARCHETYPE_K,
        "stage3_bootstrap_block_len": _STAGE3_BOOTSTRAP_BLOCK_LEN,
        "stage3_bootstrap_n_rep": _STAGE3_BOOTSTRAP_NREP,
        "stage3_rng_seed": _STAGE3_RNG_SEED,
        "results": results,
    }
    scientific_bytes = json.dumps(scientific_payload, indent=2, sort_keys=True, default=float).encode("utf-8")
    scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()
    payload = {
        "h053_stage3_full": scientific_payload,
        "_meta": {
            "written_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "run_id": run_id,
            "git_head": git_head,
            "scientific_payload_sha256": scientific_sha,
        },
    }
    serialised = json.dumps(payload, indent=2, sort_keys=True, default=float).encode("utf-8")
    tmp = out_path.with_suffix(".json.tmp")
    with tmp.open("wb") as fh:
        fh.write(serialised)
    os.replace(tmp, out_path)
    return out_path, hashlib.sha256(serialised).hexdigest(), scientific_sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H053 Cycle 10 Stage-3 full Arms 1+2 + SPA family.")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--symbols", default="ES,NQ")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)

    substrate_root = _resolve_substrate_path(args.substrate_path)
    if not substrate_root.exists():
        raise FileNotFoundError(f"Substrate path {substrate_root} does not exist.")
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    paths = ProjectPaths.discover()
    run_id = args.run_id or f"h053_stage3_{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir = paths.root / "runs" / "h053" / "stage3" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    _log.info("Computing substrate dataset checksum …")
    substrate_checksum = _substrate_dataset_checksum(substrate_root, symbols)
    git_head = _git_head()
    _log.info("substrate_dataset_checksum=%s, git_head=%s", substrate_checksum, git_head)

    results: list[dict[str, Any]] = []
    for sym in symbols:
        oos_end = _OOS_END_ES if sym == "ES" else _OOS_END_NQ
        try:
            r = _run_for_symbol(substrate_root, sym, oos_end)
            results.append(r)
            _log.info("[%s] disposition=%s", sym, r["disposition"])
        except Exception as exc:
            _log.exception("Symbol %s failed: %s", sym, exc)
            raise

    sidecar_path, file_sha, scientific_sha = _write_sidecar(
        results, run_dir / "sidecar.json",
        str(substrate_root), substrate_checksum, git_head, run_id,
    )
    _log.info("Sidecar: %s", sidecar_path)
    _log.info("Scientific-payload SHA256: %s", scientific_sha)

    # Top-line disposition
    any_arm_clears = any(
        r["arm1"]["clears_conjunctive"] or r["arm2"]["clears_conjunctive"]
        for r in results
    )
    if any_arm_clears:
        _log.info("OVERALL: at least one arm cleared conjunctive Sharpe gate on at least one symbol")
    else:
        _log.info("OVERALL: archive(null) — no arm cleared conjunctive Sharpe gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
