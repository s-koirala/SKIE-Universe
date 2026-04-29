# Changelog

All notable changes to the SKIE-Universe research program are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; conventions are tailored to a longitudinal research program rather than a versioned software release. Entries are dated and link to the canonical audit trail under [docs/audits/](docs/audits/) or the canonical research memo under [docs/research_notes/](docs/research_notes/).

## [Unreleased]

### Added — 2026-04-28 — H053 multi-timeframe regression with opening-bar mediation (Tier 2b; merged from sibling claude/laughing-shamir-059944)
- New pre-registered hypothesis **H053** added to [plan/hypothesis_backlog.md](plan/hypothesis_backlog.md) Tier 2b: "Multi-timeframe 09:45→10:30 ET ES/NQ regression with opening-bar mediation and a categorical bias-target-probability table". Three ex-ante pre-registered arms (ElasticNet / LightGBM / open-weights LLM, the LLM arm conditional on H053 design.md §11.4 deterministic-replay scaffolding).
- Predictand: `y_{i,t} = log(C_i(10:30 ET, t)) − log(C_i(09:45 ET, t))` on the front-month roll-adjusted continuous series for ES + NQ.
- Imai-Keele-Tingley 2010 mediation analysis with NDE/NIE/TCE estimands as **descriptive secondary outcomes** (NOT gating); E-value sensitivity per VanderWeele-Ding 2017.
- H053 enters the project's **flat Hansen SPA universe** (sibling-branch SPA-universe topology) alongside H050/H051/H052a/H052b with **exactly 3 ex-ante slots** (Arm 1, Arm 2, Arm 3); arms whose §11.4 prerequisites fail to land before `running` consume their slot as `archive(null, prerequisite-not-met)` per H053 §8 family-entry rule, preserving family size at exactly 3.
- Pre-registration package at [research/01_hypothesis_register/H053/](research/01_hypothesis_register/H053/) — `design.md` (481 lines, 11-section pre-reg + §11.4 prerequisites), `data_requirements_H053_2026-04-28.md`, `lit_review_H053_2026-04-28.md`. (Filename-convention deviation from canonical `data_requirements.md` / no-precedent-`lit_review.md` tracked under follow-up `P1-H053-FILENAME-CONVENTION-NORMALISE`.)
- 6-cycle staged buildout (Cycles 7-12: feature factory → Stage-1 mediator-only Gao 2018 replication → Stage-2 multi-timeframe + mediation → Stage-3 full Arms 1+2 + SPA submission → paper-trade scaffolding → optional Arm-3 LLM) at [plan/h053_buildout_2026-04-28.md](plan/h053_buildout_2026-04-28.md).
- Audit trail (sibling-branch audit-remediate-loop): [docs/audits/audit_trail_2026-04-28_h053-design.md](docs/audits/audit_trail_2026-04-28_h053-design.md).
- Merge mechanics: fast-forward of `claude/laughing-shamir-059944` (4 commits ahead of merge-base, zero behind, zero conflicts per `git merge-tree`) per the audit-remediated branch-merge decision memo at [docs/research_notes/memo_branch-merge-decision_2026-04-27.md](docs/research_notes/memo_branch-merge-decision_2026-04-27.md). Merge surfaces a structural **SPA-universe topology incompatibility** between sibling H053's flat-universe approach and the chart-reader cohort's two-tier Family A/B declaration (synthesis memo §6); adjudication deferred to **ADR-0010** (separate commit). Neither topology is binding before any family-aggregate inference report.
- Concurrent renumber: chart-reader cohort H053-H056 → H057-H060 (sibling H053 keeps the ID per its committed-frozen pre-reg; current chart-reader cohort was uncommitted at merge time).

### Added — 2026-04-27 — Tier 2c AI chart-reader hypothesis cohort
- Four pre-registered hypotheses added to [plan/hypothesis_backlog.md](plan/hypothesis_backlog.md):
  - **H057** — 1D-CNN on causal 60×5 OHLCV tensor with HMM regime gate (train-from-scratch, zero pretraining contamination).
  - **H058** — Time-series foundation model (TimesFM-2.5-200M + Chronos-Bolt-base-205M) with LoRA fine-tune and HMM regime gate; 2 backbones contribute 2 SPA family entries.
  - **H059** — Open VLM (Qwen2.5-VL-3B-Instruct) LoRA fine-tuned on rendered candlestick chart with HMM regime gate; per-bar inference cadence with fold-0 wall-clock pilot gate.
  - **H060** — PatchTST trained from scratch on causal 60×5 OHLCV with HMM regime gate (train-from-scratch transformer baseline; zero pretraining contamination).
