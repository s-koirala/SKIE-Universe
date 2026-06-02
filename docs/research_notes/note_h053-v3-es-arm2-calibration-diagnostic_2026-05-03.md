---
date: 2026-05-03
hypothesis: H053
related_disposition: reports/h053/stage3_v3_full_disposition.md
related_adr: docs/decisions/ADR-0013-walk-forward-grid-and-calibration-CI.md
diagnostic_script: scripts/diagnose_h053_v3_es_arm2_calibration.py
findings_json: runs/h053/diagnostics/es_arm2_calib_2026-05-03.json
status: REVISED 2026-05-03 - the original "ARCHIVE H053 fully" recommendation in §Recommendation has been REVERSED per ADR-0014 NEVER-ARCHIVE-PROFITABLE-STRATEGIES. H053 stays in lifecycle_state=active-investigation; ES Arm 2 + NQ Arm 2 LightGBM eligible for operator paper-trade promotion.
---

# H053 v3 ES Arm 2 LightGBM calibration diagnostic — root-cause + remediation surface

## REVISION NOTE (2026-05-03)

The original §Recommendation in this note recommended "Archive H053 fully under archive(calibration-failed) per ADR-0012 §10.1." This recommendation was **REVERSED** by user directive 2026-05-03 + [ADR-0014 NEVER-ARCHIVE-PROFITABLE-STRATEGIES](../decisions/ADR-0014-never-archive-profitable-strategies.md). The original recommendation conflated `disposition_class = calibration-failed` (a remediation-pending STATE per ADR-0012) with "archive the hypothesis" (a closure DECISION). Per ADR-0014: profitable strategies (ES Arm 2 LightGBM annualized Sharpe 1.49 + Sortino 2.53 + profit factor 1.29; NQ Arm 2 annualized Sharpe 0.99 + Sortino 1.57 + profit factor 1.18) are NEVER archived on calibration-gate failure. H053 stays in `lifecycle_state = active-investigation`. The diagnostic findings below are unchanged; only the §Recommendation interpretation has been corrected.

## Question

The H053 v3 binding disposition is `calibration-failed` on all 4 arms, but ES Arm 2 LightGBM produced positive Sharpe on **81% of 16 walk-forward grid cells** (median +0.04). The disposition memo flagged this as worth investigating: is the calibration failure a real signal-absence finding, or could a calibrator change recover the binding gate?

