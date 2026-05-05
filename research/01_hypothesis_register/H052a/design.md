---
name: H052a — HMM regime-gated first-hour ORB on CME futures (ES/NQ/MNQ/MES)
description: Pre-registered design doc for hypothesis H052a, futures-variant sibling of H052b
type: project
hypothesis_id: H052a
tier: 2b
status: designed
owner: skoir
created: 2026-04-23
citations:
  - ADR-0003-spa-vs-romanowolf
  - ADR-0004-alpha-and-power-defaults
  - ADR-0005-hmm-regime-toolkit
  - ADR-0006-scope-extension-hmm-0dte
  - Hamilton 1989 (doi:10.2307/1912559)
  - Baum et al. 1970 (doi:10.1214/aoms/1177697196)
  - Guidolin-Timmermann 2007 (doi:10.1016/j.jedc.2006.12.004)
  - Andersen-Bollerslev 1998 (doi:10.2307/2527343)
  - de Prado 2018 Advances in Financial Machine Learning (Wiley, ISBN 978-1119482086)
  - Lo 2002 (doi:10.2469/faj.v58.n4.2453)
  - Opdyke 2007 (doi:10.1057/palgrave.jam.2250084)
---

# H052a — HMM regime-gated first-hour ORB on CME futures

Pre-registration for hypothesis H052a. Futures-variant sibling of [H052b](../H052b/design.md). Frozen at `designed` on 2026-04-23.

## 1. Hypothesis

- H0: The Sharpe ratio of the **first-hour ORB long-only directional trade on ES/NQ futures conditioned on the HMM non-stress state** does **not** exceed the Sharpe of the **unconditional first-hour ORB long-only directional trade on the same instrument** by a margin that exceeds bootstrap sampling error.
- H1: It does.
- Mechanism: the ORB green-rate bias pre-registered in the sibling repo [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) for QQQ first-hour (H052b) is a statement about equity-index intraday drift in the 09:30–10:30 ET window. If that drift exists, it should also appear (with attenuation) in the futures reference NQ/MNQ (and, to lesser extent, in ES via the beta-1 SPX linkage). Prior-art SKIE Ninja work flagged the unconditional futures directional signal as ≈50% AUC on technicals alone ([README.md](../../../README.md) §Prior-art); the HMM gate is the sole new empirical content. Conditioning on a low-variance HMM emission state filters out high-noise days where even a true drift is swamped by microstructure noise.
- **Critical interpretive note:** H052a is NOT a rediscovery of ORB-on-futures. Unconditional ORB-on-futures is pre-supposed to be ≈null. H052a tests whether **regime-conditioning rescues an otherwise null signal**. A positive result would be surprising and carry large evidentiary weight against prior-art; a null is the expected outcome.
- Primary citations: [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Guidolin & Timmermann 2007, JEDC 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004); [Andersen & Bollerslev 1998, IER](https://doi.org/10.2307/2527343); de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1119482086). ORB literature (Zarattini / Galli / Pagani / Saavedra) flagged UNVERIFIED pending primary-source retrieval — will be addressed in a `lit-check` audit before `designed` → `running`.
- Test statistic: `T_H052a = SR_{ORB, HMM-gated} − SR_{ORB, unconditional}`, paired differential, constructed per-instrument and pooled via inverse-variance weighting. Enters the Romano-Wolf / Hansen SPA family per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md).

## 2. Universe and sample period

- **Instruments**: ES (primary), NQ (primary). Micros MES/MNQ reported as robustness, since they are linear price-rescaled versions of the majors (ADR-0001 capacity ceiling mapping). Any apparent divergence between the front-month major and its micro signals instrument-specific microstructure, not alpha.
- **Frequency**: 1-minute bars.
- **Session**: RTH only; 09:30–16:00 ET (`America/New_York`) per [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py). ETH explicitly excluded — the ORB thesis is a cash-session phenomenon.
- **Sample window**:
  - IS: 2020-01-01 → 2022-12-31
  - OOS: 2023-01-01 → 2024-12-31 (NQ ceiling) / 2025-12-03 (ES ceiling)