- Pre-registration design packages under [research/01_hypothesis_register/H057/](research/01_hypothesis_register/H057/), [H058/](research/01_hypothesis_register/H058/), [H059/](research/01_hypothesis_register/H059/), [H060/](research/01_hypothesis_register/H060/) — each with `design.md` (11-section pre-reg per [research/01_hypothesis_register/_TEMPLATE.md](research/01_hypothesis_register/_TEMPLATE.md)), `README.md` orientation, `data_requirements.md` companion.
- Synthesis memo: [docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md](docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md).
- Landscape survey memo: [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md).
- 3-round audit-remediate-loop with parallel quant-auditor + literature-check + reproducibility-verifier; 36 Round-1 + 22 Round-2 findings remediated; Round-3 verdict `clear`. Audit trail: [docs/audits/audit_trail_2026-04-27_chartreader-hypothesis-package.md](docs/audits/audit_trail_2026-04-27_chartreader-hypothesis-package.md).

### Changed — 2026-04-27 — Hansen SPA family declaration
- **Two separate families** declared per the chart-reader synthesis memo §6, replacing the implicit single-family assumption:
  - **Family A** (regime-lift, `{H050}`, M=1, `omega_method=hac`) — H050 stays under Romano-Wolf step-down per [ADR-0003](docs/decisions/ADR-0003-spa-vs-romanowolf.md) per its frozen pre-reg.
  - **Family B** (chart-reader cohort, `{H057, H058a, H058b, H059, H060}`, M=5, `omega_method=bootstrap`) — H050 is **baseline anchor only**, NOT a Family B member.
- The split preserves H050's frozen pre-reg without successor-ID violation and resolves the Round-1 quant-auditor finding that mixing within-arm (`gated − unconditional`) and cross-arm (`arm_gated − H050_gated`) statistics in a single Hansen SPA composite null is incommensurable.
- The pre-existing inconsistency between H050/design.md (Romano-Wolf) and H050.yaml + scripts/run_walk_forward.py (Hansen SPA) is tracked under `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` and binds resolution before any Family-A-aggregate inference.

### Changed — 2026-04-27 — Multi-sidecar `model_hash` interim composition rule
- Per-arm pre-aggregation rule pinned: `arm_sidecar_sha256 := sha256(sorted_tuple([sidecar_a, sidecar_b, ...]))`, then canonical outer 4-tuple `model_hash = sha256(sorted_tuple([arm_sidecar_sha256, hmm_sidecar_sha256, warm_cold_sidecar_sha256, ledger_rollup_sha256]))`. Permits arm-specific sidecar count while preserving outer-composition byte-equivalence. Binding until `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` lands.

## [2026-04-26]

