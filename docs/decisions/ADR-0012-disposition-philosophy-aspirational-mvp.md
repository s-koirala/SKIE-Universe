---
id: ADR-0012
title: Disposition philosophy — aspirational-MVP, KPI-reported (Sharpe / ToD-FE / Max-DD / Power → KPIs; calibration + leakage + repro + SPA-at-promotion remain binding)
status: superseded-by-ADR-0013
superseded_by: ADR-0013
superseded_date: 2026-05-03
deciders: skoir
amends:
  - ADR-0003 (SPA-vs-RomanoWolf — SPA's design-time gate role downgraded to KPI; SPA-at-operator-promotion role retained as binding family-wise-error control per Round-1 audit F-1-3 remediation)
  - ADR-0008 (SPA omega method — preserved; method continues to compute the omega-corrected p-value at design-time KPI report AND at operator-promotion gate)
  - research/01_hypothesis_register/H050/design.md §8 + §10
  - research/01_hypothesis_register/H051/design.md §8 + §10
  - research/01_hypothesis_register/H052a/design.md §8 + §10
  - research/01_hypothesis_register/H052b/design.md §8 + §10
  - research/01_hypothesis_register/H053/design.md §8 + §10 (per-hypothesis amendment; immutability boilerplate at L48 amended via this same commit per Round-1 audit F-1-10)
  - CLAUDE.md "Evidence bar" + "Execution bar" sections
  - CLAUDE.md "Research philosophy" sub-clause re: pre-reg immutability for project-level disposition-philosophy ADRs
---

# ADR-0012 — Disposition philosophy: aspirational MVP, KPI-reported

> **SUPERSEDED 2026-05-03 by [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).** ADR-0013 dissolves the three-class disposition rubric below: all Class A binding gates become KPIs in a unified KPI report card; the `archive(complete)` / `calibration-failed` / `leakage-detected` / `reproducibility-incomplete` disposition labels are removed; every strategy progresses to a mandatory NinjaScript implementation regardless of KPI values; a non-loss / non-deletion mandate is added. This file is preserved verbatim per ADR-0013 §4.1 non-loss mandate.

## Context

The SKIE-Universe research program has, since its founding (2026-04-15), used a **Sharpe-differential CI gate** as the primary disposition criterion across all Tier-2b+ hypotheses (H050, H051, H052a, H052b, H053). The pre-registered gating tree under each hypothesis's `§10. Decision rule` archives null any arm whose paired Sharpe-CI covers zero, OR whose realized max-DD worsens vs passive-long, OR whose Hansen 2005 SPA against the strategy universe rejects, OR whose realized n is below `n_required_for_power_80`. Combined with H053's conjunctive Sharpe-vs-passive-AND-Sharpe-vs-time-of-day-FE rule, this gating regime is operationally equivalent to a half-dozen independent significance tests at α=0.05 each — a Type-II-error-prone disposition pipeline.

Two empirical observations motivate this ADR:

1. **H053 Stage-1 NULL** (commit `76599bd`, 2026-05-01) was caused by Gate 1 alone — paired Sharpe-CI vs passive-long covered zero on both ES and NQ (ΔSR=0.043, CI=[-0.063, 0.152] on ES; ΔSR=0.030, CI=[-0.073, 0.135] on NQ). Stage-1 had: full 1971-session IS train fold; clean test on the mediator alone (no Daily-gate truncation defect); reasonable signal magnitudes. The disposition flipped to NULL because of a single significance test on a noisy estimator at modest sample size — not because the strategy lacked descriptive merit.

2. **H050** (closed without aggregate disposition; 2026-04-30 post-mortem) failed for **infrastructure reasons** (Windows reboots, OOM, HMM EM bottleneck) across 6 production walk-forward attempts; **no Sharpe-CI gate was ever evaluated**. The H050 gating tree at `research/01_hypothesis_register/H050/design.md` §10 — `passed=False with CI covering zero → archive(null)` etc. — was never reached. Removing those gates from H050 is a *prospective* documentation correction (preventing a future re-launch from being nulled by them), not a retrospective verdict reversal.

The user-facing project goal per [CLAUDE.md §"Research philosophy"](../../CLAUDE.md) is "longitudinal, exhaustive research program" with "null results as valuable as positive results". The current Sharpe-gated disposition pipeline is operationally **inverting** that philosophy: it discards strategies whose Sharpe-CI covers zero at the realised power, even when those strategies have non-trivial descriptive evidence (in-sample partial-R², calibration, mechanism support, mediation NIE). Per the user (2026-05-01):

> "Sharpe... is arbitrary and archaic. We exist outside of the limitations of traditional investment and trading regimes and constraints. Our purpose here is aspirational innovation — we are thinking outside of the box with these strategies and are developing something incredible. We are testing a comprehensive list of strategies, and do not want to be the cause of our own failure."

This ADR converts the disposition philosophy from "constraint-gated" to "KPI-reported, calibration-gated, leakage-blocked".

## Decision

**Three-class disposition rubric** for any hypothesis archived under [research/01_hypothesis_register/](../../research/01_hypothesis_register/):

### Class A — Binding gates (a strategy fails the disposition iff one of these fails)

Per Round-1 audit F-1-2 + F-1-6 remediation, the calibration and PIT/leakage gates are operationally **applicability-conditional** per hypothesis structure. A hypothesis whose pre-registered output is a categorical probability forecast (e.g., H053 §4.5 K×3 archetype-bias-target table) is bound by the calibration gates; a hypothesis whose pre-registered output is a continuous trading-rule decision (e.g., H050 directional signal, H051 pairs-trade entry, H052a/b HMM-state-gated entry) is **not** mechanically bound by BSS / reliability slope, but its underlying classifier output (where one exists; e.g., H050 LightGBM logistic) must be **separately calibrated** if the hypothesis is to support a probabilistic-output downstream consumer. Each per-hypothesis design.md §8.a MUST enumerate which Class A gates apply for that hypothesis with explicit `applicable: yes/no/where` annotations.

| Gate | Applicability | Source | Bind reason |
|---|---|---|---|
| **PIT / leakage-canary** | ALWAYS BINDING; per-hypothesis design.md §8.a MUST enumerate the binding integration test paths + the binding leak-canary detectors (fold-boundary monotonicity per `assert_fold_boundary_invariant`; label-purge horizon per `assert_purge_covers_label_horizon`; dual-fit observer + TracingArray per `FitCallObserver` + `TracingArray`; H053-style NaN-poison structural detector per `tests/integration/test_h053_pit_canaries.py` for any new feature factory) | design.md §3.6 + per-cycle PIT canary integration tests; Cycle-4 leak canary suite at [src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py) | Methodological correctness; data leakage produces inflated all-metrics. Without this gate, every other gate is meaningless. NEVER negotiable. |
| **Calibration: Brier Skill Score (BSS) > 0** vs per-instrument climatological prior on OOS fold | BINDING for hypotheses with categorical-probability outputs (H053 §4.5 table); WAIVED for continuous-output hypotheses (H050, H051, H052a, H052b in their original specifications). Per F-1-2 fix: where a continuous-output hypothesis HAS an underlying classifier (H050 logistic; H052a/b HMM-state posterior), BSS may be evaluated as a KPI annotation but does not bind. Per-hypothesis design.md §8.a MUST mark `applicable: yes/no` explicitly. | design.md §8 (existing); Brier 1950 | A calibrated probability model is a minimum prerequisite for any probabilistic-output deliverable. BSS ≤ 0 on a probability-output hypothesis means the model is actively misinforming. |
| **Calibration: reliability slope ∈ [0.7, 1.3]** | Same applicability as BSS | design.md §8 (existing); Niculescu-Mizil & Caruana 2005 | Same rationale; failures here indicate gross miscalibration. |
| **Reproducibility log present** (git_head + dataset_checksum + scientific_payload_sha256 + pip_freeze sha) | ALWAYS BINDING | CLAUDE.md user-global §Reproducibility (hook-enforced) | Without provenance the result cannot be defended on subsequent re-runs or independent replication. |
| **DSR/PSR above `dsr_activation_size`** (currently no-op; family=7<10) | BINDING when family ≥ activation_size | design.md §8 (existing); Bailey & López de Prado 2014 | When the family is large enough that selection bias inflates raw Sharpe, DSR is the corrected statistic. Currently below activation; will bind once family ≥ 10. The activation_size=10 itself is an operational pin tracked under `P1-DSR-ACTIVATION-SIZE-EMPIRICAL-CALIBRATION` per Round-1 audit F-1-12. |
| **Hansen 2005 SPA family p ≤ α at operator-promotion** | BINDING at operator-promotion gate (NOT at design-time disposition); per Round-1 audit F-1-3 remediation | ADR-0003 + ADR-0008 (omega correction); Hansen 2005 | The operator may not promote an arm to paper-trade if the SPA family p > α at the time of promotion; this preserves family-wise error control across the strategy universe under the user-global rules/quant-project.md §Inference mandate. The omega-corrected p-value is reported as a KPI at design-time AND re-evaluated at operator-promotion as a binding precondition. |

### Class B — KPIs (recorded, reported, monitored — but DO NOT null the disposition)

These are quantitative dimensions of the result reported in the hypothesis disposition memo. Each KPI has a **qualitative strength / weakness annotation** but does **not** null the strategy.

**Per Round-1 audit F-1-4 remediation**: numerical annotation thresholds (e.g., the original 0.20-Sharpe / 0.10-partial-R² boundaries) are NOT hard-coded in this ADR or in any binding hypothesis design.md text. The qualitative annotations below carry no quantitative pre-registered boundaries; the operational pins that previously appeared in this section are deferred to follow-up `P1-DISPOSITION-KPI-ANNOTATION-THRESHOLD-CALIBRATION` (empirical calibration via simulation + bootstrap on the project's existing strategy-universe Sharpe distribution). Until that follow-up closes, the KPI report card uses the qualitative labels below; numeric values are reported alongside but the strength/weakness assignment is deferred to operator judgment per §"Operator-promotion rule" below.

| KPI | Source | Qualitative annotation |
|---|---|---|
| **Paired Sharpe-differential CI vs passive-long** (Lo 2002 / Mertens 2002 / Opdyke 2007 asymptotic; Ledoit-Wolf 2008 studentized circular-block bootstrap) | Was H050/H051/H052a/H052b/H053 §10.1.4 gate | `sharpe-vs-passive-positive` (CI excludes zero, point > 0) / `sharpe-vs-passive-marginal` (CI covers zero, point > 0) / `sharpe-vs-passive-flat` (CI covers zero, point ≈ 0) / `sharpe-vs-passive-negative` (point < 0). The numeric ΔSR + CI bounds are reported alongside; "strong/weak" sub-classification deferred to `P1-DISPOSITION-KPI-ANNOTATION-THRESHOLD-CALIBRATION`. |
| **Paired Sharpe-differential CI vs benchmark-of-record** (for H053: per-prior-day-same-bin per `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE`; this is an AR(1) lag-1 baseline, NOT the original HKS periodicity-confound benchmark per Round-1 audit F-1-11; the HKS confound remains unaddressed under the AR(1) substitute) | Was H053 §10.1.6 conjunctive gate | `sharpe-vs-bench-positive` / `sharpe-vs-bench-marginal` / `sharpe-vs-bench-flat` / `sharpe-vs-bench-negative`. |
| **Hansen 2005 SPA family p-value** with ADR-0008 omega correction across the SPA universe | Was §10.1.7 gate; **also a Class A binding gate at operator-promotion per F-1-3 remediation** | `spa-family-passes` (p ≥ α) / `spa-family-rejects` (p < α). The SPA p is reported at design-time (KPI) AND re-evaluated at operator-promotion (binding). |
| **Realized max-DD ratio** (arm DD / passive DD) | Was H053 §10.1.5 gate | `max-dd-favorable` / `max-dd-comparable` / `max-dd-adverse`. The numeric ratio is reported alongside. |
| **Power-margin ratio** (realized OOS n / `n_required_for_power_80` per Lo 2002 §III HAC-adjusted Sharpe MDE under option-3 conservative prior) | Was §10.1.3 gate | `power-margin-adequate` / `power-margin-marginal` / `power-margin-low`. Per Round-1 audit F-1-8 remediation: a `power-margin-low` arm requires an **extended paper-trade verification window of 120 session-days** (vs the 60-session-day default), to compensate for the loss of design-time power. This is a binding §11.1 / §Execution-bar amendment, not just an annotation. |
| **Mediation NIE / NDE point estimate + CI** (Imai-Keele-Tingley 2010 + bootstrap CI; design.md §5.4) | Already an annotation in H053 §10.2 | `mediation-NIE-significant` / `mediation-NDE-significant` / `mediation-flat`. Descriptive-only per design.md §1; per Round-1 audit F-1-14: "NIE annotation does not entitle promotion absent corroborating Sharpe-vs-passive-positive AND partial-R²-positive evidence; the sequential-ignorability + SUTVA assumptions remain heroic per H053 design.md §1 critical interpretive note." |
| **In-sample partial-R² of multi-tf X over mediator alone** | New KPI | `partial-r2-positive` (CI excludes zero) / `partial-r2-flat` (CI covers zero). Numeric value reported alongside; magnitude sub-classification deferred. |
| **Cost-floor sensitivity** (1-tick vs 2-tick slippage) | Was §7.1 + §10.2 annotation | `cost-floor-conditional` (positive at 1-tick only) / `cost-robust` (positive at both) / `cost-flat` (flat at 1-tick). |

### Class C — Documentation requirements (must accompany every disposition)

- **Strengths/weaknesses report card** populated from Class B KPIs.
- **Per-cycle audit-remediate-loop trail** (3-round cap) per [`audit-remediate-loop`](../../.claude/skills/audit-remediate-loop/SKILL.md) skill.
- **Substrate dataset_checksum + scientific_payload_sha256** binding.
- **PIT canary suite** green for all feature factory blocks the hypothesis consumes.

## Disposition labels under the new rubric

The disposition string format becomes:

```
hypothesis_id  |  disposition_class  |  KPI report card  |  annotations
```

Where `disposition_class` is one of (in strict order):

1. **`leakage-detected`** — PIT canary or other leakage gate failed. Not eligible for any further consideration without remediation.
2. **`calibration-failed`** — BSS ≤ 0 or reliability slope outside [0.7, 1.3]. Strategy is recorded but is not eligible for paper-trade.
3. **`reproducibility-incomplete`** — required provenance fields missing.
4. **`archive(complete; KPI report)`** — passes Class A gates; KPI report card published; eligible for paper-trade subject to operator review of the report card. Replaces the binary `archive(positive)` / `archive(null)` of the old regime.

The old labels `archive(positive)` and `archive(null)` are deprecated. Existing archive(null) labels in the project history (Stage-1 `archive(null)` from H053 commit `76599bd`; provisional H053 `archive(null)` from `28f93ec` already reversed by `8c1de7c`) are retroactively re-tagged `archive(complete; KPI report)` with the original Sharpe-CI null rendered as a `sharpe-vs-passive-positive-weak` annotation.

## Cross-validation methodology under the new philosophy

**CPCV is restored as the canonical splitter** for any hypothesis disposition that produces a Sharpe KPI. Per Lopez de Prado AFML §12 + the project's existing scaffolding at [src/skie_ninja/backtest/splits.py](../../src/skie_ninja/backtest/splits.py) `cpcv_split` (committed Cycle 4, 2026-04-23), the H053 Stages 1-3 first-pass implementation that used a single train/test cut (2015-2022 IS, 2024-2025 OOS) is **operationally insufficient** for a credible Sharpe KPI distribution. CPCV produces N choose K backtest paths per fold, giving a path-distribution of Sharpe (rather than a single point) that feeds Hansen SPA + DSR more honestly.

**Action for Stage-3 re-run**: switch from the single-train/test split to `cpcv_split(n_groups=10, n_test_groups=2)` per AFML §12.1.3 (yields C(10,2)=45 backtest paths per fold). The full path-reconstruction follow-up `P1-BACKTEST-CPCV` is promoted from non-blocking to **BLOCKING-BEFORE-ANY-STAGE-3-RE-RUN-OR-NEW-HYPOTHESIS-DISPOSITION**.

### CPCV acceptance criteria (per Round-1 audit F-1-5 remediation)

A `P1-BACKTEST-CPCV` implementation is acceptable for closing the BLOCKING gate iff it satisfies all of:

1. **Minimum 45 backtest paths per fold** at `n_groups=10, n_test_groups=2` per AFML §12.1.3.
2. **Per-path Sharpe distribution monotonicity**: the returned path-Sharpe distribution's empirical CDF converges as `n_paths` increases from 10 to 45 (Kolmogorov-Smirnov distance between consecutive 5-path-batch CDFs ≤ 0.05 by 30 paths). This is the operational sufficiency check that CPCV has run long enough.
3. **Per-path Sharpe distribution moments**: mean + std + 5%/95% quantiles reported in the disposition memo; the Class B `sharpe-vs-passive-positive/marginal/flat/negative` annotation uses the **median** path Sharpe (not the single-fold-cut Sharpe).
4. **Computational budget cap**: max wall-clock 24 hours per H053 cycle; if exceeded, the operator may downgrade to `n_groups=8, n_test_groups=2` (yields C(8,2)=28 paths) with a `cpcv-downsampled` annotation in the disposition memo.
5. **DSR computed under CPCV path distribution** per Bailey-Lopez de Prado 2014: deflated Sharpe uses the CPCV path-Sharpe std (not the asymptotic Sharpe-CI std) to estimate the family selection bias.

A CPCV implementation that satisfies all 5 closes `P1-BACKTEST-CPCV`. Implementations that ship without (2) or (3) are not sufficient and the BLOCKING gate remains open.

## Operator-promotion rule (per Round-1 audit F-1-7 remediation)

A `archive(complete; KPI report)` disposition makes arm `a` **eligible** for paper-trade. The operator's promotion decision is constrained by the following pre-registered rule (NOT operator-discretionary):

### Operator-promotion gate (binding)

The operator MUST promote any arm `a` satisfying ALL of:
1. All Class A binding gates pass (PIT/leakage + applicable calibration + reproducibility + DSR-when-active).
2. **`sharpe-vs-passive-positive`** OR **`sharpe-vs-passive-marginal`** (i.e., point estimate > 0, regardless of CI).
3. **Hansen SPA family p ≤ α at the time of promotion** (binding family-wise-error control per F-1-3 remediation; SPA is re-evaluated at the operator-promotion step using the strategy universe accumulated to date INCLUDING any sibling arms promoted in the same window).
4. `max-dd-comparable` OR `max-dd-favorable` (max-DD ratio ≤ 1.5; the 1.5 multiplier mirrors the kill-switch `k_DD` operational threshold per design.md §11.1, also a forward-looking pin tracked under `P1-DISPOSITION-MAX-DD-RATIO-CALIBRATION`).

The operator MAY defer promotion under the following pre-registered conditions, with deferral requiring a written justification logged in the disposition memo:

- `max-dd-adverse` (ratio > 1.5): may defer pending operator review of risk-tolerance rationale.
- `power-margin-low`: per F-1-8 remediation, `power-margin-low` arms require an extended 120-session-day paper-trade verification window (vs the 60-session-day default); the operator may defer launching paper-trade pending this longer-runway commitment.
- `cost-floor-conditional`: may defer pending operator decision on which slippage assumption is realistic for the deployment venue.

Deferrals NOT covered by the above conditions require an explicit ADR amendment (or a successor disposition-philosophy ADR) to legitimise. **The operator may NOT defer based on KPI patterns not enumerated above** — specifically, the operator may NOT cherry-pick arms based on attractive partial-R² + mediation-NIE-significant patterns; per F-1-14, mediation NIE alone does not entitle promotion absent corroborating Sharpe + partial-R² evidence.

### Promotion log

Every promotion decision (promote / defer) MUST be logged to `logs/promotions/{run_id}_{hypothesis_id}_{arm_id}_promotion.md` with:
- The Class B KPI report card values at promotion time
- The operator's decision (promote / defer) with timestamp
- If defer: the pre-registered deferral condition invoked + written justification
- Cross-link to the disposition memo + ReproLog

The promotion log is the audit-trail-of-record for any subsequent live-promotion decision per [CLAUDE.md §Execution bar](../../CLAUDE.md).

## Frozen pre-registration amendment (per Round-1 audit F-1-10 remediation)

This ADR retroactively amends the `§8 + §10` sections of 5 hypothesis design.md files (H050, H051, H052a, H052b, H053) that are pre-registered with `status: designed` (or `designed-amended`). Each design.md frontmatter includes immutability boilerplate stating "Any change requires a successor hypothesis ID."

**Amendment precedent under this ADR**: the immutability discipline is amended (project-wide) to permit **project-level disposition-philosophy ADRs** (i.e., this ADR and any successor) to amend the §8 + §10 gating tree of frozen pre-registrations, **without requiring a successor hypothesis ID**, subject to:

1. The amendment must be a project-wide ADR that applies uniformly to all in-scope hypotheses (not a single-hypothesis carve-out).
2. The amendment must be tracked via an audit-remediate-loop trail (this commit's [audit_trail_2026-05-01_disposition-philosophy-shift.md](../audits/audit_trail_2026-05-01_disposition-philosophy-shift.md)).
3. Each affected hypothesis design.md must reference the amending ADR explicitly in §8 + §10.
4. The amendment must NOT change the §1 (hypothesis statement), §2 (universe/sample), §3-§7 (features, labels, splitter, cost model) — these remain immutable per the original pre-reg discipline.

The amendment to the immutability discipline itself is recorded in [CLAUDE.md §"Research philosophy"](../../CLAUDE.md) (this commit). Any change to §1-§7 still requires a successor hypothesis ID; only §8 + §10 (gating tree + decision rule) is amendable via project-level ADR. This narrow exception preserves the spirit of pre-reg discipline (substantive hypothesis content immutable) while permitting cross-hypothesis disposition-philosophy evolution.

## Alternatives considered

### A. Keep Sharpe-CI as a binding gate; tighten s_min to 0.20 instead of 0.12

Rejected. Per user 2026-05-01 the Sharpe metric itself is "arbitrary and archaic"; the issue is not the threshold but the framing. A 60-session-day paper-trade evidence floor (per [CLAUDE.md §Execution bar](../../CLAUDE.md)) provides a stronger empirical constraint than any backtested-Sharpe gate.

### B. Replace Sharpe gate with information-coefficient (IC) gate

Rejected as a like-for-like swap; same Type-II problem at the same realised n.

### C. Drop ALL gates including BSS + reliability + leakage

Rejected. Per user: "we will have removed *most* constraints altogether" — calibration + leakage gates are the methodological floor below which any disposition is meaningless. A leakage-contaminated strategy reports inflated Sharpe AND BSS AND reliability; all KPIs are corrupted. Calibration failure means the categorical-table deliverable would systematically mislead users. These are **not** "Sharpe-style arbitrary thresholds"; they are correctness preconditions.

### D. Convert to a single composite "research-fitness score" combining all KPIs

Rejected. Composite scores hide trade-offs; the per-KPI report card is more honest. The reader can synthesize a composite if they wish.

## Consequences

### Adopted

- All Tier-2b+ hypothesis design.md §10 gating trees rewritten to use the three-class rubric.
- All current and future hypothesis dispositions report a KPI report card alongside the disposition class.
- CPCV becomes mandatory for Sharpe-KPI computation on any hypothesis with a Sharpe-style metric.
- The 60-session-day paper-trade evidence floor per [CLAUDE.md §Execution bar](../../CLAUDE.md) becomes the load-bearing pre-live constraint, NOT the backtested-Sharpe gate.

### Trade-offs accepted

- The strategy universe entering paper-trade may be larger under the new rubric than under the old (since fewer strategies null at the design-time gate). Operator review of the KPI report card is required to triage.
- Hansen SPA family p-values become reported KPIs; multiple-testing concern is no longer enforced at the design-time gate. Readers wanting a strict Bonferroni-corrected disposition can compute it from the reported per-arm Sharpe values.
- Backwards-compatibility: existing dispositions tagged `archive(null, sharpe-ci-not-clearing-conjunctive)` etc. need a one-time retag to `archive(complete; KPI: sharpe-vs-passive-positive-weak)` etc. This is a documentation update, not a re-run.
- The **paper-trade clock** (60 session-day evidence floor per CLAUDE.md §Execution bar) effectively replaces the design-time Sharpe gate as the binding pre-live constraint. Strategies that pass Class A gates AND clear paper-trade Sharpe-within-CI per CLAUDE.md §Execution bar are eligible for live promotion. The aspirational MVP is therefore "paper-trade ready" rather than "design-time Sharpe-positive".

### Residual risk

- **False-positive risk** in the strategy universe entering paper-trade. Mitigated by: (a) the binding calibration gates (BSS + reliability), (b) the paper-trade 60-session-day Sharpe-within-CI gate, (c) the kill-switch design (per design.md §11.1).
- **Data leakage** is now the SOLE methodological-correctness gate at the design-time disposition. Mitigated by: (a) PIT canary integration tests per design.md §11.2 prereq 11 (e.g., the H053 NaN-poison structural detector at `tests/integration/test_h053_pit_canaries.py`), (b) the Cycle-4 leak canary suite at `src/skie_ninja/backtest/leak_canaries.py`, (c) the `dual-fit-call observer + TracingArray` proxy wired to every hypothesis's feature factory.
- **The Class B KPI annotations are interpretive, not algorithmic**. Future hypothesis archivists may disagree about the boundary between e.g. `sharpe-vs-passive-positive-weak` vs `sharpe-vs-passive-flat`. The boundary thresholds in §B (ΔSR ≥ 0.20 for "strong", point estimate > 0 for "positive-weak", etc.) are operational pins; tracked under follow-up `P1-DISPOSITION-KPI-ANNOTATION-THRESHOLD-CALIBRATION`.

## Empirical justification

The empirical basis for this ADR is the H053 build sequence's NULL-disposition direction and the H050 production-run-failure record (which never reached a disposition). Per user 2026-05-01 the existing Sharpe-CI gating regime is "the cause of our own failure" — discarding strategies for failing to clear a noisy CI test at modest sample size, when the descriptive evidence (in-sample partial-R², calibration, mediation, mechanism support) supports continued investigation through to paper-trade.

The CLAUDE.md user-global §"Evidence Hierarchy" (peer-reviewed → official docs → standards → vetted forums → reproduction) does NOT mandate a single gating statistic; it mandates evidence quality. A comprehensive KPI report card with binding calibration + leakage gates IS evidence of quality; a single Sharpe-CI gate IS NOT.

The 60-session-day paper-trade Sharpe-within-CI gate per [CLAUDE.md §Execution bar](../../CLAUDE.md) provides empirical Sharpe verification BEFORE live execution, with realized data rather than backtested data. This is the stronger constraint and the natural venue for the Sharpe-evidence requirement that the design-time gate previously enforced.

## References

- [CLAUDE.md "Research philosophy"](../../CLAUDE.md) — null results as valuable as positive results.
- [CLAUDE.md "Evidence bar"](../../CLAUDE.md) — replaced by the §"Adopted" bullet above.
- [CLAUDE.md "Execution bar"](../../CLAUDE.md) — 60-session-day paper-trade Sharpe-within-CI floor.
- [docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md](../research_notes/memo_h050-prodrun-postmortem_2026-04-30.md) — H050 never reached a disposition.
- [docs/audits/audit_trail_2026-05-01_h053-disposition-reversal.md](../audits/audit_trail_2026-05-01_h053-disposition-reversal.md) — H053 Stage-3 disposition was nulled by Daily-block defect, not by gate fairness.
- [src/skie_ninja/backtest/splits.py](../../src/skie_ninja/backtest/splits.py) `cpcv_split` — CPCV scaffolding from Cycle 4; full path reconstruction tracked under `P1-BACKTEST-CPCV` (promoted to BLOCKING per this ADR).
- Bailey, D. H. & López de Prado, M. 2014. "The Deflated Sharpe Ratio." *J Portfolio Management* 40(5):94-107. [DOI 10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094).
- Niculescu-Mizil, A. & Caruana, R. 2005. "Predicting good probabilities with supervised learning." ICML 2005. [DOI 10.1145/1102351.1102430](https://doi.org/10.1145/1102351.1102430).
- López de Prado, M. 2018. *Advances in Financial Machine Learning* §12 (CPCV). Wiley. ISBN 978-1-119-48208-6.

## Follow-ups

- `P1-DISPOSITION-KPI-RETAG-EXISTING-NULLS` — one-time retag of all existing `archive(null, sharpe-ci-...)` records to `archive(complete; KPI: ...)`.
- `P1-DISPOSITION-KPI-ANNOTATION-THRESHOLD-CALIBRATION` — operational thresholds for "strong" / "weak" / "flat" / "negative" annotations.
- `P1-BACKTEST-CPCV` — full CPCV path-reconstruction implementation. **PROMOTED TO BLOCKING-BEFORE-ANY-STAGE-3-RE-RUN-OR-NEW-HYPOTHESIS-DISPOSITION** per this ADR.
- `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE` — re-spec ToD-FE benchmark for single-clock-time predictands; promoted to BLOCKING-BEFORE-NEXT-H053-STAGE-3 (the operational defect identified in the design-audit memo 2026-05-01).
- `P1-H053-DAILY-405-GATE-RECONCILE` — relax Daily gate to `>= 404` OR substrate-side fix; remains BLOCKING-BEFORE-NEXT-H053-STAGE-3.
- `P1-PAPER-TRADE-SHARPE-WITHIN-CI-VERIFICATION-PROTOCOL` — operational protocol for the 60-session-day paper-trade Sharpe-within-CI gate per CLAUDE.md §Execution bar (now load-bearing under this ADR; the prior Sharpe-CI design-time gate is downgraded to KPI).
- `P1-ADR-0003-DOWNGRADE-SPA-TO-KPI` — formally downgrade ADR-0003 SPA-vs-RomanoWolf to KPI scope (this ADR effectively does so; the formal supersession amendment to ADR-0003 is the housekeeping follow-up).
- `P1-ADR-0008-DOWNGRADE-OMEGA-TO-KPI` — same, for ADR-0008 SPA omega method.

This ADR is the canonical reference for the SKIE-Universe project's disposition philosophy from 2026-05-01 forward. All future hypothesis design.md §8/§10 amendments must conform to the three-class rubric defined here.
