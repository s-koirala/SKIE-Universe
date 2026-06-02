---
hypothesis_id: H061
schema_version: hypothesis_design_v1
status: designed
tier: 2c
created: 2026-05-12
created_by: skoir
description: Pre-registered design doc for hypothesis H061 — cross-futures time-series momentum (TSMOM) on equal-weighted CME basket {ES, NQ, CL, MGC, SIL} under the Phase N survival-constrained / MPPM(ρ=1) / Kelly-grid / BOCD-decay / barbell payoff-shape / causal-mechanism paradigm. v2-with-CL successor to H060 v1 per `P1-H060-V2-WITH-CL-FULL-SIZE`.
---

# H061 — Cross-futures TSMOM with full-size CL on {ES, NQ, CL, MGC, SIL}

> **Canonical TSMOM construction on a 5-asset CME-Globex / NYMEX basket adding the canonical energy contract.** H061 applies the [Moskowitz, Ooi, Pedersen 2012, *JFE* 104(2):228-250](https://doi.org/10.1016/j.jfineco.2011.11.003) (henceforth "MOP 2012") time-series-momentum construction — 12-month look-back signal × ex-ante volatility scaling × monthly rebalance — to the equal-weighted basket of E-mini S&P 500 (ES), E-mini Nasdaq-100 (NQ), **NYMEX WTI Light Sweet Crude (CL)**, COMEX Micro Gold (MGC), and COMEX Micro Silver (SIL) front-month roll-adjusted continuous contracts. H061 is structurally identical to [H060](../H060/design.md) except for the basket scope: full-size CL is added (NOT substituted for any v1 asset) to test whether the canonical energy contract — with structurally different return character than precious metals (lower correlation with equity; higher volatility; supply-shock-driven episodic moves) — moves the H060 v1 non-significant-null verdict toward a directionally-positive outcome. v2-with-CL successor to [H060 v1](../H060/design.md) per the `P1-H060-V2-WITH-CL-FULL-SIZE` follow-up.
>
> **Full Phase N paradigm inheritance.** Same as H060 — [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) primary metric vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) inner-CV fitness + Kelly-multiplier grid + BOCD signal-decay monitor + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness annotation + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism annotation + [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate.
>
> **Daily-cadence — NOT bar-cadence.** Same as H060. TSMOM at the canonical monthly-rebalance horizon on daily-close bars is structurally a different regime from bar-cadence intraday strategies. Bar-cadence variants explicitly out-of-scope per `P1-H060-BAR-CADENCE-OUT-OF-SCOPE` (inherited).

## 1. Hypothesis

- **H_0**: The TSMOM (12-month signal, ex-ante-vol-scaled, monthly rebalance) equal-weighted 5-asset portfolio over {ES, NQ, CL, MGC, SIL} does NOT produce a Sharpe-vs-passive-equal-weighted-long differential whose 95% LW2008 studentized stationary-bootstrap CI excludes zero on the 2024-2025 OOS test fold; AND the primary fitness function MPPM(ρ=1) per [Ingersoll, Spiegel, Goetzmann, Welch 2007, *RFS* 20(5):1503-1546](https://doi.org/10.1093/rfs/hhm025) does NOT exceed zero with a stationary-bootstrap CI excluding zero per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1.
- **H_1**: BOTH (a) the Sharpe-differential 95% LW2008 CI strictly excludes zero on the positive side AND (b) MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero on the positive side per ADR-0018 D-1. Promotion-decision-rule layer is governed by [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3 Pareto-front operator review across the four primary survival-constrained metrics (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean); the Sharpe-differential + MPPM(ρ=1) entries above are the load-bearing INFERENTIAL family entries (§8 KPI annotation grammar).
- **Predictand**: per-asset signed log-return over the rebalance horizon (monthly default; grid-searched per §5). TSMOM portfolio return at session t is `r_TSMOM,t = Σ_i w_{i,t-1} · r_{i,t}` where `w_{i,t-1}` is the vol-scaled signed position computed at the prior close (one-day-ahead causal structure per MOP 2012 §3); index i now runs over the 5-asset basket.
- **Test statistic** (load-bearing): `T_H061_basket = SR_TSMOM − SR_passive_EW` evaluated under [Ledoit & Wolf 2008, *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap CI with block length per [Politis & White 2004, *Econometric Reviews* 23(1):53-70](https://doi.org/10.1081/ETC-120028836) + [Patton, Politis & White 2009, *Econometric Reviews* 28(4):372-375](https://doi.org/10.1080/07474930802459016) correction; per-asset SR differentials reported as sibling family entries under Benjamini-Hochberg FDR at α=0.05. Hansen 2005 SPA p reported as KPI annotation per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-and-m1-degenerate.md) (KPI-only at M=6 family size — 5 per-asset + 1 basket).

### 1.3 Causal-mechanism vs correlation-only annotation (per ADR-0022)

- **Claim type**: `hybrid` (upstream causal mechanism on the long-horizon signal; correlation-only refinement on the vol-scaling and Kelly-multiplier layers). Same as H060 with the addition of the energy-specific oil-price-and-macro-uncertainty mechanism on the CL leg.
- **Mechanism description (who/what/why/when)**:
  - **WHO** (inherited from H060 §1.3): institutional commodity-trading-advisors (CTAs) + risk-parity funds + retail trend-followers; aggregate AUM in systematic-trend strategies estimated at ~$300-500B globally. **CL-specific addition**: physical-energy hedgers (airline / refiner / E&P producer hedging programs) provide directional flow that interacts with trend-following demand at the WTI complex — this is a different micro-structure than the precious-metals leg, which is dominated by ETF-rebalance + macro-narrative flow.
  - **WHAT** (inherited): programmatic position-flow into existing trends on slow rebalance horizons, often vol-target-scaled to a fixed annualised volatility budget. **CL-specific**: oil-price moves transmit through inflation expectations and growth expectations into the macro-economy ([Hamilton 1996, *J Monetary Economics* 38(2):215-220](https://doi.org/10.1016/S0304-3932(96)01282-2) "This is what happened to the oil price-macroeconomy relationship"), making the CL trend signal a partial proxy for macro-regime shifts that may not be captured by the equity / metals legs alone.
  - **WHY** (inherited): (i) institutional mandate to "be in the trade"; (ii) underreaction to long-horizon news per [Hong & Stein 1999, *J Finance* 54(6):2143-2184](https://doi.org/10.1111/0022-1082.00184) gradual-information-diffusion model; (iii) anchoring + disposition-effect per [Frazzini 2006, *J Finance* 61(4):2017-2046](https://doi.org/10.1111/j.1540-6261.2006.00896.x); (iv) risk-parity rebalance amplifies persistence. **CL-specific**: supply-shock-driven episodic moves (2014-2016 oil crash, 2020 negative-price event, 2022 Russia-Ukraine supply disruption) generate large persistent trends that should be captured by a 12-month look-back signal.
  - **WHEN** (inherited): persistent across regimes per [Hurst, Ooi, Pedersen 2017, *J Portfolio Management* 44(1):15-29](https://doi.org/10.3905/jpm.2017.44.1.015) 137-year multi-asset backtest. Regime-dependent / momentum-crash-vulnerable per [Daniel & Moskowitz 2016, *JFE* 122(2):221-247](https://doi.org/10.1016/j.jfineco.2015.12.002). **CL-specific**: oil-shock regimes (Hamilton 1996) are episodic; the CL leg may contribute most of its informational content during a small number of high-magnitude periods (consistent with positive L-skewness payoff under ADR-0019).
- **E-value / robustness anchor**: Hurst-Ooi-Pedersen 2017 137-year multi-asset backtest INCLUDES crude oil in its basket — the CL contribution is therefore directly anchored in the load-bearing primary out-of-sample evidence (NOT a novel inclusion at H061 time). Rough magnitude E-value equivalent ≥ 3.0 (same as H060 §1.3).

### 1.4 Pre-empirical caveat: TSMOM is a partially-decayed factor; H061 specifically tests whether CL changes the H060 v1 verdict

Inherits H060 §1.4 in full: TSMOM has decayed post-publication per [Huang, Li, Wang & Zhou 2020, *J Financial Economics* 137(3):695-712](https://doi.org/10.1016/j.jfineco.2020.04.003), [Baltas & Kosowski 2013 *SSRN 1968996*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1968996), and the SocGen Trend Index 2009-2018 Sharpe ≈ 0 practitioner counter-anchor. Expected basket Sharpe under H_1 is **0.2-0.4 annualized**, not the canonical MOP 2012 ~1.0.

**H061-specific question**: does adding the canonical energy contract (CL) to the H060 v1 4-asset basket move the verdict? H060 v1 produced a **non-significant null** (per the [H060 KPI report card v1](../H060/H060_kpi_report_v1.md)) at the pre-cost 4-asset basket level — basket realized +89.43% over 1,260 concatenated OOS sessions vs +83.13% passive (Δ +6.30%), with the LW2008 Sharpe-differential CI covering zero. The pre-empirical expectation for H061 is **similar magnitude / similar verdict**: adding one more correlated asset to a 4-asset basket does not fundamentally change the post-publication decay regime. The hypothesis is worth running specifically because (a) CL has substantially different return character than the v1 4-asset basket (lower equity correlation; episodic supply shocks per Hamilton 1996); (b) the canonical 5-asset cross-asset breadth completes the experiment the operator deferred from H060 v1 due to budget; (c) the H060 v1 KPI table 8 best-fold Kelly-multiplier was `2.5` on most folds — the leverage layer is at the upper grid edge and adding a fifth uncorrelated asset may shift the optimum cell. **Honest expectation**: a similar pre-cost basket return / non-significant-null verdict to H060 v1. The value is in completing the experiment, not in expecting a different verdict.

### 1.5 Pre-empirical caveat on cross-mechanism interactions

Inherits H060 §1.5 + extension: the 5-asset basket {ES, NQ, CL, MGC, SIL} spans equity-index (ES, NQ), energy (CL), and metals (MGC, SIL) regimes. Cross-asset correlation is empirically time-varying; equity-commodity correlation flipped from ~-0.2 (1990s-2000s) to +0.3-0.5 (post-2008 QE era) to ~0 (2022-2024 inflation cycle). **CL-specific**: oil-equity correlation flipped sign in 2014-2016 (oil crash decoupled from equity rallies) and again in 2022 (oil-driven inflation correlated negatively with growth-sensitive equity); these episodic decoupling events are exactly the regimes where adding CL should matter most. The TSMOM construction is per-asset and the basket return is the equal-weighted sum — no explicit cross-asset weighting at the signal layer (canonical MOP 2012 §2.1). Risk-parity / inverse-vol / equal-vol-contribution variants are deferred per `P1-H060-RISK-PARITY-WEIGHTING-SUCCESSOR` (inherited).

## 2. Universe and sample period

- **Instruments at H061 v1**: ES (E-mini S&P 500; CME), NQ (E-mini Nasdaq-100; CME), **CL (NYMEX WTI Light Sweet Crude; full-size, 1000 bbl/contract)**, MGC (Micro Gold; COMEX-on-CME-Globex), SIL (Micro Silver; COMEX-on-CME-Globex). All front-month roll-adjusted continuous contracts.  <!-- justify: full 5-asset basket adds the canonical energy contract to the H060 v1 4-asset basket; full-size CL (NOT Micro Crude MCL) chosen because MCL inception 2021-07-12 precludes the §2 calibration holdout 2015-2019, AND full-size CL is the literature-canonical energy contract used in MOP 2012 + Hurst-Ooi-Pedersen 2017; retail-tier capacity ceiling enforced via §3 capacity cap (CL ≤ 5 contracts per ADR-0001 analog) -->
- **Substrate availability** (BLOCKING precondition; out-of-band operator action):
  - **CL substrate**: NOT YET EXTRACTED. The 2026-05-12 cost dossier (`logs/databento_cost_dossiers/metals_energy_consolidated_2026-05-12.json`) quotes `CL.FUT ohlcv-1m 2015-2025` at **$239.82 USD** vs the operator's standing $80 budget — pre-H061 substrate extraction requires a separate operator authorization out-of-band. Tracked under `P1-H061-CL-SUBSTRATE-EXTRACTION-AUTHORIZE` (BLOCKING; operator-action).
  - **{ES, NQ, MGC, SIL} substrate**: already live at [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) per the H060 v1 binding (combined SHA256 `242aaa280b216f45edc3b9d9de9630f52f71206eea7832c1cb0470296190f46f`). The H060 v1 production-run substrate SHA was `1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959` (post-Stage-B ES + NQ + MGC + SIL) — this is the substrate that H061 will extend by adding the CL partition.
  - **Combined H061 substrate SHA256**: TBD post-CL extraction. Recorded in [data_requirements.md](data_requirements.md) at substrate-freeze time per ADR-0013 §16 convention.
- **Sample window** (BINDING; identical to H060 v1):
  - **Calibration holdout**: 2015-01-01 → 2019-12-31 (5 years). CL has been continuously traded since 1983 so it contributes the full 5-year window (unlike MCL's 2021-07-12 inception that forced the H060 4-asset compromise). MGC + SIL + CL contribute the full 5-year window; ES + NQ have no pre-2020 substrate so they contribute zero rows to the calibration holdout. Calibration-holdout role is supplemental at v1 (cross-hypothesis fit-set isolation per H055 / H060 precedent); the actual inner-CV operates on IS only.  <!-- justify: disjoint from the test folds of H050/H052a/H053/H054/H055/H060; matches the H055/H060 calibration-holdout convention so cross-hypothesis ID-selection fit-set isolation is preserved on the metals + energy legs; the asymmetric ES/NQ coverage is documented and accepted (same as H060) -->
  - **IS** (inner-CV grid search across §5 hyperparameter cells): 2020-01-01 → 2023-12-31 (4 years; matches H060 v1).
  - **OOS test**: per-symbol substrate right-edges: ES → 2024-01-01 → 2025-12-03; NQ → 2024-01-01 → 2024-12-19; MGC + SIL → 2024-01-01 → 2025-12-30; CL → 2024-01-01 → right-edge TBD post-extraction (expected ≥ 2025-12-03 since CL is liquid throughout). Per-asset basket-return is computed on the intersection of available symbols at each session.
- **Cadence**: **daily session-close bars** (same as H060 v1). Bar-cadence (1-min) is OUT OF SCOPE for v1.
  - Daily close definitions: per-instrument's own daily settlement convention. ES + NQ at 16:00 ET RTH-close; MGC at 13:30 ET COMEX pit-close; SIL at 13:25 ET COMEX silver pit-close; **CL at 14:30 ET NYMEX RTH-close convention**. Per-asset close-time differences make a strict "synchronous daily close" formally impossible — TSMOM signal is computed on each asset's own daily close; the rebalance event is end-of-CME-Globex-trading-day (16:00 CT) on the rebalance day. Logged via `classify_energy_metals_session` in [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py) (extended per `P1-SESSION-POLICY-24-5-IMPL` closure; CL 24/5 with daily settlement per ADR-0023).
- **Roll treatment**: per-asset roll-adjusted front-month continuous series per the [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) v0.4.0 deliverable; CL uses monthly roll-codes (F/G/H/J/K/M/N/Q/U/V/X/Z) per `P1-MONTHLY-ROLL-MODULE-IMPL` (closed pre-H060 v1; reused for CL).

- **Cost model — ZERO at H061 v1 (inherited from H060 v1 operator decision; research-only pre-cost)**: zero commissions, zero exchange fees, zero NFA fees, zero slippage applied at v1. Realized OOS equity is the **pre-cost upper bound**. Cost-realism deferred to `P1-H061-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE per ADR-0017 §3). Methodological-correctness annotation `cost-zero-v1-pre-cost-research-only` carried in every KPI report card emitted at v1.

## 3. Features

All features are computed at daily session-close using only data available at time t-1 (PIT-causal; one-day-ahead causal structure per MOP 2012 §3). Identical to H060 §3 with the addition of CL at the per-asset signal layer.

- **Per-asset TSMOM signal** (per MOP 2012 §3): `signal_{i,t} = sign(R_{i,[t-h, t-1]})`; default `h = 252` sessions; grid-searched per §5 over {63, 126, 252, 504} per [Asness, Moskowitz, Pedersen 2013, *J Finance* 68(3):929-985](https://doi.org/10.1111/jofi.12021).
- **Per-asset ex-ante volatility estimate** (per MOP 2012 §3): `σ_{i,t}^{ex-ante} = sqrt(261 × EW-MA(r_{i,t-1}^2; halflife = H))`; default `H = 60` days; grid over {20, 60} days.
- **Per-asset vol-scaled position** (per MOP 2012 §3): `w_{i,t} = (vol_target / σ_{i,t}^{ex-ante}) × signal_{i,t}`; default `vol_target = 0.10`; grid over {0.05, 0.10, 0.15}.
- **Kelly-multiplier grid** (per ADR-0018 D-2): `w_{i,t} *= kelly_multiplier` with `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}`.
- **Capacity hard cap** (per ADR-0001 retail-tier ceiling): clipping after vol-scaling + Kelly:
  - ES: ≤ 20 contracts
  - NQ: ≤ 40 contracts
  - **CL: ≤ 5 contracts**  <!-- justify: CL notional at $70-80/bbl × 1000 bbl/contract ≈ $70-80K notional per contract; retail-tier capacity cap of 5 contracts ≈ $350-400K notional matches the ADR-0001 retail-tier convention; consistent with the H060 design.md §3 unused CL/GC capacity-cap entries originally scoped for the v1 basket pre-deferral -->
  - MGC: ≤ 5 contracts
  - SIL: ≤ 5 contracts

## 4. Label construction

Identical to H060 §4 modulo the 5-asset basket.

- **Per-asset daily log-return**: `r_{i,t} = log(C_{i,t} / C_{i,t-1})`.
- **Basket per-session return**: `r_TSMOM,t = (1 / N_assets) × Σ_i w_{i,t-1} × r_{i,t}` where N_assets = 5.
- **Rebalance cadence**: monthly default; grid over {weekly, monthly, quarterly}.
- **Position taken at t-open / return realised t-close-to-t-close**: signal computed at t-1 close; position taken at t open; standard one-day-ahead causal structure per MOP 2012 §3.
- **Capacity**: ADR-0001 hard cap per §3 above; cap applied BEFORE order placement, AFTER Kelly multiplier.

## 5. Splitter / Estimator

### 5.1 Walk-forward outer CV

Identical to H060 §5.1: rolling 252-session-train / 60-session-test per [Bergmeir & Benítez 2012, *Information Sciences* 191:192-213](https://doi.org/10.1016/j.ins.2011.12.028); embargo = 1 session per [ADR-0007](../../../docs/decisions/ADR-0007-stacked-embargo-convention.md); monthly roll cadence.

### 5.2 Inner-CV grid

Per-fold grid search; selected by MPPM(ρ=1) per ADR-0018 D-1:

| Symbol | Description | Search domain |
|---|---|---|
| h | TSMOM look-back horizon (sessions) | {63, 126, 252, 504} |
| H_halflife | ex-ante vol half-life (sessions) | {20, 60} |
| vol_target | annualised vol target | {0.05, 0.10, 0.15} |
| rebalance_cadence | rebalance event | {weekly, monthly, quarterly} |
| kelly_multiplier | leverage scalar | {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} |

Total cells: 4 × 2 × 3 × 3 × 6 = **432 cells**. Inner-CV draws: N_draws = 30 per [Varma & Simon 2006, *BMC Bioinformatics* 7:91](https://doi.org/10.1186/1471-2105-7-91). Identical to H060 §5.2. Per the H060 v1 production-run note, the production orchestrator collapsed the 432-cell grid to 72 cells at daily cadence; H061 will inherit the same operational collapse if the same orchestrator is reused (`P1-H061-INNER-CV-GRID-PARITY-WITH-H060`).

### 5.3 Inner-CV selection metric

**MPPM(ρ=1)** per ADR-0018 D-1; primitive at [src/skie_ninja/inference/mppm.py](../../../src/skie_ninja/inference/mppm.py). Identical to H060 §5.3.

### 5.4 BOCD signal-decay monitor

Per ADR-0018 D-3; primitive at [src/skie_ninja/inference/bocd.py](../../../src/skie_ninja/inference/bocd.py). Identical to H060 §5.4. Change-point posterior > 0.5 at run-length ≥ 3 folds → emit `signal-decay-flag` annotation. KPI annotation, NOT a binding gate.

### 5.5 Inner-CV regularisation discipline

Identical to H060 §5.5: purged-walk-forward inner CV per [Lopez de Prado 2018 *AFML* Wiley Ch.7](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086); cell selection by MPPM(ρ=1); per-fold cell-selection stability tracked per `P1-ADR-0015-NESTED-CV-PROTOCOL-PRIMITIVE`.

## 6. Cost model

**ZERO at H061 v1 (inherited from H060 v1)**. Per the §2 cost-model line. Cost-realistic v2 deferred to `P1-H061-COST-EMPIRICAL-CALIBRATION`. Per-asset NT8-realistic cost modules are available per H060 §6 (`NT8CrudeOilRthV1CostModel` already implemented per `P1-METALS-ENERGY-COST-MODEL-IMPL` closure) and will be wired at v2-cost-aware emission.

- **Application rule at v2**: per-trade log-return drag `log(1 - cost_round_trip / notional)` per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3.1 F-CONV-2.
- **Cost-floor sensitivity exhibit (v2)**: 1-tick slippage primary; 2-tick sensitivity per §13.

## 7. No look-ahead

Identical to H060 §7. TSMOM signal at t uses information ≤ t-1 close; ex-ante vol estimate ≤ t-1; position taken at t open; return realised t-close to t-close. PIT-causality unit-tested per `P1-H061-PIT-CANARY-INTEGRATION-TEST` (BLOCKING per §11.2; same canary suite as H060).

## 8. Gate thresholds (per ADR-0013; KPI-only, no binding gates)

Per ADR-0013 §1, no KPI value forces or blocks any stage transition. Every former Class A item from ADR-0012 reported as a KPI annotation.

### 8.a Methodological-correctness annotations (per ADR-0013 §2)

Identical to H060 §8.a:
- `leakage-canary-{pass,fail}` per §11.2 PIT canary suite.
- `bss-{positive,flat,negative}` per inner-CV out-of-fold isotonic-calibrated forecast vs equal-weighted-passive climatological prior.
- `reliability-in-band` ∈ [0.7, 1.3] / `reliability-out-of-band`.
- `repro-log-{complete,incomplete}`.
- `cost-{robust,conditional,flat}` per §6 sensitivity exhibit (v2 only; v1 is `cost-zero-v1-pre-cost-research-only`).
- `dsr-{positive,marginal,negative}` per Bailey-López de Prado 2014 deflated Sharpe at family size **M=6 (5 per-asset + 1 basket)**.

### 8.b Performance KPIs (per ADR-0017 §3 primary metrics; per ADR-0013 §B preserved)

**Primary (per ADR-0017 §3 Pareto-front operator review)**:
- `tw-q05-{above-half,above-zero,below-zero}`: terminal-wealth-q05 on $10K-starting 252-session forward bootstrap projection.
- `calmar-diff-{positive,marginal,negative}`: Calmar-differential vs passive-equal-weight benchmark; CI per [src/skie_ninja/inference/calmar.py](../../../src/skie_ninja/inference/calmar.py).
- `pf-diff-{positive,marginal,negative}`: profit-factor differential; CI per [src/skie_ninja/inference/profit_factor.py](../../../src/skie_ninja/inference/profit_factor.py).
- `r-multiple-mean-{positive,marginal,negative}`: per-rebalance-period R-multiple mean; CI per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py).

**Secondary (Sharpe-family preserved as academic-comparability KPI per ADR-0017 §3)**:
- Sharpe-vs-passive-equal-weight LW2008 differential CI (basket level + per-asset BH-FDR-adjusted family).
- Sharpe-vs-AR(1)-lag-1-bench LW2008 differential CI.
- Hansen 2005 SPA p-value at M=6 (KPI annotation per ADR-0008; not load-bearing for H_1).

### 8.c ADR-0018 / ADR-0019 / ADR-0022 annotations

Identical to H060 §8.c:
- `mppm-rho1-{positive,marginal,negative}` per inner-CV out-of-fold MPPM(ρ=1) with stationary-bootstrap CI.
- `bocd-decay-flag-{raised,not-raised}`.
- `kelly-multiplier-best-fold-{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per fold; mode aggregate.
- `l-skewness-{positive,zero,negative}` per ADR-0019 on per-rebalance-period basket R-multiple distribution.  <!-- justify: TSMOM is structurally skew-positive on diversified-trend baskets; the CL addition is hypothesised to INCREASE positive L-skewness (episodic-supply-shock-driven CL contributions are right-tail events) — this is itself a KPI annotation to monitor at H061 emission -->
- `causal-mechanism-{causal,correlation-only,hybrid}` per §1.3; H061 is `hybrid`.

## 9. Power

Identical to H060 §9 modulo family size M=6 (vs M=5 at H060). At M=6 family + α=0.05 + N=24 monthly observations, minimum-detectable Sharpe-differential at 80% power is slightly tighter than H060 (~0.55-0.85). Power calibration deferred to `P1-H061-POWER-SIMULATION-EXECUTE` (BLOCKING per §11.2).

## 10. Decision rule

Identical to H060 §10.

- **Conjunctive PASS (all four primary survival-constrained metrics positive on bootstrap CI)** → operator-discretionary `paper-trade-active` promotion per ADR-0017 §3.
- **Any one primary metric covers zero** → stage transition `kpi-report-emitted`; NinjaScript implementation mandatory per ADR-0013 §5 (or operator-discretionary decline per the 2026-05-04 standing directive).
- **Any one primary metric strictly excludes zero on the negative side** → ADR-0019 `barbell-rebalance-candidate` flag raised.
- **`signal-decay-flag` raised** → record annotation in KPI report card; no automatic disposition change.
- **Power-shortfall** → `underpowered` annotation; operator-discretionary choice of aggregation cadence / sub-hypothesis collapse / OOS extension.

## 11. Kill switches and pre-launch BLOCKING preconditions

### 11.1 Hard kill-switch constraints (per ADR-0017 §5; mandatory inheritance from H060)

Identical to H060 §11.1, with CL added to K-4 and K-5 inventory:

- **K-1 Per-trade $-stop**: `1.0R` (Turtle 2N convention per [Faith 2007 *Way of the Turtle*](https://www.amazon.com/Way-Turtle-Secret-Methods-Successful/dp/0071486646), *practitioner*).
- **K-2 Per-trade time-stop**: 2× median holding period on calibration holdout.
- **K-3 No-add-to-loser** (zero exception).
- **K-4 Per-symbol cap** per ADR-0001: ES ≤ 20, NQ ≤ 40, **CL ≤ 5**, MGC ≤ 5, SIL ≤ 5.
- **K-5 Correlated-instrument inventory cap**: ES+MES share budget; NQ+MNQ share budget; **CL+MCL share budget** (NEW for H061; MCL inventory is zero at v1 since MCL is excluded, but the shared-budget rule is registered for future v2/v3 amendments); GC+MGC share budget; SI+SIL share budget.
- **K-6 Daily circuit breaker**: -2% of basket equity realised P/L → halt new entries.
- **K-7 Weekly circuit breaker**: -5% of basket equity realised P/L → halt new entries.
- **K-8 Adverse-direction entry filter**: per H060 §11.1 K-8 daily-cadence adaptation (TSMOM signal sign vs 5-day return sign + 0.5 ATR adverse-move filter).

### 11.2 Pre-launch BLOCKING preconditions (BLOCKING-BEFORE-LAUNCH)

| Follow-up | Status | Notes |
|---|---|---|
| `P1-H061-CL-SUBSTRATE-EXTRACTION-AUTHORIZE` | **OPEN (operator-action; ~$240 USD)** | the load-bearing BLOCKING follow-up; operator must approve the out-of-band Databento extraction per the 2026-05-12 cost dossier (`logs/databento_cost_dossiers/metals_energy_consolidated_2026-05-12.json`) at $239.82 USD for CL.FUT ohlcv-1m 2015-2025. |
| `P1-H061-CL-DATA-INGEST-RUN` | OPEN (depends on above) | after CL Stage A authorization, Stage B ingest + roll-adjustment per the Phase O.0 pattern; produces the CL partition under [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) and the new combined substrate SHA256. |
| `P1-H061-INSTRUMENTS-YAML-CL-ENTRY` | OPEN (~10 min) | adds CL entry to [config/instruments.yaml](../../../config/instruments.yaml); spec already enumerated in ADR-0023 §Decision 1 Tier-1. |
| `P1-H061-PIT-CANARY-INTEGRATION-TEST` | OPEN | BLOCKING; analogous to H060 PIT canary integration test (`P1-H060-PIT-CANARY-INTEGRATION-TEST` is closed per the H060 v1 run). |
| `P1-H061-POWER-SIMULATION-EXECUTE` | OPEN | BLOCKING; fills the §9 power-calibration placeholder at the new M=6 family size. |
| `P1-MONTHLY-ROLL-MODULE-IMPL` | CLOSED | landed pre-H060 v1; CL uses monthly roll-codes per the same module. |
| `P1-SESSION-POLICY-24-5-IMPL` | CLOSED | CL 24/5 with daily settlement per the H060 closure. |
| `P1-METALS-ENERGY-COST-MODEL-IMPL` | CLOSED | `NT8CrudeOilRthV1CostModel` available; activated only at v2-cost-aware emission. |
| `P1-MPPM-RHO-1-FITNESS-PRIMITIVE` | CLOSED | landed ADR-0018. |
| `P1-BOCD-DECAY-DETECTOR-PRIMITIVE` | CLOSED | landed ADR-0018. |
| `P1-L-SKEWNESS-PRIMITIVE-IMPL` | CLOSED | landed ADR-0018. |
| `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE` | CLOSED | landed ADR-0018. |

### 11.3 Concurrent inheritance preconditions (from ADR-0017 Phase L Thread A)

Same as H060 §11.3 — `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` and `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` remain OPEN per Phase L Thread A. H061 production walk-forward dispatch inherits the same BLOCKING status as H060.

## 12. Sample bias / robustness

- **Survivorship**: ES, NQ, CL, MGC, SIL are all live and continuously-active CME / NYMEX / COMEX contracts. CL has been continuously traded since 1983 (longer history than the v1 ES/NQ/metals legs combined). No survivorship bias.
- **Look-ahead**: identical to H060 §12.
- **Multiple-testing**: H061 is M=6 family (5 per-asset + 1 basket); intra-H061 family-wise correction by Benjamini-Hochberg FDR at α=0.05. Cross-hypothesis SPA family construction (across H050-H055-H060-H061) deferred to `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR` (inherited from H060).
- **Cross-asset correlation time-variation**: per §1.5; the CL leg adds the oil-equity decoupling regime that the H060 v1 basket cannot capture.

## 13. Robustness exhibits (informational; not load-bearing per ADR-0013 §1)

H061-specific sub-basket robustness exhibits (the load-bearing exhibits for the H061-vs-H060 comparison):

- **Sub-basket {ES, NQ}**: equity-pair-only sub-basket. Inherited from H060 §13. Low-breadth degenerate case.
- **Sub-basket {MGC, SIL}**: metals-pair-only sub-basket. Inherited from H060 §13.
- **Sub-basket {ES, NQ, MGC, SIL}**: the H060 v1 4-asset basket itself, re-computed on the H061 substrate + orchestrator for direct H061-vs-H060 comparison (BLOCKING for the H061 KPI report card's "does adding CL change the verdict?" question). The substrate SHA256 of the v1 4-asset slice within the H061 substrate must be byte-identical to the H060 v1 binding (`1247dc7e...`) per `P1-H061-V1-SUBSTRATE-INHERITANCE-VERIFY`.
- **Sub-basket {CL, MGC, SIL}**: commodity-pair-plus-energy sub-basket. NEW for H061; high-breadth potential; cross-commodity correlation tracking.
- **Full 5-asset basket {ES, NQ, CL, MGC, SIL}**: the H061 §1 primary basket; the load-bearing §1 family entry.
- **Look-back sensitivity**: 63 / 252 / 504-day lookback per H060 §13.
- **Vol-target sensitivity**: 5% / 10% / 15% vol-target per H060 §13.
- **Cost-floor sensitivity**: v2 only (v1 is zero-cost per §6).
- **ADR-0019 barbell-sibling exhibit**: pair the TSMOM basket with an ES long-OTM-put overlay; descriptive only.
- **Per-rebalance-cadence sensitivity**: weekly / monthly / quarterly cadence.

**Critical H061-specific exhibit**: side-by-side table of the {ES, NQ, MGC, SIL} sub-basket from H061 vs the H060 v1 KPI report card — every realized OOS / projected forward / R-multiple / Calmar / profit-factor / MPPM(ρ=1) metric must reconcile within numerical-noise floor (the orchestrator + substrate are byte-identical on this sub-basket per `P1-H061-V1-SUBSTRATE-INHERITANCE-VERIFY`). Any cross-cell disagreement is a build-defect, not a substantive finding. The substantive H_1 evidence is the **delta** between this sub-basket and the full 5-asset basket.

## 14. Reporting

Per [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) §3.2 (extended to 13 tables under ADR-0019 + 12 mandatory primary-metric tables under ADR-0017 §3.2); identical to H060 §14 modulo family size M=6.

| # | Table | Source |
|---|---|---|
| 1 | P/L (realized OOS, $10K starting capital) | per ADR-0017 §3.2 §1 |
| 2 | Drawdown (realized + projected) | per ADR-0017 §3.2 §2 |
| 3 | Sharpe — primary inference (T = SR_TSMOM − SR_passive_EW per §1; LW2008 CI) | per ADR-0013 §3 §3 |
| 3a | Calmar-differential — primary survival inference | per ADR-0017 §3.2 §3a |
| 3b | Profit-factor differential — primary survival inference | per ADR-0017 §3.2 §3b |
| 3c | R-multiple-mean — primary survival inference | per ADR-0017 §3.2 §3c |
| 4 | Annualised Sharpe | per ADR-0013 §3 §4 |
| 5 | Win/Loss/Zero counts + win rate | per ADR-0014 §5 |
| 6 | Forward 1-year projection (Median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%)) | per ADR-0013 §3.1 / ADR-0014 §6 |
| 7 | Hansen SPA family p (KPI annotation at M=6) | per ADR-0014 §7 |
| 8 | Other KPIs (best Kelly per fold, n_folds, MPPM(ρ=1), BOCD, L-skewness, causal-mechanism) | per ADR-0014 §8 |
| 9 | Methodological-correctness annotations | per ADR-0014 §9 |

Plus mandatory **bottom-line prose paragraph** (≤ 8 sentences) stating the primary inferential verdict + realised + projected $10K equity outcome + next mandatory stage transition + cross-link to full report card body. **H061-mandatory addition**: explicit side-by-side comparison table vs the H060 v1 4-asset basket (§13 critical exhibit).

## 15. NinjaScript implementation (mandatory per ADR-0013 §5)

H061 is **pure-C# implementable** (no Python inference at decision time); identical to H060 §15 modulo basket scope.

- **C# class**: `H061_TSMOM_CrossFutures_v2_with_CL` at `ninjascript/strategies/H061_TSMOM_CrossFutures_v2_with_CL.cs`.
- **Python-prototype hyperparameter mapping**: `h`, `H_halflife`, `vol_target`, `rebalance_cadence`, `kelly_multiplier` each map 1:1 to NinjaScript `[NinjaScriptProperty]` parameters.
- **Entry/exit logic**: 1:1 with Python signal generation (§3); cost model wired via [config/instruments.yaml](../../../config/instruments.yaml) per-instrument.
- **Kill-switch parameters**: K-1..K-8 per §11.1.
- **Fill-log schema**: matches plan §6.1.
- **Sim101 smoke-test record**: required post-implementation.
- **Python ↔ NinjaScript parity-check**: byte-equality on the integer signal vector per ADR-0013 §5.2; per-strategy calibration via `P1-H061-NINJASCRIPT-PARITY-TOLERANCE`.

## 16. Pre-registration freeze metadata

- **Substrate dataset_checksum**: TBD post-CL extraction. Recorded in [data_requirements.md](data_requirements.md) prior to first production walk-forward dispatch.
  - The {ES, NQ, MGC, SIL} subset of the H061 substrate MUST equal the H060 v1 binding `1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959` (verification under `P1-H061-V1-SUBSTRATE-INHERITANCE-VERIFY`).
  - CL partition SHA256: TBD post-extraction.
  - Combined H061 substrate SHA256: TBD.
- **Scientific payload SHA256**: computed at first orchestrator run; recorded at `runs/h061/<run_id>/sidecar.json`.
- **Reproducibility log path**: `logs/reproducibility/<run_id>.json`.
- **Git HEAD at pre-registration freeze**: recorded in the §17 revision log entry.
- **RNG seed**: `20260512_h061` (date-anchored; distinct from H060's `20260512` to avoid sharing bootstrap-index seeds across the two hypotheses' inference families).

## 17. Revision log

- **2026-05-12 — initial pre-registration draft; status `designed`.**
  - Author: skoir (independent researcher).
  - Inheritance: identical ADR stack to H060 — [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md), [ADR-0006](../../../docs/decisions/ADR-0006-scope-extension-hmm-0dte.md), [ADR-0007](../../../docs/decisions/ADR-0007-stacked-embargo-convention.md), [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-and-m1-degenerate.md), [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md), [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md), [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md), [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md), [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md).
  - Cherry-picked literature anchor: [Hamilton 1996, *J Monetary Economics* 38(2):215-220](https://doi.org/10.1016/S0304-3932(96)01282-2) "This is what happened to the oil price-macroeconomy relationship" — added at §1.3 to anchor the CL-specific oil-price-and-macro-uncertainty mechanism beyond the inherited MOP 2012 / Hong-Stein 1999 / Hurst-Ooi-Pedersen 2017 stack. All other primary anchors inherited from the H060 lit review at [research/01_hypothesis_register/H060/lit_review_H060_2026-05-12.md](../H060/lit_review_H060_2026-05-12.md) (no separate H061 lit review per the parent-instruction-pre-emption: H061's citation set is a strict superset of H060's plus the Hamilton 1996 anchor).
  - Basket scope: {ES, NQ, CL, MGC, SIL} (5 assets; full-size CL ADDED to the H060 v1 4-asset basket, NOT substituted for any v1 asset).
  - Causal-mechanism claim type (§1.3): `hybrid` (institutional CTA flow + Hong-Stein 1999 underreaction + Hamilton 1996 oil-macro mechanism on the CL leg).
  - Pre-launch BLOCKING preconditions: 5 open (CL-substrate-extraction-authorize, CL-data-ingest-run, instruments-yaml-CL-entry, PIT-canary-integration-test, power-simulation-execute) + 2 ADR-0017 Phase L Thread A residuals (failure-mode stress test, kill-switch backtest validation) + 7 closed preconditions inherited from H060.
  - Frozen §1-§7 immutability per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Frozen pre-registration amendment".
  - Audit-remediate-loop discipline: pre-registration draft inherits the H060 design.md audit posture (the H061 file is a structurally-modular extension of H060 with the basket scope as the sole substantive amendment); follow-on round-1 audit deferred until post-CL-substrate-extraction so the audit operates on a complete (non-substrate-pending) artifact.
