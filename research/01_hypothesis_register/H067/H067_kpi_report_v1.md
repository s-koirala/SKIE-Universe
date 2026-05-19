---
hypothesis_id: H067
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-19
git_head: 525bad069e2808d6d5d01527ab2be63550735467
substrate_dataset_checksum: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_path: artifacts/runs/H067/ade85c4b74dd4c64aecba3b30821caed/sidecar.json
sidecar_scientific_payload_sha256: 90539e711f30c98a73de24317a42af5f213178a423dfd9ed0689fb1292848931
simulation_log_sha256: TBD on commit (covered by ReproLog 13-field record at logs/reproducibility/ade85c4b74dd4c64aecba3b30821caed.json)
simulation_script_sha256: see sidecar.script_sha256 field (runtime-computed at execution)
run_id: ade85c4b74dd4c64aecba3b30821caed
sizing_convention: per_trade_atr_stop_5min_intraday_SIL_log_return
supersedes: H067_kpi_report_v0.md
superseded_by: null
parent_hypothesis_id: H065
parent_hypothesis_kpi: H065_kpi_report_v2.md
cost_model_v1_scope: two_cost_arm_A0_zero_A1_conservative_prior
post_run_audit_trail: docs/audits/audit_trail_2026-05-19_h067-v1-walk-forward-post-run.md
---

# H067 — KPI Report Card v1

> **H067 v1 production walk-forward** on canonical post-Phase-O.10 substrate `317429e4...`; 60-cell N-lot × Kelly × cost-arm sweep on SIL standalone (2020-01-01 → 2026-05-15 OOS). Per H067 design.md §1 H_1: there exists `N* ∈ {1, 2, 3, 4, 5}` such that **simultaneously** (a) realized SIL OOS ROI > 0 at conservative_prior AND (b) basket MPPM(ρ=1) CI strictly excludes zero positively AND (c) cost-friction-breakeven ratio ≥ 2 (`cost-friction-dominated-edge-present` per ADR-0028 §D-2). **VERDICT: H_1 NULL on all 5 N-cells at conservative_prior** — confirms the H067 design.md §1.4 + §6 + §17 (Phase O.16 amendment) structural prediction that under linear-scaling cost model, N-lot mechanism cannot recover the H065 v2 M_inf-SIL parent ratio (0.955 sub-breakeven) above the ≥ 2 threshold. **The H067 v1 emission is the canonical-instance ADR-0027 §D-3 finding**: the H067 R1 audit (Phase O.15) caught the N-lot mechanism error in design.md §6 BEFORE the empirical run; this run is the after-the-fact empirical confirmation that the mechanism doesn't recover.

- **Hypothesis** (per [design.md §1](design.md)): cost-light Donchian channel-breakout on SIL standalone, with N-lot grid `{1, 2, 3, 4, 5}` as primary cost-reduction axis; genetic successor of [H065 v2 M_inf-SIL cell](../H065/H065_kpi_report_v2.md).
- **Stage**: `kpi-report-emitted` per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1. v0 (pre-emission skeleton) → v1 stage transition recorded in [stage.md](stage.md).
- **Cost model**: two-arm v1 per ADR-0028 §D-2 — **A0** = `cost-zero` (ADR-0025 §D-5 zero-cost reference); **A1** = `cost-conservative-prior` via `nt8_realistic_v1` at `sensitivity_mult=1.0` per [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py). SIL fees per Phase O.16 verified CME 2025-02-01 schedule: $1.87/side fixed (= $0.85 commission + $1.00 exchange + $0.02 NFA) + $5.00/side slip at 1-tick prior = $6.87/side × 2 sides × N-lot.
- **Universe**: SIL standalone (1 symbol; 12 partitions on canonical substrate; 2015-01-01 → 2026-05-15 coverage; OOS 2020-01-01 → 2026-05-15).
- **Cell-budget**: 60 cells (5 N × 6 Kelly × 2 cost-arm) per ADR-0027 §D-2 declaration; well under v1 cap of 1000.
- **Sample size**: 438,979 5-min bars × 1,978 sessions. A0 cells: 5,600-5,686 trades. A1 cells: 808-1,922 trades (post-cost-drag reduction).
- **Run provenance**: run_id `ade85c4b74dd4c64aecba3b30821caed`; sidecar SHA `90539e711f30c98a73de24317a42af5f213178a423dfd9ed0689fb1292848931`; ReproLog 13-field schema at [logs/reproducibility/ade85c4b74dd4c64aecba3b30821caed.json](../../../logs/reproducibility/ade85c4b74dd4c64aecba3b30821caed.json); substrate SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json).

