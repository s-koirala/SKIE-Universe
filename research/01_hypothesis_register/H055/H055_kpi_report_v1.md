---
hypothesis: H055
version: v1
status: kpi-report-emitted
run_id: v2_sweep_20260516T025924Z
sidecar_sha256: 83cd09e88476b93d0be18d4a12c4cd90dbaf7d21168aec0bf9d9741c33e43ef5
git_head: 07d58a42dc3b19b282055db0ebcd6bccf86da495
substrate_dataset_checksum: b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce
emitted_utc: 2026-05-16T02:59:50Z
predecessor_versions: []
---

# H055 KPI Report Card v1 — Aggressive-sizing sweep on wick-rejection mean-reversion scalping

Per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) + [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md), this report card emits H055 KPIs under the survival-constrained / regime-conditional aggressive-growth paradigm. The sweep evaluates 5 sizing configurations (v1 / C2 / C3 / C9 / C5) on the H055 design.md §3 wick-rejection setup family (swing-pivot + wick-reversal-non-swing) across the 4-symbol cross-futures basket {ES, NQ, MGC, SIL}.

**This is research-only** — H055 design.md is frozen at `status: designed` 2026-05-06. Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1, the stage transition `exploration-in-progress` → `kpi-report-emitted` is operator-discretionary upon canonical-format presentation. Per the operator's 2026-05-04 standing directive, the subsequent `kpi-report-emitted` → `ninjascript-implemented` transition is also operator-discretionary.

## §1 Hypothesis preamble (cross-link to design.md)

- **H_0**: v2 (any of the 5 sweep variants) does NOT strictly dominate B&H / TSMOM / no-skill bootstrap on Sharpe-differential CI (LW2008) per design.md §1.
- **H_1**: at least one sweep variant produces a basket-level KPI configuration (MPPM(ρ=1) > 0; Calmar > 0.5; profit-factor > 1.1; R-multiple-mean > 0; payoff-shape ≠ skew-negative) under ADR-0017 §1 primary metric vector on the 2024-01-01 → 2026-05-15 OOS window.
- **Pre-empirical framing** (per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §Context + AMH per Lo 2004 *J Portfolio Mgmt* 30(5):15-29): strategy decay is the null. The 5-config sweep tests whether ADR-0017 §4.1 current-equity rebase + ADR-0018 D-2 Kelly multiplier grid + D-3 BOCD step-up can extract any geometric-growth potential from the H055 wick-rejection setup distribution. The v1 baseline is the **fixed-equity-quarter-Kelly** floor; the C2/C3/C5/C9 cells test the aggressive-growth paradigm.

## §2 End-of-simulation results summary

Per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), the 9 mandatory tables + bottom-line. Per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §3 amendment + [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md), **MPPM(ρ=1)** replaces Sharpe-differential as the primary inferential metric. Sharpe-family CIs are reported as secondary KPI annotations per ADR-0017 §1.2.

### Table 1 — P/L (realized OOS, $10,000 starting capital)

Full OOS window: 2024-01-01 → 2026-05-15 (per-symbol substrate right edges). Sub-window: 2026-04-01 → 2026-05-15 (recent 6 weeks).

