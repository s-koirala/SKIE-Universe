---
name: Implementation Plan 2026-04-15
description: Engineering-grade extension of plan/phases.md with Phase-0 punch list, contracts, gates, risks, 12-week critical path
type: project
status: accepted
date: 2026-04-15
---

# Implementation Plan — 2026-04-15 (extends [phases.md](phases.md))

## 1. Phase 0 Punch List (weeks 1–2, strict ordering)

Each item is a module or file with acceptance criteria enforceable by `pytest`.

### P0-1. [src/skie_ninja/utils/reproducibility.py](../../src/skie_ninja/utils/reproducibility.py)
- **Contents**: `@dataclass(frozen=True) class ReproLog` with fields `git_head: str`, `pip_freeze: str`, `dataset_checksums: dict[str, str]`, `rng_seed: int`, `model_hash: str | None`, `timestamp_utc: str`, `env_id: str`. Helpers: `capture() -> ReproLog`, `write(path: Path) -> Path` (JSON, sorted keys), `verify(path) -> bool`.
- **Acceptance**: `tests/unit/test_reproducibility.py` asserts (a) all six required fields populate, (b) `write→read` round-trips byte-identically, (c) `capture()` is pure — two successive calls differ only in `timestamp_utc`, (d) Windows path serialization uses POSIX style.

### P0-2. [src/skie_ninja/utils/paths.py](../../src/skie_ninja/utils/paths.py)
- Central `ProjectPaths` resolver (no hard-coded absolutes). Drives `data/raw`, `data/interim`, `data/processed`, `artifacts/models`, `artifacts/reports`, `logs/reproducibility`.
- **Acceptance**: test that every downstream module imports paths only through this resolver (grep-guard test).

### P0-3. [src/skie_ninja/utils/clock.py](../../src/skie_ninja/utils/clock.py)
- Exchange-aware clock: `to_exchange(ts)`, `session_of(ts) -> Literal["RTH","ETH","OVN","HALT"]`, `trading_day(ts)`. Uses CME calendar; RTH = 08:30–15:15 CT for ES/NQ.
- **Acceptance**: property tests over DST transitions, half-days (Thanksgiving, Christmas Eve), roll days; never returns "RTH" outside 08:30–15:15 CT.

### P0-4. [config/instruments.yaml](../../config/instruments.yaml) population
- Fields per contract: `root`, `exchange`, `tick_size`, `tick_value`, `multiplier`, `session_rth`, `session_eth`, `roll_rule` (`volume_crossover` with window), `commission_per_side_usd`, `exchange_fee_usd`, `nfa_fee_usd`, `micro_ratio`.
- **Acceptance**: `tests/unit/test_instruments.py` validates via pydantic `InstrumentSpec` model; loader rejects missing fields; round-trip fixture for ES, NQ, MES, MNQ.

### P0-5. [src/skie_ninja/utils/hashing.py](../../src/skie_ninja/utils/hashing.py)
- Deterministic `file_sha256`, `frame_sha256(df, sort_cols)` for pandas/polars, `model_sha256(state_dict | sklearn_estimator)`.
- **Acceptance**: property test — any row permutation of a stable-sorted frame yields the same hash; any value mutation changes it.

### P0-6. `.pre-commit-config.yaml` + `.gitattributes`
- Hooks: `ruff`, `ruff-format`, `nbstripout`, `nbqa-ruff`, custom `check-repro-log` hook that fails if a notebook under `notebooks/reproducible/` lacks a `ReproLog` cell output.
- **Acceptance**: `pre-commit run --all-files` green on a clean tree; a deliberate nb with no ReproLog fails.

### P0-7. [src/skie_ninja/utils/logging_setup.py](../../src/skie_ninja/utils/logging_setup.py)
- Structured JSON logger (stdlib `logging` + `rich` pretty console in dev). Required context keys: `run_id`, `phase`, `hypothesis_id`, `git_head`.
- **Acceptance**: test that every log line is valid JSON and contains those keys.

### P0-8. [scripts/bootstrap_env.py](../../scripts/bootstrap_env.py) (read-only check)
- Verifies Python 3.11/3.12, `uv` present, writes a one-time `logs/reproducibility/env_{YYYYMMDD}.json`.
- **Acceptance**: non-zero exit if `python --version` outside band.

### P0-9. [ninjascript/strategies/TrivialSmokeTest.cs](../../ninjascript/strategies/TrivialSmokeTest.cs)
- Buys 1 MES at 09:30 CT, flattens at 15:00 CT. Logs fills to CSV for cost-model ingestion.
- **Acceptance**: runs against paper account for 3 sessions with zero errors; CSV validated by P1-3.

