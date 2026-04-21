# Audit trail — Phase 1 ingest remediation (2026-04-20)

## Context
Project originated on a separate machine. On checkout at `c:\Users\skoir\Documents\SKIE-Universe` the [data/](../../data/) tree held only `.gitkeep` placeholders, `~/datasets/` did not exist, and no environment (`uv`, Python 3.11, `FRED_API_KEY`, `SKIE_SHARED_DATA`) was provisioned. Task: bring Phase 1 ingest pipelines to first successful end-to-end run on this machine.

## Round 1 — host provisioning and first run

**Actions.**
1. Created central shared-data root per [config/shared_data.yaml](../../config/shared_data.yaml): `C:\Users\skoir\datasets\{fred,fomc_text,spf,es_tick,nq_tick}`.
2. Installed `uv 0.11.7` via the Astral standalone installer (`irm https://astral.sh/uv/install.ps1`). User-scope install at `C:\Users\skoir\.local\bin`.
3. `uv python install 3.11` → cpython-3.11.15 under `%APPDATA%\uv\python\`. Project band `>=3.11,<3.13` per [pyproject.toml](../../pyproject.toml) satisfied.
4. `uv venv --python 3.11 .venv` + `uv pip install -e ".[dev]"` completed.
5. Persisted `FRED_API_KEY` and `SKIE_SHARED_DATA=C:\Users\skoir\datasets` via `setx`.
6. [scripts/bootstrap_env.py](../../scripts/bootstrap_env.py) wrote `logs/reproducibility/env_20260420.json`.
7. First FOMC + macro_surprise ingests executed against real network.

**Result.** Raw-fetch phase succeeded for both (164 FOMC HTML docs; 11 ALFRED series JSONs; all SPF files). Post-write validation **failed** on both pipelines.

## Round 2 — first defect class: timezone-aware vs naive datetime

**Finding.** Schema declared `release_ts_utc: pl.Datetime` (naive) but ingest emitted `pl.Datetime("us", "UTC")` (tz-aware). Column name `release_ts_utc` and ingest docstrings both indicate UTC is the intended semantic — schema was the defect.

**Citations.**
- Polars dtype contract: [`pl.Datetime`](https://docs.pola.rs/api/python/stable/reference/api/polars.datatypes.Datetime.html) is `tz=None` by default; tz-aware type is `pl.Datetime(time_zone="UTC")`.
- Pandera-polars enforces exact dtype equality including `time_zone` ([pandera docs](https://pandera.readthedocs.io/en/stable/polars.html#schema-types)).

**Patch.** [src/skie_ninja/data/validation/schema.py](../../src/skie_ninja/data/validation/schema.py) — changed `FomcTextSchema.release_ts_utc`, `FomcTextSchema.embargo_ts_utc`, and `MacroSurpriseSchema.release_ts_utc` from `pl.Datetime` to `pl.Datetime(time_zone="UTC")`. Test fixtures in [tests/unit/test_fomc_text.py](../../tests/unit/test_fomc_text.py) and [tests/unit/test_validation_schema.py](../../tests/unit/test_validation_schema.py) updated to construct tz-aware `datetime(..., tzinfo=UTC)` and declare `pl.Datetime(time_zone="UTC")` in explicit schema overrides.

**Verification.** `uv run pytest tests/unit/` — 196/196 passed. FOMC ingest rerun to completion: 164 processed parquets, post-write schema validation passed, provenance emitted to [data/processed/\_provenance/fomc_text_20260420.json](../../data/processed/_provenance/fomc_text_20260420.json).

## Round 3 — second defect class: (release_date, event_id) non-uniqueness under ALFRED boundary clipping

**Finding.** Macro_surprise validation rejected the parsed frame with `columns '('release_date', 'event_id')' not unique`. First failing sample: 101,945 rows with duplicate `PAYEMS_2016-01-01` pairs.

**Root cause.** ALFRED `output_type=1` returns first-release observations within a `[realtime_start, realtime_end]` window. When an observation's true first-release predates `realtime_start`, ALFRED clips `realtime_start` in the response to the query-window boundary. Multiple pre-2016 observations therefore share `realtime_start=2016-01-01`, producing aliased events under the existing event_id formula `{indicator}_{vintage_date}`. API documented at [FRED Observations endpoint](https://fred.stlouisfed.org/docs/api/fred/series_observations.html).

**Patch (three sub-fixes).**

1. **Dedupe raw actuals by (indicator, release_date)**, keeping the most recently-dated observation (the genuine release; earlier obs_dates at the boundary are backfill artifacts). [src/skie_ninja/data/ingest/macro_surprise.py](../../src/skie_ninja/data/ingest/macro_surprise.py) line ~551.

2. **Output-boundary dedupe** after SPF and forecast-error-std joins. Upstream aggregation in `compute_spf_consensus` and `compute_forecast_error_std` can emit multiple rows per (indicator, obs_date), fanning `result` under the subsequent left-joins. Enforcing uniqueness on (indicator, release_date) at the output boundary with deterministic tiebreak (`keep="first", maintain_order=True`) before the z-score computation.

3. **Explicit Float64 casts for nullable consensus columns** on both parse output and per-row write-back. Polars collapses single-row frames with all-null nullable fields to `dtype=Null` on construction; parquet round-trip preserves this, and pandera rejects it against the declared `pl.Float64` contract. Casts added in `parse` (final `with_columns`) and in `write_processed` (row-level `with_columns` before `write_parquet`).

**Verification.** `uv run pytest tests/unit/` — 196/196 passed. Macro_surprise ingest rerun to completion:

- **1,791** processed parquets under [data/processed/macro_surprise/](../../data/processed/macro_surprise/), partitioned `release_date=YYYY-MM-DD/event_id={indicator}_{YYYY-MM-DD}.parquet`.
- Post-write schema validation passed.
- Provenance emitted to [data/processed/\_provenance/macro_surprise_20260420.json](../../data/processed/_provenance/macro_surprise_20260420.json).
- One fetch-side error logged and tolerated: `EXHOSLUSM495S` returned HTTP 400 from FRED (series was removed or renamed); ingest continued on remaining 11 series. Documented as a separate Phase 1 follow-up item.

## Final inventory (as of 2026-04-20 18:32 ET)

| Layer | Artifact | Count | Location |
|---|---|---|---|
| raw (shared) | FOMC HTML (statement / minutes / press_conference) | 164 | `C:\Users\skoir\datasets\fomc_text\` |
| raw (shared) | ALFRED first-release vintage JSONs | 11 | `C:\Users\skoir\datasets\fred\{CPIAUCSL,GDPC1,PAYEMS,UNRATE,PCEPI,PPIACO,RSAFS,INDPRO,HOUST,ICSA,UMCSENT}\` |
| raw (shared) | SPF quarterly CSVs | as fetched by run | `C:\Users\skoir\datasets\spf\` |
| processed (repo) | FOMC text parquets | 164 | [data/processed/fomc_text/](../../data/processed/fomc_text/) |
| processed (repo) | macro_surprise parquets | 1,791 | [data/processed/macro_surprise/](../../data/processed/macro_surprise/) |
| provenance | fomc_text, macro_surprise | 2 | [data/processed/\_provenance/](../../data/processed/_provenance/) |
| reproducibility logs | env + per-run records | 6 | [logs/reproducibility/](../../logs/reproducibility/) |

## Known follow-ups

1. **`EXHOSLUSM495S`** — FRED 400 on fetch. Likely discontinued/renamed; reconcile [config/macro_indicators.yaml](../../config/macro_indicators.yaml) against current FRED catalog.
2. **ES/NQ tick data** — still gated on Databento account and ADR-0002 bridge decision per README Phase 1 entry.
3. **QQQ 0DTE option chains (H052)** — no ingest path yet; requires vendor decision (CBOE DataShop or Polygon-options).
4. **Sibling repo data sweep** — [Documents\SKIE Enterprises\Futures_ML_Prediction\US100_5min_*.csv](../../../SKIE%20Enterprises/Futures_ML_Prediction/) contains NQ 5-min bars exported from NinjaTrader. Not a reusable ingestion *method* (static NT8 export, no API), but a candidate *input* pending instrument-provenance verification. Documented here rather than copied into the repo.

## Audit-remediate-loop rounds

| Round | Defect | Fix | Test state | Ingest state |
|---|---|---|---|---|
| 1 | env not provisioned | `uv` + Py 3.11 + env vars + shared dir | n/a | raw OK, validate fail |
| 2 | schema tz mismatch | schema+tests tz-aware | 196/196 | FOMC OK, macro fail |
| 3 | non-unique events + Null-dtype round-trip | dedupe + Float64 casts | 196/196 | FOMC + macro OK (1,791 rows — **subsequently identified as dedupe-masked boundary clips**) |
| 4 (audit-remediate) | **wrong FRED `output_type` parameter** and release-vs-observation event conflation — masked by R3 dedupe | `output_type=1` → `output_type=4` (FRED enum: initial release only); event_id keyed to `obs_date` not `vintage_date`; pre-join raw-actuals dedupe removed (no longer needed); output-boundary dedupe re-keyed to `event_id`; integration test updated; two negative schema tests added (naive datetime rejection) | 198/198 | FOMC + macro OK (**1,686 rows of genuine first-release observations; 105-row delta vs round 3 = the boundary-clipped aliases that are no longer returned**) |

3-round cap from [~/.claude/CLAUDE.md](~/.claude/CLAUDE.md) (arXiv:2511.00751 preprint — Loo, "Reevaluating Self-Consistency Scaling in Multi-Agent Systems"; not peer-reviewed) respected; round 4 here is the audit-remediate-loop itself, not a debugging iteration.

## Round-4 findings closed (auditor IDs from [audit-remediate log](#))

- **Literature (L-1, critical) — closed.** FRED `output_type=1` is "Observations by Real-Time Period" (all vintages active in window), NOT "first release only." The initial-release enum value is `output_type=4`. Corrected in [src/skie_ninja/data/ingest/macro_surprise.py](../../src/skie_ninja/data/ingest/macro_surprise.py) lines 10, 55, 107, 121. Sourced directly from [FRED API series/observations docs](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) `output_type` enumeration.
- **Quant (F-1-1, critical) — closed.** The boundary-clipping phenomenon was a symptom of (L-1), not a semantics problem with ALFRED. With the corrected `output_type=4`, each `(indicator, obs_date)` pair appears exactly once at its true first-release `realtime_start`; the three-step dedup from round 3 becomes partially redundant.
- **Quant (F-1-2, critical) — closed.** Event grain is now `(indicator, obs_date)`, set via `event_id = f"{ind['id']}_{obs_date.isoformat()}"`. `release_date` remains `vintage_date` (= first-publication date). For any indicator with a publication lag, the SPF left-join on `(indicator, obs_date) == (fred_indicator, forecast_date)` now keys consistently with ABDV 2003 surprise semantics (the surprise is for the observation, released at the vintage time).
- **Literature (L-2, L-3, L-4, minor) — acknowledged.** Polars dtype URL updated mentally to /dev/; ABDV 2003 DOI added below. Pandera-polars citation cross-referenced to the `pandera.engines.polars_engine.DateTime` reference page.
- **Reproducibility (R-3, major) — open, deferred.** Per-run [ReproLog](../../logs/reproducibility/) has empty `dataset_checksums: {}`. Raw-source SHA256s are captured in the parallel [data/processed/_provenance/](../../data/processed/_provenance/) payload but not cross-linked into the ReproLog. Remediation requires wiring `ctx.add_dataset_checksum(...)` into [scripts/ingest.py](../../scripts/ingest.py) post-fetch. Out of scope for this cycle; opened as a follow-up.
- **Reporting (F-1-6, major) — open, deferred.** `EXHOSLUSM495S` HTTP 400 is still logged-and-continued without a run-level assertion that `len(successful_series) == len(configured_series)`. Follow-up: consult [FRED series EXHOSLUSM495S](https://fred.stlouisfed.org/series/EXHOSLUSM495S) (actually invalid — series ID removed; "EXHOSLUSM495S" likely corruption of `EXHOSLUSM495N` or `EXHOSLMUSM495N`; reconcile [config/macro_indicators.yaml](../../config/macro_indicators.yaml)). Ingest emits a complete record for 11 of 12 series as of this run.
- **Testing (F-1-8, major) — partially closed.** Negative tests added: `test_naive_datetime_rejected` on both `FomcTextSchema` and `MacroSurpriseSchema` in [tests/unit/test_validation_schema.py](../../tests/unit/test_validation_schema.py). Dedup-collapse parse-level test and single-row Null-dtype round-trip test still open — deferred.
- **Minor: stale artifacts on disk.** Switching event_id from `{ind}_{vintage_date}` to `{ind}_{obs_date}` means the pre-remediation parquets (from round-3 run) are not name-compatible with the new ones. Disk state therefore shows ~3,477 files under [data/processed/macro_surprise/](../../data/processed/macro_surprise/) = 1,686 new + 1,791 legacy. The 1,791 legacy files must be cleaned before downstream consumers read this directory; deletion requires explicit user authorization per session policy.

## Primary-source citations (corrected)

- **FRED Observations output_type enum** — https://fred.stlouisfed.org/docs/api/fred/series_observations.html (output_type: 1=all vintages in real-time window, 2=all vintages by vintage date, 3=new+revised by vintage date, **4=initial release only**).
- **FRED real-time period semantics (closed, closed window)** — https://fred.stlouisfed.org/docs/api/fred/realtime_period.html.
- **Polars Datetime dtype** — https://docs.pola.rs/user-guide/transformations/time-series/timezones/ and API ref https://docs.pola.rs/api/python/dev/reference/api/polars.datatypes.Datetime.html (`time_zone=None` default = naive).
- **Pandera polars DateTime** — https://pandera.readthedocs.io/en/latest/polars.html and engine ref https://pandera.readthedocs.io/en/v0.20.3/reference/generated/pandera.engines.polars_engine.DateTime.html (strict `time_zone` equality by default; `time_zone_agnostic=True` opt-out exists).
- **Andersen, Bollerslev, Diebold & Vega (2003).** "Micro Effects of Macro Announcements: Real-Time Price Discovery in Foreign Exchange." *American Economic Review* 93(1):38–62. https://doi.org/10.1257/000282803321455151.
- **Loo (2025 preprint)** — arXiv:2511.00751, "Reevaluating Self-Consistency Scaling in Multi-Agent Systems." *Preprint; not peer-reviewed.*

## Commit hygiene pending
Source tree has uncommitted changes in [src/skie_ninja/data/validation/schema.py](../../src/skie_ninja/data/validation/schema.py), [src/skie_ninja/data/ingest/macro_surprise.py](../../src/skie_ninja/data/ingest/macro_surprise.py), [tests/unit/test_fomc_text.py](../../tests/unit/test_fomc_text.py), [tests/unit/test_validation_schema.py](../../tests/unit/test_validation_schema.py), and new files under [data/processed/](../../data/processed/) and [logs/reproducibility/](../../logs/reproducibility/). Awaiting user authorization per [~/.claude/CLAUDE.md](~/.claude/CLAUDE.md) commit policy.
