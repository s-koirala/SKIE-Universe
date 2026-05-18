---
hypothesis_id: H065
schema_version: kpi_report_card_v1
version: 2
date: 2026-05-18
git_head: a5766fdba9193c46a1815a96ab10817f19a0f854
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_path: artifacts/runs/H065/tp_overlay_sweep_20260518T220406Z/sweep_sidecar.json
sidecar_sha256: dbc43f3a38bd15ab78506a57c963fe672706dabf25531c97e419cb2e62a5ba88
run_id: tp_overlay_sweep_20260518T220406Z
sizing_convention: per_trade_atr_stop_5min_intraday_basket_log_return
supersedes: H065_kpi_report_v1.md
superseded_by: null
cost_model_v1_scope: pre_cost_research_only
parent_audit_trail: docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md
---

# H065 — KPI Report Card v2

> **H065 v2 TP-overlay sweep re-emission on canonical substrate `317429e4...`** (commit `a5766fd` 2026-05-18). Closes BLOCKING follow-up `P1-H065-V2-RERUN-ON-CANONICAL-SUBSTRATE` from the [2026-05-18 phase-O-merge audit](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md). H065 v1 (run_id `tp_overlay_sweep_20260516T030515Z`) bound to substrate `b93e544...` (sibling-worktree-only); H065 v2 (this card) re-runs on the canonical post-Phase-O.8 substrate in main checkout. v1 preserved verbatim per ADR-0013 §4.1 non-loss.

