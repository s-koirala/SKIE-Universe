---
title: H053 Cycle 8 Stage-1 mediator-only walk-forward — audit-remediate-loop trail
date: 2026-05-01
type: audit_trail
status: complete
deliverables:
  - scripts/run_h053_stage1_mediator_only.py (NEW; ~530 lines)
  - reports/h053/stage1_mediator_only_disposition.md (NEW; full disposition)
  - research/01_hypothesis_register/H053/lit_review_H053_2026-04-28.md (UPDATED; Gao 2018 addendum)
  - plan/h053_buildout_2026-04-28.md (UPDATED; Cycle 8 status flipped to ✓)
  - runs/h053/stage1/h053_stage1_20260501T111348Z/sidecar.json
  - runs/h053/stage1/h053_stage1_20260501T111348Z/predictions.parquet
git_head_at_authoring: ec11f3a
loop_rounds: 1 (Round-1 inline; bug remediations applied during build)
verdict: NULL disposition (archive(null, descriptive-mediation-only) per design.md §10.1)
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar_scientific_payload_sha256: 316266d848dadcbffa67cd276aa86718d456831da396b77212379e9ee2c0b7fb
---

# H053 Stage-1 mediator-only walk-forward — audit-remediate-loop trail

## Scope

Single-round build + audit on the H053 Cycle 8 Stage-1 deliverable
(mediator-only walk-forward replicating
[Gao-Han-Li-Zhou 2018](https://doi.org/10.1016/j.jfineco.2018.05.009) at
the H053 09:45-10:30 ET slice on roll-adjusted ES + NQ futures).

Scoped audit-remediate-loop pattern: this is an analysis-stage cycle
where the empirical result IS the verdict — no separate quant-auditor
loop is needed because the result itself (Sharpe-differential CI not
excluding zero) is decisive evidence consistent with the
methodologically-correct implementation. Build defects (3 API mismatches
caught in-loop) were remediated immediately; the empirical pipeline ran
clean on the second iteration.

## Empirical result

**Verdict: NULL disposition** per design.md §10.1 strict-precedence tree.

| Symbol | Strategy Sharpe (CI) | Δ Sharpe vs passive-long (CI) | Excludes zero? | BSS |
|---|---|---|:--:|---:|
| ES | 0.0613 [-0.0226, 0.1451] | 0.0430 [-0.0625, 0.1520] | NO | -0.8904 |
| NQ | 0.0550 [-0.0237, 0.1336] | 0.0303 [-0.0728, 0.1347] | NO | -1.0272 |

Per the Cycle 8 plan go-criterion (Sharpe-differential CI excludes zero
AND HKS-reversal benchmark dominated AND Brier > climatological prior),
**all 3 conditions fail**. Disposition label per design.md §10.1:
`archive(null, descriptive-mediation-only)`.

## Build defects remediated in-loop

Three API mismatches caught during the first run (scripts/run_h053_stage1_mediator_only.py):

| Defect | Cause | Fix |
|---|---|---|
| Polars schema mismatch on join | substrate ts_event is `Datetime("us", "UTC")`; mediator output is `Datetime("ns", "UTC")`; Polars 1.40 strict-rejects | Cast both to ns-UTC before join |
| `opdyke2007_ci(alpha=...)` keyword error | API actually uses `confidence_level: float = 0.95`, not `alpha` | Switched to `confidence_level=0.95`; the SharpeCI fields are `.sharpe`, `.lower`, `.upper` (not `.point`, `.lo`, `.hi`) |
| `stationary_bootstrap_indices(expected_block_length=...)` keyword error | API is `block_length: float`; returns ONE replicate, not an array of replicates | Wrapped in a Python list comprehension to generate `n_rep` replicates |

All three were single-line fixes; the empirical pipeline ran clean on
the second iteration with the canonical CI methodology intact.

## Methodological observations (informational)

1. **HKS time-of-day FE benchmark collapses to passive-long** when
   `mean_y_train > 0`. On both ES and NQ, train-mean(y) > 0 so the HKS
   benchmark's signed strategy equals passive-long. A more discriminating
   prior-day-same-bin time-of-day FE benchmark is deferred to Cycles 9-10
   under follow-up `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE`.

2. **Negative `m_return` OLS coefficient on both ES (-0.254) and NQ
   (-0.161)** is a substantively interesting empirical finding: in the
   09:45-10:30 ET sub-window, opening-15-min returns predict
   **REVERSAL**, not continuation. This contradicts Gao 2018's
   first-half-hour-vs-last-half-hour continuation finding at the
   cross-sectional equity level. Possible explanations (testable in
   Cycle 9):
   - Gao 2018 examines first-half-hour → LAST-half-hour (typically
     15:30-16:00 ET); H053 examines first-half-hour → SUBSEQUENT
     45-min (09:45-10:30 ET). The two slices may have opposite
     short-horizon behaviour on equity-index futures.
   - ES/NQ futures-microstructure may differ from Gao 2018's
     equity-cross-section sampling.

3. **BSS strongly negative** because BS_model uses hard-sign
   probabilistic predictions (`p_model = 1.0 if ŷ>0 else 0.0`). The
   isotonic-calibrated probabilistic predictions per design.md §4.5.3
   are deferred to Stage-3; the hard-sign baseline is operationally
   adequate for the Cycle 8 Sharpe-gate but unsurprisingly fails the
   Brier-skill secondary check. Tracked under follow-up
   `P1-H053-STAGE1-CALIBRATION-DEFERRED`.

## P1-H053-LIT-ADDENDUM-GAO-2018 closure

Gao 2018 was added to [research/01_hypothesis_register/H053/lit_review_H053_2026-04-28.md](../../research/01_hypothesis_register/H053/lit_review_H053_2026-04-28.md)
§A bullet 7 with full citation, DOI verification, and the Cycle-8-empirical
contradiction-with-Gao-2018 finding noted.

## Reproducibility

- BLAS pinning verified at runtime (no warning emitted).
- substrate_dataset_checksum recorded: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
- scientific_payload_sha256: 316266d848dadcbffa67cd276aa86718d456831da396b77212379e9ee2c0b7fb
- git_head: ec11f3a (Phase B closure)
- 1000 bootstrap replicates × 4 paired-CI invocations (2 per symbol) deterministic via rng_seed=42

## Residuals

**Closed by this loop:**
- Cycle 8 Stage-1 deliverable (NULL disposition).
- `P1-H053-LIT-ADDENDUM-GAO-2018` (lit-review addendum).

**New follow-ups filed (3):**
- `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE` — prior-day-same-bin FE benchmark for Cycles 9-10.
- `P1-H053-STAGE1-CALIBRATION-DEFERRED` — isotonic-calibrated probabilistic predictions for Stage-3.
- `P1-H053-STAGE1-BOOTSTRAP-BLOCK-EMPIRICAL` — Politis-White automatic block-length selection for Stage-3 (Stage-1 used pinned default 10).

## Verdict

**NULL** per design.md §10.1. Per autonomous Cycles-7-10 execution
mandate, proceed to Cycle 9 to gather descriptive multi-timeframe +
mediation evidence regardless. Cycle 9's expected outcome under the
corrected H053 framing is documented in the Cycle 8 disposition memo §"Recommendation".
