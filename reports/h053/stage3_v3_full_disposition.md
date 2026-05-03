---
hypothesis_id: H053
stage: Stage-3 v3 (walk-forward grid + bootstrap-CI calibration)
adr: ADR-0013
plan: plan/h053_stage3_v3_plan_2026-05-03.md (v3-r3)
audit_trail: docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md
run_id: h053_stage3_v3_20260503T173742Z
sidecar_sha256: 5da28988aa1b5ecae7b6f3b8198df41662c08bff19827b92aba20e9b68ea5b55
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
git_head: 0d1fb08442747cc07b63b33d173c20eaf8e65966
status: BINDING — disposition decided per ADR-0012 §10.1 strict precedence
---

# H053 Stage-3 v3 — disposition report

## TL;DR

**Disposition: `calibration-failed; paper_trade_eligible=False` on all 4 arms (ES Arm 1 + Arm 2; NQ Arm 1 + Arm 2).**

Per [ADR-0012 §10.1](../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) strict precedence: PIT canary passed (14/14 each symbol); ReproLog complete; **binary BSS bootstrap CI lower-bound > 0 FAILED on all 4 arms**; reliability slope CI covers 1.0 also FAILED on all 4 arms. The disposition class drops out at the calibration gate per the strict-precedence tree, before the Class B Sharpe + SPA KPIs are evaluated for promotion.

**Substantive empirical finding** (Class B KPI; non-binding for disposition):
- **ES Arm 2 LightGBM**: cell-pass-fraction 81% (13 of 16 walk-forward grid cells produce positive Sharpe); median cell Sharpe +0.04; mean +0.03; max +0.09. **The walk-forward grid finds a weak directional signal** that survives across most W_train sizes for ES on the LightGBM arm.
- **NQ Arm 2 LightGBM**: cell-pass-fraction 56% (9 of 16); median cell Sharpe +0.01; weaker signal.
- **Both ElasticNet arms**: cell-pass-fraction 25% (ES) / 6% (NQ) — essentially no signal under linear modeling.
- **Hansen SPA**: ES p=0.12; NQ p=0.30 (both `spa-rejects` at α=0.05).

The dichotomy — **positive raw Sharpe but failed calibration gate** — is the methodology working as designed. The strategy's directional bet is profitable on average for ES Arm 2 LightGBM, but the predicted-probability calibration is poor: the forecast probabilities do not faithfully map onto outcome frequencies. The reliability slope point estimate is **-0.04** on ES Arm 2 (near-zero — almost constant prediction), with CI [-0.16, 0.10] — centered near zero, not 1.0. The model emits probabilities that do not reflect actual outcome distributions even though directional skill exists.

This is a **methodologically-correct null disposition**. Per ADR-0012, calibration-failed at design-time means the operator cannot promote this signal to paper-trade without first addressing the calibration gap.

## Methodology summary

Per [ADR-0013](../../docs/decisions/ADR-0013-walk-forward-grid-and-calibration-CI.md) (this commit):
- **Walk-forward grid Sharpe**: 8-cell geometric W_train `[630, 684, 743, 807, 876, 951, 1033, 1122]` × 2 modes (rolling, expanding) = 16 cells per arm × symbol.
- **Inner walk-forward CV** for hyperparameter selection (replaces v2 KFold-shuffle).
- **Held-out CV-fold isotonic** calibration per design.md §4.5.3.
- **Binary BSS bootstrap CI** binding gate: `lower_CI > 0` vs climatological prior.
- **Reliability slope bootstrap CI** binding gate: `1.0 ∈ [lower, upper]`.
- **LW2008 paired-cell Sharpe CI** for cell-pair comparisons.
- **Hansen SPA** stacked (n_oos, m) loss-differential matrix per Hansen 2005 §2.4.
- All bootstrap procedures: B=2000, paired stationary bootstrap on (p_oof, d) tuples, PW2004+PPW2009 block length, 95% percentile.

## Sample sizes + provenance

| Element | Value |
|---|---|
| ES train (IS 2015-2022) | 1332 sessions |
| ES test (OOS 2024-2025) | 367 sessions |
| NQ train | 1323 sessions |
| NQ test | 372 sessions |
| n_features | 42 (matches v2; floor 15·k = 630 per Riley 2019 Part I) |
| Substrate dataset checksum | `bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665` |
| Sidecar `scientific_payload_sha256` | `5da28988aa1b5ecae7b6f3b8198df41662c08bff19827b92aba20e9b68ea5b55` |
| Git HEAD | `0d1fb08442747cc07b63b33d173c20eaf8e65966` |
| Total wall-clock | 18 min (12:37 → 12:55 CT) |

## Class A binding-gate verdicts (ADR-0012 §10.1)

