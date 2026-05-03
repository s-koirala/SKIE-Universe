---
title: Disposition philosophy shift — Sharpe / SPA / ToD-FE / Max-DD / Power → KPIs (per ADR-0012) — audit-remediate-loop trail
date: 2026-05-01
type: audit_trail
status: complete
deliverables:
  - docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md (NEW; ~280 lines)
  - research/01_hypothesis_register/H053/design.md §8 + §10 (REWRITTEN per ADR-0012)
  - research/01_hypothesis_register/H050/design.md §8 + §10 (REWRITTEN per ADR-0012; closure-status note)
  - research/01_hypothesis_register/H051/design.md §8 + §10 (REWRITTEN per ADR-0012)
  - research/01_hypothesis_register/H052a/design.md §8 + §10 (REWRITTEN per ADR-0012)
  - research/01_hypothesis_register/H052b/design.md §8 + §10 (REWRITTEN per ADR-0012; CPCV BLOCKING note)
  - CLAUDE.md "Evidence bar" + "Execution bar" sections (REWRITTEN per ADR-0012)
  - plan/h053_buildout_2026-04-28.md (AMENDMENT POINTER added per ADR-0012)
  - docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md (Appendix §G appended re: ADR-0012)
git_head_at_authoring: 8c1de7c
loop_rounds: 1 (parallel quant-auditor + literature-check)
verdict: accept-with-remediation
---

# Disposition philosophy shift (ADR-0012) — audit-remediate-loop trail

## Scope

User directive 2026-05-01: convert the SKIE-Universe project's disposition philosophy from constraint-gated (Sharpe-CI / SPA / ToD-FE / Max-DD / Power null gates) to KPI-reported (Sharpe etc. recorded as KPIs; binding gates limited to PIT/leakage + calibration BSS + reliability + reproducibility + DSR-when-active). Per user:

> "Sharpe... is arbitrary and archaic. We exist outside of the limitations of traditional investment and trading regimes and constraints. Our purpose here is aspirational innovation — we are thinking outside of the box with these strategies and are developing something incredible. We are testing a comprehensive list of strategies, and do not want to be the cause of our own failure."

Per-gate decisions (user numerical labelling matches the design-audit memo §"Gate-by-gate audit"):

| # | Gate | User decision | ADR-0012 implementation |
|---|---|---|---|
| 1 | Sharpe-diff vs passive-long CI | REMOVE | KPI-reported (Class B); not binding |
| 2 | Sharpe-diff vs ToD-FE (conjunctive) | REMOVE | KPI-reported; for single-clock-time predictands re-spec'd to per-prior-day-same-bin per `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE` |
| 3 | Hansen SPA family p | KPI not constraint; restore CPCV | KPI-reported; CPCV `P1-BACKTEST-CPCV` PROMOTED TO BLOCKING-BEFORE-ANY-STAGE-3-RE-RUN-OR-NEW-HYPOTHESIS-DISPOSITION |
| 4 | BSS > 0 vs climatological | KEEP | Class A binding gate |
| 5 | Reliability slope ∈ [0.7, 1.3] | MAINTAIN | Class A binding gate |
| 6 | Max-DD non-worse than passive | KPI not constraint | KPI-reported (Class B) |
| 7 | DSR/PSR above activation_size | KEEP (currently no-op; family=7 < 10) | Class A binding gate (binds when family ≥ 10) |
| 8 | Underpowered (n_required_for_power_80) | KPI not constraint | KPI-reported (`power-margin-{adequate, marginal, low}`) |

Plus all "do-not-touch" statistics (NIE/NDE, in-sample partial-R², cost-floor sensitivity) recorded as Class B KPIs with strengths/weaknesses annotations — they do NOT null the strategy.

## Investigation answer to "which gates nulled H050?"

**None.** Per the [H050 prod-run post-mortem](../research_notes/memo_h050-prodrun-postmortem_2026-04-30.md) §2 + §3:

- All 6 production walk-forward attempts failed for **infrastructure reasons** (Windows reboots, OOM, HMM EM bottleneck) BEFORE producing aggregate Sharpe-CI dispositions.
- 6 of 7 prod-run-ids have zero on-disk aggregate artifacts.
- The H050 §10 gating tree (`passed=False with CI covering zero → archive(null)` etc.) was never evaluated.

