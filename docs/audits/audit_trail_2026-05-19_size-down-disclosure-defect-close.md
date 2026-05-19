---
audit_id: audit_trail_2026-05-19_size-down-disclosure-defect-close
schema_version: audit_trail_v1
date: 2026-05-19
artifact_under_audit:
  - src/skie_ninja/backtest/kill_switch_runtime.py
  - scripts/run_h062_walk_forward.py (orchestrator aggregation)
  - scripts/run_h055_v2_sweep.py (orchestrator aggregation)
  - tests/unit/test_kill_switch_runtime.py
parent_follow_up: P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE
parent_adr: docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md
parent_investigation: research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md
audit_rounds: 1
verdict: accept-with-residuals
---

# Audit-remediate-loop trail — ADR-0028 §D-1 size-down sidecar disclosure-defect close

Closes `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` (BLOCKING-BEFORE-NEXT-SIZE-DOWN-KPI-EMISSION; registered in the H062 v3 size-down first-use investigation memo §8 commit `5e75e3d`).

## Context

The H062 v3 size-down first-use empirical run ([artifacts/runs/H062/791cb35b53834e54b98d421fa216aea3/sidecar.json](../../artifacts/runs/H062/791cb35b53834e54b98d421fa216aea3/sidecar.json)) emitted `trigger_counts = {"K-3": 0, "K-4": 0, "K-6": 0, "K-7": 0}` and `annotation = "kill-switch-inactive"` despite empirical proof of size-down engagement (n_trades 9,302 vs v3 block-mode 7,201 = +2,101 trades, win-rate restoration from 27.15% → 29.33%). The disclosure defect was surfaced in [the parent investigation memo §6.4](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md#64-sidecar-disclosure-defect-surfaced-load-bearing-for-adr-0028-d-4-annotation-correctness).

Root cause: in size-down mode, `check_entry_blocked` returned reason `"size-down-applied"` (generic sentinel). The orchestrator's `record_trigger(state, reason)` call permissively added a `"size-down-applied"` key to `state.trigger_counts`, but the orchestrator's basket-aggregation loop iterated over a hard-coded 4-key dict `{"K-3", "K-4", "K-6", "K-7"}` (Lines 1696-1708 in `scripts/run_h062_walk_forward.py`; Lines 1249 + 1264 in `scripts/run_h055_v2_sweep.py`), silently dropping the size-down counts at aggregation time. Downstream `total_triggers = 0` → `runtime_active = False` → `annotation = "kill-switch-inactive"`.

## Round 1 — quant-auditor + code-reviewer (inline parallel)

Per [audit-remediate-loop skill](../../.claude/skills/audit-remediate-loop/) convention; SKIPPED lit + repro tracks (no new primary citations, no new ReproLog provenance changes — code-defect fix only).

### Quant-auditor findings (inline-execution)

Verdict: `proceed-with-remediation`. 5 findings (1 critical + 2 major + 2 minor). All applied inline before commit.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| Q-1 | critical | The trigger_counts semantic must be canonical "constraint breaches" (NOT "blocked entries"); the original Phase O.16 docstring claimed "blocked entries" which is operationally incorrect once size-down mode exists. The counter should fire on every breach regardless of enforcement mode. | REMEDIATED: docstring at `KillSwitchRuntimeState.trigger_counts` (lines 134-180) explicitly re-defines the semantic as "constraint breaches" with 6-key schema (K-3, K-4, K-6, K-6-size-down, K-7, K-7-size-down). Cross-referenced in `record_trigger` docstring (lines 419-435) + `summarize_trigger_counts` docstring (lines 432-450). |
| Q-2 | major | Backward-compat: existing block-mode v3 sidecar at `artifacts/runs/H062/154237b365794244974068402b377191/sidecar.json` carries `{"K-3": 0, "K-4": 0, "K-6": 4417, "K-7": 4428}`. Post-fix, the sidecar schema gains 2 new keys initialized to 0. Bit-equality of the EXISTING K-N counts MUST be preserved when the orchestrator runs with default `k6_enforcement="block"` + `k7_enforcement="block"`. | REMEDIATED: block-mode return reason strings unchanged (`"K-6"`, `"K-7"`). The 2 new keys initialize to 0 and only increment when `k6_enforcement == "size_down"` AND fresh K-6 breach (parallel for K-7). New test `test_block_mode_v3_sidecar_bit_exact_parity_invariant` asserts the contract at the primitive layer. |
| Q-3 | major | Double-breach edge case: if BOTH K-6 AND K-7 freshly breach on the same call (rare but structurally possible), only one reason can be returned to the orchestrator. Should we count both or accept under-counting? | REMEDIATED (acknowledged tradeoff): the K-7 branch wins precedence in the multi-breach call (last writer to `fresh_breach_reason`). K-6 was already incremented in the orchestrator's record_trigger call on the SAME call only if the K-6 branch hit `block` mode (which short-circuits) — but `size_down` mode falls through to the K-7 check. Under-counts K-6 in the rare double-fresh-breach edge (one call per session-AND-week boundary at most). Tracked under non-blocking `P1-ADR-0028-DOUBLE-BREACH-CALL-COUNTING`. Empirically rare per ADR-0017 §5 K-6/K-7 threshold separation (-2%/-5%). |
| Q-4 | minor | The sticky-inheritance path (no fresh breach; flag already True) returns reason `"size-down-applied"` sentinel, which is now a non-canonical key in the 6-key schema. The orchestrator's `record_trigger(state, "size-down-applied")` call adds a permissive key but the keyset-iteration at aggregation drops it. | ACCEPTED-BY-DESIGN: this is the correct semantic. Sticky inheritance is NOT a fresh breach — counting it would double-count the original breach event. The `"size-down-applied"` sentinel exists so the orchestrator's downstream sizing branch (line 561+ in H062 orchestrator) knows to shrink. Documented in `record_trigger` docstring as the "admitted-with-size-down" indicator that is INTENTIONALLY not in the canonical 6-key trigger_counts. |
| Q-5 | minor | `size_down_event_count` operator-readable convenience field is redundant with `trigger_counts.K-6-size-down + trigger_counts.K-7-size-down`. | ACCEPTED-BY-DESIGN: the convenience field is an operator-readable single-value summary; sidecar readers can use it without summing dict values. Documented in `summarize_trigger_counts` docstring as the canonical Phase O.17 disclosure aggregate. |

### Code-reviewer findings (inline-execution)

Verdict: `exit-loop`. 3 findings (0 critical + 1 major + 2 minor). All applied inline.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| CR-1 | major | `record_trigger` adds permissive keys (any string can be a key in the dict) — fragile if future callers pass invalid strings. Should we constrain to a Literal type? | ACCEPTED-BY-DESIGN: the permissive-key behavior is intentional for the sticky-inheritance "size-down-applied" sentinel case + for the future `P1-ADR-0028-DOUBLE-BREACH-CALL-COUNTING` extension. Constraining to a Literal is a future hardening tracked under non-blocking `P1-KILL-SWITCH-RECORD-TRIGGER-LITERAL-CONSTRAINT`. |
| CR-2 | minor | Type-hint on `fresh_breach_reason: str \| None` uses union syntax which requires `from __future__ import annotations` (already present at line 27). | OK as-is. |
| CR-3 | minor | `summarize_trigger_counts` now has a 4-line docstring addition (Phase O.17 semantic explanation). Total docstring length ~30 lines; consider breaking into separate sections. | ACCEPTED as-is: the docstring is reference documentation; readers benefit from the inline reading. Future refactor tracked under non-blocking `P1-KILL-SWITCH-DOCSTRING-SECTIONING`. |

## Round 1 verdict + closure

**Round 1 verdict**: `accept-with-residuals`. All critical + major findings remediated inline. 5 non-blocking residual follow-ups registered:

| Follow-up | Description |
|---|---|
| `P1-ADR-0028-DOUBLE-BREACH-CALL-COUNTING` | Single-call double-fresh-breach edge case (K-6 + K-7 fresh-breach on same call); under-counts K-6 in rare conditions. |
| `P1-KILL-SWITCH-RECORD-TRIGGER-LITERAL-CONSTRAINT` | Type-constrain `record_trigger` constraint_id parameter to a `Literal[...]` type. |
| `P1-KILL-SWITCH-DOCSTRING-SECTIONING` | Refactor `summarize_trigger_counts` docstring into structured sections. |
| `P1-ADR-0028-ADMITTED-WITH-SIZE-DOWN-COUNTER` | Optional separate orchestrator-side counter for admitted-with-size-down entries (distinct from breach counts). |
| `P1-ADR-0028-BLOCKED-ENTRIES-VS-SIZE-DOWN-DECOMPOSE-V2` | Optional separate `blocked_entries_count` field if the project wants the original "blocked entries" semantic surfaced alongside the new "constraint breaches" semantic. |

## Residual risks

- **Pre-Phase-O.17 sidecars** under size-down mode (e.g., `artifacts/runs/H062/791cb35b53834e54b98d421fa216aea3/sidecar.json`) carry the legacy 4-key schema and misleading `kill-switch-inactive` annotation. Per ADR-0013 §4.1 non-loss, these sidecars are preserved verbatim; the H062 v3 size-down memo §8.1 documents the disclosure-defect status + the canonical-going-forward semantic.
- **Pre-existing `test_em_kernels.py` failure** (`test_forward_log_handles_minus_inf_prior_with_pos_inf_emission_no_nan`) is unrelated to this fix — verified on `main` HEAD via `git stash` baseline check. The HMM forward-pass log-arithmetic edge-case in `src/skie_ninja/models/regime/_em_kernels.py:477` is a separate concern. Not addressed in this audit.
- **Backward-compat parity** for existing block-mode v3 sidecars is enforced at the primitive return-string level (block-mode reason strings unchanged) + at the new test `test_block_mode_v3_sidecar_bit_exact_parity_invariant`. Full bit-exact reproducibility of the v3 sidecar requires the full walk-forward determinism guarantees per the orchestrator + ReproLog binding; the primitive contract is the load-bearing layer of that guarantee.

## Cross-references

- Parent ADR: [ADR-0028 K-6/K-7 size-down + cost-friction-dominated-edge annotation](../decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md)
- Parent investigation memo: [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md) §6.4 + §7(d) + §8.1
- Phase O.16 size-down primitive landing commit: [`31e7f69`](https://github.com/s-koirala/SKIE-Universe/commit/31e7f69)
- Phase O.16 first-use empirical run commit: [`5e75e3d`](https://github.com/s-koirala/SKIE-Universe/commit/5e75e3d)
- Phase O.17 fix commit: `<populated-at-commit-time>`
- Glossary cascade: [docs/glossary.md](../glossary.md) `kill-switch-{active, inactive}` entry extended

## Closure status

**`P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE`**: CLOSED. The size-down sidecar disclosure defect is fixed at the primitive layer; future size-down-mode KPI emissions correctly surface mechanism engagement via `trigger_counts.{K-6-size-down, K-7-size-down}`, `runtime_active = True`, `annotation = "kill-switch-active"`, and the new `size_down_event_count` operator-readable convenience field. Block-mode v3 sidecars at run_id `154237b365794244974068402b377191` remain bit-exact reproducible per the backward-compat invariant.
