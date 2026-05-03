---
hypothesis_id: H053
schema_version: kpi_report_card_v1
version: 3
date: 2026-05-03
git_head: 0d1fb08442747cc07b63b33d173c20eaf8e65966
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar_scientific_payload_sha256: 4d5a826babf25cf2697f8df5e57c9b6abf48b4a87b9a3b3ad57cb9a2e2bcd1f8
simulation_log_sha256: 5f92e1c12e95136790c8533d5946b90f87a9bccec55176522aa4a4266c46091a
simulation_script_sha256: 59127e6304080e1ab36aebe0f217813f7742edf169d10f9f595f771f7b0f6fe1
run_id: fe051383e6c146bea93051b816c7e0a1
sizing_convention: intraday_daily_clear  # ADR-0013 §3.1.1 default for daily-cleared single-leg intraday
supersedes: H053_kpi_report_v2.md
superseded_by: null
---

# H053 — KPI Report Card v3

> **First realization of the [ADR-0013 §3.1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) Realized-OOS + Forward-Projection mandate (2026-05-03 amendment).** Supersedes [v2](H053_kpi_report_v2.md) substantively by adding §"Realized OOS + Forward Projection" per the user 2026-05-03 directive ("the final deliverable of all hypothesis should be similar realized OOS and 2026 projections of strategies, in addition to metrics such as drawdowns, winrates, sharpes, etc."). All other KPIs from v2 preserved verbatim — the Path B Stage-3 v4 sidecar (`4d5a826b...`) is the same canonical run; v3 differs from v2 only in the new mandatory block. v2 preserved verbatim per ADR-0013 §4.1 non-loss mandate.

- **Hypothesis**: 09:45→10:30 ET ES/NQ regression with multi-timeframe features + opening-bar mediator + categorical archetype-bias-target table
- **Design.md**: [design.md](design.md)
- **Stage**: `kpi-report-emitted` per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). Next mandatory transition: `ninjascript-implemented` per ADR-0013 §5.
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | **pass** (14/14) | PIT canaries verified at [tests/integration/test_h053_pit_canaries.py](../../../tests/integration/test_h053_pit_canaries.py) at HEAD `0d1fb08`; not re-run inline. |
| `bss-{positive,flat,negative}` | mixed: 1 flat, 3 negative | OOF isotonic-calibrated probability via pre-test-causal held-out source (F-V3-2 fix). |
| `reliability-{in,out}-of-band` | **out-of-band** on all 4 arms | Slope of binned mean(d) vs binned mean(p_oof) on 10 quantile bins. |
| `repro-log-{complete,incomplete}` | **complete** | Canonical ReproLog at [logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json](../../../logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json). |
| `dsr-{positive,marginal,negative,n/a}` | n/a (family below activation_size) | When DSR-active, all 4 arm × symbol cells are negative ([-3.81, -3.29]). |

**No methodological-correctness banner triggered** per ADR-0013 §2.1.

## Performance KPIs (per ADR-0013 §3 + `rules/quant-project.md` §Reporting)

### Sharpe-vs-passive (CPCV OOS-only)

| Symbol | Arm | median | CI [q05, q95] | n_folds | DSR | KS-monotonicity | Annotation |
|---|---|---:|---|---:|---:|---|---|
| ES | ElasticNet | +0.393 | [-1.425, +3.931] | 45 | -3.553 | not-converged | `sharpe-vs-passive-marginal` |
| ES | LightGBM | +0.634 | [-2.276, +3.258] | 45 | -3.608 | not-converged | `sharpe-vs-passive-marginal` |
| NQ | ElasticNet | +1.714 | [-3.234, +3.606] | 45 | -3.294 | not-converged | `sharpe-vs-passive-marginal` |
| NQ | LightGBM | +0.213 | [-3.752, +1.977] | 45 | -3.808 | not-converged | `sharpe-vs-passive-marginal` |

### Sharpe-vs-bench (LW2008 differential CI; bench = AR(1) lag-1)

