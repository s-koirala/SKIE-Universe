---
hypothesis_id: H068_v2
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-20
git_head: TBD-pending-smoke-run
substrate_dataset_checksum: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_scientific_payload_sha256: TBD-pending-smoke-run
simulation_log_sha256: TBD-pending-smoke-run
simulation_script_sha256: TBD-pending-smoke-run
run_id: TBD-pending-smoke-run
sizing_convention: per_trade_atr_stop_5min_intraday_per_symbol_log_return_fixed_equity_rebase
supersedes: H068_v2_kpi_report_v0.md
superseded_by: null
parent_hypothesis_id: H068
parent_hypothesis_kpi: H068_kpi_report_v1.md
---

# H068 v2 — KPI Report Card v1 (PLACEHOLDER PENDING SMOKE-AUTHORIZED RUN)

> **v1 emitted as smoke-mode placeholder per Phase O.20 load-management directive.**
> The smoke walk-forward + sidecar SHA capture is deferred to an
> operator-authorized follow-up cycle. The orchestrator at
> [scripts/run_h068_v2_walk_forward.py](../../../scripts/run_h068_v2_walk_forward.py)
> is built and tested (44/44 unit + integration tests green on Phase O.20
> landing); per Phase O.20 §"CRITICAL SCOPE BOUND" the operator authorizes
> smoke runs separately as a follow-up cycle.

- **Hypothesis**: Multi-instrument basket expansion of H068 v1 cost-light Donchian channel-breakout. Universe expansion ES standalone → 3-symbol basket {ES, MGC, SIL} per ADR-0027 §D-4 single-axis-genetic-cross discipline. Closes `P1-H068-V2-EXPANDED-SUBSTRATE` BLOCKING follow-up registered by Phase O.18 closure synthesis (CLAUDE.md commit `8434c37`). Primary inferential test: per-slip-cell basket-aggregated MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero positively AND basket realized OOS ROI > 0 under conservative_prior AND per-symbol cost-friction-breakeven ratio ≥ 2 on ≥ 2 of 3 symbols (`cost-friction-dominated-edge-present` at basket level per ADR-0028 §D-2).
- **Design.md**: [design.md](design.md)
- **Stage**: `kpi-report-emitted` (per ADR-0013 §1 placeholder-emission protocol; numeric fields TBD pending smoke run)
- **Stage-tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)
- **Parent hypothesis**: [H068 v1 design.md](../H068/design.md) + [H068 v1 KPI v1](../H068/H068_kpi_report_v1.md). H068 v2 inherits H068 v1 modal feature configuration verbatim (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; fixed-equity rebase; slip-sensitivity sweep `sensitivity_mult ∈ {1.0, 0.5, 0.25}` ticks; A0 zero-cost + A1 conservative-prior cost arms); adds multi-instrument basket expansion as the single genetic-cross axis per ADR-0027 §D-4.
- **Empirical anchor**: [H068 v1 KPI v1 §"H_1 conjunctive verdict"](../H068/H068_kpi_report_v1.md) (slip=0.5 A1 ratio 2.278 + +23.12% realized OOS + n_trades=108 → CI width 4.35 → H_1 conjunctive NULL on criterion (b) statistical-power floor; first cost-light positive ROI in project history; pre-empirical structural prediction verified within 3% deviation).
- **Audit trail**: [docs/audits/audit_trail_2026-05-20_h068_v2_orchestrator.md](../../../docs/audits/audit_trail_2026-05-20_h068_v2_orchestrator.md)

## 0. End-of-simulation 3-component summary header (per ADR-0026 §D-1; effective 2026-05-19)

<!--
Per ADR-0026 §D-1: every KPI report card emitted from 2026-05-19 forward SHALL carry a §0 "3-component summary"
section PRECEDING the ADR-0014 §3.2 13-table format. The §0 consists of per-cell 3-row blocks at per-symbol AND
basket-aggregated granularity (per design.md §13 — per-symbol cells emit as descriptive supplementary; basket-
aggregated cells are the H_1 inferential anchor).
-->

| # | Component | Window | P/L % | Max-DD % | Win rate W/(W+L+Z) | MPPM(ρ=1) point | Realized-OOS q05 equity | Forward q05 equity | N (sessions/trades) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Realized OOS (full) | 2024-01-01 → 2026-05-15 | TBD-pending-smoke-run | TBD-pending-smoke-run | TBD-pending-smoke-run | TBD-pending-smoke-run | TBD-pending-smoke-run | n/a | TBD-pending-smoke-run |
| 2 | Realized OOS (2026-onward) | 2026-04-01 → 2026-05-15 | TBD-pending-smoke-run | TBD-pending-smoke-run | TBD-pending-smoke-run | TBD-pending-smoke-run | TBD-pending-smoke-run | n/a | TBD-pending-smoke-run |
| 3 | Forward 1-year bootstrap | 252-session MC per ADR-0013 §3.1.1 | n/a | TBD-pending-smoke-run | n/a | TBD-pending-smoke-run | n/a | TBD-pending-smoke-run | n/a |

