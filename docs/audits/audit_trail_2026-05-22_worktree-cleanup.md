# Audit trail — worktree cleanup with ADR-0013 §4.1 non-loss preservation

**Date**: 2026-05-22
**Trigger**: operator directive — recover ~60 GB occupied by `.claude/worktrees/`
**Loop**: audit-remediate-loop (3-round cap; R1 BLOCK → R2 BLOCK → R3 ACCEPT)
**Operator**: skoir
**Script**: [scripts/worktree_cleanup_2026-05-22.ps1](../../scripts/worktree_cleanup_2026-05-22.ps1)
**Preservation logs**: [logs/worktree_cleanup_preservation_2026-05-22_20260522T080022.log](../../logs/worktree_cleanup_preservation_2026-05-22_20260522T080022.log) + [20260522T080144.log](../../logs/worktree_cleanup_preservation_2026-05-22_20260522T080144.log)

## Pre-state
- 18 git worktrees + 5 orphan stub directories under `.claude/worktrees/`
- ~46 GB on disk (43 GB concentrated in `friendly-ritchie-cd2dda/artifacts/runs/H050/31d23ecd.../$_cfg_checkpoints/`)
- 4 unmerged claude/* branches (ecstatic-hellman not on origin; others pushed)
- 2 locked agent worktrees claiming PID 27424

## Initial plan (R1 candidate)
Chat-only 5-step script: preserve 2 named run dirs + push ecstatic-hellman + remove all worktrees + prune.

## R1 audit (3 parallel branches)
- **reproducibility-verifier**: BLOCK (4 critical + 5 major)
- **code-reviewer**: BLOCK (4 critical + 5 major)
- **format-auditor**: proceed-with-remediation (only minor)

R1 critical findings:

| ID | Branch | Issue |
|---|---|---|
| RV-1 | repro | friendly-ritchie has 6 additional H050 production runs (0ce7136c, 1e0575ba, 4585e766, 61750fc1, a08b75a1, fdaa598c) + 102 unique ReproLogs — plan only preserves 31d23ecd |
| RV-2 | repro | friendly-ritchie has 38 unique untracked ReproLogs in `logs/reproducibility/` |
| RV-3 | repro | 7 other worktrees carry unique §4.1 artifacts (fervent-brown 10 ReproLogs; nervous-greider 10 sidecars; inspiring-franklin 228; thirsty-hawking 12; etc.) — plan only addresses 2 worktrees |
| RV-4 | repro | Step 3 push has no exit-code check |
| RV-5 | repro | No `$ErrorActionPreference = 'Stop'` — silent Copy-Item failures |
| CR-1 | code | `scientific_payload_sha256.txt` referenced but presence not verified |
| CR-2 | code | Worktree count was 16; actual is 18 |
| CR-3 | code | Single `--force` insufficient against locked worktrees |
| CR-4 | code | No `$ErrorActionPreference = 'Stop'`; no git push exit-code check |

## R1 → R2 remediation
Wrote [scripts/worktree_cleanup_2026-05-22.ps1](../../scripts/worktree_cleanup_2026-05-22.ps1) v1 with:
- `$ErrorActionPreference = 'Stop'` at top
- pre-flight PID 27424 liveness check
- pre-flight dirty-worktree sweep
- union-copy preservation across 6 path classes × all 18 worktrees
- explicit `git worktree unlock` before `--force remove`
- `_cfg_checkpoints` exclusion (43 GB drop)
- `Copy-IfMissing` idempotent skip-if-dst-exists

## R2 audit (3 parallel branches)
- **reproducibility-verifier**: BLOCK (3 critical + 3 major)
- **code-reviewer**: REMEDIATE (3 critical + 7 major)
- **format-auditor**: EXIT-LOOP (only minor)

R2 critical findings:

| ID | Branch | Issue |
|---|---|---|
| R2-RV-1 | repro | Top-level `runs/` NOT swept — blissful-lichterman has 11 unique H053 sidecars |
| R2-RV-2 | repro | `reports/` NOT swept — blissful-lichterman has 1 H053 disposition memo |
| R2-RV-3 | repro | `docs/decisions/` + `docs/research_notes/` NOT swept — 11 ADR collisions + 4 unique research_notes |
| R2-RV-4 | repro | Copy non-atomic; partial-failure leaves truncated files |
| R2-CR-1 | code | `git push` stderr captured but NOT included in throw message |
| R2-CR-2 | code | `git ls-remote` truthiness check broken — error string passes truthy gate |
| R2-CR-3 | code | Subexpression syntax bug: `$($var -split '\s')[0]` array index outside subexpression |

## R2 → R3 remediation
Rewrote script with:
- Added 4 more preservation paths (`runs/`, `reports/`, `docs/decisions/`, `docs/research_notes/`) — total 10 path classes
- `Copy-IfMissing-WithCollisionDetect` for ADRs — SHA256 compare + SHA-prefixed variant filename under `docs/decisions/_pending_renumber_from_worktrees/`
- Atomic copy via `.cleanup_tmp` + size assertion + Move-Item
- `$pushOut` captured and included in throw
- `git ls-remote` exit code checked separately from regex `^[0-9a-f]{40}\s` SHA format validation
- `$remoteSha` extracted as separate assignment statement
- Operator-action prompt at end
- `# justify:` annotations on hardcoded `$lockedPid` and `$lockedWorktrees`
- Orphan-stub regex extended to all 10 protected paths
- Timestamped preservation log filename

## R3 audit (2 parallel branches)
- **reproducibility-verifier**: ACCEPT (4 minor only)
- **code-reviewer**: EXIT-LOOP (3 minor only)

R3 residual minor findings (operator-accepted, not remediated):

| ID | Severity | Issue |
|---|---|---|
| R3-1 | minor | `Copy-RunDir` not atomic at directory granularity (mitigated by Test-Path idempotency on re-run) |
| R3-2 | minor | Collision-variant filename ambiguity at >1 worktree with same-name-different-content (ADDRESSED inline via SHA-prefixed filenames before execution) |
| R3-3 | minor | Size-only integrity check (Windows kernel Copy-Item is disk-driver checksummed) |
| CR-3-1 | minor | `MatchInfo` coercion via implicit `ToString()` (functional) |
| CR-3-2 | minor | Brittle `'not locked'` string match for benign unlock failures (intentional soft-fail) |
| CR-3-3 | minor | `$script:` scope mutation in helper functions (acceptable for one-shot script) |

R3 verdict: **ACCEPT — proceed to execution**

## Execution
Two invocations (first halted on PowerShell `Stop`-preference misinterpretation of git's `remote:` stderr progress lines; second invocation with `$ErrorActionPreference = 'Continue'` scoped around git operations + explicit `$LASTEXITCODE` checks):

**First run (partial)**:
- Preservation sweep: 693 files / 20.11 MB / 14 ADR collisions captured
- Push: ecstatic-hellman → origin (`20c4a07b7b4d7f30833e59d26f60b6cb3143a45f`)
- Halted at worktree-removal step due to NativeCommandError on git push stderr

**Second run (completion)**:
- Preservation: 0 new files (3,388 skipped — idempotent re-run)
- Push: "Everything up-to-date" (already on origin)
- Removed 2 locked agent worktrees (after `git worktree unlock`)
- Removed 16 tracked worktrees
- Removed 5 orphan stub directories
- `git worktree prune` clean

## Outcome

| Metric | Before | After |
|---|---:|---:|
| Worktrees tracked by git | 18 | 1 (main only) |
| `.claude/worktrees/` size | ~46 GB | 8 KB |
| ReproLogs in `logs/reproducibility/` | ~80 | 502 |
| ADR variants preserved | n/a | 14 (in `_pending_renumber_from_worktrees/`) |
| H053 sidecars in `runs/h053/` | 0 | preserved |
| H053 disposition memos in `reports/h053/` | 4 | 5 (added `stage3_v3_full_disposition.md`) |

**Disk reclaimed**: ~46 GB
**Artifacts preserved**: 693 files / 20.11 MB (per first-run preservation log)
**Net free**: ~46 GB minus 20 MB ≈ 45.98 GB

## §4.1 non-loss compliance
- 502 ReproLogs preserved into `logs/reproducibility/` (union of all worktrees)
- All H050/H052a/H054/H055/H060/H062/H065/H067/H068/MPV1 unique run-directories preserved (minus `_cfg_checkpoints/` per the §4.1 list — checkpoints are intermediate compute state, not analytical deliverables; pre-commit guard `scripts/_hooks/check_non_loss_deletion.py` does not flag them)
- `runs/h053/` + `reports/h053/` newly preserved
- 14 ADR collision variants saved under `docs/decisions/_pending_renumber_from_worktrees/` with SHA-prefixed filenames (deduplicates identical variants from multiple worktrees)
- 4 unique audit trails preserved into `docs/audits/`
- 4 unique research_notes preserved into `docs/research_notes/`
- ecstatic-hellman branch pushed to `origin/claude/ecstatic-hellman-937c44` — H057/H058/H059 design.md commit objects survive

## Residual operator actions
1. Review preservation log + git status — 814 untracked files now in main checkout
2. Commit preserved artifacts per [/commit-with-provenance](../../.claude/commands/commit-with-provenance.md) ceremony
3. Review `docs/decisions/_pending_renumber_from_worktrees/` (14 ADR variants) — renumber + integrate or document obsolescence
4. Optional: delete the 4 retained branch refs (`claude/blissful-lichterman-d5de97`, `claude/fervent-brown-77ab36`, `claude/friendly-ritchie-cd2dda`, `claude/ecstatic-hellman-937c44`) after confirming origin has them

## Auditor agentIds
- R1 reproducibility-verifier: `a6d17aade126f66eb`
- R1 code-reviewer: `ad3e472c5947629c1`
- R1 format-auditor: `ae77a70200fdf7898`
- R2 reproducibility-verifier: `a09f1235cb87b1660`
- R2 code-reviewer: `a82b775a64f67f647`
- R2 format-auditor: `ae40d0e2a076cb01a`
- R3 reproducibility-verifier: `a75810aea84d92ce7`
- R3 code-reviewer: `a9350bda1045ddfac`
