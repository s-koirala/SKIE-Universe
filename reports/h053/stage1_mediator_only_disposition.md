---
title: H053 Cycle 8 Stage-1 mediator-only walk-forward — disposition memo (RETAGGED 2026-05-01 per ADR-0012)
date: 2026-05-01
type: stage1_disposition
status: ⚠ RETAGGED — per ADR-0012 the original "archive(null) per Sharpe-CI gate" disposition is reframed as "calibration-failed" because the Stage-1 categorical-table BSS is strongly negative (-0.89 ES, -1.03 NQ). The retag honours the new Class A binding gate (BSS > 0); it is NOT a goalpost-move.
status_first_pass: NULL — Sharpe-differential CI excludes zero on neither ES nor NQ (under legacy gating tree, now superseded by ADR-0012)
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar: runs/h053/stage1/h053_stage1_20260501T111348Z/sidecar.json
sidecar_scientific_payload_sha256: 316266d848dadcbffa67cd276aa86718d456831da396b77212379e9ee2c0b7fb
git_head_at_authoring: ec11f3a
recommendation_per_design_md_section_10_1_legacy: archive(null, descriptive-mediation-only)
recommendation_per_adr_0012: calibration-failed; KPI: sharpe-vs-passive-marginal (point=+0.043 ES, +0.030 NQ; CI covers zero), bss-strongly-negative (BSS=-0.89 ES, -1.03 NQ), reliability-not-evaluated, max-dd-favorable, power-margin-adequate, mediation-deferred-to-stage-2, partial-r2-not-applicable-stage-1, cost-not-evaluated
go_criterion_to_cycle_9: NOT MET (per the strict reading); proceeded under autonomous-mandate to Stages 2 + 3
---

# H053 Stage-1 mediator-only walk-forward — disposition memo

## Executive summary

