---
title: H053 Block B hourly-timeframe features — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverables:
  - src/skie_ninja/features/h053/hourly.py (NEW; ~370 lines, closes design.md §3.2)
  - src/skie_ninja/features/h053/__init__.py (UPDATED; exports H053Hourly)
  - tests/unit/test_h053_hourly.py (NEW; 15 tests, all passing)
git_head_at_authoring: 57d4cdd
loop_rounds: 1 (Round-1 with parallel quant-auditor + reproducibility-verifier)
verdict: accept-with-remediation
---

# H053 Block B hourly-timeframe features — audit-remediate-loop trail

## Scope

Round-1 audit on the H053 Cycle-7 fourth build deliverable: the per-session 27-feature hourly-timeframe block (24 lag features + 3 single-value features) under the §3.0 bar-edge convention with CME maintenance halt (16:00-17:00 CT = 17:00-18:00 ET) handled via forward-fill. Closes design.md §3.2 implementation.

Two subagents launched in parallel (proper-isolated; main-thread orchestration):
- `quant-auditor` (25 findings)
- `reproducibility-verifier` (15 findings, all-pass; verdict `accept`)

Total: 40 findings (0 critical, 5 major from quant, 35 minor / positive-verification).

Lit-check skipped this turn — the only external citation in the module is the §3.0 R5 shorthand convention (already verified across mediator + daily audits) plus implicit CME calendar references (clock.py-anchored).

## Per-finding disposition

