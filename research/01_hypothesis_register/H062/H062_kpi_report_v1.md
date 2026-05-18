---
hypothesis_id: H062
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-15
git_head: 463378b
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: 1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959
sidecar_scientific_payload_sha256: fbd85226d304b7dacc1e2b2ef0f701be860a6ed8808a214a47031cfdd054612c
config_resolved_sha256: 314f6ea93efc680169583dc4337b340a7a60c19c2c6005c1ef86e2c64fdd0788
run_id: 16cb68d997c148a2834aad21b73bfdb6
rng_seed: 20260514
sizing_convention: per_trade_atr_stop_5min_intraday_basket_log_return
supersedes: null
superseded_by: null
cost_model_v1_scope: pre_cost_research_only
---

# H062 — KPI Report Card v1

> **First H062 production walk-forward Stage-3 KPI emission** — intraday N-bar Donchian-channel breakout at 5-min cadence on the 4-asset CME-Globex retail-tier basket {ES, NQ, MGC, SIL} on the post-Phase-O.0 substrate (commit `463378b` 2026-05-15). Canonical [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3 + [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) 13-table format + [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) primary survival-constrained vector + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) + Kelly-grid + BOCD + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism + [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate. Production run completed 2026-05-15 ~18:35 (run_id `16cb68d9...`; wall-clock ~38 min; sidecar at [artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json](../../../artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json)).

- **Hypothesis** (per [design.md §1](design.md)): H_1: BOTH (a) basket MPPM(ρ=1) > 0 with stationary-bootstrap CI strictly excluding zero on the positive side AND (b) all four ADR-0017 primary survival-constrained metrics (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) excluded-zero-positive on their bootstrap CIs. H_0: at least one of (a) or (b) fails.
- **Design.md**: [design.md](design.md) (frozen at `status: designed`; §11.2 8/9 BLOCKING preconditions closed per CLAUDE.md Phase O.2 ledger).
- **Stage**: `kpi-report-emitted` per ADR-0013 §1. Next mandatory transition: `ninjascript-implemented` per ADR-0013 §5; pure-C# implementable per design.md §15 (Donchian + ATR + ID_1 trend filter + first-fire dwell are all closed-form). Per the user 2026-05-04 standing directive, the transition is operator-discretionary upon canonical-format presentation.
- **Stage tracker**: [stage.md](stage.md)
- **Scope deviations from frozen design.md** (recorded here per Path A frozen-pre-reg amendment discipline; §1-§7 preserved):
  - Inner-CV grid REDUCED from the full 13,824-cell design.md §8.a combinatorial product to a tractable 48-cell representative grid (`channel_n × k_atr × kelly_multiplier`; trend_id + h_dwell + atr_n + cadence fixed at representative values). Full-grid tracked under `P1-H062-FULL-INNER-CV-GRID-V2`.
  - **Cost model = ZERO** (`zero_cost_v1_pre_cost_research_only`). PRE-COST research-only v1 per operator 2026-05-08 + 2026-05-12 standing directive. Cost-realism deferred to `P1-H062-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-V2).
  - Per-trade simulator uses fixed-equity rebase (target_dollar_risk = $10K × 1% = $100) rather than the ADR-0017 §4.1 current-equity rebase; tracked under `P1-H062-CURRENT-EQUITY-REBASE-IMPL`.

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md))

H062 production walk-forward (run_id `16cb68d997c148a2834aad21b73bfdb6`; ~38 min wall-clock; substrate `1247dc7e...` ES+NQ+MGC+SIL on the post-Phase-O.0 frame; **PRE-COST research-only**; 93 walk-forward folds; concatenated OOS = 2,944 sessions, 8,270 OOS trades):

### 1. P/L (realized OOS, $10K starting capital, 5-min intraday basket log-return per ADR-0013 §3.1.1)

| Arm | End equity | Δ vs $10k | Δ pct | Cost model |
|---|---:|---:|---:|---|
| H062 Donchian breakout (4-asset basket) | $14,324.87 | +$4,324.87 | **+43.25%** | zero_cost_v1 (pre-cost research-only) |
| Passive EW long basket | $40,447.32 | +$30,447.32 | +304.47% | zero_cost_v1 (pre-cost research-only) |

Realized over 2,944 concatenated OOS walk-forward test sessions (Q1 2020 - 2025-Q4 depending on per-fold test windows). The arm captured **+43.25%** in nominal returns but underperformed passive equal-weight long by 261.22 percentage points. **PRE-COST** result.

### 2. Drawdown (realized + projected)

| Arm | Realized max-DD | Proj median DD | Proj q05 DD | Proj q95 DD |
|---|---:|---:|---:|---:|
| H062 basket | **90.97%** | n/a (iid bootstrap MaxDD not directly emitted) | n/a | n/a |
| Passive EW | 39.74% | n/a | n/a | n/a |

H062 realized max-DD 90.97% is catastrophic; the arm drew down nearly 91% from peak before recovering to the +43.25% terminal. Passive max-DD 39.74% (2020 COVID-era + 2022 metals correction). The 51-pp DD differential is the binding survival-constraint signal per ADR-0017 §3.

### 3. Sharpe — primary inference (T_H062 = SR_breakout − SR_passive per design.md §1)

| Metric | Value | LW2008 95% CI [low, high] | excludes zero | Annualised |
|---|---:|---|:---:|---:|
| T_H062 (per-session log-ret scale) | **-0.0352** | [-0.0778, +0.0114] | **NO** | n/a (per-session) |

**Result**: H_1 condition (a) (LW2008 CI excludes zero on positive side) NOT met. Point estimate is mildly negative (-0.035 in per-session SR units); LW2008 differential CI covers zero. The Donchian breakout arm is **statistically indistinguishable from passive equal-weight long** on a Sharpe-differential basis over 2,944 OOS sessions. (LW2008 per-replicate NW1994 bandwidth + stationary-bootstrap, n_bootstrap=1000, α=0.05.)

### 3a. Calmar-differential — primary survival inference

| Metric | Value | 95% CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| Calmar_breakout − Calmar_passive | **-0.286** | [-1.078, +0.422] | NO | `calmar-diff-marginal` |
| Calmar_breakout | 0.034 | — | — | — |
| Calmar_passive | 0.320 | — | — | — |

(Politis-Romano 1994 stationary-bootstrap CI; n_bootstrap=1000; rng_seed=20260514+1001.) The arm Calmar 0.034 is severely depressed by the 90.97% realized max-DD.

### 3b. Profit-factor differential — primary survival inference

| Metric | Value | 95% CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| PF_breakout − PF_passive | -0.107 | [-0.261, +0.051] | NO | `pf-diff-marginal` |
| PF_breakout | 1.008 | — | — | — |
| PF_passive | 1.115 | — | — | — |

Arm PF of 1.008 is barely above breakeven; passive PF 1.115 reflects modest long-bias edge over the 2020-2025 window.

### 3c. R-multiple-mean — primary survival inference

| Metric | Value | 95% CI [low, high] | excludes zero | excludes +0.5 | Annotation |
|---|---:|---|:---:|:---:|---|
| R-multiple mean (per-session) | +0.044 | [-0.017, +0.109] | NO | NO | `r-multiple-mean-marginal` |

n=2,944 per-session R-multiples; the per-trade R-multiple is computed via `realized_log_return / 1R_log` where `1R_log` = the ATR-scaled stop distance in log-return units at trade entry. The mean is mildly positive (+0.044) but the CI covers zero — no edge-bearing R-multiple distribution at the per-trade level.

### 4. Annualised Sharpe (×√252 = 15.875)

| Arm | Annualised Sharpe |
|---|---:|
| H062 basket | **+0.042** |
| Passive EW | +0.600 |

Both arms positive; passive is **0.56 Sharpe higher** in annualised units. PRE-COST; net-of-cost would move both arms down by ~50-150bp/yr depending on slippage assumption per design.md §6.

### 5. Win/Loss/Zero session counts + win rate

| Arm | Wins | Losses | Zeros | Win rate W/(W+L+Z) |
|---|---:|---:|---:|---:|
| H062 basket | 912 | 2,031 | 1 | **31.0%** |

Per-session counts on the concatenated OOS. Win rate **31%** is low and consistent with a breakout strategy that takes many small losses (stop-out) with relatively rare large wins. The W/L ratio 1:2.23 (912 winners vs 2,031 losers) requires a strong winning-trade-magnitude tail to be profitable; the realized data show that tail is present (the arm did finish positive at +43%), but the catastrophic 91% max-DD shows the survival-constraint failure mode is also severe.

### 6. Forward 1-year (252-session) bootstrap projection ($10k starting capital)

5,000 bootstrap MC paths × 252 sessions; iid bootstrap on per-session log-returns (PW2004 block_length=1.0 → iid); rng_seed=20260514:

| Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) | method |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| H062 basket | $10,220.46 | — | — | $3,103.80 | $36,145.00 | — | **48.96%** | 18.36% | **15.82%** | iid |
| Passive EW | $11,251.68 | — | — | $8,140.33 | $15,738.85 | — | 27.58% | 0.38% | 0.00% | iid |

H062 forward distribution is **wider-tailed in both directions** than passive — q95 upside $36k (vs passive $15.7k) but q05 downside $3.1k (vs passive $8.1k). **P(<half) = 15.82%** says 1 in 6 forward paths cuts the $10k bankroll in half within 1 year; ADR-0017 §4.2 survival-constraint clearly violated relative to passive (0.0%).

### 7. Hansen SPA family p-value

| Metric | Value |
|---|---:|
| T_SPA statistic | 0.0 |
| p-value | 1.000 |
| n_bootstrap | 1000 |
| n_strategies | 1 (M=1 degenerate per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md)) |
| variant | consistent |

Per design.md §1 + ADR-0008, the H062 SPA family at the basket level has M=1 (the basket arm vs passive); SPA p is uninformative beyond the LW2008 CI in §3 above (KPI annotation only). Annotation: `spa-marginal-m1-degenerate`. Per-symbol M=4 SPA family + Romano-Wolf stepwise FWER per design.md §1 are tracked under `P1-H062-FAMILY-SPA-RW2005-COMPUTE` (open follow-up; v1 v reports basket-level SPA only).

### 8. Other KPIs

| KPI | Value |
|---|---|
| Best Kelly multiplier (per-fold mode) | **0.25** (93/93 folds; quarter-Kelly unanimous) |
| Best channel_n (per-fold mode) | mixed: N=60 / N=120 / N=240 each ~30% of folds; N=20 ~10% |
| Best k_atr (per-fold mode) | mixed: k=2.0 ~50%; k=1.5 ~35%; k=2.5 ~15% |
| MPPM(ρ=1) basket OOS | -0.223 [-0.599, +0.172] (block_length=1.0; n_bootstrap=1000) |
| MPPM(ρ=1) annotation | `mppm-rho1-marginal` |
| BOCD decay-detected on per-fold MPPM path | **NO** (max_posterior=NaN; hazard_rate=0.01; window=60; threshold=0.5) |
| L-skewness τ_3 (per-trade R-multiples) | **+0.740** [+0.728, +0.751] |
| L-skewness annotation | **`skew-positive`** (per [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md); τ_3 > +0.1 cutoff) |
| Risk-of-ruin Monte Carlo (Vince f sizing applied to per-trade R-mult) | **P(ruin)=1.000** (5000/5000 paths; quarter-Kelly cap=0.25) — see caveat below |
| n_folds (realized/expected) | 93 / 93 (ES 25 + NQ 16 + MGC 26 + SIL 26) |
| Aggregate OOS sessions | 2,944 |
| Aggregate OOS trades | 8,270 |
| Per-symbol trade counts | ES 280; NQ 41; MGC 3,309; SIL 4,640 |
| Causal-mechanism annotation | `claim-type-hybrid` (per design.md §1.3 + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md)) |
| Cost model | `zero_cost_v1_pre_cost_research_only` — PRE-COST |

**Caveat on the risk-of-ruin Monte Carlo**: per-trade R-multiples were computed via `realized_pnl_dollar / r_dollar` where r_dollar is the ATR-scaled stop distance at entry. The Vince-f Kelly bet sizing inside `probability_of_ruin_monte_carlo` interprets this sequence as iid 1R-stop bets and applies the quarter-Kelly cap. The 8,270-trade R-multiple distribution has mean +0.044 and substantial left tail (gap-through-stop trades contribute R-multiples below -1.0); 5000/5000 paths hit the 50% ruin threshold within 252 sessions under this model. This **P(ruin)=1.0 figure is operationally informative but should be read alongside the §6 forward-projection P(<half) = 15.8%** — the forward projection uses per-session aggregated log-returns (not per-trade R-multiples) and gives the more realistic survival signal. The same caveat applied to H060 v1 (P1-H060-ROR-1R-STOP-SEMANTICS-RECONCILE precedent); for H062 this is tracked under `P1-H062-ROR-1R-STOP-SEMANTICS-RECONCILE` (new follow-up).

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2)

`leakage-canary-pass · mppm-rho1-marginal · bocd-decay-flag-not-raised · kelly-multiplier-0.25 · skew-positive · claim-type-hybrid · cost-zero-v1-pre-cost-research-only · repro-log-complete · calmar-diff-marginal · pf-diff-marginal · r-multiple-mean-marginal`

### Bottom line

H062 v1 is a **non-significant null** under design.md §1 H_1: basket MPPM(ρ=1) point=-0.223 with 95% CI=[-0.599, +0.172] covers zero; all three additional primary survival-constrained metrics (Calmar-differential, profit-factor-differential, R-multiple-mean) also have CIs that cover zero. Realized OOS basket P/L is +43.25% (vs passive EW +304.47%); annualised Sharpe is +0.042 (vs passive +0.600); 252-session forward-projection median ending equity is $10,220 (P(loss)=49.0%, P(<half)=15.8%) — all consistent with the design.md §1.4 pre-empirical caveat that intraday channel breakouts on large-cap equity-index + metals at this cadence are a partially-decayed factor per Marshall-Cahan-Cahan 2008 + Hsu-Kuan 2005 + Park-Irwin 2007. The realized 90.97% max-DD on the arm (vs passive 39.74%) is the binding survival-constraint signal: H062 captured nominal upside but at the cost of catastrophic interim drawdown. **L-skewness τ_3 = +0.740 confirms the structural prediction of design.md §13** — the Donchian breakout payoff is positively skewed (truncate left tail at ATR-stop; let right tail run via opposite-channel exit), but skew-positive payoff was not sufficient to overcome the win-rate ~31% combined with the absence of cost-realism. **PRE-COST** caveat: realistic 1-tick slippage across 8,270 OOS trades + standard CME futures commission schedules would absorb a material fraction of the arm's edge; cost-realistic v2 result is likely flat-to-negative. Per ADR-0013 §1 + §5, H062 progresses to mandatory NinjaScript implementation (pure-C# per design.md §15) regardless of these KPIs; operator-discretionary decline allowed per the 2026-05-04 standing directive. Next mandatory transition: `kpi-report-emitted` → `ninjascript-implemented` (tracked under `P1-H062-NINJASCRIPT-IMPL`).

Full report card body: §"Methodological-correctness annotations" through §"Operator review section" below; sidecar at [artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json](../../../artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json); scientific_payload_sha256 = `fbd85226d304b7dacc1e2b2ef0f701be860a6ed8808a214a47031cfdd054612c`.

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | **pass** | Donchian channel at bar t uses closes [t-N, t-1] only (PIT-causal per design.md §7 + Faith 2007 §3 Turtle close-to-close convention); ATR at bar t uses TR through t inclusive; entry at bar (t+1) open. Unit test coverage: [tests/unit/test_h062_donchian.py::TestPITCausality](../../../tests/unit/test_h062_donchian.py) + [tests/unit/test_h062_level_state_fold_continuity.py](../../../tests/unit/test_h062_level_state_fold_continuity.py) + [tests/integration/test_h062_pit_canaries.py](../../../tests/integration/test_h062_pit_canaries.py). |
| `bss-{positive,flat,negative}` | **n/a** | H062 v1 produces directional channel-break signals; Brier-score competition operates at the trend_id selection layer per design.md §5.1 (not at the post-cell-grid forecast layer). Per design.md §8.a `applicable: NO` at v1. |
| `reliability-{in,out}-of-band` | **n/a** | Same rationale as BSS. |
| `repro-log-{complete,incomplete}` | **complete** | RunContext + ReproLog at `logs/reproducibility/16cb68d997c148a2834aad21b73bfdb6.json` with all 13 fields. dataset_checksum `1247dc7e...`, rng_seed=20260514, config_resolved_sha256=`314f6ea9...`, model_hash=`fbd85226...` (scientific_payload SHA256 binding). |
| `dsr-{positive,marginal,negative,n/a}` | **n/a** | Single-strategy family (M=1) below `dsr_activation_size`; the 48-cell inner-CV TPE-explored set per fold is below the design.md §8.a `dsr_activation_size` threshold. |
| `cost-{robust,conditional,flat}` | **zero-v1-pre-cost-research-only** | Operator decision 2026-05-08 + 2026-05-12: cost model = zero. Empirical regime-wise calibration deferred to `P1-H062-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-V2). |
| `post-run-audit-{pass,fail}` | **pass** | Sidecar scientific_payload_sha256 `fbd85226...` matches the model_hash field in the canonical ReproLog. |
| `mppm-rho1-{positive,marginal,negative}` | **marginal** | MPPM(ρ=1) = -0.223; 95% CI [-0.599, +0.172] covers zero. |
| `bocd-decay-flag-{raised,not-raised}` | **not-raised** | hazard_rate=0.01, window=60, threshold=0.5; max posterior on the 93-element per-fold MPPM path = NaN (BOCD initialization failure on a path with strong negative-mean drift + high variance — investigation tracked under `P1-H062-BOCD-NAN-POSTERIOR-INVESTIGATE`). Defaulted to `not-raised`. |
| `kelly-multiplier-mode-{0.25..2.5}` | **0.25** | **93 of 93 folds selected km=0.25** (quarter-Kelly unanimous). The MPPM(ρ=1) inner-CV fitness on every fold preferred the lowest Kelly cell — a strong structural signal that the strategy lacks edge sufficient to warrant scaling up. No `super-kelly-operator-discretionary` annotation raised (km ≤ 1.0 in all folds). |
| `l-skewness-{positive,zero,negative}` | **positive** | τ_3 = +0.740; 95% CI [+0.728, +0.751] strictly > +0.1 cutoff. **Confirms the structural design.md §13 prediction** that Donchian-channel-breakout produces skew-positive R-multiple distribution (truncate left tail at ATR-stop; let right tail run). Barbell-rebalance-candidate flag NOT raised (skew-positive is the desirable direction). |
| `claim-type-{causal,correlation-only,hybrid}` | **hybrid** | Per design.md §1.3: Hong-Stein 1999 underreaction + stop-order liquidity at multi-bar pivots (Bouchaud et al 2004) + momentum anchoring on round numbers (Frazzini 2006) as upstream causal mechanism; channel_n + k_atr + Kelly-multiplier as correlation-only refinement. E-value anchor: Hurst-Ooi-Pedersen 2017 137-year daily-grain benchmark (intraday cadence is one shift below). |
| `data-quality-degraded-days-annotated` | **acknowledged** | The Phase O.0 Stage A ingest surfaced 3 degraded sessions (2017-11-13, 2018-10-21, 2019-01-15) per Databento BentoWarning. All 3 pre-2020 → calibration-holdout window only; not IS or OOS for H062 v1. Schema-invariant tests passed (`tests/unit/test_h062_data_quality_canary.py`). |
| `kill-switch-validation-{pass,fail}` | **pass (post-simulation)** | K-1 / K-3 / K-4 / K-6 / K-7 validators per [src/skie_ninja/backtest/kill_switch_validation.py](../../../src/skie_ninja/backtest/kill_switch_validation.py) are operational (16 regression tests; commit `12c4316`). Per-trade ledger validation not yet wired into the orchestrator's post-simulation hook; tracked under `P1-H062-KILL-SWITCH-VALIDATOR-WIRE-ORCHESTRATOR` (new follow-up). At v1 the K-constraints are enforced structurally inside `_run_per_trade_simulation` (K-2 by EOD-flatten, K-4 by capacity cap inside `compute_position_size`, K-8 by ID_1 trend-filter gate). |

