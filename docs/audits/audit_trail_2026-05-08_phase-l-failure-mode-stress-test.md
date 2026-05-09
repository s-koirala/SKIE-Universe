---
deliverables:
  - src/skie_ninja/backtest/stress_test.py
  - tests/unit/test_stress_test_failure_modes.py
  - scripts/stress_test_failure_modes.py
audit_pattern: parallel_proper_isolated_triad
auditors_round_1:
  - quant-auditor (agentId a8ff1473b04e957c8; verdict block; 11 findings: 2 critical + 6 major + 3 minor)
  - literature-check (agentId aa0795fcceb287e5b; verdict proceed-with-remediation; 7 findings: 0 critical + 2 major + 5 minor)
  - reproducibility-verifier (agentId a433d9ffe63ca7c19; verdict proceed-with-remediation; 5 findings: 0 critical + 1 major + 4 minor)
auditors_round_2:
  - quant-auditor (agentId a9f7c779ab910b664; verdict accept; 0 new findings; all Round-1 critical/major closed)
  - reproducibility-verifier (agentId a56fc4b3465d8b58f; verdict accept; 0 new findings; standard 10-check battery passes)
parent_directive: P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE (BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §6); H055 §11.2 BLOCKING-BEFORE-LAUNCH precondition
predecessor_audit: docs/audits/audit_trail_2026-05-09_phase-l-sizing-risk-of-ruin.md (Phase L commit-2 closure of P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE + P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE)
status: accept (closed Round-2)
---

# Audit trail — Phase L failure-mode stress test primitive (2026-05-08)

## Context

This audit lands `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` per ADR-0017 §6, the
sixth of seven BLOCKING-BEFORE-LAUNCH primitives required by H055 §11.2. The
primitive implements 5 synthetic-failure-mode stress tests (FM-1..FM-5) against
the project-wide hard kill-switch constraints K-1..K-8 from ADR-0017 §5.

The implementation lives at [src/skie_ninja/backtest/stress_test.py](../../src/skie_ninja/backtest/stress_test.py)
(simulator + 5 FMs + dataclasses), with comprehensive unit tests at
[tests/unit/test_stress_test_failure_modes.py](../../tests/unit/test_stress_test_failure_modes.py)
(54 tests; all green) and a CLI wrapper at
[scripts/stress_test_failure_modes.py](../../scripts/stress_test_failure_modes.py)
(synthetic + empirical-mode stub).

## Round 0 — production drafting

Initial implementation: simulator with K-1 + K-6 + K-7 kill switches; 5 FM
functions; dataclasses for KillSwitchParams, TradeEvent, StressTestResult,
KillSwitchSimulationResult; CLI with synthetic-baseline mode for sanity-checking.
46 unit tests written; 1 surfaced a substantive K-7 calibration finding
(per-week loss falls just short of -5% threshold under 1% risk budget × 5
trades/week; cumulative damage across multiple weeks compounds beyond 5%
without K-7 ever firing within a single week). Test re-framed to assert this
honestly; new test added for the K-7 firing path with 2% risk budget. Final
Round-0 result: 47/47 green.

CLI smoke test in synthetic mode produced 4/5 passed (FM-1, FM-2, FM-3, FM-4)
and 1/5 failed (FM-5 due to subtle break-severity not crossing K-7 threshold).

## Round 1 — parallel proper-isolated triad audit

Three subagents spawned in parallel (single message, multiple Agent tool uses)
per [SKILL.md §"Auditor selection"](../../../../.claude/skills/audit-remediate-loop/SKILL.md):
quant-auditor, literature-check, reproducibility-verifier. All three proper-
isolated; brief contained the artifact paths, ADR-0017 §5+§6 spec, H055 §11.1
numeric defaults, and the audit-remediate-loop SKILL.md cap discipline.

### Round-1 findings table

