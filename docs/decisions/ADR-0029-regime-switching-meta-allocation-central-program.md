---
id: ADR-0029
title: Regime-switching meta-allocation closed-loop as the central research program
status: accepted
date: 2026-06-02
decision-owner: operator (SKIE)
supersedes: []
related:
  - ADR-0013  # permanent-exploration / non-loss reusable library (ENABLER)
  - ADR-0017  # survival-constrained metric vector (time-average-flavored)
  - ADR-0018  # aggressive-growth: MPPM(ρ=1), Kelly grid, BOCD, switching-bandit
  - ADR-0020  # meta-portfolio orchestrator (PROMOTED to central — it IS the allocator)
  - ADR-0024  # H062 aggressive-growth canonical; Lo 2004 AMH philosophy
  - ADR-0026  # §0 3-component KPI header (AMENDED: headline = median/time-average)
  - ADR-0027  # operational discipline / genetic-successor / bounded exploration
---

# ADR-0029 — Regime-switching meta-allocation closed-loop as the central research program

> **Banner.** This ADR re-states the project's *center of gravity*. Per-hypothesis pre-registration → backtest → KPI work continues unchanged, but is reframed as **arm-library cultivation feeding a capital allocator**. The allocator — not the individual arm — becomes the primary NinjaScript-terminus target (ADR-0013 §5). No prior ADR is superseded or deleted; §D-5 enumerates what is preserved / amended / reframed. This ADR is durable: it exists so future independent sessions read regime-switching meta-allocation as THE objective without manual context re-invocation.

## Context

### The external-validity problem (the motivating finding)

Every emitted KPI card to date shows that per-hypothesis edge is **market-climate-specific**, not a dispassionate, regime-invariant property:

- **Phase O.7.5**: H062's headline +208.8% basket decomposes to +96.9% concentrated in **261 of 3,611 session-days (7.2%)** — the early-2020 COVID-volatility burst. The walk-forward per-fold inferential reality is negative (H062 family cum-MPPM ≈ −29).
- **Phase O.18** (`INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS`): MGC swings +87% / −94% / +69% across cell-Kelly-regime configurations; the dominant driver is the **hypothesis-family-mechanic × OOS-window-regime composite**, not a stable signal.
- **Phase O.7 synthesis**: across ~120 cell-Kelly-config tests on the H062 family, exactly **1 cell** achieves MPPM CI strictly positive (0.83% — consistent with the null of zero mean-edge).

