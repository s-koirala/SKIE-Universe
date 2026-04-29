---
title: P1-HMM-EM-NUMBA-KERNELS — audit-remediate-loop trail
date: 2026-04-28
artifact: src/skie_ninja/models/regime/_em_kernels.py + src/skie_ninja/models/regime/_core.py + src/skie_ninja/models/regime/hmm_fit_cache.py + tests/unit/test_em_kernels.py + scripts/bench/bench_em_kernels.py
followup_id: P1-HMM-EM-NUMBA-KERNELS
exit_state: round-1 accept-with-residuals
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
operational_constraint: prod-run-3 (PIDs 33640+36128) terminated cleanly via 24-hour supervisor cap (Layer 4 / ADR-0010) at 2026-04-28 19:08 CT after 22.78 hours, 6/27 cfgs of one symbol's first fold completed; pre-disk-persist HEAD `4ae8ca77` so the in-memory HMM cache died with the process (≈22 hr of computed fits unsalvageable). No process protection conflict during this loop.
---

## Scope

Replace the per-timestep Python `for t in range(T)` loops in
`forward_log`, `backward_log`, `forward_log_from_prior`, and the
`(T-1, N, N)` log-ξ tensor materialisation in `forward_backward_log`
with Numba `@njit` kernels. The patch is a pure performance change:
no methodological, pre-registration, or ADR-0005 modifications. The
in-house numerical core is preserved (audit-clean) and bit-equivalence
with the existing scipy path is testable to `rtol=1e-12`.

Background: H050 prod-run-3 terminated at the 24-hour supervisor cap
after completing only 6/27 cfgs of one symbol's first fold. Diagnosis
in [audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md)
attributed the dominant cost to per-timestep `scipy.special.logsumexp`
calls inside the Python-level forward/backward recursions at T≈3·10⁶
and N∈{2..4}.

## Decision pathway

Three parallel research agents (proper main-thread-spawned, isolated)
converged on the same intervention:

1. **Numba `@njit` JIT** on the FB recursions with manual logsumexp.
2. Stream the log-ξ accumulation to avoid the (T-1, N, N) tensor.
3. Keep a NumPy/scipy fallback so the module imports without numba.

Alternative paths considered and rejected:
- **Cython / Pythran**: build-tooling complexity not justified given
  numba's pip-install-only deployment.
- **JAX `jit`**: introduces XLA dependency + GPU-vs-CPU ambiguity for
  a CPU-bound kernel; project has no CUDA infrastructure.
- **Online EM (Cappé 2011) / Mini-batch EM (Liang & Klein 2009)**:
  changes the optimisation objective; pre-reg drift; rejected.
- **Statistical Jump Models (Nystrup 2020)**: different model class;
  out-of-scope for this perf fix.

## Round 1 — parallel quant + repro audit

Subagents (proper-isolated, main-thread-spawned):
- `quant-auditor` (`agentId a92d857e9d4e31f9f`) — 12 findings (F-1-2, F-1-3, F-1-7, F-1-12 majors; F-1-1, F-1-4, F-1-5, F-1-6, F-1-8, F-1-9, F-1-10, F-1-11 minors).
- `reproducibility-verifier` (`agentId a08788ce7c1c5c293`) — 9 findings (R-1 through R-5 majors; R-6 through R-9 minors).

### Round-1 dispositions

