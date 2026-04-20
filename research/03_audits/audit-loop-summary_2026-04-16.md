---
name: Audit-remediate-loop summary 2026-04-16
description: Phase-0 + Phase-1 data pipeline audit across two full audit-remediate loops
type: project
date: 2026-04-16
---

# Audit-Remediate Loop Summary — 2026-04-16

## Scope

Two independent audit-remediate loops executed in a single session:

1. **Phase-0 foundation** (P0-1 through P0-12): 3-round loop, final verdict **pass**.
2. **Phase-1 data pipelines** (ingest registry, FOMC, macro surprise, validation, provenance, CLI): 3-round loop, final verdict **pass**.

## Phase-0 loop

### Round 2 — quant audit
- 20 findings: 1 critical (F-2-1 NT8 timezone bug), 13 major, 6 minor.
- Key issues: `ReproLog` schema drift (extra field), byte-identity test gap, paths grep-guard scope, clock half-day citation gap, instruments magic numbers, runcontext non-atomic writes, pickle nondeterminism, pre-commit hook weaknesses.

### Round 2 — remediation (6 parallel agents)
- All 20 findings addressed. F-2-14 (ADR-0002 measurement) and F-2-15 (NT8 compile) deferred as user-hardware-gated.

### Round 3 — verification
- 18/20 closed. 2 user-hardware-gated items accepted as residual per plan P0-10.
- No new critical/major findings.
- Verdict: **pass**.

## Phase-1 loop

### Round 1 — quant audit
- 11 findings: 2 critical (F-1-1 ET→UTC fixed offset, F-1-2 fomc_text not self-registering), 6 major, 3 minor.
- Key issues: DST-incorrect release timestamps creating look-ahead risk, missing SHA256 idempotency, incomplete two-phase commit, missing vendor in provenance, self-comparison in distribution check, no EsTick schema stub.

### Round 2 — remediation
- All 11 findings addressed in single agent.

### Round 3 — verification
- 11/11 round-1 findings closed.
- 2 new findings: F-3-1 (distribution self-comparison), F-3-2 (timezone inconsistency between pipelines).
- Both fixed directly (ingest.py prior-snapshot reference, fomc_text tz-aware UTC).
- Verdict: **pass** (after inline fixes).

## CME calendar correction (discovered during test execution)

The hand-coded holiday fallback table in `clock.py` over-counted full closures. CME equity-index futures are fully closed only on New Year's Day and Christmas. Most federal holidays (MLK, Presidents Day, Good Friday, Memorial Day, Juneteenth, July 4, Labor Day, Thanksgiving) are early-close trading days at 12:00 CT (Good Friday at 08:15 CT). Corrected against `pandas_market_calendars` CME_Equity calendar with cross-check test.

## Dependency changes

- `tick>=0.7` moved to `[project.optional-dependencies].phase2` (no cp311 wheel).
- Added: `beautifulsoup4>=4.12`, `lxml>=5.2`, `pandas-market-calendars>=4.4`, `pandera[polars]>=0.20`.
- Integration test marker added to pytest config.

## Test counts

| Stage | Tests |
|---|---|
| Post Phase-0 implementation | 122 |
| Post Phase-0 remediation | 122 |
| Post CME calendar fix | 122 |
| Post Phase-1 implementation | 183 |
| Post Phase-1 remediation | 196 |

## Open items remaining

| Item | Owner | Blocker |
|---|---|---|
| NT8 F5-compile of TrivialSmokeTest.cs | User | NT8 Desktop not installed |
| ADR-0002 latency measurement (10k+ messages) | User | NT8 Desktop not installed |
| `FRED_API_KEY` env var for integration test | User | API key not yet provisioned |
| Databento account for ES/NQ tick ingest | User | Account signup + $125 credit |
| O-11 empirical justification of magic numbers | Phase 1 | Per plan open items table |
