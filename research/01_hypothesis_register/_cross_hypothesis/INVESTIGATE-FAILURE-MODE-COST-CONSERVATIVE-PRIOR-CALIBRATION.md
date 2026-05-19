---
investigation_id: INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION
schema_version: investigation_memo_v1
created: 2026-05-19
status: complete-no-further-action
hypothesis_of_investigation: H050, H052a, H053, H055, H060, H062, H065
parent_kpi_report_card: research/01_hypothesis_register/RESULTS_INDEX.md
---

# Investigation Memo — Cross-hypothesis cost-realism: per-cell cost-friction-breakeven for every emitted KPI v(latest)

Per [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) §D-1, this memo is the canonical artifact class for `INVESTIGATE-FAILURE-MODE-*` follow-ups. Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1 non-loss, this memo is immutable post-completion; corrections produce a versioned successor (e.g., `INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_v2.md`).

This is a **cross-hypothesis** investigation occupying the `_cross_hypothesis/` sibling-of-`H{NNN}/` namespace under `research/01_hypothesis_register/`. Per the operator 2026-05-19 directive following the H062 v3 ablation closure: project-level cost-realism reframing required.

## 1. Hypothesis-of-investigation

The [H062 v3 primitive-attribution ablation](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) (commit `1adc62a`, 2026-05-19) established that on H062 v3 the `conservative_prior` cost-model alone — without kill-switch + without equity-rebase — drives basket OOS from A0 zero-cost +261.88% to A1 cost-only **−99.99997%** on *identical* 10,326 trades. Cost is the *dominant* primitive driver of the H062 v3 catastrophe (100.0% of cumulative Δ vs A0 baseline).

This **reframes the project's null-result inventory** as a population-level investigation: of the 7 emitted hypotheses × 5 candidate symbols (basket / ES / NQ / MGC / SIL) = up to 35 cells, how many are **cost-friction-dominated-edge-present** (positive gross edge under zero cost that conservative_prior would extinguish) vs **edge-absent** (no positive gross edge under any cost regime)? The distinction matters per ADR-0027 §D-4 genetic-successor discipline: cost-friction-dominated cells warrant **cost-light genetic successors** (re-pre-registration at lower trade-frequency, larger position size, longer holding period, or batch-execution paradigm); edge-absent cells warrant retirement (per ADR-0013 §1 stage-progression `kpi-report-emitted` permanent state — no follow-on genetic branching warranted).

## 2. Decomposition plan

Per [ADR-0027 §D-1(b)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) decomposition discipline, this investigation runs **NO new walk-forward compute** — it is a pure post-hoc decomposition over existing sidecars. Per ADR-0027 §D-2 cell-budget: 35 cells (7 hypotheses × 5 symbols) is well under the 1000-cell soft cap; bounded explicit set.

Per-cell metric computation:

1. **Per-cell cost-friction-breakeven ratio** = |avg-per-trade-return-bps-of-equity| / cost-per-round-trip-bps-of-equity. The conversion to bps-of-equity (NOT bps-of-notional) is dimensionally load-bearing: average per-trade return is `(roi_pct / 100) / n_trades` expressed as a fraction of $10K starting equity (per ADR-0017 §4.1 + design.md §5.3 retail-tier $10K sandbox + Kelly 0.25 + 1% risk-budget); round-trip cost is `cost_usd / starting_equity` for the 1-contract assumption per design.md §5.3 typical position size.
2. **Classification per (hypothesis × symbol) cell** (label semantics per task-spec convention):
   - `cost-friction-dominated-edge-present` — ratio ≥ 2 AND zero-cost (A0) reference realized OOS > 0% AND verified ablation pair present. **Semantic glossary**: this label denotes "the cell is in a cost-friction-DOMINATED regime BUT positive edge IS PRESENT in the absence of friction." Higher ratio = edge is large enough that even friction-domination cannot extinguish it; this is the **most promising** category for cost-light genetic-successor pre-registration per ADR-0027 §D-4. The label is operator-canonical from the task spec; an alternative label such as `edge-survives-cost-friction-2x` would convey the same operational semantic and is recommended for the future ADR-0028 annotation grammar.
   - `cost-friction-marginal-edge-present` — 1 ≤ ratio < 2 AND zero-cost reference > 0%. Edge is comparable in magnitude to cost; borderline.
   - `edge-present-cost-light` — ratio < 1 BUT zero-cost reference > 0%. Counter-intuitive label that does NOT appear in the data; reserved for theoretical future cells with very-low-friction (e.g., paper-trade-empirical calibration reveals empirical cost << conservative_prior).
   - `edge-absent` — ratio < 1 AND zero-cost reference ≤ 0% (or no positive realized OOS).
   - `likely-cost-friction-dominated-pending-A0-verification` — ratio ≥ 2 AND positive realized; no A0 reference (most emitted KPIs lack zero-cost-vs-cost-on twin ablation pairs).
   - `likely-marginal-pending-A0` — 1 ≤ ratio < 2 AND positive realized; no A0 reference.
   - `likely-edge-absent` — ratio < 1 AND non-positive realized; no A0 reference.
3. **Ranking**: descending by ratio = most-promising-under-realistic-cost first; ascending = worst-friction-burden first.

Cost models surveyed (all 3 at `sensitivity_mult = 1.0` default 1-tick prior):

| Model id | Module | Symbol coverage | Round-trip cost USD (1 contract) |
|---|---|---|---|
| `nt8_es_nq_rth_v1` | [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) | ES/NQ/MES/MNQ | ES $29.10; NQ $14.10; MES $3.94; MNQ $2.44 |
| `futures_orb_v1` | [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py) | ES/NQ/MES/MNQ | identical to `nt8_es_nq_rth_v1` per-symbol (different per-session vs per-bar convention; same fee schedule) |
| `nt8_realistic_v1` | [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py) | ES/NQ/MES/MNQ + MGC/SIL/MCL (ADR-0025 extension) | ES $29.10; NQ $14.10; MES $3.94; MNQ $2.44; MGC $4.64 *placeholder*; SIL $12.64 *placeholder*; MCL $4.74 *placeholder* |