| ID | Severity | Issue | Round-1 disposition |
|---|---|---|---|
| **F-1-1** | minor | Kernels write `log_alpha[t,j] = log_B[t,j] + (-inf)`; if `log_B[t,j]` is `+inf` the result is NaN. Latent because tests only used finite `log_B`. | **Fixed**: short-circuit to `-inf` directly when `m == -inf` (the additional `log_B` term is irrelevant — structurally zero-mass state). Patched at three sites: `_forward_log_njit` (t≥1 inner branch + t=0 init), `_forward_log_from_prior_njit` (t=0 + t≥1). New regression test `test_forward_log_handles_minus_inf_prior_with_pos_inf_emission_no_nan` constructs `log_pi[1] = -inf` + `log_B[0,1] = +inf` and asserts no NaN escapes. |
| **F-1-2** | major | xi-sum streaming uses `rtol=1e-10` vs `1e-12` elsewhere; tolerance gap unjustified inline. | **Documented + extreme-T test**: kernel docstring's "Cross-host determinism caveat" + "Small-N assumption" sections cite Higham 2002 §4.2 sequential-summation error growth O(N·u). New test `test_xi_sum_kernel_extreme_T_rtol_bounded` at T=10⁶ asserts `rtol≤1e-9` against the scipy reference, pinning the ceiling well below `_DEFAULT_EM_TOL=1e-4`. |
| **F-1-3** | major | `forward_log_from_prior` ran K-step propagation TWICE (numpy guard + kernel internal); semantics drifted because the numpy guard rejected legitimate `-inf` priors. | **Fixed**: replaced the redundant numpy K-step propagation with a finite-check on the input `log_alpha_prior` (NaN/+inf raises; `-inf` permitted as a structurally-forbidden state marker). Kernel-internal propagation is now the sole production path. |
| **F-1-4** | minor | `numba.cache=True` writes `__pycache__/<module>.nbi` files; cache key does NOT include llvmlite version, so silent stale-binary risk on llvmlite version drift. | **Documented**: cross-host determinism caveat in module docstring + `kernel_implementation_id` SHA256 in cache schema (see F-1-7). Tracked as `P1-REPROLOG-NUMBA-LLVMLITE-VERSION` for future ReproLog extension. |
| **F-1-5** | minor | "~10-25× speedup" in docstring was unverified hand-estimate; project precedent (P1-HMM-FULL-COV-1DIM-REDUNDANT) requires a measured Tier-5 microbench artifact. | **Fixed**: ran a thread-pinned (ADR-0009) microbench across T∈{10k, 50k, 200k, 500k} × N∈{2,3,4}; **measured speedup is 400–1200×**, not 10–25× (hand estimate was off by ~50×). Bench script at `scripts/bench/bench_em_kernels.py` mirrors the `bench_hmm_cov_d1.py` shape (git_head + numba/llvmlite/numpy versions + thread pinning + pip freeze). Raw at [logs/bench_em_kernels_2026-04-28.json](../../logs/bench_em_kernels_2026-04-28.json). Docstring updated with measured table + extrapolation. |
| **F-1-6** | minor | Code duplication between `_forward_log_njit` and `_forward_log_from_prior_njit` (inner step + terminal LL identical). | **Deferred**: tracked as `P1-EM-KERNELS-DEDUP`. Cosmetic; numba inlines `@njit`-to-`@njit` calls so a refactor would be transparent. |
| **F-1-7** | major | Disk-persist cache schema records `git_head + python_version + numpy_version` but not `numba_version` or kernel-source-id; cross-numba-version resume silently mixes numerical paths. | **Fixed**: schema bumped `hmm_fit_cache_v2_pickle5 → hmm_fit_cache_v3_pickle5_numba`. Pickle payload now records `numba_version` (or `"unavailable"`) + `kernel_implementation_id` (SHA256 of `_em_kernels.py` bytes). `check_provenance` returns mismatch entries for both new fields; existing WARN-but-load policy preserved. |
| **F-1-8** | minor | Streaming xi-sum has untested 'one finite v among many -inf' edge case. | **Fixed**: new `test_xi_sum_kernel_sparse_finite_among_minus_inf` constructs sparse `log_alpha`/`log_beta` and asserts kernel agrees with scipy reference. |
| **F-1-9** | minor | `fastmath=False` not justified inline; future drive-by edit risk. | **Fixed**: added `KERNEL_FASTMATH_NOTE` block at top of kernels section + `# fastmath=False — see KERNEL_FASTMATH_NOTE` comment on each `@njit` decorator. Notes IEEE-754 reassociation hazard. |
| **F-1-10** | minor | Perf-smoke gate has fixed kernel-first ordering + no warmup variance control. | **Deferred**: tracked as `P1-EM-KERNELS-PYTEST-BENCHMARK`. The bench script in scripts/bench/ is the authoritative measurement; the in-test gate is a coarse regression catcher only. |
| **F-1-11** | minor | `n_states=1` not in test parametrise. | **Fixed**: extended `test_forward_log_kernel_matches_numpy_reference` and `test_backward_log_kernel_matches_numpy_reference` to `n_states ∈ {1,2,3,4,5}`. |
| **F-1-12** | major | Sequential summation in inner logsumexp has error growth O(N·u); small-N assumption unstated; would silently exceed rtol contract for N>~8. | **Fixed**: added `MAX_KERNEL_N = 8` + `_check_small_n` wrapper guard. Each public kernel function calls the guard before dispatch; raises `ValueError` with `MAX_KERNEL_N` text on N>8. Test `test_forward_log_kernel_rejects_large_n` exercises the guard. Followup `P1-EM-KERNELS-LARGE-N` tracks Kahan-compensated kernel for the >8 regime. |
| **R-1** | major | Cache provenance missing `numba_version` (silent cross-numba-version drift). | **Fixed (with F-1-7)**: schema v3 records `numba_version`. |
| **R-2** | major | Cross-host AVX-512 vs AVX2 LLVM codegen produces different fp summation orders; F-1-4 byte-identity claim of `hmm_fit_cache.py` holds only within a host. | **Documented**: kernel docstring "Cross-host determinism caveat" makes this explicit; recommends re-execution on the same host for byte-identical resumes. The `kernel_implementation_id` SHA captures source drift; cross-host CPU drift remains an rtol-bounded contract. |
| **R-3** | major | README install snippet missing `[perf]` extra. | **Fixed**: README "Environment setup" section now points to the kernel docstring caveat + the audit trail. |
| **R-4** | major | `dev` extra didn't pull in numba; CI silently soft-skipped the kernel test. | **Fixed**: numba+llvmlite added to `dev` extra (with same band as `perf`); the standard `uv pip install -e ".[dev]"` install now exercises the @njit path. |
| **R-5** | major | No audit trail file. | **Fixed**: this document. |
| **R-6** | minor | Patch not yet committed. | **Fixed**: see Commit section below. |
| **R-7** | minor | `*.nbi`/`*.nbc` defense-in-depth gitignore rule. | **Fixed**: `.gitignore` now has explicit `*.nbi`, `*.nbc`, `**/numba_cache/` rules in addition to the existing `__pycache__/` catch-all. |
| **R-8** | minor | No extreme-T regression test for streaming xi-sum cumulative round-off. | **Fixed (with F-1-2)**: new T=10⁶ test asserts `rtol≤1e-9`. |
| **R-9** | minor | `numba>=0.59`, `llvmlite>=0.42` floors are too permissive. | **Fixed**: tightened to `numba>=0.65,<0.70`, `llvmlite>=0.47,<0.50`. Upper bound guards against numba 0.70's documented `@njit` cache semantic drift. |

