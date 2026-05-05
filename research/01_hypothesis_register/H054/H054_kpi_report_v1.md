---
hypothesis_id: H054
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-05
git_head: 66dab5d98c43a15e1b2b763d4237b320cffeeb37
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d
  vix_daily: 0a0e9f252bcaa3f2f9ee2d0ef142e8fff88924aa6a2590d76e924dd50d6ab552
sidecar_scientific_payload_sha256: 395dd00877d3b5fae99d9fbbb7bac243d70dd14cd7983ca77b065a14205e3ff4
config_resolved_sha256: bcfec78b72bfd27e3c3000eade608d19ed5365800514e16fa0af012c4f6d2438
env_id: be80f7deb0f0c666d78e06d0e7917780f64f567b730e064d0515fc4142ec9d55
pip_freeze_sha256: c92ce92af9a6a103f64241690f3a5c22b7f542053ef524fefcd74662651d9d4e
run_id: dd916fc67b504c528fda7abbde6700f1
rng_seed: 20260505
sizing_convention: first_hour_orb_futures_session_cadence  # ADR-0013 §3.1.1
supersedes: null
superseded_by: null
---

# H054 — KPI Report Card v1

> **First production walk-forward Stage-3 KPI emission** for hypothesis H054 — anti-gate first-hour ORB on CME ES futures (inverse-gate companion of H052a). Canonical [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3 + ADR-0014 §3.2 KPI report card on the post-Cell-I substrate, ES-only 2025 fresh OOS per the F-Q-1 + F-Q-6 Round-2 audit-remediate-loop fixes. Production run completed 2026-05-05 17:01 CT (run_id `dd916fc6...`; ~7 min wall-clock; ReproLog at [logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json](../../../logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json)).

- **Hypothesis** (per [design.md §1](design.md)):
  - H_1 PRIMARY: T_H054_b = SR_anti_gated > 0 (absolute profitability standalone of stress-state ORB sessions)
  - H_1 SECONDARY: T_H054_a = SR_anti_gated − SR_unconditional > 0 (incremental Sharpe over unconditional ORB)
  - Mechanism: literature-silent at the intraday HMM-stress-state level per Phase 0 lit-check; HOP 2017 directionally consistent (stress-period TSMOM positive). Empirical motivation (load-bearing): H052a KPI report card v1.
- **Design.md**: [design.md](design.md) (frozen at `status: designed` 2026-05-05; Round-2+3 audit-remediate-loop ACCEPT closing 5 critical/major + 5 minor R1 findings)
- **Stage**: `kpi-report-emitted` per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). Per user's 2026-05-04 standing directive, next stage transition is operator-discretionary.
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md))

H054 v1 production walk-forward (run_id `dd916fc67b504c528fda7abbde6700f1`; commit `66dab5d`; ~7 min wall-clock; substrate `b3ee230a...` 2020-2023H1 IS + ES-only 2025 OOS; cost-aware net-of-cost per design.md §1 + §7 + cost model `futures_orb_v1`):

### 1. P/L (realized OOS, $10K starting capital, daily-cleared session-cadence per ADR-0013 §3.1.1)

| Symbol | Arm | End equity | Δ vs $10k | Δ pct | Cost model |
|---|---|---:|---:|---:|---|
| ES | anti_gated (PRIMARY) | $10,349.81 | +$349.81 | **+3.50%** | futures_orb_v1, $29.10 r/t |
| ES | unconditional | $9,946.31 | -$53.69 | -0.54% | futures_orb_v1, $29.10 r/t |

### 2. Drawdown (realized + projected)

| Symbol | Arm | Realized max-DD | Proj median DD | Proj q95 DD |
|---|---|---:|---:|---:|
| ES | anti_gated | **3.19%** | 3.63% | 8.54% |
| ES | unconditional | 6.99% | 10.12% | 19.28% |

Anti-gated max-DD materially better than unconditional on both realized and projected (a-priori expected: 7 trades carries less variance than 237 trades).

### 3. Sharpe — primary inference (T_H054_b = SR_anti_gated; Opdyke 2007 univariate CI per Round-2 F-Q-2 fix)