| Config | Symbol | n_trades | End equity ($10K start) | OOS ROI% | Sub-window n_trades | Sub-window ROI% |
|---|---|---:|---:|---:|---:|---:|
| v1 | ES | 0 | $10,000 | +0.0% | 0 | +0.0% |
| v1 | NQ | 0 | $10,000 | +0.0% | 0 | +0.0% |
| v1 | MGC | 3,622 | $9,884 | -1.2% | 0 | +0.0% |
| v1 | SIL | 329 | $9,883 | -1.2% | 0 | +0.0% |
| **v1 BASKET** | 4-sym | 3,951 | $39,767 | **-0.6%** | 0 | +0.0% |
| C2 full-Kelly | ES | 641 | $9,900 | -1.0% | 53 | -1.6% |
| C2 full-Kelly | NQ | 8 | $10,029 | +0.3% | 0 | +0.0% |
| C2 full-Kelly | MGC | 10,321 | $17,240 | +72.4% | 1,179 | +13.4% |
| C2 full-Kelly | SIL | 5,978 | $10,183 | +1.8% | 0 | +0.0% |
| **C2 full-Kelly BASKET** | 4-sym | 16,948 | $47,352 | **+18.4%** | 1,232 | +4.1% |
| C3 super-Kelly km=2.0 | ES | 3,301 | $12,306 | +23.1% | 285 | -9.0% |
| C3 super-Kelly km=2.0 | NQ | 238 | $7,888 | -21.1% | 0 | +0.0% |
| C3 super-Kelly km=2.0 | MGC | 7,625 | $18,700 | +87.0% | 770 | -4.7% |
| C3 super-Kelly km=2.0 | SIL | 4,177 | $8,989 | -10.1% | 35 | -1.8% |
| **C3 super-Kelly BASKET** | 4-sym | 15,341 | $47,883 | **+19.7%** | 1,090 | -4.4% |
| C9 BOCD step-up | ES | 653 | $9,917 | -0.8% | 0 | +0.0% |
| C9 BOCD step-up | NQ | 134 | $8,367 | -16.3% | 0 | +0.0% |
| C9 BOCD step-up | MGC | 9,442 | $15,797 | +58.0% | 1,089 | +7.6% |
| C9 BOCD step-up | SIL | 3,959 | $10,718 | +7.2% | 0 | +0.0% |
| **C9 BOCD BASKET** | 4-sym | 14,188 | $44,798 | **+12.1%** | 1,089 | +2.5% |
| C5 super + pyramid | ES | 706 | $4,648 | -53.5% | 60 | -2.0% |
| C5 super + pyramid | NQ | 398 | $9,648 | -3.5% | 13 | -1.4% |
| C5 super + pyramid | MGC | 7,665 | $17,718 | +77.2% | 786 | +8.5% |
| C5 super + pyramid | SIL | 3,509 | $5,336 | -46.6% | 30 | -1.2% |
| **C5 super-pyramid BASKET** | 4-sym | 12,278 | $37,350 | **-6.6%** | 889 | +3.0% |

### Table 2 — Drawdown (realized only; forward projection deferred to §3 below)

| Config | Symbol | Max-DD% (realized OOS) | Sub-window Max-DD% |
|---|---|---:|---:|
| v1 | ES | 0.0% | 0.0% |
| v1 | NQ | 0.0% | 0.0% |
| v1 | MGC | 9.8% | 0.0% |
| v1 | SIL | 4.4% | 0.0% |
| C2 full-Kelly | ES | 15.2% | 1.9% |
| C2 full-Kelly | NQ | 1.9% | 0.0% |
| C2 full-Kelly | MGC | 29.6% | 10.0% |
| C2 full-Kelly | SIL | 35.9% | 0.0% |
| C3 super-Kelly km=2.0 | ES | 41.0% | 19.0% |
| C3 super-Kelly km=2.0 | NQ | 34.6% | 0.0% |
| C3 super-Kelly km=2.0 | MGC | 37.3% | 22.6% |
| C3 super-Kelly km=2.0 | SIL | 58.3% | 11.2% |
| C9 BOCD step-up | ES | 23.2% | 0.0% |
| C9 BOCD step-up | NQ | 25.6% | 0.0% |
| C9 BOCD step-up | MGC | 21.4% | 4.8% |
| C9 BOCD step-up | SIL | 32.7% | 0.0% |
| C5 super + pyramid | ES | **58.3%** | 2.0% |
| C5 super + pyramid | NQ | 23.3% | 2.0% |
| C5 super + pyramid | MGC | 39.8% | 20.4% |
| C5 super + pyramid | SIL | **64.5%** | 1.2% |

### Table 3 — Primary inference: MPPM(ρ=1) per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1

T_H055 = MPPM(ρ=1) [annualised log-wealth growth rate per Goetzmann-Ingersoll-Spiegel-Welch 2007 *RFS* 20(5):1503-1546 DOI 10.1093/rfs/hhm025]. Bootstrap CI deferred to follow-up `P1-H055-MPPM-RHO-1-CI-PRIMITIVE`; point estimate only at v1.

