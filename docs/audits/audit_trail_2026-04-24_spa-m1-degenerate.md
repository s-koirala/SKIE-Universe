---
title: P1-H050-SPA-M1-DEGENERATE — single-strategy degenerate handling for Hansen 2005 SPA
date: 2026-04-24
worktree: claude/inspiring-franklin-13a1f1
artifact: ADR-0008 §"Single-strategy degenerate handling (|M|=1)" + hansen_spa.py runtime invariant + test coverage
ticket: P1-H050-SPA-M1-DEGENERATE
audit_protocol: ~/.claude/skills/audit-remediate-loop (Round-1 implementation; subagent verification deferred to main thread per SKILL.md §40-43)
verdict: round-1-implementation-complete (subagent-verified Round-2 not claimed in this trail)
---

# Audit trail — P1-H050-SPA-M1-DEGENERATE

## Context

[scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) (line 474, post-rebase) calls `hansen_spa_test` with a single-strategy column (`|M|=1`). [Hansen 2005, *J. Business & Economic Statistics* 23(4):365-380](https://doi.org/10.1198/073500105000000063) SPA is fundamentally a multi-strategy null-hypothesis test (`H_0: max_{k=1..m} E[d_{k,t}] <= 0`) — with `|M|=1` the max collapses to a single term and the SPA-vs-benchmark family interpretation becomes degenerate. Per [~/.claude/rules/quant-project.md](../../.claude/rules/quant-project.md) §Inference, "Multiple testing across strategies: Hansen 2005 SPA". The single-strategy invocation needs documented semantics.

## Method-fidelity anchor

Hansen 2005 §2 + §2.4 frames the test as

  T_SPA = max_k max(0, sqrt(n) · d_bar_k / omega_k),
  H_0  : max_k E[d_{k,t}] <= 0,

with three recentering variants (SPA_l, SPA_c, SPA_u) for the bootstrap analogue. At `m = 1` the max-over-k reduces to the single-column statistic; the bootstrap p-value `p = (1/B) #{ b : T*^b >= T_SPA }` becomes a one-sided studentised stationary-bootstrap test of `H_0: E[d] <= 0`, equivalent in construction to the studentised pivotal CI of [Hall 1992 §3.5](https://doi.org/10.1007/978-1-4612-4384-7) / [Davison & Hinkley 1997 §5.4](https://doi.org/10.1017/CBO9780511802843) (one-sided, recentered at the chosen `g`).

**Variant-collapse table (m = 1)** derived directly from `_recenter_terms` in [src/skie_ninja/inference/multipletest/hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py):

| Regime | g_lower | g_consistent | g_upper | p-value relation |
|---|---|---|---|---|
| `d_bar >= 0` | `d_bar` | `d_bar` | `d_bar` | identical |
| `0 > studentised >= -threshold` | `0` | `d_bar` | `d_bar` | SPA_l differs |
| `studentised < -threshold` | `0` | `0` | `d_bar` | SPA_u differs |

Threshold `threshold = sqrt(2 log log n)` is the Andrews 1999 constant from §2.4.

The user-task brief asserted "all three collapse to the same single-strategy p-value" — corrected here: variants collapse only in the practically-relevant `d_bar > 0` regime (the regime of any signal that would pass an evidence-bar gate). In negative-`d_bar` regimes the variants split mechanically; the split is not interpretable as "best-of-family" at `m = 1` because there is no family. This refined statement is documented in the new ADR-0008 subsection.

## Subagent-spawn protocol — AVAILABILITY NOTE

Per [~/.claude/skills/audit-remediate-loop/SKILL.md](C:\Users\skoir\.claude\skills\audit-remediate-loop\SKILL.md) §2 and "Auditor selection", end-of-round audits MUST spawn `quant-auditor` and `literature-check` subagents via the Agent (Task) tool. **The Agent / Task tool is NOT surfaced in this environment** — verified by ToolSearch queries `select:Task,Agent` and `subagent` (no matches). Pattern matches the constraint documented in [audit_trail_2026-04-24_lw2008-differential-ci.md](audit_trail_2026-04-24_lw2008-differential-ci.md).

This trail therefore records **Round-1 implementation only** with inline self-audit. Subagent-verified Round-2 is deferred to the main thread per SKILL.md §40-43 ("proper-isolated subagent verification will run from main thread"). The Round-1 product is deliberately scoped narrow to keep that subsequent verification tractable.

## Round 1 — implementation

### Files modified

1. **[docs/decisions/ADR-0008-spa-omega-method.md](../../docs/decisions/ADR-0008-spa-omega-method.md)** — appended new subsection "Single-strategy degenerate handling (|M|=1)" with: background, mathematical reduction, variant-collapse table, decision (pass-through), rejected alternatives (skip / raise), cross-reference to [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) and the [audit_trail_2026-04-24_lw2008-differential-ci.md](audit_trail_2026-04-24_lw2008-differential-ci.md) closing of `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` at commit `11f8fce`, code-level invariants, and verification status.

2. **[src/skie_ninja/inference/multipletest/hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py)** — added:
   - `import warnings`.
   - New class `SingleStrategySPAWarning(UserWarning)` with docstring pointing to ADR-0008 §"Single-strategy degenerate handling (|M|=1)".
   - Function-entry `warnings.warn(..., SingleStrategySPAWarning, stacklevel=2)` inside `hansen_spa_test` after the `n >= 4 and m >= 1` validation, fired iff `m == 1`. Pass-through behaviour preserved (no `raise`).
   - "Notes" section in the function docstring documenting the degenerate case and pointing the caller at `ledoit_wolf_2008_differential_ci` for primary single-statistic inference.
   - `SingleStrategySPAWarning` added to `__all__`.

3. **[src/skie_ninja/inference/multipletest/__init__.py](../../src/skie_ninja/inference/multipletest/__init__.py)** — re-export `SingleStrategySPAWarning`.

4. **[tests/unit/test_inference_hansen_spa.py](../../tests/unit/test_inference_hansen_spa.py)** — added test class `TestSingleStrategyDegenerate` with 6 tests:
   - `test_m_eq_1_emits_warning` — `pytest.warns(SingleStrategySPAWarning, match="m=1")`.
   - `test_m_eq_1_warning_class_is_user_warning` — class hierarchy invariant.
   - `test_m_geq_2_no_warning` — `simplefilter("error", SingleStrategySPAWarning)` confirms no emit at `m=3`.
   - `test_m_eq_1_returns_valid_result` — pass-through returns `n_strategies == 1`, all p-values in `[0, 1]`.
   - `test_m_eq_1_pvalue_matches_manual_one_sided_bootstrap` — replicates the bootstrap with the same RNG seed + block length on the single column and confirms `res.statistic` and `res.p_value` match a manual one-sided studentised stationary-bootstrap p-value to `1e-12`. Exercises the variant-collapse table by asserting the fixture has `d_bar > 0` (so SPA_c uses `g = d_bar`, matching the manual recenter).
   - `test_m_eq_1_variant_collapse_in_positive_dbar_regime` — confirms `p_lower == p_consistent == p_upper` in the positive-`d_bar` regime (table row 1).
   - `test_m_eq_1_variant_ordering_preserved` — confirms `p_lower <= p_consistent <= p_upper` still holds at `m=1` in the negative-`d_bar` regime (mechanical consequence of recentering definitions).

   Also added top-level imports (`warnings`, `stationary_bootstrap_indices`, `SingleStrategySPAWarning`) — the manual-bootstrap test reuses the project's stationary-bootstrap primitive for index draws to match `hansen_spa_test`'s internal call exactly.

### Files NOT modified (per task brief)

- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) — parallel orchestrator-triple agent has scope; degenerate handling pushed down to the SPA function level.
- [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py), [sharpe_ci.py](../../src/skie_ninja/inference/stats/sharpe_ci.py), [ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py).
- Hypothesis register, root `CLAUDE.md`, other ADRs, memory files.

### Inline self-audit findings

| ID | Severity | Category | Issue | Disposition |
|---|---|---|---|---|
| F-1-1 | minor | method | User brief asserts "all three variants collapse to the same single-strategy p-value when m=1" — false in negative-`d_bar` regime (see variant-collapse table) | Documented correctly in ADR with three-row regime table; test `test_m_eq_1_variant_collapse_in_positive_dbar_regime` only asserts collapse in positive-`d_bar` regime; complementary test `test_m_eq_1_variant_ordering_preserved` covers ordering in negative-`d_bar` regime |
| F-1-2 | minor | method | Manual-bootstrap test must use the same recentering as SPA_c (the default `variant`); SPA_c at `d_bar > 0` uses `g = d_bar` so the manual test centres at `boot_means - d_bar` | Asserted as a precondition (`assert d_bar > 0.0`) and inline-commented |
| L-1-1 | residual | citation | Hansen 2005 JBES PDF blocked at tandfonline; SSRN preprint returned HTTP 403 on 2026-04-24 | Documented in new ADR subsection §"Verification status"; existing follow-up `P1-SPA-PDF-VERIFY` covers the broader gap (cycle 5 audit trail) |
| L-1-2 | minor | citation | SPA pass-through behaviour at `m=1` cited against secondary sources (`arch` Python package, MulCom Ox reference) | Acceptable for an ADR documenting project policy; primary-source verification of `m=1` semantics is part of `P1-SPA-PDF-VERIFY` |
| L-1-3 | verified | citation | Hall 1992 ISBN 978-0-387-94508-8 (Springer) and Davison & Hinkley 1997 ISBN 978-0-521-57471-6 (Cambridge UP) verified via the existing LW2008 audit trail; reused here for the studentised-pivotal CI cross-reference | — |
| R-1-1 | minor | reproducibility | New warning is `UserWarning` subclass — captured by default `pytest` warning filters (no `pytest.ini` override needed) | Verified by running `pytest tests/unit/test_inference_hansen_spa.py -W error` locally — `test_m_geq_2_no_warning` is the explicit guard |
| R-1-2 | minor | reproducibility | `stacklevel=2` attributes the warning to the caller's frame (so `pytest -W error::skie_ninja.inference.multipletest.SingleStrategySPAWarning` points at the orchestrator, not the SPA module internals) | Documented in ADR §"Code-level invariants" |

### Code-style / lint

- Pre-edit ruff baseline on the three edited files: 16 errors (pre-existing tech-debt: `PLR0912`, `N806` on existing `T_stat`/`T_boot`, `PLC0415` deferred imports, `SIM108` ternary, `PLR2004` magic numbers in size tests).
- Post-edit ruff: 16 errors (same set; `PLR0912` count went from `14 > 12` to `15 > 12` due to the added `if m == 1:` branch but no new error rows).
- New tests use lowercase `t_obs` / `t_boot_manual` to avoid introducing new `N806` rows (the existing module's `T_stat`/`T_boot` are pre-existing and out of scope for this follow-up).
- Net new ruff errors introduced: **0**.

### Test-suite delta

- Pre-edit `tests/unit/test_inference_hansen_spa.py`: 22 tests.
- Post-edit: **29 tests** (+7 new in `TestSingleStrategyDegenerate`).
- Targeted run under BLAS-pinned env (`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run python -m pytest tests/unit/test_inference_hansen_spa.py -q`): **29 passed in 3.13s**.
- Joint Hansen-SPA + bootstrap suite (sanity check on shared bootstrap primitives): **61 passed in 3.50s**.
- Full unit suite re-run pending in-thread (background process active at trail-write time); the touched-file paths are isolated from the orchestrator/H050 path so cross-suite regressions are not expected.

## Residual risk

- **Subagent-verified Round-2 not run.** `quant-auditor` + `literature-check` + `reproducibility-verifier` parallel triad is the project's standing audit protocol; the Agent tool's absence in this environment forced inline self-audit substitution. Main-thread subagent verification is the next step before this follow-up is closed in [CLAUDE.md](../../CLAUDE.md). Pattern documented in [audit_trail_2026-04-24_lw2008-differential-ci.md](audit_trail_2026-04-24_lw2008-differential-ci.md) and [audit_trail_2026-04-24_h050-aggregation-rule.md](audit_trail_2026-04-24_h050-aggregation-rule.md).
- **Primary-source quote from Hansen 2005 §2.4 not obtained** — `P1-SPA-PDF-VERIFY` (cycle-5 follow-up) covers this; the new ADR subsection's verification status section explicitly notes the gap and the secondary-source cross-checks.
- **PLR0912 branch count** in `hansen_spa_test` is now `15 > 12`; pre-existing tech-debt with one additional branch from this change. Refactoring the validation block to a helper would eliminate the lint but is out of scope for this follow-up.
- **Pass-through choice does not eliminate the gate-decision question.** The orchestrator still passes the `m=1` SPA p-value through to the gate logic. Per the new ADR subsection, LW2008 differential CI is the *primary* inference for H050; the `m=1` SPA result is corroborative. Whether the orchestrator actually treats SPA as corroborative-only (vs as a hard gate) is a separate orchestrator-level concern, out of scope here per the task brief's "DO NOT touch this section" constraint.

## Citations chain (verified at this revision)

- [Hansen, P. R. 2005. "A Test for Superior Predictive Ability". *J. Business & Economic Statistics* 23(4):365-380](https://doi.org/10.1198/073500105000000063) — primary reference; PDF blocked, secondary verification via existing module docstring.
- [White, H. 2000. "A Reality Check for Data Snooping". *Econometrica* 68(5):1097-1126](https://doi.org/10.1111/1468-0262.00152) — the RC test SPA generalizes; relevant for variant-collapse argument.
- [Andrews, D. W. K. 1999. "Consistent Moment Selection Procedures for Generalized Method of Moments Estimation". *Econometrica* 67(3):543-564](https://doi.org/10.1111/1468-0262.00036) — `sqrt(2 log log n)` threshold cited in `_andrews_threshold`.
- Hall, P. 1992. *The Bootstrap and Edgeworth Expansion*. Springer. ISBN 978-0-387-94508-8 — studentised pivotal CI construction; cross-reference for the one-sided reduction.
- Davison, A. C. & Hinkley, D. V. 1997. *Bootstrap Methods and their Application*. Cambridge UP. ISBN 978-0-521-57471-6 — §5.4 eq. 5.10 for the studentised pivotal CI.
- [Ledoit, O. & Wolf, M. 2008. "Robust performance hypothesis testing with the Sharpe ratio". *J. Empirical Finance* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) — primary inference for H050 single-statistic case; cross-referenced from new ADR subsection.
- [audit_trail_2026-04-24_lw2008-differential-ci.md](audit_trail_2026-04-24_lw2008-differential-ci.md) — closes `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` at commit `11f8fce`; cross-referenced for the LW2008 callable now available to the orchestrator.

## Exit posture

- **Verdict**: round-1-implementation-complete. Subagent-verified Round-2 deferred to main-thread per task brief.
- **Files modified**: 4 (1 ADR, 1 module + 1 package init, 1 test file).
- **Tests added**: 7 (in 1 new test class).
- **Test suite**: 22 → 29 in `test_inference_hansen_spa.py`; all green under BLAS-pinned env.
- **Ruff**: net zero new errors.
- **Not committed** per task brief.
- **Follow-up**: `P1-H050-SPA-M1-DEGENERATE` ready for closure pending main-thread subagent verification. `P1-SPA-PDF-VERIFY` remains open (cycle-5 follow-up; out of scope here).
