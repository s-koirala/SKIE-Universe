---
id: ADR-0020
title: Meta-portfolio orchestrator — cross-arm decorrelation + inverse-variance breadth multiplier
status: proposed
date: 2026-05-12
deciders: skoir
amends:
  - (none — additive; introduces a new orchestration layer that sits above the per-hypothesis KPI report card layer. The ADR sits alongside ADR-0013 + ADR-0014 + ADR-0015 + ADR-0017 as a project-level standing rule that successor hypotheses and the new Meta-Portfolio v1 (MPV1) entity cite without re-derivation.)
preserves_immutability_of:
  - ADR-0013 §1 stage-progression model (the meta-portfolio is itself a hypothesis entity and progresses through the same stages)
  - ADR-0013 §3 KPI report card canonical structure (MPV1 emits a KPI report card under the same §3 structure)
  - ADR-0013 §4 non-loss mandate (per-arm `oos_returns.parquet` artifacts are inputs, never deleted or overwritten by the meta layer)
  - ADR-0013 §5 NinjaScript-terminus mandate (the meta-portfolio orchestrator gets its own C# implementation)
  - ADR-0014 §3.2 12-table results-summary structure (MPV1 KPI report card carries the full canonical table set as extended by ADR-0017)
  - ADR-0017 §3 survival-constrained primary inferential vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) — the meta-portfolio inherits these as primary metrics
  - ADR-0017 §5 K-1..K-8 kill-switch constraints (K-4 per-symbol cap + K-5 correlated-instrument inventory cap become load-bearing at the meta-allocator layer)
  - All previously frozen `status: designed` design.md §1-§7 sections (constituent arms are sourced from frozen pre-registrations, not amended)
---

# ADR-0020 — Meta-portfolio orchestrator: cross-arm decorrelation as the load-bearing breadth multiplier

## Context

The SKIE-Universe hypothesis register currently holds four emitted KPI report cards (H050, H052a, H053 v3, H054 v1) plus two designed-status hypotheses (H051, H055). Per-strategy results across the emitted set range roughly `SR ∈ [−0.45, +1.71]`; under [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md), no single arm has a Sharpe-differential CI excluding zero at the conventional one-sided level, and survival metrics are operator-mixed (NQ unconditional ORB at +10.61% realized OOS / P(loss) = 18.56%; NQ LightGBM at +10.8% realized OOS / max-DD 3.7%; all H050 gated arms catastrophic). The per-strategy inferential framing has produced six independent verdicts and zero composite verdict — **the cross-arm correlation matrix has never been computed**.

