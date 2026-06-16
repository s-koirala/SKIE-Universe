---
id: MPV2
artifact: kpi_report_card
version: v1
date: 2026-06-15
stage_on_emit: kpi-report-emitted
authority: ADR-0029 (center of gravity) · ADR-0020 (meta-portfolio) · ADR-0013 (governance) · ADR-0014 §3.2 (results-summary) · ADR-0026 §D-1 (3-component header) · ADR-0017/0018 (survival + MPPM)
verdict: NULL — closed-loop allocator beats NEITHER 1/N NOR buy-and-hold OOS
run_id: 1980ec1eba2d4f4b965c44a965780370
sidecar: artifacts/runs/MPV2/1980ec1eba2d4f4b965c44a965780370/sidecar.json
scientific_payload_sha256: d85ae777d754de3c6981703bc919fc16f999efcdfacdebc3a6681485221acffb
substrate_dataset_checksum: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
arm_stream_vintage: 286829dce681bec874be0464731013f628d49d0b61005ec1500875f947fc12ea
repro_log_status: complete (P1-MPV2-REPROLOG-WIRE closed — `scripts/run_mpv2_closed_loop.py --real`)
---

# MPV2 KPI report card v1 — regime-switching meta-allocation closed loop: forward-validation against 1/N and buy-and-hold

> **Disposition: `null` per [MPV2 design.md §8](design.md).** The closed-loop regime-switching allocator does **not** beat equal-weight 1/N (the switching−1/N CI lower bound covers zero on both windows — this alone rejects the conjunctive H_1), and **no allocator — switching, causal joint-Kelly, or 1/N — statistically beats buy-and-hold OOS** on either evaluated window. This is the falsifiable center of the [ADR-0029](../../../docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md) paradigm returning a NULL, which [ADR-0029 §D-4 pre-registered as a fully informative outcome](../../../docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md) (per [Lo 2004](https://doi.org/10.3905/jpm.2004.442611) AMH; recorded under [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) non-loss). The result POINTS to the simultaneous portfolio (concurrent pooling, [ADR-0020](../../../docs/decisions/ADR-0020-meta-portfolio-orchestrator.md)) over switching as the durable-upside route — and, because even pooling does not clear B&H net of the library's cost-fragility, motivates the cost-light forward direction (H068 lineage; see [ADR-0030](../../../docs/decisions/ADR-0030-cost-light-arm-generation-refined-center-of-gravity.md)).

**Reproducibility note.** The verdict is now CLI-reproducible: `OMP_NUM_THREADS=1 uv run --extra dev python scripts/run_mpv2_closed_loop.py --real` emits the canonical sidecar (run_id `1980ec1e…`; sci_sha `d85ae777…`; ReproLog `logs/reproducibility/1980ec1eba2d4f4b965c44a965780370.json`) — closing `P1-MPV2-REPROLOG-WIRE` and superseding the ad-hoc Phase-P drive's two-pass value sets. The reproducing run reads the regenerated `317429e4` substrate for the buy-and-hold series; the arm reward streams (H060 `c31a8a60…`, H062 `5554a2f8…`, H055 C9 `v2_sweep_20260602T200706Z`) were generated on the `286829dc` 2015–2025 vintage, but the 3-arm (2024–2025) and 2-arm (2020–2025) common windows are **vintage-invariant** (the 2026 partitions never touch a pre-2026 common date), so the verdict is identical on either vintage. **Single material correction vs the Phase-P buildout narrative:** the 2-arm switching MPPM is **+0.0279, not −0.020** (the buildout/earlier-drive copied the 3-arm −0.020 into the 2-arm row); the qualitative verdict is unchanged (+0.028 < 1/N 0.261 < B&H 0.191).

## §0 — Three-component KPI summary (per [ADR-0026 §D-1](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md); headline = median-path + MPPM(ρ=1) per [ADR-0029 §D-3.1](../../../docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md))

Headline figure for a meta-allocator is the **time-average growth rate MPPM(ρ=1)** (the operator-experienced compounding rate under non-ergodicity; ADR-0029 §D-3.1) of the closed-loop equity path vs each benchmark. The **median terminal-wealth path** (the second mandated headline) is deferred (`P1-MPV2-FULL-SURVIVAL-VECTOR` — the allocator equity array is emitted by the runner but the median-path/forward survival vector is not yet computed).

| Component | Window | Closed-loop MPPM(ρ=1) | 1/N pool | Buy-and-hold | Verdict |
|---|---|---:|---:|---:|:--:|
| **1. Full realized OOS** (3-arm {H055, H060, H062}; v1-scoped pre-reg window) | 2024-01-02 → 2025-05-30 (364 sess) | **−0.020** | 0.320 | 0.127 | allocator < 1/N ; no allocator beats B&H |
| **1. Full realized OOS** (2-arm {H060, H062}; wider-history subset diagnostic) | 2020-12-23 → 2025-11-06 (1252 sess) | **+0.028** | 0.261 | 0.191 | allocator < 1/N < B&H-comparable ; no allocator beats B&H |
| **2. 2026-onward sub-window** | — | N/A | N/A | N/A | arm streams are 2015–2025 vintage (2026 excluded); `P1-MPV2-SUBSTRATE-2026-EXTENSION` |
| **3. Forward 1-yr bootstrap projection** | — | deferred | deferred | deferred | allocator survival-vector not yet computed; `P1-MPV2-FULL-SURVIVAL-VECTOR` |

**One-line bottom line:** the switching closed loop fails to beat 1/N on both windows (switching−1/N CI lower bound −0.001477 / −0.000639 covers zero) — rejecting the conjunctive H_1; and separately every allocator's 1/N−B&H and pooled−B&H lower bounds cover zero, so no allocator statistically beats buy-and-hold. A clean NULL that reframes the center of gravity toward cost-light arm generation per ADR-0030.

## §1 — Hypothesis (per [design.md §1](design.md), FROZEN) and verdict

**H_1**: the closed-loop allocator's OOS per-session return stream beats **BOTH** (a) equal-weight 1/N (the [DeMiguel-Garlappi-Uppal 2009](https://doi.org/10.1093/rfs/hhm075) stringent benchmark) **AND** (b) buy-and-hold passive-long, on the primary metric (§7), at 95% one-sided.

**Verdict: H_1 REJECTED (NULL).** The disposition chain (per [design.md §8](design.md) conjunctive rule): the switching allocator fails to beat 1/N — the switching−1/N paired-bootstrap one-sided lower bound covers zero on both windows (−0.001477 [3-arm], −0.000639 [2-arm]) — **this alone rejects the conjunctive H_1**, independent of the B&H leg. The supplementary finding that **no allocator (including 1/N and the causal joint-Kelly pool) beats B&H** is reported separately below; it strengthens the AMH read but is not the disposition basis. A NULL is fully informative per ADR-0029 §D-4; §"Regime-conditional breakdown" reports where (if anywhere) the allocator adds value.

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md), adapted for a meta-allocator forward-validation)