| Symbol | Arm | Δ Sharpe (annualized) | CI [low, high] | excludes_zero | block_length | bandwidth | Annotation |
|---|---|---:|---|:---:|---:|---:|---|
| ES | ElasticNet | +0.625 | [-1.614, +2.920] | False | 1.0 | 3 | `sharpe-vs-bench-marginal` |
| ES | LightGBM | +1.953 | [-0.506, +4.362] | False | 1.0 | 8 | `sharpe-vs-bench-marginal` |
| NQ | ElasticNet | +1.468 | [-1.073, +3.821] | False | 1.0 | 1 | `sharpe-vs-bench-marginal` |
| NQ | LightGBM | +1.894 | [-0.341, +4.117] | False | 1.0 | 3 | `sharpe-vs-bench-marginal` |

### Other KPIs

| Symbol | Arm | BSS | Reliability slope | Max-DD ratio | Power-margin | SPA p (m=2) |
|---|---|---:|---:|---:|---:|---:|
| ES | ElasticNet | -0.010 (`flat`) | +0.081 (out-of-band) | 1.438 (adverse) | 0.592 (low) | 0.367 (rejects) |
| ES | LightGBM | -0.061 (`negative`) | +0.296 (out-of-band) | 0.621 (favorable) | 0.592 (low) | 0.367 (rejects) |
| NQ | ElasticNet | -0.145 (`negative`) | -0.052 (out-of-band) | 0.554 (favorable) | 0.600 (low) | 0.290 (rejects) |
| NQ | LightGBM | -0.060 (`negative`) | +0.108 (out-of-band) | 0.368 (favorable) | 0.600 (low) | 0.290 (rejects) |

### Mandatory KPIs not yet computed (deferred follow-ups)

| KPI | Status | Follow-up |
|---|---|---|
| Sortino ratio | not computed in Stage-3 v4 | `P1-H053-SORTINO-COMPUTE` |
| Turnover (per-day) | not computed in Stage-3 v4 | `P1-H053-TURNOVER-COMPUTE` (sign-changes / session) |
| Capacity estimate (contracts/bar OR USD/day) | not computed in Stage-3 v4 | `P1-H053-CAPACITY-EMPIRICAL` (depends on cost model + slippage from paper-trade logs) |
| Mediation NIE / NDE on Stage-3 v4 features | not re-computed | Stage-2 v1 results preserved at [reports/h053/stage2_multitf_mediation_disposition.md](../../../reports/h053/stage2_multitf_mediation_disposition.md) |
| Cost-aware forward projection | not yet applied | `P1-H053-COST-EMPIRICAL` (subtract NT8 RTH cost model from per-session strategy returns; re-run §"Forward 1-year projection" below) |

## Realized OOS + Forward-Projection block (MANDATORY per ADR-0013 §3.1)

> **Caveats** (binding per ADR-0013 §3.1):
> - **Cost model: NOT applied** — these are cost-free upper bounds. The H053 NT8 RTH cost model (per-contract commission + exchange fee + 1-2 tick slippage; ~$4-8 per round-trip on MES; ~$8-16 on ES) would subtract approximately $1,000-$2,000 over 252 sessions on a $10k account. Cost-aware variant tracked under `P1-H053-COST-EMPIRICAL`.
> - **Position-sizing convention: 100%-of-equity per session, no leverage** — `equity_{t+1} = equity_t × exp(r_t)` where `r_t` = strategy log return. Equivalent to holding $10k of underlying index for the 09:45-10:30 ET window. In practice, $10k supports ~1-2 MES contracts (each ≈ $29k notional × 5% margin ≈ $1.4k margin); the simulation is the approximate fractional-position equivalent.
> - **Bootstrap-as-generative-model**: forward distribution assumes 2026 mirrors the OOS empirical distribution (2024-2025).
> - **Cross-reference**: Sharpe-vs-passive CIs from §"Performance KPIs" above are uniformly `marginal` (cover zero on all arms) — the projection's wide bands and elevated P(loss) values reflect this honestly.

### Realized OOS ($10,000 starting capital; OOS-window-start to OOS-window-end)