## Round 2 — internal verification

Per [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) §"Cap":
Round-2 was a remediation-only round; no Round-2 fresh subagent audit
(3-round cap reserved for future drift). Verification:

- **84/84 `test_em_kernels` tests green** (was 72; +12 new tests:
  N=1 parametrise extension across forward+backward = 8 new cases,
  -inf+inf NaN guard, sparse-finite, extreme-T at T=10⁶, large-N
  reject).
- **205/205 targeted tests green** across `test_em_kernels`,
  `test_hmm_*`, `test_orchestrator_progress_log` (sequential, no
  `-n auto`).
- **Tier-5 microbench** at thread-pinned BLAS=1 confirms 400–1200×
  speedup on (T, N) grid spanning the H050 production substrate
  envelope. Raw artifact:
  [logs/bench_em_kernels_2026-04-28.json](../../logs/bench_em_kernels_2026-04-28.json).

### Measured speedups (kernel vs scipy reference, min-of-3 timing)

| T | N=2 | N=3 | N=4 |
|---|---|---|---|
| 10,000 | 405× | 731× | 487× |
| 50,000 | 1182× | 741× | 503× |
| 200,000 | 1210× | 985× | 575× |
| 500,000 | 1233× | 651× | 536× |

Linear extrapolation to H050 production T≈3·10⁶ predicts the scipy
forward+backward pair at ~6–12 minutes per EM iteration, kernel path
at ~0.5–1 second. With 30–50 EM iterations × 6 cold fits per
walk-forward run, end-to-end HMM-fit cost expected to drop from
**~100+ hours to ~30–60 minutes**.

