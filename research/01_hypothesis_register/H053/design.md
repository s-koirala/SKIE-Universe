---
name: H053 — Multi-timeframe 09:45→10:30 ET ES/NQ regression with opening-bar mediation and a categorical bias-target-probability table
description: Pre-registered design doc for hypothesis H053
type: project
hypothesis_id: H053
tier: 2b
status: designed
owner: skoir
created: 2026-04-28
citations:
  - ADR-0003-spa-vs-romanowolf
  - ADR-0004-alpha-and-power-defaults
  - ADR-0007-stacked-embargo
  - ADR-0008-spa-omega
  - ADR-0009-blas-thread-pinning
  - Andersen-Bollerslev 1998 (doi:10.2307/2527343)
  - Andersen-Bollerslev-Diebold-Labys 2003 (doi:10.1111/1468-0262.00418)
  - Heston-Korajczyk-Sadka 2010 (doi:10.1111/j.1540-6261.2010.01573.x)
  - Lou-Polk-Skouras 2019 (doi:10.1016/j.jfineco.2019.03.011)
  - Chernozhukov-Chetverikov-Demirer-Duflo-Hansen-Newey-Robins 2018 (doi:10.1111/ectj.12097)
  - Cochran 1954 (doi:10.2307/3001616)
  - Almgren-Chriss 2001 (J Risk 3(2):5-39)
  - Bailey-Lopez-de-Prado 2014 (doi:10.3905/jpm.2014.40.5.094)
  - Imai-Keele-Tingley 2010 (doi:10.1037/a0020761)
  - Imai-Keele-Yamamoto 2010 (doi:10.1214/10-STS321)
  - VanderWeele 2015 Explanation in Causal Inference (OUP, ISBN 978-0199325870)
  - VanderWeele-Ding 2017 (doi:10.7326/M16-2607)
  - Lo 2002 (doi:10.2469/faj.v58.n4.2453)
  - Opdyke 2007 (doi:10.1057/palgrave.jam.2250084)
  - Ledoit-Wolf 2008 (doi:10.1016/j.jempfin.2008.03.002)
  - Hansen 2005 (doi:10.1198/073500105000000063)
  - Politis-White 2004 (doi:10.1081/ETC-120028836)
  - Patton-Politis-White 2009 (doi:10.1080/07474930802459016)
  - de Prado 2018 Advances in Financial Machine Learning (Wiley, ISBN 978-1119482086)
  - Bergstra-Bengio 2012 JMLR 13:281-305
  - Zou-Hastie 2005 (doi:10.1111/j.1467-9868.2005.00503.x)
  - Friedman 2001 (doi:10.1214/aos/1013203451)
  - Garman-Klass 1980 (doi:10.1086/296072)
  - Parkinson 1980 (doi:10.1086/296071)
  - Yang-Zhang 2000 (doi:10.1086/209650)
  - Lee-Ready 1991 (doi:10.1111/j.1540-6261.1991.tb02683.x)
  - Niculescu-Mizil-Caruana 2005 (doi:10.1145/1102351.1102430)
  - Brier 1950 (doi:10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2)
---

# H053 — Multi-timeframe 09:45→10:30 ET regression with opening-bar mediation

Pre-registration for hypothesis H053. Frozen at `designed` on 2026-04-28. Companion: [lit_review_H053_2026-04-28.md](lit_review_H053_2026-04-28.md). Any change requires a successor hypothesis ID.

## 1. Hypothesis

**Predictand.** For each session `t` and instrument `i ∈ {ES, NQ}` on the front-month roll-adjusted continuous series, define
```
y_{i,t} = log( C_i(10:30 ET, t) ) − log( C_i(09:45 ET, t) )
```
where `C_i(τ, t)` is the close of the 1-min bar ending at clock time `τ` in `America/New_York` on session `t`. `y_{i,t}` is a fixed-clock-time, fixed-horizon log return over the 09:45–10:30 ET window (three 15-min candles; equivalent to 08:45–09:30 CST). The categorical secondary outcome is `d_{i,t} = sign(y_{i,t})` with tie-break rule pre-registered in §4.

**Predictor `X_{i,t}`.** A snapshot at 09:45 ET on session `t` of three chart timeframes, defined in §3:
- daily bars covering ≥ 60 trading sessions prior (`as_of = T−1 close`);
- hourly bars covering ≥ 5 sessions prior (24/7 ETH+RTH consolidated);
- 5- and 15-min bars covering 24–48 hours prior (24/7).

**Candidate mediator `M_{i,t}`.** A vector of summary statistics of the 09:30–09:45 ET opening 15-min bar (the *first* 15-min RTH candle): return, log-range (Garman-Klass), volume, and OFI tick-rule proxy. `as_of(M_{i,t}) = 09:45 ET` exactly.

**Estimands.**
- `TCE` = total causal effect of `X` on `y` under do-intervention on `X` (per VanderWeele 2015 Ch. 2).
- `NDE` = natural direct effect (`X → y` not through `M`).
- `NIE` = natural indirect effect (`X → M → y`).
- Sharpe-differential `T_H053^{(arm)} = SR_strategy^{(arm)} − SR_benchmark` for each model arm; primary benchmark = a passive long held 09:45–10:30 ET RTH-only on the same instrument.

**H0 / H1 (primary, gating).** Per ADR-0003 and ADR-0004:
- H0: For each model arm `a ∈ {elasticnet, lightgbm, llm}`, `T_H053^{(a)} ≤ 0` on the OOS test fold.
- H1: `T_H053^{(a)} > 0`; one-sided test at α = 0.05.
- Primary inference: paired Ledoit-Wolf 2008 studentized circular-block bootstrap on session-by-session net-of-cost return differentials; HAC variance per Newey-West with bandwidth selected by Politis-White 2004 (PPW 2009 corrected) optimal block length on the differential series. Family enters Hansen SPA per ADR-0003 / ADR-0008.

**H0 / H1 (secondary, descriptive — NOT gating).** Per Imai-Keele-Tingley 2010:
- H0_NIE: `NIE = 0` on the OOS test fold.
- H0_NDE: `NDE = 0` on the OOS test fold.
- Inference: paired stationary-bootstrap percentile CIs on `âb̂` (NIE) and `ĉ′` (NDE) per the parametric mediation model in §5; sensitivity-analysis E-value per VanderWeele-Ding 2017.

**Critical interpretive note.** The mediation framework requires sequential ignorability and SUTVA (Imai-Keele-Yamamoto 2010). In a 1-min-bar futures series with serial dependence, opening-window order flow, and unobserved overnight news, those assumptions are heroic. **The mediation block is descriptive decomposition, not causal-identification.** A statistically significant `NIE` is not evidence that the opening bar *causes* the post-09:45 ET return; it is evidence that predictability flowing through the opening bar is non-zero in our walk-forward sample. The decision rule in §10 reflects this: a Sharpe-null with a significant mediation result archives `null, descriptive-mediation-only`, not `positive`.

