---
addendum_id: INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION_addendum
schema_version: investigation_memo_addendum_v1
created: 2026-05-19
status: complete-no-further-action
parent_investigation: research/01_hypothesis_register/_cross_hypothesis/INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md
hypothesis_of_investigation: H055, H065 (MGC + SIL legs); H067 (depends on SIL parent ratio)
parent_kpi_report_card: research/01_hypothesis_register/RESULTS_INDEX.md
phase_o16_canonical_commits: 31e7f696ca8ac091c88ec32be86b7b0d5d646d85 (fee values landed) + 9a3a512 (independent re-verification audit trail)
---

# Investigation Memo Addendum — Cost-friction re-ranking post Phase O.16 fee recalibration

Per [ADR-0013 §4.1 non-loss](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), this is a **versioned successor** to the parent investigation memo [INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md](INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md) (the parent memo is immutable post-completion 2026-05-19; this addendum is appended as the canonical re-ranking artifact post fee recalibration; the parent's §1-§8 are unchanged).

Per [ADR-0027 §D-1](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md): this addendum runs NO new walk-forward compute; it is a pure post-hoc recomputation of the parent's §6.1 cost-friction-breakeven table using the Phase O.16 verified CME 2025-02-01 metals/energy fee schedule. The parent memo's pre-Phase-O.16 §6.1 ratios are preserved verbatim per non-loss.

## 1. Recalibration deltas (Phase O.16 fee recalibration)

[Phase O.16 commit 31e7f69](https://github.com/s-koirala/SKIE-Universe/commit/31e7f69) (2026-05-19) closed `P1-METALS-ENERGY-CME-FEE-VERIFY` via 3-way broker-passthrough triangulation against CME 2025-02-01 fee schedule. Independent re-verification [commit 9a3a512](https://github.com/s-koirala/SKIE-Universe/commit/9a3a512) confirmed canonical values. Per-side exchange-fee deltas:

| Symbol | Pre-Phase-O.16 (placeholder) | Post-Phase-O.16 (verified) | Delta per side | Composition impact |
|---|---:|---:|---:|---|
| **MGC** | $0.45 | **$0.60** | **+$0.15** | +33% per side (rate increased eff. 2025-02-01 per CME schedule) |
| **SIL** | $0.45 | **$1.00** | **+$0.55** | +122% per side (under-stated placeholder; MATERIAL) |
| **MCL** | $0.50 | $0.50 | $0.00 | MATCH (placeholder unchanged) |
| ES | $1.18 | $1.18 | $0.00 | not in Phase O.16 scope (already CME-verified 2024-02) |
| NQ | $1.18 | $1.18 | $0.00 | not in Phase O.16 scope |
| MES | $0.35 | $0.35 | $0.00 | not in Phase O.16 scope |
| MNQ | $0.35 | $0.35 | $0.00 | not in Phase O.16 scope |
| NFA fee | $0.02/side | $0.02/side | $0.00 | unchanged since 2018-01-01 (closes `P1-NFA-FEE-VERIFY-2026`) |

**Round-trip cost-bps-of-equity recalibration** (at $10K starting equity per ADR-0017 §4.1 + design.md §5.3 retail sizing convention; 1-contract assumption; per-side fixed = commission $0.85 + exchange + NFA $0.02):

| Symbol | Pre-Phase-O.16 cost_bps_eq | Post-Phase-O.16 cost_bps_eq | Delta | Compositional notes |
|---|---:|---:|---:|---|
| **MGC** | 4.640 | **4.940** | **+0.300** | fixed-per-side $1.32 → $1.47; slip-per-side $1.00 unchanged; round-trip $4.64 → $4.94 (+6.5%) |
| **SIL** | 12.640 | **13.740** | **+1.100** | fixed-per-side $1.32 → $1.87; slip-per-side $5.00 unchanged; round-trip $12.64 → $13.74 (+8.7%); slip dominates 73% of cost composition, fee 27% — moderate compositional impact |
| **MCL** | 4.740 | 4.740 | 0.000 | MATCH |
| ES / NQ / MES / MNQ | unchanged | unchanged | 0.000 | not in Phase O.16 scope |

Note that the SIL fee increase ($0.55/side delta) is the largest single recalibration in the Phase O.16 cycle, but the slip-component (1-tick × $5.00 tick-value = $5.00/side) dominates total cost composition; the round-trip cost increase is only $1.10 (+8.7%) despite the +122% fee-rate change. The MGC fee increase ($0.15/side delta) is smaller in absolute terms but the round-trip cost increase percentage is +6.5% (slip dominates less since MGC tick-value = $1.00/side = 67% of fixed-per-side; fee 33%).

## 2. Per-cell ratio updates (22 cells with MGC or SIL exposure)

Per the task #14 parent memo §6.1 schema. ES + NQ + MCL cells UNCHANGED (not in Phase O.16 scope; copied forward verbatim from parent §6.1). MGC + SIL cells RECALIBRATED. Sorted descending by post-Phase-O.16 ratio:

| Rank (post) | Hypothesis × cell | Sym | OOS% | n_trades | avg_per_trade_bps_eq | Pre cost_bps_eq | Post cost_bps_eq | **Pre ratio** | **Post ratio** | Δ ratio | Δ class? |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | H065 v2 M_inf_h062_v1_fixed | ES | +40.54% | 110 | 36.855 | 29.100 | 29.100 | **1.266** | **1.266** | 0.000 | unchanged (ES not in scope) |
| 2 | H065 v2 M_inf_h065_current | **SIL** | +734.68% | 5,600 | 13.119 | 12.640 | 13.740 | **1.038** | **0.955** | **−0.083** | **CROSSED BELOW 1.0** |
| 3 | H065 v2 M_inf_h062_v1_fixed | **SIL** | +446.38% | 4,165 | 10.717 | 12.640 | 13.740 | **0.848** | **0.780** | **−0.068** | no |
| 4 | H065 v2 M_inf_h065_current | **MGC** | −82.69% | 3,611 | −2.290 | 4.640 | 4.940 | 0.494 | 0.464 | −0.030 | no (edge-absent both) |
| 5 | H065 v2 M_inf_h062_v1_fixed | **MGC** | +116.48% | 5,221 | 2.231 | 4.640 | 4.940 | 0.481 | 0.452 | −0.029 | no |
| 6 | H065 v2 M_1.5 | ES | +18.15% | 211 | 8.602 | 29.100 | 29.100 | 0.296 | 0.296 | 0.000 | unchanged |
| 7 | H065 v2 M_2.5 | **MGC** | −68.81% | 5,084 | −1.353 | 4.640 | 4.940 | 0.292 | 0.274 | −0.018 | no |
| 8 | H055 v2 C5_super_pyramid | ES | −53.48% | 706 | −7.575 | 29.100 | 29.100 | 0.260 | 0.260 | 0.000 | unchanged |
| 9 | H055 v2 C3_superkelly | NQ | −19.30% | 530 | −3.642 | 14.100 | 14.100 | 0.258 | 0.258 | 0.000 | unchanged |
| 10 | H055 v2 C9_bocd_stepup | NQ | −8.69% | 249 | −3.490 | 14.100 | 14.100 | 0.248 | 0.248 | 0.000 | unchanged |
| 11 | H065 v2 M_inf_h065_current | ES | +54.37% | 759 | 7.163 | 29.100 | 29.100 | 0.246 | 0.246 | 0.000 | unchanged |
| 12 | H055 v2 C2_fullkelly | NQ | +0.89% | 26 | 3.423 | 14.100 | 14.100 | 0.243 | 0.243 | 0.000 | unchanged |
| 13 | **H055 v2 C3_superkelly** | **MGC** | +87.04% | 7,625 | 1.142 | 4.640 | 4.940 | **0.246** | **0.231** | −0.015 | no |
| 14 | H055 v2 C5_super_pyramid | **MGC** | +77.19% | 7,665 | 1.007 | 4.640 | 4.940 | 0.217 | 0.204 | −0.013 | no |
| 15 | H052a v1 (uncond) | NQ | +10.61% | 369 | 2.875 | 14.100 | 14.100 | 0.204 | 0.204 | 0.000 | unchanged |
| 16 | H053 v3 LightGBM | NQ | +10.80% | 372 | 2.903 | 14.100 | 14.100 | 0.206 | 0.206 | 0.000 | unchanged |
| 17 | H065 v2 M_1.0 | ES | +8.18% | 147 | 5.565 | 29.100 | 29.100 | 0.191 | 0.191 | 0.000 | unchanged |
| 18 | H055 v2 C5_super_pyramid | NQ | −14.30% | 584 | −2.449 | 14.100 | 14.100 | 0.174 | 0.174 | 0.000 | unchanged |
| 19 | H065 v2 M_1.0 | **SIL** | −62.71% | 2,993 | −2.095 | 12.640 | 13.740 | 0.166 | 0.152 | −0.013 | no |
| 20 | H055 v2 C2_fullkelly | **MGC** | +72.37% | 10,321 | 0.701 | 4.640 | 4.940 | 0.151 | 0.142 | −0.009 | no |
| 21 | H065 v2 M_1.5 | **SIL** | −58.26% | 3,015 | −1.932 | 12.640 | 13.740 | 0.153 | 0.141 | −0.012 | no |
| 22 | H065 v2 M_1.0 | **MGC** | +62.25% | 9,591 | 0.649 | 4.640 | 4.940 | 0.140 | 0.131 | −0.009 | no |
| 23 | H055 v2 C9_bocd_stepup | **MGC** | +58.04% | 9,442 | 0.615 | 4.640 | 4.940 | 0.132 | 0.124 | −0.008 | no |
| 24 | H065 v2 M_2.5 | **SIL** | −60.67% | 3,623 | −1.675 | 12.640 | 13.740 | 0.132 | 0.122 | −0.011 | no |
| 25 | H053 v3 ElasticNet | NQ | +6.20% | 372 | 1.667 | 14.100 | 14.100 | 0.118 | 0.118 | 0.000 | unchanged |
| 26 | H055 v2 C5_super_pyramid | **SIL** | −46.58% | 3,509 | −1.327 | 12.640 | 13.740 | 0.105 | 0.097 | −0.008 | no |
| 27 | H065 v2 M_2.0 | **SIL** | −36.26% | 3,859 | −0.940 | 12.640 | 13.740 | 0.074 | 0.068 | −0.006 | no |
| 28 | H052a v1 NQ (gated) | NQ | +3.39% | 369 | 0.919 | 14.100 | 14.100 | 0.065 | 0.065 | 0.000 | unchanged |
| 29 | H065 v2 M_2.5 | ES | +3.35% | 187 | 1.791 | 29.100 | 29.100 | 0.062 | 0.062 | 0.000 | unchanged |
| 30 | H053 v3 LightGBM | ES | +6.40% | 367 | 1.744 | 29.100 | 29.100 | 0.060 | 0.060 | 0.000 | unchanged |
| 31 | H065 v2 M_2.0 | ES | +2.23% | 169 | 1.320 | 29.100 | 29.100 | 0.045 | 0.045 | 0.000 | unchanged |
| 32 | H053 v3 ElasticNet | ES | −3.20% | 367 | −0.872 | 29.100 | 29.100 | 0.030 | 0.030 | 0.000 | unchanged |
| 33 | H055 v2 v1baseline | **SIL** | −1.21% | 329 | −0.368 | 12.640 | 13.740 | 0.029 | 0.027 | −0.002 | no |
| 34 | H053 v3 passive | NQ | +1.30% | 372 | 0.349 | 14.100 | 14.100 | 0.025 | 0.025 | 0.000 | unchanged |
| 35 | H065 v2 M_1.5 | **MGC** | −7.84% | 7,326 | −0.107 | 4.640 | 4.940 | 0.023 | 0.022 | −0.001 | no |
| 36 | H055 v2 C3_superkelly | **SIL** | −10.12% | 4,177 | −0.242 | 12.640 | 13.740 | 0.019 | 0.018 | −0.002 | no |
| 37 | H052a v1 (uncond) | ES | +1.61% | 371 | 0.434 | 29.100 | 29.100 | 0.015 | 0.015 | 0.000 | unchanged |
| 38 | H055 v2 C9_bocd_stepup | **SIL** | +7.23% | 3,959 | 0.183 | 12.640 | 13.740 | 0.014 | 0.013 | −0.001 | no |
| 39 | H052a v1 (gated) | ES | −0.94% | 371 | −0.253 | 29.100 | 29.100 | 0.009 | 0.009 | 0.000 | unchanged |
| 40 | H055 v2 v1baseline | **MGC** | −1.22% | 3,622 | −0.034 | 4.640 | 4.940 | 0.007 | 0.007 | 0.000 | no |
| 41 | H055 v2 C5_super_pyramid | ES | −0.97% | 641 | −0.151 | 29.100 | 29.100 | 0.005 | 0.005 | 0.000 | unchanged |
| 42 | H055 v2 C9_bocd_stepup | ES | −0.79% | 653 | −0.121 | 29.100 | 29.100 | 0.004 | 0.004 | 0.000 | unchanged |
| 43 | H055 v2 C2_fullkelly | **SIL** | +1.83% | 5,978 | 0.031 | 12.640 | 13.740 | 0.002 | 0.002 | 0.000 | no |
| 44 | H065 v2 M_2.0 | **MGC** | −0.65% | 7,055 | −0.009 | 4.640 | 4.940 | 0.002 | 0.002 | 0.000 | no |
| 45 | H050 v1 NQ (gated) | NQ | −84.20% | 673,274 | −0.013 | 14.100 | 14.100 | 0.001 | 0.001 | 0.000 | unchanged |
| 46 | H050 v1 ES (gated) | ES | −81.02% | 337,837 | −0.024 | 29.100 | 29.100 | 0.001 | 0.001 | 0.000 | unchanged |
| 47 | H050 v1 (uncond) ES | ES | −43.69% | 337,837 | −0.013 | 29.100 | 29.100 | 0.000 | 0.000 | 0.000 | unchanged |
| 48 | H050 v1 (uncond) NQ | NQ | −25.60% | 673,274 | −0.004 | 14.100 | 14.100 | 0.000 | 0.000 | 0.000 | unchanged |
| 49 | H053 v3 passive | ES | 0.00% | 367 | 0.000 | 29.100 | 29.100 | 0.000 | 0.000 | 0.000 | unchanged |

**Summary of recalibration impact** (per §1 fee deltas):

- **22 cells with MGC or SIL exposure**: ratio shifted DOWN (all MGC + SIL cells get smaller because cost denominator increased). Median ratio shift = −0.012; max ratio shift = −0.083 (the H067-parent SIL cell at rank #2).
- **27 cells with ES + NQ + MCL exposure**: ratio UNCHANGED (cost-bps-of-equity denominator unchanged on these symbols; ratios copy forward verbatim from parent memo §6.1).
- **One cell crossed a categorical threshold**: H065 v2 M_inf_h065_current SIL crossed from `pre = 1.038 ABOVE 1.0` to `post = 0.955 BELOW 1.0` — the only cell to change above-vs-below-unity classification under recalibration.
- **No new cells emerged in the top-3**: ES rank #1 unchanged at 1.266; SIL cells continued to occupy ranks #2-#3; H055 MGC + H065 MGC cells retain their mid-ranked positions.
- **Raw computation output**: post-Phase-O.16 JSON sidecar at [artifacts/runs/cost_realism_investigation/cost_friction_breakeven_post_phase_o16.json](../../../artifacts/runs/cost_realism_investigation/cost_friction_breakeven_post_phase_o16.json). Reproduction: `uv run python scripts/cost_realism_investigation_compute.py --fee-vintage post_phase_o16`. Pre-Phase-O.16 raw artifact preserved bit-identically at [artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json](../../../artifacts/runs/cost_realism_investigation/cost_friction_breakeven.json) plus a single annotation-field addition (`"fee_vintage": "pre_phase_o16"`) per ADR-0013 §4.1 non-loss; canonical row values bit-identical.

## 3. Re-ranked top-3 successor candidates (post Phase O.16)

Per the parent memo §7.4 framing + ADR-0027 §D-4 genetic-successor discipline. Ranking criterion: highest cost-friction-breakeven ratio under post-Phase-O.16 conservative_prior, given positive realized OOS, given the candidate is a genetic-successor target (NOT a derived-from-noise cell).

| Rank | Pre-Phase-O.16 | Post-Phase-O.16 | Δ rank | Pre-cost OOS | Post-recalibration ratio | Pre-recalibration ratio | CRR for ratio ≥ 2 (post) |
|---|---|---|---|---:|---:|---:|---:|
| **#1** | H067 (cost-light H065-M_inf-SIL successor) — parent ratio 1.04 | **H068** (cost-light H065-M_inf-ES successor) — parent ratio **1.27** | **NEWLY #1** | +40.54% (110 trades) | **1.266** | 1.266 (unchanged) | **36.7%** |
| **#2** | H068 (cost-light H065-M_inf-ES successor) — parent ratio 1.27 | **H067** (cost-light H065-M_inf-SIL successor) — parent ratio **0.96** | **DEMOTED to #2** | +734.68% (5,600 trades) | **0.955** | 1.038 (was above unity) | **52.3%** |
| **#3** | H069 (cost-light H055 v2 MGC C3 super-Kelly successor) | **#3 unchanged** — H069 (cost-light H055 v2 MGC C3 super-Kelly successor) | unchanged | +87.04% (7,625 trades) | 0.231 | 0.246 (small drift) | **88.4%** |

**Two reframings vs the parent memo §7.4**:

1. **H067 demoted from #1 to #2** — the H067 parent cell (H065 v2 M_inf_h065_current SIL) now has cost-friction-breakeven ratio **0.955 (sub-breakeven; per-trade gross-edge is now SLIGHTLY LESS than per-trade cost burden at conservative_prior)**. The parent's pre-Phase-O.16 ratio of 1.038 was already at-the-margin (only 3.8% above unity); the +8.7% SIL round-trip cost increase pushed it just below 1.0. Operationally, the H067 v1 KPI emission under conservative_prior will report (at the parent cell's modal hyperparameters) avg-per-trade-edge of 13.119 bps-of-equity vs cost of 13.740 bps-of-equity — the strategy slightly LOSES on a per-trade basis at the conservative_prior. The H067 design.md §1(c) inferential criterion (ratio ≥ 2 under conservative_prior) requires **52.3% cost reduction** (CRR) — a larger empirical-slip-reduction is now required.

2. **H068 promoted from #2 to #1** — the H068 candidate cell (H065 v2 M_inf_h062_v1_fixed ES) has ratio **1.266 UNCHANGED** since ES fees were not in Phase O.16 scope (ES fees were already CME-verified effective 2024-02 per [config/instruments.yaml line 50](../../../config/instruments.yaml)). H068 is empirically the strongest cost-light successor candidate by ratio; per-trade gross-edge (36.855 bps-of-equity) is 1.27× the conservative_prior round-trip cost (29.100 bps-of-equity). CRR for ratio ≥ 2 (cost-friction-dominated-edge-present per ADR-0028 §D-2) = **36.7%** — substantially LESS empirical-slip-reduction required vs H067.

3. **H069 unchanged at #3** — MGC fee increased $0.45 → $0.60/side (smaller absolute delta vs SIL); ratio drift modest 0.246 → 0.231 (−0.015). H069 remains the third-place candidate with the largest CRR (88.4%); cost-friction is still ~4× the per-trade gross-edge. Of the three candidates H069 has the LARGEST empirical-slip-reduction hurdle (88.4% is structurally unlikely to be achievable via slippage-only calibration; per parent memo §7.2 expected empirical-slip reduction on liquid futures is 30-70% which would translate to ratio improvements to ~0.6-0.9 NOT to ≥ 2).

**Why is the n_trades = 110 ES candidate empirically superior to the n_trades = 5,600 SIL candidate?**

The structural inversion vs the parent memo §7.4 ordering is load-bearing. The parent memo's "top candidate" SIL had +734.68% realized OOS on 5,600 trades — a much larger headline pre-cost outcome than ES's +40.54% on 110 trades. But the cost-friction-breakeven ratio is a per-trade metric: it tests whether the *typical* trade generates enough gross-edge to absorb the typical cost burden. SIL's per-trade gross-edge is 13.119 bps-of-equity; ES's per-trade gross-edge is 36.855 bps-of-equity (almost 3× larger per trade). SIL's headline outperformance comes from sheer trade volume × marginal positive expectancy; ES's headline outperformance comes from few large-edge trades. Under conservative_prior cost subtraction, ES's per-trade gross-edge has more headroom; SIL's barely covers cost.

**Statistical-power caveat for H068** (ES candidate): the n_trades = 110 figure is small. Per [Tharp 1998 *Trade Your Way to Financial Freedom*](https://www.amazon.com/Trade-Way-Financial-Freedom-Tharp/dp/0070647623) (*practitioner*) typical R-multiple-distribution-CI requires n ≥ 30 for narrow CI; n = 110 is comfortably above that threshold but well BELOW the n = 5,600 in the SIL parent. The point estimate (+40.54% / 110 trades) is reliable but its CI is wider than SIL's. The H068 cost-light pre-registration design.md §11.2 SHOULD declare a `n_min_trades = 50` precondition to ensure post-cost-light-filtering the cell retains enough trades to be statistically meaningful.

**Newly-promoted candidates** (cells that moved from below-unity to at-or-near-unity, or vice versa): one cell. H065 v2 M_inf_h065_current SIL is the SOLE cell that crossed the 1.0 boundary under recalibration. No previously-borderline cell moved upward into the top-3 because cost increased for MGC + SIL and ES + NQ + MCL ratios are unchanged.

## 4. Implication for H067 — should the project pivot to H068 ES instead?

This is the operationally-load-bearing decision the addendum forces.

### 4.1 H067 under post-Phase-O.16 numerics

H067 v1 was pre-registered 2026-05-19 at commit f71a6df (Phase O.15) with the parent-cell pre-Phase-O.16 ratio of 1.04 documented as the load-bearing motivating anchor (per H067 design.md §1.4 + §17 revision-log + §17.1 genetic-successor-cross-citation). The pre-registration text in §1.4 states:

> "The H065 v2 M_inf-SIL parent cell's cost-friction-breakeven ratio is 1.04 per the cross-hypothesis investigation 2026-05-19 §6.1 (13.12 bps-of-equity per-trade gross-edge vs 12.64 bps-of-equity round-trip cost at conservative_prior). This is at-the-margin under the canonical cost model — a modest empirical-cost reduction (e.g., 50% slip-component shrinkage from 1-tick to 0.5-tick per the cross-hypothesis investigation §7.2 anchored on practitioner anecdotes about retail-tier liquid-contract slippage) yields disproportionate outcome change because the compounding gross edge × 5,600 trades is multiplicative."

Post-Phase-O.16 the parent-cell ratio is **0.955**, NOT 1.04. The "at-the-margin under the canonical cost model" framing is no longer accurate — the parent cell is **slightly sub-breakeven** under verified fees. The H067 H_1 inferential criterion at design.md §1(c) (ratio ≥ 2 under conservative_prior) now requires:

- **52.3% CRR** (cost-reduction-required) to clear the cost-friction-dominated-edge-present threshold post-Phase-O.16.
- vs **48.1% CRR** pre-Phase-O.16 (recomputed correctly per the Phase O.16 audit trail F-4; the parent memo §6.4 cited "45%" was a 5pp arithmetic error per the Phase O.16 audit F-4 fix).
- The +4.2 pp CRR increase is small but tightens the empirical-slip-reduction hurdle.

Per parent memo §7.2 (preserved verbatim in the parent memo per non-loss), the EMPIRICALLY-REASONABLE slip-reduction range on liquid CME futures is 30-70% (cuts round-trip cost roughly 35-50% on equity-index symbols where slip dominates; SIL's slip-fraction is 73% per §1 above so a 50% slip cut yields ~36% cost reduction). At the upper end of the §7.2 range (70% slip cut) SIL achieves ~51% cost reduction — JUST at the CRR threshold for H067.

**The implication**: H067 v1 is now operationally borderline-but-not-disqualified. The H_1 criterion is achievable ONLY if empirical-slip on SIL turns out to be at the optimistic end of the §7.2 practitioner-anecdotal range. The pre-registration is still informative (it measures the structural sensitivity of the ratio to N-lot scaling under conservative_prior; the v1 conservative_prior emission will report whether N-lot scaling alone closes the gap — per parent memo §7.2 the bps-of-equity ratio is approximately N-invariant under conservative_prior, so the empirical-slip refinement is the load-bearing path).

### 4.2 H068 as the empirically-superior alternative

**Pre-registration of H068 is NOT yet landed**; per the parent memo §7.4 H068 was specified as the secondary candidate (rank #2). The post-Phase-O.16 re-ranking makes H068 the **empirically-strongest cost-light successor candidate** by ratio. Key comparison:

| Dimension | H067 (SIL parent) | H068 (ES parent) | Implication |
|---|---|---|---|
| Post-Phase-O.16 parent ratio | 0.955 (sub-breakeven) | 1.266 (above breakeven) | H068 has structural headroom |
| CRR for ratio ≥ 2 | 52.3% | 36.7% | H068 has 16pp lower hurdle |
| n_trades in parent cell | 5,600 | 110 | H067 has 51× more statistical power |
| Pre-cost OOS | +734.68% | +40.54% | H067 has 18× larger headline |
| Per-trade gross-edge (bps-of-equity) | 13.119 | 36.855 | H068 has 2.8× larger per-trade edge |
| ADR-0001 retail-capacity headroom | SIL ≤ 5 contracts (per H067 §1 binding) | ES ≤ 20 contracts (per ADR-0001) | H068 has 4× more retail-capacity headroom |
| Cost-axis preservation under N-lot scaling | per H067 design.md §1.4 caveat: ratio approximately invariant under N-lot at conservative_prior; depends on tier-commission-discount + empirical-slip-reduction | structurally similar; ES has VIP tier schedule (per [config/instruments.yaml line 238](../../../config/instruments.yaml) Tier 1 = $1.18; Tier 2 ≥ 1,000 contracts/month = $1.14; Tier 3 ≥ 10,000 contracts/month = $1.09); H068 N-lot scaling at N=5 over ~600 trades/year reaches ~3,000 contracts/year — above Tier 2 threshold | H068 has more concrete VIP-tier cost-discount mechanic |
| Lit-anchor coverage | partial-decay literature (Marshall-Cahan-Cahan 2008 + Hsu-Kuan 2005; per parent memo §7.4 + H062 §1.4) — `mixed` verdict | inherits same partial-decay literature plus equity-index has more direct intraday-ORB-on-futures lit-anchor (Holmberg-Lönnbark-Lundström 2013 + Tsai 2019) | H068 has a directly applicable lit-anchor |
| Substrate availability | SIL ≥ 11 partitions on canonical post-Phase-O.10 substrate `317429e4...` | ES ≥ 11 partitions on canonical post-Phase-O.10 substrate `317429e4...` | parity |
| Frozen pre-reg status | designed 2026-05-19 | not yet pre-registered | H068 requires new pre-reg cycle |

### 4.3 Operationally-actionable Pareto-front interpretation

Two operationally distinct paths emerge under the post-Phase-O.16 numerics:

**Path A: Continue H067 as-currently-pre-registered, with §17 amendment per Path A frozen-pre-reg amendment discipline.** H067's §1-§7 (immutable) frame SIL as the cell of interest; §17 revision-log appends the post-Phase-O.16 ratio shift (1.04 → 0.96) as documented context for future-stage interpretation. H067 v1 KPI emission proceeds; the v1 will report whether N-lot scaling under conservative_prior closes the gap (per H067 §1.4 caveat: not expected to under conservative_prior alone; the §6.3 forward path is paper-trade-empirical slip calibration via `P1-H067-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION`).

- **Pro**: preserves the H067 design.md frozen pre-reg per ADR-0013 §1-§7 immutability + ADR-0013 §4.1 non-loss audit-discipline value (the H067 pre-registration documents a decision made under a specific information state at a specific time; the post-Phase-O.16 reframing is an empirical update that subsequent emissions interpret against).
- **Pro**: H067's larger n_trades (5,600 in parent) yields tighter statistical inference at KPI emission than H068's n_trades = 110.
- **Pro**: SIL has the largest headline pre-cost OOS in the project (+734.68%); the structural skew-positive payoff shape at scale is itself documentation-worthy.
- **Con**: the H_1 criterion is now structurally harder to clear (52.3% CRR); the most-likely v1 verdict is "design.md §1 H_1 not supported under conservative_prior; potentially supportable under paper-trade-empirical slip reduction at the upper end of §7.2 range".

**Path B: Concurrent pre-registration of H068 as the empirically-stronger cost-light successor candidate.** H068 design.md inherits H067's template (single-axis N-lot grid; two-cost-arm A0 + A1 emission per ADR-0028 §D-2; etc.) with ES as the parent cell. ES fees unchanged at $29.10/round-trip → 29.100 bps-of-equity; parent ratio 1.266; CRR for ratio ≥ 2 = 36.7%.

- **Pro**: empirically the strongest cost-light successor candidate by ratio AND by per-trade gross-edge.
- **Pro**: ES has VIP-tier commission discount mechanic (Tier 2 ≥ 1,000 contracts/month) which is operationally realistic at N-lot scaling.
- **Pro**: lower CRR hurdle (36.7% vs 52.3%) means less empirical-slip-reduction needed for H_1 to clear.
- **Con**: H068 parent cell has only 110 trades (vs H067's 5,600); statistical inference is wider-CI.
- **Con**: requires new pre-registration cycle (lit-review + design.md + ADR-0027 §D-4 four-field disclosure + audit-remediate-loop); operational cost ~half-day.

### 4.4 Project-level recommendation framing

This is operator-discretionary per ADR-0013 §1 + ADR-0027 §D-4 + the operator 2026-05-04 + 2026-05-15 standing decline-ninjascript directive (which establishes that operator review is the load-bearing decision layer). The empirical ranking is post-Phase-O.16 #1 = H068 ES, #2 = H067 SIL, #3 = H069 MGC C3.

**The empirical case for H068 is the post-Phase-O.16 numerics**; the empirical case for H067 (now ranked #2) is statistical power + larger headline pre-cost OOS + N=5,600 trade-volume robustness. Both are admissible genetic-successor candidates. Operator review on the §4.3 Pareto-front is the load-bearing transition. The two paths are NOT mutually exclusive — both could be pursued concurrently (H067 KPI emission under existing pre-reg + new H068 pre-reg cycle in parallel), at the cost of additional infrastructure execution.

## 5. Operator-actionable next step (objective ranking + caveats)

Per [ADR-0026 §D-2](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) memo discipline: this section presents the objective ranking + caveats without phrasing recommendations as a question.

**Objective ranking**: top-3 cost-light genetic-successor candidates by post-Phase-O.16 cost-friction-breakeven ratio (highest = empirically strongest under realistic-cost framing):

1. **H068** (cost-light H065-M_inf-ES successor; NOT yet pre-registered) — ratio 1.266; CRR 36.7%; n_trades = 110.
2. **H067** (cost-light H065-M_inf-SIL successor; pre-registered 2026-05-19 commit f71a6df at status: designed) — ratio 0.955; CRR 52.3%; n_trades = 5,600.
3. **H069** (cost-light H055 v2 MGC C3 super-Kelly successor; NOT yet pre-registered) — ratio 0.231; CRR 88.4%; n_trades = 7,625.

**Caveats applicable to ALL three candidates**:

- Cost-friction-breakeven ratio is computed at PRE-cost realized OOS; post-cost A1 conservative_prior outcome is bounded below by the log-drag-compounded-and-bounded result demonstrated by the H062 v3 ablation A0 → A1 (parent memo §6.1 row "H062 v3 A1" cell). The headline pre-cost OOS figures are upper bounds; realistic-cost projections are bounded by the cost-friction ratio.
- ES + NQ + MCL fees were NOT in Phase O.16 scope (already CME-verified per parent memo §2). They remain canonical at pre-Phase-O.16 values per [config/instruments.yaml](../../../config/instruments.yaml) HEAD.
- Slippage component (1-tick prior per side) is unchanged across all three candidates; the parent memo §7.2 slippage-reduction-empirical path is the load-bearing forward calibration step that could push ALL three ratios upward in tandem.
- ADR-0001 retail-capacity ceilings constrain N-lot scaling: SIL ≤ 5; ES ≤ 20; MGC ≤ TBD (not in ADR-0001 v1; per H067 + H062 design.md §11.1 K-4 binding).
- The parent memo §7.4 ID-numbering convention is preserved (H067 / H068 / H069); H066 remains reserved for the H065 + Turtle System 2 pyramiding successor per [H065/design.md §17](../H065/design.md).

**Whether H067 SIL retains top-candidate status under post-Phase-O.16 numerics**: **NO** — empirically demoted from #1 (pre-Phase-O.16 ratio 1.038) to #2 (post-Phase-O.16 ratio 0.955). The demotion does NOT invalidate H067 — H067's status remains `designed` with substantial statistical power and N-lot grid sensitivity surfacing as v1 deliverable. H067 v1 KPI emission proceeds under existing pre-registration; the §17 revision-log gains a new row recording the post-Phase-O.16 ratio shift.

**Newly-promoted candidates (post-recalibration)**: H068 (ES) is the empirically-strongest cost-light successor candidate at rank #1 post-Phase-O.16; H067 (SIL) is now rank #2. Operator pre-registration of H068 as a Path B parallel cycle is the recommended operationally-actionable next step alongside continuing H067 v1 KPI emission.

## 6. Closure

- **Closure date**: 2026-05-19
- **Closure type**: re-ranking-complete (per ADR-0027 §D-1(c) form (i)) — 22 cells with MGC + SIL exposure recomputed under verified CME 2025-02-01 fee schedule; top-3 successor candidates re-ranked
- **Closure verdict**: `complete-no-further-action` at the addendum layer; the empirical finding is the canonical INPUT to (a) the H067 design.md §17 revision-log Path A amendment landed in the same commit cycle, (b) the operator-discretionary H068 pre-registration cycle if pursued, (c) the parent investigation memo §8 follow-up `P1-COST-LIGHT-GENETIC-SUCCESSOR-PRE-REG` re-ranking input
- **Downstream artifacts produced**:
  - Addendum memo (this file)
  - Recomputation script: [scripts/cost_realism_investigation_compute.py](../../../scripts/cost_realism_investigation_compute.py) with `--fee-vintage post_phase_o16` flag (non-invasive amendment per task spec guardrails)
  - Raw computation output: [artifacts/runs/cost_realism_investigation/cost_friction_breakeven_post_phase_o16.json](../../../artifacts/runs/cost_realism_investigation/cost_friction_breakeven_post_phase_o16.json)
  - Pre-Phase-O.16 raw artifact preserved bit-identically + single annotation-field addition (`"fee_vintage": "pre_phase_o16"`) per ADR-0013 §4.1 non-loss
  - Audit trail: [docs/audits/audit_trail_2026-05-19_cost-realism-rerank-post-phase-o16.md](../../../docs/audits/audit_trail_2026-05-19_cost-realism-rerank-post-phase-o16.md)
  - H067 design.md §17 revision-log Path A amendment (concurrent commit)
  - hypothesis_backlog.md H067 row update (concurrent commit)
  - Commit SHA: (this commit's HEAD; populated post-commit)

### New follow-ups registered

| Follow-up | Status | Description |
|---|---|---|
| `P1-H068-PRE-REGISTRATION-COST-LIGHT-ES-SUCCESSOR` | NEW; non-blocking; operator-discretionary | Per §4.4 Path B: pre-register H068 as cost-light H065-M_inf-ES successor; design.md mirrors H067 template with ES parent cell, N-lot grid `N ∈ {1, 2, 3, 4, 5}` capped at ADR-0001 retail-capacity ES ≤ 20 ceiling, two-cost-arm A0 + A1 emission per ADR-0028 §D-2. CRR for ratio ≥ 2 = 36.7% (modest empirical-slip-reduction hurdle). |
| `P1-H067-DESIGN-MD-§17-PATH-A-AMENDMENT-POST-PHASE-O16` | CLOSED in this commit cycle | H067 design.md §17 revision-log gains row recording post-Phase-O.16 parent-ratio shift 1.04 → 0.96; cross-references this addendum memo. Path A admissible per ADR-0013 §"Frozen pre-registration amendment" (§17 is outside §1-§7 immutable range). |
| `P1-HYPOTHESIS-BACKLOG-H067-POST-PHASE-O16-DESC-UPDATE` | CLOSED in this commit cycle | hypothesis_backlog.md H067 row description gains post-Phase-O.16 ratio shift (1.04 → 0.96) + parent-ratio-now-sub-breakeven framing per the addendum §3 re-ranking. |
| `P1-PARENT-MEMO-§6.4-ARITHMETIC-ERRATUM` | NEW; non-blocking | Parent memo §6.4 "Most promising successor candidate?" column reports H067 cost-reduction-required as "45%" but the correct pre-recalibration figure is 48.1% per Phase O.16 audit F-4. Parent is immutable per ADR-0013 §4.1; the erratum is canonical at this addendum §4.1 + the Phase O.16 audit trail [docs/audits/audit_trail_2026-05-19_metals-energy-cme-fee-verify.md](../../../docs/audits/audit_trail_2026-05-19_metals-energy-cme-fee-verify.md) F-4 disposition. |
| `P1-COST-LIGHT-GENETIC-SUCCESSOR-PRE-REG-RE-RANK` | (re-references existing parent §8 `P1-COST-LIGHT-GENETIC-SUCCESSOR-PRE-REG`) | The post-Phase-O.16 re-ranking is the empirical input to the parent's open follow-up; ranking is now (H068, H067, H069) descending. |

## Cross-references

- Parent investigation memo: [INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION](INVESTIGATE-FAILURE-MODE-COST-CONSERVATIVE-PRIOR-CALIBRATION.md)
- Phase O.16 fee-verification audit trail (canonical): [audit_trail_2026-05-19_adr-0028-code-primitives.md](../../../docs/audits/audit_trail_2026-05-19_adr-0028-code-primitives.md)
- Phase O.16 fee-verification independent re-verification audit trail: [audit_trail_2026-05-19_metals-energy-cme-fee-verify.md](../../../docs/audits/audit_trail_2026-05-19_metals-energy-cme-fee-verify.md)
- Phase O.16 canonical commit: [31e7f69](https://github.com/s-koirala/SKIE-Universe/commit/31e7f69)
- Phase O.16 independent re-verification commit: [9a3a512](https://github.com/s-koirala/SKIE-Universe/commit/9a3a512)
- H067 design.md (parent successor pre-reg): [H067/design.md](../H067/design.md)
- H067 v1 lit-review: [H067/lit_review_H067_2026-05-19.md](../H067/lit_review_H067_2026-05-19.md)
- ADR-0023 metals/energy substrate expansion: [ADR-0023](../../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md)
- ADR-0025 abandonment-trigger infrastructure: [ADR-0025](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md)
- ADR-0027 operational discipline + bounded exploration: [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- ADR-0028 K-6/K-7 size-down + cost-friction-dominated-edge annotation: [ADR-0028](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md)
- config/instruments.yaml at HEAD (canonical post-Phase-O.16 metals/energy fee values): [config/instruments.yaml](../../../config/instruments.yaml)
- nt8_realistic_v1 cost-model at HEAD: [src/skie_ninja/backtest/costs/nt8_realistic.py](../../../src/skie_ninja/backtest/costs/nt8_realistic.py)
- Re-ranking audit trail: [audit_trail_2026-05-19_cost-realism-rerank-post-phase-o16.md](../../../docs/audits/audit_trail_2026-05-19_cost-realism-rerank-post-phase-o16.md)

## Append discipline

- Sections 1-5 are FROZEN at addendum start (2026-05-19); they MAY be edited only via versioned-successor pattern per ADR-0013 §4.1.
- Section 6 (Closure) is APPEND-as-work-completes; rows in §6 follow-up table are immutable once landed.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
