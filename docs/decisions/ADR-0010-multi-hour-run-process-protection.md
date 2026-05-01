---
id: ADR-0010
title: Multi-hour-run process protection on Windows — idle-sleep wake-lock + pre-launch checklist + USOSvc-task disable + resume-from-checkpoint
status: accepted
date: 2026-04-27
amended: 2026-04-30 (Layer-1 framing correction + Layer-5 USOSvc task disable per P1-ADR-0010-LAYER-1-FRAMING-CORRECT + P1-ADR-0010-LAYER-AMENDMENT)
deciders: skoir
supersedes: P1-WIN-UPDATE-AUTO-REBOOT (follow-up filed by audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md)
---

# ADR-0010 — Multi-hour-run process protection on Windows

## Context

The H050 walk-forward run is expected to take 12-22 hours per the addendum revision r2 ([research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md](../../research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md) §4.4 + §5.4). Two distinct termination modes have been observed in the prod-run sequence:

1. **prod-run-1 (2026-04-26)** — operator-killed at +180 min for diagnostic investigation. Fixed: `P1-HMM-FULL-COV-1DIM-REDUNDANT` deduplication + `P1-ORCHESTRATOR-PROGRESS-LOGGING`.
2. **prod-run-2 (2026-04-27)** — externally killed at +4h37m by Windows Update auto-reboot. Documented at [docs/audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](../audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md). Root cause: Microsoft-Windows-Kernel-Power Event 109 ("Action: Power Action Reboot. Reason: Kernel API"); the system was marked "Active" because the orchestrator did not register itself as a system-required workload.

A 12-22 hour run that has any non-trivial probability of being killed by an OS-level reboot is operationally infeasible. Each prod-run-1 / prod-run-2 cycle costs the entire wall-clock to detect failure. The `P1-ORCHESTRATOR-PROGRESS-LOGGING` patch made the diagnosis legible, but did not prevent the termination.

## Decision

Three-layer process protection for any walk-forward run expected to exceed one hour. Layer 2 has two sub-layers (manual runbook + supervisor enforcement) that share the same checklist:

### Layer 1 — Process-level idle-sleep wake-lock (Windows-native)

**(Layer-1 framing correction landed 2026-04-30 per `P1-ADR-0010-LAYER-1-FRAMING-CORRECT`.)** This layer **prevents idle sleep** during a long-running compute. It does **NOT** prevent OS-initiated reboots; that path is addressed by Layer 2 (preflight refusal) + Layer 5 (USOSvc task disable, this commit).

Per Microsoft's documentation of [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) Remarks:

> *"This function can be used to prevent the system from entering sleep or turning off the display while an application is running."*

The Microsoft-documented contract is **idle-sleep + display-off prevention**, **not reboot suppression**. The 2026-04-29 prod-run-6 attempt-2 incident, where `ES_SYSTEM_REQUIRED` was active but a Microsoft-Windows-Kernel-Power Event 109 reboot occurred 49 minutes into the run, is consistent with the documented contract — the API was working as specified; the original ADR text simply over-stated its scope. See post-mortem [memo_h050-prodrun-postmortem_2026-04-30.md](../research_notes/memo_h050-prodrun-postmortem_2026-04-30.md) §5.1 for the verbatim Remarks citation.

The orchestrator's `__main__` block calls Win32 `SetThreadExecutionState` via `ctypes` with the flag combination:

```
ES_CONTINUOUS | ES_SYSTEM_REQUIRED
```

| Flag | Purpose |
|---|---|
| `ES_CONTINUOUS` (0x80000000) | Apply the state until explicitly cleared, not just for the next call. |
| `ES_SYSTEM_REQUIRED` (0x00000001) | Forces the system idle timer to reset, preventing **idle sleep**. (Does NOT prevent OS-initiated reboot.) |

`ES_DISPLAY_REQUIRED` is intentionally NOT set so the display can sleep during a long run.

