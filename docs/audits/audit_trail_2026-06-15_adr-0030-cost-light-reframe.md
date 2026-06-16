# Audit-remediate-loop trail — ADR-0030 cost-light arm-generation refined center of gravity

**Date**: 2026-06-15
**Artifact**: [docs/decisions/ADR-0030-cost-light-arm-generation-refined-center-of-gravity.md](../decisions/ADR-0030-cost-light-arm-generation-refined-center-of-gravity.md)
**Closes**: `P1-ADR-0029-COST-LIGHT-REFRAME`.
**Discipline**: per SKILL.md audit-remediate-loop 3-round cap; Round-1 proper-isolated parallel literature-check + quant-auditor; verdict **accept-with-remediation**.

## Round 1 — parallel branches

- **literature-check** (agentId `a213c7802454e0732`) — verdict **`accept`, 0 findings**. All 11 citations (9 external + 2 internal) verified: DOI resolution + bibliographic metadata + finding-direction. The three explicitly-flagged hazards each CONFIRMED CORRECT: (1) Novy-Marx-Velikov 2016 DOI is `10.1093/rfs/hhv063` and NOT an `hhm…` prefix (DGU 2009 is the genuine `hhm075`); (2) Frazzini-Israel-Moskowitz is a working paper with no peer-reviewed journal DOI (do not invent one); (3) Marshall-Cahan-Cahan is the *J. Banking & Finance* commodity-futures paper, not the same-authors' *J. Empirical Finance* 15(2) intraday-equity paper. The Korajczyk-Sadka survival-qualifier representation (NOT monolithic cost-nihilism) and the FIM-vs-Patton-Weller cost-model-dependence nuance were both confirmed faithful to the sources. No wrong-paper-DOI of the Breiman-1996 class; no finding-direction inversion of the Hsu-Kuan-2005 class.
- **quant-auditor** (agentId `a51ff6492b90cd53d`) — verdict `proceed-with-remediation`; 0 critical + 4 major + 6 minor. Cost-erosion arithmetic (ES PF 1.07→0.43, ROI +21.9%→−50.7%; MGC; SIL) confirmed cell-for-cell against the buildout milestone-5 source of record.

## Quant findings + remediation

