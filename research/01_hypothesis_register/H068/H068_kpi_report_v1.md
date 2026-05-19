---
hypothesis_id: H068
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-19
git_head: 525bad069e2808d6d5d01527ab2be63550735467
substrate_dataset_checksum: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_scientific_payload_sha256: a5bce59880e0dd5d824a5b4fd6d7ef7db1df80f05599dc34744f0d26b59ca714
simulation_log_sha256: a5bce59880e0dd5d824a5b4fd6d7ef7db1df80f05599dc34744f0d26b59ca714
simulation_script_sha256: scripts/run_h068_sensitivity_sweep.py @ git_head
run_id: 957643d6cb8441e29d888482447ead6e
sizing_convention: per_trade_atr_stop_5min_intraday_ES_log_return_fixed_equity_rebase
supersedes: H068_kpi_report_v0.md
superseded_by: null
parent_hypothesis_id: H065
parent_hypothesis_kpi: H065_kpi_report_v2.md
---

# H068 — KPI Report Card v1

- **Hypothesis**: Cost-light Donchian channel-breakout on ES standalone, with sub-1-tick slip empirical sensitivity sweep `sensitivity_mult ∈ {0.25, 0.5, 1.0}` ticks as primary cost-reduction axis. Genetic successor of [H065 v2 M_inf_h062_v1_fixed-ES cell](../H065/H065_kpi_report_v2.md) per cross-hypothesis investigation 2026-05-19 addendum §3 row #1. Primary inferential test: per-slip-cell ES OOS realized ROI > 0 under conservative_prior AND MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero positively AND cost-friction-breakeven ratio ≥ 2 (`cost-friction-dominated-edge-present` per ADR-0028 §D-2).
- **Design.md**: [design.md](design.md) (frozen at `status: designed` 2026-05-19 commit `15a569b` per CLAUDE.md Phase O.17 ledger).
- **Stage**: `kpi-report-emitted` (transition from `exploration-in-progress` recorded in [stage.md](stage.md)).
- **Stage-tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)
- **Parent hypothesis**: [H065 design.md](../H065/design.md) + [H065 KPI v2](../H065/H065_kpi_report_v2.md). H068 v1 inherits feature configuration verbatim (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; M=∞ no TP overlay; fixed-equity rebase per H062 v1 modal); adds slip-sensitivity sweep as the single genetic-cross axis per ADR-0027 §D-4.
- **Empirical anchor**: cross-hypothesis investigation 2026-05-19 addendum §3 row #1 (parent cell breakeven ratio = 1.266; H065 v2 M_inf_h062_v1_fixed-ES standalone 110 trades; ES fees CME-verified effective 2024-02 unchanged through Phase O.16).
- **H_1 conjunctive verdict (per design.md §1)**: **NULL on all 3 slip cells**. Detail in §8 Inferential verdict. The pre-empirical structural prediction at sensitivity_mult=0.5 (ratio ≈ 2.22 just crosses ADR-0028 §D-2 threshold; design.md §1.4) was **EMPIRICALLY VERIFIED** at realized ratio = **2.278** (within 0.058 of prediction). Conjunctive H_1 fails on criterion (b) MPPM CI excludes zero positively — n_trades=108 yields CIs too wide to clear zero despite the structural cost-reduction working as predicted.

## 0. End-of-simulation 3-component summary header (per ADR-0026 §D-1)

Per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) §0 mandatory 3-component summary header preceding the ADR-0014 §3.2 13-table format.

H068 v1 ES standalone (no basket; "basket" = ES). Per-slip-cell × per-Kelly × per-cost-arm. Component-1 (Realized OOS full 2020-01-01 → 2026-05-15 walk-forward equivalent across all signal-generating bars) is the primary inferential window per design.md §2; Component-2 (Realized OOS 2026-onward sub-window 2026-04-01 → 2026-05-15) is mandatory per ADR-0026 §D-1; Component-3 (Forward 1-year bootstrap) is preserved as PLACEHOLDER per `P1-H068-FORWARD-PROJECTION-COMPUTE` (sample-size constrained at n_trades=108 below the 252-session bootstrap saturation point).

**Per-slip × modal-Kelly=0.25 cell summary** (per design.md §8 Pareto-front operator-deliverable load-bearing reference; full 36-cell matrix in §"Performance KPIs"):