### Added
- **HMM-fit cache amortization** via commit [`1c85f5f`](#) — closes `P1-H050-SMOKE-RUNTIME-INVESTIGATE`. Cache key `(symbol, fold_id, label_horizon)` yields 9× speedup on the H050 27-cell grid via 3-stratum × 9-cfgs/stratum amortization. Warm-cold sidecar SHA256 byte-identical under cache toggle. Round-2 isolated quant-auditor caught F-PLV-1 critical (2-tuple cache key would crash on cross-`vertical_barrier` cfg transition); fixed by extending key with `label_horizon`. Audit trail: [docs/audits/audit_trail_2026-04-26_hmm-cache-amortization.md](docs/audits/audit_trail_2026-04-26_hmm-cache-amortization.md).
- **Decade-wraparound bug fix** via commit [`329fd1b`](#) — roll-adjusted module v0.2.0 → v0.3.0 with `contract_id_full` disambiguation; AFML §2.4.3 anchor invariant verified empirically. Output frame SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`. Audit trail: [docs/audits/audit_trail_2026-04-26_roll-adjust-decade-wraparound.md](docs/audits/audit_trail_2026-04-26_roll-adjust-decade-wraparound.md).
- **Atomic `data_requirements.md` re-freeze** via commit [`029f85d`](#) — post-Cell-I substrate binding tables; runbook §8.1-8.6 verified. Audit trail: [docs/audits/audit_trail_2026-04-26_data-requirements-refreeze.md](docs/audits/audit_trail_2026-04-26_data-requirements-refreeze.md).
- **Cell I substrate landed** — Stage A executed for $16.5171 USD live `metadata.get_cost`; Stage B re-ran `vendor_legacy_1min` + `vendor_legacy_1min_roll_adjusted` with 22 partitions and 7,354,066 rows ES + NQ × 2015-2025. Closes `P1-H050-DATA-COVERAGE` and `P1-H050-CELL-I-LIVE-COST-CAPTURE`.

### Investigated
- **First production H050 walk-forward run** launched 2026-04-26 ~15:07 CT; killed at +180 min for diagnostic investigation. Diagnosis: HMM `select_gaussian_hmm` cold-fit per stratum-fold-symbol with `covariance_type=[diag, full]` on a single-feature 1-dim emission — for d=1 the `full` and `diag` paths are mathematically equivalent but the `full` implementation incurs ~10× the per-iteration constant factor of `diag`. New follow-ups: `P1-HMM-FULL-COV-1DIM-REDUNDANT` (perf, blocking next run; closure patch via model-class deduplication in `select_gaussian_hmm` + H050.yaml `hmm.covariance_type: [diag]` under preparation on a sibling branch — not yet merged into this lineage), `P1-ORCHESTRATOR-PROGRESS-LOGGING`. Audit trail: [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md).

## [2026-04-24]

### Added — Cycle 6 H050 feature factory + walk-forward orchestrator
- Yang–Zhang volatility + triple-barrier labels (`TripleBarrierLabeler`); 4 microstructure features (Parkinson RV, realized variance, realized skew, OFI tick-rule proxy; all PIT-safe, deterministic, no-silent-NaN); NT8 ES/NQ RTH cost model (`NT8EsNqRthV1CostModel`); Phase-A orchestrator [scripts/run_walk_forward.py](scripts/run_walk_forward.py) composing cycles 1–5; `H050.yaml` config; ADR-0007 (stacked embargo) + ADR-0008 (SPA omega). Audit trail: [docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md](docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md).
- **`P1-H050-AGGREGATION-RULE`** closed via commit `f96cf7d` — addendum r2 with binding §5 directives for arithmetic-vs-log conversion + LW2008 implementation gap. Audit trail: [docs/audits/audit_trail_2026-04-24_h050-aggregation-addendum.md](docs/audits/audit_trail_2026-04-24_h050-aggregation-addendum.md).
- **`P1-H050-LW2008-DIFFERENTIAL-CI-IMPL`** closed via commit `11f8fce` — Ledoit-Wolf 2008 studentised CI with per-replicate bandwidth + UZH IEW WP 320 verification. Audit trail: [docs/audits/audit_trail_2026-04-24_lw2008-differential-ci.md](docs/audits/audit_trail_2026-04-24_lw2008-differential-ci.md).
- **`P1-H050-AGGREGATION-CONVENTION-TEST`** closed via commit `edbf8c1` — machine-precision aggregation gate with 14 tests. Audit trail: [docs/audits/audit_trail_2026-04-24_h050-aggregation-convention-test.md](docs/audits/audit_trail_2026-04-24_h050-aggregation-convention-test.md).
- **`P1-H050-SPA-M1-DEGENERATE`** closed via commit `ade5ac0` — ADR-0008 extension + `SingleStrategySPAWarning` + 7 tests. Audit trail: [docs/audits/audit_trail_2026-04-24_spa-m1-degenerate.md](docs/audits/audit_trail_2026-04-24_spa-m1-degenerate.md).
- **`P1-H050-INNER-CV` + `P1-H050-LABEL-CV` + `P1-H050-UNIVERSE-ES-ONLY`** closed via commit `54f138a` — orchestrator triple per design.md §4 (AFML §3.4 triple-barrier 27-cell CV) + §5 (nested walk-forward CV per Varma & Simon 2006 with N_draws=200 + Bergstra-Bengio §2.2 volume argument). Audit trail: [docs/audits/audit_trail_2026-04-24_orchestrator-triple.md](docs/audits/audit_trail_2026-04-24_orchestrator-triple.md).
- **`P1-HMM-FOLD-WARM-START`** closed via commit `6fb2412`. Audit trail: [docs/audits/audit_trail_2026-04-24_hmm-fold-warm-start.md](docs/audits/audit_trail_2026-04-24_hmm-fold-warm-start.md).
- **`P1-HMM-BLAS-THREADING-ADR`** closed via commit `5b38e08` — ADR-0009 post-loop-verified. Audit trail: [docs/audits/audit_trail_2026-04-24_blas-threading-adr.md](docs/audits/audit_trail_2026-04-24_blas-threading-adr.md).
- **`P1-HMM-WARM-COLD-DIAGNOSTIC`** closed via commit `ec95c09` — Hellinger/TV passive observer. Audit trail: [docs/audits/audit_trail_2026-04-24_hmm-warm-cold-diagnostic.md](docs/audits/audit_trail_2026-04-24_hmm-warm-cold-diagnostic.md).
- **`P1-WF-ENGINE-FOLD-ID-PASSTHROUGH`** closed via commit `81f25f8` — engine introspection-based fold_id injection. Audit trail: [docs/audits/audit_trail_2026-04-24_wf-fold-id-passthrough.md](docs/audits/audit_trail_2026-04-24_wf-fold-id-passthrough.md).
- **`P1-CYCLE6-REPRO-DATASET-CHECKSUM`** closed via commit `6f19094` (wiring gate; 4 tests).
- **`P1-AUDIT-TRAIL-FULL-SUITE-COUNT`** closed — 552/552 unit tests green at HEAD.

## [2026-04-23]

### Added — Tier-2b buildout Cycles 1–5
- **Cycle 1** — Roll-adjusted continuous-contract derivative `vendor_legacy_1min_roll_adjusted` v0.2.0 per AFML §2.4.3 multiplicative ratio adjustment. 241/241 unit tests green. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle1-roll-adjusted-1min.md](docs/audits/audit_trail_2026-04-23_cycle1-roll-adjusted-1min.md).
- **Cycle 2** — NW-HAC + Sharpe-CI primitives at [src/skie_ninja/inference/stats/](src/skie_ninja/inference/stats/): Newey-West 1987 Bartlett estimator + Andrews 1991/NW 1994 bandwidths; Lo 2002 iid/η(q)/HAC-approx + Opdyke 2007 Mertens-HAC (primary). 273/273 unit tests green. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle2-hac-sharpe-ci.md](docs/audits/audit_trail_2026-04-23_cycle2-hac-sharpe-ci.md).
- **Cycle 3** — HMM regime-inference toolkit per [ADR-0005](docs/decisions/ADR-0005-hmm-regime-toolkit.md). Package [src/skie_ninja/models/regime/](src/skie_ninja/models/regime/) with log-space Baum-Welch EM, `GaussianHMM`, BIC grid selection, `HMMSidecar` SHA256 → `ReproLog.model_hash` via `with_model_hash`. 47 new unit tests; 320/320 green. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle3-hmm-toolkit.md](docs/audits/audit_trail_2026-04-23_cycle3-hmm-toolkit.md).
- **Cycle 4** — Walk-forward engine + purged/embargo CV + leak canaries. Package [src/skie_ninja/backtest/](src/skie_ninja/backtest/): `walk_forward_split` (per Bergmeir-Benítez 2012, Tashman 2000), `purged_kfold_split` + `cpcv_split` (AFML §7.4 / Ch.12; mlfinlab-compatible stacked embargo), `WalkForwardEngine` with Int64-schema-validated parquet ledger + SHA256 roll-up. 79 new unit tests; 399/399 green. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md](docs/audits/audit_trail_2026-04-23_cycle4-walk-forward.md).
- **Cycle 5** — Hansen 2005 SPA + Politis-Romano 1994 stationary bootstrap with Politis-White 2004 (+ PPW 2009 correction) automatic block-length selection. Modules: [src/skie_ninja/inference/bootstrap.py](src/skie_ninja/inference/bootstrap.py) + [src/skie_ninja/inference/multipletest/hansen_spa.py](src/skie_ninja/inference/multipletest/hansen_spa.py). 54 new unit tests; 453/453 green. Audit trail: [docs/audits/audit_trail_2026-04-23_cycle5-hansen-spa-bootstrap.md](docs/audits/audit_trail_2026-04-23_cycle5-hansen-spa-bootstrap.md).
- **ES + NQ 1-min raw OHLCV (Databento GLBX.MDP3, evidence-bar tier)** — 3,733,906 rows scriptable via `python scripts/ingest.py --dataset vendor_legacy_1min`. License verified. Audit trail: [docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md).

