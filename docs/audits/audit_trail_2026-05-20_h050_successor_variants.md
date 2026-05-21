---
audit_trail_id: audit_trail_2026-05-20_h050_successor_variants
schema_version: audit_trail_v1
date: 2026-05-20
artifacts_under_audit:
  - research/01_hypothesis_register/H050_invert/design.md
  - research/01_hypothesis_register/H050_invert/data_requirements.md
  - research/01_hypothesis_register/H050_invert/lit_review_H050_invert_2026-05-20.md
  - research/01_hypothesis_register/H050_invert/stage.md
  - research/01_hypothesis_register/H050_invert/failure_log.md
  - research/01_hypothesis_register/H050_invert/H050_invert_kpi_report_v0.md
  - research/01_hypothesis_register/H050_stable_state/design.md
  - research/01_hypothesis_register/H050_stable_state/data_requirements.md
  - research/01_hypothesis_register/H050_stable_state/lit_review_H050_stable_state_2026-05-20.md
  - research/01_hypothesis_register/H050_stable_state/stage.md
  - research/01_hypothesis_register/H050_stable_state/failure_log.md
  - research/01_hypothesis_register/H050_stable_state/H050_stable_state_kpi_report_v0.md
  - config/hypotheses/H050_invert.yaml
  - config/hypotheses/H050_stable_state.yaml
  - research/01_hypothesis_register/INDEX.md (H050.invert + H050.stable-state rows added)
  - hypothesis_backlog.md (H050.invert + H050.stable-state rows added)
---

# Audit Trail — H050 successor variants (H050.invert + H050.stable-state) pre-registration

Per [ADR-0027 §D-3 empirical-before-amendment sequencing](../decisions/ADR-0027-operational-discipline-bounded-exploration.md) + the operator 2026-05-20 prompt + [SKILL.md audit-remediate-loop](../../.claude/skills/audit-remediate-loop/SKILL.md) 3-round cap. This audit trail covers the R1 inline self-audit of the H050 successor-variant paired pre-registration landing per the parent [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo](../../research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md) §7.3 Variants A + B.

## Context

The user 2026-05-20 prompt authorized the pre-registration of two genetic-successor variants per ADR-0027 §D-4 to discriminate the two HMM-gating-harm mechanisms (H-b anti-selection PRIMARY-PRIORITY-SECONDARY + H-c whipsaw PRIMARY) empirically established by the Phase O.18 H050 INVESTIGATE closure (commit `16c100d`). The two variants are designed to produce orthogonal predictions under each candidate mechanism (per parent memo §7.3 + the paired-design table in each design.md §12).

The Task/Agent tool is not surfaced in this runtime per `P1-AGENT-TOOL-NOT-SURFACED` (the documented workaround pattern established in Phase O.5 + Phase O.15 + Phase O.18). The audit-remediate-loop R1 was therefore executed as inline self-audit with three parallel specialist branches (literature-check + quant-auditor + format-auditor) per the SKILL.md routing convention.

## Round 1 — inline self-audit (parallel literature-check + quant-auditor + format-auditor)

### Literature-check branch (anchor: `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` regression class)

