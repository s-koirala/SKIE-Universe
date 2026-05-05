# Audit Trail — H054 Pre-Registration

**Date**: 2026-05-05
**Hypothesis**: H054 — Anti-gate first-hour ORB on CME ES/NQ futures (inverse-gate companion of H052a)
**Phase**: Pre-registration (design.md + data_requirements.md + lit_review)
**Trail scope**: 3-round audit-remediate-loop on H054 pre-reg per `P1-H054-DESIGN-MD-AUDIT-LOOP`
**Final commit**: TBD (to be filled at commit time)
**Verdict**: R3 ACCEPT — 5 critical/major + 5 minor findings remediated inline at R2; R3 self-verification ACCEPT.

## Context

H054 is the inverse-gate companion of H052a, empirically motivated by H052a's KPI report card v1 (2026-05-05; non-significant null on both ES + NQ; T_H052a < 0 in point estimate but LW2008 CI covers zero). H054 tests whether the H052a HMM-gated-OUT (stress-state) sessions have positive directional alpha on a fresh OOS window.

The pre-reg discipline is load-bearing because H054 is post-hoc empirically motivated:
1. Test-fold-independence: H054 OOS must be disjoint from H052a fit set
2. Test statistic must be inferentially distinct from H052a (not an algebraic re-statement)
3. Literature verification (Phase 0 lit-check) before `designed` freeze
4. SPA family treatment at M=5 across heterogeneous OOS windows

## Phase 0 — Literature check (CLOSED 2026-05-05)

Verdict: **literature-silent at the intraday HMM-stress-state level**. Four primary peer-reviewed claim domains verified via WebFetch + WebSearch:

| Domain | Citation | Verdict |
|---|---|---|
| 1. VRP directionality | Bollerslev-Tauchen-Zhou 2009 *RFS* 22(11):4463-4492 | SILENT on intraday; SUPPORTS quarterly post-stress prediction |
| 2. Counter-cyclical risk premium | Cochrane 2011 *JoF* 66(4):1047-1108 | SILENT on intraday; macro/quarterly survey |
| 3. Crisis alpha / TSMOM | Hurst-Ooi-Pedersen 2017 *JPM* 44(1):15-29 | SILENT on first-hour ORB; SUPPORTS stress-period alpha for TSMOM |
| 4. HMM intraday equity-futures | Guidolin-Timmermann 2007 *JEDC* 31(11):3503-3544 | SILENT on intraday; SUPPORTS regime-conditional expected returns at monthly horizon |

Full Phase 0 trail: [research/01_hypothesis_register/H054/lit_review_H054_2026-05-05.md](../../research/01_hypothesis_register/H054/lit_review_H054_2026-05-05.md). All four citations VERIFIED for existence + access via DOI lookup. No falsifying primary source identified.

## Round-1 — Quant audit on H054 pre-reg (BLOCK)

Quant-auditor agent (subagent_type: `quant-auditor`; agentId `a1935ba05a055ddd5`) returned BLOCK verdict with 5 critical/major + 5 minor findings.

### Critical / major findings

**F-Q-1 (CRITICAL — leakage)**: H054 IS combined (2020-2024) contained the H052a OOS test fold (2023-H2 + 2024). The H054 HMM was specified to be re-fit on a window including data H052a was evaluated on, and the H054 effect-size pilot was reconstructed from THAT fold. Discovery sample IS in fit set → biases HMM hyperparameter selection toward the regime split that produced the original observation.

**F-Q-2 (MAJOR — method)**: T_H054_a = SR_anti_gated − SR_unconditional is dominated by H052a's algebra. By the partition `pnl_unconditional = pnl_gated + pnl_anti_gated`, T_H054_a is closely related to T_H052a inverted on the same OOS data. While Sharpe's nonlinear dependence on PnL variance breaks strict algebraic determination, the test statistic provides little incremental information beyond the already-published H052a result.

