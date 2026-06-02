# Memo — Foundations of the regime-switching meta-allocation closed loop

- **Date**: 2026-06-02
- **Status**: research synthesis (companion to [ADR-0029](../decisions/ADR-0029-regime-switching-meta-allocation-central-program.md))
- **Provenance**: two parallel literature-verification threads (2026-06-02); every DOI CrossRef- or publisher-resolved; corrections + unverifiable items flagged.
- **Purpose**: ground the two binding constraints (premature-deviation early warning; lucky/unlucky path-dependence) in primary literature, and give concrete implementation levers for the Phase P buildout.

---

## 1. Thrust 1 — leading early-warning detection (complement, not replacement, for BOCD)

### 1.1 Problem

BOCD ([Adams-MacKay 2007](https://arxiv.org/abs/0710.3742)) returns a posterior over run-length and confirms a changepoint only after post-change evidence concentrates — **lagging by construction**. We want a **leading** signal that fires while the strategy is still nominally in-regime, so the allocator pre-emptively de-risks (size-down) rather than waiting for confirmation to fully reallocate.

### 1.2 Three precursor families (all read on the per-session performance path)

**(a) Critical-slowing-down early-warning signals.** Near a fold/saddle-node bifurcation the system's recovery from perturbations slows, with statistical fingerprints **rising variance + rising lag-1 autocorrelation** ([Scheffer et al. 2009](https://doi.org/10.1038/nature08227), *Nature* 461:53-59 — canonical anchor). The operationalizable estimator toolbox — detrending, rolling-window variance + lag-1 AR, Kendall-τ trend test — is [Dakos et al. 2012](https://doi.org/10.1371/journal.pone.0041010) (*PLoS ONE* 7:e41010; the R `earlywarnings` reference paper). Tunable knobs: window width + detrending bandwidth + Kendall-τ trigger threshold.

> **Financial-path caveat (load-bearing).** [Guttal et al. 2016](https://doi.org/10.1371/journal.pone.0144198) (*PLoS ONE* 11:e0144198) find across DJIA/S&P/NASDAQ/DAX/FTSE that crashes show **rising variance but NO rising lag-1 AR** — financial meltdowns look noise-amplitude-driven, not slowing-recovery-driven. **Implication: weight variance over AR(1) on the performance path.** [Diks-Hommes-Wang 2019](https://doi.org/10.1007/s00181-018-1527-3) (*Empirical Economics* 57:1201-1228) found CSD before Black Monday 1987 but insignificant for 1997/2000/2008 — so this is a tripwire with a real false-negative rate, not an oracle. Honest prior for expected hit rate.

**(b) Sequential change detection (fires earlier than retrospective).** **CUSUM** ([Page 1954](https://doi.org/10.1093/biomet/41.1-2.100), *Biometrika* 41:100-115): accumulate the running sum of demeaned (or log-LR) per-session-excess-return increments; alarm when cumulative deviation from the recent minimum exceeds threshold `h`. Threshold `h` sets ARL-to-false-alarm vs detection-delay directly; reference value `k` sets the minimum drift it is tuned to catch. **GLR** ([Lorden 1971](https://doi.org/10.1214/aoms/1177693055), *Ann. Math. Stat.* 42:1897-1908 — the correct GLR origin, NOT the commonly mis-cited Lai surveys): for unknown decay magnitude, maximize the LR over candidate change-points and post-change magnitudes. **Shiryaev-Roberts** (sums rather than maximizes LRs; faster for distant-horizon changes) — [Shiryaev 1963](https://doi.org/10.1137/1108002) (*Theory Probab. Appl.* 8(1):22-46, DOI 10.1137/1108002 — SIAM retroactively minted).

**(c) Drawdown-velocity / time-under-water.** [Bailey & López de Prado 2015](https://doi.org/10.21314/JOR.2015.317) (*J. Risk* 18(2):61-93) — closed-form quantiles for max-drawdown + time-under-water under first-order serial correlation; the "triple penance" rule (expected recovery ≈ 3× time-to-max-loss) gives a *distribution-calibrated* stop threshold rather than an arbitrary drawdown limit (ignoring serial correlation understates downside up to ~70%). Signal-agnostic — reads the wealth path directly; cheapest leading layer; orthogonal to (a)/(b) which read the return-increment distribution.

**(d) Finance-specific anticipation (optional, network-based).** [Gatfaoui & de Peretti 2019](https://doi.org/10.1038/s41598-019-42223-9) (*Sci. Reports* 9:5671) — "flickering" (intermittent node switching in a market causal network) as a resilience-loss precursor; complement to CSD per Scheffer 2012. Deferred — requires cross-instrument network construction beyond the per-arm performance path.

### 1.3 Architecture

Two-tier: precursor layer (variance-EWS + CUSUM/SR scalar + drawdown-velocity band) = low-confidence, short-lead **partial-de-risk tripwire** tuned for lead time at accepted higher false-positive rate; BOCD posterior crossing = high-confidence **full-reallocation confirmation**. A precursor false positive costs a partial de-risk reversed if BOCD never confirms — small and bounded. Every threshold calibrated on a pre-OOS holdout per ADR-0027 §D-2 + the no-magic-number rule. Central tradeoff (lead time ↔ false-positive rate) IS the calibration objective.

---

## 2. Thrust 2 — path-dependence under aggressive sizing (the lucky/unlucky problem)

### 2.1 Why it happens (the theoretical core)

Multiplicative wealth dynamics are **non-ergodic**: the **ensemble average** (mean across parallel Monte-Carlo universes) ≠ the **time average** (what a single trader compounding over time experiences) ([Peters 2019](https://doi.org/10.1038/s41567-019-0732-0), *Nature Physics* 15:1216-1221). Evaluating a gamble correctly means computing the time-average growth rate under the *dynamics actually played* — for multiplicative wealth, the growth rate of log-wealth, which recovers Kelly with no exogenous risk-aversion parameter ([Peters & Gell-Mann 2016](https://doi.org/10.1063/1.4940236), *Chaos* 26:023103).

**Direct consequence for the project:** the +2,690% Monte-Carlo *ensemble mean* is the average over parallel universes — NOT the operator-experienced quantity. Over a long horizon the operator's realized growth rate converges a.s. to the **time-average growth rate** g = E[log(1+r)] (the project's MPPM(ρ=1) primitive computes this exactly); the **median terminal-wealth path** is the finite-horizon operator-facing central estimate (= exp(g·T)·W₀ exactly only under lognormality; the two can diverge under the project's skew-positive τ₃≈+0.74 regime — so report both, do not equate them). Super-Kelly *depresses* g while inflating the ensemble mean; the jackpot-tail-and-ruin dichotomy is exactly non-ergodicity. **Reporting fix (ADR-0029 §D-3.1): headline two figures — the median equity path AND MPPM(ρ=1); demote the ensemble mean to a caveated annotation.**

### 2.2 Mitigation levers

**(a) Kelly ceiling.** Full-Kelly (multiplier 1.0) is the time-average-growth optimum; super-Kelly is **uniformly dominated in the growth-security plane** — more drawdown AND less time-average growth ([MacLean-Thorp-Ziemba 2011](https://doi.org/10.1142/7598), edited volume). The risk-constrained Kelly optimum is *always fractional* and parametrized by a single risk knob ([Busseti-Ryu-Boyd 2016](https://doi.org/10.3905/joi.2016.25.3.118), *J. Investing* 25(3):118-134; convex program). **Lever: cap the promotable Kelly multiplier at ≤ 1.0; choose the fraction from a target P(ruin) via the convex program.** Super-Kelly stays a sandbox-exploration tool, annotated `super-kelly-time-average-dominated`.

**(b) Drawdown-constrained / cushion-proportional sizing.** [Grossman & Zhou 1993](https://doi.org/10.1111/j.1467-9965.1993.tb00044.x) (*Math. Finance* 3:241-276): keep wealth above a fixed fraction of the running maximum; optimal exposure ∝ cushion (current − floor) — exposure → 0 as wealth → floor, → up on new highs. (Caveat: Cherny-Obłój later showed non-optimal in some settings; cite as *an* anchor, the project's `drawdown_constrained_kelly` lineage.)

**(c) CPPI floor-ratcheting.** [Black & Jones 1987](https://doi.org/10.3905/jpm.1987.409131) (*JPM* 14(1):48-51): exposure = m × (Wealth − Floor); the frictionless floor is never breached. Rigorous-frictions treatment [Black & Perold 1992](https://doi.org/10.1016/0165-1889(92)90043-E) (*JEDC* 16:403-426): optimal under HARA/subsistence utility; the floor can **gap through** under discrete trading + gaps (≈ the residual ruin the project's MC shows). **Lever: floor = protected fraction (e.g. ratchet to a fraction of running peak to lock in gains); buffer above the 50% ruin line to absorb gap-through.**

**(d) Time-diversification — the ergodicity-sanctioned aggressive route.** [Peters & Adamou 2022](https://doi.org/10.1098/rsta.2020.0425) (*Phil. Trans. R. Soc. A* 380:20200425, peer-reviewed; working-paper [arXiv:1506.03414](https://arxiv.org/abs/1506.03414)): pooling across cooperating entities reduces each one's multiplicative variance; since variance depresses time-average growth (not ensemble mean), pooling *raises* every participant's long-run growth rate. **Lever: run N de-correlated concurrent arms and pool P&L — variance ~1/N pulls the realized path toward the ensemble mean. This is the structural cure for the lucky/unlucky dichotomy, and it is the meta-portfolio (ADR-0020 / MPV-lineage).** Independence is load-bearing — compute the cross-arm correlation matrix first.

**(e) Joint simultaneous-bet Kelly.** [Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x) (*BSTJ* 35:917-926) + Thorp chapters in MacLean-Thorp-Ziemba 2011: with k concurrent independent favorable bets, solve the *joint* log-growth maximization — per-bet fractions are SMALLER than standalone Kelly, total exposure well below the naïve sum. **Lever: when M arms signal together, size at the joint-Kelly fraction with a total-concurrent-exposure cap — never standalone × M (which over-bets back into ruin).** *Flagged: no single canonical "simultaneous-bet Kelly" primary paper exists — this chain is the citable basis.*

---

## 3. Synthesis — the explain-and-mitigate spine

| Constraint | Theoretical core | Implementation levers |
|---|---|---|
| Detection lag (premature deviation) | critical-slowing-down + sequential detection | variance-weighted EWS + CUSUM/SR + drawdown-velocity tripwire → partial de-risk; BOCD = confirmation |
| Lucky/unlucky path | non-ergodicity (time ≠ ensemble) | report median not mean; Kelly ≤ 1.0 promotable; CPPI floor-ratchet; N concurrent de-correlated arms (variance ~1/N); joint-Kelly cap |

**The non-obvious conclusion:** the route to durable aggressive upside is NOT higher Kelly (which ergodicity proves reduces the operator-experienced growth) — it is **many concurrent de-correlated arms with the realized path pulled toward the ensemble by pooling**. The operator's regime-switching-over-a-reusable-library instinct is precisely the ergodicity-sanctioned mechanism. MPV2 (ADR-0029 §D-4) is the experiment that tests whether it delivers a forward edge over 1/N.

## Correction / verification flags

- Ergodicity-economics textbook = **LML Press** (ISBN 9781068649134), NOT World Scientific.
- **No single "simultaneous-bet Kelly" primary paper** — use Kelly 1956 + MacLean-Thorp-Ziemba 2011 chain.
- **Shiryaev 1963** Shiryaev-Roberts — DOI 10.1137/1108002 (SIAM retroactively minted; the earlier "no era-DOI" assumption was incorrect, corrected per the 2026-06-02 literature-check).
- Gatfaoui-de Peretti 2019 + the two §1.2(d) follow-on finance EWS papers are search/CrossRef-attested; Scheffer 2012 *Science* 338:344-348 (DOI 10.1126/science.1225244) verified for the flickering extension.
