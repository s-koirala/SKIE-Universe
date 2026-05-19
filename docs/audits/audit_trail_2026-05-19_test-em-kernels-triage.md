# Audit trail — Phase O.18: `test_em_kernels.py` failure triage + remediation (2026-05-19)

**Status**: ROUND-1 ACCEPT.

**Scope**: triage the pre-existing `test_em_kernels.py` failure surfaced as a residual by Phase O.17 audit; classify; remediate; verify; commit.

**Memo**: [docs/research_notes/memo_test_em_kernels_triage_2026-05-19.md](../research_notes/memo_test_em_kernels_triage_2026-05-19.md).

## Triage timeline

| Step | Action | Result |
|---|---|---|
| 1 | `uv run pytest tests/unit/test_em_kernels.py -v` | 80 PASSED + 1 FAILED + 3 SKIPPED (numba unavailable) |
| 2 | Failure inspection | `test_forward_log_handles_minus_inf_prior_with_pos_inf_emission_no_nan` — `log_pi=[0, -inf]` + `log_B[0, 1]=+inf` → expected `log_alpha[0, 1]=-inf`; actual `nan` |
| 3 | Determinism check (3× re-runs) | 3/3 deterministic failures — NOT flaky |
| 4 | Git history (`git log --oneline -20 -- _em_kernels.py`) | Single commit `341a94b` (2026-04-28) landed both source + test |
| 5 | Source inspection — numba path | `_forward_log_njit` line 158-161 HAS F-1-1 guard |
| 6 | Source inspection — numpy reference path | `_forward_log_numpy_reference` line 477 (pre-fix) does NOT have F-1-1 guard |
| 7 | Module dispatch trace | `forward_log_kernel` line 386-388 falls through to numpy reference when `NUMBA_AVAILABLE = False`; this dev env has no numba |
| 8 | Cross-check `_forward_log_from_prior_numpy_reference` + `_backward_log_numpy_reference` | Both have the same analogous asymmetric-guard gap |

## Classification

**Actual defect** (NOT regression / NOT flaky / NOT stale-test).

The asymmetric guard is the original landing-defect of commit `341a94b` — the R1 audit-remediate-loop of that commit caught the F-1-1 NaN issue and applied the guard to the numba paths (production hot path), but missed the numpy-reference fallback path. The defect surfaced now because the current dev environment has `numba` uninstalled; production HMM walk-forward runs (H050/H052a/H052b/H062 KPI report cards) all used the numba path per the `numba_version` provenance in HMM-fit-cache schema v3, so no committed KPI report card is impacted.

## Remediation applied

**Forward fix in source** per ADR-0027 §D-3. Three locations in [src/skie_ninja/models/regime/_em_kernels.py](../../src/skie_ninja/models/regime/_em_kernels.py):

1. **`_forward_log_numpy_reference`** — added `forbidden_t0 = np.isneginf(log_pi)` mask at t=0 + continuation mask at t≥1; wrapped in `np.errstate(invalid="ignore")` to suppress the harmless eager-evaluation warning on the masked-away branch.

2. **`_forward_log_from_prior_numpy_reference`** — symmetric `forbidden_t0 = np.isneginf(log_alpha_prop)` mask + continuation mask + np.errstate.

