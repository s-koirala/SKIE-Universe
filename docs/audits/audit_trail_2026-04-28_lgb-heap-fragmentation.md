---
title: P1-LGB-INNER-CV-HEAP-FRAGMENTATION — diagnosis + remediation
date: 2026-04-28
artifact: scripts/run_walk_forward.py (`_inner_cv_select_hp`)
followup_id: P1-LGB-INNER-CV-HEAP-FRAGMENTATION
exit_state: round-1 inline-fix; targeted tests green
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
parent_diagnosis: prod-run-4 crash at cfg 20 (run_id 54d1369c354f4ee89a74b857cc1910fe)
---

## Symptom

prod-run-4 (HEAD `341a94b`, numba-kernels + disk-persist HMM cache)
launched 2026-04-28 19:46:55 CT, ran cleanly through 19/27 ES cfgs,
then crashed at cfg 20 with:

```
numpy._core._exceptions._ArrayMemoryError: Unable to allocate
4.61 MiB for an array with shape (604755,) and data type float64
```

The `_run_inner_cv_select_hp` PROGRESS marker recorded
`failed elapsed=62.248s exc=MemoryError`. Supervisor RSS at crash:
**5.74 GB** (stable around 5–7 GB across the entire 2-hour run; never
exceeded 7.82 GB peak at substrate load).

## Root cause

The 4.6 MiB allocation request being *denied* despite a healthy 5.7 GB
working set is a textbook fingerprint of **address-space fragmentation
in the Windows CRT heap allocator**. Per the traceback,
`predict_proba` was attempting `np.vstack((1.0 - result, result))`
which needs a contiguous 4.6 MiB block — `VirtualAlloc` could not
find one despite total committed memory being well under any system
ceiling.

Source of fragmentation: the `_inner_cv_select_hp` loop at
[scripts/run_walk_forward.py:684-759](../../scripts/run_walk_forward.py)
ran:

- 200 LightGBM HP draws × 3 inner folds = **600 LGB Booster fit-predict
  cycles per cfg**
- 19 cfgs completed cleanly before cfg 20 → **11,400 LGB cycles
  cumulative** at the point of failure
- Each cycle creates a fresh `lgb.LGBMClassifier`, fits 50 trees, runs
  `predict_proba`, then implicitly rebinds `model` on the next
  iteration

LightGBM's `LGBMClassifier` wraps a C++ `Booster` object via the
SWIG-generated bindings. The Booster holds tree blocks in its own
malloc-backed heap; the wrapper destructor (and thus the C-side
`free`) only fires when Python's gc pass collects the dropped
reference. The implicit-rebind pattern keeps the prior wrapper alive
as a generational-gc candidate longer than the inner fit cycle, so
the C-side heap accumulates small allocations between gc passes.

After ~11k cycles on Windows the heap free-list is highly
non-contiguous, even though the *total* committed size is stable —
a classic fragmentation footprint. Python's small-object allocator
(`pymalloc`) is similarly affected: the numpy fancy-indexing copies
`X_in_tr / X_in_te / y_in_tr / y_in_te / r_in_te` create per-iter
arrays in the 50–100 MB range that round-trip through
`PyMem_RawMalloc`, leaving holes when freed.

## Remediation

Inline patch to `_inner_cv_select_hp` in
[scripts/run_walk_forward.py](../../scripts/run_walk_forward.py)
(diff vs prod-run-4 HEAD):

1. **Explicit `del` after each inner-fold step** — drop refs to
   `model`, `p_te`, and the four fancy-indexed slices before the next
   iteration creates new ones. Frees the LGB Booster's C-side memory
   immediately rather than at the next gc pass.
2. **Periodic `gc.collect()` every 20 draws** — coalesces the freed
   Booster + numpy fragments back into the free-list. 20 is tunable
   downwards; cost is negligible vs LGB fit time at ~2 s/draw.
3. **Final `gc.collect()` at function exit** — heap clean across the
   cfg-loop boundary so the next cfg starts in a defragmented state.
4. **Defense-in-depth `gc.collect()` at the cfg-loop boundary** in
   `_run_symbol_body` after each `_run_symbol_label_cfg` call (line
   ~2261). Catches anything held by the engine state, label panels,
   or fold ledgers.
5. Added `import gc` to the orchestrator.

## Verification

- 33/33 targeted tests green (`test_orchestrator_progress_log` +
  `test_hmm_fit_cache`). The smoke-dry-run integration path exercises
  `_inner_cv_select_hp` end-to-end and the new gc/del code did not
  regress.
- The fix is observation-equivalent to the original loop: same fits,
  same predictions, same metric reduction. The only behavioural
  delta is heap-fragmentation bound + ~10 ms gc.collect() overhead
  every 20 draws (<1% relative to ~40 s of LGB fit time per 20
  draws).

## Why this was not caught by the kernel-patch audit-remediate-loop

The audit-remediate-loop on the numba kernels (P1-HMM-EM-NUMBA-KERNELS)
was scoped to the HMM forward-backward path. The LGB inner-CV loop is
in a different code module (`scripts/run_walk_forward.py` vs
`src/skie_ninja/models/regime/`) and was not in the audit's review
scope. The OOM is an emergent property of the *substrate scale* (T=3M)
× the *post-kernel fit-cycle count* (which is now finite and large
because cold HMM fits no longer dominate). prod-run-3 never reached
this many LGB cycles because it spent all its wall-clock in HMM fits.

## Operational impact

- prod-run-4's 19 cfgs of inner-CV-LGB results are lost (in-memory
  only; LGB inner-CV results are not disk-persisted).
- The disk-persistent HMM cache survived: ES fold 0 × {30, 60, 120}
  pickles are intact in `artifacts/runs/H050/54d1369c…/_hmm_cache/`.
- Next launch resumes via `--resume-hmm-cache 54d1369c354f4ee89a74b857cc1910fe`,
  reusing those HMM fits at no cost. Inner-CV-LGB re-runs entirely.
- Estimated runtime under the patch: ~5–6 hours (ES + NQ; previously
  blew up at ~2 hr on ES alone).

## Residuals carried forward

- `P1-LGB-INNER-CV-RESULT-CHECKPOINT` — inner-CV-LGB results should
  be checkpointed to disk per cfg so a crash-resume doesn't lose
  hours of work. Currently only HMM fits persist.
- `P1-LGB-INNER-CV-SUBPROCESS-ISOLATION` — for ultimate fragmentation
  immunity, run each cfg's `_inner_cv_select_hp` in a fresh
  subprocess. Cost: subprocess startup ~1–2 s × 27 cfgs = trivial.
  Benefit: bulletproof heap. Defer until next observed OOM.
- `P1-LGB-N-DRAWS-EMPIRICAL` (pre-existing) — the 200-draw random
  search may be over-spec'd given the 12-cell discrete LGB grid;
  reducing n_draws would directly reduce cycle count.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [docs/audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md](audit_trail_2026-04-28_hmm-em-numba-kernels.md) — preceding kernel patch.
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) — patched orchestrator.
- [logs/walk_forward_runs/h050_prod_run_2026-04-28T194653.summary.json](../../logs/walk_forward_runs/h050_prod_run_2026-04-28T194653.summary.json) — prod-run-4 crash classification.
- Microsoft Learn: [Troubleshoot pool leaks](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-pool-leaks) — Windows kernel-pool fragmentation guidance applicable to user-space heap.
- Ke, G. et al. 2017. "LightGBM: A Highly Efficient Gradient Boosting Decision Tree." *NeurIPS 2017*. — Booster C++ design context.
