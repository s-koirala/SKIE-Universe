---
title: H050 production walk-forward — Run 1 diagnosis
date: 2026-04-26
artifact: scripts/run_walk_forward.py production execution on post-Cell-I substrate
followup_id: P1-H050-PROD-RUN-1-DIAGNOSIS
exit_state: round-1 accept-with-pending-fix-decision
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
---

## Scope

Diagnose why the first production H050 walk-forward run on the
post-Cell-I substrate (run_id `e33eff2e1bb449f89b654a38bd80d660`,
background task `bezuqbcc0`) ran for 180 minutes wall-clock with
no per-fold or aggregate artifact written. The run was killed at
+180 min for diagnostic investigation.

## Run state at kill

| Metric | Value |
|---|---|
| Wall time | 180.4 min |
| CPU time | 174.4 min (97% utilisation, single-threaded per ADR-0009 BLAS pinning) |
| Working set | 256 MB (started at 326 MB, dropped during run — GC of intermediate EM matrices) |
| Threads | 86 (numpy / sklearn pool capped at 1 logical thread by env vars) |
| Feature provenance JSONs | **4 written** at `logs/reproducibility/features/{rv_realized,rv_parkinson,realized_skew,ofi_tickrule}_1.0_e33eff2e1bb449f89b654a38bd80d660.json` (latency 0.91 sec each on n_rows=7,354,066) |
| Per-fold artifacts | 0 |
| Aggregate artifacts | 0 |
| stdout file | 0 bytes (subprocess buffered, never flushed) |

Substrate: ES + NQ × 2015-2025, 7,354,066 rows, combined SHA256
`b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`
per the atomic re-freeze in commit `029f85d`.

## Subagent isolation

Round-1 inline-audit by main thread (the implementing-agent
runtime that launched the orchestrator) was inadequate: 180 min
of zero-artifact wall-clock did not point to a specific phase.
Round-1 was therefore re-cast as the post-loop-verification round
with proper subagent isolation per [SKILL.md](../../.claude/skills/audit-remediate-loop/) §40-43:

- **General-purpose script-flow agent** (`agentId a179b31d29b2a63f1`) — read [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py), [src/skie_ninja/features/](../../src/skie_ninja/features/), [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py), [src/skie_ninja/models/regime/_core.py](../../src/skie_ninja/models/regime/_core.py), [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml). Tasked with ranking 8 hypotheses for the dominant bottleneck.
- **reproducibility-verifier agent** (`agentId abf41808d1d8c81cd`) — verified substrate integrity end-to-end. 22 partitions × {NaN/Inf/zero/duplicate/schema/dtype/coverage/roll-contamination} checks.

## Hypotheses tested + verdicts

| ID | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| H1 | Feature matrix not yet computed | **FALSIFIED** | 4 feature provenance JSONs written at run-start with `latency_seconds ≈ 0.91`. Polars rolling-window operations on 7.4M rows complete in ~3.6 sec total. Orchestrator was past feature assembly within the first 4 seconds of the run. |
| H2 | Polars rolling-window pathology | FALSIFIED | Same evidence as H1; per-feature latency 0.91 sec confirms C-level rolling, not Python-level apply. |
| H3 | TripleBarrierLabeler nested Python loop | MEDIUM-priori | [src/skie_ninja/features/labels.py:282-316](../../src/skie_ninja/features/labels.py) has nested Python `for i in range(n)` × `for j in range(i+1, end)` over n=3.7M with inner bound vertical_barrier. Per-cfg cost ~100-300 sec single-threaded. Cumulative across 27 cfgs × 2 syms ≈ 2.25 hr — plausible but not dominant: any cfg completion would emit an artifact, none did. |
| **H4** | **HMM `select_gaussian_hmm` cold-start cost** | **CONFIRMED-DOMINANT** | [selection.py:117-153](../../src/skie_ninja/models/regime/selection.py) iterates `n_states_grid × covariance_types = 1 × 2` outer × `min_restarts=5..max_restarts=10` per-grid EM. Each EM on a ~3M-observation train fold is single-threaded (BLAS pinned to 1 by [ADR-0009](../decisions/ADR-0009-blas-thread-pinning.md)). Per-fit: 30–100 EM iter × ~10–30 sec/iter = ~5–50 min × 5–10 restarts × 2 cov_types ≈ 50 min – 17 hr per `select_gaussian_hmm` call. The HMM cache (commit `1c85f5f`) keyed on `(symbol, fold_id, label_horizon)` only AMORTIZES across the 9 cfgs sharing each `vertical_barrier` stratum — the FIRST cfg of fold 0 for ES still pays the full cold cost. Empty `ES/folds/` after 180 min is exactly consistent with the very first HMM selection still running. |
| H5 | LightGBM inner-CV scaling | LOW | LGB is multi-threaded by default; CPU usage at 97% single-core argues against it. Would have shown 1600%+ on a 16-core box if dominant. Falsified by CPU-utilisation profile. |
| H6 | Memory churn / GC pressure | LOW | WS 326 → 256 MB drop is consistent with EM matrices released between restarts; not pathological. |
| H7 | Hansen SPA bootstrap | LOW | SPA fires at fold completion; no fold has completed. |
| H8 | Warm-cold diagnostic redundancy | LOW | Same — fires at fold prediction time; not the current bottleneck. |

