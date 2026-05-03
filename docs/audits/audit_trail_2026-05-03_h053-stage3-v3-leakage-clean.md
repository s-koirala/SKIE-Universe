---
title: H053 Path B leakage-clean refactor (Stage-3 v3 → v4) — 3-round audit-remediate-loop trail
date: 2026-05-03
type: audit_trail
status: complete (3 rounds; SKILL.md cap reached; verdict ACCEPT)
phase: H053 Cycle 10 Path B
deliverables_landed:
  - scripts/run_h053_stage3_v3.py (NEW; Round-1 attempt; 2 critical leakage residuals)
  - scripts/run_h053_stage3_v4.py (NEW; Round-2 remediation; verdict ACCEPT)
  - runs/h053/stage3_v3/h053_stage3_v3_20260503T204100Z/sidecar.json (NEW; preserved per ADR-0013 §4.1)
  - runs/h053/stage3_v4/d0ada892ca194becbcf7879f8b5a842b/sidecar.json (NEW; v4 first-run with LW2008 build defect; preserved)
  - runs/h053/stage3_v4/fe051383e6c146bea93051b816c7e0a1/sidecar.json (NEW; v4 canonical run; ACCEPT verdict)
  - logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json (NEW; canonical ReproLog per ADR-0013 §4.1 #4)
  - research/01_hypothesis_register/H053/H053_kpi_report_v1.md (NEW; retroactive re-tag of Stage-3 v2)
  - research/01_hypothesis_register/H053/H053_kpi_report_v2.md (NEW; canonical Path B output)
  - research/01_hypothesis_register/H053/stage.md (NEW; first stage tracker per ADR-0013 §1.1)
  - research/01_hypothesis_register/H053/failure_log.md (NEW; first failure log per ADR-0013 §4.2)
loop_rounds: 3
verdict: accept
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
v3_sidecar_sha256: 4cf291c036505f63f24e2a4ddaabc1772bdb1de973d4db48b3e76967fe6f6371
v4_sidecar_sha256: 4d5a826babf25cf2697f8df5e57c9b6abf48b4a87b9a3b3ad57cb9a2e2bcd1f8
git_head: 0d1fb08442747cc07b63b33d173c20eaf8e65966 (worktree dirty; ADR-0013 + this trail uncommitted at audit close)
---

# H053 Path B — Leakage-clean refactor of Stage-3 v2

## Context

H053 Stage-3 v2 (commits `28f93ec`, `221a635`, `0d1fb08`; audit trail [audit_trail_2026-05-03_h053-stage3-v2.md](audit_trail_2026-05-03_h053-stage3-v2.md)) was identified by Round-1 quant-auditor `ab9ea26236a94fabd` as having 3 critical leakage defects:

- **F-2-1** (critical): CPCV runs over FULL panel (train+test concatenated) with `embargo=0`, allowing train/test segments to abut.
- **F-2-2** (critical): Inner `KFold(shuffle=True, random_state=42)` for hyperparameter selection violates `rules/quant-project.md` §Time-series integrity.
- **F-2-3** (critical): OOF isotonic fits on `arm_local.predict(X_train[train_idx])` — in-sample to inner arm fit.

Per the user's 2026-05-03 directive ("let us accomplish path b then compile new results. then we will proceed with path a"), Path B is the [P1-H053-STAGE3-V2-ROUND-2-REMEDIATION](.) follow-up's full execution. This trail consolidates the 3-round audit-remediate-loop on the leakage-clean refactor.

ADR-0013 ([docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)) was adopted in the same session and is in force; H053's KPI report cards v1 + v2 conform to its §3 canonical structure.

## Round-1 — quant-auditor + reproducibility-verifier on Stage-3 v3

Stage-3 v3 [scripts/run_h053_stage3_v3.py](../../scripts/run_h053_stage3_v3.py) attempted to close F-2-1/F-2-2/F-2-3 via:
- F-2-1: `cpcv_path_sharpe(..., embargo=2)` (= 2 × `label_horizon=1`)
- F-2-2: `purged_kfold_split(n_splits=3, ...)` for inner CV
- F-2-3: 80/20 chronological split of inner-train; first 80% = inner-arm-train, last 20% = inner-iso-fit (held-out, NOT pre-test causal)

Run on post-Cell-I substrate (substrate_dataset_checksum `bc06b4e1...`); sidecar at [runs/h053/stage3_v3/h053_stage3_v3_20260503T204100Z/sidecar.json](../../runs/h053/stage3_v3/h053_stage3_v3_20260503T204100Z/sidecar.json) (sha256=4cf291c036505f63).

### Round-1 quant-auditor (`acb41ffd953b6fd58`) — verdict BLOCK

10 findings (3 critical, 5 majors, 2 minors). Critical findings:

| ID | Severity | Finding | v4 closure |
|---|---|---|---|
| F-V3-1 | **critical** | CPCV runs over FULL panel; `embargo=2` closes (a) but not (b); IS rows can still appear in CPCV training folds for IS-region test blocks | **CLOSED in v4** — CPCV runs on `len(X_test)` only (OOS test region) |
| F-V3-2 | **critical** | Held-out iso source (last 20% of inner-train) is NOT strictly pre-test causal; for late-region test blocks, inner-iso-fit overlaps test era; for early-region test blocks, iso is anti-causal | **CLOSED in v4** — `pre_test_train = tr_sorted[tr_sorted < min(te)]` filters to strictly-before; `pre_test_skips` counter for folds where `len(pre_test_train) < 150` |
| F-V3-6 | major | No `RunContext`/`ReproLog` wiring; `repro-log-complete` annotation is string literal | **CLOSED in v4** — `with RunContext(phase='h053_stage3_v4', ...)` wraps main; canonical ReproLog at `logs/reproducibility/{run_id}.json` |

Majors:

| ID | Severity | Finding | v4 closure |
|---|---|---|---|
| F-V3-3 | major | Inner CV n_splits=3 under-powered for 9-cell ElasticNet + 4-cell LightGBM grid | **CLOSED in v4** — `_INNER_CV_FOLDS_V4=5` per AFML §7.4.3 default |
| F-V3-4 | major | Embargo=2 weak for AFML §7.4.2 `h ≈ 0.01·T`; T≈1900 → h≈19 (full panel) or T≈370 → h≈4 (OOS-only) | **CLOSED in v4** — `_CPCV_EMBARGO=4` (per AFML for OOS-only panel size) |
| F-V3-5 | major | `sharpe_vs_bench` CI is `NaN` with `ci_method='deferred'`; annotation `sharpe-vs-bench-positive` derived from point alone | **CLOSED in v4** — `ledoit_wolf_2008_differential_ci` invoked; LW2008 studentised pivotal CI; n_bootstrap=2000 |
| F-V3-7 | major | Hansen SPA m=2 degenerate-family annotation gap | residual; minor add-on follow-up `P1-H053-SPA-M2-DEGENERATE-ANNOTATION` |
| F-V3-8 | minor | Reliability slope no CI | residual; follow-up `P1-H053-RELIABILITY-SLOPE-CI` |
| F-V3-9 | minor | AR(1) bench missing `over('symbol')` partition guard | residual; defensive (single-symbol-per-call usage is safe); follow-up `P1-H053-AR1-OVER-SYMBOL` |
| F-V3-10 | minor | Leakage-canary annotation hard-coded string literal; canary not re-run inline | residual; follow-up `P1-H053-STAGE3-V4-CANARY-INLINE-VERIFY` |

### Round-1 reproducibility-verifier (`aa828a2b7ea1ebb07`) — verdict ACCEPT-WITH-RESIDUALS

12 findings (1 critical, 4 majors, 7 minor-or-pass). Closures:

| ID | Severity | Finding | v4 status |
|---|---|---|---|
| R-V3-1 to R-V3-7 | pass / minor | All sidecar payload completeness + substrate provenance + determinism checks pass | PASS |
| R-V3-8 | major | `pyproject.toml` missing `[build-system]` declaration; v2 also fails fresh-venv | residual; follow-up `P1-PYPROJECT-BUILD-SYSTEM-DECLARE`; build-defect entry 1 in [failure_log.md](../../research/01_hypothesis_register/H053/failure_log.md) |
| R-V3-9 | major | Substrate path hard-coded sibling-worktree absolute Windows path; non-portable | residual; follow-up `P1-H053-STAGE3-SUBSTRATE-CONFIG-PIN`; build-defect entry 2 in failure_log |
| R-V3-10 | major | Worktree dirty at run-time; v3 script untracked; recorded git_head underspecifies actual code state | operator concern; resolved at commit time |
| R-V3-11 | major | ReproLog not emitted; `logs/reproducibility/` empty | **CLOSED in v4** via F-V3-6 |
| R-V3-12 | minor | `pip-freeze` SHA missing | **CLOSED in v4** via F-V3-6 (RunContext captures it) |

## Round-2 — remediation: Stage-3 v4

[scripts/run_h053_stage3_v4.py](../../scripts/run_h053_stage3_v4.py) closes all 6 of F-V3-1, F-V3-2, F-V3-3, F-V3-4, F-V3-5, F-V3-6.

### Build defect during Round-2

v4 first-run (run_id `d0ada892ca194becbcf7879f8b5a842b`) failed at F-V3-5 closure due to LW2008 API field-name mismatch: wrapper read `result.delta_sharpe` but the canonical `DifferentialCIResult` dataclass exposes `point_estimate`, `lower`, `upper`. Wrapper failure caused all 4 LW2008 invocations to emit `nan`-CI fallback; CPCV + BSS + RunContext closures all worked correctly. Sidecar preserved per ADR-0013 §4.1 non-loss. Failure log entry 3 in [research/01_hypothesis_register/H053/failure_log.md](../../research/01_hypothesis_register/H053/failure_log.md).

Wrapper fixed inline; v4 re-run (run_id `fe051383e6c146bea93051b816c7e0a1`) is the canonical Path B output.

### Round-2 results (canonical Stage-3 v4)

Sidecar `4d5a826babf25cf2697`; ReproLog at [logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json](../../logs/reproducibility/fe051383e6c146bea93051b816c7e0a1.json).

| Symbol | Arm | Sharpe-vs-passive (OOS-only CPCV) | Sharpe-vs-bench (LW2008) | BSS (pre-test causal) | Reliability slope | Max-DD | SPA p |
|---|---|---|---|---:|---:|---|---:|
| ES | ElasticNet | median=+0.39 CI=[-1.43, +3.93] DSR=-3.55 KS=NOT-converged (`marginal`) | Δ=+0.63 CI=[-1.61, +2.92] excludes-zero=False (`marginal`) | -0.010 (`flat`) | +0.08 (out-of-band) | 1.44 (adverse) | 0.367 (rejects) |
| ES | LightGBM | median=+0.63 CI=[-2.28, +3.26] DSR=-3.61 KS=NOT-converged (`marginal`) | Δ=+1.95 CI=[-0.51, +4.36] excludes-zero=False (`marginal`) | -0.061 (`negative`) | +0.30 (out-of-band) | 0.62 (favorable) | 0.367 (rejects) |
| NQ | ElasticNet | median=+1.71 CI=[-3.23, +3.61] DSR=-3.29 KS=NOT-converged (`marginal`) | Δ=+1.47 CI=[-1.07, +3.82] excludes-zero=False (`marginal`) | -0.145 (`negative`) | -0.05 (out-of-band) | 0.55 (favorable) | 0.290 (rejects) |
| NQ | LightGBM | median=+0.21 CI=[-3.75, +1.98] DSR=-3.81 KS=NOT-converged (`marginal`) | Δ=+1.89 CI=[-0.34, +4.12] excludes-zero=False (`marginal`) | -0.060 (`negative`) | +0.11 (out-of-band) | 0.37 (favorable) | 0.290 (rejects) |

LW2008 block_length=1.0 in all 4 invocations (Politis-White 2004 selected b=1 because the strategy-minus-AR(1)-bench differential is essentially uncorrelated). Bandwidths via NW1994 plug-in per replicate: 1, 3, 3, 8. n_degenerate_resamples=0 throughout. pre_test_skips=1 per arm × symbol (1 of 5 inner CPCV folds skipped because pre-test region <150 rows for early-region test blocks).

## Round-3 — verification audit

### Round-3 quant-auditor (`ab0bc634f28343b44`) — verdict ACCEPT

8 verification findings (all minor, marked `verification-gap` category indicating successful closure; no regressions):

| ID | Severity | Verification |
|---|---|---|
| F-V4-1 | minor (closure verified) | F-V3-1 closed clean: CPCV `n_samples=len(X_test)`; closures index exclusively into `X_test`/`y_test`; no IS-leakage path |
| F-V4-2 | minor (closure verified) | F-V3-2 closed clean: `pre_test_train = tr_sorted[tr_sorted < min(te)]`; `pre_test_skips=1` per cell consistent with early-region test blocks |
| F-V4-3 | minor (closure verified) | F-V3-3 closed clean: `_INNER_CV_FOLDS_V4=5` consumed in both `_fit_arm{1,2}_v4` |
| F-V4-4 | minor (closure verified) | F-V3-4 closed clean: `_CPCV_EMBARGO=4` per AFML §7.4.2 `h ≈ 0.01·T` for OOS T≈370 |
| F-V4-5 | minor (closure verified) | F-V3-5 closed clean: LW2008 imported correctly; field names `point_estimate`/`lower`/`upper`; annualized × sqrt(252); excludes_zero computed; finite numeric CIs in sidecar |
| F-V4-6 | minor (closure verified) | F-V3-6 closed clean: `RunContext` imported + wraps main; ReproLog file exists with canonical fields (git_head, env_id, model_hash, dataset_checksums, rng_seed, run_id) |
| F-V4-7 | minor | OOS-only CPCV path-Sharpe std doubled vs v3 (full-panel) — consistent with CLT scaling + smaller panel (370 vs 1700 rows). DSR more negative — consistent with Bailey-LdP 2014 deflation under wider std. LW2008 block_length=1.0 expected because AR(1) bench absorbs lag-1 component. **Reporting note**: KPI report card v2 surfaces this panel-scope-OOS-only caveat to prevent v1 ↔ v2 std/DSR head-to-head confusion. |
| F-V4-8 | minor | CPCV closures call `_fit_arm{1,2}_v4` internally → hyperparameter selection inside CPCV is decoupled from headline `arm{1,2}_meta.best_cell` (which describes FULL-IS fit only). This is the canonical AFML §12 refit-inside-CPCV pattern. **Reporting note**: KPI report card v2 documents this. |

### Path B verdict

**Accept**. All 6 v3 audit findings closed clean in v4; verified independently by Round-3 quant-auditor. F-V4-7 + F-V4-8 are reporting residuals (handled in KPI report card v2 narrative), not regressions. Path B audit-remediate-loop closes per SKILL.md 3-round cap.

## Substantive empirical interpretation (informational; no gates fire under ADR-0013 §1)

Under honest leakage-clean methodology (v4), the H053 09:45→10:30 ET ES/NQ slice continues to show:

1. **Sharpe-vs-passive uniformly `marginal`** across all 4 (arm × symbol) cells. Point estimates positive on 3 of 4 arms (NQ ElasticNet leads at +1.71), but CIs all cover zero.
2. **Sharpe-vs-bench (AR(1) lag-1) uniformly `marginal`** under LW2008 differential CI. Point estimates +0.63 to +1.95 annualized; CIs all cover zero.
3. **BSS uniformly ≤ 0** under pre-test-causal calibration (1 flat at -0.010, 3 negative at [-0.06, -0.15]).
4. **Reliability slopes uniformly out-of-band** ([-0.05, +0.30] vs project-operational [0.7, 1.3]). The H053 probability estimates are systematically underconfident relative to climatological prior under honest OOF calibration.
5. **DSR uniformly strongly negative** under CPCV-path deflation.

These are KPI annotations under ADR-0013 §1, not gates. H053 progresses to `ninjascript-implemented` per §5 mandate regardless.

## Comparison vs v1 (Stage-3 v2 first-pass under ADR-0012)

| KPI | v1 (Stage-3 v2; leakage) | v2 (Stage-3 v4; leakage-clean) | Direction |
|---|---|---|---|
| Sharpe-vs-passive median (ES/NQ × Arm1/Arm2) | -0.11 / +0.43 / +0.47 / +0.42 | +0.39 / +0.63 / +1.71 / +0.21 | Mixed; widely-varying due to OOS-only panel |
| Sharpe-vs-passive CI std | 0.56-0.81 | 1.76-2.24 | **Wider** (CLT: smaller panel → wider CI) |
| DSR | -1.04 to -1.39 | -3.29 to -3.81 | **More negative** (wider std → larger deflation) |
| BSS (ElasticNet ES/NQ) | -0.013 / -0.010 | -0.010 / -0.145 | Mixed; ES essentially identical, NQ much worse under pre-test causality |
| BSS (LightGBM ES/NQ) | -0.176 / -0.207 | -0.061 / -0.060 | **Improved** (held-out isotonic fit produces tighter calibration on overfit-prone arm) |
| Reliability slope | sentinel-1.0 (placeholder) | actual: [-0.05, +0.30] | **Computed honestly**; reveals systematic underconfidence not visible in v1 |
| Sharpe-vs-bench CI | placeholder ±0.1 | LW2008: ±[1.6, 4.4] | **Real CI computed**; v1 placeholder annotation `positive` corrected to `marginal` |
| ReproLog | NOT emitted | canonical at logs/reproducibility/{run_id}.json | **Emitted** |

Net: the v1 → v2 transition closes 6 leakage / methodological-correctness gaps. The substantive disposition (H053 09:45→10:30 ET slice does not establish a clear-CI Sharpe-vs-passive at α=0.10 on ES/NQ) is preserved across both — the leakage in v1 was not the cause of the marginal-Sharpe finding, but the leakage in v1 obscured the honest CI widths and reliability-slope-out-of-band finding.

## Residuals (tracked follow-ups)

- `P1-H053-SPA-M2-DEGENERATE-ANNOTATION` (operational): SPA at m=2 is operationally degenerate; report Bonferroni-adjusted p alongside as sanity check
- `P1-H053-RELIABILITY-SLOPE-CI` (operational): bootstrap CI on reliability slope (current point estimates decisively out-of-band so CI does not change interpretation)
- `P1-H053-AR1-OVER-SYMBOL` (defensive): explicit `over('symbol')` partition for AR(1) lag-1 bench computation
- `P1-H053-STAGE3-V4-CANARY-INLINE-VERIFY` (operational): invoke canary suite as subprocess at script start
- `P1-H053-SORTINO-COMPUTE` + `P1-H053-TURNOVER-COMPUTE` + `P1-H053-CAPACITY-EMPIRICAL`: mandatory `rules/quant-project.md` §Reporting KPIs deferred from this v2 emission
- `P1-PYPROJECT-BUILD-SYSTEM-DECLARE` (project-wide): add `[build-system]` to pyproject.toml so editable install is reproducible from a fresh clone
- `P1-H053-STAGE3-SUBSTRATE-CONFIG-PIN`: pin substrate path via `SKIE_SHARED_DATA` env var + `ProjectPaths` resolver
- `P1-H053-NINJASCRIPT-IMPL` (BLOCKING per ADR-0013 §5; next mandatory transition)
- `P1-CROSS-HYPOTHESIS-SPA-PANEL` (per ADR-0013): cross-link from KPI report card v2 once the panel is built
- `P1-ISO-HELDOUT-FRACTION-CALIBRATION` (operational): empirical calibration of the 0.20 chronological-cut fraction

## Cross-references

- [ADR-0013](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — disposition philosophy in force
- [audit_trail_2026-05-03_h053-stage3-v2.md](audit_trail_2026-05-03_h053-stage3-v2.md) — the precipitating Stage-3 v2 audit (F-2-1/F-2-2/F-2-3 source)
- [audit_trail_2026-05-03_adr-0013-permanent-exploration.md](audit_trail_2026-05-03_adr-0013-permanent-exploration.md) — concurrent ADR-0013 audit-remediate trail
- [research/01_hypothesis_register/H053/H053_kpi_report_v1.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v1.md) — retroactive re-tag
- [research/01_hypothesis_register/H053/H053_kpi_report_v2.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v2.md) — canonical Path B output
- [research/01_hypothesis_register/H053/stage.md](../../research/01_hypothesis_register/H053/stage.md) — stage tracker
- [research/01_hypothesis_register/H053/failure_log.md](../../research/01_hypothesis_register/H053/failure_log.md) — append-only failure log