- **Roll treatment**: **roll-adjusted front-month continuous series required** via `vendor_legacy_1min_roll_adjusted` (Cycle-1 deliverable of the Tier-2b buildout, 2026-04-23). Ratio adjustment, rolled on volume-crossover per [config/instruments.yaml](../../../config/instruments.yaml) `roll_rule`. **Runs on raw `vendor_legacy_1min` (no roll adjustment) are explicitly forbidden by this pre-reg; results on raw are diagnostic-only and cannot promote H052a past `running`.**
- **Dataset snapshot frozen at pre-registration**: SHA256 of the roll-adjusted parquet captured at the first `running` run and persisted to `ReproLog.dataset_checksums` under key `vendor_legacy_1min_roll_adjusted`. Snapshot is immutable across re-runs of this hypothesis ID.

## 3. Features

HMM emission features (point-in-time, `as_of` strictly ≤ decision timestamp):

- **Realized variance of log-returns** on the front-month ratio-adjusted 1-min series, per [Andersen & Bollerslev 1998, IER 39(4):885–905](https://doi.org/10.2307/2527343). Rolling lookback CV-selected from `{30m, 60m, 120m}` on training folds.
- **First-hour directional sign** (+1/0/−1) at 10:30 ET, matching sibling-repo feature definition.
- **Gap-size bucket**: open(09:30) vs prior-session close log-return, discretized by training-fold quantiles.
- **Day-of-week** one-hot.
- **ETH-session pre-RTH returns**: 06:00–09:29 ET log-return, as a conditioning feature distinguishing "news-driven overnight" from "quiet overnight."
- **VIX daily level**, `as_of = T−1 close` (CBOE). Joins on calendar date.

PIT property tests per implementation-plan §3 and §4.6; stateful features (rolling variances, regime posteriors) use the causal forward filter `p(s_t | y_{1:t})` only per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md).

## 4. Label construction

Per-session P/L on a **futures ORB long-only directional trade**:

- **Entry**: 10:30 ET market order on the front-month roll-adjusted contract when entry gate fires.
- **Side**: long only (pre-reg — matches the sibling QQQ-call positive-delta bias; tests symmetric short side as a robustness exhibit, not as a gating signal).
- **Profit target**: `k_pt × realized_vol_60m` grid on training folds, where `realized_vol_60m` is the prior-hour annualized σ.
- **Stop**: `k_sl × realized_vol_60m` grid.
- **Time stop**: 14:00 ET.
- **Hard close**: 15:55 ET (before 16:00 ET settlement to avoid wide closing-auction spreads).
- **Settlement**: 1-min bar close at exit time; slippage modeled per Cycle-1 cost-model fit.
- **pt_sl**: both active (volatility-normalized).
- **vertical_barrier**: 15:55 ET.
- **volatility_estimator**: realized-vol over prior 60-min window, walk-forward.
- **Capacity**: ≤20 ES and/or ≤40 NQ per [CLAUDE.md](../../../CLAUDE.md) / [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md); enforced at backtest level via `MaxPositionSwitch` simulation.

## 5. Estimator

