# Phase P buildout — Regime-switching meta-allocation closed loop

- **Date opened**: 2026-06-02
- **Authority**: [ADR-0029](../../docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md) (center-of-gravity); operator directive 2026-06-02.
- **Companion**: [memo_regime-switching-closed-loop-foundations_2026-06-02.md](../../docs/research_notes/memo_regime-switching-closed-loop-foundations_2026-06-02.md) (lit synthesis).
- **Center claim under test**: does the closed-loop allocator beat BOTH buy-and-hold AND equal-weight 1/N out-of-sample? (ADR-0029 §D-4)

This is the staged roadmap from the current arm library to a forward-validated closed-loop meta-allocator. Each cycle lands code + tests under audit-remediate-loop discipline (3-round cap per SKILL.md). Cycles are sequenced by dependency; wall-clock estimates are pre-empirical (anchored on prior-phase precedent), flagged for revision.

## Sequencing (dependency-ordered)

```
P-1 MPV2 substrate  ──►  P-2 early-warning   ──►  P-5 closed-loop
(per-session emit)        primitive (Thrust 1)      assembly + MPV2
      │                          │                  forward-validation
      │                   P-3 ergodicity sizing  ───────┘
      │                   primitives (Thrust 2)
      └──► P-4 cross-arm correlation matrix (one-shot; gates P-3.d)
```

## P-1 — MPV2 per-session-returns substrate (`P1-MPV2-PER-SESSION-RETURNS-INTEGRATION`, elevated to BLOCKING-BEFORE-CLOSED-LOOP-CLAIM)

The spine. Current MPV1 builds on per-fold MPPMs (too coarse for a session-cadence allocator). Re-emit each underlying orchestrator (H050, H052a, H053 v4, H054, H055 v2, H060, H062, H065, H067, H068) with a `per_session_logret_aggregate` array in its sidecar (the schema field already landed Phase O.13 for H062/H055; extend to the rest). Then build a session-aligned cross-arm reward matrix (join on session-calendar, not `t mod n` — closes `P1-MPV1-CALENDAR-ALIGNMENT`).

- **Deliverable**: every arm sidecar carries `per_session_logret_aggregate`; `scripts/build_mpv2_reward_matrix.py` produces the calendar-aligned matrix + provenance.
- **Audit**: reproducibility-verifier (sidecar schema + checksum) + quant-auditor (calendar-join correctness, no look-ahead in the alignment).
- **Wall-clock**: arm re-emissions are mostly smoke-cadence (~minutes each) except H050 (~7-8 hr full); most arms have committed sidecars already — only the schema field needs back-filling.
- **Blocks**: P-5.

## P-2 — Early-warning detector primitive (`P1-EARLY-WARNING-DETECTOR-PRIMITIVE`, Thrust 1)

