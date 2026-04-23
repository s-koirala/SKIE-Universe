# SKIE-Universe

Longitudinal research program for intraday ES/NQ futures day trading, executed on NinjaTrader 8 Desktop with Python/NinjaScript/MCP automation.

## Prior-art context (SKIE Ninja github projects)
Empirically established in prior SKIE Ninja work:
- Volatility is predictable (walk-forward).
- Breakouts are predictable.
- Movement size is predictable.
- **Direction is 50% AUC via technicals alone.**
- News/geopolitical structured surprises show predictable patterns.

This project does not re-test those facts. It attacks the **directional AUC wall** by stacking directional conditioning variables on top of the already-working size/vol/breakout stack, and by exhaustively evaluating every promising signal in the literature plus the research-frontier whitespace.

## Current status (2026-04-20)

**Phase 0 (Foundation)** — complete. 196 unit tests passing. All P0-1 through P0-12 items delivered and audit-remediated (3-round cap). Two items deferred to user: NT8 F5-compile (P0-9) and ADR-0002 bridge latency measurement (P0-10) — both require NinjaTrader 8 Desktop installation.

**Phase 1 (Data substrate)** — FOMC text + macro_surprise ingest pipelines operational as of 2026-04-20. Final end-to-end run (post audit-remediate) landed 164 FOMC parquets (2015-01-01 → 2026-04-20, statements + minutes + press conferences across 64 meetings) and 1,686 macro_surprise parquets (11 of 12 ALFRED initial-release indicators active + SPF consensus, 2016-01-01 → 2026-04-20). Audit-remediate cycle resolved: schema tz-awareness, wrong FRED `output_type` parameter (1 → 4 per FRED enum), event_id grain (now keyed to `obs_date`, not `vintage_date`), Null-dtype parquet round-trip. Trail: [docs/audits/audit_trail_2026-04-20_phase1-ingest-remediation.md](docs/audits/audit_trail_2026-04-20_phase1-ingest-remediation.md). ES/NQ tick ingest still awaiting Databento account + ADR-0002. `EXHOSLUSM495S` returned HTTP 400 across both `output_type=1` and `output_type=4`; pending FRED catalog reconciliation (series likely renamed/removed).

