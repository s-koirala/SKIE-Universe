---
hypothesis_id: H052a
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-05
git_head: 0aa92585c80e85b371af918691ebcbfb3b9980b5
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d
  vix_daily: 0a0e9f252bcaa3f2f9ee2d0ef142e8fff88924aa6a2590d76e924dd50d6ab552
sidecar_scientific_payload_sha256: cca86b2746e5cb1bc62984352d21d2a55c182ed779fe3f741da52bfa52e60442
config_resolved_sha256: b8b6018ca3529f588fa7f3fe6e2e6dd850b9d67ae5ad502f67f52f6516768250
orchestrator_script_sha256: de3a41e7351915edc43c11e2d9daaa742ea1bc0601a78fba2018a83a60c9e24d
env_id: be80f7deb0f0c666d78e06d0e7917780f64f567b730e064d0515fc4142ec9d55
pip_freeze_sha256: c92ce92af9a6a103f64241690f3a5c22b7f542053ef524fefcd74662651d9d4e
run_id: 184eccd67bf24d71990265d39c28daf0
rng_seed: 20260423
sizing_convention: first_hour_orb_futures_session_cadence  # ADR-0013 §3.1.1 first-hour ORB futures row
supersedes: null
superseded_by: null
---

# H052a — KPI Report Card v1

> **First production walk-forward Stage-3 KPI emission** for hypothesis H052a — HMM regime-gated first-hour ORB on CME ES/NQ futures. Canonical [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3 + §3.1 KPI report card on the post-Cell-I substrate following the Phase 1 dedicated-orchestrator buildout (commit `6e87a9d`) + Phase 2 build-defect remediation chain (commits `583a4ee` → `0aa9258`). Production run completed 2026-05-05 11:44:43 (run_id `184eccd6...`; ReproLog at [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../../../logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json)).

- **Hypothesis** (per [design.md §1](design.md)): H_1: `T_H052a = SR_{ORB, HMM-gated} − SR_{ORB, unconditional} > 0`. H_0: regime-gating does not improve Sharpe over the unconditional first-hour ORB on the same instrument by more than bootstrap sampling error. Per design.md §1 critical interpretive note, unconditional ORB-on-futures is pre-supposed to be ≈null; H052a tests whether **regime-conditioning rescues an otherwise null signal**. A positive result would carry large evidentiary weight; a null is the expected outcome. (Pre-supposition narrowed by Phase-0 lit-check Erratum-2 — see [§15.1 errata addendum](design.md#151-citation-errata-phase-0-orb-lit-check-2026-05-04-findings-l-1-through-l-4): Holmberg-Lönnbark-Lundström 2013 + Tsai 2019 establish modestly positive unconditional ORB-on-futures in primary literature; H_1 unchanged.)
- **Design.md**: [design.md](design.md) (frozen at `status: designed`; §15 + §15.1 errata addendum landed 2026-05-04 commit `fa7b5c8` per Path A frozen-pre-reg amendment discipline)
- **Stage**: `kpi-report-emitted` per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). Next mandatory transition: `ninjascript-implemented` per ADR-0013 §5; pure-C# implementable (HMM forward filter at session-open requires Python inference at decision time per ADR-0005, so bridge-mediated per ADR-0013 §1.2 + ADR-0002).
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md) (this commit creates entries 1-6 for the Phase 2 build-defect remediation chain)

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md))

H052a production walk-forward (run_id `184eccd67bf24d71990265d39c28daf0`; commit `0aa9258`; ~14 min wall-clock; substrate `b3ee230a...` 2020-2024 ES + 2020-2024 NQ + VIX `0a0e9f25...`; cost-aware net-of-cost per design.md §1 + §7 + cost model `futures_orb_v1`):

### 1. P/L (realized OOS, $10K starting capital, daily-cleared single-leg session-cadence per ADR-0013 §3.1.1 first-hour ORB futures row)

| Symbol | Arm | End equity | Δ vs $10k | Δ pct | Cost model |
|---|---|---:|---:|---:|---|
| ES | hmm_gated | $9,905.85 | -$94.15 | **-0.94%** | futures_orb_v1, $29.10 r/t |
| ES | unconditional | $10,161.33 | +$161.33 | +1.61% | futures_orb_v1, $29.10 r/t |
| NQ | hmm_gated | $10,338.73 | +$338.73 | +3.39% | futures_orb_v1, $14.10 r/t |
| NQ | unconditional | $11,061.27 | +$1,061.27 | **+10.61%** | futures_orb_v1, $14.10 r/t |

### 2. Drawdown (realized + projected)

| Symbol | Arm | Realized max-DD | Proj median DD | Proj q95 DD |
|---|---|---:|---:|---:|
| ES | hmm_gated | 6.99% | 5.85% | 11.22% |
| ES | unconditional | 6.68% | 6.09% | 11.89% |
| NQ | hmm_gated | **11.83%** | 6.70% | 13.12% |
| NQ | unconditional | 7.95% | 6.36% | 12.43% |

(Projected DD bootstrap on per-session log returns; PW2004 selected `block_length=1.0` on 3 of 4 cells, `1.30` on NQ unconditional. Bootstrap is at session granularity (the natural ORB cadence), so unlike H050 there is no bar-vs-session understatement caveat.)

### 3. Sharpe — primary inference (T_H052a = SR_gated − SR_uncond per design.md §1)

