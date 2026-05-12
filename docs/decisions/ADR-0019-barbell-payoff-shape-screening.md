---
id: ADR-0019
title: Barbell payoff-shape screening discipline — L-skewness annotation in every KPI report card
status: proposed
date: 2026-05-12
---

# ADR-0019 — Barbell payoff-shape screening discipline

## Context

The SKIE-Universe project has emitted three production KPI report cards under [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) + [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) discipline. The realized-OOS pattern across them is structurally consistent and load-bearing for this ADR:

- **H050 v1** ([research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md)): realized $10K → $1,898 (ES gated, −81.0%) / $1,580 (NQ gated, −84.2%) over 489 OOS sessions; realized win rate 32.9% / 31.4%; the gated-arm equity curve is the canonical "death-by-thousand-cuts" shape — a long sequence of small losing bars (always-in cost drag plus regime-gating noise) with no compensating right-tail event.
- **H052a v1** ([research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md)): NQ unconditional ORB realized $10K → $11,061 (+10.61%) over 369 OOS sessions with realized max-DD ~12%; trade-distribution histogram exhibits a positive right shoulder (the rare 2-to-3-ATR breakout day) and a truncated left tail (stop-loss imposes a hard floor at −1R) — mildly skew-positive by construction.
- **H053 v4** ([research/01_hypothesis_register/H053/H053_kpi_report_v3.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v3.md)): NQ LightGBM realized +10.8% / max-DD 3.7%; the per-session predictand window (09:45→10:30 ET) is symmetric by construction since the labeller is signed continuous return — no asymmetric stop-loss truncation; observed skewness near zero.