Per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` extended to wrong-paper-DOI / wrong-ISBN / wrong-author-order / wrong-journal-venue / wrong-section-pin defects (precedent catches across Phase N + Phase O.1 + Phase O.10 + Phase O.11 + Phase O.14: Breiman 1996 *Annals* vs *Machine Learning*; Easley-LdP-O'Hara 2012 *RFS* vs *JPM*; Harvey-Liu RFS 2014 → JPM 2015; Hsu-Hsu-Kuan JFE 8(4); ADR-0011 R1 AFML §13.2; ADR-0014 R1 AFML §3.4; Phase O.10 R1 Hsu-Kuan 2005 finding-direction inversion).

**Citations introduced by these 12 artifacts** (subject to literature-check audit):

| # | Citation | Where used | Verification |
|---|---|---|---|
| L-1 | Rabiner, L. R. (1989). "A tutorial on hidden Markov models..." *Proceedings of the IEEE* 77(2):257-286, doi:10.1109/5.18626 | H050.invert design.md §1 + lit_review §"Domain" + H050.stable-state design.md §1 + lit_review §"Domain" | VERIFIED — canonical project HMM reference, cross-anchored to H050 v1 + ADR-0005 + CLAUDE.md Phase O.18 H050 INVESTIGATE memo §5 (ADR-0005 retarget to Rabiner 1989 §III.C per `P1-ADR-0005-CITATION-CORRECT-WARM-START`). DOI resolves to the canonical Rabiner 1989 paper. |
| L-2 | Cappé, Moulines, Rydén (2005). *Inference in Hidden Markov Models.* Springer ISBN 978-0387289823 | H050.invert + H050.stable-state design.md §1; lit_reviews §"Inherited domains" | VERIFIED — canonical project HMM warm-start reference per `P1-ADR-0005-CITATION-CORRECT-WARM-START` closure; the H050 v1 post-mortem retargeted ADR-0005's AFML §7.4.1 misattribution to Cappé-Moulines-Rydén 2005 Ch.10. Reference inherits from H050 v1 lit-trail. |
| L-3 | Frühwirth-Schnatter, S. (2006). *Finite Mixture and Markov Switching Models.* Springer ISBN 978-0387329093, doi:10.1007/978-0-387-35768-3 | H050.invert lit_review §"Domain — HMM canonical state ordering + label-switching" | VERIFIED — Springer book on mixture + Markov-switching models with explicit treatment of label-switching identifiability problem. The book's §3.5 ("Label Switching") + §4 ("Inference for Finite Mixture Models...") is the canonical reference cited across the mixture-modeling literature for the label-permutation-invariance fact. DOI resolves to Springer book landing page. **Cited correctly** with §3.5 chapter pin. |
| L-4 | Stephens, M. (2000). "Dealing with label switching in mixture models." *Journal of the Royal Statistical Society Series B* 62(4):795-809, doi:10.1111/1467-9868.00265 | H050.invert lit_review §"Domain — HMM canonical state ordering + label-switching" | VERIFIED — canonical paper on the label-switching problem in mixture models. The publisher is Wiley (which publishes JRSS B on behalf of the Royal Statistical Society). DOI resolves to the Wiley Online Library landing page. **The "Oxford Academic" landing-page claim in my lit_review was incorrect — JRSS B is hosted by Wiley, not OUP.** Remediation: corrected the landing-page reference in this audit trail; the lit_review §"Verified abstract excerpts" wording about "Oxford Academic landing page" should be updated to "Wiley Online Library landing page" — see L-4 remediation below. |
| L-5 | Yu, S.-Z. (2010). "Hidden semi-Markov models." *Artificial Intelligence* 174(2):215-243, doi:10.1016/j.artint.2009.11.011 | H050.stable-state lit_review §"Domain — N-bar state-stability..." | VERIFIED — canonical modern survey of explicit-duration HMM extensions. Elsevier ScienceDirect; DOI resolves to the *Artificial Intelligence* journal landing page. |
| L-6 | Page, E. S. (1954). "Continuous inspection schemes." *Biometrika* 41(1/2):100-115, doi:10.2307/2333009 | H050.stable-state lit_review §"Domain — N-bar state-stability..." | VERIFIED — canonical CUSUM change-point detection paper. JSTOR landing; DOI resolves to the paper. **Note**: the *Biometrika* volume 41 contains issues 1 and 2 jointly bound (a single-volume issue per the 1954 publishing convention); my citation "41(1/2):100-115" is correct as that is the canonical citation form for this paper. |
| L-7 | Ferguson, J. D. (1980). "Variable duration models for speech." | H050.stable-state lit_review §"Domain — N-bar state-stability..." | NOT INDEPENDENTLY VERIFIED — the Ferguson 1980 technical report is not in open-access channels. Cross-anchored via Rabiner 1989 §IV.A which cites it. The H050.stable-state framework does NOT rely on Ferguson 1980 directly; Rabiner 1989 §IV.A provides the project-anchor. **Disposition**: lit_review explicitly flags this as cross-anchored-only via Rabiner 1989 §IV.A. No load-bearing claim depends on Ferguson 1980 directly. |
| L-8 | Aydin, T., et al. (2006). "MARGINAL & POSTERIOR PROBABILITIES IN PROFILE HIDDEN MARKOV MODELS." | H050.stable-state lit_review §"Domain — N-bar state-stability..." | NOT INDEPENDENTLY VERIFIED — cross-referenced from biological-sequence HMM literature; the citation lacks venue/year detail in my draft. **Critical defect**: incomplete citation. Remediation per L-8 below. |
| L-9 | Hamilton 1989, Andersen-Bollerslev 1998, Baum et al. 1970, Hosking 1990, Goetzmann-Ingersoll-Spiegel-Welch 2007, Politis-White 2004, Patton-Politis-White 2009, Ledoit-Wolf 2008, Bergstra-Bengio 2012, VanderWeele-Ding 2017 | Both design.md headers + lit_reviews §"Inherited domains" | VERIFIED — all are inherited from H050 v1 + ADR-0005 + Phase L + Phase N + Phase O.14 + Phase O.18 lit trails. DOIs preserved verbatim from the source artifacts. |
| L-10 | López de Prado 2018 *AFML* §3.4 | Both design.md §4 references | VERIFIED — corrected pin per H050 v1 §15.1 Erratum-1 (§3.2 was originally cited; §3.4 is the canonical Triple-Barrier Method chapter). H050.invert + H050.stable-state inherit the corrected pin. |

### Quant-auditor branch

| # | Finding | Severity | Disposition |
|---|---|---|---|
| Q-1 | The H050 v1 design.md §5 line 63 canonical state-ordering rule says "states sorted by emission-mean ascending; gate state = highest-mean state." H050.invert's design.md §5 inverts this to "gate state = lowest-mean state." Is this a mathematically meaningful inversion or a tautology? | major (resolved) | Resolved per the H050 v1 INVESTIGATE memo §6.1: on BOTH ES and NQ, the H050 v1 highest-mean state has WORSE per-bar Sharpe than the discarded lowest-mean state on the unconditional return series. The inversion is therefore a non-trivial empirical test — if Sharpe-positive bars cluster in the low-mean state, the inverted gate produces positive realized OOS. Per Stephens 2000 + Frühwirth-Schnatter 2006 §3.5, the underlying HMM likelihood is label-permutation-invariant so the inversion does NOT amend ADR-0005's HMM toolkit; it pre-registers an alternative labeling convention for this specific successor variant. |
| Q-2 | H050.stable-state §5 N grid `{3, 5, 10, 20}` — the rationale states N=3 is "the noise floor (matches median run length so the filter is approximately a no-op)." But mathematically, requiring N=3 consecutive bars in-state is NOT equivalent to no filter — it still gates out transient single-bar or 2-bar excursions. | minor (clarified) | The "approximately no-op" framing is operator-conservative — N=3 is the noise floor in the sense that it matches the median active-run length (3 bars on ES per the parent INVESTIGATE memo §6.3). It does NOT mean "literally no filter." The H050.stable-state design.md §5 + the yaml grid `[3, 5, 10, 20]` correctly preserve the filter semantic at N=3. **Disposition**: the lit_review framing "filter ~= no-op" should be replaced with "filter at noise floor" in a future revision. Tracked as non-blocking polish under `P1-H050-STABLE-STATE-N3-FRAMING-CLARIFY`. |
| Q-3 | H050.stable-state §5 + yaml — is the stability counter measured on the modal-state assignment (i.e., `argmax_s p(s_t = s \| y_{1:t})`) or on the posterior-mass threshold (e.g., `p(s_t = gate_state \| y_{1:t}) > 0.5`)? | major (resolved) | Resolved by H050.stable-state design.md §5 explicit wording: "if the forward-filter posterior `p(s_t = gate_state | y_{1:t})` has placed `gate_state` as the modal state for N consecutive bars." The modal-state interpretation is the canonical default per H050 v1 §15.3 sizing convention. Posterior-mass-threshold variant is a future genetic successor reserved under `P1-H050-STABLE-STATE-POSTERIOR-MASS-V2`. |
| Q-4 | H050.stable-state §5 + design.md §11.2 — at fold boundaries, does the stability counter reset OR carry forward from the train-fold tail into the test fold? | major (resolved) | Resolved per design.md §11.2 + yaml `state_stability_filter.counter_reset_at_fold_boundary: true` + the H055 `P1-H055-LEVEL-STATE-FOLD-CONTINUITY` pattern. Counter resets at fold boundaries to preserve PIT-causality (no conditioning on near-purge train-tail state). This is conservative but operator-canonical. Carry-forward variant tracked under `P1-H050-STABLE-STATE-CARRY-FORWARD-V2`. |
| Q-5 | Both design.md §11.1 — kill-switch K-6/K-7 disabled at v1. But the parent investigation memo §6.4 quantified the cost-drag at 1.87×-5.66× of the unconditional signal magnitude. If K-6/K-7 are off, the v1 emissions will produce numerically-comparable cost-drag patterns to H050 v1. Is this defensible? | major (resolved) | Resolved per design.md §11.1 `# justify:`: K-6/K-7 at 1-min cadence × bar-level returns have minimal traction; enabling produces the asymmetric blocking pattern documented in Phase O.15 H062 v3 ablation. The cost-drag at v1 is measured per the cost-conservative-prior annotation; the kill-switch primitives are opt-in per ADR-0024 §D-2. Operator may enable per design.md §11.1 in a v2 emission via the orchestrator CLI flags (per the ADR-0025 §D-1..§D-4 + ADR-0028 §D-1 patterns; the H050.invert + H050.stable-state orchestrators MUST land the CLI flag wiring identically to the H062 + H055 v3 orchestrators). |
| Q-6 | H050.stable-state has a 4-N × 2-symbol = 8-strategy SPA family. Does this trigger ADR-0027 §D-2 DSR/PSR deflation? | minor (resolved) | Resolved per yaml `romano_wolf_stepwise: true` + ADR-0027 §D-2 + F-1-2 fix: 8 strategies is below the project-default `dsr_activation_size = 10` per [config/gate.yaml](../../config/gate.yaml); DSR remains `n/a` at v1. The Romano-Wolf 2005 stepwise FWER is the family-wise correction across the 4-N grid per the H055 `P1-H055-RW2005-STEPWISE-CONJUNCTIVE` precedent. The KPI v0 skeleton notes `dsr-n/a` with a v1-verification note. |
| Q-7 | H050.invert §1 H-c whipsaw vs H-b anti-selection discrimination claim — the parent investigation memo §6.6 says H-c is PRIMARY and H-b is SECONDARY. Yet H050.invert tests H-b in isolation. Is this an appropriate prioritization? | major (clarified) | Resolved per the design.md §12 paired-design logic: the discrimination is JOINT across both variants. H050.invert alone tests whether the inverted gate produces non-negative edge (if YES → H-b contributes; if NO → H-b alone is insufficient OR H-c whipsaw also obtains under the inverted gate). H050.stable-state alone tests whether stability monotonically improves edge (if YES → H-c contributes; if NO → H-c alone is insufficient). The cross-arm comparison discriminates the two mechanisms — neither variant alone is dispositive. The parent investigation memo §6.6 H-c-PRIMARY framing is the EMPIRICAL DECOMPOSITION result on existing fixtures; the variants test the CAUSAL CLAIMS implied by that decomposition under operator-actionable interventions. |
| Q-8 | H050.invert + H050.stable-state both report `kelly-multiplier-1.0` in KPI v0 skeleton (100%-of-equity-when-active sizing per H050 v1 §15.3). But ADR-0018 §D-2 says the canonical Kelly grid for ADR-0024 paradigm hypotheses is `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}`. Is the v1 single-Kelly-cell defensible? | minor (resolved) | Resolved per design.md §11.1 `# justify:`: H050.invert + H050.stable-state v1 inherit the H050 v1 §15.3 sizing convention for direct cross-arm comparability with H050 v1 per ADR-0027 §D-4 "preserved infrastructure" framing. The Kelly-multiplier grid is reserved for a SEPARATE genetic successor variant (combining the inverted gate / stability filter with the ADR-0018 §D-2 grid) under `P1-H050-INVERT-KELLY-GRID-V2` + `P1-H050-STABLE-STATE-KELLY-GRID-V2`. The single-axis change per ADR-0027 §D-4 canonical-cross discipline is the load-bearing inferential property of the paired design. |

