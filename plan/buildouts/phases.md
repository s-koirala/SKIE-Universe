# Phased Execution Plan — living document

This plan is deliberately *longitudinal*. Phases are not gates we finish and walk away from; most phases run concurrently once bootstrapped, and the hypothesis backlog is continuously drained.

## Phase 0 — Foundation (weeks 1–2)
- Environment: `uv` venv pinned, ruff/pytest/nbstripout wired.
- SessionStart/SessionEnd reproducibility hooks confirmed writing to [../logs/reproducibility/](../../logs/reproducibility/).
- Instrument specs and roll calendar locked in [../config/instruments.yaml](../../config/instruments.yaml).
- NinjaTrader 8 Desktop: paper-account wired, connection to market-data feed verified, one trivial NinjaScript strategy deployed end-to-end (e.g. "buy 1 MES on 09:30 CT, flat at 15:00 CT") to prove the execution loop.
- Python ↔ NinjaTrader bridge: *one* of {ATI via socket, NTDirect DLL via pythonnet, file-bridge, or MCP server} selected after the execution-research agent report.

## Phase 1 — Data substrate (weeks 2–6, concurrent)
- Ingest ES/NQ tick/MBP-10 for ≥ 5 years historical from chosen vendor.
- Ingest OPRA / CBOE 0DTE option chain for GEX construction.
- Stand up macro-surprise store (actual, consensus, surprise z) back ≥ 10 years.
- Stand up text corpus: FOMC statements/minutes, ECB pressers, BLS releases — with embedding pipeline.
- Kalshi + Polymarket tick archival (forward-only; no deep history exists).
- Altdata pilots for Tier-3 hypotheses (AIS, on-chain, ERCOT).
- Validation: schema + distribution + provenance checks per `validate-data` skill for every ingest.

## Phase 2 — Feature factories (weeks 4–10, concurrent)
One module per feature family under [../src/skie_ninja/features/](../../src/skie_ninja/features/):
- `microstructure/` — OFI, deep OFI, LOB state vectors, Hawkes-clock resampler.
- `macro/` — surprise z-scores, event-window features.
- `text/` — FOMC delta, sentence-level embedding streams, topic drift.
- `altdata/` — GEX, AIS events, on-chain mints, nodal LMP.
- `crossasset/` — Hasbrouck info share, transfer entropy, lead-lag.

Each feature ships with: unit tests, point-in-time correctness test (no look-ahead), provenance log.

## Phase 3 — Model zoo (weeks 6–16, concurrent)
- **Directional** binary and three-class classifiers: logistic-regularized, XGBoost, LightGBM, temporal-fusion transformer, state-space SSM.
- **Volatility**: HAR-RV, GARCH-family, rough-vol (fOU / fBm), neural-SDE.
- **Breakout / size**: survival models, quantile regression, distributional transformers (FutureQuant-style).
- **Regime**: HMM, change-point (BOCPD), rough-Hurst tracker.
- **LLM-native**: prompt-based reasoning over structured feature vectors; evaluate only with DSPy/GEPA-optimized prompts (never hand-tuned).

All trained with purged walk-forward CV + combinatorial purged CV where sample efficiency matters.

## Phase 4 — Inference + multiple-testing (weeks 8–ongoing)
- NW-HAC standard errors with Andrews 1991 bandwidth.
- Sharpe CI via Lo 2002 and Opdyke 2007 in parallel; pick tighter by bootstrap coverage check.
- Ledoit-Wolf 2008 studentized bootstrap for strategy comparisons.
- Hansen SPA (2005) across cumulative strategy universe; White reality check as secondary.
- Every result tagged with the SPA-corrected p-value, not the raw p-value.

## Phase 5 — Backtest engine + cost model (weeks 10–14)
- Walk-forward engine in [../src/skie_ninja/backtest/engine/](../../src/skie_ninja/backtest/engine/).
- Transaction cost model fit empirically from NinjaTrader paper-trade fills (not assumed).
- Slippage distribution per session regime (RTH / ETH / overnight).
- Capacity curve estimated via square-root impact, recalibrated quarterly.

## Phase 6 — Paper trading (weeks 14+, rolling)
- Any strategy passing the Phase-4 bar enters NinjaTrader paper for ≥ 60 session-days.
- Realized vs backtest Sharpe delta monitored daily; delta > CI → halt and post-mortem.

## Phase 7 — Live (gated; no fixed timeline)
- Single-strategy live size capped; ensemble live only after 3 individual strategies have each passed paper.
- Kill-switch wired to drawdown, fill-latency anomaly, and data-feed staleness.

## Phase 8 — Continuous research (permanent)
- Hypothesis backlog drained at ~2 designs/week.
- Quarterly audit-remediate-loop across entire active-strategy portfolio.
- Annual literature-check pass to catch new published angles.

## Phase dependencies (true gates only)

```
P0 → P1
P1 → P2 → P3
P2,P3 → P4 → P5 → P6 → P7
P8 runs permanently from P3 onward
```
