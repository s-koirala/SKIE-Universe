---
title: H053 Cycle 10 Stage-3 full Arms 1+2 + SPA family — disposition memo
date: 2026-05-01
type: stage3_disposition
status: ARCHIVE NULL — no arm clears conjunctive Sharpe gate on either ES or NQ; SPA p > 0.05
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar: runs/h053/stage3/h053_stage3_20260501T115445Z/sidecar.json
sidecar_scientific_payload_sha256: 6a001cf4a847c4d70122b13652bbb35d4ba85aa6b5bb884eedbc8df36cdf1cf5
git_head_at_authoring: ee2eeaa
recommendation_per_design_md_section_10_1: archive(null) — Sharpe-CI gate not cleared; SPA p > α
overall_h053_disposition: archive(null, descriptive-mediation-only)
---

# H053 Stage-3 full Arms 1+2 + SPA family — disposition memo

## Executive summary

**OVERALL DISPOSITION: ARCHIVE NULL.**

Stage-3 fits the full design.md §5 estimator stack (Arm 1 ElasticNet,
Arm 2 LightGBM) with inner-WF CV grid selection on the IS train fold,
then evaluates on the 2024-2025 OOS test fold against passive-long and
time-of-day fixed-effects benchmarks. **Neither arm clears the conjunctive
Sharpe-CI gate** on either ES or NQ; Hansen SPA p > 0.05 on both
instruments.

| Symbol | Arm 1 Sharpe (CI) | Arm 1 vs passive | Arm 1 vs ToD-FE | Arm 2 Sharpe (CI) | Arm 2 vs passive | Arm 2 vs ToD-FE | SPA p | Disposition |
|---|---|:--:|:--:|---|:--:|:--:|---:|---|
| ES | -0.028 | NO | NO | +0.004 | NO | NO | 0.593 | archive_null |
| NQ | -0.048 | NO | NO | +0.034 | NO | NO | 0.501 | archive_null |

Per the design.md §10.1 strict-precedence tree:

```
1. Sharpe-CI gate (conjunctive vs passive-long AND time-of-day-FE)
   → FAILS on both arms × both symbols
2. Hansen SPA p-value
   → > 0.05 on both symbols (no SPA-significant arm)
3. Disposition → archive(null)
```

Combined with the Cycle 9 Stage-2 partial-R² CI excluding zero (descriptive,
in-sample on OOS) and the Cycle 8 Stage-1 NULL disposition (mediator-only
also failed the Sharpe gate), the H053 multi-timeframe-snapshot hypothesis
is **archived as null** with a `descriptive-mediation-only` annotation
per design.md §10.2 (descriptive partial-R² evidence at the multi-timeframe
level + directionally-consistent NIE point estimates from Cycle 9, even
without Sharpe-significance).

## Per-instrument detail

### ES

- Train n=178, Test n=367 (after Block A SMA200 + 60-day RV warmup).
- **Arm 1 ElasticNet**: best inner-CV cell α=1.0, l1_ratio=0.9; CV R²=-0.0723
  (negative — model predicts worse than the train mean on inner-fold validation).
  OOS strategy Sharpe -0.028; both paired-CI checks (vs passive AND vs ToD-FE)
  fail to exclude zero.
- **Arm 2 LightGBM**: best cell n_estimators=100, max_depth=3; CV R²=-0.1804
  (also negative). OOS strategy Sharpe +0.004; same two-failure conjunctive-gate.
- **Hansen SPA**: relative-performance matrix d ∈ ℝ^(367, 2) where columns are
  (arm1_return - passive_return, arm2_return - passive_return). p_consistent =
  0.5930 — far from significance.
- **Categorical table v2**: K=5 archetypes × 3 ŷ-quantile-bins per archetype with
  isotonic calibration. Ships as research artifact per design.md §10.2 even
  under Sharpe-null. Detailed cells in [sidecar.json](../../runs/h053/stage3/h053_stage3_20260501T115445Z/sidecar.json) `categorical_table_v2`.

### NQ

- Train n=169, Test n=372.
- **Arm 1 ElasticNet**: best cell α=1.0, l1_ratio=0.9; CV R²=-0.0723.
  OOS Sharpe -0.048.
- **Arm 2 LightGBM**: best cell n_estimators=100, max_depth=3; CV R²=-0.1804.
  OOS Sharpe +0.034.
- **Hansen SPA**: p_consistent = 0.5010.

## Diagnosis

The inner-CV R² being negative on BOTH arms at the optimum hyperparameter cell
is the load-bearing finding: **the 42-feature multi-timeframe matrix has
inadequate predictive power for the H053 09:45→10:30 ET predictand at this
substrate envelope**. Two complementary explanations:

1. **Train-fold size truncation**. The Block A daily features (SMA50, SMA200,
   60-day RV, weekly trend slope, daily YZ vol) require ~290 calendar days of
   warmup, eating the first ~14 months of the 8-year IS window and leaving only
   ~170 train sessions. With 42 features, the effective sample-to-feature ratio
   is ~4 — well below the convergence regime for both ElasticNet and LightGBM.

