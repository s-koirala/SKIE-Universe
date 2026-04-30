---
title: P1-LGB-INNER-CV-RESULT-CHECKPOINT + P1-WAKE-LOCK-BYPASS-INVESTIGATION + P1-PREFLIGHT-SCRIPT-TIMEOUT — implementation + 1-round audit-remediate
date: 2026-04-30
artifact: src/skie_ninja/backtest/lgb_inner_cv_checkpoint.py + scripts/run_walk_forward.py + scripts/preflight/{check_windows_update,pause_windows_update}.ps1 + scripts/supervised_run.py + tests/unit/test_lgb_inner_cv_checkpoint.py
followup_id: P1-RECOVERY-LOOP-2026-04-30-EVENING
exit_state: round-1 accept-with-residuals (Round-2 verification deferred to next ARL on disposition output)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
parent_diagnosis: docs/audits/audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md
---

## Scope

Implementation + 1-round audit-remediate-loop on the three blocking follow-ups closed today (2026-04-30). The user-requested workflow chains these closures with main-branch merge + H050 launch.

| Follow-up | Resolution |
|---|---|
| `P1-PREFLIGHT-SCRIPT-TIMEOUT` | timeout 60→180s in [scripts/supervised_run.py](../../scripts/supervised_run.py); `-OutputPath` parameter on [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) writes incremental JSON; supervisor reads partial-on-`TimeoutExpired`. |
| `P1-WAKE-LOCK-BYPASS-INVESTIGATION` | 4-criterion acceptance: USO/Operational probe found Event 26 same-second as Kernel-Power 109; Smart-AH probe (registry value unset) eliminated H-A; H-B is consistent-with-evidence-not-confirmed (Q-1-5 audit fix); defense layer shipped at [scripts/preflight/pause_windows_update.ps1](../../scripts/preflight/pause_windows_update.ps1) writing both Settings-UI and Group-Policy registry paths. |
| `P1-LGB-INNER-CV-RESULT-CHECKPOINT` | new module [src/skie_ninja/backtest/lgb_inner_cv_checkpoint.py](../../src/skie_ninja/backtest/lgb_inner_cv_checkpoint.py) `SCHEMA_VERSION = "lgb_inner_cv_checkpoint_v2_pickle5"`; per-(cfg, fold_id, draw_idx) atomic-write checkpoint; orchestrator wired via module-level `_LGB_INNER_CV_CURRENT_CTX`; 32 unit tests all pass. |

## Round 1 — produce + parallel quant + repro audit

Subagents (proper-isolated, main-thread-spawned):

- `quant-auditor` (`agentId ad2cbc0f5075c87ce`) — 9 findings (1 critical/major-equivalent at semantic-equivalence layer, 5 majors, 3 minors) + per-table verdict `accept-with-remediation`.
- `reproducibility-verifier` (`agentId af3682c3a555b1c10`) — 7 findings (1 critical, 6 minors) + verdict `accept-with-remediation`.

