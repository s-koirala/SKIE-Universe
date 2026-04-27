# scripts/bench — Microbenches

Tier-5 in-house empirical measurements that anchor specific
quantitative claims in audit trails, addenda, or research notes.
Per the user-global evidence hierarchy
(`~/.claude/CLAUDE.md` §"Evidence Hierarchy"), these are
**Tier-5 single-host hand measurements** — not published
benchmarks. Every consumer of a microbench number must label it
as such in the citing artifact.

All microbenches in this directory pin BLAS to a single thread
per [ADR-0009](../../docs/decisions/ADR-0009-blas-thread-pinning.md).
Production walk-forward runs are likewise single-threaded; the
microbenches measure the same regime.

## bench_hmm_cov_d1.py

Anchors the d=1 `full`-vs-`diag` covariance constant-factor claim
in the H050 prod-run-1 diagnosis
([docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../../docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md))
and the model-class deduplication addendum
([research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md](../../research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md)).

### Canonical invocation

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    uv run python -u scripts/bench/bench_hmm_cov_d1.py \
    --out logs/bench_hmm_cov_d1_<DATE>.json
```

### What it measures

1. **Per-E-step `log_emission_matrix`** at `(T, N=2, d=1)` cells
   `(10k, 100k, 1M, 3M)` under both `sigma2=1.0` (default) and
   `sigma2=1e-8` (production-realistic log-return scale). Reports
   `diag` median, `full` median, `full/diag` ratio, 95% percentile
   bootstrap CI on the ratio (2000 resamples), and bit-exact
   equality check on the log-density output.
2. **End-to-end `select_gaussian_hmm`** at `(T, N=2)` cells
   `(20k, 50k)` mirroring the H050 orchestrator call site
   `(scripts/run_walk_forward.py:788-795)`: `n_states_grid=(2,)`,
   `min_restarts=5`, `max_restarts=10`. Compares `[diag]`-only vs
   `[diag, full]` (with the dedup landed in `selection.py`); the
   ratio should be ≈1× and `n_aliased_candidates` should be 1 of
   the 2 candidates. Verifies BIC equality between the two cov
   types at d=1.

Skip the end-to-end loop with `--skip-endtoend` for fast turnaround
(per-E-step block alone takes ~minutes; end-to-end takes ~10s of
minutes per cell at `min_restarts=5` on a 10-iter EM).

### What is in the output JSON

The bench writes its output JSON **atomically and incrementally**
(after every cell) so a partial run still persists provenance. Keys:

- `git_head`, `platform`, `platform_processor`, `platform_machine`,
  `python`, `numpy` — environment manifest.
- `blas_pinned` — captured env-var values (must all be `"1"`).
- `numpy_show_config` — BLAS vendor / build info from
  `np.show_config()` (e.g. `mkl_info`, `openblas_info`).
- `uv_pip_freeze_first_lines` — first 30 lines of `uv pip freeze`
  for dependency reproduction.
- `log_emission_matrix_runs[]` — per-cell timing records.
- `select_gaussian_hmm_endtoend[]` — per-cell end-to-end records.
- `runtime_status` — `"in_progress"` while running, `"completed"`
  on clean exit. A killed run leaves `"in_progress"` so an
  auditor can detect partial output.

### Limitations (Tier-5 caveats)

1. **Single-host**. The constant-factor magnitude is hardware +
   BLAS-vendor-conditional. Replication on different `numpy_show_config`
   is required to generalise the magnitude.
2. **No multi-replicate aggregation**. One host, one run; the
   95% bootstrap CI on the ratio measures *within-run* variability,
   not across-run / across-host variability.
3. **Per-E-step measurement**. The bench measures
   `log_emission_matrix` only; the M-step (`_m_step_emissions` at
   [src/skie_ninja/models/regime/_core.py:553-634](../../src/skie_ninja/models/regime/_core.py))
   is **not** measured, and at d=1 the diag and full M-step
   paths handle the variance floor differently
   (`np.maximum(raw, min_var)` vs `_ensure_pd(raw, min_var)`),
   which can cause EM trajectories to diverge in the floor regime.
   The end-to-end bench captures the combined effect, but the
   per-E-step ratio is not the full pipeline ratio.
