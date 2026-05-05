---
hypothesis_id: H050
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-04
git_head: d8c6acd1a9acd4d8f55f426213d21220536ccebe
substrate_dataset_checksum: b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d
sidecar_scientific_payload_sha256: c979c56ab606651b955aaedfeba2b030fdbc5ab3cba864e5b1b2d19cedfd9bc4
simulation_log_sha256: 1adc9a154571f2b00ae36bd62fd012da1aeeae443573d1ddf5ca104b464da503
simulation_script_sha256: 3557e2d0b073bfc73bf203f53a1f8bbf9f73897bb50d1b4706964a96ae8ab21d
simulation_output_sha256: 76d3a332b65d1d362fe992fb268bcfc1ec4e7ea01ef5a4c3a6d272a9ef454eee
reprolog_model_hash: 6b6ed8fae988f9f154cde88a6069b78377a34a62ab8139bbfde56aad41fdc379
run_id: 31d23ecd8e3842dd8ebd5687ce9c91d5
sizing_convention: hmm_gated_multibar_intraday  # ADR-0013 §3.1.1 entry for HMM-gated strategies
supersedes: null
superseded_by: null
---

# H050 — KPI Report Card v1

> **First production walk-forward Stage-3 KPI emission** for hypothesis H050 — HMM regime-conditioned ES/NQ intraday directional signal. Canonical [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3 + §3.1 KPI report card on the post-Cell-I substrate following the Path B leakage-clean refactor (commit `d8c6acd`). Production run completed 2026-05-04 02:40:59 CDT after 7hr 50min wall-clock (`run_id` 31d23ecd...; ReproLog at [logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json](../../../logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json)).

- **Hypothesis**: H_1: SR_filtered_gated − SR_filtered_unconditional > 0 on the OOS test fold; HMM regime-gating concentrates directional predictability in the high-mean state on RTH 1-min ES/NQ.
- **Design.md**: [design.md](design.md) (frozen at `status: designed`)
- **Stage**: `kpi-report-emitted` per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). Next mandatory transition: `ninjascript-implemented` per ADR-0013 §5 (bridge-mediated per §1.2 since HMM filter requires Python inference at decision time).
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md))

H050 production walk-forward (run_id `31d23ecd8e3842dd8ebd5687ce9c91d5`; commit `d8c6acd`; 7hr 50min wall-clock; substrate `b3ee230a...` 2015-2025 ES+NQ; cost-aware per design.md §1 net-of-cost binding):

### 1. P/L (realized OOS, $10K starting capital, 100%-of-equity-when-active per ADR-0013 §3.1.1)

| Symbol | Arm | End equity | % change | OOS bars | OOS sessions (eq) |
|---|---|---:|---:|---:|---:|
| ES | hmm_gated | **$1,898.23** | **−81.02%** | 337,837 | ~866 |
| ES | unconditional | $5,630.64 | −43.69% | 337,837 | ~866 |
| NQ | hmm_gated | **$1,580.46** | **−84.20%** | 673,274 | ~1,726 |
| NQ | unconditional | $7,440.31 | −25.60% | 673,274 | ~1,726 |

### 2. Drawdown (realized + projected)

| Symbol | Arm | Realized max-DD | Proj median DD | Proj q95 DD |
|---|---|---:|---:|---:|
| ES | hmm_gated | **81.12%** | 38.42% | 41.75% |
| ES | unconditional | 45.02% | 17.11% | 24.63% |
| NQ | hmm_gated | **84.36%** | 23.93% | 28.52% |
| NQ | unconditional | 35.05% | 13.34% | 23.92% |

(Projected DD bar-level iid bootstrap UNDERSTATES regime-conditional risk per F-Q-3 caveat in §3.1 below.)

### 3. Sharpe — primary inference (T_H050 = SR_gated − SR_uncond per design.md §1)

| Symbol | SR_gated | SR_uncond | T_H050 | LW2008 CI [low, high] | excludes zero | T_H050 annualised |
|---|---:|---:|---:|---|:---:|---:|
| ES | −0.04554 | −0.00840 | **−0.03714** | [−0.04052, −0.03390] | **YES (negative)** | **−11.65** |
| NQ | −0.02311 | −0.00126 | **−0.02185** | [−0.02455, −0.01903] | **YES (negative)** | **−6.85** |

**H_1 (gating improves Sharpe) is rejected on both symbols at 95% one-sided.** HMM gating actively HARMS the directional signal.

### 4. Annualised Sharpe (×√(252×390)=313.5)

| Symbol | SR_gated | SR_uncond |
|---:|---:|---:|
| ES | **−14.28** | −2.63 |
| NQ | −7.25 | −0.39 |

(Annualisation factor: per-bar substrate uses √(252 × 390 RTH bars/session). Lo 2002 η(q) correction for bar-level lag-1 ρ ≈ −0.03 not applied; tracked under `P1-H050-LO-CORRECTED-ANNUALIZATION`; effect ~3-4% on |annualised SR|.)

### 5. Win/Loss/Zero bar counts + win rate

| Symbol | Arm | W | L | Z | Win rate W/(W+L+Z) |
|---|---|---:|---:|---:|---:|
| ES | hmm_gated | 111,026 | 130,831 | 95,980 | 32.9% |
| ES | unconditional | 133,118 | 141,178 | 63,541 | 39.4% |
| NQ | hmm_gated | 239,098 | 273,792 | 160,384 | 35.5% |
| NQ | unconditional | 319,657 | 329,196 | 24,421 | 47.5% |

