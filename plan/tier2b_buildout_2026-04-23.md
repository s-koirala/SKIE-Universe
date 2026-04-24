---
name: Tier-2b buildout 2026-04-23
description: 6-cycle sequential audit-remediate buildout to MVP-1 (first H050 walk-forward result)
type: project
status: in_progress
date: 2026-04-23
---

# Tier-2b buildout — 6-cycle sequential audit-remediate (started 2026-04-23)

Critical-path sequence from the 2026-04-23 reassessment ([docs/research_notes/memo_phase1-reassessment_2026-04-23.md](../docs/research_notes/memo_phase1-reassessment_2026-04-23.md)) to first walk-forward MVP-1 result on H050. Each cycle is a self-contained audit-remediate invocation (3-round cap per [skill](../../.claude/skills/audit-remediate-loop/)).

## Sequencing decision

Sequential over parallel because cycles 3–5 depend on artifacts from cycles 1–2; merging concurrent edits across [src/skie_ninja/inference/](../src/skie_ninja/inference/) + [src/skie_ninja/models/](../src/skie_ninja/models/) would cost more in review than the ~2-day parallel-save.

## Cycles

| # | Deliverable | Artifact paths | Audit agents (parallel where independent) |
|---|---|---|---|
| 1 | Roll-adjusted 1-min derivative + ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py`, tests, audit trail | `quant-auditor` + `reproducibility-verifier` (parallel), `lit-check` on AFML ch.2 roll method |
| 2 | NW-HAC + Sharpe CI (Lo 2002 + Opdyke 2007) + synthetic-null coverage | `src/skie_ninja/inference/stats/{hac,sharpe_ci}.py`, tests | `quant-auditor` + `lit-check` (parallel) |
| 3 | HMM toolkit (Baum-Welch, causal Viterbi, BIC/CV, sidecar) per ADR-0005 | `src/skie_ninja/models/regime/hmm.py`, sidecar serializer, tests | `lit-check` (Rabiner 1989, Baum 1972, Viterbi 1967) + `quant-auditor` (parallel) |
| 4 | Walk-forward engine + purged/embargo CV + leak canaries | `src/skie_ninja/backtest/engine/walk_forward.py`, `src/skie_ninja/backtest/splits.py`, canary tests | `quant-auditor` + `reproducibility-verifier` (parallel) |
| 5 | Hansen SPA + Politis-White stationary bootstrap | `src/skie_ninja/inference/multipletest/hansen_spa.py`, `src/skie_ninja/inference/bootstrap.py` | `lit-check` (Hansen 2005, PW 2004) + `quant-auditor` (parallel) |
| 6 | H050 feature factory + first walk-forward run | `src/skie_ninja/features/{macro,microstructure}/*.py`, `config/hypotheses/H050.yaml`, `artifacts/runs/H050/{run_id}/` | End-to-end audit-remediate on the composed deliverable |

## Completion criteria per cycle

A cycle is `done` iff all of:

1. All new modules green on `pytest -m "not integration" -n auto`.
2. `quant-auditor` returns zero HIGH or CRITICAL findings; MEDIUM findings either remediated or tracked as follow-ups in [plan/implementation-plan_2026-04-15.md](implementation-plan_2026-04-15.md) Open items.
3. `reproducibility-verifier` confirms pinned deps, seeds, checksums, env capture (where applicable).
4. Dated audit trail committed to [docs/audits/](../docs/audits/) with format `audit_trail_{YYYY-MM-DD}_cycle{N}-{slug}.md`.
5. [README.md](../README.md) + [CLAUDE.md](../CLAUDE.md) §Implemented-infrastructure section updated.
6. Conventional-commit on a single logical change; git HEAD captured in the cycle's audit trail.

## Post-MVP-1 trajectory

After Cycle 6 produces H050 result (positive or null):

- H051 execution: reuses cycles 1–5 infrastructure at ~1 week marginal cost (adds Kalman filter + cointegration test).
- H052a execution: reuses cycles 1–5 + the ORB label logic from Cycle 6 at ~1 week marginal cost. Pre-reg auto-archives null if Sharpe differential CI covers zero.
- H052b execution: remains vendor-gated on QQQ 0DTE option chain purchase (no engineering dependency).
- Paper-trade floor: 60 session-days per [CLAUDE.md](../CLAUDE.md) §Execution bar — immovable.

## Update cadence

This memo is updated at the conclusion of each cycle. Completed cycles get a `✓` and an audit-trail link. Partially complete cycles retain `in_progress` with a note on blockers.

## Cycle status

- [x] **Cycle 1 — roll-adjusted 1-min derivative** (2026-04-23) ✓ accepted. 241/241 unit tests green; 29 new tests for this deliverable. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle1-roll-adjusted-1min.md](../docs/audits/audit_trail_2026-04-23_cycle1-roll-adjusted-1min.md). 3-round audit-remediate cleared 2 criticals (oscillation guard, PIT caveat), 2 lit-check criticals (AFML §2.4.1 → §2.4.3 citation + AFML-canonical anchor rule), 7 majors. Six items deferred to Phase-1 follow-ups (`P1-LEVEL-USE-POLICY`, `P1-ROLL-METHOD`, `P1-ROLL-ANCHOR`, `P1-INGEST-ROLLBACK`, `P1-SESSION-EDGE-TESTS`, `P1-INGEST-RUNBOOK`). Key deliverable: [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) v0.2.0.
- [x] **Cycle 2 — NW-HAC + Sharpe CI** (2026-04-23) ✓ accepted. 273/273 unit tests green; 32 new tests. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle2-hac-sharpe-ci.md](../docs/audits/audit_trail_2026-04-23_cycle2-hac-sharpe-ci.md). Round 1 raised 2 lit-check criticals (Lo 2002 Prop 3 misattribution; Opdyke 2007 scalar-ratio approximation vs full-GMM derivation) + 4 majors; Round-2 remediation honestly relabeled methods, added literal Lo 2002 Prop-2 η(q) CI alongside, warned on negative-variance fallback, and fixed ddof consistency. Round-3 verification deferred to Cycle 6 end-to-end (rationale in audit trail). Six Phase-1 follow-ups recorded (`P1-OPDYKE-FULL-GMM` is load-bearing). Key deliverables: [src/skie_ninja/inference/stats/hac.py](../src/skie_ninja/inference/stats/hac.py) + [src/skie_ninja/inference/stats/sharpe_ci.py](../src/skie_ninja/inference/stats/sharpe_ci.py).
- [x] **Cycle 3 — HMM regime-inference toolkit** (2026-04-23) ✓ accepted. 320/320 unit tests green; 47 new tests. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle3-hmm-toolkit.md](../docs/audits/audit_trail_2026-04-23_cycle3-hmm-toolkit.md). Round-1 remediation: 1 lit-check critical (Biernacki 2003 mislabel for 5-restart floor → honest operational-floor label) + 5 majors (EM off-by-one, scale-adaptive `min_var`, conditional PD ridge for tied/full, dead-state / PD-ridge event recording, Rabiner 1989 eq. numbers softened to §-level). Round-2 verification deferred to Cycle 6 per Cycle-2 precedent. Four Phase-1 follow-ups (`P1-HMM-ADAPTIVE-RESTART`, `P1-HMM-WFCV`, `P1-HMM-SIDECAR-DIAGNOSTICS`, `P1-HMM-VERIFIED-EQ-NUMBERS`). Anti-look-ahead prefix-causality invariant unit-gated (`test_filter_prefix_causality`). Key deliverables: [src/skie_ninja/models/regime/](../src/skie_ninja/models/regime/) package.
- [x] **Cycle 4 — walk-forward engine + purged CV + leak canaries** (2026-04-23) ✓ accepted. 399/399 unit tests green; 79 new tests (50 splits, 18 engine, 21 canaries). Audit trail: [docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md](../docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md). Round 1 parallel triad (quant-auditor + literature-check + reproducibility-verifier) raised 4 quant majors (canary c dead-observer, embargo placement, canary a monotonicity, walk-forward embargo over-accumulation), 3 literature majors (Bergmeir overreach, CPCV Ch.12 not §7.5, Cawley §7 unverifiable → Varma & Simon 2006 added), 1 repro major (ledger dtype drift); all remediated Round 1. Round 2 (quant + repro) surfaced 2 new majors — embargo stacked vs overlap interpretation (flipped back to mlfinlab-stacked) and TracingArray public-field bypass (renamed `_array` + `__slots__`); both remediated. Three Phase-1 follow-ups (`P1-BACKTEST-CPCV` full path-reconstruction, `P1-BACKTEST-EMBARGO-MODE-ADR`, `P1-BACKTEST-TRACINGARRAY-STRICT`). Key deliverables: [src/skie_ninja/backtest/](../src/skie_ninja/backtest/) package (splits.py, engine/walk_forward.py, leak_canaries.py).
- [x] **Cycle 5 — Hansen SPA + Politis-White bootstrap** (2026-04-23) ✓ accepted. 453/453 unit tests green; 54 new tests (35 bootstrap/PW-2004, 19 Hansen SPA). Audit trail: [docs/audits/audit_trail_2026-04-23_cycle5-hansen-spa-bootstrap.md](../docs/audits/audit_trail_2026-04-23_cycle5-hansen-spa-bootstrap.md). Round-1 parallel quant-auditor + literature-check cleared 1 critical (L-1-1: Politis-Romano 1995 flat-top kernel mis-cited as *JASA* 90:1105-1118 → corrected to *JTSA* 16(1):67-103), 3 majors (L-1-2: PPW 2009 revised both SB and CB constants, not CB alone; L-1-3: threshold-rule `c·sqrt(log10(n)/n)` mis-attributed to Brockwell-Davis 1991 §7.2 → corrected to Politis & White 2004 §3.1 with Politis 2003 added; L-1-8: tandfonline-paywall verification gap explicitly documented in both module docstrings), and 1 promoted-minor (F-1-1: inconsistent ε-floor scale between HAC and bootstrap omega branches → unified on variance scale `omega² >= _EPS_FLOOR`). Round-2 verification deferred to Cycle 6 end-to-end per Cycle-2/3 precedent. Three Phase-1 follow-ups (`P1-SPA-PDF-VERIFY`, `P1-SPA-ARCH-BENCHMARK`, `P1-SPA-HAC-DEFAULT-ADR`). Key deliverables: [src/skie_ninja/inference/bootstrap.py](../src/skie_ninja/inference/bootstrap.py) + [src/skie_ninja/inference/multipletest/hansen_spa.py](../src/skie_ninja/inference/multipletest/hansen_spa.py).
- [~] **Cycle 6 — H050 feature factory + first walk-forward run** (2026-04-24) **Phase-A only ✓; live WF pending — 10 blockers**. Phase-A scaffolding (feature factory, labeler, microstructure, NT8 cost model, orchestrator, ADR-0007/0008, H050.yaml, data_requirements.md) committed. 54/54 Cycle-6 unit tests green (32 feature + 22 cost model); pause memo cites 517 full-suite total (not corroborated in audit trail — see follow-up `P1-AUDIT-TRAIL-FULL-SUITE-COUNT`). In-tree Cycle-6 audit trail: [docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md](../docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md). Pause memo: [docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](../docs/research_notes/memo_cycle6-pause-status_2026-04-24.md). 3-round in-tree triad (quant-auditor + literature-check + reproducibility-verifier) cleared the items recorded in that audit trail. A subsequent **Round-1 audit-remediate-loop on 2026-04-24** (parallel triad over the committed Phase-A; not separately committed) reconciled the 5 pause-memo blockers, confirmed all 5, and surfaced 3 additional pre-reg deviations + 2 reproducibility gaps. **10 items blocking evidence-bar execution**:
  - `P1-HMM-FOLD-WARM-START` *(major)* — HMM filter restarts log_pi each fold (warm-up bias O(dwell_time)). [scripts/run_walk_forward.py:334](../scripts/run_walk_forward.py); [src/skie_ninja/models/regime/_core.py:296-297](../src/skie_ninja/models/regime/_core.py).
  - `P1-H050-SPLIT-PARAMS` *(**critical**, pre-reg violation)* — `n//3`/`n//10` literals at [scripts/run_walk_forward.py:543-554](../scripts/run_walk_forward.py); pre-reg dates in [config/hypotheses/H050.yaml](../config/hypotheses/H050.yaml) (train 2015-01-01→2022-12-31 / val 2023 / test 2024-2025).
  - `P1-H050-INNER-CV` *(major)* — in-sample HP selection at [scripts/run_walk_forward.py:259-287](../scripts/run_walk_forward.py); pre-reg [research/01_hypothesis_register/H050/design.md](../research/01_hypothesis_register/H050/design.md) §5 mandates nested walk-forward (Varma & Simon 2006, doi:[10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91)); search budget collapsed 200 → 10.
  - `P1-H050-CI-DIFFERENTIAL` *(**critical**, pre-reg violation)* — Opdyke CI on `sharpe_gated` alone at [scripts/run_walk_forward.py:358](../scripts/run_walk_forward.py); pre-reg design.md §1 binds `T_H050 = SR_gated − SR_unconditional`; [rules/quant-project.md](../../.claude/rules/quant-project.md) mandates Ledoit-Wolf 2008 (doi:[10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002)) for pairwise.
  - `P1-H050-DATA-COVERAGE` *(**critical**, pre-reg violation; user decision pending)* — substrate ES 2020-2025 + NQ 2020-2024 vs pre-reg design.md §2 demand 2015-01-01 → 2025-12-31; ~60% of pre-reg train window missing. Three paths anchored in design.md §2 line 41 ("re-runs on extended windows require a successor hypothesis ID") + §10 (archive `precondition-failed`): **B1** backfill from Databento GLBX.MDP3, **B2** register H050b with truncated windows, **B3** archive H050 as `precondition-failed`.
  - `P1-H050-LABEL-CV` *(promoted to blocking)* — pt_sl × vertical_barrier × volatility_lookback CV grid collapsed to center at [scripts/run_walk_forward.py:488-497](../scripts/run_walk_forward.py); pre-reg design.md §4 mandates joint CV.
  - `P1-H050-UNIVERSE-ES-ONLY` *(minor pre-reg deviation)* — smoke loops ES only at [scripts/run_walk_forward.py:511-512](../scripts/run_walk_forward.py); H050.yaml line 3 universe `[ES, NQ]`.
  - `P1-H050-SPA-M1-DEGENERATE` *(minor)* — Hansen SPA |M|=1 single-column at [scripts/run_walk_forward.py:362-372](../scripts/run_walk_forward.py); rules/quant-project.md intends multi-strategy SPA; document via ADR-0008 extension.
  - `P1-CYCLE6-REPRO-DATASET-CHECKSUM` *(repro)* — 5 Cycle-6 walk_forward repro logs carry `dataset_checksums={}`; `06f0402` fix wired `output_frame_sha256` into `RunContext` but no run has been executed post-fix.
  - `P1-HMM-BLAS-THREADING-ADR` *(repro)* — `sklearn.KMeans` deadlocks under default Windows MKL/OpenMP; `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` documented only in pause memo, not in repo README or any ADR. Pause memo §Issue 3 originally classified this "non-blocking, workaround known"; promoted to blocking here per [~/.claude/CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md) reproducibility schema (single-command reproduction without out-of-tree env-var setup).

  Other (non-blocking) follow-ups carried forward: `P1-H050-FEATURE-PIT-ASSERT`, `P1-H050-COST-EMPIRICAL-CALIBRATION`. Cycle-6 row will flip to `[x] ✓ accepted` when (a) the user resolves Option B (data-coverage decision: B1 / B2 / B3) and (b) the 10 items are remediated and verified in a Phase-B audit-remediate-loop with a real-data run that populates `dataset_checksums` end-to-end.

  Key deliverables (Phase-A committed): [src/skie_ninja/features/](../src/skie_ninja/features/) (labels + 4 microstructure modules), [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py), [scripts/run_walk_forward.py](../scripts/run_walk_forward.py), [research/01_hypothesis_register/H050/data_requirements.md](../research/01_hypothesis_register/H050/data_requirements.md), [config/hypotheses/H050.yaml](../config/hypotheses/H050.yaml), [docs/decisions/ADR-0007](../docs/decisions/ADR-0007-embargo-placement.md) + [ADR-0008](../docs/decisions/ADR-0008-spa-omega-method.md).
