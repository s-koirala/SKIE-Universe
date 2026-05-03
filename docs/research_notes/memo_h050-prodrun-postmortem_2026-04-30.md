---
title: H050 production walk-forward — comprehensive post-mortem (runs 1–6 attempt-2)
date: 2026-04-30
type: postmortem
status: live
supersedes: docs/research_notes/memo_h050-prodrun-retrospective_2026-04-29.md
covers_runs: prod-run-1 through prod-run-6 attempt-2 (2026-04-26 → 2026-04-29)
companion_directives: docs/decisions/ADR-0011-production-walkforward-runbook.md, research/_templates/production_run_runbook.md
audit_loop: docs/audits/audit_trail_2026-04-30_h050-prodrun-postmortem.md
git_head_at_authoring: 50f44e3113d8ab4563db13e9e67376efe0033428
external_sources_retrieved: 2026-04-30
---

# H050 production walk-forward — comprehensive post-mortem

## 1. Purpose & supersession

This document is the canonical record of every H050 production walk-forward attempt to date. It supersedes [memo_h050-prodrun-retrospective_2026-04-29.md](memo_h050-prodrun-retrospective_2026-04-29.md) (runs 1–5 only) on three dimensions:

1. **Coverage extends to run-6 attempt-2** (2026-04-29 evening) — the OS-reboot incident — and to the 2026-04-30 closures (P1-WAKE-LOCK-BYPASS-INVESTIGATION, P1-PREFLIGHT-SCRIPT-TIMEOUT, P1-LGB-INNER-CV-RESULT-CHECKPOINT).
2. **Adds a value-of-information audit** on every infrastructure artifact built reactively across the failure chain. Each artifact is classified by necessity verdict (NEEDED / NEEDED-BUT-OVERBUILT / PREMATURE / DEFENSIVE / REDUNDANT / INSUFFICIENT-EVIDENCE) with commit-anchored evidence and counterfactual.
3. **Records primary-source corrections** to load-bearing project claims that were assumed but not previously verified against canonical documentation.

The 2026-04-29 retrospective remains valid as the empirical basis for [ADR-0011](../decisions/ADR-0011-production-walkforward-runbook.md); this post-mortem does **not** invalidate ADR-0011's preflight gating. It does identify framing/citation defects in ADR-0005 and ADR-0010 and one runtime-detection gap (UsoSvc Task Scheduler path) that require their own follow-up audit-remediate-loops.

This is **not** a deliverable audit on H050. The hypothesis itself remains executing; T_H050 has not been emitted; pre-registration disposition (design.md §10) remains pending. This is a process audit on the production-run path.

This post-mortem went through a 1-round audit-remediate-loop (parallel quant-auditor + literature-check + reproducibility-verifier subagents). Audit trail: [audit_trail_2026-04-30_h050-prodrun-postmortem.md](../audits/audit_trail_2026-04-30_h050-prodrun-postmortem.md).

## 2. Complete attempt inventory

The §2 contract: every quantitative claim in the inventory is anchored to a committed audit trail or a primary repro log. Narrative-only cells may rely on the cited audit trail's prose without an additional source.

| # | Date | Run-id | HEAD | Time-to-fail | Termination cause | Cumulative cfg-ckpts at end | Audit trail |
|---|---|---|---|---|---|---|---|
| 1 | 2026-04-26 ~15:07 CT | `e33eff2e1bb449f89b654a38bd80d660` | `1c85f5f` (HMM cache landed) | 180 min | operator-killed for diagnosis (HMM cold-fit stall) | 0/27 | [audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) |
| 2 | 2026-04-27 00:01 CT | `69626bcb90f445958ca61dbb560051f5` | pre-ADR-0010 | 4h38m (00:01:23 → 04:39:18 CT) | external kill — Microsoft-Windows-Kernel-Power Event 109; Windows Update auto-reboot | 0/27 | [audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](../audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md) |
| 3 | 2026-04-27 → 2026-04-28 | `61d9eefbc06f4b4692d73f41f8a8dcac` | post-ADR-0010 | 22h47m | supervisor cap exceeded (HMM EM Python-loop bottleneck) | 6/27 (in-memory only; lost on exit) | [audit_trail_2026-04-28_hmm-em-numba-kernels.md](../audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md) §"Operational safety" |
| 4 | 2026-04-28 | `54d1369c354f4ee89a74b857cc1910fe` | post-ADR-0010, pre-cfg-ckpt | ~2h | OOM at cfg 20/27 (LGB inner-CV heap fragmentation) | 19/27 (in-memory only) | [audit_trail_2026-04-28_lgb-heap-fragmentation.md](../audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md) |
| 5 | 2026-04-28 → 2026-04-29 | `7fd20f15c85d46d0b019a8eeceee9983` | post-gc/del | ~2h | OOM at cfg 24/27 (Windows CRT structural fragmentation; gc/del shifted threshold from cfg 20 → cfg 24, did not solve) | 23/27 (in-memory only) | [audit_trail_2026-04-29_cfg-checkpoint.md](../audits/audit_trail_2026-04-29_cfg-checkpoint.md) |
| 6 attempt-1 | 2026-04-29 16:24 CT | `f306cf79b1194154b38414fa6d6a64de` (relaunch base `338aac0a2d804e62b1ec54d36dba1a25`) | `7924f0a` (relaunch loop landed) | not separately logged in primary sources (transitioned into attempt-2) | (transitioned into attempt-2) | NQ 11/27 carried from base; ES 38 cfg-ckpts on disk | retrospective §"active sixth attempt" |
| 6 attempt-2 | 2026-04-29 19:25:43 CT | `e59171865ebb45559434250f3674a9e3` | `6bed0c2` (ADR-0011 binding) | 49 min (Kernel-Power Event 109 at 20:16:03) | external kill **despite acquired `ES_CONTINUOUS\|ES_SYSTEM_REQUIRED` wake-lock**; followed by user-initiated reboot at 20:40:01 (Event 1074) | NQ 11/27 unchanged | [audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md) + [audit_trail_2026-04-29_h050-prod-run-attempt2-recovery-loop.md](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-recovery-loop.md) |

**Cumulative wall-clock burned across attempts 1–5 + 6-attempt-2:** 3.0 + 4.633 + 22.78 + 2 + 2 + 0.817 ≈ **35.2 hours**. Run-6 attempt-1 wall-clock (~3 hr est., transitioned into attempt-2) is not included in this aggregate; reconstruction tracked under follow-up `P1-RUN6-ATTEMPT1-WALLCLOCK-RECONSTRUCT`. **Aggregate disposition artifacts written: zero.**

### Run-id artifact attestation

Per [CLAUDE.md](../../CLAUDE.md) §"Reproducibility (hook-enforced)", every run should write a ReproLog under `logs/reproducibility/<run_id>.json`. The 7 cited run-ids have the following on-disk attestation as of 2026-04-30:

| Run-id (prefix) | ReproLog | Fold artifacts | HMM cache | Cfg-checkpoints |
|---|---|---|---|---|
| `e33eff2e` (run-1) | present (sibling worktree) | 4 feature-provenance JSONs only | none (predates persist) | 0 |
| `69626bcb` (run-2) | not on disk (lost on Windows Update reboot before flush) | 0 | n/a | 0 |
| `61d9eefb` (run-3) | not on disk (lost on supervisor-cap exit) | 0 | in-memory only (lost) | 0 |
| `54d1369c` (run-4) | not on disk (lost on OOM) | 0 | partial (post-67c0419 disk-persist) | 0 (predates ee2112c) |
| `7fd20f15` (run-5) | not on disk (lost on OOM) | 0 | partial | 0 (predates ee2112c) |
| `f306cf79` (run-6 attempt-1) | not on disk (transitioned into attempt-2) | unknown | merged into base `338aac0a2d80...` cache | merged into base 11/27 NQ + 38 ES |
| `e59171865ebb45559434250f3674a9e3` (run-6 attempt-2) | partial in [logs/crash_evidence/walk_forward_2026-04-29_192543/](../../logs/crash_evidence/walk_forward_2026-04-29_192543/) | 0 new | resumed from base; 0 new | 0 new |

The §2 inventory is verified against committed audit trails; absolute completeness against `logs/supervised/`, `logs/reproducibility/`, and `artifacts/runs/H050/` is not verifiable from this checkout (those paths are gitignored). Future audit trails should snapshot `ls artifacts/runs/H050/` as evidence; tracked under `P1-RUNID-ARTIFACT-INVENTORY-AUDIT`.

### Active state as of 2026-04-30 morning

No live H050 process. NQ 11/27 + ES 38 cfg-checkpoints persist on disk under base run `338aac0a2d804e62b1ec54d36dba1a25` (full UUID resolved from [logs/crash_evidence/walk_forward_2026-04-29_192543/h050_prod_run_2026-04-29T192543.log](../../logs/crash_evidence/walk_forward_2026-04-29_192543/h050_prod_run_2026-04-29T192543.log) and [scripts/supervised_relaunch_loop.sh:17](../../scripts/supervised_relaunch_loop.sh)).