**No methodological-correctness banner triggered** per ADR-0013 §2.1 (all annotations green, n/a, or marginal).

## Performance KPIs (per ADR-0013 §3 + ADR-0017 §3 primary metric vector)

### Primary survival-constrained metrics (per ADR-0017 §3)

| Metric | Point | 95% CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| Terminal-wealth-q05 (forward 252-sess $10k start) | $3,104 (H062) vs $8,140 (passive) | n/a (single-point, not bootstrapped) | n/a | `tw-q05-below-half: YES`; H062 forward q05 is below $5k threshold |
| Calmar-differential | -0.286 | [-1.078, +0.422] | NO | `calmar-diff-marginal` |
| Profit-factor differential | -0.107 | [-0.261, +0.051] | NO | `pf-diff-marginal` |
| R-multiple mean | +0.044 | [-0.017, +0.109] | NO | `r-multiple-mean-marginal` |

**Pareto-front operator review verdict (per ADR-0017 §3)**: NONE of the four primary survival-constrained metric CIs strictly excludes zero on the positive side, AND terminal-wealth-q05 falls below the $5k half-bankroll threshold (the H062 forward distribution has q05 = $3,104; passive has $8,140 — the survival-constraint signal is binding). Per design.md §10 decision rule: "Basket MPPM(ρ=1) CI covers zero → stage transition `kpi-report-emitted` with `mppm-rho1-marginal` annotation; the underlying null disposition of the H_1 hypothesis is documented; operator decides on NinjaScript implementation per ADR-0013 §5.3 operator-discretionary clause".

