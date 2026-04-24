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
Critical-path + timeline review at [docs/research_notes/memo_phase1-reassessment_2026-04-23.md](docs/research_notes/memo_phase1-reassessment_2026-04-23.md). Raw-tier ES+NQ 1-min substrate live; 60-session-day paper-trade is the unmovable calendar floor after MVP-1.

### Tier-2b buildout (started 2026-04-23)
Six-cycle audit-remediate critical path to MVP-1 documented in [plan/tier2b_buildout_2026-04-23.md](plan/tier2b_buildout_2026-04-23.md).

- **Cycle 1 ✓ done (2026-04-23)** — Roll-adjusted continuous-contract derivative. Module: [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) v0.2.0. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle1-roll-adjusted-1min.md](docs/audits/audit_trail_2026-04-23_cycle1-roll-adjusted-1min.md). Follow-ups: `P1-LEVEL-USE-POLICY` (load-bearing) + 5 others.
- **Cycle 2 ✓ done (2026-04-23)** — NW-HAC + Sharpe-CI primitives at [src/skie_ninja/inference/stats/](src/skie_ninja/inference/stats/): Newey-West 1987 Bartlett estimator + Andrews 1991/NW 1994 bandwidths; Lo 2002 iid/η(q)/HAC-approx + Opdyke 2007 Mertens-HAC (primary). 273/273 unit tests green. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle2-hac-sharpe-ci.md](docs/audits/audit_trail_2026-04-23_cycle2-hac-sharpe-ci.md). Follow-up `P1-OPDYKE-FULL-GMM` tracks full moment-vector GMM implementation.
- **Cycle 3 ✓ done (2026-04-23)** — HMM regime-inference toolkit per [ADR-0005](docs/decisions/ADR-0005-hmm-regime-toolkit.md). Package [src/skie_ninja/models/regime/](src/skie_ninja/models/regime/): log-space Baum-Welch EM (`_core.py`), `GaussianHMM` with k-means++ warm start + label-switch canonicalisation and **causal `filter_states` as sole public inference path** (`hmm.py`), BIC grid selection (`selection.py`), `HMMSidecar` (`hmm_sidecar_v1`) with SHA256 → `ReproLog.model_hash` via `with_model_hash` (`serialization.py`). 47 new unit tests; 320/320 green. Anti-look-ahead prefix-causality gate covered. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle3-hmm-toolkit.md](docs/audits/audit_trail_2026-04-23_cycle3-hmm-toolkit.md). Round-1 remediated: Biernacki 2003 mislabel → operational floor; EM off-by-one, scale-adaptive `min_var`, conditional PD ridge (tied/full), dead-state / PD-ridge event recording, Rabiner eq. numbers → §-level. Round-2 verification deferred to Cycle 6 end-to-end. Follow-ups: `P1-HMM-ADAPTIVE-RESTART`, `P1-HMM-WFCV`, `P1-HMM-SIDECAR-DIAGNOSTICS`, `P1-HMM-VERIFIED-EQ-NUMBERS`.
- **Cycle 4 ✓ done (2026-04-23)** — Walk-forward engine + purged/embargo CV + leak canaries. Package [src/skie_ninja/backtest/](src/skie_ninja/backtest/): `walk_forward_split` (rolling/expanding per Bergmeir-Benítez 2012, Tashman 2000), `purged_kfold_split` + `cpcv_split` (AFML §7.4 / Ch.12; mlfinlab-compatible stacked embargo), `WalkForwardEngine` with Int64-schema-validated parquet ledger + SHA256 roll-up → `ReproLog.model_hash` via `with_model_hash`, three leak canaries (fold-boundary invariant with monotonicity gate, label-horizon purge check, dual fit-call observer + `TracingArray` capability proxy). 79 new unit tests; 399/399 green. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md](docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md). Round-1 parallel triad (quant+lit+repro) remediated 4 quant majors (canary c dead-observer, embargo placement, canary a monotonicity, walk-forward embargo over-accumulation), 3 lit majors (Bergmeir overreach, CPCV Ch.12 not §7.5, Cawley §7 → Varma & Simon 2006), 1 repro major (ledger dtype validation). Round-2 remediated 2 new majors (embargo stacked vs overlap → mlfinlab-stacked; TracingArray public-field bypass → `_array` + `__slots__`); repro accepted clean. Follow-ups: `P1-BACKTEST-CPCV` (full path reconstruction), `P1-BACKTEST-EMBARGO-MODE-ADR`, `P1-BACKTEST-TRACINGARRAY-STRICT`.
- **Cycle 5 ✓ done (2026-04-23)** — Hansen 2005 SPA test + Politis-Romano 1994 stationary bootstrap with Politis-White 2004 (+ PPW 2009 correction) automatic block-length selection. Modules: [src/skie_ninja/inference/bootstrap.py](src/skie_ninja/inference/bootstrap.py) (`politis_white_block_length`, `choose_block_length`, `stationary_bootstrap_indices`, `stationary_bootstrap`) + [src/skie_ninja/inference/multipletest/hansen_spa.py](src/skie_ninja/inference/multipletest/hansen_spa.py) (`hansen_spa_test` with three Hansen 2005 §2.4 recentering variants SPA_l/SPA_c/SPA_u; bootstrap + HAC omega paths; shared bootstrap indices across strategies for cross-dependence preservation per Hansen §2). 54 new unit tests; 453/453 green. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle5-hansen-spa-bootstrap.md](docs/audits/audit_trail_2026-04-23_cycle5-hansen-spa-bootstrap.md). Round-1 parallel triad (quant+lit) remediated 1 critical (Politis-Romano 1995 flat-top kernel → *JTSA* 16(1):67-103, was mis-cited as *JASA*), 3 majors (PPW 2009 revised both SB+CB constants; threshold rule `c·sqrt(log10(n)/n)` attribution → PW 2004 §3.1 + Politis 2003; primary-source verification-gap explicitly documented), and 1 promoted-minor (ε-floor scale unified on variance scale across HAC and bootstrap omega branches). Round-2 verification deferred to Cycle 6 end-to-end. Follow-ups: `P1-SPA-PDF-VERIFY`, `P1-SPA-ARCH-BENCHMARK`, `P1-SPA-HAC-DEFAULT-ADR`.
- **Cycle 6 partial — Phase-A only complete (2026-04-24); live WF blocked.** H050 feature factory + walk-forward orchestrator scaffolding committed: Yang-Zhang vol + triple-barrier labels (`TripleBarrierLabeler`); 4 microstructure features (Parkinson RV, realized variance, realized skew, OFI tick-rule proxy; all PIT-safe, deterministic, no-silent-NaN); NT8 ES/NQ RTH cost model (`NT8EsNqRthV1CostModel`); Phase-A orchestrator [scripts/run_walk_forward.py](scripts/run_walk_forward.py) composing cycles 1–5; `data_requirements.md` frozen checksums; `H050.yaml` config; ADR-0007 (stacked embargo) + ADR-0008 (SPA omega). 54 Cycle-6 unit tests green; full-suite total 517 per pause memo (not corroborated in audit trail — follow-up `P1-AUDIT-TRAIL-FULL-SUITE-COUNT`). Audit trail: [docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md](docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md). Pause memo: [docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](docs/research_notes/memo_cycle6-pause-status_2026-04-24.md). A Round-1 audit-remediate-loop on 2026-04-24 (parallel quant-auditor + literature-check + reproducibility-verifier; not separately committed) confirmed all 5 in-memo blockers and surfaced 3 additional pre-reg deviations + 2 reproducibility gaps. **10 items blocking evidence-bar execution**:
  - `P1-HMM-FOLD-WARM-START` *(major)* — `filter_states` restarts from `log_pi` each fold; warm-up bias O(dwell_time). [scripts/run_walk_forward.py:334](scripts/run_walk_forward.py); [src/skie_ninja/models/regime/_core.py:296-297](src/skie_ninja/models/regime/_core.py).
  - `P1-H050-SPLIT-PARAMS` *(**critical**, pre-reg violation)* — `initial_train = max(200, n//3); test_size = max(50, n//10)`; pre-reg [config/hypotheses/H050.yaml](config/hypotheses/H050.yaml) lines 6-8 binds train 2015-01-01→2022-12-31 / val 2023 / test 2024-2025. [scripts/run_walk_forward.py:543-554](scripts/run_walk_forward.py).
  - `P1-H050-INNER-CV` *(major)* — `score = model.score(X_tr, y_tr)` (in-sample); pre-reg [research/01_hypothesis_register/H050/design.md](research/01_hypothesis_register/H050/design.md) §5 mandates nested walk-forward CV per Varma & Simon 2006, *BMC Bioinformatics* 7:91 (doi:[10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91)). N_draws collapsed from pre-reg 200 → 10. [scripts/run_walk_forward.py:259-287](scripts/run_walk_forward.py).
  - `P1-H050-CI-DIFFERENTIAL` *(**critical**, pre-reg violation)* — `ci = opdyke2007_ci(gated)` applies CI to `sharpe_gated` alone; pre-reg design.md §1 binds `T_H050 = SR_{filtered, gated} − SR_{filtered, unconditional}`; [rules/quant-project.md](../../.claude/rules/quant-project.md) mandates Ledoit & Wolf 2008, *J. Empirical Finance* 15(5):850-859 (doi:[10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002)) for pairwise. [scripts/run_walk_forward.py:358](scripts/run_walk_forward.py).
  - `P1-H050-DATA-COVERAGE` *(**critical**, pre-reg violation; user decision pending)* — substrate ES 2020-2025 + NQ 2020-2024; pre-reg design.md §2 demands 2015-01-01 → 2025-12-31; ≈60% of train window missing (2015-2019 both symbols + 2025 NQ). Three pre-registered design-change paths anchored in design.md §2 line 41 ("re-runs on extended windows require a successor hypothesis ID") + §10 (archive `precondition-failed`): **B1** backfill from Databento GLBX.MDP3, **B2** register H050b with truncated windows, **B3** archive H050 as `precondition-failed`.
  - `P1-H050-LABEL-CV` *(promoted to blocking)* — pt_sl × vertical_barrier × volatility_lookback grid collapsed to center; pre-reg design.md §4 mandates CV. [scripts/run_walk_forward.py:488-497](scripts/run_walk_forward.py).
  - `P1-H050-UNIVERSE-ES-ONLY` *(minor pre-reg deviation)* — NQ silently dropped from smoke; [config/hypotheses/H050.yaml](config/hypotheses/H050.yaml) line 3 universe `[ES, NQ]`. [scripts/run_walk_forward.py:511-512](scripts/run_walk_forward.py).
  - `P1-H050-SPA-M1-DEGENERATE` *(minor)* — Hansen SPA |M|=1 single-column semantics; rules/quant-project.md intends multi-strategy SPA; document via ADR-0008 extension. [scripts/run_walk_forward.py:362-372](scripts/run_walk_forward.py).
  - `P1-CYCLE6-REPRO-DATASET-CHECKSUM` *(repro)* — all 5 Cycle-6 walk_forward repro logs carry `dataset_checksums={}`; `06f0402` fix wired `output_frame_sha256` into `RunContext` but no run has been executed post-fix.
  - `P1-HMM-BLAS-THREADING-ADR` *(repro)* — `sklearn.KMeans` deadlock under default Windows MKL/OpenMP; `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` workaround documented only in pause memo, not in repo README/ADR. Pause memo §Issue 3 originally classified this "non-blocking, workaround known"; promoted to blocking here because [~/.claude/CLAUDE.md](~/.claude/CLAUDE.md) reproducibility schema requires single-command reproduction without out-of-tree env-var setup.

  Other (non-blocking) follow-ups: `P1-H050-FEATURE-PIT-ASSERT`, `P1-H050-COST-EMPIRICAL-CALIBRATION`.

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

