---
hypothesis_id: H050_stable_state
parent_hypothesis_id: H050
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-21
git_head: b9df7e84ea9b973577413f2dd0939c133ad6b9a3
substrate_dataset_checksum: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_scientific_payload_sha256: TBD-pending-smoke-completion
run_id: TBD-pending-smoke-completion
sizing_convention: hmm_gated_multibar_intraday
supersedes: null
superseded_by: null
emission_mode: smoke-mode placeholder
emission_caveat: |
  v1 emission is a SMOKE-MODE PLACEHOLDER. The orchestrator + tests + audit trail
  were landed in Phase O.20; the smoke walk-forward execution is deferred to a
  separate operator-authorized cycle. No production walk-forward has been run for
  any N in the pre-registered grid {3, 5, 10, 20} as of this v1 emission. Numeric
  fields (Tables 1-9 + §0 3-component header) are marked TBD-pending-smoke-run
  per the parent H050.invert KPI v1 precedent + the H062 + H055 + H065 v0 → v1
  smoke-placeholder pattern.

  This v1 placeholder lands at the orchestrator-readiness commit per the H050.invert
  Phase O.20 sibling precedent. The v1 will be POPULATED IN PLACE on smoke-run
  completion via append-only update per ADR-0013 §4.1 non-loss (existing TBD fields
  filled; existing content preserved verbatim; new version-row appended to stage.md
  at smoke-run sidecar emission).
---

# H050.stable-state — KPI Report Card v1 (smoke-mode placeholder)

> **SMOKE-MODE PLACEHOLDER** for hypothesis H050.stable-state per [design.md §5](design.md);
> tests the H-c whipsaw sub-hypothesis from the parent
> [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
> §7.3 Variant B by adding an N-bar state-stability-confirmation filter at the gate-
> engagement layer. v1 lands as a placeholder upon orchestrator + tests + audit trail
> completion per [ADR-0027 §D-3 empirical-before-amendment](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)
> sequencing rule; smoke-walk-forward execution is deferred to a separate operator-
> authorized cycle per Phase O.20 scope-bound directive.

- **Hypothesis**: H_1: For some N in the registered grid `{3, 5, 10, 20}`,
  SR_filtered_gated_stable_N − SR_filtered_unconditional > 0 on the OOS test fold
  per [design.md §1](design.md); N-bar stability filter tests the H-c whipsaw
  sub-hypothesis.
- **Design.md**: [design.md](design.md) (frozen at `status: designed`)
- **Stage**: `kpi-report-emitted` per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).
  Next mandatory transition: `kpi-report-emitted` → `ninjascript-implemented` per
  ADR-0013 §5 (bridge-mediated per §1.2 since HMM filter requires Python inference).
  Operator-discretionary per the 2026-05-04 standing decline-ninjascript directive.
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)
- **Sibling**: [H050.invert v1](../H050_invert/H050_invert_kpi_report_v1.md) (paired-design
  mechanism-discrimination Variant A; smoke-mode placeholder per the same Phase O.20
  scope-bound convention)

## §0. 3-component KPI summary header (per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md))

| Component | ES (per-N: 3 / 5 / 10 / 20) | NQ (per-N: 3 / 5 / 10 / 20) |
|---|---|---|
| **Component 1 — Full Realized OOS (2024-01-01 → 2025-12-31)** | TBD-pending-smoke-run | TBD-pending-smoke-run |
| **Component 2 — 2026-onward sub-window (per ADR-0026 §D-1 Component 2)** | NOT-IN-SCOPE-at-v1 (substrate window ends 2025-12-31; v2 reserved) | NOT-IN-SCOPE-at-v1 |
| **Component 3 — Forward 1-year bootstrap projection ($10K → 252 sessions)** | TBD-pending-smoke-run | TBD-pending-smoke-run |

(Placeholder rows pre-smoke-run; populated at smoke-run completion via append-only update.
Per-symbol-per-N values reported across the 4-cell N grid `{3, 5, 10, 20}` per
design.md §5 + §11.2 BLOCKING precondition.)

## §1. End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

> **v1 SMOKE-PLACEHOLDER NOTE**: Tables 1–9 will be populated upon smoke walk-forward
> completion. Smoke-run launch command (per `--stable-state-n N` for each N in the
> pre-registered grid `{3, 5, 10, 20}`)::
>
>     OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
>     uv run python scripts/run_h050_stable_state_walk_forward.py \
>         --stable-state-n N --smoke
>
> Wall-clock estimate per H050 v1 Phase G precedent: ~30-90 min per N × 4 N's =
> ~2-6 hr total for the 4-cell N grid sweep at smoke configuration.

