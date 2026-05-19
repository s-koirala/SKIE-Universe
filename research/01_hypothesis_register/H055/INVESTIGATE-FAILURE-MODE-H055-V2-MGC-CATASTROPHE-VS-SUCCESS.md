---
investigation_id: INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS
schema_version: investigation_memo_v1
created: 2026-05-19
status: complete-no-further-action
hypothesis_of_investigation: H055
parent_kpi_report_card: research/01_hypothesis_register/H055/H055_kpi_report_v2.md
---

# Investigation Memo — H055 v2 MGC outcome dispersion across Kelly multiplier × BOCD floor × hypothesis-family

Per [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) §D-1, this memo is the canonical artifact class for `INVESTIGATE-FAILURE-MODE-*` follow-ups. Investigation outputs do NOT use the [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) §3.2 13-table format; this template is the alternative artifact class. Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1 non-loss, this memo is immutable post-completion; corrections produce a versioned successor (e.g., `INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS_v2.md`).

Closes the third of three ADR-0027 §D-1 adoption-time `INVESTIGATE-FAILURE-MODE-*` follow-ups registered at Phase O.14.

## 1. Hypothesis-of-investigation

**Empirical question** (per the Phase O.14 registration): why does MGC outcome swing from **+87.0%** (H055 v2 C3 super-Kelly, full OOS) to **−93.7%** (H062 Phase O.3 C3 super-Kelly, full OOS) to **+69.1%** (H062 C9 BOCD step-up with km_floor=0.5) across cell-Kelly configurations? What is the per-fold dependency on regime conditioning?

