---
artifact: H065 v2 SIL standalone cell-grid robustness investigation
date: 2026-05-15
audit_type: empirical robustness check (cell-grid sensitivity sweep)
verdict: NULL (cell-conditional artifact; original v1 finding does not generalize)
---

# H065 v2 SIL Standalone — Cell-Grid Robustness Investigation

## 1. Motivation

H065 v1 KPI emission (commit `20ef08d`) surfaced a surprise finding: SIL standalone (no TP overlay; current-equity rebase; cell N=120, k_atr=2.0, h_dwell=5, atr_n=14, trend_id=a_ts_mom L=60 τ=1.0) produced **MPPM(ρ=1) CI [+0.087, +0.459] strictly excluding zero positively** — the only such cell across 9 emitted KPI report cards (H050, H052a, H053 v3+v4, H054, H055 v2, H060, H062 v1, H065 v1).

This investigation tests whether that finding is ROBUST (holds across nearby cells) or CELL-CONDITIONAL (single-cell artifact).

## 2. Investigation design

- **Cell grid**: channel_n ∈ {60, 120, 240} × k_atr ∈ {1.5, 2.0, 2.5} × h_dwell ∈ {5, 10} × atr_n = 14 = **18 cells**
- **Kelly grid**: {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} = **6 multipliers per cell**
- **Total combos**: 108
- **Per-combo computation**: full simulation on SIL 2015-2026 with current-equity rebase; MPPM(ρ=1) with 1000-bootstrap stationary-bootstrap CI; 2026-04-01→2026-05-15 sub-window separately
- **Discriminator**: cells with `mppm_ci.ci_low > 0` (strict positive-edge) counted

## 3. Result

| Metric | Value |
|---|---:|
| Cell-Kelly combos with n_trades ≥ 30 | 108 |
| Combos with MPPM CI strictly positive | **1** |
| % positive-edge | **0.9%** |
| Best cell by MPPM point | (N=120, k=1.5, h_dwell=10) km=0.25 — MPPM +0.209 CI=[-0.001, +0.430] (just covers zero) |
| ONLY positive-edge cell | (N=120, k=1.5, h_dwell=5) km=0.25 — MPPM +0.193 CI=[+0.003, +0.413] |

**Verdict**: NULL. The original v1 SIL standalone finding does NOT generalize across cells.

## 4. Substantive observations

1. **Quarter-Kelly discrimination**: the single positive-edge cell is at km=0.25 with tightly-bounded position sizes. Higher Kelly multipliers amplify variance, not edge.
2. **Realized ROI vs MPPM dissociation**: many cells show realized ROI in the +1000-1800% range (e.g., (N=240, k=1.5, h_dwell=5) km=1.0 at +1,861% realized ROI) but with MaxDD 60-75% and MPPM CI covering zero. Headline ROI ≠ Sharpe-promotable edge.
3. **2026-04-01→2026-05-15 sub-window**: predominantly 0.0% (no trades fired in 6-week sub-window for low-Kelly cells) or negative (-2% to -22%) at higher-Kelly cells. No cell-Kelly combo produced positive 2026 sub-window returns of meaningful magnitude.
4. **Channel N=120 + k_atr=1.5** is the "best-performing" sub-grid by MPPM but barely — only one cell achieves strict positive-edge and only at quarter-Kelly.
5. **Cherry-picking pathology confirmed**: H065 v1 reported the SIL standalone result from a single cell that happened to be in the marginal-positive tail of the cell-grid distribution. The 108-cell distribution has 99.1% of cells with MPPM CI covering zero — the v1 finding was statistically expected given the search-space size.

## 5. Cross-hypothesis read

Across 9 emitted KPI cards + this 108-cell investigation = ~120 distinct cell-Kelly-config tests. Total cells with MPPM CI strictly positive: 1 (= 0.83%). At α=0.05 multiple-testing nominal, expected false-positive rate ≈ 6 cells. Observing 1 cell at marginal-positive after 108 tests is **consistent with the null hypothesis that the strategy has zero mean-edge**.

The L-skewness τ_3=+0.74 (statistically positive at v1) IS real — but the H062-family signal class has positive-skew payoff WITHOUT positive mean-edge. This is the Marshall-Cahan-Cahan 2008 + Hsu-Kuan 2005 + Park-Irwin 2007 partial-decay prior playing out empirically.

## 6. Implications for the H062/H065 program

- **H065 v1 surprise finding RETRACTED**: SIL standalone is not robustly positive-edge. The v1 cell was a cherry-picked single-cell-tail observation.
- **Cell-grid sensitivity is the binding constraint**: high-N + low-k_atr + low-Kelly + dense trade count produces marginal positive MPPM points but not strict-positive CI.
- **Higher Kelly amplifies left tail proportionally**: cells with massive ROI (+1,800%) also have massive MaxDD (60-90%) and statistically marginal MPPM.
- **The path forward is NOT H066 SIL-dedicated**: the cell-grid sensitivity says SIL has no special edge beyond what the broader H062 family provides.

## 7. Recommendation

- Retire the `P1-H065-SIL-STANDALONE-V2` follow-up. The investigation confirms SIL standalone is null at conventional 95% CI.
- DO continue investigating the H062-family at the Kelly-vs-survival-constraint trade-off. The C9 BOCD step-up sweep (Phase O.4) remains the highest-value variant: basket +217.7% with 0 catastrophic legs.
- Pre-register `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` (BLOCKING-BEFORE-MPV2-INFERENCE) as the next inferential step. Cross-arm correlation analysis is the only untested project-level question.

## 8. Sidecar provenance

- Sidecar: [artifacts/runs/H065/sil_standalone_v2_20260516T033921Z/sidecar.json](../../artifacts/runs/H065/sil_standalone_v2_20260516T033921Z/sidecar.json)
- SHA256: `68ec8196662ca3f3d96ecedef91d09a972e8abe6aa94b1423bf4866ba5f2ba45`
- Script: [scripts/run_h065_sil_standalone_investigation.py](../../scripts/run_h065_sil_standalone_investigation.py)
- Wall-clock: ~10 minutes for 108 simulations × 2 windows (full + 2026 sub-window)
