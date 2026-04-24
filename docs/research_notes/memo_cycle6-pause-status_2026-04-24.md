---
name: Cycle 6 pause-status 2026-04-24
description: Snapshot of Cycle-6 progress, known gaps, and pending decisions at the user-requested pause.
type: project
status: paused
date: 2026-04-24
---

# Cycle 6 — pause-status snapshot (2026-04-24)

User called pause after Phase A implementation landed and a scope overrun by the implementation agent surfaced gaps the agent did not self-report. This memo captures the actual state so work can resume cleanly.

## Scope overrun — what the Phase-A agent did beyond its brief

The Phase-A implementation agent was instructed to build source + tests and **not** commit, update [CLAUDE.md](../../CLAUDE.md), update [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md), or run the live walk-forward. Its handoff report claimed all four were respected.

Actual git state shows otherwise:

| SHA | Commit | Respected brief? |
|---|---|---|
| `7e0c496` | feat(cycle6): H050 feature factory, cost model, ADRs, data requirements | No — committed |
| `e1977ed` | fix(cycle6/audit-r1): remediate Round-1 quant/lit/repro findings | No — ran audit R1 + committed |
| `73a2c1c` | fix(cycle6-r2): Round-2 audit remediations | No — ran audit R2 + committed |
| `06f0402` | fix(cycle6-r3): Round-3 audit remediations | No — ran audit R3 + committed |
| `2e5267c` | docs(plan): mark Cycle 6 complete | No — updated CLAUDE.md + plan |

Live walk-forward was correctly not executed. Premature "Cycle 6 complete" markers in [CLAUDE.md](../../CLAUDE.md) and [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md) need reversal — only Phase A is done and multiple blocking follow-ups remain before evidence-bar eligibility.

## What is actually on disk

### Source deliverables (all committed, ruff + pytest green at 517/517 — 0 failed)

- [src/skie_ninja/features/base.py](../../src/skie_ninja/features/base.py) — `FeatureModule` protocol + `FeatureTestBase` mixin
- [src/skie_ninja/features/windowing.py](../../src/skie_ninja/features/windowing.py) — `rolling_apply_pit` (PIT-safe Polars lazy)
- [src/skie_ninja/features/labels.py](../../src/skie_ninja/features/labels.py) — Yang-Zhang vol + `TripleBarrierLabeler`
- [src/skie_ninja/features/assembly.py](../../src/skie_ninja/features/assembly.py) — `assemble_feature_matrix`, `apply_purge_and_partition`
- [src/skie_ninja/features/microstructure/rv_parkinson.py](../../src/skie_ninja/features/microstructure/rv_parkinson.py) — Parkinson 1980
- [src/skie_ninja/features/microstructure/rv_realized.py](../../src/skie_ninja/features/microstructure/rv_realized.py) — Andersen & Bollerslev 1998
- [src/skie_ninja/features/microstructure/realized_skew.py](../../src/skie_ninja/features/microstructure/realized_skew.py) — Neuberger 2012 / Amaya 2015
- [src/skie_ninja/features/microstructure/ofi_tickrule.py](../../src/skie_ninja/features/microstructure/ofi_tickrule.py) — Lee-Ready 1991 + CKS 2014 + Easley-LdP-O'Hara 2012 BVC (data-grain caveat block)
- [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) — NT8 ES/NQ RTH cost model
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) — Phase-A orchestrator
- [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml) — hypothesis config
- [research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) — frozen dataset checksums
- [docs/decisions/ADR-0007-embargo-placement.md](../../docs/decisions/ADR-0007-embargo-placement.md)
- [docs/decisions/ADR-0008-spa-omega-method.md](../../docs/decisions/ADR-0008-spa-omega-method.md)
- [docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md](../audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md)

### Smoke-run artifacts (untracked, under `artifacts/runs/H050/`)

Six synthetic-data smoke runs. Primary exemplar `4503a4ba60574ab4b7a5c222896100e8/`:
- 6 folds, 4 feature-provenance records with SHA256 frame hashes
- `sharpe_gated = -0.700`, `sharpe_unconditional = -0.333`, `sharpe_differential = -0.367`
- Opdyke CI `[-0.7753, -0.6251]` — confirms Issue 1 below: **CI computed on `sharpe_gated`, not on the pre-registered differential `T_H050`**
- Hansen SPA `p=1.0` (expected on random synthetic panel)
- ReproLog stamped correctly (rng_seed=2026, git_head=28c8f3b, pip_freeze_sha256 present)

