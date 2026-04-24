---
name: Cycle-1 audit trail — roll-adjusted 1-min derivative
description: Audit-remediate-loop trail for the Tier-2b Cycle-1 deliverable (vendor_legacy_1min_roll_adjusted)
type: project
status: closed
date: 2026-04-23
rounds: 2 (of 3-round cap)
verdict: proceed-with-follow-ups
---

# Cycle 1 — roll-adjusted 1-min derivative

Per [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md). Delivers the evidence-bar-tier continuous-contract derivative required for H050 / H051 / H052a to promote past `designed`.

## Deliverables (committed this cycle)

- New module: [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) — version 0.2.0 (Round-2 remediation baseline).
- New schema: `VendorLegacy1minRollAdjustedSchema` in [src/skie_ninja/data/validation/schema.py](../../src/skie_ninja/data/validation/schema.py).
- Unit tests: 29 new tests in [tests/unit/test_vendor_legacy_1min_roll_adjusted.py](../../tests/unit/test_vendor_legacy_1min_roll_adjusted.py) (241/241 unit suite passing).
- CLI wiring: [scripts/ingest.py](../../scripts/ingest.py) registers `vendor_legacy_1min_roll_adjusted` in `_DATASET_CHOICES`, `_module_map`, and `_SCHEMA_MAP`.
- Parent-dataset fix: [src/skie_ninja/data/ingest/vendor_legacy_1min.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) provenance-key normalization (F-1-6 remediation — raw-ingest idempotency guard restored).

## Method

Multiplicative ratio adjustment per **de Prado 2018 AFML ch.2 §2.4.3 "Single Future Roll"** (distinct from §2.4.1 "The ETF Trick"), rolled on volume-crossover with a persistence window read from [config/instruments.yaml](../../config/instruments.yaml) `roll_rule.window_days`. Anchor: ρ = new_open(t_first_new) / old_close(t_last_old). Supplementary references: Chan 2013 ch.3, Carver 2023 app. Futures data. OHLC tuple scaling + unadjusted volume follow Norgate/CSI operational convention (not AFML).

Evidence-bar tier: **True for returns, False for levels**. Level columns (open/high/low/close) are retrospectively rescaled by the full-sample roll history and are not point-in-time safe for walk-forward use without per-fold re-materialization. Provenance JSON discriminates via `evidence_bar_eligible_returns` / `evidence_bar_eligible_levels`. Tracked as Phase-1 follow-up `P1-LEVEL-USE-POLICY` for enforcement at the feature-factory layer.

## Audit rounds

### Round 1 (parallel agents — quant-auditor + reproducibility-verifier + literature-check)

**16 findings** total (2 critical method, 2 critical citation/anchor, 7 major, 5 minor).

Critical / blocking:
- **F-1-1 (quant)** — No oscillation guard in roll detection; spurious multiplicative drift possible during roll windows.
- **F-1-2 (quant)** — Full-sample back-adjustment violates point-in-time safety for level-based features.
- **lit-check #1** — Cited `§2.4.1` (ETF Trick) but implemented Single Future Roll (§2.4.3).
- **lit-check #2** — Anchor bar was synchronous-overlap minute; AFML §2.4.3 specifies close/open succession at roll boundary.

Major:
- F-1-3 post-roll anchor fallback leak; F-1-4 calendar-date session attribution (vs CME 17:00 CT trading-day boundary); F-1-5 `window_days` config value declared but ignored in module; F-1-6 `scripts/ingest.py::_source_unchanged` key mismatch (broke SHA256 idempotency); F-1-7 missing chain-continuity assertion; F-1-8 newest-contract derivation weak against oscillation; F-1-9 schema does not enforce cross-row invariants; repro#1 non-atomic provenance write; repro#3 incomplete two-phase-commit rollback; lit-check config/impl divergence on `window_days`; lit-check OHLC/volume extension not documented as going beyond AFML; lit-check volume-vs-OI empirical-evidence gap.

Minor: tolerance magic number (F-1-10), tie-break determinism (F-1-12), provenance detail (F-1-13), documentation items, test coverage expansion.

### Round 2 — remediation (all critical + all major + select minors)

