---
adr_number: ADR-0013
title: Walk-forward grid Sharpe + bootstrap-CI calibration gates
status: Accepted
date: 2026-05-03
supersedes: none (procedural amendment to ADR-0012 disposition framework, ADR-0007 walk-forward methodology)
audit_trail: docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md
---

# ADR-0013 — Walk-forward grid Sharpe + bootstrap-CI calibration gates

## Context

H053 Stage-3 v2 (run_id `h053_stage3_20260501T115445Z`) was Round-1 BLOCKed by 12 audit findings (3 critical: F-2-1 CPCV time-ordering violation, F-2-2 KFold-shuffle inner CV, F-2-3 in-sample isotonic; 6 major; 3 minor). The remediation plan ([plan/h053_stage3_v3_plan_2026-05-03.md](../../plan/h053_stage3_v3_plan_2026-05-03.md), v3-r3 after a 2-round audit-remediate-loop on the plan itself) introduces two project-level methodology shifts that this ADR codifies:

1. **Walk-forward grid Sharpe** replaces CPCV-path-Sharpe ([cpcv_path_sharpe.py](../../src/skie_ninja/backtest/cpcv_path_sharpe.py)) as the canonical Sharpe-KPI walk-forward methodology for hypotheses with single-horizon time-ordered predictands. The CPCV primitive is preserved for hypotheses with valid CPCV semantics (i.e., where future-data leakage between train and test splits is avoidable), but H053 — and any hypothesis where the predictand is a fixed-clock-time-window return sampled once per session — uses the grid construction.

