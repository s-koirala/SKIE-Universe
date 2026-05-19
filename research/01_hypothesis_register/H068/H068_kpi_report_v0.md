---
hypothesis_id: H068
schema_version: kpi_report_card_v1
version: 0
date: 2026-05-19
git_head: TBD on first KPI emission per `P1-H068-PROD-RUN`
substrate_dataset_checksum: TBD on first KPI emission per `P1-H068-PROD-RUN` (pinned ES-only partition subset of canonical post-Phase-O.10 substrate `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`)
sidecar_scientific_payload_sha256: TBD on first KPI emission per `P1-H068-PROD-RUN`
simulation_log_sha256: TBD on first KPI emission per `P1-H068-PROD-RUN`
simulation_script_sha256: TBD on first KPI emission per `P1-H068-PROD-RUN`
run_id: TBD on first KPI emission per `P1-H068-PROD-RUN`
sizing_convention: per_trade_atr_stop_5min_intraday_ES_log_return_fixed_equity_rebase  # per ADR-0013 §3.1.1 table; mirrors H065 v2 M_inf_h062_v1_fixed-ES modal cell sizing
supersedes: null  # v0 is the pre-emission skeleton
superseded_by: null  # null until v1 lands
parent_hypothesis_id: H065
parent_hypothesis_kpi: H065_kpi_report_v2.md
---

# H068 — KPI Report Card v0 (PRE-EMISSION SKELETON)

<!--
v0 = placeholder pre-emission skeleton per CLAUDE.md §"KPI report card for every strategy".
First-emission v1 will be authored by `P1-H068-PROD-RUN` after the production walk-forward
completes. All TBD fields below resolve at that point. Per ADR-0013 §4.1 non-loss preservation,
this v0 skeleton is preserved verbatim once v1 lands.
-->

- **Hypothesis**: Cost-light Donchian channel-breakout on ES standalone, with sub-1-tick slip empirical sensitivity sweep `sensitivity_mult ∈ {1.0, 0.5, 0.25}` ticks as primary cost-reduction axis. Genetic successor of [H065 v2 M_inf_h062_v1_fixed-ES cell](../H065/H065_kpi_report_v2.md) per cross-hypothesis investigation 2026-05-19 addendum §3 row #1 (empirically promoted to rank #1 post-Phase-O.16 fee recalibration; CRR for ratio ≥ 2 = 36.7%). Primary inferential test: per-slip-cell ES OOS realized ROI > 0 under conservative_prior AND MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero positively AND cost-friction-breakeven ratio ≥ 2 (`cost-friction-dominated-edge-present` per ADR-0028 §D-2). (Final wording lifted from [design.md §1](design.md) at v1 emission.)
- **Design.md**: [design.md](design.md)
- **Stage**: `exploration-in-progress` (pre-emission)
- **Stage-tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)
- **Parent hypothesis**: [H065 design.md](../H065/design.md) + [H065 KPI v2](../H065/H065_kpi_report_v2.md). H068 inherits H065 v2 M_inf_h062_v1_fixed-ES cell modal feature configuration verbatim (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; fixed-equity rebase per H062 v1 modal); adds slip-sensitivity sweep as the single genetic-cross axis per ADR-0027 §D-4.
- **Empirical anchor**: [cross-hypothesis investigation 2026-05-19 addendum](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md) §3 row #1 (parent cell breakeven ratio = 1.266 unchanged since ES fees not in Phase O.16 scope; pre-cost OOS +40.54%; 110 trades; CRR for ratio ≥ 2 = 36.7%).
- **Sibling cost-light successor**: [H067 design.md](../H067/design.md) (H067 SIL successor; demoted to rank #2 post-Phase-O.16 per addendum §3).

## 0. End-of-simulation 3-component summary header (per ADR-0026 §D-1; effective 2026-05-19)

<!--
Per ADR-0026 §D-1: every KPI report card emitted from 2026-05-19 forward SHALL carry a §0 "3-component summary"
section PRECEDING the ADR-0014 §3.2 13-table format. The §0 consists of a single three-row table per arm × symbol + basket.
For H068 v1: ES standalone (no basket; "basket" row = ES row). Per-slip-cell rows × 3 components per cell.
-->

TBD on first KPI emission per `P1-H068-PROD-RUN`.

Per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md), the 3-component summary header SHALL emit per-slip-cell × per-Kelly-multiplier × per-cost-arm (A0/A1) rows with columns: Component / Window / P/L % / Max-DD % / Win rate W/(W+L+Z) / MPPM(ρ=1) point / Realized-OOS q05 equity / Forward q05 equity / N (sessions).

| # | Component | Window | P/L % | Max-DD % | Win rate W/(W+L+Z) | MPPM(ρ=1) point | Realized-OOS q05 equity | Forward q05 equity | N (sessions) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Realized OOS (full) | 2024-01-01 → 2026-05-15 | TBD | TBD | TBD | TBD | TBD | n/a | TBD |
| 2 | Realized OOS (2026-onward) | 2026-01-01 → 2026-05-15 | TBD | TBD | TBD | TBD | TBD | n/a | TBD |
| 3 | Forward 1-year bootstrap | 252-session MC per ADR-0013 §3.1.1 | n/a | TBD | n/a | TBD | n/a | TBD | n/a |

