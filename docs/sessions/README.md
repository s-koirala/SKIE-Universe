# Session handoffs

Per-session continuity records written at the end of a non-trivial working session
(or before a planned cross-session / multi-hour-compute handoff), per the
`session-handoff` skill. They capture what a `/compact` or fresh session would
otherwise lose: in-flight state, load-bearing decisions, dead-ends, audit branches
skipped, operator-queued decisions, and the single concrete next step.

## Layout

- `session_handoff_{YYYY-MM-DD}_{HHMM}_{slug}.md` — one per session (HHMM is local-clock
  24-hour; disambiguates same-day same-slug handoffs).
- `INDEX.md` — append-only chronological index (one row per session; never overwritten,
  mirroring the ADR-0013 §4.1 non-loss discipline — a resumed-and-finished session
  appends a new row rather than editing the prior one).

## Status vocabulary

- `closed` — work complete; no successor session needed.
- `in-flight` — paused; a successor session is expected to resume (the next step is stated).
- `aborted` — abandoned; reason in the handoff body.

## Identity hygiene

Per [rules/publishing.md](../../rules/publishing.md): `worked_by` lists agent handles
(`main`, `quant-auditor`, …), never human identifiers; `project` is the pseudonymous
name; no OS-username paths or real-name tokens.