- **Regime model**: Gaussian HMM over the §3 emission features → per-session binary entry gate.
- **HMM specification** per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md): Gaussian emissions, `covariance_type ∈ {diag, full}`, `n_states` bounded by the ADR-0005 adaptive rule (`n_states ≤ K` s.t. mean within-state `N > 30 · dim`; restart count until top-two LLs within `ε = 2 · SE(bootstrap EM LL)`; floor 5 restarts), BIC + CV selection on training folds.
- **Canonical state ordering**: ascending by emission-variance of the front-month log-return; non-stress state = state 0.
- **Inference-time posterior**: causal forward filter `p(s_t | y_{1:t})` only. Smoothed posteriors `p(s_t | y_{1:T})` are diagnostic-only and excluded from the decision path. Leakage unit test asserts filter output at `t` is a pure function of `y_{1:t}`.
- **Gate**: enter long at 10:30 ET only when `P(s_t = state_0 | y_{1:t_0}) > τ`, `t_0 = 10:30 ET`. `τ` = training-fold Youden-optimal threshold on the unconditional ORB label.
- **Hyperparameter grid**:
  - realized-vol lookback: `{30m, 60m, 120m}`
  - PT multiplier `k_pt`: `{0.5, 1.0, 1.5}`
  - SL multiplier `k_sl`: `{0.5, 1.0, 1.5}`
  - HMM `covariance_type`: `{diag, full}`
- **Search protocol**: nested walk-forward with random search, `N_draws = 200` per [Bergstra & Bengio 2012](https://www.jmlr.org/papers/v13/bergstra12a.html).
- **Loss / metric**: HMM log-likelihood for fit; Sharpe-differential for gate.

## 6. Splitter

- `PurgedWalkForwardSplitter` per implementation-plan §4.1.
- **Purge**: one trading session (intraday horizon; ORB exits before close).
- **Embargo**: data-driven via Politis-White 2004 stationary-bootstrap optimal block length on daily P/L residuals; PACF cross-check per implementation-plan §4.1. Both candidates logged to `ReproLog`.
- **CPCV**: when sample N < 20k (daily N ≈ 1250 over 2020–2024; likely trips CPCV), `CombinatorialPurgedCV` per de Prado 2018 §12 with `n_groups`/`n_test_groups` parameterized and logged.
- **Cross-instrument correlation**: ES and NQ returns are highly correlated (ρ > 0.85 on 1-min bars). Treat as one pooled hypothesis with instrument-dummy stratification; do NOT double-count as independent tests against the SPA universe.

## 7. Cost model

- `cost_model_id`: `futures_orb_v1` — to be registered in `src/skie_ninja/backtest/costs/` (Cycle-1 deliverable).
- **Commissions + exchange fees + NFA**: per-contract static schedule from [config/instruments.yaml](../../../config/instruments.yaml) (CME-cited). Applied every round-trip.
- **Slippage**: 1-tick floor on market orders at entry and exit (conservative), upgraded to regime-wise empirical fit once NT paper-trade logs accumulate per implementation-plan §6. The static floor is diagnostic-only; evidence-bar submission of H052a must include the empirical cost-model fit.
- **No borrow cost**: futures don't have one.

## 8. Gate thresholds (AMENDED 2026-05-03 per ADR-0013; supersedes the 2026-05-01 ADR-0012 amendment)

> **AMENDED 2026-05-03 by [ADR-0013 permanent-exploration-no-archive-ninjascript-terminus](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).** ADR-0013 dissolves all binding gates: every former Class A item becomes a KPI annotation in the canonical KPI report card per ADR-0013 §3, with methodological-correctness annotation banner per §2.1 (NOT a gate). H052a progresses through the stage progression of ADR-0013 §1; operator promotion at every transition is discretionary on the KPI report card (ADR-0013 §5.3). Full §10 + new §15 NinjaScript Implementation cascade lands under follow-up `P1-ADR-0013-DESIGN-MD-CASCADE`.
>
> **ALL TEXT BELOW THIS BANNER IS HISTORICAL RECORD** preserved verbatim per ADR-0013 §4.1 non-loss mandate (per Round-2 audit F-2-5 remediation). For the current disposition philosophy and authoritative gating semantics see ADR-0013 §1-§5. The legacy "binding gates" / "Class A" / "three-class rubric" / disposition labels referenced below are SUPERSEDED and exist solely for audit-trail provenance.

Per [ADR-0012 disposition-philosophy-aspirational-mvp](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) (now superseded by ADR-0013) (per Round-1 audit F-1-2 + F-1-6 remediations re: applicability), H052a's gating tree is restructured to the three-class rubric:

### 8.a Class A — Binding gates (per-hypothesis applicability)

- **PIT / leakage-canary** (ALWAYS BINDING). Binding test paths: Cycle-4 leak canary suite + per-hypothesis integration test [tests/integration/test_h052a_pit.py](../../../tests/integration/test_h052a_pit.py) to be authored as §11.2 prereq before next H052a launch (tracked under `P1-H052A-PIT-CANARY-INTEGRATION-TEST-LANDED`).
- **Calibration: BSS / reliability** — `applicable: WHERE` for the HMM-state posterior. The HMM emits per-state posterior probabilities on the OOS fold; these MAY be calibrated as a binding gate on the posterior-output KPI table if H052a ships such a deliverable. Until then, calibration is `applicable: NO` for the binary HMM-gated entry decision.
- **Reproducibility log present** (ALWAYS BINDING).
- **DSR/PSR above `dsr_activation_size`** — `applicable: when family ≥ 10`.
- **Hansen SPA family p ≤ α at operator-promotion** per ADR-0012 §"Operator-promotion rule".

### 8.b KPIs (Class B; reported, not binding at design-time)

Sharpe-vs-passive CI, Sharpe-vs-unconditional, SPA family p (KPI at design-time, BINDING at promotion), max-DD ratio, power margin, HMM-state coverage statistics. Defaults preserved (`alpha=0.05`, `bh_threshold=0.10`, `power_target=0.80`) — KPI-reported only. SPA universe entry preserved per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md).

