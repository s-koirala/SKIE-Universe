# ADR-0017 v2 OOS Dashboard — Survival-Constrained Re-ranking

Re-emits H050/H052a/H053/H054 OOS metrics under the ADR-0017 §1 primary inferential vector (terminal-wealth-q05 + Calmar-differential + forward P(loss)). Sharpe-family metrics are preserved as legacy secondary KPIs only per ADR-0017 §B + ADR-0013 §1-§7 frozen-pre-reg immutability.

**Strictly post-processing** of existing v1 KPI artifacts; no walk-forward re-run was performed. Source per cell recorded in the script [scripts/emit_adr_0017_v2_dashboard.py](../../scripts/emit_adr_0017_v2_dashboard.py).

## ADR-0017 §1 Primary Metrics — All Cells

Calmar = annualized_return / max(|MaxDD|, ε); ε = 1e-9. Annualization: (1 + r_total)^(252/n_oos_sessions) − 1.

| Hypothesis | Symbol | Arm | Role | Realized end ($10K start) | Max-DD | Calmar | Calmar-diff vs bench | Terminal-wealth-q05 | Forward P(loss) | Pareto |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|

| H050 | ES | hmm_gated | PRIMARY | $1,898 (-81.0%) | 81.1% | -0.696 | -0.141 | $5,839 | 100.0% | dom by 14 |
| H050 | ES | unconditional | BENCHMARK | $5,631 (-43.7%) | 45.0% | -0.554 | — | $7,646 | 99.6% | dom by 13 |
| H050 | NQ | hmm_gated | PRIMARY | $1,580 (-84.2%) | 84.4% | -0.714 | -0.322 | $7,181 | 100.0% | dom by 14 |
| H050 | NQ | unconditional | BENCHMARK | $7,440 (-25.6%) | 35.0% | -0.392 | — | $8,004 | 64.9% | dom by 11 |
| H052a | ES | hmm_gated | PRIMARY | $9,906 (-0.9%) | 7.0% | -0.092 | -0.255 | $9,119 | 54.8% | dom by 7 |
| H052a | ES | unconditional | BENCHMARK | $10,161 (+1.6%) | 6.7% | +0.164 | — | $9,137 | 42.9% | dom by 5 |
| H052a | NQ | hmm_gated | PRIMARY | $10,339 (+3.4%) | 11.8% | +0.195 | -0.702 | $9,117 | 37.1% | dom by 5 |
| H052a | NQ | unconditional | BENCHMARK | $11,061 (+10.6%) | 8.0% | +0.897 | — | $9,442 | 18.6% | dom by 1 |
| H053 | ES | elasticnet | ALT | $9,683 (-3.2%) | 10.2% | -0.217 | -0.217 | $8,990 | 67.6% | dom by 10 |
| H053 | ES | lightgbm | PRIMARY | $10,643 (+6.4%) | 4.5% | +0.967 | +0.967 | $9,636 | 18.8% | **FRONT** |
| H053 | ES | passive_long | BENCHMARK | $9,996 (+0.0%) | 7.2% | +0.000 | — | $9,226 | 50.7% | dom by 5 |
| H053 | NQ | elasticnet | ALT | $10,617 (+6.2%) | 5.6% | +0.743 | +0.653 | $9,314 | 27.4% | dom by 3 |
| H053 | NQ | lightgbm | PRIMARY | $11,078 (+10.8%) | 3.7% | +1.944 | +1.855 | $9,569 | 15.7% | **FRONT** |
| H053 | NQ | passive_long | BENCHMARK | $10,129 (+1.3%) | 9.8% | +0.090 | — | $9,015 | 44.3% | dom by 7 |
| H054 | ES | anti_gated | PRIMARY | $10,350 (+3.5%) | 3.2% | +1.167 | +1.249 | $9,402 | 29.2% | dom by 1 |
| H054 | ES | unconditional | BENCHMARK | $9,946 (-0.5%) | 7.0% | -0.082 | — | $8,481 | 52.5% | dom by 9 |