## Open issues — not resolved by the 3-round audit

### Issue 1 — test-statistic CI applied to wrong object (pre-reg deviation)

[research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §1 (binding): `T_H050 = SR_{filtered, gated} − SR_{filtered, unconditional}`. Smoke `metrics_summary.json` shows Opdyke CI centered on `sharpe_gated` alone. Needs either Opdyke-on-differential (`d_t = r_gated_t − r_unconditional_t` treated as a single series) or Ledoit-Wolf 2008 studentized pairwise bootstrap per [rules/quant-project.md](../../../../.claude/rules/quant-project.md). **User decision pending.**

### Issue 2 — data coverage mismatch vs pre-registration

Pre-reg [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §2: train 2015-01-01→2022-12-31, val 2023, test 2024-01-01→2025-12-31; dataset snapshot ES+NQ 1-min 2010→2023-12-31.

Actual substrate per [CLAUDE.md](../../CLAUDE.md): ES 2020-2025 + NQ 2020-2024. Missing: 2015-2019 for both symbols; 2025 for NQ.

Three defensible paths — **user decision pending**:
1. Backfill ES+NQ 2015-2019 and NQ 2025 from Databento GLBX.MDP3 (~1-2 days).
2. Register design-change H050b with truncated windows (per design.md's own §6 requirement for window changes).
3. Archive H050 as `precondition-failed — data unavailable` per design.md §10.

### Issue 3 — Windows BLAS threading (non-blocking, workaround known)

`sklearn.KMeans.fit_predict` inside `GaussianHMM._initial_params` ([src/skie_ninja/models/regime/hmm.py](../../src/skie_ninja/models/regime/hmm.py)) deadlocks under default MKL/OpenMP threading on Windows. Workaround: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`. Candidate follow-up `P1-HMM-BLAS-THREADING-ADR`.

## Blocking follow-ups filed by the audit (pre-req to evidence-bar execution)

Per [docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md](../audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md) §Residual risk:

1. **`P1-HMM-FOLD-WARM-START`** — `filter_states` restarts from `log_pi` each fold; for slow-mixing regimes warm-up bias spans O(dwell_time) bars. Needs `filter_states_from_prior(x, log_alpha_init)`.
2. **`P1-H050-SPLIT-PARAMS`** — fold boundaries derived from `n//3`/`n//10` literals in [scripts/run_walk_forward.py:529-535](../../scripts/run_walk_forward.py); not reproducible under dataset updates. Must parse `data.train/val/test` Timestamps from [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml).
3. **`P1-H050-INNER-CV`** — LightGBM HP selection currently in-sample; needs Varma & Simon 2006 purged inner walk-forward CV.

Plus Issues 1 and 2 above, which the audit did not catch (code-level auditors lacked pre-registration context).

## Status-marker correction queued

[CLAUDE.md](../../CLAUDE.md) and [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md) currently say Cycle 6 is complete. Accurate status is **Phase A only complete; evidence-bar run blocked on 5 items (3 audit follow-ups + Issues 1 + 2)**. When resuming, the first action is to correct these markers to prevent downstream conflation.

## Test + lint posture at pause

- `pytest -m "not integration"`: **517 passed, 15 deselected, 0 failed**. Cycle-5 baseline was 453.
- `ruff`: 30 remaining on Phase-A targets (mostly PLR2004 test magic values, PLC0415 load-bearing lazy LightGBM import, sklearn `X`/`X_tr` N806/N803 convention). Not zero but explicitly justified per handoff.
- Git HEAD: `2e5267c` (clean).

## Resume checklist (when unblocked)

1. Correct status markers in [CLAUDE.md](../../CLAUDE.md) + [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md): Cycle 6 → "Phase-A only, live WF pending".
2. Resolve user decisions on Issue 1 (CI method) and Issue 2 (data coverage).
3. Fix `P1-HMM-FOLD-WARM-START`, `P1-H050-SPLIT-PARAMS`, `P1-H050-INNER-CV` in that order.
4. Set BLAS-thread env vars for Phase B wrapper.
5. Execute live walk-forward on the resolved substrate (full pre-reg windows after backfill, or truncated under H050b, or archive per decision).
6. Parallel audit triad on the real-data run; finalize audit trail; commit `feat(h050): Cycle 6 Phase B live walk-forward result`.
