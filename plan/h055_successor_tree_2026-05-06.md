---
schema_version: buildout_plan_v1
created: 2026-05-06
created_by: skoir
parent_hypothesis: H055
description: Comprehensive successor tree for H055 — per-component ML, master stacking, multi-TF attention, live visual indicator. ID staking + sequencing only; each successor warrants its own multi-round audit-remediate-loop pre-registration cycle.
---

# H055 successor tree — 2026-05-06

This memo stakes the ID space and sequences a comprehensive, non-limiting successor cohort to H055 v1 ([research/01_hypothesis_register/H055/design.md](../research/01_hypothesis_register/H055/design.md), `status: designed` 2026-05-06; 3-round audit-remediate trail [docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md)). It does NOT pre-register any successor; each successor enters the project register through its own designed cycle (Phase 0 lit-check + 3-round audit-remediate-loop on the design.md per [skill audit-remediate-loop](../../.claude/skills/audit-remediate-loop/SKILL.md)). Structure mirrors [plan/h053_buildout_2026-04-28.md](h053_buildout_2026-04-28.md) cycle-table convention and the secondary template at [plan/tier2b_buildout_2026-04-23.md](tier2b_buildout_2026-04-23.md).

## 1. Scope and motivation

H055 v1 is a deterministic four-component mechanization of a discretionary intraday wick-rejection scalp on CME ES/NQ/MES/MNQ futures. The user's 2026-05-06 directive authorizes comprehensive, non-limiting expansion via successor hypotheses that progressively (a) extend the substrate to cross-asset (energy + metals + Dow micro), (b) layer per-component ML on top of v1's deterministic gates by lifting validated artifacts from the `s-koirala/SKIE-Ninja` sibling repository, (c) introduce a stacking master model over the per-component outputs, (d) add a multi-timeframe attention orchestrator, (e) ship a live visual indicator with calibrated probabilistic outputs distinct from H055 v1 §15's static rule-based dashboard.