## Pareto Front (no cell dominates these on terminal-wealth-q05 + Calmar + −P(loss))

Sorted by terminal-wealth-q05 descending, then forward P(loss) ascending.

| Rank | Hypothesis | Symbol | Arm | Terminal-wealth-q05 | Calmar | Forward P(loss) | Realized end | Max-DD |
|---:|---|---|---|---:|---:|---:|---:|---:|

| 1 | H053 | ES | lightgbm | $9,636 | +0.967 | 18.8% | $10,643 | 4.5% |
| 2 | H053 | NQ | lightgbm | $9,569 | +1.944 | 15.7% | $11,078 | 3.7% |

## Dominated Cells (sorted by terminal-wealth-q05 desc)

| Hypothesis | Symbol | Arm | Terminal-wealth-q05 | Calmar | Forward P(loss) | Dominated by |
|---|---|---|---:|---:|---:|---|

| H052a | NQ | unconditional | $9,442 | +0.897 | 18.6% | H053/NQ/lightgbm |
| H054 | ES | anti_gated | $9,402 | +1.167 | 29.2% | H053/NQ/lightgbm |
| H053 | NQ | elasticnet | $9,314 | +0.743 | 27.4% | H052a/NQ/unconditional; H053/ES/lightgbm; H053/NQ/lightgbm |
| H053 | ES | passive_long | $9,226 | +0.000 | 50.7% | H052a/NQ/unconditional; H053/ES/lightgbm; H053/NQ/elasticnet +2 more |
| H052a | ES | unconditional | $9,137 | +0.164 | 42.9% | H052a/NQ/unconditional; H053/ES/lightgbm; H053/NQ/elasticnet +2 more |
| H052a | ES | hmm_gated | $9,119 | -0.092 | 54.8% | H052a/ES/unconditional; H052a/NQ/unconditional; H053/ES/lightgbm +4 more |
| H052a | NQ | hmm_gated | $9,117 | +0.195 | 37.1% | H052a/NQ/unconditional; H053/ES/lightgbm; H053/NQ/elasticnet +2 more |
| H053 | NQ | passive_long | $9,015 | +0.090 | 44.3% | H052a/ES/unconditional; H052a/NQ/hmm_gated; H052a/NQ/unconditional +4 more |
| H053 | ES | elasticnet | $8,990 | -0.217 | 67.6% | H052a/ES/hmm_gated; H052a/ES/unconditional; H052a/NQ/hmm_gated +7 more |
| H054 | ES | unconditional | $8,481 | -0.082 | 52.5% | H052a/ES/unconditional; H052a/NQ/hmm_gated; H052a/NQ/unconditional +6 more |
| H050 | NQ | unconditional | $8,004 | -0.392 | 64.9% | H052a/ES/hmm_gated; H052a/ES/unconditional; H052a/NQ/hmm_gated +8 more |
| H050 | ES | unconditional | $7,646 | -0.554 | 99.6% | H050/NQ/unconditional; H052a/ES/hmm_gated; H052a/ES/unconditional +10 more |
| H050 | NQ | hmm_gated | $7,181 | -0.714 | 100.0% | H050/ES/unconditional; H050/NQ/unconditional; H052a/ES/hmm_gated +11 more |
| H050 | ES | hmm_gated | $5,839 | -0.696 | 100.0% | H050/ES/unconditional; H050/NQ/unconditional; H052a/ES/hmm_gated +11 more |

## ADR-0017 §1 Primary Verdict — Per Hypothesis

### H050

- **Primary arm**: `hmm_gated` — terminal-wealth-q05 = $5,839; Calmar = -0.696; forward P(loss) = 100.0%

- **Benchmark**: `unconditional` — terminal-wealth-q05 = $7,646; Calmar = -0.554; forward P(loss) = 99.6%

- **Differential (primary − benchmark)**: ΔCalmar = -0.141; Δterminal-wealth-q05 = $-1,808; ΔP(loss) = +0.4%

- **ADR-0017 §1 verdict**: **PRIMARY IS DOMINATED BY BENCHMARK** on all 3 axes


