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

## 8. Gate thresholds (AMENDED 2026-05-20 per ADR-0017 + ADR-0018; supersedes the 2026-05-03 ADR-0013 amendment, which superseded the 2026-05-01 ADR-0012 amendment)

> **AMENDED 2026-05-20 by [ADR-0017 survival-constrained optimization paradigm](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §1.2 + §3 + §5 and [ADR-0018 regime-conditional aggressive-growth paradigm](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §D-1 + §D-2 + §D-3.** Sharpe-family metrics are DEMOTED from primary inferential anchor to secondary KPI; the survival-constrained metric vector (`terminal_wealth_q05`, `calmar_differential`, `profit_factor`, `r_multiple_mean`) replaces Sharpe-differential as the load-bearing operator-review artifact. MPPM(ρ=1) per [GISW 2007 *RFS* DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025) replaces Sharpe in inner-CV fitness. The §1 `T_H051 = SR_{pair, gated} − 0` Sharpe test statistic is PRESERVED VERBATIM as a SECONDARY KPI per ADR-0017 §1.2 — it is computed verbatim and reported as a numerical KPI in every H051 KPI report card; what changes is its promotion-decision-rule weight at the §8+§10 layer. The Johansen pre-screen and rolling-Johansen BH-FDR eligibility pre-condition (§1) is PRESERVED VERBATIM as a `prerequisite-not-met` Class A condition per ADR-0013 §1 + ADR-0017 §1.2. Full cascade text + K-1..K-8 kill-switch inheritance per ADR-0017 §5 + per-hypothesis applicability table in Appendix A at the end of this file.
>
> **AMENDED 2026-05-03 by [ADR-0013 permanent-exploration-no-archive-ninjascript-terminus](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).** ADR-0013 dissolves all binding gates: every former Class A item becomes a KPI annotation in the canonical KPI report card per ADR-0013 §3, with methodological-correctness annotation banner per §2.1 (NOT a gate). H051 progresses through the stage progression of ADR-0013 §1; operator promotion at every transition is discretionary on the KPI report card (ADR-0013 §5.3). Full §10 + new §15 NinjaScript Implementation cascade lands under follow-up `P1-ADR-0013-DESIGN-MD-CASCADE`.
>
> **ALL TEXT BELOW THIS BANNER IS HISTORICAL RECORD** preserved verbatim per ADR-0013 §4.1 non-loss mandate (per Round-2 audit F-2-5 remediation). For the current disposition philosophy and authoritative gating semantics see ADR-0013 §1-§5. The legacy "binding gates" / "Class A" / "three-class rubric" / disposition labels referenced below are SUPERSEDED and exist solely for audit-trail provenance.

Per [ADR-0012 disposition-philosophy-aspirational-mvp](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) (now superseded by ADR-0013) (per Round-1 audit F-1-2 + F-1-6 remediations re: applicability), H051's gating tree is restructured to the three-class rubric:

### 8.a Class A — Binding gates (per-hypothesis applicability)

- **PIT / leakage-canary** (ALWAYS BINDING). Binding test paths: Cycle-4 leak canary suite at [tests/unit/test_leak_canaries.py](../../../tests/unit/test_leak_canaries.py); per-hypothesis integration test [tests/integration/test_h051_pit.py](../../../tests/integration/test_h051_pit.py) to be authored as §11.2 prereq before next H051 launch (tracked under `P1-H051-PIT-CANARY-INTEGRATION-TEST-LANDED`).
- **Calibration: BSS / reliability** — `applicable: NO`. H051's pre-registered output is a Kalman-filtered hedge-ratio z-score gating a continuous pairs-trade entry; not a probability forecast.
- **Reproducibility log present** (ALWAYS BINDING).
- **DSR/PSR above `dsr_activation_size`** — `applicable: when family ≥ 10`.
- **Hansen SPA family p ≤ α at operator-promotion** per ADR-0012 §"Operator-promotion rule".

### 8.b KPIs (Class B; reported, not binding at design-time)

Sharpe-vs-passive CI (Lo 2002 / Mertens / Opdyke / LW2008), SPA family p (KPI at design-time, BINDING at promotion), max-DD ratio, power margin, Johansen pre-screen statistic. Defaults preserved (`alpha=0.05`, `bh_threshold=0.10`, `power_target=0.80`) — KPI-reported only.

## 9. Stopping rule

- Stop: fixed walk-forward fold count from `n_required_for_power_80` pilot. Underpowered status now recorded as a `power-margin-low` KPI annotation per ADR-0012, not an `archive(null)` verdict.
- Max wall-clock: 72 hours.
- Johansen pre-screen failure → `prerequisite-not-met` (Class A.4 per ADR-0012), not `archived(null, precondition-failed)`.

## 10. Decision rule (AMENDED 2026-05-20 per ADR-0017 + ADR-0018; supersedes the 2026-05-01 ADR-0012 amendment)

> **AMENDED 2026-05-20** per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md). The H051 decision rule is restructured to the survival-constrained metric vector + MPPM(ρ=1) inner-CV fitness layer. Operator review of the canonical ADR-0014 §3.2 13-table KPI report card is the load-bearing artifact. The legacy §1 T_H051 Sharpe statistic is preserved verbatim as a SECONDARY KPI (computed and reported in every emission). The Johansen pre-screen eligibility precondition remains a `prerequisite-not-met` Class A condition. Per ADR-0013 §5.3 + the user 2026-05-04 standing decline-ninjascript directive, the `kpi-report-emitted` → `ninjascript-implemented` transition is operator-discretionary. Full cascade text + per-hypothesis applicability in Appendix A.

The H051 decision rule is restructured per [ADR-0012 §"Disposition labels under the new rubric"](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) into the three-class disposition rubric (`leakage-detected` / `reproducibility-incomplete` / `calibration-failed` / `prerequisite-not-met` / `archive(complete; KPI report)`). All Sharpe / SPA / power outcomes are now Class B KPIs reported in the disposition memo's report card; they do NOT null the strategy. Johansen pre-screen failure is now `prerequisite-not-met` per ADR-0012 Class A.4.

## 11. Reproducibility commitments

- git HEAD: TBD at run.
- `uv pip freeze` sha: TBD at run.
- RNG seed: 20260421.
- Dataset checksums: frozen in `data_requirements.md` — pre-reg companion to be completed before `status=running`; its SHA256 checksum field is the binding artifact.
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json`.

## Appendix A — ADR-0017 + ADR-0018 cascade amendment (2026-05-20)

Per the BLOCKING-BEFORE-NEXT-STAGE-3-RUN follow-ups `P1-ADR-0017-DESIGN-MD-CASCADE` + `P1-ADR-0018-DESIGN-MD-CASCADE`, this appendix is the load-bearing reference for the 2026-05-20 amendment of §8 + §10 + §11.1 per Path A frozen-pre-reg amendment discipline ([ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Frozen pre-registration amendment"). §1-§7 are PRESERVED VERBATIM. The §1 `T_H051 = SR_{pair, gated} − 0` Sharpe test statistic is preserved as a SECONDARY KPI computed and reported verbatim in every KPI report card. The Johansen pre-screen eligibility precondition (§1) is PRESERVED VERBATIM.

### A.1 Primary inferential vector (replaces Sharpe at §8+§10 layer)

Per [ADR-0017 §1 + §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md), the load-bearing operator-review artifact becomes the survival-constrained metric vector with bootstrap CIs:

| Primary metric | Definition (per ADR-0017 §3) | KPI annotation grammar |
|---|---|---|
| `terminal_wealth_q05` | 5th percentile of 252-session bootstrap-forward $10K ending equity | `tw-q05-{above-baseline, above-half, below-half, below-quarter}` |
| `calmar_differential` | `Calmar_arm − Calmar_bench`; H051 benchmark = zero (per §1 H_1 `SR_{pair, gated} > 0`); paired-pairs block-stationary-bootstrap CI per [Politis-Romano 1994](https://doi.org/10.1080/01621459.1994.10476870) | `calmar-diff-{positive, marginal, negative}` |
| `profit_factor` | `gross_profit / gross_loss` per arm | `pf-diff-{positive, marginal, negative}` |
| `r_multiple_mean` | Per-trade R-multiple mean of distribution | `r-multiple-mean-{positive, marginal, negative}` |

Inner-CV fitness becomes **MPPM(ρ=1)** per [ADR-0018 §D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) ([GISW 2007 *RFS* 21(4) DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025)). Sharpe-family LW2008 differential CI + Hansen 2005 SPA p preserved as secondary KPIs at their existing ADR-0014 §3.2 table positions.

### A.2 Inner-CV fitness — MPPM(ρ=1)

For H051 hyperparameter selection across the Kalman transition variance scale `Q ∈ {1e-6, 1e-5, 1e-4}` and observation variance scale `R ∈ {1e-4, 1e-3}` per §5, fitness is **MPPM(ρ=1)** on per-session-aggregated log-return basket NOT Sharpe-differential. Kelly multiplier grid `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per ADR-0018 §D-2; super-Kelly cells `{1.5, 2.0, 2.5}` carry mandatory `super-kelly-operator-discretionary` annotation. BOCD decay detector per ADR-0018 §D-3.

### A.3 K-1..K-8 kill-switch inheritance (per ADR-0017 §5)

| # | Constraint (ADR-0017 §5) | H051 applicability |
|---|---|---|
| K-1 | Per-trade $-stop = 1.0R; `k=2.0` (Turtle 2N) | applicable; triple-barrier `pt_sl` per §4 implements the contract on the basis residual. |
| K-2 | Per-trade time-stop = 2× median winning-trade duration | applicable; `vertical_barrier` per §4 (`{30m, 60m, 120m}`). |
| K-3 | No-add-to-loser | applicable; single-position-per-pair convention. |
| K-4 | Per-symbol position cap per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) | applicable; ES leg + NQ leg each ≤ retail-capacity ceiling. |
| K-5 | Correlated-instrument inventory cap | **APPLICABLE** at H051 by construction — H051 trades the ES+NQ pair (or MES+MNQ); the cross-instrument exposure within a single arm is the strategy. The per-arm K-5 cap is `aggregate dollar-notional ≤ 1.0× the largest single-symbol cap`. K-5 also applies if the strategy adds the micro-pair (MES+MNQ) alongside the major-pair (ES+NQ) in a future amendment. |
| K-6 | Daily circuit breaker = -2% equity | applicable; runtime layer per ADR-0025 §D-1. |
| K-7 | Weekly circuit breaker = -5% equity | applicable; same. |
| K-8 | Adverse-direction entry filter | applicable-by-existing-gate; HMM gate + Johansen pre-screen + Kalman-residual z-score per §5 encode the entry-direction logic; K-8 spec satisfied. |