## 0. End-of-simulation 3-component summary header (per ADR-0026 §D-1; effective 2026-05-19)

Per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md): the 3-component summary header consists of a single per-cell × per-cost-arm × component table. H067 v1 reports the **two parent-cell anchors** (N=1 A0 zero-cost reference + N=1 A1 conservative_prior) plus the **best A0 cell** (N=3) + **least-negative A1 cell** (N=1) per the H_1 §1 ranking. Forward q05 deferred to `P1-H067-FORWARD-PROJECTION-COMPUTE` (non-blocking).

### Component 1 — Realized OOS (full): 2020-01-01 → 2026-05-15 (1,978 sessions)

| Cell | A0 ROI% | A0 Max-DD% | A0 W/L/Z | A0 MPPM pt | A1 ROI% | A1 Max-DD% | A1 W/L/Z | A1 MPPM pt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **N=1 (parent baseline)** | **+734.68%** | 64.84% | 1,142/4,422/36 | +0.282 | **−79.81%** | 90.02% | 327/1,595/0 | −0.436 |
| **N=2** | +1,052.12% | 71.35% | 1,156/4,492/36 | +0.323 | −91.54% | 92.54% | 164/751/0 | −1.417 |
| **N=3 (best A0)** | **+1,217.49%** | 67.16% | 1,157/4,493/36 | **+0.340** | −94.68% | 98.77% | 210/938/0 | −1.540 |
| **N=4** | +948.71% | 72.09% | 1,157/4,493/36 | +0.310 | −96.59% | 99.30% | 179/783/0 | −2.241 |
| **N=5 (ADR-0001 ceiling)** | +920.32% | 75.07% | 1,157/4,493/36 | +0.307 | −97.39% | 99.28% | 147/661/0 | −2.843 |

### Component 2 — Realized OOS (2026-onward sub-window): 2026-04-01 → 2026-05-15 (~30 sessions)

| Cell | A0 sub-ROI% | A0 sub-Max-DD% | A1 sub-ROI% | A1 sub-Max-DD% |
|---|---:|---:|---:|---:|
| N=1 | −0.05% | 22.18% | +0.00% | 0.00% (zero sub-window trades; A1 bankroll already at floor) |
| N=2 | +1.98% | 42.17% | +0.00% | 0.00% (zero sub-window trades) |
| N=3 | +15.48% | 43.24% | +0.00% | 0.00% (zero sub-window trades) |
| N=4 | +19.30% | 53.14% | +0.00% | 0.00% (zero sub-window trades) |
| N=5 | +19.39% | 54.67% | +0.00% | 0.00% (zero sub-window trades) |

**Critical sub-window observation**: A1 cells produce **ZERO sub-window trades** across all 5 N values. The conservative_prior cost-drag drives equity to ~$200-$2,000 by the start of the 2026-04-01 sub-window, and the position-size floor at `risk_budget_pct × current_equity / dollar_1r_per_contract` clips entries to 0 contracts. The A1 path is structurally inactive in the recent window.

### Component 3 — Forward 1-year bootstrap projection (252-session MC per ADR-0013 §3.1)

Deferred to `P1-H067-FORWARD-PROJECTION-COMPUTE` (non-blocking; the H_1 verdict is structurally null at A1 under conservative_prior, making forward projection of the dominant A1 cell uninformative).

## End-of-simulation results summary (per ADR-0014 §3.2 + ADR-0017 §3.2 + ADR-0019 Table 1c; 13 mandatory tables + bottom-line prose)

Per ADR-0014 §3.2 — 13 tables; values are a RE-PRESENTATION of figures already in §"Per-cell sweep results" — they MUST NOT introduce new KPI values. The full per-cell numeric table is preserved at [`artifacts/runs/H067/ade85c4b74dd4c64aecba3b30821caed/kpi_table.txt`](../../../artifacts/runs/H067/ade85c4b74dd4c64aecba3b30821caed/kpi_table.txt) and in the sidecar's `kpi_table_text` + `per_cell_results` blocks.