### 6. Forward 1-year projection ($10K → 98,280 bars; iid bootstrap via PW2004 selected b=1.0; n_paths=5,000; rng_seed=20261420)

| Symbol | Arm | Median | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ES | hmm_gated | $6,172.60 | $5,692.50 | $5,838.93 | $6,520.23 | $6,661.99 | **100.0%** | 0% | 0% |
| ES | unconditional | $8,471.01 | $7,282.50 | $7,646.47 | $9,413.79 | $9,844.24 | 99.6% | 0% | 0% |
| NQ | hmm_gated | $7,642.81 | $7,002.20 | $7,181.29 | $8,101.84 | $8,332.87 | **100.0%** | 0% | 0% |
| NQ | unconditional | $9,596.62 | $7,472.15 | $8,003.69 | $11,509.66 | $12,406.38 | 64.9% | 0% | 0% |

### 7. Hansen SPA family p-value

| Symbol | T_SPA | p | n_bootstrap | Annotation |
|---|---:|---:|---:|---|
| ES | 0.0 | 1.0 | 1000 | `spa-rejects` (m=1 degenerate per ADR-0008; T_SPA = max(0, √n·d̄/ω) = 0 because T_H050 < 0; p=1.0 = fail to reject H_0:E[d]≤0) |
| NQ | 0.0 | 1.0 | 1000 | `spa-rejects` (same mechanism) |

### 8. Other KPIs

| KPI | ES | NQ |
|---|---|---|
| Best label cfg | (pt_sl=1.0, vb=120m, vl=20) | (pt_sl=1.0, vb=120m, vl=20) |
| n_folds (realized/expected) | 1/2 → `power-margin-low` | 2/3 → `power-margin-low` |
| max-DD annotation | `max-dd-adverse` | `max-dd-adverse` |
| Sharpe-vs-uncond annotation | `sharpe-vs-unconditional-negative` | `sharpe-vs-unconditional-negative` |
| Cost model | `nt8_es_nq_rth_v1` constant-tick prior, applied | same |
| Sortino / turnover / capacity | not computed (deferred follow-ups) | not computed |

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2)

`leakage-canary-pass` · `bss-n/a` · `reliability-n/a` · `repro-log-complete` · `dsr-n/a (M=1)` · `post-run-audit-pass`

### Bottom line

H050 is a **definitive negative result** under ADR-0013 §1: HMM regime-gating is significantly worse than the unconditional LightGBM directional signal at 1-min ES/NQ on the 2024-2025 OOS test fold, with LW2008 differential CIs excluding zero on the negative side for both symbols (ES T_H050 = −0.037 [−0.041, −0.034]; NQ T_H050 = −0.022 [−0.025, −0.019]). Realized $10K equity outcomes are catastrophic on both gated arms (ES −81%, NQ −84%); both gated arms project P(loss)=100% over the next year on bar-level iid bootstrap (which UNDERSTATES regime-conditional forward risk per F-Q-3 caveat). Per ADR-0013 §1+§5, H050 progresses to mandatory bridge-mediated NinjaScript implementation regardless of these KPIs (next mandatory transition `kpi-report-emitted` → `ninjascript-implemented`; tracked under `P1-H050-NINJASCRIPT-IMPL`).

Full report card body: §"Methodological-correctness annotations" through §"Operator review section" below; sim output at [logs/simulate_h050_10k_2026.json](../../../logs/simulate_h050_10k_2026.json); ReproLog at [logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json](../../../logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json).

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | **pass** | Path B leakage-clean refactor 2026-05-03 (commit `d8c6acd`); 14 critical+major findings closed across 3 audit-remediate-loop rounds. F-Q-1 (PW2004 embargo on full panel) fixed via train-only slicing; F-Q-3 (lgb_seed reused) fixed via per-(fold, cfg) SeedSequence; F-R-1 + F-R-6 (no scientific_payload SHA + no hash_fn) fixed; full audit trail at [docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md) |
| `bss-{positive,flat,negative}` | **n/a** | design.md §8.a binds `Calibration: BSS > 0 — applicable: NO for H050`. H050's pre-registered output is a continuous trading-rule directional signal, not a calibrated probability forecast. |
| `reliability-{in,out}-of-band` | **n/a** | Same rationale as BSS; design.md §8.a binds `applicable: NO`. |
| `repro-log-{complete,incomplete}` | **complete** | Canonical ReproLog at [logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json](../../../logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json). All 13 fields present: `git_head=d8c6acd`, `pip_freeze_sha256=c92ce92a...`, `dataset_checksums` (3 entries), `rng_seed=20260420`, `model_hash=6b6ed8fa...` (binds scientific_payload via F-R-1+F-R-6 fix), `config_resolved_sha256=2b271608...`, `env_id=be80f7de...`, etc. |
| `dsr-{positive,marginal,negative,n/a}` | **n/a** | Single-strategy family (M=1) below `dsr_activation_size`; per [config/gate.yaml](../../../config/gate.yaml). |
| `post-run-audit-{pass,fail}` | **pass** | Sidecar correspondence verified: scientific_payload SHA `c979c56a...` matches the metrics_summary.json bytes hash. ReproLog `model_hash=6b6ed8fa...` is the SHA256 of `f"model_rollup={rolled};scientific_payload={scientific_sha}"` per F-R-1 fix. Atomic writes per F-R-5 fix; PENDING sentinel cleared on success per F-R-7 fix. |