(For each of the 108 per-symbol cells (3 symbols × 3 slip × 6 Kelly × 2 cost arms) PLUS each of the 36 basket-aggregated cells (3 slip × 6 Kelly × 2 cost arms), this 3-row block will be emitted per ADR-0028 §D-2 zero-cost-A0-reference convention at smoke-run-authorized emission cycle. Total per-symbol rows = 108 × 3 = 324; basket-aggregated rows = 36 × 3 = 108; grand total = 432 emitted rows post-smoke-run.)

## End-of-simulation results summary (per ADR-0014 §3.2 + ADR-0017 §3.2 + ADR-0019 Table 1c; 13 mandatory tables + bottom-line prose)

All 13 tables emit as **TBD-pending-smoke-run** placeholders below; full population is the operator-authorized smoke-run follow-up cycle. Per ADR-0014 §3.2 the 13 tables are a re-presentation of values already in §"Performance KPIs" + §"Realized OOS + Forward-Projection block" — they MUST NOT introduce new KPI values; cross-cell numerical agreement enforced at every audit-remediate-loop R3 verification step.

### Table 1 — P/L (realized OOS, $10K starting capital)

TBD-pending-smoke-run. Per-symbol per-slip × per-Kelly × per-cost-arm matrix + basket-aggregated matrix.

### Table 1c — Payoff-shape diagnostics (per ADR-0019)

TBD-pending-smoke-run. L-skewness τ_3 + 95% CI; payoff-shape annotation `skew-{positive,flat,negative}`; barbell-rebalance-candidate flag per ADR-0019 §3.

### Table 2 — Drawdown (realized + projected)

TBD-pending-smoke-run.

### Table 3 — Primary inference (T = MPPM(ρ=1) per design.md §1; primary CI with excludes-zero column)

TBD-pending-smoke-run. MPPM(ρ=1) per [ADR-0018 D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md); stationary-bootstrap CI via Politis-White 2004 block-length selection; n_bootstrap=1000; rng_seed=20260520.

### Table 3a — Terminal-wealth q05 (per ADR-0017 §3.2)

TBD-pending-smoke-run.

### Table 3b — Calmar-differential (per ADR-0017 §3.2)

TBD-pending-smoke-run.

### Table 3c — Profit-factor + R-multiple-mean (per ADR-0017 §3.2)

TBD-pending-smoke-run.

### Table 4 — Annualised Sharpe (with annualisation-factor declaration)

TBD-pending-smoke-run. Annualisation factor = 252 sessions/year per project-canonical convention.

### Table 5 — Win/Loss/Zero counts + win rate

TBD-pending-smoke-run. Per-symbol W/L/Z + basket-aggregated W/L/Z.

### Table 6 — Forward 1-year projection (252-session MC per ADR-0013 §3.1.1)

TBD-pending-smoke-run.

### Table 7 — Hansen SPA family p (per ADR-0008)

TBD-pending-smoke-run. KPI annotation only per design.md §8.

### Table 8 — Other KPIs

TBD-pending-smoke-run. Includes: best cfg per H_1; n_folds realized vs expected; max-DD annotation; cost model annotation; kill-switch runtime annotation; BOCD live-pause annotation; equity rebase mode; cost-friction-dominated-edge annotation per ADR-0028 §D-2; kill-switch-mode annotation per ADR-0028 §D-1; deferred-KPIs status.

### Table 9 — Methodological-correctness annotations

TBD-pending-smoke-run (one-line dot-separated). Expected annotation set on first emission:
- `leakage-canary-pass` (per Cycle-4 leak-canary inheritance verified by integration test)
- `repro-log-complete` (per ReproLog 13-field via RunContext binding)
- `paradigm-adr-0024-aggressive-growth` (paradigm inheritance from ADR-0024)
- `kelly-multiplier-grid-search` (per ADR-0018 D-2)
- `cost-conservative-prior` or `cost-zero` per cell-arm (per ADR-0025 §D-3)
- `kill-switch-mode-block` (per ADR-0028 §D-1 default; design.md §11.1)
- `bocd-live-inactive` (deferred per `P1-H068-V3-BOCD-LIVE`)
- `causal-mechanism-hybrid` (per ADR-0022 §1.3 inheritance from H068 v1)
- `payoff-shape-skew-positive` or `payoff-shape-skew-flat` per cell (per ADR-0019)
- `cost-friction-dominated-edge-{present, absent, n/a}` per slip-cell per ADR-0028 §D-2
- `power-margin-{ok, low}` per cell per design.md §9 + §11.2 n_min_trades_guard
- `promising-*` annotation per ADR-0026 §D-3 if any basket cell strictly excludes zero positively

## §"Bottom line" prose (≤ 8 sentences)