The legacy primary gate (Sharpe-differential CI vs unconditional excludes zero at 95%), secondary gate (max-DD non-worse), and DSR/PSR gating are all downgraded to Class B KPIs per ADR-0012 §"Class B".

## 9. Stopping rule + power

- Random search budget `N_draws = 200`.
- Max-iter EM = 500; tol = 1e-4.
- Max wall-clock: 48 hours.
- Pre-registered `power` block (per implementation-plan §5.1):
  ```yaml
  power:
    s_min: 1.0
    alpha: 0.05
    target_power: 0.80
    ar1_rho: [0.00, 0.10]
    excess_kurtosis: 5.0    # pilot-data estimate, to be refined on IS-fold
    variance_formula: lo2002_hac_adjusted
    n_required: ...         # computed by inference/power.py::required_n
  ```
- HMM stationarity pre-check failure per ADR-0005 → `prerequisite-not-met` (Class A.4 per ADR-0012), not `archived(null, precondition-failed)`.
- Sample-size precondition: realized OOS sample failing `n_required_for_power_80` is now a `power-margin-low` KPI annotation per ADR-0012, not an `archive(null)` verdict.

## 10. Decision rule (AMENDED 2026-05-01 per ADR-0012)

The H052a decision rule is restructured per [ADR-0012 §"Disposition labels under the new rubric"](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) into the three-class disposition rubric (`leakage-detected` / `reproducibility-incomplete` / `calibration-failed` / `prerequisite-not-met` / `archive(complete; KPI report)`). All Sharpe / SPA / power / max-DD outcomes are now Class B KPIs reported in the disposition memo's report card; they do NOT null the strategy.
- Raw (non-roll-adjusted) data used for any promotion decision → automatic `archive(null, data-violation)`. Roll-adjusted derivative is a hard prerequisite per §2.

## 11. Reproducibility commitments