`src/skie_ninja/inference/early_warning.py`:
- `critical_slowing_down(path, window) -> {variance_tau, ar1_tau}` (Kendall-τ of rolling variance + lag-1 AR; Dakos 2012 estimator; variance-weighted per Guttal 2016).
- `cusum_detector(excess_returns, k, h)` (Page 1954) + optional `glr_detector` (Lorden 1971).
- `drawdown_velocity(equity_path, confidence, rho)` (Bailey-López de Prado 2015 triple-penance band).
- `EarlyWarningState` composing the three into an `armed / fired` annotation feeding a partial-de-risk fraction.
- **Threshold calibration is a separate follow-up** (`P1-EARLY-WARNING-THRESHOLD-CALIBRATE`, BLOCKING-BEFORE-CLOSED-LOOP-RUN): calibrate window/`k`/`h`/confidence on a pre-OOS holdout for a target lead-time/false-positive operating point. No hand-set thresholds.
- **Audit**: quant-auditor (CUSUM recursion correctness, Kendall-τ, drawdown-quantile math) + literature-check (method-citation fidelity).
- **Tests**: synthetic regime-shift fixtures (step-change in mean/variance) — detector fires before the post-change window completes; null fixture — false-positive rate within the calibrated bound.
- **Status (2026-06-02): ✓ primitive landed** at [src/skie_ninja/inference/early_warning.py](../../src/skie_ninja/inference/early_warning.py) (3 detectors: CSD variance/AR-τ, lower-CUSUM, drawdown/TuW + streaming composite mirroring the bocd interface shape; optional frozen in-regime reference). 39 unit tests at [tests/unit/test_early_warning.py](../../tests/unit/test_early_warning.py); ruff-clean. R1 audit-remediate-loop (quant-auditor + code-reviewer) closed 2 critical (F-1 near-zero-σ false-fire; F-2 trailing-reference self-cancel) + 2 major + minors; trail [docs/audits/audit_trail_2026-06-02_phase-p-early-warning-primitive.md](../../docs/audits/audit_trail_2026-06-02_phase-p-early-warning-primitive.md). Remaining: `P1-EARLY-WARNING-THRESHOLD-CALIBRATE` (BLOCKING-BEFORE-CLOSED-LOOP-RUN), `P1-EARLY-WARNING-CSD-SURROGATE-NULL`, `P1-EARLY-WARNING-INCREMENTAL-UPDATE` (perf).

## P-3 — Ergodicity sizing primitives (Thrust 2)

- **P-3.a `P1-KPI-MEDIAN-HEADLINE-PRIMITIVE`** (BLOCKING-BEFORE-NEXT-KPI-EMISSION): forward-projection block + §0 header report median/time-average path as headline; ensemble mean → caveated annotation; emit `time-average-vs-ensemble-gap-{small,large}`. Amends the KPI template (ADR-0026 §D-1 per ADR-0029 §D-3.1).
- **P-3.b `P1-CPPI-FLOOR-RATCHET-SIZING-PRIMITIVE`**: `cppi_position_size(equity, floor, m)` + peak-referenced ratcheting floor with above-50%-ruin-line buffer (Black-Jones 1987 / Black-Perold 1992 / Grossman-Zhou 1993). Integrates with existing `compute_position_size`.
- **P-3.c `P1-JOINT-KELLY-CONCURRENT-SIZING-PRIMITIVE`**: `joint_kelly_fractions(arm_edges, arm_cov)` with total-concurrent-exposure cap (Kelly 1956 + MTZ 2011). Caps the promotable Kelly multiplier at 1.0; super-Kelly retained sandbox-only with `super-kelly-time-average-dominated` annotation.
- **Audit**: quant-auditor (Kelly-ceiling reasoning, CPPI gap-through floor buffer, joint-Kelly over-bet avoidance) + literature-check.
- **Tests**: CPPI floor never breached frictionless; joint-Kelly total exposure < Σ standalone; median-headline regression on an existing v(N) card.
- **Status (2026-06-02): P-3.b + P-3.c ✓ landed** at [src/skie_ninja/sizing/ergodicity.py](../../src/skie_ninja/sizing/ergodicity.py) (`cppi_risk_overlay` floor-ratchet + `joint_kelly_fractions` with no-ruin SLSQP constraint + `bankrupts_on_path` + exact cap renormalization; re-exported from the sizing package root). 27 unit tests at [tests/unit/test_sizing_ergodicity.py](../../tests/unit/test_sizing_ergodicity.py); ruff-clean. R1 audit-remediate-loop (quant-auditor + code-reviewer) closed 6 majors (F-1-1 joint-Kelly could return a bankrupting fraction; F-1-2 floored growth_rate masked ruin; F-1-3/F-1-4 cap-saturation test tautologies; CR-1-1/CR-1-2 silent fail-open; CR-1-3 scipy narrowing) + minors; trail [docs/audits/audit_trail_2026-06-02_phase-p-ergodicity-sizing-primitives.md](../../docs/audits/audit_trail_2026-06-02_phase-p-ergodicity-sizing-primitives.md). **P-3.a (`P1-KPI-MEDIAN-HEADLINE-PRIMITIVE`) still pending** (reporting primitive; BLOCKING-BEFORE-NEXT-KPI-EMISSION, not before the closed-loop run). New follow-up `P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION` (floor_fraction/multiplier/min_floor holdout calibration). Pre-existing-unrelated: `P1-SIZING-COMPUTE-POSITION-SIZE-TESTS-STALE` (2 stale `compute_position_size` tests, confirmed pre-existing via stash-attribution).

