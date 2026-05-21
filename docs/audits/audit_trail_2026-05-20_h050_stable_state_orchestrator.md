---
audit_id: 2026-05-20_h050_stable_state_orchestrator
scope: H050.stable-state walk-forward orchestrator + 3 test suites + KPI v1 placeholder (Phase O.20)
hypothesis_id: H050_stable_state
parent_hypothesis_id: H050
rounds_executed: 1
verdict_at_close: accept-with-residuals
audit_remediate_loop_skill: ~/.claude/skills/audit-remediate-loop
audit_remediate_loop_3_round_cap_status: round-1-complete; rounds-2-and-3-deferred-to-smoke-run-cycle
---

# Audit-remediate-loop trail — H050.stable-state walk-forward orchestrator (Phase O.20)

> R1 single-round audit-remediate-loop on the orchestrator-extension code + 3 test
> suites + KPI v1 placeholder + audit-trail + INDEX/RESULTS_INDEX + stage tracker
> update for the H050.stable-state genetic-successor variant per
> [H050_stable_state/design.md §11.2][1] BLOCKING-BEFORE-PRODUCTION-RUN.
>
> Per Phase O.20 scope-bound directive: the smoke walk-forward execution is
> deferred to a separate operator-authorized cycle; this audit covers the
> orchestrator + test plumbing layer only. R2 + R3 verification rounds will run
> when the smoke walk-forward emits a sidecar.

## R1 — Inline audit + remediation (2026-05-21)

Per the audit-remediate-loop skill convention, R1 was executed inline with four
specialist branches (quant + code-reviewer + format-auditor + reproducibility-
verifier) on the orchestrator extension + tests + KPI placeholder. Findings are
enumerated below; all critical and load-bearing major findings are remediated
inline before commit.

### Branch 1: quant-auditor — stability-filter mechanic correctness

**Verdict**: `accept`

| # | Finding | Severity | Disposition |
|---|---|---|---|
| Q-1 | Stability filter at gate-engagement layer (NOT at state-selection layer): the H050.stable-state mechanism operates on the per-bar `posterior > 0.5` indicator sequence at `_predict_fold` line ~1793 (post-warm-start forward filter). H050 v1 §5 line 63 canonical highest-mean ordering is PRESERVED verbatim per the parent INVESTIGATE memo §7.3 + ADR-0027 §D-4 "preserved infrastructure"; the stability filter only ADDS a temporal-persistence layer at the engagement decision. | accept | Verified at `scripts/run_walk_forward.py:_predict_fold` — `regime_high_mean` (state choice) is unchanged; `raw_indicator = (filtered[:, high_state] > 0.5)` (per-bar choice) is unchanged; only the NEW post-step `regime_indicator = (rolling_N_sum >= N)` is added. |
| Q-2 | Counter-reset-at-fold-boundary convention (per design.md §5 operator-conservative): the filter consumes only the test-fold posterior sequence (`filtered = hmm.filter_states_from_prior(test_obs, ...)`); train-fold-tail modal-state sequence is NOT carried forward into the test-fold first-N-1 bars. | accept | Verified at the production-code site: `filtered` is computed from `test_obs` only; the stability-filter cumsum starts at 0 at the first test-fold bar; the first N-1 bars of `regime_indicator` are 0 by construction (insufficient streak length). This is the canonical fold-boundary reset; the train-fold-tail carry-forward variant (which the design.md §5 explicitly rejects) is NOT implemented. |
| Q-3 | PIT-causality preserved: gate at bar `t` depends only on `raw_indicator[t-N+1:t+1]`, each of which is a pure function of `y_{1:t}` via `filter_states_from_prior`. | accept | The stability filter is a deterministic causal state machine over the test-fold posterior sequence. Verified by `TestPITCausalityBoundaryConditions` unit tests (gate depends only on last N bars; gate does not look ahead). |
| Q-4 | N=1 is a strict no-op (no-op == raw indicator == H050 v1 production code path): operator can launch the wrapper with `--stable-state-n 1` to reproduce H050 v1 byte-equal sidecars. | accept | Verified at the production-code site: `if _STABLE_STATE_N <= 1: regime_indicator = raw_indicator` is a bit-identical alias. `TestStateBitEqualityUnderFoldPartition::test_n1_is_bit_identical_to_v1_raw_indicator` is the regression test. |
| Q-5 | Monotonicity invariant (load-bearing for the H-c whipsaw discriminant per design.md §1 + §8): higher N produces non-increasing gate-firing counts. | accept | Verified by `TestStabilityFilterLogic::test_higher_n_reduces_gate_firings` on a high-flip synthetic sequence + the integration canary `TestCanaryEFullCompositionSmoke::test_full_composition_pre_registered_n_grid` on a fitted 2-state HMM. Monotonicity is the operator-readable empirical handle on the H-c hypothesis: if higher N reduces forced flips AND improves realized OOS, that is evidence for H-c whipsaw dominance. |

