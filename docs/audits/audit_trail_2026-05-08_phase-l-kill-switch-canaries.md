---
deliverables:
  - src/skie_ninja/backtest/kill_switch_canaries.py
  - tests/unit/test_kill_switch_canaries.py
audit_pattern: parallel_proper_isolated_dyad (quant-auditor + reproducibility-verifier; literature-check skipped — no new citation claims introduced; only ADR-0017 + ADR-0001 cross-references which were verified in the predecessor Phase L commit-3 audit)
auditors_round_1:
  - quant-auditor (agentId a9e8c50595b9ee10e; verdict proceed-with-remediation; 11 findings: 2 critical + 2 major + 7 minor)
  - reproducibility-verifier (agentId a4d45c92557533abb; verdict accept; 1 minor finding — unused numpy import)
parent_directive: P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION (BLOCKING-BEFORE-LAUNCH per ADR-0017 §5; H055 §11.2 BLOCKING-BEFORE-LAUNCH precondition)
predecessor_audit: docs/audits/audit_trail_2026-05-08_phase-l-failure-mode-stress-test.md (A1 closure)
status: accept (Round-1 remediation closed all critical+major; minors remediated or tracked as follow-ups; exit per SKILL.md "Exit check" — only minors remain)
---

# Audit trail — Phase L kill-switch backtest validation canaries (2026-05-08)

## Context

This audit lands `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` per ADR-0017
§5 + Cycle-4 leak-canary discipline; the seventh and final BLOCKING-BEFORE-
LAUNCH primitive required by H055 §11.2. The primitive validates K-1..K-8
hard kill-switch constraints against a per-fold strategy trade ledger and
emits a 3-state annotation `kill-switch-canary-{pass,fail,partial}` for the
KPI report card §"Methodological-correctness annotations" per ADR-0014 §3.2
row 9.

Implementation lives at [src/skie_ninja/backtest/kill_switch_canaries.py](../../src/skie_ninja/backtest/kill_switch_canaries.py)
(440+ LoC; TradeLedgerEntry + KillSwitchCanaryResult + 8 K-N validators +
orchestration), with comprehensive unit tests at
[tests/unit/test_kill_switch_canaries.py](../../tests/unit/test_kill_switch_canaries.py)
(29 tests; all green). The simulator at
[src/skie_ninja/backtest/stress_test.py](../../src/skie_ninja/backtest/stress_test.py)
gained a new `skipped_trade_indices` field on `KillSwitchSimulationResult`
to enable correct K-6/K-7 violation attribution.

## Round 0 — production drafting

Initial implementation: 8 K-N validators (K-1, K-2, K-3, K-4, K-5, K-6,
K-7, K-8) + orchestration function `validate_kill_switches_per_fold` that
runs all 8 and emits a summary annotation. 27 unit tests; all green at
Round 0.

## Round 1 — parallel proper-isolated dyad audit

Two subagents spawned in parallel: quant-auditor + reproducibility-verifier.

### Round-1 findings table