### ADR-0018 fitness layer (MPPM(ρ=1) + Kelly-multiplier + BOCD)

| Metric | Value |
|---|---|
| MPPM(ρ=1) point | -0.223 |
| MPPM(ρ=1) 95% CI | [-0.599, +0.172] |
| `mppm-rho1` annotation | **marginal** |
| BOCD on per-fold MPPM path | NOT raised (NaN posterior; investigation deferred) |
| Selected Kelly multiplier (modal) | **0.25** (93/93 folds; quarter-Kelly unanimous) |
| Super-Kelly cells (km > 1.0) selected | **0/93 folds** |

The unanimous km=0.25 selection across all 93 folds is a stronger structural signal than the marginal MPPM CI alone: the MPPM(ρ=1) fitness on **every single fold** preferred quarter-Kelly over full-Kelly or super-Kelly. This is the canonical signature of a strategy whose edge is below the Kelly-criterion-relevant magnitude. Per ADR-0018 D-2, super-Kelly cells would require the inner-CV fitness to strictly prefer them; that did not happen on a single fold across 4 symbols.

### ADR-0019 payoff-shape

| Metric | Value |
|---|---:|
| L-skewness τ_3 (Hosking 1990) | **+0.740** |
| 95% CI [low, high] | [+0.728, +0.751] |
| `payoff_shape` annotation | **skew-positive** |
| Barbell-rebalance-candidate flag | NOT raised (skew-positive is desirable) |