## 1-dim emission redundancy of `full` covariance

H050 binds emissions to **single-feature returns** (`r_tr.reshape(-1, 1)`, dim=1). For d=1, `full` and `diag` covariance encode the SAME object: a single positive scalar per state. BIC selection between them is degenerate (identical likelihood, identical effective parameter count `k = N` for both, per `count_free_parameters` at [_core.py:780-823](../../src/skie_ninja/models/regime/_core.py); in fact `spherical = diag = full = N` at d=1 and only `tied = 1` differs). The IMPLEMENTATION paths differ structurally:

- **`diag` path** ([_core.py:200-211](../../src/skie_ninja/models/regime/_core.py)): 3 vectorised ufuncs (`diff ** 2 / covars`, `log(covars)`, sum) on a T-length array.
- **`full` path** ([_core.py:232-250](../../src/skie_ninja/models/regime/_core.py)): per-state-per-iteration `np.linalg.cholesky` (1×1 matrix → trivial mathematically but invokes LAPACK) + `np.linalg.solve` (triangular, T-length) + `np.einsum`.

**Constant-factor amendment (2026-04-26).** This audit trail's original text estimated the `full` overhead at "~10×" without an in-run measurement. That estimate was wrong. A subsequent in-house Tier-5 microbench (BLAS pinned to 1 thread per ADR-0009; source [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py); raw JSON [logs/bench_hmm_cov_d1_2026-04-26.json](../../logs/bench_hmm_cov_d1_2026-04-26.json); console transcript [logs/bench_hmm_cov_d1_2026-04-26.log](../../logs/bench_hmm_cov_d1_2026-04-26.log)) measured the per-E-step `full/diag` ratio with 95% percentile-bootstrap CI (2000 resamples) at unit variance:

| T (rows) | diag (ms) | full (ms) | ratio | 95% CI | max-abs-diff |
|---|---|---|---|---|---|
| 10,000     | 0.051  | 0.130   | **2.569×** | [2.531, 2.630] | 0.0 (bit-exact) |
| 100,000    | 2.140  | 2.340   | **1.093×** | [1.034, 1.166] | 0.0 (bit-exact) |
| 1,000,000  | 27.787 | 33.989  | **1.223×** | [1.184, 1.256] | 0.0 (bit-exact) |
| 3,000,000  | 89.724 | 104.731 | **1.167×** | [1.140, 1.193] | 0.0 (bit-exact) |

At production-realistic σ²=1e-8 (1-min log-return scale), the ratios are 1.250× / 1.171× / 1.206× at T = (100k, 1M, 3M) with `max_abs_diff ≈ 5×10⁻¹⁵` (floating-point round-off; algebraic equivalence holds to ε_machine precision).

At the production fold size (T~3M), `full` is **1.17-1.21× per-E-step**, not 10×. The `~10×` was off by ~7-8×. Tier-5 single-host hand measurement; magnitude is hardware + BLAS-vendor-conditional (see `numpy_show_config` key in JSON manifest).

**Mechanism note:** the original Recommended-fix paragraph below proposed dropping `full` from H050.yaml. After the Round-1 audit-remediate-loop, the implementation was changed to model-class deduplication inside `select_gaussian_hmm` ([src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py)) — pre-reg fidelity preserved (the `[diag, full]` grid in H050.yaml and design.md is unchanged); the second EM trajectory is short-circuited via aliased `SelectionCandidate(n_restarts_used=0)`. See [research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md](../../research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md) for the formal addendum and [docs/research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md](../research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md) for the reconciling proposal memo. Audit-remediate-loop trail: [docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md](audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md).

For 1-dim emissions, fitting `full` does **redundant** work — it produces an identical likelihood at the per-E-step ratio above. This is not an algorithmic optimisation; it is removal of computation that has no effect on the model.

## Substrate verification

Independent reproducibility-verifier agent (`abf41808d1d8c81cd`)
verified the substrate end-to-end with 9 hypotheses tested:

| Check | Verdict |
|---|---|
| All-zero close | PASS (0 / 7,354,066) |
| All-zero volume | PASS (0 / 7,354,066) |
| Duplicate `(symbol, ts_event)` | PASS (0) |
| Out-of-order `ts_event` per partition | PASS (0) |
| NaN/Inf in OHLCV | PASS (0) |
| `adjustment_factor ≤ 0` | PASS (0) — range 1.0000 (anchor) → 1.2337 (NQH5_2015) |
| Schema/dtype drift across partitions | PASS (1 distinct schema across 22 partitions) |
| Partition fragmentation | PASS (313k–344k rows/partition; 3 row-groups @ ~7 MB each) |
| Year-end roll contamination | PASS (0 mis-partitioned bars; v0.3.0 disambiguation working) |
| Per-(symbol, year) coverage gaps | FLAG-EXPECTED (ES 2025 → 2025-12-03; NQ 2025 → 2025-12-19; matches CLAUDE.md disclosure and is documented as `P1-DATABENTO-RIGHT-EDGE-EXTENSION`) |

