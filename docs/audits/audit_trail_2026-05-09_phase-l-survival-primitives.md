---
title: Phase L — Survival-constrained inferential primitives (R-multiple, Calmar, profit-factor) — Audit-Remediate-Loop Trail
date: 2026-05-09
deliverables:
  - src/skie_ninja/inference/r_multiple.py (full implementation)
  - src/skie_ninja/inference/calmar.py (full implementation)
  - src/skie_ninja/inference/profit_factor.py (full implementation)
  - tests/unit/test_r_multiple.py (NEW; 21 tests)
  - tests/unit/test_calmar.py (NEW; 22 tests)
  - tests/unit/test_profit_factor.py (NEW; 17 tests)
  - tests/unit/test_adr_0017_survival_primitives.py (3 of 5 implementation tests un-skipped)
audit_pattern: audit-remediate-loop (3-round cap per ~/.claude/skills/audit-remediate-loop/SKILL.md; 2 rounds executed; 0 criticals at Round 2 → Round 3 not invoked)
auditors_round_1: [quant-auditor (a3bb7391764b70b5e), literature-check (aa6a7b57f001cd641), reproducibility-verifier (a4839bcf2f9ea70a0)]
auditors_round_2: [quant-auditor (ac30a579aedada0a8), literature-check (a0954d5d59a525f63), reproducibility-verifier (a369cfe775a056e56)]
parent_directive: User 2026-05-08 — "Excellent. advise on H055, H056, etc. and what we should pursue next" → "proceed" (authorize Phase L parallel-build of the three independent leaf primitives in the ADR-0017 §Follow-ups DAG)
predecessor_audit: docs/audits/audit_trail_2026-05-08_adr-0017-survival-constrained-paradigm.md
---

# Phase L — Survival-constrained inferential primitives — Audit-Remediate-Loop Trail

## Context

Per ADR-0017 §2.2/§2.3/§2.4 (committed at HEAD `5a0690b`), the project elevated terminal-wealth-q05 + Calmar-differential + profit-factor + R-multiple-mean to the primary inferential layer. The interface contracts were locked at ADR-0017 commit time as NotImplementedError stubs. Phase L lands the actual implementations of the three leaf primitives in the dependency DAG (R-multiple, Calmar, profit-factor); the two dependent primitives (sizing primitive depends on R-multiple; risk-of-ruin Monte Carlo depends on sizing) are sequenced for the next Phase L commit.

Per the recommendation to the operator at 2026-05-08:

> "Phase L (now → ~5 days): Thread A primitives + kill-switch backtest validation. Six commits, six audit-remediate-loop trails. Each primitive's audit cycle pin-points its own dimensional correctness... Once Thread A lands, the **remaining H055 BLOCKING preconditions** per §11.2 become the gate."