| Sensitivity_mult | Cost arm | Component | Window | P/L % | Max-DD % | Win rate W/(W+L+Z) | MPPM(ρ=1) point | MPPM CI [low, high] | excludes 0 | N (trades) |
|---:|---|---:|---|---:|---:|---|---:|---|:--:|---:|
| 0.25 | A0 zero-cost | 1 Realized OOS full | 2020-01-01 → 2026-05-15 | **+41.21%** | 15.18% | 11/(11+96+1) = 10.18% | +0.935 | [-0.799, +3.283] | NO | 108 |
| 0.25 | A0 zero-cost | 2 Realized OOS (2026-onward) | 2026-04-01 → 2026-05-15 | 0.00% | 0.00% | 0/0 | n/a | n/a | n/a | 0 |
| 0.25 | A1 conservative-prior | 1 Realized OOS full | 2020-01-01 → 2026-05-15 | **+29.93%** | 17.77% | 11/(11+97+0) = 10.19% | +0.709 | [-1.103, +3.145] | NO | 108 |
| 0.25 | A1 conservative-prior | 2 Realized OOS (2026-onward) | 2026-04-01 → 2026-05-15 | 0.00% | 0.00% | 0/0 | n/a | n/a | n/a | 0 |
| 0.50 | A0 zero-cost | 1 Realized OOS full | 2020-01-01 → 2026-05-15 | +41.21% | 15.18% | 10.18% | +0.935 | [-0.799, +3.283] | NO | 108 |
| 0.50 | A0 zero-cost | 2 Realized OOS (2026-onward) | 2026-04-01 → 2026-05-15 | 0.00% | 0.00% | 0/0 | n/a | n/a | n/a | 0 |
| 0.50 | A1 conservative-prior | 1 Realized OOS full | 2020-01-01 → 2026-05-15 | **+23.12%** | 19.77% | 11/(11+97+0) = 10.19% | +0.564 | [-1.300, +3.052] | NO | 108 |
| 0.50 | A1 conservative-prior | 2 Realized OOS (2026-onward) | 2026-04-01 → 2026-05-15 | 0.00% | 0.00% | 0/0 | n/a | n/a | n/a | 0 |
| 1.00 | A0 zero-cost | 1 Realized OOS full | 2020-01-01 → 2026-05-15 | +41.21% | 15.18% | 10.18% | +0.935 | [-0.799, +3.283] | NO | 108 |
| 1.00 | A0 zero-cost | 2 Realized OOS (2026-onward) | 2026-04-01 → 2026-05-15 | 0.00% | 0.00% | 0/0 | n/a | n/a | n/a | 0 |
| 1.00 | A1 conservative-prior | 1 Realized OOS full | 2020-01-01 → 2026-05-15 | +13.04% | 23.69% | 11/(11+94+0) = 10.48% | +0.332 | [-1.591, +2.878] | NO | 105 |
| 1.00 | A1 conservative-prior | 2 Realized OOS (2026-onward) | 2026-04-01 → 2026-05-15 | 0.00% | 0.00% | 0/0 | n/a | n/a | n/a | 0 |

**Component 3 (Forward 1-year bootstrap; 5,000 paths × 252 sessions)**: PLACEHOLDER per `P1-H068-FORWARD-PROJECTION-COMPUTE` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED; n_trades=108 is below the projection-saturation threshold of 252 sessions per ADR-0013 §3.1.1 bootstrap-saturation footnote; the per-trade R-multiple distribution shape is documented in §"Performance KPIs" Table 1c but the projected ending-equity distribution is deferred).

Component-2 (2026-onward sub-window) returns **0 ES trades across all 3 slip cells × all 6 Kelly cells × both cost arms** — the 6-week window contains no eligible channel-break + first-fire-dwell + ID_1 trend-gate events. This is consistent with H062 v1 + H065 v2 2026-onward sub-window observations on ES (low trade-frequency cell-conditional on the trend-filter gate inhibiting entries during the post-2026-04-01 ES microstructure regime).

## End-of-simulation results summary (per ADR-0014 §3.2 + ADR-0017 §3.2 + ADR-0019 Table 1c; 13 mandatory tables + bottom-line prose)

Per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) §3 13-table format. Cell-grid re-organized as per-slip-modal-Kelly rows for cross-comparability with the parent H065 v2 M_inf_h062_v1_fixed-ES at sensitivity_mult=1.0 conservative-prior cell.

### Table 1 — P/L (realized OOS, $10K starting capital)

Per-slip × cost-arm at modal Kelly=0.25 (full 36-cell matrix in [sidecar.json](../../../artifacts/runs/H068/957643d6cb8441e29d888482447ead6e/sidecar.json) `per_cell_results`):

