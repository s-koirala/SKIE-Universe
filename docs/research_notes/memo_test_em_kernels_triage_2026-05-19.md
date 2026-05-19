# Memo — `test_em_kernels.py` failure triage (2026-05-19)

**Phase**: O.18 (residual triage from Phase O.17 audit).

**Status**: closed — actual defect; symmetric F-1-1 guard remediation applied to the numpy-reference fallback paths.

## 1. Failure verbatim

`uv run pytest tests/unit/test_em_kernels.py -v` (numba unavailable in this dev environment per the `test_numba_available_in_test_env` skip):

```
tests/unit/test_em_kernels.py::test_forward_log_handles_minus_inf_prior_with_pos_inf_emission_no_nan FAILED
...
AssertionError: NaN leaked into log_alpha; first NaN at index [0 1]

C:\Users\skoir\Documents\SKIE-Universe\src\skie_ninja\models\regime\_em_kernels.py:477:
  RuntimeWarning: invalid value encountered in add
    log_alpha[0] = log_pi + log_B[0]

Test fixture:
  log_pi = [0.0, -np.inf]                  # state 1 forbidden by warm-start prior
  log_transmat = log(0.5*ones(2, 2))
  log_B = zeros((20, 2)); log_B[0, 1] = +np.inf

Expected: log_alpha[0, 1] == -np.inf  (per F-1-1 contract)
Actual:   log_alpha[0, 1] == np.nan
```

Deterministic — 3 of 3 standalone runs failed identically. Not flaky.

## 2. Classification

**Actual defect** — asymmetric F-1-1 guard between numba JIT path and numpy-reference fallback path.

## 3. Root-cause analysis

The test docstring explicitly cites the F-1-1 guard in `_forward_log_from_prior_njit` (numba path)
and asserts an "equivalent path" in `_forward_log_njit`. Inspection confirms:

- `_forward_log_njit` (line 145-191 of [src/skie_ninja/models/regime/_em_kernels.py](../../src/skie_ninja/models/regime/_em_kernels.py)) — **has** the F-1-1 guard at line 158-161 (`if log_pi[j] == -np.inf: log_alpha[0, j] = -np.inf`) and the t≥1 continuation guard at line 169-175.
- `_forward_log_numpy_reference` (line 470-483 pre-fix) — **does NOT** have the F-1-1 guard; line 477 used naive vectorised `log_alpha[0] = log_pi + log_B[0]` which produces `nan` under IEEE-754 `-inf + +inf` semantics.
- `_forward_log_from_prior_numpy_reference` (line 501-520 pre-fix) — same asymmetric gap (numba path has guard; numpy reference does not).
- `_backward_log_numpy_reference` (line 486-498 pre-fix) — same analogous gap on the backward recursion's RHS expression (`log_B[t+1, j] + log_beta[t+1, j]` can be `+inf + -inf` when state j is forbidden by the backward recursion and has degenerate +inf emission).

Origin commit: `341a94b` ("perf(hmm): P1-HMM-EM-NUMBA-KERNELS — numba @njit FB recursions; 400-1200x speedup"; 2026-04-28). The R1 audit-remediate-loop on that commit caught the NaN-guard requirement and applied it to the numba paths (the production hot path), but the numpy-reference paths (the fallback + the regression-test oracle) were not symmetrically patched. The defect surfaced now because:

1. The current dev environment has `numba` uninstalled (the perf extra is not active per `uv pip list | grep numba` empty result).
2. Module dispatch in `forward_log_kernel` (line 386-388) falls through to `_forward_log_numpy_reference` when `NUMBA_AVAILABLE = False`.
3. The test fixture exercises the precise `-inf + +inf` corner the asymmetric guard misses.

This is the same regression class flagged by `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` (silent-asymmetry drift across paired primitives); it is mechanical-not-conceptual.

## 4. Fix description

Three locations in [src/skie_ninja/models/regime/_em_kernels.py](../../src/skie_ninja/models/regime/_em_kernels.py):

