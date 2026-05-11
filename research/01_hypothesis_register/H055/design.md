---
hypothesis_id: H055
schema_version: hypothesis_design_v1
status: designed  # 3-round audit-remediate-loop ACCEPT 2026-05-06
tier: 2b
created: 2026-05-06
created_by: skoir
description: Pre-registered design doc for hypothesis H055 — mechanized wick-rejection scalping with deterministic trend gate (HMM-deferred)
---

# H055 — Mechanized wick-rejection scalp on CME equity-index futures (ES/NQ + micros)

> **Mechanized successor of a discretionary v1 baseline.** H055 v2 mechanizes the three discretionary degrees of freedom in the operator's discretionary v1 wick-rejection scalp (directional discretion, setup-quality discretion, position-size discretion) into four deterministic components: (1) a non-ML trend-strength gate, (2) a closed-form body-overlap consolidation score, (3) a level-exhaustion state machine, (4) ATR-scaled TP/SL with fractional-Kelly sizing.
>
> **The motivation is empirical.** The 2026-05-01 → 2026-05-06 NinjaTrader pilot ledger ([data/external/h055_pilot_ledger/Performance.csv](../../../data/external/h055_pilot_ledger/Performance.csv); 171 trades, 74.85% win rate, $36.01 expectancy) shows the operator's discretionary side-skew is symbol-conditional and day-conditional in a pattern Component 1's deterministic gate must reproduce. The pilot window is **out-of-sample relative to the H055 v1 OOS test fold** (which ends 2025-12-{03,19}); the pilot is descriptive only, not an inferential window.
>
> **HMM is OUT OF SCOPE for v1.** Component 1 uses deterministic identifiers only (TSMOM sign, ADX, log-price slope t, MA-crossover). HMM regime-conditioning is a v3 successor under follow-up `P1-H055-V2-WITH-HMM-REGIME-GATE`.

## 1. Hypothesis

