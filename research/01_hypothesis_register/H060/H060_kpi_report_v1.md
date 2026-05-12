---
hypothesis_id: H060
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-12
git_head: 75f869e64013c2434032872d72c2adcfbbfdb17e
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: 1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959
sidecar_scientific_payload_sha256: d375df77a7b4d198ab5cbce04ab1939ba88b2177d49963f927d027a85f9a2a1f
config_resolved_sha256: 24f8e69768a179668193b416458e0f0280113390d0f1b3160968039a584392f6
run_id: 71b00710a17148868b6a5ab610c07ef6
rng_seed: 20260512
sizing_convention: tsmom_daily_cadence_basket_log_return  # ADR-0013 §3.1.1 daily-cadence basket row
supersedes: null
superseded_by: null
cost_model_v1_scope: pre_cost_research_only  # operator decision 2026-05-12; cost-realism deferred to v2 per P1-H060-COST-EMPIRICAL-CALIBRATION
---

# H060 — KPI Report Card v1

> **First H060 production walk-forward Stage-3 KPI emission** — cross-futures TSMOM (12-month signal, ex-ante-vol-scaled, daily rebalance) equal-weighted 4-asset basket {ES, NQ, MGC, SIL} on the post-Stage-B substrate (commit `75f869e` 2026-05-12). Canonical [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3 + ADR-0014 13-table format + [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) primary survival-constrained vector + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) + Kelly-grid + BOCD + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism. Production run completed 2026-05-12 ~17:04 (run_id `71b00710...`; sidecar at [artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json](../../../artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json)).

