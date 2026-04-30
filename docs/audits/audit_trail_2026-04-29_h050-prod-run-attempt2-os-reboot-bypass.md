---
title: H050 prod-run-6 attempt-2 termination — system reboot DESPITE active wake-lock + preflight timeout
date: 2026-04-29
artifact: H050 walk-forward run_id e59171865ebb45559434250f3674a9e3 + supervisor PID 33108 + child PID 3212 + Windows System Event Log
followup_id: P1-WAKE-LOCK-BYPASS-INVESTIGATION
exit_state: round-1 root-cause-partial (wake-lock bypass mechanism unresolved)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
parent_diagnoses: prod-run-2 (2026-04-27 WU-driven reboot), cfg-checkpoint diagnosis 2026-04-29
---

## Scope

Diagnose the termination of the H050 prod-run-6 relaunch loop's second attempt (run_id `e59171865ebb45559434250f3674a9e3`, launched 2026-04-29 19:25:43 CT under HEAD `6bed0c2` after the ADR-0011 governance directive landed). Documented evidence:

- Wake-lock `ES_CONTINUOUS|ES_SYSTEM_REQUIRED` (flags `0x80000001`) acquired at 19:26:45 per [logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.log](../../logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.log) (`wakelock acquired: ES_CONTINUOUS|ES_SYSTEM_REQUIRED (flags=0x80000001, prev=0x-80000000, refcount=1)`).
- Last orchestrator PROGRESS line at 19:27:38 (`PROGRESS inner-cv-lgb start | sym=NQ fold_id=0 n_draws=200 n_inner_folds=3`).
- Last supervisor telemetry sample at 20:15:18 (orchestrator alive, RSS 2.32 GB, 88 threads, **`cpu_percent: 0.0`**).
- **20:16:02 — System EventLog stopped** (Event 6006, clean shutdown beginning).
- **20:16:03 — Microsoft-Windows-Kernel-Power Event 109**: "Action: Power Action Reboot. Event Code: 0x0. Reason: Kernel API". System-initiated reboot.
- 20:16:35 — System back up (Event 6005 + Event 6013).
- 20:40:01 — User32 Event 1074 — user-initiated reboot.
- 20:40:43 — System back up.
- No `.summary.json` artifact written for the 19:25 attempt — supervisor's `finally` block at [scripts/supervised_run.py:411-437](../../scripts/supervised_run.py) did not execute (consistent with hard kill, not graceful termination). The supervisor's classification logic (`_classify_exit` + summary write) did not run; however, the `.supervisor.jsonl` first sample IS effectively a process-spawn record — it captures supervisor PID 33108 + orchestrator PID 3212 + child create_time + first PROGRESS line — confirming the supervisor entered its telemetry loop and the orchestrator launched. The preflight write at scripts/supervised_run.py:303 happened before orchestrator launch, so `.preflight.json` is the load-bearing pre-launch evidence.

This is the **6th distinct production-run failure** in the H050 arc, and the **first to occur after the ADR-0011 directive landed** (commit `6bed0c2`). Documented audit trails for prior 5 failures: [prod-run-1](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md), [prod-run-2](audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md), [numba-kernels-prod-run-3](audit_trail_2026-04-28_hmm-em-numba-kernels.md), [lgb-heap-fragmentation-prod-run-4](audit_trail_2026-04-28_lgb-heap-fragmentation.md), [cfg-checkpoint-prod-run-5](audit_trail_2026-04-29_cfg-checkpoint.md).

## Evidence-preservation note

Originals at `logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.{log,supervisor.jsonl,preflight.json}` are gitignored (per `logs/**` rule) and ephemeral. **Canonical, non-ignored copies** are at [logs/crash_evidence/walk_forward_2026-04-29_192543/](../../logs/crash_evidence/walk_forward_2026-04-29_192543/) (3 sidecars, byte-identical to originals at copy time) and the System EventLog slice at [logs/crash_evidence/system_events_2026-04-29_2014-2017.json](../../logs/crash_evidence/system_events_2026-04-29_2014-2017.json) (~56 KB). All inline `logs/walk_forward_runs/...` references in this trail are convenience pointers; the load-bearing audit-evidence references are the `logs/crash_evidence/` copies.

## Three confirmed findings

### F-1 — System reboot fired despite active wake-lock (regression of ADR-0010 Layer 1)

The wake-lock at [src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py) was acquired with the flag combination ADR-0010 specifies as the run-2 fix: `ES_CONTINUOUS | ES_SYSTEM_REQUIRED` (`0x80000001`). The orchestrator log confirms acquisition at 19:26:45. Yet 49 minutes later, Microsoft-Windows-Kernel-Power Event 109 fired with reason "Kernel API" — exactly the run-2 (2026-04-27) signature.