| Slip (sensitivity_mult) | Cost arm | Final equity | Realized ROI % | n_trades | Total gross PnL $ | Total cost USD | Total net PnL $ |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0.25 | A0 zero-cost | $14,120.94 | +41.21% | 108 | +$4,121 | $0 | +$4,121 |
| 0.25 | A1 conservative-prior | $12,993.24 | +29.93% | 108 | +$4,121 | $1,128 | +$2,993 |
| 0.50 | A0 zero-cost | $14,120.94 | +41.21% | 108 | +$4,121 | $0 | +$4,121 |
| **0.50** | **A1 conservative-prior** | **$12,311.79** | **+23.12%** | **108** | **+$4,121** | **$1,809** | **+$2,312** |
| 1.00 | A0 zero-cost | $14,120.94 | +41.21% | 108 | +$4,121 | $0 | +$4,121 |
| 1.00 | A1 conservative-prior | $11,304.28 | +13.04% | 105 | +$4,121 | $3,085 | +$1,304 |

Modal Kelly=0.25 reference (Kelly cells {0.5, 1.0, 1.5, 2.0, 2.5} produce numerically-identical per-trade outcomes per design.md §4 single-unit entry at v1; Kelly-multiplier is a hyperparameter at inner-CV only — preserved from H062 v1 + H065 v2 modal cell behavior). K-6 daily breaker fired 3 times on slip=0.25 + slip=0.5 cells (108 trades) and 6 times on slip=1.0 (105 trades; +3 trades blocked by tighter cost drag).

### Table 1c — Payoff-shape diagnostics (per ADR-0019)

L-skewness τ_3 + 95% bootstrap CI on per-trade R-multiple distribution per [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md):

| Slip × cost arm | L-skewness τ_3 point | τ_3 95% CI | Payoff-shape annotation | Barbell-rebalance candidate? |
|---|---:|---|---|:--:|
| 0.25 × A0 zero-cost | +0.900 | [+0.828, +0.939] | **skew-positive** | yes |
| 0.25 × A1 conservative | +0.896 | [+0.822, +0.939] | **skew-positive** | yes |
| 0.50 × A0 zero-cost | +0.900 | [+0.828, +0.939] | **skew-positive** | yes |
| **0.50 × A1 conservative** | **+0.894** | **[+0.820, +0.938]** | **skew-positive** | yes |
| 1.00 × A0 zero-cost | +0.900 | [+0.828, +0.939] | **skew-positive** | yes |
| 1.00 × A1 conservative | +0.887 | [+0.808, +0.937] | **skew-positive** | yes |