**Mechanism.** The 09:30–09:45 ET opening 15-min bar concentrates overnight information, gap dynamics, and order-flow imbalance into a single observed object ([Lou, Polk & Skouras 2019, JFE 134(1):192–213](https://doi.org/10.1016/j.jfineco.2019.03.011); [Andersen, Bollerslev, Diebold & Labys 2003, Econometrica 71(2):579–625](https://doi.org/10.1111/1468-0262.00418); [Heston, Korajczyk & Sadka 2010, J Finance 65(4):1369–1407](https://doi.org/10.1111/j.1540-6261.2010.01573.x)). Higher-timeframe state (daily trend, hourly path) constrains how that information is priced over the next 45 minutes. H053 tests whether (a) higher-timeframe context predicts the 09:45–10:30 ET return, (b) the predictability is mediated by the opening-bar features, and (c) the joint signal supports a positive Sharpe-differential against a passive-long benchmark net of NT8-realistic costs.

**Primary citations.** [Lou, Polk & Skouras 2019](https://doi.org/10.1016/j.jfineco.2019.03.011); [Heston, Korajczyk & Sadka 2010](https://doi.org/10.1111/j.1540-6261.2010.01573.x); [Andersen & Bollerslev 1998](https://doi.org/10.2307/2527343); [Imai, Keele & Tingley 2010](https://doi.org/10.1037/a0020761); [Imai, Keele & Yamamoto 2010](https://doi.org/10.1214/10-STS321); VanderWeele 2015 (OUP, ISBN 978-0199325870); [VanderWeele & Ding 2017](https://doi.org/10.7326/M16-2607); [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453); [Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002); [Hansen 2005](https://doi.org/10.1198/073500105000000063); de Prado 2018 (Wiley, ISBN 978-1119482086).

**Test statistic.** `T_H053^{(arm)}` enters the project's Hansen SPA universe per ADR-0003 / ADR-0008 alongside H050/H051/H052a/H052b. Three slots (Arm 1, Arm 2, Arm 3) are pre-registered ex ante; arms whose §11 prerequisites fail to land before `running` consume their slot as `archive(null, prerequisite-not-met)` per §8, preserving family size at exactly 3.

## 2. Universe and sample period

- **Instruments.** ES (primary), NQ (primary). Micros MES, MNQ as robustness exhibits — linear price-rescaled versions of the majors per ADR-0001 capacity ceiling mapping; any apparent ES↔MES (or NQ↔MNQ) divergence reflects instrument-specific microstructure rather than alpha. The user-facing categorical table (§4.5) is presented per-instrument; the SPA-gating `T_H053` pools ES + NQ with instrument-dummy stratification (per H052a §6).
- **Frequency.** 1-min bars (base grid). Hourly and daily features are derived by aggregation; 5/15-min features are derived by resampling.
- **Session.** Predictand RTH-only (09:45–10:30 ET, `America/New_York`) per [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py). Features from the hourly and 5/15-min blocks consume 24/7 ETH+RTH bars; this is explicit, not a leak. Every feature row carries an `as_of` timestamp ≤ 09:45 ET t=0 (see §3).
- **Sample window.**
  - IS: 2015-01-01 → 2022-12-31.
  - Validation: 2023-01-01 → 2023-12-31 (inner walk-forward folds).
  - OOS / test: 2024-01-01 → 2025-12-{03 ES, 19 NQ} per the post-Cell-I substrate envelope recorded in [CLAUDE.md](../../../CLAUDE.md) §Implemented infrastructure 2026-04-23 and pinned in [data_requirements_H053_2026-04-28.md](data_requirements_H053_2026-04-28.md) §Coverage. NQ right edge is 2025-12-19 under left-closed-right-open semantics with the Z-window `('Z', '09-15', '12-20')`; the design cites the bar-timestamp value (19), not the Z-window upper bound (20).
- **Roll treatment.** `vendor_legacy_1min_roll_adjusted` (Cycle-1 deliverable, ratio-adjusted, volume-crossover roll) per [config/instruments.yaml](../../../config/instruments.yaml). **Runs on raw `vendor_legacy_1min` are forbidden by this pre-reg; raw-data results are diagnostic-only and cannot promote H053 past `running`** (mirrors H052a §2 hard prohibition).
- **Dataset snapshot frozen at pre-registration.** SHA256 of the roll-adjusted parquet pinned in the companion [data_requirements_H053_2026-04-28.md](data_requirements_H053_2026-04-28.md) at `designed` status (this date), and re-asserted at the first `running` run with a hard-fail check at **partition-level granularity**: `dataset_checksums_running` must equal `dataset_checksums_designed` for the combined frame **and** every per-partition row in the binding table; mismatch → `archive(null, data-violation)` per §10.1.1. Partition-level granularity catches partial re-ingest issues earlier than combined-frame-only would; both are bound consistently across this design and the companion. Pattern mirrors H050 post-Cell-I atomic re-freeze (commit `029f85d`).

## 3. Features

All features computed at point-in-time `as_of` ≤ 09:45 ET t=0; mediator features `as_of = 09:45 ET` exactly under the bar-edge convention in §3.0. Leakage tests per implementation-plan §3 and §4.6, and the dual-fit-call observer / monotonicity canary from Cycle-4 must pass; the canaries are wired specifically on the H053 feature factory (§11 prerequisite 11).

### 3.0 Bar-edge convention (binding)

This subsection pins the wall-clock semantics that the §1 predictand definition and the §3.4 mediator depend on. Without it the boundary timestamps are ambiguous and admit a latent same-bar leak.

- **Bar timestamp policy.** Every 1-min bar carries a single timestamp equal to the *end* of the bar. A bar with timestamp `09:45 ET` covers trades in the half-open interval `[09:44 ET, 09:45 ET)`. Intervals are **left-closed-right-open** on `America/New_York` wall-clock (per [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py)).
- **Mediator-window bar set.** The mediator window 09:30–09:45 ET consists of exactly the 15 bars with timestamps `{09:31, 09:32, …, 09:45 ET}`. The `09:45 ET` bar is the *last* bar of the mediator window.
- **Predictand-window bar set.** The predictand window 09:45–10:30 ET consists of exactly the 45 bars with timestamps `{09:46, 09:47, …, 10:30 ET}`. The `09:45 ET` bar is **excluded** from the predictand window.
- **Predictand left-endpoint reference.** `C_i(09:45 ET, t)` denotes the close of the `09:45 ET`-timestamped bar. This single scalar is shared between the §1 predictand definition (as `y`'s left endpoint) and the §3.4 mediator (as `m_return`'s right endpoint). The shared scalar is unavoidable without redefining the windows; it is *not* a feature consuming a future bar — it is a clock-time anchor.
- **Mediator-open notation shorthand.** When the mediator block (§3.4) and the §1 mechanism paragraph use `O_{09:30}`, this is shorthand for the open of the 09:31 ET-timestamped bar — the first trade in the `[09:30, 09:31)` interval and the first bar of the mediator window. There is no 09:30 ET-timestamped bar in the convention; the shorthand is retained for readability across the design and the lit-review.
- **Disjoint bar sets.** Predictand and feature row sets are bar-set-disjoint: features (including mediator) consume bars with timestamp ≤ `09:45 ET`; predictand consumes bars with timestamp > `09:45 ET` up to and including `10:30 ET`. The shared `C_i(09:45 ET, t)` scalar appears as a *boundary anchor*, not as an input to any model fit.
- **Unit-test gate (§11 prerequisite 11).** A unit test asserts (a) feature bar set ∩ predictand bar set = ∅; (b) the predictand reads no bar with timestamp ≤ `09:45 ET` other than via the explicit boundary anchor `C_i(09:45 ET, t)`; (c) the dual-fit-call observer + `TracingArray` capability proxy from [docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md](../../../docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md) is wired on the H053 feature factory.

### 3.1 Block A — Daily-timeframe (`as_of = T−1 close`)

- `log_close_minus_sma50` — `log(C_{T−1} / SMA_{50, T−1})`.
- `log_close_minus_sma200` — `log(C_{T−1} / SMA_{200, T−1})`.
- `daily_realized_range_n` — N-day rolling Garman-Klass log-range estimator per [Garman & Klass 1980, *Journal of Business* 53(1):67–78](https://doi.org/10.1086/296072) and [Parkinson 1980, *Journal of Business* 53(1):61–65](https://doi.org/10.1086/296071); N selected by training-fold CV from `{20, 60, 120}`.
- `weekly_trend_slope` — rolling OLS log-price slope over the prior 5 sessions; sign-only signal kept and slope retained.
- `daily_yz_vol` — Yang-Zhang volatility per [Yang & Zhang 2000, *Journal of Business* 73(3):477–491](https://doi.org/10.1086/209650), already implemented in the project.

### 3.2 Block B — Hourly-timeframe (24/7, prior several days)

- `hourly_returns_lag_k` — log-returns at hourly resolution for `k ∈ {1, 2, …, 24}` lags counted backward from 09:00 ET t=0; ETH+RTH consolidated.
- `prior_session_vwap_dev` — `log( C_{T−1, 16:00 ET} / VWAP_{T−1, RTH} )`.
- `overnight_return` — `log( O_{09:30 ET, t} / C_{16:00 ET, T−1} )`.
- `pre_open_return` — `log( O_{09:30 ET, t} / O_{06:00 ET, t} )` over the 06:00–09:29 ET ETH window.

### 3.3 Block C — 5- and 15-minute features (24–48h, `as_of ≤ 09:45 ET`)

- `rv_realized_5m` — squared-returns realized variance per [Andersen & Bollerslev 1998, *International Economic Review* 39(4):885–905](https://doi.org/10.2307/2527343), 5-min bars over the prior 24h.
- `rv_parkinson_5m` — Parkinson estimator over the same window.
- `realized_skew_5m` — third standardized central moment.
- `ofi_tickrule_5m` — order-flow-imbalance proxy via tick-rule sign classification per [Lee & Ready 1991, *Journal of Finance* 46(2):733–746](https://doi.org/10.1111/j.1540-6261.1991.tb02683.x); pending the project's MBP-10 substrate, the tick-rule proxy is the load-bearing version (UNVERIFIED on Cont-Kukanov-Stoikov 2014 OFI primary DOI; the tick-rule sign classification is the verified primitive). When MBP-10 substrate lands (project follow-up `P1-MBP10-INGEST-LANDED`), an addendum to this design will swap `ofi_tickrule_*` → `ofi_cks_*` and re-run the OOS fold; the swap is pre-registered as a sensitivity exhibit, not as a re-promotion of the design.
- `range_z_15m` — standardized 15-min range over the prior 24h, training-fold mean/SD.
- `volume_z_15m` — standardized 15-min volume over the prior 24h, training-fold mean/SD.

### 3.4 Block D — Mediator block (`as_of = 09:45 ET`)

Computed only from bars with timestamp ∈ {09:31, 09:32, …, 09:45 ET} per §3.0. The mediator vector `M_{i,t}`:

- `m_return` — `log( C_{09:45} / O_{09:30} )` where `O_{09:30}` is the open of the 09:31 ET bar (first mediator-window bar) and `C_{09:45}` is the close of the 09:45 ET bar (last mediator-window bar; also the predictand's boundary anchor per §3.0).
- `m_log_range` — Garman-Klass log-range over the 15 mediator-window bars.
- `m_volume` — total contract volume summed over the 15 mediator-window bars.
- `m_ofi_tickrule` — OFI proxy summed over the 15 mediator-window bars.

PIT property tests assert that (a) no row of `M` references any 1-min bar with timestamp > 09:45 ET on the same session, and (b) the bar-set disjointness in §3.0 holds for the mediator block specifically.

### 3.5 Block E — Image features (Tier-3, LLM-arm only; conditional on §11 prerequisites)

- PNG renders of three timeframe charts (daily, hourly, 5/15-min) at fixed style: matplotlib backend version pinned, font path pinned, DPI = 100, axis-tick formatter deterministic, no axis-text reflow across runs. Each render's SHA256 is logged into `ReproLog.image_render_hashes`.
- Encoded as base64 attachments in the LLM prompt; consumed only by the LLM arm (§5.3). The ElasticNet (§5.1) and LightGBM (§5.2) arms ignore this block.
- Image features are dropped from Arm 3's input set if §11.4 prerequisite 7 (LLM-arm deterministic-replay scaffolding) does not land before `running`; the Arm-3 SPA slot is still consumed as `archive(null, prerequisite-not-met)` per §8 — image-feature absence does not exempt the slot.
- Image-render hardware scope per §11.3 (same machine, same conda env hash; cross-OS / cross-Python-minor-version determinism not guaranteed).

### 3.6 PIT and leakage assertions

- Every feature row in Blocks A/B/C carries `as_of` ∈ bar timestamps `≤ 09:45 ET` strictly *before* the mediator-window-last bar; mediator block rows carry `as_of = 09:45 ET` per §3.0.
- The Cycle-4 dual-fit-call observer + `TracingArray` capability proxy (per project [docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md](../../../docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md)) is wired on the H053 feature factory; §11 prerequisite 11 binds the wiring.
- A leakage unit test asserts (a) bar-set disjointness per §3.0, and (b) the boundary-anchor `C_i(09:45 ET, t)` is the only scalar shared between feature and predictand input streams.

## 4. Label construction

### 4.1 Primary label

Fixed-clock-time, fixed-horizon log return:
```
y_{i,t} = log( C_i(10:30 ET, t) ) − log( C_i(09:45 ET, t) )
```
This is **not** a triple-barrier label. Justification: the predictand is a deterministic 45-min clock window with no path-dependent exit; PT/SL/`vertical_barrier` grids would all be degenerate (the time barrier dominates by construction). H053 is therefore label-incomparable with H050/H051/H052a/H052b — the SPA family treats `T_H053` as a paired-differential statistic against a passive-long benchmark, not as a triple-barrier-derived Sharpe.

### 4.2 Secondary label

Directional sign with explicit tie-break:
```
d_{i,t} =  +1     if y_{i,t} >  +ε
           0     if |y_{i,t}| ≤ ε         (tie, dropped from the directional arm)
          -1     if y_{i,t} < −ε
```
- `ε` = 0.5 × tick-equivalent log return computed as `log(1 + 0.5 · tick_size / median_mid_price_IS)`, where `median_mid_price_IS` is the median front-month roll-adjusted mid-price over the IS fold (2015-01-01 → 2022-12-31), per-instrument. **Pinned ONCE at the start of `running`** using the median over the full IS window per instrument; held constant across all inner walk-forward training folds, validation, and OOS test. Persisted to `ReproLog.tied_row_epsilon_{ES, NQ}`.
- Sensitivity exhibit (not gating): per-WF-fold re-pinned ε reported alongside the one-shot pin; if directional dispositions diverge, annotate `epsilon-pin-sensitive` per §10.2.
- A diagnostic gate asserts the per-fold tied-row rate stays within ±2σ of the IS-fold rate; violations are flagged in the run summary, not blocking. This addresses the price-drift sensitivity of a mid-price-relative ε across 2015–2025 (ES went from ~2000 to ~5000+; tick is constant 0.25).
- Tied rows are excluded from the directional classifier and reported as their own count in the run summary.

### 4.3 Tertiary (volatility-normalized) label

```
z_{i,t} = y_{i,t} / σ̂_{train, i}
```
where `σ̂_{train, i}` is the training-fold realized standard deviation of `y_{i,t}` over the IS window. Used for cross-instrument pooling and as a robustness exhibit; not a primary or secondary gate target.

### 4.4 Splitter horizons

- `purge` = 45 min (the predictand horizon) per [de Prado 2018](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) §7.4.
- Mediator window = 15 min, lies entirely *before* the predictand window — no purge interaction.

### 4.5 User-facing categorical bias-target-probability table (the table deliverable)

The headline output of H053 is a per-instrument lookup table whose rows are pre-registered opening-15-min-candle archetypes and whose entries are calibrated conditional empirical frequencies for the 09:45–10:30 ET window. Schematically:

| Opening-15-min archetype `A_k` | Directional bias | Target zone | Probability |
| --- | --- | --- | --- |
| `bearish_engulf` | continuation down | quantile band on `C_{09:45} − k_σ · σ̂` | `P̂(d=−1, target_hit | A_k)` ± CI |
| `indecision_doji` | breakdown after balance | similar | similar |
| ... five rows total | ... | ... | ... |

The user's example numeric MNQ levels (27,000 / 26,730–26,800 / etc.) are illustrative for table layout only; **they are not pre-registered as fixed numbers.** What is pre-registered is the *algorithm* that constructs the table on each walk-forward fold:

#### 4.5.1 Archetype categorization

- The opening-15-min-candle feature vector `M_{i,t}` from §3.4 is partitioned into `K` mutually-exclusive archetypes using a deterministic rule on training-fold quantiles. The rule is:
  1. Sign of `m_return`: positive vs negative.
  2. Quintile of `|m_return| / σ̂_{15min, train}`: small / medium / large.
  3. Quintile of `m_log_range / σ̂_{range, train}`: narrow / wide.
  4. Sign of `m_ofi_tickrule`: buy-imbalanced vs sell-imbalanced vs balanced (tick-rule null-band).
- `K` is **CV-tuned**, not magic. Selection: `K ∈ {3, 5, 7, 9}`, criterion = mean OOS Brier score on the inner walk-forward folds of the training window; ties broken by smaller `K` (parsimony). Per-fold `K` selection is persisted to `ReproLog.archetype_K_selection_{run_id}.json`. The user's example 5-row table is illustrative for layout, not a binding `K`.
- The cross-product of the four axes is collapsed to the selected `K` by aggregating sparse cells into the nearest non-sparse cell. Cell-count threshold for non-sparseness: `N_min = max(30, n_min_chi2)` where `n_min_chi2` is the [Cochran 1954, *Biometrics* 10(4):417–451](https://doi.org/10.2307/3001616) expected-cell-count rule (≥5 expected count for ≥80% of cells; ≥1 for all cells), evaluated on the training-fold marginal frequencies. The "30" floor is empirical (>200 sessions → ≥5% prevalence per cell at K=5); the chi-square anchor binds the inferential validity of the conditional empirical-frequency CIs reported in §4.5.3. (Note: prior draft cited ADR-0005 `dim ≥ 30 · n_states` for this floor — that rule is for HMM Gaussian-emission identifiability and was misapplied; corrected per Round-1 quant-auditor finding.)
- Archetype display labels (`bearish_engulf`, `indecision_doji`, `bullish_spike_midrange`, `strong_bullish_close`, `gap_fill_reversal` for the `K = 5` case; analogous labels generated for other `K`) are **post-hoc display strings**; the binding pre-reg is the rule above plus the per-fold quantile thresholds, persisted to `ReproLog.archetype_thresholds_{run_id}.json`.

#### 4.5.2 Target zones

For each archetype `A_k`, the target zone is two quantile bands of the forward 45-min log-return distribution conditional on `A_k`, estimated on the training fold:
- `target_lo_k = quantile(y | A_k, q=0.25)`
- `target_hi_k = quantile(y | A_k, q=0.75)`

Re-expressed in price terms at run-time via `target_band_k = C_{09:45} · exp(target_{lo|hi}_k)`. The price band is therefore time-varying and instrument-specific; only the conditional return-distribution quantile rule is pre-registered.

#### 4.5.3 Probability cells

For each archetype `A_k`, three conditional empirical frequencies are reported with paired stationary-bootstrap percentile CIs (block length per Politis-White 2004, PPW 2009 corrected):
- `P̂(d=+1 | A_k)` — probability of a positive 09:45→10:30 ET return given archetype.
- `P̂(d=-1 | A_k)` — probability of a negative return.
- `P̂(target_hit | A_k)` — probability that `y_{i,t}` falls inside the conditional target zone (between `target_lo_k` and `target_hi_k`).

Calibration is via held-out CV-fold isotonic regression per [Niculescu-Mizil & Caruana 2005, ICML](https://doi.org/10.1145/1102351.1102430), fitted **per-arm** and **globally across archetypes** (one isotonic curve per arm; archetype is a stratification axis for diagnostic plots only, not a separate calibration surface). Sample-size precondition: `N_cal ≥ 500 sessions per arm` after purge + ADR-0007 stacked embargo (loose anchor on Niculescu-Mizil & Caruana 2005 §3 isotonic-regression sample-size simulations, where ~1000 samples is the dominance regime over Platt; 500 is a relaxed lower bound for futures-session cadence; empirical recalibration via training-fold synthetic Bernoulli coverage at `N ∈ {200, 300, 500, 1000}` is tracked under follow-up `P1-H053-NCAL-EMPIRICAL`); if `N_cal < 500`, fall back to Platt scaling per Platt 1999 with the choice persisted to `ReproLog.calibration_method`. Calibration quality is reported on the OOS fold via Brier score and reliability decomposition per [Brier 1950](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2) and [Murphy 1973, *Journal of Applied Meteorology* 12(4):595–600](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2). A Brier-skill-score threshold of `BSS > 0` against a climatological per-instrument prior is a *secondary* gating condition for the table deliverable (see §10).

#### 4.5.4 Multiple-testing inside the table

The table reports `K × 3` probability cells (5 archetypes × 3 cells) plus the target-zone interval. Per-cell p-values are not reported; instead, the table is evaluated *jointly* via the Brier score and reliability decomposition. This avoids cell-level false-discovery inflation — the user reads the table as one calibrated object, not as 15 independent tests.

## 5. Estimator

Three model arms, each producing a row-level prediction that is then consumed by (a) the Sharpe-differential gate in §8 and (b) the categorical-table calibration pipeline in §4.5.

### 5.1 Arm 1 — ElasticNet (penalised linear)

- Implementation: [Zou & Hastie 2005, *JRSS-B* 67(2):301–320](https://doi.org/10.1111/j.1467-9868.2005.00503.x). Standardize features by training-fold mean/SD; predict `y_{i,t}` (regression) and `d_{i,t}` (logistic with the same penalty grid).
- Hyperparameter grid: `alpha ∈ {1e-4, 1e-3, 1e-2, 1e-1, 1.0}`, `l1_ratio ∈ {0.1, 0.5, 0.9}`.
- Loss: MSE for the regression target; logistic for the directional classifier.
- Search protocol: nested walk-forward random search per [Bergstra & Bengio 2012, *JMLR* 13:281–305](https://www.jmlr.org/papers/v13/bergstra12a.html), `N_draws = 200`, fixed seed (§11).

### 5.2 Arm 2 — LightGBM (GBM)

- Implementation: [Friedman 2001, *Annals of Statistics* 29(5):1189–1232](https://doi.org/10.1214/aos/1013203451). LightGBM (Ke et al. 2017, NeurIPS) is the project's GBM library; same as H050.
- Hyperparameter grid (mirrors H050 §5): `num_leaves ∈ {15, 31, 63}`, `learning_rate ∈ {0.01, 0.05}`, `min_data_in_leaf ∈ {20, 50}`, `n_estimators` early-stopped on the validation fold (max 2000, patience 50).
- Loss: regression L2 for `y_{i,t}`; logistic for `d_{i,t}`.
- Search protocol: nested walk-forward random search, `N_draws = 200`.
- Probability calibration for the categorical-table arm: isotonic regression on a held-out CV fold per Niculescu-Mizil & Caruana 2005.

### 5.3 Arm 3 — LLM-with-context (Tier-3, conditional)

- Implementation: open-weights model (FinGPT-class or general-purpose pinned by hash) under a documented prompt template. Numeric chart state is encoded as text; image features (§3.5) are attached as base64.
- Prompt selection: data-driven per [~/.claude/CLAUDE.md §Parameter & Prompt Selection](../../../../.claude/CLAUDE.md). DSPy-style prompt-search ([Khattab et al. 2023, arXiv:2310.03714](https://arxiv.org/abs/2310.03714)) on the training fold is the pre-registered method; hand-tuned prompts are forbidden once the LLM arm has been used >5 times. (GEPA UNVERIFIED — flagged in [lit_review_H053_2026-04-28.md](lit_review_H053_2026-04-28.md) §F; if the lit-check audit can pin a primary identifier, GEPA may be added; otherwise DSPy alone.)
- Determinism (binding):
  - temperature = 0; seed pinned; KV-cache disabled across rows.
  - `torch.use_deterministic_algorithms(True)` + `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
  - CUDA version pinned in `ReproLog.cuda_version`; GPU model pinned in `ReproLog.gpu_model`; CPU/GPU-only fallback path documented for replay environments without the same hardware.
  - Tokenizer version + model weight SHA256 recorded into `ReproLog.llm_arm`.
  - Replay check uses **bit-identical logit tensors at top-1 token** across two consecutive runs on the pinned hardware target. If bit-identical fails on the same hardware, Arm 3 enters as `archive(null, prerequisite-not-met)` per §8 (no degraded-determinism fallback is admissible for SPA-family entry).
  - Hardware target documented as a §11.3 reproducibility commitment, not a soft expectation.
  - Prompt-search method persisted to `ReproLog.prompt_search_method ∈ {dspy_only, dspy_plus_gepa, fallback_handtuned}` at run start, bound by §11.2 item 13 lit-check outcome on GEPA. `fallback_handtuned` admissible only if the LLM arm has been used ≤ 5 times project-wide per [~/.claude/CLAUDE.md §Parameter & Prompt Selection](../../../../.claude/CLAUDE.md).
- **Tier flag.** If the LLM-arm deterministic-replay scaffolding does not land before `running` (see §11 prerequisite 7), Arm 3 is recorded as `archive(null, prerequisite-not-met)` and the SPA slot is consumed by that null record (per §8 family-entry rule). Adding Arm 3 post-hoc would inflate the family and bias the omega correction per ADR-0008; dropping Arm 3 ex post would also bias the family by selecting on prerequisite-completion. Pre-registering the slot and consuming it as a null on prerequisite failure preserves the family size at exactly 3.

### 5.4 Mediation estimator (descriptive, NOT gating)

- **Treatment scalarization with fold-disjoint protocol.** The treatment `X` is high-dimensional. To make Imai-Keele-Tingley 2010 / VanderWeele 2015 estimands well-defined under non-circular estimation, the scalarization and the mediation regressions are estimated on **disjoint sub-folds** within each walk-forward training window:
  1. Within each walk-forward training window, partition along the time axis into `S` (scalarization sub-fold, ≈50%) and `Med` (mediation sub-fold, ≈50%), with an embargo between them per [ADR-0007](../../../docs/decisions/ADR-0007-stacked-embargo.md).
  2. Fit Arm-1 ElasticNet on `S` using Block A + Block B + Block C features only (mediator block excluded) to produce the scalarization model `f_S`.
  3. Compute `X̂_{i,t} = f_S(features_{A+B+C, i,t})` on `Med` rows and on the OOS test fold using the `S`-fitted model only — `f_S` is frozen across `Med` and OOS.
  4. Estimate the two-equation mediation regressions on `Med` rows; the bootstrap (below) resamples `Med` rows only.
  5. The cross-fitted DML alternative ([Chernozhukov, Chetverikov, Demirer, Duflo, Hansen, Newey & Robins 2018, *Econometrics Journal* 21:C1–C68](https://doi.org/10.1111/ectj.12097)) is pre-registered as a sensitivity exhibit; the primary estimator is the fold-disjoint protocol above.
- Two-equation parametric mediation per [Baron & Kenny 1986](https://doi.org/10.1037/0022-3514.51.6.1173) / VanderWeele 2015 Ch. 2 (estimated on `Med`):
  1. `M_{i,t} = α₀ + a · X̂_{i,t} + ε_M`
  2. `y_{i,t} = β₀ + c′ · X̂_{i,t} + b · M_{i,t} + ε_y`
- Estimands:
  - `NIE = â · b̂` (indirect effect, product-of-coefficients form per [MacKinnon, Lockwood, Hoffman, West & Sheets 2002, *Psychological Methods* 7(1):83–104](https://doi.org/10.1037/1082-989X.7.1.83)).
  - `NDE = ĉ′` (direct effect).
- **Inference (primary).** Paired-pairs (rows-of-`(X̂, M, y)`) stationary bootstrap on `Med` rows, B = 1000 replicates, single shared block length per Politis-White 2004 (PPW 2009 corrected). Per-replicate refit of both equations on the resampled rows. The shared block length and the paired-pairs scheme are pre-registered to remain valid under residual heteroskedasticity and serial correlation; residual-based bootstrap is reported as a sensitivity exhibit only ([MacKinnon, Lockwood & Williams 2004, *Multivariate Behavioral Research* 39(1):99–128](https://doi.org/10.1207/s15327906mbr3901_4); Davison & Hinkley 1997 *Bootstrap Methods and their Application*, Cambridge UP, ISBN 978-0521574716).
- **Sensitivity.** E-value per [VanderWeele & Ding 2017](https://doi.org/10.7326/M16-2607) on the NIE point estimate against unmeasured mediator-outcome confounding; Imai-Keele-Yamamoto 2010 ρ-sensitivity reported alongside.
- **Multivariate mediator collapse.** `M_{i,t}` is summarized as a single scalar `M̂` = first principal component of standardized mediator vector on the `S` sub-fold (rotation persisted to `ReproLog.mediation_pca_rotation`). PC1 variance-explained ratio is reported in `ReproLog.mediation_pc1_var_explained` per fold; if PC1 explains < 50% of total variance on any fold, the per-coordinate robustness exhibit (one mediator coordinate at a time) is promoted from secondary to a co-primary diagnostic for that fold. The 50% threshold is a practitioner default (Jolliffe 2002 *Principal Component Analysis* 2nd ed §6.1.1, Springer, ISBN 978-0387954424; Cattell 1966 scree-test heuristic); empirical recalibration via training-fold synthetic-null mediator-block coverage at thresholds `{0.5, 0.7, 0.8, 0.9}` is tracked under follow-up `P1-H053-PC1-THRESHOLD-EMPIRICAL`.
- HAC SE per Newey-West with bandwidth from [src/skie_ninja/inference/stats/](../../../src/skie_ninja/inference/stats/), reported in addition to the bootstrap CI.
- **Coverage gate (synthetic-null prerequisite, §11 prerequisite 3).** The mediation estimator passes the `designed → running` gate only after a synthetic-null Monte-Carlo coverage test confirms the rejection rate at α=0.05 covers nominal under H0_NIE under known generative parameters with serial-dependent residuals.

### 5.5 Cross-instrument pooling

ES and NQ returns are highly correlated (ρ > 0.85 on 1-min bars per H052a §6). Concrete operationalization for H053:

- **Arms 1 and 2 (ElasticNet, LightGBM):** a single binary instrument indicator (`is_NQ ∈ {0, 1}`; ES = 0, NQ = 1) is concatenated to the feature vector. One pooled model is fitted on the stacked ES+NQ rows; coefficients are shared across instruments other than via the indicator.
- **Arm 3 (LLM):** the instrument symbol (`"ES"` or `"NQ"`) is included in the system message; one prompt-search and one set of LLM weights serves both instruments.
- **Sharpe gate.** Inference at the SPA level uses the pooled-strata return series with HAC-paired-bootstrap; no separate per-instrument SPA slots. This avoids double-counting an effective single-test as two independent tests against the SPA family per H052a §6.
- **Table deliverable (§4.5).** Reported per-instrument (ES separately, NQ separately, MES/MNQ as robustness exhibits) — the user-facing artifact is per-instrument because target-zone price levels are instrument-specific.
- **Mediation block.** Primary estimator pooled (one set of `(â, b̂, ĉ′)` across ES+NQ); per-instrument breakouts pre-registered as a secondary exhibit.

### 5.6 Loss / metric

- Model fit: MSE / logistic / negative-log-likelihood per arm and label.
- Primary gate metric: out-of-sample net-of-cost Sharpe of the trading rule that maps each arm's prediction at 09:45 ET into a 09:45 ET MOC entry and a 10:30 ET MOC unwind.
- Table-deliverable metric: Brier score + reliability decomposition (Brier 1950); BSS against climatological per-instrument prior.

## 6. Splitter

- `PurgedWalkForwardSplitter` per implementation-plan §4.1 (Cycle-4 deliverable).
- **Purge.** 45 min (predictand horizon).
- **Embargo.** Data-driven Politis-White 2004 stationary-bootstrap optimal block length on session-grouped residuals; PACF cross-check; both candidates logged to `ReproLog`. Embargo placement per [ADR-0007](../../../docs/decisions/ADR-0007-stacked-embargo.md) (mlfinlab-stacked).
- **CPCV escalation.** When realized OOS sample fails the §9 power precondition or training-fold daily N < 5,000, escalate to `CombinatorialPurgedCV` per de Prado 2018 §12 with `n_groups`/`n_test_groups` parameterized and logged to `ReproLog`.
- **Cross-instrument correlation.** Pool ES+NQ as one stratified hypothesis (per §5.5).
- **Calibration fold.** Within each walk-forward step, reserve a slice of the training fold for the §4.5 calibration step. The slice is the chronologically latest portion of the training fold *after* purge + ADR-0007 stacked embargo are applied; the slice size targets `N_cal ≥ 500 sessions per arm` (per §4.5.3). If the post-purge-and-embargo training fold cannot supply 500 sessions, escalate to Platt scaling per §4.5.3. The calibration fold is purged + embargoed from both the model-fitting fold and the OOS evaluation fold using the same ADR-0007 stacked-embargo specification, not a chronological-only split.
- **Mediation sub-folds.** Within each walk-forward step, the §5.4 fold-disjoint scalarization protocol partitions the (post-calibration) training fold into `S` (≈50%) and `Med` (≈50%) sub-folds along the time axis, with ADR-0007 stacked embargo between them. The walk-forward outer split → calibration → `S` / `Med` partition is therefore a four-way time-ordered split: `[outer_train_fit_S | embargo | outer_train_fit_Med | embargo | calibration | embargo | OOS_test]`.
- **Inner-WF-step floor.** `N_Med ≥ 200` and `N_S ≥ 200` after stacked embargo per inner WF step. If either falls below the floor in any inner WF step, the mediation block for that step is recorded as `archive(null, mediation-underpowered)` and contributes only to the §10.2 descriptive annotation pathway; the §10.1 Sharpe-differential gate is unaffected by mediation-block underpowering. Feasibility is unit-tested per §11.2 item 15 against the smallest realized inner-WF training fold across the IS window.

## 7. Cost model

- `cost_model_id`: `nt8_es_nq_rth_v1` — the Cycle-6 NT8 ES/NQ RTH cost model already implemented in [src/skie_ninja/backtest/costs/](../../../src/skie_ninja/backtest/costs/).
- **One round-trip per session.** Entry 09:45 ET MOC, exit 10:30 ET MOC. The single-round-trip cost burden is materially lighter than the path-dependent triple-barrier strategies (H050/H052a) — explicitly documented for cross-strategy interpretability; not exploited as an evidence-bar relaxation.
- **Slippage (primary).** 1-tick floor at entry and exit on the roll-adjusted front-month; upgraded to empirical fit when NT paper-trade logs accumulate (mirrors H052a §7).
- **Commissions + exchange fees + NFA.** Per-contract static schedule from [config/instruments.yaml](../../../config/instruments.yaml) (CME-cited).
- **No borrow cost** (futures).

### 7.1 Slippage sensitivity (binding secondary cost arm)

The 1-tick floor at 09:45 ET MOC entry is *not* uniformly conservative: 09:45 ET sits in a relative liquidity trough between the 09:30 ET open and the post-09:30 macro-news echo, where bid-ask widening on full-size positions can exceed 1 tick (Almgren-Chriss 2001 transient impact upper-bound). To hedge this, a 2-tick-floor cost arm is pre-registered as a secondary exhibit:

- Re-run all three model arms with a 2-tick floor at entry and exit, holding everything else fixed.
- Reported alongside the 1-tick result in the run summary.
- **Decision-rule interaction (binds §10):** if the 2-tick result archives null while the 1-tick result archives positive for the same model arm, the 1-tick result archives as `archive(positive, conditional-on-cost-floor)` rather than unconditionally `archive(positive)`. This makes the cost-floor sensitivity explicit in the disposition rather than buried in the run summary.
- Reference: [Almgren & Chriss 2001, *Journal of Risk* 3(2):5–39](https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf) for transient impact upper-bound at MOC entry; [Frazzini, Israel & Moskowitz 2018, SSRN 2294498](https://doi.org/10.2139/ssrn.2294498) for empirical equity-index slippage scaling.

## 8. Gate thresholds (AMENDED 2026-05-03 per ADR-0013; supersedes the 2026-05-01 ADR-0012 amendment)

> **AMENDED 2026-05-03 by [ADR-0013 permanent-exploration-no-archive-ninjascript-terminus](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).** ADR-0013 dissolves all binding gates: every former Class A item becomes a KPI annotation in the canonical KPI report card per ADR-0013 §3, with methodological-correctness annotation banner per §2.1 (NOT a gate). H053 progresses through the stage progression of ADR-0013 §1; operator promotion at every transition is discretionary on the KPI report card (ADR-0013 §5.3). H053's Stage-3 v2 disposition (`calibration-failed` under ADR-0012) is **retroactively re-tagged** to `kpi-report-emitted` per ADR-0013 §"Retroactive re-tag of existing dispositions". Full §10 + new §15 NinjaScript Implementation cascade lands under follow-up `P1-ADR-0013-DESIGN-MD-CASCADE`; H053's NinjaScript implementation is mandatory per ADR-0013 §5.
>
> **ALL TEXT BELOW THIS BANNER IS HISTORICAL RECORD** preserved verbatim per ADR-0013 §4.1 non-loss mandate (per Round-2 audit F-2-5 remediation). For the current disposition philosophy and authoritative gating semantics see ADR-0013 §1-§5. The legacy "binding gates" / "Class A" / "three-class rubric" / disposition labels (`archive(complete; KPI report)`, `calibration-failed`, `leakage-detected`, `reproducibility-incomplete`, `archive(null, ...)`) referenced below are SUPERSEDED and exist solely for audit-trail provenance.

Per [ADR-0012 disposition-philosophy-aspirational-mvp](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) (now superseded by ADR-0013), the H053 gating tree is restructured from "Sharpe-CI gates plus annotations" to a **three-class rubric**: binding gates (Class A); KPIs reported but not nulling (Class B); documentation requirements (Class C). The original H053 gate enumeration is preserved below as the §8.b legacy reference.

### 8.a Class A — Binding gates (a strategy fails the disposition iff one of these fails) (per-hypothesis applicability per Round-1 audit F-1-2 + F-1-6)

Per [ADR-0012 §"Class A"](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md):

- **PIT / leakage-canary** (ALWAYS BINDING; `applicable: yes`). Binding test paths: [tests/integration/test_h053_pit_canaries.py](../../../tests/integration/test_h053_pit_canaries.py) (NaN-poison structural detector + dual-fit-call invariance + boundary-anchor inclusion) + Cycle-4 leak canary suite at [tests/unit/test_leak_canaries.py](../../../tests/unit/test_leak_canaries.py) (fold-boundary monotonicity + label-purge horizon + dual-fit observer + TracingArray). Methodological correctness; never negotiable.
- **Calibration: Brier Skill Score (BSS) > 0** vs per-instrument climatological prior on the OOS fold (`applicable: yes` — H053 ships the §4.5 K×3 categorical-archetype-bias-target probability table).
- **Calibration: reliability slope ∈ [0.7, 1.3]** per [Niculescu-Mizil & Caruana 2005](https://doi.org/10.1145/1102351.1102430) (loose-band; `applicable: yes` for the §4.5 categorical table).
- **Reproducibility log present** (ALWAYS BINDING; `applicable: yes`). git_head + dataset_checksum + scientific_payload_sha256 + pip_freeze sha. Per CLAUDE.md user-global §Reproducibility (hook-enforced).
- **DSR / PSR above `dsr_activation_size`** per [config/gate.yaml](../../../config/gate.yaml) (`applicable: when family ≥ 10`; currently no-op; family=7 < activation_size=10). Will bind once family ≥ 10.
- **Hansen SPA family p ≤ α at operator-promotion** (`applicable: at-operator-promotion`; binding at the promotion gate per [ADR-0012 §"Operator-promotion rule"](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md), NOT at design-time disposition).

### 8.b Class B — KPIs (recorded; reported in disposition memo; do NOT null the disposition)

Per [ADR-0012 §"Class B"](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md). The disposition memo's KPI report card includes:

- **Paired Sharpe-differential CI vs passive-long benchmark** (Lo 2002 §III HAC-adjusted SE / Mertens 2002 / Opdyke 2007 asymptotic with [Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized circular-block bootstrap). Annotation: `sharpe-vs-passive-{positive-strong, positive-weak, flat, negative}` per ADR-0012 thresholds.
- **Paired Sharpe-differential CI vs time-of-day-FE benchmark**. For H053's single-clock-time predictand (09:45→10:30 ET per session), the canonical per-clock-bin spec collapses; re-spec'd per `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE` to **prior-day same-bin return**: `ŷ_{i,t} = y_{i,t-1}`. This addresses the [Heston, Korajczyk & Sadka 2010](https://doi.org/10.1111/j.1540-6261.2010.01573.x) periodicity-confound risk identified in [lit_review_H053_2026-04-28.md](lit_review_H053_2026-04-28.md) §A as a **descriptive comparison**, not a binding gate.
- **Hansen 2005 SPA family p-value** with [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega.md) omega correction across the SPA universe (H050 + H051 + H052a + H052b + H053). H053 contributes 3 ex-ante-fixed slots (Arm 1, Arm 2, Arm 3) per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md). Reported alongside per-arm Sharpe; readers can apply their own family-wise correction. CPCV path-reconstruction (`P1-BACKTEST-CPCV`) extends the SPA universe to per-path Sharpe distributions; **CPCV is now BLOCKING-BEFORE-ANY-STAGE-3-RE-RUN-OR-NEW-HYPOTHESIS-DISPOSITION** per ADR-0012 §"Cross-validation methodology".
- **Realized max-DD ratio** (arm DD / passive DD).
- **Power-margin ratio** (realized OOS n / `n_required_for_power_80` per Lo 2002 §III HAC-adjusted Sharpe MDE under option-3 conservative prior per [power_calibration_addendum_2026-04-30.md](power_calibration_addendum_2026-04-30.md)). The dataset envelope is fixed (per CLAUDE.md §Standing constraints + user 2026-05-01 directive); power-margin is a descriptor, not a gate.
- **Mediation NIE / NDE point estimate + bootstrap CI** per design.md §5.4 (descriptive-only per §1).
- **In-sample partial-R²** of multi-timeframe X over mediator alone (per Stage-2).
- **Cost-floor sensitivity** (1-tick vs 2-tick slippage per design.md §7.1).

### 8.c SPA-family slot consumption (preserved from §8 legacy)

H053 enters the project's `universe_snapshot_id` alongside H050/H051/H052a/H052b with **exactly three slots pre-registered ex ante** (Arm 1, Arm 2, Arm 3). An arm whose §11 prerequisites do not land before `running` is recorded as `prerequisite-not-met` and **its slot is consumed by that record** — the slot is not freed for a fourth arm and is not removed from the family. This eliminates the adversarial-drop loophole and preserves family size at exactly 3 for the Hansen 2005 §2.4 ex-ante-fixed-universe requirement and the ADR-0008 omega correction. (NOTE: Hansen SPA itself is now a Class B KPI per ADR-0012, not a binding gate; the slot-consumption discipline remains because the SPA p-value is still computed and reported.)

### 8.d Defaults (preserved from §8 legacy)

- `alpha`: 0.05 (one-sided). Used only in the KPI-reported Hansen SPA p-value computation; no longer a binding gate.
- `bh_threshold`: 0.10. Same — KPI-reported only.
- `power_target`: 0.80. Used only in the `n_required_for_power_80` KPI computation; underpowered status is now an annotation, not a null verdict.

### 8.e Legacy reference (the original H053 gate spec, retained for archival traceability)

The pre-ADR-0012 H053 gate spec was a conjunctive Sharpe-differential CI rule: "Sharpe-differential CI excludes zero at 95% against both the passive-long benchmark and the time-of-day fixed-effects benchmark, AND realized max-DD non-worse than the passive-long benchmark." That spec is superseded by §8.a + §8.b above; the original is retained in git history at commit `b6df757` (design.md initial) for retrospective audits. The H053 Stage-1 first-pass `archive(null, sharpe-ci-not-clearing-conjunctive)` verdict per commit `76599bd` is retroactively re-tagged `archive(complete; KPI: sharpe-vs-passive-positive-weak)` per ADR-0012 §"Disposition labels under the new rubric"; see [docs/audits/audit_trail_2026-05-01_disposition-philosophy-shift.md](../../../docs/audits/audit_trail_2026-05-01_disposition-philosophy-shift.md).

## 9. Stopping rule + power

- `N_draws = 200` per arm per Bergstra-Bengio 2012. Caveat (inherited from project follow-up `P1-H050-LGB-N-DRAWS-EMPIRICAL`): for the H053 grid sizes (ElasticNet 5×3 = 15 cells; LightGBM 3×2×2 = 12 cells), `N_draws = 200` is replicate-coverage rather than the high-dim B&B regime; the project-wide N_draws calibration follow-up extends to H053 as `P1-H053-N-DRAWS-EMPIRICAL` (non-blocking).
- LightGBM early-stopping: `n_estimators` ≤ 2000, patience 50.
- Max wall-clock: 48 h per H052a §9.
- **Pre-registered `power` block (recalibrated for H053).** Unlike H052a's path-dependent triple-barrier predictand, H053's predictand is a 45-min fixed-clock-time return sampled once per session. `s_min` is therefore recalibrated, not copy-pasted:
  ```yaml
  power:
    alpha: 0.05
    target_power: 0.80
    n_obs_per_year: 252        # one obs per session
    n_obs_pooled_per_year: 504 # ES + NQ pooled
    expected_n_oos: ...        # filled at the start of the running run from §6 splitter outputs
    s_min: ...                 # MDE-inverted from expected_n_oos via Lo 2002 §III HAC-adjusted Sharpe SE
    ar1_rho_pilot: ...         # estimated on a pre-IS pilot window (2010-2014, outside IS) and pinned
    excess_kurtosis_pilot: ... # estimated on the same pilot window and pinned (NOT refined on IS)
    variance_formula: lo2002_hac_adjusted
    n_required: ...            # inference/power.py::required_n
  ```
  - The `s_min` placeholder is filled by **inverting the MDE for 80% power** at α=0.05 one-sided given `expected_n_oos` and the pilot-pinned (`ar1_rho`, `excess_kurtosis`); the calculation and the result are persisted to `ReproLog.power_calibration_{run_id}.json`.
  - `ar1_rho_pilot` and `excess_kurtosis_pilot` are estimated on a **pre-IS pilot window** (2010-2014), explicitly outside the IS fold, to avoid in-sample tuning. Pinning at the start of `running` is binding; refining on IS is pre-registered as **forbidden** for H053 (departure from H052a's `pilot estimate, refined on IS-fold` language).
  - References: [Lo 2002 §III](https://doi.org/10.2469/faj.v58.n4.2453); [Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094) for DSR-inflation calibration; [Heston, Korajczyk & Sadka 2010](https://doi.org/10.1111/j.1540-6261.2010.01573.x) implied annualized intraday-momentum Sharpes as a sanity-check anchor.
- Sample-size precondition: realized OOS sample must meet `n_required_for_power_80` per arm; underpowered arms are recorded as `archive(null, underpowered)` per arm and the SPA slot is consumed by that null record (per §8; not freed for a fourth arm).
- No HMM stationarity precondition (H053 has no HMM gate).

## 10. Decision rule (AMENDED 2026-05-01 per ADR-0012)

The decision rule per ADR-0012 §"Disposition labels under the new rubric" produces one of four **disposition classes**, evaluated top-down per model arm `a`. Class C documentation requirements + Class B KPI report card accompany every disposition regardless of class.

### 10.1 Disposition class (strict precedence)

1. **`leakage-detected`** — PIT canary or any other §3.6 / §11.2-prereq-11 leakage gate failed for arm `a`. Disposition: `leakage-detected`. Not eligible for any further consideration without remediation. Terminates.
2. **`reproducibility-incomplete`** — required §11 provenance fields (git_head, dataset_checksum, scientific_payload_sha256, pip_freeze sha) missing on arm `a`'s ReproLog. Disposition: `reproducibility-incomplete`. Terminates.
3. **`calibration-failed`** — §4.5 table-deliverable BSS ≤ 0 vs per-instrument climatological prior on the OOS fold, OR reliability slope outside [0.7, 1.3]. Disposition: `calibration-failed`. The strategy is recorded but is NOT eligible for paper-trade. Terminates.
4. **`prerequisite-not-met`** — §11.2 / §11.3 / §11.4 prerequisites for arm `a` did not land before `running`. Disposition: `prerequisite-not-met`. The SPA slot is consumed per §8.c. Terminates.
5. **`archive(complete; KPI report)`** — passes Class A gates (PIT/leakage + BSS + reliability + reproducibility + DSR-when-active). The §8.b KPI report card is published. Eligible for paper-trade subject to operator review of the KPI report card and the [CLAUDE.md §Execution-bar](../../../CLAUDE.md) 60-session-day Sharpe-within-CI floor. Terminates.

### 10.2 KPI report card (accompanies every disposition that reaches §10.1.5)

Per [ADR-0012 §"Class B"](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md), the KPI report card is published in the disposition memo with one **qualitative** annotation per KPI. Per Round-1 audit F-1-4 remediation, **numerical sub-classification thresholds (e.g., the "strong" vs "weak" 0.20 / 0.10 boundaries) are deferred to follow-up `P1-DISPOSITION-KPI-ANNOTATION-THRESHOLD-CALIBRATION`**; numeric values are reported alongside the qualitative annotation.

| KPI | Qualitative annotation values |
|---|---|
| Sharpe-vs-passive | `positive` (CI excl. 0, point > 0) / `marginal` (CI covers 0, point > 0) / `flat` (CI covers 0, point ≈ 0) / `negative` (point < 0) |
| Sharpe-vs-bench | same; for H053 the bench is per-prior-day-same-bin (an AR(1) lag-1 baseline; the original HKS periodicity-confound benchmark is degenerate for single-clock-time predictands and is unaddressed under the AR(1) substitute per Round-1 audit F-1-11) |
| SPA family p (omega-corrected) | `spa-passes` (p ≥ α) / `spa-rejects` (p < α). Re-evaluated as binding gate at operator-promotion per ADR-0012. |
| Max-DD ratio (arm/passive) | `favorable` / `comparable` / `adverse` |
| Power margin (n_oos / n_required_for_power_80) | `adequate` / `marginal` / `low`. Per ADR-0012 §"Class B" + Round-1 F-1-8: a `power-margin-low` arm requires an extended **120-session-day** paper-trade verification window. |
| Mediation NIE | `significant` / `flat`. Per Round-1 F-1-14: NIE annotation does NOT entitle promotion absent corroborating Sharpe-vs-passive-positive AND partial-R²-positive evidence. |
| Mediation NDE | `significant` / `flat` (same caveat as NIE). |
| In-sample partial-R² (multi-tf X over mediator) | `positive` (CI excl. 0) / `flat` (CI covers 0). Magnitude sub-classification deferred. |
| Cost-floor sensitivity (1-tick vs 2-tick) | `cost-robust` / `cost-floor-conditional` / `cost-flat` |

The disposition string format: `{disposition_class} | {KPI report card} | {strengths/weaknesses summary}`.

### 10.3 Example combined dispositions

- All Class A gates pass; Sharpe-vs-passive positive-weak; Sharpe-vs-todfe flat; SPA passes; max-DD favorable; power-margin adequate; mediation NIE significant; partial-R² moderate; cost-robust → `archive(complete; KPI: sharpe-vs-passive-positive-weak, sharpe-vs-todfe-flat, spa-passes, max-dd-favorable, power-margin-adequate, mediation-NIE-significant, partial-r2-moderate, cost-robust)`.
- BSS = -0.02 (calibration failed) → `calibration-failed; KPI: ...` (KPI report still published; strategy recorded but not paper-trade-eligible).
- PIT canary detects post-cutoff bar contamination → `leakage-detected` (KPI report NOT published; remediate-then-rerun).

### 10.4 Eligibility for paper-trade promotion

A `archive(complete; KPI report)` disposition makes arm `a` **eligible for paper-trade** subject to:
- Operator review of the KPI report card (the strengths-and-weaknesses summary informs the operator's decision; per ADR-0012 the design-time gate no longer mechanically auto-promotes).
- The [CLAUDE.md §Execution bar](../../../CLAUDE.md) 60-session-day paper-trade Sharpe-within-CI floor (this is the load-bearing pre-live constraint; the prior design-time Sharpe-CI gate is downgraded to a KPI per ADR-0012).
- The [§11.1 kill-switch](#111-kill-switch-design-binding-before-paper-trade) (binding before paper-trade, per the original §11.1 spec).
- Capacity caps in [CLAUDE.md §Standing constraints](../../../CLAUDE.md).

### 10.5 Legacy reference (the original H053 §10 gating tree, retained for archival traceability)

The pre-ADR-0012 H053 §10 was a strict precedence-ordered tree with rules 1-8 producing `archive(null, ...)` outcomes including: data-violation, prerequisite-not-met, underpowered, Sharpe-differential null vs passive, risk-violation, periodicity-confound, SPA family rejection. The Stage-1 first-pass `archive(null, sharpe-ci-not-clearing-conjunctive)` verdict from commit `76599bd` was per the legacy §10.1.4 rule (Sharpe-differential null vs passive-long). Under the new rubric §10.1.5 this becomes `archive(complete; KPI: sharpe-vs-passive-positive-weak, sharpe-vs-todfe-flat-degenerate-bench, max-dd-favorable, power-margin-adequate, partial-r2-not-applicable-stage-1, cost-robust)`. Retroactive re-tag is documented in [docs/audits/audit_trail_2026-05-01_disposition-philosophy-shift.md](../../../docs/audits/audit_trail_2026-05-01_disposition-philosophy-shift.md).

## 11. Reproducibility commitments

- git HEAD: TBD at run.
- `uv pip freeze` sha: TBD at run.
- RNG seed: 20260428.
- Dataset checksum: `vendor_legacy_1min_roll_adjusted` SHA256, captured in `ReproLog.dataset_checksums`.
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- Mediation bootstrap trace path: `logs/reproducibility/{run_id}_mediation.json`.
- Archetype thresholds path: `logs/reproducibility/{run_id}_archetype_thresholds.json`.
- Calibration trace path: `logs/reproducibility/{run_id}_isotonic_calibration.json`.
- LLM-arm trace path (if Arm-3 ships): `logs/reproducibility/{run_id}_llm_prompt_selection.json`, with prompt SHA256 + model weight hash + tokenizer version + image-render hashes.
- BLAS-thread pinning per [ADR-0009](../../../docs/decisions/ADR-0009-blas-thread-pinning.md).

### 11.1 Kill-switch design (binding before paper-trade)

[CLAUDE.md](../../../CLAUDE.md) §Execution bar requires a documented kill-switch before live execution. The kill-switch is not enforced for `designed` status but is binding before promotion to paper-trade following an `archive(positive)` outcome under §10.1.8.

**Operational-threshold note.** The trip thresholds below (`k_DD = 1.5`, 5-session warm-up, 20-session rolling Sharpe window, 2σ × 20-session Brier-drift) are **paper-trade operational thresholds, not statistical-inference parameters**. They do not enter the SPA family, the power calibration, or the §10 gating tree. The empirical-justification rule in [~/.claude/CLAUDE.md §Parameter & Prompt Selection](../../../../.claude/CLAUDE.md) does not bind operational thresholds; recalibration to empirically-fit values via IS-fold realized-DD distribution is tracked under follow-up `P1-H053-KDD-EMPIRICAL-CALIBRATION` and must close before any *live* (post-paper-trade) promotion under [CLAUDE.md](../../../CLAUDE.md) §Execution bar.

Trip conditions:

- **Realized intraday DD trip.** Per-session realized DD from any 09:45 ET entry to its 10:30 ET exit > `k_DD × backtested_max_session_DD`, where `k_DD = 1.5` is pre-registered as the paper-trade operational threshold, applied to the realized series after a 5-session warm-up.
- **Rolling Sharpe trip.** Realized Sharpe over a rolling 20-session window of paper-trade returns < 0 (annualized).
- **Calibration drift trip.** Per-session Brier score on the §4.5 table > the OOS-fold Brier score + `2 × σ̂_{Brier, OOS}` over a rolling 20-session window.
- **Substrate trip.** Roll-adjusted-substrate SHA256 mismatch between the running run and the `designed`-time companion (§2 hard-fail check fires → kill).

When tripped, the kill-switch halts further `running`-source orders, archives the run as `archive(null, kill-switch-tripped)`, and triggers a post-mortem before any restart. The kill-switch artifact lives at [config/kill_switch_H053.yaml](../../../config/kill_switch_H053.yaml) (to be authored as a `designed → running` prerequisite, §11.2 item 12).

### 11.3 Hardware reproducibility commitments

Round-2 of the audit-remediate-loop tightened the LLM-arm determinism requirement (§5.3) and the chart-image render scope (§3.5). Both depend on a binding hardware target persisted to ReproLog at run start:

- **Pinned GPU model + driver version** (e.g., NVIDIA A100 / H100 / consumer RTX class), recorded in `ReproLog.gpu_model` and `ReproLog.driver_version`.
- **Pinned CUDA version**, recorded in `ReproLog.cuda_version`.
- **Pinned conda environment hash** (sorted `uv pip freeze` SHA256), recorded in `ReproLog.env_hash`.
- **Bit-identical-logit-tensor replay protocol** — top-1-token logit tensors compared bit-by-bit across two consecutive runs on the pinned hardware target. Failure → `archive(null, prerequisite-not-met)` per §5.3 + §10.1.2.
- **Image-render-hash determinism** — same-machine + same-env determinism is guaranteed; cross-OS / cross-Python-minor-version determinism is **not** guaranteed and is tracked as the CI-portability follow-up `P1-H053-IMAGE-RENDER-CI-PORTABILITY`.

References: [PyTorch reproducibility notes](https://pytorch.org/docs/stable/notes/randomness.html); [matplotlib stable docs](https://matplotlib.org/stable/devel/coding_guide.html) (no formal cross-platform guarantee).

### 11.2 Prerequisite artifacts for `designed` → `running`

1. `vendor_legacy_1min_roll_adjusted` ingest module green (Cycle-1 ✓).
2. ElasticNet wrapper committed under [src/skie_ninja/models/](../../../src/skie_ninja/models/).
3. Mediation estimator + paired-pairs bootstrap CI module committed and green on synthetic-null coverage tests (mediation under known generative model with serial-dependent residuals recovers `NIE`, `NDE` within Monte-Carlo SE; rejection rate at α=0.05 covers nominal under H0_NIE; per-replicate refit of both equations).
4. Walk-forward engine + purged CV (Cycle-4 ✓).
5. Hansen SPA (Cycle-5 ✓).
6. NT8 cost model (Cycle-6 ✓).
7. (Conditional on Arm-3 inclusion; per §5.3) LLM-arm deterministic-replay scaffolding green: temperature 0 + seed pinned + weight-hash logged + `torch.use_deterministic_algorithms(True)` + `CUBLAS_WORKSPACE_CONFIG=:4096:8` + bit-identical-logit-tensor replay across two consecutive runs on the pinned hardware target. Failure to land → `archive(null, prerequisite-not-met)` per §10.1.2; the SPA slot is consumed by that null record. Image-render-hash determinism check (per §3.5) is scoped to the same machine + same conda env hash; cross-OS / cross-Python-minor-version determinism is **not** guaranteed and is documented as a CI follow-up under `P1-H053-IMAGE-RENDER-CI-PORTABILITY`.
8. Archetype categorization module + isotonic calibration wrapper committed and green; calibration unit tests assert (a) reliability slope ∈ [0.7, 1.3] on a held-out synthetic Bernoulli sample, (b) Brier reduction over uncalibrated baseline, (c) per-arm `N_cal ≥ 500` precondition wired with Platt-scaling fallback.
9. Fold-disjoint scalarization protocol unit-tested: synthetic data with known mediator recovery; verifies (a) `f_S` is fitted on `S` only and frozen across `Med` and OOS; (b) bootstrap resampling on `Med` rows recovers nominal coverage on a known generative model.
10. Companion data_requirements_H053_2026-04-28.md authored at `designed` status with binding `vendor_legacy_1min_roll_adjusted` SHA256 (per §2).
11. PIT / leakage canaries wired on the H053 feature factory: bar-set disjointness assertion (§3.0) + Cycle-4 dual-fit-call observer + `TracingArray` capability proxy.
12. Kill-switch config [config/kill_switch_H053.yaml](../../../config/kill_switch_H053.yaml) authored per §11.1 trip conditions.
13. `lit-check` audit against §A and §C citations completed on the design.md draft (this round of audit-remediate-loop).
14. `quant-auditor` audit against this design completed (this round of audit-remediate-loop).
15. **Four-way time-ordered split feasibility unit test** asserts `N_cal ≥ 500` (or Platt fallback per §4.5.3) plus `N_S ≥ 200` plus `N_Med ≥ 200` (per §6 inner-WF floor) on the smallest realized inner-WF training fold across the IS window 2015-2022; below-floor inner steps route to the §6 + §10.1 mediation-underpowered annotation pathway.
16. **ADR-0008 omega-correction integration test** green on a 3-slot SPA family with one null slot (the `archive(null, prerequisite-not-met)` consumption pattern from §8 must round-trip through the omega correction without inflating Type-I).
17. **Time-of-day fixed-effects benchmark module** green: per-clock-bin fixed-effects fit on IS, evaluated on OOS; conjunctive-rule pairing with passive-long verified on synthetic data (§8 + §10.1.6 logic).
18. **2-tick slippage cost arm** wired in [src/skie_ninja/backtest/costs/](../../../src/skie_ninja/backtest/costs/) and unit-tested for parity with the 1-tick path other than the floor parameter; cost-floor-conditional annotation in §10.2 has runnable evidence.
19. **Power-calibration solver** implemented in `inference/power.py::required_n` + MDE inverter for [Lo 2002 §III HAC-adjusted Sharpe SE](https://doi.org/10.2469/faj.v58.n4.2453); writes `ReproLog.power_calibration_{run_id}.json` at run start before any model fit.

## 12. Relationship to other Tier-2b hypotheses

H053 distinguishes itself from the existing Tier-2b register entries on four axes; appending to the existing taxonomy in [H052a/design.md](../H052a/design.md) §12 and the project's prior-art landscape:

- **(a) Predictand.** H053 = fixed-clock-time, fixed-horizon (45 min) regression. H050 = event-driven triple-barrier directional. H051 = mean-reversion entry on a Kalman-filtered basis. H052a = first-hour ORB long with PT/SL/time barriers. H052b = SKIE-ORB-CALL long-call 0DTE.
- **(b) Conditioning.** H053 = multi-timeframe snapshot regression (no HMM gate). H050/H052a/H052b = HMM-gated. H051 = HMM-gated cointegration entry.
- **(c) Mediation framing.** H053 includes a descriptive (not causal) mediation decomposition of higher-timeframe signal through the 09:30–09:45 ET opening bar. None of H050/H051/H052a/H052b include a mediation block.
- **(d) Cost burden.** H053 = single round-trip per session. H050/H051/H052a = path-dependent open-ended. H052b = path-dependent option premium.
- **(e) User-facing deliverable.** H053 produces a partitioned conditional-probability lookup table (§4.5) as the headline output; the Sharpe-differential gate is the primary inferential gate but the table is the primary *artifact* the user reads. None of H050/H051/H052a/H052b produces a per-archetype lookup table.

H053 shares with all five hypotheses: the same `vendor_legacy_1min_roll_adjusted` substrate, the same NT8 RTH cost model, the same project-level inference primitives (Lo 2002, Opdyke 2007, Ledoit-Wolf 2008, Hansen 2005, Politis-White 2004), and the same Hansen SPA universe-snapshot family. H053 contributes three SPA slots ex ante (Arm 1, Arm 2, Arm 3); arms whose prerequisites fail to land before `running` consume their slot as `archive(null, prerequisite-not-met)` per §8, preserving family size at exactly 3.
