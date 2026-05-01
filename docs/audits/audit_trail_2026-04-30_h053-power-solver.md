---
title: H053 power-calibration solver — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverables:
  - src/skie_ninja/inference/power.py (NEW; closes H053 design.md §11.2 prereq 19)
  - tests/unit/test_h053_power_solver.py (NEW; 33 tests, all passing)
git_head_at_authoring: 50f3f73
loop_rounds: 1 (Round-1 with parallel quant-auditor + literature-check + reproducibility-verifier)
verdict: accept-with-remediation
---

# H053 power-calibration solver — audit-remediate-loop trail

## Scope

Round-1 audit on the H053 Cycle-7 first build deliverable: the parametric
`required_n` + `mde` solver implementing the inverse-problem counterpart to
the project's data-driven Sharpe-CI infrastructure
(`src/skie_ninja/inference/stats/sharpe_ci.py`). Closes
[research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md)
§11.2 prerequisite 19.

Three subagents launched in parallel (proper-isolated; main-thread orchestration):
- `quant-auditor` (25 findings)
- `literature-check` (5 findings)
- `reproducibility-verifier` (10 findings)

Total: 40 findings (1 critical, 6 major, 33 minor / positive-verification).

## Per-finding disposition

### Critical (1)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| L-2 / F-1-3 | Lo 2002 Proposition 2 misattribution: `(1+ρ)/(1−ρ)` is the AR(1) long-run-variance ratio (Hamilton 1994 §10.3 eq. 10.3.6 geometric series limit), NOT the Bartlett spectral kernel at lag 1 (which is `1+2ρ`) and NOT literal Lo 2002 Prop 2 (which uses η(q) finite-lag NW estimator). The project's Cycle-2 audit already flagged this exact pattern; this regression is exactly what `P1-AUDIT-LOOP-LITCHECK-ON-ADRS` aims to catch. | **ACCEPTED** | Module docstring rewritten to match the hedging pattern established by `sharpe_ci.py::lo2002_hac_adjusted_ci`: explicitly distinguishes the Mertens-Opdyke iid form from literal Lo 2002 §III; explicitly distinguishes the AR(1) closed-form HAC inflation from the data-driven Lo 2002 Prop 2 NW estimator; cites Hamilton 1994 §10.3 eq. 10.3.6 as the primary anchor for `(1+ρ)/(1−ρ)`; cross-references `sharpe_ci.py::lo2002_prop2_eta_ci` for the literal-form data-driven estimator. |

### Major (6)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| L-1 / F-1-1 | Lo 2002 §III "equation 14" attribution: the form `(1 − γ_3·Ŝ + (γ_4−1)·Ŝ²/4)/T` is the Mertens 2002 / Opdyke 2007 generalisation, not literal Lo 2002 eq. 14. Lo 2002 itself contains only the iid-Gaussian special case (eq. 4) and the autocorrelated Proposition 2. | **ACCEPTED** | Docstring updated to credit Mertens 2002 + Opdyke 2007 (DOI [10.1057/palgrave.jam.2250084](https://doi.org/10.1057/palgrave.jam.2250084)). Added explicit references to project's audited `sharpe_ci.py::opdyke2007_ci` which uses the same form with correct attribution. |
| F-1-6 | Unicode `ρ`, `γ_4` characters in raise messages crash on Windows cp1252-default consoles/loggers (project is on Windows 11). | **ACCEPTED** | All raise messages converted to ASCII-only (`rho`, `kurtosis`, `gamma_4` instead of Greek letters). Two regression tests added (`test_raise_messages_are_ascii_only`, `test_mde_pathological_raise_message_is_ascii`) that fail on `str(exc).encode("ascii")` if any non-ASCII bytes regress in. |
| F-1-15 | `n_obs` field name in `PowerCalibration` is ambiguous — could mean per-instrument-annual rate (252), pooled-annual rate (504), or splitter-derived realized OOS sample size (variable). The test fixture used 504 (pooled-annual) but the design.md §9 line 366 binding is `expected_n_oos` (the realized OOS count). | **ACCEPTED** | Renamed `n_obs` → `expected_n_oos` to match design.md §9 line 366 verbatim. Test fixture updated; the value 504 is now correctly interpreted as "504 sessions of pooled OOS data" (≈2 years ES+NQ). |
| F-1-20 | Sidecar write was non-atomic (`path.open("w")` direct write). Mid-write OS-kill (a recurring failure mode per the H050 production-run history) leaves a half-written file. | **ACCEPTED** | Atomic-write pattern: payload is first written to a `.tmp` sibling, then `os.replace()`-d to the final path. New regression test `test_atomic_write_no_residual_tmp` asserts no residual `.tmp` after success. |
| F-1-21 | `written_at` timestamp via `datetime.now()` is non-deterministic; embedded in the main payload it would block any future SHA roll-up of the `PowerCalibration` record. | **ACCEPTED** | Sidecar JSON refactored into a two-block schema: `power_calibration` (the load-bearing dataclass record, bit-deterministic given inputs) + `_meta` (`written_at`, `run_id` — non-deterministic provenance, segregated). Test schema-checked. |
| F-1-2 / L-4 | The H053 power_calibration_addendum_2026-04-30 has an internal language inconsistency between table line 35 (`excess_kurtosis_pilot = 3.0`) and operational-consequence prose (`κ_excess = 0`). Both encode Gaussian under their respective conventions but use the variable name inconsistently. The implementation is internally consistent; the upstream pre-reg language is the bug. | **ACCEPTED — FOLLOW-UP** | Module docstring's Convention note expanded to explicitly call out the upstream language inconsistency, name the responsible follow-up `P1-H053-KURTOSIS-CONVENTION-RECONCILE`, and document that the implementation follows the full-kurtosis convention. |

