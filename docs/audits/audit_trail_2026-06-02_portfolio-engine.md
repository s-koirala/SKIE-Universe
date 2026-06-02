# Audit trail — simultaneous multi-asset long/short portfolio engine (ADR-0020)

- **Date**: 2026-06-02
- **Artifacts**: [src/skie_ninja/meta/portfolio.py](../../src/skie_ninja/meta/portfolio.py); [tests/unit/test_portfolio.py](../../tests/unit/test_portfolio.py).
- **Authority**: ADR-0020 (`P1-META-PORTFOLIO-ORCHESTRATOR-IMPL`) + ADR-0029 §D-3.4 (pooling) + the operator 2026-06-02 ask: "union signals independently, buy/short/Kelly multiple assets." The simultaneous-portfolio paradigm, complementary to MPV2 switching.
- **Discipline**: audit-remediate-loop, 3-round cap. Round 1 with proper-isolated parallel quant-auditor + code-reviewer. Round 2 deferred to the first real-data multi-asset book run.

## Round 1 — code-reviewer (agentId a5c48bb32341a52e7)

| # | Severity | Finding | Remediation |
|---|---|---|---|
| CR-1 | **critical** | `isinstance(per_instrument_cap, float)` returns False for an **int** cap (the natural call form) → falls to the dict branch → `(5).get(inst)` → `AttributeError`, violating the `ValueError` contract. | **Applied.** Inverted to `isinstance(..., dict)` — any non-dict scalar (int / float / np.floating) is a uniform cap. Regression test `test_int_cap_treated_as_uniform_scalar`. |
| CR-2 | major | The documented `K >= 1` guard was delegated to `joint_kelly_fractions`, whose error message leaks the internal `returns_matrix` param name to a `construct_portfolio` caller. | **Applied.** Local `k_bets < 1` guard with a caller-facing message. |
| CR-3 | major | Coverage gaps: `instrument_capped` flag, `growth_rate` value, continuous-signal, int-cap, empty `per_instrument_gross`, `n_periods`. | **Applied.** Added `test_int_cap_*`, `test_continuous_signal_scales`, `test_instrument_capped_flag_and_empty_gross`, `test_growth_rate_analytic_constant`, `test_n_periods_and_status_fields`. |
| CR-4..CR-10 | minor | Type-hint precision, `.copy()` redundancy, naming drift, by-design double-validation. | Documented / accepted as convention-consistent; the `.copy()` is defensive. |

## Round 1 — quant-auditor (agentId a0b218708a9dae9dc) — verdict `proceed-with-remediation`

Core composition verified methodologically correct: signed-return long/short encoding is valid for a long-only joint-Kelly; the gross-per-instrument cap is provably conservative (`gross >= |net|` confirmed — capacity never under-stated); `dr @ fractions` is the correct realized book return (partial deployment → undeployed bankroll earns 0, correct); book no-ruin is inherited while uncapped.

| # | Severity | Finding | Remediation |
|---|---|---|---|
| F-1-1 | major | Continuous-signal magnitude double-counts conviction against the Kelly fraction (the docstring invited magnitude-as-conviction; joint-Kelly ALSO sizes → effective exposure non-monotone in declared conviction). No-op for the sign-only signals all tests use. | **Applied.** Docstring reworded: the SIGN is direction; **v1 recommends sign-only**; a continuous magnitude is a pre-Kelly leverage tilt Kelly partially undoes (NOT a conviction weight — conviction is joint-Kelly's job). Continuous semantics → `P1-PORTFOLIO-CONTINUOUS-SIGNAL-CONVICTION`. |
| F-1-2 | major | `PortfolioResult` dropped joint-Kelly's `bankrupts_on_path` + `converged`; `growth_rate` used the `1e-9` floor — re-introducing one layer up the exact positively-biased masking the ergodicity F-1-2 fix prevents. | **Applied.** `PortfolioResult` gains `converged` + `bankrupts_on_path`; `growth_rate = -inf` when `min_t(1 + book_return) <= 0`; warns on non-convergence. |
| F-1-3 | major | The per-instrument cap is a POST-HOC proportional throttle, not a constrained joint-Kelly solve — freed capacity is not reallocated, so under an active cap the book is growth-suboptimal. The within-group scaling is correct. | **Applied.** Docstring (PortfolioResult.growth_rate + construct_portfolio NOTE) scopes it as a lower bound on constrained-optimal growth; `instrument_capped=True` ⇒ suboptimal-vs-constrained. v2 → `P1-PORTFOLIO-CONSTRAINED-JOINT-KELLY-V2`. |
| F-1-4 | minor | Gross-per-instrument cap is conservative vs true netting (`gross >= |net|`) — capacity never under-stated; cost is potential under-deployment when offsetting arms share an instrument. | **Applied.** `cap_by_instrument` docstring states the conservative-but-capital-inefficient tradeoff + the netting v2 (`P1-PORTFOLIO-NET-LONG-SHORT-V2`). |
| F-1-5 | minor | Undeployed bankroll earning 0 (cash) is correct but undocumented; `dr @ f` correctly does NOT renormalize to sum-1. | Documented (the bankroll-fraction convention; risk-free carry on undeployed capital is v1-out-of-scope). |
| F-1-6 | minor | The instrument-group abstraction is the right K-5 primitive, but the v1 fraction-space cap equals the ADR-0017 §5.2 $-notional K-5 cap only iff fractions are bankroll-notional-normalized (the joint-Kelly fractions are). | **Applied.** `cap_by_instrument` docstring states the fraction-space-vs-notional equivalence condition + the caller's responsibility to pass the fraction-space equivalent of the §5.2 cap. |
| F-1-7 | minor | Long/short fixture used a degenerate anti-correlated pair + no `instrument_ids`. | **Applied.** Added `test_shared_instrument_long_short_gross_capped` (long-ES + short-ES sharing one budget, gross-capped). |

## Verdict

Round 1: **accept-with-residuals.** The critical CR-1 (int-cap crash) + all 3 quant majors + all code-reviewer majors remediated. 23/23 portfolio tests + 110 meta-allocation/Phase-P tests green; ruff-clean + formatted. The engine correctly delivers the operator ask — **union K independent per-asset signals, long/short (signed-return encoding), joint-Kelly-sized concurrently, with per-instrument capacity caps** — closing `P1-META-PORTFOLIO-ORCHESTRATOR-IMPL`.

**Residuals (v2 refinements, not v1 defects):** `P1-PORTFOLIO-NET-LONG-SHORT-V2` (true same-instrument long/short netting vs the conservative gross cap); `P1-PORTFOLIO-CONSTRAINED-JOINT-KELLY-V2` (per-instrument caps inside the joint-Kelly solve vs the post-hoc throttle); `P1-PORTFOLIO-CONTINUOUS-SIGNAL-CONVICTION` (clean continuous-conviction semantics); `P1-ADR-0020-LONG-SHORT-MULTI-ASSET-AMENDMENT` (formalize the per-asset-signal-union extension of ADR-0020's arm-weighting framing). A real-data multi-asset book run + benchmark vs 1/N is the natural next step (shares the P-1 substrate dependency with MPV2).