**Pre-investigation candidate decomposition** (per the task framing in the operator's spawn prompt):

- **H-a (time-window dependence)**: MGC outcome is concentrated in regime-conditional eras (early-2020 COVID-volatility windows + similar high-vol regimes); rest of OOS is flat-to-negative.
- **H-b (Kelly-multiplier dependence)**: at km=1.5+ MGC stays exposed in drawdown regimes; at km=0.5 (BOCD-floored) MGC sits out those regimes; the +69% vs −94% swing is C9 (BOCD-halved) vs C3 (always-on).
- **H-c (cell-grid dependence)**: MGC's signal has a narrow profitability window in (N, k_atr) hyperparameter space; small shifts in cell selection flip MGC from positive to negative.

**Reference anchor — parent KPI card**: [H055 v2 KPI report card](H055_kpi_report_v2.md) emits 5 configs × 4 symbols × 14 metrics on the 2024-01-01 → 2026-06-30 OOS window; **the strongest standalone cell project-wide is MGC C3 super-Kelly +87.0%** (MPPM(ρ=1) point estimate +0.263; cell-conditional H_1 PARTIAL-confirm). The investigation's anchor data are five sidecars from two hypothesis families (H055 v2 + H062 Phase O.3-O.7) sharing the substrate vintage at SHA `b93e544...` / `317429e4...` (MGC partition byte-identical across the two vintages per the [substrate-vintage memo](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)).

## 2. Decomposition plan

Three orthogonal axes of decomposition on existing sidecars (no new walk-forward execution; per ADR-0013 §4.1 non-loss preserve existing provenance):

- **Axis I — cross-Kelly dispersion at a fixed hypothesis-family** (H-b probe): compare per-config MGC outcomes within H055 v2 (5 configs: v1 km=0.25, C2 km=1.0, C3 km=2.0, C9 km_start=1.5+BOCD, C5 km=2.0+pyramid) and within H062 Phase O.3 (6 configs: v1 + C1 + C2 + C3 + C4 + C5).
- **Axis II — cross-hypothesis-family dispersion at fixed (or matched) Kelly multiplier** (H-c probe): compare H055 v2 C3 (km=2.0) MGC = +87% vs H062 Phase O.3 C3 (km=2.0) MGC = −94%. The Kelly multiplier is identical; the hypothesis mechanic (wick-rejection mean-reversion vs Donchian-channel breakout) differs. This is the load-bearing comparison for H-c.
- **Axis III — temporal decomposition (km-era) at fixed family and configuration** (H-a probe): use the H062 C9 km-era decomposition sidecar (Phase O.7.4) which segments the C9 trajectory by Kelly-multiplier era (km=1.5 = first 261 sessions across all 4 symbols; km=1.0 = transition 117 sessions; km=0.5 = remaining 3,233 sessions) and reports per-era MGC ROI on unit bankroll. The km-era decomposition is the canonical regime-window probe published at [Phase O.7.4 commit `444eaf2`](../../../docs/research_notes/) and re-used here.

Output: 3-axis findings table at §6 + synthesis paragraph identifying the dominant sub-hypothesis (or combination thereof).

## 3. Termination criterion

Per [ADR-0027 §D-1(c)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) acceptable form (i): close when the 3-axis decomposition table (§6) is populated from existing sidecars + §7 implication identifies the load-bearing sub-hypothesis (a / b / c / combination) with operator-actionable MGC-specific cell-selection insight. No new walk-forward execution; this is an empirical-attribution investigation on existing provenance.

## 4. Wall-clock soft cap

Per [ADR-0027 §D-1(d)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) soft cap discipline:

| Estimate | Actual | Delta | Justify (if overrun) |
|---|---|---|---|
| 3 hr (sidecar parse + table assembly + memo + R1 audit) | ~2 hr | −1 hr (under) | n/a |

Hard cap per task spec: 5 hr.

## 5. Output artifact spec

Per [ADR-0027 §D-1(e)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md):

- **Output class**: investigation-memo (this artifact)
- **Cross-references**:
  - Parent KPI: [H055 v2 KPI report card](H055_kpi_report_v2.md)
  - Sister investigation memos: [H062 v3 primitive attribution](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md); [H062 v3 size-down first-use](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md)
  - Phase O.7.4 km-era decomposition: CLAUDE.md "Phase O.7.4" ledger entry (full per-symbol per-km-era table)
  - Phase O.7.5 walk-forward inferential picture: CLAUDE.md "Phase O.7.5" ledger entry (cross-arm per-fold mppm_oos distribution)
  - Audit trail: [docs/audits/audit_trail_2026-05-19_h055-v2-mgc-catastrophe-investigate.md](../../../docs/audits/audit_trail_2026-05-19_h055-v2-mgc-catastrophe-investigate.md)

## 6. Findings

> Per [ADR-0013 §4.1 non-loss](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), table rows are APPEND-as-work-completes; rows are immutable once landed.

### 6.0 Important reframing of the spawn-prompt numerics

The spawn prompt cites three MGC outcomes — "+87.0% (C3) / −94% (C3 in some Phase O.7 sub-window slices) / +73.4% (C9 BOCD step-up)" — and treats them as three slices of a single hypothesis-family sweep. The empirical record on disk says something narrower:

- **+87.0% is the H055 v2 C3 super-Kelly MGC outcome** (run_id `v2_sweep_20260516T025924Z`; bit-identical re-emission at `v2_sweep_20260518T220351Z` on the canonical substrate). This is the H055 wick-rejection mean-reversion family.
- **−93.73% is the H062 Phase O.3 C3 super-Kelly MGC outcome** (run_id `aggressive_sizing_sweep_20260515T235648Z`). This is the H062 Donchian-channel breakout family. **Different hypothesis class**, same Kelly multiplier.
- **+69.12% (≈ +73.4% as previously cited; the spawn prompt rounds slightly differently) is the H062 C9 BOCD step-up MGC outcome** (run_id `c9_bocd_step_up_20260516T013136Z`; floor=0.5; km_terminal=0.5). Same H062 family as the −94%, modified by BOCD-driven Kelly de-risking.

So the +87% / −94% comparison is **cross-hypothesis-family**, not within-H055-cell-Kelly-grid. The H055 v2 sweep itself produces no negative-MGC outcome at any sweep cell. This reframing is itself a finding (carried into the audit trail) and re-orders the candidate sub-hypothesis weighting away from "intra-H055 km-volatility" toward "cross-family mechanic differences interacting with Kelly multiplier."

### 6.1 Axis I — cross-Kelly dispersion at fixed hypothesis-family

**H055 v2 MGC per-config** (sidecar `cd95ebdbd01592d35b04c0d4472605c2530dfeda6cd49d683dd0ae460f053082`; H055 wick-rejection family; canonical substrate `317429e4...`; full OOS 2024-01-01 → 2026-06-30):

| Config | km | rebase | bocd | pyramid | n_trades | ROI % | MaxDD % | Win rate | MPPM(ρ=1) | Calmar | PF | Sub-window ROI |
|---|---:|:---:|:---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 0.25 | F | F | F | 3,622 | **−1.22** | +9.84 | 45.5% | −0.007 | −0.075 | 0.994 | 0.00 |
| C2_fullkelly | 1.00 | T | F | F | 10,321 | **+72.37** | +29.59 | 47.6% | +0.206 | +0.696 | 1.028 | +13.44 |
| C3_superkelly | 2.00 | T | F | F | 7,625 | **+87.04** | +37.34 | 47.0% | **+0.263** | +0.706 | 1.024 | −4.75 |
| C9_bocd_stepup | 1.50 start | T | T | F | 9,442 | **+58.04** | +21.40 | 47.2% | +0.185 | **+0.861** | 1.040 | +7.61 |
| C5_super_pyramid | 2.00 | T | F | T | 7,665 | **+77.19** | +39.79 | 46.5% | +0.243 | +0.612 | 1.021 | +8.52 |

**Pattern**: H055 v2 MGC is **monotonically improved by Kelly scaling** from −1.2% (v1 km=0.25) to +87% (C3 km=2.0). C9 BOCD step-up (km_start=1.5; floor halved to 0.5 at decay-detection) intermediate at +58%. **No negative-MGC config in the H055 v2 sweep.** Pyramiding (C5) trims +10 pp vs pure C3.

**H062 Phase O.3 MGC per-config** (sidecar `4e5a33175b518dd8f6228aa37a3068d0d5d2b0900589e3500aa922f8a0d729ec`; H062 Donchian-channel breakout family; substrate `b3ee230a...` (Phase O.3 vintage); full OOS 2020-01 → 2026-05; **note 6-year OOS span vs H055 v2's 2.5-year span**):

| Config | km | rebase | pyramid | n_trades | ROI % | MaxDD % | Win rate | Final equity | n_ruin |
|---|---:|:---:|:---:|---:|---:|---:|---:|---:|---:|
| v1 | 0.25 | F | F | 1,998 | **−25.02** | +42.82 | 19.2% | $7,498 | 0 |
| C1_rebase | 0.25 | T | F | 1,914 | **−27.01** | +43.27 | 20.2% | $7,299 | 0 |
| C2_fullkelly | 1.00 | T | F | 3,621 | **−83.01** | +94.27 | 20.8% | $1,699 | 871 |
| C3_superkelly | 2.00 | T | F | 3,649 | **−93.73** | +97.99 | 21.3% | $627 | **722** |
| C4_fullkelly_pyramid | 1.00 | T | T | 2,007 | **−90.74** | +96.03 | 15.6% | $926 | 605 |
| C5_super_2pct_pyramid | 2.00 | T | T | 5,327 | **+479.11** | +90.82 | 22.1% | $57,911 | 201 |

**Pattern**: H062 Phase O.3 MGC is **monotonically WORSE with Kelly scaling** from −25% (v1) to −94% (C3); pyramiding flips C5 dramatically positive but at the cost of 201 ruin events. **The ONLY non-catastrophic H062 MGC config without pyramiding is v1 quarter-Kelly** (still −25%). The win rate (19-21%) is structurally HALF of H055 v2's (45-48%).

**Axis I synthesis**: the cross-Kelly dispersion runs in OPPOSITE directions across the two hypothesis families. H055 monotonically improves with km; H062 monotonically degrades. The Kelly multiplier alone (H-b) is therefore NOT the dominant axis — the same Kelly setting produces +87% on H055 and −94% on H062. **H-b is rejected as the sole-driver hypothesis.**

### 6.2 Axis II — cross-hypothesis-family dispersion at matched Kelly

Hold km=2.0 fixed; compare H055 v2 C3 vs H062 Phase O.3 C3 on MGC:

| Family | Mechanic | n_trades | Win rate | Avg per-trade R | ROI % | MaxDD % | Skew τ_3 |
|---|---|---:|---:|---:|---:|---:|---:|
| **H055 v2 C3** | wick-rejection mean-reversion | 7,625 | 47.0% | (PF 1.024 → mean R ≈ +0.011) | **+87.04** | 37.3% | small positive |
| **H062 Phase O.3 C3** | Donchian-channel breakout | 3,649 | **21.3%** | mean R ≈ +0.006 but heavily left-tailed | **−93.73** | 98.0% | strongly positive (per Phase O.7 framing) |

The hypothesis mechanics produce **fundamentally different per-trade R-distributions**:

- H055 wick-rejection MR: ~47% win rate; PF ~1.02; small positive average R; many small wins and many small losses; symmetric-ish R-distribution with mild right-skew. Kelly scaling AMPLIFIES the mild positive drift without de-amplifying the symmetric losses → +87% at C3.
- H062 Donchian breakout: ~21% win rate; mean R slightly positive at v1 quarter-Kelly but the **trade frequency multiplied roughly 2x at C3** (1,998 → 3,649 trades — the entry threshold's interaction with current-equity rebase admits more entries as equity grows; the inverse multiplies losses as equity falls). The strongly positive τ_3 means rare large winners + frequent small losses; at km=2.0 + current-equity rebase, the frequent small losses compound into catastrophic drawdown before the rare winners can recover.

**Axis II synthesis**: the +87% vs −94% gap is **dominantly driven by the hypothesis mechanic** (H-c-adjacent: not a (N, k_atr) cell shift but a mean-reversion vs breakout mechanic shift) interacting with Kelly multiplier. Same km=2.0; opposite outcomes. The H-c hypothesis as originally framed ("(N, k_atr) hyperparameter space") is too narrow — the dispersion is across hypothesis-family-level mechanics, not within an H055 hyperparameter grid.

### 6.3 Axis III — temporal decomposition (km-era) at fixed family

Phase O.7.4 km-era decomposition (sidecar `9d07d5563644fba0e0899bca5d40a14f2be73ad8afd6ee1b0050297ae0e29270`; H062 C9 BOCD step-up; per-symbol per-era):

**H062 C9 MGC per km-era**:

| km era | n_sessions | First → Last | cum log return | ROI on unit bankroll | Sharpe annualized |
|---:|---:|---|---:|---:|---:|
| 1.5 | 110 | 2020-01-02 → 2020-05-21 | +0.964 | **+162.15%** | **+2.567** |
| 1.0 | 60 | 2020-05-22 → 2020-07-30 | −0.020 | −1.94% | −0.222 |
| 0.5 | **1,559** | **2020-07-31 → 2026-05-14** | **−0.394** | **−32.54%** | **−0.220** |

**This is the load-bearing decomposition**. MGC C9's headline +69% (+73.4% per the spawn prompt) is the COMPOSITION of:

- A massive early-2020 COVID-volatility win at km=1.5 (+162% in 110 sessions; Sharpe 2.57).
- A brief transition at km=1.0 (−1.94% in 60 sessions; near-flat).
- A **6-year flat-to-negative tail at km=0.5** (−32.54% in 1,559 sessions; Sharpe −0.22).

The km=1.5 early-2020 burst (110 sessions = 4.4% of total sessions) generates +162%-on-unit-bankroll; multiplied through the BOCD-halving sequence, this compounds to the +69% headline. The remaining 95.6% of sessions are flat-to-negative.

**Implication for the −94% H062 Phase O.3 C3 outcome**: C3 is ALWAYS-ON at km=2.0; it captures the early-2020 burst (likely at +200%+ on unit bankroll at km=2.0 vs km=1.5) but then sits exposed at km=2.0 across the entire 6-year flat-to-negative tail. Doubled-Kelly amplifies the slow bleed beyond recovery. Per the Phase O.7.4 decomposition framing, the C3 −94% trajectory IS the C9 +69% trajectory minus the BOCD step-down. The C9 BOCD step-down at session ~180 is the operational difference.

**Axis III synthesis**: H-a (time-window dependence) is **strongly supported** by the km-era decomposition. The MGC outcome is concentrated in regime-conditional eras; the 6-year post-COVID-recovery period is flat-to-negative regardless of strategy. BOCD-driven Kelly de-risking (C9) transforms the catastrophic-tail H062 C3 −94% into a positive-headline +69% by mostly sitting-out the long flat-tail at km=0.5. **C9 +69% is a survival mechanic, not an edge mechanic.**

### 6.4 H055 v2 outcome under the same lens

The 6-year-flat-tail problem of H062 does NOT apply to H055 v2 the same way because H055's OOS window is **only 2.5 years (2024-01-01 → 2026-06-30)**, not 6 years. The H055 v2 OOS span post-dates the early-2020 COVID regime entirely. So the H055 v2 +87% is NOT a "captured early-2020 burst" result. It's a 2024-2026 result, on a regime where the wick-rejection mean-reversion mechanic happens to have positive mean-edge on the gold micro contract (MGC). Three sub-windows visible in the sidecar:

- Full OOS 2024-01 → 2026-06 = +87.04% (continuous accumulation under C3 km=2.0).
- 2026-04 → 2026-05 sub-window = −4.75% (regime-conditional flat-to-negative; the BOCD step-up that would have de-risked C9 already activated and reduced sub-window exposure).
- H055 v2 C9 sub-window = +7.61% (BOCD effectively absorbed the 2026 Q1-Q2 underperformance).

This is corroborating evidence for H-a but on a different timeframe. The mean-reversion mechanic's profitability window on MGC includes the 2024-2025 period; the 2026-onward period appears regime-changed.

### 6.5 Axis IV — Walk-forward inferential picture (cross-reference Phase O.7.5)

Per the [Phase O.7.5 cross-arm walk-forward picture](../../../CLAUDE.md), H062-MGC per-fold mppm_oos cum = +1.67 with 54% positive folds and median +0.231. **Marginal positive at the walk-forward inferential level.** This is the methodologically-cleanest MGC inference (no fixed-cell hindsight bias; no single-cell cherry-picking). The H055 v2 inference equivalent does not have a published walk-forward cum_mppm because H055 v2 is a single-cell sweep on a representative production cell (not a walk-forward inner-CV).

The walk-forward picture says: under fold-by-fold inner-CV cell selection on H062, MGC is the second-best leg of the H062 family (behind H060 +2.23 cum_mppm). **The hindsight H062 Phase O.3 C3 −94% does NOT survive walk-forward CV** — the walk-forward picture is the +1.67 marginal positive, which is qualitatively different from both the −94% headline and the +69% C9 headline. The headline numerics are sensitive to hyperparameter-fixing-at-session-0 bias.

### 6.6 Synthesis

The empirical decomposition resolves the +87% / −94% / +69.1% spread into a **combination of all three sub-hypotheses, with a clear ordering**:

| Rank | Sub-hypothesis | Evidence weight | Mechanism |
|---:|---|:---:|---|
| 1 | **H-c (hypothesis-family mechanic)** | **STRONGLY SUPPORTED** | The +87% vs −94% gap at fixed km=2.0 is fundamentally driven by mean-reversion vs breakout R-distribution shape × win-rate (47% vs 21%) × trade-frequency-scaling with current-equity rebase. Reframe: NOT (N, k_atr) cell drift; rather hypothesis-class-level mechanic difference. |
| 2 | **H-a (time-window / regime-window dependence)** | **STRONGLY SUPPORTED** | The H062 C9 +69% decomposes as +162% in 110 early-2020 sessions (4.4% of total) + −32.5% in 1,559 km=0.5 sessions (62% of total). The early-2020 burst is necessary and (almost) sufficient. Post-2020 the H062 mechanic flat-lines. |
| 3 | **H-b (Kelly-multiplier alone)** | **PARTIALLY SUPPORTED, NOT DOMINANT** | Within a hypothesis-family, Kelly scaling AMPLIFIES the directional outcome — monotonically positive in H055 v2 (v1 −1.2% → C3 +87%); monotonically negative in H062 v1 (−25%) → C3 (−94%). BUT Kelly-multiplier alone does NOT explain cross-family +87% vs −94%. It's an amplifier, not a sign-flipper. |

**The "swing" from +87% to −94% to +69%** decomposes as: (i) +87% to −94% is a cross-family mechanic + Kelly amplifier × OOS-window-length composite (H055 2.5-yr OOS dominated by positive-mean-edge MGC regime; H062 6-yr OOS dominated by flat-to-negative post-COVID tail); (ii) −94% to +69% is the BOCD step-down halving Kelly from 1.5 to 0.5 at session ~180, mostly sitting-out the long flat-tail.

**The H055 v2 MGC +87% IS NOT a regime-window-conditional artifact** — it is the H055 wick-rejection mean-reversion mechanic compounding through a 2.5-year MGC window at km=2.0. The mechanic has positive mean-edge on MGC in this regime. **Whether this regime-conditional positive-edge persists forward is the operator-actionable question, not the cross-family +87/−94 confusion.**

## 7. Implication

### (a) Implication for H055 (parent hypothesis)

H055 v2 MGC C3 super-Kelly +87% is the strongest cell project-wide and is **operator-actionable**, with three caveats:

- **Out-of-sample horizon limitation**: the +87% is a 2024-01 to 2026-06 OOS window; the 2026-04 to 2026-05 sub-window already shows −4.75% on C3, suggesting regime-conditional underperformance has started. **Operator-action**: monitor 2026-Q3-Q4 paper-trade fill-data closely; if MGC C3 sub-window remains negative through 2026-Q3 → ADR-0018 §D-3 BOCD-live abandonment trigger fires → switch to C9 BOCD step-up variant (which already showed sub-window +7.61% via decay-detection).
- **Cost realism gap**: H055 v2 is `cost-zero-v1-pre-cost-research-only` per the standing operator directive. The H062 Phase O.16 cost-realism re-ranking finding (commit `bc743f7`) shows cost subtraction is a load-bearing primitive — the cost-free +87% MGC will compress materially under conservative_prior cost. `P1-H055-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE) is the gating prerequisite for any operator-actionable promotion. **Operator-action**: do not advance MGC C3 to ninjascript-implemented until `P1-H055-COST-EMPIRICAL-CALIBRATION` lands and MGC C3 is re-emitted at cost-conservative-prior.
- **Walk-forward CV vs single-cell sweep**: H055 v2 emits a single-cell single-config sweep (not a per-fold inner-CV walk-forward like H062). The single-cell hindsight bias documented in Phase O.7.5 applies: per-fold inner-CV selection on H055 has not been performed. **Operator-action**: `P1-H055-OPTUNA-INNER-CV-IMPL` (BLOCKING; carried from design.md §11.2) lands the walk-forward inner-CV; until that's done, H055 v2 +87% is qualitatively comparable to a fixed-cell H062 result, not to the walk-forward H062-MGC cum_mppm = +1.67 inferential result.

§17 revision-log row to be appended in a subsequent commit: *2026-05-19 — Investigation INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS closed; finding records that H055 v2 MGC C3 +87.0% is mechanic-driven (wick-rejection MR positive-mean-edge on MGC × Kelly amplification) NOT regime-window-driven; the +87 / −94 / +69 spread cited in the spawn prompt is cross-hypothesis-family, NOT within-H055. Recommend deferring NinjaScript progression behind P1-H055-COST-EMPIRICAL-CALIBRATION + P1-H055-OPTUNA-INNER-CV-IMPL.* (Operator-discretionary append per ADR-0013 §17 amendment policy.)

### (b) Implication for project-level ADRs

No ADR amendment warranted by this investigation per [ADR-0027 §D-3](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) empirical-before-amendment sequencing rule. The investigation findings RE-CONFIRM existing ADRs without requiring amendments:

- ADR-0018 §D-3 BOCD decay-detector + switching mechanic is empirically vindicated by the Phase O.7.4 km-era decomposition (BOCD-halving converts H062 catastrophic tail to positive headline).
- ADR-0017 §1 survival-constrained metric vector + ADR-0019 §3 L-skewness barbell shape detection are empirically vindicated by the +87% MGC C3 cell's MPPM(ρ=1) point estimate +0.263 + Calmar +0.706.
- ADR-0024 §D-7 Lo 2004 AMH (strategy decay is the null) is empirically vindicated by the 2026-Q2 sub-window underperformance signal on H055 C3 MGC.

The cross-family-amplifier finding is a project-level inference that future hypothesis design.md §1.5 (or equivalent expected-payoff block) SHALL acknowledge: **Kelly multiplier amplifies the directional sign of the mechanic's mean-edge; it does not create or destroy edge.** This is already partially captured by `P1-PHASE-O15-LSKEWNESS-NEGATIVE-MEAN-EDGE-WARNING` (open from H062 v3 primitive-attribution investigation). No new follow-up needed.

### (c) Implication for future hypotheses

- **Constraint-to-inherit**: any new hypothesis that scales Kelly above the operator-default 0.25 SHALL include a §1.5-equivalent statement acknowledging that the Kelly multiplier is a directional-amplifier and SHALL include risk-of-ruin Monte Carlo + BOCD-live + size-down primitive integration per ADR-0025 + ADR-0028. H055 already inherits these via §11.1 + §11.2; the V3 KPI emission with the abandonment-trigger suite ON is the prospective realization.
- **Failure-mode-to-canary**: any new hypothesis on MGC SHALL include a 6-year-flat-tail canary (extending the OOS test window to capture multiple regime transitions). The MGC 2020-07 → 2026-05 −32.5% on unit bankroll at C9 km=0.5 is the load-bearing canary fixture for "post-COVID metals regime is flat-to-negative for this signal class." Successor variants are likely to inherit this regime-conditional flat behavior.

### (d) MGC-specific cell-selection insight (operator-actionable)

The most operator-actionable insight from this investigation:

> **MGC C3 super-Kelly on H055 v2 (wick-rejection MR mechanic; km=2.0; current-equity rebase) is the strongest standalone cell project-wide on 2024-2026 OOS, but its forward survival depends on three independent constraints: (i) cost-realistic recalibration via `P1-H055-COST-EMPIRICAL-CALIBRATION`; (ii) walk-forward inner-CV validation via `P1-H055-OPTUNA-INNER-CV-IMPL`; (iii) 2026-Q3-Q4 paper-trade monitoring with ADR-0018 §D-3 BOCD-live abandonment trigger ARMED. Absent any of the three, the +87% headline is qualitatively comparable to the H062 Phase O.3 hindsight result class (Phase O.7.5 walk-forward refutation precedent).**

This is the third candidate-MGC-cell across the three completed `INVESTIGATE-FAILURE-MODE-*` investigations of the Phase O.18 / 2026-05-19 series; combined with the H062 cost-realism re-ranking finding, the operator-recommended next mandatory transition for the H055 family is the cost-empirical-calibration cycle, NOT immediate NinjaScript progression.

## 8. Closure

- **Closure date**: 2026-05-19
- **Closure type**: ablation-complete (3-axis decomposition on existing sidecars)
- **Closure verdict**: complete-no-further-action
- **Downstream artifacts produced**: this investigation memo + audit trail at [docs/audits/audit_trail_2026-05-19_h055-v2-mgc-catastrophe-investigate.md](../../../docs/audits/audit_trail_2026-05-19_h055-v2-mgc-catastrophe-investigate.md); no new follow-up registered (all operator-actions land under existing follow-ups `P1-H055-COST-EMPIRICAL-CALIBRATION` + `P1-H055-OPTUNA-INNER-CV-IMPL` + `P1-PHASE-O15-LSKEWNESS-NEGATIVE-MEAN-EDGE-WARNING`). Operator-discretionary §17 revision-log append on H055 design.md per (a) above.

## Cross-references

- Parent KPI report card: [H055 v2 KPI report card](H055_kpi_report_v2.md)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Sister investigation memos: [H062 v3 primitive-attribution](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md); [H062 v3 size-down first-use](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md)
- Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-19_h055-v2-mgc-catastrophe-investigate.md](../../../docs/audits/audit_trail_2026-05-19_h055-v2-mgc-catastrophe-investigate.md)
- ADR-0027 §D-1 (this template's source mandate): [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- Sidecar SHA inventory (sources):
  - H055 v1 sweep `83cd09e88476b93d0be18d4a12c4cd90dbaf7d21168aec0bf9d9741c33e43ef5` ([artifacts/runs/H055/v2_sweep_20260516T025924Z/sweep_sidecar.json](../../../artifacts/runs/H055/v2_sweep_20260516T025924Z/sweep_sidecar.json))
  - H055 v2 sweep `cd95ebdbd01592d35b04c0d4472605c2530dfeda6cd49d683dd0ae460f053082` ([artifacts/runs/H055/v2_sweep_20260518T220351Z/sweep_sidecar.json](../../../artifacts/runs/H055/v2_sweep_20260518T220351Z/sweep_sidecar.json))
  - H062 Phase O.3 sweep `4e5a33175b518dd8f6228aa37a3068d0d5d2b0900589e3500aa922f8a0d729ec` ([artifacts/runs/H062/aggressive_sizing_sweep_20260515T235648Z/sweep_sidecar.json](../../../artifacts/runs/H062/aggressive_sizing_sweep_20260515T235648Z/sweep_sidecar.json))
  - H062 C9 step-up `6f154944a1708b30f015e57af1844e564fae96cead7501b93d26757195f5b794` ([artifacts/runs/H062/c9_bocd_step_up_20260516T013136Z/sidecar.json](../../../artifacts/runs/H062/c9_bocd_step_up_20260516T013136Z/sidecar.json))
  - H062 C9 km-era decomposition `9d07d5563644fba0e0899bca5d40a14f2be73ad8afd6ee1b0050297ae0e29270` ([artifacts/runs/H062/c9_km_era_decomposition_20260516T041548Z/sidecar.json](../../../artifacts/runs/H062/c9_km_era_decomposition_20260516T041548Z/sidecar.json))
  - H062 C9 km_floor sweep `318e035a05d84f6b0bcd8c421762016753bb35393855b30e2c7827188864c35a` ([artifacts/runs/H062/c9_km_floor_sweep_20260516T040904Z/sidecar.json](../../../artifacts/runs/H062/c9_km_floor_sweep_20260516T040904Z/sidecar.json))
  - H062 C9 2026 Q1Q2 `a1d16d3af05c75224445593654175dd6c15e4518cb3c2317050d69cf0d8fb3d7` ([artifacts/runs/H062/c9_2026_q1q2_20260516T040345Z/sidecar.json](../../../artifacts/runs/H062/c9_2026_q1q2_20260516T040345Z/sidecar.json))
  - H062 C3 2026 Q1Q2 `4b3d09609f5911c674eb6e470580bdfd21f4112f99063ad43cb0ddf6bcca6680` ([artifacts/runs/H062/c3_2026_q1q2_20260516T001902Z/sidecar.json](../../../artifacts/runs/H062/c3_2026_q1q2_20260516T001902Z/sidecar.json))

## Append discipline

- Sections 1-5 are frozen at investigation start (this commit); they MAY be edited only via versioned-successor pattern per ADR-0013 §4.1.
- Sections 6-8 are APPEND-as-work-completes; rows in §6 ablation table are immutable once landed.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