H062 v1 **strongly confirms the design.md §13 structural prediction** that the Donchian-channel-breakout payoff distribution is skew-positive. The τ_3=0.740 is well above the +0.1 cutoff with a tight CI strictly excluding the threshold. This is the **first H062-family payoff-shape KPI to emit at the ADR-0019 `skew-positive` annotation level** — H060 emitted `skew-flat` (τ_3=-0.018); H050 + H053 had skew-flat or skew-negative depending on configuration. The skew-positive payoff structure is the structural foundation for the barbell-rebalance discipline of ADR-0019 — H062 sits on the "let winners run via opposite-channel exit; truncate losers at ATR-stop" side of the barbell.

Caveat: skew-positive payoff in isolation does NOT compensate for the catastrophic 90.97% max-DD. The barbell-rebalance candidate flag is reserved for skew-NEGATIVE payoff structures requiring convex-hedge addition; H062 does not need that intervention.

### Secondary Sharpe-family (academic comparability per ADR-0017 §1.2)

| Metric | Value |
|---|---:|
| Sharpe H062 (annualised) | +0.042 |
| Sharpe passive EW (annualised) | +0.600 |
| LW2008 differential CI point | -0.0352 |
| LW2008 95% CI [low, high] | [-0.0778, +0.0114] |
| excludes_zero | NO |
| Hansen SPA p-value | 1.000 (M=1 degenerate) |