`ES_AWAYMODE_REQUIRED` was originally included but **removed in Round-2 audit-remediate (Q-1-2)** per [Microsoft Docs](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) Remarks: *"ES_AWAYMODE_REQUIRED should be used only when absolutely necessary by media-recording and media-distribution applications"*. A walk-forward orchestrator is neither, and on Windows-11 SKUs where Away Mode is disabled by default, the flag can fail or be partially honoured.

The previous execution state returned by `SetThreadExecutionState` on first acquire is captured and **restored exactly on final release** (Round-2 Q-1-1 fix), so the helper composes correctly under nested context managers via a refcount: outer acquire stores prev + sets system-required; inner acquire bumps refcount only (no syscall); inner release decrements refcount only; outer release restores the captured prev. This avoids clobbering any flags an outer caller (e.g. parent process, embedded host) had set.

**Mechanism scope.** The Windows power manager treats a process as a system-required workload (suppressing idle-sleep timers) only if it explicitly declares so via this API. There is no automatic detection from CPU usage; a single-threaded EM loop at 97% one-core CPU does not by itself suppress idle-sleep transitions.

**Cross-platform behaviour.** On non-Windows hosts the call is a no-op. The orchestrator imports `ctypes.windll` only inside an `if sys.platform == "win32"` guard so the import does not raise on Linux/macOS.

**Out-of-scope (corrected 2026-04-30):** The wake-lock does NOT prevent any of:
- **OS-initiated reboot via the UsoSvc Task Scheduler tree** (this is the load-bearing reboot path on Windows-11 Home; addressed by **Layer 5** below).
- WUfB compliance-deadline override (Pro/Enterprise/Education only; not on Home edition).
- User-initiated reboot (Event ID 1074).
- `Restart-Computer` PowerShell cmdlet from an elevated session.
- WMI/CIM `Win32_OperatingSystem.Win32Shutdown(2)` invocations (some MDM agents).
- BSOD / kernel crash (Event ID 1001).
- Hardware power loss.
- Forced reboot via `shutdown /f`.

For the OS-initiated-reboot path, Layer 5 is the canonical mitigation. For BSOD / hardware events, Layer 3 (resume-from-checkpoint) is the recovery path.

### Layer 2 — Pre-launch runbook

Before launching any walk-forward run expected to exceed one hour:

1. Verify Windows Update has no pending-restart updates: `Get-WindowsUpdateLog` or `Restart-Required` registry check ([scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1)).
2. Verify Active Hours covers the expected runtime:
   - PowerShell: `Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -Name 'ActiveHoursStart','ActiveHoursEnd'`
   - Settings → Update & Security → Windows Update → Change active hours.
3. Verify the wake-lock is active by inspecting `powercfg /requests` after the orchestrator starts:
   ```
   powercfg /requests
   # Expected: SYSTEM section lists `[PROCESS] python.exe` (or `uv.exe`).
   ```
4. Confirm no scheduled tasks will run during the expected window: `schtasks /query /fo LIST | findstr /R /C:"^Next Run Time"`.
5. Confirm the supervisor wrapper (Layer 3 below) is in use rather than direct `python scripts/run_walk_forward.py` invocation.
6. **(Added 2026-04-30 per `P1-ADR-0010-LAYER-AMENDMENT`.)** Confirm the USOSvc reboot-task disable (Layer 5) is wired: `scripts/supervised_run.py` calls `disable_for_run(<run_dir>/_usosvc_disable_state.json)` after preflight passes and `restore_after_run(<state_path>)` in the cleanup `finally`. Launch from an elevated terminal (`Start-Process -Verb RunAs powershell.exe`); the helper's exit-code-2 ("elevation required") is the canonical signal that the operator forgot. The cross-hypothesis runbook template at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md) inherits this step (tracked under follow-up `P1-PRODRUN-RUNBOOK-TEMPLATE-USOSVC-STEP` for any per-hypothesis-instantiated runbook that pre-dates this amendment).

