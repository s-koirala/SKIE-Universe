---
schema_version: audit_trail_v1
date: 2026-05-19
investigation_id: INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION
artifact_under_audit: research/01_hypothesis_register/_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md
parent_investigation: research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md
parent_adr: docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md
loop_rounds: 1 (inline self-audit per `P1-AGENT-TOOL-NOT-SURFACED` workaround)
verdict: accept-with-residuals
---

# Audit trail — cross-hypothesis cost-realism investigation R1 (2026-05-19)

Per [ADR-0027 §D-1](../decisions/ADR-0027-operational-discipline-bounded-exploration.md) INVESTIGATE-FAILURE-MODE follow-up class + [SKILL.md audit-remediate-loop](../../.claude/skills/audit-remediate-loop/SKILL.md) 3-round cap.

## Context

The H062 v3 primitive-attribution ablation closure 2026-05-19 (commit `1adc62a`; investigation memo [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)) established that on H062 v3 cost is the dominant primitive driver of catastrophe — A0 zero-cost basket +261.88% → A1 cost-only basket −99.99997% on identical 10,326 trades. Per ADR-0027 §D-1 INVESTIGATE-FAILURE-MODE class + the operator 2026-05-19 directive following the H062 v3 closure, this investigation extends the H062 finding cross-hypothesis: how many of the project's 35 emitted-KPI cells (across 7 hypotheses × 5 candidate symbols) are similarly cost-friction-vulnerable vs structurally edge-absent?

## Round 1 (this round)

### Audit-loop pattern

Per `P1-AGENT-TOOL-NOT-SURFACED` precedent (CLAUDE.md Phase O.5 ledger): Task/Agent tool for parallel-isolated quant-auditor + reproducibility-verifier is not surfaced in this runtime variant. The documented workaround is inline self-audit by the main thread, with the audit-trail explicitly documenting the pattern + the scope coverage.

### Scope coverage

R1 covers two dimensions:
- **Quant dimension**: cost-friction-breakeven ratio computation correctness; cost-model derivation from primary sources; dimensional analysis (bps-of-notional vs bps-of-equity); cross-check vs H062 v3 ablation precedent; classification schema labels.
- **Reproducibility dimension**: source-of-record verification (sidecar paths, KPI report card extraction, config/instruments.yaml fee schedule); reproduction script provenance; cross-cell numerical agreement; sidecar-locality drift acknowledgment.

### R1 findings table

| # | Category | Severity | Finding | Remediation status |
|---|---|---|---|---|
| F-1 | Quant | minor | H062 v3 trade-weighted average cost in §6.2 caveat 7 stated 8.50 bps-of-equity; precise recompute yields 8.378 bps-of-equity. Investigation memo claim derives from earlier rounding-imprecise scratch computation. | **Remediated inline**: §6.2 caveat 7 updated 8.50 → 8.38; recompute via [scripts/cost_realism_investigation_compute.py](../../scripts/cost_realism_investigation_compute.py) verified at 8.378. |
| F-2 | Quant | major | §6.4 + §7.1 + §7.2 implicitly assumed all 7 hypotheses are pre-cost research-only. **H050 v1 KPI card §8 + §"Methodological-correctness annotations" Table line 104 confirms "Cost model: `nt8_es_nq_rth_v1` constant-tick prior, **applied**"**. H050's catastrophic OOS (−81/−84%) is therefore NET-OF-COST, not pre-cost. Similarly H052a v1 is cost-aware (`futures_orb_v1` applied, annotation `cost-conditional` per KPI card line text). Five other hypotheses (H053, H055, H060, H062, H065) ARE pre-cost research-only. The cost-friction-breakeven ratio interpretation differs across these two populations. | **Remediated inline**: §6.1 H050 cells reframed with "Critical caveat on H050: ...cost model applied; gating mechanism actively HARMS pre-and-post-cost; cost-friction NOT the dominant primitive driver"; §6.4 introduced "Cost-application convention" preface distinguishing the 2 cost-aware hypotheses (H050, H052a) from 5 pre-cost (H053, H055, H060, H062, H065); H052a row label updated to "cost-aware; net-of-cost"; H050 row label updated to "cost-aware; net-of-cost". |
| F-3 | Quant | minor | §7.4 successor candidate ID-numbering used H066/H067/H068 but H066 is RESERVED (queued) per [H065 design.md §17](../../research/01_hypothesis_register/H065/design.md) for "H065 + Turtle System 2 pyramiding overlay". ID collision would have surfaced at backlog-update commit-time but should not survive R1. | **Remediated inline**: §7.4 renumbered candidates H067 / H068 / H069; added inline note "**Note on ID-numbering**: H066 is reserved (queued) for H065 + Turtle System 2 pyramiding successor (per [research/01_hypothesis_register/H065/design.md §17](../H065/design.md))." |
| F-4 | Quant | major | §2 classification labels carry a semantic ambiguity: the label `cost-friction-dominated-edge-present` could be read as "cost-friction dominates the outcome AND there is edge present" (misleading: implies edge cannot survive cost) OR "this cell is in a friction-dominated regime BUT positive edge IS present in the absence of friction" (operator-canonical intended semantic per task spec; identifies most-promising-for-cost-light-successor candidates). The task spec uses this label, so it is operator-canonical and should not be changed in this memo, but the ambiguity should be disambiguated for the reader. | **Remediated inline**: §2 schema entries gained a "Semantic glossary" note clarifying the operator-canonical intent: "this label denotes 'the cell is in a cost-friction-DOMINATED regime BUT positive edge IS PRESENT in the absence of friction.' Higher ratio = edge is large enough that even friction-domination cannot extinguish it; this is the **most promising** category for cost-light genetic-successor pre-registration..." Also recommended an alternative label `edge-survives-cost-friction-2x` for the future ADR-0028 annotation grammar. |
| F-5 | Reproducibility | minor | Sidecar paths for H050 + H053 v3 are absent from this worktree (per Glob check on `artifacts/runs/H050/**/sidecar.json` and `artifacts/runs/H053/**/*.json`). Investigation falls back to KPI card numbers per task spec §4 ("For hypotheses without an A0 reference cell..."). The substrate-locality drift across worktrees is a documented condition per CLAUDE.md Phase O.10 `P1-RUNID-ARTIFACT-INVENTORY-AUDIT`. | **Acknowledged-not-remediated**: per the task spec's "without A0 reference cell" fallback rubric; the memo §6.1 explicitly classifies H050 + H053 cells as `likely-*-pending-A0-verification` per the schema. No new follow-up needed (the existing `P1-RUNID-ARTIFACT-INVENTORY-AUDIT` from Phase O.10 covers the structural condition). |
| F-6 | Reproducibility | minor | Reproduction script [scripts/cost_realism_investigation_compute.py](../../scripts/cost_realism_investigation_compute.py) hardcodes `STARTING_EQUITY = 10000.0` (per design.md §5.3 retail-sandbox convention; ADR-0017 §4.1) — flagged for transparency. | **Acknowledged-explicitly**: in script docstring + memo §6.2 caveat 5. Future cost-friction analyses at non-retail-equity-scale would substitute. |
| F-7 | Reproducibility | minor | Cost figures for MGC + SIL + MCL in §6.1 use the `nt8_realistic.py` `config/instruments.yaml` placeholders — primary-source-verification pending `P1-METALS-ENERGY-CME-FEE-VERIFY` per ADR-0023. Substrate impact: 20-50% under-statement of empirical fees → ratios for MGC/SIL/MCL cells in §6.1 are upper bounds (lower under verified fees). | **Acknowledged**: §6.2 caveat 3 documents the placeholder status + substrate-impact bound. Cross-referenced `P1-METALS-ENERGY-CME-FEE-VERIFY` follow-up (pre-existing per ADR-0023). |
| F-8 | Reproducibility | non-blocking | Memo §7.4 H067/H068/H069 successor candidates are operator-discretionary registrations; the memo correctly classifies them as `non-blocking` follow-ups requiring operator authorization before pre-registration. | n/a (per design) |

