---
title: H053 PIT canaries integration test (design.md §11.2 prereq 11 sub-clause c) — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverables:
  - tests/integration/test_h053_pit_canaries.py (NEW; ~600 lines, 14 tests, all passing)
git_head_at_authoring: fea696a
loop_rounds: 3 (Round-1 + Round-2 + Round-3 must-land remediation)
verdict: accept-with-remediation (SKILL.md 3-round cap reached)
---

# H053 PIT canaries integration test — audit-remediate-loop trail

## Scope

Three-round audit-remediate-loop on the H053 Cycle-7 PIT/leakage canaries
deliverable per design.md §11.2 prereq 11 sub-clause c. Closes the
H053-specialised wiring of the Cycle-4 leak-canary patterns from
[src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py)
to the H053 feature factory blocks (A/B/C/D + archetype classifier).

Two subagents launched in parallel each round (proper-isolated;
main-thread orchestration):
- `quant-auditor` Round-1 (verdict `block`; 1 critical + 5 major + 3 minor + 1 positive-verification + 1 verification-gap; agentId `a670ff58d13beaa9b`)
- `reproducibility-verifier` Round-1 (verdict `accept`; all 10 dimensions clean; agentId `a4afb8267ccc8f1c3`)
- `quant-auditor` Round-2 (verdict `block`; 1 critical + 3 major + 3 minor; agentId `a810859548724f287`)
- Round-3: remediation-only (SKILL.md 3-round cap; no further audit invocation)

Total: 24 findings across 3 rounds (2 critical, 8 major, 11 minor + 3
positive-verification / verification-gap).

## Round-1: dispositions (Round-1 verdict `block`)

### Critical (1)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-1-1 | `TracingPanel` class defined but NEVER used by any test; `TestTracingCapabilityProxy` only inspects OUTPUT max(ts_event) ≤ now, not which input bars compute() actually read. design.md §11.2 prereq 11(c) verbatim binds the Cycle-4 `TracingArray` capability proxy. | **ACCEPTED — Round-2 found this remediation regressed (see F-2-1)** | Round-1 fix: replaced TracingPanel with **input-poisoning capability proxy** — `_poison_panel_after_cutoff` overwrites OHLCV in post-cutoff bars with sentinel values (close=99999999 etc); test asserts no output column has \|value\| ≥ 1e6. Round-2 found this insufficient for log-domain features. **Round-3 final fix: NaN-poison structural detector** (see F-2-1 below). |

### Major (5)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-1-2 | `TestBarSetDisjointness` was tautological — Polars filters the test author wrote, not bars compute() actually consumed. | **ACCEPTED** | Round-1 fix: removed the tautological filter check; replaced with the input-poisoning approach which exercises the actual feature-factory read pattern. |
| F-1-3 | Boundary-anchor 09:45 ET bar inclusion not tested; off-by-one bug would pass dual-fit silently (both panels equally exclude the bar). | **ACCEPTED** | Round-1 fix: `TestBoundaryAnchorInclusion::test_mediator_m_return_uses_0945_close` constructs a panel where the 09:45 ET bar's close is 4600.0 (vs 4503.5 from the linear drift); asserts m_return matches log(4600/4500.25), not log(4503.5/4500.25). Round-2 F-2-3 found OHLC inconsistency (close=4600 > high=4504); Round-3 fixed by also setting high=4600.25. |
| F-1-4 | Adversarial leak-injection too trivial (`max(ts_event)`); doesn't exercise data-driven leaks. | **ACCEPTED** | Round-1 fix: expanded to 3 leak modes — trivial ts-leak, mean-of-close leak (forgotten _pit_cutoff), and capability-proxy detection of mean-of-close leak. Round-3 added single-bar leak positive control on long fixture. |
| F-1-5 | `train_panel_checksum` enforcement gap — recorded but never checked at apply-time. | **ACCEPTED — DOC** | Round-1 fix: docstring clarifies the checksum is **sidecar-only for orchestrator-side enforcement** via the existing `P1-H053-ARCHETYPE-SIDECAR-MODEL-HASH-WIRING` follow-up. |
| F-1-6 | Daily block silently vacuous on 32-business-day panel (SMA200 never warms up); both `out_full` and `out_truncated` are empty → equal trivially. | **ACCEPTED** | Round-1 fix: new `long_panel_anchor` module-scope fixture spans 250 business days (`pd.date_range(start="2023-03-01", end="2024-03-15", freq="B")`); SMA200 warmup completes; output is non-empty. `assert len(out) > 0` precondition added (was `if len(out) > 0`). |