### Table 1 — P/L (realized OOS, $10K starting capital)

A0 (zero-cost reference):

| N-lot | Start equity | End equity | ROI% | Trade count |
|---:|---:|---:|---:|---:|
| 1 | $10,000 | $83,468 | +734.68% | 5,600 |
| 2 | $10,000 | $115,212 | +1,052.12% | 5,684 |
| 3 | $10,000 | $131,749 | **+1,217.49%** ← best A0 | 5,686 |
| 4 | $10,000 | $104,871 | +948.71% | 5,686 |
| 5 | $10,000 | $102,032 | +920.32% | 5,686 |

A1 (conservative_prior):

| N-lot | Start equity | End equity | ROI% | Trade count |
|---:|---:|---:|---:|---:|
| 1 | $10,000 | $2,019 | **−79.81%** ← least-negative A1 | 1,922 |
| 2 | $10,000 | $846 | −91.54% | 915 |
| 3 | $10,000 | $532 | −94.68% | 1,148 |
| 4 | $10,000 | $341 | −96.59% | 962 |
| 5 | $10,000 | $261 | −97.39% | 808 |

### Table 1c — Payoff-shape diagnostics (per ADR-0019)

| N-lot | A0 τ_3 | A0 payoff-shape | A1 τ_3 | A1 payoff-shape |
|---:|---:|---|---:|---|
| 1 | +0.759 | skew-positive | +0.717 | skew-positive |
| 2 | +0.759 | skew-positive | +0.699 | skew-positive |
| 3 | +0.759 | skew-positive | +0.696 | skew-positive |
| 4 | +0.759 | skew-positive | +0.689 | skew-positive |
| 5 | +0.759 | skew-positive | +0.692 | skew-positive |

L-skewness preserved across cost-arms — confirms the H067 design.md §1.3 prediction that **the Donchian channel-breakout payoff distribution is per-trade-unit shape-invariant under linear position-size scaling**. The barbell payoff structure of the H065 parent is preserved in H067; the issue is NOT shape inversion (vs. H065 M=1.0 TP-overlay which DID invert skew), it is mean-edge insufficiency relative to cost burden. Annotation: `payoff-shape-skew-positive` on every cell.

### Table 2 — Drawdown (realized + projected)

| N-lot | A0 Max-DD% | A1 Max-DD% |
|---:|---:|---:|
| 1 | 64.84% | 90.02% |
| 2 | 71.35% | 92.54% |
| 3 | 67.16% | 98.77% |
| 4 | 72.09% | 99.30% |
| 5 | 75.07% | 99.28% |

A0 max-DD grows with N (64% → 75%); A1 max-DD approaches 99% by N=4 (near-complete bankroll loss). Forward bootstrap-projection deferred per `P1-H067-FORWARD-PROJECTION-COMPUTE`.

### Table 3 — Primary inference (T = MPPM(ρ=1) per design.md §1; stationary-bootstrap CI; excludes-zero column)

| N-lot | A0 MPPM pt | A0 MPPM 95% CI | A0 excl. zero | A1 MPPM pt | A1 MPPM 95% CI | A1 excl. zero |
|---:|---:|---|:---:|---:|---|:---:|
| 1 | +0.282 | [−0.110, +0.718] | **no** (covers zero) | −0.436 | [−1.193, +0.366] | no (covers zero) |
| 2 | +0.323 | [−0.185, +0.815] | **no** | −1.417 | [−3.288, +0.525] | no |
| 3 | +0.340 | [−0.187, +0.893] | **no** | −1.540 | [−4.130, +1.255] | no |
| 4 | +0.310 | [−0.267, +0.916] | **no** | −2.241 | [−5.567, +1.902] | no |
| 5 | +0.307 | [−0.312, +0.942] | **no** | −2.843 | [−8.123, +2.249] | no |

**Primary inferential verdict**: H_1 §1(b) FAILS on all 5 N-cells × both cost arms. Even at zero-cost A0, the MPPM CI covers zero (lower bound −0.11 to −0.31). At conservative_prior A1, the MPPM CI also covers zero (very wide range due to small post-cost-drag sample size). **Per design.md §1: H_1 NULL.**

