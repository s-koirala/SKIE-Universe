---
title: ADR-0011 production-walkforward-runbook directive — audit-remediate-loop trail
date: 2026-04-29
artifact: docs/decisions/ADR-0011-production-walkforward-runbook.md + docs/research_notes/memo_h050-prodrun-retrospective_2026-04-29.md + research/_templates/production_run_runbook.md
followup_id: P1-ADR-0011-PRODUCTION-WALKFORWARD-RUNBOOK
exit_state: round-2 accept-with-residuals (SKILL.md cap reached)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
operational_constraint: H050 prod-run-6 (relaunch loop PID 23618) running concurrently; this audit-remediate-loop operates on commits + audit trails + memos with no live-state dependency
---

## Scope

A retrospective + governance audit-remediate-loop on the H050 production-walkforward arc 2026-04-26 → 2026-04-29 (5 prod-run failures, ~34 hours of compute, zero aggregate disposition artifacts). Output: a binding directive (ADR-0011) + per-hypothesis runbook template + retrospective memo + follow-up ledger update, intended to make the failure pattern non-repeatable for H051, H052a, H052b.

Subagents (proper-isolated, main-thread-spawned):

- `quant-auditor` (R1 + R2): Round-1 11 findings, Round-2 4 new findings.
- `reproducibility-verifier` (R1 + R2): Round-1 10 findings, Round-2 4 new findings.

This trail is operations-focused (governance), not method-focused. No new statistical method is introduced; literature-check was therefore not invoked.

## Round 1 — produce + parallel quant + repro audit

### Produced (Round 1)

1. [memo_h050-prodrun-retrospective_2026-04-29.md](../research_notes/memo_h050-prodrun-retrospective_2026-04-29.md) — five-failure retrospective, categorised predictable-by-preflight (Class A) vs structural (Class B).
2. [ADR-0011-production-walkforward-runbook.md](../decisions/ADR-0011-production-walkforward-runbook.md) — binding 14-item preflight checklist + execution shape + post-run audit gate.
3. [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md) — instantiable per-hypothesis runbook.

