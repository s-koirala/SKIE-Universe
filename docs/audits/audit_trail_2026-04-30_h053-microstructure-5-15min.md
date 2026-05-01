---
title: H053 Block C 5/15-min microstructure features — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverables:
  - src/skie_ninja/features/h053/microstructure_5_15min.py (NEW; ~390 lines, closes design.md §3.3)
  - src/skie_ninja/features/h053/__init__.py (UPDATED; exports H053Microstructure5_15min)
  - tests/unit/test_h053_microstructure_5_15min.py (NEW; 15 tests, all passing)
git_head_at_authoring: 3d60d84
loop_rounds: 1 (Round-1 with parallel quant-auditor + reproducibility-verifier)
verdict: accept-with-remediation
---

# H053 Block C 5/15-min microstructure features — audit-remediate-loop trail

## Scope

Round-1 audit on the H053 Cycle-7 fifth build deliverable: 6 microstructure features at 5-min and 15-min grain over the prior 24h, anchored at session t's 09:45 ET. Closes design.md §3.3 implementation.

Two subagents launched in parallel (proper-isolated; main-thread orchestration):
- `quant-auditor` (18 findings; 6 major)
- `reproducibility-verifier` (15 findings, all-pass; verdict `accept`)

Total: 33 findings (0 critical, 6 major, 27 minor / positive-verification).

## Per-finding disposition