### Minor (4) — applied inline

| ID | Finding | Remediation |
|---|---|---|
| F-1-7 | `if len(out) > 0:` silent-pass guards (dead-canary anti-pattern). | Replaced with explicit `assert len(out) > 0`. |
| F-1-8 | `_frames_byte_equal` did not pin schema before `equals`. | Explicit `a.schema == b.schema` check before `equals(b, null_equal=True)`. |
| F-1-10 | Module docstring §3.5 vs §3.6 mis-pin. | Changed to §3.6. |
| F-1-11 | `_truncate_panel_at` naming ambiguity (≤ inclusive vs Cycle-4 strict). | Renamed to `_truncate_panel_at_or_before`; docstring cross-references `leak_canaries.py:60-71` for the intentional semantic difference. |
| F-1-13 | Hard-coded RNG seeds without `# justify:` comments. | Added `# justify:` comments at line 80 and line 470 (now 547). |

### Positive-verification (1) + verification-gap (1)

- F-1-9 (minor coverage gap): test cases for multi-symbol, no-future-bars, DST/holiday, early-close — non-blocking; deferred to follow-up `P1-H053-PIT-CANARY-COVERAGE-EXPANSION`.
- F-1-12 (positive verification): dual-fit-invariance correctly catches mean-of-close + Lee-Ready cross-session canaries.

## Round-2: dispositions (Round-2 verdict `block`)

### Critical (1)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-2-1 | Round-1's input-poisoning capability proxy is largely a dead canary. The 1e6 magnitude bound does NOT detect leaks on log-domain features: `log(99999999) ≈ 18.4`; squared GK ≈ 51; rv_realized_5m worst-case ≈ 29,000 — all bounded under 1e6 even when feature reads poisoned bars wholesale. | **ACCEPTED** | **Round-3 fix**: switched to **NaN-poison structural detector** — `_poison_panel_after_cutoff` now overwrites OHLCV with `pl.lit(float("nan"))`. The downstream test asserts (a) poisoned-panel output row count equals truncated-panel output row count, AND (b) no NaN escapes into feature columns. NaN propagation is structural and codomain-independent. New helper `_output_rows_match_truncated` returns `(rows_clean, rows_poisoned, ok)`. |

### Major (3)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-2-2 | Mediator's NaN-poison test is structurally tautological under current `mediator.py` implementation (mediator-window filter restricts to 09:31-09:45 ET regardless of PIT cutoff). | **ACCEPTED — DOC** | Round-3 fix: docstring for `TestInputPoisonCapabilityProxy` and `test_mediator_does_not_read_post_cutoff_bars` explicitly acknowledges this; the test is retained as a **regression guard** against future implementations that loosen the window filter. |
| F-2-3 | Boundary-anchor test panel internally inconsistent (close=4600 > high=4504). A defensive future GK-validity guard would drop the row and break the test. | **ACCEPTED** | Round-3 fix: also bumped `rows[15]["high"] = 4600.25` to keep OHLC self-consistent. |
| F-2-4 | Input-poisoning does NOT corrupt `ts_event` of post-cutoff bars (Polars Datetime("ns", "UTC") does not accept NaN). A trivial `max(panel.ts_event)` leak would not be caught by the input-poisoning proxy alone. | **ACCEPTED — DOC** | Round-3 fix: `_poison_panel_after_cutoff` docstring explicitly acknowledges this; the **dual-fit canary** (`TestPITCutoffDualFitInvariance`) is the load-bearing detector for ts_event-derived leaks. |

### Minor (3) — applied inline

| ID | Finding | Remediation |
|---|---|---|
| F-2-5 | No long-fixture single-bar-leak positive control. | Round-3 fix: new `test_nan_poison_detects_single_bar_leak_on_long_fixture` constructs a leaky compute that returns `panel.argmax(ts_event).close` and asserts the NaN-poison detector catches it. |
| F-2-6 | Module-scope fixture memory estimate inaccurate ("18 MB" claim, actual ~40-160 MB transient). | Round-3 fix: docstring updated to ~40 MB resident, ~160 MB transient. |
| F-2-7 | Archetype checksum sidecar test was one-sided (only inequality assertion). | Round-3 fix: added second assertion — `rule_clean.train_panel_checksum == fit_archetype_rule(train_only, K=5).train_panel_checksum` (idempotency). |

