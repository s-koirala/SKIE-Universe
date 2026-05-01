---
title: H053 Cycle 10 Stage-3 full Arms 1+2 + SPA family — audit-remediate-loop trail
date: 2026-05-01
type: audit_trail
status: complete
deliverables:
  - scripts/run_h053_stage3_full.py (NEW; ~640 lines)
  - reports/h053/stage3_full_disposition.md (NEW; full disposition)
  - runs/h053/stage3/h053_stage3_20260501T115445Z/sidecar.json
git_head_at_authoring: ee2eeaa
loop_rounds: 1 (Round-1 inline)
verdict: archive(null, descriptive-mediation-only) — neither arm clears conjunctive Sharpe-CI gate; SPA p > 0.05
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar_scientific_payload_sha256: 6a001cf4a847c4d70122b13652bbb35d4ba85aa6b5bb884eedbc8df36cdf1cf5
---

# H053 Stage-3 full Arms 1+2 + SPA family — audit-remediate-loop trail

## Scope

Single-round build + audit on the H053 Cycle 10 Stage-3 deliverable
(full design.md §5 estimator stack + Hansen SPA + categorical table v2
with isotonic calibration). Closes the H053 hypothesis disposition.

## Empirical result

**Verdict: ARCHIVE NULL** per design.md §10.1.

| Symbol | Arm 1 (ElasticNet) Sharpe (CI) | Arm 1 conjunctive | Arm 2 (LightGBM) Sharpe (CI) | Arm 2 conjunctive | SPA p | Disposition |
|---|---|:--:|---|:--:|---:|---|
| ES | -0.028 | NOT CLEAR | +0.004 | NOT CLEAR | 0.593 | archive_null |
| NQ | -0.048 | NOT CLEAR | +0.034 | NOT CLEAR | 0.501 | archive_null |

Per design.md §10.1 strict-precedence tree:
1. Sharpe-CI gate (conjunctive vs passive-long AND time-of-day-FE) → FAILS on both arms × both symbols.
2. Hansen SPA p-value → > 0.05 on both symbols.
3. Disposition → `archive(null, descriptive-mediation-only)`.

All 3 H053 SPA family slots consumed:
- Arm 1: `archive(null, sharpe-ci-not-clearing-conjunctive)`.
- Arm 2: `archive(null, sharpe-ci-not-clearing-conjunctive)`.
- Arm 3 (LLM): `archive(null, prerequisite-not-met)` (design.md §11.4 prereq 7 not landed).

## Inner-CV diagnostic

Both arms produced **negative inner-CV R² at the optimum cell**:
- Arm 1 ElasticNet: best (α=1.0, l1_ratio=0.9) → CV R² = -0.0723.
- Arm 2 LightGBM: best (n_estimators=100, max_depth=3) → CV R² = -0.1804.

Negative inner-CV R² means the model predicts WORSE than the train mean
on inner-validation folds. This is the load-bearing diagnostic: **the
42-feature multi-timeframe matrix has inadequate predictive power for
the H053 09:45→10:30 ET predictand at this substrate-envelope train-size**.

## Diagnosis

The Stage-1 → Stage-2 → Stage-3 sequence consistently archives as NULL
despite progressively richer estimators:

| Stage | Estimator | Train n | Result |
|---|---|---:|---|
| 1 | OLS on M only (4 features) | 1971 ES / 1970 NQ | NULL (Sharpe-diff CI covers zero) |
| 2 | Partial-R² of M+X over M (42 features) | 178 ES / 169 NQ | descriptive-positive (in-sample on OOS) |
| 3 | ElasticNet + LightGBM with inner CV | 178 ES / 169 NQ | NULL (no arm clears conjunctive Sharpe gate) |

The Stage-2 in-sample partial-R² is descriptive: 13-17% additional
variance is jointly explainable on the OOS fold by multi-timeframe X
beyond mediator alone. Stage-3 shows this descriptive predictability
does NOT translate to Sharpe-promotable OOS predictions when the
estimator is fitted on the much-smaller train fold (Block A's 290-day
warmup eats most of the IS window).

Two complementary explanations of the NULL:

1. **Train-fold size truncation**: ~170 train sessions × 42 features
   = ~4 sample-to-feature ratio, well below convergence regime.