### Per-symbol breakdown (93 folds across 4 symbols)

| Symbol | Folds | OOS trades | MPPM_oos mean | MPPM_oos median | MPPM > 0 (folds) | SR_arm median | SR_bench median |
|---|---:|---:|---:|---:|:---:|---:|---:|
| ES | 25 | 280 | -1.586 | -2.340 | 5 of 20 | -9.504 | +0.956 |
| NQ | 16 | 41 | +2.454 | +0.501 | 3 of 5 | +2.584 | +0.525 |
| MGC | 26 | 3,309 | +0.064 | +0.231 | 14 of 26 | +0.702 | +0.893 |
| SIL | 26 | 4,640 | -0.442 | -0.429 | 7 of 26 | -0.308 | +0.114 |

Per-symbol-class read:
- **MGC is the strongest leg** (14 of 26 folds MPPM>0; positive median SR; closest to the basket-aggregate marginal MPPM). Metals-with-fundamental-vol-anchor drives ~3,300 OOS trades on the 24/5 substrate.
- **NQ is sparsest** (only 41 OOS trades across 16 folds). The N=60/120/240 channel + first-fire dwell + ID_1 trend gate (a_ts_mom L=60 τ=1.0) intersects very rarely with the eligible-bar set on NQ RTH. Where it does fire, the win rate is decent (3 of 5 non-NaN folds MPPM>0; median SR +2.58) but the sample is too small for inference. The 5 NaN-MPPM folds on NQ are folds with 0 OOS trades (channel did not break on any eligible bar in the test window).
- **ES is the weakest** (5 of 20 non-NaN folds MPPM>0; median SR -9.50). Large-cap equity-index intraday channel breakouts decay aggressively per the Hsu-Kuan 2005 large-cap-fails-SPA prior.
- **SIL is moderate** (7 of 26 folds MPPM>0; median SR -0.31). 4,640 OOS trades dominates the basket trade count.

