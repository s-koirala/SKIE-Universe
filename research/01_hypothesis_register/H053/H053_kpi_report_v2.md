---
hypothesis_id: H053
schema_version: kpi_report_card_v1
version: 2
date: 2026-05-03
git_head: 0d1fb08442747cc07b63b33d173c20eaf8e65966
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar_scientific_payload_sha256: 4d5a826babf25cf2697f8df5e57c9b6abf48b4a87b9a3b3ad57cb9a2e2bcd1f8
run_id: fe051383e6c146bea93051b816c7e0a1
supersedes: H053_kpi_report_v1.md
superseded_by: H053_kpi_report_v3.md
---

# H053 — KPI Report Card v2

> **NOTE — SUPERSEDED 2026-05-03 by [v3](H053_kpi_report_v3.md).** v3 differs from v2 ONLY by the addition of the §"Realized OOS + Forward-Projection" block per [ADR-0013 §3.1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) (mandatory 2026-05-03 amendment). All other v2 content is identical in v3. v2 preserved verbatim per ADR-0013 §4.1 non-loss mandate.

> **PATH B leakage-clean refactor (Stage-3 v4).** Supersedes [v1](H053_kpi_report_v1.md). v2 closes the 6 audit findings from v1's Stage-3 v2 + v3 audit trails:
> - F-V3-1 CPCV runs on **OOS test region only** (was full IS+OOS panel)
> - F-V3-2 OOF iso source is **strictly pre-test causal** (filtered to indices < min(test_segment))
> - F-V3-3 inner CV `n_splits=5` per AFML §7.4.3 default (was 3)
> - F-V3-4 CPCV embargo=4 sessions per AFML §7.4.2 `h ≈ 0.01·T` (was 2)
> - F-V3-5 LW2008 differential CI for sharpe-vs-bench (was placeholder ±0.1)
> - F-V3-6 RunContext + canonical ReproLog at [logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json](../../../logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json)

- **Hypothesis**: 09:45→10:30 ET ES/NQ regression with multi-timeframe features + opening-bar mediator + categorical archetype-bias-target table
- **Design.md**: [design.md](design.md)
- **Stage**: `kpi-report-emitted` per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). Next mandatory transition: `ninjascript-implemented` per ADR-0013 §5.
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | **pass** (14/14) | PIT canaries verified at [tests/integration/test_h053_pit_canaries.py](../../../tests/integration/test_h053_pit_canaries.py) at HEAD `0d1fb08`; not re-run inline. Canary-inline-verify tracked under `P1-H053-STAGE3-V4-CANARY-INLINE-VERIFY`. |
| `bss-{positive,flat,negative}` | mixed: 1 flat, 3 negative (see KPI table) | OOF isotonic-calibrated probability via **pre-test-causal held-out source** (F-V3-2 fix). Per-instrument climatological prior on the test fold. |
| `reliability-{in,out}-of-band` | **out-of-band** on all 4 arms | Slope of binned mean(d) vs binned mean(p_oof) on 10 quantile bins. Project-operational band [0.7, 1.3] per `P1-RELIABILITY-SLOPE-EMPIRICAL-CALIBRATION`. |
| `repro-log-{complete,incomplete}` | **complete** | Canonical ReproLog at [logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json](../../../logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json) per ADR-0013 §4.1 #4. RunContext-emitted; carries git_head + dataset_checksums + rng_seed + model_hash + env_id + pip_freeze_path. |
| `dsr-{positive,marginal,negative,n/a}` | n/a (family below activation_size) | When DSR-active, all 4 arm × symbol cells are negative ([-3.81, -3.29] under CPCV path-Sharpe deflation). Reported as KPI per ADR-0013 §2; not binding. |

**No methodological-correctness banner triggered** per ADR-0013 §2.1 (banner is for `leakage-canary-fail` OR `repro-log-incomplete`).

## Performance KPIs (per ADR-0013 §3 + `rules/quant-project.md` §Reporting)

### Sharpe-vs-passive (CPCV OOS-only, F-V3-1 fix)

| Symbol | Arm | median | CI [q05, q95] | n_folds | DSR | KS-monotonicity | Annotation |
|---|---|---:|---|---:|---:|---|---|
| ES | ElasticNet | +0.393 | [-1.425, +3.931] | 45 | -3.553 | not-converged | `sharpe-vs-passive-marginal` |
| ES | LightGBM | +0.634 | [-2.276, +3.258] | 45 | -3.608 | not-converged | `sharpe-vs-passive-marginal` |
| NQ | ElasticNet | +1.714 | [-3.234, +3.606] | 45 | -3.294 | not-converged | `sharpe-vs-passive-marginal` |
| NQ | LightGBM | +0.213 | [-3.752, +1.977] | 45 | -3.808 | not-converged | `sharpe-vs-passive-marginal` |

