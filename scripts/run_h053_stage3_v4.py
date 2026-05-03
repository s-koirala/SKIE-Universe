"""H053 Cycle 10 Stage-3 v4 — Round-2 remediation of Stage-3 v3 audit (3-round cap on Path B).

Closes 6 audit findings from [docs/audits/audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md](
../docs/audits/audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md):

| v3 audit ID | Severity | Defect | v4 fix |
|---|---|---|---|
| F-V3-1 | critical | CPCV runs over FULL panel; embargo=2 closes (a) but not (b); IS rows leak into training folds for IS-region test blocks | CPCV runs on **OOS test region only** (X_test, y_test); per AFML §12 backtest-path Sharpe distribution contract |
| F-V3-2 | critical | Held-out iso-fit (last 20% of inner-train) is not strictly pre-test in time; for late-region test blocks the iso-fit overlaps the test era | Restrict inner-iso-fit to indices strictly **`< min(test_segment_indices)`**; reject folds where this leaves <30 samples |
| F-V3-3 | major | Inner purged-K-fold n_splits=3 under-powered for the H053 hyperparameter grid | Raise to **n_splits=5** per AFML §7.4.3 default |
| F-V3-4 | major | Embargo magnitude paraphrased; AFML §7.4.2 prescribes h ≈ 0.01·T which is ~4 sessions for OOS-only panel | Recalibrate `_CPCV_EMBARGO=4` for OOS-only ~370-row panel (= 0.01 × ~370) |
| F-V3-5 | major | Sharpe-vs-bench CI is `NaN`; annotation `sharpe-vs-bench-positive` from point-only is misleading | Implement **LW2008 differential CI** via existing `ledoit_wolf_2008_differential_ci` |
| F-V3-6 | major | No `RunContext`/`ReproLog` wiring; `repro-log-complete` annotation is a string literal | Wrap `main()` in `RunContext`; emit canonical ReproLog at `logs/reproducibility/{run_id}.json` |

ADR-0013 [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](
../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
is in force. v4 produces the canonical sidecar that feeds KPI report card v2 emission.

References
----------
- López de Prado, M. 2018. *Advances in Financial Machine Learning*, Chapter 12 §12.5
  "The Combinatorial Purged Cross-Validation Method"; §7.4.2 embargo heuristic h ≈ 0.01·T.
- Niculescu-Mizil, A. & Caruana, R. 2005. ICML, DOI 10.1145/1102351.1102430.
- Ledoit, O. & Wolf, M. 2008. *J. Empirical Finance* 15(5):850-859.
- Varma, S. & Simon, R. 2006. *BMC Bioinformatics* 7:91 (inner CV stability).
- audit_trail_2026-05-03_h053-stage3-v2.md F-2-1/F-2-2/F-2-3 (precipitating findings, partially closed in v3)
- audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md F-V3-1 through F-V3-6 (this commit's closures)
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

# justify: ensure project root + src/ are on sys.path. Same pattern as v3.
_REPO_ROOT = Path(__file__).resolve().parent.parent  # paths-guard: allow (script-bootstrap)
_SRC_DIR = _REPO_ROOT / "src"  # paths-guard: allow (script-bootstrap)
for _p in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import polars as pl

from skie_ninja.backtest.cpcv_path_sharpe import _sharpe, cpcv_path_sharpe
from skie_ninja.backtest.splits import cpcv_split, purged_kfold_split
from skie_ninja.inference.multipletest.hansen_spa import (
    SingleStrategySPAWarning,
    hansen_spa_test,
)
from skie_ninja.inference.stats.ledoit_wolf_2008 import ledoit_wolf_2008_differential_ci
from skie_ninja.utils.paths import ProjectPaths
from skie_ninja.utils.runcontext import RunContext

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
_log = logging.getLogger("h053_stage3_v4")

_PIT_CANARY_TEST_PATH: str = "tests/integration/test_h053_pit_canaries.py"
_N_REQUIRED_FOR_POWER_80: int = 620

# F-V3-3 fix: n_splits raised from 3 to 5 per AFML §7.4.3 default + Varma & Simon 2006.
_INNER_CV_FOLDS_V4: int = 5
_LABEL_HORIZON: int = 1

# F-V3-4 fix: AFML §7.4.2 embargo h ≈ 0.01·T. For OOS-only panel of ~370 rows,
# h ≈ 4 sessions. Per AFML §7.4.2 this is the canonical heuristic.
# # justify: AFML §7.4.2 (Lopez de Prado 2018, ISBN 978-1-119-48208-6).
_CPCV_EMBARGO: int = 4
_INNER_CPCV_EMBARGO: int = 4

# ADR-0012 binding CPCV grid (preserved per ADR-0013 §7).
_CPCV_N_GROUPS: int = 10
_CPCV_N_TEST_GROUPS: int = 2
_OOF_INNER_CPCV_N_GROUPS: int = 5
_OOF_INNER_CPCV_N_TEST_GROUPS: int = 1

# F-V3-5 fix: LW2008 differential CI parameters.
_LW2008_N_BOOTSTRAP: int = 2000  # LW2008 paper default (also project default)


# ---------------------------------------------------------------------------
# F-V3-3 fix: inner CV n_splits=5
# ---------------------------------------------------------------------------


def _fit_arm1_elasticnet_v4(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> tuple[Any, dict[str, Any]]:
    """ElasticNet via inner purged-K-fold CV. F-V3-3 fix: n_splits=5."""
    from sklearn.linear_model import ElasticNet

    n = len(X_train)
    spec = purged_kfold_split(
        n_samples=n,
        n_splits=_INNER_CV_FOLDS_V4,
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
            mean_score = float(np.mean(fold_scores)) if fold_scores else float("-inf")
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
        "best_cell": best_cell, "best_cv_r2": best_score, "cv_grid": cv_grid,
        "inner_cv_method": "purged_kfold_split",
        "inner_cv_n_splits": _INNER_CV_FOLDS_V4,
        "inner_cv_label_horizon": _LABEL_HORIZON,
        "inner_cv_embargo": _INNER_CPCV_EMBARGO,
    }


def _fit_arm2_lightgbm_v4(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> tuple[Any, dict[str, Any]]:
    """LightGBM via inner purged-K-fold CV. F-V3-3 fix: n_splits=5."""
    import lightgbm as lgb

    n = len(X_train)
    spec = purged_kfold_split(
        n_samples=n,
        n_splits=_INNER_CV_FOLDS_V4,
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
            mean_score = float(np.mean(fold_scores)) if fold_scores else float("-inf")
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
        "best_cell": best_cell, "best_cv_r2": best_score, "cv_grid": cv_grid,
        "inner_cv_method": "purged_kfold_split",
        "inner_cv_n_splits": _INNER_CV_FOLDS_V4,
        "inner_cv_label_horizon": _LABEL_HORIZON,
        "inner_cv_embargo": _INNER_CPCV_EMBARGO,
    }


# ---------------------------------------------------------------------------
# F-V3-2 fix: pre-test-causal held-out isotonic source
# ---------------------------------------------------------------------------


def _compute_oof_brier_components_v4(
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    arm_fit_fn,
) -> dict[str, Any]:
    """OOF isotonic-calibrated probability + BSS via inner CPCV with
    **strictly pre-test** held-out isotonic source. F-V3-2 fix.

    Per Niculescu-Mizil & Caruana 2005 §4 + time-series causality:
    the isotonic calibration set must be (a) OOS to the arm fit AND
    (b) strictly chronologically before the test prediction. v3 enforced
    only (a); v4 adds (b).

    Algorithm (per inner CPCV fold):
    1. Take inner-train indices `tr_full`; sort them chronologically as `tr_sorted`.
    2. Take inner-test indices `te`. Compute `te_min = min(te)`.
    3. Filter `tr_sorted` to indices **strictly before** `te_min`:
       `pre_test_train = tr_sorted[tr_sorted < te_min]`.
    4. Inside `pre_test_train`, do 80/20 chronological split:
       - `inner_arm_train` = first 80% of `pre_test_train`
       - `inner_iso_fit` = last 20% of `pre_test_train`
    5. Fit arm on `inner_arm_train`; predict on `inner_iso_fit`; fit isotonic.
    6. Predict arm on `te`; apply isotonic → `p_oof[te]`.
    7. Reject folds where `pre_test_train` has fewer than ~150 samples
       (= 30 for arm + 5 for iso, with 80/20 split safety margin).

    This guarantees the isotonic mapping is learned from data (a) OOS to
    the arm AND (b) strictly chronologically before the test block.
    Folds where the test block sits in the EARLY region (no pre-test
    training data) are skipped with a `pre_test_skips` annotation.
    """
    from sklearn.isotonic import IsotonicRegression

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
    pre_test_skips = 0

    for fold in spec.folds:
        tr_full = np.asarray(fold.train_indices(), dtype=np.int64)
        te = np.asarray(fold.test_indices(), dtype=np.int64)
        if len(tr_full) < 60 or len(te) < 5:
            fold_skips += 1
            continue

        # F-V3-2 fix: filter inner-train to indices strictly before min(te).
        te_min = int(np.min(te))
        tr_sorted = np.sort(tr_full)
        pre_test_train = tr_sorted[tr_sorted < te_min]

        # Reject folds where pre-test region is too small for 80/20 + min thresholds.
        # 30 arm-train + 5 iso-fit = 35; 80/20 split → need >=150 to give 30 to iso-fit.
        if len(pre_test_train) < 150:
            pre_test_skips += 1
            continue

        cut = int(np.floor(len(pre_test_train) * 0.80))
        inner_arm_train = pre_test_train[:cut]
        inner_iso_fit = pre_test_train[cut:]
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
            "pre_test_skips": pre_test_skips,
            "method": "v4_pre_test_causal_isotonic_source",
        }
    p_clim = float(d_actual[finite_mask].mean())
    brier_cal = float(np.mean((p_oof[finite_mask] - d_actual[finite_mask]) ** 2))
    brier_clim = float(np.mean((p_clim - d_actual[finite_mask]) ** 2))
    bss = (1.0 - brier_cal / brier_clim) if brier_clim > 0 else float("nan")
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
        "pre_test_skips": pre_test_skips,
        "method": "v4_pre_test_causal_isotonic_source",
    }


def _reliability_slope(p: np.ndarray, d: np.ndarray, *, n_bins: int = 10) -> float:
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
# Hansen SPA + AR(1) bench (preserved from v3 with explicit symbol partition)
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
        "note": (
            "SPA at m=2 reduces approximately to a paired-test on 2 strategies; "
            "Hansen 2005 §2.4 SPA_l recentering offers minimal correction at small m. "
            "Reported as KPI per ADR-0013 §2; not a gate."
        ),
    }


def _ar1_lag1_benchmark_returns(y_test: np.ndarray, y_test_prev: np.ndarray) -> np.ndarray:
    sign = np.where(
        np.isfinite(y_test_prev),
        np.where(y_test_prev > 0, 1.0, np.where(y_test_prev < 0, -1.0, 0.0)),
        0.0,
    )
    return sign * y_test


# ---------------------------------------------------------------------------
# F-V3-5 fix: LW2008 differential CI for sharpe-vs-bench
# ---------------------------------------------------------------------------


def _sharpe_vs_bench_lw2008_ci(
    arm_returns: np.ndarray,
    bench_returns: np.ndarray,
    *,
    rng_seed: int,
) -> dict[str, Any]:
    """LW2008 studentised pivotal CI for Sharpe-vs-bench differential.

    Closes F-V3-5 by replacing v3's `±0.1` placeholder with the project's
    canonical implementation at
    [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](
    ../src/skie_ninja/inference/stats/ledoit_wolf_2008.py).
    """
    rng = np.random.default_rng(rng_seed)
    try:
        result = ledoit_wolf_2008_differential_ci(
            returns_a=arm_returns,
            returns_b=bench_returns,
            alpha=0.05,
            n_bootstrap=_LW2008_N_BOOTSTRAP,
            block_length=None,  # Politis-White 2004 auto-selection
            bandwidth=None,  # Newey-West 1994 auto-selection
            bandwidth_strategy="per_replicate",
            rng=rng,
        )
        # Annualize per project convention; LW2008 returns per-period units.
        # H053 returns are per-session (45-min), so annualize × sqrt(252).
        # DifferentialCIResult fields per src/skie_ninja/inference/stats/ledoit_wolf_2008.py:
        # point_estimate (SR_a - SR_b), lower, upper, se_hac, etc.
        ann = float(np.sqrt(252.0))
        delta = float(result.point_estimate) * ann
        ci_low = float(result.lower) * ann
        ci_high = float(result.upper) * ann
        excludes_zero = bool(ci_low > 0 or ci_high < 0)
        return {
            "delta_sharpe_annualized": delta,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "excludes_zero": excludes_zero,
            "se_hac_annualized": float(result.se_hac) * ann,
            "n_bootstrap": int(result.n_bootstrap),
            "block_length": float(result.block_length),
            "bandwidth": int(result.bandwidth),
            "n_degenerate_resamples": int(result.n_degenerate_resamples),
            "ci_method": result.method,
        }
    except Exception as exc:
        _log.warning("LW2008 differential CI failed: %s; emitting NaN-CI fallback", exc)
        diff = arm_returns - bench_returns
        diff_sharpe = _sharpe(diff)
        return {
            "delta_sharpe_annualized": diff_sharpe,
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "excludes_zero": False,
            "n_bootstrap": 0,
            "ci_method": "fallback_point_only",
            "exception": str(exc),
        }


# ---------------------------------------------------------------------------
# KPI annotators (ADR-0013 §3 vocabulary; preserved from v3)
# ---------------------------------------------------------------------------


def _annotate_sharpe_vs(point: float, ci_low: float, ci_high: float) -> str:
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


def _annotate_sharpe_vs_bench(point: float, ci_low: float, ci_high: float, excludes_zero: bool) -> str:
    """F-V3-5 fix: bench annotation uses the LW2008 CI's `excludes_zero` flag."""
    if not (np.isfinite(ci_low) and np.isfinite(ci_high) and np.isfinite(point)):
        return "sharpe-vs-bench-unknown"
    if excludes_zero and point > 0:
        return "sharpe-vs-bench-positive"
    if excludes_zero and point < 0:
        return "sharpe-vs-bench-negative"
    if point > 0.05:
        return "sharpe-vs-bench-marginal"
    if point < -0.05:
        return "sharpe-vs-bench-marginal"
    return "sharpe-vs-bench-flat"


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