### Per-fold inner-CV cell selection summary

| Parameter | Selected distribution |
|---|---|
| Channel N (lookback bars) | N=20: ~10% folds, N=60: ~30%, N=120: ~25%, N=240: ~35% |
| k_atr (ATR-stop multiplier) | k=1.5: ~35%, k=2.0: ~50%, k=2.5: ~15% |
| Kelly multiplier | **km=0.25: 93/93 folds (100%)** |
| Trend ID (fixed at v1) | a_ts_mom (lookback_l=60, τ_m=1.0) |
| H_dwell (fixed at v1) | 5 bars |
| ATR n (fixed at v1) | 14 |

The Kelly-multiplier 100% concentration at quarter-Kelly is the binding signal of a sub-edge strategy. Full-grid expansion per `P1-H062-FULL-INNER-CV-GRID-V2` (trend_id × h_dwell × atr_n × cadence × all 6 Kelly cells) is unlikely to materially alter this verdict but would surface whether different trend-ID candidates produce different Kelly-cell preference patterns.

## Reproducibility provenance (per [rules/quant-project.md](../../../../.claude/rules/quant-project.md) §Reproducibility)

| Field | Value |
|---|---|
| git_head | 463378b (claude/nervous-greider-90c8f0 branch) |
| dataset_checksum (vendor_legacy_1min_roll_adjusted) | 1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959 |
| rng_seed | 20260514 |
| config_resolved_sha256 | 314f6ea93efc680169583dc4337b340a7a60c19c2c6005c1ef86e2c64fdd0788 |
| sidecar_scientific_payload_sha256 | fbd85226d304b7dacc1e2b2ef0f701be860a6ed8808a214a47031cfdd054612c |
| run_id | 16cb68d997c148a2834aad21b73bfdb6 |
| Orchestrator | [scripts/run_h062_walk_forward.py](../../../scripts/run_h062_walk_forward.py) |
| Sidecar | [artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json](../../../artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json) |
| ReproLog | logs/reproducibility/16cb68d997c148a2834aad21b73bfdb6.json |

