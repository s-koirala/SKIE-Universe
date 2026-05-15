---
hypothesis_id: H062
schema_version: kpi_report_card_v1
version: 0
date: 2026-05-14
git_head: TBD on first KPI emission per `P1-H062-PROD-RUN`
substrate_dataset_checksum: TBD on first KPI emission per `P1-H062-PROD-RUN` (pinned subset-SHA of post-Phase-O.0 33-partition H062 universe; verified parent `output_frame_sha256 = 1247dc7ebd2252be837b545b1163702fd8d7bb20512dd3b206e69ec7a0cfe959`)
sidecar_scientific_payload_sha256: TBD on first KPI emission per `P1-H062-PROD-RUN`
simulation_log_sha256: TBD on first KPI emission per `P1-H062-PROD-RUN`
simulation_script_sha256: TBD on first KPI emission per `P1-H062-PROD-RUN`
run_id: TBD on first KPI emission per `P1-H062-PROD-RUN`
sizing_convention: intraday_daily_clear  # per ADR-0013 §3.1.1 table
supersedes: null  # v0 is the pre-emission skeleton
superseded_by: null  # null until v1 lands
---

# H062 — KPI Report Card v0 (PRE-EMISSION SKELETON)

<!--
v0 = placeholder pre-emission skeleton per CLAUDE.md §"KPI report card for every strategy".
First-emission v1 will be authored by `P1-H062-PROD-RUN` after the production walk-forward
completes. All TBD fields below resolve at that point. Per ADR-0013 §4.1 non-loss preservation,
this v0 skeleton is preserved verbatim once v1 lands.
-->

- **Hypothesis**: Intraday N-bar Donchian-channel breakout on {ES, NQ, MGC, SIL} at super-Kelly multiplier grid with BOCD decay-detector halt + switching-bandit redirect. Primary inferential test: basket MPPM(ρ=1) > 0 on stationary-bootstrap CI per ADR-0018 D-1. (Final wording lifted from design.md §1 at v1 emission.)
- **Design.md**: [research/01_hypothesis_register/H062/design.md](design.md)
- **Stage**: `exploration-in-progress` (pre-emission)
- **Stage-tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)

## End-of-simulation results summary (per ADR-0014 §3.2 + ADR-0017 §3.2 + ADR-0019 Table 1c; 13 mandatory tables + bottom-line prose)

TBD on first KPI emission per `P1-H062-PROD-RUN`. The 13 tables are a re-presentation of values already in §"Performance KPIs" + §"Realized OOS + Forward-Projection block" — they MUST NOT introduce new KPI values; cross-cell numerical agreement enforced at every audit-remediate-loop R3 verification step per ADR-0014 §3.2.

### Table 1 — P/L (realized OOS, $10K starting capital)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 1c — Payoff-shape diagnostics (per ADR-0019)

TBD on first KPI emission per `P1-H062-PROD-RUN`. L-skewness τ_3 + 95% CI; payoff-shape annotation `skew-{positive,zero,negative}`; barbell-rebalance-candidate flag per ADR-0019 §3.

### Table 2 — Drawdown (realized + projected)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 3 — Sharpe — primary inference (T = MPPM(ρ=1) per design.md §1; primary CI with excludes-zero column)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 3a — Calmar-differential — primary survival inference (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 3b — Profit-factor differential — primary survival inference (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 3c — R-multiple-mean — primary survival inference (per ADR-0017 §3.2)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 4 — Annualised Sharpe (with annualisation-factor declaration)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 5 — Win/Loss/Zero counts + win rate W/(W+L+Z)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 6 — Forward 1-year projection (Median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%))

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 7 — Hansen SPA family p (KPI annotation per ADR-0008; TPE-coverage-conditioned per H055 precedent)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 8 — Other KPIs (best Kelly-multiplier-mode per fold, best channel-N per fold, best k_atr per fold, switching-bandit-algo, BOCD decay-flag, L-skewness, causal-mechanism, super-kelly-operator-discretionary annotation if applicable)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Table 9 — Methodological-correctness annotations (one-line dot-separated)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Bottom line