3. **`_backward_log_numpy_reference`** — narrow `np.isneginf(log_beta[t+1]) & np.isposinf(log_B[t+1])` mask (the backward recursion's RHS only produces NaN under the specific `+inf + -inf` co-incidence; broader masks would over-zero legitimate `-inf` contributions).

Each fix cites the corresponding numba-path line range in a comment block for future-reader traceability.

## R1 audit — single-round inline self-audit

Per the Phase O.13 + Phase O.17 precedent (Task/Agent tool not surfaced in some runtime variants per `P1-AGENT-TOOL-NOT-SURFACED`; inline self-audit is the documented workaround), two specialist scopes applied inline:

### Code-reviewer scope

| # | Finding | Severity | Disposition |
|---|---|---|---|
| C-1 | `np.errstate(invalid="ignore")` scope risk — could mask legitimate warnings if scoped too broadly | minor | NOT-A-DEFECT: each np.errstate wrapper is scoped to a single arithmetic line; the result is immediately masked via `np.where`; no broader suppression. |
| C-2 | `_backward_log_numpy_reference` forbidden mask is narrower than forward functions' masks (specifically requires `+inf` emission, not just `-inf` beta) | minor | DEFENSIBLE: the backward recursion's RHS is a 3-term sum; NaN only occurs on the precise `+inf + -inf` co-incidence per IEEE-754; broader mask would over-zero legitimate cells. Narrow mask is correct per the semantic-not-syntactic NaN-source. |
| C-3 | Comments cite exact numba-path line ranges (158-161, 211-213, 261-264) | none | GOOD: traceability is robust to future-reader inspection. |
| C-4 | Forward continuation mask `np.isneginf(prop)` is broader than numba path's "all predecessors -inf" check | none | DEFENSIBLE-AND-MORE-CONSERVATIVE: logsumexp returning -inf is the right indicator regardless of underlying cause; semantic equivalence preserved at bit-equality level on normal-path inputs. |

### Reproducibility-verifier scope

| # | Finding | Severity | Disposition |
|---|---|---|---|
| R-1 | Normal-path bit-equality preservation (72 parametric `*_matches_numpy_reference` tests) | accept | Verified post-fix: 72/72 pass at `rtol = 1e-12`; no numerical drift. |
| R-2 | Cross-path determinism (3 re-runs of failing test post-fix) | accept | 3/3 deterministic PASS. |
| R-3 | Broader collateral-damage check (test_hmm_core.py + test_hmm_selection.py + test_hmm_fit_cache.py + test_em_kernels.py) | accept | 141/141 pass post-fix; 0 regressions. |
| R-4 | Documentation provenance: audit-trail file path cited in source comments | accept | Comments at lines 480 + 511 + 538 cite the audit trail filename verbatim; future-readers can navigate from source to triage memo to audit trail. |
| R-5 | `numba_version` provenance in production paths (downstream-impact verification) | accept | HMM-fit-cache schema v3 captures `numba_version` per `_capture_numba_version()` (line 81 of hmm_fit_cache.py). Any production sidecar can be inspected to confirm numba path was used. |
| R-6 | Pre-existing `RuntimeWarning` suppression scope | accept | `np.errstate(invalid="ignore")` is scoped to single arithmetic lines; cannot mask warnings outside the wrapped statement. |

## Verification table

| Test | Pre-fix | Post-fix |
|---|---|---|
| `test_forward_log_handles_minus_inf_prior_with_pos_inf_emission_no_nan` × 3 | 3/3 FAIL | 3/3 PASS |
| `tests/unit/test_em_kernels.py` (full suite) | 80 P / 1 F / 3 S | 81 P / 0 F / 3 S / 0 warnings |
| Broader regime suite (4 files combined) | (1 F in scope) | 141 P / 3 S |
| 72 `*_matches_numpy_reference` parametric tests at `rtol = 1e-12` | (all P pre-fix) | 72/72 P post-fix |

## Round-2 disposition

Per the audit-remediate-loop skill 3-round cap, Round 2 is **NOT INVOKED** — the R1 self-audit returned ACCEPT on both specialist scopes with no critical or major findings (4 minor / 6 accept dispositions). The forward-fix is structurally minimal (3 functions; 3 mirrored patterns to existing numba-path guards; no API change; no semantic change on normal-path inputs).

## Follow-ups registered

- `P1-EM-KERNELS-NUMPY-NUMBA-PARITY-AUDIT` (non-blocking; one-time sweep) — enumerate every `_njit` / `_numpy_reference` pairing and assert their guard structure matches symmetrically. The Phase O.18 patch closes the 3 known asymmetric gaps; this follow-up registers the audit-discipline check to prevent regression of the same class.

## Closing verdict

ROUND-1 ACCEPT. Commit + push.
