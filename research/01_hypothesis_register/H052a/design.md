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

## 8. Gate thresholds (AMENDED 2026-05-01 per ADR-0012)

Per [ADR-0012 disposition-philosophy-aspirational-mvp](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) (per Round-1 audit F-1-2 + F-1-6 remediations re: applicability), H052a's gating tree is restructured to the three-class rubric:

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

**AMENDMENT 2026-05-03 per [ADR-0014 never-archive-profitable-strategies](../../../docs/decisions/ADR-0014-never-archive-profitable-strategies.md)**:

The disposition-class labels per [ADR-0012](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) §10.1 strict precedence (`leakage-detected`, `reproducibility-incomplete`, `calibration-failed`, `prerequisite-not-met`) are STATES indicating remediation-pending status — they are NOT archive decisions. The ONLY archive labels are `archive(complete; KPI report)` and `archive(null, <reason>)`.

A new `lifecycle_state` field is emitted alongside `disposition_class` per ADR-0014; the lifecycle_state values are:
- `paper-trade-eligible` — Class A gates pass; auto-promotion eligible
- `active-investigation` — Class A gate failure(s) AND/OR remediation-pending; **default state**
- `archived` — set ONLY by operator decision via `compose_disposition(explicit_archive=True)` per ADR-0014 §8 NEVER ARCHIVE AUTONOMOUSLY

Profitable strategies (annualized return > 0% AND Sortino > 0 AND profit factor > 1.0) STAY in `active-investigation` regardless of Class A gate failures per ADR-0014 §2 NEVER-ARCHIVE-PROFITABLE-STRATEGIES. The `archive(null, data-violation)` rule above (raw vs roll-adjusted data) is preserved as an explicit operator-promotion guard, NOT an autonomous archive — under ADR-0014 §8 a data-violation finding sets `lifecycle_state = active-investigation` until operator review.

Phase-end summaries must report the strategy-performance dashboard per ADR-0014 §9 (annualized Sharpe + Sortino + Calmar + max DD + win rate + profit factor + Hansen SPA p + LW2008 ΔSharpe vs passive); the canonical template is at [research/_templates/phase_performance_report.md](../../_templates/phase_performance_report.md).

§1-§7 of this design (hypothesis statement, universe/sample, features, labels, splitter, cost model) remain IMMUTABLE per ADR-0012 §"Frozen pre-registration amendment" carve-out conditions (d).

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