**No methodological-correctness banner triggered** per ADR-0013 §2.1 (all annotations green or n/a).

## Performance KPIs (per ADR-0013 §3 + `rules/quant-project.md` §Reporting)

### Sharpe-vs-unconditional differential (LW2008 studentised stationary bootstrap CI)

H050's design.md §1 binds `T_H050 = SR_filtered_gated − SR_filtered_unconditional`. F-Q-5 fix (Round-2 audit-remediate-loop 2026-05-04 minor): the unconditional series is `sign(2·p_classifier − 1) · r_t − cost_t` (the same LightGBM directional signal applied at every bar, WITHOUT the HMM regime-gate factor). The gated series multiplies by the binary HMM regime-state indicator `reg_t ∈ {0, 1}`: `gated_t = sign(2·p_classifier − 1) · reg_t · r_t − cost_t`. Where `reg_t = 0` (HMM forward-filter posterior outside the high-mean state), the gated arm is flat at zero `r·position` cost; where `reg_t = 1`, gated and unconditional coincide modulo cost-of-position-flip. The test compares the HMM-conditioning's incremental contribution.

The Sharpe values reported below are **per-bar** statistics (1-min bar frequency); the LW2008 CI is computed on the same per-bar scale per [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py). The annualised Sharpe (multiplied by √(252 × 390) ≈ 313.5) is reported alongside for operator-readable comparison; both are honest representations of the same statistic.

| Symbol | SR_gated (per-bar) | SR_uncond (per-bar) | **T_H050 (per-bar)** | LW2008 CI [low, high] | excludes_zero | T_H050 annualised | Annotation |
|---|---:|---:|---:|---|:---:|---:|---|
| ES | −0.04554 | −0.00840 | **−0.03714** | [−0.04052, −0.03390] | **YES (negative side)** | **−11.65** | `sharpe-vs-unconditional-negative` |
| NQ | −0.02311 | −0.00126 | **−0.02185** | [−0.02455, −0.01903] | **YES (negative side)** | **−6.85** | `sharpe-vs-unconditional-negative` |

**Result**: H_1 (T_H050 > 0) is rejected on both symbols at the 95% level, one-sided. The HMM regime-gate ACTIVELY HARMS the directional signal — gated Sharpe is significantly worse than unconditional Sharpe on the 2024-2025 OOS test fold.

### Sharpe-vs-passive (annualised; informational)

| Symbol | Annualised SR_gated | Annualised SR_uncond | n_bars |
|---|---:|---:|---:|
| ES | −14.28 | −2.63 | 337,837 |
| NQ | −7.25 | −0.39 | 673,274 |

Both gated AND unconditional Sharpes are strongly negative annualised. The LightGBM-on-microstructure directional signal at 1-min ES/NQ is itself near-noise (per-bar Sharpe in [−0.046, −0.001]); the HMM gate's narrowing of the sample increases noise variance enough to deepen the negative annualised Sharpe by ~5-12×.

### Hansen SPA family p-value

| Symbol | SPA statistic | p-value | n_bootstrap | omega method | Annotation |
|---|---:|---:|---:|---|---|
| ES | 0.0 | 1.0 | 1000 | hac (m=1 degenerate) | `spa-rejects` (m=1 degenerate per ADR-0008; T_SPA = max(0, √n·d̄/ω) = 0 because T_H050 < 0; p=1.0 means failure to reject H_0: E[d] ≤ 0) |
| NQ | 0.0 | 1.0 | 1000 | hac (m=1 degenerate) | `spa-rejects` (same mechanism) |

H050's pre-registered SPA family per [ADR-0003](../../../docs/decisions/ADR-0003-spa-vs-romanowolf.md) has only 1 strategy (the H050 hypothesis itself); per [ADR-0008 §"Single-strategy degenerate handling (|M|=1)"](../../../docs/decisions/ADR-0008-spa-omega-method.md) the SPA composite null degenerates to a single-strategy one-sided test of `H_0: E[d] ≤ 0` with `T_SPA = max(0, √n · d̄ / ω)`. F-Q-4 fix (Round-2 audit-remediate-loop 2026-05-04 major): with `d̄ < 0` (T_H050 < 0 on both symbols), `T_SPA = max(0, negative) = 0`; the bootstrap p-value `p = (1/B) #{b : T*_b ≥ T_SPA}` approaches 1.0 because every bootstrap replicate `T*_b ≥ 0` by the `max(0, ·)` construction. The result `p=1.0` is a mechanical consequence of T_H050 < 0, NOT an "ADR-0008 convention". Annotation `spa-rejects` follows the project convention (`spa-passes` = p ≤ α; `spa-rejects` = p > α; matches H053 v3 KPI report card §"Performance KPIs" usage). For primary inference, the LW2008 differential CI above is the binding KPI; the SPA result here is reported per `rules/quant-project.md` §Inference but is not informative beyond the LW2008 CI.

### Other performance KPIs (per `rules/quant-project.md` §Reporting)