(For each of the 18 cells = 3 slip × 6 Kelly multipliers, both A0 and A1 cost arms emit this 3-row block per ADR-0028 §D-2 zero-cost-A0-reference convention. Total = 36 cells × 3 components = 108 emitted rows.)

## End-of-simulation results summary (per ADR-0014 §3.2 + ADR-0017 §3.2 + ADR-0019 Table 1c; 13 mandatory tables + bottom-line prose)

TBD on first KPI emission per `P1-H068-PROD-RUN`. The 13 tables are a re-presentation of values already in §"Performance KPIs" + §"Realized OOS + Forward-Projection block" — they MUST NOT introduce new KPI values; cross-cell numerical agreement enforced at every audit-remediate-loop R3 verification step per ADR-0014 §3.2.

### Table 1 — P/L (realized OOS, $10K starting capital)

TBD on first KPI emission per `P1-H068-PROD-RUN`. Per-slip-cell × per-Kelly-multiplier × per-cost-arm matrix. Annotate the H065 v2 M_inf_h062_v1_fixed-ES parent baseline (`sensitivity_mult=1.0` A1 cell) as comparison reference.

### Table 1c — Payoff-shape diagnostics (per ADR-0019)

TBD on first KPI emission per `P1-H068-PROD-RUN`. L-skewness τ_3 + 95% CI; payoff-shape annotation `skew-{positive,flat,negative}`; barbell-rebalance-candidate flag per ADR-0019 §3. Expected per parent H065 v2 M_inf-ES: skew-positive baseline preserved by slip-sensitivity sweep (the slip refinement does NOT affect per-trade R-multiple distribution shape; only the realized P/L magnitude after cost subtraction).

### Table 2 — Drawdown (realized + projected)

TBD on first KPI emission per `P1-H068-PROD-RUN`.

### Table 3 — Primary inference (T = MPPM(ρ=1) per design.md §1; primary CI with excludes-zero column)

TBD on first KPI emission per `P1-H068-PROD-RUN`. MPPM(ρ=1) per [ADR-0018 D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md); stationary-bootstrap CI via Politis-White 2004 block-length selection; n_bootstrap=1000; rng_seed=20260519.

### Table 3a — Terminal-wealth q05 (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H068-PROD-RUN`.

### Table 3b — Calmar-differential (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H068-PROD-RUN`. Benchmark = passive-long ES on same OOS window.

### Table 3c — Profit-factor + R-multiple-mean (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H068-PROD-RUN`.

### Table 4 — Annualised Sharpe (with annualisation-factor declaration)

TBD on first KPI emission per `P1-H068-PROD-RUN`. Annualisation factor √252 for per-session predictand; ES RTH session-day count per substrate.

### Table 5 — Win/Loss/Zero counts + win rate

TBD on first KPI emission per `P1-H068-PROD-RUN`.

### Table 6 — Forward 1-year projection (Median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%))

TBD on first KPI emission per `P1-H068-PROD-RUN`. Per ADR-0013 §3.1: 5,000 bootstrap paths × 252 sessions; per-arm initial bankroll = $10,000.

### Table 7 — Hansen SPA family p-value (KPI annotation per ADR-0008)

TBD on first KPI emission per `P1-H068-PROD-RUN`. Family size = 3 slip-cells (or 18 if extended to slip × Kelly grid); per ADR-0027 §D-2 DSR deflation MANDATORY since realized cells ≥ dsr_activation_size=10. Note: SPA + DSR are KPI annotations only per [ADR-0024 §D-1](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) no-binding-gates discipline.

### Table 8 — Other KPIs (cell-conditional annotations)

TBD on first KPI emission per `P1-H068-PROD-RUN`. Required rows per ADR-0014 §3.2 + ADR-0025 §D-5 + ADR-0028 §D-4 grammar:

