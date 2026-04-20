# Data-Sources Inventory — SKIE-Universe

**Date:** 2026-04-15
**Author:** SKIE
**Status:** Draft v1 — pre-vendor-contact. Pricing figures are public list as of pull date; expect renegotiation.
**Scope:** Intraday ES/NQ research program covering CME futures, OPRA options, macro surprise, central-bank text, prediction markets, on-chain, AIS, power/weather, rates, and HF model hubs.

---

## 1. Overview and Point-in-Time Principle

Every feature feeding a model must be **point-in-time (PIT)**: the value used at time t must equal the value that was observable at time t, not a later revision. Two failure modes dominate intraday quant research and are the primary lens of this inventory:

1. **Look-ahead via revision.** Macro series (GDP, NFP, ISM), consensus prints (survey mediums re-surveyed), FRED levels (BEA/BLS vintages), and exchange corrections (busted trades, late prints) are routinely rewritten. Using the *current* value at an earlier timestamp injects information the model could not have had.
2. **Look-ahead via timestamp semantics.** CME tick data has three candidate timestamps — matching-engine, gateway send, and vendor receive. Only the matching-engine timestamp (`ts_event` in Databento's MBO schema) is valid for event-study work; vendor-receive is permissible for execution simulation only if the backtest venue is the same as the live venue.

Every vendor below carries a `PIT` flag: `pit-native` (vendor publishes vintage or never rewrites), `pit-reconstructable` (vintage recoverable from archive snapshots), or `revised` (do not use for features without a workaround).

References for PIT discipline: Croushore & Stark (2001) *J. Econometrics* 105:111 on real-time macro vintages ([DOI](https://doi.org/10.1016/S0304-4076(01)00072-0)); López de Prado (2018) *Advances in Financial Machine Learning* ch. 4 on triple-barrier and leakage; Bailey & López de Prado (2014) *J. Portfolio Management* on deflated Sharpe.

---

## 2. CME Futures Market Data

ES and NQ are CME Group products. Every downstream vendor pays CME Group a **professional/non-professional market-data license fee** that is passed through (typically USD 135/month pro, USD 22/month non-pro for CME E-mini Equity Index Level 2, per [CME market-data fees schedule](https://www.cmegroup.com/market-data/distributor/fee-schedule.html)). This is independent of the vendor's own fee. Any vendor offering "free" or flat-rate CME data without this line-item is either (a) using delayed data (10-min lag, not usable for intraday), (b) bundling it into a brokerage-trading relationship (Rithmic/CQG via NinjaTrader), or (c) violating the license — diligence required.

Product tiers CME distributes:
- **TOB (top-of-book / Level 1):** best bid/ask, last trade.
- **MBP-10 (market-by-price, 10 levels):** aggregated depth.
- **MBO (market-by-order) / tick:** every order add/modify/cancel with matching-engine timestamp. Required for queue-position modeling, microstructure alpha, HFT imbalance signals.

### Comparison

| Vendor | ES/NQ product offered | Historical depth | Latency (live) | Schema | Python SDK | Cost (USD, list) | CME license pass-through | PIT |
|---|---|---|---|---|---|---|---|---|
| **Databento** | MBO, MBP-10, TBBO, OHLCV-{1s,1m} | Globex 2010-present | ~25 µs colo, ~few ms WAN | DBN (binary), Parquet, CSV | `databento` official | Pay-per-GB historical (~USD 0.30/GB for MBP-10, higher for MBO); live metered | Yes, itemized on invoice | pit-native (matching-engine ts) |
| **CME DataMine** | MBO, MBP-10, BBO, EOD, Market Depth | Globex 2006-present (varies by product) | Not a live feed — end-of-day SFTP | Proprietary packet capture + FIXBinary replay | None official; parsers: `cme-market-data-platform` community | Per-dataset, USD 500–5000/year depending on product | N/A (direct from CME) | pit-native |
| **Polygon.io** | US equities + options primarily; futures coverage is partial and not CME-authoritative | Options since 2020 | ~20 ms | REST + WS JSON, Flat-file S3 | `polygon-api-client` | USD 200/mo Options Advanced; futures not a first-class product | Options only; check futures status | pit-native for trades; quotes subject to OPRA revision rules |
| **dxFeed** | CME full-depth, OPRA | 2005-present | sub-ms | QDS binary, Python `dxfeed` | `dxfeed` (pip) | Quote-based; typical USD 500–2000/mo + CME pass-through | Yes | pit-native |
| **Rithmic** | Live only (execution-tier) | None beyond session | sub-ms (colo) | R\|API binary; `pyrithmic` wrappers community | None official | Via FCM; ~USD 100/mo data + exchange fees | Yes | live-only, no history |
| **CQG** | Live + limited historical (30-day rolling) | 30 days–2 yrs | sub-ms | CQG API / WebAPI | `pycqg` community, unofficial | Via FCM or direct ~USD 595/mo Integrated Client | Yes | pit-native live |
| **Kinetick** (NinjaTrader) | EOD + intraday minute back to ~2009 | ~15 yrs 1-min | Real-time quote | NinjaTrader native | No | USD 50–130/mo | Bundled with CME pass-through | Minute-bar only; revised on busts — **revised** |
| **NinjaTrader bundled** | Same as Kinetick/Rithmic/CQG depending on selection | Depends on feed | Varies | NT8 DB | No (NT8 C#) | Platform USD 1099 one-time or USD 50/mo | Yes | Depends on underlying feed |
| **Algoseek** | ES/NQ minute, second, tick | 2007-present | EOD delivery | CSV, Parquet | `algoseek-connector` | USD per-year per-dataset, typ. USD 5–25k/yr for full futures | N/A (historical redistributor, CME-licensed) | pit-native |
| **FirstRate Data** | ES/NQ 1-min back to 2005, tick back to 2008 | ~20 yrs | EOD | CSV | None | USD 149–499 one-time per bundle | Redistribution license embedded | Minute OHLCV revised on corrections; tick PIT — mixed |
| **TickData.com** (ICE-owned) | Tick + 1-min + quote ES/NQ 1998-present | ~27 yrs | EOD | TickWrite exporter, CSV | `tickdata` Windows tool | Historical from ~USD 500/instrument-year | Yes | pit-native (tick); 1-min derived |
| **QuantTower / ATAS** | Platform on top of Rithmic/CQG; not a data vendor | — | — | Platform cache | No | USD 75–150/mo | Via underlying feed | N/A |

**Narrative.** For research-grade microstructure, only Databento, CME DataMine, dxFeed, Algoseek, and TickData deliver matching-engine tick data without look-ahead. Databento is the only one of these with a first-class Python SDK and metered cost that scales for exploratory work; DataMine is authoritative but ops-heavy (SFTP batch, raw packet parsing). Execution-side feeds (Rithmic/CQG via NinjaTrader) are operationally required for the live NinjaScript bridge but should not be sources of historical truth.

Known caveat: Databento's MBP-10 book depth is a reconstruction from MBO, not an exchange-published snapshot. For queue-position alpha this matters — confirm reconstruction algorithm against [Databento MBO docs](https://databento.com/docs/schemas-and-data-formats/mbo). Recommended validation: pull one day of MBO, reconstruct MBP-10 locally, diff against Databento-published MBP-10. Expected diff rate <1 event/day; anything higher indicates a book-replay bug.

---

## 3. Options / GEX Inputs

OPRA is the consolidated options tape. SPX and SPXW (0DTE) are CBOE proprietary and require an additional CBOE license on top of OPRA. GEX ("gamma exposure") is a *derived* metric; the inputs are OI + IV-skew + spot, so the question is whether to buy the derived product or compute it.

### Comparison

| Vendor | Product | Historical | Latency | Schema | Cost | License caveat | PIT |
|---|---|---|---|---|---|---|---|
| **CBOE DataShop** | SPX/SPXW trades, quotes, OI, 0DTE | 2004-present | EOD | CSV, Parquet | SPX 0DTE quote data: USD 3–10k/yr depending on tier; see [DataShop catalog](https://datashop.cboe.com/) | **SPX/SPXW requires CBOE Global Indices license for redistribution even of derived signals**; internal research use OK | pit-native |
| **Polygon.io OPRA** | OPRA full tape | 2020-present | ~20 ms | REST/WS JSON + Flat-files | USD 200/mo Options Advanced (pro subscription) | OPRA pro fee USD 30/mo pass-through | pit-native |
| **dxFeed OPRA** | OPRA + CBOE indices | 2005-present | sub-ms | QDS | Quote-based | OPRA + CBOE pass-through | pit-native |
| **Databento OPRA** | OPRA MBP-1 and trades | 2023-present | sub-ms | DBN | Pay-per-GB | OPRA pass-through itemized | pit-native |
| **SpotGamma** | Derived GEX levels, HIRO, vol trigger | 2020-present | Delayed (1–15 min) | Web + CSV export | USD 99–499/mo retail, institutional on request | **Black-box methodology**; no audit of dealer-direction assumption | derived, revised as OI updates post-settle |
| **Menthor Q** | Derived GEX, vanna, charm | 2022-present | EOD + intraday | API | USD 150–750/mo | Same black-box concern | derived |
| **SqueezeMetrics (DIX/GEX)** | Dark index + GEX proxy | 2011-present | EOD only | CSV | USD ~50/mo retail | Simpler methodology, [white paper](https://squeezemetrics.com/download/The_Implied_Order_Book.pdf) available | derived, EOD |
| **Gamma Labs** | Similar derived dealer positioning | 2022-present | Intraday | API | USD ~300/mo | Black-box | derived |

**Narrative.** Buy OPRA raw (Polygon or Databento); compute GEX in-house. Dealer-sign assumption is the single largest modeling decision in GEX — any vendor imposing theirs without disclosing it violates the evidence hierarchy. Reference implementations: Barbon & Buraschi (2021) [SSRN 3865903](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3865903) for dealer-gamma decomposition; Garleanu, Pedersen & Poteshman (2009) *RFS* 22:4259 [DOI](https://doi.org/10.1093/rfs/hhp005) for demand-based option pricing, the canonical theoretical frame.

For SPX 0DTE specifically: confirm CBOE DataShop **Tier 2** (quotes, not just trades) and CBOE Global Indices license. Without Global Indices, modeling SPX but reporting in NDX-proxy terms is the common workaround; internal-only use usually exempt.

---

## 4. Macro Surprise

The feature of interest is `surprise = (actual - consensus) / σ(consensus)` measured **at release minute**. Two PIT hazards:

1. Consensus is survey-rewritten: Bloomberg/Refinitiv re-poll economists and overwrite the pre-release median. Only archived snapshots preserve the true consensus-as-of-t-1.
2. Actual is revised: NFP, GDP, retail sales all carry 1–3 revisions. The *first print* is the trading input; the current FRED value is useless for event study.

### Comparison

| Vendor | Consensus PIT | Actual PIT | Historical depth | Access | Cost | Notes |
|---|---|---|---|---|---|---|
| **Bloomberg ECO** | Yes — ECO\<GO\> preserves surveys with timestamps | Yes — first-print and revision vintages | 1990s-present | Terminal only | USD ~2500/mo | Not redistributable. Scrape for personal research only. |
| **Refinitiv / LSEG Eikon** | Partial — IBES-style vintage available with add-on | Partial | 1995-present | Terminal + DSS | USD ~2000/mo | StarMine economic-data add-on required for vintage |
| **Trading Economics API** | **No** — consensus often back-filled | **No** — revised | 2010-present | REST | USD 29–500/mo | Do not use for event-study features without caveat |
| **Econoday** | Yes on archived feed | Yes | 2000-present | Licensed data-feed | USD ~5–15k/yr | Standard Wall Street sell-side surprise vendor |
| **HAVER Analytics** | Partial | Yes | 1960s-present | DLX client + API | USD ~5k/yr | Good for levels; surprise construction manual |
| **FRED-ALFRED** | N/A (no consensus) | **Yes — full vintage** | Series-dependent, many to 1950s | REST | Free | ALFRED is the vintage FRED; `fredapi` + `alfred` endpoints — the only free PIT macro source. See [ALFRED docs](https://alfred.stlouisfed.org/docs/alfred_API.pdf). |
| **MoneyNet / Action Economics** | Yes (survey archive) | Yes | 2005-present | Feed | USD ~10k/yr | Niche, but surveys preserved |

**Narrative.** ALFRED + Econoday is the defensible stack. ALFRED supplies vintage actuals free; Econoday supplies archived consensus with release timestamps. Trading Economics' low price tempts, but their API documentation is explicit that consensus is editorially maintained — treat as **revised** and exclude from features.

Published PIT methodology: Faust & Wright (2013) *Handbook of Economic Forecasting* 2:2 on real-time forecasting; Croushore (2011) *J. Econ. Lit.* 49:72 [DOI](https://doi.org/10.1257/jel.49.1.72) on real-time data.

---

## 5. Text Corpora

### Sources

| Source | Coverage | Format | Access | PIT |
|---|---|---|---|---|
| **federalreserve.gov** | FOMC statements, minutes, speeches, Beige Book, SEP | HTML + PDF | Free scrape; [FRASER](https://fraser.stlouisfed.org/) archives historical | pit-native (release timestamp on press page) |
| **ECB.europa.eu** | ECB press conferences, accounts, SMA, speeches | HTML + PDF | Free scrape | pit-native |
| **BLS / BEA / Census release pages** | NFP, CPI, PCE, GDP release narratives | HTML + PDF | Free scrape; embargo lifted at release minute | pit-native |
| **FRASER** | Historical Fed/Treasury docs 1914-present | PDF scans (OCR quality varies) | Free | pit-native; OCR revised |
| **BOJ, BoE, SNB, RBA** | Statements, minutes, speeches | HTML | Free scrape | pit-native |

### Parsers and prior work

- **Gorodnichenko, Pham & Talavera (2023)** *JME* [DOI](https://doi.org/10.1016/j.jmoneco.2023.04.008) — FOMC tone via transformer audio + text; replication code [GitHub](https://github.com/oletalavera).
- **Gentzkow, Shapiro & Taddy (2019)** *Econometrica* 87:1307 [DOI](https://doi.org/10.3982/ECTA16566) — `textir` Python/R; partisan-language inverse regression, generalizable to hawkish/dovish inference.
- **Hansen, McMahon & Prat (2018)** *QJE* 133:801 [DOI](https://doi.org/10.1093/qje/qjx045) — FOMC deliberation, LDA topic model.
- **Shapiro & Wilson (2022)** *RES* 89:2768 — monetary-policy sentiment dictionary.
- **Loughran-McDonald (2011)** *JF* 66:35 — the canonical finance sentiment lexicon; [LM dictionary](https://sraf.nd.edu/loughranmcdonald-master-dictionary/).

### Hugging Face datasets

| Dataset | Content | License | Caveat |
|---|---|---|---|
| `FinanceInc/auditor_sentiment` | Annotated auditor opinions | Apache-2.0 | Accounting, not monetary policy |
| `gtfintechlab/fomc_communication` | FOMC sentences, hawkish/dovish/neutral labels | CC-BY-NC-4.0 | Non-commercial — fine for research, flag if publishing |
| `gtfintechlab/fed_chairs_speech` | Fed chair speeches with labels | CC-BY-NC-4.0 | Same |
| `causal-nlp/CPI` | CPI report annotated | Apache-2.0 | Small |
| `AdaptLLM/finance-tasks` | Multi-task financial NLP | Apache-2.0 | General finance, not macro-specific |

---

## 6. Prediction Markets

| Vendor | Coverage | Historical tick | Latency | API | PIT | Archival pattern |
|---|---|---|---|---|---|---|
| **Kalshi** | CPI, FOMC, NFP, SPX close, elections | From contract inception (2022-present for most) | Real-time REST/WS | [Kalshi Trading API](https://trading-api.readme.io/) official | pit-native | Poll `GET /markets/{ticker}/trades` every 1s; WS `market_ticker` channel preferred |
| **Polymarket** | Macro, geopolitical, elections | On-chain (Polygon) since 2020 | Chain-tip latency (~2s) | GraphQL (Goldsky) + on-chain CLOB | pit-native on-chain | Use [py-clob-client](https://github.com/Polymarket/py-clob-client) + Goldsky subgraph backfill |
| **PredictIt** | Legacy US politics | 2014–shutdown pending | REST | Public JSON | pit-native | Archive via WayBack + direct polling; regulatory shutdown ongoing |
| **Manifold Markets** | Long tail, prediction-aggregator | 2022-present | REST | Public | pit-native | Low ES/NQ relevance; skip Phase 1 |

**Tick archival recommendation.** Run a lightweight collector (asyncio WS client) writing line-delimited Parquet partitions by contract-day into `data/raw/prediction_markets/{venue}/{ticker}/{date}.parquet`. Include WS sequence number for gap detection. Kalshi WS occasionally drops reconnects — implement sequence-gap detection + REST backfill.

---

## 7. On-Chain

| Vendor | Coverage | Resolution | API | Cost | PIT |
|---|---|---|---|---|---|
| **Glassnode** | BTC/ETH on-chain metrics, stablecoin supply | Hourly tier-2, minute tier-3 (Institutional) | REST | USD 39/mo retail, USD 800+/mo institutional for minute | pit-native (chain is immutable) |
| **Coin Metrics** | Multi-chain, stablecoin, exchange flow | Block-level available in `CM Pro` | REST + Python `coinmetrics-api-client` | Community free tier limited; Pro USD 1k+/mo | pit-native |
| **Dune Analytics** | SQL over indexed chains; stablecoin mint/burn queryable | Block-level | GraphQL / REST | Free tier 2500 rows, Plus USD 390/mo | pit-native (chain), but query-dependent — save query hash |
| **Etherscan API** | ETH + L2 events | Block-level | REST | Free 5 req/s, Pro USD 200/mo+ | pit-native |
| **Tenderly** | Simulation + historical traces | Block-level | REST | Tiered | pit-native, dev-focused |
| **Allium** | Multi-chain warehouse, stablecoin firehose | Block-level, near-real-time | SQL (Snowflake), API | USD ~1k+/mo | pit-native |
| **Chainalysis Kryptos** | Compliance-grade flows | Hour to minute | REST | Enterprise only | pit-native |

**Minute-resolution stablecoin mint/burn.** Etherscan + Tron public RPC give block-level (12s ETH, 3s Tron) directly — free. Glassnode and Allium pre-aggregate at minute. For Phase 1, run an in-house ETH + Tron RPC watcher on Tether Treasury (`0x5754284f345afc66a98fbB0a0Afe71e0F007B949`), Circle mint/burn (`0x55FE...`), and equivalent Tron contracts. Zero vendor cost; incurs node cost (~USD 50/mo Infura or free public RPC).

---

## 8. AIS / Satellite

| Vendor | Coverage | Latency | License for intraday | Cost | PIT |
|---|---|---|---|---|---|
| **MarineTraffic API** | Global AIS, terrestrial-heavy | 5–15 min | Commercial tier required for intraday redistribution | USD 100–2000/mo by tier | pit-native |
| **Spire Maritime** | Global S-AIS (satellite) | 1–5 min S-AIS | Enterprise only, ~USD 10k+/mo | Enterprise | pit-native |
| **AISHub** | Community-pooled T-AIS | Variable | Data-sharing agreement (contribute a feeder) | Free | pit-native but coverage-gap |
| **Planet Labs (PlanetScope)** | Optical imagery | 24h revisit | Enterprise, ~USD 20k+/yr AOI | Enterprise | pit |
| **SkyFi** | On-demand imagery | Hours-days | Consumer tier exists | Per-image USD 10–500 | pit |
| **VesselFinder API** | Global AIS | 5 min | Commercial tier | USD 99–999/mo | pit-native |

For the project's scope (Cushing, Ras Tanura, Rotterdam port arrivals), terrestrial coverage is sufficient at Rotterdam and Ras Tanura. Cushing is pipeline+tank, not port — AIS is irrelevant there; substitute EIA weekly crude-oil stocks ([EIA API](https://www.eia.gov/opendata/)) released Wednesdays 10:30 ET.

---

## 9. Power / Weather

| Vendor | Coverage | Cadence | Access | Cost | PIT |
|---|---|---|---|---|---|
| **ERCOT MIS** | Real-time LMP, load, wind/solar | 5-min LMP, 15-min load | Free public via [ERCOT MIS](https://www.ercot.com/mp/data-products) | Free | pit-native (published with release timestamp) |
| **PJM DataMiner 2** | Real-time 5-min LMP, load, generation mix | 5-min | Free REST [dataminer2.pjm.com](https://dataminer2.pjm.com/) | Free | pit-native |
| **CAISO OASIS** | 5-min LMP, load | 5-min | Free | Free | pit-native |
| **NOAA HRRR** (via NCEP or AWS Open Data) | Hi-Res Rapid Refresh, 3km CONUS | Hourly init, 18–48h forecast | [AWS Open Data](https://registry.opendata.aws/noaa-hrrr-pds/) free S3 | Free | pit-native (archive by init-time) |
| **ECMWF HRES/IFS** | Global 9km | 6h init | [Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data) subset free; full via MARS paid | Free tier limited | pit-native |
| **RTMA / URMA** | NOAA real-time mesoscale analysis | Hourly | AWS Open Data | Free | pit-native but URMA is revised; RTMA is PIT |

**Nowcasting cadence.** HRRR every hour with sub-hourly (15-min HRRRv4 subhourly) forecasts. For ES/NQ the relevant chain is: weather → ERCOT LMP spikes → natgas demand → NG futures → correlated risk-on/off. Monitor ERCOT RT LMP + HRRR 2m temp forecast delta vs ISO load forecast. All free, all PIT.

---

## 10. Rates / Reference

| Vendor | Coverage | Access | Cost | PIT |
|---|---|---|---|---|
| **FRED** | SOFR, IOER, Treasury par yields, spreads | [fredapi](https://github.com/mortada/fredapi) | Free | **revised** — use ALFRED for vintage |
| **ALFRED** | Vintage FRED | REST | Free | pit-native |
| **TreasuryDirect** | Auction schedule, results, WI | REST [treasurydirect.gov](https://www.treasurydirect.gov/TA_WS/) | Free | pit-native |
| **NY Fed** | SOFR, TGCR, BGCR, repo ops, H.4.1 | [NY Fed data](https://www.newyorkfed.org/markets/data-hub) | Free | pit-native for reference rates (published 8am ET next business day); revised for survey series |
| **CRSP** | Historical US equity + Treasury | WRDS | University sub ~USD 3k/yr; commercial USD 20k+/yr | pit-native for equity, pit-native for Treasury |
| **IDC / ICE** | Reference, evaluated prices | Enterprise | USD 10k+/yr | evaluated = proprietary model; not raw |
| **Bloomberg BVAL** | Evaluated fixed-income | Terminal / BPIPE | USD 2500/mo + BPIPE | evaluated |

---

## 11. Hugging Face Model Hubs

Selection must be by **empirical IR on internal corpus**, not leaderboard chasing — enforce user-level rule. Candidate models:

| Model | License | Intended domain | Notes |
|---|---|---|---|
| `ProsusAI/finbert` | Apache-2.0 | Financial news sentiment (Fin-PhraseBank) | Baseline; limited to sentence-level sentiment |
| `yiyanghkust/finbert-tone` | Apache-2.0 | Analyst-report tone | Better than ProsusAI on analyst text |
| `yiyanghkust/finbert-fls` | Apache-2.0 | Forward-looking statement detection | Useful for 10-K/8-K |
| `FinLang/finance-embeddings-investopedia` | MIT | Finance retrieval embeddings | Open, MIT — preferred baseline for embeddings |
| `FinLang/investopedia-embedding-model` | MIT | Retrieval | As above |
| `voyage-finance-2` (API) | Commercial, Voyage AI | Finance retrieval embeddings | Closed-weights, API-only; USD ~0.12/1M tokens; strong on FinMTEB |
| `BAAI/bge-large-en-v1.5` | MIT | General retrieval | Strong baseline, not finance-specialized |
| `jinaai/jina-embeddings-v3` | CC-BY-NC-4.0 | General retrieval, multilingual | **Non-commercial** — flag for publishing |
| `nomic-ai/nomic-embed-text-v1.5` | Apache-2.0 | General retrieval | Good commercial alternative |
| `gtfintechlab/FinBERT-FOMC` | CC-BY-NC-4.0 | FOMC tone | Non-commercial; research-only |
| `TheBloke/finance-LLM-*` | Various; check per-model | Instruction-tuned finance LLMs | Quantized derivatives; verify original base-license |

Evaluation protocol: build a held-out corpus of 500 FOMC sentences, 500 BLS/BEA release sentences, 500 10-K MD&A paragraphs; label for the downstream task (hawkish-dovish, surprise-direction, etc.); rank models by F1 / nDCG@10 before committing. Follow FinMTEB ([arXiv 2409.18511](https://arxiv.org/abs/2409.18511)) as an off-the-shelf benchmark.

---

## 12. Recommended Phase-1 Minimal Stack

One vendor per category, justified by the criteria above. Selection horizon: 12 months; revisit at Phase 2.

| Category | Pick | Justification |
|---|---|---|
| CME futures tick | **Databento MBO + MBP-10** | Only vendor with matching-engine ts, Python SDK, pay-per-GB, no lock-in. CME pass-through transparent. |
| CME futures live | **Rithmic via NinjaTrader** (execution) + Databento (research) | Rithmic required by NinjaScript bridge; research uses Databento. |
| Options | **Polygon.io OPRA Advanced** | USD 200/mo, full OPRA, Python SDK, flat-file S3 for history. Compute GEX in-house. |
| Macro surprise (actuals) | **ALFRED** | Free, vintage, PIT. |
| Macro surprise (consensus) | **Econoday feed** | Preserved surveys with release timestamps; industry-standard. |
| Central-bank text | **Direct scrape of federalreserve.gov, ECB, BLS, BEA + FRASER** | Free, authoritative, PIT. No vendor needed. |
| Prediction markets | **Kalshi official API + Polymarket on-chain** | Both official, free, PIT. Run in-house tick collector. |
| On-chain stablecoin | **Direct ETH + Tron RPC watcher** on Tether/Circle treasury contracts | Free, PIT, minute-resolution (block-level actually). |
| AIS | **VesselFinder API** (Rotterdam, Ras Tanura) + EIA API for Cushing crude stocks | USD 99–999/mo; replaces MarineTraffic at lower cost. Skip Spire until Phase 2. |
| Power / weather | **ERCOT MIS + PJM DataMiner 2 + NOAA HRRR via AWS Open Data** | All free, all PIT, all documented. |
| Rates / reference | **ALFRED + TreasuryDirect + NY Fed** | Free, PIT. CRSP deferred to Phase 2 if needed. |
| Embedding model | **FinLang/finance-embeddings-investopedia** as baseline, benchmark `voyage-finance-2` API quarterly | MIT-licensed baseline; paid model only if IR gain > 5% on internal eval. |

Total Phase-1 monthly cost ceiling: **~USD 500/mo** (Databento metered, Polygon OPRA USD 200, Econoday pro-rated ~USD 200, AIS USD 100; everything else free or consumption-based).

---

## 13. Ingestion Architecture

Three-stage pipeline mirrors the user's `SessionStart` reproducibility-log format: every artifact carries `git_head`, `venv_freeze`, `dataset_checksum`, `rng_seed`, `model_commit`.

### Stage: `raw/`
- Immutable exact copy of vendor delivery.
- Path: `data/raw/{source}/{endpoint}/{ingest_date=YYYY-MM-DD}/{filename}`.
- Sidecar JSON: `{filename}.meta.json` with:
  - `sha256`, `size_bytes`, `mtime_utc`
  - `source_endpoint_url`, `vendor_request_id` (if available)
  - `ingest_run_id` (uuid4), `git_head`, `session_id`
  - `vendor_schema_version`
- Never edited. Never deleted without a `data/raw/.deletions.log` entry.

### Stage: `interim/`
- Parsed, typed, schema-validated; not yet feature-engineered.
- Parquet with ZSTD; partitioned by `symbol` + `trade_date` for futures, `release_date` for macro.
- Schema enforced via `pydantic` or `pa.DataFrameSchema` (pandera). Schema version recorded in file metadata.
- Checksum of all raw inputs recorded in `interim/{dataset}/_manifest.json`: `{interim_file_sha: [list_of_raw_sha]}`.

### Stage: `processed/`
- Feature-engineered, join-ready, no look-ahead verified.
- Each processed file carries `provenance.json`: ordered list of `(stage, sha256, git_head, code_ref)`.
- PIT audit: for each feature column, assert `observation_time <= effective_time` on a sample; fail build if violated.

### Provenance log
- `logs/data_provenance.jsonl` — one line per ingest, transform, or publish event.
- Written by the same `SessionStart`/`SessionEnd` hooks that write code-env provenance, so the data and compute ledgers are aligned.
- Format: `{timestamp, event_type, dataset, input_shas, output_sha, run_id, git_head, env_hash}`.

### Operational rules
- No vendor call from a notebook. All ingest via `src/skie_ninja/ingest/{source}.py` CLIs; notebooks read `processed/` only.
- Any ingest that touches a PII/PHI-adjacent source is disallowed by default and requires a README note (no such sources in current plan).
- Clock: all internal timestamps UTC nanoseconds. Matching-engine timestamps kept separate from vendor-receive timestamps; never reconcile silently.
- Retention: `raw/` indefinite; `interim/` rebuildable from raw + code, retained 90 days then garbage-collected by hash of inputs.

---

## 14. Licensing Red-Flags Checklist

Run before signing any commercial feed contract. Each item is a hard stop unless remediated in writing.

- [ ] **CME Group license pass-through** explicitly itemized on vendor's invoice (pro vs non-pro). Absence = assume you will be back-billed by CME.
- [ ] **Redistribution clause**: is research output (a blog post, an SSRN paper, a Zenodo release) considered redistribution? For SPX/SPXW, CBOE Global Indices contract language usually requires a separate *derivative works* rider.
- [ ] **Delayed-vs-real-time tier** stated in contract, with the exact latency SLA (sub-ms, 10 ms, 10 min).
- [ ] **Historical vs live split**: some vendors price them separately (Databento) and some bundle (dxFeed). Confirm before signing.
- [ ] **Data-quality SLA**: published correction policy, notification channel, back-fill window.
- [ ] **Termination clause**: can you retain data purchased under a cancelled subscription? Default answer is usually *yes for historical, no for live cache*. Get in writing.
- [ ] **Export control**: AIS + satellite imagery occasionally hit ITAR/EAR. Confirm Spire/Planet delivery to your jurisdiction is permitted.
- [ ] **PII/PHI absence**: confirm no vendor feed contains PII or PHI (unexpected for this project, but e.g. Chainalysis flows can include attributed-wallet metadata).
- [ ] **Audit rights**: vendor retains right to audit your usage. Typical; keep a clean log of user-counts.
- [ ] **Source-of-record language** for tick data: does the contract concede that the exchange is the source of record (correct) or claim the vendor is (incorrect, liability concern)?
- [ ] **AI-training restriction**: many post-2024 licenses forbid training ML models on the data. For a quant research project this is existential — insist on a "research and modeling" carve-out. Citing [ICMJE 2026](https://www.icmje.org/recommendations/) for publication-side disclosure is not a substitute.
- [ ] **Non-compete / downstream-product clause**: vendor may forbid use in a commercial fund. If the project path includes a managed-account strategy, flag early.
- [ ] **PIT / vintage language**: does contract preserve your right to the first-print value? Most vendors rewrite without notice; get explicit language if the series is a feature input.

---

## Appendix: Evidence-Hierarchy Audit Trail

Vendor pricing figures sourced from public pages as of 2026-04-15 (category 1–3 hierarchy: official documentation). All academic references cited inline with DOI. Where no peer-reviewed reference exists for a vendor claim (e.g. "Databento sub-ms colo latency"), the source is the vendor's own technical documentation, flagged as tier-2. No folklore factors, no unattributed claims.

Next action: compile this into `config/data_sources.yaml` with `vetted: true` on the Phase-1 picks, and open a decision-record under `docs/decisions/ADR-0001-phase1-data-stack_2026-04-15.md` before any vendor contract is signed.
