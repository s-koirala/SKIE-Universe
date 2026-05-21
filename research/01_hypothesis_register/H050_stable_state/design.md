---
name: H050.stable-state — HMM regime-conditioned ES/NQ intraday directional signal with N-bar state-stability filter
description: Pre-registered design doc for hypothesis H050.stable-state; genetic successor to H050
type: project
hypothesis_id: H050_stable_state
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

# H050.stable-state — HMM regime-conditioned ES/NQ intraday directional signal with N-bar state-stability filter

This document is the pre-registration record for hypothesis H050.stable-state. Frozen at `designed`; any change requires a new hypothesis ID per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Frozen pre-registration amendment".

H050.stable-state is a **genetic successor** to H050 v1 per [ADR-0027 §D-4 genetic-successor discipline](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md). Empirical motivation per the [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md) §7.3 Variant B. See §17 revision-log for the 4-field cross-citation.

## 1. Hypothesis

- H0: Under the H050 v1 canonical state-ordering rule (`gate = highest-mean state` per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)) with an N-bar state-stability filter requiring N consecutive bars in the chosen state before gate engagement, the realized Sharpe of the directional signal does not exceed the Sharpe of the unconditional version of the same signal. Formally `SR_{gated, stable_N} − SR_uncond ≤ 0` on the OOS test fold for every N in the registered grid.
- H1: For some N in the registered grid, `SR_{gated, stable_N} − SR_uncond > 0` on the OOS test fold; one-sided test at alpha per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md). Equivalently, the state-stability filter monotonically improves realized OOS as N rises, indicating the H-c whipsaw mechanism (per the parent investigation §6.3 + §6.6) is the load-bearing failure mode of H050 v1.
- Mechanism: per the parent-H050 INVESTIGATE-FAILURE-MODE closure memo §6.3, H050 v1 experiences 102,472 forced position transitions on a 337,837-bar ES OOS fold (30.33% transition rate; median active-run length = 3 bars). Per §6.4, cost-drag from the whipsaw alone exceeds the full-path unconditional signal magnitude by 1.87×-5.66× (ES-NQ range), fully explaining the gated-arm catastrophe. H050.stable-state tests the **H-c whipsaw sub-hypothesis** by adding a state-stability-confirmation period: the gate fires only after N consecutive bars in the chosen state. If H-c dominates, raising N monotonically reduces forced flips and improves realized OOS toward neutral. If H-b anti-selection dominates instead (per the parent memo §6.1 + §6.6 secondary mechanism), stabilizing the state will LOCK the gate into the worse-Sharpe state and produce monotonically WORSE realized OOS as N rises — discriminating the two mechanisms empirically.
- Primary citations: [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Andersen-Bollerslev 1998](https://doi.org/10.2307/2527343); [Rabiner 1989](https://doi.org/10.1109/5.18626) §III.C (forward-filter causal inference); [Cappé-Moulines-Rydén 2005](https://link.springer.com/book/10.1007/0-387-28982-8) Ch.10 HMM warm-start per `P1-ADR-0005-CITATION-CORRECT-WARM-START`.
- Test statistic: `T_H050_stable_state(N) = SR_{filtered, gated, stable_N} − SR_{filtered, unconditional}` for each N in the registered grid `{3, 5, 10, 20}` (1-min bars). Sharpe-family demoted to secondary KPI per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §1.2 + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §D-1; PRIMARY inference vector is MPPM(ρ=1) + survival-constrained metrics per §1.3 + §1.4 below.

## 1.3 Causal-mechanism vs correlation-only annotation (per [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md))

- **Claim type**: `correlation-only`.
- **Mechanism description**: identical framing to H050.invert §1.3 — HMM regime conditioning is correlational. The state-stability filter adds a temporal-persistence layer to the gate selection but does not introduce a generative mechanism that PRODUCES a directional edge inside the stably-held state. The filter is an empirical test of WHETHER the per-bar Sharpe-positive subset is concentrated in transient bursts (in which case the filter degrades performance by gating them out) OR concentrated in sustained regimes (in which case the filter improves performance by filtering out the whipsaw noise around regime boundaries).
- **E-value or robustness anchor**: `n/a (correlation-only)` per ADR-0022 §3. E-value primitive at [src/skie_ninja/inference/e_value.py](../../../src/skie_ninja/inference/e_value.py) available as a sensitivity exhibit if operator review at KPI emission requests it.

## 1.4 Primary inference vector (per [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained paradigm + [ADR-0018 §D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1))

Identical to H050.invert §1.4 (preserved verbatim across the paired-design sibling for cross-arm comparability per ADR-0027 §D-4):

PRIMARY:
- `MPPM(ρ=1)` on per-session-aggregated gated arm log-return series via [Goetzmann-Ingersoll-Spiegel-Welch 2007 RFS](https://doi.org/10.1093/rfs/hhm025); CI via stationary-bootstrap per [Politis-White 2004](https://doi.org/10.1081/ETC-120028836) + [Patton-Politis-White 2009](https://doi.org/10.1080/07474930802459016) correction. KPI annotation `mppm-rho1-{positive,marginal,negative}` per ADR-0018 §D-1.
- Survival-constrained metric vector per ADR-0017 §3: `terminal_wealth_q05`, `calmar_differential`, `profit_factor`, `r_multiple_mean`. Each with block-stationary-bootstrap CI; KPI annotations `tw-q05-{above-half,above-zero,below-zero}`, `calmar-diff-{positive,marginal,negative}`, `pf-diff-{positive,marginal,negative}`, `r-multiple-mean-{positive,marginal,negative}`.

SECONDARY (Sharpe-family demoted per ADR-0017 §1.2):
- LW2008 differential CI on `T_H050_stable_state(N)` for each N per [Ledoit-Wolf 2008 *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002).
- Hansen 2005 SPA family p across the 4 N-cells × 2 symbols = 8-strategy family per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md).

PAYOFF-SHAPE per [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md):
- L-skewness `τ_3 = λ_3 / λ_2` on per-trade R-multiple distribution per [Hosking 1990 *JRSS B* 52(1):105-124](https://www.jstor.org/stable/2345653). KPI annotation `payoff-shape-{skew-positive,skew-flat,skew-negative}`.

RISK-OF-RUIN per ADR-0017 §4.2:
- Monte Carlo `P(equity reaches 50% of starting bankroll before 252 sessions)`; 5000 paths × 252 sessions.

ABANDONMENT-TRIGGER ANNOTATIONS per ADR-0025 + ADR-0028 (opt-in):
- `kill-switch-{active,inactive}` + `kill-switch-mode-{block,size-down}` + `bocd-live-{active,pause,inactive}` + `cost-{empirical-calibrated,conservative-prior,zero}` + `cost-friction-dominated-edge-{present,absent,n/a}`.

## 2. Universe and sample period

Identical to H050 v1 §2 (preserved verbatim per ADR-0027 §D-4 "preserved infrastructure"):

- Instruments: ES and NQ front-month per [config/instruments.yaml](../../../config/instruments.yaml).
- Frequency: 1-minute bars; HMM observation cadence selected by BIC over `{1m, 5m, 15m}` inside the train fold.
- Session: RTH only.
- Train window: 2015-01-01 through 2022-12-31.
- Validation window: 2023-01-01 through 2023-12-31.
- Test window: 2024-01-01 through 2025-12-31.

**Substrate binding**: `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per the canonical post-Phase-O.10 substrate.

## 3. Features

Identical to H050 v1 §3 (preserved verbatim): `rv_parkinson@1.0`, `rv_realized@1.0`, `realized_skew@1.0`, `ofi_tickrule@1.0`. Leakage tests per plan §3 and §4.6 must pass before run.

## 4. Label construction

Identical to H050 v1 §4 (preserved verbatim): triple-barrier per López de Prado 2018 *AFML* §3.4 (per H050 design.md §15.1 Erratum-1).

## 5. Estimator (THE STABILITY-FILTER SITE — only divergence from H050 v1)

Identical to H050 v1 §5 EXCEPT the addition of an N-bar state-stability-confirmation period before gate engagement:

- Model class: directional classifier composed with HMM regime-gate per H050 v1 §5. Base classifier is LightGBM; HMM per ADR-0005.
- Canonical state ordering at each walk-forward fit: **preserved verbatim from H050 v1 §5 line 63** — states sorted by emission-mean of the primary directional feature ascending; gate state = highest-mean state. The H050 v1 canonical ordering is preserved deliberately so the stability filter's effect is measured in ISOLATION from the gate-selection question (which is tested separately in [H050.invert](../H050_invert/design.md)).
- **State-stability filter (NEW; only divergence from H050 v1)**: the gate fires at bar `t` only if the forward-filter posterior `p(s_t = gate_state | y_{1:t})` has placed `gate_state` as the modal state for N consecutive bars `t−N+1, t−N+2, ..., t−1, t`. Until N consecutive bars of in-state have accumulated, the gate stays OFF (position size = 0). Once N consecutive bars accumulate, the gate engages until the modal state flips away; on flip, the counter resets to 0 and N consecutive bars in the new state are required to re-engage.
  - **N grid (PRE-REGISTERED + BINDING)**: `{3, 5, 10, 20}` bars at 1-min cadence (= 3, 5, 10, 20 minutes minimum stability before gate engagement).
  - **Inner-CV selection**: NOT applied. All 4 N values are emitted as a 4-cell family on each symbol; the family p-value is reported via Hansen SPA + Romano-Wolf FWER per §1.4 SECONDARY. Operator review at KPI emission compares the 4 N values to assess monotonicity (the H-c whipsaw signature).
  - **Rationale for the grid choice**: median active-run length in H050 v1 is 3 bars on ES (per parent investigation §6.3); N=3 is the noise floor (matches median run length so the filter is approximately a no-op). N=5/10/20 progressively raise the stability requirement; N=20 corresponds to ~7× median run length and forces the gate to engage only in sustained regime episodes. The grid is geometric in `{3, 5, 10, 20}` (ratios 1.67, 2.0, 2.0) which spans a factor of ~7 — sufficient to surface monotonic trends if they exist.

  > `# justify`: N grid `{3, 5, 10, 20}` chosen to span the H050 v1 empirical median active-run length (3 bars per parent investigation §6.3) up to ~7× that median. Lower-bound N=3 is the noise floor (filter ~= no-op); upper-bound N=20 corresponds to ~7× median active-run, deep enough to force the gate into sustained regime episodes only. Per ADR-0027 §D-2 grid-search discipline, the 4-cell grid lands within the cell-budget cap = 1000 per hypothesis lineage. No upper-bound exploration beyond N=20 at v1 — extension to larger N is a separate genetic successor `P1-H050-STABLE-STATE-EXTENDED-N-GRID-V2`.

- State assignment at inference (decision) time uses the causal forward filter `p(s_t | y_{1:t})` per ADR-0005. The N-bar stability counter is a deterministic state machine on the forward-filter output sequence — PIT-causal by construction (state at bar `t` depends only on the modal-state sequence at bars `t−N+1, ..., t`, each of which is a pure function of `y_{1:t}`).
- Hyperparameter grid (preserved verbatim from H050 v1 §5): LightGBM `num_leaves ∈ {15, 31, 63}`, `learning_rate ∈ {0.01, 0.05}`, `min_data_in_leaf ∈ {20, 50}`.
- Search protocol (preserved verbatim from H050 v1 §5 + §15.1 Erratum-3): random search with fixed seed; N_draws = 200 per fold.
- Loss / metric: logistic loss for training; MPPM(ρ=1) for inner-CV fitness per ADR-0018 §D-1; Sharpe-family demoted to secondary KPI per ADR-0017 §1.2.

## 6. Splitter

Identical to H050 v1 §6 (preserved verbatim).

## 7. Cost model

Per [ADR-0025 §D-3](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) + the operator standing directive: v1 default `cost-conservative-prior` per [NT8RealisticCostModel](../../../src/skie_ninja/backtest/costs/nt8_realistic.py); `cost_sensitivity_mult: 1.0`. Empirical recalibration deferred to paper-trade per `P1-H050-STABLE-STATE-COST-EMPIRICAL-CALIBRATION` BLOCKING-BEFORE-PAPER-TRADE-EVALUATED.

The cost-model annotation has a critical secondary role for H050.stable-state: per the parent investigation §6.4, H-c whipsaw cost-drag exceeds the H050 v1 unconditional signal magnitude by 1.87×-5.66×. Reducing the transition rate via the stability filter should produce a quantifiable cost-drag reduction; the KPI report card MUST cross-reference the per-N transition rate + cost-drag attribution table per ADR-0014 §3.2 Table 8 ("Other KPIs") extension.

## 8. KPI report card emission (per ADR-0013 §3 + ADR-0026 §D-1)

Every walk-forward emission produces a KPI report card with:
- §0 mandatory 3-component summary header per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md): Component 1 Full Realized OOS / Component 2 2026-onward sub-window / Component 3 Forward 1-year bootstrap projection.
- ADR-0014 §3.2 13-table format per ADR-0019 §3 amendment.
- 4-cell N grid sweep: per-N row in Tables 1-8 for each symbol.
- Per-N transition rate + cost-drag attribution row in Table 8 per §7 above.
- Monotonicity diagnostic exhibit (qualitative trend in MPPM(ρ=1) + realized OOS across the N grid) per §1 H1 specification.
- Methodological-correctness annotation banner per ADR-0013 §2.1.
- `promising-{kpi-vector-slug}-{cost-model-slug}-{substrate-sha-prefix-16}` annotation per ADR-0026 §D-3 if applicable.

## 9. Stopping rule

Identical to H050 v1 §9 (preserved verbatim): fixed walk-forward fold count equal to `n_required_for_power_80` computed from pilot training-fold Sharpe dispersion.

## 10. Decision rule

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): no binding gates. Per-N metrics emit as KPI annotations on the report card. Stage transitions are operator-discretionary per ADR-0013 §5.3. Mandatory `kpi-report-emitted` → `ninjascript-implemented` per ADR-0013 §5; bridge-mediated per ADR-0013 §1.2 (HMM filter requires Python inference at decision time per ADR-0005). Operator 2026-05-04 standing decline-ninjascript directive applies per H052a precedent.