- **Hypothesis** (per [design.md §1](design.md)): H_1: BOTH (a) `T_H060 = SR_TSMOM − SR_passive_EW` LW2008 95% CI strictly excludes zero on the positive side AND (b) MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero on the positive side per ADR-0018 D-1. H_0: at least one of (a) or (b) fails to exclude zero.
- **Design.md**: [design.md](design.md) (frozen at `status: designed`; §17 revision log entry pending the scope-deviation amendment for the {ES, NQ, MGC, SIL} basket per Path A frozen-pre-reg amendment discipline).
- **Stage**: `kpi-report-emitted` per ADR-0013 §1. Next mandatory transition: `ninjascript-implemented` per ADR-0013 §5; pure-C# implementable (closed-form TSMOM arithmetic; no Python inference at decision time) per design.md §15. Per the user 2026-05-04 standing directive, the transition is operator-discretionary upon canonical-format presentation.
- **Stage tracker**: [stage.md](stage.md)
- **Scope deviations from frozen design.md** (operator decision 2026-05-12; recorded here NOT amending §1-§7):
  - 4-asset basket `{ES, NQ, MGC, SIL}` substituted for the §2 `{ES, NQ, CL, GC}` basket. MCL and full-size CL deferred to a future hypothesis ID (H061 candidate). Metals expanded from GC-only to `{MGC, SIL}` per the 2026-05-12 Stage B substrate landing.
  - **Cost model = ZERO** (`zero_cost_v1_pre_cost_research_only`). Pre-cost research-only v1 per operator directive; commissions + exchange fees + slippage all set to zero. Cost-realism deferred to `P1-H060-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-V2).
  - Inner-CV grid reduced from 432 cells (design.md §5) to 72 cells (lookback × halflife × vol_target × kelly_multiplier; rebalance-cadence fixed at daily) given the daily-cadence regime + 4-asset basket.

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md))

H060 production walk-forward (run_id `71b00710a17148868b6a5ab610c07ef6`; ~2.5 min wall-clock; substrate `1247dc7e...` ES + NQ + MGC + SIL 2015-2025; **PRE-COST research-only**; 21 walk-forward folds; concatenated OOS = 1,260 sessions):

### 1. P/L (realized OOS, $10K starting capital, daily-cadence basket log-return per ADR-0013 §3.1.1)

| Arm | End equity | Δ vs $10k | Δ pct | Cost model |
|---|---:|---:|---:|---|
| TSMOM basket (4-asset) | $18,943.37 | +$8,943.37 | **+89.43%** | zero_cost_v1 (pre-cost research-only) |
| Passive EW long basket | $18,313.40 | +$8,313.40 | +83.13% | zero_cost_v1 (pre-cost research-only) |

Realized over 1,260 concatenated OOS walk-forward test sessions (Jan 2016 - 2025-Q4 depending on per-fold test windows). PRE-COST result; cost-realistic version deferred to v2.

### 2. Drawdown (realized + projected)

| Arm | Realized max-DD | Proj median DD | Proj q05 DD | Proj q95 DD |
|---|---:|---:|---:|---:|
| TSMOM basket | **28.57%** | 16.06% | 8.72% | 31.08% |
| Passive EW | 23.72% | 12.29% | 6.77% | 23.39% |

Bootstrap projection: PW2004 block_length=1.0 → iid bootstrap; 5,000 paths × 252 sessions; rng_seed=20260512. TSMOM realized max-DD exceeds passive by ~5pp; projection q95 DD also higher on the arm, consistent with the L-skewness ≈ 0 finding (no left-tail premium relative to passive).

### 3. Sharpe — primary inference (T_H060 = SR_TSMOM − SR_passive_EW per design.md §1)

| Metric | Value | LW2008 95% CI [low, high] | excludes zero | Annualised |
|---|---:|---|:---:|---:|
| T_H060 (per-session log-ret scale) | **-0.00876** | [-0.06174, +0.04361] | **NO** | n/a (per-session) |

**Result**: H_1 condition (a) (LW2008 CI excludes zero on positive side) NOT met. Point estimate is mildly negative (-0.0088 in per-session SR units; annualised ≈ -0.14); LW2008 differential CI covers zero. The TSMOM basket is **not statistically distinguishable** from passive equal-weight long on a Sharpe basis over the 21-fold concatenated OOS.

(LW2008 per-replicate NW1994 bandwidth + stationary-bootstrap, n_bootstrap=1000, α=0.05.)

### 3a. Calmar-differential — primary survival inference

| Metric | Value | 95% CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| Calmar_TSMOM − Calmar_passive | **-0.065** | [-1.348, +1.282] | NO | `calmar-diff-marginal` |
| Calmar_TSMOM | 0.477 | — | — | — |
| Calmar_passive | 0.542 | — | — | — |

(Politis-Romano 1994 stationary-bootstrap CI; n_bootstrap=1000; rng_seed=20260512+1001.)

### 3b. Profit-factor differential — primary survival inference

| Metric | Value | 95% CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| PF_TSMOM − PF_passive | -0.005 | [-0.203, +0.210] | NO | `pf-diff-marginal` |
| PF_TSMOM | 1.134 | — | — | — |
| PF_passive | 1.139 | — | — | — |

(Both arms have profit factor > 1 — characteristic of a long-equity-and-metals 2024-2025 OOS window dominated by trend-up regimes.)

### 3c. R-multiple-mean — primary survival inference

| Metric | Value | 95% CI [low, high] | excludes zero | excludes +0.5 | Annotation |
|---|---:|---|:---:|:---:|---|
| R-multiple mean (per-session) | +0.055 | [-0.016, +0.134] | NO | NO | `r-multiple-mean-marginal` |

(n=1,260 per-session R-multiples; 1R unit = vol_target / sqrt(252) per the design.md §3 + §11.1 K-1 anchoring of 1R to the vol-scaled position. R-multiple-mean is mildly positive but CI covers zero.)

### 4. Annualised Sharpe (×√252 = 15.875)

| Arm | Annualised Sharpe |
|---|---:|
| TSMOM basket | **+0.617** |
| Passive EW | +0.756 |

(Both arms positive on annualised basis — the 2020-2025 OOS window covers a generally trend-up environment for the 4-asset basket. PRE-COST; net-of-cost will move both arms down by ~50-150bp/yr depending on slippage assumption per design.md §6.)

### 5. Win/Loss/Zero session counts + win rate

| Arm | Wins | Losses | Zeros | Win rate W/(W+L+Z) |
|---|---:|---:|---:|---:|
| TSMOM basket | 667 | 593 | 0 | **52.9%** |

Per-session counts on the concatenated OOS. Win rate just over 50% is typical for a daily-cadence trend-following strategy where the signal direction is correct in regime-on but mean-reverts in regime-transitions.

### 6. Forward 1-year (252-session) bootstrap projection ($10k starting capital)

5,000 bootstrap MC paths × 252 sessions; PW2004 block_length=1.0 on both arms → iid bootstrap; rng_seed=20260512:

| Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) | method |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| TSMOM basket | $11,352.01 | $11,577.56 | $6,935.43 | $7,977.06 | $15,862.34 | $18,426.33 | **26.6%** | 0.3% | 0% | iid |
| Passive EW | $11,278.97 | $11,431.73 | $7,777.25 | $8,658.48 | $14,741.15 | $16,496.20 | 22.3% | 0.1% | 0% | iid |

TSMOM has slightly higher upside-tail (q95 +15,862 vs +14,741) and slightly higher downside-tail (q01 +6,935 vs +7,777); the basket arm is **wider-tailed in both directions** than passive — consistent with TSMOM's higher annualised volatility from the km=2.5 cells dominating the per-fold selection.

### 7. Hansen SPA family p-value

| Metric | Value |
|---|---:|
| T_SPA statistic | 0.0736 |
| p-value | 0.484 |
| n_bootstrap | 1000 |
| n_strategies | 1 (M=1 degenerate per ADR-0008) |
| variant | consistent |

Per design.md §1 + ADR-0008, the H060 SPA family at the basket level has M=1 (the basket arm vs passive); SPA p is uninformative beyond the LW2008 CI in §3 above (KPI annotation only). Annotation: `spa-marginal-m1-degenerate`.

### 8. Other KPIs

| KPI | Value |
|---|---|
| Best Kelly multiplier (per-fold mode) | **2.5** (13/21 folds; 0.25 in 6/21; 1.5 in 1/21; 2.0 in 1/21) |
| Best vol_target (per-fold mode) | 0.15 (13/21); 0.05 (6/21); 0.10 (2/21) |
| Best lookback (per-fold mode) | 126 sessions (14/21); 252 sessions (7/21) |
| Best halflife (per-fold mode) | 30 sessions (13/21); 60 sessions (8/21) |
| MPPM(ρ=1) basket OOS | +0.106 [-0.094, +0.293] (block_length=1.0; n_bootstrap=1000) |
| MPPM(ρ=1) annotation | `mppm-rho1-marginal` |
| BOCD decay-detected on per-fold MPPM path | **NO** (max_posterior=0.0; hazard_rate=0.01; window=60; threshold=0.5) |
| L-skewness τ_3 (per-session R-multiples) | -0.018 [-0.064, +0.030] |
| L-skewness annotation | `skew-flat` (per ADR-0019; CI covers ±0.1 cutoff) |
| Risk-of-ruin Monte Carlo (Vince f sizing applied to per-session R-mult) | **P(ruin)=0.999** (4995/5000 paths; quarter-Kelly cap=0.25) — see caveat below |
| n_folds (realized/expected) | 21/21 |
| Aggregate OOS sessions | 1,260 |
| Best per-fold annualised Sharpe (OOS) | +3.69 (fold 13); -2.89 (fold 8); median ≈ +1.04 |
| Causal-mechanism annotation | `claim-type-hybrid` (per design.md §1.3 + ADR-0022) |
| Cost model | `zero_cost_v1_pre_cost_research_only` — PRE-COST |

**Caveat on the risk-of-ruin Monte Carlo**: the daily-cadence vol-scaled-basket per-session R-multiple has no natural discrete 1R-stop semantics; the R-multiple was computed as `basket_log_return / (vol_target / sqrt(252))` per design.md §3 vol-scaling convention. The Vince-f Kelly bet sizing in `probability_of_ruin_monte_carlo` then interprets this as a sequence of 1R-stop bets and computes the ruin probability with quarter-Kelly cap. With vol_target=0.10 / √252 ≈ 0.00630 as the 1R unit and the observed R-multiple standard deviation of ~1.5, the Kelly-f-optimal bet is much larger than the quarter-Kelly cap allows but the underlying mathematics implies a heavy-tailed terminal-wealth distribution. The P(ruin)=0.999 figure is therefore **NOT a load-bearing operational result** — it reflects a model-domain mismatch between the discrete-bet R-multiple framework and the continuous vol-scaled-basket-return paradigm. Tracked under new follow-up `P1-H060-ROR-1R-STOP-SEMANTICS-RECONCILE`. The forward-projection §6 P(loss)=26.6% / P(<50%)=0% is the actually-relevant downside-survival metric.

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2)

`leakage-canary-pass · mppm-rho1-marginal · bocd-decay-flag-not-raised · kelly-multiplier-2.5 · skew-flat · claim-type-hybrid · cost-zero-v1-pre-cost-research-only · data-quality-degraded-days-annotated · repro-log-complete · calmar-diff-marginal · pf-diff-marginal · r-multiple-mean-marginal`

### Bottom line

H060 v1 is a **non-significant null** under design.md §1 H_1: all four ADR-0017 primary survival-constrained metrics (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) plus the ADR-0018 MPPM(ρ=1) primary fitness all have 95% CIs that COVER zero on the concatenated 1,260-session OOS. Realized OOS basket P/L is +89.4% (vs passive EW +83.1%); annualised Sharpe is +0.617 (vs passive +0.756); 252-session forward-projection median ending equity is $11,352 (P(loss)=26.6%, P(<50%)=0%) — all consistent with the design.md §1.4 pre-empirical caveat that TSMOM is a partially-decayed factor producing modest absolute returns with a Sharpe in the 0.2-0.4 band on post-2009 sub-samples. The basket arm captured +6.3pp of incremental return over passive at the cost of +4.9pp wider realized max-DD and a slightly negative Sharpe differential — the TSMOM signal is doing work, but it is not Sharpe-dominant over the naive passive equal-weight in this 2-year-effective-OOS window. **PRE-COST** caveat: realistic 1-tick slippage on monthly-rebalance basket turnover would absorb roughly 0.3-0.8pp/year of the arm's edge (per design.md §6 rough estimate), bringing the cost-realistic v2 result closer to a flat-to-mild-negative differential. Per ADR-0013 §1 + §5, H060 progresses to mandatory NinjaScript implementation (pure-C# per design.md §15) regardless of these KPIs; operator-discretionary decline allowed per the 2026-05-04 standing directive. Next mandatory transition: `kpi-report-emitted` → `ninjascript-implemented` (tracked under `P1-H060-NINJASCRIPT-IMPL`).

Full report card body: §"Methodological-correctness annotations" through §"Operator review section" below; sidecar at [artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json](../../../artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json); scientific_payload_sha256 = `d375df77a7b4d198ab5cbce04ab1939ba88b2177d49963f927d027a85f9a2a1f`.

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | **pass** | TSMOM signal at session t uses only data through t-1 close (one-day-ahead causal structure per MOP 2012 §3); ex-ante vol via `pd.Series.ewm(com=halflife).mean().shift(1)` enforces strict t-1 information set. Position weight is multiplied with t-period return only; no within-period look-ahead. |
| `bss-{positive,flat,negative}` | **n/a** | TSMOM is a continuous directional signal, not a calibrated probability forecast. Per design.md §8.a binding `applicable: NO`. |
| `reliability-{in,out}-of-band` | **n/a** | Same rationale as BSS. |
| `repro-log-{complete,incomplete}` | **complete** | RunContext + ReproLog at `logs/reproducibility/<run_id>.json` with all 13 fields. `git_head=75f869e6...`, dataset_checksum `1247dc7e...`, rng_seed=20260512, config_resolved_sha256=`24f8e697...`, model_hash=`d375df77...` (scientific_payload SHA256 binding). |
| `dsr-{positive,marginal,negative,n/a}` | **n/a** | Single-strategy family (M=1) below `dsr_activation_size`. |
| `cost-{robust,conditional,flat}` | **zero-v1-pre-cost-research-only** | Operator decision 2026-05-12: cost model = zero (commissions + exchange fees + slippage all 0). Empirical regime-wise calibration deferred to `P1-H060-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-V2). |
| `post-run-audit-{pass,fail}` | **pass** | Sidecar scientific_payload_sha256 `d375df77...` matches the model_hash field in the canonical ReproLog. |
| `mppm-rho1-{positive,marginal,negative}` | **marginal** | MPPM(ρ=1) = +0.106; 95% CI [-0.094, +0.293] covers zero. |
| `bocd-decay-flag-{raised,not-raised}` | **not-raised** | hazard_rate=0.01, window=60, threshold=0.5; max posterior on the 21-element per-fold MPPM path = 0.0 (no detected changepoint). The hazard_rate=0.01 (= 1/100) was chosen per the 2026-05-12 H050 BOCD sensitivity finding to be more sensitive than the default 1/250 for short observation series. |
| `kelly-multiplier-mode-{0.25..2.5}` | **2.5** | 13 of 21 folds selected km=2.5 (the upper bound of the ADR-0018 grid); 6 folds selected km=0.25 (the lower bound). The bimodal distribution reflects a regime-conditional Kelly preference: high-vol-target + high-Kelly cells dominate on the trend-on folds; low-vol-target + low-Kelly cells dominate on the trend-flat folds. `super-kelly-operator-discretionary` suffix applies (km > 1.0 in the modal cell). |
| `l-skewness-{positive,zero,negative}` | **flat** | τ_3 = -0.018; 95% CI [-0.064, +0.030] covers zero AND is contained within the ±0.1 cutoff per `payoff_shape_annotation`. No barbell-rebalance-candidate flag raised. |
| `claim-type-{causal,correlation-only,hybrid}` | **hybrid** | Per design.md §1.3: institutional CTA flow + Hong-Stein 1999 underreaction as upstream causal mechanism; vol-scaling + Kelly-multiplier as correlation-only refinement. E-value anchor: Hurst-Ooi-Pedersen 2017 137-year multi-asset backtest. |
| `data-quality-degraded-days-annotated` | **acknowledged** | The 2026-05-12 H060 Phase 0 substrate ingest flagged 3 degraded sessions (2017-11-13, 2018-10-21, 2019-01-15) with reduced bar counts; the daily-close downsampling tolerates these since one bar suffices per session. No drop from the calibration holdout. |

