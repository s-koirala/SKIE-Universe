---
hypothesis_id: H068_v2
schema_version: kpi_report_card_v1
version: 0
date: 2026-05-20
git_head: TBD on first KPI emission per `P1-H068-V2-PROD-RUN`
substrate_dataset_checksum: TBD on first KPI emission per `P1-H068-V2-PROD-RUN` (pinned {ES, MGC, SIL} 3-symbol-subset of canonical post-Phase-O.10 substrate `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`)
sidecar_scientific_payload_sha256: TBD on first KPI emission per `P1-H068-V2-PROD-RUN`
simulation_log_sha256: TBD on first KPI emission per `P1-H068-V2-PROD-RUN`
simulation_script_sha256: TBD on first KPI emission per `P1-H068-V2-PROD-RUN`
run_id: TBD on first KPI emission per `P1-H068-V2-PROD-RUN`
sizing_convention: per_trade_atr_stop_5min_intraday_per_symbol_log_return_fixed_equity_rebase  # per ADR-0013 §3.1.1 table; preserves H068 v1 + H065 v2 M_inf_h062_v1_fixed modal cell sizing per parent-cell preservation discipline
supersedes: null  # v0 is the pre-emission skeleton
superseded_by: null  # null until v1 lands
parent_hypothesis_id: H068
parent_hypothesis_kpi: H068_kpi_report_v1.md
---

# H068 v2 — KPI Report Card v0 (PRE-EMISSION SKELETON)

<!--
v0 = placeholder pre-emission skeleton per CLAUDE.md §"KPI report card for every strategy".
First-emission v1 will be authored by `P1-H068-V2-PROD-RUN` after the production walk-forward
completes. All TBD fields below resolve at that point. Per ADR-0013 §4.1 non-loss preservation,
this v0 skeleton is preserved verbatim once v1 lands.
-->

