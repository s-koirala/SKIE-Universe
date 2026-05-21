---
hypothesis_id: H050_invert
parent_hypothesis_id: H050
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-20
git_head: f665aefc422ca42efaf8603d10e4dc8e77e0aca8
substrate_dataset_checksum: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_scientific_payload_sha256: TBD-pending-smoke-completion
run_id: 29eac562e2354b91acdb0f65a7198b00
sizing_convention: hmm_gated_multibar_intraday
supersedes: null
superseded_by: null
emission_mode: smoke
emission_caveat: |
  v1 emission is SMOKE-mode (--smoke flag): 1-cell label grid (center cell only;
  pt_sl=1.5, vb=60m, vl=60), 5 LightGBM random-search draws (vs production 200),
  2 inner walk-forward CV folds (vs production 3). The smoke mode validates the
  H050.invert gate-state-inversion orchestrator pipeline end-to-end on the canonical
  post-Phase-O.10 substrate (317429e4...) but does NOT exercise the full hyperparameter
  surface. Canonical full-production run scheduled per `P1-H050-INVERT-PRODUCTION-RUN`
  (~7-8 hr wall-clock per H050 v1 Phase G precedent).
---

# H050.invert — KPI Report Card v1 (smoke emission)

> **Smoke-mode emission** for hypothesis H050.invert per [design.md §5][1]; tests
> the H-b anti-selection sub-hypothesis from the parent
> [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo][2] §7.3 Variant A
> by inverting the HMM gate-state selection from canonical highest-mean (H050 v1)
> to lowest-mean (H050.invert). v1 lands in smoke mode for the [ADR-0027 §D-3
> empirical-before-amendment][3] sequencing rule; v2 reserved for the full
> production walk-forward run per `P1-H050-INVERT-KPI-V2-FULL-RUN`.

- **Hypothesis**: H_1: SR_filtered_gated_LOW − SR_filtered_unconditional > 0 on the OOS test fold per [design.md §1][1]; gate-state inversion vs H050 v1's highest-mean canonical ordering tests H-b anti-selection.
- **Design.md**: [design.md](design.md) (frozen at `status: designed`)
- **Stage**: `kpi-report-emitted` per [ADR-0013 §1][4]. Next mandatory transition: `kpi-report-emitted` → `ninjascript-implemented` per ADR-0013 §5 (bridge-mediated per §1.2 since HMM filter requires Python inference). Operator-discretionary per the 2026-05-04 standing decline-ninjascript directive.
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)
- **Sibling**: [H050.stable-state](../H050_stable_state/H050_stable_state_kpi_report_v0.md) (paired-design mechanism-discrimination Variant B; pending smoke emission)

## §0. 3-component KPI summary header (per [ADR-0026 §D-1][5])

| Component | ES | NQ |
|---|---|---|
| **Component 1 — Full Realized OOS (2024-01-01 → 2025-12-{03,19})** | TBD pending smoke completion | TBD pending smoke completion |
| **Component 2 — 2026-onward sub-window** | NOT IN SCOPE at v1 smoke; substrate window ends 2025-12-{03,19}. v2 reserved | NOT IN SCOPE at v1 smoke |
| **Component 3 — Forward 1-year bootstrap projection ($10K → 252 sessions)** | TBD pending smoke completion | TBD pending smoke completion |

## §1. End-of-simulation results summary (per [ADR-0014 §3.2][6] + [ADR-0019 §3][7])

> **v1 SMOKE NOTE**: tables 1-9 will be populated upon smoke walk-forward run completion.
> The smoke run is in flight (`run_id` = `29eac562e2354b91acdb0f65a7198b00`); HMM cold-fit
> on the 3M-row train fold is the dominant wall-clock cost (~30-90min per the H050 v1
> Phase G precedent + the d=1 dedup at [src/skie_ninja/models/regime/selection.py][8]).
> Population of numeric fields is a follow-up commit cycle gated on the smoke run's clean
> exit + sidecar SHA256 capture.

### Table 1. P/L (realized OOS, $10K starting capital, 100%-of-equity-when-active per ADR-0013 §3.1.1)

| Symbol | Arm | End equity | % change | OOS bars | OOS sessions (eq) |
|---|---|---:|---:|---:|---:|
| ES | hmm_gated (inverted) | TBD | TBD | TBD | TBD |
| ES | unconditional | TBD | TBD | TBD | TBD |
| NQ | hmm_gated (inverted) | TBD | TBD | TBD | TBD |
| NQ | unconditional | TBD | TBD | TBD | TBD |

