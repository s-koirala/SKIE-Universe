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

## 15. NinjaScript Implementation (NEW per [ADR-0013 §5.1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), 2026-05-03)

Per ADR-0013 §5 + §5.1, every hypothesis design.md gains a §15 enumerating the NinjaScript C# implementation that is the terminal state of the research loop. H050's NinjaScript implementation is sequenced AFTER the production walk-forward Stage-3 KPI report card emission per follow-up `P1-H050-NINJASCRIPT-IMPL`.

This section is also the venue for **citation-erratum acknowledgments** per ADR-0013 §"Frozen pre-registration amendment" (§1-§7 of this design.md are immutable; corrections to citation defects in §1-§7 are documented here without editing the original §-text).

### 15.1 Citation errata (Round-1 audit-remediate-loop 2026-05-03 findings F-L-1, F-L-3, F-L-4)

The following citation defects were surfaced by Round-1 of the H050 orchestrator leakage-clean audit-remediate-loop ([docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md)). They are recorded here per the §1-§7 immutability discipline:

#### Erratum-1 (F-L-1; severity = major): AFML §3.2 → §3.4

**Frozen text** (design.md §4 line 53): "Triple-barrier per Lopez de Prado AFML §3.2."

**Correct citation**: López de Prado, M. (2018). *Advances in Financial Machine Learning*, Wiley, ISBN 978-1-119-48208-6, **§3.4** "The Triple-Barrier Method" (p. 45). §3.2 is "The Fixed-Time Horizon Method" — a different, weaker labelling scheme. The triple-barrier is in §3.4.

**Operational impact**: NONE. The orchestrator at [scripts/run_walk_forward.py:14-22](../../../scripts/run_walk_forward.py) cites AFML §3.4 correctly and explicitly flags the design.md §4 line 53 reference as "an inherited erratum, preserved by Path-A pre-reg immutability." The triple-barrier labels emitted by [src/skie_ninja/features/labels.py](../../../src/skie_ninja/features/labels.py) implement §3.4, NOT §3.2.

**Disposition**: erratum-acknowledged-here; no §4 line 53 edit.

#### Erratum-2 (F-L-3; severity = major): Hamilton 1989 scope

**Frozen text** (design.md §1 line 28): "Mechanism: regime-dependent drift in equity-index futures... ([Hamilton 1989](https://doi.org/10.2307/1912559); ...)."

**Verified scope**: Hamilton, J. D. (1989). *Econometrica* 57(2):357-384. The paper estimates Markov regime-switching on **quarterly US real GNP** (1951Q2-1984Q4) — a macroeconomic application. The intraday extrapolation to ES/NQ futures is NOT directly supported by Hamilton 1989 alone.

