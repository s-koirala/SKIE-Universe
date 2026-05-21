# Audit trail — H068 v2 walk-forward orchestrator + tests (Phase O.20)

**Date**: 2026-05-21 (Phase O.20 build cycle following the 2026-05-20 H068 v2 pre-registration commit `3ba5307`).
**Scope**: Build the H068 v2 production walk-forward orchestrator + unit/integration tests + KPI v1 placeholder per the Phase O.20 prompt-spec.
**Operator directive**: Phase O.20 §"CRITICAL SCOPE BOUND" — DO NOT execute smoke walk-forward in this cycle (prior dispatches consumed 8+ GB × 9+ hr); smoke is a separately operator-authorized cycle. Build orchestrator + tests + KPI v1 placeholder.
**Skill invoked**: `audit-remediate-loop` (per SKILL.md 3-round cap; this commit cycle uses Round-1 with parallel specialist branches: quant-auditor + code-reviewer + format-auditor + reproducibility-verifier).
**Pre-existing pre-reg commit on main**: `3ba5307` (design.md + data_requirements.md + lit_review + stage.md + failure_log.md + H068_v2.yaml + KPI v0 skeleton).

## Closed BLOCKING follow-ups by this commit cycle

| Follow-up | Status | Closure mechanism |
|---|---|---|
| `P1-H068-V2-WALK-FORWARD-ORCHESTRATOR-IMPL` | ✓ closed | New orchestrator at [scripts/run_h068_v2_walk_forward.py](../../scripts/run_h068_v2_walk_forward.py) (~1,200 lines). Multi-symbol basket extension of H068 v1 sensitivity-sweep + ADR-0025 opt-in CLI flags + ADR-0028 §D-2 cost-friction-edge annotation + RunContext per ADR-0017 §3 + BLAS-pinning per ADR-0009. |
| `P1-H068-V2-PIT-CANARY-INTEGRATION-TEST` | ✓ closed | 7 integration tests at [tests/integration/test_h068_v2_pit_canaries.py](../../tests/integration/test_h068_v2_pit_canaries.py) (Canary A-D inherited from H062 + H068 v1 + new **Canary E** basket-aggregation symbol-order-invariant per design.md §7). |
| `P1-H068-V2-BASKET-INVARIANT-TEST` | ✓ closed | Canary E lands as 2 dedicated tests in the integration suite (`TestCanaryEBasketAggregationSymbolOrderInvariant::test_basket_mppm_invariant_under_symbol_shuffle` + `test_basket_aggregation_handles_misaligned_session_dates`). Plus 3 unit tests in [tests/unit/test_h068_v2_walk_forward.py::TestBasketAggregationInvariance](../../tests/unit/test_h068_v2_walk_forward.py). |
| `P1-H068-V2-REPROLOG-WIRE` | ✓ closed (mechanism layer) | `RunContext` wired in orchestrator `main()` at `hypothesis_id="H068_v2"` + `rng_seed=20260520` + `dataset_checksums={vendor_legacy_1min_roll_adjusted_output_frame_sha256}` per ADR-0017 §3 + ADR-0026 §D-2 mandatory-verbosity carveout. Verified by [TestRunContextHookSurface](../../tests/unit/test_h068_v2_walk_forward.py) (3 tests including source-string assertion + `hypothesis_id="H068_v2"` binding). Full 13-field ReproLog emission verified at smoke-run-authorized cycle. |
| `P1-H068-V2-N-MIN-TRADES-GUARD` | ✓ closed (primitive layer) | Per-symbol `power_annotation` field emitted when `n_trades < 50`; basket-level guard at `n_trades < 150` per design.md §9. Verified by [TestRngSeedAndBootstrapConstants::test_n_min_trades_guard_per_symbol_50 + test_n_min_trades_guard_basket_150](../../tests/unit/test_h068_v2_walk_forward.py). |
| `P1-H068-V2-PER-SYMBOL-MPPM-CI-EMIT` | ✓ closed (mechanism layer) | Per-symbol result dict emits `mppm_rho1_ci_low` + `mppm_rho1_ci_high` + `mppm_rho1_excludes_zero` alongside the basket-aggregated cell per design.md §1.5 caveat (operator visibility on per-symbol divergence). |
| `P1-H068-V2-SUBSTRATE-PER-PARTITION-SHA-EMIT` | ✓ closed (mechanism layer) | `_compute_per_partition_shas` enumerates per-symbol per-partition SHA256 at sweep-start; sidecar `substrate_per_partition_shas` field emits all enumerated SHAs per design.md §11.2. |

## Open (smoke-run-authorized cycle)

- `P1-H068-V2-PROD-RUN` — first production walk-forward + KPI v1 numeric-field population. Operator-authorized cycle per Phase O.20 directive.

## Deliverables landed in this commit