TBD-pending-smoke-run. Will state: H_1 conjunctive verdict per slip cell (MET / NOT-MET per the 3-criterion test); H068 v1 → H068 v2 inferential-power lift quantification (per design.md §9 expected ~8.2× CI shrinkage); per-symbol divergence finding (per design.md §1.5 caveat); next mandatory stage transition; cross-link to full report card body.

## 1. Methodological-correctness annotations

- **Leakage canary**: `leakage-canary-pass` — passed via [tests/integration/test_h068_v2_pit_canaries.py](../../../tests/integration/test_h068_v2_pit_canaries.py) (Canary A boundary-invariant + Canary B label-horizon + Canary C no train→test leak + Canary D NaN-poison + **Canary E NEW for H068 v2: cross-symbol-basket-aggregation symbol-order-invariant** per design.md §7 + `P1-H068-V2-BASKET-INVARIANT-TEST` BLOCKING-BEFORE-LAUNCH).
- **Reproducibility log**: `repro-log-complete` *(pending smoke-run)* — RunContext binding verified via [tests/unit/test_h068_v2_walk_forward.py::TestRunContextHookSurface](../../../tests/unit/test_h068_v2_walk_forward.py); ReproLog 13 fields emit at smoke-run execution time per `P1-H068-V2-REPROLOG-WIRE` (closed by orchestrator landing).
- **Substrate dataset_checksum**: `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per design.md §2 binding; per-partition SHA enumeration at smoke-run execution time per `P1-H068-V2-SUBSTRATE-PER-PARTITION-SHA-EMIT`.
- **Power-margin**: per design.md §9 H068 v2 expected basket n_trades ≈ 7,200 (~67× v1 ES-only n=108) clears the basket-level n_min=150 threshold easily; per-symbol per-cell n_min=50 threshold expected to clear on MGC + SIL; ES per-cell may emit `power-margin-low` annotation per design.md §11.2 `P1-H068-V2-N-MIN-TRADES-GUARD`.
- **Causal-mechanism annotation**: `causal-mechanism-hybrid` per ADR-0022 §1.3 inheritance from H068 v1 + H065 + H062.

## 2. Operator review section

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) no-binding-gates: the per-symbol AND basket-aggregated KPIs are reported in [§"End-of-simulation results summary"](#end-of-simulation-results-summary-per-adr-0014-32--adr-0017-32--adr-0019-table-1c-13-mandatory-tables--bottom-line-prose) alongside the H068 v1 parent reference + the H062 v2 per-symbol baseline. The operator chooses promotion timing on the Pareto-front per design.md §1 H_1.

**Next mandatory transition** (per ADR-0013 §1):
1. **Operator authorization of smoke walk-forward run** — operator authorizes execution of the [scripts/run_h068_v2_walk_forward.py](../../../scripts/run_h068_v2_walk_forward.py) orchestrator at the canonical launch path (documented below). Smoke run takes operator-discretionary wall-clock (~10-60 min on canonical substrate per H068 v1 + H062 v2 precedent; full sweep multi-hour).
2. **Stage transition** `kpi-report-emitted` → `ninjascript-implemented` is operator-discretionary per the user 2026-05-04 standing decline-ninjascript directive + ADR-0013 §5.3 operator-discretionary clause.

## 3. Canonical launch command (operator-authorized future smoke run)

Per Phase O.20 §"Full-production launch command":

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  uv run python scripts/supervised_run.py --hypothesis H068_v2 \
  --config config/hypotheses/H068_v2.yaml \
  --enable-kill-switch-runtime --enable-equity-rebase-current \
  --cost-model conservative_prior
```

Smoke run (operator-discretionary timing):

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  uv run python scripts/run_h068_v2_walk_forward.py --smoke
```

## 4. Cross-references

- Design: [design.md](design.md)
- Data requirements: [data_requirements.md](data_requirements.md)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Lit review: [lit_review_H068_v2_2026-05-20.md](lit_review_H068_v2_2026-05-20.md)
- Orchestrator: [scripts/run_h068_v2_walk_forward.py](../../../scripts/run_h068_v2_walk_forward.py)
- Unit tests: [tests/unit/test_h068_v2_walk_forward.py](../../../tests/unit/test_h068_v2_walk_forward.py)
- Integration tests: [tests/integration/test_h068_v2_pit_canaries.py](../../../tests/integration/test_h068_v2_pit_canaries.py)
- Audit trail: [docs/audits/audit_trail_2026-05-20_h068_v2_orchestrator.md](../../../docs/audits/audit_trail_2026-05-20_h068_v2_orchestrator.md)
- Parent KPI: [H068 v1 KPI v1](../H068/H068_kpi_report_v1.md)
- Parent design: [H068 v1 design.md](../H068/design.md)
- Sibling KPI: [H067 v1 KPI v1](../H067/H067_kpi_report_v1.md) (cost-light null reference)
- Grandparent design: [H065 design.md](../H065/design.md)