### Round-1 dispositions

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| **Q-1-1** | major | 36-hr cap text doesn't match `supervised_relaunch_loop.sh:30` PER_LAUNCH_CAP_S=10800 (3 hr) | **Fixed**: ADR §"Execution shape" now has explicit cap-and-attempts hierarchy table citing exact line numbers. |
| **Q-1-2** | major | `--max-attempts` default 5 vs script's 10 | **Fixed**: aligned to 10; `P1-RELAUNCH-MAX-ATTEMPTS-DERIVATION` registered. |
| **Q-1-3** | major | 22-hr `expected_runtime_hours` is H050-hardcoded; would mis-fire on H051+ | **Fixed**: gate 13 now requires explicit `--hypothesis <HXXX> --config config/hypotheses/<HXXX>.yaml`; H050-default drop tracked under `P1-SUPERVISED-RELAUNCH-LOOP-HXXX-DEFAULTS-DROP` + `P1-SUPERVISED-RUN-EXPECTED-RUNTIME-HYPOTHESIS-BOUND`. |
| **Q-1-4** | major | Gate 1 only checks `full ∈ covariance_type`; misses `spherical = diag = full` redundancy at d=1 | **Fixed**: reformulated to `len(set(cfg.hmm.covariance_type) - {"tied"}) >= 2 at d=1`. |
| **Q-1-5** | major | Run-3 categorisation as Class A is contestable (bottleneck only manifests at production-T) | **Fixed**: relaxed Class A definition (config-time check OR microbench artifact); new gate 2b (microbench-readiness, non-waivable) added. |
| **Q-1-6** | major | Gates 1, 2, 9, 10 are aspirational; implementation does not exist | **Fixed**: marked **spec'd, not shipped** with named follow-ups (`P1-ADR-0011-GATE-{1-DEDUP-DETECT, 2-COST-PROJECTOR, 2B-MICROBENCH-CATALOGUE, 3-ENVELOPE-CHECK, 8-POSTLAUNCH-VERIFY, 9-SCHTASKS, 10-DISK-PRECHECK}`). |
| **R-1-1** | major | Gate 4 enumerates 4 of 12 ReproLog fields; missing model_hash, config_resolved_sha256, env_id | **Fixed**: explicit 8-field operator-controlled enumeration; 5 auto-captured fields disclosed. |
| **R-1-2** | major | Substrate-checksum-survival check unspecified | **Fixed**: post-run audit gate item 2 now names `_load_output_sha256` + [tests/unit/test_orchestrator_dataset_checksums.py](../../tests/unit/test_orchestrator_dataset_checksums.py); supervisor sidecar correspondence sub-bullet added. |
| **R-1-3** | major | Schema-versioning of per-hypothesis runbook implicit | **Fixed**: template frontmatter has `runbook_schema_version: production_run_runbook_v1` + `adr_0011_revision`; ADR §"Per-hypothesis runbook" subsection added. |
| **R-1-4** | major | Cache-on/cache-off byte-identity unactionable ("where applicable") | **Fixed**: cite [tests/unit/test_orchestrator_hmm_cache.py](../../tests/unit/test_orchestrator_hmm_cache.py) + [tests/unit/test_hmm_fit_cache.py](../../tests/unit/test_hmm_fit_cache.py) F-1-4 contract; per-cfg checkpoint byte-identity excluded with rationale. |
| **R-1-5** | major | Model-hash chain composition unspecified | **Fixed**: ADR specifies SHA256 of canonical concatenation of HMM sidecar + walk-forward ledger + warm-cold diagnostic; `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` promoted to residual-risk table. |
| **R-1-6** | major | 2026-04-27 runbook supersession undeclared | **Fixed**: 2026-04-27 runbook frontmatter `status: superseded` + admonition; ADR-0011 frontmatter `supersedes:` lists it. |
| Q-1-7 | minor | Wall-clock arithmetic off by ~3 hr | **Fixed**: ~28 → 30.4 hr Class A; ~31 → 34.4 hr cumulative; ~112 → ~120 hr cross-hypothesis projection. |
| Q-1-8 | minor | 80% disk + 5/10-attempt cap empirical-justification gaps | **Fixed**: `P1-ADR-0011-DISK-CEILING-EMPIRICAL`, `P1-RELAUNCH-MAX-ATTEMPTS-DERIVATION`, `P1-ADR-0011-AH-MARGIN-EMPIRICAL` registered. |
| Q-1-9 | minor | 36-hr cap citation should be `supervised_run.py:53` not ADR-0010 | **Fixed**: cap-and-attempts table cites exact line. |
| Q-1-10 | minor | Gate 8 phrasing inversion ("Run-2 root cause" was the FIX, not cause) | **Fixed**: "no wake-lock registered → OS classified host as Active → Windows Update issued Kernel-Power Event 109 reboot". |
| Q-1-11 | minor | Asymmetric waivability for gates 7 vs 8 | **Fixed**: gate 7 promoted to non-waivable; rationale at ADR §85 (compensating control: documented Windows-Update pause for run window). |
| R-1-7 | minor | Waiver auditability — no programmatic binding | **Fixed**: gate 14 requires supervisor capture of `runbook_commit_hash` + `runbook_file_sha256` into `.preflight.json`; `P1-SUPERVISOR-RUNBOOK-COMMIT-CAPTURE` registered. |
| R-1-8 | minor | Audit-trail filename pattern collides on re-disposition | **Fixed**: `audit_trail_<YYYY-MM-DD>_<HXXX>-disposition-<run_id_short>.md` (8-hex). |
| R-1-9 | minor | Schema string constants not pinned | **Fixed**: `"hmm_fit_cache_v3_pickle5_numba"` + `"cfg_checkpoint_v1_pickle5"` pinned at gates 11/12. |
| R-1-10 | minor | Provenance-drift convention not documented in ADR | **Fixed**: new §"Provenance drift handling" subsection (WARN-but-load + hard-error semantics, with reference impls). |

