---
hypothesis_id: H{NNN}
schema_version: kpi_report_card_v1
version: {N}
date: YYYY-MM-DD
git_head: {short_sha}
substrate_dataset_checksum: {sha256}
sidecar_scientific_payload_sha256: {sha256}
simulation_log_sha256: {sha256_of_simulate_log}  # per ADR-0013 §3.1 item 5 (F-CONV-8 audit)
simulation_script_sha256: {sha256_of_simulate_script}  # per ADR-0013 §3.1 item 5
run_id: {run_id}
sizing_convention: intraday_daily_clear  # per ADR-0013 §3.1.1 table
supersedes: v{N-1}  # null for v1
superseded_by: null  # null until a successor lands
---

# H{NNN} — KPI Report Card v{N}

<!--
INSTRUCTION (template guidance; NOT rendered in production cards):
If ANY arm of this strategy has `leakage-canary-fail` OR `repro-log-incomplete`,
INSERT the following visible callout block IMMEDIATELY after the H1 above
(per ADR-0013 §2.1 + Round-2 audit F-2-3 remediation; the callout MUST be
rendered visible, NOT wrapped in HTML comments):

> [!CAUTION]
> **METHODOLOGICAL-CORRECTNESS-VIOLATION**
> Detected: {comma-separated list: e.g., `leakage-canary-fail` (feature factory: X), `repro-log-incomplete` (missing: Y), `post-run-audit-fail` (sidecar mismatch)}
> Implication: ALL reported KPIs below are UPPER BOUNDS. Operator promotion past `kpi-report-emitted` requires a written acknowledgment in `logs/promotions/{run_id}_H{NNN}_{arm_id}_promotion.md`.

If NO methodological-correctness violations: omit the callout entirely.
Then DELETE this HTML-comment instruction block before committing the card.
-->


- **Hypothesis**: {one-line statement from design.md §1}
- **Design.md**: [research/01_hypothesis_register/H{NNN}/design.md](design.md)
- **Stage**: {stage from stage.md}
- **Stage-tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | {} | feature factories audited: {list}; canary paths: {list} |
| `bss-{positive,flat,negative}` | {} | BSS = {value}; per-instrument climatological prior on OOS fold |
| `reliability-{in-band,out-of-band}` | {} | slope = {value}; band [0.7, 1.3] is project-operational per `P1-RELIABILITY-SLOPE-EMPIRICAL-CALIBRATION` |
| `repro-log-{complete,incomplete}` | {} | missing fields: {list or none} |
| `dsr-{positive,marginal,negative,n/a}` | {} | family size at evaluation: {n}; activation_size: {threshold} |

## Performance KPIs (per ADR-0013 §3 + `rules/quant-project.md` §Reporting)

| KPI | Annotation | Numeric value | CI / details |
|---|---|---|---|
| Sharpe-vs-passive | `{positive,marginal,flat,negative}` | ΔSR = {value} | CI: [{lo}, {hi}] (Lo 2002 / Opdyke 2007 / Ledoit-Wolf 2008) |
| Sharpe-vs-bench | `{positive,marginal,flat,negative}` | ΔSR = {value} | CI: [{lo}, {hi}] |
| Sortino | `{positive,marginal,flat,negative}` | Sortino ratio = {value} | downside-deviation per Sortino & Price 1994 |
| Max-DD ratio | `{favorable,comparable,adverse}` | arm/passive = {value} | |
| Winrate | numeric only | W/L/Z = {w}/{l}/{z}; **win rate = W/(W+L+Z)** = {win_rate} | per-session count + project-canonical W/(W+L+Z) winrate (see ADR-0013 §3.1 item 1; report all three counts so readers can re-compute under W/(W+L)) |
| Turnover | numeric only | per-day = {value} | |
| Capacity estimate | numeric only | contracts-per-bar = {value} OR USD/day = {value} | retail-size ceiling per CLAUDE.md §Standing constraints |
| SPA family p | `{passes,rejects}` | p = {value} | omega-corrected per ADR-0008 |
| Power-margin | `{adequate,marginal,low}` | realized n / n_required_for_power_80 = {ratio} | |
| Mediation NIE | `{significant,flat}` | NIE = {value} | CI: [{lo}, {hi}] (if applicable) |
| Mediation NDE | `{significant,flat}` | NDE = {value} | CI: [{lo}, {hi}] (if applicable) |
| Partial-R² | `{positive,flat}` | R² = {value} | (if applicable) |
| Cost-floor | `{robust,conditional,flat}` | 1-tick: {value}; 2-tick: {value} | NT8-realistic fill assumptions |
| CPCV path-Sharpe | `{converged,not-converged}` | KS distance = {value} | n_paths = {value}; AFML §12.5 |

## Realized OOS + Forward-Projection block (MANDATORY per ADR-0013 §3.1)

**Caveats** (annotate explicitly):
- Cost model applied: yes / no (cost-free is upper bound; cost-aware variant tracked under `P1-{HID}-COST-EMPIRICAL`)
- Position-sizing convention: 100%-of-equity per session, no leverage, daily clearing (`equity_{t+1} = equity_t × exp(r_t)`)
- Bootstrap-as-generative-model: forward distribution assumes 2026 mirrors OOS distribution
- Cross-reference to Sharpe-vs-passive CI from §"Performance KPIs" above (if CI covers zero, P(loss) value must surface this)

### Realized OOS ($10,000 starting capital; OOS-window-start to OOS-window-end)

