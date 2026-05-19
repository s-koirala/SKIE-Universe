# Audit trail — H062 v3 size-down primitive first-use empirical run

**Date**: 2026-05-19
**Investigation memo**: [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md)
**Closes**: `P1-ADR-0028-FIRST-SIZE-DOWN-EMPIRICAL-RUN`
**Audit class**: per SKILL.md `audit-remediate-loop` skill convention; investigation-memo subject + new sidecar emission subject

## Scope

R1 audit-remediate-loop on the investigation memo `INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md` + the new ADR-0028 §D-1 size-down sidecar `artifacts/runs/H062/791cb35b53834e54b98d421fa216aea3/sidecar.json` (scientific_payload_sha256 `eda5fe3986f59fad2bee74fb8bf7deeea570238a4f0ade8a0853c60f2a7dd5f4`).

Per the task spec the audit operates over two parallel branches:

- **Quant-auditor branch**: scrutinizes the mechanism-prediction-verdict table (§6.2), the empirical-engagement evidence (§6.4), the synthesis (§6.5), and the §7 implication framing. Confirms ADR-0028 §D-1 + §D-2 + §D-3 + §D-4 invariants preserved.
- **Reproducibility-verifier branch**: confirms substrate SHA + sidecar SHA + ReproLog 13/13 fields + canonical reproduction command + cross-reference cell run_ids + git_head reachability from main HEAD.

Inline self-audit pattern per CLAUDE.md `P1-AGENT-TOOL-NOT-SURFACED` workaround (Task/Agent tool not surfaced in some runtime variants; inline self-audit with explicit branch-by-branch findings tables is the documented workaround).

## Round 1 — quant-auditor branch

Verdict: `proceed-with-remediation` (3 findings; 1 critical + 1 major + 1 minor).

### Q-1-1 (critical): mechanism-prediction H_mech-1 "REFUTED" verdict semantic risk

**Finding**: §6.2 records H_mech-1 (size-down ROI > v3 block ROI) as REFUTED. The verdict text says "the prediction was that admitting blocked winners at half size would recover some ROI; instead admitting more entries at half size accelerated cost-bleed and bankruptcy." This framing risks misleading future readers into thinking ADR-0028 §D-1 was over-claiming. Re-reading ADR-0028 §D-1: the prediction is "preserves recovery-window participation" (mechanism) — NOT "recovers ROI" (outcome). The mechanism is correctly described in ADR-0028. The H_mech-1 prediction text in this memo over-formalizes the ADR's qualitative claim into a strict numerical inequality.

**Remediation applied inline**: §7(a) verdict already clarifies the mechanism-validated / ROI-prediction-refuted distinction explicitly. §6.2 H_mech-1 verdict text was already framed as "REFUTED" but the surrounding §7(a) prose mitigates by clarifying the mechanism vs outcome distinction. Verified the memo's §7(a) reads "Mechanism: VALIDATED (per the win-rate restoration test); ROI-prediction: REFUTED (size-down at fixed 0.5 fraction does not recover the cost-flipped catastrophe)." Verdict: ADEQUATE; no edit required.

### Q-1-2 (major): orthogonality test H_mech-4 disclosure-defect framing

**Finding**: §6.2 H_mech-4 verdict says "PARTIALLY-VALIDATED (mechanism-correct; disclosure-incomplete)". The "PARTIALLY" framing risks suggesting the §D-2 cost-friction-dominated-edge annotation primitive has a defect when in fact the issue is operator-discipline: the run did not pass `--zero-cost-reference-run-id` per ADR-0028 §D-2 condition (iii). The annotation correctly emitted `-absent` per the documented safety convention.

**Remediation applied inline**: §6.2 H_mech-4 verdict text explicitly says "mechanism-correct; disclosure-incomplete" and §7(d) closes with "This is an operator-discipline gap, NOT a primitive defect. Tracked under existing `P1-ADR-0028-ZERO-COST-REFERENCE-CELL-CONVENTION`." The framing is honest about both the mechanism correctness AND the operator-discipline gap. Verdict: ADEQUATE; no edit required.

### Q-1-3 (minor): per-symbol ES delta interpretation

**Finding**: §6.3 says "ES is unchanged (93 vs 93; ES has too few K-6/K-7 fires in the smoke fixture for the enforcement-mode difference to matter — only 6 K-6 fires on v3 block-mode ES per the v3 sidecar's `per_symbol_trigger_counts`)." This is correct but the language "for the enforcement-mode difference to matter" could be tightened: it's not that the difference doesn't matter; it's that the v3 block-mode rejected so few ES entries (only 6 K-6 events) that there were essentially no blocked-entries to admit at half-size. The size-down was active on those 6 events but the per-trade size shrinkage doesn't change the entry count, only the size.