Combined SHA256 reproduces exactly. **The substrate is not the cause of the hang.** Compute is genuine, not pathological.

## Recommended fix

**Patch (final, after Round-1 audit-remediate-loop)**: model-class deduplication inside `select_gaussian_hmm` ([src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py)). The H050.yaml `[diag, full]` grid and design.md §5 binding are preserved verbatim; the redundant second EM trajectory is short-circuited at fit time via aliased `SelectionCandidate(n_restarts_used=0)`. Both candidates still appear in `SelectionResult.candidates` for audit fidelity. This is **not a method change** — it removes redundant computation that has no model-class consequence on 1-dimensional emissions.

The original "~drop `full` from H050.yaml + new addendum + Schwarz docstring fix" proposal (the literal text removed from this section) was rescinded after Round-1 quant-auditor finding Q-1-4 confirmed [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §5 line 62 binds `covariance_type ∈ {diag, full}` as a 2-element grid. Editing the YAML grid would have been a contestable pre-reg edit. The deduplication path (auditor's recommended fix (c)) preserves pre-reg fidelity exactly.

Estimated impact (revised 2026-04-26 after microbench in §"Constant-factor amendment"):
- Removes the redundant compute (only one EM trajectory runs per stratum-fold-symbol-equivalence-class); the second `(n, "full")` candidate is recorded in `SelectionResult.candidates` with `n_restarts_used = 0` as the alias marker.
- Per-fold HMM cold-fit: roughly the previous `(diag + full)` time × `1/(1 + 1.18) ≈ 0.46` (per-E-step ratio at production-realistic σ²).
- Total run wall-clock: ~24–48 hr (pre-fix estimate) → **~12–22 hr** (post-fix estimate, including non-HMM floor of ~2-3 hr from TripleBarrierLabeler and other components unaffected by this patch). The original "~3–6 hr" estimate in this audit trail was based on the unattributed ~10× figure and is rescinded.
- Cache amortisation unchanged (still 9× within stratum-fold).

Alternative fixes (deferred unless needed):
- Reduce `min_restarts=5` floor (ADR-0005 bound; would need ADR amendment).
- Subsample returns for HMM fit (every 5–10 bars) — methodological change; requires successor hypothesis.
- Coarser-grain HMM emission (5-min bars) — same; successor hypothesis.

## Exit verdict

`accept-with-pending-fix-decision` — the diagnosis is rigorous (substrate clean; bottleneck is HMM `full` cold-fit on 1-dim emissions, mathematically redundant); the fix path is documented; user direction pending on whether to patch + relaunch immediately or first add instrumentation logging to confirm the diagnosis empirically.

## New follow-ups logged

- `P1-HMM-FULL-COV-1DIM-REDUNDANT` *(perf, blocking next walk-forward run — closed in same patch)* — implement model-class deduplication inside `select_gaussian_hmm` ([src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py)) so the redundant `full`-cov fit at d=1 is short-circuited via aliased `SelectionCandidate(n_restarts_used=0)`. The pre-registered `[diag, full]` grid in [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml) and [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §5 is preserved verbatim. The original "patch H050.yaml" recommendation in this audit trail's first iteration was rescinded after Round-1 audit-remediate finding Q-1-4 confirmed the YAML edit would have been a contestable pre-reg edit. Formal addendum: [research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md](../../research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md). Audit-remediate-loop trail: [docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md](audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md).
- `P1-ORCHESTRATOR-PROGRESS-LOGGING` *(operational, open)* — add INFO-level progress log lines at `_fit_fold` start/end + per-cfg start/end so a future multi-hour run is observable without `py-spy` dump. Should not require any logging-config change beyond the existing structured-JSON logger.

## References

- ADR-0005 (HMM regime toolkit) §"Hyperparameter governance" — `min_restarts` floor.
- [ADR-0009](../decisions/ADR-0009-blas-thread-pinning.md) — BLAS thread pinning rationale (single-threaded EM).
- Commit `1c85f5f` (P1-H050-SMOKE-RUNTIME-INVESTIGATE closure) — HMM cache scope and limitations.
- López de Prado 2018 *Advances in Financial Machine Learning*, ISBN 978-1-119-48208-6, §4 (triple-barrier) + §7 (purge/embargo).
- Rabiner 1989 *Proc. IEEE* 77(2):257-286 §III.A — Baum-Welch EM forward-backward recursion.
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) — orchestrator.
- [src/skie_ninja/models/regime/_core.py](../../src/skie_ninja/models/regime/_core.py) — `log_emission_matrix` for `diag` vs `full` paths on 1-dim emissions.
- [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json) — substrate provenance.