1. `_forward_log_numpy_reference` — added `forbidden_t0 = np.isneginf(log_pi)` mask at t=0 with `np.where(forbidden_t0, -np.inf, log_pi + log_B[0])`; analogous mask in the t≥1 continuation. Wrapped both inside `np.errstate(invalid="ignore")` because numpy evaluates both branches of `np.where` eagerly, and the masked-away branch can produce the same `RuntimeWarning` even though the result is overwritten.

2. `_forward_log_from_prior_numpy_reference` — same pattern on `log_alpha_prop` (the propagated prior); mirrors the numba `_forward_log_from_prior_njit` guard at line 261-264.

3. `_backward_log_numpy_reference` — symmetric NaN guard on the RHS expression `log_transmat + log_B[t+1] + log_beta[t+1]`; identifies cells where `log_beta[t+1, j] == -inf` AND `log_B[t+1, j] == +inf` and masks them to `-inf` before the logsumexp. Mirrors the numba `_backward_log_njit` early-return at line 211-213.

All three fixes are bit-identical to the existing numpy-reference behaviour on **normal-path inputs** (no `-inf` priors, no `+inf` emissions). The 72 existing `*_matches_numpy_reference` parametric bit-equality tests at `rtol = 1e-12` continue to pass unchanged.

## 5. Downstream impact

**Limited to test environments without `numba`.** Production HMM fits used by H050 + H052a + H052b (per ADR-0005 + ADR-0006) use the numba path; this is confirmed by the `numba_version` provenance field in the HMM fit cache schema v3 ([src/skie_ninja/models/regime/hmm_fit_cache.py](../../src/skie_ninja/models/regime/hmm_fit_cache.py) line 204) which is captured into every cached fit. The numba path **already had** the F-1-1 guard at production hot-path layer.

No prior KPI report card (H050 v1/v2, H052a v1, H053 v3/v4, H055 v2, H060 v1/v2, H062 v1/v2/v3-smoke, H065 v1/v2) is impacted: all production walk-forward runs were executed with `numba` installed (verified via the `model_hash` SHA in their persisted `ReproLog` envelopes, which include the numba path's source SHA).

No retroactive re-run of any committed KPI report card is required.

## 6. Verification steps

```
# Failing test pre-fix
uv run pytest tests/unit/test_em_kernels.py::test_forward_log_handles_minus_inf_prior_with_pos_inf_emission_no_nan -v
# -> FAILED (deterministic 3/3 runs)

# Post-fix
uv run pytest tests/unit/test_em_kernels.py::test_forward_log_handles_minus_inf_prior_with_pos_inf_emission_no_nan -v
# -> PASSED (deterministic 3/3 runs)

# Full EM kernels suite
uv run pytest tests/unit/test_em_kernels.py
# -> 81 passed, 3 skipped (the 3 skips are numba-unavailable gates; unchanged)
# -> 0 warnings (RuntimeWarning suppressed via np.errstate context manager)

# Broader regime test suite — collateral damage check
uv run pytest tests/unit/test_hmm_core.py tests/unit/test_hmm_selection.py tests/unit/test_hmm_fit_cache.py tests/unit/test_em_kernels.py
# -> 141 passed, 3 skipped
```

All 72 normal-path bit-equality regression tests (`*_matches_numpy_reference` family) pass post-fix at the original `rtol = 1e-12` tolerance — confirming the F-1-1 guards introduce no numerical drift on the normal-path arithmetic.

## 7. Decision per ADR-0027 §D-3 (regression vs forward fix)

Choice: **forward fix in source** (NOT revert + NOT mark test as skip).

Rationale: the test is correct and the source-side asymmetric-guard defect is a real (not intentional) gap missed by the R1 audit of `341a94b`. Fixing the numpy-reference paths to match the numba paths is the symmetric remediation per the audit-remediate-loop skill convention; it preserves the test-as-evidence + closes the latent defect that would surface in any future dev environment without numba installed.

## 8. Follow-up registered

- `P1-EM-KERNELS-NUMPY-NUMBA-PARITY-AUDIT` (non-blocking): one-time audit sweep of `_em_kernels.py` to enumerate every pairing of `_njit` and `_numpy_reference` functions and assert their guard structure matches symmetrically. The Phase O.18 patch closes 3 asymmetric gaps; this follow-up registers the audit-discipline check to prevent regression of the same class.
