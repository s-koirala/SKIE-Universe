# Audit trail — Cycle 5: Hansen SPA + Politis-White stationary bootstrap

**Date:** 2026-04-23
**Deliverable:** [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py), [src/skie_ninja/inference/multipletest/hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py)
**Plan reference:** [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md) §Cycle 5
**Test result:** 453/453 unit tests green (54 new — 35 bootstrap/PW-2004, 19 Hansen SPA).
**Loop:** `audit-remediate-loop` — 1 audit round required; Round-2 verification deferred to Cycle 6 end-to-end per Cycle-2/3 precedent.

## Scope delivered

- [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py)
  - `BlockLengthSelection` dataclass (frozen, `to_dict` for ReproLog sidecar).
  - `_flat_top_kernel` (Politis-Romano 1995 *JTSA*).
  - `politis_white_block_length` — PW 2004 §3.1-§3.2 pilot m̂ + M=2m̂ + flat-top weighted G/D, with PPW 2009 corrected constants `D_SB = 2 g(0)²`, `D_CB = (4/3) g(0)²`.
  - `choose_block_length` — multivariate-safe wrapper (max across columns per PW 2004 multivariate recommendation).
  - `stationary_bootstrap_indices` — PR 1994 algorithm with vectorized switch/fresh pre-draws (RNG consumption documented).
  - `stationary_bootstrap` — B-replication driver, same indices across 2-D columns.
- [src/skie_ninja/inference/multipletest/hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py)
  - `HansenSPAResult` dataclass (p-values for all three variants, studentized statistic, best-strategy index, block-length selection, omega method, variant).
  - `_andrews_threshold` — `sqrt(2 log log n)` per Andrews 1999 / Hansen 2005 §2.4 (with floor for tiny n).
  - `_omega_hac` — NW 1994 bandwidth + NW-HAC LRV; variance-scale ε floor.
  - `_omega_bootstrap` — `sqrt(n · var_b(d̄_k^{*b}))`; variance-scale ε floor (unified with HAC path post F-1-1 fix).
  - `_recenter_terms` — computes `g_k^l`, `g_k^c`, `g_k^u` for all three Hansen 2005 §2.4 variants.
  - `hansen_spa_test` — main entry point; returns all three p-values in every call, with the `variant` arg controlling which is reported in `p_value`.
- Two test files: [tests/unit/test_inference_bootstrap.py](../../tests/unit/test_inference_bootstrap.py) (35 tests: uniform-marginal sanity, reproducibility, AR(1) monotonicity, SB-vs-CB coefficient ratio, multivariate max, shape, validation), [tests/unit/test_inference_hansen_spa.py](../../tests/unit/test_inference_hansen_spa.py) (19 tests: variant ordering, RC pathology on dominated strategies, alt/null behavior, 100-MC approximate-size smoke test, both omega paths, reproducibility, validation).

## Audit round

### Round 1 — parallel triad (quant-auditor + literature-check)

| ID | Severity | Category | Disposition |
|---|---|---|---|
| F-1-1 | minor → promoted | stability (inconsistent eps floor scale) | **Remediated** — `_EPS_FLOOR` hoisted to module top; both HAC and bootstrap omega branches now floor on variance scale `omega² >= _EPS_FLOOR`, eliminating the prior scale mismatch. |
| F-1-2 | minor | correctness (no external benchmark) | **Dropped** per skill spec — qualitative tests cover variant ordering, null-size, alt-power, RC pathology, reproducibility, validation. Numerical cross-check against `arch.bootstrap.SPA` logged as Phase-1 follow-up `P1-SPA-ARCH-BENCHMARK`. |
| F-1-3 | minor | other (RNG consumption order) | **Remediated in docstring** — `stationary_bootstrap_indices` docstring now explicitly notes the vectorized pre-draw order differs from lazy-on-switch (`arch`) consumption; self-reproducibility under a fixed seed is preserved, cross-implementation reproducibility is not a design goal. |
| L-1-1 | **critical** | citation (wrong journal for PR 1995) | **Remediated** — Politis & Romano 1995 flat-top kernel reference corrected from (wrong) JASA 90:1105-1118 to the actual *Journal of Time Series Analysis* 16(1): 67-103, https://doi.org/10.1111/j.1467-9892.1995.tb00223.x. Fixed in both the module preamble References block and the `_flat_top_kernel` docstring. |
| L-1-2 | major | overreach (PPW 2009 scope) | **Remediated** — the docstring claim that PPW 2009 "only modifies the circular-block formula" was overreach; PPW 2009 revised both SB and CB constants. Rephrased to state that PPW 2009 revised both and that the implemented `D_SB = 2 g(0)²` and `D_CB = (4/3) g(0)²` are the post-correction values matching `arch` + `blocklength`. |
| L-1-3 | major | misattribution (threshold rule) | **Remediated** — the threshold-rule formula `c · sqrt(log10(n)/n)` with `c=2` and the `K_N` lookahead window is Politis & White 2004 §3.1 (building on Politis 2003), not Brockwell & Davis 1991 §7.2. BD §7.2-§7.3 only motivates the Gaussian 95% critical-value factor of 2 for iid sample-ACF; the `log10(n)/n` inflation is PW 2004's. Docstring and inline comment both corrected; Politis 2003 added to References. |
| L-1-4 | minor | citation (§3.4 vs §3.3 multivariate) | **Remediated** — dropped the specific subsection label, retained the substantive "max across columns" attribution to the PW 2004 multivariate discussion. |
| L-1-5, L-1-6, L-1-7 | minor | wrong-eq-number / unverified section | **Remediated** — removed all unverified equation-number claims (`eq. 4-5`, `eq. 7`, `footnote 2`, `§2.1`) from the Hansen SPA docstring and inline comments, replacing with §-level references verified against secondary summaries (`§2.2`, `§2.4`, `§2`). Added a "Verification status" note to the module docstring. |
| L-1-8 | major | verification-gap (primary-source PDFs blocked) | **Remediated** — explicit "Verification status of primary-source claims" paragraph added to both [bootstrap.py](../../src/skie_ninja/inference/bootstrap.py) and [hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py) module docstrings. Each records: (a) the tandfonline/wiley paywall block, (b) what was verified against secondary implementations (`arch` Python package, `blocklength` R package, Hansen-Lunde MulCom conventions), (c) what remains pending. Full-PDF reconciliation tracked as `P1-SPA-PDF-VERIFY`. |