τ_3 95% CIs **all STRICTLY exclude zero positively**. The H068 v1 payoff distribution is uniformly strongly skew-positive across all 6 cells (consistent with parent H065 v2 M_inf-ES strong skew-positive observation). Slip refinement does NOT affect payoff-distribution shape (cost subtracts a constant from each trade's net P/L; shape preserved); only realized $-magnitude varies.

### Table 2 — Drawdown (realized + projected)

Realized at full OOS 2020-01-01 → 2026-05-15:

| Slip × cost arm | Realized Max-DD % | Raw Max-DD % (pre-cap) | Bankroll-blowup? |
|---|---:|---:|:--:|
| 0.25 × A0 zero-cost | 15.18% | 15.18% | No |
| 0.25 × A1 conservative | 17.77% | 17.77% | No |
| 0.50 × A0 zero-cost | 15.18% | 15.18% | No |
| **0.50 × A1 conservative** | **19.77%** | **19.77%** | **No** |
| 1.00 × A0 zero-cost | 15.18% | 15.18% | No |
| 1.00 × A1 conservative | 23.69% | 23.69% | No |

Forward-projection Max-DD distribution: PLACEHOLDER per `P1-H068-FORWARD-PROJECTION-COMPUTE` (n_trades=108 below saturation threshold).

### Table 3 — Primary inference (T = MPPM(ρ=1); stationary-bootstrap CI)

Per [ADR-0018 D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) on per-session-aggregated ES log-return series; Politis-White 2004 stationary-bootstrap block-length selection; n_bootstrap=1000; rng_seed=20260519.

| Slip × cost arm | MPPM(ρ=1) point | 95% CI [low, high] | excludes 0 positively |
|---|---:|---|:--:|
| 0.25 × A0 zero-cost | +0.935 | [-0.799, +3.283] | NO |
| 0.25 × A1 conservative | +0.709 | [-1.103, +3.145] | NO |
| 0.50 × A0 zero-cost | +0.935 | [-0.799, +3.283] | NO |
| **0.50 × A1 conservative** | **+0.564** | **[-1.300, +3.052]** | **NO** |
| 1.00 × A0 zero-cost | +0.935 | [-0.799, +3.283] | NO |
| 1.00 × A1 conservative | +0.332 | [-1.591, +2.878] | NO |

H_1 criterion (b) FAILS on all 6 cells; MPPM CIs uniformly cover zero. The point estimates are POSITIVE across the board (+0.33 to +0.94) — consistent with realized ROI > 0 — but n_trades=108 → per-session log-return sample n ≈ 90-100 → bootstrap CI width swallows the point estimate per design.md §1.4 statistical-power caveat (7× wider than the H067-SIL n=5,600 equivalent).

### Table 3a — Terminal-wealth q05 (per ADR-0017 §3.2)

Per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained primary metric vector — 1-year bootstrap forward `terminal_wealth_q05` per 252-session basis:

| Slip × cost arm | terminal_wealth_q05 ($10K basis) | Annotation |
|---|---:|---|
| All 6 cells | PLACEHOLDER per `P1-H068-FORWARD-PROJECTION-COMPUTE` | `tw-q05-n/a-pending-projection` |

Realized OOS q05 equity per cell IS measurable from the equity curve but Component-3 bootstrap forward projection is deferred per the n_trades=108 sample-size constraint (below the 252-session bootstrap saturation threshold per ADR-0013 §3.1.1 footnote).

### Table 3b — Calmar-differential (per ADR-0017 §3.2)

Calmar ratio (per-cell) at full OOS:

| Slip × cost arm | Calmar ratio point | Sharpe (annualised) |
|---|---:|---:|
| 0.25 × A0 zero-cost | 10.194 | 1.378 |
| 0.25 × A1 conservative | 5.812 | 1.007 |
| 0.50 × A0 zero-cost | 10.194 | 1.378 |
| **0.50 × A1 conservative** | **3.828** | **0.781** |
| 1.00 × A0 zero-cost | 10.194 | 1.378 |
| 1.00 × A1 conservative | 1.663 | 0.447 |

Calmar-differential CI vs passive-EW ES PLACEHOLDER per `P1-H068-CALMAR-DIFFERENTIAL-CI-COMPUTE` (Calmar-CI primitive needs paired-pairs stationary-bootstrap CI; point estimates above are diagnostic-only). Per ADR-0017 §3 annotation: `calmar-diff-n/a-pending-ci`.

### Table 3c — Profit-factor + R-multiple-mean (per ADR-0017 §3.2)

| Slip × cost arm | Profit factor | R-multiple-mean | R-mean 95% CI | excludes 0 |
|---|---:|---:|---|:--:|
| 0.25 × A0 zero-cost | 1.49 | +0.419 | n/a (n=108 within-sample) | NO via bootstrap |
| 0.25 × A1 conservative | 1.32 | +0.304 | [-0.625, +1.557] | NO |
| 0.50 × A0 zero-cost | 1.49 | +0.419 | n/a | NO |
| **0.50 × A1 conservative** | **1.23** | **+0.234** | **[-0.707, +1.489]** | **NO** |
| 1.00 × A0 zero-cost | 1.49 | +0.419 | n/a | NO |
| 1.00 × A1 conservative | 1.12 | +0.136 | [-0.836, +1.420] | NO |

R-mean-mean per-cell strictly above 0.0 ($-net positive expectancy) but CIs uniformly cover zero (n_trades=108 inferential-power floor per design.md §9). PF strictly > 1.0 at all 6 cells. ADR-0017 §3 annotations: `pf-marginal` (PF > 1 but no CI gating); `r-mean-marginal`.

### Table 4 — Annualised Sharpe (with annualisation-factor declaration)

Annualisation factor = 252 sessions/year per project-canonical convention; per-session log-returns Sharpe = mean/std; annualised = √252 × per-session Sharpe.

(Numbers identical to Table 3b column "Sharpe (annualised)".)

### Table 5 — Win/Loss/Zero counts + win rate

| Slip × cost arm | W | L | Z | n_trades | Win rate W/(W+L+Z) |
|---|---:|---:|---:|---:|---:|
| 0.25 × A0 zero-cost | 11 | 96 | 1 | 108 | 10.19% |
| 0.25 × A1 conservative | 11 | 97 | 0 | 108 | 10.19% |
| 0.50 × A0 zero-cost | 11 | 96 | 1 | 108 | 10.19% |
| **0.50 × A1 conservative** | **11** | **97** | **0** | **108** | **10.19%** |
| 1.00 × A0 zero-cost | 11 | 96 | 1 | 108 | 10.19% |
| 1.00 × A1 conservative | 11 | 94 | 0 | 105 | 10.48% |

Strongly skew-positive payoff shape per ADR-0019 §3: low win rate (~10%) with τ_3 ≈ +0.90 means the H068 v1 wick-rejection variant is dominated by a small number of large wins (the right tail of the channel-breakout-let-it-run-to-channel-reverse distribution).

### Table 6 — Forward 1-year projection (Median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%))

PLACEHOLDER per `P1-H068-FORWARD-PROJECTION-COMPUTE` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED; sample-size constraint at n_trades=108 below 252-session bootstrap saturation per ADR-0013 §3.1.1 footnote).

