---
title: P1-CFG-CHECKPOINT — per-cfg pickle checkpoint + resume
date: 2026-04-29
artifact: src/skie_ninja/backtest/cfg_checkpoint.py + scripts/run_walk_forward.py + tests/unit/test_cfg_checkpoint.py
followup_id: P1-CFG-CHECKPOINT
exit_state: round-1 inline-fix; targeted tests green
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
parent_diagnoses: prod-run-4 (cfg 20 OOM), prod-run-5 (cfg 24 OOM)
---

## Symptom

prod-run-5 (HEAD `d902440`, with the LGB inner-CV gc/del fix from
[audit_trail_2026-04-28_lgb-heap-fragmentation.md](audit_trail_2026-04-28_lgb-heap-fragmentation.md))
crashed with:

```
numpy._core._exceptions._ArrayMemoryError: Unable to allocate
28.2 MiB for an array with shape (3693681,) and data type float64
```

at `_run_symbol_label_cfg_body` line 1870 — the polars→numpy close-
column conversion at the start of cfg 24 (out of 27). RSS at crash:
~5.9 GB. Total runtime ~2 hours — mirrors prod-run-4's failure
profile despite the gc/del patch.

## Root cause

The gc/del fix in `_inner_cv_select_hp` reduced the LGB-Booster
contribution to fragmentation, moving the crash threshold from
cfg 20 → cfg 24 (~20% improvement). But fragmentation has multiple
sources beyond LGB:

- polars `get_column().to_numpy().astype(float64)` (~28 MiB per call,
  several per cfg)
- HMM cache pickle loads (each ~MB-scale numpy arrays)
- Label panel construction (numpy fancy indexing)
- Feature matrix slicing per fold

After ~24 cfgs of these compounding allocations, the Windows CRT
heap free-list is non-contiguous enough that even a 28 MiB request
fails — *despite* total committed memory being ~6 GB on a host with
much more RAM.

This is not a leak; it's structural. Any sufficiently long-running
process that does many polars→numpy + LGB cycles on Windows will hit
the same wall, regardless of how aggressive the gc passes are.

## Remediation: per-cfg disk checkpointing

Architectural shift: rather than fight the heap allocator, **bound
the work loss to one cfg** by persisting each cfg's `candidate` dict
to disk immediately after completion. A crash relaunches with
`--resume-cfg-checkpoint <prior_run_id>` and skips the cfgs whose
checkpoints exist.

Module: [src/skie_ninja/backtest/cfg_checkpoint.py](../../src/skie_ninja/backtest/cfg_checkpoint.py)

- `CfgKey` dataclass — canonical identity (sym, cfg_idx, pt_sl,
  vertical_barrier_seconds, volatility_lookback) with stable
  `filename_stem()` and `signature()` (SHA256).
- `save_checkpoint(...)` — atomic write (tmp + fsync + rename).
  Pickle protocol 5 (matches `hmm_fit_cache.py`). Payload records
  schema_version + git_head + producing_run_id + python_version +
  numpy_version + cfg_key_signature.
- `load_checkpoint(path)` — schema-version gate; raises ValueError
  on mismatch.
- `discover_checkpoints(run_dir)` — enumerates checkpoint dir;
  returns mapping `cfg_key_tuple → payload`. Skips corrupt or
  schema-mismatched pickles silently (defensive against truncated
  writes from a prior crash).
- `check_provenance(payload, *, current_git_head=None)` — returns
  mismatch strings. WARN-but-load semantics consistent with
  hmm_fit_cache.

Orchestrator wiring at
[scripts/run_walk_forward.py](../../scripts/run_walk_forward.py):

- New CLI flag `--resume-cfg-checkpoint <RUN_ID>`.
- `_run_symbol_body` reads the prior run's checkpoint dir at startup
  if the flag is set; populates `cfg_checkpoint_resume` dict.
- The cfg-loop short-circuits a `_run_symbol_label_cfg` call when a
  checkpoint exists for the cfg's key; logs `status=resumed` on the
  PROGRESS marker.
