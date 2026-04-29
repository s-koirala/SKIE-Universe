---
name: Branch-merge decision — claude/laughing-shamir-059944 → claude/ecstatic-hellman-937c44
description: Empirical research memo for integration of sibling branch and adjudication of H053 hypothesis-ID collision
type: project
created: 2026-04-27
---

# Branch-merge decision — sibling integration and H053 ID collision

## 1. Question

Three integration options for the sibling branch `origin/claude/laughing-shamir-059944` (HEAD `318c502`) into the current branch `claude/ecstatic-hellman-937c44` (HEAD `2f24b0a`, working tree dirty with the chart-reader cohort):

- (a) Install only the sibling H053 hypothesis package files.
- (b) Full git merge of the sibling branch.
- (c) Cherry-pick selected commits.

Plus a hard hypothesis-ID collision: both branches assert `hypothesis_id: H053` with `status: designed`, on entirely different research designs.

## 2. Method

Read-only git inspection from the live worktree. Commands run (no merge / cherry-pick / stash executed):

- `git status --short`
- `git rev-parse HEAD`, `git merge-base HEAD origin/claude/laughing-shamir-059944`
- `git rev-list --count` in both directions across HEAD ↔ sibling and main ↔ each
- `git log --oneline 2f24b0a..origin/claude/laughing-shamir-059944` (the four sibling-only commits)
- `git diff --stat HEAD..origin/claude/laughing-shamir-059944`
- `git diff --stat main..origin/claude/laughing-shamir-059944` and `main..HEAD`
- `git merge-tree HEAD origin/claude/laughing-shamir-059944` (predicts a clean tree SHA `3ee891c`)
- `git diff HEAD -- CLAUDE.md README.md plan/hypothesis_backlog.md` (uncommitted edits)
- `git show origin/claude/laughing-shamir-059944:<path>` for sibling versions of: `research/01_hypothesis_register/H053/design.md`, `data_requirements_H053_2026-04-28.md`, `lit_review_H053_2026-04-28.md`, `plan/h053_buildout_2026-04-28.md`, `CLAUDE.md`
- `git ls-tree -r origin/claude/laughing-shamir-059944 -- research/01_hypothesis_register/H053/`
- `git ls-tree -r HEAD -- research/01_hypothesis_register/H050/ H051/ H052a/ H052b/`
- `git show --stat <sha>` for each of the four sibling-only commits
- Filesystem listing of `research/01_hypothesis_register/H053/`, `H054/`, `H055/`, `H056/` working-tree contents

Files read directly:
- [CLAUDE.md](../../CLAUDE.md) (working-tree)
- [README.md](../../README.md) (working-tree, head only)
- [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md) (working-tree)
- [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) (frozen-status precedent)
- [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md) (current chart-reader)

## 3. Empirical findings — A. Merge-conflict surface

**Critical structural finding.** The current branch HEAD `2f24b0a` IS the merge-base with the sibling branch. Sibling is exactly four commits ahead of HEAD; HEAD is zero commits ahead of sibling:

```
git rev-list --count HEAD..origin/claude/laughing-shamir-059944  →  4
git rev-list --count origin/claude/laughing-shamir-059944..HEAD  →  0
```

The four sibling-only commits are H053-package-only:

```
89c5396 docs(h053): add pre-registration literature review
193120f docs(h053): add pre-registered design + data_requirements companion
ec7c840 chore(audits): record h053 design audit-remediate-loop trail
318c502 plan(h053): add 6-cycle staged buildout (Cycles 7-12)
```

`git diff --stat HEAD..origin/claude/laughing-shamir-059944` adds exactly five files, zero modifications, zero deletions:

```
docs/audits/audit_trail_2026-04-28_h053-design.md       | 119 +++++
plan/h053_buildout_2026-04-28.md                        |  64 +++
research/01_hypothesis_register/H053/data_requirements_H053_2026-04-28.md | 101 +++++
research/01_hypothesis_register/H053/design.md          | 481 +++++++++++++
research/01_hypothesis_register/H053/lit_review_H053_2026-04-28.md        | 149 +++++
 5 files changed, 914 insertions(+)
```