A meta-allocator forward-validation is not a single-arm walk-forward, so the per-symbol single-arm tables of the [canonical 13-table template](../../_templates/kpi_results_summary_template.md) (Win/Loss/Zero, per-symbol annualised Sharpe, Hansen SPA family) are **N/A by construction** (enumerated in §E) and are replaced by the allocator-appropriate analogues.

### A. Cross-arm independence (P-4 diagnostic per [design.md §3.3](design.md); the §1 pooling premise)

| Window | n arms | n common sessions | selected bandit | Effective number of bets (Meucci 2009) |
|---|---:|---:|---|---:|
| 3-arm {H055, H060, H062} (pre-reg window) | 3 | 364 | EXP3.S | **2.989 / 3** (mean \|off-diag corr\| 0.052) |
| 2-arm {H060, H062} (subset diagnostic) | 2 | 1252 | D-UCB | **1.999 / 2** (mean \|off-diag corr\| 0.035) |

The arms are near-perfectly de-correlated — the ergodicity pooling precondition ([ADR-0029 §D-3.4](../../../docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md)) is met emphatically. This is precisely the regime in which de-correlated arms favour **pooling over switching** (and in which 1/N is hardest to beat, DGU 2009) — so the switching-bandit's failure is the theory-predicted outcome, not an implementation defect.

### B. Primary inference — MPPM(ρ=1) time-average growth (causal, CI-backed; sidecar `1980ec1e…`)

Joint-Kelly fractions are fit on the pre-OOS calibration head (fraction 0.30), **frozen**, and applied to the disjoint evaluation tail (no look-ahead in the weights). The 1/N and B&H benchmarks are parameter-free on the identical calendar-aligned matrix.

| Allocator | 3-arm {H055, H060, H062} 2024–2025 (364 sess) | 2-arm {H060, H062} 2020–2025 (1252 sess) | beats B&H (one-sided CI excl 0⁺) |
|---|---:|---:|:--:|
| **1/N equal-weight pool** (DGU 2009) | **0.320** | **0.261** | **NO** (1/N−B&H lower bound −0.0007 [3-arm] / −0.0011 [2-arm]) |
| Buy-and-hold (EW {ES, NQ, MGC, SIL} daily) | 0.127 | 0.191 | — (reference) |
| OOS joint-Kelly pool (causal, fit-on-calib) | 0.150 | 0.045 | NO (pooled−B&H lower −0.0011 / −0.0011) |
| **Switching closed-loop** (bandit → early-warning → CPPI) | **−0.020** | **+0.028** | NO |

