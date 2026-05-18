---
hypothesis_id: H055
schema_version: kpi_report_card_v1
version: 2
date: 2026-05-18
git_head: a5766fdba9193c46a1815a96ab10817f19a0f854
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_path: artifacts/runs/H055/v2_sweep_20260518T220351Z/sweep_sidecar.json
sweep_sha256: (per artifacts/runs/H055/v2_sweep_20260518T220351Z/sweep_sha256.txt)
run_id: v2_sweep_20260518T220351Z
sizing_convention: per_trade_atr_stop_5min_intraday_basket_log_return
supersedes: H055_kpi_report_v1.md
superseded_by: null
cost_model_v1_scope: pre_cost_research_only
parent_audit_trail: docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md
---

# H055 — KPI Report Card v2

> **H055 v2 aggressive-sizing sweep re-emission on canonical substrate `317429e4...`** (commit `a5766fd` 2026-05-18). Closes BLOCKING follow-up `P1-H055-V2-RERUN-ON-CANONICAL-SUBSTRATE` from the [2026-05-18 phase-O-merge audit](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md). H055 v1 (run_id `v2_sweep_20260516T025924Z`) bound to substrate `b93e544...` (sibling-worktree-only); H055 v2 (this card) re-runs on the canonical post-Phase-O.8 substrate in main checkout. v1 preserved verbatim per ADR-0013 §4.1 non-loss.