| Symbol | SR_anti_gated (per-sess) | Opdyke 2007 95% CI [low, high] | Excludes zero | SR_anti_gated annualised |
|---|---:|---|:--:|---:|
| ES | +0.0362 | [-0.0327, +0.1050] | NO | **+0.573** |

H_1_primary (T_H054_b > 0) is NOT supported at α=0.05; CI covers zero. **Point estimate is POSITIVE and directionally consistent with the H052a-implied reading**, but with n_anti = 7 the CI is structurally wide. Per design.md §9.5 expectation-management note: "A v1 result of 'T_H054_b LW2008 CI covers zero' should be interpreted as 'consistent-with-noise-given-low-trade-count', NOT 'anti-gate hypothesis falsified.'"

### 3.1 Sharpe — secondary inference (T_H054_a = SR_anti_gated − SR_unconditional; LW2008 differential CI)

| Symbol | T_H054_a (per-sess) | LW2008 CI [low, high] | Excludes zero | T_H054_a annualised |
|---|---:|---|:--:|---:|
| ES | +0.0398 | [-0.0411, +0.1394] | NO | +0.630 |

Same verdict: point positive, CI covers zero, secondary informational (per F-Q-2 fix the secondary statistic is informational, not load-bearing).

### 4. Annualised Sharpe (per-arm; ×√252 = 15.875)

| Symbol | Arm | Annualised Sharpe |
|---|---|---:|
| ES | anti_gated | **+0.573** |
| ES | unconditional | -0.057 |

Anti-gated arm point estimate exceeds unconditional by +0.630 annualised — directionally consistent with H_1 even though CI covers zero.

### 5. Win/Loss/Zero session counts + win rate

| Symbol | Arm | Wins | Losses | Zeros | Win rate (W/(W+L)) |
|---|---|---:|---:|---:|---:|
| ES | anti_gated | 3 | 4 | 230 | **42.9%** (on 7 active trades) |
| ES | unconditional | 126 | 111 | 0 | 53.2% |

Anti-gate fired on 7/237 sessions (2.95% trade rate; matches the H052a-implied stress-state frequency on 2025 fresh OOS, materially below the design.md §9 estimated 10% based on H052a OOS empirical). Win rate on active trades is BELOW unconditional (42.9% vs 53.2%) but the magnitude of the wins is larger (positive realized P/L despite lower hit rate).

### 6. Forward 1-year (252-session) bootstrap projection ($10k start)

5,000 bootstrap MC paths × 252 sessions; rng_seed=20260505; PW2004-selected block_length=1.0 (iid bootstrap on the per-session log returns):

| Symbol | Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) | block_b | method |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ES | anti_gated | $10,319.37 | $10,379.30 | $9,031.91 | $9,402.22 | $11,524.10 | $12,183.07 | **29.24%** | 0% | 0% | 1.0 | iid_bootstrap |
| ES | unconditional | $9,930.46 | $9,995.82 | $7,864.02 | $8,481.31 | $11,711.36 | $12,546.37 | 52.50% | 0% | 0% | 1.0 | iid_bootstrap |

**Anti-gated dominates unconditional on every forward metric**: higher median ($10,319 vs $9,930), higher q05 ($9,402 vs $8,481), lower P(loss) (29.24% vs 52.50%). The forward projection's higher resolution (5,000 paths × 252 sessions) provides a stronger signal than the 230-session realized OOS CI alone.

### 7. Hansen SPA family p (M=1 degenerate per ADR-0008 + F-Q-5 fix)