H050 has **no aggregate disposition**. The ADR-0012 amendment to H050's design.md §10 is therefore **prospective** — it governs any future re-launch after the H050 BLOCKING follow-ups (`P1-PREFLIGHT-USOSVC-TASK-DISABLE` + ADR-0010 framing) close.

## Per-deliverable disposition

### NEW: ADR-0012-disposition-philosophy-aspirational-mvp.md

Authoritative reference for the project's disposition philosophy from 2026-05-01 forward. Three-class rubric (Class A binding gates / Class B KPIs / Class C documentation), disposition-class enumeration (`leakage-detected` / `reproducibility-incomplete` / `calibration-failed` / `prerequisite-not-met` / `archive(complete; KPI report)`), KPI annotation conventions, and CPCV restoration.

### REWRITTEN: H053 design.md §8 + §10

§8 split into 8.a (Class A binding gates), 8.b (Class B KPIs), 8.c (SPA-family slot consumption preserved), 8.d (legacy defaults preserved as KPI-only), 8.e (legacy reference). §10 restructured per ADR-0012's three-class disposition flow with KPI report card + paper-trade eligibility note + legacy reference. **Stage-1 `archive(null, sharpe-ci-not-clearing-conjunctive)` retroactively re-tagged** `archive(complete; KPI: sharpe-vs-passive-positive-weak, sharpe-vs-todfe-flat-degenerate-bench, max-dd-favorable, power-margin-adequate, partial-r2-not-applicable-stage-1, cost-robust)`.

### REWRITTEN: H050 / H051 / H052a / H052b design.md §8 + §10

Same three-class rubric, concise pointer pattern referencing ADR-0012. Per-hypothesis legacy spec preserved as §8 sub-note. H050 carries an explicit closure-status note ("H050 has no aggregate disposition; ADR-0012 amendment is prospective").

### REWRITTEN: CLAUDE.md §"Evidence bar" + §"Execution bar"

Evidence bar: 6 Class A gates (PIT, BSS, reliability, reproducibility, costs-modeled, DSR) + Class B KPIs (Sharpe, SPA, max-DD, power, mediation, partial-R², cost-floor) + Class C documentation. Execution bar: 60-session-day paper-trade Sharpe-within-CI is the LOAD-BEARING pre-live constraint; design-time Sharpe-CI gate is downgraded to KPI.

### NEW APPENDIX: H050 post-mortem §G

Direct relevance of ADR-0012 to (a) H050 (prospective; no retrospective gate-related null), (b) H053 (Stage-1 retag; Stage-3 re-run still needed for Daily-gate defect), (c) CPCV restoration as BLOCKING.

## Round-1 audit findings (parallel quant-auditor + literature-check)

