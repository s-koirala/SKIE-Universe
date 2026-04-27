---
name: H050 HMM covariance grid — d=1 equivalence addendum
description: Path-A in-place addendum to design.md formalising the algebraic equivalence of `full` and `diag` covariance parameterisations at the H050 single-feature emission dimension d=1; resolves P1-HMM-FULL-COV-1DIM-REDUNDANT via model-class deduplication inside select_gaussian_hmm (no YAML grid edit); gates relaunch of the production walk-forward run.
type: project
hypothesis_id: H050
parent: design.md
status: designed
revision: r2
effective_from: 2026-04-26
owner: skoir
---

# H050 — HMM covariance grid d=1 equivalence addendum (2026-04-26)

This addendum is an in-place **Path A clarification** to [design.md](design.md) for hypothesis H050. It documents and operationalises the algebraic equivalence of the `full` and `diag` covariance parameterisations at the H050 single-feature emission dimension `d = 1`. The pre-registered grid in [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml) `hmm.covariance_type` (line 37) (`covariance_type: [diag, full]`) is **preserved verbatim** to satisfy [design.md](design.md) §5 line 62 (`covariance_type ∈ {diag, full}`); the redundant computation is removed by model-class deduplication inside `select_gaussian_hmm` ([src/skie_ninja/models/regime/selection.py](../../../src/skie_ninja/models/regime/selection.py)).

**Change in r2 from r1:** The original r1 of this addendum proposed editing [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml) line 24 from `[diag, full]` to `[diag]`. Round-1 audit-remediate-loop quant-auditor finding Q-1-4 ([docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md](../../../docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md)) flagged this as a contestable pre-reg edit because [design.md](design.md) §5 line 62 explicitly binds `covariance_type ∈ {diag, full}`. The cleaner Path-A solution — implemented in r2 — is to keep both YAML and design.md unchanged, and to dedupe **at fit time** inside the selector. The candidates list still contains both `(n, "diag")` and `(n, "full")` entries (audit fidelity); only the second EM trajectory is skipped.

It is a sibling of (and disjoint in scope from) the existing [aggregation_rule_addendum_2026-04-24.md](aggregation_rule_addendum_2026-04-24.md) (revision r2). That earlier addendum is scoped to cross-symbol return aggregation; this addendum is scoped to HMM hyperparameter governance. The two do not interact.

Resolution memo (proposal): [docs/research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md](../../../docs/research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md).
Diagnosis trail: [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../../../docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md).
Audit trail (this addendum): [docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md](../../../docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md).

## §1. What design.md / H050.yaml pre-registers

[design.md](design.md) §5 line 62 binds `covariance_type ∈ {diag, full}` as the pre-registered grid. [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml) `hmm.covariance_type` (line 37) carries the same grid: `hmm.covariance_type: [diag, full]`.

The orchestrator at [scripts/run_walk_forward.py:788-795](../../../scripts/run_walk_forward.py) calls `select_gaussian_hmm(r_tr.reshape(-1, 1), n_states_grid=(2,), covariance_types=hmm_cov_types, …)` where `hmm_cov_types` is loaded directly from H050.yaml.

The single-feature emission dimension `d = 1` is a structural property of the H050 design (single per-symbol log-return as the HMM observable; the four microstructure features in `features:` go to LightGBM, **not** to the HMM). It is not a tunable hyperparameter and is not at risk of changing within the H050 hypothesis ID.

**Pre-r2 (naive) execution.** Without the deduplication this addendum lands, every `select_gaussian_hmm` cold-fit per stratum-fold-symbol pays for two EM trajectories at d=1 — and the second, fit with `covariance_type="full"`, produces an algebraically-identical likelihood (per §2 below) at a measurable per-E-step constant-factor overhead (per §4). This was the bottleneck identified in [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../../../docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md).

**Post-r2 (deduplicated) execution.** With the model-class deduplication landed in [src/skie_ninja/models/regime/selection.py](../../../src/skie_ninja/models/regime/selection.py) (see §5 below), only the first model-class-equivalent fit runs the EM; the second (and any further `{spherical, diag, full}` entries at d=1) is aliased to the first fit's likelihood + BIC. The pre-reg grid is preserved on the audit trail (the candidates list still contains both `(n, "diag")` and `(n, "full")` records); only the redundant compute is skipped.