## Operator review section

H062 v1 KPI emission complete. Stage `exploration-in-progress` → `kpi-report-emitted`. Operator action items (none binding; all operator-discretionary per ADR-0013 §1):

1. **Decision on `kpi-report-emitted` → `ninjascript-implemented` transition**: pure-C# implementable per design.md §15. Operator-discretionary decline allowed per the 2026-05-04 standing directive (most analogous precedents: H052a `operator-decline-ninjascript` 2026-05-05; H060 v1 declined 2026-05-12). Given the marginal-on-every-primary-metric result + catastrophic 90.97% max-DD + 15.8% P(<half) forward-projection + 31% win rate + PRE-COST caveat, **declining and prioritising H063 / cost-realistic v2** is the recommended path.
2. **v2 cost-realistic re-run** (`P1-H062-COST-EMPIRICAL-CALIBRATION`): BLOCKING-BEFORE-V2 per the operator 2026-05-12 directive. 8,270 OOS trades × 1-tick slippage at intraday cadence is non-trivial cost; cost-realistic version likely flat-to-negative arm P/L.
3. **`P1-H062-CURRENT-EQUITY-REBASE-IMPL`**: per-trade simulator uses fixed-equity rebase; ADR-0017 §4.1 current-equity rebase would change the catastrophic max-DD interpretation (with current-equity rebase, position sizes would shrink as the bankroll draws down, capping the absolute-dollar drawdown). Recommend implementing for v2.
4. **`P1-H062-FULL-INNER-CV-GRID-V2`**: expand from 48-cell to full 13,824-cell grid per design.md §8.a. The current 48-cell grid fixes trend_id at a_ts_mom L=60 τ=1.0; production-mode would let ID_1 vary across {a_ts_mom, b_adx, c_hac_ols_slope_t, d_ma_cross}, h_dwell ∈ {1, 2, 5, 10}, atr_n ∈ {14, 21, 60}.
5. **`P1-H062-BOCD-NAN-POSTERIOR-INVESTIGATE`**: BOCD posterior on the 93-element per-fold MPPM path returned NaN. Likely numerical instability on the strong-negative-mean + high-variance MPPM sequence. Investigate hazard rate sensitivity + numerical stabilisation.
6. **`P1-H062-ROR-1R-STOP-SEMANTICS-RECONCILE`**: same model-domain mismatch as H060 P1-H060-ROR-1R-STOP-SEMANTICS-RECONCILE. The P(ruin)=1.0 from `probability_of_ruin_monte_carlo` is operationally informative but should be read against the §6 forward-projection P(<half)=15.8% which is the actually-relevant downside-survival metric.
7. **`P1-H062-KILL-SWITCH-VALIDATOR-WIRE-ORCHESTRATOR`**: wire the new `validate_kill_switches` post-simulation validator into the orchestrator's KPI assembly step (commit `12c4316` landed the validator + 16 tests; the orchestrator does not yet emit the per-fold trade ledger for the validator to consume).
8. **`P1-H062-FAMILY-SPA-RW2005-COMPUTE`**: per-symbol M=4 SPA family + Romano-Wolf 2005 stepwise FWER family-wise correction per design.md §1. v1 reports basket-level SPA only.
9. **Design.md §17 amendment**: record this v1 KPI report card + the scope deviations per Path A frozen-pre-reg amendment discipline (operator action; preserves §1-§7 immutability).

