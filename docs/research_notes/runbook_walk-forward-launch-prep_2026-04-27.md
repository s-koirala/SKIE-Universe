---
title: H050 walk-forward launch — pre-launch runbook (ADR-0010 Layer 2)
date: 2026-04-27
type: runbook
status: superseded
superseded_by: docs/decisions/ADR-0011-production-walkforward-runbook.md, research/_templates/production_run_runbook.md
superseded_date: 2026-04-29
applies_to: any walk-forward run expected to exceed 1 hour wall-clock
supersedes: prior ad-hoc launch (no pre-launch checks)
---

> **SUPERSEDED 2026-04-29** — this operator-facing per-run runbook is replaced by the per-hypothesis runbook template at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md), instantiated per hypothesis under [research/01_hypothesis_register/<HXXX>/production_run_runbook.md](../../research/01_hypothesis_register/) and bound by [ADR-0011](../decisions/ADR-0011-production-walkforward-runbook.md). The 5-step content below remains historically valid for the H050 launch arc but is no longer the canonical reference. Empirical basis for supersession: [memo_h050-prodrun-retrospective_2026-04-29.md](memo_h050-prodrun-retrospective_2026-04-29.md).

# H050 walk-forward launch — pre-launch runbook

This runbook is the operator-facing checklist for launching a multi-hour walk-forward run on Windows. It implements [ADR-0010](../decisions/ADR-0010-multi-hour-run-process-protection.md) Layer 2 (pre-launch verification) and is enforced programmatically by [scripts/supervised_run.py](../../scripts/supervised_run.py) which runs the same checks before spawning the orchestrator subprocess.

The motivation is the 2026-04-27 prod-run-2 termination: a Windows Update auto-reboot killed the run at +4h37m. Diagnosis: [docs/audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](../audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md).

## Step-by-step (manual operator path)