| Statistic | Value |
|---|---|
| median ending equity | TBD |
| q01 / q05 / q95 / q99 | TBD / TBD / TBD / TBD |
| P(loss) | TBD |
| P(double) | TBD |
| P(<50%) | TBD |

### Table 7 — Hansen SPA family p (with mechanical interpretation)

PLACEHOLDER per `P1-H068-HANSEN-SPA-COMPUTE` (operator-discretionary; family size = 3 slip-cells × 6 Kelly = 18 cells; tractable but not yet wired into the orchestrator). Per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) `omega-corrected` method.

### Table 8 — Other KPIs (per ADR-0017 §3 + ADR-0019 + ADR-0025 + ADR-0026 + ADR-0028 + ADR-0026 §D-3)

| Annotation key | Value | Source |
|---|---|---|
| `best_label_cfg` | sensitivity_mult=0.5 (load-bearing per design.md §1.4 mid empirical anchor; ratio just crosses ADR-0028 threshold) | per-cell sweep |
| `n_folds_realized` | n/a (representative cell grid; no walk-forward outer-CV in v1) | sweep design |
| `n_folds_expected` | n/a (per design.md §13 v1 scope deviation) | design.md §13 |
| `max_dd_annotation` | drawdown-acceptable-at-19.77pct (per Tharp 1998 *practitioner* DD < 25% rule of thumb) | Table 2 |
| `cost_model` | nt8_realistic_v1; conservative_prior; sensitivity_mult ∈ {0.25, 0.5, 1.0}; ES exchange + NFA CME-verified eff. 2024-02 | [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) + design.md §6 |
| `deferred_kpis` | terminal_wealth_q05; Calmar-differential CI; Hansen SPA; forward-projection — all DEFERRED per follow-ups below | §6 |
| `kill-switch-mode` | **block** (K-4 + K-6 + K-7 enabled in block-mode per design.md §11.1 + ADR-0028 §D-1 default) | design.md §11.1 |
| `K-6 trigger counts (modal Kelly=0.25)` | 3 sessions at slip ∈ {0.25, 0.5}; 6 sessions at slip=1.0 | sidecar |
| `K-7 trigger counts (modal Kelly=0.25)` | 0 weeks (5%-week threshold never breached on any cell) | sidecar |
| `equity-rebase-mode` | fixed (H062 v1 modal preserved per design.md §11.1; current-equity deferred to v3) | design.md §11.1 |
| `bocd-live-mode` | inactive (deferred per `P1-BOCD-LIVE-PRIOR-CALIBRATION-H068-V3`) | design.md §11.1 |
| `cost-friction-dominated-edge-{present, absent, n/a}` (per ADR-0028 §D-2) | **absent on all 3 slip cells** — both A0 zero-cost AND A1 conservative-prior produce realized ROI > 0; the A1 cell does NOT flip A0 sign; per ADR-0028 §D-2 trigger semantics this is `absent` regardless of breakeven ratio | per breakeven table below |
| `cost-friction-breakeven-ratio-crosses-2` (per ADR-0028 §D-2 threshold; design.md §6 Pareto-front interpretation) | **TRUE at slip=0.25 (3.65) AND slip=0.5 (2.28); FALSE at slip=1.0 (1.30)** | per breakeven table below |
| `pre-empirical-ratio-prediction-verified` | YES (predicted ~2.22 at slip=0.5; realized 2.278; deviation +0.058 = 2.6%) | design.md §1.4 + breakeven table |
| `promising-mppm-{cost-provenance}-{substrate-checksum-prefix}-{cell-coordinates}` (per ADR-0026 §D-3) | **`promising-mppm-none`** — no cell carries MPPM CI strictly excluding zero positively | sidecar `promising_annotation` |
| `payoff-shape` (per ADR-0019 §3) | **skew-positive** (τ_3 ≈ +0.89 with 95% CI strictly excludes zero positively on every cell) | Table 1c |
| `super-kelly-operator-discretionary` (per ADR-0018 §D-2) | n/a (Kelly=0.25..1.0 cells are NOT super-kelly; Kelly ∈ {1.5, 2.0, 2.5} cells reported but produce numerically-identical per-trade outcomes at v1 single-unit-entry sizing) | design.md §5.3 |
| `causal-mechanism-{causal-mechanism, correlation-only, hybrid}` (per ADR-0022 §3) | **hybrid** (channel-break-as-information-event causal claim from parent H062 + H065; sub-1-tick slip empirical sensitivity layer is correlation-only refinement) | design.md §1.3 |

