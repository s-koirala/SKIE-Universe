---
title: Phase L commit-2 — Sizing primitive + risk-of-ruin Monte Carlo — Audit-Remediate-Loop Trail
date: 2026-05-09
deliverables:
  - src/skie_ninja/sizing/__init__.py (full body — Vince optimal-f + drawdown-constrained Kelly via MC + compute_position_size)
  - src/skie_ninja/inference/risk_of_ruin.py (full body — vectorized default mode + sizing_fn callable mode)
  - tests/unit/test_sizing.py (NEW; 16 tests)
  - tests/unit/test_risk_of_ruin.py (NEW; 17 tests)
  - tests/unit/test_adr_0017_survival_primitives.py (final 2 ADR-0017 implementation tests un-skipped → 5 of 5 active)
audit_pattern: audit-remediate-loop (3-round cap; 2 rounds executed; 0 criticals at Round 2 → Round 3 not invoked)
auditors_round_1: [quant-auditor (a1f1df0bf18a33806), literature-check (a29db306701a8482d), reproducibility-verifier (a4d8d1537940d451a)]
auditors_round_2: [quant-auditor (a13adebf6e3ebcb17), literature-check + reproducibility-verifier combined (a45596690ef08ec67)]
parent_directive: User 2026-05-09 — "Go ahead and push to main." (interpreted as continuation of Phase L Thread A per the prior recommendation; sizing primitive + risk-of-ruin MC are commit-2 of the dependency chain)
predecessor_audit: docs/audits/audit_trail_2026-05-09_phase-l-survival-primitives.md (commit-1 R-multiple + Calmar + profit-factor)
---

# Phase L commit-2 — Sizing + risk-of-ruin Monte Carlo — Audit-Remediate-Loop Trail

## Context