- After every successful cfg (cache miss, normal execution),
  immediately writes the candidate to the current run's checkpoint
  dir. Errors swallowed with WARNING (in-memory state preserved).

## Verification

- 12 new regression tests in
  [tests/unit/test_cfg_checkpoint.py](../../tests/unit/test_cfg_checkpoint.py):
  round-trip pickle, schema-version gate (rejects v0), atomic-write
  cleanup (no `.tmp` left behind), discover with multiple keys,
  empty dir → empty dict, corrupt pickle skipped, provenance no-drift,
  python_version drift, git_head drift, unknown-git both-sides skip,
  parent-dir auto-create.
- 129/129 across cfg_checkpoint + orchestrator-progress-log +
  hmm_fit_cache + em_kernels.
- The smoke-dry-run integration path exercises the new save+load
  loop on every cfg — confirms wiring is correct without crashing.

### Caught during wiring

The initial implementation referenced `ctx.run_id` directly; the
RunContext class actually holds run_id at `ctx.log.run_id`. The test
suite caught this (AttributeError) before commit. The corrected
attribute access is `ctx.log.run_id if (ctx is not None and ctx.log
is not None) else None`.

The `discover_checkpoints` initially caught
`(OSError, pickle.PickleError, ValueError)` but Python's pickle
raises `EOFError` for truncated input — which is not a subclass of
`PickleError`. Test surfaced this; widened catch to include
`EOFError`.

## Operational impact

- prod-run-5's HMM fits at
  `artifacts/runs/H050/7fd20f15c85d46d0b019a8eeceee9983/_hmm_cache/`
  are intact and resume-eligible via `--resume-hmm-cache`.
- prod-run-5's 23 completed inner-CV-LGB cfg results are **lost**
  (predates this patch).
- Next launch (prod-run-6) starts fresh on the cfg-checkpoint side
  but resumes HMM fits. Each cfg now writes its checkpoint
  immediately on completion, so any future crash's recovery cost is
  bounded to one cfg + the relaunch overhead.
- A relaunch loop driven by the supervisor wrapper can now bring a
  fragmentation-prone process to completion in O(n_crashes × 1) cfg
  recompute, instead of O(n_crashes × cfgs_per_crash) (the prior
  cost).

## What this does NOT solve

This patch bounds the *work loss* per crash, not the crash itself.
The fragmentation source is structural; future crashes are still
expected. The next architectural step
(`P1-CFG-SUBPROCESS-ISOLATION`) runs each cfg in a fresh subprocess,
making fragmentation impossible by construction. Cost: ~5–15 s
process startup × 54 cfgs ≈ 5–15 minutes total wall-clock overhead.
Deferred until the cfg-checkpoint path proves insufficient.

## Residuals carried forward

- `P1-CFG-SUBPROCESS-ISOLATION` — fresh subprocess per cfg for
  bulletproof heap isolation.
- `P1-CFG-CHECKPOINT-AUTO-RELAUNCH` — supervisor wrapper detects
  MemoryError + cfg-checkpoint flag set → auto-relaunch up to N
  attempts. Currently manual.
- `P1-CFG-CHECKPOINT-PARALLEL-EXECUTION` — once subprocess isolation
  exists, multiple cfgs could run concurrently across worker
  processes. Currently sequential.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [docs/audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md](audit_trail_2026-04-28_lgb-heap-fragmentation.md) — preceding gc/del patch.
- [src/skie_ninja/backtest/cfg_checkpoint.py](../../src/skie_ninja/backtest/cfg_checkpoint.py) — module.
- [src/skie_ninja/models/regime/hmm_fit_cache.py](../../src/skie_ninja/models/regime/hmm_fit_cache.py) — schema v3 pickle pattern; cfg_checkpoint mirrors its provenance fields.
- [logs/walk_forward_runs/h050_prod_run_2026-04-28T220010.summary.json](../../logs/walk_forward_runs/h050_prod_run_2026-04-28T220010.summary.json) — prod-run-5 crash classification.