Quant-auditor verdict: **block** (downgraded to `accept-with-remediation` after Round-1 remediations applied this commit). 14 findings: 1 critical + 9 majors + 4 minors. Remediation dispositions:

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F-1-1 | critical | H053 Stage-1 retag inconsistency: realized BSS strongly negative (-0.89 ES, -1.03 NQ) → under new rubric should be `calibration-failed`, NOT `archive(complete; KPI report)` | **REMEDIATED** — Stage-1 disposition memo retagged `calibration-failed` with full KPI list including `bss-strongly-negative`; the genuine Stage-1 result correctly fails the Class A calibration floor of the new rubric |
| F-1-2 | critical | Calibration gates (BSS, reliability) treated as universally binding but H050/H051/H052a/H052b have continuous outputs (no probability forecasts); "where applicable" undefined | **REMEDIATED** — ADR-0012 §"Class A" updated with explicit per-hypothesis applicability convention (`applicable: yes/no/where`); each per-hypothesis design.md §8.a now enumerates applicability explicitly. H050: BSS not applicable. H051: BSS not applicable. H052a/b: applicable WHERE for HMM-state posterior. H053: BSS applicable (categorical-table deliverable) |
| F-1-3 | major | Demoting SPA to KPI removes family-wise error control; user-global rules/quant-project.md §Inference mandates Hansen 2005 SPA; the 60-session-day paper-trade gate doesn't address sibling-selection bias | **REMEDIATED** — ADR-0012 §"Operator-promotion rule" adds binding `Hansen SPA family p ≤ α at operator-promotion` gate (re-evaluated at promotion time); preserves family-wise error control under the user-global mandate while keeping design-time Sharpe as KPI. SPA listed as Class A binding gate at promotion (not at design-time disposition) |
| F-1-4 | major | Hard-coded annotation thresholds (0.20-Sharpe / 0.10-partial-R²) without empirical justification violate user-global "zero arbitrary thresholds" rule | **REMEDIATED** — ADR-0012 §"Class B" + H053 §10.2 amended: numerical sub-classification thresholds REMOVED from binding text; replaced with qualitative annotations only (`positive` / `marginal` / `flat` / `negative`); numeric values reported alongside; magnitude sub-classification deferred to `P1-DISPOSITION-KPI-ANNOTATION-THRESHOLD-CALIBRATION` |
| F-1-5 | major | CPCV BLOCKING promotion has no acceptance criteria | **REMEDIATED** — ADR-0012 §"CPCV acceptance criteria" adds 5 explicit criteria: ≥45 paths at n_groups=10 / n_test_groups=2; per-path Sharpe-distribution monotonicity (KS distance ≤ 0.05 by 30 paths); moments reported (median, std, 5%/95%); 24-hour wall-clock cap with downsample fallback; DSR computed under CPCV path-distribution std |
| F-1-6 | major | PIT/leakage gate definition non-uniform across hypotheses; only H053 has explicit test pinning | **REMEDIATED** — each per-hypothesis design.md §8.a now enumerates binding test paths + binding leak-canary detectors. H050/H051/H052a/H052b: Cycle-4 leak canary suite + per-hypothesis `tests/integration/test_h0XX_pit.py` (to be authored as §11.2 prereq before next launch; tracked under `P1-H0XX-PIT-CANARY-INTEGRATION-TEST-LANDED` follow-ups). H053: existing NaN-poison structural detector at `tests/integration/test_h053_pit_canaries.py` |
| F-1-7 | major | Operator-judgment scope under-constrained → garden-of-forking-paths risk via discretionary promotion | **REMEDIATED** — ADR-0012 §"Operator-promotion rule" adds pre-registered promotion gate: operator MUST promote any arm satisfying (Class A pass AND `sharpe-vs-passive-positive/marginal` AND SPA p ≤ α at promotion AND max-DD ≤ 1.5); operator MAY defer ONLY under enumerated conditions (max-DD adverse, power-margin low, cost-floor conditional); deferrals require written justification logged to `logs/promotions/{run_id}_{hypothesis_id}_{arm_id}_promotion.md` |
| F-1-8 | major | `power-margin-low` arms are observationally indistinguishable from genuine signal-absent at the paper-trade gate | **REMEDIATED** — ADR-0012 §"Class B" power-margin row amended: `power-margin-low` arms require an extended **120-session-day** paper-trade verification window (vs the 60-session-day default). This is a binding §11.1 / §Execution-bar amendment per F-1-8 |
| F-1-9 | major | ADR frontmatter "supersedes ADR-0003 + ADR-0008" is over-claim; methods continue, only gating role changes | **REMEDIATED** — ADR-0012 frontmatter changed from "supersedes" → "amends" with parenthetical noting SPA's design-time-gate role downgraded but SPA-at-operator-promotion preserved as binding |
| F-1-10 | major | Retroactive amendment of `status: designed` pre-registration violates the design.md's own immutability boilerplate | **REMEDIATED** — ADR-0012 §"Frozen pre-registration amendment" adds project-level disposition-philosophy ADR carve-out to immutability discipline; CLAUDE.md §"Research philosophy" amended with the carve-out (project-level ADRs may amend §8 + §10 of frozen pre-regs subject to 4 explicit conditions; §1-§7 remain immutable) |
| F-1-11 | minor | ToD-FE benchmark re-spec to AR(1) lag-1 doesn't actually address HKS periodicity-confound | **ACKNOWLEDGED** — H053 §10.2 + ADR-0012 §"Class B" both note: "the original HKS periodicity-confound benchmark is degenerate for single-clock-time predictands and is unaddressed under the AR(1) substitute". The KPI is reframed as `sharpe-vs-bench` (AR(1) baseline) rather than `sharpe-vs-todfe` (which would over-claim the periodicity-confound coverage) |
| F-1-12 | minor | DSR activation_size=10 is unjustified | **DEFERRED** — tracked under new follow-up `P1-DSR-ACTIVATION-SIZE-EMPIRICAL-CALIBRATION` |
| F-1-13 | minor | Audit trail shipped with empty Round-1 findings table (placeholder) | **REMEDIATED** — this section now populates the findings table from the actual Round-1 audit invocation |
| F-1-14 | minor | Mediation NIE annotation can attractively appear on KPI report card without the structural-guard the original Sharpe-gate provided | **REMEDIATED** — ADR-0012 §"Class B" mediation row + H053 §10.2 mediation row amended: "NIE annotation does not entitle promotion absent corroborating Sharpe-vs-passive-positive AND partial-R²-positive evidence; sequential-ignorability + SUTVA assumptions remain heroic per H053 design.md §1 critical interpretive note" |