CI primitive: stationary-bootstrap percentile per Politis-Romano 1994 + Politis-White 2004 block-length selection via [`mppm_with_ci`](../../../src/skie_ninja/inference/mppm.py); n_bootstrap=1,000; rng_seed=20260519.

### Table 3a — Terminal-wealth q05 (per ADR-0017 §3.2)

| N-lot | A0 realized end | A1 realized end | A1 q05 forward (deferred) |
|---:|---:|---:|---:|
| 1 | $83,468 | $2,019 | deferred to `P1-H067-FORWARD-PROJECTION-COMPUTE` |
| 2 | $115,212 | $846 | deferred |
| 3 | $131,749 | $532 | deferred |
| 4 | $104,871 | $341 | deferred |
| 5 | $102,032 | $261 | deferred |

A1 realized end-equity below half of starting ($5K threshold) on all 5 cells. Annotation: `tw-q05-below-half` per ADR-0017 §3.2 grammar (best-case under conservative_prior; if anything, the forward projection would worsen).

### Table 3b — Calmar-differential (per ADR-0017 §3.2)

| N-lot | A0 Calmar | A1 Calmar |
|---:|---:|---:|
| 1 | +0.504 | −0.393 |
| 2 | +0.534 | −0.819 |
| 3 | **+0.604** ← best A0 | −0.795 |
| 4 | +0.505 | −0.900 |
| 5 | +0.478 | −0.949 |

Differential-vs-passive-long SIL benchmark + bootstrap CI deferred to `P1-H067-CALMAR-DIFFERENTIAL-VS-PASSIVE-CI` (non-blocking). Annotation: `calmar-diff-negative` for all A1 cells; `calmar-diff-marginal-to-positive` for A0 cells.

### Table 3c — Profit-factor + R-multiple-mean (per ADR-0017 §3.2)

| N-lot | A0 PF | A0 R-mean | A1 PF | A1 R-mean |
|---:|---:|---:|---:|---:|
| 1 | 1.05 | +0.093 | 0.94 | −0.058 |
| 2 | 1.05 | +0.088 | 0.90 | −0.009 |
| 3 | 1.05 | +0.088 | 0.97 | −0.018 |
| 4 | 1.04 | +0.088 | 0.97 | −0.022 |
| 5 | 1.04 | +0.088 | 0.96 | +0.012 |

A0 PF marginally above 1.0 (1.04-1.05); A1 PF marginally below 1.0 (0.90-0.97). A0 R-mean consistently +0.088-0.093 (below the +0.5 Tharp 1998 *practitioner* canonical-edge threshold). A1 R-mean near zero on all N values. R-multiple CI bootstrap deferred to `P1-H067-R-MULTIPLE-MEAN-CI-EMIT` (sidecar contains the CI bounds per cell). Annotation: `r-multiple-mean-marginal` on A0; `r-multiple-mean-negative-marginal` on A1.

### Table 4 — Annualised Sharpe (annualisation factor √252)

| N-lot | A0 Sharpe ann | A1 Sharpe ann |
|---:|---:|---:|
| 1 | 0.488 | −0.605 |
| 2 | 0.457 | −1.094 |
| 3 | 0.460 | −0.772 |
| 4 | 0.371 | −0.976 |
| 5 | 0.340 | −0.947 |

A0 Sharpe annualised mildly positive (0.34-0.49); A1 Sharpe annualised strongly negative. LW2008 differential CI vs passive-long benchmark deferred to `P1-H067-LW2008-VS-PASSIVE-LONG-CI` (non-blocking; secondary KPI per ADR-0017 §1.2 demotion machinery). Annotation: `sharpe-vs-passive-long-marginal` on A0; `sharpe-vs-passive-long-negative` on A1.

### Table 5 — Win/Loss/Zero counts + win rate W/(W+L+Z)

