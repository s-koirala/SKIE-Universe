# Phase-1 reassessment + critical path to first strategy result (2026-04-23)

## One-line status

Data substrate for the directional track is now in place (raw tier); **zero code exists under [src/skie_ninja/{features,models,inference,backtest}/](../../src/skie_ninja/)** — those are scaffolded empty dirs. Strategy-development *code* can start today; first practical walk-forward result lands ~3 weeks out with focused work; paper-trade verdict lands ~3 months after that.

## What's actually delivered (2026-04-23)

### Phase 0 — Foundation
| Item | State |
|---|---|
| `uv` env + `uv.lock` + ruff/pytest/pre-commit | ✓ live |
| SessionStart / SessionEnd reproducibility hooks | ✓ live (session trails committed) |
| [config/instruments.yaml](../../config/instruments.yaml) | ✓ ES/NQ/MES/MNQ with CME-cited fees |
| NinjaTrader 8 Desktop | ✓ installed (discovered 2026-04-23); db tree populated with ES minute bars |
| `TrivialSmokeTest.cs` compiled + executed | ✗ awaiting F5 compile |
| ADR-0002 Python ↔ NT8 bridge | ✗ `proposed`; latency measurement pending live bench run |

### Phase 1 — Data substrate
| Dataset | Tier | Coverage | State |
|---|---|---|---|
| FOMC text (statements/minutes/press conf) | evidence-bar | 2015-01-01 → 2026-04-20, 164 docs | ✓ live |
| Macro surprise (ALFRED initial release + SPF) | evidence-bar | 2016-01-01 → 2026-04-20, 11 series, 1,686 events | ✓ live (`EXHOSLUSM495S` pending catalog reconciliation) |
| Vendor-SKIE-Ninja 5-min features parquet | **prototype** | ES 2020-01-01 → 2025-12-03, 269,594 rows, 47 features | ✓ live; **sibling-authored features, not in-project-verified** → prototype only per CLAUDE.md §Verification |
| vendor_legacy_1min raw OHLCV | **raw, NOT evidence-bar** | ES 2020-2025 + NQ 2020-2024, 3,733,906 bars | ✓ live; **no roll adjustment** → futures-analog of the corporate-action requirement in rules/quant-project.md §Time-series integrity is unmet |
| ES/NQ sub-minute tick (MBO / MBP-10) | — | — | ✗ gated on direct Databento subscription |
| QQQ 0DTE option chain | — | — | ✗ blocks H052; vendor/cost decision pending |
| Kalshi + Polymarket tick archive | — | — | ✗ not started |
| Altdata pilots (AIS / on-chain / ERCOT) | — | — | ✗ not started |

### Phase 2-5 — Features / Models / Inference / Backtest
**Zero .py files under** [src/skie_ninja/features/](../../src/skie_ninja/features/), [src/skie_ninja/models/](../../src/skie_ninja/models/), [src/skie_ninja/inference/](../../src/skie_ninja/inference/), [src/skie_ninja/backtest/](../../src/skie_ninja/backtest/), [src/skie_ninja/execution/](../../src/skie_ninja/execution/). The folder skeleton exists; no implementations.

## Gap analysis for "first strategy result"

"First strategy result" = first walk-forward out-of-sample Sharpe CI on a pre-registered hypothesis (H050 being the cheapest entry point — directional HMM on ES). The evidence bar from [CLAUDE.md](../../CLAUDE.md) §3:

1. Walk-forward OOS Sharpe CI (Lo 2002 / Opdyke 2007) excludes zero at 95%.
2. Passes Hansen SPA (2005) against the strategy universe to date.
3. Costs modeled with NT-realistic fill assumptions (fit, not assumed).
4. Reproducibility log present.

To produce one such result for H050 requires building all of:

| Build item | Lit references to verify before coding | Scope | Effort |
|---|---|---|---|
| Roll-adjustment derivative (`vendor_legacy_1min_roll_adjusted`) | De Prado *AFML* ch.2; CME roll calendar | 1 module, 1 schema, 1 ingest derivative, tests | 1-2 days |
| HMM toolkit per [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md) | Baum 1972 for Baum-Welch; Rabiner 1989 tutorial; Viterbi 1967 (causal forward-filter variant not raw Viterbi) | `skie_ninja/models/regime/hmm.py`, BIC/CV n_states selection, sidecar serialization | 1-1.5 weeks |
| Feature factory (H050-minimum set) | ABDV 2003 for macro; Hasbrouck for microstructure if extended | `skie_ninja/features/{macro,microstructure}/*.py`, point-in-time unit tests | 3-5 days |
| Walk-forward engine + purged/embargo CV | De Prado *AFML* ch.7; Bailey & De Prado 2012 (PBO) | `skie_ninja/backtest/engine/walk_forward.py`, purge + embargo config | 3-5 days |
| Cost model fit from (eventually) paper-trade fills | assume-zero is not acceptable; fit from logs, fallback to CME-published fee schedule | `skie_ninja/backtest/costs/`, slippage per session regime | 1-2 days (static floor); full fit gated on paper logs |
| Hansen SPA + stationary bootstrap | Hansen 2005; Politis-White 2004 bandwidth | `skie_ninja/inference/multipletest/hansen_spa.py`, bootstrap helpers | 2-3 days |
| Lo 2002 / Opdyke 2007 Sharpe CI | Lo 2002 FAJ; Opdyke 2007 SSRN | `skie_ninja/inference/stats/sharpe_ci.py` | 1 day |
| Newey-West HAC standard errors | NW 1987; Andrews 1991 bandwidth; NW 1994 bandwidth | `skie_ninja/inference/stats/hac.py` | 0.5-1 day |
| Assemble H050 pre-registered experiment | design.md; register null-result path | notebook or script under [research/02_experiments/](../../research/) | 1 day |