| Symbol | Arm | Realized-path Sharpe† | Realized end | % change | Realized max-DD | W/L/Z | Win rate (W/(W+L+Z)) |
|---|---|---:|---:|---:|---:|---:|---:|
| {sym} | {arm_id} | {sharpe} | ${end_eq} | {pct}% | {dd}% | {w}/{l}/{z} | {wr}% |

† **Realized-path Sharpe** = single-OOS-trajectory annualised mean/std × √252 of strategy log returns. Per ADR-0013 §3.1 item 1 + F-CONV-1 audit: this is **NOT** the same statistic as the canonical CPCV path-Sharpe distribution median in §"Performance KPIs / Sharpe-vs-passive" above (which is the median of 45 per-fold Sharpes). Both are reported; do NOT compare them as if equivalent.

### Forward 1-year projection ($10,000 → 252 sessions ahead; bootstrap from OOS empirical distribution)

| Symbol | Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| {sym} | {arm_id} | ${med} | ${mean} | ${q01} | ${q05} | ${q95} | ${q99} | {p_loss}% | {p_double}% | {p_ruin50}% |

q01/q99 columns are MANDATORY (per F-CONV-7 audit) so the operator can read the actual distribution shape when P(double) and P(<50%) degenerate to 0% (typical for low-volatility daily-cleared intraday strategies at 252 sessions).

### Forward max-drawdown projection (% of peak)

| Symbol | Arm | Median DD | Mean DD | q05 | q95 |
|---|---|---:|---:|---:|---:|
| {sym} | {arm_id} | {med}% | {mean}% | {q05}% | {q95}% |

Bootstrap configuration: n_paths={5000} × n_sessions={252}; rng_seed=_STAGE3_RNG_SEED+1000=1042 (single seed across all arms per F-CONV-4 audit; per-arm RNG offsets are FORBIDDEN). Sampling: **per-arm Politis-White 2004 block-length selection on each arm's strategy-log-return level series** (not the strategy-minus-bench differential). When PW2004 selects block_length = 1.0 the iid bootstrap is appropriate; otherwise Politis-Romano 1994 stationary bootstrap with the PW2004-selected block length per arm. Selected block lengths recorded in the sidecar per arm. (Per F-CONV-3 audit: borrowing the LW2008 differential's block_length is NOT acceptable justification.)

Reference implementation: [scripts/simulate_h053_v4_10k_2026.py](../../scripts/simulate_h053_v4_10k_2026.py). Common forward-projection helpers tracked under `P1-FORWARD-PROJECTION-PRIMITIVE` (see ADR-0013 §3.1 for the tightened scope contract).

## Build / run history

Per ADR-0013 §3, full per-stage execution record:

| Stage | Run ID | Date | Sidecar SHA | Per-stage findings |
|---|---|---|---|---|
| Stage-1 | {run_id} | YYYY-MM-DD | {sha} | {findings} |
| Stage-2 | {run_id} | YYYY-MM-DD | {sha} | {findings} |
| Stage-3 | {run_id} | YYYY-MM-DD | {sha} | {findings} |

## Failure log entries (cross-referenced)

| Entry ID | Date | Category | Resolution |
|---|---|---|---|
| {n} | YYYY-MM-DD | {category} | commit {sha} |

## Audit-remediate-loop trails

| Round | Trail path | Verdict | Findings |
|---|---|---|---|
| 1 | docs/audits/audit_trail_YYYY-MM-DD_{topic}.md | {accept/accept-with-residuals/block} | {summary} |

## Cross-validation methodology (per ADR-0013 §7)

- CPCV configuration: n_groups = {n}, n_test_groups = {k}, n_paths = C(n,k) = {paths}
- KS-monotonicity: {converged / not-converged at threshold 0.05 by 30 paths}
- Per-path Sharpe distribution moments: mean = {value}, std = {value}, q05 = {value}, q95 = {value}, median = {value}
- Wall-clock cap respected: {yes / no — downsampled to n_groups=8}
- DSR under CPCV path distribution: {value}

## Cross-links

- ReproLog: [logs/reproducibility/{run_id}.json](../../../logs/reproducibility/{run_id}.json)
- Sidecar: [artifacts/runs/H{NNN}/{run_id}/sidecar.json](../../../artifacts/runs/H{NNN}/{run_id}/sidecar.json)
- Pre-registered design: [design.md](design.md)
- Cross-hypothesis SPA panel: `P1-CROSS-HYPOTHESIS-SPA-PANEL` (when available)

## Versioning

This is v{N}. Prior versions:
- v{N-1}: [{HID}_kpi_report_v{N-1}.md]({HID}_kpi_report_v{N-1}.md) (preserved verbatim per ADR-0013 §4.1)

A version increment is triggered by substantive changes (numeric values, qualitative annotations, methodological-correctness banner, build/run history). Cosmetic edits (typo, formatting) are permitted in-place.

## Operator review section (filled at promotion time per ADR-0013 §5.3)

- Operator: {name}
- Promotion decision: {promote / defer / pull / retire}
- Rationale: {≥ 1 sentence per KPI section above}
- Methodological-correctness acknowledgments (if applicable per §2.1): {explicit acknowledgment of leakage / repro-incomplete; "all KPIs above are upper bounds"}
- Cross-link to promotion log: [logs/promotions/{run_id}_H{NNN}_{arm_id}_promotion.md](../../../logs/promotions/{run_id}_H{NNN}_{arm_id}_promotion.md)