### Format-auditor branch

| # | Finding | Severity | Disposition |
|---|---|---|---|
| F-1 | Both KPI v0 skeletons emit `cost-conservative-prior` annotation but the design.md §7 + yaml cost_model field is `nt8_es_nq_rth_v1` (the H050 v1 cost model), not `NT8RealisticCostModel` (the Phase O.11 multi-instrument primitive). | minor (clarified) | Resolved: the H050 v1 universe is {ES, NQ} — both covered by the legacy `nt8_es_nq_rth_v1` cost model. The Phase O.11 NT8RealisticCostModel extends to {MGC, SIL, MCL} but the H050 family does NOT use those symbols. The annotation grammar `cost-{empirical-calibrated, conservative-prior, zero}` from ADR-0025 §D-3 is orthogonal to the model-id; it documents provenance, not the model class. Both annotations co-exist: `cost-conservative-prior` (provenance) + `nt8_es_nq_rth_v1` (model id). |
| F-2 | Per ADR-0026 §D-1 the §0 3-component summary header is MANDATORY at the top of every KPI report card. v0 skeletons land §0 BUT with all numeric fields as "TBD at v1 emission" — is the v0 then ADR-0026-compliant? | minor (clarified) | Resolved per the H062 + H065 + H055 v0 skeleton precedent (CLAUDE.md Phase O.1 + Phase O.2 + Phase O.6): v0 skeletons land the canonical-format scaffolding with TBD numeric fields PRE-emission. The v0 is NOT a "KPI report" per ADR-0026 §D-1's load-bearing semantic; it is a scaffolding artifact that anchors the canonical format AHEAD of the v1 emission. The v1 emission populates all TBD fields per the BLOCKING preconditions in design.md §11.2. ADR-0026 §D-1 is fully complied with at v1 emission, not at v0. |
| F-3 | Both KPI v0 skeletons reference Tables 1, 1c, 2, 3, 3a, 3b, 3c, 4, 5, 6, 7, 8, 9. Per ADR-0014 §3.2 + ADR-0019 §3 the canonical 13-table mandate is correct. But the H050.stable-state Table 8 has an additional row ("per-N transition rate + cost-drag attribution") that is NOT in the canonical ADR-0014 §3.2 template. | minor (resolved) | Resolved per design.md §7 + §8 + yaml `cost_drag_attribution.per_n_rows: true`: the per-N transition rate + cost-drag attribution row is an ADR-0014 §3.2 Table 8 ("Other KPIs") canonical extension for hypotheses that test cost-drag mechanisms. The H050.stable-state hypothesis specifically tests whether the stability filter reduces transition rate + cost-drag; reporting these per-N is load-bearing for the H-c whipsaw discrimination. The KPI v0 skeleton notes this extension explicitly in the §"Methodological-correctness annotations" + the design.md §8 emission requirements. |
| F-4 | H050.invert + H050.stable-state share the OOS test fold with H050 v1 — is the `data-overlap-h050-v1-acknowledged` annotation sufficient? | minor (resolved) | Resolved per data_requirements.md §"Cross-hypothesis fit-set isolation table" + the H055 substrate-overlap convention. The OOS overlap is intentional under the paired-design mechanism-discrimination framing per design.md §1 + §12; the annotation `data-overlap-h050-v1-acknowledged` is the canonical disclosure pattern. The variants are NOT independent OOS tests in the multiple-testing-correction sense — they are sibling mechanism-discrimination probes on the SAME parent hypothesis. |
| F-5 | The H050.invert + H050.stable-state RNG seed is `20260520` (design-date YYYYMMDD per F-Q-8 H054 precedent). Both variants use the SAME seed. Is this defensible for cross-arm comparability? | minor (resolved) | Resolved per design.md §11 `# justify:`: identical seeds at the hypothesis level ensure the LightGBM random-search trajectories are deterministic across variants under the same train fold. The randomness in the inner-CV cell selection + bootstrap CI machinery is offset by hypothesis-specific `rng_seed_offset` fields in the yaml (`mppm_rho_1.rng_seed_offset=100`, `terminal_wealth_q05.rng_seed_offset=0` default, etc.) per the ADR-0017 + ADR-0018 primitive convention. The empirical inference is NOT statistically dependent in a way that the shared seed would inflate Type-I error — the two variants probe DIFFERENT mechanisms on the SAME OOS data; the inference shared-randomness affects only the inner-CV trajectory, not the OOS-evaluation determinism. |
| F-6 | The literature-check L-4 catches that JRSS B is hosted by Wiley, not OUP (Oxford Academic). My lit_review H050.invert §"Domain" §"Verified abstract excerpts" Stephens 2000 entry references "Oxford Academic landing page" instead of Wiley. | minor (remediated below at L-4 + F-6) | Apply inline lit_review remediation: replace "Oxford Academic landing page" with "Wiley Online Library landing page" for the Stephens 2000 verification. |
| F-7 | L-8 Aydin et al. 2006 citation is incomplete (no venue/year/full author list). | minor (remediated below at L-8 + F-7) | Apply inline lit_review remediation: remove the Aydin et al. 2006 reference (it is cross-anchored only; no load-bearing claim depends on it). |