The runbook is published at [docs/research_notes/runbook_walk-forward-launch-prep_2026-04-27.md](../research_notes/runbook_walk-forward-launch-prep_2026-04-27.md) and the supervisor wrapper enforces the checklist programmatically.

> **Note (2026-04-29):** This Layer was extended from Windows-Update-specific to general production-run gating by [ADR-0011](ADR-0011-production-walkforward-runbook.md). The 2026-04-27 operator-facing per-run runbook was superseded on 2026-04-29 by the per-hypothesis runbook template at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md), instantiated per hypothesis under `research/01_hypothesis_register/<HXXX>/production_run_runbook.md`. The 2026-04-27 runbook remains historically valid for the H050 launch arc but is no longer the canonical reference.

### Layer 3 — Resume-from-checkpoint

Even with Layers 1 and 2, treat external termination as possible. The orchestrator writes per-fold artifacts (`fold_<N>.json`) to `artifacts/runs/H050/<run_id>/<sym>/folds/` *as each fold completes*. A relaunch with the same `run_id` (or a `--resume <run_id>` flag) detects already-completed folds by file presence and skips them.

**Scope of resume in this ADR phase: design only; implementation deferred.**

The resume design is documented here, but **implementation is deferred to follow-up `P1-PER-SYMBOL-RESUME`** because:

1. **The immediate prod-run-2 case (killed during ES fold 0) gains nothing from per-symbol resume** — no symbol completed before the kill. The wake-lock (Layer 1) is the load-bearing protection for the relaunch.
2. **RunContext modification is invasive.** Per-symbol resume requires the resumed run to use the SAME `run_id` so the cached `<run_dir>/<sym>/` artifacts are reachable. RunContext currently generates a fresh `run_id` per `capture(...)` call; threading a `run_id` parameter through `RunContext.__init__` + `capture()` + the `ReproLog` schema is a focused but distinct change that should be re-validated by the existing reproducibility tests.
3. **Per-symbol resume's marginal value is bounded by ~50% of wall-clock** (ES + NQ are roughly symmetric; resume after ES completes but NQ interrupted saves ~half). Per-fold resume (within an interrupted symbol) is what would meaningfully shrink recovery time, and that requires invasive `WalkForwardEngine.run` modification (tracked under `P1-WALK-FORWARD-PER-FOLD-CHECKPOINT`).

**Design (for the planned implementation):**

- The orchestrator writes `<run_dir>/<sym>/aggregate/metrics_summary.json` at end of each successful symbol via `_write_aggregate(agg_dir, metrics)`.
- A relaunch with `--resume <run_id>` inspects `<run_dir>/<sym>/aggregate/metrics_summary.json` per symbol BEFORE entering `_run_symbol_body`. If the file exists with `status="ok"` AND `n_folds >= 1`, the symbol is treated as already-complete: the orchestrator loads the cached metrics, registers the cached `model_hash_combined` in the per-universe roll-up, and skips re-execution.
- A `PROGRESS symbol start ... resume=cached` line is emitted so the resume is observable.
- The atomic-write convention is unchanged: `_write_aggregate` writes the JSON via `tmp.replace(out_path)` so a mid-write kill leaves no partial artifact.
- The CLI flag `--resume <RUN_ID>` is in the parser scaffolding (this commit) but raises `NotImplementedError` until `P1-PER-SYMBOL-RESUME` lands. This makes the planned interface visible without misleading the operator into thinking resume already works.

**What replaces resume in this commit:** the supervisor wrapper (Layer 4 — `scripts/supervised_run.py`) detects external-kill via post-mortem inspection of the orchestrator subprocess's exit code + final PROGRESS line; an operator confirming "OS reboot killed it" can choose to relaunch. The wake-lock prevents the avoidable terminations entirely; supervisor + manual relaunch handles the residual hardware/BSOD cases pending Layer 3 implementation.