Kill-switch enforcement-mode per [ADR-0028 §D-1](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) — `block` default; `size_down` operator-opt-in.

### A.4 §11.1 Kill-switch parameters (NEW)

NinjaScript implementation kill-switch parameters (used at paper-trade-active and live stages, NOT during backtest):

- `K-1 per-trade $-stop` per the §4 triple-barrier `pt_sl` (1.0R on residual std).
- `K-2 per-trade time-stop` per §4 `vertical_barrier`.
- `K-3 no-add-to-loser`: enforced at sizing layer.
- `K-4 per-symbol position cap` per ADR-0001 retail-capacity ceiling (each leg).
- `K-5 correlated-instrument inventory cap`: aggregate dollar-notional ES+NQ (or MES+MNQ) ≤ 1.0× the largest single-symbol cap.
- `K-6 daily circuit breaker` = -2% equity.
- `K-7 weekly circuit breaker` = -5% equity.
- `K-8 adverse-direction entry filter`: structurally satisfied by HMM + Johansen + Kalman z-score gate per §5.

Calibrated post-paper-trade under follow-up `P1-H051-KILL-SWITCH-EMPIRICAL`.

### A.5 Revision-log

| Date | Amendment | Cross-reference |
|---|---|---|
| 2026-04-20 | Initial design.md commit, `status: designed` | git history initial commit |
| 2026-05-01 | §8 + §10 amended per ADR-0012 (superseded) | Phase D ADR-0012 amendment |
| 2026-05-03 | §8 + §10 amended per ADR-0013 (KPI-only) | [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) + Phase F |
| 2026-05-20 | §8 + §10 + §11.1 amended per ADR-0017 + ADR-0018 (this Appendix A); §1-§7 preserved verbatim; T_H051 secondary KPI | [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) + Phase O.19 audit trail at [docs/audits/audit_trail_2026-05-20_adr-0017-0018-design-md-cascade.md](../../../docs/audits/audit_trail_2026-05-20_adr-0017-0018-design-md-cascade.md) |

### A.6 §1-§7 immutability assertion

Per [ADR-0013 §"Frozen pre-registration amendment"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): §1-§7 are IMMUTABLE under project-level ADR amendments. This 2026-05-20 cascade amends ONLY §8 + §10 + §11.1. The §1 H_1 `T_H051 = SR_{pair, gated} − 0` test statistic and the §1 H_1 statement `Sharpe on OOS strictly greater than zero` are PRESERVED VERBATIM. The §1 Johansen pre-screen eligibility precondition (rolling-window BH-FDR adjustment at α=0.05; 60% rejection-rate threshold pre-registered from training-fold simulation) is PRESERVED VERBATIM.