| Symbol | SR_gated (per-sess) | SR_uncond (per-sess) | T_H052a (per-sess) | LW2008 95% CI [low, high] | excludes zero | T_H052a annualised |
|---|---:|---:|---:|---|:---:|---:|
| ES | -0.00750 | -0.01089 | -0.01840 | [-0.06762, +0.02604] | NO | -0.292 |
| NQ | +0.01975 | +0.05389 | -0.03417 | [-0.12321, +0.00326] | NO (barely) | -0.542 |

H_1 (T_H052a > 0) is NOT supported on either symbol — point estimates are negative, but LW2008 differential CIs cover zero. **Result: T_H052a not statistically distinguishable from zero at α=0.05; HMM gating does NOT rescue the signal as hypothesised.**

(Primary inference is on per-session log returns. SR_gated and SR_uncond above are per-session statistics; the LW2008 CI is computed on the same per-session scale per [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) with NW1994 per-replicate bandwidth selection; n_bootstrap=2000.)

### 4. Annualised Sharpe (×√252 = 15.875)

| Symbol | Arm | Annualised Sharpe |
|---|---|---:|
| ES | hmm_gated | **-0.119** |
| ES | unconditional | +0.173 |
| NQ | hmm_gated | +0.313 |
| NQ | unconditional | **+0.855** |

(Annualisation factor: per-session × √252 — the canonical convention for daily-cleared session-cadence strategies per ADR-0013 §3.1.1 sizing-convention table.)

### 5. Win/Loss/Zero session counts + win rate

| Symbol | Arm | Wins | Losses | Zeros | Win rate W/(W+L+Z) |
|---|---|---:|---:|---:|---:|
| ES | hmm_gated | 175 | 158 | 38 | 47.2% |
| ES | unconditional | 195 | 176 | 0 | 52.6% |
| NQ | hmm_gated | 189 | 164 | 16 | 51.2% |
| NQ | unconditional | 199 | 170 | 0 | 53.9% |

ES gated-out 38/371 sessions (10.2%); NQ gated-out 16/369 (4.3%). The gated-out sessions on ES were predominantly **non-losing** in the unconditional arm (gating reduces ES W by 20 + L by 18 + Z by ±0 → −10 sessions of net +PnL); on NQ, gated-out reduced unconditional W by 10 + L by 6 (− net +PnL). Both directions: HMM gating filters out marginally-positive-edge sessions, NOT the high-loss tail.

### 6. Forward 1-year (252-session) bootstrap projection ($10k starting capital)

5,000 bootstrap MC paths × 252 sessions; rng_seed=20260423; PW2004-selected block lengths per arm × symbol (3 cells iid, 1 cell stationary block=1.30):

| Symbol | Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) | block_b | method |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ES | hmm_gated | $9,942.80 | $9,952.48 | $8,742.58 | $9,118.69 | $10,852.55 | $11,246.76 | **54.84%** | 0% | 0% | 1.0 | iid_bootstrap |
| ES | unconditional | $10,112.78 | $10,131.56 | $8,774.98 | $9,136.67 | $11,193.15 | $11,662.87 | 42.94% | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | hmm_gated | $10,244.36 | $10,272.37 | $8,652.63 | $9,116.80 | $11,551.12 | $12,207.52 | 37.12% | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | unconditional | $10,729.27 | $10,766.49 | $8,902.67 | $9,442.41 | $12,239.43 | $12,914.52 | **18.56%** | 0% | 0% | 1.30 | stationary_bootstrap_PR1994 |

NQ unconditional ORB is the single positive cell on every metric (highest median ending equity; lowest P(loss); positive realised OOS).

### 7. Hansen SPA family p-value

| Symbol | T_SPA | p | n_bootstrap | omega method | Annotation |
|---|---:|---:|---:|---|---|
| ES | 0.0 | 1.0 | 1000 | hac | `spa-rejects` (m=1 degenerate per ADR-0008; T_SPA = max(0, √n·d̄/ω) = 0 because T_H052a < 0; p=1.0 = fail to reject H_0:E[d]≤0) |
| NQ | 0.0 | 1.0 | 1000 | hac | `spa-rejects` (same mechanism) |

H052a's pre-registered SPA family per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md) has only 1 strategy (the H052a hypothesis itself); per [ADR-0008 §"Single-strategy degenerate handling (|M|=1)"](../../../docs/decisions/ADR-0008-spa-omega-method.md) the SPA composite null degenerates to a single-strategy one-sided test of `H_0: E[d] ≤ 0` with `T_SPA = max(0, √n·d̄/ω)`. With `d̄ < 0` (T_H052a < 0 on both symbols), `T_SPA = max(0, negative) = 0`; p=1.0 is a mechanical consequence, NOT a "ADR-0008 convention". For primary inference, the LW2008 differential CI in §3 above is the binding KPI; the SPA result here is reported per `rules/quant-project.md` §Inference but is not informative beyond the LW2008 CI.

### 8. Other KPIs

