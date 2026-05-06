---
hypothesis_id: H055
schema_version: kpi_report_card_v1
version: 0
date: 2026-05-06
git_head: TBD on first KPI emission per `P1-H055-PROD-RUN`
substrate_dataset_checksum: TBD on first KPI emission per `P1-H055-PROD-RUN`
sidecar_scientific_payload_sha256: TBD on first KPI emission per `P1-H055-PROD-RUN`
simulation_log_sha256: TBD on first KPI emission per `P1-H055-PROD-RUN`
simulation_script_sha256: TBD on first KPI emission per `P1-H055-PROD-RUN`
run_id: TBD on first KPI emission per `P1-H055-PROD-RUN`
sizing_convention: intraday_daily_clear  # per ADR-0013 §3.1.1 table
supersedes: null  # v0 is the pre-emission skeleton
superseded_by: null  # null until v1 lands
---

# H055 — KPI Report Card v0 (PRE-EMISSION SKELETON)

<!--
v0 = placeholder pre-emission skeleton per CLAUDE.md §"KPI report card for every strategy".
First-emission v1 will be authored by `P1-H055-PROD-RUN` after the production walk-forward
completes. All TBD fields below resolve at that point. Per ADR-0013 §4.1 non-loss preservation,
this v0 skeleton is preserved verbatim once v1 lands.
-->

- **Hypothesis**: TBD on first KPI emission per `P1-H055-PROD-RUN` (one-line statement to be lifted from design.md §1)
- **Design.md**: [research/01_hypothesis_register/H055/design.md](design.md)
- **Stage**: `exploration-in-progress` (pre-emission)
- **Stage-tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)

## End-of-simulation results summary (per ADR-0014 §3.2; 9 mandatory tables + bottom-line prose)

TBD on first KPI emission per `P1-H055-PROD-RUN`. The 9 tables are a re-presentation of values
already in §"Performance KPIs" + §"Realized OOS + Forward-Projection block" — they MUST NOT
introduce new KPI values; cross-cell numerical agreement enforced at every audit-remediate-loop
R3 verification step per ADR-0014 §3.2.

### Table 1 — P/L (realized OOS, $10K starting capital)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Table 2 — Drawdown (realized + projected)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Table 3 — Sharpe — primary inference (T = SR_v2 per design.md §1; primary CI with excludes-zero column)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Table 4 — Annualised Sharpe (with annualisation-factor declaration)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Table 5 — Win/Loss/Zero counts + win rate W/(W+L+Z)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Table 6 — Forward 1-year projection (Median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%))

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Table 7 — Hansen SPA family p (with mechanical interpretation if M=1 degenerate per ADR-0008)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Table 8 — Other KPIs (best label cfg, n_folds realized/expected, max-DD annotation, cost model, deferred-KPIs status)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Table 9 — Methodological-correctness annotations (one-line dot-separated)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Bottom line

TBD on first KPI emission per `P1-H055-PROD-RUN`. (≤ 8 sentences stating primary inferential
verdict + realized + projected $10K equity outcome + next mandatory stage transition + cross-link
to full report card body.)

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | leakage-canary-pending | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| `bss-{positive,flat,negative}` | bss-pending | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| `reliability-{in-band,out-of-band}` | reliability-pending | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| `repro-log-{complete,incomplete}` | repro-log-pending | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| `dsr-{positive,marginal,negative,n/a}` | dsr-pending | TBD on first KPI emission per `P1-H055-PROD-RUN` |

## Performance KPIs (per ADR-0013 §3 + `rules/quant-project.md` §Reporting)

| KPI | Annotation | Numeric value | CI / details |
|---|---|---|---|
| Sharpe-vs-passive | TBD | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| Sharpe-vs-bench | TBD | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| Sortino | TBD | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| Max-DD ratio | TBD | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| Winrate | numeric only | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| Turnover | numeric only | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| Capacity estimate | numeric only | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| SPA family p | TBD | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| Power-margin | TBD | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| Mediation NIE | n/a (not in H055 scope) | n/a | n/a |
| Mediation NDE | n/a (not in H055 scope) | n/a | n/a |
| Partial-R² | n/a (not in H055 scope) | n/a | n/a |
| Cost-floor | TBD | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |
| CPCV path-Sharpe | TBD | TBD | TBD on first KPI emission per `P1-H055-PROD-RUN` |

## Realized OOS + Forward-Projection block (MANDATORY per ADR-0013 §3.1)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Realized OOS ($10,000 starting capital; OOS-window-start to OOS-window-end)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Forward 1-year projection ($10,000 → 252 sessions ahead; bootstrap from OOS empirical distribution)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

### Forward max-drawdown projection (% of peak)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

## Build / run history

TBD on first KPI emission per `P1-H055-PROD-RUN`.

| Stage | Run ID | Date | Sidecar SHA | Per-stage findings |
|---|---|---|---|---|
| Stage-1 | TBD | TBD | TBD | TBD |
| Stage-2 | TBD | TBD | TBD | TBD |
| Stage-3 | TBD | TBD | TBD | TBD |

## Failure log entries (cross-referenced)

TBD on first KPI emission per `P1-H055-PROD-RUN`.

## Audit-remediate-loop trails

TBD on first KPI emission per `P1-H055-PROD-RUN`.

## Cross-validation methodology (per ADR-0013 §7)

- CPCV configuration: TBD on first KPI emission per `P1-H055-PROD-RUN`
- KS-monotonicity: TBD on first KPI emission per `P1-H055-PROD-RUN`
- Per-path Sharpe distribution moments: TBD on first KPI emission per `P1-H055-PROD-RUN`
- Wall-clock cap respected: TBD on first KPI emission per `P1-H055-PROD-RUN`
- DSR under CPCV path distribution: TBD on first KPI emission per `P1-H055-PROD-RUN`

## Cross-links

- ReproLog: TBD on first KPI emission per `P1-H055-PROD-RUN`
- Sidecar: TBD on first KPI emission per `P1-H055-PROD-RUN`
- Pre-registered design: [design.md](design.md)
- Cross-hypothesis SPA panel: `P1-CROSS-HYPOTHESIS-SPA-PANEL` (when available)

## Versioning

This is v0 — the pre-emission skeleton. v1 will be the first emission per `P1-H055-PROD-RUN`,
authored from this skeleton with all TBD fields resolved. Per ADR-0013 §4.1 non-loss preservation,
this v0 skeleton is preserved verbatim once v1 lands.

## Operator review section (filled at promotion time per ADR-0013 §5.3)

- Operator: TBD on first KPI emission per `P1-H055-PROD-RUN`
- Promotion decision: TBD on first KPI emission per `P1-H055-PROD-RUN`
- Rationale: TBD on first KPI emission per `P1-H055-PROD-RUN`
- Methodological-correctness acknowledgments (if applicable per §2.1): TBD on first KPI emission per `P1-H055-PROD-RUN`
- Cross-link to promotion log: TBD on first KPI emission per `P1-H055-PROD-RUN`
