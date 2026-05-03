"""Diagnostic: why does ES Arm 2 LightGBM produce near-constant probabilities after isotonic?

Per [reports/h053/stage3_v3_full_disposition.md](../reports/h053/stage3_v3_full_disposition.md)
+ [docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md](../docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md):
the H053 v3 binding disposition is `calibration-failed; paper_trade_eligible=False`
on all 4 arms, but ES Arm 2 LightGBM produces positive Sharpe on 81% of 16
walk-forward grid cells (median +0.04). Reliability slope point estimate is -0.04
(near-constant after isotonic); the question this diagnostic answers is:

1. Are the LightGBM RAW scores (pre-calibration) near-constant, OR does isotonic
   over-smooth them?
2. Does longer N_cal (full IS train fold instead of inner-CV-fold subset) recover
   the reliability slope toward 1.0?
3. Does beta calibration (Kull et al. 2017) outperform isotonic on this surface?
4. Is the directional skill (positive Sharpe) preserved under any calibrator that
   passes the binding gate?

Findings inform the operator decision per ADR-0014 §8 (NEVER ARCHIVE
AUTONOMOUSLY). Possible operator dispositions: keep H053 in
lifecycle_state=active-investigation (default per ADR-0014 §4), spawn a
successor hypothesis with an amended calibrator per ADR-0012 §"Frozen
pre-registration amendment" §1-§7 immutable rule, or — if the operator
explicitly chooses — emit `archive(null, <reason>)` with the full evidence
package per ADR-0014 §8. Claude SHALL NOT propose archive autonomously.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# justify: ensure project root on sys.path  # paths-guard: allow (script-bootstrap)
_REPO_ROOT = Path(__file__).resolve().parent.parent  # paths-guard: allow (script-bootstrap)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import polars as pl

from skie_ninja.inference.calibration import (
    binary_brier_skill_score,
    binary_bss_bootstrap_ci,
    fit_beta_calibration,
    fit_calibrator,
    predict_beta_calibration,
    predict_calibrated,
    reliability_slope_point,
    reliability_slope_bootstrap_ci,
    select_calibrator,
)
from scripts.run_h053_stage3_full import (
    _IS_END,
    _IS_START,
    _OOS_END_ES,
    _OOS_START,
    _STAGE3_RNG_SEED,
    _compute_features_per_session,
    _compute_predictand,
    _load_substrate,
    _passive_long_returns,
    _resolve_substrate_path,
    _strategy_returns_from_pred,
)
from scripts.run_h053_stage3_v3 import _fit_arm2_lightgbm_wf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_log = logging.getLogger("h053_v3_diagnostic")


def _sharpe(returns: np.ndarray) -> float:
    """Annualized Sharpe approximation (per-bar; daily frequency)."""
    if len(returns) < 2:
        return float("nan")
    mu = float(np.mean(returns))
    sigma = float(np.std(returns, ddof=1))
    return mu / sigma if sigma > 1e-12 else 0.0


def main(substrate_path: str | None = None) -> dict:
    """Run the diagnostic and return a structured findings dict."""
    substrate_root = _resolve_substrate_path(substrate_path)
    _log.info("Loading ES substrate from %s …", substrate_root)
    panel = _load_substrate(substrate_root, "ES")
    features = _compute_features_per_session(panel)
    target_dtype = pl.Datetime("ns", "UTC")
    features = features.with_columns(pl.col("ts_event").cast(target_dtype))
    predictand = _compute_predictand(panel).with_columns(pl.col("ts_event").cast(target_dtype))
    aligned = predictand.join(features, on=["symbol", "ts_event"], how="inner")
    _log.info("Aligned panel: %d sessions", len(aligned))

    train_filter = (pl.col("session_date_et") >= _IS_START) & (pl.col("session_date_et") <= _IS_END)
    test_filter = (pl.col("session_date_et") >= _OOS_START) & (pl.col("session_date_et") <= _OOS_END_ES)

    skip = {"ts_event", "symbol", "session_date_et", "y", "c_0945", "c_1030"}
    feature_cols = [
        c for c in aligned.columns
        if c not in skip and not c.startswith("_") and not c.endswith("_right")
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
    X_train = train.select(feature_cols).to_numpy()
    y_train = train["y"].to_numpy()
    X_test = test.select(feature_cols).to_numpy()
    y_test = test["y"].to_numpy()
    _log.info("ES train n=%d, test n=%d, k=%d", len(train), len(test), len(feature_cols))

    # Step 1: Fit LightGBM on FULL IS train (1332 sessions; longer N_cal than inner-CV ~266)
    _log.info("Fitting LightGBM on full IS train …")
    arm, arm_meta = _fit_arm2_lightgbm_wf(X_train, y_train, inner_seed=_STAGE3_RNG_SEED)
    _log.info("LightGBM best cell: %s (CV R²=%s)", arm_meta["best_cell"], arm_meta["best_cv_r2"])

    # Step 2: Predict on OOS test
    raw_test = arm.predict(X_test)
    raw_train = arm.predict(X_train)  # for in-sample inspection only

    # Step 3: RAW prediction distribution diagnostics
    raw_test_q = np.quantile(raw_test, [0.0, 0.05, 0.25, 0.50, 0.75, 0.95, 1.0])
    raw_test_std = float(np.std(raw_test))
    raw_test_iqr = float(raw_test_q[3] - raw_test_q[1])  # placeholder; actual IQR below
    raw_test_iqr = float(np.quantile(raw_test, 0.75) - np.quantile(raw_test, 0.25))
    raw_test_mad = float(np.median(np.abs(raw_test - np.median(raw_test))))
    _log.info(
        "RAW LightGBM test predictions: q=%s; std=%.6f; IQR=%.6f; MAD=%.6f",
        raw_test_q.tolist(), raw_test_std, raw_test_iqr, raw_test_mad,
    )

    # The predictand y is approximately ±50-100 bps per session; a meaningful raw
    # prediction should have similar magnitude. If raw_test_std << 1e-3, the model
    # is producing near-constant predictions and isotonic has nothing to recover.

    # Step 4: Strategy returns + Sharpe under the RAW prediction
    raw_strategy_returns = _strategy_returns_from_pred(raw_test, y_test)
    raw_sharpe = _sharpe(raw_strategy_returns)
    _log.info("RAW strategy Sharpe (sign(raw_pred) * y_test): %.4f", raw_sharpe)

    # Step 5: Test 4 calibrators on the OOS surface
    d_test = (y_test > 0).astype(np.float64)
    d_train = (y_train > 0).astype(np.float64)

    rng_master = np.random.default_rng(_STAGE3_RNG_SEED + 1000)
    findings: dict = {
        "raw_prediction_diagnostics": {
            "test_quantiles_p0_5_25_50_75_95_100": raw_test_q.tolist(),
            "test_std": raw_test_std,
            "test_IQR": raw_test_iqr,
            "test_MAD": raw_test_mad,
            "predictand_typical_sigma_bps": "y ≈ ±50-100 bps per session; std comparable means model is varying meaningfully",
        },
        "raw_directional_sharpe": raw_sharpe,
        "best_lgb_cell": arm_meta["best_cell"],
        "best_lgb_cv_r2": arm_meta["best_cv_r2"],
        "n_train": len(train),
        "n_test": len(test),
        "calibrator_comparisons": [],
    }

    # Calibrator A: NO calibration (raw rank → directly map to probability via min-max scaling)
    raw_min, raw_max = float(raw_test.min()), float(raw_test.max())
    raw_range = raw_max - raw_min
    if raw_range > 1e-12:
        p_no_calib = (raw_test - raw_min) / raw_range  # in [0, 1]
    else:
        p_no_calib = np.full_like(raw_test, 0.5)
    bss_no = binary_brier_skill_score(p_no_calib, d_test)
    slope_no, _ = reliability_slope_point(p_no_calib, d_test, n_bins=10)
    bss_ci_no = binary_bss_bootstrap_ci(p_no_calib, d_test, n_bootstrap=500, rng=rng_master)
    slope_ci_no = reliability_slope_bootstrap_ci(p_no_calib, d_test, n_bootstrap=500, n_bins=10, rng=rng_master)
    findings["calibrator_comparisons"].append({
        "name": "no_calibration_minmax_scaled",
        "n_cal": 0,
        "bss_point": bss_no,
        "bss_lower_ci": bss_ci_no.bss_ci_lower,
        "bss_upper_ci": bss_ci_no.bss_ci_upper,
        "binding_bss_passed": bss_ci_no.binding_gate_passed,
        "reliability_slope_point": slope_no,
        "reliability_slope_lower": slope_ci_no.slope_ci_lower,
        "reliability_slope_upper": slope_ci_no.slope_ci_upper,
        "binding_slope_passed": slope_ci_no.binding_gate_passed,
    })
    _log.info("[A] no-calib: BSS_point=%.4f BSS_CI=[%.4f,%.4f] slope=%.4f slope_CI=[%.4f,%.4f]",
              bss_no, bss_ci_no.bss_ci_lower, bss_ci_no.bss_ci_upper, slope_no, slope_ci_no.slope_ci_lower, slope_ci_no.slope_ci_upper)

    # Calibrator B: isotonic on FULL IS train (the v3 production used inner-CV-fold isotonic ~266 obs;
    # this tests whether the longer N_cal=1332 recovers the slope)
    iso_long = fit_calibrator(raw_train, (y_train > 0).astype(int))
    p_iso_long = predict_calibrated(iso_long, raw_test)
    bss_iso_long = binary_brier_skill_score(p_iso_long, d_test)
    slope_iso_long, _ = reliability_slope_point(p_iso_long, d_test, n_bins=10)
    bss_ci_iso_long = binary_bss_bootstrap_ci(p_iso_long, d_test, n_bootstrap=500, rng=rng_master)
    slope_ci_iso_long = reliability_slope_bootstrap_ci(p_iso_long, d_test, n_bootstrap=500, n_bins=10, rng=rng_master)
    findings["calibrator_comparisons"].append({
        "name": "isotonic_full_IS_train",
        "n_cal": len(y_train),
        "bss_point": bss_iso_long,
        "bss_lower_ci": bss_ci_iso_long.bss_ci_lower,
        "bss_upper_ci": bss_ci_iso_long.bss_ci_upper,
        "binding_bss_passed": bss_ci_iso_long.binding_gate_passed,
        "reliability_slope_point": slope_iso_long,
        "reliability_slope_lower": slope_ci_iso_long.slope_ci_lower,
        "reliability_slope_upper": slope_ci_iso_long.slope_ci_upper,
        "binding_slope_passed": slope_ci_iso_long.binding_gate_passed,
    })
    _log.info("[B] isotonic-full-IS: BSS_point=%.4f BSS_CI=[%.4f,%.4f] slope=%.4f slope_CI=[%.4f,%.4f]",
              bss_iso_long, bss_ci_iso_long.bss_ci_lower, bss_ci_iso_long.bss_ci_upper,
              slope_iso_long, slope_ci_iso_long.slope_ci_lower, slope_ci_iso_long.slope_ci_upper)

    # Calibrator C: beta calibration (Kull 2017) on full IS train
    a, b, c = fit_beta_calibration(raw_train, (y_train > 0).astype(int))
    p_beta = predict_beta_calibration(raw_test, a, b, c)
    bss_beta = binary_brier_skill_score(p_beta, d_test)
    slope_beta, _ = reliability_slope_point(p_beta, d_test, n_bins=10)
    bss_ci_beta = binary_bss_bootstrap_ci(p_beta, d_test, n_bootstrap=500, rng=rng_master)
    slope_ci_beta = reliability_slope_bootstrap_ci(p_beta, d_test, n_bootstrap=500, n_bins=10, rng=rng_master)
    findings["calibrator_comparisons"].append({
        "name": "beta_calibration_full_IS_train",
        "n_cal": len(y_train),
        "bss_point": bss_beta,
        "bss_lower_ci": bss_ci_beta.bss_ci_lower,
        "bss_upper_ci": bss_ci_beta.bss_ci_upper,
        "binding_bss_passed": bss_ci_beta.binding_gate_passed,
        "reliability_slope_point": slope_beta,
        "reliability_slope_lower": slope_ci_beta.slope_ci_lower,
        "reliability_slope_upper": slope_ci_beta.slope_ci_upper,
        "binding_slope_passed": slope_ci_beta.binding_gate_passed,
        "beta_params": {"a": a, "b": b, "c": c},
    })
    _log.info("[C] beta-full-IS: BSS_point=%.4f BSS_CI=[%.4f,%.4f] slope=%.4f slope_CI=[%.4f,%.4f]",
              bss_beta, bss_ci_beta.bss_ci_lower, bss_ci_beta.bss_ci_upper,
              slope_beta, slope_ci_beta.slope_ci_lower, slope_ci_beta.slope_ci_upper)

    # Calibrator D: Platt (logistic) on full IS train — explicit comparison even though n_cal > 500
    from sklearn.linear_model import LogisticRegression
    platt = LogisticRegression(C=1e9, solver="lbfgs", max_iter=1000)
    platt.fit(raw_train.reshape(-1, 1), (y_train > 0).astype(int))
    p_platt = platt.predict_proba(raw_test.reshape(-1, 1))[:, 1]
    bss_platt = binary_brier_skill_score(p_platt, d_test)
    slope_platt, _ = reliability_slope_point(p_platt, d_test, n_bins=10)
    bss_ci_platt = binary_bss_bootstrap_ci(p_platt, d_test, n_bootstrap=500, rng=rng_master)
    slope_ci_platt = reliability_slope_bootstrap_ci(p_platt, d_test, n_bootstrap=500, n_bins=10, rng=rng_master)
    findings["calibrator_comparisons"].append({
        "name": "platt_logistic_full_IS_train",
        "n_cal": len(y_train),
        "bss_point": bss_platt,
        "bss_lower_ci": bss_ci_platt.bss_ci_lower,
        "bss_upper_ci": bss_ci_platt.bss_ci_upper,
        "binding_bss_passed": bss_ci_platt.binding_gate_passed,
        "reliability_slope_point": slope_platt,
        "reliability_slope_lower": slope_ci_platt.slope_ci_lower,
        "reliability_slope_upper": slope_ci_platt.slope_ci_upper,
        "binding_slope_passed": slope_ci_platt.binding_gate_passed,
    })
    _log.info("[D] platt-full-IS: BSS_point=%.4f BSS_CI=[%.4f,%.4f] slope=%.4f slope_CI=[%.4f,%.4f]",
              bss_platt, bss_ci_platt.bss_ci_lower, bss_ci_platt.bss_ci_upper,
              slope_platt, slope_ci_platt.slope_ci_lower, slope_ci_platt.slope_ci_upper)

    # Synthesis
    any_passes = any(c["binding_bss_passed"] and c["binding_slope_passed"] for c in findings["calibrator_comparisons"])
    findings["synthesis"] = {
        "any_calibrator_passes_binding_gates_at_full_IS_train": any_passes,
        "interpretation": (
            "If raw_test_std is small (<1e-3), the LightGBM RAW predictions are near-constant — "
            "no calibrator can recover what isn't there. If raw_test_std is meaningful (>1e-3) but "
            "no calibrator passes both binding gates, the issue is fundamental forecast-frequency "
            "mismatch on this OOS fold (regime shift, distribution drift, or signal absence). If "
            "any calibrator at full IS train passes both gates, the v3 inner-CV-fold N_cal was the "
            "limiting factor and a successor hypothesis with an amended calibrator could promote."
        ),
    }
    return findings


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--substrate-path", default=None)
    p.add_argument("--out", default=None, help="Output JSON path; default stdout")
    args = p.parse_args()
    out = main(args.substrate_path)
    serialised = json.dumps(out, indent=2, sort_keys=True, default=str)
    if args.out:
        Path(args.out).write_text(serialised, encoding="utf-8")
        print(f"Findings written to {args.out}")
    else:
        print(serialised)