### H052a

- **Primary arm**: `hmm_gated` — terminal-wealth-q05 = $9,119; Calmar = -0.092; forward P(loss) = 54.8%

- **Benchmark**: `unconditional` — terminal-wealth-q05 = $9,137; Calmar = +0.164; forward P(loss) = 42.9%

- **Differential (primary − benchmark)**: ΔCalmar = -0.255; Δterminal-wealth-q05 = $-18; ΔP(loss) = +11.9%

- **ADR-0017 §1 verdict**: **PRIMARY IS DOMINATED BY BENCHMARK** on all 3 axes


### H053

- **Primary arm**: `lightgbm` — terminal-wealth-q05 = $9,636; Calmar = +0.967; forward P(loss) = 18.8%

- **Benchmark**: `passive_long` — terminal-wealth-q05 = $9,226; Calmar = +0.000; forward P(loss) = 50.7%

- **Differential (primary − benchmark)**: ΔCalmar = +0.967; Δterminal-wealth-q05 = $+410; ΔP(loss) = -31.9%

- **ADR-0017 §1 verdict**: **PRIMARY DOMINATES BENCHMARK** on all 3 axes


### H054

- **Primary arm**: `anti_gated` — terminal-wealth-q05 = $9,402; Calmar = +1.167; forward P(loss) = 29.2%

- **Benchmark**: `unconditional` — terminal-wealth-q05 = $8,481; Calmar = -0.082; forward P(loss) = 52.5%

- **Differential (primary − benchmark)**: ΔCalmar = +1.249; Δterminal-wealth-q05 = $+921; ΔP(loss) = -23.3%

- **ADR-0017 §1 verdict**: **PRIMARY DOMINATES BENCHMARK** on all 3 axes


## Profit-factor + R-multiple-mean (deferred per strategy class)

Per ADR-0017 §2.3 + §2.4: **profit-factor** requires per-session-or-per-bar P/L stream; **R-multiple-mean** requires per-trade stop-loss-distance + position-size + multiplier (definition: `R = realized_pnl / (stop_distance × position_size × multiplier)`).

- H050: per-bar HMM-gated; no per-trade stop → R-multiple structurally **n/a**. Profit-factor needs per-bar P/L stream (`oos_returns.parquet` not in worktree); tracked under `P1-WALK-FORWARD-PER-TRADE-LEDGER-SCHEMA`.
- H052a / H054: per-session ORB; no per-trade stop in summary → R-multiple **n/a**. Profit-factor needs per-session P/L stream (not preserved in metrics_summary.json).
- H053: per-session prediction → arm trade; no per-trade stop → R-multiple **n/a**. Profit-factor needs per-session P/L stream from sidecar; not yet exposed in scientific_payload.
- H055+ (per-trade ATR-scaled TP/SL): all 4 ADR-0017 primary metrics computable from inception per design.md §1.

Follow-up `P1-PER-SESSION-PNL-STREAM-EXPORT` (BLOCKING-BEFORE-FULL-V2-CASCADE): extend orchestrator outputs to preserve per-session P/L streams enabling profit-factor + period-Sharpe + arm-vs-bench distributional CI.


## Methodological annotations

- **Annualization**: realized period return → annualized via (1 + r)^(252/n_oos) − 1; clamped at −0.999 to preserve sign on catastrophic loss without complex roots.
- **Calmar denominator**: max(|MaxDD|, 1e-9); ε per ADR-0017 §2.2.
- **Forward projection**: 5,000 paths × 252 sessions; iid bootstrap where PW2004-selected block length = 1.0 else stationary bootstrap (Politis-Romano 1994). Per arm × symbol from existing v1 cards.
- **Pareto-dominance**: arm a dominates arm b iff a ≥ b on (terminal-wealth-q05, Calmar) AND a ≤ b on forward P(loss), with strict inequality on at least one axis.
- **Sharpe column omitted from primary table** per ADR-0017 §B; preserved per arm internally but not displayed in the operator-facing primary inferential view.
