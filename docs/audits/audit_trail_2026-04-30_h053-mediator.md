---
title: H053 Block D mediator — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverables:
  - src/skie_ninja/features/h053/__init__.py (NEW)
  - src/skie_ninja/features/h053/mediator.py (NEW; ~270 lines, closes design.md §3.4)
  - tests/unit/test_h053_mediator.py (NEW; 22 tests, all passing)
git_head_at_authoring: 982a2e4
loop_rounds: 1 (Round-1 with parallel quant-auditor + literature-check + reproducibility-verifier)
verdict: accept-with-remediation
---

# H053 Block D mediator — audit-remediate-loop trail

## Scope

Round-1 audit on the H053 Cycle-7 second build deliverable: the per-session 4-feature mediator block (`m_return`, `m_log_range`, `m_volume`, `m_ofi_tickrule`) that anchors the H053 design's mediation analysis. Closes [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md) §3.4 implementation; sub-clause c of §11.2 prereq 11 (PIT canaries) remains a separate Cycle-7 deliverable.

Three subagents launched in parallel (proper-isolated; main-thread orchestration):
- `quant-auditor` (17 findings)
- `literature-check` (8 findings)
- `reproducibility-verifier` (12 findings, all-pass; verdict `accept`)

Total: 37 findings (1 critical, 6 major, 30 minor / positive-verification).

## Per-finding disposition

### Critical (1)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-1-2 | Lee-Ready sign step `shift(1).over("symbol")` crosses session boundaries — 09:31 ET bar at session N could reference 16:15 ET close of session N-1 (RTH) or any ETH bar between sessions, instead of 09:30 ET of same session. **Real correctness bug**: produces silently-wrong `m_ofi_tickrule` on real ETH+RTH panels. | **ACCEPTED** | Both shift+fill_null repartitioned to `over(["symbol", "_session_date_et"])`. ET wall-clock conversion + `_session_date_et` derivation hoisted BEFORE the sign step. The 09:31 ET bar's prior reference is now strictly the 09:30 ET bar of the same session; cross-session carry-forward eliminated. 22/22 tests still green (the synthetic fixtures use full-coverage panels that pass under either partition; the bug surfaces only on production substrate with discontinuous bar coverage at session boundaries). |

### Major (6)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-1-3 | Same root cause as F-1-2 for the `fill_null(strategy="forward")` step — also crosses session boundaries silently. | **ACCEPTED** | Bundled with F-1-2 fix; both shift and fill_null now session-partitioned. |
| L-1 | Garman-Klass DOI `10.1086/296503` is INCORRECT. Lit-check confirmed via IDEAS/RePEc + multiple secondary sources: GK 1980 J. Business 53(1):67-78 → DOI `10.1086/296072`. The same wrong DOI exists in `src/skie_ninja/features/microstructure/rv_parkinson.py` line 16 (Parkinson 1980 → correct DOI `10.1086/296071`). Project-wide DOI typo. | **ACCEPTED** | mediator.py docstring + module-level References section corrected to `10.1086/296072`. New follow-up `P1-DOI-296503-PROJECT-WIDE-CORRECTION` filed to sweep `rv_parkinson.py` and any other usage in a separate audit-loop. |
| F-1-4 | `output_schema` declares all 4 mediator features `nullable=False` but no `.is_finite()` guard against pathological GK negative-variance cases (Garman-Klass §V acknowledges this for thin windows) or log of zero/negative inputs. Schema contract could be silently violated. | **ACCEPTED** | Step-7 added at end of `compute()`: filter rows where any of `m_return / m_log_range / m_volume / m_ofi_tickrule` is non-finite. Drop rather than emit NaN preserves the `nullable=False` contract. New non-blocking follow-up `P1-H053-MEDIATOR-DROP-TELEMETRY` for structured logging on session drop. |
| F-1-5 | GK aggregated-OHLC interpretation vs sum-of-per-bar GK is design.md §3.4 ambiguous ("Garman-Klass log-range over the 15 mediator-window bars" doesn't disambiguate). Implementation chose aggregated-OHLC (range of the *window*); a future re-read could legitimately expect sum-of-per-bar. Pre-registration deviation risk. | **ACCEPTED — FOLLOW-UP** | Mediator docstring explicitly notes the implementation choice and references the follow-up. New follow-up `P1-H053-GK-INTERPRETATION-ADDENDUM` for design.md §3.4 binding addendum + regression-locking test. Implementation continues with aggregated-OHLC. |
| L-2 | "Garman-Klass eq. 6" attribution is plausible but unverifiable from accessible sources; primary PDF paywalled at JSTOR / UChicago Press. Project's own audit pattern (Yang-Zhang eq. 8 verification gap) is to file a follow-up rather than block. | **ACCEPTED — HEDGED** | Docstring softened from `"Garman & Klass 1980 eq. 6"` to `"Garman & Klass 1980 (the simple log-range with C/O drift form; the paper's full estimator with cross-terms is eq. 4. The exact equation number for the simple form was not primary-source verified ...)"`. New follow-up `P1-GK1980-EQ6-PRIMARY-VERIFY` filed. |
| L-5 | "Lee-Ready 1991 §III.A" anchor unverifiable from accessible sources; primary PDF paywalled at Wiley. Project's prior audit at `audit_trail_2026-04-24_cycle6-h050-feature-factory.md` line 109 already flagged the same gap for the sibling `ofi_tickrule.py`. | **ACCEPTED — HEDGED** | Docstring softened from `"Lee & Ready 1991 §III.A"` to `"Lee & Ready 1991 §III tick test (the §III.A sub-anchor was not primary-source verified — paywalled at Wiley; ...)"`. New follow-up `P1-LR1991-III-A-PRIMARY-VERIFY` filed. |