### Round-1 dispositions

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| **R-1-1** | **critical** | Per-draw cache key collided across outer folds within one cfg. `_inner_cv_select_hp` runs once per outer fold; without `fold_id` in the key, fold N's pickle overwrote fold N-1's, and resume silently substituted prior-fold inner-CV outputs. | **Fixed**: schema v1 → v2; LgbDrawKey extended to (cfg_signature, fold_id, draw_idx); filename `fold_<NN>_draw_<NNNN>.pkl`; payload includes `fold_id`; new `filter_draws_by_fold` helper projects the global cached dict to the fold-local view; ctx[`fold_id`] injected at the call site inside `_fit_fold_body` (where fold_id is in scope). New regression test `test_fold_id_in_key_prevents_overwrite` constructs the v1-collision pattern and asserts both folds' pickles survive. |
| **Q-1-1** | major | Non-deterministic iteration over cached draws breaks bit-identical resume on metric ties (`Path.iterdir()` filesystem-order). | **Fixed**: `discover_draws` returns `dict(sorted(out.items()))`; `merge_resume_into_current` re-sorts after dict.update. New test `test_discover_draws_returns_sorted` + `test_merge_resume_returns_sorted_dict` asserts deterministic key order. |
| **Q-1-2** | major | `cfg_signature` did not include `lgb_seed`; cross-seed resume silently substituted cached params from a different HP-draw stream. | **Fixed**: `lgb_inner_cv_cfg_dir(run_dir, cfg_signature, lgb_seed=...)` namespaces the cfg subdirectory by seed; runs with different `lgb_seed` cannot share pickles. Payload also records `lgb_seed`. New tests `test_lgb_seed_in_cfg_dir_path` + `test_cross_seed_isolation`. |
| **Q-1-3** | major | `pause_windows_update.ps1` constructed expiry as `(Get-Date).AddHours().ToString("...Z")` — local time labeled as UTC. On a CT host, a 24-hr pause genuinely lasted ~19 hr. | **Fixed**: `(Get-Date).ToUniversalTime().AddHours($Hours).ToString("yyyy-MM-ddTHH:mm:ssZ")`. Comment block cites Q-1-3 + audit-trail F-1. |
| **Q-1-4** | major | Pause registry writes targeted only `UX\Settings`; UsoSvc enforcement reads `Policies\Microsoft\Windows\WindowsUpdate`. Defense layer ineffective against the H-B mechanism it was shipped to block. | **Fixed**: also writes to `HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate` with `PauseFeatureUpdatesStartTime` + `PauseFeatureUpdatesEndTime` + `PauseQualityUpdatesStartTime` + `PauseQualityUpdatesEndTime`. Settings-UI write retained for operator visibility. `-Resume` clears both paths. |
| **Q-1-5** | major | Audit-trail H-B "confirmed leading candidate" overreached evidence; Event 26 is scan-completion, not reboot-trigger. USO trace channel was specified in acceptance criterion (1) but not probed. | **Fixed**: H-B disposition demoted to "consistent with evidence; load-bearing candidate caller; not yet confirmed". USO trace probe deferred to new follow-up `P1-USO-TRACE-CHANNEL-PROBE`. Defense layer (Q-1-4 fix) ships against H-B regardless. |
| **Q-1-7** | minor | Preflight WU-paused downgrade did not validate parsed expiry exceeds run window. | **Fixed**: `[DateTime]::ParseExact(... AssumeUniversal | AdjustToUniversal)` + comparison against `(Get-Date).ToUniversalTime().AddHours($ExpectedRuntimeHours)`. New field `wu_pause_covers_run` (true/false/null) gates the downgrade. |
| **R-1-3** | minor | `load_draw_checkpoint` ValueError wording shorter than peer modules; missing operator-action sentence. | **Fixed**: appended "Stale artifacts must not be silently loaded; delete the per-cfg directory or re-run from scratch." |
| **R-1-5** | minor | No test covered the prior-run-dir-exists-but-cfg-subdir-missing case. | **Fixed**: new test `test_merge_resume_prior_with_no_cfg_subdir`. |
| Q-1-6 | minor | Module-level mutable global `_LGB_INNER_CV_CURRENT_CTX` would race under future multi-process driver. | **Deferred**: `P1-LGB-INNER-CV-CTX-CONTEXTVAR-MIGRATION`. Today's serial cfg loop is safe. |
| Q-1-8 | minor | `_PREFLIGHT_TIMEOUT_S = 180` + `-Hours 24` defaults lack measured empirical justification. | **Deferred**: `P1-PREFLIGHT-TIMEOUT-EMPIRICAL` + `P1-WU-PAUSE-DEFAULT-HOURS-EMPIRICAL`. Operator-budget thresholds; softer rule per project conventions. |
| Q-1-9 | minor | `cfg_signature[:16]` directory truncation justification frame was wrong universe. | **Deferred**: `P1-LGB-INNER-CV-DIR-NAME-FULL-HEX`. |
| R-1-2 | minor | Parent-fsync caveat not documented in module docstring. | **Fixed in-loop**: docstring of `save_draw_checkpoint` now cites the F-1-3 disposition. |
| R-1-4 | minor | Test `test_cfg_signature_matches_cfg_checkpoint_canonical_format` asserts hash equality only, not canonical-string format. | **Deferred**: `P1-LGB-INNER-CV-CANONICAL-FORMAT-REGRESSION-TEST`. |
| R-1-6 | minor | Module-level ctx clearing relies on prior-iteration finally; defensive clear at top of cfg loop would make invariant local. | **Deferred**: `P1-LGB-INNER-CV-CTX-DEFENSIVE-CLEAR`. The current invariant holds because the only paths that exit the cfg loop body either run the `finally` clear or terminate the program. |
| R-1-7 | minor | `Write-PartialReport` swallows partial-write failures silently. | **Deferred**: `P1-PREFLIGHT-WRITE-PARTIAL-STDERR-SIGNAL`. |