#### Cost-friction-breakeven ratio per slip cell (modal Kelly=0.25)

| sensitivity_mult | A0 ROI % | A1 ROI % | per-trade gross-edge bps-eq | per-trade cost bps-eq | ratio (gross/cost) | crosses ≥2 threshold? | edge_annotation |
|---:|---:|---:|---:|---:|---:|:--:|---|
| **0.25** | +41.21% | +29.93% | 38.16 | 10.45 | **3.653** | **YES** | absent (A1 not negative) |
| **0.50** | +41.21% | +23.12% | 38.16 | 16.75 | **2.278** | **YES** | absent (A1 not negative) |
| 1.00 (parent baseline) | +41.21% | +13.04% | 38.16 | 29.38 | 1.299 | NO | absent (A1 not negative) |

Pre-empirical prediction in design.md §1.4: ratio at slip=0.5 ≈ 2.22; ratio at slip=0.25 ≈ 3.56; ratio at slip=1.0 ≈ 1.27 (anchored on cross-hypothesis investigation 2026-05-19 addendum §3 row #1 H065 v2 M_inf_h062_v1_fixed-ES parent cell). Realized values: 2.278 / 3.653 / 1.299. **Pre-empirical prediction VERIFIED within ≤ 3% deviation** at every slip cell. The structural cost-reduction working as predicted does NOT translate to H_1 conjunctive clearance because the A1 cell's realized OOS ROI remains positive (+23.12% at slip=0.5) — the A0 → A1 transition does not flip P/L sign so the ADR-0028 §D-2 "cost-friction-dominated-edge-present" annotation does not fire by construction.

### Table 9 — Methodological-correctness annotations

`leakage-canary-pass · mppm-rho1-positive-ci-covers-zero · skew-positive-strict-ci-excludes-zero · cost-friction-dominated-edge-absent · cost-friction-breakeven-ratio-crosses-2-at-slip-0.5-and-0.25 · pre-empirical-ratio-prediction-verified · kelly-multiplier-0.25 · cost-conservative-prior-sensitivity-0.5 · promising-mppm-none · kill-switch-mode-block · k6-triggers-3-sessions · k7-triggers-0-weeks · equity-rebase-fixed · bocd-live-inactive · causal-mechanism-hybrid · paradigm-adr-0024-aggressive-growth · paradigm-adr-0028-block-default · repro-log-complete · power-margin-ok-n-trades-108-above-50`

## Bottom line (≤ 8 sentences per ADR-0014 §3.2)

H068 v1 — sub-1-tick slip empirical sensitivity sweep on the H065 v2 M_inf_h062_v1_fixed-ES parent cell — produces a **null verdict on the H_1 conjunctive criterion at all 3 slip cells**, despite the structural cost-reduction mechanism working empirically as predicted (per-trade cost-friction-breakeven ratio rises from 1.30 at slip=1.0 baseline to 2.28 at slip=0.5 and 3.65 at slip=0.25, **VERIFYING the design.md §1.4 pre-empirical prediction within ≤ 3% deviation** at every cell). The limiting H_1 criterion is (b) MPPM(ρ=1) CI excludes zero positively — at n_trades=108 the bootstrap CI width swallows the +0.33 to +0.94 point-estimate range; per design.md §1.4 statistical-power caveat the H068-ES sample is 7× wider than the H067-SIL n=5,600 equivalent. Realized OOS ROI is positive on every A1 cell (+13% at slip=1.0 baseline; +23% at slip=0.5 mid; +30% at slip=0.25 aggressive) with strongly skew-positive payoff structure (τ_3 ≈ +0.89 with 95% CI strictly excluding zero on every cell). The 2026-04-01 → 2026-05-15 sub-window produces zero ES trades across all 36 cells — the post-2026-04-01 ES microstructure regime does not generate signal-eligible channel-break + first-fire + trend-gate events on the canonical substrate. The K-6 daily breaker fired 3 sessions at slip ∈ {0.25, 0.5} and 6 sessions at slip=1.0 (tighter cost drag → more drawdown-induced K-6 fires); K-7 never fired. **Operator interpretation per design.md §10 + ADR-0013 §1**: the H068 v1 result confirms the cost-light genetic-cross is mechanically working — sub-1-tick slip refinement does push the cost-friction-breakeven ratio above the ADR-0028 §D-2 ≥2 threshold — but the load-bearing operator-actionable answer "how much slip reduction is needed to push the ES cell into MPPM CI-strict-positive territory" requires paper-trade fill-data calibration of the empirical slip prior (`P1-H068-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION`) AND a larger trade sample. Pareto-front recommendation: **sensitivity_mult=0.5 is the load-bearing operator-readable threshold** (ratio 2.28 just clears ≥2; realized ROI +23% positive; uniquely "above breakeven but below empirically-saturated"). Next mandatory transition per ADR-0013 §5: `kpi-report-emitted` → `ninjascript-implemented` (operator-discretionary per user 2026-05-04 standing decline directive).

## Pareto-front operator deliverable (per design.md §8 + §13)

| sensitivity_mult | H_1 (a) ROI > 0 | H_1 (b) MPPM CI excludes 0 pos | H_1 (c) ratio ≥ 2 | H_1 conjunctive met | Recommendation per design.md §1 |
|---:|:--:|:--:|:--:|:--:|---|
| 0.25 (aggressive) | YES (+29.93%) | NO ([−1.10, +3.15]) | YES (3.65) | NO | Operationally-aggressive prior; only valid if paper-trade fill-data calibration confirms ≤ 0.25-tick empirical slip on RTH ES |
| **0.50 (mid empirical sensitivity)** | YES (+23.12%) | NO ([−1.30, +3.05]) | **YES (2.28)** | **NO** | **Recommended operator-readable slip\* per design.md §1.4 Pareto-front interpretation (largest slip satisfying ratio ≥ 2)**; consistent with cross-hypothesis investigation §7.2 practitioner-anecdote range 0.3-0.7 ticks for retail-tier liquid CME equity-index futures on RTH high-liquidity hours |
| 1.00 (parent baseline) | YES (+13.04%) | NO ([−1.59, +2.88]) | NO (1.30) | NO | Conservative-prior baseline; preserved as direct-comparability anchor to cross-hypothesis investigation 2026-05-19 addendum §3 row #1 |

The Pareto-front operator-recommended slip\* = 0.5 ticks per side ($6.25/side on ES) — the LARGEST slip value satisfying ratio ≥ 2.0 per design.md §1.4 + design.md §8 Pareto-front interpretation.

## Per-fold + per-fold-aggregate cell results

Full 36-cell sidecar at [artifacts/runs/H068/957643d6cb8441e29d888482447ead6e/sidecar.json](../../../artifacts/runs/H068/957643d6cb8441e29d888482447ead6e/sidecar.json) (scientific_payload SHA256 = `a5bce59880e0dd5d824a5b4fd6d7ef7db1df80f05599dc34744f0d26b59ca714`). Per-partition ES SHA enumeration also recorded in the sidecar `substrate_per_partition_shas_es` field (12 partitions: years 2015-2026).

## Substrate provenance

| Field | Value |
|---|---|
| substrate_dataset_checksum | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.10 main-HEAD) |
| ES partition coverage | 2015-01-01 → 2026-05-15 (12 partitions per year) |
| Active OOS window per design.md §2 | 2020-01-01 → 2026-05-15 (5-min bars resampled from 1-min roll-adjusted; 431,751 bars across 1,903 sessions) |
| Sub-window (per ADR-0026 §D-1 component 2) | 2026-04-01 → 2026-05-15 (~30 sessions; 0 trades fired across all 36 cells) |