**Note (per F-V4-7 verification)**: OOS-only CPCV path-Sharpe std (~1.7-2.2) is roughly 3× wider than v1's full-panel CPCV (~0.6-0.8) because the OOS panel is ~370 sessions vs ~1700 sessions full-panel. Wider distribution + Bailey-LdP 2014 deflation pushes DSR substantially negative. The honest OOS-only Sharpe estimate has all CIs covering zero. **Cross-reference with v1 std/DSR is misleading** — v1 included IS rows in CPCV training folds (F-V3-1 leakage).

### Sharpe-vs-bench (LW2008 differential CI, F-V3-5 fix)

Bench: AR(1) lag-1 (per `P1-H053-STAGE1-HKS-BENCHMARK-RECONCILE`); not the original HKS time-of-day-FE bench (which collapsed to passive).

| Symbol | Arm | Δ Sharpe (annualized) | CI [low, high] | excludes_zero | block_length | bandwidth | Annotation |
|---|---|---:|---|:---:|---:|---:|---|
| ES | ElasticNet | +0.625 | [-1.614, +2.920] | False | 1.0 | 3 | `sharpe-vs-bench-marginal` |
| ES | LightGBM | +1.953 | [-0.506, +4.362] | False | 1.0 | 8 | `sharpe-vs-bench-marginal` |
| NQ | ElasticNet | +1.468 | [-1.073, +3.821] | False | 1.0 | 1 | `sharpe-vs-bench-marginal` |
| NQ | LightGBM | +1.894 | [-0.341, +4.117] | False | 1.0 | 3 | `sharpe-vs-bench-marginal` |

LW2008: studentised pivotal CI per [Ledoit-Wolf 2008 *J. Empirical Finance* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002). 2000 stationary-bootstrap replicates per arm. Block length selected by Politis-White 2004 (uniformly 1.0 on the strategy-minus-AR(1)-bench differential — consistent with weak/no autocorrelation in the residual). Bandwidth via NW1994 plug-in per replicate. n_degenerate_resamples=0 in all 4 invocations.

### Other KPIs

| Symbol | Arm | BSS | Reliability slope | Max-DD ratio | Power-margin | SPA p (m=2) |
|---|---|---:|---:|---:|---:|---:|
| ES | ElasticNet | -0.010 (`flat`) | +0.081 (out-of-band) | 1.438 (adverse) | 0.592 (low) | 0.367 (rejects) |
| ES | LightGBM | -0.061 (`negative`) | +0.296 (out-of-band) | 0.621 (favorable) | 0.592 (low) | 0.367 (rejects) |
| NQ | ElasticNet | -0.145 (`negative`) | -0.052 (out-of-band) | 0.554 (favorable) | 0.600 (low) | 0.290 (rejects) |
| NQ | LightGBM | -0.060 (`negative`) | +0.108 (out-of-band) | 0.368 (favorable) | 0.600 (low) | 0.290 (rejects) |

BSS components: pre_test_skips=1 per arm × symbol (1 of 5 inner CPCV folds skipped because pre-test region <150 rows for early-region test blocks); n_oof per arm = 1058-1065 (very high coverage of the IS train fold).

SPA p computed at m=2 strategies (Arm1-vs-passive, Arm2-vs-passive). At m=2 the SPA test reduces approximately to a paired-test; Hansen 2005 §2.4 SPA_l recentering offers minimal correction at small m. Reported as KPI; not binding (per ADR-0013 §2). 0 SingleStrategySPAWarnings raised.

### Mandatory KPIs not yet computed (deferred follow-ups)

| KPI | Status | Follow-up |
|---|---|---|
| Sortino ratio | not computed in Stage-3 v4 | `P1-H053-SORTINO-COMPUTE` |
| Turnover (per-day) | not computed in Stage-3 v4 | `P1-H053-TURNOVER-COMPUTE` (sign-changes / session) |
| Capacity estimate (contracts/bar OR USD/day) | not computed in Stage-3 v4 | `P1-H053-CAPACITY-EMPIRICAL` (depends on cost model + slippage from paper-trade logs) |
| Mediation NIE / NDE on Stage-3 v4 features | not re-computed | Stage-2 v1 results preserved at [reports/h053/stage2_multitf_mediation_disposition.md](../../../reports/h053/stage2_multitf_mediation_disposition.md) |
| In-sample partial-R² on Stage-3 v4 features | not re-computed | Stage-2 v1 partial-R² preserved at [reports/h053/stage2_multitf_mediation_disposition.md](../../../reports/h053/stage2_multitf_mediation_disposition.md) |

These are mandatory per `rules/quant-project.md` §Reporting and ADR-0013 §3 — operationally deferred for this v2 emission to keep the leakage-clean refactor scope tight; tracked above.