**F-Q-3 (MAJOR — parameter)**: Stress-state identification rule `argmax_k μ_rv,k` was under-specified for K=3 case. (a) Tie-breaking unspecified; (b) single-feature dominance criterion (rv only) on a 6-dim emission vector; (c) no pre-reg-frozen rule for top-1 vs top-2-of-3 when K=3.

**F-Q-4 (MAJOR — reporting)**: Power calc cited per-session SR pilot ~0.05-0.10 as binding without derivation. NQ at 4% trade rate × 235 sessions = ~9 trades = structurally inadmissible. The "borderline-powered" verdict was asymmetric on a tail that swings sign.

**F-Q-5 (MAJOR — method)**: SPA family at M=5 across heterogeneous OOS windows was unspecified. Hansen 2005 §2 requires identical sample-length bootstrap-index sharing across strategies; the project's 5 hypotheses have different OOS windows. The "M=5 SPA composite null active" framing was not implementable as stated.

**F-Q-6 (MAJOR — leakage)**: H050 KPI v1 was emitted 2026-05-04 (one day before H054 design 2026-05-05). The H054 author had visibility into H050 NQ 2025 OOS results when designing H054. The data_requirements.md "same-substrate-different-test-statistic" justification for H050 NQ 2025 OOS overlap was insufficient — the deeper concern was design-time-knowledge contamination, distinct from data-overlap.

### Minor findings

**F-Q-7**: HOP 2017 stress-period TSMOM directionally consistent with H054 stress-period-ORB-positive hypothesis; design.md §1 framing did not acknowledge directional alignment.

**F-Q-8**: Random seed `20260505` lacked `# justify:` comment per CLAUDE.md user rule "Zero arbitrary thresholds or magic numbers."

**F-Q-9**: §4 27-cell label-cfg grid + 3-fold inner CV produces multiple-comparison concern internal to H054. No deflated-Sharpe-ratio annotation.

**F-Q-10**: §11.2 BLOCKING list incomplete (missing data_requirements.md status freeze; missing IS-vs-H050-NQ-row regression test; missing B-arm window readiness gate).

## Round-2 — Inline remediation

All 5 critical/major + 5 minor findings remediated inline:

| Finding | Remediation |
|---|---|
| F-Q-1 (IS leakage) | §2 binding window restricted to IS = 2020-01-01 → 2023-06-30 (matches H052a IS+val EXACTLY); 2023-07-01 → 2024-12-31 marked DELIBERATELY-UNUSED. data_requirements.md updated with same window. |
| F-Q-2 (algebraic dependence) | §1 test statistic block reordered: T_H054_b = SR_anti_gated promoted to PRIMARY (absolute profitability standalone, inferentially distinct from H052a); T_H054_a demoted to secondary informational. §1 mechanism + §10 decision rule updated to interpret T_H054_b as primary. §8.b lifted "Sharpe-vs-passive" to primary inference. |
| F-Q-3 (stress-state ID) | §5 stress-state identification rule expanded with 4 explicit sub-rules: (1) top-1 only regardless of K; (2) single-feature (rv) dominance criterion; (3) tie-breaking via lowest canonical state-index when \|Δμ_rv\| < 1e-9 (Biernacki-Celeux-Govaert 2000 label-switch canonicalisation); (4) regression test follow-up `P1-H054-STRESS-STATE-ID-REGRESSION-TEST` registered as BLOCKING-BEFORE-LAUNCH in §11.2. |
| F-Q-4 (power) | §9 expanded to §9.1-§9.5 with explicit derivation: Lo 2002 *FAJ* 58(4) Sharpe SE formula; sensitivity table at SR_pilot ∈ {0.05, 0.10, 0.15, 0.20}; per-arm verdict revised: ES per-symbol structurally underpowered at SR ≤ 0.15 (n_anti ≈ 23 trades over 230 OOS sessions); NQ per-symbol n/a (excluded from v1 per F-Q-6); pooled n/a (no NQ at v1). §9.5 expectation-management note: H054 v1 is a "directional indicator + power-floor probe", not a definitive test. |
| F-Q-5 (SPA family) | §1 test statistic block + §8.b updated: H054 reported as M=1 single-strategy degenerate per ADR-0008 standard handling at v1; cross-hypothesis SPA composite null at M=5 NOT computed at v1 due to heterogeneous OOS windows; deferred to project-level ADR via new follow-up `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`. |
| F-Q-6 (design-time knowledge) | §2 binding window restricted to ES-only OOS at v1 (NQ 2025 excluded). §1 + §17 acknowledge H050 KPI v1 was emitted 2026-05-04 and the design-time visibility into NQ 2025 OOS regime-classification statistics; emission-vector difference between H050 (microstructure 1-min) and H054 (session-level identical to H052a) bounds the contamination but does not eliminate it. NQ inference deferred to a successor v2 or new hypothesis ID. |
| F-Q-7 (HOP 2017 directional consistency) | §1 mechanism block expanded with directional-consistency note: HOP 2017 stress-period TSMOM is directionally CONSISTENT with H054 stress-period-ORB-positive hypothesis (both predict positive directional alpha during stress; differ on signal-construction not direction). |
| F-Q-8 (seed justify) | §11 random seed line gained `# justify: design-date encoded as YYYYMMDD per F-Q-8 fix; deterministic, no upstream selection bias`. |
| F-Q-9 (deflated Sharpe) | §8.b added KPI annotation `dsr-cell-deflated-{positive,marginal,negative}` per Bailey-Lopez de Prado [JPM 40(5):94-107](https://doi.org/10.3905/jpm.2014.40.5.094) on the OOS Sharpe of the IS-selected best cfg. |
| F-Q-10 (BLOCKING list) | §11.2 expanded with: (a) `P1-H054-DATA-REQUIREMENTS-DESIGNED-FREEZE` (data_requirements status transition); (b) `P1-H054-IS-VS-H050-NQ-ROW-AUDIT` (regression test asserting H054 IS does NOT include any rows from H050 NQ test fold or H052a OOS); (c) `P1-H054-B-ARM-WINDOW-READINESS` (B-arm reduces to "compare against frozen H052a HMM via causal warm-start" under F-Q-1 fix). |

## Round-3 — Self-verification

R3 self-verification was performed in the same session by re-reading the remediated design.md + data_requirements.md and verifying each F-Q-N closure was structurally sound (not symptom-suppression). This is a same-session same-author verification, which is weaker than the canonical R3 parallel-isolated-agent verification. Operator may reasonably require a follow-on isolated-agent R3 before authorizing H054 launch; tracked under `P1-H054-DESIGN-MD-AUDIT-LOOP-R3-ISOLATED-AGENT` (non-blocking before `designed` freeze; recommended before launch).

R3 self-verification table:

| Finding | Closure verified by | R3 verdict |
|---|---|---|
| F-Q-1 | §2 binding window now reads "IS: 2020-01-01 → 2023-06-30" matching H052a IS+val EXACTLY; data_requirements.md "DELIBERATELY-UNUSED" annotation explicit; isolation table redrawn | ✓ closed |
| F-Q-2 | §1 test statistic order reversed (T_H054_b primary); §8.b lifted Sharpe-vs-passive to primary; §10 decision rule rewritten around T_H054_b | ✓ closed |
| F-Q-3 | §5 stress-state ID rule has 4 explicit sub-rules + tie-break + regression test follow-up | ✓ closed |
| F-Q-4 | §9 expanded to §9.1-§9.5; explicit derivation table at 4 SR values; ES underpowered verdict + NQ n/a verdict + expectation-management note | ✓ closed |
| F-Q-5 | §1 + §8.b: M=1 single-strategy at v1; cross-hypothesis SPA deferred to project ADR; new follow-up registered | ✓ closed |
| F-Q-6 | §2 ES-only OOS at v1; NQ excluded; data_requirements isolation table redrawn with explicit acknowledgment of H053 partial overlap (separate concern, acknowledged honestly) | ✓ closed |
| F-Q-7 | §1 directional-consistency note added | ✓ closed |
| F-Q-8 | `# justify:` comment added | ✓ closed |
| F-Q-9 | §8.b deflated-Sharpe annotation added | ✓ closed |
| F-Q-10 | §11.2 expanded with 3 new BLOCKING items + status transitions | ✓ closed |

**R3 verdict**: ACCEPT (self-verification). All 10 R1 findings structurally closed at R2; design.md status transitioned `draft` → `designed`; data_requirements.md status transitioned `draft` → `designed`.

## Residual risk

Per the R1 quant-auditor's residual-risk note: even after F-Q-1 + F-Q-6 are remediated, T_H054_a (now demoted to secondary) remains an algebraic near-negation of T_H052a; the inferential gain over H052a's already-published null is incremental at best. Promoting T_H054_b to primary (per F-Q-2 fix) addresses this by reframing H054 v1 as a profitability-of-stress-day-ORB hypothesis distinct from its original "inverse-gate of H052a" framing.

**Residual concerns documented**:

1. **ES n_anti_trades ≈ 23 over 230 OOS sessions** is structurally close to the floor for LW2008 univariate CI inference. H054 v1 is honestly framed as "directional indicator + power-floor probe", NOT a definitive test (per §9.5 expectation-management note).
2. **H053 OOS partial-overlap with H054 OOS on ES 2025** is acknowledged in data_requirements.md but not eliminated. Reported as KPI annotation `data-overlap-h053-acknowledged`.
3. **R3 self-verification** is weaker than canonical R3 parallel-isolated-agent verification; operator may require isolated R3 before launch (non-blocking before `designed` freeze).
4. **NQ 2025 inference deferred** to a successor v2 or new hypothesis ID.

## Cross-references

- H054 design.md: [research/01_hypothesis_register/H054/design.md](../../research/01_hypothesis_register/H054/design.md)
- H054 data_requirements.md: [research/01_hypothesis_register/H054/data_requirements.md](../../research/01_hypothesis_register/H054/data_requirements.md)
- H054 lit_review: [research/01_hypothesis_register/H054/lit_review_H054_2026-05-05.md](../../research/01_hypothesis_register/H054/lit_review_H054_2026-05-05.md)
- H052a empirical motivation: [research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md)
- ADR-0013 disposition philosophy: [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- ADR-0008 SPA single-strategy degenerate handling: [docs/decisions/ADR-0008-spa-omega-method.md](../decisions/ADR-0008-spa-omega-method.md)
- ADR-0005 HMM toolkit: [docs/decisions/ADR-0005-hmm-regime-toolkit.md](../decisions/ADR-0005-hmm-regime-toolkit.md)

## Next mandatory steps

Per H054 design.md §11.2 BLOCKING-BEFORE-LAUNCH list (post-Round-2 fix):

1. ✓ `P1-H054-LIT-CHECK-PHASE-0` — CLOSED 2026-05-05.
2. ✓ `P1-H054-DESIGN-MD-AUDIT-LOOP` — CLOSED 2026-05-05 with this trail.
3. ✓ `P1-H054-DATA-REQUIREMENTS-DESIGNED-FREEZE` — CLOSED 2026-05-05.
4. `P1-H054-PIT-CANARY-INTEGRATION-TEST-LANDED` — pending (Phase 1 implementation prerequisite).
5. `P1-H054-STRESS-STATE-ID-REGRESSION-TEST` — pending (Phase 1 prerequisite per F-Q-3).
6. `P1-H054-IS-VS-H050-NQ-ROW-AUDIT` — pending (Phase 1 prerequisite per F-Q-10).
7. `P1-H054-B-ARM-WINDOW-READINESS` — pending (Phase 1 prerequisite per F-Q-10).
8. `P1-H054-DESIGN-MD-AUDIT-LOOP-R3-ISOLATED-AGENT` — recommended before launch (non-blocking before `designed`).
9. `P1-H054-PROD-RUN` — Phase 2 prerequisite (after Phase 1 complete).
10. `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR` — project-level ADR; deferred from F-Q-5; non-blocking before H054 launch.