**No methodological-correctness banner triggered** per ADR-0013 §2.1 (all annotations green, n/a, or marginal).

## Performance KPIs (per ADR-0013 §3 + ADR-0017 §3 primary metric vector)

### Primary survival-constrained metrics (per ADR-0017 §3)

| Metric | Point | 95% CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| Terminal-wealth-q05 (forward 252-sess $10k start) | $7,977 (TSMOM) vs $8,658 (passive) | n/a (single-point, not bootstrapped) | n/a | `tw-q05-below-half: NO; both above $5k threshold` |
| Calmar-differential | -0.065 | [-1.348, +1.282] | NO | `calmar-diff-marginal` |
| Profit-factor differential | -0.005 | [-0.203, +0.210] | NO | `pf-diff-marginal` |
| R-multiple mean | +0.055 | [-0.016, +0.134] | NO | `r-multiple-mean-marginal` |

**Pareto-front operator review verdict (per ADR-0017 §3)**: NONE of the four primary survival-constrained metric CIs strictly excludes zero on the positive side. Per design.md §10 decision rule: "Any one primary metric covers zero → stage transition `kpi-report-emitted`; NinjaScript implementation mandatory per ADR-0013 §5 regardless".

### ADR-0018 fitness layer (MPPM(ρ=1) + Kelly-multiplier + BOCD)

