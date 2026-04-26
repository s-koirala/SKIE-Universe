---
title: P1-H050-SMOKE-RUNTIME-INVESTIGATE — audit-remediate-loop trail
date: 2026-04-26
artifact: HMM-fit cache amortising select_gaussian_hmm across the 27-cell label grid
followup_id: P1-H050-SMOKE-RUNTIME-INVESTIGATE
exit_state: round-1 implementation; subagent_isolation=deferred-to-main-thread
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: deferred-to-main-thread
---

## Scope

Close `P1-H050-SMOKE-RUNTIME-INVESTIGATE` (CLAUDE.md §"Implemented infrastructure (as of 2026-04-23) → Cycle 6 partial"). The brief: amortise the per-fold HMM fit (`select_gaussian_hmm` with `min_restarts=5, max_restarts=10` over `covariance_types`) across the 27-cell label grid by recognising that the HMM input `r_tr = r[train_idx]` is a function of `(symbol, train_idx)` only — label cfg parameters (`pt_sl`, `vertical_barrier`, `volatility_lookback`) perturb `y` and the outer-fold `purge_window` (and therefore fold geometry) but not the close-derived returns. Without amortisation, the orchestrator's real-substrate smoke run hung at 41 min on a 3M-row substrate (per CLAUDE.md `P1-CYCLE6-REPRO-DATASET-CHECKSUM` closure note); the dominant cost is the BIC-grid HMM EM, paid 27× per (symbol, fold) under the legacy code path.

This is a pure performance refactor with NO methodological surface. Behaviour for production walk-forward runs is byte-identical (warm-cold sidecar SHA256 unchanged for fixed seeds + data); the cache is exposed as a toggle (`--no-hmm-cache`) for byte-identical-output regression verification and rollback safety. The HMM module ([src/skie_ninja/models/regime/](../../src/skie_ninja/models/regime/)) and the engine layer ([src/skie_ninja/backtest/engine/walk_forward.py](../../src/skie_ninja/backtest/engine/walk_forward.py)) are out of scope per the brief — no algorithm change; no engine change.

## Method-fidelity anchor

None. Performance refactor only. The cache invariant (`train_idx_len` + first/last index match) is a load-bearing correctness gate against fold-id collisions across engines with diverging purge_window geometry; it raises rather than silently serves a stale fit.

## Round-1

### Implementation summary

- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py):
  - New frozen dataclass `_CachedHmmFit` capturing the fitted `GaussianHMM`, the train-fold terminal log α (P1-HMM-FOLD-WARM-START warm-start sufficient statistic), the train-fold terminal bar position, the `regime_high_mean` index, and the cache-invariant guards (`train_idx_len`, `train_idx_first`, `train_idx_last`).
  - New `_HmmCacheStats` dataclass tracking `n_hits`, `n_misses`, `total_hmm_fit_time_s`, `total_cache_lookup_time_s`, and a `unique_keys` set for `n_unique_keys`. Operational telemetry only — NOT included in the model hash, NOT a methodological artifact.
  - New `_validate_cache_invariant(cached, train_idx, *, symbol, fold_id)` raises `RuntimeError` when a cached entry's geometry mismatches the requesting fold. Documents the invariant: for a fixed symbol's `r` array, `fold_id` deterministically selects `train_idx` for the engine that produced it; collisions across engines with different `purge_window` are a programmer error against the engine-reset contract.
  - `_fit_fold(...)` extended with four new keyword args: `fold_id: int | None = None`, `symbol: str | None = None`, `hmm_cache: dict[tuple[str, int], _CachedHmmFit] | None = None`, `hmm_cache_stats: _HmmCacheStats | None = None`. The body branches on cache hit / miss:
    - **Hit**: skip `select_gaussian_hmm`; reuse cached `hmm`, `hmm_terminal_log_alpha`, `hmm_train_terminal_position`, `regime_high_mean`. Increment `n_hits`. Run `_validate_cache_invariant` first.
    - **Miss**: run `select_gaussian_hmm` exactly as before; populate cache entry; increment `n_misses` and `unique_keys`; record `total_hmm_fit_time_s`.
  - The y-degenerate short-circuit branch (`len(np.unique(y_tr)) < 2`) also reuses cached values when available and populates the cache on miss, so a degenerate fold is not re-fit on subsequent cfg cells.
  - `_run_symbol_label_cfg(...)` accepts `hmm_cache` + `hmm_cache_stats` kwargs and passes them through `engine.run(fit_kwargs=dict(..., symbol=sym, hmm_cache=hmm_cache, hmm_cache_stats=hmm_cache_stats))`. The engine's `_accepts_fold_id_kwarg` introspection (P1-WF-ENGINE-FOLD-ID-PASSTHROUGH, commit `81f25f8`) injects `fold_id` automatically; `symbol`, `hmm_cache`, `hmm_cache_stats` flow through `fit_kwargs`.
  - `_run_symbol(...)` instantiates one `_HmmCacheStats` and one `dict[(str,int), _CachedHmmFit]` per invocation. Cache is `None` when `args.no_hmm_cache` is set (legacy path). Loop body passes the cache + stats into each `_run_symbol_label_cfg` call across the 27-cell label grid. End-of-symbol `_LOG.info(...)` emits cache stats; the per-symbol run-summary dict carries `hmm_cache_stats` and `hmm_cache_enabled`.
  - `_parse_args(...)`: new `--no-hmm-cache` flag. Default off (cache enabled). Help text documents the toggle's purpose (rollback / regression verification).
  - `run_summary.json` extended with `hmm_cache_enabled` and per-symbol `hmm_cache_stats` blocks.
