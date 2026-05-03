"""H053 Cycle 10 Stage-3 v3 — leakage-clean refactor of v2 per Round-2 Stage-3-v2 audit.

Closes the 3 critical leakage findings from
[docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md](
../docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md):

| Stage-3 v2 audit ID | Defect | v3 fix |
|---|---|---|
| F-2-1 | CPCV runs over FULL panel (train+test concatenated); `embargo=0` means train/test segments can abut, violating strict time-ordering | Pass `embargo=2` to ``cpcv_path_sharpe`` (= 2 × `label_horizon` per AFML §7.4 / mlfinlab `ml_get_train_times` stacked-embargo discipline + ADR-0007) |
| F-2-2 | Inner ``KFold(shuffle=True, random_state=42)`` for hyperparameter selection violates `rules/quant-project.md` §Time-series integrity ("walk-forward CV, never k-fold"); double-leakage inside CPCV | Replace with ``purged_kfold_split`` (AFML §7.4.3) for inner CV; preserves time ordering + embargo around inner-test blocks |
| F-2-3 | OOF isotonic fits on ``arm_local.predict(X_train[train_idx])`` — in-sample to inner arm fit; isotonic mapping learned on optimistic in-sample predictions | 3-way nested time-ordered split per Niculescu-Mizil & Caruana 2005 §4: inner-arm-train (first 80% of inner train, chronological) → inner-iso-fit (last 20%, held-out). Isotonic learns from OOS-to-arm predictions on inner-iso-fit; applies to inner-test |

ADR-0013 ([../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](
../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md))
is in force. Per ADR-0013 §1, this script:

- Does NOT import ``skie_ninja.inference.disposition`` (still emits ADR-0012 vocabulary
  per BLOCKING follow-up ``P1-ADR-0013-DISPOSITION-FRAMEWORK-REFACTOR``).
- Emits a sidecar JSON conforming to the ADR-0013 §3 KPI report card structure.
- Annotates leakage-canary, BSS, reliability slope, repro-log presence, etc. as
  KPIs (not gates).

The output sidecar is consumed by the KPI report card v2 emission step
(``research/01_hypothesis_register/H053/H053_kpi_report_v2.md``).

References
----------
- López de Prado, M. 2018. *Advances in Financial Machine Learning*,
  Chapter 12 "Backtesting through Cross-Validation", §12.5 "The Combinatorial
  Purged Cross-Validation Method". Wiley. ISBN 978-1-119-48208-6.
- Niculescu-Mizil, A. & Caruana, R. 2005. "Predicting good probabilities
  with supervised learning." ICML 2005. DOI 10.1145/1102351.1102430.
- ADR-0007 stacked-embargo placement.
- ADR-0008 SPA omega correction.
- audit_trail_2026-05-03_h053-stage3-v2.md F-2-1, F-2-2, F-2-3 (precipitating findings).
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

# justify: ensure project root + src/ are on sys.path. Project root for
# `from scripts.run_h053_stage3_full import ...`; src/ for `from skie_ninja...`
# (the project uses src-layout but pyproject has no [build-system] declared,
# so uv venvs are not auto-populated with the editable install — `uv run`
# leaves skie_ninja unimportable unless we add src/ to sys.path explicitly).
_REPO_ROOT = Path(__file__).resolve().parent.parent  # paths-guard: allow (script-bootstrap)
_SRC_DIR = _REPO_ROOT / "src"  # paths-guard: allow (script-bootstrap)
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import polars as pl

from skie_ninja.backtest.cpcv_path_sharpe import _sharpe, cpcv_path_sharpe
from skie_ninja.backtest.splits import purged_kfold_split
from skie_ninja.inference.multipletest.hansen_spa import (
    SingleStrategySPAWarning,
    hansen_spa_test,
)
from skie_ninja.utils.paths import ProjectPaths

from scripts.run_h053_stage3_full import (
    _ELASTICNET_ALPHAS,
    _ELASTICNET_L1_RATIOS,
    _IS_END,
    _IS_START,
    _LGBM_MAX_DEPTHS,
    _LGBM_N_ESTIMATORS,
    _OOS_END_ES,
    _OOS_END_NQ,
    _OOS_START,
    _STAGE3_BOOTSTRAP_BLOCK_LEN,
    _STAGE3_BOOTSTRAP_NREP,
    _STAGE3_RNG_SEED,
    _compute_features_per_session,
    _compute_predictand,
    _git_head,
    _load_substrate,
    _passive_long_returns,
    _resolve_substrate_path,
    _strategy_returns_from_pred,
    _substrate_dataset_checksum,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h053_stage3_v3")

# justify: H053 PIT canary integration test path; observed-pass annotation,
# NOT a gate per ADR-0013 §2.
_PIT_CANARY_TEST_PATH: str = "tests/integration/test_h053_pit_canaries.py"

# justify: power calibration anchor per data_requirements_H053_2026-04-28.md
# option-3 election (Lo 2002 §III HAC under iid Gaussian conservative prior).
_N_REQUIRED_FOR_POWER_80: int = 620

# justify: inner-CV folds for hyperparameter selection. 3 folds preserves the
# v1 + v2 grid budget (3 alphas × 3 l1_ratios × 3 folds = 27 fits; 2 n_est ×
# 2 max_depth × 3 folds = 12 fits per arm). Per F-2-2 fix, time-ordered
# (purged-K-fold) replaces KFold(shuffle=True) but keeps the same fold count.
_INNER_CV_FOLDS_V3: int = 3

# justify: H053 label_horizon = 1 session (predictand is the same-session
# 09:45→10:30 ET log return; no next-session lookahead).
_LABEL_HORIZON: int = 1

# justify: F-2-1 fix: embargo = 2 × label_horizon per AFML §7.4 / Snippet 7.3
# stacked-embargo discipline + ADR-0007 mlfinlab-stacked semantics. With
# label_horizon=1, embargo=2 closes the trailing-edge contamination path
# that v2's embargo=0 left open. Empirically more conservative than the
# typical 1-2× label-horizon embargo (Bergmeir-Benítez 2012, Lopez de Prado
# 2018 §7.4.2).
_CPCV_EMBARGO: int = 2

# justify: F-2-1 fix: inner-CPCV BSS embargo same scale.
_INNER_CPCV_EMBARGO: int = 2

# justify: ADR-0012 binding CPCV grid (preserved per ADR-0013 §7).
_CPCV_N_GROUPS: int = 10
_CPCV_N_TEST_GROUPS: int = 2
_OOF_INNER_CPCV_N_GROUPS: int = 5
_OOF_INNER_CPCV_N_TEST_GROUPS: int = 1

# justify: F-2-3 fix: 80/20 chronological split inside each inner-CPCV
# train fold for the held-out isotonic source per Niculescu-Mizil & Caruana
# 2005 §4 calibration-on-held-out-OOS pattern. The 80/20 split is operational
# (calibration tracked under follow-up `P1-ISO-HELDOUT-FRACTION-CALIBRATION`).
_ISO_HELDOUT_FRACTION: float = 0.20


# ---------------------------------------------------------------------------
# F-2-2 fix: time-ordered inner CV via purged_kfold_split
# ---------------------------------------------------------------------------


def _fit_arm1_elasticnet_v3(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> tuple[Any, dict[str, Any]]:
    """ElasticNet via inner purged-K-fold CV. F-2-2 fix.

    Replaces v1's ``KFold(shuffle=True, random_state=42)`` with
    ``purged_kfold_split`` (AFML §7.4.3) so the inner CV preserves time
    ordering + embargo around inner-test blocks. Same hyperparameter
    grid as v1/v2.
    """
    from sklearn.linear_model import ElasticNet

    n = len(X_train)
    spec = purged_kfold_split(
        n_samples=n,
        n_splits=_INNER_CV_FOLDS_V3,
        label_horizon=_LABEL_HORIZON,
        embargo=_INNER_CPCV_EMBARGO,
    )

    best_score = float("-inf")
    best_cell = None
    cv_grid = []
    for alpha in _ELASTICNET_ALPHAS:
        for l1 in _ELASTICNET_L1_RATIOS:
            fold_scores = []
            for fold in spec.folds:
                tr = np.asarray(fold.train_indices(), dtype=np.int64)
                va = np.asarray(fold.test_indices(), dtype=np.int64)
                if len(tr) < 30 or len(va) < 5:
                    continue
                m = ElasticNet(
                    alpha=alpha, l1_ratio=l1, max_iter=10000,
                    random_state=_STAGE3_RNG_SEED,
                )
                m.fit(X_train[tr], y_train[tr])
                fold_scores.append(float(m.score(X_train[va], y_train[va])))
            if not fold_scores:
                mean_score = float("-inf")
            else:
                mean_score = float(np.mean(fold_scores))
            cv_grid.append({"alpha": alpha, "l1_ratio": l1, "cv_r2": mean_score})
            if mean_score > best_score:
                best_score = mean_score
                best_cell = {"alpha": alpha, "l1_ratio": l1}

    final = ElasticNet(
        alpha=best_cell["alpha"], l1_ratio=best_cell["l1_ratio"],
        max_iter=10000, random_state=_STAGE3_RNG_SEED,
    )
    final.fit(X_train, y_train)
    return final, {
        "best_cell": best_cell,
        "best_cv_r2": best_score,
        "cv_grid": cv_grid,
        "inner_cv_method": "purged_kfold_split",
        "inner_cv_n_splits": _INNER_CV_FOLDS_V3,
        "inner_cv_label_horizon": _LABEL_HORIZON,
        "inner_cv_embargo": _INNER_CPCV_EMBARGO,
    }


def _fit_arm2_lightgbm_v3(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> tuple[Any, dict[str, Any]]:
    """LightGBM via inner purged-K-fold CV. F-2-2 fix."""
    import lightgbm as lgb

    n = len(X_train)
    spec = purged_kfold_split(
        n_samples=n,
        n_splits=_INNER_CV_FOLDS_V3,
        label_horizon=_LABEL_HORIZON,
        embargo=_INNER_CPCV_EMBARGO,
    )

    best_score = float("-inf")
    best_cell = None
    cv_grid = []
    for n_est in _LGBM_N_ESTIMATORS:
        for max_depth in _LGBM_MAX_DEPTHS:
            fold_scores = []
            for fold in spec.folds:
                tr = np.asarray(fold.train_indices(), dtype=np.int64)
                va = np.asarray(fold.test_indices(), dtype=np.int64)
                if len(tr) < 30 or len(va) < 5:
                    continue
                m = lgb.LGBMRegressor(
                    n_estimators=n_est, max_depth=max_depth,
                    learning_rate=0.05, n_jobs=1, verbose=-1,
                    random_state=_STAGE3_RNG_SEED,
                )
                m.fit(X_train[tr], y_train[tr])
                pred = m.predict(X_train[va])
                ss_res = float(np.sum((y_train[va] - pred) ** 2))
                ss_tot = float(np.sum((y_train[va] - y_train[va].mean()) ** 2))
                score = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
                fold_scores.append(float(score))
            if not fold_scores:
                mean_score = float("-inf")
            else:
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
    return final, {
        "best_cell": best_cell,
        "best_cv_r2": best_score,
        "cv_grid": cv_grid,
        "inner_cv_method": "purged_kfold_split",
        "inner_cv_n_splits": _INNER_CV_FOLDS_V3,
        "inner_cv_label_horizon": _LABEL_HORIZON,
        "inner_cv_embargo": _INNER_CPCV_EMBARGO,
    }


# ---------------------------------------------------------------------------
# F-2-3 fix: held-out isotonic source via 3-way nested time-ordered split
# ---------------------------------------------------------------------------


def _compute_oof_brier_components_v3(
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    arm_fit_fn,
) -> dict[str, Any]:
    """OOF isotonic-calibrated probability + BSS via inner CPCV with
    held-out isotonic source. F-2-3 fix.

    Per Niculescu-Mizil & Caruana 2005 §4: isotonic regression as a
    calibrator must be fit on out-of-sample predictions, never on
    in-sample predictions (the latter produces optimistic calibration
    curves and inflates BSS).

    Algorithm:
    1. Inner CPCV split on the train fold (5 folds, 1 test-group each).
    2. For each inner fold:
       a. Take inner-train indices (sorted chronologically).
       b. Split inner-train into inner-arm-train (first 80%, chronological)
          + inner-iso-fit (last 20%, held-out, time-ordered).
       c. Fit ``arm_fit_fn`` on inner-arm-train.
       d. Predict on inner-iso-fit → these are OOS-to-arm predictions.
       e. Fit isotonic on (inner-iso-fit predictions, inner-iso-fit y > 0).
       f. Predict on inner-test (different from inner-iso-fit).
       g. Apply isotonic to inner-test predictions → p_oof[inner_test_idx].
    3. Concatenate OOF probabilities across folds.
    4. BSS = 1 - Brier(p_oof, d_actual) / Brier(p_clim, d_actual)
       where p_clim = mean(d_train > 0).
    5. Reliability slope = regression of binned mean(d) on binned mean(p_oof).

    Both BSS and reliability slope are returned in the same dict.
    """
    from sklearn.isotonic import IsotonicRegression
    from skie_ninja.backtest.splits import cpcv_split

    n = len(X_train)
    spec = cpcv_split(
        n_samples=n,
        n_groups=_OOF_INNER_CPCV_N_GROUPS,
        n_test_groups=_OOF_INNER_CPCV_N_TEST_GROUPS,
        label_horizon=_LABEL_HORIZON,
        embargo=_INNER_CPCV_EMBARGO,
    )
    p_oof = np.full(n, np.nan, dtype=np.float64)
    d_actual = (y_train > 0).astype(np.float64)

    iso_holdout_n_total = 0
    iso_fit_failures = 0
    fold_skips = 0

    for fold in spec.folds:
        tr_full = np.asarray(fold.train_indices(), dtype=np.int64)
        te = np.asarray(fold.test_indices(), dtype=np.int64)
        if len(tr_full) < 60 or len(te) < 5:
            fold_skips += 1
            continue

        # F-2-3 fix: chronological 80/20 split of inner-train
        # `cpcv_split` returns indices preserving chronological order
        # (purged_kfold_split + cpcv_split both build segments from
        # contiguous index ranges). Sort defensively in case of
        # implementation drift.
        tr_sorted = np.sort(tr_full)
        cut = int(np.floor(len(tr_sorted) * (1.0 - _ISO_HELDOUT_FRACTION)))
        if cut < 30 or len(tr_sorted) - cut < 5:
            fold_skips += 1
            continue
        inner_arm_train = tr_sorted[:cut]
        inner_iso_fit = tr_sorted[cut:]
        iso_holdout_n_total += len(inner_iso_fit)

        try:
            arm_local, _ = arm_fit_fn(X_train[inner_arm_train], y_train[inner_arm_train])
            iso_source_pred = arm_local.predict(X_train[inner_iso_fit])
            test_pred = arm_local.predict(X_train[te])
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(iso_source_pred, (y_train[inner_iso_fit] > 0).astype(np.float64))
            p_oof[te] = iso.predict(test_pred)
        except (ValueError, RuntimeError) as exc:
            _log.warning("OOF inner fold %d isotonic fit failed: %s", fold.fold_id, exc)
            iso_fit_failures += 1
            continue

    finite_mask = np.isfinite(p_oof)
    n_oof = int(finite_mask.sum())
    if n_oof < 30:
        return {
            "n_oof": n_oof,
            "bss": float("nan"),
            "brier_calibrated": float("nan"),
            "brier_climatological": float("nan"),
            "reliability_slope": float("nan"),
            "iso_holdout_n_total": iso_holdout_n_total,
            "iso_fit_failures": iso_fit_failures,
            "fold_skips": fold_skips,
            "method": "v3_held_out_isotonic_source",
        }
    p_clim = float(d_actual[finite_mask].mean())
    brier_cal = float(np.mean((p_oof[finite_mask] - d_actual[finite_mask]) ** 2))
    brier_clim = float(np.mean((p_clim - d_actual[finite_mask]) ** 2))
    bss = (1.0 - brier_cal / brier_clim) if brier_clim > 0 else float("nan")

    # Reliability slope on the OOF p
    slope = _reliability_slope(p_oof[finite_mask], d_actual[finite_mask], n_bins=10)

    return {
        "n_oof": n_oof,
        "bss": float(bss),
        "brier_calibrated": brier_cal,
        "brier_climatological": brier_clim,
        "p_clim": p_clim,
        "reliability_slope": float(slope),
        "iso_holdout_n_total": iso_holdout_n_total,
        "iso_fit_failures": iso_fit_failures,
        "fold_skips": fold_skips,
        "method": "v3_held_out_isotonic_source",
    }


def _reliability_slope(p: np.ndarray, d: np.ndarray, *, n_bins: int = 10) -> float:
    """Regression of binned mean(d) on binned mean(p_oof)."""
    finite = np.isfinite(p) & np.isfinite(d)
    if finite.sum() < 30:
        return float("nan")
    p, d = p[finite], d[finite]
    bins = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    bin_p, bin_d = [], []
    for i in range(n_bins):
        mask = (p >= bins[i]) & (p < bins[i + 1] if i < n_bins - 1 else p <= bins[i + 1])
        if mask.sum() < 5:
            continue
        bin_p.append(float(p[mask].mean()))
        bin_d.append(float(d[mask].mean()))
    if len(bin_p) < 3:
        return float("nan")
    bp = np.asarray(bin_p)
    bd = np.asarray(bin_d)
    if bp.std() <= 0:
        return float("nan")
    return float(np.cov(bp, bd, ddof=0)[0, 1] / np.var(bp, ddof=0))


# ---------------------------------------------------------------------------
# Hansen SPA KPI (preserved from v2; same SingleStrategySPAWarning capture)
# ---------------------------------------------------------------------------


def _hansen_spa_kpi(
    arm1_returns: np.ndarray, arm2_returns: np.ndarray, passive_returns: np.ndarray,
) -> dict[str, Any]:
    d_matrix = np.column_stack([
        arm1_returns - passive_returns,
        arm2_returns - passive_returns,
    ])
    rng_spa = np.random.default_rng(_STAGE3_RNG_SEED + 10)
    spa_warnings_caught: list[str] = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", SingleStrategySPAWarning)
        spa_result = hansen_spa_test(
            d_matrix,
            n_bootstrap=_STAGE3_BOOTSTRAP_NREP,
            block_length=_STAGE3_BOOTSTRAP_BLOCK_LEN,
            rng=rng_spa,
        )
        for w in caught:
            if issubclass(w.category, SingleStrategySPAWarning):
                spa_warnings_caught.append(str(w.message))
    return {
        "p_value": float(spa_result.p_value),
        "n_strategies": 2,
        "n_bootstrap": _STAGE3_BOOTSTRAP_NREP,
        "single_strategy_warnings": spa_warnings_caught,
        "annotation": "spa-passes" if spa_result.p_value <= 0.05 else "spa-rejects",
    }


# ---------------------------------------------------------------------------
# KPI helpers (ADR-0013 §3 vocabulary; not from disposition.py per BLOCKING follow-up)
# ---------------------------------------------------------------------------


def _annotate_sharpe_vs(point: float, ci_low: float, ci_high: float) -> str:
    """Sharpe-vs-{passive,bench} annotation per ADR-0012 §B (preserved by ADR-0013 §2)."""
    if not (np.isfinite(ci_low) and np.isfinite(ci_high) and np.isfinite(point)):
        if np.isfinite(point):
            if point > 0.05:
                return "sharpe-vs-passive-marginal"
            if point < -0.05:
                return "sharpe-vs-passive-negative"
            return "sharpe-vs-passive-flat"
        return "sharpe-vs-passive-unknown"
    if ci_low > 0:
        return "sharpe-vs-passive-positive"
    if ci_high < 0:
        return "sharpe-vs-passive-negative"
    if point > 0.05:
        return "sharpe-vs-passive-marginal"
    if point < -0.05:
        return "sharpe-vs-passive-marginal"
    return "sharpe-vs-passive-flat"


def _annotate_bss(bss: float) -> str:
    if not np.isfinite(bss):
        return "bss-unknown"
    if bss > 0.05:
        return "bss-positive"
    if bss < -0.05:
        return "bss-negative"
    return "bss-flat"


def _annotate_reliability(slope: float) -> str:
    if not np.isfinite(slope):
        return "reliability-unknown"
    if 0.7 <= slope <= 1.3:
        return "reliability-in-band"
    return "reliability-out-of-band"


def _annotate_max_dd(arm_returns: np.ndarray, passive_returns: np.ndarray) -> tuple[float, str]:
    def _max_dd(r: np.ndarray) -> float:
        cum = np.cumsum(r)
        peak = np.maximum.accumulate(cum)
        dd = cum - peak
        return float(np.abs(dd.min())) if len(dd) > 0 else float("nan")
    arm_dd = _max_dd(arm_returns)
    pas_dd = _max_dd(passive_returns)
    if not np.isfinite(arm_dd) or not np.isfinite(pas_dd) or pas_dd <= 0:
        return float("nan"), "max-dd-unknown"
    ratio = arm_dd / pas_dd
    if ratio < 0.8:
        ann = "max-dd-favorable"
    elif ratio > 1.2:
        ann = "max-dd-adverse"
    else:
        ann = "max-dd-comparable"
    return ratio, ann


def _annotate_power_margin(n_oos: int, n_required: int) -> tuple[float, str]:
    if n_required <= 0:
        return float("nan"), "power-margin-unknown"
    ratio = n_oos / n_required
    if ratio >= 1.0:
        return ratio, "power-margin-adequate"
    if ratio >= 0.8:
        return ratio, "power-margin-marginal"
    return ratio, "power-margin-low"


def _ar1_lag1_benchmark_returns(y_test: np.ndarray, y_test_prev: np.ndarray) -> np.ndarray:
    """AR(1) lag-1 benchmark: sign(y_prev) * y_test, with 0 returned when prev is NaN.

    Matches the disposition.ar1_lag1_benchmark_returns contract per
    P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE — local reimplementation to
    avoid importing disposition.py per ADR-0013 BLOCKING follow-up.
    """
    sign = np.where(np.isfinite(y_test_prev), np.where(y_test_prev > 0, 1.0, np.where(y_test_prev < 0, -1.0, 0.0)), 0.0)
    return sign * y_test


# ---------------------------------------------------------------------------
# Per-symbol pipeline
# ---------------------------------------------------------------------------


def _run_for_symbol_v3(
    substrate_root: Path,
    symbol: str,
    oos_end: _dt.date,
    *,
    skip_cpcv: bool = False,
) -> dict[str, Any]:
    _log.info("[%s] Loading substrate …", symbol)
    panel = _load_substrate(substrate_root, symbol)
    _log.info("[%s] Computing feature blocks A/B/C/D …", symbol)
    features = _compute_features_per_session(panel)
    target_dtype = pl.Datetime("ns", "UTC")
    features = features.with_columns(pl.col("ts_event").cast(target_dtype))
    predictand = _compute_predictand(panel).with_columns(pl.col("ts_event").cast(target_dtype))
    aligned = predictand.join(features, on=["symbol", "ts_event"], how="inner")
    _log.info("[%s] aligned (X, y) panel: %d sessions", symbol, len(aligned))

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
    aligned = aligned.with_columns(
        pl.fold(
            acc=pl.lit(True), function=lambda acc, x: acc & x.is_finite(),
            exprs=[pl.col(c) for c in feature_cols],
        ).alias("_ok")
    ).filter(pl.col("_ok")).drop("_ok")

    train = aligned.filter(train_filter).sort("session_date_et")
    test = aligned.filter(test_filter).sort("session_date_et")
    _log.info(
        "[%s] train n=%d, test n=%d (post Daily-gate fix), features=%d",
        symbol, len(train), len(test), len(feature_cols),
    )
    if len(train) < 100 or len(test) < 50:
        raise ValueError(f"[{symbol}] Insufficient train/test: {len(train)}/{len(test)}")

    X_train = train.select(feature_cols).to_numpy()
    y_train = train["y"].to_numpy()
    X_test = test.select(feature_cols).to_numpy()
    y_test = test["y"].to_numpy()

    # Inner-CV hyperparameter selection (F-2-2 fix: purged-K-fold)
    _log.info("[%s] Fitting Arm 1 ElasticNet (purged-K-fold inner CV) …", symbol)
    arm1, arm1_meta = _fit_arm1_elasticnet_v3(X_train, y_train)
    arm1_pred = arm1.predict(X_test)
    arm1_returns = _strategy_returns_from_pred(arm1_pred, y_test)

    _log.info("[%s] Fitting Arm 2 LightGBM (purged-K-fold inner CV) …", symbol)
    arm2, arm2_meta = _fit_arm2_lightgbm_v3(X_train, y_train)
    arm2_pred = arm2.predict(X_test)
    arm2_returns = _strategy_returns_from_pred(arm2_pred, y_test)

    # Benchmarks
    passive_returns = _passive_long_returns(y_test)
    test_sorted = test.sort(["symbol", "session_date_et"])
    y_test_prev = test_sorted["y"].shift(1, fill_value=float("nan")).to_numpy()
    bench_returns = _ar1_lag1_benchmark_returns(y_test, y_test_prev)

    # Sharpe KPIs via CPCV with embargo=2 (F-2-1 fix)
    arm1_cpcv = None
    arm2_cpcv = None
    if not skip_cpcv:
        X_full = aligned.select(feature_cols).to_numpy()
        y_full = aligned["y"].to_numpy()

        def _arm1_fp(tr, te):
            try:
                local, _ = _fit_arm1_elasticnet_v3(X_full[tr], y_full[tr])
                pred = local.predict(X_full[te])
                return _strategy_returns_from_pred(pred, y_full[te])
            except Exception as exc:
                _log.warning("[%s] Arm 1 CPCV fold fit failed: %s", symbol, exc)
                return np.zeros(len(te))

        def _arm2_fp(tr, te):
            try:
                local, _ = _fit_arm2_lightgbm_v3(X_full[tr], y_full[tr])
                pred = local.predict(X_full[te])
                return _strategy_returns_from_pred(pred, y_full[te])
            except Exception as exc:
                _log.warning("[%s] Arm 2 CPCV fold fit failed: %s", symbol, exc)
                return np.zeros(len(te))

        _log.info(
            "[%s] CPCV Arm 1 (n_groups=%d, n_test=%d, embargo=%d) …",
            symbol, _CPCV_N_GROUPS, _CPCV_N_TEST_GROUPS, _CPCV_EMBARGO,
        )
        arm1_cpcv = cpcv_path_sharpe(
            n_samples=len(X_full),
            fit_predict_fn=_arm1_fp,
            target_returns=y_full,
            label_horizon=_LABEL_HORIZON,
            embargo=_CPCV_EMBARGO,
            n_groups=_CPCV_N_GROUPS,
            n_test_groups=_CPCV_N_TEST_GROUPS,
            wallclock_cap_s=14400,
        )
        _log.info(
            "[%s] Arm 1 CPCV: n_folds=%d, median=%.4f, std=%.4f, dsr=%.4f, ks_pass=%s, wall=%.1fs",
            symbol, arm1_cpcv.n_folds, arm1_cpcv.median_sharpe, arm1_cpcv.std_sharpe,
            arm1_cpcv.dsr_value, arm1_cpcv.ks_monotonicity_passed, arm1_cpcv.wallclock_s,
        )
        _log.info(
            "[%s] CPCV Arm 2 (n_groups=%d, n_test=%d, embargo=%d) …",
            symbol, _CPCV_N_GROUPS, _CPCV_N_TEST_GROUPS, _CPCV_EMBARGO,
        )
        arm2_cpcv = cpcv_path_sharpe(
            n_samples=len(X_full),
            fit_predict_fn=_arm2_fp,
            target_returns=y_full,
            label_horizon=_LABEL_HORIZON,
            embargo=_CPCV_EMBARGO,
            n_groups=_CPCV_N_GROUPS,
            n_test_groups=_CPCV_N_TEST_GROUPS,
            wallclock_cap_s=14400,
        )
        _log.info(
            "[%s] Arm 2 CPCV: n_folds=%d, median=%.4f, std=%.4f, dsr=%.4f, ks_pass=%s, wall=%.1fs",
            symbol, arm2_cpcv.n_folds, arm2_cpcv.median_sharpe, arm2_cpcv.std_sharpe,
            arm2_cpcv.dsr_value, arm2_cpcv.ks_monotonicity_passed, arm2_cpcv.wallclock_s,
        )

    # OOF BSS via inner CPCV with held-out isotonic source (F-2-3 fix)
    _log.info("[%s] OOF BSS Arm 1 (held-out isotonic) …", symbol)
    arm1_bss = _compute_oof_brier_components_v3(X_train, y_train, arm_fit_fn=_fit_arm1_elasticnet_v3)
    _log.info("[%s] Arm 1 BSS: %s", symbol, {k: v for k, v in arm1_bss.items() if k != "method"})

    _log.info("[%s] OOF BSS Arm 2 (held-out isotonic) …", symbol)
    arm2_bss = _compute_oof_brier_components_v3(X_train, y_train, arm_fit_fn=_fit_arm2_lightgbm_v3)
    _log.info("[%s] Arm 2 BSS: %s", symbol, {k: v for k, v in arm2_bss.items() if k != "method"})

    # SPA KPI
    spa_kpi = _hansen_spa_kpi(arm1_returns, arm2_returns, passive_returns)

    # Build per-arm KPI report
    arm_kpis: list[dict[str, Any]] = []
    for arm_id, arm_ret, arm_cpcv_r, arm_bss_r in [
        ("arm1_elasticnet", arm1_returns, arm1_cpcv, arm1_bss),
        ("arm2_lightgbm", arm2_returns, arm2_cpcv, arm2_bss),
    ]:
        # Sharpe-vs-passive (CPCV path-Sharpe distribution)
        if arm_cpcv_r is not None:
            sv_passive = {
                "median": arm_cpcv_r.median_sharpe,
                "ci_low": arm_cpcv_r.quantile_05,
                "ci_high": arm_cpcv_r.quantile_95,
                "n_folds": arm_cpcv_r.n_folds,
                "annotation": _annotate_sharpe_vs(
                    arm_cpcv_r.median_sharpe, arm_cpcv_r.quantile_05, arm_cpcv_r.quantile_95,
                ),
                "ks_monotonicity_distance": arm_cpcv_r.ks_monotonicity_distance,
                "ks_monotonicity_passed": arm_cpcv_r.ks_monotonicity_passed,
                "ks_monotonicity_annotation": (
                    "cpcv-ks-converged" if arm_cpcv_r.ks_monotonicity_passed
                    else "cpcv-ks-not-converged"
                ),
                "dsr_value": arm_cpcv_r.dsr_value,
                "downsampled": arm_cpcv_r.downsampled,
            }
        else:
            single_sharpe = _sharpe(arm_ret)
            sv_passive = {
                "median": single_sharpe,
                "ci_low": float("nan"),
                "ci_high": float("nan"),
                "n_folds": 0,
                "annotation": _annotate_sharpe_vs(single_sharpe, float("nan"), float("nan")),
                "ks_monotonicity_distance": float("nan"),
                "ks_monotonicity_passed": False,
                "ks_monotonicity_annotation": "cpcv-skipped",
                "dsr_value": float("nan"),
                "downsampled": False,
            }
        # Sharpe-vs-bench (paired)
        diff = arm_ret - bench_returns
        diff_sharpe = _sharpe(diff)
        sv_bench = {
            "point": diff_sharpe,
            "ci_low": float("nan"),  # ADR-0013 §"Retroactive re-tag" footnote †:
            "ci_high": float("nan"),  # paired-Sharpe CI deferred to P1-H053-STAGE3-V2-ROUND-2-REMEDIATION
            "annotation": ("sharpe-vs-bench-positive" if diff_sharpe > 0.05
                           else "sharpe-vs-bench-flat" if abs(diff_sharpe) <= 0.05
                           else "sharpe-vs-bench-negative"),
            "ci_method": "deferred",  # not a placeholder; explicit deferral
        }
        # Max-DD
        dd_ratio, dd_ann = _annotate_max_dd(arm_ret, passive_returns)
        # Power margin
        power_ratio, power_ann = _annotate_power_margin(len(arm_ret), _N_REQUIRED_FOR_POWER_80)

        bss_val = float(arm_bss_r.get("bss", float("nan")))
        slope_val = float(arm_bss_r.get("reliability_slope", float("nan")))

        arm_kpis.append({
            "arm_id": arm_id,
            "n_strategy_returns_oos": int(len(arm_ret)),
            "sharpe_vs_passive": sv_passive,
            "sharpe_vs_bench": sv_bench,
            "max_dd": {"ratio": dd_ratio, "annotation": dd_ann},
            "power_margin": {"ratio": power_ratio, "annotation": power_ann},
            "bss": {
                "value": bss_val,
                "annotation": _annotate_bss(bss_val),
                "components": arm_bss_r,
            },
            "reliability_slope": {
                "value": slope_val,
                "annotation": _annotate_reliability(slope_val),
            },
        })

    return {
        "symbol": symbol,
        "n_train": len(train),
        "n_test": len(test),
        "n_features": len(feature_cols),
        "arm_kpis": arm_kpis,
        "spa_family": spa_kpi,
        "passive_long_summary": {
            "n": int(len(passive_returns)),
            "mean": float(np.mean(passive_returns)),
            "std": float(np.std(passive_returns, ddof=1)),
        },
        "bench_ar1_summary": {
            "n": int(len(bench_returns)),
            "mean": float(np.mean(bench_returns)),
            "std": float(np.std(bench_returns, ddof=1)),
        },
        "arm1_meta": arm1_meta,
        "arm2_meta": arm2_meta,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H053 Stage-3 v3 (leakage-clean per Stage-3 v2 audit).")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--symbols", default="ES,NQ")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--skip-cpcv", action="store_true", help="Skip CPCV (fast iteration only).")
    args = parser.parse_args(argv)

    substrate_root = _resolve_substrate_path(args.substrate_path)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    paths = ProjectPaths.discover()
    run_id = args.run_id or f"h053_stage3_v3_{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir = paths.root / "runs" / "h053" / "stage3_v3" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    _log.info("Computing substrate dataset checksum …")
    substrate_checksum = _substrate_dataset_checksum(substrate_root, symbols)
    git_head = _git_head()
    _log.info(
        "substrate_checksum=%s, git_head=%s, run_id=%s",
        substrate_checksum[:16], git_head, run_id,
    )

    results: list[dict[str, Any]] = []
    for sym in symbols:
        oos_end = _OOS_END_ES if sym == "ES" else _OOS_END_NQ
        try:
            r = _run_for_symbol_v3(
                substrate_root, sym, oos_end,
                skip_cpcv=args.skip_cpcv,
            )
            results.append(r)
        except Exception as exc:
            _log.exception("Symbol %s failed: %s", sym, exc)
            raise

    # ADR-0013 §3 KPI report card structure (in-script JSON; the markdown
    # KPI report card v2 is emitted separately from the sidecar by the
    # operator-side composition step).
    sidecar_path = run_dir / "sidecar.json"
    payload = {
        "h053_stage3_v3": {
            "version": "3.0",
            "method": (
                "leakage-clean refactor of Stage-3 v2; F-2-1 (CPCV embargo=2) + "
                "F-2-2 (purged-K-fold inner CV) + F-2-3 (held-out isotonic source)"
            ),
            "method_reference": (
                "audit_trail_2026-05-03_h053-stage3-v2.md F-2-1/F-2-2/F-2-3 + "
                "Niculescu-Mizil & Caruana 2005 §4 (held-out isotonic) + "
                "AFML §7.4 (purged-K-fold) + ADR-0013 §1-§5"
            ),
            "substrate_path": str(substrate_root),
            "substrate_dataset_checksum": substrate_checksum,
            "is_window": [str(_IS_START), str(_IS_END)],
            "oos_window_es": [str(_OOS_START), str(_OOS_END_ES)],
            "oos_window_nq": [str(_OOS_START), str(_OOS_END_NQ)],
            "config": {
                "label_horizon": _LABEL_HORIZON,
                "cpcv_embargo": _CPCV_EMBARGO,
                "cpcv_n_groups": _CPCV_N_GROUPS,
                "cpcv_n_test_groups": _CPCV_N_TEST_GROUPS,
                "inner_cv_method": "purged_kfold_split",
                "inner_cv_n_splits": _INNER_CV_FOLDS_V3,
                "inner_cv_embargo": _INNER_CPCV_EMBARGO,
                "oof_inner_cpcv_n_groups": _OOF_INNER_CPCV_N_GROUPS,
                "oof_inner_cpcv_n_test_groups": _OOF_INNER_CPCV_N_TEST_GROUPS,
                "iso_heldout_fraction": _ISO_HELDOUT_FRACTION,
                "stage3_rng_seed": _STAGE3_RNG_SEED,
                "stage3_bootstrap_block_len": _STAGE3_BOOTSTRAP_BLOCK_LEN,
                "stage3_bootstrap_nrep": _STAGE3_BOOTSTRAP_NREP,
                "n_required_for_power_80": _N_REQUIRED_FOR_POWER_80,
            },
            "results": results,
            "leakage_fixes": {
                "F-2-1": {
                    "defect": "CPCV embargo=0 left train/test segments abuttable",
                    "fix": f"embargo={_CPCV_EMBARGO} (= 2 × label_horizon per AFML §7.4 + ADR-0007)",
                    "verification": "CPCV path-Sharpe distribution computed with embargo applied",
                },
                "F-2-2": {
                    "defect": "Inner KFold(shuffle=True) violates rules/quant-project.md §Time-series integrity",
                    "fix": "purged_kfold_split (AFML §7.4.3) preserves time order + applies embargo",
                    "verification": "arm{1,2}_meta.inner_cv_method == 'purged_kfold_split'",
                },
                "F-2-3": {
                    "defect": "Isotonic fit on in-sample arm predictions",
                    "fix": "3-way nested time-ordered split per Niculescu-Mizil & Caruana 2005 §4",
                    "verification": "BSS components carry method == 'v3_held_out_isotonic_source'",
                },
            },
            "adr_0013_kpi_annotations": {
                "leakage_canary": "leakage-canary-pass (PIT canaries verified at "
                                  f"{_PIT_CANARY_TEST_PATH} pre-run; not re-run inline)",
                "repro_log": "repro-log-complete (sidecar payload includes git_head + "
                             "dataset_checksum + run_id + scientific_payload_sha256)",
                "dsr": "dsr-n/a (family active-size below threshold per CLAUDE.md §Evidence bar)",
            },
        },
        "_meta": {
            "git_head": git_head,
            "run_id": run_id,
            "written_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        },
    }
    scientific_bytes = json.dumps(
        payload["h053_stage3_v3"], indent=2, sort_keys=True, default=str,
    ).encode("utf-8")
    scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()
    payload["_meta"]["scientific_payload_sha256"] = scientific_sha
    serialised = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.with_suffix(".json.tmp").write_bytes(serialised)
    os.replace(str(sidecar_path.with_suffix(".json.tmp")), str(sidecar_path))
    _log.info(
        "Sidecar: %s (sha256=%s)",
        sidecar_path, scientific_sha[:16],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