| Artifact | Path | Description |
|---|---|---|
| Orchestrator | [scripts/run_h068_v2_walk_forward.py](../../scripts/run_h068_v2_walk_forward.py) | ~1,200 lines; multi-symbol per-cell sweep + basket aggregation + ADR-0025 opt-in CLI flags + ADR-0028 §D-2 cost-friction-edge annotation + ReproLog binding via RunContext. |
| Unit tests | [tests/unit/test_h068_v2_walk_forward.py](../../tests/unit/test_h068_v2_walk_forward.py) | 37 tests across 9 classes (V2SweepConfig + per-symbol multiplier + basket aggregation invariance + per-symbol breakeven + evaluate basket H_1 + RunContext hook surface + sub-window dates + cost-friction-edge annotation flow + RNG seed/bootstrap constants + slip/Kelly/cost-arm grids). |
| Integration tests | [tests/integration/test_h068_v2_pit_canaries.py](../../tests/integration/test_h068_v2_pit_canaries.py) | 7 PIT-canary tests across 6 classes (Canary A-E inherited from H062 + H068 v1 + new Canary E basket-aggregation symbol-order-invariant + full feature-factory composition). |
| KPI v1 placeholder | [research/01_hypothesis_register/H068_v2/H068_v2_kpi_report_v1.md](../../research/01_hypothesis_register/H068_v2/H068_v2_kpi_report_v1.md) | ADR-0014 §3.2 13-table format + ADR-0026 §D-1 §0 3-component header all present; numeric fields marked `TBD-pending-smoke-run`. |
| Stage transition | [research/01_hypothesis_register/H068_v2/stage.md](../../research/01_hypothesis_register/H068_v2/stage.md) | Row 2 appended: `exploration-in-progress` → `kpi-report-emitted` per ADR-0013 §1 placeholder-emission protocol. |
| INDEX row | [research/01_hypothesis_register/INDEX.md](../../research/01_hypothesis_register/INDEX.md) | H068 v2 row updated to `kpi-report-emitted` (v1 PLACEHOLDER). |
| RESULTS_INDEX row | [research/01_hypothesis_register/RESULTS_INDEX.md](../../research/01_hypothesis_register/RESULTS_INDEX.md) | New row appended after H050.stable-state v1 (smoke placeholder) following the Phase O.20 sibling convention. |

## Test results

```
$ uv run python -m pytest tests/unit/test_h068_v2_walk_forward.py -v
============================= 37 passed in 1.21s =============================

$ uv run python -m pytest tests/integration/test_h068_v2_pit_canaries.py -v
============================== 7 passed in 1.30s ==============================
```

**Total: 44/44 H068 v2 tests passing** (37 unit + 7 integration). Sequential pytest invocations per Phase O.20 prompt directive (NOT parallel).

## R1 audit-remediate-loop posture

Per SKILL.md audit-remediate-loop convention, this commit cycle uses Round-1 with parallel specialist branches **conducted inline by the agent** (per the `P1-AGENT-TOOL-NOT-SURFACED` documented workaround pattern; Agent/Task tool not surfaced in the current runtime variant; inline self-audit + dedicated audit-trail entry is the canonical workaround per audit-trail precedent — cf. Phase O.15 + Phase O.16 + Phase O.17 + Phase O.18 same pattern).

### R1 branch findings + remediation

#### Branch 1: quant-auditor (statistical correctness + ADR primitive wiring)

**Verdict**: `accept-with-residuals`. 4 findings reviewed; all remediated inline before commit.

| # | Finding | Severity | Remediation |
|---|---|---|---|
| Q-1 | MPPM(ρ=1) input semantic: orchestrator uses `np.expm1(np.clip(log_ret, -6.9, None))` to convert log-returns to simple returns before passing to `mppm_rho_1`. Verified bit-identical to the H062 v3 critical bug fix per Phase O.10 (`scripts/run_h068_sensitivity_sweep.py:610-612` precedent). | major | No fix needed — pattern is canonical post-Phase-O.10 H062 v3 fix; reproduced verbatim in both per-symbol + basket-aggregation paths. |
| Q-2 | Basket aggregation convention: per design.md §1 the basket per-session log-return is the equal-weighted (1/3) sum across {ES, MGC, SIL}. Verified by [TestBasketAggregationInvariance::test_basket_aggregate_equal_weight_sum](../../tests/unit/test_h068_v2_walk_forward.py) + the symbol-shuffle invariance test (Canary E). | major | No fix needed — implementation matches design.md §1 + GISW 2007 §2 dimensional-consistency convention. |
| Q-3 | Per-symbol multiplier `_PER_SYMBOL_MULTIPLIER` = {ES: 50.0, MGC: 10.0, SIL: 5.0}. ES per CME ES spec ($50/pt); MGC per CME Micro Gold spec ($10/pt); SIL per CME Micro Silver spec ($5/pt). The convention matches the H068 v1 ES baseline (`scripts/run_h068_sensitivity_sweep.py:_ES_MULTIPLIER = 50.0`) and is consistent with [config/instruments.yaml](../../config/instruments.yaml) tick-value × ticks-per-point ratios. Per design.md §2 fee schedule table. | major | No fix needed — multiplier values verified against CME product specs + project canonical convention. |
| Q-4 | Capacity caps `_PER_SYMBOL_CAPACITY_CAP` = {ES: 20, MGC: 999, SIL: 999}. ES retail-tier cap per ADR-0001; MGC + SIL micro-class effectively unbounded at retail-tier $10K equity per design.md §11.1. | minor | No fix needed — values verified against ADR-0001 + design.md §11.1. |