### Round-2 verification deferral

Consistent with Cycle 2 (HAC+Sharpe-CI) and Cycle 3 (HMM toolkit) precedents, Round-2 parallel re-audit is deferred to Cycle 6 end-to-end verification. Rationale:

1. All Round-1 findings have been remediated in a single round; no new load-bearing behavior changes remain.
2. The lone behavioral change (F-1-1 ε-floor unification on the variance scale) is defensive only — for non-degenerate data, `n · var_b(d̄^{*})` is orders of magnitude above `_EPS_FLOOR`, so the fix affects no realistic input.
3. The residual verification-gap (L-1-8) is not addressable without physical access to the primary PDFs; it is tracked as a follow-up and does not block progression to Cycle 6.
4. Cycle 6 will exercise the full composed pipeline (walk-forward → HAC Sharpe CI → Hansen SPA over the accumulated strategy universe) on H050, which is the authoritative end-to-end regression for Cycles 2-5.

## Residual risk

1. **Primary-source PDF verification gap** (L-1-8) — Hansen 2005 JBES, Politis & White 2004, and Patton-Politis-White 2009 PDFs were inaccessible during this audit (tandfonline paywall / 403 binary). Formulas and constants were cross-validated against the `arch` Python package (Kevin Sheppard, post-PPW 2009) and the `blocklength` R package (PWSD), and against the Hansen-Lunde MulCom Ox reference implementation conventions. Section-level labels (`§2.2`, `§2.4`, `§3.1`, `§3.2`) follow secondary summaries. Tracked as `P1-SPA-PDF-VERIFY`.
2. **No external numerical benchmark test** (F-1-2) — the test suite verifies qualitative SPA properties (variant ordering, RC pathology on dominated strategies, alt/null behavior, approximate size under H₀) but not pointwise equality against `arch.bootstrap.SPA`. Tracked as `P1-SPA-ARCH-BENCHMARK`.
3. **RNG consumption order is implementation-specific** (F-1-3 as documented) — `stationary_bootstrap_indices` pre-draws the switch and fresh-start vectors in one shot; self-reproducibility under a fixed seed holds, but `arch`-compatible cross-implementation replay is not available. Not a Phase-1 follow-up unless a paired replay is required.
4. **`omega_method="bootstrap"` couples two sources of MC error** — the p-value depends on the same bootstrap draws twice (once for ω̂², once for the null distribution), creating a mild downward bias in p-values at small B. Hansen 2005 §2.2 acknowledges this; using `omega_method="hac"` decouples the two. Default remains bootstrap (matching MulCom); users with tight-gate H0xx hypotheses should re-run with HAC.

## Follow-ups filed

- `P1-SPA-PDF-VERIFY` — reconcile Hansen 2005 JBES, PW 2004, and PPW 2009 primary-source PDFs against all in-source section and equation references once physical / author-hosted PDFs are available.
- `P1-SPA-ARCH-BENCHMARK` — add a pinned-seed numerical regression test comparing this module's `hansen_spa_test` output to `arch.bootstrap.SPA` on a common panel.
- `P1-SPA-HAC-DEFAULT-ADR` — ADR to decide whether `omega_method="hac"` should be the default for H050 gate computation given the MC-coupling concern in (4) above.

## Provenance

- Git HEAD at start: `d9c98d5` (claude/thirsty-hawking-472887, clean).
- `deps-sha`: `45cff4f379f9` (158 pkgs in `uv.lock`, unchanged since Cycle 4).
- Data dir manifest: 9 files, sha `0a2606358b8f`.
- Test runtime: 121 s wall (453 unit tests, of which 54 new this cycle).
- Audit artifacts: this file.
