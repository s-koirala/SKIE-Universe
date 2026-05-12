---
id: ADR-0023
title: Metals and energy futures substrate expansion (CL/MCL/GC/MGC + deferred Tier-2)
status: proposed
date: 2026-05-12
decision-owner: Lead researcher
supersedes: none
related:
  - docs/decisions/ADR-0001-project-scope.md
  - docs/decisions/ADR-0002-bridge-selection.md
  - docs/decisions/ADR-0006-scope-extension-hmm-0dte.md
  - docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md
  - docs/decisions/ADR-0019-barbell-payoff-shape-screening.md
  - docs/decisions/ADR-0021-liquidity-provision-research-track-scoping.md
  - config/instruments.yaml
  - src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py
  - src/skie_ninja/utils/clock.py
  - hypothesis_backlog.md
---

# ADR-0023 — Metals and energy futures substrate expansion

## Status

Proposed. Acceptance follows (a) operator authorization of the Databento `metadata.get_cost` quote per `P1-DATABENTO-METALS-ENERGY-COST-DOSSIER`, (b) landing of the four BLOCKING-before-H060 implementation follow-ups enumerated in §Decision, and (c) first pre-registered metals/energy hypothesis (H060) clearing design audit-remediate-loop.

## Context

### Operator directive 2026-05-12

User 2026-05-12 directive (paraphrased from the operator transcript): "let us stick to futures moving forward. including metals and energy. we have databento api." This authorizes substrate expansion within the CME-Globex futures universe to cover metals and energy contracts, leveraging the existing Databento API access that powered the H050 Cell-I ES/NQ ingest per `P1-H050-CELL-I-LIVE-COST-CAPTURE`.

### Empirical motivation — 2026-05-06 pilot ledger cross-asset divergence

The 2026-05-06 operator pilot ledger recorded in [data/external/h055_pilot_ledger/Performance.csv](../../data/external/h055_pilot_ledger/Performance.csv) (171 trades, SHA256 `4c5ebf85f38f2881df12335f27f2007d930e7951c71c9339d2a2d3f9735c454a`; landed via CLAUDE.md Phase I) contains a load-bearing empirical observation: on a single 2026-05-06 session the operator traded CL while CL was -10% intraday and NQ was at all-time highs across the same week. That cross-asset regime divergence is structurally invisible to a substrate restricted to ES/NQ correlated equity-index contracts. The H055 v1 design.md §1 acknowledges this gap (`P1-H055-CL-MCL-MYM-MGC-INGEST-AND-EXTEND` was registered 2026-05-06) but the follow-up has remained open without action. This ADR operationalizes that follow-up.

The cross-asset regime-divergence framing is consistent with ADR-0019 (barbell payoff-shape screening across asset classes; gold as risk-off complement) and ADR-0020 (meta-portfolio orchestrator). Both ADRs presuppose a cross-asset universe that this expansion enables.

### Phase N strategic redirect

The 2026-05-12 operator conversation registered a strategic redirect away from deepening the H055-H059 successor tree (per [plan/buildouts/h055_successor_tree_2026-05-06.md](../../plan/buildouts/h055_successor_tree_2026-05-06.md)) in favor of universe expansion. The redirect rationale is that incremental H056-H059 ML-stacking work amortizes over a single asset class, whereas metals/energy substrate expansion unlocks a structurally new dimension. Metals/energy is the natural first expansion vector because:

1. **Same venue.** CME Group Globex hosts NYMEX energy (CL/NG/RB/HO) and COMEX metals (GC/SI/HG/PL) alongside the existing CME equity-index contracts. No new data-vendor relationship is required.
2. **Same Databento dataset.** Databento serves all CME-Globex futures via the `GLBX.MDP3` dataset family per [the Databento Datasets catalog](https://databento.com/datasets) (retrieval 2026-05-12). The existing `scripts/ingest.py --dataset vendor_legacy_1min` pipeline pattern carries over with parameter changes only.
3. **Same NinjaTrader execution path.** NinjaTrader 8 supports CME metals/energy contracts natively per ADR-0002; no new bridge architecture is needed for the terminal NinjaScript implementation per ADR-0013 §5.
4. **Operator domain experience.** The pilot ledger demonstrates the operator already trades CL/MCL discretionarily; the mechanical hypothesis layer can be calibrated against operator behavioral asymmetry (per the H055 design.md §1 motivation pattern).

### Pre-existing constraints

The substrate-expansion proposal interacts with three pre-existing project constraints that this ADR must address:

- **ADR-0001 capacity ceilings** were specified for equity-index contracts only (≤20 ES, ≤40 NQ). Metals/energy capacity must be extended explicitly.
- **Session policy** in [src/skie_ninja/utils/clock.py](../../src/skie_ninja/utils/clock.py) splits CME equity-index trading into RTH (08:30-15:15 CT) / ETH (17:00-08:30 CT next day) / HALT segments per the equity-index session calendar. CME metals and energy follow a different convention: 17:00 CT Sunday through 16:00 CT Friday with a single 16:00-17:00 CT daily maintenance break per the CME Globex trading hours pages ([energy](https://www.cmegroup.com/markets/energy.html), [metals](https://www.cmegroup.com/markets/metals.html); retrieval 2026-05-12). The single-RTH/ETH-split assumption embedded in `clock.py` does not generalize.
- **Roll calendar** in [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) v0.3.0 assumes quarterly H/M/U/Z roll codes per CME equity-index convention. Energy contracts (CL, NG, RB, HO) have monthly delivery — twelve contracts per year per symbol — and metals (GC, SI, HG) have mixed bi-monthly conventions. The roll-adjusted module's quarterly assumption is invalid for both classes.

## Decision (proposed)

### 1. Target contracts

**Tier 1 (BLOCKING for H060 pre-registration; landing concurrently with this ADR's acceptance):**

| Symbol | Description | Multiplier | Tick / Tick $ | Source |
|---|---|---|---|---|
| CL | NYMEX WTI Light Sweet Crude, 1000 bbl | $1000/$ | 0.01 / $10.00 | [CME Energy](https://www.cmegroup.com/markets/energy.html) |
| MCL | Micro WTI Crude, 100 bbl | $100/$ | 0.01 / $1.00 | [CME Energy](https://www.cmegroup.com/markets/energy.html) |
| GC | COMEX Gold, 100 troy oz | $100/oz | 0.10 / $10.00 | [CME Metals](https://www.cmegroup.com/markets/metals.html) |
| MGC | Micro Gold, 10 troy oz | $10/oz | 0.10 / $1.00 | [CME Metals](https://www.cmegroup.com/markets/metals.html) |

Each row pulled from the linked CME Group contract-spec page at retrieval date 2026-05-12. Numeric values are reproduced in the [config/instruments.yaml](../../config/instruments.yaml) extension landed under `P1-INSTRUMENTS-YAML-METALS-ENERGY-EXTEND`; the YAML carries the authoritative copy and this table is informational.

**Tier 2 (deferred until Tier-1 operational; tracked as the open universe):**

NG (Henry Hub Natural Gas, 10,000 MMBtu), RB (RBOB Gasoline, 42,000 gal), HO (NY Harbor ULSD heating oil, 42,000 gal), HG (COMEX Copper, 25,000 lbs), SI (COMEX Silver, 5,000 troy oz), SIL (Micro Silver, 1,000 troy oz), PL (NYMEX Platinum, 50 troy oz). All sourced from the same CME spec pages. Tier-2 instruments enter via amendment to this ADR after Tier-1 production walk-forward emits a KPI report card on at least one metals/energy hypothesis.

The Tier-1 / Tier-2 split is operational, not literature-driven: Tier-1 covers the four contracts the operator traded discretionarily in the 2026-05-06 pilot ledger; Tier-2 expands once the substrate-and-tooling pattern is validated against Tier-1 production.

### 2. Monthly-roll calendar module

A new module at `src/skie_ninja/data/ingest/vendor_legacy_1min_monthly_roll_adjusted.py` will parallel the existing quarterly `vendor_legacy_1min_roll_adjusted.py` v0.3.0. The new module handles:

- **CME monthly roll codes:** F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun, N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec. Codes per the CME Globex contract-specification convention used uniformly across all CME products; verification against the [CME contract-spec pages](https://www.cmegroup.com/markets/energy.html) at retrieval date 2026-05-12.
- **Energy roll cadence.** CL has 12 active monthly contracts per year with rollover typically 3-5 sessions before last trading day (LTD), which itself falls on the third business day prior to the 25th calendar day of the month preceding the contract month. The roll-decision rule will be open-interest-crossover-based per the AFML §2.4.3 anchor invariant convention preserved from the v0.3.0 quarterly module (per CLAUDE.md ledger entry on `329fd1b` decade-wraparound bug fix), not a fixed-calendar-day rule, so the module degrades gracefully across CME contract-calendar revisions.
- **Metals roll cadence.** GC has six actively-traded contracts per year — F/J/M/Q/V/Z (Feb/Apr/Jun/Aug/Oct/Dec) — vs SI / HG actively trading H/K/N/U/Z (Mar/May/Jul/Sep/Dec). The roll-decision rule is the same open-interest-crossover convention; the difference between metals and energy is contract-density per calendar year, not algorithmic.
- **Contract-id disambiguation.** The decade-wraparound `contract_id_full` invariant introduced in the v0.3.0 quarterly module per the 2026-04-26 audit trail carries over: `contract_id_full` is constructed as `{root}{month_code}{year_4digit}` (e.g., `CLZ2025` not `CLZ5`) to prevent the cross-decade collision bug that the multi-decade ES/NQ substrate exposed.
- **AFML §2.4.3 anchor invariant verification.** End-to-end test that the most-recent contract anchors at adjustment-factor 1.0 (per `vendor_legacy_1min_roll_adjusted.py` v0.3.0 acceptance criterion); regression test landed alongside module implementation.

Tracked under new follow-up `P1-MONTHLY-ROLL-MODULE-IMPL` (BLOCKING-BEFORE-H060-PRODUCTION-RUN).

### 3. Session policy extension

CME energy and metals trade Sunday 17:00 CT through Friday 16:00 CT with a single daily maintenance break 16:00-17:00 CT, per the CME Globex trading-hours pages cited above. This is structurally different from the CME equity-index split RTH (08:30-15:15 CT) / ETH (17:00-08:30 CT) embedded in [src/skie_ninja/utils/clock.py](../../src/skie_ninja/utils/clock.py).

The session-policy module will be extended to support per-instrument session classification:

- Existing equity-index session taxonomy (RTH / ETH / OVN / HALT) preserved for ES / NQ / MES / MNQ — unchanged behavior.
- New metals/energy session taxonomy: ACTIVE (Sunday 17:00 CT → Friday 16:00 CT excluding maintenance break) / MAINTENANCE (daily 16:00-17:00 CT) / WEEKEND (Friday 16:00 CT → Sunday 17:00 CT). No RTH/ETH split because metals/energy intraday-volume profiles do not exhibit a clean equity-RTH-equivalent peak; pit-session conventions for CL pit (open-outcry 08:00-13:30 CT) are historical and not load-bearing for an electronic-execution-only research program.
- Per-instrument session classification is keyed off `InstrumentSpec.session_taxonomy: Literal["equity_index_rth_eth", "globex_24_5"]` (or equivalent enum); existing equity-index instruments default to `equity_index_rth_eth` for backward compatibility.
- DST handling: both taxonomies anchor to Chicago local time (America/Chicago) and inherit existing DST-correct behavior from `clock.py` v0.x.

Tracked under new follow-up `P1-SESSION-POLICY-24-5-IMPL` (BLOCKING-BEFORE-H060-PRODUCTION-RUN).

### 4. Cost model extension

Per ADR-0017 §"Cost-modeling realism" KPI convention and the existing cost-model pattern at [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../src/skie_ninja/backtest/costs/futures_orb_v1.py), each new instrument class gets a dedicated cost model:

- `NT8CrudeOilV1CostModel` covering CL + MCL.
- `NT8GoldV1CostModel` covering GC + MGC.

Each cost model captures:

1. **CME exchange fees per instrument.** Cite the CME Group [Schedule of Fees — Energy](https://www.cmegroup.com/company/clearing-fees.html) and [Schedule of Fees — Metals](https://www.cmegroup.com/company/clearing-fees.html) (retrieval 2026-05-12); these differ from the Equity Index VIP schedule embedded in the ES/NQ cost model. NinjaTrader Brokerage Unlimited commission rates apply uniformly per [the NT Brokerage public schedule](https://ninjatrader.com/futures/brokerage/) (retrieval 2026-05-12); these are the same across asset classes for retail-tier accounts.
2. **Tick-cost realism per instrument.** Per-contract tick value differs across the four Tier-1 contracts ($10 for CL/GC, $1 for MCL/MGC); the slippage / partial-fill assumptions must scale appropriately. Default model: 1-tick slippage on entry + 1-tick on exit per fill, calibrated per [NinjaTrader Sim101 fill simulation conventions](https://ninjatrader.com/support/helpGuides/nt8/sim101.htm) (retrieval 2026-05-12).
3. **Margin requirements.** CME initial-margin requirements differ across asset classes (cite the CME Group [Performance-Bond Requirements page](https://www.cmegroup.com/clearing/risk-management/financial-and-collateral-management/performance-bonds.html); retrieval 2026-05-12). The cost model exposes margin as a parameter for the ADR-0017 §"Risk-of-ruin Monte Carlo" primitive but does not enforce it (capacity ceilings in §5 below dominate).

Tracked under new follow-up `P1-METALS-ENERGY-COST-MODEL-IMPL` (BLOCKING-BEFORE-H060-PRODUCTION-RUN).

The 1-tick-slippage default is a project-operational placeholder per the ADR-0017 §"Cost-empirical-calibration" convention; the empirical calibration follow-up `P1-METALS-ENERGY-COST-EMPIRICAL-CALIBRATION` is registered as non-blocking pending paper-trade fill data accumulation.

### 5. ADR-0001 amendment — capacity ceiling extension

ADR-0001 §Capacity-ceiling table extended:

| Symbol | Retail capacity ceiling | Notional reference | Daily P/L variance proxy |
|---|---:|---|---|
| ES (existing) | ≤ 20 | $5K × 4500 × 20 = $450M nope; 50 × 4500 × 20 = $4.5M | per ADR-0001 |
| NQ (existing) | ≤ 40 | $20 × 18000 × 40 = $14.4M | per ADR-0001 |
| CL (new) | ≤ 5 | $1000 × 80 × 5 = $400K notional | ~$8K daily at typical 1-2% σ |
| MCL (new) | ≤ 50 | delta-equivalent to 5 CL | per CL row |
| GC (new) | ≤ 5 | $100 × 2000 × 5 = $1.0M notional | ~$10K daily at typical 1% σ |
| MGC (new) | ≤ 50 | delta-equivalent to 5 GC | per GC row |

The capacity ceilings are **project-operational defaults**, not derived from empirical capacity studies. The methodology is: pick a retail-realistic ceiling such that worst-case daily P/L variance at typical σ does not exceed ~2-5% of a notional $200K-$500K account. This anchors the figures to the operator's account size class without overfitting to a single-account snapshot.

Empirical calibration deferred to post-paper-trade follow-up `P1-ADR-0001-METALS-ENERGY-CAPACITY-CALIBRATE` (non-blocking).

### 6. Databento API spend governance

Precedent: H050 Cell-I (per `P1-H050-CELL-I-LIVE-COST-CAPTURE` closure 2026-04-26) recorded a live `metadata.get_cost` figure of $16.5171 USD for ES + NQ 2015-01-01 → 2025-12-{03,20} `ohlcv-1m` schema on the `GLBX.MDP3` dataset.

**Estimate for CL + MCL + GC + MGC 2015-01-01 → 2025-12-31 same schema:** $30-80 USD. Reasoning: per-symbol-decade Databento rate from H050 Cell-I ≈ $16.5171 / 2 symbols ≈ $8.25; metals/energy contract density is ~3× equity-index due to monthly vs quarterly rolls (more distinct continuous-contract identifiers per year for the Databento query), so per-symbol estimate scales to ~$15-25, times 4 symbols = $60-100 raw, discounted for Databento volume-aggregation rules to the $30-80 USD band.

This is a **pre-extraction estimate**, not a binding figure. The binding figure is the live `metadata.get_cost` output recorded in the operator-action follow-up `P1-DATABENTO-METALS-ENERGY-COST-DOSSIER` (operator runs `metadata.get_cost` for the target symbol-window combo, records the figure, and authorizes the spend per `P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE`). The two operator-action follow-ups are sequenced: cost-dossier before extraction-authorize; extraction-authorize before any actual Databento API spend.

### 7. Configuration

Extend [config/instruments.yaml](../../config/instruments.yaml) with CL, MCL, GC, MGC entries paralleling the existing ES/NQ/MES/MNQ structure. Each entry carries:

- `root`: `CL` / `MCL` / `GC` / `MGC`
- `exchange`: `NYMEX` (energy) or `COMEX` (metals)
- `multiplier`: per §1 table
- `tick_size`: per §1 table
- `tick_value`: per §1 table
- `session_taxonomy`: `globex_24_5`
- `roll_calendar`: `monthly` (CL, MCL) or `bimonthly_metals` (GC, MGC; per §2 roll-cadence table)
- `cme_spec_url`: link to the linked CME contract-spec page
- `cme_spec_retrieval_date`: `2026-05-12`
- `nt_brokerage_commission_per_contract_usd`: placeholder pending NinjaTrader Brokerage Unlimited fee verification
- `capacity_ceiling_contracts`: per §5 table

The schema extension is mechanical against the existing `InstrumentSpec` pydantic model; no schema change required if `session_taxonomy` and `roll_calendar` fields already exist on the model (verify during implementation). If schema extension is required, the `pydantic` schema bump lands concurrently with the config entries.

Tracked under new follow-up `P1-INSTRUMENTS-YAML-METALS-ENERGY-EXTEND` (BLOCKING-BEFORE-H060-PRE-REG).

## Consequences

### Positive

- **Unlocks H060** (pre-registered placeholder for first metals/energy hypothesis; cross-futures TSMOM is the natural first candidate per [Moskowitz-Ooi-Pedersen 2012 JFE](https://doi.org/10.1016/j.jfineco.2011.11.003) extension to commodity futures).
- **Unlocks H023** (pre-existing AIS oil-terminal events → CL hypothesis on the backlog; previously blocked by absence of CL substrate; remains gated by AIS data license but the futures-side substrate is now feasible).
- **Unlocks H024** (pre-existing ERCOT/PJM nodal LMP → NG hypothesis; same gating logic as H023).
- **Enables ADR-0019 barbell sibling-pair across asset classes** — gold (GC/MGC) as risk-off complement to equity-index in the barbell payoff-shape screening framework; previously not possible because the substrate was equity-index-only.
- **Enables ADR-0020 meta-portfolio orchestrator across asset classes** — the meta-portfolio framework presupposed cross-asset coverage and this expansion delivers the substrate prerequisite.
- **Strengthens the H055 cross-asset regime-divergence validation** — the H055 design.md §1 referenced the 2026-05-06 CL -10% vs NQ ATH pilot observation; with CL substrate in place, the cross-asset regime check moves from operator-narrative to backtested-evidence.

### Negative

- **Databento spend.** Estimated $30-80 USD; binding figure recorded post-`metadata.get_cost`.
- **Implementation lift.** Four BLOCKING follow-ups: monthly-roll module, session-policy 24/5 extension, two new cost models, instruments.yaml extension. Estimated ~half-day to one-day total lift at solo-developer pace per the existing v0.3.0 quarterly-roll module pattern (which took ~one day end-to-end per the 2026-04-23 audit trail).
- **Asset-class intraday-seasonality risk.** Energy and metals exhibit different intraday seasonality and regime structure than equity-index. OPEC announcements move CL more than FOMC moves ES at intraday grain; gold has a London/COMEX session-handoff microstructure that ES does not. Hypotheses developed on ES/NQ substrate may not transport to CL/GC; this is a feature (the substrate expansion is precisely to test cross-asset robustness), but it is a research-cost: each new hypothesis needs per-asset-class calibration where the equity-index hypotheses had one-shot ES + NQ calibration.
- **Roll-calendar complexity surface area.** Twelve monthly contracts per year per energy symbol vs four quarterly contracts per equity-index symbol triples the roll-event count per calendar year. This is the load-bearing risk: a roll-calendar bug at production-run scale on metals/energy will be three times more expensive than the equivalent bug at the same scale on equity-index. The AFML §2.4.3 anchor-invariant regression test from the v0.3.0 module is the structural defense.

### Open question — cross-month spreads

Should the project's universe include cross-month spreads (e.g., CL calendar spread CL_M2-CL_U2, GC-SI ratio across metals)? Calendar spreads have a distinct microstructure (lower volatility, often mean-reverting in commodity contango/backwardation regimes) and an entire literature in their own right. Deferred per `P1-ADR-0023-CALENDAR-SPREADS-V2`; primary-source anchoring for any calendar-spread hypothesis pre-registration deferred to that follow-up's Phase-0 lit-check.

**Decision: defer to v2 of this ADR.** Calendar spreads enter the universe only after Tier-1 outright-contract substrate has produced at least one KPI report card. The deferral logic parallels the ADR-0006 scope-extension precedent that staged HMM and 0DTE tracks across two ADRs rather than merging into one.

### Alternatives considered

**A. Extend to equities (ETFs / single names) instead of metals/energy.** Rejected. The operator directive 2026-05-12 explicitly anchored to futures ("let us stick to futures moving forward"); equities would also require a new data-vendor relationship (Databento covers equities under different dataset families with different licensing) and would dilute the project's intraday-futures focus per ADR-0001 §Scope.

**B. Restrict expansion to micro contracts only (MCL/MGC).** Rejected. The full-size contracts (CL, GC) have substantially higher open interest and tighter spreads (per the CME daily volume reports at retrieval 2026-05-12) — restricting to micros would systematically under-sample the cleanest microstructure regime. Capacity ceiling in §5 is the structural defense against full-size contracts blowing up at retail account size.

**C. Add Tier-2 contracts (NG, RB, HG, SI, etc.) in the same ADR.** Rejected. The Tier-1 / Tier-2 split is operationally important: Tier-1 covers what the operator actually trades discretionarily and what is mostly likely to fast-track to operator paper-trade and live. Tier-2 adds breadth at the cost of doubling the implementation surface area (more roll calendars, more cost models, more capacity calibration). Sequential expansion per the ADR-0006 staged-scope precedent is preferred over big-bang.

**D. Defer the entire metals/energy expansion until after H055 production-run results.** Rejected. The 2026-05-12 operator directive is explicit, and the H055 production-run timeline is uncertain pending the seven BLOCKING preconditions per H055 design.md §11.2 + the two remaining ADR-0017 primitives per CLAUDE.md Phase L. Decoupling the substrate-expansion track from the H055 track lets both progress in parallel; the substrate expansion does not depend on H055 results, and H055 does not depend on the metals/energy substrate.

## References

- [CME Group — Energy products landing page](https://www.cmegroup.com/markets/energy.html) (retrieval 2026-05-12).
- [CME Group — Metals products landing page](https://www.cmegroup.com/markets/metals.html) (retrieval 2026-05-12).
- [CME Group — Agriculture products landing page](https://www.cmegroup.com/markets/agriculture.html) (retrieval 2026-05-12; informational, agriculture is out of scope for this ADR).
- [CME Group — Clearing fees schedule](https://www.cmegroup.com/company/clearing-fees.html) (retrieval 2026-05-12).
- [CME Group — Performance-bond / initial-margin requirements](https://www.cmegroup.com/clearing/risk-management/financial-and-collateral-management/performance-bonds.html) (retrieval 2026-05-12).
- [Databento — Datasets catalog (GLBX.MDP3 coverage)](https://databento.com/datasets) (retrieval 2026-05-12).
- [NinjaTrader Brokerage — Commission schedule](https://ninjatrader.com/futures/brokerage/) (retrieval 2026-05-12).
- [Moskowitz, Ooi, Pedersen 2012 — "Time series momentum"](https://doi.org/10.1016/j.jfineco.2011.11.003) JFE 104(2):228-250 (primary; commodity-futures TSMOM canonical reference for the H060 motivation).
- [ADR-0001 — Project scope](ADR-0001-project-scope.md).
- [ADR-0002 — Bridge selection](ADR-0002-bridge-selection.md).
- [ADR-0006 — Scope extension: HMM regime track and 0DTE option track](ADR-0006-scope-extension-hmm-0dte.md) (staged-scope precedent).
- [ADR-0017 — Survival-constrained optimization paradigm](ADR-0017-survival-constrained-optimization-paradigm.md).
- [ADR-0019 — Barbell payoff-shape screening](ADR-0019-barbell-payoff-shape-screening.md).
- [ADR-0021 — Liquidity provision research-track scoping](ADR-0021-liquidity-provision-research-track-scoping.md).

## Follow-ups registered by this ADR

BLOCKING-BEFORE-H060-PRODUCTION-RUN:
- `P1-MONTHLY-ROLL-MODULE-IMPL` — implement `vendor_legacy_1min_monthly_roll_adjusted.py` paralleling v0.3.0 quarterly module; AFML §2.4.3 anchor-invariant regression test included.
- `P1-SESSION-POLICY-24-5-IMPL` — extend `src/skie_ninja/utils/clock.py` with per-instrument `session_taxonomy` keying off `InstrumentSpec`; new `globex_24_5` taxonomy.
- `P1-METALS-ENERGY-COST-MODEL-IMPL` — implement `NT8CrudeOilV1CostModel` + `NT8GoldV1CostModel` per the ADR-0017 cost-modeling-realism convention.

BLOCKING-BEFORE-H060-PRE-REG:
- `P1-INSTRUMENTS-YAML-METALS-ENERGY-EXTEND` — add CL, MCL, GC, MGC entries with full §7 metadata.

Operator-action (sequenced):
- `P1-DATABENTO-METALS-ENERGY-COST-DOSSIER` — operator runs `metadata.get_cost` for the target symbol-window combo and records the binding figure.
- `P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE` — operator authorizes the Databento spend per the binding figure; gates the actual API call.

Non-blocking:
- `P1-ADR-0001-METALS-ENERGY-CAPACITY-CALIBRATE` — empirical capacity calibration post-paper-trade.
- `P1-METALS-ENERGY-COST-EMPIRICAL-CALIBRATION` — post-paper-trade fill-data-based cost-model calibration per the ADR-0017 cost-empirical convention.
- `P1-ADR-0023-V2-TIER-2-EXPANSION` — Tier-2 contract expansion (NG, RB, HG, SI, etc.) after Tier-1 produces first KPI report card.
- `P1-ADR-0023-CALENDAR-SPREADS-V2` — calendar-spread universe extension (open question §Consequences).