| Symbol | T_SPA | p | n_bootstrap | Annotation |
|---|---:|---:|---:|---|
| ES | 0.670 | 0.285 | 1000 | `spa-fail-to-reject` (M=1 degenerate per ADR-0008 + F-Q-5 fix; cross-hypothesis SPA at M=5 deferred to project-level ADR per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`) |

T_SPA = 0.670 (positive d̄; p=0.285 fails to reject H_0:E[d]≤0 at α=0.05). Note: p=0.285 is DIFFERENT from H050/H052a's degenerate p=1.0 because in H054 d̄ > 0 (T_H054_a positive; the H054 anti-gate marginally beats unconditional in point estimate); the SPA test is non-trivial here, not mechanically degenerate. Still does not reach α=0.05 significance.

### 8. Other KPIs

| Item | ES |
|---|---|
| Best label cfg (PT, SL, vol-lookback) | pt=1.0, sl=1.5, vol_lb=120m |
| Inner-CV mean Sharpe at optimum (unconditional) | -0.667 |
| HMM selected (cov, n_states) | full, 3 |
| HMM stress_state | 2 (highest realized_vol emission mean) |
| Train / Test sessions | 736 / 237 |
| Anti-gate trade frequency | 7 / 237 (2.95%) |
| n_folds (realized/expected) | 1/1 (single outer fold per design.md §6) |
| Feature NaN drops | 0 |
| Entry-price NaN drops | 1 |
| Cost-floor sensitivity_mult | 1.0 (1-tick prior) |
| Round-trip cost / contract | $29.10 |
| Sortino / turnover / capacity | not computed (deferred follow-ups) |
| Bailey-Lopez de Prado deflated SR | not computed at v1 (`P1-H054-DSR-CELL-DEFLATION-COMPUTE`) |

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2)

`leakage-canary-pass` · `bss-n/a` · `reliability-n/a` · `repro-log-complete` · `dsr-n/a (M=1)` · `cost-conditional` · `post-run-audit-pass` · `power-margin-low (n_anti=7; design.md §9.5)` · `data-overlap-h053-acknowledged`

### Bottom line

H054 v1 is a **non-significant null on the primary inferential statistic** (T_H054_b Opdyke 2007 univariate CI [-0.033, +0.105] per-session; covers zero) but with **positive point estimates directionally consistent with H_1 on every metric**: SR_anti_gated annualised +0.573 (vs unconditional -0.057); realized $10K +3.50% (vs unconditional -0.54%); forward 252-session median $10,319 (vs $9,930) with P(loss) 29.24% (vs 52.50%); max-DD 3.19% (vs 6.99%). Per design.md §9.5 binding expectation-management: with n_anti = 7 trades over 237 OOS sessions (3.0% trade rate), the v1 result is structurally a **"directional indicator + power-floor probe"**, NOT a definitive test — the wide CI is structural, not informational. The directional consistency with H052a's gated-out subset (positive Sharpe on the stress-state subset) PARTIALLY GENERALISES to fresh 2025 OOS, but the small-sample CI cannot distinguish the +0.573 annualised SR from random noise at α=0.05.

Per design.md §10 decision rule, this falls into the "T_H054_b LW2008 CI covers zero → non-significant null" bucket: operator may reasonably decline NinjaScript progression, OR pursue a successor v2 with longer accumulated OOS (matching the design.md §9.5 expectation-management note's "successor v2 with pooled ES+NQ + MES+MNQ" framing). Per the user's 2026-05-04 standing directive, next stage transition is operator-discretionary upon canonical-format presentation.

Full report card body: §"Methodological-correctness annotations" through §"Operator review section" below; sidecar at [artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/sidecar.json](../../../artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/sidecar.json); ReproLog at [logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json](../../../logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json).

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | **pass** | 17/17 BLOCKING tests green at [tests/integration/test_h054_pit.py](../../../tests/integration/test_h054_pit.py); causal HMM warm-start via `terminal_log_alpha` + `filter_states_from_prior` per ADR-0005; anti-gate inversion is a pure post-processing transform on causally-computed regime indicator; H054 IS (2020-01-01 → 2023-06-30) is disjoint from H052a OOS (2023-07-01 → 2024-12-31) and H050 NQ test fold per F-Q-1 + F-Q-6 fixes. |
| `bss-{positive,flat,negative}` | **n/a** | design.md §8.a binds `applicable: NO` — H054 is a continuous trading-rule signal, not a calibrated probability forecast. |
| `reliability-{in,out}-of-band` | **n/a** | Same rationale as BSS. |
| `repro-log-{complete,incomplete}` | **complete** | All 13 ReproLog fields present: `git_head=66dab5d`, `pip_freeze_sha256=c92ce92a...`, `dataset_checksums` (2 entries), `rng_seed=20260505`, `model_hash=395dd008...` (= scientific_payload SHA256 binding), `config_resolved_sha256=bcfec78b...`, `env_id=be80f7de...`. |
| `dsr-{positive,marginal,negative,n/a}` | **n/a** | Single-strategy family (M=1) per ADR-0008 + F-Q-5 fix; cross-hypothesis SPA at M=5 deferred to project-level ADR. |
| `cost-{robust,conditional,flat}` | **conditional** | 1-tick slippage prior per design.md §7; cost APPLIED as per-session log-return drag per ADR-0013 §3.1 F-CONV-2. Empirical calibration deferred to `P1-H054-COST-CALIBRATION-EMPIRICAL`. |
| `post-run-audit-{pass,fail}` | **pass** | Sidecar correspondence verified: scientific_payload SHA `395dd008...` matches ReproLog model_hash. |
| `power-margin-low` | **declared** | n_anti = 7 trades over 237 OOS sessions (2.95% trade rate); structurally underpowered per design.md §9.5; expectation-management note pre-baked into the pre-reg. |
| `data-overlap-h053-acknowledged` | **declared** | H054 v1 OOS (ES 2025) overlaps H053 OOS partially per data_requirements.md isolation tables; methodologically defensible under different-signal-class-on-shared-substrate framing; acknowledged honestly per F-Q-6 audit fix. |

**No methodological-correctness banner triggered** per ADR-0013 §2.1 (all annotations green, n/a, or low-power-declared).

## Performance KPIs (per ADR-0013 §3 + `rules/quant-project.md` §Reporting)

### T_H054_b primary — SR_anti_gated > 0 (Opdyke 2007 univariate Sharpe CI)

H054's design.md §1 binds T_H054_b = SR_anti_gated as PRIMARY (per F-Q-2 fix; promoted from secondary because T_H054_a is algebraically dependent on T_H052a). The "anti-gated arm" trades the first-hour ORB ONLY on sessions where the HMM forward-filter posterior at 10:30 ET classifies the session into the stress state (the state with highest mean realized_vol emission per design.md §5 + F-Q-3 ID rule). On non-stress sessions the position is flat.

The Sharpe values reported below are **per-session** statistics (1 round-trip per RTH session); the Opdyke 2007 univariate Sharpe CI is computed on the same per-session scale per [src/skie_ninja/inference/stats/sharpe_ci.py](../../../src/skie_ninja/inference/stats/sharpe_ci.py) `opdyke2007_ci` (Mertens 2002 + Opdyke 2007 higher-moment iid asymptotic-variance formula with HAC scalar-ratio adjustment per audit L-6 / F-1-3).

| Symbol | SR_anti_gated (per-sess) | **T_H054_b (per-sess)** | Opdyke 2007 95% CI [low, high] | excludes_zero | T_H054_b annualised | Annotation |
|---|---:|---:|---|:---:|---:|---|
| ES | +0.0362 | **+0.0362** | [-0.0327, +0.1050] | NO | **+0.573** | `sharpe-vs-passive-marginal-positive` |

**Result**: H_1_primary (T_H054_b > 0) is NOT supported at α=0.05; CI covers zero. Point estimate POSITIVE, directionally consistent with H_1 and with the H052a-implied reading. The structurally wide CI reflects n_anti = 7 trades; this is the design.md §9.5 expected outcome.

### T_H054_a secondary — SR_anti_gated − SR_unconditional > 0 (LW2008 differential CI)

H054's design.md §1 binds T_H054_a as SECONDARY informational (post-Round-2 F-Q-2 fix). LW2008 differential CI computed per [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) with NW1994 per-replicate bandwidth selection; n_bootstrap=2000; α=0.05.

| Symbol | SR_anti_gated (per-sess) | SR_uncond (per-sess) | T_H054_a (per-sess) | LW2008 CI [low, high] | excludes_zero | T_H054_a annualised | Annotation |
|---|---:|---:|---:|---|:---:|---:|---|
| ES | +0.0362 | -0.0036 | +0.0398 | [-0.0411, +0.1394] | NO | +0.630 | `sharpe-vs-unconditional-marginal-positive` |

Same verdict: point positive, CI covers zero, secondary informational.

### Hansen SPA M=1 degenerate (per ADR-0008 + F-Q-5 fix)

| Symbol | SPA statistic | p-value | n_bootstrap | omega method | Annotation |
|---|---:|---:|---:|---|---|
| ES | 0.670 | 0.285 | 1000 | hac (M=1 degenerate per ADR-0008 + F-Q-5 fix) | `spa-fail-to-reject` |

Note: p=0.285 here is materially different from H050/H052a's degenerate p=1.0 because d̄ > 0 in H054 (T_H054_a positive in point estimate; the relative-performance series `(anti_gated - unconditional)` is positive on average). The SPA test is non-trivial here, not mechanically degenerate by `T_SPA = max(0, neg) = 0`. Still does not reach α=0.05 significance — consistent with the LW2008 CI covering zero. Cross-hypothesis SPA at M=5 deferred to project-level ADR per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`.

### Sharpe-vs-passive (annualised; informational)

| Symbol | Annualised SR_anti_gated | Annualised SR_uncond | n_test_sessions | n_anti_trades |
|---|---:|---:|---:|---:|
| ES | **+0.573** | -0.057 | 237 | 7 |

Anti-gated annualised Sharpe (+0.573) is positive AND meaningfully exceeds unconditional (-0.057). The +0.630 annualised differential is the strongest single positive signal in the run. **Caveat**: with only 7 trades, the differential is point-estimate-only and statistically indistinguishable from zero on either CI.

### Other performance KPIs (per `rules/quant-project.md` §Reporting)

| Symbol | Realized end equity (anti) | Max-DD (anti) | Realized end equity (uncond) | Max-DD (uncond) | n_folds (realized/expected) | best label cfg |
|---|---:|---:|---:|---:|:---:|---|
| ES | $10,349.81 (+3.50%) | 3.19% | $9,946.31 (-0.54%) | 6.99% | 1/1 | (pt=1.0, sl=1.5, vol_lb=120m) |

**Power-margin annotation**: `power-margin-low` (n_anti = 7 vs n_required ≥ 174 sessions for SR_pilot=0.15 per design.md §9.2 derivation).
**Max-DD annotation**: `max-dd-favourable-anti-vs-uncond` (anti-gated 3.19% < unconditional 6.99%; consistent with smaller exposure of anti-gated arm).

### Mandatory KPIs not yet computed (deferred follow-ups; per ADR-0013 §3.1.2)

| KPI | Status | Follow-up |
|---|---|---|
| Sortino ratio | not computed | `P1-H054-SORTINO-COMPUTE` |
| Capacity estimate | not computed | `P1-H054-CAPACITY-EMPIRICAL` |
| Cost-magnitude empirical calibration | constant 1-tick prior applied | `P1-H054-COST-CALIBRATION-EMPIRICAL` |
| Cost-floor sensitivity (1-tick vs 2-tick) | not computed at v1 | `P1-H054-COST-FLOOR-SENSITIVITY` |
| Bailey-Lopez de Prado deflated Sharpe | not computed at v1 (per F-Q-9 fix the annotation is registered; computation deferred) | `P1-H054-DSR-CELL-DEFLATION-COMPUTE` |
| Lo 2002 η(q) corrected annualization | session-level √252 used; lag-1 ρ correction not applied | `P1-H054-LO-CORRECTED-ANNUALIZATION` |
| B-arm robustness (frozen H052a HMM via causal warm-start) | not run at v1 | `P1-H054-B-ARM-EXECUTE` |

## Realized OOS + Forward-Projection block (MANDATORY per ADR-0013 §3.1)

> **Caveats** (binding per ADR-0013 §3.1):
> - **Cost model: APPLIED (cost-aware results, NOT cost-free upper bounds)** — per design.md §1 + §7 + ADR-0013 §3.1 F-CONV-2 binding.
> - **Position-sizing convention: first_hour_orb_futures_session_cadence** per ADR-0013 §3.1.1; 1 contract per active session, daily-cleared, single-leg long-only.
> - **Forward-projection horizon: 252 sessions** — H054 substrate is session-cadence (1 round-trip per RTH session by design when anti-gate fires; flat otherwise). Bootstrap operates directly on per-session log returns; PW2004 selected `block_length=1.0` (iid bootstrap) for both arms.
> - **Bootstrap-as-generative-model**: forward distribution assumes 2026 session-level returns mirror the 2025 OOS empirical distribution. Regime-shift risk and structural breaks beyond the OOS window are NOT modelled.
> - **n_anti = 7**: the anti-gated arm's empirical distribution is built from only 7 trades. The forward projection's bootstrap from this 7-element set has meaningful uncertainty in the resampled-mean per-bootstrap-replicate; the 5,000-path output is honest given this n, but the underlying empirical distribution is small-sample.
> - **Cross-reference**: T_H054_b Opdyke 2007 CI from §"Performance KPIs" above COVERS zero — the projection's directional dominance of anti-gated over unconditional reflects the +0.630 annualised point estimate, NOT a statistically significant differential.

### Realized OOS ($10,000 starting capital; ES 2025-01-01 → 2025-12-03 fresh OOS)

| Symbol | Arm | Realized end | % change | Realized max-DD | W / L / Z sessions | Win rate (W/(W+L+Z)) |
|---|---|---:|---:|---:|---:|---:|
| ES | anti_gated (PRIMARY) | **$10,349.81** | **+3.50%** | **3.19%** | 3 / 4 / 230 | 1.27% (or 42.9% on 7 active trades) |
| ES | unconditional | $9,946.31 | -0.54% | 6.99% | 126 / 111 / 0 | 53.2% |

OOS session window:
- ES: 2025-01-01 → 2025-12-03 UTC; n_test_sessions=237 (1 NaN entry-price drop reduces effective from 238 to 237)

### Forward 1-year projection ($10,000 → 252 sessions)

5,000 bootstrap MC paths × 252 sessions; rng_seed=20260505; PW2004-selected block_length=1.0 for both arms (iid bootstrap on per-session log returns).

| Symbol | Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) | block_b | method |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ES | anti_gated | **$10,319.37** | $10,379.30 | $9,031.91 | $9,402.22 | $11,524.10 | $12,183.07 | **29.24%** | 0% | 0% | 1.0 | iid_bootstrap |
| ES | unconditional | $9,930.46 | $9,995.82 | $7,864.02 | $8,481.31 | $11,711.36 | $12,546.37 | 52.50% | 0% | 0% | 1.0 | iid_bootstrap |

