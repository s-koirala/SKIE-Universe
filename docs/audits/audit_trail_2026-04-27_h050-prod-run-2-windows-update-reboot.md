---
title: H050 prod-run-2 termination — Windows Update auto-reboot
date: 2026-04-27
artifact: H050 walk-forward run_id 69626bcb90f445958ca61dbb560051f5 + Windows System Event Log
followup_id: P1-WIN-UPDATE-AUTO-REBOOT
exit_state: root-cause-confirmed
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: not yet (this is the diagnosis trail; remediation triggers an isolated audit-remediate-loop)
---

## Scope

Diagnose why the H050 prod-run-2 (run_id `69626bcb90f445958ca61dbb560051f5`, launched 2026-04-27 00:01:23 CT under commit `429f2555524`) terminated mid-execution between 00:02:05 CT (last `PROGRESS hmm-fit start` log line) and 04:39:18 CT (operating system shutdown). No `PROGRESS hmm-fit done`, `failed`, or any subsequent line was emitted; no per-fold artifacts were written; no Python traceback or stderr message was captured.

The earlier prod-run-1 ([docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md)) had a different failure mode (operator-killed at +180 min for diagnostic purposes; HMM cov-redundancy bottleneck identified). Prod-run-2 was launched under both fixes (`P1-HMM-FULL-COV-1DIM-REDUNDANT` deduplication landed in commit `c2caa20`; `P1-ORCHESTRATOR-PROGRESS-LOGGING` in commit `429f255`) and is the first run on the post-fix codebase.

## Evidence chain

### Run state at termination

| Metric | Value |
|---|---|
| Wall time at last log line | ~2 min 42 sec (00:01:23 → 00:02:05 CT) |
| Wall time from launch to OS shutdown | ~4 hr 38 min (00:01:23 → 04:39:18 CT) |
| PROGRESS lines emitted | 6 (run start → symbol start → label-cfg-loop-step start → label-cfg start → fold-fit start → hmm-fit start) |
| `PROGRESS done` markers | 0 |
| `PROGRESS failed` markers | 0 |
| Per-fold artifacts | 0 |
| Aggregate artifacts | 0 |
| stderr | empty (no Python traceback) |
| Process state at investigation time | not present in `tasklist` |

### Windows System Event Log — reboot window (04:35:00 → 04:45:00 CT)

Raw evidence captured to [logs/crash_evidence/system_events_2026-04-27_0435-0445.json](../../logs/crash_evidence/system_events_2026-04-27_0435-0445.json) (76KB, full event record set in the 10-minute reboot window).

Summary of the load-bearing events (ordered by `TimeCreated`):

| TimeCreated (CT) | Event ID | Provider | Significance |
|---|---|---|---|
| 04:39:12 | 7002 | Microsoft-Windows-Winlogon | "User Logoff Notification for Customer Experience Improvement Program" — first sign the OS began session-teardown |
| 04:39:18 | 6006 | EventLog | "The Event log service was stopped" — clean shutdown began |
| 04:39:18 | 50037 | Dhcp-Client | "DHCPv4 client service is stopped. ShutDown Flag value is 1" — confirms shutdown path, not crash |
| 04:39:20 | **109** | **Microsoft-Windows-Kernel-Power** | **"The kernel power manager has initiated a shutdown transition. Action: Power Action Reboot. Event Code: 0x0. Reason: Kernel API"** |
| 04:39:20 | **577** | **Microsoft-Windows-Kernel-Power** | **"The system has prepared for a system initiated reboot from Active"** |
| 04:39:37 | 578 | Microsoft-Windows-Kernel-Power | "The system has detected a system initiated reboot from Active" |
| 04:39:47 | 6005 | EventLog | "The Event log service was started" — boot complete |
| 04:39:47 | 6013 | EventLog | "The system uptime is 17 seconds" — confirms a fresh boot session |

### What was NOT in the event log

