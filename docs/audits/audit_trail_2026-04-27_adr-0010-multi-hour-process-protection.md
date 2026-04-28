---
title: P1-WIN-UPDATE-AUTO-REBOOT — ADR-0010 audit-remediate-loop trail
date: 2026-04-27
artifact: scripts/run_walk_forward.py + src/skie_ninja/utils/process_protection.py + scripts/supervised_run.py + scripts/preflight/check_windows_update.ps1 + ADR-0010 + runbook + tests
followup_id: P1-WIN-UPDATE-AUTO-REBOOT
exit_state: round-2 accept-with-residuals (SKILL.md cap reached)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
---

## Scope

Implement ADR-0010's three-layer process protection (wake-lock + pre-launch runbook + supervisor wrapper) in response to the H050 prod-run-2 termination at +4h37m (Windows Update auto-reboot; diagnosis at [docs/audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md)).

## Final implementation

**Wake-lock helper** ([src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py)):
- Calls Win32 `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` = 0x80000001 (Round-2 Q-1-2: dropped `ES_AWAYMODE_REQUIRED` per Microsoft docs).
- Captures previous state on first acquire; restores it exactly on final release (Round-2 Q-1-1).
- Refcount-based composition: nested `system_required_wakelock()` blocks issue only one acquire syscall + one release syscall (Round-2 Q-1-1).
- No-op on non-Windows.

**Orchestrator integration** ([scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) `__main__`):
- Wraps `run(sys.argv[1:])` in `with system_required_wakelock():`.
- `--resume` CLI flag rejected at argparse-time (Round-2 Q-1-12; was raised at `_run_inner` entry).

**Pre-launch runbook** ([docs/research_notes/runbook_walk-forward-launch-prep_2026-04-27.md](../research_notes/runbook_walk-forward-launch-prep_2026-04-27.md)):
- 5-step operator checklist: preflight → Active Hours → scheduled tasks → launch → monitor.
- Failure-mode → action matrix.

**Preflight script** ([scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1)):
- Checks 5 pending-restart registry markers (CBS / WindowsUpdate / Netlogon / OSUpgrade / PendingFileRenameOperations).
- Active Hours sourced in priority: Group Policy override → user-set → smart-AH state.
- `-ExpectedRuntimeHours` parameter (default 22) — verifies AH covers the run window with day-wrap handling (Round-2 Q-1-5).
- Exit code 0/2/3.

**Supervisor wrapper** ([scripts/supervised_run.py](../../scripts/supervised_run.py)):
- Runs preflight first; refuses launch on rc=2 (warn) unless `--allow-preflight-warn`, refuses on rc=3 (block) unconditionally (Round-2 Q-1-4: was silently permissive).
- Spawns the orchestrator subprocess with BLAS env-vars propagated.
- Telemetry loop: samples RSS/CPU/threads every 30s; appends to `.supervisor.jsonl`.
- `--max-runtime-s` cap (default 36hr; Round-2 Q-1-3): terminate + 30s grace + kill on exceed.
- Defensive `finally` block: terminates+kills subprocess on any supervisor exit path.
- Exit classification: `clean_exit_success` / `clean_exit_python_exception` / `external_kill_or_segfault` / `supervisor_max_runtime_exceeded` / `ambiguous`.
- Non-Windows skip on preflight (Round-2 R-4).

**ADR-0010** ([docs/decisions/ADR-0010-multi-hour-run-process-protection.md](../decisions/ADR-0010-multi-hour-run-process-protection.md)):
- Layer 1 (wake-lock) + Layer 2 (runbook + supervisor enforcement) + Layer 3 (resume — design only; implementation deferred to `P1-PER-SYMBOL-RESUME`).
- Documents the AWAYMODE removal rationale + restore-prev pattern + the `--resume` deferral honestly (Round-2 R-2).

