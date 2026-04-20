# Hypothesis Backlog

Every signal, transform, or angle considered for this project. Status transitions:
`queued → designed → running → evaluated → archived(positive|null|negative)`.

Each row gets a dedicated design doc in [../research/01_hypothesis_register/](../research/01_hypothesis_register/) before execution, with pre-registered hypothesis, data, estimator, assumptions, and stopping rule.

## Tier 1 — directional conditioning variables (attack 50% AUC wall)

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H001 | Dealer net-gamma regime conditions intraday drift sign | [Dim-Eraker-Vilkov 2024](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190); [Cboe 0DTE GEX study](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf) | queued |
| H002 | Macro-surprise z-scores drive 5–30 min ES/NQ direction | [Andersen-Bollerslev-Diebold-Vega 2007, JIE](https://doi.org/10.1016/j.jinteco.2006.07.002) | queued |
| H003 | Kalshi macro-contract drift as directional prior pre-release | [Kalshi crypto-vol paper arXiv 2604.01431](https://arxiv.org/html/2604.01431v1) | archived(null) — round-1 lit remediation found no peer-reviewed empirics; revisit if publication emerges |
| H004 | FOMC statement semantic delta (hawkish-tilt) directional within 10 min of release | [Cieslak-Morse-Vissing-Jorgensen](https://www.aeaweb.org/articles?id=10.1257/aer.20180850) | queued |
| H005 | Retail 0DTE P/C ratio contrarian for last-hour ES | — | queued |

## Tier 2 — microstructure / flow

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H010 | Deep OFI (Kolm-Turiel-Westray 2021) on ES MBP-10 | [SSRN 3900141](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3900141) | queued |
| H011 | Event-time (Hawkes-clock) resampling before feature engineering | [Rambaldi-Bacry-Muzy 2017](https://arxiv.org/abs/1412.7096); [Oxford JFEC MHP 2024](https://academic.oup.com/jfec/article/22/3/743/7082927) | queued |
| H012 | Transfer entropy ES ↔ MES ↔ SPY ↔ 0DTE-implied-spot ↔ Kalshi | [Schreiber 2000, PRL](https://doi.org/10.1103/PhysRevLett.85.461); Hasbrouck 1995 | queued |
| H013 | Bouchaud square-root metaorder footprint detection | [Tóth et al. 2011](https://arxiv.org/abs/1104.1694) | queued |
| H014 | NYSE/Nasdaq MOC imbalance leakage into ES last 10 min | — (tacit) | queued |
| H015 | Treasury auction when-issued drift → ZN/ZB jump, ES beta | [Fleming-Rosenberg, NY Fed SR 299](https://www.newyorkfed.org/research/staff_reports/sr299.html) | queued |

## Tier 3 — frontier / low published coverage

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H020 | Rough-volatility Hurst exponent regime detector | [Gatheral-Jaisson-Rosenbaum 2018, Quant Fin](https://doi.org/10.1080/14697688.2017.1393551) | queued |
| H021 | Live FOMC speech sentence-level embedding drift → ES direction | [Macro-alpha FinBERT arXiv 2505.16136](https://arxiv.org/html/2505.16136v1) | queued |
| H022 | Stablecoin mint/burn → BTC basis → ES risk-on/off beta | [CF Benchmarks basis](https://www.cfbenchmarks.com/blog/revisiting-the-bitcoin-basis-how-momentum-sentiment-impact-the-structural-drivers-of-basis-activity) | queued |
| H023 | AIS vessel arrival events at oil terminals → CL → ES energy-beta path | — | queued |
| H024 | ERCOT/PJM nodal LMP + HRRR nowcast → NG → ES commodity-beta | — | queued |
| H025 | FX carry unwind via SOFR-IOER spread → ES direction | — | queued |
| H026 | Implied-realized correlation divergence (CBOE COR) as regime gate | — | queued |

## Tier 4 — execution / portfolio

| ID | Angle | Mechanism | Status |
|---|---|---|---|
| H040 | Stack Tier-1 directional gates on existing vol/size/breakout models | internal SKIE-Ninja ensemble | queued |
| H041 | Kelly-fractional sizing with Sharpe-bootstrap CI floor | [Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084) | queued |
| H042 | Hansen SPA gate across the full accumulated strategy universe | [Hansen 2005, JBES](https://doi.org/10.1198/073500105000000063) | queued |

## Tier 2b — regime/state (added 2026-04-20 per ADR-0006)

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
<!-- hypothesis_new.py appended --> H050 | HMM regime-conditioned ES/NQ intraday directional signal | [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Ryou et al. 2020, Sustainability 12(17):7031](https://doi.org/10.3390/su12177031); [Guidolin & Timmermann 2007, JEDC 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004) | designed |
<!-- hypothesis_new.py appended --> H051 | HMM-gated ES/NQ (or MES/MNQ) basis pairs trade with Kalman hedge ratio | [Johansen 1991](https://doi.org/10.2307/2938278); [Osterwald-Lenum 1992](https://doi.org/10.1111/j.1468-0084.1992.tb00013.x); West & Harrison 1997, ISBN 978-0387947259; Chan 2013, ISBN 978-1118460146 | designed |
<!-- hypothesis_new.py appended --> H052 | HMM regime-gated QQQ first-hour long-call 0DTE scalp (SKIE-ORB-CALL overlay) | [Ryou et al. 2020](https://doi.org/10.3390/su12177031); [Guidolin-Timmermann 2007](https://doi.org/10.1016/j.jedc.2006.12.004); [Hamilton 1989](https://doi.org/10.2307/1912559); [Andersen-Bollerslev 1998](https://doi.org/10.2307/2527343); de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1119482086); sibling repo [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) | designed |

## Round-1 remediation adjustments (2026-04-15)

Lit-check audit invalidated three cites grounding these hypotheses. Status updates:
- **H003** → `archived(null)` above.
- **H030** (iceberg detection) → downgrade Tier-2 HIGH to MED; deep-learning framing unsupported, survives as survival / hidden-liquidity.
- **H044** (weekly OI pin migration) → `archived(null)`; mechanism unsupported by current citations.

New items append with sequential IDs. Negative/null results move to `archived(null)` but **stay in the file** — they document the search space we've covered.