Differences from run-2:
- **Run-2**: no wake-lock acquired (orchestrator did not register itself as system-required); reboot at +4h37m.
- **Run-attempt-2 (2026-04-29)**: wake-lock acquired and confirmed in the log; reboot at +49m.

Hypotheses for the bypass mechanism (each requires further evidence; none fully confirmed):

| Hypothesis | Supporting evidence | Refuting evidence |
|---|---|---|
| **H-A. Smart Active Hours dynamic expiry** — registry static AH is 8–1 (17h coverage from 8 AM to 1 AM next day) but Smart AH may dynamically classify the system as idle (orchestrator at 0% CPU) and trigger a maintenance-window reboot regardless of `ES_SYSTEM_REQUIRED`. Tracked under existing `P1-PREFLIGHT-SMART-AH-DYNAMIC` in the ADR-0010 residual ledger. | The 19:25 launch was clearly inside static AH (19:25 < 1 AM next day); a system that respects static AH would not reboot. | Per Microsoft Learn ([active-hours](https://learn.microsoft.com/en-us/windows/deployment/update/active-hours)), when `ActiveHoursStart`/`ActiveHoursEnd` are manually configured (host has 8/1), Smart AH dynamic-computation is typically disabled. Absence of `SmartActiveHoursState` is consistent with manual-AH-configured-and-Smart-AH-not-engaged. **Status: not eliminated, not confirmed** — registry-state interpretation is insufficient on its own; needs empirical replication on a test rig. |
| **H-B. UsoSvc / Update Orchestrator Service enforcement-deadline reboot** — Microsoft-Windows-WindowsUpdateClient events 19/20 fire on installation activity, not on the reboot-orchestration call itself; UsoSvc / MoUsoCoreWorker (Update Orchestrator Service) is the actual Kernel-API caller for an enforcement-deadline reboot, logging to the Microsoft-Windows-WindowsUpdateClient/Operational + USO trace channels — not necessarily to the System log. The post-reboot 19/43/44 events at 20:26-20:27 are consistent with WU finishing an install it initiated pre-reboot. `ES_SYSTEM_REQUIRED` does NOT block UsoSvc enforcement-deadline reboots per the documented `SetThreadExecutionState` semantics. | Kernel-Power 109 reason 0x0 ("Kernel API") is the documented signature for UsoSvc-initiated reboots. The post-reboot 19/43/44 events at 20:26-20:27 indicate WU activity in the period spanning the reboot. | The 18:00–20:18 System-log channel returned no WindowsUpdateClient events — but UsoSvc may log to Operational + USO trace channels not queried. **Status: not eliminated, not confirmed** — needs probe of `Microsoft-Windows-WindowsUpdateClient/Operational` + USO trace channels for the 20:14-20:16 window. |
| **H-C. Driver / kernel watchdog detected hung process** — orchestrator at 0% CPU for at least 2 minutes (20:13:18 → 20:15:18 supervisor samples) before the reboot. A driver watchdog or DPC timeout might force a reboot if it interprets the hang as a system-fault. | 0% CPU is unusual for a single-threaded BLAS-pinned LGB inner-CV that should be CPU-bound. The hang preceded the reboot. | **Strongly refuted by mechanism analysis**: Windows does not auto-reboot hung user-mode processes via Kernel-Power 109. DPC/ISR watchdog hangs produce Bugcheck 0x133 (DPC_WATCHDOG_VIOLATION); none observed. Hardware power-loss produces Event 41; none observed. The Kernel-Power 109 path is process-initiated (`InitiateSystemShutdownEx`-equivalent), not OS-initiated on a hung user-mode process. **Status: eliminated.** |
| **H-D. Manual user reboot via non-1074 path** — operator at the machine, used a non-Start-menu mechanism (PowerShell `Restart-Computer`, Win+X). Run-attempt-2's first reboot showed no 1074 — so if user-initiated, by a non-Start-menu mechanism. | The second reboot at 20:40:01 *did* log User32 Event 1074, confirming user activity at the machine in the same window. | Inconsistent: if the user rebooted at 20:16, they would normally use the same mechanism that produced 1074 at 20:40. **Status: weakly refuted** but cannot be fully eliminated without operator interview. |
| **H-E. Hardware-level event** (UPS battery, momentary power, brownout) | Two reboots within 24 min is consistent with a flaky power supply or a UPS battery on its last legs (kicked over to battery, came back, kicked over again). | Kernel-Power 109 is a *clean* shutdown transition initiated via Kernel API. Hardware power loss would log Event 41 ("Kernel-Power: The system has rebooted without cleanly shutting down first"), not 109. **Event 41 absent.** **Status: eliminated.** |

**Disposition after Round-1 audit:** H-A and H-B are unprobed candidates of approximately equal weight; H-C and H-E are eliminated by mechanism analysis; H-D is weakly refuted but not fully eliminated. **No single hypothesis is "leading"** until the empirical probes specified under `P1-WAKE-LOCK-BYPASS-INVESTIGATION` (acceptance criteria below) execute.

`P1-WAKE-LOCK-BYPASS-INVESTIGATION` is filed as the umbrella follow-up; it must conclude before another multi-hour H050 launch.

### F-2 — Preflight script timed out at 60s, supervisor proceeded under `--allow-preflight-warn`

[h050_prod_run_2026-04-29T192543.preflight.json](../../logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.preflight.json) records:

```json
{
  "status": "warn",
  "error": "TimeoutExpired(['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', 'scripts\\\\preflight\\\\check_windows_update.ps1', '-ExpectedRuntimeHours', '2'], 60)"
}
```

[scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) timed out at 60 seconds. Without the JSON report, **gates 6 (pending-restart), 7 (Active Hours coverage), 9 (scheduled tasks), 10 (disk-space) were not exercised** for this launch. The supervised relaunch loop passes `--allow-preflight-warn` per `scripts/supervised_relaunch_loop.sh:73`, so the supervisor proceeded.

This is a Class-A failure of the launch path: ADR-0011's preflight-gate auditability claim is paper-only when the preflight script does not produce its JSON. Filed under `P1-PREFLIGHT-SCRIPT-TIMEOUT`. The 60s budget needs to be raised (likely to 180s for a slow first-run on a host that has been up for a while), or the script needs to produce partial-JSON-on-timeout rather than total failure.

### F-3 — Orchestrator at 0% CPU before the reboot

Five consecutive supervisor telemetry samples at 30s intervals (20:13:18, 20:13:48, 20:14:18, 20:14:48, 20:15:18) report `cpu_percent: 0.0` for both the supervisor (PID 33108) and the orchestrator (PID 3212). Orchestrator state: 88 threads, RSS 2.32 GB, status `running`. The earliest sample at 0% CPU is the first sample after the supervisor was monitoring; we don't know how far back the 0% CPU pattern extended.

Production single-threaded BLAS-pinned LGB inner-CV at `n_draws=200, n_inner_folds=3, train_size=2978358` should be CPU-bound at ~97% (the run-3 / run-4 / run-5 telemetry baseline). 0% CPU is consistent with one of:

- **Deadlock** — Python GIL contention with numba `@njit` kernel callbacks; LightGBM Booster destructor blocking on an unreachable C++ resource; thread-pool wait on a never-coming signal.
- **Synchronous I/O block** — polars to-numpy materialisation hitting a swap-bound page that never comes back in.
- **Windows handle exhaustion** — 88 threads is high; possible the process hit a per-process handle limit and is blocked on a kernel call.

**Mechanism analysis — F-3 is coincident with, not the cause of, F-1.** Kernel-Power 109 reason 0x0 ("Kernel API") is by definition a process-initiated shutdown call (e.g. `InitiateSystemShutdownEx`). Windows does not auto-reboot hung user-mode processes via this path: DPC/ISR watchdog hangs produce Bugcheck 0x133 (DPC_WATCHDOG_VIOLATION), and hardware power loss produces Kernel-Power Event 41 — neither was observed. The 0% CPU pattern is consistent with a hung process being concurrently killed by an unrelated reboot trigger (whichever of H-A/H-B/H-D ultimately resolves to root cause); it is not itself the trigger.

Without a `py-spy dump` on the live process (no longer possible — process is dead), the deadlock vs I/O block distinction is not recoverable from this attempt. Filed under `P1-LGB-INNER-CV-CPU-ZERO-INVESTIGATION` as a soft follow-up; the architectural fix (`P1-LGB-INNER-CV-RESULT-CHECKPOINT`) bounds the cost regardless of root cause.

## What did NOT happen (rule-outs)

- No Application Error / Critical events in 20:14-20:17 window — no Python traceback, no driver crash.
- No Bugcheck 1001 — not a kernel BSOD.
- No Kernel-Power Event 41 — not a hard power loss.
- No WindowsUpdateClient 19/20 events before 20:16 — reboot was not WU-installation-driven (does **not** refute H-B UsoSvc enforcement-deadline path; see F-1 H-B row — `Microsoft-Windows-WindowsUpdateClient/Operational` + USO trace channels not yet probed).
- No User32 Event 1074 between 18:00 and 20:18 — first reboot was not user-initiated via Start menu / `shutdown.exe` / `Restart-Computer`.

## Operational state at write-time (23:26 CT)

- Both supervisor + orchestrator PIDs gone from `tasklist /v`.
- Relaunch loop (PID 23618) gone.
- No `summary.json` for the 19:25 attempt — terminal classification not written.
- Cumulative NQ cfg-checkpoints across all attempts: still **11 / 27** (carried forward from base run `338aac0a` from 2026-04-26; neither attempt 1 at 16:24 nor attempt 2 at 19:25 produced a new NQ cfg.pkl).
- ES cfg-checkpoints: 38 in base run (sufficient).
- The 20:16 reboot also kicked the relaunch loop out; the loop's outer bash session is dead. No further attempts will fire.

## The 4 user-prescribed steps — actual disposition

| Step | User intent | Actual disposition |
|---|---|---|
| 1. Kill the hung attempt | Manual termination of the alive-but-stuck process. | **Performed by the OS** at 20:16:03 via Kernel-Power 109. Both supervisor (33108) and orchestrator (3212) and the relaunch loop (23618) are dead. No manual kill required. |
| 2. Diagnose the 0% CPU | `py-spy dump --pid 3212`. | **Not possible** — PID 3212 was killed before py-spy could be run. The 0% CPU pattern is documented under F-3 as an unresolved investigation; the architectural fix (per-fold checkpointing) bounds the cost without depending on root-cause clarity. |
| 3. Raise `PER_LAUNCH_CAP_S` to ≥6 hr | Allow cfgs to complete within one attempt. | **Implementing**: this commit raises `PER_LAUNCH_CAP_S=10800` → `21600` (6 hr) in `scripts/supervised_relaunch_loop.sh:30` with rationale comment. This addresses the cap-vs-cfg-cost mismatch but does NOT solve F-1 (wake-lock bypass) — a 6-hour run is also vulnerable to a system-initiated reboot if the bypass mechanism repeats. |
| 4. Promote `P1-LGB-INNER-CV-RESULT-CHECKPOINT` to blocking | Within-cfg checkpointing as the architectural fix. | **Implementing**: ADR-0011 §"Residual risk" updated to mark this follow-up `[blocking-before-next-H050-launch]`. The within-cfg checkpoint is the defense for both F-3 (hung cfg) and F-1 (any external kill mid-cfg). |

## Net implications

- **The wake-lock alone is not sufficient** — at least one OS-level mechanism can override `ES_SYSTEM_REQUIRED` at 0% CPU. ADR-0010 Layer 1 needs investigation. F-1 has 5 candidate hypotheses (H-A Smart AH dynamic / H-B UsoSvc enforcement-deadline unprobed-after-Round-1; H-D weakly refuted; H-C kernel watchdog / H-E hardware eliminated by mechanism analysis); existing follow-up `P1-PREFLIGHT-SMART-AH-DYNAMIC` is renamed `P1-WAKE-LOCK-BYPASS-INVESTIGATION` (umbrella) for end-to-end coverage.
- **Preflight gate auditability is paper-only when the script times out** — F-2 is a direct attack on ADR-0011 gates 6/7/9/10 effectiveness. `P1-PREFLIGHT-SCRIPT-TIMEOUT` filed.
- **Per-attempt cap raise (3 hr → 6 hr) is necessary but not sufficient** — solves the cap-vs-cfg-cost livelock but does nothing for the wake-lock bypass.
- **Within-cfg checkpoint is the load-bearing architectural defense** — `P1-LGB-INNER-CV-RESULT-CHECKPOINT` is now blocking; without it, every external kill (whether OS-reboot, BSOD, hardware) loses up to one cfg of inner-CV-LGB regardless of cap size.

## New follow-ups

- `P1-WAKE-LOCK-BYPASS-INVESTIGATION` — umbrella follow-up; investigate why Kernel-Power 109 fired despite an acquired `ES_SYSTEM_REQUIRED` wake-lock. **Acceptance criteria** (all required to close): (1) probe `Microsoft-Windows-WindowsUpdateClient/Operational` channel + USO trace channel for the 20:14-20:16 window (addresses H-B); (2) probe Smart Active Hours behaviour on a test rig with manual AH 8/1 set, simulating idle for 90+ min, recording whether `SmartActiveHoursState` materialises (addresses H-A); (3) for each of H-A through H-E, decide eliminated / confirmed / open based on (1)+(2); (4) ship a defense layer for whichever hypothesis remains open (e.g. wevtutil-based pre-reboot canary, Group-Policy-based WU pause for the run window, ES_AWAYMODE_REQUIRED with documented Modern-Standby risk acceptance). Subsumes the older `P1-PREFLIGHT-SMART-AH-DYNAMIC`. Blocking before the next multi-hour H050 launch.
- `P1-PREFLIGHT-SCRIPT-TIMEOUT` — raise the 60s timeout (likely to 180s) and emit partial JSON on timeout rather than total failure. Blocking before the next launch.
- `P1-LGB-INNER-CV-RESULT-CHECKPOINT` — **promoted from non-blocking to blocking** before the next H050 launch. Within-cfg / per-inner-fold checkpointing.
- `P1-LGB-INNER-CV-CPU-ZERO-INVESTIGATION` — soft follow-up. **Capture stack on next observed 0% CPU event in this priority order**: (a) `py-spy dump --pid <orchestrator>` for Python frame stack; (b) Sysinternals `procdump -ma <pid>` for full minidump (works on apparently-frozen processes; analysable in WinDbg); (c) supervisor-side ETW trace via `wpr -start CPU,FileIO -filemode` for the 60 s preceding any kill. Add a supervisor-level threshold trigger (e.g. 5 consecutive 30 s samples at 0% CPU → auto-procdump) so capture does not depend on operator presence.
- `P1-SUPERVISOR-FINALLY-WRITE-ON-HARD-KILL` — supervisor's terminal `summary.json` was not written under the OS-reboot path; the `finally` block doesn't execute when SIGKILL-equivalent fires. Investigate atomic write of partial summary on supervisor process spawn so a hard kill leaves at least the spawn record on disk.
- `P1-SUPERVISOR-CAP-FIELD-PERSISTENCE` — persist `max_runtime_s` + `expected_runtime_h` into every `.preflight.json` at supervisor-spawn time (before orchestrator launches), so the cap value is on disk regardless of whether `finally` ever runs. Currently the cap value is only recoverable via `git blame scripts/supervised_relaunch_loop.sh:30` against the supervisor-spawn timestamp captured in `.preflight.json` first sample — recovery procedure documented but not machine-readable per attempt.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [ADR-0010-multi-hour-run-process-protection.md](../decisions/ADR-0010-multi-hour-run-process-protection.md) — wake-lock + supervisor + Windows-Update preflight design.
- [ADR-0011-production-walkforward-runbook.md](../decisions/ADR-0011-production-walkforward-runbook.md) — binding directive landed at HEAD of attempt-2.
- [audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md) — earlier WU-driven reboot (different mechanism).
- [audit_trail_2026-04-29_adr-0011-prodrun-runbook-directive.md](audit_trail_2026-04-29_adr-0011-prodrun-runbook-directive.md) — directive that landed at HEAD `6bed0c2`.
- [logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.log](../../logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.log) — orchestrator log (truncated at 19:27:38; **un-ignored copy at [logs/crash_evidence/walk_forward_2026-04-29_192543/h050_prod_run_2026-04-29T192543.log](../../logs/crash_evidence/walk_forward_2026-04-29_192543/h050_prod_run_2026-04-29T192543.log) is the load-bearing audit-evidence reference**).
- [logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.supervisor.jsonl](../../logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.supervisor.jsonl) — supervisor telemetry (last sample 20:15:18; **un-ignored copy at [logs/crash_evidence/walk_forward_2026-04-29_192543/](../../logs/crash_evidence/walk_forward_2026-04-29_192543/)**).
- [logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.preflight.json](../../logs/walk_forward_runs/h050_prod_run_2026-04-29T192543.preflight.json) — preflight timeout record (**un-ignored copy at [logs/crash_evidence/walk_forward_2026-04-29_192543/](../../logs/crash_evidence/walk_forward_2026-04-29_192543/)**).
- [logs/crash_evidence/system_events_2026-04-29_2014-2017.json](../../logs/crash_evidence/system_events_2026-04-29_2014-2017.json) — Windows System Event Log slice for the 20:14-20:17 reboot window (~56 KB), captured per F-1/F-3 evidence-preservation contract; same schema as the 2026-04-27 prod-run-2 dump.
- Microsoft Docs: [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) — flag semantics.
- Microsoft Docs: [Smart Active Hours](https://learn.microsoft.com/en-us/windows/deployment/update/active-hours) — dynamic AH end-time on Windows 11.