## Round 2 — verification audit + remediation

Subagents:
- `quant-auditor` Round 2 (`agentId a140cbe960a0dc0b6`) — verified all 10 Round-1 quant findings; 4 new findings.
- `reproducibility-verifier` Round 2 (`agentId a20eddb440fda8f9b`) — verified 8/10 Round-1 repro findings; R-1-1 rejected (count error); R-1-3 verified-with-residual; 4 new findings.

### Round-2 dispositions

| ID | Severity | Issue | Round-2 disposition (no Round-3 per SKILL.md cap) |
|---|---|---|---|
| **Q-2-1** | minor | Memo §Recommendations line still said "14-item gate" after gate 2b insertion | **Fixed in-loop**: edited to "15-item gate (14 originally proposed + 1 microbench-readiness gate added in the Round-1 audit-remediate-loop)". |
| **Q-2-2** | major | Template §"Failure-mode → action matrix" permitted `--allow-preflight-warn` waiver path on AH coverage, contradicting ADR's non-waivable gate 7 | **Fixed in-loop**: edited template line 148 to drop the `--allow-preflight-warn` option; replaced with documented Windows-Update pause as the only compensating control. |
| **Q-2-3** | minor | Template Status column placeholder `<pass / waived>` used for non-waivable gates | **Fixed in-loop**: 9 non-waivable rows changed to `<pass>`; non-waivable status marked inline in gate-name column. |
| **Q-2-4** | minor | Missing dependency note: `P1-ADR-0011-GATE-2-COST-PROJECTOR` requires `P1-ADR-0011-GATE-2B-MICROBENCH-CATALOGUE` | **Fixed in-loop**: dependency note added to residual-risk table. |
| **R-2-1** | major | "12 fields" claim mismatched the 13-field ReproLog dataclass; gate 4 enumeration listed only 8 of 13 | **Fixed in-loop**: prose updated to "13 fields"; enumeration restructured as "5 auto-captured (`run_id`, `phase`, `hypothesis_id`, `timestamp_utc`, `host`) + 8 operator-controlled (gate-4-mandatory)"; ADR + template + post-run audit gate all updated. |
| **R-2-2** | minor | Chicken-and-egg unresolved for `adr_0011_revision` placeholder under co-commit | **Fixed in-loop**: ADR §"Per-hypothesis runbook" extended with "Co-commit resolution" paragraph: TODO marker → fill in follow-up commit; runbook-validator detects. |
| **R-2-3** | minor | ADR-0010 §Layer 2 still references 2026-04-27 runbook without ADR-0011 cross-reference | **Fixed in-loop**: admonition note added to ADR-0010 §Layer 2 pointing to ADR-0011 + the new template. |
| **R-2-4** | minor | Gate 14 auditability is unshipped-supervisor-dependent | **Fixed in-loop**: transitional clause added to gate 14 (operator records commit hash manually until `P1-SUPERVISOR-RUNBOOK-COMMIT-CAPTURE` ships); explicitly marked load-bearing in residual-risk ledger. |

## Tier coverage matrix (post-remediation)

15-gate preflight checklist coverage of the 5 H050 prod-run failures:

| Failure | Gate(s) that catch it (post-remediation) |
|---|---|
| Run-1 — HMM d=1 cov-redundancy | Gate 1 (Tier 1; non-waivable) — generalised to all `set(cov_types) - {tied}` redundancies. |
| Run-2 — Windows Update auto-reboot | Gates 6 (pending-restart), 7 (AH coverage; non-waivable post-Round-1), 8 (wake-lock; non-waivable). |
| Run-3 — HMM EM Python-loop bottleneck | Gate 2b (microbench-readiness; non-waivable) — requires production-T-scale microbench artifact at toolkit-build-time + gate 2 (budget feasibility). |
| Run-4 — LGB heap fragmentation OOM | NOT CAUGHT at preflight (correctly Class B); bounded by gates 12 (per-cfg checkpoint) + 13 (supervised relaunch loop). |
| Run-5 — Windows-CRT structural fragmentation | Same Class-B bounding as Run-4. |