| Symbol | Realized end equity (gated) | Max-DD (gated) | Realized end equity (uncond) | Max-DD (uncond) | n_folds (realized/expected) | best label cfg |
|---|---:|---:|---:|---:|:---:|---|
| ES | $1,898 (−81.0%) | **81.12%** | $5,631 (−43.7%) | 45.02% | 1/2 | (1.0, 120m, 20) |
| NQ | $1,580 (−84.2%) | **84.36%** | $7,440 (−25.6%) | 35.05% | 2/3 | (1.0, 120m, 20) |

**Power-margin annotation**: `power-margin-low` (realized n_folds < expected n_folds on both symbols).
**Max-DD annotation**: `max-dd-adverse` (gated max-DD on both symbols exceeds 80%; unconditional exceeds 35%).
**Common best label cfg**: both symbols converged on `pt_sl=1.0, vertical_barrier=120m, volatility_lookback=20` (longest vertical barrier, shortest volatility window, lowest profit-target multiplier from the 27-cell pre-reg grid).

### Mandatory KPIs not yet computed (deferred follow-ups; per ADR-0013 §3.1.2)

| KPI | Status | Follow-up |
|---|---|---|
| Sortino ratio | not computed in this run | `P1-H050-SORTINO-COMPUTE` (downside-deviation per Sortino & Price 1994) |
| Turnover (per-day) | not computed | `P1-H050-TURNOVER-COMPUTE` (sign-changes / RTH session) |
| Capacity estimate | not computed | `P1-H050-CAPACITY-EMPIRICAL` (depends on cost model + slippage from paper-trade logs) |
| Cost-magnitude empirical calibration | constant-tick prior applied; calibration deferred | `P1-H050-COST-CALIBRATION-EMPIRICAL` (renamed from `P1-H050-COST-EMPIRICAL` per F-Q-1 fix Round-2 audit-remediate-loop 2026-05-04 — the cost IS already applied per design.md §1; this follow-up is about CALIBRATING the cost prior magnitude from paper-trade logs once `TrivialSmokeTest` runs land per design.md §7) |
| Mediation / partial-R² | n/a (not applicable to H050 design) | — |
| Session-aggregate forward projection | bar-level bootstrap shipped in v1; session-aggregation deferred | `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION` (Round-2 F-Q-2 + F-Q-3 critical co-mitigation — aggregate per-bar log returns to per-session log returns + session-block-bootstrap to preserve intra-day regime persistence; requires adding `ts_event` to `oos_returns.parquet` orchestrator schema, currently absent) |
| Bar-level vs session-level Sharpe annualisation | bar-level √(252·390)=313.5 convention used; Lo 2002 η(q) correction not applied | `P1-H050-LO-CORRECTED-ANNUALIZATION` (Round-2 F-Q-8 minor — bar-level lag-1 ρ ≈ −0.03 → Lo 2002 η(q) inflates \|annualized SR\| by ~3-4%) |

The deferred-follow-up annotation satisfies the rules/quant-project.md reporting mandate per ADR-0013 §3.1.2; the rule is "every backtest doc lists" the KPI, not "every backtest doc has a non-null value for" the KPI.

## Realized OOS + Forward-Projection block (MANDATORY per ADR-0013 §3.1)

