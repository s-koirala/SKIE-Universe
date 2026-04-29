---
title: H050 production walk-forward — five-failure retrospective
date: 2026-04-29
type: retrospective
status: live
applies_to: H050 (executing); H051 / H052a / H052b (queued); future hypotheses
covers_runs: prod-run-1 through prod-run-5 (2026-04-26 → 2026-04-29)
companion_directives: docs/decisions/ADR-0011-production-walkforward-runbook.md, research/_templates/production_run_runbook.md
---

# H050 production walk-forward — five-failure retrospective

## Purpose

Categorise the five H050 production walk-forward failures over 2026-04-26 → 2026-04-29 as **predictable-by-preflight** (could have been caught before launch with a finite, scriptable check) versus **structural / irreducible** (only a relaunch architecture or a deeper redesign avoids the failure). Output is the empirical basis for [ADR-0011](../decisions/ADR-0011-production-walkforward-runbook.md) and the H051/H052a/H052b runbook template at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md).

This is **not** a deliverable audit on H050 (the run is still executing under the relaunch loop). It is a process audit on the five-failure pattern itself.

## Failure inventory

Each row binds to a committed audit trail; any claim without a `[link]` is fabricated.

| # | Date | Mode | Run-id | Time-to-fail | Artifacts produced | Audit trail |
|---|---|---|---|---|---|---|
| 1 | 2026-04-26 | operator-killed for diagnosis | `e33eff2e1bb449f89b654a38bd80d660` | +180 min | 4 feature provenance JSONs; 0 per-fold; 0 aggregate | [audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) |
| 2 | 2026-04-27 | external kill — Windows Update reboot | `69626bcb90f445958ca61dbb560051f5` | +4h37m (reboot at 04:39 CT) | 6 PROGRESS lines; 0 fold; 0 aggregate | [audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](../audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md) |
| 3 | 2026-04-27 → 2026-04-28 | supervisor-cap exceeded | `61d9eefbc06f4b4692d73f41f8a8dcac` | +22h47m (24h cap) | 6/27 cfgs of one symbol's first fold; in-memory HMM cache (lost on exit) | [audit_trail_2026-04-28_hmm-em-numba-kernels.md](../audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md) §"Operational safety" |
| 4 | 2026-04-28 | OOM — LGB inner-CV heap fragmentation | `54d1369c354f4ee89a74b857cc1910fe` | ~2 hr; cfg 20/27 ES | 19 cfgs ES (in-memory only); HMM cache disk-persisted | [audit_trail_2026-04-28_lgb-heap-fragmentation.md](../audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md) |
| 5 | 2026-04-28 → 2026-04-29 | OOM — Windows-CRT structural fragmentation | `7fd20f15c85d46d0b019a8eeceee9983` | ~2 hr; cfg 24/27 ES | 23 cfgs (in-memory only); HMM cache disk-persisted | [audit_trail_2026-04-29_cfg-checkpoint.md](../audits/audit_trail_2026-04-29_cfg-checkpoint.md) |

Cumulative wall-clock burned across the five runs: ~34.4 hours of compute (sum of 3.0 + 4.6 + 22.8 + ~2 + ~2 hr per the run-by-run rows above), zero aggregate disposition artifacts written. The active relaunch-loop attempt (`f306cf79b1194154b38414fa6d6a64de`, launched 2026-04-29 16:24 CT under HEAD `7924f0a`) is the sixth attempt and the first to use both disk-persistent HMM cache + per-cfg checkpoint resume + the supervised relaunch loop ([scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh)).

## Categorisation

### Class A — predictable-by-preflight (3 of 5)

A failure is in this class iff **either** (i) a deterministic, scriptable, pre-launch check on the hypothesis configuration or host state would have flagged it, **or** (ii) a documented production-T-scale microbench artifact (existing at toolkit-build-time, not constructed retroactively from the failure) would have flagged the latency-envelope incompatibility before launch. Both surfaces are static relative to launch time: (i) is a YAML / registry probe; (ii) is a versioned file with a SHA256 + percentile-bootstrap CI. The relaxed definition (ii) is needed to keep run-3 in this class — its bottleneck only manifested at production-T and so a config-time check could not see it, but a microbench artifact would have.