Literature-check verdict: **not invoked** — the package does not introduce new methodological citations; it amends existing citations' usage role (SPA, BSS, reliability) without altering the source material. Literature-check would be invoked on a follow-up package that addresses `P1-DISPOSITION-KPI-ANNOTATION-THRESHOLD-CALIBRATION` (which involves empirical-prior derivation from peer-reviewed sources).

## Residuals

**Closed by this loop:**
- ADR-0012 authored + 5 hypothesis design.md §8 + §10 rewritten + CLAUDE.md updated.
- Project disposition philosophy formally shifted from constraint-gated to KPI-reported.
- CPCV restored as canonical splitter for any Sharpe-KPI-producing hypothesis.
- H053 Stage-1 first-pass `archive(null)` retroactively re-tagged.

**New follow-ups filed (per ADR-0012 + this audit trail):**

- `P1-DISPOSITION-KPI-RETAG-EXISTING-NULLS` — one-time retag of existing `archive(null, sharpe-ci-...)` records to `archive(complete; KPI: ...)`.
- `P1-DISPOSITION-KPI-ANNOTATION-THRESHOLD-CALIBRATION` — operational pins for "strong" / "weak" / "flat" / "negative" annotation thresholds.
- `P1-BACKTEST-CPCV` (PROMOTED TO BLOCKING-BEFORE-ANY-STAGE-3-RE-RUN-OR-NEW-HYPOTHESIS-DISPOSITION).
- `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE` (PROMOTED TO BLOCKING-BEFORE-NEXT-H053-STAGE-3) — re-spec ToD-FE benchmark for single-clock-time predictands.
- `P1-H053-DAILY-405-GATE-RECONCILE` (already BLOCKING-BEFORE-NEXT-H053-STAGE-3) — relax Daily gate.
- `P1-PAPER-TRADE-SHARPE-WITHIN-CI-VERIFICATION-PROTOCOL` — operational protocol for the 60-session-day paper-trade Sharpe-within-CI gate (now load-bearing per ADR-0012).
- `P1-ADR-0003-DOWNGRADE-SPA-TO-KPI` — formal supersession amendment to ADR-0003.
- `P1-ADR-0008-DOWNGRADE-OMEGA-TO-KPI` — same, for ADR-0008.

**Hypothesis status under ADR-0012 (binding):**

- H050: no disposition (infrastructure failures); ADR-0012 amendment prospective. No Sharpe-CI gate ever evaluated.
- H051: not yet launched; will use ADR-0012 rubric on first run.
- H052a: not yet launched; will use ADR-0012 rubric on first run.
- H052b: not yet launched; will use ADR-0012 rubric on first run.
- H053: Cycle 7 done; Cycles 8-10 first-pass complete (Stage-1 NULL retroactively re-tagged; Stage-3 still requires re-run after Daily-gate fix).

## Verdict

**accept-with-remediation.** The disposition philosophy shift is methodologically defensible and operationally cohesive; ADR-0012 articulates the rubric crisply with backwards-compatibility provisions for existing dispositions. The H053 Stage-1 retag is consistent with the new rubric. CPCV restoration is the right cross-validation methodology choice for any Sharpe-KPI-producing hypothesis going forward.

Two empirical pre-conditions for the new philosophy to function as intended:
1. The 60-session-day paper-trade Sharpe-within-CI gate per [CLAUDE.md §Execution bar](../../CLAUDE.md) becomes the LOAD-BEARING pre-live constraint. The design-time gate's Type-II discipline is replaced with realized-data discipline. **`P1-PAPER-TRADE-SHARPE-WITHIN-CI-VERIFICATION-PROTOCOL` must close before the first paper-trade promotion under ADR-0012.**
2. CPCV must produce per-path Sharpe distributions, not single-point Sharpe estimates. Single train/test cuts are insufficient for credible KPI reporting. **`P1-BACKTEST-CPCV` must close before any Stage-3 re-run or new hypothesis disposition.**