2. **Genuine signal weakness in the H053 slice**. Stage-1 (mediator-only
   linear) showed negative `m_return` coefficient (reversal not continuation);
   Stage-2 NDE was strongly negative on both ES and NQ (multi-timeframe
   reversal beyond the mediator); Stage-3 inner-CV R² is negative on both
   arms. This is a consistent pattern: the H053 09:45→10:30 ET sub-window
   exhibits short-horizon reversal across mediator + multi-timeframe
   features, and the Sharpe-promotable signal that reversal would suggest
   (short ESif ŷ>0 / long ES if ŷ<0) is washed out by the cost-floor
   considerations baked into the design.md §7.1 binding (2-tick slippage
   floor; not exercised in Stage-3 but would degrade the inverse-strategy
   Sharpe further).

These two explanations are not mutually exclusive. The Stage-1 + Stage-2 +
Stage-3 sequence consistently archives as NULL despite using progressively
richer estimators on the same data — the simplest reading is that the
H053-pre-registered multi-timeframe snapshot at 09:45 ET has descriptive
partial-R² (Stage-2: 0.13-0.17 in-sample on OOS) but does NOT translate to
OOS Sharpe-promotable predictive content.

## Disposition (per design.md §10.1)

**Outcome label**: `archive(null, descriptive-mediation-only)` per
design.md §10.1 + §10.2.

**SPA family slot consumption** (per design.md §8):
- Arm 1 (ElasticNet) slot: consumed as `archive(null, sharpe-ci-not-clearing-conjunctive)`.
- Arm 2 (LightGBM) slot: consumed as `archive(null, sharpe-ci-not-clearing-conjunctive)`.
- Arm 3 (LLM) slot: consumed as `archive(null, prerequisite-not-met)` (design.md §11.4
  prereq 7 deterministic-replay scaffolding never landed).

All 3 ex-ante SPA slots resolved.

## What ships as research artifact (per design.md §10.2)

Even under Sharpe-null, the following ship as research artifacts:

1. **Categorical-table v2** with isotonic-calibrated probabilities per
   archetype × ŷ-quantile-bin. Available in [sidecar.json](../../runs/h053/stage3/h053_stage3_20260501T115445Z/sidecar.json)
   `categorical_table_v2` field per symbol.
2. **Cycle 9 partial-R² + NIE/NDE descriptive evidence**: multi-timeframe
   X has 13-17% in-sample partial-R² on OOS test fold; NIE point positive,
   NDE point negative on both ES + NQ.
3. **Stage-1 + Stage-2 + Stage-3 Sharpe-comparison ledger** as a documented
   negative result: the H053 09:45→10:30 ET slice does NOT translate
   Gao-2018-style cross-sectional intraday momentum into a single-instrument
   Sharpe-promotable signal on ES/NQ futures.

These artifacts ship to the per-hypothesis register
([research/01_hypothesis_register/H053/](../../research/01_hypothesis_register/H053/))
and are referenced from the hypothesis-backlog null-result section
(per CLAUDE.md §"Research philosophy" — "null results are as valuable as
positive results and protect against later rediscovery").

## Cycle 11 paper-trade scaffolding

**NOT FIRED.** Per design.md §10.1 + plan/h053_buildout_2026-04-28.md
Cycle 11 row, paper-trade scaffolding only fires on `archive(positive)`.
H053 archives as null; Cycle 11 is **skipped**. The 60-session-day
paper-trade clock does NOT start.

## Cycle 12 LLM Arm 3

**SKIPPED.** Per plan §Cycles, Cycle 12 is "conditional on Cycles 8-10
outcomes". With Arms 1+2 archived null, the cost-benefit of building the
deterministic-replay scaffolding for an LLM arm is negative; the Arm 3
SPA slot is already consumed as `archive(null, prerequisite-not-met)`.
H053 finishes at the Stage-3 disposition.

## Closes

- Cycle 10 Stage-3 deliverable: full Arms 1+2 + SPA family + categorical
  table v2 + isotonic calibration.
- All 3 H053 SPA family slots resolved.
- H053 archive disposition: `archive(null, descriptive-mediation-only)`.

## Follow-ups filed

- `P1-H053-CYCLE10-FULL-CV-GRIDS` — design.md §5.1+§5.2 27-cell grids
  were operationally simplified to 9+4 = 13 cells for Stage-3; full
  grids deferred for any future re-run.
- `P1-H053-CYCLE10-ISOTONIC-OOF` — isotonic calibration is fitted
  in-fold per archetype; true out-of-fold isotonic deferred for table-v2
  promotion if Cycle 11 ever fires for a sibling hypothesis.
- `P1-H053-WARMUP-TRUNCATION-IMPACT` — the ~170-session train fold after
  Block A warmup is the load-bearing operational constraint; future
  re-runs should split-train the multi-timeframe X separately so Block
  A's warmup eats less of the IS window.

## References

- design.md §1, §3, §4.5.3, §5, §6, §8, §10.1, §10.2, §11
- [Zou & Hastie 2005 *JRSS-B* 67(2):301-320](https://doi.org/10.1111/j.1467-9868.2005.00503.x)
- [Friedman 2001 *Annals of Statistics* 29(5):1189-1232](https://doi.org/10.1214/aos/1013203451)
- [Niculescu-Mizil & Caruana 2005 *ICML*](https://doi.org/10.1145/1102351.1102430)
- [Hansen 2005 *JBES* 23(4):365-380](https://doi.org/10.1198/073500105000000063)
- [Ledoit & Wolf 2008 *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002)
- [Lo 2002 *FAJ* 58(4):36-52](https://doi.org/10.2469/faj.v58.n4.2453)
- [Gao, Han, Li & Zhou 2018 *JFE* 129(2):394-414](https://doi.org/10.1016/j.jfineco.2018.05.009)