## 11. Reproducibility commitments

- git HEAD (at run): TBD at execution.
- `uv pip freeze` sha (at run): TBD at execution.
- RNG seed: 20260520 (`# justify`: design-date YYYYMMDD per F-Q-8 H054 precedent + H055 convention; identical to H050.invert seed for cross-arm comparability).
- Dataset checksums: see §2 substrate binding `317429e4...` + [data_requirements.md](data_requirements.md).
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json` per ADR-0005.

## 11.1 Operator-discretionary annotations (per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §5 + [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) §D-2 opt-in tooling)

- ADR-0017 §5 K-1..K-8 kill-switch constraints: identical to H050.invert §11.1 (K-1 enabled, K-2 structural EOD-flatten, K-6/K-7 disabled at v1).
- ADR-0017 §6 FM-1..FM-5 stress tests: recorded as KPI annotations in the failure log per ADR-0013 §4.2.
- ADR-0018 §D-2 Kelly multiplier grid: NOT in scope at v1 (identical to H050.invert §11.1).
- ADR-0018 §D-3 BOCD live-pause: opt-in per `--enable-bocd-live` flag; calibration tracked under `P1-BOCD-LIVE-PRIOR-CALIBRATION-H050-STABLE-STATE` BLOCKING-BEFORE-LAUNCH-WITH-BOCD-LIVE.

## 11.2 Pre-launch BLOCKING preconditions

- `P1-H050-STABLE-STATE-WALK-FORWARD-ORCHESTRATOR-IMPL` (BLOCKING-BEFORE-PRODUCTION-RUN): orchestrator at [scripts/run_h050_stable_state_walk_forward.py](../../../scripts/run_h050_stable_state_walk_forward.py) — adapt H050 v1 orchestrator with the N-bar stability filter inserted between the forward-filter output and the gate-engagement layer; preserve all other code paths verbatim; emit per-N rows in the sidecar payload.
- `P1-H050-STABLE-STATE-LEAKAGE-CANARY-INTEGRATION-TEST` (BLOCKING-BEFORE-PRODUCTION-RUN): Cycle-4 leak-canary integration test at [tests/integration/test_h050_stable_state_pit.py](../../../tests/integration/test_h050_stable_state_pit.py); verifies the stability-counter at bar `t` is a pure function of the modal-state sequence at bars `t−N+1, ..., t`, each of which is PIT-causal per ADR-0005.
- `P1-H050-STABLE-STATE-FOLD-CONTINUITY-TEST` (BLOCKING-BEFORE-PRODUCTION-RUN): unit test asserting the stability counter resets at fold boundaries OR carries the train-fold-tail counter forward into the test fold IFF the train + test bars are continuous (analogous to the H055 `P1-H055-LEVEL-STATE-FOLD-CONTINUITY` pattern). Default convention: counter resets at fold boundaries per the walk-forward purge + embargo per H050 v1 §6 — train-fold-tail counter NOT carried forward (operator-conservative; preserves PIT-causality without conditioning on near-purge train-tail state).
- `P1-H050-STABLE-STATE-POWER-SIMULATION` (non-blocking; rebound from H050 v1 pilot Sharpe dispersion across the 4-N grid).
- `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` (CLOSED per CLAUDE.md Phase O.1 follow-on).
- `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` (CLOSED per CLAUDE.md Phase O.2).
- `P1-CAUSAL-DAG-DESIGN-MD-TEMPLATE` (OPEN; project-level; NOT H050.stable-state-blocking because §1.3 annotation is `correlation-only` and does not require DAG specification per ADR-0022 §3).

## 12. Successor pre-registration linkage

This hypothesis is the **B variant** in the H050 mechanism-discrimination paired-design (Variant B: H-c whipsaw test via state-stability filter). Its **A sibling** is [H050.invert](../H050_invert/design.md) (Variant A: H-b anti-selection test via gate-state inversion). See [H050.invert §12](../H050_invert/design.md) for the full paired-design discrimination logic.

If H050.stable-state produces monotonically improving realized OOS as N rises across the 4-N grid on both symbols AND H050.invert produces continued negative realized OOS, the empirical evidence converges on H-c whipsaw as the load-bearing failure mechanism of H050 v1; this would empirically motivate `P1-ADR-0005-HMM-STATE-STABILITY-AMENDMENT` (per CLAUDE.md Phase O.18 follow-up registration). If H050.stable-state produces monotonically WORSE realized OOS as N rises (locking the gate into the worse-Sharpe state for longer) AND H050.invert produces non-negative realized OOS, the empirical evidence converges on H-b anti-selection as the load-bearing mechanism. The two amendments are NOT mutually exclusive; a third successor variant combining both modifications is reserved under `P1-H050-INVERT-PLUS-STABLE-STATE-V2`.

## 15. NinjaScript Implementation (per [ADR-0013 §5.1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md))

H050.stable-state's NinjaScript implementation is **bridge-mediated** per ADR-0013 §1.2. Tracked under `P1-H050-STABLE-STATE-NINJASCRIPT-IMPL` (mandatory per ADR-0013 §5; operator-discretionary timing per the 2026-05-04 standing decline-ninjascript directive).

Provisional structure (to be completed when the follow-up fires):
- **C# class name**: `HmmRegimeConditionedDirectionalSignalStableState`
- **C# file path**: `ninjascript/strategies/HmmRegimeConditionedDirectionalSignalStableState.cs`
- **Strategy parameters**: mapped from H050_stable_state.yaml `classifier.grid` + HMM cfg + the chosen N (operator-selected from the 4-N grid at NinjaScript-implementation time per ADR-0013 §5.3 operator-discretionary clause)
- **Entry / exit logic**: 1:1 with Python signal generation per [scripts/run_h050_stable_state_walk_forward.py](../../../scripts/run_h050_stable_state_walk_forward.py)
- **Kill-switch parameters**: per §11.1
- **Fill-log schema**: matches plan §6.1
- **Sim101 smoke-test record**: TBD when follow-up fires
- **Cross-reference**: this design.md + the canonical KPI report card v1 (TBD)

Python ↔ NinjaScript parity-check artifact required per ADR-0013 §5.2; tracked under `P1-H050-STABLE-STATE-NINJASCRIPT-PARITY-TOLERANCE`.

## 16. Substrate dataset checksum binding

Per §2: `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per the canonical post-Phase-O.10 substrate. Per-partition SHA enumeration in [data_requirements.md](data_requirements.md).