#### Run-1: HMM `full`-covariance redundancy on 1-dim emissions

H050 binds emissions to a single feature (`r_tr.reshape(-1, 1)`, d=1). For d=1, `full` and `diag` covariance encode the SAME object — a single positive scalar per state — at identical likelihood and identical effective parameter count `k = N` per [_core.py:780-823](../../src/skie_ninja/models/regime/_core.py) `count_free_parameters`. The implementation paths differ only in constant factor (1.17–1.21× per-E-step at production T=3M, microbench [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py)).

**Why this was predictable.** The dimension-of-emission is fixed at config-load time. A 5-line static check on `H050.yaml`:

```python
if len(cfg.hmm.feature_columns) == 1 and "full" in cfg.hmm.covariance_type:
    raise ConfigError(f"covariance_type 'full' is mathematically redundant with 'diag' at d=1; "
                      f"either drop 'full' or implement model-class deduplication")
```

would have rejected the config at preflight. The eventual fix was model-class deduplication inside `select_gaussian_hmm` ([commit c2caa20](../../src/skie_ninja/models/regime/selection.py)), preserving the pre-reg grid verbatim, but the operational cost was 180 minutes of wall-clock + a 2-round audit-remediate-loop.

**What should have caught it earlier.** The HMM toolkit's preconditions (ADR-0005) were not checked against the H050 emission dimensionality at config time. A registry-of-redundancy preflight gate is a one-time engineering investment that protects every future hypothesis using the toolkit.

#### Run-2: Windows Update auto-reboot

Microsoft-Windows-Kernel-Power Event 109 ("Action: Power Action Reboot. Reason: Kernel API") fired at 04:39:20 CT while the orchestrator was running. The system was marked "Active" because no process had registered itself as a system-required workload via Win32 [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate). Full reboot-window evidence preserved at [logs/crash_evidence/system_events_2026-04-27_0435-0445.json](../../logs/crash_evidence/system_events_2026-04-27_0435-0445.json).

**Why this was predictable.** Two state checks would have caught the configuration:

1. **Pending-restart registry markers** (CBS RebootPending, WindowsUpdate Auto Update RebootRequired, PendingFileRenameOperations, Netlogon JoinDomain, Win11 OSUpgrade) — a 5-key registry probe answers "is a Windows reboot already pending?" deterministically.
2. **Active Hours coverage** — a 22-hour walk-forward run launched at 18:00 CT under default 8:00–17:00 Active Hours has a 100% probability of being killed by Windows Update during the run.