Three previously-blocking follow-ups closed today (commit `681c8c7`):
- `P1-LGB-INNER-CV-RESULT-CHECKPOINT` — per-draw checkpoint module + `--resume-cfg-checkpoint` flag.
- `P1-WAKE-LOCK-BYPASS-INVESTIGATION` — H-B (UsoSvc enforcement-deadline) classed *consistent with evidence and load-bearing candidate caller; not yet confirmed* per the recovery-loop audit-trail Q-2-1 disposition; H-A/H-C/H-E eliminated, H-D weakly refuted; defense layer = registry-pause helper + preflight read.
- `P1-PREFLIGHT-SCRIPT-TIMEOUT` — 60s → 180s + incremental JSON output.

`PER_LAUNCH_CAP_S` raised 10800 → 21600 (3 hr → 6 hr) in [scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh) (commit `234af2e`); fail-fast on preflight rc=3 added (commit `50f44e3`); LW2008 canonical migration (commit `f6a2a26`).

## 3. What went wrong, why, what to learn

### Run-1 — HMM `full`-covariance redundancy at d=1

**What:** 180 min wall-clock, zero per-fold artifacts. Operator killed for diagnosis after stdout produced 0 bytes for the duration.

**Why:** H050 binds emissions to a single feature (`r_tr.reshape(-1, 1)`, d=1). For d=1, `full` and `diag` covariance encode the SAME object — a single positive scalar per state. Likelihood is identical, parameter count `k = N` is identical. The implementation paths differ only in constant factor (1.17–1.21× per-E-step at production T=3M, microbench [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py)). The `full`-covariance fit was redundant computation × 5–10 restarts × cold-fit on T=3M.

**Lesson:** Redundancy detection at the hypothesis-toolkit interface is a config-time check, not a runtime one. A 5-line preflight gate on `H050.yaml` would have rejected the configuration before launch (ADR-0011 gate 4). The eventual fix preserved the pre-reg grid via model-class deduplication inside [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py); see [audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md](../audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md).

### Run-2 — Windows Update auto-reboot

**What:** Microsoft-Windows-Kernel-Power Event 109 at 04:39:18 CT after 4h38m of execution (00:01:23 → 04:39:18 CT, per [audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md:24](../audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md)). Reboot reason: "Action: Power Action Reboot. Reason: Kernel API". System marked "Active" because no process had registered itself as system-required workload.

**Why:** No call to `SetThreadExecutionState` had been made. The host's observed Active Hours window (8:00–17:00 CT, per the run-2 audit trail) excluded the entire 22-hour expected runtime; Windows Update enforced an automated restart at the next non-Active-Hours opportunity.

**Lesson:** Two state checks would have caught this — (i) pending-restart registry markers (CBS RebootPending et al.), (ii) Active Hours coverage versus expected runtime. Both now live in [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) (commit `4ae8ca7`), retrofitted from the post-mortem. **Important:** this only addresses the *path of detection*. The wake-lock acquired in subsequent runs does **not** prevent OS-initiated reboot — see Run-6 attempt-2 below and §5.1.

### Run-3 — HMM EM Python-loop bottleneck

**What:** 22h47m elapsed, supervisor 24-hour cap exceeded with 6/27 cfgs of one symbol's first fold complete. Per-cfg work was held in-memory only and lost on exit.

**Why:** Per-timestep `scipy.special.logsumexp` calls inside Python-level forward / backward / forward-backward recursions at T≈3·10⁶ × N∈{2..4} × 30–100 EM iterations × 5–10 restarts × multiple folds (per [audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md:71](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md)). The forward-backward recursion is the canonical inner loop of Baum-Welch (Rabiner 1989 §III.A — Solution to Problem 1). A CPython for-loop over 3 million timesteps is a textbook performance pathology. The numba `@njit` patch ([commit 341a94b](../audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md)) measured 400–1200× speedup on the same (T, N) grid (see §5.3 below for plausibility-of-magnitude caveat).

**Lesson:** A *production-T-scale microbench artifact* on the HMM toolkit's `forward_log` / `backward_log` paths — at T=3M, BLAS pinned to 1, with percentile-bootstrap CI — would have given a single number that, multiplied by the H050 grid cardinality, projects to >>24 hr and is rejectable at the budget-feasibility gate (ADR-0011 gate 2b). The artifact landed *post-failure*; gate 2b makes the artifact mandatory at toolkit-build time for future hypotheses.

### Run-4 — LGB inner-CV heap fragmentation OOM (cfg 20/27)

**What:** ~2 hr elapsed, OOM at cfg 20. Crash signature: 4.6 MiB allocation request denied at RSS=5.74 GB on a host with 32+ GB RAM.

**Why:** ~11,400 LightGBM Booster fit-predict cycles cumulative (per [audit_trail_2026-04-28_lgb-heap-fragmentation.md](../audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md)) plus per-cfg polars→numpy slicing for the inner-CV loop left the Windows CRT user-mode heap free-list non-contiguous. Per Microsoft documentation, the Low-Fragmentation Heap (LFH) only services allocations ≲16 KB ([Low-fragmentation Heap | Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/memory/low-fragmentation-heap), retrieved 2026-04-30). LightGBM training arrays / numpy buffers / polars→numpy conversions in H050 are dominantly above this cutoff; the back-end heap does not coalesce aggressively. The exact fraction of allocations exceeding 16 KB during H050 inner-CV is project-internal; a `tracemalloc` profile would tighten the claim. Tracked under follow-up `P1-LGB-INNER-CV-ALLOCATION-PROFILE`.

**This is fragmentation, not a leak.** Total committed memory was stable around 5–7 GB across the 2-hour run (peak 7.82 GB at substrate load, per the audit trail). Standard memory-pressure monitoring (RSS, working-set, committed-bytes) showed nothing wrong at the moment of crash.

**Lesson:** No static check on `H050.yaml` maps `n_draws=200 × n_inner_folds=3 × n_cfgs=27` → "will fragment heap at cfg 20". The structural fix is per-cfg subprocess isolation (deferred follow-up `P1-CFG-SUBPROCESS-ISOLATION`), which is the canonically documented CPython core-dev workaround for this exact pattern. The Python core-developer thread on bpo-19246 ("high fragmentation of the memory heap on Windows") was closed-rejected; Victor Stinner's documented workaround: *"Another option, maybe more complex, is to create a subprocess to process data, and destroy the process to release the memory. multiprocessing helps to implement that."* ([Python tracker issue 19246](https://bugs.python.org/issue19246), retrieved 2026-04-30).

### Run-5 — Windows-CRT fragmentation OOM (cfg 24/27)

**What:** ~2 hr elapsed, OOM at cfg 24. Same root cause as run-4, different proximate trigger (28 MiB polars→numpy float64 conversion at the start of cfg 24).

**Why:** The `gc`/`del` patch ([commit d902440](../../scripts/run_walk_forward.py)) shifted the failure threshold from cfg 20 → cfg 24 (~20% improvement) but did not solve the underlying fragmentation. The empirical signature of a 20% threshold shift under a heavyweight allocation reduction is consistent with a structural bound, not a coding error.

**Lesson:** Per-cfg disk checkpointing ([commit ee2112c](../audits/audit_trail_2026-04-29_cfg-checkpoint.md)) bounds work loss to one cfg; the supervised relaunch loop ([scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh)) drives the run to completion in O(n_crashes × 1 cfg recompute). This is a pragmatic bounded-loss alternative to the proper structural fix (subprocess isolation per cfg, additional cost ~5–15 min total).

### Run-6 attempt-2 — wake-lock does not address OS-initiated reboot at all

**What:** 49 min elapsed, Microsoft-Windows-Kernel-Power Event 109 at 20:16:03 CT *despite* acquired `ES_CONTINUOUS | ES_SYSTEM_REQUIRED` wake-lock at 19:26:45. Followed 24 min later by user-initiated reboot at 20:40:01 (Event 1074).

**Why — corrected framing (primary source).** The 2026-04-29 evening diagnosis labelled this a "wake-lock bypass" and pursued five hypotheses (H-A through H-E) about which Windows mechanism overrode the wake-lock. The post-mortem external-research pass (2026-04-30) finds that **`SetThreadExecutionState` was never documented to block reboots in the first place**. Per [Microsoft Learn — SetThreadExecutionState | Remarks](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) (retrieved 2026-04-30):

> *"The SetThreadExecutionState function cannot be used to prevent the user from putting the computer to sleep."*