| Severity | ID | Auditor | Issue | Disposition |
|---|---|---|---|---|
| critical | Q-1 | quant | FM-2 implements the DEPRECATED K-1-floor-at-session-open pass criterion. ADR-0017 §6 row 2 + F-15 audit remediation require a session-boundary mark-to-market force-close — K-1 is an ATR-stop *during* a held trade, not a session-boundary trigger. RTH-only strategies are exempt by construction (closing parenthetical). | REMEDIATED — new `rth_only_exempt: bool = True` parameter (H055 v1 default; exempts by construction); new `session_boundary_mtm_force_close_R` parameter required when `rth_only_exempt=False`; canonical force-close path implemented |
| critical | Q-2 / L-2 | quant + lit | FM-3 implements the deprecated DISJUNCTIVE pass criterion. ADR-0017 §6 row 3 + F-15 audit remediation reformulated to AND-CONJUNCTION: BOTH (a) news-calendar filter prevents entry AND (b) counterfactual K-1 binds. The prior disjunctive form was trivially satisfiable. | REMEDIATED — new `news_calendar_filter_active: bool = False` parameter; pass requires both conditions; default False reflects primitive-layer scope; `condition_a_orchestrator_coverage_required` reported when path (a) cannot be self-tested |
| major | Q-3 | quant | FM-4 cost-application order under-counts realized cost on K-1-floored losers. Cost was deducted BEFORE the K-1 floor, so a -0.95R + 0.10R cost would clamp at -1R rather than realize -1.05R. Slippage is a real-money cost ABOVE any K-1 stop. | REMEDIATED — simulator gained `post_floor_cost_in_r` parameter applied AFTER K-1 floor; FM-4 routes its cost through this parameter; canonical "stop-loss exit + slippage" model. |
| major | Q-4 | quant | FM-1 vacuous-pass logic too lenient. The prior `passed = k6_fired_post or vacuous` allowed strategies with no K-6 trigger condition to silently pass without exercising the failure-mode test's intent. | REMEDIATED — added no-kill-switch counterfactual (thresholds = -0.999); pass requires K-6 fired AND demonstrably catches damage (kill-switch terminal > no-kill-switch terminal) OR honest vacuous pass with `vacuous_pass=True` annotation |
| major | Q-5 | quant | FM-5 substituted a non-spec `damage_bounded` fallback that was structurally weaker than the spec's "regime-conditioning catches the break". Strategies with strong unconditional edges could trivially pass without exhibiting any regime-conditioning behavior. | REMEDIATED — `damage_bounded` fallback removed; pass = K-7 fired (path b only) at primitive layer; path (a) regime-conditioning explicitly deferred to orchestrator layer per `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` |
| major | Q-6 | quant | FM-1 docstring claimed "preserves total $-loss" but the implementation does NOT (current-equity rebase compounds 4 small losses differently from 1 big loss). | REMEDIATED — docstring reframed to "R-multiple-sum-preserving with O(risk_budget_pct² × cuts) discrepancy in the conservative direction"; test renamed to reflect the actual behavior |
| major | R-1 | repro | `config_path = str(Path(args.config))` produces OS-native path separators, breaking cross-platform `payload_sha256` reproducibility (Windows backslash vs Linux forward slash). | REMEDIATED — CLI uses `config_path.as_posix()`; verified the SHA reproduces across platforms |
| minor | L-3 | lit | 5σ adverse spike docstring lacks temporal-scale clarifier (per-trade σ vs 1-min-bar σ). | REMEDIATED — docstring now states "per-trade scale (σ_per_trade ≈ 0.5R under Turtle 2N)" |
| minor | L-4 | lit | FM-4 docstring claims "(default 0.5 = the ADR-0017 §4.2 ruin threshold)" but ADR-0017 §6 row 4 does NOT numerically pin a survival threshold — the 50% floor is borrowed from §4.2. | REMEDIATED — docstring clarifies "borrows the ADR-0017 §4.2 ruin threshold as the operational quantification" |
| minor | L-5 + L-6 | lit | Faith 2007 cited without `*practitioner*` tag in inline references. | REMEDIATED — added `*practitioner*` + ISBN inline at simulator + CLI argparse help |
| minor | R-3 | repro | `run_all_failure_mode_stress_tests` allows fm_kwargs to contain top-level common keys (starting_equity etc.), causing TypeError collision. | REMEDIATED — added `_RUN_ALL_COMMON_KEYS` validation that raises ValueError on collision; test added |
| minor | R-4 | repro | CLI silently falls back to default kill-switch params when --config points to a non-existent file. Undermines audit-trail discipline. | REMEDIATED — CLI now exits 2 with explicit error message on missing config |

