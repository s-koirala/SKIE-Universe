---
hypothesis_id: H068_v2
schema_version: hypothesis_design_v1
status: designed
tier: 2c
created: 2026-05-20
created_by: skoir
parent_hypothesis_id: H068
parent_hypothesis_kpi: H068_kpi_report_v1.md
description: Multi-instrument basket expansion of H068 v1 cost-light Donchian channel-breakout. Genetic successor per ADR-0027 §D-4 single-axis discipline; single cross-axis = universe expansion from ES standalone to 3-symbol basket {ES, MGC, SIL} on the canonical post-Phase-O.10 substrate. Closes `P1-H068-V2-EXPANDED-SUBSTRATE` BLOCKING follow-up registered by Phase O.18 closure synthesis. Inferential motivation = lift H068 v1 statistically-underpowered conjunctive H_1 NULL (n_trades=108 below 252-session bootstrap saturation) to a power-clear evaluation via multi-instrument breadth (expected basket n_trades ≈ 7,200 ≥ 70× v1).
---

# H068 v2 — Multi-instrument basket expansion of H068 v1 cost-light Donchian channel-breakout on {ES, MGC, SIL}

> **Genetic successor of [H068 v1 KPI v1](../H068/H068_kpi_report_v1.md).** Per ADR-0027 §D-4 single-axis-genetic-cross discipline + the empirical motivation from CLAUDE.md Phase O.18 closure (the H068 v1 "edge present, statistically underpowered" verdict at n_trades=108 was the load-bearing motivation for `P1-H068-V2-EXPANDED-SUBSTRATE`). H068 v2 preserves every mechanical layer of H068 v1 (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0; fixed-equity rebase per H062 v1 modal; ATR-stop + EOD-flatten + opposite-channel exit per H062 §4; slip-sensitivity sweep `sensitivity_mult ∈ {1.0, 0.5, 0.25}` ticks per H068 v1 §6; A0 zero-cost + A1 conservative-prior cost-arms per ADR-0028 §D-2) **verbatim** and adds **ONE** new mechanic per ADR-0027 §D-4 single-axis discipline: **universe expansion from ES standalone to a 3-symbol basket {ES, MGC, SIL}** on the canonical post-Phase-O.10 substrate.
>
> **Hypothesis-of-record (H_1)**: under the v1 verified ES + MGC + SIL exchange fees on canonical substrate `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`, with per-symbol cost-friction-breakeven ratio inherited from the parent v1 emission, there exists a `slip* ∈ {0.25, 0.5, 1.0}` tick such that the BASKET-aggregated per-session log-return MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero positively at that slip cell AND cost-friction-breakeven ratio ≥ 2 on at least 2 of 3 symbols (`cost-friction-dominated-edge-present` per ADR-0028 §D-2 at the basket level).
>
> **Honest pre-empirical caveat — empirical motivation, not improved-edge hypothesis** (per CLAUDE.md Phase O.18 strategic finding): v2 expansion lifts inferential POWER, NOT mean-edge per se. Per [H062 v2 KPI report card §"2026 sub-window" diagnostic](../H062/H062_kpi_report_v2.md), the H062-family signal class produces n_trades roughly proportional to substrate-availability × symbol trade-frequency. ES standalone (H068 v1) yielded n=108 over 2020-2026 OOS; multi-instrument {ES, MGC, SIL} expansion yields expected basket n_trades ≈ 7,200 per H062 v2 trade-frequency observation (MGC 3,928 + SIL 3,180 + ES 93 over the same 2020-2026 window per [H062 v3 smoke sidecar](../../../artifacts/runs/H062/154237b365794244974068402b377191/sidecar.json) per-symbol trade activity table). Per-cell MPPM CI width shrinks by ~√(7200/108) ≈ 8.2× under the basket-level evaluation. **This is the load-bearing improvement axis at v2 — narrower CI under the same per-trade mean-edge, NOT a new signal-class hypothesis.**
>
> **NQ deliberately omitted from the v2 basket** per Phase O.10 + H062 v2 + H065 v1 + H068 v1 empirical finding that NQ structurally produces 0 trades at $10K retail starting equity (per `P1-H065-MNQ-SUBSTITUTION` documented in [H065 KPI v1 §"Empirical structural findings"](../H065/H065_kpi_report_v1.md)). NQ tick_value $5/tick × ATR-stop sizing × 1% Kelly-derived risk floor produces position size < 1 contract at $10K. MNQ substitution would resolve this but requires a new Databento extraction for the H068-universe partition coverage (MNQ NOT in canonical substrate `317429e4...` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) confirmed symbol set `{ES, NQ, MGC, SIL, MCL}`); MNQ-extension deferred per `P1-H068-V2-MNQ-EXTENSION-V3` (BLOCKING-BEFORE-V3-WITH-MNQ). The H068 v2 basket {ES, MGC, SIL} provides 3-asset breadth across equity-index (ES) + metals (MGC, SIL) without requiring a new substrate extraction.
>
> **MCL deliberately omitted from the v2 basket** per H060 v1 + H065 v1 precedent (2021-07-12 inception precludes the 2020-2026 OOS coverage symmetry with ES/MGC/SIL). Tracked under existing `P1-H068-V2-WITH-CL-MCL-EXTEND` (deferred to v3 successor on the H061 substrate-extension cycle).
>
> **Full paradigm inheritance**: H068 v2 inherits the same paradigm stack as H068 v1: ADR-0013 + ADR-0014 + ADR-0017 (survival-constrained primary metric vector + K-1..K-8 kill switches + FM-1..FM-5) + ADR-0018 (MPPM(ρ=1) inner-CV fitness + Kelly-multiplier grid + BOCD decay monitor) + ADR-0019 (L-skewness annotation) + ADR-0022 (causal-mechanism §1.3 annotation) + ADR-0024 (opt-in framing) + ADR-0025 (abandonment-trigger primitives) + ADR-0026 §0 (mandatory 3-component KPI summary header) + ADR-0027 §D-4 (genetic-successor 4-field cross-citation) + ADR-0028 (K-6/K-7 size-down + cost-friction-dominated-edge annotation).
>
> **Out of scope at v2** (per ADR-0027 §D-4 single-axis-genetic-cross discipline; alternate cross axes deferred): N-lot position-size scaling deferred to `P1-H068-V3-N-LOT-SCALING-PATH-DELAYED` (H067 R1 audit + Phase O.18 strategic finding established that N-lot at conservative_prior is NOT a cost-reduction mechanism); bar-cadence reduction (daily/4-hour) deferred to `P1-H068-V3-COST-REDUCTION-AXIS-BAR-CADENCE`; current-equity rebase deferred to `P1-H068-V3-CURRENT-EQUITY-REBASE`; BOCD live-pause integration deferred to `P1-H068-V3-BOCD-LIVE` (calibration depends on the v2 per-session log-return aggregate per `P1-BOCD-CALIBRATION-PRE-OOS-HOLDOUT`); finer-grained slip sub-sweep deferred to `P1-H068-V3-COST-FRICTION-SENSITIVITY-EMPIRICAL-DEEPEN`.

## 1. Hypothesis

