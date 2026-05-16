---
hypothesis_id: H065
schema_version: hypothesis_design_v1
status: designed
tier: 2b
created: 2026-05-15
created_by: skoir
description: H062 with ATR-scaled profit-target overlay (Turtle System 2 + TP grid). Tests whether truncating the H062 v1 right tail with M ∈ {1.0, 1.5, 2.0, 2.5} × R targets converts the τ_3=+0.74 skew-positive payoff into MPPM(ρ=1) > 0 strict-positive CI without breaking it.
---

# H065 — Intraday Donchian-channel breakout on {ES, NQ, MGC, SIL} with ATR-scaled profit-target overlay

> **TP-overlay extension of [H062 v1](../H062/H062_kpi_report_v1.md).** H065 keeps every mechanical layer of [H062 design.md](../H062/design.md) — Donchian channel + first-fire dwell + ATR-stop + ID_1 trend gate + EOD-flatten + Kelly-multiplier grid + MPPM(ρ=1) inner-CV fitness per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1/D-2 + ADR-0017 §4.1 current-equity rebase per the Phase O.4 + ADR-0024 paradigm resolution — and adds **ONE** new mechanic: an ATR-scaled profit target at `entry ± M × k_atr × ATR_n,t` for `M ∈ {1.0, 1.5, 2.0, 2.5}` R-multiples. The TP-overlay is sized in the same R-units as the ATR-stop, so each TP cell corresponds to a fixed risk:reward ratio (M=1 → 1:1; M=2.5 → 1:2.5).
>
> **Hypothesis-of-record (H_1)**: there exists an M cell that produces (a) basket MPPM(ρ=1) > 0 with stationary-bootstrap CI strictly excluding zero on the positive side, AND (b) per-trade L-skewness τ_3 ≥ 0 — i.e., the TP overlay does NOT invert the H062 v1 skew-positive payoff distribution into skew-negative ("death-by-thousand-cuts"). Either condition failing on every M cell = null disposition; H062 v1 (no-TP) remains the structurally-preferred configuration. **The load-bearing question is whether the TP-truncated-right-tail produces a mean-edge improvement (MPPM > 0 CI strict-positive) before it inverts the skew direction.**
>
> **Full Phase N + Phase O.0 + Phase O.4 + ADR-0024 paradigm inheritance.** H065 inherits the same paradigm stack as H062 + the post-2026-05-15 amendments: [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) permanent-exploration / no-binding-gates / mandatory-NinjaScript-terminus / non-loss preservation + [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) canonical 13-table results-summary + [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained primary metric vector + K-1..K-8 kill switches + FM-1..FM-5 stress-test suite + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) inner-CV fitness + Kelly-multiplier grid + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness annotation + barbell-rebalance-candidate flag + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism vs correlation-only annotation (§1.3) + [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate expansion + ADR-0024 paradigm resolution.
>
> **Pyramiding deferred to a v2 successor (H066)**. H065 tests the TP-overlay extension in isolation. Combining TP + pyramiding multiplies the parameter surface; the comparison value of an isolated TP test outweighs the combined-test optionality. v1 is **no-pyramiding** + **single-unit entry** + TP-overlay. H066 (queued) = H065 + Turtle System 2 pyramiding overlay.

## 1. Hypothesis

- **H_0**: For every M ∈ {1.0, 1.5, 2.0, 2.5}, at least one of: (a) basket MPPM(ρ=1) ≤ 0 OR stationary-bootstrap CI covers zero, OR (b) per-trade L-skewness τ_3 < 0 (skew-inverted to skew-negative) under the [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) ±0.1 cutoff and CI.
- **H_1**: There exists an `M* ∈ {1.0, 1.5, 2.0, 2.5}` such that (a) basket MPPM(ρ=1) > 0 with stationary-bootstrap CI strictly excluding zero on the positive side, AND (b) per-trade L-skewness τ_3 ≥ 0 (CI does not exclude positive-side; payoff remains skew-positive or skew-flat). The recommended `M*` (operator-discretionary) is the one minimizing `−MPPM(ρ=1)_lower_CI_bound` subject to `τ_3 ≥ -0.1` (annotation `skew-flat` or `skew-positive`).
- **Predictand**: same as H062 — per-trade R-multiple `R_t = realized_PL_t / |1R_t|` per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py); per-session-aggregated basket log-return series for MPPM(ρ=1) per design.md §1 of H062.
- **Test statistic** (load-bearing): per-M-cell `T_H065_basket(M) = MPPM(ρ=1)[r_basket_OOS_session_aggregated(M)]` where the simulator is re-run with TP-grid cell M and otherwise-identical mechanics. Family size at the basket level = 4 (one per M cell); per-symbol-per-M family size = 16 (4 symbols × 4 M cells) under [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER family-wise correction. **No-TP H062 v1 baseline reported alongside as the M=∞ reference cell** for the operator to assess marginal contribution of TP overlay.
- **Secondary inferential KPIs** (per ADR-0017 §1.2 demotion machinery): per-symbol Sharpe-differential under [Ledoit-Wolf 2008 *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap CI; Hansen 2005 SPA p reported as KPI annotation per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-and-m1-degenerate.md) at M=4-cells (basket-level family) + M=16 (per-symbol family).

### 1.3 Causal-mechanism vs correlation-only annotation (per ADR-0022)

- **Claim type**: `hybrid` (inherits H062's causal mechanism on the channel-break-as-information-event layer; TP-overlay is **correlation-only refinement** on top of that mechanism).
- **Mechanism description (who/what/why/when)**: inherits H062 design.md §1.3 verbatim for the breakout-event-as-information-revelation upstream mechanism (Hong-Stein 1999 underreaction + Bouchaud-Gefen-Potters-Wyart 2004 stop-order liquidity at multi-bar pivots + Frazzini 2006 round-number anchoring). TP-overlay layer **has no independent causal claim** — the M-grid selection is a parameterization-tuning question with no theoretical anchor in the underlying microstructure mechanism. Tharp 1998 *Trade Your Way to Financial Freedom* (*practitioner*; ISBN 978-0070647626) §"R-multiple" discusses ATR-scaled TPs at fixed risk:reward ratios as a trade-management convention; this is `correlation-only refinement` per ADR-0022 §3.
- **E-value / robustness anchor**: deferred to first post-primitive KPI emission per H062 design.md §1.3 — the [src/skie_ninja/inference/e_value.py](../../../src/skie_ninja/inference/e_value.py) primitive is closed (Phase O.1 follow-on); H065 KPI report card v1 carries the E-value annotation against the 137-year Hurst-Ooi-Pedersen 2017 daily-grain reference.
- **TP-grid M is correlation-only**: no causal claim about which M is "the true risk:reward ratio". M is grid-searched per §5; the recommended M* per H_1 is operator-discretionary on a Pareto-front of MPPM CI strict-positivity AND τ_3 ≥ 0.

### 1.4 Pre-empirical caveat: H065 is a TP-overlay test on a partially-decayed-factor strategy

H065 inherits H062's §1.4 pre-empirical caveat verbatim: the underlying intraday channel-breakout is a **partially-decayed factor** per [Marshall-Cahan-Cahan 2008 *JBF* 32(9):1810-1819 DOI 10.1016/j.jbankfin.2007.12.011](https://doi.org/10.1016/j.jbankfin.2007.12.011); [Hsu-Kuan 2005 *J Financial Econometrics* 3(4):606-628 DOI 10.1093/jjfinec/nbi026](https://doi.org/10.1093/jjfinec/nbi026); [Park-Irwin 2007 *J Economic Surveys* 21(4):786-826 DOI 10.1111/j.1467-6419.2007.00519.x](https://doi.org/10.1111/j.1467-6419.2007.00519.x). H062 v1 emitted at MPPM(ρ=1) = -0.223 [CI -0.599, +0.172] basket-level (CI covers zero; **non-significant null on the load-bearing MPPM inference**); the strategy nevertheless captured +43.25% realized OOS over 8,270 trades vs passive +304.47%. **The TP overlay's expected mechanical effect is to truncate the right tail of the per-trade R-multiple distribution** — converting some right-tail wins (currently R > M, kept full) into capped wins (now R = M, cut at TP). For an M-grid optimal cell `M*`, this *may* convert the H062 v1 H_1-null disposition into H_1-positive if the right-tail truncation systematically reduces realized give-back from peak-to-exit on winning trades.

Theoretical anchor for the TP-overlay framing: [Tharp 1998 *Trade Your Way to Financial Freedom*](https://www.amazon.com/Trade-Your-Way-Financial-Freedom/dp/0071478716) (*practitioner*; 1st ed ISBN 978-0070647626) §6 R-multiple analysis posits that mean R-multiple is the load-bearing per-trade-edge unit; a strategy with mean R-multiple +0.5 over a sample of N=1000 trades has bankroll-blowup probability bounded below 50% Vince 1990 Ch.3 (depending on Kelly factor). H062 v1 mean R-multiple = +0.044 with CI=[-0.017, +0.109] (covers zero). **The H_1 inferential question for H065 is whether any M cell improves R-multiple mean to strict-positive CI.**

Expected H062-relative effect of TP overlay (pre-empirical; not load-bearing):
- **Lower M** (M=1.0, 1.5) → more truncation → higher win rate (trades exit at TP not at opposite-channel-break) → narrower per-trade R distribution → lower σ(R) → potentially higher Sharpe but *lower* mean R-multiple if truncation also truncates winning tail magnitude.
- **Higher M** (M=2.0, 2.5) → less truncation → preserves more of H062's right-tail magnitude → R-multiple distribution closer to H062 v1's τ_3=+0.74 skew-positive shape but with reduced give-back from peak-to-exit on each individual winning trade.
- **No M cell expected to dominate** all 4 ADR-0017 primary survival-constrained metrics simultaneously — operator review on the Pareto-front per H_1 framing is the load-bearing decision.

### 1.5 Pre-empirical caveat on cross-asset correlation + diversification

Inherits H062 design.md §1.5 verbatim. ES-NQ correlation ≈ +0.85-0.95 collapses equity pair to ~1 effective asset; MGC-SIL correlation ≈ +0.5-0.7 collapses metals pair to ~1.3 effective assets. Effective basket breadth ≈ 2.3 not 4.

## 2. Universe and sample period

Inherits H062 design.md §2 verbatim with one substrate update for the 2026-05-15 right-edge extension:

- **Instruments at v1**: ES, NQ, MGC, SIL. Same as H062 v1 (MCL deferred to H066/H067; CL deferred to H061; MES/MNQ not independent family members).
- **Substrate availability** (post-2026-05-15 H1-2026 extension; binding):
  - **Verified `output_frame_sha256`**: `b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260516.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260516.json). Includes the H1-2026 extension (ES + NQ + MGC + SIL through 2026-05-15).
  - **Coverage per provenance**: ES 2020-01-01 → 2026-05-15 (7 partitions); NQ 2020-01-01 → 2024-12-19 + 2026-01-01 → 2026-05-15 (6 partitions; 2025 gap retained from H062 v1 substrate); MGC 2015-01-01 → 2026-05-15 (12 partitions); SIL 2015-01-01 → 2026-05-15 (12 partitions). Total H065 v1 universe = 37 partitions.
- **Sample window** (BINDING; pre-reg-frozen):
  - **Calibration holdout**: 2015-01-01 → 2019-12-31 (MGC + SIL only). Same as H062.
  - **IS**: 2020-01-01 → 2023-12-31 (4 years). Same as H062.
  - **OOS test**: per-symbol right-edges; ES 2024-01-01 → 2026-05-15 (NEW; H062 v1 stopped at 2025-12-03); NQ 2024-01-01 → 2024-12-19 + 2026-01-01 → 2026-05-15 (NEW); MGC 2024-01-01 → 2026-05-15 (NEW); SIL 2024-01-01 → 2026-05-15 (NEW). The 2026-04-01 → 2026-05-15 sub-window is a **mandatory reporting cell** in §13 — operator wants the "last ~6 weeks" realized-OOS profile alongside the full OOS sweep.
- **Cadence**: 5-minute bars primary (same as H062 v1; H062 modal cell per the KPI report card §8).
- **Session policy**: same as H062 (RTH-only ES/NQ; 24/5 metals with 16:00-17:00 CT maintenance break; EOD-flatten at 15:00 CT for ES/NQ, 15:55 CT for metals).
- **Roll treatment**: per-asset roll-adjusted front-month continuous series per [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) post-Phase-O.0 deliverable. Same as H062.
- **Cost model — ZERO at v1** per operator standing directive 2026-05-08 + 2026-05-12 + 2026-05-15. PRE-COST research-only. Annotation `cost-zero-v1-pre-cost-research-only`. Empirical regime-wise calibration deferred to `P1-H065-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED-STAGE-TRANSITION).

## 3. Features

H065 inherits **every feature** from H062 design.md §3 verbatim. No new feature is introduced — the TP-overlay is a label-construction / exit-mechanic extension at §4, not a feature at §3.

- Donchian channel (close-to-close N-bar high/low; PIT-causal at bar-(t-1)).
- ATR Wilder (n grid {14, 21, 60}).
- Trend-strength filter ID_1 (4 candidates; selected per-instrument by Brier-score competition on calibration holdout).
- News-time exclusion features (FOMC ±15min; NFP ±5min; CPI ±5min).

Feature factory at [src/skie_ninja/features/h062/](../../../src/skie_ninja/features/h062/) is **reused verbatim** for H065. No new feature module is added.

## 4. Label construction (NEW SECTION RELATIVE TO H062 — TP-OVERLAY ADDITION)

Per-trade P/L on a Donchian-channel-breakout signal with ATR-scaled stop + **ATR-scaled profit target (NEW vs H062)** + opposite-channel exit + EOD-flatten.

- **Entry**: same as H062. Limit-or-market order at the next bar (t+1) open, conditional on (i) §3 channel-break detector fires at bar-t close, (ii) ID_1 trend-strength filter admits the side, (iii) bar t+1 is in the eligible-bar set.
- **Profit target (NEW vs H062)**: `TP_long = entry + M × k_atr × ATR_n,t`; `TP_short = entry - M × k_atr × ATR_n,t`. Symmetric R-multiple TP at `M × R` from entry, where `R = k_atr × ATR_n,t × point_value × contracts` is the per-trade $-distance to the ATR-stop. <!-- justify: Tharp 1998 *practitioner* §"R-multiple" canonical convention; ATR-scaled TP at fixed R-multiple is the canonical risk:reward unit for per-trade trade-management research; grid M ∈ {1.0, 1.5, 2.0, 2.5} brackets the literature-canonical 1:1 → 1:2.5 risk:reward range -->
- **TP fill logic** (intraday-bar resolution; high-low containment): if `bar_t_high >= TP_long_price` (long position; TP within bar's high-low envelope), exit at `TP_long_price` (limit fill at exact TP). Symmetric for short. Tie-breaking when bar's high+low both contain BOTH the stop AND the TP: **stop-first convention** (conservative; assume adverse fill order). <!-- justify: stop-first is the conservative/realistic intraday bar-resolution convention per López de Prado 2018 *AFML* §13.3 *practitioner*; assuming TP-first would introduce optimistic-bias in narrow-range bars where both barriers are within the bar's high-low envelope -->
- **Stop**: `SL_long = entry - k_atr × ATR_n,t`; `SL_short = entry + k_atr × ATR_n,t` (same as H062; k_atr grid {1.0, 1.5, 2.0, 2.5}).
- **Time stop / EOD flatten**: same as H062 (no explicit time stop; EOD flatten at 15:00 CT for ES/NQ, 15:55 CT for metals).
- **Opposite-channel exit**: same as H062 (channel-flip in same bar closes position at bar's close — applies when neither TP nor SL is hit but the channel flips).
- **Exit precedence within bar** (BINDING; PIT-resolved):
  1. **Gap-through-stop** at bar-t open (open beyond SL): close at open.
  2. **Stop hit** during bar (low ≤ SL_long or high ≥ SL_short): close at SL price.
  3. **TP hit** during bar (high ≥ TP_long or low ≤ TP_short): close at TP price.
  4. **Opposite-channel break** at bar-t close (channel signal flips against position): close at bar-t close.
  5. **EOD flatten** at session-cutoff bar: close at bar-t close.
  6. **Session rollover** (next bar's session differs): close at bar-t close.

The §4.2 "stop-first convention" is the load-bearing tie-breaker: in a bar where the high reaches TP AND the low reaches SL, the bar resolution is **stop-hit** (not TP-hit), per the AFML §13.3 conservative-bar-resolution convention. **R-multiple definition** (per H062 §4 + Tharp 1998 §"R-multiple"): R = realized_PL / |1R| where |1R| = k_atr × ATR_n,t × multiplier × contracts. TP-hit trades produce R ≈ M (capped at exactly M if TP fills at the limit price). Stop-hit trades produce R ≈ -1. Opposite-channel-exit produces R in (-1, +∞) — the only mechanism by which H065 can produce R > M.

**TP grid (NEW BINDING)**: `M ∈ {1.0, 1.5, 2.0, 2.5}`. <!-- justify: 1.0 = literature-canonical 1:1 risk:reward (operator-trading-convention default); 1.5 = mild positive-expectancy edge (mean R > 0 if win rate > 40%); 2.0 = Faith 2007 ATR-anchored 2R "let some run" convention; 2.5 = upper bound near the per-trade R-multiple where opposite-channel-exit becomes the dominant exit reason on H062 v1 - validation that the TP-grid spans the meaningful trade-management range -->

Plus reporting baseline `M = ∞` (no TP; identical to H062 v1; reported as **reference cell** in §13 for differential interpretation). The 4-element TP grid creates a **5-cell family per symbol** (4 TP cells + M=∞ no-TP reference).

## 5. Estimator

Inherits H062 design.md §5 **verbatim** with one extension at §5.2: the M-grid is added to the joint inner-CV cell selection.

- **§5.1 ID_1 trend-identifier selection**: same as H062. Per-instrument Brier-score competition on calibration holdout.
- **§5.2 channel-N + k_atr + cadence + M selection** (NEW: M added to the joint grid): per-instrument MPPM(ρ=1) on inner-CV out-of-fold per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1. **NEW grid**: `M ∈ {1.0, 1.5, 2.0, 2.5}` (no `M=∞` cell at inner-CV — the M=∞ baseline is reported as a sensitivity exhibit, NOT competed in the inner-CV).
- **§5.3 Kelly-multiplier grid**: same as H062. {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} per ADR-0018 D-2; super-Kelly cells {1.5, 2.0, 2.5} carry `super-kelly-operator-discretionary` annotation.
- **§5.4 BOCD signal-decay monitor**: same as H062. Adams-MacKay 2007 BOCD on per-fold MPPM(ρ=1) path; hazard rate 1/100.
- **§5.5 Switching-bandit allocation redirect**: deferred to v2/v3 successor (`P1-H065-SWITCHING-BANDIT-INTEGRATE`); not in v1 scope per single-strategy-focus discipline.
- **§5.6 Walk-forward outer CV**: same as H062. Rolling 252-session-train / 60-session-test; embargo 2400 min.
- **§5.7 Inner-CV selection metric**: same as H062. MPPM(ρ=1) per ADR-0018 D-1.
- **§5.8 Inner-CV regularisation discipline + nested-CV structure**: same as H062. Level-A (ID_1) vs Level-B (cell-grid + M) disjointness preserved.

**Joint inner-CV cell grid cardinality at full sweep** (per design.md §11.3 scope-deviation acknowledgement):
- channel_n: 6 cells {20, 40, 60, 120, 240, 480}
- k_atr: 4 cells {1.0, 1.5, 2.0, 2.5}
- atr_n: 3 cells {14, 21, 60}
- h_dwell: 4 cells {1, 2, 5, 10}
- M (TP): 4 cells {1.0, 1.5, 2.0, 2.5}
- Kelly multiplier: 6 cells {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}
- trend_id: 4 cells {a, b, c, d}

Full grid = 6 × 4 × 3 × 4 × 4 × 6 × 4 = **13,824 × 4 (M cells) = 55,296 cells**.

Per the H062 design.md §11.3 scope-deviation precedent: **v1 reduces the inner-CV grid to a tractable 16-cell representative grid** (`M × kelly_multiplier × symbol`; channel_n, k_atr, atr_n, h_dwell, trend_id fixed at H062 v1 modal values per the H062 KPI report card §8: channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0). Full-grid sweep tracked under `P1-H065-FULL-INNER-CV-GRID-V2` (deferred to a v2 successor).

## 6. Cost model

`zero_cost_v1_pre_cost_research_only` per operator standing directive. Same as H062 v1.

## 7. PIT / leakage canaries

H065 inherits H062's PIT canaries verbatim. The TP-overlay adds one new check:

- **Canary E (NEW)**: TP price is computed at entry-bar-t-close using entry_price (next-bar t+1 open) and ATR_n,t (PIT-causal as of bar t close). TP fill check at bar t+1 uses bar t+1's high (long) or low (short), which is the FIRST PIT-revealable bar after entry. The TP fill logic does NOT use bar t+1 close (the close is a posteriori the bar; the high/low/open are the realized intra-bar extremes). Unit test `tests/unit/test_h065_tp_overlay.py::test_tp_fill_uses_intrabar_high_low_not_close` verifies.

## 8. Inferential structure

Per design.md §1 framing — H_1 is a **conjunctive test on each M cell** (MPPM CI excludes zero positively AND τ_3 ≥ 0). The recommended M* per the operator review is the M cell minimizing `−MPPM(ρ=1)_lower_CI` subject to `τ_3 ≥ -0.1` (the [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) skew-flat threshold). Family-wise correction over the 4-cell M-grid via [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER. Hansen 2005 SPA p reported as KPI annotation only per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-and-m1-degenerate.md).

a. ADR-0017 §3 primary survival-constrained metric vector evaluated on each M cell.
b. Sharpe-differential (per-symbol; LW2008 CI) reported as secondary KPI per ADR-0017 §1.2.

## 9. Sample-size + power

Per H062 v1 sample data: 8,270 OOS trades over 2,944 OOS sessions across 4 symbols. H065 retains the same sample-size envelope (TP-overlay does not affect entry counts; only exit timing and trade outcome). Per-M-cell OOS sample = full 2024-01-01 → 2026-05-15 fold sweep per §2. Power calibration `P1-H065-POWER-SIMULATION-EXECUTE` deferred (non-blocking; sample size is empirically generous).

## 10. Decision rule

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) no-binding-gates discipline: the per-M-cell KPIs are reported in §13 alongside the H062 v1 no-TP reference; the operator chooses promotion timing on the Pareto-front per H_1. Stage transitions per ADR-0013 §1 (`kpi-report-emitted` → `ninjascript-implemented`) are operator-discretionary per the user 2026-05-04 standing decline-ninjascript directive.

## 11. Threats to validity + kill switches

Inherits H062 design.md §11 + §11.1 (K-1..K-8) verbatim. The TP-overlay does NOT change kill-switch semantics:

- **K-1 (per-trade $-stop)**: TP exit produces realized R ≈ +M (capped); does not weaken the K-1 $-stop discipline.
- **K-2 (time stop)**: same as H062 (EOD-flatten serves as implicit time stop at intraday cadence).
- **K-3 (no-add-to-loser)**: vacuous in H065 v1 (no pyramiding; pyramiding deferred to H066).
- **K-4 (capacity ceilings)**: same as H062 (ES 20, NQ 40, MGC 5, SIL 5).
- **K-5..K-8**: same as H062.

### 11.2 BLOCKING preconditions (pre-launch)

| ID | Status | Description |
|---|---|---|
| `P1-H065-TP-OVERLAY-IMPL` | OPEN | TP-overlay simulator extension at `scripts/run_h065_tp_overlay_sweep.py`. |
| `P1-H065-LEVEL-STATE-FOLD-CONTINUITY` | OPEN; INHERITED FROM H062 (closed for H062 v1) | Channel-state-at-fold-boundary unit test; H062 has the canonical implementation. H065 inherits per channel computation reuse. |
| `P1-H065-TP-FILL-INTRABAR-PIT-TEST` | OPEN; NEW for H065 | Unit test: TP fill logic uses bar t+1 high/low NOT close; stop-first convention on dual-barrier bars; symmetric for short. |
| `P1-H065-PROD-RUN` | OPEN | First production walk-forward + KPI report card v1. |

Closed inherited primitives: `P1-MPPM-RHO-1-FITNESS-PRIMITIVE`, `P1-BOCD-DECAY-DETECTOR-PRIMITIVE`, `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE`, `P1-L-SKEWNESS-PRIMITIVE-IMPL`, `P1-CALMAR-DIFFERENTIAL-CI-IMPL`, `P1-PROFIT-FACTOR-CI-IMPL`, `P1-R-MULTIPLE-CI-IMPL`, `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`, `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE`, `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`, `P1-H055-NEWS-CALENDAR-INGEST` (via H062 feature-factory reuse), `P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL`.

## 12. Reproducibility

H065 inherits the full SKIE-Universe reproducibility discipline: deterministic RNG seed `20260515` for all bootstrap + Monte Carlo invocations; RunContext per [src/skie_ninja/utils/runcontext.py](../../../src/skie_ninja/utils/runcontext.py); ReproLog at `logs/reproducibility/<run_id>.json`; sidecar scientific_payload_sha256 binding; substrate dataset_checksum binding to `b93e544...`. Pre-commit non-loss guard per [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## 13. Sensitivity exhibits + scope deviations

**Required sensitivity exhibits**:
- **Per-M cell** + **M=∞ (H062 v1 no-TP reference)** alongside in the KPI report card v1 §"End-of-simulation results summary" 13-table format.
- **2026-04-01 → 2026-05-15 sub-window** (~6 weeks; ~30 sessions per symbol) as a mandatory sub-period reporting cell. Operator wants the "last 6 weeks" realized-OOS profile alongside the full OOS sweep. Reported as supplementary §"2026-AprMay sub-window" table.

**Scope deviations from full-spec inner-CV grid** (recorded per Path A frozen-pre-reg amendment discipline):
- v1 inner-CV grid REDUCED from 55,296 cells to 16 representative cells (M × Kelly × symbol) at fixed H062-modal feature cell (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0). Full-grid tracked under `P1-H065-FULL-INNER-CV-GRID-V2`.
- Cost model = ZERO at v1.
- Single-unit entry; no pyramiding (pyramiding overlay deferred to H066 successor).
- v1 reports current-equity rebase per ADR-0017 §4.1 + ADR-0024 paradigm (different from H062 v1's fixed-equity rebase per the H062 KPI report card §11.3 scope deviation).

## 14. Cross-references

- **Parent hypothesis**: [H062](../H062/design.md) (no-TP baseline; same substrate, same feature factory).
- **Sibling**: [H066](../../../hypothesis_backlog.md) (queued; H065 + Turtle System 2 pyramiding overlay).
- **Paradigm stack**: [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md), [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md), [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md), [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md), [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md), ADR-0024.

## 15. NinjaScript implementation (per ADR-0013 §5; mandatory)

Mandatory C# implementation per ADR-0013 §5: `ninjascript/strategies/H065_DonchianBreakoutWithTPOverlay.cs`. Same entry/exit logic as the H062 C# implementation per H062 design.md §15 + additional TP-overlay branch in OnBarUpdate (limit order at `entry ± M × k_atr × ATR_n` placed simultaneously with stop-loss at entry; OCO bracket-order pair). Sim101 smoke-test record + ScriptSubmission timestamps + position fills + final P/L per ADR-0013 §5.1.

Python ↔ NinjaScript parity-check per ADR-0013 §5.2: byte-equality on integer entry/exit signal vector + per-trade exit-reason classification. Tracked under `P1-H065-NINJASCRIPT-IMPL` (mandatory per ADR-0013 §5; operator-discretionary decline allowed per 2026-05-04 standing directive).

## 16. Substrate provenance

Substrate: [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/); `output_frame_sha256 = b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260516.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260516.json). Includes H1-2026 extension landed 2026-05-15 + 2026-05-16 batch.

## 17. Revision log

- **2026-05-15** (initial pre-registration): `status: designed` frozen. TP-overlay extension of H062 v1; M-grid {1.0, 1.5, 2.0, 2.5}; pyramiding deferred to H066. Pre-reg authored under audit-remediate-loop discipline (3-round cap); 1-round inline audit applied at draft time; full audit trail at [docs/audits/audit_trail_2026-05-15_h065_v1.md](../../../docs/audits/audit_trail_2026-05-15_h065_v1.md).
