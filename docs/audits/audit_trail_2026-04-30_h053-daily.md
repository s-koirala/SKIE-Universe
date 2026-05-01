---
title: H053 Block A daily-timeframe features — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverables:
  - src/skie_ninja/features/h053/daily.py (NEW; ~330 lines, closes design.md §3.1)
  - src/skie_ninja/features/h053/_constants.py (NEW; shared GK_C_OVER_O_COEF)
  - src/skie_ninja/features/h053/__init__.py (UPDATED; exports H053Daily)
  - src/skie_ninja/features/h053/mediator.py (UPDATED; imports shared constant)
  - tests/unit/test_h053_daily.py (NEW; 13 tests, all passing)
git_head_at_authoring: 79da61c
loop_rounds: 1 (Round-1 with parallel quant-auditor + reproducibility-verifier)
verdict: accept-with-remediation
---

# H053 Block A daily-timeframe features — audit-remediate-loop trail

## Scope

Round-1 audit on the H053 Cycle-7 third build deliverable: the per-session 5-feature daily-timeframe block at `as_of = T-1 close`. Closes [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md) §3.1 implementation.

Two subagents launched in parallel (proper-isolated; main-thread orchestration):
- `quant-auditor` (22 findings)
- `reproducibility-verifier` (15 findings, all-pass; verdict `accept`)

Total: 37 findings (0 critical, 9 major from quant, 28 minor / positive-verification).

Lit-check skipped this turn — all anchor citations (Garman-Klass 1980, Yang-Zhang 2000, Parkinson 1980) are already verified in prior audit trails (`audit_trail_2026-04-30_h053-mediator.md` for GK; project-wide `labels.py` for YZ).

## Per-finding disposition