## CPCV diagnostics (per ADR-0013 §7)

- Configuration: n_groups=10, n_test_groups=2, n_paths=C(10,2)=45 per AFML §12.5
- **Panel scope: OOS test region only** (F-V3-1 fix; was full panel in v1)
- Embargo: 4 sessions per AFML §7.4.2 `h ≈ 0.01·T` for OOS T≈370 (was 2 in v1)
- KS-monotonicity: **NOT converged** on all 4 arms (KS dist > 0.05 by 30 paths). The smaller OOS-only panel (~370 sessions) has a path-Sharpe distribution std too high for empirical-CDF convergence at 45 paths.
- Wallclock cap respected: yes (no downsampling)

## Build / run history

| Stage | Run ID | Date | Sidecar SHA256 | Per-stage findings |
|---|---|---|---|---|
| Stage-1 (mediator-only) | h053_stage1_2026-05-01 | 2026-05-01 | 316266d848dadcbffa6 | NULL on full IS train fold; mediator alone insufficient. Preserved at [reports/h053/stage1_mediator_only_disposition.md](../../../reports/h053/stage1_mediator_only_disposition.md). Re-tagged `stage-1-kpi-recorded` per ADR-0013 §"Retroactive re-tag". |
| Stage-2 (multi-tf + mediation) | h053_stage2_2026-05-01 | 2026-05-01 | a27a46de2bc18948f65 | descriptive-positive in-sample partial-R²; NDE point negative (reversal direction). Preserved at [reports/h053/stage2_multitf_mediation_disposition.md](../../../reports/h053/stage2_multitf_mediation_disposition.md). Re-tagged `stage-2-kpi-recorded`. |
| Stage-3 first-pass | h053_stage3_20260501T115445Z | 2026-05-01 | 6a001cf4a847c4d70 | Provisional `archive(null)` reversed by commit 8c1de7c due to Daily-405-gate truncation defect (only ~178 train sessions vs expected ~1900). Re-tagged `stage-3-first-pass-defective-substrate`. |
| Stage-3 v2 | h053_stage3_v2_20260503T144640Z | 2026-05-03 | 0cd96f55ca78916257e | ADR-0012-compliant first refactor post-Daily-gate-fix. Disposition `calibration-failed` (BSS ≤ 0 across all 4 arms). 13 audit findings (3 critical leakage). Re-tagged → KPI report card [v1](H053_kpi_report_v1.md) per ADR-0013. |
| Stage-3 v3 | h053_stage3_v3_20260503T204100Z | 2026-05-03 | 4cf291c036505f63f24 | Path B Round-1 attempt; closed F-2-1 (CPCV embargo) + F-2-2 (purged-K-fold inner CV) + F-2-3 (held-out iso source) but Round-1 audit found 2 critical residuals: F-V3-1 (CPCV still over full panel) + F-V3-2 (held-out iso not pre-test causal). Sidecar preserved at [runs/h053/stage3_v3/h053_stage3_v3_20260503T204100Z/sidecar.json](../../../runs/h053/stage3_v3/h053_stage3_v3_20260503T204100Z/sidecar.json) per ADR-0013 §4.1 non-loss; not promoted to v{N} kpi_report. |
| **Stage-3 v4 (this v2 source)** | fe051383e6c146bea93051b816c7e0a1 | 2026-05-03 | 4d5a826babf25cf2697 | Path B Round-2 remediation; closes all 6 v3 audit findings; verified clean by Round-3 audit (verdict ACCEPT). Canonical KPI source for this v2 report. |

## Failure log entries (cross-referenced)

| Entry ID | Date | Category | Resolution |
|---|---|---|---|
| 1 | 2026-05-03 | build-defect | Stage-3 v3 first-run `ModuleNotFoundError: No module named 'skie_ninja'`; fix: added `_REPO_ROOT / "src"` to sys.path. See [failure_log.md](failure_log.md) entry 1. |
| 2 | 2026-05-03 | build-defect | Stage-3 v3 second-run substrate not in this worktree; fix: passed `--substrate-path` to sibling worktree (inspiring-franklin-13a1f1). See [failure_log.md](failure_log.md) entry 2. |
| 3 | 2026-05-03 | build-defect | Stage-3 v4 first-run LW2008 API field-name mismatch (`delta_sharpe` should be `point_estimate`); fix: updated wrapper to read `result.point_estimate / result.lower / result.upper`. See [failure_log.md](failure_log.md) entry 3. |

## Audit-remediate-loop trails (Path B 3-round)

