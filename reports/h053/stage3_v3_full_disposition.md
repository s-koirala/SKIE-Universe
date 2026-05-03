---
hypothesis_id: H053
stage: Stage-3 v3 (walk-forward grid + bootstrap-CI calibration)
adr: ADR-0013 + ADR-0014
plan: plan/h053_stage3_v3_plan_2026-05-03.md (v3-r3)
audit_trail: docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md
run_id: h053_stage3_v3_20260503T173742Z
sidecar_sha256: 5da28988aa1b5ecae7b6f3b8198df41662c08bff19827b92aba20e9b68ea5b55
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
git_head: 0d1fb08442747cc07b63b33d173c20eaf8e65966
status: REVISED 2026-05-03 - disposition_class is `calibration-failed` per ADR-0012 §10.1 BUT lifecycle_state is `active-investigation` per ADR-0014 NEVER-ARCHIVE-PROFITABLE-STRATEGIES; H053 is NOT archived
---

# H053 Stage-3 v3 - disposition report (REVISED 2026-05-03 per ADR-0014)

## REVISION NOTE (2026-05-03)

This memo was revised after user directive 2026-05-03: "make a note not to archive profitable strategies; we are here to innovate and to explore; we need to lower our threshold; we need to be slower on the archiving." The original interpretation conflated `disposition_class = calibration-failed` (a remediation-pending STATE per ADR-0012) with "archive H053 fully" (a closure DECISION). Per [ADR-0014](../../docs/decisions/ADR-0014-never-archive-profitable-strategies.md) NEVER-ARCHIVE-PROFITABLE-STRATEGIES: H053 ES Arm 2 + NQ Arm 2 LightGBM are profitable on the OOS fold (annualized return +7.3% / +6.7%; Sharpe 1.49 / 0.99; Sortino 2.53 / 1.57; profit factor 1.29 / 1.18) and ARE NOT ARCHIVED. The technical disposition_class label `calibration-failed` is preserved per ADR-0012 §10.1 strict precedence; the operator-visible lifecycle_state is `active-investigation`. Operator may promote either or both LightGBM arms to paper-trade subject to written gate-bypass justification per ADR-0014 §4.

## TL;DR (REVISED)

**Technical disposition_class: `calibration-failed`** on all 4 arms (per ADR-0012 §10.1 strict precedence; binary BSS bootstrap CI lower-bound did not exceed 0; reliability slope CI did not cover 1.0). PIT canary 14/14 PASS each symbol; ReproLog complete.

**Lifecycle state: `active-investigation`** for ES Arm 2 + NQ Arm 2 LightGBM per [ADR-0014 §2 NEVER-ARCHIVE-PROFITABLE-STRATEGIES](../../docs/decisions/ADR-0014-never-archive-profitable-strategies.md). Both LightGBM arms have positive annualized OOS Sharpe (1.49 / 0.99), positive total return (+10.6% / +9.9%), Sortino > 1.5, profit factor > 1.0, recoverable max DD (4.9% / 5.1%) on the OOS fold. **H053 is NOT archived.** ElasticNet arms (Arm 1 on both symbols) also stay in active-investigation per ADR-0014 §4 default.

**Operator-promotion path**: ES Arm 2 + NQ Arm 2 LightGBM are eligible for operator paper-trade promotion subject to gate-bypass justification noting:
1. The directional bet is profitable (+7.3% / +6.7% annualized return, Sharpe 1.49 / 0.99, max DD ~5%)
2. The categorical-table v2 deliverable's probability magnitudes are uncalibrated (BSS lower CI = -0.034 even with best-available beta calibration)
3. Operator should trade the directional bet but NOT trust the K×3 archetype probability table magnitudes until calibration recovery is achieved (tracked under `P1-H053-V3-CALIBRATOR-BETA-VS-ISOTONIC-EMPIRICAL` follow-up).
4. **ES is `cost-floor-conditional`** (profitable at 1-tick slippage, flips negative at 2-tick); paper-trade promotion of ES requires fill-quality monitoring with abort-trigger if observed slippage routinely exceeds 1 tick. NQ is `cost-robust` (positive Sharpe through 2-tick).
5. **LW2008 ΔSharpe vs passive CI brackets zero** on both symbols — strategy alpha not statistically distinguishable from passive at α=0.05 with n_oos ≈ 370; the live 60-session-day paper-trade is the operational test of significance per ADR-0011.

