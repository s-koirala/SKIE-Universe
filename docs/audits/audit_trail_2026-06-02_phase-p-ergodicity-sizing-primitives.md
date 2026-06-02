# Audit trail — Phase P P-3 ergodicity sizing primitives (CPPI + joint-Kelly)

- **Date**: 2026-06-02
- **Artifacts under audit**: [src/skie_ninja/sizing/ergodicity.py](../../src/skie_ninja/sizing/ergodicity.py); [tests/unit/test_sizing_ergodicity.py](../../tests/unit/test_sizing_ergodicity.py); re-export edit in [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py).
- **Authority**: ADR-0029 §D-3 (Thrust 2) / Phase P buildout P-3; follow-ups `P1-CPPI-FLOOR-RATCHET-SIZING-PRIMITIVE` + `P1-JOINT-KELLY-CONCURRENT-SIZING-PRIMITIVE`.
- **Discipline**: audit-remediate-loop, 3-round cap. Round 1 with proper-isolated parallel quant-auditor + code-reviewer. Round 2 verification deferred to the holdout-calibration + first closed-loop run (the empirical check on the optimizer behavior).

## Round 1 — quant-auditor (agentId a8a1b08cc4e068bab) — verdict `proceed-with-remediation`

CPPI arithmetic, the ratcheting floor, the canonical exposure = m × cushion, the joint objective form, the M=1 mathematical reduction, and the ergodicity framing (Peters 2019 / Peters-Adamou 2022) all verified correct. 3 majors (all on joint-Kelly) + minors:

| # | Severity | Finding | Remediation |
|---|---|---|---|
| F-1-1 | **major** | The "concave → global optimum" claim is false past the ruin boundary: the `1e-9` log-arg floor is NOT a barrier, so the optimizer can return a **guaranteed-bankrupt** fraction (probe: single arm [0.5,0.5,0.5,0.5,−0.95] at cap=5 → f*=5, worst-period gross −3.75 < 0). | **Applied.** Added a per-period **no-ruin SLSQP inequality** `min_t(1 + R·f) >= _RUIN_EPSILON` so the feasible set is the concave no-bankruptcy region; the single-arm path bounds `f_upper = min(cap, (1−ε)/|min(r)|)` (mirrors `kelly_fraction_from_r_multiples`). Docstring concavity claim qualified to the no-ruin region. Regression test `test_no_ruin_constraint_prevents_bankrupting_fraction`. |
| F-1-2 | **major** | The floor masks ruin and biases `growth_rate` to a finite value where the true time-average growth is −inf (the operative quantity per the module's own ergodicity thesis). | **Applied.** Added `bankrupts_on_path: bool` to JointKellyResult; `growth_rate = -inf` when `min_t(1 + R·f*) <= 0`. With F-1-1's constraint this should never trigger; the check is a safety annotation. `growth_rate` recomputed at the clipped fractions (not `res.fun`). |
| F-1-3 | **major** (test) | `test_correlated_arms_avoid_overbet` passed via cap-SATURATION (standalone hit per_arm_cap=2.0), not the de-correlation mechanism — a tautology. | **Applied.** Rewritten with modest-edge fixture + high per_arm_cap=5.0 so standalone is INTERIOR; now asserts `total ≈ sum_standalone/2` (two copies of one bet → joint total = single-arm Kelly = half the naive sum). |
| F-1-4 | **major** (test) | `test_single_arm_reduces_to_1d` passed because both joint + standalone pinned to the cap (diff 0.0) — validated nothing about the interior reduction. | **Applied.** Modest-edge fixture (interior Kelly ~0.56 < cap=1.0); asserts `0 < fractions[0] < 0.99` (interior) and ≈ standalone. |
| F-1-5 | minor | SLSQP satisfies `Σf <= cap` only to tolerance; the per-arm clip cannot restore the SUM cap → the "hard survival cap" could be marginally exceeded. | **Applied.** Post-solve renormalization `fractions *= cap/sum` when `sum > cap`. |
| F-1-6 | minor | Joint optimizer relies on bounds + concavity (not an explicit short-circuit) to zero negative-edge arms; asymmetry with `_single_arm_kelly`'s mean≤0 check undocumented. | Documented; the no-ruin-constraint + bounds + concavity correctly zero negative-edge arms (test `test_negative_edge_arm_gets_zero`). |
| F-1-7 | minor | CPPIResult docstring said sizing_scale is "capped at 1.0 on new highs" — false under defaults (fresh-peak scale = m·(1−ff) = 0.8 at m=4, ff=0.8; reaches 1.0 only when m ≥ 1/(1−ff)). | **Applied.** Docstring corrected with the exact fresh-peak formula. |
| F-1-8 | minor | `min_floor` (the Black-Perold gap-through protection) defaults to None → protection OFF by default, with no recommended derivation. | **Applied.** Docstring gives recommended `min_floor ≈ 0.55 × starting_equity` (buffer above the ADR-0017 §4.2 50% ruin line) + states the protection is OFF when None. Calibration follow-up `P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION`. |
| F-1-9 | minor | De-correlation precondition for the Peters-Adamou lift is an unimplemented external gate. | **Applied.** `joint_kelly_fractions` docstring states the pooling lift is conditional on caller-verified de-correlation (`P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE`). |

## Round 1 — code-reviewer (agentId a9b70ae46bafe9e05) — verdict `remediate`

3 majors + minors (the re-export was verified idiomatic + circular-import-safe; the frozen+ndarray `__eq__` footgun was recorded-not-flagged as the uniform project convention):

| # | Severity | Finding | Remediation |
|---|---|---|---|
| CR-1-1 | **major** | Silent fail-open: a non-converged joint solve returns all-zero fractions, indistinguishable from a legitimate no-edge result; not auditable. | **Applied.** `logger.warning(res.message)` on non-convergence in both paths; the `converged` flag surfaces it; docstring notes all-zero can mean no-edge OR non-convergence (read `converged`). |
| CR-1-2 | **major** | `_single_arm_kelly` silently swallowed its own non-convergence, corrupting the over-bet diagnostic. | **Applied.** Warning log on non-convergence. |
| CR-1-3 | **major** (types) | scipy `res.x` is `Any`, reused without narrowing. | **Applied.** `np.asarray(res.x, dtype=float)` at both call sites. |
| CR-1-4 | minor | Private helpers `_neg_log_growth` / `_single_arm_kelly` had no docstrings; the mean≤0 early-exit was unexplained. | **Applied.** Docstrings added; the G'(0)=mean(r)≤0 boundary cross-referenced. |
| CR-1-6 | minor | scipy `x0` warm-starts were unjustified magic initializations. | **Applied.** `# justify:` comments (interior warm-start; concave → x0-insensitive). |
| CR-1-8 | minor | Coverage gaps: `converged` flag, no-edge growth_rate, standalone fields, `per_arm_cap<=0` validation untested. | **Applied.** Added `test_converged_and_not_bankrupt_on_happy_path`, `test_growth_rate_nonpositive_for_no_edge`, `test_standalone_fractions_nonnegative`, `test_nonpositive_per_arm_cap_raises`. |
| CR-1-10 | minor | `growth_rate` recompute (vs `res.fun`) intentional-but-undocumented. | **Applied.** `# justify:` noting recompute at the clipped fractions. |
| CR-1-5, CR-1-7, CR-1-9, CR-1-11, CR-1-12 | minor | T≥2 floor permissiveness; frozen+ndarray `__eq__` (uniform convention, recorded-not-flagged); test-docstring RNG over-claim; re-export clean pass; min_floor pin. | F-1-8 covers the min_floor pin; the rest documented / accepted as convention-consistent. |

## Verdict

Round 1: **accept-with-residuals.** Both auditors' majors remediated (the two load-bearing joint-Kelly correctness defects F-1-1/F-1-2 closed with the no-ruin constraint + bankrupts_on_path; the silent fail-open CR-1-1/2 closed with warnings; the two artifact-tautology tests F-1-3/F-1-4 rewritten to exercise interior optima). 27/27 unit tests green; ergodicity.py + test file ruff-clean + formatted; the `__init__.py` re-export is circular-import-safe (verified). The 2 pre-existing `test_sizing.py` failures (`compute_position_size` tests) are UNRELATED — confirmed by stash-attribution (they fail with this edit removed); registered as `P1-SIZING-COMPUTE-POSITION-SIZE-TESTS-STALE`.

**Residuals (Phase P calibration / closed-loop concerns):** CPPI floor_fraction/multiplier/min_floor + joint total_exposure_cap calibration (`P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION`; holdout per ADR-0029 §D-3); the de-correlation gate (`P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE`) that conditions the Peters-Adamou pooling lift. Round 2 folds into the P-4 correlation matrix + the P-5 closed-loop run.