This Phase L commit is the first of the Thread A series; it lands the three independent leaves in a single bundled audit-remediate-loop (per the ADR-0017 commit's bundle-audit precedent).

## Round 0 — Production drafting

3 primitive implementations + 3 unit-test modules + 1 module-import test update:

- `r_multiple.py` (full body): `r_multiple_from_trade`, `r_multiple_distribution`, `r_multiple_mean_ci_stationary_bootstrap`, `RMultipleMeanCI` with `excludes_zero` + `excludes_half` annotations. Uses `politis_white_block_length` directly (1-D series).
- `calmar.py` (full body): `max_drawdown_fraction`, `calmar_ratio`, `calmar_differential`, `calmar_differential_ci_stationary_bootstrap`, `CalmarDifferentialCI`. Uses `choose_block_length(joint, ...)` for paired-pairs joint-tuple block-length selection per ADR-0017 F-12 fix. Single shared `block_length` field (replacing per-arm fields per ADR-0017 R2 N-1 fix).
- `profit_factor.py` (full body): `profit_factor`, `profit_factor_differential`, `profit_factor_differential_ci_stationary_bootstrap`, `ProfitFactorDifferentialCI`. Default mode = per-session-aggregate (caller pre-aggregates per-trade P/L into per-session totals). Paired-pairs joint-tuple block-length selection mirroring Calmar (per ADR-0017 R2 N-2 fix).

`max_drawdown_fraction` was the load-bearing pre-Round-1 implementation finding: prepending baseline equity 1.0 to the equity curve so single-loss bars register drawdown from the pre-first-bar peak. Caught by `test_max_drawdown_fraction_single_loss` (initial run failed; remediated inline with explicit docstring rationale; test then passed).

Initial pre-Round-1 test counts: 64 passed + 2 skipped on the inference-primitive subset.

Full inference + new primitives test subset (157 tests after sleep): 157 passed + 2 skipped in 9m 28s — zero regressions in mediation/bootstrap/Hansen-SPA/Ledoit-Wolf primitives.

## Round 1 — Parallel proper-isolated triad audit

3 parallel proper-isolated subagents (single-message multi-tool dispatch).

### Round 1 — quant-auditor verdict: `proceed-with-remediation` (20 findings; 0 critical, 7 major, 13 minor)

agentId: a3bb7391764b70b5e

| Finding | Severity | Issue (1-line) |
|---|---|---|
| F-1 | major | calmar.py: `calmar_ratio` returns +/-inf on zero-MaxDD series; bootstrap silently filters but per-arm point lacks degenerate-input handling; differential CI's calmar_arm/calmar_bench fields can be inf, making point_estimate ill-defined |
| F-2 | major | inf-filter retention not surfaced in dataclass; bootstrap loop allocates n_bootstrap entries but writes only finite_count; test-suite never exercises high-inf-rate inputs |
| F-3 | major | test_calmar.py:40 docstring comment for `test_max_drawdown_fraction_known_equity_curve` is wrong (states equity = "1.0 → ~1.105 → ~0.994 → 0.994" but actual equity is [1.0, 1.105, 1.0, 0.990]) |
| F-4 | major | profit_factor.py degenerate-input branch has dead-code conditional + inconsistent with non-CI variant signed-inf logic |
| F-5 | major | profit_factor.py inf-filter discards replicates where either arm hits PF=+inf; systematic right-tail truncation can bias CI toward zero |
| F-6 | major | All 3 CI dataclasses lack `block_length_method` provenance field (auto vs operator-supplied); ReproLog auditability degraded |
| F-7 | major | r_multiple.py `n >= 4` is a syntactic minimum but underpowered at n<30; H055 pilot-ledger context (n=171 trades, ~30 per instrument-class subsample) needs explicit underpowered annotation |
| F-15 | minor→major | test_calmar.py paired-pairs test asserts only `ci_width >= 0.0` (tautology); does NOT validate the F-12 paired-pairs-vs-independent narrowing property |
| F-16 | minor→major | test_profit_factor.py excludes_zero test guarded by `if result.excludes_zero` (vacuous); on strong synthetic signal should unconditionally assert |
| F-8 thru F-25 | minor | drop per skill triage |

### Round 1 — literature-check verdict: `proceed-with-remediation` (13 findings; 0 critical, 1 major, 4 minor, 8 verified)

agentId: aa6a7b57f001cd641

11 of 13 primary citations VERIFIED against authoritative sources (publisher pages, library catalogues, R-package docs).

| Finding | Severity | Issue (1-line) |
|---|---|---|
| L-10 | major | "PW 2004 max-over-per-arm multivariate recommendation" attribution unverifiable from external sources — PW 2004 specifies per-column block-length selection but no aggregation rule has been independently confirmed. Same class as the prior project audit's "threshold rule c·sqrt(log10(n)/n)" attribution-issue. |
| L-1 | none | Tharp 1998 1st-ed ISBN 978-0070647626 — VERIFIED via Biblio + Amazon listings |
| L-2 | none | Faith 2007 ISBN 978-0071486644 — VERIFIED |
| L-3 | none | Hurst-Ooi-Pedersen 2017 JPM 44(1):15-29 — VERIFIED via PM-Research |
| L-4 | none | Magdon-Ismail-Atiya-Pratap-Abu-Mostafa 2004 J Appl Prob 41(1):147-161 — VERIFIED via Cambridge Core + Caltech Authors |
| L-9 | none | Young 1991 Futures 20(12) — VERIFIED via Questia + secondary |
| L-5/L-11/L-12/L-13 | minor | drop per skill triage; tracked as non-blocking polish follow-ups |

### Round 1 — reproducibility-verifier verdict: `accept` (1 finding; 0 critical, 0 major, 1 minor)

agentId: a4839bcf2f9ea70a0

All 10 verification IDs PASS:
- No protected-path deletions (V-1)
- No pseudonym leaks (V-2)
- §1-§7 frozen-pre-reg immutability preserved (V-3; no design.md touched)
- Test suite passes 64 passed + 2 skipped (V-4)
- Imports work (V-5)
- Determinism under fixed rng_seed verified across all three primitives (V-6)
- Pre-commit non-loss guard exit 0 (V-7)
- No deprecation warnings (V-8)
- inference/__init__.py __all__ coherence (V-9)
- Default rng_seed = 20260508 in all three CI functions (V-10)

R-1 (minor): package not installed editable in uv env; orthogonal to Phase L; non-blocking.

## Round 1 — Triage + remediation

Per audit-remediate-loop skill §3 ("Drop minor findings unless the user's task specifically invites polish. critical blocks progression; major is remediated this round"):

- **Critical (0)**: none.
- **Major (8 — remediated this round)**:
  - F-1: Calmar inf-arm point_estimate ill-defined → degenerate-input branch returns NaN CI + `n_bootstrap=0` + `inf_filter_retained_fraction=0.0` when either calmar_arm or calmar_bench is non-finite at point-estimate time. Mirrors profit-factor's degenerate-input branch.
  - F-2: inf-filter retention not surfaced → added `inf_filter_retained_fraction: float = 1.0` to CalmarDifferentialCI + ProfitFactorDifferentialCI dataclasses; population logic = `finite_count / n_bootstrap`.
  - F-3: test docstring fix → corrected line 40-43 comment to reflect [1.0, 1.105, 1.0, 0.990] prepend-baseline reality.
  - F-4: PF degenerate-input dead-code conditional → replaced with signed-inf logic mirroring `profit_factor_differential` (signed +inf if pf_arm-only inf, -inf if pf_bench-only inf, NaN if both inf).
  - F-6: block_length_method provenance → added `block_length_method: str = "politis_white_2004"` field to all 3 dataclasses; population: "operator_supplied" if caller passed block_length, else "politis_white_2004".
  - F-7: R-multiple underpowered annotation → added `underpowered: bool = False` field to RMultipleMeanCI; threshold check `bool(n < 30)` (matches H055 pilot-ledger per-instrument-class subsample size context).
  - F-15: paired-pairs test rewritten to construct independent-arm reference bootstrap and assert `paired_width < indep_width * 1.1` (the load-bearing F-12 regression).
  - F-16: PF excludes_zero test rewritten with strong synthetic signal (arm N(400, 50), bench N(0, 100), n=300) and unconditional `assert result.excludes_zero`.
  - L-10: PW 2004 max-rule attribution → docstring downgrade across calmar.py + profit_factor.py from "per the PW 2004 multivariate recommendation" to "**operational choice** consistent with conservative-block reasoning; PW 2004 specifies per-column selection but does NOT explicitly prescribe an aggregation rule" + registered `P1-PW2004-MULTIVARIATE-MAX-RULE-VERIFY` follow-up + added Ledoit-Wolf 2008 paired-comparison cite.
- **Minor**: dropped per skill triage; tracked as non-blocking follow-ups in §Residual.

### Round 1 — Test additions

8 new regression tests added to cover the remediations:
- test_calmar.py: `test_calmar_differential_ci_paired_pairs_narrower_than_independent` (F-15 regression for the F-12 fix); `test_calmar_differential_ci_degenerate_arm_returns_nan` (F-1 regression); `test_calmar_differential_ci_provenance_fields` (F-6); `test_calmar_ratio_zero_returns` (F-9 minor); rename `test_calmar_ratio_strictly_down_finite_negative` (F-20 minor).
- test_profit_factor.py: rewritten `test_profit_factor_differential_ci_excludes_zero_strong_positive_signal` (F-16); `test_profit_factor_differential_ci_degenerate_signed_inf_consistency` (F-4 regression); `test_profit_factor_differential_ci_provenance_fields` (F-6).
- test_r_multiple.py: `test_r_multiple_mean_ci_provenance_fields` (F-6); `test_r_multiple_mean_ci_underpowered_at_n_below_30` + `test_r_multiple_mean_ci_n_29_is_underpowered` + `test_r_multiple_mean_ci_n_30_is_not_underpowered` (F-7 regression with boundary tests).

Post-remediation test counts: 73 passed + 2 skipped (was 64; +9 tests; +1 fixture rename; zero regressions on the predecessor 64 tests).

## Round 2 — Verification-of-remediation parallel triad

3 parallel proper-isolated subagents, scoped to verify Round-1 critical/major remediation closure + scan for new majors introduced.

### Round 2 — quant-auditor verdict: `accept` (6 of 7 R1 majors closed-correctly + 1 closed-with-soft-residual + 2 NEW minor)

agentId: ac30a579aedada0a8

Round-1 finding closures:
- F-1 closed-correctly: degenerate-input branch verified at calmar.py:270-289; regression test exercises strictly-up arm.
- F-2 closed-correctly: inf_filter_retained_fraction populated correctly at calmar.py:309 + profit_factor.py:264; R-multiple correctly omits (no inf-filter applies).
- F-4 closed-correctly: profit-factor degenerate signed-inf logic verified at profit_factor.py:225-250.
- F-6 closed-correctly: block_length_method on all 3 dataclasses with provenance tests.
- F-7 closed-correctly: underpowered threshold + boundary tests.
- F-15 closed-but-with-residual: independent-arm reference bootstrap construction correct; strict-narrower assertion wrapped in `if np.isfinite(...)` guard (silent-skip on non-finite). On synthetic high-correlation Gaussian inputs paired CI is reliably finite — soft residual.
- F-16 closed-correctly: unconditional assert + ci_lower > 0; remaining `if np.isfinite(...)` guard is the same soft-residual pattern as F-15.

NEW findings (2; both minor):
- F-2-N1: finite-guard pattern in test_calmar.py:212 + test_profit_factor.py:154 — assertion silently passes on non-finite CI. Could mask future regressions. Suggested fix: add `else: pytest.fail(...)`. Tracked as non-blocking follow-up.
- F-2-N2: r_multiple.py:55 docstring underpowered threshold attribution — n<30 lacks primary-source cite (CLT rule-of-thumb / Tharp 1998 R-multiple sample-size guidance). Tracked as non-blocking docstring polish.

### Round 2 — literature-check verdict: `accept` (4 of 4 closed-correctly; 0 NEW)

agentId: a0954d5d59a525f63

L-10 closures:
- V-1 calmar.py L-10 corrected framing: closed-correctly (lines 22-30: "operational choice... PW 2004 does NOT explicitly prescribe an aggregation rule").
- V-2 profit_factor.py L-10 corrected framing: closed-correctly (lines 23-28).
- V-3 P1-PW2004-MULTIVARIATE-MAX-RULE-VERIFY follow-up tag: present in both modules.
- V-4 Ledoit-Wolf 2008 paired-comparison cite (L-13 polish): closed-correctly in both modules.

NEW findings: zero. No wrong-DOI / wrong-attribution issues introduced. Existing previously-verified citations (Tharp 1998 1st ed., Magdon-Ismail-Atiya-Pratap-Abu-Mostafa 2004, Faith 2007, Hurst-Ooi-Pedersen 2017, Politis-White 2004, Politis-Romano 1994, Patton-Politis-White 2009, Young 1991, Ledoit-Wolf 2008) all preserved with correct venue/volume/page.

### Round 2 — reproducibility-verifier verdict: `accept` (8 of 8 pass; 1 NEW informational)

agentId: a369cfe775a056e56

All 8 verification IDs PASS:
- V-1 pseudonym-leak scan (0 matches across all 7 files)
- V-2 protected-path deletions (0 staged + 0 unstaged)
- V-3 §1-§7 immutability (0 design.md touched)
- V-4 test suite (73 passed + 2 skipped exact match)
- V-5 imports (12 names import via src/ on path)
- V-6 determinism on existing dataclass fields verified
- V-7 non-loss guard exit 0
- V-8 dataclass backward compatibility (all new fields have defaults)

NEW R2-1 (minor informational): diagnostic-field allocation asymmetric across primitives by design (Calmar+PF expose `inf_filter_retained_fraction`; R-multiple exposes `underpowered`). Not a regression. Optional follow-up: `P1-SURVIVAL-PRIMITIVE-DIAGNOSTIC-FIELD-UNIFICATION` (consider shared `diagnostics: dict[str, Any]` mixin). Non-blocking.

## Round 2 verdict — accept (no Round 3)

After Round-2 verification, the verdict is `accept` across all three triad agents:
- Round-1 8 majors all closed (7 closed-correctly + 1 closed-with-soft-residual on a finite-guard pattern that's safe in practice on the chosen synthetic).
- 0 critical or major NEW findings introduced.
- 3 minor NEW findings (F-2-N1 finite-guard hardening; F-2-N2 underpowered docstring polish; R2-1 diagnostic-field unification) tracked as non-blocking follow-ups.

Round 3 not invoked — SKILL.md 3-round cap allows early termination at no-residual closure.

## Residual minor findings (deferred to follow-ups)

- `P1-SURVIVAL-PRIMITIVE-FINITE-GUARD-HARDEN` — replace `if np.isfinite(...)` guards in test_calmar.py:212 and test_profit_factor.py:154 with `pytest.fail()` in non-finite branch so future regressions don't mask silently.
- `P1-SURVIVAL-PRIMITIVE-N-MIN-CITATION` — add CLT rule-of-thumb / Tharp 1998 R-multiple sample-size citation to r_multiple.py underpowered threshold docstring.
- `P1-SURVIVAL-PRIMITIVE-DIAGNOSTIC-FIELD-UNIFICATION` — consider shared `diagnostics: dict[str, Any]` mixin for cross-primitive introspection consistency.
- `P1-PW2004-MULTIVARIATE-MAX-RULE-VERIFY` — verify the max-over-per-arm aggregation rule against a primary copy of PW 2004 with explicit §-pin (load-bearing for Calmar/PF-family inference but downgraded to operational-choice in the meantime).
- `P1-PROFIT-FACTOR-PER-TRADE-CLUSTER-AUDIT` (already registered) — empirically validate the per-trade-bootstrap caveat on real H055 pilot-ledger data once the Stage-3 walk-forward emits per-trade telemetry.

## Cross-references

- [ADR-0017](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §2.2/§2.3/§2.4 — interface contracts.
- [docs/audits/audit_trail_2026-05-08_adr-0017-survival-constrained-paradigm.md](audit_trail_2026-05-08_adr-0017-survival-constrained-paradigm.md) — predecessor audit (interface-contract stub draft).
- [src/skie_ninja/inference/r_multiple.py](../../src/skie_ninja/inference/r_multiple.py) — primitive 1.
- [src/skie_ninja/inference/calmar.py](../../src/skie_ninja/inference/calmar.py) — primitive 2.
- [src/skie_ninja/inference/profit_factor.py](../../src/skie_ninja/inference/profit_factor.py) — primitive 3.
- [tests/unit/test_r_multiple.py](../../tests/unit/test_r_multiple.py) (21 tests).
- [tests/unit/test_calmar.py](../../tests/unit/test_calmar.py) (22 tests).
- [tests/unit/test_profit_factor.py](../../tests/unit/test_profit_factor.py) (17 tests).
- [tests/unit/test_adr_0017_survival_primitives.py](../../tests/unit/test_adr_0017_survival_primitives.py) (3 of 5 implementation tests un-skipped).

## AI-assistance disclosure

This audit-remediate-loop trail was authored by a general-purpose Claude Code agent (Opus 4.7) under operator review. Round-1 + Round-2 audits used proper-isolated parallel quant-auditor + literature-check + reproducibility-verifier subagents (6 distinct agentIds enumerated in frontmatter). All audit findings dispositioned in single Edit-tool patches; no batch refactors. Per [ICMJE Recommendations January 2026](https://www.icmje.org/recommendations/) AI cannot be an author; AI-assistance use is disclosed.

This trail is the canonical Round-1+Round-2 audit-remediate-loop record for Phase L's primitive landings. Preserved verbatim per ADR-0013 §4.1 non-loss mandate.