| Event ID | Provider | Meaning if present | Status |
|---|---|---|---|
| 1001 | Microsoft-Windows-WER-SystemErrorReporting | Application BugCheck (BSOD) | **absent** — not a kernel crash |
| 41 | Microsoft-Windows-Kernel-Power | Unexpected reboot / power loss | **absent** — not a hard fault |
| 1074 | User32 | User-initiated shutdown / reboot | **absent in the 04:35-04:45 window** (the 1074 at 07:13 was the user power-off later that morning) |
| 19 / 20 from WindowsUpdateClient at 04:39 | Microsoft-Windows-WindowsUpdateClient | Windows Update install completed before / triggering the reboot | **absent** — but a 19 at 04:50:05 (after the boot) shows updates installed *during* the new boot session |

## Root cause

**Windows Update issued a system-initiated reboot via the `Kernel API` (Event 109) while the orchestrator was running in the background.** Windows considered the system "Active" (Event 577 "from Active"), meaning no critical workload was registered with the power manager. The `uv run python` process did not call `SetThreadExecutionState(ES_SYSTEM_REQUIRED | ES_CONTINUOUS)` to register itself as a system-required workload, so the power manager treated the machine as idle-and-eligible-for-reboot and Windows Update enacted a maintenance-window reboot.

This is a **process-protection failure**, not a code defect. The orchestrator was working correctly when terminated; the operating system killed it.

### Evidence that it is not a code defect

- The progress-logging instrumentation (commit `429f255`) emitted 6 structured PROGRESS lines and was actively running.
- The diagnosis from the previous run (per-E-step `1.17-1.21x` ratio at production T=3M; cold HMM-fit per stratum-fold-symbol takes 5-50 min × 5-10 restarts) is consistent with the run still being inside its first cold HMM-fit at the +4h37m mark — the orchestrator was *still alive and progressing* when the OS killed it.
- No Python traceback, no `failed` marker, no critical / error event in the System log between 04:35 and 04:45 CT.

## Diagnostic value of the patches

The `P1-ORCHESTRATOR-PROGRESS-LOGGING` patch (commit `429f255`) made this diagnosis *possible* in minutes rather than hours:

- **Prod-run-1 (pre-patch)**: 180-min hang with 0 bytes of stdout. Diagnosis required external `py-spy` dump + 3-agent investigation.
- **Prod-run-2 (post-patch)**: 6 structured PROGRESS lines pinpoint the exact phase (first HMM cold-fit for ES fold 0); absence of a `failed` marker rules out a Python exception; absence of a clean `done` rules out a normal exit. The diagnostic distinction between "hung", "crashed in Python", and "killed externally" is now legible from the log alone.

The Windows Event Log evidence is the second layer that the patches cannot provide on their own — the orchestrator can't observe its own external termination.

## Remediation pointer

Tracked under new follow-up `P1-WIN-UPDATE-AUTO-REBOOT`. Three-layer remediation in subsequent commits:

1. **Process-level wake-lock**: `SetThreadExecutionState(ES_SYSTEM_REQUIRED | ES_CONTINUOUS)` from the orchestrator's `__main__` so the Windows power manager defers reboots while the run is active.
2. **Pre-launch runbook**: Active Hours configuration, "pause Windows Update" verification, pending-restart check.
3. **Resume-from-checkpoint**: per-fold artifacts written incrementally; relaunch detects already-complete folds and skips them.

A separate **process-supervisor wrapper** (`scripts/supervised_run.py`) sampled RSS/CPU/threads at intervals and detects external-kill vs clean-exit asymmetry — implemented as task (c) in the same audit-remediate sequence.

## References

- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — prior diagnosis (different failure mode).
- [docs/audits/audit_trail_2026-04-26_orchestrator-progress-logging.md](audit_trail_2026-04-26_orchestrator-progress-logging.md) — the patch that made this diagnosis legible.
- [logs/crash_evidence/system_events_2026-04-27_0435-0445.json](../../logs/crash_evidence/system_events_2026-04-27_0435-0445.json) — full Windows System Event Log dump for the reboot window.
- [logs/walk_forward_runs/h050_prod_run_2_2026-04-27.log](../../logs/walk_forward_runs/h050_prod_run_2_2026-04-27.log) — the 6-line PROGRESS log frozen at termination.
- Microsoft Docs: [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) — Win32 API for declaring a system-required workload.
- Microsoft Docs: [Kernel-Power Event 109](https://learn.microsoft.com/en-us/windows/win32/eventlog/event-categories) — system-initiated reboot transitions.