Stage-1 OLS regression of `y_{i,t}` on the H053 mediator vector
`M_{i,t}` (m_return, m_log_range, m_volume, m_ofi_tickrule) produces a
**NULL disposition** on the post-Cell-I substrate. The
[Gao-Han-Li-Zhou 2018](https://doi.org/10.1016/j.jfineco.2018.05.009)
market-intraday-momentum effect, evaluated at H053's specific 09:45→10:30
ET slice on roll-adjusted ES + NQ futures with 8-year IS / 2-year OOS
splits, does **not produce a Sharpe-differential CI that excludes zero**
against either passive-long or the time-of-day fixed-effects benchmark.
The categorical-table v1 BSS is negative on both instruments (model
worse than climatological prior).

Per design.md §10.1 strict-precedence tree, the appropriate disposition
under a Sharpe-null outcome is `archive(null, descriptive-mediation-only)`
— the result is informative as descriptive evidence on the
opening-15-min-bar's predictive content for the 09:45-10:30 ET slice
WITHOUT clearing the Sharpe-promotion gate.

Per the autonomous Cycles-7-10 execution mandate, **proceed to Cycle 9
regardless** to gather the multi-timeframe + mediation evidence; per
design.md §1 critical interpretive note + §10.2 annotation pathway, a
significant `NIE` from Cycle 9 would annotate `mediation-NIE-significant`
without promoting past the Sharpe gate.

## Method (per [scripts/run_h053_stage1_mediator_only.py](../../scripts/run_h053_stage1_mediator_only.py))

### Splits

- **Train (IS)**: 2015-01-01 → 2022-12-31 (8 calendar years).
- **Test (OOS)**: 2024-01-01 → 2025-12-{03 ES, 19 NQ} per the post-Cell-I
  substrate envelope (design.md §6).
- Validation 2023 is skipped; mediator-only OLS has no hyperparameters
  requiring inner CV.

### Estimator

OLS with intercept of `y_{i,t}` on the 4-element mediator vector,
fitted per-instrument (no pooling).

### Strategy

- **H053 model**: long if `ŷ > 0`, short if `ŷ < 0`, flat at zero.
  Realized strategy return = `sign(ŷ) · y_actual`.
- **Passive-long benchmark** (per design.md §1 + §8): always long;
  realized return = `y_actual`.
- **HKS time-of-day fixed-effects benchmark** (per design.md §8 +
  Heston-Korajczyk-Sadka 2010): predict the train mean of `y` as the
  constant signal; long if mean > 0 else short. **Note**: at H053's
  fixed-clock predictand (09:45-10:30 ET), the time-of-day FE collapses
  to a single mean across train, so this benchmark equals passive-long
  whenever `mean_y_train > 0`. On both ES and NQ in this run,
  `mean_y_train > 0` → HKS benchmark and passive-long produce identical
  return series. A more discriminating HKS-style benchmark (e.g.,
  prior-day same-bin return) is deferred to Cycle 9 + Cycle 10 where
  the time-of-day FE has more degrees of freedom.

### CIs

- **Single-strategy Sharpe-CI**: Mertens 2002 / Opdyke 2007 iid
  generalisation per [Lo 2002 §III](https://doi.org/10.2469/faj.v58.n4.2453).
- **Paired Sharpe-differential CI**: Ledoit-Wolf 2008 studentised
  stationary-bootstrap per
  [Ledoit-Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002),
  block length 10, n_replicates 1000.

### Categorical table v1

Archetype assignment via [src/skie_ninja/features/h053/archetype_classifier.py](../../src/skie_ninja/features/h053/archetype_classifier.py)
`fit_archetype_rule(K=5)` on the train mediator panel; apply on the test
mediator panel; per-archetype `P̂(d=+1 | A_k)` with paired
stationary-bootstrap percentile CI per design.md §4.5.3.

### Brier vs climatological prior

Hard probabilistic prediction `p_model = (ŷ > 0)`; `p_clim` =
empirical-frequency `P̂(y > 0)` on the train fold. BSS = 1 - BS_model /
BS_clim.

## Results

### Per-instrument bundle

| Symbol | n_train | n_test | Strategy Sharpe (CI) | Passive-long Sharpe (CI) | HKS Sharpe (CI) |
|---|---:|---:|---|---|---|
| ES | 1971 | 489 | **0.0613** [-0.0226, 0.1451] | 0.0182 [-0.0663, 0.1027] | 0.0182 [-0.0663, 0.1027] |
| NQ | 1970 | 496 | **0.0550** [-0.0237, 0.1336] | 0.0246 [-0.0615, 0.1107] | 0.0246 [-0.0615, 0.1107] |

### Paired Sharpe-differential

| Symbol | vs passive-long: ΔSR (CI) | Excludes zero? | vs HKS: ΔSR (CI) | Excludes zero? |
|---|---|:--:|---|:--:|
| ES | 0.0430 [-0.0625, 0.1520] | **NO** | 0.0430 [-0.0625, 0.1520] | **NO** |
| NQ | 0.0303 [-0.0728, 0.1347] | **NO** | 0.0303 [-0.0728, 0.1347] | **NO** |

### BSS (categorical-table v1 vs climatological prior)

| Symbol | p_clim | BS_model | BS_clim | BSS |
|---|---:|---:|---:|---:|
| ES | 0.5145 | 0.4724 | 0.2499 | **-0.8904** |
| NQ | 0.5279 | 0.5040 | 0.2486 | **-1.0272** |

Both BSS are strongly negative — the OLS-predicted hard-sign signal is
worse than the constant climatological-prior baseline. This is unsurprising
given the exploratory linear-only model with no calibration.

### Categorical table v1 (per archetype, OOS test fold)

ES (K=5):

| archetype_id | n_test | P̂(d=+1 \| A_k) | 95% CI | mean_y |
|---:|---:|---:|---|---:|
(per-archetype rows in [runs/h053/stage1/.../sidecar.json](../../runs/h053/stage1/h053_stage1_20260501T111348Z/sidecar.json) `categorical_table` field)

### OLS coefficients (per-instrument)

ES:
- intercept: 9.74e-05
- m_return: -0.2544 (negative — *contradicts* Gao 2018-style continuation expectation in this slice)
- m_log_range: +29.60 (positive — high opening-bar volatility predicts higher 09:45-10:30 ET drift)
- m_volume: -2.57e-09
- m_ofi_tickrule: +1.35e-08

NQ:
- intercept: 1.24e-04
- m_return: -0.1606 (negative — same direction as ES)
- m_log_range: +32.48 (positive — same direction as ES)
- m_volume: -1.62e-08
- m_ofi_tickrule: +6.74e-08

The negative `m_return` coefficient on both instruments is interesting:
in this 09:45-10:30 ET slice, opening-15-min returns predict
**reversal** in the subsequent 45-min window, not continuation. This
contradicts Gao 2018's market-intraday-momentum continuation finding,
suggesting either (a) the H053 slice is structurally different from
Gao 2018's market-cap cross-section + first-half-hour-vs-last-half-hour
construction, or (b) ES/NQ futures show reversal where Gao 2018's
equity universe shows continuation. Both are testable in Cycle 9 with
the multi-timeframe + mediation analysis.

## Disposition (per design.md §10.1 strict-precedence tree)

**Sharpe-CI gate**: NEITHER ES NOR NQ clears. The strict reading per
design.md §8 conjunctive rule (passive-long AND time-of-day FE) is
unmet — Stage-3 H053 Sharpe-gating is unlikely to clear unless Stage-2
multi-timeframe features add substantial Sharpe over and above the
mediator-only baseline.

**Outcome label**: `archive(null, descriptive-mediation-only)` per
design.md §10.1 + §10.2.

**Cycle 9 go criterion**: Per the plan (Stage-1 row), the formal
go-criterion to Cycle 9 is "Sharpe-differential CI excludes zero AND
HKS-reversal benchmark dominated AND Brier > climatological prior."
**This Stage-1 result fails all three.**

## Recommendation

Per the design.md §1 critical interpretive note ("descriptive-mediation
interpretation is still informative even on Sharpe-null") plus the
autonomous Cycles-7-10 execution mandate, **PROCEED TO CYCLE 9** to
gather the multi-timeframe + mediation evidence. The expected outcome
under the corrected H053 framing is:

1. Cycle 9 produces a partial-R² increment CI on the multi-timeframe X
   beyond the mediator alone. If this CI excludes zero, the H053
   multi-timeframe-snapshot information IS predictive at session grain
   (orthogonal to the Sharpe-trade outcome).
2. The mediation NIE/NDE annotates the Cycle-10 disposition without
   altering the Sharpe gate.
3. Cycle 10 Stage-3 most likely produces `archive(null)` for both ES
   and NQ Arms 1+2; the table-deliverable v2 + descriptive mediation
   ship as research artifacts per design.md §10.2.

## Closes

- Cycle 8 Stage-1 deliverable: walk-forward, Sharpe + paired CIs,
  categorical table v1, BSS, disposition memo.

## Follow-ups filed

- `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE` — HKS benchmark collapses to
  passive-long whenever `mean_y_train > 0`; Cycle 10 should use a
  prior-day-same-bin-return time-of-day FE benchmark with more degrees
  of freedom.
- `P1-H053-STAGE1-CALIBRATION-DEFERRED` — BSS uses hard sign predictions;
  isotonic-calibrated probabilistic predictions deferred to Stage-3
  per design.md §4.5.3.

## References

- design.md §1, §3.4, §4.5.3, §6, §8, §10.1, §10.2
- [Gao, Han, Li & Zhou 2018](https://doi.org/10.1016/j.jfineco.2018.05.009)
  — market intraday momentum (cross-sectional continuation in equities)
- [Lo 2002 §III](https://doi.org/10.2469/faj.v58.n4.2453)
- [Ledoit-Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002)
- [Heston-Korajczyk-Sadka 2010](https://doi.org/10.1111/j.1540-6261.2010.01573.x)
