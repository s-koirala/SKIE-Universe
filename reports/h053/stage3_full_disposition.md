---
title: H053 Cycle 10 Stage-3 full Arms 1+2 + SPA family — disposition memo (FIRST-PASS; DISPOSITION REVERSED 2026-05-01)
date: 2026-05-01
type: stage3_disposition
status: ⚠ DISPOSITION REVERSED — original archive(null) verdict was based on a setup defect (Daily-block 405-bar gate truncation); H053 UN-ARCHIVED pending Stage-3 re-run after P1-H053-DAILY-405-GATE-RECONCILE
status_first_pass: ARCHIVE NULL — no arm clears conjunctive Sharpe gate on either ES or NQ; SPA p > 0.05 (NOT BINDING due to train-fold truncation; see appended §"Disposition reversed" below)
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar: runs/h053/stage3/h053_stage3_20260501T115445Z/sidecar.json
sidecar_scientific_payload_sha256: 6a001cf4a847c4d70122b13652bbb35d4ba85aa6b5bb884eedbc8df36cdf1cf5
git_head_at_authoring: ee2eeaa
recommendation_per_design_md_section_10_1: REVERSED — first-pass archive(null) NOT BINDING due to train truncation defect
overall_h053_disposition: UN-ARCHIVED 2026-05-01; awaiting Stage-3 re-run on a fixed Daily-gate
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

**NOT FIRED.** Per design.md §10.1 + plan/buildouts/h053_buildout_2026-04-28.md
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

---

## DISPOSITION REVERSED — appended 2026-05-01 (post-hoc diagnosis)

### What changed

User-prompted post-hoc inspection of the Cycle 10 Stage-3 run revealed
that the train fold was severely truncated (~178 sessions instead of
the expected ~1900) due to a substrate × feature-block defect:

- The H053 Daily block applies a strict `n_rth_bars == 405` gate per
  design.md §3.0 R1 binding (line 297 of [src/skie_ninja/features/h053/daily.py](../../src/skie_ninja/features/h053/daily.py)).
- The post-Cell-I substrate has **median 404 RTH bars per session
  pre-2022** (one bar systematically missing across 2015-2021); from
  2022 onward, sessions consistently emit 405 bars.
- Result: only **938 of 2710 ES sessions (35%)** and **943 of 2715 NQ
  sessions (35%)** survived the Daily gate. Joining with Hourly +
  Microstructure + Mediator yielded **178 train sessions on the IS
  fold** instead of the expected ~1900 (post-warmup).

Per-year RTH bar distribution (ES, full substrate):

| Year | n_sessions | n_405 | median_bars | min_bars |
|---|---:|---:|---:|---:|
| 2015 | 246 | 4 | 404 | 208 |
| 2016 | 247 | 1 | 404 | 208 |
| 2017 | 247 | 1 | 404 | 205 |
| 2018 | 248 | 64 | 404 | 208 |
| 2019 | 250 | 3 | 404 | 208 |
| 2020 | 245 | 3 | 404 | 208 |
| 2021 | 245 | 119 | 404 | 209 |
| 2022 | 245 | 237 | 405 | 209 |
| 2023 | 246 | 237 | 405 | 209 |
| 2024 | 252 | 243 | 405 | 205 |
| 2025 | 237 | 228 | 405 | 208 |

Pre-2022: a tiny minority of sessions reach 405 bars; vast majority
reach 404. Post-2022: a strong majority reach 405. The single missing
RTH bar pre-2022 is either the 09:30 ET prior-bar reference, the
16:15 ET RTH-close bar, or a substrate-vendor cleanup-version
boundary (likely a vendor cleanup that started 2022).

### Why this invalidates the first-pass archive(null) disposition

With sample-to-feature ratio ~4 (178 train × 42 features), both
ElasticNet and LightGBM hit **negative inner-CV R² at the optimum cell**
(Arm 1 -0.0723; Arm 2 -0.1804). This is the canonical small-train-overfit-fail
pattern — NOT a clean test of "does the multi-timeframe X carry
predictive content for the H053 09:45-10:30 ET predictand". The model
literally cannot fit on the truncated train fold.

The conjunctive Sharpe-CI gate then fails because both arms produce
near-zero OOS Sharpe; that's downstream of the model failing to fit,
not of the underlying signal being absent.

### What still holds (genuinely)

- **Stage-1 NULL** with the **full 1971-session IS train fold × 4
  mediator features**: paired Sharpe-CI does not exclude zero on either
  ES or NQ. This is a clean test on a sample where the Daily-gate defect
  does NOT apply (the mediator block doesn't depend on Daily). The
  opening-15-min mediator alone does NOT carry a Sharpe-promotable
  signal at the H053 09:45-10:30 ET slice on ES/NQ. **Stage-1 NULL is
  genuine evidence.**
- **Stage-2 partial-R² 13-17% in-sample on OOS** is descriptive
  evidence that multi-timeframe X carries some additional explanatory
  variance over mediator alone in-sample on the OOS fold — but Stage-2's
  178-session train was already truncated by the same Daily-gate defect.

### What needs re-running

Cycle 10 Stage-3 must be re-run after the Daily-gate defect is fixed.
New BLOCKING-BEFORE-NEXT-STAGE-3 follow-up: `P1-H053-DAILY-405-GATE-RECONCILE`.

Two paths to fix (decision pending):

(a) **Relax the Daily gate to `n_rth_bars >= 404`** with a `# justify:`
    comment documenting the substrate's pre-2022 missing-bar pattern
    + a regression test asserting the gate accepts the empirical 404-bar
    pre-2022 sessions. This adds <0.25% missing-bar-noise to the daily
    OHLC aggregation (1 bar of 405 ≈ 0.247%); for SMA50/SMA200
    smoothing the impact is sub-bp.

(b) **Substrate-side fix**: identify which RTH bar is systematically
    missing pre-2022 (likely 09:30 ET via per-session bar-time inspection),
    add it to the substrate via a vendor-data re-ingest or interpolation,
    and re-pin the substrate_dataset_checksum.

Path (a) is faster and operationally sufficient; (b) is more rigorous
and the canonical fix. The decision goes through its own audit-remediate-loop
when prioritised.

### Disposition status (binding)

H053 is **UN-ARCHIVED 2026-05-01**. Status returns to "Cycle 10 first-pass
ran with truncated train fold; Stage-3 re-run pending Daily-gate fix".
The Stage-1 + Stage-2 + Stage-3 first-pass artifacts SHIP as a
documented build-session record (this memo + the audit trails), but the
Stage-3 verdict is NOT a binding archive disposition.

The full H053 build-session error/mistake record is appended to the H050
production-run post-mortem at
[docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md §H053 build-session findings](../../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md).

### Audit trail of the disposition reversal

[docs/audits/audit_trail_2026-05-01_h053-disposition-reversal.md](../../docs/audits/audit_trail_2026-05-01_h053-disposition-reversal.md).
