# SKIE-Universe

Longitudinal, pre-registered futures research program on CME instruments (ES, NQ, MES, MNQ; metals MGC, SIL; energy via H061 substrate-extension track). Hypotheses progress through walk-forward backtest → KPI report card → mandatory NinjaScript C# implementation per [ADR-0013](docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). Primary inferential fitness is **MPPM(ρ=1)** ([Goetzmann-Ingersoll-Spiegel-Welch 2007 *RFS*](https://doi.org/10.1093/rfs/hhm025)) per [ADR-0018](docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) + [ADR-0024](docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md); Sharpe-family + ADR-0017 survival vector preserved as KPI tier for academic comparability.

> **This is a research program, not a deployable library.** No `pip install` path. The repository documents pre-registered hypotheses, audit-remediate-loop trails, and reproducible walk-forward results. External readers: skim §"Research philosophy" → §"Best out-of-sample results" → the linked KPI report cards. Operators / contributors: see [CLAUDE.md](CLAUDE.md) for the full project-rules + phase ledger.

---

## Best out-of-sample results

The strongest realized-OOS performer across all emitted KPI report cards is auto-tracked in [**BEST_OOS.md**](BEST_OOS.md), regenerated on every push from [research/01_hypothesis_register/_oos_showcase_data.yaml](research/01_hypothesis_register/_oos_showcase_data.yaml) per [ADR-0024](docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) D-8.

**Current top performer**: [**H060** TSMOM basket](research/01_hypothesis_register/H060/H060_kpi_report_v1.md) — cross-asset trend-following on `{ES, NQ, MGC, SIL}` produced realized OOS **$10,000 → $18,943 (+89.43%)** over 1,260 walk-forward concatenated OOS sessions; max-DD 28.57%; annualized Sharpe +0.617; pre-cost research-only v1. MPPM(ρ=1) point estimate +0.106 with bootstrap CI covering zero (`mppm-rho1-marginal`); BOCD decay-flag not raised over the OOS window.

Per the [Lo 2004 AMH](https://doi.org/10.3905/jpm.2004.442611) framing (canonical per ADR-0024 D-7), every realized OOS is a single path-realization; the forward-projection P(loss) column in [BEST_OOS.md](BEST_OOS.md) is the load-bearing companion. Strategy decay is the null.

---

## Research philosophy

The project's paradigm has evolved through five ADR-codified positions. Reading top-to-bottom, each later ADR amends the prior layer rather than deleting it (per [ADR-0013](docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1 non-loss mandate):

| ADR | Date | Position | Status |
|---|---|---|---|
| [ADR-0012](docs/decisions/ADR-0012-evidence-bar.md) | 2026-04-21 | Binding evidence-bar gates (Class A: leakage-canary, BSS, reliability slope, DSR, SPA p) at every stage transition. | Superseded by ADR-0013 |
| [ADR-0013](docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) | 2026-05-03 | **No binding gates.** Every former gate is a KPI annotation. Permanent exploration. Mandatory NinjaScript terminus. Non-loss mandate. | **Accepted; load-bearing** |
| [ADR-0017](docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) | 2026-05-08 | Survival-constrained 4-metric vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) elevated as primary; K-1..K-8 hard kill switches + FM-1..FM-5 stress tests as mandatory inheritance. | Accepted; **mandatory-inheritance clauses demoted to opt-in** by ADR-0024 |
| [ADR-0018](docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) | 2026-05-12 | MPPM(ρ=1) replaces Sharpe in inner-CV fitness; Kelly multiplier grid {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} (incl. super-Kelly cells under operator-discretionary annotation); BOCD decay detector; switching-bandit meta-strategy; Lo 2004 AMH canonical. | **Accepted** via ADR-0024 D-1 (2026-05-15) |
| [ADR-0024](docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) | 2026-05-15 | Formalize the H062 aggressive-growth-with-halt-and-switch framework as project-canonical. Demote ADR-0017 §4.2 + §5 + §6 mandatory-inheritance to opt-in tooling. Mandate the BEST_OOS.md showcase. | **Accepted; current canonical paradigm** |

