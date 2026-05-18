<!--
KPI Results Summary Template (companion to research/_templates/kpi_report_card_template.md).

Per [ADR-0014 §3.2](../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md),
every KPI report card MUST include this 13-table + bottom-line summary section
between the H1 / hypothesis preamble and §"Methodological-correctness annotations".

Format-version history:
- v1 (2026-05-04 effective): 9-table format per ADR-0014 §3.2 original.
- v2 (2026-05-08 effective): 12-table format per [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3.2 amendment;
  added Tables 3a (terminal-wealth-q05), 3b (Calmar-differential), 3c (profit-factor + R-multiple-mean).
- v3 (2026-05-12 effective): 13-table format per [ADR-0019](../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) §3 amendment;
  added Table 1c (Payoff-shape diagnostics: L-skewness τ_3 per [Hosking 1990 JRSS B 52(1):105-124](https://www.jstor.org/stable/2345653)).
- v3.1 (2026-05-15 effective): 13-table format clarified per [ADR-0024](../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md);
  MPPM(ρ=1) per [ADR-0018](../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1 may replace Sharpe as Table 3 PRIMARY
  inferential anchor (operator-discretionary; depends on hypothesis pre-registered design.md §1).

The section is a re-presentation of values already in the report card's
§"Performance KPIs" mega-table + §3.1 Realized-OOS + Forward-Projection block.
It MUST NOT introduce new KPI numeric values or annotations; cross-cell
numerical agreement is enforced by the post-run audit gate per ADR-0013 §7.1.

This file can also be used standalone for status reports between full
report card emissions (e.g., mid-cycle progress updates).

Substitute {placeholders}; remove this HTML comment before commit.
-->

## End-of-simulation results summary (per [ADR-0014 §3.2](../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md))

H{NNN} {phase descriptor; e.g., "production walk-forward", "Stage-3 v4", "Cycle 6 Phase-A"} (run_id `{run_id}`; commit `{git_head}`; {wall_clock_summary}; substrate `{dataset_checksum_first16}...` {substrate_window}; {cost_application_status}):

### 1. P/L (realized OOS, $10K starting capital, {sizing_convention} per ADR-0013 §3.1.1)

| Symbol | Arm | End equity | % change | OOS bars | OOS sessions (eq) |
|---|---|---:|---:|---:|---:|
| {sym} | {arm_id} | ${end_eq} | {pct}% | {n_bars} | ~{n_sessions} |

### 1c. Payoff-shape diagnostics (per [ADR-0019](../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) §3; effective 2026-05-12)

| Symbol | Arm | τ_3 (L-skewness) | CI low | CI high | Annotation |
|---|---|---:|---:|---:|---|
| {sym} | {arm_id} | {tau_3} | {ci_lo} | {ci_hi} | `payoff-shape-skew-{positive,flat,negative}` |

L-skewness τ_3 per [Hosking 1990 *JRSS B* 52(1):105-124 JSTOR 2345653](https://www.jstor.org/stable/2345653) on per-trade R-multiple distribution; CI via stationary-bootstrap. Cutoff ±0.1 per ADR-0019 §3 project-operational threshold (NOT in Hosking 1990 primary text; empirical calibration tracked under `P1-ADR-0019-PAYOFF-SHAPE-THRESHOLD-EMPIRICAL`). `skew-positive` = barbell-rebalance-candidate; `skew-negative` = death-by-thousand-cuts payoff structure.

### 2. Drawdown (realized + projected)

| Symbol | Arm | Realized max-DD | Proj median DD | Proj q95 DD |
|---|---|---:|---:|---:|
| {sym} | {arm_id} | {realized_dd}% | {proj_med_dd}% | {proj_q95_dd}% |

({optional caveat: bar-level iid bootstrap UNDERSTATES regime-conditional risk per F-Q-3 caveat — applicable to bar-cadence substrates per ADR-0013 §3.1.1 sizing-convention table})

### 3. Primary inference — Sharpe-differential OR MPPM(ρ=1) per design.md §1

Per [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §1.2 + [ADR-0018](../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1 + [ADR-0024](../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md), MPPM(ρ=1) may replace Sharpe-differential as Table 3 PRIMARY anchor when the hypothesis's design.md §1 declares MPPM-primary. Sharpe-family CIs are then reported as SECONDARY KPI annotations.

**Sharpe-differential variant** (T = SR_{arm} − SR_{benchmark}):

| Symbol | SR_arm | SR_bench | T_primary | {Primary CI method (LW2008 / Lo 2002 / Opdyke 2007 / etc.)} CI [low, high] | excludes zero | T annualised |
|---|---:|---:|---:|---|:---:|---:|
| {sym} | {sr_arm} | {sr_bench} | {t} | [{lo}, {hi}] | {YES/NO} | {t_ann} |

**MPPM(ρ=1) variant** (per [GISW 2007 *RFS* 20(5):1503-1546 DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025); annualised log-wealth growth rate; ρ=1 reduces to Kelly fitness via L'Hôpital):

| Symbol | Arm | MPPM(ρ=1) | Stationary-bootstrap CI [low, high] | excludes zero | Annotation |
|---|---|---:|---|:---:|---|
| {sym} | {arm_id} | {mppm} | [{lo}, {hi}] | {YES/NO} | `mppm-rho1-{positive,marginal,negative,underpowered}` |

**{Primary inferential verdict in one sentence}**

### 3a. Terminal-wealth q05 (per [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3.2; effective 2026-05-08)

| Symbol | Arm | Terminal-wealth q05 (1-yr projection) | Annotation |
|---|---|---:|---|
| {sym} | {arm_id} | ${tw_q05} | `tw-q05-{above-half,above-zero,below-zero}` |

Per-arm Politis-White 2004 block-length stationary bootstrap on per-session strategy log-return level series; n_paths=5,000; per ADR-0013 §3.1.

### 3b. Calmar-differential (per [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3.2; effective 2026-05-08)

| Symbol | Calmar_arm | Calmar_bench | Calmar-diff | Bootstrap CI [low, high] | Annotation |
|---|---:|---:|---:|---|---|
| {sym} | {c_arm} | {c_bench} | {c_diff} | [{lo}, {hi}] | `calmar-diff-{positive,marginal,negative}` |

Block-stationary-bootstrap CI per [Politis-Romano 1994 *JASA* 89(428):1303-1313 DOI 10.1080/01621459.1994.10476870](https://doi.org/10.1080/01621459.1994.10476870); 1,000 replicates; primitive at `src/skie_ninja/inference/calmar.py`.

### 3c. Profit-factor + R-multiple-mean (per [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §3.2; effective 2026-05-08)

| Symbol | Arm | PF_arm | PF_bench | PF-diff | PF-diff CI [low, high] | R-multiple-mean | R-mult-mean CI [low, high] | Annotations |
|---|---|---:|---:|---:|---|---:|---|---|
| {sym} | {arm_id} | {pf_arm} | {pf_bench} | {pf_diff} | [{lo}, {hi}] | {r_mean} | [{r_lo}, {r_hi}] | `pf-diff-{positive,marginal,negative}` · `r-multiple-mean-{positive,marginal,negative}` |

Supplementary thresholds (Tharp 1998 *practitioner*; ISBN-13 978-0070647626): PF ≥ 1.5 is a practitioner-canonical adequacy floor; r-multiple-mean ≥ +0.5 is the operator-conservative-positive-edge floor.

| Symbol | SR_arm | SR_bench | T_primary | {Primary CI method (LW2008 / Lo 2002 / Opdyke 2007 / etc.)} CI [low, high] | excludes zero | T annualised |
|---|---:|---:|---:|---|:---:|---:|
| {sym} | {sr_arm} | {sr_bench} | {t} | [{lo}, {hi}] | {YES/NO} | {t_ann} |

**{Primary inferential verdict in one sentence}**

### 4. Annualised Sharpe (×{annualisation_factor})

| Symbol | SR_arm1 | SR_arm2 | ... |
|---:|---:|---:|---|
| {sym} | {sr_arm1} | {sr_arm2} | ... |

(One column per arm declared in the hypothesis's design.md §5; annotate the bench column only if the hypothesis carries a passive/AR(1) bench distinct from the primary differential's reference arm. Per ADR-0014 §3.2 Table 4 spec: column-shape is `symbol | SR_arm (one per arm) [| SR_bench if applicable]`. Annualisation factor justification: per-bar substrates use √(252 × {bars_per_session}); per-session substrates use √252. {Lo 2002 correction status}.)

### 5. Win/Loss/Zero bar (or session) counts + win rate

| Symbol | Arm | W | L | Z | Win rate W/(W+L+Z) |
|---|---|---:|---:|---:|---:|
| {sym} | {arm_id} | {w} | {l} | {z} | {win_rate}% |

### 6. Forward 1-year projection ($10K → {n_bars_or_sessions}; {sampling_method} via PW2004 selected b={block_length}; n_paths=5,000; rng_seed={rng_seed})

| Symbol | Arm | Median | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| {sym} | {arm_id} | ${med} | ${q01} | ${q05} | ${q95} | ${q99} | {p_loss}% | {p_double}% | {p_ruin50}% |

### 7. Hansen SPA family p-value

| Symbol | T_SPA | p | n_bootstrap | Annotation |
|---|---:|---:|---:|---|
| {sym} | {t_spa} | {p} | {n_b} | `spa-{passes,rejects}` ({mechanism explanation if degenerate, per ADR-0008 single-strategy convention if M=1}) |

### 8. Other KPIs

| KPI | {sym1} | {sym2} | ... |
|---|---|---|---|
| Best label cfg | {cfg_sym1} | {cfg_sym2} | ... |
| n_folds (realized/expected) | {n/exp} → `power-margin-{adequate,marginal,low}` | ... | ... |
| max-DD annotation | `max-dd-{favorable,comparable,adverse}` | ... | ... |
| Sharpe-vs-{benchmark} annotation | `sharpe-vs-{benchmark}-{positive,marginal,flat,negative}` | ... | ... |
| Cost model | `{cost_model_id}` ({applied/not applied}, {prior_status}) | ... | ... |
| Sortino / turnover / capacity | {computed_or_deferred} | ... | ... |

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2 + §2.1)

`leakage-canary-{pass,fail}` · `bss-{positive,flat,negative,n/a}` · `reliability-{in-band,out-of-band,n/a}` · `repro-log-{complete,incomplete}` · `dsr-{positive,marginal,negative,n/a}` · `post-run-audit-{pass,fail}`

{If any annotation is `fail` or `incomplete`: insert the §2.1 visible callout banner.}

### Bottom line

{≤ 8 sentences. State:
1. Primary inferential verdict (positive / null / negative) per the binding test statistic from design.md §1.
2. Realized + projected $10K equity outcome in operator-readable phrasing.
3. Next mandatory stage transition per ADR-0013 §1 + §5.
4. Cross-link to the full report card body (the 9 tables are a SUMMARY; the body retains the canonical detailed presentation per ADR-0013 §3 + §3.1).}

Full report card: [research/01_hypothesis_register/H{NNN}/H{NNN}_kpi_report_v{N}.md](../../research/01_hypothesis_register/H{NNN}/H{NNN}_kpi_report_v{N}.md). Sim output: [logs/simulate_H{NNN}_10k_2026.json](../../logs/simulate_H{NNN}_10k_2026.json).