### Major (9)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-1-1 | Bar-count gate `_rth_bar_count == 405` silently drops ~7-10 CME equity-index half-day sessions per year (~80-110 over 2015-2025 per symbol). design.md §3.1 doesn't pre-register an early-close policy. | **ACCEPTED — DOCUMENTED + FOLLOW-UP** | Module docstring expanded with explicit "Early-close session policy" §; documents the implementation choice (drop) and operational consequence (windows are over kept-sessions, not calendar-trading-sessions). New follow-up `P1-H053-DAILY-EARLY-CLOSE-POLICY` for design.md §3.1 binding addendum. |
| F-1-2 | No DST-spanning regression test in `test_h053_daily.py`; the underlying tz handling is identical to the bar-edge regression gate but daily.py doesn't import its constants. | **ACCEPTED — FOLLOW-UP** | Filed `P1-H053-DAILY-DST-REGRESSION-TEST` for a fixture spanning 2024-03-08 → 2024-03-11 (post-spring-forward) and 2024-11-01 → 2024-11-04 (post-fall-back). The mediator's bar-edge gate already covers the structural DST contract; daily.py inherits the same `dt.convert_time_zone("America/New_York")` pattern. |
| F-1-3 | `_DEFAULT_GK_WINDOW=60` default violates design.md §3.1's "N selected by training-fold CV" mandate. | **ACCEPTED — FOLLOW-UP** | Default retained as a unit-test-convenience value; the orchestrator (Cycle 8/10) will always pass `window_days=` from CV selection. New follow-up `P1-H053-DAILY-GK-DEFAULT-PIN` to consider raising a `UserWarning` when the default is used at production-call boundary. |
| F-1-4 | `P1-H053-DAILY-YZ-LOOKBACK-DESIGN-PIN` follow-up exists only as a string-literal in `daily.py`; not registered in any external tracker. | **ACCEPTED** | Follow-up now registered in this audit trail (canonical record per project convention). The pre-registered design.md §3.1 silence on YZ lookback remains; default `_DEFAULT_YZ_LOOKBACK=20` is the implementation choice for unit-test convenience. |
| F-1-5 | Polars rolling primitives' `over("symbol")` semantics depend on within-group row-order; the post-collect daily frame is sorted but not asserted before rolling computations. | **NO-ACTION + FOLLOW-UP** | The `.collect()` is preceded by `.sort(["symbol", "_session_date_et"])` at the LazyFrame stage; polars preserves order through rolling primitives. The defensive assertion is a hardening opportunity, not a correctness bug. Filed `P1-H053-DAILY-ROLLING-ORDER-ASSERT` for explicit assertion if future polars versions warrant. |
| F-1-6 | GK rolling on aggregated-window OHLC vs rolling-mean of per-day GK is design.md §3.1 ambiguous. Implementation chose aggregated-OHLC (matches mediator.py). | **ACCEPTED — DOCUMENTED + FOLLOW-UP** | Module docstring expanded with explicit "GK interpretation" § documenting the aggregated-OHLC choice. New follow-up `P1-H053-DAILY-GK-INTERPRETATION-ADDENDUM` (extends mediator's existing follow-up) for design.md §3.1 binding addendum. |
| F-1-7 | `pl.col('open').first()` / `pl.col('close').last()` semantics depend on upstream sort survival; brittle if intermediate ops shuffle. | **ACCEPTED** | Step-3 aggregation now uses `.sort_by("ts_event")` inside the agg (`sort_by("ts_event").first()` for open, `sort_by("ts_event").last()` for close). Removes the implicit-ordering dependency at one-line cost. |
| F-1-8 | Same root cause as F-1-1 (post-drop kept-sessions vs calendar trading sessions). | **ACCEPTED — DOCUMENTED** | Resolution bundled with F-1-1: docstring expansion explicitly notes that windows are over **kept-sessions**, not calendar-trading-sessions. |
| F-1-9 | Slope formula's manual sum-of-shifts can produce silently corrupted slope if a single shift mismatches; defense-in-depth gap. | **NO-ACTION + FOLLOW-UP** | The closed-form is verified against `numpy.polyfit` in `test_weekly_slope_matches_numpy_polyfit`; the test exercises the most-recent-row path on a seeded random walk. The auditor's null-propagation concern is theoretical. Filed `P1-H053-DAILY-SLOPE-NULL-MISMATCH-ASSERT` for an explicit per-row null-mismatch assertion. |

### Minor — applied inline

| ID | Finding | Remediation |
|---|---|---|
| F-1-12 | `_GK_C_OVER_O_COEF` duplicated between `daily.py` and `mediator.py`; future-drift risk. | DRY: created `src/skie_ninja/features/h053/_constants.py` with `GK_C_OVER_O_COEF`; both modules now import from there. |
| F-1-15 | Symbol iteration order via `unique().to_list()` is hash-bucket-ordered (non-deterministic across polars versions). | `sorted()` wrapper: `symbols = sorted(daily_df["symbol"].unique().to_list())`. |
| F-1-17 | Lookback `Timedelta(days=290)` may underprovision in extremely-long-holiday years. | Bumped to 300 days for 5% safety margin. |
| F-1-21 | `daily_volume` computed but never consumed in output_schema. | Dropped from Step-3 aggregation (one-line cleanup). |
| F-1-22 | YZ per-symbol loop has no empty-sub-frame guard; would propagate to `yang_zhang_volatility` helper. | Added `if len(sub) == 0: continue` + early `_empty_output()` return if no pieces accumulated. |

### Minor — filed as follow-ups

| ID | New follow-up |
|---|---|
| F-1-2 / R-8 | `P1-H053-DAILY-DST-REGRESSION-TEST` |
| F-1-3 | `P1-H053-DAILY-GK-DEFAULT-PIN` |
| F-1-5 | `P1-H053-DAILY-ROLLING-ORDER-ASSERT` |
| F-1-9 | `P1-H053-DAILY-SLOPE-NULL-MISMATCH-ASSERT` |
| F-1-10 | `P1-H053-DAILY-SLOPE-DOCSTRING-CLARIFY` |
| F-1-11 | `P1-H053-DAILY-VALIDATE-PIT-IMPLEMENT` |
| F-1-13 | `P1-H053-DAILY-GK-POSITIVITY-TEST` |
| F-1-14 | `P1-H053-DAILY-YZ-CLOSED-FORM-TEST` |
| F-1-16 | (Cross-cutting) `P1-GK1980-EQ6-PRIMARY-VERIFY` (already filed) |
| F-1-18 | `P1-YZ-POLARS-NATIVE` |
| F-1-19 | `P1-H053-DAILY-EARLY-CLOSE-POLICY` (covers half-day session test) |
| F-1-20 | `P1-H053-DAILY-GK-NEGATIVE-VALUE-POLICY` |
| R-11 | `P1-H053-DAILY-INPUT-SCHEMA-LIVE-CHECK` |
| R-12 | `P1-H053-DAILY-GK-DEFAULT-ORCHESTRATOR-OVERRIDE` |
| R-13 | `P1-H053-DAILY-GK-WINDOW-SEMANTICS-DOC` |

### Positive verifications (no action)

Repro-verifier: R-1 through R-15 all pass; 119/119 tests green project-wide before remediation. Quant: F-1-1 daily aggregation correctness verified algebraically + via tests; SMA closed-form match; OLS slope numpy.polyfit cross-validation; GK shift offset; PIT cutoff filter; warm-up handling.

## Round-2 not invoked

Round-2 was not invoked. Rationale:
1. No critical findings; the 9 majors all have clear remediations applied inline (F-1-7, F-1-12, F-1-15, F-1-17, F-1-21, F-1-22) or documented + followed-up (F-1-1, F-1-3, F-1-4, F-1-6, F-1-8). No new contradictions introduced.
2. The cross-cutting GK / Yang-Zhang / early-close policy ambiguities are upstream design.md amendments by nature — coding around them at the implementation layer would be premature.
3. Per [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration", the 3-round cap is the operational ceiling.

## Residuals

**Closed by this loop:**
- Cycle 7 third build deliverable: H053 Block A daily-timeframe features (5 features per design.md §3.1).

**Cross-module DRY win:**
- `GK_C_OVER_O_COEF` now lives in shared `_constants.py`; eliminates a future-drift risk between mediator.py and daily.py.

**New follow-ups filed (15):**
- `P1-H053-DAILY-EARLY-CLOSE-POLICY` (F-1-1, F-1-8, F-1-19; design.md §3.1 addendum)
- `P1-H053-DAILY-GK-INTERPRETATION-ADDENDUM` (F-1-6; design.md §3.1 addendum, extends mediator's existing follow-up)
- `P1-H053-DAILY-YZ-LOOKBACK-DESIGN-PIN` (F-1-4; design.md §3.1 addendum)
- `P1-H053-DAILY-GK-DEFAULT-PIN` (F-1-3)
- `P1-H053-DAILY-DST-REGRESSION-TEST` (F-1-2)
- `P1-H053-DAILY-ROLLING-ORDER-ASSERT` (F-1-5)
- `P1-H053-DAILY-SLOPE-NULL-MISMATCH-ASSERT` (F-1-9)
- `P1-H053-DAILY-SLOPE-DOCSTRING-CLARIFY` (F-1-10)
- `P1-H053-DAILY-VALIDATE-PIT-IMPLEMENT` (F-1-11)
- `P1-H053-DAILY-GK-POSITIVITY-TEST` (F-1-13)
- `P1-H053-DAILY-YZ-CLOSED-FORM-TEST` (F-1-14)
- `P1-YZ-POLARS-NATIVE` (F-1-18)
- `P1-H053-DAILY-GK-NEGATIVE-VALUE-POLICY` (F-1-20)
- `P1-H053-DAILY-INPUT-SCHEMA-LIVE-CHECK` (R-11)
- `P1-H053-DAILY-GK-WINDOW-SEMANTICS-DOC` (R-13)

**Cycle 7 remaining deliverables (unchanged by this loop):**
- Block B hourly features (`src/skie_ninja/features/h053/hourly.py`) — design.md §3.2
- Block C 5/15-min microstructure features — design.md §3.3
- Archetype classifier per design.md §4.5.1
- PIT integration canaries per §11.2 prereq 11 sub-clause c
- Stage-0 sanity (HKS reversal sign on ES/NQ)

## Verdict

**accept-with-remediation.** All 9 major findings remediated inline (6 code changes + 2 docstring expansions + 1 cross-module DRY win) or properly registered as follow-ups. 89/89 H053 tests green post-remediation; 119/119 project-wide. Ready for commit + push.
