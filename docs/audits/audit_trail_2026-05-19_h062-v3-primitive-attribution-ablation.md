# Audit trail — INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION

**Date:** 2026-05-19
**Scope:** Phase O.15 — empirical decomposition of H062 v3 smoke's −99.9995% basket OOS by per-primitive engagement (cost-model / kill-switch-runtime / equity-rebase-current) per [ADR-0027 §D-3 empirical-before-amendment sequencing rule](../decisions/ADR-0027-operational-discipline-bounded-exploration.md). Investigation entry `INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION` registered at Phase O.14 commit; closure landed in this Phase O.15 commit.
**Audit-remediate-loop skill:** invoked per SKILL.md 3-round cap (Round 1 with parallel quant-auditor + reproducibility-verifier; Round 2 verification deferred to first cross-reference cycle of the finding, e.g., the future ADR-0025 K-6/K-7 size-down vs block amendment cycle).
**Output artifact:** [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) (investigation-memo class per ADR-0027 §D-1(e)).
**Substrate dataset_checksum:** `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.0 substrate).
**Project HEAD at investigation start:** `fe95ec1bdf062cf5eb39e0bb9440ce9613da6633`.
**Empirical fixture:** 4 new smoke-mode H062 walk-forward runs (each ~12-16 min compute on 4-cell inner-CV grid × 4 symbols, 60-train/30-test inner-CV folds, rng_seed `20260514`) plus 2 reference cells (Phase O.10 v2 full-grid all-OFF sidecar `eb729b201595484594ce4c9ddde72d05`; Phase O.13 v3 smoke all-ON sidecar `154237b365794244974068402b377191`).

## Round 1 — parallel quant-auditor + reproducibility-verifier audit

Two parallel specialist branches per the audit-remediate-loop skill routing convention. Both branches operated on the investigation memo + the 4 new ablation sidecars + the cross-references to reference sidecars.

### Branch: quant-auditor (inline self-audit per `P1-AGENT-TOOL-NOT-SURFACED` documented runtime workaround)

Six findings (0 critical + 3 major + 3 minor). Verdict: `proceed-with-remediation`. All major findings remediated inline before commit.

| ID | Severity | Issue | Remediation |
|---|---|---|---|
| F-Q-1 | minor | Is the A0 baseline (smoke 4-cell grid) directly comparable to A1/A2/A3 (also smoke)? | YES — all 4 use `--smoke` with identical config (4-cell × 130-fold × rng_seed 20260514 × identical fixture; verified via `config_resolved_sha256` across sidecars). Acceptable as-is. |
| F-Q-2 | minor | Is A0 a valid v2-equivalent? A0 = +261.88% vs Phase O.10 v2 full-grid = +217.57% (Δ +44.31 pp due to smoke 4-cell grid vs 48-cell grid cell selection). | Memo §2 already explicitly frames A0 (smoke) as the within-fixture baseline; Phase O.10 v2 (full-grid) as a contextual bookend not a baseline cell. The smoke-vs-full distinction is preserved verbatim in §2 + §6 table footnote. Acceptable as-is. |
| F-Q-3 | major | A3 trade count is 10,342 vs A0's 10,326 (+16 trades) — equity-rebase shouldn't change entry decisions but does at the sizing-floor boundary. | Added "Tertiary observation on A3 trade count" paragraph to §6 trade-activity decomposition explaining the current-equity rebase × sizing-floor mechanism. Acceptable; magnitude is sensitivity-noise (+0.15%). |
| F-Q-4 | major | The saturation-floor framing of additivity (A1 ≈ v3) is load-bearing for the "cost dominates" verdict — if I'm wrong about the saturation floor, the verdict changes. | Memo §6 "Decomposition arithmetic" explicitly states "saturation floor at −100% prevents additivity" and the cumulative v3 Δ ≈ A1 Δ. The framing is empirically anchored: A1 = −100.00% (literal floor); v3 = −99.9995% (within rounding of floor). Both report MaxDD = 100.00% (literal). The framing is correct. Acceptable as-is. |
| F-Q-5 | minor | MPPM CI `excludes_zero` status across cells should be inline. | A1 CI [−1.55, −0.72] excludes zero negative; A2 CI [−0.42, +0.36] covers zero; A3 CI [−0.33, +0.52] covers zero. Documented in §6 table. Acceptable as-is. |
| F-Q-6 | major | A1 win-rate drops 34.24% → 31.17% even WITHOUT kill-switch and with IDENTICAL trade count to A0 — this is a separate mechanism (cost-flips-marginal-winners) requiring explicit synthesis. | Added "Secondary observation on A1 cost-only win-rate" paragraph to §6 trade-activity decomposition documenting the cost-flipping-marginal-winners mechanism distinct from kill-switch asymmetric blocking. |

### Branch: reproducibility-verifier (inline self-audit per `P1-AGENT-TOOL-NOT-SURFACED`)

Four findings (0 critical + 1 major + 3 minor). Verdict: `accept`. All sidecars on disk; reproducibility envelope clean.

| ID | Severity | Issue | Remediation |
|---|---|---|---|
| F-R-1 | major (verify-required) | Did all 4 sidecars use the same substrate SHA? | Verified inline: all 4 ablations + v3 reference use `vendor_legacy_1min_roll_adjusted = 317429e49ad63674...` (canonical post-Phase-O.0 substrate). Acceptable. |
| F-R-2 | minor | Did rng_seed match across all 4 cells + v3 reference? | Verified inline: all 5 cells use `rng_seed = 20260514`. Acceptable. |
| F-R-3 | minor | git_head — were the 4 new ablations made on the same HEAD? | Verified inline: all 4 ablations on `fe95ec1bdf062cf5eb39e0bb9440ce9613da6633` (current main HEAD); v3 reference on Phase O.13 HEAD `648a295fff3af9b1dedb7eb832dcecfa0a296401`. The v3 cross-HEAD reference is acceptable per ADR-0013 §4.1 non-loss (v3 sidecar preserved verbatim; not re-run). |
| F-R-4 | minor | Sidecar SHA256s reproducible? | All 4 sidecars on disk with stable SHA256 (computed inline via `hashlib.sha256(open(p, 'rb').read())`). Sidecar SHA prefix-16 recorded in §6 table per [ADR-0026 §D-3](../decisions/ADR-0026-paradigm-and-reporting-refinements.md) 16-char convention. Acceptable. |

## Round 1 verdict

- **Quant-auditor verdict:** `proceed-with-remediation` → `accept` post-remediation (3 major findings F-Q-3 + F-Q-4 + F-Q-6 closed inline; 3 minor findings F-Q-1 + F-Q-2 + F-Q-5 accept as-is).
- **Reproducibility-verifier verdict:** `accept` (1 major findings F-R-1 verified clean; 3 minor F-R-2 + F-R-3 + F-R-4 documented + accepted).
- **Combined verdict:** `accept-with-residuals` per audit-remediate-loop skill convention; Round 2 verification deferred to first cross-reference cycle of the finding (e.g., the future `P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` cycle).

## New follow-ups registered by Phase O.15

Convention: BLOCKING-* status drives ordering; non-blocking are listed below as polish/extension.

| Follow-up | Status | Description |
|---|---|---|
| `P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` | OPEN; non-blocking; sequenced AFTER this investigation per [ADR-0027 §D-3](../decisions/ADR-0027-operational-discipline-bounded-exploration.md) empirical-before-amendment rule | Empirically motivated by this investigation §7(c). Two-component amendment: (1) K-6/K-7 size-down option with tunable fraction f (operator intuition); (2) cost-realism-aware promotion-decision-rule documenting that hypotheses with marginal mean-edge (CI covers zero PRE-cost) require POST-cost evaluation at ninjascript-implementation decision point. NOT written in this memo; the empirical finding is the input. |
| `P1-H062-DESIGN-MD-CROSS-REFERENCE-INVESTIGATION` | OPEN; non-blocking | Cross-reference this investigation memo from H062 design.md §17 revision-log. Operator-discretionary timing per ADR-0013 §4.1 non-loss (the design.md §1-§7 are immutable; §17 is the canonical cross-reference location). |
| `P1-AGENT-TOOL-NOT-SURFACED` | OPEN; project-wide; carried forward from H055 v2 Phase O.5 | Task/Agent tool not surfaced in some runtime variants; inline self-audit is the documented workaround pattern. This investigation used the inline self-audit pattern; tracking continued. |
| `P1-PHASE-O15-V3-PROMOTION-DECISION-RULE` | OPEN; non-blocking | Project-level promotion-decision-rule per [ADR-0017 §3](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained metric vector SHALL be evaluated POST-cost (= conservative_prior) at first ninjascript-implementation decision point. v(N) KPI cards remain PRE-cost research-only per operator 2026-05-08 + 2026-05-12 standing directives. Implication §7(c) above is the canonical reference. |
| `P1-PHASE-O15-CROSS-HYPOTHESIS-COST-CANARY` | OPEN; non-blocking | Generalize the cost-dominance finding by repeating the ablation pattern on H055 v2 and H050 v1. H055 v2's MGC C3 +87% cell + H050's gated arms −81/−84% are the closest analogs. Tracked under `INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS` registered at Phase O.14. |
| `P1-PHASE-O15-LSKEWNESS-NEGATIVE-MEAN-EDGE-WARNING` | OPEN; non-blocking | Project-level memo: positive L-skewness alone does NOT compensate for negative mean-edge. Future hypothesis design.md §1.5 (or equivalent expected-payoff block) SHALL acknowledge this constraint. Implication §7(e) above. |

## Closure

- **Investigation closure**: per ADR-0027 §D-1(c) form (i) — closed on ablation-complete (4 sidecars on disk + §6 table populated + §7 implication written + R1 audit-remediate-loop applied with `accept-with-residuals` verdict).
- **Commit SHA**: `1adc62a` (Phase O.15 commit; landed 2026-05-19; backfilled via follow-on minor edit per the project's documented post-commit SHA-binding pattern).
- **Push target**: `origin/main`.
- **Time-budget category** (per ADR-0027 §D-5 non-binding annotation): `investigate` (catastrophic-result decomposition; counts toward the ≤25% investigation soft cap of the rolling-30-day commit history per `P1-ADR-0027-TIME-BUDGET-TRACKER-SCRIPT`).

## Cross-references

- Investigation entry source: [docs/audits/audit_trail_2026-05-19_adr-0026-adr-0027.md](audit_trail_2026-05-19_adr-0026-adr-0027.md) (Phase O.14; lists `INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION` as an adoption-time example per ADR-0027 §D-1)
- Parent KPI: [H062 v2 KPI report card](../../research/01_hypothesis_register/H062/H062_kpi_report_v2.md)
- Phase O.13 H062 v3 smoke: CLAUDE.md Phase O.13 ledger entry (sidecar `154237b365794244974068402b377191`)
- ADR-0025: [docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md](../decisions/ADR-0025-abandonment-trigger-infrastructure.md)
- ADR-0027: [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../decisions/ADR-0027-operational-discipline-bounded-exploration.md)