## 17. Revision-log + genetic-successor cross-citation (per [ADR-0027 §D-4](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md))

### Initial commit (2026-05-20)

H050.stable-state is pre-registered at `status: designed`. This is the initial commit; no amendments yet.

### Genetic-successor cross-citation (4-field per ADR-0027 §D-4)

- **Parent hypothesis ID**: H050
- **Parent final stage at the time of successor pre-registration**: `kpi-report-emitted` (frozen 2026-05-04 per [H050 KPI report card v1](../H050/H050_kpi_report_v1.md); H050 v1 stage unchanged per ADR-0013 §4.1 non-loss).
- **Motivating KPI**: H050 v1 catastrophic outcome `T_H050 < 0` with LW2008 CI excluding zero negatively on both ES + NQ; realized $10K equity −81%/−84%; forward P(loss) = 100% both arms. Plus the [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md) §6.3 + §6.4 + §6.6 findings: 30.33% transition rate on ES + median active-run length 3 bars + cost-drag exceeding full signal magnitude by 1.87×-5.66×.
- **Genetic-cross**: mechanism-discrimination variant — H050.stable-state ADDS an N-bar state-stability-confirmation period before gate engagement to test the H-c whipsaw sub-hypothesis empirically. H050 v1 §5 line 63 canonical state-ordering rule preserved verbatim (highest-mean state). The stability filter is the ONLY divergence from H050 v1's mechanism. All other §1-§7 specifications preserved verbatim per ADR-0027 §D-4.
- **Preserved infrastructure**: [ADR-0005 HMM toolkit](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) (forward-filter + causal warm-start contract); [ADR-0025 abandonment-trigger primitive suite](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md); H050 v1 §3-§4 feature factory + label construction; H050 v1 §5 LightGBM hyperparameter grid + N_draws = 200; H050 v1 §6 splitter (purged walk-forward + embargo + purge); H050 v1 §10 decision rule (per ADR-0013 §1 no-binding-gates).

### Sibling pre-registration cross-link

H050.invert is the A variant of the paired mechanism-discrimination design. See [H050_invert/design.md §1](../H050_invert/design.md) for the H-b anti-selection test specification.