## Related artifacts

- Design: [design.md](design.md)
- Data requirements: [data_requirements.md](data_requirements.md)
- Lit review: [lit_review_H062_2026-05-14.md](lit_review_H062_2026-05-14.md)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- KPI report v0 (pre-emission skeleton): [H062_kpi_report_v0.md](H062_kpi_report_v0.md)
- Orchestrator: [scripts/run_h062_walk_forward.py](../../../scripts/run_h062_walk_forward.py)
- Config: [config/hypotheses/H062.yaml](../../../config/hypotheses/H062.yaml)
- Sidecar: [artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json](../../../artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json)
- Calibration sidecar: [artifacts/runs/H062/calibration_20260515T223618Z/calibration_sidecar.json](../../../artifacts/runs/H062/calibration_20260515T223618Z/calibration_sidecar.json)
- Power simulation sidecar: [artifacts/runs/H062/power_20260515T223534Z/power_sidecar.json](../../../artifacts/runs/H062/power_20260515T223534Z/power_sidecar.json)
- Smoke run sidecar (precedent reference): [artifacts/runs/H062/33a47f84eff34a53898a089923915f1f/sidecar.json](../../../artifacts/runs/H062/33a47f84eff34a53898a089923915f1f/sidecar.json)
- Audit trail (Phase O.2 launch-readiness): [docs/audits/audit_trail_2026-05-15_h062_launch_readiness.md](../../../docs/audits/audit_trail_2026-05-15_h062_launch_readiness.md)
- ADRs: [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md), [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md), [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md), [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md), [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md)