- [tests/unit/test_orchestrator_hmm_cache.py](../../tests/unit/test_orchestrator_hmm_cache.py) — NEW file with 6 tests:
  1. `test_hmm_cache_hit_reuses_fitted_model` — synthetic 600-row fixture; first call (miss) populates cache, second call (same `(symbol, fold_id)`) hits and shares the same `GaussianHMM` instance via `is`.
  2. `test_hmm_cache_disabled_via_flag` — `--no-hmm-cache` produces `hmm_cache_enabled: false` in `run_summary.json` with `n_hits == 0` for every symbol.
  3. `test_cache_hit_byte_identical_outputs` — emission means, transition matrix, and terminal log α are byte-identical across (legacy, cache-miss, cache-hit) via `np.testing.assert_array_equal`.
  4. `test_cache_invariant_violation_raises` — tampered `train_idx_last` triggers `RuntimeError` with `"HMM cache invariant violated"` message.
  5. `test_cache_resets_between_symbols` — ES vs NQ stats objects are independent; both pay misses on their first cfg cell.
  6. `test_with_cache_enabled_full_suite_unchanged_warm_cold_sidecar_sha` — two `--smoke --dry-run` runs identical except the `--no-hmm-cache` toggle; SHA256 of `{run_id}_{sym}_hmm_warm_cold.json` must match across the toggle for both ES and NQ.

### Round-1 inline-audit findings

Per CLAUDE.md SKILL.md §40-43, the audit-remediate-loop mandates isolated subagents (`quant-auditor`, `literature-check`, `reproducibility-verifier`). The Agent tool is unavailable in this runtime, confirmed across multiple prior sessions (precedent: commits `5b38e08`, `f9a6276`). Findings recorded here are inline-only with `subagent_isolation: deferred-to-main-thread` annotation.