**Total engineering critical path: ~3 weeks of focused work** to first walk-forward result on H050. Null or positive both enter [research/01_hypothesis_register/](../../research/01_hypothesis_register/) per research philosophy; either way is a valid outcome.

## Timeline — honest estimates

Assumes focused work (not calendar-wall-clock). Multiply by availability fraction for real-world calendar.

| Milestone | Trigger condition | Engineering-time estimate | Earliest from today |
|---|---|---|---|
| **Strategy-dev code work begins** | nothing — all deps are in place | 0 days | **today** |
| **H050 first walk-forward result lands** | all 9 build items above complete, tests green, audit-remediate clears | ~3 weeks focused | ~3 weeks |
| **H050 evidence-bar cleared** | Sharpe CI excludes zero, Hansen SPA passes, null not archived | depends on actual alpha | ~3 weeks (if positive) / ∞ (if null — archive and move on) |
| **First paper-trade start** | evidence-bar cleared + NT8 bridge ADR-0002 accepted + strategy deployed to NT8 | ~1 week of integration once strategy exists | ~4 weeks if H050 passes |
| **Paper-trade verdict** | 60 session-days in NT8 with realized-vs-backtest Sharpe delta within CI per [CLAUDE.md](../../CLAUDE.md) §Execution bar | 60 session-days ≈ 12 calendar weeks | **~16 weeks** from today (if all phases pass) |
| **Live-trading candidacy** | paper-trade verdict + kill-switch wired + drawdown/latency monitors deployed | ~1-2 weeks final prep | ~18 weeks from today |

### Parallel-track items that may extend the schedule

- **H051 pairs** — needs tick (sub-minute) for queue-position work; can develop at 1-min resolution now but the evidence-bar submission likely requires a direct Databento tick subscription (~3-5 day lead for CME non-pro attestation + purchase).
- **H052 0DTE** — fully blocked on QQQ 0DTE option chain data. Separate vendor/purchase track.
- **ADR-0002 bridge latency bench** — NT8 is installed; the harness + NS AddOn scaffold can be written in ~1 day; measurement requires 3 live paper-trading sessions across RTH open / mid-day / ETH. Parallel track.

## Priority sequencing

If the goal is to front-load the **first** practical test (H050), the lowest-total-days path is:

1. **Roll-adjustment derivative** — unlocks evidence-bar tier on the existing data. ~1-2 days.
2. **HMM toolkit + Lo/Opdyke Sharpe CI + NW-HAC** — core statistical machinery. ~1.5 weeks.
3. **Walk-forward engine + purged CV** — the harness. ~3-5 days.
4. **H050 feature set (minimum)** — whatever the design doc requires. ~3-5 days.
5. **Hansen SPA** — strictly required before claiming. ~2-3 days.
6. **H050 execution + audit-remediate** — ~1 day.

Costs can be a CME-fee-schedule floor during walk-forward and refit from paper-trade logs later (the plan already gates the empirical cost model on Phase-5).

## Residual risk

- **Paper-trade calendar time is immovable** — the 60-session-day floor is a CLAUDE.md §Execution bar hard rule. No engineering acceleration reduces it.
- **Bridge selection still `proposed`** — if ATI-socket latency measurement shows p99 > 50 ms, the bridge decision shifts to NTDirect-pythonnet and that may require additional scaffolding.
- **Feature-engineering choice is the scientific content** — a rushed H050 feature set that doesn't carry signal beyond lag-1 technical noise is null by construction. CLAUDE.md §Parameter allows only data-driven, lit-cited feature choices; the ~3-5 day estimate assumes the design doc already names them.
- **Null results are successes but still block momentum** — if H050 returns null, H051/H052 inherit the same infrastructure so the per-hypothesis cost after the first is much lower (~1 week each), but calendar time for paper-trade still applies.

## Recommendation for next session

Pick one of:

- (A) Build the critical-path stack for H050, in order, with audit-remediate at each step. 3-week focused commitment. Highest leverage.
- (B) Build the roll-adjustment derivative + NT8 bridge bench harness in parallel — completes Phase-0 gate (ADR-0002 acceptance becomes possible) and upgrades the raw tier. ~1 week, lower research yield but unblocks live-track.
- (C) Attack the data gaps (QQQ 0DTE purchase decision, direct Databento tick subscription) — removes downstream blockers but does not produce a strategy result on its own.

(A) is the shortest path to a falsifiable result. Proposal: execute (A) over three one-week focused blocks, with a checkpoint after each.