This is the load-bearing oversight. The Fundamental Law of Active Management ([Grinold 1989 *J Portfolio Mgmt* 15(3):30-37](https://doi.org/10.3905/jpm.1989.409211); canonical derivation [Grinold-Kahn 1999 *Active Portfolio Management* 2nd ed. McGraw-Hill](https://www.mhprofessional.com/active-portfolio-management-a-quantitative-approach-for-producing-superior-returns-and-controlling-risk-9780070248823-usa), *practitioner*) decomposes Information Ratio as `IR ≈ IC · √breadth` — Information Coefficient times the square root of the number of independent bets per unit time. The per-strategy framing systematically leaves the `√breadth` multiplier on the table: each arm is evaluated as if it were the only signal source. If H052a NQ unconditional ORB (fires 09:30-10:30 ET on the daily opening range), H053 NQ LightGBM (fires 09:45-10:30 ET on multi-timeframe features), and H054 ES anti-gated ORB (fires on the inverse of the H052a regime gate, plausibly with low temporal overlap) have low mutual correlation — a strong prior given they fire on different intraday clock-times and different feature sets — then an equal-weight portfolio of the three carries aggregate Sharpe substantially higher than any single arm. The breadth multiplier is the unrealized alpha source.

The modern-portfolio-theory frontier is canonical: [Markowitz 1952 *J Finance* 7(1):77-91](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) establishes the mean-variance frontier; [Black-Litterman 1992 *FAJ* 48(5):28-43](https://doi.org/10.2469/faj.v48.n5.28) adds Bayesian shrinkage toward equilibrium under heterogeneous prior strength. Under the project's `N_arms ≈ 6` regime, however, the small-sample estimation noise on the `K × K` covariance matrix dominates the theoretical optimum: [DeMiguel-Garlappi-Uppal 2009 *RFS* 22(5):1915-1953](https://doi.org/10.1093/rfs/hhm075) shows that equal-weight `1/N` outperforms mean-variance MVO out-of-sample across 14 datasets, with the breakeven sample size for MVO dominance scaling roughly as `~250 × N` monthly observations — well above the project's per-arm OOS horizon. [Ledoit-Wolf 2003 *J Empirical Finance* 10(5):603-621](https://doi.org/10.1016/S0927-5398(03)00007-0) provides the shrinkage-covariance estimator that closes the small-`N` gap between sample covariance and the constant-correlation target; this is the load-bearing primitive for any operator who selects MVO over `1/N` at runtime. [Brandt-Santa-Clara-Valkanov 2009 *RFS* 22(9):3411-3447](https://doi.org/10.1093/rfs/hhp003) offers the parametric-portfolio-policy generalization for non-Gaussian per-arm returns, relevant for hypotheses whose realized OOS distribution carries fat tails or skew (H050 gated arms; H052a NQ unconditional ORB right tail).

The project's inference layer already carries [Ledoit-Wolf 2008 *J Empirical Finance* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized circular-block bootstrap as the canonical differential-Sharpe CI primitive — this primitive is directly reusable for the META-portfolio's differential Sharpe vs the single-arm benchmark, with no new statistical machinery required. ADR-0017's survival-constrained vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) inherits unchanged: the meta-portfolio's per-session log-return series is itself a return series, and the Phase-L primitives at [src/skie_ninja/inference/](../../src/skie_ninja/inference/) consume it identically.

The intersection-of-OOS-dates constraint is the substrate-binding analogue of ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline. Per-arm `oos_returns.parquet` artifacts emitted by the per-hypothesis walk-forward orchestrator carry per-session log-returns over disjoint substrate windows — H050 OOS spans 2024-2025; H053 v3 OOS spans the v4 fold structure; H052a OOS spans 2023-H2 + 2024. The intersection is mechanically smaller than any single union, and small intersections produce statistically thin correlation estimates; the annotation `cross-arm-oos-overlap-{N_sessions}` is recorded at every meta-portfolio fit so the operator and the loop's audit-remediate discipline can flag thin-overlap configurations.

This ADR sits BEFORE the first meta-portfolio computation runs so the methodological discipline (weighting-scheme menu, default selection, intersection annotation, KPI report card layer, NinjaScript terminus) is fixed before the first artifact emits.

## Decision

The SKIE-Universe project adopts a **meta-portfolio orchestrator** as a new project-level orchestration layer above the per-hypothesis KPI report card layer. The orchestrator consumes per-arm OOS return artifacts and produces a composite return series carrying its own KPI report card under the ADR-0013 §3 + ADR-0014 §3.2 (as extended by ADR-0017) canonical structure.

### §1 — Infrastructure scope

The meta-portfolio orchestrator lives at `src/skie_ninja/meta/portfolio.py`. It consumes per-arm `oos_returns.parquet` artifacts emitted by each `kpi-report-emitted` strategy's walk-forward orchestrator. The orchestrator produces a meta-portfolio per-session return series and emits its own KPI report card under a new project subtree `research/01_meta_portfolio/`. Implementation is deferred under `P1-META-PORTFOLIO-ORCHESTRATOR-IMPL` (BLOCKING-BEFORE-MPV1-KPI-EMISSION).

### §2 — Three weighting schemes

The orchestrator supports three weighting schemes; the operator selects per-meta-portfolio at runtime:

1. **Equal-weight `1/N`** (default): each constituent arm receives weight `1/N_arms`. Justification: [DeMiguel-Garlappi-Uppal 2009](https://doi.org/10.1093/rfs/hhm075) Tables 3-7 demonstrate `1/N` dominance out-of-sample under the project's small-`N` regime (≤ 10 arms, ≤ 500 OOS observations). The simplicity-plus-robustness combination is the canonical low-estimation-noise default.

2. **Inverse-variance weighting**: `w_i ∝ 1 / σ_i^2` where `σ_i^2` is each arm's OOS realized return variance over the intersection window. Risk-balances the arms without requiring a full covariance matrix; intermediate between `1/N` (no information used) and full MVO (full covariance used).

3. **Ledoit-Wolf 2003 shrinkage-covariance optimal-MVO**: shrinkage-covariance estimator from [Ledoit-Wolf 2003](https://doi.org/10.1016/S0927-5398(03)00007-0) feeding the standard Markowitz quadratic program. The shrinkage target is the constant-correlation matrix per Ledoit-Wolf 2003 §3.3; the shrinkage intensity is the analytic optimum per their Theorem 1. Available for operators who explicitly assert (in the meta-portfolio's design.md §5) that `N_arms` and OOS-intersection size warrant the additional estimation cost.

The default `1/N` selection is locked because under `N_arms ≤ 10` and OOS-intersection ≤ 500 sessions the estimation noise on the `K × K` sample covariance matrix dominates the theoretical MVO optimum; this is the empirical regime the project actually inhabits, not the asymptotic regime where MVO dominates.

### §3 — Cross-arm correlation matrix on the intersection window

The cross-arm correlation matrix is computed on the **intersection** of OOS session-dates across all constituent arms, per the project's substrate-binding discipline under ADR-0013. Arms with non-overlapping OOS windows are inadmissible to the same meta-portfolio without explicit operator justification logged in the MPV1 design.md §2 partition table. Every meta-portfolio fit records the annotation `cross-arm-oos-overlap-{N_sessions}` in the KPI report card §"Methodological-correctness annotations" line. A one-shot diagnostic that computes the correlation matrix across the current four emitted arms (H050, H052a, H053 v3, H054 v1) is registered as `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE` and can execute BEFORE the orchestrator infrastructure lands; the matrix itself is a load-bearing artifact regardless of whether MPV1 launches.

### §4 — Meta-portfolio as a hypothesis entity

The meta-portfolio is itself a hypothesis entity per ADR-0013 §1. The first instance is **Meta-Portfolio v1** (MPV1) and lives at `research/01_meta_portfolio/MPV1/design.md` with frozen §1-§7 per the standard pre-registration discipline. MPV1 progresses through `exploration-in-progress` → `kpi-report-emitted` → `ninjascript-implemented` stages identically to any per-strategy hypothesis. Pre-registration is tracked under `P1-MPV1-PRE-REGISTRATION`. The §1 H_1 statement for MPV1 is operator-selected at pre-reg time (candidate framings: H_1-A "MPV1 terminal-wealth-q05 strictly dominates the max-over-arms single-arm terminal-wealth-q05"; H_1-B "MPV1 Calmar-differential vs equal-weight-passive-long-NQ excludes zero on the positive side"; H_1-C "MPV1 IR vs the best single-arm IR exceeds the Grinold-Kahn √breadth lower bound"). The choice of H_1 is operator-discretionary at pre-reg time and is itself a §1 freeze decision.

### §5 — Two-level inner-CV hyperparameter selection

Inner-CV hyperparameter selection happens at TWO levels: (i) within each per-arm walk-forward as before (untouched by this ADR); (ii) at the meta-portfolio layer over weighting-scheme choice + rebalance frequency (per-session vs per-week vs per-month vs static-over-OOS). The Layer-(ii) fitness function is MPPM(ρ=1) per ADR-0018 (load-bearing fitness for survival-constrained optimization under the project's risk-aversion convention). Operator-selected weighting scheme is annotated `meta-weighting-{1n,invvar,lw-mvo}` in the MPV1 KPI report card.

### §6 — NinjaScript implementation per ADR-0013 §5

A thin C# orchestrator at `ninjascript/strategies/MPV1_MetaPortfolio.cs` sources signals from each constituent arm's strategy file and produces meta-portfolio position sizes per the operator-selected weighting scheme. Implementation is **bridge-mediated** where any constituent arm requires Python inference at decision time (H050 HMM filter per ADR-0005; H053 LightGBM); **pure-C#** where all constituents are pure-C# (H052a, H054). The bridge-vs-pure-C# disposition is recorded in the MPV1 design.md §15 NinjaScript implementation block per ADR-0013 §5.1. The aggregator pattern is the unit of work tracked under `P1-META-PORTFOLIO-NINJASCRIPT-AGGREGATOR`.

### §7 — Aggregate kill-switch and capacity binding

[ADR-0001](ADR-0001-project-scope.md) per-symbol position-cap (≤ 20 ES, ≤ 40 NQ, with micro-equivalent mappings) applies to the **aggregate** meta-portfolio position, not per-arm. A meta-portfolio that allocates 60% to ES LightGBM and 40% to ES anti-ORB cannot exceed 20 aggregate ES contracts (the constituent arms must scale down proportionally). [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) §5 kill-switches K-4 (per-symbol position cap) and K-5 (correlated-instrument inventory cap; ES+MES share a budget, NQ+MNQ, YM+MYM, GC+MGC) become load-bearing at the meta-allocator layer with no per-arm carve-outs.

## Consequences

**Five follow-ups registered (project-wide)**:

- `P1-META-PORTFOLIO-ORCHESTRATOR-IMPL` (BLOCKING-BEFORE-MPV1-KPI-EMISSION) — implement `src/skie_ninja/meta/portfolio.py` with the three weighting schemes from §2; emit the meta-portfolio per-session return series; wire into the [scripts/](../../scripts/) production-runbook discipline per [ADR-0011](ADR-0011-production-walkforward-runbook.md).
- `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE` (one-shot diagnostic; **can run before infrastructure lands**) — compute the cross-arm correlation matrix on the OOS intersection across H050 + H052a + H053 v3 + H054 v1 emitted arms. Output: a single artifact under `research/01_meta_portfolio/diagnostics/cross_arm_correlation_matrix_2026-05-XX.md` with the matrix, the intersection-session-count annotation, and a operator note on whether the observed correlations support proceeding to MPV1.
- `P1-META-PORTFOLIO-NINJASCRIPT-AGGREGATOR` — implement the aggregator pattern at `ninjascript/strategies/MPV1_MetaPortfolio.cs` per ADR-0013 §5 + §6 above; bridge-vs-pure-C# disposition recorded in MPV1 §15.
- `P1-MPV1-PRE-REGISTRATION` — Meta-Portfolio v1 pre-registration at `research/01_meta_portfolio/MPV1/design.md` with frozen §1 H_1 statement, §2 substrate-binding partition table (per-arm `oos_returns.parquet` SHA256 + intersection partition), §3 features = per-arm OOS returns, §4 labels = per-arm OOS realized P/L, §5 splitter = (i) per-arm walk-forward + (ii) meta-layer hyperparameter inner-CV, §6 cost model = sum of constituent arms' cost models (no double-counting), §7 evaluation = ADR-0014 §3.2 12-table KPI report card.
- `P1-CROSS-ARM-OOS-OVERLAP-AUDIT` — audit-remediate-loop on the cross-arm OOS overlap to verify each constituent arm's `oos_returns.parquet` is PIT-correct, fold-disjoint, and free of look-ahead per Cycle-4 leak canaries before any meta-portfolio computation consumes it.

**Methodological-correctness annotations introduced**: `meta-weighting-{1n,invvar,lw-mvo}`; `cross-arm-oos-overlap-{N_sessions}`; `meta-bridge-{pure-c-sharp,bridge-mediated}`; `breadth-multiplier-{realized,unrealized}` (the latter computed as `IR_meta / max_i(IR_i)` and compared against the Grinold-Kahn √breadth lower bound).

**Operator-decision boundaries**: the operator chooses (a) which constituent arms enter MPV1 (a `kpi-report-emitted` arm is eligible; a `designed`-only arm is not); (b) which weighting scheme (default `1/N`); (c) which §1 H_1 framing (A/B/C from §4 above); (d) the rebalance frequency at the meta layer. All decisions are recorded in the MPV1 design.md per the standard pre-registration discipline and are immutable once `status: designed` is frozen.

**Backward compatibility**: per-hypothesis KPI report cards are unchanged. Per-arm `oos_returns.parquet` emission becomes a load-bearing artifact rather than a diagnostic byproduct; hypotheses lacking this artifact must regenerate it before they can enter a meta-portfolio (tracked per-arm under follow-ups in the residual-risk ledger of the relevant KPI report card).

**Risks and limits**: (a) the OOS-intersection window may be too small for any statistically meaningful correlation estimate — the diagnostic in `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE` is the load-bearing test; if intersection < ~60 sessions, MPV1 defers until more arms emit overlapping OOS; (b) the ADR-0001 aggregate-cap binding can mechanically reduce the realized breadth multiplier when multiple arms compete for the same per-symbol budget — this is the capacity-vs-breadth tradeoff and is recorded as a KPI annotation, not a bug; (c) bridge-mediated NinjaScript implementation under §6 imposes the same Python-process-protection costs as H050 per [ADR-0010](ADR-0010-multi-hour-run-process-protection.md); (d) the [Black-Litterman 1992](https://doi.org/10.2469/faj.v48.n5.28) Bayesian-shrinkage framework is NOT adopted at this ADR — operator views on per-arm expected returns are out-of-scope; only the realized OOS return series is the input. A future ADR may add Black-Litterman as a fourth weighting scheme if operator-supplied views become a load-bearing input.

## References

- [Markowitz 1952](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) — *J Finance* 7(1):77-91, "Portfolio Selection"; mean-variance frontier.
- [Grinold 1989](https://doi.org/10.3905/jpm.1989.409211) — *J Portfolio Mgmt* 15(3):30-37, "The Fundamental Law of Active Management".
- Grinold-Kahn 1999 — *Active Portfolio Management* 2nd ed. McGraw-Hill, ISBN 978-0070248823, *practitioner*; canonical `IR ≈ IC·√breadth` derivation in Ch. 6.
- [Black-Litterman 1992](https://doi.org/10.2469/faj.v48.n5.28) — *FAJ* 48(5):28-43, "Global Portfolio Optimization"; Bayesian shrinkage toward equilibrium.
- [Ledoit-Wolf 2003](https://doi.org/10.1016/S0927-5398(03)00007-0) — *J Empirical Finance* 10(5):603-621, "Improved estimation of the covariance matrix of stock returns with an application to portfolio selection"; constant-correlation shrinkage target.
- [Ledoit-Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002) — *J Empirical Finance* 15(5):850-859, "Robust performance hypothesis testing with the Sharpe ratio"; differential-Sharpe CI primitive already canonical in the project's inference layer.
- [DeMiguel-Garlappi-Uppal 2009](https://doi.org/10.1093/rfs/hhm075) — *RFS* 22(5):1915-1953, "Optimal Versus Naive Diversification: How Inefficient Is the 1/N Portfolio Strategy?"; load-bearing for the `1/N` default under small-`N` estimation noise.
- [Brandt-Santa-Clara-Valkanov 2009](https://doi.org/10.1093/rfs/hhp003) — *RFS* 22(9):3411-3447, "Parametric Portfolio Policies: Exploiting Characteristics in the Cross-Section of Equity Returns"; parametric portfolio policies for non-Gaussian per-arm returns.
- [ADR-0001](ADR-0001-project-scope.md) — project scope + capacity ceilings (binding at the aggregate meta-portfolio layer).
- [ADR-0011](ADR-0011-production-walkforward-runbook.md) — production-runbook gating (inherited by MPV1 launches).
- [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — KPI-only philosophy + non-loss mandate + NinjaScript terminus (MPV1 inherits all three).
- [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — 9-table canonical results summary (extended to 12-table by ADR-0017; MPV1 KPI report card carries the full extended set).
- [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) — survival-constrained primary inferential vector + K-1..K-8 kill switches (inherited unchanged at the meta-allocator layer).
- [ADR-0018](ADR-0018-mppm-fitness-rho-1-discipline.md) — MPPM(ρ=1) fitness for survival-constrained inner-CV (load-bearing at the meta-layer hyperparameter selection per §5 above).