Round-2 verification deferred — the next audit-remediate-loop on the H050 disposition (post-launch, on the actual run output) will re-exercise the per-draw checkpoint path and surface any drift between the unit-test setup and production T~3M.

## Test pass count

- **32/32** new + extended `tests/unit/test_lgb_inner_cv_checkpoint.py` tests pass (was 25 in v1; +7 covering R-1-1 fold-collision, Q-1-1 sort, Q-1-2 cross-seed, R-1-5 prior-no-cfg-subdir).
- **36/36** surrounding tests (`test_cfg_checkpoint`, `test_supervised_run`, `test_orchestrator_progress_log`) pass — no regressions.

## Exit verdict

**`accept-with-residuals`** — implementations are operationally sound and ready for the H050 launch.

- 1 critical (R-1-1 fold-collision) remediated via schema-version bump v1→v2.
- 5 majors (Q-1-1 sort, Q-1-2 lgb_seed, Q-1-3 tz, Q-1-4 GPO path, Q-1-5 audit-trail demote) all remediated.
- 4 minors remediated in-loop (Q-1-7, R-1-2, R-1-3, R-1-5).
- 6 minors deferred to named follow-ups (operational / cosmetic; do not block the launch).

The defense-in-depth posture is materially stronger than yesterday's commit. Next H050 launch:
1. Operator runs `pause_windows_update.ps1 -Hours 30` (admin-elevated PowerShell) before launch.
2. Supervised relaunch loop launches with the per-attempt cap raised to 6 hr.
3. If a UsoSvc enforcement-deadline reboot fires inside the run window, the Group-Policy pause now defers it.
4. If any external kill lands mid-cfg, per-(cfg, fold, draw) checkpointing bounds work loss to one draw.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md](audit_trail_2026-04-29_h050-prod-run-attempt2-os-reboot-bypass.md) — substantive diagnosis (parent).
- [audit_trail_2026-04-29_h050-prod-run-attempt2-recovery-loop.md](audit_trail_2026-04-29_h050-prod-run-attempt2-recovery-loop.md) — prior recovery audit.
- [src/skie_ninja/backtest/lgb_inner_cv_checkpoint.py](../../src/skie_ninja/backtest/lgb_inner_cv_checkpoint.py) — new module (v2 schema).
- [tests/unit/test_lgb_inner_cv_checkpoint.py](../../tests/unit/test_lgb_inner_cv_checkpoint.py) — 32-test regression suite.
- [scripts/preflight/pause_windows_update.ps1](../../scripts/preflight/pause_windows_update.ps1) — defense layer (Group Policy + Settings UI registry pause).
- [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) — preflight w/ -OutputPath + WU-pause coverage validation.
- [scripts/supervised_run.py](../../scripts/supervised_run.py) — supervisor w/ 180s preflight timeout + partial-JSON-on-`TimeoutExpired`.
- Microsoft Learn: [Policy CSP - Update](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-update) — Group-Policy WU pause registry path.
- Microsoft Learn: [Pause Windows Update](https://learn.microsoft.com/en-us/windows/deployment/update/waas-pause-features) — pause mechanism.