### Changed
- **Tier-2b split** — H052 split into H052a (HMM-gated ORB on CME futures ES/NQ/MNQ/MES) and H052b (HMM-gated QQQ 0DTE long-call scalp; renamed from H052).

## [2026-04-20]

### Added — Phase 1 ingest + Phase 2 scope extension
- **FOMC text + macro_surprise ingest pipelines** operational. 164 FOMC parquets (2015-01-01 → 2026-04-20, statements + minutes + press conferences across 64 meetings) and 1,686 macro_surprise parquets (11 of 12 ALFRED initial-release indicators + SPF consensus). Audit trail: [docs/audits/audit_trail_2026-04-20_phase1-ingest-remediation.md](docs/audits/audit_trail_2026-04-20_phase1-ingest-remediation.md).
- **ES 5-min features (prototype-tier)** — 269,594-row Databento-derived parquet imported from sibling SKIE_Ninja research repo under `vendor_skie_ninja_legacy` namespace. Audit trail: [docs/audits/audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md](docs/audits/audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md).
- **Phase 2 scope extension** — accepted via [ADR-0005](docs/decisions/ADR-0005-hmm-regime-toolkit.md) (HMM toolkit) and [ADR-0006](docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) (HMM track + sibling 0DTE repo). Four pre-registered hypotheses (H050/H051/H052a/H052b). Audit trail: [docs/audits/audit_trail_2026-04-20_hmm-scope-extension.md](docs/audits/audit_trail_2026-04-20_hmm-scope-extension.md).