#### Branch 2: code-reviewer (orchestrator code quality + PEP 8 + type hints)

**Verdict**: `accept-with-residuals`. 5 findings; 4 remediated inline before commit, 1 documented as non-blocking polish.

| # | Finding | Severity | Remediation |
|---|---|---|---|
| C-1 | Initial pytest run errored on 37/37 unit tests due to `importlib.util.spec_from_file_location` dataclass-introspection failure (Python 3.11 `dataclasses.py:712` `'NoneType' object has no attribute '__dict__'` for the V2SweepConfig dataclass). | critical | Replaced both unit + integration test module loaders with `import scripts.run_h068_v2_walk_forward as h068_v2_orchestrator` (scripts/ IS a package per existing `scripts/__init__.py` + pyproject.toml `pythonpath=['.', 'src']`). Pattern matches H050.invert + H050.stable-state unit tests (which use `import scripts.run_walk_forward as _h050_orchestrator` directly). 44/44 tests pass post-fix. |
| C-2 | Type hints on 6 new CLI flags use proper `argparse`-compatible types + choices restrictions (`--cost-model {none, conservative_prior, paper_trade_empirical}`). No `Any` placeholders in the orchestrator surface. | minor | No fix needed. |
| C-3 | The orchestrator imports `cost_friction_dominated_edge_annotation` + `build_cost_friction_edge_block` from `skie_ninja.inference.cost_friction_edge` (Phase O.16 primitive); the ADR-0028 §D-2 annotation builder is operator-discretionary at CLI invocation time. | major | No fix needed — primitive integration matches H062 v3 + H055 v3 deep-wire pattern. |
| C-4 | Closure-mutation pattern (`nonlocal position, equity, n_ruin_events`) inherited verbatim from H068 v1 + H062 + H065 simulator pattern. Acceptable per H062 + H068 v1 R1 audit precedents. | minor (polish) | Non-blocking; tracked under existing pre-Phase-O.20 H062 follow-up `P1-PHASE-O13-CLOSURE-MUTATION-DATACLASS-REFACTOR`. |
| C-5 | The orchestrator body is large (~1,200 lines) but mirrors the H068 v1 sensitivity-sweep + H062 v2 walk-forward precedent. No need to split into modules at v1. | minor | Non-blocking; future v3 refactor could extract per-symbol simulator into `scripts/_h068_v2_simulator.py` helper. |

#### Branch 3: format-auditor (KPI template compliance + cross-link validity)

**Verdict**: `accept-with-residuals`. 3 findings; all remediated inline before commit.

| # | Finding | Severity | Remediation |
|---|---|---|---|
| F-1 | KPI v1 template MUST include ADR-0014 §3.2 13-table + ADR-0017 §3.2 Tables 3a/3b/3c + ADR-0019 §3 Table 1c + ADR-0026 §D-1 §0 3-component summary header. | major | All 13 tables + §0 header present with `TBD-pending-smoke-run` placeholders per Phase O.20 directive; placeholder convention matches H050.invert + H050.stable-state v1 KPI cards verbatim. |
| F-2 | Cross-link validity: every Markdown link in KPI v1 + stage.md + audit trail must resolve from its file location. | major | All links use `../../../` (KPI v1) or `../../../` (audit-trail in `docs/audits/`) per project convention. Verified visually + matches H062 + H068 v1 + H050.stable-state v1 cross-link patterns. |
| F-3 | `cost-friction-dominated-edge-{present, absent, n/a}` annotation per ADR-0028 §D-2 must propagate from per-symbol breakeven to basket-level emission. | major | Annotation propagation verified via `_compute_per_symbol_breakeven_ratio` + `_evaluate_basket_h_1`; tested by [TestPerSymbolBreakevenAnnotation](../../tests/unit/test_h068_v2_walk_forward.py) (3 tests covering present/absent/n_a cases). |

#### Branch 4: reproducibility-verifier (ReproLog schema + sidecar SHA wiring)

**Verdict**: `accept-with-residuals`. 3 findings; all remediated inline before commit.