2. **Bootstrap-CI calibration gates** replace fixed-sentinel point thresholds on binary BSS (was: `BSS > 0`) and reliability slope (was: slope ∈ [0.7, 1.3]). The new binding gates are:
   - `binary_bss_lower_CI > 0` vs climatological prior
   - `1.0 ∈ reliability_slope_CI`
   Both via paired stationary bootstrap on (p_oof, d_actual), B=2000, [Politis-White 2004](https://doi.org/10.1081/ETC-120028836) + [Patton-Politis-White 2009](https://doi.org/10.1080/07474930802459016) block length, 95% percentile.

Both shifts fall within the [ADR-0012 §"Frozen pre-registration amendment"](ADR-0012-disposition-philosophy-aspirational-mvp.md) carve-out for §8/§10 procedural amendments (they do not change the §1-§7 estimator family — calibration is still isotonic primary / Platt fallback per [design.md §4.5.3](../../research/01_hypothesis_register/H053/design.md), and the Sharpe statistic is still the [Lo 2002 / Opdyke 2007](https://doi.org/10.2469/faj.v58.n4.2453) HAC-adjusted point estimate). The CI strengthening is procedurally MORE conservative than the point thresholds, so it cannot be a Type-I-inflation amendment.

## Decision

### A. Walk-forward grid Sharpe (canonical methodology for time-ordered single-horizon hypotheses)

Per [plan v3-r3 §A](../../plan/h053_stage3_v3_plan_2026-05-03.md):

- **W_train grid**: 8-point geometric `[630, 684, 743, 807, 876, 951, 1033, 1122]` (ratio (1122/630)^(1/7) ≈ 1.0857). Floor anchored at 15·k (k = number of features) per [Riley et al. 2019 'Part I — Continuous outcomes' *Stat Med* 38(7):1262-1275 doi:10.1002/sim.7993](https://doi.org/10.1002/sim.7993). Ceiling anchored at the post-Daily-gate-fix conservative IS train fold size with explicit inner-CV reservation (3-4 inner folds × W_inner_test ≥ 63 sessions).
- **W_test = step_size = 63 sessions** (calendar choice ≈ 3 trading months). The PW2004+PPW2009 floor of 25-60 sessions is satisfied with ~5% headroom; documented as a calendar choice, not a derived value (per Round-2 plan-audit F-2-3 closure).
- **Modes**: both `rolling` AND `expanding`; per [Pesaran-Pick-Pranovich 2013](https://doi.org/10.1016/j.jeconom.2013.02.004) adaptive window combination.
- **Total cells per arm × symbol**: 16 (8 W_train × 2 modes).
- **Sensitivity report**: `L̂(W_train)` curve with HAC-CI band per [Inoue-Jin-Rossi 2017](https://doi.org/10.1016/j.jeconom.2017.05.020) (paper-level pin; Theorem-2 §-pin not verified within audit budget).
- **Cell-pair Sharpe inference**: [Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized circular-block bootstrap; substituted with Politis-Romano 1994 stationary bootstrap per [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) bootstrap-variant-substitution rationale (first-order asymptotically equivalent per Lahiri 2003).
- **SPA universe entry**: stacked (n_oos, m) loss-differential matrix passed jointly to [hansen_spa_test](../../src/skie_ninja/inference/multipletest/hansen_spa.py) with shared bootstrap indices preserving cross-cell dependence per [Hansen 2005 §2 *JBES* 23(4):365-380](https://doi.org/10.1198/073500105000000063).
- **Cell ordering**: deterministic (low W_train first); order-invariant for the SPA test under shared bootstrap indices per Hansen 2005 §2.4 (bootstrap indices are drawn jointly across all m strategies; per-strategy ordering does not enter the test statistic).

Implementation: [src/skie_ninja/backtest/walk_forward_grid_sharpe.py](../../src/skie_ninja/backtest/walk_forward_grid_sharpe.py).

### B. Bootstrap-CI calibration gates (binding gate spec under design.md §4.5.3)

- **Binary BSS gate**: `binary_bss_lower_CI > 0` vs climatological prior (sample mean of binary outcomes). CI = paired stationary bootstrap on (p_oof, d_actual) tuples, B=2000, [Politis & Romano 1994 *JASA* 89(428):1303-1313 doi:10.2307/2290993](https://doi.org/10.2307/2290993) bootstrap, PW2004+PPW2009 block length, 95% percentile.
- **Reliability slope gate**: `1.0 ∈ [slope_lower_CI, slope_upper_CI]`. Same bootstrap procedure on the [Bröcker & Smith 2007 *Weather and Forecasting* 22(3):651-661 doi:10.1175/WAF993.1](https://doi.org/10.1175/WAF993.1) reliability-slope construction (linear regression of binned conditional outcome means on binned forecast means; n_bins=10 equal-frequency).
- **Calibrator selection**: design.md §4.5.3 binding rule preserved (isotonic primary; Platt fallback at N_cal < 500 per [Niculescu-Mizil & Caruana 2005](https://doi.org/10.1145/1102351.1102430) paper-level pin). The 3-way Platt-vs-isotonic-vs-beta selector with parsimony tie-break that was proposed in plan v3-r1 was REJECTED at Round-1 plan-audit F-1-7 (the parsimony ordering inverted NM&C 2005 Figure 4's empirical finding that isotonic dominates at large n).

### C. Class B KPI exhibits (non-binding per ADR-0012 §"Class B")

- **Multinomial K_arch × 3 Brier** with global BSS bootstrap CI per [Gneiting & Raftery 2007 *JASA* 102(477):359-378](https://doi.org/10.1198/016214506000001437) (paper-level pin; Theorem-3.2 §-pin not verified within audit budget).
- **Cost-aware binary BSS** for c ∈ {1-tick, 2-tick} per symbol via [src/skie_ninja/backtest/costs/h053_cost_c.py](../../src/skie_ninja/backtest/costs/h053_cost_c.py). At c ≈ 1 bps (well below per-session predictand σ ≈ 50-100 bps), the cost-aware exhibit documents marginal sensitivity to cost-floor assumptions, NOT a substantively different signal.
- **Beta calibration** comparison per [Kull, Silva Filho, Flach 2017 *EJS* 11(2):5052-5080 doi:10.1214/17-EJS1338SI](https://doi.org/10.1214/17-EJS1338SI). Reported but not selected (design.md §4.5.3 binding rule constrains the calibrator family to {isotonic, Platt}).
- **Inner-fold seed-sensitivity** exhibit: refit 5× with different inner-fold seeds; report selected-hyperparameter empirical distribution + Kendall-τ rank stability. Tracks Round-1 F-1-10 binding-quality concern that 3-4 effective inner folds at n_train ≈ 800-1100 yield high hyperparameter variance.

### D. Multinomial-as-binding-gate explicitly REJECTED

The plan v3-r1 proposal to make multinomial K×3 Brier the BINDING calibration gate (replacing binary BSS) was rejected at Round-1 plan-audit F-1-12 as exceeding the ADR-0012 §"Frozen pre-registration amendment" carve-out scope. design.md §4.5.3 binds "one isotonic curve per arm; archetype is a stratification axis for diagnostic plots only, NOT a separate calibration surface". Inverting this binding requires a successor hypothesis ID, NOT an ADR-level amendment. Multinomial Brier is therefore ONLY a Class B KPI exhibit.

## Consequences

**Positive:**
- F-2-1 closed at the methodology level: no future H053-class hypothesis carries the CPCV time-ordering risk.
- Calibration gates are now CI-based, eliminating sentinel-band hand-tuning.
- The walk-forward grid produces a sensitivity curve `L̂(W_train)` as a first-class artifact, addressing [Inoue-Jin-Rossi 2017](https://doi.org/10.1016/j.jeconom.2017.05.020) window-selection structural-stability concerns.
- LW2008 paired-Sharpe CIs replace ±0.1 placeholder for cell-pair comparisons (F-2-5 closure).

**Negative:**
- The bootstrap CI procedure adds ~30-60% wall-clock vs the point-threshold spec (B=2000 reps × multiple bootstrap calls per arm). Not material at n_oos ≈ 250-800.
- The walk-forward grid loses the CPCV "all-paths-considered" property; it is a less-rich Type-I-control object than CPCV's combinatorial path coverage. For hypotheses where CPCV is genuinely tractable + valid (no time-ordering risk), the CPCV primitive remains preferred.
- The 8-point geometric grid is project-canon for the H053 family (k=42 features, IS train ≈ 1332). Other hypotheses at different k or n must re-derive their floor (15·k) and ceiling (post-purge IS train minus inner-CV reservation) per the same methodology.

**Open:**
- §-pin verification gaps from Round-2 plan-audit (Bergstra-Bengio §3, Tashman §4, Gneiting-Raftery Theorem 3.2, Niculescu-Mizil §4.2 Fig 4 + §3.2) tracked under follow-up `P1-PLAN-V3-CITATION-PIN-VERIFY` for ADR-0013 freeze.
- Inner-fold seed-sensitivity n_refits = 5 default; calibrate to 10-20 if the smoke run shows the 5-refit version is noisy. Tracked under `P1-PLAN-V3-INNER-FOLD-SENSITIVITY-N-REFITS-CALIBRATE`.

## Alternatives considered

1. **Keep CPCV + accept the Round-1 F-2-1 finding as residual risk.** Rejected — the CPCV time-ordering violation produces leakage of test-fold information into train-fold model selection; the BLOCK verdict is methodologically binding, not a stylistic preference.
2. **Replace CPCV with a single train/test cut.** Rejected — single-cut Sharpe has no sensitivity-analysis or window-selection robustness; gives no information about whether the result is a function of the (arbitrary) train-fold size. Walk-forward grid is the canonical alternative for this class of hypothesis.
3. **Random search over W_train (Bergstra-Bengio 2012) instead of geometric grid.** Considered — but at 8 cells, the random-search efficiency advantage over a geometric grid is negligible. The geometric grid is bit-reproducible and SPA-stackable, which random search is not without caveats.
4. **Multinomial K×3 Brier as binding gate.** Rejected per F-1-12 (carve-out scope violation; would require successor hypothesis ID).
5. **3-way calibrator selector with parsimony tie-break.** Rejected per F-1-7 (inverts NM&C 2005 Figure 4 empirical finding; no methodological basis).

## References

Cited inline above. Primary literature pre-checked in 2-round plan-audit-remediate-loop ([docs/audits/audit_trail_2026-05-03_h053-stage3-v3.md](../audits/audit_trail_2026-05-03_h053-stage3-v3.md)).