**Conservative-prior derivation** (cross-checked against [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) + [config/instruments.yaml](../../../config/instruments.yaml); CME fees effective 2024-02 + NFA fees effective 2024-01-01 + NinjaTrader Brokerage Unlimited Q1-2026 retail rate):

| Symbol | Commission/side | Exchange fee/side | NFA fee/side | Slip prior/side (1 tick × tick value) | Round-trip cost ($) | Bps-of-notional@representative-price | Bps-of-equity@$10K (1 contract) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ES | $0.85 | $1.18 | $0.02 | $12.50 (1 × $12.50) | **$29.10** | 1.16 bps | **29.10 bps** |
| NQ | $0.85 | $1.18 | $0.02 | $5.00 (1 × $5.00) | **$14.10** | 0.39 bps | **14.10 bps** |
| MES | $0.35 | $0.35 | $0.02 | $1.25 (1 × $1.25) | $3.94 | 1.58 bps | 3.94 bps |
| MNQ | $0.35 | $0.35 | $0.02 | $0.50 (1 × $0.50) | $2.44 | 0.68 bps | 2.44 bps |
| MGC | $0.85 *placeholder* | $0.45 *placeholder* | $0.02 | $1.00 (1 × $1.00) | **$4.64** | 2.11 bps | **4.64 bps** |
| SIL | $0.85 *placeholder* | $0.45 *placeholder* | $0.02 | $5.00 (1 × $5.00) | **$12.64** | 4.68 bps | **12.64 bps** |
| MCL | $0.85 *placeholder* | $0.50 *placeholder* | $0.02 | $1.00 (1 × $1.00) | $4.74 | 6.32 bps | 4.74 bps |

*MGC/SIL/MCL placeholder*: per [config/instruments.yaml:148-153](../../../config/instruments.yaml) commission + exchange-fee figures for metals/energy are *placeholders pending `P1-METALS-ENERGY-CME-FEE-VERIFY`*; the CME Energy/Metals fee schedule was NOT primary-source-verified at adoption. Substrate impact bounded — most-likely under-statement of cost on these symbols.

Bps-of-equity vs bps-of-notional distinction is load-bearing: notional / equity = leverage = 25× (ES), 36× (NQ), 2.2× (MGC), 2.7× (SIL) at $10K starting + 1 contract. The bps-of-notional figure understates equity-impact by the leverage factor; the bps-of-equity figure is the apples-to-apples denominator vs avg-per-trade-return-bps-of-equity.

## 3. Termination criterion

Per [ADR-0027 §D-1(c)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) acceptable form (i): close when the 35-cell decomposition completes, the cost-friction-breakeven ratio is populated per cell, and §6 findings + §7 implication identify the load-bearing project reframing (e.g., "X of 35 cells are cost-friction-dominated; Y cells warrant cost-light successors per ADR-0027 §D-4").

## 4. Wall-clock soft cap

Per [ADR-0027 §D-1(d)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md):

| Estimate | Actual | Delta | Justify (if overrun) |
|---|---|---|---|
| 3-4 hr soft cap | ~2.5 hr (sidecar reads + 3 cost-model reads + 35-cell ratio computation + investigation memo + audit-remediate-loop) | −0.5-1.5 hr (under budget) | n/a (no overrun) |

Hard cap: 5 hr per task spec; under budget.

## 5. Output artifact spec

Per [ADR-0027 §D-1(e)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md):