TBD on first KPI emission per `P1-H062-PROD-RUN`. (≤ 8 sentences stating primary inferential verdict on basket MPPM(ρ=1) + realized + projected $10K equity outcome + next mandatory stage transition + cross-link to full report card body.)

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | leakage-canary-pending | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| `bss-{positive,flat,negative,n/a}` | bss-pending | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| `reliability-{in-band,out-of-band,n/a}` | reliability-pending | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| `repro-log-{complete,incomplete}` | repro-log-pending | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| `dsr-{positive,marginal,negative,n/a}` | dsr-pending | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| `cost-zero-v1-pre-cost-research-only` | cost-zero-v1-pre-cost-research-only | v1 fixed annotation per design.md §6 + operator 2026-05-08 standing directive |
| `super-kelly-operator-discretionary` (if `kelly-multiplier-mode ∈ {1.5, 2.0, 2.5}`) | super-kelly-pending | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| `data-overlap-h050-h052a-h053-h054-h055-h060-acknowledged` | data-overlap-acknowledged | OOS overlap honestly acknowledged per data_requirements.md §"Cross-hypothesis fit-set isolation properties" |
| `is-superset-prior-fits-acknowledged` | is-superset-acknowledged | H062 IS (2020-2023) is SUPERSET of prior hypothesis IS windows; methodologically defensible per H055 + H060 precedent |

## Performance KPIs (per ADR-0013 §3 + ADR-0017 §3 primary + `rules/quant-project.md` §Reporting)

### Primary (per ADR-0017 §3 Pareto-front operator review)

| KPI | Annotation | Numeric value | CI / details |
|---|---|---|---|
| MPPM(ρ=1) basket | TBD | TBD | stationary-bootstrap CI; PRIMARY per ADR-0018 D-1 |
| terminal_wealth_q05 | TBD | TBD | 252-session forward bootstrap projection on $10K |
| Calmar-differential | TBD | TBD | block-stationary-bootstrap CI per [src/skie_ninja/inference/calmar.py](../../../src/skie_ninja/inference/calmar.py) |
| profit-factor differential | TBD | TBD | block-stationary-bootstrap CI per [src/skie_ninja/inference/profit_factor.py](../../../src/skie_ninja/inference/profit_factor.py) |
| R-multiple-mean | TBD | TBD | block-stationary-bootstrap CI per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py); `underpowered` annotation if n<30 |

### Secondary (Sharpe-family preserved as academic-comparability KPI per ADR-0017 §1.2)

| KPI | Annotation | Numeric value | CI / details |
|---|---|---|---|
| Sharpe-vs-passive-BH (basket) | TBD | TBD | LW2008 differential CI |
| Sharpe-vs-AR(1)-lag-1-bench (basket) | TBD | TBD | LW2008 differential CI |
| Per-symbol Sharpe-vs-passive RW2005 stepwise FWER | TBD | TBD | Romano-Wolf 2005 stepwise; M=4 family |
| Hansen 2005 SPA p (per-symbol) | TBD | TBD | KPI annotation per ADR-0008; M=K_max-realized TPE-coverage-conditioned |
| Sortino (per-symbol) | TBD | TBD | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| Max-DD ratio (arm/passive) | TBD | TBD | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| Win-rate (per-symbol) | numeric only | TBD | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| Turnover (per-symbol) | numeric only | TBD | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| Capacity estimate (per-symbol) | numeric only | TBD | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| Power-margin | TBD | TBD | TBD on first KPI emission per `P1-H062-PROD-RUN` |
| Cost-floor | cost-zero-v1-pre-cost-research-only | n/a (v1) | v2 will report 1-tick vs 2-tick sensitivity |
| CPCV path-Sharpe | TBD | TBD | optional v2; v1 uses purged walk-forward only |

### ADR-0018 / ADR-0019 / ADR-0022 annotations