### Major (5)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-12 | `lookback = pd.Timedelta(days=5)` may underprovision lag_24 across holiday-extended Monday→Tuesday boundaries (e.g., Memorial Day, Thanksgiving Friday). Worst case: Tuesday-after-holiday's lag_24 references the prior Friday's 09:00 ET = 5 calendar days back, no margin. | **ACCEPTED** | Bumped to 7-day Timedelta with explicit comment citing the holiday-extended-weekend case. Provides 2-day safety margin. |
| F-16 | `_session_date_et` uses calendar date in ET, not CME session date convention (which labels Sunday-evening ETH bars as Monday's session). The distinction is benign for this module because per-session anchor extraction inner-joins on weekday-only RTH/pre-open bars, but the calendar/session distinction is undocumented and fragile. | **ACCEPTED — DOCUMENTED** | Module docstring expanded with explicit "Calendar date vs CME session date" §; documents the calendar-date interpretation and notes that Sunday-evening ETH bars drop out via the weekday-only inner-join. Follow-up `P1-H053-HOURLY-CME-SESSION-DATE-DOC` for explicit design.md binding. |
| F-21 | `compute()` materializes the LazyFrame eagerly via `df_all = lf.collect()` early; the function signature accepts/returns `pl.LazyFrame` but execution is fully eager. The streaming contract is broken. | **ACCEPTED — DOCUMENTED** | Module docstring expanded with explicit "Eager materialization" § documenting the choice (per-symbol Python iteration over `pl.datetime_range` grids requires eager execution; ~190K hourly rows fits in memory). Follow-up `P1-H053-HOURLY-LAZY-REWRITE` for future polars-native rewrite. |
| F-23 | design.md §3.2 is silent on halt-hour forward-fill policy; the module's choice (forward-fill 17:00 ET close to 18:00 ET → halt return = 0) runs ahead of pre-registration. Per CLAUDE.md, methodology choices must be pre-registered. | **ACCEPTED — FOLLOW-UP** | Module docstring §"CME maintenance halt" already documented the policy + the follow-up tag `P1-H053-HOURLY-HALT-POLICY`. This audit adds the follow-up explicitly to the residuals ledger. The `running` status is gated on the design.md §3.2 addendum landing first. |
| F-4 / F-6 | DST regression test gap + Friday→Monday weekend regression test gap. Repro-verifier R-8 verified live that DST handling is correct (`pl.datetime_range` skips non-existent 02:00 ET on spring-forward); behavior is correct but no test regression-locks it. | **ACCEPTED — FOLLOW-UPS** | Filed `P1-H053-HOURLY-DST-REGRESSION-TEST` (spring-forward + fall-back fixtures) and `P1-H053-HOURLY-WEEKEND-REGRESSION-TEST` (Friday→Monday closed-form lag_24). Repro-verifier confirmed behavior is correct at runtime; tests lock that behavior. |

### Minor — applied inline

| ID | Finding | Remediation |
|---|---|---|
| F-18 | Halt-hour test only asserts `lag_16 ≈ 0`; doesn't verify non-halt-adjacent lags (lag_15, lag_17) are positive on monotonic synthetic, leaving a regression gap if the halt policy accidentally affected adjacent lags. | Strengthened test: now asserts lag_15 (post-halt 18:00→19:00 ET t-1) and lag_17 (pre-halt 16:00→17:00 ET t-1) both positive. |

### Minor — filed as follow-ups

| ID | New follow-up |
|---|---|
| F-1 | `P1-H053-VWAP-PRICE-CONVENTION` — design.md §3.2 binding for close vs typical-price VWAP |
| F-2 | `P1-H053-VWAP-RTH-ENDPOINT` — design.md §3.2 binding for cash-equity 16:00 vs futures 16:15 RTH boundary |
| F-3 | `P1-H053-HOURLY-LAG-INDEX-CONVENTION` — design.md §3.2 lag-direction formula binding |
| F-7, F-8, F-9 | `P1-H053-R5-SHORTHAND-SCOPE` — extend §3.0 R5 to bind Block B's `O_{09:30}` and `O_{06:00}` references |
| F-10, F-25 | `P1-H053-DROP-REASON-TELEMETRY` — replace silent `is_finite` filter with structured drop-reason logging |
| F-13 | `P1-H053-HOURLY-FFILL-UPPER-BOUND` — bound forward-fill propagation to the halt-hour count; warn on outage runs |
| F-19, F-20 | `P1-H053-HOURLY-CLOSED-FORM-TESTS` — closed-form regression tests for lag_1, vwap_dev, overnight, pre_open |
| F-22 | `P1-H053-HOURLY-VALIDATE-PIT-IMPLEMENT` — implement validate_point_in_time hook |
| F-23 | `P1-H053-HOURLY-HALT-POLICY` — design.md §3.2 halt-handling addendum |
| F-4 | `P1-H053-HOURLY-DST-REGRESSION-TEST` |
| F-6 | `P1-H053-HOURLY-WEEKEND-REGRESSION-TEST` |
| F-21 | `P1-H053-HOURLY-LAZY-REWRITE` |
| F-16 | `P1-H053-HOURLY-CME-SESSION-DATE-DOC` |

### Positive verifications (no action)

Repro-verifier: R-1 through R-15 all pass; 104/104 H053-suite tests green.
- R-8 live-verified DST handling: `pl.datetime_range` correctly skips the non-existent 02:00 ET on spring-forward (2024-03-10).
- R-12 verified us→ns Datetime cast is lossless and equality-preserving for the panel's date range.
- R-14 verified `_empty_output()` is reachable from 3 distinct guards.

Quant: F-5, F-11, F-14, F-15, F-17, F-24 are minor / informational confirmations.

## Round-2 not invoked

Round-2 was not invoked. Rationale:
1. No critical findings. The 5 majors are: 1 inline-fix (F-12 lookback bump), 2 doc-only (F-16, F-21), and 2 cross-cutting design.md amendments (F-4/F-6 test regressions, F-23 halt policy) — all with clear remediation paths and no new contradictions introduced.
2. Repro-verifier independently verified DST + empty-input + dtype-cast correctness at runtime; no behavioral defects.
3. Per [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration", the 3-round cap is the operational ceiling.

## Residuals

**Closed by this loop:**
- Cycle 7 fourth build deliverable: H053 Block B hourly-timeframe features (27 features per design.md §3.2).

**Cumulative DRY win across Block A + B + D:**
- All 3 modules now share the §3.0 R5 shorthand convention + the project-wide `_pit_cutoff` helper + the GK_C_OVER_O_COEF constant (Block D + A; Block B doesn't compute GK).

**New follow-ups filed (13):**
- `P1-H053-VWAP-PRICE-CONVENTION` (F-1)
- `P1-H053-VWAP-RTH-ENDPOINT` (F-2)
- `P1-H053-HOURLY-LAG-INDEX-CONVENTION` (F-3)
- `P1-H053-R5-SHORTHAND-SCOPE` (F-7/8/9)
- `P1-H053-DROP-REASON-TELEMETRY` (F-10/25)
- `P1-H053-HOURLY-FFILL-UPPER-BOUND` (F-13)
- `P1-H053-HOURLY-CLOSED-FORM-TESTS` (F-19/20)
- `P1-H053-HOURLY-VALIDATE-PIT-IMPLEMENT` (F-22)
- `P1-H053-HOURLY-HALT-POLICY` (F-23) — **blocking for `running` status**
- `P1-H053-HOURLY-DST-REGRESSION-TEST` (F-4)
- `P1-H053-HOURLY-WEEKEND-REGRESSION-TEST` (F-6)
- `P1-H053-HOURLY-LAZY-REWRITE` (F-21)
- `P1-H053-HOURLY-CME-SESSION-DATE-DOC` (F-16)

**Cycle 7 remaining deliverables:**
- Block C 5/15-min microstructure features — design.md §3.3
- Archetype classifier per design.md §4.5.1
- PIT integration canaries per §11.2 prereq 11 sub-clause c
- Stage-0 sanity (HKS reversal sign on ES/NQ; substrate access required)

## Verdict

**accept-with-remediation.** All 5 major findings remediated inline (1 code change + 2 docstring expansions + 1 test strengthening + 1 follow-up registration) or properly registered as follow-ups. 104/104 H053-suite tests green post-remediation; 119/119 project-wide. Ready for commit + push.