The framing is exhaustive-exploration per [ADR-0013](../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1 and §5 (NinjaScript mandate is the terminus of every successor's research loop, subject to operator discretion per the user's 2026-05-04 standing decline directive). Each successor (a) gets its own pre-registered design.md, (b) goes through Phase 0 lit-check before `designed` freeze, (c) goes through a 3-round audit-remediate-loop on the design before status transition (cap per [arXiv 2511.00751](https://arxiv.org/abs/2511.00751) self-consistency-tapering result; 3-round cap is the operational choice), (d) emits a KPI report card v1 per ADR-0013 §3 + [ADR-0014](../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) §3.2 9-table mandate, (e) inherits the 2026-05-04 operator-decline-ninjascript standing directive (from H052a's [logs/promotions/184eccd67bf24d71990265d39c28daf0_H052a_operator-decline-ninjascript.md](../logs/promotions/184eccd67bf24d71990265d39c28daf0_H052a_operator-decline-ninjascript.md)).

The H055 v1 audit trail at [docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md) is cross-linked at every successor's design.md per the non-loss mandate (ADR-0013 §4). H055 v1's pilot ledger [data/external/h055_pilot_ledger/Performance.csv](../data/external/h055_pilot_ledger/Performance.csv) (171 trades, 6 sessions, SHA256 `4c5ebf85f38f2881df12335f27f2007d930e7951c71c9339d2a2d3f9735c454a`) remains the descriptive empirical anchor for all successors.

## 2. Successor tree

```
H055 v1 (root; rule-based; status:designed 2026-05-06; on main)
├── H055 v1 §15 NinjaScript dashboard (in-place elaboration; not a new H ID)
├── H056 — Per-component ML lift (SKIE-NINJA-Volatility + body-overlap + level-exhaustion ML models)
│       └── prerequisite: ADR-0016 sibling-repo audit-and-lift protocol
├── H057 — Stacking master (Super Learner over H056 component outputs; van der Laan-Polley-Hubbard 2007)
│       └── prerequisite: H056 component outputs cached + each component's marginal ICR measured
├── H058 — Multi-TF attention orchestrator (transformer attention per Vaswani et al. 2017)
│       └── prerequisite: H057 master baseline established at fixed-TF
├── H059 — Live calibrated probabilistic visual indicator (presentation-only; not a new H_0/H_1)
│       └── prerequisite: H058 master probabilistic forecast validated under BSS + reliability slope
├── H055-CL/MCL/MYM/MGC v2 (parallel-track; deferred per `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND`)
│       └── prerequisite: substrate ingest for energy + metals + Dow micro
└── H055-event-time (parallel-track; event-clock / volume-clock variant)
        └── prerequisite: H011 backlog event-time tooling lands (López de Prado 2018 *AFML* §2.5; Easley-López de Prado-O'Hara 2012 *JPM* "The Volume Clock")
```

| Successor ID | Track | Stage | Type | Prerequisite class |
|---|---|---|---|---|
| H055 v1 | trunk | `designed` | rule-based deterministic | — (root) |
| H055 v1 §15 NinjaScript dashboard | trunk | not-started | static C# indicator (no H ID; in-place §15 elaboration) | H055 v1 ID_1*_c calibration-holdout outputs frozen |
| H056 | ML-stack | not-started | per-component ML | sibling-repo audit (ADR-0016); per-component PIT verification |
| H057 | ML-stack | not-started | master stacking (Super Learner) | H056 component outputs + measured marginal ICR per component |
| H058 | ML-stack | not-started | multi-TF attention orchestration | H057 master baseline + multi-TF feature panel infrastructure |
| H059 | UI / live presentation | not-started | calibrated probabilistic visual indicator | H058 (or H057 if H058 deferred) calibrated probabilistic forecast under BSS + reliability slope |
| H055-CL/MCL/MYM/MGC v2 | parallel substrate-extension | not-started | trunk-restated on energy + metals + Dow micro | substrate ingest per `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND` |
| H055-event-time | parallel clock-extension | not-started | event-clock / volume-clock variant of trunk | H011 event-time tooling (cross-link to [plan/hypothesis_backlog.md](hypothesis_backlog.md)) |

## 3. Per-successor sections

### 3.1 H055 v1 §15 NinjaScript dashboard (in-place elaboration; not a new H ID)

**Disposition**: in-place §15 elaboration of H055 v1's existing design.md §15. STATIC indicator showing the four deterministic component states (C1 trend gate sign / C2 ρ_1 status / C3 R(L) counter / C4 ATR-scaled sizing). NO probability output. NO bridge required.

**Hypothesis statement**: not a new hypothesis. The §15 NinjaScript implementation is a precondition deliverable for H059's PROBABILISTIC visual indicator (the visual codebase template for H059 is the §15 dashboard).

**Scope and universe**: ES + NQ + MES + MNQ per H055 v1 §2; CME ETH + RTH session per [src/skie_ninja/utils/clock.py](../src/skie_ninja/utils/clock.py).

**Prerequisites**:
- H055 v1 calibration-holdout outputs frozen (per `P1-H055-CALIBRATION-HOLDOUT-RUN`); the per-instrument-class `ID_1*_c` and global `q*` are deployment-frozen as static parameters.
- ADR-0001 capacity ceilings enforced as Kelly clamp at indicator-side (display-only; no order placement from indicator).

**Expected deliverables**:
- [ninjascript/strategies/H055AntiWickReversalScalp.cs](../ninjascript/strategies/H055AntiWickReversalScalp.cs) (entry/exit per H055 v1 §4; pure C# per ADR-0013 §1.2).
- [ninjascript/indicators/H055LiveDashboard.cs](../ninjascript/indicators/H055LiveDashboard.cs) (4-component state display).
- Sim101 smoke-test record matching plan §6.1 schema.
- Python ↔ NinjaScript parity-check artifact per ADR-0013 §5.2 (byte-equality on integer signal vector).

**Audit-remediate cycle plan**: 1 round on the C# strategy + indicator authoring (`quant-auditor` + `reproducibility-verifier`); parity-check artifact gates the close. No `lit-check` agent (no new literature claims).

**Cross-references**: H055 v1 §15; ADR-0013 §5.1.

---

### 3.2 H056 — Per-component ML lift

**Hypothesis statement (preliminary; full lit-check + pre-reg comes at H056's own designed cycle)**: replacing H055 v1's deterministic component identifiers with ML-fit analogues — (C1) ML trend-state predictor lifting [SKIE-NINJA-Volatility](https://github.com/s-koirala/SKIE-NINJA-Volatility) substrate (calibrated probabilistic regime classifier rather than deterministic TSMOM/ADX/HAC-OLS/MA-cross sign), (C2) ML body-overlap predictor (replacing closed-form `ρ_1` Jaccard with an ensemble that ingests N raw OHLCV bars on T_H), (C3) ML level-exhaustion predictor (replacing the deterministic state machine with a recurrent or gradient-boosted classifier on level-touch sequences), (C4) ML position-sizing layer (replacing the closed-form fractional-Kelly clamp with a Bayesian credibility-weighted size estimator per [Kan & Zhou 2007 *JFQA* 42(3):621-656](https://doi.org/10.1017/S0022109000004129)) — strictly dominates H055 v1 by per-component out-of-fold marginal Information Coefficient Ratio (ICR) on the post-Cell-I substrate, evaluated walk-forward with Cycle-4 leak canaries + per-component PIT integration tests.

**Scope and universe**: identical to H055 v1 §2 (ES + NQ + MES + MNQ; same calibration holdout 2015-2019 / IS 2020-2023 / OOS 2024-2025-Q4). Energy/metals deferred to H055-CL/MCL/MYM/MGC v2.

**Prerequisites**:
- ADR-0016 sibling-repo audit-and-lift protocol landed (assumed at [docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md](../docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md), being landed concurrently in this commit group).
- Per-component PIT verification (BLOCKING; see §4 cross-cutting prerequisites): each lifted artifact's output must be computable at time t with data ≤ t. Non-trivial for stepwise estimators of [Hsu, Hsu & Kuan 2010 *JEF* 17(3):471-484](https://doi.org/10.1016/j.jempfin.2010.01.001)-style; the SKIE-Ninja sibling repos predate the project's purged-walk-forward discipline so rebuild from raw data is the default unless the lift artifact's training window can be proven fold-disjoint.
- Calibration discipline per [Niculescu-Mizil & Caruana 2005 ICML](https://doi.org/10.1145/1102351.1102430) on the calibrated regime classifier output (BSS > 0 vs climatological prior on each component's own holdout).
- News-calendar ingest (`P1-H055-NEWS-CALENDAR-INGEST`; BLOCKING for H055 v1 walk-forward; cascades to H056 since the eligible-bar filter is shared).

**Expected deliverables**:
- [research/01_hypothesis_register/H056/design.md](../research/01_hypothesis_register/H056/design.md) (full pre-registered design per the H055 v1 17-section template; §15 NinjaScript implementation per ADR-0013 §5; bridge-mediated per ADR-0013 §1.2 because per-component ML inference at decision time requires Python service).
- [research/01_hypothesis_register/H056/lit_review_H056_YYYY-MM-DD.md](../research/01_hypothesis_register/H056/) (Phase 0 lit-check on the ML methods chosen per component).
- [research/01_hypothesis_register/H056/data_requirements.md](../research/01_hypothesis_register/H056/) (substrate SHA256 binding; cross-hypothesis fit-set isolation).
- Per-component module(s) under [src/skie_ninja/features/h056/](../src/skie_ninja/features/h056/).
- [scripts/run_h056_walk_forward.py](../scripts/run_h056_walk_forward.py) (orchestrator; mirrors H052a / H055 v1 dedicated-orchestrator pattern).
- KPI report card v1 with ADR-0014 §3.2 9-table summary; per-component marginal ICR table with paired stationary-bootstrap CI per [Politis & White 2004](https://doi.org/10.1081/ETC-120028836) + [Patton-Politis-White 2009](https://doi.org/10.1080/07474930802459016).
- Per-component PIT canary integration test under [tests/integration/test_h056_pit.py](../tests/integration/).

**Audit-remediate cycle plan**:
- Design-stage: 3-round audit-remediate-loop (`quant-auditor` + `lit-check` + `reproducibility-verifier` parallel; cap per skill).
- Build-stage per component: 2-3 rounds per component (4 components × 2-3 rounds = 8-12 rounds total under audit-remediate-loop discipline). `# justify:` 2-3-round-per-component is the empirical cycle-cost on the H050 → H053 → H054 → H055 trajectory (median 2.5 rounds per build-defect-cluster in [docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md](../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md)).
- Walk-forward: 1 round on the orchestrator-output KPI report card.

**Cross-references**: H055 v1 design.md; ADR-0005 (HMM toolkit; available for C1 lift); ADR-0013 (NinjaScript mandate; bridge-mediated for ML inference); SKIE-NINJA-Volatility sibling repo; SKIE-Ninja sibling repo (per ADR-0016 audit protocol).

---

### 3.3 H057 — Stacking master

**Hypothesis statement (preliminary)**: a Super Learner stacking ensemble per [van der Laan, Polley & Hubbard 2007 *Statistical Applications in Genetics and Molecular Biology* 6(1):Article 25](https://doi.org/10.2202/1544-6115.1309) over the per-component ML outputs from H056 (4 component probabilities + a header pass-through of the H055 v1 deterministic state vector) strictly dominates the best individual component model on aggregate per-trade Sharpe over the post-Cell-I substrate, evaluated by walk-forward + nested per-component CV + master-level CV with leak canaries verified at the master-input boundary.

**Scope and universe**: identical to H056 (ES + NQ + MES + MNQ; same calibration holdout / IS / OOS).

**Prerequisites**:
- H056 produces non-null per-component output for at least 2 of 4 components on at least one instrument class (enabling the master to have ≥ 2 base learners with signal — Super Learner over a single non-null base reduces to that base).
- H056 component outputs CACHED to [artifacts/runs/H056/{run_id}/component_outputs/](../artifacts/runs/H056/) so the master cycle does not re-fit the components (compute amortization).
- Each H056 component's marginal ICR measured + CI-bounded BEFORE H057 stacking begins (per the §5 sequencing rationale).
- Cross-hypothesis SPA family construction per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR` lands or is explicitly deferred for H057 with the same per-class M=N inferential family + BH-FDR adjustment as H055 v1.

**Expected deliverables**:
- [research/01_hypothesis_register/H057/](../research/01_hypothesis_register/H057/) (full pre-registered design; lit_review; data_requirements; KPI v0 → v1).
- [src/skie_ninja/models/stacking/super_learner.py](../src/skie_ninja/models/stacking/super_learner.py) (Super Learner per van der Laan et al. 2007; cross-validated coefficient selection with non-negative-least-squares constraint; loss function = paired log-Sharpe-differential).
- [scripts/run_h057_walk_forward.py](../scripts/run_h057_walk_forward.py).
- KPI report card v1 with ADR-0014 §3.2 9-table summary.
- Per-base-learner contribution decomposition per [Polley & van der Laan 2010 U.C. Berkeley Working Paper 266](https://biostats.bepress.com/ucbbiostat/paper266/) — reported as KPI annotation (`base-learner-contribution-{stable,decayed}`).

**Audit-remediate cycle plan**: 3-round design-stage; 1-2 round walk-forward (master fit on top of cached components is comparatively cheap per the §9 budget). Master overfitting risk dictates an explicit nested-CV gate at the master level (validated against synthetic-null Monte-Carlo).

**Cross-references**: H056; van der Laan-Polley-Hubbard 2007; Polley-van der Laan 2010; H055 v1 §1 LW2008 + Hansen SPA inferential framework (preserved verbatim at H057).

---

### 3.4 H058 — Multi-TF attention orchestrator

**Hypothesis statement (preliminary)**: a transformer-style multi-timeframe attention orchestrator per [Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser & Polosukhin 2017 *NeurIPS 30*](https://papers.nips.cc/paper/7181-attention-is-all-you-need) (scaled dot-product attention with positional encoding over the {1m, 5m, 15m, 30m, 60m, 240m} TF panel) strictly dominates the H057 fixed-TF stacking master on aggregate per-trade Sharpe, evaluated walk-forward with leak canaries verified at every TF-boundary attention head.

**Scope and universe**: identical to H057. Multi-TF panel construction extends the existing H055 v1 §3 dual-TF (T_H × T_L) panel to a 6-TF panel; PIT-causal aggregation per H055 v1 §3 dtype-precision contract.

**Prerequisites**:
- H057 master baseline established at fixed-TF (the comparison anchor; H058's H_1 is `T_H058 = SR_H058 − SR_H057 > 0`).
- Multi-TF feature panel infrastructure (tracked under follow-up `P1-H058-MULTI-TF-PANEL-INFRASTRUCTURE`).
- Latency budget at tick cadence: transformer attention forward-pass on a 6-TF × N-bar context window must complete within the bar-close-to-trigger-fill latency budget (TBD per per-component microbench); if not, attention is computed at T_H bar close with stale T_L contribution carried forward (fall-back; documented as `H058-latency-stale` annotation).

**Expected deliverables**:
- [research/01_hypothesis_register/H058/](../research/01_hypothesis_register/H058/) (full pre-registered design).
- [src/skie_ninja/models/attention/multi_tf.py](../src/skie_ninja/models/attention/) (transformer attention with deterministic seeding + bit-identical-logit-tensor replay scaffolding per ADR-0013 §11.3).
- [scripts/run_h058_walk_forward.py](../scripts/run_h058_walk_forward.py).
- KPI report card v1 with ADR-0014 §3.2 9-table summary.
- Per-attention-head contribution decomposition (KPI annotation; head-level interpretability).

**Audit-remediate cycle plan**: 3-round design-stage. Build-stage substantial (transformer attention requires new code; PIT compliance at the multi-TF aggregation layer is non-trivial per the H053 §5.4 fold-disjoint scalarization protocol). 3-4 round build expected.

**Cross-references**: Vaswani et al. 2017; H055 v1 §3 PIT-causal feature panel contract; ADR-0013 §11.3 deterministic-replay scaffolding.

---

### 3.5 H059 — Live calibrated probabilistic visual indicator (presentation-only; not a new H_0/H_1)

**Disposition**: PRESENTATION-only. Not a new hypothesis. Calibrated probability outputs from H057 (fall-back: H058) drive a tick-by-tick guidance display with first-passage-time bands per [Karatzas & Shreve 1991 *Brownian Motion and Stochastic Calculus*, Springer](https://doi.org/10.1007/978-1-4612-0949-2) Ch.3 + bootstrap-conditional confidence ribbons.

**Hypothesis statement**: no inferential H_0/H_1. Validation criterion is calibration drift over a rolling window: BSS > 0 and reliability slope ∈ [0.7, 1.3] (operational band per CLAUDE.md §"KPI report card" Reliability slope KPI; empirical calibration tracked under `P1-RELIABILITY-SLOPE-EMPIRICAL-CALIBRATION`) maintained on the trailing 60-session-day window.

**Scope and universe**: ES + NQ + MES + MNQ; live tick cadence on NinjaTrader 8 paper-trade and live; underlying probability source is the H057 (or H058) frozen master.

**Prerequisites**:
- H057 (or H058) walk-forward Stage-3 KPI report card v1 emitted with `bss-positive` + `reliability-in-band` annotations.
- Bridge-mediated NinjaScript implementation per ADR-0002 (because the master probability source is a Python service — pure-C# is structurally infeasible for the stacking ensemble or attention orchestrator).
- H055 v1 §15 NinjaScript dashboard (the static indicator) lands FIRST as the visual codebase template (per §8 below).

**Expected deliverables**:
- [ninjascript/indicators/H059LiveProbabilisticDashboard.cs](../ninjascript/indicators/H059LiveProbabilisticDashboard.cs) (probability ribbon + first-passage-time bands).
- [src/skie_ninja/runtime/h059_probability_service.py](../src/skie_ninja/runtime/h059_probability_service.py) (Python inference service mediating the master output to NinjaScript via bridge per ADR-0002).
- Calibration-drift kill-switch at [config/kill_switch_H059.yaml](../config/kill_switch_H059.yaml) (BSS-drops-below-zero or reliability-out-of-band triggers indicator display fall-back to H055 v1 deterministic state; logged per ADR-0013 §4.1).
- Operator-override-decision log at [logs/operator_overrides/H059/](../logs/operator_overrides/H059/) (BLOCKING-BEFORE-LIVE per §6 risk register: operator overrides during paper-trade contaminate KPI annotations and must be tagged at log-time).
- No KPI report card per ADR-0014 §3.2 (presentation-only); calibration-drift report at [reports/h059/calibration_drift_{YYYY-MM-DD}.md](../reports/h059/) on rolling 60-session cadence.

**Audit-remediate cycle plan**: 1-2 round design + build (presentation surface; primary risk is operator-override contamination which is procedural, not statistical). `quant-auditor` + `reproducibility-verifier` parallel; no `lit-check` (Karatzas-Shreve 1991 is a textbook reference, not a load-bearing claim domain).

**Cross-references**: H057 (or H058) master; ADR-0002 bridge-mediated implementation; ADR-0013 §5.3 operator-discretionary clause; H055 v1 §15 dashboard (visual codebase template).

---

### 3.6 H055-CL/MCL/MYM/MGC v2 — energy + metals + Dow micro extension (parallel-track)

**Hypothesis statement (preliminary)**: H055 v1 trunk hypothesis re-stated on the energy + metals + Dow micro instrument set {CL, MCL, MGC, MYM} produces non-null per-instrument-class Sharpe-differential CI excluding zero on at least one of the four added classes. Pilot-ledger 2026-05-06 evidence (CL 100% short skew vs NQ 84% long skew) anchors the cross-asset regime-asymmetry validation as a phase-2 falsifier — if the per-instrument-class trend gate selected via H055 v1 §5.1 supervised competition reproduces the pilot's regime asymmetry, that is corroborating evidence for Component 1's design rationale.

**Scope and universe**: CL (NYMEX crude), MCL (NYMEX micro crude), MGC (COMEX micro gold), MYM (CBOT micro Dow). Substrate ingest required.

**Prerequisites**:
- Substrate ingest per `P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND`. The current substrate at [data/processed/vendor_legacy_1min_roll_adjusted/](../data/processed/vendor_legacy_1min_roll_adjusted/) covers ES + NQ only.
- Roll calendar for CL (monthly contract roll vs ES/NQ quarterly) — non-trivial; CL settlement on penultimate-business-day-before-25th convention requires per-contract roll-rule entry in [config/instruments.yaml](../config/instruments.yaml).
- Per-instrument-class cost model — `futures_orb_v1` cost model is calibrated for CME equity index futures; energy and metals require their own calibration.
- ADR-0001 capacity ceiling extended to CL/MCL/MGC/MYM with delta-equivalent retail-tier mapping.

**Expected deliverables**:
- [research/01_hypothesis_register/H055-CL-extension/design.md](../research/01_hypothesis_register/) (separate hypothesis ID candidate: H055-EM-v2 or a successor numeric H ID).
- Substrate ingest module under [src/skie_ninja/data/ingest/](../src/skie_ninja/data/ingest/).
- [src/skie_ninja/backtest/costs/futures_energy_metals_v1.py](../src/skie_ninja/backtest/costs/) (separate cost model).
- KPI report card v1 with per-asset-class Sharpe-differential + cross-asset BH-FDR.
- Cross-asset regime-asymmetry validation report (the pilot 2026-05-06 CL-NQ asymmetry test).

**Audit-remediate cycle plan**: 3-round design-stage; 2-3 round build (substrate ingest is the largest unknown; CL roll calendar is non-canonical relative to ES/NQ).

**Cross-references**: H055 v1; [memory/regime_context_2026-05-06.md](../../skoir/.claude/projects/C--Users-skoir/memory/regime_context_2026-05-06.md) (cross-asset regime context anchor).

---

### 3.7 H055-event-time — event-clock / volume-clock variant (parallel-track)

**Hypothesis statement (preliminary)**: H055 v1 trunk hypothesis re-stated on event-time / volume-time clock per [López de Prado 2018 *Advances in Financial Machine Learning* §2.5 "Bars"](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) (Wiley, ISBN 978-1119482086, *practitioner*; canonical project-internal reference for volume-clock and dollar-clock bar construction; cross-reference: Easley, López de Prado & O'Hara 2012 "The Volume Clock: Insights into the High Frequency Paradigm" *Journal of Portfolio Management* 39(1):19-29 — the original journal source for the volume-clock framework; no DOI on that *JPM* article, [SSRN 2034858](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2034858) preprint for resolvability) — bars sampled at iso-volume / iso-dollar intervals rather than 1-min wall-clock — preserves any of H055 v1's per-component signal under PIT-causal volume-clock aggregation. Mechanism: 1-min wall-clock bars are non-stationary in information arrival rate (volume-weighted); volume-clock bars are approximately information-stationary, so per-component stationarity assumptions ([Newey & West 1994](https://doi.org/10.2307/2297912) HAC; [Andrews 1991](https://doi.org/10.2307/2938229) bandwidth) are better-supported.

**Scope and universe**: ES + NQ at v1 (same as H055 v1 trunk; restated on volume-clock bars rather than wall-clock).

**Prerequisites**:
- Event-time / volume-time tooling (cross-link to H011 backlog item per [plan/hypothesis_backlog.md](hypothesis_backlog.md)).
- Volume-clock bar construction per [López de Prado 2018 *Advances in Financial Machine Learning* §2.5 "Bars"](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) (Wiley, ISBN 978-1119482086, *practitioner*; canonical project-internal reference) + Easley, López de Prado & O'Hara 2012 "The Volume Clock: Insights into the High Frequency Paradigm" *JPM* 39(1):19-29 (no DOI on the *JPM* article; [SSRN 2034858](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2034858) for resolvability).
- Per-event-time PIT verification (volume-clock has its own PIT pitfalls; AFML §2.5.2 dollar-bar PIT note).

**Expected deliverables**:
- [research/01_hypothesis_register/H055-EvT/design.md](../research/01_hypothesis_register/) (separate hypothesis ID candidate).
- Event-time bar construction module under [src/skie_ninja/data/ingest/event_time/](../src/skie_ninja/data/ingest/).
- KPI report card v1 with H055-EvT-vs-H055-v1 paired LW2008 differential CI (parametric anchor: the volume-clock variant should reduce HAC bandwidth and improve per-component stationarity diagnostics).

**Audit-remediate cycle plan**: 3-round design-stage; 2 round build. The PIT-causal volume-clock construction is the primary technical risk.

**Cross-references**: [López de Prado 2018 *Advances in Financial Machine Learning* §2.5 "Bars"](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) (canonical bar-construction reference); Easley, López de Prado & O'Hara 2012 "The Volume Clock" *JPM* 39(1):19-29 (no DOI; [SSRN 2034858](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2034858) for resolvability — original journal source for volume-clock); H011 (cross-link to project backlog).

## 4. Cross-cutting prerequisites

Items that block multiple successors. Each is a separate follow-up tracked in the project ledger.

- **SKIE-Ninja sibling-repo audit per ADR-0016** (assumed at [docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md](../docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md), being landed concurrently in this commit group). Establishes the lift-and-audit protocol for component artifacts from the SKIE-NINJA-Volatility and SKIE-Ninja sibling repos (both predate the project's purged-walk-forward discipline, so PIT contamination is a non-trivial probability per H056 risk register §6).
- **Calibration discipline per [Niculescu-Mizil & Caruana 2005](https://doi.org/10.1145/1102351.1102430)** — already in project evidence base via H053; binding for any successor that emits a probability output (H056 components 1-3, H057 master, H058 attention orchestrator, H059 visual indicator).
- **Multi-instrument SPA family construction per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`** — open at H055 v1; remains open and is restated under each successor's design.md §1 (the per-class M=N family at the successor level + BH-FDR adjustment is the H055 v1 internal convention; cross-hypothesis composite null requires the project-level ADR).
- **Per-component-output PIT verification** — each H056 component's output must be computable at time t with data ≤ t. Non-trivial for stepwise estimators (e.g., Hsu-Hsu-Kuan 2010 stepwise SPA, or any iterative-fit analogue). The H053 §5.4 fold-disjoint scalarization protocol is the project precedent; per-component PIT integration test BLOCKING for H056 launch (analogue to `P1-H055-PIT-CANARY-INTEGRATION-TEST-LANDED`).
- **News-calendar ingest per `P1-H055-NEWS-CALENDAR-INGEST`** — BLOCKING for H055 v1 walk-forward; cascades to H056-H059 and the parallel-track variants since the eligible-bar filter is shared. Implementation at [src/skie_ninja/utils/news_calendar.py](../src/skie_ninja/utils/news_calendar.py) (FOMC release_id from FRED + NFP/CPI release-times from BLS public release-time calendar).
- **Per-component CV nesting depth** — outer walk-forward + inner per-component CV + master-level CV. Affects total compute budget multiplicatively: a successor with K_outer × K_inner × K_master = 12 × 5 × 5 = 300 fits per cell × 27 label-cfgs × per-instrument-class (4) = 32,400 fits per master cycle. `# justify:` 300-fit estimate is the H053 Stage-3 nested-CV cost (inner-WF n_splits=5 per ADR-0012 §"Cross-validation methodology" preserved by ADR-0013 §7); master-level CV is an additional layer for H057 stacking only.

## 5. Sequencing rationale

H056 → H057 → H058 → H059 is the load-bearing sequence; H055-CL/MCL/MYM/MGC v2 and H055-event-time are parallel-track.

- **H056 (per-component ML) BEFORE H057 (master) so each component's marginal contribution is measured before stacking confounds it**. If H057 stacks confounded base learners, the master Sharpe attribution per [Polley & van der Laan 2010](https://biostats.bepress.com/ucbbiostat/paper266/) cannot identify which component carries signal — a per-component marginal ICR table (H056 KPI) is the load-bearing prerequisite for H057's interpretability KPI (`base-learner-contribution-{stable,decayed}`).
- **H057 (master) BEFORE H058 (multi-TF attention) so stacking is validated on a fixed-TF setup before adding the orchestration layer**. H058 attention head decomposition over a non-validated master is the canonical "interpret a tower whose foundation is unmeasured" failure pattern; if H057 master's interpretability decays under sequential stacking, attention-head decomposition is post-hoc-rationalization.
- **H058 BEFORE H059 (visual indicator) so the displayed probabilities come from a validated probabilistic forecast (calibration BSS + reliability slope)**. The H059 indicator surfaces calibrated probability outputs to the operator at tick cadence; if those outputs come from a master whose calibration is uncertified, the indicator-visible probabilities are operator-misleading. H058 (or H057 if H058 is deferred) walk-forward Stage-3 KPI report card with `bss-positive` + `reliability-in-band` is the load-bearing prerequisite.
- **H055-CL/MCL/MYM/MGC v2 is parallel-track** — depends on substrate ingest, not on H056-H059 ML maturity. The trunk H055 v1 four-component framework is restated verbatim on the new substrate; the cross-asset regime-asymmetry validation is the parallel-track additional empirical test.
- **H055-event-time is parallel-track** — depends on H011 event-time tooling (cross-link to backlog), not on H056-H059 ML maturity. The volume-clock variant is a clock-construction extension of the trunk; per-component stationarity-diagnostics improvement is the additional empirical test.

## 6. Risk register

Substantive risks per successor.

- **H056**: lift-from-sibling-repo PIT contamination is the largest probability mass. The SKIE-Ninja and SKIE-NINJA-Volatility sibling repos predate the project's purged-walk-forward discipline (per ADR-0011 + ADR-0013 §7); their training windows likely overlap with the H055 v1 calibration holdout 2015-2019 and / or IS 2020-2023. ADR-0016 sibling-repo audit-and-lift protocol gates this; a sibling-repo audit revealing deep PIT contamination (training data overlap + label-leakage) closes the H056 lift path and falls back to building components from scratch per the §7 kill conditions.
- **H057**: master overfitting + interpretability decay. Super Learner non-negative-least-squares coefficient selection over correlated base learners can produce a master whose paired Sharpe-differential CI excludes zero only because the base learners' correlated noise is jointly fit. Synthetic-null Monte-Carlo validation (per H053 §11.2 prereq 3) is the protective measure; explicit master-level nested-CV gate.
- **H058**: TF-attention requires substantial new code (transformer attention + multi-TF positional encoding + bit-identical-logit-tensor replay scaffolding per ADR-0013 §11.3 — analogous to H053 Arm 3 LLM replay infrastructure that did not land). Latency at tick cadence: transformer attention forward-pass on 6-TF × N-bar context window may exceed the bar-close-to-trigger-fill latency budget. Fall-back: T_H bar-close attention with stale T_L contribution carried forward (`H058-latency-stale` annotation).
- **H059**: probability-display calibration drift; operator-override contamination of paper-trade KPIs. The probability ribbon at tick cadence is operator-visible and operator-actionable; if the operator overrides the indicator's probability (e.g., enters a position when probability is below threshold), the paper-trade Sharpe-within-CI KPI conflates strategy signal with operator override. Operator-override-decision log per §3.5 is BLOCKING-BEFORE-LIVE.
- **H055-CL/MCL**: cross-asset regime divergence may require per-asset-class sub-hypotheses. CL has different microstructure than ES (shorter contract roll, energy-supply event sensitivity, EIA-Wednesday-10:30-ET event, OPEC-meeting jumps); a per-asset-class trend gate (rather than a single shared trend gate across {ES, MES} ∪ {NQ, MNQ} ∪ {CL, MCL} ∪ {MGC, MYM}) is the conservative pre-reg. Possible split into H055-EM-CL-v2 (energy) + H055-EM-Metals-v2 (metals) + H055-EM-Dow-v2 (Dow) successor sub-tree if the cross-asset regime-asymmetry validation reveals divergent per-component fits.
- **All ML-bearing successors (H056-H059)**: stationary-bootstrap-conditional SPA must be reconstructed for each new SPA family. The Hansen 2005 omega-correction (per ADR-0008) + Politis-Romano 1994 stationary bootstrap with PW2004+PPW2009 block length is the canonical pattern (already implemented at [src/skie_ninja/inference/multipletest/hansen_spa.py](../src/skie_ninja/inference/multipletest/hansen_spa.py)), but each new family's M (cardinality of compared-strategies) and shared-bootstrap-index sample length affect the omega calibration. Cross-hypothesis SPA construction remains an open ADR per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`.

## 7. Decision points / kill conditions

When to abort the tree.

- **H055 v1 produces strongly negative SR with LW2008 CI excluding zero on the negative side**: H056 still proceeds per ADR-0013 §1 (permanent-exploration; null is not terminal). The per-component ML layer focus shifts from "rescue v1" to "isolate which component carries any signal" — H056's per-component marginal ICR table is the load-bearing artifact under this condition.
- **H056 produces all-component-null** (every component's marginal ICR CI covers zero on every instrument class): H057 master is structurally unlikely to find signal stacking nulls (Super Learner over a set of zero-signal base learners reduces to the climatological prior at the cross-validated coefficient solution). Suspend H058 + H059 pending H056 re-spec; consider building H056 components from scratch per the H056 risk register sibling-repo PIT contamination kill condition below.
- **SKIE-Ninja sibling-repo audit reveals deep PIT contamination** (training data overlap with H055 v1 calibration holdout + label-leakage on multiple components): H056 lift path closes. H056 falls back to building components from scratch (substantial scope expansion). The successor-tree timeline shifts by an estimated H056 wall-clock multiplier of ~3x (per §9).
- **News-calendar ingest blocks indefinitely**: H055 v1 walk-forward proceeds with eligible-bar filter degraded to RTH-session-time + feature-availability only (per H055 v1 §4 (i)+(ii)); news-window exclusion becomes a v2 amendment per H055 v1 §16 (frozen-pre-reg amendment policy). Cascades to all successors that share the eligible-bar filter (H056, H057, H058, H059 if H058 is deferred and H057 supplies probabilities to H059).
- **Latency budget at H058**: if transformer attention forward-pass exceeds bar-close-to-trigger-fill latency on the production hardware, H058 falls back to T_H-cadence attention with stale T_L; if that fall-back's stale-T_L bias is empirically large (LW2008 CI on `T_H058_latency-stale - T_H058_realtime` excludes zero), H058 is recorded as `paper-trade-blocked-by-latency` per ADR-0013 §1.2 sub-stage and H059 falls back to consuming H057's master probability instead of H058's attention output.

## 8. Visual indicator: H055 in-place §15 elaboration vs H059 standalone

Disposition (cross-link to §3.1 + §3.5 above):

- **H055 v1 §15 NinjaScript implementation is a STATIC indicator** showing rule-based component states (Component 1 trend gate sign, Component 2 ρ_1 status, Component 3 R(L) counter, Component 4 ATR-scaled sizing). NO probability display. NO bridge needed. Lives in [ninjascript/strategies/H055AntiWickReversalScalp.cs](../ninjascript/strategies/H055AntiWickReversalScalp.cs) (the strategy) plus a separate [ninjascript/indicators/H055LiveDashboard.cs](../ninjascript/indicators/H055LiveDashboard.cs) (the indicator).
- **H059 PROBABILISTIC indicator requires calibrated outputs from H057 (or H058) master model**; bridge-mediated per ADR-0002 (Python inference service); live tick-by-tick guidance; first-passage-time display via Karatzas-Shreve 1991 + bootstrap-conditional confidence ribbons.
- **The H055 §15 indicator is a precondition deliverable for H059** (the visual codebase template). H059 lifts the H055 §15 indicator's NinjaScript scaffolding (drawing primitives, color logic, on-bar-close hooks) and replaces the deterministic-state rendering with the calibrated probability ribbon + first-passage-time bands.

## 9. Compute / wall-clock budget per successor

**Pre-empirical caveat**: the multipliers below are STRUCTURAL count arguments (n_components × n_master_configs × n_orchestration_configs × nested CV depth) anchored on the H050 7h50min Phase-G clean-run baseline. They are NOT calibrated against a microbench of master-CV or transformer-attention forward-pass cost on this project's hardware. Wall-clock figures are revised post-execution of `P1-ADR-0015-MASTER-ARCHITECTURE-MICROBENCH-CATALOGUE` (per ADR-0015 follow-up). Treat the cumulative ~230-790 hr as an order-of-magnitude scoping figure, not a binding budget. The §3.7 36-hr-per-launch guardrail is the load-bearing constraint, not the cumulative.

Rough estimates anchored on H050 production walk-forward cumulative cost (~35.2 hr cumulative across 6 attempts per the [docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md](../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md) ledger; clean run-3 took 7 hr 50 min wall-clock per CLAUDE.md §"Phase G"). All numbers are pre-empirical estimates; revise post-walk-forward.

| Successor | Wall-clock estimate | Multiplier basis | `# justify:` |
|---|---|---|---|
| H055 v1 (root) | 7-12 hr | H050 clean walk-forward 7 hr 50 min (CLAUDE.md Phase G); H055 v1 adds Optuna TPE K_max=500 + 4-instrument-class outer × 27-label-cfg × 12-cell label-CV grid | provisional pending P1-H055-POWER-SIMULATION-EXECUTE final K_max binding |
| H055 v1 §15 NinjaScript dashboard | 4-8 hr (one-time C# authoring + parity check) | one-time C# strategy + indicator authoring + Sim101 smoke-test | comparable to H050 / H054 NinjaScript cycle estimates (no production run) |
| H056 | 25-60 hr | ~3-5× H055 v1 walk-forward (per-component model fit + master combination + nested CV) | per-component CV nesting depth (4 components × inner-CV n_splits=5 × outer walk-forward) drives the multiplier; sibling-repo lift cost not included (loaded into the design-stage 3-round audit-remediate cycle) |
| H057 | 50-120 hr (cumulative; assumes H056 component outputs cached) | ~2× H056 (master fit on top of cached component outputs) | master-level CV nesting + Super Learner non-negative-least-squares coefficient selection over 4-5 base learners; cached-component amortization is the load-bearing efficiency |
| H058 | 150-600 hr (cumulative) | ~3-5× H057 (TF-attention + multi-TF feature panels) | transformer attention forward-pass × backward-pass at production substrate scale × deterministic-replay scaffolding (analogue to H053 §11.3 Arm 3 LLM replay infrastructure that did not land); GPU compute may shift the multiplier (additional capex) |
| H059 | 4-12 hr (presentation-only; no walk-forward run; minimal compute) | no walk-forward; per-rolling-60-session calibration drift report | calibration drift report runs on ~60 session-day rolling cadence; per-report-cycle cost is feature-recompute + BSS + reliability slope on the trailing window |
| H055-CL/MCL/MYM/MGC v2 | 25-50 hr (substrate ingest + walk-forward) | trunk H055 v1 walk-forward × ~3-4 instrument classes × substrate ingest cost | per-asset-class cost model calibration is the largest unknown; CL roll calendar is non-canonical and may require manual roll-rule entry |
| H055-event-time | 12-30 hr (event-time bar construction + walk-forward) | trunk H055 v1 walk-forward × ~1.5 (volume-clock recompute) | event-time bar construction from raw 1-min substrate is one-shot per substrate; downstream walk-forward cost matches trunk |

Total cumulative wall-clock for the H056 → H057 → H058 → H059 main sequence: ~230-790 hr (~10-33 days continuous). Parallel-track variants add ~40-80 hr each. Empirical revision required after H056 walk-forward Stage-3 emits its KPI report card.

## 10. Pre-registration discipline preserved

Every successor:

- Gets its own design.md at `research/01_hypothesis_register/H{NNN}/`.
- Goes through Phase 0 lit-check before `designed` freeze (the H055 v1 §15.1 verdict pattern; literature-anchored on the inferential-framework spine + practitioner-anchored where applicable; no primary source CONTRADICTS the framing).
- Through 3-round audit-remediate-loop on the design before status transition (cap per the [audit-remediate-loop SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md); 3-round operational choice per [arXiv 2511.00751](https://arxiv.org/abs/2511.00751) self-consistency-tapering result).
- Produces a KPI report card v1 per ADR-0013 §3 + ADR-0014 §3.2 9-table mandate; the 9 mandatory tables + 1 mandatory bottom-line prose paragraph at the top of the report card per ADR-0014 §3.2.
- Inherits the operator-decline-ninjascript standing directive (2026-05-04 per H052a's standing decision); `kpi-report-emitted` → `ninjascript-implemented` is operator-discretionary upon canonical-format presentation.
- Feeds the cross-hypothesis SPA family construction (still open under `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`); each successor's per-class M=N inferential family + BH-FDR adjustment is internal-to-successor and does not close the project-level ADR.
- Includes a §15 NinjaScript implementation block per ADR-0013 §5 (pure-C# where possible; bridge-mediated per ADR-0013 §1.2 where Python inference at decision time is required — H056-H058 require bridge; H059 is bridge-mediated by construction).
- Carries a Realized-OOS + Forward-Projection block per ADR-0013 §3.1 (mandatory; $10K-starting-capital realized OOS equity curve + 252-session bootstrap forward projection per arm × symbol).

## 11. Cross-references

- [docs/decisions/ADR-0001-project-scope.md](../docs/decisions/ADR-0001-project-scope.md) — capacity ceiling binding per Kelly clamp.
- [docs/decisions/ADR-0002-bridge-selection.md](../docs/decisions/ADR-0002-bridge-selection.md) — bridge-mediated NinjaScript for H056-H059.
- [docs/decisions/ADR-0005-hmm-regime-toolkit.md](../docs/decisions/ADR-0005-hmm-regime-toolkit.md) — HMM toolkit available for H056 Component 1 lift; HMM is OUT-OF-SCOPE at H055 v1 per design.md §1 (deferred to v3 successor `P1-H055-V2-WITH-HMM-REGIME-GATE`).
- [docs/decisions/ADR-0008-spa-omega-method.md](../docs/decisions/ADR-0008-spa-omega-method.md) — SPA omega-correction (KPI computation per ADR-0013 §2; no longer enters any binding gate).
- [docs/decisions/ADR-0011-production-walkforward-runbook.md](../docs/decisions/ADR-0011-production-walkforward-runbook.md) — 15-item preflight checklist + canonical execution shape per successor walk-forward dispatch.
- [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1 stage progression + §5 NinjaScript mandate + §3.1 Realized-OOS + Forward-Projection block.
- [docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md](../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) §3.2 9-table summary mandate.
- [docs/decisions/ADR-0015-component-stacking-master-architecture.md](../docs/decisions/ADR-0015-component-stacking-master-architecture.md) — per-component → master → orchestrator architecture pattern; concurrent landing in this commit group.
- [docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md](../docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md) — assumed being landed concurrently in this commit group; gates H056 lift path.
- [research/01_hypothesis_register/H055/design.md](../research/01_hypothesis_register/H055/design.md) — H055 v1 `designed` 17-section pre-registration.
- [research/01_hypothesis_register/H055/data_requirements.md](../research/01_hypothesis_register/H055/data_requirements.md) — H055 v1 substrate SHA256 binding.
- [research/01_hypothesis_register/H055/lit_review_H055_2026-05-06.md](../research/01_hypothesis_register/H055/lit_review_H055_2026-05-06.md) — H055 v1 9-domain Phase 0 lit-check.
- [docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md](../docs/audits/audit_trail_2026-05-06_h055_wick_reversal_design.md) — H055 v1 3-round design audit-remediate trail.
- [plan/h053_buildout_2026-04-28.md](h053_buildout_2026-04-28.md) — direct structural template for this memo.
- [plan/tier2b_buildout_2026-04-23.md](tier2b_buildout_2026-04-23.md) — secondary template.
- [plan/hypothesis_backlog.md](hypothesis_backlog.md) — H056-H059 + H055-EM + H055-EvT rows to be added at successor designed-cycle freeze.

## Update cadence

This memo is updated at each successor's stage transition. New successors get rows in §2 + sections in §3 + risk-register entries in §6. Completed successors flip their Stage column to the canonical ADR-0013 §1 stage label (`exploration-in-progress` / `kpi-report-emitted` / `ninjascript-implemented` / `paper-trade-active` / `paper-trade-evaluated` / `live-promoted`). Per the non-loss mandate (ADR-0013 §4), supersession of any successor produces a versioned successor-tree memo (e.g., `h055_successor_tree_v2_YYYY-MM-DD.md`) referencing this memo verbatim; this memo is never deleted or overwritten.