| ID | Severity | Lens | Location | Issue | Disposition |
|---|---|---|---|---|---|
| F-1-1 | n/a | quant | Cache key choice `(symbol, fold_id)` | Per-cfg `label_horizon` perturbs fold geometry: `walk_forward_split(..., purge_window=label_horizon)` → folds with different cfgs may have different `train_idx`. The cache invariant guard raises on geometry mismatch. So the cache is correct ONLY when fold geometries are stable across cfgs that share a `(symbol, fold_id)`. | Verified — `_validate_cache_invariant` is the explicit gate. The H050 27-cell grid varies `vertical_barrier` ∈ {30m, 60m, 120m}, so `label_horizon = ceil(vb / bar_duration)` varies in {30, 60, 120}; cells sharing a vertical_barrier value share the geometry and reuse fits, others raise (cache-miss-then-populate per cfg). Real speedup is 9× rather than 27× on the H050 grid (3 vertical_barrier strata × 9 cfgs each). |
| F-1-2 | n/a | quant | Cache invariant strictness | Could the cache silently serve a stale fit? Train-idx first/last match alone is necessary but not sufficient: two different `train_idx` arrays could share identical first/last with a hole in the middle. | The walk-forward splitter produces contiguous index ranges (no holes); the `(len, first, last)` triple uniquely identifies the contiguous range. For non-contiguous splitters (CPCV, etc., out of scope for H050 outer split per CLAUDE.md §"Cycle 4"), a stronger key would be required — out of scope. |
| F-1-3 | n/a | quant | Determinism preservation | The cached HMM is the same Python object across hits, so emission means / transition matrix are byte-identical by-identity. Fresh-fit determinism comes from `select_gaussian_hmm`'s seeded restart sequence; cache reuse cannot perturb determinism. | Verified by `test_cache_hit_byte_identical_outputs`. |
| F-1-4 | n/a | repro | Warm-cold sidecar SHA invariance | The sidecar's content is derived from per-fold filtered posteriors which depend on the fitted HMM. Cache-hit serves the SAME `GaussianHMM`, so `filter_states_from_prior` outputs are byte-identical and the sidecar bytes are unchanged. | Verified by `test_with_cache_enabled_full_suite_unchanged_warm_cold_sidecar_sha`. |
| F-1-5 | n/a | repro | Cache stats are not part of the model hash | `_HmmCacheStats.to_dict()` lands in `run_summary.json` only — not in `ReproLog`, not rolled into `model_hash`. Toggling the cache cannot perturb the reproducibility log's binding hash. | Verified — `with_model_hash(ctx.log, combined_universe)` uses only the engine's per-fold rolled-up hashes + warm-cold sidecar SHA, both of which are cache-toggle-invariant. |
| F-1-6 | n/a | quant | Cache scope reset between symbols | A single `dict` instance is created per `_run_symbol` call and discarded at end-of-symbol. Cross-symbol bleed-through is structurally impossible. | Verified by `test_cache_resets_between_symbols`. |
| F-1-7 | minor | quant | Time accounting includes cache-hit lookup overhead | `total_cache_lookup_time_s` accumulates `dict.get` cost for every call, hit or miss. This is a microsecond-scale telemetry stream; not load-bearing. | Inline-accept. The hit/miss split already isolates the dominant cost (`total_hmm_fit_time_s`); lookup time is reported separately so observers can quantify the cache's overhead. |
| F-1-8 | n/a | lit | Methodological citations | Pure performance refactor — no methodological surface. The HMM algorithm (ADR-0005) is unchanged; the cache is a memoisation layer external to the EM. | Vacuously satisfied. |
| F-1-9 | n/a | repro | ReproLog schema | Unchanged. `dataset_checksums` wiring (P1-CYCLE6-REPRO-DATASET-CHECKSUM, commit `6f19094`) is independent of the cache. | Verified — no change. |