| # | Sev | Finding | Remediation |
|---|---|---|---|
| F-1-1 | major | C-3 "garbage in, garbage out" over-routes through cost-fragility; the MPV2 NULL was on PRE-COST streams, so it shows pre-cost mean-edge marginality — a deficiency distinct from cost-fragility. | **APPLIED.** C-3 rewritten to separate the **two logically distinct deficiencies**: (a) pre-cost mean-edge marginality (MPV2 NULL on zero-cost streams; even 1/N doesn't beat B&H pre-cost) and (b) cost-fragility (best arm cost-erased). The net-of-cost screen is the more stringent and subsumes (a) only where gross edge exists. |
| F-1-2 | major | C-3 "the mechanism is fine, only the arms are bad" under-acknowledges that the SWITCHING mechanism was shown inferior to 1/N on its own terms (estimation noise). | **APPLIED.** C-3 now states the NULL has a **mechanism component** (switching dominated by 1/N, DGU 2009, partly arm-independent → why §D-5 promotes pooling not switching) AND an arm-quality component (library lacks members worth pooling over). Allocation-by-POOLING over a GOOD library remains untested. |
| F-1-4 | major | The D-1 gate "≥2 de-correlated arms EACH clearing B&H net-of-cost" forecloses the [Peters-Adamou 2022](https://doi.org/10.1098/rsta.2020.0425) pooling lift (a pool of marginal-but-de-correlated arms can clear B&H that individuals do not) — internally inconsistent with the pooling thesis it promotes. | **APPLIED.** D-1 gate reworded to test the **net-of-cost POOLED equity** clearing B&H with a CI; each-arm-individually-positive is "sufficient but not necessary." This is the object the ADR-0020 engine actually trades and avoids foreclosing the engine's primary use case. |
| F-1-9 | minor (load-bearing) | The empirically-winning pooler was NAIVE 1/N (0.320/0.261); the optimised joint-Kelly (what ADR-0020's inverse-variance engine computes) was itself dominated (0.150/0.045) and didn't beat B&H. D-5 promoted "the ADR-0020 portfolio engine" without noting 1/N won. | **APPLIED.** D-5 pooling row now states the ADR-0020 engine is the right ARCHITECTURE but its DEFAULT weighting on small-N noisy arms should be naive 1/N (the empirically-winning pooler per DGU 2009), NOT the inverse-variance/MVO optimum. Prevents a future session deploying the optimised weighting when 1/N was superior. |
| F-1-8 | minor | D-5 switching-bandit shown both "preserved in full" and "dominated" without cross-noting. | **APPLIED.** The §D-2/§D-3/§D-4 preserved-row now adds "the switching-bandit is DEMOTED as the allocator mechanism per the next row (pooling dominates)" — bandit primitive non-loss-preserved (ADR-0013 §4.1) but no longer the preferred allocator. |
| F-1-3 | minor | C-2 "every C9 cell flips catastrophically negative" + 3-row table omits the buildout's 4th (NQ) cell. | **APPLIED.** Reworded to "every C9 cell with a gross-positive zero-cost edge flips catastrophically negative (NQ was already gross-negative pre-cost and is omitted)". |
| F-1-5 | minor | "binding screen" title-phrasing is in mild tension with ADR-0013's deliberately-retired "binding gate" language (body text disambiguates correctly). | **APPLIED.** Title + D-2 header → "binding **promotion** screen"; the body already says "an operator-review screen, not a mechanical gate" (consistent with ADR-0013 §1+§2). |
| F-1-6 | minor | The cited audit trail did not exist on disk while status was `accepted`. | **APPLIED** — this file. |
| F-1-7 | minor | NMV-2016 "< 50%/month" is an equity-anomaly monthly-rebalance figure imported onto an intraday-scalp universe without a frequency bridge. | **APPLIED.** D-3(i) now states "< 50%/month" is the equity-anomaly reference and the intraday operative prior is **edge-per-trade dominating round-trip cost** (round-trip cost ÷ per-trade R-multiple) — exactly the PF-1.07→0.43 mechanism. |
| F-1-10 | minor | Cost figures are smoke-grade with partly-placeholder fees per the buildout's own caveat, not carried forward into the ADR honest-scope. | **APPLIED.** Honest-scope gains the smoke-grade/placeholder-fee caveat (qualitative PF 1.07→0.43 robust to fee precision; exact net-of-cost ROIs await empirical slip calibration). The MPV2-pending bullet updated to reflect `P1-MPV2-REPROLOG-WIRE` now CLOSED + the 2-arm switching +0.028 correction. |

## Net assessment

The ADR's core strategic claim — arm generation under a net-of-cost screen is the binding upstream constraint; the allocator apparatus is preserved-but-gated; H068 cost-light is the active pursuit — is logically defensible and faithful to the empirical record. The major findings were logic/prescription refinements (the pre-cost-vs-cost-fragility distinction, the pooling-lift-aware gate, the 1/N-vs-optimised-engine prescription) that materially improve the ADR's durability for future independent sessions, all applied. The literature is clean (0 citation findings — the project's tracked finding-inversion regression class did not recur).

## Round-2 posture

Round-2 verification deferred to the first cost-light arm-generation cycle (H068 v2 net-of-cost run) where the D-1 pooled-gate + D-2 net-of-cost screen + D-3 turnover lever are first exercised empirically. **Verdict: accept-with-remediation.**

## Residual / cascade follow-ups

`P1-ADR-0030-GLOSSARY-CASCADE`, `P1-ADR-0030-TEMPLATE-CASCADE`, `P1-ADR-0030-DESIGN-MD-TURNOVER-SECTION`, `P1-NET-OF-COST-SURVIVAL-ANNOTATION-RETROACTIVE` (per the ADR §Consequences).