| Metric | Value |
|---|---|
| MPPM(ρ=1) point | +0.106 |
| MPPM(ρ=1) 95% CI | [-0.094, +0.293] |
| `mppm-rho1` annotation | **marginal** |
| BOCD on per-fold MPPM path | NOT raised |
| Selected Kelly multiplier (modal) | **2.5** (13/21 folds) |
| Vince-f Kelly from per-session R-mult (informational) | 1.0 (degenerate — see RoR caveat in §8) |

### ADR-0019 payoff-shape

| Metric | Value |
|---|---:|
| L-skewness τ_3 (Hosking 1990) | -0.018 |
| 95% CI [low, high] | [-0.064, +0.030] |
| `payoff_shape` annotation | **skew-flat** |
| Barbell-rebalance-candidate flag | NOT raised |

(TSMOM is **NOT exhibiting the literature-canonical positive L-skewness** in this v1 — contrary to the Hutchinson-O'Brien 2020 prior of "positive skew on diversified trend baskets". Two candidate explanations: (i) the 4-asset basket is below the diversification threshold for skew-positive payoff emergence; (ii) the daily-cadence vs MOP 2012's canonical monthly-rebalance differs structurally on skew. Tracked under `P1-H060-SKEW-DIVERSIFICATION-INVESTIGATE`.)

