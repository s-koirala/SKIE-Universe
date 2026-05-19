---
hypothesis_id: H067
schema_version: hypothesis_design_v1
status: designed
tier: 2c
created: 2026-05-19
created_by: skoir
description: Cost-light genetic successor of H065 v2 M_inf-SIL cell — preserves Donchian-channel + first-fire dwell + ATR-stop + ID_1 trend gate + no-TP-overlay signal-generation mechanic verbatim; varies position size from 1-lot to N-lot ∈ {1, 2, 3, 4, 5} per ADR-0001 retail capacity ceiling to probe whether N-lot sizing (combined with paper-trade-empirical slip + tier-based commission discount) shrinks the cost-friction-breakeven ratio from the parent's 1.04 above the cost-friction-dominated-edge-present threshold.
---

# H067 — Cost-light Donchian channel-breakout on SIL standalone, with N-lot position-size grid as primary cost-reduction axis

> **Genetic successor of [H065 v2 M_inf-SIL cell](../H065/H065_kpi_report_v2.md).** H067 preserves every mechanical layer of the H065 v2 M_inf no-TP-overlay variant on SIL (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; current-equity rebase per ADR-0017 §4.1; Kelly multiplier grid per ADR-0018 D-2; let-it-run on Donchian channel break/reverse + ATR stop + EOD-flatten) **verbatim** and adds **ONE** new mechanic: an N-lot position-sizing grid `N ∈ {1, 2, 3, 4, 5}` contracts capped at the ADR-0001 retail capacity ceiling for SIL (= 5 contracts per H062/H065 design.md §11.1 K-4 binding).
>
> **Hypothesis-of-record (H_1)**: under N-lot sizing within ADR-0001 retail capacity AND post-Phase-O.13 cost-realistic operation (conservative_prior cost model per ADR-0025 §D-3), there exists an `N* ∈ {1, 2, 3, 4, 5}` such that the realized OOS basket SIL ROI ≥ 0% with stationary-bootstrap CI excluding zero positively on per-session log-return MPPM(ρ=1). The cost-friction-breakeven ratio at `N*` rises above the [cross-hypothesis investigation 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md) §6.3 cost-friction-dominated-edge-present ratio ≥ 2 threshold AND zero-cost A0 reference > 0 hold simultaneously.
>
> **Honest pre-empirical caveat on the N-lot mechanism**: under the canonical [nt8_realistic_v1 conservative_prior](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) cost model, commission + slippage BOTH scale linearly with `n_contracts` per [src/skie_ninja/backtest/costs/nt8_realistic.py:225-227](../../../src/skie_ninja/backtest/costs/nt8_realistic.py); position size also scales linearly. The bps-of-equity ratio (cost ÷ notional × leverage) is therefore approximately invariant under N-lot scaling at the conservative_prior. **The N-lot cost-reduction mechanism is conditional on TWO empirical refinements over conservative_prior that are independently load-bearing**: (a) sub-1-tick empirical slippage at retail-tier SIL liquidity (cross-hypothesis investigation §7.2 anticipates 0.3-0.7 tick on equity-index micros; SIL retail liquidity at sub-100-contract sizes is anecdotally similar but unverified); (b) volume-tier-based commission discount per the existing [config/instruments.yaml fee_tiers_es_nq](../../../config/instruments.yaml) table convention (the metals/energy schedule lacks this table at adoption time; CME Metals VIP tier discount may apply at ≥ 1000 contracts/month — partial-month metals trading at N=5 over ~5,600 SIL trades/year reaches ~28,000 contracts/year, well above any reasonable monthly tier threshold). The H_1 inferential criterion above is operationally evaluable ONLY under the `paper_trade_empirical` cost-calibration path; the v1 conservative_prior emission will report the **structural sensitivity** of the per-cell ratio to N-lot scaling under the canonical prior + the **explicit operator-actionable diff** between conservative_prior bps-of-equity and the slip-reduction-multiplier needed to cross the breakeven threshold.
>
> **Full Phase N + Phase O.0 + Phase O.4 + ADR-0024 + Phase O.15 paradigm inheritance.** H067 inherits the same paradigm stack as H065 + the post-2026-05-15 Phase O.15 amendments: [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) permanent-exploration / no-binding-gates / mandatory-NinjaScript-terminus / non-loss preservation + [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) canonical 13-table results-summary + [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained primary metric vector + K-1..K-8 kill switches + FM-1..FM-5 stress-test suite + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) inner-CV fitness + Kelly-multiplier grid + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness annotation + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism §1.3 annotation + [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate + [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) opt-in framing + [ADR-0025](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) abandonment-trigger primitives + [ADR-0026](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) §0 3-component KPI summary header + promising-* annotation + [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) cell-budget cap + walk-forward-window-as-bounded-set + genetic-successor §17 discipline + [ADR-0028](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) K-6/K-7 size-down enforcement-mode + cost-friction-dominated-edge annotation.
>
> **Out of scope at v1 (alternate cost-reduction axes deferred per single-axis ADR-0027 §D-4 discipline)**: bar-cadence reduction (mechanism 2; daily / 4-hour bars rather than 5-min) deferred to `P1-H067-V2-COST-REDUCTION-AXIS-2-BAR-CADENCE`; longer-hold-time variant (mechanism 3; extended hold-time-cap) deferred to `P1-H067-V2-COST-REDUCTION-AXIS-3-LONGER-HOLD`. These are mechanically orthogonal and warrant independent v2 pre-registrations per ADR-0027 §D-4 single-axis-genetic-cross discipline.

## 1. Hypothesis

- **H_0**: For every `N ∈ {1, 2, 3, 4, 5}`, AT LEAST ONE of: (a) realized SIL OOS ROI < 0% under conservative_prior cost-model, OR (b) basket MPPM(ρ=1) stationary-bootstrap CI covers zero, OR (c) cost-friction-breakeven ratio < 2 (i.e., per-trade gross-edge insufficient to dominate per-trade cost burden at conservative_prior calibration).
- **H_1**: There exists an `N* ∈ {1, 2, 3, 4, 5}` such that (a) realized SIL OOS ROI > 0% under conservative_prior, (b) basket MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero positively, AND (c) cost-friction-breakeven ratio ≥ 2 — qualifying the cell for `cost-friction-dominated-edge-present` per ADR-0028 §D-2. The recommended `N*` (operator-discretionary) is the smallest N satisfying all three conditions, on Pareto-front interpretation: smaller N preserves the [ADR-0001 retail capacity reserve](../../../docs/decisions/ADR-0001-project-scope.md) for cross-strategy meta-portfolio allocation per [ADR-0020 meta-portfolio orchestrator](../../../docs/decisions/ADR-0020-meta-portfolio-orchestrator.md).
- **Predictand**: same as H065 — per-trade R-multiple `R_t = realized_PL_t / |1R_t|` per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py); per-session-aggregated SIL log-return series for MPPM(ρ=1) per design.md §1 of H062. **SIL standalone, NOT 4-symbol basket** — the cell-genetic-cross isolates SIL specifically because the cross-hypothesis investigation 2026-05-19 §6.3 identified SIL M_inf-current as the strongest standalone cell across the entire emitted-KPI inventory (+734.68% pre-cost OOS, 5,600 trades, breakeven ratio 1.04 — barely above unity, signal that cost-light variant could push it above the cost-friction-dominated-edge-present threshold).
- **Test statistic** (load-bearing): per-N-cell `T_H067(N) = MPPM(ρ=1)[r_SIL_OOS_session_aggregated(N)]` where the simulator is re-run with N-lot sizing and otherwise-identical mechanics. Family size at the SIL standalone level = 5 cells (one per N value); per-N-cell-per-Kelly-multiplier family = 5 × 6 = 30 under [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER family-wise correction. **N=1 reported alongside as the H065 v2 M_inf-SIL parent baseline** for direct comparability to the cross-hypothesis investigation §6.1 ratio-1.04 anchor.
- **Secondary inferential KPIs** (per ADR-0017 §1.2 demotion machinery): Sharpe-differential vs passive-long SIL under [Ledoit-Wolf 2008 *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap CI; Hansen 2005 SPA p reported as KPI annotation per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md); Calmar-differential + profit-factor + R-multiple-mean per [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md).

### 1.2 Cost-friction-dominated-edge annotation (per ADR-0028 §D-2)

H067 v1 SHALL emit explicit zero-cost A0 reference cells alongside conservative_prior A1 cells at the same N × Kelly-multiplier grid to enable the `cost-friction-dominated-edge-{present, absent, n/a}` annotation per ADR-0028 §D-2 trigger semantics. The v1 KPI report card §"Methodological-correctness annotations" line carries the annotation per-cell as the load-bearing operator-readable disclosure.

The annotation grammar:
- `cost-friction-dominated-edge-present` (per-N-cell) — realized OOS SIL ROI > 0 at A0 zero-cost AND realized OOS SIL ROI < 0 at A1 conservative_prior AND cost-friction-breakeven ratio computed per cross-hypothesis investigation §2 ≥ 2.
- `cost-friction-dominated-edge-absent` — A1 cell does NOT flip the realized OOS from positive to negative.
- `cost-friction-dominated-edge-n/a` — only PRE-cost A0 cell emitted (no cost-model context).

### 1.3 Causal-mechanism annotation (per ADR-0022)

- **Claim type**: `hybrid` (inherits H065's causal mechanism on the channel-break-as-information-event signal layer; N-lot sizing layer is **correlation-only refinement** on top of the inherited mechanism). <!-- justify: ADR-0022 §3 grammar; signal mechanism preserved verbatim from parent H065 + H062 design.md §1.3 hybrid framing; sizing layer is a parameterization-tuning question with no theoretical anchor in the underlying microstructure mechanism -->
- **Mechanism description (who/what/why/when)** — inherits H065 design.md §1.3 verbatim for the upstream signal mechanism:
  - **Who**: market participants on COMEX Micro Silver (SIL) front-month contract during 24/5 ETH + RTH sessions.
  - **What**: Donchian-channel break is an information-revelation event — bar t close beyond N-bar high/low signals that prior-range-extreme has been exceeded.
  - **Why**: [Hong-Stein 1999 *J Finance* 54(6):2143-2184 DOI 10.1111/0022-1082.00184](https://doi.org/10.1111/0022-1082.00184) underreaction mechanism (slow information diffusion across market participants) + [Bouchaud-Gefen-Potters-Wyart 2004 *Quantitative Finance* 4(2):176-190 DOI 10.1088/1469-7688/4/2/007](https://doi.org/10.1088/1469-7688/4/2/007) stop-order liquidity clustering at multi-bar pivots (channel-extreme touches induce stop-loss cascades that prolong the move beyond the breakout bar).
  - **When**: PIT-causally at bar t close + entry at bar t+1 open per H062 + H065 design.md §4 fill convention.
- **N-lot sizing layer is correlation-only**: no causal claim about which N is "the true position size". N is grid-searched per §5; the recommended N* per H_1 is operator-discretionary per the Pareto-front above.
- **E-value / robustness anchor**: per ADR-0022 §3 the [VanderWeele-Ding 2017 *Ann Intern Med* 167(4):268-274 DOI 10.7326/M16-2607](https://doi.org/10.7326/M16-2607) E-value primitive at [src/skie_ninja/inference/e_value.py](../../../src/skie_ninja/inference/e_value.py) is closed (Phase O.1 follow-on). H067 KPI report card v1 carries the E-value annotation against the H065 v2 M_inf-SIL parent at the same substrate-vintage.

### 1.4 Pre-empirical caveat: H067 is a cost-light variant of a marginal-mean-edge factor

H067 inherits H065's §1.4 partial-decay caveat verbatim with one addition: the H065 v2 M_inf-SIL parent cell's cost-friction-breakeven ratio is **1.04** per the cross-hypothesis investigation 2026-05-19 §6.1 (13.12 bps-of-equity per-trade gross-edge vs 12.64 bps-of-equity round-trip cost at conservative_prior). This is **at-the-margin** under the canonical cost model — a modest empirical-cost reduction (e.g., 50% slip-component shrinkage from 1-tick to 0.5-tick per the cross-hypothesis investigation §7.2 anchored on practitioner anecdotes about retail-tier liquid-contract slippage) yields disproportionate outcome change because the compounding gross edge × 5,600 trades is multiplicative.

**H062 v3 ablation as the load-bearing case-study**: the [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) memo establishes that cost-only at conservative_prior drives basket OOS from +261.88% (A0) to −99.99997% (A1) on IDENTICAL trades. The H067 v1 design.md §1 question is the structurally-symmetric inverse: can N-lot sizing (combined with paper-trade-empirical slip reduction per §6.3 forward path) push the per-cell ratio from 1.04 upward enough that the A0 → A1 saturation-to-bankruptcy mechanism is structurally averted?

**Expected H065-relative effect of N-lot scaling at conservative_prior** (pre-empirical; not load-bearing):
- **Larger N** (N=2, 3, 4, 5) → per-trade gross-edge bps-of-equity AND per-trade cost bps-of-equity scale linearly → cost-friction-breakeven ratio at conservative_prior **invariant** under the canonical prior. The H_1 inferential question is whether (a) tier-based commission discount kicks in at N × n_trades > tier threshold, OR (b) empirical sub-1-tick slippage applies at retail-tier liquid SIL — both push the bps-of-equity slip component down by 30-70%, lifting the ratio.
- **No N cell expected to dominate** under conservative_prior alone — operator review on the Pareto-front (smallest N satisfying ratio ≥ 2 AND MPPM CI strict-positive) is the load-bearing decision.

### 1.5 Pre-empirical caveat on SIL standalone vs basket framing

Inherits H062 design.md §1.5 verbatim with adjustment for SIL-only scope. SIL-only has effective basket breadth = 1 (no diversification). The H_1 inferential question is cell-conditional, NOT basket-aggregate; SPA family size at v1 = 5 N-cells × 6 Kelly-multipliers = 30 (per §1 above). Family-wise correction per Romano-Wolf 2005.

## 2. Universe and sample period

- **Instrument at v1**: SIL (Micro Silver; COMEX-on-CME-Globex; 1000 troy oz; tick_size 0.005 → tick_value $5.00 per [config/instruments.yaml](../../../config/instruments.yaml)). **SIL standalone, NOT 4-symbol basket** per §1 above.
- **Cross-asset diversification deferred**: 4-symbol basket framing (ES + NQ + MGC + SIL) inherited from H062/H065 deliberately omitted at v1 to isolate the SIL cell-grid mechanic. Cross-asset extension tracked under `P1-H067-V2-CROSS-ASSET-BASKET-EXTEND` (non-blocking).
- **Substrate availability** (BINDING; canonical post-Phase-O.10 substrate on main HEAD):
  - **Verified `output_frame_sha256`**: `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) per CLAUDE.md Phase O.10 substrate re-derivation (run_id `38d63bdd2def4fa9804c78fbcb1a76ce`). Includes the H1-2026 extension through 2026-05-15 + 2026-Q2-extension through 2026-05-15.
  - **SIL coverage per provenance**: 2015-01-01 → 2026-05-15 (≥ 11 partitions). Total H067 v1 universe = 1 symbol × 11+ partitions.
- **Sample window** (BINDING; pre-reg-frozen):
  - **Calibration holdout**: 2015-01-01 → 2019-12-31 (SIL only; 5 years).
  - **IS**: 2020-01-01 → 2023-12-31 (4 years; matches H065 v2 IS window).
  - **OOS test**: 2024-01-01 → 2026-05-15 (~2.5 years; matches H065 v2 OOS window).
  - **2026-04-01 → 2026-05-15 sub-window**: mandatory reporting cell per ADR-0026 §D-1 §0 3-component summary header (component 2 — Realized OOS 2026-onward sub-window).
- **Cadence**: 5-minute bars primary (inherited from H062/H065 v1 modal cell). <!-- justify: 5-min is the H065 v2 M_inf-SIL parent cell's modal cadence per H065 design.md §5 + H065 KPI report card §8; preserved verbatim per ADR-0027 §D-4 single-axis-genetic-cross discipline (N-lot is the axis; cadence is preserved infrastructure) -->
- **Session policy**: SIL is 24/5 metals with 16:00-17:00 CT maintenance break (per [config/instruments.yaml SIL session_eth: 17:00-16:00](../../../config/instruments.yaml)); EOD-flatten at 15:55 CT per H062 + H065 metals convention.
- **Roll treatment**: per-asset roll-adjusted front-month continuous series per [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) post-Phase-O.0 deliverable. Inherited from H062.
- **Cost model — TWO cells at v1 per ADR-0028 §D-2 zero-cost-A0-reference convention**:
  - **A0 (zero-cost reference)**: emitted for each (N × Kelly-multiplier) cell; annotation `cost-zero`. Required by ADR-0028 §D-2 for cost-friction-dominated-edge annotation evaluation.
  - **A1 (conservative_prior)**: emitted for each (N × Kelly-multiplier) cell; annotation `cost-conservative-prior` per ADR-0025 §D-5; cost-model `nt8_realistic_v1` per [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) with `sensitivity_mult=1.0` default 1-tick slip + per-symbol fee schedule.
  - Paper-trade-empirical calibration deferred to `P1-H067-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED stage transition; not blocking v1 emission).

**Critical risk to v1 substrate validity** — per cross-hypothesis investigation §6.2 caveat #3 + ADR-0023 §6 + `P1-METALS-ENERGY-CME-FEE-VERIFY`: the SIL cost-model placeholder commission ($0.85/side) + exchange fee ($0.45/side) per [config/instruments.yaml SIL](../../../config/instruments.yaml) are **NOT primary-source-verified against CME Energy/Metals fee schedule**. The empirical realistic cost may be 20-50% **HIGHER** than the placeholder figures. Substrate impact on H067 v1 KPI emission: the reported `cost-friction-breakeven` ratio is an OPTIMISTIC LOWER BOUND if placeholder under-states actual cost; the ratio under verified CME fees could shift the cell-conditional verdict from `cost-friction-dominated-edge-present` to `-absent` at the upper end. Tracked as new BLOCKING follow-up per §11.2.

## 3. Features

H067 inherits **every feature** from H062 design.md §3 verbatim per the H065 §3 precedent (inheritance chain: H062 → H065 → H067 single-axis cross). No new feature is introduced — N-lot sizing is a position-size-layer extension at §5, not a feature at §3.

- Donchian channel (close-to-close N-bar high/low; PIT-causal at bar-(t-1)) at channel_n = 120 (H065 v2 M_inf-SIL parent modal cell).
- ATR Wilder (atr_n = 14; H065 modal).
- Trend-strength filter ID_1 = "a_ts_mom" with L=60, τ=1.0 (H065 modal).
- News-time exclusion features (FOMC ±15min; NFP ±5min; CPI ±5min per [src/skie_ninja/utils/news_calendar.py](../../../src/skie_ninja/utils/news_calendar.py)).

Feature factory at [src/skie_ninja/features/h062/](../../../src/skie_ninja/features/h062/) is **reused verbatim** for H067. No new feature module is added.

## 4. Label construction

H067 inherits H065 design.md §4 verbatim WITH `M = ∞` fixed (no TP overlay; let-it-run on Donchian channel break/reverse). Per the H065 KPI report card §1 finding that the M=∞ no-TP variant was the strongest standalone cell (SIL +734.68% pre-cost OOS at 5,600 trades; MPPM CI [+0.087, +0.459] EXCLUDES ZERO POS in H065 v2 fixed-rebase variant), the M=∞ specification is the load-bearing parent cell preserved verbatim.

Per-trade P/L on a Donchian-channel-breakout signal with ATR-scaled stop + **NO profit target** + opposite-channel exit + EOD-flatten.

- **Entry**: same as H062 + H065. Limit-or-market order at the next bar (t+1) open, conditional on (i) channel-break detector fires at bar-t close, (ii) ID_1 trend-strength filter admits the side, (iii) bar t+1 is in the eligible-bar set.
- **No profit target** (M = ∞ binding per parent-cell preservation): position runs to channel-reverse OR ATR-stop OR EOD-flatten.
- **Stop**: `SL_long = entry - k_atr × ATR_n,t`; `SL_short = entry + k_atr × ATR_n,t` (k_atr = 2.0 fixed per H065 modal).
- **Time stop / EOD flatten**: 15:55 CT per metals convention.
- **Opposite-channel exit**: channel-flip in same bar closes position at bar's close.
- **Exit precedence within bar** (BINDING; PIT-resolved):
  1. **Gap-through-stop** at bar-t open (open beyond SL): close at open.
  2. **Stop hit** during bar (low ≤ SL_long or high ≥ SL_short): close at SL price.
  3. **Opposite-channel break** at bar-t close (channel signal flips against position): close at bar-t close.
  4. **EOD flatten** at session-cutoff bar: close at bar-t close.
  5. **Session rollover** (next bar's session differs): close at bar-t close.

**N-lot sizing — NEW relative to H065** (the genetic-cross axis per ADR-0027 §D-4):

Position size at entry = `N × 1 contract` where `N ∈ {1, 2, 3, 4, 5}` is the grid axis declared in §5 below. The N-lot multiplier is applied at the per-trade-entry sizing step, BEFORE the Kelly-multiplier × current-equity rebase per ADR-0017 §4.1.

`adjusted_position_size = min(N × kelly_multiplier × kelly_fraction × current_equity / (entry_price × multiplier), N × retail_capacity_ceiling_SIL)`

where `retail_capacity_ceiling_SIL = 5` per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) + H062/H065 design.md §11.1 K-4 binding.

**Critical**: the **maximum effective position size** is the ADR-0001 retail capacity ceiling of 5 contracts. At N=5, the cell is operating at the maximum-allowable retail-tier exposure. The Kelly-multiplier-derived component may further constrain position size DOWN from the N-lot grid value (e.g., at quarter-Kelly × $10K equity × SIL median 1R-cost ~$200, the Kelly-derived ceiling may be 1-2 contracts even at N=5). The simulator emits the **realized N_realized** (clipped to min of grid-N and Kelly-derived-N) per fold for the sidecar.

**R-multiple definition** (per H062 §4 + Tharp 1998 *practitioner*): R = realized_PL / |1R| where |1R| = k_atr × ATR_n,t × multiplier × **N_realized**. The R-multiple is **per-trade-unit**, not per-position; multi-contract trades realize R-multiple proportional to N_realized.

## 5. Estimator

H067 inherits H062 design.md §5 verbatim with one extension at §5.2: the N-lot grid replaces the M-cell grid as the joint inner-CV cell selection axis (per ADR-0027 §D-4 single-axis-genetic-cross discipline).

- **§5.1 ID_1 trend-identifier**: FIXED at `a_ts_mom` with L=60, τ=1.0 per H065 v2 modal (no inner-CV selection; preserved infrastructure per ADR-0027 §D-4).
- **§5.2 N-lot + Kelly-multiplier selection** (NEW genetic axis): per-cell MPPM(ρ=1) on inner-CV out-of-fold per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1. **NEW joint grid**: `N ∈ {1, 2, 3, 4, 5}` × `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per ADR-0018 D-2 = **30-cell joint grid**.
- **§5.3 Kelly-multiplier grid**: same as H062 + H065. `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per ADR-0018 D-2; super-Kelly cells `{1.5, 2.0, 2.5}` carry mandatory `super-kelly-operator-discretionary` annotation per ADR-0018 §D-2.
- **§5.4 BOCD signal-decay monitor**: same as H065 v2. Adams-MacKay 2007 BOCD on per-fold MPPM(ρ=1) path; hazard rate 1/100. Per ADR-0025 §D-4 the BOCD-live primitive may be enabled via design.md §11.1 opt-in declaration (not active at v1 per the parent-cell preservation discipline; deferred to v3 cycle).
- **§5.5 Switching-bandit allocation redirect**: deferred to v2/v3 successor (inherited deferral from H065 design.md §5.5; not in v1 scope).
- **§5.6 Walk-forward outer CV**: same as H062/H065. Rolling 252-session-train / 60-session-test; embargo 2400 min. <!-- justify: 252-session train per ADR-0027 §D-2 bounded set {63, 126, 252, 504}; preserved from H065 v2 parent cell -->
- **§5.7 Inner-CV selection metric**: MPPM(ρ=1) per ADR-0018 D-1 (Sharpe forbidden as inner-CV fitness post-2026-05-12 per ADR-0018 acceptance + ADR-0027 §D-2 reaffirmation).
- **§5.8 Inner-CV regularisation discipline + nested-CV structure**: Level-A (ID_1) fixed (no fitting); Level-B (N × Kelly) joint inner-CV per Varma-Simon 2006.

**Joint inner-CV cell grid cardinality** (BINDING per ADR-0027 §D-2 cell-budget cap declaration):

| Axis | Grid | Cells |
|---|---|---:|
| N-lot | {1, 2, 3, 4, 5} | 5 |
| Kelly multiplier | {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} | 6 |
| Cost-model arm (A0/A1) | {cost-zero, cost-conservative-prior} | 2 |
| **Total** | | **60** |

H067 v1 cell-budget = 60 cells. <!-- justify: well under the ADR-0027 §D-2 v1 cap of 1000 cells; full grid sweep is operationally tractable. The 2× cost-model arm multiplier is mandatory per ADR-0028 §D-2 zero-cost-A0-reference convention -->

## 6. Cost model

Two-arm emission at v1 per ADR-0028 §D-2 + §1.2 above:
- **A0**: `cost-zero` — zero-cost adapter per ADR-0025 §D-5 grammar.
- **A1**: `cost-conservative-prior` — `nt8_realistic_v1` per [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) with `sensitivity_mult=1.0` (1-tick slip prior) + per-SIL fee schedule (commission $0.85/side + exchange $0.45/side + NFA $0.02/side = $1.32/side fixed-per-side per [config/instruments.yaml SIL](../../../config/instruments.yaml); slip $5.00/side at 1-tick × $5.00 tick value; total $6.32/side = $12.64 round-trip per 1 contract; both commission AND slip scale linearly with `n_contracts` per [nt8_realistic.py:225-227](../../../src/skie_ninja/backtest/costs/nt8_realistic.py)).

**CRITICAL UNVERIFIED PLACEHOLDER RISK** (per cross-hypothesis investigation 2026-05-19 §6.2 caveat #3 + `P1-METALS-ENERGY-CME-FEE-VERIFY`): the SIL commission + exchange-fee figures in [config/instruments.yaml SIL](../../../config/instruments.yaml) are project-operational PLACEHOLDERS pending CME Energy/Metals fee schedule primary-source verification. The empirical realistic cost may be 20-50% HIGHER. Tracked as new BLOCKING follow-up per §11.2 (`P1-H067-METALS-COST-CALIBRATION` BLOCKING-BEFORE-NEXT-V3-LAUNCH).

**Cost-friction-breakeven mechanics at SIL N-lot** (anchored on cross-hypothesis investigation 2026-05-19 §6.1 H065 v2 M_inf-SIL parent cell):

| N | Per-trade cost (USD) | Position size (contracts) | Cost as % of $10K | Per-trade gross-edge (H065 parent) bps-of-equity | Breakeven ratio at conservative_prior |
|---:|---:|---:|---:|---:|---:|
| 1 (parent) | $12.64 | 1 | 0.1264% | 13.12 | 1.04 (per cross-hyp inv §6.1) |
| 2 | $25.28 | 2 | 0.2528% (per-trade gross-edge × 2 also = 26.24 bps-eq) | 26.24 (linear extrapolation) | 1.04 (invariant under conservative_prior linear scaling) |
| 3 | $37.92 | 3 | 0.3792% | 39.36 | 1.04 |
| 4 | $50.56 | 4 | 0.5056% | 52.48 | 1.04 |
| 5 (ADR-0001 ceiling) | $63.20 | 5 | 0.6320% | 65.60 | 1.04 |

The **conservative_prior cost-model scaling is approximately linear in `n_contracts` for both commission AND slippage**; the cost-friction-breakeven ratio is **structurally invariant under N-lot scaling at the conservative_prior**. This is a load-bearing audit finding: the operator-task-spec framing of "N-lot amortizes the fixed-fee component over more notional" is FACTUALLY CORRECT only under (a) flat-fee-per-trade commission (NOT the conservative_prior's per-contract commission) AND/OR (b) sub-linear slippage scaling (NOT the conservative_prior's linear scaling).

**Cost-reduction mechanism is conditional on empirical refinement** (the H_1 inferential question):
1. **Sub-1-tick empirical slippage**: per cross-hypothesis investigation §7.2, retail-tier liquid CME equity-index futures (ES, NQ) typically see 0.3-0.7 tick average slippage on market orders during high-liquidity hours. SIL retail liquidity at sub-100-contract sizes is anecdotally similar but **unverified at adoption time**. If empirical slip = 0.5 tick → SIL slip drops from $5.00 → $2.50/side per contract → round-trip from $12.64 → $7.64 (40% reduction) → ratio rises from 1.04 → 1.72.
2. **Volume-tier-based commission discount**: per [config/instruments.yaml fee_tiers_es_nq](../../../config/instruments.yaml) table at ≥ 1000 contracts/month VIP tier kicks in for equity-index. SIL fees lack a VIP tier table at adoption time — `P1-METALS-ENERGY-CME-FEE-VERIFY` is the load-bearing primary-source-verification follow-up. At N=5 × ~5,600 trades/year (H065 parent's annualized trade rate) ≈ 28,000 contracts/year ≈ 2,300 contracts/month → well above any plausible VIP tier threshold.

**Empirical sensitivity emission requirement** (BINDING at v1 KPI emission): the H067 v1 KPI report card §3a SHALL include a sensitivity table reporting cost-friction-breakeven ratio under each of:
- `sensitivity_mult = 1.0` (conservative_prior 1-tick slip; baseline)
- `sensitivity_mult = 0.5` (0.5-tick slip; sub-1-tick empirical sensitivity exhibit)
- `sensitivity_mult = 0.0` (zero-slip; commission-only sensitivity exhibit — bounds the maximum-achievable ratio under any empirical-slip refinement)

The 3-multiplier sensitivity sweep is OPERATOR-ACTIONABLE: it directly answers "how much slippage reduction is needed to push the cell above the cost-friction-dominated-edge-present threshold?"

## 7. PIT / leakage canaries

H067 inherits H062/H065 PIT canaries verbatim. No new canary is introduced — the N-lot sizing layer does NOT affect PIT semantics (sizing at entry is computed from PIT-causal ATR_n,t and current_equity_t both as-of bar t close, with entry at bar t+1 open).

Inherited canary set:
- **Canary A — boundary-invariant**: channel state computed on full continuous PIT-causal panel; bit-identical channel values regardless of fold partition.
- **Canary B — label-horizon**: trade outcomes (exit-reason classification + realized P/L) use ONLY future bars relative to entry; no peeking.
- **Canary C — train-test leak**: NO cross-fold parameter sharing post-IS-cutoff.
- **Canary D — NaN-poison**: defensive structural-detector at orchestrator-entry per H062 v1 integration test.

Integration test `tests/integration/test_h067_pit_canaries.py` to be authored per `P1-H067-PIT-CANARY-INTEGRATION-TEST` (BLOCKING-BEFORE-FIRST-V1-LAUNCH).

## 8. Inferential structure

Per design.md §1 framing — H_1 is a **conjunctive test on each N cell**: (a) realized SIL OOS ROI > 0 at conservative_prior, (b) MPPM(ρ=1) CI excludes zero positively, AND (c) cost-friction-breakeven ratio ≥ 2 (`cost-friction-dominated-edge-present` per ADR-0028 §D-2). The recommended N* per the operator review is the smallest N satisfying all three conditions (Pareto-front interpretation; smaller N preserves retail capacity reserve for cross-strategy meta-portfolio allocation per ADR-0020).

a. ADR-0017 §3 primary survival-constrained metric vector evaluated on each N × Kelly-multiplier × cost-model cell (30 conservative_prior cells + 30 zero-cost A0 reference cells = 60 cells total).
b. Sharpe-differential (LW2008 CI) vs passive-long SIL reported as secondary KPI per ADR-0017 §1.2.

Family-wise correction over the 5-N-grid (or 30-cell N × Kelly grid; operator-discretionary at KPI emission time) via [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER. Hansen 2005 SPA p reported as KPI annotation only per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md). DSR deflation per [Bailey-López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094) MANDATORY per ADR-0027 §D-2 since realized cell count 30 ≥ project's `dsr_activation_size = 10` per [config/gate.yaml](../../../config/gate.yaml).

## 9. Sample-size + power

Per H065 v2 M_inf-SIL parent cell sample data: 5,600 OOS trades over 880+ OOS sessions on SIL (post-Phase-O.3 + Phase O.10 substrate extension). H067 retains the same sample-size envelope (N-lot sizing does not affect entry counts; only per-trade position scaling). Per-N-cell OOS sample = full 2024-01-01 → 2026-05-15 fold sweep per §2.

Power calibration `P1-H067-POWER-SIMULATION-EXECUTE` deferred (non-blocking; sample size is empirically generous; the 5-N-grid family-wise correction is well-powered at n_trades ≈ 5,600 per cell).

## 10. Decision rule

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) no-binding-gates discipline: the per-N-cell KPIs are reported in §13 alongside the H065 v2 M_inf-SIL parent reference; the operator chooses promotion timing on the Pareto-front per H_1. Stage transitions per ADR-0013 §1 (`kpi-report-emitted` → `ninjascript-implemented`) are operator-discretionary per the user 2026-05-04 standing decline-ninjascript directive.

## 11. Threats to validity + kill switches

Inherits H062 + H065 design.md §11 + §11.1 (K-1..K-8) verbatim. The N-lot sizing layer does NOT change kill-switch semantics:

- **K-1 (per-trade $-stop)**: 1.0R per Turtle 2N convention; SCALES with N (R-multiple is per-trade-unit; total $-stop is N × |1R|).
- **K-2 (time stop)**: same as H062 + H065 (EOD-flatten serves as implicit time stop at intraday cadence).
- **K-3 (no-add-to-loser)**: same as H065 (vacuous in H067 v1; no pyramiding).
- **K-4 (capacity ceilings)**: SIL ≤ 5 contracts per ADR-0001 + H062/H065 design.md §11.1 K-4 binding. N=5 is the maximum-allowable cell. <!-- justify: N-lot grid {1, 2, 3, 4, 5} is bounded ABOVE by the ADR-0001 retail capacity ceiling for SIL; the grid is EXHAUSTIVE within the retail-tier sandbox -->
- **K-5 (correlated-instrument inventory cap)**: SIL + SI inventory shares budget per H062 §11.1 K-5; SI not in H067 universe so K-5 N/A at v1.
- **K-6 (daily circuit breaker)**: −2% of basket equity realized P/L → halt new entries through end of session. <!-- justify: ADR-0017 §5 K-6 default convention; literature-canonical retail-trader risk threshold; ADR-0028 §D-1 `k6_enforcement` defaults to "block" for v1 (size-down opt-in per ADR-0028 §D-1) -->
- **K-7 (weekly circuit breaker)**: −5% of basket equity realized P/L → halt new entries through end of week. <!-- justify: ADR-0017 §5 K-7 default convention; ADR-0028 §D-1 `k7_enforcement` defaults to "block" for v1 -->
- **K-8 (adverse-direction entry filter)**: same as H062 + H065.

Per [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) §D-2 opt-in framing, K-3 + K-4 + K-6 + K-7 are **opt-in** at v1 per design.md §11.1 declaration with `enable_k4=True + enable_k6=True + enable_k7=True` (preserves [src/skie_ninja/backtest/kill_switch_runtime.py](../../../src/skie_ninja/backtest/kill_switch_runtime.py) ADR-0025 §D-1 defaults).

### 11.1 Kill-switch + abandonment-trigger opt-in declaration

Per [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) §D-2 + ADR-0025 §D-1 + ADR-0028 §D-1 opt-in declarations:

| Primitive | Status at v1 | Enforcement mode |
|---|---|---|
| Kill-switch runtime K-3 (no-add-to-loser) | DISABLED (vacuous at H067 v1 single-unit; no pyramiding) | n/a |
| Kill-switch runtime K-4 (per-symbol cap) | ENABLED at SIL ≤ 5 contracts | block (ADR-0028 §D-1 default) |
| Kill-switch runtime K-6 (daily circuit breaker) | ENABLED at −2% × equity_at_session_start | **block** at v1 (ADR-0028 §D-1 default; size-down opt-in deferred to v2 per `P1-H067-V2-WITH-K6-K7-SIZE-DOWN`) <!-- justify: v1 preserves H065 v2 modal cell mechanic verbatim; the ADR-0028 §D-1 size-down enforcement-mode is a separate genetic-axis warranting independent v2 evaluation -->|
| Kill-switch runtime K-7 (weekly circuit breaker) | ENABLED at −5% × equity_at_week_start | **block** at v1 (ADR-0028 §D-1 default) |
| Equity rebase (current-equity) | ENABLED per H065 v2 modal (`current` mode per ADR-0025 §D-2) | n/a |
| BOCD live-pause | DISABLED at v1 (no calibrated priors; deferred to v3 cycle per `P1-BOCD-LIVE-PRIOR-CALIBRATION-H067-V3`) | n/a |

### 11.2 BLOCKING preconditions (pre-launch)

| ID | Status | Description |
|---|---|---|
| `P1-H067-N-LOT-CAP-CALIBRATION` | OPEN; BLOCKING-BEFORE-LAUNCH | Empirical calibration of N=5 against ADR-0001 retail-capacity discipline + SIL liquidity stress-test at retail-tier (verifies that N=5 SIL position-sizing does NOT produce adverse fill-impact beyond conservative_prior assumption). Sub-task: `# justify:` for cap value in §11.1 K-4 table. |
| `P1-H067-METALS-COST-CALIBRATION` | OPEN; BLOCKING-BEFORE-NEXT-V3-LAUNCH | CME Energy/Metals fee schedule primary-source verification per `P1-METALS-ENERGY-CME-FEE-VERIFY`. SIL commission + exchange-fee placeholders in [config/instruments.yaml SIL](../../../config/instruments.yaml) are NOT primary-source-verified. Substrate impact: H067 v1 cost-friction-breakeven ratio is a LOWER BOUND if placeholder under-states actual cost. |
| `P1-H067-SIL-SUBSTRATE-VERIFICATION` | OPEN; BLOCKING-BEFORE-LAUNCH | Verify SIL partition coverage on canonical substrate `317429e4...` against H065 v2 sidecar; SHA-match on SIL partitions; bar-count + first-last-timestamp match. |
| `P1-H067-LEVEL-STATE-FOLD-CONTINUITY` | OPEN; INHERITED FROM H062 (closed for H062 v1) | Channel-state-at-fold-boundary unit test; H062 has the canonical implementation. H067 inherits per channel computation reuse. |
| `P1-H067-PIT-CANARY-INTEGRATION-TEST` | OPEN; BLOCKING-BEFORE-LAUNCH | Integration test at `tests/integration/test_h067_pit_canaries.py` per H062 v1 canary set inheritance. |
| `P1-H067-PROD-RUN` | OPEN | First production walk-forward + KPI report card v1. |

Closed inherited primitives: `P1-MPPM-RHO-1-FITNESS-PRIMITIVE`, `P1-BOCD-DECAY-DETECTOR-PRIMITIVE`, `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE`, `P1-L-SKEWNESS-PRIMITIVE-IMPL`, `P1-CALMAR-DIFFERENTIAL-CI-IMPL`, `P1-PROFIT-FACTOR-CI-IMPL`, `P1-R-MULTIPLE-CI-IMPL`, `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`, `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE`, `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`, `P1-H055-NEWS-CALENDAR-INGEST` (via H062 feature-factory reuse), `P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL`, `P1-SIDECAR-LEVEL-A0-ZERO-COST-REFERENCE-WIRE` (per ADR-0028 §D-2 — verify orchestrator emits A0 cells alongside A1 per the 2-cost-arm spec in §5).

## 12. Reproducibility

H067 inherits the full SKIE-Universe reproducibility discipline: deterministic RNG seed `20260519` for all bootstrap + Monte Carlo invocations; RunContext per [src/skie_ninja/utils/runcontext.py](../../../src/skie_ninja/utils/runcontext.py); ReproLog at `logs/reproducibility/<run_id>.json`; sidecar `scientific_payload_sha256` binding; substrate dataset_checksum binding to `317429e4...`. Pre-commit non-loss guard per [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

ReproLog 13-field schema MANDATORY at v1 KPI emission per `P1-H067-REPROLOG-WIRE` (BLOCKING-BEFORE-V1-EMISSION; new follow-up registered below); the H067 walk-forward orchestrator MUST wrap execution in `RunContext` to emit canonical ReproLog (avoiding the H065 v1 retrofit pattern documented in [research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md](../H065/H065_kpi_report_v1_corrigendum_2026-05-18.md)).

## 13. Sensitivity exhibits + scope deviations

**Required sensitivity exhibits**:
- **Per-N cell** at v1 KPI report card §"End-of-simulation results summary" 13-table format per ADR-0014 §3.2 + ADR-0019 §3.
- **Per-N + per-Kelly-multiplier × per-cost-arm 30-cell heatmap** with cells classified per ADR-0028 §D-2 `cost-friction-dominated-edge-{present, absent, n/a}` annotation.
- **Cost-friction-breakeven ratio sensitivity table** under `sensitivity_mult ∈ {1.0, 0.5, 0.0}` per §6 binding (operator-actionable diff between conservative_prior and empirical-slip-reduction-needed-to-clear-threshold).
- **N=1 (parent baseline)** alongside in the KPI report card as the direct-comparability reference to H065 v2 M_inf-SIL cross-hypothesis investigation 2026-05-19 anchor (parent breakeven ratio = 1.04).
- **2026-04-01 → 2026-05-15 sub-window** (~6 weeks; mandatory per ADR-0026 §D-1 §0 3-component header component 2).

**Scope deviations from full-spec inner-CV grid** (recorded per Path A frozen-pre-reg amendment discipline):
- v1 inner-CV grid REDUCED from the full H062 §5 13,824-cell combinatorial grid (per H065 §5.2 inheritance) to a tractable 60-cell representative grid (N × Kelly × cost-arm) at fixed H065 v2 modal feature cell (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0). Full-grid tracked under `P1-H067-FULL-INNER-CV-GRID-V2`.
- SIL-only at v1 (no 4-symbol basket; cross-asset extension tracked under `P1-H067-V2-CROSS-ASSET-BASKET-EXTEND`).
- TWO cost-model arms at v1 (A0 zero-cost + A1 conservative_prior) per ADR-0028 §D-2; paper-trade-empirical deferred to v3 per `P1-H067-COST-EMPIRICAL-CALIBRATION`.
- Single-unit entry; no pyramiding (per H065 + H067 v1 preservation; pyramiding deferred to v2 successor).
- v1 reports current-equity rebase per ADR-0017 §4.1 + ADR-0024 paradigm per H065 v2 parent cell.
- M=∞ no-TP-overlay (fixed; not a grid axis) per H065 v2 M_inf-SIL parent-cell preservation.
- Inner-CV walk-forward window = 252-session-train / 60-session-test per ADR-0027 §D-2 bounded set {63, 126, 252, 504}; preserved from H065 v2 parent.

## 14. Cross-references

- **Parent hypothesis**: [H065](../H065/design.md) (H065 v2 M_inf-SIL cell at `kpi-report-emitted`; first KPI emission 2026-05-15; v2 retroactive emission on canonical substrate `317429e4...` per CLAUDE.md Phase O.10 extension).
- **Grandparent hypothesis**: [H062](../H062/design.md) (H067 inherits feature factory + walk-forward orchestrator + PIT canaries verbatim per the H065 §3 inheritance chain).
- **Empirical anchor**: [cross-hypothesis investigation 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md) (H065 v2 M_inf-SIL breakeven ratio = 1.04 anchor; cost-light genetic-successor candidacy per §7.4 #1).
- **H062 v3 ablation precedent**: [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) (load-bearing case-study for cost-friction-dominated-edge mechanism).
- **Sibling** (also deferred): [H066](../../../hypothesis_backlog.md) (queued; H065 + Turtle System 2 pyramiding overlay).
- **Paradigm stack**: ADR-0001 + ADR-0008 + ADR-0013 + ADR-0014 + ADR-0017 + ADR-0018 + ADR-0019 + ADR-0020 + ADR-0022 + ADR-0023 + ADR-0024 + ADR-0025 + ADR-0026 + ADR-0027 + ADR-0028.

## 15. NinjaScript implementation (per ADR-0013 §5; mandatory upon operator approval)

Mandatory C# implementation per [ADR-0013 §5](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): `ninjascript/strategies/H067_CostLightDonchianSIL.cs`.

C# class structure (skeleton; full implementation deferred to `P1-H067-NINJASCRIPT-IMPL`):
- **Class name**: `H067_CostLightDonchianSIL`
- **File path**: [ninjascript/strategies/H067_CostLightDonchianSIL.cs](../../../ninjascript/strategies/H067_CostLightDonchianSIL.cs)
- **Inheritance**: `NinjaTrader.NinjaScript.Strategies.Strategy`
- **Hyperparameter mapping** (Python ↔ C#):
  - `channel_n: int = 120` ↔ `[NinjaScriptProperty(Description="Donchian channel period")] public int ChannelN { get; set; } = 120;`
  - `k_atr: double = 2.0` ↔ `[NinjaScriptProperty(Description="ATR stop multiplier")] public double KAtr { get; set; } = 2.0;`
  - `atr_n: int = 14` ↔ `[NinjaScriptProperty(Description="ATR period")] public int AtrN { get; set; } = 14;`
  - `n_lot: int = N*` (operator-selected from {1,2,3,4,5} at deployment) ↔ `[NinjaScriptProperty(Description="N-lot position size")] public int NLot { get; set; } = 1;`
  - `kelly_multiplier: double = M*` (operator-selected from {0.25..2.5} at deployment) ↔ `[NinjaScriptProperty(Description="Kelly multiplier")] public double KellyMultiplier { get; set; } = 0.25;`
- **Entry / exit logic 1:1 with Python**: Donchian channel + ATR stop + first-fire dwell + ID_1 trend gate + EOD-flatten per H062 + H065 design.md §15 patterns.
- **Kill-switch parameters per §11.1**: K-4 enforced via `Position.Quantity` cap; K-6 / K-7 enforced via running daily/weekly P/L accumulator with `EnterLong` / `EnterShort` rejection on breach (block-mode per ADR-0028 §D-1 default).
- **Fill-log schema matching plan §6.1**: CSV with `(timestamp_ct, symbol, side, n_contracts, entry_price, exit_price, exit_reason, realized_pl_usd)` columns per H062 + H065 §15 + project plan §6.1.
- **Sim101 smoke-test record**: ScriptSubmission timestamps + position fills + final P/L per ADR-0013 §5.1 deferred to `P1-H067-NINJASCRIPT-SIM101-SMOKE-RECORD`.

Python ↔ NinjaScript parity-check per ADR-0013 §5.2: byte-equality on integer entry/exit signal vector + per-trade exit-reason classification. Tracked under `P1-H067-NINJASCRIPT-IMPL` (mandatory per ADR-0013 §5; operator-discretionary decline allowed per 2026-05-04 standing directive).

## 16. Substrate provenance

Substrate: [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/); `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) per CLAUDE.md Phase O.10 substrate re-derivation (run_id `38d63bdd2def4fa9804c78fbcb1a76ce`).

Per-partition SIL SHA enumeration at v1 freeze: see [data_requirements.md](data_requirements.md) §"Per-partition SHA enumeration".

## 17. Revision log

- **2026-05-19** (initial pre-registration): `status: designed` frozen. N-lot cost-light genetic successor of H065 v2 M_inf-SIL cell; primary cost-reduction axis = N-lot position-size grid {1, 2, 3, 4, 5}; alternate cost-reduction axes (bar-cadence reduction; longer-hold) deferred to v2 follow-ups per ADR-0027 §D-4 single-axis-genetic-cross discipline. Two-cost-arm emission (A0 zero-cost + A1 conservative_prior) per ADR-0028 §D-2 zero-cost-A0-reference convention. Pre-reg authored under audit-remediate-loop discipline (3-round cap per SKILL.md); 1-round Round-1 audit applied at draft time; full audit trail at [docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md](../../../docs/audits/audit_trail_2026-05-19_h067-cost-light-h065-sil-design.md).

### 17.1 Genetic-successor cross-citation (per ADR-0027 §D-4 four-field mandatory disclosure)

| Field | Value |
|---|---|
| **Parent hypothesis ID + final stage** | H065 v2 at `kpi-report-emitted` per CLAUDE.md Phase O.10 extension; specifically the **M_inf-SIL cell** at the H065 v2 M_inf-h065-current variant (sidecar SHA pending Phase O.10 v2 emission per the H065 v2 KPI report card at [research/01_hypothesis_register/H065/H065_kpi_report_v2.md](../H065/H065_kpi_report_v2.md)). The H065 v1 emission produced realized OOS +734.68% at MPPM CI [+0.087, +0.459] EXCLUDES ZERO POS in the fixed-rebase variant (M_inf-h062-v1-fixed); H065 v2 retroactive emission on canonical substrate `317429e4...` per CLAUDE.md Phase O.10 extension confirms the parent-cell pre-cost ROI envelope. |
| **Motivating KPI / annotation** | **Cross-hypothesis investigation 2026-05-19 §6.1 row #2**: H065 v2 M_inf-h065-current SIL standalone cell carries cost-friction-breakeven ratio **1.04** (13.12 bps-of-equity per-trade gross-edge vs 12.64 bps-of-equity round-trip cost at conservative_prior) — barely above unity; pre-cost OOS +734.68% (5,600 trades). Cell-level annotation: `likely-marginal-pending-A0` per investigation §2 schema. **The genetic-cross hypothesis**: a modest empirical-cost reduction (e.g., 25-50% slip-component shrinkage; cf. investigation §7.2 anchored on practitioner anecdotes) would push the cell above the ADR-0028 §D-2 `cost-friction-dominated-edge-present` threshold (ratio ≥ 2). H067 v1 measures the structural sensitivity of the ratio to N-lot scaling under conservative_prior + emits empirical-slip-multiplier sensitivity to operator-actionably surface the "how much slip reduction is needed" question. |
| **Genetic-cross** | **SINGLE AXIS** per ADR-0027 §D-4 single-axis-genetic-cross discipline. Cross-axis: N-lot position-size grid `N ∈ {1, 2, 3, 4, 5}` contracts capped at ADR-0001 retail-capacity ceiling (SIL ≤ 5). Cost-arm grid (A0 zero-cost + A1 conservative_prior) per ADR-0028 §D-2 zero-cost-A0-reference convention. NO change to: signal-generation mechanic (channel_n + k_atr + atr_n + h_dwell + trend_id all fixed at H065 v2 modal values); exit precedence (channel-reverse + ATR-stop + EOD-flatten); cost-model class (`nt8_realistic_v1` per ADR-0025 §D-3). The bar-cadence-reduction (mechanism 2) + longer-hold-variant (mechanism 3) cost-reduction axes are deferred to v2 successors per ADR-0027 §D-4 single-axis discipline. |
| **Preserved infrastructure** | Substrate `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.10 main-HEAD); H062 feature factory at [src/skie_ninja/features/h062/](../../../src/skie_ninja/features/h062/); H065 v2 walk-forward orchestrator at [scripts/run_h065_tp_overlay_sweep.py](../../../scripts/run_h065_tp_overlay_sweep.py) (to be forked to [scripts/run_h067_n_lot_sweep.py](../../../scripts/run_h067_n_lot_sweep.py) per `P1-H067-WALK-FORWARD-ORCHESTRATOR-IMPL`); H062 v1 PIT canaries verbatim ([tests/integration/test_h062_pit_canaries.py](../../../tests/integration/test_h062_pit_canaries.py)); ADR-0017 + ADR-0018 + ADR-0019 + ADR-0022 inner-CV machinery + KPI annotation grammar; ADR-0014 §3.2 13-table format + ADR-0026 §D-1 §0 3-component summary header + ADR-0028 §D-4 `kill-switch-mode-{block,size-down}` + `cost-friction-dominated-edge-{present,absent,n/a}` annotations; ADR-0023 metals/energy substrate; ADR-0025 abandonment-trigger primitives (kill-switch runtime + equity rebase ENABLED at v1; BOCD live-pause + size-down enforcement DEFERRED). Cell-budget cap = 60 cells per ADR-0027 §D-2 declaration (under 1000 v1 cap). Inner-CV fitness = MPPM(ρ=1) per ADR-0018 D-1. RNG seed = `20260519`. |
