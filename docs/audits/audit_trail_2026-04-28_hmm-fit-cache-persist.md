---
title: P1-HMM-FIT-CACHE-PERSIST — audit-remediate-loop trail
date: 2026-04-28
artifact: src/skie_ninja/models/regime/hmm_fit_cache.py + scripts/run_walk_forward.py + tests/unit/test_hmm_fit_cache.py
followup_id: P1-HMM-FIT-CACHE-PERSIST
exit_state: round-2 accept-with-residuals
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
operational_constraint: H050 prod-run-3 (PIDs 33640+36128) was running concurrently throughout this loop; no `-n auto` test runs; prod-run-3 verified alive after every commit-significant change
---

## Scope

Disk-persistent HMM-fit cache so a relaunch can repopulate the in-memory cache and skip recomputing the 11.2-hr cold fits observed in H050 prod-run-3. The in-memory cache (commit `1c85f5f` + `c2caa20`) does not survive process death; with prod-run-3 measuring single cold fits at +11 hr each, even one BSOD or hardware power loss could erase a full day of compute.

The patch adds `--resume-hmm-cache <prior_run_id>` CLI capability without modifying RunContext (which `P1-PER-SYMBOL-RESUME` would require). Each new cold fit is atomically pickled to `artifacts/runs/H050/<run_id>/_hmm_cache/` as soon as the fit completes.

## Round 1 — parallel quant + repro audit

Subagents (proper-isolated, main-thread-spawned):
- `quant-auditor` (`agentId ab4b6471bb7124d1d`) — 15 findings (F-1-1 critical, F-1-2..F-1-10 majors, F-1-11..F-1-15 minors).
- `reproducibility-verifier` (`agentId aa814f8a789609dc9`) — 6 findings (R-1 major, R-2..R-6 minors).

### Round-1 dispositions

