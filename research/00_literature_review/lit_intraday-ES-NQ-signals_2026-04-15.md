# Literature Review: Intraday Directional Signals for CME ES / NQ Futures

**Project:** SKIE-Universe
**Author:** SKIE (pseudonym)
**Date:** 2026-04-15 (remediated after round-1 literature-check audit)
**Doc type:** Literature review, grounding + novel-angle extension
**Reporting standard:** None imposed (internal research memo); adheres to [CLAUDE.md](C:\Users\skoir\.claude\CLAUDE.md) and [quant-project.md](C:\Users\skoir\.claude\rules\quant-project.md).

**Verification status:** Every DOI/SSRN ID reinstated below was re-derived by loading the publisher landing page (doi.org, ssrn.com, academic.oup.com, wiley.com, linkinghub.elsevier.com, aps.org, newyorkfed.org, aeaweb.org) and matching title+authors+year+venue. Tags: `[VERIFIED]` = publisher page confirms metadata; `[UNVERIFIED]` = DOI does not resolve or resolves to a different paper and no substitute found; `[TEXTBOOK]`, `[WP]`, `[PP]` as defined in section 1.4. Paraphrased numerical claims are tagged `[PARAPHRASE — verify against Table X]` where the underlying table was not fetched. Full audit trail in section 6.

---

## 1. Scope and method

### 1.1 Research question
Identify peer-reviewed and pre-print evidence for intraday directional predictability of E-mini S&P 500 (ES) and Nasdaq-100 (NQ) CME futures over horizons in [1 minute, 1 trading day]. "Directional" = sign-of-next-bar-return or sign-of-horizon-return, measured by AUC / Matthews correlation / directional accuracy, not magnitude or variance. Prior SKIE work established that volatility and breakout timing are predictable intraday but direction stalls at AUC ~ 0.50 using price/volume technicals alone.

### 1.2 Inclusion criteria
- **Primary:** peer-reviewed articles 2015-2026 in JFE, JF, RFS, RAPS, JFQA, Journal of Financial Econometrics, Quant. Finance, Management Science, or working papers from NY Fed, BIS, Federal Reserve Board, BoE.
- **Secondary:** arXiv q-fin and SSRN pre-prints 2020-2026 with an identified author affiliation and a replication artifact.
- **Tertiary (flagged):** Bouchaud/CFM, Rosenbaum, Gatheral, Lopez de Prado working papers; GitHub repos with empirical tables.
- **Excluded:** blog posts, non-refereed industry white papers, vendor-sponsored research.

### 1.3 Search strategy
Queries against arXiv q-fin.TR / q-fin.ST / q-fin.PM / q-fin.MF, SSRN FEN / FMG / RFS networks, Google Scholar, NBER, BIS WP series. Keyword sets rotated across {"order flow imbalance", "dealer gamma", "0DTE", "intraday momentum", "macro announcement drift", "Hawkes", "rough volatility", "transfer entropy", "prediction market", "FOMC embedding"}. Backward and forward citation tracing from seed papers (Kolm-Turiel, Bouchaud-Bonart, Rosenbaum-Gatheral, Bollerslev-Li-Xue).

### 1.4 Evidence hierarchy flags
- `[P]` peer-reviewed journal article.
- `[WP]` working paper from recognized institution (SSRN, NBER, Fed staff report, IMF, BIS). Not peer-reviewed.
- `[PP]` pre-print (arXiv / SSRN author-posted) with no institutional imprimatur.
- `[TEXTBOOK]` published monograph; treat as reference, not as empirical primary source.
- `[T]` tertiary (practitioner, forum).
- `[VERIFIED]` DOI/ID loaded and metadata confirmed on publisher page during 2026-04-15 remediation.
- `[UNVERIFIED — citation removed 2026-04-15]` applied to original cites whose DOI 404'd, resolved to a different paper, or could not be confirmed within the effort budget.

All non-[P] sources carry interpretive risk; see section 5.

---

## 2. Grounding citations for H001-H026 backlog

### 2.1 Tier-1 microstructure and dealer-flow hypotheses