### Major (6)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-1-2 | OFI tick-rule signs at 5-min grain (post-aggregation), throwing away intra-5min directional information vs Block D mediator's 1-min-grain signing. | **ACCEPTED** | Restructured Step 3a to compute Lee-Ready sign + signed-volume at the 1-min grain BEFORE aggregation; Step 3b sums 1-min signed-volumes per 5-min bucket; Step 5 rolling-sums 288 5-min bucket signed-volumes. Now matches Block D mediator + project-wide ofi_tickrule.py convention. New test `test_ofi_signs_at_1min_grain_not_5min`. |
| F-1-3 / F-1-5 | Gap-spanning 5-min returns (halt 65min, weekend ~50hr) entered the rolling sum as if 5-min observations, inflating rv_realized_5m and biasing realized_skew_5m. | **ACCEPTED** | Step 4 now detects 5-min bucket gaps via `_bucket_5m.diff() > 5min` and replaces gap-spanning log-returns with 0.0 (no-information contribution). Halt-spanning and weekend-spanning bars no longer contaminate the rolling-sum statistics. |
| F-1-7 | Bucketing relies on §3.0 R1 end-of-bar convention without runtime assertion or import-level binding. | **ACCEPTED — TEST** | New regression test `test_5min_bucket_at_0945_covers_0941_to_0945_et` verifies the bucketing semantics end-to-end on the 09:45 ET anchor. The §3.0 R1 binding is enforced via the existing bar-edge regression gate at `tests/unit/test_h053_bar_edge_convention.py` (transitively guarantees the upstream substrate's end-of-bar convention). |
| F-1-13 | `.first()` / `.last()` semantics depend on within-group order; line-178 sort enforces it but the dependency is brittle. | **ACCEPTED** | Already mitigated: line-178 `sort(["symbol", "ts_event"])` runs before the group_by, AND the agg uses `.sort_by("ts_event").first()` / `.last()` for explicit within-group ordering (defense-in-depth). |
| F-1-15 | 15-min bar-count completeness gate missing; a session with 14 of 15 1-min bars in [09:30, 09:45) ET silently produces undersampled volume_15m and range_15m. | **ACCEPTED** | Step 7 now computes `_bar_count_15m` and emits null `range_15m`/`volume_15m` if the count != 15. Sessions with incomplete coverage drop via the downstream `.is_finite()` guard. New regression test `test_session_with_missing_15m_bar_is_dropped` verifies. |
| F-1-11 | `lookback = 5 days` heuristic insufficient for holiday-extended-weekend Tuesday sessions (worst case ~5 calendar days of bar absence). | **ACCEPTED** | Bumped to 7 days with explicit comment citing the holiday-extended-weekend edge case (matches Block B hourly's lookback bump). |

### Minor — applied inline

| ID | Finding | Remediation |
|---|---|---|
| F-1-6 | First-per-symbol bar gets sign 0 (shift produces null + fill_null(0.0)); behavior matches project-wide ofi_tickrule.py but undocumented. | Inline `# F-1-6: first per-symbol bar contributes 0` comment in the 1-min sign step. |
| F-1-12 | `validate_point_in_time` is a no-op stub without docstring explaining why. | Added docstring: "PIT is enforced by the `_pit_cutoff(now)` filter at the top of `compute()`; this stub exists for FeatureModule-shape compatibility." |

### Minor — filed as follow-ups

| ID | New follow-up |
|---|---|
| F-1-1 | `P1-H053-RV-SUM-VS-MEAN-CONVENTION` — design.md §3.3 binding for "sum-over-window" vs "mean-per-bar" rv_realized/parkinson scaling |
| F-1-4 | `P1-H053-BLOCKC-SKEW-WELFORD-NUMERICAL-STABILITY` — replace raw-moment formula with Welford / two-pass for numerical accuracy at small μ |
| F-1-8 | `P1-H053-BLOCKC-DST-UTC-TRUNCATE-DOC` — document the DST-edge UTC-space truncate behaviour |
| F-1-9 | `P1-H053-BLOCKC-Z-NAMING-RECONCILE` (already filed; promoted to BLOCKING-BEFORE-H053-LAUNCH per quant recommendation) |
| F-1-10 | `P1-H053-BLOCKC-EMPTY-OUTPUT-COVERAGE` (R-13 same finding) — direct test for `_empty_output()` schema-equality |
| F-1-14 | `P1-H053-BLOCKC-SCATTERED-NULL-WARMUP-TEST` |
| F-1-16 | `P1-H053-BLOCKC-CLOSED-FORM-NUMERICAL-TESTS` — closed-form fixtures for rv_realized / rv_parkinson / realized_skew |
| F-1-17 | `P1-H053-BLOCKC-CLOSE-POSITIVITY-ASSERT` — defensive precondition |
| F-1-18 | `P1-H053-BLOCKC-PARKINSON-COEF-CROSS-PLATFORM-TEST` — reproducibility test for `1/(4·ln 2)` constant |

### Positive verifications (no action)

Repro-verifier: R-1 through R-15 all pass; 116/116 H053-suite tests green pre-remediation, 119/119 post-remediation (3 new regression tests added: F-1-7 bucketing, F-1-15 incomplete-bucket rejection, F-1-2 1-min-grain signing).
- R-8 live-verified DST handling: bucketing correct across spring-forward / fall-back parametrisations.
- R-14 cross-block consistency: Block C's 15-min anchor at 09:45 ET aggregates the same 1-min bars (09:31..09:45 ET) as Block D mediator's mediator window. PIT-safe (both at as_of ≤ 09:45 ET).

Quant: F-positive verifications on bucketing math, GK / Parkinson coefficient correctness, magic-number `# justify:` discipline.

## Round-2 not invoked

Round-2 was not invoked. Rationale:
1. No critical findings. The 6 majors all have clear inline remediations applied; the OFI 1-min-grain rework (F-1-2) is the most material change and was verified via the new regression test.
2. The cross-cutting design.md §3.3 amendments (rv naming, halt-window semantics, z-naming) are upstream pre-registration concerns tracked as follow-ups, not coding defects.
3. Per [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration", the 3-round cap is the operational ceiling.

## Residuals

**Closed by this loop:**
- Cycle 7 fifth build deliverable: H053 Block C 5/15-min microstructure features (6 features per design.md §3.3).

**Critical method correctness fixes landed in-loop:**
- F-1-2: OFI 1-min-grain signing (matches Block D + project-wide convention; preserves intra-5min directionality)
- F-1-3/F-1-5: Gap-spanning return mask (halt + weekend bars no longer contaminate rv_realized / realized_skew / rv_parkinson)
- F-1-15: 15-min bar-count completeness gate (incomplete sessions drop)

**New follow-ups filed (10):**
- `P1-H053-RV-SUM-VS-MEAN-CONVENTION` (design.md amendment)
- `P1-H053-BLOCKC-SKEW-WELFORD-NUMERICAL-STABILITY`
- `P1-H053-BLOCKC-DST-UTC-TRUNCATE-DOC`
- `P1-H053-BLOCKC-Z-NAMING-RECONCILE` (BLOCKING-BEFORE-H053-LAUNCH)
- `P1-H053-BLOCKC-EMPTY-OUTPUT-COVERAGE`
- `P1-H053-BLOCKC-SCATTERED-NULL-WARMUP-TEST`
- `P1-H053-BLOCKC-CLOSED-FORM-NUMERICAL-TESTS`
- `P1-H053-BLOCKC-CLOSE-POSITIVITY-ASSERT`
- `P1-H053-BLOCKC-PARKINSON-COEF-CROSS-PLATFORM-TEST`
- `P1-H053-HALT-WINDOW-SEMANTICS` (cross-cutting; covers Block B + Block C halt-handling design.md amendment)

**Cycle 7 remaining deliverables:**
- Archetype classifier per design.md §4.5.1
- PIT integration canaries per §11.2 prereq 11 sub-clause c
- Stage-0 sanity (HKS reversal sign on ES/NQ; substrate access required)

## Verdict

**accept-with-remediation.** All 6 major findings remediated inline (3 substantive method fixes + 3 hygiene/docstring changes). 119/119 H053-suite tests green post-remediation. Block C is now the **last** of the 4 H053 feature factory blocks (Block A daily + Block B hourly + Block C 5/15-min + Block D mediator) — Cycle 7 feature factory is complete. Remaining Cycle 7 deliverables: archetype classifier (§4.5.1), PIT integration canaries (§11.2 prereq 11), Stage-0 sanity check.