Operational consequences of the current paradigm (ADR-0013 + ADR-0018 + ADR-0024):

- **Permanent exploration.** Every hypothesis goes into [hypothesis_backlog.md](hypothesis_backlog.md) with a pre-registered design doc. Null and negative results stay in the file — they document the search space we have covered. Per [Lo 2004 AMH](https://doi.org/10.3905/jpm.2004.442611), strategy decay is the null; a Sharpe-CI-covers-zero outcome on the OOS fold is informative evidence about regime change, not a project-level failure.
- **No gates.** Every former evidence-bar criterion is a KPI annotation in the per-strategy report card. Operator-discretionary review governs stage transitions.
- **MPPM(ρ=1) as primary fitness.** Inner-CV hyperparameter selection optimizes the Goetzmann-Ingersoll-Spiegel-Welch 2007 manipulation-proof performance measure at ρ=1 (which reduces analytically to log-wealth / Kelly fitness via L'Hôpital). Sharpe-family LW2008 differential CI + Hansen 2005 SPA p-value preserved as secondary KPIs for academic comparability.
- **Kelly multiplier grid-searched** over {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}. The literature-uniformly-dominated super-Kelly cells {1.5, 2.0, 2.5} are admissible under mandatory `super-kelly-operator-discretionary` KPI annotation per the operator 2026-05-08 standing $10K-sandbox directive; the evidence-bar discipline is **weakened** (not abolished) for those cells.
- **BOCD halt + switching-bandit redirect.** Adams-MacKay 2007 Bayesian Online Changepoint Detection on the rolling MPPM(ρ=1) path triggers a `decay-detected-yes` annotation; switching-bandit (D-UCB per Garivier-Moulines 2011 or GLR-klUCB per Besson-Kaufmann-Maillard-Seznec 2019, selected per cumulative-regret competition) redirects allocation to the next-best per-instrument arm.
- **ADR-0017 survival primitives preserved as opt-in tooling.** Eight hard kill switches K-1..K-8 + five synthetic-failure-mode stress tests FM-1..FM-5 + risk-of-ruin Monte Carlo + 4-metric survival vector are KPI annotations + opt-in tooling, no longer mandatory inheritance. Per-hypothesis design.md §11.1 may invoke any subset with `# justify:` annotation.
- **NinjaScript is the terminus.** Every hypothesis MUST progress to a working C# strategy in [ninjascript/strategies/](ninjascript/strategies/), regardless of KPI value. Operator-discretionary per the 2026-05-04 standing decline-ninjascript directive.
- **Non-loss mandate.** No audit trail, ReproLog, sidecar, KPI report card, promotion log, NinjaScript strategy, or design.md may be deleted, overwritten, or wiped. Corrections produce versioned successors. Enforced fail-closed by [scripts/_hooks/check_non_loss_deletion.py](scripts/_hooks/check_non_loss_deletion.py).
- **Walk-forward only.** No k-fold. Time-ordered disjoint splits. Purge + embargo per López de Prado 2018 AFML §7.4. CPCV is the canonical splitter for any Sharpe KPI emission.

---

## Current state (2026-05-15)

| Hypothesis | Stage | Headline result |
|---|---|---|
| [**H050**](research/01_hypothesis_register/H050/) HMM regime-conditioned ES/NQ directional | `kpi-report-emitted` ([v1](research/01_hypothesis_register/H050/H050_kpi_report_v1.md)) | Sharpe-era hypothesis-of-record cleanly rejected on the 2024-2025 OOS fold (T_H050 LW2008 CI excludes zero on the negative side both symbols). Realized OOS reflects post-2022 regime divergence per [Lo 2004 AMH](https://doi.org/10.3905/jpm.2004.442611). Strongest cell: NQ unconditional ($10K → $7,440; −25.60%; max-DD 35.05%; forward P(loss) 64.9%). Hypothesis-of-record arm (NQ HMM-gated) is $10K → $1,580 / −84.20%. |
| [H051](research/01_hypothesis_register/H051/) HMM-gated Kalman pairs ES/NQ basis | `designed` | Not yet executed. |
| [**H052a**](research/01_hypothesis_register/H052a/) HMM regime-gated first-hour ORB | `kpi-report-emitted` ([v1](research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md)) | Hypothesis-of-record non-significant null (LW2008 CIs cover zero). **Strongest cell: NQ unconditional ORB +10.61% realized OOS** over 369 sessions; P(loss)=18.56% forward; consistent with primary-literature unconditional-ORB-on-futures (Holmberg-Lönnbark-Lundström 2013). Operator-declined NinjaScript progression. |
| [H052b](research/01_hypothesis_register/H052b/) QQQ 0DTE long-call scalp | `designed` | Vendor-gated on QQQ 0DTE option chain. |
| [**H053**](research/01_hypothesis_register/H053/) Multi-TF mediation + categorical archetype table | `kpi-report-emitted` ([v3](research/01_hypothesis_register/H053/H053_kpi_report_v3.md)) | Sharpe-CIs uniformly cover zero (`marginal`). **Strongest cell: NQ LightGBM +10.8% realized OOS** over the 2024-2025 fold; max-DD 3.7%; descriptive-mediation positive (in-sample partial-R² CI excludes zero); causal-mechanism `hybrid` per ADR-0022 §1.3. |
| [**H054**](research/01_hypothesis_register/H054/) Anti-gate first-hour ORB on ES | `kpi-report-emitted` ([v1](research/01_hypothesis_register/H054/H054_kpi_report_v1.md)) | Point-positive and directionally consistent (+3.50% anti-gated; max-DD 3.19%; P(loss)=29.24% forward); LW2008 CI covers zero at exploratory power. Anti-gate trigger rate 7/237 = 2.95% drives the wide CI. |
| [**H055**](research/01_hypothesis_register/H055/) Mechanized wick-rejection scalping (HMM-deferred v3) | `exploration-in-progress` | Pre-launch. Per ADR-0024, ADR-0017 §5 K-1..K-8 + §6 FM-1..FM-5 + §4.2 risk-of-ruin are now opt-in for H055; design.md §11.1 may invoke any subset. |
| H056–H059 | `queued` | Per the [H055 successor tree](plan/buildouts/h055_successor_tree_2026-05-06.md): per-component ML → stacking master → multi-TF attention → live probability display layer. |
| [**H060**](research/01_hypothesis_register/H060/) Cross-futures TSMOM on `{ES, NQ, MGC, SIL}` | `kpi-report-emitted` ([v1](research/01_hypothesis_register/H060/H060_kpi_report_v1.md)) | **Current top OOS performer.** Basket realized **$10K → $18,943 (+89.43%)** over 1,260 walk-forward concatenated OOS sessions; ann. Sharpe +0.617; max-DD 28.57%; pre-cost research-only v1; Kelly-multiplier 2.5× (super-Kelly, operator-discretionary); MPPM(ρ=1) +0.106 (CI covers zero, `marginal`); BOCD decay-flag not raised. |
| [**H062**](research/01_hypothesis_register/H062/) Intraday Donchian-channel breakout + BOCD halt + switching-bandit | `exploration-in-progress` (designed) | Canonical instantiation of the ADR-0024 paradigm. Pre-launch; 14 open BLOCKING preconditions per design.md §11.2 (13 closed of 27 total at this README revision). |

For the full per-hypothesis stage dashboard see [research/01_hypothesis_register/INDEX.md](research/01_hypothesis_register/INDEX.md). For emitted KPI report cards with mandatory 13-table results summaries see [research/01_hypothesis_register/RESULTS_INDEX.md](research/01_hypothesis_register/RESULTS_INDEX.md). For the auto-ranked best-OOS showcase see [BEST_OOS.md](BEST_OOS.md).

**Project-wide empirical observation through 2026-05-15**: Sharpe-differential CIs are systematically tighter around zero than realized $10K trajectories diverge ([ADR-0017](docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §Context observation 2; reframed under [ADR-0018](docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §Context observation 2 as a fitness-function-misspecification rather than a measurement-error claim). MPPM(ρ=1) is the fitness that retains the log-wealth signal Sharpe loses on compounding-bankroll strategies. The H060 +89.43% / Sharpe-CI-covers-zero pattern is the canonical case.

---

## Reproducibility contract

Every walk-forward run emits a [ReproLog](src/skie_ninja/utils/reproducibility.py) sidecar at `logs/reproducibility/{run_id}.json` with 13 frozen-dataclass fields: `git_head`, `pip_freeze`, `dataset_checksums`, `rng_seed`, `model_hash`, `timestamp_utc`, `env_id`, plus per-fold artifact SHAs. Substrate parquet partitions are SHA256-bound at `designed` status in each hypothesis's `data_requirements.md`. Per [ADR-0009](docs/decisions/ADR-0009-blas-thread-pinning.md), BLAS thread pinning is required for byte-deterministic HMM fits across runs.

Canonical wall-clock for a clean production walk-forward at the existing equity-index substrate (ES + NQ × 2015-2025, ~7.4M 1-min bars): **~7h50min** on a single 24-thread workstation (H050 run_id `31d23ec...`). Mid-run external kills (Windows Update, OS reboot, supervisor cap) are protected against by the three-layer defense in [ADR-0010](docs/decisions/ADR-0010-multi-hour-run-process-protection.md) + the preflight checklist in [ADR-0011](docs/decisions/ADR-0011-production-walkforward-runbook.md). Daily-cadence cross-futures walk-forwards (H060 pattern; basket on the post-2026-05-12 substrate) complete in **~2.5 min** wall-clock.

Canonical launch path (PowerShell on Windows; same syntax on Linux/macOS Bash):

```powershell
$env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; $env:OPENBLAS_NUM_THREADS=1
uv run python scripts/supervised_run.py `
  --hypothesis H050 --config config/hypotheses/H050.yaml
```

Sister scripts: `scripts/run_h052a_walk_forward.py`, `scripts/run_h054_walk_forward.py`, `scripts/run_h053_stage{0,1,2,3}_*.py`, `scripts/run_h060_walk_forward.py`. Forward-projection: `scripts/simulate_h053_v4_10k_2026.py`, `scripts/simulate_h050_v1_10k_2026.py`. Best-OOS showcase regeneration: `scripts/showcase_best_oos.py` (idempotent; non-destructive).

---

## Repository layout

| Path | Purpose |
|---|---|
| [**BEST_OOS.md**](BEST_OOS.md) | Auto-generated showcase of the strongest realized-OOS performer; regenerated on every push per ADR-0024 D-8 |
| [**hypothesis_backlog.md**](hypothesis_backlog.md) | Project-canonical hypothesis register — at-a-glance status table + tier-organized backlog |
| [**CHANGELOG.md**](CHANGELOG.md) | Condensed phase-by-phase summary (one line per phase). Full ledger in CLAUDE.md. |
| [**CLAUDE.md**](CLAUDE.md) | Full project-rules + audit-remediate-loop ledger (load-bearing internal doc) |
| [docs/glossary.md](docs/glossary.md) | Stage labels, KPI annotation grammar, statistical primitives, reproducibility terms |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records (18 ADRs); see [decisions/README.md](docs/decisions/README.md) |
| [docs/audits/](docs/audits/) | Audit-remediate-loop trails (append-only; protected) |
| [docs/research_notes/](docs/research_notes/) | Dated research memos (postmortems, reassessments, retrospectives) |
| [research/01_hypothesis_register/](research/01_hypothesis_register/) | Per-hypothesis design.md + stage.md + KPI report cards + failure_log.md; see [INDEX.md](research/01_hypothesis_register/INDEX.md) |
| [research/01_hypothesis_register/_oos_showcase_data.yaml](research/01_hypothesis_register/_oos_showcase_data.yaml) | Machine-readable cache feeding BEST_OOS.md |
| [research/00_literature_review/](research/00_literature_review/) | Grounded primary-literature citations |
| [research/03_audits/](research/03_audits/) | Pre-Phase-0 audit-remediate records (immutable) |
| [src/skie_ninja/](src/skie_ninja/) | Python package: data ingest, features, models (HMM), backtest engine, inference primitives (MPPM, BOCD, switching-bandit, Calmar, profit-factor, R-multiple, Kelly sizing, risk-of-ruin), NinjaTrader bridge |
| [tests/](tests/) | Unit + integration + property-based tests (>1,000 unit tests) |
| [scripts/](scripts/) | Walk-forward orchestrators (one per hypothesis), simulators, ingest CLI, preflight, [showcase_best_oos.py](scripts/showcase_best_oos.py) |
| [ninjascript/](ninjascript/) | NinjaTrader 8 C# strategies (terminal state of every hypothesis per ADR-0013 §5) |
| [config/](config/) | Instrument specs, hypothesis configs, data sources |
| [data/](data/) | Raw + interim + processed substrate; `external/` for ledgers and reference datasets |
| [logs/reproducibility/](logs/reproducibility/) | Auto-generated ReproLog sidecars (one per run) |
| [logs/promotions/](logs/promotions/) | Operator promotion / decline / retirement decision logs |
| [plan/](plan/) | Operational planning — buildouts, roadmaps, engineering specs; see [plan/README.md](plan/README.md) |
| [artifacts/](artifacts/) | Versioned model binaries + reports + universe log |
| [runs/](runs/) | Per-run sidecars + per-fold metrics |
| [reports/](reports/) | Per-hypothesis stage dispositions (Markdown narrative) |
| [.githooks/](.githooks/) | Repository-shared Git hooks (install via `git config core.hooksPath .githooks`) |

---

## Environment setup

```powershell
# Requires Python 3.11+ and uv
uv venv --python 3.11 .venv
uv pip install -e ".[dev]"
python scripts/bootstrap_env.py

# Enable the shared Git hooks (one-time; installs the pre-push BEST_OOS.md regen)
git config core.hooksPath .githooks
```

Shared data directory: `~/datasets/` (override with `SKIE_SHARED_DATA` env var). See [config/shared_data.yaml](config/shared_data.yaml).

The HMM forward-backward kernels under [src/skie_ninja/models/regime/_em_kernels.py](src/skie_ninja/models/regime/_em_kernels.py) are accelerated with Numba `@njit`. As of `P1-HMM-EM-NUMBA-KERNELS`, numba is included in the `[dev]` extra so the standard install above exercises the JIT path during testing. Reproducing production HMM fits to byte identity requires the same `(numba, llvmlite, host CPU feature set)` tuple as the producing run; cross-host fits agree only to `rtol = 1e-12`.

Per [ADR-0009](docs/decisions/ADR-0009-blas-thread-pinning.md), BLAS thread counts must be pinned to 1 for any KMeans-bearing code path (unit suite, walk-forward orchestrator, anything that constructs `GaussianHMM`). Set the BLAS env vars before importing numpy / sklearn (variables read at process start):

```powershell
$env:OMP_NUM_THREADS=1
$env:MKL_NUM_THREADS=1
$env:OPENBLAS_NUM_THREADS=1
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

- [BEST_OOS.md](BEST_OOS.md) — top OOS performer + ranked emitted KPI cards
- [hypothesis_backlog.md](hypothesis_backlog.md) — what we are researching and current status
- [research/01_hypothesis_register/INDEX.md](research/01_hypothesis_register/INDEX.md) — per-hypothesis stage dashboard
- [research/01_hypothesis_register/RESULTS_INDEX.md](research/01_hypothesis_register/RESULTS_INDEX.md) — KPI report cards across all hypotheses
- [docs/decisions/README.md](docs/decisions/README.md) — ADR index
- [docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md](docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) — current canonical paradigm
- [docs/glossary.md](docs/glossary.md) — terms and conventions
- [CHANGELOG.md](CHANGELOG.md) — condensed phase log
- [CLAUDE.md](CLAUDE.md) — full project rules + audit-remediate-loop ledger

## License

See [LICENSE](LICENSE) (when present). Source code is project-internal research; do not deploy against live capital without operator authorization. Strategies promoted to `live-promoted` are tracked at [logs/promotions/](logs/promotions/).