> **Caveats** (binding per ADR-0013 §3.1; updated per Round-2 audit-remediate-loop 2026-05-04 critical findings F-Q-1, F-Q-2, F-Q-3 + minor F-L-2):
> - **Cost model: APPLIED (cost-aware results, NOT cost-free upper bounds)** — F-Q-1 fix (Round-2 critical): the orchestrator at [scripts/run_walk_forward.py:2814,2825](../../../scripts/run_walk_forward.py) subtracts `NT8EsNqRthV1CostModel` per-side cost from BOTH `gated_return` and `unconditional_return` series at the bar level BEFORE writing `oos_returns.parquet`. Per H050 design.md §1 line 30 binding ("Sharpe ratios are computed on walk-forward OOS net-of-cost returns") + §7 cost model spec, the canonical contract is net-of-cost. The realized-OOS + forward-projection numbers below are therefore **cost-aware** under the constant-tick slippage prior currently bound by [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py). Empirical cost-magnitude calibration from paper-trade logs is tracked under `P1-H050-COST-CALIBRATION-EMPIRICAL` (renamed from `P1-H050-COST-EMPIRICAL` to clarify scope: this follow-up is about CALIBRATING the cost prior, not about APPLYING cost-aware logic — the cost is already applied per design.md §1).
> - **Position-sizing convention: HMM-gated multi-bar intraday (binary on/off gate)** per ADR-0013 §3.1.1 — F-Q-6 fix (Round-2 minor): `position_t = sign(2·p_classifier − 1) × reg_t` where `reg_t ∈ {0, 1}` is the HMM forward-filter high-mean-state indicator (binary, NOT a continuous per-state multiplier). When `reg_t = 0` (regime-state-out), the gated arm is flat; when `reg_t = 1` (high-mean state), gated and unconditional differ only in the cost-charge for the position-flip. At 1-min bar frequency over the OOS window, the equity curve compounds at every bar (`equity_{t+1} = equity_t × exp(position_t × r_t − cost_t)`); a no-leverage retail position scales linearly with margin requirements.
> - **Forward-projection horizon: bar-level, NOT session-level** — F-Q-2 fix (Round-2 critical, partially addressed): ADR-0013 §3.1 binds the forward-projection horizon as "252 sessions" (designed for the H053 archetype's per-session daily-cleared returns). H050 substrate is bar-cadence (1-min); the v1 simulator translates 252 sessions × 390 RTH bars/session → 98,280 bars and bootstraps i.i.d. bars. **Methodological caveat**: with PW2004 selecting `block_length=1.0` (i.i.d. bootstrap) at 5,000 paths × 98,280 bars, the bootstrap projection collapses toward its analytical mean limit `$10,000 × exp(98,280 × μ_per_bar)`, suppressing realised-path variance. Specifically: ES gated proj median ≈ $6,173 ≈ 10,000·exp(−4.92e−6 × 98,280) ≈ 10,000·exp(−0.484) ≈ $6,166 (analytical), with q01–q99 spread compressed to ~9% of starting equity vs the realised path's 81% drawdown. The reported quantiles UNDERSTATE forward variance and UNDERSTATE forward max-DD risk under any regime-state persistence beyond the bar level. The methodologically rigorous resolution is session-aggregation (sum bar-level returns within each RTH session → bootstrap 252 i.i.d. sessions) OR session-block bootstrap (preserve intra-session structure via 390-bar contiguous blocks); both require adding `ts_event` to `oos_returns.parquet` (not currently present). Tracked under new follow-up `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION`. **For v1 we keep the bar-level bootstrap (already produced; SHAs in frontmatter remain valid) and document the methodological gap explicitly in this caveat block.**
> - **Bootstrap-destroys-regime-persistence** — F-Q-3 fix (Round-2 major): bar-level i.i.d. bootstrap (the active path here since PW2004 selected `block_length=1.0` on every arm) destroys the HMM regime-state dwell-time persistence that is captured in the realized OOS series. The HMM regime-state changes on the order of minutes-to-hours-to-days; bar-level innovations within a regime are uncorrelated, so PW2004 correctly selects `b=1.0` on the level series — but the regime-state TRANSITIONS are autocorrelated, and i.i.d. bar resampling shuffles regime-active and regime-out bars together, eliminating the contiguous-runs-of-zero-returns structure that drives realized max-DD on the gated arm. This is the empirical mechanism behind the projection-vs-realized divergence on the gated arms (proj median $6,173 vs realized $1,898 on ES gated). Tracked under same follow-up `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION` as a co-mitigation; session-block resampling at 390-bar granularity preserves intra-day regime persistence.
> - **Bootstrap-as-generative-model**: forward distribution assumes 2026 bar-level returns mirror the 2024-2025 OOS empirical distribution. Regime-shift risk and structural breaks beyond the OOS window are NOT modelled — F-L-2 fix (Round-2 minor): we cite [Andrews 1993, Econometrica 61(4):821-856, doi:10.2307/2951764](https://doi.org/10.2307/2951764) as a primary source acknowledging parameter instability is a real econometric phenomenon (the paper develops in-sample detection tests for parameter instability with unknown change point). Andrews 1993 does NOT provide a "lower bound on bootstrap projection" theorem; the bootstrap projection's understatement of realized risk is documented qualitatively here, not derived from Andrews 1993.
> - **Cross-reference**: T_H050 LW2008 CI from §"Sharpe-vs-unconditional differential" above EXCLUDES zero on the negative side for both symbols — the projection's elevated P(loss) and adverse max-DD distributions reflect this honestly. The realized-OOS equity curves on both gated arms are catastrophic (−81%, −84%); the bootstrap projection's median is less catastrophic because i.i.d. resampling decorrelates extreme runs and regime persistence the realized path captured (see F-Q-3 caveat above).

### Realized OOS ($10,000 starting capital; OOS-window-start to OOS-window-end)

| Symbol | Arm | Realized end | % change | Realized max-DD | W / L / Z bars | Win rate (W/(W+L+Z)) |
|---|---|---:|---:|---:|---:|---:|
| ES | hmm_gated | **$1,898.23** | **−81.02%** | **81.12%** | 111,026 / 130,831 / 95,980 | 32.9% |
| ES | unconditional | $5,630.64 | −43.69% | 45.02% | 133,118 / 141,178 / 63,541 | 39.4% |
| NQ | hmm_gated | **$1,580.46** | **−84.20%** | **84.36%** | 239,098 / 273,792 / 160,384 | 35.5% |
| NQ | unconditional | $7,440.31 | −25.60% | 35.05% | 319,657 / 329,196 / 24,421 | 47.5% |

OOS bar windows:
- ES: 2024-01-01 23:00:00 → 2024-12-12 20:30:00 UTC; **n_bars=337,837** (~866 RTH sessions)
- NQ: 2024-01-01 23:00:00 → 2025-12-11 14:57:00 UTC across 2 outer folds; **n_bars=673,274** (~1726 RTH sessions)

### Forward 1-year projection ($10,000 → 98,280 bars = 252 sessions × 390 RTH bars)

Per ADR-0013 §3.1 + Round-1 amendment audit findings F-CONV-3 + F-CONV-4 + F-CONV-7 from [docs/audits/audit_trail_2026-05-03_adr-0013-realized-oos-projection-amendment.md](../../../docs/audits/audit_trail_2026-05-03_adr-0013-realized-oos-projection-amendment.md) (F-L-1 fix Round-2 minor: cite the trail file by name to disambiguate which audit-remediate-loop produced these IDs): PW2004 block-length selection ran on each arm's per-bar log-return level series; **all 4 (arm × symbol) cells selected `block_length = 1.0`**. F-Q-10 fix (Round-2 minor): bar-level iid bootstrap matches the PW2004 result on the level series, but does NOT preserve the HMM regime-state dwell-time persistence (the regime-conditional risk is captured in the realized OOS series but is destroyed by bar-level iid resampling per F-Q-3 caveat above; tracked under follow-up `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION`). The reported quantiles below are therefore methodologically conservative on the negative tail (UNDERSTATE forward max-DD) and methodologically conservative on the positive tail (UNDERSTATE forward upside variance). Single rng_seed=20261420 (= H050.yaml `random_seed=20260420` + 1000 per ADR-0013 §3.1 single-seed mandate) across all arms.

| Symbol | Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) | block_b | method |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ES | hmm_gated | $6,172.60 | — | $5,692.50 | $5,838.93 | $6,520.23 | $6,661.99 | **100.0%** | 0% | 0% | 1.0 | iid_bootstrap |
| ES | unconditional | $8,471.01 | — | $7,282.50 | $7,646.47 | $9,413.79 | $9,844.24 | 99.6% | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | hmm_gated | $7,642.81 | — | $7,002.20 | $7,181.29 | $8,101.84 | $8,332.87 | **100.0%** | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | unconditional | $9,596.62 | — | $7,472.15 | $8,003.69 | $11,509.66 | $12,406.38 | 64.9% | 0% | 0% | 1.0 | iid_bootstrap |

(Mean column omitted; median is the more robust central tendency for the projected distribution. Full simulation output at [logs/simulate_h050_10k_2026.json](../../../logs/simulate_h050_10k_2026.json).)

### Forward max-drawdown projection (% of peak)

| Symbol | Arm | Median DD | Mean DD | q05 | q95 |
|---|---|---:|---:|---:|---:|
| ES | hmm_gated | 38.42% | — | — | 41.75% |
| ES | unconditional | 17.11% | — | — | 24.63% |
| NQ | hmm_gated | 23.93% | — | — | 28.52% |
| NQ | unconditional | 13.34% | — | — | 23.92% |

Bootstrap configuration: n_paths=5,000 × n_bars=98,280; rng_seed=20261420 (= H050.yaml random_seed + 1000 per ADR-0013 §3.1 single-seed mandate); sampling per arm = iid bootstrap (PW2004 selected block_length=1.0 on each arm's per-bar log-return LEVEL series — confirms the sub-1-min bar-level innovations are essentially uncorrelated despite the HMM regime-state's longer-horizon coherence; iid bootstrap is the block_length=1 limit).

Reference implementation: [scripts/simulate_h050_v1_10k_2026.py](../../../scripts/simulate_h050_v1_10k_2026.py). Common forward-projection helpers tracked under `P1-FORWARD-PROJECTION-PRIMITIVE` per ADR-0013 §3.1.2 for refactoring into `src/skie_ninja/inference/projection.py`.

### Operator interpretation (informational; per ADR-0013 §1 KPI-only philosophy)

- **All 4 (arm × symbol) cells project net-loss-at-1-year-bootstrap-median**. Best-case: NQ unconditional (median $9,596.62 = −4.0%; P(loss)=64.9%; q95=$11,509.66 = +15.1%; P(double)=0%). Worst: ES hmm_gated (median $6,172.60 = −38.3%; P(loss)=100.0%; q01=$5,692.50 = −43.1%).
- **HMM regime-gating is HARMFUL on both symbols**: gated worse than unconditional on every metric (annualised Sharpe, realized end equity, max-DD, projected ending-equity median, P(loss)).
- **Mechanism (mechanistic; informational; not load-bearing)**: the HMM identifies regimes via a single-feature emission (log-return), so the "high-mean state" picks bars with positive realised returns in the training window. Conditioning on this state at OOS time is equivalent to a backward-looking regime classifier with no forward predictive content; the resulting position selection enters bars with elevated noise variance (high-mean state has higher idiosyncratic dispersion in the OOS distribution) without forward predictive lift. The 4 microstructure features (Parkinson RV, realized variance, realized skew, OFI tick-rule) likewise provide near-noise predictive signal at 1-min frequency.
- **Pure-C# implementable**: NO. The HMM forward filter requires Python inference at decision time per [ADR-0005 §"Fold-boundary state continuity"](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md). Per ADR-0013 §1.2, H050's NinjaScript implementation will be **bridge-mediated** per [ADR-0002](../../../docs/decisions/ADR-0002-bridge-selection.md): the C# strategy is a thin client calling a Python inference service over the bridge. Tracked under `P1-H050-NINJASCRIPT-IMPL`.
- **Operator-promotion recommendation (operator-discretionary per ADR-0013 §5.3)**: H050 is a clean **null** result (T_H050 < 0 with CI excluding zero; gated worse than unconditional on every metric). Per ADR-0013 §1, this does NOT exit the research loop — H050 progresses to NinjaScript implementation regardless. The bridge-mediated C# implementation will preserve the research-record-of-failure for any future operator review, and produces a deployment-realistic test harness for any successor hypothesis that might re-use the HMM-gating infrastructure.

**Cost-aware status: APPLIED (cost-aware results, NOT cost-free upper bounds)** — F-Q-1 fix (Round-2 critical) supersedes the earlier cost-free framing: the orchestrator at [scripts/run_walk_forward.py:2814,2825](../../../scripts/run_walk_forward.py) subtracts `NT8EsNqRthV1CostModel` per-side cost from BOTH `gated_return` and `unconditional_return` at the bar level BEFORE writing `oos_returns.parquet`. Per H050 design.md §1 line 30 ("Sharpe ratios are computed on walk-forward OOS net-of-cost returns") + §7 cost-model spec, net-of-cost is the canonical contract. The realized + projected numbers above are cost-aware under the constant-tick slippage prior. Per Round-1 H053 audit F-CONV-2 (preserved across H053 → H050): the cost subtraction inside the orchestrator is correctly applied as a per-bar log-return drag (NOT a flat-dollar subtraction at horizon). Cost-magnitude empirical calibration from paper-trade logs is tracked under `P1-H050-COST-CALIBRATION-EMPIRICAL` (renamed from the deprecated `P1-H050-COST-EMPIRICAL` per the F-Q-1 fix's clarification of scope).

## Build / run history

| Stage | Run ID | Date | Sidecar SHA256 | Per-stage findings |
|---|---|---|---|---|
| Pre-mortem (6 prod-run attempts) | various (see [memo_h050-prodrun-postmortem_2026-04-30.md](../../../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md)) | 2026-04-26 → 2026-04-29 | none (zero aggregate artifacts) | 35.2 hr cumulative wall-clock burned across 6 attempts; all terminated externally (Windows Update auto-reboot, supervisor cap, OOM, OS reboot bypass). Documented in [failure_log.md](failure_log.md) entries 1-6. |
| Path B leakage-clean refactor | (Round-1+2+3 audit-remediate-loop on orchestrator) | 2026-05-03 | (see audit trail) | 4 critical + 10 major findings closed across 3 rounds; commit `d8c6acd`. Audit trail: [audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md). |
| **Production walk-forward (Stage-3 v1; this report's source)** | **31d23ecd8e3842dd8ebd5687ce9c91d5** | **2026-05-04 02:40:59 CDT** | **scientific_payload `c979c56a...`; ReproLog model_hash `6b6ed8fa...`** | **First clean completion (28,225s = 7hr 50min). Both symbols ok. ES 27/27 cfgs in 3hr 2min; NQ 27/27 cfgs in 4hr 47min. HMM cache amortization: 24+48 hits / 3+6 misses (9× speedup as designed). Both symbols converged on best label cfg `(pt_sl=1.0, vertical_barrier=120m, volatility_lookback=20)`. T_H050 < 0 on both symbols, LW2008 CI excludes zero on the negative side.** |
| §3.1 Realized-OOS + Forward-Projection (this report) | 31d23ecd... (this v1 emission) | 2026-05-04 | (this card) | Bootstrap simulation per [scripts/simulate_h050_v1_10k_2026.py](../../../scripts/simulate_h050_v1_10k_2026.py); log SHA `1adc9a15...`; output JSON SHA `76d3a332...`. PW2004 selected `block_length=1.0` for all 4 (arm × symbol) cells → iid bootstrap. |

## Failure log entries (cross-referenced)

The full per-strategy failure log is at [failure_log.md](failure_log.md). 10 entries to date:

| Entry ID | Date | Category | Resolution |
|---|---|---|---|
| 1-6 | 2026-04-26 → 2026-04-29 | external-kill / OOM / supervisor-cap | Six prod-run attempts terminated by Windows Update reboot, supervisor 24-hr cap, LGB heap fragmentation, OS-reboot-bypass-of-wake-lock. Closures landed across commits `1c85f5f` (HMM cache), ADR-0010 commit (wake-lock + preflight), ADR-0011 commit (15-item preflight), `681c8c7` (USOSvc disable + ADR-0010 framing fix), `d8c6acd` (Path B leakage-clean). |
| 7 | 2026-05-03 | build-defect | F-R-2 critical: H050.yaml seed mismatch vs design.md §11 (this commit's predecessor). |
| 8 | 2026-05-03 | build-defect (leakage) | F-Q-1 critical: PW2004 embargo on full panel including OOS test fold (F-V3-1 analog). |
| 9 | 2026-05-03 | build-defect (reproducibility) | F-R-1 + F-R-6: scientific_payload SHA + hash_fn callback. |
| 10 | 2026-05-03 | build-defect (citation) | F-L-2: PW2004 → CV embargo substitution lacks primary source. |

## Audit-remediate-loop trails

| Round-set | Trail path | Verdict | Findings |
|---|---|---|---|
| Path B leakage-clean (R1+R2+R3) | [audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md) | Round-3 ACCEPT (14/14 closures verified) | Round-1: 4 critical + 10 major + 11 minor + 9 observations-passing. Round-2: all 14 critical+major remediated. Round-3: 2-agent verification ACCEPT. |
| KPI report card v1 + simulator (this report) | [audit_trail_2026-05-04_h050-kpi-report-v1.md](../../../docs/audits/audit_trail_2026-05-04_h050-kpi-report-v1.md) | Round-2 remediation in-progress (Round-3 verification pending) | Round-1: 2 critical (F-Q-1 cost-aware narrative; F-Q-2 horizon mismatch) + 2 major (F-Q-3 regime persistence; F-Q-4 SPA wording) + 7 minor + 8 lit-verified + 9 repro-verified. Round-2 remediated all 4 critical+major inline (cost-aware narrative; horizon caveat + new follow-up; regime-persistence caveat; SPA mechanism explained). Round-3 verdict TBD. |

## Cross-validation methodology (per ADR-0013 §7)

H050's pre-registered splitter is `PurgedWalkForwardSplitter` per design.md §6 (NOT CPCV — design.md §6 explicitly defers CPCV escalation to a successor hypothesis ID). The 5 ADR-0012 CPCV acceptance criteria are preserved as KPI annotations per ADR-0013 §7:

| ADR-0012 criterion | Status for H050 |
|---|---|
| #1 minimum 45 paths at C(10,2) | n/a — H050 uses walk-forward, not CPCV. CPCV escalation is registered as a successor-hypothesis-ID design change. |
| #2 KS-monotonicity ≤ 0.05 by 30 paths | n/a — same |
| #3 per-path Sharpe distribution moments | Reported in §"Performance KPIs" above; n_folds=1 (ES) and n_folds=2 (NQ) so no path distribution. |
| #4 24-hour wall-clock cap with downsample fallback | Met: 7hr 50min wall-clock under the 36hr supervisor cap. |
| #5 DSR computed under CPCV path distribution | n/a (M=1; ADR-0008 single-strategy degenerate handling). |

Walk-forward configuration (per design.md §6 + Round-2 §F-2 + the 2026-05-03 [purge_rule_addendum_2026-05-03.md](purge_rule_addendum_2026-05-03.md)):
- `embargo`: PW2004-selected on training-fold-only residuals (per F-Q-1 fix); `block_length` per arm × symbol (all selected `1.0` here)
- `purge_window`: per-cfg `label_horizon` (matches AFML §7.4; ratified by addendum)
- `mode`: rolling

## Cross-links

- ReproLog: [logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json](../../../logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json) ✓
- Sidecar (per-symbol metrics_summary.json): `artifacts/runs/H050/31d23ecd8e3842dd8ebd5687ce9c91d5/{ES,NQ}/aggregate/metrics_summary.json`
- Run summary: `artifacts/runs/H050/31d23ecd8e3842dd8ebd5687ce9c91d5/run_summary.json`
- Scientific payload SHA: `artifacts/runs/H050/31d23ecd8e3842dd8ebd5687ce9c91d5/scientific_payload_sha256.txt` = `c979c56ab606651b955aaedfeba2b030fdbc5ab3cba864e5b1b2d19cedfd9bc4`
- OOS returns parquet (gated + unconditional per bar): `artifacts/runs/H050/31d23ecd8e3842dd8ebd5687ce9c91d5/{ES,NQ}/oos_returns.parquet`
- Pre-registered design: [design.md](design.md)
- Frozen-pre-reg amendments: [aggregation_rule_addendum_2026-04-24.md](aggregation_rule_addendum_2026-04-24.md), [hmm_covariance_d1_equivalence_addendum_2026-04-26.md](hmm_covariance_d1_equivalence_addendum_2026-04-26.md), [purge_rule_addendum_2026-05-03.md](purge_rule_addendum_2026-05-03.md), [embargo_pw2004_addendum_2026-05-03.md](embargo_pw2004_addendum_2026-05-03.md)
- Forward-projection simulator: [scripts/simulate_h050_v1_10k_2026.py](../../../scripts/simulate_h050_v1_10k_2026.py)
- Simulation log: [logs/simulate_h050_10k_2026.log](../../../logs/simulate_h050_10k_2026.log)
- Simulation output JSON: [logs/simulate_h050_10k_2026.json](../../../logs/simulate_h050_10k_2026.json)
- Cross-hypothesis SPA panel: NOT YET BUILT; tracked under `P1-CROSS-HYPOTHESIS-SPA-PANEL`
- Cross-strategy comparability table: NOT YET BUILT; tracked under `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD`

## Versioning

This is **v1** — the first H050 KPI report card emission per ADR-0013 §3.

A version increment to v2 would be triggered by: cost-magnitude empirical calibration from paper-trade logs (`P1-H050-COST-CALIBRATION-EMPIRICAL`), session-aggregate forward-projection re-run (`P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION`), Sortino/turnover/capacity computation, Lo-corrected annualization (`P1-H050-LO-CORRECTED-ANNUALIZATION`), paper-trade-evaluated stage transition adding the realized-Sharpe-vs-backtest observation, NinjaScript-parity-check artifact emission per ADR-0013 §5.2, or any other substantive KPI change.

Per ADR-0013 §4.1 non-loss mandate: this v1 is preserved verbatim under any future v2+ emission.

## Operator review section (filled at promotion time per ADR-0013 §5.3)

- **Operator**: skoir
- **Promotion decision**: TO BE FILLED at next stage transition (`kpi-report-emitted` → `ninjascript-implemented`)
- **Rationale**: TO BE FILLED — operator review of this v1 KPI report card values + 2026 forward projection
- **Methodological-correctness acknowledgments**: NOT REQUIRED (no `leakage-canary-fail`, `repro-log-incomplete`, or `post-run-audit-fail` annotations)
- **Cross-link to promotion log**: TBD (path: `logs/promotions/{run_id}_H050_{arm_id}_promotion.md`)