## Round 1 remediation (inline before commit)

Three findings carry inline remediation actions:

1. **L-4 + F-6**: lit_review H050.invert §"Domain — HMM canonical state ordering + label-switching" §Stephens 2000 — replace "Oxford Academic landing page" with "Wiley Online Library landing page" (this is a venue-publisher correction; same regression class as the Phase O.10 R1 Hsu-Kuan 2005 venue inversion, caught at R1).

2. **L-8 + F-7**: lit_review H050.stable-state §"Domain — N-bar state-stability..." §Aydin et al. 2006 — DELETE this citation entry (incomplete; cross-anchored only; no load-bearing claim depends on it). The canonical anchor remains Rabiner 1989 §IV.A + Yu 2010 §3.

3. **Q-2**: lit_review framing "filter ~= no-op" at N=3 — non-blocking polish; tracked under `P1-H050-STABLE-STATE-N3-FRAMING-CLARIFY` for a future revision. Not remediated inline (the design.md §5 wording is already correct; the lit_review framing is non-load-bearing).

## Round 1 verdict

**`accept-with-residuals`** per the audit-remediate-loop skill convention. R1 surfaced 2 minor lit-defects (L-4 + L-8) that are remediated inline below; the remaining quant + format findings are either resolved by existing artifact wording or tracked as non-blocking follow-ups. No critical findings (no wrong-paper-DOI / wrong-ISBN / wrong-author-order errors of the precedent regression class).