A single arm fitted to one climate has no forward live/paper external validity. This is the [Lo 2004](https://doi.org/10.3905/jpm.2004.442611) Adaptive Markets Hypothesis playing out empirically (ADR-0024 §D-7): **strategy decay is the null, not the exception**, and decayed strategies re-emerge in their native regime.

### The operator's 2026-06-02 directive

Reframe the project around a closed loop: (1) deploy $10K into a strategy in its favorable climate; (2) capture geometric upside; (3) detect when the climate changes and the strategy is no longer viable; (4) retrain/reallocate to a different hypothesis; (5) cycle. The operator's mental model — hypotheses are *reusable* and particular climates are *optimal for particular hypotheses* (range-bound MR scalping vs parabolic-breakout) — is the correct organizing principle. It is already instantiated in the arm library: **H055** = range-bound wick-rejection MR (many scalps, avg_loss/avg_win = 2.39×); **H062/H065** = breakout (win rate ~27–31%, skew-positive τ₃ = +0.74, fat right tail).

### Two binding constraints (the 2026-06-02 analysis)

1. **Detection lag.** The BOCD changepoint detector ([Adams-MacKay 2007](https://arxiv.org/abs/0710.3742), ADR-0018 §D-3) confirms a regime shift only *after* the post-change evidence accumulates — by construction lagging. The closed loop eats the transition drawdown. The operator asks: can we capture *premature deviation from profit* before confirmation?

2. **Path-dependence under aggressive sizing.** Under super-Kelly the single realized equity path diverges sharply from the Monte-Carlo ensemble: the same machinery that produced +2,690% on one historical path produces ruin (P(ruin)=100% at the 50% threshold) on the typical path. The operator is willing to explore routes to navigate the lucky/unlucky path.

### What already exists (the assembled-from-pieces observation)

BOCD ([bocd.py](../../src/skie_ninja/inference/bocd.py), [bocd_live.py](../../src/skie_ninja/inference/bocd_live.py)); switching-bandit D-UCB/SW-UCB/GLR-klUCB/EXP3.S ([switching_bandit.py](../../src/skie_ninja/meta/switching_bandit.py)); meta-portfolio MPV1 (ADR-0020); the non-loss reusable hypothesis library (ADR-0013 §4.1); drawdown-constrained Kelly + risk-of-ruin primitives ([src/skie_ninja/sizing/](../../src/skie_ninja/sizing/), [risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py)). The closed loop was never assembled into a **forward-validated** system. MPV1's current verdict: all bandit-vs-1/N CIs cover zero — no allocator has yet beaten equal-weight at 95%.

## Decision

### D-1 — Center of gravity

The project's organizing objective is the **regime-switching meta-allocation closed loop**: a capital allocator over the non-loss hypothesis library that (i) sizes into the currently-favored arm, (ii) detects decay via a two-tier early-warning + confirmation stack (D-2), (iii) reallocates via the switching-bandit (ADR-0018 §D-4), and (iv) cycles. Per-hypothesis work is **arm-library cultivation**. The allocator (the MPV-lineage meta-portfolio, ADR-0020) is the primary NinjaScript-terminus target per ADR-0013 §5; per-hypothesis NinjaScript remains operator-discretionary (2026-05-04 standing directive).

### D-2 — Two-tier decay detection (Thrust 1: premature-deviation early warning)

Add a **leading** early-warning tier above BOCD's **lagging** confirmation. Three precursor signals, all read on the per-session performance path the allocator already maintains, feeding a **pre-emptive partial de-risk** (size-down, not exit):

1. **Critical-slowing-down EWS** — rolling **variance** + lag-1 **autocorrelation**, which rise as a dynamical system approaches a critical transition ([Scheffer et al. 2009](https://doi.org/10.1038/nature08227); estimator toolbox [Dakos et al. 2012](https://doi.org/10.1371/journal.pone.0041010)). **Financial-path caveat ([Guttal et al. 2016](https://doi.org/10.1371/journal.pone.0144198)): weight variance over AR(1)** — on market series variance rises before crashes but lag-1 AR often does not. Trigger = Kendall-τ trend of the indicator over the trailing window. Mixed-evidence honesty: [Diks-Hommes-Wang 2019](https://doi.org/10.1007/s00181-018-1527-3) found CSD before 1987 but insignificant for recent crises — so this layer is a tripwire, not an oracle.
2. **Sequential change detection** — a **CUSUM** ([Page 1954](https://doi.org/10.1093/biomet/41.1-2.100)) or Shiryaev-Roberts scalar on per-session excess-return-vs-recent-in-regime-mean; **GLR** when the decay magnitude is unknown ([Lorden 1971](https://doi.org/10.1214/aoms/1177693055) — the canonical GLR origin, *Ann. Math. Stat.* 42(6), not the commonly mis-cited Lai surveys). The alarm threshold is the single knob mapping detection-delay to false-alarm rate (ARL₀).
3. **Drawdown-velocity / time-under-water** — deviation-from-running-peak band ([Bailey & López de Prado 2015](https://doi.org/10.21314/JOR.2015.317) "triple penance"): distribution-calibrated stop quantiles under serial correlation. Signal-agnostic (reads the wealth path directly); the cheapest leading layer.

**Wiring**: precursor crossing → partial de-risk; BOCD posterior crossing → full reallocation. The cost is explicit and bounded — a precursor false positive is a partial de-risk reversed if BOCD never confirms. All thresholds (window widths, Kendall-τ / z-score / ARL₀ / confidence-band levels) are **empirically calibrated on a pre-OOS holdout, never hand-set**, per the project no-magic-number rule (CLAUDE.md §"Parameter & Prompt Selection") and ADR-0027 §D-2. The central tradeoff — lead time vs false-positive rate — is the calibration objective. The precursor layer's success metric is **detection-lead relative to the BOCD-confirmed changepoint** on the holdout (a relative-timing statistic) — "leading" means "fires before BOCD confirms," NOT "forecasts an unrealized future change" (CSD is a coincident-to-slightly-leading fingerprint, insignificant for 1997/2000/2008 per Diks-Hommes-Wang 2019); the layer is reported as a tripwire, not standalone forecast skill.

### D-3 — Path-dependence resolution via ergodicity (Thrust 2: navigating lucky vs unlucky)

1. **Time-average vs ensemble-average as the canonical lens.** Multiplicative wealth dynamics are **non-ergodic**: the ensemble average (mean across parallel Monte-Carlo universes) is NOT the growth rate a single trader compounding over time realizes — over a long horizon the single path's realized growth rate converges almost surely to the **time-average growth rate** g = E[log(1+r)], which differs from the ensemble-mean rate because the latter is dominated by a vanishing-probability jackpot tail ([Peters 2019](https://doi.org/10.1038/s41567-019-0732-0); [Peters & Gell-Mann 2016](https://doi.org/10.1063/1.4940236)). At finite horizon the operator experiences one draw centered on the **median terminal-wealth path** (the operator-facing central estimate; it equals exp(g·T)·W₀ exactly only under lognormality and can diverge from the exact time-average growth under the project's skew-positive τ₃≈+0.74 regime — so the two are reported separately, not equated). **KPI-reporting amendment (amends ADR-0026 §D-1 + ADR-0013 §3.1):** the §0 3-component header + forward-projection block report **two** headline figures — the **median terminal-wealth equity path** (operator-facing) and **MPPM(ρ=1)** (the exact time-average growth rate, already a project primitive at [mppm.py](../../src/skie_ninja/inference/mppm.py)) — and demote the ensemble mean to a secondary annotation carrying an explicit non-ergodicity caveat. The +2,690% ensemble-mean class of figure is never again presented as the operator-experienced outcome.

2. **Kelly ceiling for promotable cells.** Full-Kelly (multiplier 1.0) is the **time-average-growth optimum** — it maximizes the strictly-concave expected-log-growth g(f) = E[log(1+f·R)] on the *true* distribution; multipliers > 1.0 lie on its decreasing branch (and turn growth negative far enough out), and with estimation error the practical optimum shrinks *below* the plug-in full-Kelly (the fractional-Kelly-for-uncertainty argument — an additional reason the ceiling is at-most full-Kelly). Super-Kelly is *uniformly dominated in the growth-security plane* — it pays *both* more drawdown *and* less time-average growth ([MacLean-Thorp-Ziemba 2011](https://doi.org/10.1142/7598); [Busseti-Ryu-Boyd 2016](https://doi.org/10.3905/joi.2016.25.3.118), whose risk-constrained optimum is always *fractional* Kelly). **Resolution that preserves ADR-0018's grid:** super-Kelly cells {1.5, 2.0, 2.5} remain admissible for **sandbox exploration** (the ADR-0018 §D-2 grid is preserved verbatim — they demonstrate the regime-burst-capture *mechanism*), but carry the new mandatory `super-kelly-time-average-dominated` annotation and **may not be the promoted configuration past paper-trade without explicit operator override.** The promotable ceiling is full-Kelly; the fraction is chosen from a target P(ruin) via the Busseti-Ryu-Boyd convex program, not set ad hoc.

3. **CPPI floor-ratcheting** — convert the operator's profit-lock-in intuition into a citable rule: size aggressive exposure in the **cushion above a peak-referenced floor**, exposure = m × (equity − floor) ([Black & Jones 1987](https://doi.org/10.3905/jpm.1987.409131); rigorous-frictions treatment [Black & Perold 1992](https://doi.org/10.1016/0165-1889(92)90043-E)). Ratchet the floor to a fraction of the running peak (lock in gains on new highs). **Buffer the floor above the 50% ruin line** to absorb discrete-trade gap-through (Black-Perold shows the floor can gap under discrete trading — the residual ruin the project's MC still shows). The CPPI multiplier m and the floor-buffer magnitude are **empirically calibrated on the holdout** (the buffer sized to cover a high quantile of the observed discrete-trade / overnight gap distribution), never hand-set; the 50% ruin line itself is inherited-and-principled from ADR-0017 §4.2. The continuous parent is the cushion-proportional rule of [Grossman & Zhou 1993](https://doi.org/10.1111/j.1467-9965.1993.tb00044.x), already cited by the project's `drawdown_constrained_kelly` primitive.

4. **Time-diversification — the ergodicity-sanctioned route to aggressive upside.** Run **N de-correlated concurrent arms and pool P&L**: pooling reduces the variance of the multiplicative process ~1/N, and because fluctuations have a net-negative effect on the time-average growth rate, pooling *raises* every arm's time-average growth without changing the ensemble mean — the realized path converges toward the ensemble ([Peters & Adamou 2022](https://doi.org/10.1098/rsta.2020.0425), peer-reviewed; working-paper form [arXiv:1506.03414](https://arxiv.org/abs/1506.03414)). This is the **structural cure for the lucky/unlucky dichotomy** and is exactly the meta-portfolio object (ADR-0020 / MPV-lineage). **Joint-Kelly sizing** ([Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x); Thorp's chapters in MacLean-Thorp-Ziemba 2011): when M arms signal simultaneously, size each at the *joint*-Kelly fraction (cap total concurrent exposure), NOT standalone × M — naïve summation over-bets and re-introduces ruin. **Two precisions:** the ~1/N reduction holds only for de-correlated equal-variance arms — with residual positive correlation it floors at the average pairwise covariance (the project's ES-NQ ≈ +0.85 collapses equity-index effective breadth), so independence is the load-bearing assumption and the cross-arm correlation matrix (`P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE`) must be computed first; and the Peters-Adamou growth-lift requires **genuine P&L pooling** (a shared rebased bankroll re-divided across arms), NOT parallel siloed sub-accounts.

### D-4 — MPV2 as the canonical forward-validation experiment

Elevate `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` to **BLOCKING-BEFORE-ANY-CLOSED-LOOP-EXTERNAL-VALIDITY-CLAIM**. Re-emit every arm's per-session return arrays (current MPV1 uses per-fold MPPMs — too coarse); build the allocator on per-session reward sequences. The falsifiable claim at the center of the paradigm:

> **Does the closed-loop allocator — D-2 early-warning + D-3 ergodicity-sanctioned sizing + ADR-0018 §D-4 switching-bandit, on the per-session reward sequences — beat BOTH buy-and-hold AND equal-weight 1/N out-of-sample?**

1/N is the load-bearing benchmark, not a strawman: [DeMiguel-Garlappi-Uppal 2009](https://doi.org/10.1093/rfs/hhm075) shows 1/N is hard to beat under estimation noise. MPV2 decides whether regime-switching meta-allocation has forward external validity. If the allocator does not beat 1/N OOS, the honest paradigm conclusion is recorded (per ADR-0013 non-loss; per Lo 2004 the answer may itself be regime-dependent).

**Causal-alignment invariant (BLOCKING for the MPV2 claim).** The forward-validation is correctly specified at the inference layer, but the per-session reward matrix is exposed to two look-ahead vectors visible in the MPV1 predecessor (`t mod n` cycle-resampling; an ex-post `oracle_baseline` over full-sample arm means). MPV2 MUST satisfy: (i) arm-k's session-t reward is computed from arm-k positions sized by parameters **frozen on data strictly preceding t** (walk-forward-frozen, not re-fitted on the evaluation window — so the allocator does not inherit arm-level look-ahead from per-fold inner-CV-selected MPPMs); (ii) the 1/N and buy-and-hold benchmarks are built on the **identical** per-session matrix with no ex-post arm selection; (iii) the full-sample oracle remains a labeled **non-tradeable diagnostic**, excluded from the beat-target. MPV2 inherits the Cycle-4 fold-boundary / look-ahead leak canaries ([src/skie_ninja/backtest/](../../src/skie_ninja/backtest/)). A look-ahead bug here would invalidate the central claim even with a correct inference design.

### D-5 — Reconciliation of prior ADRs (the "unblock" requirement)

No ADR is superseded. Explicit preserved / amended / reframed:

| ADR | Disposition under ADR-0029 |
|---|---|
| **ADR-0013** permanent-exploration / non-loss / NinjaScript terminus | **PRESERVED + reframed.** The non-loss reusable arm library is the *enabler* of regime-reuse. Amended only: the NinjaScript terminus target extends to the meta-allocator; per-hypothesis terminus stays operator-discretionary. |
| **ADR-0017** survival-constrained metric vector | **PRESERVED + reinforced.** Ergodicity (D-3) is the theoretical foundation for the survival-constrained vector — terminal-wealth-q05 is a time-average-flavored statistic; the paradigm explains *why* it is the right primary. |
| **ADR-0018** aggressive growth / Kelly grid / BOCD / switching-bandit | **PRESERVED.** Grid VALUES {0.25…2.5} preserved verbatim (sandbox exploration); D-3.2 ADDS a promotable-cell ceiling (full-Kelly) + a second annotation — these *tighten promotion eligibility*, they do not alter the grid. The new `super-kelly-time-average-dominated` annotation (ergodicity-mechanism flag) **co-exists with** ADR-0018's existing `super-kelly-operator-discretionary` (literature-evidence flag); neither supersedes the other. BOCD + switching-bandit become the closed loop's confirmation + reallocation layers. |
| **ADR-0020** meta-portfolio orchestrator | **PROMOTED from peripheral to central — it IS the allocator.** Status remains `proposed`; MPV2 (D-4) is its forward-validation. |
| **ADR-0024** H062 aggressive-growth canonical / Lo 2004 AMH | **PRESERVED.** AMH is the philosophical parent of regime-switching. |
| **ADR-0026** §0 3-component KPI header | **AMENDED per D-3:** headline figure = median / time-average path; ensemble mean demoted to annotation. |
| **ADR-0027** bounded exploration / genetic successor | **PRESERVED + applied.** Early-warning + ergodicity primitives are infrastructure; the closed-loop assembly is a present-tense thrust under the §D-5 time-budget split. |

### D-6 — Project-objective amendment

CLAUDE.md §"Research philosophy" gains a **center-of-gravity** statement (this commit) so future independent sessions read regime-switching meta-allocation as THE objective. The per-hypothesis-exhaustive-exploration framing is retained as the arm-cultivation sub-program beneath it.

## Alternatives considered

- **(A) Crank Kelly higher to force 1000%.** Rejected. Ergodicity (D-3) proves super-Kelly *reduces* the time-average growth the operator experiences; it inflates the ensemble mean (jackpot tail) while ruining the typical path. The aggressive-upside goal is met by time-diversification (D-3.4), not higher leverage.
- **(B) Keep per-hypothesis terminus as the center.** Rejected — Phase O.7.5 shows each arm is climate-specific with no forward external validity; only an adaptive allocator can survive regime change.
- **(C) Rely on BOCD alone for switching.** Rejected — lagging; eats the transition drawdown (constraint 1). D-2 adds the leading tier.
- **(D) Static equal-weight 1/N (no switching).** NOT rejected — it is the BENCHMARK the closed loop must beat (D-4). DeMiguel-Garlappi-Uppal 2009 makes this a stringent bar.
- **(E) Defer until live fee data.** Rejected — the forward-validation question (D-4) is answerable on the existing OOS substrate; cost-realism is layered per ADR-0025 / ADR-0028.

## Consequences

**New primitives (BLOCKING-BEFORE-CLOSED-LOOP-RUN; see Phase P buildout):**

| Follow-up | Primitive |
|---|---|
| `P1-EARLY-WARNING-DETECTOR-PRIMITIVE` | EWS (variance + lag-1 AR, Kendall-τ) + CUSUM/SR + drawdown-velocity, at `src/skie_ninja/inference/early_warning.py` |
| `P1-CPPI-FLOOR-RATCHET-SIZING-PRIMITIVE` | cushion-proportional sizing + peak-referenced ratcheting floor, in `src/skie_ninja/sizing/` |
| `P1-JOINT-KELLY-CONCURRENT-SIZING-PRIMITIVE` | joint simultaneous-bet Kelly with total-exposure cap |
| `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` | (elevated) per-session reward emission across all arms + allocator on per-session sequences |
| `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE` | (elevated; independence is load-bearing for D-3.4) |

**New KPI annotations** (cascade to ADR-0014 §3.2 / glossary / template): `super-kelly-time-average-dominated` (co-exists with ADR-0018's `super-kelly-operator-discretionary`; see §D-5), `early-warning-{armed, fired, n/a}`, `time-average-vs-ensemble-gap-{small, large}` (gap = ensemble-mean ÷ median-path terminal wealth).

**Cascade follow-ups:** `P1-ADR-0029-CLAUDE-MD-CASCADE` (closed this commit), `P1-ADR-0029-DECISIONS-README-CASCADE` (closed this commit), `P1-ADR-0029-GLOSSARY-CASCADE`, `P1-ADR-0029-TEMPLATE-CASCADE` (median-headline + new annotations), `P1-ADR-0029-KPI-MEDIAN-HEADLINE-RETROACTIVE` (re-present existing v(N) cards' §0 headers as median/time-average).

**Audit-remediate-loop:** Round 1 — parallel literature-check (citation transcription + no new unverified sources) + quant-auditor (ergodicity / EWS / CUSUM / Kelly-ceiling method-correctness). Trail: [docs/audits/audit_trail_2026-06-02_adr-0029-regime-switching-central-program.md](../audits/audit_trail_2026-06-02_adr-0029-regime-switching-central-program.md).

## References

All DOIs CrossRef- or publisher-resolved by the two 2026-06-02 research threads; corrections flagged inline.

**Adaptive markets / regime philosophy**
- Lo, A.W. (2004). "The Adaptive Markets Hypothesis." *J. Portfolio Management* 30(5):15-29. DOI [10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611).

**Thrust 1 — early-warning / change detection**
- Scheffer, M., et al. (2009). "Early-warning signals for critical transitions." *Nature* 461(7260):53-59. DOI [10.1038/nature08227](https://doi.org/10.1038/nature08227).
- Dakos, V., et al. (2012). "Methods for Detecting Early Warnings of Critical Transitions in Time Series Illustrated Using Simulated Ecological Data." *PLoS ONE* 7(7):e41010. DOI [10.1371/journal.pone.0041010](https://doi.org/10.1371/journal.pone.0041010).
- Guttal, V., et al. (2016). "Lack of Critical Slowing Down Suggests that Financial Meltdowns Are Not Critical Transitions…" *PLoS ONE* 11(1):e0144198. DOI [10.1371/journal.pone.0144198](https://doi.org/10.1371/journal.pone.0144198). [variance > AR(1) on financial paths]
- Diks, C., Hommes, C. & Wang, J. (2019). "Critical slowing down as an early warning signal for financial crises?" *Empirical Economics* 57(4):1201-1228. DOI [10.1007/s00181-018-1527-3](https://doi.org/10.1007/s00181-018-1527-3). [mixed evidence — honest prior]
- Page, E.S. (1954). "Continuous Inspection Schemes." *Biometrika* 41(1-2):100-115. DOI [10.1093/biomet/41.1-2.100](https://doi.org/10.1093/biomet/41.1-2.100). [CUSUM]
- Lorden, G. (1971). "Procedures for Reacting to a Change in Distribution." *Ann. Math. Stat.* 42(6):1897-1908. DOI [10.1214/aoms/1177693055](https://doi.org/10.1214/aoms/1177693055). [GLR origin]
- Bailey, D.H. & López de Prado, M. (2015). "Stop-outs under serial correlation and the triple penance rule." *J. Risk* 18(2):61-93. DOI [10.21314/JOR.2015.317](https://doi.org/10.21314/JOR.2015.317).
- Adams, R.P. & MacKay, D.J.C. (2007). "Bayesian Online Changepoint Detection." [arXiv:0710.3742](https://arxiv.org/abs/0710.3742). [BOCD — confirmation layer]
- Shiryaev, A.N. (1963). "On Optimum Methods in Quickest Detection Problems." *Theory Probab. Appl.* 8(1):22-46. DOI [10.1137/1108002](https://doi.org/10.1137/1108002). [Shiryaev-Roberts origin; SIAM retroactively minted the DOI — the draft's prior "no era-DOI" flag was itself incorrect, per the 2026-06-02 literature-check.]

**Thrust 2 — ergodicity / Kelly / floor protection / diversification**
- Peters, O. (2019). "The ergodicity problem in economics." *Nature Physics* 15(12):1216-1221. DOI [10.1038/s41567-019-0732-0](https://doi.org/10.1038/s41567-019-0732-0).
- Peters, O. & Gell-Mann, M. (2016). "Evaluating gambles using dynamics." *Chaos* 26(2):023103. DOI [10.1063/1.4940236](https://doi.org/10.1063/1.4940236).
- Peters, O. & Adamou, A. (2022). "The ergodicity solution of the cooperation puzzle." *Phil. Trans. R. Soc. A* 380(2227):20200425. DOI [10.1098/rsta.2020.0425](https://doi.org/10.1098/rsta.2020.0425). [pooling raises time-average growth]
- Kelly, J.L. (1956). "A New Interpretation of Information Rate." *Bell Syst. Tech. J.* 35(4):917-926. DOI [10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x).
- MacLean, L.C., Thorp, E.O. & Ziemba, W.T. (eds.) (2011). *The Kelly Capital Growth Investment Criterion: Theory and Practice* (edited volume). World Scientific. DOI [10.1142/7598](https://doi.org/10.1142/7598).
- Grossman, S.J. & Zhou, Z. (1993). "Optimal Investment Strategies for Controlling Drawdowns." *Mathematical Finance* 3(3):241-276. DOI [10.1111/j.1467-9965.1993.tb00044.x](https://doi.org/10.1111/j.1467-9965.1993.tb00044.x).
- Busseti, E., Ryu, E.K. & Boyd, S. (2016). "Risk-Constrained Kelly Gambling." *J. Investing* 25(3):118-134. DOI [10.3905/joi.2016.25.3.118](https://doi.org/10.3905/joi.2016.25.3.118). (preprint [arXiv:1603.06183](https://arxiv.org/abs/1603.06183))
- Black, F. & Jones, R.W. (1987). "Simplifying portfolio insurance." *J. Portfolio Management* 14(1):48-51. DOI [10.3905/jpm.1987.409131](https://doi.org/10.3905/jpm.1987.409131). [CPPI]
- Black, F. & Perold, A.F. (1992). "Theory of constant proportion portfolio insurance." *J. Economic Dynamics & Control* 16(3-4):403-426. DOI [10.1016/0165-1889(92)90043-E](https://doi.org/10.1016/0165-1889(92)90043-E).
- DeMiguel, V., Garlappi, L. & Uppal, R. (2009). "Optimal Versus Naive Diversification: How Inefficient Is the 1/N Portfolio Strategy?" *Review of Financial Studies* 22(5):1915-1953. DOI [10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075). [1/N benchmark]
- *Correction flagged:* the ergodicity-economics textbook (Peters & Adamou, *An Introduction to Ergodicity Economics*, 2025, ISBN 9781068649134) is **LML Press, not World Scientific**. *Absence flagged:* no single canonical "simultaneous-bet Kelly" primary paper exists — use the Kelly 1956 + MacLean-Thorp-Ziemba 2011 (Thorp chapters) chain.