- git HEAD: TBD at run.
- `uv pip freeze` sha: TBD at run.
- RNG seed: 20260423.
- Dataset checksum: `vendor_legacy_1min_roll_adjusted` SHA256, captured in `ReproLog.dataset_checksums`.
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json`.
- **Prerequisite artifacts for `designed` → `running` transition**:
  1. `vendor_legacy_1min_roll_adjusted` ingest module committed and green on tests (Cycle-1 deliverable).
  2. HMM toolkit committed and green on tests (Cycle-3 deliverable).
  3. Walk-forward engine + purged CV committed and green (Cycle-4 deliverable).
  4. Hansen SPA committed and green on synthetic-null coverage tests (Cycle-5 deliverable).
  5. `lit-check` audit against ORB primary-source literature (Zarattini et al.) completed.

## 12. Relationship to H052b and other Tier-2b hypotheses

H052a and [H052b](../H052b/design.md) share: HMM toolkit, first-hour directional timing signal, emission-feature family, gate logic. They differ in: execution instrument (futures vs QQQ 0DTE calls), payoff structure (linear vs long-convex), capacity mapping (direct vs delta-equivalent), data dependency (live raw 1-min vs vendor-gated option chain). Both enter the same Hansen SPA universe. [H050](../H050/) and [H051](../H051/) likewise share the HMM toolkit but carry distinct economic content.

## 15. NinjaScript Implementation (NEW per [ADR-0013 §5.1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), 2026-05-04)

Per ADR-0013 §5 + §5.1, every hypothesis design.md gains a §15 enumerating the NinjaScript C# implementation. H052a's NinjaScript implementation is sequenced AFTER the production walk-forward Stage-3 KPI report card emission per follow-up `P1-H052A-NINJASCRIPT-IMPL`.

**Operator-discretionary per 2026-05-04 user directive**: per the user 2026-05-04 directive following H050 v1's definitive negative result, NinjaScript implementation past `kpi-report-emitted` is **operator-discretionary on the canonical KPI report card values** (per ADR-0013 §5.3 + §1 stage-progression operator-promotion semantics). H052a's `kpi-report-emitted` → `ninjascript-implemented` transition is therefore not auto-triggered; the operator decides upon review of the §3.2 canonical 9-table summary at end-of-simulation per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md).

This section is also the venue for **citation-erratum acknowledgments** per ADR-0013 §"Frozen pre-registration amendment" (§1-§7 of this design.md are immutable; corrections to citation defects in §1-§7 are documented here without editing the original §-text).

### 15.1 Citation errata (Phase-0 ORB lit-check 2026-05-04 findings L-1 through L-4)

The following citation + framing defects were surfaced by the Phase-0 ORB lit-check audit ([docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md](../../../docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md)). They are recorded here per the §1-§7 immutability discipline:

#### Erratum-1 (L-1; severity = critical): "Zarattini / Galli / Pagani / Saavedra" citation chain

**Frozen text** (design.md §1 line 34): "ORB literature (Zarattini / Galli / Pagani / Saavedra) flagged UNVERIFIED pending primary-source retrieval — will be addressed in a `lit-check` audit before `designed` → `running`."

**Verified primary sources** (Phase-0 lit-check 2026-05-04):
- **Zarattini ✓ VERIFIED**: Carlo Zarattini, Concretum Group / Swiss Finance Institute. Three SSRN papers verified:
  - Zarattini, C., Barbon, A. & Aziz, A. (2024). "A Profitable Day Trading Strategy For The U.S. Equity Market." [SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284) (SFI Research Paper No. 24-98).
  - Zarattini, C. & Aziz, A. (2023). "Can Day Trading Really Be Profitable?" [SSRN 4416622](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622).
  - Zarattini, C., Aziz, A. & Barbon, A. (2024). "Beat the Market: An Effective Intraday Momentum Strategy for SPY." [SSRN 4824172](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172).
- **Pagani — PARTIAL MISATTRIBUTION**: Alberto Pagani is a real Concretum Group co-author of Zarattini, but on **NON-ORB** papers (trend-following on stocks SSRN 5084316; crypto trend SSRN 5209907; factor-portfolio rebalancing SSRN 5747964; QuanTip intraday-trend overlay SSRN 6391638). No Pagani-authored ORB paper exists. Pagani is correctly recognized as a Zarattini collaborator but is NOT part of the ORB primary-literature chain.
- **Galli — UNVERIFIABLE**: searches across SSRN, ResearchGate, Concretum publication list, Semantic Scholar, IEEE Xplore, ScienceDirect returned no ORB-related paper authored by anyone named "Galli". Likely a hallucinated citation.
- **Saavedra — UNVERIFIABLE**: searches returned no ORB-related paper by "Saavedra". Likely a hallucinated citation.

**Replacement primary-source citation chain** for the ORB literature underpinning H052a (use these going forward):
- **Crabel, T. (1990).** *Day Trading with Short Term Price Patterns and Opening Range Breakout.* Greenville, SC: Traders Press. ISBN 0934380171. (Historical primary; pre-electronic-trading universe.)
- **Holmberg, U., Lönnbark, C. & Lundström, C. (2013).** "Assessing the profitability of intraday opening range breakout strategies." *Finance Research Letters* 10(1):27-33. [doi:10.1016/j.frl.2012.09.001](https://doi.org/10.1016/j.frl.2012.09.001). (Tier-1 peer-reviewed; S&P-500 + crude oil futures; significantly positive returns.)
- **Lundström, C.** (Umeå Economic Studies WP 845; [DiVA 732318](https://www.diva-portal.org/smash/get/diva2:732318/FULLTEXT02.pdf)). S&P-500 futures volatility-state conditioning; reports ~150 bp/day differential between high-vs-low-vol states. **CLOSEST PUBLISHED ANALOGUE** to the H052a HMM-regime composition.
- **Zarattini, C., Barbon, A. & Aziz, A. (2024).** [SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284). (Tier-2 SSRN working paper; ~7,000 single-name US equities; 5-min ORB primary with 15/30/60-min comparison.)
- **Tsai, Y.-C., Wu, M.-E., Syu, J.-H., Lei, C.-L., Wu, C.-S., Ho, J.-M. & Wang, C.-J. (2019).** "Assessing the Profitability of Timely Opening Range Breakout on Index Futures Markets." *IEEE Access* 7:32061-32071. [doi:10.1109/ACCESS.2019.2899852](https://doi.org/10.1109/ACCESS.2019.2899852). (Tier-1 peer-reviewed; DJIA, SP500, NASDAQ, HSI, TAIEX index futures 2003-2013; >8% annual / p<0.03 in all five markets.)

**Operational impact**: design.md §1 line 34 retains its frozen text for pre-reg-fidelity; this §15.1 erratum is the canonical citation chain going forward. Implementation code + KPI report card v1 (when emitted) MUST cite the verified primaries from this section, NOT the original four-name string.

**Disposition**: erratum-acknowledged-here; no §1 line 34 edit.

#### Erratum-2 (L-2; severity = major): "Unconditional ORB-on-futures is pre-supposed to be ≈null"

**Frozen text** (design.md §1 line 33): "H052a is NOT a rediscovery of ORB-on-futures. Unconditional ORB-on-futures is pre-supposed to be ≈null. H052a tests whether **regime-conditioning rescues an otherwise null signal**. A positive result would be surprising and carry large evidentiary weight against prior-art; a null is the expected outcome."

**Lit-check finding**: this pre-supposition is **CONTRADICTED by the peer-reviewed primary literature**:
- Holmberg-Lönnbark-Lundström 2013 (FRL doi:10.1016/j.frl.2012.09.001) reports significantly positive ORB returns on S&P-500 + crude oil futures.
- Tsai et al. 2019 (IEEE Access doi:10.1109/ACCESS.2019.2899852) reports >8% annual / p<0.03 on five index futures including S&P 500.

The "≈50% AUC" cite in §1 line 32 is to an internal SKIE Ninja README — Tier-5 evidence, not peer-reviewed.

**Reconciliation as project-internal prior** (per audit recommendation Path A): the §1 line 33 pre-supposition is **reframed** as a project-internal prior specific to the SKIE Ninja cost-aware constant-tick-slippage setup. The peer-reviewed lit reports gross-of-cost or modest-cost positive returns; the SKIE Ninja prior expects the per-tick slippage + commission overhead to attenuate the gross effect to ≈null on retail-size positions. The HMM-regime-conditioning is then the empirical content tested.

**Implications for H_1**: H_1 (T_H052a = SR_gated − SR_uncond > 0) is unchanged. The reconciliation affects only the §1 motivational framing — H_1 still tests whether HMM-gating adds value, regardless of whether the unconditional baseline is ≈null (project prior) or modestly positive (peer-reviewed lit). A positive T_H052a establishes "HMM-gating adds value over unconditional ORB" REGARDLESS of which baseline framing is correct.

**Disposition**: erratum-acknowledged-here; design.md §1 line 33 unchanged. Operator review at the KPI report card stage transition consults the realized unconditional ORB Sharpe (computed alongside the gated Sharpe per the design.md §1 paired-differential test statistic) for the actual baseline magnitude on H052a's substrate.

#### Erratum-3 (L-3; severity = major): Lundström vol-state-conditioning prior-art uncited

**Frozen text** (design.md §1 line 32): "Mechanism: ... [HMM emission state filtering of] high-noise days where even a true drift is swamped by microstructure noise."

**Closest published analogue** (uncited in §1): Lundström S&P-500 futures volatility-state conditioning (Umeå Economic Studies WP 845 / DiVA 732318) reports ~150 bp/day differential between high-vol and low-vol states on S&P-500 futures. This is the closest published analogue to the H052a HMM-regime composition: ORB profitability is regime-conditional at the volatility-state grain.

**Implications**: the H052a HMM-gate is **novel as a Gaussian-HMM composition** but stands on **Lundström's vol-state-conditioning prior-art**. This **strengthens** H052a's mechanistic motivation, NOT weakens it. The HMM-gate is a multi-state generalization (Gaussian-HMM with `n_states ≥ 2` per ADR-0005) of Lundström's binary-vol-state cut; the project's contribution is methodological (HMM toolkit replaces ad-hoc vol percentile cut) rather than mechanistic-novelty.

**Disposition**: erratum-acknowledged-here; design.md §1 line 32 unchanged. Implementation code + KPI report card MUST cite Lundström as prior-art alongside the H_1 test.

#### Erratum-4 (L-4; severity = minor): 60-min "first hour" OR window vs literature-canonical 5-min

**Frozen text** (design.md §1 line 31, §4 line 65, §11.5 prereq): "first-hour ORB long-only directional trade ... 10:30 ET ..."

**Lit-check finding**: the literature-canonical OR window is shorter than 60 minutes:
- Crabel 1990: 5/15/30-min OR
- Zarattini 2024 primary: 5-min OR (with 15/30/60-min comparison)
- Holmberg 2013: not pinned to 60-min
- Tsai 2019 TORB: volatility-pinned, not strict 60-min

The H052a 60-min OR window is operator-anchored to the **09:30-10:30 ET sibling QQQ-call window** (H052b first-hour 0DTE long-call scalp; documented in [research/01_hypothesis_register/H052b/design.md](../H052b/design.md)). It is **not** literature-canonical.

**Disposition**: erratum-acknowledged-here; the 60-min choice is preserved under pre-reg fidelity. A future successor hypothesis (or a `P1-H052A-OR-WINDOW-ROBUSTNESS-EXHIBIT` follow-up) MAY add 5/15/30-min OR robustness exhibits as ex-post diagnostics; this v1 reports the 60-min OR per the frozen pre-reg.

### 15.2 ADR-0014 §3.2 canonical end-of-simulation results-summary tables (MANDATORY)

Every H052a KPI report card from `kpi-report-emitted` forward MUST include the §"End-of-simulation results summary" section per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md): 9 tables + bottom-line prose at the top of the report card (between H1 + preamble and §"Methodological-correctness annotations"). Template at [research/_templates/kpi_results_summary_template.md](../../../research/_templates/kpi_results_summary_template.md). Reference realization: [H050 KPI report card v1](../H050/H050_kpi_report_v1.md) §"End-of-simulation results summary".

H052a sizing convention per ADR-0013 §3.1.1 row "First-hour ORB futures (H052a)": 100%-of-equity at ORB-trigger; position closed at end-of-first-hour or stop-out. The §3.2 simulator (forward 1-year projection) is daily-cleared session-cadence (sessions = trading days; n_sessions = 252) per ADR-0013 §3.1 + §3.1.2 — **avoids the bar-vs-session horizon mismatch that complicated H050's §3.1 forward projection** (per H050 v1 audit-remediate-loop F-Q-2 critical finding).

### 15.3 NinjaScript implementation plan (deferred to `P1-H052A-NINJASCRIPT-IMPL`)

H052a's NinjaScript implementation is **deferred** to follow-up `P1-H052A-NINJASCRIPT-IMPL`, which fires per **operator-discretionary review** of the canonical §3.2 9-table summary at end-of-simulation per the 2026-05-04 user directive.

Provisional structure (to be completed when the follow-up fires):

- **C# class name**: `HmmRegimeGatedFirstHourORB` (provisional)
- **C# file path**: `ninjascript/strategies/HmmRegimeGatedFirstHourORB.cs` (provisional)
- **Strategy parameters**: mapped from H052a.yaml — `or_window_minutes=60` + `pt_multiplier ∈ {0.5, 1.0, 1.5}` + `sl_multiplier ∈ {0.5, 1.0, 1.5}` + HMM cfg (`covariance_type ∈ {diag, full}`, `n_states` per ADR-0005 adaptive rule)
- **Entry logic**: long market order at 10:30 ET when (a) price > opening-range high AND (b) HMM forward-filter posterior `P(s_t = state_0 | y_{1:t_0}) > τ`; flat otherwise
- **Exit logic**: PT at `entry + k_pt × σ_60m`, SL at `entry - k_sl × σ_60m`, time-stop 14:00 ET, hard-close 15:55 ET (mirrors design.md §4)
- **Kill-switch parameters**: per design.md §11.1 (TBD)
- **Fill-log schema**: matches plan §6.1
- **Sim101 smoke-test record**: TBD when follow-up fires
- **Bridge-mediated implementation** per [ADR-0002](../../../docs/decisions/ADR-0002-bridge-selection.md) (HMM forward-filter requires Python inference at decision time per [ADR-0005 §"Fold-boundary state continuity"](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md))
- **Cross-reference**: this design.md + the canonical KPI report card v1 (TBD)

### 15.4 Cross-references

- ADR-0013 §5 (NinjaScript-mandate; 2026-05-04 operator-discretionary amendment) + §5.1 (NinjaScript Implementation section requirement) + §5.2 (bridge-mediated parity check) + §3.1 (Realized-OOS + Forward-Projection mandate) + §3.1.1 (sizing-convention table row "First-hour ORB futures")
- [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — canonical 9-table + bottom-line summary
- [docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md](../../../docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md) — Phase-0 ORB lit-check audit-remediate-loop trail (this commit)
- [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../H050/H050_kpi_report_v1.md) §15 — H050 erratum precedent (AFML §3.2 → §3.4 + Hamilton 1989 quarterly-GNP scope + B&B 2012 N=200 vs N=60)
- [research/01_hypothesis_register/H052b/design.md](../H052b/design.md) — sibling 0DTE QQQ first-hour long-call scalp (separate sibling repo `s-koirala/SKIE-NINJA-0DTE`)