### P0-10. [docs/decisions/ADR-0002-bridge-selection.md](../../docs/decisions/ADR-0002-bridge-selection.md)
- Output of the execution-research agent. Selects exactly one of {ATI-socket, NTDirect-pythonnet, file-bridge, MCP-server}. Records measured one-way latency p50/p99 per option over **≥10k test messages per option** (1k is insufficient for stable p99 — standard error on an empirical p99 with n=1000 is ≈√(0.01·0.99/1000)/f(q) and dominates the quantile at heavy-tailed latencies).
- **Acceptance**: decision is `accepted`; latency table present; losing options explicitly rejected with reason.

### P0-11. [scripts/hypothesis_new.py](../../scripts/hypothesis_new.py) (see §10)

### P0-12. [src/skie_ninja/utils/runcontext.py](../../src/skie_ninja/utils/runcontext.py)
- `RunContext` context manager that opens a run, captures `ReproLog`, sets RNG seeds (numpy, torch, python), registers cleanup, writes `logs/reproducibility/{run_id}.json`.
- **Acceptance**: any `pytest` test using the `run_context` fixture produces exactly one repro-log file; crash path still flushes.

**Phase-0 gate**: all 12 items green in CI; `ninjascript/strategies/TrivialSmokeTest.cs` executed 3 live paper sessions; ADR-0002 accepted.

---

## 2. Minimum-Viable Data Spine

Least work to get ES tick + macro surprise + FOMC text to `data/processed/` with validation and provenance.

### 2.1 Modules

- `src/skie_ninja/data/ingest/es_tick.py` — vendor-agnostic loader (Databento/CQG/Rithmic adapter). Parquet partitioned by `trading_day`; schema: `ts_event_ns, ts_recv_ns, price, size, side, aggressor, sequence, symbol, contract_month`.
- `src/skie_ninja/data/ingest/macro_surprise.py` — BLS/BEA/ISM/Fed releases with `actual`, `consensus_median`, `std_consensus`, `surprise_z = (actual - median) / std`. Source: Haver/Bloomberg/Econoday snapshot CSV.
- `src/skie_ninja/data/ingest/fomc_text.py` — statements + minutes (HTML → normalized text); fields: `release_ts_utc, embargo_ts_utc, doc_type, sha256, raw_path, text_normalized`.
- `src/skie_ninja/data/ingest/_registry.py` — `IngestJob` protocol: `fetch`, `parse`, `validate`, `write_processed`, `emit_provenance`.
- `src/skie_ninja/data/validation/schema.py` — pydantic + pandera schemas. Enforces monotonic `ts_event_ns`, `price > 0`, `size > 0`, zero duplicate `(ts, sequence)`.
- `src/skie_ninja/data/validation/distribution.py` — per-day KS stability check vs trailing 30-day reference; alert if p<1e-6.
- `src/skie_ninja/data/provenance.py` — emits `data/processed/_provenance/{dataset}_{YYYYMMDD}.json` with vendor, snapshot_ts, source_urls, sha256 of raws, `ReproLog`.

### 2.2 Layout

```
data/processed/
  es_tick/dt=YYYY-MM-DD/part-0000.parquet
  macro_surprise/release_date=YYYY-MM-DD/event_id=*.parquet
  fomc_text/release_date=YYYY-MM-DD/doc_type=*.parquet
  _provenance/
```

### 2.3 Entry point

`scripts/ingest.py --dataset {es_tick|macro_surprise|fomc_text} --start YYYY-MM-DD --end YYYY-MM-DD --dry-run`. Idempotent; re-run overwrites only if source sha256 changed.

### 2.4 Validation skill wiring

Every ingest run invokes the `validate-data` skill against the processed output; failure aborts the write via two-phase commit (write to `_staging/`, rename only on pass).

**Acceptance**: 1 year of ES tick, 10 years of macro surprises, all FOMC statements 2015→present land in `data/processed/` with valid provenance. `tests/integration/test_data_spine.py` exercises one day of each end-to-end with a vendored fixture.

---

## 3. Feature Factory Contract

Single abstract interface under `src/skie_ninja/features/base.py`:

```python
class FeatureModule(Protocol):
    name: str                    # "ofi_deep_l10"
    version: str                 # semver; any logic change bumps it
    lookback: pd.Timedelta       # max history needed at inference time
    inputs: tuple[DatasetRef, ...]
    output_schema: pa.Schema     # pyarrow schema

    def compute(
        self,
        panel: pl.LazyFrame,      # point-in-time panel, ts <= now
        now: pd.Timestamp,
        ctx: RunContext,
    ) -> pl.LazyFrame: ...

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None: ...
```

### Contractual guarantees (enforced by shared test base class)