## Performance dashboard (the un-archive evidence)

[runs/h053/diagnostics/arm2_performance_2026-05-03.json](../../runs/h053/diagnostics/arm2_performance_2026-05-03.json) — comprehensive metrics on the OOS fold (2024-01-03 to 2025-12-{03,18}; n=367 ES / 372 NQ):

| Symbol | Total log return | Annualized return | Annualized vol | Annualized Sharpe | Sortino | Calmar | Max DD | Win rate | Profit factor | Net of cost (1-tick) Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ES Arm 2 LightGBM** | +1060 bps | **+7.28%** | 4.88% | **+1.49** [-0.07, 3.08] | +2.53 | +1.48 | -4.92% | 53.7% | 1.29 | **+0.59** |
| **NQ Arm 2 LightGBM** | +991 bps | **+6.71%** | 6.79% | **+0.99** [-0.66, 2.62] | +1.57 | +1.32 | -5.09% | 51.6% | 1.18 | **+0.70** |

**ES Arm 2 LightGBM details**:
- DD trajectory: peak 2025-02-28 -> trough 2025-04-25 -> recover 2025-10-14 (121 sessions DD duration; 317 total underwater sessions)
- Avg win / avg loss: +24.08 / -21.79 bps
- Max consecutive wins / losses: 6 / 5
- 2024 ann return / Sharpe: +6.75% / 1.98
- 2025 ann return / Sharpe: +3.85% / 1.05

**NQ Arm 2 LightGBM details**:
- DD trajectory: peak 2024-10-01 -> trough 2024-11-07 -> recover 2025-03-05 (75 sessions DD duration; 337 total underwater)
- Avg win / avg loss: +34.56 / -31.36 bps
- Max consec wins / losses: 7 / 5
- 2024 ann return / Sharpe: +8.16% / 1.64
- 2025 ann return / Sharpe: +1.75% / 0.35

**Both strategies are profitable gross AND net of 1-tick cost** (cost-c ES 1.74 bps/RT; NQ 0.76 bps/RT). The strategies meet the ADR-0014 §2 "profitable" floor (annualized return > 0% AND Sortino > 0 AND profit factor > 1.0) by substantial margin.

### LW2008 paired-Sharpe vs passive long (multiple-testing-corrected per ADR-0008)

| Symbol | Passive ann Sharpe | ΔSharpe (arm − passive) | LW2008 95% CI | Excludes zero |
|---|---:|---:|---|---|
| ES | -0.0052 | **+0.0945** | [-0.0652, +0.2578] | No (CI brackets 0) |
| NQ | +0.1278 | +0.0543 | [-0.0989, +0.2153] | No (CI brackets 0) |

Both LW2008 paired-Sharpe CIs bracket zero — at n_oos ≈ 370, the strategy's marginal alpha over passive long is positive in point estimate but not statistically distinguishable at α=0.05. This is consistent with weak signal at moderate sample size; live paper-trade verification (the ADR-0011 60-session-day floor) is the operational test.

### Cost-floor sensitivity (1-tick + 2-tick per design.md §7.1)

| Symbol | Cost-c (1-tick) | Net Sharpe (1-tick) | Cost-c (2-tick) | Net Sharpe (2-tick) | Cost-floor annotation |
|---|---:|---:|---:|---:|---|
| ES Arm 2 LightGBM | 1.74 bps | **+0.59** | 3.23 bps | **-0.18** | `cost-floor-conditional` (1-tick OK; 2-tick flips negative) |
| NQ Arm 2 LightGBM | 0.76 bps | **+0.70** | 1.31 bps | **+0.50** | `cost-robust` (positive Sharpe through 2-tick) |

