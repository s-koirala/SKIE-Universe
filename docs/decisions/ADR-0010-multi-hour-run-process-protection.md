---
id: ADR-0010
title: Multi-hour-run process protection on Windows — wake-lock + pre-launch checklist + resume-from-checkpoint
status: accepted
date: 2026-04-27
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

### Layer 1 — Process-level wake-lock (Windows-native)

The orchestrator's `__main__` block calls Win32 [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) via `ctypes` with the flag combination:

```
ES_CONTINUOUS | ES_SYSTEM_REQUIRED
```

| Flag | Purpose |
|---|---|
| `ES_CONTINUOUS` (0x80000000) | Apply the state until explicitly cleared, not just for the next call. |
| `ES_SYSTEM_REQUIRED` (0x00000001) | Forces the system idle timer to reset (system stays "active" → Windows Update + sleep timers do not fire). |

`ES_DISPLAY_REQUIRED` is intentionally NOT set so the display can sleep during a long run.

`ES_AWAYMODE_REQUIRED` was originally included but **removed in Round-2 audit-remediate (Q-1-2)** per [Microsoft Docs](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) Remarks: *"ES_AWAYMODE_REQUIRED should be used only when absolutely necessary by media-recording and media-distribution applications"*. A walk-forward orchestrator is neither, and on Windows-11 SKUs where Away Mode is disabled by default, the flag can fail or be partially honoured. ES_SYSTEM_REQUIRED alone defers Windows-Update reboots.

The previous execution state returned by `SetThreadExecutionState` on first acquire is captured and **restored exactly on final release** (Round-2 Q-1-1 fix), so the helper composes correctly under nested context managers via a refcount: outer acquire stores prev + sets system-required; inner acquire bumps refcount only (no syscall); inner release decrements refcount only; outer release restores the captured prev. This avoids clobbering any flags an outer caller (e.g. parent process, embedded host) had set.

**Mechanism rationale.** The Windows power manager treats a process as a system-required workload only if it explicitly declares so via this API. There is no automatic detection from CPU usage; a single-threaded EM loop at 97% one-core CPU does not by itself prevent a Windows Update reboot.

**Cross-platform behaviour.** On non-Windows hosts the call is a no-op. The orchestrator imports `ctypes.windll` only inside an `if sys.platform == "win32"` guard so the import does not raise on Linux/macOS.

**Out-of-scope.** The wake-lock does NOT prevent:
- User-initiated reboot (Event ID 1074).
- BSOD / kernel crash (Event ID 1001).
- Hardware power loss.
- Forced reboot via `shutdown /f`.
For these residual cases, Layer 3 (resume-from-checkpoint) is the recovery path.

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
- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — prior failure mode (HMM cov-redundancy; not OS-level).
- [docs/audits/audit_trail_2026-04-26_orchestrator-progress-logging.md](../audits/audit_trail_2026-04-26_orchestrator-progress-logging.md) — the patch that made this diagnosis legible.
- [Microsoft Docs: SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate).
- [Microsoft Docs: Kernel-Power Event 109](https://learn.microsoft.com/en-us/windows/win32/eventlog/event-categories).
- [Microsoft Docs: Power Awareness for Applications](https://learn.microsoft.com/en-us/windows/win32/power/power-awareness-for-applications).
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) `__main__` — wake-lock activation site.
- [scripts/supervised_run.py](../../scripts/supervised_run.py) — process supervisor wrapper (separate commit).
- [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) — pending-restart check (separate commit).
