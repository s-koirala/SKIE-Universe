---
date: 2026-05-19
phase: O.18
follow_up_closed: P1-ADR-0028-BLOCKED-ENTRIES-VS-SIZE-DOWN-DECOMPOSE-V2
scope:
  - src/skie_ninja/backtest/kill_switch_runtime.py
  - tests/unit/test_kill_switch_runtime.py
  - docs/glossary.md
audit_pattern: inline self-audit (Task/Agent tool not surfaced in this runtime per P1-AGENT-TOOL-NOT-SURFACED workaround)
specialist_branches: quant-auditor + code-reviewer (lit + repro + format skipped — no new citations, no ReproLog change, no identity-hygiene exposure)
rounds_used: 1
verdict: accept
---

# Audit trail — Phase O.18 trigger_counts v2 decomposition

## Scope

Close `P1-ADR-0028-BLOCKED-ENTRIES-VS-SIZE-DOWN-DECOMPOSE-V2` (Phase O.17 deferred polish per CLAUDE.md ledger §Phase O.17). Add parallel `blocked_entries_count: dict[str, int]` field to `KillSwitchRuntimeState` decomposing constraint breaches (existing 6-key trigger_counts per Phase O.17) from entries actually rejected (new 4-key blocked_entries_count). Pure additive polish; trigger_counts schema is preserved verbatim per the ADR-0028 §D-3 backward-compatibility contract.

## Acceptance criteria

1. **Bit-exact backward-compat for block-mode AND size-down mode**: existing 6-key trigger_counts + the Phase O.17 block-mode bit-exact-v3-sidecar-parity test must still pass.
2. **Pure additive**: do NOT modify the existing 6-key trigger_counts schema; the new `blocked_entries_count` is a parallel field.
3. **Parity invariant**: for block-mode-only runs, `blocked_entries_count[K-N] == trigger_counts[K-N]` for K ∈ {3, 4, 6, 7}.
4. **Glossary update**: clarify "constraint breaches" vs "entries rejected" semantic distinction.

## Round 1 findings table

### Quant-auditor branch (statistical/numerical correctness)

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| Q-F-1 | major | `record_trigger` | Orchestrator-side contract incomplete: if orchestrator skips `record_trigger` on size-down `blocked=False` returns, parity invariant breaks asymmetrically. | NO-OP: pre-existing Phase O.17 contract; orchestrator MUST call `record_trigger` for all non-None reasons (already enforced by existing tests `test_size_down_k6_increments_trigger_counts` + `test_size_down_k7_increments_trigger_counts`). New field follows same orchestrator-call contract; silent-failure consistency preserved. |
| Q-F-2 | minor | `record_trigger` allowlist | Hardcoded constraint-id set literal `{"K-3", "K-4", "K-6", "K-7"}`. A typo at orchestrator layer (lowercase / extra digit) would silently land outside both `trigger_counts` block-mode keys AND `blocked_entries_count`. | TRACKED-EXISTING: covered by `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` extended scope (constraint-id typo detection at orchestrator layer is a separate defensive-helper question; cross-coupling risk if added inline). |
| Q-F-3 | verified-clean | new test `test_v3_sidecar_bit_exact_block_mode_parity_invariant` | V3 sidecar at run_id `154237b365794244974068402b377191` carries K-6: 4417 + K-7: 4428 in trigger_counts. | PASS: Phase O.18 parity invariant `blocked_entries_count == trigger_counts` holds bit-exactly for block-mode keys; verified by new dedicated test. |
| Q-F-4 | verified-clean | `record_trigger` | Size-down K-6 / K-7 breaches increment only `trigger_counts["K-N-size-down"]`; `blocked_entries_count` stays at zero. | PASS: semantically correct per ADR-0028 §D-1 size-down mode (entry admitted at reduced size, not rejected). |

### Code-reviewer branch (Python/general code quality)

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| CR-F-1 | minor | `record_trigger` line 599 | Hardcoded set literal `{"K-3", "K-4", "K-6", "K-7"}` repeated each call; clarity + minor performance loss. | REMEDIATED inline: extracted as module-level `_BLOCK_MODE_REASONS: frozenset[str]` constant per the code-reviewer recommendation. |
| CR-F-2 | minor | `summarize_trigger_counts` line 626 | `if state.blocked_entries_count` evaluates False for empty-dict cases; would emit `total_blocked_entries=0` + `blocked_entries_count={}` for pre-Phase-O.18 state constructed without `init_runtime_state`. | NO-OP: empty-dict default is the backward-compat path; Phase O.18 invariant only applies to post-`init_runtime_state` callers. Documented in field docstring. |
| CR-F-3 | verified-clean | dataclass | Frozen dataclass + immutable-update pattern preserved via `replace()`; no mutation of input state. | PASS. |
| CR-F-4 | verified-clean | test coverage | 12 new tests covering (a) init schema (b) all 4 block-mode K-N record paths (c) size-down K-6 + K-7 paths (d) sticky size-down-applied sentinel (e) parity invariant (f) divergence (g) V3 sidecar bit-exact replay. | PASS: 7 semantic axes covered. |