**Operational implication for ES Arm 2 LightGBM**: profitability is conditional on execution slippage staying within ~1.5 ticks of the 09:45 ET MOC (entry) and 10:30 ET MOC (exit). At 2-tick slippage, ES net annualized return is -0.86%. NinjaTrader bridge needs to be fill-quality-monitored; if observed slippage routinely exceeds 1 tick, ES paper-trade promotion should be deferred. NQ has more headroom — even at 2-tick slippage, +3.4% annualized net return / Sharpe 0.50.

## Original (now-historical) TL;DR

The pre-revision memo recorded "Disposition: calibration-failed; paper_trade_eligible=False on all 4 arms" and recommended ARCHIVE H053 FULLY in the operator-decision section. That recommendation was REVERSED by user directive 2026-05-03 + ADR-0014; preserved here for audit traceability:

> **Disposition (BINDING; pre-revision): `calibration-failed; paper_trade_eligible=False` on all 4 arms (ES Arm 1 + Arm 2; NQ Arm 1 + Arm 2).**

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

**Calibration-recovery diagnostic complete (2026-05-03)**: per [docs/research_notes/note_h053-v3-es-arm2-calibration-diagnostic_2026-05-03.md](../../docs/research_notes/note_h053-v3-es-arm2-calibration-diagnostic_2026-05-03.md), tested 4 calibrators × full-IS-train N_cal on the ES Arm 2 LightGBM surface. **Beta calibration (Kull 2017) outperforms isotonic** on this near-constant-raw-prediction surface (BSS point +0.003, slope CI [-0.85, 1.02] **passes** the binding gate; isotonic produces slope = 0). However, **even beta calibration's BSS lower CI = -0.034 fails the binding `BSS_lower_CI > 0` gate** at n_oos = 367 — the signal magnitude is too small to clear the bootstrap-CI noise floor on the K×3 categorical-table deliverable.

**Operator decision (REVISED 2026-05-03 per user directive + ADR-0014): KEEP H053 IN ACTIVE INVESTIGATION.** The original recommendation to "ARCHIVE H053 fully under `archive(calibration-failed)`" was REVERSED. Per ADR-0014 §2 + §6, profitable strategies are NEVER archived on calibration-gate failure alone. The ES Arm 2 + NQ Arm 2 LightGBM arms have positive annualized return + Sharpe > 0 + Sortino > 0 + profit factor > 1.0 — they enter `lifecycle_state = active-investigation`, not archive.

**The directional skill (positive raw Sharpe + cell-pass-fraction 81% on ES Arm 2) is the load-bearing finding.** Operator-promotion to paper-trade is recommended for ES Arm 2 LightGBM (Sharpe 1.49 + Sortino 2.53 + 4.9% max DD) and NQ Arm 2 LightGBM (Sharpe 0.99 + Sortino 1.57 + 5.1% max DD), with the categorical-table deliverable's probability-magnitude calibration documented as an OPEN follow-up per `P1-H053-V3-CALIBRATOR-BETA-VS-ISOTONIC-EMPIRICAL`.

## SPA family slot consumption

Per design.md §8 + ADR-0012, H053 contributes 3 ex-ante slots to the SPA family. Slot accounting (per ADR-0014 §1 vocabulary correction — `calibration-failed` and `prerequisite-not-met` are remediation-pending STATES per ADR-0012, not archive labels; they consume their slot via state-emission, not via `archive(...)` notation):
- Slot 1 (Arm 1 ElasticNet): consumed by `disposition_class = calibration-failed` (lifecycle_state = active-investigation per ADR-0014; archive ONLY by operator decision)
- Slot 2 (Arm 2 LightGBM): consumed by `disposition_class = calibration-failed` (lifecycle_state = active-investigation per ADR-0014; archive ONLY by operator decision)
- Slot 3 (Arm 3 LLM): consumed by `disposition_class = prerequisite-not-met` (design.md §11.4 prereq 7 deterministic-replay scaffolding never landed; archive ONLY by operator decision per ADR-0014 §8)