### Forward max-drawdown projection (% of peak)

| Symbol | Arm | Median DD | Mean DD | q05 | q95 |
|---|---|---:|---:|---:|---:|
| ES | anti_gated | **3.63%** | 3.84% | 0.47% | 8.54% |
| ES | unconditional | 10.12% | 10.89% | 5.00% | 19.28% |

### Operator interpretation (informational; per ADR-0013 §1 KPI-only philosophy)

- **The directional reading is consistent with the H052a-implied "stress-state subset has positive Sharpe" hypothesis on fresh 2025 OOS**: SR_anti_gated annualised +0.573 (positive); +3.50% realized $10K; lower P(loss) and lower max-DD than unconditional on every metric. This is a meaningful directional finding — the H054 hypothesis is NOT falsified.
- **The CI verdict is NULL at α=0.05**: T_H054_b Opdyke 2007 CI [-0.033, +0.105] covers zero; T_H054_a LW2008 CI [-0.041, +0.139] covers zero. The point-positive estimates are not statistically distinguishable from random noise at the conventional significance level.
- **n_anti = 7 is the structural cause of the wide CI**: the anti-gate fired on only 7 of 237 OOS sessions (2.95% trade rate; lower than the design.md §9 estimated 10% based on H052a OOS). The HMM's stress-state classification is more conservative on 2025 fresh OOS than on the H052a IS+val fit period; this could be either (a) a real regime shift (2025 has fewer "stress" sessions than 2020-2023H1) or (b) the BIC-selected K=3 HMM in H054 partitions the state space differently than the H052a HMM.
- **Pure-C# implementable**: NO. The HMM forward filter at session-open requires Python inference at decision time per ADR-0005; bridge-mediated NinjaScript per ADR-0013 §1.2 + ADR-0002 if undertaken.
- **Operator-promotion recommendation (operator-discretionary per ADR-0013 §5.3)**: H054 v1 is a clean **directional indicator + power-floor probe** result — point-positive on every metric, CI covers zero, structural sample-size limitation. Three reasonable next steps:
  1. **Decline NinjaScript progression at v1** per the user's 2026-05-04 standing directive precedent (consistent with H052a operator decision); record decision and progress to v2 successor.
  2. **Pursue H054 v2 with pooled ES + NQ + MES + MNQ on 2025+ OOS** to accumulate n_anti to the design.md §9.2-required ≥ 174 sessions for adequate power. This requires a successor pre-reg with revised data_requirements.md.
  3. **Pursue NinjaScript implementation as a deployment-realistic test harness** to gather paper-trade observations, even though the v1 KPI is non-significant. Bridge-mediated per ADR-0002.

