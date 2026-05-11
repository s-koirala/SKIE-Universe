---
id: ADR-0015
title: Per-component → stacking-master → multi-TF-attention architecture pattern (project-level)
status: proposed
date: 2026-05-06
deciders: skoir
amends:
  - (none — additive; introduces a new architectural-pattern section to the project standing rules. The ADR sits alongside ADR-0013 + ADR-0014 as a project-level standing rule that successor hypotheses cite without re-derivation, the same way ADR-0008 sits alongside ADR-0003 for SPA omega-method selection.)
preserves_immutability_of:
  - ADR-0013 §1 KPI-only philosophy (no binding gates)
  - ADR-0013 §3 KPI report card canonical structure
  - ADR-0013 §4 non-loss mandate
  - ADR-0013 §5 NinjaScript-mandate
  - ADR-0014 §3.2 9-table results summary
  - ADR-0008 SPA omega-method default
  - ADR-0007 embargo placement convention
  - All previously frozen `status: designed` design.md §1-§7 sections (each successor architectural layer is a NEW hypothesis ID, not an amendment to an existing one)
---

# ADR-0015 — Per-component → stacking-master → multi-TF-attention architecture pattern

## Context

The SKIE-Universe hypothesis register currently contains rule-based and single-model architectures: H050 HMM-gated single-channel directional signal; H052a HMM-gated first-hour ORB; H053 multi-timeframe regression with descriptive opening-bar mediation (ElasticNet + LightGBM arms); H054 anti-gate ORB; H055 mechanized wick-rejection scalping with four rule-based components (C1 trend-strength gate; C2 body-overlap consolidation indicator; C3 level-exhaustion counter; C4 ATR-scaled TP/SL with fractional-Kelly sizing). All are calibrated as **single-channel** strategies — one model (or one rule-set) emits one signal per session-bar.

H055 v1's four-component decomposition is the empirical opening for a richer architectural family. Each rule-based component admits a calibrated probabilistic-model upgrade (Component 1's deterministic Brier-score competition between TS-mom / ADX / OLS-slope-t / MA-crossover candidates is already a Layer-1 instance in disguise — the supervised pilot-asymmetry target on the calibration holdout is the per-component CV objective). The natural research progression is: (Layer 1) replace each rule-based component with a per-component calibrated probabilistic ML model; (Layer 2) compose the per-component outputs via a stacked meta-learner producing direction + magnitude + first-passage-time predictions; (Layer 3) orchestrate per-timeframe stacking masters via a tabular-attention layer; (Layer 4) feed the calibrated probability stream to a NinjaScript indicator overlay for live operator review.

The user 2026-05-06 directive ("comprehensive successor staking; per-component → stacking master → multi-TF attention") authorizes the architectural family but does not pre-commit to any one Layer-2 master architecture (Super Learner vs Mixture of Experts vs BMA vs Feature-Weighted Linear Stacking) or any one Layer-3 orchestration mechanism (multi-head attention vs hierarchical Bayesian partial-pooling vs simple TF ensemble). The per-instance choice is a successor-hypothesis design.md §5 decision; this ADR establishes the **project-level convention** under which those decisions are pre-registered.

The ADR sits BEFORE any individual successor hypothesis (H056 / H057 / H058 / H059 in the current sequence) pre-registers a specific instance, so that the pre-registration discipline (per-layer hypothesis-ID, nested-CV protocol, SPA family construction, calibration BLOCKING annotation, PIT-correctness verification, interpretability requirement) is fixed before the first instance is implemented. The ordering is the analogue of ADR-0008 landing before any multi-strategy SPA invocation: the architectural-pattern conventions are project-wide, not per-hypothesis.

This ADR inherits ADR-0013's permanent-exploration framing without amendment. Calibration failure, leakage detection, post-run-audit failure, and SPA rejection are all KPI annotations, not gates. The ADR does NOT introduce new gating semantics — calibration BLOCKING in §3.3 below is a documentation-and-acknowledgment requirement of the §2.1 pattern, not a stage gate.

## Decision

### §2.1. Layer 1 — Per-component calibrated probabilistic models