| Round | Trail path | Verdict | Findings |
|---|---|---|---|
| Round-1 (on v3 leakage-clean refactor) | [audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md) | block | 10 quant + 12 repro = 22 total; 2 critical leakage residuals |
| Round-2 (v4 remediation; closes 6 findings) | (subsumed in Round-1 trail's Path B addendum) | (remediation) | All 6 closed inline |
| Round-3 (v4 verification) | (subsumed in Round-1 trail's Path B addendum) | accept | 8 verification-pass findings; F-V4-7 + F-V4-8 minor residuals |

## Cross-validation methodology (per ADR-0013 §7)

- CPCV configuration per ADR-0012 binding: n_groups=10, n_test_groups=2, n_paths=C(10,2)=45 = AFML §12.5
- KS-monotonicity sub-criterion: cpcv-ks-not-converged on all 4 arms (KPI annotation; does not gate per ADR-0013 §7)
- Per-path Sharpe distribution moments: median + std + q05 + q95 reported above
- Wall-clock cap: 14400s per arm × 2 arms = 28800s; actual wall-clock per arm ~26-28s
- DSR computed under CPCV path distribution: see Sharpe-vs-passive table

## Cross-links

- ReproLog: [logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json](../../../logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json) ✓
- Sidecar: [runs/h053/stage3_v4/fe051383e6c146bea93051b816c7e0a1/sidecar.json](../../../runs/h053/stage3_v4/fe051383e6c146bea93051b816c7e0a1/sidecar.json)
- Pre-registered design: [design.md](design.md)
- Cross-hypothesis SPA panel: NOT YET BUILT; tracked under `P1-CROSS-HYPOTHESIS-SPA-PANEL` per ADR-0013 follow-ups

## Versioning

This is v2. v1 at [H053_kpi_report_v1.md](H053_kpi_report_v1.md) preserved verbatim per ADR-0013 §4.1 non-loss mandate.

A version increment to v3 would be triggered by substantive changes (e.g., re-running with the deferred follow-up KPIs Sortino/turnover/capacity computed; re-running after `P1-ADR-0013-DISPOSITION-FRAMEWORK-REFACTOR` lands; paper-trade-evaluated stage transition adding realized-vs-backtest Sharpe-within-CI observation).

## Operator review section (filled at promotion time per ADR-0013 §5.3)

- **Operator**: skoir
- **Promotion decision**: TO BE FILLED at next stage transition
- **Rationale**: TO BE FILLED — operator review of the v2 KPI report card values
- **Methodological-correctness acknowledgments**: NOT REQUIRED (no `leakage-canary-fail` or `repro-log-incomplete` annotations)
- **Cross-link to promotion log**: TBD at promotion (path: `logs/promotions/{run_id}_H053_{arm_id}_promotion.md`)

## Substantive interpretation (informational; per ADR-0013 §2 KPI-only philosophy)

After 3 rounds of audit-remediate-loop on Path B, the H053 09:45→10:30 ET ES/NQ slice exhibits:

1. **Sharpe-vs-passive uniformly marginal**: all 4 arms have CPCV path-Sharpe q05/q95 covering zero. Point estimates positive on 3 of 4 arms (ES Arm 2 +0.63, NQ Arm 1 +1.71, NQ Arm 2 +0.21) but with very wide CIs. The honest OOS-only path-Sharpe distribution does not establish a positive Sharpe at α=0.10 (q05 < 0).

2. **Sharpe-vs-bench (AR(1) lag-1) uniformly marginal**: LW2008 studentised CIs all cover zero. Point estimates positive (Δ Sharpe annualized +0.63 to +1.95). The H053 multi-tf signal does carry information beyond the AR(1)-lag-1 baseline at point-estimate level, but not at α=0.05 CI level on this OOS sample.

3. **BSS uniformly ≤ 0 under honest pre-test-causal calibration**: 1 flat (ES ElasticNet -0.010), 3 negative ([-0.061, -0.145]). The H053 multi-tf features cannot produce probability estimates that meaningfully beat the per-instrument climatological prior.

4. **Reliability slopes uniformly out-of-band** ([-0.05, +0.30]): under honest OOF calibration, the H053 probability estimates are systematically underconfident (slopes < 0.7) — the binned p_oof does not track binned d_actual at unit slope.

5. **DSR uniformly strongly negative** under CPCV-path deflation: even the median per-path Sharpe does not survive the family-selection-bias correction.

6. **Substantive empirical pattern** (informational): NQ ElasticNet's median Sharpe of +1.71 is the highest point-estimate across all 4 arms, but its CI is the widest [-3.23, +3.61]. The pattern of stronger NQ-than-ES results is consistent with the prior Stage-1 + Stage-2 reversal-direction findings; the wider NQ CI is consistent with NQ's higher intraday volatility footprint.

Per ADR-0013 §1, H053 progresses to `ninjascript-implemented` regardless of these KPI values. Operator promotion to paper-trade is discretionary on this report card per ADR-0013 §5.3.