| N-lot | A0 W/L/Z | A0 win rate | A1 W/L/Z | A1 win rate |
|---:|---:|---:|---:|---:|
| 1 | 1,142/4,422/36 | 20.4% | 327/1,595/0 | 17.0% |
| 2 | 1,156/4,492/36 | 20.3% | 164/751/0 | 17.9% |
| 3 | 1,157/4,493/36 | 20.3% | 210/938/0 | 18.3% |
| 4 | 1,157/4,493/36 | 20.3% | 179/783/0 | 18.6% |
| 5 | 1,157/4,493/36 | 20.3% | 147/661/0 | 18.2% |

Win rate stable at ~20% across cells (consistent with Donchian-channel-breakout convention: ~20% wins × R-multiple-mean ~+0.5 = expectancy +0.1R per Tharp 1998 *practitioner*; H067 R-mean actually ~+0.09 → mean-edge marginal-but-positive at zero-cost).

### Table 6 — Forward 1-year projection (Median + q05/q95 + P(loss)/P(double)/P(<50%))

Deferred to `P1-H067-FORWARD-PROJECTION-COMPUTE` (non-blocking). Per design.md §1 H_1 §1(b) FAILS at A1 on all 5 N-cells; forward-projection on the dominant A1 cell would project median bankroll near $0 (degenerate; uninformative). Forward-projection on A0 cells emits the zero-cost upper-bound reference per ADR-0028 §D-2 (deferred to follow-up; sidecar contains the data to compute).

### Table 7 — Hansen SPA family p-value (KPI annotation per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md))

Family size = 60 cells (5 N × 6 Kelly × 2 cost-arm) per design.md §1 + §5.2. **Note**: per F1-Q-2 audit finding ([docs/audits/audit_trail_2026-05-19_h067-v1-walk-forward-post-run.md](../../../docs/audits/audit_trail_2026-05-19_h067-v1-walk-forward-post-run.md)), Kelly multiplier is structurally invariant within N-lot cells under the H067 v1 simulator (Kelly is a hyperparameter at inner-CV selection only per the H062 v1 convention inherited verbatim). **Effective distinct family size = 5 N-cells × 2 cost-arm = 10**.

DSR deflation per [Bailey-López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094): activation_size = 10 from [config/gate.yaml](../../../config/gate.yaml); 10 effective cells ≥ activation threshold → DSR deflation MANDATORY at v1. Computed bound:

Per design.md §8: "DSR deflation per Bailey-López de Prado 2014 MANDATORY per ADR-0027 §D-2 since realized cell count 30 ≥ project's dsr_activation_size = 10." Compute deferred to `P1-H067-DSR-DEFLATION-COMPUTE` (non-blocking; the H_1 verdict is null on the un-deflated CI; deflation can only widen the CI further toward null). Annotation: `dsr-mandatory-not-yet-computed` with the follow-up registered.

Hansen 2005 SPA p computation deferred to `P1-H067-HANSEN-SPA-COMPUTE` (non-blocking; KPI annotation only per ADR-0024 §D-1 no-binding-gates discipline). Annotation: `dsr-mandatory-not-yet-computed` + `hansen-spa-deferred`.

### Table 8 — Other KPIs (cell-conditional annotations)