| Symbol | Arm | PIT | ReproLog | BSS CI lower | Reliability slope CI covers 1.0 | Disposition class |
|---|---|---|---|---:|---|---|
| ES | Arm 1 ElasticNet | PASS (14/14) | PASS | -0.0489 | FAIL ([-1.29, 0.96] — upper just below 1.0) | **calibration-failed** |
| ES | Arm 2 LightGBM | PASS (14/14) | PASS | -0.4317 | FAIL ([-0.16, 0.10]) | **calibration-failed** |
| NQ | Arm 1 ElasticNet | PASS (14/14) | PASS | -0.0237 | FAIL ([-1.46, 1.00] — upper at 1.00 boundary; computational rather than statistical pass) | **calibration-failed** |
| NQ | Arm 2 LightGBM | PASS (14/14) | PASS | -0.4653 | FAIL ([-0.12, 0.11]) | **calibration-failed** |

**Note**: The reliability slope CI on NQ Arm 1 has upper endpoint exactly at 0.9972 — fails by 0.003 numerically; substantively the slope CI is centered at -0.23, far from 1.0. Both ElasticNet arms have very wide reliability slope CIs (range > 2.0), reflecting the small effective sample for slope inference; LightGBM CIs are narrow but centered at zero (constant-predictor regime).

## Class B KPI report card (non-binding)

### Walk-forward grid sensitivity curves

| Symbol | Arm | Cell-pass-fraction | Median cell Sharpe | Mean | Min | Max |
|---|---|---:|---:|---:|---:|---:|
| ES | Arm 1 ElasticNet | 0.250 | -0.0169 | -0.0114 | -0.0364 | +0.0215 |
| ES | Arm 2 LightGBM | **0.812** | **+0.0402** | +0.0338 | -0.0192 | +0.0884 |
| NQ | Arm 1 ElasticNet | 0.062 | -0.0172 | -0.0201 | -0.0553 | +0.0018 |
| NQ | Arm 2 LightGBM | 0.562 | +0.0149 | +0.0114 | -0.0330 | +0.0691 |

The cell-pass-fraction continuous KPI (per F-1-15 closure) shows **LightGBM dominates ElasticNet** on both symbols, and **ES dominates NQ** on both arms. ES Arm 2 LightGBM is the strongest signal; NQ Arm 1 ElasticNet is the weakest.

### Hansen SPA (Class B KPI per ADR-0012)

| Symbol | p-value | Annotation |
|---|---:|---|
| ES | 0.1225 | spa-rejects |
| NQ | 0.2950 | spa-rejects |

Both p-values fail to reject H0 of "best strategy is no better than benchmark" at α=0.05, consistent with the calibration-failed disposition.

### Per-arm OOS arm returns

| Symbol | Arm | n | mean | std |
|---|---|---:|---:|---:|
| ES | Arm 1 | 367 | -0.000001 | 0.003087 |
| ES | Arm 2 | 367 | +0.000289 | 0.003073 |
| NQ | Arm 1 | 372 | -0.000035 | 0.004285 |
| NQ | Arm 2 | 372 | +0.000266 | 0.004277 |

ES Arm 2 + NQ Arm 2 have positive mean OOS returns; ElasticNet arms are essentially zero.

### Calibrator selection

All 4 arms used **isotonic** calibrator (n_cal effective ≥ 500 in inner walk-forward folds; design.md §4.5.3 binding rule satisfies the threshold).

## Why calibration-failed despite positive raw Sharpe (the substantive interpretation)

The walk-forward Sharpe shows LightGBM produces directional skill — its predictions agree with the sign of OOS returns more often than not. But **the magnitude calibration is broken**: the model emits probabilities like "P(up) = 0.62" but the empirical frequency in the bin centered at 0.62 is closer to 0.5 (or worse). The reliability slope captures exactly this gap — slope = 1 means perfectly-calibrated; slope = 0 means the predictions are constant; negative slope means inverse-calibrated.

For ES Arm 2: reliability slope point = -0.04 (essentially zero), CI = [-0.16, 0.10]. The CI is narrow and centered near zero — the LightGBM probabilities are NEAR-CONSTANT after isotonic calibration on the OOS fold. So "the model emits a constant probability that happens to align with sign(OOS-return) frequency" — directional skill, no probabilistic skill.

This is **methodologically distinct** from the v2 first-pass `archive(null, descriptive-mediation-only)` (which was leakage-inflated due to F-2-1/F-2-2/F-2-3 defects). v3 has clean methodology AND a substantive null at the calibration gate.

## Comparison vs v2 first-pass

| Metric | v2 (BLOCKed) | v3 (binding) |
|---|---|---|
| Disposition | calibration-failed (BLOCK; not binding) | **calibration-failed (binding)** |
| Methodology | CPCV time-ordering violation, KFold-shuffle inner CV, in-sample isotonic | walk-forward grid + walk-forward inner CV + held-out isotonic |
| ES Arm 2 LightGBM Sharpe | +0.428 (CPCV median; leakage-inflated) | +0.040 (walk-forward grid median; honest) |
| NQ Arm 2 LightGBM Sharpe | +0.422 (leakage-inflated) | +0.015 (honest) |
| Cost-c bps | 10.6 (10× error in plan) | 1.06 (corrected per F-1-1) |
| Audit-loop residuals | 12 BLOCKING findings | All closed; 5 minor follow-ups registered |