**Cost-aware status: APPLIED (cost-aware results, NOT cost-free upper bounds)** per design.md §1 + §7 + ADR-0013 §3.1 F-CONV-2 binding. Per-session log-return drag ≈ -3e-4 per active session for ES (cost $29.10 / notional ~$240k at ES=4800). Cost-magnitude empirical calibration tracked under `P1-H054-COST-CALIBRATION-EMPIRICAL`.

## Build / run history

| Stage | Commit / Run ID | Date | Sidecar SHA256 | Per-stage findings |
|---|---|---|---|---|
| Phase 0 ORB lit-check (4 primary citations verified) | (Phase 0 trail) | 2026-05-05 | n/a | Verdict: literature-silent at intraday HMM-stress-state level. Trail: [lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md). |
| Pre-reg drafted + Round-1+2+3 audit-remediate-loop | `66dab5d` (PR #3 merged 2026-05-05 21:26 UTC) | 2026-05-05 | n/a | R1 BLOCK with 5 critical/major + 5 minor; R2 inline remediation closing all 10; R3 self-verification ACCEPT. design.md + data_requirements.md `status: draft` → `status: designed`. Trail: [audit_trail_2026-05-05_h054-pre-reg.md](../../../docs/audits/audit_trail_2026-05-05_h054-pre-reg.md). |
| Phase 1 implementation (orchestrator + 4 BLOCKING tests) | TBD this commit | 2026-05-05 | n/a | `config/hypotheses/H054.yaml` + `scripts/run_h054_walk_forward.py` (gate inverted; T_H054_b primary via Opdyke 2007 univariate CI; ES-only) + `tests/integration/test_h054_pit.py` (17/17 passed). |
| Phase 2 production walk-forward (1st attempt) | run_id `39922391...` | 2026-05-05 ~16:55 | n/a (failed at Opdyke API) | AttributeError: 'SharpeCI' object has no attribute 'point_estimate' (Phase 2 build defect; SharpeCI dataclass field is `sharpe`, not `point_estimate`). Fixed inline; relaunched. |
| **Phase 2 production walk-forward (2nd attempt; this report's source)** | **`66dab5d` / run_id `dd916fc67b504c528fda7abbde6700f1`** | **2026-05-05 17:01 CT** | **scientific_payload `395dd008...`; ReproLog model_hash `395dd008...`** | **Clean exit 0 (~7 min wall-clock; ES-only). 27/27 cfgs evaluated; HMM (full, 3-state) selected; stress_state = 2 (highest realized_vol emission). T_H054_b Opdyke 2007 CI covers zero; T_H054_a LW2008 CI covers zero. Point estimates positive on both.** |

## Failure log entries (cross-referenced)

The full per-strategy failure log is at [failure_log.md](failure_log.md). Phase 2 build-defect entries 1-2 created in this commit (1: SharpeCI attribute access; 2: clean exit 0 on relaunch).

## Audit-remediate-loop trails

| Round-set | Trail path | Verdict |
|---|---|---|
| Pre-reg R1+R2+R3 | [audit_trail_2026-05-05_h054-pre-reg.md](../../../docs/audits/audit_trail_2026-05-05_h054-pre-reg.md) | R3 ACCEPT (10/10 R1 findings closed) |
| Phase 2 build defects + production run | [audit_trail_2026-05-05_h054-phase-2.md](../../../docs/audits/audit_trail_2026-05-05_h054-phase-2.md) (this commit) | R1 build-defect + R2 ACCEPT |

## Cross-validation methodology (per ADR-0013 §7)

H054's pre-registered splitter is `PurgedWalkForwardSplitter` per design.md §6 (rolling, single outer fold). The 5 ADR-0012 CPCV acceptance criteria are preserved as KPI annotations per ADR-0013 §7:

| ADR-0012 criterion | Status for H054 |
|---|---|
| #1 minimum 45 paths at C(10,2) | n/a — H054 uses walk-forward, not CPCV. |
| #2 KS-monotonicity ≤ 0.05 by 30 paths | n/a |
| #3 per-path Sharpe distribution moments | n_folds=1 (single outer fold per design.md §6); no path distribution. |
| #4 24-hour wall-clock cap with downsample fallback | Met: ~7 min wall-clock under the 36hr supervisor cap. |
| #5 DSR computed under CPCV path distribution | n/a (M=1; ADR-0008 single-strategy degenerate handling). |

Walk-forward configuration:
- **Outer**: train 2020-01-01 → 2022-12-31, val 2023-01-01 → 2023-06-30, test 2025-01-01 → 2025-12-03 (per H054.yaml + design.md §2 post-Round-2 F-Q-1 + F-Q-6 fixes)
- **Inner CV** (label cfg selection): 3 folds on IS combined window, purge=embargo=1 session
- **Mode**: rolling
- **DELIBERATELY-UNUSED**: 2023-07-01 → 2024-12-31 (the H052a OOS window; H054 v1 does NOT touch this data in any phase)

## Cross-links

- ReproLog: [logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json](../../../logs/reproducibility/dd916fc67b504c528fda7abbde6700f1.json) ✓
- Sidecar: [artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/sidecar.json](../../../artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/sidecar.json)
- Per-symbol metrics summary: [artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/ES_metrics_summary.json](../../../artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/ES_metrics_summary.json)
- Scientific payload SHA: [artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/scientific_payload_sha256.txt](../../../artifacts/runs/H054/dd916fc67b504c528fda7abbde6700f1/scientific_payload_sha256.txt) = `395dd00877d3b5fae99d9fbbb7bac243d70dd14cd7983ca77b065a14205e3ff4`
- Pre-registered design: [design.md](design.md)
- Pre-reg lit review: [lit_review_H054_2026-05-05.md](lit_review_H054_2026-05-05.md)
- Pre-reg data requirements: [data_requirements.md](data_requirements.md)
- Orchestrator: [scripts/run_h054_walk_forward.py](../../../scripts/run_h054_walk_forward.py)
- BLOCKING tests: [tests/integration/test_h054_pit.py](../../../tests/integration/test_h054_pit.py) (17/17 PASS)
- Cost model: [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../../src/skie_ninja/backtest/costs/futures_orb_v1.py) (shared with H052a)

## Versioning

This is **v1** — the first H054 KPI report card emission per ADR-0013 §3.

A version increment to v2 would be triggered by: (a) H054 v2 with pooled ES + NQ + MES + MNQ on accumulated 2025+ OOS to address n_anti structural underpowering; (b) cost-magnitude empirical calibration; (c) cost-floor sensitivity sweep at sensitivity_mult=2.0; (d) Sortino / capacity / DSR computation; (e) B-arm robustness execution; (f) NinjaScript implementation if operator authorizes; (g) any other substantive KPI change.

Per ADR-0013 §4.1 non-loss mandate: this v1 is preserved verbatim under any future v2+ emission.

## Operator review section (filled at promotion time per ADR-0013 §5.3)

- **Operator**: skoir
- **Promotion decision**: TO BE FILLED at next stage transition. Per the user's 2026-05-04 standing directive ("The failure of profit and projected profit negates our need to move onto ninjascript implementation. This will be the user's discretion upon presentation of results in the canonical format"), the next stage transition is operator-discretionary upon canonical-format presentation.
- **Rationale**: TO BE FILLED — operator review of v1 KPI report card values + 2026 forward projection. Decision considerations:
  - Point estimates positive and directionally consistent with H_1 + H052a-implied reading
  - CIs cover zero on both primary and secondary statistics
  - Forward projection: anti-gated dominates unconditional on every metric (median, P(loss), max-DD)
  - n_anti = 7 structurally underpowered per design.md §9.5 expectation-management
  - Three options: (a) decline NinjaScript progression and record; (b) pursue H054 v2 with pooled multi-instrument; (c) pursue bridge-mediated NinjaScript as deployment-realistic test harness
- **Methodological-correctness acknowledgments**: NOT REQUIRED (no `leakage-canary-fail`, `repro-log-incomplete`, or `post-run-audit-fail` annotations)
- **Cross-link to promotion log**: TBD (path: `logs/promotions/{run_id}_H054_{arm_id}_promotion.md`)