### Table 1. P/L (realized OOS, $10K starting capital, 100%-of-equity-when-active per ADR-0013 §3.1.1)

| Symbol | N | Arm | End equity | % change | OOS bars | OOS sessions (eq) |
|---|---|---|---:|---:|---:|---:|
| ES | 3 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| ES | 5 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| ES | 10 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| ES | 20 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| ES | — | unconditional | TBD | TBD | TBD | TBD |
| NQ | 3 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| NQ | 5 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| NQ | 10 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| NQ | 20 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| NQ | — | unconditional | TBD | TBD | TBD | TBD |

### Table 1c. Payoff-shape diagnostics (per [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness)

| Symbol | N | Arm | τ_3 | 95% CI | Annotation |
|---|---|---|---:|---|---|
| ES | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD per-N | TBD per-N | TBD per-N |
| NQ | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD per-N | TBD per-N | TBD per-N |

### Table 2. Drawdown (realized + projected)

| Symbol | N | Arm | Realized max-DD | Proj median DD | Proj q95 DD |
|---|---|---|---:|---:|---:|
| ES | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD per-N | TBD per-N | TBD per-N |
| ES | — | unconditional | TBD | TBD | TBD |
| NQ | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD per-N | TBD per-N | TBD per-N |
| NQ | — | unconditional | TBD | TBD | TBD |

### Table 3. Sharpe — primary inference (T = SR_gated_stable_N − SR_uncond per design.md §1; per-N)

| Symbol | N | SR_gated_stable_N | SR_uncond | T_H050_stable_state(N) | LW2008 CI [low, high] | excludes zero | T annualised |
|---|---|---:|---:|---:|---|:---:|---:|
| ES | 3 / 5 / 10 / 20 | TBD per-N | TBD | TBD per-N | TBD per-N | TBD per-N | TBD per-N |
| NQ | 3 / 5 / 10 / 20 | TBD per-N | TBD | TBD per-N | TBD per-N | TBD per-N | TBD per-N |

### Table 3a. Terminal-wealth q05 (per [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| Symbol | N | Arm | q05 ($10K baseline) | Annotation |
|---|---|---|---:|---|
| ES | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD per-N | TBD per-N |
| NQ | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD per-N | TBD per-N |

### Table 3b. Calmar-differential (per ADR-0017 §3)

| Symbol | N | Calmar_diff | 95% CI | Annotation |
|---|---|---:|---|---|
| ES | 3 / 5 / 10 / 20 | TBD per-N | TBD per-N | TBD per-N |
| NQ | 3 / 5 / 10 / 20 | TBD per-N | TBD per-N | TBD per-N |

### Table 3c. Profit-factor + R-multiple-mean (per ADR-0017 §3)

| Symbol | N | PF_diff | R-mean | R-mean 95% CI | Annotation |
|---|---|---:|---:|---|---|
| ES | 3 / 5 / 10 / 20 | TBD per-N | TBD per-N | TBD per-N | TBD per-N |
| NQ | 3 / 5 / 10 / 20 | TBD per-N | TBD per-N | TBD per-N | TBD per-N |

### Table 4. Annualised Sharpe (×√(252×390))

| Symbol | N | SR_gated_stable_N | SR_uncond |
|---|---|---:|---:|
| ES | 3 / 5 / 10 / 20 | TBD per-N | TBD |
| NQ | 3 / 5 / 10 / 20 | TBD per-N | TBD |

### Table 5. Win/Loss/Zero bar counts + win rate

| Symbol | N | Arm | W | L | Z | Win rate W/(W+L+Z) |
|---|---|---|---:|---:|---:|---:|
| ES | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| ES | — | unconditional | TBD | TBD | TBD | TBD |
| NQ | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD | TBD | TBD | TBD |
| NQ | — | unconditional | TBD | TBD | TBD | TBD |

### Table 6. Forward 1-year projection ($10K → 252 sessions; iid bootstrap; n_paths=5,000)

| Symbol | N | Arm | Median | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ES | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD per-N | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| NQ | 3 / 5 / 10 / 20 | hmm_gated_stable_N | TBD per-N | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

### Table 7. Hansen SPA family p-value (M = 4-N × 2-symbol = 8 strategies per design.md §1.4 SECONDARY)