Four pre-registered hypotheses under [research/01_hypothesis_register/](research/01_hypothesis_register/):

- **H050** — HMM regime-conditioned ES/NQ intraday directional signal (Tier 2b)
- **H051** — HMM-gated Kalman pairs trade on ES/NQ (or MES/MNQ) basis (Tier 2b)
- **H052a** — HMM regime-gated first-hour ORB on CME futures ES/NQ/MNQ/MES (Tier 2b; added 2026-04-23 as futures-variant sibling of H052b — HMM-gate is sole new content atop a prior-art-null underlying)
- **H052b** — HMM regime-gated QQQ first-hour long-call 0DTE scalp, SKIE-ORB-CALL overlay (Tier 2b; renamed from H052 on 2026-04-23)

HMM hyperparameters (n_states, covariance, init, restarts) are BIC/CV-selected inside walk-forward per ADR-0005; emission and transition metadata written to sidecar `logs/reproducibility/{run_id}_hmm_selection.json`, hashed into `ReproLog.model_hash` (no frozen-dataclass change). Audit trail: [docs/audits/audit_trail_2026-04-20_hmm-scope-extension.md](docs/audits/audit_trail_2026-04-20_hmm-scope-extension.md).

### Test coverage
- 196 unit tests passing (9s runtime)
- 2 integration tests (network-gated: FOMC fetch, ALFRED fetch)
- Property tests via Hypothesis: row-permutation hash invariant, clock session labels, DST transitions