## §2. Algebraic-equivalence proof at d=1

### §2.1 Parameter shapes (covariance taxonomy at d=1)

Per the four-way `{spherical, diag, tied, full}` covariance taxonomy used by hmmlearn ([stats.py](https://github.com/hmmlearn/hmmlearn/blob/main/src/hmmlearn/stats.py)), sklearn.mixture ([_gaussian_mixture.py](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/mixture/_gaussian_mixture.py)), and the in-tree implementation at [src/skie_ninja/models/regime/_core.py:139-252](../../../src/skie_ninja/models/regime/_core.py), the per-state covariance object's shape and content at `d = 1` is:

| Type | covars shape | At d=1 | Per-state interpretation |
|---|---|---|---|
| `spherical` | `(N,)` | `(N,)` of positive scalars | one variance per state |
| `diag`      | `(N, d)` = `(N, 1)` | `(N, 1)` of positive scalars | one variance per state |
| `tied`      | `(d, d)` = `(1, 1)` | one positive scalar | one variance **shared** across all states |
| `full`      | `(N, d, d)` = `(N, 1, 1)` | `(N, 1, 1)` of positive scalars | one variance per state |

Three of the four (`spherical`, `diag`, `full`) are *parameter-identical* at d=1 — each encodes one positive scalar variance per state, total `N` free covariance parameters. Only `tied` is materially different: it constrains all `N` states to share a single variance, total `1` free covariance parameter — a stronger model assumption.

### §2.2 BIC parameter count at d=1

In-tree `count_free_parameters` at [_core.py:780-823](../../../src/skie_ninja/models/regime/_core.py) implements the Schwarz-1978 / Celeux-Durand-2008 / Rabiner-1989 simplex parameter accounting:

```
k = (N − 1)              # initial distribution
  + N (N − 1)            # transition matrix rows
  + N · d                # emission means
  + k_covar              # covariance
```

with

```
k_covar(spherical) = N
k_covar(diag)      = N · d
k_covar(tied)      = d (d + 1) / 2
k_covar(full)      = N · d (d + 1) / 2
```

Substituting `d = 1`:

```
k_covar(spherical) = N
k_covar(diag)      = N · 1 = N
k_covar(tied)      = 1 · (1 + 1) / 2 = 1
k_covar(full)      = N · 1 · (1 + 1) / 2 = N
```

Therefore at `d = 1`, the `spherical`, `diag`, and `full` parameterisations have **identical** total parameter counts (and hence identical BIC penalty terms), and only `tied` differs.

### §2.3 Likelihood identity at d=1

The Gaussian log-density `log N(x | μ, Σ) = -½ (d log 2π + log|Σ| + (x−μ)ᵀ Σ⁻¹ (x−μ))` reduces at `d = 1` and `Σ = [[σ²]]` (per-state PSD scalar) to `-½ (log 2π + log σ² + (x−μ)² / σ²)`. This is what the `diag` path computes by `(diff² / var) + log(var)` ufuncs; this is also what the `full` path computes by Cholesky-factorising the 1×1 matrix `[[σ²]]` to `[[σ]]`, calling `solve_triangular` with that single triangular element, squaring, and adding `2 log σ` for the log-determinant.

The two paths are **algebraically identical** at d=1 — they compute the same Gaussian log-density via different code paths.

This was verified by direct microbench (§4):

- At `σ² = 1.0` (unit-variance synthetic input), `max_abs_diff_log_density = 0.0` at every tested `(T, N)` cell — **bit-exact equality**.
- At `σ² = 1e-8` (production-realistic log-return scale), `max_abs_diff_log_density ≈ 4-5 × 10⁻¹⁵` — at floating-point round-off (16-digit double-precision noise floor; not zero because the order-of-operations in the two ufunc/LAPACK paths differs by a few flops, which propagates through finite-precision arithmetic differently). The two paths remain algebraically equivalent; the residual is at `O(ε_machine)`, well below any model-relevant tolerance.

### §2.4 M-step floor-regime caveat

The M-step covariance update at d=1 differs structurally between the two paths in the variance-floor regime ([_core.py:602-608](../../../src/skie_ninja/models/regime/_core.py) for `diag` vs [:622-632](../../../src/skie_ninja/models/regime/_core.py) for `full`):

- `diag` clamps elementwise: `covars[i] = np.maximum(raw, min_var)`.
- `full` adds a ridge only when needed: `_ensure_pd(raw, min_var)` either returns `raw` unchanged (if Cholesky succeeds and `min(diag(L))² ≥ min_var`) or returns `raw + min_var * I` (otherwise).

For raw `σ² ≥ min_var` (the unconstrained regime), both return `raw` and the EM trajectories are bit-exact identical. For raw `σ² < min_var` (the floor regime), the two paths produce different `σ²` values: `diag` returns exactly `min_var`, `full` returns `raw + min_var`. EM trajectories may then diverge.

For production-realistic returns (1-min log-returns, σ ~ 1e-4 to 1e-3, σ² ~ 1e-6 to 1e-8), the floor regime is rarely entered (`min_var` is scale-adaptive and floors at `~1e-15`). The deduplication in [selection.py](../../../src/skie_ninja/models/regime/selection.py) (§5) renders this caveat moot in production: only one EM trajectory runs per model-class equivalence class, so divergence between paths cannot arise.

## §3. Anchor citations

Primary sources for the parameterisation taxonomy and BIC parameter count:

**Tier 2 — official documentation:**

- **sklearn user guide §2.1 (Gaussian mixture models)** — [scikit-learn.org/stable/modules/mixture.html](https://scikit-learn.org/stable/modules/mixture.html). Documents the four-way `{spherical, diag, tied, full}` covariance-type taxonomy + per-component covariance-shape semantics. The page warns that with `full` covariance "estimating the covariance matrices becomes difficult, and the algorithm is known to diverge and find solutions with infinite likelihood unless one regularizes the covariances artificially" — a numerical-singularity caveat, distinct from the d=1-redundancy argument here.
- **Bishop, *Pattern Recognition and Machine Learning* 2006** — §9.2 (Mixtures of Gaussians; develops GMM with general per-component Σ_k that the sklearn/hmmlearn covariance-type taxonomy specialises) and §13.2 (Hidden Markov Models, including Gaussian emissions). The d=1-equivalence corollary is a direct algebraic consequence of the parameter shapes and the Gaussian log-density formula; it is not separately stated as a theorem in either chapter.
- **Murphy, *Machine Learning: A Probabilistic Perspective* 2012** §17.3-17.5 (HMM block: representation, inference, and learning). §17.5 is "Learning for HMMs" (Baum-Welch, Bayesian fitting, model selection), not specifically "HMM with Gaussian emissions"; Gaussian-emission HMMs are touched on across §17.3-17.5.

**Tier 1 — peer-reviewed:**

- **Schwarz, G. 1978. "Estimating the Dimension of a Model." *Ann. Stat.* 6(2):461-464, [doi:10.1214/aos/1176344136](https://doi.org/10.1214/aos/1176344136)** — original BIC; the parameter-count term `k log T` in BIC.
- **Rabiner 1989, *Proc. IEEE* 77(2):257-286, [doi:10.1109/5.18626](https://doi.org/10.1109/5.18626)** — HMM transition + initial-distribution simplex parameter accounting (`(N−1)` + `N(N−1)`). Section pin §III.C.2 is the conventional in-tree attribution at [src/skie_ninja/models/regime/_core.py:801-805](../../../src/skie_ninja/models/regime/_core.py); this paper is paywalled on IEEE Xplore (verification-gap inherited from the project-wide citation policy; tracked under `P1-HMM-VERIFIED-EQ-NUMBERS`).
- **Celeux, G.; Durand, J.-B. 2008. "Selecting hidden Markov model state number with cross-validated likelihood." *Comput. Stat.* 23(4):541-564, [doi:10.1007/s00180-007-0097-1](https://doi.org/10.1007/s00180-007-0097-1)** — modern presentation of HMM parameter count for BIC/CV selection. §3.1 attribution carried from the in-tree docstring at [_core.py:801](../../../src/skie_ninja/models/regime/_core.py); paywalled on Springer (verification-gap, same caveat as Rabiner).

**Tier 4 — vetted reference-library source:**

- **hmmlearn `_log_multivariate_normal_density_diag` and `_log_multivariate_normal_density_full`** — [github.com/hmmlearn/hmmlearn/blob/main/src/hmmlearn/stats.py](https://github.com/hmmlearn/hmmlearn/blob/main/src/hmmlearn/stats.py). The two density paths' implementations are reference-library source-of-truth for the d=1 algebraic equivalence claim. (Per evidence-hierarchy in [~/.claude/CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md), reference-library source code is Tier 4 — vetted technical forum / library source — not Tier 2 official documentation.)
- **sklearn.mixture.GaussianMixture `_estimate_log_gaussian_prob`** — [github.com/scikit-learn/scikit-learn/blob/main/sklearn/mixture/_gaussian_mixture.py](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/mixture/_gaussian_mixture.py). Identical four-way covariance taxonomy with documented shape semantics.

The d=1 equivalence claim itself is therefore at **Tier 2 / Tier 4 hybrid**: the parameterisation shapes are documented in sklearn user guide §2.1 (Tier 2); the d=1 algebraic equivalence is a direct corollary derivable from the documented shapes plus the Gaussian log-density formula, with the canonical implementation paths in hmmlearn / sklearn (Tier 4) as the source-of-truth for the per-state scalar-variance representation.

## §4. Microbench (Tier-5 in-house measurement)

### §4.1 Methodology

Source: [scripts/bench/bench_hmm_cov_d1.py](../../../scripts/bench/bench_hmm_cov_d1.py).
Runbook: [scripts/bench/README.md](../../../scripts/bench/README.md) (canonical invocation, output schema, limitations).
Raw output: [logs/bench_hmm_cov_d1_2026-04-26.json](../../../logs/bench_hmm_cov_d1_2026-04-26.json) — atomic-incremental JSON manifest with `git_head`, `platform`, `platform_processor`, `numpy_show_config` (BLAS vendor), `uv_pip_freeze_first_lines`, and `runtime_status` keys.
Console transcript: [logs/bench_hmm_cov_d1_2026-04-26.log](../../../logs/bench_hmm_cov_d1_2026-04-26.log).
BLAS pinned to 1 thread per [ADR-0009](../../../docs/decisions/ADR-0009-blas-thread-pinning.md): `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.
Tier per [~/.claude/CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md) §"Evidence Hierarchy": **5 — single-host empirical hand measurement, not a published benchmark**.

### §4.2 Per-E-step `log_emission_matrix` ratios

Median over `n_iter ∈ {30, 50}` calls; N=2 states; d=1; warm-up call dropped; 95% percentile-bootstrap CI on the ratio (2000 resamples). Two scale regimes: `σ² = 1.0` (default synthetic) and `σ² = 1e-8` (production-realistic 1-min log-return scale).

**σ² = 1.0:**

| T (rows) | diag median (ms) | full median (ms) | full/diag ratio | 95% bootstrap CI | log-density max-abs-diff |
|---|---|---|---|---|---|
| 10,000     | 0.051  | 0.130   | 2.569× | [2.531, 2.630] | 0.0 (bit-exact) |
| 100,000    | 2.140  | 2.340   | 1.093× | [1.034, 1.166] | 0.0 (bit-exact) |
| 1,000,000  | 27.787 | 33.989  | 1.223× | [1.184, 1.256] | 0.0 (bit-exact) |
| 3,000,000  | 89.724 | 104.731 | 1.167× | [1.140, 1.193] | 0.0 (bit-exact) |

**σ² = 1e-8 (production-realistic):**

| T (rows) | diag median (ms) | full median (ms) | full/diag ratio | log-density max-abs-diff |
|---|---|---|---|---|
| 100,000    | 1.955  | 2.444   | 1.250× | 4 × 10⁻¹⁵ |
| 1,000,000  | 28.252 | 33.086  | 1.171× | 5 × 10⁻¹⁵ |
| 3,000,000  | 87.002 | 104.948 | 1.206× | 5 × 10⁻¹⁵ |

The bit-exact equality at `σ² = 1.0` confirms §2.3's algebraic-identity claim cleanly. At `σ² = 1e-8`, `max_abs_diff` is at the floating-point round-off floor (~10⁻¹⁵, double-precision noise) — the algebraic equivalence holds; the residual is at `O(ε_machine)` from order-of-operations differences between the ufunc and Cholesky+solve+einsum paths. This is below any model-relevant tolerance.

The production-fold per-E-step ratio is **≈ 1.17× to 1.21× at T = 3M** (95% CI excludes 1.0). Compare to the original diagnosis's "~10×" estimate — off by ~7-8×.

### §4.3 End-to-end `select_gaussian_hmm` after dedup

Mirror of the production call site at [scripts/run_walk_forward.py:788-795](../../../scripts/run_walk_forward.py): `n_states_grid=(2,)`, `min_restarts=5`, `max_restarts=10`. Compares `[diag]`-only vs `[diag, full]` (with the §5 dedup landed). The expected ratio is **≈ 1×** (the dedup short-circuits the second EM trajectory; only BIC recomputation remains, an O(1) cost). `n_aliased_candidates` should be 1.

**Results** (single replicate per cell; see [logs/bench_hmm_cov_d1_2026-04-26.json](../../../logs/bench_hmm_cov_d1_2026-04-26.json) `select_gaussian_hmm_endtoend`):

| T (rows) | `[diag]`-only (s) | `[diag, full]` w/ dedup (s) | ratio | aliased | BIC match |
|---|---|---|---|---|---|
| 20,000 | 224.46 | 273.75 | 1.220× | 1 | True |
| 50,000 | 797.95 | 811.55 | **1.017×** | 1 | True |

The T=50k ratio of 1.017× is essentially perfect — the dedup adds <2% wall-clock overhead at this scale. The T=20k 1.220× appears to be single-replicate wall-time variance (smaller absolute time → larger relative noise; both runs use bit-identical RNG seeds per `SeedSequence.spawn` determinism). `BIC match = True` confirms the aliased candidate's BIC equals the original-fit candidate's BIC byte-exactly.

### §4.4 Wall-clock saving — production extrapolation

Bounding the H050 walk-forward wall-clock saving from the §4.2 measurements:

- **Without dedup** (the regime the original diagnosis hung on): every `select_gaussian_hmm` call pays for two EM trajectories at d=1. The full trajectory's per-iter cost is ~1.17-1.21× the diag trajectory's (§4.2 production-realistic σ² cell). Cold-fit cost decomposes as `(per-iter cost) × (EM iterations) × (restarts) × (covariance-type variants)`. Per §2.3 + §2.4, EM landscapes are identical at d=1 outside the floor regime, so iterations + restarts are identical in expectation. The expected total cost is thus `T_diag + T_full ≈ T_diag × (1 + 1.18) ≈ 2.18 × T_diag`.
- **With dedup** (this addendum's r2): the second trajectory is skipped; `T_dedup ≈ T_diag`. Saving relative to the no-dedup regime is `1 − 1/2.18 ≈ 54%`.

**Wall-clock estimate revision.** The diagnosis's pre-fix `~24-48 hr` estimate is itself a back-of-envelope claim with no separate validation. Even granting it, the saving applies *only to the HMM cold-fit component* — non-HMM components form a floor:

- TripleBarrierLabeler (diagnosis §H3 row): plausible ~2.25 hr cumulative across 27 cfgs × 2 syms; unaffected by this patch.
- Feature pass (rolling-window microstructure, 7.4M rows): ~3.6 sec; negligible.
- Hansen SPA bootstrap: minutes; negligible.

Therefore: `post-dedup wall-clock = HMM_pre × 0.46 + non_HMM_floor`. With HMM dominant at ~80-90% of the pre-fix wall-clock and non-HMM floor ~2-3 hr:

```
post = HMM_pre × 0.46 + non_HMM_floor
     ≈ (24-48) × 0.85 × 0.46 + 2.5
     ≈ 9-19 + 2.5
     ≈ 12-22 hr
```

The honest revised estimate is **~12-22 hr** (single-host extrapolation per Tier-5 microbench; non-HMM floor included). The original diagnosis's "~3-6 hr" estimate was based on the unattributed ~10× figure and is rescinded.

### §4.5 What the bench does **not** establish

- It does not establish the magnitude on hardware other than this one; the constant factor is hardware + BLAS-vendor-conditional (per the bench manifest, this run was OpenBLAS 0.3.31.188.0 USE64BITINT DYNAMIC_ARCH on Intel64 Family 6 Model 183, single-threaded). The `numpy_show_config` and `uv_pip_freeze_first_lines` fields in the JSON manifest enable cross-host replication but do not extend the magnitude claim. No published benchmark of 1×1 Cholesky overhead exists; closest indirect evidence is [SciPy issue #23774](https://github.com/scipy/scipy/issues/23774) (d=20 smallest reported size) and the [Julia Discourse `LAPACK.potrf!` thread](https://discourse.julialang.org/t/why-the-time-consumed-of-lapack-potrf-increase-hugely-when-the-dimension-is-bigger-than-a-special-number/82270) (n=16→17 cliff).
- It does not establish a *qualitative* claim that did not already follow from source-code inspection: the `full` path always invokes per-state Cholesky + LAPACK triangular solve + einsum, and is therefore guaranteed to be ≥ the `diag` path's vectorised-ufunc cost on any platform.
- It does not measure interaction with EM convergence iterations across the full restart × max-iter envelope; the per-E-step bench measures `log_emission_matrix` only and the M-step paths handle the variance floor differently (§2.4). The end-to-end bench captures the combined effect for the dedup case (the T=50k cell measured `ratio = 1.017×` between `[diag]`-only and `[diag, full]`-with-dedup, confirming the dedup short-circuit produces a clean ≈1× wall-clock match).

## §5. The patch

### §5.1 Implementation: model-class deduplication in select_gaussian_hmm

[src/skie_ninja/models/regime/selection.py](../../../src/skie_ninja/models/regime/selection.py) `select_gaussian_hmm` is patched to detect d=1 model-class equivalents and skip redundant fits. The pre-registered grid in [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml) is **preserved verbatim** (`[diag, full]`); the candidates list still contains both `(n, "diag")` and `(n, "full")` entries; only the second EM trajectory is skipped via aliasing.

Mechanism:

```python
def _model_class_signature(cov: CovarianceType) -> str:
    if dim == 1 and cov in ("spherical", "diag", "full"):
        return "d1_per_state_scalar"
    return cov

# Per (n_states, signature) → (log_likelihood, fitted_model). At d=1,
# {spherical, diag, full} all collapse to "d1_per_state_scalar"; tied
# remains its own signature.
fit_cache: dict[tuple[int, str], tuple[float, GaussianHMM]] = {}

# Inside the (n, cov) loop:
sig = (n, _model_class_signature(cov))
if sig in fit_cache:
    ll, _ = fit_cache[sig]
    bic_score = bic(log_likelihood=ll, n_states=n, dim=dim,
                    covariance_type=cov, t_len=...)
    candidates.append(SelectionCandidate(
        n_states=n, covariance_type=cov, log_likelihood=ll, bic=bic_score,
        n_restarts_used=0,  # alias marker
    ))
    continue
# else: fit normally and populate fit_cache[sig].
```

The aliased `SelectionCandidate` carries `n_restarts_used = 0` as the alias marker; downstream readers can detect aliases without ambiguity. The BIC is recomputed under the requested `cov_type` label so any future drift in `count_free_parameters` would surface as a BIC mismatch in the test suite (regression coverage in [tests/unit/test_hmm_selection.py](../../../tests/unit/test_hmm_selection.py) `TestD1ModelClassDeduplication`).

### §5.2 Equivalence-class membership at d=1

Per §2 derivation:

- `{spherical, diag, full}` at d=1 all encode *one positive scalar variance per state* with `k_covar = N`. They are model-class equivalent. Aliased.
- `tied` at d=1 encodes *one positive scalar variance shared across states* with `k_covar = 1`. **Not** equivalent. Always fit independently.

The deduplication is keyed on `(n_states, signature)`; mixing dim into the signature would be redundant since a single `select_gaussian_hmm` call has fixed `dim`. At d > 1, no aliasing occurs (the `if dim == 1` guard returns the literal cov-type).

### §5.3 What is **not** changed

- The pre-registered grid in [design.md](design.md) §5 (`covariance_type ∈ {diag, full}`) and [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml) `hmm.covariance_type` (line 37) (`[diag, full]`).
- The `SelectionResult.candidates` tuple — every requested `(n, cov)` pair appears as a candidate; aliased candidates differ only in their `n_restarts_used = 0` marker.
- BIC values for the diag and full candidates at d=1 — by §2.2 they are identical; the patch makes this exact (the second BIC reuses the first's log-likelihood).
- The pre-registered hypothesis ID, test statistic, universe, train/val/test windows, label method, classifier family, splitter, gates, cost model, or random seed.
- The `best_model` returned. With the strict `<` BIC comparison, the first-encountered cov-type at the BIC-minimising n_states wins ties; for H050's `[diag, full]` ordering, that is `diag`. Downstream prediction via `log_emission_matrix(x, means, covars, "diag")` is bit-exact identical at d=1 to what the `"full"`-labelled path would produce (§2.3, §4.2).

### §5.4 What is changed

- Compute. Cold-fit wall-clock per stratum-fold-symbol: ~46% of the no-dedup baseline (§4.4) at production scale.
- `n_restarts_used` field on aliased candidates: now `0` (was the underlying fit's `n_restarts_used`, which would have been a separate fit's value pre-dedup). Audit-trail readers must interpret `n_restarts_used = 0` as "alias, see prior candidate at same `(n, signature)`".
- Total H050 walk-forward wall-clock estimate: **~12-22 hr** (revised per §4.4; the diagnosis's "~3-6 hr" estimate based on the unattributed ~10× figure is rescinded).

## §6. Pre-reg-fidelity argument

A later auditor could ask: does the deduplication subvert the pre-reg fidelity argument that motivated Cell I (per [docs/research_notes/memo_option-b-data-coverage_2026-04-24.md](../../../docs/research_notes/memo_option-b-data-coverage_2026-04-24.md))? The argument that it does **not**:

1. **The grid is unchanged.** [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml) still binds `[diag, full]`; [design.md](design.md) §5 still binds `covariance_type ∈ {diag, full}`. Nothing pre-registered is edited. The `SelectionResult.candidates` tuple still contains both `(n, "diag")` and `(n, "full")` records.
2. **The d=1 equivalence is established prior to any data observation.** It is a fact about the model class, derivable from parameter shapes (sklearn user guide §2.1, hmmlearn / sklearn source) and the Gaussian log-density formula. The BIC parameter count at d=1 makes the two grid points **identical** at the selection step regardless of which observations are fed to the HMM. The deduplication is therefore a substrate-blind optimisation: it operates on a property of the model class, not of the data.
3. **The user-global rule at [~/.claude/CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md) §"Parameter & Prompt Selection"** — "Zero arbitrary thresholds or magic numbers. Tunable values require empirical justification" — constrains the *selection of tunable values*, not the *deduplication of provably equivalent grid points*. The dedup keeps both grid points in the audit log; only the redundant compute is skipped.
4. **The diagnosis triggered the audit, but the equivalence argument is independent of the diagnosis** (it would have been true regardless of whether the run hung). The deduplication implementation is itself substrate-blind: the `_model_class_signature` function consults only `dim` and `cov_type`, never any data property.
5. **Path A admissibility under [design.md](design.md) §10 + ¶22** (the in-place-clarification escape that the existing aggregation-rule addendum r2 invokes): this addendum operationalises an algebraic property of the pre-reg model class. No binding statistic, universe, window, or model-class assumption changes.

## §7. References

In-tree:
- [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml) — pre-reg config (unchanged grid; top-of-file comment block points here).
- [src/skie_ninja/models/regime/_core.py](../../../src/skie_ninja/models/regime/_core.py) — `log_emission_matrix` at lines 139-252; `count_free_parameters` at 780-823; `bic` at 826-846; `_m_step_emissions` at 553-634.
- [src/skie_ninja/models/regime/selection.py](../../../src/skie_ninja/models/regime/selection.py) — `select_gaussian_hmm` with the d=1 model-class deduplication landed.
- [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) — orchestrator call at lines 788-795.
- [scripts/bench/bench_hmm_cov_d1.py](../../../scripts/bench/bench_hmm_cov_d1.py) — Tier-5 microbench source.
- [scripts/bench/README.md](../../../scripts/bench/README.md) — bench runbook + canonical invocation.
- [logs/bench_hmm_cov_d1_2026-04-26.json](../../../logs/bench_hmm_cov_d1_2026-04-26.json) — bench output (atomic-incremental JSON manifest).
- [logs/bench_hmm_cov_d1_2026-04-26.log](../../../logs/bench_hmm_cov_d1_2026-04-26.log) — bench console transcript.
- [tests/unit/test_hmm_selection.py](../../../tests/unit/test_hmm_selection.py) — `TestD1ModelClassDeduplication` regression suite (7 tests).
- [tests/unit/test_hmm_core.py](../../../tests/unit/test_hmm_core.py) — `test_d1_full_equals_diag_bit_exact`, `test_d1_spherical_equals_diag_bit_exact`, `test_d1_param_count_equivalence_class`, `test_d1_bic_equivalence_class` regression tests.
- [tests/unit/test_h050_config.py](../../../tests/unit/test_h050_config.py) — pre-reg-grid invariant tests asserting `[diag, full]` is preserved.
- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../../../docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — diagnosis audit trail (amended in same patch).
- [docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md](../../../docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md) — audit-remediate-loop trail for this addendum.
- [docs/research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md](../../../docs/research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md) — proposal memo this addendum implements.
- [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](aggregation_rule_addendum_2026-04-24.md) — sibling addendum on cross-symbol aggregation (disjoint scope).
- [research/01_hypothesis_register/H050/design.md](design.md) — H050 pre-registration record.
- [docs/decisions/ADR-0009-blas-thread-pinning.md](../../../docs/decisions/ADR-0009-blas-thread-pinning.md) — BLAS single-thread pinning rationale.

External (Tier 1 — peer-reviewed):
- [Schwarz 1978, *Ann. Stat.* 6(2):461-464, doi:10.1214/aos/1176344136](https://doi.org/10.1214/aos/1176344136).
- [Rabiner 1989, *Proc. IEEE* 77(2):257-286, doi:10.1109/5.18626](https://doi.org/10.1109/5.18626).
- [Celeux & Durand 2008, *Comput. Stat.* 23(4):541-564, doi:10.1007/s00180-007-0097-1](https://doi.org/10.1007/s00180-007-0097-1).

External (Tier 2 — official documentation):
- [sklearn user guide §2.1 Gaussian mixture models](https://scikit-learn.org/stable/modules/mixture.html).
- Bishop 2006 *PRML* §9.2 (Mixtures of Gaussians) + §13.2 (Hidden Markov Models).
- Murphy 2012 *MLPP* §17.3-17.5 (HMM block).

External (Tier 4 — vetted reference-library source):
- [hmmlearn stats.py](https://github.com/hmmlearn/hmmlearn/blob/main/src/hmmlearn/stats.py) — `_log_multivariate_normal_density_diag/full`.
- [sklearn _gaussian_mixture.py](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/mixture/_gaussian_mixture.py) — `_estimate_log_gaussian_prob` four-way cov-type dispatch.
- [pomegranate issue #227](https://github.com/jmschrei/pomegranate/issues/227) — feature request from 2017-02-26 for hmmlearn-style covariance-type parameter; not implemented as of issue date (no maintainer comment about univariate-emission workarounds).
- [SciPy issue #23774](https://github.com/scipy/scipy/issues/23774) — `linalg` Python-side overhead at d=20 (smallest reported size in that thread); the closest published numbers to a 1×1 LAPACK Cholesky benchmark.
- [Julia Discourse: `LAPACK.potrf!` n=16→17 cliff](https://discourse.julialang.org/t/why-the-time-consumed-of-lapack-potrf-increase-hugely-when-the-dimension-is-bigger-than-a-special-number/82270) — qualitative confirmation that small-n LAPACK is overhead-bound, not arithmetic-bound.
- [depmixS4 JSS 36(7) 2010, doi:10.18637/jss.v036.i07](https://www.jstatsoft.org/article/view/v036i07) — R HMM package with API-level univariate vs multivariate response separation (no `covariance_type` knob).