`git merge-tree HEAD origin/claude/laughing-shamir-059944` returns a clean tree SHA `3ee891c3076712d8053aa9d3c1ed0afe66ee0963` with **no conflict markers**. Git considers the COMMITTED state of the two branches mergeable trivially as a fast-forward (sibling is strictly ahead).

The actual collision surface is between sibling's tracked H053 package and current's UNTRACKED working-tree files:

| File | Hunks | Severity | Resolution sketch |
|---|---|---|---|
| [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md) | full file (untracked vs sibling-tracked, different content) | doctrine-clash | Not text-mergeable. Different hypotheses. Requires ID-collision adjudication, not text merge. |
| [research/01_hypothesis_register/H053/README.md](../../research/01_hypothesis_register/H053/README.md) | working-tree-only, sibling has none | trivial | Renames with H053 (current) keeps file as-is or moves to successor-ID directory under chosen renumber path. |
| [research/01_hypothesis_register/H053/data_requirements.md](../../research/01_hypothesis_register/H053/data_requirements.md) | working-tree-only at this filename; sibling has `data_requirements_H053_2026-04-28.md` | structural (filename convention divergence) | Different filenames so no overwrite. Sibling's date-suffixed name violates the established `data_requirements.md` convention (see §5). |
| (sibling) `lit_review_H053_2026-04-28.md` | sibling-only | trivial | Lands cleanly under whichever ID it ends up at; convention drift on filename (no precedent for `lit_review_*.md` in [H050](../../research/01_hypothesis_register/H050/), [H051](../../research/01_hypothesis_register/H051/), [H052a](../../research/01_hypothesis_register/H052a/), or [H052b](../../research/01_hypothesis_register/H052b/)). |
| [CLAUDE.md](../../CLAUDE.md) | working-tree edits only; sibling unchanged from HEAD-committed | trivial | `git diff HEAD origin/claude/laughing-shamir-059944 -- CLAUDE.md` returns empty. Working-tree adds Tier 2c paragraph; sibling does not touch it. No conflict. |
| [README.md](../../README.md) | working-tree edits only; sibling unchanged | trivial | Same as above. |
| [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md) | working-tree edits only; sibling unchanged | trivial | Same as above. The Tier 2c block in the working tree carries `H053` for the chart-reader CNN; under sibling-keeps-H053 path this row renumbers. |