**H001 - Dealer GEX regime.**
Mechanism: option dealers short-gamma sell rallies and buy dips, flipping the intraday return autocorrelation sign when aggregate dealer gamma crosses zero.
- `[WP]` Barbon, Beckmeyer, Buraschi, Moerke, *The role of intermediaries in options markets*, [SSRN 3925725](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3925725) `[VERIFIED]`. Working paper (not yet peer-reviewed in RFS). Original draft cite `10.1093/rfs/hhae001` resolved to a different paper (Congressional-viewpoints / social-media study); that DOI has been removed.
- `[P]` Ni, Pearson, Poteshman, White, *Does option trading have a pervasive impact on underlying stock prices?*, Review of Financial Studies 34, 2021, [10.1093/rfs/hhaa082](https://doi.org/10.1093/rfs/hhaa082) `[VERIFIED]`.
- `[WP]` Baltussen, Terstegge, Whelan, *Option-implied hedging pressure and the equity risk premium*, SSRN 2023 `[UNVERIFIED — abstract ID not in original draft; retained under [WP] pending manual ID re-confirmation]`.
- Data: CBOE SPX chain + OCC volumes; dealer-inventory proxy via commercial GEX vendors or self-computed via Garleanu-Pedersen-Poteshman demand-based option-pricing decomposition.
- Testability: split intraday into gamma-positive vs gamma-negative regimes; test sign of 15-min autocorrelation.

**H010 - Deep order-flow imbalance.**
- `[P]` Kolm, Turiel, Westray, *Deep order flow imbalance: Extracting alpha at multiple horizons from the limit order book*, Mathematical Finance 33, 2023, [10.1111/mafi.12413](https://doi.org/10.1111/mafi.12413) `[VERIFIED]`.
- `[P]` Cont, Cucuringu, Zhang, *Cross-impact of order flow imbalance in equity markets*, Quantitative Finance 23, 2023, [10.1080/14697688.2023.2236159](https://doi.org/10.1080/14697688.2023.2236159) `[VERIFIED]`.
- `[P]` Cont, Kukanov, Stoikov, *The price impact of order book events*, Journal of Financial Econometrics 12, 2014, [10.1093/jjfinec/nbt003](https://doi.org/10.1093/jjfinec/nbt003) `[VERIFIED]`.
- Data: CME MBO (market-by-order) feed or CME MDP 3.0 depth.
- Non-obvious: multi-level OFI weighted by distance-to-mid outperforms L1 OFI `[PARAPHRASE — verify against Kolm-Turiel-Westray 2023 Table X]`. Prior claim of "0.56-0.58 AUC at 1-5 min" is dropped pending direct table check.

**H011 - Hawkes event-time resampling.**
- `[P]` Bacry, Mastromatteo, Muzy, *Hawkes processes in finance*, Market Microstructure and Liquidity 1, 2015, [10.1142/S2382626615500057](https://doi.org/10.1142/S2382626615500057) `[VERIFIED]`.
- `[P]` Jaisson, Rosenbaum, *Limit theorems for nearly unstable Hawkes processes*, Annals of Applied Probability 25, 2015, [10.1214/14-AAP1005](https://doi.org/10.1214/14-AAP1005) `[VERIFIED]`.
- `[P]` Morariu-Patrichi, Pakkanen, *State-dependent Hawkes processes and their application to limit order book modelling*, Quantitative Finance 22, 2022, [10.1080/14697688.2021.1983199](https://doi.org/10.1080/14697688.2021.1983199) `[VERIFIED]`.
- Non-obvious: resampling bars by integrated Hawkes intensity yields near-iid innovations `[PARAPHRASE — verify against Morariu-Patrichi-Pakkanen Table X]`.

**H012 - Transfer entropy cross-venue.**
- `[P]` Dimpfl, Peter, *Using transfer entropy to measure information flows between financial markets*, Studies in Nonlinear Dynamics & Econometrics 17, 2013, [10.1515/snde-2012-0044](https://doi.org/10.1515/snde-2012-0044) `[VERIFIED]`.
- `[TEXTBOOK]` Bossomaier, Barnett, Harre, Lizier, *An Introduction to Transfer Entropy*, Springer 2016, [10.1007/978-3-319-43222-9](https://doi.org/10.1007/978-3-319-43222-9). Methodological reference; not an empirical primary source.
- `[P]` Behrendt, Schmidt, *The Twitter myth revisited: Intraday investor sentiment, Twitter activity and individual-level stock return volatility*, Journal of Banking & Finance 96, 2018, [10.1016/j.jbankfin.2018.07.010](https://doi.org/10.1016/j.jbankfin.2018.07.010) `[VERIFIED]`.
- Data: synchronized ES, NQ, YM, RTY millisecond midquotes; lead-lag via Schreiber (2000) TE estimator with Kraskov-Stoegbauer-Grassberger k-NN.

**H013 - Square-root metaorder footprint.**
- `[P]` Toth, Lemperiere, Deremble, de Lataillade, Kockelkoren, Bouchaud, *Anomalous price impact and the critical nature of liquidity in financial markets*, Physical Review X 1, 2011, [10.1103/PhysRevX.1.021006](https://doi.org/10.1103/PhysRevX.1.021006) `[VERIFIED]`.
- `[P]` Bucci, Benzaquen, Lillo, Bouchaud, *Crossover from linear to square-root market impact*, Physical Review Letters 122, 2019, [10.1103/PhysRevLett.122.108302](https://doi.org/10.1103/PhysRevLett.122.108302) `[VERIFIED]`.
- Testability: detect footprint via rolling Almgren-like regression of return on sqrt(volume imbalance).

**H014 - MOC imbalance leakage to ES.**
- `[P]` Bogousslavsky, Muravyev, *Who trades at the close? Implications for price discovery and liquidity*, Journal of Financial Markets 66, 2023, [10.1016/j.finmar.2023.100819](https://doi.org/10.1016/j.finmar.2023.100819) `[VERIFIED]`.
- `[WP]` Hu, Murphy, *Competition for retail order flow and market quality*, [SSRN 4070056](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4070056) `[VERIFIED]`. Substitutes original draft's unresolvable `SSRN 4559305`. Related close-auction work by the same authors covers floor-broker imbalance reversals on NYSE.
- Non-obvious: NYSE imbalance feed released at 15:50 ET with second-level updates; cross-asset front-running testable as Granger causality on tick data `[PARAPHRASE — effect not directly quantified in Bogousslavsky-Muravyev for ES; own-verification required]`.

**H015 - Treasury auction WI drift.**
- `[P]` Lou, Yan, Zhang, *Anticipated and repeated shocks in liquid markets*, Review of Financial Studies 26, 2013, [10.1093/rfs/hht034](https://doi.org/10.1093/rfs/hht034) `[VERIFIED]`.
- `[WP]` Fleming, Nguyen, Rosenberg, *How do Treasury dealers manage their positions?*, Federal Reserve Bank of New York Staff Report 299 (revised) `[UNVERIFIED — staff-report number retained from draft, not re-confirmed against newyorkfed.org during this round; downgrade to [WP] is conservative]`.
- `[P]` Hu, Pan, Wang (tri-party repo pricing citation) `[UNVERIFIED — JFQA DOI 10.1017/S002210902000027X in the original draft was not re-checked in this round; citation retained but flagged]`.

### 2.2 Tier-2 macro, sentiment, policy

**H002 - Macro-surprise z-scores.**
- `[P]` Faust, Rogers, Wang, Wright, *The high-frequency response of exchange rates and interest rates to macroeconomic announcements*, Journal of Monetary Economics 54, 2007, [10.1016/j.jmoneco.2006.05.015](https://doi.org/10.1016/j.jmoneco.2006.05.015) `[UNVERIFIED — DOI not re-fetched this round; classical citation, retained]`.
- `[P]` Bollerslev, Li, Xue, *Volume, volatility, and public news announcements*, Review of Economic Studies 85, 2018, [10.1093/restud/rdx055](https://doi.org/10.1093/restud/rdx055) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Gurkaynak, Sack, Swanson, *Do actions speak louder than words?*, International Journal of Central Banking 1, 2005 (no DOI assigned). Path/target decomposition.
- `[P]` Altavilla, Brugnolini, Gurkaynak, Motto, Ragusa, *Measuring euro area monetary policy*, Journal of Monetary Economics 108, 2019, [10.1016/j.jmoneco.2019.08.016](https://doi.org/10.1016/j.jmoneco.2019.08.016) `[UNVERIFIED — not re-fetched this round; retained]`.

**H003 - Kalshi prediction-market leakage.**
- `[P]` Wolfers, Zitzewitz, *Prediction markets*, Journal of Economic Perspectives 18, 2004, [10.1257/0895330041371321](https://doi.org/10.1257/0895330041371321) `[UNVERIFIED — not re-fetched this round; classical]`.
- `[P]` Snowberg, Wolfers, Zitzewitz, *Prediction markets for economic forecasting*, Handbook of Economic Forecasting vol 2, 2013, [10.1016/B978-0-444-53683-9.00014-1](https://doi.org/10.1016/B978-0-444-53683-9.00014-1) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[TEXTBOOK]` Bouchaud, Bonart, Donier, Gould, *Trades, Quotes and Prices*, Cambridge UP 2018, [10.1017/9781316659335](https://doi.org/10.1017/9781316659335). Reference monograph. Removed from this hypothesis grounding — textbook is a general microstructure reference, not a Kalshi-specific finding.
- Flag: Kalshi-specific empirical work is largely `[PP]` / `[T]` as of 2026; H003 grounding is thin.

**H004 - FOMC semantic delta.**
- `[P]` Hansen, McMahon, *Shocking language: Understanding the macroeconomic effects of central bank communication*, Journal of International Economics 99, 2016, [10.1016/j.jinteco.2015.12.008](https://doi.org/10.1016/j.jinteco.2015.12.008) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Cieslak, Schrimpf, *Non-monetary news in central bank communication*, Journal of International Economics 118, 2019, [10.1016/j.jinteco.2019.01.012](https://doi.org/10.1016/j.jinteco.2019.01.012) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Gorodnichenko, Pham, Talavera, *The voice of monetary policy*, American Economic Review 113(2), 2023, 548-584, [10.1257/aer.20220129](https://doi.org/10.1257/aer.20220129) `[VERIFIED]`.
- `[WP]` Handlan, *Text shocks and monetary surprises: Text analysis of FOMC statements with machine learning*, working paper, Brown / University of Georgia 2022 `[VERIFIED]`. Author-hosted PDFs confirm title and content; no FRB St Louis working-paper series number is reliably attached, so the original "FRB STL WP 2020-014" tag was stripped.

**H005 - Retail 0DTE put-call.**
- `[WP]` Beckmeyer, Branger, Gayda, *Retail traders love 0DTE options... but should they?*, [SSRN 4404704](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4404704) `[VERIFIED]`. Substitutes the original draft's incorrect `SSRN 4588661`. Status: working paper (not "revise-and-resubmit JF" — that claim is stripped).
- `[WP]` Bandi, Fusari, Renò, *0DTE option pricing*, [SSRN 4503344](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4503344), *Journal of Finance* forthcoming `[VERIFIED per auditor-supplied anchor]`. Substitutes original draft's `SSRN 4361595` and wrong JFE venue.
- `[WP]` Brogaard, Han, Won, *How does zero-day-to-expiry options trading affect the volatility of underlying assets?*, [SSRN 4426358](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4426358) `[VERIFIED per auditor-supplied anchor]`. Substitutes original draft's RAPS DOI `10.1093/rapstu/raae002`, which resolves to Kubitza-Pelizzon-Sherman on CCP loss-sharing.
- Data: CBOE DataShop 0DTE tick; segregate by trade-size bucket per Boehmer-Jones-Zhang-Zhang retail-identification approach.

### 2.3 Tier-3 cross-asset and regime

**H020 - Rough-vol Hurst regime.**
- `[P]` Gatheral, Jaisson, Rosenbaum, *Volatility is rough*, Quantitative Finance 18, 2018, [10.1080/14697688.2017.1393551](https://doi.org/10.1080/14697688.2017.1393551) `[UNVERIFIED — not re-fetched this round; widely indexed, retained]`.
- `[P]` Bayer, Friz, Gatheral, *Pricing under rough volatility*, Quantitative Finance 16, 2016, [10.1080/14697688.2015.1099717](https://doi.org/10.1080/14697688.2015.1099717) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Fukasawa, Takabatake, Westphal, *Is volatility rough?*, Mathematical Finance 32, 2022, [10.1111/mafi.12337](https://doi.org/10.1111/mafi.12337) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Bennedsen, Lunde, Pakkanen, *Decoupling the short- and long-term behavior of stochastic volatility*, Journal of Financial Econometrics 20, 2022, [10.1093/jjfinec/nbaa049](https://doi.org/10.1093/jjfinec/nbaa049) `[UNVERIFIED — not re-fetched this round; retained]`.

**H021 - Live FOMC speech embedding drift.** Same anchors as H004 plus:
- `[P]` Gentzkow, Kelly, Taddy, *Text as data*, Journal of Economic Literature 57, 2019, [10.1257/jel.20181020](https://doi.org/10.1257/jel.20181020) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[PP]` Lopez-Lira, Tang, *Can ChatGPT forecast stock price movements? Return predictability and large language models*, [SSRN 4412788](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4412788) `[VERIFIED]`. Status: author-posted SSRN pre-print (2023-2024 revisions); no publisher-side confirmation of any journal acceptance — the original draft's "Journal of Finance forthcoming" claim is stripped.

**H022 - Stablecoin mint/burn to BTC to ES.**
- `[P]` Griffin, Shams, *Is Bitcoin really untethered?*, Journal of Finance 75, 2020, [10.1111/jofi.12903](https://doi.org/10.1111/jofi.12903) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Lyons, Viswanath-Natraj, *What keeps stablecoins stable?*, Journal of International Money and Finance 131, 2023, [10.1016/j.jimonfin.2022.102777](https://doi.org/10.1016/j.jimonfin.2022.102777) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Liu, Tsyvinski, Wu, *Common risk factors in cryptocurrency*, Journal of Finance 77, 2022, [10.1111/jofi.13119](https://doi.org/10.1111/jofi.13119) `[UNVERIFIED — not re-fetched this round; retained]`.

**H023 - AIS vessel arrivals to CL to ES.**
- `[P]` Brancaccio, Kalouptsidi, Papageorgiou, *Geography, transportation, and endogenous trade costs*, Econometrica 88, 2020, [10.3982/ECTA15455](https://doi.org/10.3982/ECTA15455) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[WP]` Cerutti, Gopinath, Mohommad, IMF working paper on AIS-based shipping tracking `[UNVERIFIED — exact IMF WP number not re-confirmed during this round]`.
- The draft's Adland-Jia-Strandenes 2017 cite is retained as background but tagged `[UNVERIFIED — not re-fetched this round]`.

**H024 - ERCOT/PJM plus HRRR to NG to ES.**
- `[P]` Schwartz, Smith, *Short-term variations and long-term dynamics in commodity prices*, Management Science 46, 2000, [10.1287/mnsc.46.7.893.12034](https://doi.org/10.1287/mnsc.46.7.893.12034) `[UNVERIFIED — not re-fetched this round; classical, retained]`.
- `[P]` Auffhammer, Baylis, Hausman, *Climate change is projected to have severe impacts on electricity system reliability*, PNAS 114, 2017, [10.1073/pnas.1613193114](https://doi.org/10.1073/pnas.1613193114) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Gonzato, Sgarra, *Self-exciting jumps in the oil market*, Energy Economics 100, 2021, [10.1016/j.eneco.2021.105375](https://doi.org/10.1016/j.eneco.2021.105375) `[UNVERIFIED — not re-fetched this round; retained]`.

**H025 - SOFR-IOER carry unwind.**
- `[P]` Afonso, Cipriani, Copeland, Kovner, La Spada, Martin, *The market events of mid-September 2019*, FRBNY Economic Policy Review 27(2), 2021; also NY Fed Staff Report 918 / [SSRN 3915127](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3915127) `[VERIFIED]`. Substitutes original draft's `SSRN 3778488`.
- `[WP]` Correa, Du, Liao, *US banks and global liquidity*, Federal Reserve Board IFDP 1289, 2020, [10.17016/IFDP.2020.1289](https://doi.org/10.17016/IFDP.2020.1289) `[UNVERIFIED — not re-fetched this round; retained as [WP]]`.
- `[WP]` Copeland, Duffie, Yang, *Reserves were not so ample after all*, NBER WP 29090 `[UNVERIFIED — "QJE forthcoming" claim stripped; retain as NBER WP]`.

**H026 - Implied-realized correlation divergence.**
- `[P]` Driessen, Maenhout, Vilkov, *The price of correlation risk: Evidence from equity options*, Journal of Finance 64, 2009, [10.1111/j.1540-6261.2009.01467.x](https://doi.org/10.1111/j.1540-6261.2009.01467.x) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Buss, Schoenleber, Vilkov, *Expected correlation and future market returns* `[UNVERIFIED — DOI 10.1287/mnsc.2023.4812 not re-fetched this round; retained with [P] tag pending spot-check]`.
- `[P]` Faria, Kosowski, Wang `[UNVERIFIED — JBF DOI 10.1016/j.jbankfin.2021.106099 not re-fetched this round; retained]`.

---

## 3. New angles not in the backlog (ranked by expected directional-AUC lift)

Ranking heuristic: prior published effect size on short-horizon directional accuracy, data availability to retail/pro-retail quant, and originality vs the backlog. Expected-lift bands are qualitative until empirically estimated.

### H030 - CME iceberg detection and hidden-liquidity inference (MED, downgraded from HIGH)
Mechanism: hidden iceberg orders in ES reveal institutional accumulation/distribution; refill patterns after visible slice execution precede directional moves.
- `[P]` Zotikov, *CME iceberg order detection and prediction*, Quantitative Finance 21(11), 2021, [10.1080/14697688.2020.1813904](https://doi.org/10.1080/14697688.2020.1813904) `[VERIFIED via Taylor & Francis listing]`. Substitutes the original draft's fabricated "Huang-Polak 2023 QF 10.1080/14697688.2023.2218472" citation (DOI 404s).
- `[WP]` Frey, Sandås, *The impact of hidden liquidity in limit order books*, CFS working paper 2008/48 and [SSRN 1343538](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1343538) `[VERIFIED]`. Substitutes the original draft's fabricated "Frey-Sanmartin JFM 70 2024" (unresolvable). The real author is Sandås; no 2024 JFM version exists.
- `[P]` Cebiroglu, Hautsch, *Hidden liquidity, market quality, and order submission strategies*, Journal of Financial Markets 2022, [10.1016/j.finmar.2022.100719](https://doi.org/10.1016/j.finmar.2022.100719) `[UNVERIFIED — DOI not fetched this round; substitute candidate sourced from search]`.
- Data: CME MBO with order IDs.
- Hypothesis tier downgraded HIGH → MED because the deep-learning iceberg claim rested entirely on the fabricated Huang-Polak citation; the real Zotikov paper uses Kaplan-Meier survival modeling, not deep learning.

### H031 - Cross-sectional lead-lag via Hayashi-Yoshida with asynchronous ticks (HIGH)
- `[P]` Hayashi, Yoshida, *On covariance estimation of non-synchronously observed diffusion processes*, Bernoulli 11, 2005, [10.3150/bj/1116340299](https://doi.org/10.3150/bj/1116340299) `[UNVERIFIED — not re-fetched this round; classical, retained]`.
- `[WP]` Dobrev, Schaumburg, *High-frequency cross-market trading: model-free measurement and applications*, Federal Reserve Board / AQR working paper, presented at the Atlanta Fed 2018 Financial Stability workshop `[VERIFIED as WP — original draft's IFDP number 2017-1210 is not confirmed; downgrade from [P] to [WP]]`.
- `[P]` Buccheri, Corsi, Peluso, *High-frequency lead-lag effects and cross-asset linkages*, Journal of Business and Economic Statistics 39, 2021, [10.1080/07350015.2019.1697699](https://doi.org/10.1080/07350015.2019.1697699) `[UNVERIFIED — not re-fetched this round; retained]`.

### H032 - Intraday PEAD in index constituents aggregated to ES (MED-HIGH)
- `[P]` Chordia, Goyal, Sadka, Sadka, Shivakumar, *Liquidity and the post-earnings-announcement drift*, Financial Analysts Journal 65, 2009, [10.2469/faj.v65.n4.3](https://doi.org/10.2469/faj.v65.n4.3) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` So, Wang, *News-driven return reversals: Liquidity provision ahead of earnings announcements*, Journal of Financial Economics 114, 2014, [10.1016/j.jfineco.2014.06.009](https://doi.org/10.1016/j.jfineco.2014.06.009) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Weller, *Does algorithmic trading reduce information acquisition?*, Review of Financial Studies 31, 2018, [10.1093/rfs/hhx137](https://doi.org/10.1093/rfs/hhx137) `[UNVERIFIED — not re-fetched this round; retained]`.

### H033 - VIX term-structure twist (intraday) (MED-HIGH)
- `[P]` Johnson, *Risk premia and the VIX term structure*, Journal of Financial and Quantitative Analysis 52, 2017, [10.1017/S0022109017000825](https://doi.org/10.1017/S0022109017000825) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Cheng, *The VIX premium*, Review of Financial Studies 32(1), 2019, 180-227, [10.1093/rfs/hhy062](https://doi.org/10.1093/rfs/hhy062) `[VERIFIED]`.
- `[WP]` Van Tassel, *The law of one price in equity volatility markets*, [Federal Reserve Bank of New York Staff Report 953](https://www.newyorkfed.org/research/staff_reports/sr953.html), December 2020 `[VERIFIED]`.

### H034 - Intraday momentum and end-of-day reversal on ES (MED-HIGH)
- `[P]` Gao, Han, Li, Zhou, *Market intraday momentum*, Journal of Financial Economics 129, 2018, [10.1016/j.jfineco.2018.05.009](https://doi.org/10.1016/j.jfineco.2018.05.009) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Bogousslavsky, *The cross-section of intraday and overnight returns*, Journal of Financial Economics 141, 2021, [10.1016/j.jfineco.2021.04.018](https://doi.org/10.1016/j.jfineco.2021.04.018) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Lou, Polk, Skouras, *A tug of war: Overnight versus intraday expected returns*, Journal of Financial Economics 134, 2019, [10.1016/j.jfineco.2019.03.011](https://doi.org/10.1016/j.jfineco.2019.03.011) `[UNVERIFIED — not re-fetched this round; retained]`.

### H035 - Realized semivariance asymmetry (MED)
- `[TEXTBOOK/chapter]` Barndorff-Nielsen, Kinnebrock, Shephard, *Measuring downside risk: realised semivariance*, in *Volatility and Time Series Econometrics*, OUP 2010. No DOI. Seminal.
- `[P]` Patton, Sheppard, *Good volatility, bad volatility: Signed jumps and the persistence of volatility*, Review of Economics and Statistics 97, 2015, [10.1162/REST_a_00503](https://doi.org/10.1162/REST_a_00503) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Bollerslev, Li, Patton, Quaedvlieg, *Realized semicovariances*, Econometrica 88, 2020, [10.3982/ECTA17056](https://doi.org/10.3982/ECTA17056) `[UNVERIFIED — not re-fetched this round; retained]`.

### H036 - FX carry unwind signal via JPY and CHF intraday (MED)
- `[P]` Brunnermeier, Nagel, Pedersen, *Carry trades and currency crashes*, NBER Macroeconomics Annual 23, 2008, [10.1086/593088](https://doi.org/10.1086/593088) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Menkhoff, Sarno, Schmeling, Schrimpf, *Carry trades and global foreign exchange volatility*, Journal of Finance 67, 2012, [10.1111/j.1540-6261.2012.01728.x](https://doi.org/10.1111/j.1540-6261.2012.01728.x) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Lettau, Maggiori, Weber, *Conditional risk premia in currency markets and other asset classes*, Journal of Financial Economics 114, 2014, [10.1016/j.jfineco.2014.07.006](https://doi.org/10.1016/j.jfineco.2014.07.006) `[UNVERIFIED — not re-fetched this round; retained]`.

### H037 - Treasury basis and cash-futures arb stress to equity beta (MED)
- `[WP]` Barth, Kahn, *Hedge funds and the Treasury cash-futures disconnect*, OFR WP 21-01, 2021 `[UNVERIFIED — not re-fetched this round; retained as [WP]]`.
- `[P]` Du, Hebert, Wang, *Are intermediary constraints priced?*, Review of Financial Studies 36, 2023, [10.1093/rfs/hhac083](https://doi.org/10.1093/rfs/hhac083) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[WP]` Duffie, *Still the world's safe haven? Redesigning the US Treasury market after the COVID-19 crisis*, Hutchins Center WP 62, 2020 `[UNVERIFIED — not re-fetched]`.

### H038 - ETF authorized-participant creation/redemption flow (MED)
- `[P]` Ben-David, Franzoni, Moussawi, *Do ETFs increase volatility?*, Journal of Finance 73, 2018, [10.1111/jofi.12727](https://doi.org/10.1111/jofi.12727) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[P]` Pan, Zeng, *ETF arbitrage under liquidity mismatch*, Journal of Financial Economics 143, 2022, [10.1016/j.jfineco.2021.07.001](https://doi.org/10.1016/j.jfineco.2021.07.001) `[UNVERIFIED — not re-fetched this round; retained]`.
- `[WP]` Evans, Moussawi, Pagano, Sedunov, *Operational shorting and ETF liquidity provision* (working title formerly *ETF short interest and failures-to-deliver: Naked short-selling or operational shorting?*), [SSRN 2961954](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2961954) `[VERIFIED]`. Original draft's "2024 forthcoming RFS" claim stripped — publisher-side confirmation not found; retain as [WP].

### H039 - CLS settlement window and FX liquidity reflux (LOW-MED, novel)
- `[P]` Fischer, Ranaldo, *Does FOMC news drive global FX markets?*, Journal of Banking and Finance 35, 2011, [10.1016/j.jbankfin.2011.03.002](https://doi.org/10.1016/j.jbankfin.2011.03.002) `[UNVERIFIED — not re-fetched]`.
- `[P]` Hasbrouck, Levich, *Network structure and pricing in the FX market*, Journal of Financial Economics 141, 2021, [10.1016/j.jfineco.2021.04.011](https://doi.org/10.1016/j.jfineco.2021.04.011) `[UNVERIFIED — not re-fetched]`.
- `[P]` Cipriani, La Spada, *Investors' appetite for money-like assets*, Journal of Financial Economics 140, 2021, [10.1016/j.jfineco.2020.12.009](https://doi.org/10.1016/j.jfineco.2020.12.009) `[UNVERIFIED — not re-fetched; original draft's [WP] tag upgraded to [P] pending spot-check]`.

### H040 - Natural-language FOMC minutes-release drift with LLM embeddings (MED)
- `[P]` Bybee, Kelly, Manela, Xiu, *Business news and business cycles*, Journal of Finance 79, 2024, [10.1111/jofi.13377](https://doi.org/10.1111/jofi.13377) `[VERIFIED per auditor-supplied anchor]`. Substitutes original draft's wrong DOI `10.1111/jofi.13321`.
- `[P]` Gu, Kelly, Xiu, *Empirical asset pricing via machine learning*, Review of Financial Studies 33, 2020, [10.1093/rfs/hhaa009](https://doi.org/10.1093/rfs/hhaa009) `[UNVERIFIED — not re-fetched]`.
- `[PP]` Chen, Kelly, Xiu, *Expected returns and large language models*, SSRN 4416687, 2024 `[UNVERIFIED — abstract ID not re-fetched]`.
- Model-choice note: FinBERT-Tone [Huang-Wang-Yang 2023, CAR, [10.1111/1911-3846.12832](https://doi.org/10.1111/1911-3846.12832)] `[UNVERIFIED — not re-fetched]` + sentence-transformers all-mpnet-base-v2 for delta features. BloombergGPT model-card is `[T]`.

### H041 - Triple/quad witching and expiration-week effect (MED)
- `[P]` Ni, Pearson, Poteshman, *Stock price clustering on option expiration dates*, Journal of Financial Economics 78, 2005, [10.1016/j.jfineco.2004.08.005](https://doi.org/10.1016/j.jfineco.2004.08.005) `[UNVERIFIED — not re-fetched]`.
- `[P]` Golez, Jackwerth, *Pinning in the S&P 500 futures*, Journal of Financial Economics 106, 2012, [10.1016/j.jfineco.2012.06.011](https://doi.org/10.1016/j.jfineco.2012.06.011) `[UNVERIFIED — not re-fetched]`.
- `[P]` Stivers, Sun, *Returns and option activity over the option-expiration week for S&P 100 stocks*, Journal of Banking and Finance 37, 2013, [10.1016/j.jbankfin.2013.08.003](https://doi.org/10.1016/j.jbankfin.2013.08.003) `[UNVERIFIED — not re-fetched]`.

### H042 - Volatility-targeted fund rebalancing bands (MED)
- `[P]` Moreira, Muir, *Volatility-managed portfolios*, Journal of Finance 72, 2017, [10.1111/jofi.12513](https://doi.org/10.1111/jofi.12513) `[UNVERIFIED — not re-fetched]`.
- `[P]` Barbon, Di Maggio, Franzoni, Landier, *Brokers and order flow leakage: Evidence from fire sales*, Journal of Finance 74, 2019, [10.1111/jofi.12840](https://doi.org/10.1111/jofi.12840) `[UNVERIFIED — not re-fetched]`.
- `[P]` Baltas, *The impact of crowding on the performance of trend-following strategies*, Journal of Alternative Investments 23, 2020, [10.3905/jai.2020.1.099](https://doi.org/10.3905/jai.2020.1.099) `[UNVERIFIED — not re-fetched]`.

### H043 - Options market maker crash-put reinsurance (LOW-MED, novel)
- `[P]` Garleanu, Pedersen, Poteshman, *Demand-based option pricing*, Review of Financial Studies 22, 2009, [10.1093/rfs/hhp005](https://doi.org/10.1093/rfs/hhp005) `[UNVERIFIED — not re-fetched]`.
- `[P]` Bollen, Whaley, *Does net buying pressure affect the shape of implied volatility functions?*, Journal of Finance 59, 2004, [10.1111/j.1540-6261.2004.00647.x](https://doi.org/10.1111/j.1540-6261.2004.00647.x) `[UNVERIFIED — not re-fetched]`.
- `[P]` Andersen, Fusari, Todorov, *The pricing of short-term market risk*, Journal of Finance 72, 2017, [10.1111/jofi.12486](https://doi.org/10.1111/jofi.12486) `[UNVERIFIED — not re-fetched]`.

### H044 - Weekly option OI pin migration (LOW-MED) — tier downgraded
- `[P]` Barraclough, Whaley, *Early exercise of put options on stocks*, Journal of Finance 67, 2012, [10.1111/j.1540-6261.2012.01761.x](https://doi.org/10.1111/j.1540-6261.2012.01761.x) `[UNVERIFIED — not re-fetched]`.
- `[WP]` Ernst, Spatt, *Equity market microstructure in the age of 0DTE*, Office of Financial Research Brief 2024 `[UNVERIFIED — not re-fetched; [WP]]`.
- Fewer peer-reviewed 2024-26 confirmations; tier already LOW-MED.

### H045 - CTA trend-follower breakout thresholds (MED)
- `[P]` Baltas, Kosowski, *Demystifying time-series momentum strategies: Volatility estimators, trading rules and pairwise correlations*, Market Microstructure and Liquidity 3, 2017, [10.1142/S2382626617500046](https://doi.org/10.1142/S2382626617500046) `[UNVERIFIED — not re-fetched]`.
- `[P]` Moskowitz, Ooi, Pedersen, *Time series momentum*, Journal of Financial Economics 104, 2012, [10.1016/j.jfineco.2011.11.003](https://doi.org/10.1016/j.jfineco.2011.11.003) `[UNVERIFIED — not re-fetched]`.
- `[WP]` Bouchaud et al., *Black was right: Price is within a factor 2 of value*, SSRN 3070850, 2018 `[UNVERIFIED — not re-fetched; [WP]]`.

### H046 - Bond-equity correlation sign-flip regime (MED)
- `[P]` Campbell, Pflueger, Viceira, *Macroeconomic drivers of bond and equity risks*, Journal of Political Economy 128, 2020, [10.1086/706290](https://doi.org/10.1086/706290) `[UNVERIFIED — not re-fetched]`.
- `[P]` David, Veronesi, *What ties return volatilities to price valuations and fundamentals?*, Journal of Political Economy 121, 2013, [10.1086/671794](https://doi.org/10.1086/671794) `[UNVERIFIED — not re-fetched]`.
- `[P]` Cieslak, Pang, *Common shocks in stocks and bonds*, Journal of Financial Economics 142, 2021, [10.1016/j.jfineco.2021.04.035](https://doi.org/10.1016/j.jfineco.2021.04.035) `[UNVERIFIED — not re-fetched]`.

### H047 - Liquidity-tier time-of-day seasonality with Fourier features (LOW-MED)
- `[P]` Admati, Pfleiderer, *A theory of intraday patterns: Volume and price variability*, Review of Financial Studies 1, 1988, [10.1093/rfs/1.1.3](https://doi.org/10.1093/rfs/1.1.3) `[UNVERIFIED — not re-fetched; classical]`.
- `[P]` Hong, Wang, *Trading and returns under periodic market closures*, Journal of Finance 55, 2000, [10.1111/0022-1082.00203](https://doi.org/10.1111/0022-1082.00203) `[UNVERIFIED — not re-fetched]`.

### H048 - Repo specialness and overnight equity flow (LOW-MED, novel)
- `[P]` Duffie, *Special repo rates*, Journal of Finance 51, 1996, [10.1111/j.1540-6261.1996.tb02694.x](https://doi.org/10.1111/j.1540-6261.1996.tb02694.x) `[UNVERIFIED — not re-fetched; classical]`.
- `[P]` Jordan, Jordan, *Special repo rates: An empirical analysis*, Journal of Finance 52, 1997, [10.1111/j.1540-6261.1997.tb02750.x](https://doi.org/10.1111/j.1540-6261.1997.tb02750.x) `[UNVERIFIED — not re-fetched]`.
- `[P]` Infante, Vardoulakis, *Collateral runs*, Review of Financial Studies 34, 2021, [10.1093/rfs/hhaa074](https://doi.org/10.1093/rfs/hhaa074) `[UNVERIFIED — not re-fetched]`.

### H049 - News-wire latency arbitrage across Bloomberg / Reuters / Dow Jones (LOW, infra-bound)
- `[P]` Foucault, Hombert, Rosu, *News trading and speed*, Journal of Finance 71, 2016, [10.1111/jofi.12302](https://doi.org/10.1111/jofi.12302) `[UNVERIFIED — not re-fetched]`.
- `[P]` Laughlin, Aguirre, Grundfest, *Information transmission between financial markets in Chicago and New York*, Financial Review 49, 2014, [10.1111/fire.12036](https://doi.org/10.1111/fire.12036) `[UNVERIFIED — not re-fetched]`.
- `[P]` Shkilko, Sokolov, *Every cloud has a silver lining: Fast trading, microwave connectivity, and trading costs*, Journal of Finance 75, 2020, [10.1111/jofi.12864](https://doi.org/10.1111/jofi.12864) `[UNVERIFIED — not re-fetched]`.

### H050 - Analyst revision and recommendation-change flow aggregated to index (LOW-MED)
- `[P]` Jegadeesh, Kim, Krische, Lee, *Analyzing the analysts: When do recommendations add value?*, Journal of Finance 59, 2004, [10.1111/j.1540-6261.2004.00657.x](https://doi.org/10.1111/j.1540-6261.2004.00657.x) `[UNVERIFIED — not re-fetched]`.
- `[P]` Loh, Stulz, *When are analyst recommendation changes influential?*, Review of Financial Studies 24, 2011, [10.1093/rfs/hhq094](https://doi.org/10.1093/rfs/hhq094) `[UNVERIFIED — not re-fetched]`.
- `[P]` Kadan, Madureira, Wang, Zach, *Conflicts of interest and stock recommendations*, Review of Financial Studies 22, 2009, [10.1093/rfs/hhn109](https://doi.org/10.1093/rfs/hhn109) `[UNVERIFIED — not re-fetched]`.

### H051 - Social-media attention bursts with language-model sentiment (LOW-MED)
- `[P]` Da, Engelberg, Gao, *In search of attention*, Journal of Finance 66, 2011, [10.1111/j.1540-6261.2011.01679.x](https://doi.org/10.1111/j.1540-6261.2011.01679.x) `[UNVERIFIED — not re-fetched]`.
- `[P]` Bradley, Hanousek, Jame, Xiao, *Place your bets? The value of investment research on Reddit's WallStreetBets*, Review of Financial Studies 37, 2024, [10.1093/rfs/hhad074](https://doi.org/10.1093/rfs/hhad074) `[UNVERIFIED — not re-fetched]`.
- `[PP]` Lopez-Lira, Tang 2024 (see H021).

### H052 - Institutional 13F + short-interest overlay for sector rotation (LOW)
- `[P]` Agarwal, Jiang, Tang, Yang, *Uncovering hedge fund skill from the portfolio holdings they hide*, Journal of Finance 68, 2013, [10.1111/jofi.12052](https://doi.org/10.1111/jofi.12052) `[UNVERIFIED — not re-fetched]`.
- `[P]` Boehmer, Jones, Zhang, *Which shorts are informed?*, Journal of Finance 63, 2008, [10.1111/j.1540-6261.2008.01324.x](https://doi.org/10.1111/j.1540-6261.2008.01324.x) `[UNVERIFIED — not re-fetched]`.

### H053 - Multi-timeframe 09:45→10:30 ET ES/NQ regression with opening-bar mediation (Tier 2b, designed 2026-04-28)

**Remediation note (2026-04-30):** the prior entry for H053 in this slot ("Sovereign CDS and cross-border risk-on signal") was a *stale candidate framing* that never materialised as a registered hypothesis. The actual H053, registered at `designed` status 2026-04-28 and brought into main on 2026-04-30, is the multi-timeframe ES/NQ intraday regression described below. Closes follow-up `P1-LIT-REVIEW-H053-STALE-ENTRY-RESOLVE`.

Pre-registration: [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md). Per-hypothesis-register companion lit review: [research/01_hypothesis_register/H053/lit_review_H053_2026-04-28.md](../../research/01_hypothesis_register/H053/lit_review_H053_2026-04-28.md). Buildout plan: [plan/buildouts/h053_buildout_2026-04-28.md](../../plan/buildouts/h053_buildout_2026-04-28.md). Audit trail (design): [docs/audits/audit_trail_2026-04-28_h053-design.md](../../docs/audits/audit_trail_2026-04-28_h053-design.md).

Mechanism: predictand `y_{i,t} = log(C_i(10:30 ET, t)) − log(C_i(09:45 ET, t))` for `i ∈ {ES, NQ}` on the roll-adjusted continuous front-month substrate; predictor `X_{i,t}` is a 09:45 ET snapshot of three timeframes (daily ≥60 sessions, hourly ≥5 sessions, 5/15-min 24-48 hr); mediator `M_{i,t}` is summary stats of the 09:30–09:45 ET opening 15-min bar. Three pre-registered model arms enter a flat Hansen SPA family with three ex-ante slots: Arm 1 ElasticNet, Arm 2 LightGBM, Arm 3 LLM-with-context (Tier-3 conditional). Primary gate is paired Sharpe-differential (Ledoit-Wolf 2008 studentized circular-block bootstrap) vs both a passive-long benchmark and a time-of-day fixed-effects benchmark, AND realized max-DD non-worse than the passive-long benchmark — conjunctive intersection-union per Hochberg-Tamhane 1987 (addresses Heston-Korajczyk-Sadka 2010 periodicity confound). Secondary gate is a user-facing categorical `K × 3` archetype-bias-target-probability table with isotonic calibration (Niculescu-Mizil & Caruana 2005); BSS > 0 vs climatological prior + reliability slope ∈ [0.7, 1.3]. Mediation block (Imai-Keele-Tingley 2010) is descriptive-only — sequential ignorability + SUTVA are heroic in 1-min-bar futures; a significant `NIE` annotates but does not promote past Sharpe gate.

Primary anchors (verified 2026-04-28 via the H053 design audit-remediate-loop; DOIs match design.md frontmatter):
- `[P]` Lou, Polk, Skouras, *A Tug of War: Overnight Versus Intraday Expected Returns*, Journal of Financial Economics 134(1):192-213, 2019, [10.1016/j.jfineco.2019.03.011](https://doi.org/10.1016/j.jfineco.2019.03.011). Canonical anchor for the overnight→opening-bar→intraday return decomposition that motivates the H053 mediator.
- `[P]` Heston, Korajczyk, Sadka, *Intraday Patterns in the Cross-Section of Stock Returns*, Journal of Finance 65(4):1369-1407, 2010, [10.1111/j.1540-6261.2010.01573.x](https://doi.org/10.1111/j.1540-6261.2010.01573.x). Half-hour reversal periodicity — Stage-0 sanity-check anchor + benchmark for the time-of-day fixed-effects conjunctive gate.
- `[P]` Andersen, Bollerslev, Diebold, Labys, *Modeling and Forecasting Realized Volatility*, Econometrica 71(2):579-625, 2003, [10.1111/1468-0262.00418](https://doi.org/10.1111/1468-0262.00418). Realized-volatility methodology underpinning the mediator log-range feature.
- `[P]` Andersen, Bollerslev, *Answering the Skeptics: Yes, Standard Volatility Models Do Provide Accurate Forecasts*, International Economic Review 39(4):885-905, 1998, [10.2307/2527343](https://doi.org/10.2307/2527343). RV-based volatility-model forecast-evaluation methodology supporting the realized-volatility feature definitions.
- `[P]` Imai, Keele, Tingley, *A General Approach to Causal Mediation Analysis*, Psychological Methods 15(4):309-334, 2010, [10.1037/a0020761](https://doi.org/10.1037/a0020761). Mediation framework (descriptive use only per H053 §1 critical interpretive note).
- Full citation set in [design.md](../../research/01_hypothesis_register/H053/design.md) frontmatter — 33 entries (28 external citations + 5 ADR cross-references), audit-remediated 2026-04-28.

---

## 4. Methodological citations (inference tooling for the project)

Methodological citations below are classical and widely indexed. DOIs were not re-fetched during this round; they are tagged `[UNVERIFIED — not re-fetched]` to make the provenance uniform with the rest of the document. A future round may spot-check.

### 4.1 Standard errors and bandwidth selection
- `[P]` Newey, West, *Automatic lag selection in covariance matrix estimation*, Review of Economic Studies 61, 1994, [10.2307/2297912](https://doi.org/10.2307/2297912).
- `[P]` Andrews, *Heteroskedasticity and autocorrelation consistent covariance matrix estimation*, Econometrica 59, 1991, [10.2307/2938229](https://doi.org/10.2307/2938229).
- `[P]` Kiefer, Vogelsang, *A new asymptotic theory for HAR tests*, Econometric Theory 21, 2005, [10.1017/S0266466605050632](https://doi.org/10.1017/S0266466605050632).

### 4.2 Sharpe ratio inference
- `[P]` Lo, *The statistics of Sharpe ratios*, Financial Analysts Journal 58, 2002, [10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453).
- `[P]` Opdyke, *Comparing Sharpe ratios: So where are the p-values?*, Journal of Asset Management 8, 2007, [10.1057/palgrave.jam.2250084](https://doi.org/10.1057/palgrave.jam.2250084).
- `[P]` Ledoit, Wolf, *Robust performance hypothesis testing with the Sharpe ratio*, Journal of Empirical Finance 15, 2008, [10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002).
- `[WP]` Ledoit, Wolf, *Robust performance hypothesis testing with smooth functions of population moments*, [SSRN 4461030](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4461030). Status: working paper; original draft's "Journal of Empirical Finance 78, 2024 forthcoming" claim stripped pending publisher-side confirmation.

### 4.3 Multiple-testing across strategies
- `[P]` White, *A reality check for data snooping*, Econometrica 68, 2000, [10.1111/1468-0262.00152](https://doi.org/10.1111/1468-0262.00152).
- `[P]` Hansen, *A test for superior predictive ability*, Journal of Business and Economic Statistics 23, 2005, [10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063).
- `[P]` Romano, Wolf, *Stepwise multiple testing as formalized data snooping*, Econometrica 73, 2005, [10.1111/j.1468-0262.2005.00615.x](https://doi.org/10.1111/j.1468-0262.2005.00615.x).
- `[P]` Harvey, Liu, Zhu, *...and the cross-section of expected returns*, Review of Financial Studies 29, 2016, [10.1093/rfs/hhv059](https://doi.org/10.1093/rfs/hhv059).

### 4.4 Backtest overfitting and CV
- `[P]` Bailey, Borwein, Lopez de Prado, Zhu, *The probability of backtest overfitting*, Journal of Computational Finance 20, 2017, [10.21314/JCF.2016.322](https://doi.org/10.21314/JCF.2016.322).
- `[TEXTBOOK]` Lopez de Prado, *Advances in Financial Machine Learning*, Wiley 2018. Canonical reference for combinatorially purged cross-validation (Ch 7) and purging/embargoing (Ch 7-8). Not peer-reviewed; use as reference.
- `[P]` Lopez de Prado, *The 10 reasons most machine learning funds fail*, Journal of Portfolio Management 44, 2018, [10.3905/jpm.2018.44.6.120](https://doi.org/10.3905/jpm.2018.44.6.120).
- `[P]` Cerqueira, Torgo, Mozetic, *Evaluating time series forecasting models*, Machine Learning 109, 2020, [10.1007/s10994-020-05910-7](https://doi.org/10.1007/s10994-020-05910-7).

### 4.5 Diebold-Mariano and forecast comparison
- `[P]` Diebold, Mariano, *Comparing predictive accuracy*, Journal of Business and Economic Statistics 13, 1995, [10.1080/07350015.1995.10524599](https://doi.org/10.1080/07350015.1995.10524599).
- `[P]` Giacomini, White, *Tests of conditional predictive ability*, Econometrica 74, 2006, [10.1111/j.1468-0262.2006.00718.x](https://doi.org/10.1111/j.1468-0262.2006.00718.x).

### 4.6 Realized variance estimators
- `[P]` Andersen, Bollerslev, Diebold, Labys, *The distribution of realized exchange rate volatility*, JASA 96, 2001, [10.1198/016214501750332965](https://doi.org/10.1198/016214501750332965).
- `[P]` Barndorff-Nielsen, Hansen, Lunde, Shephard, *Designing realised kernels*, Econometrica 76, 2008, [10.3982/ECTA6495](https://doi.org/10.3982/ECTA6495).
- `[P]` Ait-Sahalia, Mykland, Zhang, *A tale of two time scales*, JASA 100, 2005, [10.1198/016214504000001880](https://doi.org/10.1198/016214504000001880).

### 4.7 Classification calibration (directional AUC context)
- `[P]` DeLong, DeLong, Clarke-Pearson, *Comparing the areas under two or more correlated ROC curves*, Biometrics 44, 1988, [10.2307/2531595](https://doi.org/10.2307/2531595).
- `[TEXTBOOK/chapter]` Platt, *Probabilistic outputs for support vector machines*, in *Advances in Large Margin Classifiers*, MIT Press 1999. No DOI.
- `[P]` Niculescu-Mizil, Caruana, *Predicting good probabilities with supervised learning*, ICML 2005, [10.1145/1102351.1102430](https://doi.org/10.1145/1102351.1102430).

### 4.8 Deep-learning finance benchmarks
- `[P]` Zhang, Zohren, Roberts, *DeepLOB*, IEEE Transactions on Signal Processing 67, 2019, [10.1109/TSP.2019.2907260](https://doi.org/10.1109/TSP.2019.2907260).
- `[P]` Sirignano, Cont, *Universal features of price formation*, Quantitative Finance 19, 2019, [10.1080/14697688.2019.1622295](https://doi.org/10.1080/14697688.2019.1622295).
- `[P]` Gu, Kelly, Xiu 2020 (see H040).

---

## 5. Evidence-hierarchy flags and interpretive risk

- `[PP]` Handlan FOMC ML paper (H004, H021): working-paper status; use for hypothesis generation, not for parameter calibration.
- `[PP]` Lopez-Lira and Tang LLM return paper (H021, H051): no publisher-side journal confirmation; treat as pre-print.
- `[WP]` Baltussen-Terstegge-Whelan (H001): SSRN, not peer-reviewed. The peer-reviewed anchor for dealer-gamma pressure is Ni et al 2021 RFS (Barbon et al remains [WP]).
- `[WP]` Barth-Kahn OFR 2021 (H037): government-agency working paper; peer-reviewed anchor is Du-Hebert-Wang 2023 RFS.
- `[WP]` Cerutti-Gopinath-Mohommad IMF WP (H023): staff analysis; AIS methodology is peer-reviewed via Brancaccio et al 2020 Econometrica.
- `[T]` BloombergGPT / Voyage-finance model cards (H040): non-peer-reviewed vendor publications. Do not cite for empirical performance claims; model-provenance metadata only.
- `[T]` SqueezeMetrics and SpotGamma GEX products (H001): commercial proxies. Reproduce from first principles before deployment.
- `[WP]` Ernst-Spatt OFR brief (H044): policy brief, not peer-reviewed article.
- `[WP]` Barbon et al. SSRN 3925725 (H001): working paper; original draft's RFS 2024 DOI was fabricated.
- `[WP]` Brogaard-Han-Won (H005): SSRN; not RAPS.
- `[WP]` Bandi-Fusari-Renò (H005): SSRN; *JF* forthcoming, not JFE.

### Replication-artifact notes
Any factor implemented from the backlog or from section 3 must be reproduced against the published effect size before trading. Where the anchor paper provides no code, the implementation must be unit-tested against the paper's Table 1 or equivalent on an overlapping sample. Discrepancies beyond 1 sigma of the reported effect trigger a re-derivation round under the [audit-remediate-loop](C:\Users\skoir\.claude\skills\audit-remediate-loop) skill.

### Open gaps requiring further search
- Kalshi-specific peer-reviewed empirics (H003) — as of 2026-04 the venue is too new for journal-level coverage.
- Live FOMC audio + vision embeddings (H021) — Gorodnichenko et al 2023 AER anchors audio; video embedding drift remains speculative.
- ERCOT/PJM to NG to ES chain (H024) — each link is peer-reviewed but the composite chain is not jointly documented.

---

## 6. Verification audit trail 2026-04-15

### 6.1 Citations removed as fabricated / unresolvable

| Location (old line) | Stated | Action |
|---|---|---|
| H001 / Barbon et al. | RFS 2024 `10.1093/rfs/hhae001` | DOI resolves to "Using Social Media to Identify the Effects of Congressional Viewpoints on Asset Prices" (different paper). Substituted with [SSRN 3925725](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3925725). Status: [WP]. |
| H005 / Brogaard-Han-Won | RAPS 14 2024 `10.1093/rapstu/raae002` | DOI resolves to Kubitza-Pelizzon-Sherman *Loss sharing in central clearinghouses*. Substituted with [SSRN 4426358](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4426358). Status: [WP]. |
| H005 / Bandi-Fusari-Renò | JFE forthcoming, SSRN 4361595 | Substituted with [SSRN 4503344](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4503344), *Journal of Finance* forthcoming. |
| H005 / Beckmeyer-Branger-Gayda | SSRN 4588661 | Correct ID is [SSRN 4404704](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4404704). "Revise-and-resubmit JF" claim stripped. |
| H014 / Hu-Murphy | SSRN 4559305 | Unresolvable to stated content. Substituted with [SSRN 4070056](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4070056) *Competition for retail order flow and market quality*. |
| H025 / Afonso et al. | SSRN 3778488 | Correct ID is [SSRN 3915127](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3915127); also FRBNY Staff Report 918 and EPR 27(2) 2021. |
| H030 / Huang-Polak iceberg | QF 2023 `10.1080/14697688.2023.2218472` | DOI 404. Paper not found. Substituted with Zotikov 2021 QF [10.1080/14697688.2020.1813904](https://doi.org/10.1080/14697688.2020.1813904). Hypothesis tier downgraded HIGH → MED. |
| H030 / Frey-Sanmartin | JFM 70 2024 `10.1016/j.finmar.2024.100911` | DOI exists but resolves to a Journal of Financial Markets 2024 article (not by these authors). The real author pairing is Frey-Sandås (working paper, 2008/[SSRN 1343538](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1343538)). Original cite removed; substituted. Status: [WP]. |
| H031 / Dobrev-Schaumburg | IFDP 2017-1210 | IFDP number not confirmed; real paper is a 2018 Atlanta Fed workshop WP. Downgraded from [P] to [WP]. |
| H040 / Bybee-Kelly-Manela-Xiu | JoF 2024 `10.1111/jofi.13321` | Wrong DOI. Correct DOI [10.1111/jofi.13377](https://doi.org/10.1111/jofi.13377). |
| H038 / Evans et al. | "2024 forthcoming RFS" | No publisher-side confirmation; retained as [WP] [SSRN 2961954](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2961954). |
| H021 / Lopez-Lira-Tang | "JoF forthcoming" | Stripped; remains [PP] [SSRN 4412788](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4412788). |
| H025 / Copeland-Duffie-Yang | "QJE forthcoming" | Stripped; retained as NBER WP 29090. |
| H003 / Bouchaud et al. *TQP* | [WP] tag | Retagged [TEXTBOOK]; removed from Kalshi-specific grounding (general reference only). |
| L4.2 / Ledoit-Wolf 2024 | "JEF 78, 2024 forthcoming" | Stripped; retained as [WP] [SSRN 4461030](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4461030). |

### 6.2 Citations verified clean (publisher-page metadata confirmed this round)

- Ni-Pearson-Poteshman-White 2021 RFS `10.1093/rfs/hhaa082`
- Kolm-Turiel-Westray 2023 Math Finance `10.1111/mafi.12413` (auditor-anchor)
- Cont-Cucuringu-Zhang 2023 QF `10.1080/14697688.2023.2236159`
- Cont-Kukanov-Stoikov 2014 JFE `10.1093/jjfinec/nbt003`
- Bacry-Mastromatteo-Muzy 2015 MML `10.1142/S2382626615500057`
- Jaisson-Rosenbaum 2015 AAP `10.1214/14-AAP1005`
- Morariu-Patrichi-Pakkanen 2022 QF `10.1080/14697688.2021.1983199`
- Dimpfl-Peter 2013 SNDE `10.1515/snde-2012-0044`
- Behrendt-Schmidt 2018 JBF `10.1016/j.jbankfin.2018.07.010`
- Toth et al. 2011 PRX `10.1103/PhysRevX.1.021006`
- Bucci et al. 2019 PRL `10.1103/PhysRevLett.122.108302`
- Bogousslavsky-Muravyev 2023 JFM `10.1016/j.finmar.2023.100819`
- Gorodnichenko-Pham-Talavera 2023 AER `10.1257/aer.20220129`
- Cheng 2019 RFS `10.1093/rfs/hhy062`
- Bybee-Kelly-Manela-Xiu 2024 JoF `10.1111/jofi.13377`
- Van Tassel 2020 NY Fed SR 953
- Afonso et al. 2021 FRBNY EPR / SR 918 / SSRN 3915127
- Beckmeyer-Branger-Gayda SSRN 4404704
- Evans-Moussawi-Pagano-Sedunov SSRN 2961954
- Bandi-Fusari-Renò SSRN 4503344 (auditor-anchor)
- Brogaard-Han-Won SSRN 4426358 (auditor-anchor)
- Barbon et al. SSRN 3925725 (auditor-anchor)
- Lopez-Lira-Tang SSRN 4412788 (via SSRN search)
- Handlan working paper (author-hosted PDF)

### 6.3 Citations retained but UNVERIFIED this round

All citations not in 6.1 or 6.2 are tagged `[UNVERIFIED — not re-fetched this round]` inline in sections 2-4. They are classical or widely-indexed entries that the original draft assembled from standard reading lists. They should be spot-checked in round 2 before any of them drives a hypothesis into Phase 4 empirical work. Total: roughly 55 citations.

### 6.4 Hypotheses whose grounding is now too weak

Criteria: the round-1 audit removed a primary anchor and no clean substitute with equivalent empirical content was found, or the tier rested on a fabricated citation.

- **H030** (iceberg detection) — downgraded HIGH → MED. Original "deep-learning iceberg" claim was supported entirely by the fabricated Huang-Polak 2023 and the fabricated Frey-Sanmartin 2024. Replacements (Zotikov 2021 Kaplan-Meier; Frey-Sandås 2008 CFS WP) do not support the deep-learning framing; the hypothesis survives at MED tier as a survival-modeling / hidden-liquidity signal, not a deep-learning signal.
- **H003** (Kalshi prediction-market leakage) — already LOW and flagged; further weakened because the removed Bouchaud et al. "textbook" cite was the only micro-structure anchor. Recommend moving to `archived(null)` in the backlog unless a Kalshi-specific empirical paper is found.
- **H044** (weekly option OI pin migration) — already LOW-MED and resting on two non-primary citations; Ernst-Spatt is an OFR brief, not peer-reviewed; Barraclough-Whaley is tangential. Recommend `archived(null)` pending a 2024-26 peer-reviewed 0DTE pinning paper.

No other hypothesis is recommended for archival in this round.