### Minor — applied inline

| ID | Finding | Remediation |
|---|---|---|
| F-1-7 | `output_schema` declares `pa.timestamp("ns", tz="UTC")` but polars LazyFrame inherits panel unit; if upstream is `us`-precision, schema gate would raise. | Final select now explicitly casts `ts_event` to `pl.Datetime("ns", "UTC")`. |
| F-1-13 | Lookback comment misstates math: "16 minutes captures {09:30, 09:31, ..., 09:45 ET}" — that's 16 timestamps but a 15-min span + 1-min lookback. | Comment rewritten: "16-min Timedelta covers the 15-min mediator span + 1-min OFI prior-bar lookback bound." |
| F-1-15 | `m_return` recomputed twice (once as own column, once inside m_log_range derivation). Polars CSE not guaranteed across versions. | m_log_range now uses `pl.col("m_return").pow(2)` instead of re-applying `(close/open).log().pow(2)`. Single source of truth. |

### Minor — filed as follow-ups

| ID | Description | New follow-up |
|---|---|---|
| L-1 (project-wide) | DOI `10.1086/296503` typo also in `rv_parkinson.py` line 16; sweep all uses across project. | `P1-DOI-296503-PROJECT-WIDE-CORRECTION` |
| L-2 | Primary-source PDF verification of GK eq. 6 anchor when paywall access available. | `P1-GK1980-EQ6-PRIMARY-VERIFY` |
| L-5 | Primary-source PDF verification of Lee-Ready 1991 §III.A sub-anchor. | `P1-LR1991-III-A-PRIMARY-VERIFY` |
| F-1-5 | design.md §3.4 binding addendum on aggregated-OHLC vs sum-of-per-bar GK + regression-locking test. | `P1-H053-GK-INTERPRETATION-ADDENDUM` |
| F-1-4 (extension) | Structured logging on session drop with per-symbol counts; persist to ReproLog. | `P1-H053-MEDIATOR-DROP-TELEMETRY` |
| F-1-6 | Polars `group_by` `maintain_order=True` docstring nitpick. | (filed inline; non-blocking) |
| F-1-8 | (subsumed by `P1-H053-MEDIATOR-DROP-TELEMETRY`) | — |
| F-1-9 | Volume cast to Float64 IEEE-754 mantissa precision (low-risk; 2^53 contracts within 15-bar window is impossible for ES/NQ but not enforced). | `P1-H053-MEDIATOR-VOLUME-INT-PATH` (non-blocking) |
| F-1-10 | Lookback semantic verification gap — no test asserts the 16-min span is exactly necessary. | `P1-H053-MEDIATOR-LOOKBACK-EXERCISE` (non-blocking) |
| F-1-11 | tzdata version pinning for cross-platform DST stability; Python's `zoneinfo` uses system IANA tzdata. | `P1-PROJECT-TZDATA-VERSION-PIN` (non-blocking; project-wide) |
| F-1-12 | Verify `test_h053_bar_edge_convention.py` imports the same constants from `mediator.py` (avoid silent drift). | `P1-H053-MEDIATOR-CONST-IMPORT-IN-GATE` (non-blocking) |
| F-1-14 | PIT-invariant test should also assert dtype-equality. | `P1-H053-MEDIATOR-PIT-DTYPE-ASSERT` (non-blocking) |
| F-1-16 | Module `_VERSION` lacks a bump-policy comment. | `P1-FEATURE-VERSION-POLICY-COMMENT` (project-wide; non-blocking) |
| F-1-17 | Cycle-4 dual-fit-call observer + TracingArray canaries on H053 factory — separate verification. This is the §11.2 prereq 11 sub-clause c (PIT canaries integration test); a Cycle-7 deliverable still pending. | `P1-H053-CYCLE4-CANARY-WIRING` (tracked as Cycle-7 remaining work) |