## P-4 — Cross-arm correlation matrix (`P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE`, elevated)

One-shot diagnostic on the P-1 session-aligned reward matrix. Independence is load-bearing for the D-3.d variance-~1/N claim — if arms are highly correlated, pooling buys little. Reports the correlation matrix + effective-breadth estimate (Grinold √breadth). Gates whether the closed loop can realistically reduce path-dependence.

## P-5 — Closed-loop assembly + MPV2 forward-validation (the falsifiable center)

`scripts/run_mpv2_closed_loop.py`: switching-bandit (ADR-0018 §D-4) over the P-1 reward matrix, with P-2 early-warning de-risk + BOCD confirmation gating reallocation, P-3 ergodicity sizing (Kelly ≤ 1.0, CPPI floor, joint-Kelly concurrent). Walk-forward OOS. **Causal-alignment invariant (BLOCKING, per ADR-0029 §D-4):** arm-k's session-t reward uses only arm-k decisions with data ≤ t (walk-forward-frozen params, not re-fitted on the evaluation window); 1/N + buy-and-hold built on the identical causal per-session matrix with no ex-post arm selection; the full-sample oracle stays a labeled non-tradeable diagnostic excluded from the beat-target; PIT-canaried via the Cycle-4 leak canaries (risk R-5).

- **The test (ADR-0029 §D-4)**: closed-loop allocator vs (i) buy-and-hold, (ii) equal-weight 1/N (DeMiguel-Garlappi-Uppal 2009 — the stringent benchmark), on per-session reward sequences. Paired stationary-bootstrap CI on the differential. MPV2 gets its own pre-registration entity (`research/01_meta_portfolio/MPV2/` per ADR-0020) with frozen §1-§7.
- **Honest exit**: if the allocator does not beat 1/N OOS, record it (ADR-0013 non-loss). Per Lo 2004, the answer may itself be regime-dependent — report which regimes (if any) the closed loop adds value in.
- **Audit**: full parallel triad (quant + lit + repro) per the post-run audit gate (ADR-0011).

## Risk register

| # | Risk | Mitigation |
|---|---|---|
| R-1 | Early-warning false positives churn capital (de-risk → reverse) | partial de-risk only; BOCD gates full reallocation; calibrate false-positive rate on holdout (P-2) |
| R-2 | Arms too correlated → pooling buys no variance reduction | P-4 correlation matrix is a gate, run before claiming D-3.d benefit |
| R-3 | Allocator does not beat 1/N OOS | this is a VALID falsification, not a failure to hide — record per non-loss; 1/N is hard to beat (DGU 2009) |
| R-4 | Switching cost / lag erodes the edge | switching-cost regret is bounded Θ(T^{2/3}) (Dekel-Ding-Koren-Peres, ADR-0018); model explicit cost per reallocation |
| R-5 | Look-ahead in calendar alignment or threshold calibration | P-1 calendar-join + P-2 pre-OOS-holdout calibration both PIT-canaried |
| R-6 | Per-session emission inconsistency across heterogeneous arm sidecars | adapter layer; schema-version gate (`P1-MPV1-EXTEND-ARM-UNIVERSE` schema heterogeneity) |

## Scheduled audit-remediate-loops