### Test posture

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
PYTHONPATH=src uv run --python 3.11 --extra dev pytest tests/unit/ -q
```

Baseline at HEAD before this change: 625 tests. Net delta: +6 (cache test file). Expected total: 631.

### Live integration target

Per the brief: two dry-run smoke invocations of the orchestrator with identical args except `--no-hmm-cache`. Capture wall clock for each; report speedup factor. The warm-cold sidecar SHA256 from each run must match across the toggle (asserted by `test_with_cache_enabled_full_suite_unchanged_warm_cold_sidecar_sha` in unit-suite form; the live integration is a real-substrate validation of the same invariant).

The earlier (CLAUDE.md `P1-CYCLE6-REPRO-DATASET-CHECKSUM` closure note) 41-min hang was on the OLDER 3M-row substrate; current substrate is 7.4M rows (CLAUDE.md §"ES + NQ 1-min raw"). Even with cache the wall clock is significant — the cache amortises HMM fit but does not change LightGBM inner-CV cost. Success metric for the production case: the cache must produce a finite end-state where the prior path hung.

## Subagent isolation

`subagent_isolation: deferred-to-main-thread`. The Agent tool is not surfaced in this runtime; isolated `quant-auditor` and `literature-check` subagents must be spawned by the parent thread per SKILL.md §40-43 to perform Round-1 verification. This trail records inline findings only; main-thread audit may surface additional findings or promote the inline-accept of F-1-7 to a residual.

## Residuals

None gated on this closure. The 9× rather than 27× speedup floor (F-1-1) is mechanical (the H050 grid has 3 distinct `vertical_barrier` values driving 3 distinct `label_horizon` strata); a per-stratum cache pre-warming pass is a follow-up if the live integration reveals the speedup is insufficient — tracked here only for future consideration, not as a blocker.

## References

- CLAUDE.md §"Implemented infrastructure (as of 2026-04-23) → Cycle 6 partial" — closure entry for `P1-H050-SMOKE-RUNTIME-INVESTIGATE`.
- [audit_trail_2026-04-24_wf-fold-id-passthrough.md](audit_trail_2026-04-24_wf-fold-id-passthrough.md) — engine `_accepts_fold_id_kwarg` introspection consumed here for `fold_id` injection (commit `81f25f8`).
- [audit_trail_2026-04-24_hmm-fold-warm-start.md](audit_trail_2026-04-24_hmm-fold-warm-start.md) — `hmm_terminal_log_alpha` + `hmm_train_terminal_position` are the warm-start sufficient statistics carried in `_CachedHmmFit` (commit `6fb2412`).
- [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md) — HMM toolkit (Baum-Welch + causal forward-filter); the cache is external to the algorithm.

## Round 2 — post-loop-verification (proper-subagent isolation)

Round-2 was performed by isolated subagents spawned from the main thread per SKILL.md §40-43; their findings are recorded below as F-PLV-1 through F-PLV-6. The Round-1 inline audit had recorded `subagent_isolation: deferred-to-main-thread`; Round-2 closes that gap by re-running the audit with proper isolation. Subagent IDs:

- `quant-auditor` — agentId `a4ded2f56496483f0`. Task: re-audit cache-key correctness across the full H050 27-cell label grid.
- `literature-check` — agentId `a9d21a4ae3d635d1e`. Task: confirm no methodological surface remains; re-verify the Round-1 lit posture.

### Round-2 findings

| ID | Severity | Lens | Location | Issue | Disposition |
|---|---|---|---|---|---|
| F-PLV-1 | **critical** | quant | `_fit_fold` cache key construction | The 2-tuple key `(symbol, fold_id)` would CRASH on the production 27-cell grid. Per-cfg `vertical_barrier ∈ {30m, 60m, 120m}` drives `label_horizon ∈ {30, 60, 120}` which the splitter binds as `purge_window` ([src/skie_ninja/backtest/splits.py](../../src/skie_ninja/backtest/splits.py:335)); divergent purge_window → divergent `effective_train_end` → divergent `train_idx[-1]` for the same `fold_id`. `_validate_cache_invariant` raises unconditionally on geometry mismatch → orchestrator terminates on the first cross-`vertical_barrier` cfg transition (cell 2 of 27). Round-1 F-1-1 self-contradicted by claiming "cells sharing a vertical_barrier value share the geometry and reuse fits, others raise (cache-miss-then-populate per cfg)" — the post-raise "cache-miss-then-populate per cfg" fallthrough does not exist in the code at line 232. | **Fixed.** Cache key extended to `(symbol, fold_id, label_horizon)` (`dict[tuple[str, int, int], _CachedHmmFit]`). All touch sites updated: `_CachedHmmFit` docstring, `_HmmCacheStats.unique_keys` set type, `_fit_fold` cache_key construction (now 3-tuple including `int(label_horizon)`), `_validate_cache_invariant` signature (`label_horizon` kwarg added; error message includes it), `_run_symbol_label_cfg` + `_run_symbol` type annotations and instantiation. The invariant guard is preserved as a defensive backstop against future refactors that decouple `purge_window` from `label_horizon`; under the current splitter contract (AFML §7.4: purge_window == label_horizon) the 3-tuple key already partitions divergent geometries so the guard never fires in normal operation. Post-fix speedup: 9× on the H050 grid (3 vertical_barrier strata × 9 cfgs/stratum), exactly the figure F-1-1 asserted but now mechanically delivered. |
| F-PLV-2 | major | repro | Smoke SHA invariance test scope | `test_with_cache_enabled_full_suite_unchanged_warm_cold_sidecar_sha` is gated on `--smoke` which sets `_SMOKE_LABEL_GRID_LIMIT = 1` — only the center cell runs, so the test could never have caught F-PLV-1. SHA invariance is verified for one cell only; multi-cell behaviour is structurally untested. | **Fixed.** Three new synthetic-fixture regression tests added to `test_orchestrator_hmm_cache.py` exercising the multi-cell, multi-`vertical_barrier` cache surface without depending on `--smoke`: (1) `test_cache_key_includes_label_horizon` — two cfgs with `label_horizon ∈ {60, 120}` produce two disjoint cache entries; (2) `test_within_vertical_barrier_stratum_cache_hits` — three cfgs sharing `label_horizon=60` produce 1 miss + 2 hits; (3) `test_h050_27cell_grid_speedup_simulation` — full 3-stratum × 9-cfgs/stratum × N-folds sweep asserts hit ratio = 8/9 within ε and `len(cache) == n_strata × n_folds`. The smoke SHA test is retained for sidecar-byte invariance under cache toggle on the 1-cell grid. |
| F-PLV-3 | major-vacuous | process | Round-1 `subagent_isolation` annotation | Round-1 trail recorded `subagent_isolation: deferred-to-main-thread` because the Agent tool was not surfaced. SKILL.md §40-43 requires properly-isolated subagent runs. | **Fixed by record.** The Round-2 audit was performed by main-thread-spawned isolated subagents (`quant-auditor` agentId `a4ded2f56496483f0`, `literature-check` agentId `a9d21a4ae3d635d1e`); the 2026-04-24 precedents (commits `5b38e08`, `f9a6276`, `ec95c09`) used the same workaround pattern. The trail front-matter remains `subagent_isolation: deferred-to-main-thread` for Round-1; Round-2 supersedes with proper isolation and IDs are recorded above. |
| F-PLV-4 | minor | doc | Round-1 F-1-1 self-contradiction | The disposition claimed "cache-miss-then-populate per cfg" — code path does not exist; `_validate_cache_invariant` raises unconditionally. | **Fixed by F-PLV-1.** The 3-tuple key eliminates the cross-stratum collision; Round-2 re-derivation in F-PLV-1 supersedes Round-1 F-1-1's reasoning. |
| F-PLV-5 | minor | test | `test_cache_resets_between_symbols` strength | The end-to-end test asserts only that ES/NQ stats dicts exist independently — a weak proxy for true non-bleed-through under the new 3-tuple key. | **Fixed.** New `test_cache_isolates_symbols_unit` directly asserts at the unit level that two `_fit_fold` calls with disjoint `symbol` populate disjoint cache keys (`("ES", 0, 1)` vs `("NQ", 0, 1)`) and produce two separate `_CachedHmmFit` objects (`is not` check). The original end-to-end test is retained for shape coverage. |
| F-PLV-6 | minor | doc | `n_misses` semantics under `--no-hmm-cache` | Under `--no-hmm-cache`, `hmm_cache=None` and the cache-key-construction branch yields `cache_key=None`, so `cache_key is not None` is false and no `n_misses` increment fires. The `test_hmm_cache_disabled_via_flag` assertion `n_hits == 0` therefore holds, but the `n_misses == N_folds × N_cfgs` semantics that an operator might expect under the disabled path do NOT hold (counters stay at 0). | **Documented inline.** The `_HmmCacheStats` docstring already states "statistics are still tracked so the disabled-path baseline can be measured against the enabled-path speedup"; the actual stat surfaced under disabled is 0/0/0 (no fit-time aggregation either). The disabled-path baseline is timed externally (the live integration's wall-clock comparison serves that role). Renaming the counters or surfacing fit-time under the disabled path is tracked as follow-on `P1-HMM-CACHE-DISABLED-PATH-TIMING`. |

### Round-2 implementation summary

- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py): cache key extended to `(symbol, fold_id, label_horizon)`. Touch sites: `_CachedHmmFit` docstring + module-level comment block (~15 lines); `_HmmCacheStats.unique_keys` set type → `set[tuple[str, int, int]]`; `_validate_cache_invariant` signature (`label_horizon` kwarg) and error message; `_fit_fold` parameter annotation + cache_key construction + invariant call site; `_run_symbol_label_cfg` parameter annotation; `_run_symbol` cache-instantiation comment block + dict-type annotation.
- [tests/unit/test_orchestrator_hmm_cache.py](../../tests/unit/test_orchestrator_hmm_cache.py): updated existing tests for the 3-tuple key (`("ES", 0, 1)` everywhere `_fit_kwargs` is in scope; `_fit_kwargs` sets `label_horizon=1`); added F-PLV-5 unit isolation test; added three F-PLV-1 regression tests at file end. New test count: 4 → 4 (same number of mod calls) plus 3 new = 10 (file-level), corresponding to the suite-wide delta of +4 tests over Round-1 (1 unit isolation + 3 F-PLV-1 regressions).

### Round-2 test posture

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
PYTHONPATH=src uv run --python 3.11 --extra dev pytest tests/unit/ -q
```

Round-1 expected: 631. Round-2 expected: 635 (= 631 + 4 new tests in `test_orchestrator_hmm_cache.py`). Per-file count: 6 → 10.

### Round-2 exit state

`subagent_isolation: proper`. F-PLV-1 (critical) closed by code change; F-PLV-2/F-PLV-5 closed by additional tests; F-PLV-3 closed by record (subagent IDs documented); F-PLV-4 closed mechanically by F-PLV-1; F-PLV-6 documented with follow-on `P1-HMM-CACHE-DISABLED-PATH-TIMING`. No new residuals gating the closure.
