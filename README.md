# SKIE-Universe

Longitudinal, pre-registered intraday futures research program on CME ES/NQ (and micro equivalents MES/MNQ). Hypotheses progress through walk-forward backtest → KPI report card → mandatory NinjaScript C# implementation per [ADR-0013](docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). Primary inferential metrics are survival-constrained (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) per [ADR-0017](docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md); Sharpe-family preserved as secondary KPI.

> **This is a research program, not a deployable library.** No `pip install` path. The repository documents pre-registered hypotheses, audit-remediate-loop trails, and reproducible walk-forward results. External readers: skim §"Research philosophy" → §"Current state" → the linked KPI report cards. Operators / contributors: see [CLAUDE.md](CLAUDE.md) for the full project-rules + phase ledger.

---

## Research philosophy

Per [ADR-0013](docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) (the central governance ADR):

- **Permanent exploration.** Every hypothesis goes into [hypothesis_backlog.md](hypothesis_backlog.md) with a pre-registered design doc. Null and negative results stay in the file — they document the search space we have covered.
- **No gates.** Every former evidence-bar criterion (leakage-canary, BSS, reliability slope, DSR, SPA p) is now a **KPI annotation** in the per-strategy report card. Operator-discretionary review of the KPI report card governs stage transitions.
- **NinjaScript is the terminus.** Every hypothesis MUST progress to a working C# strategy in [ninjascript/strategies/](ninjascript/strategies/), regardless of KPI value. The Python prototype is intermediate; the NinjaScript implementation is the canonical research-loop output.
- **Non-loss mandate.** No audit trail, ReproLog, sidecar, KPI report card, promotion log, NinjaScript strategy, or design.md may be deleted, overwritten, or wiped. Corrections produce versioned successors. Enforced fail-closed by [scripts/_hooks/check_non_loss_deletion.py](scripts/_hooks/check_non_loss_deletion.py).
- **Walk-forward only.** No k-fold. Time-ordered disjoint splits. Purge + embargo per López de Prado 2018 AFML §7.4. CPCV is the canonical splitter for any Sharpe KPI emission.

Per [ADR-0017](docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) (the central inferential ADR, 2026-05-08):

- **Survival metrics are primary.** terminal-wealth-q05 + Calmar-differential + profit-factor + R-multiple-mean are the load-bearing operator-review artifact. Sharpe-family preserved as secondary KPI for academic comparability.
- **Hard kill-switches K-1..K-8** mandatory inheritance from H055 forward (per-trade $-stop, time-stop, no-add-to-loser, position cap, correlated-instrument inventory cap, daily/weekly circuit breakers, adverse-direction entry filter).
- **Drawdown-constrained quarter-Kelly sizing** with current-equity rebasing (MacLean-Thorp-Ziemba 2010).
- **Forward-projection block mandatory** in every KPI report card from 2026-05-03 forward ($10K-baseline 252-session bootstrap; per ADR-0013 §3.1).

---

## Current state (2026-05-11)

| Hypothesis | Stage | Headline result |
|---|---|---|
| [**H050**](research/01_hypothesis_register/H050/) HMM regime-conditioned ES/NQ directional | `kpi-report-emitted` ([v1](research/01_hypothesis_register/H050/H050_kpi_report_v1.md)) | Catastrophic. Gated arms ES −81%, NQ −84% realized; T_H050 CIs exclude zero on the **negative** side. HMM-gating actively harms the directional signal. |
| [H051](research/01_hypothesis_register/H051/) HMM-gated Kalman pairs ES/NQ basis | `designed` | Not yet executed. |
| [**H052a**](research/01_hypothesis_register/H052a/) HMM regime-gated first-hour ORB | `kpi-report-emitted` (operator-declined-ninjascript) | Non-significant null on hypothesis-of-record. Strongest cell is **NQ unconditional ORB** (+10.61% realized) — literature-replication artifact. |
| [H052b](research/01_hypothesis_register/H052b/) QQQ 0DTE long-call scalp | `designed` | Vendor-gated on QQQ 0DTE option chain. |
| [**H053**](research/01_hypothesis_register/H053/) Multi-TF mediation + categorical archetype table | `kpi-report-emitted` ([v3](research/01_hypothesis_register/H053/H053_kpi_report_v3.md)) | CI-marginal across 4 arms; **NQ LightGBM +10.8%** realized 2-yr OOS, max-DD 3.7%, forward median $10,713 / P(loss)=15%. |
| [**H054**](research/01_hypothesis_register/H054/) Anti-gate first-hour ORB on ES | `kpi-report-emitted` ([v1](research/01_hypothesis_register/H054/H054_kpi_report_v1.md)) | Point-positive (+3.50% realized anti-gated, P(loss)=29.2%) but CIs cover zero. Structurally low-power (anti-gate fires 7/237 sessions). |
| [**H055**](research/01_hypothesis_register/H055/) Mechanized wick-rejection scalping (HMM-deferred v3) | `exploration-in-progress` | Pre-launch; 7+ BLOCKING preconditions outstanding. |
| H056–H059 | `queued` | Per the [H055 successor tree](plan/buildouts/h055_successor_tree_2026-05-06.md): per-component ML → stacking master → multi-TF attention → live probability display layer. |