### Branch 2: code-reviewer — minimal-diff orchestrator pattern

**Verdict**: `accept-with-residual`

| # | Finding | Severity | Disposition |
|---|---|---|---|
| CR-1 | Minimal-diff pattern adherence: `scripts/run_walk_forward.py` gets 3 surgical patches (module-flag declaration + parser arg + run-time wire-up) + 1 in-place modification at `_predict_fold` (the gate-engagement-site filter). Pattern mirrors the sibling H050.invert (commit `7fc9021`) exactly. | accept | Patch is ~50 lines net in 4 contiguous regions of the 3300-line orchestrator. Stability-filter algorithm is locally implemented via numpy cumsum (vectorised, deterministic). No new imports; no architectural restructure. |
| CR-2 | Wrapper script signature parity with `scripts/run_h050_invert_walk_forward.py`: same module-load idiom; same `_resolve_*_argv` helper pattern; same `run()` entry point; same `__main__` guard. | accept | One semantic divergence from H050.invert: the wrapper REQUIRES `--stable-state-n N` explicit (raises `ValueError` if missing) because each N in the pre-registered grid `{3, 5, 10, 20}` is its own cell per design.md §5. This is the correct semantic — there is no defensible default N. |
| CR-3 | Type-hint hygiene: all new function signatures use proper union types (`list[str] \| None`, etc.); no `Any` placeholders. | accept | The wrapper uses `from __future__ import annotations` + `list[str] \| None` style; consistent with the H050.invert sibling. |
| CR-4 | Defensive validation in `run()`: `--stable-state-n` value < 1 raises `ValueError` early ("N=1 is the H050 v1 no-op default; N >= 2 enables the stability filter"). | accept | Prevents nonsensical N=0 or N=-1 inputs from silently producing degenerate behavior. |
| CR-5 | Comments + docstrings: the new module-level `_STABLE_STATE_N` flag has a detailed docstring matching the H050.invert sibling's pattern. The stability-filter algorithm at `_predict_fold` carries an inline `# justify:` explanation tying the cumsum-based rolling sum to the equivalent naive per-bar loop. | accept | Documentation parity with H050.invert achieved. |
| CR-6 | Test coverage: 19 unit tests (orchestrator parser + wrapper argv + filter logic + module-flag isolation) + 15 fold-continuity tests (counter reset + PIT-causality + N=1 byte-equality, parametrized over `{3, 5, 10, 20}`) + 6 integration canaries (A-E covering filter PIT, fold reset, no-train-test-leak, NaN-poison, full composition). | accept | Total 40 tests across the H050.stable-state surface; 19/19 H050.invert regression tests preserved → 59/59 H050-family tests green. |

### Branch 3: format-auditor — KPI template compliance + cross-link validity

**Verdict**: `accept-with-residuals` (smoke-mode placeholder caveats annotated inline)

| # | Finding | Severity | Disposition |
|---|---|---|---|
| F-1 | KPI v1 placeholder structure matches the H050.invert v1 sibling placeholder (smoke-mode caveat + per-N row scaffolding + monotonicity-discriminant section). | accept | Mirrors the H050.invert v1 emission convention exactly. |
| F-2 | 13-table format compliance per ADR-0014 §3.2 + ADR-0017 §3.2 + ADR-0019 §3 (Tables 1, 1c, 2, 3, 3a, 3b, 3c, 4, 5, 6, 7, 8, 9): all 13 tables present in v1 placeholder with per-N row scaffolding across the pre-registered N grid `{3, 5, 10, 20}`. | accept | Per-N rows are the canonical reporting axis for H050.stable-state per design.md §8 (monotonicity diagnostic exhibit). |
| F-3 | ADR-0026 §D-1 3-component summary header: §0 present at top of v1 placeholder; Component 2 marked `NOT-IN-SCOPE-at-v1` per the H050.stable-state §2 substrate window ending 2025-12-31 (no 2026-onward sub-window in OOS by construction). | accept | Same disposition as the sibling H050.invert v1 placeholder. |
| F-4 | Cross-link integrity: 18 cross-references in v1 placeholder + 5 in audit trail + 4 in stage.md update; all resolve. | accept | Verified by inspection. |
| F-5 | Annotation grammar per ADR-0025 §D-5 + ADR-0028 §D-4 + ADR-0026 §D-3: v1 placeholder declares `stability-filter-N-{3,5,10,20}` (per design.md §5 pre-registered grid; the new H050.stable-state-specific annotation) + standard `gate-ordering-highest-mean` (preserved verbatim; the H050 v1 canonical) + `causal-mechanism-correlation-only` + `cost-conservative-prior`. The annotation `monotonicity-verdict-TBD` is declared as the load-bearing discriminator for the empirical H-c hypothesis. | accept | Annotation grammar mirrors the sibling H050.invert pattern + adds the H050.stable-state-specific `stability-filter-N` + `transition-rate` + `monotonicity-verdict` triple per design.md §7 + §8. |