### Minor — applied inline

| ID | Finding | Remediation |
|---|---|---|
| F-1-4 | HAC inflation distinct from Lo 2002 Prop 2 NW estimator | Module docstring now explicitly distinguishes parametric-pin AR(1) closed-form vs data-driven NW estimator. |
| F-1-5 | `mde` docstring "f(s) is decreasing in s" overpromises in the pathological regime where `z_β·sqrt((γ_4-1)/(4n))·sqrt((1+ρ)/(1-ρ)) ≥ 1`. | Added `test_mde_pathological_regime_raises` that triggers the regime (γ_4=10, ρ=0.95, n=10) and asserts the `s_hi_cap` raise; raise message documents the precise sufficient condition. |
| F-1-18 / F-1-19 / R-8 | `s_max=100.0`, `s_hi_cap = s_max * 1000.0`, `tol=1e-9` magic numbers undocumented per CLAUDE.md "no arbitrary thresholds". | Added inline `# justify:` comments on each, with reasoning anchored in Sharpe-magnitude scale + float64 round-off + bisection-bracket safety. |
| F-1-25 | No test for the negative-variance guard regime in `lo2002_sr_variance`. | Added `test_negative_variance_guard_raises` triggering the regime (skew=2, kurt=3, sr=0.6 → iid_term = -0.155). |

### Minor — filed as follow-ups