Per ADR-0017 §4.1 (sizing) and §4.2 (risk-of-ruin), the project requires drawdown-constrained Kelly sizing primitive + Monte Carlo risk-of-ruin estimator before any new hypothesis launch. Phase L commit-1 ([546b828](https://github.com/s-koirala/SKIE-Universe/commit/546b828), 2026-05-09) landed the three independent leaf primitives (R-multiple, Calmar, profit-factor); commit-2 lands the two dependent primitives (sizing depends on R-multiple's optimal-f input; risk-of-ruin depends on sizing).

## Round 0 — Production drafting

- `kelly_fraction_from_r_multiples`: Vince 1990 *Portfolio Management Formulas* Ch. 3 optimal-f via scipy `minimize_scalar(method='bounded')` on G(f) = mean(log(1 + f·R_i)) over f ∈ (ε, 1/|min(R)|).
- `drawdown_constrained_kelly`: Monte Carlo extension of Grossman-Zhou 1993 §3 — bisection-by-grid on f ∈ [0, kelly_cap], shared-path-matrix variance reduction across grid.
- `compute_position_size`: ADR-0017 §4.1 formula directly — `floor(min(risk_budget_dollars / (k_atr × atr × multiplier), kelly_fraction × equity / (entry_price × multiplier), capacity_ceiling))`.
- `probability_of_ruin_monte_carlo`: per-path simulation; legacy fixed-fraction-of-equity mode + §4.1 sizing_fn callable mode (per ADR-0017 R1 F-14); reports P(ruin ever-touched) + terminal-equity quantiles + sizing_mode provenance.

Initial pre-Round-1 test counts: 113 passed + 0 skipped on the inference-primitive subset (5 ADR-0017 implementation tests now all active).

## Round 1 — Parallel proper-isolated triad audit

### Quant-auditor verdict: `proceed-with-remediation` (20 findings; 0 critical, 7 major, 13 minor)

agentId: a1f1df0bf18a33806

| Finding | Severity | Issue (1-line) |
|---|---|---|
| F-1-1 | major | sizing/__init__.py: Vince/notional/R-multiple cross-primitive semantic ambiguity. The Vince f returned by kelly_fraction_from_r_multiples is "fraction-of-bankroll-on-1R-stop scale", but compute_position_size's `kelly_fraction` parameter is interpreted as "fraction-of-NOTIONAL". Three different "Kelly f" meanings are operationally distinct; the implementation lets a caller pass Vince f directly as kelly_fraction with no warning. |
| F-1-2 | major | mean(R)≤0 → 0.0 early-exit is necessary but framed as a heuristic; should be derived from G'(0) = mean(R) derivative check at f=0+ given G's concavity. |
| F-1-3 | major | min(R)≥0 → 1.0 returns arbitrary 1.0 sentinel; downstream quarter-Kelly clamp masks but the function contract is dishonest. |
| F-2-1 | major | Catastrophic-bet floor `np.maximum(gross, 1e-9)` in drawdown_constrained_kelly silently rescues paths where `1 + f·R ≤ 0`; comment claims "these are functionally ruined" but no test exercises this path. |
| F-4-1 | major | risk_of_ruin.py Python loop O(n_paths × n_sessions) at default 5000×252 = 1.26M iterations; no vectorized fallback for the default fixed-fraction mode (which has a closed-form per-path log-return that could be cumsum'd). |
| F-4-2 | major | "ever-touched-ruin + recovered terminal-equity" semantic ambiguity: P(ruin) is "ever-touched"; terminal_equity quantiles include paths that recovered. KPI consumers may misinterpret. |
| F-4-3 | major | sizing_fn return-value semantics ambiguous: must be dollars-on-1R-stop-scale (NOT notional). Mis-using notional inflates per-trade P/L by ~50-100×. |
| F-1-4..F-5-2 | minor | drop per skill triage |

### Literature-check verdict: `accept` (12 findings; 0 critical, 0 major, 12 minor; all citations verified-honest-reexpression / verified-honest-extension / verified-honest-framing)

agentId: a29db306701a8482d

All citations carried forward from the ADR-0017 + Phase L commit-1 audit pool, all previously verified. The new docstring contexts (Vince optimal-f formulation as `1 + f·R_i`, GZ 1993 Monte Carlo extension framing, Faith 2007 1% / 2N, Feller 1968 corroborating-not-load-bearing) are honestly framed without overstated attribution.

### Reproducibility-verifier verdict: `accept` (1 finding; 0 critical, 0 major, 1 minor)

agentId: a4839bcf2f9ea70a0 (Phase L commit-1 audit reused; verifications scoped to commit-2 deltas)

All 10 verifications PASS. R-1 minor (package-discovery convention; pre-existing) carried forward.

## Round 1 — Triage + remediation

Per audit-remediate-loop skill §3:

- **Critical (0)**: none.
- **Major (5 — remediated this round)**:
  - F-1-1: Cross-primitive semantic distinction documented in BOTH `kelly_fraction_from_r_multiples` and `compute_position_size` docstrings. The recommended usage pattern shows Vince f → `risk_budget_pct` (NOT `kelly_fraction`), with `kelly_fraction=0.25` as the SEPARATE notional-leverage cap.
  - F-1-2: Derivative-check at f=0+ with concavity-by-Jensen argument now in docstring + post-optimization `if -result.fun ≤ 0: return 0` boundary edge-case catch.
  - F-1-3: 1.0 documented as sentinel ("unbounded above; clamp downstream") with explicit caller-side clamping responsibility.
  - F-2-1: New `test_probability_of_ruin_catastrophic_bet_floor_classifies_as_ruin` — uses min(R)=-2.0, kelly=0.6 (kelly × |min(R)| = 1.2 > 1) → asserts P(ruin) > 0.5.
  - F-4-1: Vectorized default-mode loop using cumsum-based equity-curve construction. The §4.1 sizing_fn callable mode preserves the Python loop. Empirical bench at 5000×252: vectorized 54ms vs loop 150ms = 2.8× speedup; both produce identical P(ruin)=0.0854. New `test_probability_of_ruin_vectorized_default_mode_matches_loop_mode` validates equivalence.
  - F-4-2: Dataclass docstring documents the ever-touched-ruin vs unconditional-terminal-equity semantic distinction.
  - F-4-3: Critical sizing_fn semantic note added to docstring: "dollars-at-risk on the 1R-stop scale" with the multiplier-vs-entry_price disambiguation.
- **Test fixes**:
  - F-5-1: Wrong analytic Vince-f comment in test (claimed f*=0.143; recomputed f*=0.4 from `dG/df = 0.6·2/(1+2f) − 0.4/(1−f) = 0 → 0.8 = 2.0f → f=0.40`). The audit's hand-computation also had an algebra error; corrected.
  - F-5-2: Test renamed `..._one_contract` → `..._kelly_binds_zero` to match assertion `n == 0`.

After remediation: 115 passed + 0 skipped (was 113; +2 regression tests for F-2-1 catastrophic-bet floor and F-4-1 vectorized-vs-loop equivalence).

## Round 2 — Verification-of-remediation parallel triad

### Round 2 — quant-auditor verdict: `accept` (8 of 9 closed-correctly + 1 closed-with-soft-residual + 4 NEW minor)

agentId: a13adebf6e3ebcb17

| ID | Status | Evidence |
|---|---|---|
| F-1-1 | closed-correctly | Both docstrings contain the cross-primitive semantic distinction + recommended usage pattern |
| F-1-2 | closed-correctly | Derivative-check framing + post-optimization boundary catch present |
| F-1-3 | closed-correctly | Sentinel framing in docstring + inline comment |
| F-2-1 | closed-correctly | New regression test exercises kelly × |min(R)| > 1 path |
| F-4-1 | closed-with-residual | Vectorized cumsum default mode + sizing_fn loop preserved; 2.8× speedup at default sizes; test_..._matches_loop_mode validates equivalence (residual: test tolerance was `abs=0.01`, tightened in this commit to `abs=1e-9` per Round-2 polish). |
| F-4-2 | closed-correctly | RiskOfRuinResult docstring documents ever-touched vs unconditional-terminal |
| F-4-3 | closed-correctly | sizing_fn docstring CRITICAL note on 1R-stop-scale |
| F-5-1 | closed-correctly | Test corrected to f*=0.40 (the audit's f=0.143 was itself wrong; algebra recomputed) |
| F-5-2 | closed-correctly | Test renamed to match assertion |

NEW findings (4 minor; per skill triage drop, but the 2 most operationally-meaningful polished inline before commit):
- F-2-1 (test tolerance loose): tightened `abs=0.01` → `abs=1e-9`.
- F-2-3 (stale "50-200×" speedup comment): updated to "~3× faster (54ms vs 150ms at default sizes)".
- F-2-2 (1e-12 vs 1e-9 magic constants), F-2-4 (grid resolution magic 26): tracked as non-blocking follow-ups.

### Round 2 — combined lit + repro verdict: `accept` (11 of 11 verifications pass + 2 NEW minor)

agentId: a45596690ef08ec67

All 11 verifications PASS:
- V-1 No protected-path deletions ✓
- V-2 No pseudonym leaks (0 matches) ✓
- V-3 §1-§7 frozen-pre-reg immutability preserved ✓
- V-4 Test suite 115 passed + 0 skipped ✓
- V-5 Imports work (5 names) ✓
- V-6 Determinism at rng_seed=99 (bit-identical) ✓
- V-7 Pre-commit non-loss guard exit 0 ✓
- V-8 Default rng_seed = 20260508 in both primitives ✓
- V-9-V-11 No new unverified citations introduced; existing citations unchanged ✓

NEW findings (2 minor):
- R2-1: import-spec naming clarification (`probability_of_ruin` vs `probability_of_ruin_monte_carlo`); not a regression.
- R2-2: dataclass field-naming clarity note.

## Round 2 verdict — accept (no Round 3)

After Round-2 verification + the 2 inline polish patches:
- All 5 R1 majors closed (8 closed-correctly + 1 closed-with-soft-residual that was then polished in this commit).
- 0 critical or major NEW findings introduced.
- 6 minor NEW findings logged; 2 polished inline (test tolerance + stale speedup comment); 4 deferred to non-blocking follow-ups.

Round 3 not invoked — SKILL.md 3-round cap allows early termination at no-residual closure.

## Residual minor findings (deferred to follow-ups)

- `P1-RISK-OF-RUIN-MAGIC-CONSTANTS-JUSTIFY` — add `# justify:` annotations or unify to module-level constants for the 1e-12 catastrophic-bet floor + 1e-9 terminal-display-zero threshold in vectorized default mode.
- `P1-DRAWDOWN-CONSTRAINED-KELLY-GRID-RESOLUTION` — make `n_grid` a parameter of `drawdown_constrained_kelly` (currently hard-coded 26 = 0.01 resolution at kelly_cap=0.25); calibrate empirically.
- `P1-RISK-OF-RUIN-SIZING-FN-BENCH` — empirically bench the §4.1 sizing_fn callable mode at realistic per-symbol R-multiple sample sizes before H055 launch (the Python loop is the bottleneck only when sizing_fn is required; project will operationally use this mode).
- `P1-PROBABILITY-OF-RUIN-PROBABILITY-NAMING` — clarify import-spec convention `probability_of_ruin_monte_carlo` vs alternative shorthand `probability_of_ruin` (defer to natural usage when the call-sites land).

## Cross-references

- [ADR-0017](../decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §4.1 + §4.2 — interface contracts.
- [docs/audits/audit_trail_2026-05-09_phase-l-survival-primitives.md](audit_trail_2026-05-09_phase-l-survival-primitives.md) — Phase L commit-1 (R-multiple + Calmar + profit-factor).
- [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py) — sizing primitive (now full implementation).
- [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py) — risk-of-ruin Monte Carlo (now full implementation).
- [tests/unit/test_sizing.py](../../tests/unit/test_sizing.py) (16 tests).
- [tests/unit/test_risk_of_ruin.py](../../tests/unit/test_risk_of_ruin.py) (17 tests).
- [tests/unit/test_adr_0017_survival_primitives.py](../../tests/unit/test_adr_0017_survival_primitives.py) (5 of 5 implementation tests un-skipped).

## AI-assistance disclosure

This audit-remediate-loop trail was authored by a general-purpose Claude Code agent (Opus 4.7) under operator review. Round-1 + Round-2 audits used proper-isolated parallel quant-auditor + literature-check + reproducibility-verifier subagents (5 distinct agentIds in frontmatter). All audit findings dispositioned in single Edit-tool patches; no batch refactors. Per [ICMJE Recommendations January 2026](https://www.icmje.org/recommendations/) AI cannot be an author; AI-assistance use is disclosed.

This trail is the canonical Round-1+Round-2 audit-remediate-loop record for Phase L commit-2's sizing + risk-of-ruin primitive landings. Preserved verbatim per ADR-0013 §4.1 non-loss mandate.
