---
hypothesis_id: H060
schema_version: hypothesis_design_v1
status: designed
tier: 2b
created: 2026-05-12
created_by: skoir
description: Pre-registered design doc for hypothesis H060 — cross-futures time-series momentum (TSMOM) on equal-weighted CME basket {ES, NQ, CL, GC} under the Phase N survival-constrained / MPPM(ρ=1) / Kelly-grid / BOCD-decay / barbell payoff-shape / causal-mechanism paradigm.
---

# H060 — Cross-futures time-series momentum (TSMOM) on {ES, NQ, CL, GC}

> **Canonical TSMOM construction on a 4-asset CME-Globex retail-tier basket.** H060 applies the [Moskowitz, Ooi, Pedersen 2012, *JFE* 104(2):228-250](https://doi.org/10.1016/j.jfineco.2011.11.003) (henceforth "MOP 2012") time-series-momentum construction — 12-month look-back signal × ex-ante volatility scaling × monthly rebalance — to the equal-weighted basket of E-mini S&P 500 (ES), E-mini Nasdaq-100 (NQ), NYMEX WTI Light Sweet Crude (CL), and COMEX Gold (GC) front-month roll-adjusted continuous contracts.
>
> **Full Phase N paradigm inheritance.** H060 is the first post-Phase-N hypothesis pre-registered under the unified survival-constrained / MPPM(ρ=1) / Kelly-grid / BOCD-decay / barbell payoff-shape / causal-mechanism stack: [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) primary metric vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) inner-CV fitness + Kelly-multiplier grid + BOCD signal-decay monitor + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness annotation + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism annotation + [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate.
>
> **Daily-cadence — NOT bar-cadence.** TSMOM at the canonical monthly-rebalance horizon on daily-close bars is structurally a different regime from the bar-cadence intraday strategies (H050, H052a, H053, H054, H055). The H050 catastrophic-drawdown failure mode under HMM-gated 1-min ES/NQ is one empirical anchor for the daily-cadence choice: bar-cadence trend-following on equity-index futures was demonstrated by H050 KPI report card v1 to produce realised -81%/-84% on the gated arms; daily-cadence TSMOM avoids that pathology by construction (MOP 2012 §2.1 baseline construction; Hurst-Ooi-Pedersen 2017 137-year backtest at monthly cadence).

## 1. Hypothesis

- **H_0**: The TSMOM (12-month signal, ex-ante-vol-scaled, monthly rebalance) equal-weighted 4-asset portfolio over {ES, NQ, CL, GC} does NOT produce a Sharpe-vs-passive-equal-weighted-long differential whose 95% LW2008 studentized stationary-bootstrap CI excludes zero on the 2024-2025 OOS test fold; AND the primary fitness function MPPM(ρ=1) per [Ingersoll, Spiegel, Goetzmann, Welch 2007, *RFS* 20(5):1503-1546](https://doi.org/10.1093/rfs/hhm025) does NOT exceed zero with a stationary-bootstrap CI excluding zero per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1.
- **H_1**: BOTH (a) the Sharpe-differential 95% LW2008 CI strictly excludes zero on the positive side AND (b) MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero on the positive side per ADR-0018 D-1. Promotion-decision-rule layer is governed by [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3 Pareto-front operator review across the four primary survival-constrained metrics (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean); the Sharpe-differential + MPPM(ρ=1) entries above are the load-bearing INFERENTIAL family entries (§8 KPI annotation grammar). Sharpe-family CI is reported per the project's standing inference convention but is secondary KPI per ADR-0017.
- **Predictand**: per-asset signed log-return over the rebalance horizon (monthly default; grid-searched per §5). TSMOM portfolio return at session t is `r_TSMOM,t = Σ_i w_{i,t-1} · r_{i,t}` where `w_{i,t-1}` is the vol-scaled signed position computed at the prior close (one-day-ahead causal structure per MOP 2012 §3).
- **Test statistic** (load-bearing): `T_H060_basket = SR_TSMOM − SR_passive_EW` evaluated under [Ledoit & Wolf 2008, *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap CI with block length per [Politis & White 2004, *Econometric Reviews* 23(1):53-70](https://doi.org/10.1081/ETC-120028836) + [Patton, Politis & White 2009, *Econometric Reviews* 28(4):372-375](https://doi.org/10.1080/07474930802459016) correction; per-asset SR differentials (`SR_TSMOM_i − SR_passive_i`) reported as sibling family entries under Benjamini-Hochberg FDR at α=0.05 per the project's standing convention. Hansen 2005 SPA p reported as KPI annotation per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-and-m1-degenerate.md) (KPI-only at M=4 family size; not load-bearing for H_1).

### 1.3 Causal-mechanism vs correlation-only annotation (per ADR-0022)

- **Claim type**: `hybrid` (upstream causal mechanism on the long-horizon signal; correlation-only refinement on the vol-scaling and Kelly-multiplier layers).
- **Mechanism description (who/what/why/when)**:
  - **WHO**: institutional commodity-trading-advisors (CTAs) + risk-parity funds + retail trend-followers. Aggregate AUM in systematic-trend strategies estimated at ~$300-500B globally per the SocGen CTA Index + BarclayHedge CTA universe; long-only risk-parity AUM (which embeds long-horizon momentum-like rebalancing) several × larger.
  - **WHAT**: programmatic position-flow into existing trends on slow rebalance horizons (monthly typical), often vol-target-scaled to a fixed annualised volatility budget (10% canonical per MOP 2012; 15% on AQR-Trend-style products).
  - **WHY**: (i) institutional mandate to "be in the trade" once trend has been established (career risk + tracking-error mandate); (ii) underreaction to long-horizon news per [Hong & Stein 1999, *J Finance* 54(6):2143-2184](https://doi.org/10.1111/0022-1082.00184) gradual-information-diffusion model; (iii) anchoring + disposition-effect-induced delayed price discovery on slow-moving fundamentals per [Frazzini 2006, *J Finance* 61(4):2017-2046](https://doi.org/10.1111/j.1540-6261.2006.00896.x); (iv) risk-parity rebalance amplifies persistence on the high-Sharpe / low-vol assets.
  - **WHEN**: persistent across regimes per [Hurst, Ooi, Pedersen 2017, *J Portfolio Management* 44(1):15-29](https://doi.org/10.3905/jpm.2017.44.1.015) 137-year multi-asset backtest (1880-2016). Regime-dependent / time-varying per the momentum-crashes literature ([Daniel & Moskowitz 2016, *JFE* 122(2):221-247](https://doi.org/10.1016/j.jfineco.2015.12.002)) — momentum is structurally vulnerable to sharp regime-reversal crashes coincident with low-vol-state-followed-by-large-positive-market-jump dynamics; this is the structural ADR-0019 payoff-shape risk explicitly anticipated below.
- **E-value / robustness anchor**: Hurst-Ooi-Pedersen 2017 137-year multi-asset backtest is the canonical out-of-sample robustness exhibit; rough magnitude E-value equivalent ≥ 3.0 (an unmeasured confounder would need to produce an RR-equivalent of ≥ 3 across 137 years of multi-asset data to nullify the observed effect; the 137-year persistence is itself the load-bearing primary-source verification per ADR-0022).

### 1.4 Pre-empirical caveat: TSMOM is a partially-decayed factor, not a strong-non-decayed-edge prior

This v1 is framed honestly as a **partially-decayed-factor test**, NOT a "strong non-decayed edge" wager. Three load-bearing primary sources document substantial post-publication TSMOM decay:

- [Huang, Li, Wang & Zhou 2020, *J Financial Economics* 137(3):695-712](https://doi.org/10.1016/j.jfineco.2020.04.003) reports that TSMOM predictability fails bootstrap-resampling tests on out-of-sample data when correctly accounting for time-series dependence; the canonical Moskowitz-Ooi-Pedersen 2012 result is weakened substantially under their robustness diagnostics.
- [Baltas & Kosowski 2013 *SSRN 1968996*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1968996) "Demystifying Time-Series Momentum Strategies: Volatility Estimators, Trading Rules and Pairwise Correlations" documents that post-2008 the cross-asset correlation structure of the canonical TSMOM basket has degraded its diversification benefit; the headline 1985-2009 basket Sharpe ~1.0 falls to ~0.4-0.6 in post-2008 sub-samples.
- The SocGen Trend Index (a real-money tradeable practitioner benchmark of systematic CTA trend programs) realized Sharpe ≈ 0.0 over 2009-2018 — a decade of near-zero returns to live trend-following capital. This is the load-bearing *practitioner* counter-anchor: the post-publication regime where TSMOM has been actively traded by sophisticated capital has produced approximately zero risk-adjusted return.

Expected basket Sharpe under H_1 is therefore framed at **0.2-0.4 annualized** (not the canonical MOP 2012 1985-2009 ~1.0), with MPPM(ρ=1) > 0 on the inferential CI the load-bearing test rather than a Sharpe-vs-MOP-headline magnitude comparison. This honesty is per the [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §Context Adaptive Markets Hypothesis framing: strategy decay is the null, not the alternative; H060 is not exempt from the AMH prior just because TSMOM is the most-cited robust-futures-strategy in the literature. The Hurst-Ooi-Pedersen 2017 137-year backtest cited in §1.3 is the strongest robustness anchor available but does NOT preclude post-2012 sub-sample decay; the 137-year average masks the post-publication degradation that Huang-Li-Wang-Zhou 2020 + Baltas-Kosowski 2013 + the SG-Trend practitioner record document.

### 1.5 Pre-empirical caveat on cross-mechanism interactions

The four assets {ES, NQ, CL, GC} span equity-index (ES, NQ) and commodity (CL, GC) regimes. Cross-asset correlation is empirically time-varying: equity-commodity correlation flipped from ~-0.2 (1990s-2000s) to +0.3-0.5 (post-2008 QE era) to ~0 (2022-2024 inflation cycle). The TSMOM construction is per-asset and the basket return is the equal-weighted sum — there is NO explicit cross-asset weighting at the signal layer. This is canonical MOP 2012 §2.1 construction; cross-asset weighting variants (risk-parity, equal-vol-contribution) are deferred to a successor hypothesis per `P1-H060-RISK-PARITY-WEIGHTING-SUCCESSOR`.

## 2. Universe and sample period

- **Instruments at v1**: ES (E-mini S&P 500; CME), NQ (E-mini Nasdaq-100; CME), CL (NYMEX WTI Light Sweet Crude; NYMEX-on-CME), GC (COMEX Gold; COMEX-on-CME). All front-month roll-adjusted continuous contracts.  <!-- justify: 4-asset basket is the minimum-diversification cross-asset TSMOM construction per MOP 2012 §2.1 (their basket was 58 instruments; this 4-asset retail-tier basket is the smallest credible projection that preserves equity vs commodity asset-class breadth at the ADR-0001 retail-capacity ceiling) -->
- **Micros NOT included at v1**: MES/MNQ are deterministic linear rescalings per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) and are NOT entered as independent family members; the cost-equivalent micro-substitution is a sizing-layer detail (§4 capacity cap), not a signal-layer decision. MCL/MGC similarly deferred.  <!-- justify: TSMOM signal is per-asset (sign of past 12mo return); micros share the signal with their major counterparts; treating them as independent family members would inflate the SPA family size at no informational gain -->
- **Substrate availability** (BLOCKING precondition; per §11.1):
  - ES + NQ: post-Cell-I substrate at [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/); dataset SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` per H050/H052a/H053/H054/H055 binding.
  - CL + GC: NOT YET INGESTED. BLOCKED on `P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE` per [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md). Ingest authorization is the operator-action precondition before §5/§11 calibration can run.
- **Sample window** (BINDING; pre-reg-frozen):
  - **Calibration holdout**: 2015-01-01 → 2019-12-31 (5 years).  <!-- justify: disjoint from the test folds of H050/H052a/H053/H054/H055; matches the H055 calibration-holdout convention so cross-hypothesis ID-selection fit-set isolation property is preserved -->
  - **IS** (inner-CV grid search across §5 hyperparameter cells): 2020-01-01 → 2023-12-31 (4 years; matches H050 train + H055 IS window).
  - **OOS test**: 2024-01-01 → 2025-12-03 (ES, CL) and 2024-01-01 → 2025-12-19 (NQ, GC) per per-symbol substrate right-edges.  <!-- justify: CL and GC right-edges will be set to match the Databento extraction right-edge actually obtained; placeholder 12-03 / 12-19 reflects the H055 ES/NQ pattern and will be amended at substrate-freeze time per the §16 dataset-checksum freeze procedure -->
- **Cadence**: **daily session-close bars** are the canonical TSMOM horizon (MOP 2012 §3 monthly rebalance evaluated on daily closes; Hurst-Ooi-Pedersen 2017 §2 monthly rebalance from daily series). Bar-cadence (1-min) is OUT OF SCOPE for v1 and explicitly NOT a robustness exhibit: bar-cadence trend-following on equity-index futures was demonstrated by H050 KPI report card v1 to produce realised -81%/-84% on the gated arms over the 2024-2025 OOS — bar-cadence is a structurally different regime, not a refinement of TSMOM. Bar-cadence variant is deferred to a separate hypothesis ID per `P1-H060-BAR-CADENCE-OUT-OF-SCOPE`.
  - Daily close definitions: ES + NQ at 16:00 ET RTH-close (the project's standing session-policy convention); CL at 14:30 ET pit-close NYMEX convention (continuous-trading-day boundary); GC at 13:30 ET COMEX pit-close convention. Per-asset close-time differences make a strict "synchronous daily close" formally impossible — TSMOM signal is computed on each asset's own daily close; the rebalance event is end-of-RTH on the rebalance day. Logged in [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py) extension per `P1-SESSION-POLICY-24-5-IMPL`.
- **Roll treatment**: per-asset roll-adjusted front-month continuous series per the [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) Cycle-1 deliverable v0.3.0 convention extended to CL + GC. Roll calendar per [config/instruments.yaml](../../../config/instruments.yaml) extended per `P1-INSTRUMENTS-YAML-METALS-ENERGY-EXTEND`.

## 3. Features

All features are computed at daily session-close using only data available at time t-1 (PIT-causal; one-day-ahead causal structure per MOP 2012 §3).

- **Per-asset TSMOM signal** (per MOP 2012 §3):
  - `signal_{i,t} = sign(R_{i,[t-h, t-1]})` where `R_{i,[a,b]}` is the cumulative log-return of asset i over the window [a, b] and `h` is the look-back horizon (default `h = 252` sessions ≈ 12 months per MOP 2012 §3 baseline).
  - Look-back horizon is grid-searched per §5 over {63, 126, 252, 504} sessions (≈ 3, 6, 12, 24 months per [Asness, Moskowitz, Pedersen 2013, *J Finance* 68(3):929-985](https://doi.org/10.1111/jofi.12021) cross-sectional momentum spectrum).
- **Per-asset ex-ante volatility estimate** (per MOP 2012 §3):
  - `σ_{i,t}^{ex-ante} = sqrt(261 × EW-MA(r_{i,t-1}^2; halflife = H))` where r is the daily log-return, 261 is the annualisation factor (MOP 2012 §3 convention: 261 trading days/year for ex-ante vol scaling), and `H` is the half-life of the exponentially-weighted moving average over squared returns.
  - Default `H = 60` days per MOP 2012 §3 baseline; grid-searched per §5 over {20, 60} days.
- **Per-asset vol-scaled position** (per MOP 2012 §3):
  - `w_{i,t} = (vol_target / σ_{i,t}^{ex-ante}) × signal_{i,t}` where `vol_target` is the annualised volatility target.
  - Default `vol_target = 0.10` (10% annualised per MOP 2012 §3); grid-searched per §5 over {0.05, 0.10, 0.15}.
- **Kelly-multiplier grid** (per ADR-0018 D-2): `w_{i,t} *= kelly_multiplier` with `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` selected per-fold on inner-CV MPPM(ρ=1) fitness per ADR-0018 D-1. The Kelly multiplier is a leverage scalar applied AFTER the MOP 2012 vol-scaling and BEFORE the ADR-0001 retail-capacity hard cap (§4).  <!-- justify: ADR-0018 D-2 grid is the project-canonical Kelly-grid per the survival-constrained paradigm; the quarter-Kelly lower bound per MacLean-Thorp-Ziemba 2010 ruin-controlled regime is preserved as the minimum cell; the 2.5× upper bound is the highest cell at which the ADR-0017 §4.1 drawdown-constrained Kelly remains theoretically defensible under per-asset ATR-stop sizing -->
- **Capacity hard cap** (per ADR-0001 retail-tier ceiling): after vol-scaling and Kelly-multiplier, `w_{i,t}` is clipped to the per-instrument capacity ceiling:
  - ES: ≤ 20 contracts
  - NQ: ≤ 40 contracts
  - CL: ≤ 5 contracts  <!-- justify: CL notional at $80/bbl × 1000 bbl/contract = $80K notional per contract; retail-tier capacity cap of 5 contracts = $400K notional matches the ADR-0001 retail-tier convention -->
  - GC: ≤ 5 contracts  <!-- justify: GC notional at $2000/oz × 100 oz/contract = $200K notional per contract; retail-tier capacity cap of 5 contracts = $1M notional matches ADR-0001 retail-tier convention with a margin headroom factor of ~2 -->

## 4. Label construction

Per-rebalance-period basket return on a daily-close-cadence rebalanced equal-weighted long/short portfolio.

- **Per-asset daily log-return**: `r_{i,t} = log(C_{i,t} / C_{i,t-1})` where `C_{i,t}` is the roll-adjusted continuous-front-month close.
- **Basket per-session return**: `r_TSMOM,t = (1 / N_assets) × Σ_i w_{i,t-1} × r_{i,t}` where N_assets = 4 (equal-weighted at the basket layer; per-asset vol-scaling already applied at §3 signal-construction layer).
- **Rebalance cadence**: monthly default (rebalance on the first session of each calendar month per MOP 2012 §3); grid-searched per §5 over {weekly, monthly, quarterly}.
- **Position taken at t-open / return realised t-close-to-t-close**: signal computed at t-1 close; position taken at t open (next-day execution); return measured t-close-to-t-close end-of-rebalance-period. Standard one-day-ahead causal structure per MOP 2012 §3.
- **Capacity**: per ADR-0001 hard cap per §3 above; cap is applied BEFORE order placement, AFTER Kelly multiplier.

## 5. Splitter / Estimator

### 5.1 Walk-forward outer CV

- **Outer walk-forward**: rolling 252-session-train / 60-session-test per [Bergmeir & Benítez 2012, *Information Sciences* 191:192-213](https://doi.org/10.1016/j.ins.2011.12.028); embargo = 1 session per [ADR-0007](../../../docs/decisions/ADR-0007-stacked-embargo-convention.md) stacked-embargo convention.
- **Roll cadence**: monthly per the canonical TSMOM rebalance cadence; matches the §4 label-construction cadence.

### 5.2 Inner-CV grid

Per-fold grid search over the H060 hyperparameter cells, selected by MPPM(ρ=1) per ADR-0018 D-1:

| Symbol | Description | Search domain |
|---|---|---|
| h | TSMOM look-back horizon (sessions) | {63, 126, 252, 504} |
| H_halflife | ex-ante vol half-life (sessions) | {20, 60} |
| vol_target | annualised vol target | {0.05, 0.10, 0.15} |
| rebalance_cadence | rebalance event | {weekly, monthly, quarterly} |
| kelly_multiplier | leverage scalar | {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} |

Total cells: 4 × 2 × 3 × 3 × 6 = **432 cells**. Inner-CV draws: N_draws = 30 per [Varma & Simon 2006, *BMC Bioinformatics* 7:91](https://doi.org/10.1186/1471-2105-7-91) bias-correction framework; bracketed by [Bergstra & Bengio 2012, *JMLR* 13:281-305](https://www.jmlr.org/papers/v13/bergstra12a.html) random-search-volume reasoning for the discrete-grid case.

### 5.3 Inner-CV selection metric

Inner-CV selection: **MPPM(ρ=1)** per ADR-0018 D-1 on the inner-CV out-of-fold per-rebalance-period basket return series. The MPPM(ρ=1) primitive is at [src/skie_ninja/inference/mppm.py](../../../src/skie_ninja/inference/mppm.py) per `P1-MPPM-RHO-1-FITNESS-PRIMITIVE` (landed in ADR-0018 commit `40fb53d`); risk-aversion parameter `ρ = 1` matches the log-utility / Kelly-criterion-consistent regime per Ingersoll-Spiegel-Goetzmann-Welch 2007 §2 + MacLean-Thorp-Ziemba 2010 Ch. 1.

### 5.4 BOCD signal-decay monitor

Per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-3, every walk-forward fold runs a Bayesian Online Change-point Detection ([Adams & MacKay 2007 arXiv:0710.3742](https://arxiv.org/abs/0710.3742)) monitor on the per-fold OOS Sharpe / MPPM(ρ=1) / per-asset signal-strength series; the BOCD primitive is at [src/skie_ninja/inference/bocd.py](../../../src/skie_ninja/inference/bocd.py) per `P1-BOCD-DECAY-DETECTOR-PRIMITIVE`. Change-point posterior > 0.5 on any monitored series at run-length ≥ 3 folds → emit `signal-decay-flag` annotation in the KPI report card. This is a KPI annotation per ADR-0018 — NOT a binding gate.

### 5.5 Inner-CV regularisation discipline

To prevent inner-CV overfit on the 432-cell grid: (i) purged-walk-forward inner CV per [Lopez de Prado 2018 *AFML* Wiley ISBN 978-1119482086 Ch.7](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) with purge = embargo = 1 session at the daily-cadence layer; (ii) cell selection by MPPM(ρ=1) (not raw Sharpe) per ADR-0018 D-1; (iii) per-fold cell-selection stability tracked as a sensitivity exhibit (the project's standing nested-CV-overfit guard per `P1-ADR-0015-NESTED-CV-PROTOCOL-PRIMITIVE`).

## 6. Cost model

- **Per-asset NT8-realistic cost model**:
  - ES, NQ: existing [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) (1-tick slippage prior; per-side commission + exchange fee + NFA per [config/instruments.yaml](../../../config/instruments.yaml)).
  - CL: new module `NT8CrudeOilRthV1CostModel` at `src/skie_ninja/backtest/costs/nt8_cl_rth_v1.py` per `P1-METALS-ENERGY-COST-MODEL-IMPL`.
  - GC: new module `NT8GoldRthV1CostModel` at `src/skie_ninja/backtest/costs/nt8_gc_rth_v1.py` per `P1-METALS-ENERGY-COST-MODEL-IMPL`.
- **Cadence-implied turnover**: monthly rebalance → ~12 round-trips per asset per year (rough upper bound; actual turnover is lower because not every rebalance flips signs).
- **Cost drag** (pre-empirical estimate): ~0.5-1.5% annualised per asset depending on contract value and tick-size-to-notional ratio; dollar-weighted basket cost drag ~0.5% annualised at retail capacity ceiling.
- **Application rule**: per-trade log-return drag `log(1 - cost_round_trip / notional)` per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3.1 F-CONV-2 binding.
- **Cost-floor sensitivity exhibit**: 1-tick slippage primary; 2-tick slippage reported as sensitivity exhibit per §14 (`sensitivity_mult ∈ {1.0, 2.0}`).
- **Empirical regime-wise cost calibration**: deferred to follow-up `P1-H060-COST-EMPIRICAL-CALIBRATION` (paper-trade prerequisite).

## 7. No look-ahead

- TSMOM signal at session t uses information up to and including session t-1 close.
- Ex-ante vol estimate at t uses EW-MA of squared returns through t-1.
- Position taken at t open (next-day execution after t-1 close signal).
- Return realised t-close to t-close at end of rebalance period.

This is the canonical MOP 2012 §3 one-day-ahead causal structure. PIT-causality is unit-tested per `P1-H060-PIT-CANARY-INTEGRATION-TEST` (BLOCKING per §11.2) using the project's standing Cycle-4 leak-canary discipline (boundary invariant + label-horizon purge check + dual fit-call observer per [src/skie_ninja/backtest/](../../../src/skie_ninja/backtest/) `WalkForwardEngine` + `TracingArray`).

## 8. Gate thresholds (per ADR-0013; KPI-only, no binding gates)

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1, no KPI value forces or blocks any stage transition. Every former Class A item from ADR-0012 is reported as a KPI annotation.

### 8.a Methodological-correctness annotations (per ADR-0013 §2)

- `leakage-canary-{pass,fail}` per §11.2 PIT canary suite.
- `bss-{positive,flat,negative}` per inner-CV out-of-fold isotonic-calibrated forecast vs equal-weighted-passive climatological prior.
- `reliability-in-band` ∈ [0.7, 1.3] / `reliability-out-of-band` (numeric reported) per [Niculescu-Mizil & Caruana 2005, *ICML*](https://www.cs.cornell.edu/~caruana/niculescu.scldbst.crc.rev4.pdf) reliability-diagram concept.
- `repro-log-{complete,incomplete}`.
- `cost-{robust,conditional,flat}` per §6 sensitivity exhibit.
- `dsr-{positive,marginal,negative}` per Bailey-López de Prado 2014 deflated Sharpe at family size M=5 (4 per-asset + 1 basket); reported.

### 8.b Performance KPIs (per ADR-0017 §3 primary metrics; per ADR-0013 §B preserved)

**Primary (per ADR-0017 §3 Pareto-front operator review)**:
- `tw-q05-{above-half,above-zero,below-zero}`: terminal-wealth-q05 on $10K-starting 252-session forward bootstrap projection per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3.1; primitive at [scripts/simulate_h053_v4_10k_2026.py](../../../scripts/simulate_h053_v4_10k_2026.py) (daily-cadence reference implementation; consolidated under `P1-FORWARD-PROJECTION-PRIMITIVE`).
- `calmar-diff-{positive,marginal,negative}`: Calmar-differential vs passive-equal-weight benchmark; CI per [src/skie_ninja/inference/calmar.py](../../../src/skie_ninja/inference/calmar.py) (landed Phase L commit `546b828`).
- `pf-diff-{positive,marginal,negative}`: profit-factor differential; CI per [src/skie_ninja/inference/profit_factor.py](../../../src/skie_ninja/inference/profit_factor.py) (landed Phase L commit `546b828`).
- `r-multiple-mean-{positive,marginal,negative}`: per-rebalance-period R-multiple mean; CI per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py) (landed Phase L commit `546b828`).

**Secondary (Sharpe-family preserved as academic-comparability KPI per ADR-0017 §3)**:
- Sharpe-vs-passive-equal-weight LW2008 differential CI (basket level + per-asset Benjamini-Hochberg FDR-adjusted family).
- Sharpe-vs-AR(1)-lag-1-bench LW2008 differential CI.
- Hansen 2005 SPA p-value at M=4 per-asset family + basket (KPI annotation per ADR-0008; not load-bearing for H_1).

### 8.c ADR-0018 / ADR-0019 / ADR-0022 annotations

- `mppm-rho1-{positive,marginal,negative}` per inner-CV out-of-fold MPPM(ρ=1) with stationary-bootstrap CI per ADR-0018 D-1.
- `bocd-decay-flag-{raised,not-raised}` per §5.4 BOCD monitor at posterior > 0.5 + run-length ≥ 3 folds.
- `kelly-multiplier-best-fold-{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per fold; aggregate annotation `kelly-multiplier-mode = mode(per-fold-best)`.
- `l-skewness-{positive,zero,negative}` per ADR-0019 on per-rebalance-period basket R-multiple distribution; L-skewness primitive at [src/skie_ninja/inference/l_moments.py](../../../src/skie_ninja/inference/l_moments.py) per `P1-L-SKEWNESS-PRIMITIVE-IMPL`.  <!-- justify: TSMOM is structurally skew-positive on diversified-trend baskets per Hutchinson & O'Brien 2020 (positive L-skewness reflects trend-following's "small losses, occasional large wins" payoff shape; left-tail-bounded by per-trade stop-loss); ADR-0019 §3 barbell-rebalance-candidate flag is raised if τ_3 < 0 (a negative-skew trend strategy is a structurally-non-trend-following artifact that warrants barbell-hedge sibling) -->
- `causal-mechanism-{causal,correlation-only,hybrid}` per §1.3 ADR-0022 annotation; H060 is `hybrid`.

## 9. Power

- N_OOS_sessions ≈ 489 per asset (2024-01-01 → 2025-12-{03,19}) × 4 assets = ≈ 1956 per-asset-session observations; per-rebalance-period basket observations under monthly cadence ≈ 24 rebalance events × 4 assets = ~96 per-asset-rebalance observations.
- Power calibration (the M=5 family α-adjusted minimum-detectable-effect size at 80% power) is deferred to `P1-H060-POWER-SIMULATION-EXECUTE` (BLOCKING per §11.2; analogous to H055 `P1-H055-POWER-SIMULATION-EXECUTE`). Pre-empirical estimate: at M=5 family + α=0.05 + N=24 monthly observations, minimum-detectable Sharpe-differential at 80% power is ~0.5-0.8 — a tight constraint that may force aggregation to weekly cadence for adequate power at the basket level (logged as a §10 decision rule for power-shortfall handling).

## 10. Decision rule

- **Conjunctive PASS (all four primary survival-constrained metrics positive on bootstrap CI)** → operator-discretionary `paper-trade-active` promotion per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3 Pareto-front operator review.
- **Any one primary metric covers zero** → stage transition `kpi-report-emitted`; NinjaScript implementation mandatory per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §5 regardless (or operator-discretionary decline per the 2026-05-04 standing directive).
- **Any one primary metric strictly excludes zero on the negative side** → ADR-0019 `barbell-rebalance-candidate` flag raised; suggest convex-hedge sibling hypothesis with long-OTM-options leg per ADR-0019 §3.
- **`signal-decay-flag` raised** (BOCD posterior > 0.5 at run-length ≥ 3 folds per §5.4) → record annotation in KPI report card; no automatic disposition change (KPI-only per ADR-0018).
- **Power-shortfall** (minimum-detectable-effect at the realised rebalance cadence exceeds the empirical effect size by > 2×) → emit `underpowered` annotation in the R-multiple-mean CI per Phase L commit `546b828` n<30 boundary discipline; operator-discretionary decision whether to (a) aggregate to weekly cadence (improves N), (b) collapse to per-asset sub-hypothesis with M=4 family adjustment, or (c) extend OOS by relaxing the OOS-right-edge constraint at substrate-extension time.

## 11. Kill switches and pre-launch BLOCKING preconditions

### 11.1 Hard kill-switch constraints (per ADR-0017 §5; mandatory inheritance)

- **K-1 Per-trade $-stop**: `1.0R` where `R = vol_target / σ_{i,t}^{ex-ante}` × per-contract dollar move per 1.0 vol-unit (Turtle 2N convention per [Faith 2007 *Way of the Turtle*](https://www.amazon.com/Way-Turtle-Secret-Methods-Successful/dp/0071486646), *practitioner*).
- **K-2 Per-trade time-stop**: 2× median holding period on calibration holdout (~6 weeks on monthly-cadence TSMOM; ~2 weeks on weekly cadence).
- **K-3 No-add-to-loser** (zero exception): TSMOM signal flip closes the prior position; new entry is fresh.
- **K-4 Per-symbol cap** per ADR-0001: ES ≤ 20, NQ ≤ 40, CL ≤ 5, GC ≤ 5 contracts.
- **K-5 Correlated-instrument inventory cap**: ES+MES inventory shares budget; NQ+MNQ inventory shares budget; CL+MCL inventory shares budget; GC+MGC inventory shares budget. (Cross-asset cap deferred to a successor hypothesis; the v1 4-asset basket is treated as 4 independent inventory budgets at the cap layer.)
- **K-6 Daily circuit breaker**: -2% of basket equity realised P/L → halt new entries through end of session.
- **K-7 Weekly circuit breaker**: -5% of basket equity realised P/L → halt new entries through end of week.
- **K-8 Adverse-direction entry filter**: forbid new entries when TSMOM signal sign disagrees with the asset's most-recent 5-day return sign AND the asset has moved adversely > 0.5 ATR from prior-day close at fill time (the ADR-0017 §5 K-8 binding adapted to daily-cadence TSMOM by replacing the bar-cadence T_H trend-gate with the 5-day return sign).

### 11.2 Pre-launch BLOCKING preconditions (BLOCKING-BEFORE-LAUNCH)

These follow-ups MUST land before the H060 production walk-forward dispatch:

| Follow-up | Status | Notes |
|---|---|---|
| `P1-INSTRUMENTS-YAML-METALS-ENERGY-EXTEND` | OPEN | per ADR-0023; adds CL/GC to [config/instruments.yaml](../../../config/instruments.yaml) with tick-size, multiplier, fee schedule. |
| `P1-DATABENTO-METALS-ENERGY-COST-DOSSIER` | OPEN | per ADR-0023; pre-Stage-A cost dossier for the CL+GC extraction. |
| `P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE` | OPEN | operator-action; per ADR-0023; CL+GC raw-bar extraction from Databento. |
| `P1-MONTHLY-ROLL-MODULE-IMPL` | OPEN | per ADR-0023; CL/GC roll calendars differ from ES/NQ quarterly; monthly-roll module required. |
| `P1-SESSION-POLICY-24-5-IMPL` | OPEN | per ADR-0023; [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py) extension for CL (24/5 with daily settlement) and GC (24/5 with daily settlement). |
| `P1-METALS-ENERGY-COST-MODEL-IMPL` | OPEN | per ADR-0023; `NT8CrudeOilRthV1CostModel` + `NT8GoldRthV1CostModel` modules. |
| `P1-MPPM-RHO-1-FITNESS-PRIMITIVE` | CLOSED | landed ADR-0018 commit `40fb53d`. |
| `P1-BOCD-DECAY-DETECTOR-PRIMITIVE` | CLOSED | landed ADR-0018 commit `40fb53d`. |
| `P1-L-SKEWNESS-PRIMITIVE-IMPL` | CLOSED | landed ADR-0018 commit `40fb53d`. |
| `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE` | CLOSED | landed ADR-0018 commit `40fb53d`. |
| `P1-H060-PIT-CANARY-INTEGRATION-TEST` | OPEN | BLOCKING; analogous to H053 / H055 PIT canary integration test. |
| `P1-H060-POWER-SIMULATION-EXECUTE` | OPEN | BLOCKING; fills the §9 power-calibration placeholder; gates the N_OOS/M=5/α budget reconciliation. |

### 11.3 Concurrent inheritance preconditions (from ADR-0017 Phase L Thread A)

The following Phase L primitives are landed but the BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH follow-ups remain open:
- `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` — OPEN per Phase L Thread A.
- `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` — OPEN per Phase L Thread A; wires K-1..K-8 into the Cycle-4 leak-canary discipline at the orchestrator layer.

H060 production walk-forward dispatch is BLOCKED until both Phase L Thread A residuals land per the ADR-0017 §5 mandatory-inheritance-from-H055-forward convention.

## 12. Sample bias / robustness

- **Survivorship**: ES, NQ, CL, GC are all live and continuously-active CME / NYMEX / COMEX contracts. No survivorship bias.
- **Look-ahead**: signal at t-1, position at t-open, return at t-close. Standard MOP 2012 §3 one-day-ahead causal structure. PIT-canary unit-tested per §11.2.
- **Multiple-testing**: H060 is M=5 family (4 per-asset + 1 basket); intra-H060 family-wise correction by Benjamini-Hochberg FDR at α=0.05 per the project's standing convention. Cross-hypothesis SPA family construction (across H050, H052a, H053, H054, H055, H060) is deferred to `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR` (heterogeneous OOS windows + heterogeneous bar-vs-daily cadences preclude shared bootstrap-index sample length per Hansen 2005 §2).
- **Cross-asset correlation time-variation**: equity-commodity correlation is empirically non-stationary (sign-flips across decades; §1.4 caveat). The TSMOM construction is per-asset; basket equal-weight is the only cross-asset weighting at v1. Risk-parity / inverse-vol / equal-vol-contribution variants are deferred per `P1-H060-RISK-PARITY-WEIGHTING-SUCCESSOR`.

## 13. Robustness exhibits (informational; not load-bearing per ADR-0013 §1)

- **Sub-basket {ES, NQ}**: equity-pair-only sub-basket. Low-breadth degenerate case; high ES-NQ correlation (ρ > 0.85 on daily returns) compresses the diversification gain.
- **Sub-basket {CL, GC}**: commodity-pair-only sub-basket. High-breadth potential; low CL-GC correlation.
- **Look-back sensitivity**: 63-day vs 252-day vs 504-day lookback comparison; primary literature (MOP 2012 §6) documents qualitative invariance across 1-12 month horizons.
- **Vol-target sensitivity**: 5% vs 10% vs 15% vol-target comparison.
- **Cost-floor sensitivity**: 1-tick (primary) vs 2-tick (sensitivity exhibit per §6).
- **ADR-0019 barbell-sibling exhibit**: pair the TSMOM basket with an explicit 5-10% long-OTM-put overlay on ES (1-month rolling, 10-delta strike) as tail-hedge; reported as descriptive exhibit only; NOT a formal §1 family entry.
- **Per-rebalance-cadence sensitivity**: weekly vs monthly vs quarterly cadence; descriptive exhibit; not a §1 family entry.

## 14. Reporting

Per [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) §3.2 (extended to 13 tables under ADR-0019 + 12 mandatory primary-metric tables under ADR-0017 §3.2), the H060 KPI report card MUST include the following structured end-of-simulation summary section between the H1 / hypothesis preamble and the §"Methodological-correctness annotations":

| # | Table | Source |
|---|---|---|
| 1 | P/L (realized OOS, $10K starting capital) | per ADR-0017 §3.2 §1 |
| 2 | Drawdown (realized + projected) | per ADR-0017 §3.2 §2 |
| 3 | Sharpe — primary inference (T = SR_TSMOM − SR_passive_EW per §1; LW2008 CI with excludes-zero column) | per ADR-0013 §3 §3 |
| 3a | Calmar-differential — primary survival inference | per ADR-0017 §3.2 §3a |
| 3b | Profit-factor differential — primary survival inference | per ADR-0017 §3.2 §3b |
| 3c | R-multiple-mean — primary survival inference | per ADR-0017 §3.2 §3c |
| 4 | Annualised Sharpe (with annualisation-factor declaration) | per ADR-0013 §3 §4 |
| 5 | Win/Loss/Zero counts + win rate W/(W+L+Z) | per ADR-0014 §5 |
| 6 | Forward 1-year projection (Median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%)) | per ADR-0013 §3.1 / ADR-0014 §6 |
| 7 | Hansen SPA family p (KPI annotation per ADR-0008 at M=5; not load-bearing) | per ADR-0014 §7 |
| 8 | Other KPIs (best Kelly-multiplier per fold, n_folds realized/expected, MPPM(ρ=1), BOCD decay-flag, L-skewness, causal-mechanism annotation) | per ADR-0014 §8 |
| 9 | Methodological-correctness annotations | per ADR-0014 §9 |

Plus mandatory **bottom-line prose paragraph** (≤ 8 sentences) stating the primary inferential verdict + realised + projected $10K equity outcome + next mandatory stage transition + cross-link to full report card body.

Template at [research/_templates/kpi_results_summary_template.md](../../../research/_templates/kpi_results_summary_template.md).

## 15. NinjaScript implementation (mandatory per ADR-0013 §5)

H060 is **pure-C# implementable** (no Python inference at decision time):
- TSMOM signal is `sign(past-h-session-log-return)` — closed-form arithmetic on a rolling close-to-close-return buffer.
- Ex-ante vol estimate is an EW-MA of squared returns — closed-form recursion with a single state variable per asset.
- Position rule is `vol_target / σ_ex_ante × signal × kelly_multiplier` clipped to ADR-0001 capacity ceilings — deterministic.
- Rebalance event is a calendar-cadence trigger (weekly/monthly/quarterly) — `OnBarUpdate` + `Time[0]` checks.

- **C# class**: `H060_TSMOM_CrossFutures` at `ninjascript/strategies/H060_TSMOM_CrossFutures.cs`.
- **Python-prototype hyperparameter mapping**: `h`, `H_halflife`, `vol_target`, `rebalance_cadence`, `kelly_multiplier` each map 1:1 to NinjaScript `[NinjaScriptProperty]` parameters.
- **Entry/exit logic**: 1:1 with the Python signal generation (§3); cost model wired via [config/instruments.yaml](../../../config/instruments.yaml) per-instrument tick-size + multiplier.
- **Kill-switch parameters**: K-1..K-8 per §11.1 enforced at the strategy layer.
- **Fill-log schema**: matches plan §6.1 fill-log schema.
- **Sim101 smoke-test record**: required post-implementation; ScriptSubmission timestamps + position fills + final P/L logged.
- **Python ↔ NinjaScript parity-check**: byte-equality on the integer signal vector per ADR-0013 §5.2; per-strategy calibration via `P1-H060-NINJASCRIPT-PARITY-TOLERANCE`.

## 16. Pre-registration freeze metadata

- **Substrate dataset_checksum** (pending CL/GC extraction; placeholder will be amended at substrate-freeze time):
  - ES + NQ: `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` (post-Cell-I substrate per H050/H052a/H053/H054/H055 binding).
  - CL + GC: TBD per `P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE`; SHA256 to be computed post-extraction and recorded in [research/01_hypothesis_register/H060/data_requirements.md](data_requirements.md) prior to the first production walk-forward dispatch.
- **Scientific payload SHA256**: computed at first orchestrator run; recorded in the per-run sidecar at `runs/h060/<run_id>/sidecar.json`.
- **Reproducibility log path**: `logs/reproducibility/<run_id>.json` (project standing convention).
- **Git HEAD at pre-registration freeze**: recorded in the §17 revision log entry below.
- **RNG seed**: `20260512` (date-anchored; consistent with H055 convention).

## 17. Revision log

- **2026-05-12 — initial pre-registration draft; status `designed`.**
  - Author: skoir (independent researcher).
  - Inheritance: [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) retail-tier capacity ceiling, [ADR-0006](../../../docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) project-scope extension, [ADR-0007](../../../docs/decisions/ADR-0007-stacked-embargo-convention.md) stacked-embargo convention, [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-and-m1-degenerate.md) SPA M=1 degenerate handling, [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) permanent-exploration / no-binding-gates / mandatory-NinjaScript-terminus / non-loss preservation, [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) canonical KPI results-summary tables, [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained primary metric vector + drawdown-constrained Kelly + K-1..K-8 kill switches + FM-1..FM-5 stress-test suite, [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) fitness + Kelly-multiplier grid + BOCD signal-decay monitor, [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness annotation + barbell-rebalance-candidate flag, [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism vs correlation-only annotation, [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate extension.
  - Causal-mechanism claim type (§1.3): `hybrid` (institutional CTA flow + Hong-Stein 1999 underreaction model upstream causal mechanism; vol-scaling + Kelly-multiplier layers correlation-only refinement); E-value anchor Hurst-Ooi-Pedersen 2017 137-year multi-asset backtest.
  - Pre-launch BLOCKING preconditions: 12 follow-ups listed in §11.2 + §11.3 (4 closed; 8 open).
  - Frozen §1-§7 immutability per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Frozen pre-registration amendment".
  - Audit-remediate-loop discipline: pre-registration draft pending Round-1 isolated quant-auditor + literature-check; expected audit findings include (a) CL/GC right-edge placeholder concretisation, (b) per-asset close-time disambiguation (ES/NQ 16:00 ET vs CL 14:30 ET vs GC 13:30 ET), (c) cost-model verification against ADR-0023 cost dossier, (d) MPPM(ρ=1) inner-CV variance under M=5 family. Audit trail will be at `docs/audits/audit_trail_<date>_h060_design.md`.