- **H_0**: For every `slip ∈ {0.25, 0.5, 1.0}` tick, AT LEAST ONE of: (a) BASKET-aggregated realized OOS ROI < 0% under the corresponding `sensitivity_mult` cost-model cell, OR (b) basket MPPM(ρ=1) stationary-bootstrap CI covers zero, OR (c) per-symbol cost-friction-breakeven ratio < 2 on ≥ 2 of 3 symbols at the corresponding slip cell.
- **H_1**: There exists a `slip* ∈ {0.25, 0.5, 1.0}` tick such that (a) basket realized OOS ROI > 0% at the corresponding `sensitivity_mult` cost-model cell, (b) basket MPPM(ρ=1) stationary-bootstrap CI strictly excludes zero positively, AND (c) per-symbol cost-friction-breakeven ratio ≥ 2 on at least 2 of 3 symbols (`cost-friction-dominated-edge-present` per ADR-0028 §D-2 at the basket-level). The recommended `slip*` (operator-discretionary) is the LARGEST slip value satisfying all three conditions (Pareto-front interpretation per H068 v1 §1).
- **Predictand**: per-trade R-multiple `R_t = realized_PL_t / |1R_t|` per [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py); BASKET-AGGREGATED per-session log-return series for MPPM(ρ=1) computed as equal-weighted sum across the 3-symbol basket per Goetzmann-Ingersoll-Spiegel-Welch 2007 §2 dimensional-consistency convention (cf. H062 design.md §1 + H060 v1 basket-aggregation pattern).
- **Test statistic** (load-bearing): per-slip-cell `T_H068_v2(slip) = MPPM(ρ=1)[r_basket_OOS_session_aggregated(slip)]` where the basket-aggregated per-session log-return series is the equal-weighted (1/3) sum of per-symbol per-session log-returns across {ES, MGC, SIL}. Family size at the basket level = 3 cells (one per slip value); per-slip × per-Kelly-multiplier × per-cost-arm grid family = 3 × 6 × 2 = 36 under [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER family-wise correction (same family size as H068 v1; basket aggregation does NOT multiply the cell count since per-symbol cells aggregate to one basket cell per parameter triple).
- **Secondary inferential KPIs** (per ADR-0017 §1.2 demotion machinery): per-symbol Sharpe-differential vs passive-long under [Ledoit-Wolf 2008 *JEF* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentized stationary-bootstrap CI; basket-aggregated LW2008 CI alongside; Hansen 2005 SPA p reported as KPI annotation per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md); Calmar-differential + profit-factor + R-multiple-mean per [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) at both per-symbol AND basket-aggregated granularity.

### 1.1 Empirical motivation per `P1-H068-V2-EXPANDED-SUBSTRATE`

H068 v1 (commit `4d14bfb` per CLAUDE.md Phase O.18) produced the project's **first cost-light positive realized ROI** (+23.12% at slip=0.5; A1 ratio 2.278; pre-empirical prediction VERIFIED within 3%). The H_1 conjunctive verdict was NULL only on criterion (b) — MPPM CI excludes zero positively — because n_trades=108 yielded CI width [-1.30, +3.05] at A1 conservative-prior slip=0.5 (per [H068 v1 KPI v1 Table 3](../H068/H068_kpi_report_v1.md)). The point estimate (+0.564) was positive but the CI was 7.1× wider than H067 SIL's n=5,600 equivalent. v2 expansion to a 3-symbol basket is the empirically-grounded inferential power-lift per `P1-H068-V2-EXPANDED-SUBSTRATE` (registered by Phase O.18 closure synthesis).

### 1.2 Cost-friction-dominated-edge annotation (per ADR-0028 §D-2)

H068 v2 SHALL emit explicit zero-cost A0 reference cells alongside conservative-prior A1 cells at the same slip × Kelly-multiplier grid PER SYMBOL to enable the `cost-friction-dominated-edge-{present, absent, n/a}` annotation per ADR-0028 §D-2 trigger semantics. Annotations emitted at BOTH per-symbol AND basket-aggregated levels; the basket-level annotation per H_1 criterion (c) requires ratio ≥ 2 on ≥ 2 of 3 symbols. The v2 KPI report card §"Methodological-correctness annotations" line carries the per-cell + basket-level annotation as the load-bearing operator-readable disclosure.

### 1.3 Causal-mechanism annotation (per ADR-0022)

- **Claim type**: `hybrid` (inherits H068 v1 + H065 + H062 §1.3 verbatim; multi-instrument basket expansion does NOT introduce a new causal mechanism — same Donchian channel-break-as-information-event signal layer on each symbol).
- **Mechanism description (who/what/why/when)** — inherits H068 v1 §1.3 verbatim per parent-cell preservation. The Hong-Stein 1999 underreaction + Bouchaud-Gefen-Potters-Wyart 2004 stop-order liquidity-clustering mechanisms apply to each symbol independently; basket aggregation is statistical (equal-weighted per-session log-return sum) not causal.
- **Multi-instrument basket aggregation is correlation-only**: no causal claim about cross-asset relationships; symbols are treated as independent draws from the same channel-break-signal-class distribution for inferential power-lift purposes. The basket-aggregated MPPM(ρ=1) trades higher per-cell statistical power for assumption of common signal-class distribution across {ES, MGC, SIL}; this is a standard meta-analytic move per [Grinold 1989 *JPM* 15(3):30-37 DOI 10.3905/jpm.1989.409211](https://doi.org/10.3905/jpm.1989.409211) Fundamental Law of Active Management (`IR ≈ IC · √breadth`).
- **E-value / robustness anchor**: per ADR-0022 §3 the [VanderWeele-Ding 2017](https://doi.org/10.7326/M16-2607) E-value primitive at [src/skie_ninja/inference/e_value.py](../../../src/skie_ninja/inference/e_value.py) is closed (Phase O.1 follow-on). H068 v2 KPI report card v1 SHALL carry the E-value annotation against the H068 v1 parent at the same substrate vintage `317429e4...`.

### 1.4 Pre-empirical caveat: H068 v2 is a power-lift on the H068 v1 marginally-positive cost-light variant, NOT a new signal-class hypothesis

Per CLAUDE.md Phase O.18 strategic finding, H068 v1 produced the first cost-light positive realized ROI in project history (+23.12% at slip=0.5) but H_1 conjunctive remained NULL on inferential-power grounds (CI width 7.1× SIL equivalent). v2 multi-instrument expansion targets the **statistical-power axis** (basket aggregation → narrower CI under same per-trade mean-edge), NOT the signal-class axis. Three load-bearing peer-reviewed primary sources document material decay in the channel-breakout family per the H062 + H065 + H068 chain's §1.4 partial-decay framing: [Marshall-Cahan-Cahan 2008 *J Banking & Finance* 32(9):1810-1819 DOI 10.1016/j.jbankfin.2007.12.011](https://doi.org/10.1016/j.jbankfin.2007.12.011); [Hsu-Kuan 2005 *J Financial Econometrics* 3(4):606-628 DOI 10.1093/jjfinec/nbi026](https://doi.org/10.1093/jjfinec/nbi026) (per the canonical [2026-05-18 erratum](../_erratum_hsu_kuan_2005_2026-05-18.md) ES tracks S&P 500 → mature-market classification; the H068 v1 +40.54% pre-cost OOS edge is the project's empirically-observed-positive counter-evidence to the Hsu-Kuan 2005 mature-market disfavor); [Park-Irwin 2007 *J Economic Surveys* 21(4):786-826 DOI 10.1111/j.1467-6419.2007.00519.x](https://doi.org/10.1111/j.1467-6419.2007.00519.x). Expected basket MPPM(ρ=1) under H_1 framed at **0.0-0.5 annualized log-wealth** with **narrower CI** than H068 v1 (per the inferential-power lift; same point-estimate envelope as H068 v1's [-1.30, +3.05] but shrunk to ~[-0.16, +0.37] under √(7200/108) factor). The H062 v2 + H055 v2 + H060 v2 cross-hypothesis empirical pattern is consistent: structural-property (skew-positive payoff τ_3 > 0; CI strictly excludes zero) but marginal mean-edge across the H062-family signal class.

### 1.5 Pre-empirical caveat: H068 v2 basket aggregation does NOT improve mean-edge — only narrows the CI

The basket-aggregated MPPM(ρ=1) point estimate is approximately the average of per-symbol MPPM(ρ=1) point estimates weighted by per-symbol n_sessions (the basket per-session log-return is the equal-weighted sum; the MPPM(ρ=1) of an equal-weighted sum is approximately the equal-weighted average MPPM at low Δt per the GISW 2007 §2 Δt → 0 limit). If individual per-symbol point estimates are scattered around zero (as observed in H068 v1 ES at +0.564 + H062 v2 per-symbol MGC/SIL/NQ analogous-cell estimates ranging −0.5 to +0.6 per the H062 v2 sidecar), the basket-aggregated point estimate will be near zero. **The v2 inferential value is NOT a higher point estimate; it is a narrower CI on the (likely-near-zero) point estimate.** The H_1 inferential criterion (b) is therefore a STRICTER test than v1: it requires the basket-aggregated point estimate to be both positive AND statistically distinguishable from zero at the post-aggregation narrower CI width.

**Sensitivity caveat — per-symbol MPPM divergence**: if per-symbol MPPM(ρ=1) point estimates are positive on some symbols and negative on others (e.g., +0.6 on MGC vs −0.4 on ES per a hypothetical observation), the basket aggregation may produce a near-zero point estimate that is statistically NEAR zero — failing H_1 even though some symbols carry per-symbol edge. The v2 KPI report card SHALL report per-symbol MPPM(ρ=1) CIs alongside the basket-aggregated CI to expose this potential divergence; operator may make symbol-selective promotion decisions on the per-symbol cells per ADR-0013 §1 operator-discretionary discipline.

## 2. Universe and sample period

- **Instruments at v2**: {ES, MGC, SIL} 3-symbol basket on the canonical post-Phase-O.10 substrate. <!-- justify: NQ produces 0 trades at $10K retail per H062 v2 + H065 v1 + H068 v1 empirical observation; MNQ substitution would resolve this but requires new Databento extraction per `P1-H068-V2-MNQ-EXTENSION-V3`; MCL has 2021-07-12 inception per H060 v1 precedent; the {ES, MGC, SIL} basket maximizes substrate-coverage with 3-asset breadth -->
- **Symbol roles**:
  - **ES** (E-mini S&P 500; equity-index): preserves the H068 v1 parent-cell signal class with verified ES fees (CME-verified effective 2024-02 per Phase O.16 NOT in scope).
  - **MGC** (Micro Gold; metals): inherits per-Phase-O.16 fee recalibration ($1.45/side per [config/instruments.yaml MGC](../../../config/instruments.yaml) per Phase O.16 commit `9a3a512` substrate update).
  - **SIL** (Micro Silver; metals): inherits per-Phase-O.16 fee recalibration ($1.00/side per [config/instruments.yaml SIL](../../../config/instruments.yaml) per Phase O.16 fee update).
- **Substrate availability** (BINDING; canonical post-Phase-O.10 substrate on main HEAD):
  - **Verified `output_frame_sha256`**: `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) (run_id `38d63bdd2def4fa9804c78fbcb1a76ce`). Includes ES + NQ + MGC + SIL + MCL coverage; H068 v2 universe is the 3-symbol subset {ES, MGC, SIL}.
  - **Per-symbol coverage per provenance**:
    - ES: 2020-01-01 → 2026-05-15 (12 partitions: years 2015-2026 per Phase O.0 ingest; ES first-row 2020-01-01).
    - MGC: 2015-01-01 → 2026-05-15 (12 partitions per Phase O.0 Stage A extraction).
    - SIL: 2015-01-01 → 2026-05-15 (12 partitions per Phase O.0 Stage A extraction).
  - **Total H068 v2 universe**: 3 symbols × ≥ 11+ partitions each = ≥ 33 partitions. Sub-1-tick slip empirical sensitivity sweep applied uniformly across all 3 symbols.
- **Sample window** (BINDING; pre-reg-frozen):
  - **Calibration holdout**: 2020-01-01 → 2020-12-31 (1 year; constrained by ES substrate start). <!-- justify: ES substrate begins 2020-01-01 per CLAUDE.md Phase O.10 §"Substrate row counts" table; MGC + SIL have pre-2020 coverage but the cross-symbol-comparability of the calibration window benefits from a uniform start per ADR-0027 §D-2 bounded-set discipline; matches H068 v1 §2 calibration holdout precisely -->
  - **IS**: 2021-01-01 → 2023-12-31 (3 years; matches H068 v1 IS window).
  - **OOS test**: 2024-01-01 → 2026-05-15 (~2.5 years; matches H068 v1 OOS window per parent-cell preservation).
  - **2026-04-01 → 2026-05-15 sub-window**: mandatory reporting cell per ADR-0026 §D-1 §0 3-component summary header (component 2 — Realized OOS 2026-onward sub-window).
- **Cadence**: 5-minute bars primary (inherited from H068 v1 § parent-cell preservation per ADR-0027 §D-4 single-axis-genetic-cross discipline).
- **Session policy**: Per-symbol session inheritance:
  - **ES**: RTH-only (08:30-15:15 CT per [config/instruments.yaml ES session_rth](../../../config/instruments.yaml)); EOD-flatten at 15:00 CT per H068 v1 + H062 § 2 RTH-equity-index convention.
  - **MGC + SIL**: 24/5 session per [src/skie_ninja/utils/clock.py](../../../src/skie_ninja/utils/clock.py) Phase O.0 metals/energy session extension; per-symbol EOD-flatten at 16:00 CT (session-rollover boundary; the 1-hour daily maintenance break 16:00-17:00 CT serves as the EOD-flatten convention for 24/5 instruments per the Phase O.0 §"Session policy" definition).
- **Roll treatment**: per-asset roll-adjusted front-month continuous series per [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) post-Phase-O.0 deliverable. Inherited from H062 + H068 v1.
- **Cost model — A0 + A1 per ADR-0028 §D-2 × 3 slip sensitivity cells × 3 symbols × 6 Kelly multipliers = 108 cells total** (vs H068 v1's 36 cells; 3× factor from universe expansion).

**Per-symbol fee schedules**:

| Symbol | commission_per_side_usd | exchange_fee_usd | nfa_fee_usd | tick_value | Source |
|---|---:|---:|---:|---:|---|
| ES | 0.85 | 1.18 | 0.02 | 12.50 | CME 2024-02 (verified pre-Phase-O.16) |
| MGC | 0.85 | 1.45 | 0.02 | 1.00 | CME 2024-02 (verified Phase O.16 per commit `9a3a512`) |
| SIL | 0.85 | 1.00 | 0.02 | 5.00 | CME 2024-02 (verified Phase O.16 per commit `9a3a512`) |

**Per-symbol round-trip cost** at v1 cost-arm cells (per side fixed = commission + exchange + nfa; per side slip = sensitivity_mult × tick_value; total per side = fixed + slip; round-trip = 2 × per-side):

| Symbol | sensitivity_mult | Per-side fixed $ | Per-side slip $ | Total per side $ | Round-trip $ |
|---|---:|---:|---:|---:|---:|
| ES | 1.0 | 2.05 | 12.50 | 14.55 | 29.10 |
| ES | 0.5 | 2.05 | 6.25 | 8.30 | 16.60 |
| ES | 0.25 | 2.05 | 3.125 | 5.175 | 10.35 |
| MGC | 1.0 | 2.32 | 1.00 | 3.32 | 6.64 |
| MGC | 0.5 | 2.32 | 0.50 | 2.82 | 5.64 |
| MGC | 0.25 | 2.32 | 0.25 | 2.57 | 5.14 |
| SIL | 1.0 | 1.87 | 5.00 | 6.87 | 13.74 |
| SIL | 0.5 | 1.87 | 2.50 | 4.37 | 8.74 |
| SIL | 0.25 | 1.87 | 1.25 | 3.12 | 6.24 |

**Per-symbol cost-reduction percentages at slip=0.5 vs slip=1.0 baseline**: ES −43% (round-trip $29.10 → $16.60); MGC −15% (round-trip $6.64 → $5.64; metals have lower slip-fraction-of-total because per-side fixed dominates); SIL −36% (round-trip $13.74 → $8.74). **Slip refinement is empirically more impactful on ES than on MGC** because ES tick_value $12.50 dominates the per-side cost; MGC tick_value $1.00 is small relative to per-side fixed $2.32, so slip refinement has smaller cost-reduction leverage on MGC.

**Cross-symbol cost-reduction asymmetry note**: the v2 KPI report card §6 SHALL emit the per-symbol breakeven-ratio sensitivity table per the H068 v1 §6 binding × 3 symbols, surfacing the load-bearing finding that **MGC's slip refinement does NOT cross the ADR-0028 §D-2 threshold (≥ 2) at any slip cell** under the per-symbol-fixed-dominated cost structure. The v2 basket-level evaluation must surface this asymmetry; per-symbol promotion decisions remain operator-discretionary per ADR-0013 §1.

## 3. Features

H068 v2 inherits **every feature** from H068 v1 + H065 + H062 design.md §3 verbatim per the single-axis-genetic-cross discipline (per ADR-0027 §D-4). No new feature is introduced — multi-instrument basket expansion is a universe-layer change at §2, not a feature-layer change at §3.

- Donchian channel (close-to-close N-bar high/low; PIT-causal at bar-(t-1)) at channel_n = 120 (H065 v2 M_inf-ES parent modal cell; preserved per parent-cell discipline).
- ATR Wilder (atr_n = 14; H065 modal).
- Trend-strength filter ID_1 = "a_ts_mom" with L=60, τ=1.0 (H065 modal).
- News-time exclusion features (FOMC ±15min; NFP ±5min; CPI ±5min per [src/skie_ninja/utils/news_calendar.py](../../../src/skie_ninja/utils/news_calendar.py)).

Feature factory at [src/skie_ninja/features/h062/](../../../src/skie_ninja/features/h062/) is **reused verbatim** for H068 v2 across all 3 symbols. No new feature module is added.

## 4. Label construction

H068 v2 inherits H068 v1 + H065 design.md §4 verbatim WITH `M = ∞` fixed (no TP overlay; let-it-run on Donchian channel break/reverse). Per-symbol per-trade P/L on a Donchian-channel-breakout signal with ATR-scaled stop + **NO profit target** + opposite-channel exit + EOD-flatten.

- **Entry**: same as H068 v1 (limit-or-market order at next bar t+1 open, conditional on channel-break + ID_1 trend-strength filter admits side + bar t+1 in eligible-bar set per per-symbol session policy from §2).
- **No profit target** (M = ∞ binding per parent-cell preservation).
- **Stop**: `SL_long = entry - k_atr × ATR_n,t`; `SL_short = entry + k_atr × ATR_n,t` (k_atr = 2.0 fixed per H065 modal).
- **Time stop / EOD flatten**: per-symbol per §2 session policy (15:00 CT for ES; 16:00 CT session-rollover for MGC + SIL).
- **Opposite-channel exit**: channel-flip in same bar closes position at bar's close.
- **Exit precedence within bar** (BINDING; PIT-resolved): inherited verbatim from H068 v1 + H062 §4.
  1. Gap-through-stop at bar-t open.
  2. Stop hit during bar.
  3. Opposite-channel break at bar-t close.
  4. EOD flatten at session-cutoff bar.
  5. Session rollover.

**Position sizing — 1-lot per symbol at v2** (N-lot scaling DEFERRED to v3 per ADR-0027 §D-4 single-axis discipline + H067 R1 audit lesson):

Position size at entry per symbol = `1 × kelly_multiplier × kelly_fraction × current_equity / (entry_price × multiplier)` where the Kelly-derived sizing yields integer-rounded position size per [src/skie_ninja/sizing/__init__.py](../../../src/skie_ninja/sizing/__init__.py) `compute_position_size` (existing primitive per ADR-0017 §4.1 + ADR-0028 §D-1). **Per-symbol independent sizing**: each symbol carries its own kelly_multiplier × kelly_fraction × current_equity allocation (no inter-symbol correlation adjustment at v2; correlation-aware allocation deferred to MPV2 cycle per `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION`).

**Per-symbol position caps**: per [ADR-0001](../../../docs/decisions/ADR-0001-project-scope.md) ES ≤ 20 contracts; MGC + SIL operate at micro-class capacity (no canonical cap; effectively unbounded at retail-tier given per-trade-risk-budget × $10K equity).

**R-multiple definition** (per H068 v1 + H062 §4 + Tharp 1998 *practitioner*): R = realized_PL / |1R| where |1R| = k_atr × ATR_n,t × multiplier × position_size per symbol. **Basket-aggregated R-multiple**: the basket-aggregated R-multiple-mean is the n_trades-weighted average across the 3 symbols per the [src/skie_ninja/inference/r_multiple.py](../../../src/skie_ninja/inference/r_multiple.py) primitive's basket-aggregation pattern.

## 5. Estimator

H068 v2 inherits H068 v1 + H062 + H065 design.md §5 verbatim. The slip-sensitivity grid + Kelly-multiplier grid + cost-arm grid is preserved verbatim per ADR-0027 §D-4 single-axis-genetic-cross discipline; the universe expansion to 3 symbols is the cross axis at §2, not the estimator axis.

- **§5.1 ID_1 trend-identifier**: FIXED at `a_ts_mom` with L=60, τ=1.0 per H068 v1 + H065 modal preservation.
- **§5.2 sensitivity_mult × Kelly-multiplier selection**: per-cell MPPM(ρ=1) on inner-CV out-of-fold per ADR-0018 D-1. Joint grid `sensitivity_mult ∈ {1.0, 0.5, 0.25}` × `kelly_multiplier ∈ {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` = 18-cell joint inner-CV per symbol; basket-level evaluation aggregates per-symbol cells per H_1.
- **§5.3 Kelly-multiplier grid**: same as H068 v1 + H062 + H065. `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` per ADR-0018 D-2; super-Kelly cells `{1.5, 2.0, 2.5}` carry mandatory `super-kelly-operator-discretionary` annotation per ADR-0018 §D-2.
- **§5.4 BOCD signal-decay monitor**: same as H065 v2 + H068 v1. Adams-MacKay 2007 BOCD on per-fold basket-aggregated MPPM(ρ=1) path; hazard rate 1/100. BOCD-live primitive deferred per ADR-0025 §D-4 opt-in declaration (not active at v2 per parent-cell preservation; deferred to v3 per `P1-H068-V3-BOCD-LIVE`).
- **§5.5 Switching-bandit allocation redirect**: deferred to v3 successor (inherited deferral from H065 + H068 v1 design.md §5.5; not in v2 scope).
- **§5.6 Walk-forward outer CV**: same as H068 v1. Rolling 252-session-train / 60-session-test; embargo 2400 min. <!-- justify: 252-session train per ADR-0027 §D-2 bounded set {63, 126, 252, 504}; preserved from H068 v1 parent + H065 v2 grandparent -->
- **§5.7 Inner-CV selection metric**: MPPM(ρ=1) per ADR-0018 D-1 (Sharpe forbidden as inner-CV fitness post-2026-05-12 per ADR-0018 acceptance + ADR-0027 §D-2 reaffirmation). **Per-symbol vs basket-aggregated inner-CV**: at v2 the inner-CV cell selection is per-symbol (preserves H068 v1 per-cell selection mechanic verbatim); the basket-aggregated MPPM is reported at outer-CV emission only as the H_1 inferential test statistic. This preserves the v1 inner-CV machinery without modification.
- **§5.8 Inner-CV regularisation discipline + nested-CV structure**: Level-A (ID_1) fixed (no fitting); Level-B (sensitivity_mult × Kelly) joint inner-CV per Varma-Simon 2006 per symbol.

**Joint cell grid cardinality** (BINDING per ADR-0027 §D-2 cell-budget cap declaration):

| Axis | Grid | Cells |
|---|---|---:|
| Symbols | {ES, MGC, SIL} | 3 |
| Sensitivity_mult (slip per side in ticks) | {1.0, 0.5, 0.25} | 3 |
| Kelly multiplier | {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} | 6 |
| Cost-model arm (A0/A1) | {cost-zero, cost-conservative-prior-sensitivity_mult} | 2 |
| **Total per-symbol** | | 36 |
| **Total all-symbols** | | **108** |

H068 v2 cell-budget = 108 cells. <!-- justify: well under the ADR-0027 §D-2 v1 cap of 1000 cells; full grid sweep is operationally tractable on the existing canonical substrate. The 3× factor from universe expansion brings cell count from H068 v1's 36 to 108; basket-level evaluation aggregates per-symbol cells per H_1 (the basket-aggregated MPPM is computed at outer-CV emission from per-symbol per-session log-returns; the inferential family size at the basket level remains 3 slip cells per H068 v1 §1 family-size convention) -->

## 6. Cost model

Per-symbol two-cost-arm emissions at v2 per ADR-0028 §D-2 + §1.2 above × 3 slip cells × 3 symbols × 6 Kelly multipliers = 108 cells total:

- **A0 sub-arm (`cost-zero`)** PER SYMBOL: zero-cost adapter per ADR-0025 §D-5 grammar; emitted for each (symbol × slip × Kelly) cell. Required by ADR-0028 §D-2 for per-symbol cost-friction-dominated-edge annotation evaluation.
- **A1 sub-arm at `sensitivity_mult=1.0` (`cost-conservative-prior`)** PER SYMBOL: `nt8_realistic_v1` per [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) with `sensitivity_mult=1.0` (1-tick slip prior) + per-symbol fee schedule (per §2 above).
- **A1 sub-arm at `sensitivity_mult=0.5` (`cost-empirical-slip-0.5-tick`)** PER SYMBOL: `nt8_realistic_v1` with `sensitivity_mult=0.5`.
- **A1 sub-arm at `sensitivity_mult=0.25` (`cost-empirical-slip-0.25-tick`)** PER SYMBOL: `nt8_realistic_v1` with `sensitivity_mult=0.25`.

**Per-symbol cost-friction-breakeven mechanics at sub-1-tick slip refinement**: see §2 fee schedules table; v2 KPI report card §6 SHALL reproduce the per-symbol breakeven-ratio sensitivity table verbatim with actual realized per-symbol per-slip ratio + post-cost realized OOS values.

**Pre-empirical caveat — H068 v2 universe expansion does NOT improve per-symbol cost-reduction leverage**: per §2 fee schedule analysis, MGC slip-fraction-of-total cost is small (per-side fixed $2.32 dominates per-side slip $1.00 at 1-tick) → slip refinement has limited leverage on MGC's cost-friction-breakeven ratio. ES + SIL retain higher slip-fraction-of-total → slip refinement remains load-bearing on those symbols. The basket H_1 criterion (c) — ratio ≥ 2 on ≥ 2 of 3 symbols — is **most likely to clear on ES + SIL specifically**; MGC may remain at ratio < 2 even at slip=0.25.

## 7. PIT / leakage canaries

H068 v2 inherits H068 v1 + H062/H065 PIT canaries verbatim. No new canary is introduced — universe expansion does NOT affect PIT semantics (the canaries operate at the per-symbol feature-factory layer; multi-instrument basket aggregation does NOT introduce cross-symbol leakage at the feature layer).

Inherited canary set:
- **Canary A — boundary-invariant**: channel state computed on full continuous PIT-causal panel per-symbol.
- **Canary B — label-horizon**: trade outcomes use ONLY future bars relative to entry per symbol.
- **Canary C — train-test leak**: NO cross-fold parameter sharing post-IS-cutoff per symbol.
- **Canary D — NaN-poison**: defensive structural-detector at orchestrator-entry per H062 v1 integration test.
- **Canary E (NEW per H068 v2)**: **cross-symbol-basket-aggregation invariant** — basket-aggregated MPPM(ρ=1) computed from per-symbol per-session log-returns should be invariant to symbol ordering. Smoke test: shuffle symbol order in basket-aggregation pipeline; basket MPPM must match within machine-precision tolerance. Tracked under new BLOCKING `P1-H068-V2-BASKET-INVARIANT-TEST` (tests/integration/test_h068_v2_basket_invariant.py).

Integration test `tests/integration/test_h068_v2_pit_canaries.py` to be authored per `P1-H068-V2-PIT-CANARY-INTEGRATION-TEST` (BLOCKING-BEFORE-FIRST-V2-LAUNCH; per-symbol canary set + Canary E basket-invariant).

## 8. Inferential structure

Per design.md §1 framing — H_1 is a **conjunctive test at the basket level**: (a) basket realized OOS ROI > 0 at A1 conservative-prior at corresponding `sensitivity_mult`, (b) basket-aggregated MPPM(ρ=1) CI excludes zero positively, AND (c) per-symbol cost-friction-breakeven ratio ≥ 2 on ≥ 2 of 3 symbols. The recommended `slip*` per operator review is the LARGEST slip value satisfying all three conditions (Pareto-front interpretation per H068 v1 §8).

a. ADR-0017 §3 primary survival-constrained metric vector evaluated on each slip × Kelly-multiplier × cost-model cell PER SYMBOL + basket-aggregated (108 per-symbol cells + 36 basket-aggregated cells = 144 cells emitted total).
b. Sharpe-differential (LW2008 CI) vs passive-long PER SYMBOL + basket vs equal-weighted passive basket reported as secondary KPI per ADR-0017 §1.2.

Family-wise correction over the 3-slip-grid (the H_1 family size remains 3 at the basket level per H068 v1 §1 convention; per-symbol cells emit as descriptive supplementary cells without independent family-wise correction at v2 — operator-discretionary per-symbol promotion per ADR-0013 §1 + ADR-0027 §D-4 single-axis discipline). [Romano-Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) stepwise FWER applied at the 3-slip-cell family level. Hansen 2005 SPA p reported as KPI annotation only per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md). DSR deflation per [Bailey-López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094) MANDATORY since realized cell count at the basket level (3 slip cells × 6 Kelly multipliers = 18 cells) ≥ project's `dsr_activation_size = 10` per [config/gate.yaml](../../../config/gate.yaml).

## 9. Sample-size + power

Per H062 v2 per-symbol n_trades observation on the same canonical substrate `317429e4...` (per H062 v2 sidecar `eb729b201595484594ce4c9ddde72d05` per [H062 v2 KPI v2 §"Per-symbol trade activity"](../H062/H062_kpi_report_v2.md)) at the same modal feature cell (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom"):

| Symbol | Expected n_trades (per H062 v2 reference) | Per-symbol n_min_trades guard threshold |
|---|---:|---|
| ES | 93-110 (≥ 93 per H062 v3 smoke; 110 per H065 v2 M_inf-ES reference; 108 per H068 v1) | n_min=50 per H068 v1 §9 statistical-power caveat |
| MGC | 3,928 (per H062 v3 smoke) — 4,686 (per C9 BOCD step-up sidecar) | n_min=50 (easily cleared) |
| SIL | 3,180 (per H062 v3 smoke) — 5,313 (per C9 BOCD step-up sidecar) | n_min=50 (easily cleared) |
| **Basket total** | **~7,200-10,000** | basket-level n_min=150 (3 × 50) |

**Inferential power-lift quantification**: per H068 v1 §9 the basket-aggregated MPPM(ρ=1) CI width scales by ~1/√n_trades. v1 ES standalone at n=108 yielded CI width 4.35 at A1 slip=0.5 (per H068 v1 KPI v1 Table 3 [-1.300, +3.052]); v2 basket at n=7,200 expected to yield CI width 4.35 × √(108/7200) ≈ **0.53** — an **8.2× narrower CI**. **If the v1 point estimate of +0.564 holds at the v2 basket aggregation, the H_1 criterion (b) CI excludes zero positively cleanly**. Conversely, if the basket-aggregated point estimate shrinks to near zero due to per-symbol divergence (per §1.5 caveat), the narrower CI provides a STRICTER test of statistical-distinguishability from zero.

**Statistical-power caveat for H068 v2** (per CLAUDE.md Phase O.18 strategic finding): the basket-aggregation inferential power-lift IS the v2 design.md value proposition; the H_1 verdict at v2 is therefore a structurally STRONGER inferential test than v1. v2 SHALL emit per-symbol MPPM(ρ=1) CIs alongside the basket-aggregated CI to surface per-symbol divergence per §1.5 caveat.

Power calibration `P1-H068-V2-POWER-SIMULATION-EXECUTE` deferred (non-blocking; sample size is empirically adequate at basket n_trades ≈ 7,200 with the 3-slip-cell family-wise correction).

## 10. Decision rule

Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) no-binding-gates discipline: the per-symbol AND basket-aggregated KPIs are reported in §13 alongside the H068 v1 parent reference + the H062 v2 per-symbol baseline; the operator chooses promotion timing on the Pareto-front per H_1. Stage transitions per ADR-0013 §1 (`kpi-report-emitted` → `ninjascript-implemented`) are operator-discretionary per the user 2026-05-04 standing decline-ninjascript directive.

## 11. Threats to validity + kill switches

Inherits H068 v1 + H062 + H065 design.md §11 + §11.1 (K-1..K-8) verbatim. Multi-instrument basket expansion DOES affect K-5:

- **K-1 (per-trade $-stop)**: 1.0R per Turtle 2N convention; per-symbol 1R varies per ATR + tick_value scaling.
- **K-2 (time stop)**: EOD-flatten serves as implicit time stop at intraday cadence; per-symbol per §2 session policy.
- **K-3 (no-add-to-loser)**: vacuous in H068 v2 (no pyramiding; 1-lot per symbol per cell at v2).
- **K-4 (capacity ceilings)**: ES ≤ 20 contracts per ADR-0001; MGC + SIL micro-class effectively unbounded at retail. v2 uses 1-lot per cell per symbol (cap is informational; not binding at v2).
- **K-5 (correlated-instrument inventory cap)**: per ADR-0017 §5 K-5 correlated-pair taxonomy + ADR-0025 §D-1 F-1-6 fix in [src/skie_ninja/backtest/kill_switch_runtime.py](../../../src/skie_ninja/backtest/kill_switch_runtime.py). **At H068 v2 universe {ES, MGC, SIL}, K-5 is N/A**: ES has no micro-pair in the basket (MES not in universe; ES not paired with MGC/SIL); MGC has no full-size pair (GC not in universe); SIL has no full-size pair (SI not in universe). The runtime's `validate_universe_for_k5(["ES", "MGC", "SIL"])` returns clean per the ADR-0025 §D-1 contract. **If MES or GC or SI is added in a future v3 successor, K-5 enforcement MUST be re-evaluated** per `P1-H068-V3-K5-CORRELATED-EXTEND`.
- **K-6 (daily circuit breaker)**: −2% of equity realized P/L → halt new entries through end of session per ADR-0017 §5 + ADR-0028 §D-1 default. <!-- justify: ADR-0028 §D-1 `k6_enforcement` defaults to "block" per Task #20 empirical finding (H062 v3 ablation A2 cost-only run produced same magnitude as cost-only A1; size-down does not recover cost-dominated catastrophes); block default preserved at v2 per parent-cell preservation -->
- **K-7 (weekly circuit breaker)**: −5% of equity realized P/L → halt new entries through end of week per ADR-0017 §5 + ADR-0028 §D-1 default.
- **K-8 (adverse-direction entry filter)**: same as H068 v1.

Per [ADR-0024](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) §D-2 opt-in framing, K-3 + K-4 + K-6 + K-7 are **opt-in** at v2 per design.md §11.1 declaration with `enable_k4=True + enable_k6=True + enable_k7=True` (preserves [src/skie_ninja/backtest/kill_switch_runtime.py](../../../src/skie_ninja/backtest/kill_switch_runtime.py) ADR-0025 §D-1 defaults).

### 11.1 Kill-switch + abandonment-trigger opt-in declaration

Per [ADR-0024 §D-2](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) + ADR-0025 §D-1 + ADR-0028 §D-1 opt-in declarations:

| Primitive | Status at v2 | Enforcement mode |
|---|---|---|
| Kill-switch runtime K-3 (no-add-to-loser) | DISABLED (vacuous at H068 v2 single-unit) | n/a |
| Kill-switch runtime K-4 (per-symbol cap) | ENABLED at ES ≤ 20 contracts; MGC + SIL micro-class effectively unbounded | block (ADR-0028 §D-1 default) |
| Kill-switch runtime K-5 (correlated-instrument inventory) | N/A at v2 universe {ES, MGC, SIL} (no correlated pairs in basket) | n/a |
| Kill-switch runtime K-6 (daily circuit breaker) | ENABLED at −2% × equity_at_session_start per-symbol | **block** at v2 (ADR-0028 §D-1 default; size-down opt-in deferred to v3 per `P1-H068-V3-WITH-K6-K7-SIZE-DOWN`) |
| Kill-switch runtime K-7 (weekly circuit breaker) | ENABLED at −5% × equity_at_week_start per-symbol | **block** at v2 (ADR-0028 §D-1 default) |
| Equity rebase | FIXED-equity per H068 v1 + H065 v2 M_inf_h062_v1_fixed-ES parent cell <!-- justify: parent-cell preservation per ADR-0027 §D-4; current-equity rebase is a separate v3 axis warranting independent evaluation per `P1-H068-V3-CURRENT-EQUITY-REBASE` --> | n/a |
| BOCD live-pause | DISABLED at v2 (no calibrated priors per `P1-BOCD-CALIBRATION-PRE-OOS-HOLDOUT`; deferred to v3 per `P1-H068-V3-BOCD-LIVE`) | n/a |

### 11.2 BLOCKING preconditions (pre-launch)

| ID | Status | Description |
|---|---|---|
| `P1-H068-V2-WALK-FORWARD-ORCHESTRATOR-IMPL` | OPEN; BLOCKING-BEFORE-LAUNCH | Fork H068 v1's [scripts/run_h068_sensitivity_sweep.py](../../../scripts/run_h068_sensitivity_sweep.py) → `scripts/run_h068_v2_basket_sweep.py` per H068 v2 design.md §15 + §17.1 preserved-infrastructure binding. The new orchestrator extends the existing slip-sensitivity parameter pass-through to iterate over 3 symbols per cell with per-symbol cost-arm × slip-arm sweep + basket-level aggregation. |
| `P1-H068-V2-PIT-CANARY-INTEGRATION-TEST` | OPEN; BLOCKING-BEFORE-LAUNCH | Integration test at `tests/integration/test_h068_v2_pit_canaries.py` per H068 v1 + H062 v1 canary set inheritance + new Canary E (basket-aggregation symbol-order invariant). |
| `P1-H068-V2-BASKET-INVARIANT-TEST` | OPEN; BLOCKING-BEFORE-LAUNCH | New unit test at `tests/unit/test_h068_v2_basket_invariant.py`: shuffle symbol order in basket-aggregation pipeline; basket-aggregated MPPM(ρ=1) must match within machine-precision tolerance per §7 Canary E. |
| `P1-H068-V2-SUBSTRATE-PER-PARTITION-SHA-EMIT` | OPEN; BLOCKING-BEFORE-V2-EMISSION | Walk-forward orchestrator emits per-symbol per-partition SHA list in v2 sidecar `dataset_checksums.per_partition` field per data_requirements.md §"Per-partition SHA enumeration". |
| `P1-H068-V2-REPROLOG-WIRE` | OPEN; BLOCKING-BEFORE-V2-EMISSION | Wrap orchestrator execution in `RunContext` per ADR-0017 §3 + ADR-0026 §D-2 mandatory-verbosity carveout. Avoid the H065 v1 + H067 v1 retrofit pattern documented in [research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md](../H065/H065_kpi_report_v1_corrigendum_2026-05-18.md). |
| `P1-H068-V2-N-MIN-TRADES-GUARD` | OPEN; BLOCKING-BEFORE-V2-EMISSION | Walk-forward orchestrator asserts post-cost-light-filtering per-cell per-symbol n_trades ≥ 50 per §9 statistical-power caveat. Per-symbol cell failing the guard emits `power-margin-low` annotation per ADR-0014 §3.2 Table 8. Basket-aggregated n_min=150 per §9. |
| `P1-H068-V2-PER-SYMBOL-MPPM-CI-EMIT` | OPEN; BLOCKING-BEFORE-V2-EMISSION | v2 KPI report card SHALL emit per-symbol MPPM(ρ=1) CI alongside basket-aggregated CI per §1.5 caveat (operator visibility on per-symbol divergence). |
| `P1-H068-V2-PROD-RUN` | OPEN | First production walk-forward + KPI report card v2. |

Closed inherited primitives: `P1-MPPM-RHO-1-FITNESS-PRIMITIVE`, `P1-BOCD-DECAY-DETECTOR-PRIMITIVE`, `P1-KELLY-CAP-GRID-SEARCH-PRIMITIVE`, `P1-L-SKEWNESS-PRIMITIVE-IMPL`, `P1-CALMAR-DIFFERENTIAL-CI-IMPL`, `P1-PROFIT-FACTOR-CI-IMPL`, `P1-R-MULTIPLE-CI-IMPL`, `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`, `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE`, `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`, `P1-H055-NEWS-CALENDAR-INGEST` (via H062 feature-factory reuse), `P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL`, `P1-SIDECAR-LEVEL-A0-ZERO-COST-REFERENCE-WIRE`, `P1-METALS-ENERGY-CME-FEE-VERIFY` (closed Phase O.16; substrate fee schedules verified per commit `9a3a512`).

## 12. Reproducibility

H068 v2 inherits the full SKIE-Universe reproducibility discipline: deterministic RNG seed `20260520` for all bootstrap + Monte Carlo invocations (v2 seed distinguished from v1's `20260519` per the pre-reg-date 2026-05-20); RunContext per [src/skie_ninja/utils/runcontext.py](../../../src/skie_ninja/utils/runcontext.py); ReproLog at `logs/reproducibility/<run_id>.json`; sidecar `scientific_payload_sha256` binding; substrate dataset_checksum binding to `317429e4...`. Pre-commit non-loss guard per [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

ReproLog 13-field schema MANDATORY at v2 KPI emission per `P1-H068-V2-REPROLOG-WIRE` (BLOCKING-BEFORE-V2-EMISSION); the H068 v2 walk-forward orchestrator MUST wrap execution in `RunContext` to emit canonical ReproLog (avoiding the H065 v1 + H067 v1 retrofit patterns documented in [research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md](../H065/H065_kpi_report_v1_corrigendum_2026-05-18.md)).

## 13. Sensitivity exhibits + scope deviations

**Required sensitivity exhibits**:
- **Per-symbol per-slip cell** at v2 KPI report card §"End-of-simulation results summary" 13-table format per ADR-0014 §3.2 + ADR-0019 §3 PER SYMBOL.
- **Basket-aggregated 13-table summary** for each slip × Kelly × cost-arm cell (3 × 6 × 2 = 36 basket-aggregated cells).
- **Per-symbol + per-Kelly-multiplier × per-cost-arm 108-cell heatmap** with cells classified per ADR-0028 §D-2 `cost-friction-dominated-edge-{present, absent, n/a}` annotation.
- **Cost-friction-breakeven ratio sensitivity table** under `sensitivity_mult ∈ {1.0, 0.5, 0.25}` × 3 symbols per §2 binding (operator-actionable diff between per-symbol conservative_prior and empirical-slip-reduction; surfaces the MGC vs ES + SIL asymmetry per §6).
- **slip=1.0-tick (parent baseline)** alongside in the KPI report card as the direct-comparability reference to H068 v1 anchor.
- **2026-04-01 → 2026-05-15 sub-window** (~6 weeks; mandatory per ADR-0026 §D-1 §0 3-component header component 2).

**Scope deviations from full-spec inner-CV grid** (recorded per Path A frozen-pre-reg amendment discipline):
- v2 inner-CV grid is the 108-cell representative grid (3 symbols × 3 slip × 6 Kelly × 2 cost-arm) at fixed H065 v2 modal feature cell (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0). Full-grid tracked under `P1-H068-V2-FULL-INNER-CV-GRID-V3`.
- 3-symbol basket {ES, MGC, SIL} at v2; NQ deliberately omitted per §1 NQ retail-floor constraint; MNQ substitution deferred per `P1-H068-V2-MNQ-EXTENSION-V3`; MCL deferred per `P1-H068-V2-WITH-CL-MCL-EXTEND`. 4-symbol basket {ES, MNQ, MGC, SIL} at v3 successor on the MNQ-extension cycle.
- Single-unit entry (1-lot per symbol); no pyramiding (preserved from H068 v1 + H065).
- v2 reports fixed-equity rebase per H062 v1 modal (preserved from H068 v1 + H065 v2 M_inf_h062_v1_fixed-ES anchor).
- M=∞ no-TP-overlay (fixed; not a grid axis) per H068 v1 + H065 v2 parent-cell preservation.
- Inner-CV walk-forward window = 252-session-train / 60-session-test per ADR-0027 §D-2 bounded set {63, 126, 252, 504}; preserved from H068 v1 parent.
- BOCD live-pause primitive NOT activated at v2 (deferred to v3 per `P1-H068-V3-BOCD-LIVE` + `P1-BOCD-CALIBRATION-PRE-OOS-HOLDOUT`).
- Per-symbol independent sizing at v2 (no inter-symbol correlation-aware allocation; deferred to MPV2 cycle per `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION`).

## 14. Cross-references

- **Parent hypothesis**: [H068 v1](../H068/design.md) (H068 v1 at `kpi-report-emitted` per CLAUDE.md Phase O.18 — first cost-light positive ROI in project history; sidecar `957643d6cb8441e29d888482447ead6e`; substrate `317429e4...`).
- **Sibling cost-light successor**: [H067](../H067/design.md) (H067 v1 SIL standalone N-lot grid; demoted to rank #2 per Phase O.16 + Phase O.18 strategic finding that N-lot is NOT a cost-reduction mechanism at conservative_prior).
- **Grandparent hypothesis**: [H065](../H065/design.md) (H065 v2 M_inf_h062_v1_fixed-ES cell at `kpi-report-emitted`; H068 v2 inherits H065 v2 modal feature configuration via H068 v1).
- **Great-grandparent hypothesis**: [H062](../H062/design.md) (H062 inherits feature factory + walk-forward orchestrator + PIT canaries verbatim per the H065 §3 inheritance chain).
- **Empirical anchor**: [H068 v1 KPI v1](../H068/H068_kpi_report_v1.md) (slip=0.5 A1 ratio 2.278; pre-empirical prediction verified within 3%; H_1 conjunctive NULL on n_trades=108 inferential-power floor — the load-bearing motivation for v2 multi-instrument expansion per `P1-H068-V2-EXPANDED-SUBSTRATE`).
- **Cross-hypothesis substrate reference**: [H062 v2 KPI v2](../H062/H062_kpi_report_v2.md) (per-symbol trade-frequency reference: MGC 3,928 + SIL 3,180 trades on 5-min cadence × 2020-2026 OOS modal cell on the same canonical substrate `317429e4...`).
- **Substrate-vintage memo**: [docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md).
- **Paradigm stack**: ADR-0001 + ADR-0008 + ADR-0013 + ADR-0014 + ADR-0017 + ADR-0018 + ADR-0019 + ADR-0020 + ADR-0022 + ADR-0023 + ADR-0024 + ADR-0025 + ADR-0026 + ADR-0027 + ADR-0028.
- **CLAUDE.md ledger** Phase O.18 closure synthesis (commit `8434c37` per CLAUDE.md "Phase O.18 closure synthesis — 6-parallel-agent campaign cross-task report 2026-05-19"): `P1-H068-V2-EXPANDED-SUBSTRATE` registered as the BLOCKING-BEFORE-V2-INFERENCE follow-up; this design.md is its closure deliverable.

## 15. NinjaScript implementation (per ADR-0013 §5; mandatory upon operator approval)

Mandatory C# implementation per [ADR-0013 §5](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md): `ninjascript/strategies/H068_v2_BasketDonchian.cs`.

C# class structure (skeleton; full implementation deferred to `P1-H068-V2-NINJASCRIPT-IMPL`):
- **Class name**: `H068_v2_BasketDonchian`
- **File path**: [ninjascript/strategies/H068_v2_BasketDonchian.cs](../../../ninjascript/strategies/H068_v2_BasketDonchian.cs)
- **Inheritance**: `NinjaTrader.NinjaScript.Strategies.Strategy`
- **Multi-symbol implementation**: per-symbol Strategy instance instantiated with NinjaTrader 8 MultiSeries API (`AddDataSeries("MGC 06-26")` + `AddDataSeries("SIL 06-26")` alongside primary ES series). Per-symbol Donchian + ATR + ID_1 computation runs independently per series; basket-level coordination via shared kill-switch state.
- **Hyperparameter mapping** (Python ↔ C#): same as H068 v1 §15 hyperparameter table verbatim per parent-cell preservation; the additional kwargs at v2 are universe-list (declared statically in C# constructor; not exposed as runtime hyperparameters).
- **Entry / exit logic 1:1 with Python**: per-symbol Donchian channel + ATR stop + first-fire dwell + ID_1 trend gate + EOD-flatten (per-symbol session policy from §2).
- **Kill-switch parameters per §11.1**: K-4 per-symbol via `Position.Quantity` cap; K-6 / K-7 via running per-symbol daily/weekly P/L accumulator with `EnterLong` / `EnterShort` rejection on breach (block-mode per ADR-0028 §D-1 default).
- **Fill-log schema matching plan §6.1**: CSV with `(timestamp_ct, symbol, side, n_contracts, entry_price, exit_price, exit_reason, realized_pl_usd)` columns; per-symbol rows; basket-level aggregation computed downstream.
- **Sim101 smoke-test record**: ScriptSubmission timestamps + per-symbol position fills + final per-symbol P/L per ADR-0013 §5.1 deferred to `P1-H068-V2-NINJASCRIPT-SIM101-SMOKE-RECORD`.

Python ↔ NinjaScript parity-check per ADR-0013 §5.2: byte-equality on per-symbol integer entry/exit signal vector + per-trade exit-reason classification. Tracked under `P1-H068-V2-NINJASCRIPT-IMPL` (mandatory per ADR-0013 §5; operator-discretionary decline allowed per 2026-05-04 standing directive).

## 16. Substrate provenance

Substrate: [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/); `output_frame_sha256 = 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) per CLAUDE.md Phase O.10 substrate re-derivation (run_id `38d63bdd2def4fa9804c78fbcb1a76ce`).

H068 v2 universe = {ES, MGC, SIL} 3-symbol subset of the 5-symbol canonical substrate. Per-symbol partition SHA enumeration at v2 freeze: see [data_requirements.md](data_requirements.md) §"Per-partition SHA enumeration".

## 17. Revision log

- **2026-05-20** (initial pre-registration): `status: designed` frozen. Multi-instrument basket expansion of H068 v1 cost-light Donchian channel-breakout; primary cross-axis = universe expansion from ES standalone → 3-symbol basket {ES, MGC, SIL}; preserves every other H068 v1 mechanical layer verbatim. NQ omitted per retail-equity-floor empirical constraint; MNQ substitution + MCL extension deferred to v3. Pre-reg authored under audit-remediate-loop discipline (per SKILL.md 3-round cap; R1 parallel literature-check + quant-auditor + format-auditor branches at draft time); full audit trail at [docs/audits/audit_trail_2026-05-20_h068_v2_design.md](../../../docs/audits/audit_trail_2026-05-20_h068_v2_design.md).

### 17.1 Genetic-successor cross-citation (per ADR-0027 §D-4 four-field mandatory disclosure)

| Field | Value |
|---|---|
| **Parent hypothesis ID + final stage** | H068 v1 at `kpi-report-emitted` per CLAUDE.md Phase O.18 closure synthesis (commit `4d14bfb` per Phase O.18 §Task #24); KPI v1 published with substrate `317429e4...` + sidecar `957643d6cb8441e29d888482447ead6e` + scientific_payload_sha256 `a5bce59880e0dd5d824a5b4fd6d7ef7db1df80f05599dc34744f0d26b59ca714` + 36-cell representative grid (3 slip × 6 Kelly × 2 cost-arm) × ES standalone × 2020-2026 OOS × 108 trades. |
| **Motivating KPI / annotation** | **H068 v1 KPI v1 §"H_1 conjunctive verdict"**: **NULL on all 3 slip cells**, despite the pre-empirical structural prediction at sensitivity_mult=0.5 (ratio ≈ 2.22 just crosses ADR-0028 §D-2 threshold) being **EMPIRICALLY VERIFIED** at realized ratio 2.278 (within 0.058 of prediction = 2.6% deviation). The conjunctive H_1 failed on criterion (b) MPPM CI excludes zero positively — n_trades=108 yields CI width 4.35 too wide for the +0.564 point estimate to clear zero positively. Per H068 v1 §1.4 statistical-power caveat: H068 v1 CI is 7.1× wider than H067 SIL's n=5,600 equivalent. **Motivating annotation**: `promising-realized-roi-cost-conservative-prior-317429e49ad63674` per Phase O.18 promising-annotation registration (CLAUDE.md Phase O.18 §"`promising-*` annotations registered per ADR-0026 §D-3"). The genetic-cross hypothesis: multi-instrument basket expansion to 3 symbols lifts inferential POWER (basket n_trades ≈ 7,200 = 67× v1) WITHOUT changing per-trade mean-edge; the H_1 conjunctive evaluation under the basket-aggregated MPPM CI should clear at the same v1 +0.564 point estimate magnitude if it holds at v2. |
| **Genetic-cross** | **SINGLE AXIS** per ADR-0027 §D-4 single-axis-genetic-cross discipline. Cross-axis: **universe expansion from ES standalone → 3-symbol basket {ES, MGC, SIL}**. NO change to: signal-generation mechanic (channel_n=120 + k_atr=2.0 + atr_n=14 + h_dwell=5 + trend_id="a_ts_mom" + L=60 + τ=1.0 all fixed at H065 v2 modal values inherited via H068 v1); slip-sensitivity grid (`sensitivity_mult ∈ {1.0, 0.5, 0.25}` preserved verbatim); Kelly-multiplier grid (`{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` preserved verbatim); cost-arm grid (A0 zero-cost + A1 conservative_prior preserved verbatim); fixed-equity rebase (H065 v2 M_inf_h062_v1_fixed parent cell mechanic preserved); per-symbol session policy (ES RTH-only; MGC + SIL 24/5 per Phase O.0 metals/energy session extension); cell-budget cap = 108 cells per ADR-0027 §D-2 declaration (108 < 1000 v1 cap). Inner-CV fitness = MPPM(ρ=1) per ADR-0018 D-1. RNG seed = `20260520` (v2 distinguished from v1's `20260519` per ADR-0017 §3 fresh-seed convention). The N-lot scaling (mechanism per H067 R1 audit + Phase O.18 strategic finding that N-lot is NOT a cost-reduction mechanism at conservative_prior) + bar-cadence-reduction (mechanism 2; daily/4-hour) + longer-hold-variant (mechanism 3) + finer-grained slip sub-sweep (mechanism 4) + current-equity rebase (mechanism 5) + BOCD live-pause (mechanism 6) cost-reduction + abandonment-trigger axes are deferred to v3 successors per ADR-0027 §D-4 single-axis discipline. MNQ extension (universe-axis sub-variant) deferred per `P1-H068-V2-MNQ-EXTENSION-V3` requiring new Databento extraction. MCL extension deferred per `P1-H068-V2-WITH-CL-MCL-EXTEND` (existing follow-up). |
| **Preserved infrastructure** | Substrate `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.10 main-HEAD); H062 feature factory at [src/skie_ninja/features/h062/](../../../src/skie_ninja/features/h062/); H068 v1 walk-forward orchestrator at [scripts/run_h068_sensitivity_sweep.py](../../../scripts/run_h068_sensitivity_sweep.py) (to be forked to [scripts/run_h068_v2_basket_sweep.py](../../../scripts/run_h068_v2_basket_sweep.py) per `P1-H068-V2-WALK-FORWARD-ORCHESTRATOR-IMPL`); H062 v1 PIT canaries verbatim ([tests/integration/test_h062_pit_canaries.py](../../../tests/integration/test_h062_pit_canaries.py)) + new Canary E basket-aggregation symbol-order invariant per §7; ADR-0017 + ADR-0018 + ADR-0019 + ADR-0022 inner-CV machinery + KPI annotation grammar; ADR-0014 §3.2 13-table format + ADR-0026 §D-1 §0 3-component summary header + ADR-0028 §D-4 `kill-switch-mode-{block,size-down}` + `cost-friction-dominated-edge-{present,absent,n/a}` annotations; ADR-0025 abandonment-trigger primitives (kill-switch runtime ENABLED at v2 with block-mode default per Task #20 finding + parent-cell preservation; equity-rebase FIXED per parent cell; BOCD live-pause + size-down enforcement DEFERRED to v3). Cell-budget cap = 108 cells per ADR-0027 §D-2 declaration. Inner-CV fitness = MPPM(ρ=1) per ADR-0018 D-1. RNG seed = `20260520`. Per-symbol fee schedules per [config/instruments.yaml](../../../config/instruments.yaml) (ES CME-verified eff. 2024-02 + MGC + SIL CME-verified per Phase O.16 commit `9a3a512`). |