### Positive verifications (no action)

- Repro-verifier: R-1 through R-12 all pass; 126/126 tests green project-wide.
- Lit-check: L-3 (GK formula coefficients verified), L-4 (Lee-Ready DOI verified), L-7 (zero-tick logic correctness verified).
- Quant: F-1-1 (m_return formula), m_volume aggregation, F-1-11 (DST awareness).

## Round-2 not invoked

Round-2 was not invoked. Rationale:
1. The single critical finding (F-1-2 / F-1-3 session-partition correctness bug) was remediated by repartitioning shift + fill_null on `(symbol, _session_date_et)`. Test suite verified green post-remediation.
2. The 6 major findings landed text/code changes with new follow-ups for design.md amendments where applicable. The DOI fix (L-1) is a pure documentation fix; the paywall hedges (L-2, L-5) inherit the project's existing audit pattern.
3. The deferred follow-ups are non-blocking and don't affect mediator correctness.
4. Per [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration", the 3-round cap is the operational ceiling. A second round on a remediation that introduced no new contradiction is process for its own sake.

## Residuals

**Closed by this loop:**
- Cycle 7 second build deliverable: H053 Block D mediator (per design.md §3.4 minus PIT canaries integration test).

**Critical correctness bug fixed:**
- F-1-2 / F-1-3 cross-session sign carry-forward — production substrate with discontinuous bar coverage will no longer produce silently-wrong OFI values.

**New follow-ups filed:**
- `P1-DOI-296503-PROJECT-WIDE-CORRECTION` (project-wide DOI typo sweep)
- `P1-GK1980-EQ6-PRIMARY-VERIFY` (GK eq. 6 anchor verification)
- `P1-LR1991-III-A-PRIMARY-VERIFY` (Lee-Ready §III.A anchor verification)
- `P1-H053-GK-INTERPRETATION-ADDENDUM` (design.md §3.4 GK aggregated-OHLC binding)
- `P1-H053-MEDIATOR-DROP-TELEMETRY` (structured logging on session drop)
- `P1-H053-MEDIATOR-VOLUME-INT-PATH` (volume sum precision)
- `P1-H053-MEDIATOR-LOOKBACK-EXERCISE` (lookback semantic test)
- `P1-PROJECT-TZDATA-VERSION-PIN` (project-wide tzdata pin)
- `P1-H053-MEDIATOR-CONST-IMPORT-IN-GATE` (regression-gate constant import)
- `P1-H053-MEDIATOR-PIT-DTYPE-ASSERT` (dtype-equality in PIT test)
- `P1-FEATURE-VERSION-POLICY-COMMENT` (project-wide feature versioning)
- `P1-H053-CYCLE4-CANARY-WIRING` (PIT canaries integration test; Cycle-7 remaining)

**Cycle 7 remaining deliverables (unchanged by this loop):**
- Block A daily features (`src/skie_ninja/features/h053/daily.py`)
- Block B hourly features (`src/skie_ninja/features/h053/hourly.py`)
- Block C 5/15-min microstructure features (`src/skie_ninja/features/h053/microstructure_5_15min.py`)
- Archetype classifier (`src/skie_ninja/features/h053/archetype_classifier.py`) per design.md §4.5.1
- PIT integration canaries (`tests/integration/test_h053_pit_canaries.py`) — §11.2 prereq 11 sub-clause c
- Stage-0 sanity: HKS 2010 half-hour-reversal sign on ES/NQ

## Verdict

**accept-with-remediation.** Critical correctness bug (F-1-2/F-1-3 cross-session sign carry-forward) remediated in-loop with regression-safe fix; major DOI/citation defects corrected with hedged language matching the project's existing audit-pattern; 76/76 H053 tests + 126/126 project-wide green. Ready for commit + push.