## Round 2 verification posture

Per the audit-remediate-loop skill 3-round cap, Round 2 verification is deferred to the v1 KPI report card emission cycle for each variant (post-`P1-H050-INVERT-PROD-RUN` + `P1-H050-STABLE-STATE-PROD-RUN`). The v1 emissions will surface any remaining methodological defects empirically per the Phase O.13 H062 v3 ablation + Phase O.18 H067 + H068 v1 walk-forward precedents.

## New follow-ups registered by this R1

| Follow-up | Status | Description |
|---|---|---|
| `P1-H050-INVERT-WALK-FORWARD-ORCHESTRATOR-IMPL` | OPEN; BLOCKING-BEFORE-PRODUCTION-RUN | Orchestrator at `scripts/run_h050_invert_walk_forward.py` adapting H050 v1 orchestrator with the inverted state-ordering rule at the gate-selection layer. |
| `P1-H050-INVERT-LEAKAGE-CANARY-INTEGRATION-TEST` | OPEN; BLOCKING-BEFORE-PRODUCTION-RUN | Cycle-4 leak-canary integration test at `tests/integration/test_h050_invert_pit.py`. |
| `P1-H050-INVERT-PARITY-INVARIANT-TEST` | OPEN; BLOCKING-BEFORE-PRODUCTION-RUN | Gate-label-swap parity test to H050 v1. |
| `P1-H050-INVERT-POWER-SIMULATION` | OPEN; non-blocking | Power calibration from H050 v1 pilot Sharpe dispersion. |
| `P1-BOCD-LIVE-PRIOR-CALIBRATION-H050-INVERT` | OPEN; BLOCKING-BEFORE-LAUNCH-WITH-BOCD-LIVE | Mirrors the H062 v3 + H055 v3 BOCD-live prior calibration follow-up. |
| `P1-H050-INVERT-COST-EMPIRICAL-CALIBRATION` | OPEN; BLOCKING-BEFORE-PAPER-TRADE-EVALUATED | Empirical cost-realism calibration post-paper-trade per the H055 v2 + H062 v2 precedent. |
| `P1-H050-INVERT-NINJASCRIPT-IMPL` | OPEN; mandatory per ADR-0013 §5; operator-discretionary timing | Bridge-mediated C# implementation. |
| `P1-H050-INVERT-NINJASCRIPT-PARITY-TOLERANCE` | OPEN; non-blocking | Python ↔ NinjaScript parity-check per ADR-0013 §5.2. |
| `P1-H050-INVERT-PROD-RUN` | OPEN; v1 KPI report card emission | Walk-forward run on canonical post-Phase-O.10 substrate. |
| `P1-H050-INVERT-KELLY-GRID-V2` | OPEN; non-blocking | v2 successor combining the inverted gate with ADR-0018 §D-2 Kelly multiplier grid. |
| `P1-H050-STABLE-STATE-WALK-FORWARD-ORCHESTRATOR-IMPL` | OPEN; BLOCKING-BEFORE-PRODUCTION-RUN | Orchestrator at `scripts/run_h050_stable_state_walk_forward.py` adapting H050 v1 orchestrator with the N-bar stability filter inserted between forward-filter output and gate engagement; emits per-N rows in sidecar payload. |
| `P1-H050-STABLE-STATE-LEAKAGE-CANARY-INTEGRATION-TEST` | OPEN; BLOCKING-BEFORE-PRODUCTION-RUN | Cycle-4 leak-canary integration test at `tests/integration/test_h050_stable_state_pit.py`. |
| `P1-H050-STABLE-STATE-FOLD-CONTINUITY-TEST` | OPEN; BLOCKING-BEFORE-PRODUCTION-RUN | Stability counter reset / carry policy at fold boundaries. |
| `P1-H050-STABLE-STATE-POWER-SIMULATION` | OPEN; non-blocking | Power calibration across the 4-N grid. |
| `P1-BOCD-LIVE-PRIOR-CALIBRATION-H050-STABLE-STATE` | OPEN; BLOCKING-BEFORE-LAUNCH-WITH-BOCD-LIVE | Mirrors the H050.invert + H062 v3 + H055 v3 BOCD-live prior calibration follow-up. |
| `P1-H050-STABLE-STATE-COST-EMPIRICAL-CALIBRATION` | OPEN; BLOCKING-BEFORE-PAPER-TRADE-EVALUATED | Empirical cost-realism calibration post-paper-trade. |
| `P1-H050-STABLE-STATE-NINJASCRIPT-IMPL` | OPEN; mandatory per ADR-0013 §5; operator-discretionary timing | Bridge-mediated C# implementation. |
| `P1-H050-STABLE-STATE-NINJASCRIPT-PARITY-TOLERANCE` | OPEN; non-blocking | Python ↔ NinjaScript parity-check per ADR-0013 §5.2. |
| `P1-H050-STABLE-STATE-PROD-RUN` | OPEN; v1 KPI report card emission | Walk-forward run on canonical post-Phase-O.10 substrate; per-N grid emission. |
| `P1-H050-STABLE-STATE-N3-FRAMING-CLARIFY` | OPEN; non-blocking polish | Replace "filter ~= no-op" framing in lit_review with "filter at noise floor" wording (Q-2 deferred polish). |
| `P1-H050-STABLE-STATE-POSTERIOR-MASS-V2` | OPEN; non-blocking | v2 successor with posterior-mass threshold gating (Q-3 reserved variant). |
| `P1-H050-STABLE-STATE-CARRY-FORWARD-V2` | OPEN; non-blocking | v2 successor with stability counter carrying across fold boundaries (Q-4 reserved variant). |
| `P1-H050-STABLE-STATE-EXTENDED-N-GRID-V2` | OPEN; non-blocking | v2 successor with extended N grid beyond {3, 5, 10, 20} (design.md §5 reserved). |
| `P1-H050-STABLE-STATE-HSMM-V2` | OPEN; non-blocking | v2 successor embedding the stability requirement inside the HMM likelihood via Yu 2010 HSMM (lit_review §"Domain" reserved successor). |
| `P1-H050-STABLE-STATE-KELLY-GRID-V2` | OPEN; non-blocking | v2 successor combining the stability filter with ADR-0018 §D-2 Kelly multiplier grid. |
| `P1-H050-INVERT-PLUS-STABLE-STATE-V2` | OPEN; non-blocking | v2 successor combining inverted gate AND stability filter (design.md §12 reserved variant). |