| KPI | SIL |
|---|---|
| Best N-lot cell per A0 ROI | **N=3** at +1,217.49% / max-DD 67.16% / MPPM +0.340 [−0.187, +0.893] |
| Best N-lot cell per A1 ROI | **N=1** at −79.81% / max-DD 90.02% (least catastrophic) |
| Best Kelly-multiplier per fold | N/A — Kelly structurally invariant within N-cell (F1-Q-2 audit finding) |
| n_folds (realized/expected) | N/A — sweep emission, not walk-forward CV; full walk-forward deferred to `P1-H067-FULL-WALK-FORWARD-V2` |
| max-DD annotation | `max-dd-adverse` on A0 (65-75%); `max-dd-catastrophic` on A1 (90-99%) per ADR-0014 §3.2 grammar |
| Sharpe-vs-passive-long annotation | `sharpe-vs-passive-long-marginal` (A0); `sharpe-vs-passive-long-negative` (A1) — LW2008 CI deferred |
| Cost model | `nt8_realistic_v1` × {A0 zero-cost, A1 conservative_prior} → `cost-zero` AND `cost-conservative-prior` per ADR-0025 §D-5 (2 cost arms per ADR-0028 §D-2) |
| Cost-friction-breakeven ratio (per ADR-0028 §D-2 + cross-hyp inv §2 schema) | **N=1: 0.769** ; **N=2: 0.592** ; **N=3: 0.807** ; **N=4: 0.810** ; **N=5: 0.770** — all sub-breakeven at sensitivity_mult=1.0 |
| Cost-friction-dominated-edge annotation | **`cost-friction-dominated-edge-present`** on all 5 N-lot pairs (A0 ROI positive AND A1 ROI negative AND ratio sub-2.0) per ADR-0028 §D-2 trigger semantics |
| Sortino / turnover / capacity | Sortino deferred to `P1-H067-SORTINO-COMPUTE`; turnover at N=5 reaches ~5,686 trades/year on $10K (excessive at retail); capacity remains within ADR-0001 SIL ≤ 5 ceiling on all N |
| Kill-switch runtime (ADR-0025 §D-1) | `kill-switch-active` (K-4 + K-6 + K-7 enabled at v1; K-3 vacuous; runtime did NOT trip K-6/K-7 enforcement at A0 cells but did trip on A1 cells — see runtime block in sidecar) |
| Kill-switch enforcement-mode (ADR-0028 §D-4) | `kill-switch-mode-block` (v1 default per design.md §11.1) |
| BOCD live-pause (ADR-0025 §D-4) | `bocd-live-inactive` (v1 deferred per `P1-BOCD-LIVE-PRIOR-CALIBRATION-H067-V3`) |
| Equity rebase (ADR-0025 §D-2) | mode=`current` per design.md §5 (H065 v2 modal parent cell preservation) |
| Promising-* annotation (ADR-0026 §D-3) | **`not-promising-mppm-cost-conservative-prior-317429e49ad63674`** on all 5 A1 cells (MPPM CI does NOT strictly exclude zero positively); **`not-promising-mppm-cost-zero-317429e49ad63674`** on all 5 A0 cells (even zero-cost MPPM CI covers zero on lower bound) |
| Causal-mechanism annotation (ADR-0022) | `causal-mechanism-hybrid` per design.md §1.3 (channel-break-as-information-event upstream + correlation-only N-lot refinement) |

### Cost-friction-breakeven sensitivity table (per design.md §6 binding; operator-actionable diff)

Per H067 design.md §6 mandatory sensitivity exhibit: cost-friction-breakeven ratio under sensitivity_mult ∈ {1.0, 0.5, 0.0}. Operator-actionable diff between conservative_prior and empirical-slip-reduction-needed-to-clear-threshold.

| N-lot | sens=1.0 (baseline) ratio | sens=0.5 (50% slip cut) ratio | sens=0.0 (zero-slip; commission-only) ratio |
|---:|---:|---:|---:|
| **1** | **0.769** | 1.210 | 2.827 |
| 2 | 0.592 | 0.930 | 2.173 |
| 3 | 0.807 | 1.269 | 2.966 |
| 4 | 0.810 | 1.274 | 2.977 |
| 5 | 0.770 | 1.211 | 2.830 |

**Critical operator-actionable diagnostic** (per design.md §6 + cross-hyp inv §7.2):
- At sensitivity_mult=1.0 (current conservative_prior baseline): all 5 N-cells **BELOW** the ratio ≥ 2 threshold for `cost-friction-dominated-edge-present`. H_1 §1(c) FAILS on all cells.
- At sensitivity_mult=0.5 (50% empirical slip cut anchored on practitioner anecdote of liquid retail futures; cross-hyp inv §7.2): N-cells reach **ratio 0.93-1.27**. Still BELOW the ≥ 2 threshold. **50% slip cut is INSUFFICIENT.** H_1 §1(c) still FAILS.
- At sensitivity_mult=0.0 (zero-slip; commission-only sensitivity bound; physically unachievable but bounds the maximum): N-cells reach **ratio 2.17-2.98**. ABOVE the ≥ 2 threshold but this requires 100% slip elimination which is empirically impossible.

