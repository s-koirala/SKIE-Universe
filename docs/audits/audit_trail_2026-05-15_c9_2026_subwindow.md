---
artifact: H062 C9 BOCD step-up on 2026-04-01 → 2026-05-15 OOS sub-window
date: 2026-05-15
audit_type: empirical sub-window test (autonomous-loop iteration)
verdict: SUBSTANTIVE FINDING — C9 sits out 2026; outperforms C3 by avoidance
---

# C9 BOCD-step-up on 2026 sub-window — findings

## 1. Motivation

Per [audit_trail_2026-05-15_h065_sil_standalone_v2.md §7](audit_trail_2026-05-15_h065_sil_standalone_v2.md) recommendation 2 ("Continue C9 BOCD step-up (Phase O.4) — still the highest-leverage variant"), test whether C9's +217.7% basket result (full 2020-2025; [artifacts/runs/H062/c9_bocd_step_up_20260516T013136Z/](../../artifacts/runs/H062/c9_bocd_step_up_20260516T013136Z/)) holds on the fresh 2026-04-01 → 2026-05-15 sub-window.

Comparison anchor: C3 super-Kelly on same sub-window returned **-6.1%** basket (per [artifacts/runs/H062/c3_2026_q1q2_20260516T001902Z/](../../artifacts/runs/H062/c3_2026_q1q2_20260516T001902Z/)).

## 2. Methodology

- Warm-up: 2024-01-01 → 2026-04-01 (~500 sessions to initialize C9 BOCD state machine + dense per-session MPPM path)
- Sub-window: 2026-04-01 → 2026-05-15 (~30 sessions per symbol)
- Cell: v1 production representative (N=120, k_atr=2.0, h_dwell=5, atr_n=14, a_ts_mom L=60 τ=1.0)
- C9 config: km_grid={0.5, 1.0, 1.5, 2.0, 2.5}, km_start=1.5, BOCD hazard_rate=1/100, window=60, threshold=0.5

## 3. Result

[artifacts/runs/H062/c9_2026_q1q2_20260516T040345Z/sidecar.json](../../artifacts/runs/H062/c9_2026_q1q2_20260516T040345Z/sidecar.json) (sha256 `a1d16d3af05c7522...`):

| Symbol | Sub-window ROI | n_sessions | km_terminal | Full-window ROI | Trades total | Last trade |
|---|---:|---:|---:|---:|---:|---|
| ES | 0.0% | 0 | 0.50 | +101.4% | 191 | Pre-2025-09 |
| NQ | 0.0% | 0 | 1.00 | -11.7% | 14 | Pre-2025-09 |
| MGC | 0.0% | 0 | 0.50 | -6.5% | 985 | 2025-09-30 |
| SIL | 0.0% | 0 | 0.50 | +49.0% | 776 | 2025-09-30 |
| **BASKET** | **0.0%** | — | — | — | 1,966 | — |

**Sub-window basket ROI: 0.0%** (vs C3 -6.1%; vs passive +11.8%).

## 4. Substantive finding — sizing-zero floor

All 4 symbols ended with **zero sub-window trades** despite the substrate covering 2026-04-01 → 2026-05-15. Root cause:

1. C9 BOCD correctly detected decay across all 4 symbols during 2024-2025 OOS and halved km from 1.5 → 1.0 → 0.5 (km_terminal=0.5 for ES, MGC, SIL; NQ stayed at 1.0 because only 14 trades fired, insufficient to trigger BOCD halving).
2. At km=0.5 + 1% risk_budget × current equity (which ranged $9-15K post-drawdown), per-trade target risk ≈ $50.
3. SIL example: dollar_1r ≈ k_atr × ATR × multiplier = 2.0 × $0.06 × $1000 = $120 → position size = floor($50/$120) = **0 contracts**. Trade NOT fired.
4. Symmetric for MGC + ES at km=0.5.

**C9 effectively "sat out" the 2026 sub-window via Kelly de-risking to a size-floor that blocks new entries.**

## 5. Comparison vs C3

| Config | 2026 sub-window basket ROI | Risk behavior |
|---|---:|---|
| C3 super-Kelly km=2.0 | -6.1% | Kept full-Kelly sizing; took 102 trades; lost on majority |
| **C9 BOCD step-up** | **0.0%** | **Sat out via Kelly halving to size-floor** |
| Passive equal-weight | +11.8% | Continuous exposure to underlying trend |

## 6. Interpretation

This is **not the same as "C9 has alpha"**. It's **"C9 has a survival-instinct"**: when BOCD detects decay, it scales Kelly down; at retail equity that translates to position-size-zero, effectively pausing the strategy. The 0% sub-window result vs C3's -6.1% is loss-avoidance, not edge.

**Loss-avoidance vs edge**:
- 6-week alpha capture: ZERO (C9 made no trades).
- 6-week loss avoidance: +6.1% relative to C3.
- 6-week opportunity cost: -11.8% relative to passive long.

**Operator implication**: at retail equity, C9 BOCD's de-risking mechanism is a CIRCUIT BREAKER, not a Kelly-scale-down. The strategy goes inactive when BOCD halves km below the size-floor threshold. This is desirable behavior (don't trade during regime decay) but means the +217.7% basket result on the full 2020-2025 sample is heavily skewed toward the EARLY portion of the OOS when BOCD hadn't yet halved.

## 7. Cross-cutting implications

- The full 2020-2025 C9 basket +217.7% was earned in the FIRST half of the sample (before BOCD detected decay across all legs). The SECOND half (late 2025 + 2026) produced no trades.
- The realized OOS Sharpe + MPPM CI from the full-window C9 result should be re-computed on just the FIRST-HALF sub-period (before BOCD halving fired) to surface the true edge-bearing regime.
- **C9 is implicitly a regime-detection-and-sit-out system**, not a continuous-edge-bearing strategy. This is fine — but the operator should know.

## 8. Recommendations

1. Document this finding in the C9 KPI report card (when the full Phase O.4 report card v1 is authored). The current Phase O.4 ledger entry mentions BOCD detected decay but doesn't surface the size-floor consequence.
2. Pre-register `P1-C9-CIRCUIT-BREAKER-VS-EDGE-DECOMPOSITION` follow-up: re-compute the C9 +217.7% full-window result on the pre-decay-detection sub-period only.
3. For LIVE operation at retail equity, set a minimum-Kelly-floor (e.g., km_min=1.0 not 0.5) to keep the strategy active even during BOCD-flagged regimes. Trade-off: less de-risking. Tracked under new follow-up `P1-C9-KM-FLOOR-RETAIL-EQUITY`.

## 9. Sidecar provenance

- Sidecar: [artifacts/runs/H062/c9_2026_q1q2_20260516T040345Z/sidecar.json](../../artifacts/runs/H062/c9_2026_q1q2_20260516T040345Z/sidecar.json)
- SHA256: `a1d16d3af05c7522...`
- Script: [scripts/run_h062_c9_2026_q1q2.py](../../scripts/run_h062_c9_2026_q1q2.py)
- Wall-clock: ~10 seconds for 4 symbols × 2024-2026 warm-up + filter