### 1. Run the preflight check

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\preflight\check_windows_update.ps1
```

The script returns exit code 0 (safe), 2 (warn), or 3 (block). It writes a JSON report to stdout listing:
- `pending_restart` — true if any of `CBS RebootPending`, `WindowsUpdate Auto Update RebootRequired`, `PendingFileRenameOperations`, `Netlogon JoinDomain`, or Win11 `WindowsUpdate OSUpgrade` markers are present.
- `active_hours_start` / `active_hours_end` — current Active Hours configuration. Sourced in priority order: Group Policy override → user-set value.
- `active_hours_covers_run` — true if the next `expected_runtime_hours` window stays inside Active Hours; false if it would extend past AH end; null if AH is not configured (Round-2 ADR-0010 Q-1-5).
- `expected_runtime_hours` — int echoed from the `-ExpectedRuntimeHours` parameter (default 22 per H050 addendum §4.4 upper bound).
- `smart_active_hours_state` — int|null. If 1, Smart Active Hours is enabled and AH end-time is dynamic; the static value is informational only. Operators should widen AH manually or pause Windows Update.
- `last_boot_time` — timestamp of last system boot.

If exit code is 3 (block): **do not launch**. Either reboot to clear the pending update first, or defer the run.

### 2. Verify Active Hours covers the expected runtime

The H050 walk-forward run is estimated at 12-22 hours per the [HMM covariance d=1 equivalence addendum](../../research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md) §4.4. Active Hours must span the expected runtime to prevent Windows Update from initiating reboots inside the window.

Set Active Hours via:
- **Settings UI**: Settings → Update & Security → Windows Update → Change active hours → set to span your run window (max 18 hours per the OS limit).
- **PowerShell** (admin):
  ```powershell
  Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -Name 'ActiveHoursStart' -Value 0
  Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -Name 'ActiveHoursEnd' -Value 18
  ```
- For runs that exceed the 18-hour Active Hours cap, additionally pause Windows Update for up to 35 days via Settings → Windows Update → Pause updates.

### 3. Pause non-essential scheduled tasks

```powershell
schtasks /query /fo LIST | findstr /R /C:"^Next Run Time"
```

Identify any tasks scheduled to run during the expected window. Disable them temporarily:
```powershell
Disable-ScheduledTask -TaskName "<task-name>"
# Re-enable after run completes
```

Common offenders: defragmentation, disk cleanup, antivirus full scans.

### 4. Launch the orchestrator under the supervisor

**Canonical command** (recommended; runs the runbook checks programmatically + captures resource telemetry):

```powershell
$env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; $env:OPENBLAS_NUM_THREADS=1
uv run python scripts\supervised_run.py --hypothesis H050 --config config\hypotheses\H050.yaml
```

**Direct invocation** (only if the supervisor is unavailable; same wake-lock behaviour but no resource telemetry, no pre-launch verification):

```powershell
$env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; $env:OPENBLAS_NUM_THREADS=1
uv run python scripts\run_walk_forward.py --hypothesis H050 --config config\hypotheses\H050.yaml
```

The wake-lock acquired by the orchestrator's `__main__` (via [src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py) `system_required_wakelock`) is the primary defence against Windows-Update reboots. To verify it is active after launch:

```powershell
powercfg /requests
# Expected: SYSTEM section lists `[PROCESS] python.exe` (or whichever Python the venv uses).
```

If the SYSTEM section does NOT list a Python entry, the wake-lock did not engage. Diagnose:
- Ensure the orchestrator was launched via `__main__` (not imported from another script — only `__main__` triggers `setup_logging` + `system_required_wakelock`).
- Check for an `wakelock acquired` INFO line in the JSON log stream.

### 5. Monitor the run

```powershell
Get-Content -Wait -Tail 50 logs\walk_forward_runs\h050_prod_run_<DATE>.log | Select-String "PROGRESS"
```

Or via the supervisor's combined view:
```powershell
Get-Content -Wait -Tail 50 logs\walk_forward_runs\h050_prod_run_<DATE>.log
```

Healthy signals:
- `PROGRESS hmm-fit done elapsed=<N>s` lines for each completed fold (long; 5-50 min × 5-10 restarts × 1 trajectory after dedup).
- `PROGRESS fold-fit done elapsed=<N>s` for each completed outer fold.
- `PROGRESS symbol done` after each symbol completes.
- Final `PROGRESS run done` at completion.

Failure signals:
- `PROGRESS <phase> failed exc=<ExceptionType>` — Python exception inside the body (the wrapper try/except caught it; the exception will also be in the stderr).
- Log goes silent for >10 min without a `done` or `failed` — process likely killed externally (OS-level). Check `tasklist | findstr python` to confirm process is gone.

## Failure-mode → action matrix

| Symptom | Action |
|---|---|
| Preflight returns exit 3 (block) | Reboot to clear pending update; rerun preflight; only launch when exit 0 |
| `powercfg /requests` does not list Python after launch | Wake-lock didn't engage; kill run, debug `process_protection.py`, relaunch |
| Log silent >10 min with no done/failed | Check `tasklist`; if process gone, check Windows System Event Log for Kernel-Power Event 109 (Windows-Update reboot); relaunch with cleared pending update |
| `PROGRESS hmm-fit failed exc=<X>` | Python exception; inspect stderr for traceback; fix and relaunch |
| `PROGRESS run done` but no `metrics_summary.json` | Bug in `_write_aggregate`; investigate before next run |

## Implemented by

- [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) — pending-restart + Active Hours check (Step 1).
- [src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py) — `system_required_wakelock()` context manager (Step 4 wake-lock).
- [scripts/supervised_run.py](../../scripts/supervised_run.py) — supervisor wrapper that runs the runbook programmatically + samples RSS/CPU/threads (Step 4 canonical path).
- [docs/decisions/ADR-0010-multi-hour-run-process-protection.md](../decisions/ADR-0010-multi-hour-run-process-protection.md) — design rationale.

## Audit-trail expectation

When a multi-hour run is launched under the supervised path, the supervisor writes:

- `logs/walk_forward_runs/h050_prod_run_<DATE>.log` — orchestrator JSON log (PROGRESS markers + INFO/WARN/ERROR).
- `logs/walk_forward_runs/h050_prod_run_<DATE>.supervisor.jsonl` — supervisor telemetry (per-sample RSS, CPU%, thread count, latest PROGRESS line).
- `logs/walk_forward_runs/h050_prod_run_<DATE>.preflight.json` — preflight check result.

These three artifacts together establish the run's reproducibility envelope. Per [~/.claude/CLAUDE.md](C:/Users/skoir/.claude/CLAUDE.md) §Reproducibility: every run logs git HEAD, project-venv `pip freeze`, dataset checksum, RNG seed, model commit hash. The orchestrator's existing `RunContext` covers those; the supervisor adds operational telemetry on top.