| KPI | ES | NQ |
|---|---|---|
| Best label cfg (PT, SL, vol-lookback) | pt=1.0, sl=1.5, vol_lb=120m | pt=0.5, sl=1.0, vol_lb=60m |
| Inner-CV mean Sharpe at optimum | **-0.667** | **-1.294** |
| HMM selected (cov, n_states) | full, 3 | full, 3 |
| HMM nonstress_state | 0 | 0 |
| Train / Test sessions | 736 / 371 | 736 / 369 |
| n_folds (realized/expected) | 1/1 (single outer fold per design.md §6) | 1/1 |
| Feature NaN drops | 0 | 0 |
| Entry-price NaN drops | 1 (single missing 10:30 ET bar) | 1 |
| Cost-floor sensitivity_mult | 1.0 (1-tick prior; design.md §7) | 1.0 |
| Round-trip cost / contract | $29.10 (commission $0.85 × 2 + exchange $1.18 × 2 + NFA $0.02 × 2 + 1-tick slip $12.50 × 2) | $14.10 (same fees, 1-tick = $5.00 × 2) |
| Cost-to-notional ratio (typical entry) | ~3e-4 | ~3e-4 |
| Sortino / turnover / capacity | not computed (deferred follow-ups) | not computed |

Both arms have **negative inner-CV Sharpe at the optimum cell**. The 27-cell PT × SL × vol-lookback grid does not yield a positive-Sharpe configuration on the inner walk-forward CV (3 folds × purge=embargo=1 session). On ES, 4 of 27 cells have positive inner-CV mean Sharpe on fold-0 only — none survive the fold-1 + fold-2 averaging. Same canonical signal-absence pattern as H050.

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2)

`leakage-canary-pass` · `bss-n/a` · `reliability-n/a` · `repro-log-complete` · `dsr-n/a (M=1)` · `cost-conditional` · `post-run-audit-pass`

### Bottom line

H052a is a **non-significant null** under ADR-0013 §1: T_H052a < 0 on both symbols, but LW2008 differential CIs cover zero on both — the negative point estimate is not statistically distinguishable from zero at α=0.05 (ES T_H052a = -0.0184 [-0.0676, +0.0260]; NQ T_H052a = -0.0342 [-0.1232, +0.0033]). HMM regime-gating as configured does NOT rescue the unconditional ORB signal; on NQ it actively REDUCES Sharpe (annualised SR drops +0.855 → +0.313) and ending equity (drops +10.6% → +3.4% over 369 OOS sessions) while filtering only 4.3% of sessions. Per design.md §1 critical interpretive note, a null was the expected outcome — HMM-gating was the sole new empirical content; the prior-art-narrowed Erratum-2 framing (modestly positive unconditional ORB-on-futures per Holmberg 2013 + Tsai 2019) is supported by the unconditional NQ result (+0.855 annualised SR, +10.6% realized OOS, P(loss)=18.6% in the 252-session forward projection). Per ADR-0013 §1 + §5, H052a progresses to mandatory bridge-mediated NinjaScript implementation regardless of these KPIs (next mandatory transition `kpi-report-emitted` → `ninjascript-implemented`; tracked under `P1-H052A-NINJASCRIPT-IMPL`).

Full report card body: §"Methodological-correctness annotations" through §"Operator review section" below; sidecar at [artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/sidecar.json](../../../artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/sidecar.json); ReproLog at [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../../../logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json).

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | **pass** | Phase 1 R2 audit ACCEPT (5 critical + 9 major remediated; [audit_trail_2026-05-04_h052a-phase-1-infrastructure.md](../../../docs/audits/audit_trail_2026-05-04_h052a-phase-1-infrastructure.md)). Causal HMM warm-start via `terminal_log_alpha(X_train)` + `filter_states_from_prior(X_test, log_alpha_prior, n_propagation_steps=...)` per ADR-0005 (F-Q-4 Phase 1 fix). ETH+RTH bars retained for HMM emission features (F-Q-3 Phase 1 fix); RTH-only used for ORB labelling. Walk-forward inner CV with purge=embargo=1 session (F-Q-5 Phase 1 fix). |
| `bss-{positive,flat,negative}` | **n/a** | design.md §8.a binds `Calibration: BSS > 0 — applicable: NO for H052a`. H052a's pre-registered output is a continuous trading-rule directional signal (PT/SL/timestop session P/L), not a calibrated probability forecast. |
| `reliability-{in,out}-of-band` | **n/a** | Same rationale as BSS; design.md §8.a binds `applicable: NO`. |
| `repro-log-{complete,incomplete}` | **complete** | Canonical ReproLog at [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../../../logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json). All 13 fields present: `git_head=0aa92585`, `pip_freeze_sha256=c92ce92a...`, `dataset_checksums` (2 entries: `vendor_legacy_1min_roll_adjusted` + `vix_daily`), `rng_seed=20260423`, `model_hash=cca86b27...` (matches scientific_payload SHA256 binding), `config_resolved_sha256=b8b6018c...`, `env_id=be80f7de...`, etc. (Sidecar `git_head=unknown` is a pre-existing issue tracked under `P1-RUNCONTEXT-GIT-HEAD`; the canonical git_head is in the ReproLog and matches commit `0aa9258`.) |
| `dsr-{positive,marginal,negative,n/a}` | **n/a** | Single-strategy family (M=1) below `dsr_activation_size`; per [config/gate.yaml](../../../config/gate.yaml). |
| `cost-{robust,conditional,flat}` | **conditional** | 1-tick slippage prior per design.md §7 + [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py); cost is APPLIED as a per-session log-return drag `log(1 - cost_round_trip / notional)` per ADR-0013 §3.1 F-CONV-2 binding. Empirical regime-wise calibration deferred to `P1-H052A-COST-CALIBRATION-EMPIRICAL`. |
| `post-run-audit-{pass,fail}` | **pass** | Sidecar correspondence verified: scientific_payload SHA `cca86b27...` (in [scientific_payload_sha256.txt](../../../artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/scientific_payload_sha256.txt)) matches the model_hash in ReproLog. |