| Symbol | Arm | Realized-path Sharpe† | Realized end | % change | Realized max-DD | W/L/Z | Win rate (W/(W+L+Z)) |
|---|---|---:|---:|---:|---:|---:|---:|
| ES | ElasticNet | -0.452 | $9,683 | -3.2% | 10.2% | 188/178/1 | 51.2% |
| ES | LightGBM | +0.874 | $10,643 | +6.4% | 4.5% | 195/171/1 | 53.1% |
| ES | passive-long | -0.005 | $9,996 | 0.0% | 7.2% | 186/180/1 | 50.7% |
| NQ | ElasticNet | +0.596 | $10,617 | +6.2% | 5.6% | 193/179/0 | 51.9% |
| NQ | LightGBM | +1.021 | $11,078 | **+10.8%** | 3.7% | 189/183/0 | 50.8% |
| NQ | passive-long | +0.128 | $10,129 | +1.3% | 9.8% | 192/180/0 | 51.6% |

† **Realized-path Sharpe** = single-OOS-trajectory annualised mean/std × √252 of strategy log returns. Per ADR-0013 §3.1 item 1 + Round-1 audit F-CONV-1: this is **NOT** the same statistic as the canonical CPCV path-Sharpe distribution median in §"Sharpe-vs-passive (CPCV OOS-only)" above (which is the median of 45 per-fold Sharpes). Both are reported; do NOT compare them as if equivalent. E.g., NQ ElasticNet has CPCV-OOS-median Sharpe +1.71 (path-distribution median) AND realized-path Sharpe +0.60 (single-trajectory) — both honest, measuring different things.

OOS windows: ES 2024-01-03 → 2025-12-03 (n=367 sessions); NQ 2024-01-03 → 2025-12-18 (n=372 sessions).

### Forward 1-year projection ($10,000 → 252 sessions ahead; bootstrap from OOS empirical distribution)

Per ADR-0013 §3.1 + Round-1 audit F-CONV-3 + F-CONV-4 + F-CONV-7 fixes: PW2004 block-length selection ran on each arm's strategy-log-return level series; **all 6 arms × symbols selected `block_length = 1.0`** → iid bootstrap is the appropriate sampling method. Single rng_seed=1042 across all arms (per-arm RNG offsets forbidden). q01/q99 columns added for tail visibility.

| Symbol | Arm | Median | Mean | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) | block_b | method |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ES | ElasticNet | $9,789 | $9,789 | $8,698 | $8,990 | $10,590 | $10,922 | **67.6%** | 0% | 0% | 1.0 | iid_bootstrap |
| ES | LightGBM | $10,434 | $10,446 | $9,351 | $9,636 | $11,291 | $11,648 | 18.8% | 0% | 0% | 1.0 | iid_bootstrap |
| ES | passive-long | $9,993 | $10,001 | $8,941 | $9,226 | $10,807 | $11,172 | 50.7% | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | ElasticNet | $10,393 | $10,435 | $8,850 | $9,314 | $11,690 | $12,237 | 27.4% | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | LightGBM | **$10,699** | $10,726 | $9,177 | $9,569 | $11,972 | $12,561 | **15.7%** | 0% | 0% | 1.0 | iid_bootstrap |
| NQ | passive-long | $10,092 | $10,113 | $8,613 | $9,015 | $11,305 | $11,850 | 44.3% | 0% | 0% | 1.0 | iid_bootstrap |

### Forward max-drawdown projection (% of peak)

| Symbol | Arm | Median DD | Mean DD | q05 | q95 |
|---|---|---:|---:|---:|---:|
| ES | ElasticNet | 6.1% | 6.5% | 2.9% | 11.8% |
| ES | LightGBM | 3.8% | 4.1% | 2.1% | 7.4% |
| ES | passive-long | 5.2% | 5.6% | 2.6% | 10.0% |
| NQ | ElasticNet | 5.8% | 6.3% | 3.1% | 11.3% |
| NQ | LightGBM | 5.1% | 5.6% | 2.9% | 9.9% |
| NQ | passive-long | 6.7% | 7.3% | 3.5% | 13.2% |