**Mitigation**: design.md §1 line 28 also cites [Guidolin & Timmermann 2007, JEDC 31(11):3503-3544](https://doi.org/10.1016/j.jedc.2006.12.004) (multi-asset regime-switching at monthly frequency) and [Ryou-Bae-Lee-Oh 2020, Sustainability 12(17):7031](https://doi.org/10.3390/su12177031) (HMM momentum on equity returns). These co-citations bridge Hamilton's macro framework to financial-return regime-switching but at monthly-and-above frequencies. Intraday-1-min HMM stationarity is a project-level methodological commitment tracked under follow-up `P1-CYCLE6-FOLD-STATIONARITY`.

**Disposition**: erratum-acknowledged-here; design.md §1 line 28 unchanged. Operator review at the KPI report card stage transition consults the empirical HMM stationarity diagnostic for the actual evidence on intraday regime-switching.

#### Erratum-3 (F-L-4; severity = major): Bergstra & Bengio 2012 N=200 vs N=60

**Frozen text** (design.md §5 line 66): "N_draws = 200 per walk-forward fold, chosen to give ≥95% expected coverage of the top-5% configuration per Bergstra & Bengio 2012, JMLR 13:281-305."

**Verified derivation**: B&B 2012 §2.2's volume-coverage argument gives `N ≥ ceil(log(1-p) / log(1-v))` for top-fraction `v` and target probability `p`. For `(v=0.05, p=0.95)`, the threshold is **N ≥ 59** (the canonical "60-trial" B&B result). N=200 is heavy oversampling rather than a B&B-dictated coverage requirement. The argument is dimension-INDEPENDENT (a volume measure on the search space).

**Operational note**: The H050 LightGBM grid is a 12-cell discrete product (`3 × 2 × 2`); over a 12-cell grid, N=200 random samples cover the grid with high replicate-density rather than B&B-style volume coverage of a continuous space. The orchestrator's docstring at [scripts/run_walk_forward.py:580-595](../../../scripts/run_walk_forward.py) already documents this gap; empirical N_draws calibration is tracked under follow-up `P1-H050-LGB-N-DRAWS-EMPIRICAL`.

**Disposition**: erratum-acknowledged-here; N=200 preserved under pre-reg fidelity; calibration tracked separately.

### 15.2 NinjaScript implementation plan (deferred to `P1-H050-NINJASCRIPT-IMPL`)

H050's NinjaScript implementation is **deferred** to follow-up `P1-H050-NINJASCRIPT-IMPL`, which fires AFTER the production walk-forward Stage-3 KPI report card v1 emission per ADR-0013 §"Follow-ups". The C# strategy will be **bridge-mediated** per ADR-0013 §1.2 (the HMM regime-gate requires Python inference at runtime; no native C# HMM library covers the warm-start `filter_states_from_prior` causal path).

Provisional structure (to be completed when the follow-up fires):

- **C# class name**: `HmmRegimeConditionedDirectionalSignal` (provisional; final name TBD)
- **C# file path**: `ninjascript/strategies/HmmRegimeConditionedDirectionalSignal.cs` (provisional)
- **Strategy parameters**: mapped from H050.yaml `classifier.grid` (LightGBM hyperparameters chosen by inner-CV at the canonical run) + HMM cfg (`covariance_type`, `n_states`)
- **Entry / exit logic**: 1:1 with Python signal generation per [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) `_predict_fold` (line 1564-1653)
- **Kill-switch parameters**: `max-drawdown-percent`, `max-position-duration-bars`, `max-loss-per-trade-ticks` (defaults per CLAUDE.md §Standing constraints retail-size ceiling)
- **Fill-log schema**: matches plan §6.1
- **Sim101 smoke-test record**: TBD when follow-up fires
- **Cross-reference**: this design.md + the canonical KPI report card v1 (TBD)

### 15.3 Sizing convention (per ADR-0013 §3.1.1)

H050 archetype: **HMM-gated multi-bar intraday** (per ADR-0013 §3.1.1 table). Sizing convention: per-state position multiplier × 100%-of-equity-when-active; equity unchanged when state-gated-out. Specifically:
- When the HMM forward-filter posterior places the high-mean state as the modal state at bar `t`, position size is `sign(2·p_classifier - 1) × 100%` of equity.
- When the HMM forward-filter posterior places any other state as the modal state, position size is 0.
- Equity is updated multiplicatively: `equity_{t+1} = equity_t × exp(r_t)` where `r_t` is the per-bar log return of the gated-vs-unconditional differential (test statistic per design.md §1).

This sizing convention will inform the §3.1 Realized OOS + Forward-Projection block of the H050 KPI report card v1 when the production walk-forward run completes.

### 15.4 Cross-references

- ADR-0013 §5 — NinjaScript-mandate; §5.1 NinjaScript Implementation section requirement; §5.2 bridge-mediated parity check; §3.1 Realized-OOS + Forward-Projection mandate; §3.1.1 sizing-convention table
- [research/01_hypothesis_register/H050/purge_rule_addendum_2026-05-03.md](purge_rule_addendum_2026-05-03.md) — per-cfg purge ratification (F-Q-2 closure)
- [research/01_hypothesis_register/H050/embargo_pw2004_addendum_2026-05-03.md](embargo_pw2004_addendum_2026-05-03.md) — PW2004 embargo project-operational framing (F-L-2 closure)
- [docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md) — Round-1 + Round-2 + Round-3 audit-remediate-loop trail