Both checks now exist at [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) (commit `4ae8ca7`, after the failure), but they were retrofitted from the post-mortem. The wake-lock at [src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py) is the canonical Microsoft-recommended pattern documented in [Power Awareness for Applications](https://learn.microsoft.com/en-us/windows/win32/power/power-awareness-for-applications); the API has existed since Windows XP. Not knowing it is the gap.

**What should have caught it earlier.** A Windows-host preflight catalogue keyed against the OS's documented power-management contract. ADR-0010 is the post-hoc codification; ADR-0011 makes it preflight-mandatory.

#### Run-3: HMM EM Python-loop bottleneck

Run-3 hit the supervisor's 24-hour cap with 6/27 cfgs of one symbol's first fold complete. Diagnosis pinned the bottleneck to per-timestep `scipy.special.logsumexp` calls inside Python-level forward / backward / forward-backward recursions at T≈3·10⁶ × N∈{2..4}. The numba `@njit` patch ([commit 341a94b](../../src/skie_ninja/models/regime/_em_kernels.py)) measured 400–1200× speedup on the same (T, N) grid; with that constant, total HMM-fit cost projects from ~100+ hours → ~30–60 minutes for a full run.

**Why this was Class-A under the relaxed definition (ii).** The forward-backward recursion is the canonical inner loop of Baum-Welch (Rabiner 1989 §III.A); a CPython for-loop over 3 million timesteps × ~30 EM iterations × 5–10 restarts × multiple folds is a textbook performance pathology. A *production-T-scale microbench artifact* on the HMM toolkit's `forward_log` / `backward_log` paths — at T=3M, BLAS pinned to 1, with percentile-bootstrap CI — would have given a single number ("scipy reference forward-backward cost = O(minutes per EM iteration)") that, multiplied by the H050 grid cardinality, projects to >>24 hr and is rejectable at the budget-feasibility gate (ADR-0011 gate 2). The microbench artifact landed *post-failure* at [scripts/bench/bench_em_kernels.py](../../scripts/bench/bench_em_kernels.py) ([commit 341a94b](../audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md)) and measured 400–1200× kernel-vs-scipy speedup, confirming that the same artifact built at toolkit-build-time would have flagged the issue.

A pure config-time check (definition (i)) cannot catch this. The bottleneck is a constant-factor property of the toolkit, not of the H050 YAML.

**What should have caught it earlier.** A microbench-readiness gate (ADR-0011 gate 2b) at hypothesis-design time: for each non-trivial inner loop in the model toolkit invoked by the hypothesis, a microbench artifact at production-T scale must exist with `git_head` + BLAS pinning + percentile-bootstrap CI. The artifact is a single-page JSON per model class. The H050 toolkit landed at 2026-04-23 (Cycle 3) without this artifact for the FB recursions; the artifact at [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py) does exist for the cov-type ratio (which is why run-1 had a measured fix path) but not for the toolkit's per-timestep cost at T=3M. The ADR-0011 gate 2b makes this artifact mandatory before launch.

### Class B — structural / architecturally-irreducible (2 of 5)

A failure is in this class iff no scriptable preflight check could have caught it; only a relaunch architecture or a structural code change avoids the failure.

#### Run-4: LGB inner-CV heap fragmentation OOM (cfg 20/27)

The crash signature was a 4.6 MiB allocation request denied at RSS=5.74 GB on a host with 32+ GB RAM ([audit_trail_2026-04-28_lgb-heap-fragmentation.md](../audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md)). Source: ~11,400 LightGBM Booster fit-predict cycles + ~6,000 polars-to-numpy fancy-indexing copies left the Windows CRT heap free-list non-contiguous. This is **not a memory leak** (total committed memory was stable at ~5.7 GB across the 2-hour run); it is **address-space fragmentation**, which Windows' user-space heap allocator does not coalesce aggressively.

**Why this was structural.** The fragmentation footprint depends on the *count* of fit-predict cycles × *substrate scale* × *Windows CRT allocator behaviour*. There is no static check on `H050.yaml` that maps `n_draws=200 × n_inner_folds=3 × n_cfgs=27` → "will fragment heap at cfg 20". The only way to detect the failure is to run it.

**Why even a runtime check fails.** RSS, working-set, and committed-memory all looked healthy at the moment of crash. Standard memory-pressure monitoring would not have predicted the next-allocation denial.

**Architectural response.** Two options:
- **Bound work loss to one cfg** via per-cfg disk checkpointing ([commit ee2112c](../../src/skie_ninja/backtest/cfg_checkpoint.py)) + relaunch loop ([commit 7924f0a](../../scripts/supervised_relaunch_loop.sh)). Accepts the crash; minimises wasted compute. **This is what the active run is doing.**
- **Subprocess isolation per cfg** (deferred follow-up `P1-CFG-SUBPROCESS-ISOLATION`) — fresh Python process per cfg means fragmentation cannot accumulate across cfgs. Added cost: ~5–15 sec startup × 54 cfgs ≈ 5–15 minutes total. This is the proper fix when the relaunch path proves insufficient.

The gc/del fix ([commit d902440](../../scripts/run_walk_forward.py)) did not solve the failure; it shifted the threshold from cfg 20 → cfg 24 (~20% improvement). That is the empirical signature of a structural bound, not a coding error.

#### Run-5: Windows-CRT fragmentation OOM (cfg 24/27)

Same root cause as run-4, different proximate trigger: a 28 MiB polars→numpy float64 conversion at the start of cfg 24. Confirmed structural by the gc/del patch's 20% threshold-shift not solving the failure.

**Architectural response.** Per-cfg disk checkpoint ([commit ee2112c](../../docs/audits/audit_trail_2026-04-29_cfg-checkpoint.md)) was the response that landed; it does not prevent the crash, it bounds the work loss per crash to one cfg, and a supervised relaunch loop drives the run to completion in O(n_crashes × 1 cfg recompute) instead of O(n_crashes × cfgs_per_crash).

## Cross-cutting observations

### O-1. Diagnostic instrumentation arrived late

The orchestrator progress logging ([commit 429f255](../../docs/audits/audit_trail_2026-04-26_orchestrator-progress-logging.md)) made the run-2 diagnosis legible in minutes rather than the 3-agent investigation that run-1 required. Until that patch, prod-run-1's stdout was 0 bytes after 180 minutes of wall-clock. Every multi-hour run *must* emit per-phase PROGRESS markers from the first commit, not retroactively.

### O-2. Disk-persistent caches arrived after they would have prevented the loss

The disk-persistent HMM cache ([commit 67c0419](../../docs/audits/audit_trail_2026-04-28_hmm-fit-cache-persist.md)) post-dated run-3, which lost ~22 hours of in-memory HMM fits to the supervisor cap. The per-cfg checkpoint ([commit ee2112c](../../docs/audits/audit_trail_2026-04-29_cfg-checkpoint.md)) post-dated run-5, which lost 23 cfgs of inner-CV-LGB to fragmentation OOM. The pattern is consistent: persistence layers are built reactively after a crash demonstrates the loss.

### O-3. Audit-remediate discipline held throughout

Every patch in the failure chain went through a proper-isolated audit-remediate-loop with parallel quant-auditor + reproducibility-verifier subagents. Quoting the run-1 diagnosis: *"Round-1 inline-audit by main thread (the implementing-agent runtime that launched the orchestrator) was inadequate"*. The discipline is sound. The gap is **upstream** — at hypothesis-design time, before the first launch.

### O-4. The pre-reg pattern is leak-protected, not stall-protected

Pre-registration prevents result-conditional method changes (good); it does not prevent infrastructure-conditional thrash (where the team is now). The five-failure pattern reveals that the gating checklist for "is this hypothesis launchable?" is missing from the project conventions.

## Predictable-vs-structural ratio

| Class | Count | Wall-clock burned | Recovery shape |
|---|---|---|---|
| A — predictable-by-preflight | 3 | ~30.4 hr (run-1: 3.0 hr; run-2: 4.6 hr; run-3: 22.8 hr) | Avoidable with config-time + microbench-readiness + Windows-host preflight gates |
| B — structural / irreducible | 2 | ~4 hr (run-4 + run-5) | Architecturally bounded by checkpointing + relaunch |

Three of five failures (60% by count, ~88% by wall-clock burned: 30.4 / 34.4) were preventable. The remaining two are now bounded by the cfg-checkpoint architecture; the residual cost is the relaunch overhead, which the active sixth attempt is paying down at the time of writing (11 NQ cfgs reloaded from prior run; ES already at 38 cfg-checkpoints on disk).

## Implications for H051, H052a, H052b

If the same pattern repeats per hypothesis, total stall cost across the four pre-registered Tier-2b hypotheses projects to ~30.4 hr × 4 ≈ ~120 hours of avoidable wall-clock plus four reactive audit-remediate-loops per failure mode. The runbook template at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md) inherits the Class-A failures as upfront preflight gates (including the microbench-readiness gate 2b for non-trivial toolkit inner loops) and the Class-B architecture as a default execution shape.

