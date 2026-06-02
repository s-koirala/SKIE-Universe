---
id: ADR-0017
title: Survival-constrained optimization paradigm — profit-and-drawdown-primary inference, Sharpe demoted to KPI
status: accepted
date: 2026-05-08
deciders: skoir
supersedes:
  - (none — Sharpe ratio was the *de facto* primary inferential anchor across H050/H052a/H053/H054 §1 statements; ADR-0017 reframes the project's optimization-and-promotion paradigm without deleting any frozen §1 statement)
amends:
  - ADR-0014 §3.2 9-table results-summary → 12-table format extension (new mandatory tables 3a/3b/3c added between Tables 3 and 4 for terminal-wealth-q05, Calmar-differential, R-multiple distribution; existing Tables 1-9 retain their indices for downstream cross-link compatibility per F-10 audit remediation)
  - ADR-0013 §3 KPI report card canonical structure — primary inferential vector at the §3-layer reframed to the survival-constrained metric vector; the §3-layer demotion of Sharpe-family is the SCOPE of this amendment (the design.md §1 H_1 statements are NOT amended; see §1.2 below)
  - CLAUDE.md §"KPI report card for every strategy" — primary objective vector amended to (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean); Sharpe-family demoted to KPI annotation
  - CLAUDE.md §"Standing constraints" — adds the 8 hard kill-switch constraints from §5 below as project-wide mandatory inheritance for every hypothesis from H055 forward
  - research/01_hypothesis_register/H055/design.md §11.1 — kill-switch parameter list expanded per §5 below; §17 amendment ledger entry per Path A (§1-§7 NOT amended; preserved verbatim per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability)
  - All hypothesis design.md §8 + §10 (project-wide; deferred cascade per `P1-ADR-0017-DESIGN-MD-CASCADE` BLOCKING-BEFORE-NEXT-STAGE-3-RUN per the ADR-0013 §"Frozen pre-registration amendment" §1-§4 amendment discipline that is preserved by this ADR)
preserves_immutability_of:
  - All hypothesis design.md §1 (statement) through §7 (cost model) — per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline; this ADR is a §8+§10 amendment only (the primary inferential vector is reframed at the project-level KPI report card layer; the pre-registered T_H statistic in each frozen §1 is preserved as a *secondary KPI* and remains computable verbatim)
  - All historical audit trails, ReproLogs, sidecars, KPI report cards, promotion logs, NinjaScript strategies, and pilot ledger artifacts (per ADR-0013 §4.1 non-loss mandate)
  - ADR-0013 §1 stage-progression model + §4 non-loss mandate + §5 NinjaScript-terminus mandate (all preserved unchanged)
  - ADR-0014 §3.2 9-table format (preserved in structure; the contents of Tables 3 + 4 are reframed at the inferential-load-bearing layer, but the tables themselves remain mandatory at the canonical position)
---

# ADR-0017 — Survival-constrained optimization: profit-and-drawdown-primary inference

## Context

The SKIE-Universe project's existing inferential paradigm under [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) + [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) anchors hypothesis-of-record `T_H` statistics on Sharpe-differentials (`SR_arm − SR_bench`) with [Ledoit-Wolf 2008 *J Empirical Finance* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap CI as the load-bearing inferential criterion. Three empirical observations precipitated this ADR:

### Empirical observation 1 — H050 Sharpe-test correctly captured catastrophic outcome

H050 KPI report card v1 (commit `244eea8`, 2026-05-04) emitted `T_H050 < 0` with LW2008 CI excluding zero on the negative side on both ES + NQ. Realized $10K-baseline OOS equity: -81.0% (ES gated) and -84.2% (NQ gated). Forward 252-session bootstrap projection: P(loss) = 100% on both gated arms. **The Sharpe-test correctly flagged the H050 catastrophe.** This is the case where Sharpe-primary works.

### Empirical observation 2 — H052a + H053 Sharpe-test missed substantively profitable cells

[H052a KPI report card v1](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md) (commit `c16b1ab`, 2026-05-05): T_H052a CIs cover zero on both symbols (non-significant null). But the strongest cell — NQ unconditional ORB — produced realized OOS +10.61% with P(loss) = 18.56% in the forward projection. The Sharpe-test labeled it "non-significant null"; the realized economic outcome was substantively positive.

[H053 KPI report card v3](../../research/01_hypothesis_register/H053/H053_kpi_report_v3.md) (commit `bab405e`, 2026-05-03): all 4 arms × 2 symbols showed `marginal` on both Sharpe-vs-passive and Sharpe-vs-bench (CIs covered zero). But realized OOS for NQ LightGBM was +10.8% with max-DD 3.7%. A strategy with positive realized P/L and reasonable drawdown was statistically labeled "marginal" because its Sharpe-CI covered zero.

The pattern: **Sharpe-differential CIs are systematically tighter around zero than profit-and-drawdown reality**, leading to false-negative dispositions in the operator-economic sense.

### Empirical observation 3 — Operator pilot ledger documents the dual failure modes

The [data/external/h055_pilot_ledger/](../../data/external/h055_pilot_ledger/) ledger spanning 2026-05-01 → 2026-05-07 (226 trades from a $2,000 starting principal that reached $9,421 max-equity then drew down to ~$2,243 net over 11 hours on 2026-05-07 17:00-20:00 ET) documents two distinct empirical failure modes that Sharpe ratio is structurally blind to:

1. **Behavioral failure ("hold until profitable")**: avg-loss / avg-win = 2.39× ($164.67 / $68.95); avg-losing-trade-time / avg-winning-trade-time = 3.65× (1h 9m 49s / 19m 9s). 72.12% win rate masking a left-tailed loss distribution. Empirically clean canonical case: 2026-05-07 17:06-17:16 three CL longs entered at 97.83/97.60/97.25 as oil sold off, all liquidated at 95.61 at 20:00:27 after 2h 44m to 2h 54m holds → **stacked $-5,850 loss in one co-stopped exit**.

2. **Sizing failure (size scaled with run-up)**: 1 contract of full CL (~$100K notional at ~$95/bbl) on a $7-9K account at 17:06:03 on 2026-05-07. Independent of the holding-time failure, the leverage was structurally unsurvivable — even with a perfect entry, a 2% adverse move at that size erases ~25% of bankroll per contract.

**The 4.7× run-up retraced 96.7% in 11 hours is precisely the higher-order-moment tail event that Sharpe ratio is mathematically incapable of penalizing.** Sharpe is a function of the first two moments of the return distribution; it is structurally blind to drawdown-path concentration. Calmar (return / |MaxDD|), terminal-wealth distribution percentiles, and risk-of-ruin probability all capture the tail event Sharpe misses.

### User 2026-05-08 directive (verbatim)

> "Sharpe ratio to me seems to be arbitrary and archaic. We are here to push the limits and test boundaries. we ask research questions no one has asked before and conduct grid searches on a scale akin to multiverses. we do not suppress ideas or potential based on conservative or outdated ideologies just because they are tradition. Let us reframe the paradigm to the entire SKIE-Universe project based on profit, win/loss ratio, and drawdown."

The substantive directive is to **demote Sharpe ratio from primary inferential anchor to secondary KPI** and elevate profit-and-drawdown-aware metrics to the load-bearing position. The user-supplied "Sharpe is archaic" framing is partially right (it assumes Gaussian returns; it penalizes upside vol; it is path-independent — all wrong for retail futures) and partially overstated (it has the cleanest CI machinery in the literature, which is why it persists). What this ADR adopts is not "delete Sharpe" but "replace Sharpe as the *primary* with metrics that align with operator-bankroll-survival reality, while preserving the Sharpe-family computation for academic comparability". The pre-registered §1 T_H statistics in frozen design.md files are preserved verbatim as secondary KPIs; this ADR amends only the project-level §8+§10 promotion paradigm and the §3 KPI report card primary inferential layer.

## Decision

### §1. Primary inferential vector replaces Sharpe-differential

The hypothesis-of-record promotion criterion at the `kpi-report-emitted` → `ninjascript-implemented` and `ninjascript-implemented` → `paper-trade-active` and `paper-trade-active` → `live-promoted` stage transitions is reframed from Sharpe-differential CI dominance to a **survival-constrained metric vector**. Every KPI report card from 2026-05-08 forward MUST surface the following four primary metrics with bootstrap CIs at the §3 canonical-tables level (`H055_kpi_report_v0.md` and forward; retroactively-applied to existing frozen design.md hypotheses via project-level §8+§10 amendment per ADR-0013 §"Frozen pre-registration amendment" §1-§4 amendment discipline):

| Primary metric | Definition | CI primitive | Promotion criterion under ADR-0017 |
|---|---|---|---|
| `terminal_wealth_q05` | 5th percentile of 1-year (252-session) bootstrap-forward $10K-baseline ending equity | Per-arm Politis-White 2004 block-length stationary bootstrap on per-session strategy log-return level series; n_paths = 5,000; rng_seed pinned per ADR-0013 §3.1 | KPI annotation `tw-q05-{above-baseline,above-half,below-half,below-quarter}` with numeric value reported alongside; tiers: `above-baseline` = q05 ≥ $10K (no expected bankroll loss in worst 5%); `above-half` = $5K ≤ q05 < $10K; `below-half` = $2.5K ≤ q05 < $5K; `below-quarter` = q05 < $2.5K (catastrophic-loss tail) |
| `calmar_differential` | `Calmar_arm − Calmar_bench` (difference-of-ratios; each `Calmar_i = (annualized_return_i − rf_i) / \|MaxDD_i\|` per the canonical Young 1991 formulation; per-arm Calmars reported alongside in §3 Table 3b) | Paired-pairs block-stationary-bootstrap CI per [Politis-Romano 1994 *JASA* 89(428):1303-1313](https://doi.org/10.1080/01621459.1994.10476870) on the joint `(r_arm_t, r_bench_t)` tuple series; PW2004-selected block length on the joint level series; 1,000 replicates; new primitive at [src/skie_ninja/inference/calmar.py](../../src/skie_ninja/inference/calmar.py) per `P1-CALMAR-DIFFERENTIAL-CI-IMPL` | KPI annotation `calmar-diff-{positive,marginal,negative}` per CI-vs-zero excludes/covers rule (mirroring the existing ADR-0013 §B annotation grammar) |
| `profit_factor` | `gross_profit / gross_loss` per arm; differential against bench reported as `PF_arm − PF_bench` | Block-stationary-bootstrap CI on the joint per-trade P/L series with PW2004-selected block length; 1,000 replicates; new primitive at [src/skie_ninja/inference/profit_factor.py](../../src/skie_ninja/inference/profit_factor.py) per `P1-PROFIT-FACTOR-CI-IMPL` | KPI annotation `pf-diff-{positive,marginal,negative}`; supplementary `PF >= 1.5` threshold annotation (operator-canonical practitioner convention; Tharp 1998 *Trade Your Way to Financial Freedom* — *practitioner*) |
| `r_multiple_mean` | Per-trade R-multiple = realized P/L / |1R| where 1R = the trade's pre-entry stop-loss distance × position size; mean of the per-trade distribution | Block-stationary-bootstrap CI on per-trade R-multiple series; 1,000 replicates; new primitive at [src/skie_ninja/inference/r_multiple.py](../../src/skie_ninja/inference/r_multiple.py) per `P1-R-MULTIPLE-CI-IMPL` | KPI annotation `r-multiple-mean-{positive,marginal,negative}`; supplementary `r-multiple-mean >= +0.5` threshold annotation (operator-canonical convention indicating "winners pay 1.5R+ on average") |

The promotion criterion is operator-discretionary on the KPI report card (per ADR-0013 §5.3 preserved) but the *load-bearing artifact* the operator reviews is now the survival-constrained metric vector, NOT the Sharpe-differential. A strategy with `tw-q05-above-zero` AND `calmar-diff-positive` AND `pf-diff-positive` AND `r-multiple-mean >= +0.5` is the canonical promotion candidate; one with mixed signals across the four metrics is the canonical operator-judgment-call candidate; one with `tw-q05-below-zero` is the canonical "withhold promotion until remediation" candidate. None of these is binding (per ADR-0013 §1+§2 no-gates philosophy preserved).

### §1.1. Sharpe demoted to secondary KPI

The Sharpe-vs-passive and Sharpe-vs-bench differentials with LW2008 CIs and the Hansen 2005 SPA family p-value are preserved as **secondary KPIs** in the §3 canonical structure. They retain the existing ADR-0013 §B annotation grammar (`sharpe-vs-passive-{positive,marginal,flat,negative}`, `sharpe-vs-bench-{positive,marginal,flat,negative}`, `spa-passes` / `spa-rejects`). Their position in the ADR-0014 §3.2 9-table summary is preserved verbatim; their interpretive load-bearing role is reduced from primary-inferential to KPI-only-for-academic-comparability.

The user 2026-05-08 framing-of-record: "Sharpe-family computation is preserved for cross-strategy and cross-paper comparability with the published quantitative-finance literature; it is not the primary lens through which operator promotion decisions are made under SKIE-Universe."

### §1.2. Pre-registered §1 T_H statistics preserved as secondary KPIs

Each frozen hypothesis design.md §1 contains a `T_H` test statistic on Sharpe-differential (e.g., `T_H050 = SR_gated − SR_uncond`; `T_H052a = SR_gated − SR_uncond`; `T_H053_arm = SR_arm − SR_bench`; `T_H054 = SR_anti_gate − SR_passive`; `T_H055_class = SR_v2 − {SR_BH, SR_TSMOM, SR_RND}` per instrument-class). Per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability, these statistics are **preserved verbatim** in their respective design.md §1 + computed verbatim in the KPI report card alongside the new primary vector. The §1 *statement* is not deleted, modified, or weakened.

What changes is the **§8 + §10 promotion-decision-rule layer** at the project level: §8 + §10 now reference the survival-constrained primary vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) for the load-bearing operator-review artifact, and the design.md-§1-T_H is a §B (per ADR-0012 / ADR-0013 KPI-grammar) secondary annotation.

**Clarification on §1 inferential weight** (per F-16 audit remediation): the §1 H_1 statement remains **computed verbatim** and reported as a numerical KPI in every KPI report card. What this ADR amends is which KPI carries promotion-decision weight at the §8+§10 layer. The §1 H_1 test outcome (e.g., LW2008 strict CI dominance for H055; LW2008 differential CI for H050/H052a/H054; per-arm marginal/positive/negative for H053) is reported alongside the survival-constrained vector in every KPI report card; operator-discretionary review weighs both. The §1 statement's *computational* role is preserved verbatim; its *promotion-decision-rule* role is reduced from primary to secondary at the §8+§10 layer. This is the same amendment-discipline mechanism ADR-0013 used to convert ADR-0012 Class A binding gates into KPI annotations without touching frozen §1-§7 content. Path A.

### §2. Survival-theory metric definitions (load-bearing for §1)

#### §2.1. Terminal-wealth distribution

Per [Browne 1998 *Advances in Applied Probability* 30(1):216-238 "The return on investment from proportional portfolio strategies"](https://doi.org/10.1239/aap/1035228001) survival-probability-maximization framework: starting from $10,000 baseline equity at OOS-window start, the strategy's per-session log-return series defines a multiplicative-equity process `E_{t+1} = E_t × exp(r_t − cost_drag_t)`. The 1-year forward bootstrap (n_paths = 5,000, n_sessions = 252) is the operationally-canonical projection (per ADR-0013 §3.1 preserved verbatim). The terminal-wealth distribution's percentiles {q01, q05, q25, q50 (median), q75, q95, q99} are reported in the §3.1 block; **q05 is the load-bearing primary metric per §1**.

The q05 metric directly answers "in the worst 5% of bootstrapped futures, what is the surviving bankroll fraction?". The q01 supplementary metric answers the analogous question at the 1% tail. Both numbers translate directly to operator-bankroll-survival reasoning in a way that Sharpe ratio cannot.

#### §2.2. Calmar-differential

Per Young, T. W. 1991. "Calmar Ratio: A Smoother Tool." *Futures* 20(12), October 1991 (*practitioner*; trade-press, not peer-reviewed; the original venue for the Calmar attribution — Terry W. Young, California Managed Accounts; "CALMAR" = CALifornia Managed Accounts Reports). The closed-form MaxDD distribution for **Brownian motion with drift** (= the log-return process of GBM) is given by [Magdon-Ismail, Atiya, Pratap & Abu-Mostafa 2004 *J Applied Probability* 41(1):147-161 "On the maximum drawdown of a Brownian motion"](https://www.semanticscholar.org/paper/02bd29696844c0d428412d7300fa5056f0aa9172) — the load-bearing primary source for the closed-form result. The companion practitioner summary is at *Risk* 17(10):99-102, [open-access PDF](https://magdon.cs.rpi.edu/ps/journal/maxdd_risk.pdf) (*practitioner* trade-press; corroborates the *J Applied Probability* result for non-academic readers).

The metric `Calmar_i = (annualized_return_i − rf_i) / |MaxDD_i|` is computed per arm independently (per the canonical Young 1991 formulation); the differential reported is `Calmar_arm − Calmar_bench` (a difference-of-ratios, NOT a ratio-of-difference). The §1 table cell formula in this ADR is updated accordingly: the primary inferential statistic is `Calmar_arm − Calmar_bench`, with the per-arm Calmars reported alongside in the §3 canonical Table 3b.

The CI primitive uses **paired-pairs block-stationary-bootstrap**: joint `(r_arm_t, r_bench_t)` tuples are resampled with a shared block length on the joint series, preserving cross-arm dependence per the H053 Stage-2 paired-pairs primitive precedent at [src/skie_ninja/inference/mediation.py](../../src/skie_ninja/inference/mediation.py). Independent per-arm bootstraps (which would produce miscalibrated CI coverage for the differential statistic) are explicitly forbidden. Block length is selected per Politis-White 2004 + Patton-Politis-White 2009 on the joint level series, not on the differential. Implementation lands at [src/skie_ninja/inference/calmar.py](../../src/skie_ninja/inference/calmar.py) per BLOCKING follow-up `P1-CALMAR-DIFFERENTIAL-CI-IMPL`.

#### §2.3. Profit factor differential

Profit-factor is a long-standing futures-trading practitioner convention (TradeStation system-trading literature, 1980s; Charles LeBeau, David Lucas, Larry Williams; *practitioner-canonical*, multi-source). [Tharp 1998 *Trade Your Way to Financial Freedom* 1st ed., McGraw-Hill, ISBN 978-0070647626](https://www.amazon.com/Trade-Your-Way-Financial-Freedom/dp/0070647623) (*practitioner*) popularized the `PF ≥ 1.5` operator-threshold convention as part of the R-multiple framework. Definition: `gross_profit / gross_loss` per arm; differential reported alongside (`PF_arm − PF_bench`). The metric is operator-intuitive, scale-invariant, and directly measures the symmetry of winning vs losing dollar-flow. The inferential criterion is the bootstrap CI excluding zero (or excluding 1.0 if reported as ratio rather than differential). (Per L-2 audit remediation: Tharp 1998 1st-edition ISBN is 978-0070647626; the 2007 2nd edition has ISBN 978-0071478717. The R-multiple framework was introduced in the 1998 1st edition.)

**Bootstrap-on-per-trade-series caveat** (per F-13 audit remediation): the per-trade P/L series in high-frequency intraday strategies exhibits intra-session correlation (multiple trades within a session correlated via shared regime conditions). Block-stationary-bootstrap on the raw per-trade series with PW2004-selected block length may **under-select the block length** if intra-session clustering is material. Two operationally-acceptable mitigations: (a) bootstrap at the **per-session aggregate level** (gross_profit/gross_loss per session, then aggregate to PF); (b) document the per-trade-bootstrap as an approximation valid under low intra-day clustering, with empirical verification under follow-up `P1-PROFIT-FACTOR-PER-TRADE-CLUSTER-AUDIT`. The default mode is (a) per-session-aggregate; per-trade-bootstrap is a sensitivity exhibit.

#### §2.4. R-multiple distribution

Per [Tharp 1998 *Trade Your Way to Financial Freedom* 1st ed., McGraw-Hill, ISBN 978-0070647626](https://www.amazon.com/Trade-Your-Way-Financial-Freedom/dp/0070647623) (*practitioner*; the R-multiple terminology is genuinely Tharp's, introduced in the 1998 first edition): R = realized per-trade P/L divided by the trade's pre-entry stop-loss distance × position size. The R-multiple distribution captures the convex-payoff structure that all retail-replicable success cases share (Turtles per [Faith 2007 *Way of the Turtle*](https://www.amazon.com/Way-Turtle-Secret-Methods-Successful/dp/0071486646) *practitioner*; CTAs per [Hurst-Ooi-Pedersen 2017 *JPM* 44(1):15-29](https://doi.org/10.3905/jpm.2017.44.1.015) "A Century of Evidence on Trend-Following Investing"). Mean R-multiple ≥ +0.5 is the operator-canonical "winners are 1.5× the size of losers on average" convention.

The R-multiple is **the direct mechanical inverse of the operator's empirical 2026-05-07 failure mode**: the pilot ledger's avg_loss / avg_win = 2.39× corresponds to a mean R-multiple of approximately −0.59 if 1R is calibrated to the avg-loss, or approximately +0.42 if 1R is calibrated to the avg-win. Either way, the empirical R-multiple is well below the +0.5 threshold and the metric directly catches what Sharpe missed.

### §3. KPI report card §3.2 9-table amendment (Path A; preserves ADR-0014 structure)

Per ADR-0014 §3.2 (9-table format mandatory; preserved in this ADR), the existing tables are retained but two are reframed and three new tables are added. The amended table list:

| # | Title | Status under ADR-0017 |
|---|---|---|
| 1 | P/L (realized OOS, $10K baseline) | **PRESERVED** |
| 2 | Drawdown (realized + projected) | **PRESERVED + ELEVATED** to primary inferential layer |
| 3 | Sharpe — primary inference | **DEMOTED to secondary KPI** (table retained at canonical position; interpretive load-bearing role removed) |
| 4 | Annualised Sharpe | **DEMOTED to secondary KPI** (same treatment) |
| 5 | Win/Loss/Zero counts + win rate | **PRESERVED** with new mandatory column `avg_win / avg_loss ratio` and `avg_winning_time / avg_losing_time ratio` (the empirical "hold until profitable" failure-mode signatures from the H055 pilot ledger) |
| 6 | Forward 1-year projection | **PRESERVED + ELEVATED** to primary inferential layer; q05 + q01 columns gain mandatory bold-rendering as the load-bearing entry |
| 7 | Hansen SPA family p | **PRESERVED as secondary KPI** (interpretive role unchanged from ADR-0013) |
| 8 | Other KPIs | **PRESERVED** |
| 9 | Methodological-correctness annotations | **PRESERVED** |
| **NEW 3a** | **Terminal-wealth distribution percentiles** ($10K → 252-session forward bootstrap; columns: q01, q05, q25, median, q75, q95, q99; per arm; per symbol) | **PRIMARY INFERENTIAL** (load-bearing for §1) |
| **NEW 3b** | **Calmar-differential** with bootstrap CI (columns: Calmar_arm, Calmar_bench, ΔCalmar, CI 95%, excludes zero?) | **PRIMARY INFERENTIAL** (load-bearing for §1) |
| **NEW 3c** | **Profit factor + R-multiple** (columns: PF_arm, PF_bench, ΔPF, PF CI; R_mean_arm, R_mean_bench, ΔR_mean, R_mean CI; supplementary `avg_loss/avg_win`, `avg_losing_time/avg_winning_time`) | **PRIMARY INFERENTIAL** (load-bearing for §1) |

**Table-renumbering convention** (per F-10 audit remediation): the canonical table sequence becomes 1, 2, 3, 3a, 3b, 3c, 4, 5, 6, 7, 8, 9 (12 tables total). **Tables 1-9 retain their prior ADR-0014 §3.2 indices** so that downstream cross-references in existing KPI report cards (H050 v1, H052a v1, H053 v1/v2/v3) continue to resolve correctly without retroactive amendment per ADR-0013 §4.1 non-loss. New tables use the 3a/3b/3c suffix-naming convention to avoid shifting downstream indices. Tables 3a/3b/3c are inserted in canonical position **between Table 3 (Sharpe primary inference, now demoted) and Table 4 (Annualised Sharpe, now demoted)** so that visual scanning reads "the survival-constrained vector first, then the legacy Sharpe-family for academic comparability". The bottom-line prose continues to reference the primary inferential vector by name.

The updated template at [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) is amended in this commit per `P1-ADR-0017-TEMPLATE-CASCADE` (BLOCKING-CONCURRENT-WITH-ADR).

### §4. Drawdown-survival-constrained Kelly sizing primitive

#### §4.1. Sizing primitive specification

Per [Kelly 1956 *Bell System Technical Journal* 35(4):917-926](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x) (the canonical Kelly criterion for log-optimal bet sizing) + [Vince 1990 *Portfolio Management Formulas*](https://www.amazon.com/Portfolio-Management-Formulas-Mathematical-Strategies/dp/0471527564) (*practitioner*; risk-of-ruin and optimal-f extensions) + [Grossman & Zhou 1993 *Mathematical Finance* 3(3):241-276](https://doi.org/10.1111/j.1467-9965.1993.tb00044.x) (drawdown-constrained portfolio choice; the canonical theoretical foundation for "maximize growth subject to P(MaxDD > κ) ≤ ε") + Cvitanić, J. & Karatzas, I. 1995. "On portfolio optimization under 'drawdown' constraints." in *Mathematical Finance* (IMA Volumes in Mathematics and its Applications, Vol. 65), Davis, M.H.A. et al. (eds.), Springer, pp. 77-88 ([open-access PDF](https://www.cis.upenn.edu/~mkearns/finread/drawdown.pdf)) (extension to general utility), the project-canonical sizing rule for retail-tier futures strategies is:

```
position_size_at_t = floor(
    min(
        per_trade_risk_budget_t / (k × ATR_n_t × multiplier),    # Vince/Turtle: 1% risk per trade in ATR-units
        kelly_fraction_t × equity_t / (entry_price_t × multiplier),    # Kelly: log-optimal cap
        retail_capacity_ceiling                                   # ADR-0001: hard cap regardless of theory
    )
)
```

where:
- `per_trade_risk_budget_t = 0.01 × equity_t` (1% of equity at risk per trade; the Turtle convention per Faith 2007 *practitioner*)
- `k × ATR_n_t` is the ATR-scaled stop-loss distance in **price units** (typically `k = 2.0`; the Turtle `2N` convention). Multiplying by `multiplier` (the contract multiplier, e.g., 50 for ES, 5 for MES) converts the price-distance to **dollar-loss-per-contract**, so the risk-budget bound returns a contract count.
- `kelly_fraction_t × equity_t / (entry_price_t × multiplier)` is the contract-count form of "deploy fraction `kelly_fraction_t` of equity at price `entry_price_t`" since `entry_price_t × multiplier` is the **dollar-notional-per-contract** and `kelly_fraction_t × equity_t` is the dollar-allocation. (Per F-1/F-2/F-3 audit remediation: the previous formulation included `tick_value` in both bounds; `tick_value` already encodes `multiplier × tick_size` so its inclusion was dimensionally redundant. `tick_value` is retained at the cost-and-slippage layer per [futures_orb_v1 cost model](../../src/skie_ninja/backtest/costs/futures_orb_v1.py) but is NOT part of the sizing rule.)
- `kelly_fraction_t = clamp(f_kelly_raw_t, 0, kelly_cap)` where `f_kelly_raw_t` is the **optimal-f** computed from the IS-fold per-trade R-multiple distribution per [Vince 1990 *Portfolio Management Formulas* Ch. 3](https://www.amazon.com/Portfolio-Management-Formulas-Mathematical-Strategies/dp/0471527564) (*practitioner*); optimal-f returns a fraction in [0, 1] directly, so the clamp at `kelly_cap = 0.25` IS the quarter-Kelly shrinkage. (Per F-1 + L-7 audit remediation: prior formulation `clamp(f_kelly_raw × 0.25, 0, 0.25)` double-applied the shrinkage; corrected formulation `clamp(f_kelly_raw, 0, 0.25)` applies the shrinkage once via the upper-bound clamp. The fractional-Kelly literature surveys shrinkage in [0.25, 0.5] per [MacLean, Thorp & Ziemba 2010 *Kelly Capital Growth*, World Scientific, ISBN 978-9814293495, DOI 10.1142/7598](https://doi.org/10.1142/7598); `kelly_cap = 0.25` is the project-operational lower-bound choice. Full-Kelly is theoretically log-optimal but empirically catastrophic at retail bankroll size due to estimation error in the R-multiple distribution.)
- `retail_capacity_ceiling` per [ADR-0001](ADR-0001-project-scope.md) (≤ 20 ES / ≤ 40 NQ / ≤ 200 MES / ≤ 400 MNQ; equivalent ceilings for CL/MCL/MGC/MYM under the §6 cascade)
- `equity_t` is the current account equity at t (NOT starting equity; the sizing rebases as bankroll grows or shrinks — this is the canonical defense against the operator's empirical "size scaled with run-up but not unscaled with drawdown" failure mode)

**Worked unit-check example** (ES; per F-2 audit remediation): equity = $10,000, entry_price = 5000, ATR = 25, multiplier = 50, kelly_fraction = 0.25, k = 2. Risk-budget bound = `100 / (2 × 25 × 50)` = `100 / 2500` = `0.04 contracts`. Kelly bound = `0.25 × 10000 / (5000 × 50)` = `2500 / 250000` = `0.01 contracts`. floor(min(0.04, 0.01, 20)) = 0 contracts. (At $10K bankroll, ES is correctly sized at 0 contracts; the operator must use MES.) Worked example for MES: entry_price = 5000, multiplier = 5. Risk-budget bound = `100 / (2 × 25 × 5)` = `0.4 contracts`. Kelly bound = `0.25 × 10000 / (5000 × 5)` = `0.1 contracts`. floor(min(0.4, 0.1, 200)) = 0 contracts. **Both bounds bind to zero at $10K bankroll on a 2N-stop ES/MES trade**: this is the canonical "$10K is too small for full ES; barely-feasible for MES" finding that motivates fractional-Kelly retail sizing. The unit-check verifies the formula is dimensionally consistent.

The primitive lands at [src/skie_ninja/sizing/](../../src/skie_ninja/sizing/) per `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE` (BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH). The module includes:
- `kelly_fraction_from_r_multiples(r_multiples: np.ndarray) -> float` — point estimate of `f_kelly_raw` from the IS-fold per-trade R-multiple empirical distribution (Vince 1990 *Portfolio Management Formulas* Ch. 3 "The Optimal f"; *practitioner*)
- `drawdown_constrained_kelly(r_multiples, max_dd_target, confidence) -> float` — `f_kelly_raw` clamped at the value satisfying `P(MaxDD ≤ max_dd_target) ≥ confidence` per Grossman-Zhou 1993 §3 closed-form approximation
- `compute_position_size(equity, atr, tick_value, multiplier, kelly_fraction, capacity_ceiling, k_atr=2.0, risk_budget_pct=0.01) -> int` — the canonical position-sizing function called at every entry decision in NinjaScript and Python orchestrators

#### §4.2. Risk-of-ruin computation

Per [Vince 1990 *Portfolio Management Formulas*](https://www.amazon.com/Portfolio-Management-Formulas-Mathematical-Strategies/dp/0471527564) Ch. 4 "Risk of Ruin" (*practitioner*; the canonical practitioner derivation for fixed-fraction-of-equity sizing under an empirical R-multiple distribution), every KPI report card from 2026-05-08 forward MUST report the **Monte-Carlo-estimated probability of ruin** = P(equity reaches a `ruin_threshold` before `n_sessions` = 252) under the strategy's empirical per-trade R-multiple distribution × the §4.1 sizing rule.

**Ruin threshold default + rationale** (per F-7 audit remediation): `ruin_threshold = 0.5 × starting_equity` (50% of starting bankroll) is the project-operational default. Rationale: the Vince 1990 Ch. 4 risk-of-ruin formulation parameterizes ruin as an arbitrary percentage of starting bankroll; the 50% threshold reflects the operator-canonical "don't delete more than half the bankroll" floor and is calibratable per follow-up `P1-ADR-0017-RUIN-THRESHOLD-EMPIRICAL` (e.g., the Faith 2007 Turtle 20% MaxDD floor is a stricter alternative; the operator may calibrate per-strategy). The metric is reported alongside `terminal_wealth_q05` in §3 canonical Table 3a and feeds directly into operator promotion review.

**Note on Feller 1968 Ch. XIV cite** (per F-6 audit remediation): the gambler's-ruin closed-form recurrence in [Feller 1968 *An Introduction to Probability Theory and Its Applications* Vol. I, 3rd ed., Wiley, ISBN 978-0471257080](https://www.wiley.com/en-us/An+Introduction+to+Probability+Theory+and+Its+Applications%2C+Volume+1%2C+3rd+Edition-p-9780471257080) Ch. XIV is for symmetric / asymmetric **simple random walks with fixed bet size** and is NOT directly applicable to multiplicative-equity processes with varying R-multiples and ATR-scaled position sizing. Feller 1968 is cited as **corroborating motivation** (the gambler's-ruin framework is the conceptual ancestor of the Monte Carlo simulation), NOT as the load-bearing primary source for the simulator's correctness. The simulator's correctness derives from the empirical R-multiple distribution + multiplicative-equity dynamics + the §4.1 sizing rule, not from Feller's closed-form.

**Sizing-rule integration** (per F-14 audit remediation): the Monte Carlo simulator at [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py) accepts a callable `sizing_fn(equity, atr, ...) -> contracts` parameter that defaults to the §4.1 sizing rule. The interface contract permits both (a) the canonical project sizing rule (default; called per-trade with current equity), and (b) the simplified fixed-fraction-of-equity approximation (legacy default for cross-paper comparability). Both modes must be supported; the report card MUST surface which mode was used.

### §5. Hard kill-switch constraints (project-wide; mandatory for every hypothesis from H055 forward)

The following 8 hard rule constraints are **mandatory inheritance** for every hypothesis design.md §11.1 from H055 forward (and via the `P1-ADR-0017-DESIGN-MD-CASCADE` deferred follow-up, retroactively for the frozen hypotheses H050/H051/H052a/H052b/H053/H054). These are NOT optimization targets and NOT promotion criteria; they are operational hard-stops at the kill-switch layer that mechanize the inverse of the operator's empirical failure modes documented in §Context observation 3.

| # | Constraint | Default value | Rationale |
|---|---|---|---|
| K-1 | **Per-trade $-stop** | 1.0 R where R = `k × ATR_n × tick_value × position_size`, `k = 2.0` | Mechanical inverse of avg_loss = 2.39× avg_win in the pilot ledger; caps single-trade losses at the entry-time ATR-scaled stop. Turtle 2N convention per Faith 2007 *practitioner*. |
| K-2 | **Per-trade time-stop** | 2× median winning-trade duration on the calibration holdout (per-instrument-class; reported in design.md §11.1 numerically per hypothesis) | Mechanical inverse of avg_losing_time = 3.65× avg_winning_time in the pilot ledger; terminates trades that have not closed in winner-canonical time. |
| K-3 | **No-add-to-loser** | Forbid second entry on the same instrument while an open position is in unrealized loss | Mechanical inverse of the 2026-05-07 17:06/17:08/17:16 CL stack ($-5,850 in one co-stopped exit). Zero exception. |
| K-4 | **Per-symbol position cap** | Per [ADR-0001](ADR-0001-project-scope.md) retail capacity ceiling (≤ 20 ES, ≤ 40 NQ, ≤ 200 MES, ≤ 400 MNQ; equivalent for CL/MCL/MGC/MYM per §6 cascade) | Hard cap regardless of Kelly output; binds at the `compute_position_size` floor per §4.1. |
| K-5 | **Correlated-instrument inventory cap** | CL+MCL share a budget; ES+MES share a budget; NQ+MNQ share a budget; YM+MYM share a budget; GC+MGC share a budget. Aggregate per-group exposure ≤ 1.0× the largest single-symbol cap in the group (in $-notional terms). | Catches the cross-symbol stack that the per-symbol cap K-4 misses (e.g., 1 CL + 4 MCL ≠ 0 CL + 4 MCL). Prevents undeclared cross-symbol leverage. |
| K-6 | **Daily circuit breaker** | Cease trading for the session at -2% of equity realized P/L | Mechanical inverse of the 2026-05-07 11-hour escalation from peak-equity to MaxDD; caps single-day damage at a survivable fraction of bankroll. |
| K-7 | **Weekly circuit breaker** | Cease trading for the week at -5% of equity realized P/L (approximately 2.5× the daily cap) | Catches the multi-day version of the same escalation pattern; allows the operator to step away and reassess before the bankroll is materially impaired. |
| K-8 | **Per-trade entry-into-adverse-direction filter** | Forbid entries where the trigger bar's higher-TF (T_H) trend gate sign disagrees with the entry direction AND the price has moved adversely > 0.5 ATR from the entry-bar open at fill time | Mechanical inverse of the 2026-05-07 CL stack which entered longs as oil was selling off; closes the "averaging-down into a falling knife" pattern at the entry filter. |

The defaults above are the project-canonical baselines. Each hypothesis design.md §11.1 MAY tighten any constraint with `# justify:` annotation but MAY NOT loosen any below the default (loosening requires a project-level ADR amendment). The constraints are enforced **at the kill-switch layer** in NinjaScript implementation per ADR-0013 §5.1 and validated **at the backtest layer** in the Python walk-forward orchestrator per the Cycle-4 leak-canary discipline (per `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`).

#### §5.1. K-1 vs K-6 interaction analysis (per F-8 audit remediation)

K-1 per-trade $-stop = 1R = 0.01·equity (1% per trade; assuming K-1 binds the per-trade loss exactly at risk-budget). K-6 daily circuit breaker = -2% of equity. Two losing trades at exactly 1R each hit the K-6 daily breaker exactly. For a high-frequency scalp strategy (the H055 archetype) with N trades/session, the implied break-even win-rate to avoid daily K-6 activation under worst-case equal-magnitude losers is `win_rate ≥ N / (N + 2)`: a 30-trade/session strategy must achieve ≥ 93.75% win-rate to mathematically guarantee K-6 stays inactive, regardless of R-multiple. This is INTENTIONAL: the K-6 floor is operator-bankroll-survival-protective, not strategy-protective. The implication is that K-6 will fire on bad days for any realistic high-frequency strategy, and that's the design — K-6 is not a strategy-failure signal but a daily-loss-cap that ends trading for the session.

**Operator-discretionary tightening**: a hypothesis whose IS-fold empirical session-loss distribution shows P(daily-loss > -3%) < 5% may tighten K-6 to -1.5% with `# justify:` annotation. Conversely, a hypothesis with a thicker-tailed session-loss distribution may NOT loosen K-6 above -2% without project-level ADR amendment. The interaction `K-1 × N_trades_per_session × P(loss-per-trade)` is computed per hypothesis at the calibration-holdout stage and reported in design.md §11.1 as load-bearing rationale for any K-1/K-6 calibration deviation.

#### §5.2. K-5 correlated-instrument cap worked example (per F-9 audit remediation)

K-5 reads "aggregate per-group $-notional ≤ 1.0× the largest single-symbol cap in the group". Worked example for ES+MES group:
- ES single-symbol cap (K-4): 20 contracts × $50 multiplier × $5,000 entry-price = **$5,000,000 notional**
- MES single-symbol cap (K-4): 200 contracts × $5 multiplier × $5,000 entry-price = **$5,000,000 notional**
- "Largest single-symbol cap in the group" = $5,000,000
- K-5 group cap = 1.0 × $5,000,000 = **$5,000,000 aggregate notional across ES+MES**

This means: 20 ES + 0 MES ≡ 0 ES + 200 MES ≡ 10 ES + 100 MES (each = $5M notional) are all admissible at K-5; 20 ES + 200 MES ($10M) is NOT admissible (would require K-5 = 2.0×, which exceeds the project default). K-5 thus enforces a "no-double-counting" constraint preventing K-4 ES and K-4 MES limits from being independently saturated. The same arithmetic applies to NQ+MNQ, YM+MYM, GC+MGC, CL+MCL groups with their per-symbol caps. The dollar-notional formulation is invariant to instrument choice within the group.

### §6. Failure-mode-overfitting stress test

Per the §Context observation that the H055 pilot ledger contains **N=1 catastrophic event** (the 2026-05-07 CL stack), there is genuine overfitting-to-failure-mode risk in mechanizing the kill-switch constraints around the specific empirical anti-pattern. To mitigate, every hypothesis from H055 forward MUST execute a **synthetic-failure-mode stress test** at the §11.2 BLOCKING-BEFORE-LAUNCH precondition layer:

| Synthetic failure mode | Description | Stress-test pass criterion |
|---|---|---|
| FM-1 — Death by thousand cuts | Replace per-trade losses with `-0.25R` losses in larger quantity (e.g., 4× as many trades, each 1/4 the loss); preserves total $-loss but spreads across more entries | The §5 K-1 to K-8 constraints catch the cumulative damage via K-6 daily circuit breaker before week-end |
| FM-2 — Gap-overnight | Inject an overnight gap = -3 ATR on a held position from one session to the next | The strategy implements an explicit session-boundary mark-to-market check: if the held position's unrealized P/L at session-open exceeds -1R, the position is force-closed at session-open at the marked-to-market price. Realized loss bounded at session-open mark-to-market. (Per F-15 audit remediation: the prior pass criterion "K-1 fires at session open" was insufficient because K-1 is an ATR-stop *during* a held trade, not a session-boundary trigger — the gap event occurs between sessions. The session-boundary check is an explicit additional kill-switch beyond K-1..K-8 for any strategy that holds positions overnight; strategies with an in-session-only mandate (RTH close = hard close) are exempt by construction.) |
| FM-3 — News-spike | Inject a 5σ adverse return in a 1-min bar during an active position (modeling a Reuters headline / Twitter-bomb / ECB unscheduled release) | The strategy MUST satisfy BOTH conditions: (a) the news-calendar §4 eligible-bar filter prevents entry in the configured news window (FOMC ±15min, NFP ±5min, CPI ±5min per H055 §4); AND (b) for the unscheduled-news case (Reuters headline / Twitter-bomb not on the configured calendar), a counterfactual entry into the spike triggers K-1 with realized-loss-bound at 1R. (Per F-15 audit remediation: prior disjunctive criterion was trivially satisfiable by enabling the news-calendar filter; the AND-conjunction tests both the configured-news handling AND the unscheduled-news bound.) |
| FM-4 — Latency-induced bad fill | Inject 2-tick adverse slippage on every entry and exit (modeling a degraded NT8 bridge connection) | The cost-floor sensitivity exhibit per design.md §14 (cost_mult = 2.0) demonstrates the strategy survives the elevated cost regime |
| FM-5 — Regime change mid-trade | Inject a structural break in the per-session return distribution at the OOS-window midpoint (modeling a regime change the IS-fold did not contain) | Either the strategy's regime-conditioning catches the break OR the §K-7 weekly circuit breaker fires before the cumulative damage exceeds 5% of equity |

The stress test is implemented at [scripts/stress_test_failure_modes.py](../../scripts/stress_test_failure_modes.py) per `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` (BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH; for retroactive coverage of H050/H052a/H053/H054, the stress test is NON-BLOCKING but emitted as a v{N+1} KPI report card amendment).

The pass criteria are NOT binding gates (per ADR-0013 §1+§2 no-gates philosophy). A strategy failing one or more stress tests records the failure as a methodological-correctness annotation `stress-test-FM-N-fail` with the offending behavior enumerated in the failure_log.md (per ADR-0013 §4.2). Operator-discretionary review at promotion time decides remediation timing.

## Frozen pre-registration amendment

This ADR amends §8 + §10 of all hypothesis design.md files (H050, H051, H052a, H052b, H053, H054, H055, H056, H057, H058, H059) project-wide per ADR-0013 §"Frozen pre-registration amendment" §1-§4 amendment discipline. Per the same discipline, each affected design.md must reference ADR-0017 explicitly in §8 + §10 + new §11.1 amendment. The cascade is tracked under follow-up `P1-ADR-0017-DESIGN-MD-CASCADE` and is BLOCKING-BEFORE-NEXT-STAGE-3-RUN per the ADR-0013 precedent (P1-ADR-0013-DISPOSITION-FRAMEWORK-REFACTOR).

For H055 (the immediately-load-bearing instance), the §11.1 amendment lands in the same commit group as this ADR per Path A frozen-pre-reg amendment scope. H055's §17 amendment ledger gains a 2026-05-08 entry recording the ADR-0017 cross-link.

For H056-H059 (currently `queued` per [plan/h055_successor_tree_2026-05-06.md](../../plan/h055_successor_tree_2026-05-06.md)), ADR-0017's §1 + §3 + §4 + §5 are inherited at pre-registration time; their design.md §1 statements are written under the survival-constrained paradigm from inception (no Sharpe-differential T_H statistic in §1; Sharpe-family computation reported as KPI annotation per §1.2).

## Alternatives considered

### A. Retain Sharpe-differential as primary; add survival metrics as supplementary KPIs only

Rejected. The empirical observations 2 + 3 in §Context demonstrate that Sharpe-CIs are systematically tighter around zero than profit-and-drawdown reality, which leads to false-negative dispositions on substantively profitable cells. The user 2026-05-08 directive is explicit ("reframe the paradigm to the entire SKIE-Universe project based on profit, win/loss ratio, and drawdown"). A half-measure preserving Sharpe-as-primary contradicts the directive.

### B. Replace Sharpe in §1 of frozen design.md files (delete + rewrite §1 verbatim)

Rejected. ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability is non-negotiable — modifying §1 would invalidate the pre-registration discipline and (more practically) destroy the H050/H052a/H053/H054 KPI report card cross-references that depend on the §1 T_H statistic. The Path A amendment mechanism (this ADR amends §8 + §10 + adds §11.1 elaboration) preserves §1-§7 verbatim and elevates the primary-inferential layer at the §3 KPI report card structure layer, where the amendment is principled and safe.

### C. Make the survival metrics binding gates (not KPIs)

Rejected. ADR-0013 §1+§2 no-gates philosophy is project-canonical and unmodified by this ADR. The survival-constrained metrics are the **load-bearing operator-review artifact**, not gates. Operator promotion decisions are operator-discretionary (per ADR-0013 §5.3 preserved); the metrics inform the decision without binding it. This is the same pattern ADR-0013 used to convert ADR-0012 Class A binding gates into KPIs.

### D. Adopt only one of {Calmar, terminal-wealth-q05, profit-factor, R-multiple} as the single primary metric

Rejected. The four metrics measure overlapping-but-distinct aspects of strategy quality:
- `terminal-wealth-q05` answers "will my bankroll survive in the worst 5% of futures?"
- `Calmar-differential` answers "is this strategy meaningfully better than the bench per unit of drawdown pain?"
- `profit-factor` answers "is the dollar-flow symmetric (gross profit ≥ gross loss)?"
- `r-multiple-mean` answers "do winners pay more R than losers cost?"

Reducing to a single primary risks the same overfit-to-one-metric pathology that motivated this ADR (Sharpe-only optimization missing Calmar-catastrophic strategies). The vector formulation forces operator review across the four lenses.

### E. Defer the kill-switch §5 constraints to a separate ADR (focus this ADR on metric-paradigm only)

Rejected. The §5 kill-switch constraints are the *mechanical* counterpart to the §1-§4 *measurement* paradigm shift. Decoupling them creates a window where the new metrics are measured but the failure modes they were designed to catch are not yet structurally prevented. The empirical evidence (2026-05-07 pilot ledger) demonstrates that measurement without mechanical prevention is insufficient. Bundle the two; land them together.

### F. Use the SKIE-Universe pilot ledger as the calibration substrate for §5 default values

Rejected. The pilot ledger is N=1 catastrophic event (the 2026-05-07 stack); calibrating the §5 defaults to fit the pilot would be the canonical overfitting-to-failure-mode pathology that §6 stress tests are designed to detect. The §5 defaults are anchored to **literature-canonical conventions** (Turtle 2N stop, 1% per-trade risk, fractional-Kelly with 0.25 cap) that have multi-decade out-of-sample evidence across Faith 2007 *practitioner*, Vince 1990 *practitioner*, MacLean-Thorp-Ziemba 2010 *peer-reviewed* and the long-running CTA literature. The pilot ledger informs the **rationale** for the §5 constraints (column 4 of the §5 table); it does not calibrate their numeric values.

## Consequences

### Adopted

- Survival-constrained metric vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) becomes the primary inferential layer for operator promotion review.
- Sharpe-family computations (LW2008 differential CI, Hansen 2005 SPA p) are demoted to secondary KPIs preserved for academic comparability.
- 8 hard kill-switch constraints (§5) are mandatory inheritance for every hypothesis from H055 forward.
- 5 synthetic-failure-mode stress tests (§6) are mandatory for every hypothesis from H055 forward.
- Drawdown-survival-constrained Kelly sizing primitive (§4) is mandatory for every hypothesis from H055 forward (and for the retroactive cascade where the existing strategy did not implement it).
- ADR-0014 §3.2 9-table format is updated to a 12-table format with new mandatory tables 3a/3b/3c.
- All pre-registered §1 T_H statistics are preserved verbatim per ADR-0013 §1-§7 immutability; their interpretive role is reduced from primary-inferential to secondary KPI.

### Trade-offs accepted

- **Inferential machinery for the new primary vector is less mature than for Sharpe-family.** Mitigated by: (a) Calmar / profit-factor / R-multiple all admit block-stationary-bootstrap CIs as a universal hammer (the existing [src/skie_ninja/inference/bootstrap.py](../../src/skie_ninja/inference/bootstrap.py) primitive is re-used); (b) terminal-wealth-q05 is a direct read on the existing ADR-0013 §3.1 forward-projection block (no new infrastructure required for the metric itself; only for the CI primitives). The trade-off is that Sharpe-family has multi-decade peer-reviewed CI literature ([Lo 2002 *FAJ*](https://doi.org/10.2469/faj.v58.n4.2453); [Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084); [LW2008](https://doi.org/10.1016/j.jempfin.2008.03.002)); the survival-constrained metric CIs lean on the more general bootstrap framework ([Politis-Romano 1994](https://doi.org/10.1080/01621459.1994.10476870)) without metric-specific asymptotic theory. This is acceptable per the user 2026-05-08 directive's explicit prioritization of operator-bankroll-survival reasoning over academic-comparability rigor.
- **Multiple-testing deflation for the survival-constrained vector is less developed than for Sharpe.** [Bailey & López de Prado 2014 *JPM* 40(5):94-107 "The Deflated Sharpe Ratio"](https://doi.org/10.3905/jpm.2014.40.5.094) provides PSR/DSR for Sharpe; equivalent constructions exist for Sortino and Omega in the Bailey-LdP follow-on literature but are not yet implemented in [src/skie_ninja/inference/](../../src/skie_ninja/inference/). The PBO ([Bailey, Borwein, López de Prado, Zhu 2014 *Notices AMS* 61(5):458-471](https://www.ams.org/notices/201405/rnoti-p458.pdf)) combinatorially-symmetric CV is metric-agnostic and applies directly to the new primary vector. PSR/DSR-equivalent for terminal-wealth-q05 and Calmar are research-extension work tracked under `P1-ADR-0017-MULTIPLE-TESTING-DEFLATION-RESEARCH`.
- **Operator review burden grows.** Twelve canonical tables instead of nine; the operator must reason across four primary metrics instead of one. This is a deliberate trade for the no-overfit-to-Sharpe philosophy.
- **Retroactive cascade work is non-trivial.** H050/H051/H052a/H052b/H053/H054 design.md §8 + §10 + §11.1 must be amended; existing KPI report cards (H050 v1, H052a v1, H053 v1/v2/v3) are not retroactively edited (per ADR-0013 §4.1 non-loss); v{N+1} report cards are emitted with the new tables 3a/3b/3c as the cascade lands. Sequenced per operator priority under `P1-ADR-0017-DESIGN-MD-CASCADE` + `P1-ADR-0017-KPI-REPORT-CARD-V2-CASCADE`.

### Residual risk

- **The 8 hard kill-switch constraints are mechanical inverses of the operator's specific 2026-05-07 failure mode.** N=1 catastrophic event is thin evidence for the specific numeric defaults. Mitigated by: (a) §6 stress tests force evaluation against synthetic alternative failure modes; (b) the literature-canonical defaults (Turtle 2N, 1% risk, fractional-Kelly 0.25 cap) have multi-decade out-of-sample evidence; (c) per-hypothesis tightening is allowed via `# justify:` annotation, encouraging strategy-specific calibration without project-wide loosening.
- **Terminal-wealth-q05 with bootstrap-as-generative-model assumes the OOS distribution mirrors the forward distribution.** This assumption fails under regime change beyond the OOS window (per ADR-0013 §3.1 caveat already in force). Mitigated by: (a) §6 FM-5 (regime change mid-trade) stress test; (b) operator-discretion at every promotion remains the structural safeguard.
- **Sharpe-family demotion may invite "regression to old paradigm" pressure during cross-paper comparability discussions.** Mitigated by: (a) Sharpe is preserved verbatim as a secondary KPI in every report card (the metric is not deleted; its interpretive load-bearing role is reduced); (b) the user 2026-05-08 directive is explicit and project-binding; (c) every promotion decision logs the operator's rationale across the survival-constrained primary vector AND the Sharpe-family secondary KPIs.

## Empirical justification

The empirical basis is the conjunction of (a) the H050 + H052a + H053 KPI emissions demonstrating that Sharpe-CIs are systematically tighter around zero than profit-and-drawdown reality, (b) the operator 2026-05-01 → 2026-05-07 pilot ledger documenting the dual failure-mode signature (behavioral + sizing), and (c) the user 2026-05-08 directive explicitly reframing the project paradigm. Each is independent evidence; together they constitute the load-bearing motivation for this ADR.

The CLAUDE.md user-global §"Evidence Hierarchy" is preserved unchanged: peer-reviewed → official docs → professional standards → vetted forums → reproduction. The ADR-0017 metric vector draws from a mix of peer-reviewed primary sources (Browne 1998; Grossman-Zhou 1993; Cvitanić-Karatzas 1995 IMA; Kelly 1956; MacLean-Thorp-Ziemba 2010; Bailey-López de Prado 2014; Politis-Romano 1994) and operator-canonical practitioner sources (Faith 2007; Tharp 1998; Vince 1990; Young 1991), each tagged accordingly per CLAUDE.md §"Practitioner-source-tag" convention.

## References

### Peer-reviewed primary

- Browne, S. 1998. "The return on investment from proportional portfolio strategies." *Advances in Applied Probability* 30(1):216-238. [DOI 10.1239/aap/1035228001](https://doi.org/10.1239/aap/1035228001). (Survival-probability-maximization framework for terminal-wealth-q05; load-bearing for §2.1. Per L-1 audit remediation: prior cite "Browne 1995 J Appl Prob 32(3):759-779 DOI 10.2307/3215126" was a wrong-DOI error — that DOI resolves to Asmussen & Nielsen 1995 "Ruin probabilities via local adjustment coefficients", a different paper; the actual Browne paper is in *Adv Appl Prob* 30(1) 1998.)
- Grossman, S. J. & Zhou, Z. 1993. "Optimal investment strategies for controlling drawdowns." *Mathematical Finance* 3(3):241-276. [DOI 10.1111/j.1467-9965.1993.tb00044.x](https://doi.org/10.1111/j.1467-9965.1993.tb00044.x). (Drawdown-constrained portfolio choice; load-bearing for §4.1.)
- Cvitanić, J. & Karatzas, I. 1995. "On portfolio optimization under 'drawdown' constraints." in *Mathematical Finance* (IMA Volumes in Mathematics and its Applications, Vol. 65), Davis, M.H.A. et al. (eds.), Springer, pp. 77-88. [Open-access PDF](https://www.cis.upenn.edu/~mkearns/finread/drawdown.pdf). (Per L-3 audit remediation: prior cite "Mathematical Finance 5(2):153-188 DOI 10.1111/j.1467-9965.1995.tb00037.x" — that DOI returns 404; the actual venue is the Springer IMA Volumes Vol. 65. Extension to general utility; corroborating Grossman-Zhou 1993.)
- Magdon-Ismail, M., Atiya, A. F., Pratap, A. & Abu-Mostafa, Y. S. 2004. "On the maximum drawdown of a Brownian motion." *Journal of Applied Probability* 41(1):147-161. [Semantic Scholar listing](https://www.semanticscholar.org/paper/02bd29696844c0d428412d7300fa5056f0aa9172). (Closed-form MaxDD distribution for Brownian motion with drift = the log-return process of GBM; load-bearing for §2.2 Calmar inferential framework. Per L-4 audit remediation: the closed-form result is in this *J Applied Probability* paper, NOT in the *Risk* magazine note cited below.)
- Magdon-Ismail, M. & Atiya, A. F. 2004. "Maximum drawdown." *Risk* 17(10):99-102. [Open-access PDF](https://magdon.cs.rpi.edu/ps/journal/maxdd_risk.pdf). (*practitioner* trade-press; corroborates the *J Applied Probability* result for non-academic readers.)
- Kelly, J. L. 1956. "A new interpretation of information rate." *Bell System Technical Journal* 35(4):917-926. [DOI 10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x). (Canonical Kelly criterion for log-optimal bet sizing; load-bearing for §4.1 sizing primitive.)
- MacLean, L. C., Thorp, E. O. & Ziemba, W. T. (eds.) 2010. *The Kelly Capital Growth Investment Criterion: Theory and Practice*. World Scientific, ISBN 978-9814293495. [DOI 10.1142/7598](https://doi.org/10.1142/7598). (Fractional-Kelly literature canon; load-bearing for §4.1 fractional-Kelly clamp.)
- Bailey, D. H. & López de Prado, M. 2014. "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality." *J Portfolio Management* 40(5):94-107. [DOI 10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094). (DSR multiple-testing deflation; preserved as Sharpe-family KPI per §1.1.)
- Bailey, D. H., Borwein, J. M., López de Prado, M. & Zhu, Q. J. 2014. "Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance." *Notices of the American Mathematical Society* 61(5):458-471. [Open access](https://www.ams.org/notices/201405/rnoti-p458.pdf). (PBO combinatorially-symmetric CV; metric-agnostic; applies to the §1 primary vector.)
- Ledoit, O. & Wolf, M. 2008. "Robust performance hypothesis testing with the Sharpe ratio." *J Empirical Finance* 15(5):850-859. [DOI 10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002). (LW2008 studentized stationary-bootstrap CI; preserved as Sharpe-family KPI computation.)
- Lo, A. W. 2002. "The Statistics of Sharpe Ratios." *Financial Analysts Journal* 58(4):36-52. [DOI 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453). (Sharpe asymptotic CI; preserved as Sharpe-family KPI computation.)
- Opdyke, J. D. 2007. "Comparing Sharpe ratios: So where are the p-values?" *J Asset Management* 8(5):308-336. [DOI 10.1057/palgrave.jam.2250084](https://doi.org/10.1057/palgrave.jam.2250084). (Mertens-HAC variant for Sharpe CI; preserved as Sharpe-family KPI computation.)
- Hansen, P. R. 2005. "A test for superior predictive ability." *J Business & Economic Statistics* 23(4):365-380. [DOI 10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063). (SPA family p-value; preserved as Sharpe-family KPI computation.)
- Politis, D. N. & Romano, J. P. 1994. "The stationary bootstrap." *Journal of the American Statistical Association* 89(428):1303-1313. [DOI 10.1080/01621459.1994.10476870](https://doi.org/10.1080/01621459.1994.10476870). (Stationary bootstrap; load-bearing for §2.2 Calmar-differential CI.)
- Hurst, B., Ooi, Y. H. & Pedersen, L. H. 2017. "A Century of Evidence on Trend-Following Investing." *J Portfolio Management* 44(1):15-29. [DOI 10.3905/jpm.2017.44.1.015](https://doi.org/10.3905/jpm.2017.44.1.015). (Trend-following retail-replicable success-evidence; corroborating §Context observation 3 alternative-paradigm framing.)

### Practitioner

- Faith, C. M. 2007. *Way of the Turtle: The Secret Methods that Turned Ordinary People into Legendary Traders*. McGraw-Hill, ISBN 978-0071486644. (*practitioner*; Turtle 1% risk-per-trade + 2N stop + 20-day Donchian breakout; load-bearing for §5 K-1 + §4.1 risk-budget convention.)
- Vince, R. 1990. *Portfolio Management Formulas: Mathematical Trading Methods for the Futures, Options, and Stock Markets*. Wiley, ISBN 978-0471527565. (*practitioner*; risk-of-ruin recurrence + optimal-f sizing; load-bearing for §4.2 risk-of-ruin computation.)
- Tharp, V. K. 1998. *Trade Your Way to Financial Freedom* 1st ed. McGraw-Hill, ISBN 978-0070647626. (*practitioner*; R-multiple framework introduced + profit-factor `PF ≥ 1.5` operator-threshold popularized; load-bearing for §1 + §2.3 + §2.4. Note: 2007 2nd edition has ISBN 978-0071478717 — both editions cover the R-multiple material; the 1998 1st edition is the original attribution.)
- Young, T. W. 1991. "Calmar Ratio: A Smoother Tool." *Futures* magazine. (*practitioner*; trade-press, not peer-reviewed; canonical attribution for the Calmar ratio name; corroborated by Magdon-Ismail-Atiya 2004 above for the closed-form MaxDD distribution.)
- Feller, W. 1968. *An Introduction to Probability Theory and Its Applications, Volume I*, 3rd ed. Wiley, ISBN 978-0471257080. Ch. XIV "The Gambler's Ruin Problem". (Canonical primary source for the gambler's-ruin recurrence underlying §4.2 risk-of-ruin Monte Carlo.)

### Project-internal

- [ADR-0001](ADR-0001-project-scope.md) — retail capacity ceiling; load-bearing for §5 K-4.
- [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — KPI-only, no-archive, NinjaScript terminus, non-loss mandate; load-bearing for the amendment-discipline mechanism this ADR uses.
- [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — canonical 9-table results-summary; this ADR amends to 12-table format.
- [ADR-0015](ADR-0015-component-stacking-master-architecture.md) — component-stacking master architecture; preserved unchanged.
- [ADR-0016](ADR-0016-sibling-repo-audit-and-lift-protocol.md) — sibling-repo audit-and-lift protocol; preserved unchanged.
- [data/external/h055_pilot_ledger/](../../data/external/h055_pilot_ledger/) — pilot ledger 2026-05-01 → 2026-05-06 (171 trades); load-bearing empirical motivation for §Context observation 3. The 2026-05-08 226-trade extension PDF (Performance.20260508.202151.pdf, processed via §Context observation; NOT committed per the user 2026-05-08 directive on public-repo identity-hygiene) supplements the load-bearing motivation but does not land in the repository.
- [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md) — H050 KPI report card; load-bearing for §Context observation 1 (Sharpe-test correctly captured catastrophe).
- [research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md) — H052a KPI report card; load-bearing for §Context observation 2 (NQ unconditional ORB false-negative).
- [research/01_hypothesis_register/H053/H053_kpi_report_v3.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v3.md) — H053 KPI report card; load-bearing for §Context observation 2 (NQ LightGBM false-negative).
- [docs/audits/audit_trail_2026-05-08_adr-0017-survival-constrained-paradigm.md](../audits/audit_trail_2026-05-08_adr-0017-survival-constrained-paradigm.md) — this ADR's audit-remediate-loop trail.

## Follow-ups

### Cascade (housekeeping; not blocking the ADR's adoption — landing concurrent with this ADR commit per Path A)

- `P1-ADR-0017-DESIGN-MD-CASCADE` — cascade ADR-0017 references into all hypothesis design.md §8 + §10 + §11.1 amendments. **BLOCKING-BEFORE-NEXT-STAGE-3-RUN** per the ADR-0013 P1-ADR-0013-DISPOSITION-FRAMEWORK-REFACTOR precedent. Minimum cascade for H055 lands inline with this ADR commit.
- `P1-ADR-0017-TEMPLATE-CASCADE` — update [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) with new mandatory tables 3a/3b/3c per §3. **BLOCKING-CONCURRENT-WITH-ADR**; lands in this commit group.
- `P1-ADR-0017-KPI-REPORT-CARD-V2-CASCADE` — emit v{N+1} KPI report cards for H050/H052a/H053/H054 with the new tables 3a/3b/3c populated; v{N} preserved verbatim per ADR-0013 §4.1. Sequenced per operator priority.
- `P1-ADR-0017-CLAUDE-MD-CASCADE` — full CLAUDE.md amendment for §"KPI report card for every strategy" + §"Standing constraints" (this commit lands the minimal Phase K ledger entry; the comprehensive cascade is the follow-up).

### Inferential primitives (BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH; concurrent build with this ADR or immediately after)

- `P1-CALMAR-DIFFERENTIAL-CI-IMPL` — implement [src/skie_ninja/inference/calmar.py](../../src/skie_ninja/inference/calmar.py) with `calmar_ratio`, `calmar_differential`, `calmar_differential_ci_stationary_bootstrap` per §2.2.
- `P1-PROFIT-FACTOR-CI-IMPL` — implement [src/skie_ninja/inference/profit_factor.py](../../src/skie_ninja/inference/profit_factor.py) with `profit_factor`, `profit_factor_differential`, `profit_factor_differential_ci_stationary_bootstrap` per §2.3.
- `P1-R-MULTIPLE-CI-IMPL` — implement [src/skie_ninja/inference/r_multiple.py](../../src/skie_ninja/inference/r_multiple.py) with `r_multiple_from_trade`, `r_multiple_distribution`, `r_multiple_mean_ci_stationary_bootstrap` per §2.4.
- `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE` — implement [src/skie_ninja/sizing/](../../src/skie_ninja/sizing/) module per §4.1 (`kelly_fraction_from_r_multiples`, `drawdown_constrained_kelly`, `compute_position_size`).
- `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE` — implement [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py) with `probability_of_ruin_monte_carlo` per §4.2.
- `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` — implement [scripts/stress_test_failure_modes.py](../../scripts/stress_test_failure_modes.py) with the 5 synthetic failure modes per §6.
- `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` — wire the §5 hard kill-switch constraints into the Cycle-4 leak-canary discipline at the walk-forward orchestrator layer; emit a `kill-switch-canary-{pass,fail}` annotation per fold.
- `P1-ADR-0017-MULTIPLE-TESTING-DEFLATION-RESEARCH` — research-extension follow-up to develop PSR/DSR-equivalent constructions for terminal-wealth-q05 and Calmar-differential beyond the metric-agnostic PBO.

### Non-blocking

- `P1-ADR-0017-PILOT-LEDGER-V2-NON-COMMIT-PROVENANCE` — record the 2026-05-08 226-trade pilot ledger PDF SHA256 in a sealed-non-committed provenance file (per the user 2026-05-08 directive that the ledger NOT be committed to the public repo while preserving the audit-trail integrity).
- `P1-ADR-0017-RETROACTIVE-V2-KPI-REPORT-CARD-CASCADE-PRIORITY` — operator decision on the priority order for emitting v2 KPI report cards on H050/H052a/H053/H054 with the new tables 3a/3b/3c.

This ADR is the canonical reference for the SKIE-Universe project's optimization-and-promotion paradigm from 2026-05-08 forward. It supersedes the *de facto* Sharpe-as-primary anchor that emerged from the H050/H052a/H053/H054/H055 design.md §1 statements; the §1 statements themselves are preserved verbatim per ADR-0013 §1-§7 immutability and remain inferentially computable as secondary KPIs.