**No methodological-correctness banner triggered** per ADR-0013 §2.1 (all annotations green or n/a).

## Performance KPIs (per ADR-0013 §3 + `rules/quant-project.md` §Reporting)

### Sharpe-vs-unconditional differential (LW2008 studentised stationary bootstrap CI)

H052a's design.md §1 binds `T_H052a = SR_{ORB, HMM-gated} − SR_{ORB, unconditional}`. The unconditional series is the same first-hour ORB long-only directional trade applied at every session WITHOUT the HMM regime-gate factor; the gated series multiplies the binary HMM regime-state indicator `reg_t ∈ {0, 1}` (1 = HMM forward-filter posterior in non-stress state, 0 = stress state → flat for the session). Where `reg_t = 0`, the gated arm is flat at zero P/L (and zero cost); where `reg_t = 1`, gated and unconditional coincide trade-for-trade.

The Sharpe values reported below are **per-session** statistics (1 round-trip per RTH session); the LW2008 CI is computed on the same per-session scale per [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py); n_bootstrap=2000; α=0.05.

| Symbol | SR_gated (per-sess) | SR_uncond (per-sess) | **T_H052a (per-sess)** | LW2008 CI [low, high] | excludes_zero | T_H052a annualised | Annotation |
|---|---:|---:|---:|---|:---:|---:|---|
| ES | -0.00750 | -0.01089 | -0.01840 | [-0.06762, +0.02604] | NO | -0.292 | `sharpe-vs-unconditional-marginal` |
| NQ | +0.01975 | +0.05389 | -0.03417 | [-0.12321, +0.00326] | NO (barely) | -0.542 | `sharpe-vs-unconditional-marginal` |

**Result**: H_1 (T_H052a > 0) is NOT supported on either symbol. Point estimates are negative on both, but LW2008 differential CIs cover zero — the result is **non-significant null**, not a significant negative result (cf. H050 where LW2008 CI excluded zero on the negative side on both symbols). Mechanism (informational; not load-bearing): the HMM emission vector (5 features: realized variance, first-hour sign, gap size, DOW, ETH pre-RTH return + VIX daily join) does not isolate sessions where the unconditional ORB would lose money — it filters out marginally-positive-edge sessions on ES (10.2% gated-out, near-zero realized lift) and modestly-positive-edge sessions on NQ (4.3% gated-out, +0.4pp win-rate but Sharpe drops by 0.54).

### Sharpe-vs-passive (annualised; informational)

| Symbol | Annualised SR_gated | Annualised SR_uncond | n_test_sessions |
|---|---:|---:|---:|
| ES | -0.119 | +0.173 | 371 |
| NQ | +0.313 | **+0.855** | 369 |

NQ unconditional ORB is the strongest standalone signal in the run. Annualised Sharpe +0.855 is consistent with primary literature on intraday futures ORB (Holmberg-Lönnbark-Lundström 2013; Tsai 2019 — see design.md §15.1 Erratum-2). ES unconditional Sharpe (+0.173) is materially weaker, consistent with ES being the higher-volume / lower-edge sibling per ADR-0001 capacity ceiling table.

### Hansen SPA family p-value

| Symbol | SPA statistic | p-value | n_bootstrap | omega method | Annotation |
|---|---:|---:|---:|---|---|
| ES | 0.0 | 1.0 | 1000 | hac (m=1 degenerate) | `spa-rejects` (mechanical: T_H052a < 0 → T_SPA = max(0, neg) = 0 → p=1.0; ADR-0008 §"Single-strategy degenerate handling (\|M\|=1)") |
| NQ | 0.0 | 1.0 | 1000 | hac (m=1 degenerate) | `spa-rejects` (same mechanism) |

`SingleStrategySPAWarning` raised on both symbols. Pre-registered SPA family of 1 strategy; SPA p-value uninformative at m=1 by ADR-0008. For primary inference, the LW2008 differential CI is the binding KPI.

### Other performance KPIs (per `rules/quant-project.md` §Reporting)

| Symbol | Realized end equity (gated) | Max-DD (gated) | Realized end equity (uncond) | Max-DD (uncond) | n_folds (realized/expected) | best label cfg |
|---|---:|---:|---:|---:|:---:|---|
| ES | $9,905.85 (-0.94%) | 6.99% | $10,161.33 (+1.61%) | 6.68% | 1/1 | (pt=1.0, sl=1.5, vol_lb=120m) |
| NQ | $10,338.73 (+3.39%) | 11.83% | **$11,061.27 (+10.61%)** | 7.95% | 1/1 | (pt=0.5, sl=1.0, vol_lb=60m) |

**Power-margin annotation**: `power-margin-met` (n_folds=1/1 expected per design.md §6 single-outer-fold convention).
**Max-DD annotation**: `max-dd-mild` (all 4 cells under 12% realised; well below the H050 catastrophic 80%+ band).
**Best label cfg divergence**: ES converged on long-vertical (vol_lb=120m), high-PT (pt=1.0), wide-SL (sl=1.5); NQ converged on short-vertical (vol_lb=60m), tight-PT (pt=0.5), tight-SL (sl=1.0). Diverging best-cfg across symbols is consistent with ES having longer-decay edge and NQ having faster-decay edge — operator-readable and interpretable, but reflects 27-cell grid noise not signal.

