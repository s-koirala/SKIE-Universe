<!--
KPI Results Summary Template (companion to research/_templates/kpi_report_card_template.md).

Per [ADR-0014 §3.2](../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md),
every KPI report card MUST include this 9-table + bottom-line summary section
between the H1 / hypothesis preamble and §"Methodological-correctness annotations".

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

### 2. Drawdown (realized + projected)

| Symbol | Arm | Realized max-DD | Proj median DD | Proj q95 DD |
|---|---|---:|---:|---:|
| {sym} | {arm_id} | {realized_dd}% | {proj_med_dd}% | {proj_q95_dd}% |

({optional caveat: bar-level iid bootstrap UNDERSTATES regime-conditional risk per F-Q-3 caveat — applicable to bar-cadence substrates per ADR-0013 §3.1.1 sizing-convention table})

### 3. Sharpe — primary inference (T = SR_{arm} − SR_{benchmark} per design.md §1)

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