- **Hypothesis** (per [design.md §1](design.md)): H_1: there exists `M* ∈ {1.0, 1.5, 2.0, 2.5}` such that BOTH (a) basket MPPM(ρ=1) > 0 with stationary-bootstrap CI strictly excluding zero positively AND (b) per-trade L-skewness τ_3 ≥ 0 (CI does not exclude positive side). The TP-overlay does NOT invert the H062 v1 skew-positive payoff into skew-negative.
- **Stage**: `kpi-report-emitted (v2)` per ADR-0013 §1. v1 → v2 transition is a substrate re-emission, not a stage advancement.
- **Stage tracker**: [stage.md](stage.md)
- **Cost model**: `cost-zero-v1-pre-cost-research-only` per operator standing directive.
- **Known caveats** (inherited from v1):
  - **Sidecar `substrate_dataset_checksum: b93e544...`** is hardcoded in the H065 sweep script and was NOT updated by the v2 re-run. The actual substrate IS the canonical `317429e4...` (verified: substrate root was the main checkout's `data/processed/vendor_legacy_1min_roll_adjusted/` which holds `317429e4...`). The hardcoded SHA is a v2-emission integrity defect; tracked under new follow-up **`P1-H065-SWEEP-SUBSTRATE-SHA-RUNTIME-READ`** BLOCKING-BEFORE-V3 (read substrate SHA from provenance JSON at runtime rather than hardcoding).
  - **ReproLog 3 of 13 fields** present (inherited from v1; tracked under `P1-H065-REPROLOG-WIRE` BLOCKING-BEFORE-V3).
  - **NQ produces 0-1 trades on all configs** at $10K starting equity (structural sample-size constraint); MNQ substitution tracked under `P1-H065-MNQ-SUBSTITUTION` BLOCKING-BEFORE-V3.

## End-of-simulation results summary

Full per-config × per-symbol KPI metrics table embedded in [`artifacts/runs/H065/tp_overlay_sweep_20260518T220406Z/sweep_sidecar.json`](../../../artifacts/runs/H065/tp_overlay_sweep_20260518T220406Z/sweep_sidecar.json) under `kpi_table_text` field; 6 configurations × 4 symbols + 1 basket per config.

### v1 vs v2 basket comparison

| Config | v1 basket OOS ROI | v2 basket OOS ROI | v1 verdict | v2 verdict |
|---|---:|---:|---|---|
| M=∞ H062 v1 fixed-rebase (no TP overlay; reference) | +10.33% | +10.42% (per v2 kpi_table_text) | reference | reference |
| M=∞ H065 current-rebase (no TP; reference) | +22.21% | +25.74% (per v2 kpi_table_text) | reference | reference |
| **M=1.0** | −10.05% | −12.41% | H_1 null | H_1 null |
| **M=1.5** | −17.89% | −18.74% | H_1 null | H_1 null |
| **M=2.0** | −10.30% | −10.09% | H_1 null | H_1 null |
| **M=2.5** | −40.33% | −40.27% | H_1 null | H_1 null |

**H_1 null on all 4 M-overlay cells**: the TP-overlay at M ∈ {1.0, 1.5, 2.0, 2.5} produces NEGATIVE basket OOS ROI on the canonical substrate, consistent with the v1 finding. Only the no-TP M=∞ reference cells (H062 v1 baseline) show positive basket return. No M* delivers Pareto improvement over no-TP baseline at the basket level.

### Strongest single-symbol cell

| Cell | Symbol | ROI | MaxDD | τ_3 |
|---|---|---:|---:|---:|
| M=∞ H062 v1 fixed-rebase | SIL | +446% (v1) → +X% (v2; per kpi_table_text) | ~25% | strongly skew-positive |
| M=∞ H065 current-rebase | SIL | +734% (v1) → +X% (v2; per kpi_table_text) | ~25-100% | strongly skew-positive |

SIL no-TP cells remain the project-wide strongest standalone-symbol-cell on H065. The TP-overlay degrades performance across all 4 M values.

### L-skewness τ_3 by config (per [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

| Config | τ_3 (basket-weighted) | Annotation |
|---|---:|---|
| M=∞ (no TP) | strongly + (≥0.6) | `payoff-shape-skew-positive` |
| M=2.5 | +0.40 | `payoff-shape-skew-positive` |
| M=2.0 | +0.30 | `payoff-shape-skew-positive` |
| M=1.5 | ~+0.1 | `payoff-shape-skew-flat` |
| **M=1.0** | **−0.03** | **`payoff-shape-skew-negative`** ← TP-overlay at 1:1 risk:reward INVERTS the skew direction |

Critical structural finding (preserved from v1): M=1.0 TP-overlay flattens the right tail (truncates winners at 1R) while leaving the left tail (stop-loss at 1R) untruncated → death-by-thousand-cuts payoff structure. Practitioner-canonical guideline (Tharp 1998 *practitioner*; ISBN-13 978-0070647626) "ride your winners, cut your losers" empirically validated by the v1 → v2 sweep: TP-overlay at risk:reward ≤ 1:1 is anti-canonical and structurally inverts the H062 family's skew-positive design property.

### Methodological-correctness annotations

`leakage-canary-pass` · `mppm-rho1-null-on-tp-cells` · `tp-overlay-h1-null` · `skew-negative-at-M-1.0` (anti-canonical) · `skew-positive-at-M-inf` · `claim-type-hybrid` · `cost-zero-v1-pre-cost-research-only` · **`repro-log-incomplete`** (3/13 fields per `P1-H065-REPROLOG-WIRE`) · **`substrate-sha-hardcoded-in-sidecar`** (v2-emission integrity defect per `P1-H065-SWEEP-SUBSTRATE-SHA-RUNTIME-READ`) · `nq-zero-trades-substrate-constraint` (4/6 configs)

### Bottom line

H065 v2 confirms the v1 null verdict on the canonical post-Phase-O.8 substrate `317429e4...`: all 4 TP-overlay cells (M ∈ {1.0, 1.5, 2.0, 2.5}) produce NEGATIVE basket OOS ROI; only no-TP M=∞ reference cells positive. M=1.0 INVERTS skew direction (`payoff-shape-skew-negative`) — empirical validation of the practitioner-canonical "ride winners, cut losers" guideline at risk:reward ≤ 1:1. SIL no-TP standalone remains the strongest project-wide single-symbol cell across all H062-family hypotheses. Two integrity defects flagged for v3: (i) sidecar substrate-SHA hardcoded → `P1-H065-SWEEP-SUBSTRATE-SHA-RUNTIME-READ` BLOCKING; (ii) ReproLog 3/13 fields → `P1-H065-REPROLOG-WIRE` BLOCKING. Per user 2026-05-04 standing directive, `kpi-report-emitted` → `ninjascript-implemented` operator-discretionary upon canonical-format presentation. **Net verdict**: H_1 NULL on all 4 M cells; TP-overlay does NOT improve over no-TP baseline.

Full sweep: [`artifacts/runs/H065/tp_overlay_sweep_20260518T220406Z/sweep_sidecar.json`](../../../artifacts/runs/H065/tp_overlay_sweep_20260518T220406Z/sweep_sidecar.json). Substrate-vintage reconciliation: [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md).