1. P-1 (repro + quant) — sidecar schema + calendar-join.
2. P-2 (quant + lit) — detector method-correctness + citation fidelity.
3. P-3 (quant + lit) — sizing method-correctness + Kelly/CPPI/ergodicity claims.
4. P-5 (quant + lit + repro) — full post-run gate on the forward-validation result.

## New follow-ups registered by Phase P

BLOCKING-BEFORE-CLOSED-LOOP-RUN: `P1-EARLY-WARNING-DETECTOR-PRIMITIVE`, `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`, `P1-CPPI-FLOOR-RATCHET-SIZING-PRIMITIVE`, `P1-JOINT-KELLY-CONCURRENT-SIZING-PRIMITIVE`, `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` (elevated), `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE` (elevated).
BLOCKING-BEFORE-NEXT-KPI-EMISSION: `P1-KPI-MEDIAN-HEADLINE-PRIMITIVE`.
Non-blocking: `P1-MPV1-CALENDAR-ALIGNMENT`, `P1-MPV1-EXTEND-ARM-UNIVERSE`, `P1-ADR-0029-GLOSSARY-CASCADE`, `P1-ADR-0029-TEMPLATE-CASCADE`, `P1-ADR-0029-KPI-MEDIAN-HEADLINE-RETROACTIVE`, `P1-MPV2-PRE-REGISTRATION`.

Registered by the P-2 landing (2026-06-02): `P1-EARLY-WARNING-CSD-SURROGATE-NULL` (BLOCKING-BEFORE-CSD-GATING — surrogate/bootstrap-null significance for the CSD Kendall-τ per Dakos 2012, replacing the raw fixed-τ cutoff; CSD is advisory-only until landed), `P1-EARLY-WARNING-INCREMENTAL-UPDATE` (non-blocking perf — incremental detector update vs the current O(n)-per-evaluate buffer recompute).

## P-1 + P-4 + P-5 status (2026-06-02): MPV2 pre-reg + closed-loop machinery landed (synthetic-validated)

The MPV2 pre-registration ([research/01_meta_portfolio/MPV2/design.md](../../research/01_meta_portfolio/MPV2/design.md)) froze the **arm set {H050, H055, H060, H062}** (one representative per signal class — HMM-gated directional / mean-reversion / daily-trend / intraday-breakout — chosen to MAXIMIZE de-correlation, the precondition for the ergodicity pooling lift; H052a/H053/H054/H065/H067/H068 reserved for v2 as correlated/null). The P-1 reward-matrix builder + P-4 cross-arm correlation diagnostic + P-5 closed-loop runner (bandit → early-warning de-risk → CPPI sizing, vs sized-1/N + sized-B&H with paired-bootstrap CI) all landed in [scripts/run_mpv2_closed_loop.py](../../scripts/run_mpv2_closed_loop.py), validated end-to-end on a regime-structured synthetic fixture (21 tests). R1 audit-remediate-loop (quant + code-reviewer): the **look-ahead / causal-alignment invariant verified clean** (the load-bearing risk); 1 critical (F-1-1 sized-consistent benchmarks) + 6 majors remediated; trail [docs/audits/audit_trail_2026-06-02_mpv2-closed-loop.md](../../docs/audits/audit_trail_2026-06-02_mpv2-closed-loop.md). **The terminal P-5 verdict (does the closed loop beat 1/N + B&H OOS?) requires the real-data run** — gated on `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` (P-1 arm re-emission, multi-hour compute on the regenerated substrate). BLOCKING-before-real-verdict residuals: `P1-MPV1-CALENDAR-ALIGNMENT`, `P1-MPV2-FULL-SURVIVAL-VECTOR`, `P1-MPV2-JOINT-BOOTSTRAP-CONJUNCTIVE`, `P1-MPV2-REPROLOG-WIRE`, `P1-MPV2-BH-SERIES-WIRE`, `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`, `P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION`. Non-blocking: `P1-MPV2-DATACLASS-RETURNS`, `P1-PAIRED-BOOTSTRAP-CI-SHARED-PRIMITIVE`.
