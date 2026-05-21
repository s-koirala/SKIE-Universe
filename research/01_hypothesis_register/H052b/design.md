---
name: H052 — HMM regime-gated QQQ first-hour long-call 0DTE scalp
description: Pre-registered design doc for hypothesis H052
type: project
hypothesis_id: H052
tier: 3
status: designed
owner: skoir
created: 2026-04-20
citations:
  - ADR-0003-spa-vs-romanowolf
  - ADR-0004-alpha-and-power-defaults
  - ADR-0005-hmm-regime-toolkit
  - ADR-0006-scope-extension-hmm-0dte
  - de Prado 2018 Advances in Financial Machine Learning (Wiley, ISBN 978-1119482086)
  - Ryou et al. 2020 (doi:10.3390/su12177031)
  - Guidolin-Timmermann 2007 (doi:10.1016/j.jedc.2006.12.004)
  - Andersen-Bollerslev 1998 (doi:10.2307/2527343)
---

# H052 — HMM regime-gated QQQ first-hour long-call 0DTE scalp

Pre-registration for hypothesis H052. Frozen at `designed`.

## 1. Hypothesis

- H0: The Sharpe ratio of the **SKIE-ORB-CALL long-call 0DTE scalp conditioned on the HMM non-stress state** does **not** exceed the Sharpe ratio of the **unconditional SKIE-ORB-CALL scalp**.
- H1: It does. Mechanism: the first-hour directional bias operationalized in the sibling repo (see [`research/00-hypothesis.md`](https://github.com/s-koirala/SKIE-NINJA-0DTE/blob/main/research/00-hypothesis.md) — P(QQQ price at 10:30 > 09:30 open) > 0.50) interacts with the prevailing volatility regime. Long-premium call scalps are long gamma and long delta but **negative theta**; conditioning on a low-vol HMM state filters out high-gamma-decay days on which realized P/L is dominated by theta bleed rather than by the directional bias. Regime gating concentrates exposure on days where the underlying directional edge has room to overcome decay.
- Primary citations: [Ryou et al. 2020, Sustainability 12(17):7031](https://doi.org/10.3390/su12177031); [Guidolin & Timmermann 2007, JEDC 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004); [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Andersen & Bollerslev 1998, Int. Econ. Rev.](https://doi.org/10.2307/2527343); de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1119482086); Zarattini, Galli, Pagani, Saavedra — ORB literature, flagged UNVERIFIED pending primary-source retrieval.
- Test statistic: `T_H052 = SR_{ORB-CALL, HMM-gated} − SR_{ORB-CALL, unconditional}`. **Paired differential.** Enters the Romano-Wolf / SPA family per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md).

Strategy structure is fixed at pre-reg: **long-premium 0DTE/1DTE QQQ calls**, strike ATM–1OTM (delta window 0.40–0.55), entry 10:30–10:35 ET, time stop 14:00 ET, hard close 15:45 ET (per sibling repo `research/03-strategy-architecture.md` and `research/04-data-requirements.md`).

## 2. Universe and sample period

- Instruments: **QQQ spot (primary)** for the underlying directional signal and HMM features; QQQ 0DTE/1DTE calls for execution. NQ/MNQ futures used as an **equity-layer cross-validation** (mapping consistency between QQQ first-hour direction and NQ first-hour direction).
- Frequency: 1-minute bars per sibling repo `research/04-data-requirements.md` (Polygon.io + Databento + FirstRate).
- Session: RTH only; 09:30–16:00 ET.
- Train / validation / test: **IS 2015–2021, OOS 2022–2025** to match sibling repo §3.4. 0DTE contracts on QQQ became daily in 2022; pre-2022 dates use the nearest 1DTE (next-session expiration) call with an explicit structure flag recorded per trade.
- Dataset snapshot frozen at pre-registration: SHA256 of the QQQ 1-min bars 2015–2025 and QQQ option chain 2022–2025, captured in `data_requirements.md` at `status=designed`. Any data after 2025-12-31 is locked away; re-runs on extended windows require a successor hypothesis ID.

Sibling repo [`s-koirala/SKIE-NINJA-0DTE`](https://github.com/s-koirala/SKIE-NINJA-0DTE) (internal project code SKIE-ORB-CALL) is the canonical code path under ADR-0006 Option C. Key sibling artifacts: `CLAUDE.md`, `research/00-hypothesis.md`, `research/03-strategy-architecture.md`, `research/04-data-requirements.md`, `research/06-roadmap.md`. The sibling-repo Phase-1 binomial test (first-hour green-rate > 0.50) is a **precondition** for H052.

### 2.1 Capacity mapping (pre-registered)

Long QQQ calls. Position cap is derived from the retail ceiling **≤40 NQ contracts** (CLAUDE.md / [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md)) mapped via delta-equivalence:

`D_port ≤ 40 × $20 × NQ_index × (QQQ_level / NQ_level) / ρ_{QQQ,NQ}`

where `D_port` = aggregate delta exposure of long-call position in dollars, `$20` is the NQ point multiplier, and `ρ_{QQQ,NQ}` is the training-fold rolling correlation (lower correlation → tighter cap, conservative). Additional per-trade risk cap: **1–2% of account equity per trade** per sibling repo `research/03-strategy-architecture.md §4.2`. The numeric cap is pre-registered in the sibling-repo `config/` (or mirrored into [config/instruments.yaml](../../../config/instruments.yaml) in a follow-up edit); status transition `designed` → `running` is blocked until that number lands.

## 3. Features

HMM emission features (all point-in-time, `as_of` timestamp per row):

- QQQ 1-minute **realized variance** per [Andersen & Bollerslev 1998, Int. Econ. Rev. 39(4):885–905](https://doi.org/10.2307/2527343), rolling lookback CV-selected from a grid.
- **First-hour directional sign** (+1/0/−1) per sibling `research/04-data-requirements.md §4.1`; `as_of = 10:30 ET`.
- **VIX daily level**, `as_of = T−1 close` (CBOE/Yahoo per sibling §4).
- **Gap-size bucket** (discretized open-vs-prior-close log-return) per sibling §3.2 stratification.
- **Day-of-week** one-hot.
- **50-DMA regime** (QQQ close above/below 50-day moving average), `as_of = T−1 close`.

Leakage tests per plan §3 and §4.6; `as_of` strictly ≤ decision timestamp.

## 4. Label construction

Per-trade P/L on the long QQQ 0DTE/1DTE call, following sibling repo `research/04-data-requirements.md §4.2` execution layer:

- **Entry**: 10:30–10:35 ET, strike = ATM–1OTM (delta 0.40–0.55 grid; strike selected by training-fold expected-information-per-dollar).
- **Profit target**: 20–50% premium gain (grid).
- **Stop**: 30–50% premium loss (grid).
- **Time stop**: 14:00 ET.
- **Hard close**: 15:45 ET.
- **Settlement**: intraday option mid or exchange print at exit time; no overnight exposure (0DTE exits same day, 1DTE exits by hard close).
- `pt_sl`: both active (premium-based).
- `vertical_barrier`: 15:45 ET.
- `volatility_estimator`: training-fold realized-variance estimator, lookback CV-selected.

## 5. Estimator

- Model class: Gaussian HMM over QQQ 1-min emission features → per-session binary entry gate on the SKIE-ORB-CALL signal.
- HMM per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md): Gaussian emissions, `covariance_type ∈ {diag, full}`, `n_states` bounded by ADR-0005 adaptive rule (n_states ≤ K s.t. mean within-state N > 30·dim; restart count until top-two LLs within ε = 2·SE(bootstrap EM LL); floor 5 restarts), BIC + CV selection.
- **Canonical state ordering**: states sorted by **emission-variance of QQQ log-return ascending**; non-stress state = state 0 (lowest variance).
- **State assignment at inference time uses the causal forward filter `p(s_t | y_{1:t})` only; smoothed posteriors `p(s_t | y_{1:T})` are diagnostic only and never inform an out-of-sample decision.** A leakage unit test asserts filter output at `t` is a pure function of `y_{1:t}`.
- Gate: enter the long-call trade only when `P(s_t = state_0 | y_{1:t}) > τ`, where `τ` is the training-fold Youden-optimal threshold.
- Hyperparameter grid: realized-vol lookbacks over `{30m, 60m, 120m}`.
- Search protocol: nested walk-forward with random search.
- Loss / metric: HMM log-likelihood for fit; Sharpe-differential for gate.

## 6. Splitter

- `PurgedWalkForwardSplitter` (plan §4.1), nested within the sibling repo's **CPCV** framework (de Prado 2018 ch. 12) and **PBO** overfitting diagnostic.
- `purge`: one trading session (intraday 0DTE horizon).
- `embargo`: Politis-White optimal block length on daily P/L residuals; half-day sessions per [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py); weekend gap treated as embargo-transparent.
- **Multiple-testing correction**: Bonferroni / Holm-Sidak across stratified strata (day-of-week × gap-size × VIX-regime) per sibling §3.4, inherited.

## 7. Cost model

- `cost_model_id`: `qqq_0dte_v1` — to be registered in `src/skie_ninja/backtest/costs/` as a follow-up before `status=running`.
- **Option spread**: $0.01–$0.03 per contract for QQQ calls (sibling `research/04-data-requirements.md §4.2`).
- **Commissions**: retail broker schedule (Alpaca and IBKR per sibling `research/06-roadmap.md` Phase 4); per-contract fee + exchange fees, frozen at pre-reg.
- **Slippage**: bid-ask crossing at entry and exit, walk-forward fit to sibling-repo paper-trade quote snapshots when available; widening-tail explicit.

## 8. Gate thresholds (AMENDED 2026-05-20 per ADR-0017 + ADR-0018; supersedes the 2026-05-03 ADR-0013 amendment, which superseded the 2026-05-01 ADR-0012 amendment)

> **AMENDED 2026-05-20 by [ADR-0017 survival-constrained optimization paradigm](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) §1.2 + §3 + §5 and [ADR-0018 regime-conditional aggressive-growth paradigm](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) §D-1 + §D-2 + §D-3.** Sharpe-family metrics are DEMOTED from primary inferential anchor to secondary KPI; the survival-constrained metric vector (`terminal_wealth_q05`, `calmar_differential`, `profit_factor`, `r_multiple_mean`) replaces Sharpe-differential as the load-bearing operator-review artifact. MPPM(ρ=1) per [GISW 2007 *RFS* DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025) replaces Sharpe in inner-CV fitness. The §1 `T_H052 = SR_{ORB-CALL, HMM-gated} − SR_{ORB-CALL, unconditional}` paired-differential Sharpe test statistic is PRESERVED VERBATIM as a SECONDARY KPI per ADR-0017 §1.2 — it is computed verbatim and reported as a numerical KPI in every H052b KPI report card; what changes is its promotion-decision-rule weight at the §8+§10 layer. H052b execution is in sibling repo [`s-koirala/SKIE-NINJA-0DTE`](https://github.com/s-koirala/SKIE-NINJA-0DTE); this main-repo design.md is the reference document — the sibling repo MUST inherit this amendment per ADR-0006 + ADR-0016 cross-track discipline. Full cascade text + K-1..K-8 kill-switch inheritance per ADR-0017 §5 + per-hypothesis applicability table in Appendix A at the end of this file.
>
> **AMENDED 2026-05-03 by [ADR-0013 permanent-exploration-no-archive-ninjascript-terminus](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).** ADR-0013 dissolves all binding gates: every former Class A item becomes a KPI annotation in the canonical KPI report card per ADR-0013 §3, with methodological-correctness annotation banner per §2.1 (NOT a gate). H052b progresses through the stage progression of ADR-0013 §1; operator promotion at every transition is discretionary on the KPI report card (ADR-0013 §5.3). Full §10 + new §15 NinjaScript Implementation cascade lands under follow-up `P1-ADR-0013-DESIGN-MD-CASCADE`.
>
> **ALL TEXT BELOW THIS BANNER IS HISTORICAL RECORD** preserved verbatim per ADR-0013 §4.1 non-loss mandate (per Round-2 audit F-2-5 remediation). For the current disposition philosophy and authoritative gating semantics see ADR-0013 §1-§5. The legacy "binding gates" / "Class A" / "three-class rubric" / disposition labels referenced below are SUPERSEDED and exist solely for audit-trail provenance.

Per [ADR-0012 disposition-philosophy-aspirational-mvp](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) (now superseded by ADR-0013) (per Round-1 audit F-1-2 + F-1-6 remediations re: applicability), H052b's gating tree is restructured to the three-class rubric:

### 8.a Class A — Binding gates (per-hypothesis applicability)

- **PIT / leakage-canary** (ALWAYS BINDING). Binding test paths: Cycle-4 leak canary suite + per-hypothesis integration test [tests/integration/test_h052b_pit.py](../../../tests/integration/test_h052b_pit.py) to be authored as §11.2 prereq before next H052b launch (tracked under `P1-H052B-PIT-CANARY-INTEGRATION-TEST-LANDED`).
- **Calibration: BSS / reliability** — `applicable: WHERE` for the HMM-state posterior (same as H052a §8.a).
- **Reproducibility log present** (ALWAYS BINDING).
- **DSR/PSR above `dsr_activation_size`** — `applicable: when family ≥ 10`.
- **Hansen SPA family p ≤ α at operator-promotion** per ADR-0012 §"Operator-promotion rule".

### 8.b KPIs (Class B; reported, not binding at design-time)

Sharpe-vs-passive CI, Sharpe-vs-unconditional, SPA family p (KPI at design-time, BINDING at promotion), max-DD ratio, ES at 97.5% (BCBS 2019 FRTB), power margin, HMM-state coverage statistics. Defaults preserved (`alpha=0.05`, `bh_threshold=0.10`, `power_target=0.80`) — KPI-reported only. SPA universe entry preserved per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md). Long-premium structural property recorded as `long-premium-bounded-downside` strength annotation.

The legacy primary gate (Sharpe-differential CI), secondary gate (max-DD non-worse), and ES monitoring metric are all reported in the disposition memo's KPI report card per ADR-0012 §"Class B".

**Note on long-premium specification**: H052b's long-premium structure (long gamma, long delta, negative theta) gives the strategy bounded downside per-position; this property is preserved as a strength annotation in the KPI report card under ADR-0012 §"Class B" (`long-premium-bounded-downside`).

## 9. Stopping rule

- CPCV `n_groups` selected per de Prado 2018 §12 rule. **CPCV becomes BLOCKING-BEFORE-DISPOSITION per ADR-0012 §"Cross-validation methodology"**; `P1-BACKTEST-CPCV` full path-reconstruction follow-up is the load-bearing implementation.
- Random search budget `N_draws = 200` per [Bergstra & Bengio 2012, JMLR 13:281–305](https://www.jmlr.org/papers/v13/bergstra12a.html).
- Max-iter EM = 500; tol = 1e-4.
- Max wall-clock: 72 hours.
- HMM stationarity pre-check failure per ADR-0005 → `prerequisite-not-met` (Class A.4 per ADR-0012), not `archived(null, precondition-failed)`.

## 10. Decision rule (AMENDED 2026-05-20 per ADR-0017 + ADR-0018; supersedes the 2026-05-01 ADR-0012 amendment)

> **AMENDED 2026-05-20** per [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md). The H052b decision rule is restructured to the survival-constrained metric vector + MPPM(ρ=1) inner-CV fitness layer. Operator review of the canonical ADR-0014 §3.2 13-table KPI report card is the load-bearing artifact. The legacy §1 T_H052 Sharpe-differential statistic is preserved verbatim as a SECONDARY KPI. The sibling-repo SKIE-ORB-CALL Phase-1 binomial pre-condition remains BINDING as a `prerequisite-not-met` Class A condition per ADR-0013. The long-premium structural property `long-premium-bounded-downside` is preserved as a KPI annotation. Per ADR-0013 §5.3 + the user 2026-05-04 standing decline-ninjascript directive, the `kpi-report-emitted` → `ninjascript-implemented` transition is operator-discretionary. Full cascade text + per-hypothesis applicability in Appendix A.

The H052b decision rule is restructured per [ADR-0012 §"Disposition labels under the new rubric"](../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md) into the three-class disposition rubric (`leakage-detected` / `reproducibility-incomplete` / `calibration-failed` / `prerequisite-not-met` / `archive(complete; KPI report)`). All Sharpe / SPA / power / max-DD outcomes are now Class B KPIs reported in the disposition memo's report card; they do NOT null the strategy.

The **sibling-repo SKIE-ORB-CALL Phase-1 binomial pre-condition** remains binding as a `prerequisite-not-met` (Class A.4 per ADR-0012). Capacity breach is preserved as a `capacity-binding` annotation on the disposition (now operational, not a null verdict).

## 11. Reproducibility commitments

- git HEAD: TBD at run (across this repo and the sibling repo [`s-koirala/SKIE-NINJA-0DTE`](https://github.com/s-koirala/SKIE-NINJA-0DTE)).
- `uv pip freeze` sha: TBD at run.
- RNG seed: 20260422.
- Dataset checksums: frozen in `data_requirements.md` — pre-reg companion to be completed before `status=running`; its SHA256 checksum field is the binding artifact. QQQ spot + QQQ option chain vendor + snapshot date recorded (Polygon.io / Databento / FirstRate; CBOE/Yahoo for VIX).
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json`.
- **Precondition evidence path**: sibling-repo artifact `results/phase1_first_hour_green_rate-YYYYMMDD.json` (binomial test outcome) must exist and pass before H052 transitions `designed` → `running`.

## Appendix A — ADR-0017 + ADR-0018 cascade amendment (2026-05-20)

Per the BLOCKING-BEFORE-NEXT-STAGE-3-RUN follow-ups `P1-ADR-0017-DESIGN-MD-CASCADE` + `P1-ADR-0018-DESIGN-MD-CASCADE`, this appendix is the load-bearing reference for the 2026-05-20 amendment of §8 + §10 + §11.1 per Path A frozen-pre-reg amendment discipline ([ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Frozen pre-registration amendment"). §1-§7 are PRESERVED VERBATIM. The §1 `T_H052 = SR_{ORB-CALL, HMM-gated} − SR_{ORB-CALL, unconditional}` paired-differential Sharpe statistic is preserved as a SECONDARY KPI computed and reported verbatim in every KPI report card. H052b execution is in sibling repo [`s-koirala/SKIE-NINJA-0DTE`](https://github.com/s-koirala/SKIE-NINJA-0DTE) — the sibling repo MUST inherit this amendment per ADR-0006 + ADR-0016 cross-track discipline.

### A.1 Primary inferential vector (replaces Sharpe-differential at §8+§10 layer)

Per [ADR-0017 §1 + §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md), the load-bearing operator-review artifact becomes the survival-constrained metric vector with bootstrap CIs:

| Primary metric | Definition (per ADR-0017 §3) | KPI annotation grammar |
|---|---|---|
| `terminal_wealth_q05` | 5th percentile of 252-session bootstrap-forward $10K ending equity | `tw-q05-{above-baseline, above-half, below-half, below-quarter}` |
| `calmar_differential` | `Calmar_arm − Calmar_bench`; paired-pairs block-stationary-bootstrap CI per [Politis-Romano 1994](https://doi.org/10.1080/01621459.1994.10476870) | `calmar-diff-{positive, marginal, negative}` |
| `profit_factor` | `gross_profit / gross_loss` per arm | `pf-diff-{positive, marginal, negative}` |
| `r_multiple_mean` | Per-trade R-multiple mean of distribution | `r-multiple-mean-{positive, marginal, negative}` |

Inner-CV fitness becomes **MPPM(ρ=1)** per [ADR-0018 §D-1](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md). Sharpe-family LW2008 differential CI + Hansen 2005 SPA p preserved as secondary KPIs at their existing ADR-0014 §3.2 table positions. The long-premium structural property is preserved as a `long-premium-bounded-downside` KPI annotation per §8.b.

### A.2 Inner-CV fitness — MPPM(ρ=1)

For H052b hyperparameter selection across the realized-vol lookback `{30m, 60m, 120m}` + delta window `0.40-0.55` (strike-selection grid) per §3 + §4, fitness is **MPPM(ρ=1)** on per-session-aggregated log-return basket NOT Sharpe-differential. Kelly multiplier grid `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per ADR-0018 §D-2 with the additional ADR-0001 capacity ceiling `D_port ≤ 40 × $20 × NQ_index × (QQQ_level / NQ_level) / ρ_{QQQ,NQ}` per §2.1 delta-equivalent cap. BOCD decay detector per ADR-0018 §D-3.

### A.3 K-1..K-8 kill-switch inheritance (per ADR-0017 §5)

H052b is a 0DTE/1DTE long-premium QQQ-call strategy. K-1..K-8 applicability differs from the futures-leg H050/H051/H052a/H053/H054 patterns:

| # | Constraint (ADR-0017 §5) | H052b applicability |
|---|---|---|
| K-1 | Per-trade $-stop = 1.0R; `k=2.0` (Turtle 2N) | applicable; PT 20-50% premium gain + SL 30-50% premium loss per §4 implement the contract on premium-scale rather than price-scale. |
| K-2 | Per-trade time-stop = 2× median winning-trade duration | applicable; 14:00 ET time-stop + 15:45 ET hard-close per §4. |
| K-3 | No-add-to-loser | applicable; single-position-per-session convention. |
| K-4 | Per-symbol position cap per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) | applicable; delta-equivalent cap `D_port ≤ 40 × $20 × NQ_index × (QQQ_level / NQ_level) / ρ_{QQQ,NQ}` per §2.1. |
| K-5 | Correlated-instrument inventory cap | applicable; QQQ-call delta + any concurrent NQ/MNQ futures position is implicitly correlated (both equity-index directional). v1 H052b runs standalone — K-5 becomes load-bearing if a future amendment co-deploys with H052a/NQ futures. |
| K-6 | Daily circuit breaker = -2% equity | applicable; runtime layer per ADR-0025 §D-1. |
| K-7 | Weekly circuit breaker = -5% equity | applicable; same. |
| K-8 | Adverse-direction entry filter | applicable-by-existing-gate; HMM forward-filter at §5 (`P(s_t = state_0 | y_{1:t}) > τ` for long-call entry) IS the trend gate; K-8 spec structurally satisfied. |

Long-premium structural property (`long-premium-bounded-downside`) provides built-in K-1 enforcement per option-premium-bounded-loss semantics — the per-position loss is bounded by the initial premium paid, naturally implementing a 1.0R-stop interpretation. This is preserved as the existing `long-premium-bounded-downside` annotation under §8.b.

Kill-switch enforcement-mode per [ADR-0028 §D-1](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) — `block` default; `size_down` operator-opt-in.

### A.4 §11.1 Kill-switch parameters (NEW; sibling-repo SKIE-ORB-CALL MUST inherit)

NinjaScript implementation kill-switch parameters (used at paper-trade-active and live stages):

- `K-1 per-trade $-stop` per §4 PT 20-50% + SL 30-50% premium barriers (1.0R = premium-scale; structurally bounded by long-premium per the §8.b `long-premium-bounded-downside` annotation).
- `K-2 per-trade time-stop` = 14:00 ET per §4 + hard-close 15:45 ET.
- `K-3 no-add-to-loser`: enforced at sizing layer.
- `K-4 per-symbol position cap` = delta-equivalent per §2.1 `D_port ≤ 40 × $20 × NQ_index × (QQQ_level / NQ_level) / ρ_{QQQ,NQ}`.
- `K-5 correlated-instrument inventory cap`: aggregate QQQ-call delta + concurrent NQ/MNQ futures position ≤ 1.0× the largest single-instrument cap when co-deployed.
- `K-6 daily circuit breaker` = -2% equity.
- `K-7 weekly circuit breaker` = -5% equity.
- `K-8 adverse-direction entry filter`: satisfied by HMM gate per §5.

Calibrated post-paper-trade under sibling-repo follow-up `P1-H052B-KILL-SWITCH-EMPIRICAL` (to be registered in sibling repo).

### A.5 Revision-log

| Date | Amendment | Cross-reference |
|---|---|---|
| 2026-04-20 | Initial design.md commit, `status: designed` (renamed from H052 to H052b 2026-04-23) | git history initial commit |
| 2026-05-01 | §8 + §10 amended per ADR-0012 (superseded) | Phase D ADR-0012 amendment |
| 2026-05-03 | §8 + §10 amended per ADR-0013 (KPI-only) | [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) + Phase F |
| 2026-05-20 | §8 + §10 + §11.1 amended per ADR-0017 + ADR-0018 (this Appendix A); §1-§7 preserved verbatim; T_H052 secondary KPI; sibling-repo MUST inherit | [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) + Phase O.19 audit trail at [docs/audits/audit_trail_2026-05-20_adr-0017-0018-design-md-cascade.md](../../../docs/audits/audit_trail_2026-05-20_adr-0017-0018-design-md-cascade.md) |

### A.6 §1-§7 immutability assertion

Per [ADR-0013 §"Frozen pre-registration amendment"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): §1-§7 are IMMUTABLE under project-level ADR amendments. This 2026-05-20 cascade amends ONLY §8 + §10 + §11.1. The §1 H_1 `T_H052 = SR_{ORB-CALL, HMM-gated} − SR_{ORB-CALL, unconditional}` paired-differential test statistic and the §1 mechanism statement (long-premium + long-gamma + long-delta + negative-theta; HMM-gating filters high-gamma-decay days) are PRESERVED VERBATIM. The sibling-repo SKIE-ORB-CALL Phase-1 binomial precondition remains BINDING as a `prerequisite-not-met` Class A condition per ADR-0013 + ADR-0006 cross-track discipline.