Each rule-based component of a parent hypothesis (e.g., H055 v1's four components) becomes a **calibrated probabilistic model** whose output is a probability or score on `[0, 1]`. The Layer-1 instance is a NEW pre-registered hypothesis ID with its own `design.md` per ADR-0013 §1; it amends NO frozen `status: designed` parent design.md (ADR-0012 §"Frozen pre-registration amendment" §1-§7 immutability is preserved).

Per-component calibration discipline:

1. **Probabilistic output**: each component emits `p̂ ∈ [0, 1]` (or a real-valued score with a documented monotone link). Hard / categorical outputs are NOT permitted at Layer 1; they are deferred to Layer 2 if needed by the master.
2. **Calibrator**: isotonic regression per [Niculescu-Mizil & Caruana 2005 ICML](https://doi.org/10.1145/1102351.1102430) fitted on the inner-CV folds of the outer walk-forward; Platt scaling permitted as sensitivity exhibit. Calibrator parameters frozen on the inner-CV closure and applied **pre-test-causally** on the OOS fold (the H053 v3 → v4 leakage-clean refactor is the canonical reference).
3. **Per-component CV nested inside the outer walk-forward** per ADR-0007 embargo placement + [López de Prado 2018 *Advances in Financial Machine Learning* Ch. 7 "Cross-Validation in Finance"](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) (Wiley, ISBN 978-1119482086, *practitioner*) §7.4 purged + embargoed walk-forward.
4. **PIT-correctness**: each component's feature factory is verified against the project's leakage-canary integration test pattern (canaries a/b/c per the H050 + H053 reference suites). The canary is a Layer-1 BLOCKING-BEFORE-LAUNCH precondition per the parent hypothesis's design.md §11.2 prereq table.
5. **Per-component output is preserved as a sidecar field** for the Layer-2 master + downstream interpretability inspection (per §3.6 below).

Each component is its own pre-registered hypothesis ID iff the component's input feature space, label, or splitter differs structurally from sibling components. If all four components share the same input panel + label + splitter and differ only in the modeling head, ONE Layer-1 hypothesis ID is permitted with an internal "arm" decomposition (analogous to H053's ElasticNet / LightGBM / LLM Arm 1 / Arm 2 / Arm 3 structure). The choice is a successor-hypothesis design.md §5 decision documented at pre-registration.

### §2.2. Layer 2 — Stacking master

The Layer-2 master combines the per-component calibrated probabilities into the parent hypothesis's prediction targets — direction sign, magnitude (signed log-return forecast or quantile-bucketed forecast), and timing (first-passage-time distribution per the AFML §3.4 triple-barrier framework or the parent's own labelling §4 convention).

The master architecture is a per-successor design.md §5 decision. The ADR-0015 ENUMERATES the four canonical alternatives but does NOT prescribe a default; the successor's design.md §5 selects ONE primary architecture and may optionally pre-register an additional architecture as a sensitivity-only sibling exhibit:

- **Super Learner** ([van der Laan, Polley, Hubbard 2007 *Statistical Applications in Genetics and Molecular Biology* 6(1) Article 25](https://doi.org/10.2202/1544-6115.1309)) — cross-validated meta-learner over a library of base learners; theoretically optimal under the oracle inequality of [vdL et al. 2007 §3-§4]. The default for unconditional combination when no regime-conditional structure is known a priori.
- **Mixture of Experts** ([Jacobs, Jordan, Nowlan, Hinton 1991 *Neural Computation* 3(1):79-87](https://doi.org/10.1162/neco.1991.3.1.79)) — gating network conditions weights on a regime-state input. The natural choice when the parent hypothesis's HMM track (ADR-0005) supplies a regime input or when the per-component performance is known a priori to depend on a low-dimensional context.
- **Bayesian Model Averaging** ([Hoeting, Madigan, Raftery, Volinsky 1999 *Statistical Science* 14(4):382-417](https://www.jstor.org/stable/2676803)) — posterior model probabilities weight the combination; produces calibrated uncertainty intervals at the master output. The preferred choice when downstream Layer-4 indicator-overlay surfaces predictive intervals and the operator wishes to inspect model-class uncertainty.
- **Feature-Weighted Linear Stacking** ([Sill, Takács, Mackey, Lin 2009 arXiv:0911.0460](https://arxiv.org/abs/0911.0460)) — linear master with feature-conditioned blending coefficients; interpretable per-coefficient inspection. The preferred choice when the §3.6 interpretability requirement's `interpretability-full` annotation is the operator's pre-registered priority.

The four alternatives reduce to identical static-weight averaging in the limit of degenerate inputs (single regime; uniform posterior; constant blending features); the choice is load-bearing only when the per-component performance varies across the conditioning variable. The successor's design.md §5 must document which conditioning structure justifies the selected master.

Master-level CV is **nested inside the per-component CV which is nested inside the outer walk-forward**. The outer-inner-master triple-nesting is a per-design.md §5.4 specification (the H050 + H053 v4 orchestrator-triple is the project reference; H050 used outer-WF + 27-cell label CV + 12-cell LGB CV; H053 v4 used outer-WF + inner CV n_splits=5 + isotonic calibration on inner-OOF). Master hyperparameters are searched on the master-level CV folds; per-component models are FROZEN before master fit.

### §2.3. Layer 3 — Multi-TF orchestration

The Layer-3 layer integrates per-timeframe Layer-2 stacking masters into a single multi-TF prediction. One Layer-2 master per timeframe is fitted independently (e.g., daily / hourly / 5-15min per the H053 multi-TF block decomposition); the Layer-3 layer combines the per-TF master outputs.

The Layer-3 architecture is a per-successor design.md §5 decision. ADR-0015 ENUMERATES three alternatives without prescribing a default:

- **Multi-head attention layer** ([Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin 2017 NIPS arXiv:1706.03762](https://arxiv.org/abs/1706.03762), lifted to the tabular setting) — TF-attention weights adapt to the input. The natural choice when the parent hypothesis's signal is known to be regime-dependent across TFs.
- **Hierarchical Bayesian partial-pooling** with TF as the partial-pooling level — produces credible intervals on the per-TF contribution. The preferred choice when sample size per-TF is small relative to the master's parameter count.
- **Simple TF ensemble** (equal-weight or CV-weighted) — the no-extra-hyperparameter baseline; required as the §3.4 SPA-family null-comparator.

The same outer-WF → per-component CV → master CV → orchestration CV nesting from §2.2 lifts to a quadruple-nesting at Layer 3. The compute multiplier is `O(K_outer × K_inner_component × K_master × K_orchestration)` per cell — see §3.7 budget cap.

### §2.4. Layer 4 — Live calibrated probability display

The terminal Layer-4 instance is a NinjaScript indicator overlay surfacing the calibrated per-component probabilities, the Layer-2 master output (direction + magnitude + first-passage-time), and the Layer-3 multi-TF integrated prediction to the operator at run-time. Per ADR-0013 §5 the NinjaScript-mandate applies: every Layer-1 / Layer-2 / Layer-3 hypothesis MUST progress to a working `ninjascript-implemented` C# indicator (or bridge-mediated indicator-service per ADR-0002 + ADR-0013 §1.2) regardless of KPI value. Layer 4 is **presentation-only** — it does NOT introduce a new H_0 / H_1 and does NOT consume an SPA-family slot. The parity-check artifact required by ADR-0013 §5.2 applies to the Layer-2 / Layer-3 prediction output, not to the visual overlay.

The operator-promotion decision (Layer-4 indicator → Layer-4 paper-trade strategy → live capital) is operator-discretionary per ADR-0013 §5.3; the calibrated probability display is the operator-review artifact, not a binding gate.

## §3. Pre-registration discipline per layer

### §3.1. One pre-registered hypothesis ID per layer

The current sequence is (placeholder; per the user's 2026-05-06 directive, the IDs are claimed at the time the successor's design.md is drafted, not pre-allocated here):

| Layer | Hypothesis ID (current sequence) | Scope |
|---|---|---|
| Layer 1 (per-component models) | H056 | Wraps the H055 v1 four components into four parallel calibrated probabilistic ML models on a shared substrate; arms = component-by-component CV |
| Layer 2 (stacking master) | H057 | Frozen H056 component outputs as Layer-2 master input; chooses ONE Super Learner / MoE / BMA / FWLS architecture per design.md §5 |
| Layer 3 (multi-TF orchestration) | H058 | Frozen H057 master per TF; Layer-3 architecture choice per design.md §5 |
| Layer 4 (live probability display) | H059 | NinjaScript indicator overlay; presentation-only |

Each layer is a SEPARATE design.md frozen at `status: designed` with its own §1-§7 immutability. The ADR-0012 §"Frozen pre-registration amendment" discipline forbids in-place upgrade of Layer-N to Layer-N+1 within a single hypothesis ID — a Layer-2 design choice that supersedes a Layer-1 component is a NEW hypothesis ID, NOT an amendment.

### §3.2. Nested-CV protocol

The outer walk-forward + inner per-component CV + master-level CV + (Layer-3 only) orchestration CV nesting is BLOCKING for any successor at this architectural family:

| Level | Splitter | Purge / embargo |
|---|---|---|
| Outer | Walk-forward per Bergmeir-Benítez 2012 / Tashman 2000; calendar-anchored where parent supports it | Embargo per [ADR-0007](ADR-0007-embargo-placement.md) |
| Inner per-component | Purged k-fold per [López de Prado 2018 *Advances in Financial Machine Learning* Ch. 7](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) §7.4, *practitioner* | Stacked embargo per ADR-0007 |
| Master | Inner CV on the closure of per-component fits; n_splits + embargo per design.md §5.4 | Inherits parent hypothesis's embargo |
| Orchestration (Layer 3 only) | Inner CV on the closure of per-TF master fits | Inherits parent hypothesis's embargo |

Each layer's CV produces a sidecar `cv_protocol_sha256` field that the post-run audit verifies against the design.md §5 declared protocol (per ADR-0011 §"post-run audit gate" → ADR-0013 §7.1 KPI-annotation reframe).

### §3.3. Calibration BLOCKING annotation

Calibration is BLOCKING in the §2.1 documentation-and-acknowledgment sense (per ADR-0013 §2.1 — NOT a stage gate; a methodological-correctness banner + operator-acknowledgment requirement). Annotations:

- `bss-positive` / `bss-flat` (`|BSS| < 0.05`) / `bss-negative` against the per-instrument climatological prior per [Brier 1950 *Mon. Wea. Rev.* 78(1):1-3](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2) and [Murphy 1973 *J Appl Meteor* 12:595-600](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2)
- `reliability-in-band` (`∈ [0.7, 1.3]` per CLAUDE.md operational threshold; empirical calibration tracked under `P1-RELIABILITY-SLOPE-EMPIRICAL-CALIBRATION`) / `reliability-out-of-band`

A `bss-negative` OR `reliability-out-of-band` annotation triggers the §2.1 banner + operator-acknowledgment requirement on the KPI report card; the strategy still progresses to `kpi-report-emitted` and onward. Calibration is computed via isotonic regression on the inner-CV folds and applied **pre-test-causally** on the OOS fold — the H053 v3 → v4 leakage-clean refactor's pre-test-causal isotonic source is the canonical reference implementation.

Probabilistic-forecast skill is additionally annotated against [Gneiting & Raftery 2007 *J American Statistical Association* 102(477):359-378](https://doi.org/10.1198/016214506000001437) proper scoring rules (logarithmic + CRPS) and the broader [Gneiting & Katzfuss 2014 *Annual Review of Statistics* 1:125-151](https://doi.org/10.1146/annurev-statistics-062713-085831) probabilistic-forecasting framework. The proper-scoring-rule columns extend §3.3 of the KPI report card without amending ADR-0014's 9-table summary structure.

### §3.4. SPA family construction per layer

Each layer's SPA family is the LAYER'S OWN evaluated configurations. Per [Hansen 2005 *J Bus & Econ Stat* 23(4):365-380](https://doi.org/10.1198/073500105000000063) with the omega-correction per [ADR-0008](ADR-0008-spa-omega-method.md):

- Layer 1 (H056 reference): family = the per-component arm enumeration (e.g., 4 components × candidate model classes per component).
- Layer 2 (H057 reference): family = the master-level configuration grid (architectural variant × hyperparameter cell within the architecture).
- Layer 3 (H058 reference): family = the orchestration-level configuration grid.

The CROSS-LAYER composite null (a single SPA p over the union of Layer-1 + Layer-2 + Layer-3 families) is **deferred** to a new follow-up `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`. The deferral is intentional: the cross-layer null requires a Hansen 2005 §2 dependence-structure specification across the per-layer bootstrap families, and the per-layer bootstraps share neither a common resampling index (Layer 1 resamples per-component bars; Layer 2 resamples on the master's input vectors; Layer 3 resamples on the orchestration's per-TF outputs) nor a common n. The resolution is a project-level cross-hypothesis SPA construction ADR; the candidate framings are [Romano & Wolf 2005 *Econometrica* 73(4):1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER over a layered family, hierarchical BH under the Benjamini-Heller-Yekutieli grouped-FDR framing, or a Hansen-style superset-null on a synchronized resampling index.

Until the follow-up ADR closes, the per-layer SPA p is reported as a KPI annotation per ADR-0013 §2 + ADR-0014 §3.2 Table 7 mechanical-interpretation column.

### §3.5. PIT-correctness verification per layer

Each layer's output MUST be recomputable at time `t` with data ≤ `t` only. The leakage-canary integration-test pattern from H050 + H053 is lifted to the per-layer level:

- Layer 1: per-component canary on the (component-input, component-output) pair.
- Layer 2: master canary on the (frozen-component-output vector, master-output) pair, with the additional invariant that the per-component frozen output is itself PIT-clean.
- Layer 3: orchestration canary on the (frozen-master-per-TF vector, orchestration-output) pair, with the cascading invariant.

The integration test is BLOCKING-BEFORE-LAUNCH per the parent hypothesis's design.md §11.2 prereq table (the H055 PIT-canary-integration-test-landed precondition is the reference convention). The post-run audit gate (per ADR-0011 → ADR-0013 §7.1) checks the canary status as a `leakage-canary-pass` / `leakage-canary-fail` KPI annotation; failure does not gate stage progression.

### §3.6. Interpretability annotation

Even when the master is a black box (a deep MoE gating network; a high-dimensional FWLS with non-sparse coefficients), the **per-component outputs MUST be inspectable per fold per regime**. The successor's KPI report card carries a new `interpretability-{full,partial,opaque}` annotation in the methodological-correctness section per ADR-0013 §2:

- `interpretability-full` — per-component output + per-component CV-fold contribution + master-coefficient inspection all available (FWLS; equal-weight TF ensemble; small-K MoE with explicit gating).
- `interpretability-partial` — per-component output available; master internals are inspectable only at the layer-aggregate level (Super Learner; BMA at K small).
- `interpretability-opaque` — per-component output available but master internals are not directly inspectable (deep attention; MoE at K large; high-dimensional Bayesian neural network as the meta-learner).

The annotation does NOT gate; it surfaces in the KPI report card §"Methodological-correctness annotations" line. An `interpretability-opaque` strategy still progresses to `ninjascript-implemented`. The cascade into the KPI-report-card-template is a follow-up `P1-ADR-0015-INTERPRETABILITY-KPI-ANNOTATION-CASCADE`.

### §3.7. Cross-validation budget cap

**Pre-empirical caveat**: the multipliers below (and the analogous "scales at minimum 4× at Layer 1, 4-12× at Layer 2, 3-9× at Layer 3" wording in §"Consequences" → "Trade-offs accepted") are STRUCTURAL count arguments (n_components × n_master_configs × n_orchestration_configs × nested CV depth) anchored on the H050 7h50min Phase-G clean-run baseline. They are NOT calibrated against a microbench of master-CV or transformer-attention forward-pass cost on this project's hardware. Wall-clock figures are revised post-execution of `P1-ADR-0015-MASTER-ARCHITECTURE-MICROBENCH-CATALOGUE` (the §"Follow-ups" item below). Treat any cumulative wall-clock projection as an order-of-magnitude scoping figure, not a binding budget. The 36-hr-per-launch guardrail (item 3 below) is the load-bearing constraint, not the cumulative.

Nested CV multiplies compute by `O(K_outer × K_inner_component × n_components × n_master_configs × K_master)` at Layer 2; Layer 3 multiplies further by `O(K_orchestration × n_TFs × n_orchestration_configs)`. The H050 production walk-forward at the outer + 27-cell label-CV + 12-cell LGB-CV + HMM `[diag, full] × {2, 3}-states` + Hansen SPA 1000-bootstrap on 7,354,066 rows took ~7h50min wall-clock on a single-machine CPU after the BLAS-pinning + HMM-cache amortization fixes (per CLAUDE.md §"Phase G").

The successor's design.md §11.1 wall-clock budget MUST cap the worst-case nested CV cost. The cap is calibrated by:

1. A microbench measuring per-cell wall-clock at the per-component CV inner-most level (the H050 `bench_hmm_cov_d1.py` is the project-reference microbench template).
2. A per-cell-cost projector multiplying through the nested-CV grid.
3. A wall-clock guardrail of 36 hr per-launch per the supervisor wrapper convention (ADR-0010 + ADR-0011 §"canonical-execution-shape").

Successors whose worst-case projection exceeds 36 hr MUST either downsample the configuration grid, factor the components into separate sibling hypotheses, or land a per-fold-checkpoint primitive (the H053 v4 `lgb_inner_cv_checkpoint_v1_pickle5` schema is the project-reference). Per CLAUDE.md zero-arbitrary-thresholds, the 36 hr guardrail is itself empirically calibrated under the existing `P1-RELAUNCH-PER-ATTEMPT-CAP-CALIBRATION` follow-up.

## Alternatives considered

### A. Single end-to-end deep model

Rejected. (1) Intraday futures sample size at 1-min granularity is `O(10^6)` bars per symbol per 10-year span, but the labelled-event count at the parent hypothesis's predictand cadence is `O(10^3)` sessions — well below the data regime where end-to-end deep models deliver an oracle-inequality-style guarantee. (2) Loses the per-component interpretability that ADR-0013 §"Research philosophy" + the per-strategy KPI report card framing requires. (3) The per-component PIT-canary lift in §3.5 has no analogue in an end-to-end model — a single canary on the input → output pair cannot localize leakage to a feature factory, which empirically defeats the H050 + H053 leakage-detection pattern. The architectural-pattern decision is to pay the nested-CV compute multiplier in exchange for per-layer interpretability + per-component leakage localizability.

### B. Boosting on residuals

Rejected. Boosting per [Friedman 2001 *Ann. Statist.* 29(5):1189-1232 GBM](https://doi.org/10.1214/aos/1013203451) sequentially fits each component to the residual of the previous components' predictions. This conflates Layer 1 (per-component model) with Layer 2 (master combination): the Layer-1 components are not independent calibrated probabilistic models; they are coupled through the residual sequence. Cross-validating a serial-fit chain at the per-component level requires holding out the residual seen by component k+1 from the fold seen by component k — a non-trivial Layer-1 CV protocol with no clean ADR-0007 embargo placement. The architectural-pattern decision is to keep Layer 1 components mutually independent so the per-component CV is straightforward.

### C. Hand-tuned weighted average at Layer 2

Rejected per [CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md) §Parameter & Prompt Selection ("Zero arbitrary thresholds or magic numbers; tunable values require empirical justification: grid/random/Bayesian search, CV, information criteria, or bootstrap CIs"). A hand-tuned static weight is the degenerate case of every Layer-2 alternative (Super Learner with degenerate library; MoE with constant gate; BMA with uniform prior; FWLS with constant features), so the successor MAY arrive at near-equal weights as the empirical CV-selected solution — but the successor MUST run the CV.

### D. No stacking; keep all hypotheses single-component

Rejected. ADR-0013's permanent-exploration framework explicitly supports the natural research direction the user 2026-05-06 directive authorizes; declining the architectural family would close off the per-component-model upgrade path the H055 four-component decomposition motivates. The architectural-pattern decision is to LIFT the existing single-component KPI-report-card discipline to the layered case via the §3 pre-registration discipline.

## Consequences

### Adopted

- §2.1 + §2.2 + §2.3 + §2.4 layered architecture pattern as a project-level standing rule for any successor in this architectural family.
- §3.1 each layer is a separate hypothesis ID (H056 / H057 / H058 / H059 in the current sequence).
- §3.2 nested-CV protocol BLOCKING for every successor.
- §3.3 calibration discipline lifted to a project-wide architectural mandate (already implicit per ADR-0013 §2 + Niculescu-Mizil & Caruana 2005; ADR-0015 makes it explicit at the layered level).
- §3.4 per-layer SPA family construction; cross-layer composite null deferred under a new follow-up ADR.
- §3.5 PIT-canary integration test BLOCKING-BEFORE-LAUNCH per layer.
- §3.6 new `interpretability-{full,partial,opaque}` KPI annotation; cascade into the KPI report card template under follow-up.
- §3.7 nested-CV budget cap binding via design.md §11.1.

### Trade-offs accepted

- **Compute multiplies**: outer × inner-component × n_components × master CV × (Layer-3 only) orchestration CV. The H050 ~7h50min reference scales at minimum 4× at Layer 1 (n_components=4), 4-12× at Layer 2 (master CV inside the closure), and 3-9× at Layer 3 (per-TF orchestration). The full Layer-1+2+3 nested run worst-case is `O(10^2 × H050_cell)` ≈ `O(weeks)` on a single CPU. Mitigated by: (a) the §3.7 budget cap; (b) the H050 + H053 v4 cache-amortization + per-fold-checkpoint primitives; (c) the supervised-relaunch-loop wrapper from ADR-0010; (d) optional per-component parallelization on a multi-core host.
- **Interpretability decay at the master layer**: the `interpretability-opaque` annotation is permitted (§3.6); operator review of an opaque-master strategy is structurally less informative than a `interpretability-full` strategy. Mitigated by the per-component output preservation in §2.1 — even an opaque master is layered on inspectable per-component outputs, so the per-component contribution is always available for fold-by-fold + regime-by-regime inspection.
- **SPA family multiplicity grows**: each layer adds its own family. The cross-layer composite null is deferred under a new follow-up; until the follow-up closes, the per-layer SPA p is the canonical KPI annotation. An unsophisticated cross-layer null (Bonferroni over per-layer p-values) is permitted as a sensitivity-only exhibit.
- **Pre-registration burden grows**: each layer is its own design.md with §1-§7 immutability + §8-§10 + §11 + §15. The successor is responsible for the per-design.md §5 architectural choice + §5.4 nested-CV protocol + §11.2 prereq table + §15 NinjaScript implementation. Mitigated by the project-reference H055 design.md template (17 sections) — the layered successors inherit the structure with the §5 + §11.2 sections expanded for the layered specifics.

### Residual risk

- **Cross-layer SPA family construction is open**. Until `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR` closes, the multi-testing across layers is reported per-layer with no synchronized null. The risk is that a successor with a positive Layer-3 SPA p and a negative Layer-1 + Layer-2 SPA p surface the wrong inferential verdict at the operator-review stage. Mitigated by the ADR-0014 §3.2 9-table summary's per-arm Hansen SPA row + the explicit cross-link to the cross-layer ADR follow-up in every successor's KPI report card §"Methodological-correctness annotations" line.
- **Per-component calibration drift across the outer walk-forward**: isotonic regression fitted on inner-CV folds may deteriorate if the per-component label distribution shifts across the outer-WF roll cadence. Mitigated by the existing Andrews 1993 parameter-instability-detection convention from ADR-0013 §3.1 caveat; the §3.6 interpretability annotation surfaces the per-fold per-regime BSS so drift is detectable post-hoc.
- **Sibling-repo lift discipline is open** for any successor that consumes a sibling-repo signal as a Layer-1 component (e.g., the SKIE-NINJA-0DTE first-hour binomial signal as a Layer-1 component of a Layer-2 multi-asset master). The lift convention is addressed in the ADR-0016 sibling-repo-lift discipline (concurrent-landing).

## References

### Architectural-pattern primary anchors

- [Wolpert 1992 *Neural Networks* 5(2):241-259](https://doi.org/10.1016/S0893-6080(05)80023-1) — original stacked generalization.
- [Breiman 1996 *Machine Learning* 24:49-64](https://doi.org/10.1007/BF00117832) — "Stacked Regressions".
- [van der Laan, Polley, Hubbard 2007 *Statistical Applications in Genetics and Molecular Biology* 6(1) Article 25](https://doi.org/10.2202/1544-6115.1309) — Super Learner.
- [Sill, Takács, Mackey, Lin 2009 arXiv:0911.0460](https://arxiv.org/abs/0911.0460) — Feature-Weighted Linear Stacking.
- [Jacobs, Jordan, Nowlan, Hinton 1991 *Neural Computation* 3(1):79-87](https://doi.org/10.1162/neco.1991.3.1.79) — Mixture of Experts.
- [Hoeting, Madigan, Raftery, Volinsky 1999 *Statistical Science* 14(4):382-417](https://www.jstor.org/stable/2676803) — Bayesian Model Averaging.
- [Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin 2017 NIPS arXiv:1706.03762](https://arxiv.org/abs/1706.03762) — multi-head attention (lifted to tabular setting for §2.3).

### Calibration + probabilistic-forecast anchors

- [Niculescu-Mizil & Caruana 2005 ICML](https://doi.org/10.1145/1102351.1102430) — predicting good probabilities; isotonic + Platt scaling.
- [Brier 1950 *Mon. Wea. Rev.* 78(1):1-3](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2) — Brier Score primary source.
- [Murphy 1973 *J Appl Meteor* 12:595-600](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2) — Brier Skill Score formulation.
- [Gneiting & Raftery 2007 *J American Statistical Association* 102(477):359-378](https://doi.org/10.1198/016214506000001437) — proper scoring rules.
- [Gneiting & Katzfuss 2014 *Annual Review of Statistics* 1:125-151](https://doi.org/10.1146/annurev-statistics-062713-085831) — probabilistic forecasting review.

### Cross-validation in finance

- [López de Prado 2018 *Advances in Financial Machine Learning* Ch. 7 "Cross-Validation in Finance"](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086), Wiley, ISBN 978-1119482086, *practitioner* — §7.4 purged + embargoed walk-forward.

### Multiple-testing across stacked architectures

- [Romano & Wolf 2005 *Econometrica* 73(4):1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x) — stepwise FWER.
- [Hansen 2005 *J Bus & Econ Stat* 23(4):365-380](https://doi.org/10.1198/073500105000000063) — SPA test; preserved as KPI per [ADR-0008](ADR-0008-spa-omega-method.md) + ADR-0013.

### Project-internal cross-links

- [ADR-0005](ADR-0005-hmm-regime-toolkit.md) — HMM toolkit; the Layer-2 MoE gating-network input convention.
- [ADR-0007](ADR-0007-embargo-placement.md) — embargo placement for the §3.2 nested-CV protocol.
- [ADR-0008](ADR-0008-spa-omega-method.md) — SPA omega-method default for the §3.4 per-layer SPA p computation.
- [ADR-0010](ADR-0010-multi-hour-run-process-protection.md) — multi-hour-run process protection; load-bearing for the §3.7 wall-clock budget cap.
- [ADR-0011](ADR-0011-production-walkforward-runbook.md) — production walk-forward runbook; the post-run audit gate convention referenced in §3.2 + §3.5.
- [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — permanent-exploration framework; ADR-0015 inherits §1 KPI-only philosophy + §3 KPI report card canonical structure + §4 non-loss mandate + §5 NinjaScript-mandate without amendment.
- [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — canonical 9-table results summary; ADR-0015 §3.6 interpretability annotation cascades into the §3.2 9-table Table 9 methodological-correctness one-liner.
- ADR-0016 (concurrent-landing) — sibling-repo lift discipline; addresses the §"Residual risk" sibling-repo open item.
- [research/01_hypothesis_register/H055/design.md](../../research/01_hypothesis_register/H055/design.md) — H055 v1 four-component structure; the empirical opening for the architectural family.
- `plan/buildouts/h055_successor_tree_2026-05-06.md` — H055 successor tree (concurrent-landing artifact; documents the H056 / H057 / H058 / H059 sequence claimed at this commit).

## Follow-ups

- `P1-ADR-0015-CROSS-LAYER-SPA-FAMILY-CONSTRUCTION` — closes the open cross-hypothesis SPA construction question for stacked architectures specifically. Candidate framings enumerated in §3.4: Romano-Wolf 2005 stepwise FWER over a layered family; hierarchical BH under a grouped-FDR framing; Hansen-style superset-null on a synchronized resampling index. Resolution is a project-level cross-hypothesis SPA construction ADR. **BLOCKING-BEFORE-FIRST-LAYER-3-SPA-EMISSION** to avoid the residual-risk scenario where a Layer-3 positive SPA + Layer-1 + Layer-2 negative SPA produces an operator-confusion verdict at KPI report card emission.
- `P1-ADR-0015-PER-COMPONENT-CALIBRATION-PRIMITIVE` — consolidate the calibration code per Niculescu-Mizil & Caruana 2005 + Gneiting & Raftery 2007 proper-scoring-rule columns into a shared module under `src/skie_ninja/inference/calibration.py`. Per-component isotonic + Platt + reliability-slope + BSS + log-score + CRPS primitives. Signature contract per the H053 v4 `pre_test_causal_isotonic` reference; PIT-canary integration test landed as a regression test in `tests/integration/test_calibration_pit_canaries.py`.
- `P1-ADR-0015-INTERPRETABILITY-KPI-ANNOTATION-CASCADE` — cascade the §3.6 `interpretability-{full,partial,opaque}` annotation into [research/_templates/kpi_report_card_template.md](../../research/_templates/kpi_report_card_template.md) §"Methodological-correctness annotations" + the ADR-0014 §3.2 Table 9 one-liner. Non-blocking; the annotation is operative from the first H056 KPI report card emission forward via in-design.md §15 wording until the template cascade lands.
- `P1-ADR-0015-NESTED-CV-PROTOCOL-PRIMITIVE` — refactor the nested outer-WF + inner per-component CV + master CV + (Layer-3 only) orchestration CV nesting into a shared protocol module under `src/skie_ninja/backtest/nested_cv.py` so the H056 / H057 / H058 successors do not each re-implement the nesting in their own orchestrator scripts. Signature contract derived from the H050 + H053 v4 orchestrator-triple references.
- `P1-ADR-0015-MASTER-ARCHITECTURE-MICROBENCH-CATALOGUE` — per-cell wall-clock microbench for each of the four §2.2 master architectures + each of the three §2.3 orchestration architectures, lifted from the [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py) project-reference template. Calibrates §3.7 wall-clock budget projector at design.md §11.1 freeze time.
- `P1-ADR-0015-LAYER-N-PIT-CANARY-INTEGRATION-TEST-PRIMITIVE` — consolidate the per-layer PIT-canary integration-test pattern into a shared fixture under `tests/integration/_layered_canaries.py` so the Layer-1 / Layer-2 / Layer-3 cascading invariants are tested by a single test class parameterized on the layer.

This ADR is the canonical reference for the SKIE-Universe project's stacked-architecture conventions from 2026-05-06 forward. It does NOT supersede any prior ADR; it is additive, sitting alongside ADR-0013 + ADR-0014 in the project standing-rules family.
