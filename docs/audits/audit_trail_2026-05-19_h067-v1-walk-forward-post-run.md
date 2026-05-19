---
schema_version: audit_trail_v1
date: 2026-05-19
artifact_under_audit: H067 v1 production walk-forward + KPI report card v1 emission
hypothesis_id: H067
audit_type: post-run audit gate per ADR-0011
rounds_used: 1
cap_per_skill_md: 3
verdict: accept-with-residuals
---

# Audit Trail — H067 v1 production walk-forward + KPI v1 (2026-05-19 post-run)

Per [ADR-0011 production-walkforward-runbook](../decisions/ADR-0011-production-walkforward-runbook.md) §"Post-run audit gate" + the audit-remediate-loop skill (3-round cap per SKILL.md), this trail documents the post-run audit on the H067 v1 sweep output. Audit verdict at Round 1: `accept-with-residuals`. Per the audit-remediate-loop discipline, additional rounds (Round 2 + Round 3 verification) are deferred per the diminishing-returns argument since the H_1 verdict is structurally determined by the conservative_prior linear-scaling cost-model mechanism (predicted in design.md §1.4 + §6; empirically confirmed by sweep output).

## Round-1 audit scope (2026-05-19 post-sweep)

3 parallel specialist branches per the audit-remediate-loop skill convention:
- **Quant-auditor branch**: methodology + inference + KPI-cell numerical agreement.
- **Reproducibility-verifier branch**: RunContext + ReproLog 13-field schema + sidecar SHA + substrate SHA binding.
- **Format-auditor branch**: ADR-0014 §3.2 13-table compliance + ADR-0026 §D-1 §0 3-component header + ADR-0028 §D-2 + §D-4 annotation grammar.

## R1 findings

### F1-Q-1 (R1 quant; major; CLOSED inline pre-emission)

`MPPMResult.point_estimate` attribute access defect inherited from H065 sweep fork. The H065 sweep script's `_run_tp_overlay_simulation` uses `mppm_ci_result.point_estimate` which is NOT a field on the `MPPMResult` dataclass at [src/skie_ninja/inference/mppm.py:83](../../src/skie_ninja/inference/mppm.py). The correct attribute is `theta_hat` per the GISW 2007 manipulation-proof point-estimate convention. The H065 sweep's exception fallback path masks the defect by falling back to `mppm_rho_1(...)` directly; the H067 fork inherited the buggy pattern. First 7 H067 cells emitted with `MPPM CI = [NaN, NaN]`.

**Resolution applied inline**: rebuilt H067 sweep at `scripts/run_h067_n_lot_sweep.py` with corrected attribute access (`mppm_ci_result.theta_hat` + null-safe access on `ci_low`/`ci_high`/`excludes_zero`). First aborted run discarded (cell 1-7 outputs not committed). Re-launched cleanly; all 60 cells emit valid MPPM CI.

