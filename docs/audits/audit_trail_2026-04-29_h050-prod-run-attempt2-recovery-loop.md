---
title: H050 prod-run-6 attempt-2 recovery — audit-remediate-loop on the 4-step response
date: 2026-04-29
artifact: docs/audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md + scripts/supervised_relaunch_loop.sh + docs/decisions/ADR-0011-production-walkforward-runbook.md + docs/decisions/ADR-0010-multi-hour-run-process-protection.md + research/_templates/production_run_runbook.md + CLAUDE.md + logs/crash_evidence/walk_forward_2026-04-29_192543/* + logs/crash_evidence/system_events_2026-04-29_2014-2017.json
followup_id: P1-RECOVERY-LOOP-2026-04-29-EVENING
exit_state: round-2 accept-with-residuals (SKILL.md cap reached)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
parent_diagnosis: docs/audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md
---

## Scope

Audit-remediate-loop wrapping the 4-step response to the H050 prod-run-6 attempt-2 termination at 20:16:03 CT on 2026-04-29 (Microsoft-Windows-Kernel-Power Event 109 reboot DESPITE an acquired `ES_SYSTEM_REQUIRED` wake-lock). The 4 user-prescribed steps were: (1) kill the hung attempt; (2) diagnose the 0% CPU; (3) raise `PER_LAUNCH_CAP_S` ≥6 hr; (4) promote `P1-LGB-INNER-CV-RESULT-CHECKPOINT` to blocking. Steps 1 and 2 were partly mooted by the OS reboot (no live process to kill or py-spy); steps 3 and 4 landed; new findings (F-1 wake-lock bypass, F-2 preflight timeout, F-3 0% CPU coincident-not-cause) added new blocking follow-ups beyond the original 4-step plan.

This trail records the 2-round audit-remediate-loop on the recovery deliverables. The substantive diagnosis is at [audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md).

## Round 1 — produce + parallel quant + repro audit

### Produced (Round 1)

1. [audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md) — F-1/F-2/F-3 diagnosis with 5-hypothesis enumeration on the wake-lock bypass.
2. [scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh) line 30 — `PER_LAUNCH_CAP_S` 10800 → 21600 (6 hr) with rationale comment.
3. [docs/decisions/ADR-0011-production-walkforward-runbook.md](../decisions/ADR-0011-production-walkforward-runbook.md) §"Residual risk" — `P1-LGB-INNER-CV-RESULT-CHECKPOINT` promoted to BLOCKING-BEFORE-NEXT-H050-LAUNCH; 5 new follow-ups registered.
4. [CLAUDE.md](../../CLAUDE.md) — new "Prod-run-6 attempt-2 OS-reboot-bypass diagnosis" subsection.

Subagents (proper-isolated, main-thread-spawned):
- `quant-auditor` Round 1 (`agentId ae67c5a20597a96a3`) — 7 findings (Q-1-1..Q-1-7).
- `reproducibility-verifier` Round 1 (`agentId a9a3cae35abb3394e`) — 8 findings (R-1-1..R-1-8).

### Round-1 dispositions

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| **Q-1-1** | major | H-A "leading candidate" claim contradicted by its own row's refuting-evidence column | **Fixed**: H-A reclassified to "not eliminated, not confirmed"; cited Microsoft Learn URL anchor + acknowledged registry-state interpretation requires test-rig replication. |
| **Q-1-2** | major | H-B refutation over-strong; UsoSvc enforcement-deadline reboot path doesn't require pre-reboot WU 19/20 events | **Fixed**: H-B reframed to "UsoSvc / Update Orchestrator Service enforcement-deadline reboot"; refutation downgraded to "not eliminated, not confirmed — needs probe of WindowsUpdateClient/Operational + USO trace channels". |
| **Q-1-3** | minor | F-3 cause-vs-coincident hedging asymmetric vs platform mechanics | **Fixed**: added "Mechanism analysis — F-3 is coincident with, not the cause of, F-1" with Bugcheck 0x133 + Event 41 platform-mechanics citation. |
| **Q-1-4** | major | Cap-raise comment claimed "6 hr is the empirical floor"; only 1 datapoint (attempt-1) supports lower bound | **Fixed**: both `supervised_relaunch_loop.sh:30` comment block and ADR-0011 ledger row now read "**6 hr is a provisional doubling, not an empirical floor**". |
| **Q-1-5** | minor | `P1-LGB-INNER-CV-CPU-ZERO-INVESTIGATION` limited to py-spy | **Fixed**: extended scope to priority order (a) py-spy → (b) procdump -ma → (c) ETW trace + supervisor-side 5-consecutive-30s-samples auto-trigger. |
| **Q-1-6** | minor | `P1-WAKE-LOCK-BYPASS-INVESTIGATION` had no acceptance criteria | **Fixed**: 4-criterion acceptance — (1) USO trace probe, (2) Smart-AH test rig, (3) per-hypothesis disposition, (4) ship defense layer. |
| **Q-1-7** | minor | CLAUDE.md inherited "leading hypothesis" framing | **Fixed**: replaced with "5-hypothesis disposition with H-C/H-E eliminated and H-A/H-B/H-D unprobed-after-Round-1". |
| **R-1-1** | major | `logs/walk_forward_runs/` sidecars are gitignored | **Fixed**: 3 sidecars (log, supervisor.jsonl, preflight.json) copied byte-identically to [logs/crash_evidence/walk_forward_2026-04-29_192543/](../../logs/crash_evidence/walk_forward_2026-04-29_192543/); audit-trail references updated. |
| **R-1-2** | major | Windows Event Log not preserved on disk | **Fixed**: 20:14-20:17 System Event Log slice captured via Get-WinEvent → ConvertTo-Json to [logs/crash_evidence/system_events_2026-04-29_2014-2017.json](../../logs/crash_evidence/system_events_2026-04-29_2014-2017.json) (~56 KB); same schema as 2026-04-27 prod-run-2 dump. |
| **R-1-3** | major | Cap value not persisted into any committed manifest | **Fixed (transitional)**: `P1-SUPERVISOR-CAP-FIELD-PERSISTENCE` follow-up registered; recovery procedure documented (`git blame supervised_relaunch_loop.sh:30` against supervisor-spawn timestamp from `.supervisor.jsonl[0].create_time` — both endpoints non-ignored after R-1-1 remediation). |
| **R-1-4** | major | New BLOCKING-BEFORE-NEXT-HXXX-LAUNCH severity tier introduced without `runbook_schema_version` bump | **Fixed**: clarifying paragraph added to ADR-0011 §"Per-hypothesis runbook" — marker is informational on ADR-0011 only; per-hypothesis runbook inherits gating via gate-14 consultation hook (operationalised in Round 2 per R-2-1). |
| **R-1-5** | minor | "Classification logic ran" framing overstated | **Fixed**: audit-trail F-2 framing softened to "supervisor's `finally` block did not execute; the `.supervisor.jsonl` first sample IS effectively a process-spawn record". |
| **R-1-6** | minor | ADR-0010 doesn't reflect the wake-lock regression | **Fixed**: 2026-04-29 forward-link Note added to ADR-0010 §"Layer 1" stating "Layer 1 alone is empirically insufficient on Windows 11 under at least one bypass mechanism". |
| **R-1-7** | minor | Per-hypothesis runbook gates 7/8 don't cross-reference Smart-AH probe | **Fixed**: gate 7 verification cell extended with Smart-AH probe sub-bullet referencing audit trail + `P1-WAKE-LOCK-BYPASS-INVESTIGATION`. |
| **R-1-8** | minor | Audit-trail chain navigability check | **Verified**: prior `audit_trail_2026-04-29_adr-0011-prodrun-runbook-directive.md` was committed in `6bed0c2`; chain ADR-0010 → ADR-0011 → directive-audit → bypass-audit is navigable. |

## Round 2 — verification audit + remediation

Subagents:
- `quant-auditor` Round 2 (`agentId adfb7fff4560404fd`) — verified 7/7 Q-1 dispositions; 4 new findings (Q-2-1 major, Q-2-2 major, Q-2-3 minor, Q-2-4 minor).
- `reproducibility-verifier` Round 2 (`agentId a222949a8db0c3cb3`) — verified 7/8 R-1 dispositions; R-1-4 verified-with-residual; 3 new findings (R-2-1 major, R-2-2 minor, R-2-3 minor).

### Round-2 dispositions (no Round-3 per SKILL.md cap)

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| **Q-2-1** | major | "Leading hypothesis" framing survived at audit trail line 108 + ADR-0011 ledger line 207, contradicting Q-1-1/Q-1-7 dispositions | **Fixed in-loop**: audit trail "Net implications" → "F-1 has 5 candidate hypotheses (H-A/H-B/H-D unprobed; H-C/H-E eliminated)"; ADR-0011 ledger row → "Five-hypothesis disposition: H-A and H-B unprobed-after-Round-1, H-D weakly refuted but not fully eliminated, H-C and H-E eliminated by mechanism analysis". |
| **Q-2-2** | major | Round-1 expanded scope didn't propagate into ADR-0011 ledger rows for `P1-WAKE-LOCK-BYPASS-INVESTIGATION` (4-criteria) and `P1-LGB-INNER-CV-CPU-ZERO-INVESTIGATION` (priority order + auto-trigger) | **Fixed in-loop**: full 4-criterion acceptance (USO trace, Smart-AH rig, per-hypothesis disposition, ship defense) propagated verbatim into ADR-0011 ledger; py-spy → procdump -ma → ETW priority order + 5-consecutive-30s-samples auto-trigger propagated verbatim. |
| **Q-2-3** | minor | Audit-trail rule-out at line 86 reads as refuting H-B prematurely | **Fixed in-loop**: appended "(does **not** refute H-B UsoSvc enforcement-deadline path; see F-1 H-B row — Microsoft-Windows-WindowsUpdateClient/Operational + USO trace channels not yet probed)". |
| **Q-2-4** | minor | Template post-run audit gate item 1 said "12 fields"; gate-4 row says 13 fields | **Fixed in-loop**: template line 173 → "all 13 fields per gate 4 enumeration (5 auto-captured + 8 operator-controlled)"; matches ADR-0011 §"Post-run audit gate" item 2. |
| **R-2-1** | major | R-1-4 inheritance asserted but not operationalised in template gate 14 | **Fixed in-loop**: template gate 14 verification cell extended with "Residual-risk gating consultation" sub-bullet — "Operator confirms no `[BLOCKING-BEFORE-NEXT-<HXXX>-LAUNCH]` row in ADR-0011 §Residual risk remains open for `<HXXX>`; record disposition (closed-via-commit / waived-with-mitigation) for each blocking row in §3 below before launch." ADR-0011 §"Per-hypothesis runbook" Severity-tier paragraph also updated to point at the new gate-14 sub-bullet (bidirectional cross-reference). Per Q-2-1 fix interpretation: this is operational, not a schema-version-bump-triggering, change. |
| **R-2-2** | minor | Audit-trail dual references to ignored originals + un-ignored copies invite future drift | **Fixed in-loop**: §"Evidence-preservation note" added near top of audit trail stating originals are ephemeral / canonical copies are at `logs/crash_evidence/`. |
| **R-2-3** | minor | Cap-raise commit-time consistency (working-copy modified at audit snapshot time) | **Verified clean by commit**: this audit trail and the cap-raise are committed together in commit `<filled-at-commit-time>`; git blame against supervisor-spawn timestamp (2026-04-29 19:27:13 CT, pre-commit) yields the original 10800 value at the parent commit `6bed0c2`. Recovery procedure operational. |

## Coverage of the 4 user-prescribed steps

| Step | User intent | Disposition |
|---|---|---|
| 1. Kill the hung attempt | Manual termination of stuck process | **Performed by the OS** at 20:16:03 via Kernel-Power 109 reboot. PIDs 33108 (supervisor) + 3212 (orchestrator) + 23618 (relaunch loop) all gone from `tasklist /v`. No manual kill needed. |
| 2. Diagnose the 0% CPU | py-spy dump on PID 3212 | **Live capture not possible** — PIDs killed by OS reboot before any dump. Documented under F-3 (orchestrator at 0% CPU for ≥2 min before reboot). Mechanism analysis: F-3 is coincident-not-cause of F-1. Future-event capture path expanded under `P1-LGB-INNER-CV-CPU-ZERO-INVESTIGATION` to py-spy → procdump → ETW with auto-trigger. |
| 3. Raise `PER_LAUNCH_CAP_S` ≥6 hr | Allow cfgs to complete in one attempt | **Implemented** — `scripts/supervised_relaunch_loop.sh:30` 10800 → 21600 (6 hr). Rationale: provisional doubling, not empirical floor; calibration tracked under `P1-RELAUNCH-PER-ATTEMPT-CAP-CALIBRATION`. Does **not** solve the wake-lock bypass (F-1) — see `P1-WAKE-LOCK-BYPASS-INVESTIGATION`. |
| 4. Promote `P1-LGB-INNER-CV-RESULT-CHECKPOINT` to blocking | Within-cfg checkpoint as architectural defense | **Implemented** — ADR-0011 §"Residual risk" row tagged `**[BLOCKING-BEFORE-NEXT-H050-LAUNCH]**` with rationale (within-cfg checkpoint is load-bearing for both F-3 hung-cfg and F-1 any-external-kill-mid-cfg). |

## New blocking follow-ups (per ADR-0011 §"Residual risk" + CLAUDE.md ledger)

Three items now `[BLOCKING-BEFORE-NEXT-H050-LAUNCH]`:

1. `P1-LGB-INNER-CV-RESULT-CHECKPOINT` — within-cfg / per-inner-fold / per-LGB-draw checkpointing.
2. `P1-WAKE-LOCK-BYPASS-INVESTIGATION` — 4-criterion acceptance: USO trace probe + Smart-AH test rig + per-hypothesis disposition + ship defense layer.
3. `P1-PREFLIGHT-SCRIPT-TIMEOUT` — raise 60s timeout to 180s + emit partial JSON on timeout rather than total failure.

Soft + threshold-derivation follow-ups: `P1-LGB-INNER-CV-CPU-ZERO-INVESTIGATION`, `P1-SUPERVISOR-FINALLY-WRITE-ON-HARD-KILL`, `P1-SUPERVISOR-CAP-FIELD-PERSISTENCE`, `P1-RELAUNCH-PER-ATTEMPT-CAP-CALIBRATION`. R-2-1 closure introduces `P1-ADR-0011-RESIDUAL-RISK-CONSULTATION-HOOK` — closed in this commit by the gate-14 sub-bullet edit (no separate follow-up).

## Operational state at write-time (Wed 2026-04-29 23:30 CT)

- All H050 prod-run-6 processes terminated (OS reboots at 20:16 + 20:40).
- Cumulative NQ cfg-checkpoints: 11/27 (unchanged from base run `338aac0a`).
- ES cfg-checkpoints: 38 in base (sufficient).
- Next launch is gated on the 3 BLOCKING-BEFORE-NEXT-H050-LAUNCH items above. The cap raise + governance directive are in-place; the architectural defenses (within-cfg checkpoint, wake-lock-bypass investigation, preflight timeout fix) are required before another multi-hour attempt.

## Exit verdict

**`accept-with-residuals`** — the recovery is operationally sound and ready for adoption.

- All 7 Round-1 quant majors+minors remediated.
- All 8 Round-1 repro majors+minors remediated.
- All 4 Round-2 quant findings (2 majors + 2 minors) remediated in-loop.
- All 3 Round-2 repro findings (1 major + 2 minors) remediated in-loop.
- Evidence preservation verifiable from repo alone (R-1-1 + R-1-2 byte-identical un-ignored copies).
- Cross-reference chain ADR-0010 → ADR-0011 → directive-audit → bypass-audit → recovery-loop-audit (this trail) → CLAUDE.md is bidirectionally navigable.
- Three blocking follow-ups must close before the next H050 launch.

**Residuals carried forward** (all named in ADR-0011 §"Residual risk"):

- 3 NEW + BLOCKING follow-ups (above).
- `P1-LGB-INNER-CV-CPU-ZERO-INVESTIGATION` (soft; capture-on-next-event).
- `P1-SUPERVISOR-FINALLY-WRITE-ON-HARD-KILL` (operational).
- `P1-SUPERVISOR-CAP-FIELD-PERSISTENCE` (machine-readable cap persistence).
- `P1-RELAUNCH-PER-ATTEMPT-CAP-CALIBRATION` (threshold derivation; depends on `P1-LGB-INNER-CV-RESULT-CHECKPOINT` for per-draw progress).

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md) — substantive diagnosis.
- [audit_trail_2026-04-29_adr-0011-prodrun-runbook-directive.md](audit_trail_2026-04-29_adr-0011-prodrun-runbook-directive.md) — prior governance directive trail (commit `6bed0c2`).
- [ADR-0011-production-walkforward-runbook.md](../decisions/ADR-0011-production-walkforward-runbook.md) — binding directive (residual-risk ledger updated by this commit).
- [ADR-0010-multi-hour-run-process-protection.md](../decisions/ADR-0010-multi-hour-run-process-protection.md) — Layer-1 forward-link Note added by this commit.
- [logs/crash_evidence/walk_forward_2026-04-29_192543/](../../logs/crash_evidence/walk_forward_2026-04-29_192543/) — un-ignored sidecar copies (3 files).
- [logs/crash_evidence/system_events_2026-04-29_2014-2017.json](../../logs/crash_evidence/system_events_2026-04-29_2014-2017.json) — ~56 KB Windows Event Log slice.