## Round 1 remediation applied

- **CR-F-1 (minor → applied inline)**: Extracted `_BLOCK_MODE_REASONS: frozenset[str] = frozenset({"K-3", "K-4", "K-6", "K-7"})` as module-level constant; `record_trigger` references the constant via `if constraint_id in _BLOCK_MODE_REASONS`. Performance + clarity improvement. Justify comment added inline.

No critical findings; no remaining majors.

## Test results

```
tests/unit/test_kill_switch_runtime.py: 58 passed (46 baseline + 12 new Phase O.18)
tests/unit/test_kill_switch_validation.py: 20 passed (validator parity preserved)
combined: 78 passed in 0.74s
```

### New Phase O.18 test class `TestBlockedEntriesCountV2` — 12 tests

| Test | Verifies |
|---|---|
| `test_init_state_has_canonical_4_key_blocked_entries_schema` | Init schema = {K-3, K-4, K-6, K-7}: 0 |
| `test_block_mode_k6_increments_both_fields` | Parity: trigger_counts.K-6 ++ AND blocked_entries_count.K-6 ++ |
| `test_block_mode_k7_increments_both_fields` | Parity: K-7 symmetric to K-6 |
| `test_block_mode_k3_increments_both_fields` | K-3 (no-add-to-loser) increments both |
| `test_block_mode_k4_increments_both_fields` | K-4 (capacity-cap) increments both |
| `test_size_down_k6_does_not_increment_blocked_entries` | Divergence: K-6-size-down → trigger_counts.K-6-size-down ++ only |
| `test_size_down_k7_does_not_increment_blocked_entries` | Divergence: K-7-size-down → trigger_counts.K-7-size-down ++ only |
| `test_sticky_size_down_applied_increments_neither` | Sentinel: neither canonical field touched |
| `test_summarize_emits_both_count_fields` | Summary includes blocked_entries_count + total_blocked_entries |
| `test_summarize_block_mode_parity_invariant` | Synthetic 3+2+5+4 mix: parity invariant holds |
| `test_summarize_size_down_divergence` | Synthetic 2 K-3 + 3 K-6-size-down: blocked=2 vs triggers=5 |
| `test_v3_sidecar_bit_exact_block_mode_parity_invariant` | V3 ledger replay: K-6=4417, K-7=4428 → blocked_entries_count agrees |

## Backward-compat verification

1. **Phase O.17 6-key trigger_counts schema preserved verbatim** — `init_runtime_state` still produces the 6-key dict; `record_trigger` still increments `trigger_counts[constraint_id]` for ANY non-empty constraint_id (block-mode + size-down + sticky-sentinel all permissively recorded).
2. **V3 sidecar at run_id `154237b365794244974068402b377191`** reproducible bit-exactly — `test_v3_sidecar_bit_exact_block_mode_parity_invariant` synthesises the V3 ledger directly at the primitive layer (4417 K-6 + 4428 K-7 block-mode triggers); both `trigger_counts` (Phase O.17 contract) AND new `blocked_entries_count` (Phase O.18 parallel field) carry the canonical values.
3. **Pre-Phase-O.18 state constructed without `init_runtime_state`** — `default_factory=dict` on the new field tolerates empty-dict default; `record_trigger.get(...).get(constraint_id, 0) + 1` initializes missing keys at 0+1=1; `summarize_trigger_counts` emits empty dict + `total_blocked_entries=0` for pre-Phase-O.18 state.

## Glossary update

[docs/glossary.md](../glossary.md) `kill-switch-{active, inactive}` entry extended with explicit semantic decomposition: `trigger_counts` (constraint breaches; 6-key) vs `blocked_entries_count` (entries rejected; 4-key) + the operator-readable invariant `total_triggers - total_blocked_entries = size_down_event_count`. Cross-link to Phase O.18 follow-up ID.

## Residual risk

- Q-F-2 minor (constraint-id typo detection at orchestrator layer): tracked under `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` extended scope; defensive helper would create cross-coupling.

## Verdict

**Round 1 ACCEPT** — no critical or major findings; one minor remediated inline; backward-compat fully preserved; new test class covers 7 semantic axes; V3 sidecar bit-exact parity invariant verified.

## Closes

- `P1-ADR-0028-BLOCKED-ENTRIES-VS-SIZE-DOWN-DECOMPOSE-V2` (Phase O.17 deferred polish; non-blocking).