### Layer 5 — USOSvc Task Scheduler reboot-task disable (added 2026-04-30)

**(Layer-5 added 2026-04-30 per `P1-ADR-0010-LAYER-AMENDMENT`.)** This layer **prevents OS-initiated reboot** by temporarily disabling the registered Windows Update Orchestrator (UsoSvc) reboot tasks for the duration of a long-running run. It addresses the failure mode that Layer 1 was incorrectly thought to address (Layer-1 contract is idle-sleep, not reboot suppression — see corrected framing above + post-mortem §5.1).

**Background.** On Windows-11 Home (the H050 host), Group Policy / WUfB compliance-deadline overrides are not available (Home edition does not support GPO; the host is not MDM-enrolled). The reboot path is therefore the **internal UsoSvc Task Scheduler tree**:

```
\Microsoft\Windows\UpdateOrchestrator\Reboot_AC
\Microsoft\Windows\UpdateOrchestrator\Reboot_Battery
\Microsoft\Windows\UpdateOrchestrator\Universal Orchestrator Start
\Microsoft\Windows\UpdateOrchestrator\Schedule Reboot
\Microsoft\Windows\UpdateOrchestrator\Schedule Wakeup
```

These tasks fire when Windows Update has staged updates whose installation requires a reboot — independently of Active Hours, of `ES_SYSTEM_REQUIRED`, and of WU-pause registry state. The canonical mitigation is to enumerate and `schtasks /Change /DISABLE` them for the run window, then restore on exit.

**Implementation.** Two artifacts:

- [scripts/preflight/manage_usosvc_reboot_tasks.ps1](../../scripts/preflight/manage_usosvc_reboot_tasks.ps1): PowerShell helper with `-Action {List, Disable, Enable}` subactions. Disable persists prior task state (Ready vs Disabled) to a JSON state file; Enable reads the JSON and restores per-task to its prior state. Atomic via tmp + Move-Item. Returns exit code 2 if elevation is required (the `\Microsoft\Windows\` task tree typically requires Administrator context for `schtasks /Change`).

- [src/skie_ninja/utils/usosvc_task_manager.py](../../src/skie_ninja/utils/usosvc_task_manager.py): Python wrapper exposing `list_tasks()`, `disable_for_run(state_path)`, `restore_after_run(state_path)`. Cross-platform-safe (returns a `{"action": "skipped"}` envelope on non-Windows hosts; the supervisor + tests can call them on Linux CI without conditional guards).

**Wiring (landed 2026-04-30 per `P1-SUPERVISOR-USOSVC-INTEGRATION`).** [scripts/supervised_run.py](../../scripts/supervised_run.py) calls `disable_for_run(state_path)` immediately after the preflight gate passes and `restore_after_run(state_path)` in a `finally` block around the orchestrator subprocess. The state file lives at `<log_dir>/h050_prod_run_<tag>.usosvc_state.json`. Both calls degrade gracefully on non-Windows (skipped envelope) and on non-elevated Windows (exit-code-2 + log; supervisor proceeds without Layer 5 protection rather than refusing to launch). Hard-kill cases (OS reboot mid-run) bypass the `finally` block; tracked under the existing `P1-SUPERVISOR-FINALLY-WRITE-ON-HARD-KILL` follow-up. Manual restore command surfaced in the supervisor log:

```
pwsh -File scripts/preflight/manage_usosvc_reboot_tasks.ps1 -Action Enable -StatePath <state_path>
```

**Operational requirement.** `schtasks /Change` against `\Microsoft\Windows\` tasks requires Administrator elevation. The supervisor must be launched from an elevated PowerShell or terminal (`Start-Process -Verb RunAs powershell.exe`); the helper's exit-code-2 ("elevation required") is the canonical signal that the operator forgot. Tracked under follow-up `P1-SUPERVISOR-ELEVATION-REQUIRED-PRECHECK` if a non-elevated default-launch failure mode becomes operationally common.

**Cross-platform.** The helper is Windows-only (`schtasks` is a Windows command). The Python wrapper degrades to a `{"skipped": "non-windows host"}` envelope on Linux/macOS so test fixtures, CI, and Linux-migration explorations (per `P1-LINUX-MIGRATION-CONSIDERATION`) succeed without conditional guards in the supervisor.

**Out-of-scope.** The disable does NOT cover:
- WUfB compliance-deadline overrides (not applicable on Home edition; relevant on Pro/Enterprise/Education where GPO is available — separate mitigation needed under `P1-WUFB-COMPLIANCE-DEADLINE-MITIGATION` if the host migrates).
- Manual user reboot (Event ID 1074).
- BSOD / hardware power loss.

For Pro/Enterprise hosts the WUfB compliance-deadline mitigation is `Set-PSWindowsUpdate`-style policy delays, not the USOSvc-task disable; tracked under the follow-up above.

## Alternatives considered

### A. Disable Windows Update entirely

Rejected. Disabling Windows Update has security implications and requires Group Policy / registry edits that persist beyond the run. The wake-lock is reversible at process exit.

### B. Run the orchestrator inside a Windows service

Rejected. Service mode requires UAC elevation, breaks the existing test fixtures (which import `run` directly), and adds a separate code path that the audit-remediate-loop would have to re-validate. The wake-lock achieves the same OS-level protection without architectural surgery.

### C. Run on Linux / WSL

Considered but deferred. The user's BLAS pinning ([ADR-0009](ADR-0009-blas-thread-pinning.md)) is currently calibrated against the Windows OpenBLAS 0.3.31 stack documented in the bench manifest. Migrating to Linux requires re-running the [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py) microbench under the new BLAS vendor and re-validating the constant-factor claims. This is a separate decision tracked under follow-up `P1-LINUX-MIGRATION-CONSIDERATION`.

### D. Resume-from-checkpoint as the *only* protection (no wake-lock)

Rejected. Resume incurs cold-fit cost on the first fold of each interrupted run; for the H050 27-cell × 2-symbol grid, a single Windows Update reboot mid-run can cost 2-4 hours of recomputed work even with resume. The wake-lock prevents the avoidable terminations entirely; resume is the safety net for the remaining (BSOD, hardware) cases.

## Consequences

### Adopted

- The orchestrator's `__main__` registers itself as system-required for the lifetime of the process. Display and idle-timer can sleep; the system cannot reboot or sleep without explicit user action.
- A `scripts/preflight/` directory is created with the pre-launch verification scripts.
- The supervisor wrapper at `scripts/supervised_run.py` (separate commit; tracked under `P1-WIN-UPDATE-AUTO-REBOOT` Layer 4) is the canonical launch path and enforces the runbook programmatically.
- `artifacts/runs/H050/<run_id>/<sym>/folds/fold_<N>.json` is written atomically as each fold completes; relaunch detects and skips already-complete folds.

### Trade-offs accepted

- The wake-lock keeps the system "active" during the run, which means scheduled defragmentation, antivirus scans, and other maintenance tasks may also defer. The orchestrator already runs single-BLAS-thread per ADR-0009 so the system has spare cores; competing maintenance work would not have measurably impacted the run anyway.
- Resume reads cached fold artifacts on relaunch — adds I/O at the start of each resumed symbol. Cost is bounded by `n_folds * artifact_size`; on the H050 grid this is tens of MB total, sub-second to read.
- The audit trail must be re-run on any future change to `_fit_fold`'s output schema, since `fold_<N>.json` becomes the resume source-of-truth. A schema-version tag inside each artifact (`"schema_version": "h050.v1"`) defends against silent breakage.

### Residual risk

Hardware-level events (UPS battery failure, sudden power loss to the wall) are not addressed by any of these layers. The recovery is operational: maintain a UPS for the workstation. Tracked under follow-up `P1-WORKSTATION-UPS-RECOMMENDATION` (advisory only; out of repo scope).

Group Policy changes that re-enable Windows Update auto-reboot regardless of `ES_SYSTEM_REQUIRED` are theoretically possible but not present on the current host. The pre-launch runbook's `Get-ItemProperty` check on the registry catches a configuration drift if it occurs.

## Empirical justification

The wake-lock approach is the canonical Microsoft-recommended pattern for long-running computational workloads on Windows; documented at [Microsoft Docs: SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) and used by long-running scientific-computing patterns (e.g. installer / patch / build pipelines that hold the system awake during multi-hour operations).

Resume-from-checkpoint is the standard pattern in scientific computing (DASK, Snakemake, Nextflow). Per [~/.claude/CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md) "Verification" → "Confirm numerical results against a benchmark", the resumed-run output must be bit-identical to the un-interrupted-run output for the same `run_id` + `random_seed`.

**Resume implementation status: deferred.** Layer 3 of this ADR is design only in this commit; the implementation (and the bit-identical-output regression test that validates it) is tracked under follow-up `P1-PER-SYMBOL-RESUME`. The `--resume <RUN_ID>` CLI flag is parsed but raises `NotImplementedError` so the operator gets an immediate honest error rather than a silent fresh run. The wake-lock (Layer 1) + supervisor (Layer 2 enforcement) are the load-bearing protections in this commit.

## References

- [docs/audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](../audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md) — the diagnosis trail that motivated this ADR.
- [docs/audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](../audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md) — Round-2 incident (Kernel-Power 109 despite acquired wake-lock) that exposed the Layer-1 framing defect.
- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — prior failure mode (HMM cov-redundancy; not OS-level).
- [docs/audits/audit_trail_2026-04-26_orchestrator-progress-logging.md](../audits/audit_trail_2026-04-26_orchestrator-progress-logging.md) — the patch that made this diagnosis legible.
- [docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md](../research_notes/memo_h050-prodrun-postmortem_2026-04-30.md) — comprehensive H050 prod-run post-mortem; §5.1 verbatim citation of the SetThreadExecutionState Remarks (load-bearing Layer-1 framing correction); §5.2 USOSvc Task Scheduler tree analysis (load-bearing Layer-5 motivation).
- [Microsoft Docs: SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) — Remarks pin Layer-1 contract to idle-sleep + display-off prevention only.
- [Microsoft Docs: schtasks](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-change) — `/Change /DISABLE` semantics for Layer 5.
- [Microsoft Docs: Update Orchestrator service (UsoSvc)](https://learn.microsoft.com/en-us/windows/deployment/update/) — internal task scheduler tree for OS-initiated reboots on Windows-11 Home.
- [Microsoft Docs: Kernel-Power Event 109](https://learn.microsoft.com/en-us/windows/win32/eventlog/event-categories).
- [Microsoft Docs: Power Awareness for Applications](https://learn.microsoft.com/en-us/windows/win32/power/power-awareness-for-applications).
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) `__main__` — wake-lock activation site (Layer 1).
- [scripts/supervised_run.py](../../scripts/supervised_run.py) — process supervisor wrapper (Layer 4 enforcement; Layer 5 wiring deferred to `P1-SUPERVISOR-USOSVC-INTEGRATION`).
- [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) — pending-restart + Active-Hours check (Layer 2 — pre-launch).
- [scripts/preflight/manage_usosvc_reboot_tasks.ps1](../../scripts/preflight/manage_usosvc_reboot_tasks.ps1) — Layer 5 USOSvc reboot-task disable (this commit, 2026-04-30).
- [src/skie_ninja/utils/usosvc_task_manager.py](../../src/skie_ninja/utils/usosvc_task_manager.py) — Python wrapper around the Layer-5 PS1 helper (this commit).