For the full per-hypothesis stage dashboard see [research/01_hypothesis_register/INDEX.md](research/01_hypothesis_register/INDEX.md). For emitted KPI report cards with mandatory 9-table results summaries see [RESULTS_INDEX.md](research/01_hypothesis_register/RESULTS_INDEX.md).

**Project-wide observation through 2026-05-11**: across H050 + H052a + H053 + H054 the Sharpe-family inferential anchor consistently clustered around zero while realized $10K trajectories diverged materially. This empirical pattern motivated [ADR-0017](docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md), which demoted Sharpe to a secondary KPI from H055 forward.

---

## Reproducibility contract

Every walk-forward run emits a [ReproLog](src/skie_ninja/utils/reproducibility.py) sidecar at `logs/reproducibility/{run_id}.json` with 13 frozen-dataclass fields: `git_head`, `pip_freeze`, `dataset_checksums`, `rng_seed`, `model_hash`, `timestamp_utc`, `env_id`, plus per-fold artifact SHAs. Substrate parquet partitions are SHA256-bound at `designed` status in each hypothesis's `data_requirements.md`. Per [ADR-0009](docs/decisions/ADR-0009-blas-thread-pinning.md), BLAS thread pinning is required for byte-deterministic HMM fits across runs.

Canonical wall-clock for a clean production walk-forward at the current substrate (ES + NQ × 2015-2025, ~7.4M 1-min bars): **~7h50min** on a single 24-thread workstation (H050 run_id `31d23ec...`). Mid-run external kills (Windows Update, OS reboot, supervisor cap) are protected against by the three-layer defense in [ADR-0010](docs/decisions/ADR-0010-multi-hour-run-process-protection.md) + the preflight checklist in [ADR-0011](docs/decisions/ADR-0011-production-walkforward-runbook.md).

Canonical launch path (Windows):

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  uv run python scripts/supervised_run.py \
  --hypothesis H050 --config config/hypotheses/H050.yaml