**Phase 2 (HMM regime + 0DTE track)** — scope extension accepted 2026-04-20 via [ADR-0005](docs/decisions/ADR-0005-hmm-regime-toolkit.md) (HMM toolkit: Baum-Welch + causal Viterbi) and [ADR-0006](docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) (HMM track + sibling 0DTE repo). Three pre-registered hypotheses (H050/H051/H052) live under [research/01_hypothesis_register/](research/01_hypothesis_register/). Sibling repo [`s-koirala/SKIE-NINJA-0DTE`](https://github.com/s-koirala/SKIE-NINJA-0DTE) (SKIE-ORB-CALL, QQQ first-hour long-call scalp) verified live. Audit trail: [docs/audits/audit_trail_2026-04-20_hmm-scope-extension.md](docs/audits/audit_trail_2026-04-20_hmm-scope-extension.md) (3 rounds).

### Phase-0 gate checklist
- P0-1 `reproducibility.py` — done, tested, atomic writes
- P0-2 `paths.py` — done, tested (+ shared data dir at `~/datasets`)
- P0-3 `clock.py` — done, CME half-day calendar validated against `pandas_market_calendars`
- P0-4 `instruments.yaml` + pydantic loader — done, CME fees cited
- P0-5 `hashing.py` — done, cross-process determinism tested
- P0-6 `.pre-commit-config.yaml` + `.gitattributes` — done
- P0-7 `logging_setup.py` — done, JSON structured + rich console
- P0-8 `bootstrap_env.py` — done, Python 3.11+ band enforced
- P0-9 `TrivialSmokeTest.cs` — written, awaiting NT8 install + F5 compile
- P0-10 ADR-0002 bridge selection — `proposed`, awaiting latency measurement
- P0-11 `hypothesis_new.py` + templates — done
- P0-12 `runcontext.py` — done, atomic writes, crash-path flush

### Phase-1 data pipelines
- FOMC text: federalreserve.gov scraper with two-phase commit, DST-aware timestamps, BeautifulSoup parser (statements 1994+, minutes 1993+, press conferences 2011+). **Live on this machine as of 2026-04-20**: 164 parquets under [data/processed/fomc_text/](data/processed/fomc_text/), raw HTML cached at `C:\Users\skoir\datasets\fomc_text\`.
- Macro surprises: ALFRED API initial-release observations (`output_type=4`) + Philadelphia Fed SPF consensus, forecast-error-std proxy per ABDV 2003 (11 active FRED series, 1 pending catalog reconciliation). **Live on this machine as of 2026-04-20**: 1,686 parquets under [data/processed/macro_surprise/](data/processed/macro_surprise/), raw JSON + SPF CSV cached at `C:\Users\skoir\datasets\{fred,spf}\`. Event grain: `(indicator, obs_date)`; `release_date` = ALFRED `realtime_start`.
- ES 5-min engineered features: prototype-tier, imported 2026-04-20 — see [audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md](docs/audits/audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md).
- **ES + NQ 1-min raw OHLCV (Databento GLBX.MDP3, evidence-bar eligible): live on this machine as of 2026-04-23.** 3,733,906 rows partitioned under [data/processed/vendor_legacy_1min/](data/processed/vendor_legacy_1min/) as `symbol={ES,NQ}/year={YYYY}/`. ES spans 2020-01-01 → 2025-12-03 (6 years); NQ spans 2020-01-01 → 2024-12-19 (5 years; 2025 pending sibling pull). Ingest module [src/skie_ninja/data/ingest/vendor_legacy_1min.py](src/skie_ninja/data/ingest/vendor_legacy_1min.py) is SHA256-idempotent, OHLC-consistency validated, and `ctx.add_dataset_checksum`-wired (closes the prior follow-up on empty ReproLog dataset_checksums). Audit trail: [audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md).
- ES tick (sub-minute): Databento recommended (plan §2.1), `EsTickSchema` stub in place; direct SKIE-Universe subscription still awaiting account for tick-level H051 queue-position work.

## Local directory rename (2026-04-20)

- Repo renamed to `SKIE-Universe` on GitHub (remote: `s-koirala/SKIE-Universe`).
- Local directory currently `C:\Users\skoir\SKIE-Ninja-Intraday\`; user will `mv` to `C:\Users\skoir\SKIE-Universe\` out-of-session.
- After rename, recreate venv: `uv venv --python 3.11 .venv && uv pip install -e ".[dev]"` (absolute paths are baked into the old `.venv/`).
- Harness memory dir already mirrored to `c--Users-skoir-SKIE-Universe` so the new session retains prior memory.
- Python package `skie_ninja` is unchanged; imports untouched.

## Layout

| Path | Purpose |
|---|---|
| [config/](config/) | Instrument specs, data sources, model registry, macro indicators |
| [data/](data/) | Raw, interim, processed. `external/` holds alt-data |
| [docs/decisions/](docs/decisions/) | ADR-0001 scope, ADR-0002 bridge, ADR-0003 SPA, ADR-0004 alpha/power, ADR-0005 HMM toolkit, ADR-0006 HMM+0DTE scope |
| [docs/audits/](docs/audits/) | Audit-remediate-loop trails (e.g., HMM scope extension 2026-04-20) |
| [docs/research_notes/](docs/research_notes/) | Dated research memos (e.g., Medallion/HMM lineage 2026-04-20) |
| [docs/templates/](docs/templates/) | Pre-registered hypothesis design, config, data requirements |
| [docs/methodology/](docs/methodology/) | Architecture surveys, data source inventories |
| [research/](research/) | Lit review, hypothesis register, experiments, audits |
| [src/skie_ninja/utils/](src/skie_ninja/utils/) | Clock, hashing, instruments, logging, paths, reproducibility, runcontext |
| [src/skie_ninja/data/](src/skie_ninja/data/) | Ingest registry, FOMC/macro pipelines, validation schemas, provenance |
| [tests/](tests/) | Unit (196 passing), integration (2, network-gated), property-based |
| [scripts/](scripts/) | `ingest.py`, `bootstrap_env.py`, `hypothesis_new.py`, pre-commit hooks |
| [ninjascript/](ninjascript/) | NinjaTrader 8 C# strategies (TrivialSmokeTest) |
| [artifacts/](artifacts/) | Versioned model binaries, reports, universe log |
| [plan/](plan/) | Phased plan, implementation plan, hypothesis backlog |
| [logs/reproducibility/](logs/reproducibility/) | Auto-generated audit trail |

## Environment setup

```bash
# Requires Python 3.11+ and uv
uv venv --python 3.11 .venv
uv pip install -e ".[dev]"
python scripts/bootstrap_env.py
```

Shared data directory: `~/datasets/` (override with `SKIE_SHARED_DATA` env var). See [config/shared_data.yaml](config/shared_data.yaml).

## Key scripts

```bash
# Data ingestion
python scripts/ingest.py --dataset fomc_text --start 2015-01-01 --end 2026-04-16 --dry-run
python scripts/ingest.py --dataset macro_surprise --start 2016-01-01 --end 2026-04-16

# Hypothesis management
python scripts/hypothesis_new.py H027 --title "CBOE COR regime gate" --tier 3 --citations doi:10.xxxx/yyyy

# Validate instruments config
python -m skie_ninja.utils.instruments

# Tests
pytest tests/unit/ -v                              # 196 tests, no network
pytest tests/integration/ -v -m integration        # requires FRED_API_KEY
```

## Entry points
- [plan/phases.md](plan/phases.md) — phased execution plan (8 phases, P0-P8)
- [plan/implementation-plan_2026-04-15.md](plan/implementation-plan_2026-04-15.md) — engineering spec with acceptance criteria
- [plan/hypothesis_backlog.md](plan/hypothesis_backlog.md) — 26 ranked hypotheses across 4 tiers
- [research/00_literature_review/](research/00_literature_review/) — grounded citations
- [research/03_audits/](research/03_audits/) — audit-remediate loop records
- [CLAUDE.md](CLAUDE.md) — project-local rules

## Architecture decisions

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](docs/decisions/ADR-0001-project-scope.md) | Project scope | accepted |
| [ADR-0002](docs/decisions/ADR-0002-bridge-selection.md) | Python-NT8 bridge selection | proposed (user measurement pending) |
| [ADR-0003](docs/decisions/ADR-0003-spa-vs-romanowolf.md) | SPA vs Romano-Wolf for FWER control | proposed |
| [ADR-0004](docs/decisions/ADR-0004-alpha-and-power-defaults.md) | Alpha and power defaults | accepted |
| [ADR-0005](docs/decisions/ADR-0005-hmm-regime-toolkit.md) | HMM canonical regime-inference toolkit (Baum-Welch + causal Viterbi) | proposed |
| [ADR-0006](docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) | Scope extension: HMM track + sibling 0DTE repo | proposed |
