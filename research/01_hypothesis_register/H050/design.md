---
name: H050 — HMM regime-conditioned ES/NQ intraday directional signal
description: Pre-registered design doc for hypothesis H050
type: project
hypothesis_id: H050
tier: 2b
status: designed
owner: skoir
created: 2026-04-20
citations:
  - ADR-0003-spa-vs-romanowolf
  - ADR-0004-alpha-and-power-defaults
  - ADR-0005-hmm-regime-toolkit
  - ADR-0006-scope-extension-hmm-0dte
  - Hamilton 1989 (doi:10.2307/1912559)
  - Baum-Petrie-Soules-Weiss 1970 (doi:10.1214/aoms/1177697196)
  - Andersen-Bollerslev 1998 (doi:10.2307/2527343)
---

# H050 — HMM regime-conditioned ES/NQ intraday directional signal

This document is the pre-registration record for hypothesis H050. Frozen at `designed`; any change requires a new hypothesis ID.

## 1. Hypothesis

- H0: Inside the HMM-decoded state `s*` identified on the training fold, the realized Sharpe of the directional signal does not exceed the Sharpe of the unconditional version of the same signal. Formally `SR_{s*} - SR_uncond ≤ 0` on the OOS test fold.
- H1: `SR_{s*} - SR_uncond > 0` on the OOS test fold; one-sided test at alpha per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).
- Mechanism: regime-dependent drift in equity-index futures; states identified by vol + flow + skew features concentrate directional predictability ([Hamilton 1989](https://doi.org/10.2307/1912559); [Guidolin & Timmermann 2007, JEDC 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004); [Ryou, Bae, Lee, Oh 2020, Sustainability 12(17):7031](https://doi.org/10.3390/su12177031)).
- Primary citations: [Hamilton 1989](https://doi.org/10.2307/1912559), [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196), [Andersen & Bollerslev 1998, Int. Econ. Rev.](https://doi.org/10.2307/2527343).
- Test statistic: `T_H050 = SR_{filtered, gated} − SR_{filtered, unconditional}`, where both Sharpe ratios are computed on walk-forward OOS net-of-cost returns. Enters Romano-Wolf step-down family (per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md)) with `T_H050` as a paired-differential statistic.

## 2. Universe and sample period

- Instruments: ES and NQ front-month per [config/instruments.yaml](../../../config/instruments.yaml); roll-handling per that file's calendar.
- Frequency: 1-minute bars as the base grid; HMM observation cadence selected by BIC over `{1m, 5m, 15m}` inside the train fold.
- Session: RTH only. ETH is a separate regime per project CLAUDE.md and will be addressed in a sibling hypothesis if H050 passes.
- Train window: 2015-01-01 through 2022-12-31 (calendar bounds; walk-forward splits applied within).
- Validation window: 2023-01-01 through 2023-12-31, embedded as inner folds of walk-forward.
- Test window: 2024-01-01 through 2025-12-31, strictly held out until final SPA submission.
- Roll-handling note: front-month, back-adjusted via CME calendar; roll dates frozen at pre-reg.
- Dataset snapshot frozen at pre-registration: SHA256 of `{ES 1-min bars 2010–2023-12-31; NQ 1-min bars same}` captured in `data_requirements.md` at `status=designed`. Any data after 2025-12-31 is locked away; re-runs on extended windows require a successor hypothesis ID.

## 3. Features

- `rv_parkinson@1.0` — realized variance, Parkinson estimator (training-fold lookback selected by CV).
- `rv_realized@1.0` — squared-returns realized variance ([Andersen & Bollerslev 1998](https://doi.org/10.2307/2527343)).
- `realized_skew@1.0` — third central moment, standardized.
- `ofi_tickrule@1.0` — order-flow-imbalance proxy via tick rule (Lee-Ready), dependent on H010 deliverable when MBP-10 is available; falls back to tick-rule proxy until then (dependency flagged in `data_requirements.md`).
- Leakage tests per plan §3 and §4.6 must pass before run.

## 4. Label construction

Triple-barrier per Lopez de Prado AFML §3.2.

- `pt_sl`: symmetric around volatility, multiplier selected by walk-forward CV over `{1.0, 1.5, 2.0}` on the train fold.
- `vertical_barrier`: `{30m, 60m, 120m}` grid, selected by same CV.
- `volatility_estimator`: Yang–Zhang with lookback selected by CV over `{20, 60, 120}` minutes.
- Meta-label horizon upper bound: max of selected `vertical_barrier` across folds; fed to splitter `purge`.

## 5. Estimator

- Model class: directional classifier composed with HMM regime-gate. Base classifier is gradient-boosted trees (LightGBM) trained on features in §3. HMM per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md): Gaussian emissions, `covariance_type ∈ {diag, full}`, `n_states` grid per ADR-0005 adaptive rule (lower bound 2; upper bound K_max such that mean within-state sample size ≥ 30 × dim(emission) on train fold), selection by BIC + CV log-likelihood.
- Canonical state ordering at each walk-forward fit: states sorted by emission-mean of the primary directional feature (ES log-return) **ascending**; gate state = highest-mean state (directional-drift convention per ADR-0005).
- State assignment at inference (decision) time uses the causal forward filter `p(s_t | y_{1:t})` only; smoothed posteriors `p(s_t | y_{1:T})` are used solely as a training-fold diagnostic and never inform an out-of-sample decision. A leakage unit test asserts filter output at `t` is a pure function of `y_{1:t}`.
- Hyperparameter grid: pre-registered. LightGBM `num_leaves ∈ {15, 31, 63}`, `learning_rate ∈ {0.01, 0.05}`, `min_data_in_leaf ∈ {20, 50}`.
- Search protocol: random search with fixed seed; N_draws = 200 per walk-forward fold, chosen to give ≥95% expected coverage of the top-5% configuration per [Bergstra & Bengio 2012, JMLR 13:281–305](https://www.jmlr.org/papers/v13/bergstra12a.html); per-config max-iter EM budget = 500 with convergence tolerance 1e-4; grid points exceeding this cap are recorded as right-censored in diagnostics, not dropped. Nested walk-forward; no single-split tuning.
- Loss / metric: logistic loss for training; Sharpe for gate evaluation.

## 6. Splitter

- Splitter: `PurgedWalkForwardSplitter` per plan §4.1.
- `embargo`: max of residual-PACF-based lag and Politis–White optimal block length on stacked residuals.
- `purge`: `max(vertical_barrier)` across CV-selected folds.
- CPCV not used for H050; if statistical power is insufficient after fold-count selection, escalation to CPCV is registered as a design-change requiring a new hypothesis ID.

## 7. Cost model

- `cost_model_id`: `nt8_es_nq_rth_v1` (to be registered in `src/skie_ninja/backtest/costs/`; placeholder until commit lands).
- Commission: per-contract commission from [config/instruments.yaml](../../../config/instruments.yaml) (CME-cited fees).
- Slippage: regime-conditional (RTH only for H050), fit walk-forward from paper-trade logs once the TrivialSmokeTest run completes; until then, a conservative constant-tick slippage prior is used with sensitivity analysis.

## 8. Gate thresholds (AMENDED 2026-05-03 per ADR-0013; supersedes the 2026-05-01 ADR-0012 amendment)

> **AMENDED 2026-05-03 by [ADR-0013 permanent-exploration-no-archive-ninjascript-terminus](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).** ADR-0013 dissolves all binding gates: every former Class A item becomes a KPI annotation in the canonical KPI report card per ADR-0013 §3, with methodological-correctness annotation banner per §2.1 (NOT a gate). H050 progresses through the stage progression of ADR-0013 §1; operator promotion at every transition is discretionary on the KPI report card (ADR-0013 §5.3). Full §10 + new §15 NinjaScript Implementation cascade lands under follow-up `P1-ADR-0013-DESIGN-MD-CASCADE`.
>
> **ALL TEXT BELOW THIS BANNER IS HISTORICAL RECORD** preserved verbatim per ADR-0013 §4.1 non-loss mandate (per Round-2 audit F-2-5 remediation). For the current disposition philosophy and authoritative gating semantics see ADR-0013 §1-§5. The legacy "binding gates" / "Class A" / "three-class rubric" / disposition labels (`archive(complete; KPI report)`, `calibration-failed`, `leakage-detected`, `reproducibility-incomplete`) referenced below are SUPERSEDED and exist solely for audit-trail provenance.

Per [ADR-0012 disposition-philosophy-aspirational-mvp](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) (now superseded by ADR-0013), H050's gating tree is restructured to the three-class rubric: binding gates (Class A: PIT/leakage + BSS + reliability + reproducibility + DSR-when-active), KPIs (Class B: Sharpe-vs-passive, SPA family p, max-DD ratio, power margin, etc.), and documentation requirements (Class C). See ADR-0012 for the full rubric specification.

**Closure note**: H050 has no aggregate disposition (per [docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md](../../../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md) §2 — 6 of 7 prod-run-ids have zero on-disk aggregate artifacts; all 6 production walk-forward attempts failed for infrastructure reasons before reaching the disposition tree). The ADR-0012 amendment is **prospective**: any future H050 re-launch (e.g., after the H050 BLOCKING follow-ups close per `P1-PREFLIGHT-USOSVC-TASK-DISABLE` + ADR-0010 framing) will use the three-class disposition rubric, not the legacy Sharpe-CI gating tree retained in §8.b below.

### 8.a Class A — Binding gates (per ADR-0012; per-hypothesis applicability)

Per ADR-0012 §"Class A" + Round-1 audit F-1-2 + F-1-6 remediations:

- **PIT / leakage-canary** (ALWAYS BINDING). Binding integration test paths for H050: [tests/unit/test_leak_canaries.py](../../../tests/unit/test_leak_canaries.py) (Cycle-4 fold-boundary monotonicity + label-purge horizon + dual-fit observer + TracingArray detectors). Binding feature-factory test path: [tests/integration/test_h050_pit.py](../../../tests/integration/test_h050_pit.py) (to be authored as a §11.2 prereq before next H050 launch; tracked under new follow-up `P1-H050-PIT-CANARY-INTEGRATION-TEST-LANDED`).
- **Calibration: BSS > 0** — `applicable: NO` for H050. H050's pre-registered output is a continuous trading-rule directional signal, not a calibrated probability forecast. The underlying classifier (LightGBM logistic in §5) MAY be calibrated as a KPI annotation but does not bind.
- **Calibration: reliability slope ∈ [0.7, 1.3]** — `applicable: NO` for H050 (same rationale).
- **Reproducibility log present** (ALWAYS BINDING). git_head + dataset_checksum + scientific_payload_sha256 + pip_freeze sha.
- **DSR/PSR above `dsr_activation_size`** — `applicable: when family ≥ 10`. Currently no-op (family=7).
- **Hansen SPA family p ≤ α at operator-promotion** (BINDING at promotion-gate per ADR-0012 §"Operator-promotion rule"; not at design-time disposition).

### 8.b KPIs (per ADR-0012; reported, not nulling)

Sharpe-vs-passive CI (Lo 2002 / Mertens / Opdyke / LW2008), Hansen SPA family p, max-DD ratio, power margin, HMM stationarity diagnostic, regime-state coverage statistics.

### 8.c Defaults (preserved from legacy)

- `alpha`: 0.05 (one-sided). KPI-reported only; no longer a binding gate.
- `bh_threshold`: 0.10. Same.
- `dsr_activation_size`: project default per [config/gate.yaml](../../../config/gate.yaml).
- Power target: 0.80. KPI-reported only.

### 8.d Legacy reference (the original H050 §8 + §10 spec, retained for archival traceability)

The pre-ADR-0012 H050 §8 + §10 was a Sharpe-CI gating tree archiving null on: CI covers zero, SPA fails, underpowered, HMM stationarity precondition fails. None of these gates were ever evaluated (per the post-mortem); the ADR-0012 amendment is therefore prospective. The H050 SPA family entry per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md) is preserved for KPI-reporting purposes.

## 9. Stopping rule

- Stop criterion: fixed walk-forward fold count equal to `n_required_for_power_80` computed from the pilot training-fold Sharpe dispersion.
- Max folds: computed at pre-reg time from pilot; bounded above by calendar-window limit.
- Search budget exceedance (per §5 random-search cap) is recorded as right-censoring in the selection log, not a halt.

## 10. Decision rule (AMENDED 2026-05-01 per ADR-0012)

The H050 decision rule is restructured per [ADR-0012 §"Disposition labels under the new rubric"](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) into the three-class disposition rubric (`leakage-detected` / `reproducibility-incomplete` / `calibration-failed` / `prerequisite-not-met` / `archive(complete; KPI report)`).

The legacy §10 spec (Sharpe-CI null + SPA-fail null + underpowered null + HMM-stationarity-precondition-failed null) is superseded. All Sharpe / SPA / power / max-DD outcomes are now Class B KPIs reported in the disposition memo's report card; they do NOT null the strategy. The HMM stationarity pre-check remains a precondition (per ADR-0005) but failure now produces `prerequisite-not-met` (Class A.4 per ADR-0012), not `archive(null, precondition-failed)`.

**Closure status**: H050 has no aggregate disposition; the legacy §10 was never reached. The ADR-0012 amendment is prospective for any future re-launch.

## 11. Reproducibility commitments

- git HEAD (at run): TBD at execution.
- `uv pip freeze` sha (at run): TBD at execution.
- RNG seed: 20260420.
- Dataset checksums (frozen at pre-reg): captured in `data_requirements.md` alongside this file — the file is a pre-reg companion to be completed before `status=running`; its SHA256 checksum field is the binding artifact.
- Reproducibility log path: `logs/reproducibility/{run_id}.json`
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json` per ADR-0005.