**The H067 v1 conservative_prior emission demonstrates structurally** that the H065 parent cell at SIL is mean-edge-insufficient relative to retail-tier cost burden EVEN if the slip component is halved. The operator-actionable forward path per design.md §17 is `P1-H067-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED stage transition); the empirical evidence at conservative_prior + 50% slip reduction is INSUFFICIENT to lift the cell to promotable.

### Table 9 — Methodological-correctness annotations (one-line per ADR-0013 §2 + §2.1 + ADR-0028 §D-4)

`leakage-canary-pass` · `mppm-rho1-marginal-A0` (CI covers zero) · `mppm-rho1-negative-A1` · `bss-n/a` · `reliability-n/a` · `repro-log-complete` · `dsr-mandatory-not-yet-computed` (`P1-H067-DSR-DEFLATION-COMPUTE`) · `post-run-audit-pass` · `kill-switch-active` · `kill-switch-mode-block` · `bocd-live-inactive` · `cost-{zero, conservative-prior}` (2-arm per ADR-0028 §D-2) · `cost-friction-dominated-edge-present` (per N-cell × A1 pair per ADR-0028 §D-2 trigger semantics) · `causal-mechanism-hybrid` · `payoff-shape-skew-positive` · `not-promising-mppm-cost-conservative-prior-317429e49ad63674` · `not-promising-mppm-cost-zero-317429e49ad63674` (even A0 marginal at MPPM CI)

### Bottom line

H067 v1 NULL on all 5 N-cells: the N-lot mechanism does NOT recover the H065 v2 M_inf-SIL parent cell's sub-breakeven ratio (0.955 post-Phase-O.16) under the canonical conservative_prior linear-scaling cost model — empirically confirming the design.md §1.4 + §6 + §17 structural prediction. Realized OOS A0 (zero-cost) ranges +734.68% to +1,217.49% across N ∈ {1, 2, 3, 4, 5} on 5,600-5,686 trades each; A1 (conservative_prior) catastrophic at −79.81% to −97.39% (best N=1 least-catastrophic). Cost-friction-breakeven ratio bounded [0.59, 0.81] at sensitivity_mult=1.0 across all N — invariant under N-lot scaling per the design.md §6 linear-scaling prediction. Sensitivity analysis: 50% empirical slip cut INSUFFICIENT to clear ratio ≥ 2 (lifts to 0.93-1.27); only zero-slip bound (physically unachievable) clears (2.17-2.98). The H067 v1 emission is the canonical-instance ADR-0027 §D-3 finding: the R1 design audit caught the N-lot mechanism error BEFORE the empirical run; this v1 run is the after-the-fact empirical confirmation. **Per the user 2026-05-04 standing decline-ninjascript directive + the H_1 null verdict, `kpi-report-emitted` → `ninjascript-implemented` is operator-deferred**: the empirical evidence does not support a forward path to NinjaScript implementation at the current cost calibration. The forward research path per design.md §17 is paper-trade-empirical slip calibration to break the 0.955 sub-breakeven barrier; tracked under `P1-H067-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` BLOCKING-BEFORE-PAPER-TRADE-EVALUATED.

Full sweep: [`artifacts/runs/H067/ade85c4b74dd4c64aecba3b30821caed/`](../../../artifacts/runs/H067/ade85c4b74dd4c64aecba3b30821caed/). Post-run audit trail: [`docs/audits/audit_trail_2026-05-19_h067-v1-walk-forward-post-run.md`](../../../docs/audits/audit_trail_2026-05-19_h067-v1-walk-forward-post-run.md). Pre-registration audit trail (Phase O.15): [`docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md`](../../../docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md).

## Empirical findings (descriptive; not part of the H_1 inferential test)

1. **N-lot mechanism failure mechanism — confirmed**: under linear-scaling cost (commission × N_contracts + slip × N_contracts), per-trade gross-edge bps-of-equity AND per-trade cost bps-of-equity both scale linearly with N. Ratio invariance is the expected outcome. The observed mild ratio drift across N (0.59-0.81) reflects trade-mix composition shifts as the current-equity rebase eliminates partial entries under cost-drag, not a true cost-amortization effect.

2. **Unanticipated current-equity-rebase × cost-drag interaction**: at A1 conservative_prior, trade count drops from 1,922 (N=1) to 808 (N=5) — a 58% reduction. As cost drag shrinks equity, the position-size floor at `risk_budget_pct × current_equity / dollar_1r_per_contract` drops to 0 contracts more frequently, eliminating entries. This was NOT documented in design.md §1.4 pre-empirical caveat; recorded for v2 cycle interpretation under `P1-H067-V2-TRADE-FREQUENCY-INVESTIGATE` (non-blocking).

3. **Kelly multiplier structurally invariant**: per F1-Q-2 audit finding, the Kelly grid {0.25..2.5} is not exercised at the per-trade-sizing layer (`size_from_risk = risk_budget × equity / dollar_1r`; Kelly NOT multiplied). All 6 Kelly cells within an N-cell produce bit-identical results. Effective distinct family size = 10 (5 N × 2 cost-arm), NOT 60. The H067 §5.3 declaration preserves the Kelly grid per ADR-0018 D-2 design.md binding completeness; v2 cycle (`P1-H067-FULL-INNER-CV-GRID-V2`) wires Kelly into per-trade scaling.

4. **L-skewness preserved across cost-arms** — τ_3 stable at +0.69-+0.76 on all cells (A0 + A1); the barbell payoff structure of the H065 M_inf-SIL parent is preserved under N-lot scaling. The H067 failure is NOT a shape inversion (vs H065 M=1.0 TP overlay which DID invert skew); it is mean-edge insufficiency.

5. **Best A0 cell = N=3 (+1,217.49% / max-DD 67.16% / MPPM +0.340 [−0.187, +0.893])**. Operator-recommended reference cell for cross-hypothesis investigation 2026-05-19 §7 follow-on candidates: this cell anchors a 1,217% pre-cost upper bound for any SIL Donchian-channel-breakout variant. The conservative_prior cost-drag converts this to −94.68%; a paper-trade-empirical calibration cycle (`P1-H067-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION`) is the only forward path to evaluate whether sub-conservative-prior slip-reduction can lift any cell to positive realized OOS.

## Cross-references

- [Design: H067 design.md](design.md) (frozen at status=designed Phase O.15 commit f71a6df; §17 Phase O.16 amendment for parent ratio recalibration; §1-§7 IMMUTABLE per ADR-0013)
- [Data requirements: H067 data_requirements.md](data_requirements.md) + [SIL per-partition SHA enumeration: _sil_substrate_partitions.json](_sil_substrate_partitions.json) (12 partitions; 1,997,220 SIL rows total on canonical substrate)
- [Lit review: H067 lit_review_H067_2026-05-19.md](lit_review_H067_2026-05-19.md)
- [Stage tracker: stage.md](stage.md)
- [Failure log: failure_log.md](failure_log.md) (2 build-defect entries from launch sequence)
- [Pre-registration audit trail (Phase O.15): docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md](../../../docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md)
- [Post-run audit trail: docs/audits/audit_trail_2026-05-19_h067-v1-walk-forward-post-run.md](../../../docs/audits/audit_trail_2026-05-19_h067-v1-walk-forward-post-run.md)
- [Parent hypothesis H065 design.md](../H065/design.md) + [H065 KPI v2](../H065/H065_kpi_report_v2.md)
- [Cross-hypothesis investigation 2026-05-19 + Phase O.16 addendum](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md)
- [H062 v3 ablation precedent](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- [Sweep script: scripts/run_h067_n_lot_sweep.py](../../../scripts/run_h067_n_lot_sweep.py)
- [PIT canary integration test: tests/integration/test_h067_pit_canaries.py](../../../tests/integration/test_h067_pit_canaries.py)
- [Sidecar + KPI table: artifacts/runs/H067/ade85c4b74dd4c64aecba3b30821caed/](../../../artifacts/runs/H067/ade85c4b74dd4c64aecba3b30821caed/)
- [ReproLog: logs/reproducibility/ade85c4b74dd4c64aecba3b30821caed.json](../../../logs/reproducibility/ade85c4b74dd4c64aecba3b30821caed.json)

## Paradigm stack

ADR-0001 + ADR-0008 + ADR-0013 + ADR-0014 + ADR-0017 + ADR-0018 + ADR-0019 + ADR-0020 + ADR-0022 + ADR-0023 + ADR-0024 + ADR-0025 + ADR-0026 + ADR-0027 + ADR-0028.