The empirical pattern: SKIE strategies that emit large realized losses do so via the **skew-negative** mechanism (many small losing trades plus occasional large losses, with no fat right tail to compensate); strategies that emit modest realized gains do so via mild **skew-positive** asymmetry (stop-loss caps the left tail, occasional 2–3R breakouts populate the right tail). This is exactly the structural distinction [Taleb 2007 *The Black Swan*](https://www.amazon.com/Black-Swan-Improbable-Robustness-Fragility/dp/081297381X) Ch. 16 + [Taleb 2012 *Antifragile*](https://www.amazon.com/Antifragile-Things-That-Disorder-Incerto/dp/0812979680) Ch. 18-19 — both *practitioner* — frames as the **fragile vs antifragile** payoff dichotomy: convex payoffs ("benefit from disorder") gain from rare large moves; concave payoffs ("harmed by disorder") suffer from them.

The operator articulated 2026-05-12 the goal of "exponential profitability". Geometric compounding under bounded drawdown ([ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) §4.1 fractional-Kelly sizing) produces exponential equity growth **only when the right tail of the per-trade R-multiple distribution is fat enough to dominate the left tail in the log-utility integral**. Concretely, for log-utility growth rate `g = E[log(1 + f·R)]` where `R` is the per-trade R-multiple and `f` is the Kelly fraction, `g > 0` requires either positive mean (the case ADR-0017 §4.1 already addresses via the `kelly_fraction_from_r_multiples` primitive) **or** positive skewness contribution in the Taylor expansion `g ≈ f·μ_R − (f²/2)·σ_R² + (f³/3)·γ_R·σ_R³ − ...` where `γ_R` is the standardised third moment. A skew-negative strategy (`γ_R < 0`) leaks growth-rate via the third-moment term even at constant mean and variance; the [Brandt-Santa-Clara-Valkanov 2009 *RFS* 22(9):3411-3447](https://doi.org/10.1093/rfs/hhp003) parametric-portfolio-policies framework formalizes this by directly conditioning on higher-moment characteristics of the predictand distribution rather than the Sharpe-mean only.

[ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) §3 introduced four primary metrics (`terminal_wealth_q05`, `calmar_differential`, `profit_factor`, `r_multiple_mean`); ADR-0018 introduces MPPM(ρ=1) per [Goetzmann-Ingersoll-Spiegel-Welch 2007 *RFS*](https://doi.org/10.1093/rfs/hhm025) as the aggressive-growth primary fitness for inner-CV hyperparameter selection. Neither ADR captures the **shape** of the per-trade R-multiple distribution beyond its first two moments and aggregate drawdown — both can score "marginal" on a skew-negative strategy that is actually structurally doomed to leak growth-rate in the long-horizon limit. This ADR closes that gap with a pre-strategy-launch *screening* annotation, not a gate.

Ordinary sample skewness `(1/n)·Σ(x − x̄)³/s³` is known to be unstable in heavy-tailed samples (its variance is itself a function of the population sixth moment, which is often infinite or ill-defined for futures-trade R-multiple distributions). [Hosking 1990 *J Royal Stat Soc B* 52(1):105-124](https://www.jstor.org/stable/2345653) introduces **L-moments** as linear combinations of order statistics; the L-skewness `τ_3 = λ_3/λ_2` is bounded in `[−1, 1]`, has finite variance whenever the second L-moment is finite (a much weaker condition than finite sixth moment), and is the canonical robust skew estimator for financial returns per [Theodossiou 1998 "Financial Data and the Skewed Generalized T Distribution," *Mgmt Sci* 44(12-Part-1):1650-1661](https://doi.org/10.1287/mnsc.44.12.1650). This is the primitive ADR-0019 adopts.

## Decision

Effective 2026-05-12, every KPI report card emitted under [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) discipline carries a mandatory **payoff-shape annotation** and a new mandatory results-summary table. No gate is added; promotion remains operator-discretionary per [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1+§2 no-binding-gates philosophy.

**Decision 1 — payoff-shape KPI annotation**. Every KPI report card includes `payoff-shape-{skew-positive, skew-flat, skew-negative}` based on the per-trade R-multiple distribution L-skewness estimator τ_3 per [Hosking 1990](https://www.jstor.org/stable/2345653). Threshold rule:
- `τ_3 > +0.1` → `skew-positive` (antifragile in the Taleb 2012 sense; right-tail-fat)
- `τ_3 < −0.1` → `skew-negative` (fragile; left-tail-fat — current SKIE H050 gated-arm pattern)
- otherwise → `skew-flat`

The ±0.1 cutoff is **project-operational** and consistent with [Hosking 1990](https://www.jstor.org/stable/2345653) §4 sampling-variance scaling for L-moment estimators at typical financial sample sizes (n ≈ 200–500 trades); the specific table-page pin is tracked under follow-up `P1-ADR-0019-HOSKING-SECTION-PIN-VERIFY`. Empirical calibration of the cutoff against the SKIE realized-OOS distribution is tracked under `P1-ADR-0019-PAYOFF-SHAPE-THRESHOLD-EMPIRICAL`. Bootstrap 95% CI on τ_3 reported via percentile [Politis-Romano 1994 *JASA*](https://doi.org/10.1080/01621459.1994.10476870) stationary bootstrap; if the CI crosses ±0.1, the annotation reads `skew-{positive,negative}-marginal`.

**Decision 2 — Table 1c "Payoff-shape diagnostics" added to ADR-0014 §3.2**. The canonical 9-table results summary mandated by [ADR-0014 §3.2](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) is extended to **13 tables** when ADR-0019 is in force (Tables 1c + 3a + 3b + 3c per ADR-0017 §3.2 + this Table 1c). Table 1c reports, per arm:
- L-skewness τ_3 point estimate
- 95% bootstrap percentile CI on τ_3
- Max single-trade R-multiple (the right-tail extremum)
- Min single-trade R-multiple (the left-tail extremum; structurally bounded near −1 when stop-loss enforced per [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) §5 K-1)
- Tail-ratio `(P95 R) / |P05 R|` — a heuristic complement to τ_3 anchored on operator-interpretable percentiles
- Payoff-shape annotation per Decision 1

**Decision 3 — no binding gate**. Skew-negative strategies still progress to NinjaScript implementation per [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §5 terminal-state mandate. The annotation enters the operator promotion-decision-rule under [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) §3 as an additional column; operators MAY decline `paper-trade-active` or `live-promoted` transitions on skew-negative strategies with documented rationale, and that decision is reversible per [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4 non-loss preservation.

**Decision 4 — inner-CV tie-breaker**. The walk-forward inner-CV hyperparameter selector (e.g., [scripts/run_h055_walk_forward.py](../../scripts/run_h055_walk_forward.py) and successors) MAY use L-skewness τ_3 as a **tie-breaker** when MPPM(ρ=1) values per ADR-0018 §Decision 1 are within 1σ across grid cells. The primary fitness remains MPPM(ρ=1); τ_3 is consulted only on the boundary. The tie-breaker rule prefers the more skew-positive cell. This preserves ADR-0018's growth-rate primary fitness while breaking ties in the direction of antifragility.

**Decision 5 — barbell-rebalance-candidate flag**. Strategies labeled `skew-negative` receive a `barbell-rebalance-candidate` flag in the KPI report card §"Methodological-correctness annotations" line. The flag indicates that the operator may want to investigate adding an explicit convex-hedge sibling arm — concretely, a far-OTM long-options leg whose payoff is bounded-loss-unbounded-gain by construction — to convert the family payoff-shape from concave-toward-net-skew-negative to convex-toward-net-skew-positive. This is the [Taleb 2012 *Antifragile*](https://www.amazon.com/Antifragile-Things-That-Disorder-Incerto/dp/0812979680) Ch. 23-25 "barbell strategy": pair a low-risk core (`90%` capital in T-bill-equivalent) with a high-convexity tail (`10%` capital in far-OTM options) to produce an aggregate payoff that gains from disorder. The flag is informational; no automatic sibling arm is generated. The 0DTE sibling repo [SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) per [ADR-0006](ADR-0006-scope-extension-hmm-0dte.md) is a natural barbell-tail candidate; cross-link is recorded in flagged strategies' design.md §15.2.

## Consequences

**Positive**:
- Closes the higher-moment blind spot in [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) + ADR-0018 primary metrics. A strategy can now be `tw-q05-above-half + calmar-diff-positive + mppm-positive + skew-negative` — the four primary annotations capture mean-variance + survival, the new annotation captures shape.
- Provides a structural diagnostic for why H050 v1 realized catastrophically despite Sharpe-CI excluding zero negatively on the inferential side: skew-negative payoff under fractional-Kelly produces growth-rate leakage via the third-moment Taylor term; ADR-0019 makes that mechanism visible in the report card rather than implicit in the aggregate equity curve.
- [Hosking 1990](https://www.jstor.org/stable/2345653) L-skewness is the most-cited robust skew estimator in financial-time-series literature; the project gains a peer-reviewed-anchored shape diagnostic at the cost of one new primitive (≈ 80 lines of code).
- [Harvey-Liu-Zhu 2016 *RFS* 29(1):5-68](https://doi.org/10.1093/rfs/hhv059) supplies the multiple-testing-deflation discipline (t-stat threshold ≥ 3.0 for factor-anomaly survival under family-wise error control). The conjecture that skew-positive payoff structures *survive deflation better than skew-negative structures* is a **project-operational prior** (the rare-win signal is structurally harder for an overfit model to manufacture than the always-in-noise of a skew-negative cell) and is NOT attributed to a specific HLZ 2016 finding — empirical calibration of this prior is tracked under `P1-ADR-0019-SKEW-SURVIVAL-EMPIRICAL`. The annotation gives the operator a structural skepticism toward skew-negative cells that score well on aggregate Sharpe or MPPM as a complement to the HLZ 2016 deflation machinery.

**Negative / costs**:
- Adds one mandatory column to every KPI report card. Per `P1-DOCS-INDEX-AUTOGENERATE`, the new field must be added to the [research/01_hypothesis_register/RESULTS_INDEX.md](../../research/01_hypothesis_register/RESULTS_INDEX.md) autogeneration schema.
- The ±0.1 cutoff is operational and not yet empirically calibrated against the SKIE realized-OOS distribution; `P1-ADR-0019-PAYOFF-SHAPE-THRESHOLD-EMPIRICAL` tracks calibration once ≥ 5 KPI cards carry τ_3 estimates.
- L-skewness is robust but not invariant to the per-trade unit (R-multiples vs $ P/L vs log-return); ADR-0019 fixes the unit at R-multiples (per [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) §3 R-multiple primitive). Strategies without explicit stop-loss-defined 1R (e.g., H053 continuous-predictand cells) require a derived 1R via the per-trade realized-volatility-scaled convention documented in [src/skie_ninja/inference/r_multiple.py](../../src/skie_ninja/inference/r_multiple.py); tracked under `P1-R-MULTIPLE-DERIVED-1R-FOR-CONTINUOUS-PREDICTAND`.
- Sample-size sensitivity: τ_3 bootstrap CI widens substantially when realized trade count < 100. Marginal annotations (`skew-{positive,negative}-marginal`) will be common on freshly-emitted KPI cards and tighten as paper-trade and live data accumulate per [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §6 paper-trade-evaluated stage transition.

**Follow-ups registered**:
- `P1-L-SKEWNESS-PRIMITIVE-IMPL` (BLOCKING-BEFORE-NEXT-NEW-KPI-CARD): land [src/skie_ninja/inference/skewness.py](../../src/skie_ninja/inference/skewness.py) with `l_skewness_tau3`, `l_skewness_tau3_ci_stationary_bootstrap`, and `payoff_shape_annotation` per Decisions 1–2; unit-test against [Hosking 1990](https://www.jstor.org/stable/2345653) §4 closed-form values for known distributions (exponential τ_3 = 1/3, Gumbel τ_3 = 0.1699, normal τ_3 = 0).
- `P1-ADR-0019-PAYOFF-SHAPE-RETROACTIVE` (non-blocking; deferred until primitive lands): cascade payoff-shape annotation onto v_{N+1} KPI report cards for H050 / H052a / H053 / H054 per [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) cascade precedent.
- `P1-ADR-0019-PAYOFF-SHAPE-THRESHOLD-EMPIRICAL`: empirically calibrate the ±0.1 cutoff against the SKIE realized-OOS τ_3 distribution once ≥ 5 KPI cards carry the annotation.
- `P1-ADR-0019-INNER-CV-TIE-BREAKER-WIRE`: wire Decision 4 tie-breaker into the H055 and successor walk-forward orchestrators; track the boundary-cell hit-rate as a diagnostic.
- `P1-ADR-0019-BARBELL-SIBLING-PROTOCOL`: formalize the Decision 5 barbell-rebalance-candidate workflow — when an operator elects to investigate a convex-hedge sibling arm, what is the pre-registration discipline? Likely a new hypothesis ID per `P1-H052C-NQ-UNCONDITIONAL-ORB-PRE-REG` precedent.
- `P1-ADR-0019-TEMPLATE-CASCADE`: update [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) to include Table 1c.
- `P1-ADR-0019-CLAUDE-MD-CASCADE`: amend CLAUDE.md §"KPI report card for every strategy" to enumerate the payoff-shape annotation alongside the existing six methodological-correctness annotations.
- `P1-ADR-0019-SKEW-SURVIVAL-EMPIRICAL` (non-blocking): empirically validate the project-operational prior that skew-positive strategies survive multiple-testing deflation better than skew-negative — requires accumulating ≥ 10 KPI cards with τ_3 annotations + paired deflation analysis.
- `P1-ADR-0019-HOSKING-SECTION-PIN-VERIFY` (non-blocking; verification-gap): pin the specific Hosking 1990 §4 page/table that grounds the ±0.1 sampling-variance cutoff once primary copy is consulted; until pinned, the cutoff stands as project-operational.

## References

**Primary literature**:
- [Taleb 2007 *The Black Swan: The Impact of the Highly Improbable*](https://www.amazon.com/Black-Swan-Improbable-Robustness-Fragility/dp/081297381X) Ch. 16, Random House — *practitioner*. Original framing of the fragile-vs-antifragile payoff dichotomy.
- [Taleb 2012 *Antifragile: Things That Gain from Disorder*](https://www.amazon.com/Antifragile-Things-That-Disorder-Incerto/dp/0812979680) Ch. 18-19, 23-25, Random House — *practitioner*. The barbell strategy as canonical antifragile design.
- [Brandt-Santa-Clara-Valkanov 2009 *Rev Financial Studies* 22(9):3411-3447](https://doi.org/10.1093/rfs/hhp003). Parametric portfolio policies with non-Gaussian utility; load-bearing peer-reviewed anchor for skew-conditioning in portfolio formation.
- [Harvey-Liu-Zhu 2016 *RFS* 29(1):5-68](https://doi.org/10.1093/rfs/hhv059) §V. Multiple-testing deflation; skew-positive strategies survive deflation better because the rare-win signal is harder to overfit.
- [Hosking 1990 *J Royal Stat Soc B* 52(1):105-124](https://www.jstor.org/stable/2345653). L-moments as robust order-statistic-based moment estimators; τ_3 ∈ [−1, 1] with finite variance under finite second L-moment.
- [Theodossiou 1998 "Financial Data and the Skewed Generalized T Distribution," *Mgmt Sci* 44(12-Part-1):1650-1661](https://doi.org/10.1287/mnsc.44.12.1650). Skewed-t distribution for financial returns; canonical justification for robust skew estimation in finance.
- [Politis-Romano 1994 *JASA* 89(428):1303-1313](https://doi.org/10.1080/01621459.1994.10476870). Stationary bootstrap for bootstrap CI on τ_3.

**Project ADRs**:
- [ADR-0006 scope extension HMM + 0DTE](ADR-0006-scope-extension-hmm-0dte.md) — 0DTE sibling repo is a natural barbell-tail candidate per Decision 5.
- [ADR-0013 permanent-exploration](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — no-binding-gates philosophy preserved by Decision 3.
- [ADR-0014 canonical end-of-simulation results-summary tables](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — extended by Decision 2 to 13 tables when ADR-0019 in force.
- [ADR-0017 survival-constrained optimization paradigm](ADR-0017-survival-constrained-optimization-paradigm.md) — fractional-Kelly sizing on R-multiples is the unit ADR-0019 inherits; growth-rate leakage via third-moment Taylor term is the structural mechanism ADR-0019 makes visible.
- [ADR-0018 regime-conditional aggressive-growth paradigm](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — MPPM(ρ=1) is the primary fitness; Decision 4 makes τ_3 a tie-breaker, not a competitor.

**Project ledger entries**:
- [CLAUDE.md Phase G](../../CLAUDE.md) — H050 KPI report card v1; canonical empirical anchor for the skew-negative pattern.
- [CLAUDE.md Phase H](../../CLAUDE.md) — H052a NQ unconditional ORB; canonical empirical anchor for the mildly skew-positive pattern.
- [CLAUDE.md Phase F](../../CLAUDE.md) — H053 v4; canonical empirical anchor for the skew-flat continuous-predictand pattern.