The causal joint-Kelly fit **zeros out H062** on both windows ([H055 0.608, H060 0.392, H062 0.0] on 3-arm; [H060 0.257, H062 0.0] de-levered on 2-arm) — yet the optimised pool (0.150 / 0.045) is **dominated by naive 1/N** (0.320 / 0.261). This is the [DGU 2009](https://doi.org/10.1093/rfs/hhm075) estimation-noise result in force and is the empirical basis for the [ADR-0030](../../../docs/decisions/ADR-0030-cost-light-arm-generation-refined-center-of-gravity.md) note that the winning pooler is 1/N, not the optimised weighting.

### C. Paired-bootstrap differential CIs (per [design.md §7](design.md); [Politis-Romano 1994](https://doi.org/10.1080/01621459.1994.10476870) stationary bootstrap, PW2004 block length, 1000 replicates; all from the single sidecar run)

| Differential | 3-arm mean / one-sided lower | 2-arm mean / one-sided lower | excludes zero⁺ |
|---|---|---|:--:|
| switching − 1/N (sized) | −0.000675 / **−0.001477** | −0.000141 / **−0.000639** | NO (rejects H_1 1/N-leg) |
| switching − B&H (sized) | −0.000147 / −0.000976 | −0.000191 / −0.000821 | NO |
| pooled(JK) − 1/N | −0.000675 / −0.002078 | −0.000860 / −0.002081 | NO |
| pooled(JK) − B&H | +0.000092 / −0.001149 | −0.000581 / −0.001143 | NO |
| 1/N − B&H | +0.000768 / −0.000735 | +0.000279 / −0.001053 | NO |

Every margin's one-sided lower bound covers zero: **no allocator statistically beats buy-and-hold on either window**, and the switching loop fails its 1/N leg (the disposition basis).

### D. Causal-fit detail (in-sample-overfit guard)

The in-sample joint-Kelly on the full window is markedly higher than the causal fit (the Phase-P drive reported an in-sample joint-Kelly +0.229 on the 3-arm window) — the canonical look-ahead-in-the-weights trap. The **causal fractions** above ([H055 0.608, H060 0.392, H062 0.0]; 2-arm [H060 0.257, H062 0.0]) and the causal pooled MPPM (0.150 / 0.045) are the load-bearing values; the in-sample number is recorded only so a successor never re-reports it as a result.

### E. N/A single-arm tables (auditable omissions)

| Template table | Status | Reason |
|---|---|---|
| 1. P/L per symbol · 1c. τ_3 · 4. Annualised Sharpe per symbol | N/A | allocator is cross-arm; no per-symbol arm; Sharpe demoted to secondary per ADR-0017 §1.2 (MPPM is primary, Table B) |
| 3a/3b/3c survival vector | DEFERRED | terminal-wealth-q05 / Calmar-diff / PF / R-mult at the allocator layer not yet computed; `P1-MPV2-FULL-SURVIVAL-VECTOR` |
| 5. Win/Loss/Zero | N/A | allocator emits a per-session reward stream, not a per-trade ledger |
| 6. Forward 1-yr projection | DEFERRED | allocator survival-vector not yet computed; `P1-MPV2-FULL-SURVIVAL-VECTOR` |
| 7. Hansen SPA family p | N/A | the disposition is a conjunctive two-benchmark test (design.md §7 AND-rule), NOT a max-over-family SPA; the five reported differential CIs (§C) are descriptive and all cover zero, so no multiplicity adjustment can change the NULL verdict (adjustment only widens intervals) |

### F. Causal-alignment invariant attestation (the #1 risk; [design.md §3.4](design.md) BLOCKING)

The load-bearing risk for any allocator forward-validation is look-ahead. Verified clean on four sub-checks (the R1 audit of the P-5 machinery + the reproducible-run causal construction): (i) each arm's session-t reward comes from positions sized by parameters frozen on data strictly preceding t (walk-forward-frozen orchestrators; MPV2 does not re-fit); (ii) 1/N and B&H are built on the identical calendar-aligned matrix with no ex-post arm selection; (iii) the full-sample oracle is a labelled non-tradeable diagnostic, excluded from the beat-target; (iv) the allocator's session-t decision uses only rewards through t−1 (bandit, early-warning, CPPI sizing all causal by construction). The reproducibility-verifier independently re-ran the committed functions and matched every headline number; the in-sample → causal joint-Kelly demotion (+0.229 → 0.150/0.045) is itself the proof the invariant is enforced.

### 9. Methodological-correctness annotations

`causal-alignment-invariant-clean` · `leakage-canary-pass` (Cycle-4 canaries inherited via the walk-forward-frozen arm orchestrators) · `mppm-primary-headline` · `repro-log-complete` (sidecar `1980ec1e…`; ReproLog flushed) · `bss-n/a` · `reliability-n/a` · `dsr-n/a` (single allocator, no strategy family) · `cost-zero-v1` (arm reward streams are pre-cost; cost-fragility established separately at the arm layer per milestone-5 / ADR-0030) · `post-run-audit-pass` (Round-1 quant + reproducibility, trail [docs/audits/audit_trail_2026-06-15_mpv2-kpi-card-and-real-run.md](../../../docs/audits/audit_trail_2026-06-15_mpv2-kpi-card-and-real-run.md))

## Regime-conditional breakdown (per [design.md §8](design.md) / [Lo 2004](https://doi.org/10.3905/jpm.2004.442611) AMH)

The switching closed loop is negative-to-marginal on both windows (−0.020 / +0.028), so there is no window in which it adds value over 1/N. The instructive AMH read is across the allocator *family*: **pooling dominates switching, and within pooling NAIVE 1/N dominates the optimised joint-Kelly** (which the estimation-noise of DGU 2009 penalises). On de-correlated arms, holding all N concurrently is the time-average-growth-superior move ([ADR-0029 §D-3.4](../../../docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md); [Peters-Adamou 2022](https://doi.org/10.1098/rsta.2020.0425)), and switching merely incurs reallocation churn. The operator's "switch strategies when the climate changes" intuition is the wrong mechanism for a de-correlated library; "hold all N, 1/N-weighted" is the right one — and even that does not clear B&H at 95% because the underlying arms' edge over passive is marginal and cost-fragile (milestone-5; ADR-0030).

## Scope caveats (each tracked)

- **Smoke-grade arms** — H055 (C9 config) and H062 ran in `--smoke`; full-grid arms tracked `P1-MPV2-FULL-GRID-ARMS`.
- **3-arm 2024–2025 window** is the v1-scoped pre-registered result (bounded by H055's smoke OOS right edge); the **2-arm 2020–2025 window is a wider-history subset diagnostic** (pre-2024 H055 absent), not the design.md §2 frozen 4-arm common fold. A longer 3-arm window needs H055's full OOS (`P1-MPV2-H055-FULL-OOS-WINDOW`).
- **H050 deferred** — its committed `oos_returns.parquet` is dateless (not calendar-joinable); the known signal-HARMING HMM-gated arm re-enters at v2 via a dated re-run (`P1-MPV2-H050-DATED-RERUN`, BLOCKING-before-4-arm-verdict). v1 scope = 3 arms.
- **Substrate vintages** — verdict reproduced on `317429e4`; arm streams on `286829dc`; common windows vintage-invariant. A v2 may regenerate all arms with 2026 (`P1-MPV2-SUBSTRATE-2026-EXTENSION`).

## Bottom line

The regime-switching meta-allocation closed loop — the falsifiable center of the [ADR-0029](../../../docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md) paradigm — returns a clean **NULL**: it fails to beat 1/N on both windows (the disposition basis), and the switching bandit (MPPM −0.020 / +0.028) is dramatically worse than naive 1/N (+0.320 / +0.261). More broadly, **no allocator statistically beats buy-and-hold** on either window (every 1/N−B&H and pooled−B&H lower bound covers zero) — confirming, per [Lo 2004](https://doi.org/10.3905/jpm.2004.442611) AMH and substantiating the operator's external-validity concern, that the current arm library's edge over passive is marginal and climate-conditional. The load-bearing finding is constructive: on de-correlated arms, **simultaneous pooling dominates switching, and naive 1/N dominates the optimised joint-Kelly** ([DeMiguel-Garlappi-Uppal 2009](https://doi.org/10.1093/rfs/hhm075) in full force), so the durable-upside route is the [ADR-0020](../../../docs/decisions/ADR-0020-meta-portfolio-orchestrator.md) concurrent portfolio defaulting to 1/N weighting, not the switching loop. Because even pooling does not clear B&H net of the library's cost-fragility (milestone-5: every standalone arm is cost-erased), the next mandatory transition is **not** NinjaScript (the allocator is not a worthy candidate per ADR-0029 §D-1) but the **cost-light arm-generation refinement of the center of gravity** ([ADR-0030](../../../docs/decisions/ADR-0030-cost-light-arm-generation-refined-center-of-gravity.md); H068 lineage). Verdict reproducible via `scripts/run_mpv2_closed_loop.py --real` (sidecar `1980ec1e…`). Remaining residuals: `P1-MPV2-FULL-SURVIVAL-VECTOR` (allocator-layer survival vector), `P1-MPV2-H050-DATED-RERUN` (4-arm verdict).
