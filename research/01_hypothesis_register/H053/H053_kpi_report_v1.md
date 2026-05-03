---
hypothesis_id: H053
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-03
git_head: 0d1fb08442747cc07b63b33d173c20eaf8e65966
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar_scientific_payload_sha256: 0cd96f55ca78916257ee6a7e22a07d96c1a71490fdbf316d6a5ac75433b0bb28
run_id: h053_stage3_v2_20260503T144640Z
supersedes: null
superseded_by: H053_kpi_report_v2.md
---

# H053 — KPI Report Card v1

> **NOTE — RETROACTIVE RE-TAG.** This report card retroactively documents the H053 Stage-3 v2 disposition (commits [221a635](https://github.com), [0d1fb08](https://github.com)) under [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Retroactive re-tag of existing dispositions". The v1 results were emitted under the superseded ADR-0012 framework (`calibration-failed` disposition; binding gates) and have **known leakage defects** that were closed in v2 (Stage-3 v4) per Path B remediation. v1 is preserved verbatim per ADR-0013 §4.1 non-loss mandate. **For the canonical leakage-clean H053 KPI report, see [v2](H053_kpi_report_v2.md).**

- **Hypothesis**: 09:45→10:30 ET ES/NQ regression with multi-timeframe features + opening-bar mediator + categorical archetype-bias-target table
- **Design.md**: [design.md](design.md)
- **Stage at v1 emission**: `kpi-report-emitted` (retroactive re-tag from ADR-0012's `calibration-failed`)
- **Source disposition**: [reports/h053/stage3_full_disposition.md](../../../reports/h053/stage3_full_disposition.md)
- **Source audit trail**: [docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md](../../../docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md)
- **Stage tracker**: [stage.md](stage.md)
- **Failure log**: [failure_log.md](failure_log.md)

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | pass (14/14) | PIT canaries verified at [tests/integration/test_h053_pit_canaries.py](../../../tests/integration/test_h053_pit_canaries.py) at the run's HEAD (commit 221a635). |
| `bss-{positive,flat,negative}` | flat / negative | OOF isotonic-calibrated; per-instrument climatological prior. **Known leakage defect (F-2-3 from v2 audit)**: in-sample isotonic source inflates BSS optimistically. v2 (this report) values are upper bounds; honest BSS in v2 (Stage-3 v4 results — see report card [v2](H053_kpi_report_v2.md)). |
| `reliability-{in,out}-of-band` | sentinel-pass | **Sentinel placeholder**: v1 used `reliability_slope=1.0` when BSS was finite (placeholder for binding-gate flow per ADR-0012). Honest reliability slope computed in v2. |
| `repro-log-{complete,incomplete}` | partial | Sidecar payload includes git_head + dataset_checksum + scientific_payload_sha256 + run_id, but no canonical ReproLog at `logs/reproducibility/` was emitted (no `RunContext` wiring). |
| `dsr-{positive,marginal,negative,n/a}` | n/a | Family active size below activation threshold per CLAUDE.md §Evidence bar. |

## Performance KPIs (per ADR-0013 §3 + `rules/quant-project.md` §Reporting)

| Symbol | Arm | sharpe-vs-passive (CPCV median) | sharpe-vs-bench† | spa-family p | bss | max-dd | power-margin |
|---|---|---|---|---:|---|---|---|
| ES | ElasticNet | -0.112 (`marginal`) [-1.173, +0.715] DSR=-1.36 | +0.405 (placeholder†) | 0.367 | -0.013 (`flat`) | 1.146 (adverse) | 0.592 (low) |
| ES | LightGBM | +0.428 (`marginal`)‡ [-0.509, +1.547] DSR=-1.04 | +1.369 (placeholder†) | 0.367 | -0.176 (`negative`) | 0.621 (favorable) | 0.592 (low) |
| NQ | ElasticNet | +0.472 (`marginal`)‡ [-0.737, +1.195] DSR=-1.07 | +0.858 (placeholder†) | 0.309 | -0.010 (`flat`) | 0.654 (favorable) | 0.600 (low) |
| NQ | LightGBM | +0.422 (`marginal`)‡ [-1.096, +1.593] DSR=-1.39 | +1.308 (placeholder†) | 0.309 | -0.207 (`negative`) | 0.368 (favorable) | 0.600 (low) |

† `sharpe-vs-bench` numeric CI is from a Stage-3 v2 implementation **placeholder** (±0.1, `excludes_zero` hard-coded False per Round-1 audit F-2-5). Annotation in v1 was `sharpe-vs-bench-positive` derived from point alone; **annotation corrected in v2 via LW2008 differential CI implementation** — all 4 arms become `sharpe-vs-bench-marginal`.

‡ ES Arm 2, NQ Arm 1, NQ Arm 2 `sharpe-vs-passive` annotations were silently upgraded from `marginal` to `positive` in the original disposition memo; corrected in [ADR-0013 §"Retroactive re-tag"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) per Round-1 audit F-1-1 (CPCV q05/q95 cover zero on these 3 arms with point > 0 → `marginal` per ADR-0012 §B definition). Restated `marginal` in this v1 report.

## CPCV diagnostics (per ADR-0013 §7)

- Configuration: n_groups=10, n_test_groups=2, n_paths=C(10,2)=45 per AFML §12.5
- **Panel scope: full panel (IS+OOS concatenated)** — leakage defect (F-V3-1 from v3 audit); honest OOS-only CPCV in v2.
- KS-monotonicity: **NOT converged** on 3 of 4 arms (ES Arm 1 only at 0.044/converged; ES Arm 2 0.156, NQ Arm 1 0.067, NQ Arm 2 0.067 — all > 0.05 threshold)
- Per-path Sharpe distribution std: 0.56-0.81 annualized
- DSR (Bailey-LdP 2014 deflation): all 4 arms negative ([-1.04, -1.39])
- Wallclock cap respected: yes (no downsampling)

## Build / run history (v1 only — single Stage-3 v2 run)

| Stage | Run ID | Date | Sidecar SHA256 | Per-stage findings |
|---|---|---|---|---|
| Stage-3 v2 | h053_stage3_v2_20260503T144640Z | 2026-05-03 | 0cd96f55ca78916257e | First-pass disposition under ADR-0012 three-class rubric. Original disposition `calibration-failed` (BSS ≤ 0 on all 4 arms). 13 audit-trail findings (3 critical: F-2-1 CPCV over full panel, F-2-2 KFold-shuffle inner CV, F-2-3 in-sample isotonic source); robustness analysis at audit-trail §Robustness suggested calibration-failed disposition robust to leakage direction. |

Prior Stage-1 + Stage-2 results (preserved per ADR-0013 §4.1 non-loss):
- Stage-1 (mediator-only): NULL disposition under pre-ADR-0012 framework. [reports/h053/stage1_mediator_only_disposition.md](../../../reports/h053/stage1_mediator_only_disposition.md). Re-tagged `stage-1-kpi-recorded` per ADR-0013 §"Retroactive re-tag".
- Stage-2 (multi-tf + descriptive mediation): descriptive-positive (in-sample partial-R² CI excludes zero). [reports/h053/stage2_multitf_mediation_disposition.md](../../../reports/h053/stage2_multitf_mediation_disposition.md). Re-tagged `stage-2-kpi-recorded`.
- Stage-3 first-pass: provisional `archive(null)` reversed by [commit 8c1de7c](https://github.com) due to Daily-405-gate truncation defect. Re-tagged `stage-3-first-pass-defective-substrate`.

## Audit-remediate-loop trails

| Round | Trail path | Verdict |
|---|---|---|
| Round-1 (Stage-3 v2 design audit) | [audit_trail_2026-05-03_h053-stage3-v2.md](../../../docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md) | block (13 findings) |

## Cross-links

- ReproLog: NOT EMITTED in v1 (annotation-only; `repro-log-incomplete`)
- Sidecar: [runs/h053/stage3_v2/h053_stage3_v2_20260503T144640Z/sidecar.json](../../../runs/h053/stage3_v2/h053_stage3_v2_20260503T144640Z/sidecar.json)
- Pre-registered design: [design.md](design.md)

## Versioning

This is v1 (retroactive). Superseded by [v2](H053_kpi_report_v2.md) which closes the 6 audit findings via Path B (Stage-3 v4) leakage-clean refactor.

## Operator review

Not yet reviewed. v1 is a retroactive record; operator review applies to v2 going forward.
