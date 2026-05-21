---
date: 2026-05-20
title: ADR-0017 + ADR-0018 design.md cascade — H050/H051/H052a/H052b/H053/H054 §8+§10+§11.1 harmonization
phase: O.19
type: audit_trail
status: R1 accept-with-residuals
---

# Audit trail — ADR-0017 + ADR-0018 design.md cascade (Phase O.19)

## Scope

Per the BLOCKING-BEFORE-NEXT-STAGE-3-RUN follow-ups `P1-ADR-0017-DESIGN-MD-CASCADE` + `P1-ADR-0018-DESIGN-MD-CASCADE`, this cascade amends the §8 + §10 + §11.1 promotion-decision-rule layer of the six pre-Phase-N frozen pre-registrations to inherit the canonical ADR-0017 + ADR-0018 paradigm. All §1-§7 content is preserved verbatim per [ADR-0013 §"Frozen pre-registration amendment"](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1-§7 immutability.

Six files amended:
- [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md)
- [research/01_hypothesis_register/H051/design.md](../../research/01_hypothesis_register/H051/design.md)
- [research/01_hypothesis_register/H052a/design.md](../../research/01_hypothesis_register/H052a/design.md)
- [research/01_hypothesis_register/H052b/design.md](../../research/01_hypothesis_register/H052b/design.md)
- [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md)
- [research/01_hypothesis_register/H054/design.md](../../research/01_hypothesis_register/H054/design.md)

## Amendment pattern

Each design.md receives:
1. **§8 banner amendment**: short banner above existing ADR-0013 amendment notes pointing to Appendix A.
2. **§10 banner amendment**: same pattern.
3. **§11.1 K-1..K-8 inheritance**: if the file lacks §11.1, an `### 11.1 Kill-switch parameters` subsection is appended within §11 inheriting the K-1..K-8 list. Existing §11.1 entries (H053, H054) gain a cross-link.
4. **Appendix A (new section)**: full ADR-0017 + ADR-0018 cascade amendment text — three subsections (primary metric vector, MPPM(ρ=1) inner-CV fitness, K-1..K-8 inheritance) + revision-log entry.

§1-§7 are PRESERVED VERBATIM. The §1 T_H hypothesis-of-record test statistic is preserved as a SECONDARY KPI per ADR-0017 §1.2.

## R1 audit-remediate-loop (inline self-audit per `P1-AGENT-TOOL-NOT-SURFACED` documented workaround)

Three parallel specialist branches inline:

### Format-auditor branch (load-bearing)

**Finding F-F-1**: cross-link integrity — every ADR cross-link in the cascade text must resolve under the current docs/decisions/ layout. Verified by `Glob docs/decisions/ADR-001*` and `Glob docs/decisions/ADR-002*`:
- ADR-0013 — `docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md` ✓
- ADR-0014 — `docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md` ✓
- ADR-0017 — `docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md` ✓
- ADR-0018 — `docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md` ✓
- ADR-0019 — `docs/decisions/ADR-0019-barbell-payoff-shape-screening.md` ✓
- ADR-0022 — `docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md` ✓
- ADR-0024 — `docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md` ✓
- ADR-0028 — `docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md` ✓

Remediation: cascade-text cross-links cite ADR-0017 + ADR-0018 + ADR-0013 anchors verbatim from this verified set.

**Finding F-F-2**: §17 revision-log harmonization — H050/H051/H052a/H052b/H053 lack a §17 (only H054 has one). Cascade pattern places the revision-log entry inside Appendix A under a clearly labeled "Revision-log" subsection rather than introducing a new §17 (which would risk visual collision with H054's existing §17 across the project). Each file's Appendix A becomes the cross-link anchor.

**Finding F-F-3**: H054 already inherits the ADR-0013 KPI-only philosophy in §8 + §10 + §11.1 verbatim. The Appendix A overlay on H054 is a documentation-completeness addition, not a substantive amendment — H054's §11.1 already enumerates kill-switch parameters that fit the project pre-existing convention (not the K-1..K-8 ADR-0017 §5 list). The Appendix A K-1..K-8 inheritance text is therefore added as a cross-reference cascade, with the existing §11.1 content preserved verbatim and a cross-link to Appendix A added.

### Literature-check branch

Verification scope: NO new primary citations introduced by the cascade. All amendment text cites existing ADRs (which themselves have audit-remediate-loop-verified citation chains per Phase K + Phase N audit trails). The precedent regression class (Phase O.10 Hsu-Kuan 2005 finding-direction inversion; Phase O.11 AFML §13.2 wrong-section pin; Phase N Breiman 1996 *Annals* vs *Machine Learning* DOI swap) is structurally precluded since no new primary citations are introduced.

**No findings**. Verdict: accept.

### Quant-auditor branch

**Finding Q-1**: §1 T_H statistic immutability — every design.md §1 contains a Sharpe-differential T_H statistic. ADR-0017 §1.2 (and ADR-0018 §D-1) demote this from PRIMARY to SECONDARY KPI at the §8+§10 promotion-decision-rule layer, but preserve it verbatim in §1 with `computed verbatim and reported as numerical KPI in every KPI report card`. Verified: the Appendix A text says explicitly "the immutable §1 T_H statement is preserved as a secondary KPI per ADR-0017 §1.2" rather than the load-bearing primary inferential metric. Remediation: this is the canonical pattern; no change.

**Finding Q-2**: K-5 correlated-instrument inventory cap applicability per design.md universe — H050 single-symbol-per-arm (separate ES + NQ arms; no cross-instrument pair within an arm); H051 ES+NQ pair trade (cross-instrument pair IS the strategy — K-5 applicable IF the strategy were to add MES alongside ES, but per universe stipulation it is ES OR MES, not both); H052a + H052b siblings on different symbols (per design.md §12 separate hypothesis IDs); H053 ES + NQ pooled with instrument-dummy stratification (cross-instrument K-5 not directly applicable — ES+NQ correlation is high but they are not a CL+MCL-style correlated-pair); H054 ES-only at v1 (per design.md §9.3 NQ excluded). Per-hypothesis K-5 applicability is documented in Appendix A per file.

**Finding Q-3**: K-8 adverse-direction entry filter applicability — H050 trend-gate is the HMM filter itself (not a T_H trend gate per ADR-0017 §5 K-8 spec). H051 entry condition is Kalman-residual z-score with Johansen pre-screen (no T_H trend gate). H052a + H052b HMM-gated ORB with PT/SL barriers. H053 multi-timeframe regression. H054 anti-gate inversion. For most of these the K-8 spec ("forbid entries where T_H trend gate sign disagrees with entry direction") is **structurally already satisfied** by the gating mechanic (HMM gate, Johansen screen, regime indicator) — adverse-direction protection is intrinsic to the design. Appendix A documents K-8 as `applicable-by-existing-gate` for each hypothesis where the existing entry filter already encodes adverse-direction protection.

**No critical findings**. Verdict: accept-with-residuals.

## Round 1 verdict

`accept-with-residuals` per the audit-remediate-loop skill convention. Residuals are documentation-completeness items (per-file applicability tables for K-1..K-8) that are explicitly addressed in each file's Appendix A. No code primitives change; no new sidecar emission required; no new primary citations introduced.

## Round 2 verification posture

Per SKILL.md 3-round cap, Round 2 verification is deferred to the first downstream stage-3 run that consumes the amended design.md §8+§10+§11.1 cascade (per `P1-ADR-0017-DESIGN-MD-CASCADE` + `P1-ADR-0018-DESIGN-MD-CASCADE` BLOCKING-BEFORE-NEXT-STAGE-3-RUN). The next stage-3 run will empirically validate the cascade by emitting KPI cards under the canonical paradigm.

## Closes

- `P1-ADR-0017-DESIGN-MD-CASCADE` (BLOCKING-BEFORE-NEXT-STAGE-3-RUN per Phase K Phase O.14 ledger).
- `P1-ADR-0018-DESIGN-MD-CASCADE` (BLOCKING-BEFORE-NEXT-STAGE-3-RUN per Phase N ledger).

## New non-blocking follow-ups registered

None. This cascade is a §8+§10+§11.1 documentation amendment per ADR-0013 §"Frozen pre-registration amendment" — the substantive ADR-0017 + ADR-0018 primary-metric and inner-CV-fitness primitives are already implemented (Phase L + Phase O.13 onward) and bound by every post-Phase-N hypothesis pre-registration (H055, H060, H062, H065, H067, H068).

## Cross-references

- [ADR-0017 §1.2 + §3 + §5](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md) — primary metric vector + Sharpe demotion + K-1..K-8.
- [ADR-0018 §D-1 + §D-2 + §D-3](../decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — MPPM(ρ=1) replaces Sharpe + Kelly grid + BOCD decay detector.
- [ADR-0013 §"Frozen pre-registration amendment"](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — §1-§7 immutability discipline.
- CLAUDE.md Phase O.19 ledger entry (this commit).