Module rewritten to v0.2.0:
1. ✓ `apply_persistence_guard` with `window_days` consecutive-session persistence requirement (F-1-1, F-1-5).
2. ✓ Provenance flags `evidence_bar_eligible_returns` / `evidence_bar_eligible_levels` discrimination + `level_use_pit_safe: false` + `P1-LEVEL-USE-POLICY` follow-up (F-1-2).
3. ✓ AFML §2.4.3 citation (module + schema) (lit-check #1).
4. ✓ `compute_roll_ratio_afml` uses old_close / new_open succession, no synchronous-overlap or post-roll fallback (lit-check #2, F-1-3).
5. ✓ `_session_date_expr` uses `+7h` CME trading-day boundary via polars `dt.offset_by` (F-1-4).
6. ✓ `sp.as_posix()` keys on both sides of the idempotency guard, plus `date.today()` → UTC in the CLI (F-1-6).
7. ✓ Chain-continuity assertion in `_adjust_one_symbol` (F-1-7).
8. ✓ Newest contract derived from `effective_front.sort('session_date').tail(1)` and cross-checked against `ratios[-1].event.new_contract` (F-1-8).
9. ✓ `validate()` enforces cross-row invariants: (a) exactly one contract/symbol with factor==1.0, (b) factor constant within (symbol, contract), (c) `roll_flag` consistency (F-1-9).
10. ✓ `_atomic_write_json` (tempfile + fsync + `os.replace`) for provenance (repro#1).
11. ✓ Two-phase commit with pre-promotion snapshot + rollback (repro#3).
12. ✓ Docstring notes on OHLC/volume convention extension + Chan 2013 / Carver 2023 supplementary citations + `P1-ROLL-METHOD` / `P1-ROLL-ANCHOR` verification-gap notes (lit-check major).
13. ✓ Tolerance documented as `10 * n_rolls * eps * max_px` (Higham 2002 §3.1) (F-1-10).
14. ✓ Secondary deterministic sort key `contract_symbol` in front-month argmax (F-1-12).
15. ✓ Provenance `run_summary` with rolls / contract_factors / rejected_oscillations / bars_dropped_non_front (F-1-13).

Round-2 verification by quant-auditor: **5 findings** (1 major carry-over fix, 2 minor doc/robustness, 2 minor test-coverage):
- **F-2-5 (major)** — evidence-bar flag discrimination (levels vs returns).
- F-2-1 schema docstring still said §2.4.1.
- F-2-2 persistence-guard retroactive-rewrite semantics documentation.
- F-2-3 two-phase-commit memory cost at scale (defer).
- F-2-4 session-edge test coverage (defer).

### Round 3 — cheap remediation + close

- ✓ F-2-5: `evidence_bar_eligible_returns` / `_levels` split in provenance; legacy single-boolean alias retained.
- ✓ F-2-1: schema docstring §2.4.1 → §2.4.3 with ETF-Trick disambiguation.
- ✓ F-2-2: module docstring Step 3 clarifies retroactive-rewrite semantics.

## Deferred to Phase-1 follow-ups

| Item | Source | Why deferred | Follow-up ID |
|---|---|---|---|
| Level-based feature enforcement at feature-factory layer | F-1-2 / F-2-5 | Feature factory arrives in Cycle 4/6; advisory flags are sufficient for Cycle 1 | `P1-LEVEL-USE-POLICY` |
| Volume-crossover vs OI-crossover empirical study | lit-check | No peer-reviewed evidence exists; practitioner convention for now | `P1-ROLL-METHOD` |
| Anchor-choice sensitivity (close/open vs synchronous vs settlement) | F-1-11 | Study requires actual multi-roll historical data ingested, which is now available — can run in Phase 1 | `P1-ROLL-ANCHOR` |
| Memory-efficient two-phase-commit rollback | F-2-3 | In-memory snapshot works at current ~20MB/partition scale | `P1-INGEST-ROLLBACK` |
| Session-edge-case test coverage | F-1-15 / F-2-4 | Current tests cover the hot path; edge-case regression coverage deferred | `P1-SESSION-EDGE-TESTS` |
| NoOverlapError operational runbook automation | F-1-16 | Documented in module docstring; automation not required yet | `P1-INGEST-RUNBOOK` |

## Residual risk

Level-based features built on this derivative in walk-forward CV will silently leak future rolls unless re-materialized per fold. The provenance flag discrimination + module docstring + Phase-1 follow-up `P1-LEVEL-USE-POLICY` are the current mitigations. H050 / H052a designs must specify return-based features only, or explicitly require per-fold re-materialization, for Cycle 6.

## Verdict

**proceed-with-follow-ups.** Cycle 1 deliverable accepted. Cycle 2 (NW-HAC + Sharpe CI) starts next.