| Config | Symbol | MPPM(ρ=1) | sign | KPI annotation |
|---|---|---:|:---:|---|
| v1 | MGC | -0.007 | flat | `mppm-flat` |
| v1 | SIL | -0.023 | negative | `mppm-negative` |
| C2 full-Kelly | ES | -0.010 | flat | `mppm-flat` |
| C2 full-Kelly | NQ | +0.175 | positive | `mppm-positive` |
| C2 full-Kelly | MGC | +0.206 | positive | `mppm-positive` |
| C2 full-Kelly | SIL | +0.009 | flat | `mppm-flat` |
| C3 super-Kelly km=2.0 | ES | +0.099 | positive | `mppm-positive` |
| C3 super-Kelly km=2.0 | NQ | -0.629 | negative | `mppm-negative` |
| C3 super-Kelly km=2.0 | MGC | +0.263 | positive | `mppm-positive` |
| C3 super-Kelly km=2.0 | SIL | -0.059 | flat | `mppm-flat` |
| C9 BOCD step-up | ES | -0.013 | flat | `mppm-flat` |
| C9 BOCD step-up | NQ | -0.678 | negative | `mppm-negative` |
| C9 BOCD step-up | MGC | +0.185 | positive | `mppm-positive` |
| C9 BOCD step-up | SIL | +0.037 | flat | `mppm-flat` |
| C5 super + pyramid | ES | -0.885 | negative | `mppm-negative` |
| C5 super + pyramid | NQ | -0.066 | flat | `mppm-flat` |
| C5 super + pyramid | MGC | +0.243 | positive | `mppm-positive` |
| C5 super + pyramid | SIL | -0.398 | negative | `mppm-negative` |

**Strongest cells by MPPM(ρ=1)**: MGC C3 (+0.263) > MGC C5 (+0.243) > MGC C2 (+0.206) > MGC C9 (+0.185) > NQ C2 (+0.175) > ES C3 (+0.099).

### Table 4 — Annualised Sharpe (secondary KPI per ADR-0017 §1.2)

Annualisation factor: √(n_trades / n_years_proxy) where n_years_proxy = n_bars / (78 × 252) per RTH-session-bar convention. Reported for academic comparability only.

| Config | Symbol | Per-trade SR | Annualised SR |
|---|---|---:|---:|
| v1 | MGC | -0.001 | -0.05 |
| v1 | SIL | -0.014 | -0.15 |
| C2 full-Kelly | ES | -0.001 | -0.02 |
| C2 full-Kelly | NQ | +0.018 | +0.05 |
| C2 full-Kelly | MGC | +0.005 | +0.33 |
| C2 full-Kelly | SIL | +0.000 | +0.01 |
| C3 super-Kelly km=2.0 | ES | +0.003 | +0.10 |
| C3 super-Kelly km=2.0 | NQ | -0.030 | -0.45 |
| C3 super-Kelly km=2.0 | MGC | +0.004 | +0.26 |
| C3 super-Kelly km=2.0 | SIL | -0.001 | -0.05 |
| C9 BOCD step-up | ES | -0.000 | -0.01 |
| C9 BOCD step-up | NQ | -0.042 | -0.48 |
| C9 BOCD step-up | MGC | +0.005 | +0.43 |
| C9 BOCD step-up | SIL | +0.001 | +0.07 |
| C5 super + pyramid | ES | -0.024 | -0.64 |
| C5 super + pyramid | NQ | -0.003 | -0.05 |
| C5 super + pyramid | MGC | +0.003 | +0.24 |
| C5 super + pyramid | SIL | -0.005 | -0.28 |

### Table 5 — Win/Loss/Zero counts + win rate

| Config | Symbol | Wins | Losses | Zeros | Total | Win rate (W/(W+L+Z)) |
|---|---|---:|---:|---:|---:|---:|
| v1 | MGC | 1,649 | 1,779 | 194 | 3,622 | 45.5% |
| v1 | SIL | 119 | 142 | 68 | 329 | 36.2% |
| C2 full-Kelly | ES | 274 | 318 | 49 | 641 | 42.7% |
| C2 full-Kelly | NQ | 3 | 4 | 1 | 8 | 37.5% |
| C2 full-Kelly | MGC | 4,915 | 5,128 | 278 | 10,321 | 47.6% |
| C2 full-Kelly | SIL | 2,622 | 2,893 | 463 | 5,978 | 43.9% |
| C3 super-Kelly km=2.0 | ES | 1,450 | 1,675 | 176 | 3,301 | 43.9% |
| C3 super-Kelly km=2.0 | NQ | 104 | 129 | 5 | 238 | 43.7% |
| C3 super-Kelly km=2.0 | MGC | 3,586 | 3,829 | 210 | 7,625 | 47.0% |
| C3 super-Kelly km=2.0 | SIL | 1,853 | 2,051 | 273 | 4,177 | 44.4% |
| C9 BOCD step-up | ES | 282 | 324 | 47 | 653 | 43.2% |
| C9 BOCD step-up | NQ | 56 | 76 | 2 | 134 | 41.8% |
| C9 BOCD step-up | MGC | 4,458 | 4,686 | 298 | 9,442 | 47.2% |
| C9 BOCD step-up | SIL | 1,689 | 1,909 | 361 | 3,959 | 42.7% |
| C5 super + pyramid | ES | 278 | 392 | 36 | 706 | 39.4% |
| C5 super + pyramid | NQ | 175 | 217 | 6 | 398 | 44.0% |
| C5 super + pyramid | MGC | 3,565 | 3,887 | 213 | 7,665 | 46.5% |
| C5 super + pyramid | SIL | 1,488 | 1,775 | 246 | 3,509 | 42.4% |

