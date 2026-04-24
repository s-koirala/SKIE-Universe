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
- [ ] Cycle 5 — Hansen SPA + Politis-White bootstrap
- [ ] Cycle 6 — H050 feature factory + first walk-forward run