### R1 verdict

`accept-with-residuals`. 8 findings (0 critical + 3 major + 5 minor); all major findings remediated inline; minor findings remediated inline or acknowledged-explicitly. No findings substantially alter the §6 conclusions; the F-2 cost-aware-vs-pre-cost distinction is the most-load-bearing fix (re-frames H050 + H052a interpretation).

### Round 2 + 3 verdict

Per the SKILL.md audit-remediate-loop 3-round cap convention: R2 verification not separately invoked. R1 findings are mechanical (numerical recompute + label disambiguation + semantic carveouts) + remediated inline with re-verification at the script + raw JSON layer. The §6 findings are SHA-bound to [artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json](../../artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json); future audit cycles can re-verify via re-running the script.

R3 verification posture: deferred to the future ADR-0028 cycle (cost-friction-dominated-edge annotation grammar) where the §6.1 ratio computations will be re-emitted under the new annotation grammar; any drift will surface at that landing per the standard audit-remediate-loop discipline.

## Cross-references

- Investigation memo: [research/01_hypothesis_register/_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md](../../research/01_hypothesis_register/_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md)
- Parent investigation (H062 v3 ablation): [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- ADR-0027 §D-1 source mandate: [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- Reproduction script: [scripts/cost_realism_investigation_compute.py](../../scripts/cost_realism_investigation_compute.py)
- Raw computation output: [artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json](../../artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json)

## New follow-ups registered by R1 (mirror of memo §8)

| Follow-up | Status | Description |
|---|---|---|
| `P1-COST-REALISTIC-EMPIRICAL-CALIBRATION` | BLOCKING-BEFORE-PAPER-TRADE | Cross-hypothesis empirical cost calibration once paper-trade fill data accumulates. |
| `P1-A0-ZERO-COST-ABLATION-MANDATORY-FUTURE-KPIS` | BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-PRE-REG | Every future hypothesis pre-reg SHALL declare A0-zero-cost-ablation cell at v1 emission. |
| `P1-H050-PER-ENTRY-COST-INVENTORY` | non-blocking | Extract entry-count + round-trip-count separately at v2 emission. |
| `P1-H060-PER-SYMBOL-N-TRADES-SIDECAR-EXTEND` | non-blocking | Extend H060 sidecar with per-symbol n_trades at v3 emission. |
| `P1-COST-LIGHT-GENETIC-SUCCESSOR-PRE-REG` | non-blocking | Per ADR-0027 §D-4: pre-register H067 + H068 + H069 cost-light successors. |
| `P1-COST-FRICTION-BREAKEVEN-KPI-CARD-ANNOTATION` | non-blocking (forward-link to ADR-0028) | Add cost-friction annotation to KPI card §"Methodological-correctness annotations" once ADR-0028 lands grammar. |

## Append discipline

- Per [ADR-0013 §4.1 non-loss](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), this trail is immutable post-commit; corrections produce a versioned successor.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../scripts/_hooks/check_non_loss_deletion.py).