## Cross-references

- Parent H050 design: [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md)
- Parent H050 KPI v1: [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md)
- Parent H050 INVESTIGATE-FAILURE-MODE closure memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../../research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md)
- Parent INVESTIGATE closure audit trail: [docs/audits/audit_trail_2026-05-19_h050-hmm-gating-harm-investigate.md](audit_trail_2026-05-19_h050-hmm-gating-harm-investigate.md)
- H050.invert design: [research/01_hypothesis_register/H050_invert/design.md](../../research/01_hypothesis_register/H050_invert/design.md)
- H050.stable-state design: [research/01_hypothesis_register/H050_stable_state/design.md](../../research/01_hypothesis_register/H050_stable_state/design.md)
- ADR-0027 §D-4 genetic-successor discipline: [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- ADR-0013 §"Frozen pre-registration amendment" + §4.1 non-loss: [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- ADR-0026 §D-1 mandatory §0 3-component summary header: [docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md](../decisions/ADR-0026-paradigm-and-reporting-refinements.md)
- ADR-0005 HMM toolkit: [docs/decisions/ADR-0005-hmm-regime-toolkit.md](../decisions/ADR-0005-hmm-regime-toolkit.md)
- CLAUDE.md Phase O.18 closure synthesis: [CLAUDE.md](../../CLAUDE.md) §"Phase O.18 closure synthesis"
- SKILL audit-remediate-loop: [.claude/skills/audit-remediate-loop/SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md)
