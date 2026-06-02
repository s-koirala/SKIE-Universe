# Memo — Session-handoff / cross-session-continuity pattern research

**Date:** 2026-05-19
**Author:** SKIE
**Scope:** survey the Claude / Codex / AI-engineering community's session-handoff
patterns and recommend a fit for SKIE-Universe (and the two operator-owned
template repos that should inherit it).
**Status:** draft research memo; operator review pending. NOT committed.

---

## §1 Research scope + sources

Twelve primary sources reviewed. Each is enumerated below with its URL and a
one-sentence summary of load-bearing relevance.

### Tier-1 repos (verified via direct GitHub fetch or canonical project page)

1. [parcadei/Continuous-Claude-v3](https://github.com/parcadei/Continuous-Claude-v3)
   — "Context management for Claude Code. Hooks maintain state via ledgers and
   handoffs. MCP execution without context pollution. Agent orchestration with
   isolated context windows." Canonical reference for the YAML-handoff +
   continuity-ledger + PreCompact-hook pattern.

2. [AnastasiyaW/mclaude](https://github.com/AnastasiyaW/mclaude) —
   "Multi-session collaboration for Claude Code: atomic locks, handoffs, memory
   graph, messaging, hub server, bridge, voice I/O. 166 tests. Zero core deps."
   Canonical reference for the dated-filename handoff + `worked_by` call-stack
   + "NOT worked" dead-end-prevention pattern.

3. [wshobson/agents](https://github.com/wshobson/agents) — "Intelligent
   automation and multi-agent orchestration for Claude Code." Confirms the
   80-plugin curated set has NO native session-handoff (delegates to Pensyve
   plugin); useful negative evidence.

4. [anthropics/claude-code issue #18417](https://github.com/anthropics/claude-code/issues/18417)
   — "Feature Request: Native session persistence and context continuity" —
   confirms cross-session handoff is an open community-recognized gap.

5. [anthropics/claude-code issue #15222](https://github.com/anthropics/claude-code/issues/15222)
   — "[FEATURE] Decision History Tracking with DECISIONS.md" — community-
   surfaced proposal for explicit decision + rejected-alternative tracking.

6. [edwilde gist "handoff" skill](https://gist.github.com/edwilde/cb2bf5f8851ea1d79ddc19995eec8b5b)
   — A complete six-section SKILL.md handoff template (Goal / Constraints /
   Current State / Technical Context / Next Steps / Restoration Procedure).
   Writes to `./session-summary/`.

7. [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit)
   — Curated toolkit README; lists several third-party session-memory plugins
   (claude-mem, claude-recap, claude-supermemory, cortex) and an
   orchestration-level "Context Manager" agent specializing in context
   compression + session summaries. The toolkit itself is a directory; the
   pattern lives in its referenced plugins. Negative evidence: the toolkit
   does not advertise a single canonical handoff convention — the ecosystem
   is fragmented.

### Tier-2 docs and skill descriptions

8. [Claude Code session-memory docs (claudefa.st)](https://claudefa.st/blog/guide/mechanics/session-memory)
   — Documents Claude Code's BUILT-IN auto-extracted session summary stored at
   `~/.claude/projects/<hash>/<session-id>/session-memory/summary.md` with
   four canonical fields: session title, current status, key results, work log.

9. [Session-Handoff skill (mcpmarket listing)](https://mcpmarket.com/tools/skills/session-handoff)
   — Marketplace skill that automates YAML+markdown handoff document creation
   capturing goal / status / decisions / failed approaches / next step.

10. [Pulumi blog "Picking the Right Framework for Your Coding Agent"](https://www.pulumi.com/blog/claude-code-orchestration-frameworks/)
    — Comparison of Superpowers vs GSD vs GSTACK. Identifies state-to-disk
    handoff (GSD) and role-scoped handoff (GSTACK) as alternatives to the
    single-orchestrator pattern (Superpowers). Diagnoses the "mega-orchestrator
    hits its own context limit" failure mode.

11. [Deferred Finding Manager skill (mcpmarket)](https://mcpmarket.com/ko/tools/skills/deferred-finding-manager)
    — Skill that converts code-review findings deferred from current PR into
    GitHub issues with linked context — directly analogous to SKIE-Universe's
    `P1-*` follow-up convention.

12. [Async Task Queue skill (mcpmarket)](https://mcpmarket.com/tools/skills/async-task-queue)
    — Persistent JSON queue for technical-debt + minor-fix items deferred from
    current session.

### Negative-evidence checks (cited to acknowledge the gap)

- [hesreallyhim/awesome-claude-code README](https://github.com/hesreallyhim/awesome-claude-code/blob/main/README.md)
  — top-level table-of-contents marked "TODO; under reconstruction" at fetch
  time; no current session-handoff index entry to verify.
- The `claude-code-superpowers` repository name surfaces frequently in blog
  posts but search did not return a verifiable canonical GitHub URL during this
  session. The "Superpowers" framework is real and documented (see source 10),
  but the specific repo URL was not independently verified; treat the name as
  "framework / convention" rather than a single repo attribution.
- Both anthropics/claude-code issues #15222 (DECISIONS.md) and #18417 (native
  session persistence) were closed `not planned` at audit time. That status
  reinforces the gap-is-real framing — the community has surfaced the request,
  the canonical product has declined to ship it natively, so third-party
  patterns (mclaude, Continuous-Claude-v3, the marketplace skills) fill the
  gap.

---

## §2 Patterns surfaced

The twelve sources cluster into four pattern-families. Each family is named,
described, and attributed to its primary canonical source.

### Pattern-family A — "Structured-handoff-memo, markdown + YAML frontmatter"

**Canonical sources:** parcadei/Continuous-Claude-v3 (source 1), AnastasiyaW/mclaude
(source 2), the edwilde gist (source 6), mcpmarket Session-Handoff (source 9).

**Core idea.** At session end (or pre-compaction), write one markdown file per
session to a known directory. YAML frontmatter carries machine-readable
metadata (date, session id, status); the body carries human-readable sections.
Next session loads the latest file via a SessionStart hook or manual
invocation.

**Section conventions (intersection across the four sources):**

- Goal (1-2 sentences)
- Done (concrete results with file paths)
- In progress / current state
- Decisions (with rationale)
- What did NOT work (the failed-approach ledger; explicit in mclaude)
- Blockers
- Next step (one concrete thing to do next)

**File naming:** `YYYY-MM-DD_HH-MM_<session-id>_<slug>.md` (mclaude); or
`<project>_session_summary_<date>.md` (edwilde gist).

**Storage:** `thoughts/shared/handoffs/<session>/` (Continuous-Claude-v3);
`.claude/handoffs/` (mclaude); `./session-summary/` (edwilde).

### Pattern-family B — "Memory graph with valid-from / superseded-by metadata"

**Canonical source:** AnastasiyaW/mclaude (source 2).

**Core idea.** Decisions are stored as small markdown files in a hierarchical
"memory drawer". Each file carries `valid_from`, `valid_to`, `superseded_by`
metadata. Old decisions are NEVER deleted — they are marked superseded and
kept for history. Wiki-link `[[path]]` navigation connects related files.

This is the pattern most analogous to SKIE-Universe's existing ADR-0013 §4.1
non-loss mandate. It generalizes the ADR convention to per-decision
granularity below the ADR level.

### Pattern-family C — "Append-only chronological index / continuity ledger"

**Canonical sources:** parcadei/Continuous-Claude-v3 (source 1) "continuity
ledger" + mclaude (source 2) `INDEX.md` with `ACTIVE / RESUMED / CLOSED /
ABANDONED` status markers.

**Core idea.** A single per-project `INDEX.md` or `CONTINUITY_*.md` carries a
chronological log of work-units. Each row has a status marker and a pointer
to the per-session handoff file. Never overwritten; always append. New
sessions read the tail of the index, then load the pointed-to handoff(s).

This directly maps to what SKIE-Universe currently does at the **phase** level
(CLAUDE.md Phase O.0 → Phase O.13 ledger). The gap: SKIE-Universe has no
sub-phase / per-session granularity in the ledger.

### Pattern-family D — "Deferred-findings queue + decision-history register"

**Canonical sources:** Deferred Finding Manager skill (source 11), Async Task
Queue skill (source 12), proposed DECISIONS.md (source 5).

**Core idea.** Two separate persistent stores:
(a) a **deferred-findings queue** (JSON or markdown table) for "noticed in
this session, deferred to a future session" items;
(b) a **DECISIONS.md** ledger for "alternatives considered, paths rejected,
backtracked approaches" — answers the why-not as well as the why.

This directly maps to SKIE-Universe's `P1-*` follow-up convention. The gap:
SKIE-Universe currently mixes BLOCKING preconditions, non-blocking polish, and
operator-action items in a single flat namespace; there's no per-session
"opened this session / closed this session / still open" view.

### Cross-pattern observation

The frameworks compared by Pulumi (source 10) — Superpowers vs GSD vs GSTACK —
diverge primarily on **whether the orchestrator itself persists state to
disk between phases**. GSD wins this comparison ("each orchestrator stays
under 50% context capacity; on phase complete, writes state to disk; fresh
orchestrator picks up"). GSD's approach is essentially Pattern-family A
applied **at phase boundaries within a single session as well as across
sessions** — the same handoff document serves both purposes.

---

## §3 Pattern recommendation for SKIE-Universe

### Recommended pattern: A + C + D hybrid (mclaude-shaped backbone)

**Adopt all three of A, C, D; defer B.** Rationale ≤300 words:

SKIE-Universe already implements Pattern B in spirit (ADR-0013 §4.1 non-loss
mandate; design.md frozen §1-§7 + Path A amendment discipline; versioned
successor naming such as `kpi_report_v2.md` that reference v1 verbatim). The
mclaude memory-graph would duplicate this with per-decision granularity below
the ADR level, which is more machinery than the per-session-continuity gap
warrants. The current ADR + KPI-report-card non-loss convention is already
mature.

The gap the operator identified is squarely **A + C + D**. CLAUDE.md captures
WHAT (phase ledger) and WHY (decision rationale) at the project level; an
ADR-0013 audit trail captures the audit-remediate-loop trail per-task. What's
missing is the **session-level** layer between the audit trail and CLAUDE.md:
what was investigated this session, what audit branches were skipped and why,
what's still in flight, what queued for next session.

**Trade-offs.** Cost: one new file per session (~3-8 sessions per work-week
estimated from the Phase O.10-O.13 cadence); ~5 minutes of session-end author
time per file. Benefit: a Session-(N+1) agent can read one handoff + one
audit trail to inherit Session-N's mental model, eliminating the
re-discovery cost. The cost compounds favourably: at 20-30 minutes saved per
session of warm-up, the handoff pays for itself after the first session that
references it. Risk: handoff hygiene drift — operator may stop writing them
once novelty wears off. Mitigation: a SessionEnd hook (analogous to the
existing emit-repro-log discipline) makes handoff creation a structural
default rather than a per-session memory check.

**Structural sketch of the handoff template** (the artifact this skill
produces — section conventions are mclaude-derived; the field set is augmented
to mirror SKIE-Universe's existing audit + follow-up vocabulary):

```markdown
---
session_id: <YYYY-MM-DD_HHMM>_<topic-slug>
date: <ISO-8601 UTC>
project: SKIE-Universe
worked_by: [<agent-handle>, <subagent-handles-in-call-stack-order>]
status: closed | in-flight | aborted
phase: <CLAUDE.md phase pointer, e.g., Phase O.13 Step 1b>
audit_trail: <pointer to docs/audits/audit_trail_*.md if any>
---

## Goal
<1-2 sentences. WHY did this session exist.>

## Done
<concrete results: bullet list with file paths + commit hashes if any>

## In flight
<work started this session that's NOT done; explicit state of the work>

## Decisions made (with rationale)
<load-bearing decisions made this session that a future session must inherit>

## What did NOT work
<dead ends investigated this session; explicit so a future session does NOT
rediscover them>

## Audit branches skipped (and why)
<SKIE-Universe-specific: which audit-remediate-loop branches were
deliberately omitted; reference the SKILL.md routing convention>

## Open decisions queued for operator
<questions requiring operator input; explicit so the next session knows what
to ask first>

## Follow-ups opened this session
<new `P1-*` items registered; cross-link to CLAUDE.md or hypothesis_backlog.md
entry>

## Next step
<single most concrete thing to do next; one sentence>

## Restoration procedure
<environment / config / branch info the next session needs to resume>
```

**Storage convention** (mirroring the existing
`docs/audits/audit_trail_YYYY-MM-DD_*.md` + `docs/research_notes/memo_*.md`
patterns):

- Per-session file: `docs/sessions/session_handoff_YYYY-MM-DD_<topic-slug>.md`
- Project-level chronological index: `docs/sessions/INDEX.md` (append-only;
  one row per session with status marker + file pointer)

The index file gives a Session-(N+1) agent a single point of entry; the
per-session files give the detail. The append-only INDEX is Pattern C; the
per-session template is Pattern A; the "follow-ups opened" + "open decisions
queued" sections are Pattern D.

---

## §4 The deliverable prompt

The text below is the prompt the operator can paste into a fresh Claude or
Codex session against each of the three target repos. It is self-contained —
no prior conversation context is required. Reuse across the three repos by
substituting the per-repo block in §4.B.

> ---
>
> **Task: land a session-handoff + cross-session-continuity pattern into the
> target repo.**
>
> **Context — the gap (read first).** SKIE-Universe is a longitudinal
> pre-registered quant-research repository that uses an audit-remediate-loop
> skill, typed subagents (quant-auditor / reproducibility-verifier /
> literature-check / code-reviewer / format-auditor), and a chronological
> phase-ledger in CLAUDE.md to govern session-level orchestration. CLAUDE.md
> captures WHAT decisions are made + WHY. CHANGELOG.md is one line per phase.
> Per-task audit trails live at `docs/audits/audit_trail_YYYY-MM-DD_*.md`.
>
> **What's missing.** The orchestrator-level reasoning a Session-N agent
> should hand off to Session-(N+1): in-flight investigation contexts, audit
> branches deliberately skipped, deferred-not-applied findings, load-bearing
> assumptions the next session should inherit, open operator-decision queues.
> Research into the Claude / Codex community surfaced four canonical pattern-
> families addressing this gap. The recommended fit is an
> mclaude-shaped per-session handoff document + append-only chronological
> index + explicit deferred-findings queue, captured under
> `docs/sessions/session_handoff_<date>_<slug>.md` with an index at
> `docs/sessions/INDEX.md`. The full research memo is at
> [docs/research_notes/memo_session_handoff_research_2026-05-19.md](docs/research_notes/memo_session_handoff_research_2026-05-19.md)
> in the SKIE-Universe worktree.
>
> **§4.A Section convention to use (mclaude-derived; same template in all
> three repos).** Every per-session handoff carries:
> YAML frontmatter — session_id, date (ISO-8601 UTC), project, worked_by
> (call-stack order), status (closed / in-flight / aborted), phase, audit_trail
> pointer.
> Body sections — Goal (1-2 sentences); Done (concrete results + file paths);
> In flight; Decisions made (with rationale); What did NOT work; Audit branches
> skipped (and why); Open decisions queued for operator; Follow-ups opened this
> session; Next step (single concrete thing); Restoration procedure.
>
> **§4.B Per-repo deliverable.** Substitute the appropriate block:
>
> **Block (1) — for s-koirala/dotfiles target.** Add a `claude/skills/session-handoff/`
> directory with a SKILL.md authoring the template above, plus a
> `claude/templates/session_handoff_TEMPLATE.md`, plus a
> `claude/commands/session-handoff.md` command-style entry that invokes the
> skill. The skill SHALL write to `docs/sessions/` in the current cwd (NOT in
> the home directory). Add a sample `docs/sessions/INDEX.md` schema-only file.
> Do NOT introduce a SessionEnd hook in this repo — hooks are settings.json-
> level and should land separately under operator-explicit review. Identity
> hygiene: every committed file must be free of real-name fields, OS username
> paths, and personal-email-TLD addresses per the publishing.md convention.
>
> **Block (2) — for s-koirala/codex-research-bootstrap target.** Add a
> `skills/session-handoff/SKILL.md` parallel to the existing
> `skills/audit-remediate-loop/SKILL.md`; add
> `templates/session_handoff_TEMPLATE.md`. Update `examples/AGENTS.md` (the
> sample shipped to end users) to reference the new skill in its operating
> posture section. Wire the skill into `tools/bootstrap_project.py` so a fresh
> `bootstrap-project` run scaffolds `docs/sessions/INDEX.md` alongside the
> existing scaffold output. The skill must use Python stdlib only on the
> bootstrap path; third-party deps reserved for skill-asset / analysis-pipeline
> files per the existing dependency-posture convention. Pass through the
> existing `tools/check_identity.py` forbidden-token list at commit time.
>
> **Block (3) — for the LOCAL `C:\Users\skoir\.claude\` directory target
> (non-destructive).** Add a `skills/session-handoff/SKILL.md` parallel to
> the existing `skills/audit-remediate-loop/SKILL.md`. Add
> `commands/session-handoff.md`. Do NOT modify the existing CLAUDE.md, rules/,
> hooks/, agents/, or settings.json — those are user-global and any change
> requires explicit operator review. The skill SHALL write to the current
> project cwd's `docs/sessions/` (NOT into `~/.claude/`). If the cwd does not
> contain a `docs/` directory, create one and emit a single
> `docs/sessions/README.md` documenting the convention.
>
> **§4.C Audit-remediate-loop discipline (mandatory for this task).** Apply
> SKIE-Universe's three-round-cap audit-remediate-loop convention. Round 1:
> spawn parallel format-auditor + literature-check + code-reviewer agents
> against the new SKILL.md + template + per-repo wiring. Format-auditor
> verifies the template carries every required section + YAML field +
> identity-hygiene compliance. Literature-check verifies any cited pattern
> attribution (mclaude / Continuous-Claude-v3 / Pulumi GSD-vs-GSTACK) resolves
> to a real public URL with the claimed content. Code-reviewer verifies the
> SKILL.md is well-formed (parseable YAML frontmatter; consistent markdown
> structure; no inline secrets) and any code touchpoints (bootstrap script for
> repo 2) follow the host repo's existing conventions. Apply Round-1
> remediation inline. Save the audit trail at
> `docs/audits/audit_trail_YYYY-MM-DD_session-handoff-landing.md` in the
> respective repo. Round 2 is required only if Round 1 surfaces a critical
> defect (wrong-DOI / wrong-attribution / identity-hygiene failure).
>
> **§4.D Guardrails.**
> Do not commit + push without explicit operator sign-off. Save files to disk;
> stage them; show the diff; STOP. Do not run `git push`.
> Do not modify settings.json, hooks, or any pre-commit gate in any of the
> three repos.
> Per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE`: when citing a community pattern
> as the source of a design decision, verify the source URL is reachable +
> the cited claim is in the page body. Do not paraphrase what a repo
> "presumably" contains — fetch and verify.
> Identity hygiene: no real-name fields; no OS username paths
> (`C:\Users\<name>\` should appear as `<HOME>\` or a similar placeholder in
> committed files); no personal-email-TLD addresses; no maintainer-specific
> project tokens.
> Non-loss for personal data in the dotfiles repo: if a file is being added
> alongside existing files that look operator-personal, do not move or rename
> them. Add only.
>
> **§4.E End-of-task deliverable summary.** End the task with a < 200-word
> summary covering: files added per repo + lines added; audit-trail file
> location; Round-1 findings count by branch + remediation count; explicit
> "NOT committed; operator review pending" statement.
>
> ---

---

## §5 Out-of-scope / not-recommended-here

Items reviewed during research but explicitly NOT recommended for adoption in
the current cycle:

- **PostgreSQL + pgvector persistence (Continuous-Claude-v3 stack).** Too
  heavyweight for the SKIE-Universe single-operator solo-research deployment
  model. Plain markdown + a SessionStart hook (deferred to a future cycle)
  matches the operating posture.
- **MCP-server-backed memory hub (mclaude hub server).** Adds an
  always-running process; deployment cost > continuity benefit at current
  research velocity (~3-8 sessions per work-week).
- **PreCompact hook auto-write (Continuous-Claude-v3).** Useful but
  hook-layer change; deferred to a separate operator-explicit cycle. Manual
  handoff authoring is the v1 default; auto-emit can land in a v2.
- **mclaude memory graph with `valid_from` / `superseded_by` per-decision
  metadata.** ADR-0013 §4.1 + the project's versioned-successor convention
  already covers the same ground at the ADR + design.md + KPI-card level.
  Per-sub-decision granularity is more machinery than the operator-identified
  gap requires.

---

## §6 Next steps

1. Operator reviews this memo + the audit trail at
   [docs/audits/audit_trail_2026-05-19_session-handoff-research.md](../audits/audit_trail_2026-05-19_session-handoff-research.md).
2. On operator sign-off, the §4 deliverable prompt is pasted into three
   fresh sessions (one per target repo) — each session runs the audit-remediate-loop
   discipline of §4.C + saves its own audit trail.
3. After the three repos land the pattern, a follow-on cycle (a) writes the
   first SKIE-Universe handoff under the new convention; (b) optionally
   considers a SessionEnd hook (operator-explicit decision).
4. The first 5-10 handoffs serve as the empirical calibration for whether the
   template needs adjustment (sections added / dropped / renamed). Treat v1
   of the template as provisional.

---

*Memo emitted 2026-05-19. NOT committed; operator review pending.*