### Table 1c. Payoff-shape diagnostics (per [ADR-0019 §3][7] L-skewness)

| Symbol | Arm | τ_3 | 95% CI | Annotation |
|---|---|---:|---|---|
| ES | hmm_gated (inverted) | TBD | TBD | TBD |
| NQ | hmm_gated (inverted) | TBD | TBD | TBD |

### Table 2. Drawdown (realized + projected)

| Symbol | Arm | Realized max-DD | Proj median DD | Proj q95 DD |
|---|---|---:|---:|---:|
| ES | hmm_gated (inverted) | TBD | TBD | TBD |
| ES | unconditional | TBD | TBD | TBD |
| NQ | hmm_gated (inverted) | TBD | TBD | TBD |
| NQ | unconditional | TBD | TBD | TBD |

### Table 3. Sharpe — primary inference (T = SR_gated_LOW − SR_uncond per design.md §1)

| Symbol | SR_gated_LOW | SR_uncond | T_H050_invert | LW2008 CI [low, high] | excludes zero | T_H050_invert annualised |
|---|---:|---:|---:|---|:---:|---:|
| ES | TBD | TBD | TBD | TBD | TBD | TBD |
| NQ | TBD | TBD | TBD | TBD | TBD | TBD |

### Table 3a. Terminal-wealth q05 (per [ADR-0017 §3][9])

| Symbol | Arm | q05 ($10K baseline) | Annotation |
|---|---|---:|---|
| ES | hmm_gated (inverted) | TBD | TBD |
| NQ | hmm_gated (inverted) | TBD | TBD |

### Table 3b. Calmar-differential (per [ADR-0017 §3][9])

| Symbol | Calmar_diff | 95% CI | Annotation |
|---|---:|---|---|
| ES | TBD | TBD | TBD |
| NQ | TBD | TBD | TBD |

### Table 3c. Profit-factor + R-multiple-mean (per [ADR-0017 §3][9])

| Symbol | PF_diff | R-mean | R-mean 95% CI | Annotation |
|---|---:|---:|---|---|
| ES | TBD | TBD | TBD | TBD |
| NQ | TBD | TBD | TBD | TBD |

### Table 4. Annualised Sharpe (×√(252×390))

| Symbol | SR_gated_LOW | SR_uncond |
|---|---:|---:|
| ES | TBD | TBD |
| NQ | TBD | TBD |

### Table 5. Win/Loss/Zero bar counts + win rate

| Symbol | Arm | W | L | Z | Win rate W/(W+L+Z) |
|---|---|---:|---:|---:|---:|
| ES | hmm_gated (inverted) | TBD | TBD | TBD | TBD |
| ES | unconditional | TBD | TBD | TBD | TBD |
| NQ | hmm_gated (inverted) | TBD | TBD | TBD | TBD |
| NQ | unconditional | TBD | TBD | TBD | TBD |

### Table 6. Forward 1-year projection ($10K → 98,280 bars; iid bootstrap; n_paths=5,000)

| Symbol | Arm | Median | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ES | hmm_gated (inverted) | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| NQ | hmm_gated (inverted) | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

### Table 7. Hansen SPA family p-value

| Symbol | M | SPA p | Annotation |
|---|---:|---:|---|
| ES | 1 | TBD | M=1 degenerate per H050 v1 precedent (ADR-0008) |
| NQ | 1 | TBD | same |

### Table 8. Other KPIs

| KPI | Value | Notes |
|---|---|---|
| best label cfg | center cell (pt_sl=1.5, vb=60m, vl=60) | smoke 1-cell grid |
| n_folds realized/expected | TBD/TBD | smoke reduced fold count |
| max-DD ratio (arm/passive) | TBD | |
| cost model | nt8_es_nq_rth_v1 | conservative-prior; ADR-0025 §D-3 |
| Kelly multiplier | 1.0 (H050 v1 sizing convention) | not in scope per design.md §11.1 |
| Transition rate (gate flips/bar) | TBD | KEY DISCRIMINANT vs H050 v1's ~30.33% |
| L-skewness τ_3 (basket) | TBD | per ADR-0019 §3 |

### Table 9. Methodological-correctness annotations

`leakage-canary-pass · bss-n/a · reliability-n/a · cost-conservative-prior · dsr-n/a (M=1) · mppm-rho1-TBD · tw-q05-TBD · calmar-diff-TBD · pf-diff-TBD · r-multiple-mean-TBD · payoff-shape-TBD · causal-mechanism-correlation-only · kelly-multiplier-1.0 · gate-ordering-lowest-mean (THE INVERSION) · data-overlap-h050-v1-acknowledged · paradigm-adr-0024-aggressive-growth-n/a · repro-log-complete (TBD pending smoke completion)`