12 minor + 4 deferred findings (validation range loosening, pre_stress_n_trades
field, FM-1 before-week-end check, skie_ninja import path, etc.) tracked but
non-blocking; documented in the auditor JSON outputs and accepted as
non-blocking polish per SKILL.md §"Triage" + the audit-remediate-loop's
3-round cap.

### Round-1 remediation patches applied

1. `simulate_equity_with_kill_switches` gained `post_floor_cost_in_r` parameter
   (Q-3 fix). Cost applied after K-1 clamp.
2. FM-2 reframed with `rth_only_exempt` + `session_boundary_mtm_force_close_R`
   parameters (Q-1 fix). RTH-only is the H055 v1 default; overnight strategies
   must specify the force-close threshold.
3. FM-3 reformulated as AND-conjunction with `news_calendar_filter_active`
   parameter (Q-2/L-2 fix). Pass requires both conditions.
4. FM-1 added no-kill-switch counterfactual + `k6_demonstrably_caught_damage`
   field (Q-4 fix). Vacuous pass honest.
5. FM-5 dropped `damage_bounded` fallback; pass = `k7_fired` (Q-5 fix). Path
   (a) regime-conditioning explicitly orchestrator-deferred.
6. CLI uses `config_path.as_posix()` for cross-platform SHA stability (R-1 fix).
7. CLI fails loud on missing config file (R-4 fix).
8. `run_all_failure_mode_stress_tests` validates fm_kwargs against common-key
   collision (R-3 fix).
9. Docstring reframings (Q-6, L-3, L-4) + `*practitioner*` tags (L-5/L-6).

54 tests green after remediation; 169 tests green across the full Phase L +
new stress test surface (no regressions).

## Round 2 — parallel proper-isolated verification

Two subagents spawned (the literature-check Round-2 step was elided — the
Round-1 lit findings were either remediated by the docstring reframings or
classified non-blocking; no new lit-attribution claims introduced by
remediation patches). Both Round-2 auditors returned `verdict=accept`.

| Auditor | Verdict | Round-1 closures | New findings |
|---|---|---|---|
| quant-auditor (a9f7c779ab910b664) | accept | Q-1, Q-2, Q-3, Q-4, Q-5 all closed by direct evidence | 0 |
| reproducibility-verifier (a56fc4b3465d8b58f) | accept | R-1, R-2, R-3, R-4 all closed; R-5 n/a; standard 10-check battery passes | 0 |

### Standard reproducibility battery (Round-2)

- Identity hygiene: 0 matches across all 4 artifacts (stress_test.py, scripts CLI, tests, H055_smoke.json) for `skoir/.claude` / `C:/Users/skoir` / `~/.claude` patterns
- Non-loss / non-deletion: only ADD operations + 1 stub-replacement; pre-commit guard exits 0
- Frozen pre-reg §1-§7 immutability: H055 design.md unchanged
- Test suite: 54/54 green in 0.11s
- Phase L regression suite: 169/169 green in 0.64s (test_stress_test_failure_modes.py 54 + ADR-0017 smoke 10 + Calmar 21 + profit-factor 20 + R-multiple 24 + sizing 24 + risk-of-ruin 16)
- Imports clean (PYTHONPATH=src)
- CLI runs end-to-end (synthetic mode); exits 0; produces "3/5 passed; failed=[FM-3, FM-5]"
- CLI reproducibility: two consecutive runs byte-equal
- Smoke test SHA reproducibility: embedded `payload_sha256` byte-equals canonical-JSON-SHA recomputation
- Pre-commit non-loss guard: exit 0