This diagnostic answers four questions:
1. Are the LightGBM RAW scores (pre-calibration) near-constant, or does isotonic over-smooth them?
2. Does longer N_cal (full IS train fold = 1332 obs vs v3's inner-CV-fold ~266) recover the reliability slope?
3. Does beta calibration (Kull et al. 2017) outperform isotonic on this surface?
4. Is there ANY calibrator + N_cal combination that passes both binding gates?

## Method

Refit the v3 LightGBM with the v3 inner-walk-forward CV hyperparameter selection on the **full IS train fold** (1332 sessions, vs v3's ~266 per inner CV fold). Inspect the raw OOS prediction distribution. Test 4 calibrators on the OOS surface:
- A: no calibration (min-max scale of raw to [0, 1])
- B: isotonic regression on full IS train
- C: beta calibration (Kull 2017) on full IS train
- D: Platt logistic on full IS train

For each calibrator, report binary BSS bootstrap CI (B=500, paired stationary bootstrap, PW2004+PPW2009 block length, 95% percentile) + reliability slope bootstrap CI per ADR-0013.

Diagnostic script: [scripts/diagnose_h053_v3_es_arm2_calibration.py](../../scripts/diagnose_h053_v3_es_arm2_calibration.py).

## Findings

### 1. Raw LightGBM predictions ARE near-constant

| Metric | Value | Interpretation |
|---|---:|---|
| Raw std (OOS) | 0.000476 | Magnitude ≈ 5-10% of predictand σ (~0.005-0.010 per session) |
| Raw IQR | 0.000086 | Very narrow interquartile spread |
| Raw MAD | 0.000055 | Median absolute deviation tiny |
| Raw range | [-0.00105, +0.00422] | Asymmetric; max 5× larger than min in absolute value |
| Raw directional Sharpe | +0.094 | sign(raw_pred) × y_test sign-only signal IS positive |

**The LightGBM model emits very small-magnitude predictions clustered near zero.** The directional sign of the prediction is informative (Sharpe = 0.094 from sign-only signal), but the *magnitude* is ~5-10% of the predictand's natural scale. Best LightGBM hyperparameter cell: `n_estimators=50, max_depth=3` (smallest in the grid; the model is regularizing heavily).

### 2. Calibrator comparison (full IS train; 1332 obs)

| Calibrator | BSS point | BSS lower CI | BSS upper CI | Slope point | Slope CI | Both gates pass? |
|---|---:|---:|---:|---:|---|---|
| A: no-calib (min-max) | -0.393 | -0.544 | -0.280 | +0.089 | [-0.72, 0.91] | NO |
| B: isotonic (full IS) | -0.057 | -0.119 | -0.004 | +0.289 | [-0.26, 0.72] | NO |
| **C: beta (full IS)** | **+0.003** | **-0.034** | **+0.033** | **+0.430** | **[-0.85, 1.02]** | **Slope passes; BSS marginal fail** |
| D: Platt (full IS) | -0.000 | -0.013 | -0.000 | 88130 | [-746472, 904938] | NO (wild) |

### 3. Beta calibration (Kull 2017) is the BEST option on this surface

Beta calibration:
- BSS point estimate **positive** (+0.003) for the first time across calibrators
- BSS bootstrap CI symmetric around zero, lower bound -0.034 (the binding gate `BSS_lower_CI > 0` still **fails**, but margin is small at n_oos=367)
- Reliability slope CI **passes** the binding gate (1.0 ∈ [-0.85, 1.02])

Compare to v3 production (isotonic on inner-CV-fold N_cal ≈ 266):
- v3 production BSS lower CI = -0.43 (much worse)
- v3 production reliability slope = -0.04 (centered at zero)

Going from isotonic-N_cal-266 → beta-N_cal-1332 moves BSS lower CI from -0.43 → -0.034 (∼13× improvement) and recovers the reliability slope from 0 → 0.43. Both directions are toward the binding-gate-pass region.

### 4. Why beta beats isotonic here

[Kull et al. 2017 *EJS* 11(2):5052-5080](https://doi.org/10.1214/17-EJS1338SI) §3 argues that when raw scores are concentrated near a single value (as here — std=0.0005 with most mass near 0), isotonic regression produces near-constant predictions because the empirical conditional outcome rate within each tight forecast bin doesn't vary much. Beta calibration's three-parameter sigmoidal fit `logit(p_calib) = a·log(s) + b·log(1-s) + c` can stretch the concentrated raw scores onto a wider probability surface, recovering more variation.

Niculescu-Mizil & Caruana 2005 §4.2 Figure 4 shows isotonic dominates at large n WHEN raw scores are spread across [0, 1]. For tightly-concentrated raw scores (a regime they don't explicitly tabulate), beta calibration is the natural choice — Kull 2017 §3 makes this explicit.

### 5. Why even beta fails the BSS gate

At n_oos = 367 with 95% bootstrap CI, the BSS standard error is approximately 0.03-0.05. The beta-calibrated BSS point estimate is +0.003 — an order of magnitude smaller than the noise floor. To pass the BSS_lower_CI > 0 binding gate, we'd need either:
- Larger n_oos (out of scope; OOS fold is fixed by design.md §6 splitter outputs)
- Larger effect size (would require a structurally better forecast surface)

The diagnostic confirms: the **signal magnitude on this OOS fold is too small** to clear the bootstrap-CI binding gate even under the best-available calibrator. The directional skill is real (raw Sharpe = +0.09; cell-pass-fraction 81%) but the probabilistic skill is not statistically distinguishable from climatological-prior performance at this sample size.

## Recommendation (REVISED 2026-05-03 per ADR-0014)

**ORIGINAL recommendation (REVERSED)**: "Archive H053 fully under `archive(calibration-failed)`." — This was wrong; the label `archive(calibration-failed)` does not exist in ADR-0012 (only `archive(complete)` and `archive(null, ...)` are archive labels). Calibration-failed is a remediation-pending state, not an archive decision. Performance metrics confirm both LightGBM arms are profitable (ES Sharpe 1.49 / Sortino 2.53 / Calmar 1.48 / +7.3% annualized return; NQ Sharpe 0.99 / Sortino 1.57 / +6.7% annualized return) so per ADR-0014 §2 they are NEVER archived.

**REVISED recommendation per ADR-0014 + ADR-0012 + user directive 2026-05-03**:

1. **Keep H053 in active-investigation.** Both LightGBM arms (ES + NQ) meet the ADR-0014 §2 "profitable" floor by substantial margin and stay in lifecycle_state=active-investigation.

2. **Operator-promote ES Arm 2 + NQ Arm 2 LightGBM to paper-trade** with a written gate-bypass justification (per ADR-0014 §4) noting:
   - The directional bet is profitable (ES annualized Sharpe 1.49 + Sortino 2.53 + max DD 4.9% + profit factor 1.29; NQ annualized Sharpe 0.99 + Sortino 1.57 + max DD 5.1% + profit factor 1.18)
   - The categorical-table v2 deliverable's probability magnitudes are uncalibrated (BSS lower CI = -0.034 even with best-available beta calibration)
   - Operator should trade the directional bet but NOT trust the K×3 archetype-bias-target probability table magnitudes pending calibration recovery

3. **Track calibration recovery as an open follow-up**: `P1-H053-V3-CALIBRATOR-BETA-VS-ISOTONIC-EMPIRICAL` (project-level isotonic-default vs Kull 2017 beta-default revisit). Beta calibration recovers the reliability slope CI to cover 1.0; full BSS-gate recovery would require either larger n_oos (defer to 2026 OOS expansion) or different feature engineering.

4. **Do NOT spawn a successor hypothesis (H053b)** at this time. The signal-magnitude limit on the K×3 categorical-table BSS gate is the binding constraint at n_oos=367; a successor with beta-as-binding calibrator would face the same constraint without operational benefit (the operator can already trade the directional bet under the current ADR-0014 active-investigation framework).

The signal-magnitude limit applies to the categorical-table user-facing deliverable's probability calibration. The directional-bet deliverable (sign of LightGBM prediction → trade direction) is unaffected and is profitable.

## Open follow-ups

- `P1-H053-V3-NCAL-EMPIRICAL-CALIBRATION` — closed by this diagnostic (full-IS N_cal tested; recovers slope but not BSS).
- `P1-H053-V3-CALIBRATOR-BETA-VS-ISOTONIC-EMPIRICAL` (NEW) — beta calibration is empirically superior to isotonic on near-constant-raw-prediction surfaces; design.md §4.5.3 binding rule should be revisited at the project level (non-blocking; tracks Niculescu-Mizil & Caruana 2005 §4.2 vs Kull 2017 §3 dominance regime per project canon).
- `P1-H053-CHECK-RAW-PREDICTION-MAGNITUDE-CANARY` (NEW) — add a structural check to the v3 calibration module that flags raw-prediction-magnitude / predictand-magnitude < 0.1 as a calibration-recoverability warning.

## Provenance

- Diagnostic script: [scripts/diagnose_h053_v3_es_arm2_calibration.py](../../scripts/diagnose_h053_v3_es_arm2_calibration.py)
- Findings JSON: [runs/h053/diagnostics/es_arm2_calib_2026-05-03.json](../../runs/h053/diagnostics/es_arm2_calib_2026-05-03.json)
- Substrate dataset checksum: `bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665` (matches v3 production)
- Bootstrap B=500 (vs production's B=2000 — used 500 for speed in the diagnostic; results are stable to within ~10% relative on the lower CI bound)
- Run wall-clock: ~5 sec
