---
id: ADR-0018
title: Regime-conditional aggressive-growth paradigm — MPPM-fitness, Kelly grid-search, BOCD decay detection, switching-bandit meta-strategy
status: proposed
date: 2026-05-12
---

## Context

### Empirical motivation

Three converging empirical observations from the 2026-04-30 → 2026-05-08 production-run cohort motivate a paradigm-level reframing of the SKIE-Universe fitness function and capital-allocation policy.

**Observation 1 — H050 catastrophic OOS is a decay event, not an alpha failure.** The H050 KPI report card v1 ([research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md), run_id `31d23ecd8e3842dd8ebd5687ce9c91d5`, 2026-05-04) emitted T_H050 = SR_gated − SR_uncond at ES −0.0371 [−0.041, −0.034] and NQ −0.0219 [−0.025, −0.019] with LW2008 differential CIs excluding zero on the negative side on both symbols. Realized $10K equity over the 2024–2025 OOS test fold: ES gated −81.0%, NQ gated −84.2%. The unconditional (HMM-ungated) arms were near-flat on both. The hypothesis-of-record verdict was clean: HMM regime-gating *actively harms* the 1-min ES/NQ directional signal on the OOS fold.

Re-examined under the framing of this ADR, the H050 outcome is consistent with two distinct causal stories. (a) The signal carried no alpha at any point and the gated arm's losses are amplified noise. (b) The signal was profitable on the 2020–2022 in-sample train fold and *decayed* — through regime change, crowding ([McLean & Pontiff 2016 *J Finance*](https://doi.org/10.1111/jofi.12365)), or microstructure change ([Khandani & Lo 2011 *J Financial Markets*](https://doi.org/10.1016/j.finmar.2010.07.005)) — at or near the train/test boundary. Distinguishing (a) from (b) on a single-cell OOS test is impossible. But the project's policy response to (a) and (b) should diverge: (a) calls for hypothesis retirement; (b) calls for a *decay detector* that would have triggered a switch off the strategy before the realized catastrophic drawdown materialized. The current ADR-0017 toolkit has no decay-detection primitive — the strategy ran to completion across the full OOS fold because nothing was watching its rolling fitness path.

**Observation 2 — H052a / H053 Sharpe-CI-tight-around-zero pattern.** H052a KPI report card v1 ([research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md)) and H053 KPI report card v3 ([research/01_hypothesis_register/H053/H053_kpi_report_v3.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v3.md)) both produced LW2008 differential Sharpe CIs that covered zero ("non-significant null") on the hypothesis-of-record arms, *while* the realized $10K trajectories on substantively profitable cells materially exceeded zero: H052a NQ unconditional ORB +10.61% realized OOS with P(loss) = 18.56% in the 252-session forward projection; H053 NQ LightGBM +10.8% realized OOS with max-DD 3.7%. The Sharpe-differential CI is correctly *centered* near zero — the absolute magnitude of the differential per session is small — but the *log-wealth trajectory* is materially positive. Sharpe-as-fitness loses the signal that log-wealth-as-fitness retains. This is the analytical content of Goetzmann-Ingersoll-Spiegel-Welch 2007 §III: the Sharpe ratio is manipulable by leverage and dynamic strategy, and is dominated by the manipulation-proof performance measure (MPPM) as a fitness function for portfolios that compound.

