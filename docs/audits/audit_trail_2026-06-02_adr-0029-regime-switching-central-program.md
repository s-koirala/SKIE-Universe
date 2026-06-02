# Audit trail — ADR-0029 regime-switching meta-allocation central program

- **Date**: 2026-06-02
- **Artifacts under audit**: [ADR-0029](../decisions/ADR-0029-regime-switching-meta-allocation-central-program.md); [memo_regime-switching-closed-loop-foundations_2026-06-02.md](../research_notes/memo_regime-switching-closed-loop-foundations_2026-06-02.md); [plan/buildouts/phase_p_regime_switching_closed_loop_buildout.md](../../plan/buildouts/phase_p_regime_switching_closed_loop_buildout.md).
- **Discipline**: audit-remediate-loop, 3-round cap per SKILL.md. Round 1 executed with proper-isolated parallel subagents (Agent tool available this session). Round 2 verification deferred to Phase P primitive implementation (where parity/PIT tests empirically enforce the design claims).
- **Provenance**: preceded by two parallel literature-verification research threads (2026-06-02) supplying the verified citation set before drafting.

## Round 1 — parallel literature-check + quant-auditor

### Literature-check (agentId a77994323ef5647c1) — verdict `accept`

24 distinct sources checked on BOTH bibliographic accuracy AND finding-direction fidelity (the project's recurring regression class). **23/24 verify clean.** The documented finding-direction-inversion class (cf. Hsu-Kuan 2005 Phase O.10, AFML Phase O.11/O.14, Breiman 1996 Phase N) did **not** recur — every direction-sensitive attribution (Peters ×3, Guttal negative-result, Diks-Hommes-Wang mixed-evidence, Busseti-Ryu-Boyd fractional-optimum, Black-Perold gap-through, MacLean-Thorp-Ziemba growth-security) checked against source and held. MacLean-Thorp-Ziemba 2011 confirmed an edited volume. LML-Press correction confirmed correct.

| # | Severity | Finding | Remediation |
|---|---|---|---|
| L-1 | minor | The artifacts' own flag "Shiryaev 1963 has no era-DOI" is **itself wrong** — SIAM retroactively minted DOI [10.1137/1108002](https://doi.org/10.1137/1108002), which resolves to the exact paper (*Theory Probab. Appl.* 8(1):22-46, 1963). The conservative disposition was harmless but the stated reason was a factual error. | **Applied.** ADR References + memo §1.2(b) + §3 corrected to cite the DOI; Shiryaev-Roberts promoted from "secondary-only flag" to a verified primary citation. |

Informational (no action): Peters 2019 carries an Author Correction (DOI 10.1038/s41567-019-0769-0); the cited primary DOI stands.

### Quant-auditor (agentId af7309e10b0650ca3) — verdict `proceed-with-remediation`

1 major + 7 minor. All remediated inline.

| # | Severity | Finding | Remediation |
|---|---|---|---|
| F-1-1 | **major** (leakage) | MPV2 §D-4 inference design correct, but the per-session reward-matrix construction's **causal-alignment invariant was unstated**. The MPV1 predecessor it elevates uses `t mod n` cycle-resampling + an ex-post `oracle_baseline` (full-sample arm means); a look-ahead bug there would invalidate the "beat 1/N OOS" claim despite correct inference. | **Applied.** Added an explicit "Causal-alignment invariant (BLOCKING)" paragraph to §D-4: (i) arm-k session-t reward from params frozen on data < t; (ii) 1/N + B&H on the identical causal matrix; (iii) oracle is a non-tradeable diagnostic excluded from the beat-target; (iv) MPV2 inherits Cycle-4 leak canaries. Mirrored into Phase P buildout P-5. |
| F-1-2 | minor (method) | §D-3.1 equated "median terminal-wealth path / geometric-mean growth / time-average" — they coincide only under lognormality; under the project's skew-positive τ₃≈+0.74 regime they diverge. | **Applied.** §D-3.1 + memo §2.1 now report **two** headline figures — median equity path (operator-facing) AND MPPM(ρ=1) (exact time-average growth, an existing primitive) — and state the lognormal-only coincidence. |
| F-1-3 | minor (method) | Kelly-optimum claim should specify it maximizes the concave g(f)=E[log(1+f·R)] on the *true* distribution; estimation error shrinks the practical optimum below plug-in full-Kelly. | **Applied.** §D-3.2 adds the concavity + fractional-Kelly-for-uncertainty sentence (strengthens the ceiling argument). |
| F-1-4 | minor (method) | "operator experiences the time-average" is an asymptotic a.s.-limit statement, slightly overstated as finite-horizon determinism. | **Applied.** §D-3.1 reworded to a.s.-convergence-at-long-horizon + median-as-finite-horizon-central-estimate. |
| F-1-5 | minor (assumption) | "variance ~1/N pooling" holds only for de-correlated equal-variance arms; floors at average pairwise covariance (ES-NQ ≈ +0.85); Peters-Adamou lift requires genuine P&L pooling, not siloed sub-accounts. | **Applied.** §D-3.4 annotated with the correlation-floor caveat + genuine-pooling requirement. |
| F-1-6 | minor (consistency) | "Super-Kelly grid preserved verbatim" understates that D-3.2 tightens promotion eligibility; `super-kelly-time-average-dominated` vs ADR-0018's `super-kelly-operator-discretionary` co-existence unclear. | **Applied.** §D-5 ADR-0018 row reworded (grid VALUES preserved; promotion eligibility tightened); co-existence (ergodicity-mechanism flag vs literature-evidence flag, neither supersedes) stated in §D-5 + §Consequences. |
| F-1-7 | minor (method) | "leading" should be operationalized as detection-lead-relative-to-BOCD on the holdout, not standalone forecast skill. | **Applied.** §D-2 Wiring paragraph adds the relative-timing-statistic clause + the Diks-Hommes-Wang tripwire hedge. |
| F-1-8 | minor (parameter) | CPPI multiplier m + floor-buffer magnitude lacked the holdout-calibration flag the EWS thresholds carry (no-magic-number discipline); 50% ruin line is principled (inherited ADR-0017 §4.2). | **Applied.** §D-3.3 adds the holdout-calibration flag for m + buffer; 50%-line provenance noted. |

## Verdict

Round 1: **accept-with-residuals.** All critical/major findings (1 major) + all 8 minor findings remediated inline. The single literature finding (L-1) was a self-correction (the artifact's own flag was wrong) and carries no propagation risk. No finding-direction-inversion regression recurred.

**Residuals (Phase P execution concerns, not artifact defects):** (a) F-1-1's MPV2 causal-alignment invariant must be *empirically* enforced by the Cycle-4 leak canaries when `scripts/run_mpv2_closed_loop.py` is built (P-5); (b) F-1-5's realized cross-arm correlation (ES-NQ ≈ +0.85) may leave insufficient effective breadth for the time-diversification growth-lift — gated by `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE` (P-4). Both are the right thing for the buildout to surface and are registered as BLOCKING-BEFORE-CLOSED-LOOP-RUN.

Round 2 verification deferred to Phase P primitive landings per the SKILL.md cap (the parity/PIT tests there are the empirical check on these design claims).
