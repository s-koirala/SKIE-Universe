# KPI Report Cards — Results Index

Every emitted KPI report card across all hypotheses. Per [ADR-0013](../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1, when a new version supersedes an existing version both versions are preserved verbatim — the index lists every version, not only the latest. Per [ADR-0014](../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), each report card carries the mandatory 9-table results summary; per [ADR-0013](../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3.1 every card emitted from 2026-05-03 forward also carries the Realized-OOS + Forward-Projection block.

## Reading the table

Each row reports the headline result at the time of report emission. Specific cell values and methodology annotations live in the report card itself. Sharpe-family numbers are reported for academic comparability per [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §1.2 but are no longer the primary inferential anchor — the load-bearing metrics for hypotheses from H055 forward are terminal-wealth-q05, Calmar-differential, profit-factor, and R-multiple-mean.

## Index

| Hypothesis | Version | Date | Report card | Run ID | Headline T_H (primary CI) | Realized OOS (gated/primary arm) | Forward 252-session P(loss) | Methodological annotations |
|---|---|---|---|---|---|---|---|---|
| H050 | v1 | 2026-05-04 | [H050_kpi_report_v1.md](H050/H050_kpi_report_v1.md) | `31d23ec...` | ES T_H050 = −0.0371 [−0.0405, −0.0339]; NQ T_H050 = −0.0219 [−0.0245, −0.0190] (LW2008; excludes zero on **negative** side both symbols) | ES −81%, NQ −84% (catastrophic) | 100% on both gated arms; ~100% on both unconditional arms | `leakage-canary-pass`, `bss-n/a`, `reliability-n/a`, `repro-log-complete`, `dsr-n/a (M=1)`, `post-run-audit-pass`, `sharpe-vs-unconditional-negative`, `max-dd-adverse` |
| H052a | v1 | 2026-05-05 | [H052a_kpi_report_v1.md](H052a/H052a_kpi_report_v1.md) | `184eccd...` | ES T_H052a = −0.0184 [−0.0676, +0.0260]; NQ T_H052a = −0.0342 [−0.1232, +0.0033] (LW2008; covers zero both symbols → non-significant null) | Gated ES −0.94%, NQ +3.39%; **NQ unconditional +10.61%** (literature-replication artifact, not hypothesis-of-record) | Gated ES 54.84%, NQ 37.12%; uncond ES 42.94%, **NQ 18.56%** | All methodological-correctness annotations green or n/a; operator-declined-ninjascript progression per 2026-05-04 standing directive |
| H053 | v1 | 2026-05-03 | [H053_kpi_report_v1.md](H053/H053_kpi_report_v1.md) | (retroactive re-tag of v2 lineage) | Sharpe-vs-passive uniformly marginal across 4 arms × 2 symbols | (pre-Path-B; superseded) | (pre-Path-B; superseded) | (retroactive re-tag per ADR-0013 §"Retroactive re-tag") |
| H053 | v2 | 2026-05-03 | [H053_kpi_report_v2.md](H053/H053_kpi_report_v2.md) | `fe05138...` | Path B leakage-clean (Stage-3 v4 sidecar 4d5a826b); 4 arms × 2 symbols; medians +0.21 to +1.71 ann. Sharpe; all CIs cover zero | (numerical table in card §"End-of-simulation results summary") | (per-arm in card) | `leakage-canary-pass`, all green or n/a |
| H053 | v3 | 2026-05-03 | [H053_kpi_report_v3.md](H053/H053_kpi_report_v3.md) | `fe05138...` | v2 + mandatory Realized-OOS + Forward-Projection block per ADR-0013 §3.1 amendment | **NQ LightGBM +10.8%** (max-DD 3.7%); ES LightGBM +6.4%; ES ElasticNet weakest forward projection | NQ LGBM 15%; ES ElasticNet 69% | v2 annotations + forward-projection metadata fields |
| H054 | v1 | 2026-05-05 | [H054_kpi_report_v1.md](H054/H054_kpi_report_v1.md) | `dd916fc...` | T_H054_b (primary, Opdyke 2007): SR_anti_gated = +0.0362 [−0.0327, +0.1050]; T_H054_a (secondary, LW2008): SR_anti_gated − SR_uncond = +0.0398 [−0.0411, +0.1394]; **both CIs cover zero** | Anti-gated **+3.50%**, uncond −0.54% on ES OOS (237 sessions; anti-gate fires 7/237 = 2.95%) | Anti-gated 29.24%, uncond 52.50% | All methodological-correctness annotations green or n/a; non-significant null but **point-positive and directionally consistent** |
| H055 | v0 (skeleton) | 2026-05-06 | [H055_kpi_report_v0.md](H055/H055_kpi_report_v0.md) | — (pre-emission) | (TBD per `P1-H055-PROD-RUN`) | (TBD) | (TBD) | Skeleton only; numeric fields populated at `kpi-report-emitted` transition |

## What's in a KPI report card

Per [ADR-0014 §3.2](../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), every KPI report card from 2026-05-04 forward carries a 9-table mandatory results summary between the H1 / hypothesis preamble and §"Methodological-correctness annotations":

1. P/L (realized OOS, $10K starting capital)
2. Drawdown (realized + projected)
3. Sharpe — primary inference (T = SR_arm − SR_bench)
4. Annualised Sharpe (with annualisation-factor declaration)
5. Win/Loss/Zero counts + win rate
6. Forward 1-year projection (median + q01/q05/q95/q99 + P(loss)/P(double)/P(<50%))
7. Hansen SPA family p
8. Other KPIs (best label cfg, n_folds realized/expected, max-DD annotation, cost model, deferred-KPIs status)
9. Methodological-correctness annotations (one-line dot-separated)

Plus a §"Bottom line" prose paragraph (≤ 8 sentences).

Per [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3.2 (in force for KPI report cards from 2026-05-08 forward), the 9 tables are extended to 12 with new mandatory tables 3a (terminal-wealth-q05), 3b (Calmar-differential), 3c (profit-factor + R-multiple-mean).

## See also

- [INDEX.md](INDEX.md) — per-hypothesis stage dashboard
- [hypothesis_backlog.md](../../hypothesis_backlog.md) — project-canonical hypothesis register
- [docs/glossary.md](../../docs/glossary.md) — KPI annotation grammar + lifecycle terms
- Forward-projection reference implementations: [scripts/simulate_h053_v4_10k_2026.py](../../scripts/simulate_h053_v4_10k_2026.py), [scripts/simulate_h050_v1_10k_2026.py](../../scripts/simulate_h050_v1_10k_2026.py)
