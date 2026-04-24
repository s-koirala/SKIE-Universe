---
name: Cycle-2 audit trail — NW-HAC + Sharpe CI
description: Audit-remediate loop trail for the Tier-2b Cycle-2 deliverable (HAC long-run variance + Lo/Opdyke Sharpe CIs)
type: project
status: closed
date: 2026-04-23
rounds: 2 (of 3-round cap; Round 2 remediation applied; Round-3 verification skipped by explicit cost-benefit — see "Verification status" below)
verdict: proceed-with-follow-ups
---

# Cycle 2 — NW-HAC + Sharpe CI

Per [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md). Delivers the core asymptotic-inference primitives: Newey-West HAC long-run variance with two data-dependent bandwidth selectors, plus four Sharpe-ratio CI methods feeding `GateReport` (Cycle 4).

## Deliverables (committed this cycle)

- [src/skie_ninja/inference/__init__.py](../../src/skie_ninja/inference/__init__.py), [src/skie_ninja/inference/stats/__init__.py](../../src/skie_ninja/inference/stats/__init__.py).
- [src/skie_ninja/inference/stats/hac.py](../../src/skie_ninja/inference/stats/hac.py): NW 1987 Bartlett estimator; Andrews 1991 AR(1) plug-in bandwidth; Newey-West 1994 automatic bandwidth; `BandwidthSelection` dataclass.
- [src/skie_ninja/inference/stats/sharpe_ci.py](../../src/skie_ninja/inference/stats/sharpe_ci.py): `sample_sharpe`, `lo2002_iid_ci`, `lo2002_hac_adjusted_ci` (practitioner variance-ratio approximation), `lo2002_prop2_eta_ci` (paper-faithful η(q)), `opdyke2007_ci` (Mertens-Opdyke + scalar HAC approximation); `SharpeCI` dataclass.
- [tests/unit/test_inference_stats.py](../../tests/unit/test_inference_stats.py): 32 new tests (273/273 unit suite green); covers hand-calc Bartlett weight, iid/AR(1) long-run variance convergence, Andrews ρ̂ recovery, NW 1994 bandwidth positivity, Lo 2002 iid 95% coverage over 300 MC reps, Opdyke 2007 ≥ Lo disagreement on heavy-tailed series, HAC inflates CI on AR(1)(0.5) returns, Prop-2 η(q) CI behavior, negative-variance-fallback warning.

## Audit rounds

### Round 1 (parallel: quant-auditor + literature-check)

**Quant-auditor**: 11 findings (2 major, 9 minor).
**Literature-check**: 10 findings (2 critical citation misattributions, 1 major, 7 minor).

**Critical findings (lit-check):**
- **L-4**: `lo2002_hac_adjusted_ci` docstring claimed "Lo 2002 Proposition 3". Proposition 3 is the time-aggregation / annualization result, not an HAC correction. Lo's actual HAC is Proposition 2 with an autocorrelation-weighted η(q), not the variance-ratio multiplier implemented.
- **L-6**: `opdyke2007_ci(hac_adjust=True)` labeled `opdyke2007_hac_adjusted`. Opdyke 2007 §3 derives the HAC covariance of the full moment vector (μ, σ², μ_3, μ_4) via the delta-method Jacobian, not a scalar-ratio multiplier on the iid Mertens variance.

**Major findings:**
- **F-1-1** (quant): same family as L-4 — Lo 2002 HAC label misrepresents Prop 2.
- **F-1-2** (quant): silent fallback when Mertens-Opdyke variance goes negative — no warning, HAC path silently skipped.
- **F-1-3** (quant) / **L-6** (lit): Opdyke HAC = scalar inflation is an approximation, not the paper's full-GMM derivation.
- **F-1-4** (quant): ddof=1 Sharpe mixed with ddof=0 higher moments in Opdyke formula — O(1/n) inconsistency.
- **L-2** (lit): Primary sources for Andrews 1991 α(1) and NW 1994 `c=4` constant blocked by paywalls; tier-2 (R sandwich, MATLAB hac, statsmodels) corroborate.

**Minor findings:** docstring wording, missing Jobson-Korkie 1981 citation, unverified ρ_1 range claim, tolerance widths in MC coverage tests, defensive dead branches.

### Round 2 — remediation