- **H_0**: The net (post-cost, post-slippage) annualized log-return Sharpe of v2, evaluated by purged walk-forward CV per §6, does NOT strictly dominate the corresponding Sharpe of (a) buy-and-hold of the front-month roll-adjusted continuous contract, (b) a TSMOM benchmark per [Moskowitz, Ooi, Pedersen 2012, *JFE* 104(2):228-250](https://doi.org/10.1016/j.jfineco.2011.11.003), and (c) a no-skill random-entry bootstrap matched on side mix and holding-period distribution, on a per-instrument-class basis ({ES, MES} pooled and {NQ, MNQ} pooled per ADR-0001 micros mapping).
- **H_1**: v2 strictly dominates each of the three inferential benchmarks on net Sharpe per instrument-class: each pairwise Sharpe-differential 95% CI under [Ledoit & Wolf 2008, *J Empirical Finance* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap (block length per [Politis & White 2004, *Econometric Reviews* 23(1):53-70](https://doi.org/10.1081/ETC-120028836) with [Patton, Politis & White 2009, *Econometric Reviews* 28(4):372-375](https://doi.org/10.1080/07474930802459016) correction) lies strictly above zero. The [Hansen 2005, *JBES* 23(4):365-380](https://doi.org/10.1198/073500105000000063) SPA p-value is reported as a KPI annotation per ADR-0013 §2; given the TPE-conditioning of the candidate set, the reported p does not provide grid-wide superior-predictive-ability guarantees and is interpreted under the [Bergstra et al. 2011](https://papers.nips.cc/paper/4443-algorithms-for-hyper-parameter-optimization) TPE coverage assumption.
- **SPA reporting caveat**: SPA p reported is conditional on the realized TPE exploration trajectory and the Type-I rate is not guaranteed at nominal α; the load-bearing inferential criterion is the LW2008 strict CI dominance against the three benchmarks (B&H, TSMOM, no-skill bootstrap). Conjunctive multi-strategy correction across the 4 instrument-class siblings via [Romano & Wolf 2005, *Econometrica* 73(4):1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER control + [Harvey, Liu & Zhu 2016, *RFS* 29(1):5-68](https://doi.org/10.1093/rfs/hhv059) multiple-testing-aware deflation is tracked under follow-up `P1-H055-RW2005-STEPWISE-CONJUNCTIVE` (deferred from this immediate landing scope; v1 retains the BH-FDR adjustment per §1 SPA family entry).
- **Mechanism**: the discretionary v1 scalp produces positive expectancy on a 6-session pilot but cannot be inferentially evaluated (n=171, single window, no walk-forward analogue). v2 mechanizes the three discretionary degrees of freedom enumerated in the preamble. Each mechanization is anchored to a peer-reviewed primary source where one exists (TSMOM trend gate per [Moskowitz, Ooi, Pedersen 2012](https://doi.org/10.1016/j.jfineco.2011.11.003); HAC-OLS slope per [Newey & West 1994, *RES* 61(4):631-653](https://doi.org/10.2307/2297912) / [Andrews 1991, *Econometrica* 59(3):817-858](https://doi.org/10.2307/2938229) for L≥60 and [Kiefer & Vogelsang 2002, *Econometrica* 70(5):2093-2095](https://doi.org/10.1111/1468-0262.00366) fixed-b for L<60; realized-volatility regime characterization per [Andersen, Bollerslev, Diebold, Labys 2003, *Econometrica* 71(2):579-625](https://doi.org/10.1111/1468-0262.00418); fractional-Kelly clamping per [MacLean, Thorp, Ziemba 2010 *Kelly Capital Growth*, World Scientific (DOI 10.1142/7598)](https://doi.org/10.1142/7598)) and to a flagged practitioner source where one does not (Wilder 1978 ADX/ATR; Connors-Raschke 1995 NR7; Bollinger 2001 squeeze; Nison 1991 candlestick wick conventions; *practitioner*).
- **Primary citations** (frozen at pre-reg; Phase 0 lit-check status per §15.1):
  - TSMOM trend sign: [Moskowitz, Ooi, Pedersen 2012, *JFE* 104(2):228-250](https://doi.org/10.1016/j.jfineco.2011.11.003).
  - HAC-OLS slope (L≥60): [Newey & West 1994, *RES* 61(4):631-653](https://doi.org/10.2307/2297912); [Andrews 1991, *Econometrica* 59(3):817-858](https://doi.org/10.2307/2938229).
  - HAC-OLS slope (L<60): [Kiefer & Vogelsang 2002, *Econometrica* 70(5):2093-2095](https://doi.org/10.1111/1468-0262.00366) fixed-b.
  - Realized-volatility regime: [Andersen, Bollerslev, Diebold, Labys 2003, *Econometrica* 71(2):579-625](https://doi.org/10.1111/1468-0262.00418); [Andersen & Bollerslev 1998, *IER* 39(4):885-905](https://doi.org/10.2307/2527343).
  - Level memory (formal cousin to Component 3): [Bouchaud, Gefen, Potters, Wyart 2004, *Quantitative Finance* 4(2):176-190](https://doi.org/10.1080/14697680400000022).
  - Fractional-Kelly: [MacLean, Thorp, Ziemba 2010, *Kelly Capital Growth*, World Scientific Ch. 1+6 (DOI 10.1142/7598)](https://doi.org/10.1142/7598).
  - Sharpe inference: [Lo 2002, *FAJ* 58(4):36-52](https://doi.org/10.2469/faj.v58.n4.2453); [Opdyke 2007, *J Asset Management* 8(5):308-336](https://doi.org/10.1057/palgrave.jam.2250084); [Ledoit & Wolf 2008, *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002).
  - Block-length: [Politis & White 2004, *ER* 23(1):53-70](https://doi.org/10.1081/ETC-120028836); [Patton, Politis & White 2009, *ER* 28(4):372-375](https://doi.org/10.1080/07474930802459016); [Politis & Romano 1994, *JASA* 89(428):1303-1313](https://doi.org/10.1080/01621459.1994.10476870).
  - Multiple-testing: [Hansen 2005, *JBES* 23(4):365-380](https://doi.org/10.1198/073500105000000063); [Hsu, Hsu & Kuan 2010, *JEF* 17(3):471-484](https://doi.org/10.1016/j.jempfin.2010.01.001) (finite-K SPA bound); [White 2000, *Econometrica* 68(5):1097-1126](https://doi.org/10.1111/1468-0262.00152) (Reality Check; corroborating); [Romano & Wolf 2005, *Econometrica* 73(4):1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x); [Harvey, Liu & Zhu 2016, *RFS* 29(1):5-68](https://doi.org/10.1093/rfs/hhv059); [Harvey & Liu 2015, *JPM* 42(1):13-28](https://doi.org/10.3905/jpm.2015.42.1.013).
  - Walk-forward protocol: [Tashman 2000, *Int J Forecasting* 16(4):437-450](https://doi.org/10.1016/S0169-2070(00)00065-0); López de Prado 2018 *AFML* Wiley ISBN 978-1119482086 Ch.7 (*practitioner*).
  - News-time exclusion (FOMC drift): [Lucca & Moench 2015, *J Finance* 70(1):329-371](https://doi.org/10.1111/jofi.12196).
  - Capacity bound: [Loeb 1983, *FAJ* 39(3):39-44](https://doi.org/10.2469/faj.v39.n3.39) (*practitioner*).
  - Practitioner: Wilder 1978 *New Concepts in Technical Trading Systems* (ADX/ATR); Connors & Raschke 1995 *Street Smarts* (NR7); [Bollinger 2001 *Bollinger on Bollinger Bands*, McGraw-Hill, ISBN 978-0071373685](https://www.mhprofessional.com/) (squeeze); Nison 1991 *Japanese Candlestick Charting Techniques* (wick/body); all *practitioner*.
  - Empirical motivation (load-bearing; descriptive): pilot ledger [data/external/h055_pilot_ledger/Performance.csv](../../../data/external/h055_pilot_ledger/Performance.csv) covering 2026-05-01 → 2026-05-06.
- **Test statistic**: per instrument-class i ∈ {ES+MES, NQ+MNQ}, the family `T_H055_i = {SR_v2_i − SR_BH_i, SR_v2_i − SR_TSMOM_i, SR_v2_i − SR_RND_i}` evaluated under LW2008 studentized stationary-bootstrap CI. Conjunctive dominance criterion is STRICT: lower-bound of v2 differential CI > upper-bound of benchmark differential CI on each pairwise comparison.  <!-- justify: STRICT dominance per F1 + Round-2 audit; weak dominance (CI excludes zero on positive side) is insufficient under LW2008 §3 because the studentized SB-variant produces a one-sided rejection region whose upper-CI tail is the only inferentially load-bearing quantity; LW2008 §3 + Romano-Wolf 2005 §3 -->
- **SPA family entry**: H055 is **FOUR sibling hypotheses** indexed by instrument-class {ES, MES, NQ, MNQ}, not one pooled hypothesis.  <!-- justify: per-instrument-class trend-gate parameter freedom (§5) means {ES, MES} and {NQ, MNQ} have independent trend-gate fits and the pairwise SR differentials are not exchangeable across classes; family-wise control across the four classes is via Benjamini-Hochberg FDR per Hansen 2005 §2 + the BH-FDR cross-instrument convention used in H050 multi-symbol --> Family-wise BH-FDR is applied across the four instrument-class hypotheses at α=0.05. The four-element BH adjustment is reported alongside per-class LW2008 + per-class Hansen SPA. Cross-hypothesis (cross-design.md) SPA family construction with the rest of the project's hypotheses (H050, H052a, H053, H054) is deferred to project-level ADR per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR` (heterogeneous OOS windows preclude shared bootstrap-index sample length per Hansen 2005 §2).
- **Decision rule cross-link**: see §10 below.

## 2. Universe and sample period

- **Instruments at v1**: ES (primary), NQ (primary), MES (micro of ES; linear price-rescaled per ADR-0001), MNQ (micro of NQ; linear price-rescaled per ADR-0001).  <!-- justify: substrate at data/processed/vendor_legacy_1min_roll_adjusted/ contains ES + NQ bars only; MES/MNQ are deterministic linear rescalings per ADR-0001 capacity ceiling; CL/MCL/MYM/MGC excluded at v1 because the substrate does not contain bars for those instruments -->
- **Energy and metals deferred**: CL, MCL, MGC, MYM are EXCLUDED at v1 and tracked under follow-up `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND`. The pilot ledger's regime-asymmetry signal (manual ledger 2026-05-06 shows 100% short on CL) becomes a phase-2 falsifier once those bars are ingested. Without them, the cross-asset regime-asymmetry validation cannot be performed at v1.
- **Frequency**: 1-minute bars on the lower TF (T_L); higher TF (T_H) bars derived deterministically by aggregation (15m / 30m / 60m / 240m). Both RTH and ETH bars are admissible at the feature-construction layer; the eligible-bar set (§4) restricts entries to RTH per the operator's discretionary-v1 baseline.
- **Session**: CME Globex (ETH 23-hour electronic + RTH 09:30-16:00 ET), holiday-adjusted per [config/instruments.yaml](../../../config/instruments.yaml) and [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py). RTH-only is the primary entry filter; ETH-only is reported as sensitivity exhibit per §14.
- **Sample window** (BINDING; pre-reg-frozen):
  - **Calibration holdout**: 2015-01-01 → 2019-12-31 (5 years).  <!-- justify: Calibration holdout is disjoint from the *test folds* of H050/H052a/H053/H054 (the load-bearing property for hyperparameter pre-registration per López de Prado 2018 *AFML* §11). H050 train and H053 IS span 2015-2022 — disjoint-from-test-fold property is what protects ID_1 selection from circular validation; the calibration holdout is NOT disjoint from prior IS windows but is disjoint from prior OOS test folds. Identical-in-substance to data_requirements.md §"Cross-hypothesis fit-set isolation properties" load-bearing isolation property 1. -->
  - **IS** (Optuna trial-budget K_max search; trend-gate per-instrument-class fit; label-cfg search): 2020-01-01 → 2023-12-31 (4 years; matches H050 train + H054 IS+val combined window).
  - **OOS test**: 2024-01-01 → 2025-12-03 (ES + MES) and 2024-01-01 → 2025-12-19 (NQ + MNQ).  <!-- justify: matches the substrate right-edge per the post-Cell-I substrate envelope; ES substrate ends 2025-12-03, NQ extends to 2025-12-19; per-class right-edge per the substrate's per-symbol coverage --> The ES OOS spans 244 + 230 = 474 RTH sessions (approximate); the NQ OOS spans 244 + 245 = 489 RTH sessions (approximate). Per-symbol session count is logged at run time.
  - **Pilot window 2026-05-01 → 2026-05-06**: OUT-OF-SAMPLE relative to the OOS test fold; descriptive only; reported as adherence-audit input per §14, not as inferential evidence.
- **Roll treatment**: roll-adjusted front-month continuous series via [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) (ratio adjustment, rolled on volume-crossover per [config/instruments.yaml](../../../config/instruments.yaml) `roll_rule`; deterministic continuous front-month per Cycle-1 deliverable v0.3.0 with `contract_id_full` disambiguation; 2026-04-26).
- **Dataset snapshot frozen at pre-registration**: SHA256 of the roll-adjusted parquet `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` per the H050/H052a/H053/H054 binding; snapshot is immutable across re-runs of this hypothesis ID; persisted to `ReproLog.dataset_checksums` under key `vendor_legacy_1min_roll_adjusted`.

## 3. Features

All features are computed at bar close on T_L or T_H using only data available at time t (PIT-causal). Feature panels are joined on `session_date_et` per the H053 dtype-precision contract (`pl.Datetime("ns", "UTC")` uniform across blocks; per `P1-FEATURE-PANEL-PRECISION-CONTRACT`).

- **Component 1 — trend-strength gate (deterministic; HMM-deferred)**. State `s_t ∈ {up, neutral, down}` on T_H; longs fire only on `s_t ∈ {up, neutral}`, shorts on `s_t ∈ {down, neutral}`. The trend-identifier `ID_1 ∈ {a, b, c, d}` is per-instrument-class (one for {ES, MES}, one for {NQ, MNQ}) and selected per §5 via supervised competition on the calibration holdout:
  - (a) **TSMOM sign** per [Moskowitz, Ooi, Pedersen 2012](https://doi.org/10.1016/j.jfineco.2011.11.003): `M_t(L) = sign(Σ_{i=1..L} r_{t−i})`; `s_t = up` if `M_t = +1` and `|Σr| > τ_M·σ_t·√L`.
  - (b) **ADX threshold** (Wilder 1978; *practitioner*): `s_t = sign(+DI − −DI)` if `ADX_t > τ_ADX`, else neutral.
  - (c) **HAC-OLS slope t-statistic**: regress `log(P_{t−L+1..t})` on time index; `t = β̂/SE(β̂)`; HAC SE per Newey-West 1994 / Andrews 1991 bandwidth for L≥60 and per Kiefer-Vogelsang 2002 fixed-b for L<60; `s_t = up` if `t > τ_t`, neutral if `|t| ≤ τ_t`, down if `t < −τ_t`.
  - (d) **MA-crossover sign**: `s_t = sign(MA_short − MA_long)`; neutral if `|MA_short − MA_long| / σ_t < τ_MA`.
- **Component 2 — body-overlap consolidation indicator** (per-instrument-class shared parameters per §5 robustness). For higher-TF bars `i ∈ {1, …, N}` on T_H, body interval `B_i = [min(O_i, C_i), max(O_i, C_i)]`. Pre-registered primary score is `ρ_1` (mean pairwise Jaccard); sensitivity score is `ρ_2` (common intersection); `ρ_3` is dropped per round-3 audit residual.  <!-- justify: ρ_1 is the primary indicator because (i) the median-anchored ρ_3 introduces a researcher degree of freedom on tie-break with no published canonical resolution, and (ii) ρ_2 collapses to 0 on a single disjoint bar (a fragility documented at calibration); ρ_2 is reported for sensitivity but is NOT entered into the SPA family per F1-005 + C2-6 -->
  - `ρ_1 = (1 / C(N,2)) · Σ_{i<j} |B_i ∩ B_j| / |B_i ∪ B_j|` — primary, mean pairwise Jaccard.
  - `ρ_2 = |∩_{i=1..N} B_i| / |∪_{i=1..N} B_i|` — sensitivity-only, common intersection.
  - The trigger threshold `ρ*` is calibrated against the empirical CDF of `ρ_1` on the §2 calibration holdout (2015-2019); see §5.
  - Closest formal cousin: realized-vol regime characterization per Andersen-Bollerslev-Diebold-Labys 2003. Practitioner ancestors: NR7 (Connors-Raschke 1995; *practitioner*); Bollinger squeeze (Bollinger 2001; *practitioner*).
- **Component 3 — level-exhaustion counter**. State machine on each swing-pivot level L:
  - **Touch** at t: `|P_t − L| ≤ δ · ATR_n`.
  - **Rejection** within k bars of touch: close beyond L on the same side as the prior tape AND price reverts by `≥ γ · ATR_n`. `R(L) += 1`.
  - **Penetration** within k bars: close through L. `R(L) → ∞`.
  - Entry permitted while `R(L) ≤ R*`. State machine RESETS at each fold boundary (per the round-1 audit fix) to eliminate forward-looking contamination; alternative snapshot policy (carry only the snapshot state at the embargo's right edge) is exercised under the §14 robustness exhibit. Practitioner heuristic ("third test breaks"); formal cousin: limit-order-book level memory per [Bouchaud-Gefen-Potters-Wyart 2004](https://doi.org/10.1080/14697680400000022).
- **Component 4 (sizing inputs) — ATR and realized variance**. ATR_n on T_L via Wilder smoothing over n bars (Wilder 1978; *practitioner*). Realized variance on the IS fold with HAC adjustment per Newey-West 1994 (used in §5 Kelly variance estimator).
- **Wick-rejection setup detector** (preserved verbatim from operator's discretionary v1):
  - **Long swing pivot**: 3 consecutive lower lows then 2 subsequent higher lows (the second pair need not be consecutive). Entry at the wick of the swing-low bar.
  - **Short swing pivot**: symmetric — 3 consecutive higher highs then 2 lower highs. Entry at the upper wick.
  - **Wick-reversal (non-swing)**: bar whose wick punctures the most recent swing high/low without the close breaking through; gated by `θ_wick = wick / body ≥ θ_wick_min` per §5 search domain.

## 4. Label construction

Per-trade P/L on a wick-rejection mean-reversion scalp on T_L. Labels are constructed at trade close (TP, SL, or time stop), not at session close.

- **Entry**: limit order posted at the wick extreme of the trigger bar, conditional on (i) Component 1 admits the side, (ii) Component 2 `ρ_1 > ρ*` within `H_dwell` bars on T_H preceding the trigger, (iii) Component 3 `R(L) ≤ R*` at fill time, (iv) the trigger bar passes the eligible-bar filter (below).
- **Profit target**: `TP = entry ± α · ATR_n`.
- **Stop**: `SL = entry ∓ β · ATR_n`.
- **Time stop**: `k_swing` bars on T_L after fill, parameter-grid-searched per §5.
- **Hard close**: 15:55 ET (RTH-mode) or session-end (ETH-mode sensitivity).
- **Settlement**: 1-min bar close at exit time.
- **pt_sl** both active; **vertical_barrier** = time stop or hard close, whichever first.
- **Capacity**: per ADR-0001 ≤ 20 ES / ≤ 40 NQ / ≤ 200 MES / ≤ 400 MNQ contracts per signal regardless of Kelly output (§5 hard cap; documented as Kelly clamp).  <!-- justify: ADR-0001 capacity ceiling is binding for retail-tier strategies regardless of theoretical Kelly fraction; cap is applied AFTER the f̂ clamp of §5 and before order placement -->

**Eligible-bar set** (binding pre-reg):
- (i) **Feature availability**: all T_L and T_H lookback bars present and non-NaN at bar close.
- (ii) **RTH session-time filter**: timestamp ∈ 09:30:00 → 15:55:00 ET inclusive (RTH primary; ETH-only sensitivity per §14).
- (iii) **News calendar exclusion**:
  - **FOMC release** ±15 min around the scheduled press-release time.  <!-- justify: Lucca-Moench 2015 RFS pre-FOMC drift is the canonical literature finding establishing systematic pre-announcement abnormal returns; ±15 min envelope brackets the 2-hour pre-FOMC drift window's fastest-moving end and the post-statement adjustment phase per Lucca-Moench 2015 §III; news source = FRED release_id for FOMC -->
  - **NFP release** ±5 min.  <!-- justify: BLS NFP release at 08:30 ET; ±5 min envelope brackets the Treasury-futures spike documented in standard event-study literature; conservative pre-reg envelope; news source = BLS public release-time calendar -->
  - **CPI release** ±5 min.  <!-- justify: BLS CPI release at 08:30 ET; same envelope-rationale as NFP; news source = BLS public release-time calendar -->
  - News-calendar implementation: FOMC release_id pulled from FRED `release_id` API; NFP and CPI release-times pulled from BLS public release-time calendar; pre-loaded into [src/skie_ninja/utils/news_calendar.py](../../../src/skie_ninja/utils/news_calendar.py) (to be authored as §11.2 prereq under follow-up `P1-H055-NEWS-CALENDAR-INGEST`).

## 5. Estimator

### 5.1 Trend-identifier selection methodology (Component 1; per-instrument-class)

Per-instrument-class supervised competition on the §2 calibration holdout (2015-2019; disjoint from IS and OOS):
- For each candidate `ID_1 ∈ {a, b, c, d}` and instrument-class `c ∈ {ES+MES, NQ+MNQ}`, fit the trend-gate parameters `{L, τ_M, τ_t, τ_MA, τ_ADX}` on a held-out fragment of the calibration holdout (2015-2018; 4 years), then evaluate the side-skew Brier score on the remaining calibration fragment (2019; 1 year) per:
  - `BS_c(ID_1) = mean over eligible bars of (ŷ_side_t − y_side_t)²`, where `ŷ_side_t ∈ {+1, 0, −1}` is the gate's predicted side and `y_side_t ∈ {+1, −1}` is the realized sign of the next-`k_swing`-bar log-return on T_L.
- Select `ID_1*_c = arg min_{ID_1} BS_c(ID_1)` per instrument-class.  <!-- justify: option (b) per the locked decision; supervised on side-skew Brier score on a held-out fragment of the calibration holdout (NOT the OOS, NOT the v2 walk-forward IS) so ID_1 selection cannot leak into the H_1 inferential family; Brier score is the canonical proper-scoring-rule for binary-with-abstain prediction per Niculescu-Mizil & Caruana 2005 -->
- Components 2-4 (overlap, exhaustion, ATR/Kelly) are SHARED across instrument-classes at primary; per-instrument-class robustness exhibit reported per §14.  <!-- justify: per-instrument-class trend gate captures the directional asymmetry the operator's discretionary v1 manual ledger shows is symbol-conditional (CL/MCL short-skewed; NQ/MNQ long-skewed) without quadrupling the parameter freedom of overlap/exhaustion/sizing, which exhibit cross-instrument-class invariance in primary literature (NR7, Bollinger, Wilder ATR all symbol-agnostic) -->

### 5.2 Body-overlap ρ calibration (Component 2)

The trigger threshold `ρ*` is calibrated against the empirical CDF of `ρ_1` on the §2 calibration holdout. For each candidate quantile `q ∈ {0.50, 0.60, 0.70, 0.80, 0.90}`:
- Compute `ρ*_q = empirical_quantile(ρ_1, q)` on the calibration holdout.
- Score by the conditional Brier of "next-`H_dwell`-bar wick-reversal trigger fires" given `ρ_1 ≥ ρ*_q`.

The selected quantile is the minimum-Brier `q*`; `ρ* = ρ*_{q*}`. `ρ_1` is the primary scoring quantity; `ρ_2` is reported for sensitivity only and is NOT entered into the SPA family.

### 5.3 Level-exhaustion state machine (Component 3)

State machine per §3; reset at each fold boundary (primary policy; alternative snapshot policy per §14 sensitivity). Embargo formula with explicit minute units:
```
embargo_minutes >= k_swing × minutes_per_T_H_bar + max_holding_period × minutes_per_T_L_bar
embargo_sessions = ceil(embargo_minutes / minutes_per_session)
```
where `minutes_per_session = 1380` for CME ETH (23-hour electronic) or `405` for RTH-only; logged at run time. Unit-test BLOCKING precondition per §11.2.

### 5.4 Kelly sizing (Component 4)

```
qty = floor( (f̂ · equity) / (β · ATR_n · point_value) )
f̂ = clamp(f_Kelly · shrinkage, 0, f_max)
shrinkage = max(0, CI_lower) / max(ε, CI_upper)
ε = sqrt(machine_epsilon_float64) ≈ 1.49e-8
```
- Variance estimator = realized variance on the IS fold with HAC adjustment per Newey-West 1994.  <!-- justify: per locked decision; full IS fold with NW1994 HAC bandwidth so the variance estimate is consistent under the project's standing HAC convention; data-dependent bandwidth per NW1994 §4 with serial-correlation adjustment for the trade-return series -->
- `CI_lower`, `CI_upper`: bounds of the bootstrap CI on the per-fold estimated edge (per-trade Sharpe × √trades_per_year), computed via stationary bootstrap with PW2004+PPW2009 block length.
- When `CI_lower < 0`: `shrinkage = 0` → `f̂ = 0` → no position taken on that fold (trading suppressed).
- `f_max = 0.5` (half-Kelly upper bound per MacLean-Thorp-Ziemba 2010 ruin-controlled regime).
- `ε = sqrt(machine_epsilon_float64)` per IEEE-754 double-precision convention.
- After Kelly clamp, apply ADR-0001 hard cap (§4 capacity) which OVERRIDES `qty` if `qty > {20 ES, 40 NQ, 200 MES, 400 MNQ}`. Documented as Kelly clamp.
- Ruin-probability simulation under `f̂` with stationary-bootstrap-resampled returns logged per fold.
- Citations: MacLean-Thorp-Ziemba 2010 (DOI 10.1142/7598) Ch.1 + Ch.6; [Kan & Zhou 2007, *JFQA* 42(3):621-656](https://doi.org/10.1017/S0022109000004129) cited as Bayesian credibility-weighted alternative (NOT adopted at primary; recorded as alternative for ablation).

### 5.5 Long/short parameter asymmetry

Independent fit per side at primary; Stein shrinkage as sensitivity exhibit per §14.  <!-- justify: the operator's discretionary v1 ledger shows directionally-asymmetric win rate (longs 72.34% vs shorts 77.92%) and symbol-conditional side-skew; independent fit per side preserves the asymmetry the mechanical strategy must reproduce; Stein shrinkage at sensitivity is the standard "is the apparent asymmetry stable enough to fit independently" guard per James-Stein 1961 -->

### 5.6 Hyperparameter search (TPE; Optuna)

All free parameters selected by Bayesian optimization (Optuna TPE) inside the walk-forward outer loop. Trial-budget per fold capped at K_max = 500 (pre-registered per §9). Search domains and `# justify:` annotations:

| Symbol | Description | Search domain | # justify: |
|---|---|---|---|
| T_H | higher TF for trend gate and ρ | {15m, 30m, 60m, 240m} | discrete TFs available from CME data feed; spans intraday-to-session |
| T_L | lower TF for entries | {1m, 5m, 15m} | matches v1 trade-execution practice on NinjaTrader |
| ID_1 | trend identifier id (per instrument-class; selected on calibration holdout per §5.1, NOT TPE-searched) | {a, b, c, d} | calibration-holdout selection per §5.1; not free-parameter |
| L | trend-gate lookback (bars on T_H) | {20, 40, 60, 120, 240} | brackets MOP 2012 1-12 month range scaled to intraday bar counts |
| τ_M, τ_t, τ_MA | trend magnitude thresholds | continuous; prior on σ-units (0, 3] | one-sided hypothesis-test scale |
| τ_ADX | ADX threshold | [10, 50] | Wilder 1978 (*practitioner*) range |
| N | overlap window length on T_H | {5, 7, 10, 14, 20} | brackets NR7 (Connors-Raschke 1995; *practitioner*) and Bollinger 20-bar window (Bollinger 2001; *practitioner*) |
| ρ* | overlap trigger | calibrated from §5.2 holdout CDF; q ∈ {0.50, 0.60, 0.70, 0.80, 0.90} | calibration-holdout selection; not free-parameter |
| H_dwell | bars on T_H during which ρ-trigger remains active | {1, 2, 3, 5} | bounded above by typical overlap-cluster persistence on equity-index futures |
| k_swing | bars allowed between pivot leg and confirmation | {3, 5, 8, 13} | Fibonacci-spaced practitioner bar counts; spans 3-13 to match v1 confirmation-latency lower bound |
| θ_wick | minimum wick-to-body ratio | [1.0, 4.0] | lower bound = "wick at least equals body" (Nison 1991; *practitioner*); upper bound from empirical 99th percentile |
| n | ATR lookback on T_L | {7, 14, 21} | Wilder 1978 (*practitioner*) default 14 plus ±1 doubling |
| α | TP multiple of ATR | [0.5, 4.0] | brackets reward-risk 0.5-4 across published intraday studies |
| β | SL multiple of ATR | [0.5, 3.0] | survivability lower bound + practitioner upper bound |
| δ | touch tolerance, ATR units | [0.05, 0.5] | tick-size-aware lower bound; upper bound from typical equity-index noise band |
| γ | rejection reversion, ATR units | [0.1, 1.0] | half-ATR is the canonical "meaningful move" cut |
| k | exhaustion-counter bar window | {3, 5, 8, 13} | matches k_swing rationale |
| R* | exhaustion threshold | {1, 2, 3, 4} | "third test breaks" = R* ∈ {2, 3} central practitioner case; ablation either side |
| f_Kelly | Kelly-fraction nominal | (0, 0.5] | half-Kelly upper bound from MacLean-Thorp-Ziemba 2010 ruin-controlled regime |

TPE bookkeeping per [Bergstra et al. 2011, *NeurIPS 24*](https://papers.nips.cc/paper/4443-algorithms-for-hyper-parameter-optimization). All Optuna study state + per-trial OOS-Sharpe trajectory logged for SPA family entry per §8.b.

## 6. Splitter

- **Outer split**: purged walk-forward over 2020-01-01 → 2025-12-{03,19} per §2.  <!-- justify: walk-forward is the canonical project splitter per CLAUDE.md "Walk-forward only" standing constraint; CPCV remains the canonical cross-validation methodology for any disposition that produces a Sharpe KPI per ADR-0012/ADR-0013 §7 but H055 v1 uses single-path walk-forward to match the H050/H052a/H054 single-outer-fold convention -->
- **Walk-forward roll cadence**: monthly OOS roll.  <!-- justify: monthly cadence is the locked decision; matches the trades/year-cadence implied by the v1 pilot (171 trades / 6 sessions ≈ 28.5 trades/session) which produces well-populated monthly OOS folds; monthly is also the cadence at which Components 1-3 trend-gate/overlap/exhaustion calibrations are stable per the calibration-holdout sensitivity sweep -->
- **IS/OOS sensitivity sweep grid** (pre-registered): IS ∈ {12, 24, 36, 48} months × OOS ∈ {1, 3} months × embargo per §5.3 formula. **Selection criterion**: minimize mean OOS−IS Sharpe gap on the calibration holdout (separate from the walk-forward IS/OOS).  <!-- justify: pre-registered grid + selection criterion follows H053 design.md §5 protocol; the {12, 24, 36, 48} IS-length range brackets the trades-per-year-vs-stationarity tradeoff for a sub-daily strategy on equity-index futures per Tashman 2000 + Lopez de Prado AFML §7.4 -->
- **Embargo**: per §5.3 formula; reset-at-boundary policy primary; snapshot-at-right-edge alternative per §14.
- **Inner CV** (label-cfg + Optuna TPE): 3-fold purged walk-forward on each IS fold, purge=embargo per §5.3.
- **Cross-instrument correlation**: ES and NQ returns are highly correlated (ρ > 0.85 on 1-min bars); the SPA family construction per §1 treats {ES, MES} and {NQ, MNQ} as separate instrument-classes; within an instrument-class, the major + micro are linear-rescaled per ADR-0001 and treated as a single family member.

## 7. Cost model

`futures_orb_v1` per [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py) (1-tick slippage prior; per-side commission + exchange fee + NFA per [config/instruments.yaml](../../../config/instruments.yaml)). Cost is APPLIED as a per-trade log-return drag `log(1 - cost_round_trip / notional)` per ADR-0013 §3.1 F-CONV-2 binding. Empirical regime-wise calibration deferred to follow-up `P1-H055-COST-EMPIRICAL-CALIBRATION` (paper-trade prerequisite).

**Cost-floor sensitivity**: 1-tick slippage primary; 2-tick slippage reported as sensitivity exhibit per §14 (`sensitivity_mult ∈ {1.0, 2.0}`).  <!-- justify: 2-tick is the H050/H054 canonical sensitivity floor per ADR-0013 §3.1; ensures comparability of cost-conditional vs cost-robust annotations across the project's hypotheses -->

## 8. Gate thresholds (per ADR-0013; KPI-only, no binding gates)

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1, no KPI value forces or blocks any stage transition. Every former Class A item from ADR-0012 is reported as a KPI annotation.

### 8.a Methodological-correctness annotations (per ADR-0013 §2)

- **PIT / leakage-canary**: applicable: YES; binding test paths: Cycle-4 leak canary suite + per-hypothesis integration test [tests/integration/test_h055_pit.py](../../../tests/integration/test_h055_pit.py) (to be authored as §11.2 prereq before next H055 launch under follow-up `P1-H055-PIT-CANARY-INTEGRATION-TEST-LANDED`).
- **Calibration BSS**: applicable: NO. H055's pre-registered output is a continuous trading-rule directional signal (per-trade ATR-scaled TP/SL session P/L), not a calibrated probability forecast.
- **Reliability slope**: applicable: NO (same rationale as BSS).
- **Reproducibility log**: applicable: YES (canonical ReproLog per ADR-0009 13-field schema).
- **Cost-modeling realism**: applicable: YES (`cost-conditional` annotation expected; constant-tick slippage prior calibrated post-paper-trade).
- **DSR / PSR**: applicable: NO at v1 (the per-class SPA family at M=3 has no per-strategy CPCV path distribution; DSR computed under CPCV path distribution per ADR-0012 #5; H055 v1 uses single-path walk-forward per §6).

### 8.b KPIs (Class B; reported, not binding)

Per ADR-0013 §3.1 + §3.2 (mandatory ADR-0014 §3.2 9-table + bottom-line summary at top of KPI report card):

- **Sharpe-vs-passive**: passive benchmark = always-flat (zero return) AND buy-and-hold of front-month roll-adjusted continuous contract. Reported with LW2008 univariate CI on each arm.
- **Sharpe-vs-bench**: paired LW2008 differential CI vs (i) B&H, (ii) TSMOM per MOP 2012, (iii) no-skill random-entry bootstrap matched on side mix and holding-period distribution. Conjunctive STRICT dominance per §1.
- **Hansen SPA family p**: per-class SPA over the realized Optuna TPE-explored trial set (cardinality K ≤ K_max = 500 per fold). SPA_l / SPA_c / SPA_u all reported per Hansen 2005 §2.4.
- **Cross-instrument BH-FDR**: 4-element BH adjustment across {ES, MES, NQ, MNQ} per-class p-values at α=0.05.
- **Max-DD ratio (arm/passive)**: reported per ADR-0013 §3.1.
- **Power-margin ratio**: realized OOS n_trades / `n_required_for_power_80` per §9 below.
- **Cost-floor sensitivity**: 1-tick vs 2-tick (`sensitivity_mult ∈ {1.0, 2.0}`).
- **Body-overlap-coil-condition annotation** (KPI annotation per Component 2 calibration): `coil-condition-binding` if the OOS realised-`ρ_1` distribution's selected `q*`-quantile materially exceeds the calibration-holdout `q*`-quantile (≥ 1.96 SD on the bootstrap CI of the difference); `coil-condition-stable` otherwise. Reports the selected `ρ*` and the OOS realized `ρ_1` distribution per fold.
- **Trend-gate prediction Brier-score annotation** (KPI annotation per Component 1): per-fold OOS Brier score of the selected `ID_1*_c` against realized next-`k_swing`-bar log-return sign on T_L. Reported as `trend-gate-brier-{stable, drifted}` based on bootstrap CI overlap with the calibration-holdout Brier.
- **Inner-CV-winner deflation**: Bailey-López de Prado [Deflated Sharpe Ratio per JPM 40(5):94-107 (2014)](https://doi.org/10.3905/jpm.2014.40.5.094) on the OOS Sharpe of the IS-selected best cfg. Annotation: `dsr-cell-deflated-{positive, marginal, negative}`.

### 8.c Decision rule (§10 cross-reference)

Per ADR-0013 §1 KPI-only philosophy, the operator reviews the KPI report card values and decides the next stage transition. No KPI value forces or blocks. The user's 2026-05-04 standing directive applies: `kpi-report-emitted` → `ninjascript-implemented` is operator-discretionary upon canonical-format presentation.

## 9. Stopping rule + power

### 9.1 Trial-budget K_max derivation (pre-registered)

Pre-registered target detectable annualized Sharpe effect = 0.30 at SPA α = 0.05. SPA power for a centered alternative is monotone-decreasing in K and in the dispersion ω of the inferior-model loss (Hansen 2005 §3). Power table populated by [scripts/run_h055_spa_power_simulation.py](../../../scripts/run_h055_spa_power_simulation.py) (stub at this commit; body-pending under follow-up `P1-H055-POWER-SIMULATION-EXECUTE`):

| K \ ω | ω = 0.30 | ω = 0.45 (central) | ω = 0.60 |
|---|---|---|---|
| 100 | [to be filled] | [to be filled] | [to be filled] |
| 250 | [to be filled] | [to be filled] | [to be filled] |
| 500 | [to be filled] | [to be filled] | [to be filled] |
| 1000 | [to be filled] | [to be filled] | [to be filled] |

DGP for the simulation = stationary bootstrap on the v1 pilot returns at PW2004+PPW2009 block length; target effect size 0.30 annualized SR; α = 0.05; output `power(K, ω)`.

**K_max selection rule**: choose K_max such that power ≥ 0.80 in the central cell (ω = 0.45). The pre-registered K_max = 500 value is **provisional pending P1-H055-POWER-SIMULATION-EXECUTE**; the production walk-forward dispatch is conditional on the simulation having run and producing the empirical K_max. If the central-cell power at K = 500 falls below 0.80, K_max is reduced to the largest K satisfying the rule; if power is comfortably above 0.80 at smaller K, K_max is rebound to that smaller value at the first running run via the simulation script's output. The provisional 500 is sourced from the H050/H054 typical Optuna trial budget, not from a power calculation. The finite-K SPA bound of [Hsu, Hsu & Kuan 2010, *JEF* 17(3):471-484](https://doi.org/10.1016/j.jempfin.2010.01.001) corroborates the cap.  <!-- justify: K_max = 500 is PROVISIONAL pending P1-H055-POWER-SIMULATION-EXECUTE; rebound to empirical value at first running run; the 500 is provisional from the H050/H054 typical Optuna trial budget; cap satisfies the Hsu-Hsu-Kuan 2010 finite-K SPA bound at α=0.05 -->

**SPA-family scope**: the discrete enumerated grid (T_H × T_L × ID_1 × L × N × H_dwell × k_swing × n × k × R*) has cardinality ≈ 460,800 combinations before continuous-axis discretization, so K_max = 500 covers ≈ 0.1% of the discrete grid by enumeration. The SPA family is therefore explicitly defined as the **TPE-explored subset** of trials actually evaluated, interpreted under the TPE coverage and convergence properties of [Bergstra et al. 2011, *NeurIPS 24*](https://papers.nips.cc/paper/4443-algorithms-for-hyper-parameter-optimization). **Inferential implication**: SPA p-values are conditional on the realized TPE exploration trajectory and do not provide grid-wide superior-predictive-ability guarantees; this is a deliberate scope choice. Data-snooping concern explicitly addressed via Romano-Wolf 2005 + Harvey-Liu-Zhu 2016. White 2000 Reality Check reported as corroborating second test.

### 9.2 Per-arm power calculation

For LW2008 univariate CI on `T_H055_i = SR_v2_i − SR_bench_i` excluding zero at α=0.05 two-sided, 80% power requires (per [Lo 2002, *FAJ* 58(4):36-52](https://doi.org/10.2469/faj.v58.n4.2453) Sharpe SE ≈ √((1+0.5·SR²)/n)):

- SR_pilot per-trade ≈ 0.50 (from v1 pilot 74.85% win rate × $36.01 expectancy / $72.02 per-trade σ); annualized SR_pilot ≈ 0.50 × √7180 ≈ 42.4 if cadence holds at scale (highly optimistic; cadence floor is the controlling assumption).
- Realistic v2 OOS effect at differential-Sharpe scale (v2 − bench): pre-registered target = 0.30 annualized; equivalent per-trade = 0.30 / √7180 ≈ 3.54e-3.
- Required T_per_trade for SE(SR) ≤ 1.81e-3 ≈ 343,000 per-trade observations under iid Lo 2002 benchmark; under autocorrelation-adjusted Lo 2002 §III.B / eq. 19 the required T scales with the autocorrelation factor.
- Realized OOS trade count: approximately 244 + 230 = 474 RTH sessions × pilot-cadence-projection 28.5 trades/session = 13,500 trades (ES); approximately 244 + 245 = 489 sessions × 28.5 ≈ 13,940 trades (NQ). **Cadence floor**: if realized v2 cadence is ½ pilot, required T quadruples; if 2× pilot, required T halves.

### 9.3 Power verdict

Per-instrument-class H055 v1 inference is **adequately powered** at the pre-registered 0.30 annualized SR target IF realized v2 cadence ≥ ½ × pilot cadence (≥ 14.25 trades/session). If realized cadence falls below this floor on the OOS, `power-margin-low` annotation is applied per ADR-0013 §3.1 and the result is interpreted accordingly.

Realized n vs n_required ratio reported as `power-margin-ratio` KPI annotation per ADR-0013 §3.

### 9.4 Stopping rule

Single production walk-forward run per instrument-class on the §2 OOS test fold. No multiple-rerun-on-same-OOS pattern. If a run completes and the KPIs produce a marginal verdict, the result is recorded and operator decides next steps; no re-running with different seeds or different inner-CV folds on the same OOS (would constitute pseudo-multiple-testing per López de Prado AFML §13).

**Per-fold disposition**: any fold flagged by Ljung-Box on squared returns at α=0.05 with [Holm 1979, *Scand J Statistics* 6(2):65-70](https://www.jstor.org/stable/4615733) Holm-Bonferroni adjustment across the K folds, OR by [Bai & Perron 2003, *J Applied Econometrics* 18(1):1-22](https://doi.org/10.1002/jae.659) CUSUM-style break detection at the fold's own significance level, is excluded from the SPA family and the exclusion is logged in the audit trail.

**Minimum surviving fold count**: `n_min_folds = ceil(0.6 × total_folds)` pending the K_max power simulation (§9.1).  <!-- justify: 0.6 surviving-fold floor pending empirical calibration under P1-H055-POWER-SIMULATION-EXECUTE; chosen as a placeholder consistent with the H050/H054 walk-forward fold-survivability convention. HHK 2010 reference DROPPED — citation does not address this rule. -->

### 9.5 Methodologically-honest expectation

H055 v1 is a non-trivial mechanization of a 6-session discretionary pilot whose realized expectancy is positive but whose inferential support is structurally weak (n=171, single window, no walk-forward analogue). The v1 OOS test fold exists to determine whether the four-component mechanization preserves any of the pilot's economic signal under walk-forward purged CV with realistic costs. A null result is consistent with "the pilot's realized expectancy was the upper-tail of a session-cadence small-sample distribution"; a positive result is consistent with "the four-component mechanization captures structural alpha that survives walk-forward + cost realism."

## 10. Decision rule

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): no KPI value forces or blocks any stage transition. Operator reviews the KPI report card and decides at every transition (operator-discretionary; decision-logged).

Stage progression is the canonical: `exploration-in-progress` → `kpi-report-emitted` → `ninjascript-implemented` → `paper-trade-active` → `paper-trade-evaluated` → `live-promoted`. Per the user's 2026-05-04 standing directive, the `kpi-report-emitted` → `ninjascript-implemented` transition is operator-discretionary upon canonical-format presentation. **H055 explicitly inherits the operator-decline-ninjascript directive** from H052a's 2026-05-04 standing decision.

**Pre-reg-frozen interpretation guide** (operator-informational, NOT a binding gate):

- **All three pairwise LW2008 differential CIs strictly exclude zero on the positive side, AND BH-FDR-adjusted q < 0.05 on the instrument-class** (conjunctive STRICT dominance + family-wise FDR control): H_1 supported on that class. Hansen SPA p reported as advisory annotation `spa-p-{below,above}-0.05` per F1-007 downgrade (ADVISORY, not conjunctive — the TPE-conditioned SPA p does not provide grid-wide superior-predictive-ability guarantees). Operator may reasonably authorize NinjaScript progression.
- **At least one pairwise LW2008 CI covers zero, OR BH-FDR q ≥ 0.05**: H_1 not supported on that class (conjunctive criterion fails). Operator may reasonably decline NinjaScript progression. SPA-p-fail moves from CONJUNCTIVE to ADVISORY per F1-007 (annotation only).
- **Drawdown breach**: OOS MaxDD exceeds the empirical 95th percentile of v1-pilot rolling MaxDD on the same instrument set. Operator should weight toward decline.
- **Capacity floor**: estimated capacity (square-root impact bound per [Loeb 1983, *FAJ* 39(3):39-44](https://doi.org/10.2469/faj.v39.n3.39); *practitioner*) < live equity × max position notional implied by f̂. Operator should weight toward decline.

What replaces v2 on a kill decision: **stand aside** (no v1-mechanical fallback). The discretionary v1 cannot be mechanized as fallback because v1 is by definition discretionary; mechanizing it as fallback would re-introduce the same discretionary failure modes the v2 mechanization is designed to eliminate.  <!-- justify: locked decision; v1-mechanical-fallback would reintroduce the directional/setup/sizing discretion that is the design target of v2 mechanization, defeating the purpose of the H055 hypothesis -->

## 11. Reproducibility commitments

Per [ADR-0009](../../../docs/decisions/ADR-0009-blas-thread-pinning.md) + [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3:

- BLAS thread pinning (OMP_NUM_THREADS=1 + MKL_NUM_THREADS=1 + OPENBLAS_NUM_THREADS=1 env-var assertion + `threadpoolctl.threadpool_limits(1)` in orchestrator `__main__`).
- All 13 ReproLog fields populated: git_head, dataset_checksums, config_resolved_sha256, env_id, model_hash (= scientific_payload_sha256 binding; for H055, the Optuna study identifier + study-state hash, or the artifact hash of the trained-parameter pickle), pip_freeze_sha256, rng_seed, etc.
- Sidecar with scientific_payload SHA256 binding to ReproLog model_hash.
- Random seed: 20260506 (frozen).  <!-- justify: design-date encoded as YYYYMMDD per the H054 F-Q-8 convention; deterministic, no upstream selection bias -->
- Single-seed mandate: no per-replicate seed sweep on the OOS test fold.

### 11.1 Kill-switch parameters (per ADR-0013 §5.1; amended 2026-05-08 per ADR-0017 §5; cross-link to NinjaScript §15)

NinjaScript implementation kill-switch parameters. The 8 hard kill-switch constraints K-1 through K-8 are inherited from [ADR-0017 §5](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) project-wide mandatory inheritance; the H055-specific numeric defaults are calibrated below. Constraints are enforced at the kill-switch layer in NinjaScript implementation (used at paper-trade-active and live stages) AND validated at the backtest layer in the Python walk-forward orchestrator (per `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`).

Per ADR-0017 §5, defaults MAY be tightened with `# justify:` annotation but MAY NOT be loosened below the ADR-0017 default without project-level ADR amendment.

| ID | Constraint | H055 default | Cross-link |
|---|---|---|---|
| K-1 | Per-trade $-stop | `1.0 × R` where `R = β · ATR_n · point_value · position_size`, `β` per §5 search domain (default 1.5; ATR-units) | ADR-0017 §5 K-1; Turtle 2N convention per Faith 2007 *practitioner* |
| K-2 | Per-trade time-stop | 2 × median winning-trade duration on calibration holdout (per-instrument-class; populated post-`P1-H055-CALIBRATION-HOLDOUT-RUN`); fallback default = 30 min if calibration not yet run | ADR-0017 §5 K-2; mechanical inverse of avg_losing_time = 3.65× avg_winning_time in pilot ledger |
| K-3 | No-add-to-loser | Forbid second entry on same instrument while open position is in unrealized loss; **zero exception** | ADR-0017 §5 K-3; mechanical inverse of 2026-05-07 17:06/17:08/17:16 CL stack ($-5,850 in one co-stopped exit) |
| K-4 | Per-symbol position cap | Per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md): ≤ 20 ES, ≤ 40 NQ, ≤ 200 MES, ≤ 400 MNQ; energy/metals deferred per §2 (`P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND`) | ADR-0017 §5 K-4 |
| K-5 | Correlated-instrument inventory cap | ES+MES share a budget; NQ+MNQ share a budget; aggregate per-group $-notional ≤ 1.0× the largest single-symbol cap in the group | ADR-0017 §5 K-5; catches cross-symbol stacks |
| K-6 | Daily circuit breaker | Cease trading for the session at -2% of equity realized P/L | ADR-0017 §5 K-6; mechanical inverse of 2026-05-07 11-hour escalation from peak-equity to MaxDD |
| K-7 | Weekly circuit breaker | Cease trading for the week at -5% of equity realized P/L | ADR-0017 §5 K-7 |
| K-8 | Adverse-direction entry filter | Forbid entries where the trigger bar's higher-TF (T_H per §3 Component 1) trend gate sign disagrees with the entry direction AND price has moved adversely > 0.5 ATR from entry-bar open at fill time | ADR-0017 §5 K-8; mechanical inverse of "averaging-down into a falling knife" pattern |

Legacy H055-specific operational parameters (preserved for paper-trade calibration; NOT in the ADR-0017 K-1..K-8 set):

- `Daily attempt cap`: 50 wick-rejection attempts per session (≈ 1.75× pilot-cadence ceiling; slack for adverse-selection sessions). Calibration holdout will refine this default under `P1-H055-KILL-SWITCH-EMPIRICAL`.
- `Wall-clock cap`: 15:55 ET timestop (matches §4 hard close); subsumed by K-2 per-trade time-stop in the limit but retained as session-end safety net.

### 11.1.1 Survival-constrained sizing (per ADR-0017 §4.1; binding for production walk-forward)

Component 4 (sizing inputs) per §3 is amended to use the project-canonical drawdown-constrained Kelly sizing rule per [ADR-0017 §4.1](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md). The position-size formula is:

```
position_size_t = floor(min(
    per_trade_risk_budget_t / (k × ATR_n_t × tick_value),
    kelly_fraction_t × equity_t / (entry_price_t × tick_value × multiplier),
    retail_capacity_ceiling
))
```

with:
- `per_trade_risk_budget_t = 0.01 × equity_t` (1% of current equity; Turtle convention per Faith 2007 *practitioner*)
- `k = 2.0` (the Turtle 2N stop convention)
- `kelly_fraction_t = clamp(f_kelly_raw_t × 0.25, 0, 0.25)` (quarter-Kelly cap; the practitioner-canonical floor per [MacLean-Thorp-Ziemba 2010](https://doi.org/10.1142/7598)); `f_kelly_raw_t` from the IS-fold per-trade R-multiple distribution per Vince 1990 *practitioner*
- `equity_t` is the **current** account equity at t (NOT starting equity); this is the structural defense against the operator's empirical "size scaled with run-up but not unscaled with drawdown" failure mode

Implementation is bound to [src/skie_ninja/sizing/](../../../src/skie_ninja/sizing/) per `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE` (BLOCKING-BEFORE-LAUNCH per §11.2).

### 11.2 Pre-reg implementation prerequisites (BLOCKING-BEFORE-LAUNCH)

- `P1-H055-LIT-CHECK-PHASE-0` (BLOCKING-BEFORE-`designed`-FREEZE): see §15.1 verdict.
- `P1-H055-DESIGN-MD-AUDIT-LOOP` (BLOCKING-BEFORE-`designed`-FREEZE): 3-round audit-remediate-loop on the staging draft → this restructured H055 design.md; closed 2026-05-06; audit trail [docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../../../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md).
- `P1-H055-DATA-REQUIREMENTS-DESIGNED-FREEZE` (BLOCKING-BEFORE-LAUNCH): [data_requirements.md](data_requirements.md) `status: draft` → `status: designed` concurrently with this design.md freeze.
- `P1-H055-PIT-CANARY-INTEGRATION-TEST-LANDED` (BLOCKING-BEFORE-LAUNCH): integration test [tests/integration/test_h055_pit.py](../../../tests/integration/test_h055_pit.py) wiring the Cycle-4 leak canary suite around the H055 feature factory + label construction + walk-forward orchestrator.
- `P1-H055-LEVEL-STATE-FOLD-CONTINUITY-TEST` (BLOCKING-BEFORE-LAUNCH): unit test [tests/unit/test_h055_level_state_fold_continuity.py](../../../tests/unit/test_h055_level_state_fold_continuity.py) per §5.3 fixture cases (ETH 23-hour, RTH-only 405-min, fold boundary across CME daily 17:00 CT maintenance halt) and embargo unit-consistency assertions.
- `P1-H055-NEWS-CALENDAR-INGEST` (BLOCKING-BEFORE-LAUNCH): news-calendar module [src/skie_ninja/utils/news_calendar.py](../../../src/skie_ninja/utils/news_calendar.py) with FOMC/NFP/CPI release-time loaders per §4.
- `P1-H055-POWER-SIMULATION-EXECUTE` (BLOCKING-BEFORE-LAUNCH): execute [scripts/run_h055_spa_power_simulation.py](../../../scripts/run_h055_spa_power_simulation.py) and populate the §9.1 4×3 power table; revisit K_max + `n_min_folds` per the §9 selection rules.
- `P1-H055-CALIBRATION-HOLDOUT-RUN` (BLOCKING-BEFORE-LAUNCH): execute the §5.1 trend-identifier supervised competition + §5.2 ρ* calibration on the 2015-2019 calibration holdout; freeze the per-instrument-class `ID_1*_c` and the global `q*` for the production walk-forward.
- `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE` (BLOCKING-BEFORE-LAUNCH per ADR-0017 §4.1): implement [src/skie_ninja/sizing/](../../../src/skie_ninja/sizing/) module with `kelly_fraction_from_r_multiples`, `drawdown_constrained_kelly`, `compute_position_size` per ADR-0017 §4.1.
- `P1-CALMAR-DIFFERENTIAL-CI-IMPL` (BLOCKING-BEFORE-LAUNCH per ADR-0017 §2.2): implement [src/skie_ninja/inference/calmar.py](../../../src/skie_ninja/inference/calmar.py) with `calmar_ratio`, `calmar_differential`, `calmar_differential_ci_stationary_bootstrap`.
- `P1-PROFIT-FACTOR-CI-IMPL` (BLOCKING-BEFORE-LAUNCH per ADR-0017 §2.3): implement [src/skie_ninja/inference/profit_factor.py](../../../src/skie_ninja/inference/profit_factor.py) with `profit_factor`, `profit_factor_differential`, `profit_factor_differential_ci_stationary_bootstrap`.
- `P1-R-MULTIPLE-CI-IMPL` (BLOCKING-BEFORE-LAUNCH per ADR-0017 §2.4): implement [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py) with `r_multiple_from_trade`, `r_multiple_distribution`, `r_multiple_mean_ci_stationary_bootstrap`.
- `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE` (BLOCKING-BEFORE-LAUNCH per ADR-0017 §4.2): implement [src/skie_ninja/inference/risk_of_ruin.py](../../../src/skie_ninja/inference/risk_of_ruin.py) with `probability_of_ruin_monte_carlo`.
- `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` (BLOCKING-BEFORE-LAUNCH per ADR-0017 §6): implement [scripts/stress_test_failure_modes.py](../../../scripts/stress_test_failure_modes.py) with the 5 synthetic failure modes (FM-1 death-by-thousand-cuts, FM-2 gap-overnight, FM-3 news-spike, FM-4 latency-induced-bad-fill, FM-5 regime-change-mid-trade).
- `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` (BLOCKING-BEFORE-LAUNCH per ADR-0017 §5): wire the K-1..K-8 hard kill-switch constraints into the Cycle-4 leak-canary discipline at the walk-forward orchestrator layer; emit a `kill-switch-canary-{pass,fail}` annotation per fold.

## 12. Relationship to other hypotheses

- **H050** (HMM-gated 1-min directional): definitive negative on the 2024-2025 OOS (T_H050 LW2008 CI excludes zero on negative side). H055 is ORTHOGONAL: different signal class (wick-rejection MR vs HMM-gated continuation), HMM-deferred, different label (per-trade ATR-scaled vs per-bar regime-gated).
- **H052a** (HMM-gated ORB): non-significant null on 2023-H2 + 2024 OOS. H055 is orthogonal: different signal class (intraday wick-rejection scalp vs first-hour ORB breakout), HMM-deferred, different label (per-trade ATR-scaled vs per-session ORB), different cadence (sub-daily many-trades vs once-per-session).
- **H053** (multi-timeframe regression with mediation): kpi-report-emitted; marginal results. H055 is orthogonal (deterministic-rule wick-rejection vs ML-regression multi-timeframe).
- **H054** (anti-gate stress-state ORB): pending production walk-forward. H055 is orthogonal: different signal class, HMM-deferred (vs H054's anti-gate inversion of an HMM emission), different label (per-trade vs per-session ORB).
- **H055 successor**: `P1-H055-V2-WITH-HMM-REGIME-GATE` (deferred to v3; integrate the existing HMM toolkit per ADR-0005 + the `filter_states` causal forward filter as a layer on top of Component 1; v2 may also extend to CL/MCL/MGC/MYM under `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND`).

### 12.1 Cross-hypothesis SPA construction

H055 enters the per-hypothesis SPA family as a per-class M=3 inferential family (B&H, TSMOM, no-skill) with a BH-FDR adjustment across the four instrument-classes. Cross-hypothesis SPA composite null at full project family (H050 + H052a + H053 + H054 + H055) is NOT computed at v1 due to heterogeneous OOS windows (Hansen 2005 §2 requires shared bootstrap-index sample length across strategies for cross-dependence preservation). Deferred to project-level ADR per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`.

### 12.2 Successors (amendment 2026-05-06)

Per the 2026-05-06 H055 successor tree at [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md) (concurrent landing in this commit group), H055 v1 spawns the following successor lineage. Sequencing: **H056 → H057 → H058 → H059** as the main chain; **H055-CL/MCL/MYM/MGC v2** + **H055-event-time** as parallel tracks. All successors carry their own pre-registration discipline; this subsection records the cross-link and locks the queue order, not the design content.

- **H056 — Per-component ML successor**. Lifts SKIE-NINJA-Volatility ML primitives per [ADR-0016](../../../docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md) audit-and-lift protocol (concurrent landing); new ML probability heads for body-overlap, level-exhaustion, and swing-pivot detection replacing the deterministic Components 2-4. Per-component pre-registration discipline per [ADR-0015](../../../docs/decisions/ADR-0015-component-stacking-master-architecture.md) §2.1 (concurrent landing). Status: queued. Cross-link: [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md).
- **H057 — Stacking master successor**. Super Learner per [van der Laan, Polley, Hubbard 2007 *Stat Appl Genet Mol Biol* 6(1):Article 25](https://doi.org/10.2202/1544-6115.1309) over the H056 component panel. One stacking master per instrument-class. Status: queued. Cross-link: [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md).
- **H058 — Multi-TF attention orchestrator**. TF-attention per [Vaswani et al. 2017 *NeurIPS* (arXiv:1706.03762)](https://arxiv.org/abs/1706.03762) lifted to the tabular setting; one stacking master per timeframe with attention integration across {1m, 5m, 15m}. Feeds on §14.1 MTF confluence + cross-TF divergence exhibits. Status: queued. Cross-link: [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md).
- **H059 — Live probability display layer**. Calibrated direction probability + first-passage-time price targets via Karatzas & Shreve 1991 *Brownian Motion and Stochastic Calculus* (Springer GTM 113) first-passage results + bootstrap-conditional CI. Presentation-only; not a new H_0 / H_1; no SPA family entry. Status: queued. Cross-link: [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md).
- **H055-CL/MCL/MYM/MGC v2 (energy + metals + Dow micro extension)**. Pending substrate ingest per `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND` (already-noted at §12 main bullet for H055 successor); same components, expanded universe. Parallel track to the H056-H059 main chain. Status: queued.
- **H055-event-time variant**. Event-time / volume-clock bars per [López de Prado 2018 *Advances in Financial Machine Learning* §2.5 "Bars"](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) (Wiley, ISBN 978-1119482086, *practitioner*; canonical project-internal reference for the bar-construction framework) with cross-reference to Easley, López de Prado & O'Hara 2012 "The Volume Clock: Insights into the High Frequency Paradigm" *Journal of Portfolio Management* 39(1):19-29 (original journal source for the volume-clock framework; no DOI on the *JPM* article; [SSRN 2034858](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2034858) preprint for resolvability). Re-bar at uniform-volume buckets and re-run the same Components 1-4. Cross-link to backlog item H011 (event-time bars). Parallel track to the H056-H059 main chain. Status: queued.

Each successor will register its own design.md + lit_review + data_requirements + KPI report card under [research/01_hypothesis_register/](../../) and carry its own ADR-0014 §3.2 9-table results-summary. The successor queue order locked here is itself a pre-registration commitment under Path A.

## 13. Output artifacts

Per ADR-0013 §3 + ADR-0014 §3.2, the production walk-forward must produce:

- KPI report card v1 [research/01_hypothesis_register/H055/H055_kpi_report_v1.md](H055_kpi_report_v1.md) (template per ADR-0014 §3.2 9-table format mandatory).
- Stage tracker [research/01_hypothesis_register/H055/stage.md](stage.md) (kpi-report-emitted row).
- Failure log [research/01_hypothesis_register/H055/failure_log.md](failure_log.md).
- Audit-remediate-loop trail at [docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../../../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md) (this commit's design audit) plus subsequent per-stage trails at `docs/audits/audit_trail_YYYY-MM-DD_h055-*.md`.
- Sidecar at `artifacts/runs/H055/{run_id}/sidecar.json` with scientific_payload SHA256.
- ReproLog at `logs/reproducibility/{run_id}.json`.
- Operator decision logged at `logs/promotions/{run_id}_H055_{instrument_class}_promotion.md` per ADR-0013 §5.3.
- Pilot ledger reconciliation report at `reports/h055/pilot_adherence_audit_v1.md` per §14 advisory adherence audit.

## 14. Robustness exhibits (informational; not gating)

- **Per-instrument-class vs cross-instrument-class sensitivity**: re-fit Components 2-4 per-instrument-class (4 separate fits) with James-Stein 1961 shrinkage toward the cross-class mean; report differential Sharpe and BH-FDR-adjusted differential.  <!-- justify: locked decision; tests whether the design's primary "shared C2-C4 across classes" choice introduces material bias; James-Stein shrinkage as the principled mid-point between fully-pooled and fully-separate -->
- **Long/short asymmetric parameters as sensitivity**: re-fit with Stein-shrunk long/short parameter vectors; compare against the primary independent-fit baseline.
- **Cost-floor 2-tick**: re-run with `sensitivity_mult = 2.0` on the same artifacts.
- **ETH-only vs RTH-only sensitivity**: re-run with the eligible-bar filter switched to ETH-only (sessions 17:00 ET previous day → 09:30 ET) and RTH-only; compare differential Sharpe.
- **ρ_2 fragility sensitivity**: re-run with `ρ_2` substituted for `ρ_1` as the Component 2 trigger; report differential Sharpe and the per-fold rate at which `ρ_2` collapses to 0 (the disjoint-bar-fragility documented at calibration).
- **Snapshot-at-right-edge alternative for Component 3 state machine**: re-run with the level-exhaustion state machine carrying the snapshot state at the embargo's right edge instead of resetting at fold boundary; report differential Sharpe.
- **MES/MNQ robustness**: reported as KPI annotation; not load-bearing.
- **Pilot adherence audit (advisory only)**: replay the 171-trade pilot ledger from 2026-05-01 → 2026-05-06 against v2; classify each trade as adherent/non-adherent across each component (C1 trend-gate state, C2 ρ trigger, C3 R(L) ≤ R*, C4 sizing within ±1 contract); estimate the realized-P&L cost per failure mode. **Statistical procedure**: stratum-mean stationary-bootstrap CI on per-trade dollar P&L with minimum cell size such that half-width ≤ h* per [Bickel & Freedman 1981, *Annals of Statistics* 9(6):1196-1217](https://doi.org/10.1214/aos/1176345637) bounds; sparse cells pooled before inference. **Advisory only** per ADR-0013 §1; feeds operator review, does not gate progression.

### 14.1 Cross-timeframe robustness exhibits (amendment 2026-05-06; informational; not gating)

Per the 2026-05-06 amendment landing concurrently with the H055 successor tree at [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md) + [ADR-0015](../../../docs/decisions/ADR-0015-component-stacking-master-architecture.md) component-stacking master architecture + [ADR-0016](../../../docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md) sibling-repo audit-and-lift protocol, the following five cross-timeframe (MTF) exhibits are appended. All are INFORMATIONAL only — none enters the LW2008 strict-CI-dominance H_1 family or the Hansen 2005 SPA family per H055 v1's strict CI dominance criterion (§1 + §10). All are reported as KPI annotations on the OOS test fold and feed successor pre-registrations (H056 / H057 / H058) per the successor tree. This subsection is Path A frozen-pre-reg amendment scope per ADR-0013 (informational exhibits, not new features in §3).

- **MTF confluence score (informational; not gating)**: count of timeframes T ∈ {1m, 5m, 15m} simultaneously showing (`is_swing_pivot` AND `ρ_1 > ρ*` AND `wick_size > θ_wick · ATR_n`). Score ∈ {0, 1, 2, 3}. Reported as KPI annotation `mtf-confluence-{0,1,2,3}` per ADR-0013 §2 binding. Stratified P&L reporting per confluence score on the OOS test fold. Empirically motivated by the observation that practitioner wick-rejection setups often gain robustness when multiple timeframes agree (Connors & Raschke 1995 *Street Smarts*, *practitioner*; loose statistical anchor in [Lo, Mamaysky, Wang 2000 *J Finance* 55(4):1705-1765](https://doi.org/10.1111/0022-1082.00265) on technical-pattern conditional return distributions). <!-- justify: T ∈ {1m, 5m, 15m} mirrors the higher-TF set already present in §3 Component 2 body-overlap; ρ* + θ_wick are the same thresholds bound at calibration per §3, no new free parameter is introduced -->
- **Cross-TF momentum divergence**: trend-identifier sign on T_H (15m) × wick-rejection setup on T_L (1m). The classical "trade with the higher-TF trend, fade the local lower-TF extreme" pattern. Reported as KPI annotation `mtf-divergence-{trend-aligned,trend-fade,neutral}`. Stratified P&L by alignment status on the OOS test fold. Practitioner-derived (Connors & Raschke 1995 *Street Smarts*, *practitioner*); flagged as such; no new features in §3 (re-uses Component 1 trend-identifier output × existing setup detector).
- **Multi-TF ATR ratio**: ATR_n[1m] / ATR_n[15m]. Scale-mismatch indicator. Reported as a robustness exhibit at four quantile cuts of the ratio (Q1, Q2, Q3, Q4 buckets) on OOS. Investigates whether the wick-rejection edge concentrates in specific cross-TF volatility regimes. <!-- justify: quartile cuts (not deciles) chosen to keep stratum cell-size adequate for the OOS sample (n_OOS ≈ 2024-2025 sessions × intraday-trade rate) per the same Bickel-Freedman 1981 half-width logic as §14 pilot adherence audit; reported on existing ATR_n already bound in §3 Component 4, no new parameter -->
- **Multi-TF Hurst exponent**: per-TF rough-vs-trending classifier per [Gatheral, Jaisson, Rosenbaum 2018 *Quantitative Finance* 18(6):933-949](https://doi.org/10.1080/14697688.2017.1393551). Reported as KPI annotation `hurst-{rough,neutral,trending}` × T_H. Investigates whether the H055 wick-rejection setup is preferentially profitable in rough-volatility (low-Hurst, H < 0.5) regimes where intraday mean reversion is more reliable. <!-- justify: rough/neutral/trending tertiles bound at the cross-fold IS empirical Hurst distribution (33rd / 67th percentiles), not a magic-number threshold; computed per-TF on a rolling window matched to the §3 Component 1 trend-identifier window -->
- **Daily / session-context exhibit**: distance from yesterday's high / low / close in ATR units; opening gap relative to prior session range. Reported as KPI annotation `prev-day-context-{at-extreme,inside-range,gap}`. Investigates the well-documented (practitioner) interaction between intraday wick-rejection setups and prior-session structural levels. Practitioner-anchored (Crabel 1990 *Day Trading with Short Term Price Patterns and Opening Range Breakout*, *practitioner*; same anchor as H052a §15.1 erratum-1); flagged as such; loose statistical cousin in level-memory effects per Bouchaud-Gefen-Potters-Wyart 2004 *Quant Finance* (already cited at §15.1 row 4). <!-- justify: at-extreme / inside-range / gap classification uses ATR-unit distance bands derived at calibration on the IS fold (no in-test threshold tuning); ATR_n is already bound in §3 Component 4 -->

**Successor-tree binding**. Each exhibit informs successor hypothesis pre-registrations per the H055 successor tree at [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md) (concurrent landing in this commit group; the file may not exist on disk yet at the moment this amendment lands but the cross-link is forward-looking and will resolve in the same commit group). Specifically: (a) MTF confluence + cross-TF divergence feed H058 multi-TF attention orchestrator feature design; (b) Multi-TF ATR ratio + multi-TF Hurst feed H056 per-component ML successor's volatility-regime conditioning per ADR-0015 §2.1; (c) daily / session-context feeds H056's body-overlap + level-exhaustion ML probability heads per ADR-0016 audit-and-lift protocol from sibling SKIE-NINJA-Volatility.

## 15. NinjaScript Implementation (per ADR-0013 §5.1)

Per ADR-0013 §5 + §5.1, every hypothesis design.md gains a §15 enumerating the NinjaScript C# implementation. H055's NinjaScript implementation is sequenced AFTER the production walk-forward Stage-3 KPI report card emission per follow-up `P1-H055-NINJASCRIPT-IMPL`.

Implementation pattern (pure-C# implementable per ADR-0013 §1.2; no bridge required because Components 1-4 are deterministic, non-ML, and require no Python inference at decision time — HMM is OUT-OF-SCOPE at v1):

- **C# class**: `H055AntiWickReversalScalp` at `ninjascript/strategies/H055AntiWickReversalScalp.cs`.
- **Entry/exit logic**: 1:1 with Python signal generation per design.md §4.
- **Component 1 trend gate**: NinjaScript-native ADX (built-in indicator) + NinjaScript-native EMA (for MA-crossover); HAC-OLS slope and TSMOM sign implemented in pure C# using the existing rolling-window primitives.
- **Component 2 body-overlap**: closed-form pairwise Jaccard over the last N higher-TF bars; pure C# loop.
- **Component 3 level-exhaustion state machine**: pure C# state-machine class.
- **Component 4 ATR + Kelly clamp**: NinjaScript-native ATR; Kelly clamp computed per fold offline (Python) and deployed as a static parameter per instrument-class.
- **Kill-switch parameters**: per §11.1.
- **Fill-log schema**: matches H050/H054 plan §6.1 schema; includes `component_state_at_fill` field (C1 sign, C2 ρ_1, C3 R(L) count) for post-trade reconciliation.
- **Sim101 smoke-test record**: TBD (run after NinjaScript class authored).
- **Cross-reference to canonical KPI report card**: H055_kpi_report_v1.md.

Python ↔ NinjaScript parity-check artifact required per ADR-0013 §5.2 (default convention: byte-equality on integer signal vector — sign of next entry per (instrument-class, T_L bar) tuple; per-strategy calibration via `P1-H055-NINJASCRIPT-PARITY-TOLERANCE`).

**Operator 2026-05-04 standing decline directive applies**: `kpi-report-emitted` → `ninjascript-implemented` is operator-discretionary upon canonical-format presentation. The implementation work is sequenced per ADR-0013 §5; the operator may decline progression at any KPI level.

### 15.1 Phase 0 lit-check verdict

Per `P1-H055-LIT-CHECK-PHASE-0`, the primary-source claim domains in §1 + §3 + §5 were verified during the round-1 audit-remediate loop on the staging draft (audit trail [docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../../../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md); literature findings L1-001 through L1-014 in Round 1; subsequent rounds dispositioned). Verdict summary:

| Domain | Citation | Verification | Verdict on H055 framing |
|---|---|---|---|
| 1. TSMOM (Component 1a) | MOP 2012 *JFE* | DOI verified in audit trail | SUPPORTS continuation-sign trend gate at multi-month; intraday extension is parameter-grid-search not literature-canonical |
| 2. HAC-OLS (Component 1c) | NW 1994 + Andrews 1991 + Kiefer-Vogelsang 2002 | DOIs verified; KV 2002 added in R1 for L<60 fixed-b | SUPPORTS HAC-corrected slope inference |
| 3. Realized vol regime (formal cousin to Component 2) | Andersen-Bollerslev-Diebold-Labys 2003 *Econometrica* | DOI verified | SUPPORTS regime characterization; not directly the body-overlap consolidation rule (practitioner-anchored) |
| 4. Level memory (formal cousin to Component 3) | Bouchaud-Gefen-Potters-Wyart 2004 *Quant Finance* | DOI verified; replaced BMP 2002 in R1 | SUPPORTS level-memory effects in LOB; H055 swing-pivot levels are practitioner-anchored |
| 5. Fractional-Kelly (Component 4) | MacLean-Thorp-Ziemba 2010 (DOI 10.1142/7598) | DOI verified | SUPPORTS half-Kelly clamping rationale |
| 6. Sharpe inference | Lo 2002 + Opdyke 2007 + LW 2008 + PW 2004 + PPW 2009 | DOIs verified | ESTABLISHED standard; LW 2008 SB-variant used per project convention |
| 7. SPA / multiple-testing | Hansen 2005 + Hsu-Hsu-Kuan 2010 + White 2000 + Romano-Wolf 2005 + Harvey-Liu-Zhu 2016 | DOIs verified | ESTABLISHED standard; H055 SPA family scope is the realized TPE trial set per Bergstra 2011 |
| 8. News-time exclusion | Lucca-Moench 2015 *J Finance* | DOI verified | SUPPORTS pre-FOMC drift exclusion; ±15 min envelope is conservative pre-reg |
| 9. Capacity bound | Loeb 1983 *FAJ* (*practitioner*) | DOI verified; replaced Almgren 2005 in R1 (Almgren rejects square-root impact) | SUPPORTS square-root impact as bounding heuristic |

**Overall Phase 0 verdict**: **literature-anchored on the inferential-framework spine** (Components 1c, 4, 6, 7, 8, 9 above) and **practitioner-anchored on the trading-rule spine** (Components 1b, 1d, 2, 3 — Wilder, Connors-Raschke, Bollinger, Nison; all flagged *practitioner*). The §1 "Mechanism" framing is anchored where peer-reviewed sources exist and explicitly flagged as practitioner where they do not. No primary source CONTRADICTS the H055 framing; the round-1 L1 finding that contradicted Almgren 2005 was remediated by replacing with Loeb 1983.

**§15.1 BLOCKING-before-`designed`-freeze condition: SATISFIED** as of 2026-05-06 via the staging-draft 3-round audit-remediate-loop. Pre-reg may proceed to ACCEPT and `designed` freeze.

## 16. Frozen-pre-reg amendment policy

Per [ADR-0013 §"Frozen pre-registration amendment"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): project-level disposition-philosophy ADRs MAY amend §8 + §10 (gate thresholds + decision rule) of frozen `status: designed` pre-registrations WITHOUT requiring a successor hypothesis ID. Other amendments (to §1-§7) require a successor hypothesis ID.

§15.1 erratum-style additions (citation corrections discovered post-`designed` per Phase 0 lit-check) are permitted within the existing hypothesis ID under Path A frozen-pre-reg amendment discipline (matching the H052a §15.1 + H054 §15.1 precedent).

**2026-05-06 amendment** (Path A): §14.1 cross-TF robustness exhibits (informational; not gating) and §12.2 successor cross-links (H056 → H057 → H058 → H059 main chain + H055-CL/MCL/MYM/MGC v2 + H055-event-time parallel tracks) added per ADR-0015 + ADR-0016 + [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md). §1-§7 immutable and preserved verbatim. Decision-log entry at §17.

AI-assistance disclosure per [ICMJE Recommendations January 2026](https://www.icmje.org/recommendations/): the round-1+2+3 audit-remediate-loop on the staging draft used parallel quant-auditor + literature-check sub-agents and a general-purpose remediator; this design.md was authored by a general-purpose Claude Code agent under operator review per the SKIE pseudonym project's AI-assistance policy. Documented in §17 cross-references.

## 17. Decision log + cross-references

- **Pre-reg drafted**: 2026-05-06 (this commit; `status: designed` after staging-draft 3-round ACCEPT).
- **Phase 0 lit-check**: SATISFIED 2026-05-06 via staging-draft Round 1 (L1-001 through L1-014 dispositioned in audit trail).
- **Round-1 audit-remediate-loop on the staging draft**: 31 findings (14 quant + 17 lit); 4 critical, 13 major, 14 minor; all critical/major remediated in-loop; verdict `proceed`. Audit trail: [docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../../../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md).
- **Round-2 audit-remediate-loop**: 19 findings (12 quant + 7 lit); 2 critical, 9 major, 8 minor; all critical/major remediated in-loop; verdict `proceed`.
- **Round-3 audit-remediate-loop**: 9 findings (8 quant + 1 lit); 3 critical, 6 major, 0 minor; verdict `exit-with-residual` per the SKILL.md 3-round cap; round-3 residuals (#1-#3) include the ρ_3 drop, the cadence-sensitivity remark, and the SPA-family-scope conditioning on TPE coverage. All round-3 critical/major findings have inline `# justify:` annotations in this design.md.
- **Status transition**: `status: draft` → `status: designed` 2026-05-06 (this commit; concurrently with [data_requirements.md](data_requirements.md) `status: draft` → `status: designed` per `P1-H055-DATA-REQUIREMENTS-DESIGNED-FREEZE` BLOCKING-before-freeze gate).
- **First production walk-forward**: pending (`P1-H055-PROD-RUN`); BLOCKING-AFTER-`designed`-freeze; gated by §11.2 BLOCKING-BEFORE-LAUNCH prerequisites.
- **Empirical motivation**: pilot ledger [data/external/h055_pilot_ledger/Performance.csv](../../../data/external/h055_pilot_ledger/Performance.csv) covering 2026-05-01 → 2026-05-06 (171 trades, 74.85% win rate, $36.01 expectancy). Note: pilot is OUT-OF-SAMPLE relative to the §2 OOS test fold (which ends 2025-12-{03,19}); pilot is descriptive-only and feeds the §14 advisory adherence audit, not the H_1 inferential family.
- **Companion lit-review**: [lit_review_H055_2026-05-06.md](lit_review_H055_2026-05-06.md) (TBD; produced concurrently with this design.md or as a §15.1 erratum-style addition; non-blocking).
- **Substrate binding**: [data_requirements.md](data_requirements.md) (TBD; produced before `designed` freeze).
- **AI-assistance disclosure**: this design.md was authored by a general-purpose Claude Code agent under operator review; the staging-draft 3-round audit-remediate-loop used parallel quant-auditor + literature-check sub-agents (rounds 1-3) and a general-purpose remediator (rounds 1-2). Per [ICMJE Recommendations January 2026](https://www.icmje.org/recommendations/) AI cannot be an author; AI-assistance use is disclosed; the reproducibility log path is `logs/reproducibility/{run_id}.json` per §11.
- **Successor cross-link**: `P1-H055-V2-WITH-HMM-REGIME-GATE` (HMM regime-gate integration at v3); `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND` (energy + metals + Dow micro extension; phase-2 falsifier for the regime-asymmetry validation).
- **2026-05-06 — Amendment per ADR-0015 + ADR-0016 + [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md)**: added cross-TF robustness exhibits in §14 (new §14.1 with five informational MTF exhibits — confluence score, cross-TF momentum divergence, multi-TF ATR ratio, multi-TF Hurst, daily / session-context); added successor cross-links in §12 (new §12.2 binding H056 → H057 → H058 → H059 main chain + H055-CL/MCL/MYM/MGC v2 + H055-event-time as parallel tracks). §1-§7 (hypothesis statement, universe/sample, features, labels, splitter, cost model) immutable per ADR-0013 frozen-pre-reg amendment policy and **preserved verbatim**. Amendment is **Path A** under ADR-0013 frozen-pre-reg amendment policy (informational exhibits + relationship cross-links only; no change to §1-§7 nor to gate thresholds §8 nor decision rule §10; the §14.1 exhibits are reported as KPI annotations and do not enter the LW2008 strict-CI-dominance H_1 family or the Hansen 2005 SPA family). Cross-link to [ADR-0015](../../../docs/decisions/ADR-0015-component-stacking-master-architecture.md) (component-stacking master architecture) + [ADR-0016](../../../docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md) (sibling-repo audit-and-lift protocol). Concurrent landing with [plan/buildouts/h055_successor_tree_2026-05-06.md](../../../plan/buildouts/h055_successor_tree_2026-05-06.md).
- **2026-05-08 — Amendment per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md)** (survival-constrained optimization paradigm; profit-and-drawdown-primary inference; Sharpe demoted to KPI). §11.1 amended: 8 hard kill-switch constraints K-1..K-8 inherited from ADR-0017 §5 with H055-specific calibrated defaults (per-trade $-stop, per-trade time-stop, no-add-to-loser, per-symbol cap, correlated-instrument cap, daily/weekly circuit breakers, adverse-direction entry filter). §11.1.1 added: drawdown-constrained Kelly sizing primitive per ADR-0017 §4.1 (1% per-trade risk budget, quarter-Kelly cap, current-equity rebasing). §11.2 BLOCKING-BEFORE-LAUNCH preconditions extended: 7 new follow-ups for inferential/sizing primitives (Calmar-differential CI, profit-factor CI, R-multiple CI, risk-of-ruin Monte Carlo, sizing primitive, failure-mode stress test, kill-switch backtest validation). §1-§7 (hypothesis statement, universe/sample, features, labels, splitter, cost model) **preserved verbatim** per ADR-0013 frozen-pre-reg amendment §1-§7 immutability discipline. Amendment is **Path A** under ADR-0013 (the §1 T_H055_class statistic is preserved verbatim as a secondary KPI; the load-bearing operator-review artifact at §8+§10 promotion-decision-rule layer is reframed to the ADR-0017 §1 survival-constrained metric vector — terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean). The empirical motivation is the operator pilot ledger 2026-05-01 → 2026-05-07 (the 2026-05-08 226-trade extension processed in-context but NOT committed to the public repo per the user 2026-05-08 directive on identity-hygiene; SHA256 provenance recorded under `P1-ADR-0017-PILOT-LEDGER-V2-NON-COMMIT-PROVENANCE`). Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-08_adr-0017-survival-constrained-paradigm.md](../../../docs/audits/audit_trail_2026-05-08_adr-0017-survival-constrained-paradigm.md).
