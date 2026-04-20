# Memo — Medallion/HMM lineage and retail-adaptable takeaways (2026-04-20)

Purpose: fix the project's working model of what the Medallion / Renaissance lineage actually teaches us that is (a) evidence-grade and (b) compatible with a retail-capacity program. Every quantitative Medallion claim is flagged [UNVERIFIED — flag for lit-check] pending Round-2 literature resolution.

## 1. Medallion performance claims

| Claim | Candidate source | Status | Project treatment |
|---|---|---|---|
| Medallion ~63.3% compound gross annualized 1988–2018 | [Cornell 2019, SSRN id 3504766](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3504766) | Verified (Cornell). | Not a target; not a benchmark. |
| $100 initial → $398,723,873 terminal; no negative annual return 1988–2018 | [Cornell 2019, SSRN id 3504766](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3504766) | Verified (Cornell). | Noted as folklore; excluded from any calibration. |
| 5-and-44 fee schedule | Zuckerman 2019 *The Man Who Solved the Market* / Institutional Investor | Tier-5 trade press (orienting). | Not evidence-grade; not a target. |
| 2024 Medallion ~30% on $12B internal capital | [Hedgeweek coverage](https://www.hedgeweek.com/) | Tier-5 trade press; specific article URL pending. | Trade-press; not evidence-grade. |
| Mercer ~50.75% hit rate with 1–5 bp edge | Zuckerman 2019 *The Man Who Solved the Market* (page citation pending) | Tier-5 trade press (orienting). | Orienting only; our gate is Sharpe CI + SPA, not hit-rate. |
| Leverage regime 12.5x–20x | Multiple press accounts | [UNVERIFIED — flag for lit-check] | **Out of scope** per capacity ceiling in [ADR-0001](../decisions/ADR-0001-project-scope.md). |

The retail transferable observation is qualitative: a system that combines latent-state inference, many small-edge trades, and a unified cross-asset feature space can in principle produce a high-Sharpe signal stack. The fee schedule, capacity, and leverage are not transferable and not targets.

## 2. Methodological pillars

| Pillar | Primary citation | Status |
|---|---|---|
| Hidden Markov Model (Baum-Welch EM) | [Baum et al. 1970, Ann. Math. Stat.](https://doi.org/10.1214/aoms/1177697196) | Verified DOI. |
| Viterbi decoding | [Viterbi 1967, IEEE TIT](https://doi.org/10.1109/TIT.1967.1054010) | Verified DOI. |
| Rabiner HMM tutorial | [Rabiner 1989, Proc. IEEE](https://doi.org/10.1109/5.18626) | Verified DOI. |
| Regime switching for macro/financial series | [Hamilton 1989, Econometrica](https://doi.org/10.2307/1912559) | Verified DOI. |
| Leonard Baum at IDA; Baum/Welch named for same | Historical | [UNVERIFIED — flag for lit-check] |
| Simons recruited Mercer and Brown from IBM c. 1993 | Biographical (Zuckerman 2019) | [UNVERIFIED — flag for lit-check] |
| James Ax extended Baum's HMM work at Axcom / Medallion predecessor | Biographical | [UNVERIFIED — flag for lit-check] |
| Kernel methods / embeddings for non-stationary finance | No single canonical cite | [UNVERIFIED — flag for lit-check] |
| Per-trade edge × volume (Kelly-adjacent) | [Kelly 1956, Bell System Technical J.](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x) and [Thorp 2006, Handbook of Asset and Liability Management] | Partial; Thorp chapter DOI not confirmed [UNVERIFIED — flag for lit-check] |
| HMM in momentum / equity timing | [Ryou, Bae, Lee, Oh 2020, "Momentum Investment Strategy Using a Hidden Markov Model," Sustainability 12(17):7031](https://doi.org/10.3390/su12177031) | Verified DOI. |
| Regime-switching asset allocation | [Guidolin & Timmermann 2007, JEDC 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004) | Verified DOI. |
| HMM model selection | [Celeux & Durand 2008, Computational Statistics 23(4):541–564](https://doi.org/10.1007/s00180-007-0097-1) | Verified DOI. |
| Pair-trading reference textbook | Chan 2013 *Algorithmic Trading*, Wiley, ISBN 978-1118460146 | ISBN from listing; publisher-page confirmation pending. |
| DLM / Kalman textbook | West & Harrison 1997 *Bayesian Forecasting and Dynamic Models*, 2nd ed., Springer, ISBN 978-0387947259 | ISBN from listing; publisher-page confirmation pending. |

## 3. Reference-implementation survey

Be skeptical. Most public HMM-on-equity repos leak the future in at least one of: (i) fitting the HMM on the full sample then backtesting inside that sample, (ii) using close-to-close returns aligned to the same close that generated the state, (iii) k-fold rather than walk-forward, (iv) parameter tuning outside a nested CV.

- **[EwanKW/Pairs-Trading-with-Robust-Kalman-Filter-and-Hidden-Markov-Model](https://github.com/EwanKW/Pairs-Trading-with-Robust-Kalman-Filter-and-Hidden-Markov-Model)** — Kalman filter for time-varying hedge ratio plus HMM over residuals. The Kalman architecture is reusable: state equation fits our online-updateable requirement. Risk points to audit before reuse: cointegration assumed rather than tested rolling-window; HMM `n_states` appears fixed a priori (would violate our no-magic-numbers rule); unclear whether the HMM is refit per walk-forward fold. Adapt conceptually; re-implement end-to-end inside our walk-forward harness.
- **[Bratet/Stock-Prediction-Using-Hidden-Markov-Chains](https://github.com/Bratet/Stock-Prediction-Using-Hidden-Markov-Chains)** — educational scope. High leakage risk; no walk-forward visible on quick survey. Useful as a sanity-check implementation of Baum-Welch wiring only.
- **[whrit/markovMaker](https://github.com/whrit/markovMaker)** — heuristic state-tagger; unclear evaluation protocol. Not suitable as a reference for our gate.
- **[Nikhil-Kumar-Patel/Hidden-Makov-Model](https://github.com/Nikhil-Kumar-Patel/Hidden-Makov-Model)** — small teaching repo; do not rely on for evaluation methodology.
- [`s-koirala/SKIE-NINJA-0DTE`](https://github.com/s-koirala/SKIE-NINJA-0DTE) — **sibling repo, LIVE** (created 2026-04-19; author Sudarshan "SKIE" Koirala; internal project code **SKIE-ORB-CALL**). Canonical code path for the 0DTE track under the Option C decision in [ADR-0006](../decisions/ADR-0006-scope-extension-hmm-0dte.md). Thesis: QQQ first-hour (09:30–10:30 ET) bullish bias > 0.50 green-rate, operationalized via long-premium 0DTE/1DTE QQQ call scalps. The repo has its own authoritative strategy PDF (`1st hr 0dte.pdf`) plus section-level extracts under `research/00-hypothesis.md` through `research/10-glossary.md`; it runs **CPCV + PBO + Bonferroni / Holm-Sidak** internally per de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1119482086) across stratified strata (day-of-week × gap-size × VIX-regime). Evaluation protocol is rigorous on its face: IS 2015–2021 / OOS 2022–2025; explicit time-ordered disjoint splits. Reproducibility-log schema compatibility with our [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md) extension still needs a direct audit when integration lands.

General rule: no public repo is adopted as-is. Reusable pieces get re-implemented inside our walk-forward harness with purge/embargo per Lopez de Prado AFML §7.

## 4. Retail-scale adaptations

- Leverage 12.5x–20x is out of scope. Capacity ceiling from [ADR-0001](../decisions/ADR-0001-project-scope.md) governs.
- The transferable edge is not a single large Sharpe — it is the composition of many small per-trade edges, which is brittle against realistic retail cost models. Every hypothesis must reference an explicit `cost_model_id` per plan §6 and run slippage walk-forward, not single-split.
- HMM's role in this project is **regime-conditioning of existing signals**, not replacement. A Tier-1 directional signal whose Sharpe CI excludes zero only inside a specific HMM state counts as a positive result for that regime-gated variant; the unconditional variant is evaluated separately and the comparison is registered in the pre-reg.
- Short-vol 0DTE (H052) carries a fat left tail; Sharpe-only gating is insufficient. Expected Shortfall CI ([Rockafellar & Uryasev 2000, J. Risk](https://doi.org/10.21314/JOR.2000.038)) and max-adverse-excursion are mandatory gate companions for 0DTE hypotheses.

## 5. Open questions remaining after Round 2

- Biographical claims (Baum/IDA, Simons/Mercer/Brown, Ax) remain Tier-5 orienting pending Zuckerman 2019 page numbers; they are narrative background outside the evidence hierarchy.
- Publisher-page ISBN confirmation for Chan 2013 and West & Harrison 1997.
- Specific Hedgeweek article URL for the 2024 Medallion performance claim (held as Tier-5 trade press).