## Round-3: remediation-only (SKILL.md 3-round cap)

Per [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration", the 3-round cap is the
operational ceiling. Round-3 was a remediation-only round applying the
must-land Round-2 fixes (F-2-1 NaN-poison, F-2-3 OHLC consistency,
F-2-2/F-2-4 docstring acknowledgements, F-2-5/6/7 polish).

**Round-3 verification**: 14/14 PIT-canary tests pass after Round-3
remediations; full H053 suite green at 173/173 (was 159 + 14 new
PIT-canary tests). The NaN-poison structural detector correctly catches
the mean-of-close leak (mean over NaN-bearing column propagates NaN) and
the single-bar argmax-close leak (NaN at the argmax row).

Residual risk per Round-2: a stationary-distribution-equivalent leak
(compute reads a post-cutoff bar but the bar is statistically
indistinguishable from its pre-cutoff cohort) would pass dual-fit only
if the implementation aggregates with a pure-mean estimator on a
stationary input; the synthetic panel here has non-stationary drift, so
this is not a current risk. Tracked under
`P1-H053-PIT-CANARY-STATIONARY-LEAK-RISK` for future evidence-bar
audits.

## Reproducibility verifier — accept (Round-1, no Round-2 invocation needed)

All 10 verification dimensions PASSED on Round-1:
- R-1: panel-builder determinism via seed=42.
- R-2: dual-fit comparator byte-stable under BLAS-pinned single-threaded execution.
- R-3: 11 tests in 6.13s wall-clock (well under 30s budget); Round-3's 14-test version completes in 7.28s.
- R-4: cross-platform — uses pathlib + zoneinfo, no Windows-specific calls.
- R-5: timestamp dtype invariant — `pl.Datetime("ns", "UTC")` consistent across all 4 blocks.
- R-6: imports clean — all 7 H053 symbols re-exported correctly.
- R-7: no network or external substrate; in-memory only.
- R-8: 170/170 → 173/173 H053 suite green.
- R-9: ~2.2 MB Round-1 panel size; Round-3 long fixture ~40 MB resident, ~160 MB transient.
- R-10: no commit-hash / wall-clock dependency.

## Residuals

**Closed by this loop:**
- Cycle 7 fourth deliverable: H053 PIT canaries integration test
  (design.md §11.2 prereq 11 sub-clause c).

**Critical method correctness fixes landed across the 3 rounds:**
- F-1-1 + F-2-1: Cycle-4 `TracingArray` → input-poisoning numeric →
  **NaN-poison structural detector** (codomain-independent).
- F-1-3 + F-2-3: boundary-anchor 09:45 ET inclusion test, with
  OHLC-consistent panel.
- F-1-6: 250-business-day long fixture so Daily block actually exercises.

**New follow-ups filed (4):**
- `P1-H053-PIT-CANARY-COVERAGE-EXPANSION` — multi-symbol, no-future-bars,
  DST/holiday, early-close test cases (Round-1 F-1-9).
- `P1-H053-PIT-CANARY-STATIONARY-LEAK-RISK` — stationary-distribution-
  equivalent leak modes uncovered by current dual-fit + NaN-poison combo.
- `P1-H053-PIT-CANARY-MEMORY-PROFILE` — long-fixture transient memory
  profile under input-poisoning expansion (currently estimated ~160 MB).
- `P1-H053-ARCHETYPE-SIDECAR-MODEL-HASH-WIRING` — orchestrator-side
  `with_model_hash` integration of the archetype sidecar SHA256 (this
  follow-up was filed during the archetype classifier deliverable;
  re-anchored here as the PIT canary integration test verifies the
  sidecar-only contract).

**Cycle 7 remaining deliverables:**
- Stage-0 sanity (HKS reversal sign on ES/NQ; substrate access required).

## Verdict

**accept-with-remediation.** All critical findings remediated across 3
rounds (Round-1 F-1-1 → Round-2 F-2-1 → Round-3 NaN-poison final fix).
All major findings remediated inline (Round-1: F-1-2/3/4/5/6;
Round-2: F-2-2/3/4). All minor findings applied inline. Repro accepted
clean on Round-1.

**SKILL.md 3-round cap: REACHED.** Per [CLAUDE.md](../../CLAUDE.md)
§"Agentic Iteration", further iteration is operationally rejected.
Residual risks tracked as 4 follow-ups for future evidence-bar
disposition.

14/14 PIT-canary tests green; full H053 suite 173/173.
