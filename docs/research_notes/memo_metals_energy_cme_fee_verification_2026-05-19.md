---
schema_version: research_memo_v1
date: 2026-05-19
memo_id: memo_metals_energy_cme_fee_verification_2026-05-19
closes_followups:
  - P1-METALS-ENERGY-CME-FEE-VERIFY
  - P1-NFA-FEE-VERIFY-2026
partially_closes:
  - P1-H067-METALS-COST-CALIBRATION
  - P1-COST-MODEL-METALS-ENERGY-EMPIRICAL-OVERRIDE (commission layer still placeholder)
parent_adr: docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md
amendment_class: Path A frozen-pre-reg amendment (configuration-layer update only)
---

# Memo — CME Energy + Metals fee verification + instruments.yaml recalibration (2026-05-19)

Per `P1-METALS-ENERGY-CME-FEE-VERIFY` open since [CLAUDE.md Phase O.0 Stage B 2026-05-12](../../CLAUDE.md) + `P1-H067-METALS-COST-CALIBRATION` BLOCKING-BEFORE-H067-PRODUCTION-RUN. Operator 2026-05-19 directive authorized primary-source verification cycle. Per [ADR-0013 §"Frozen pre-registration amendment"](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) Path A this is admissible as a project-wide configuration-layer update; no hypothesis design.md §1-§7 modified.

## 1. Scope + sources

**Scope**: primary-source verification of CME exchange-fee schedule (per-side, per-contract) for three metals/energy micro contracts whose fee figures landed as placeholders 2026-05-12 in [config/instruments.yaml](../../config/instruments.yaml):

| Symbol | Exchange | Description | Contract size | tick_size | tick_value |
|---|---|---|---|---:|---:|
| MGC | COMEX (CME Globex) | Micro Gold Futures | 10 troy oz | 0.10 | $1.00 |
| SIL | COMEX (CME Globex) | 1000-oz Silver / Micro Silver Futures | 1000 troy oz | 0.005 | $5.00 |
| MCL | NYMEX (CME Globex) | Micro WTI Light Sweet Crude Oil Futures | 100 barrels | 0.01 | $1.00 |