**Observation 3 — $10K sandbox framing.** The operator's 2026-05-08 pilot trajectory ($2K → $9.4K → ~$2.2K in five days; recorded in ADR-0017 §Context) and the 2026-05-08 standing directive that "Sharpe ratio … seems to be arbitrary and archaic … push the limits and test boundaries" together reframe the project's capital-deployment context. Capital at risk is operator-scale ($10K starting bankroll per project-canonical simulation convention per ADR-0013 §3.1); regulatory-fiduciary-style §IV.A institutional risk constraints do not bind; the deployment context is closer to the Kelly-criterion compounding-bankroll framework than to mean-variance-with-VaR-budget institutional asset management. In this regime, log-wealth is the operator-correct utility function ([Kelly 1956 *Bell Syst Tech J*](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x); [Breiman 1961](https://projecteuclid.org/euclid.bsmsp/1200512630) showing log-utility maximizes asymptotic growth rate; [Thorp 2006 §III](https://www.elsevier.com/books/handbook-of-asset-and-liability-management/zenios/978-0-444-50875-1)), and Sharpe-anchored fitness is provably suboptimal in any positive-drift compounding setting where the operator has access to fractional sizing.

### Theoretical grounding — Adaptive Markets Hypothesis

[Lo 2004 *J Portfolio Mgmt* 30(5):15-29](https://doi.org/10.3905/jpm.2004.442611) argues that market efficiency is not a Boolean state but the result of an evolutionary process: heuristics that worked are arbitraged away ([McLean & Pontiff 2016](https://doi.org/10.1111/jofi.12365) document a ~58% post-publication decay in 97 cross-sectional anomalies); new heuristics evolve from boundedly-rational adaptation under changing market ecology; the marginal alpha at any moment depends on the current population of competing strategies and the prevailing regime. The four AMH implications load-bearing for this ADR are: (i) **strategy decay is the null, not the alternative** — a hypothesis that produces zero post-publication decay is the surprising case; (ii) **regime-conditional efficiency** — the same heuristic can be alpha-positive in one regime and alpha-negative in the adjacent regime, so the operationally-relevant question is "which regime are we in *now*" rather than "is this strategy permanently profitable"; (iii) **heterogeneous time-varying risk premia** — the equity / Sharpe / drawdown relationship is itself regime-dependent, so static evaluation metrics undercount regime-conditional fitness; (iv) **continuous innovation as evolutionary necessity** — a portfolio of strategies, with active replacement of decayed members by newly-evolved candidates, dominates any single-strategy commitment. The SKIE-Universe permanent-exploration framing of ADR-0013 §"Research philosophy" is already congruent with (iv); ADR-0018 makes (i)–(iii) operational at the inferential layer.

The AMH framing also disposes of a latent embarrassment in the project's prior framing. ADR-0017 §Context describes the H050 catastrophic OOS as evidence that "HMM regime-gating actively HARMS the directional signal." Under AMH, this is a *category error*: the regime that prevailed in the H050 2020–2022 train fold is not the regime that prevailed in the 2024–2025 test fold (post-2022 inflation regime change, post-2024 election regime change, multiple Fed-cycle inflections). The gated arm overfit to the train-fold regime; the OOS regime mismatch is the predicted AMH outcome, not an indictment of the gating mechanism. The operational fix is *not* "abandon HMM gating" but "detect the regime decay and switch off the decayed gating".

### Theoretical grounding — Sharpe-as-fitness is manipulable; MPPM(ρ=1) is not

[Goetzmann-Ingersoll-Spiegel-Welch 2007 *RFS*](https://doi.org/10.1093/rfs/hhm025) Theorem 1 establishes that for any benchmark utility function exhibiting CRRA with coefficient ρ, the MPPM defined as $\hat{\Theta}_\rho = \frac{1}{(1-\rho)\Delta t} \ln\left(\frac{1}{T+1}\sum_{t=0}^{T}\left[\frac{1+r_t}{1+r_{f,t}}\right]^{1-\rho}\right)$ is (i) manipulation-proof — no dynamic strategy can inflate $\hat{\Theta}_\rho$ above its true value; (ii) properly accounts for higher-order moments via its dependence on the full return distribution; (iii) admits the analytical reduction at ρ = 1 (after applying L'Hôpital's rule to the limit) to $\hat{\Theta}_1 = \frac{1}{\Delta t} \cdot \overline{\ln\left[(1+r_t)/(1+r_{f,t})\right]}$ — the empirical mean of excess log-returns, *i.e.* the Kelly-criterion fitness function up to a constant. The Sharpe ratio is *not* manipulation-proof: GISW §IV documents three explicit strategies (dynamic over-investment in tails, selling out-of-the-money puts, conditional leverage) that inflate Sharpe arbitrarily while reducing investor welfare. For a compounding-bankroll setting with discretionary sizing, MPPM(ρ=1) is therefore both the manipulation-proof and the analytically-correct fitness function.

### Literature pushback on super-Kelly

A complete framing requires explicit documentation of the literature's near-uniform position against super-Kelly sizing ($f > 1.0 \times f_{\text{Kelly-optimal}}$). [MacLean-Ziemba-Blazenko 1992 *Mgmt Sci*](https://doi.org/10.1287/mnsc.38.11.1562) prove fractional Kelly $f \in (0, 1)$ Pareto-dominates full Kelly on the (long-run-growth-rate, time-to-recovery-from-drawdown) frontier under realistic parameter uncertainty. [MacLean-Thorp-Ziemba 2010](https://doi.org/10.1142/7598) collect 60 years of theoretical and empirical analysis converging on $f \in [0.25, 0.50]$ as the operationally-preferred regime. [Samuelson 1979 *J Banking Finance*](https://doi.org/10.1016/0378-4266(79)90023-2) ("Why we should not make mean log of wealth big though years to act are long") argues full Kelly is not utility-optimal for any agent with risk-aversion strictly greater than log. [Chopra-Ziemba 1993 *JPM*](https://doi.org/10.3905/jpm.1993.409440) document that mean-estimation error has ~10× the certainty-equivalent impact of variance-estimation error, which compounds to roughly half-Kelly being the parameter-uncertainty-robust optimum. [Grossman-Zhou 1993 *Math Finance*](https://doi.org/10.1111/j.1467-9965.1993.tb00044.x) construct the drawdown-constrained optimal-growth solution, which is strictly below full Kelly. [Browne 1999 *Finance & Stochastics*](https://doi.org/10.1007/s007800050063) "Beating a moving target" extends with explicit stochastic-benchmark-outperformance constraints; the solution again sits below full Kelly. **The primary literature is uniform: $f \leq 1.0 \times$ Kelly is the evidence-supported regime.** ADR-0018 *grid-searches over super-Kelly multipliers anyway* per the operator's 2026-05-08 standing directive ("push the limits and test boundaries"); the §Consequences caveat below documents the evidence-bar weakening explicitly.

## Decision

**D-1 — MPPM(ρ=1) replaces Sharpe in inner-CV fitness.** Every hypothesis whose inner-CV hyperparameter selection currently optimizes Sharpe-differential (H050, H052a, H053 v4, H054, H055-pending) is amended at §10 (decision rule) only — §1–§7 frozen pre-reg sections preserved verbatim per ADR-0013 §"Frozen pre-registration amendment" — to optimize MPPM(ρ=1) instead. The MPPM(ρ=1) primitive lands at [src/skie_ninja/inference/mppm.py](../../src/skie_ninja/inference/mppm.py) per `P1-MPPM-RHO-1-FITNESS-PRIMITIVE` with the GISW 2007 Theorem 1 analytical form, the $\Delta t$ annualization-factor declaration per ADR-0014 §3.2 Table 4 convention, and a regression test pinning the limiting-case identity $\lim_{\rho \to 1} \hat{\Theta}_\rho = \overline{\ln[(1+r_t)/(1+r_{f,t})]}/\Delta t$ to L'Hôpital floating-point tolerance. The Sharpe-family LW2008 differential CI and Hansen 2005 SPA p-value primitives are preserved and continue to be reported in the KPI report card v{N+1} §"Performance KPIs" block as secondary KPIs per ADR-0017 D-1 (Sharpe-demotion is preserved through ADR-0018; MPPM is the further refinement at the fitness layer).

**D-2 — Kelly cap is grid-searched, not fixed.** ADR-0017 §4.1 fixed the Kelly multiplier at 0.25 (quarter-Kelly per MacLean-Thorp-Ziemba 2010). ADR-0018 amends this to an explicit grid: $f \in \{0.25, 0.50, 1.00, 1.50, 2.00, 2.50\} \times f_{\text{Kelly-optimal}}$. The primitive at [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py) `compute_position_size` gains a `kelly_multiplier_grid` parameter and the orchestrator selects the multiplier on each inner-CV fold by MPPM(ρ=1) on the validation split, per `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE`. The literature-uniformly-dominated regime ($f > 1.0$) is documented as caveat in §Consequences but not excluded from the search — operator-discretionary per the $10K sandbox framing. The selected multiplier becomes a logged KPI annotation `kelly-multiplier-{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` in the KPI report card's §"Methodological-correctness annotations" line.

**D-3 — BOCD decay detector primitive.** [Adams & MacKay 2007 *arXiv:0710.3742*](https://arxiv.org/abs/0710.3742) Bayesian Online Changepoint Detection is implemented at [src/skie_ninja/inference/bocd.py](../../src/skie_ninja/inference/bocd.py) per `P1-BOCD-DECAY-DETECTOR-PRIMITIVE`. The detector consumes a rolling-window MPPM(ρ=1) path computed per session on a configurable lookback ($W \in \{20, 60, 120\}$ sessions, grid-searched on calibration holdout per the H055 calibration-holdout protocol), maintains the Adams-MacKay 2007 §2 run-length posterior $P(r_t \mid x_{1:t})$ under the conjugate hazard prior with rate $\lambda$ (default $\lambda = 1/250$ per AMH-canonical annual regime cadence; calibrated empirically per `P1-BOCD-HAZARD-RATE-EMPIRICAL`), and emits a `decay-detected-yes` annotation when $P(\text{changepoint within last } W/2 \text{ sessions}) > 0.5$. The annotation feeds the meta-strategy switching layer (D-4) and is logged as a KPI annotation `decay-detected-{yes, no}` in the KPI report card.

**D-4 — Switching-bandit meta-strategy.** The decay-triggered strategy-switching layer is implemented as a non-stationary multi-armed bandit at [src/skie_ninja/meta/switching_bandit.py](../../src/skie_ninja/meta/switching_bandit.py) per `P1-SWITCHING-BANDIT-META-STRATEGY` (folded into this ADR; no separate ADR needed). Three primary algorithms supported, each with its own load-bearing primary source:

- **D-UCB / SW-UCB** ([Garivier & Moulines 2011 *arXiv:0805.3415*](https://arxiv.org/abs/0805.3415) §3.1 / §3.2): discount-factor and sliding-window UCB variants with regret bound $O(\sqrt{\Upsilon_T \cdot T \log T})$ against $\Upsilon_T$ piecewise-stationary breakpoints — the regret bound directly applies in the AMH-framed regime where the number of regime shifts on a multi-year OOS fold is bounded but non-zero.
- **CUSUM-UCB / GLR-klUCB** ([Besson-Kaufmann-Maillard-Seznec 2019 *arXiv:1902.01575*](https://arxiv.org/abs/1902.01575) §3): CUSUM-test-armed UCB; explicitly chains a changepoint detector (project default: BOCD per D-3) to the UCB arm-selection rule.
- **EXP3.S baseline** ([Auer-Cesa-Bianchi-Freund-Schapire 2002 *SIAM J Computing* 32(1):48-77](https://doi.org/10.1137/S0097539701398375) §8): adversarial-bandit benchmark for non-stationary settings; reported as comparator-only.

Switching-cost regret is handled per [Dekel-Ding-Koren-Peres 2014 *STOC* arXiv:1310.2997](https://arxiv.org/abs/1310.2997) "Bandits with Switching Costs: $T^{2/3}$ Regret": the per-switch cost (transaction cost + opportunity cost during transition) enters the regret accounting with the $\tilde{O}(T^{2/3})$ bound applicable to bandits-with-switching-costs. The cost-model integration is delegated to the existing per-hypothesis cost-model primitives ([src/skie_ninja/backtest/costs/](../../src/skie_ninja/backtest/costs/)).

**D-5 — ADR-0017 survival infrastructure preserved verbatim.** This ADR amends ADR-0017 §1 (Sharpe-secondary clause; now MPPM-secondary) and §4.1 (¼-Kelly cap; now grid-searched) but explicitly **preserves**: ADR-0017 §4.2 risk-of-ruin Monte Carlo at [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py); ADR-0017 §5 eight hard kill switches K-1..K-8 ($1.0R per-trade stop, $2 \times$ median-winning-duration time stop, no-add-to-loser, per-symbol capacity cap per [ADR-0001](ADR-0001-project-scope.md), correlated-instrument inventory cap, −2% daily circuit breaker, −5% weekly circuit breaker, adverse-direction entry filter); ADR-0017 §6 five failure-mode stress tests FM-1..FM-5; ADR-0017 §3 four-metric primary inferential vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) in the KPI report card §"End-of-simulation results summary" tables per ADR-0014 §3.2. The kill switches remain hard constraints at the NinjaScript layer per [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §5.1 regardless of the bandit's arm-selection decision.

**D-6 — AMH framing adopted as project-canonical philosophy.** [Lo 2004](https://doi.org/10.3905/jpm.2004.442611) Adaptive Markets Hypothesis is recorded as the project's canonical theoretical framing for hypothesis-decay treatment, with the four implications enumerated in §Context binding on all future hypothesis pre-registrations from 2026-05-12 forward. The hypothesis-design template at [research/_templates/](../../research/_templates/) gains a §"AMH decay treatment" subsection per `P1-ADR-0018-DESIGN-MD-CASCADE` requiring each new pre-registration to state (a) the prior on regime-cadence for the strategy's signal class; (b) the BOCD hazard rate $\lambda$ selected on calibration holdout; (c) the meta-strategy peer-arm set the strategy will be switched against.

## Consequences

### Preserve / amend / supersede matrix

| Prior ADR | Section | Status under ADR-0018 |
|---|---|---|
| [ADR-0001](ADR-0001-project-scope.md) | Universe + capacity ceiling | **Preserved** |
| [ADR-0010](ADR-0010-multi-hour-run-process-protection.md) | All layers | **Preserved** |
| [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) | All sections; non-loss mandate; mandatory NinjaScript terminus; §"Frozen pre-registration amendment" | **Preserved**; ADR-0018 itself is a project-level §1+§10 amendment per the discipline |
| [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) | 9-table + bottom-line structure | **Preserved**; Table 3 (Sharpe primary) reframed to MPPM primary; Tables 3a/3b/3c (per ADR-0017) preserved; new Table 3d (kelly-multiplier-grid-selection diagnostic) appended per `P1-ADR-0018-KPI-CARD-CASCADE` |
| [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) | §1 (Sharpe-secondary) | **Amended**: MPPM(ρ=1) replaces Sharpe in the fitness role; Sharpe remains secondary-KPI for academic comparability |
| ADR-0017 | §4.1 (¼-Kelly cap) | **Amended**: ¼-Kelly replaced by the $\{0.25, 0.5, 1.0, 1.5, 2.0, 2.5\}$ grid; selected multiplier logged as KPI annotation |
| ADR-0017 | §4.2 (risk-of-ruin Monte Carlo) | **Preserved verbatim** |
| ADR-0017 | §5 (kill switches K-1..K-8) | **Preserved verbatim**; kill switches bind regardless of bandit decision |
| ADR-0017 | §6 (failure-mode stress tests FM-1..FM-5) | **Preserved verbatim** |
| ADR-0017 | §3 (4-metric primary inferential vector) | **Preserved** in the §"End-of-simulation results summary" tables; reinterpreted in §"Performance KPIs" as KPI annotations subordinate to MPPM in the fitness role |

### KPI annotation grammar additions

The KPI annotation vocabulary in CLAUDE.md §"KPI report card for every strategy" is extended with three new annotation families:

- `mppm-rho1-{positive, marginal, negative}` — sign of MPPM(ρ=1) point estimate on the OOS fold with Politis-White 2004 block-stationary-bootstrap CI (1,000 replicates per `P1-MPPM-RHO-1-CI-PRIMITIVE`). `marginal` if CI covers zero.
- `decay-detected-{yes, no}` — BOCD posterior $P(\text{changepoint within last } W/2 \text{ sessions}) > 0.5$ on the rolling-MPPM path over the OOS fold.
- `kelly-multiplier-{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` — selected Kelly multiplier per D-2 grid-search on inner-CV.

### Literature super-Kelly caveat

Per the §Context literature pushback summary, the primary sources ([MacLean-Ziemba-Blazenko 1992](https://doi.org/10.1287/mnsc.38.11.1562); [Samuelson 1979](https://doi.org/10.1016/0378-4266(79)90023-2); [Chopra-Ziemba 1993](https://doi.org/10.3905/jpm.1993.409440); [Grossman-Zhou 1993](https://doi.org/10.1111/j.1467-9965.1993.tb00044.x); [Browne 1999](https://doi.org/10.1007/s007800050063); [MacLean-Thorp-Ziemba 2010](https://doi.org/10.1142/7598)) uniformly endorse $f \leq 1.0 \times$ Kelly under any realistic parameter-uncertainty + risk-aversion-greater-than-log specification. The Kelly grid in D-2 extends to $2.5 \times$ Kelly **per the operator's 2026-05-08 standing $10K-sandbox directive**; this is the operator-discretionary regime in which the evidence-bar discipline of CLAUDE.md §"Evidence Hierarchy" is **weakened**. Specifically: for any KPI report card v{N+1} that lands at `kelly-multiplier-{1.5, 2.0, 2.5}`, the report card's §"Methodological-correctness annotations" line MUST carry the additional annotation `super-kelly-operator-discretionary` and the §"Bottom line" prose MUST contain a sentence explicitly noting the literature-evidence-bar deviation. Operator review at every stage transition (per ADR-0013 §6) bears the full discretion for this regime; the audit-remediate-loop is not weakened, only the evidence-bar default. Re-evaluation of this carve-out on the first paper-trade evaluation that lands a super-Kelly arm is tracked under `P1-ADR-0018-SUPER-KELLY-EMPIRICAL-CALIBRATION`.

### Cascade requirements

Per ADR-0013 §"Frozen pre-registration amendment" §1–§7 immutability discipline, the project-level §1+§10 amendment at ADR-0018 requires explicit cascade to every designed-status hypothesis's design.md §8 + §10 + §11.1:

- **`P1-ADR-0018-DESIGN-MD-CASCADE`** (BLOCKING-BEFORE-NEXT-STAGE-3-RUN) — H050, H051, H052a, H052b, H053, H054, H055 design.md §10 (decision rule) reframed from Sharpe-differential to MPPM(ρ=1); §11.1 (kill switches) preserved verbatim per D-5; §17 (revision log) appended with the ADR-0018 amendment reference. Frozen §1–§7 untouched.
- **`P1-ADR-0018-TEMPLATE-CASCADE`** — [research/_templates/](../../research/_templates/) hypothesis-design template gains the §"AMH decay treatment" subsection per D-6.
- **`P1-ADR-0018-KPI-CARD-CASCADE`** — KPI report card template at [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) extended with Table 3d (kelly-multiplier-grid-selection diagnostic) plus the three new annotation families.
- **`P1-ADR-0018-CLAUDE-MD-CASCADE`** — CLAUDE.md §"KPI report card for every strategy" updated with the new annotations and the super-Kelly caveat.

### BLOCKING follow-ups registered by ADR-0018

| Follow-up | Status | Description |
|---|---|---|
| `P1-MPPM-RHO-1-FITNESS-PRIMITIVE` | BLOCKING-BEFORE-NEXT-INNER-CV-RUN | GISW 2007 MPPM(ρ=1) implementation + L'Hôpital identity regression test |
| `P1-BOCD-DECAY-DETECTOR-PRIMITIVE` | BLOCKING-BEFORE-NEXT-STAGE-3-RUN | Adams-MacKay 2007 BOCD on rolling MPPM path |
| `P1-SWITCHING-BANDIT-META-STRATEGY` | BLOCKING-BEFORE-FIRST-META-STRATEGY-RUN | D-UCB / SW-UCB / CUSUM-UCB / EXP3.S primitives per Garivier-Moulines 2011 + Besson-Kaufmann 2018 + Auer-CB-Fischer 2002 |
| `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE` | BLOCKING-BEFORE-NEXT-STAGE-3-RUN | $\{0.25, 0.5, 1.0, 1.5, 2.0, 2.5\}$ grid in `compute_position_size` |
| `P1-ADR-0018-DESIGN-MD-CASCADE` | BLOCKING-BEFORE-NEXT-STAGE-3-RUN | Per-hypothesis §8 + §10 + §11.1 cascade |

### Non-blocking follow-ups registered by ADR-0018

`P1-MPPM-RHO-1-CI-PRIMITIVE` (stationary-bootstrap CI on MPPM); `P1-BOCD-HAZARD-RATE-EMPIRICAL` (calibrate $\lambda$ on calibration holdout); `P1-BOCD-WINDOW-W-EMPIRICAL` (grid-search $W$); `P1-SWITCHING-BANDIT-PEER-ARM-SET-PROTOCOL` (define peer-arm-set construction per signal class); `P1-ADR-0018-SUPER-KELLY-EMPIRICAL-CALIBRATION` (post-first-super-Kelly paper-trade re-evaluation); `P1-ADR-0018-KPI-CARD-CASCADE`; `P1-ADR-0018-TEMPLATE-CASCADE`; `P1-ADR-0018-CLAUDE-MD-CASCADE`; `P1-ADR-0017-VS-ADR-0018-CROSSWALK-MEMO` (operator-readable crosswalk explaining where ADR-0017 ends and ADR-0018 begins).

## References

### Manipulation-Proof Performance Measure
- Goetzmann, W., Ingersoll, J., Spiegel, M., & Welch, I. (2007). Portfolio performance manipulation and manipulation-proof performance measures. *Review of Financial Studies*, 20(5), 1503–1546. [DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025)

### Kelly criterion + log-utility lineage
- Kelly, J. L. (1956). A new interpretation of information rate. *Bell System Technical Journal*, 35(4), 917–926. [DOI 10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)
- Breiman, L. (1961). Optimal gambling systems for favorable games. *Proceedings of the Fourth Berkeley Symposium on Mathematical Statistics and Probability*, 1, 65–78.
- Thorp, E. O. (2006). The Kelly criterion in blackjack, sports betting, and the stock market. In S. A. Zenios & W. T. Ziemba (Eds.), *Handbook of Asset and Liability Management*, Vol. 1, Ch. 9. Elsevier.
- MacLean, L. C., Thorp, E. O., & Ziemba, W. T. (Eds.). (2010). *The Kelly Capital Growth Investment Criterion: Theory and Practice*. World Scientific. [DOI 10.1142/7598](https://doi.org/10.1142/7598)

### Fractional / drawdown-constrained Kelly
- MacLean, L. C., Ziemba, W. T., & Blazenko, G. (1992). Growth versus security in dynamic investment analysis. *Management Science*, 38(11), 1562–1585. [DOI 10.1287/mnsc.38.11.1562](https://doi.org/10.1287/mnsc.38.11.1562)
- Samuelson, P. A. (1979). Why we should not make mean log of wealth big though years to act are long. *Journal of Banking and Finance*, 3(4), 305–307. [DOI 10.1016/0378-4266(79)90023-2](https://doi.org/10.1016/0378-4266(79)90023-2)
- Chopra, V. K., & Ziemba, W. T. (1993). The effect of errors in means, variances, and covariances on optimal portfolio choice. *Journal of Portfolio Management*, 19(2), 6–11. [DOI 10.3905/jpm.1993.409440](https://doi.org/10.3905/jpm.1993.409440)
- Grossman, S. J., & Zhou, Z. (1993). Optimal investment strategies for controlling drawdowns. *Mathematical Finance*, 3(3), 241–276. [DOI 10.1111/j.1467-9965.1993.tb00044.x](https://doi.org/10.1111/j.1467-9965.1993.tb00044.x)
- Browne, S. (1999). Beating a moving target: Optimal portfolio strategies for outperforming a stochastic benchmark. *Finance and Stochastics*, 3(3), 275–294. [DOI 10.1007/s007800050063](https://doi.org/10.1007/s007800050063)

### Adaptive Markets Hypothesis + strategy decay
- Lo, A. W. (2004). The Adaptive Markets Hypothesis: Market efficiency from an evolutionary perspective. *Journal of Portfolio Management*, 30(5), 15–29. [DOI 10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611)
- McLean, R. D., & Pontiff, J. (2016). Does academic research destroy stock return predictability? *Journal of Finance*, 71(1), 5–32. [DOI 10.1111/jofi.12365](https://doi.org/10.1111/jofi.12365)
- Khandani, A. E., & Lo, A. W. (2011). What happened to the quants in August 2007? Evidence from factors and transactions data. *Journal of Financial Markets*, 14(1), 1–46. [DOI 10.1016/j.finmar.2010.07.005](https://doi.org/10.1016/j.finmar.2010.07.005)

### Bayesian Online Changepoint Detection
- Adams, R. P., & MacKay, D. J. C. (2007). Bayesian online changepoint detection. [arXiv:0710.3742](https://arxiv.org/abs/0710.3742)

### Non-stationary bandits + switching-cost regret
- Garivier, A., & Moulines, E. (2011). On upper-confidence bound policies for switching bandit problems. *Proc. ALT 2011*, LNCS 6925:174–188. [DOI 10.1007/978-3-642-24412-4_16](https://doi.org/10.1007/978-3-642-24412-4_16) (preprint: [arXiv:0805.3415](https://arxiv.org/abs/0805.3415), 2008).
- Besson, L., Kaufmann, E., Maillard, O.-A., & Seznec, J. (2019). Efficient change-point detection for tackling piecewise-stationary bandits. [arXiv:1902.01575](https://arxiv.org/abs/1902.01575). Canonical CUSUM-UCB / GLR-klUCB reference.
- Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002). Finite-time analysis of the multiarmed bandit problem (UCB1). *Machine Learning*, 47(2–3), 235–256. [DOI 10.1023/A:1013689704352](https://doi.org/10.1023/A:1013689704352)
- Auer, P., Cesa-Bianchi, N., Freund, Y., & Schapire, R. E. (2002). The nonstochastic multiarmed bandit problem (EXP3 / EXP3.S). *SIAM Journal on Computing*, 32(1):48–77. [DOI 10.1137/S0097539701398375](https://doi.org/10.1137/S0097539701398375)
- Dekel, O., Ding, J., Koren, T., & Peres, Y. (2014). Bandits with switching costs: $T^{2/3}$ regret. *Proceedings of STOC 2014*. [arXiv:1310.2997](https://arxiv.org/abs/1310.2997)

### Project-internal ADRs
- [ADR-0001 project scope](ADR-0001-project-scope.md)
- [ADR-0010 multi-hour-run process protection](ADR-0010-multi-hour-run-process-protection.md)
- [ADR-0013 permanent-exploration / no-archive / NinjaScript terminus](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- [ADR-0014 canonical end-of-simulation results-summary tables](ADR-0014-canonical-end-of-simulation-results-summary-tables.md)
- [ADR-0017 survival-constrained optimization paradigm](ADR-0017-survival-constrained-optimization-paradigm.md)