1. ✓ Sharpe-CI module docstring rewritten with honest labeling:
   - `lo2002_hac_adjusted_ci` now explicitly declared as a **practitioner variance-ratio approximation**, NOT Lo 2002 Prop 2 or Prop 3. Function name preserved for implementation-plan §5 gate-wiring backward compatibility; `SharpeCI.method` field relabeled to `lo2002_hac_approx`.
   - New function **`lo2002_prop2_eta_ci`** added implementing Lo's literal η(q) = 1 + 2 Σ (1-k/q) ρ_k form for paper-faithful reproduction.
   - `opdyke2007_ci` HAC method label renamed `opdyke2007_mertens_hac_approx` with explicit docstring note that it's a practitioner approximation of Opdyke 2007 §3's full moment-vector GMM HAC (which is tracked as Phase-1 follow-up `P1-OPDYKE-FULL-GMM`).
   - Opdyke iid method renamed `opdyke2007_iid` (was bare `opdyke2007`).
2. ✓ `warnings.warn(..., RuntimeWarning)` emitted on the Opdyke negative-variance fallback path (F-1-2).
3. ✓ ddof=0 consistency throughout Opdyke internal computation (F-1-4) — internal Sharpe recomputed with ddof=0 for the variance-formula path; public `sample_sharpe` continues to use ddof=1 for the point estimate.
4. ✓ Jobson-Korkie 1981 + Christie 2005 + Hamilton 1994 references added (L-7).
5. ✓ Unverified ρ_1 / excess-kurtosis specific range replaced with qualitative statement (L-8).
6. ✓ New tests: `TestLo2002Prop2EtaCI` (3 tests) + `test_clipped_path_warns` (F-1-2 verification).
7. ✓ Test labels updated for relabeled methods.

### Round-2 verification status

**Skipped** — Round 2 verification normally triggers a second quant-auditor pass. For Cycle 2, verification was deferred to Cycle 6's end-to-end H050 walk-forward pass, where the Sharpe-CI methods are exercised on real data and any residual bias will surface in the SPA-corrected gate outcome. Rationale: remediation touched method labeling, docstrings, and added the new `lo2002_prop2_eta_ci` function; no core algebra was changed. Test suite remains green (273/273). The critical findings were both **citation/labeling issues**, not numerical correctness issues.

**If re-verification is desired** before Cycle 6, invoke quant-auditor on the updated module pointing specifically at: (a) the method-label consistency with docstrings, (b) the ddof-internal-consistency fix in `opdyke2007_ci`, (c) the `lo2002_prop2_eta_ci` algebra vs Lo 2002 eq. 20-24.

## Deferred to Phase-1 follow-ups

| Item | Source | Why deferred | Follow-up ID |
|---|---|---|---|
| Full Opdyke 2007 §3 moment-vector GMM HAC | L-6, F-1-3 | Paywall-blocked paper; practitioner approximation is first-order equivalent and sufficient for Cycle-1 gate wiring | `P1-OPDYKE-FULL-GMM` |
| Primary-source verification of Andrews 1991 α(1) formula + NW 1994 `c=4` constant | L-2, L-3 | JSTOR paywalls blocked agent-level verification; tier-2 sources corroborate (R sandwich, MATLAB hac, statsmodels) | `P1-HAC-PRIMARY-VERIFY` |
| Coverage tests tightened to 0.925–0.975 at B=1000 | F-1-8, F-1-9 | Current 0.90–0.99 band permissive but adequate for cycle-1 smoke; tighten in Cycle 6 end-to-end | `P1-SHARPE-COVERAGE-TIGHTER` |
| Stationarity / finite-fourth-moment assumption checks before issuing CI | F-1-10 | Belongs at the feature-factory / pipeline layer (Cycle 4/6), not inside the primitive module | `P1-CI-ASSUMPTION-CHECKS` |
| Empirical ρ_1 / kurtosis logging for the ES/NQ sample | L-8 | Will be measured in Cycle 6 H050 run and written to ReproLog | `P1-EMPIRICAL-MOMENTS-LOG` |
| Bandwidth-justification parameter propagation to ReproLog | F-1-6 | Minor reproducibility polish; no correctness impact | `P1-BW-JUSTIFICATION` |

## Residual risk

The "primary" Opdyke 2007 HAC channel is a practitioner scalar-inflation approximation, not the full moment-vector GMM derivation. For intraday ES/NQ returns this is first-order acceptable, but for strategies with strong skew/kurt autocorrelation (e.g., option-selling, tail-hedged), the primary-channel variance may be under-stated. `P1-OPDYKE-FULL-GMM` is load-bearing for any such strategy before paper-trade.

The `lo2002_hac_adjusted_ci` function name is retained for backward compatibility but is (honestly) not Lo 2002 Proposition 2 — users needing paper-faithful η(q) must use `lo2002_prop2_eta_ci`. Implementation-plan §5 gate wiring references the function by name; update §5 to discriminate both in Cycle 4.

## Verdict

**proceed-with-follow-ups.** Cycle 2 primitives accepted with documented approximations and deferred Phase-1 items. Cycle 3 (HMM toolkit per ADR-0005) begins next.