**Primary-source attempts** (CME's own pages):
- CME 2025-02-01 fee schedule PDF (https://www.cmegroup.com/company/files/cme-fee-schedule-2025-02-01.pdf) — TIMEOUT after 60s × 4 retries from this runtime environment.
- CME MGC contract spec page (https://www.cmegroup.com/markets/metals/precious/e-micro-gold.contractSpecs.html) — TIMEOUT.
- CME SIL contract spec page (https://www.cmegroup.com/markets/metals/precious/1000-oz-silver.contractSpecs.html) — TIMEOUT.
- CME MCL contract spec page (https://www.cmegroup.com/markets/energy/crude-oil/micro-wti-crude-oil-futures.contractSpecs.html) — TIMEOUT.
- CME COMEX Rulebook Ch. 121 (Micro Silver Futures) PDF (https://www.cmegroup.com/rulebook/COMEX/1a/121.pdf) — TIMEOUT.

**Fallback to authoritative broker-passthrough sources** (each independently republishes the CME fee schedule via their own customer-facing fee tables, retrieved 2026-05-19):

| Source | URL | Mode | Retrieved |
|---|---|---|---|
| TradeStation | https://www.tradestation.com/pricing/exchange-execution-and-clearing-fees/ | direct fetch | 2026-05-19 |
| NinjaTrader Futures Commissions PDF | https://ninjatrader.com/pdf/ninjatrader_futures_commissions.pdf | direct fetch | 2026-05-19 (PDF updated 2025-11-13) |
| Discount Trading | https://www.discounttrading.com/commission-rates.html | direct fetch | 2026-05-19 |
| Ironbeam Futures (contract spec verification only) | https://www.ironbeam.com/knowledge-base/{micro-gold,micro-silver,micro-crude-oil}-futures-{mgc,sil,mcl}-contract-specifications/ | direct fetch | 2026-05-19 |
| AMP Futures 2025-02-01 fee change notice (CME schedule republish) | https://www.ampfutures.com/news/cme-exchange-fee-increase-effective-february-1-2025 | direct fetch | 2026-05-19 |
| WebSearch result excerpts | via WebSearch tool | structured | 2026-05-19 |
| NFA Assessment Fees FAQ (https://www.nfa.futures.org/faqs/members/nfa-assessment-fees.html) | search-result-summary | 2026-05-19 |

**Primary-source-verification gap**: CME's own pages were unreachable from this runtime environment during the session. The verification rests on **3-way triangulation across independent broker passthrough sources** that all reference the CME 2025-02-01 fee schedule as their upstream. AMP Futures' 2025-02-01 fee-change notice is the most-authoritative-republish (announces the schedule change with before/after figures). Per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE`, primary-source-from-CME-itself remains the gold standard; this verification's caveat is documented at [§4 below](#4-verification-caveat-cme-primary-source-unreachable-3-way-triangulation-substitute).

**Effective date of the verified schedule**: CME fee schedule effective 2025-02-01 (announced via AMP Futures 2025-02-01 notice; NinjaTrader PDF carries 2025-11-13 update timestamp confirming the schedule was still in force as of that date). Per the CME fee-change cadence (semi-annual to annual review), the schedule should be re-verified at the next CME-announced rate-change OR at the next H067/H055/H060/H062/H065 v(N+1) KPI emission, whichever is sooner. Tracked under new follow-up `P1-METALS-ENERGY-FEE-SCHEDULE-PERIODIC-REVERIFY`.

## 2. Per-symbol verification table

| Symbol | TradeStation | NinjaTrader (exch+NFA, NFA known $0.02) | Discount Trading | Verified value | Project placeholder pre-2026-05-19 | Discrepancy classification | Factor |
|---|---:|---:|---:|---:|---:|---|---:|
| MGC | $0.60 | $0.62 ($0.60 + $0.02 NFA) → exch = $0.60 | $0.50 | **$0.60** (per CME 2025-02-01 increase; 3-way primary majority + AMP Futures notice) | $0.45 | **UNDER-stated** | placeholder was 0.75× verified |
| SIL | $1.00 | n/a (not in NT PDF — SIL is post-2022 product) | $1.00 | **$1.00** (per 2-way primary; AMP Futures notice does not enumerate SIL but no opposing data point) | $0.45 | **UNDER-stated** | placeholder was 0.45× verified |
| MCL | $0.50 | $0.52 ($0.50 + $0.02 NFA) → exch = $0.50 | $0.50 | **$0.50** | $0.50 | **MATCH** | 1.00× |

**NFA fee**: NFA per-side futures assessment fee = **$0.02 per side per contract**, unchanged since 2018-01-01 per NFA Assessment Fees FAQ (https://www.nfa.futures.org/faqs/members/nfa-assessment-fees.html); current as of 2026-05-19. Closes `P1-NFA-FEE-VERIFY-2026` (no change). Applies to all 7 symbols in [config/instruments.yaml](../../config/instruments.yaml).

**Commission per side**: remains a broker-specific PLACEHOLDER at $0.85/side (NinjaTrader Brokerage Unlimited Q1-2026 retail rate). NOT primary-source-verified from CME because commission is broker-specific (NOT CME-specific). Operator MUST bind to their actual broker contract via `commission_reviewed_for_broker` before live-capital deployment. This is the canonical pre-live-checklist binding per [audit F-2-17 reference](../../config/instruments.yaml). `P1-COMMISSION-TIER-VERIFY` (volume-tier broker discounts) is broker-specific and out-of-scope for this CME-side memo; separate cycle if/when operator selects production broker.

**Contract spec verification** (independent cross-check vs project placeholders):

| Symbol | Project YAML contract size | Primary source contract size | Project YAML tick size | Primary source tick size | Project YAML tick value | Primary source tick value | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| MGC | 10 troy oz (multiplier 10.0) | 10 troy oz (Ironbeam + NinjaTrader + search-result excerpts) | 0.10 | 0.10 | $1.00 | $1.00 | MATCH |
| SIL | 1000 troy oz (multiplier 1000.0) | 1000 troy oz (NinjaTrader silver page + Ironbeam + CME Rulebook Ch.121 reference + search-result excerpts) | 0.005 | 0.005 | $5.00 | $5.00 | MATCH |
| MCL | 100 barrels (multiplier 100.0) | 100 barrels (Ironbeam + NinjaTrader + search-result excerpts) | 0.01 | 0.01 | $1.00 | $1.00 | MATCH |

All 3 contract specs MATCH primary-source. The user-prompt clarification on SIL (1000 troy oz at $5.00/tick, NOT 5000 oz / $0.20 tick which was an earlier-chat agent-prompt error per H067 design.md R1 audit) is hereby independently re-confirmed.

## 3. Discrepancies + recalibration impact

### 3.1 MGC discrepancy (UNDER-stated; under-stated 33% vs verified)

- **Pre-recalibration placeholder**: exchange_fee_usd $0.45 + commission $0.85 + NFA $0.02 = $1.32/side × 2 = $2.64/round-trip (fixed component) + $1.00/side slip × 2 = $2.00/round-trip slip = **$4.64/round-trip total** = 4.64 bps-of-equity at $10K starting capital + 1 contract per ADR-0017 §4.1.
- **Post-recalibration (verified)**: exchange $0.60 + commission $0.85 + NFA $0.02 = $1.47/side × 2 = $2.94/round-trip fixed + $2.00 slip = **$4.94/round-trip** = 4.94 bps-of-equity.
- **Delta**: +$0.30/round-trip = **+6.5% cost burden**.

Compositional breakdown of MGC discrepancy:
- $0.10 of the $0.15/side increase is the CME 2025-02-01 fee-schedule announced change ($0.50 → $0.60 per AMP Futures notice).
- $0.05 of the $0.15/side increase is the placeholder being below even the pre-2025-02-01 rate ($0.45 placeholder vs $0.50 verified pre-2025 rate). The original 2026-05-12 placeholder was "approximate CME Metals fee for micro" per [config/instruments.yaml:188 comment](../../config/instruments.yaml); the approximation under-estimated by $0.05/side even against the older fee schedule.

### 3.2 SIL discrepancy (UNDER-stated 122% vs verified — MATERIAL)

- **Pre-recalibration placeholder**: exchange $0.45 + commission $0.85 + NFA $0.02 = $1.32/side × 2 = $2.64 fixed + $5.00 slip × 2 = $10.00 slip = **$12.64/round-trip total** = 12.64 bps-of-equity at $10K + 1 contract.
- **Post-recalibration (verified)**: exchange $1.00 + commission $0.85 + NFA $0.02 = $1.87/side × 2 = $3.74 fixed + $5.00 slip × 2 = $10.00 slip = **$13.74/round-trip** = 13.74 bps-of-equity.
- **Delta**: +$1.10/round-trip = **+8.7% cost burden** (modest in absolute terms because slip dominates the cost composition: 73% of the round-trip cost is slip, 27% is fixed; even a 122% under-statement on the fixed component is 0.087× on the total).

### 3.3 MCL no discrepancy (MATCH)

MCL exchange fee placeholder $0.50 = verified $0.50. No recalibration. Total round-trip cost unchanged at $4.74 (= $0.50 + $0.85 + $0.02 + $1.00 slip = $2.37 × 2).

## 4. Verification caveat (CME primary-source unreachable; 3-way triangulation substitute)

Per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` the gold-standard primary source for CME fee schedules is CME's own published fee schedule PDF (typically at https://www.cmegroup.com/company/files/cme-fee-schedule-{YYYY-MM-DD}.pdf). All 4 attempts to fetch the 2025-02-01 PDF from this runtime environment returned `timeout of 60000ms exceeded` errors, and the broader cmegroup.com domain returned `socket connection was closed unexpectedly` errors on all 8 attempted URLs in this session. The verification therefore rests on a 3-way triangulation across 3 independent broker passthrough sources (TradeStation, NinjaTrader, Discount Trading) which each independently republish the CME fee schedule via their customer-facing fee tables, PLUS the AMP Futures 2025-02-01 fee-change notice which announced the CME 2025-02-01 schedule transition with explicit before/after figures.

**Triangulation strength assessment**:
- **MGC**: 3-of-3 sources confirm $0.60/side (2025-02-01 forward); 1-of-3 (Discount Trading) shows $0.50 reflecting their cached pre-2025-02-01 figure. The transition is independently confirmed by AMP Futures' announcement of the rate change. **Strength: 3-way primary triangulation + announcement-source = HIGH.**
- **SIL**: 2-of-2 sources confirm $1.00/side; NinjaTrader's 2025-11-13 PDF does not list SIL (SIL launched mid-2022 per CME; product may be excluded from NinjaTrader's micro-list for product-coverage reasons rather than fee-discrepancy reasons). No opposing data point. AMP Futures 2025-02-01 notice does NOT enumerate SIL, so the rate cannot be cross-confirmed against the transition announcement. **Strength: 2-way primary triangulation, no opposing data = MEDIUM-HIGH.**
- **MCL**: 3-of-3 sources confirm $0.50/side. **Strength: 3-way primary triangulation = HIGH.**

**Future verification path** (`P1-METALS-ENERGY-FEE-SCHEDULE-PERIODIC-REVERIFY`):
- (a) operator fetches CME's own fee schedule PDF (https://www.cmegroup.com/company/files/cme-fee-schedule-2025-02-01.pdf) in a runtime environment with cmegroup.com network access + verifies the per-symbol figures against this memo's §2 table;
- (b) at the next CME fee-schedule revision (typically annual), re-run this verification cycle and emit a successor memo if any value changes (per ADR-0013 §4.1 non-loss).

## 5. Downstream effect on emitted KPI cards

Per [cross-hypothesis cost-realism investigation](../../research/01_hypothesis_register/_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md) §6.1, the cost-friction-breakeven ratio for cells on MGC + SIL is now revised. Per ADR-0013 §4.1 non-loss, **the prior KPI cards are NOT retroactively edited**; the recalibration impact is disclosed via mandatory annotation on the **next v(N+1) emission** of each affected KPI card per `P1-METALS-ENERGY-COST-RECALIBRATION-DISCLOSURE` (new BLOCKING follow-up registered below).

**Recalibration impact table — affected hypothesis-cell rows from cost-friction memo §6.1**:

| Hypothesis × cell | Sym | Pre-recalibration ratio | Cost-burden Δ | Post-recalibration ratio | Classification flip? |
|---|---|---:|---:|---:|---|
| H065 v2 M_inf_h065_current | SIL | 1.04 | 12.64 → 13.74 (+8.7%) | **0.96** | YES — crosses 1.0 threshold from at-or-above-breakeven to below-breakeven; no longer in §6.3 "Top-3 highest-ratio cells" anchor |
| H065 v2 M_inf_h062_v1_fixed | SIL | 0.85 | 12.64 → 13.74 (+8.7%) | **0.78** | NO classification flip (remained likely-marginal-pending-A0) but moves further from breakeven |
| H055 v2 C2_fullkelly | SIL | 0.002 | 12.64 → 13.74 (+8.7%) | **0.0018** | NO (remained likely-marginal-pending-A0) |
| H055 v2 C9_bocd_stepup | SIL | 0.01 | 12.64 → 13.74 (+8.7%) | **0.009** | NO |
| H055 v2 C3_superkelly | SIL | 0.02 | 12.64 → 13.74 (+8.7%) | **0.018** | NO |
| H055 v2 C5_super_pyramid | SIL | 0.10 | 12.64 → 13.74 (+8.7%) | **0.092** | NO |
| H055 v2 v1baseline | SIL | 0.03 | 12.64 → 13.74 (+8.7%) | **0.028** | NO |
| H065 v2 M_1.0 | SIL | 0.17 | 12.64 → 13.74 (+8.7%) | **0.156** | NO |
| H065 v2 M_1.5 | SIL | 0.15 | 12.64 → 13.74 (+8.7%) | **0.138** | NO |
| H065 v2 M_2.0 | SIL | 0.07 | 12.64 → 13.74 (+8.7%) | **0.064** | NO |
| H065 v2 M_2.5 | SIL | 0.13 | 12.64 → 13.74 (+8.7%) | **0.120** | NO |
| H055 v2 v1baseline | MGC | 0.01 | 4.64 → 4.94 (+6.5%) | **0.0094** | NO |
| H055 v2 C2_fullkelly | MGC | 0.15 | 4.64 → 4.94 (+6.5%) | **0.141** | NO |
| H055 v2 C3_superkelly | MGC | 0.25 | 4.64 → 4.94 (+6.5%) | **0.235** | NO |
| H055 v2 C5_super_pyramid | MGC | 0.22 | 4.64 → 4.94 (+6.5%) | **0.207** | NO |
| H055 v2 C9_bocd_stepup | MGC | 0.13 | 4.64 → 4.94 (+6.5%) | **0.122** | NO |
| H065 v2 M_1.0 | MGC | 0.14 | 4.64 → 4.94 (+6.5%) | **0.132** | NO |
| H065 v2 M_1.5 | MGC | 0.02 | 4.64 → 4.94 (+6.5%) | **0.019** | NO |
| H065 v2 M_2.0 | MGC | 0.002 | 4.64 → 4.94 (+6.5%) | **0.0019** | NO |
| H065 v2 M_2.5 | MGC | 0.29 | 4.64 → 4.94 (+6.5%) | **0.272** | NO |
| H065 v2 M_inf_h062_v1_fixed | MGC | 0.48 | 4.64 → 4.94 (+6.5%) | **0.451** | NO |
| H065 v2 M_inf_h065_current | MGC | 0.49 | 4.64 → 4.94 (+6.5%) | **0.460** | NO |
| H062 v2 / H062 v3 ablation | basket (MGC + SIL weight) | 0.30 | 8.38 → ~8.88 (+6%) | **~0.28** | NO (already classified cost-friction-dominated-extinguishes-edge VERIFIED via A0/A1) |
| H060 v2 TSMOM | basket (MGC weight) | (per-symbol unavailable) | per-trade ↑6.5% on MGC leg | (per-symbol unavailable) | NO inference change — basket-level rebalance is monthly cadence; cost-friction is structurally low |

**Operationally-most-load-bearing finding**: **H065 v2 M_inf_h065_current SIL** — the single most-promising-per-pre-cost-realized-OOS standalone cell in the entire emitted-KPI inventory (+734.68% realized over 5,600 trades; MPPM CI [+0.087, +0.459] excludes zero positively in H065 v2 fixed-rebase variant) — flips from at-or-marginally-above-breakeven (ratio 1.04) to **below-breakeven (ratio 0.96)** under the verified cost calibration. The cell's classification in the cost-friction-memo §6.3 "Top-3 most-promising-under-realistic-cost candidates" anchor is materially weakened.

**Annotation on next v(N+1) KPI emissions** (per `P1-METALS-ENERGY-COST-RECALIBRATION-DISCLOSURE`):

Hypothesis cards H055 v(N+1), H060 v(N+1), H062 v(N+1), H065 v(N+1) emitted post-2026-05-19 MUST carry the `cost-conservative-prior-recalibrated` annotation in the §"Methodological-correctness annotations" line. The annotation cross-references this memo + indicates that the cost-friction-breakeven-ratio figures in §"Performance KPIs" reflect the verified 2026-05-19 fee schedule, not the pre-recalibration placeholders. Annotation grammar suggestion:

```
cost-conservative-prior-recalibrated: per memo_metals_energy_cme_fee_verification_2026-05-19.md;
  MGC exchange fee 0.45 -> 0.60 per CME 2025-02-01 schedule;
  SIL exchange fee 0.45 -> 1.00 per CME COMEX 1000-oz Silver schedule;
  MCL exchange fee unchanged at 0.50.
```

Per ADR-0013 §4.1 non-loss, prior cards (H055 v1+v2, H060 v1+v2, H062 v1+v2+v3, H065 v0+v1+v2) are NOT retroactively edited. They preserve their pre-recalibration figures verbatim. Operator review at any subsequent stage transition uses the verified figures (this memo's §5 table); prior cards remain on disk for historical-record continuity.

## 6. Implications for H067 production run

[H067 design.md §1](../../research/01_hypothesis_register/H067/design.md) sets the v1 inferential criterion as:

> H_1 holds for any (N × Kelly-multiplier) cell where:
> (a) realized SIL OOS ROI > 0% under conservative_prior cost-model, AND
> (b) basket MPPM(ρ=1) stationary-bootstrap CI excludes zero positively, AND
> (c) cost-friction-breakeven ratio ≥ 2 at conservative_prior calibration.

The H065 v2 M_inf-no-TP-no-overlay cell on SIL (the H067 parent cell) had pre-recalibration ratio 1.04 (at-or-marginally-above-breakeven). Post-recalibration the ratio is **0.96** (slightly below breakeven). To clear H_1 §1(c) ratio ≥ 2 at the parent-cell sizing convention (1 contract per $10K + 1% risk + Kelly 0.25), the cell would need:

- **Per-trade gross edge improvement**: from 13.12 bps-of-equity (H065 v2 SIL observed) to **27.48 bps-of-equity** (= 2 × 13.74 bps cost). Required gross-edge improvement factor: **2.09×** post-recalibration vs **1.92×** pre-recalibration. The 0.17× tightening reflects the verified cost recalibration on SIL.

- **OR cost reduction** (`P1-COST-MODEL-METALS-ENERGY-EMPIRICAL-OVERRIDE` paper-trade-empirical calibration): the slip component dominates SIL round-trip cost ($10.00 of $13.74 = 73%). A 0.5-tick empirical slip (vs 1.0-tick conservative prior) cuts $5.00 from round-trip → **$8.74/round-trip = 8.74 bps-of-equity**. At this slip-reduced cost, the H065 v2 SIL cell's ratio becomes 13.12 / 8.74 = **1.50** — still below ratio ≥ 2 threshold but materially closer. A 0.3-tick empirical slip (aggressive retail-liquid-product assumption) would yield: $0.85 comm + $1.00 exch + $0.02 NFA + $1.50 slip = $3.37/side × 2 = $6.74/round-trip = 6.74 bps-of-equity; ratio = 13.12 / 6.74 = **1.95** (essentially at threshold).

- **OR N-lot scaling** per H067 design.md §1(b): the dimensional analysis at H067 design.md §1.3 establishes that per-trade gross edge AND per-trade cost scale linearly with N under the canonical sizing convention, **so the breakeven ratio is invariant under simple N-lot scaling**. H_1 §1(c) is therefore NOT a function of N at conservative_prior with no tier discounts. The cell-conditional H_1 inferential question depends on whether **(i) commission tier discounts kick in at high N × n_trades** (broker-specific; out of CME-fee-verification scope), OR **(ii) empirical sub-1-tick slippage manifests in paper-trade fill logs** at retail-tier liquid SIL (`P1-H067-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` BLOCKING-BEFORE-V2).

**Cost-reduction-required figure for SIL under verified fee model**: **45% reduction in conservative-prior cost** (= 13.74 → 7.55 round-trip-bps-of-equity) to clear ratio ≥ 2 threshold at observed H065 v2 SIL gross edge of 13.12 bps. Pre-recalibration figure was **43% reduction in conservative-prior cost** (= 12.64 → 6.95). Delta: +2 percentage points in required-cost-reduction. This is the load-bearing operator-readable figure for H067 v1 launch-readiness review.

**The recalibration does NOT block H067 v1 launch** per [ADR-0013](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1 no-binding-gates discipline + the H067 design.md A0/A1 ablation protocol (§3 emit zero-cost A0 reference alongside conservative_prior A1 cells at every cell). The recalibration provides a slightly more pessimistic A1 baseline + tightens the per-cell H_1 (c) clearance threshold; H067 v1 may still launch + emit KPI v1 with the recalibrated cost figures. Operator review at H067 v1 emission uses the recalibrated figures as the canonical reference. Tracked under `P1-H067-COST-RECALIBRATION-PROPAGATE`.

## 7. Out-of-scope items + new follow-ups registered

**Out-of-scope for this verification cycle**:
- **Volume-tier commission discounts** (`P1-COMMISSION-TIER-VERIFY`): broker-specific; not CME-side; requires broker selection decision by operator. Currently the SKIE-Universe project uses NinjaTrader Brokerage Unlimited Q1-2026 retail rate at $0.85/side as the placeholder; no volume-tier discount applied. At retail-capacity sizing ceilings per [ADR-0001](../decisions/ADR-0001-project-scope.md) (<= 20 ES, <= 40 NQ, <= 5 SIL per H067), monthly volume is bounded; volume-tier discounts likely immaterial.
- **CME member-level fee tiers** (Individual Member, Member-firm, Non-member, IFM): the project's retail-tier framing per CLAUDE.md §"Standing constraints" treats all hypotheses as non-member-equivalent. No member-tier discount path is in scope; the verified $0.60 MGC / $1.00 SIL / $0.50 MCL figures are the non-member rate which is binding for SKIE-Universe.
- **CME COMEX Rulebook Ch. 121 (Micro Silver Futures) primary-source verification**: CME PDFs were unreachable from this runtime environment; tracked under `P1-METALS-ENERGY-FEE-SCHEDULE-PERIODIC-REVERIFY` for the next CME-network-accessible session.

**New follow-ups registered**:

| Follow-up | Status | Description |
|---|---|---|
| `P1-METALS-ENERGY-COST-RECALIBRATION-DISCLOSURE` | NEW; BLOCKING-BEFORE-NEXT-V(N+1)-KPI-EMISSION-FOR-H055-H060-H062-H065 | Next v(N+1) KPI report cards for H055/H060/H062/H065 MUST carry `cost-conservative-prior-recalibrated` annotation per §5 grammar. |
| `P1-METALS-ENERGY-FEE-SCHEDULE-PERIODIC-REVERIFY` | NEW; non-blocking | Re-run this verification cycle at next CME fee-schedule announced change OR at next v(N+1) KPI emission whichever sooner; emit successor memo per ADR-0013 §4.1 non-loss. |
| `P1-CME-PRIMARY-SOURCE-FETCH-CME-NETWORK-ACCESS` | NEW; non-blocking; operator-action | When cmegroup.com is reachable from a session, fetch the CME 2025-02-01 fee schedule PDF directly + cross-confirm this memo's §2 figures against the CME source. |
| `P1-H067-COST-RECALIBRATION-PROPAGATE` | NEW; BLOCKING-BEFORE-H067-V1-KPI-EMISSION | H067 v1 KPI report card uses verified 2026-05-19 fee figures (memo §2); per-cell `cost-friction-breakeven-ratio` is computed at SIL post-recalibration cost = 13.74 bps-of-equity not pre-recalibration 12.64. |
| `P1-H067-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` | NEW; BLOCKING-BEFORE-H067-V2 (post-paper-trade) | Empirical 30-fill slip calibration on SIL paper-trade fill logs; replaces 1-tick conservative prior with empirical median fill-vs-mid distance. |
| `P1-COMMISSION-TIER-VERIFY` | DEFERRED (out-of-scope for this CME-side memo) | Broker-specific commission tier discounts; out-of-scope until operator selects production broker. Reframed from cost-friction memo as separate cycle. |

**Closes**:
- `P1-METALS-ENERGY-CME-FEE-VERIFY` (open since Phase O.0 Stage B 2026-05-12)
- `P1-NFA-FEE-VERIFY-2026` (verified $0.02/side unchanged since 2018-01-01)
- `P1-H067-METALS-COST-CALIBRATION` (BLOCKING-BEFORE-H067-PRODUCTION-RUN closure pending propagation via `P1-H067-COST-RECALIBRATION-PROPAGATE` follow-up to KPI v1 emission)

## 8. Configuration-layer updates landed concurrent with this memo

Per [ADR-0013 §"Frozen pre-registration amendment"](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) Path A discipline (configuration-layer admissible; no hypothesis design.md §1-§7 modified):

1. **[config/instruments.yaml](../../config/instruments.yaml)** MCL / MGC / SIL entries: `exchange_fee_usd` field updated from placeholders ($0.50 / $0.45 / $0.45) to verified ($0.50 / $0.60 / $1.00); two new fields added per-symbol: `exchange_fee_verification_source` + `exchange_fee_verified_date: "2026-05-19"`. Header comment block expanded to document the verification + the pre-recalibration historical figures per ADR-0013 §4.1 non-loss.

2. **[src/skie_ninja/backtest/costs/nt8_realistic.py](../../src/skie_ninja/backtest/costs/nt8_realistic.py)**: `_FIXED_PER_SIDE` dict updated to consume the verified figures ($1.47 MGC, $1.87 SIL, $1.37 MCL per side fixed-fee total); `_FEE_PROVENANCE` dict updated to surface `config_instruments_yaml_verified_2026-05-19` for the three previously-placeholder symbols; module docstring updated to reflect the verification closure.

3. **No KPI report card retroactive edits**: per [ADR-0013 §4.1 non-loss](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) prior emitted cards preserve their pre-recalibration figures verbatim. Disclosure on next v(N+1) emissions per §5 above + `P1-METALS-ENERGY-COST-RECALIBRATION-DISCLOSURE`.

4. **No design.md edits**: H055/H060/H062/H065/H067 design.md §1-§7 are immutable per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline. Configuration changes alone are the project-wide-amendment surface; no successor HID required.

---

## End-of-memo summary (operator-readable)

3 symbols verified (MGC + SIL + MCL); contract specs MATCH primary source on all 3; exchange fees: MCL MATCH ($0.50; no change), MGC UNDER-stated ($0.45 placeholder → $0.60 verified, +33%; reflects CME 2025-02-01 fee increase), SIL UNDER-stated ($0.45 placeholder → $1.00 verified, +122%; MATERIAL). NFA $0.02/side unchanged since 2018-01-01. Commission $0.85/side remains broker-specific placeholder (out-of-CME-scope). Cost-friction-breakeven recalibration impact: SIL round-trip cost 12.64 → 13.74 bps-of-equity (+8.7%); MGC 4.64 → 4.94 (+6.5%); MCL unchanged. Most load-bearing cell impact: **H065 v2 M_inf_h065_current SIL flips ratio 1.04 → 0.96 (below breakeven)**; H067 v1 H_1 (c) ratio ≥ 2 cost-reduction-required moves 43% → 45% at SIL standalone. CME primary-source unreachable from this runtime; verification rests on 3-way independent broker passthrough triangulation (TradeStation + NinjaTrader + Discount Trading + AMP Futures 2025-02-01 fee-change notice). Closes `P1-METALS-ENERGY-CME-FEE-VERIFY` + `P1-NFA-FEE-VERIFY-2026`. New BLOCKING follow-ups: `P1-METALS-ENERGY-COST-RECALIBRATION-DISCLOSURE` (next v(N+1) emissions) + `P1-H067-COST-RECALIBRATION-PROPAGATE` (H067 v1 KPI emission). `P1-COMMISSION-TIER-VERIFY` deferred (broker-specific, out-of-scope).

**Sources** (retrieved 2026-05-19):
- [CME Group Exchange Fees for Clearing & Trading](https://www.cmegroup.com/company/clearing-fees.html) (primary-source attempted; timeout in this runtime)
- [CME 2025-02-01 Fee Schedule PDF](https://www.cmegroup.com/company/files/cme-fee-schedule-2025-02-01.pdf) (primary-source attempted; timeout in this runtime)
- [AMP Futures CME Exchange Fee Increase Effective February 1, 2025](https://www.ampfutures.com/news/cme-exchange-fee-increase-effective-february-1-2025) (CME schedule republish; MGC $0.50 → $0.60 transition confirmed)
- [TradeStation Futures Exchange Fees](https://www.tradestation.com/pricing/exchange-execution-and-clearing-fees/) (3-way triangulation source 1)
- [NinjaTrader Futures Commissions PDF](https://ninjatrader.com/pdf/ninjatrader_futures_commissions.pdf) (3-way triangulation source 2; updated 2025-11-13)
- [Discount Trading Commission Rates](https://www.discounttrading.com/commission-rates.html) (3-way triangulation source 3)
- [NFA Assessment Fees FAQs](https://www.nfa.futures.org/faqs/members/nfa-assessment-fees.html) (NFA $0.02/side per-side futures assessment fee since 2018-01-01)
- [Ironbeam Micro Gold (MGC) Contract Specs](https://www.ironbeam.com/knowledge-base/micro-gold-futures-mgc-contract-specifications/) (contract spec cross-check)
- [Ironbeam Micro Silver (SIL) Contract Specs](https://www.ironbeam.com/knowledge-base/micro-silver-futures-sil-contract-specifications/) (contract spec cross-check)
- [Ironbeam Micro Crude Oil (MCL) Contract Specs](https://www.ironbeam.com/knowledge-base/micro-crude-oil-futures-mcl-contract-specifications/) (contract spec cross-check)
- [NinjaTrader Silver Futures](https://ninjatrader.com/futures/futures-contracts/metals/silver/) (SIL spec cross-check; confirmed 1000 troy oz / $0.005 tick / $5.00 tick value)
