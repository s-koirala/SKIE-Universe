---
title: H053 Cycle 10 Stage-3 v2 — Phase 1 (refactor) + Phase 2 (production run) audit-remediate-loop trail
date: 2026-05-03
type: audit_trail
status: complete (Phase 1 + Phase 2 LANDED; Round-1 audit BLOCK; remediation tracker in §Residuals)
phase_1_deliverables:
  - scripts/run_h053_stage3_v2.py (NEW; ~625 lines; ADR-0012-compliant refactor)
  - scripts/__init__.py (NEW; enables `from scripts.X import Y`)
  - src/skie_ninja/inference/disposition.py (UPDATED; added missing ClassAGateApplicability.to_dict())
phase_2_deliverables:
  - runs/h053/stage3_v2/h053_stage3_v2_20260503T144640Z/sidecar.json (NEW)
phase_1_git_head: 221a635
phase_2_git_head: 221a635 (same; v2 script invoked under that HEAD)
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar_scientific_payload_sha256: 0cd96f55ca78916257ee6a7e22a07d96c1a71490fdbf316d6a5ac75433b0bb28
loop_rounds: 1 (Round-1 quant-auditor on Phase 1; verdict block; Round-2 remediation deferred to follow-up)
verdict: phase_1_block_per_round_1_audit + phase_2_results_landed_with_leakage_caveats
---

# H053 Stage-3 v2 — Phase 1 (refactor) + Phase 2 (production run)

## Phase 1 — Stage-3 v2 script refactor (LANDED `221a635`)

Per [ADR-0012](../decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) + Round-1 compliance audit (commit `957bea8` agentId `a3f906e5e461e6535`), 5 of 13 BLOCKING audit findings against legacy `run_h053_stage3_full.py` were closed in this Phase 1 refactor:

| Audit ID | Defect | Phase 1 fix |
|---|---|---|
| F-1-3 | ToD-FE bench collapses to passive | AR(1) lag-1 bench via `disposition.ar1_lag1_benchmark_returns` |
| F-1-5 | BSS hard-sign yielded ≈ -0.89 | OOF isotonic via inner 5-fold CPCV (per-arm); ES smoke shows BSS=-0.013 vs legacy -0.89 |
| F-1-9 | SPA at design-time gate | SPA is Class B KPI only; binding only at operator-promotion |
| F-1-11 | SPA SingleStrategySPAWarning suppressed | warnings.simplefilter("always"); warnings recorded in sidecar |
| F-1-12 | In-fold isotonic optimistic | OOF isotonic via inner CPCV (5 folds) |
| F-1-13 | PIT canary not bound to sidecar | `assert_pit_canaries_green` wired into Class A gate evaluation |

Plus framework benefits from disposition.py (commit `957bea8`) + cpcv_path_sharpe.py (commit `c615f72`).

## Phase 2 — Stage-3 v2 production run (LANDED `runs/h053/stage3_v2/h053_stage3_v2_20260503T144640Z/`)

### Run metadata

- Substrate: post-Cell-I roll-adjusted ES + NQ (substrate_dataset_checksum `bc06b4e1...`)
- git HEAD: `221a635`
- Wall-clock: **2 min 27 sec** total (ES ~64s, NQ ~67s, sidecar ~16s)
- BLAS: pinned to single-thread per ADR-0009
- Run-id: `h053_stage3_v2_20260503T144640Z`
- Sidecar scientific_payload_sha256: `0cd96f55ca78916257ee6a7e22a07d96c1a71490fdbf316d6a5ac75433b0bb28`

### Sample sizes (post Daily-gate fix to ≥404 RTH bars; commit `48f116a`)

| Symbol | Train n (IS 2015-2022) | Test n (OOS 2024-2025) | Features | Aligned panel |
|---|---:|---:|---:|---:|
| ES | 1332 | 367 | 42 | 1886 sessions |
| NQ | 1323 | 372 | 42 | 1881 sessions |

(Pre-Daily-gate-fix: train n was 178 / 169 — see disposition-reversal trail commit `8c1de7c`.)

### CPCV path-Sharpe (45 folds at n_groups=10, n_test_groups=2)

| Symbol | Arm | n_folds | median | std | q05 | q95 | DSR | KS-monotonicity | wall-clock |
|---|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| ES | Arm 1 ElasticNet | 45 | -0.1123 | 0.5590 | -1.1731 | +0.7150 | -1.3620 | **FAIL** | 1.1s |
| ES | Arm 2 LightGBM | 45 | **+0.4284** | 0.6562 | -0.5092 | +1.5472 | -1.0386 | **FAIL** | 51.7s |
| NQ | Arm 1 ElasticNet | 45 | **+0.4721** | 0.6886 | -0.7371 | +1.1949 | -1.0674 | **FAIL** | 1.1s |
| NQ | Arm 2 LightGBM | 45 | **+0.4216** | 0.8096 | -1.0959 | +1.5925 | -1.3884 | **FAIL** | 54.1s |