### Mandatory KPIs not yet computed (deferred follow-ups; per ADR-0013 §3.1.2)

| KPI | Status | Follow-up |
|---|---|---|
| Sortino ratio | not computed | `P1-H052A-SORTINO-COMPUTE` (downside-deviation per Sortino & Price 1994) |
| Turnover (per-day) | n/a (1 round-trip per session by design) | — (turnover is 2 sides per session by construction; not informative) |
| Capacity estimate | not computed | `P1-H052A-CAPACITY-EMPIRICAL` (depends on cost model + slippage from paper-trade logs) |
| Cost-magnitude empirical calibration | constant 1-tick prior applied; calibration deferred | `P1-H052A-COST-CALIBRATION-EMPIRICAL` (regime-wise empirical fit from paper-trade logs) |
| Cost-floor sensitivity (1-tick vs 2-tick) | not computed at v1 | `P1-H052A-COST-FLOOR-SENSITIVITY` (re-run with `sensitivity_mult=2.0` on the existing artifacts) |
| Mediation / partial-R² | n/a (not applicable to H052a design) | — |
| Lo 2002 η(q) corrected annualization | session-level √252 used; lag-1 ρ correction not applied | `P1-H052A-LO-CORRECTED-ANNUALIZATION` (per-session lag-1 ρ on the OOS series; effect typically <2% for daily-cleared session-cadence) |

The deferred-follow-up annotation satisfies the rules/quant-project.md reporting mandate per ADR-0013 §3.1.2.

## Realized OOS + Forward-Projection block (MANDATORY per ADR-0013 §3.1)

> **Caveats** (binding per ADR-0013 §3.1):
> - **Cost model: APPLIED (cost-aware results, NOT cost-free upper bounds)** — per design.md §1 + §7 binding ("Sharpe ratios computed on walk-forward OOS net-of-cost session-cadence returns") + ADR-0013 §3.1 F-CONV-2 (log-return-drag application rule). The orchestrator at [scripts/run_h052a_walk_forward.py](../../../scripts/run_h052a_walk_forward.py) calls `FuturesOrbV1CostModel.cost_per_session_log_return(symbol=..., entry_price=..., n_contracts=1)` per session and subtracts the per-session log-return drag from `pnl_log` BEFORE writing the session-level returns table. The realized + projected numbers below are cost-aware under the constant-tick slippage prior (1-tick floor on entry + exit; per-side fee schedule from [config/instruments.yaml](../../../config/instruments.yaml)). Empirical cost-magnitude calibration tracked under `P1-H052A-COST-CALIBRATION-EMPIRICAL`.
> - **Position-sizing convention: first_hour_orb_futures_session_cadence** per ADR-0013 §3.1.1 sizing-convention table (First-hour ORB futures row): 1 contract per session, daily-cleared, single-leg long-only. Equity compounds at the session level (`equity_{t+1} = equity_t × exp(pnl_log_t)`); a no-leverage retail position is fixed-1-contract for the simulation (capacity ceiling per ADR-0001 is ≤20 ES / ≤40 NQ).
> - **Forward-projection horizon: 252 sessions (canonical for daily-cleared session-cadence per ADR-0013 §3.1)**. H052a substrate is session-cadence (1 round-trip per RTH session by design). The bootstrap operates directly on per-session log returns; PW2004 selects block-length on the level series; 3 of 4 cells select `b=1.0` (i.i.d. session bootstrap) and 1 cell (NQ unconditional) selects `b=1.30` (stationary block bootstrap per Politis-Romano 1994 with PPW 2009-corrected SB constants). Unlike H050 (bar-cadence), there is NO bar-vs-session understatement caveat here — the simulator operates at the natural ORB cadence.
> - **Bootstrap-as-generative-model**: forward distribution assumes 2026 session-level returns mirror the 2023-2024 OOS empirical distribution. Regime-shift risk and structural breaks beyond the OOS window are NOT modelled — see [Andrews 1993, Econometrica 61(4):821-856](https://doi.org/10.2307/2951764) for in-sample parameter-stability tests.
> - **Cross-reference**: T_H052a LW2008 CI from §"Sharpe-vs-unconditional differential" above COVERS zero on both symbols — the projection's elevated P(loss) on ES gated (54.84%) reflects the marginal-negative-edge of that arm, but the difference between gated and unconditional is within sampling error.

### Realized OOS ($10,000 starting capital; 2023-2024 OOS test fold)

| Symbol | Arm | Realized end | % change | Realized max-DD | W / L / Z sessions | Win rate (W/(W+L+Z)) |
|---|---|---:|---:|---:|---:|---:|
| ES | hmm_gated | $9,905.85 | -0.94% | 6.99% | 175 / 158 / 38 | 47.2% |
| ES | unconditional | $10,161.33 | +1.61% | 6.68% | 195 / 176 / 0 | 52.6% |
| NQ | hmm_gated | $10,338.73 | +3.39% | **11.83%** | 189 / 164 / 16 | 51.2% |
| NQ | unconditional | **$11,061.27** | **+10.61%** | 7.95% | 199 / 170 / 0 | 53.9% |

OOS session windows:
- ES: 2023-07-01 → 2024-12-31 (test fold per design.md §6); n_test_sessions=371
- NQ: 2023-07-01 → 2024-12-31 (test fold per design.md §6); n_test_sessions=369

### Forward 1-year projection ($10,000 → 252 sessions)

5,000 bootstrap MC paths × 252 sessions; rng_seed=20260423; PW2004-selected block-length per arm × symbol on the per-session level series.

| Symbol | Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) | block_b | method |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ES | hmm_gated | $9,942.80 | $9,952.48 | $8,742.58 | $9,118.69 | $10,852.55 | $11,246.76 | **54.84%** | 0% | 0% | 1.0 | iid_bootstrap |
| ES | unconditional | $10,112.78 | $10,131.56 | $8,774.98 | $9,136.67 | $11,193.15 | $11,662.87 | 42.94% | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | hmm_gated | $10,244.36 | $10,272.37 | $8,652.63 | $9,116.80 | $11,551.12 | $12,207.52 | 37.12% | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | unconditional | $10,729.27 | $10,766.49 | $8,902.67 | $9,442.41 | $12,239.43 | $12,914.52 | **18.56%** | 0% | 0% | 1.30 | stationary_bootstrap_PR1994 |