- **Hypothesis**: Multi-instrument basket expansion of H068 v1 cost-light Donchian channel-breakout. Universe expansion ES standalone → 3-symbol basket {ES, MGC, SIL} per ADR-0027 §D-4 single-axis-genetic-cross discipline. Closes `P1-H068-V2-EXPANDED-SUBSTRATE` BLOCKING follow-up registered by Phase O.18 closure synthesis. Primary inferential test: per-slip-cell basket-aggregated MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero positively AND basket realized OOS ROI > 0 under conservative_prior AND per-symbol cost-friction-breakeven ratio ≥ 2 on ≥ 2 of 3 symbols (`cost-friction-dominated-edge-present` at basket level per ADR-0028 §D-2). (Final wording lifted from [design.md §1](design.md) at v1 emission.)
- **Design.md**: [design.md](design.md)
- **Stage**: `exploration-in-progress` (pre-emission)
- **Stage-tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)
- **Parent hypothesis**: [H068 v1 design.md](../H068/design.md) + [H068 v1 KPI v1](../H068/H068_kpi_report_v1.md). H068 v2 inherits H068 v1 modal feature configuration verbatim (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; fixed-equity rebase; slip-sensitivity sweep `sensitivity_mult ∈ {1.0, 0.5, 0.25}` ticks; A0 zero-cost + A1 conservative-prior cost arms); adds multi-instrument basket expansion as the single genetic-cross axis per ADR-0027 §D-4.
- **Empirical anchor**: [H068 v1 KPI v1 §"H_1 conjunctive verdict"](../H068/H068_kpi_report_v1.md) (slip=0.5 A1 ratio 2.278 + +23.12% realized OOS + n_trades=108 → CI width 4.35 → H_1 conjunctive NULL on criterion (b) statistical-power floor; first cost-light positive ROI in project history; pre-empirical structural prediction verified within 3% deviation).
- **Sibling cost-light successor**: [H067 design.md](../H067/design.md) (H067 SIL standalone N-lot grid; demoted to rank #2 per Phase O.18 strategic finding that N-lot is NOT a cost-reduction mechanism at conservative_prior).
- **Grandparent hypothesis**: [H065 design.md](../H065/design.md) (H065 v2 M_inf_h062_v1_fixed-ES parent cell; KPI v2 at `kpi-report-emitted`).

## 0. End-of-simulation 3-component summary header (per ADR-0026 §D-1; effective 2026-05-19)

<!--
Per ADR-0026 §D-1: every KPI report card emitted from 2026-05-19 forward SHALL carry a §0 "3-component summary"
section PRECEDING the ADR-0014 §3.2 13-table format. The §0 consists of per-cell 3-row blocks at per-symbol AND
basket-aggregated granularity (per design.md §13 — per-symbol cells emit as descriptive supplementary; basket-
aggregated cells are the H_1 inferential anchor).
-->

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`.

Per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md), the 3-component summary header SHALL emit per-symbol AND basket-aggregated rows × per-slip-cell × per-Kelly-multiplier × per-cost-arm (A0/A1) cells with columns: Component / Window / P/L % / Max-DD % / Win rate W/(W+L+Z) / MPPM(ρ=1) point / Realized-OOS q05 equity / Forward q05 equity / N (sessions or trades).

| # | Component | Window | P/L % | Max-DD % | Win rate W/(W+L+Z) | MPPM(ρ=1) point | Realized-OOS q05 equity | Forward q05 equity | N (sessions/trades) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Realized OOS (full) | 2024-01-01 → 2026-05-15 | TBD | TBD | TBD | TBD | TBD | n/a | TBD |
| 2 | Realized OOS (2026-onward) | 2026-04-01 → 2026-05-15 | TBD | TBD | TBD | TBD | TBD | n/a | TBD |
| 3 | Forward 1-year bootstrap | 252-session MC per ADR-0013 §3.1.1 | n/a | TBD | n/a | TBD | n/a | TBD | n/a |

(For each of the 108 per-symbol cells (3 symbols × 3 slip × 6 Kelly × 2 cost arms) PLUS each of the 36 basket-aggregated cells (3 slip × 6 Kelly × 2 cost arms), this 3-row block is emitted per ADR-0028 §D-2 zero-cost-A0-reference convention. Total per-symbol rows = 108 × 3 = 324; basket-aggregated rows = 36 × 3 = 108; grand total = 432 emitted rows.)

## End-of-simulation results summary (per ADR-0014 §3.2 + ADR-0017 §3.2 + ADR-0019 Table 1c; 13 mandatory tables + bottom-line prose)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. The 13 tables are a re-presentation of values already in §"Performance KPIs" + §"Realized OOS + Forward-Projection block" — they MUST NOT introduce new KPI values; cross-cell numerical agreement enforced at every audit-remediate-loop R3 verification step per ADR-0014 §3.2.

**v2 KPI report card scope clarification**: per [design.md §13](design.md), the 13-table summary is emitted at BOTH per-symbol granularity (3 × 13 = 39 tables emitted) AND basket-aggregated (13 tables emitted). The basket-aggregated tables are the H_1 inferential anchor; the per-symbol tables are descriptive supplementary surfaces for operator-discretionary per-symbol promotion decisions per ADR-0013 §1.

### Table 1 — P/L (realized OOS, $10K starting capital)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Per-symbol per-slip × per-Kelly × per-cost-arm matrix + basket-aggregated matrix. Annotate the H068 v1 ES standalone parent baseline (`sensitivity_mult=0.5` A1 cell at +23.12%) as comparison reference.

### Table 1c — Payoff-shape diagnostics (per ADR-0019)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. L-skewness τ_3 + 95% CI; payoff-shape annotation `skew-{positive,flat,negative}`; barbell-rebalance-candidate flag per ADR-0019 §3. Expected per parent H068 v1: skew-positive baseline preserved by multi-instrument basket aggregation (slip refinement + basket aggregation do NOT affect per-trade R-multiple distribution shape per-symbol; only the realized P/L magnitude after cost subtraction; basket-aggregated τ_3 will average per-symbol τ_3 values weighted by n_trades).

### Table 2 — Drawdown (realized + projected)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`.

### Table 3 — Primary inference (T = MPPM(ρ=1) per design.md §1; primary CI with excludes-zero column)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. MPPM(ρ=1) per [ADR-0018 D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md); stationary-bootstrap CI via Politis-White 2004 block-length selection; n_bootstrap=1000; rng_seed=20260520. **Expected CI width per Grinold 1989 √breadth multiplier**: basket-aggregated CI ≈ H068 v1 CI × 1/√(effective_breadth ≈ 2.5) ≈ H068 v1 CI × 0.63 vs naive √(n_v2/n_v1) ≈ 0.12 — the n-weighted-average dominates breadth at H068 v2's trade-count asymmetry.

### Table 3a — Terminal-wealth q05 (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`.

### Table 3b — Calmar-differential (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`.

### Table 3c — Profit-factor + R-multiple-mean (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`.

### Table 4 — Annualised Sharpe (with annualisation-factor declaration)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Annualisation factor = 252 sessions/year per project-canonical convention; per-session log-returns Sharpe = mean/std; annualised = √252 × per-session Sharpe. Per-symbol Sharpe + basket-aggregated Sharpe reported alongside.

### Table 5 — Win/Loss/Zero counts + win rate

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Per-symbol W/L/Z + basket-aggregated W/L/Z.

### Table 6 — Forward 1-year projection (Median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%))

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Per-symbol projection + basket-aggregated projection. Expected per H068 v1 forward-projection deferred footnote (sample-size constraint at n_trades=108 below 252-session bootstrap saturation): v2 expansion lifts n_trades to ~7,200 ≥ saturation threshold; v2 forward-projection IS expected to be tractable.

### Table 7 — Hansen SPA family p (with mechanical interpretation)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Family size at basket level = 3 slip-cells; K_max grows with the 18-cell joint slip × Kelly grid per H068 v1 §"deferred_kpis" status. Per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) `omega-corrected` method.

### Table 8 — Other KPIs (per ADR-0017 §3 + ADR-0019 + ADR-0025 + ADR-0026 + ADR-0028)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Per H068 v1 KPI v1 §Table 8 row template extended with:
- `best_label_cfg` — load-bearing per-slip-cell per-symbol + basket-aggregated winners
- `n_folds_realized` — TBD (multi-symbol walk-forward fold count)
- `n_folds_expected` — TBD
- `max_dd_annotation` — TBD per Tharp 1998 *practitioner* rule + per-symbol + basket-aggregated levels
- `cost_model` — nt8_realistic_v1; conservative_prior; sensitivity_mult ∈ {1.0, 0.5, 0.25}; per-symbol fee schedules per [data_requirements.md §"Per-symbol fee schedules"](data_requirements.md)
- `deferred_kpis` — TBD per H068 v1 deferred-kpi list inheritance
- `kill-switch-mode` — block (ADR-0028 §D-1 default; preserved from H068 v1)
- `K-6 trigger counts (per-symbol)` — TBD per symbol
- `K-7 trigger counts (per-symbol)` — TBD per symbol
- `equity-rebase-mode` — fixed (preserved from H068 v1 modal)
- `bocd-live-mode` — inactive (deferred to v3 per `P1-BOCD-CALIBRATION-PRE-OOS-HOLDOUT`)
- `cost-friction-dominated-edge-{present, absent, n/a}` — per ADR-0028 §D-2; per-symbol AND basket-aggregated
- `promising-mppm-{cost-provenance}-{substrate-checksum-prefix}-{cell-coordinates}` per ADR-0026 §D-3
- `payoff-shape` — skew-positive (expected per parent inheritance)
- `super-kelly-operator-discretionary` — TBD per Kelly cell
- `causal-mechanism` — hybrid (preserved from H068 v1)
- `cross-symbol-aggregation` — equal-weighted 1/N per DGU 2009 §3 (NEW v2 annotation)

### Table 9 — Methodological-correctness annotations

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Expected v2 annotation extensions vs H068 v1: `cross-symbol-aggregation-equal-weight` + `basket-invariant-canary-pass` (per design.md §7 Canary E new test) + per-symbol + basket-aggregated cost-friction-dominated-edge annotations.

## Bottom line (≤ 8 sentences per ADR-0014 §3.2)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`.

## Pareto-front operator deliverable (per design.md §8 + §13)

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Per-slip-cell × per-symbol vs basket-aggregated H_1 conjunctive verdict + operator-recommended slip* per Pareto-front interpretation.

## Per-fold + per-fold-aggregate cell results

TBD on first KPI emission per `P1-H068-V2-PROD-RUN`. Full 108-cell sidecar.

## Substrate provenance

| Field | Value |
|---|---|
| substrate_dataset_checksum | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.10 main-HEAD) |
| Symbols | {ES, MGC, SIL} (3-symbol subset of canonical 5-symbol substrate; NQ deliberately omitted per retail-equity-floor constraint; MCL deferred per inception-date constraint) |
| Per-symbol partition coverage | ES 2020-01-01 → 2026-05-15 (effective); MGC 2015-01-01 → 2026-05-15; SIL 2015-01-01 → 2026-05-15 |
| Active OOS window per design.md §2 | 2024-01-01 → 2026-05-15 per symbol |
| Sub-window (per ADR-0026 §D-1 component 2) | 2026-04-01 → 2026-05-15 (~30 sessions) |

