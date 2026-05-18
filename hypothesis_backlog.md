# Hypothesis Backlog

Project-canonical register of every signal, transform, or angle considered for SKIE-Universe. The backlog is **append-only** — null and negative results stay in the file to document the search space already covered. Per [ADR-0013](docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), there is no `archive` stage; every hypothesis progresses through the lifecycle below, irrespective of KPI values.

Each row gets a dedicated design doc in [research/01_hypothesis_register/](research/01_hypothesis_register/) before execution, with pre-registered hypothesis, data, estimator, assumptions, and stopping rule. Per-hypothesis stage trackers, KPI report cards, and failure logs live alongside design.md in that folder.

## Lifecycle (ADR-0013 §1)

`queued` → `designed` → `exploration-in-progress` → `kpi-report-emitted` → `ninjascript-implemented` → `paper-trade-active` → `paper-trade-evaluated` → `live-promoted`

Legacy disposition labels (`running`, `evaluated`, `archived(positive|null|negative)`) are preserved verbatim in pre-ADR-0013 stage rows per the non-loss mandate (ADR-0013 §4.1) but no longer drive promotion decisions. See the per-hypothesis [stage tracker](research/01_hypothesis_register/INDEX.md) for current state.

---

## At-a-glance status (2026-05-18)

Live snapshot of every hypothesis with a stage row beyond `queued`. For the full per-stage history see [research/01_hypothesis_register/INDEX.md](research/01_hypothesis_register/INDEX.md). For emitted KPI report cards see [research/01_hypothesis_register/RESULTS_INDEX.md](research/01_hypothesis_register/RESULTS_INDEX.md).

| ID | Title (short) | Tier | Current stage | Headline OOS result |
|---|---|---|---|---|
| **H050** | HMM regime-conditioned ES/NQ directional | 2b | `kpi-report-emitted` | Catastrophic. Gated arms ES −81%, NQ −84% realized OOS; T_H050 CIs exclude zero on the **negative** side; forward 252-session P(loss)=100%. HMM-gating actively harms the directional signal. |
| **H051** | HMM-gated Kalman pairs ES/NQ basis | 2b | `designed` | Not yet executed. |
| **H052a** | HMM regime-gated first-hour ORB on ES/NQ | 2b | `kpi-report-emitted` (operator-declined-ninjascript) | Non-significant null on hypothesis-of-record (T_H052a CIs cover zero). Strongest cell is **NQ unconditional ORB** (+10.61% realized; P(loss)=18.56%) — literature-replication artifact, not the gating hypothesis. |
| **H052b** | HMM regime-gated QQQ 0DTE long-call scalp | 2b | `designed` | Vendor-gated on QQQ 0DTE option chain; not yet executed. |
| **H053** | Multi-TF 09:45→10:30 ET regression + opening-bar mediation | 2b | `kpi-report-emitted` (v3) | CI-marginal across 4 arms; NQ LightGBM strongest (**+10.8%** realized 2-yr OOS, max-DD 3.7%, forward median $10,713 / P(loss)=15%). ES ElasticNet weakest (forward P(loss)=69%). |
| **H054** | Anti-gate first-hour ORB on CME ES | 2b | `kpi-report-emitted` | Point-positive (+3.50% realized anti-gated, P(loss)=29.2%) but CIs cover zero. Structurally low-power: anti-gate fires 7/237 sessions (2.95% trade rate). |
| **H055** | Mechanized wick-rejection scalping (HMM-deferred v3) | 2b | `kpi-report-emitted` (**v2**; canonical substrate) | v2 re-emitted 2026-05-18 on canonical post-Phase-O.8 substrate `317429e4...` (closes `P1-H055-V2-RERUN-ON-CANONICAL-SUBSTRATE`); qualitative v1 findings preserved with small drift (C3 basket +20.2% / C9 +13.9% / MGC C3 +87.0% strongest single-symbol-cell). MPPM CI deferred per `P1-H055-MPPM-RHO-1-CI-PRIMITIVE`; 4 design.md §11.2 BLOCKING preconditions remain. |
| **H062** | Intraday Donchian-channel breakout on {ES, NQ, MGC, SIL} at super-Kelly grid with BOCD halt + switching-bandit redirect | 2c | `kpi-report-emitted` (**v2**; canonical substrate + MPPM/inner-CV fixes) | v2 (2026-05-18) corrects v1 critical defects (MPPM double-log + in-sample-CV). MPPM(ρ=1) sign-flips +0.095 [-0.343, +0.540] (vs v1 -0.223); realized +217.57% basket ROI (vs v1 +43%); same 93% MaxDD; τ_3=+0.737 strongly skew-positive; quarter-Kelly unanimous across 84/84 walk-forward folds (now genuinely WFCV-selected). 2026 sub-window: MGC +8.03% / basket +2.01%. CIs marginal on all 4 ADR-0017 primary metrics. |
| **H065** | Intraday Donchian-channel breakout with ATR-scaled TP overlay (H062 + M-grid; Turtle System 2 partial inheritance) | 2b | `kpi-report-emitted` (v1; H_1 null on all TP cells) | TP overlay at M ∈ {1.0, 1.5, 2.0, 2.5} R-multiples DOES NOT improve over H062 v1 no-TP baseline at basket level; M=1.0 INVERTS skew direction (τ_3 −0.034 vs M=∞ +0.807); SIL M=∞ fixed-rebase standalone is strongest project-wide cell (MPPM CI [+0.087, +0.459] excludes zero pos; +446% ROI; MaxDD 25%); NQ structurally infeasible at $10K starting equity. |
| H056 | Per-component ML successor of H055 (ADR-0015 Layer 1) | 2b | `queued` | Sequenced after H055 KPI emission + ADR-0016 SKIE-NINJA-Volatility audit. |
| H057 | Stacking master successor of H056 (ADR-0015 Layer 2) | 2b | `queued` | Sequenced after H056. |
| H058 | Multi-TF attention orchestrator (ADR-0015 Layer 3) | 2b | `queued` | Sequenced after H057. |
| H059 | Live probability display layer (presentation-only) | 2b | `queued` | Sequenced after H058 calibration. |