### Forward max-drawdown projection (% of peak)

| Symbol | Arm | Median DD | Mean DD | q05 | q95 |
|---|---|---:|---:|---:|---:|
| ES | hmm_gated | 5.85% | 6.32% | 2.91% | 11.22% |
| ES | unconditional | 6.09% | 6.64% | 3.16% | 11.89% |
| NQ | hmm_gated | 6.70% | 7.36% | 3.54% | 13.12% |
| NQ | unconditional | 6.36% | 6.92% | 3.50% | 12.43% |

Reference implementation: [scripts/run_h052a_walk_forward.py](../../../scripts/run_h052a_walk_forward.py) (orchestrator with embedded simulator; common forward-projection helpers tracked under `P1-FORWARD-PROJECTION-PRIMITIVE` for refactoring into `src/skie_ninja/inference/projection.py` per ADR-0013 §3.1.2).

### Operator interpretation (informational; per ADR-0013 §1 KPI-only philosophy)

- **NQ unconditional ORB** is the single positive cell on every metric: highest realised end equity (+10.61%), highest annualised Sharpe (+0.855), lowest forward-projection P(loss) (18.56%), median forward equity $10,729. Consistent with primary-literature unconditional ORB-on-futures (Holmberg-Lönnbark-Lundström 2013; Tsai 2019); see design.md §15.1 Erratum-2.
- **HMM regime-gating reduces but does not significantly damage performance** on this run: T_H052a < 0 in point estimate on both symbols, but LW2008 CI covers zero on both. The non-significant null is consistent with design.md §1's a-priori expectation ("a null is the expected outcome"). Compare to H050 where LW2008 CI excluded zero on the negative side on both symbols — the H050 HMM bar-level filter actively HARMED, while the H052a HMM session-level filter is statistically indistinguishable from unconditional at α=0.05.
- **Mechanism (mechanistic; informational; not load-bearing)**: the H052a HMM emission vector has 5 features (realized variance, first-hour sign, gap size, DOW one-hot, ETH pre-RTH return) plus the daily VIX join. The "non-stress state" `s=0` from the BIC-selected 3-state full-cov HMM picks low-realized-vol / first-hour-positive / small-gap sessions. These are not the high-edge ORB sessions; they're the consensus-low-volatility sessions. A first-hour ORB long-only signal extracts more edge from sessions with elevated realized vol AND positive first-hour sign (Lundström DiVA 732318 vol-state-conditioning prior-art per design.md §15.1 Erratum-3); the BIC-selected non-stress state filters in the wrong direction.
- **Pure-C# implementable**: NO. The HMM forward filter at session-open requires Python inference at decision time per ADR-0005 §"Fold-boundary state continuity". Per ADR-0013 §1.2, H052a's NinjaScript implementation will be **bridge-mediated** per ADR-0002: the C# strategy is a thin client invoking a Python inference service over the bridge at 10:30 ET each session, OR the C# strategy implements an unconditional first-hour ORB and the Python service publishes only the binary regime-gate signal pre-09:30 ET. Tracked under `P1-H052A-NINJASCRIPT-IMPL`.
- **Operator-promotion recommendation (operator-discretionary per ADR-0013 §5.3)**: H052a is a clean **non-significant null** for the gated arms. Per ADR-0013 §1, this does NOT exit the research loop — H052a progresses to NinjaScript implementation regardless. The bridge-mediated C# implementation will preserve the research-record-of-failure for any future operator review. **Two natural variants worth registering as successor hypotheses (NOT covered by this v1 emission)**:
  1. `P1-H052A-HMM-EMISSION-RECONSIDER` — Lundström-style vol-state-conditioning emission (replace the BIC-selected non-stress state with the high-realized-vol / positive-first-hour state) per design.md §15.1 Erratum-3 prior-art guidance.
  2. **NQ unconditional ORB as a standalone hypothesis** — the strongest cell here; pure-C# implementable (no HMM); appropriate as a `H052c` or successor with its own pre-reg.