ReproLog at `logs/reproducibility/<run_id>.json` (13/13 fields per CLAUDE.md §"Reproducibility (hook-enforced)" mandate; binds `model_hash` to `scientific_payload_sha256` per ADR-0017 §3). RNG seed = `20260520` (v2 distinguished from H068 v1's `20260519`).

## Scope deviations from full-spec inner-CV grid (recorded per Path A frozen-pre-reg amendment discipline)

- v2 reports the 108-cell representative grid (3 symbols × 3 slip × 6 Kelly × 2 cost-arm) at fixed H065 v2 modal feature cell. Full-grid combinatorial sweep tracked under `P1-H068-V2-FULL-INNER-CV-GRID-V3`.
- 3-symbol basket {ES, MGC, SIL}. 4-symbol basket {ES, MNQ, MGC, SIL} extension tracked under `P1-H068-V2-MNQ-EXTENSION-V3` (requires new Databento extraction; MNQ not in canonical substrate).
- MCL extension tracked under `P1-H068-V2-WITH-CL-MCL-EXTEND` (deferred from H068 v1; depends on H061 substrate-extension cycle).
- Walk-forward outer CV per H068 v1 (252-session-train / 60-session-test; embargo 2400 min).
- Forward-projection bootstrap EXPECTED to be tractable at v2 (n_trades ≈ 7,200 above 252-session saturation threshold).
- 1-lot per symbol at v2 (no pyramiding); N-lot scaling deferred to v3 per `P1-H068-V3-N-LOT-SCALING-PATH-DELAYED`.
- Equity rebase FIXED per H068 v1 + H065 v2 M_inf_h062_v1_fixed parent cell preservation. Current-equity rebase tracked under `P1-H068-V3-CURRENT-EQUITY-REBASE`.
- Kelly-multiplier {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} per ADR-0018 D-2 (preserved from H068 v1).
- BOCD live-pause primitive DISABLED at v2 per parent-cell preservation (deferred to v3 per `P1-H068-V3-BOCD-LIVE` + `P1-BOCD-CALIBRATION-PRE-OOS-HOLDOUT`).
- News-calendar exclusion (FOMC ±15min + NFP ±5min + CPI ±5min) feature-factory layer inherited from H062 + H068 v1 verbatim (no new exclusion at v2).

## Stage transition + next-step

| Field | Value |
|---|---|
| Stage at v0 (pre-emission) | `exploration-in-progress` (recorded in [stage.md](stage.md)) |
| Stage at v1 emission | `kpi-report-emitted` (transition pending `P1-H068-V2-PROD-RUN`) |
| Next mandatory transition per ADR-0013 §5 | `kpi-report-emitted` → `ninjascript-implemented` (operator-discretionary per user 2026-05-04 standing decline directive) |
| Tracked under | `P1-H068-V2-NINJASCRIPT-IMPL` (open; multi-symbol C# implementation per design.md §15) |

## Follow-ups registered by this KPI v0 emission

(Per [design.md §11.2](design.md) §11.2 BLOCKING preconditions; preserved here for traceability)

- `P1-H068-V2-WALK-FORWARD-ORCHESTRATOR-IMPL` (BLOCKING-BEFORE-LAUNCH)
- `P1-H068-V2-PIT-CANARY-INTEGRATION-TEST` (BLOCKING-BEFORE-LAUNCH)
- `P1-H068-V2-BASKET-INVARIANT-TEST` (BLOCKING-BEFORE-LAUNCH)
- `P1-H068-V2-SUBSTRATE-PER-PARTITION-SHA-EMIT` (BLOCKING-BEFORE-V2-EMISSION)
- `P1-H068-V2-REPROLOG-WIRE` (BLOCKING-BEFORE-V2-EMISSION)
- `P1-H068-V2-N-MIN-TRADES-GUARD` (BLOCKING-BEFORE-V2-EMISSION)
- `P1-H068-V2-PER-SYMBOL-MPPM-CI-EMIT` (BLOCKING-BEFORE-V2-EMISSION)
- `P1-H068-V2-PROD-RUN` (OPEN)
- `P1-H068-V2-MNQ-EXTENSION-V3` (deferred to v3; requires new Databento extraction)
- `P1-H068-V2-WITH-CL-MCL-EXTEND` (deferred; depends on H061 substrate-extension cycle)
- `P1-H068-V2-FULL-INNER-CV-GRID-V3` (deferred to v3)
- `P1-H068-V3-N-LOT-SCALING-PATH-DELAYED` (deferred per ADR-0027 §D-4 single-axis discipline)
- `P1-H068-V3-COST-REDUCTION-AXIS-BAR-CADENCE` (deferred per ADR-0027 §D-4 single-axis discipline)
- `P1-H068-V3-CURRENT-EQUITY-REBASE` (deferred per ADR-0027 §D-4 single-axis discipline)
- `P1-H068-V3-BOCD-LIVE` (deferred per `P1-BOCD-CALIBRATION-PRE-OOS-HOLDOUT`)
- `P1-H068-V3-COST-FRICTION-SENSITIVITY-EMPIRICAL-DEEPEN` (deferred per ADR-0027 §D-4)
- `P1-H068-V3-WITH-K6-K7-SIZE-DOWN` (deferred per ADR-0027 §D-4)
- `P1-H068-V2-NINJASCRIPT-IMPL` (operator-discretionary per ADR-0013 §5)
- `P1-H068-V2-NINJASCRIPT-PARITY-TOLERANCE` (operator-discretionary)
- `P1-H068-V2-GRINOLD-1989-DOI-VERIFY` (non-blocking verification-gap; pm-research.com auth-walled)
- `P1-H068-V2-BLDP-2014-DOI-VERIFY` (non-blocking verification-gap; pm-research.com auth-walled)
- `P1-H068-V2-MOSKOWITZ-OOI-PEDERSEN-2012-SECTION-PIN-VERIFY` (non-blocking section-pin verification)
- `P1-H068-V3-K5-CORRELATED-EXTEND` (deferred; re-evaluate K-5 when MES/GC/SI added)