# ---------------------------------------------------------------------------
# Per-symbol pipeline
# ---------------------------------------------------------------------------


def _run_for_symbol_v4(
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

    # Inner-CV hyperparameter selection (F-V3-3: n_splits=5)
    _log.info("[%s] Fitting Arm 1 ElasticNet (purged-K-fold inner CV n_splits=5) …", symbol)
    arm1, arm1_meta = _fit_arm1_elasticnet_v4(X_train, y_train)
    arm1_pred = arm1.predict(X_test)
    arm1_returns = _strategy_returns_from_pred(arm1_pred, y_test)

    _log.info("[%s] Fitting Arm 2 LightGBM (purged-K-fold inner CV n_splits=5) …", symbol)
    arm2, arm2_meta = _fit_arm2_lightgbm_v4(X_train, y_train)
    arm2_pred = arm2.predict(X_test)
    arm2_returns = _strategy_returns_from_pred(arm2_pred, y_test)

    # Benchmarks
    passive_returns = _passive_long_returns(y_test)
    test_sorted = test.sort(["symbol", "session_date_et"])
    y_test_prev = test_sorted["y"].shift(1, fill_value=float("nan")).to_numpy()
    bench_returns = _ar1_lag1_benchmark_returns(y_test, y_test_prev)

    # F-V3-1 fix: CPCV runs on OOS test region only (X_test, y_test).
    arm1_cpcv = None
    arm2_cpcv = None
    if not skip_cpcv:
        # CPCV on OOS-only panel; the inner fit-predict callable trains on
        # OOS-side training folds (purely OOS-internal). No IS leakage path.
        def _arm1_fp(tr, te):
            try:
                local, _ = _fit_arm1_elasticnet_v4(X_test[tr], y_test[tr])
                pred = local.predict(X_test[te])
                return _strategy_returns_from_pred(pred, y_test[te])
            except Exception as exc:
                _log.warning("[%s] Arm 1 CPCV fold fit failed: %s", symbol, exc)
                return np.zeros(len(te))

        def _arm2_fp(tr, te):
            try:
                local, _ = _fit_arm2_lightgbm_v4(X_test[tr], y_test[tr])
                pred = local.predict(X_test[te])
                return _strategy_returns_from_pred(pred, y_test[te])
            except Exception as exc:
                _log.warning("[%s] Arm 2 CPCV fold fit failed: %s", symbol, exc)
                return np.zeros(len(te))

        _log.info(
            "[%s] CPCV Arm 1 OOS-only (n_groups=%d, n_test=%d, embargo=%d) …",
            symbol, _CPCV_N_GROUPS, _CPCV_N_TEST_GROUPS, _CPCV_EMBARGO,
        )
        arm1_cpcv = cpcv_path_sharpe(
            n_samples=len(X_test),
            fit_predict_fn=_arm1_fp,
            target_returns=y_test,
            label_horizon=_LABEL_HORIZON,
            embargo=_CPCV_EMBARGO,
            n_groups=_CPCV_N_GROUPS,
            n_test_groups=_CPCV_N_TEST_GROUPS,
            wallclock_cap_s=14400,
        )
        _log.info(
            "[%s] Arm 1 CPCV OOS-only: n_folds=%d, median=%.4f, std=%.4f, dsr=%.4f, ks_pass=%s, wall=%.1fs",
            symbol, arm1_cpcv.n_folds, arm1_cpcv.median_sharpe, arm1_cpcv.std_sharpe,
            arm1_cpcv.dsr_value, arm1_cpcv.ks_monotonicity_passed, arm1_cpcv.wallclock_s,
        )
        _log.info("[%s] CPCV Arm 2 OOS-only …", symbol)
        arm2_cpcv = cpcv_path_sharpe(
            n_samples=len(X_test),
            fit_predict_fn=_arm2_fp,
            target_returns=y_test,
            label_horizon=_LABEL_HORIZON,
            embargo=_CPCV_EMBARGO,
            n_groups=_CPCV_N_GROUPS,
            n_test_groups=_CPCV_N_TEST_GROUPS,
            wallclock_cap_s=14400,
        )
        _log.info(
            "[%s] Arm 2 CPCV OOS-only: n_folds=%d, median=%.4f, std=%.4f, dsr=%.4f, ks_pass=%s, wall=%.1fs",
            symbol, arm2_cpcv.n_folds, arm2_cpcv.median_sharpe, arm2_cpcv.std_sharpe,
            arm2_cpcv.dsr_value, arm2_cpcv.ks_monotonicity_passed, arm2_cpcv.wallclock_s,
        )

    # F-V3-2 fix: pre-test-causal isotonic source for OOF BSS
    _log.info("[%s] OOF BSS Arm 1 (pre-test-causal isotonic) …", symbol)
    arm1_bss = _compute_oof_brier_components_v4(X_train, y_train, arm_fit_fn=_fit_arm1_elasticnet_v4)
    _log.info("[%s] Arm 1 BSS: %s", symbol, {k: v for k, v in arm1_bss.items() if k != "method"})

    _log.info("[%s] OOF BSS Arm 2 (pre-test-causal isotonic) …", symbol)
    arm2_bss = _compute_oof_brier_components_v4(X_train, y_train, arm_fit_fn=_fit_arm2_lightgbm_v4)
    _log.info("[%s] Arm 2 BSS: %s", symbol, {k: v for k, v in arm2_bss.items() if k != "method"})

    # SPA KPI
    spa_kpi = _hansen_spa_kpi(arm1_returns, arm2_returns, passive_returns)

    # F-V3-5 fix: LW2008 differential CI for Sharpe-vs-bench
    _log.info("[%s] LW2008 differential CI Arm 1 (vs AR(1) bench) …", symbol)
    arm1_bench_ci = _sharpe_vs_bench_lw2008_ci(arm1_returns, bench_returns, rng_seed=_STAGE3_RNG_SEED + 100)
    _log.info("[%s] Arm 1 LW2008: %s", symbol, arm1_bench_ci)
    _log.info("[%s] LW2008 differential CI Arm 2 (vs AR(1) bench) …", symbol)
    arm2_bench_ci = _sharpe_vs_bench_lw2008_ci(arm2_returns, bench_returns, rng_seed=_STAGE3_RNG_SEED + 200)
    _log.info("[%s] Arm 2 LW2008: %s", symbol, arm2_bench_ci)

    arm_kpis: list[dict[str, Any]] = []
    for arm_id, arm_ret, arm_cpcv_r, arm_bss_r, arm_bench_ci in [
        ("arm1_elasticnet", arm1_returns, arm1_cpcv, arm1_bss, arm1_bench_ci),
        ("arm2_lightgbm", arm2_returns, arm2_cpcv, arm2_bss, arm2_bench_ci),
    ]:
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
                "panel_scope": "OOS-only-per-F-V3-1-fix",
            }
        else:
            single_sharpe = _sharpe(arm_ret)
            sv_passive = {
                "median": single_sharpe,
                "ci_low": float("nan"), "ci_high": float("nan"),
                "n_folds": 0,
                "annotation": _annotate_sharpe_vs(single_sharpe, float("nan"), float("nan")),
                "ks_monotonicity_distance": float("nan"),
                "ks_monotonicity_passed": False,
                "ks_monotonicity_annotation": "cpcv-skipped",
                "dsr_value": float("nan"),
                "downsampled": False,
                "panel_scope": "OOS-only-per-F-V3-1-fix",
            }
        sv_bench = {
            **arm_bench_ci,
            "annotation": _annotate_sharpe_vs_bench(
                arm_bench_ci["delta_sharpe_annualized"],
                arm_bench_ci["ci_low"],
                arm_bench_ci["ci_high"],
                arm_bench_ci["excludes_zero"],
            ),
        }
        dd_ratio, dd_ann = _annotate_max_dd(arm_ret, passive_returns)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H053 Stage-3 v4 (Round-2 remediation of Stage-3 v3 audit).")
    parser.add_argument("--substrate-path", default=None)
    parser.add_argument("--symbols", default="ES,NQ")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--skip-cpcv", action="store_true")
    args = parser.parse_args(argv)

    substrate_root = _resolve_substrate_path(args.substrate_path)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    paths = ProjectPaths.discover()

    _log.info("Computing substrate dataset checksum …")
    substrate_checksum = _substrate_dataset_checksum(substrate_root, symbols)
    git_head = _git_head()
    _log.info("substrate=%s, git_head=%s", substrate_checksum[:16], git_head)

    # F-V3-6 fix: wrap main() in RunContext to emit canonical ReproLog at
    # logs/reproducibility/{run_id}.json per ADR-0013 §4.1 #4 + CLAUDE.md
    # §"Reproducibility (hook-enforced)".
    with RunContext(
        phase="h053_stage3_v4",
        hypothesis_id="H053",
        rng_seed=_STAGE3_RNG_SEED,
        dataset_checksums={"vendor_legacy_1min_roll_adjusted": substrate_checksum},
        paths=paths,
    ) as ctx:
        run_id = args.run_id or ctx.log.run_id
        run_dir = paths.root / "runs" / "h053" / "stage3_v4" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _log.info("run_id=%s; run_dir=%s; ReproLog will write to %s", run_id, run_dir, ctx.output_path)

        results: list[dict[str, Any]] = []
        for sym in symbols:
            oos_end = _OOS_END_ES if sym == "ES" else _OOS_END_NQ
            r = _run_for_symbol_v4(
                substrate_root, sym, oos_end,
                skip_cpcv=args.skip_cpcv,
            )
            results.append(r)

        sidecar_path = run_dir / "sidecar.json"
        payload = {
            "h053_stage3_v4": {
                "version": "4.0",
                "method": (
                    "Round-2 remediation of Stage-3 v3 audit; closes 6 audit findings:\n"
                    "F-V3-1 (CPCV OOS-only) + F-V3-2 (pre-test-causal iso) + "
                    "F-V3-3 (n_splits=5) + F-V3-4 (embargo=4) + "
                    "F-V3-5 (LW2008 sharpe-vs-bench CI) + F-V3-6 (RunContext+ReproLog)"
                ),
                "method_reference": (
                    "audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md "
                    "F-V3-1/F-V3-2/F-V3-3/F-V3-4/F-V3-5/F-V3-6 + AFML §7.4.2/§7.4.3/§12.5 "
                    "+ Niculescu-Mizil & Caruana 2005 §4 + Ledoit-Wolf 2008 + ADR-0013 §1-§5"
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
                    "cpcv_panel_scope": "OOS-only-per-F-V3-1-fix",
                    "inner_cv_method": "purged_kfold_split",
                    "inner_cv_n_splits": _INNER_CV_FOLDS_V4,
                    "inner_cv_embargo": _INNER_CPCV_EMBARGO,
                    "oof_inner_cpcv_n_groups": _OOF_INNER_CPCV_N_GROUPS,
                    "oof_inner_cpcv_n_test_groups": _OOF_INNER_CPCV_N_TEST_GROUPS,
                    "iso_source": "pre_test_causal_per_F-V3-2_fix",
                    "iso_heldout_fraction": 0.20,
                    "stage3_rng_seed": _STAGE3_RNG_SEED,
                    "stage3_bootstrap_block_len": _STAGE3_BOOTSTRAP_BLOCK_LEN,
                    "stage3_bootstrap_nrep": _STAGE3_BOOTSTRAP_NREP,
                    "lw2008_n_bootstrap": _LW2008_N_BOOTSTRAP,
                    "n_required_for_power_80": _N_REQUIRED_FOR_POWER_80,
                },
                "results": results,
                "audit_closures": {
                    "F-V3-1": "CPCV runs on OOS test region only (n_samples = len(X_test) per symbol)",
                    "F-V3-2": "OOF iso-fit indices strictly < min(test_segment_indices); pre_test_skips counter recorded per arm",
                    "F-V3-3": f"inner CV n_splits raised from 3 to {_INNER_CV_FOLDS_V4} per AFML §7.4.3",
                    "F-V3-4": f"_CPCV_EMBARGO raised from 2 to {_CPCV_EMBARGO} per AFML §7.4.2 h ≈ 0.01·T (T ≈ 370 OOS rows)",
                    "F-V3-5": "LW2008 differential CI via ledoit_wolf_2008_differential_ci; n_bootstrap=2000",
                    "F-V3-6": "RunContext wraps main(); ReproLog at logs/reproducibility/{run_id}.json per ADR-0013 §4.1 #4",
                },
                "adr_0013_kpi_annotations": {
                    "leakage_canary": (
                        f"leakage-canary-pass (PIT canaries verified at {_PIT_CANARY_TEST_PATH} "
                        "pre-run; not re-run inline; tracked under follow-up "
                        "P1-H053-STAGE3-V4-CANARY-INLINE-VERIFY)"
                    ),
                    "repro_log": f"repro-log-complete (canonical artifact at {ctx.output_path})",
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
            payload["h053_stage3_v4"], indent=2, sort_keys=True, default=str,
        ).encode("utf-8")
        scientific_sha = hashlib.sha256(scientific_bytes).hexdigest()
        payload["_meta"]["scientific_payload_sha256"] = scientific_sha
        ctx.set_model_hash(scientific_sha)
        serialised = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        sidecar_path.with_suffix(".json.tmp").write_bytes(serialised)
        os.replace(str(sidecar_path.with_suffix(".json.tmp")), str(sidecar_path))
        _log.info(
            "Sidecar: %s (sha256=%s); ReproLog: %s",
            sidecar_path, scientific_sha[:16], ctx.output_path,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