**Cost-aware status: APPLIED (cost-aware results, NOT cost-free upper bounds)** per design.md §1 + §7 + ADR-0013 §3.1 F-CONV-2. Per-session log-return drag `log(1 - cost_round_trip / notional)` ≈ -3e-4 per session for ES (cost $29.10 / notional ~$240k at ES=4800) and ≈ -3e-4 per session for NQ (cost $14.10 / notional ~$340k at NQ=17000). Cost-magnitude empirical calibration from paper-trade logs is tracked under `P1-H052A-COST-CALIBRATION-EMPIRICAL`.

## Build / run history

| Stage | Commit / Run ID | Date | Sidecar SHA256 | Per-stage findings |
|---|---|---|---|---|
| Phase 0 ORB lit-check + §15 errata addendum (Path A) | `fa7b5c8` | 2026-05-04 | (audit trail [audit_trail_2026-05-04_h052a-orb-lit-check.md](../../../docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md)) | L-1 critical (Galli/Saavedra hallucinated; Pagani non-ORB misattribution); L-2 major (≈null pre-supposition contradicted by Holmberg 2013 + Tsai 2019); L-3 major (Lundström vol-state-conditioning prior-art uncited); L-4 minor (60-min OR window not literature-canonical). All 4 dispositioned via §15.1 errata addendum (Path A frozen-pre-reg amendment discipline; §1-§7 immutable). |
| Phase 1 dedicated orchestrator + features + cost model | `6e87a9d` | 2026-05-04 | (audit trail [audit_trail_2026-05-04_h052a-phase-1-infrastructure.md](../../../docs/audits/audit_trail_2026-05-04_h052a-phase-1-infrastructure.md)) | R2 ACCEPT. 5 critical + 9 major remediated: F-Q-1 (Hansen SPA API), F-Q-2 (LW2008 API), F-Q-3 (ETH bars filtered), F-Q-4 (HMM cold-start ADR-0005 violation), F-Q-5 (single calendar val split), R-1 (BLAS pinning), F-L-1/F-L-2/F-L-3 (ADR-0014 §3.2 misattributions corrected to ADR-0013 §3.1.1 + §3.1 F-CONV-2). |
| Phase 2 build-defect remediation chain | `583a4ee` → `27ed41d` → `3f2330a` → `20e6450` → `0aa9258` | 2026-05-05 | (audit trail [audit_trail_2026-05-05_h052a-phase-2-build-defects.md](../../../docs/audits/audit_trail_2026-05-05_h052a-phase-2-build-defects.md)) | 5 build defects fixed under audit-remediate-loop discipline. 1st launch: 27-min stall via O(N²) labeller (Polars==-style per-session boolean mask × 2710 sessions; fixed via `pd.factorize` + change-points). 2nd launch: pd.merge_asof MergeError (μs-vs-ms VIX dtype). 3rd: polars.join SchemaError (μs-vs-ns inter-feature-block). 4th: orchestrator labels↔features SchemaError (μs-vs-ns). 5th: HMMParams.n_states method-vs-attribute TypeError. 6th: clean exit 0. |
| **Production walk-forward (Stage-3 v1; this report's source)** | **`0aa9258` / run_id `184eccd67bf24d71990265d39c28daf0`** | **2026-05-05 11:44:43** | **scientific_payload `cca86b27...`; ReproLog model_hash `cca86b27...`** | **First clean H052a production walk-forward (~14 min wall-clock, much faster than the ~1-2hr/symbol pre-launch estimate due to ORB session cadence vs H050 bar cadence). Both symbols ok; ES 27/27 cfgs + NQ 27/27 cfgs. T_H052a < 0 on both symbols, LW2008 differential CI COVERS zero on both — non-significant null.** |
| §3.1 Realized-OOS + Forward-Projection (this report) | (same run_id) | 2026-05-05 | (this card) | Bootstrap simulation embedded in orchestrator (per Phase 1 R2 ACCEPT design); 5,000 paths × 252 sessions × 4 cells; PW2004-selected block-lengths per arm × symbol (3 cells `b=1.0`, 1 cell `b=1.30`). |

## Failure log entries (cross-referenced)

The full per-strategy failure log is at [failure_log.md](failure_log.md). Phase 2 build-defect entries 1-6 created in this commit.

## Audit-remediate-loop trails

| Round-set | Trail path | Verdict | Findings |
|---|---|---|---|
| Phase 0 ORB lit-check (R1+R2) | [audit_trail_2026-05-04_h052a-orb-lit-check.md](../../../docs/audits/audit_trail_2026-05-04_h052a-orb-lit-check.md) | R2 ACCEPT (4/4 dispositioned via §15.1 errata addendum) | Round-1: 1 critical + 2 major + 1 minor. Round-2: §15.1 errata addendum drafted + verified. |
| Phase 1 dedicated orchestrator (R1+R2) | [audit_trail_2026-05-04_h052a-phase-1-infrastructure.md](../../../docs/audits/audit_trail_2026-05-04_h052a-phase-1-infrastructure.md) | R2 ACCEPT (14/14 closures verified) | Round-1: 5 critical + 9 major + 11 minor + 6 lit-check + 9 repro. Round-2: all 14 critical+major remediated; verification ACCEPT. |
| Phase 2 build-defect remediation (R1+R2) | [audit_trail_2026-05-05_h052a-phase-2-build-defects.md](../../../docs/audits/audit_trail_2026-05-05_h052a-phase-2-build-defects.md) (this commit) | R2 ACCEPT (5/5 build defects remediated; 6th launch exit 0) | Round-1: 5 build defects across 5 sequential launches (1: O(N²) labeller; 2: VIX dtype; 3: feature panel precision; 4: orchestrator join precision; 5: HMMParams API). Round-2: 6th launch clean. |
| KPI report card v1 (this report; pending Round-3 verification) | [audit_trail_2026-05-05_h052a-kpi-report-v1.md](../../../docs/audits/audit_trail_2026-05-05_h052a-kpi-report-v1.md) (TBD on next audit-remediate-loop) | TBD | TBD |

## Cross-validation methodology (per ADR-0013 §7)

H052a's pre-registered splitter is `PurgedWalkForwardSplitter` per design.md §6 (rolling, single outer fold). The 5 ADR-0012 CPCV acceptance criteria are preserved as KPI annotations per ADR-0013 §7:

| ADR-0012 criterion | Status for H052a |
|---|---|
| #1 minimum 45 paths at C(10,2) | n/a — H052a uses walk-forward, not CPCV. CPCV escalation is registered as a successor-hypothesis-ID design change. |
| #2 KS-monotonicity ≤ 0.05 by 30 paths | n/a — same |
| #3 per-path Sharpe distribution moments | n_folds=1 (single outer fold per design.md §6) so no path distribution. |
| #4 24-hour wall-clock cap with downsample fallback | Met: ~14 min wall-clock total. |
| #5 DSR computed under CPCV path distribution | n/a (M=1; ADR-0008 single-strategy degenerate handling). |

Walk-forward configuration:
- **Outer**: train 2020-2022, val 2023-H1, test 2023-H2 + 2024 (per design.md §6 + [config/hypotheses/H052a.yaml](../../../config/hypotheses/H052a.yaml))
- **Inner CV** (label cfg selection): 3 folds, purge=embargo=1 session each (per F-Q-5 Phase 1 fix)
- **Mode**: rolling
- **Purge / embargo**: 1 session each (sufficient given session-cadence; futures-ORB has no AFML §7.4 multi-bar label horizon)

## Cross-links

- ReproLog: [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../../../logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json) ✓
- Sidecar: [artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/sidecar.json](../../../artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/sidecar.json)
- Per-symbol metrics summary: [artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/ES_metrics_summary.json](../../../artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/ES_metrics_summary.json), [NQ_metrics_summary.json](../../../artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/NQ_metrics_summary.json)
- Scientific payload SHA: [artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/scientific_payload_sha256.txt](../../../artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/scientific_payload_sha256.txt) = `cca86b2746e5cb1bc62984352d21d2a55c182ed779fe3f741da52bfa52e60442`
- Pre-registered design: [design.md](design.md)
- §15 errata addendum: [design.md §15.1](design.md#151-citation-errata-phase-0-orb-lit-check-2026-05-04-findings-l-1-through-l-4)
- Orchestrator: [scripts/run_h052a_walk_forward.py](../../../scripts/run_h052a_walk_forward.py) (SHA256 `de3a41e7...`)
- Cost model: [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py)
- Labeller: [src/skie_ninja/features/labels.py](../../../src/skie_ninja/features/labels.py) `OpeningRangeBreakoutLabeller`
- Features: [src/skie_ninja/features/h052a/features.py](../../../src/skie_ninja/features/h052a/features.py)
- VIX ingest: [src/skie_ninja/data/ingest/vix_daily.py](../../../src/skie_ninja/data/ingest/vix_daily.py)
- Cross-hypothesis SPA panel: NOT YET BUILT; tracked under `P1-CROSS-HYPOTHESIS-SPA-PANEL`
- Cross-strategy comparability table: NOT YET BUILT; tracked under `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD`

## Versioning

This is **v1** — the first H052a KPI report card emission per ADR-0013 §3.

A version increment to v2 would be triggered by: cost-magnitude empirical calibration (`P1-H052A-COST-CALIBRATION-EMPIRICAL`), cost-floor sensitivity sweep (`P1-H052A-COST-FLOOR-SENSITIVITY` at sensitivity_mult=2.0), Sortino/capacity computation, Lo-corrected annualization, paper-trade-evaluated stage transition adding the realized-Sharpe-vs-backtest observation, NinjaScript-parity-check artifact emission per ADR-0013 §5.2, or any other substantive KPI change.

Per ADR-0013 §4.1 non-loss mandate: this v1 is preserved verbatim under any future v2+ emission.

## Operator review section (filled at promotion time per ADR-0013 §5.3)

- **Operator**: skoir
- **Promotion decision**: TO BE FILLED at next stage transition (`kpi-report-emitted` → `ninjascript-implemented`)
- **Rationale**: TO BE FILLED — operator review of this v1 KPI report card values + 2026 forward projection. Per the user's 2026-05-04 standing directive ("The failure of profit and projected profit negates our need to move onto ninjascript implementation. This will be the user's discretion upon presentation of results in the canonical format"), the next stage transition is operator-discretionary, NOT auto-mandated.
- **Methodological-correctness acknowledgments**: NOT REQUIRED (no `leakage-canary-fail`, `repro-log-incomplete`, or `post-run-audit-fail` annotations)
- **Cross-link to promotion log**: TBD (path: `logs/promotions/{run_id}_H052a_{arm_id}_promotion.md`)