The "FM-3 + FM-5 fail" CLI output is the CORRECT post-remediation behavior:
- FM-3 fails because `news_calendar_filter_active=False` by default, requiring
  orchestrator-layer wiring per `P1-H055-NEWS-CALENDAR-INGEST` BLOCKING-BEFORE-
  LAUNCH precondition
- FM-5 fails because synthetic +0.1R-mean trades + -0.5R regime break do not
  accumulate enough cumulative weekly damage to fire K-7; path (a) regime-
  conditioning is orchestrator-deferred

Both failures are honest signals (NOT bugs) — `condition_a_orchestrator_
coverage_required` and `path_a_regime_conditioning_orchestrator_coverage_
required` annotations make this explicit in `fm_specific`.

## Verdict

**Accept** at Round 2. Closed: 12 critical+major+minor Round-1 findings.
Residual: 3 deferred-to-orchestrator paths (FM-2 overnight force-close, FM-3
condition (a), FM-5 path (a)) honestly surfaced via `fm_specific` provenance
fields and tracked under `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` (Phase
L follow-up A2; BLOCKING-BEFORE-LAUNCH per H055 §11.2).

## Cross-references

- ADR-0017 §6 (FM-1..FM-5 + F-15 audit remediation): [docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md)
- ADR-0017 §5 (K-1..K-8 numeric defaults): same file §5
- ADR-0013 §1+§2 (no-gates philosophy; FM-N stress-test annotations are NOT binding gates): [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- ADR-0013 §4.2 (failure_log.md non-loss mandate; `stress-test-FM-N-fail` annotations recorded there)
- H055 §11.2 BLOCKING-BEFORE-LAUNCH precondition list: [research/01_hypothesis_register/H055/design.md](../../research/01_hypothesis_register/H055/design.md) §11.2
- H055 §11.1 numeric K-1..K-8 parameter defaults: same file §11.1
- Phase L predecessor audit (sizing + risk-of-ruin): [docs/audits/audit_trail_2026-05-09_phase-l-sizing-risk-of-ruin.md](audit_trail_2026-05-09_phase-l-sizing-risk-of-ruin.md)

## New follow-ups registered by this audit

- `P1-FM-2-SESSION-BOUNDARY-MTM-KILL-SWITCH` (BLOCKING-BEFORE-FIRST-OVERNIGHT-HOLDING-HYPOTHESIS): wire the session-boundary mark-to-market force-close as a first-class kill switch K-9 in the orchestrator layer for any future hypothesis whose strategy holds positions across a session boundary
- `P1-FM-3-CONJUNCTIVE-CRITERION-ORCHESTRATOR-COVERAGE` (cross-link to A2): condition (a) news-calendar filter integration at orchestrator layer
- `P1-WALK-FORWARD-PER-TRADE-LEDGER-SCHEMA` (BLOCKING-BEFORE-EMPIRICAL-MODE-FIRST-USE): wire per-trade R-multiple ledger emission in the H055 walk-forward orchestrator so the FM stress test's empirical mode can be invoked post-walk-forward
- `P1-FM-1-BEFORE-WEEK-END-CHECK` (non-blocking polish): add explicit "K-6 fires before max(session_id within week_id)" check to FM-1 pass criterion
- `P1-FM-4-SURVIVAL-THRESHOLD-EMPIRICAL` (non-blocking polish): per-hypothesis empirical calibration of the 50% survival floor

## AI-assistance disclosure

Implementation drafted by Claude Opus 4.7 (claude-opus-4-7) under operator
direction (autonomous Cycles 7-10 + Phase K + Phase L mandate per the user's
2026-05-08 directive). Audit-remediate-loop Round 1 + Round 2 used proper-
isolated parallel triad (quant-auditor + literature-check + reproducibility-
verifier subagents). Reproducibility log emission pending the H055 walk-
forward orchestrator integration (`P1-WALK-FORWARD-PER-TRADE-LEDGER-SCHEMA`).
ICMJE Recommendations (updated Jan 2024): AI is not an author; the operator
(GitHub @s-koirala / pseudonym SKIE) is the responsible author.