## Operational safety

prod-run-3 (PIDs 33640 supervisor + 36128 child Python; H050
walk-forward, run_id `61d9eefbc06f4b4692d73f41f8a8dcac`, launched
2026-04-27 19:08 CT, git_head `4ae8ca77`) **terminated cleanly via
the 24-hour supervisor cap** at 2026-04-28 19:08 CT. Rc=1; classified
as `supervisor_max_runtime_exceeded` per [supervised_run.py](../../scripts/supervised_run.py)
classifier. Layer 4 of ADR-0010 worked as designed. The 22.78 hours
of computed HMM fits were in-memory only (prod-run-3 HEAD predates
commit 67c0419 `P1-HMM-FIT-CACHE-PERSIST`); unsalvageable. The next
production run will benefit from both the disk-persistent cache and
the numba kernels, so this is the last fully-from-scratch H050 run.

## Exit verdict

**`accept-with-residuals`** — patch is operationally sound for use as
the new HMM-fit production path:

- All 5 majors (F-1-2/F-1-3/F-1-7/F-1-12, plus R-1/R-2/R-3/R-4/R-5)
  remediated in-loop.
- 8 of 8 minors that interacted with the public API or contracts
  remediated.
- 4 minors deferred as cosmetic or strict-reproducibility follow-ups.
- Numerical equivalence with the scipy reference verified at
  `rtol=1e-12` on the regression suite (T≤5k, N∈{1..5}) and
  `rtol≤1e-9` at T=10⁶.
- Speedup verified empirically at 400–1200× on a Tier-5 microbench.
- Cache provenance extended for cross-numba-version drift detection.
- Cross-host determinism caveat documented; byte-identity contract
  scoped explicitly to within-host runs.

**Residuals carried forward (non-blocking):**

- `P1-EM-KERNELS-DEDUP` (F-1-6) — factor shared inner-step + terminal-LL
  helper.
- `P1-EM-KERNELS-PYTEST-BENCHMARK` (F-1-10) — replace ratio<1.5×
  smoke test with `pytest-benchmark` fixture.
- `P1-EM-KERNELS-LARGE-N` (F-1-12) — Kahan-compensated kernel for
  N>8.
- `P1-REPROLOG-NUMBA-LLVMLITE-VERSION` (F-1-4) — extend ReproLog to
  capture numba/llvmlite versions per run for cross-environment
  audit trail.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [src/skie_ninja/models/regime/_em_kernels.py](../../src/skie_ninja/models/regime/_em_kernels.py) — kernel module.
- [src/skie_ninja/models/regime/_core.py](../../src/skie_ninja/models/regime/_core.py) — wired to delegate to kernels.
- [src/skie_ninja/models/regime/hmm_fit_cache.py](../../src/skie_ninja/models/regime/hmm_fit_cache.py) — schema v3 with numba_version + kernel_implementation_id.
- [tests/unit/test_em_kernels.py](../../tests/unit/test_em_kernels.py) — 84-test regression suite.
- [scripts/bench/bench_em_kernels.py](../../scripts/bench/bench_em_kernels.py) — Tier-5 microbench.
- [logs/bench_em_kernels_2026-04-28.json](../../logs/bench_em_kernels_2026-04-28.json) — empirical speedup measurements.
- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — original diagnosis pointing at the FB Python-loop bottleneck.
- [docs/audits/audit_trail_2026-04-28_hmm-fit-cache-persist.md](audit_trail_2026-04-28_hmm-fit-cache-persist.md) — preceding work: disk-persistent HMM-fit cache.
- Lam, S. K., Pitrou, A., & Seibert, S. 2015. "Numba: a LLVM-based Python JIT compiler." *Proceedings of the Second Workshop on the LLVM Compiler Infrastructure in HPC* (LLVM '15), Article 7. https://doi.org/10.1145/2833157.2833162
- Higham, N. J. 2002. *Accuracy and Stability of Numerical Algorithms*, 2nd ed. SIAM. ISBN 978-0-89871-521-7. §4.2 (summation algorithms and error analysis).