The function's documented contract is to **reset the system idle timer** (`ES_SYSTEM_REQUIRED`) and to **reset the display idle timer** (`ES_DISPLAY_REQUIRED`). It addresses **idle sleep**, not OS-initiated reboot. An explicit `NtInitiatePowerAction` / `ExitWindowsEx`-class call by a service is outside the API's contract entirely. ADR-0010 §"Layer 1" framing — that the wake-lock prevents OS-initiated reboot — was a documentation defect on first principles; the API itself works as documented.

**The H-B leading-candidate framing also requires correction.** The recovery-loop audit-trail Q-2-1 disposition ([audit_trail_2026-04-29_h050-prod-run-attempt2-recovery-loop.md](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-recovery-loop.md)) explicitly forbade "leading candidate" framing — the os-reboot-bypass diagnosis classes H-B as *"consistent with evidence; load-bearing candidate caller; not yet confirmed"*. The 2026-04-30 CLAUDE.md ledger update (commit `681c8c7`) re-introduced "leading candidate" wording without re-running the audit-remediate-loop; that wording is corrected in this post-mortem.

**The "H-B = WUfB compliance deadline" reading also requires correction.** [WUfB compliance-deadline policies](https://learn.microsoft.com/en-us/windows/deployment/update/wufb-compliancedeadlines) explicitly override Active Hours (*"Once the effective deadline is reached, the device is forced to restart regardless of active hours."*) but require GPO (Pro/Enterprise/Education) or MDM enrollment. Windows 11 Home does not support GPO and the host is not MDM-enrolled. The reboot path is therefore the **internal UsoSvc Task Scheduler tree** (`\Microsoft\Windows\UpdateOrchestrator\Reboot_AC`, `Reboot_Battery`, `Universal Orchestrator Start`), which is **not** WUfB. The canonical mitigation for the UsoSvc path is to enumerate and temporarily disable the registered Reboot* tasks via `schtasks /Change /TN "\Microsoft\Windows\UpdateOrchestrator\Reboot_AC" /DISABLE` for the run window, in addition to the registry pause that already shipped 2026-04-30 (commit `681c8c7`).

**Lesson:** ADR-0010 §"Layer 1" must be reframed as "prevent idle sleep" (its actual contract), not "prevent reboot". The reboot path is addressed by Layer 2 (preflight refusing-to-launch when reboot is pending) plus a new layer (provisional Layer 5 — UsoSvc Task Scheduler disable for the run window — not yet implemented; new follow-up `P1-PREFLIGHT-USOSVC-TASK-DISABLE`, requires concurrent ADR-0010 amendment under `P1-ADR-0010-LAYER-AMENDMENT`). The empirical 5-hypothesis disposition in [audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md) remains valid as a process-of-elimination on *which* override fired; the corrected framing is that the wake-lock was never a sufficient defense.

## 4. Infrastructure value-of-information audit

For each artifact built reactively across the failure chain, this section records the necessity verdict, evidence, and counterfactual. Verdicts (six, exhaustive):

- **NEEDED** — failure mode is recurring; artifact prevents recurrence; no simpler alternative documented.
- **NEEDED-BUT-OVERBUILT** — failure mode is real; artifact resolves it; simpler/cheaper alternative was available but not taken.
- **REDUNDANT** — failure mode is real; another already-shipped artifact would have been sufficient.
- **PREMATURE** — failure mode would have been caught by an upstream gate that *already existed*; artifact is downstream cleanup.
- **DEFENSIVE** — built before any failure; counterfactual cannot be assessed empirically.
- **INSUFFICIENT-EVIDENCE** — primary-source data does not let me decide.

A separate dimension — **mis-framed-but-correctly-built** — is captured in §6 O-3 (literature-check coverage on infrastructure ADRs). The ADR-0010 wake-lock is an artifact in this dimension: NEEDED for the idle-sleep path, but ADR-0010 §"Layer 1" over-stated the API's contract. The verdict in this table reflects the artifact's necessity; the framing defect is tracked separately in §7.

| # | Artifact | Verdict | Evidence (commit / failure-anchor) | Counterfactual | Simpler alternative documented? | Re-exercised by subsequent failure? |
|---|---|---|---|---|---|---|
| 1 | `P1-ORCHESTRATOR-PROGRESS-LOGGING` (`429f255`) | **NEEDED** | Run-1 stdout 0 bytes after 180 min; Run-2 diagnosable in minutes | Without: every multi-hour run requires external py-spy + 3-agent investigation per failure | None; structured logging is baseline observability | Yes — runs 2, 3, 4, 5 all relied on PROGRESS markers for fast diagnosis |
| 2 | HMM cov-dedup at d=1 (`c2caa20`) | **NEEDED** | Run-1: redundant `full` cov fit × 5–10 restarts cold-fit on T=3M | Without: Run-1 stall recurs; pre-reg fidelity broken if YAML edited | Drop `full` from grid (rejected — pre-reg edit) or alias-deduplicate (accepted) | Not directly; downstream patches made cold-fit cost finite |
| 3 | ADR-0010 wake-lock (`4ae8ca7`) | **NEEDED** (for idle-sleep path; framing defect tracked separately under `P1-ADR-0010-LAYER-1-FRAMING-CORRECT`) | Run-2: 22-hr expected runtime crosses idle-sleep timer windows; without wake-lock, idle-sleep is the documented failure path | Without: idle-sleep-driven kill could occur on a 22+ hr run; documented protection persists | The API itself is the canonical mechanism | Re-exercised by run-6 attempt-2 — but the OS-initiated-reboot was outside the API's documented scope (§5.1); framing was over-stated, artifact worked as documented |
| 4 | ADR-0010 supervisor wrapper (`4ae8ca7`) | **NEEDED** | Run-2 motivated preflight enforcement; subprocess-boundary exit classification (per `_classify_exit` in `supervised_run.py`) is load-bearing for distinguishing operator-kill / external-kill / cap-exceeded — inline preflight cannot diagnose external kills | Without: orchestrator runs without external-kill diagnosis; supervisor-cap mechanism cannot exist | Inline preflight + `--max-runtime` could replace preflight + cap, but cannot replace exit classification (subprocess boundary required) | Yes — supervised the 24-hr cap on Run-3 as designed |
| 5 | ADR-0010 Windows-Update preflight (`4ae8ca7`) | **NEEDED** | Run-2: registry markers + Active Hours coverage check would have rejected the launch | Without: Run-2 reboot recurs identically | Static registry + clock math is minimal | Not in anger; runs 3–6 failed for orthogonal reasons |
| 6 | HMM cache disk-persist (`67c0419`) | **NEEDED** | Run-3 lost ~22 hr of in-memory HMM fits on supervisor cap (per [audit_trail_2026-04-28_hmm-em-numba-kernels.md:9](../audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md)); 11.2-hr cold fits observed (per [audit_trail_2026-04-28_hmm-fit-cache-persist.md:14](../audits/audit_trail_2026-04-28_hmm-fit-cache-persist.md)) | Without: every supervisor-cap-exceeded run loses all HMM compute | None — once cost-to-checkpoint is decided, pickling is the only viable form | Yes — runs 4, 5, 6 all benefit; `--resume-hmm-cache` is the active relaunch path |
| 7 | HMM EM numba kernels (`341a94b`) | **NEEDED** | Run-3 bottleneck; without the kernels, runs 4, 5, 6 never launch under 24-hr cap. Microbench-readiness gate (ADR-0011 gate 2b) did not exist at toolkit-build time, so the kernels were the unblocking dependency given actual project state. | Without: no recovery path under 24-hr supervisor cap | Microbench-readiness gate (post-hoc lesson, not available at the time) | Indirectly; deployed before Run-4. The patch is well-engineered. **Footnote — missing upstream gate:** had ADR-0011 gate 2b existed at toolkit-build (2026-04-23), the latency envelope would have been flagged before Run-1; the kernels would still have been built but proactively, not reactively. |
| 8 | LGB gc/del patch (`d902440`) | **NEEDED-BUT-OVERBUILT** | Run-4 → Run-5 threshold shift cfg 20 → cfg 24 (20% improvement, per [audit_trail_2026-04-29_cfg-checkpoint.md:30-31](../audits/audit_trail_2026-04-29_cfg-checkpoint.md)) | Without: Run-4-style failure recurs at slightly lower cfg | Subprocess isolation is the structural fix (deferred follow-up `P1-CFG-SUBPROCESS-ISOLATION`); per-cfg checkpointing (row 9) bounds the work loss without solving the cause | Negatively — Run-5 proved the patch did not solve the cause; the per-cfg checkpoint that landed 1 day later (commit `ee2112c`) is the bounded-loss expedient |
| 9 | Per-cfg checkpoint (`ee2112c`) | **NEEDED** | Bounds work loss to one cfg; relaunch resume capability | Without: each fragmentation crash loses entire cfg run; convergence O(n_crashes × cfgs_per_crash) | None — cfg-result persistence is required for any bounded-loss relaunch | Yes — actively used by run-6 supervised relaunch loop |
| 10 | Supervised relaunch loop (`7924f0a`) | **NEEDED** | Auto-relaunches `supervised_run.py` up to N times after fragmentation OOM, consolidating cfg-checkpoints + HMM pickle between attempts | Without: operator must manually detect crash + invoke `--resume-cfg-checkpoint` per crash | Subprocess isolation per cfg (deferred; lower complexity, same outcome) | Yes — drove run-6 attempt sequence |
| 11 | ADR-0011 production-runbook directive (`6bed0c2`) | **DEFENSIVE** | Codifies Class-A lessons from runs 1–5 as 15-item preflight gate | No prior failure caused by missing ADR-0011 gates; value is preventing future recurrence (H051+) | None — directive is governance, not enforcement | Not yet — H051+ are the test |
| 12 | Per-hypothesis runbook template (`6bed0c2`) | **DEFENSIVE** | Pre-registration deliverable for H051/H052a/H052b | H050 produced a post-hoc runbook (2026-04-27); template is preventive | None | Not yet |
| 13 | WU-pause helper (`681c8c7`, today) | **NEEDED** | Run-6 attempt-2 motivated belt-and-suspenders defense after preflight timed out at 60s ([audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md) F-2 — the primary preflight defense **failed open** in the actual incident; supervisor proceeded under `--allow-preflight-warn`) | Without: preflight failure-to-run leaves no defense against the UsoSvc path | Active Hours adjustment alone (extend AH to 24:00) — simpler when preflight runs to completion, but does not protect against preflight timeout failure mode | Not yet |
| 14 | Preflight 60s→180s + incremental JSON (`681c8c7`, today) | **NEEDED** | Empirical: prod-run-6 attempt-2 preflight at [logs/crash_evidence/walk_forward_2026-04-29_192543/...preflight.json](../../logs/crash_evidence/walk_forward_2026-04-29_192543/) timed out at 60s | Without: preflight times out on slow systems, false-positive rc=2 | Fixed 180s without incremental — but observability cost is minimal | Not yet — exercised on next H050 launch |
| 15 | LGB inner-CV per-draw checkpoint (`681c8c7`, today) | **NEEDED** | Bounds inner-CV recompute on cfg-resume to one draw; per [audit_trail_2026-04-28_lgb-heap-fragmentation.md](../audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md), 200 draws × 3 inner folds = 600 cycles per cfg at ~2 s/draw → ~20 min per cfg recompute without per-draw checkpoint vs ~6 s per single-draw recompute with it (~200× ratio at the per-draw grain). | Without: cfg resume re-runs full inner CV; relaunch loop convergence slows at the inner-CV grain | Accept the ~20 min per-cfg overhead — workable but slower | Not yet |
| 16 | LW2008 canonical migration (`f6a2a26`, today) | **NEEDED** | Audit during the migration found the user's `sharpe_diff_ci.py` had violations versus the project's audited canonical primitive (per ADR-0008); the migration deletes the non-canonical path and routes the H050 gate to the audited primitive. (Audit trail for the migration itself: see commit `f6a2a26` message; standalone audit-trail document tracked under `P1-LW2008-MIGRATION-AUDIT-TRAIL`.) | Without: H050 gate dispatches to unaudited path; evidence-bar disposition invalid | None — audit-anchored canonical primitive is the only acceptable form for the evidence bar | Not yet — H050 gate exercises it on next run |

**Verdict distribution (16 artifacts):**

| Verdict | Count | Artifacts |
|---|---|---|
| NEEDED | 12 | Progress logging, HMM cov-dedup, wake-lock (idle-sleep), supervisor wrapper, preflight, HMM cache, numba kernels, cfg-checkpoint, relaunch loop, WU-pause, preflight timeout/JSON, LGB per-draw checkpoint, LW2008 migration |
| NEEDED-BUT-OVERBUILT | 1 | LGB gc/del patch (transient bridge before structural fix) |
| DEFENSIVE | 2 | ADR-0011 directive, per-hypothesis runbook template |
| PREMATURE | 0 | (No artifact resolves a non-actual problem) |
| REDUNDANT | 0 | (No artifact is subsumed by another already-shipped) |
| INSUFFICIENT-EVIDENCE | 0 | (All 16 artifacts have measured or mechanism-defensible counterfactuals) |

(Counts: 12 + 1 + 2 = 15. Wake-lock is also tracked under `P1-ADR-0010-LAYER-1-FRAMING-CORRECT` for its documentation defect; the artifact-necessity verdict and the framing defect are orthogonal dimensions.)

## 5. External-source verification findings

Primary-source verifications. Sources retrieved 2026-04-30. All quotes are exact-match against the cited URL unless explicitly marked.

### 5.1 ADR-0010 Layer 1 framing — `SetThreadExecutionState` does not block reboots

[Microsoft Learn — SetThreadExecutionState | Remarks](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) (retrieved 2026-04-30):

> *"The SetThreadExecutionState function cannot be used to prevent the user from putting the computer to sleep."*

The function's documented behaviour for `ES_SYSTEM_REQUIRED`: "Forces the system to be in the working state by resetting the system idle timer." For `ES_DISPLAY_REQUIRED`: "Forces the display to be on by resetting the display idle timer." It addresses the **idle-sleep path**, not OS-initiated reboot. Microsoft does not document any behaviour that would block `NtInitiatePowerAction` / `ExitWindowsEx`-class calls — by design, the API contract is silent on the reboot path because the API does not address it.

**Implication:** ADR-0010 §"Layer 1" should be reframed as "prevent idle sleep during long-running compute". The reboot mitigation is fully on Layer 2 (preflight refusal) plus a new layer (provisional Layer 5 — UsoSvc Task Scheduler disable). New follow-up: `P1-ADR-0010-LAYER-1-FRAMING-CORRECT` (Layer 1 narrative); concurrent: `P1-ADR-0010-LAYER-AMENDMENT` (formal addition of provisional Layer 5).

### 5.2 H-B is not WUfB on Windows 11 Home

[Microsoft Learn — Enforce compliance deadlines with policies](https://learn.microsoft.com/en-us/windows/deployment/update/wufb-compliancedeadlines) (retrieved 2026-04-30):

> *"Once the effective deadline is reached, the device is forced to restart regardless of active hours."*

WUfB compliance-deadline policies are exposed via GPO (Pro/Enterprise/Education) or MDM (Intune/Autopatch CSP, namespace `Update/ConfigureDeadlineFor*`, see [Policy CSP - Update](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-update)). Windows 11 Home does not include the Group Policy Editor and is not MDM-enrolled by default; the GPO-edition matrix is documented at [Microsoft Learn — Group Policy and the Windows feature lifecycle](https://learn.microsoft.com/en-us/windows/whats-new/windows-11-requirements). The host is not MDM-enrolled.

The reboot path on this host is therefore the internal UsoSvc Task Scheduler tree — `\Microsoft\Windows\UpdateOrchestrator\Reboot_AC`, `Reboot_Battery`, `Universal Orchestrator Start` — which is **not** WUfB. The current preflight reads pending-restart markers (this is correct), and the registry pause helper (`pause_windows_update.ps1`) addresses the UsoSvc-scheduling state.

**Implication:** Extend the preflight to enumerate registered `\Microsoft\Windows\UpdateOrchestrator\Reboot*` tasks and `schtasks /Change /DISABLE` them for the run window, then re-enable on exit. New follow-up: `P1-PREFLIGHT-USOSVC-TASK-DISABLE`.

### 5.3 Plausibility-of-magnitude caveat on the 400–1200× numba speedup

The project's measured 400–1200× speedup of the numba `@njit` Baum-Welch kernels over `scipy.special.logsumexp`-based recursions is anchored to the in-house bench [logs/bench_em_kernels_2026-04-28.json](../../logs/bench_em_kernels_2026-04-28.json) and the audit trail [audit_trail_2026-04-28_hmm-em-numba-kernels.md](../audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md) F-1-5: *"measured speedup is 400–1200×, not 10–25× (hand estimate was off by ~50×)"*. The plausibility argument compounds two factors: (i) per-call dispatcher + numpy temporary-array allocation in `scipy.special.logsumexp` dominates the math at small N (N=2..4 hidden states); (ii) `@njit` over a tight inner loop with all kwargs hoisted out and parallel reduction within the inner dimension is constant-factor competitive with hand-written C. Neither factor has a single peer-reviewed benchmark at this magnitude.

The scipy issue tracker [scipy issue #9300](https://github.com/scipy/scipy/issues/9300) acknowledges *"logsumexp is a VERY slow function (takes about 75% of the program time)"* — the reporter's empirical observation, not a maintainer benchmark. [Pomegranate JMLR 2018](https://www.jmlr.org/papers/volume18/17-636/17-636.pdf) measures hmmlearn ~25 s vs pomegranate ~13 s single-threaded (~2× ratio) / ~4 s with 4 threads (~6× ratio) for 5 Baum-Welch iterations at T=1000, d=10, n_seq=100. These are cross-package factors at smaller (T, d) grain; not directly comparable to the project's T=3M, d=1, scipy-baseline measurement.

**No primary-source corroboration of the exact 400–1200× ratio is located.** The corroborating evidence is the project's own bench artifact + the indirect compounding argument above.

**Implication:** Treat the 400–1200× as project-internal pending cross-validation against pomegranate v1 (PyTorch) or dynamax (JAX) on the same substrate. New follow-up: `P1-NUMBA-EM-CROSS-VALIDATE`.

### 5.4 ADR-0005 AFML §7.4.1 citation error

ADR-0005 cites AFML §7.4.1 as the anchor for the K-step HMM warm-start formula. Per the publisher TOC ([ETH Library mirror](https://toc.library.ethz.ch/objects/pdf03/e01_978-1-119-48208-6_01.pdf), retrieved 2026-04-30; tier-4 corroboration from secondary AFML notes) of López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. ISBN 978-1-119-48208-6:

- **§7.4.1: "Purging the Training Set"** (page 105)
- §7.4.2: "Embargo" (page 107)
- §7.4.3: "The Purged K-Fold Class" (page 108)

§7.4.1 is about training-set purging in CV folds, not about HMM filter-state continuity. AFML contains no HMM chapter. The correct primary anchor for sequential HMM warm-starting is **Cappé, Moulines & Rydén (2005), *Inference in Hidden Markov Models*, Springer Series in Statistics**, or **Rabiner (1989) §III.C (Solution to Problem 3 — parameter re-estimation by Baum-Welch / EM)**. Cappé-Moulines-Rydén Chapter 10 ("EM-based Methods for Inference in HMM") is the canonical EM-for-HMMs treatment per secondary sources; section-level pinning for warm-starting across data segments is deferred to direct book access — tracked under follow-up `P1-CAPPE-2005-SECTION-PIN`.

**Implication:** ADR-0005 §"Fold-boundary state continuity" must retarget the AFML §7.4.1 reference to a primary HMM-inference source. The §7.4.1 anchor remains valid where it is genuinely load-bearing (purged-fold CV in [src/skie_ninja/backtest/](../../src/skie_ninja/backtest/)) but not for warm-start. New follow-up: `P1-ADR-0005-CITATION-CORRECT-WARM-START`.

### 5.5 Windows-CRT fragmentation diagnosis is canonically supported

[Low-fragmentation Heap | Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/memory/low-fragmentation-heap) (retrieved 2026-04-30):

> *"In the current implementation, the system does not use the LFH for allocations larger than approximately 16 KB, whether or not the LFH is enabled."*

[Python tracker issue 19246](https://bugs.python.org/issue19246) (closed/rejected, retrieved 2026-04-30): Victor Stinner's documented workaround: *"Another option, maybe more complex, is to create a subprocess to process data, and destroy the process to release the memory. multiprocessing helps to implement that."*

**Implication:** Per-cfg subprocess isolation (deferred follow-up `P1-CFG-SUBPROCESS-ISOLATION`) is the canonically documented CPython core-dev recommendation for this exact pattern. The 16 KB LFH cutoff is the load-bearing detail — most LightGBM/numpy/polars allocations sit above it and bypass LFH entirely. This last claim is project-internal pending a `tracemalloc` profile during cfg execution; tracked under `P1-LGB-INNER-CV-ALLOCATION-PROFILE`. `HeapCompact` cannot relocate live allocations and so cannot help with the dominant fragmentation pattern. The project's bounded-loss strategy (cfg-checkpoint + relaunch loop) is consistent with the literature; the proper structural fix remains subprocess isolation.

## 6. Cross-cutting observations

### O-1. Diagnostic instrumentation arrived late — recurrence

Already documented in 2026-04-29 retrospective §O-1; reinforced by run-6 attempt-2: the OS-reboot diagnosis was only legible because progress-logging existed. The pattern is consistent — instrumentation is the cheapest insurance and should land at toolkit-build time, not after the first failure.

### O-2. Persistence layers arrived after they would have prevented loss — recurrence

Already documented in 2026-04-29 retrospective §O-2. The 2026-04-30 LGB inner-CV per-draw checkpoint is another instance: it now exists, but no H050 run in the audit window was protected by it.

### O-3. External-source verification was missing from the audit-remediate-loop on infrastructure ADRs

Three of the audited claims (ADR-0010 Layer 1 contract, the H-B "WUfB compliance deadline" reading, ADR-0005 §7.4.1 citation) had not been verified against canonical Microsoft / publisher documentation before this post-mortem. Per the [CLAUDE.md](../../CLAUDE.md) ledger entry on ADR-0010 (commit `4ae8ca7`), the ADR-0010 audit-remediate-loop ran with quant-auditor + reproducibility-verifier only — a 2-agent pair, not a triad. ADR-0011 ran with the same 2-agent pair. No literature-check agent was invoked on either ADR.

The project's evidence hierarchy mandates "reproduce, don't paraphrase" but the audit-remediate-loop's literature-check agent had been invoked on hypothesis-design documents and statistical primitives (HAC, Sharpe CI, LW2008, SPA), not on infrastructure ADRs. New process directive: extend the audit-remediate-loop to require literature-check on every ADR that cites an external API contract or published method. Captured as `P1-AUDIT-LOOP-LITCHECK-ON-ADRS`.

### O-4. Audit-remediate discipline held throughout — confirmed with one regression

Every patch in the failure chain went through a proper-isolated audit-remediate-loop with parallel quant-auditor + reproducibility-verifier subagents. The discipline is sound. The exceptions: (a) infrastructure ADRs lacked literature-check coverage (§O-3); (b) the 2026-04-30 CLAUDE.md ledger update introduced "H-B confirmed leading candidate" wording in commit `681c8c7` without re-running the audit-remediate-loop, contradicting the recovery-loop trail's Q-2-1 disposition (corrected in this post-mortem §3 Run-6 attempt-2 above). Both patterns are tracked under `P1-AUDIT-LOOP-LITCHECK-ON-ADRS` (a) and `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` (b).

### O-5. The pre-reg pattern is leak-protected, not stall-protected — confirmed

Already documented in 2026-04-29 retrospective §O-4; reinforced by the run-6 attempt-2 OS-reboot diagnosis (a stall, not a leak; pre-reg fidelity intact throughout). The gating checklist for "is this hypothesis launchable?" remains the load-bearing addition.

### O-6. The run-6 attempt-2 5-hypothesis disposition is *narrowed*, not preserved, on the corrected framing

The 2026-04-29 evening 5-hypothesis disposition (H-A through H-E) eliminated H-A/H-C/H-E, classed H-B as *consistent with evidence; load-bearing candidate caller; not yet confirmed* (per [audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md:82](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md)) and H-D as weakly refuted. This was correct *given the assumed premise* that the wake-lock should have prevented the reboot.

With the corrected premise (the wake-lock does not address that path at all, §5.1), the disposition is **narrowed**, not preserved. Under the new framing the question is "which OS service initiated the reboot?", whose answer set is restricted to {UsoSvc / scheduled task, manual user, hardware} — a smaller set than the original "which override fired?". H-A (Smart Active Hours dynamic computation) is **structurally moot** rather than empirically eliminated under the new framing — Smart AH governs WU's *reboot timing*, not its decision to reboot, so even an active Smart-AH state would not initiate the reboot. H-E (hardware) is still eliminated; H-D (manual user) is still weakly refuted. H-B (UsoSvc internal Task Scheduler) remains the load-bearing candidate caller on the new framing for a different reason: the WUfB-deadline override path is not available on Home edition (§5.2), so the only documented OS service that would initiate a reboot in this state-space is the UsoSvc Task Scheduler tree.

**H-B falsification criterion under the new framing:** H-B is falsified if the `Microsoft-Windows-USO-CoreWorker/Operational` channel for the 20:14:00–20:16:30 window contains no UsoSvc / MoUsoCoreWorker reboot-orchestration call (i.e., no `InitiateSystemShutdownEx`-equivalent trace from a UsoSvc-owned process); H-B is confirmed if such a trace is present same-second as Kernel-Power 109. The trace channel probe is queued under `P1-USO-TRACE-CHANNEL-PROBE`.

## 7. Required remediation actions

| ID | Description | Priority | Anchor |
|---|---|---|---|
| `P1-ADR-0010-LAYER-1-FRAMING-CORRECT` | Reframe ADR-0010 §"Layer 1" as "prevent idle sleep" not "prevent OS-initiated reboot"; cite SetThreadExecutionState Remarks verbatim | BLOCKING for next H051+ launch | §5.1 |
| `P1-ADR-0010-LAYER-AMENDMENT` | Amend ADR-0010 to formally register a Layer 5 (UsoSvc Task Scheduler disable for run window) once `P1-PREFLIGHT-USOSVC-TASK-DISABLE` lands | BLOCKING for next H051+ launch | §3 Run-6 attempt-2 + §5.2 |
| `P1-PREFLIGHT-USOSVC-TASK-DISABLE` | Extend `check_windows_update.ps1` (or new helper) to enumerate `\Microsoft\Windows\UpdateOrchestrator\Reboot*` tasks and `schtasks /Change /DISABLE` for run window; re-enable on exit | BLOCKING for next H050 launch | §5.2 |
| `P1-ADR-0005-CITATION-CORRECT-WARM-START` | Retarget AFML §7.4.1 reference for HMM warm-start to Cappé-Moulines-Rydén 2005 (Chapter 10 — EM-based Methods for Inference in HMM) and/or Rabiner 1989 §III.C (Solution to Problem 3 — parameter re-estimation); preserve §7.4.1 anchor for purged-fold CV. | non-blocking | §5.4 |
| `P1-CAPPE-2005-SECTION-PIN` | Pin the specific section in Cappé-Moulines-Rydén 2005 Chapter 10 covering warm-starting EM across data segments; requires direct book access | non-blocking; depends on `P1-ADR-0005-CITATION-CORRECT-WARM-START` | §5.4 |
| `P1-NUMBA-EM-CROSS-VALIDATE` | Cross-validate the 400–1200× numba speedup against pomegranate v1 (PyTorch) or dynamax (JAX) on the same substrate; treat as project-internal until then | non-blocking | §5.3 |
| `P1-AUDIT-LOOP-LITCHECK-ON-ADRS` | Extend audit-remediate-loop to require literature-check on every ADR that cites an external API contract or published method | non-blocking process directive | §O-3 |
| `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` | Codify that CLAUDE.md ledger updates that re-frame audit-trail dispositions must themselves go through audit-remediate-loop (caught the 2026-04-30 "H-B leading candidate" regression) | non-blocking process directive | §O-4 |
| `P1-USO-TRACE-CHANNEL-PROBE` | Probe `Microsoft-Windows-USO-CoreWorker/Operational` channel for 20:14:00–20:16:30 window to falsify or confirm H-B | non-blocking diagnostic | §O-6 |
| `P1-CFG-SUBPROCESS-ISOLATION` | (Pre-existing) Implement per-cfg subprocess isolation as the structural fix for Windows CRT heap fragmentation; current cfg-checkpoint + relaunch is the bounded-loss alternative | non-blocking pending relaunch convergence | §5.5 + retrospective §B-4 |
| `P1-LGB-INNER-CV-ALLOCATION-PROFILE` | `tracemalloc` profile during H050 cfg execution to confirm the project-internal claim that "most LightGBM/numpy/polars allocations sit above 16 KB" | non-blocking | §5.5 |
| `P1-LW2008-MIGRATION-AUDIT-TRAIL` | Commit a standalone audit trail document for commit `f6a2a26` (LW2008 canonical migration) so the §4 row 16 evidence anchor resolves to a trail file rather than a commit message | non-blocking documentation hygiene | §4 row 16 |
| `P1-RUN6-ATTEMPT1-WALLCLOCK-RECONSTRUCT` | Reconstruct run-6 attempt-1 wall-clock from `supervised_relaunch_loop` logs and amend the cumulative figure in §2 | non-blocking | §2 |
| `P1-RUNID-ARTIFACT-INVENTORY-AUDIT` | Future audit trails snapshot `ls artifacts/runs/H050/` as evidence; closes the run-id artifact-traceability gap surfaced by R-1 in this post-mortem's audit trail | non-blocking | §2 attestation table |
| `P1-NARRATIVE-DOC-FRONTMATTER-SCHEMA` | Define minimal frontmatter schema for `type: postmortem|retrospective|memo` with `git_head_at_authoring` + `external_sources_retrieved` fields | non-blocking | post-mortem frontmatter |
| `P1-MICROBENCH-READINESS-GATE` | (Subsumed by ADR-0011 gate 2b) Make production-T-scale microbench artifact mandatory at toolkit-build time for non-trivial inner loops | (already binding) | retrospective §A-3 |

## 8. Implications for H051, H052a, H052b

The 2026-04-29 retrospective projected ~120 hours of avoidable wall-clock across H051/H052a/H052b if the same pattern repeats. With the 2026-04-30 closures and the new ADR-0010-Layer-1 / UsoSvc-task / ADR-0005-citation remediation items, the avoidable burn is reduced further. The runbook template at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md) inherits the corrected ADR-0010 framing as a Layer-2-mandatory gate.

The structural Class-B failures (Windows CRT fragmentation) are bounded by per-cfg checkpoint + relaunch loop, which now ship before any H051+ launch. Subprocess isolation remains the proper structural fix and is tracked under `P1-CFG-SUBPROCESS-ISOLATION`.

## 9. References

### Project-internal

- [memo_h050-prodrun-retrospective_2026-04-29.md](memo_h050-prodrun-retrospective_2026-04-29.md) — superseded retrospective (runs 1–5).
- [audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — run-1.
- [audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](../audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md) — run-2.
- [audit_trail_2026-04-27_adr-0010-multi-hour-process-protection.md](../audits/audit_trail_2026-04-27_adr-0010-multi-hour-process-protection.md) — wake-lock + supervisor implementation.
- [audit_trail_2026-04-28_hmm-em-numba-kernels.md](../audits/audit_trail_2026-04-28_hmm-em-numba-kernels.md) — run-3 + numba kernels.
- [audit_trail_2026-04-28_hmm-fit-cache-persist.md](../audits/audit_trail_2026-04-28_hmm-fit-cache-persist.md) — disk-persistent HMM cache.
- [audit_trail_2026-04-28_lgb-heap-fragmentation.md](../audits/audit_trail_2026-04-28_lgb-heap-fragmentation.md) — run-4 + gc/del.
- [audit_trail_2026-04-29_cfg-checkpoint.md](../audits/audit_trail_2026-04-29_cfg-checkpoint.md) — run-5 + per-cfg checkpoint.
- [audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md) — run-6 attempt-2 diagnosis.
- [audit_trail_2026-04-29_h050-prod-run-attempt2-recovery-loop.md](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-recovery-loop.md) — recovery-loop infrastructure.
- [audit_trail_2026-04-30_h050-prodrun-postmortem.md](../audits/audit_trail_2026-04-30_h050-prodrun-postmortem.md) — this post-mortem's audit-remediate-loop trail.
- [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md), [ADR-0010](../decisions/ADR-0010-multi-hour-run-process-protection.md), [ADR-0011](../decisions/ADR-0011-production-walkforward-runbook.md).

### External (primary sources, retrieved 2026-04-30)

- Microsoft Learn: [SetThreadExecutionState function (winbase.h)](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate).
- Microsoft Learn: [Low-fragmentation Heap (Win32 apps)](https://learn.microsoft.com/en-us/windows/win32/memory/low-fragmentation-heap).
- Microsoft Learn: [HeapCompact function (heapapi.h)](https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapcompact).
- Microsoft Learn: [Enforce compliance deadlines with policies (WUfB)](https://learn.microsoft.com/en-us/windows/deployment/update/wufb-compliancedeadlines).
- Microsoft Learn: [Policy CSP - Update](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-update).
- Microsoft Learn: [Group Policy and the Windows feature lifecycle](https://learn.microsoft.com/en-us/windows/whats-new/windows-11-requirements) (for the GPO-edition support matrix).
- Python tracker: [Issue 19246 — Windows heap fragmentation](https://bugs.python.org/issue19246).
- SciPy: [Issue #9300 — Faster logsumexp request](https://github.com/scipy/scipy/issues/9300).
- hmmlearn: [Changelog](https://hmmlearn.readthedocs.io/en/latest/changelog.html).
- Schreiber, J. (2018). "pomegranate: Fast and Flexible Probabilistic Modeling in Python." *JMLR* 18(164):1-6. [PDF](https://www.jmlr.org/papers/volume18/17-636/17-636.pdf).
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. ISBN 978-1-119-48208-6. [TOC PDF mirror, ETH Library](https://toc.library.ethz.ch/objects/pdf03/e01_978-1-119-48208-6_01.pdf).
- Cappé, O., Moulines, E., Rydén, T. (2005). *Inference in Hidden Markov Models*. Springer Series in Statistics. ISBN 978-0-387-40264-2.
- Rabiner, L. R. (1989). "A tutorial on hidden Markov models and selected applications in speech recognition." *Proc. IEEE* 77(2):257-286. doi:[10.1109/5.18626](https://doi.org/10.1109/5.18626).

---

## Appendix — H053 build-session findings (appended 2026-05-01)

The autonomous Cycles 7-10 H053 build sequence (2026-04-30 → 2026-05-01) ran through to a provisional `archive(null, descriptive-mediation-only)` Stage-3 disposition that was REVERSED on user-prompted post-hoc diagnosis. Like the H050 prod-run sequence, the H053 build accumulated a meaningful defect ledger that is canonically appended here for cross-hypothesis discipline. Each finding is given a verdict using the same convention as §4 above.

### A. Setup defects that affected the H053 disposition (DEFECT)

| # | Defect | Where | Impact | Fix path |
|---|---|---|---|---|
| H053-D1 | **Daily-block strict `n_rth_bars == 405` gate truncates train fold** by 65% | [src/skie_ninja/features/h053/daily.py](../../src/skie_ninja/features/h053/daily.py):297 | Stage-2 + Stage-3 train fold dropped from ~1900 → ~178 sessions on the IS fold; sample-to-feature ratio ~4 → negative inner-CV R² → spurious archive(null) verdict | `P1-H053-DAILY-405-GATE-RECONCILE` (BLOCKING-BEFORE-NEXT-STAGE-3): relax to `>= 404` with `# justify:` documenting substrate's pre-2022 missing-bar pattern + regression test; OR substrate-side fix to identify + add the missing pre-2022 RTH bar. Per-year RTH bar distribution: median 404 bars/session pre-2022, 405 from 2022 onward |
| H053-D2 | **Polars i8 overflow in `dt.hour() * 60` arithmetic** for `_h ≥ 12` | [scripts/run_h053_stage0_hks_sanity.py](../../scripts/run_h053_stage0_hks_sanity.py) initial draft | Stage-0 HKS sanity initially produced "ES bin returns: 350 rows across 89 sessions, 4 unique bins" instead of the expected 13 bins × ~2700 sessions | Fixed in-loop: explicit `.cast(pl.Int32)` on `_hour_et` / `_minute_et` at extraction; locked by regression test [tests/unit/test_h053_stage0_hks_sanity.py](../../tests/unit/test_h053_stage0_hks_sanity.py) `TestBinAssignmentNoIntOverflow` |
| H053-D3 | **Polars `Datetime("us", "UTC")` substrate vs `Datetime("ns", "UTC")` feature output dtype mismatch** in `join` | Cycle 8/9/10 scripts (recurring) | First-pass scripts crashed on the join with `SchemaError: datatypes of join keys don't match`; required explicit cast at join-time for each script | Pattern fix: cast both sides at the join boundary; deeper fix is upstream uniform ns-precision policy. Tracked under follow-up `P1-SUBSTRATE-PRECISION-UNIFY` |
| H053-D4 | **H053Hourly internally constructs ns-precision `pl.datetime_range` grid but receives μs panel** | [src/skie_ninja/features/h053/hourly.py](../../src/skie_ninja/features/h053/hourly.py) | Hourly's compute crashes with `_ts_et_grid: ns vs _ts_et: μs` schema error when called with default-precision substrate | Stage-2/3 entry-point worked around by casting panel to ns BEFORE Hourly invocation; upstream fix tracked under `P1-H053-HOURLY-PRECISION-COERCE` |
| H053-D5 | **Cross-block ts_event misalignment — each H053 block anchors at a different intraday clock-time** | Block A Daily anchors at T-1 16:15 ET; Block B Hourly at 09:31 ET; Block C/D at 09:45 ET | First-pass Stage-2/3 scripts attempted inner-join on `ts_event` and got 0 rows; not detected by unit tests because each block was tested in isolation | Stage-2/3 fix: switch the inter-block join to `(symbol, session_date_et)` with Daily's date shifted +1 calendar day. No upstream fix — the per-block ts_event anchors are correct per design.md §3.0 R5; the inter-block join is the consumer's responsibility |
| H053-D6 | **Daily column name bakes the CV-tuned N (e.g., `daily_realized_range_60`)** | [src/skie_ninja/features/h053/daily.py](../../src/skie_ninja/features/h053/daily.py) | First-pass Stage-2 scripts hardcoded `daily_realized_range_n` and crashed on `ColumnNotFoundError` | Stage-2 fix: auto-discover columns via `df.columns` rather than enumerating; upstream improvement tracked under `P1-H053-DAILY-COLUMN-NAME-STABILITY` |

### B. Methodological deferrals that may bias Stage-3 once re-run (DEFENSIVE / NEEDED-BUT-OVERBUILT)

| # | Deferral | Verdict | Note |
|---|---|---|---|
| H053-M1 | **Cross-fitted DML alternative (Chernozhukov et al. 2018)** deferred from Stage-2 | NEEDED-FOR-STAGE-3 | Stage-2 partial-R² is in-sample on OOS; the canonical OOS predictive partial-R² requires the design.md §5.4 fold-disjoint scalarization protocol with `f_S` fitted on `S` sub-fold + frozen on `Med` + OOS. Tracked under `P1-H053-CYCLE9-DML-SENSITIVITY` |
| H053-M2 | **Synthetic-null Monte-Carlo coverage test (design.md §11.2 prereq 3)** deferred from Stage-2 to Stage-3 | NEEDED-FOR-STAGE-3 | Unit-tested at coarse precision in [tests/unit/test_h053_mediation.py](../../tests/unit/test_h053_mediation.py); production-grade Monte-Carlo (~5000 replicates, AR(1) residuals) deferred. Tracked under `P1-H053-CYCLE9-OOS-PARTIAL-R2-COVERAGE-TEST` |
| H053-M3 | **PC1 < 50% triggers per-coordinate robustness exhibit at Stage-3** | NEEDED-FOR-STAGE-3 | Stage-2 found ES PC1 var-expl 0.479, NQ 0.461 — both below the design.md §5.4 50% threshold. Per-coordinate exhibit is mandatory for Stage-3 re-run. Tracked under `P1-H053-CYCLE10-PC1-PER-COORDINATE-ROBUSTNESS` |
| H053-M4 | **27-cell CV grids → simplified to 9+4 = 13 cells** in Stage-3 first-pass | NEEDED-BUT-OVERBUILT-IF-RE-RUN-WITH-FULL-GRID | Operational simplification of design.md §5.1 + §5.2; the binding pre-reg grid is 5×3 ElasticNet × 3×2×2 LightGBM = 27 cells. Tracked under `P1-H053-CYCLE10-FULL-CV-GRIDS` |
| H053-M5 | **Isotonic calibration fitted in-fold per archetype** instead of true OOF | NEEDED-FOR-STAGE-3 | Stage-3 first-pass categorical-table v2 used in-fold isotonic which is mildly optimistic; design.md §4.5.3 binds OOF calibration. Tracked under `P1-H053-CYCLE10-ISOTONIC-OOF` |
| H053-M6 | **HKS time-of-day-FE benchmark collapses to passive-long when `mean_y_train > 0`** | DEFECT-IN-BENCHMARK | The constant-mean-of-train signal sets sign=+1 for all sessions when train mean is positive (which is the realised case on ES + NQ); makes the conjunctive `arm vs ToD-FE` test redundant with `arm vs passive`. Better benchmark: prior-day-same-bin return. Tracked under `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE` |

### C. Cross-cutting protocol observations (mirroring H050 §6)

#### O-H053-1. Diagnostic instrumentation arrived after the build, not before

The pre-2022 RTH bar count distribution was not inspected at any point during the Stage-2 / Stage-3 build until after the user prompted post-hoc diagnosis. A pre-build sanity audit on the substrate's per-session bar-count distribution would have surfaced the `404 vs 405` discrepancy before the Daily-block gate truncated the train fold. **This is a recurrence of H050 §O-1**: diagnostic instrumentation arriving late.

**Mitigation**: pre-build "substrate fitness for hypothesis" sanity check that includes per-session-bar-count distribution + RTH-window-coverage histogram. Tracked under `P1-PRE-BUILD-SUBSTRATE-FITNESS-AUDIT`.

#### O-H053-2. Single-round inline audit on Cycles 8/9/10 missed the truncation

Each of Cycles 8 / 9 / 10 used a "single-round inline" audit-remediate pattern (the build defects were caught in-loop during script iteration, but no separate quant-auditor / repro-verifier subagent was launched). On Cycle 7 + Phase B I used the canonical 2-3 round parallel-subagent audit; on Cycles 8/9/10 I scoped down to "the empirical result IS the verdict" and skipped the formal audit. **This is the failure mode**: a parallel quant-auditor invocation on Cycle 9 / 10 would likely have flagged the small train fold as a confounding factor before the disposition was committed.

**Mitigation**: parallel quant-auditor is mandatory on every "binding disposition" cycle (8, 9, 10), even when the result appears clean from inline iteration. The scope-down "single-round inline" pattern is acceptable for build-only deliverables (Cycle 7 feature factory), not for evidence-bar dispositions. Tracked under `P1-AUDIT-DISCIPLINE-DISPOSITION-CYCLES`.

#### O-H053-3. The reversal-direction empirical pattern survives the truncation defect, but is narrower than first claimed

Stage-1's negative `m_return` OLS coefficient on full 1971-session IS train was **not** affected by the Daily-gate defect (mediator block doesn't depend on Daily). Stage-2's negative NDE point estimate was on the truncated 178-session train, so it is fragile. Stage-3's negative inner-CV R² is mostly an artifact of the truncation. The genuine empirical finding from the H053 build sequence is therefore narrower than the original phrase "consistent reversal-direction pattern across all 3 stages": it is "the H053 mediator alone shows no Sharpe-promotable signal in 09:45-10:30 ET on ES/NQ at the full 1971-session sample" (Stage-1). Whether multi-timeframe X carries Sharpe-promotable signal is **untested** until the Daily-gate defect is fixed and Stage-3 is re-run.

#### O-H053-4. CLAUDE.md ledger update on `archive(null)` was premature

The Phase E commit (`28f93ec`) wrote the H053 archive disposition to CLAUDE.md before the user-prompted diagnosis exposed the truncation. Per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` (filed 2026-04-30 in this same post-mortem), CLAUDE.md ledger updates that reframe audit-trail dispositions must themselves go through the audit-remediate-loop. **The Phase E ledger update violates that discipline** and is being remediated in the same commit as this appendix (un-archive section + appended findings).

**Mitigation**: CLAUDE.md `archive(...)` ledger entries require an explicit audit-remediate-loop pass that includes a "is the disposition robust to the build defects observed in the cycle" gate. Tracked under `P1-CLAUDE-MD-LEDGER-DISPOSITION-ROBUSTNESS-CHECK`.

### D. Defect taxonomy summary (H053 build vs H050 prod-run)

| Category | H050 prod-run § | H053 build § |
|---|---|---|
| OS / hardware kills (reboot, OOM) | §3 (run-2 reboot, run-4 OOM, run-5 OOM, run-6 reboot-bypass) | n/a (offline analysis) |
| Substrate quality issues | implicit in Cell-I refresh + decade-wraparound | **H053-D1** (404 vs 405 bar pre-2022) |
| Feature-factory dtype + alignment | n/a (H050 used pre-aligned features) | **H053-D2/D3/D4/D5/D6** |
| Methodological deferrals (proper protocol postponed) | §3 run-3 numba-equivalence claim | **H053-M1/M2/M3/M4/M5** |
| Audit-discipline regressions | §6 O-3 (lit-check on ADRs) + §6 O-4 (regression in CLAUDE.md re-framing) | **O-H053-2/O-H053-4** |
| Diagnostic instrumentation late | §6 O-1 | **O-H053-1** (recurrence) |

### E. New follow-ups filed (H053 appendix)

- `P1-H053-DAILY-405-GATE-RECONCILE` — BLOCKING-BEFORE-NEXT-STAGE-3 — relax gate to `>= 404` OR substrate-side fix.
- `P1-SUBSTRATE-PRECISION-UNIFY` — uniform ns-precision policy across substrate vendors.
- `P1-H053-HOURLY-PRECISION-COERCE` — H053Hourly internal cast to ns-precision.
- `P1-H053-DAILY-COLUMN-NAME-STABILITY` — stable column naming independent of CV-tuned N.
- `P1-PRE-BUILD-SUBSTRATE-FITNESS-AUDIT` — pre-build substrate-fitness audit including per-session-bar-count distribution.
- `P1-AUDIT-DISCIPLINE-DISPOSITION-CYCLES` — parallel quant-auditor mandatory on disposition cycles.
- `P1-CLAUDE-MD-LEDGER-DISPOSITION-ROBUSTNESS-CHECK` — extend `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` to include disposition-robustness gate.

### F. H053 disposition status (binding)

**UN-ARCHIVED 2026-05-01.** Stage-1 NULL evidence (mediator alone insufficient on full 1971 IS sessions) holds and is genuine. Stage-2 + Stage-3 first-pass results are NOT BINDING due to train-fold truncation. Stage-3 must be re-run after `P1-H053-DAILY-405-GATE-RECONCILE` lands.

### G. ADR-0012 disposition-philosophy shift (appended 2026-05-01)

User-prompted post-design-audit on the H053 gating tree (2026-05-01) led to [ADR-0012 disposition-philosophy-aspirational-mvp](../decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md), which restructures the per-hypothesis §8 + §10 gating trees from "Sharpe-CI gates plus annotations" to a three-class rubric: binding gates (Class A: PIT/leakage + BSS + reliability + reproducibility + DSR-when-active), KPIs (Class B: Sharpe-vs-passive, Sharpe-vs-todfe, SPA family p, max-DD ratio, power margin, etc.), and documentation requirements (Class C).

**Direct relevance to H050 post-mortem**: per the user-prompted gate audit, the user noted that the existing Sharpe-CI gating regime is "the cause of our own failure" — discarding strategies for failing to clear a noisy CI test at modest sample size, when the descriptive evidence supports continued investigation through to paper-trade. **None of the H050 prod-run failures (runs 1-6 attempt-2) was caused by the design-time Sharpe-CI gate** — H050 never reached the gating tree, dying for infrastructure reasons (Windows reboots, OOM, HMM EM bottleneck). The ADR-0012 amendment is therefore **prospective for H050**: any future H050 re-launch (e.g., after the H050 BLOCKING follow-ups close per `P1-PREFLIGHT-USOSVC-TASK-DISABLE` + ADR-0010 framing) will use the three-class disposition rubric, not the legacy Sharpe-CI gating tree.

**Direct relevance to H053 build-session findings (this appendix §C)**: §C-O-H053-2 ("Single-round inline audit on Cycles 8/9/10 missed the truncation") and §C-O-H053-4 ("CLAUDE.md ledger update on archive(null) was premature") both reflect the constraint-gated disposition pipeline producing premature NULL labels. Under ADR-0012, the H053 Stage-1 first-pass `archive(null, sharpe-ci-not-clearing-conjunctive)` verdict from commit `76599bd` is retroactively re-tagged `archive(complete; KPI: sharpe-vs-passive-positive-weak, sharpe-vs-todfe-flat-degenerate-bench, max-dd-favorable, power-margin-adequate, partial-r2-not-applicable-stage-1, cost-robust)`. Stage-3 still requires re-run (the Daily-gate truncation defect is independent of the ADR-0012 amendment), but the disposition labels for the re-run will use the three-class rubric.

**CPCV restoration**: the H053 Stage-1/2/3 first-pass implementations used a single train/test cut (2015-2022 IS, 2024-2025 OOS), NOT CPCV. Per ADR-0012 §"Cross-validation methodology", `P1-BACKTEST-CPCV` is promoted to BLOCKING-BEFORE-ANY-STAGE-3-RE-RUN. The Cycle-4 scaffolding at [src/skie_ninja/backtest/splits.py](../../src/skie_ninja/backtest/splits.py) `cpcv_split` is the implementation foundation; full path-reconstruction is the load-bearing follow-up.

**Audit trail**: [docs/audits/audit_trail_2026-05-01_disposition-philosophy-shift.md](../audits/audit_trail_2026-05-01_disposition-philosophy-shift.md).

### H. H053 Stage-3 v2 production run (appended 2026-05-03)

Phase 1 (refactor) + Phase 2 (production run) under ADR-0012; full audit trail at [docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md](../audits/audit_trail_2026-05-03_h053-stage3-v2.md).

**Phase 2 result summary** (4 arms × 2 symbols, all `calibration-failed; paper_trade_eligible=False`):

| Symbol | Arm | CPCV median Sharpe | DSR | OOF-iso BSS | Disposition |
|---|---|---:|---:|---:|---|
| ES | ElasticNet | -0.112 | -1.36 | -0.013 | calibration-failed |
| ES | LightGBM | +0.428 | -1.04 | -0.176 | calibration-failed |
| NQ | ElasticNet | +0.472 | -1.07 | -0.010 | calibration-failed |
| NQ | LightGBM | +0.422 | -1.39 | -0.207 | calibration-failed |

Train n=1332 (ES) / 1323 (NQ) — Daily-gate fix verified. PIT canary 14/14 PASS both symbols. Hansen SPA p=0.37/0.31 (KPI; not binding). Wall-clock 2 min 27 sec.

**Round-1 audit on Phase 1 returned BLOCK** (3 critical: CPCV time-ordering violation, KFold-shuffle inner-CV, in-sample isotonic source; 6 majors). Critical findings INFLATE Sharpe + calibration metrics, so the `calibration-failed` disposition is robust to leakage direction (BSS<0 despite leakage means honest BSS would also be <0). Sharpe KPIs (3/4 positive median) are leakage-upper-bounds and should not inform operator-promotion until Round-2 remediation lands.

**Tracker for Round-2**: `P1-H053-STAGE3-V2-ROUND-2-REMEDIATION` (BLOCKING-BEFORE-PAPER-TRADE-ELIGIBILITY).
