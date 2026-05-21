---
name: H050.invert — HMM regime-conditioned ES/NQ intraday directional signal with INVERTED gate-state selection
description: Pre-registered design doc for hypothesis H050.invert; genetic successor to H050
type: project
hypothesis_id: H050_invert
parent_hypothesis_id: H050
tier: 2b
status: designed
owner: skoir
created: 2026-05-20
citations:
  - ADR-0005-hmm-regime-toolkit
  - ADR-0013-permanent-exploration-no-archive-ninjascript-terminus
  - ADR-0017-survival-constrained-optimization-paradigm
  - ADR-0018-regime-conditional-aggressive-growth-paradigm
  - ADR-0019-barbell-payoff-shape-screening
  - ADR-0022-causal-mechanism-vs-correlation-only-annotation
  - ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical
  - ADR-0025-abandonment-trigger-infrastructure
  - ADR-0026-paradigm-and-reporting-refinements
  - ADR-0027-operational-discipline-bounded-exploration
  - ADR-0028-k6-k7-size-down-cost-friction-edge
  - Hamilton 1989 (doi:10.2307/1912559)
  - Baum-Petrie-Soules-Weiss 1970 (doi:10.1214/aoms/1177697196)
  - Andersen-Bollerslev 1998 (doi:10.2307/2527343)
  - Rabiner 1989 (doi:10.1109/5.18626)
---

# H050.invert — HMM regime-conditioned ES/NQ intraday directional signal with INVERTED gate-state selection

This document is the pre-registration record for hypothesis H050.invert. Frozen at `designed`; any change requires a new hypothesis ID per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Frozen pre-registration amendment".

H050.invert is a **genetic successor** to H050 v1 per [ADR-0027 §D-4 genetic-successor discipline](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md). Empirical motivation per the [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md) §7.3 Variant A. See §17 revision-log for the 4-field cross-citation.

## 1. Hypothesis