**Project-wide finding through 2026-05-11**: across H050 + H052a + H053 + H054 the Sharpe-family inferential anchor consistently clustered around zero while realized $10K trajectories diverged materially. [ADR-0017 survival-constrained optimization paradigm](docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) (2026-05-08) demoted Sharpe to a secondary KPI and elevated terminal-wealth-q05 + Calmar-differential + profit-factor + R-multiple-mean as the primary inferential vector for every hypothesis from H055 forward.

---

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

## Tier 2b — regime/state (added 2026-04-20 per ADR-0006)

The active research front. Hypotheses H050-H055 carry pre-registered design.md + per-stage tracker + KPI report cards where emitted; H056-H059 are queued per the [H055 successor tree](plan/buildouts/h055_successor_tree_2026-05-06.md).

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H050 | HMM regime-conditioned ES/NQ intraday directional signal | [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Ryou et al. 2020](https://doi.org/10.3390/su12177031); [Guidolin-Timmermann 2007](https://doi.org/10.1016/j.jedc.2006.12.004); design [H050/design.md](research/01_hypothesis_register/H050/design.md); KPI [v1](research/01_hypothesis_register/H050/H050_kpi_report_v1.md); stage [stage.md](research/01_hypothesis_register/H050/stage.md) | kpi-report-emitted |
| H051 | HMM-gated ES/NQ (or MES/MNQ) basis pairs trade with Kalman hedge ratio | [Johansen 1991](https://doi.org/10.2307/2938278); [Osterwald-Lenum 1992](https://doi.org/10.1111/j.1468-0084.1992.tb00013.x); West & Harrison 1997; Chan 2013; design [H051/design.md](research/01_hypothesis_register/H051/design.md) | designed |
| H052a | HMM regime-gated first-hour ORB on CME futures (ES/NQ/MNQ/MES) | [Hamilton 1989](https://doi.org/10.2307/1912559); [Guidolin-Timmermann 2007](https://doi.org/10.1016/j.jedc.2006.12.004); [Zarattini-Barbon-Aziz 2024](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284); [Holmberg-Lönnbark-Lundström 2013](https://doi.org/10.1016/j.frl.2012.09.001); design [H052a/design.md](research/01_hypothesis_register/H052a/design.md); KPI [v1](research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md); stage [stage.md](research/01_hypothesis_register/H052a/stage.md) | kpi-report-emitted (operator-declined-ninjascript) |
| H052b | HMM regime-gated QQQ first-hour long-call 0DTE scalp (SKIE-ORB-CALL overlay) | [Ryou et al. 2020](https://doi.org/10.3390/su12177031); [Guidolin-Timmermann 2007](https://doi.org/10.1016/j.jedc.2006.12.004); [Hamilton 1989](https://doi.org/10.2307/1912559); sibling repo [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE); design [H052b/design.md](research/01_hypothesis_register/H052b/design.md) | designed |
| H053 | Multi-timeframe 09:45→10:30 ET ES/NQ regression with opening-bar mediation and a categorical bias-target-probability table | [Lou-Polk-Skouras 2019](https://doi.org/10.1016/j.jfineco.2019.03.011); [Heston-Korajczyk-Sadka 2010](https://doi.org/10.1111/j.1540-6261.2010.01573.x); [Imai-Keele-Tingley 2010](https://doi.org/10.1037/a0020761); [Niculescu-Mizil-Caruana 2005](https://doi.org/10.1145/1102351.1102430); design [H053/design.md](research/01_hypothesis_register/H053/design.md); buildout [plan/buildouts/h053_buildout_2026-04-28.md](plan/buildouts/h053_buildout_2026-04-28.md); KPI [v1](research/01_hypothesis_register/H053/H053_kpi_report_v1.md) / [v2](research/01_hypothesis_register/H053/H053_kpi_report_v2.md) / [v3](research/01_hypothesis_register/H053/H053_kpi_report_v3.md); stage [stage.md](research/01_hypothesis_register/H053/stage.md) | kpi-report-emitted |
| H054 | Anti-gate first-hour ORB on CME ES (HMM-gated stress-state subset on fresh OOS) | empirical motivation H052a KPI v1; [Hamilton 1989](https://doi.org/10.2307/1912559); [Bollerslev-Tauchen-Zhou 2009](https://doi.org/10.1093/rfs/hhp008); [Hurst-Ooi-Pedersen 2017](https://www.pm-research.com/content/iijpormgmt/44/1/15); design [H054/design.md](research/01_hypothesis_register/H054/design.md); KPI [v1](research/01_hypothesis_register/H054/H054_kpi_report_v1.md); stage [stage.md](research/01_hypothesis_register/H054/stage.md) | kpi-report-emitted |
| H055 | Mechanized intraday wick-rejection scalping with deterministic trend gate (HMM-deferred to v3) on CME ES/NQ/MES/MNQ | [Lehmann 1990 QJE](https://doi.org/10.2307/2937816); [Lo-MacKinlay 1990 RFS](https://doi.org/10.1093/rfs/3.2.175); [Moskowitz-Ooi-Pedersen 2012 JFE](https://doi.org/10.1016/j.jfineco.2011.11.003); [Bouchaud-Gefen-Potters-Wyart 2004 QF](https://doi.org/10.1080/14697680400000022); [Lucca-Moench 2015 JoF](https://doi.org/10.1111/jofi.12196); design [H055/design.md](research/01_hypothesis_register/H055/design.md); pilot ledger [data/external/h055_pilot_ledger/Performance.csv](data/external/h055_pilot_ledger/Performance.csv); KPI [v1](research/01_hypothesis_register/H055/H055_kpi_report_v1.md); stage [stage.md](research/01_hypothesis_register/H055/stage.md) | kpi-report-emitted |
| H056 | Per-component ML successor of H055 — ADR-0015 Layer 1 (lifts SKIE-NINJA-Volatility under ADR-0016 audit-and-lift) | [Wolpert 1992 NN](https://doi.org/10.1016/S0893-6080(05)80023-1); [Breiman 1996 ML](https://doi.org/10.1007/BF00117832); [van der Laan-Polley-Hubbard 2007 SAGMB](https://doi.org/10.2202/1544-6115.1309); [Niculescu-Mizil-Caruana 2005 ICML](https://doi.org/10.1145/1102351.1102430); [Bailey-López de Prado 2014 JPM](https://doi.org/10.3905/jpm.2014.40.5.094); roadmap [plan/buildouts/h055_successor_tree_2026-05-06.md](plan/buildouts/h055_successor_tree_2026-05-06.md); architecture [ADR-0015](docs/decisions/ADR-0015-component-stacking-master-architecture.md); lift protocol [ADR-0016](docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md) | queued |
| H057 | Stacking master successor of H056 — ADR-0015 Layer 2 (Super Learner / MoE / BMA / FWLS) | [van der Laan-Polley-Hubbard 2007 SAGMB](https://doi.org/10.2202/1544-6115.1309); [Jacobs-Jordan-Nowlan-Hinton 1991 Neural Comp](https://doi.org/10.1162/neco.1991.3.1.79); [Hoeting-Madigan-Raftery-Volinsky 1999 Stat Sci](https://www.jstor.org/stable/2676803); [Sill-Takács-Mackey-Lin 2009 arXiv](https://arxiv.org/abs/0911.0460); roadmap [plan/buildouts/h055_successor_tree_2026-05-06.md](plan/buildouts/h055_successor_tree_2026-05-06.md) | queued |
| H058 | Multi-TF attention orchestrator of H057 — ADR-0015 Layer 3 (TF-attention master) | [Vaswani et al. 2017 NeurIPS / arXiv](https://arxiv.org/abs/1706.03762); [Andersen-Bollerslev-Diebold-Labys 2003 ECTA](https://doi.org/10.1111/1468-0262.00418); roadmap [plan/buildouts/h055_successor_tree_2026-05-06.md](plan/buildouts/h055_successor_tree_2026-05-06.md) | queued |
| H059 | Live probability display layer — calibrated direction probability + first-passage-time price targets (presentation-only) | Karatzas & Shreve 1991 *Brownian Motion and Stochastic Calculus* Springer ISBN 978-0387976556; [Niculescu-Mizil-Caruana 2005 ICML](https://doi.org/10.1145/1102351.1102430); [Gneiting-Katzfuss 2014 Annual Rev Stat](https://doi.org/10.1146/annurev-statistics-062713-085831); roadmap [plan/buildouts/h055_successor_tree_2026-05-06.md](plan/buildouts/h055_successor_tree_2026-05-06.md) | queued |

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

## Tier 2c — cross-asset futures (added 2026-05-12 per ADR-0023)

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H060 | Cross-futures time-series momentum (TSMOM) on equal-weighted basket {ES, NQ, MGC, SIL} — pre-cost research-only v1 per operator 2026-05-12 zero-cost decision | [Moskowitz-Ooi-Pedersen 2012 JFE 104(2):228-250](https://doi.org/10.1016/j.jfineco.2011.11.003) canonical; [Hurst-Ooi-Pedersen 2017 JPM 44(1):15-29](https://doi.org/10.3905/jpm.2017.44.1.015) 137-yr backtest; [Huang-Li-Wang-Zhou 2020 JFE 137(3):695-712](https://doi.org/10.1016/j.jfineco.2020.04.003) post-publication decay; [Hong-Stein 1999 JoF 54(6):2143-2184](https://doi.org/10.1111/0022-1082.00184) gradual-info-diffusion mechanism; design [H060/design.md](research/01_hypothesis_register/H060/design.md); lit-review [H060/lit_review_H060_2026-05-12.md](research/01_hypothesis_register/H060/lit_review_H060_2026-05-12.md) | designed |
| H061 | H060 v2: cross-futures TSMOM with full-size NYMEX WTI (CL) added to the basket; brings energy futures to the cross-asset breadth | Same TSMOM canon as H060; substrate-extension blocked on `P1-H060-V2-WITH-CL-FULL-SIZE` follow-up (~$240 USD Databento extraction per 2026-05-12 cost-dossier) | queued |
| H062 | Intraday N-bar Donchian-channel breakout on 4-asset CME basket {ES, NQ, MGC, SIL} at super-Kelly multiplier grid {0.25..2.5} with BOCD decay-detector halt + switching-bandit redirect; primary inference MPPM(ρ=1) > 0 on stationary-bootstrap CI per ADR-0018 D-1 | [Faith 2007 *Way of the Turtle* McGraw-Hill ISBN 978-0071486644](https://www.amazon.com/Way-Turtle-Secret-Methods-Successful/dp/0071486646) (*practitioner*) Turtle System 1/2 channel-breakout canon; [Marshall-Cahan-Cahan 2008 JBF 32(9):1810-1819 DOI 10.1016/j.jbankfin.2007.12.011](https://doi.org/10.1016/j.jbankfin.2007.12.011) commodity-futures-rule SPA-null result; [Hsu-Kuan 2005 JFE 3(4):606-628 DOI 10.1093/jjfinec/nbi026](https://doi.org/10.1093/jjfinec/nbi026) data-snooping-corrected channel-breakout (per [2026-05-18 erratum](research/01_hypothesis_register/_erratum_hsu_kuan_2005_2026-05-18.md): finding is young-vs-mature markets, NOT small-vs-large-cap); [Holmberg-Lönnbark-Lundström 2013 FRL 10(1):27-33 DOI 10.1016/j.frl.2012.09.001](https://doi.org/10.1016/j.frl.2012.09.001) intraday-ORB-on-futures; [Hong-Stein 1999 JoF 54(6):2143-2184 DOI 10.1111/0022-1082.00184](https://doi.org/10.1111/0022-1082.00184) underreaction-mechanism causal anchor; [Adams-MacKay 2007 arXiv:0710.3742](https://arxiv.org/abs/0710.3742) BOCD halt; [Garivier-Moulines 2011 ALT LNCS 6925:174-188 DOI 10.1007/978-3-642-24412-4_16](https://doi.org/10.1007/978-3-642-24412-4_16) D-UCB switching-bandit; design [H062/design.md](research/01_hypothesis_register/H062/design.md); lit-review [H062/lit_review_H062_2026-05-14.md](research/01_hypothesis_register/H062/lit_review_H062_2026-05-14.md); KPI [v1](research/01_hypothesis_register/H062/H062_kpi_report_v1.md); stage [stage.md](research/01_hypothesis_register/H062/stage.md) | kpi-report-emitted (v1; v2 BLOCKING on MPPM double-log + walk-forward-inner-CV remediation per 2026-05-18 audit) |

## Tier 4 — execution / portfolio

| ID | Angle | Mechanism | Status |
|---|---|---|---|
| H040 | Stack Tier-1 directional gates on existing vol/size/breakout models | internal SKIE-Ninja ensemble | queued |
| H041 | Kelly-fractional sizing with Sharpe-bootstrap CI floor | [Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084) | queued |
| H042 | Hansen SPA gate across the full accumulated strategy universe | [Hansen 2005, JBES](https://doi.org/10.1198/073500105000000063) | queued |

## Tier 5 — meta-portfolio (added 2026-05-12 per ADR-0020)

| ID | Angle | Mechanism | Status |
|---|---|---|---|
| MPV1 | Meta-portfolio across emitted hypothesis arms (equal-weight 1/N default; inverse-variance and Ledoit-Wolf shrinkage-MVO alternatives) | [Grinold 1989 JPM 15(3):30-37 DOI 10.3905/jpm.1989.409211](https://doi.org/10.3905/jpm.1989.409211) Fundamental Law of Active Management `IR ≈ IC·√breadth`; [DeMiguel-Garlappi-Uppal 2009 RFS 22(5):1915-1953 DOI 10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075) 1/N robustness under small-N | queued (pre-reg pending `P1-MPV1-PRE-REGISTRATION`) |

## H100-H149 — liquidity-provision research track (reserved 2026-05-12 per ADR-0021)

| ID | Angle | Mechanism | Status |
|---|---|---|---|
| H100 | First-hour-RTH passive limit-order quoting around the 09:30-10:00 ET opening range; Avellaneda-Stoikov reservation-price framework | [Avellaneda-Stoikov 2008 QF 8(3):217-224 DOI 10.1080/14697680701381228](https://doi.org/10.1080/14697680701381228); adverse-selection cost via [Glosten-Milgrom 1985 DOI 10.1016/0304-405X(85)90044-3](https://doi.org/10.1016/0304-405X(85)90044-3) / [Kyle 1985 Econometrica 53(6):1315-1335 DOI 10.2307/1913210](https://doi.org/10.2307/1913210) λ / [Hasbrouck 1991 J Finance 46(1):179-207 DOI 10.1111/j.1540-6261.1991.tb03749.x](https://doi.org/10.1111/j.1540-6261.1991.tb03749.x) VAR | reserved (BLOCKED on `P1-ORDERBOOK-INGEST-SCOPE-DESIGN` + `P1-CME-MDP3-LICENSE-NEGOTIATION`) |
| H101-H149 | Successor liquidity-provision hypotheses (regime-gated, multi-symbol, options market-making, etc.) | TBD per ADR-0021 successor-tree pattern | reserved |

## H200-H249 — synthetic-substrate-augmentation research track (reserved 2026-05-12 per memo)

| ID | Angle | Mechanism | Status |
|---|---|---|---|
| H200 | TimeGAN-augmented H052a NQ unconditional ORB OOS evaluation across N=1,000 synthetic paths; pilot for the synthetic-substrate research thread | [Yoon-Jarrett-van der Schaar 2019 *NeurIPS* TimeGAN](https://papers.nips.cc/paper/8789-time-series-generative-adversarial-networks); [Wiese et al 2020 Quant GANs QF 20(9):1419-1440 DOI 10.1080/14697688.2020.1730426](https://doi.org/10.1080/14697688.2020.1730426); [Cont 2001 stylized facts QF 1(2):223-236 DOI 10.1080/713665670](https://doi.org/10.1080/713665670) validation gate | reserved (memo proposal-only; pre-reg gated on `P1-SYNTHETIC-SUBSTRATE-PHASE-0-LITCHECK`) |
| H201-H249 | Successor synthetic-substrate hypotheses (multi-symbol, regime-conditional, diffusion-based, etc.) | TBD | reserved |

---

## 2026-05-12 — ADR-0018 + 0019 + 0020 + 0022 paradigm-expansion cascade

[ADR-0018 regime-conditional aggressive-growth paradigm](docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) (2026-05-12) amends every hypothesis's §10 (decision rule) from Sharpe-differential to MPPM(ρ=1) per [Goetzmann-Ingersoll-Spiegel-Welch 2007 RFS](https://doi.org/10.1093/rfs/hhm025) and lifts the ¼-Kelly cap to a grid-search over `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5} × f_Kelly-optimal`. §1-§7 frozen pre-reg sections preserved verbatim. Cascade tracked under `P1-ADR-0018-DESIGN-MD-CASCADE` (BLOCKING-BEFORE-NEXT-STAGE-3-RUN).

[ADR-0019 barbell payoff-shape screening](docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) (2026-05-12) adds mandatory `payoff-shape-{skew-positive, skew-flat, skew-negative}` KPI annotation via L-skewness τ_3 per [Hosking 1990](https://www.jstor.org/stable/2345653) on per-trade R-multiple distribution; extends ADR-0014 §3.2 canonical results summary to 13 tables when in force.

[ADR-0020 meta-portfolio orchestrator](docs/decisions/ADR-0020-meta-portfolio-orchestrator.md) (2026-05-12) reserves the new MPV-series (above) for cross-hypothesis meta-portfolio research per [Grinold 1989](https://doi.org/10.3905/jpm.1989.409211) Fundamental Law `IR = IC·√breadth`.

[ADR-0022 causal-mechanism vs correlation-only annotation](docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) (2026-05-12) mandates §1.3 in every new design.md from 2026-05-12 forward with claim-type label (`causal-mechanism` / `correlation-only` / `hybrid`), four-field *who/what/why/when* mechanism description, and E-value/robustness anchor. Retroactive labeling table for H050-H055 supplied at ADR-0022 §Consequences. Cascade tracked under `P1-ADR-0022-DESIGN-MD-CASCADE`.

The [docs/research_notes/memo_synthetic-substrate-augmentation_2026-05-12.md](docs/research_notes/memo_synthetic-substrate-augmentation_2026-05-12.md) memo scopes the H200-series (above) as a research thread; decision-to-adopt deferred.

---

## 2026-05-08 — ADR-0017 inheritance cascade

[ADR-0017 survival-constrained optimization paradigm](docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) (2026-05-08) inherits at design-time for every hypothesis from H055 forward (H055, H056, H057, H058, H059, plus all parallel-track variants in [plan/buildouts/h055_successor_tree_2026-05-06.md](plan/buildouts/h055_successor_tree_2026-05-06.md)). Each design.md §1 statement under ADR-0017 inheritance is written under the survival-constrained paradigm from inception (no Sharpe-differential T_H statistic in §1; Sharpe-family computation reported as KPI annotation per ADR-0017 §1.2). The 8 hard kill-switch constraints K-1..K-8 (per ADR-0017 §5) and the drawdown-constrained Kelly sizing primitive (per ADR-0017 §4.1) are mandatory inheritance for every hypothesis from H055 forward.

For the existing frozen hypotheses H050/H051/H052a/H052b/H053/H054, ADR-0017 amends §8+§10 promotion-decision-rule layer per ADR-0013 §"Frozen pre-registration amendment" §1-§4 amendment discipline (the §1 T_H statistic in each is preserved verbatim as a secondary KPI per ADR-0013 §1-§7 immutability). Cascade tracked under `P1-ADR-0017-DESIGN-MD-CASCADE` (BLOCKING-BEFORE-NEXT-STAGE-3-RUN per the ADR-0013 P1-ADR-0013-DISPOSITION-FRAMEWORK-REFACTOR precedent).

## 2026-04-23 — Tier-2b split

H052 split into two siblings: **H052a** (HMM-gated ORB on CME futures ES/NQ/MNQ/MES) and **H052b** (HMM-gated QQQ 0DTE long-call scalp; the original H052 renamed, content unchanged). Rationale: the SKIE-ORB-CALL first-hour directional signal is economically separable from its long-premium-call execution wrapper; running it on futures tests the regime-gating content on a prior-art-null underlying (directional futures ≈50% AUC per project prior-art context), isolating the HMM gate as the sole new empirical content. Data substrate for H052a is already live (raw 1-min); H052b remains vendor-gated on the QQQ 0DTE option chain. Both enter the same Hansen SPA universe snapshot so no inflation of the multiple-testing family.

## Round-1 remediation adjustments (2026-04-15)

Lit-check audit invalidated three cites grounding these hypotheses. Status updates:
- **H003** → `archived(null)` above.
- **H030** (iceberg detection) → downgrade Tier-2 HIGH to MED; deep-learning framing unsupported, survives as survival / hidden-liquidity.
- **H044** (weekly OI pin migration) → `archived(null)`; mechanism unsupported by current citations.

New items append with sequential IDs. Negative/null results move to `archived(null)` but **stay in the file** — they document the search space we've covered. Per ADR-0013 §4.1 non-loss, the `archived(null)` label is preserved verbatim from the pre-ADR-0013 lifecycle; future stage transitions follow the ADR-0013 lifecycle above.