| Severity | ID | Auditor | Issue | Disposition |
|---|---|---|---|---|
| critical | Q-1 | quant | K-6 violation attribution wrong: pre-halt trades flagged as false positives. Simulator halts AT the breaching trade; trades 0+1+2 in `[-1R, -1R, -1R, -0.5R, -0.5R]` execute legitimately (K-6 fires after trade 2's PnL is realised); only trades 3, 4 are violations. Validator's "first-encounter" heuristic flagged trades 1, 2, 3, 4. | REMEDIATED — added `skipped_trade_indices` field to `KillSwitchSimulationResult`; K-6/K-7 validators now derive violations directly from this field |
| critical | Q-2 | quant | K-7 same defect as K-6. | REMEDIATED with same fix |
| major | Q-3 | quant | Silent-pass on deferred metadata: when K-2/K-5/K-8 metadata absent, validator records `per_K_passed[K-N]=True`, annotation = "kill-switch-canary-pass". Operator reading the report card cannot distinguish "all 8 K-N validated and passed" from "K-1/K-3/K-4/K-6/K-7 passed; K-2/K-5/K-8 deferred". | REMEDIATED — added `per_K_validated` field to `KillSwitchCanaryResult`; new 3-state annotation grammar: "pass" (all validated AND passed), "fail" (any validated K-N failed), "partial" (no failures, but some K-N deferred / n/a) |
| major | Q-4 | quant | K-4 validates per-trade `\|position_size\|`, not running portfolio position. Two overlapping ES trades of 10 + 15 = 25 running position pass K-4 (each individually <= 20) but exceed the cap. ADR-0001 + CLAUDE.md §Standing constraints define K-4 as a portfolio-wide running limit. | REMEDIATED — replaced per-trade check with running-position scan analogous to K-5; new test `test_k4_fails_on_concurrent_positions_exceeding_running_cap` exact-asserts viols=(1,) |
| minor | Q-5 | quant | K-3 conservative implementation flags ANY same-direction overlap, but spec says "while in unrealized loss" — would falsely flag legitimate pyramid-into-winner strategies | TRACKED — `P1-K3-MARK-TO-MARKET-AWARE-VALIDATOR` follow-up; conservatism documented in docstring |
| minor | Q-6 | quant | K-5 uses entry fill_price (matches ADR-0017 §5.2 worked example); should explicitly note bias direction in docstring | DOCUMENTED — docstring updated to note bias |
| minor | Q-7 | quant | K-2 `tolerance_ns=60_000_000_000` lacks `# justify:` annotation | TRACKED — `P1-K2-TOLERANCE-NS-JUSTIFY` |
| minor | Q-8 | quant | Default per_symbol_caps hardcoded {"ES": 20, "NQ": 40, "MES": 200, "MNQ": 400} per ADR-0001 + CLAUDE.md §Standing constraints; ADR-0001 itself does not enumerate the numerics (only "retail-size") | TRACKED — `P1-ADR-0001-NUMERIC-CAPACITY-CAPS-CANONICALIZE` |
| minor | Q-9 | quant | TradeLedgerEntry lacks `cost_in_r` / `cost_model_id` field; the K-1 r_value is documented as "post-K-1-floor + post-cost" but the dataclass cannot represent per-trade slippage | TRACKED — `P1-TRADE-LEDGER-COST-FIELDS` |
| minor | Q-10 | quant | K-6/K-7 tests use weak existence assertions (`assert 3 in v and 4 in v`) instead of exact-match. Critical Q-1/Q-2 defects shipped green because of this. | REMEDIATED — both tests updated to `assert v == (3, 4)` and `assert v == (6, 7)` exact-match assertions per audit recommendation |
| minor | Q-11 | quant | K-6/K-7 validators don't verify the simulator's session_id-contiguity precondition; out-of-order ledgers would produce undefined behavior | TRACKED — `P1-LEDGER-CONTIGUITY-PRECONDITION-CHECK` |
| minor | R-1 | repro | `import numpy as np` unused | REMEDIATED — removed |

### Round-1 remediation patches applied

1. `KillSwitchSimulationResult` extended with `skipped_trade_indices: tuple[int, ...]`; simulator records the indices of trades skipped due to K-6 or K-7 halt (Q-1+Q-2 fix).
2. `validate_k6_daily_circuit_breaker` + `validate_k7_weekly_circuit_breaker` rewritten to derive violation indices from `sim.skipped_trade_indices` (Q-1+Q-2 fix).
3. `KillSwitchCanaryResult` extended with `per_K_validated: dict[str, bool]` (Q-3 fix).
4. `validate_kill_switches_per_fold` 3-state annotation grammar: pass / fail / partial (Q-3 fix).
5. `validate_k4_per_symbol_position_cap` rewritten as running-position scan (Q-4 fix).
6. K-6/K-7 test assertions strengthened to exact-match (Q-10 fix).
7. K-4 tests: 2 new tests for concurrent-position semantics (`test_k4_fails_on_concurrent_positions_exceeding_running_cap`, `test_k4_passes_when_overlapping_below_running_cap`); 1 renamed (`test_k4_passes_under_cap_running_position`); 1 renamed (`test_k4_fails_above_cap_single_trade`) (Q-4 fix).
8. Test `test_canary_pass_on_clean_strategy` refactored as `test_canary_partial_when_metadata_deferred` to reflect Q-3's 3-state annotation; per_K_validated assertions added.
9. `import numpy as np` removed (R-1 fix).
10. Q-5/Q-6 docstrings updated to note conservatism + bias direction.

29 tests green after remediation; 198 tests green across the full Phase L
+ canary primitive surface (no regressions in calmar, profit-factor,
R-multiple, sizing, risk-of-ruin, ADR-0017 smoke, FM stress test).

## Exit per SKILL.md "Exit check"

Per [SKILL.md §"Loop structure" Round-N step 5](../../../../.claude/skills/audit-remediate-loop/SKILL.md):
> If `findings == []` or only `minor` remain → exit. Otherwise increment N.

After Round-1 remediation:
- All 2 critical findings closed by direct code+test evidence (Q-1, Q-2 fix
  verified by `assert v == (3, 4)` and `assert v == (6, 7)` exact-match
  assertions on the regression suite)
- All 2 major findings closed (Q-3 partial-annotation grammar verified;
  Q-4 running-position semantics verified by 2 new tests)
- 1 minor finding remediated (R-1 unused numpy import)
- 6 minor findings tracked as follow-ups (Q-5, Q-7, Q-8, Q-9, Q-11)
- 2 minor findings remediated inline as docstring notes (Q-6 + parts of Q-5)

No critical or major residual; only minor follow-ups remain → **exit**.

## Cross-references

- ADR-0017 §5 (K-1..K-8 hard kill-switch constraints + numeric defaults): [docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md)
- ADR-0017 §5.2 worked example (K-5 group cap): same file §5.2
- ADR-0001 (retail capacity ceiling; load-bearing for K-4): [docs/decisions/ADR-0001-project-scope.md](../decisions/ADR-0001-project-scope.md)
- ADR-0014 §3.2 row 9 (Methodological-correctness annotations grammar): [docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md](../decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md)
- ADR-0013 §1+§2 (no-gates philosophy): [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- Predecessor audit (A1 = P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE): [audit_trail_2026-05-08_phase-l-failure-mode-stress-test.md](audit_trail_2026-05-08_phase-l-failure-mode-stress-test.md)
- Cycle-4 leak-canary precedent: [src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py)
- Simulator: [src/skie_ninja/backtest/stress_test.py](../../src/skie_ninja/backtest/stress_test.py)

## New follow-ups registered by this audit

- `P1-K3-MARK-TO-MARKET-AWARE-VALIDATOR` (non-blocking polish): refine K-3 to use per-tick mark-to-market for the strict "while in unrealized loss" check; the conservative "any same-direction overlap" approximation may surface false positives on legitimate pyramid-into-winner strategies
- `P1-ADR-0001-NUMERIC-CAPACITY-CAPS-CANONICALIZE` (non-blocking): update ADR-0001 to enumerate the numeric capacity caps explicitly (currently only CLAUDE.md §Standing constraints + H055 §11.1 carry the numbers)
- `P1-TRADE-LEDGER-COST-FIELDS` (non-blocking): extend TradeLedgerEntry with `cost_in_r` / `cost_model_id` fields for cost-aware K-1 cross-validation
- `P1-K2-TOLERANCE-NS-JUSTIFY` (non-blocking polish): add `# justify:` annotation to the K-2 60-second tolerance default
- `P1-LEDGER-CONTIGUITY-PRECONDITION-CHECK` (non-blocking): runtime-assert the simulator's session_id-contiguity precondition at the K-6/K-7 validator entry points

## AI-assistance disclosure

Implementation drafted by Claude Opus 4.7 (claude-opus-4-7) under operator
direction (autonomous Cycles 7-10 + Phase K + Phase L mandate per the user's
2026-05-08 directive). Audit-remediate-loop Round 1 used proper-isolated
parallel dyad (quant-auditor + reproducibility-verifier subagents); literature-
check skipped per audit-task scoping (no new citation claims). Reproducibility
log emission pending H055 walk-forward orchestrator integration. ICMJE
Recommendations (updated Jan 2024): AI is not an author; the operator (GitHub
@s-koirala / pseudonym SKIE) is the responsible author.