ReproLog at [logs/reproducibility/957643d6cb8441e29d888482447ead6e.json](../../../logs/reproducibility/957643d6cb8441e29d888482447ead6e.json) (13/13 fields per CLAUDE.md §"Reproducibility (hook-enforced)" mandate; binds `model_hash` to `scientific_payload_sha256` per ADR-0017 §3).

## Scope deviations from full-spec inner-CV grid (recorded per Path A frozen-pre-reg amendment discipline)

- v1 reports the 36-cell representative grid (3 sensitivity_mult × 6 Kelly × 2 cost-arm) at fixed H065 v2 modal feature cell. Full 13,824-cell combinatorial grid tracked under `P1-H068-FULL-INNER-CV-GRID-V2`.
- ES standalone (no 4-symbol basket). Cross-asset extension tracked under `P1-H068-V2-CROSS-ASSET-BASKET-EXTEND`.
- Walk-forward outer CV NOT executed at v1 (n_trades=108 over 6 years OOS is below the per-fold subsampling threshold); v1 reports the full single-pass OOS aggregate. Walk-forward outer-CV variant tracked under `P1-H068-WALK-FORWARD-OUTER-CV-V2`.
- Forward-projection bootstrap deferred per `P1-H068-FORWARD-PROJECTION-COMPUTE` (sample-size constraint).
- Kelly-multiplier {0.5, 1.0, 1.5, 2.0, 2.5} cells produce numerically-identical per-trade outcomes to Kelly=0.25 at v1 single-unit-entry sizing (Kelly is a hyperparameter at inner-CV only per H062 v1 + H065 v2 modal cell preservation). Multi-lot Kelly-scaling tracked under `P1-H068-V2-N-LOT-SCALING-PATH-DELAYED`.
- 1-lot at v1 (no pyramiding); pyramiding tracked under H066 sibling and `P1-H068-V2-N-LOT-SCALING-PATH-DELAYED`.
- News-calendar exclusion (FOMC ±15min + NFP ±5min + CPI ±5min) feature-factory layer inherited from H062 + H065 verbatim (no new exclusion at v1).