| Annotation | Status | Detail |
|---|---|---|
| `mppm-rho1-{positive,marginal,negative}` | TBD | LOAD-BEARING H_1 inferential annotation per design.md §1 |
| `bocd-decay-flag-{raised,not-raised}` | TBD | BOCD posterior > 0.5 at run-length ≥ 3 folds per design.md §5.4 |
| `kelly-multiplier-mode-{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` | TBD | mode of per-fold-best Kelly multiplier per design.md §5.3 |
| `switching-bandit-algo-{d_ucb, glr_klucb}` | TBD | winner of design.md §5.5 cumulative-regret-minimization competition (R2 F2-005 fix) |
| `l-skewness-{positive,zero,negative}` | TBD | per-trade basket R-multiple distribution; ADR-0019 |
| `causal-mechanism-hybrid` | causal-mechanism-hybrid | per design.md §1.3; channel-break-as-information-event upstream causal + correlation-only refinement on N + k_atr + Kelly-multiplier layers |

## Realized OOS + Forward-Projection block (MANDATORY per ADR-0013 §3.1)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Realized OOS ($10,000 starting capital; OOS-window-start to OOS-window-end)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Forward 1-year projection ($10,000 → 252 sessions ahead; bootstrap from OOS empirical distribution)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

### Forward max-drawdown projection (% of peak)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

## Build / run history

TBD on first KPI emission per `P1-H062-PROD-RUN`.

| Stage | Run ID | Date | Sidecar SHA | Per-stage findings |
|---|---|---|---|---|
| Stage-1 | TBD | TBD | TBD | TBD |
| Stage-2 | TBD | TBD | TBD | TBD |
| Stage-3 | TBD | TBD | TBD | TBD |

## Failure log entries (cross-referenced)

TBD on first KPI emission per `P1-H062-PROD-RUN`.

## Audit-remediate-loop trails

TBD on first KPI emission per `P1-H062-PROD-RUN`.

## Cross-validation methodology (per ADR-0013 §7)

- CPCV configuration: NOT USED at v1 (purged walk-forward only per design.md §5.6); CPCV deferred to potential v2 per `P1-H062-CPCV-V2`.
- KS-monotonicity: n/a at v1.
- Per-path Sharpe distribution moments: n/a at v1.
- Wall-clock cap respected: TBD on first KPI emission per `P1-H062-PROD-RUN`.
- DSR under purged walk-forward path distribution: TBD on first KPI emission per `P1-H062-PROD-RUN`.

## Cross-links

- ReproLog: TBD on first KPI emission per `P1-H062-PROD-RUN`
- Sidecar: TBD on first KPI emission per `P1-H062-PROD-RUN`
- Pre-registered design: [design.md](design.md)
- Data requirements: [data_requirements.md](data_requirements.md)
- Cross-hypothesis SPA panel: `P1-CROSS-HYPOTHESIS-SPA-PANEL` (when available)

## Versioning

This is v0 — the pre-emission skeleton. v1 will be the first emission per `P1-H062-PROD-RUN`, authored from this skeleton with all TBD fields resolved. Per ADR-0013 §4.1 non-loss preservation, this v0 skeleton is preserved verbatim once v1 lands.

## Operator review section (filled at promotion time per ADR-0013 §5.3)

- Operator: TBD on first KPI emission per `P1-H062-PROD-RUN`
- Promotion decision: TBD on first KPI emission per `P1-H062-PROD-RUN`
- Rationale: TBD on first KPI emission per `P1-H062-PROD-RUN`
- Super-kelly operator-discretionary acknowledgment (if applicable per ADR-0018 D-2): TBD on first KPI emission per `P1-H062-PROD-RUN`
- Methodological-correctness acknowledgments (if applicable per ADR-0013 §2.1): TBD on first KPI emission per `P1-H062-PROD-RUN`
- Cross-link to promotion log: TBD on first KPI emission per `P1-H062-PROD-RUN`