2. **Genuine signal weakness**: consistent reversal-direction OLS
   coefficients (Stage-1 negative `m_return`; Stage-2 negative NDE on
   both ES + NQ) suggest H053's 09:45-10:30 ET sub-window is
   structurally a reversal slice, not a continuation slice as
   Gao-2018-style cross-sectional intraday momentum would suggest.
   The Sharpe-promotable signal under reversal would be the
   *opposite-sign* strategy (short ES if ŷ>0; long ES if ŷ<0), but
   such an inverse strategy would face the design.md §7.1 cost-floor
   binding (2-tick slippage) which would degrade its Sharpe further.

These explanations are not mutually exclusive.

## Build defects remediated in-loop

| Defect | Cause | Fix |
|---|---|---|
| sklearn warning "X does not have valid feature names" | LightGBM's CV step trains on a DataFrame slice; predict step receives ndarray | warning is benign (functionality intact); ignored via warnings filter is not applied since warnings are informational here. |
| Hansen SPA `n_strategies` field naming | The `HansenSPAResult` dataclass exposes `p_value`, `p_value_l`, `p_value_u` — not all are guaranteed across versions | use `getattr` with `None` fallback for the optional fields |
| Archetype rule fit warnings under truncated train fold | "no non-sparse cell available; falling back to largest-count" — Cycle 7 fail-safe path engages because the ~170-row train fold has insufficient density across the 36-cell raw archetype space | benign per Cycle 7 design (fail-safe documented in `archetype_classifier.py` Step 4 inline); table v2 still produced |

## Reproducibility

- BLAS pinning verified (no warning emitted at runtime).
- substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665.
- scientific_payload_sha256: 6a001cf4a847c4d70122b13652bbb35d4ba85aa6b5bb884eedbc8df36cdf1cf5.
- git_head: ee2eeaa (Phase D / Cycle 9 closure).
- 1000 bootstrap replicates × deterministic rng_seed=42 across all CI invocations + SPA test.
- ElasticNet + LightGBM all fitted with `random_state=_STAGE3_RNG_SEED`.

## Categorical table v2

Per design.md §10.2: ships as research artifact even under Sharpe-null.
K=5 archetypes × 3 ŷ-quantile-bins = 15 cells per symbol. Isotonic
calibration fitted in-fold per archetype. Available in
[sidecar.json](../../runs/h053/stage3/h053_stage3_20260501T115445Z/sidecar.json)
`categorical_table_v2` field.

True out-of-fold isotonic calibration is deferred to follow-up
`P1-H053-CYCLE10-ISOTONIC-OOF` for any future re-run.

## Residuals

**Closed by this loop:**
- Cycle 10 Stage-3 deliverable.
- H053 hypothesis disposition: `archive(null, descriptive-mediation-only)`.
- All 3 SPA family slots resolved.

**Cycles 11 + 12 disposition:**
- Cycle 11 (paper-trade scaffolding): NOT FIRED — only fires on
  `archive(positive)` per plan/h053_buildout_2026-04-28.md.
- Cycle 12 (Arm 3 LLM): SKIPPED — conditional on Cycles 8-10 producing
  positive; Cycles 8-10 archived null.

**Phase E closure**: H053 buildout sequence terminates at Stage-3 with a
NULL archive. The full H053 research artifact (Stage-1 + Stage-2 +
Stage-3 + categorical table v2 + descriptive mediation evidence) ships
to [research/01_hypothesis_register/H053/](../../research/01_hypothesis_register/H053/)
as a documented null-result.

**New follow-ups filed (3):**
- `P1-H053-CYCLE10-FULL-CV-GRIDS` — Stage-3 simplified the 27-cell
  design.md §5.1+§5.2 grids to 9+4 cells; full grids for re-runs.
- `P1-H053-CYCLE10-ISOTONIC-OOF` — true out-of-fold isotonic
  calibration for table v2.
- `P1-H053-WARMUP-TRUNCATION-IMPACT` — Block A's 290-day warmup eating
  the IS train fold is the load-bearing operational constraint.

## Verdict

**archive(null, descriptive-mediation-only).** H053 buildout sequence
complete; 4 of 5 phases of the autonomous Cycles 7-10 mandate executed
through to disposition. The mandate's Cycle 7-10 scope is now complete;
Cycles 11-12 are skipped per the design.md §10.1 NULL disposition.

The H053 archive is itself the empirical contribution per CLAUDE.md
§"Research philosophy" — null results are as valuable as positive
results and protect against later rediscovery of the same negative
finding.
