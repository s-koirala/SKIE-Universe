# Hypothesis Register — Stage Dashboard

Per-hypothesis current stage per [ADR-0013](../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1. The stage value is the most recent row in each hypothesis's `stage.md` (append-only; rows never deleted per ADR-0013 §4.1 non-loss).

For the broader hypothesis register (queued + tier-organized) see the project-canonical [hypothesis_backlog.md](../../hypothesis_backlog.md) at repo root. For emitted KPI report cards see [RESULTS_INDEX.md](RESULTS_INDEX.md).

## Lifecycle (ADR-0013 §1)

`queued` → `designed` → `exploration-in-progress` → `kpi-report-emitted` → `ninjascript-implemented` → `paper-trade-active` → `paper-trade-evaluated` → `live-promoted`

No stage is terminal. There is no `archive` stage. Operator-discretionary review of the KPI report card governs every stage transition.

## Active hypotheses (stage ≥ `designed`)

| ID | Title | Tier | Stage | Design | Stage tracker | KPI report cards | Failure log |
|---|---|---|---|---|---|---|---|
| **H050** | HMM regime-conditioned ES/NQ intraday directional signal | 2b | `kpi-report-emitted` | [design.md](H050/design.md) | [stage.md](H050/stage.md) | [v1](H050/H050_kpi_report_v1.md) | [failure_log.md](H050/failure_log.md) |
| **H051** | HMM-gated Kalman pairs ES/NQ basis | 2b | `designed` | [design.md](H051/design.md) | — | — | — |
| **H052a** | HMM regime-gated first-hour ORB on CME futures (ES/NQ/MNQ/MES) | 2b | `kpi-report-emitted` (operator-declined-ninjascript) | [design.md](H052a/design.md) | [stage.md](H052a/stage.md) | [v1](H052a/H052a_kpi_report_v1.md) | [failure_log.md](H052a/failure_log.md) |
| **H052b** | HMM regime-gated QQQ first-hour long-call 0DTE scalp | 2b | `designed` | [design.md](H052b/design.md) | — | — | — |
| **H053** | Multi-TF 09:45→10:30 ET ES/NQ regression with opening-bar mediation | 2b | `kpi-report-emitted` (v3) | [design.md](H053/design.md) | [stage.md](H053/stage.md) | [v1](H053/H053_kpi_report_v1.md) · [v2](H053/H053_kpi_report_v2.md) · [v3](H053/H053_kpi_report_v3.md) | [failure_log.md](H053/failure_log.md) |
| **H054** | Anti-gate first-hour ORB on CME ES | 2b | `kpi-report-emitted` | [design.md](H054/design.md) | [stage.md](H054/stage.md) | [v1](H054/H054_kpi_report_v1.md) | [failure_log.md](H054/failure_log.md) |
| **H055** | Mechanized intraday wick-rejection scalping (HMM-deferred v3) | 2b | `exploration-in-progress` (`designed` frozen) | [design.md](H055/design.md) | [stage.md](H055/stage.md) | [v0 skeleton](H055/H055_kpi_report_v0.md) | [failure_log.md](H055/failure_log.md) |
| **H060** | Cross-futures TSMOM on {ES, NQ, MGC, SIL} (pre-cost research-only v1) | 2c | `kpi-report-emitted` (non-significant null) | [design.md](H060/design.md) | [stage.md](H060/stage.md) | [v1](H060/H060_kpi_report_v1.md) | [failure_log.md](H060/failure_log.md) |
| **H062** | Intraday Donchian-channel breakout on {ES, NQ, MGC, SIL} at super-Kelly grid with BOCD halt + switching-bandit redirect | 2c | `kpi-report-emitted` (v1) | [design.md](H062/design.md) | [stage.md](H062/stage.md) | [v0 skeleton](H062/H062_kpi_report_v0.md) · [v1](H062/H062_kpi_report_v1.md) | [failure_log.md](H062/failure_log.md) |
| **H065** | Intraday Donchian-channel breakout with ATR-scaled TP overlay (H062 + M-grid) | 2b | `kpi-report-emitted` (v1; H_1 null on TP cells) | [design.md](H065/design.md) | [stage.md](H065/stage.md) | [v1](H065/H065_kpi_report_v1.md) | [failure_log.md](H065/failure_log.md) |

## Queued (per the H055 successor tree)

H056–H059 are pre-registered in [hypothesis_backlog.md](../../hypothesis_backlog.md) Tier 2b at status `queued`; design.md folders are created at `designed` transition per ADR-0013 §1. See [plan/buildouts/h055_successor_tree_2026-05-06.md](../../plan/buildouts/h055_successor_tree_2026-05-06.md) for sequencing.

| ID | Title | Architecture role | Blocker |
|---|---|---|---|
| H056 | Per-component ML successor of H055 | ADR-0015 Layer 1 | Awaits H055 KPI emission + ADR-0016 SKIE-NINJA-Volatility audit |
| H057 | Stacking master successor of H056 | ADR-0015 Layer 2 | Awaits H056 |
| H058 | Multi-TF attention orchestrator | ADR-0015 Layer 3 | Awaits H057 |
| H059 | Live probability display layer | Presentation-only | Awaits H058 calibration |

## Per-hypothesis structure

Each `H<ID>/` directory contains the following files (mandatory; per ADR-0013 §3):

- `design.md` — pre-registered hypothesis statement, universe, features, labels, splitter, cost model (§1–§7 immutable once frozen)
- `stage.md` — append-only chronological stage tracker
- `H<ID>_kpi_report_v<N>.md` — KPI report card per version (versioned successors only; v1 preserved verbatim when v2 emits per ADR-0013 §4.1)
- `failure_log.md` — append-only log of external kills, build defects, run failures, operator overrides
- `data_requirements.md` (where applicable) — substrate SHA256 binding at `designed` status
- `lit_review_H<ID>_<DATE>.md` (where applicable) — Phase-0 literature review

Frozen-pre-reg amendments (Path A under ADR-0013 §"Frozen pre-registration amendment") land as `*_addendum_<DATE>.md` files in the hypothesis directory; design.md §1–§7 are never modified after freeze.

## See also

- [ADR-0013 permanent-exploration / no-archive / NinjaScript terminus](../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- [ADR-0014 canonical end-of-simulation results-summary tables](../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md)
- [ADR-0017 survival-constrained optimization paradigm](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md)
- [docs/glossary.md](../../docs/glossary.md)