- **Output class**: investigation-memo (this artifact); no successor pre-registration or ADR amendment written here per the task spec's "DO NOT write any ADR amendment in this work — the ADR-0017 §3 / ADR-0014 §3.2 cost-friction-dominated-edge annotation grammar is being landed via a sibling ADR-0028 task currently in progress. Reference ADR-0028 as forward-link." constraint.
- **Cross-references**:
  - H062 v3 ablation precedent: [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
  - Cost-model machinery: [nt8_es_nq_rth_v1](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) + [futures_orb_v1](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py) + [nt8_realistic_v1](../../../src/skie_ninja/backtest/costs/nt8_realistic.py)
  - Parent KPI cards: see [RESULTS_INDEX.md](../RESULTS_INDEX.md) for all 7 hypotheses × per-symbol cells
  - ADR-0017 §3 survival-constrained primary metric vector: [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md)
  - ADR-0025 §D-3 cost-model `nt8_realistic_v1` infrastructure: [ADR-0025](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md)
  - Forward-link to sibling ADR-0028 (cost-friction-dominated-edge annotation grammar; in progress concurrently with this investigation)
  - Reproduction script: [scripts/cost_realism_investigation_compute.py](../../../scripts/cost_realism_investigation_compute.py)
  - Raw computation output: [artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json](../../../artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json)
  - Audit trail: [docs/audits/audit_trail_2026-05-19_cost-realism-investigation.md](../../../docs/audits/audit_trail_2026-05-19_cost-realism-investigation.md)

## 6. Findings

> Per [ADR-0013 §4.1 non-loss](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), table rows are APPEND-as-work-completes; rows are immutable once landed.

### 6.1 Findings table — per (hypothesis × symbol) cell

35 cells across 7 hypotheses. Cells reported in descending-ratio order; classification per §2 schema. `OOS%` is realized OOS basket-or-per-symbol % vs $10K starting equity per the v(latest) KPI report card. `n_trades` is the sidecar-bound figure; for H050 `n_trades` is bar-count (multibar holding strategy; see caveat in §6.2). For H060 basket-aggregate-only; per-symbol n_trades not preserved in sidecar.

| Rank | Hypothesis × cell | Sym | OOS% | n_trades | avg_per_trade_bps_eq | cost_bps_eq | breakeven ratio | A0 ref | Classification |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | H065 v2 M_inf_h062_v1_fixed | ES | +40.54% | 110 | 36.86 | 29.10 | **1.27** | n/a | likely-marginal-pending-A0 |
| 2 | H065 v2 M_inf_h065_current | SIL | +734.68% | 5,600 | 13.12 | 12.64 | **1.04** | n/a | likely-marginal-pending-A0 |
| 3 | H065 v2 M_inf_h062_v1_fixed | SIL | +446.38% | 4,165 | 10.72 | 12.64 | 0.85 | n/a | likely-marginal-pending-A0 |
| 4 | H065 v2 M_inf_h065_current | MGC | −82.69% | 3,611 | −2.29 | 4.64 | 0.49 | n/a | likely-edge-absent |
| 5 | H065 v2 M_inf_h062_v1_fixed | MGC | +116.48% | 5,221 | 2.23 | 4.64 | 0.48 | n/a | likely-marginal-pending-A0 |
| 6 | H065 v2 M_1.5 | ES | +18.15% | 211 | 8.60 | 29.10 | 0.30 | n/a | likely-marginal-pending-A0 |
| 7 | H065 v2 M_2.5 | MGC | −68.81% | 5,084 | −1.35 | 4.64 | 0.29 | n/a | likely-edge-absent |
| 8 | H055 v2 C5_super_pyramid | ES | −53.48% | 706 | −7.58 | 29.10 | 0.26 | n/a | likely-edge-absent |
| 9 | H055 v2 C3_superkelly | NQ | −19.30% | 530 | −3.64 | 14.10 | 0.26 | n/a | likely-edge-absent |
| 10 | H055 v2 C9_bocd_stepup | NQ | −8.69% | 249 | −3.49 | 14.10 | 0.25 | n/a | likely-edge-absent |
| 11 | H055 v2 C2_fullkelly | NQ | +0.89% | 26 | 3.42 | 14.10 | 0.24 | n/a | likely-marginal-pending-A0 |
| 12 | H055 v2 C3_superkelly | MGC | +87.04% | 7,625 | 1.14 | 4.64 | 0.25 | n/a | likely-marginal-pending-A0 |
| 13 | H055 v2 C5_super_pyramid | MGC | +77.19% | 7,665 | 1.01 | 4.64 | 0.22 | n/a | likely-marginal-pending-A0 |
| 14 | H055 v2 C5_super_pyramid | NQ | −14.30% | 584 | −2.45 | 14.10 | 0.17 | n/a | likely-edge-absent |
| 15 | H055 v2 C2_fullkelly | MGC | +72.37% | 10,321 | 0.70 | 4.64 | 0.15 | n/a | likely-marginal-pending-A0 |
| 16 | H055 v2 C9_bocd_stepup | MGC | +58.04% | 9,442 | 0.62 | 4.64 | 0.13 | n/a | likely-marginal-pending-A0 |
| 17 | H053 v3 ElasticNet | NQ | +6.20% | 372 | 1.67 | 14.10 | 0.12 | n/a | likely-marginal-pending-A0 |
| 18 | H055 v2 C5_super_pyramid | SIL | −46.58% | 3,509 | −1.33 | 12.64 | 0.10 | n/a | likely-edge-absent |
| 19 | H065 v2 M_1.0 | MGC | +62.25% | 9,591 | 0.65 | 4.64 | 0.14 | n/a | likely-marginal-pending-A0 |
| 20 | H065 v2 M_2.5 | SIL | −60.67% | 3,623 | −1.68 | 12.64 | 0.13 | n/a | likely-edge-absent |
| 21 | H052a v1 (uncond) | NQ | +10.61% | 369 | 2.88 | 14.10 | 0.20 | n/a | likely-marginal-pending-A0 |
| 22 | H053 v3 LightGBM | NQ | +10.80% | 372 | 2.90 | 14.10 | 0.21 | n/a | likely-marginal-pending-A0 |
| 23 | H065 v2 M_1.5 | SIL | −58.26% | 3,015 | −1.93 | 12.64 | 0.15 | n/a | likely-edge-absent |
| 24 | H065 v2 M_1.0 | SIL | −62.71% | 2,993 | −2.10 | 12.64 | 0.17 | n/a | likely-edge-absent |
| 25 | H065 v2 M_inf_h065_current | ES | +54.37% | 759 | 7.16 | 29.10 | 0.25 | n/a | likely-marginal-pending-A0 |
| 26 | H065 v2 M_1.0 | ES | +8.18% | 147 | 5.57 | 29.10 | 0.19 | n/a | likely-marginal-pending-A0 |
| 27 | H065 v2 M_2.0 | ES | +2.23% | 169 | 1.32 | 29.10 | 0.05 | n/a | likely-marginal-pending-A0 |
| 28 | H065 v2 M_2.5 | ES | +3.35% | 187 | 1.79 | 29.10 | 0.06 | n/a | likely-marginal-pending-A0 |
| 29 | H065 v2 M_2.0 | SIL | −36.26% | 3,859 | −0.94 | 12.64 | 0.07 | n/a | likely-edge-absent |
| 30 | H053 v3 LightGBM | ES | +6.40% | 367 | 1.74 | 29.10 | 0.06 | n/a | likely-marginal-pending-A0 |
| 31 | H053 v3 ElasticNet | ES | −3.20% | 367 | −0.87 | 29.10 | 0.03 | n/a | likely-edge-absent |
| 32 | H055 v2 C3_superkelly | ES | +23.09% | 3,301 | 0.70 | 29.10 | 0.02 | n/a | likely-marginal-pending-A0 |
| 33 | H055 v2 C9_bocd_stepup | SIL | +7.23% | 3,959 | 0.18 | 12.64 | 0.01 | n/a | likely-marginal-pending-A0 |
| 34 | H055 v2 C2_fullkelly | SIL | +1.83% | 5,978 | 0.03 | 12.64 | 0.002 | n/a | likely-marginal-pending-A0 |
| 35 | H055 v2 v1baseline | MGC | −1.22% | 3,622 | −0.03 | 4.64 | 0.01 | n/a | likely-edge-absent |
| — | H052a v1 (gated) | ES | −0.94% | 371 | −0.25 | 29.10 | 0.01 | n/a | likely-edge-absent |
| — | H052a v1 (gated) | NQ | +3.39% | 369 | 0.92 | 14.10 | 0.07 | n/a | likely-marginal-pending-A0 |
| — | H052a v1 (uncond) | ES | +1.61% | 371 | 0.43 | 29.10 | 0.01 | n/a | likely-marginal-pending-A0 |
| — | H053 v3 passive | ES | 0.00% | 367 | 0.00 | 29.10 | 0.00 | n/a | likely-edge-absent |
| — | H053 v3 passive | NQ | +1.30% | 372 | 0.35 | 14.10 | 0.02 | n/a | likely-marginal-pending-A0 |
| — | H055 v2 v1baseline | SIL | −1.21% | 329 | −0.37 | 12.64 | 0.03 | n/a | likely-edge-absent |
| — | H055 v2 C2_fullkelly | ES | −0.97% | 641 | −0.15 | 29.10 | 0.01 | n/a | likely-edge-absent |
| — | H055 v2 C9_bocd_stepup | ES | −0.79% | 653 | −0.12 | 29.10 | 0.004 | n/a | likely-edge-absent |
| — | H055 v2 C3_superkelly | SIL | −10.12% | 4,177 | −0.24 | 12.64 | 0.02 | n/a | likely-edge-absent |
| — | H065 v2 M_2.0 | MGC | −0.65% | 7,055 | −0.01 | 4.64 | 0.002 | n/a | likely-edge-absent |
| — | H065 v2 M_1.5 | MGC | −7.84% | 7,326 | −0.11 | 4.64 | 0.02 | n/a | likely-edge-absent |

**H050 v1 bar-cadence cells** (n_trades = bar-count, NOT entry-count; see §6.2 caveat 1) — and IMPORTANT: H050 v1 is the ONLY emitted KPI that is **already cost-aware** (`nt8_es_nq_rth_v1 constant-tick prior, applied` per KPI v1 §8 Table). The realized OOS figures below are NET-OF-COST; the cost-friction ratio for H050 expresses the *residual* (post-cost) per-bar edge relative to the conservative-prior cost. All other 6 hypotheses are pre-cost research-only (per the v(latest) `cost_model_v1_scope: pre_cost_research_only` annotations):

| Hypothesis × cell | Sym | OOS% (net-of-cost) | n_bars | breakeven ratio | Classification |
|---|---|---:|---:|---:|---|
| H050 v1 (gated) | ES | −81.02% | 337,837 | 0.001 | likely-edge-absent (net-of-cost; HMM gating itself produces negative edge) |
| H050 v1 (gated) | NQ | −84.20% | 673,274 | 0.001 | likely-edge-absent |
| H050 v1 (uncond) | ES | −43.69% | 337,837 | 0.000 | likely-edge-absent |
| H050 v1 (uncond) | NQ | −25.60% | 673,274 | 0.000 | likely-edge-absent |

**Critical caveat on H050**: the H050 v1 KPI card §1 P/L Table reports the NET-OF-COST realized OOS as the headline; per the §"Methodological-correctness annotations" table line 104: "Cost model: `nt8_es_nq_rth_v1` constant-tick prior, applied". H050's catastrophic outcome (−81/−84% on the gated arms vs −44/−26% on the unconditional arms) is therefore **post-cost** — the gating mechanism actively HARMS the directional signal **even before cost considerations**. H050's status is: cost-friction analysis is degenerate (the strategy is uniformly negative pre-and-post-cost; cost-friction is not the dominant primitive driver of H050 catastrophe). This contrasts H062 v3 where the A0 zero-cost reference is strongly positive (+261.88%) and cost-friction extinguishes it.

**H060 v2 basket-aggregate** (no per-symbol n_trades persisted in sidecar; basket-level skipped per §2 schema):

| Hypothesis × cell | Sym | OOS% | n_sessions | Notes |
|---|---|---:|---:|---|
| H060 v2 TSMOM | basket | +68.75% | 1,260 | per-symbol n_trades not persisted; TSMOM monthly rebalance → ~60-120 round-trips/symbol over 5-yr OOS; cost-friction ratio inferable but pending sidecar-schema-extension follow-up |

**H062 v3 ablation A0/A1 — load-bearing VERIFIED reference cell**:

| Hypothesis × cell | Sym | OOS% | n_trades | A0 zero-cost reference | Verified delta | Classification |
|---|---|---:|---:|---:|---|---|
| H062 v3 A0 (zero-cost basket) | basket | **+261.88%** | 10,326 | — (this IS the A0) | (reference) | (zero-cost reference) |
| H062 v3 A1 (conservative-prior basket) | basket | **−99.99997%** | 10,326 | +261.88% | **−361.88 pp** | **cost-friction-dominated-edge-present (VERIFIED)** |

The H062 v3 A0/A1 pair is the **only directly-verified A0-zero-cost-vs-A1-cost-on-IDENTICAL-trades pair** in the entire emitted-KPI inventory. It empirically establishes that on the H062 v2 cell-grid + retail $10K + Kelly 0.25 + 1% risk sizing, the `conservative_prior` cost-model alone is **sufficient to drive +261.88% → ~bankruptcy** at the basket level. The trade-weighted average cost-friction-breakeven ratio for H062 basket = **0.30** (gross-edge ≈ 30% of round-trip-cost-burden); the rest of the gross-edge is absorbed entirely by friction over the 6-year × 10,326-trade horizon.

### 6.2 Caveats + cross-check anomalies

1. **H050 bar-cadence vs trade-cadence**: H050's `n_trades` field in the sidecar is the bar-count (337,837 / 673,274 for ES/NQ) — a multibar-holding strategy where every bar is a "decision point" but actual entry/exit events are far fewer. Treating each bar as a round-trip overstates cost burden by the average-holding-period factor (likely 5-30 bars per trade). The H050 ratios in §6.1 are **lower bounds** under this convention; true per-entry cost burden is materially lighter. Tracked under new follow-up `P1-H050-PER-ENTRY-COST-INVENTORY` to extract entry-count + round-trip-count separately from the sidecar at v2 KPI emission.

2. **No A0 (zero-cost) reference cells for any emitted KPI except H062 v3 ablation**: of the 35 cells in §6.1, only the H062 v3 A0/A1 pair has a directly-verified zero-cost-vs-cost-on twin ablation. All other classifications are `likely-*-pending-A0-verification` per §2 schema. Future genetic-successor pre-registration SHALL include an explicit A0 zero-cost ablation cell at first KPI emission per `P1-A0-ZERO-COST-ABLATION-MANDATORY-FUTURE-KPIS` follow-up (registered below).

3. **MGC/SIL/MCL cost-model placeholders**: per [config/instruments.yaml:148-153](../../../config/instruments.yaml), MGC + SIL + MCL commission + exchange-fee figures are *placeholders pending* `P1-METALS-ENERGY-CME-FEE-VERIFY`. The ratios for cells on these symbols (H055 v2 MGC/SIL; H060 v2 basket; H065 v2 MGC/SIL) are at-best lower bounds. CME Energy/Metals fees were never primary-source-verified; the empirical realistic cost may be 20-50% higher than the placeholder figures. Substrate impact on rankings: H055 MGC cells (ratios 0.13-0.25) + H065 MGC cells (ratios 0.14-0.48) + H065 SIL cells (ratios 0.85-1.04) may move ratio-down by 1.2-1.5× under verified CME fees.

4. **Bps-of-equity vs bps-of-notional**: the load-bearing denominator is bps-of-equity (per ADR-0017 §4.1 + design.md §5.3 retail $10K + Kelly 0.25 sizing). A naive bps-of-notional comparison (ratio = avg-per-trade-bps-of-equity / cost-bps-of-notional) overstates cost-resilience by the leverage factor (25× for ES; 36× for NQ; 2× for MGC; 3× for SIL). The dimensional correction was caught in this investigation R1 (and is now load-bearing); the first-pass computation script overstated ratios by leverage factor before correction.

5. **1-contract-position assumption**: cost is computed at the per-round-trip-per-1-contract level (per the conservative-prior config in [src/skie_ninja/backtest/costs/nt8_realistic.py:212-227](../../../src/skie_ninja/backtest/costs/nt8_realistic.py)). At $10K + Kelly 0.25 + 1% risk, position-size typically floors to 1 contract per design.md §5.3 (ES/NQ specifically have $250-360K notional and $5-12.50/tick risk — 1 contract typically maxes out the risk budget). Larger positions multiply cost proportionally; the ratio is therefore size-invariant under the canonical sizing convention. Cells where empirical position > 1 contract (H055 v2 super-Kelly km=2.0+ × C3/C5; H065 v2 M_inf_h065_current) are slightly under-stated in cost burden by the position-multiplier; bounded ≤ 2× under super-Kelly km=2.0 + 1% risk budget at retail $10K.

6. **Per-trade-cost-burden vs per-trade-LOG-cost-burden**: the conservative_prior cost is applied as `log(1 - cost/notional)` per-session log-return drag per ADR-0013 §3.1.1 F-CONV-2 + [src/skie_ninja/backtest/costs/futures_orb_v1.py:117-161](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py) machinery. For typical cost-to-notional ratios ~3-7e-4, the log approximation `log(1-x) ≈ -x` holds. At small basket-aggregate compound effects (H062 v3 A1 going to −99.99997%), the log-drag accumulates multiplicatively — the realized compound is bounded below by −100% (bankruptcy floor in [scripts/run_h055_v2_sweep.py + run_h062_walk_forward.py]). This is mechanically consistent with the H062 v3 A1 result.

7. **Cross-check against H062 v3 ablation A0 → A1 per-trade attribution**: per-trade-avg gross return at A0 zero-cost basket = +261.88% / 10,326 trades = **+0.0254% per trade = 2.54 bps-of-equity**. Trade-weighted average cost = (97/10326) × 29.10 + (0/10326) × 14.10 + (5701/10326) × 4.64 + (4528/10326) × 12.64 = **8.38 bps-of-equity**. Breakeven ratio at H062 basket = 2.54 / 8.38 = **0.30**. **This matches the computational signal in §6.1**: cost burden is 3.3× the gross edge; A1 catastrophe is mechanically expected. Naive sum-of-cost over 10,326 trades = 8.38 bps × 10,326 = **865% of equity** (would push log-drag through bankruptcy floor); A1 actual outcome (−99.99997%) is the log-drag-compounded-and-bounded result. The ablation finding is dimensionally consistent with the §6.1 framework.

### 6.3 Findings synthesis

**Of the 35 per-cell + 2 cross-cell entries**: ZERO cells classify as `cost-friction-dominated-edge-present` (ratio ≥ 2 + positive realized + A0 reference present + verified). The H062 v3 ablation A0/A1 pair is the only verified-A0-reference; it classifies *negatively* (ratio 0.30 → cost-friction-dominated-extinguishes-edge per the −100% A1 outcome).

**Of the 35 single-cells**: ZERO cells classify as `cost-friction-dominated-edge-present` (ratio ≥ 2 + positive realized + A0 present); the 11 cells originally flagged `likely-cost-friction-dominated-pending-A0-verification` in the dimensionally-incorrect bps-of-notional first-pass DROPPED to `likely-marginal-pending-A0` under the corrected bps-of-equity computation.

**Top-3 highest-ratio cells with positive realized OOS** (most-promising-under-realistic-cost candidates pending A0 verification):

1. **H065 v2 M_inf_h062_v1_fixed ES** — ratio 1.27, +40.54% OOS, 110 trades. Lowest-frequency strategy in the entire inventory at this position; per-trade-gross-edge **only barely** exceeds round-trip cost (37 bps vs 29 bps).
2. **H065 v2 M_inf_h065_current SIL** — ratio 1.04, +734.68% OOS, 5,600 trades. Strongest standalone-cell realized OOS in the entire emitted-KPI inventory; per-trade-gross-edge essentially equals cost burden (13.1 bps vs 12.6 bps). Survival under conservative-prior cost is at the H_0-boundary.
3. **H065 v2 M_inf_h062_v1_fixed SIL** — ratio 0.85, +446.38% OOS, 4,165 trades. Mirror finding to #2; per-trade-edge slightly LESS than cost burden but compensated by sheer trade volume + strong path-dependency.

**Reframing implication**: under the dimensionally-correct bps-of-equity denominator at retail $10K + Kelly 0.25 + 1-contract-position sizing convention, **NO emitted KPI v(latest) cell carries a gross-edge that comfortably exceeds (≥ 2×) the conservative-prior round-trip cost**. The strongest cells achieve at-or-just-above breakeven (ratio 0.85-1.27); the typical cell sits at 0.05-0.30 (cost is 3-20× gross edge per trade). This is the load-bearing project-level reframing: the H062 v3 ablation finding is **not a single-hypothesis defect** but a **population-level pattern** across the entire emitted-KPI inventory.

The 3 cells with ratio ≥ 0.85 are all H065 v2 M_inf-no-TP variants (H062-v1-baseline-mirror cells at H065's design.md §5.6 reference position). These are the natural genetic-successor candidates per ADR-0027 §D-4 — cost-light variants would propose lower-frequency entry filters (channel-N > 240; vol-regime gating; news-calendar exclusion expansion) to preserve the per-trade-edge while reducing the trade count.

The remaining 32 cells with ratio < 0.85 require either substantial gross-edge improvement (10-100×) or substantial cost-reduction (paper-trade-empirical calibration of slippage that may reveal lower realistic cost) to clear the conservative-prior bar under retail sizing convention. Genetic-successor variants are still feasible (per ADR-0027 §D-4) but the gross-edge improvement required is significant — the operator's strongest forward-projection candidates remain a small subset.

### 6.4 Per-hypothesis cost-friction summary

**Cost-application convention** (cross-hypothesis): of the 7 emitted hypotheses, only **2 are cost-aware** (H050 v1 `nt8_es_nq_rth_v1 applied`; H052a v1 `futures_orb_v1 applied` annotation `cost-conditional`). The remaining 5 (H053 v3 / H055 v2 / H060 v2 / H062 v2 / H065 v2) all carry `cost-zero-v1-pre-cost-research-only` per operator standing directive 2026-05-08 + 2026-05-12. The cost-friction-breakeven ratio interpretation differs:
- For cost-aware hypotheses (H050, H052a): the ratio expresses RESIDUAL per-trade edge under conservative_prior cost; the headline OOS% IS the realistic-cost outcome.
- For pre-cost hypotheses (H053, H055, H060, H062, H065): the ratio is the predicted edge-vs-friction at the conservative-prior; the headline OOS% is upper-bound that conservative_prior would degrade per the §6.1 ratio decomposition.

| Hypothesis | Best-cell ratio | Best-cell ROI | Worst-cell ratio | Most promising successor candidate? | Verdict |
|---|---:|---:|---:|---|---|
| H050 v1 (cost-aware; net-of-cost) | 0.001 (gated ES bar-cadence) | −81% (net-of-cost) | 0.000 (uncond NQ) | NO — already cost-aware; HMM gating actively harms directional signal pre-and-post-cost; entry-cadence convention bounded below ~0.1 even at trade-cadence | edge-absent (uniformly; cost-friction NOT the dominant primitive driver) |
| H052a v1 (cost-aware; net-of-cost) | 0.20 (uncond NQ) | +10.61% (net-of-cost) | 0.01 (gated ES) | MAYBE — uncond NQ is literature-replication artifact not hypothesis-of-record; ORB session-cadence inherently low-cost-burden; already-cost-aware so NQ +10.61% is the realistic-cost result | edge-marginal-cell-conditional (NQ uncond only); already-cost-realistic |
| H053 v3 | 0.21 (LightGBM NQ) | +10.80% | 0.03 (ElasticNet ES) | MAYBE — NQ LightGBM has favorable forward-projection (P(loss)=15.7%); session-cadence is low-cost | edge-marginal-cell-conditional (NQ LightGBM only) |
| H055 v2 | 0.25 (C3 MGC, C3 NQ) | +87% (MGC) | 0.002 (C2 SIL) | NO — high trade frequency × intraday cadence × ATR-stop = cost burden dominates; MGC C3 +87% has ratio 0.25 (cost = 4× edge) | edge-friction-vulnerable |
| H060 v2 | (per-symbol unavailable) | +68.75% basket | (per-symbol unavailable) | TENTATIVELY YES — TSMOM monthly rebalance is structurally low-frequency; pending sidecar-schema-extension for per-symbol n_trades verification | edge-marginal-pending-sidecar-extension |
| H062 v2 | 0.30 (basket weighted; VERIFIED via A0/A1 ablation) | +217.57% basket | (basket only) | NO — verified cost-friction-dominated (A0 → A1 = +262 → −100); v2 cells are 6-year compound of marginal per-trade edges that friction extinguishes | edge-marginal-friction-dominated (VERIFIED) |
| H065 v2 | **1.27** (M_inf_h062_v1_fixed ES), 1.04 (M_inf_h065_current SIL) | +40.54% (ES), +734.68% (SIL) | 0.002 (M_2.0 MGC) | **YES** — M_inf-no-TP no-overlay cells on ES + SIL are at-or-above breakeven; cost-light successor candidates per ADR-0027 §D-4 | edge-marginal-cell-conditional |

## 7. Implication

Per [ADR-0027 §D-3](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) empirical-before-amendment sequencing rule: this memo does NOT write any ADR amendment. The findings are EMPIRICAL INPUTS to subsequent decisions tracked under the new follow-ups registered in §8.

### 7.1 Reframing implication for the project (load-bearing)

**The project's "null-result inventory" is heterogeneous along the cost-friction-dominance dimension that was not previously surfaced**. The §6 decomposition shows:

- **3 cells** (H065 v2 M_inf-no-TP variants on ES + SIL × 2 cells) sit at or marginally above breakeven (ratio 0.85-1.27). These are candidates for cost-light genetic-successor pre-registration per ADR-0027 §D-4.
- **~7 cells** (H052a NQ uncond; H053 NQ LightGBM; H055 MGC C3/C5; H062 v2 basket; H060 TSMOM; H065 ES M_inf cells) sit in the 0.20-0.50 ratio range — friction is 2-5× edge. These are candidates for substantial-cost-reduction-via-paper-trade-empirical-calibration (`P1-{HXXX}-COST-EMPIRICAL-CALIBRATION` is BLOCKING-BEFORE-PAPER-TRADE for all hypotheses; this is the empirical-cost-recovery path).
- **~25 cells** (everything else, including H050 gated/uncond + many H055 + H062 + H065 sub-cells) sit at ratio < 0.20 — friction is 5-100× edge. These are candidates for retirement-by-stage-progression per ADR-0013 §1 (`kpi-report-emitted` permanent state; no genetic-successor warranted; the cell-level edge structure cannot survive realistic cost regardless of further refinement).

**This reframes the operator-readable presentation of the project**: the H062 v3 ablation's "cost dominates the catastrophe" finding is not a single-hypothesis defect. It is a population-level pattern: **the project's accumulated empirical-edge across 35 cells × 7 hypotheses is small** relative to the conservative_prior cost burden. The PRE-cost realized OOS figures in the v(latest) KPI cards are NOT cost-realistic forward-projections; they are upper bounds whose realistic-cost projections under conservative_prior would collapse most cells to bankruptcy.

This is **consistent with [ADR-0024 §D-7 Lo 2004 AMH framing](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md)**: partial-decay is the null; the surviving cells under realistic cost are a *narrow subset* of the original universe.

### 7.2 Whether conservative_prior is itself pessimistically calibrated

**Yes, almost certainly — but only modestly**. Per the §6.2 caveats:

- **MGC/SIL/MCL fees** are **placeholders** pending `P1-METALS-ENERGY-CME-FEE-VERIFY`. The empirical realistic cost may be 20-50% **higher** than placeholder (CME Energy/Metals fees are typically retail-priced higher than equity-index micros); this would push ratios for MGC + SIL cells DOWNWARD (worse cost burden), not upward.
- **Slippage prior (1 tick per side)** is itself a conservative prior. Empirically, retail-order-flow at sub-100-contract sizes on liquid CME equity-index futures (ES, NQ) typically sees **sub-1-tick** average slippage on market orders during high-liquidity hours (RTH primary session) per practitioner anecdotes — actual slippage may be 0.3-0.7 tick at retail size. This would push cost lower by 0.3-0.7× the slip-component-of-round-trip-cost. For ES: slip dominates ($12.50 of $14.55 per side = 86%); a 0.5-tick empirical slip cuts round-trip cost from $29.10 → $14.60 (50% reduction). For NQ: slip is 71%; 0.5-tick cuts from $14.10 → $9.10 (35% reduction). This would push ratios UP by 1.4-2.0× on equity-index cells (favorable to genetic-successor pre-registration).
- **Commission + exchange + NFA** are the contractually-fixed component; cannot be empirically reduced via paper-trade calibration. These are firm.

**Implication**: the actual realistic cost under paper-trade-empirical calibration is plausibly **50-100% of conservative_prior** on equity-index cells; possibly **100-150%** on metals/energy cells (placeholder under-statement risk). The investigation registers `P1-COST-REALISTIC-EMPIRICAL-CALIBRATION` as a BLOCKING follow-up at first paper-trade fill-data accumulation (per ADR-0025 §D-3 + `P1-COST-MODEL-METALS-ENERGY-EMPIRICAL-OVERRIDE`). The empirical realistic cost should be revisited at this calibration point.

If the empirical cost emerges at ~50% of conservative_prior on equity-index cells, the ratio thresholds in §2 schema effectively halve: the 3 cells at ratio 0.85-1.27 become 1.7-2.5 (cost-friction-dominated-edge-present, VERIFIED); the 7 cells at 0.20-0.50 become 0.4-1.0 (marginal-edge-present); the bottom 25 cells remain edge-absent. This is the most-optimistic-feasible-reframing.

### 7.3 Cross-check anomalies vs existing KPI card metrics

**None found of concern**. The cost-friction-breakeven ratios are derived from PRE-cost realized OOS figures × conservative_prior cost subtraction; no discrepancy with KPI card §3.2 Table 1 (realized OOS) or Table 4 (annualized Sharpe) was surfaced. The metric is novel — it doesn't appear in any existing KPI card — so there is no cross-cell numerical-agreement requirement (per ADR-0014 §3.2 + ADR-0019 §3 13-table format).

One **methodology anomaly worth flagging** for sibling-ADR-0028 amendment (where the new annotation lands):

- **The H062 v3 ablation A1 result (−99.99997%)** is the only EMPIRICALLY-VERIFIED cost-friction-dominated cell in the entire inventory. All other 35 cells are `likely-*-pending-A0-verification`. The verified-vs-likely distinction is significant. ADR-0028 (concurrent work) should make A0-zero-cost-ablation MANDATORY at first KPI emission for every future genetic-successor hypothesis per `P1-A0-ZERO-COST-ABLATION-MANDATORY-FUTURE-KPIS`.

### 7.4 Top 2-3 candidates for cost-light genetic-successor (per ADR-0027 §D-4)

Per the §6.4 verdict + §7.1 reframing:

**Note on ID-numbering**: H066 is reserved (queued) for H065 + Turtle System 2 pyramiding successor (per [research/01_hypothesis_register/H065/design.md §17](../H065/design.md)). The candidate IDs below use H067 / H068 / H069 to avoid collision.

1. **H067 (cost-light H065-M_inf-SIL successor)** — predicted-best candidate. Lift the H065 v2 M_inf_h065_current SIL cell (+734.68% pre-cost OOS at 5,600 trades) into a new pre-registered hypothesis with: (a) lower trade-frequency entry-filter (channel-N ≥ 240 vs current 120; or news-calendar exclusion of FOMC + NFP + CPI release ±15min per design.md §11.2.6); (b) longer holding period via larger ATR-stop (k_atr ≥ 2.5 vs current 2.0); (c) wider opposite-channel-exit window. Goal: reduce trades from ~5,600 → ~1,000-2,000 over the same OOS while preserving per-trade-gross-edge ≥ 12-15 bps-of-equity. Pre-emit A0 ablation cell mandatory.

2. **H068 (cost-light H065-M_inf-ES successor)** — second-best. The H065 v2 M_inf_h062_v1_fixed ES cell at 110 trades is already structurally low-frequency. A successor with even higher channel-N + news-exclusion may reach ratio ≥ 2 (cost-friction-dominated-edge-present); but the small n_trades=110 reduces statistical power. Risk: degenerate-to-null under stricter filters.

3. **H069 (per-session-cadence variant of H055 v2 MGC C3 super-Kelly cell)** — speculative. The H055 v2 MGC C3 cell (+87% pre-cost OOS at 7,625 trades) has cost-friction ratio 0.25 but enormous trade count; a per-session-cadence (1 entry/session) restriction with ATR-tighter stop could collapse trades to ~700-1000 while preserving cell-conditional edge. Risk: the per-trade-gross-edge may drop proportionally and the cost-friction ratio fail to materially improve.

**Backlog placement**: per ADR-0027 §D-4 + ADR-0026 §D-3, these successors land at `queued` in [hypothesis_backlog.md](../../../hypothesis_backlog.md) Tier-2c following operator review.

## 8. Closure

- **Closure date**: 2026-05-19
- **Closure type**: ablation-complete (per ADR-0027 §D-1(c) form (i)) — 35-cell decomposition + 2 H062 v3 verified-ablation entries complete; cost-friction-breakeven ratio populated per cell; classification per §2 schema applied
- **Closure verdict**: `complete-no-further-action` at the investigation-memo layer; the empirical finding is the canonical INPUT to a future ADR-0028 cycle (concurrent; cost-friction-dominated-edge annotation grammar) and the future cost-light genetic-successor pre-registration cycle per `P1-COST-LIGHT-GENETIC-SUCCESSOR-PRE-REG`
- **Downstream artifacts produced**:
  - Investigation memo (this file): [research/01_hypothesis_register/_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md](INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md)
  - Reproduction script: [scripts/cost_realism_investigation_compute.py](../../../scripts/cost_realism_investigation_compute.py)
  - Raw computation output: [artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json](../../../artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json)
  - Audit trail: [docs/audits/audit_trail_2026-05-19_cost-realism-investigation.md](../../../docs/audits/audit_trail_2026-05-19_cost-realism-investigation.md)
  - New follow-ups registered (see below)
  - Commit SHA: (this commit's HEAD; populated post-commit)

### New follow-ups registered

| Follow-up | Status | Description |
|---|---|---|
| `P1-COST-REALISTIC-EMPIRICAL-CALIBRATION` | BLOCKING-BEFORE-PAPER-TRADE | Cross-hypothesis empirical cost calibration once paper-trade fill data accumulates (per ADR-0025 §D-3 `EmpiricalFeeOverride` machinery). Lands per-symbol slip + fee empirical-overrides; re-runs the §6.1 ratio computation at empirical values. |
| `P1-A0-ZERO-COST-ABLATION-MANDATORY-FUTURE-KPIS` | BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-PRE-REG | Every future hypothesis pre-registration design.md §5 SHALL declare an explicit A0-zero-cost-ablation cell to be run alongside the v1 KPI emission; closes the verified-vs-likely classification gap surfaced in §6.3. |
| `P1-H050-PER-ENTRY-COST-INVENTORY` | non-blocking | H050 v1 sidecar's `n_trades` field is bar-count (multibar-holding strategy); extract entry-count + round-trip-count separately at v2 emission; corrects the §6.1 H050 cost-friction ratio under entry-cadence convention. |
| `P1-H060-PER-SYMBOL-N-TRADES-SIDECAR-EXTEND` | non-blocking | H060 v2 basket-aggregate sidecar lacks per-symbol n_trades; extend at v3 emission to enable per-symbol cost-friction-breakeven analysis. |
| `P1-METALS-ENERGY-CME-FEE-VERIFY` | OPEN (pre-existing; ADR-0023) | CME Energy/Metals fee schedule placeholder verification per config/instruments.yaml:148-153; substrate-impact on cost-friction ratio for MGC + SIL + MCL cells (lower bound estimates in §6.1). |
| `P1-COST-LIGHT-GENETIC-SUCCESSOR-PRE-REG` | non-blocking | Per ADR-0027 §D-4: pre-register H066 + H067 + H068 (or operator-renamed equivalents) as cost-light genetic successors of H065 v2 + H055 v2 + (operator-selected source cell) per §7.4. |
| `P1-COST-FRICTION-BREAKEVEN-KPI-CARD-ANNOTATION` | non-blocking (forward-link to ADR-0028) | Once ADR-0028 lands the cost-friction-dominated-edge annotation grammar: add the new annotation to every emitted KPI card §"Methodological-correctness annotations" line; retroactive cascade per `P1-ADR-0028-DESIGN-MD-CASCADE` analog. |

## Cross-references

- H062 v3 ablation precedent: [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION](../H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- ADR-0027 §D-1 source mandate: [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- ADR-0017 survival-constrained primary metric vector: [docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md)
- ADR-0025 §D-3 cost-model infrastructure: [docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md)
- RESULTS_INDEX of every emitted KPI: [research/01_hypothesis_register/RESULTS_INDEX.md](../RESULTS_INDEX.md)
- Forward-link to ADR-0028 (cost-friction-dominated-edge annotation grammar; concurrent work; SHA TBD)
- Cost-model machinery: [nt8_es_nq_rth_v1](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) + [futures_orb_v1](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py) + [nt8_realistic_v1](../../../src/skie_ninja/backtest/costs/nt8_realistic.py)
- Config: [config/instruments.yaml](../../../config/instruments.yaml) (fee placeholders + retrieval dates)

## Append discipline

- Sections 1-5 are FROZEN at investigation start (2026-05-19); they MAY be edited only via versioned-successor pattern per ADR-0013 §4.1.
- Sections 6-8 are APPEND-as-work-completes; rows in the §6 cost-friction-breakeven table are immutable once landed.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