Bootstrap configuration: n_paths=5,000 × n_sessions=252; rng_seed=`_STAGE3_RNG_SEED + 1000` (=1042); sampling per arm = iid bootstrap (Politis-White 2004 selected block_length=1.0 on each arm's strategy-log-return LEVEL series — confirms weak/no autocorrelation in daily-cleared intraday strategy returns; iid bootstrap is the block_length=1 limit). Per F-CONV-3 audit, this PW2004 selection is on the LEVEL series (not the strategy-minus-bench differential as v3-pre-Round-2 incorrectly claimed). Per F-CONV-4 audit, single rng_seed across all arms (per-arm offsets forbidden).

Reference implementation: [scripts/simulate_h053_v4_10k_2026.py](../../../scripts/simulate_h053_v4_10k_2026.py). Common forward-projection helpers tracked under `P1-FORWARD-PROJECTION-PRIMITIVE` for refactoring into `src/skie_ninja/inference/projection.py` (scope tightened per ADR-0013 §3.1.2).

### Operator interpretation (informational; per ADR-0013 §1 KPI-only philosophy)

- **Best projected**: NQ LightGBM (median +7.0%; P(loss)=15.7%; median DD 5.1%; q01 = $9,177 / q99 = $12,561). Realized OOS over 2 years: +10.8% / max-DD 3.7%. Bridge-mediated NinjaScript implementation required (no native LGB runtime in NT8 C#).
- **Strongest |sharpe-vs-bench|**: ES LightGBM (+1.95 annualized vs AR(1) lag-1; CI covers zero). Median projected ending equity +4.3%; P(loss)=18.8%.
- **Pure-C# implementable**: ElasticNet arms (linear coefficients trivial; isotonic-calibration is a finite-bin lookup table). NQ ElasticNet has the highest CPCV-OOS-median Sharpe (+1.71) but the widest CI [-3.23, +3.61]; median projected ending equity +3.9%; P(loss)=27.4%; q01-q99 spans the widest range across all arms ($8,850 - $12,237).
- **Worst projected**: ES ElasticNet (median -2.1%; P(loss)=67.6%; consistent with realized-path Sharpe -0.45). Re-fitting may be warranted under successor hypothesis with revised feature set.

**Cost-aware projection: NOT YET RUN** (tracked under `P1-H053-COST-EMPIRICAL`). Per Round-1 audit F-CONV-2: a flat-dollar cost subtraction at horizon (e.g., subtracting `$N_round-trips × $cost_per_trip` from compounded ending equity) is dimensionally inconsistent with the 100%-of-equity compound-return path. The correct cost-aware projection applies a per-session log-return drag (`r_t' = r_t - cost_per_session/equity_t`) inside the simulation loop. The canonical `NT8EsNqRthV1CostModel` cost model at [src/skie_ninja/backtest/](../../../src/skie_ninja/backtest/) will be wired into the simulation under the tracked follow-up; this v3 reports cost-free upper bounds only.

## Build / run history

| Stage | Run ID | Date | Sidecar SHA256 | Per-stage findings |
|---|---|---|---|---|
| Stage-1 (mediator-only) | h053_stage1_2026-05-01 | 2026-05-01 | 316266d848dadcbffa6 | NULL on full IS train fold; mediator alone insufficient. |
| Stage-2 (multi-tf + mediation) | h053_stage2_2026-05-01 | 2026-05-01 | a27a46de2bc18948f65 | descriptive-positive in-sample partial-R²; NDE point negative (reversal direction). |
| Stage-3 first-pass | h053_stage3_20260501T115445Z | 2026-05-01 | 6a001cf4a847c4d70 | Provisional `archive(null)` reversed by commit 8c1de7c due to Daily-405-gate truncation defect. |
| Stage-3 v2 | h053_stage3_v2_20260503T144640Z | 2026-05-03 | 0cd96f55ca78916257e | ADR-0012-compliant first refactor post-Daily-gate-fix. Disposition `calibration-failed`. 13 audit findings (3 critical leakage). Re-tagged → KPI report card [v1](H053_kpi_report_v1.md) per ADR-0013. |
| Stage-3 v3 | h053_stage3_v3_20260503T204100Z | 2026-05-03 | 4cf291c036505f63f24 | Path B Round-1 attempt; 2 critical leakage residuals (F-V3-1 + F-V3-2). Sidecar preserved per ADR-0013 §4.1; not promoted to v{N} kpi_report. |
| **Stage-3 v4 (this v3 source)** | fe051383e6c146bea93051b816c7e0a1 | 2026-05-03 | 4d5a826babf25cf2697 | Path B Round-2 remediation; closes all 6 v3 audit findings; Round-3 verdict ACCEPT. Canonical KPI source for [v2](H053_kpi_report_v2.md) and v3. |
| **§3.1 Realized-OOS + Forward-Projection** | (this v3 emission) | 2026-05-03 | (this card) | Bootstrap simulation per [scripts/simulate_h053_v4_10k_2026.py](../../../scripts/simulate_h053_v4_10k_2026.py) at log [logs/simulate_10k_2026.log](../../../logs/simulate_10k_2026.log). v3 = v2 + new mandatory §3.1 block. |

## Failure log entries (cross-referenced)

| Entry ID | Date | Category | Resolution |
|---|---|---|---|
| 1 | 2026-05-03 | build-defect | Stage-3 v3 first-run `ModuleNotFoundError`; fix: `_REPO_ROOT / "src"` to sys.path. |
| 2 | 2026-05-03 | build-defect | Stage-3 v3 second-run substrate not in this worktree; fix: `--substrate-path` to sibling. |
| 3 | 2026-05-03 | build-defect | Stage-3 v4 first-run LW2008 API field-name mismatch; fix: `point_estimate / lower / upper`. |
| 4 | 2026-05-01 | build-defect (substrate) | Daily-block 405-bar gate dropped pre-2022 sessions; fix: `>= 404`. |

## Audit-remediate-loop trails (Path B 3-round)

| Round | Trail path | Verdict | Findings |
|---|---|---|---|
| Round-1 (on v3 leakage-clean refactor) | [audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md) | block (R1) → accept (R3) | Round-1: 22 findings (2 critical); Round-2: 6 closures + LW2008 build defect; Round-3: 8 verification-pass findings |

## Cross-validation methodology (per ADR-0013 §7)

- CPCV configuration per ADR-0012 binding: n_groups=10, n_test_groups=2, n_paths=C(10,2)=45 = AFML §12.5
- Panel scope: OOS test region only (F-V3-1 fix; was full panel in v1)
- Embargo: 4 sessions per AFML §7.4.2 `h ≈ 0.01·T` for OOS T≈370
- KS-monotonicity: cpcv-ks-not-converged on all 4 arms
- Wall-clock cap: respected; no downsampling

## Cross-links

- ReproLog: [logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json](../../../logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json) ✓
- Sidecar: [runs/h053/stage3_v4/fe051383e6c146bea93051b816c7e0a1/sidecar.json](../../../runs/h053/stage3_v4/fe051383e6c146bea93051b816c7e0a1/sidecar.json)
- Pre-registered design: [design.md](design.md)
- Cross-hypothesis SPA panel: NOT YET BUILT; tracked under `P1-CROSS-HYPOTHESIS-SPA-PANEL`
- Cross-strategy comparability table: NOT YET BUILT; tracked under `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD`

## Versioning

This is v3. Predecessors:
- [v1](H053_kpi_report_v1.md) — retroactive re-tag of Stage-3 v2 (ADR-0012 disposition `calibration-failed`)
- [v2](H053_kpi_report_v2.md) — canonical Path B output (Stage-3 v4 leakage-clean refactor)
- v3 (this card) — v2 + Realized-OOS + Forward-Projection block per ADR-0013 §3.1 amendment

A version increment to v4 would be triggered by: cost-aware forward-projection re-run (`P1-H053-COST-EMPIRICAL`), Sortino/turnover/capacity computation, paper-trade-evaluated stage transition, or any other substantive KPI change.

## Operator review section (filled at promotion time per ADR-0013 §5.3)

- **Operator**: skoir
- **Promotion decision**: TO BE FILLED at next stage transition (`kpi-report-emitted` → `ninjascript-implemented`)
- **Rationale**: TO BE FILLED — operator review of the v3 KPI report card values + 2026 projection
- **Recommended starting arms** (per realized + projected metrics):
  1. NQ LightGBM (best projected; bridge-mediated NT8 implementation required)
  2. ES LightGBM (largest |sharpe-vs-bench|; bridge-mediated)
  3. NQ ElasticNet (highest CPCV-OOS-median; pure-C# implementable; widest CI)
- **Methodological-correctness acknowledgments**: NOT REQUIRED (no `leakage-canary-fail` or `repro-log-incomplete` annotations)
- **Cross-link to promotion log**: TBD (path: `logs/promotions/{run_id}_H053_{arm_id}_promotion.md`)