| KPI | ES |
|---|---|
| Best label cfg per fold | TBD |
| Best slip cell per fold | TBD |
| Best Kelly-multiplier per fold | TBD |
| n_folds (realized/expected) | TBD → `power-margin-{adequate,marginal,low}` |
| n_trades per cell (min/median/max) | TBD → `power-margin-low` if any cell < 50 trades per §11.2 `P1-H068-N-MIN-TRADES-GUARD` |
| max-DD annotation | TBD → `max-dd-{favorable,comparable,adverse}` |
| Sharpe-vs-passive-long annotation | TBD → `sharpe-vs-passive-long-{positive,marginal,flat,negative}` |
| Cost model | `nt8_realistic_v1` × {A0 zero-cost, A1 conservative_prior at sensitivity_mult ∈ {1.0, 0.5, 0.25}} → `cost-zero` AND `cost-conservative-prior` (sensitivity_mult=1.0) AND `cost-empirical-slip-0.5-tick` (sensitivity_mult=0.5) AND `cost-empirical-slip-0.25-tick` (sensitivity_mult=0.25) per ADR-0025 §D-5 grammar extension per ADR-0028 §D-2 |
| Cost-friction-breakeven ratio (per ADR-0028 §D-2 + cross-hypothesis investigation 2026-05-19 §2 schema) | TBD per slip-cell; expected baseline 1.266 at sensitivity_mult=1.0; rises to ~2.22 at 0.5-tick; ~3.56 at 0.25-tick |
| Cost-friction-dominated-edge annotation | TBD → `cost-friction-dominated-edge-{present,absent,n/a}` per ADR-0028 §D-2 trigger semantics |
| Sortino / turnover / capacity | TBD |
| Kill-switch runtime (ADR-0025 §D-1) | `kill-switch-{active,inactive}` (K-4 + K-6 + K-7 enabled at v1; K-3 vacuous) |
| Kill-switch enforcement-mode (ADR-0028 §D-4) | `kill-switch-mode-block` (v1 default per Task #20 empirical finding; size-down deferred to v2) |
| BOCD live-pause (ADR-0025 §D-4) | `bocd-live-inactive` (v1 deferred per `P1-BOCD-LIVE-PRIOR-CALIBRATION-H068-V3`) |
| Equity rebase (ADR-0025 §D-2) | mode=`fixed` (per H065 v2 M_inf_h062_v1_fixed-ES parent cell preservation; current-equity rebase deferred to `P1-H068-V3-CURRENT-EQUITY-REBASE`) |
| Promising-* annotation (ADR-0026 §D-3) | TBD → `promising-mppm-cost-empirical-slip-0.5-tick-317429e49ad63674` per qualifying cell |
| Causal-mechanism annotation (ADR-0022) | `causal-mechanism-hybrid` per design.md §1.3 |

### Table 9 — Methodological-correctness annotations (one-line per ADR-0013 §2 + §2.1 + ADR-0028 §D-4)

TBD on first KPI emission per `P1-H068-PROD-RUN`. Expected annotation grammar:

`leakage-canary-{pass,fail}` · `bss-{positive,flat,negative,n/a}` · `reliability-{in-band,out-of-band,n/a}` · `repro-log-{complete,incomplete}` · `dsr-{positive,marginal,negative,n/a}` · `post-run-audit-{pass,fail}` · `kill-switch-{active,inactive}` · `kill-switch-mode-{block,size-down}` · `bocd-live-{pause,active}` · `cost-{empirical-calibrated,conservative-prior,zero,empirical-slip-0.5-tick,empirical-slip-0.25-tick}` · `cost-friction-dominated-edge-{present,absent,n/a}` · `causal-mechanism-{hybrid,causal-mechanism,correlation-only}` · `skew-{positive,flat,negative}` · `promising-{kpi-vector-slug}-{cost-model-slug}-{substrate-sha-prefix-16}` (per qualifying cell; ADR-0026 §D-3)

### Bottom line

TBD on first KPI emission per `P1-H068-PROD-RUN`. Per ADR-0014 §3.2 Bottom-line ≤ 8 sentences stating:
1. Primary inferential verdict (positive / null / negative) per the binding test statistic from design.md §1.
2. Realized + projected $10K equity outcome in operator-readable phrasing per slip-cell ranking.
3. Cost-friction-breakeven ratio summary + cost-light-mechanism interpretive verdict (does sub-1-tick slip push above ratio ≥ 2 threshold at sensitivity_mult=0.5? At sensitivity_mult=0.25?).
4. Next mandatory stage transition per ADR-0013 §1 + §5 (operator-discretionary decline-ninjascript per 2026-05-04 standing directive).
5. Cross-link to full report card body (the 13 tables are SUMMARY; body retains canonical detailed presentation per ADR-0013 §3 + §3.1).

Full report card: [research/01_hypothesis_register/H068/H068_kpi_report_v1.md](H068_kpi_report_v1.md). Sim output: TBD per `P1-H068-PROD-RUN`.

## Cross-references

- [Design: H068 design.md](design.md)
- [Data requirements: H068 data_requirements.md](data_requirements.md)
- [Lit review: H068 lit_review_H068_2026-05-19.md](lit_review_H068_2026-05-19.md)
- [Stage tracker: stage.md](stage.md)
- [Failure log: failure_log.md](failure_log.md)
- [Parent hypothesis H065 design.md](../H065/design.md) + [H065 KPI v2](../H065/H065_kpi_report_v2.md)
- [Sibling cost-light successor H067 design.md](../H067/design.md) (demoted to rank #2 post-Phase-O.16 per cross-hypothesis investigation addendum §3)
- [Cross-hypothesis investigation 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md) + [addendum 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md)
- [H062 v3 ablation precedent](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- [Audit trail: docs/audits/audit_trail_2026-05-19_h068-cost-light-h065-es-design.md](../../../docs/audits/audit_trail_2026-05-19_h068-cost-light-h065-es-design.md)