**Win rates uniformly < 50%** across all cells. The strategy expectancy comes from R:R asymmetry (α_tp = 2.0 × ATR vs β_sl = 1.5 × ATR ≈ 1.33R reward-to-risk); winning trades on average pay more than losing trades cost.

### Table 6 — Forward 1-year projection (252-session bootstrap)

DEFERRED — forward projection per [ADR-0017 §1](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) requires the R-multiple distribution bootstrap primitive at [src/skie_ninja/inference/risk_of_ruin.py](../../../src/skie_ninja/inference/risk_of_ruin.py). Annotated as `forward-projection-deferred-v2`; tracked under follow-up `P1-H055-FORWARD-PROJECTION-COMPUTE` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED).

| Config | Symbol | Median | q05 | q95 | P(loss) | P(<50%) | Risk-of-ruin |
|---|---|---:|---:|---:|---:|---:|---:|
| (deferred) | — | — | — | — | — | — | — |

### Table 7 — Hansen SPA family p (per [ADR-0017 §1.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) secondary KPI demotion)

DEFERRED at v1 — the v1 sweep is a 5-cell sizing variant comparison, NOT a hyperparameter-grid TPE-search per design.md §5.6. SPA family is empty at this scope (M=1 degenerate per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md)). Reported as `spa-n/a-m1-degenerate`. Full SPA family entry deferred to follow-up `P1-H055-POWER-SIMULATION-EXECUTE` + `P1-H055-OPTUNA-INNER-CV-IMPL` (the production-grade walk-forward).

| Config | Hansen SPA p | Notes |
|---|---|---|
| All | n/a (M=1 degenerate) | `spa-n/a-m1-degenerate` per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) |

### Table 8 — Other KPIs

| Config | Symbol | Calmar | Profit factor | R-mean | L-skew τ_3 | Payoff-shape |
|---|---|---:|---:|---:|---:|:---|
| v1 | MGC | -0.075 | 0.99 | -0.002 | +0.075 | skew-flat |
| v1 | SIL | -0.534 | 0.94 | -0.025 | +0.064 | skew-flat |
| C2 full-Kelly | ES | -0.069 | 1.00 | +0.003 | +0.110 | skew-positive |
| C2 full-Kelly | NQ | +9.358 | 1.10 | +0.052 | +0.113 | skew-positive |
| C2 full-Kelly | MGC | +0.696 | 1.03 | +0.009 | +0.068 | skew-flat |
| C2 full-Kelly | SIL | +0.025 | 1.00 | +0.006 | +0.079 | skew-flat |
| C3 super-Kelly km=2.0 | ES | +0.240 | 1.01 | +0.006 | +0.096 | skew-flat |
| C3 super-Kelly km=2.0 | NQ | -1.820 | 0.86 | -0.047 | +0.145 | skew-positive |
| C3 super-Kelly km=2.0 | MGC | +0.706 | 1.02 | +0.009 | +0.075 | skew-flat |
| C3 super-Kelly km=2.0 | SIL | -0.102 | 1.00 | +0.000 | +0.080 | skew-flat |
| C9 BOCD step-up | ES | -0.058 | 1.00 | -0.004 | +0.108 | skew-positive |
| C9 BOCD step-up | NQ | -2.647 | 0.81 | -0.068 | +0.175 | skew-positive |
| C9 BOCD step-up | MGC | +0.861 | 1.04 | +0.011 | +0.069 | skew-flat |
| C9 BOCD step-up | SIL | +0.113 | 1.01 | +0.005 | +0.084 | skew-flat |
| C5 super + pyramid | ES | -1.516 | 0.84 | -0.126 | +0.137 | skew-positive |
| C5 super + pyramid | NQ | -0.283 | 0.99 | -0.091 | +0.120 | skew-positive |
| C5 super + pyramid | MGC | +0.612 | 1.02 | -0.002 | +0.073 | skew-flat |
| C5 super + pyramid | SIL | -0.617 | 0.97 | -0.043 | +0.069 | skew-flat |