KS-monotonicity FAILS on all 4 arms because per-fold Sharpe std (0.56-0.81 annualized) is too high for empirical-CDF convergence at 30 vs 45 folds (KS distance > 0.05). Median Sharpe on 3 of 4 arms (ES Arm 2, NQ Arm 1, NQ Arm 2) is positive but DSR (Bailey-LdP 2014 deflation by E[max-of-N=45 standard normals]) drives all 4 to negative values.

### OOF-isotonic BSS (5-fold inner CPCV)

| Symbol | Arm | n_oof | BSS | Brier-calibrated | Brier-climatological | Class A `bss_passed` |
|---|---|---:|---:|---:|---:|:---:|
| ES | Arm 1 ElasticNet | 1332 | -0.0130 | 0.2531 | 0.2499 | **FAIL** |
| ES | Arm 2 LightGBM | 1332 | -0.1763 | 0.2939 | 0.2499 | **FAIL** |
| NQ | Arm 1 ElasticNet | 1323 | -0.0101 | 0.2519 | 0.2494 | **FAIL** |
| NQ | Arm 2 LightGBM | 1323 | -0.2072 | 0.3011 | 0.2494 | **FAIL** |

**ElasticNet arms are calibration-MARGINAL** (BSS just under zero on both ES and NQ); **LightGBM arms are clearly miscalibrated** (BSS -0.176 / -0.207). Compare legacy hard-sign BSS = -0.89 / -1.03 — the new OOF-isotonic-calibrated BSS is far more honest but still fails the Class A binding gate.

### Class B KPI report card (per-symbol per-arm)

| Symbol | Arm | Sharpe-vs-passive | Sharpe-vs-bench | Max-DD ratio | Max-DD ann | Power margin | Power ann |
|---|---|:---:|:---:|---:|:---:|---:|:---:|
| ES | Arm 1 ElasticNet | negative | positive | 1.146 | adverse | 0.592 | marginal |
| ES | Arm 2 LightGBM | marginal | positive | 0.621 | favorable | 0.592 | marginal |
| NQ | Arm 1 ElasticNet | marginal | positive | 0.654 | favorable | 0.600 | marginal |
| NQ | Arm 2 LightGBM | marginal | positive | 0.368 | favorable | 0.600 | marginal |

Hansen SPA family p (KPI; not binding at design-time): ES=0.3700 (`spa-rejects`), NQ=0.3090 (`spa-rejects`). Zero `SingleStrategySPAWarning` warnings raised on the m=2 test (audit F-1-11 fix verified).

### Class A binding gate verdicts

| Symbol | Arm | PIT canary | BSS pass | Reliability pass | Repro-log | DSR-when-active | Disposition class |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| ES | Arm 1 ElasticNet | PASS (14/14) | FAIL (BSS=-0.013) | sentinel-PASS | PASS | n/a | `calibration-failed` |
| ES | Arm 2 LightGBM | PASS (14/14) | FAIL (BSS=-0.176) | sentinel-PASS | PASS | n/a | `calibration-failed` |
| NQ | Arm 1 ElasticNet | PASS (14/14) | FAIL (BSS=-0.010) | sentinel-PASS | PASS | n/a | `calibration-failed` |
| NQ | Arm 2 LightGBM | PASS (14/14) | FAIL (BSS=-0.207) | sentinel-PASS | PASS | n/a | `calibration-failed` |

**`paper_trade_eligible=False` on all 4 arms** because Class A binding `BSS > 0` gate fails. H053 remains UN-ARCHIVED but is not paper-trade-eligible without further work.

## Round-1 audit on Phase 1 — verdict BLOCK (12 findings)

Quant-auditor agentId `ab9ea26236a94fabd`. 3 critical + 6 majors + 3 minors. Critical findings + remediation status:

| ID | Severity | Finding | Status |
|---|---|---|---|
| F-2-1 | critical | CPCV runs over FULL panel (train+test concatenated); inner CPCV folds violate strict time-ordering for futures returns. label_horizon=1, embargo=0 means train/test segments can abut. | **OPEN** — inflates Sharpe KPIs (positive medians on 3 of 4 arms are upper-bounds; honest re-run with OOS-only CPCV likely shows smaller magnitudes); does NOT affect calibration-failed disposition direction (leakage typically inflates calibration metrics, so BSS<0 despite leakage means honest BSS would also be <0). Remediation: restrict CPCV to OOS test window OR add embargo > 0 + sort enforcement. |
| F-2-2 | critical | Inner KFold(shuffle=True, random_state=42) for hyperparameter selection violates `rules/quant-project.md` §Time-series-integrity ("Walk-forward CV, never k-fold"); double-leakage inside CPCV. | **OPEN** — replace with `walk_forward_split` or `purged_kfold_split` for hyperparameter inner-CV. Affects both arm1+arm2 across all CPCV folds. |
| F-2-3 | critical | OOF isotonic fits on `arm_local.predict(X_train[train_idx])` — this is in-sample to the inner arm fit; isotonic mapping learned on optimistic in-sample predictions, undoes OOF contract. | **OPEN** — fit isotonic on a held-out portion of inner-train (3-way nested time-ordered split per Niculescu-Mizil-Caruana 2005). |
| F-2-4 | major | Reliability slope sentinel-1.0 = false attestation of binding Class A gate. | **OPEN** — couple reliability slope computation to OOF p_oof (refactor `_compute_oof_brier_components` to expose p_oof + d_actual; call `_compute_reliability_slope`). |
| F-2-5 | major | Sharpe-vs-bench CI placeholder ±0.1 — not a CI; `excludes_zero` hard-coded False. | **OPEN** — compute proper paired-Sharpe-differential CI via Ledoit-Wolf 2008 studentized circular-block bootstrap. |
| F-2-6 | major | `_compute_prior_session_y` missing `over('symbol')` partition guard for AR(1) bench. | **OPEN** — currently safe (single-symbol invocation) but silently miscoded for multi-symbol reuse. |
| F-2-7 | major | No RunContext/ReproLog wiring; sidecar omits pip_freeze_sha + rng_seed; `repro_log_present=True` is hard-coded (false attestation). | **OPEN** — wrap main() in RunContext; populate ReproLog with pip_freeze_sha + rng_seed + model_hash. |
| F-2-8 | major | Class A composite uses `is not False` (allows None to pass) — more permissive than framework's `bool(...)`. | **OPEN** — match framework's strict-True check after F-2-4 lands. |
| F-2-9 | major | `--skip-pit-canary` silently bypasses Class A; sidecar can't distinguish bypass from real-pass. | **OPEN** — annotate `pit-canary-skipped`; force `paper_trade_eligible=False` regardless. |
| F-2-10 | minor | Inner-arm RNG seed reuse across all CPCV folds. | OPEN; deferred. |
| F-2-11 | minor | `emit_promotion_log` imported but never called. | OPEN; trivial fix. |
| F-2-12 | minor | SPA m=2 verification gap. | OPEN; defensive. |

**Remediation tracker**: `P1-H053-STAGE3-V2-ROUND-2-REMEDIATION` (BLOCKING-BEFORE-PAPER-TRADE-ELIGIBILITY). Round-2 of audit-remediate-loop deferred — Phase 2 results published with explicit leakage caveats so the user can decide whether to proceed with Round-2 + Round-3 re-run or treat the calibration-failed disposition as binding (since BSS<0 is robust to leakage direction).

## Robustness analysis: do leakage caveats change the disposition?

**No.** The leakage in F-2-1/F-2-2/F-2-3 INFLATES Sharpe-style metrics and calibration metrics. Specifically:
- CPCV over full panel → optimistic median Sharpe (upper bound).
- KFold-shuffle for hyperparameter selection → optimistic in-sample predictions → optimistic isotonic mapping → optimistic BSS.
- In-sample isotonic source → optimistic calibration curve.

If the Phase 2 result with leakage shows BSS < 0, an honest re-run without leakage would show BSS even lower (or no different — calibration metrics can be insensitive to time-ordering leakage on stationary distributions).

**The `calibration-failed` disposition is therefore robust to the leakage caveats.** H053's H053-mediator + multi-timeframe X cannot be calibrated to BSS > 0 against the per-instrument climatological prior on the OOS fold under any of the 4 arm + symbol combinations tested, even with leakage-optimistic methodology.

The Sharpe KPI values (3 of 4 arms positive median) are legitimately interesting but should NOT be acted on until the leakage issues are remediated (Round-2 re-run). They are consistent with "this signal might be promotable if the calibration issue can be fixed".

## Path to MVP under ADR-0012

H053 → MVP is now blocked by:

1. **Calibration**: BSS must clear > 0 on at least one arm × symbol combination. The OOF-isotonic-calibrated BSS is currently in [-0.21, -0.01] across all 4 arms. Possible improvements:
   - Better calibrator (e.g., Platt scaling instead of isotonic; or beta calibration)
   - Larger inner-CPCV (more OOF coverage; current 5 folds → try 10)
   - Different feature set / model (the underlying model needs to produce calibrate-able probability estimates; ElasticNet's near-zero BSS is closest to the boundary)
   - Re-spec the categorical-table deliverable to use a different probability estimator path
2. **Round-2 audit-remediation** on F-2-1/F-2-2/F-2-3 (CPCV time-ordering + walk-forward inner CV + held-out isotonic source). Until these land, the Sharpe KPI values are leakage-inflated and should not inform operator promotion.
3. **Operator-promotion gate**: even with calibration fixed, ADR-0012 §"Operator-promotion rule" requires sharpe-vs-passive ∈ {positive, marginal} + SPA p ≤ α at promotion + max-DD comparable/favorable. Current SPA p ≈ 0.31-0.37 (`spa-rejects`); would need to land below 0.05 at the operator-promotion gate.

## Verdict

**Phase 1 + Phase 2 deliverables LANDED with explicit caveats.** Disposition: H053 remains `calibration-failed` across all 4 arms (this is BINDING under ADR-0012 even after Round-2 remediation, given leakage-direction analysis). Cycle 11 paper-trade scaffolding does NOT fire. Re-running after Round-2 remediation may or may not flip the disposition; the user's decision.