Total files touched by sibling: 5 (all additions). Conflict surface breakdown (Q-R1-3 remediation):
- **1 doctrine-clash** ([H053/design.md](../../research/01_hypothesis_register/H053/design.md)) — incommensurable hypotheses on the same ID.
- **1 structural** (the data_requirements filename-convention divergence row).
- **5 trivial** (3 working-tree-only files that don't collide with sibling; 2 working-tree edits to docs that sibling does not touch — CLAUDE.md, README.md, plan/hypothesis_backlog.md).

The "30+ commits" framing in the task brief refers to `main..sibling = 31`. From the perspective of the branch we are actually merging *into*, the delta is 4 commits and 5 files.

## 4. Empirical findings — B. Infrastructure-reference compatibility

`git diff HEAD origin/claude/laughing-shamir-059944 -- src/ scripts/ tests/ docs/decisions/ pyproject.toml` returns empty. All the infrastructure cited by the chart-reader design docs already lives on current HEAD because current HEAD IS the merge-base.

| Reference | Sibling-branch path | Match? | Evidence |
|---|---|---|---|
| `ledoit_wolf_2008_differential_ci` callable | [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py):591 | yes | Grep on current HEAD found `def ledoit_wolf_2008_differential_ci(` at line 591. Identical to sibling (zero diff). |
| Warm-cold sidecar from commit `ec95c09` | [src/skie_ninja/models/regime/diagnostics.py](../../src/skie_ninja/models/regime/diagnostics.py) | yes | `git log --oneline | grep ec95c09` returns `ec95c09 feat(hmm): P1-HMM-WARM-COLD-DIAGNOSTIC Hellinger/TV warm-vs-cold filter regression detector`. File present at the cited path. |
| Orchestrator-triple expansion in `scripts/run_walk_forward.py` | [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) | yes | Audit trail [docs/audits/audit_trail_2026-04-24_orchestrator-triple.md](../../docs/audits/audit_trail_2026-04-24_orchestrator-triple.md) present. `git diff HEAD origin/.../059944 -- scripts/run_walk_forward.py` empty. |
| [ADR-0008-spa-omega-method.md](../../docs/decisions/ADR-0008-spa-omega-method.md) | docs/decisions/ | yes | File present on current HEAD; bytewise-identical to sibling. |
| [ADR-0009-blas-thread-pinning.md](../../docs/decisions/ADR-0009-blas-thread-pinning.md) | docs/decisions/ | yes | Same as above. |
| `vendor_legacy_1min_roll_adjusted.py` v0.3.0, commit `329fd1b`, output SHA256 `b3ee230a...3168e1d` | [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) | yes | `329fd1b` present in `git log --oneline`. Provenance JSON [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json) present (path corrected per R-R1-1 — actual location is one directory level shallower than the original draft cited). |
| `select_gaussian_hmm` cache from commit `1c85f5f` | [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py):71 | yes | Grep found `def select_gaussian_hmm(` at line 71. Commit present in `git log`. |

The premise in the task brief that current branch's chart-reader docs reference modules that exist on sibling but not on current's lineage is **false**. The merge-base IS current HEAD; everything past `main` lives on both branches identically.

## 5. Empirical findings — C. Hypothesis-ID convention

Verbatim from [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md):22 (frozen pre-reg):

> This document is the pre-registration record for hypothesis H050. Frozen at `designed`; any change requires a new hypothesis ID.

Verbatim from sibling's H053 design.md (shown via `git show`):

> Pre-registration for hypothesis H053. Frozen at `designed` on 2026-04-28. ... Any change requires a successor hypothesis ID.

Verbatim from current chart-reader H053 design.md:

> This document is the pre-registration record for hypothesis H053. Frozen at `designed`; any change requires a new hypothesis ID.

**Both H053s claim `status: designed` and frozen pre-reg discipline.** Both invoke the successor-ID rule against any change to themselves.

Existing register convention from `git ls-tree HEAD -- research/01_hypothesis_register/`:

```
H050/{README.md, design.md, data_requirements.md, aggregation_rule_addendum_2026-04-24.md}
H051/{README.md, design.md}
H052a/{README.md, design.md}
H052b/{README.md, design.md}
```

- Core files have NO date suffix: `design.md`, `data_requirements.md`, `README.md`. Date suffixes only on dated addenda (e.g. H050's `aggregation_rule_addendum_2026-04-24.md`).
- Sibling H053's `data_requirements_H053_2026-04-28.md` and `lit_review_H053_2026-04-28.md` violate this convention.
- `lit_review_*.md` is unprecedented — H050/H051/H052a/H052b have no separate literature-review file; cites live inline in design.md and in the YAML `citations` block.

ID-renumber precedent: H052 → H052b (2026-04-23) is the sole rename in project history. Documented in [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md) §"2026-04-23 — Tier-2b split". The renumber added a SUFFIX (`b`) and split-cloned content into a sibling (`H052a`) with new ID — it did NOT reassign `H052` to a different hypothesis. The semantic is preserve-and-disambiguate, never re-bind.

Tier numbering convention: H050-H052b are Tier 2b (registered 2026-04-20). Sibling's H053 declares `tier: 2b`; current's chart-reader H053 declares `tier: 2c` (Tier 2c is a NEW tier defined in current's uncommitted CLAUDE.md / hypothesis_backlog.md edits).

"First commit wins" precedent: there is none — no two hypotheses have ever been independently designed against the same ID. The only reservation mechanism in tooling is `scripts/hypothesis_new.py` which uses the `<!-- hypothesis_new.py appended -->` comment marker visible in [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md):53–56. None of the four current-branch chart-reader rows nor sibling's H053 row was added via that script (they are hand-edited table rows).

Sibling commit timestamps are 2026-04-28 09:16-09:50 CDT (one day AFTER current's chart-reader `2026-04-27` synthesis memo timestamp, but the sibling commits are the only ones COMMITTED to git). Current's chart-reader work is uncommitted. Under "first commit wins", sibling H053 has priority by being committed; under "first design-doc dated wins", current chart-reader H053 has priority by one day.

## 6. Empirical findings — D. Risk assessment

| Option | Scope (files) | Doctrine-clash conflicts | Repro-debt impact | Pre-reg discipline | Tests | Wall-clock |
|---|---|---|---|---|---|---|
| (a) Install only H053 package, sibling-keeps-H053 | 5 sibling files + rename current 4 dirs + edit 3 working-tree docs | 1 (the design.md collision, resolved by renumbering current) | Neutral; loses sibling's `plan/h053_buildout_2026-04-28.md` traceability if it isn't included; including it makes this functionally indistinguishable from (b) | Forces successor IDs on current's H053→H057, H054→H058, H055→H059, H056→H060 — but these are uncommitted, so frozen-pre-reg rule does not bite; the synthesis memo (committed-status: untracked) needs a one-line note | None added beyond sibling's 0 test additions in the H053 package | 30-60 min (rename 4 dirs + grep-replace 4 IDs across uncommitted files + write the 5 sibling files into the working tree + update synthesis memo) |
| (a) Install only H053 package, current-keeps-H053 | 5 sibling files at H057 + leave current 4 dirs as-is + leave 3 working-tree doc edits as-is | 1 (the design.md collision, resolved by renumbering sibling) | Neutral; same loss as above unless buildout plan included | Sibling H053 design.md says "Any change requires a successor hypothesis ID" — renumbering it H053 → H057 is a successor-ID action; sibling H053 is committed-frozen on its own branch but unmerged on current, so editing the YAML `hypothesis_id: H053 → H057` and renaming files at the moment of import is the same authority as a normal merge edit | Same | 30-45 min (write 5 sibling files at adjusted paths/IDs + grep-replace `H053` → `H057` inside those 5 files + add Tier-2b row in current's working-tree backlog edit) |
| (b) Full git merge, sibling-keeps-H053 | 5 added + working-tree rename of 4 dirs + working-tree edit of 3 docs | Same 1 doctrine-clash (the merge itself is a fast-forward; the doctrine-clash is in working-tree files git-merge does not see) | Best — preserves the four committed sibling commits in DAG history, no orphaned context | Same as (a) with sibling-keeps | None added beyond sibling | 45-75 min (fast-forward / merge commit + same renames + same edits + verify suite still green) |
| (b) Full git merge, current-keeps-H053 | Same | Same 1 doctrine-clash, same resolution direction as (a)/current-keeps | Best | Editing committed sibling files post-merge requires a follow-up commit; technically sound and identical to any other post-merge fix | Same | 45-75 min |
| (c) Cherry-pick subset | 0-4 commits + same renames + same edits | Same 1 doctrine-clash | Worse — partial-history cherry-pick adds DAG noise without benefit since the four commits are already linear and form a coherent sequence | Same | Same | 60-90 min (no benefit over b) |

Repro-debt is identical across all options because all infrastructure is already on current HEAD (§4). The "D-2 doc-audit finding" framing in the task brief does not apply to this branch pair — it would apply if comparing current branch to `main`, but that comparison is irrelevant for the merge decision.

## 7. Empirical findings — E. Project-wide impact

`git diff HEAD origin/claude/laughing-shamir-059944 -- pyproject.toml .pre-commit-config.yaml .gitignore .gitattributes` returns empty.

- No new dependencies on the sibling branch.
- No new environment variables.
- No new dataset paths or `~/datasets/` requirements.
- No commits on the sibling branch touch `.gitignore`, `.gitattributes`, `pyproject.toml`, `.pre-commit-config.yaml`, or `uv.lock`.

The five new files all land under existing directories (`docs/audits/`, `plan/`, `research/01_hypothesis_register/H053/`).

## 8. Synthesis and recommendation

**Recommendation: Option (b) full merge with sibling-keeps-H053 / current-renumbers-to-H057-H058-H059-H060.** Two open user-decisions remain: (i) renumber target H057-H060 vs H060-H063 (no precedent binds either; see §10), (ii) SPA-universe topology adjudication (sibling's flat-universe vs current's two-tier; see item 4 below + §10 question 2).

Justification grounded strictly in §§3–7:

1. **Option (b) is weakly dominant on repro-debt (ties with full-package (a)) and strictly dominant on DAG-hygiene** (Q-R1-5 remediation; §6 "Repro-debt impact" column). The sibling branch is exactly four linear commits ahead of HEAD with zero divergent commits in the other direction (§3 evidence: `git rev-list --count` 4 vs 0). A merge is fast-forward-eligible at the merge-base with no conflict markers (`git merge-tree` returns clean tree `3ee891c`). Cherry-picking (option c) would either replay all four commits with new SHAs, fragmenting attribution, or skip some, leaving the sibling's plan/buildout doc orphaned from its design.md predecessor. Option (a) means manually copying tracked files into the worktree, losing the four committed-author / commit-message / sign-off records — strictly worse on DAG hygiene; ties with (b) on repro-debt only if the buildout doc is included (per §6's own text).

2. **Option (b) carries no scope premium over (a)** (§4 + §7). All sibling-only code is zero-diff against HEAD; no new dependencies, no new env vars, no repo-wide config changes. The merge writes exactly five new tracked files — all additions, no modifications.

3. **Sibling-keeps-H053 is required by the existing register convention** (§5 evidence):
   - Sibling H053 declares `tier: 2b`, joining the existing committed sequence H050–H052b at the next sequential slot. This is the convention precedent (Tier 2b uses H050+).
   - Current chart-reader cohort declares `tier: 2c` — a NEW tier whose first row is, by definition, the first ID in the new tier's allocation block. Block-numbering choice (H057–H060 contiguous vs H060–H063 with a gap) is left to user decision per §10 question 1; precedent does not bind either choice (Q-R1-4 remediation).
   - The current chart-reader cohort is uncommitted (working tree only). Renumbering uncommitted working-tree files does not violate the frozen-pre-reg rule, because the rule binds at `designed`-status-AND-committed pre-reg artefacts. The synthesis memo dating to 2026-04-27 documents the cohort's design intent but is itself untracked.
   - Sibling H053 is committed (commits `89c5396`, `193120f`, `ec7c840`, `318c502`). Renaming a committed `designed`-status hypothesis is a frozen-pre-reg violation that would require a successor ID per the verbatim rule (§5). Sibling-keeps-H053 avoids that violation; current-keeps-H053 incurs it.

4. **The doctrine-clash is structural, not nominal — and extends beyond the H053 ID to SPA-universe topology** (Q-R1-1 remediation):
   - Sibling H053 is "Multi-timeframe 09:45→10:30 ET regression with opening-bar mediation" (Imai-Keele-Tingley mediation, ElasticNet/LightGBM/LLM ensemble; Tier 2b). Current H053 (about to be renumbered H057) is "1D-CNN on causal 60×5 OHLCV tensor" (train-from-scratch CNN; Tier 2c). Neither is a refinement of the other. Both must coexist as separately-registered hypotheses.
   - **SPA-universe topology incompatibility (load-bearing).** Sibling H053 design.md §1 + §10.1.5 explicitly enter the **flat project Hansen SPA universe** alongside H050/H051/H052a/H052b with **exactly three pre-registered ex-ante slots** (Arm 1 ElasticNet, Arm 2 LightGBM, Arm 3 LLM), preserving family size at 3 per Hansen 2005 §2.4 ex-ante-fixed-universe requirement. Sibling makes **zero "Family A" / "Family B" declarations**; the cohort taxonomy is flat. Current chart-reader synthesis memo §6 declares a **two-tier topology**: Family A (H050 alone, Romano-Wolf step-down per ADR-0003, M=1) + Family B (chart-reader cohort, Hansen SPA, M=5, with H050 as baseline anchor only). The two topologies are mutually incompatible: H050 cannot simultaneously sit in a Family A solo Romano-Wolf family AND in a flat Hansen SPA universe alongside H051/H052a/H052b/H053-arms.
   - This is the same incompatibility tracked under the existing follow-up `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` (the H050 design.md Romano-Wolf vs H050.yaml Hansen-SPA wiring inconsistency). Both branches added independent work that depends on different resolutions; the merge surfaces the conflict but does not adjudicate it.
   - **Resolution required, not blocked**: the merge can proceed and both H053 and the renumbered chart-reader cohort can land before the SPA-universe topology is adjudicated, because no run is executed at the merge step. Adjudication is a follow-up ADR (proposed: ADR-0010 `spa-universe-topology-flat-vs-two-tier`) and binds before any run that emits a Family-anything-aggregate inference report. Open question for user — see §10 question 2.

5. **Renumber target should be H057-H058-H059-H060 OR H060-H061-H062-H063** (Q-R1-4 remediation): precedent does not bind. Actual existing block boundaries are H001–H005 (T1), H010–H015 (T2), H020–H026 (T3), H040–H042 (T4), H050–H052b (T2b) — gaps of 4, 4, 13, 7. There is no "10-block convention." Both targets are defensible: (i) H057–H060 contiguous mirrors the H040-H042 / H050-H052b precedent of small-gap continuation within a related research thread; (ii) H060–H063 leaves a deliberate gap to signal the new tier. User selects.

   Concretely (assuming H057–H060 for now; trivially adjusted if user picks H060–H063): rename current's working-tree dirs and inline IDs `H053 → H057`, `H054 → H058`, `H055 → H059`, `H056 → H060`, and amend the working-tree CLAUDE.md / README.md / hypothesis_backlog.md / synthesis memo to reflect those IDs. The chart-reader cohort retains its M=5 internal labelling (`{H057, H058a, H058b, H059, H060}`) as a self-contained cohort declaration; whether that cohort enters the flat project Hansen SPA universe or remains a separate Family B awaits the §10 question 2 adjudication.

### Execution sketch (Q-R1-2 remediation: corrected to avoid `--ff-only` after a non-FF state)

The simplest sequencing is **fast-forward merge FIRST while HEAD is still the merge-base**, then commit chart-reader work at the renumbered IDs in a single commit. This eliminates the rename-before-merge dance entirely because the chart-reader files are uncommitted and can simply be staged at the new path names in one commit.

1. **Fast-forward merge** `git merge --ff-only origin/claude/laughing-shamir-059944`. This works *only because HEAD is still the merge-base* (§3: 4 commits ahead, 0 behind). HEAD advances to sibling HEAD `318c502`; sibling H053 lands cleanly in `research/01_hypothesis_register/H053/` with no conflicts; the working-tree chart-reader files at `research/01_hypothesis_register/H053/{design.md, README.md, data_requirements.md}` (untracked) **collide on filename** with sibling's just-merged tracked files at the same path.

2. **Resolve the working-tree filename collision before staging**. Two paths:
   - **Preferred**: `git mv` is not available for the sibling's merged files (we want them to keep H053). Move the working-tree chart-reader files to their new H057/H058/H059/H060 paths via filesystem `mv` (these are untracked, so plain `mv` is correct):
     - `mv research/01_hypothesis_register/H053/{design.md, README.md, data_requirements.md} research/01_hypothesis_register/H057/`
     - `mv research/01_hypothesis_register/H054 research/01_hypothesis_register/H058`
     - `mv research/01_hypothesis_register/H055 research/01_hypothesis_register/H059`
     - `mv research/01_hypothesis_register/H056 research/01_hypothesis_register/H060`
     - The first `mv` requires `mkdir -p research/01_hypothesis_register/H057/` first because the H053/ dir is now occupied by sibling's tracked files.
   - Alternative: stash the working-tree changes BEFORE step 1, do the FF merge, then unstash to a different path. Stash mechanics are more error-prone; use the plain-mv path.

3. **Grep-replace IDs** inside the renamed files and the working-tree doc edits, working from the highest ID first to avoid prefix collisions:
   - In the four renamed dirs (H057, H058, H059, H060), replace `H056 → H060`, then `H055 → H059`, then `H054 → H058`, then `H053 → H057`. Tooling: `ripgrep` to enumerate, then `sed -i` per file. Be careful that `H050`, `H051`, `H052a`, `H052b` are NOT touched (they are unrelated to the renumber).
   - Same replacement in the working-tree synthesis memo, hypothesis-survey memo, audit_trail file, and the working-tree edits to CLAUDE.md / README.md / plan/hypothesis_backlog.md.
   - Update Family B internal labelling: `{H053, H054a, H054b, H055, H056} → {H057, H058a, H058b, H059, H060}`. **Do NOT rename "Family B" to "Family C"** — the prior draft's premise that sibling H053 also uses "Family B" is empirically false (Q-R1-1 remediation). The actual SPA-universe topology question is deferred to ADR-0010 per §10 question 2.

4. **Stage and commit** the chart-reader cohort + working-tree doc edits at their renumbered IDs in one focused commit. Commit message references the merge commit (sibling H053 SHA) and the §10 question 2 SPA-topology open follow-up.

5. **Verify**: `python -m pytest tests/unit -x` (current HEAD ships 552/552 green per [docs/research_notes/memo_full-suite-count_2026-04-24.md](../../docs/research_notes/memo_full-suite-count_2026-04-24.md); sibling adds zero tests). Run pre-commit hooks on the renumbered files.

6. **Tag**: open follow-up `P1-CHARTREADER-RENUMBER-CASCADE` if any external references to H053-H056 remain (CHANGELOG.md, audit trail body text); these can land in a follow-up commit without blocking.

If step 1 fails for any reason (e.g., dirty working tree blocks the merge), fall back to: stash the working-tree changes, FF-merge, unstash with `git stash pop`, then proceed from step 2 with the same `mv` operations.

## 9. Sequencing (Q-R1-2 remediation)

**Recommended: merge-FIRST sequencing** (matches §8 execution sketch):

1. Fast-forward merge sibling **while HEAD is still the merge-base** (no prior local commit) — `git merge --ff-only origin/claude/laughing-shamir-059944`. This succeeds because sibling is strictly ahead of HEAD per §3. Working-tree chart-reader files remain untracked and unchanged through the merge (git's FF merge does not touch the working tree at uncommitted-conflicting paths beyond what the merge actually adds).
2. Resolve working-tree path collision via `mv` operations (chart-reader files are untracked, so filesystem `mv` is correct).
3. Grep-replace IDs in the renamed dirs + working-tree doc edits.
4. Stage + commit chart-reader cohort at renumbered IDs in one focused commit.
5. Pre-commit + suite run before push.

**Why merge-first is safer than commit-first** (corrects the prior-draft sequencing): committing the chart-reader work BEFORE the merge changes HEAD to a non-merge-base state, so `git merge --ff-only` will fail and the operator must fall back to `git merge --no-ff` (per `man git-merge` `--ff-only` requires the current HEAD to be already up to date or the merge to resolve as a fast-forward). Both paths are mechanically sound but FF-only with `mv` resolution is simpler and produces a cleaner DAG (sibling's four commits land linearly + one chart-reader commit on top, vs an explicit merge commit + a chart-reader commit + a rename commit).

**Edge case**: if the FF merge step 1 is refused by git because the working-tree contains untracked files at sibling-tracked paths (`research/01_hypothesis_register/H053/{design.md, README.md, data_requirements.md}`), git will output `error: Untracked working tree file ... would be overwritten by merge`. Resolution: `mv` the chart-reader H053 dir contents to a temporary path first (e.g., `research/01_hypothesis_register/H057_pending/`), do the FF merge, then `mv` again into the final H057 path. This is a 2-mv cost vs the 1-mv path; mechanically equivalent.

Do NOT stash the chart-reader work as the primary path — stashing untracked files requires `git stash --include-untracked` and the unstash-restore step is more error-prone than the explicit `mv` sequence above. Stash is the fallback if the `mv` path encounters unexpected git resistance.

## 10. Open questions for user

1. **Tier 2c block-numbering preference.** §8 recommends H057–H060 (contiguous with H050-block) but precedent does not bind (Q-R1-4 remediation). Existing block boundaries are H001–H005, H010–H015, H020–H026, H040–H042, H050–H052b — gaps 4, 4, 13, 7. Both H057–H060 and H060–H063 are defensible. (i) H057–H060 contiguous mirrors the H040-H042 / H050-H052b precedent of small-gap continuation within a related research thread. (ii) H060–H063 leaves a deliberate gap to signal the Tier 2b → Tier 2c transition. User selects; whichever is chosen, the renumber sweep is mechanically identical except for the offset.
2. **SPA-universe topology adjudication (load-bearing — Q-R1-1 remediation; replaces the prior-draft "Family B / Family C name collision" framing which was empirically false).** The two branches encode incompatible SPA-universe topologies for the H050-and-after research program:
   - **Sibling's flat-universe**: per sibling H053 design.md §1 + §10.1.5, all hypotheses (H050, H051, H052a, H052b, H053-arms-1/2/3, plus chart-reader cohort post-renumber as H057+) enter a single Hansen SPA universe via `universe_snapshot_id`. Sibling H053 contributes 3 ex-ante slots; total M = 1 + 1 + 1 + 1 + 3 + 5 = 12 (or whatever the chart-reader cohort's M evaluates to under this topology).
   - **Current chart-reader's two-tier**: per [docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md](memo_chartreader-research-synthesis_2026-04-27.md) §6, H050 sits in **Family A** alone (Romano-Wolf step-down per ADR-0003, M=1 degenerate per ADR-0008 single-strategy handling) and the chart-reader cohort sits in **Family B** (Hansen SPA, M=5, with H050 as baseline anchor only — H050 is NOT a Family B member). Sibling H053's three arms have no declared home in this topology; H051/H052a/H052b also have no declared home.
   - The two topologies cannot both be true simultaneously. This is the same incompatibility tracked under the existing follow-up `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` (the H050 design.md Romano-Wolf vs H050.yaml Hansen-SPA wiring inconsistency). Both branches added work that depends on different resolutions; the merge surfaces the conflict but does not adjudicate it.
   - **Adjudication is a follow-up ADR**, not a merge-blocker. The merge can land cleanly with both H053 and the renumbered chart-reader cohort coexisting at the file-system level. Adjudication binds before any run that emits a Family-anything-aggregate inference report. Recommend: open ADR-0010 `spa-universe-topology-flat-vs-two-tier` post-merge with the synthesis memo + sibling H053 + H050 design.md as input artefacts; user (or a focused audit-remediate-loop) selects the topology and amends the affected docs in a single follow-up commit. Until then, neither family-aggregate inference report can be emitted as evidence-bar artefact.
3. **Sibling H053 filename-convention deviation.** Sibling commits `data_requirements_H053_2026-04-28.md` and `lit_review_H053_2026-04-28.md` instead of the established `data_requirements.md` (and a non-precedented `lit_review.md`). Renaming sibling's files post-merge to canonical `data_requirements.md` and (new) `lit_review.md` would tighten convention but technically requires a successor-ID per the frozen-pre-reg rule. Cleanest path: leave sibling files at the date-suffixed names and document the deviation as a one-time exception in CLAUDE.md, OR file a tiny follow-up `P1-H053-FILENAME-CONVENTION-NORMALISE` flagged as not-a-pre-reg-change because the ID and content are unchanged.
4. **Sibling H053 documentation cascade.** Sibling H053 is not yet referenced in CLAUDE.md, README.md, plan/hypothesis_backlog.md, or CHANGELOG.md (none of those files were modified on the sibling branch). Post-merge, all four documentation files need a sibling-H053 row / paragraph. This is a follow-up commit (combine with the SPA-topology ADR work or land separately).