| ID | Severity | Issue | Round-2 disposition |
|---|---|---|---|
| **F-1-1 / R-1** | **critical** / major | Pickle had no env coupling — git HEAD, python/numpy version, pickle protocol number all absent. Cross-HEAD or cross-env relaunch silently loaded pickles from a different code version. | **Fixed**: payload now records `git_head`, `producing_run_id`, `python_version`, `numpy_version`, `pickle_protocol`. New `check_provenance(payload, current_git_head)` returns mismatch list; resume path WARN-but-loads on drift (log surfaces operator's choice). |
| **F-1-2** | major | Bit-exact test only covered `log_emission_matrix`, not `filter_states` or `terminal_log_alpha` (the load-bearing fold-warm-start methods per ADR-0005). | **Fixed**: added `test_filter_states_round_trip_bit_identical` + `test_terminal_log_alpha_method_round_trip_bit_identical`. |
| **F-1-4** | major | Pickle non-deterministic at byte level when numpy arrays have non-contiguous layout (view-strided). Defeats the byte-identical-output regression contract of `--no-hmm-cache` mode. | **Fixed**: `_ensure_contiguous_params` rebuilds `HMMParams` with every numpy field via `np.ascontiguousarray` before pickling. New regression test `test_byte_deterministic_pickle_under_identical_fits` asserts SHA256 stability. |
| **F-1-5** | major | No test for `fit_result_` round-trip when non-None; only `_make_fitted_hmm` left it None. Pickle's None-vs-FitResult drift could silently load a stale FitResult schema. | **Fixed**: `test_fit_result_round_trips_when_non_none` constructs full `FitResult` (all 9 fields including 3 numpy arrays), saves, reconstructs, asserts every field round-trips. |
| **F-1-6** | major | `_load_hmm_fits_from_prior_run` had no guard against substrate drift between the prior run and the current run. Different `dataset_checksums` would silently inject fits computed on different data into the current pipeline. | **Fixed**: resume loader reads the prior run's `reprolog.json` `dataset_checksums` and compares to the current run's. Mismatch raises `ValueError` unless `--allow-substrate-drift` is passed (operator's explicit acceptance of the leakage risk). |
| **F-1-7** | major | `pickle.HIGHEST_PROTOCOL` is runtime-dependent; a Python 3.13 upgrade would silently produce pickles that 3.11/3.12 cannot read. | **Fixed**: pinned to `_PICKLE_PROTOCOL = 5` (max for Python ≥3.8; project's requires-python is `>=3.11,<3.13`). Encoded in `SCHEMA_VERSION = "hmm_fit_cache_v2_pickle5"` so a future bump is unambiguous. |
| **F-1-9** | major | `_persist_hmm_fit_to_disk` swallowed all exceptions including `pickle.PicklingError` from programmer errors. | **Fixed**: narrowed clause to `(OSError, PermissionError, pickle.PickleError)`. Programmer errors propagate so they surface at test time. |
| **F-1-10** | major | Cache-write was in-memory-first then disk. A kill between writes loses the disk artifact even though the in-memory dict was already populated. | **Fixed**: reversed order at both cache-write sites. Disk is the source of truth; in-memory is a within-process optimization. |
| **F-1-11** | minor | Non-existent prior run_id silently fell through to a fresh recompute. Operator typo masked for hours. | **Fixed**: raises `FileNotFoundError` unless `--allow-empty-resume` is passed. |
| F-1-3 | major (downgrade) | Atomic write doesn't fsync the parent directory. Power-loss between rename and journal flush leaves the rename rolled back. | **Documented in module docstring**: a power loss between rename and journal flush leaves the prior file in place (clean state — entry is *missing*, not corrupt). Severity downgraded to minor. |
| F-1-8 | major | Unbounded disk usage. No cleanup, no max-age, no per-run-id quota. | **Deferred**: tracked as `P1-HMM-FIT-CACHE-CLEANUP-POLICY`. Ceiling is operator-managed via filesystem usage. |
| F-1-12 | minor | Glob pattern `<SYM>__fold_*.pkl` would over-match a future sibling artifact. | **Fixed**: tightened to `<SYM>__fold_???__lh_????.pkl`. |
| F-1-13 | minor | No telemetry on resume effectiveness. | **Partial fix**: aggregate INFO log line now reports `attempted=N loaded=M skipped=K provenance_drift=L`. Per-key tracking deferred as `P1-HMM-FIT-CACHE-RESUME-TELEMETRY`. |
| F-1-14 | minor | `CachedFitRecord` and `_CachedHmmFit` field-set sync gap. | **Deferred**: tracked as `P1-CACHED-FIT-DATACLASS-CONSOLIDATE`. |
| F-1-15 | minor | Loose type contract for `train_idx_first/last` ints. | **Deferred** (no observable defect under current bounds). |
| R-2 | minor | No integrity checksum in pickle. | **Deferred**: `P1-HMM-FIT-CACHE-INTEGRITY-CHECKSUM`. |
| R-3 | minor | Windows MAX_PATH guard not present. | **Deferred**: paths well under 260 chars under typical worktree layout; tracked as `P1-HMM-FIT-CACHE-WINDOWS-LONGPATH-GUARD`. |
| R-4 | minor | `with_suffix('.pkl.tmp')` would shift semantics on a future stem-with-dot change. | **Fixed**: replaced with `path.parent / (path.name + ".tmp")`. |
| R-5 | minor | `CachedFitRecord` frozen-but-mutable note. | **Fixed in docstring**: explicit "treat as read-only" note added. |
| R-6 | minor | Resume telemetry didn't surface skipped/total counts. | **Fixed** (with F-1-13): aggregate INFO line shows attempted/loaded/skipped/provenance_drift. |

## Round 2 — internal verification

Per [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) §"Cap": Round-2 was a remediation-only round; no Round-2 fresh subagent audit (3-round cap reserved for future drift). Verification:

- **23/23 hmm_fit_cache tests green** (was 15; +8 new tests: filter_states + terminal_log_alpha + fit_result_ + byte-deterministic + 4 provenance tests).
- **76/76 targeted tests green** across hmm_fit_cache + orchestrator_progress_log + supervised_run + h050_config + paths + process_protection (sequential, no `-n auto` to avoid CPU contention with prod-run-3).
- **Orchestrator import sanity**: `_parse_args(['--resume-hmm-cache','test','--allow-substrate-drift','--allow-empty-resume'])` parses cleanly; new flags wired through.

## Operational safety

prod-run-3 (PIDs 33640 supervisor + 36128 child Python; H050 walk-forward, run_id `61d9eefbc06f4b4692d73f41f8a8dcac`, launched 2026-04-27 19:08 CT) ran throughout this audit-remediate-loop. The currently-running orchestrator imported all modules into RAM at process start; on-disk edits to `scripts/run_walk_forward.py` and `src/skie_ninja/models/regime/*.py` did NOT affect the running session. Verified by `tail -1 supervisor.jsonl` showing `status=running` after every commit-significant change. Telemetry samples accumulated normally (every 30s).

## Exit verdict

**`accept-with-residuals`** — patch is operationally sound for use as the relaunch checkpoint:

- Atomic-write semantics (tmp + fsync + replace) defended.
- Schema-version + pickle-protocol pinned.
- Env-coupling provenance fields persisted; cross-HEAD relaunch surfaces a WARNING.
- Substrate-drift guard via `dataset_checksums` comparison.
- Bit-exact reconstruction tested for `log_emission_matrix`, `filter_states`, `terminal_log_alpha`, `FitResult`.
- Byte-deterministic pickle output via `np.ascontiguousarray`.
- Disk-first / memory-second write ordering — disk is the source of truth.

**Residuals carried forward (non-blocking):**

- `P1-HMM-FIT-CACHE-CLEANUP-POLICY` (F-1-8) — disk-budget enforcement.
- `P1-HMM-FIT-CACHE-INTEGRITY-CHECKSUM` (R-2) — SHA256 over payload bytes for in-place corruption detection.
- `P1-HMM-FIT-CACHE-WINDOWS-LONGPATH-GUARD` (R-3) — Windows MAX_PATH defensive check.
- `P1-HMM-FIT-CACHE-RESUME-TELEMETRY` (F-1-13 partial) — per-key resume hit/miss tracking.
- `P1-CACHED-FIT-DATACLASS-CONSOLIDATE` (F-1-14) — merge `CachedFitRecord` and `_CachedHmmFit`.
- `P1-HMM-FIT-CACHE-PARENT-DIR-FSYNC` (F-1-3) — parent dir fsync after rename for full POSIX durability.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [src/skie_ninja/models/regime/hmm_fit_cache.py](../../src/skie_ninja/models/regime/hmm_fit_cache.py) — implementation.
- [tests/unit/test_hmm_fit_cache.py](../../tests/unit/test_hmm_fit_cache.py) — 23-test regression suite.
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) — orchestrator integration (`--resume-hmm-cache`, `--allow-substrate-drift`, `--allow-empty-resume` flags + persist + load helpers).
- [docs/decisions/ADR-0010-multi-hour-run-process-protection.md](../decisions/ADR-0010-multi-hour-run-process-protection.md) — Layer 3 design (resume-from-checkpoint).
- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — original HMM cold-fit cost diagnosis.
- [docs/audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md) — process-protection failure mode.