```

Sister scripts: `scripts/run_h052a_walk_forward.py`, `scripts/run_h054_walk_forward.py`, `scripts/run_h053_stage{0,1,2,3}_*.py`. Forward-projection: `scripts/simulate_h053_v4_10k_2026.py`, `scripts/simulate_h050_v1_10k_2026.py`.

---

## Repository layout

| Path | Purpose |
|---|---|
| [**hypothesis_backlog.md**](hypothesis_backlog.md) | Project-canonical hypothesis register — at-a-glance status table + tier-organized backlog |
| [**CHANGELOG.md**](CHANGELOG.md) | Condensed phase-by-phase summary (one line per phase). Full ledger in CLAUDE.md. |
| [**CLAUDE.md**](CLAUDE.md) | Full project-rules + audit-remediate-loop ledger (~140 KB; load-bearing internal doc) |
| [docs/glossary.md](docs/glossary.md) | Stage labels, KPI annotation grammar, statistical primitives, reproducibility terms |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records (17 ADRs); see [decisions/README.md](docs/decisions/README.md) |
| [docs/audits/](docs/audits/) | Audit-remediate-loop trails (append-only; protected) |
| [docs/research_notes/](docs/research_notes/) | Dated research memos (postmortems, reassessments, retrospectives) |
| [research/01_hypothesis_register/](research/01_hypothesis_register/) | Per-hypothesis design.md + stage.md + KPI report cards + failure_log.md; see [INDEX.md](research/01_hypothesis_register/INDEX.md) |
| [research/00_literature_review/](research/00_literature_review/) | Grounded primary-literature citations |
| [research/03_audits/](research/03_audits/) | Pre-Phase-0 audit-remediate records (immutable) |
| [src/skie_ninja/](src/skie_ninja/) | Python package: data ingest, features, models (HMM), backtest engine, inference primitives, NinjaTrader bridge |
| [tests/](tests/) | Unit + integration + property-based tests (>1,000 unit tests as of 2026-05-09) |
| [scripts/](scripts/) | Walk-forward orchestrators (one per hypothesis), simulators, ingest CLI, preflight |
| [ninjascript/](ninjascript/) | NinjaTrader 8 C# strategies (terminal state of every hypothesis per ADR-0013 §5) |
| [config/](config/) | Instrument specs, hypothesis configs, data sources, gate thresholds |
| [data/](data/) | Raw + interim + processed substrate; `external/` for ledgers and reference datasets |
| [logs/reproducibility/](logs/reproducibility/) | Auto-generated ReproLog sidecars (one per run) |
| [logs/promotions/](logs/promotions/) | Operator promotion / decline / retirement decision logs |
| [plan/](plan/) | Operational planning — buildouts, roadmaps, engineering specs; see [plan/README.md](plan/README.md) |
| [artifacts/](artifacts/) | Versioned model binaries + reports + universe log |
| [runs/](runs/) | Per-run sidecars + per-fold metrics |
| [reports/](reports/) | Per-hypothesis stage dispositions (Markdown narrative) |

---

## Environment setup

```bash
# Requires Python 3.11+ and uv
uv venv --python 3.11 .venv
uv pip install -e ".[dev]"
python scripts/bootstrap_env.py
```

Shared data directory: `~/datasets/` (override with `SKIE_SHARED_DATA` env var). See [config/shared_data.yaml](config/shared_data.yaml).

The HMM forward-backward kernels under [src/skie_ninja/models/regime/_em_kernels.py](src/skie_ninja/models/regime/_em_kernels.py) are accelerated with Numba `@njit`. As of `P1-HMM-EM-NUMBA-KERNELS`, numba is included in the `[dev]` extra so the standard install above exercises the JIT path during testing. Reproducing production HMM fits to byte identity requires the same `(numba, llvmlite, host CPU feature set)` tuple as the producing run; cross-host fits agree only to `rtol = 1e-12`.

Per [ADR-0009](docs/decisions/ADR-0009-blas-thread-pinning.md), BLAS thread counts must be pinned to 1 for any KMeans-bearing code path (unit suite, walk-forward orchestrator, anything that constructs `GaussianHMM`). Set the BLAS env vars before importing numpy / sklearn (variables read at process start):

```bash
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
```

---

## Sibling repositories

Per [ADR-0006](docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) + [ADR-0016](docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md):

- **[SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE)** (internal: SKIE-ORB-CALL) — QQQ first-hour long-call 0DTE scalp; cross-track sibling for H052b.
- **[SKIE-NINJA-Volatility](https://github.com/s-koirala/SKIE-NINJA-Volatility)** — first audit-and-lift target per ADR-0016 (BLOCKING-BEFORE-H056-LIFT-OPTION-3-2).
- **[SKIE-Ninja](https://github.com/s-koirala/SKIE-Ninja)** — legacy precursor (~500+ feature ML system); future audit per ADR-0016.
- **[SKIENINJA-V3](https://github.com/s-koirala/SKIENINJA-V3)** — BTC-focused; out-of-universe per ADR-0001; cited for scope-boundary clarity.

Sibling-repo artifacts cannot be promoted into SKIE-Universe successors without passing the [ADR-0016](docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md) 7-gate audit (substrate-compatibility, PIT correctness via Cycle-4 leak canaries, purged/embargoed walk-forward verification, multi-testing correction, BSS + reliability slope, ReproLog schema compatibility, license + commit-SHA provenance).

---

## Key entry points

- [hypothesis_backlog.md](hypothesis_backlog.md) — what we are researching and current status
- [research/01_hypothesis_register/INDEX.md](research/01_hypothesis_register/INDEX.md) — per-hypothesis stage dashboard
- [research/01_hypothesis_register/RESULTS_INDEX.md](research/01_hypothesis_register/RESULTS_INDEX.md) — KPI report cards across all hypotheses
- [docs/decisions/README.md](docs/decisions/README.md) — ADR index
- [docs/glossary.md](docs/glossary.md) — terms and conventions
- [CHANGELOG.md](CHANGELOG.md) — condensed phase log
- [CLAUDE.md](CLAUDE.md) — full project rules + audit-remediate-loop ledger

## License

See [LICENSE](LICENSE) (when present). Source code is project-internal research; do not deploy against live capital without operator authorization. Strategies promoted to `live-promoted` are tracked at [logs/promotions/](logs/promotions/).