## [2026-04-16]

### Added — Phase 0 foundation
- **Reproducibility utils** — [src/skie_ninja/utils/](src/skie_ninja/utils/): `paths.py` (ProjectPaths resolver), `clock.py` (CME session taxonomy), `instruments.py` (pydantic InstrumentSpec), `hashing.py` (deterministic file/frame/model SHA256), `reproducibility.py` (frozen `ReproLog` dataclass + atomic writes), `runcontext.py` (RunContext + crash-safe flush), `logging_setup.py` (structured JSON logger).
- **Tooling** — `.pre-commit-config.yaml` (ruff + nbstripout + nbqa + check-repro-log + check-instruments-yaml + check-ast-import-guard); `scripts/bootstrap_env.py` (Python 3.11+ band check); `scripts/hypothesis_new.py` (CLI scaffold).
- **NinjaTrader** — [ninjascript/strategies/TrivialSmokeTest.cs](ninjascript/strategies/TrivialSmokeTest.cs) (buy 1 MES 09:30 CT, flatten 15:00 CT, CSV fill log).

## ADRs

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](docs/decisions/ADR-0001-project-scope.md) | Project scope | accepted |
| [ADR-0002](docs/decisions/ADR-0002-bridge-selection.md) | Python-NT8 bridge selection | proposed |
| [ADR-0003](docs/decisions/ADR-0003-spa-vs-romanowolf.md) | SPA vs Romano-Wolf for FWER control | proposed |
| [ADR-0004](docs/decisions/ADR-0004-alpha-and-power-defaults.md) | Alpha and power defaults | accepted |
| [ADR-0005](docs/decisions/ADR-0005-hmm-regime-toolkit.md) | HMM canonical regime-inference toolkit | proposed |
| [ADR-0006](docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) | Scope extension: HMM track + sibling 0DTE repo | proposed |
| [ADR-0007](docs/decisions/ADR-0007-embargo-placement.md) | Embargo placement: stacked vs overlap form | accepted |
| [ADR-0008](docs/decisions/ADR-0008-spa-omega-method.md) | SPA omega estimator selection | accepted |
| [ADR-0009](docs/decisions/ADR-0009-blas-thread-pinning.md) | BLAS thread pinning for reproducibility | accepted |

## Conventions

- New entries land at the top of the `[Unreleased]` section while in-flight; promoted to a dated section at the close of each cycle / hypothesis package.
- Each entry references the canonical commit, audit trail, or research memo by markdown link.
- Negative / null hypothesis results are recorded here exactly like positives — see [plan/hypothesis_backlog.md](plan/hypothesis_backlog.md) §"New items append with sequential IDs" and the [archived(null) entries](plan/hypothesis_backlog.md) for the established record-everything discipline.
- Backfilled retroactively from existing audit trails 2026-04-27. Pre-2026-04-16 history is in [git log](../../commits/main).