## Implementation status (post-remediation)

**Shipped gates (no follow-up):** 5, 6, 7, 8 (post-launch verify pending), 11, 12, 13 (defaults-drop pending). 7 of 15.

**Spec'd-not-shipped gates (named follow-ups in residual-risk ledger):** 1 (auto-detect), 2, 2b (catalogue), 3, 8 (post-launch), 9, 10, 13 (defaults-drop), 14 (supervisor capture). 9 follow-ups.

**Threshold-derivation follow-ups:** 3 (`P1-ADR-0011-AH-MARGIN-EMPIRICAL`, `P1-ADR-0011-DISK-CEILING-EMPIRICAL`, `P1-RELAUNCH-MAX-ATTEMPTS-DERIVATION`).

The directive is materially stronger than the no-directive baseline; the partly-aspirational gates carry tractable, named, ledger-tracked follow-ups.

## Operational safety

H050 prod-run-6 (relaunch loop PID 23618; child run_id `f306cf79b1194154b38414fa6d6a64de`) ran throughout this audit-remediate-loop. The currently-running orchestrator imported all modules into RAM at process start; on-disk edits to `docs/`, `research/_templates/`, and ADR-0010 did NOT affect the running session. Verified by tail of [logs/walk_forward_runs/h050_prod_run_2026-04-29T162429.log](../../logs/walk_forward_runs/h050_prod_run_2026-04-29T162429.log) showing PROGRESS markers continuing normally.

## Exit verdict

**`accept-with-residuals`** — the directive set is operationally sound and ready for adoption.

- All 12 Round-1 majors remediated; all 9 Round-1 minors that affect cross-hypothesis durability remediated.
- 2 new majors + 6 new minors from Round 2 all remediated in-loop.
- All numeric claims verified arithmetically: 15 gates (6 + 5 + 4); non-waivable list 10 items; 30.4 / 34.4 = 88.4% wall-clock; 30 hr × 0.9 = 27 hr usable budget.
- Schema constants byte-identical to source; references resolve to extant test files.
- Supersession metadata propagated through ADR-0010, ADR-0011, the 2026-04-27 runbook, and the retrospective.

**Residuals carried forward** (all named in ADR-0011 §"Residual risk" table):

- 9 spec-only follow-ups for the implementation track.
- 3 threshold-derivation follow-ups.
- `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` (multi-sidecar chain composability).
- `P1-SUPERVISOR-RUNBOOK-COMMIT-CAPTURE` (load-bearing for full gate-14 auditability; transitional operator-recorded value used until shipping).
- 6 pre-existing structural follow-ups (cfg subprocess isolation, per-symbol resume, per-fold checkpoint, etc.).

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [memo_h050-prodrun-retrospective_2026-04-29.md](../research_notes/memo_h050-prodrun-retrospective_2026-04-29.md) — empirical basis (5-failure retrospective).
- [ADR-0011-production-walkforward-runbook.md](../decisions/ADR-0011-production-walkforward-runbook.md) — binding directive.
- [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md) — per-hypothesis runbook template.
- [ADR-0010-multi-hour-run-process-protection.md](../decisions/ADR-0010-multi-hour-run-process-protection.md) — extended by ADR-0011 §Layer 2.
- [docs/research_notes/runbook_walk-forward-launch-prep_2026-04-27.md](../research_notes/runbook_walk-forward-launch-prep_2026-04-27.md) — superseded.
- Five canonical prod-run audit trails: [diagnosis-1](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md), [diagnosis-2](audit_trail_2026-04-27_h050-prod-run-2-windows-update-reboot.md), [numba-kernels](audit_trail_2026-04-28_hmm-em-numba-kernels.md), [lgb-heap-fragmentation](audit_trail_2026-04-28_lgb-heap-fragmentation.md), [cfg-checkpoint](audit_trail_2026-04-29_cfg-checkpoint.md).
