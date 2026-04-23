# SKIE-Universe — Project-Local Rules

Inherits all user-global rules from `~/.claude/CLAUDE.md` plus the imported `rules/quant-project.md` (this cwd matches `**/SKIE-Ninja*/**`).

## Scope
Intraday directional, volatility, breakout, and size trading on CME ES and NQ (and micro equivalents MES/MNQ) futures. Execution target: NinjaTrader 8 Desktop, automated via Python bridge or NinjaScript. ML/LLM inference may connect via MCP or REST.

Parallel tracks authorized by [ADR-0006](docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) (2026-04-20):

- **HMM regime track** — Baum-Welch + causal forward-filter Viterbi ([ADR-0005](docs/decisions/ADR-0005-hmm-regime-toolkit.md)) as regime-conditioning layer on top of existing directional/vol/breakout hypotheses.
- **0DTE options track** — QQQ first-hour long-call scalp via sibling repo [`s-koirala/SKIE-NINJA-0DTE`](https://github.com/s-koirala/SKIE-NINJA-0DTE) (internal code SKIE-ORB-CALL). Equity layer cross-validated on NQ/MNQ futures.

## Standing constraints

- **Universe**: ES, NQ, MES, MNQ front-month contracts. Roll calendar documented in [config/instruments.yaml](config/instruments.yaml). 0DTE track adds QQQ (primary) and QQQ 0DTE/1DTE calls (2022+ daily expirations).
- **Session policy**: RTH and ETH treated as separate regimes. Overnight risk is explicit, not implicit. 0DTE track uses RTH-only (09:30–16:00 ET, `America/New_York`).
- **Capacity ceiling**: retail-size strategies only (<= 20 ES contracts, <= 40 NQ). 0DTE positions sized via delta-equivalent mapping to the NQ ceiling. Capacity-constrained alpha is acceptable.
- **Walk-forward only**. No k-fold. Time-ordered disjoint splits. Purge + embargo per Lopez de Prado. Sibling-repo CPCV + PBO acts as prior screen; our Hansen SPA is additive.

## Research philosophy
This is a *longitudinal, exhaustive* research program — not a single-strategy project. Every hypothesis goes into [research/01_hypothesis_register/](research/01_hypothesis_register/) with a pre-registered design doc. Results enter the hypothesis register whether they succeed or fail; null results are as valuable as positive results and protect against later rediscovery.

## Evidence bar for any signal reaching paper-trade
1. Walk-forward out-of-sample Sharpe CI (Lo 2002 or Opdyke 2007) excludes zero at 95%.
2. Passes Hansen SPA (2005) against the strategy universe accumulated to date.
3. Costs modeled with NinjaTrader-realistic fill assumptions (per-contract commission, exchange fee, slippage distribution fit from paper-trade logs).
4. Reproducibility log present: git HEAD, `uv pip freeze`, dataset checksum, RNG seed, model hash.

## Execution bar for live
Passes paper-trade for at least 60 session-days with realized Sharpe within CI of backtested Sharpe. Kill-switch documented.

## Conventions
- Python env: `uv`. Lint: `ruff`. Notebooks: `nbstripout` + `nbqa ruff`.
- NinjaScript strategies in [ninjascript/strategies/](ninjascript/strategies/), one C# file per strategy.
- Artifacts named `{type}_{description}_{YYYY-MM-DD}.md`.
- Every backtest writes to [logs/reproducibility/](logs/reproducibility/) automatically.

## Implemented infrastructure (as of 2026-04-23)

### Reassessment 2026-04-23
Critical-path + timeline review at [docs/research_notes/memo_phase1-reassessment_2026-04-23.md](docs/research_notes/memo_phase1-reassessment_2026-04-23.md). Raw-tier ES+NQ 1-min substrate now live; [src/skie_ninja/{features,models,inference,backtest,execution}/](src/skie_ninja/) hold only empty folder skeletons — ~3 weeks focused engineering to first walk-forward H050 result; 60-session-day paper-trade is the unmovable calendar floor after that.

## Implemented infrastructure (as of 2026-04-20)

### Phase 1 ingest — live on this machine (2026-04-20)
- Central shared-data root: `C:\Users\skoir\datasets\{fred,fomc_text,spf,es_tick,nq_tick,vendor_skie_ninja_legacy}` (env `SKIE_SHARED_DATA` set).
- FOMC text: 164 processed parquets, 2015-01-01 → 2026-04-20 across 64 meetings.
- Macro surprise: 1,686 processed parquets across 11 ALFRED initial-release series (`output_type=4`) + SPF consensus (`EXHOSLUSM495S` pending FRED catalog reconciliation — HTTP 400 on fetch). Event grain: `(indicator, obs_date)`.
- ES 5-min features (prototype-tier): 269,594-row Databento-derived parquet (2020-01-01 → 2025-12-03) imported from sibling SKIE_Ninja research repo under `vendor_skie_ninja_legacy` namespace. Evidence-bar runs must re-derive features from raw Databento 1-min per [docs/audits/audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md](docs/audits/audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md).
- **ES + NQ 1-min raw (evidence-bar tier)**: 3,733,906 Databento GLBX.MDP3 ohlcv-1m rows (ES 2020-2025 + NQ 2020-2024), scriptable via `python scripts/ingest.py --dataset vendor_legacy_1min`. Raw CSVs land under `~/datasets/vendor_skie_ninja_legacy/raw_1min/`, partitioned parquet under [data/processed/vendor_legacy_1min/](data/processed/vendor_legacy_1min/). License verified 2026-04-23. Audit trail: [docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md).
- Audit-remediate loop (3-round cap) resolved schema tz-awareness, wrong FRED `output_type` parameter, event_id grain conflation, and Null-dtype parquet round-trip: [docs/audits/audit_trail_2026-04-20_phase1-ingest-remediation.md](docs/audits/audit_trail_2026-04-20_phase1-ingest-remediation.md).

## Phase 0 / 1 infrastructure (as of 2026-04-16)

### Phase 0 — utils layer
All modules under [src/skie_ninja/utils/](src/skie_ninja/utils/):
- `paths.py` — `ProjectPaths` resolver; shared data at `~/datasets/` (env `SKIE_SHARED_DATA`)
- `clock.py` — CME session taxonomy (RTH/ETH/OVN/HALT), DST-correct, half-day calendar
- `instruments.py` — pydantic `InstrumentSpec` loader, CLI validator via `python -m`
- `hashing.py` — deterministic `file_sha256`, `frame_sha256` (polars canonical), `model_sha256`
- `reproducibility.py` — `ReproLog` frozen dataclass matching plan section 9.3 schema, atomic writes
- `runcontext.py` — `RunContext` ctx manager: seeds RNG, captures ReproLog, crash-safe flush
- `logging_setup.py` — structured JSON logger with `run_id/phase/hypothesis_id/git_head` context

### Phase 0 — tooling
- `.pre-commit-config.yaml` — ruff, nbstripout, nbqa, check-repro-log, check-instruments-yaml, check-ast-import-guard
- `scripts/bootstrap_env.py` — Python 3.11+ band check, uv presence, env snapshot
- `scripts/hypothesis_new.py` — CLI to scaffold pre-registered hypothesis folders

### Phase 0 — NinjaTrader
- [ninjascript/strategies/TrivialSmokeTest.cs](ninjascript/strategies/TrivialSmokeTest.cs) — buy 1 MES 09:30 CT, flatten 15:00 CT, CSV fill log matching plan section 6.1 schema. Awaiting NT8 install.

### Phase 1 — data ingest
- `src/skie_ninja/data/ingest/_registry.py` — `IngestJob` protocol + `INGEST_REGISTRY`
- `src/skie_ninja/data/ingest/fomc_text.py` — federalreserve.gov scraper, two-phase commit, DST-aware
- `src/skie_ninja/data/ingest/macro_surprise.py` — ALFRED + SPF, surprise z per ABDV 2003
- `src/skie_ninja/data/validation/schema.py` — pandera-polars schemas (FomcText, MacroSurprise, EsTick stub)
- `src/skie_ninja/data/validation/distribution.py` — KS drift with BH FDR correction
- `src/skie_ninja/data/provenance.py` — provenance emission per plan section 2.1
- `scripts/ingest.py` — CLI with `--dry-run`, `--force`, SHA256 idempotency, post-write validation

### Configuration files
- [config/instruments.yaml](config/instruments.yaml) — ES/NQ/MES/MNQ with CME-cited fees + volume tiers
- [config/macro_indicators.yaml](config/macro_indicators.yaml) — 13 FRED series with release times, SPF flags
- [config/shared_data.yaml](config/shared_data.yaml) — shared data directory layout
- [config/data_sources.yaml](config/data_sources.yaml) — vetted sources: ALFRED, SPF, federalreserve.gov

### Architecture decisions
- [ADR-0001](docs/decisions/ADR-0001-project-scope.md) — project scope (accepted)
- [ADR-0002](docs/decisions/ADR-0002-bridge-selection.md) — Python-NT8 bridge (proposed, pending measurement)
- [ADR-0003](docs/decisions/ADR-0003-spa-vs-romanowolf.md) — SPA vs Romano-Wolf (proposed)
- [ADR-0004](docs/decisions/ADR-0004-alpha-and-power-defaults.md) — alpha=0.05, power=0.80 defaults (accepted)
- [ADR-0005](docs/decisions/ADR-0005-hmm-regime-toolkit.md) — HMM (Baum-Welch + causal Viterbi) canonical regime-inference toolkit (proposed, 2026-04-20)
- [ADR-0006](docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) — scope extension: HMM track + 0DTE QQQ sibling repo (proposed, 2026-04-20)

### Phase 2 — HMM regime + 0DTE track (added 2026-04-20)

Three pre-registered hypotheses under [research/01_hypothesis_register/](research/01_hypothesis_register/):

- **H050** — HMM regime-conditioned ES/NQ intraday directional signal (Tier 2b)
- **H051** — HMM-gated Kalman pairs trade on ES/NQ (or MES/MNQ) basis (Tier 2b)
- **H052** — HMM regime-gated QQQ first-hour long-call 0DTE scalp, SKIE-ORB-CALL overlay (Tier 2b)

HMM hyperparameters (n_states, covariance, init, restarts) are BIC/CV-selected inside walk-forward per ADR-0005; emission and transition metadata written to sidecar `logs/reproducibility/{run_id}_hmm_selection.json`, hashed into `ReproLog.model_hash` (no frozen-dataclass change). Audit trail: [docs/audits/audit_trail_2026-04-20_hmm-scope-extension.md](docs/audits/audit_trail_2026-04-20_hmm-scope-extension.md).

### Test coverage
- 196 unit tests passing (9s runtime)
- 2 integration tests (network-gated: FOMC fetch, ALFRED fetch)
- Property tests via Hypothesis: row-permutation hash invariant, clock session labels, DST transitions