Family size remains 3; not freed for additional arms. Per design.md §8 + Hansen 2005 §2.4 ex-ante-fixed-universe requirement.

## Cycle 11 paper-trade scaffolding: NOT FIRED

Per [plan/h053_buildout_2026-04-28.md](../../plan/h053_buildout_2026-04-28.md) §Cycle 11, paper-trade scaffolding only fires on at least one arm reaching `archive(complete; KPI report)` per ADR-0012 §10.1. All 4 H053 arms archive at calibration-failed; Cycle 11 does not fire. Cycle 12 LLM Arm 3 also does not fire (conditional on Cycle 10 producing positive).

## Class B KPI exhibits (deferred — to be filled in subsequent commits)

The plan v3-r3 §B specified four Class B KPI exhibits: (1) multinomial K_arch×3 Brier with global BSS bootstrap CI; (2) cost-aware binary BSS for 1-tick + 2-tick; (3) beta calibration comparison; (4) inner-fold seed-sensitivity. The v3 first-pass production run instrumented #1-#3 in the script (`_compute_kpi_exhibits`) but tied them to a separate downstream call that requires re-fitting the per-arm OOF p-vector outside the calibration-payload structure. This is tracked under follow-up `P1-H053-V3-KPI-EXHIBIT-INTEGRATION` (operational; non-blocking — the exhibits do not affect the binding disposition class).

## Follow-ups registered

- `P1-H053-V3-NCAL-EMPIRICAL-CALIBRATION` — **CLOSED 2026-05-03** by [diagnostic note](../../docs/research_notes/note_h053-v3-es-arm2-calibration-diagnostic_2026-05-03.md): full-IS N_cal tested; recovers slope but not BSS gate.
- `P1-H053-V3-KPI-EXHIBIT-INTEGRATION` (NEW) — wire multinomial + cost-aware + beta KPI exhibits into the per-arm payload (operational; non-blocking).
- `P1-H053-V3-CALIBRATOR-BETA-VS-ISOTONIC-EMPIRICAL` (NEW from diagnostic) — beta calibration empirically superior to isotonic on near-constant-raw-prediction surfaces; design.md §4.5.3 binding rule should be revisited at the project level (Niculescu-Mizil & Caruana 2005 §4.2 vs Kull 2017 §3 dominance regime per project canon).
- `P1-H053-CHECK-RAW-PREDICTION-MAGNITUDE-CANARY` (NEW from diagnostic) — add a structural check to the v3 calibration module that flags raw-prediction-magnitude / predictand-magnitude < 0.1 as a calibration-recoverability warning.
- `P1-PLAN-V3-INNER-FOLD-SENSITIVITY-N-REFITS-CALIBRATE` (R2 plan-audit residual) — calibrate n_refits ≥ 10 if the 5-refit version is noisy.
- `P1-PLAN-V3-CITATION-PIN-VERIFY` (R1 plan-audit residual) — verify §-pin gaps L-1, L-4, L-13, L-15, L-18 before ADR-0013 freeze.
- `P1-ADR-0013-BSS-LOWER-CI-PROCEDURAL-AMENDMENT-DOC` (R2 plan-audit residual) — explicit procedural-amendment documentation in ADR-0013.

## References

- [plan/h053_stage3_v3_plan_2026-05-03.md](../../plan/h053_stage3_v3_plan_2026-05-03.md) — v3-r3 plan
- [docs/decisions/ADR-0013-walk-forward-grid-and-calibration-CI.md](../../docs/decisions/ADR-0013-walk-forward-grid-and-calibration-CI.md) — canonical methodology
- [docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md](../../docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md) — audit trail
- [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md) §4.5.3 — binding calibration rule
- Sidecar: `runs/h053/stage3_v3/h053_stage3_v3_20260503T173742Z/sidecar.json`