**Cross-hypothesis follow-up registered**: `P1-H065-SWEEP-MPPM-ATTRIBUTE-FIX` (BLOCKING-BEFORE-NEXT-H065-V3-RUN; the H065 sweep at [scripts/run_h065_tp_overlay_sweep.py](../../scripts/run_h065_tp_overlay_sweep.py) has the same defect; H065 v1/v2 KPI emissions cite `point_estimate` paths that produce NaN — the only reason H065 v1/v2 emitted valid CIs is that the fallback path called `mppm_rho_1(...)` directly. Recommend fix at next H065 V3 emission cycle.

### F1-Q-2 (R1 quant; informational; documented in KPI card §"Empirical findings")

Kelly multiplier is structurally invariant within N-lot cells under the H067 v1 simulator. Per H062 v1 KPI report card §"Scope deviations" + the H065 sweep convention inherited verbatim: the per-trade sizing formula is `size_from_risk = (risk_budget_pct × equity) / dollar_1r_per_contract` — Kelly multiplier is NOT multiplied into the position-size formula. Kelly is a hyperparameter at inner-CV selection only.

**Empirical consequence**: at any N-lot cell, cells across all 6 Kelly values `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` produce BIT-IDENTICAL output (same ROI, same MPPM, same trade count). The effective family size is **5 N-cells × 2 cost arms = 10 distinct cells**, NOT 60. This is consistent with the H067 design.md §5.3 declaration that the Kelly grid is preserved per ADR-0018 D-2 inheritance but not actually exercised at the simulator layer.

**Resolution**: documented in KPI v1 §"Empirical findings". The Kelly grid is preserved for design.md §5 binding-completeness (per `P1-H067-FULL-INNER-CV-GRID-V2` deferred follow-up); the v1 emission reports the 60 cells in the canonical table per design.md §13 with the Kelly column as a structural-invariance diagnostic.

### F1-Q-3 (R1 quant; load-bearing structural finding; ACCEPT)

H067 N-lot mechanism FAILS to lift any cell above the H067 §1(c) inferential criterion (cost-friction-breakeven ratio ≥ 2) under conservative_prior cost model. This is the EXPECTED OUTCOME per:

- H067 design.md §1.4 ("Pre-empirical caveat: H067 is a cost-light variant of a marginal-mean-edge factor"): "Per H067 design.md §17 amendment 2026-05-19: post-Phase-O.16 SIL fee recalibration shifts parent ratio to **0.955** (sub-breakeven)."
- H067 design.md §6 ("Cost-friction-breakeven mechanics at SIL N-lot"): "the **conservative_prior cost-model scaling is approximately linear in `n_contracts` for both commission AND slippage**; the cost-friction-breakeven ratio is **structurally invariant under N-lot scaling at the conservative_prior**."
- Cross-hypothesis investigation 2026-05-19 §6.1 (Phase O.16 addendum): post-recalibration SIL ratio = 0.955 with 52.3% CRR required.

**Empirical confirmation**: the sweep shows ratio actually DEGRADES at higher N-lot values (N=1 A1 ratio = 0.769; N=2 A1 ratio = 0.592) — confirming the design.md §6 prediction + revealing an UNANTICIPATED mechanism: the current-equity rebase × cost-drag interaction kills trade entries (N=1 A1: 1,922 trades; N=2 A1: 915 trades). As equity shrinks from cost drag, the position-size floor at `risk_budget × current_equity / dollar_1r_per_contract` drops to 0 contracts more frequently, eliminating entries.

**Resolution**: documented in KPI v1 §"Bottom line" + §"Empirical findings" as the canonical-instance ADR-0027 §D-3 finding (H067 R1 audit caught the linear-scaling cost mechanism BEFORE the empirical run; this run is the after-the-fact empirical confirmation that the mechanism doesn't recover).

### F1-R-1 (R1 repro; minor; CLOSED inline)

ReproLog 13-field schema MUST be complete at v1 emission per `P1-H067-REPROLOG-WIRE` BLOCKING-BEFORE-V1-EMISSION. The H067 sweep wraps execution in `RunContext` + emits canonical ReproLog at `logs/reproducibility/<run_id>.json` per ADR-0011 gate 8. Verified.

### F1-R-2 (R1 repro; minor; CLOSED inline)

Per-partition SHA enumeration emitted in sidecar `sil_partition_shas` field per `P1-H067-SUBSTRATE-PER-PARTITION-SHA-EMIT`. 12 SIL partitions enumerated (2015 → 2026); each with `sha256` + `row_count`. Verified.

### F1-F-1 (R1 format; minor; CLOSED inline)

KPI v1 card includes all 13 ADR-0014 §3.2 mandatory tables + ADR-0026 §D-1 §0 3-component summary header + ADR-0019 §3 Table 1c L-skewness diagnostics + ADR-0028 §D-2 cost-friction-dominated-edge annotation + ADR-0028 §D-4 `kill-switch-mode-block` annotation + `cost-{zero, conservative-prior}` annotation set per ADR-0025 §D-5. Per ADR-0026 §D-3 `not-promising-*` annotation emitted per cell where MPPM CI does not strictly exclude zero positively (expected on all conservative_prior A1 cells per design.md §1.4 prediction).

### Non-binding observations (minor; documented for future cycles)

- **N-lot grid {1, 2, 3, 4, 5}** is bounded ABOVE by the ADR-0001 retail capacity ceiling for SIL (= 5). The grid is EXHAUSTIVE within the retail-tier sandbox per `P1-H067-N-LOT-CAP-CALIBRATION` (CLOSED via H067 design.md §11.1 K-4 binding + this audit-trail verification).

- **Trade-frequency reduction** at A1 is a structural-but-undocumented mechanism not anticipated in design.md §1.4 prediction. Recommend adding a §17 revision-log entry (`P1-H067-V2-TRADE-FREQUENCY-INVESTIGATE`) tracking the equity-rebase × cost-drag interaction observation for v2 cycle interpretation. Non-blocking.

- **Sensitivity table** at sensitivity_mult ∈ {1.0, 0.5, 0.0} per design.md §6 binding is emitted in sidecar `cost_sensitivity_table` block. Operator-actionable diff: at sensitivity_mult=0.5 (50% slip cut anchored on cross-hypothesis investigation §7.2 practitioner anecdote), the parent N=1 cell ratio rises from ~0.77 → ~1.30; still BELOW the ratio ≥ 2 threshold for cost-friction-dominated-edge-present. At sensitivity_mult=0.0 (zero-slip; commission-only sensitivity bound), the parent cell ratio rises to ~3.7 — ABOVE threshold. Confirms the design.md §6 + cross-hypothesis investigation 2026-05-19 §7.2 forward path: the H_1 inferential criterion is operationally evaluable only under paper-trade-empirical calibration of the slip-reduction component.

## Round-2 verification posture

Per the audit-remediate-loop skill 3-round cap convention + the operator-stated "diminishing returns" framing: Round 2 verification is DEFERRED. The H_1 verdict is structurally determined (cost-friction-breakeven ratio is invariant under N-lot scaling at conservative_prior linear cost; empirically confirmed by N=1 → N=2 ratio drift from 0.769 → 0.592). No additional rounds would materially shift the verdict.

Round 2 verification would re-examine: (a) any residual sidecar binding defect; (b) DSR deflation correctness across the 10 effective-distinct cells; (c) Sharpe-vs-passive-long benchmark computation. These are non-load-bearing for the v1 H_1 null verdict and tracked under `P1-H067-V2-DSR-DEFLATION-VERIFY` non-blocking follow-up.

## Audit-trail residuals

| Residual | Status | Description |
|---|---|---|
| `P1-H065-SWEEP-MPPM-ATTRIBUTE-FIX` | NEW; BLOCKING-BEFORE-NEXT-H065-V3-RUN | H065 sweep at scripts/run_h065_tp_overlay_sweep.py:579 has the same `mppm_ci_result.point_estimate` defect. Fix attribute access to `.theta_hat`. |
| `P1-H067-FULL-INNER-CV-GRID-V2` | NON-BLOCKING; OPEN | Wire Kelly multiplier into per-trade sizing formula at v2 (current invariance is a design.md §5 binding-completeness placeholder). |
| `P1-H067-V2-TRADE-FREQUENCY-INVESTIGATE` | NON-BLOCKING; OPEN | Investigate the equity-rebase × cost-drag interaction that reduces N=1→N=2 trade count by ~50% under A1. |
| `P1-H067-V2-DSR-DEFLATION-VERIFY` | NON-BLOCKING; OPEN | Verify DSR deflation correctness across 10 effective-distinct cells (or recompute over 30 conservative_prior cells with Kelly-distinct sizing in v2). |
| `P1-H067-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` | OPEN; BLOCKING-BEFORE-PAPER-TRADE-EVALUATED | Per design.md §17 + this audit's empirical confirmation: H_1 is operationally evaluable only under paper-trade-empirical calibration (the conservative_prior + N-lot path is structurally null). |
| `P1-H067-COMMISSION-TIER-VERIFY` | OPEN; non-blocking | Verify whether SIL commission has a VIP tier discount at >= 1000 contracts/month (NinjaTrader Brokerage commission schedule does NOT publish public VIP-tier discount as of 2026-05-19; recommend operator-side commission negotiation per [config/instruments.yaml `commission_reviewed_for_broker: null` placeholder](../../config/instruments.yaml)). |

## Cross-references

- [Sweep script: scripts/run_h067_n_lot_sweep.py](../../scripts/run_h067_n_lot_sweep.py)
- [PIT canary integration test: tests/integration/test_h067_pit_canaries.py](../../tests/integration/test_h067_pit_canaries.py)
- [KPI report card v1: research/01_hypothesis_register/H067/H067_kpi_report_v1.md](../../research/01_hypothesis_register/H067/H067_kpi_report_v1.md)
- [Design: H067 design.md](../../research/01_hypothesis_register/H067/design.md)
- [Pre-registration audit trail (Phase O.15): docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md](audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md)
- [Cross-hypothesis investigation (parent + addendum): research/01_hypothesis_register/_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md](../../research/01_hypothesis_register/_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md)
- [ADR-0017 survival-constrained metric vector](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md)
- [ADR-0018 MPPM(ρ=1) inner-CV fitness](../decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md)
- [ADR-0019 L-skewness annotation](../decisions/ADR-0019-barbell-payoff-shape-screening.md)
- [ADR-0025 abandonment-trigger primitives](../decisions/ADR-0025-abandonment-trigger-infrastructure.md)
- [ADR-0026 paradigm + reporting refinements](../decisions/ADR-0026-paradigm-and-reporting-refinements.md)
- [ADR-0027 operational-discipline bounded exploration](../decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- [ADR-0028 K-6/K-7 size-down + cost-friction-edge](../decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md)