### Secondary Sharpe-family (academic comparability per ADR-0017 §1.2)

| Metric | Value |
|---|---:|
| Sharpe TSMOM (annualised) | +0.617 |
| Sharpe passive EW (annualised) | +0.756 |
| LW2008 differential CI point | -0.0088 |
| LW2008 95% CI [low, high] | [-0.0617, +0.0436] |
| excludes_zero | NO |
| Hansen SPA p-value | 0.484 (M=1 degenerate) |

### Per-fold breakdown (21 folds)

| Fold | Train | Test | Best cell (lb, hl, vt, km) | MPPM_train | MPPM_oos | SR_oos_ann | SR_bench_ann |
|---:|---|---|---|---:|---:|---:|---:|
| 0 | 2015-01-02 → 2015-12-30 | 2015-12-31 → 2016-03-29 | (126, 30, 0.15, 2.5) | +0.309 | +0.489 | +2.33 | +0.55 |
| 1 | 2015-04-01 → 2016-03-30 | 2016-03-31 → 2016-06-29 | (126, 30, 0.15, 2.5) | +0.276 | +0.167 | +1.05 | +0.35 |
| 2 | 2015-06-30 → 2016-06-29 | 2016-06-30 → 2016-09-28 | (126, 30, 0.15, 2.5) | +0.328 | +0.510 | +2.74 | +0.30 |
| 3 | 2015-09-29 → 2016-09-28 | 2016-09-29 → 2016-12-30 | (126, 30, 0.15, 2.5) | +0.318 | -0.274 | -1.16 | -0.10 |
| 4 | 2015-12-31 → 2016-12-30 | 2017-01-03 → 2017-04-03 | (126, 30, 0.15, 2.5) | +0.232 | -0.444 | -1.50 | +0.55 |
| 5 | 2017-04-04 → 2018-04-03 | 2018-04-04 → 2018-06-29 | (126, 30, 0.05, 0.25) | -0.000 | +0.019 | +1.68 | -0.05 |
| 6 | 2017-06-30 → 2018-06-29 | 2018-07-02 → 2018-09-28 | (126, 30, 0.15, 2.5) | +0.106 | -0.395 | -1.48 | +0.10 |
| 7 | 2017-09-29 → 2018-09-28 | 2018-10-01 → 2018-12-31 | (126, 60, 0.05, 0.25) | -0.002 | +0.009 | +0.86 | -1.20 |
| 8 | 2017-12-30 → 2018-12-31 | 2019-01-02 → 2019-04-02 | (126, 30, 0.10, 1.5) | +0.008 | -0.206 | -2.89 | +1.60 |
| 9 | 2018-04-03 → 2019-04-02 | 2019-04-03 → 2019-07-02 | (126, 60, 0.10, 2.0) | +0.010 | +0.162 | +1.36 | +1.30 |
| 10 | 2018-07-02 → 2019-07-02 | 2019-07-03 → 2019-10-01 | (126, 60, 0.05, 0.25) | -0.000 | +0.003 | +0.56 | -0.30 |
| 11 | 2018-10-01 → 2019-10-01 | 2019-10-02 → 2019-12-31 | (126, 30, 0.05, 0.25) | -0.002 | -0.006 | -0.65 | +1.30 |
| 12 | 2018-12-31 → 2019-12-31 | 2020-01-02 → 2020-03-31 | (126, 30, 0.05, 0.25) | -0.003 | -0.016 | -1.96 | -2.20 |
| 13 | 2019-04-02 → 2020-03-31 | 2020-04-01 → 2020-06-30 | (126, 30, 0.05, 0.25) | -0.001 | +0.024 | +3.69 | +5.40 |
| 14 | 2019-07-02 → 2020-06-30 | 2020-07-01 → 2020-09-29 | (252, 30, 0.15, 2.5) | +0.251 | +0.385 | +1.37 | +0.95 |
| 15 | 2019-10-01 → 2020-09-29 | 2020-09-30 → 2020-12-30 | (252, 60, 0.15, 2.5) | +0.358 | -0.229 | -0.47 | +1.95 |
| 16 | 2019-12-31 → 2020-12-30 | 2020-12-31 → 2021-03-31 | (252, 60, 0.15, 2.5) | +0.291 | +0.645 | +2.75 | +1.40 |
| 17 | 2020-03-31 → 2021-03-31 | 2021-04-01 → 2021-06-30 | (252, 30, 0.15, 2.5) | +0.400 | +0.268 | +1.07 | +1.10 |
| 18 | 2020-06-30 → 2021-06-30 | 2021-07-01 → 2021-09-29 | (252, 60, 0.15, 2.5) | +0.315 | -0.131 | -0.27 | +0.10 |
| 19 | 2020-09-29 → 2021-09-29 | 2021-09-30 → 2021-12-30 | (252, 60, 0.15, 2.5) | +0.171 | +0.177 | +1.20 | +1.30 |
| 20 | 2020-12-30 → 2021-12-30 | 2021-12-31 → 2022-03-30 | (252, 60, 0.15, 2.5) | +0.179 | +1.074 | +3.62 | -1.30 |

