---
name: H051 — HMM-gated ES/NQ (or MES/MNQ) basis pairs trade
description: Pre-registered design doc for hypothesis H051
type: project
hypothesis_id: H051
tier: 2b
status: designed
owner: skoir
created: 2026-04-20
citations:
  - ADR-0003-spa-vs-romanowolf
  - ADR-0004-alpha-and-power-defaults
  - ADR-0005-hmm-regime-toolkit
  - ADR-0006-scope-extension-hmm-0dte
  - Johansen 1991 (doi:10.2307/2938278)
  - West & Harrison 1997 DLM textbook
---

# H051 — HMM-gated ES/NQ basis pairs trade

Pre-registration for hypothesis H051. Frozen at `designed`.

## 1. Hypothesis

- H0: An HMM-gated entry on the z-score of the Kalman-filtered hedge-ratio residual between ES and NQ (or MES/MNQ) front-month futures does not produce a Sharpe strictly greater than zero on OOS after realistic costs.
- H1: Sharpe on OOS strictly greater than zero; one-sided at alpha.
- Mechanism: short-horizon mean-reversion in the basis conditioned on a liquidity / low-vol regime; residual dynamics are only approximately stationary inside specific regimes ([Hamilton 1989](https://doi.org/10.2307/1912559)).
- Primary citations: [Johansen 1991, Econometrica](https://doi.org/10.2307/2938278); Kalman hedge-ratio estimation per West & Harrison 1997 *Bayesian Forecasting and Dynamic Models*, 2nd ed., Springer, ISBN 978-0387947259 (publisher-page ISBN confirmation pending); Chan 2013 *Algorithmic Trading: Winning Strategies and Their Rationale*, Wiley, ISBN 978-1118460146, Ch. 3 (publisher-page ISBN confirmation pending).
- Test statistic: `T_H051 = SR_{pair, gated} − 0`, benchmark zero. Enters SPA / Romano-Wolf family per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md).

**Cointegration eligibility pre-screen** — Johansen trace statistic at 5% critical value per [Osterwald-Lenum 1992, Oxford Bull. Econ. Stat. 54(3):461–472](https://doi.org/10.1111/j.1468-0084.1992.tb00013.x) critical values. Rolling windows of length `L_train` (= first training-fold length) with step = purge-length; Benjamini-Hochberg adjustment across rolling windows (α=0.05). Eligibility requires BH-adjusted rejection in ≥60% of windows, where the 60% threshold is pre-registered from training-fold simulation: the lowest fraction at which synthetic cointegrated series (generated under the training-period estimated VECM) are detected with power ≥ 0.80 at α=0.05. Simulation code path and seed logged. If eligibility fails, the run halts with `archived(null, precondition-failed)` before any HMM fit.

## 2. Universe and sample period

- Instruments: ES/NQ front-month (primary) with MES/MNQ as a retail-capacity mirror. Pair is traded as a dollar-neutral Kalman-hedged basis.
- Frequency: 5-minute bars; finer grids rejected to keep transaction costs tractable.
- Session: RTH only.
- Train / validation / test windows: same calendar bounds as H050.
- Dataset snapshot frozen at pre-registration: SHA256 of `{ES 1-min bars 2010–2023-12-31; NQ 1-min bars same}` captured in `data_requirements.md` at `status=designed`. Any data after 2025-12-31 is locked away; re-runs on extended windows require a successor hypothesis ID.

## 3. Features

- `basis_residual@1.0` — Kalman-filtered residual between ES and NQ log-prices, hedge ratio as the Kalman state.
- `residual_zscore@1.0` — rolling-standardized residual; rolling window selected by CV.
- `johansen_screen@1.0` — rolling Johansen trace statistic with BH adjustment (see §1 for critical-value source and eligibility threshold derivation); emits a boolean eligibility flag per bar. Bonferroni control removed.
- Leakage tests per plan §3 and §4.6.

## 4. Label construction

Triple-barrier applied to the basis (not to either leg).

- `pt_sl`: symmetric in residual standard deviations; multiplier from CV grid `{0.5, 1.0, 1.5}`.
- `vertical_barrier`: `{30m, 60m, 120m}` grid; CV-selected.
- `volatility_estimator`: rolling sd of Kalman residual with lookback CV-selected.
- Meta-label horizon upper bound → splitter purge.

## 5. Estimator

- Model class: Kalman filter over hedge ratio + HMM over standardized residual.
- Kalman initialization: `β₀` = OLS hedge ratio on the first K bars of each train fold; K selected by CV on one-step-ahead filtering RMSE within the train fold. `P₀` = diffuse initialization (variance 10× Var(β_OLS)) per [Durbin & Koopman 2012, *Time Series Analysis by State Space Methods*, 2nd ed., Oxford](https://doi.org/10.1093/acprof:oso/9780199641178.001.0001). All rolling-Johansen windows lie strictly within the training fold; purge and embargo apply identically.
- State assignment at inference (decision) time uses the causal forward filter `p(s_t | y_{1:t})` only; smoothed posteriors `p(s_t | y_{1:T})` are used solely as a training-fold diagnostic and never inform an out-of-sample decision. A leakage unit test asserts filter output at `t` is a pure function of `y_{1:t}`.
- HMM per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md): Gaussian emissions, `covariance_type ∈ {diag, full}`, `n_states` grid per ADR-0005 adaptive rule, BIC + CV selection.
- Entry gate: operationalized via posterior probability of the BIC-selected "low-vol / high-persistence" state; the probability threshold is selected by training-fold ROC-optimal Youden point, not hand-picked. Labeling of the gate state uses the canonical ordering rule from ADR-0005 (emission-variance rank ascending).
- Hyperparameter grid: Kalman transition variance scale `Q ∈ {1e-6, 1e-5, 1e-4}`, observation variance scale `R ∈ {1e-4, 1e-3}`.
- Search protocol: grid inside nested walk-forward.
- Loss / metric: log-likelihood for Kalman/HMM fit; Sharpe for gate evaluation.

## 6. Splitter

- `PurgedWalkForwardSplitter` per plan §4.1.
- `embargo`: max of residual-PACF lag and Politis–White optimal block length.
- `purge`: `max(vertical_barrier)` across CV-selected folds.

## 7. Cost model

- `cost_model_id`: `nt8_es_nq_pair_rth_v1` (placeholder, to be registered).
- Commission: two legs, per-contract fee from [config/instruments.yaml](../../../config/instruments.yaml).
- Slippage: regime-conditional, walk-forward fit; constant-tick prior until paper-trade logs accumulate.

## 8. Gate thresholds

Defaults per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md). SPA family per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md).

- `alpha`: 0.05.
- `bh_threshold`: 0.10.
- Power target: 0.80.

## 9. Stopping rule

- Stop: fixed walk-forward fold count from `n_required_for_power_80` pilot.
- Max wall-clock: 72 hours.
- Pre-screen failure → halt with `archived(null, precondition-failed)`.

## 10. Decision rule

- `passed=True` → archive(positive); paper-trade eligibility.
- `passed=False` with CI excluding zero, SPA failing → archive(null) with multiple-testing note.
- `passed=False` with CI covering zero → archive(null).
- Underpowered → archive(null, underpowered).
- Johansen pre-screen rejects → archive(null, precondition-failed).

## 11. Reproducibility commitments

- git HEAD: TBD at run.
- `uv pip freeze` sha: TBD at run.
- RNG seed: 20260421.
- Dataset checksums: frozen in `data_requirements.md` — pre-reg companion to be completed before `status=running`; its SHA256 checksum field is the binding artifact.
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json`.