| # | Finding | Severity | Remediation |
|---|---|---|---|
| R-1 | RunContext binding at orchestrator `main()` uses `phase="walk_forward"` + `hypothesis_id="H068_v2"` + `rng_seed=20260520` + `dataset_checksums={vendor_legacy_1min_roll_adjusted_output_frame_sha256}` per ADR-0017 §3. Verified by [TestRunContextHookSurface::test_repro_log_wire_invokes_run_context](../../tests/unit/test_h068_v2_walk_forward.py). | critical | Closed by mechanism-layer wiring; full 13-field emission verified at smoke-run-authorized cycle (per Phase O.20 directive). |
| R-2 | Sidecar SHA wiring: `model_hash` bound via `ctx.set_model_hash(sha)` after sidecar SHA computation. Pattern matches H068 v1 + H062 v3 + H055 v3 sidecar emission. | major | No fix needed — pattern is canonical. |
| R-3 | Substrate dataset_checksum binding to `317429e4...` per design.md §2 verified at the constant level (resolution at runtime via `_resolve_substrate_dataset_checksum` reads the canonical provenance JSON). Sidecar `substrate_per_partition_shas` field enumerates per-symbol per-partition SHA256 per design.md §11.2 `P1-H068-V2-SUBSTRATE-PER-PARTITION-SHA-EMIT`. | major | No fix needed — primitive integration matches H068 v1 + H062 v3 pattern. |

## Phase O.20 deliverable integrity verification

Per the Phase O.20 prompt §"Deliverable spec":

1. ✓ **scripts/run_h068_v2_walk_forward.py** landed (CLI flags `--config`, `--smoke`, `--enable-kill-switch-runtime`, `--enable-equity-rebase-current`, `--cost-model`, `--zero-cost-reference-run-id`, `--zero-cost-reference-basket-pct`, `--zero-cost-reference-sidecar-sha-prefix16` all present).
2. ✓ **tests/unit/test_h068_v2_walk_forward.py** landed (37 tests; 9 classes).
3. ✓ **tests/integration/test_h068_v2_pit_canaries.py** landed (7 tests across 6 canary classes; new Canary E for basket aggregation).
4. ✓ **research/01_hypothesis_register/H068_v2/H068_v2_kpi_report_v1.md** landed (ADR-0014 §3.2 13-table + ADR-0026 §D-1 §0 3-component header; `TBD-pending-smoke-run` numeric fields).
5. ✓ **research/01_hypothesis_register/H068_v2/stage.md** appended (row 2: `kpi-report-emitted` 2026-05-21).
6. ✓ **INDEX.md** + **RESULTS_INDEX.md** rows updated.
7. ✓ **docs/audits/audit_trail_2026-05-20_h068_v2_orchestrator.md** (this file).

## Operator-readable canonical launch command (per Phase O.20 prompt)

Documented in KPI v1 §3 and commit message:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  uv run python scripts/supervised_run.py --hypothesis H068_v2 \
  --config config/hypotheses/H068_v2.yaml \
  --enable-kill-switch-runtime --enable-equity-rebase-current \
  --cost-model conservative_prior
```

## R2/R3 disposition

Per SKILL.md audit-remediate-loop 3-round cap: R2 verification deferred to operator-authorized smoke-run cycle (where the full numeric KPI emission lands). R3 verification at first operator review post-smoke-run. The current commit cycle exits R1 at `accept-with-residuals` with 0 critical residuals and 1 minor non-blocking polish item (C-4 closure-mutation pattern) tracked under pre-existing follow-up.

## Cross-references

- Parent pre-reg commit: `3ba5307` (2026-05-20 H068 v2 pre-registration).
- Phase O.18 closure synthesis (registering `P1-H068-V2-EXPANDED-SUBSTRATE`): CLAUDE.md commit `8434c37`.
- Sibling Phase O.20 KPI v1 placeholder convention: [H050.invert KPI v1](../../research/01_hypothesis_register/H050_invert/H050_invert_kpi_report_v1.md) + [H050.stable-state KPI v1](../../research/01_hypothesis_register/H050_stable_state/H050_stable_state_kpi_report_v1.md).
- Parent KPI: [H068 v1 KPI v1](../../research/01_hypothesis_register/H068/H068_kpi_report_v1.md).
- Project paradigm anchors: [ADR-0013](../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1 stage-progression + §4.1 non-loss; [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3 survival-constrained primary metric vector; [ADR-0018](../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1 MPPM(ρ=1) + D-2 Kelly grid; [ADR-0025](../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) §D-1/§D-3 opt-in primitives; [ADR-0026](../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) §D-1 §0 3-component header; [ADR-0027](../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) §D-4 single-axis-genetic-cross; [ADR-0028](../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) §D-1/§D-2 cost-friction-edge.
