# Audit Trail — H054 Phase 2 (production walk-forward + KPI report card v1)

**Date**: 2026-05-05
**Hypothesis**: H054 — Anti-gate first-hour ORB on CME ES futures
**Phase**: 2 (production walk-forward execution + KPI report card emission)
**Trail scope**: 1 build-defect (Opdyke 2007 API) → clean run → KPI report card v1 emission
**Final run_id**: `dd916fc67b504c528fda7abbde6700f1`
**Final commit**: `66dab5d`
**Verdict**: R2 ACCEPT — 1 build defect remediated inline; 2nd launch clean exit 0; KPI v1 emitted.

## Context

Phase 1 (commit `66dab5d`, PR #3 merged 2026-05-05 21:26 UTC) landed H054 pre-reg + 4 BLOCKING tests + orchestrator + cost model wiring. Phase 2 was the first attempt to execute the orchestrator end-to-end on the post-Cell-I substrate, ES-only 2025 fresh OOS.

## Round-1 — build-defect discovery

### F-Q-1 — SharpeCI attribute access (severity: critical, build)

**Launch 1** (run_id `39922391abf14fc6bd8d0f61a256b5d6`, ~16:55 CT): orchestrator ran through HMM fit + stress-state ID + per-session strategy returns successfully, then aborted at the Opdyke 2007 univariate Sharpe CI step.

**Symptom**: `AttributeError: 'SharpeCI' object has no attribute 'point_estimate'` at [scripts/run_h054_walk_forward.py:655](../../scripts/run_h054_walk_forward.py).

**Diagnosis**: the H054 orchestrator was authored by analogy to H052a's LW2008 differential CI usage (which has a `DifferentialCIResult.point_estimate` field), but the new `opdyke2007_ci` function returns a `SharpeCI` dataclass at [src/skie_ninja/inference/stats/sharpe_ci.py:127-141](../../src/skie_ninja/inference/stats/sharpe_ci.py) with the point-estimate field named `sharpe`, NOT `point_estimate`. This is a narrow API-contract mismatch typical of the H052a Phase 2 build-defect-chain pattern.

**Fix** (this commit; inline): `opdyke_ci.point_estimate` → `opdyke_ci.sharpe`.

```python
# before
opdyke_point = float(opdyke_ci.point_estimate)
# after
opdyke_point = float(opdyke_ci.sharpe)  # SharpeCI.sharpe = point estimate
```

### Launch 2 — clean exit

**Launch 2** (run_id `dd916fc67b504c528fda7abbde6700f1`, 16:55:18 → 17:01:59 CT): clean exit 0 (~6m41s wall-clock).

Headline metrics:
- ES train=736 sessions; test=237 sessions (1 NaN entry-price drop reduces effective from 238 to 237)
- 0 NaN drops on any feature panel
- HMM selected: (full, 3-state); stress_state=2 (highest realized_vol emission)
- Anti-gate fired on 7/237 OOS sessions (2.95% trade rate)
- T_H054_b PRIMARY (Opdyke 2007 univariate CI): SR_anti_gated per-session +0.0362; CI [-0.0327, +0.1050]; covers zero → non-significant null
- T_H054_a SECONDARY (LW2008 differential CI): SR_anti − SR_uncond per-session +0.0398; CI [-0.0411, +0.1394]; covers zero
- Hansen SPA M=1 degenerate: T_SPA = 0.670; p = 0.285
- Realized $10K: anti-gated $10,349.81 (+3.50%); unconditional $9,946.31 (-0.54%)
- Annualised SR: anti-gated +0.573; unconditional -0.057
- Forward 252-session projection: anti-gated median $10,319 (P(loss)=29.24%); unconditional median $9,930 (P(loss)=52.50%)
- Realized max-DD: anti-gated 3.19%; unconditional 6.99%

ReproLog at [logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json](../../logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json); scientific_payload SHA `395dd00877d3b5fae99d9fbbb7bac243d70dd14cd7983ca77b065a14205e3ff4`.

## Round-2 — verification

| Defect | Fix | Closure verified by | Verdict |
|---|---|---|---|
| F-Q-1 (SharpeCI API) | `opdyke_ci.sharpe` substitution | Launch 2 ran through Opdyke 2007 step without error; per-symbol metrics_summary.json populated `t_h054_b_primary` block with `lower`, `upper`, `point_estimate` fields | ✓ closed |

**Round-2 verdict**: ACCEPT. Build defect structurally closed; production walk-forward produced complete, sidecar-correspondent, ReproLog-complete result.

## Round-3 — KPI report card v1 emission

KPI report card v1 emitted at [research/01_hypothesis_register/H054/H054_kpi_report_v1.md](../../research/01_hypothesis_register/H054/H054_kpi_report_v1.md). Stage transition `exploration-in-progress` → `kpi-report-emitted` recorded at [stage.md](../../research/01_hypothesis_register/H054/stage.md). Failure log entries 1-2 at [failure_log.md](../../research/01_hypothesis_register/H054/failure_log.md).

KPI summary:
- **Primary inference (T_H054_b = SR_anti_gated)**: Opdyke 2007 univariate CI [-0.0327, +0.1050] per-session; **CI covers zero → non-significant null** at α=0.05. Point estimate POSITIVE (annualised +0.573); directionally consistent with H_1 + H052a-implied reading.
- **Secondary inference (T_H054_a = SR_anti − SR_uncond)**: LW2008 differential CI [-0.0411, +0.1394] per-session; **CI covers zero**. Point positive (annualised +0.630).
- **Realized $10K outcomes**: anti-gated $10,350 (+3.50%) vs unconditional $9,946 (-0.54%); anti-gate dominates point-estimate.
- **Forward 252-session projection**: anti-gated median $10,319 with P(loss)=29.24% vs unconditional $9,930 with P(loss)=52.50%; **anti-gated dominates on every forward metric**.
- **Methodological-correctness annotations**: all green or n/a + `power-margin-low` declared per design.md §9.5 expectation-management note.

The H054 v1 result is **point-positive AND directionally consistent with H_1 on every metric**, but **CIs cover zero** at α=0.05 due to n_anti = 7 structural underpowering (matches the design.md §9.5 binding expectation: "directional indicator + power-floor probe", NOT a definitive test). Per design.md §10 decision rule, this falls into the "non-significant null" bucket; operator may reasonably decline NinjaScript progression OR pursue an H054 v2 successor with pooled ES+NQ+MES+MNQ to accumulate n_anti to ≥ 174 sessions for adequate power.

## Cross-references

- KPI report card: [H054_kpi_report_v1.md](../../research/01_hypothesis_register/H054/H054_kpi_report_v1.md)
- Stage tracker: [stage.md](../../research/01_hypothesis_register/H054/stage.md)
- Failure log: [failure_log.md](../../research/01_hypothesis_register/H054/failure_log.md)
- Pre-reg: [design.md](../../research/01_hypothesis_register/H054/design.md)
- Pre-reg lit-review: [lit_review_H054_2026-05-05.md](../../research/01_hypothesis_register/H054/lit_review_H054_2026-05-05.md)
- Pre-reg audit trail: [audit_trail_2026-05-05_h054-pre-reg.md](audit_trail_2026-05-05_h054-pre-reg.md)
- Phase 2 sidecar: [artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/sidecar.json](../../artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/sidecar.json)
- Phase 2 ReproLog: [logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json](../../logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json)
- Orchestrator: [scripts/run_h054_walk_forward.py](../../scripts/run_h054_walk_forward.py)
- BLOCKING tests: [tests/integration/test_h054_pit.py](../../tests/integration/test_h054_pit.py)

## Follow-ups (informational; non-blocking)

- `P1-H054-DSR-CELL-DEFLATION-COMPUTE` — compute Bailey-Lopez de Prado deflated Sharpe per F-Q-9 fix annotation (registered but deferred at v1).
- `P1-H054-COST-FLOOR-SENSITIVITY` — re-run with `sensitivity_mult=2.0` on existing artifacts.
- `P1-H054-COST-CALIBRATION-EMPIRICAL` — pre-existing; replace 1-tick prior with regime-wise empirical fit from paper-trade logs.
- `P1-H054-B-ARM-EXECUTE` — run §14 robustness B-arm (frozen H052a HMM via causal warm-start on 2025 OOS).
- `P1-H054-NINJASCRIPT-IMPL` — per ADR-0013 §5; bridge-mediated implementation; operator-discretionary per user's 2026-05-04 standing directive.
- `P1-H054-V2-POOLED-MULTI-INSTRUMENT` — successor v2 design.md to accumulate n_anti ≥ 174 sessions via pooled ES+NQ+MES+MNQ on 2025+ OOS for adequate power per design.md §9.2 derivation.
- `P1-H054-DESIGN-MD-AUDIT-LOOP-R3-ISOLATED-AGENT` — recommended-but-non-blocking isolated-agent R3 verification on the pre-reg before any v2 launch.
- `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR` — pre-existing; deferred from F-Q-5 fix.