1. **Point-in-time**: for any `now`, `compute(panel, now) == compute(panel.filter(ts<=now), now)`. Property test via Hypothesis with 100 random `now` per feature.
2. **Determinism**: same inputs → same bytes; hashed via `frame_sha256`.
3. **No silent NaN**: all outputs declare nullability in `output_schema`; unexpected NaNs fail.
4. **Provenance emission**: every `compute` writes `logs/reproducibility/features/{name}_{version}_{run_id}.json`.
5. **Latency budget**: `compute` over 1-day slice under module-declared `latency_budget_ms`.
6. **Output schema stability**: any column change bumps `version`; CI rejects PR that changes columns without version bump.

Every subdir (`microstructure/`, `macro/`, `text/`, `altdata/`, `crossasset/`) has `__init__.py` registering modules in `FEATURE_REGISTRY` so the walk-forward runner can enumerate.

---

## 4. Model Training Harness

### 4.1 Splitter spec — `src/skie_ninja/backtest/splits.py`

- `PurgedWalkForwardSplitter(train_window, test_window, step, embargo, purge)` — Lopez de Prado (AFML 2018) §7.
  - `embargo`: **data-driven**, no magic default. Fit on the PACF of residualized (model-de-meaned) returns over the train window; select the smallest lag `L` at which PACF falls within the white-noise band `±1.96/√n`. Cross-check against the Politis-White 2004 stationary-bootstrap optimal block length ([Politis-White 2004](https://doi.org/10.1081/ETC-120028836)); take `embargo = max(L_PACF, L_PW)`. The selection and both candidate values are logged to `ReproLog`.
  - `purge`: lower bound `purge >= max_label_horizon` (strict inequality permitted when overlapping meta-labels push effective horizon beyond the nominal label horizon). The exact value is chosen from label-overlap diagnostics and logged.
- `CombinatorialPurgedCV(n_groups, n_test_groups, embargo)` — AFML §12; used only when sample count < 20k bars. `n_groups`, `n_test_groups`, and `embargo` are all parameterized and logged (no hard-coded defaults); selection rationale (per AFML §12 and sample size) recorded in `ReproLog`.
- `TripleBarrierLabeler` — AFML §3.2; optional, for classification targets.
- All splitters yield `Split(train_idx, test_idx, train_range, test_range, purge_range, embargo_range)` and reject leakage (asserted test).

### 4.2 Entry point — `scripts/run_walk_forward.py`

```
run_walk_forward.py \
  --hypothesis-id H001 \
  --config research/01_hypothesis_register/H001/config.yaml \
  --splitter {walkforward,cpcv} \
  --features ofi_deep_l10,gex_0dte,fomc_delta \
  --model xgb_directional \
  --label triple_barrier \
  --cost-model nt_paper_v1 \
  --seed 20260415 \
  --dry-run
```

Writes to `artifacts/runs/{hypothesis_id}/{YYYY-MM-DDTHH-MM-SSZ}_{run_id}/`.

### 4.3 Artifact layout per run

```
artifacts/runs/H001/2026-05-01T14-03-07Z_a1b2c3/
  config_resolved.yaml
  reprolog.json
  splits.parquet
  folds/
    fold=00/
      train_pred.parquet
      test_pred.parquet
      model.joblib (or .pt)
      model.sha256
      metrics.json
      features_used.json
  aggregate/
    oos_returns.parquet
    metrics_summary.json
    inference_gate.json
  report.md
```

### 4.4 Acceptance

- Running twice with same seed produces byte-identical `model.sha256` for all folds.
- Deliberate leak injection (shuffled label) fails purged CV — canary test in `tests/integration/test_leak_canary.py`.

### 4.5 Leaked-feature canary

In addition to the shuffled-label canary in §4.4, `tests/integration/test_leaked_feature_canary.py` injects a feature whose value at time `t` is a deterministic function of returns in the half-open interval `(t, t + H]` (future-return leaked feature). The test asserts that both:
1. The `PurgedWalkForwardSplitter` + pipeline detect the leak via the PIT property test (feature fails `validate_point_in_time`).
2. If the PIT guard is bypassed, gate §5 reports implausibly deflated p-values AND the pipeline-level leakage test (see §4.6) halts the run.

### 4.6 Pipeline-level leakage test

`tests/integration/test_pipeline_leakage.py` injects a synthetic feature whose mean depends on future data (e.g., leaked via scaler/encoder fit on the full panel rather than per-fold train slice). Test asserts the composed splitter + feature pipeline + model raises `LeakageDetected` before any fit call succeeds. This closes the hole where §3 guarantees PIT at `compute` but normalization/encoding steps may still fit on the full panel.

---

## 5. Inference Gate — `src/skie_ninja/inference/gate.py`

Single mandatory chokepoint. Nothing writes to `artifacts/reports/` without passing through this.

```python
@dataclass(frozen=True)
class GateReport:
    mean_return: float
    nw_hac_se: float             # Andrews 1991 bandwidth
    nw_hac_lag: int
    sharpe: float
    # Sharpe CIs — Opdyke 2007 is primary; Lo 2002 is diagnostic-only
    sharpe_ci_opdyke2007: tuple[float, float]              # PRIMARY
    sharpe_ci_studentized_circular_block: tuple[float, float]  # TIE-BREAKER
    sharpe_ci_lo2002: tuple[float, float]                  # DIAGNOSTIC ONLY
    sharpe_ci_bootstrap: tuple[float, float]
    chosen_ci: tuple[float, float]                         # defaults to Opdyke 2007
    # Family-wise / step-down multiple-testing controls
    hansen_spa_pvalue: float
    white_rc_pvalue: float
    romano_wolf_pvalue: float                              # stepwise, primary per ADR-0003 if chosen
    ledoit_wolf_pvalue: float | None
    # False-discovery-rate controls across the universe
    bh_qvalue: float                                       # Benjamini-Hochberg 1995
    storey_qvalue: float                                   # Storey 2002 under dependence
    # Post-selection deflation
    deflated_sharpe_ratio: float                           # Bailey-Lopez de Prado 2014 (required)
    psr_pvalue: float                                      # Probabilistic Sharpe Ratio p-value
    # Power analysis (see §5.1)
    power_at_s_min: float                                  # power to detect Sharpe>=S_min at alpha=0.05
    n_required_for_power_80: int                           # AR(1)- and kurtosis-adjusted
    # Universe reference
    universe_snapshot_id: str
    universe_snapshot_size: int
    # Gate outcome — see passed-logic block below
    passed: bool

def evaluate(
    oos_returns: pd.Series,
    strategy_universe: StrategyUniverse,
    benchmark: pd.Series | None = None,
    alpha: float = 0.05,
    bootstrap_reps: int = 10_000,  # MC SE for p at 0.05: sqrt(0.05*0.95/B) ≈ 0.0022 at B=10k
    block_len: int | None = None,  # default: Politis-White 2004 optimal
) -> GateReport: ...
```

### `passed` logic (replaces previous "CI excludes 0 AND SPA p<0.05")

A `GateReport` is `passed = True` iff all of:
1. `chosen_ci` (Opdyke 2007 primary) excludes 0.
2. `hansen_spa_pvalue < alpha` OR `romano_wolf_pvalue < alpha`. Which of the two is primary is resolved by [ADR-0003](../../docs/decisions/ADR-0003-spa-vs-romanowolf.md).
3. `bh_qvalue < bh_threshold` evaluated at the current `universe_snapshot_size`. `bh_threshold` lives in [config/gate.yaml](../../config/gate.yaml); initial value 0.10 tracks the [Benjamini-Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) conventional FDR level but is tagged `# justify:` and is subject to Phase-1 empirical calibration (follow-up F-3-1).
4. When `universe_snapshot_size > dsr_activation_size`: `deflated_sharpe_ratio > 0` and `psr_pvalue < alpha` are required; otherwise DSR/PSR are reported but not gating. `dsr_activation_size` lives in [config/gate.yaml](../../config/gate.yaml); initial placeholder 10 is driven by DSR stability at small N and is subject to Phase-1 simulation calibration (follow-up F-3-1).
5. Pre-registered power calc (§5.1) satisfied: `power_at_s_min >= 0.80` and sample meets `n_required_for_power_80`.

### Harvey-Liu-Zhu haircut reporting

Final Sharpe reported in `artifacts/reports/` must additionally apply the [Harvey-Liu-Zhu 2016 RFS](https://doi.org/10.1093/rfs/hhv059) haircut framework (Bonferroni, Holm, BHY haircut variants) alongside the raw and deflated values. The haircut table is required for every promotion decision.

### 5.1 Pre-registration power calc

Every hypothesis `config.yaml` under `research/01_hypothesis_register/{Hnnn}/` must include a `power` block:

```yaml
power:
  s_min: 1.0                 # minimum-detectable annualized Sharpe
  alpha: 0.05
  target_power: 0.80
  ar1_rho: [0.05, 0.15]      # realistic intraday ES range
  excess_kurtosis: ...       # estimated from pilot data
  variance_formula: lo2002_hac_adjusted   # Sharpe asymptotic variance per Lo 2002, HAC-adjusted
  n_required: ...            # derived, not hand-set
```

Variance of the sample Sharpe uses the [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453) asymptotic formula adjusted for autocorrelation via HAC per [Newey-West 1994](https://doi.org/10.2307/2297912). The iid-inflation factor `(1 + 2ρ/(1-ρ))` is applied and logged. `src/skie_ninja/inference/power.py::required_n(s_min, alpha, power, rho, kurt)` computes `n_required`. The gate refuses any hypothesis whose realized OOS sample is below `n_required_for_power_80` (underpowered designs cannot pass).

### Method anchors (DOIs)

- NW-HAC: [Newey-West 1994](https://doi.org/10.2307/2297912) ; [Andrews 1991](https://doi.org/10.2307/2938229)
- Sharpe CI (diagnostic, iid assumption): [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453)
- Sharpe CI higher-moment (primary): [Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084)
- Pairwise bootstrap: [Ledoit-Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002)
- Hansen SPA: [Hansen 2005](https://doi.org/10.1198/073500105000000063)
- White RC: [White 2000](https://doi.org/10.1111/1468-0262.00152)
- Romano-Wolf stepwise FWER: [Romano-Wolf 2005, Econometrica](https://doi.org/10.1111/j.1468-0262.2005.00615.x)
- BH FDR: [Benjamini-Hochberg 1995 JRSS-B](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
- Storey q-value under dependence: [Storey 2002](https://doi.org/10.1111/1467-9868.00346)
- Deflated Sharpe / PSR: [Bailey-Lopez de Prado 2014 JPM](https://doi.org/10.3905/jpm.2014.40.5.094)
- Haircut Sharpe: [Harvey-Liu-Zhu 2016 RFS](https://doi.org/10.1093/rfs/hhv059)
- Stationary bootstrap block: [Politis-White 2004](https://doi.org/10.1081/ETC-120028836)

### Primary Sharpe CI justification (Opdyke 2007 > Lo 2002)

Lo 2002 assumes stationary, approximately iid returns with finite fourth moment. Intraday ES shows first-order autocorrelation `ρ₁ ∈ [-0.08, -0.03]` (bid-ask-bounce) and excess kurtosis well above Gaussian. Opdyke 2007 explicitly handles skew/kurtosis; the studentized circular-block bootstrap serves as the tie-breaker when Opdyke and Lo disagree by more than the bootstrap MC SE. Lo 2002 is retained in `GateReport` as a diagnostic (disagreement flags model-mis-specification) but never drives `passed`.

### Universe snapshot

`StrategyUniverse` is an append-only log at `artifacts/universe/universe_log.parquet`. Every gate evaluation *hashes the full universe to date* into `universe_snapshot_id` so SPA is reproducible.

### Acceptance

- Synthetic null (iid N(0,1)): SPA p-value distribution uniform on [0,1] within KS tolerance at n=1000.
- Synthetic alternative Sharpe=1.5: Lo and Opdyke CIs cover true value at nominal 95% within MC error.
- Data-snooping canary: try 500 random signals, keep best — raw Sharpe CI excludes zero, SPA p > 0.05.

---

## 6. Backtest Cost-Model Calibration

### 6.1 Data source

NinjaTrader paper-trade fill exports → `data/raw/nt_fills/` (CSV). Schema: `order_id, submit_ts, fill_ts, symbol, side, qty, limit_px, fill_px, order_type, session, mid_at_submit, book_depth_at_submit`.

### 6.2 Module — `src/skie_ninja/backtest/costs/slippage.py`

- `ingest_nt_fills(path) -> pl.DataFrame`
- `decompose_slippage(df)` → `impact_ticks = (fill_px - mid_at_submit) * side_sign / tick_size`, `latency_ms = fill_ts - submit_ts`
- `fit_slippage_model(df, regime_col="session") -> SlippageModel` fitting per-regime (RTH/ETH/OVN):
  - **Primary mean (retail-size correct)**: `a + b * spread_ticks + c * latency_ms + d * vol_realized_1m` (linear-in-spread with latency conditioning). At our capacity ceiling (≤20 ES vs ES ADV ≈ 1.5M → `qty/ADV ≈ 1.3e-5`), the √(qty/ADV) term of Almgren-Chriss / [Tóth et al. 2011](https://arxiv.org/abs/1104.1694) is numerically indistinguishable from zero and unidentifiable from the intercept — misspecification at retail size.
  - **√ prior retained as regularized Bayesian mean only**: a weakly-informative N(0, σ²_prior) prior on the √(qty/ADV) coefficient `b_sqrt` (posterior mean shrinks to zero at retail sizes but allows the model to extend to any larger-capacity variant without refactor). σ²_prior is selected via cross-validated marginal likelihood, not hand-set.
  - Dispersion: skew-t MLE on residuals.
- `SlippageModel.sample(qty, regime, vol, spread, latency) -> float_ticks` for MC backtests.

### 6.3 Validation

- **Expanding-window walk-forward** (not 60/40 single split): chronologically sort paper fills; starting from a minimum-train window `W_0` (data-driven via learning-curve inspection, logged), refit at each calendar week, evaluate pinball loss on the next-week holdout. Aggregate pinball and calibration (PIT) across folds. Matches the project's "walk-forward only; no k-fold" rule from [quant-project.md](../../../.claude/rules/quant-project.md).
- Recalibration: quarterly OR on KS drift p < 0.001 (KS threshold tracked as open item in "Open items for Phase 1"). Triggers `audit-loop`.

### 6.4 Commission and fees

Static per `config/instruments.yaml`. Always applied; slippage model applied on top.

### 6.5 Acceptance

- `tests/integration/test_slippage_fit.py` fits on vendored 2-week sample; regime-wise calibration MAE < 0.5 ticks.

---

## 7. Execution Adapter Interface

`src/skie_ninja/execution/router.py`:

```python
class OrderRouter(Protocol):
    def submit_market(self, symbol: str, qty: int, side: Side, tag: str) -> OrderAck: ...
    def submit_limit(self, symbol: str, qty: int, side: Side, limit_px: Decimal,
                     tif: Tif, tag: str) -> OrderAck: ...
    def flatten_all(self, reason: str) -> list[OrderAck]: ...
    def position_snapshot(self) -> PositionBook: ...
    def subscribe_fills(self, handler: Callable[[Fill], None]) -> SubscriptionHandle: ...
    def health(self) -> HealthReport: ...
```

Implementations:

- `src/skie_ninja/execution/dryrun.py::DryRunRouter` — paper-mode default. Simulates fills via `SlippageModel`; writes `artifacts/dryrun/{session}.parquet`.
- `src/skie_ninja/execution/nt_adapter.py::NinjaTraderRouter` — binds to ADR-0002 bridge (hybrid Python↔NinjaScript TCP per agent recommendation).
- `src/skie_ninja/execution/mcp_adapter.py::MCPRouter` — MCP research/read-only interface only; does NOT place live orders (see ADR-0002).

All routers wrapped by `GuardedRouter(inner, kill_switches=[...])` — the only class strategies may import. Enforced by `tests/unit/test_router_import_guard.py` AST check.

### Acceptance

- `DryRunRouter` reproducibility: same seed, same `SlippageModel`, same orders → byte-identical fills file.
- `GuardedRouter` raises `KillSwitchEngaged` on synthetic tripwire tests from §8.

---

## 8. Risk Kill-Switches

All in `src/skie_ninja/execution/killswitch.py`, composed into `GuardedRouter`:

| Switch | Trigger | Source data | Action |
|---|---|---|---|
| `DailyLossSwitch` | realized+open PnL ≤ -$X or -Y% NAV | `PositionBook` + MTM stream | `flatten_all("daily_loss")` + disarm rest of day |
| `MaxPositionSwitch` | net \|qty\| > per-symbol cap (20 ES, 40 NQ per CLAUDE.md) | `PositionBook` | reject new; allow reducing |
| `DataStalenessSwitch` | no tick > `staleness_ms` (2000 RTH, 10000 ETH) | heartbeat | `flatten_all("stale_data")` |
| `LatencyAnomalySwitch` | submit→ack p99 over rolling 100 > 5× baseline | OrderAck timestamps | pause, alert |
| `ConnectionSwitch` | bridge healthcheck fails 3× in 15s | `router.health()` | `flatten_all("bridge_down")` |

Tests:
- `tests/unit/test_killswitch_*.py` — per switch with synthetic event streams.
- `tests/integration/test_guardedrouter_trips.py` — each scenario vs `DryRunRouter`.
- Property test: no valid event sequence can produce position beyond cap.

Config in `config/risk.yaml`; values versioned and logged in `ReproLog`.

---

## 9. CI and Reproducibility Gates

### 9.1 Pre-commit

- `ruff` + `ruff-format`
- `nbstripout` (except `notebooks/reproducible/` where `check-repro-log` *requires* a `ReproLog` output cell)
- `nbqa-ruff`
- `check-instruments-yaml` (pydantic)
- `check-repro-log` (new `scripts/run_*` must open `RunContext`)
- `check-ast-import-guard` (strategies import `GuardedRouter`, not raw routers)

### 9.2 GitHub Actions (`.github/workflows/ci.yml`)

- `lint`: ruff, pre-commit all-files.
- `test-unit`: `pytest -m "not integration" -n auto`.
- `test-integration` (fixture-only): `pytest -m integration`.
- `test-property` (Hypothesis).
- `repro-verify`: runs `scripts/verify_repro.py`, re-executes most recent `artifacts/runs/` with recorded seed, asserts byte-equal `model.sha256`.
- `gate-snapshot` on merge to `main`: commit `universe_snapshot_id` bump when strategy added.

### 9.3 Reproducibility log schema

```json
{
  "run_id": "ulid",
  "phase": "phase_3|...",
  "hypothesis_id": "H001",
  "timestamp_utc": "...",
  "git_head": "...",
  "pip_freeze_sha256": "...",
  "pip_freeze_path": "logs/reproducibility/env/{sha}.txt",
  "dataset_checksums": {"es_tick": "...", "macro_surprise": "..."},
  "rng_seed": 20260415,
  "model_hash": "...",
  "config_resolved_sha256": "...",
  "host": {"os": "...", "python": "...", "cpu": "..."},
  "env_id": "uv-lock-sha"
}
```

---

## 10. Hypothesis-Register Automation

### `scripts/hypothesis_new.py`

```
python scripts/hypothesis_new.py H027 \
  --title "CBOE COR regime gate" \
  --tier 3 \
  --citations doi:10.xxxx/yyyy
```

Creates:
```
research/01_hypothesis_register/H027/
  design.md                  # from docs/templates/hypothesis_design.md
  config.yaml                # skeleton for run_walk_forward.py
  data_requirements.md
  README.md
```
Also appends entry to `hypothesis_backlog.md` (repo root) with `queued` status.

Template `docs/templates/hypothesis_design.md` sections (pre-registered):
1. Hypothesis (H0, H1, mechanism, citations)
2. Universe & sample period (bounded, no discretion later)
3. Features (exact registry names + versions)
4. Label construction
5. Estimator (exact class + hyperparam search grid — fixed at pre-reg)
6. Splitter (walk-forward vs CPCV)
7. Cost model ID
8. Gate thresholds (§5)
9. Stopping rule (n folds, time budget)
10. Decision rule
11. Reproducibility commitments

Acceptance: `tests/unit/test_hypothesis_new.py` creates H999 in tmp dir; asserts files present; backlog line idempotent.

---

## 11. Ranked Risks & Mitigations

| # | Risk | Severity | Likelihood | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | **Multiple-testing false discovery across exhaustive backlog** | Critical | Near-certain at n>50 | Hansen SPA gate §5 mandatory; `universe_snapshot_id` forces full history; SPA p-value reported, not raw | Lead researcher |
| R2 | Bridge-choice lock-in wrong (NT↔Python) | High | Medium | ADR-0002 latency-measured; `OrderRouter` abstraction keeps choice swappable; `DryRunRouter` bridge-independent | Execution owner |
| R3 | Look-ahead leakage in features | High | High without guard | PIT property tests §3; leak-canary §4.4 with shuffled label | Feature owner |
| R4 | Cost model optimistic (backtest Sharpe >> paper Sharpe) | High | High | §6 empirical fit from NT paper logs; Phase-6 halts on delta > CI | Backtest owner |
| R5 | Data vendor schema drift / silent reshape | Med-high | Medium | `validate-data` skill every ingest; KS distribution guard; two-phase commit | Data owner |
| R6 | NinjaTrader API instability / disconnect | High | Medium | `ConnectionSwitch` + `DataStalenessSwitch` §8; auto-flatten; forced-drop integration tests | Execution owner |
| R7 | Reproducibility rot (env drift) | Medium | High | `uv.lock` pinned; `repro-verify` CI §9.2; quarterly reproducibility-verifier agent | Platform owner |
| R8 | Text-corpus licensing risk (FOMC OK, Bloomberg not) | Medium | Medium | Store only derived features + URLs + sha256; no raw redistribution; per-source license in provenance | Data owner |
| R9 | Regime change post-training | Medium | Certain eventually | Rough-Hurst / BOCPD regime detector (H020) wired into sizing; halt if realized Sharpe outside 95% CI for 20 sessions | Research lead |
| R10 | Capacity creep past retail ceiling | Medium | Low-medium | Hard cap in `MaxPositionSwitch`; capacity curve recalibrated quarterly | Risk owner |
| R11 | LLM-native signals (H021) nondeterministic | Medium | High | DSPy/GEPA-optimized prompts only; temperature=0; prompt + model id hashed in `ReproLog` | LLM lead |
| R12 | Backlog drain too slow (dilution vs novelty) | Low-medium | Medium | `hypothesis_new.py` automation; 2-designs/week SLA in `artifacts/reports/cadence.md` | PM |

---

## 12. Critical Path — First 12 Weeks

★ = hard gate; `||` = concurrent.

| Week | Primary track | Concurrent | Hard gate |
|---|---|---|---|
| 1 | P0-1…P0-5 (utils, paths, clock, instruments, hashing) | — | |
| 2 | P0-6…P0-9 (pre-commit, logging, env, trivial NT strategy) || ADR-0002 latency study | ★ **G0**: Phase-0 done; trivial NT strategy ran 3 paper sessions; ADR-0002 accepted |
| 3 | ES tick ingest (1-yr backfill) || macro-surprise ingest | Splitter §4.1 drafted | |
| 4 | FOMC text ingest + embedding || 10-yr macro backfill | Gate §5 skeleton + synthetic null | ★ **G1**: `data/processed/{es_tick, macro_surprise, fomc_text}` validated |
| 5 | Feature contract §3 + PIT property base || 0DTE option chain ingest | Slippage ingest from NT logs | |
| 6 | Three features: `microstructure/ofi`, `macro/surprise_z`, `text/fomc_delta` | Walk-forward runner §4.2 | ★ **G2**: one Tier-1 feature per family green on PIT + determinism |
| 7 | Model zoo bootstrap: XGBoost directional + HAR-RV vol | CPCV + leak canary | |
| 8 | Gate fully wired (Lo, Opdyke, bootstrap, SPA) | First E2E H002 walk-forward | ★ **G3**: gate returns `GateReport` on H002; leak canary passes |
| 9 | Cost model fit on 30+ NT paper sessions | Exec adapter §7 with `DryRunRouter` | |
| 10 | Kill-switches §8 all five + tests | `NinjaTraderRouter` stub per ADR-0002 | ★ **G4**: kill-switch suite green |
| 11 | Walk-forward H001 (GEX) + H010 (deep OFI) through gate | Hypothesis automation live; ≥5 `designed` | |
| 12 | Strategy registry + `universe_snapshot_id`; first audit-loop on H001/H002/H010; paper-trade promotion decisions | `GuardedRouter` hardening | ★ **G5**: ≥1 strategy satisfies `GateReport.passed` per §5 clauses 1–5 → cleared for Phase-6 paper |

Gate failure at any ★ blocks next phase; remediation via `audit-remediate-loop` (3-round cap).

---

## Open items for Phase 1

Tracked but not implemented in the Phase-0/Phase-1 scope of this plan. Each is a MEDIUM finding from [audit-round1-quant_2026-04-15.md](../../research/03_audits/audit-round1-quant_2026-04-15.md) and is recorded here as a commitment, not a specification.

| # | Item | Audit ref | Target |
|---|---|---|---|
| O-10 | Extend `GateReport` with MaxDD CI (Burghardt-Duncan-Liu 2003), Ulcer Index, turnover SE, Calmar. PSR already added. | M-10 | Phase 1 |
| O-11 | Empirical justification for each magic number: 20 ES / 40 NQ caps (capacity study), 5× latency-anomaly threshold (bootstrap CI on baseline p99), 2000 ms RTH staleness (quantile of observed inter-tick gaps), KS `p<1e-6` (FDR-adjusted), 3× bridge-fail (reliability study), quarterly recalibration (drift-detection power curve). | M-11 | Phase 1 |
| O-12 | `bootstrap_reps` selection: cite MC SE target `SE ≈ √(p(1-p)/B)`; select B to hit target SE ≤ 10% of alpha. | M-12 | Phase 1 |
| O-13 | Parameterize CPCV `n_groups`, `n_test_groups` per hypothesis; log selection rationale per AFML §12. (Partially covered in §4.1 edit; full rationale capture deferred.) | M-13 | Phase 1 |
| O-14 | Triple-barrier `pt_sl` multipliers, vertical barrier duration, and volatility estimator choice pre-registered per hypothesis `config.yaml`. | M-14 | Phase 1 |
| O-15 | Document CME volume-tier fee schedule in [config/instruments.yaml](../../config/instruments.yaml) even if immaterial at retail. | M-15 | Phase 1 |
| O-16 | Add MBP-10 / depth schema to §2.1 ingest (blocker for H010 deep-OFI). | M-16 | Phase 1 |

## Reference anchors

- Lopez de Prado, *Advances in Financial Machine Learning* (2018) — purged CV, CPCV, triple-barrier.
- [Newey-West 1994](https://doi.org/10.2307/2297912) ; [Andrews 1991](https://doi.org/10.2307/2938229)
- [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453) — Sharpe CI (diagnostic)
- [Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084) — Sharpe CI (primary)
- [Ledoit-Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002)
- [White 2000](https://doi.org/10.1111/1468-0262.00152)
- [Hansen 2005](https://doi.org/10.1198/073500105000000063)
- [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) — stepwise FWER
- [Benjamini-Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) — FDR
- [Storey 2002](https://doi.org/10.1111/1467-9868.00346) — q-value under dependence
- [Bailey-Lopez de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094) — Deflated Sharpe / PSR
- [Harvey-Liu-Zhu 2016](https://doi.org/10.1093/rfs/hhv059) — Sharpe haircut
- [Politis-White 2004](https://doi.org/10.1081/ETC-120028836)
- [Tóth et al. 2011](https://arxiv.org/abs/1104.1694) — square-root impact (context; misspecified at retail size)
- [ADR-0003](../../docs/decisions/ADR-0003-spa-vs-romanowolf.md) — SPA vs Romano-Wolf selection (proposed)