Payoff-shape annotation per [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) using L-skewness τ_3 = λ_3/λ_2 per Hosking 1990 *JRSS B* 52(1):105-124 JSTOR 2345653 (project-operational cutoff ±0.1). Universally either `skew-flat` or `skew-positive`; **no `skew-negative` configurations** — H055's ATR-scaled TP/SL truncates left-tail risk by construction.

### Table 9 — Methodological-correctness annotations

`leakage-canary-deferred-v2` · `bss-n/a` (continuous directional signal not probability forecast) · `reliability-n/a` · `repro-log-present` (sidecar SHA + git_head + substrate SHA bound) · `dsr-n/a` (M=1 single-cell) · `cost-zero-v1-pre-cost-research-only` (per operator standing directive 2026-05-08; binding tracked under `P1-H055-COST-EMPIRICAL-CALIBRATION`)

**Methodological caveats specific to v1 implementation** (documented inline in the sidecar):
- **Entry-fill simplification**: v1 simulator enters at `confirmation_bar + 1` open, NOT at the wick-extreme limit price specified in H055 design.md §4. The simplified entry **admits more trades** than the limit-fill semantic (next-bar-open always fills if there's a bar; limit-at-wick fills only on adverse touches). Tracked under follow-up `P1-H055-LIMIT-FILL-WICK-EXTREME` (BLOCKING-BEFORE-PRODUCTION-WALK-FORWARD per design.md §11.2).
- **Single-cell hyperparameter grid**: v1 uses a single fixed cell (trend_id="a"; L=60; tau_m=1.0; rho_n=10; atr_n=14; theta_wick_min=1.5; swing_window=5; alpha_tp=2.0; beta_sl=1.5; k_swing_5min=30 = 2.5 hours). H055 design.md §5.6 specifies full Optuna TPE search; v1 deferred. Tracked under `P1-H055-OPTUNA-INNER-CV-IMPL`.
- **rho_star gate = 0.0 (PLACEHOLDER)**: H055 design.md §5.2 specifies calibration-holdout quantile selection. v1 disables the gate (admits all setups). Tracked under `P1-H055-CALIBRATION-HOLDOUT-RUN-PRODUCE-RHO-STAR-BINDING`.
- **News-calendar OFF**: v1 disables FOMC/NFP/CPI exclusion for clean baseline. Production must re-enable per [src/skie_ninja/utils/news_calendar.py](../../../src/skie_ninja/utils/news_calendar.py) (`P1-H055-NEWS-CALENDAR-INGEST` already CLOSED 2026-05-14; v2 just disables to compare).
- **Calmar denominator uses absolute max-DD fraction** per [src/skie_ninja/inference/calmar.py](../../../src/skie_ninja/inference/calmar.py) `max_drawdown_fraction`; this matches ADR-0017 §1 convention.
- **MPPM input semantic fix R1**: arithmetic per-session returns are passed to `mppm_rho_1` (which internally applies log1p), NOT pre-logged values. R1 audit catch (F-1-9) corrected in commit pre-emission.

## §3 Bottom line (≤ 8 sentences)

The H055 v1 baseline (fixed-equity quarter-Kelly) **fails to generate trades on ES + NQ at $10K starting equity** — the fractional-Kelly × $10K / $300-$1,000-per-1R-cost ratio floors to 0 contracts; the v1 sizing is non-viable on equity-index futures at retail-tier capital. The C2 full-Kelly + current-equity-rebase variant unlocks the trade-generation pipeline on all 4 symbols, producing a basket +18.4% realized OOS and +4.1% sub-window — with **MGC carrying the basket** (+72.4% realized). The C3 super-Kelly km=2.0 variant pushes basket ROI to +19.7% but with **catastrophic per-symbol variance** (NQ -21.1%; SIL -10.1%; MGC +87.0%) and **basket sub-window -4.4%** — super-Kelly amplifies both upside and tail. The C9 BOCD step-up variant moderates the variance — basket +12.1% OOS, +2.5% sub-window — by adapting Kelly down on decay detection; this is the **survival-constrained sweet spot** under ADR-0017 + ADR-0018. The C5 super-Kelly + Turtle-2 pyramid variant is **the worst overall** at -6.6% basket OOS — pyramiding amplifies losses asymmetrically on losing instruments (ES -53.5%; SIL -46.6%) while only modestly helping winning instruments (MGC +77.2% vs C3 +87.0%). **Primary recommendation** (operator-discretionary per ADR-0013 §1): C9 BOCD step-up is the load-bearing variant for any forward consideration; C5 pyramiding is **declined for paper-trade** at v1 evidence level. The next mandatory stage transition per ADR-0013 §5 is `kpi-report-emitted` → `ninjascript-implemented`; per operator's 2026-05-04 standing decline-ninjascript directive, this transition is operator-discretionary and **may reasonably be declined** given (a) MGC carrying basket performance suggests instrument-class-specific edge, not strategy-class edge; (b) ES/NQ produced zero or marginal returns under all aggressive variants; (c) the v1 sizing/entry-fill simplifications introduce known optimistic bias.

## §4 Methodological annotations summary

`leakage-canary-deferred-v2` · `bss-n/a` · `reliability-n/a` · `repro-log-present` · `dsr-n/a` (M=1) · `cost-zero-v1-pre-cost-research-only` · `cpcv-not-applied-single-path-wf` (deferred to production) · `power-margin-not-computed-v1` · `payoff-shape-skew-{flat,positive}` (uniformly; no skew-negative) · `mppm-positive` (C2 MGC+NQ; C3 ES+MGC; C9 MGC; C5 MGC) · `mppm-negative` (C3 NQ; C9 NQ; C5 ES+SIL; v1 SIL) · `super-kelly-operator-discretionary` (C3 km=2.0; C5 km=2.0) · `cost-empirical-deferred` · `forward-projection-deferred-v2`

## §5 Cross-reference + audit trail

- Pre-registration: [research/01_hypothesis_register/H055/design.md](design.md) (frozen 2026-05-06 `status: designed`).
- v0 skeleton: [H055_kpi_report_v0.md](H055_kpi_report_v0.md) (placeholder; superseded by this v1).
- v2 sweep sidecar: [artifacts/runs/H055/v2_sweep_20260516T025924Z/sweep_sidecar.json](../../../artifacts/runs/H055/v2_sweep_20260516T025924Z/sweep_sidecar.json) (SHA `83cd09e88476b93d...`).
- KPI metrics table: [artifacts/runs/H055/v2_sweep_20260516T025924Z/kpi_metrics_table.md](../../../artifacts/runs/H055/v2_sweep_20260516T025924Z/kpi_metrics_table.md).
- Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-15_h055_v2.md](../../../docs/audits/audit_trail_2026-05-15_h055_v2.md).
- Implementing script: [scripts/run_h055_v2_sweep.py](../../../scripts/run_h055_v2_sweep.py).
- Substrate: vendor_legacy_1min_roll_adjusted SHA `b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce` (2026-05-15 right-edge).
- Stage tracker: [stage.md](stage.md) (transition `exploration-in-progress` → `kpi-report-emitted` recorded inline upon emission).
- Failure log: [failure_log.md](failure_log.md) (5 R1 audit findings remediated; documented in audit_trail).

## §6 Next mandatory transition

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §5: `kpi-report-emitted` → `ninjascript-implemented`.

Per operator 2026-05-04 standing decline-ninjascript directive + [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §5.3 operator-discretionary clause, this transition is operator-discretionary upon canonical-format presentation. **Operator recommendation** (based on this v1 KPI emission): defer NinjaScript progression pending (i) full Optuna TPE walk-forward (`P1-H055-OPTUNA-INNER-CV-IMPL`), (ii) limit-fill semantic correction (`P1-H055-LIMIT-FILL-WICK-EXTREME`), (iii) realistic cost-model calibration (`P1-H055-COST-EMPIRICAL-CALIBRATION`), and (iv) forward-projection + risk-of-ruin computation (`P1-H055-FORWARD-PROJECTION-COMPUTE`). If operator authorizes immediate NinjaScript progression, the load-bearing variant is **C9 BOCD step-up** (best survival-constrained profile); C5 pyramid is declined.

H055 stage remains `kpi-report-emitted` upon emission of this v1 report card; per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1 non-loss mandate, this v1 report card is the canonical record and is preserved verbatim; any future v2 KPI emission will create a successor `H055_kpi_report_v2.md` without modifying this file.