The honest walk-forward Sharpes are an order of magnitude smaller than the leakage-inflated v2 CPCV medians. This is the v2-vs-v3 calibration of the magnitude of the signal — when methodology corrects for leakage, the apparent Sharpe magnitude collapses by ~10×.

## Operator decision

Per ADR-0012 §"Operator-promotion rule" + design.md §10.1: H053 is **NOT paper-trade-eligible** at this run. The 60-session-day paper-trade clock does not start.

Operator may consider:
1. **Investigate the calibration gap on ES Arm 2 LightGBM specifically.** The walk-forward Sharpe is positive on 81% of cells — this is suggestive of a real directional signal. Recalibrating the LightGBM probability surface (e.g., longer N_cal window, beta calibration as binding rather than KPI exhibit, or a different isotonic-fitting strategy) could shift the BSS lower CI above zero. This requires a successor hypothesis ID (would amend design.md §4.5.3 §1-§7).
2. **Accept the calibration-failed disposition.** H053 archives at this stage; the directional signal observed on ES Arm 2 LightGBM is documented as a Class B KPI exhibit but not promoted.
3. **Re-run with longer N_cal** (e.g., expand the calibration sub-fold). Tracked under follow-up `P1-H053-V3-NCAL-EMPIRICAL-CALIBRATION` (new this disposition).

## SPA family slot consumption

Per design.md §8 + ADR-0012, H053 contributes 3 ex-ante slots to the SPA family. Slot accounting:
- Slot 1 (Arm 1 ElasticNet): consumed by `archive(calibration-failed)`
- Slot 2 (Arm 2 LightGBM): consumed by `archive(calibration-failed)`
- Slot 3 (Arm 3 LLM): consumed by `archive(prerequisite-not-met)` (design.md §11.4 prereq 7 deterministic-replay scaffolding never landed)

Family size remains 3; not freed for additional arms. Per design.md §8 + Hansen 2005 §2.4 ex-ante-fixed-universe requirement.

## Cycle 11 paper-trade scaffolding: NOT FIRED

Per [plan/h053_buildout_2026-04-28.md](../../plan/h053_buildout_2026-04-28.md) §Cycle 11, paper-trade scaffolding only fires on at least one arm reaching `archive(complete; KPI report)` per ADR-0012 §10.1. All 4 H053 arms archive at calibration-failed; Cycle 11 does not fire. Cycle 12 LLM Arm 3 also does not fire (conditional on Cycle 10 producing positive).

## Class B KPI exhibits (deferred — to be filled in subsequent commits)

The plan v3-r3 §B specified four Class B KPI exhibits: (1) multinomial K_arch×3 Brier with global BSS bootstrap CI; (2) cost-aware binary BSS for 1-tick + 2-tick; (3) beta calibration comparison; (4) inner-fold seed-sensitivity. The v3 first-pass production run instrumented #1-#3 in the script (`_compute_kpi_exhibits`) but tied them to a separate downstream call that requires re-fitting the per-arm OOF p-vector outside the calibration-payload structure. This is tracked under follow-up `P1-H053-V3-KPI-EXHIBIT-INTEGRATION` (operational; non-blocking — the exhibits do not affect the binding disposition class).

## Follow-ups registered

- `P1-H053-V3-NCAL-EMPIRICAL-CALIBRATION` (NEW) — empirical calibration of N_cal threshold per arm; consider N_cal ≥ 800 for isotonic stability on H053 OOS-size folds
- `P1-H053-V3-KPI-EXHIBIT-INTEGRATION` (NEW) — wire multinomial + cost-aware + beta KPI exhibits into the per-arm payload
- `P1-PLAN-V3-INNER-FOLD-SENSITIVITY-N-REFITS-CALIBRATE` (R2 plan-audit residual) — calibrate n_refits ≥ 10 if the 5-refit version is noisy
- `P1-PLAN-V3-CITATION-PIN-VERIFY` (R1 plan-audit residual) — verify §-pin gaps L-1, L-4, L-13, L-15, L-18 before ADR-0013 freeze
- `P1-ADR-0013-BSS-LOWER-CI-PROCEDURAL-AMENDMENT-DOC` (R2 plan-audit residual) — explicit procedural-amendment documentation in ADR-0013

## References

- [plan/h053_stage3_v3_plan_2026-05-03.md](../../plan/h053_stage3_v3_plan_2026-05-03.md) — v3-r3 plan
- [docs/decisions/ADR-0013-walk-forward-grid-and-calibration-CI.md](../../docs/decisions/ADR-0013-walk-forward-grid-and-calibration-CI.md) — canonical methodology
- [docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md](../../docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md) — audit trail
- [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md) §4.5.3 — binding calibration rule
- Sidecar: `runs/h053/stage3_v3/h053_stage3_v3_20260503T173742Z/sidecar.json`