| Symbol | M | SPA p | Annotation |
|---|---:|---:|---|
| ES | 4 (per-N family across 4 N's) | TBD | TBD |
| NQ | 4 (per-N family across 4 N's) | TBD | TBD |
| **Joint (8-strategy family + RW-FWER per H055 precedent)** | 8 | TBD | TBD |

### Table 8. Other KPIs (load-bearing for the H-c whipsaw discriminant per design.md §7)

| KPI | Value | Notes |
|---|---|---|
| best N (per symbol, by MPPM(ρ=1)) | TBD per-symbol | Operator-readable per-N selection from the 4-cell grid |
| **transition rate (gate flips/bar; per-N)** | **TBD per-N — LOAD-BEARING for H-c hypothesis** | H050 v1 baseline = ~30.33% per parent INVESTIGATE memo §6.3; H050.stable-state expected to fall monotonically as N rises if H-c whipsaw dominates |
| **cost-drag attribution (per-N)** | **TBD per-N — LOAD-BEARING for H-c hypothesis** | per design.md §7; per-N cost-drag should decrease as N rises if H-c whipsaw dominates (cost-drag tied to forced flips) |
| n_folds realized/expected | TBD/TBD | per ADR-0013 §9 stopping rule |
| max-DD ratio (arm/passive; per-N) | TBD per-N | |
| cost model | nt8_es_nq_rth_v1 (conservative-prior per ADR-0025 §D-3) | |
| Kelly multiplier | 1.0 (H050 v1 sizing convention) | not in scope per design.md §11.1 |
| L-skewness τ_3 (per-N) | TBD per-N | per ADR-0019 §3 |
| stability-filter N grid | {3, 5, 10, 20} | per design.md §5 pre-registered grid |

### Table 9. Methodological-correctness annotations

`leakage-canary-pass · bss-n/a · reliability-n/a · cost-conservative-prior · dsr-n/a (M=8 < project default `dsr_activation_size = 10`) · mppm-rho1-TBD-per-N · tw-q05-TBD-per-N · calmar-diff-TBD-per-N · pf-diff-TBD-per-N · r-multiple-mean-TBD-per-N · payoff-shape-TBD-per-N · causal-mechanism-correlation-only · kelly-multiplier-1.0 · gate-ordering-highest-mean (H050 v1 canonical preserved) · stability-filter-N-per-cell · transition-rate-TBD-per-N · monotonicity-verdict-TBD · data-overlap-h050-v1-acknowledged · paradigm-adr-0024-aggressive-growth-n/a · repro-log-complete (TBD pending smoke completion)`

### Bottom line (≤ 8 sentences per ADR-0014 §3.2)

TBD pending smoke walk-forward completion. v1 emits as orchestrator-readiness placeholder
per the Phase O.20 scope-bound directive: the orchestrator + 3 test suites (40/40 H050.
stable-state tests green; 19/19 H050.invert tests preserved as regression) + audit trail
landed in this commit; smoke walk-forward execution deferred to a separate operator-
authorized cycle. On smoke-run completion, this v1 will be populated in place per ADR-
0013 §4.1 non-loss (existing TBD fields filled; structural body preserved verbatim) with
per-N rows across the pre-registered `{3, 5, 10, 20}` grid + the load-bearing
`monotonicity-verdict-{improving, flat, worsening, mixed}` annotation per design.md §8
discriminating the H-c whipsaw hypothesis from the paired sibling H050.invert (Variant A).

## Empirical-prediction discriminant (load-bearing per parent INVESTIGATE memo §7.3)

Per the parent [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md) §7.3 Variant B:

- **H-c whipsaw dominance** (forced gate flips are the load-bearing failure mode): predicted
  H050.stable-state realized OOS improves monotonically as N rises (transition rate falls;
  cost-drag falls; realized OOS approaches neutral); paired sibling H050.invert produces
  continued negative realized OOS.
- **H-b anti-selection dominance** (gate selects worse-Sharpe state): predicted H050.stable-
  state realized OOS WORSENS monotonically as N rises (stabilizing the gate locks it into
  the worse-Sharpe state for longer); paired sibling H050.invert produces non-negative
  realized OOS.
- **Mixture**: both variants partially improve realized OOS but neither fully restores
  positive realized OOS edge.

The discriminant is non-binding per [ADR-0013 §1 no-binding-gates](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md);
operator-discretionary interpretation per the KPI report card + sibling [H050.invert v1](../H050_invert/H050_invert_kpi_report_v1.md).

## v1 emission scope

v1 lands at orchestrator-readiness commit per the Phase O.20 scope-bound directive. The
deliverables completed in this commit:

- **Orchestrator extension** to [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py):
  module-level `_STABLE_STATE_N` flag + `--stable-state-n N` CLI flag + N-bar stability
  filter at the single gate-engagement site in `_predict_fold` (after
  `filter_states_from_prior`). Default N=1 preserves H050 v1 bit-identical behavior.
- **Wrapper script** at [scripts/run_h050_stable_state_walk_forward.py](../../../scripts/run_h050_stable_state_walk_forward.py)
  enforcing `--hypothesis H050_stable_state` + `--config H050_stable_state.yaml` invariants
  + requiring `--stable-state-n N` explicit (no default; operator must choose N from the
  pre-registered grid).
- **Unit tests** at [tests/unit/test_h050_stable_state_orchestrator.py](../../../tests/unit/test_h050_stable_state_orchestrator.py)
  (19 tests; 5 classes; covers module-flag default, CLI argv invariants, stability-filter
  logic, production-vs-helper parity, module-flag isolation).
- **BLOCKING fold-continuity test** at [tests/unit/test_h050_stable_state_fold_continuity.py](../../../tests/unit/test_h050_stable_state_fold_continuity.py)
  (15 parametrized tests across the pre-registered N grid {3, 5, 10, 20}; covers counter-
  reset-at-fold-boundary + PIT-causality + N=1 H050-v1-byte-equality).
- **Cycle-4 PIT canary integration test** at [tests/integration/test_h050_stable_state_pit_canaries.py](../../../tests/integration/test_h050_stable_state_pit_canaries.py)
  (6 tests; 5 canary classes A-E covering filter PIT-causality, fold-boundary reset,
  no-train→test-leak, NaN-poison + module-flag isolation, full-composition).
- **Audit trail** at [docs/audits/audit_trail_2026-05-20_h050_stable_state_orchestrator.md](../../../docs/audits/audit_trail_2026-05-20_h050_stable_state_orchestrator.md).
- **Test results**: 40/40 H050.stable-state tests green (19 + 15 + 6); 19/19 H050.invert
  regression tests preserved.

**Out-of-scope at v1 (deferred to separate operator-authorized cycle)**: smoke walk-forward
execution per `--stable-state-n N` for each N ∈ {3, 5, 10, 20}; sidecar SHA capture;
numeric population of Tables 1-9 + §0 3-component header; v1 → v2 successor cycle if
operator-discretionary post-smoke review motivates further refinement.

## Canonical full-production launch command (for next operator-authorized cycle)

For each N in the pre-registered grid `{3, 5, 10, 20}`, the canonical launch command per
[ADR-0010 / ADR-0011 supervised-run](../../../docs/decisions/ADR-0011-production-walkforward-runbook.md) is:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
uv run python scripts/supervised_run.py \
    --hypothesis H050_stable_state \
    --config config/hypotheses/H050_stable_state.yaml \
    --extra-args "--stable-state-n N"
```

Operator sweeps the pre-registered grid by repeating the command for N ∈ {3, 5, 10, 20};
each run emits its own sidecar JSON via `RunContext` per ADR-0013 §3.1 reproducibility
envelope. Smoke-mode equivalent uses `scripts/run_h050_stable_state_walk_forward.py
--stable-state-n N --smoke` for fast iteration.

## Cross-references

- Parent H050 KPI v1: [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../H050/H050_kpi_report_v1.md)
- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
- Sibling H050.invert v1: [research/01_hypothesis_register/H050_invert/H050_invert_kpi_report_v1.md](../H050_invert/H050_invert_kpi_report_v1.md)
- Design: [design.md](design.md)
- Data requirements: [data_requirements.md](data_requirements.md)
- Lit review: [lit_review_H050_stable_state_2026-05-20.md](lit_review_H050_stable_state_2026-05-20.md)
- v0 skeleton (preserved verbatim per ADR-0013 §4.1 non-loss): [H050_stable_state_kpi_report_v0.md](H050_stable_state_kpi_report_v0.md)
- Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-20_h050_stable_state_orchestrator.md](../../../docs/audits/audit_trail_2026-05-20_h050_stable_state_orchestrator.md)
- Orchestrator wrapper: [scripts/run_h050_stable_state_walk_forward.py](../../../scripts/run_h050_stable_state_walk_forward.py)
- Canonical orchestrator extension: [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) (module-level `_STABLE_STATE_N` + `--stable-state-n` CLI flag + stability filter in `_predict_fold`)
- Unit tests: [tests/unit/test_h050_stable_state_orchestrator.py](../../../tests/unit/test_h050_stable_state_orchestrator.py)
- Fold-continuity test (BLOCKING): [tests/unit/test_h050_stable_state_fold_continuity.py](../../../tests/unit/test_h050_stable_state_fold_continuity.py)
- PIT canary integration test (BLOCKING): [tests/integration/test_h050_stable_state_pit_canaries.py](../../../tests/integration/test_h050_stable_state_pit_canaries.py)
- Canonical format references: [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0018 §D-1 + §D-2](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) + [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) + [ADR-0024 §D-1](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) + [ADR-0025 §D-1..§D-7](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) + [ADR-0026 §D-1..§D-3](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) + [ADR-0027 §D-4](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md).