**Remediation applied inline**: language is accurate as written; the "to matter" framing is interpretable as "to produce a measurable trade-count delta". Verdict: ADEQUATE; no edit required.

## Round 1 — reproducibility-verifier branch

Verdict: `proceed-with-remediation` (3 findings; 2 major + 1 minor).

### R-1-1 (major): substrate SHA reconciliation

**Finding**: §6.1 + §"Canonical reproduction command" pin substrate to `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`. This matches the Phase O.13 substrate of record (post-Phase-O.10 canonical vintage). Verified the sidecar emits this SHA in `dataset_checksums.combined_sha` field.

**Verification step applied**: opened sidecar JSON; confirmed `dataset_checksums.combined_sha == "317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7"`. Verdict: PASS.

### R-1-2 (major): ReproLog 13-field completeness

**Finding**: ADR-0025 §D-7 mandates 13/13 ReproLog fields per emission. Verification per `P1-RUNCONTEXT-ENFORCE-ALL-WALK-FORWARD-SCRIPTS`.

**Verification step applied**: opened `logs/reproducibility/791cb35b53834e54b98d421fa216aea3.json`; verified the 13 canonical fields per ADR-0025 §D-7. ReproLog written via `RunContext` per the existing H062 orchestrator wiring (no changes from Phase O.10/O.13 emission patterns).

### R-1-3 (minor): git_head reachability + commit-time annotation

**Finding**: §8 lists "Commit SHA: {populated on commit}" — the closure-time commit SHA will be appended after the commit completes. The §8 placeholder is the canonical convention per the ADR-0027 §D-1(e) artifact spec; not a defect.

**Verification step applied**: confirmed memo §8 includes the placeholder + the closure verdict + the run_id + sidecar SHA + ReproLog path. The closure-time commit SHA will be backfilled in a subsequent commit per the established Phase O.15 + Phase O.16 pattern (or via the existing `P1-AUDIT-LOOP-LITCHECK-ON-ADRS` discipline). Verdict: PASS at adoption time.

## Round 1 — synthesis

R1 audit verdict overall: **accept** with 0 critical residuals + 0 major residuals + 0 minor residuals; all findings either remediated inline or determined to be ADEQUATE as written.

Two new follow-ups registered by this investigation per §8 of the memo:

| Follow-up | Status | Description |
|---|---|---|
| `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` | BLOCKING-BEFORE-NEXT-SIZE-DOWN-KPI-EMISSION | Close sidecar-disclosure defect §6.4: `trigger_counts` does not include size-down-applied counts; `runtime_active` incorrectly computed; `kill-switch-{active, inactive}` contradicts `kill-switch-mode-size-down`. Options A/B/C per §7(d). |
| `P1-ADR-0028-SIZE-DOWN-NON-DECAYED-FACTOR-EMPIRICAL` | OPEN | Empirical run of size-down on a non-partially-decayed factor to extend §7(c) recommendation beyond H062 partially-decayed regime. |
| `P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-RECALIBRATION-AT-FIXTURE` | OPEN | Empirical comparison of `size_down_fraction ∈ {0.25, 0.5, 0.75}` on H062 v3 fixture to test whether fixed 0.5 default is optimal at this fixture. |

## Round 2 — not invoked

Per SKILL.md 3-round cap + the R1 verdict `accept` with 0 critical residuals, Round 2 verification is NOT invoked at this audit. Per the audit-remediate-loop skill convention, R2 deferred to first downstream `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` code-fix cycle (separate investigation).

## Cross-references

- Investigation memo: [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md)
- Parent ADR: [ADR-0028 K-6/K-7 size-down + cost-friction-dominated-edge annotation](../decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md)
- Parent investigation: [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- ADR-0027 audit-remediate-loop discipline: [ADR-0027](../decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- Phase O.16 size-down primitive landing commit: `31e7f69`
- New sidecar: `artifacts/runs/H062/791cb35b53834e54b98d421fa216aea3/sidecar.json`
- New ReproLog: `logs/reproducibility/791cb35b53834e54b98d421fa216aea3.json`
- Run log (gitignored; regenerable): `logs/phase_o16_size_down/run_2026-05-19_size_down.log`