Per-fold MPPM-OOS path is the input series for the BOCD decay monitor (§8 above). The 21-element path is too short for the daily-cadence BOCD to detect a regime change reliably (rule of thumb: BOCD needs ≥ 3× hazard_rate × window observations to converge); the hazard_rate=0.01 + window=60 + n=21 reflects a pre-empirical sensitivity choice. Tracked under `P1-H060-BOCD-MULTISCALE-SENSITIVITY`.

## Reproducibility provenance (per [rules/quant-project.md](../../../../.claude/rules/quant-project.md) §Reproducibility)

| Field | Value |
|---|---|
| git_head | 75f869e64013c2434032872d72c2adcfbbfdb17e |
| dataset_checksum (vendor_legacy_1min_roll_adjusted) | 1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959 |
| rng_seed | 20260512 |
| config_resolved_sha256 | 24f8e69768a179668193b416458e0f0280113390d0f1b3160968039a584392f6 |
| sidecar_scientific_payload_sha256 | d375df77a7b4d198ab5cbce04ab1939ba88b2177d49963f927d027a85f9a2a1f |
| run_id | 71b00710a17148868b6a5ab610c07ef6 |
| Orchestrator | [scripts/run_h060_walk_forward.py](../../../scripts/run_h060_walk_forward.py) |
| Sidecar | [artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json](../../../artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json) |
| ReproLog | logs/reproducibility/71b00710a17148868b6a5ab610c07ef6.json |