- H0: Inside the HMM-decoded LOW-EMISSION-MEAN state `s_low` identified on the training fold (i.e., the state DISCARDED by H050 v1's canonical highest-mean gating), the realized Sharpe of the directional signal does not exceed the Sharpe of the unconditional version of the same signal. Formally `SR_{s_low} − SR_uncond ≤ 0` on the OOS test fold.
- H1: `SR_{s_low} − SR_uncond > 0` on the OOS test fold; one-sided test at alpha per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).
- Mechanism: per the parent-H050 INVESTIGATE-FAILURE-MODE closure memo §6.1, on both ES and NQ the HMM canonical state-ordering rule (`gate = highest-mean state` per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)) empirically selects a state with WORSE per-bar Sharpe than the discarded low-mean state on the unconditional return series (ES: SR_state1_uncond=−0.0147 vs SR_state0_uncond=+0.00061; NQ analogous pattern). H050.invert tests the **H-b anti-selection sub-hypothesis** by inverting the gate selection: `gate = lowest-mean state`. If H-b dominates the H050 catastrophe, the inverted gate produces non-negative realized OOS edge. If the H-c whipsaw mechanism dominates instead (per the same memo §6.3 + §6.6), the inverted gate STILL whipsaws at ~30% transition rate (ES) and produces comparable negative realized OOS — discriminating the two mechanisms empirically.
- Primary citations: [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Andersen-Bollerslev 1998](https://doi.org/10.2307/2527343); [Rabiner 1989](https://doi.org/10.1109/5.18626) §III.C (forward-filter causal inference); [Cappé-Moulines-Rydén 2005](https://link.springer.com/book/10.1007/0-387-28982-8) Ch.10 HMM warm-start per `P1-ADR-0005-CITATION-CORRECT-WARM-START`.
- Test statistic: `T_H050_invert = SR_{filtered, gated_LOW} − SR_{filtered, unconditional}`, where both Sharpe ratios are computed on walk-forward OOS net-of-cost returns. Sharpe-family demoted to secondary KPI per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §1.2 + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §D-1; PRIMARY inference vector is MPPM(ρ=1) + survival-constrained metrics per §1.3 + §1.4 below.

## 1.3 Causal-mechanism vs correlation-only annotation (per [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md))

- **Claim type**: `correlation-only`.
- **Mechanism description**: HMM regime conditioning is correlational, not mechanism-based. The HMM forward-filter posterior at bar `t` is a function of the emission feature trajectory `y_{1:t}`; gating on the modal-state assignment selects a subset of bars on which to act. There is no claimed who/what/why/when generative mechanism that PRODUCES a directional edge inside the low-emission-mean state — the inversion is an empirical test of WHICH state-subset (highest-mean per H050 v1 or lowest-mean per this variant) actually carries the per-bar Sharpe-positive subset of bars. The mechanism is observational at the gate layer; the directional signal underneath (LightGBM logistic on `rv_parkinson`, `rv_realized`, `realized_skew`, `ofi_tickrule`) is correlational by construction of feature engineering against returns.
- **E-value or robustness anchor**: per [VanderWeele-Ding 2017 *Ann Intern Med* 167(4):268-274](https://doi.org/10.7326/M16-2607) — the E-value for the H050 v1 result was reported as part of the parent investigation; for H050.invert the E-value annotation is `n/a (correlation-only)` per ADR-0022 §3 (correlational claims do not require E-value robustness anchoring at adoption time; E-value primitive at [src/skie_ninja/inference/e_value.py](../../../src/skie_ninja/inference/e_value.py) is available if operator review at KPI emission requests it as a sensitivity exhibit).

## 1.4 Primary inference vector (per [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained paradigm + [ADR-0018 §D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1))

PRIMARY:
- `MPPM(ρ=1)` on per-session-aggregated gated arm log-return series via [Goetzmann-Ingersoll-Spiegel-Welch 2007 RFS](https://doi.org/10.1093/rfs/hhm025); CI via stationary-bootstrap per [Politis-White 2004](https://doi.org/10.1081/ETC-120028836) + [Patton-Politis-White 2009](https://doi.org/10.1080/07474930802459016) correction. KPI annotation `mppm-rho1-{positive,marginal,negative}` per ADR-0018 §D-1.
- Survival-constrained metric vector per ADR-0017 §3: `terminal_wealth_q05`, `calmar_differential`, `profit_factor`, `r_multiple_mean`. Each with block-stationary-bootstrap CI; KPI annotations `tw-q05-{above-half,above-zero,below-zero}`, `calmar-diff-{positive,marginal,negative}`, `pf-diff-{positive,marginal,negative}`, `r-multiple-mean-{positive,marginal,negative}`.

SECONDARY (Sharpe-family demoted per ADR-0017 §1.2):
- LW2008 differential CI on `T_H050_invert` per [Ledoit-Wolf 2008 *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) — preserved verbatim from H050 v1 §1 statement so the cross-arm Sharpe comparison remains comparable.
- Hansen 2005 SPA family p per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md). M=1 degenerate per H050 precedent.

PAYOFF-SHAPE per [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md):
- L-skewness `τ_3 = λ_3 / λ_2` on per-trade R-multiple distribution per [Hosking 1990 *JRSS B* 52(1):105-124](https://www.jstor.org/stable/2345653). KPI annotation `payoff-shape-{skew-positive,skew-flat,skew-negative}`.

RISK-OF-RUIN per ADR-0017 §4.2:
- Monte Carlo `P(equity reaches 50% of starting bankroll before 252 sessions)` under §4.1 sizing rule × empirical R-multiple distribution; 5000 paths × 252 sessions.

ABANDONMENT-TRIGGER ANNOTATIONS per ADR-0025 + ADR-0028 (opt-in):
- `kill-switch-{active,inactive}` + `kill-switch-mode-{block,size-down}` + `bocd-live-{active,pause,inactive}` + `cost-{empirical-calibrated,conservative-prior,zero}` + `cost-friction-dominated-edge-{present,absent,n/a}`.

## 2. Universe and sample period

Identical to H050 v1 §2 (preserved verbatim for direct comparability per ADR-0027 §D-4 genetic-successor discipline "preserved infrastructure"):

- Instruments: ES and NQ front-month per [config/instruments.yaml](../../../config/instruments.yaml); roll-handling per that file's calendar.
- Frequency: 1-minute bars as the base grid; HMM observation cadence selected by BIC over `{1m, 5m, 15m}` inside the train fold per H050 v1 §2 (preserved unchanged; cadence-5min variant is a SEPARATE genetic successor `P1-H050-CADENCE-5MIN-SUCCESSOR-PRE-REG` and is NOT in scope here).
- Session: RTH only.
- Train window: 2015-01-01 through 2022-12-31.
- Validation window: 2023-01-01 through 2023-12-31 (inner folds of walk-forward).
- Test window: 2024-01-01 through 2025-12-31 (strictly held out until final SPA submission).
- Roll-handling: front-month, back-adjusted via CME calendar; roll dates frozen at pre-reg.

**Substrate binding**: `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per the canonical post-Phase-O.10 substrate (CLAUDE.md Phase O.10 + [memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)). The H050 v1 binding `b3ee230a...` is superseded; H050.invert uses the canonical-going-forward substrate per the Phase O.10 reconciliation.

## 3. Features

Identical to H050 v1 §3 (preserved verbatim):
- `rv_parkinson@1.0` — realized variance, Parkinson estimator.
- `rv_realized@1.0` — squared-returns realized variance per Andersen-Bollerslev 1998.
- `realized_skew@1.0` — third central moment, standardized.
- `ofi_tickrule@1.0` — order-flow-imbalance proxy via tick rule (Lee-Ready); falls back to tick-rule proxy per H050 v1 §3 H010 dependency.
- Leakage tests per plan §3 and §4.6 must pass before run.

## 4. Label construction

Identical to H050 v1 §4 (preserved verbatim): triple-barrier per López de Prado 2018 *AFML* §3.4 (per H050 design.md §15.1 Erratum-1 corrected pin):
- `pt_sl`: `{1.0, 1.5, 2.0}`; selected by walk-forward inner CV.
- `vertical_barrier`: `{30m, 60m, 120m}`; same.
- `volatility_estimator`: Yang-Zhang; lookback `{20, 60, 120}` minutes.
- Meta-label horizon upper bound = max selected `vertical_barrier`; fed to splitter `purge`.

## 5. Estimator (THE INVERSION SITE — only divergence from H050 v1)

Identical to H050 v1 §5 EXCEPT the canonical state-ordering rule at line 63:

- Model class: directional classifier composed with HMM regime-gate. Base classifier is LightGBM trained on §3 features. HMM per ADR-0005: Gaussian emissions; `covariance_type ∈ {diag, full}` (d=1 dedup applied per H050 v1 §5 + the `hmm_covariance_d1_equivalence_addendum_2026-04-26.md` precedent); `n_states` grid per ADR-0005 adaptive rule; selection by BIC + CV log-likelihood.
- **Canonical state ordering at each walk-forward fit (INVERTED FROM H050 v1)**: states sorted by emission-mean of the primary directional feature (ES log-return) **ascending**; **gate state = LOWEST-mean state** (NOT highest-mean as in H050 v1 §5 line 63). The convention is operator-discretionary per ADR-0005 §"Canonical state-ordering rule" + the parent investigation's `P1-ADR-0005-CANONICAL-STATE-ORDERING-SHARPE-VS-MEAN` proposal; H050.invert pre-registers the lowest-mean choice as the empirical test of the H-b anti-selection mechanism. The state-ordering rule for H050.invert is binding for the duration of this hypothesis; any change requires a successor ID per ADR-0013 §"Frozen pre-registration amendment".

  > `# justify`: H050 v1 + parent INVESTIGATE-FAILURE-MODE memo §6.1 established that the highest-mean state has empirically WORSE per-bar Sharpe than the lowest-mean state on both ES (SR_state1_uncond=−0.0147 vs SR_state0_uncond=+0.00061) and NQ. Inverting the gate is the canonical empirical test of which state-subset carries the per-bar-Sharpe-positive bars. Per ADR-0027 §D-3 empirical-before-amendment, this hypothesis tests the inversion mechanism BEFORE any ADR-0005 amendment to the canonical ordering rule lands.

- State assignment at inference (decision) time uses the causal forward filter `p(s_t | y_{1:t})` only per ADR-0005 (preserved verbatim from H050 v1 §5).
- Hyperparameter grid (preserved verbatim from H050 v1 §5): LightGBM `num_leaves ∈ {15, 31, 63}`, `learning_rate ∈ {0.01, 0.05}`, `min_data_in_leaf ∈ {20, 50}`.
- Search protocol (preserved verbatim from H050 v1 §5 + §15.1 Erratum-3): random search with fixed seed; N_draws = 200 per fold; per-config max-iter EM budget = 500 with convergence tolerance 1e-4.
- Loss / metric: logistic loss for training; MPPM(ρ=1) for inner-CV fitness per ADR-0018 §D-1 (CHANGED FROM H050 v1's Sharpe-for-gate-evaluation per Phase N ADR-0018 cascade); Sharpe-family demoted to secondary KPI per ADR-0017 §1.2.

## 6. Splitter

Identical to H050 v1 §6 (preserved verbatim):
- `PurgedWalkForwardSplitter` per plan §4.1.
- `embargo`: max of residual-PACF-based lag and Politis-White optimal block length on stacked residuals.
- `purge`: `max(vertical_barrier)` across CV-selected folds.
- CPCV not used at v1; escalation requires a successor ID per H050 v1 §6 convention.

## 7. Cost model

Per [ADR-0025 §D-3](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) + the operator 2026-05-08 + 2026-05-12 standing zero-cost-v1-pre-cost-research-only directive:
- v1 default: `cost-conservative-prior` per [NT8RealisticCostModel](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) (matches H062 + H055 v3 + post-Phase-O.13 default). Per-side slip prior at the conservative end; commission per CME-cited fees in [config/instruments.yaml](../../../config/instruments.yaml).
- `cost_sensitivity_mult`: 1.0 (1-tick prior); 2.0 sensitivity exhibit per H050 v1 §7 convention.
- Empirical recalibration deferred to paper-trade per `P1-H050-INVERT-COST-EMPIRICAL-CALIBRATION` BLOCKING-BEFORE-PAPER-TRADE-EVALUATED.

## 8. KPI report card emission (per ADR-0013 §3 + ADR-0026 §D-1)

Every walk-forward emission produces a KPI report card with:
- §0 mandatory 3-component summary header per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md): Component 1 Full Realized OOS / Component 2 2026-onward sub-window / Component 3 Forward 1-year bootstrap projection.
- ADR-0014 §3.2 13-table format per ADR-0019 §3 amendment.
- Methodological-correctness annotation banner per ADR-0013 §2.1 (NOT a gate).
- `promising-{kpi-vector-slug}-{cost-model-slug}-{substrate-sha-prefix-16}` annotation per ADR-0026 §D-3 if applicable.

## 9. Stopping rule

Identical to H050 v1 §9 (preserved verbatim): fixed walk-forward fold count equal to `n_required_for_power_80` computed from pilot training-fold Sharpe dispersion; max folds bounded above by calendar-window limit.

## 10. Decision rule

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): no binding gates. All metrics emit as KPI annotations on the report card. Stage transitions are operator-discretionary on the KPI report card per ADR-0013 §5.3. Mandatory `kpi-report-emitted` → `ninjascript-implemented` per ADR-0013 §5; bridge-mediated per ADR-0013 §1.2 (HMM filter requires Python inference at decision time per ADR-0005). Operator 2026-05-04 standing decline-ninjascript directive applies per H052a precedent.

## 11. Reproducibility commitments

- git HEAD (at run): TBD at execution.
- `uv pip freeze` sha (at run): TBD at execution.
- RNG seed: 20260520 (`# justify`: design-date YYYYMMDD per F-Q-8 H054 precedent + H055 convention).
- Dataset checksums: see §2 substrate binding `317429e4...` + [data_requirements.md](data_requirements.md).
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json` per ADR-0005.

## 11.1 Operator-discretionary annotations (per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §5 + [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) §D-2 opt-in tooling)

- ADR-0017 §5 K-1..K-8 kill-switch constraints: opt-in per design-time declaration. H050.invert v1 default: `kill-switch-K-1-enabled` + `kill-switch-K-2-enabled` (EOD-flatten enforced structurally) + `kill-switch-K-6-disabled` + `kill-switch-K-7-disabled` (1-min cadence × bar-level returns means daily/weekly breakers have minimal traction at v1; enabling produces the asymmetric blocking pattern documented in the H062 v3 primitive-attribution ablation per `P1-PHASE-O15-LSKEWNESS-NEGATIVE-MEAN-EDGE-WARNING`).
- ADR-0017 §6 FM-1..FM-5 stress tests: recorded as KPI annotations in the failure log per ADR-0013 §4.2.
- ADR-0018 §D-2 Kelly multiplier grid `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}`: NOT in scope at v1. H050.invert v1 uses the H050 v1 §15.3 sizing convention (100%-of-equity-when-active) for direct comparability per ADR-0027 §D-4. Kelly-multiplier grid extension is a separate genetic successor.
- ADR-0018 §D-3 BOCD live-pause: opt-in via [scripts/run_h050_invert_walk_forward.py](../../../scripts/run_h050_invert_walk_forward.py) `--enable-bocd-live` flag per `P1-BOCD-LIVE-PRIOR-CALIBRATION-H050-INVERT` BLOCKING-BEFORE-LAUNCH-WITH-BOCD-LIVE.

## 11.2 Pre-launch BLOCKING preconditions

- `P1-H050-INVERT-WALK-FORWARD-ORCHESTRATOR-IMPL` (BLOCKING-BEFORE-PRODUCTION-RUN): orchestrator at [scripts/run_h050_invert_walk_forward.py](../../../scripts/run_h050_invert_walk_forward.py) — adapt H050 v1 orchestrator with the inverted state-ordering rule at the gate-selection layer; preserve all other code paths verbatim.
- `P1-H050-INVERT-LEAKAGE-CANARY-INTEGRATION-TEST` (BLOCKING-BEFORE-PRODUCTION-RUN): Cycle-4 leak-canary integration test at [tests/integration/test_h050_invert_pit.py](../../../tests/integration/test_h050_invert_pit.py); verifies the inverted gate computation is PIT-causal (no future-knowing in the state-ordering selection).
- `P1-H050-INVERT-PARITY-INVARIANT-TEST` (BLOCKING-BEFORE-PRODUCTION-RUN): unit test asserting `H050_invert.gate_state_label == H050.gate_state_label` swapped on every fold (i.e., the inverted gate is bit-identical to the H050 v1 gate with the state labels swapped); detects orchestrator-drift between H050 v1 and H050.invert.
- `P1-H050-INVERT-POWER-SIMULATION` (non-blocking; rebound from H050 v1 pilot Sharpe dispersion).
- `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` (CLOSED per CLAUDE.md Phase O.1 follow-on).
- `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` (CLOSED per CLAUDE.md Phase O.2).
- `P1-CAUSAL-DAG-DESIGN-MD-TEMPLATE` (OPEN; project-level; NOT H050.invert-blocking because §1.3 annotation is `correlation-only` and does not require DAG specification per ADR-0022 §3).

## 12. Successor pre-registration linkage

This hypothesis is the **A variant** in the H050 mechanism-discrimination paired-design (Variant A: H-b anti-selection test via gate-state inversion). Its **B sibling** is [H050.stable-state](../H050_stable_state/design.md) (Variant B: H-c whipsaw test via state-stability filter). Together the two variants produce orthogonal predictions under each candidate mechanism — operator review of both KPI report cards discriminates empirically per the parent INVESTIGATE-FAILURE-MODE memo §7.3.

If H050.invert produces non-negative realized OOS edge on both symbols AND H050.stable-state produces continued negative realized OOS, the empirical evidence converges on H-b anti-selection as the load-bearing mechanism; this would empirically motivate an ADR-0005 amendment for canonical state-ordering by emission Sharpe (per `P1-ADR-0005-CANONICAL-STATE-ORDERING-SHARPE-VS-MEAN`) AFTER the empirical decomposition completes per ADR-0027 §D-3 sequencing rule. If H050.invert produces continued negative realized OOS AND H050.stable-state produces improving realized OOS as N rises, the empirical evidence converges on H-c whipsaw as the load-bearing mechanism, motivating a future ADR-0005 amendment for mandatory state-stability-confirmation per `P1-ADR-0005-HMM-STATE-STABILITY-AMENDMENT`. The two amendments are NOT mutually exclusive; a third successor variant combining both modifications is reserved under `P1-H050-INVERT-PLUS-STABLE-STATE-V2`.

## 15. NinjaScript Implementation (per [ADR-0013 §5.1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md))

H050.invert's NinjaScript implementation is **bridge-mediated** per ADR-0013 §1.2 (HMM filter requires Python inference at decision time per ADR-0005). Tracked under `P1-H050-INVERT-NINJASCRIPT-IMPL` (mandatory per ADR-0013 §5; operator-discretionary timing per the 2026-05-04 standing decline-ninjascript directive).

Provisional structure (to be completed when the follow-up fires):
- **C# class name**: `HmmRegimeConditionedDirectionalSignalInverted`
- **C# file path**: `ninjascript/strategies/HmmRegimeConditionedDirectionalSignalInverted.cs`
- **Strategy parameters**: mapped from H050_invert.yaml `classifier.grid` (LightGBM hyperparameters chosen by inner-CV) + HMM cfg (`covariance_type`, `n_states`) + the inverted state-ordering rule
- **Entry / exit logic**: 1:1 with Python signal generation per [scripts/run_h050_invert_walk_forward.py](../../../scripts/run_h050_invert_walk_forward.py) (TBD when follow-up fires)
- **Kill-switch parameters**: per §11.1 K-1..K-2 (K-6/K-7 disabled at v1)
- **Fill-log schema**: matches plan §6.1
- **Sim101 smoke-test record**: TBD when follow-up fires
- **Cross-reference**: this design.md + the canonical KPI report card v1 (TBD)

Python ↔ NinjaScript parity-check artifact required per ADR-0013 §5.2; tracked under `P1-H050-INVERT-NINJASCRIPT-PARITY-TOLERANCE`.

## 16. Substrate dataset checksum binding

Per §2: `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per the canonical post-Phase-O.10 substrate. Per-partition SHA enumeration in [data_requirements.md](data_requirements.md).

## 17. Revision-log + genetic-successor cross-citation (per [ADR-0027 §D-4](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md))

### Initial commit (2026-05-20)

H050.invert is pre-registered at `status: designed`. This is the initial commit; no amendments yet.

### Genetic-successor cross-citation (4-field per ADR-0027 §D-4)

- **Parent hypothesis ID**: H050
- **Parent final stage at the time of successor pre-registration**: `kpi-report-emitted` (frozen 2026-05-04 per [H050 KPI report card v1](../H050/H050_kpi_report_v1.md); H050 v1 stage unchanged — H050 is not retired, per [ADR-0013 §4.1 non-loss](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)).
- **Motivating KPI**: H050 v1 catastrophic outcome `T_H050 = SR_gated − SR_uncond < 0` on both ES (−0.0371 [−0.041, −0.034]) and NQ (−0.0219 [−0.025, −0.019]) with LW2008 CI excluding zero negatively; realized $10K equity −81%/−84%; forward P(loss) = 100% both arms. Plus the [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md) §6.6 finding that H-b anti-selection on the per-bar Sharpe dimension is empirically present on both symbols (ES SR_state1_uncond=−0.0147 vs SR_state0_uncond=+0.00061; NQ analogous).
- **Genetic-cross**: mechanism-discrimination variant — H050.invert inverts the gate-state selection from H050 v1's "highest-mean state" to "lowest-mean state" to test the H-b anti-selection sub-hypothesis empirically. All other H050 v1 §1-§7 mechanic specifications preserved verbatim per ADR-0027 §D-4.
- **Preserved infrastructure** (per ADR-0027 §D-4 "preserved infrastructure" field): [ADR-0005 HMM toolkit](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) (forward-filter + causal warm-start contract); [ADR-0025 abandonment-trigger primitive suite](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) (kill-switch runtime, equity-rebase, BOCD live-pause, cost-model — all opt-in per ADR-0024 §D-2); H050 v1 §3-§4 feature factory + label construction; H050 v1 §5 LightGBM hyperparameter grid + N_draws = 200 random search; H050 v1 §6 splitter (purged walk-forward + embargo + purge); H050 v1 §10 decision rule (per ADR-0013 §1 no-binding-gates).

### Sibling pre-registration cross-link

H050.stable-state is the B variant of the paired mechanism-discrimination design. See [H050_stable_state/design.md §1](../H050_stable_state/design.md) for the H-c whipsaw test specification.