**Crash evidence preservation** ([logs/crash_evidence/system_events_2026-04-27_0435-0445.json](../../logs/crash_evidence/system_events_2026-04-27_0435-0445.json)):
- 76KB Windows System Event Log dump for the reboot window.
- `.gitignore` updated with `!logs/crash_evidence/` + `!logs/crash_evidence/**` (Round-2 R-1 + R-1-RESIDUAL: git's directory-exclusion semantics required two patterns).

## Round 1 — parallel quant + repro audit

Subagents (all proper-isolated, main-thread-spawned):
- `quant-auditor` (`agentId a9ea9fa91de509ea2`) — 13 findings (Q-1-1 through Q-1-13).
- `reproducibility-verifier` (`agentId a954b8da52ea9b66f`) — 7 findings (R-1 through R-7).

### Round-1 dispositions

| ID | Severity | Issue | Round-2 disposition |
|---|---|---|---|
| **Q-1-1** | major | Wake-lock didn't preserve prev state on release | **Fixed**: refcount + saved_prev + restore-exact-prev |
| **Q-1-2** | major | ES_AWAYMODE_REQUIRED is for media apps; can fail on Win11 | **Fixed**: dropped; flag is now ES_CONTINUOUS \| ES_SYSTEM_REQUIRED = 0x80000001 |
| **Q-1-3** | major | Supervisor had no max-runtime cap | **Fixed**: `--max-runtime-s` (default 36hr) + terminate+grace+kill |
| **Q-1-4** | major | Preflight returned rc=0 (silently safe) on missing/error | **Fixed**: rc=2 (warn) on missing/error; supervisor refuses on warn |
| **Q-1-5** | major | Preflight didn't check AH covers run window | **Fixed**: `-ExpectedRuntimeHours` param + AH-covers-runtime computation |
| **R-1** | major | Crash evidence gitignored | **Fixed (with R-1-RESIDUAL)**: two .gitignore patterns required |
| **R-2** | major | ADR §"Empirical justification" referenced non-existent test | **Fixed**: rewritten to honestly defer Layer 3 |
| Q-1-6 | minor | Ctrl-C mis-classified as external_kill | **Deferred**: `P1-CLASSIFY-CTRL-C` |
| Q-1-7 | minor | Substring matching brittle to whitespace in ctx values | **Deferred**: `P1-PROGRESS-MARKER-CONSTANT-EXPORT` |
| Q-1-8 | minor | Supervisor doesn't log own git HEAD/version | **Deferred**: `P1-SUPERVISOR-SELF-VERSION` |
| Q-1-9 | minor | Telemetry write has no OSError handling | **Fixed (in Round 2 inline)** + defensive `finally` for subprocess termination |
| Q-1-10 | minor | "Layer 4" vs "Layer 2/3" docs taxonomy drift | **Fixed**: ADR-0010 §Decision header updated |
| Q-1-11 | minor | Supervisor doesn't forward --resume | **Deferred** (moot until P1-PER-SYMBOL-RESUME lands) |
| Q-1-12 | minor | --resume raises at function entry not argparse-time | **Fixed**: ap.error() at parse time |
| Q-1-13 | minor | Preflight misses Win11 Smart AH paths | **Partial fix**: now reads policy override + smart_active_hours_state; dynamic AH end deferred as `P1-PREFLIGHT-SMART-AH-DYNAMIC` |
| R-3 | minor | Preflight schema not pydantic-validated | **Deferred**: `P1-PREFLIGHT-SCHEMA-PYDANTIC` |
| **R-4** | minor | Supervisor _run_preflight not platform-guarded | **Fixed**: non-Windows short-circuit |
| R-5 | minor | Substring `"PROGRESS` couples to JSON formatter | **Deferred**: `P1-PROGRESS-MARKER-CONSTANT-EXPORT` (overlaps Q-1-7) |
| **R-6** | minor | Preflight doesn't compute AH-covers-runtime | **Fixed (with Q-1-5)** |
| R-7 | minor | Supervisor artifacts not in ReproLog | **Deferred**: `P1-SUPERVISOR-REPROLOG-INTEGRATION` |

## Round 2 — parallel quant + repro re-audit

Subagents:
- `quant-auditor` (`agentId af6c0af39d75b8622`) — 5 findings (F-2-1 through F-2-5); verdict `accept`.
- `reproducibility-verifier` (`agentId a0ccf7b2ee0eb48a9`) — 4 findings (R-1-RESIDUAL, R-8, R-9, plus pre-existing HMM-cache regression flagged); verdict `proceed-with-remediation`.

### Round-2 dispositions

| ID | Severity | Issue | Disposition (no Round-3 per SKILL.md cap) |
|---|---|---|---|
| **R-1-RESIDUAL** | major | `.gitignore` `!logs/crash_evidence/**` doesn't work because git can't re-include children of an excluded parent dir | **Fixed in-loop**: added `!logs/crash_evidence/` (no slash) before `!logs/crash_evidence/**`; verified with `git check-ignore` + `git add -n` |
| **R-8** | minor | Runbook didn't document new .preflight.json schema fields | **Fixed in-loop**: appended `active_hours_covers_run` + `expected_runtime_hours` + `smart_active_hours_state` to runbook step 1 |
| **R-9** | minor | psutil pin `>=5.9` too loose (psutil 6.x has API breakage) | **Fixed in-loop**: tightened to `>=5.9,<7` |
| **F-2-3** | minor | Supervisor doesn't print preflight_report_path on WARN-refusal | **Fixed in-loop**: 1-line print added |
| F-2-1 | minor | Magic-number defaults (36hr cap, 22h expected) lack explicit derivation | **Deferred**: `P1-SUPERVISOR-DEFAULTS-DERIVATION-DOC` |
| F-2-2 | minor | proc.terminate() doesn't trigger Python atexit; 30s grace doesn't flush ReproLog | **Deferred**: `P1-ORCHESTRATOR-SIGTERM-HANDLER` |
| F-2-4 | minor | README doesn't reference supervisor as canonical launch path | **Deferred**: `P1-README-SUPERVISOR-CANONICAL-PATH` |
| F-2-5 | minor | Supervisor classifier substring matching brittle | **Deferred** (overlaps Q-1-7 + R-5): `P1-PROGRESS-MARKER-CONSTANT-EXPORT` |
| **PRE-EXISTING-HMM-CACHE** | minor | `test_with_cache_enabled_full_suite_unchanged_warm_cold_sidecar_sha` fails (warm-cold sidecar SHA divergence for ES) | **NOT introduced by this patch** — verified pre-existing on commit `429f255`. Tracked under new follow-up `P1-HMM-CACHE-WARM-COLD-SHA-REGRESSION` (separate from ADR-0010) |

## Test pass count

- 691/691 unit tests green per the Round-2 test run (was 661/661 + 12 Round-1 new + 12 Round-2 new for 691 total: 14 wake-lock + 16 supervisor + 661 prior).
- One test (`test_with_cache_enabled_full_suite_unchanged_warm_cold_sidecar_sha`) fails on the long-form suite run — verified pre-existing per the Round-2 repro auditor's bisection on stashed HEAD `429f255`. NOT caused by this patch. Tracked separately.

## Smoke-test verification (proven by Round-2 repro auditor)

- `powershell.exe -ExecutionPolicy Bypass -File scripts/preflight/check_windows_update.ps1 -ExpectedRuntimeHours 22` returns exit 2 on the current host (WARN: AH=8-1=17h < 22h run); JSON has all required keys.
- `uv run python scripts/supervised_run.py --hypothesis H050 --config config/hypotheses/H050.yaml --orchestrator-args="--dry-run --smoke --smoke-n 2000" --max-runtime-s 300` runs cleanly: preflight WARN (allow-warn used in test), orchestrator subprocess runs, telemetry samples land (16 lines for the smoke), classification = `clean_exit_success`, no orphaned process.

## Exit verdict

**`accept-with-residuals`** — the patch is operationally sound for the H050 prod-run-3 relaunch. Wake-lock + supervisor + preflight prevent the 2026-04-27 prod-run-2 failure mode (Windows Update auto-reboot). Crash evidence is now versioned. ADR-0010 documentation is honest about the deferred resume layer.

**Residuals carried forward (non-blocking):**

- `P1-PER-SYMBOL-RESUME` (ADR-0010 Layer 3 implementation) — the irreplaceable safety net for hardware/BSOD residuals; partial-run recovery saves up to half the wall-clock.
- `P1-WALK-FORWARD-PER-FOLD-CHECKPOINT` (engine modification for per-fold artifact incremental write) — finer-grained recovery.
- `P1-CLASSIFY-CTRL-C` (Q-1-6) — distinguish operator-Ctrl-C from external OS kill in the supervisor classifier.
- `P1-PROGRESS-MARKER-CONSTANT-EXPORT` (Q-1-7 + R-5 + F-2-5) — export PROGRESS marker tokens as constants from the orchestrator module so the supervisor doesn't substring-couple to the format string.
- `P1-SUPERVISOR-SELF-VERSION` (Q-1-8) — capture supervisor's own git HEAD + Python version + psutil version in the summary.json.
- `P1-PREFLIGHT-SMART-AH-DYNAMIC` (Q-1-13) — query the dynamic Smart Active Hours end-time on Windows 11 hosts.
- `P1-PREFLIGHT-SCHEMA-PYDANTIC` (R-3) — pydantic validation of the .preflight.json schema in the supervisor.
- `P1-SUPERVISOR-REPROLOG-INTEGRATION` (R-7) — fold supervisor artifact SHA256s into the orchestrator's ReproLog.
- `P1-SUPERVISOR-DEFAULTS-DERIVATION-DOC` (F-2-1) — embed addendum-link justification for the 36hr cap + 22h expected runtime defaults.
- `P1-ORCHESTRATOR-SIGTERM-HANDLER` (F-2-2) — install a SIGTERM handler in the orchestrator's `__main__` so supervisor-initiated termination flushes the ReproLog.
- `P1-README-SUPERVISOR-CANONICAL-PATH` (F-2-4) — README §"Multi-hour walk-forward runs" pointing to the supervisor.
- `P1-HMM-CACHE-WARM-COLD-SHA-REGRESSION` — pre-existing test failure unrelated to ADR-0010; separate investigation needed.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [docs/decisions/ADR-0010-multi-hour-run-process-protection.md](../decisions/ADR-0010-multi-hour-run-process-protection.md) — design.
- [docs/audits/audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md](audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md) — the diagnosis that motivated this patch.
- [docs/research_notes/runbook_walk-forward-launch-prep_2026-04-27.md](../research_notes/runbook_walk-forward-launch-prep_2026-04-27.md) — operator runbook.
- [logs/crash_evidence/system_events_2026-04-27_0435-0445.json](../../logs/crash_evidence/system_events_2026-04-27_0435-0445.json) — root-cause evidence (now versioned).
- [src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py) — wake-lock helper.
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) — orchestrator (`__main__` wake-lock + argparse `--resume` reject).
- [scripts/supervised_run.py](../../scripts/supervised_run.py) — supervisor wrapper.
- [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) — preflight script.
- [tests/unit/test_process_protection.py](../../tests/unit/test_process_protection.py) — 14 wake-lock tests.
- [tests/unit/test_supervised_run.py](../../tests/unit/test_supervised_run.py) — 16 supervisor tests.