### Branch 4: reproducibility-verifier — ReproLog schema + substrate binding

**Verdict**: `accept-with-residual` (smoke-run cycle will close the residuals)

| # | Finding | Severity | Disposition |
|---|---|---|---|
| R-1 | ReproLog 13-field schema (placeholder verification): v1 placeholder declares `git_head: b9df7e84ea9b973577413f2dd0939c133ad6b9a3` + `substrate_dataset_checksum: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (the canonical post-Phase-O.10 substrate per H050 v1 + H050.invert + H050.stable-state design.md §2 binding) + `sidecar_scientific_payload_sha256: TBD-pending-smoke-completion`. | accept | Verification deferred to smoke-run cycle: on smoke-run completion the orchestrator's `RunContext` per ADR-0013 §3.1 will populate the 13 ReproLog fields automatically; the `TBD-pending-smoke-completion` annotation flags this for follow-up. |
| R-2 | Substrate dataset_checksum binding: the v1 placeholder declares `317429e4...` per the canonical post-Phase-O.10 substrate. This SHA is shared with H050 v1 + H050.invert + H055/H062/H065 v2 KPI cards per the Phase O.10 + Phase O.18 ledger. | accept | Verified against the existing canonical-substrate binding pattern. |
| R-3 | Sidecar SHA wiring (deferred): the orchestrator's existing `RunContext` + `ReproLog` infrastructure (per H050 v1 production-run pattern) writes `scientific_payload_sha256` to the sidecar on `run()` exit. No new sidecar-writing code is needed; the H050.stable-state orchestrator inherits the H050 v1 sidecar contract verbatim. | accept | Verified by inspection of `scripts/run_walk_forward.py:run()` — `RunContext` writes sidecar JSON + computes SHA on every walk-forward run, regardless of CLI flag values. |
| R-4 | BLAS pinning per ADR-0009: the H050.stable-state wrapper invokes the canonical orchestrator's `run()` which already includes the BLAS thread-pinning preamble + `threadpoolctl.threadpool_limits(1)` from H050 v1 production runs. | accept | The wrapper's `__main__` docstring documents the canonical launch envelope; no new BLAS-pinning code in the wrapper. |
| R-5 | Test reproducibility: all 40 H050.stable-state tests use deterministic synthetic substrates with fixed seeds (`rng = np.random.default_rng(20260520)` per design.md §11 RNG seed). | accept | Bit-deterministic across runs; verified by re-running each test file. |

## Round-1 verdict

`accept-with-residuals` — all critical and load-bearing major findings remediated
inline before commit. Residuals are operationally `TBD-pending-smoke-completion`
fields in the v1 placeholder (numerical KPI values + sidecar SHA256 + populated
ReproLog 13 fields) and are closed by the next operator-authorized smoke-run cycle.

## Test results

| Suite | Tests | Pass | Fail | File |
|---|---:|---:|---:|---|
| H050.stable-state orchestrator unit | 19 | 19 | 0 | `tests/unit/test_h050_stable_state_orchestrator.py` |
| H050.stable-state fold-continuity BLOCKING unit | 15 | 15 | 0 | `tests/unit/test_h050_stable_state_fold_continuity.py` |
| H050.stable-state PIT canary integration | 6 | 6 | 0 | `tests/integration/test_h050_stable_state_pit_canaries.py` |
| H050.invert orchestrator unit (regression) | 13 | 13 | 0 | `tests/unit/test_h050_invert_orchestrator.py` |
| H050.invert PIT canary integration (regression) | 6 | 6 | 0 | `tests/integration/test_h050_invert_pit_canaries.py` |
| **Total** | **59** | **59** | **0** | (all H050-family genetic-successor tests) |

Test execution was sequential (one pytest invocation per file) per the Phase O.20
scope-bound load-management directive. Total wall-clock ~25 s across all 5 files.

## Closed follow-ups per Phase O.20

| Follow-up | Status | Closure evidence |
|---|---|---|
| `P1-H050-STABLE-STATE-WALK-FORWARD-ORCHESTRATOR-IMPL` | ✓ closed | `scripts/run_h050_stable_state_walk_forward.py` thin wrapper + module-level `_STABLE_STATE_N` + `--stable-state-n N` CLI + N-bar stability filter at the single gate-engagement site in `_predict_fold` (default N=1 preserves H050 v1 bit-identical behavior). |
| `P1-H050-STABLE-STATE-LEAKAGE-CANARY-INTEGRATION-TEST` | ✓ closed | `tests/integration/test_h050_stable_state_pit_canaries.py` with 6 tests across 5 canary classes (A filter PIT-causal / B fold-boundary reset / C no-train-test-leak / D NaN-poison + module-flag isolation / E full-composition smoke). All 6 PASS on synthetic 2-regime substrate. |
| `P1-H050-STABLE-STATE-FOLD-CONTINUITY-TEST` | ✓ closed | `tests/unit/test_h050_stable_state_fold_continuity.py` with 15 parametrized tests across the pre-registered N grid (counter reset at fold boundary; PIT-causality boundary conditions; N=1 byte-equality with H050 v1 raw indicator). |
| `P1-H050-STABLE-STATE-PARITY-INVARIANT-TEST` (orchestrator unit tests) | ✓ closed | `tests/unit/test_h050_stable_state_orchestrator.py` with 19 tests across 5 classes (module-flag default; CLI argv invariants; stability-filter logic; production-vs-helper parity; module-flag isolation). |

## Deferred to smoke-run cycle (R2 + R3 verification)

R2 verification will run on smoke-walk-forward completion (separate operator-
authorized cycle per Phase O.20 scope-bound directive). Scope:

- Verify `RunContext` writes 13/13 ReproLog fields to the sidecar.
- Verify sidecar SHA256 is computed + persisted.
- Verify the smoke run produces non-degenerate per-N artifacts across the
  pre-registered N grid `{3, 5, 10, 20}`.
- Populate v1 placeholder's TBD numerical fields in place per ADR-0013 §4.1
  non-loss (existing TBD fields filled; structural body preserved verbatim).
- Append a `kpi-report-v1-populated` row to `stage.md`.
- Empirically validate the monotonicity invariant on real-substrate fixtures
  (Tables 1-9 + transition-rate per-N attribution + cost-drag attribution per
  design.md §7 — load-bearing for the H-c whipsaw discriminant).

R3 will run on first v(N+1) KPI emission if numerical refinement is operator-
discretionary motivated (e.g., if the smoke run surfaces unexpected behavior
warranting a full production-walk-forward cycle).

## Cross-references

- Parent H050 KPI v1: [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md)
- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../../research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
- Sibling H050.invert audit trail: [docs/audits/audit_trail_2026-05-20_h050_invert_orchestrator_smoke.md](audit_trail_2026-05-20_h050_invert_orchestrator_smoke.md)
- H050.stable-state design: [research/01_hypothesis_register/H050_stable_state/design.md](../../research/01_hypothesis_register/H050_stable_state/design.md)
- H050.stable-state KPI v1 (smoke placeholder): [research/01_hypothesis_register/H050_stable_state/H050_stable_state_kpi_report_v1.md](../../research/01_hypothesis_register/H050_stable_state/H050_stable_state_kpi_report_v1.md)
- H050.stable-state stage tracker: [research/01_hypothesis_register/H050_stable_state/stage.md](../../research/01_hypothesis_register/H050_stable_state/stage.md)
- Orchestrator wrapper: [scripts/run_h050_stable_state_walk_forward.py](../../scripts/run_h050_stable_state_walk_forward.py)
- Canonical orchestrator extension: [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) (module-level `_STABLE_STATE_N` declaration + `--stable-state-n` CLI flag + stability filter in `_predict_fold`)
- Unit tests:
  - [tests/unit/test_h050_stable_state_orchestrator.py](../../tests/unit/test_h050_stable_state_orchestrator.py)
  - [tests/unit/test_h050_stable_state_fold_continuity.py](../../tests/unit/test_h050_stable_state_fold_continuity.py)
- Integration tests: [tests/integration/test_h050_stable_state_pit_canaries.py](../../tests/integration/test_h050_stable_state_pit_canaries.py)
- ADR cascade: [ADR-0013 §3.1 + §4.1](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), [ADR-0014 §3.2](../decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), [ADR-0017 §3 + §3.2](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md), [ADR-0018 §D-1](../decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md), [ADR-0019 §3](../decisions/ADR-0019-barbell-payoff-shape-screening.md), [ADR-0022](../decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md), [ADR-0024 §D-1 + §D-2](../decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md), [ADR-0025 §D-1..§D-7](../decisions/ADR-0025-abandonment-trigger-infrastructure.md), [ADR-0026 §D-1..§D-3](../decisions/ADR-0026-paradigm-and-reporting-refinements.md), [ADR-0027 §D-3 + §D-4](../decisions/ADR-0027-operational-discipline-bounded-exploration.md).

[1]: ../../research/01_hypothesis_register/H050_stable_state/design.md