## Recommendations (binding once ADR-0011 is accepted)

1. **Hypothesis preflight is mandatory** before the first `python scripts/run_walk_forward.py` launch on real substrate. Captured in ADR-0011 §"Preflight checklist" as a 15-item gate (14 originally proposed + 1 microbench-readiness gate added in the Round-1 audit-remediate-loop).
2. **Production walk-forward runs use the supervised relaunch loop by default** ([scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh)), not direct orchestrator invocation. The supervisor wrapper enforces the runbook checklist programmatically.
3. **Each hypothesis spawns a runbook artifact** at design time, not after the first failure. Template at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md). Captured in ADR-0011 §"Per-hypothesis runbook" as a deliverable of pre-registration.
4. **The follow-up ledger is pruned** to retire follow-ups subsumed by ADR-0011's binding gates and to elevate the still-open architectural items (`P1-CFG-SUBPROCESS-ISOLATION`, `P1-PER-SYMBOL-RESUME`, `P1-WALK-FORWARD-PER-FOLD-CHECKPOINT`) to ADR-0011's residual-risk ledger. Captured in this memo's §"Follow-up ledger reconciliation".

## Follow-up ledger reconciliation

The current followups inline in [CLAUDE.md](../../CLAUDE.md) Cycle-6 paragraph mix four kinds of items:

1. **Closed (~closed-via commit cite)** — keep as historical record.
2. **Open and superseded by ADR-0011** — close with a "subsumed by ADR-0011 §<X>" note in the next CLAUDE.md edit. Candidates: `P1-ORCHESTRATOR-PROGRESS-LOGGING` (closed via 429f255 already; verify), `P1-HMM-CACHE-DISABLED-PATH-TIMING` (operational diagnostic now bounded to relaunch-loop telemetry), `P1-HMM-COV-DEDUP-AUDIT-MARKER`, `P1-BENCH-CITATION-TAG-PINNING`, `P1-BENCH-RUNTIME-STATUS-TIMESTAMP`.
3. **Open and structural** — promote to ADR-0011's residual-risk ledger: `P1-CFG-SUBPROCESS-ISOLATION`, `P1-CFG-CHECKPOINT-AUTO-RELAUNCH`, `P1-PER-SYMBOL-RESUME`, `P1-WALK-FORWARD-PER-FOLD-CHECKPOINT`, `P1-LGB-INNER-CV-RESULT-CHECKPOINT`, `P1-LGB-INNER-CV-SUBPROCESS-ISOLATION`.
4. **Open and orthogonal** — leave alone: items unrelated to the production-run path (`P1-LW2008-CALIBRATION-VS-PW2004`, `P1-DATABENTO-RIGHT-EDGE-EXTENSION`, `P1-OPDYKE-FULL-GMM`, etc.).

The actual CLAUDE.md edit lands together with ADR-0011's commit so the directive and the ledger are in one logical change.

## References

- [audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — run-1 diagnosis.
- [audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](../audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md) — run-2 diagnosis.
- [audit_trail_2026-04-27_adr-0010-multi-hour-process-protection.md](../audits/audit_trail_2026-04-27_adr-0010-multi-hour-process-protection.md) — wake-lock + supervisor + preflight implementation.
- [audit_trail_2026-04-28_hmm-em-numba-kernels.md](../audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md) — run-3 diagnosis + numba kernels.
- [audit_trail_2026-04-28_hmm-fit-cache-persist.md](../audits/audit_trail_2026-04-28_hmm-fit-cache-persist.md) — disk-persistent HMM cache.
- [audit_trail_2026-04-28_lgb-heap-fragmentation.md](../audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md) — run-4 diagnosis + gc/del.
- [audit_trail_2026-04-29_cfg-checkpoint.md](../audits/audit_trail_2026-04-29_cfg-checkpoint.md) — run-5 diagnosis + per-cfg checkpoint.
- [ADR-0010-multi-hour-run-process-protection.md](../decisions/ADR-0010-multi-hour-run-process-protection.md) — wake-lock + runbook + resume design.
- [runbook_walk-forward-launch-prep_2026-04-27.md](runbook_walk-forward-launch-prep_2026-04-27.md) — operator-facing pre-launch runbook.
- Rabiner, L. R. 1989. "A tutorial on hidden Markov models and selected applications in speech recognition." *Proc. IEEE* 77(2):257-286. §III.A — Baum-Welch EM forward-backward recursion.
- Microsoft Docs: [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) — Win32 wake-lock API.
- Microsoft Docs: [Kernel-Power Event 109](https://learn.microsoft.com/en-us/windows/win32/eventlog/event-categories) — system-initiated reboot transitions.
- Microsoft Learn: [Troubleshoot pool leaks](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-pool-leaks) — Windows kernel-pool fragmentation guidance applicable to user-space heap.