## Stage transition + next-step

| Field | Value |
|---|---|
| Stage at v1 emission | `kpi-report-emitted` (recorded in [stage.md](stage.md)) |
| Next mandatory transition per ADR-0013 §5 | `kpi-report-emitted` → `ninjascript-implemented` (operator-discretionary per user 2026-05-04 standing decline directive) |
| Tracked under | `P1-H068-NINJASCRIPT-IMPL` (open; bridge-mediated per design.md §15 + ADR-0013 §5.2) |

## Follow-ups registered by this KPI v1 emission

- `P1-H068-FORWARD-PROJECTION-COMPUTE` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED stage transition; sample-size constraint at n_trades=108 below 252-session bootstrap saturation per ADR-0013 §3.1.1 footnote).
- `P1-H068-CALMAR-DIFFERENTIAL-CI-COMPUTE` (paired-pairs stationary-bootstrap CI vs passive-EW ES reference; Calmar point estimates per Table 3b).
- `P1-H068-HANSEN-SPA-COMPUTE` (family size = 18 cells; tractable; operator-discretionary timing).
- `P1-H068-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED; load-bearing per design.md §1.3 — the sub-1-tick slip empirical reasonableness depends on order book depth + RTH liquidity stratification + order type + size).
- `P1-H068-NINJASCRIPT-IMPL` (mandatory per ADR-0013 §5; operator-discretionary decline allowed per 2026-05-04 standing directive).
- `P1-H068-NINJASCRIPT-PARITY-TOLERANCE` (Python ↔ NinjaScript parity-check per ADR-0013 §5.2).
- `P1-H068-WALK-FORWARD-OUTER-CV-V2` (n_trades=108 below per-fold subsampling threshold at v1; v2 successor at larger trade sample).
- `P1-H068-FULL-INNER-CV-GRID-V2` (v1 used 36-cell representative grid).
- `P1-H068-V2-CROSS-ASSET-BASKET-EXTEND` (ES-only at v1; 4-symbol basket at v2 successor).
- `P1-H068-V2-N-LOT-SCALING-PATH-DELAYED` (1-lot at v1; N-lot deferred per ADR-0027 §D-4 single-axis discipline).
- `P1-H068-V3-CURRENT-EQUITY-REBASE` (fixed-equity rebase at v1 per parent-cell preservation; current-equity rebase v3 axis).
- `P1-BOCD-LIVE-PRIOR-CALIBRATION-H068-V3` (BOCD live-pause primitive deferred at v1; v3 cycle).