### Bottom line (≤ 8 sentences per ADR-0014 §3.2)

TBD pending smoke walk-forward completion. The smoke run is in flight as of 2026-05-20 evening; `run_id` `29eac562e2354b91acdb0f65a7198b00`. Per the parent [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM memo §7.3 Variant A][2], the empirical-prediction discriminant is: if H050.invert realized OOS basket > 0 substantially, H-b anti-selection dominates the H050 v1 catastrophe; if H050.invert ≈ H050 v1 (catastrophic), H-c whipsaw dominates; intermediate values indicate a mixture mechanism. The smoke run output will be populated into Tables 1-9 in the next commit cycle once the orchestrator emits the canonical sidecar JSON + scientific_payload_sha256.

## Empirical-prediction discriminant (load-bearing per parent INVESTIGATE memo §7.3)

Per the parent [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo][2] §7.3 Variant A:

- **H-b dominance** (H050 v1 selected worse-Sharpe state): predicted H050.invert realized OOS ≫ 0 (positive); paired sibling H050.stable-state has weaker positive effect.
- **H-c dominance** (whipsaw cost-drag is direction-agnostic): predicted H050.invert ≈ H050 v1 (catastrophic on both symbols); paired sibling H050.stable-state restores realized OOS via reduced gate-flip rate.
- **Mixture**: both variants improve realized OOS but neither fully restores positive realized OOS edge.

The discriminant is non-binding per [ADR-0013 §1 no-binding-gates][4]; operator-discretionary interpretation per the KPI report card v1 + sibling H050.stable-state KPI v1 (forthcoming).

## v1 emission scope

v1 lands at smoke completion (~30-90 min wall-clock estimate; HMM cold-fit dominated). The smoke configuration is:

- **Label grid**: 1 cell (center: pt_sl=1.5, vertical_barrier=60m, volatility_lookback=60). Full production = 27-cell Cartesian grid per design.md §4.
- **LightGBM random search**: 5 draws (vs production 200 per design.md §5).
- **Inner walk-forward CV folds**: 2 (vs production 3 per H050 v1 Phase G).
- **HMM cov grid**: [diag, full] preserved per design.md §5 + d=1 dedup at [src/skie_ninja/models/regime/selection.py][8].
- **HMM n_states grid**: BIC-selected per ADR-0005 (typically K=2 on H050 substrate).
- **Universe**: ES + NQ (both symbols).
- **OOS window**: 2024-01-01 → 2025-12-{03,19} per design.md §2 + per-symbol substrate right-edges.

## Cross-references

- Parent H050 KPI v1: [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../H050/H050_kpi_report_v1.md)
- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md][2]
- Sibling H050.stable-state v0: [research/01_hypothesis_register/H050_stable_state/H050_stable_state_kpi_report_v0.md](../H050_stable_state/H050_stable_state_kpi_report_v0.md)
- Design: [design.md][1]
- Data requirements: [data_requirements.md](data_requirements.md)
- Lit review: [lit_review_H050_invert_2026-05-20.md](lit_review_H050_invert_2026-05-20.md)
- Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-20_h050_invert_orchestrator_smoke.md](../../../docs/audits/audit_trail_2026-05-20_h050_invert_orchestrator_smoke.md)
- Orchestrator wrapper: [scripts/run_h050_invert_walk_forward.py](../../../scripts/run_h050_invert_walk_forward.py)
- Unit tests: [tests/unit/test_h050_invert_orchestrator.py](../../../tests/unit/test_h050_invert_orchestrator.py)
- PIT canary integration tests: [tests/integration/test_h050_invert_pit_canaries.py](../../../tests/integration/test_h050_invert_pit_canaries.py)
- Canonical format references: [ADR-0014 §3.2][6] + [ADR-0017 §3][9] + [ADR-0018 §D-1 + §D-2](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) + [ADR-0019 §3][7] + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) + [ADR-0024 §D-1](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) + [ADR-0025 §D-1..§D-7](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) + [ADR-0026 §D-1..§D-3][5] + [ADR-0027 §D-4][3].

[1]: design.md
[2]: ../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md
[3]: ../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md
[4]: ../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md
[5]: ../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md
[6]: ../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md
[7]: ../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md
[8]: ../../../src/skie_ninja/models/regime/selection.py
[9]: ../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md
