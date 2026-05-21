---
hypothesis_id: H050_invert
parent_hypothesis_id: H050
schema_version: kpi_report_card_v0
version: 0
date: 2026-05-20
git_head: TBD-at-emission
substrate_dataset_checksum: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_scientific_payload_sha256: TBD-at-emission
run_id: TBD-at-emission
sizing_convention: hmm_gated_multibar_intraday  # ADR-0013 §3.1.1 entry for HMM-gated strategies; identical to H050 v1
supersedes: null
superseded_by: null
---

# H050.invert — KPI Report Card v0 (pre-emission skeleton)

> **Pre-emission v0 skeleton** for the H050.invert hypothesis — HMM regime-conditioned ES/NQ intraday directional signal with INVERTED gate-state selection per [design.md §5](design.md). v0 lands at this pre-registration commit per the H062 + H055 + H060 + H065 v0 precedent; numeric fields TBD per `P1-H050-INVERT-PROD-RUN`.
>
> Mandatory canonical-format sections per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) (§0 3-component header) + [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) (13 tables per ADR-0019 §3 amendment) + [ADR-0013 §3.1 + §3.2](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) (realized-OOS + forward-projection block).

- **Hypothesis**: H_1: SR_filtered_gated_LOW − SR_filtered_unconditional > 0 on the OOS test fold per [design.md §1](design.md); gate-state inversion vs H050 v1's highest-mean canonical ordering tests the H-b anti-selection sub-hypothesis per the parent [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md) §7.3 Variant A.
- **Design.md**: [design.md](design.md) (frozen at `status: designed`)
- **Stage**: `exploration-in-progress` per the [stage tracker](stage.md). Next mandatory transition: `kpi-report-emitted` upon production walk-forward emission per ADR-0013 §1.
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)
- **Sibling**: [H050.stable-state](../H050_stable_state/H050_stable_state_kpi_report_v0.md) (paired-design mechanism-discrimination Variant B)

## §0. 3-component KPI summary header (per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md))

| Component | ES | NQ |
|---|---|---|
| **Component 1 — Full Realized OOS (2024-01-01 → 2025-12-31)** | TBD at v1 emission | TBD at v1 emission |
| **Component 2 — 2026-onward sub-window (per ADR-0026 §D-1 Component 2)** | TBD at v1 emission | TBD at v1 emission |
| **Component 3 — Forward 1-year bootstrap projection ($10K → 252 sessions)** | TBD at v1 emission | TBD at v1 emission |

(Placeholder rows pre-emission; populated at v1 KPI report card emission per `P1-H050-INVERT-PROD-RUN`.)

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

13 tables placeholder; numeric fields populated at v1 emission. Tables 1, 1c (L-skewness), 2, 3, 3a (terminal-wealth-q05), 3b (Calmar-differential), 3c (profit-factor + R-multiple-mean), 4, 5, 6, 7, 8, 9.

### Bottom line (≤ 8 sentences per ADR-0014 §3.2)

TBD at v1 emission.

## Methodological-correctness annotations (per [ADR-0013 §2 + §2.1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md))

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-pass` / `leakage-canary-fail` | TBD | Cycle-4 leak canary; binding integration test path: [tests/integration/test_h050_invert_pit.py](../../../tests/integration/test_h050_invert_pit.py) per `P1-H050-INVERT-LEAKAGE-CANARY-INTEGRATION-TEST` |
| `bss-positive` / `bss-flat` / `bss-negative` | n/a | H050.invert inherits H050 v1 `bss-n/a` per design.md §1 (continuous trading-rule signal, not probabilistic forecast) |
| `reliability-in-band` / `reliability-out-of-band` | n/a | same rationale |
| `repro-log-complete` / `repro-log-incomplete` | TBD | 13-field ReproLog per CLAUDE.md §"Reproducibility" |
| `cost-{empirical-calibrated, conservative-prior, zero}` | `cost-conservative-prior` | per design.md §7 + ADR-0025 §D-3 + the operator standing zero-cost-v1-pre-cost-research-only directive |
| `dsr-positive` / `dsr-marginal` / `dsr-negative` | n/a (M=1) | per H050 v1 precedent |
| `mppm-rho1-{positive, marginal, negative}` | TBD | PRIMARY per ADR-0018 §D-1 |
| `payoff-shape-{skew-positive, skew-flat, skew-negative}` | TBD | per ADR-0019 §3 |
| `tw-q05-{above-half, above-zero, below-zero}` | TBD | per ADR-0017 §3 |
| `calmar-diff-{positive, marginal, negative}` | TBD | per ADR-0017 §3 |
| `pf-diff-{positive, marginal, negative}` | TBD | per ADR-0017 §3 |
| `r-multiple-mean-{positive, marginal, negative}` | TBD | per ADR-0017 §3 |
| `causal-mechanism-{causal, correlation, hybrid}` | `correlation-only` | per design.md §1.3 + ADR-0022 |
| `kelly-multiplier-{0.25, ...}` | `kelly-multiplier-1.0` (H050 v1 sizing convention; 100%-of-equity-when-active) | per design.md §11.1 + ADR-0018 §D-2 (Kelly-multiplier grid NOT in scope at v1) |
| `paradigm-adr-0024-aggressive-growth` | n/a (H050.invert v1 inherits H050 v1 sizing) | per design.md §11.1 |
| `data-overlap-h050-v1-acknowledged` | YES | per data_requirements.md §"Cross-hypothesis fit-set isolation table" |
| `gate-ordering-{highest-mean, lowest-mean, sharpe-ascending}` | `gate-ordering-lowest-mean` | per design.md §5 — THE inversion site; H050.invert binds the gate to the lowest-mean state |
| `promising-{kpi-vector-slug}-{cost-model-slug}-{substrate-sha-prefix-16}` | TBD at v1 | per ADR-0026 §D-3 |

## v0 emission scope

This v0 is **pre-emission skeleton** per the H062 + H065 v0 precedent: no walk-forward run has been executed. The v0 lands at this pre-registration commit to:

1. Establish the ADR-0026 §D-1 + ADR-0014 §3.2 + ADR-0019 §3 canonical-format scaffolding ahead of the v1 emission.
2. Cross-link the design.md + data_requirements.md + lit_review + stage tracker + failure log.
3. Anchor the `gate-ordering-lowest-mean` KPI annotation as the binding annotation for the H050.invert v1 emission (the inversion is pre-registered, not deferred).
4. Provide the operator with a complete reference for the BLOCKING preconditions per [design.md §11.2](design.md) that must close before the v1 production walk-forward.

## Cross-references

- Parent H050 KPI v1: [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../H050/H050_kpi_report_v1.md)
- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
- Sibling H050.stable-state v0: [research/01_hypothesis_register/H050_stable_state/H050_stable_state_kpi_report_v0.md](../H050_stable_state/H050_stable_state_kpi_report_v0.md)
- Design: [design.md](design.md)
- Data requirements: [data_requirements.md](data_requirements.md)
- Lit review: [lit_review_H050_invert_2026-05-20.md](lit_review_H050_invert_2026-05-20.md)
- Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-20_h050_successor_variants.md](../../../docs/audits/audit_trail_2026-05-20_h050_successor_variants.md)
- Canonical format references: [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0018 §D-1 + §D-2](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) + [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) + [ADR-0024 §D-1](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) + [ADR-0025 §D-1..§D-7](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) + [ADR-0026 §D-1..§D-3](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) + [ADR-0027 §D-4](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) + [ADR-0028](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md).
