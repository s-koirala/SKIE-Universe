---
hypothesis_id: H062
schema_version: hypothesis_design_v1
status: designed
tier: 2b
created: 2026-05-14
created_by: skoir
description: Pre-registered design doc for hypothesis H062 — intraday N-bar Donchian-channel breakout on a 4-asset CME-Globex retail-tier basket {ES, NQ, MGC, SIL} at super-Kelly multiplier grid with BOCD decay-detector halt + switching-bandit redirect under the Phase N + Phase O.0 paradigm stack (ADR-0013 / ADR-0014 / ADR-0017 / ADR-0018 / ADR-0019 / ADR-0022 / ADR-0023).
---

# H062 — Intraday Donchian-channel breakout on {ES, NQ, MGC, SIL}

> **Aggressive-growth intraday channel-breakout on CME equity-index + metals futures.** H062 applies the canonical N-bar Donchian-channel breakout rule ([Faith 2007 *Way of the Turtle*, McGraw-Hill, ISBN 978-0071486644](https://www.amazon.com/Way-Turtle-Secret-Methods-Successful/dp/0071486646), *practitioner*) at 5-min intraday cadence on a 4-asset CME-Globex retail-tier basket {ES, NQ, MGC, SIL}, with super-Kelly position sizing per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-2 Kelly-multiplier grid + Bayesian Online Change-point Detection ([Adams-MacKay 2007 arXiv:0710.3742](https://arxiv.org/abs/0710.3742)) decay monitor + switching-bandit allocation redirect ([Garivier-Moulines 2011 *ALT* LNCS 6925:174-188 DOI 10.1007/978-3-642-24412-4_16](https://doi.org/10.1007/978-3-642-24412-4_16)). The hypothesis is the H062 entry in the ADR-0018 §Decision-1 "regime-conditional aggressive-growth paradigm" framing — designed to test whether intraday channel breakouts (a) retain a measurable but partially-decayed payoff at this cadence (per the [Lo 2004 AMH](https://doi.org/10.3905/jpm.2004.442611) framing: strategy decay is the null, not the alternative) and (b) admit super-Kelly position sizing under operator-discretionary oversight without triggering catastrophic OOS drawdown.
>
> **Full Phase N + Phase O.0 paradigm inheritance.** H062 inherits the unified survival-constrained / MPPM(ρ=1) / Kelly-grid / BOCD-decay / barbell payoff-shape / causal-mechanism / cross-futures-substrate stack: [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) permanent-exploration / no-binding-gates / mandatory-NinjaScript-terminus / non-loss preservation + [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) canonical 13-table results-summary + [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained primary metric vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) + drawdown-constrained Kelly + K-1..K-8 kill switches + FM-1..FM-5 stress-test suite + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) inner-CV fitness + Kelly-multiplier grid + BOCD signal-decay monitor + switching-bandit meta-strategy + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness annotation + barbell-rebalance-candidate flag + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism vs correlation-only annotation (§1.3) + [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate expansion.
>
> **Intraday channel-breakout — distinguished from H052a ORB + H060 daily TSMOM.** H062 uses a **rolling N-bar** Donchian channel (long on close above the past-N-bar high; short on close below the past-N-bar low) at 5-min cadence within RTH (for ES/NQ) or 24/5 (for MGC/SIL with single 16:00-17:00 CT maintenance break). This is structurally distinct from: (a) the H052a / H054 **time-anchored** opening-range-breakout (first-hour high/low), (b) the H055 wick-rejection mean-reversion signal, (c) the H060 daily-cadence monthly-rebalance TSMOM signal. H062 is the intraday-breakout entry in the H050-H055-H060 progression. The closest peer-reviewed validation literature is the Holmberg-Lönnbark-Lundström 2013 + Zarattini-Barbon-Aziz 2024 intraday ORB results; the closest *practitioner*-canonical anchor is Faith 2007 Turtle System 1 (`N=20` daily) + System 2 (`N=55` daily) geometrically rescaled to the 5-min cadence.
>
> **The hypothesis is honestly framed as a partially-decayed-factor test, NOT a strong-edge test** per the lit-review verdict in [lit_review_H062_2026-05-14.md](lit_review_H062_2026-05-14.md). Marshall-Cahan-Cahan 2008 *JBF* documents that 7846 trading rules including channel breakouts fail to produce statistically significant profits on commodity futures 1984-2005 after Romano-Wolf 2005 stepwise FWER correction; Hsu-Kuan 2005 *JFE* shows channel breakouts survive only on small-cap (Russell 2000) under SPA correction, NOT on large-cap (Nasdaq Composite); Park-Irwin 2007 meta-analysis documents declining technical-analysis profitability post-1990. The H062 expected basket MPPM(ρ=1) is framed as **slightly positive in the 0-0.3 annualized-log-wealth range** under H_1 with stationary-bootstrap CI excluding zero, NOT a Sharpe ~1 wager.

## 1. Hypothesis

- **H_0**: The intraday N-bar Donchian-channel breakout strategy at 5-min cadence on the 4-asset basket {ES, NQ, MGC, SIL} does NOT produce MPPM(ρ=1) > 0 on stationary-bootstrap CI per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1 over the 2024-01-01 → 2025-12-{03,19,30} OOS test fold; OR (alternatively framed against the survival-constrained primary metric vector per ADR-0017) at least ONE of {terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean} covers zero on its block-stationary-bootstrap CI.
- **H_1**: BOTH (a) basket MPPM(ρ=1) > 0 with stationary-bootstrap CI strictly excluding zero on the positive side AND (b) all four primary survival-constrained metrics excluded-zero-positive on their respective block-stationary-bootstrap CIs per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3 Pareto-front operator-review framing. Per-symbol family entries (`MPPM_{ρ=1,i}`, `T_H062_i = SR_breakout_i − SR_passive_BH_i`) reported under Romano-Wolf 2005 stepwise FWER family-wise control at α=0.05.
- **Predictand**: per-bar signed log-return on the entry-side of each Donchian-channel-breakout trade signal; per-trade R-multiple `R_t = realized_PL_t / |1R_t|` where `1R_t = entry_t ∓ k_atr × ATR_n,t` is the per-trade dollar-stop (Turtle 2N convention per Faith 2007, *practitioner*). Per-asset Sharpe / MPPM(ρ=1) / Calmar / profit-factor / R-multiple-mean computed on the per-trade R-multiple distribution per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py) (Phase L commit `546b828`).
- **Test statistic** (load-bearing): `T_H062_basket = MPPM(ρ=1)[r_basket_OOS_session_aggregated]` where `r_basket_OOS_session_aggregated` is the **equal-weighted basket per-session aggregated log-return series** across the 4 instruments on the OOS test fold. Per-session aggregation: for each session s and instrument i, `r_{i,s} = Σ_{trade t in session s} log(1 + R_{i,t} × per_trade_dollar_risk_t / equity_t)` (per-trade log-return contributions summed at the per-session level); basket per-session return `r_{basket,s} = (1/4) Σ_i r_{i,s}`. **MPPM(ρ=1) computation uses Δt = 1/252 (session-cadence)** per Goetzmann-Ingersoll-Spiegel-Welch 2007 §2 convention. **R1 F1-005 fix**: prior draft specified per-trade log-return series with Δt=1/252, which is dimensionally inconsistent (per-trade returns are event-driven and irregular-cadence; Δt must match input periodicity per GISW 2007 §2). The corrected per-session aggregation preserves the load-bearing inferential properties of MPPM(ρ=1) while ensuring dimensional consistency with the project-canonical daily Δt convention. **Primary inferential test**: paired stationary-bootstrap CI per [Politis-Romano 1994, *JASA* 89(428):1303-1313](https://doi.org/10.1080/01621459.1994.10476870) with block length per [Politis-White 2004, *Econometric Reviews* 23(1):53-70](https://doi.org/10.1081/ETC-120028836) + [Patton-Politis-White 2009, *Econometric Reviews* 28(4):372-375](https://doi.org/10.1080/07474930802459016) correction. Sharpe-differential family `T_H062_i = SR_breakout_i − SR_passive_BH_i` reported as **secondary KPI** per ADR-0017 §1.2 demotion machinery, under [Ledoit-Wolf 2008 *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap CI; Hansen 2005 SPA p reported as KPI annotation per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-and-m1-degenerate.md) at M=4 family size (per-symbol).

### 1.3 Causal-mechanism vs correlation-only annotation (per ADR-0022)

- **Claim type**: `hybrid` (upstream causal mechanism on the breakout-event-as-information-revelation layer; correlation-only refinement on the channel-N + k_atr + Kelly-multiplier parameter layers).
- **Mechanism description (who/what/why/when)**:
  - **WHO**: short-horizon discretionary momentum traders + algorithmic breakout-strategy traders + stop-order activation by inventory traders whose stops sit at the prior multi-bar high/low boundary. Stop-order liquidity at multi-bar pivot levels documented in the limit-order-book microstructure literature ([Bouchaud-Gefen-Potters-Wyart 2004, *Quantitative Finance* 4(2):176-190](https://doi.org/10.1080/14697680400000022); H055 §3 Component 3 lit anchor).
  - **WHAT**: programmatic flow into the breakout direction once price closes above/below the multi-bar channel — the channel-break itself is the *information event* that reveals buying/selling pressure has overcome the prior support/resistance level.
  - **WHY**: (i) underreaction to gradual information diffusion per [Hong-Stein 1999, *J Finance* 54(6):2143-2184](https://doi.org/10.1111/0022-1082.00184) — until the channel-break occurs the market is in a "no consensus" state; the channel-break is the signal that consensus has shifted; (ii) stop-order activation (mechanical liquidity at prior-channel boundaries) amplifies the post-break move; (iii) momentum-trader anchoring on round-number psychological levels per [Frazzini 2006, *J Finance* 61(4):2017-2046](https://doi.org/10.1111/j.1540-6261.2006.00896.x).
  - **WHEN**: persistent across regimes per the Hurst-Ooi-Pedersen 2017 137-year backtest at daily-grain; the intraday-cadence variant is structurally weaker — Marshall-Cahan-Cahan 2008 finds NO commodity-futures channel-breakout rule survives SPA correction over 1984-2005, indicating the intraday-grain decay is more aggressive than the daily-grain decay. Regime-dependent under [Lo 2004 AMH](https://doi.org/10.3905/jpm.2004.442611) — the H_1 expected basket MPPM is modest (0-0.3 annualized log-wealth) precisely because the underlying inefficiency has been substantially competed away.
- **E-value / robustness anchor**: VanderWeele-Ding 2017 E-value primitive **per `P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL` (STATUS OPEN — primitive not yet landed; R2-002 fix)**; target path on landing `src/skie_ninja/inference/e_value.py`. For H062 the E-value annotation is deferred to the first post-primitive KPI emission per ADR-0022 §3 (NOT calibrated pre-empirically here; KPI annotation is informational, not load-bearing for H_1). The 137-year Hurst-Ooi-Pedersen 2017 anchor at daily-grain is the structural robustness reference; the intraday H062 cadence is one cadence-shift below that anchor.
- **Channel-N + k_atr + Kelly-multiplier layers are correlation-only**: no causal claim about which channel-N is "correct" or which k_atr value is "the true stop". These are nuisance parameters selected by **MPPM(ρ=1) on inner-CV per ADR-0018 D-1** (channel-N + k_atr + cadence + Kelly-multiplier + switching-bandit-algo via cumulative-regret); ID_1 trend-filter is the only layer selected by Brier-score competition (§5.1; proper scoring rule for probabilistic side-prediction). **R2 F2-004 fix**: prior draft mistakenly attributed Brier-score selection to channel-N + k_atr (which produce continuous P/L, not probabilities); MPPM(ρ=1) is the load-bearing fitness per ADR-0018 D-1. The causal claim is on the channel-break-as-information-event mechanism; the parameterizations are operationalizations.

### 1.4 Pre-empirical caveat: H062 is a partially-decayed-factor test

This v1 is framed honestly as a **partially-decayed-factor test**, NOT a "strong non-decayed edge" wager. Three load-bearing peer-reviewed primary sources document material post-publication decay in the channel-breakout family:

- [Marshall-Cahan-Cahan 2008, *J Banking & Finance* 32(9):1810-1819](https://doi.org/10.1016/j.jbankfin.2007.12.011): tests 7846 trading rules (including channel breakouts) across 15 commodity futures 1984-2005 using a stepwise SPA + Romano-Wolf framework. **No rule generates statistically significant profits after multiple-testing correction.** This is the canonical commodity-futures-channel-breakout decay result.
- [Hsu, Po-Hsuan; Kuan, Chung-Ming (2005). "Reexamining the Profitability of Technical Analysis with Data Snooping Checks." *Journal of Financial Econometrics* 3(4):606-628, DOI 10.1093/jjfinec/nbi026](https://doi.org/10.1093/jjfinec/nbi026): N-bar channel breakouts survive [White 2000 Reality Check](https://doi.org/10.1111/1468-0262.00152) and Hansen 2005 SPA on small-cap Russell 2000 but FAIL on large-cap Nasdaq Composite. H062's universe is large-cap equity-index (ES, NQ) plus metals (MGC, SIL), aligned with the harder-to-beat regime. (Verified venue per R1 L1-004 fix: *Journal of Financial Econometrics*, NOT *Journal of Financial Markets* or *JFE* — the ambiguous *JFE* abbreviation in finance usually means *Journal of Financial Economics*, a different journal; full-venue spelling preserved.)
- [Park-Irwin 2007, *J Economic Surveys* 21(4):786-826](https://doi.org/10.1111/j.1467-6419.2007.00519.x): meta-analysis of 95 modern technical-analysis studies. Channel-breakout profitability concentrated pre-1990s; weakening post-1990. Application to H062's 2020-2025 OOS window: expect material decay from the Faith 2007 Turtle-system 1983-1988 historical record.

Expected basket MPPM(ρ=1) under H_1 is therefore framed at **0-0.3 annualized log-wealth** (NOT the canonical Turtle 1983-1988 Sharpe ~2-3 historical record). The H_1 inferential test is **whether the stationary-bootstrap CI on basket MPPM(ρ=1) excludes zero on the positive side**, not a Sharpe-vs-Turtle-headline comparison. This is per the [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §Context Adaptive Markets Hypothesis framing: strategy decay is the null, not the alternative.

### 1.5 Pre-empirical caveat on cross-asset correlation + diversification

The H062 basket {ES, NQ, MGC, SIL} spans equity-index (ES, NQ) and metals (MGC, SIL). Cross-asset correlation is empirically time-varying per the H060 §1.5 caveat (equity-commodity correlation flipped from ~-0.2 to +0.5 over the 1990s-post-2008 transition). ES-NQ correlation ≈ +0.85 to +0.95 collapses the equity pair to ~1 effective asset; MGC-SIL correlation ≈ +0.5 to +0.7 collapses the metals pair to ~1.3 effective assets. Effective basket breadth ≈ 2.3 not 4; the Grinold-Kahn 1999 √breadth multiplier is therefore ~1.52, not 2.0. This is the structural effective-breadth ceiling on H062's diversification gain; per-asset MPPM(ρ=1) is the load-bearing per-instrument inference, with the basket-level MPPM as the equal-weighted aggregation under the same Romano-Wolf FWER family.

## 2. Universe and sample period

- **Instruments at v1**: ES (E-mini S&P 500; CME), NQ (E-mini Nasdaq-100; CME), MGC (Micro Gold; COMEX-on-CME-Globex), SIL (Micro Silver; COMEX-on-CME-Globex). All front-month roll-adjusted continuous contracts. <!-- justify: 4-asset basket is the operationally-realised Phase O.0 post-Stage-B substrate; matches H060 v1; smallest credible cross-asset breadth that preserves equity vs metals dimensions at the ADR-0001 retail-capacity ceiling -->
- **Crude oil deferred to H061** (NYMEX WTI full-size CL): substrate-extraction cost ~$240 USD per the 2026-05-12 Databento cost-dossier exceeded operator's $80 budget ceiling at Phase O.0; reserved for the H061 / H062-v2 substrate-extension cycle per `P1-H062-V2-WITH-CL-MCL-EXTEND` follow-up.
- **MCL excluded from v1**: Micro WTI (MCL) is on disk in the post-Phase-O.0 substrate but the 2021-07-12 contract-inception date precludes the §2 2015-2019 calibration holdout per the H060 v1 amendment precedent.
- **Micros (MES/MNQ) NOT included at v1**: deterministic linear rescalings of ES/NQ per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md); not independent family members. Cost-equivalent micro-substitution is a sizing-layer detail (§4 capacity cap), not a signal-layer decision.
- **Substrate availability** (post-Phase-O.0 Stage B; binding):
  - **Verified `output_frame_sha256`**: `1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json) (run_id `eab2e95a73e44e3886d5a802b13da6bd`, timestamp 2026-05-12 21:27:40 UTC). **NOTE**: CLAUDE.md Phase O.0 ledger entry claims `242aaa280b216f45edc3b9d9de9630f52f71206eea7832c1cb0470296190f46f`; verified provenance reports `1247dc7e...`. H062 binds the verified provenance value; ledger reconciliation tracked under new follow-up `P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE`.
  - **Coverage per provenance**: ES 2020-2025 (6 partitions; no pre-2020 in this substrate frame), NQ 2020-2024 (5 partitions), MGC 2015-2025 (11 partitions), SIL 2015-2025 (11 partitions). Total H062 v1 universe = 33 partitions (broader 38-partition figure includes MCL, not used by H062 v1).
  - Per-symbol coverage details + cross-hypothesis fit-set isolation in [data_requirements.md](data_requirements.md).
- **Sample window** (BINDING; pre-reg-frozen):
  - **Calibration holdout**: 2015-01-01 → 2019-12-31 (5 years; MGC + SIL only — ES + NQ have zero pre-2020 substrate in the post-Phase-O.0 frame). Used for (i) metals-leg ID_1 trend-filter selection via Brier-score competition per §5.1, and (ii) metals-leg channel-N + k_atr + cadence + Kelly-multiplier selection via MPPM(ρ=1) inner-CV competition per §5.2 (R2 F2-004 residual fix: corrected from Brier-score to MPPM(ρ=1) for continuous-P/L parameter layers); equity-index channel-N + k_atr selected on inner-CV of IS instead. <!-- justify: disjoint from test folds of H050/H052a/H053/H054/H055/H060 per data_requirements.md cross-hypothesis fit-set isolation table; asymmetric ES/NQ coverage documented and accepted per H060 v1 precedent -->
  - **IS** (inner-CV grid search across §5 hyperparameter cells): 2020-01-01 → 2023-12-31 (4 years; matches H050 train + H055 IS + H060 IS window). All 4 v1 symbols have data covering the full IS window.
  - **OOS test**: per-symbol substrate right-edges: ES → 2024-01-01 → 2025-12-03; NQ → 2024-01-01 → 2024-12-19; MGC → 2024-01-01 → 2025-12-30; SIL → 2024-01-01 → 2025-12-30. Per-asset per-trade R-multiples are computed on each symbol's own OOS coverage; basket-level MPPM(ρ=1) is computed on the union of per-trade events across all 4 symbols.
- **Cadence**: **5-minute bars primary** for entry signal generation + channel computation; 1-min + 15-min as sensitivity exhibits per §13. <!-- justify: 5-min cadence balances over-fitting on 1-min noise vs under-sampling on 15-min; calibrated via MPPM(ρ=1) inner-CV competition per §5.2 (R2 F2-004 fix: prior draft said Brier-score competition; MPPM(ρ=1) is the canonical fitness for continuous-P/L signal selection per ADR-0018 D-1); the 5-min primary choice is empirically defended NOT pre-asserted -->
- **Session policy**:
  - ES + NQ: RTH-only at v1 (08:30-15:15 CT = 09:30-16:15 ET) <!-- justify: equity-index RTH-only matches H052a/H054/H055 convention; ETH bars admissible at feature-availability layer but not eligible for entry per §4 eligible-bar set -->
  - MGC + SIL: 24/5 with 16:00-17:00 CT maintenance-break exclusion <!-- justify: metals trade 24/5 on CME Globex per Phase O.0 clock.py extension; maintenance break is the single daily down-window; consistent with the [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py) `classify_energy_metals_session` per the 2026-05-12 `P1-SESSION-POLICY-24-5-IMPL` closure -->
  - **EOD flatten policy**: ES + NQ flatten at 15:00 CT (60 min before RTH close; conservative buffer); MGC + SIL flatten at 15:55 CT (5 min before daily settlement); intraday by definition. <!-- justify: EOD flatten eliminates overnight gap risk per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) intraday scope; ES/NQ 15:00 CT buffer per H052a convention; metals 15:55 CT per CME settlement bracketing -->
- **Roll treatment**: per-asset roll-adjusted front-month continuous series per the [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) post-Phase-O.0 deliverable (parameterized v0.4.0+ with `roll_rule.codes` per [config/instruments.yaml](../../../config/instruments.yaml); equity-index quarterly H/M/U/Z for ES + NQ; monthly F/G/H/J/K/M/N/Q/U/V/X/Z for MGC + SIL; per the 2026-05-12 monthly-roll-codes extension).

- **Cost model — ZERO at v1 (operator 2026-05-08 + 2026-05-12 standing decision; research-only pre-cost)**: Zero commissions, zero exchange fees, zero NFA fees, zero slippage applied at v1. Realized OOS equity is therefore the **pre-cost upper bound**; live + paper-trade P/L will be strictly less than v1 KPI report card. Empirical regime-wise cost calibration deferred to `P1-H062-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED-STAGE-TRANSITION per ADR-0017 §3 cost-modelling-realism). Methodological-correctness annotation `cost-zero-v1-pre-cost-research-only` will be carried in every KPI report card emitted at v1.

## 3. Features

All features are computed at 5-min bar close using only data available at time t-1 close (PIT-causal; one-bar-ahead causal structure). Feature panels are joined on `session_minute_et` (or `session_minute_ct` for metals) per the [H053 dtype-precision contract](../H053/design.md) (`pl.Datetime("ns", "UTC")` uniform across blocks).

- **Donchian channel** (per Faith 2007 Turtle System 1; *practitioner*):
  - `channel_high_t = max(close_{t-1}, close_{t-2}, ..., close_{t-N})` (N-bar rolling high; t-1 most recent confirmed bar).
  - `channel_low_t = min(close_{t-1}, close_{t-2}, ..., close_{t-N})` (N-bar rolling low).
  - Channel computed on close-to-close basis (NOT high/low intrabar extremes per Faith 2007 §3 Turtle convention).
  - `N` is grid-searched per §5 over {20, 40, 60, 120, 240, 480} 5-min bars. <!-- justify: N=20 + N=55 are Turtle System 1 + 2 canonical daily values per Faith 2007; geometric rescaling from daily-grain to 5-min intraday cadence uses the session-time-equivalent transform: 1 RTH session = 78 × 5-min bars; Turtle N=20 daily ≈ 1560 × 5-min bars at full RTH-only. The H062 N grid {20, 40, 60, 120, 240, 480} 5-min bars = {100min, 200min, 5hr, 10hr, 20hr, 40hr} brackets ~0.1 to ~6 RTH sessions, capturing the intra-session to multi-session breakout horizon explicitly — different from daily-grain Turtle but anchored on the same N-bar-channel mechanic at intraday resolution -->
- **Entry-bar breakout-event detector**:
  - **Long entry signal at bar t** (firing on bar-t close): `close_t > channel_high_t` AND bar t is the FIRST bar in the past `H_dwell` bars where this condition fires (prevents repeated re-entries while the channel is broken).
  - **Short entry signal at bar t**: `close_t < channel_low_t` AND first-fire condition.
  - **H_dwell** grid-searched per §5 over {1, 2, 5, 10} 5-min bars (re-arm dwell after channel reset).
- **ATR-stop sizing input**:
  - `ATR_n,t = Wilder_smoothing_n(TR_t)` where `TR_t = max(high_t - low_t, |high_t - close_{t-1}|, |low_t - close_{t-1}|)` is the bar-t true range per Wilder 1978 (*practitioner*).
  - **n** (ATR lookback) grid-searched per §5 over {14, 21, 60} bars.
- **Trend-strength filter** (per-instrument; selected on calibration holdout via Brier-score competition):
  - **ID_1 ∈ {a, b, c, d}**: trend-identifier ID selected from candidates: (a) TSMOM-sign per Moskowitz-Ooi-Pedersen 2012 (`sign(Σ_{i=1..L} r_{t-i})` with L grid-searched); (b) ADX threshold per Wilder 1978 (*practitioner*); (c) HAC-OLS log-price slope t-statistic per [Newey-West 1994, *RES* 61(4):631-653](https://doi.org/10.2307/2297912) for L≥60 and [Kiefer-Vogelsang 2002, *Econometrica* 70(5):2093-2095](https://doi.org/10.1111/1468-0262.00366) fixed-b for L<60; (d) MA-crossover sign.
  - ID_1 selection per §5.1 supervised Brier-score competition; per-instrument fit on the calibration holdout (MGC + SIL only) and inner-CV-bootstrapped on IS for ES + NQ.
  - Long entries require ID_1 ∈ {up, neutral}; short entries require ID_1 ∈ {down, neutral}. <!-- justify: H055 §3 Component 1 precedent; deterministic trend filter eliminates the "channel-break-against-trend-direction" failure mode without HMM dependency -->
- **News-time exclusion features** (eligible-bar gating per §4):
  - FOMC release timestamp (FRED `release_id`); NFP + CPI release timestamps (BLS calendar); OPEC ministerial-meeting timestamps (OPEC public meeting calendar; energy-specific — applies to crude in v2 but NOT to v1 universe which excludes CL/MCL; included here for v2 forward-compatibility).
  - News-calendar implementation: shared with H055 per `P1-H055-NEWS-CALENDAR-INGEST` (BLOCKING; status OPEN); H062 inherits the same primitive once it lands.

## 4. Label construction

Per-trade P/L on a Donchian-channel-breakout signal with ATR-scaled stop + opposite-channel exit + EOD-flatten.

- **Entry**: limit-or-market order at the next bar (t+1) open, conditional on (i) §3 channel-break detector fires at bar-t close, (ii) ID_1 trend-strength filter admits the side, (iii) bar t+1 is in the eligible-bar set (RTH-only ES/NQ + non-news-window).
- **Profit target**: NONE. Position runs until exit-on-opposite-channel-break OR EOD-flatten OR ATR-stop hit. <!-- justify: Turtle System 1 has no profit target — winners run to the opposite N-bar channel break or to the trailing 2N ATR stop; H062 inherits this no-target convention per the §1 skew-positive payoff structure (truncate left tail at stop, let right tail run) -->
- **Stop**: `SL = entry ± k_atr × ATR_n,t` where `k_atr` is grid-searched per §5 over {1.0, 1.5, 2.0, 2.5} (Turtle 2N convention + sensitivity neighbors). <!-- justify: Turtle 2N is the canonical k_atr=2.0 stop per Faith 2007; sensitivity neighbors at ±0.5 capture the "tighter stop" and "wider stop" alternatives that Crabel 1990 and Wilder 1978 (*practitioner*) discuss as alternative trade-management conventions -->
- **Time stop**: NONE at intraday cadence (the EOD-flatten serves as the implicit time-stop). <!-- justify: at 5-min cadence the longest channel-N=480 = 40-hour rolling window already crosses multiple sessions; an explicit time-stop on top of EOD-flatten would over-constrain the holding period and remove the System-1 "let winners run within the session" optionality -->
- **EOD flatten**: per §2 session policy — ES + NQ flatten at 15:00 CT; MGC + SIL flatten at 15:55 CT.
- **R-multiple definition**: `R_t = realized_PL_t / |1R_t|` where `|1R_t| = k_atr × ATR_n,t × point_value × contracts` is the dollar-distance to the ATR-stop. <!-- justify: per Tharp 1998 (*practitioner*) canonical R-multiple convention; the per-trade R-multiple is the load-bearing per-trade unit for ADR-0017 §3 inferential CI computation per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py) -->
- **pt_sl** convention: `pt_inf` (no profit target; close to ∞ for the AFML triple-barrier convention); `sl = k_atr × ATR_n,t`; `vertical_barrier = EOD-flatten time`. Compatible with AFML §3.5 triple-barrier labeller per the H053 + H055 precedent.
- **Capacity**: per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) hard cap per §5 sizing rule; cap applied AFTER Kelly multiplier and BEFORE order placement.

**Eligible-bar set** (binding pre-reg):
- (i) **Feature availability**: all 5-min channel + ATR + ID_1 trend-filter inputs present and non-NaN at bar close.
- (ii) **Session-time filter**: per §2 — RTH-only for ES/NQ; 24/5 with maintenance-break exclusion for MGC/SIL.
- (iii) **EOD-flatten buffer**: no NEW entries within 30 min of EOD-flatten time (15-min for metals); existing positions exit at EOD-flatten.
- (iv) **News-calendar exclusion**:
  - **FOMC release** ±15 min (per [Lucca-Moench 2015, *J Finance* 70(1):329-371](https://doi.org/10.1111/jofi.12196) pre-FOMC drift window; H055 §4 precedent).
  - **NFP release** ±5 min (BLS 08:30 ET release; treasury-futures-spike envelope per H055 §4).
  - **CPI release** ±5 min (BLS 08:30 ET release; same envelope-rationale).
  - **OPEC ministerial-meeting** ±15 min for any energy-leg in scope (v1 has no energy; included for v2 forward-compatibility).

## 5. Estimator

### 5.1 Trend-identifier selection methodology (Component 1; per-instrument)

Per-instrument supervised Brier-score competition on the §2 calibration holdout (2015-2019 for MGC + SIL; inner-CV bootstrap on IS 2020-2023 for ES + NQ due to substrate constraint):

- For each candidate `ID_1 ∈ {a, b, c, d}` and instrument `i ∈ {ES, NQ, MGC, SIL}`, fit the trend-gate parameters `{L, τ_M, τ_t, τ_MA, τ_ADX}` on a held-out fragment of the calibration holdout (2015-2018 for MGC+SIL; inner-CV folds for ES+NQ), then evaluate the side-skew Brier score on the remaining fragment:
  - `BS_i(ID_1) = mean over eligible bars of (ŷ_side_t − y_side_t)²`, where `ŷ_side_t ∈ {+1, 0, −1}` is the trend-filter's predicted side and `y_side_t ∈ {+1, −1}` is the realized sign of the next-`H_dwell`-bar log-return.
- Select `ID_1*_i = arg min_{ID_1} BS_i(ID_1)` per instrument.
- This is the H055 §5.1 + H060 §5.4 precedent pattern; the supervised target is the next-step return sign (proper scoring rule per [Niculescu-Mizil & Caruana 2005, ICML](https://www.cs.cornell.edu/~caruana/niculescu.scldbst.crc.rev4.pdf)).

### 5.2 Channel-N + k_atr + cadence selection (Components 2-3)

The channel-N + k_atr + cadence (5-min / 1-min / 15-min) joint grid is selected per-instrument by MPPM(ρ=1) on inner-CV out-of-fold per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1. The MPPM(ρ=1) primitive is at [src/skie_ninja/inference/mppm.py](../../../src/skie_ninja/inference/mppm.py) per `P1-MPPM-RHO-1-FITNESS-PRIMITIVE` (closed at ADR-0018 commit `40fb53d` per CLAUDE.md Phase L). Cadence is selected jointly with N + k_atr — 5-min is the primary CANDIDATE, not the pre-asserted choice. <!-- justify: ADR-0018 D-1 mandates MPPM(ρ=1) inner-CV fitness; cadence-as-hyperparameter ensures the 5-min primary framing is empirically validated rather than asserted -->

### 5.3 Kelly-multiplier grid (Component 4)

Per ADR-0018 D-2, position sizing applies a Kelly-multiplier grid `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` to the drawdown-constrained Kelly fraction per ADR-0017 §4.1. The Kelly-multiplier grid is selected per-fold by MPPM(ρ=1) per ADR-0018 D-1 with the additional ADR-0017 §4.1 drawdown-constrained ceiling. Super-Kelly cells {1.5, 2.0, 2.5} carry mandatory `super-kelly-operator-discretionary` annotation per ADR-0018 D-2 — the operator at promotion time reviews the per-fold-best-Kelly-multiplier annotation and may decline promotion when the selected cell is in the super-Kelly regime. <!-- justify: ADR-0018 D-2 Kelly-multiplier grid is the project-canonical Kelly-grid per the regime-conditional aggressive-growth paradigm; quarter-Kelly lower bound per MacLean-Thorp-Ziemba 2010 ruin-controlled regime; 2.5× upper bound is highest cell at which the ADR-0017 §4.1 drawdown-constrained Kelly remains theoretically defensible under per-trade ATR-stop sizing -->

The sizing formula per ADR-0017 §4.1 + ADR-0018 D-2 (R2 F2-002 + F2-003 fix: aligned with production `compute_position_size` at [src/skie_ninja/sizing/__init__.py](../../../src/skie_ninja/sizing/__init__.py) lines 311-438; `tick_value` removed from sizing formula as not used in production — tick_size dimension is the same as ATR's, and the contract `multiplier` converts price-distance to $-loss-per-contract):
```
position_size_t = floor(
    min(
        per_trade_risk_budget_t / (k_atr × ATR_n,t × multiplier),
        effective_kelly_t × equity_t / (entry_price_t × multiplier),
        retail_capacity_ceiling_i
    )
)
effective_kelly_t = clamp(f_kelly_raw_t × kelly_multiplier, 0, kelly_cap_upper)
where kelly_cap_upper = max(KELLY_MULTIPLIER_GRID_DEFAULT) = 2.5 per ADR-0018 D-2 (super-Kelly upper bound)
```
**Semantic**: the Kelly-multiplier SCALES `f_kelly_raw_t` linearly (not the cap); the absolute cap is `kelly_cap_upper = 2.5` per the ADR-0018 D-2 super-Kelly upper bound. At `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` and `f_kelly_raw_t = 1.0` (canonical full-Kelly raw f), the effective_kelly is `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` (matching ADR-0017 §4.1 quarter-Kelly base at multiplier=0.25 → effective=0.25; full-Kelly at multiplier=1.0; super-Kelly at multiplier ∈ {1.5, 2.0, 2.5}). Cells `multiplier > 1.0` carry mandatory `super-kelly-operator-discretionary` annotation per ADR-0018 D-2.

where:
- `per_trade_risk_budget_t` = 1.0R = 1% of `equity_t` (Turtle 2N convention's 1-unit risk).
- `f_kelly_raw_t` = Vince 1990 optimal-f per [src/skie_ninja/sizing/__init__.py](../../../src/skie_ninja/sizing/__init__.py) `kelly_fraction_from_r_multiples` (Phase L commit `0be0f30`).
- `equity_t` = CURRENT account equity (NOT starting equity; rebases as bankroll grows or shrinks per ADR-0017 §4.1 — the structural defense against the operator-pilot-ledger size-with-runup failure mode).
- `retail_capacity_ceiling_i` = ES 20 / NQ 40 / MGC 5 / SIL 5 contracts per ADR-0001.

### 5.4 BOCD signal-decay monitor (per ADR-0018 D-3)

A Bayesian Online Change-point Detection ([Adams-MacKay 2007 arXiv:0710.3742](https://arxiv.org/abs/0710.3742)) monitor on the rolling MPPM(ρ=1) path per fold. BOCD primitive at [src/skie_ninja/inference/bocd.py](../../../src/skie_ninja/inference/bocd.py) per `P1-BOCD-DECAY-DETECTOR-PRIMITIVE` (closed at ADR-0018 commit `40fb53d`). Change-point posterior > 0.5 on rolling MPPM(ρ=1) at run-length ≥ 3 folds → emit `signal-decay-flag` annotation in the KPI report card. KPI annotation per ADR-0018 — NOT a binding gate.

**Hazard rate**: `1/100` per H050 BOCD sensitivity finding 2026-05-12 (Adams-MacKay 2007 §2.2 default; empirically calibrated cell). Window size 60 trades per ADR-0018 D-3 standard. <!-- justify: hazard rate 1/100 is the H050 + H060 default; empirically calibrated under `P1-BOCD-HAZARD-RATE-EMPIRICAL` and `P1-BOCD-WINDOW-W-EMPIRICAL` follow-ups -->

### 5.5 Switching-bandit allocation redirect (per ADR-0018 D-4)

When `signal-decay-flag` raised by §5.4 BOCD monitor, the switching-bandit primitive at [src/skie_ninja/meta/switching_bandit.py](../../../src/skie_ninja/meta/switching_bandit.py) (per `P1-SWITCHING-BANDIT-META-STRATEGY`; BLOCKING-BEFORE-FIRST-META-STRATEGY-RUN; STATUS OPEN) redirects allocation to the next-best per-instrument arm; original arm retains a floor allocation (10% per ADR-0018 D-4) for revisiting per Lo 2004 AMH. <!-- justify: AMH framing means strategy decay is regime-conditional; decayed arm may regenerate alpha when regime shifts -->

**Algorithm selection** (pre-reg choice between D-UCB / SW-UCB and GLR-klUCB / CUSUM-UCB): selected per-instrument by **cumulative-regret minimization on calibration holdout** per the canonical bandit performance metric (Garivier-Moulines 2011 §3 + Besson-Kaufmann-Maillard-Seznec 2019 §4 both use cumulative-regret as the load-bearing comparison criterion; not Brier score). **R1 F1-004 fix**: prior draft prescribed Brier-score competition on the bandit-algorithm output, but Brier score is a proper scoring rule on probabilistic forecasts and D-UCB / GLR-klUCB produce arm-allocation decisions not probabilities — the Brier-score-on-bandit-output is methodologically ill-defined. Corrected criterion: simulate each bandit algorithm on the calibration holdout against the per-arm payoff distributions of the 4 instruments × 6 channel-N candidates × ID_1 × Kelly-multiplier cells; compute cumulative-regret per-instrument; select the per-instrument minimum-regret algorithm. The empirical selection criterion is documented per `P1-H062-SWITCHING-BANDIT-ALGO-REGRET-COMPETITION` (new follow-up; renamed from prior Brier-score version). <!-- justify: cumulative-regret is the canonical bandit performance metric per Garivier-Moulines 2011 + Besson-Kaufmann-Maillard-Seznec 2019; Brier-score on bandit output is not well-defined -->

### 5.6 Walk-forward outer CV

- **Outer walk-forward**: rolling 252-session-train / 60-session-test per [Bergmeir-Benítez 2012, *Information Sciences* 191:192-213](https://doi.org/10.1016/j.ins.2011.12.028) + [Tashman 2000, *Int J Forecasting* 16(4):437-450](https://doi.org/10.1016/S0169-2070(00)00065-0); embargo per [ADR-0007](../../../docs/decisions/ADR-0007-stacked-embargo-convention.md) stacked-embargo convention.
- **Roll cadence**: monthly per the H055 + H060 precedent.
- **Purge + embargo** (R2 F2-006 fix: purge vs embargo distinction made explicit per López de Prado 2018 *AFML* §7.4.1 + §7.4.2):
  - **Purge** = feature-warm-up gap (protects test from train-fitted features bleeding through). For H062, max channel-N = 480 bars × 5 min/bar = **2400 min purge** ensures the test-fold first eligible bar has a fully-warm channel state computed entirely from train-fold-or-prior bars.
  - **Embargo** = label-horizon gap (protects test labels from depending on train-fold future bars per AFML §7.4.2). For H062, the label horizon is bounded by §4 EOD-flatten = **max session duration ≈ 1380 min** (24/5 metals leg; 405 min for ES/NQ RTH). Conservative embargo = **2400 min** covers the 24/5 label horizon by a 1.74× margin.
  - **Total purge+embargo gap** = 2400 + 2400 = **4800 min** between train-fold last bar and test-fold first eligible bar.
- Session-equivalents (with 1 RTH session = 405 min ES/NQ; 1 24/5 session = 1380 min): purge 2400 / 405 ≈ **5.93 RTH-equivalent sessions** (ES/NQ leg); 2400 / 1380 ≈ **1.74 24-5-equivalent sessions** (MGC/SIL leg). Total purge+embargo gap of 4800 min covers ~11.9 RTH sessions or ~3.5 24-5 sessions. Pre-reg-pinned at **`embargo = 2400 minutes`** (canonical unit; session-equivalents per the §2 session policy). Unit-test BLOCKING precondition per §11.2 `P1-H062-LEVEL-STATE-FOLD-CONTINUITY` (analogous to H055's intraday channel-N reset at session boundary unit test). Channel-state-at-fold-boundary policy: **channel state computed on full continuous PIT-causal panel; embargo ensures train-fold last-bar precedes test-fold first-eligible-bar by ≥ max-channel-N + embargo_minutes (= 480 × 5 + 2400 = 4800 minutes total). Unit test verifies bit-identical channel values regardless of fold partition** (R1 F1-007 fix: pre-registers the canonical AFML §7.4 walk-forward purged convention so the channel state persists PIT-causally across fold boundaries; the purge+embargo handles the leak surface).
- **Inner CV**: 3-fold purged walk-forward on each IS fold per López de Prado AFML §7.4 ([López de Prado 2018 *AFML* Wiley ISBN 978-1119482086](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086); *practitioner*).

### 5.7 Inner-CV selection metric

Inner-CV cell selection: **MPPM(ρ=1)** per ADR-0018 D-1 on the inner-CV out-of-fold per-session-aggregated basket log-return series (per §1 corrected predictand). Risk-aversion parameter `ρ = 1` matches the log-utility / Kelly-criterion-consistent regime per Goetzmann-Ingersoll-Spiegel-Welch 2007 §2 + MacLean-Thorp-Ziemba 2010 Ch. 1. **R1 L1-003 fix**: prior draft used "Ingersoll-Spiegel-Goetzmann-Welch" author order (which matches the early SSRN preprint abstract_id=1151564) but the canonical published-RFS author order is "Goetzmann-Ingersoll-Spiegel-Welch" per [Goetzmann-Ingersoll-Spiegel-Welch 2007, *RFS* 20(5):1503-1546, DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025).

### 5.8 Inner-CV regularisation discipline + nested-CV structure (R1 F1-006 fix)

**Two-level nested inner-CV structure** for ES + NQ trend-filter selection vs main cell-grid selection (mandatory per [Varma & Simon 2006 *BMC Bioinformatics* 7:91](https://doi.org/10.1186/1471-2105-7-91); without nested CV the joint selection on a shared inner-CV partition produces optimistic-bias):

- **Level-A (ID_1 trend-filter selection)**: for ES + NQ, the inner-CV bootstrap operates on the **first 2 years of IS (2020-01-01 → 2021-12-31)**; this is the ID_1 fitting + selection partition.
- **Level-B (channel-N + k_atr + cadence + Kelly-multiplier + switching-bandit-algo joint cell-grid selection)**: for ES + NQ, the inner-CV operates on the **last 2 years of IS (2022-01-01 → 2023-12-31)**, disjoint from Level-A by construction.
- **For MGC + SIL**: ID_1 trend-filter selection per §5.1 uses the **2015-2017 fragment** of the calibration holdout (3 years; ~750 sessions); channel-N + cell-grid selection per §5.2 uses the **2018-2019 fragment** (2 years; ~500 sessions) — cross-asset SYMMETRY with the ES/NQ Level-B (2022-2023) is preserved. **R2 F2-007 fix**: prior draft used 2018 single-year + 2019 single-year for the metals leg which was under-powered (250 sessions over the 864-cell joint grid → ratio 0.3); the corrected 2015-2017 ID_1 + 2018-2019 cell-grid 2-year split brings the metals Level-B sample-to-cell ratio to ~0.6, matching the ES/NQ Level-B. The metals leg still has tighter TPE-coverage K_max constraint than ES/NQ per Bergstra-Bengio 2012 §2.2; pre-reg-pinned mandatory annotation `metals-cell-grid-tpe-coverage-{stable, narrow}` per the realized TPE-explored cardinality at first run.

Prevention of inner-CV overfit on the joint cell grid (cadence × N × k_atr × ID_1 × Kelly-multiplier × switching-bandit-algo): (i) Level-A / Level-B disjointness per above (no fold leak between ID_1 and main-cell-grid selection); (ii) purged-walk-forward inner CV per López de Prado 2018 *AFML* Ch.7 with purge = embargo per §5.6 at the intraday-cadence layer; (iii) cell selection by MPPM(ρ=1) (not raw Sharpe) per ADR-0018 D-1; (iv) per-fold cell-selection stability tracked as a sensitivity exhibit (the project's standing nested-CV-overfit guard per `P1-ADR-0015-NESTED-CV-PROTOCOL-PRIMITIVE`).

## 6. Cost model

- **v1: ZERO-cost research-only** per the 2026-05-08 + 2026-05-12 operator standing directive (`cost-zero-v1-pre-cost-research-only` annotation). KPI report card explicitly reports v1 realized OOS as the pre-cost upper bound.
- **v2 cost model** (deferred per `P1-H062-COST-EMPIRICAL-CALIBRATION`):
  - ES, NQ: existing [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py).
  - MGC: new `NT8GoldRthV1CostModel` per `P1-METALS-ENERGY-COST-MODEL-IMPL` (BLOCKING per ADR-0023; STATUS OPEN).
  - SIL: new `NT8SilverRthV1CostModel` per `P1-METALS-ENERGY-COST-MODEL-IMPL` (BLOCKING; STATUS OPEN).
  - Per-trade log-return drag `log(1 - cost_round_trip / notional)` per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3.1 F-CONV-2 binding.
  - Cost-floor sensitivity exhibit: 1-tick slippage primary; 2-tick slippage as sensitivity per ADR-0013 §3.1 convention.

## 7. No look-ahead

- Channel-high/low at bar t uses information up to and including bar t-1 close (channel = max/min of closes through t-1).
- ATR_n,t at bar-t close uses Wilder-smoothed TR series through bar t inclusive (TR_t is known at bar-t close per the §3 formula); entry at bar t+1 open uses ATR_n,t computed at bar-t close. <!-- R1 F1-012 fix: temporal indexing clarified — ATR_n at bar-t close requires bar-t TR (TR_t known at bar-t close); the signal+ATR-stop pair is computed at bar-t close and frozen for bar t+1 execution -->
- ID_1 trend-filter at bar t uses lookback features through t-1.
- Entry at bar t+1 open (next-bar execution after t close signal).
- Stop monitored intrabar (NOT at bar close — H062 simulates intrabar stop-fill at the stop price; if `low_{t+1} <= stop_price` for a long position, stop fills at `stop_price` not at `close_{t+1}`). **Gap-through-stop convention**: if `open_{t+1} < stop_price` for a long position (open gaps adversely through the stop), the stop fills at `open_{t+1}` not at `stop_price` (adverse-fill semantic per López de Prado 2018 *AFML* §13 event-driven backtest convention; R1 F1-013 fix — explicitly pre-registered to avoid ambiguity at v2 cost-realism calibration time).

This is canonical event-driven backtest convention per López de Prado 2018 *AFML* §13 + the H055 §7 precedent. PIT-causality is unit-tested per `P1-H062-PIT-CANARY-INTEGRATION-TEST` (BLOCKING per §11.2) using the project's standing Cycle-4 leak-canary discipline (boundary invariant + label-horizon purge check + dual fit-call observer per [src/skie_ninja/backtest/](../../../src/skie_ninja/backtest/) `WalkForwardEngine` + `TracingArray`).

## 8. Gate thresholds (per ADR-0013; KPI-only, no binding gates)

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1, no KPI value forces or blocks any stage transition. Every former Class A item is reported as a KPI annotation.

### 8.a Methodological-correctness annotations (per ADR-0013 §2)

- `leakage-canary-{pass,fail}` per §11.2 PIT canary suite.
- `bss-{positive,flat,negative}` per inner-CV out-of-fold isotonic-calibrated forecast vs equal-weighted-passive climatological prior (applicable if Brier-score competition outputs are entered into a probabilistic forecast; flagged `bss-n/a` if not).
- `reliability-in-band` ∈ [0.7, 1.3] / `reliability-out-of-band` per [Niculescu-Mizil & Caruana 2005](https://www.cs.cornell.edu/~caruana/niculescu.scldbst.crc.rev4.pdf) reliability-diagram concept.
- `repro-log-{complete,incomplete}` per ADR-0009 13-field schema.
- `cost-zero-v1-pre-cost-research-only` (v1 fixed annotation per §6); `cost-{robust,conditional,flat}` per §6 v2 sensitivity exhibit (post `P1-H062-COST-EMPIRICAL-CALIBRATION`).
- `dsr-{positive,marginal,negative,n/a}` per [Bailey-López de Prado 2014 *JPM* 40(5):94-107](https://doi.org/10.3905/jpm.2014.40.5.094) deflated-Sharpe at family size M = (cadences × channel-N × k_atr × ID_1 × Kelly-multiplier × switching-bandit-algo) × 4 instruments = 3 × 6 × 4 × 4 × 6 × 2 × 4 = **13,824 per-cell-per-symbol cells** before TPE coverage; H062 K_max=500 TPE-explored subset yields per-symbol coverage ~14.5%. Per `P1-H062-DSR-FAMILY-SIZE-RECONCILE` follow-up the family size is bound at first-run by the realized TPE-explored trial set per the H055 K_max=500 + Hansen 2005 §2.4 TPE-coverage convention.
- **R2 F2-013 fix** — ADR-0017 §6 FM-1..FM-5 synthetic-failure-mode stress-test annotations (MANDATORY-INHERITANCE-FROM-H055-FORWARD):
  - `stress-test-FM-1-{pass,fail}` — death-by-thousand-cuts scenario.
  - `stress-test-FM-2-{pass,fail}` — gap-overnight scenario.
  - `stress-test-FM-3-{pass,fail}` — news-spike scenario.
  - `stress-test-FM-4-{pass,fail}` — latency-induced-bad-fill scenario.
  - `stress-test-FM-5-{pass,fail}` — regime-change-mid-trade scenario.
  - Pass criteria are NOT binding gates per ADR-0013 §1 + §2 no-gates philosophy preserved; failures are recorded as `stress-test-FM-N-fail` annotations in [failure_log.md](failure_log.md) per ADR-0017 §6. Implementation per `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` (BLOCKING per §11.2).

### 8.b Performance KPIs (per ADR-0017 §3 primary metrics; per ADR-0013 §B preserved)

**Primary (per ADR-0017 §3 Pareto-front operator review)**:
- `tw-q05-{above-half,above-zero,below-zero}`: terminal-wealth-q05 on $10K-starting 252-session forward bootstrap projection per ADR-0013 §3.1; primitive at the (deferred) `P1-FORWARD-PROJECTION-PRIMITIVE` consolidation module; reference implementation [scripts/simulate_h050_v1_10k_2026.py](../../../scripts/simulate_h050_v1_10k_2026.py).
- `calmar-diff-{positive,marginal,negative}`: Calmar-differential vs passive-equal-weight benchmark; CI per [src/skie_ninja/inference/calmar.py](../../../src/skie_ninja/inference/calmar.py) (Phase L commit `546b828`).
- `pf-diff-{positive,marginal,negative}`: profit-factor differential; CI per [src/skie_ninja/inference/profit_factor.py](../../../src/skie_ninja/inference/profit_factor.py) (Phase L commit `546b828`).
- `r-multiple-mean-{positive,marginal,negative}`: per-trade R-multiple mean; CI per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py) (Phase L commit `546b828`).

**Secondary (Sharpe-family preserved as academic-comparability KPI per ADR-0017 §3)**:
- Sharpe-vs-passive-BH LW2008 differential CI (basket level + per-symbol Romano-Wolf 2005 stepwise FWER family).
- Sharpe-vs-AR(1)-lag-1-bench LW2008 differential CI.
- Hansen 2005 SPA p-value at M = (cadences × channel-N × k_atr × ID_1 × Kelly-multiplier × switching-bandit-algo) × per-symbol — KPI annotation per ADR-0008; not load-bearing for H_1.

### 8.b.1 Risk-of-ruin probability (per ADR-0017 §4.2; MANDATORY — R2 F2-001 fix)

ADR-0017 §4.2 mandates a risk-of-ruin Monte Carlo computation in every KPI report card emitted from 2026-05-08 forward. Primitive at [src/skie_ninja/inference/risk_of_ruin.py](../../../src/skie_ninja/inference/risk_of_ruin.py) (Phase L commit `0be0f30`; closed). H062 inherits the ADR-0017 §4.2 mandate via the §1 + §17 inheritance list.

- `risk-of-ruin-probability-{above-X, below-X}` annotation per ADR-0017 §4.2.
- **ruin_threshold**: 50% of starting bankroll (= $5,000 on $10K starting; project-canonical default per Vince 1990 *Portfolio Management Formulas* Ch. 4 + Feller 1968 *Probability Theory* Vol. I Ch. XIV "Gambler's Ruin").
- **n_paths**: 5000.
- **n_sessions**: 252.
- **sizing_mode**: `r_multiple_with_compute_position_size` per [src/skie_ninja/sizing/__init__.py](../../../src/skie_ninja/sizing/__init__.py) `compute_position_size` (§5.3 formula).

### 8.c ADR-0018 / ADR-0019 / ADR-0022 annotations

- `mppm-rho1-{positive,marginal,negative}` per inner-CV out-of-fold MPPM(ρ=1) with stationary-bootstrap CI per ADR-0018 D-1. **This is the LOAD-BEARING H_1 inferential annotation** per §1.
- `bocd-decay-flag-{raised,not-raised}` per §5.4 BOCD monitor at posterior > 0.5 + run-length ≥ 3 folds.
- `kelly-multiplier-best-fold-{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per fold; aggregate annotation `kelly-multiplier-mode = mode(per-fold-best)`.
- `super-kelly-operator-discretionary` annotation if `kelly-multiplier-mode ∈ {1.5, 2.0, 2.5}` per ADR-0018 D-2 super-Kelly operator-discretionary clause.
- `switching-bandit-algo-{D-UCB, GLR-klUCB}` per §5.5 cumulative-regret-minimization winner (R2 F2-005 fix: prior draft referenced Brier-score competition; corrected per §5.5 + F1-004).
- `l-skewness-{positive,zero,negative}` per ADR-0019 on per-trade basket R-multiple distribution; L-skewness primitive at [src/skie_ninja/inference/skewness.py](../../../src/skie_ninja/inference/skewness.py) per `P1-L-SKEWNESS-PRIMITIVE-IMPL` (closed at ADR-0018 commit `40fb53d`). <!-- justify: H062 expected payoff-shape is `skew-positive` per Donchian-channel-breakout construction (truncate left tail at ATR-stop; let right tail run via opposite-channel exit). ADR-0019 §3 barbell-rebalance-candidate flag is raised if τ_3 < 0 (a negative-skew channel-breakout strategy is a structurally-non-trend-following artifact) -->
- `causal-mechanism-{causal,correlation-only,hybrid}` per §1.3 ADR-0022 annotation; H062 is `hybrid`.

## 9. Power

- **Pre-empirical estimate**: at the channel-N range {20, 40, 60, 120, 240, 480} 5-min bars and the IS range 2020-2023 (4 years; ~1000 RTH sessions per symbol), expected per-symbol entry frequency is ~3-15 breakouts/session for N=20 (high) decreasing to ~0.05-0.3 breakouts/session for N=480 (low). Total per-symbol trade count over IS ≈ 50-15000 depending on N; basket trade count ≈ 200-60000 depending on N + per-symbol coverage.
- **Power calibration** at the H062 family size M ≈ {cadence × channel-N × k_atr × ID_1 × Kelly-multiplier × switching-bandit-algo × 4 instruments} = TPE-explored realized set (cardinality ≤ K_max = 500 per fold by analogy with H055 §9.1) is **deferred to `P1-H062-POWER-SIMULATION-EXECUTE`** (BLOCKING per §11.2; analogous to H055 `P1-H055-POWER-SIMULATION-EXECUTE`). The minimum-detectable basket MPPM(ρ=1) at α=0.05 + power=0.80 at the realized N_OOS_basket-trade count is bound at first power-simulation run.

## 10. Decision rule

Per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3 Pareto-front operator review on the four primary survival-constrained metrics + ADR-0018 D-1 MPPM(ρ=1) inferential CI as the binding H_1 entry:

- **Conjunctive PASS** (basket MPPM(ρ=1) CI excludes zero positive AND all four primary survival-constrained metrics excluded-zero-positive on bootstrap CI) → operator-discretionary `paper-trade-active` promotion per ADR-0017 §3.
- **Basket MPPM(ρ=1) excludes zero positive but one or more survival-constrained metrics cover zero** → stage transition `kpi-report-emitted`; NinjaScript implementation mandatory per ADR-0013 §5 (or operator-discretionary decline per the 2026-05-04 standing directive per the H052a precedent).
- **Basket MPPM(ρ=1) CI covers zero** → stage transition `kpi-report-emitted` with `mppm-rho1-marginal-or-negative` annotation; the underlying null disposition of the H_1 hypothesis is documented; operator decides on NinjaScript implementation per ADR-0013 §5.3 operator-discretionary clause.
- **Basket MPPM(ρ=1) CI strictly excludes zero on the negative side** → ADR-0019 `barbell-rebalance-candidate` flag raised; suggest convex-hedge sibling hypothesis with long-OTM-options leg per ADR-0019 §3.
- **`signal-decay-flag` raised** (BOCD posterior > 0.5 at run-length ≥ 3 folds per §5.4) → record annotation in KPI report card; no automatic disposition change (KPI-only per ADR-0018).
- **`super-kelly-operator-discretionary` annotation raised** → operator review of the per-fold Kelly-multiplier-mode at promotion time; the operator may decline promotion when the selected cell is in the super-Kelly regime per ADR-0018 D-2.
- **Power-shortfall** (minimum-detectable basket MPPM(ρ=1) at realized N_OOS exceeds the empirical effect size by > 2×) → emit `underpowered` annotation in the R-multiple-mean CI per Phase L n<30 boundary discipline; operator-discretionary on whether to (a) collapse to per-symbol sub-hypothesis with M=1 family (H062a / H062b / H062c / H062d sibling spinoff), (b) extend OOS by relaxing the OOS-right-edge constraint at substrate-extension time.

## 11. Kill switches and pre-launch BLOCKING preconditions

### 11.1 Hard kill-switch constraints (per ADR-0017 §5; mandatory inheritance from H055-forward)

- **K-1 Per-trade $-stop**: `1.0R` at ATR-scaled `k_atr × ATR_n,t × point_value × contracts` (Turtle 2N convention per Faith 2007; *practitioner*).
- **K-2 Per-trade time-stop**: `2 × median_winning_trade_duration` computed on the calibration holdout (MGC + SIL 2015-2019) + inner-CV bootstrap on IS 2020-2023 (ES + NQ), per [ADR-0017 §5 K-2 mandate](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md). Empirical value pinned at first `P1-H062-CALIBRATION-HOLDOUT-RUN` execution; if the empirical 2× median holding-time exceeds the EOD-flatten boundary (§4), the EOD-flatten serves as the binding upper bound (whichever fires first). **R1 F1-002 fix**: prior draft asserted K-2 = NONE with EOD-flatten as implicit; this re-interpreted the ADR-0017 §5 K-2 mandate without a project-level amendment. The empirically-calibrated 2× median winning-trade duration is the canonical per-trade K-2 time-stop; EOD-flatten is the additional structural per-session boundary (binding whichever fires first).
- **K-3 No-add-to-loser** (zero exception): channel-break signal flip closes the prior position; new entry is fresh.
- **K-4 Per-symbol cap** per ADR-0001: ES ≤ 20, NQ ≤ 40, MGC ≤ 5, SIL ≤ 5 contracts.
- **K-5 Correlated-instrument inventory cap**: ES + MES inventory shares budget; NQ + MNQ inventory shares budget; MGC + GC inventory shares budget; SIL + SI inventory shares budget. Cross-asset cap (ES + NQ equity-pair shared budget) deferred per `P1-H062-CROSS-ASSET-CAP-SUCCESSOR`.
- **K-6 Daily circuit breaker**: -2% of basket equity realised P/L → halt new entries through end of session. <!-- justify: ADR-0017 §5 K-6 default convention; literature-canonical retail-trader risk threshold (R1 F1-010 fix) -->
- **K-7 Weekly circuit breaker**: -5% of basket equity realised P/L → halt new entries through end of week. <!-- justify: ADR-0017 §5 K-7 default convention; literature-canonical retail-trader risk threshold (R1 F1-010 fix) -->
- **K-8 Adverse-direction entry filter**: forbid new entries when ID_1 trend-filter side disagrees with channel-break direction AND price has moved adversely > 0.5 ATR from channel-break level at fill time (§3 ID_1 trend-strength filter is the load-bearing K-8 implementation).

### 11.2 Pre-launch BLOCKING preconditions (BLOCKING-BEFORE-LAUNCH)

These follow-ups MUST land before H062 production walk-forward dispatch:

| Follow-up | Status | Notes |
|---|---|---|
| `P1-MPPM-RHO-1-FITNESS-PRIMITIVE` | CLOSED | Landed ADR-0018 commit `40fb53d`; ADR-0018 D-1 inner-CV fitness primitive at [src/skie_ninja/inference/mppm.py](../../../src/skie_ninja/inference/mppm.py). |
| `P1-BOCD-DECAY-DETECTOR-PRIMITIVE` | CLOSED | Landed ADR-0018 commit `40fb53d`; primitive at [src/skie_ninja/inference/bocd.py](../../../src/skie_ninja/inference/bocd.py). |
| `P1-L-SKEWNESS-PRIMITIVE-IMPL` | CLOSED | Landed ADR-0018 commit `40fb53d`; primitive at [src/skie_ninja/inference/skewness.py](../../../src/skie_ninja/inference/skewness.py). |
| `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE` | CLOSED | Landed ADR-0018 commit `40fb53d`. |
| `P1-CALMAR-DIFFERENTIAL-CI-IMPL` | CLOSED | Landed Phase L commit `546b828`. |
| `P1-PROFIT-FACTOR-CI-IMPL` | CLOSED | Landed Phase L commit `546b828`. |
| `P1-R-MULTIPLE-CI-IMPL` | CLOSED | Landed Phase L commit `546b828`. |
| `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE` | CLOSED | Landed Phase L commit `0be0f30`. |
| `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE` | CLOSED | Landed Phase L commit `0be0f30`. |
| `P1-SWITCHING-BANDIT-META-STRATEGY` | **CLOSED 2026-05-14** | Landed Phase O.1 follow-on; [src/skie_ninja/meta/switching_bandit.py](../../../src/skie_ninja/meta/switching_bandit.py) — DUCBBandit + SWUCBBandit + GLRKLUCBBandit + EXP3SBandit + `select_bandit_by_regret`; smoke-tested 4-arm 100-step regret + cumulative-regret selection. |
| `P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL` | **CLOSED 2026-05-14** | Landed Phase O.1 follow-on; [src/skie_ninja/inference/e_value.py](../../../src/skie_ninja/inference/e_value.py) — VanderWeele-Ding 2017 E-value primitive (RR-scale + SMD-to-RR approximation); smoke-tested for RR=2 → 3.414, RR=0.5 → 3.414 (symmetric), CI-crosses-null → 1.0. |
| `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` | **CLOSED (status drift corrected 2026-05-14)** | Previously marked OPEN; verified landed at [scripts/stress_test_failure_modes.py](../../../scripts/stress_test_failure_modes.py) (257 lines; FM-1..FM-5 CLI). H062 §11.2 status was inherited from CLAUDE.md ledger drift; corrected here. |
| `P1-H062-NEWS-CALENDAR-INGEST` | **CLOSED (status drift corrected 2026-05-14)** | Previously marked OPEN; verified landed at [src/skie_ninja/utils/news_calendar.py](../../../src/skie_ninja/utils/news_calendar.py) (383 lines; FOMC + NFP + CPI + static fallback per H055 §4). H062 inherits the existing primitive; OPEC release-calendar for v2 deferred. |
| `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` | OPEN | BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH; wires K-1..K-8 into Cycle-4 leak-canary discipline at orchestrator layer. |
| `P1-ADR-0017-DESIGN-MD-CASCADE` | OPEN | BLOCKING-BEFORE-NEXT-STAGE-3-RUN; project-wide §10 reframing across H050/H051/H052a/H052b/H053/H054. |
| `P1-ADR-0018-DESIGN-MD-CASCADE` | OPEN | BLOCKING-BEFORE-NEXT-STAGE-3-RUN; project-wide MPPM(ρ=1) cascade. |
| `P1-CAUSAL-DAG-DESIGN-MD-TEMPLATE` | OPEN | BLOCKING-BEFORE-NEXT-NEW-PRE-REG; §1.3 stub per ADR-0022. |
| `P1-QUANT-PROJECT-RULES-CAUSAL-IMPORT` | OPEN | BLOCKING-BEFORE-NEXT-NEW-PRE-REG; user-level rules amendment. |
| `P1-METALS-ENERGY-COST-MODEL-IMPL` | OPEN | BLOCKING per ADR-0023; required for v2 cost model (v1 is zero-cost). |
| `P1-H062-FEATURE-FACTORY-IMPL` | OPEN | BLOCKING; `src/skie_ninja/features/h062/` Donchian + ATR + ID_1 + h_dwell-first-fire module; deferred to next-session execution per the 2026-05-14 scope-constraint disclosure. |
| `P1-H062-WALK-FORWARD-ORCHESTRATOR-IMPL` | OPEN | BLOCKING; `scripts/run_h062_walk_forward.py` analogous to `scripts/run_h060_walk_forward.py` (1086 lines reference); deferred. |
| `P1-H062-PIT-CANARY-INTEGRATION-TEST` | OPEN | BLOCKING; analogous to H053 + H055 PIT canary integration test; intraday channel-N reset at session boundary. |
| `P1-H062-LEVEL-STATE-FOLD-CONTINUITY` | OPEN | BLOCKING unit test; intraday channel-N reset at fold boundary. |
| `P1-H062-POWER-SIMULATION-EXECUTE` | OPEN | BLOCKING; fills §9 power-calibration placeholder. |
| `P1-H062-CALIBRATION-HOLDOUT-RUN` | OPEN | BLOCKING; executes (i) Brier-score competition for ID_1 trend-filter selection on the 2015-2019 (MGC + SIL) + inner-CV bootstrap (ES + NQ) calibration holdout per §5.1, and (ii) MPPM(ρ=1) inner-CV competition for channel-N + k_atr + cadence + Kelly-multiplier per §5.2, and (iii) cumulative-regret competition for switching-bandit-algo per §5.5 (R2 F2-005 fix: clarified per-mechanism selection methodology). |
| `P1-H062-DATA-QUALITY-DEGRADED-DAYS-CANARY` | OPEN | BLOCKING; data-quality canary against the 3 degraded-quality days surfaced by Databento BentoWarning (2017-11-13, 2018-10-21, 2019-01-15) + any others from `get_dataset_condition`. |
| `P1-H062-SUBSTRATE-INGEST-INTO-WORKTREE` | OPEN | BLOCKING for production-walk-forward execution; `data/processed/vendor_legacy_1min_roll_adjusted/` is empty in this worktree (cranky-shtern-3167cc); requires re-run of the Phase O.0 Stage B ingest pipeline via `scripts/ingest.py` against the raw 1-min CSVs at `~/datasets/vendor_skie_ninja_legacy/raw_1min/`. |

### 11.3 Concurrent inheritance preconditions (from ADR-0017 Phase L Thread A)

The following Phase L primitives are landed but the BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH follow-ups remain open:
- `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` — OPEN per Phase L Thread A.
- `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` — OPEN per Phase L Thread A.

H062 production walk-forward dispatch is BLOCKED until both Phase L Thread A residuals land per the ADR-0017 §5 mandatory-inheritance-from-H055-forward convention.

## 12. Sample bias / robustness

- **Survivorship**: ES, NQ, MGC, SIL are all live and continuously-active CME / NYMEX / COMEX contracts. No survivorship bias.
- **Look-ahead**: §7 PIT-causality enforced; canary unit-tested per §11.2.
- **Multiple-testing**: H062 is M=4 family (per-symbol); intra-H062 family-wise correction by Romano-Wolf 2005 stepwise FWER at α=0.05 per H055 §RW2005 precedent. Cross-hypothesis SPA family construction (across H050, H052a, H053, H054, H055, H060, H062) deferred to `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR` per the H055 + H060 precedent.
- **Cross-asset correlation time-variation**: §1.5 caveat; basket effective-breadth ≈ 2.3 not 4.

## 13. Robustness exhibits (informational; not load-bearing per ADR-0013 §1)

- **Sub-basket {ES, NQ}**: equity-pair-only sub-basket. High ES-NQ correlation (~+0.85 to +0.95) compresses diversification gain.
- **Sub-basket {MGC, SIL}**: metals-pair-only sub-basket. Moderate MGC-SIL correlation (~+0.5 to +0.7).
- **Cadence sensitivity**: 1-min vs 5-min vs 15-min comparison (per §5.2 selection).
- **Channel-N sensitivity**: per-N performance comparison across {20, 40, 60, 120, 240, 480} 5-min bars.
- **k_atr sensitivity**: per-k_atr performance comparison across {1.0, 1.5, 2.0, 2.5}.
- **Cost-floor sensitivity exhibit** (v2 only): 1-tick (primary) vs 2-tick (sensitivity).
- **ADR-0019 barbell-sibling exhibit**: pair H062 with an explicit 5-10% long-OTM-put overlay on ES (1-month rolling, 10-delta strike) as tail-hedge; reported as descriptive exhibit only; NOT a formal §1 family entry.
- **Long-only ablation**: H062a hypothetical sibling with shorts disabled; descriptive exhibit (NOT a separate hypothesis at v1).

## 14. Reporting

Per [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) §3.2 (extended to 13 tables under ADR-0019 + 12 mandatory primary-metric tables under ADR-0017 §3.2), the H062 KPI report card MUST include the following structured end-of-simulation summary section between the H1 / hypothesis preamble and the §"Methodological-correctness annotations":

| # | Table | Source |
|---|---|---|
| 1 | P/L (realized OOS, $10K starting capital) | per ADR-0017 §3.2 §1 |
| 2 | Drawdown (realized + projected) | per ADR-0017 §3.2 §2 |
| 3 | Sharpe — primary inference (T = MPPM(ρ=1) per §1; primary CI with excludes-zero column) | per ADR-0013 §3 §3 |
| 3a | Calmar-differential — primary survival inference | per ADR-0017 §3.2 §3a |
| 3b | Profit-factor differential — primary survival inference | per ADR-0017 §3.2 §3b |
| 3c | R-multiple-mean — primary survival inference | per ADR-0017 §3.2 §3c |
| 4 | Annualised Sharpe (with annualisation-factor declaration) | per ADR-0013 §3 §4 |
| 5 | Win/Loss/Zero counts + win rate W/(W+L+Z) | per ADR-0014 §5 |
| 6 | Forward 1-year projection (Median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%)) | per ADR-0013 §3.1 / ADR-0014 §6 |
| 7 | Hansen SPA family p (KPI annotation per ADR-0008 at M=K_max-realized; not load-bearing) | per ADR-0014 §7 |
| 8 | Other KPIs (best Kelly-multiplier-mode per fold, best channel-N per fold, best k_atr per fold, switching-bandit-algo, BOCD decay-flag, L-skewness, causal-mechanism annotation) | per ADR-0014 §8 |
| 9 | Methodological-correctness annotations | per ADR-0014 §9 |

Plus Table 1c (per ADR-0019): **Payoff-shape diagnostics** — L-skewness τ_3 + 95% CI; payoff-shape annotation `skew-{positive,zero,negative}`; barbell-rebalance-candidate flag (boolean per ADR-0019 §3).

Plus mandatory **bottom-line prose paragraph** (≤ 8 sentences) stating the primary inferential verdict on basket MPPM(ρ=1) + realised + projected $10K equity outcome + next mandatory stage transition + cross-link to full report card body.

Template at [research/_templates/kpi_results_summary_template.md](../../../research/_templates/kpi_results_summary_template.md).

## 15. NinjaScript implementation (mandatory per ADR-0013 §5)

H062 is **pure-C# implementable** (no Python inference at decision time):
- Donchian channel computation is `max(close[1..N])` / `min(close[1..N])` — closed-form on rolling buffer.
- ATR computation is Wilder-smoothing recursion — closed-form single-state recursion.
- ID_1 trend-filter is closed-form per the §5.1 selected family (TSMOM / ADX / OLS-slope / MA-crossover all pure-C#).
- Position-size rule is the §5.3 formula clipped to ADR-0001 capacity ceilings — deterministic.
- BOCD decay-monitor is a closed-form posterior-update recursion per [Adams-MacKay 2007 §2 arXiv:0710.3742](https://arxiv.org/abs/0710.3742) — pure-C# implementable.
- Switching-bandit allocation redirect is a deterministic algorithm per the §5.5 selected family (D-UCB / GLR-klUCB both pure-C#).

- **C# class**: `H062_DonchianChannelBreakout` at `ninjascript/strategies/H062_DonchianChannelBreakout.cs`.
- **Python-prototype hyperparameter mapping**: `cadence`, `channel_N`, `k_atr`, `ID_1` (enum selector), `H_dwell`, `kelly_multiplier`, `bocd_hazard_rate`, `bocd_window`, `switching_bandit_algo` (enum selector) each map 1:1 to NinjaScript `[NinjaScriptProperty]` parameters.
- **Entry/exit logic**: 1:1 with the Python signal generation (§3 + §4); v1 zero-cost — costs wired via [config/instruments.yaml](../../../config/instruments.yaml) per-instrument tick-size + multiplier for v2.
- **Kill-switch parameters**: K-1..K-8 per §11.1 enforced at the strategy layer per ADR-0017 §5 mandatory K-1..K-8 inheritance.
- **Fill-log schema**: matches plan §6.1 fill-log schema.
- **Sim101 smoke-test record**: required post-implementation; ScriptSubmission timestamps + position fills + final P/L logged.
- **Python ↔ NinjaScript parity-check**: byte-equality on the integer signal vector per ADR-0013 §5.2; per-strategy calibration via `P1-H062-NINJASCRIPT-PARITY-TOLERANCE`.

## 16. Pre-registration freeze metadata

- **Substrate dataset_checksum (BINDING)**:
  - `output_frame_sha256 = 1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260512.json). Subset of 38-partition combined frame restricted to H062 v1 universe (33 partitions across ES + NQ + MGC + SIL); H062-universe-subset SHA pinned in [data_requirements.md](data_requirements.md) addendum at first running run.
- **Scientific payload SHA256**: computed at first orchestrator run; recorded in the per-run sidecar at `runs/h062/<run_id>/sidecar.json`.
- **Reproducibility log path**: `logs/reproducibility/<run_id>.json` (project standing convention). Schema = [ADR-0009](../../../docs/decisions/ADR-0009-blas-thread-pinning.md) 13-field schema; `ReproLog` frozen dataclass at [src/skie_ninja/utils/reproducibility.py](../../../src/skie_ninja/utils/reproducibility.py) is the implementation-of-record (R2-008 fix: cross-link added).
- **Git HEAD at pre-registration freeze**: recorded in §17 revision-log entry below.
- **RNG seed**: `20260514` (date-anchored; consistent with project convention).

## 17. Revision log

- **2026-05-14 — initial pre-registration draft; status `designed`.**
  - Author: skoir (independent researcher).
  - Inheritance: [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) retail-tier capacity ceiling, [ADR-0006](../../../docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) project-scope extension, [ADR-0007](../../../docs/decisions/ADR-0007-stacked-embargo-convention.md) stacked-embargo convention, [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-and-m1-degenerate.md) SPA M=1 degenerate handling, [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) permanent-exploration / no-binding-gates / mandatory-NinjaScript-terminus / non-loss preservation, [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) canonical KPI results-summary tables, [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained primary metric vector + drawdown-constrained Kelly + K-1..K-8 kill switches + FM-1..FM-5 stress-test suite, [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) fitness + Kelly-multiplier grid + BOCD signal-decay monitor + switching-bandit, [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness annotation + barbell-rebalance-candidate flag, [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism vs correlation-only annotation, [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate extension.
  - Causal-mechanism claim type (§1.3): `hybrid` (channel-break-as-information-event upstream causal per Hong-Stein 1999 underreaction model; channel-N + k_atr + Kelly-multiplier layers correlation-only refinement); E-value anchor computed at first KPI emission per ADR-0022.
  - Substrate verification: actual provenance `output_frame_sha256 = 1247dc7e...` (NOT CLAUDE.md ledger's claimed `242aaa28...`; reconciliation tracked under `P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE`).
  - Pre-launch BLOCKING preconditions: 22 follow-ups listed in §11.2 (9 closed; 13 open).
  - Frozen §1-§7 immutability per ADR-0013 §"Frozen pre-registration amendment".
  - Audit-remediate-loop discipline: pre-registration draft pending Round-1 isolated quant-auditor + literature-check + R2 parallel quant-auditor + reproducibility-verifier per the H055 + H060 staging pattern. Audit trail at [docs/audits/audit_trail_2026-05-14_h062_intraday_donchian_design.md](../../../docs/audits/audit_trail_2026-05-14_h062_intraday_donchian_design.md).
