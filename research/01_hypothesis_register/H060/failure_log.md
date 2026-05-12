# H060 failure log

Append-only per ADR-0013 §4.1. Each entry records external kills, build defects, run failures, operator overrides.

## Entry 1 — 2026-05-12 — Initial orchestrator build-defect chain (R1 self-remediated)

**Trigger**: First end-to-end run of [scripts/run_h060_walk_forward.py](../../../scripts/run_h060_walk_forward.py).

**Findings (build defects, all self-remediated in-script)**:
- F-1: `MPPMResult` attribute mismatch — used `point_estimate` instead of canonical `theta_hat`. Fixed.
- F-2: `CalmarDifferentialCI` / `ProfitFactorDifferentialCI` / `RMultipleMeanCI` use `ci_lower` / `ci_upper` (not `ci_low` / `ci_high`). Fixed.
- F-3: `DifferentialCIResult` (LW2008) uses `lower` / `upper` (not `ci_low` / `ci_high`). Fixed.
- F-4: `HansenSPAResult` uses `statistic` and `p_value` directly (not `t_spa` / `p_value_consistent`). Fixed.
- F-5: BOCD `detect_decay` returns `{decay_detected, detection_index, max_posterior, posterior_series}` (not `n_changepoints`). Fixed.
- F-6: `_equity_curve` passed equity-curve array to `max_drawdown_fraction` which expects log-returns; produced NaN max-DD on the first clean run. Fixed by passing log_returns directly.

All 6 build defects were API-mismatch surface; the underlying walk-forward + inner-CV + bootstrap logic produced clean numerics from first execution.

## Entry 2 — 2026-05-12 — Risk-of-ruin Monte Carlo model-domain mismatch (escalated to new follow-up)

**Trigger**: §8 KPI table showed P(ruin) = 0.999 (4995/5000 paths ruined) under quarter-Kelly cap on per-session R-multiples.

**Diagnosis**: The daily-cadence vol-scaled-basket per-session R-multiple has no discrete 1R-stop semantics; the R-multiple was computed as `basket_log_return / (vol_target / sqrt(252))` per design.md §3 vol-scaling convention. The Vince-f Kelly bet sizing in `probability_of_ruin_monte_carlo` interprets this as a sequence of 1R-stop bets — a model-domain mismatch.

**Disposition**: P(ruin)=0.999 figure flagged in the KPI report card as NOT a load-bearing operational result. The forward-projection §6 P(loss)=26.6% / P(<50%)=0% is the actually-relevant downside-survival metric.

**Follow-up**: `P1-H060-ROR-1R-STOP-SEMANTICS-RECONCILE` registered to amend the §8 KPI row to compute RoR from forward-projected equity distribution (§6) rather than Vince-f sizing on per-session R-multiples.
