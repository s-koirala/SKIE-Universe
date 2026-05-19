---
hypothesis_id: H068
schema_version: hypothesis_design_v1
status: designed
tier: 2c
created: 2026-05-19
created_by: skoir
description: Cost-light genetic successor of H065 v2 M_inf-ES cell — preserves Donchian-channel + first-fire dwell + ATR-stop + ID_1 trend gate + no-TP-overlay signal-generation mechanic verbatim; primary cost-reduction axis is sub-1-tick slip empirical sensitivity sweep `slip_per_side ∈ {0.25, 0.5, 1.0}` ticks anchored on retail-tier liquid CME equity-index practitioner-anecdotal patterns; pre-registered concurrently with the post-Phase-O.16 fee recalibration that empirically demoted H067 (SIL successor) from #1 to #2 and promoted H068 to #1 by cost-friction-breakeven ratio (1.27 unchanged; CRR for ratio ≥ 2 = 36.7%, 15.6pp lower hurdle than H067 SIL's 52.3%).
---

# H068 — Cost-light Donchian channel-breakout on ES standalone, with sub-1-tick slip empirical sensitivity as primary cost-reduction axis

> **Genetic successor of [H065 v2 M_inf-ES cell](../H065/H065_kpi_report_v2.md).** H068 preserves every mechanical layer of the H065 v2 M_inf no-TP-overlay variant on ES (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; fixed-equity rebase per H062 v1 modal cell per H065 v2 M_inf_h062_v1_fixed-ES anchor; Kelly multiplier grid per ADR-0018 D-2; let-it-run on Donchian channel break/reverse + ATR stop + EOD-flatten on RTH) **verbatim** and adds **ONE** new mechanic: a sub-1-tick slip empirical sensitivity sweep over `slip_per_side ∈ {0.25, 0.5, 1.0}` ticks at the cost-model layer. Position size remains 1-lot per cell at v1 (N-lot scaling deferred to H068 v2 successor per single-axis ADR-0027 §D-4 discipline).
>
> **Hypothesis-of-record (H_1)**: under sub-1-tick empirical slip calibration AND verified ES exchange fees (CME 2024-02 Individual Member Electronic schedule, unchanged through Phase O.16 + cost-light-aware operation (`nt8_realistic_v1` cost model per ADR-0025 §D-3 with `sensitivity_mult ∈ {1.0, 0.5, 0.25}` parametrically swept), there exists a `slip* ∈ {0.25, 0.5, 1.0}` tick (with `slip*` corresponding to `sensitivity_mult* = slip* / 1.0`) such that the realized ES OOS ROI ≥ 0% with stationary-bootstrap CI excluding zero positively on per-session log-return MPPM(ρ=1). The cost-friction-breakeven ratio at `slip*` rises above the [cross-hypothesis investigation 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md) §6.3 + [addendum 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md) §3 cost-friction-dominated-edge-present ratio ≥ 2 threshold AND zero-cost A0 reference > 0 hold simultaneously.
>
> **Honest pre-empirical caveat on the slip-reduction mechanism**: under the canonical [nt8_realistic_v1 conservative_prior](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) cost model, slip is parameterized by `slip_per_side_usd = sensitivity_mult × tick_value` per the existing `_compute_round_trip_cost_per_contract` semantic (see [src/skie_ninja/backtest/costs/nt8_realistic.py:225-227](../../../src/skie_ninja/backtest/costs/nt8_realistic.py)). At ES tick_value = $12.50 (per [config/instruments.yaml ES](../../../config/instruments.yaml) primary spec), `sensitivity_mult=1.0` → slip $12.50/side per contract; `sensitivity_mult=0.5` → slip $6.25/side; `sensitivity_mult=0.25` → slip $3.125/side. Total ES round-trip per contract at the three `sensitivity_mult` cells: $29.10 (1.0-tick); $16.60 (0.5-tick; -43%); $10.35 (0.25-tick; -64%). **The empirical reasonableness of sub-1-tick slip on liquid ES retail-tier futures is anchored on the cross-hypothesis investigation 2026-05-19 §7.2 practitioner-anecdote range (retail-tier liquid CME equity-index futures typically see 0.3-0.7 tick average slippage on market orders during RTH high-liquidity hours)**. The H_1 inferential criterion above is operationally evaluable at the v1 emission via the `sensitivity_mult ∈ {1.0, 0.5, 0.25}` parametric sweep without requiring paper-trade fill data; the v1 KPI report card directly answers "how much slip reduction is needed to push the ES cell above the cost-friction-dominated-edge-present threshold." Volume-tier-based commission discount per [config/instruments.yaml fee_tiers_es_nq](../../../config/instruments.yaml) Tier 2 ≥ 1,000 contracts/month ($1.18 → $1.14 = -3.4%) + Tier 3 ≥ 10,000 contracts/month ($1.18 → $1.09 = -7.6%) is an ORTHOGONAL secondary cost-reduction axis flagged but NOT actively swept at v1 (operator-discretionary; CME tier thresholds anchored on real broker passthrough rates).
>
> **Full Phase N + Phase O.0 + Phase O.4 + ADR-0024 + Phase O.16 paradigm inheritance.** H068 inherits the same paradigm stack as H067 + the post-2026-05-19 Phase O.16 fee verification: [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) permanent-exploration / no-binding-gates / mandatory-NinjaScript-terminus / non-loss preservation + [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) canonical 13-table results-summary + [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained primary metric vector + K-1..K-8 kill switches + FM-1..FM-5 stress-test suite + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) inner-CV fitness + Kelly-multiplier grid + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness annotation + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism §1.3 annotation + [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) metals/energy substrate (out-of-scope for ES — equity-index already covered by pre-Phase-O.16 verified fees) + [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) opt-in framing + [ADR-0025](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) abandonment-trigger primitives + [ADR-0026](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) §0 3-component KPI summary header + promising-* annotation + [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) cell-budget cap + walk-forward-window-as-bounded-set + genetic-successor §17 discipline + [ADR-0028](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) K-6/K-7 size-down enforcement-mode + cost-friction-dominated-edge annotation.
>
> **Out of scope at v1 (alternate cost-reduction axes deferred per single-axis ADR-0027 §D-4 discipline)**: N-lot position-size scaling deferred to `P1-H068-V2-N-LOT-SCALING-PATH-DELAYED` (H067 R1 audit established that N-lot is NOT a cost-reduction mechanism at conservative_prior; the H068 v1 axis is empirical slip refinement instead); bar-cadence reduction (mechanism 2; daily / 4-hour bars rather than 5-min) deferred to `P1-H068-V2-COST-REDUCTION-AXIS-BAR-CADENCE`; longer-hold-time variant (mechanism 3; extended hold-time-cap) deferred to `P1-H068-V2-COST-REDUCTION-AXIS-LONGER-HOLD`. These are mechanically orthogonal and warrant independent v2 pre-registrations per ADR-0027 §D-4 single-axis-genetic-cross discipline.

## 1. Hypothesis

- **H_0**: For every `slip ∈ {0.25, 0.5, 1.0}` tick, AT LEAST ONE of: (a) realized ES OOS ROI < 0% under the corresponding `sensitivity_mult` cost-model cell, OR (b) per-cell MPPM(ρ=1) stationary-bootstrap CI covers zero, OR (c) cost-friction-breakeven ratio < 2 (i.e., per-trade gross-edge insufficient to dominate per-trade cost burden at the empirical slip prior).
- **H_1**: There exists a `slip* ∈ {0.25, 0.5, 1.0}` tick such that (a) realized ES OOS ROI > 0% at the corresponding `sensitivity_mult` cost-model cell, (b) MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero positively, AND (c) cost-friction-breakeven ratio ≥ 2 — qualifying the cell for `cost-friction-dominated-edge-present` per ADR-0028 §D-2. The recommended `slip*` (operator-discretionary) is the LARGEST slip value satisfying all three conditions (Pareto-front interpretation: largest slip tolerance under which H_1 still clears = most operationally robust threshold), with the sub-1-tick range `{0.25, 0.5}` providing the empirical-slip-reduction surface and the 1.0-tick `sensitivity_mult=1.0` cell preserved as the conservative_prior baseline anchor.
- **Predictand**: same as H065 — per-trade R-multiple `R_t = realized_PL_t / |1R_t|` per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py); per-session-aggregated ES log-return series for MPPM(ρ=1) per design.md §1 of H062. **ES standalone, NOT 4-symbol basket** — the cell-genetic-cross isolates ES specifically because the [cross-hypothesis investigation 2026-05-19 addendum](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md) §3 identified the H065 v2 M_inf_h062_v1_fixed ES cell as the empirically-strongest cost-light successor candidate at rank #1 post-Phase-O.16 (ratio 1.266 unchanged; CRR 36.7%; pre-cost OOS +40.54% on 110 trades).
- **Test statistic** (load-bearing): per-slip-cell `T_H068(slip) = MPPM(ρ=1)[r_ES_OOS_session_aggregated(slip)]` where the simulator is re-run with `nt8_realistic_v1(sensitivity_mult = slip/1.0)` cost model and otherwise-identical mechanics. Family size at the ES standalone level = 3 cells (one per slip value); per-slip-cell-per-Kelly-multiplier family = 3 × 6 = 18 under [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER family-wise correction. **slip=1.0-tick cell reported alongside as the conservative_prior baseline** for direct comparability to the cross-hypothesis investigation addendum §3 ratio-1.27 anchor.
- **Secondary inferential KPIs** (per ADR-0017 §1.2 demotion machinery): Sharpe-differential vs passive-long ES under [Ledoit-Wolf 2008 *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap CI; Hansen 2005 SPA p reported as KPI annotation per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md); Calmar-differential + profit-factor + R-multiple-mean per [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md).

### 1.2 Cost-friction-dominated-edge annotation (per ADR-0028 §D-2)

H068 v1 SHALL emit explicit zero-cost A0 reference cells alongside conservative_prior A1 cells at the same slip × Kelly-multiplier grid to enable the `cost-friction-dominated-edge-{present, absent, n/a}` annotation per ADR-0028 §D-2 trigger semantics. The v1 KPI report card §"Methodological-correctness annotations" line carries the annotation per-cell as the load-bearing operator-readable disclosure.

The annotation grammar:
- `cost-friction-dominated-edge-present` (per-slip-cell) — realized OOS ES ROI > 0 at A0 zero-cost AND realized OOS ES ROI < 0 at A1 `sensitivity_mult=1.0` AND cost-friction-breakeven ratio computed per cross-hypothesis investigation §2 ≥ 2.
- `cost-friction-dominated-edge-absent` — A1 cell does NOT flip the realized OOS from positive to negative.
- `cost-friction-dominated-edge-n/a` — only PRE-cost A0 cell emitted (no cost-model context).

### 1.3 Causal-mechanism annotation (per ADR-0022)

- **Claim type**: `hybrid` (inherits H065's causal mechanism on the channel-break-as-information-event signal layer; sub-1-tick slip empirical sensitivity layer is **correlation-only refinement** on top of the inherited mechanism). <!-- justify: ADR-0022 §3 grammar; signal mechanism preserved verbatim from parent H065 + H062 design.md §1.3 hybrid framing; slip-refinement layer is an empirically-observed pattern (retail-tier liquid CME futures realize sub-1-tick slip during RTH high-liquidity hours per cross-hypothesis investigation §7.2 practitioner-anecdote anchor) with NO theoretical mechanism-derivation in the underlying microstructure literature -->
- **Mechanism description (who/what/why/when)** — inherits H065 design.md §1.3 verbatim for the upstream signal mechanism:
  - **Who**: market participants on E-mini S&P 500 (ES) front-month contract during RTH primary session (08:30-15:15 CT) per [config/instruments.yaml ES session_rth](../../../config/instruments.yaml).
  - **What**: Donchian-channel break is an information-revelation event — bar t close beyond N-bar high/low signals that prior-range-extreme has been exceeded.
  - **Why**: [Hong-Stein 1999 *J Finance* 54(6):2143-2184 DOI 10.1111/0022-1082.00184](https://doi.org/10.1111/0022-1082.00184) underreaction mechanism (slow information diffusion across market participants) + [Bouchaud-Gefen-Potters-Wyart 2004 *Quantitative Finance* 4(2):176-190 DOI 10.1088/1469-7688/4/2/007](https://doi.org/10.1088/1469-7688/4/2/007) stop-order liquidity clustering at multi-bar pivots (channel-extreme touches induce stop-loss cascades that prolong the move beyond the breakout bar).
  - **When**: PIT-causally at bar t close + entry at bar t+1 open per H062 + H065 design.md §4 fill convention.
- **Sub-1-tick slip sensitivity layer is correlation-only**: no causal claim about which slip value is "the true empirical slip". The slip-sweep is grid-searched per §5; the recommended `slip*` per H_1 is operator-discretionary per the Pareto-front above. The empirical realism of sub-1-tick slip at retail-tier ES depends on (a) order book depth at fill time, (b) RTH vs ETH session liquidity stratification, (c) order type (market vs limit), (d) order size relative to top-of-book — all of which are characterizable by paper-trade fill-data capture per `P1-H068-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION`.
- **E-value / robustness anchor**: per ADR-0022 §3 the [VanderWeele-Ding 2017 *Ann Intern Med* 167(4):268-274 DOI 10.7326/M16-2607](https://doi.org/10.7326/M16-2607) E-value primitive at [src/skie_ninja/inference/e_value.py](../../../src/skie_ninja/inference/e_value.py) is closed (Phase O.1 follow-on). H068 KPI report card v1 carries the E-value annotation against the H065 v2 M_inf-ES parent at the same substrate-vintage.

### 1.4 Pre-empirical caveat: H068 is a cost-light variant of a small-sample mean-edge factor

H068 inherits H065's §1.4 partial-decay caveat verbatim with one addition: the H065 v2 M_inf_h062_v1_fixed-ES parent cell's cost-friction-breakeven ratio is **1.266** per the [cross-hypothesis investigation 2026-05-19 addendum](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md) §3 row #1 (36.855 bps-of-equity per-trade gross-edge vs 29.100 bps-of-equity round-trip cost at conservative_prior). This is **above unity but below the cost-friction-dominated-edge-present threshold** (ratio ≥ 2 per ADR-0028 §D-2) — the per-trade gross-edge has structural headroom over per-trade cost, but the operator-task-spec inferential criterion (ratio ≥ 2) requires a **36.7% cost reduction** (CRR per addendum §3) to clear.

**Per-trade gross-edge is 2.8× larger than H067-SIL parent cell** (ES 36.855 bps-of-equity vs SIL 13.119 bps-of-equity per addendum §3 rows #1 + #2). This is the structural reason ES is the empirically-stronger cost-light successor candidate post-Phase-O.16. The trade-volume trade-off: ES has 110 trades vs SIL's 5,600 (51× less statistical power); this is documented as the H068 statistical-power caveat below.

**Statistical-power caveat for H068** (per cross-hypothesis investigation addendum §3 framing): the n_trades = 110 figure is at-or-near the threshold below which per-cell R-multiple-distribution CIs become wide. Per [Tharp 1998 *Trade Your Way to Financial Freedom*](https://www.amazon.com/Trade-Way-Financial-Freedom-Tharp/dp/0070647623) (*practitioner*; 1st ed ISBN 978-0070647626) typical R-multiple-distribution-CI requires n ≥ 30 for narrow CI; n = 110 is comfortably above that threshold but well BELOW H067's n = 5,600. The point estimate (+40.54% / 110 trades) is reliable but its CI is wider than SIL's by approximately a factor of √(5600/110) ≈ 7.1×. H068 SHALL declare a `n_min_trades = 50` precondition per §11.2 to ensure post-cost-light-filtering the cell retains enough trades to be statistically meaningful.

**H062 v3 ablation as the load-bearing case-study**: the [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) memo establishes that cost-only at conservative_prior drives basket OOS from +261.88% (A0) to −99.99997% (A1) on IDENTICAL trades. The H068 v1 design.md §1 question is the structurally-symmetric inverse: can sub-1-tick slip refinement (combined with the parent cell's already-above-unity ratio of 1.27) push the per-cell ratio above the ADR-0028 §D-2 cost-friction-dominated-edge-present threshold (≥ 2) so that the H062 v3 A0 → A1 saturation-to-bankruptcy mechanism is structurally averted?

**Expected H065-relative effect of sub-1-tick slip refinement at conservative_prior** (pre-empirical; not load-bearing):
- **sensitivity_mult = 1.0** (baseline): ratio 1.27; per-trade gross-edge 36.855 bps-of-equity vs cost 29.100 bps-of-equity; below cost-friction-dominated-edge-present (ratio < 2) but above unity.
- **sensitivity_mult = 0.5** (mid-range empirical sensitivity): ratio rises to ~2.22 (per-trade cost drops to ~16.60 bps-of-equity; per-trade gross-edge unchanged at 36.855 bps-of-equity); JUST CROSSES the cost-friction-dominated-edge-present threshold.
- **sensitivity_mult = 0.25** (aggressive sub-1-tick): ratio rises to ~3.56 (per-trade cost drops to ~10.35 bps-of-equity); WELL ABOVE threshold.
- **No slip cell expected to dominate** all 4 ADR-0017 primary survival-constrained metrics simultaneously — operator review on the Pareto-front (largest `slip*` satisfying ratio ≥ 2 AND MPPM CI strict-positive) is the load-bearing decision.

### 1.5 Pre-empirical caveat on ES standalone vs basket framing

Inherits H062 design.md §1.5 verbatim with adjustment for ES-only scope. ES-only has effective basket breadth = 1 (no diversification). The H_1 inferential question is cell-conditional, NOT basket-aggregate; SPA family size at v1 = 3 slip-cells × 6 Kelly-multipliers = 18 (per §1 above). Family-wise correction per Romano-Wolf 2005.

## 2. Universe and sample period

- **Instrument at v1**: ES (E-mini S&P 500; CME Globex; index $50/point multiplier; tick_size 0.25 → tick_value $12.50 per [config/instruments.yaml ES](../../../config/instruments.yaml)). **ES standalone, NOT 4-symbol basket** per §1 above.
- **Cross-asset diversification deferred**: 4-symbol basket framing (ES + NQ + MGC + SIL) inherited from H062/H065 deliberately omitted at v1 to isolate the ES cell-grid mechanic. Cross-asset extension tracked under `P1-H068-V2-CROSS-ASSET-BASKET-EXTEND` (non-blocking).
- **Substrate availability** (BINDING; canonical post-Phase-O.10 substrate on main HEAD):
  - **Verified `output_frame_sha256`**: `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) per CLAUDE.md Phase O.10 substrate re-derivation (run_id `38d63bdd2def4fa9804c78fbcb1a76ce`). Includes the H1-2026 extension through 2026-05-15 + 2026-Q2-extension through 2026-05-15.
  - **ES coverage per provenance**: 2020-01-01 → 2026-05-15 (≥ 11 partitions). Total H068 v1 universe = 1 symbol × 11+ partitions.
- **Sample window** (BINDING; pre-reg-frozen):
  - **Calibration holdout**: 2020-01-01 → 2020-12-31 (ES; 1 year). <!-- justify: ES substrate begins 2020-01-01 (no pre-2020 ES coverage in canonical post-Phase-O.10 substrate per CLAUDE.md Phase O.10 §"Substrate row counts" table); 1-year calibration window aligns with the H067 SIL multi-year 2015-2019 calibration window framing scaled to ES coverage; full 4-year IS reserves 2021-2023 for inner-CV cell selection per ADR-0027 §D-2 bounded set -->
  - **IS**: 2021-01-01 → 2023-12-31 (3 years; aligned with H065 v2 IS window adjusted for ES 2020-onward coverage).
  - **OOS test**: 2024-01-01 → 2026-05-15 (~2.5 years; matches H065 v2 OOS window).
  - **2026-04-01 → 2026-05-15 sub-window**: mandatory reporting cell per ADR-0026 §D-1 §0 3-component summary header (component 2 — Realized OOS 2026-onward sub-window).
- **Cadence**: 5-minute bars primary (inherited from H062/H065 v1 modal cell). <!-- justify: 5-min is the H065 v2 M_inf-ES parent cell's modal cadence per H065 design.md §5 + H065 KPI report card §8; preserved verbatim per ADR-0027 §D-4 single-axis-genetic-cross discipline (slip is the axis; cadence is preserved infrastructure) -->
- **Session policy**: ES is RTH-only (08:30-15:15 CT per [config/instruments.yaml ES session_rth](../../../config/instruments.yaml)); EOD-flatten at 15:00 CT per H062 + H065 RTH-equity-index convention. ETH bars excluded from H068 v1 eligibility per H065 v2 modal cell preservation.
- **Roll treatment**: per-asset roll-adjusted front-month continuous series per [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) post-Phase-O.0 deliverable. Inherited from H062.
- **Cost model — TWO cells at v1 per ADR-0028 §D-2 zero-cost-A0-reference convention × 3 slip sensitivity cells**:
  - **A0 (zero-cost reference)**: emitted for each (slip × Kelly-multiplier) cell; annotation `cost-zero`. Required by ADR-0028 §D-2 for cost-friction-dominated-edge annotation evaluation. **Note**: A0 zero-cost is independent of `sensitivity_mult` (zero × any multiplier = zero); structurally identical across slip cells but emitted for the annotation grammar evaluation.
  - **A1 (`sensitivity_mult ∈ {1.0, 0.5, 0.25}`)**: emitted for each (slip × Kelly-multiplier) cell; annotation `cost-conservative-prior` at `sensitivity_mult=1.0` per ADR-0025 §D-5 baseline; annotation `cost-empirical-slip-{0.5,0.25}-tick` at the sub-1-tick cells (NEW v1 annotation grammar extension per §10 + §13 below); cost-model `nt8_realistic_v1` per [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) with `sensitivity_mult` parametrically applied per the existing `_compute_round_trip_cost_per_contract` semantic.
  - Paper-trade-empirical full calibration deferred to `P1-H068-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED stage transition; not blocking v1 emission — the v1 parametric sweep over `{1.0, 0.5, 0.25}` is the v1 deliverable; paper-trade data refines the empirical-slip prior at paper-trade phase).

**ES fee schedule** (canonical post-Phase-O.16; UNCHANGED from pre-Phase-O.16 since ES was not in Phase O.16 scope per [config/instruments.yaml lines 49-51](../../../config/instruments.yaml)):
- `commission_per_side_usd: 0.85` (NinjaTrader Brokerage Unlimited Q1-2026 published placeholder; broker-specific override pre-live per `commission_reviewed_for_broker` field convention)
- `exchange_fee_usd: 1.18` (CME Individual Member Equity Index electronic, Schedule of Fees eff. 2024-02; **PRIMARY-SOURCE-VERIFIED**)
- `nfa_fee_usd: 0.02` (NFA Rulebook Section 13, eff. 2024-01-01)
- Per-side fixed = $0.85 + $1.18 + $0.02 = $2.05; round-trip fixed = $4.10
- Slip at `sensitivity_mult=1.0`: 1-tick × $12.50 tick_value = $12.50/side × 2 sides = $25.00 round-trip
- Total round-trip at conservative_prior = $4.10 + $25.00 = $29.10 per contract
- Total round-trip at `sensitivity_mult=0.5`: $4.10 + $12.50 = $16.60 per contract (-43%)
- Total round-trip at `sensitivity_mult=0.25`: $4.10 + $6.25 = $10.35 per contract (-64%)

Per the cross-hypothesis investigation addendum §1 footnote: ES fees were already CME-verified effective 2024-02 per the [config/instruments.yaml ES line 50](../../../config/instruments.yaml) comment; ES is NOT in Phase O.16 scope. The H068 v1 substrate-validity is therefore not subject to the same metals-fee-recalibration risk that affects H067.

## 3. Features

H068 inherits **every feature** from H062 design.md §3 verbatim per the H065 §3 precedent (inheritance chain: H062 → H065 → H068 single-axis cross). No new feature is introduced — sub-1-tick slip empirical sensitivity is a cost-model-layer extension at §6, not a feature at §3.

- Donchian channel (close-to-close N-bar high/low; PIT-causal at bar-(t-1)) at channel_n = 120 (H065 v2 M_inf-ES parent modal cell).
- ATR Wilder (atr_n = 14; H065 modal).
- Trend-strength filter ID_1 = "a_ts_mom" with L=60, τ=1.0 (H065 modal).
- News-time exclusion features (FOMC ±15min; NFP ±5min; CPI ±5min per [src/skie_ninja/utils/news_calendar.py](../../../src/skie_ninja/utils/news_calendar.py)).

Feature factory at [src/skie_ninja/features/h062/](../../../src/skie_ninja/features/h062/) is **reused verbatim** for H068. No new feature module is added.

## 4. Label construction

H068 inherits H065 design.md §4 verbatim WITH `M = ∞` fixed (no TP overlay; let-it-run on Donchian channel break/reverse). Per the H065 KPI report card §1 finding that the M=∞ no-TP variant produced the strongest ES standalone cell at the H065 v2 M_inf_h062_v1_fixed variant (ES +40.54% pre-cost OOS at 110 trades per [cross-hypothesis investigation addendum §3 row #1](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md)), the M=∞ specification is the load-bearing parent cell preserved verbatim.

Per-trade P/L on a Donchian-channel-breakout signal with ATR-scaled stop + **NO profit target** + opposite-channel exit + EOD-flatten on RTH.

- **Entry**: same as H062 + H065. Limit-or-market order at the next bar (t+1) open, conditional on (i) channel-break detector fires at bar-t close, (ii) ID_1 trend-strength filter admits the side, (iii) bar t+1 is in the eligible-bar set (RTH only per §2 session policy).
- **No profit target** (M = ∞ binding per parent-cell preservation): position runs to channel-reverse OR ATR-stop OR EOD-flatten.
- **Stop**: `SL_long = entry - k_atr × ATR_n,t`; `SL_short = entry + k_atr × ATR_n,t` (k_atr = 2.0 fixed per H065 modal).
- **Time stop / EOD flatten**: 15:00 CT per ES RTH convention.
- **Opposite-channel exit**: channel-flip in same bar closes position at bar's close.
- **Exit precedence within bar** (BINDING; PIT-resolved):
  1. **Gap-through-stop** at bar-t open (open beyond SL): close at open.
  2. **Stop hit** during bar (low ≤ SL_long or high ≥ SL_short): close at SL price.
  3. **Opposite-channel break** at bar-t close (channel signal flips against position): close at bar-t close.
  4. **EOD flatten** at session-cutoff bar: close at bar-t close.
  5. **Session rollover** (next bar's session differs): close at bar-t close.

**Position sizing — 1-lot at v1** (N-lot scaling DEFERRED to v2 per ADR-0027 §D-4 single-axis discipline + H067 R1 audit lesson that N-lot is NOT a cost-reduction mechanism under conservative_prior linear-scaling):

Position size at entry = `1 × kelly_multiplier × kelly_fraction × current_equity / (entry_price × multiplier)` where the Kelly-derived sizing yields integer-rounded position size per [src/skie_ninja/sizing/__init__.py](../../../src/skie_ninja/sizing/__init__.py) `compute_position_size` (existing primitive per ADR-0017 §4.1 + ADR-0028 §D-1).

**Position cap**: per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) ES retail capacity ≤ 20 contracts. The Kelly-derived sizing may produce position sizes well below this cap at retail-tier $10K starting equity (e.g., at quarter-Kelly × $10K equity × ES median 1R-cost ~$200-500, the Kelly-derived sizing typically yields 1-3 contracts). The cap is the upper-bound safety constraint; v1 sizing is Kelly-derived not cap-anchored.

**R-multiple definition** (per H062 §4 + Tharp 1998 *practitioner*): R = realized_PL / |1R| where |1R| = k_atr × ATR_n,t × multiplier × position_size. The R-multiple is **per-trade-unit**, not per-position; multi-contract trades realize R-multiple proportional to position_size.

## 5. Estimator

H068 inherits H062 design.md §5 verbatim with one extension at §5.2: the slip-sensitivity grid replaces the M-cell grid (H065) and the N-lot grid (H067) as the joint inner-CV cell selection axis (per ADR-0027 §D-4 single-axis-genetic-cross discipline).

- **§5.1 ID_1 trend-identifier**: FIXED at `a_ts_mom` with L=60, τ=1.0 per H065 v2 modal (no inner-CV selection; preserved infrastructure per ADR-0027 §D-4).
- **§5.2 sensitivity_mult + Kelly-multiplier selection** (NEW genetic axis): per-cell MPPM(ρ=1) on inner-CV out-of-fold per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1. **NEW joint grid**: `sensitivity_mult ∈ {1.0, 0.5, 0.25}` × `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per ADR-0018 D-2 = **18-cell joint grid**.
- **§5.3 Kelly-multiplier grid**: same as H062 + H065 + H067. `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per ADR-0018 D-2; super-Kelly cells `{1.5, 2.0, 2.5}` carry mandatory `super-kelly-operator-discretionary` annotation per ADR-0018 §D-2.
- **§5.4 BOCD signal-decay monitor**: same as H065 v2. Adams-MacKay 2007 BOCD on per-fold MPPM(ρ=1) path; hazard rate 1/100. Per ADR-0025 §D-4 the BOCD-live primitive may be enabled via design.md §11.1 opt-in declaration (not active at v1 per the parent-cell preservation discipline; deferred to v3 cycle).
- **§5.5 Switching-bandit allocation redirect**: deferred to v2/v3 successor (inherited deferral from H065 design.md §5.5; not in v1 scope).
- **§5.6 Walk-forward outer CV**: same as H062/H065/H067. Rolling 252-session-train / 60-session-test; embargo 2400 min. <!-- justify: 252-session train per ADR-0027 §D-2 bounded set {63, 126, 252, 504}; preserved from H065 v2 parent cell + H067 v1 inheritance -->
- **§5.7 Inner-CV selection metric**: MPPM(ρ=1) per ADR-0018 D-1 (Sharpe forbidden as inner-CV fitness post-2026-05-12 per ADR-0018 acceptance + ADR-0027 §D-2 reaffirmation).
- **§5.8 Inner-CV regularisation discipline + nested-CV structure**: Level-A (ID_1) fixed (no fitting); Level-B (sensitivity_mult × Kelly) joint inner-CV per Varma-Simon 2006.

**Joint inner-CV cell grid cardinality** (BINDING per ADR-0027 §D-2 cell-budget cap declaration):

| Axis | Grid | Cells |
|---|---|---:|
| Sensitivity_mult (slip per side in ticks) | {1.0, 0.5, 0.25} | 3 |
| Kelly multiplier | {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} | 6 |
| Cost-model arm (A0/A1) | {cost-zero, cost-conservative-prior-sensitivity_mult} | 2 |
| **Total** | | **36** |

H068 v1 cell-budget = 36 cells. <!-- justify: well under the ADR-0027 §D-2 v1 cap of 1000 cells; full grid sweep is operationally tractable. The 2× cost-model arm multiplier is mandatory per ADR-0028 §D-2 zero-cost-A0-reference convention. Note: 36-cell v1 is LESS than H067's 60-cell v1 because the slip-axis grid is 3-cell {1.0, 0.5, 0.25} vs H067's 5-cell N-lot grid {1, 2, 3, 4, 5}; the 3-cell choice anchors on cross-hypothesis investigation §7.2 practitioner-anecdotal slippage range -->

## 6. Cost model

Six cost-arm emissions at v1 per ADR-0028 §D-2 + §1.2 above × 3 slip cells:

- **A0 sub-arm (`cost-zero`)**: zero-cost adapter per ADR-0025 §D-5 grammar; emitted for each of the 3 slip cells (numerically identical across slip cells since zero × any multiplier = zero; emitted for ADR-0028 §D-2 annotation grammar evaluation).
- **A1 sub-arm at `sensitivity_mult=1.0` (`cost-conservative-prior`)**: `nt8_realistic_v1` per [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) with `sensitivity_mult=1.0` (1-tick slip prior; conservative_prior baseline) + per-ES fee schedule (per §2 above; commission $0.85/side + exchange $1.18/side + NFA $0.02/side = $2.05/side fixed-per-side; slip $12.50/side at 1-tick × $12.50 tick_value; total per side $14.55 = $29.10 round-trip per 1 contract; both commission AND slip scale linearly with `n_contracts` per [nt8_realistic.py:225-227](../../../src/skie_ninja/backtest/costs/nt8_realistic.py)).
- **A1 sub-arm at `sensitivity_mult=0.5` (`cost-empirical-slip-0.5-tick`)**: `nt8_realistic_v1` with `sensitivity_mult=0.5` (0.5-tick slip empirical sensitivity exhibit; total slip $6.25/side = $12.50 round-trip; total round-trip $16.60).
- **A1 sub-arm at `sensitivity_mult=0.25` (`cost-empirical-slip-0.25-tick`)**: `nt8_realistic_v1` with `sensitivity_mult=0.25` (0.25-tick slip aggressive sensitivity exhibit; total slip $3.125/side = $6.25 round-trip; total round-trip $10.35).

**Cost-friction-breakeven mechanics at ES sub-1-tick slip refinement** (anchored on cross-hypothesis investigation 2026-05-19 addendum §3 row #1 H065 v2 M_inf_h062_v1_fixed-ES parent cell):

| Sensitivity_mult (slip per side) | Per-side fixed $ | Per-side slip $ | Total per-side $ | Round-trip $ | Cost bps-of-equity at $10K | Per-trade gross-edge bps-eq | Breakeven ratio (gross / cost) | Cost reduction vs baseline |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 (parent baseline) | $2.05 | $12.50 | $14.55 | $29.10 | 29.100 | 36.855 | **1.266** (per addendum §3 row #1) | baseline |
| **0.5** (mid empirical sensitivity) | $2.05 | $6.25 | $8.30 | $16.60 | 16.600 | 36.855 | **~2.220** | **-43%** |
| **0.25** (aggressive empirical sensitivity) | $2.05 | $3.125 | $5.175 | $10.35 | 10.350 | 36.855 | **~3.561** | **-64%** |

The **conservative_prior cost-model scaling is approximately invariant in the per-side fixed component (commission + exchange + NFA) and linear in the slip component**; the cost-friction-breakeven ratio rises monotonically as `sensitivity_mult` decreases. At `sensitivity_mult=0.5` the ratio **JUST CROSSES** the ADR-0028 §D-2 cost-friction-dominated-edge-present threshold (≥ 2); at `sensitivity_mult=0.25` it is **WELL ABOVE** threshold.

**Cost-reduction mechanism is conditional on empirical refinement** (the H_1 inferential question):
1. **Sub-1-tick empirical slippage**: per cross-hypothesis investigation §7.2, retail-tier liquid CME equity-index futures (ES, NQ) typically see 0.3-0.7 tick average slippage on market orders during RTH high-liquidity hours. The H068 v1 sweep over `sensitivity_mult ∈ {1.0, 0.5, 0.25}` directly answers "how much slip reduction is needed to push the ES cell above the cost-friction-dominated-edge-present threshold?" Per the breakeven table above, `sensitivity_mult=0.5` is sufficient.
2. **Volume-tier-based commission discount**: per [config/instruments.yaml fee_tiers_es_nq](../../../config/instruments.yaml) at ≥ 1,000 contracts/month Tier 2 kicks in ($1.18 → $1.14 = -3.4% exchange fee); ≥ 10,000 contracts/month Tier 3 ($1.18 → $1.09 = -7.6%). At 1-lot × ~50 ES trades/year (from the H065 v2 M_inf-ES 110-trade-OOS ratio extrapolated to annualized) the Tier 2 threshold is FAR below the trade rate. Volume-tier discount is therefore NOT a load-bearing cost-reduction axis at H068 v1 — it would be operationally relevant only at N-lot ≥ 5 × ≥ 50 trades/month = 250 contracts/month, still below Tier 2. Flagged as orthogonal secondary axis but NOT actively swept at v1.

**Empirical sensitivity emission requirement** (BINDING at v1 KPI emission): the H068 v1 KPI report card §3a SHALL include the §6 sensitivity table reproduced verbatim with the actual realized per-slip-cell ratio + post-cost realized OOS values. The 3-cell sensitivity sweep is OPERATOR-ACTIONABLE: it directly answers "is the H068 H_1 inferential criterion (ratio ≥ 2) achievable under the canonical conservative_prior at any sub-1-tick slip cell?"

**Note on ES fee verification status**: ES exchange fee ($1.18/side) is CME-verified effective 2024-02 per [config/instruments.yaml line 50](../../../config/instruments.yaml). ES is NOT in Phase O.16 metals/energy scope; the H068 v1 substrate-validity is NOT subject to the same fee-recalibration risk that affected H067 SIL ($0.45 → $1.00 = 122% increase). ES placeholder commission ($0.85/side) remains broker-specific; pre-live `commission_reviewed_for_broker` binding is non-blocking at v1.

## 7. PIT / leakage canaries

H068 inherits H062/H065 PIT canaries verbatim. No new canary is introduced — the slip-sensitivity layer does NOT affect PIT semantics (slip is a cost-model parameter applied at trade-close time using PIT-causal entry + exit prices both as-of trade-completion).

Inherited canary set:
- **Canary A — boundary-invariant**: channel state computed on full continuous PIT-causal panel; bit-identical channel values regardless of fold partition.
- **Canary B — label-horizon**: trade outcomes (exit-reason classification + realized P/L) use ONLY future bars relative to entry; no peeking.
- **Canary C — train-test leak**: NO cross-fold parameter sharing post-IS-cutoff.
- **Canary D — NaN-poison**: defensive structural-detector at orchestrator-entry per H062 v1 integration test.

Integration test `tests/integration/test_h068_pit_canaries.py` to be authored per `P1-H068-PIT-CANARY-INTEGRATION-TEST` (BLOCKING-BEFORE-FIRST-V1-LAUNCH).

## 8. Inferential structure

Per design.md §1 framing — H_1 is a **conjunctive test on each slip cell**: (a) realized ES OOS ROI > 0 at conservative_prior at corresponding `sensitivity_mult`, (b) MPPM(ρ=1) CI excludes zero positively, AND (c) cost-friction-breakeven ratio ≥ 2 (`cost-friction-dominated-edge-present` per ADR-0028 §D-2). The recommended `slip*` per the operator review is the LARGEST slip value satisfying all three conditions (Pareto-front interpretation; larger slip tolerance = more operationally robust threshold; sub-1-tick range provides the empirical-slip-reduction surface).

a. ADR-0017 §3 primary survival-constrained metric vector evaluated on each slip × Kelly-multiplier × cost-model cell (18 conservative_prior cells + 18 zero-cost A0 reference cells = 36 cells total).
b. Sharpe-differential (LW2008 CI) vs passive-long ES reported as secondary KPI per ADR-0017 §1.2.

Family-wise correction over the 3-slip-grid (or 18-cell slip × Kelly grid; operator-discretionary at KPI emission time) via [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER. Hansen 2005 SPA p reported as KPI annotation only per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md). DSR deflation per [Bailey-López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094) MANDATORY per ADR-0027 §D-2 since realized cell count 18 ≥ project's `dsr_activation_size = 10` per [config/gate.yaml](../../../config/gate.yaml).

## 9. Sample-size + power

Per H065 v2 M_inf_h062_v1_fixed-ES parent cell sample data: **110 OOS trades** over ~615 OOS sessions on ES (post-Phase-O.10 substrate). H068 retains the same sample-size envelope (slip-sensitivity does NOT affect entry counts; only per-trade cost subtraction). Per-slip-cell OOS sample = full 2024-01-01 → 2026-05-15 fold sweep per §2.

**Statistical-power caveat for H068** (per cross-hypothesis investigation addendum §3 framing): the n_trades = 110 figure is well above the Tharp 1998 *practitioner* n ≥ 30 threshold but well BELOW H067 SIL's n = 5,600. R-multiple-distribution-CI width scales by ~√(5600/110) ≈ 7.1× wider than SIL. Per `n_min_trades = 50` precondition declared in §11.2, post-cost-light-filtering must retain ≥ 50 trades per cell to ensure the H068 v1 KPI emission has tractable inferential power.

Power calibration `P1-H068-POWER-SIMULATION-EXECUTE` deferred (non-blocking; sample size is empirically adequate at n_trades ≈ 110 per cell with the 3-slip-grid family-wise correction).

## 10. Decision rule

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) no-binding-gates discipline: the per-slip-cell KPIs are reported in §13 alongside the H065 v2 M_inf_h062_v1_fixed-ES parent reference; the operator chooses promotion timing on the Pareto-front per H_1. Stage transitions per ADR-0013 §1 (`kpi-report-emitted` → `ninjascript-implemented`) are operator-discretionary per the user 2026-05-04 standing decline-ninjascript directive.

## 11. Threats to validity + kill switches

Inherits H062 + H065 + H067 design.md §11 + §11.1 (K-1..K-8) verbatim. The slip-sensitivity layer does NOT change kill-switch semantics:

- **K-1 (per-trade $-stop)**: 1.0R per Turtle 2N convention; ES median 1R ~$200-500 at k_atr=2.0 × ATR_14 × $50/point multiplier.
- **K-2 (time stop)**: same as H062 + H065 + H067 (EOD-flatten serves as implicit time stop at intraday cadence; ES RTH 15:00 CT flatten).
- **K-3 (no-add-to-loser)**: vacuous in H068 v1 (no pyramiding; 1-lot at v1).
- **K-4 (capacity ceilings)**: ES ≤ 20 contracts per ADR-0001 + H062/H065 design.md §11.1 K-4 binding. v1 uses 1-lot per cell (cap is informational; not binding at v1).
- **K-5 (correlated-instrument inventory cap)**: ES + MES inventory shares budget per H062 §11.1 K-5; MES not in H068 universe so K-5 N/A at v1.
- **K-6 (daily circuit breaker)**: −2% of equity realized P/L → halt new entries through end of session. <!-- justify: ADR-0017 §5 K-6 default convention; literature-canonical retail-trader risk threshold; ADR-0028 §D-1 `k6_enforcement` defaults to "block" for v1 per Task #20 empirical finding that size-down doesn't recover cost-dominated catastrophes; block default preserved -->
- **K-7 (weekly circuit breaker)**: −5% of equity realized P/L → halt new entries through end of week. <!-- justify: ADR-0017 §5 K-7 default convention; ADR-0028 §D-1 `k7_enforcement` defaults to "block" for v1 per Task #20 empirical finding -->
- **K-8 (adverse-direction entry filter)**: same as H062 + H065 + H067.

Per [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) §D-2 opt-in framing, K-3 + K-4 + K-6 + K-7 are **opt-in** at v1 per design.md §11.1 declaration with `enable_k4=True + enable_k6=True + enable_k7=True` (preserves [src/skie_ninja/backtest/kill_switch_runtime.py](../../../src/skie_ninja/backtest/kill_switch_runtime.py) ADR-0025 §D-1 defaults).

### 11.1 Kill-switch + abandonment-trigger opt-in declaration

Per [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) §D-2 + ADR-0025 §D-1 + ADR-0028 §D-1 opt-in declarations:

| Primitive | Status at v1 | Enforcement mode |
|---|---|---|
| Kill-switch runtime K-3 (no-add-to-loser) | DISABLED (vacuous at H068 v1 single-unit; no pyramiding) | n/a |
| Kill-switch runtime K-4 (per-symbol cap) | ENABLED at ES ≤ 20 contracts | block (ADR-0028 §D-1 default; v1 1-lot does not approach cap) |
| Kill-switch runtime K-6 (daily circuit breaker) | ENABLED at −2% × equity_at_session_start | **block** at v1 (ADR-0028 §D-1 default; size-down opt-in deferred to v2 per `P1-H068-V2-WITH-K6-K7-SIZE-DOWN`) <!-- justify: v1 preserves H065 v2 modal cell mechanic verbatim; the ADR-0028 §D-1 size-down enforcement-mode is a separate genetic-axis warranting independent v2 evaluation; Task #20 empirical finding that size-down doesn't recover cost-dominated catastrophes supports block default -->|
| Kill-switch runtime K-7 (weekly circuit breaker) | ENABLED at −5% × equity_at_week_start | **block** at v1 (ADR-0028 §D-1 default; Task #20 empirical finding) |
| Equity rebase | FIXED-equity per H065 v2 M_inf_h062_v1_fixed-ES parent cell <!-- justify: parent-cell preservation per ADR-0027 §D-4; the H065 v2 M_inf_h062_v1_fixed-ES variant uses fixed-equity rebase per H062 v1 modal; current-equity rebase is a separate v3 axis warranting independent evaluation per `P1-H068-V3-CURRENT-EQUITY-REBASE` --> | n/a |
| BOCD live-pause | DISABLED at v1 (no calibrated priors; deferred to v3 cycle per `P1-BOCD-LIVE-PRIOR-CALIBRATION-H068-V3`) | n/a |

### 11.2 BLOCKING preconditions (pre-launch)

| ID | Status | Description |
|---|---|---|
| `P1-H068-WALK-FORWARD-ORCHESTRATOR-IMPL` | OPEN; BLOCKING-BEFORE-LAUNCH | Fork [scripts/run_h065_tp_overlay_sweep.py](../../../scripts/run_h065_tp_overlay_sweep.py) → [scripts/run_h068_slip_sensitivity_sweep.py](../../../scripts/run_h068_slip_sensitivity_sweep.py) per H068 design.md §15 + §17.1 preserved-infrastructure binding. The new orchestrator extends the existing slip-sensitivity parameter pass-through (already supported by `nt8_realistic_v1` per [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py)) to iterate over `sensitivity_mult ∈ {1.0, 0.5, 0.25}` per cell. |
| `P1-H068-ES-SUBSTRATE-VERIFICATION` | OPEN; BLOCKING-BEFORE-LAUNCH | Verify ES partition coverage on canonical substrate `317429e4...` against H065 v2 sidecar; SHA-match on ES partitions; bar-count + first-last-timestamp match. |
| `P1-H068-LEVEL-STATE-FOLD-CONTINUITY` | OPEN; INHERITED FROM H062 (closed for H062 v1) | Channel-state-at-fold-boundary unit test; H062 has the canonical implementation. H068 inherits per channel computation reuse. |
| `P1-H068-PIT-CANARY-INTEGRATION-TEST` | OPEN; BLOCKING-BEFORE-LAUNCH | Integration test at `tests/integration/test_h068_pit_canaries.py` per H062 v1 canary set inheritance. |
| `P1-H068-SUBSTRATE-PER-PARTITION-SHA-EMIT` | OPEN; BLOCKING-BEFORE-V1-EMISSION | Walk-forward orchestrator emits per-ES-partition SHA list in v1 sidecar `dataset_checksums.per_partition` field per H068 data_requirements.md §"Per-partition SHA enumeration". |
| `P1-H068-REPROLOG-WIRE` | OPEN; BLOCKING-BEFORE-V1-EMISSION | Wrap orchestrator execution in `RunContext` per ADR-0017 §3 + ADR-0026 §D-2 mandatory-verbosity carveout. Avoid the H065 v1 retrofit pattern documented in [research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md](../H065/H065_kpi_report_v1_corrigendum_2026-05-18.md). |
| `P1-H068-N-MIN-TRADES-GUARD` | OPEN; BLOCKING-BEFORE-V1-EMISSION | Walk-forward orchestrator asserts post-cost-light-filtering per-cell n_trades ≥ 50 per §9 statistical-power caveat. Cell failing the guard emits `power-margin-low` annotation per ADR-0014 §3.2 Table 8 + skips that cell from the per-slip-Pareto-front aggregation. |
| `P1-H068-PROD-RUN` | OPEN | First production walk-forward + KPI report card v1. |

Closed inherited primitives: `P1-MPPM-RHO-1-FITNESS-PRIMITIVE`, `P1-BOCD-DECAY-DETECTOR-PRIMITIVE`, `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE`, `P1-L-SKEWNESS-PRIMITIVE-IMPL`, `P1-CALMAR-DIFFERENTIAL-CI-IMPL`, `P1-PROFIT-FACTOR-CI-IMPL`, `P1-R-MULTIPLE-CI-IMPL`, `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`, `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE`, `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`, `P1-H055-NEWS-CALENDAR-INGEST` (via H062 feature-factory reuse), `P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL`, `P1-SIDECAR-LEVEL-A0-ZERO-COST-REFERENCE-WIRE` (per ADR-0028 §D-2 — verify orchestrator emits A0 cells alongside A1 per the 2-cost-arm spec in §5), `P1-METALS-ENERGY-CME-FEE-VERIFY` (closed Phase O.16; ES not in scope — already CME-verified effective 2024-02 per [config/instruments.yaml line 50](../../../config/instruments.yaml)).

## 12. Reproducibility

H068 inherits the full SKIE-Universe reproducibility discipline: deterministic RNG seed `20260519` for all bootstrap + Monte Carlo invocations; RunContext per [src/skie_ninja/utils/runcontext.py](../../../src/skie_ninja/utils/runcontext.py); ReproLog at `logs/reproducibility/<run_id>.json`; sidecar `scientific_payload_sha256` binding; substrate dataset_checksum binding to `317429e4...`. Pre-commit non-loss guard per [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

ReproLog 13-field schema MANDATORY at v1 KPI emission per `P1-H068-REPROLOG-WIRE` (BLOCKING-BEFORE-V1-EMISSION); the H068 walk-forward orchestrator MUST wrap execution in `RunContext` to emit canonical ReproLog (avoiding the H065 v1 retrofit pattern documented in [research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md](../H065/H065_kpi_report_v1_corrigendum_2026-05-18.md)).

## 13. Sensitivity exhibits + scope deviations

**Required sensitivity exhibits**:
- **Per-slip cell** at v1 KPI report card §"End-of-simulation results summary" 13-table format per ADR-0014 §3.2 + ADR-0019 §3.
- **Per-slip + per-Kelly-multiplier × per-cost-arm 36-cell heatmap** with cells classified per ADR-0028 §D-2 `cost-friction-dominated-edge-{present, absent, n/a}` annotation.
- **Cost-friction-breakeven ratio sensitivity table** under `sensitivity_mult ∈ {1.0, 0.5, 0.25}` per §6 binding (operator-actionable diff between conservative_prior and empirical-slip-reduction).
- **slip=1.0-tick (parent baseline)** alongside in the KPI report card as the direct-comparability reference to H065 v2 M_inf_h062_v1_fixed-ES cross-hypothesis investigation addendum 2026-05-19 anchor (parent breakeven ratio = 1.266).
- **2026-04-01 → 2026-05-15 sub-window** (~6 weeks; mandatory per ADR-0026 §D-1 §0 3-component header component 2).

**Scope deviations from full-spec inner-CV grid** (recorded per Path A frozen-pre-reg amendment discipline):
- v1 inner-CV grid REDUCED from the full H062 §5 13,824-cell combinatorial grid (per H065 §5.2 inheritance) to a tractable 36-cell representative grid (slip × Kelly × cost-arm) at fixed H065 v2 modal feature cell (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0). Full-grid tracked under `P1-H068-FULL-INNER-CV-GRID-V2`.
- ES-only at v1 (no 4-symbol basket; cross-asset extension tracked under `P1-H068-V2-CROSS-ASSET-BASKET-EXTEND`).
- SIX cost-model arm cells at v1 (3 sensitivity_mult × {A0, A1}) per ADR-0028 §D-2 × §6 binding; paper-trade-empirical full calibration deferred to v3 per `P1-H068-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION`.
- Single-unit entry (1-lot); no pyramiding (per H065 + H068 v1 preservation; N-lot scaling deferred to v2 successor per `P1-H068-V2-N-LOT-SCALING-PATH-DELAYED`).
- v1 reports fixed-equity rebase per H062 v1 modal (per H065 v2 M_inf_h062_v1_fixed-ES anchor preservation).
- M=∞ no-TP-overlay (fixed; not a grid axis) per H065 v2 M_inf_h062_v1_fixed-ES parent-cell preservation.
- Inner-CV walk-forward window = 252-session-train / 60-session-test per ADR-0027 §D-2 bounded set {63, 126, 252, 504}; preserved from H065 v2 parent.

## 14. Cross-references

- **Parent hypothesis**: [H065](../H065/design.md) (H065 v2 M_inf_h062_v1_fixed-ES cell at `kpi-report-emitted`; first KPI emission 2026-05-15; v2 retroactive emission on canonical substrate `317429e4...` per CLAUDE.md Phase O.10 extension).
- **Sibling cost-light successor**: [H067](../H067/design.md) (H067 v1 SIL standalone with N-lot grid; pre-registered 2026-05-19 commit `f71a6df` at `status: designed`; demoted from #1 to #2 in cost-light successor candidate ordering post-Phase-O.16 per [INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md) §3).
- **Grandparent hypothesis**: [H062](../H062/design.md) (H068 inherits feature factory + walk-forward orchestrator + PIT canaries verbatim per the H065 §3 inheritance chain).
- **Empirical anchor**: [cross-hypothesis investigation 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md) + [addendum 2026-05-19](../_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum_2026-05-19.md) (H065 v2 M_inf_h062_v1_fixed-ES breakeven ratio = 1.266 anchor; cost-light genetic-successor candidacy per §3 #1 post-Phase-O.16; CRR for ratio ≥ 2 = 36.7%).
- **H062 v3 ablation precedent**: [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) (load-bearing case-study for cost-friction-dominated-edge mechanism).
- **Sibling** (also deferred): [H066](../../../hypothesis_backlog.md) (queued; H065 + Turtle System 2 pyramiding overlay).
- **Paradigm stack**: ADR-0001 + ADR-0008 + ADR-0013 + ADR-0014 + ADR-0017 + ADR-0018 + ADR-0019 + ADR-0020 + ADR-0022 + ADR-0023 + ADR-0024 + ADR-0025 + ADR-0026 + ADR-0027 + ADR-0028.

## 15. NinjaScript implementation (per ADR-0013 §5; mandatory upon operator approval)

Mandatory C# implementation per [ADR-0013 §5](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): `ninjascript/strategies/H068_CostLightDonchianES.cs`.

C# class structure (skeleton; full implementation deferred to `P1-H068-NINJASCRIPT-IMPL`):
- **Class name**: `H068_CostLightDonchianES`
- **File path**: [ninjascript/strategies/H068_CostLightDonchianES.cs](../../../ninjascript/strategies/H068_CostLightDonchianES.cs)
- **Inheritance**: `NinjaTrader.NinjaScript.Strategies.Strategy`
- **Hyperparameter mapping** (Python ↔ C#):
  - `channel_n: int = 120` ↔ `[NinjaScriptProperty(Description="Donchian channel period")] public int ChannelN { get; set; } = 120;`
  - `k_atr: double = 2.0` ↔ `[NinjaScriptProperty(Description="ATR stop multiplier")] public double KAtr { get; set; } = 2.0;`
  - `atr_n: int = 14` ↔ `[NinjaScriptProperty(Description="ATR period")] public int AtrN { get; set; } = 14;`
  - `kelly_multiplier: double = M*` (operator-selected from {0.25..2.5} at deployment) ↔ `[NinjaScriptProperty(Description="Kelly multiplier")] public double KellyMultiplier { get; set; } = 0.25;`
  - **NinjaScript NOTE**: the H068 v1 sensitivity_mult parameter is a Python-backtest cost-model-layer parameter that does NOT have a NinjaScript counterpart — NinjaScript Sim101 fills are simulated against live order book, not against a parametric slip model. The H068 paper-trade phase via NinjaScript Sim101 measures the EMPIRICAL slip directly per `P1-H068-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION`; the parametric sweep is BACKTEST-ONLY at v1 KPI emission.
- **Entry / exit logic 1:1 with Python**: Donchian channel + ATR stop + first-fire dwell + ID_1 trend gate + EOD-flatten (15:00 CT RTH) per H062 + H065 design.md §15 patterns.
- **Kill-switch parameters per §11.1**: K-4 enforced via `Position.Quantity` cap; K-6 / K-7 enforced via running daily/weekly P/L accumulator with `EnterLong` / `EnterShort` rejection on breach (block-mode per ADR-0028 §D-1 default).
- **Fill-log schema matching plan §6.1**: CSV with `(timestamp_ct, symbol, side, n_contracts, entry_price, exit_price, exit_reason, realized_pl_usd)` columns per H062 + H065 §15 + project plan §6.1.
- **Sim101 smoke-test record**: ScriptSubmission timestamps + position fills + final P/L per ADR-0013 §5.1 deferred to `P1-H068-NINJASCRIPT-SIM101-SMOKE-RECORD`.

Python ↔ NinjaScript parity-check per ADR-0013 §5.2: byte-equality on integer entry/exit signal vector + per-trade exit-reason classification. Tracked under `P1-H068-NINJASCRIPT-IMPL` (mandatory per ADR-0013 §5; operator-discretionary decline allowed per 2026-05-04 standing directive).

## 16. Substrate provenance

Substrate: [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/); `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) per CLAUDE.md Phase O.10 substrate re-derivation (run_id `38d63bdd2def4fa9804c78fbcb1a76ce`).

Per-partition ES SHA enumeration at v1 freeze: see [data_requirements.md](data_requirements.md) §"Per-partition SHA enumeration".

## 17. Revision log

- **2026-05-19** (initial pre-registration): `status: designed` frozen. Cost-light genetic successor of H065 v2 M_inf_h062_v1_fixed-ES cell; primary cost-reduction axis = sub-1-tick slip empirical sensitivity sweep `sensitivity_mult ∈ {1.0, 0.5, 0.25}` ticks; alternate cost-reduction axes (volume-tier commission discount; N-lot scaling; bar-cadence reduction; longer-hold) deferred to v2 follow-ups per ADR-0027 §D-4 single-axis-genetic-cross discipline. Two-cost-arm emission (A0 zero-cost + A1 conservative_prior at 3 slip cells) per ADR-0028 §D-2 zero-cost-A0-reference convention × §6 sensitivity sweep. Pre-reg authored under audit-remediate-loop discipline (3-round cap per SKILL.md); 1-round Round-1 audit applied at draft time; full audit trail at [docs/audits/audit_trail_2026-05-19_h068-cost-light-h065-es-design.md](../../../docs/audits/audit_trail_2026-05-19_h068-cost-light-h065-es-design.md).

### 17.1 Genetic-successor cross-citation (per ADR-0027 §D-4 four-field mandatory disclosure)

| Field | Value |
|---|---|
| **Parent hypothesis ID + final stage** | H065 v2 at `kpi-report-emitted` per CLAUDE.md Phase O.10 extension; specifically the **M_inf_h062_v1_fixed-ES cell** (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; fixed-equity rebase per H062 v1 modal). The H065 v1 emission produced realized OOS +40.54% at MPPM CI (wider than H067 SIL's, per addendum §3 statistical-power caveat) on 110 trades; H065 v2 retroactive emission on canonical substrate `317429e4...` per CLAUDE.md Phase O.10 extension confirms the parent-cell pre-cost ROI envelope. |
| **Motivating KPI / annotation** | **Cross-hypothesis investigation 2026-05-19 addendum §3 row #1**: H065 v2 M_inf_h062_v1_fixed-ES standalone cell carries cost-friction-breakeven ratio **1.266** (36.855 bps-of-equity per-trade gross-edge vs 29.100 bps-of-equity round-trip cost at conservative_prior) — above unity but below the cost-friction-dominated-edge-present threshold (≥ 2); pre-cost OOS +40.54% (110 trades). Cell-level annotation: `likely-marginal-pending-A0` per investigation §2 schema. **The genetic-cross hypothesis**: sub-1-tick empirical-slip refinement (e.g., the cross-hypothesis investigation §7.2 practitioner-anecdotal range of 0.3-0.7 tick on RTH ES) would push the cell above the ADR-0028 §D-2 `cost-friction-dominated-edge-present` threshold (ratio ≥ 2). At `sensitivity_mult=0.5` ratio rises to ~2.22 (just crosses threshold); at `sensitivity_mult=0.25` ratio rises to ~3.56 (well above). H068 v1 measures the structural sensitivity of the ratio to slip refinement under conservative_prior + emits operator-actionable "how much slip reduction is needed" diff via the 3-cell sweep. **Post-Phase-O.16 H068 is empirically the #1 cost-light successor candidate** (CRR 36.7% — 15.6pp lower hurdle than H067 SIL's 52.3% post-recalibration). |
| **Genetic-cross** | **SINGLE AXIS** per ADR-0027 §D-4 single-axis-genetic-cross discipline. Cross-axis: sub-1-tick slip empirical sensitivity sweep `sensitivity_mult ∈ {1.0, 0.5, 0.25}` (corresponding to slip $12.50, $6.25, $3.125 per side per contract at ES tick_value $12.50). Cost-arm grid (A0 zero-cost + A1 conservative_prior at 3 slip cells) per ADR-0028 §D-2 zero-cost-A0-reference convention. NO change to: signal-generation mechanic (channel_n + k_atr + atr_n + h_dwell + trend_id all fixed at H065 v2 modal values); exit precedence (channel-reverse + ATR-stop + EOD-flatten on RTH); cost-model class (`nt8_realistic_v1` per ADR-0025 §D-3; only the `sensitivity_mult` parameter is swept). Volume-tier commission discount per [config/instruments.yaml fee_tiers_es_nq](../../../config/instruments.yaml) flagged as ORTHOGONAL secondary cost-reduction axis but NOT actively swept at v1 (Tier 2 ≥ 1,000 contracts/month is far above the 1-lot × ~50 ES trades/year volume rate; operator-discretionary at paper-trade phase). The N-lot scaling (mechanism deferred per H067 R1 audit lesson that N-lot is NOT a cost-reduction mechanism under conservative_prior linear-scaling) + bar-cadence-reduction (mechanism 2) + longer-hold-variant (mechanism 3) cost-reduction axes are deferred to v2 successors per ADR-0027 §D-4 single-axis discipline. |
| **Preserved infrastructure** | Substrate `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.10 main-HEAD); H062 feature factory at [src/skie_ninja/features/h062/](../../../src/skie_ninja/features/h062/); H065 v2 walk-forward orchestrator at [scripts/run_h065_tp_overlay_sweep.py](../../../scripts/run_h065_tp_overlay_sweep.py) (to be forked to [scripts/run_h068_slip_sensitivity_sweep.py](../../../scripts/run_h068_slip_sensitivity_sweep.py) per `P1-H068-WALK-FORWARD-ORCHESTRATOR-IMPL`); H062 v1 PIT canaries verbatim ([tests/integration/test_h062_pit_canaries.py](../../../tests/integration/test_h062_pit_canaries.py)); ADR-0017 + ADR-0018 + ADR-0019 + ADR-0022 inner-CV machinery + KPI annotation grammar; ADR-0014 §3.2 13-table format + ADR-0026 §D-1 §0 3-component summary header + ADR-0028 §D-4 `kill-switch-mode-{block,size-down}` + `cost-friction-dominated-edge-{present,absent,n/a}` annotations; ADR-0025 abandonment-trigger primitives (kill-switch runtime ENABLED at v1 with block-mode default per Task #20 finding; equity-rebase FIXED per parent cell; BOCD live-pause + size-down enforcement DEFERRED). Cell-budget cap = 36 cells per ADR-0027 §D-2 declaration (under 1000 v1 cap). Inner-CV fitness = MPPM(ρ=1) per ADR-0018 D-1. RNG seed = `20260519`. ES fee schedule UNCHANGED from pre-Phase-O.16 (NOT in Phase O.16 scope; CME-verified effective 2024-02 per [config/instruments.yaml line 50](../../../config/instruments.yaml)). |