| ID | Description | New follow-up |
|---|---|---|
| L-3 | Lo 2002 PDF was paywalled; equation-number pin to "eq. 4" relies on the project's Cycle-2 audit module rather than primary verification. | `P1-LO2002-EQ4-PRIMARY-VERIFY` (verify equation number from a primary copy when accessible) |
| L-4 / F-1-2 | H053 power_calibration_addendum internal language inconsistency `excess_kurtosis_pilot=3.0` (full-kurtosis value with excess-kurtosis name). | `P1-H053-KURTOSIS-CONVENTION-RECONCILE` (amend addendum + data_requirements language) |
| R-6 | Sidecar path order: design.md §9 + §11.2 prereq 19 say `power_calibration_{run_id}.json`; implementation follows project-wide convention `{run_id}_power_calibration.json`. | `P1-H053-SIDECAR-PATH-DESIGN-MD-RECONCILE` (amend design.md §9 + §11.2 prereq 19 to match project convention) |
| R-7 / F-1-14 | Schema field naming differences between dataclass and design.md §9 yaml block (`expected_n_oos` resolves part of this; remaining: `kurtosis` vs `excess_kurtosis_pilot`, `ar1_rho` vs `ar1_rho_pilot`, plus added `skewness`/`one_sided`/`pilot_source` fields). | `P1-H053-POWER-SCHEMA-RECONCILE` (amend design.md §9 yaml block to match implemented dataclass schema verbatim) |
| F-1-17 | `PowerCalibration` lacks `repro_log_run_id` cross-reference back to parent ReproLog. | `P1-H053-POWER-REPRO-LOG-XREF` (add field at orchestrator integration time) |
| F-1-10 | `test_two_sided_requires_more_n_than_one_sided` asserts only monotonicity, not the analytical ratio at α=0.05. | `P1-H053-POWER-TEST-RATIO-TIGHTEN` (tighten to `n_two/n_one ≈ ((z_{α/2}+z_β)/(z_α+z_β))² ± 5%`) |
| F-1-12 | Asymptotic-recovery test 5% tolerance is empirically slack (actual error ~0.06%). | `P1-H053-POWER-TEST-ASYMPTOTIC-TIGHTEN` (tighten to 0.5%) |
| F-1-24 | No `required_n`/`mde` test exercises non-zero skewness path (option-1 reactivation). | `P1-H053-POWER-TEST-NONZERO-SKEW` (parameterized non-zero-skew coverage; gated on option-1 reactivation per addendum re-election clause) |

### Positive verifications (no action)

F-1-7 (n_init z-quantile correctness), F-1-8 (n_max raise behaviour), F-1-9 (SE under H0/H1), F-1-11 (negative-variance guard correctness), F-1-13 (inversion-consistency tolerance), F-1-22 (sqrt safety), F-1-23 (option-3 numerical pin); R-1, R-2, R-3, R-4, R-5, R-9, R-10; L-5 (power formula textbook-standard).

## Round-2 not invoked

Round-2 was not invoked. Rationale:
1. The single critical finding (L-2 / F-1-3 Lo 2002 Prop 2 misattribution) was remediated by adopting the project's own Cycle-2-audited hedging pattern verbatim. No new contradiction risk.
2. The 6 major findings landed observable text/code changes with new regression tests where applicable (ASCII raise message + atomic-write + pathological-regime).
3. The 7 deferred follow-ups are non-blocking and require coordination with future deliverables (orchestrator integration, design.md amendment, primary-source PDF access).
4. Per [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration", the 3-round cap is the operational ceiling. A second round on a remediation that introduced no new contradiction is process for its own sake.

## Residuals

**Closed by this loop:**
- H053 design.md §11.2 prereq 19 (power-calibration solver) — the parametric `required_n` + MDE inverter is now implemented and exercised by 33 tests.

**New follow-ups filed:**
- `P1-LO2002-EQ4-PRIMARY-VERIFY` (minor; primary-PDF verification)
- `P1-H053-KURTOSIS-CONVENTION-RECONCILE` (minor; pre-reg language consistency)
- `P1-H053-SIDECAR-PATH-DESIGN-MD-RECONCILE` (minor; design.md text)
- `P1-H053-POWER-SCHEMA-RECONCILE` (minor; design.md yaml block ↔ dataclass alignment)
- `P1-H053-POWER-REPRO-LOG-XREF` (minor; add `repro_log_run_id` at orchestrator integration)
- `P1-H053-POWER-TEST-RATIO-TIGHTEN` (minor; analytical-ratio assertion)
- `P1-H053-POWER-TEST-ASYMPTOTIC-TIGHTEN` (minor; asymptotic tolerance)
- `P1-H053-POWER-TEST-NONZERO-SKEW` (minor; option-1 reactivation coverage)

**Cycle 7 remaining deliverables (unchanged by this loop):**
- Feature factory under `src/skie_ninja/features/h053/{daily,hourly,microstructure_5_15min,mediator}.py`
- Archetype classifier per design.md §4.5.1
- PIT integration canaries (§11.2 prereq 11 sub-clause c — depends on feature factory)
- Stage-0 sanity: HKS 2010 half-hour-reversal sign on ES/NQ

## Verdict

**accept-with-remediation.** All critical and major findings remediated in-loop with regression tests; minor follow-ups filed. 33/33 power-solver tests green; 79/79 across H053 + clock + windowing suites. Ready for commit + push.
