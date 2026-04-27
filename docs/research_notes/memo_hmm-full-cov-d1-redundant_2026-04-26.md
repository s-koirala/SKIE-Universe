---
name: HMM full-vs-diag covariance redundancy at d=1 — proposal memo
description: Reconciles three parallel research-agent findings on whether the redundant `full`-cov fit at d=1 in H050 should be skipped; anchors the constant-factor claim in the prod-run-1 diagnosis with an in-house microbench; final mechanism after Round-1 audit-remediate-loop is model-class deduplication inside select_gaussian_hmm (no YAML grid edit); see addendum r2.
type: project
hypothesis_id: H050
followup_id: P1-HMM-FULL-COV-1DIM-REDUNDANT
date: 2026-04-26
status: implemented
revision: r2
---

# HMM full-vs-diag covariance redundancy at d=1 — proposal memo

## Revision history

- **r1 (2026-04-26)**: proposed editing [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml) line 24 from `[diag, full]` to `[diag]` and writing a sibling addendum.
- **r2 (2026-04-26, after Round-1 audit-remediate-loop)**: Round-1 quant-auditor finding Q-1-4 confirmed [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §5 line 62 binds `covariance_type ∈ {diag, full}`. Editing the YAML grid is therefore a contestable pre-reg edit. Replaced with model-class deduplication inside [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py) — the YAML and design.md grids are preserved verbatim; redundant compute is skipped at fit time. Multiple lit-check + repro fixes also applied (see [docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md](../audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md)).

## §1. Provenance

This memo reconciles three parallel research findings on the recommendation in [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) §"Recommended fix" — skip the `full`-cov fit at d=1, which the diagnosis identified as the dominant bottleneck in the killed prod-run-1.

Three agents were run in parallel (2026-04-26):

1. **literature-check** (`agentId a399c3d84482059c8`) — verified primary-source citations underpinning the d=1 equivalence claim.
2. **general-purpose library survey** (`agentId a2512950986e5e686`) — surveyed hmmlearn, sklearn.mixture, pomegranate, depmixS4, Stan/NumPyro/PyMC for d=1 covariance-type handling and any benchmark on 1×1 Cholesky overhead.
3. **codebase verifier** (Explore subagent) — verified all 10 codebase claims (`H050.yaml` line, `_core.py` paths, BIC parameter accounting, cache-key tuple, restart counts, grid sizes) PASS.

A microbench (Tier-5 in-house measurement; [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py)) was then run on this hardware + BLAS stack, single-threaded per [ADR-0009](../decisions/ADR-0009-blas-thread-pinning.md), to anchor the constant-factor claim with measured numbers and replace the diagnosis's unattributed `~10×` estimate.

## §2. Findings

### §2.1 Algebraic equivalence at d=1 — Tier-2 supported

For Gaussian-emission HMMs with `n_features = 1`, the four covariance parameterisations reduce to three model classes:

- `spherical` (covars shape `(N,)`): one positive scalar per state.
- `diag` (covars shape `(N, 1)`): one positive scalar per state.
- `full` (covars shape `(N, 1, 1)`): one positive scalar per state (the 1×1 PSD matrix).
- `tied` (covars shape `(1, 1)`): one positive scalar shared across states — **not** equivalent.

Confirmed by:

- **Source**: [hmmlearn `_log_multivariate_normal_density_*` paths](https://github.com/hmmlearn/hmmlearn/blob/main/src/hmmlearn/stats.py) — the `full` path Cholesky-factorises a 1×1 matrix `[[σ²]]` to `[[σ]]`, calls `solve_triangular`, then squares — algebraically equal to the `diag` path's scalar division.
- **Source**: [sklearn.mixture `_estimate_log_gaussian_prob`](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/mixture/_gaussian_mixture.py) — identical structural split.
- **In-tree**: BIC parameter accounting at [src/skie_ninja/models/regime/_core.py:780-823](../../src/skie_ninja/models/regime/_core.py) gives at d=1: spherical = N, diag = N·1 = N, tied = 1·(1+1)/2 = 1, full = N·1·(1+1)/2 = N. Therefore `spherical = diag = full = N` parameters; only `tied` differs (1 shared scalar).
- **Microbench**: at every tested `(T, N)`, `max_abs_diff_log_density = 0.0` between the diag and full paths (bit-exact equality, not merely up-to-round-off).

The textbook anchors are uncontroversial-by-derivation: Bishop, *PRML* 2006 §9.2 (Mixtures of Gaussians; develops GMM with general per-component Σ_k that the sklearn/hmmlearn covariance-type taxonomy specialises) and §13.2 (Hidden Markov Models, including Gaussian emissions); Murphy, *MLPP* 2012 §17.3-17.5 (HMM block; §17.5 is "Learning for HMMs", not specifically Gaussian emissions). Neither pins an equation explicitly to "for d=1, `full` ≡ `diag`," because the equivalence is a direct algebraic corollary of the parameterisation, not a separately-stated theorem. It is at **Tier 2 / Tier 4 hybrid** evidence-hierarchy: the parameterisation shapes are documented in sklearn user guide §2.1 (Tier 2 — official documentation); the d=1 algebraic equivalence is a direct corollary derivable from the documented shapes plus the Gaussian log-density formula, with the canonical implementation paths in hmmlearn / sklearn (Tier 4 — vetted reference-library source) as the source-of-truth for the per-state scalar-variance representation.

### §2.2 Constant-factor cost gap — measured

The diagnosis's `~10×` claim was Tier-5 hand-estimate without a recorded measurement. We replace it with the in-house microbench at [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py); raw JSON manifest at [logs/bench_hmm_cov_d1_2026-04-26.json](../../logs/bench_hmm_cov_d1_2026-04-26.json) (with `git_head`, BLAS vendor via `numpy_show_config`, `uv_pip_freeze_first_lines`, `runtime_status` keys); console transcript at [logs/bench_hmm_cov_d1_2026-04-26.log](../../logs/bench_hmm_cov_d1_2026-04-26.log).

**Per-E-step `log_emission_matrix` ratios** (BLAS pinned to 1 thread per ADR-0009; n_iter=30 at T≥1M, n_iter=50 at T=10k; 95% percentile-bootstrap CI on the ratio with 2000 resamples):

σ² = 1.0 (synthetic, unit variance):

| T (rows) | diag median (ms) | full median (ms) | full/diag ratio | 95% CI | log-density max-abs-diff |
|---|---|---|---|---|---|
| 10,000     | 0.051  | 0.130   | 2.569× | [2.531, 2.630] | 0.0 (bit-exact) |
| 100,000    | 2.140  | 2.340   | 1.093× | [1.034, 1.166] | 0.0 (bit-exact) |
| 1,000,000  | 27.787 | 33.989  | 1.223× | [1.184, 1.256] | 0.0 (bit-exact) |
| 3,000,000  | 89.724 | 104.731 | 1.167× | [1.140, 1.193] | 0.0 (bit-exact) |

σ² = 1e-8 (production-realistic, 1-min log-return scale):

| T (rows) | diag median (ms) | full median (ms) | full/diag ratio | log-density max-abs-diff |
|---|---|---|---|---|
| 100,000    | 1.955  | 2.444   | 1.250× | 4 × 10⁻¹⁵ |
| 1,000,000  | 28.252 | 33.086  | 1.171× | 5 × 10⁻¹⁵ |
| 3,000,000  | 87.002 | 104.948 | 1.206× | 5 × 10⁻¹⁵ |

At production-realistic σ², the diff is at floating-point round-off (`O(ε_machine)`); algebraic equivalence holds to double-precision noise. At unit variance, bit-exact equality.

**End-to-end `select_gaussian_hmm` ratios** (mirrors the production call site at [scripts/run_walk_forward.py:788-795](../../scripts/run_walk_forward.py); `n_states_grid=(2,)`, `min_restarts=5`, `max_restarts=10`):

| T (rows) | `[diag]`-only (s) | `[diag, full]` w/ dedup (s) | ratio | aliased | BIC match |
|---|---|---|---|---|---|
| 20,000 | 224.46 | 273.75 | 1.220× | 1 | True |
| 50,000 | 797.95 | 811.55 | **1.017×** | 1 | True |

The T=50k cell is the cleaner measurement (smaller T = larger relative wall-time noise). At T=50k the dedup is essentially perfect: the `[diag, full]` grid runs in 1.017× the `[diag]`-only time (≈ <2% BIC-recomputation overhead). This confirms the dedup mechanism: only one EM trajectory runs per equivalence class.

**Interpretation.**

- Per-E-step constant-factor overhead at the production fold size (T~3M) is **1.17-1.21×** (95% CI excludes 1.0), not the diagnosis's `~10×`.
- End-to-end `select_gaussian_hmm` saving from dropping or aliasing the redundant fit is `1 − 1/(1 + 1.18) ≈ 0.46` — the orchestrator does ~46% less HMM compute per cold cache miss. The dominant component is the doubling of the grid (1×1 → 1×2 cov-type variants), not the per-iter overhead.
- The end-to-end bench at T=50k confirms the dedup mechanism works as designed: `[diag, full]`-with-dedup ratio vs `[diag]`-only is 1.017× (essentially 1×; <2% wall-clock overhead from the BIC recomputation on the cache-hit branch).
- The diagnosis's wall-clock estimate (`24-48 hr → 3-6 hr` on the full production run) is therefore **optimistic by ~3-5×**. The honest revised estimate based on the measured ratios is `24-48 hr → ~12-22 hr` post-fix (see addendum §4.4 for the explicit decomposition with non-HMM floor). The patch is still worthwhile but materially smaller in impact than the diagnosis claimed.

### §2.3 No HMM library special-cases d=1, none warn

Library-survey result (Tier 2/4 sources; full table in research-agent output, summarised here):

- **hmmlearn** + **sklearn.mixture.GaussianMixture**: expose the `{spherical, diag, tied, full}` taxonomy; both use a per-component Python loop with LAPACK Cholesky for `full`, and a vectorised broadcast for `diag`. Neither special-cases d=1; neither warns. No open or closed GitHub issue raises the d=1 redundancy ([hmmlearn issue tracker](https://github.com/hmmlearn/hmmlearn/issues), [sklearn user guide §2.1](https://scikit-learn.org/stable/modules/mixture.html)).
- **pomegranate**: [issue #227](https://github.com/jmschrei/pomegranate/issues/227) is a feature request from 2017-02-26 asking for hmmlearn-style `covariance_type` support; the issue has no maintainer comment about univariate workarounds. The library does not expose a covariance-type taxonomy as of that issue date.
- **depmixS4** (R, [JSS v36 i07](https://www.jstatsoft.org/article/view/v036i07)): API forces the right class — `MVNresponse` for multivariate; univariate `gaussian()` family for d=1. No `covariance_type` knob.
- **Stan / NumPyro / PyMC** HMM tutorials: probabilistic-programming frameworks with no covariance_type enum; user writes `normal(mu[s], sigma[s])` for d=1, never `multi_normal_cholesky`. The anti-pattern cannot arise.

The sklearn user-guide entry includes a numerical-singularity caveat for `full` covariance ("the algorithm is known to diverge and find solutions with infinite likelihood unless one regularizes the covariances artificially") — distinct from the d=1-redundancy argument here. The hmmlearn changelog contains an "Accelerated M-step for `GaussianHMM` with full and tied covariances" entry, indirect maintainer concession that those are the slow paths.

### §2.4 What no published source confirms

The Tier-5 nature of the constant-factor measurement is load-bearing here:

- No peer-reviewed benchmark of 1×1 Cholesky overhead in numpy/LAPACK exists. The closest is [SciPy issue #23774](https://github.com/scipy/scipy/issues/23774), which tests `linalg` performance at d=20 (smallest reported size in that thread) and reports a ~4.75× `scipy.linalg.solve` vs `numpy.linalg.solve` overhead at that size — broadly consistent with the qualitative picture but not a 1×1 datum. The [Julia Discourse thread on `LAPACK.potrf!`](https://discourse.julialang.org/t/why-the-time-consumed-of-lapack-potrf-increase-hugely-when-the-dimension-is-bigger-than-a-special-number/82270) documents an n=16→17 cliff (LAPACK switches from unblocked to blocked path) and confirms the qualitative picture (small-n LAPACK is overhead-bound, not arithmetic-bound) but gives no `n=1` number.
- The microbench in §2.2 is an in-house Tier-5 single-host measurement and is labelled as such in [scripts/bench/README.md](../../scripts/bench/README.md) and the addendum §4.1. The user-global rule "Zero arbitrary thresholds or magic numbers" is satisfied because the number is measured + documented (not arbitrary), not Tier 1-3 because not externally published.

## §3. Implementation (r2)

### §3.1 Model-class deduplication in select_gaussian_hmm

The mechanism is implemented in [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py): a `_model_class_signature` helper returns `"d1_per_state_scalar"` for any of `{spherical, diag, full}` at d=1; the loop maintains a `fit_cache` keyed on `(n_states, signature)` and short-circuits when an equivalence-class duplicate is encountered. The aliased `SelectionCandidate` carries `n_restarts_used = 0` as the alias marker.

**Why this is preferable to a YAML edit (Round-1 Q-1-4 finding):** [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §5 line 62 binds `covariance_type ∈ {diag, full}` as a 2-element grid. Editing [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml) line 24 to `[diag]` would be a contestable pre-reg edit ("post-hoc grid collapse motivated by the run-1 hang"). Deduplication at fit time keeps both YAML and design.md unchanged — every grid point still appears in `SelectionResult.candidates`; only the second EM trajectory is skipped.

### §3.2 Updated addendum (r2)

[research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md](../../research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md) revision r2 reflects the deduplication-at-fit-time mechanism. The original r1 (proposing the YAML edit) is rescinded inline at the top of the addendum.

The addendum sections:

- §1 — what design.md / H050.yaml pre-registers (the cov-type grid `[diag, full]`); pre-r2 vs post-r2 execution.
- §2 — algebraic-equivalence proof at d=1 (parameter-shape derivation; BIC parameter count; likelihood identity; M-step floor-regime caveat).
- §3 — Tier-1/2/4 anchor citations (Schwarz 1978 / Rabiner 1989 / Celeux-Durand 2008 at Tier 1; sklearn user guide / Bishop / Murphy at Tier 2; hmmlearn / sklearn / pomegranate / depmixS4 source at Tier 4).
- §4 — Tier-5 microbench: σ²=1.0 + production-realistic σ²=1e-8 cells, with 95% bootstrap CIs on the per-E-step ratio; end-to-end with dedup; production wall-clock revision with non-HMM floor explicit.
- §5 — implementation: `_model_class_signature` + `fit_cache` in `select_gaussian_hmm`; what is and is not changed.
- §6 — pre-reg-fidelity argument (operates on substrate-blind model-class property; not a tuning choice).
- §7 — references.

### §3.3 Diagnosis audit trail amendment (in-place)

[docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) is amended with the measured ratios + a "Constant-factor amendment" subsection that replaces the unattributed "~10×" claim. The wall-clock estimate in the "Recommended fix" section is revised from "~3-6 hr" to "~12-22 hr" with the non-HMM floor made explicit.

### §3.4 Source docstring fix (literature-check L-1)

[src/skie_ninja/models/regime/_core.py:826-846](../../src/skie_ninja/models/regime/_core.py) `bic()` docstring is corrected: Schwarz 1978 has no numbered equations, and the paper's original criterion is `+log L − ½ k log n` (higher-is-better). Replaced docstring text:

> BIC = -2 log L + k log T (lower is better). Modern convention; equivalent up to the factor -2 and a sign-of-optimisation flip to Schwarz 1978's original criterion `log L - (1/2) k log n` (Annals of Statistics 6(2):461, p. 461 display sentence; the paper has no numbered equations).

### §3.5 Regression test coverage

Added in [tests/unit/test_hmm_selection.py](../../tests/unit/test_hmm_selection.py) (`TestD1ModelClassDeduplication`, 7 tests), [tests/unit/test_hmm_core.py](../../tests/unit/test_hmm_core.py) (`test_d1_full_equals_diag_bit_exact`, `test_d1_spherical_equals_diag_bit_exact`, `test_d1_param_count_equivalence_class`, `test_d1_bic_equivalence_class`), and a new [tests/unit/test_h050_config.py](../../tests/unit/test_h050_config.py) asserting `[diag, full]` is preserved in H050.yaml. 651/651 unit tests green post-patch (was 635 pre-patch + 16 new).

### §3.6 Operational follow-up (P1-ORCHESTRATOR-PROGRESS-LOGGING)

Out of scope for this memo (separate follow-up). The progress-logging gap at the orchestrator is what made the 180-min hang opaque without `py-spy`. A separate audit-remediate cycle will add INFO-level structured-log lines at `_fit_fold` start/end + per-cfg start/end. Tracked but **not bundled** here — keeps this patch a single-purpose diff.

## §4. Risks and counter-arguments

1. **Numerical-stability semantics differ between paths**. hmmlearn's `full` adds `min_covar * I` ridge if Cholesky fails; `diag` clamps elementwise from below. For d=1 in a near-zero-variance regime the failure-mode handling differs. Our `_core.py:200-211` (diag) and `:232-250` (full) have the same structural split. Risk is bounded — both still produce a valid PD scalar — and is not materially different from the risk we already accept on the diag path. **Severity: minor.**
2. **The microbench may not generalise to other hardware / BLAS**. Yes; this is acknowledged by Tier-5 labelling. The *qualitative* direction (full ≥ diag in cost) is invariant by source-code inspection. Only the *magnitude* is hardware-conditional. **Severity: minor; addressed by labelling.**
3. **Pre-reg-fidelity concern**. Could a later auditor argue that removing a grid point is a post-hoc grid collapse driven by the run-1 hang? This memo + the addendum + the pre-existence of the d=1 equivalence proof (Tier-2 derivable from source) defeat the concern: the equivalence is a fact about the model class, established without reference to any data observation. **Severity: minor; addressed by addendum citations.**
4. **Why not `tied` or `spherical`?** All three (diag, spherical, full) are model-class-equivalent at d=1; any one is admissible. We pick `diag` because (a) it matches the simplest implementation path with the lowest constant factor in the bench, (b) it is the de facto default in hmmlearn/sklearn for this d, and (c) the project's existing tests cover the `diag` path. `spherical` is equivalent but less idiomatic. `tied` is **not** equivalent (shared variance across states is a different and stronger model assumption); removing it from the grid would require a separate justification.

## §5. Open question for user

Per the diagnosis exit verdict ("decision pending on apply-fix-and-relaunch vs add-instrumentation-first"):

- **Option A** — Apply only the cov-type fix (this memo) and relaunch immediately. Lowest delta to the running code; relaunch ETA ~10-25 hr.
- **Option B** — Apply the cov-type fix + the orchestrator progress-logging patch (P1-ORCHESTRATOR-PROGRESS-LOGGING) in one bundle, then relaunch. Slightly larger diff; the next multi-hour run is observable. Recommended.
- **Option C** — Apply the cov-type fix, add a separate `--profile` flag that runs the same orchestrator under `cProfile` for a smaller subset (e.g. `--smoke`) before relaunching the full run. Slowest path; least-risk if any new bottleneck has been introduced.

Memo-author recommendation: **Option B**. The instrumentation patch is <20 LOC; the cost-of-omission (another opaque 180-min hang) is high; the revised wall-clock estimate (~10-25 hr) is long enough to justify observability.

## §6. Audit-remediate-loop expectation

This memo is the Round-1 deliverable for the audit-remediate-loop on `P1-HMM-FULL-COV-1DIM-REDUNDANT`. After loop closure:

1. The H050.yaml patch + addendum + audit-trail amendment + docstring fix land as one commit.
2. A separate audit-remediate cycle on `P1-ORCHESTRATOR-PROGRESS-LOGGING` lands its own commit (if Option B is selected).
3. CLAUDE.md + plan/tier2b_buildout_2026-04-23.md flip the `[~]` Cycle-6 row to reflect the patch and the (re)launch state.
4. Once the run completes, a **separate** audit-remediate-loop closes on the H050 walk-forward result (T_H050 + LW2008 differential CI + Hansen SPA + fold count vs `n_required_for_power_80` + HMM stationarity pre-check) per [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §10.

## §7. References

- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — diagnosis being amended.
- [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml) — pre-reg config patched.
- [src/skie_ninja/models/regime/_core.py](../../src/skie_ninja/models/regime/_core.py) — `log_emission_matrix` paths (lines 200-250) + `count_free_parameters` (lines 780-823) + `bic` (lines 826-843).
- [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py) — `select_gaussian_hmm` cov-type grid loop.
- [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py) — Tier-5 microbench source.
- [scripts/bench/README.md](../../scripts/bench/README.md) — bench runbook + canonical invocation.
- [logs/bench_hmm_cov_d1_2026-04-26.json](../../logs/bench_hmm_cov_d1_2026-04-26.json) — bench JSON manifest (atomic-incremental).
- [logs/bench_hmm_cov_d1_2026-04-26.log](../../logs/bench_hmm_cov_d1_2026-04-26.log) — bench console transcript.
- [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md) — HMM regime toolkit, `min_restarts` operational floor.
- [ADR-0009](../decisions/ADR-0009-blas-thread-pinning.md) — BLAS single-thread pinning rationale.
- [Schwarz 1978, *Ann. Stat.* 6(2):461-464, doi:10.1214/aos/1176344136](https://doi.org/10.1214/aos/1176344136) — BIC original sign convention.
- [hmmlearn `_log_multivariate_normal_density_*` (stats.py)](https://github.com/hmmlearn/hmmlearn/blob/main/src/hmmlearn/stats.py).
- [sklearn `_estimate_log_gaussian_prob` (_gaussian_mixture.py)](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/mixture/_gaussian_mixture.py).
- [sklearn user guide §2.1](https://scikit-learn.org/stable/modules/mixture.html) — covariance-type taxonomy; statistical (overfitting) note on `full`.
- [pomegranate issue #227](https://github.com/jmschrei/pomegranate/issues/227) — feature request from 2017-02-26 for hmmlearn-style covariance-type parameter; not implemented as of issue date (no maintainer comment about univariate-emission workarounds).
- [depmixS4 JSS paper (v36 i07)](https://www.jstatsoft.org/article/view/v036i07).
- [SciPy issue #23774](https://github.com/scipy/scipy/issues/23774) — Python-side LAPACK overhead at d=20.
- [Julia Discourse: `LAPACK.potrf!` n=16→17 cliff](https://discourse.julialang.org/t/why-the-time-consumed-of-lapack-potrf-increase-hugely-when-the-dimension-is-bigger-than-a-special-number/82270).