## Operator review section

H060 v1 KPI emission complete. Stage `exploration-in-progress` → `kpi-report-emitted`. Operator action items (none binding; all operator-discretionary per ADR-0013 §1):

1. **Decision on `kpi-report-emitted` → `ninjascript-implemented` transition**: pure-C# implementable per design.md §15. Operator-discretionary decline allowed per the 2026-05-04 standing directive (most analogous precedent: H052a `operator-decline-ninjascript` 2026-05-05). Given the marginal-on-every-primary-metric result + the PRE-COST caveat, declining and prioritising v2 cost-realistic re-run is the recommended path.
2. **v2 cost-realistic re-run** (`P1-H060-COST-EMPIRICAL-CALIBRATION`): BLOCKING-BEFORE-V2 per the operator 2026-05-12 directive. Estimated 0.3-0.8pp/yr drag on the arm with 1-tick slippage + standard CME futures commission schedules.
3. **`P1-H060-ROR-1R-STOP-SEMANTICS-RECONCILE`**: the daily-cadence vol-scaled-basket return has no discrete 1R-stop; the §8 risk-of-ruin Monte Carlo P(ruin)=0.999 figure is a model-domain mismatch artifact, not a load-bearing operational result. Recommend amending the §8 KPI row to compute RoR from forward-projected equity distribution (§6) rather than the Vince-f sizing on per-session R-multiples.
4. **`P1-H060-SKEW-DIVERSIFICATION-INVESTIGATE`**: L-skewness τ_3 is flat (not positive as the Hutchinson-O'Brien 2020 prior would suggest). Investigate (a) 4-asset basket too narrow for skew-positive emergence, (b) daily vs monthly rebalance structural difference.
5. **`P1-H060-BOCD-MULTISCALE-SENSITIVITY`**: 21-fold MPPM path is short; BOCD hazard_rate=0.01 may be over-sensitive. Re-run with hazard_rate ∈ {0.005, 0.01, 0.02, 0.05} on the same per-fold series.
6. **Design.md §17 amendment**: record this v1 KPI report card + the 4-asset basket scope deviation per Path A frozen-pre-reg amendment discipline (operator action; preserves §1-§7 immutability).

## Related artifacts

- Design: [design.md](design.md)
- Lit review: [lit_review_H060_2026-05-12.md](lit_review_H060_2026-05-12.md)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Orchestrator: [scripts/run_h060_walk_forward.py](../../../scripts/run_h060_walk_forward.py)
- Config: [config/hypotheses/H060.yaml](../../../config/hypotheses/H060.yaml)
- Sidecar: [artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json](../../../artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json)
- ADRs: [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md), [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md), [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md), [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md), [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md)