- **Hypothesis** (per [design.md §1](design.md)): H_1: at least one sweep variant produces a basket-level KPI configuration (MPPM(ρ=1) > 0; Calmar > 0.5; profit-factor > 1.1; R-multiple-mean > 0; payoff-shape ≠ skew-negative) under ADR-0017 §1 primary metric vector on the 2024-01-01 → 2026-06-30 OOS window.
- **Stage**: `kpi-report-emitted (v2)` per ADR-0013 §1. v1 → v2 transition is a substrate re-emission, not a stage advancement.
- **Stage tracker**: [stage.md](stage.md)
- **Cost model**: `cost-zero-v1-pre-cost-research-only` per operator standing directive.
- **Known caveat** (inherited from v1; tracked under `P1-H055-REPROLOG-WIRE` BLOCKING-BEFORE-V3): sweep sidecar carries 3 of 13 ReproLog fields; canonical 13-field ReproLog at `logs/reproducibility/{run_id}.json` is **absent**. Annotation `repro-log-incomplete` (corrected from v1's misleading `repro-log-present` per the [v1 corrigendum](H055_kpi_report_v1_corrigendum_2026-05-18.md)).

## End-of-simulation results summary

The full per-config × per-symbol KPI metrics table is at [`artifacts/runs/H055/v2_sweep_20260518T220351Z/kpi_metrics_table.md`](../../../artifacts/runs/H055/v2_sweep_20260518T220351Z/kpi_metrics_table.md) (5 configs × 4 symbols × 14 metrics per row). The v1 vs v2 substrate change produces small numerical drift; qualitative pattern preserved.

### Basket-level v1 vs v2 comparison

| Config | v1 basket OOS ROI | v2 basket OOS ROI | v1 sub-window | v2 sub-window |
|---|---:|---:|---:|---:|
| v1 (no aggressive sizing) | ~−0.5% | −0.6% | ~0.0% | +0.0% |
| C2 fullkelly | +18.4% | +18.5% | +4.0% | +4.1% |
| **C3 superkelly** | **+19.7%** | **+20.2%** | −4.1% | **−4.4%** |
| **C9 bocd_stepup** | **+12.1%** | **+13.9%** | **+2.5%** | **+2.5%** |
| C5 super_pyramid | −10.0% | −9.3% | +3.5% | +3.4% |

**v2 verdict**: substantively identical to v1. C3 superkelly produces highest full-OOS basket ROI (+20.2%); C9 bocd_stepup produces highest sub-window basket ROI (+2.5%) with lowest max-DD. Per-symbol best: **MGC C3 superkelly +87.0%** (single-symbol-cell strongest project-wide on H055).

### Strongest cells by MPPM(ρ=1) point estimate

| Rank | Config | Symbol | MPPM(ρ=1) | Sign | KPI annotation |
|---:|---|---|---:|:---:|---|
| 1 | C3 superkelly | MGC | +0.263 | + | `mppm-rho1-positive-pt-est` (CI deferred per `P1-H055-MPPM-RHO-1-CI-PRIMITIVE`) |
| 2 | C5 super_pyramid | MGC | +0.243 | + | same |
| 3 | C2 fullkelly | MGC | +0.206 | + | same |
| 4 | C9 bocd_stepup | MGC | +0.185 | + | same |
| 5 | C3 superkelly | ES | +0.099 | + | same |

(MPPM(ρ=1) CI computation deferred under `P1-H055-MPPM-RHO-1-CI-PRIMITIVE`; v2 reports point estimates only. CI required for full ADR-0017 §3 PRIMARY-table compliance.)

### L-skewness τ_3 (per [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

All v2 single-symbol cells report τ_3 ∈ [+0.06, +0.14] → `payoff-shape-skew-positive` across configs. Consistent with the H062 family pattern: ATR-stop truncates left tail; channel-breakout entry populates right tail.

### Methodological-correctness annotations (one-line per ADR-0013 §2 + §2.1)

`leakage-canary-deferred-v3` (PIT canary integration deferred per `P1-H055-PIT-CANARY-INTEGRATION-TEST-LANDED`) · `mppm-rho1-positive-pt-est-cell-MGC` (CI deferred) · `bocd-decay-flag-evaluated-per-config-v3` · `kelly-multiplier-{0.25, 1.0, 2.0, 2.5}` (super-Kelly annotations: C3 + C5 → `kelly-multiplier-2.5-super-kelly-operator-discretionary`) · `skew-positive-per-cell` · `claim-type-hybrid` · `cost-zero-v1-pre-cost-research-only` · **`repro-log-incomplete`** (3/13 ReproLog fields per `P1-H055-REPROLOG-WIRE` BLOCKING follow-up) · 5 unfulfilled design.md §11.2 BLOCKING preconditions per v1 caveat note (preserved into v2)

### Bottom line

H055 v2 re-runs the aggressive-sizing sweep on the canonical post-Phase-O.8 substrate `317429e4...` (closes `P1-H055-V2-RERUN-ON-CANONICAL-SUBSTRATE`); qualitative findings preserved from v1 with small numerical drift (C3 basket +20.2% vs v1 +19.7%; C9 basket +13.9% vs v1 +12.1%). MGC remains the project-wide strongest standalone cell across configs (C3 +87%; C5 +77%; C2 +72%; C9 +58%); ES + NQ + SIL produce wide cell-by-cell heterogeneity. MPPM(ρ=1) CI computation remains BLOCKING (`P1-H055-MPPM-RHO-1-CI-PRIMITIVE`); next mandatory transition per ADR-0013 §5 is `ninjascript-implemented` (per the user 2026-05-04 standing directive operator-discretionary upon canonical-format presentation). 4 of 5 design.md §11.2 BLOCKING preconditions remain open (PIT canary, power simulation, calibration holdout, OPTUNA inner-CV); these gate v3 emission. **Net verdict**: H_1 PARTIALLY-CONFIRMED on MGC-only (cell-conditional; not basket-level); H_1 NULL on ES + NQ + SIL.

Full metrics: [`artifacts/runs/H055/v2_sweep_20260518T220351Z/kpi_metrics_table.md`](../../../artifacts/runs/H055/v2_sweep_20260518T220351Z/kpi_metrics_table.md). Sidecar: [`artifacts/runs/H055/v2_sweep_20260518T220351Z/sweep_sidecar.json`](../../../artifacts/runs/H055/v2_sweep_20260518T220351Z/sweep_sidecar.json). Substrate-vintage reconciliation: [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md).
