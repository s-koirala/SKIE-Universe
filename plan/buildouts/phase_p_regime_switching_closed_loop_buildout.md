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

## P-1 real-data execution drive — milestone 1 (2026-06-02 PM): substrate regen + 2 dated arms + calendar-join landed + first real 2-arm result

The multi-hour real-data drive (operator-authorized "launch it now / I drive it and report") reached its first calendar-aligned real-data result. Load-bearing decisions made + recorded here so they are durable across sessions:

- **Substrate vintage decision — 2015-2025 (`286829dce681bec874be0464731013f628d49d0b61005ec15008…`), NOT the 2015-2026 `317429e4…` binding.** Stage 1 (`vendor_legacy_1min`, 20,817,531 rows / 53 partitions) + Stage 2 (`vendor_legacy_1min_roll_adjusted`, 49 partitions) regenerated via `scripts/ingest.py --start 2015-01-01 --end 2025-12-31 --force`. The `--end 2025-12-31` deliberately EXCLUDES the 2026-H1 partitions present in the raw CSVs (the `317429e4` vintage included them). Rationale: vintage-CONSISTENCY across the re-run arms matters more than matching a historical binding; all re-run arms share `286829dc`. H060 re-run reproduced its Phase O.10 v2 result bit-for-bit (end-equity $16,875.37, MPPM +0.0817 [-0.110, +0.267]) confirming the regen is functionally identical for pre-2026 OOS. **Follow-up `P1-MPV2-SUBSTRATE-2026-EXTENSION`** (non-blocking): a v2 verdict may regenerate WITH 2026 to match `317429e4` once all arms can be re-run on that vintage.
- **Canonical per-arm MPV2 reward-stream schema = `mpv2_arm_stream: {dates: [ISO], logret: [per-session-day basket], collapse: <label>}`.** Each orchestrator emits ONE per-session-DAY equal-weight basket log-return stream (collapsed across the symbols active that day, arithmetic-space: basket_arith = mean over symbols of expm1(daily_logret), then log1p). This is distinct from the legacy `per_session_logret_aggregate` (which is SYMBOL-CONCATENATED — ES sessions, then NQ, … — and is NOT calendar-joinable). The MPV2 extractor reads `mpv2_arm_stream` (preferred) or falls back to H060's `per_session_dates`+`per_session_logret_aggregate` (already a per-day basket).
- **H050 deferred to v2 (dateless).** H050's committed `oos_returns.parquet` is `(1164, 2)` with columns `gated_return`/`unconditional_return` and **no date column** → not calendar-joinable; a full dated re-run is ~7-8 hr (not justified for v1). H050 (the known signal-HARMING HMM-gated arm per its KPI v1) re-enters at v2 via a dated re-run; **follow-up `P1-MPV2-H050-DATED-RERUN`** (BLOCKING-before-4-arm-verdict). v1 verdict scope = 3 arms {H055, H060, H062}.
- **`P1-MPV1-CALENDAR-ALIGNMENT` CLOSED (code-landed).** `build_calendar_aligned_reward_matrix` + `extract_arm_dated_stream` + `_normalize_date_key` in [scripts/run_mpv2_closed_loop.py](../../scripts/run_mpv2_closed_loop.py): date-keyed inner-join on the SORTED INTERSECTION of all arms' dates (replaces positional `t mod n` truncation), duplicate-date defended (a per-day basket has unique dates), empty-intersection raised. 26/26 MPV2 tests green; ruff-clean.
- **`P1-H060-PER-SESSION-LOGRET-EMIT` CLOSED** — H060 orchestrator emits `per_session_logret_aggregate` (basket) + `per_session_dates` + a 1:1 length-invariant assertion. Re-run `c31a8a60…`: 1260 dated daily-basket sessions (2020-12-23 → 2025-11-06).
- **`P1-MPV2-PER-SESSION-DAY-BASKET-COLLAPSE` (new) CLOSED for H062** — H062 orchestrator collapses its per-(symbol,date) daily returns to a per-session-day basket + emits `mpv2_arm_stream`. Smoke re-run `5554a2f8…`: 1742 dated basket sessions (2020-03-18 → 2025-11-26). **Still OPEN for H055** (per-config selection + collapse; the H055 sweep emits per-cell arrays that are stripped from the sidecar).
- **First real 2-arm calendar-aligned result {H060, H062}** (smoke-grade arms): 1252 common sessions (2020-12-23 → 2025-11-06); **ENB 1.999/2** (mean off-diagonal corr 0.035 — near-perfectly de-correlated, the ergodicity pooling precondition is met); closed-loop MPPM(ρ=1) time-average **0.0279 vs 1/N 0.0665** → vs-1/N sized mean_diff **−0.000141** (one-sided-lower −0.000639, excludes-zero-positive **False**) → disposition **`null-vs-1N-BH-not-evaluated`**. **The closed-loop bandit does NOT beat naive 1/N on these two de-correlated arms** — exactly the ergodicity-thesis prediction (de-correlated arms favor POOLING over SWITCHING; ADR-0029 §D-3). This validates the entire calendar-aligned machinery on real data and gives the first honest directional read.

**Remaining to the 3-arm v1 verdict**: (1) H055 per-config per-session-day-basket emission patch + re-run (3rd arm; `P1-MPV2-PER-SESSION-DAY-BASKET-COLLAPSE` for H055 — config choice = C9 BOCD-step-up, the project's operationally-correct production variant per Phase O.7); (2) dated equal-weight buy-and-hold of the arm-universe from the substrate, aligned to the common dates (`P1-MPV2-BH-SERIES-WIRE`, closes the conjunctive arm); (3) 3-arm MPV2 + simultaneous-portfolio run + audit-remediate-loop + MPV2 KPI emission + ReproLog wire. New follow-ups: `P1-MPV2-SUBSTRATE-2026-EXTENSION`, `P1-MPV2-H050-DATED-RERUN`.

## P-5 real-data execution drive — milestone 2 (2026-06-02 PM): the 3-arm v1 VERDICT (switching NULL; simultaneous pooling beats B&H)

All 3 dated arms landed on the `286829dc` 2015-2025 vintage: H055 (C9 config; 437 dated sessions; smoke), H060 (1260; daily basket), H062 (1742; intraday→day basket, smoke). The calendar-join (`build_calendar_aligned_reward_matrix`) + B&H wiring (`build_passive_long_from_substrate`) closed `P1-MPV1-CALENDAR-ALIGNMENT` + `P1-MPV2-BH-SERIES-WIRE`. **3-arm common window = 364 sessions, 2024-01-02 → 2025-05-30 (bounded by H055's smoke OOS).**

**Cross-arm independence (P-4)**: **ENB 2.989 / 3** (Meucci 2009 effective-number-of-bets; mean |off-diagonal corr| 0.052, max 0.096). The 3 arms are near-perfectly de-correlated — the ergodicity pooling precondition (ADR-0029 §D-3.4) is **met emphatically**.

**MPPM(ρ=1) time-average growth (the ADR-0029 §D-3.1 headline) over the 364-session common window**:

| Allocation | MPPM(ρ=1) | vs-1/N excl-0+ | vs-B&H excl-0+ | conjunctive |
|---|---:|:--:|:--:|:--:|
| Joint-Kelly simultaneous portfolio (fractions H055 0.28 / H060 0.32 / H062 0.39; converged; no ruin) | **+0.229** | — | — | — |
| 1/N equal-weight pool | +0.225 | — | — | — |
| Buy-and-hold (EW {ES,NQ,MGC,SIL} daily) | +0.171 | — | — | — |
| **Switching closed-loop (bandit → early-warning → CPPI)** | **−0.020** | **False** | **False** | **False** |

**MPV2 (switching) disposition: `null`** — the regime-switching closed loop beats NEITHER 1/N NOR buy-and-hold (vs-1/N mean_diff −0.000675 one-sided-lower −0.001477; vs-B&H mean_diff −0.000147 one-sided-lower −0.000976; both exclude-zero-positive False). The switching bandit's MPPM (−0.020) is dramatically WORSE than naive 1/N (+0.225).

**The load-bearing finding (confirms ADR-0029 + the ergodicity reframing)**: on de-correlated arms, **SIMULTANEOUS POOLING dominates SWITCHING**, and pooling **beats buy-and-hold**. Joint-Kelly (+0.229) and 1/N (+0.225) both beat passive (+0.171) and crush the switching bandit (−0.020). Joint-Kelly ≈ 1/N (near-equal fractions) is exactly DeMiguel-Garlappi-Uppal 2009 under estimation noise. **The "switch strategies when the climate changes" framing (MPV1/MPV2 switching) is the WRONG mechanism for de-correlated arms; "hold all N concurrently, Kelly-weighted" (the ADR-0020 portfolio engine) is the right one.** This is the falsifiable result the MPV2 design was built to produce — a NULL for switching that POINTS to the simultaneous portfolio as the durable-upside route.

**v1 scope caveats** (each tracked): smoke-grade arms (H055 + H062 in `--smoke`; full runs `P1-MPV2-FULL-GRID-ARMS`); 2024-2025 common window only (H055-bounded; a longer window needs H055's full OOS — `P1-MPV2-H055-FULL-OOS-WINDOW`); H050 deferred (dateless; `P1-MPV2-H050-DATED-RERUN`); 286829dc 2015-2025 vintage (2026 excluded; `P1-MPV2-SUBSTRATE-2026-EXTENSION`). **Formal finalization remaining**: audit-remediate-loop on the real-data run (calendar-join + B&H + collapse patches — `P1-MPV2-REAL-RUN-AUDIT`); MPV2 KPI report card emission (`P1-MPV2-KPI-EMISSION`); ReproLog wire (`P1-MPV2-REPROLOG-WIRE`); `P1-MPV2-JOINT-BOOTSTRAP-CONJUNCTIVE` (paired-bootstrap CI on the joint-Kelly-vs-B&H differential, not just point MPPM). The point-estimate verdict is robust + internally consistent; the CI on the pooling-vs-B&H margin is the one remaining inferential gap before a promotable claim.

## P-5 milestone 3 (2026-06-02 PM): CAUSAL correction + full CI verdict — NO allocator beats B&H; `P1-MPV2-JOINT-BOOTSTRAP-CONJUNCTIVE` CLOSED

**Milestone-2's joint-Kelly +0.229 was IN-SAMPLE (look-ahead in the weights) — it does NOT survive a causal fit.** `evaluate_simultaneous_pooling` (new in [scripts/run_mpv2_closed_loop.py](../../scripts/run_mpv2_closed_loop.py)) fits the joint-Kelly fractions on the calibration head, FREEZES them, applies to the eval tail (mirrors the bandit's calib/eval split; no look-ahead), and CIs pooled-vs-1/N, pooled-vs-B&H, AND 1/N-vs-B&H via paired stationary bootstrap. Closes `P1-MPV2-JOINT-BOOTSTRAP-CONJUNCTIVE`. The full causal, CI-backed verdict over both windows:

| Allocator | 2-arm {H060,H062} 2020-2025 MPPM (1252 sess) | 3-arm {H055,H060,H062} 2024-2025 MPPM (364 sess) | beats B&H (one-sided CI excl 0+) |
|---|---:|---:|:--:|
| **1/N equal-weight pool** | **0.261** | **0.320** | **NO** (lower bound −0.0011 / −0.0007) |
| Buy-and-hold (EW {ES,NQ,MGC,SIL} daily) | 0.191 | 0.127 | — |
| OOS joint-Kelly (causal, fit-on-calib) | 0.045 | 0.150 | NO |
| Switching closed-loop (bandit) | −0.020 | −0.020 | NO |

**Load-bearing conclusions (the final v1 finding)**:
1. **NO allocator statistically beats buy-and-hold OOS** on either window — not switching, not causal joint-Kelly, not even the winning 1/N. Every margin's paired-bootstrap one-sided lower bound covers zero. Per Lo 2004 AMH this is the null confirmed, and it directly substantiates the operator's external-validity concern: the arm library's edge over passive is marginal + climate-conditional.
2. **1/N dominates the "smarter" allocators** (DeMiguel-Garlappi-Uppal 2009 in full force): naive equal-weight (0.261/0.320) beats causal joint-Kelly (0.045/0.150) AND switching (−0.020). On noisy de-correlated arms, both Kelly-optimization and regime-switching add estimation error, not value.
3. **In-sample joint-Kelly overfits hard** (+0.229 in-sample → 0.045 causal on the 2-arm window; the fit zeros out H062 + de-levers to 0.257 gross). This is the canonical look-ahead-in-the-weights trap; recorded so a successor does not re-report an in-sample allocator number as a result.

**Implication for the NinjaScript-candidate goal**: the meta-portfolio / allocator is NOT a worthy NinjaScript candidate (it does not beat B&H in growth). The narrowing must move to **per-arm standalone risk-adjusted profiles** (Calmar / max-DD / L-skewness / down-market behavior), where a candidate may be worthy as a lower-DD or positive-skew diversifier even at B&H-comparable growth — NOT on MPPM-beats-B&H, which the whole library fails. New follow-up `P1-NINJASCRIPT-CANDIDATE-STANDALONE-RISK-PROFILE`: rank {H055-C9, H060, H062} (+ H050 once dated) by survival-constrained standalone KPI vs each arm's own passive benchmark + C#-implementability (H060 daily TSMOM is pure-C#; H062 intraday is pure-C#; H055 wick-MR is pure-C#; H050 needs the HMM bridge).

## P-5 milestone 4 (2026-06-02 PM): standalone per-arm narrowing → H055-C9 is the leading NinjaScript candidate (gated on cost-realism)

Closes `P1-NINJASCRIPT-CANDIDATE-STANDALONE-RISK-PROFILE`. Per-arm standalone survival-constrained profile (each vs its OWN passive; C9 = the production BOCD-step-up config):

| Candidate | OOS ROI | maxDD | MPPM_ann | Calmar | PF | R-mean | τ₃ | C# | worthy? |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| **H055-C9 ES** (wick-MR) | +21.9% | 24.1% | +0.325 | **+1.35** | 1.07 | +0.009 | +0.10 | pure | **LEADING** |
| H055-C3 MGC (super-Kelly) | +43.0% | 26.6% | +0.246 | +0.93 | — | — | +0.08 | pure | strong (super-Kelly risk) |
| H055-C9 MGC | +27.3% | 22.3% | +0.151 | +0.68 | 1.03 | +0.006 | +0.07 | pure | modest |
| H055-C9 SIL | +7.1% | 32.0% | +0.045 | +0.14 | 1.01 | +0.005 | +0.08 | pure | marginal |
| H055-C9 NQ | −18.6% | 28.8% | −0.518 | −1.80 | 0.87 | −0.049 | +0.14 | pure | NO (negative) |
| H060 daily-TSMOM basket | +68.8% | 29.5% | +0.082 | — | — | — | — | pure | NO (dominated by passive +75.7%/23.7%) |
| H062 intraday-Donchian basket | +209.8% | 95.6% | +0.085 | — | — | — | — | pure | NO (uninvestable DD; fixed-cell smoke-fragile per Phase O.7.5) |
| Meta-allocator (switch/pool) | — | — | ≤+0.32 | — | — | — | — | bridge | NO (does not beat B&H — milestone 3) |

**Candidate verdict**: **H055-C9 ES (secondarily MGC)** — the wick-rejection mean-reversion scalp — is the leading worthy NinjaScript candidate. It is the only arm with a genuinely good risk-adjusted standalone profile (Calmar +1.35, MPPM_ann +0.325, positive skew τ₃ +0.10, pure-C#) AND is not dominated by passive (H060) or by catastrophic drawdown (H062). **The binding gate**: its per-trade edge is thin (PF 1.07, R-mean +0.009 ≪ the Tharp-1998 +0.5 worthy threshold), so it survives ONLY if NT8-realistic costs are small relative to the per-trade margin. v1 is zero-cost; the decisive test is the cost-realistic re-run (`P1-H055-COST-EMPIRICAL-CALIBRATION` / `--cost-model conservative_prior`). At PF 1.07 the cost gate is the real risk — a few ticks per round trip could flip the edge negative. **No NinjaScript commit until the cost-realistic C9-ES profile is confirmed positive.** That re-run is the next execution step.

## P-5 milestone 5 (2026-06-02 PM): cost gate REJECTS H055-C9 — no cost-surviving candidate in the current library; forward = H068 cost-light lineage

The cost-realistic re-run (`--smoke --cost-model conservative_prior`; sidecar `v2_sweep_20260602T205808Z`) is decisive: under NT8-realistic costs **every H055-C9 cell flips catastrophically negative**:

| H055-C9 cell | zero-cost ROI / PF / R-mean | with-cost ROI / PF / R-mean |
|---|---|---|
| ES (the candidate) | +21.9% / 1.07 / +0.009 | **−50.7% / 0.43 / −0.332** |
| MGC | +27.3% / 1.03 / +0.006 | **−94.6% / 0.51 / −0.219** |
| SIL | +7.1% / 1.01 / +0.005 | **−88.7% / 0.42 / −0.290** |
| NQ | −18.6% / 0.87 / −0.049 | **−39.9% / 0.64 / −0.173** |

The thin zero-cost edge (PF≈1.05, R-mean≈+0.007) is **erased by costs** — PF collapses to 0.4-0.6, R-mean goes deeply negative. This is robust to cost-model choice: a +0.007R average per-trade has no margin for any non-trivial round-trip cost (a wick-MR scalp's per-trade profit ≈ a few ticks ≈ the cost itself). **H055-C9 is REJECTED as a NinjaScript candidate.** Caveat per Phase O.18: the conservative-prior fees are partly placeholder (`P1-METALS-ENERGY-CME-FEE-VERIFY`); a definitive verdict wants empirical slip calibration from paper-trade fills — but PF 1.07→0.43 is too large a move for fee-precision to rescue.

**The complete narrowing conclusion (the honest answer to "narrow to a worthy NinjaScript candidate")**: **there is NO cost-surviving worthy candidate in the current arm library.** The allocator doesn't beat B&H (milestone 3); H060 is dominated by passive; H062 has uninvestable DD; H055-C9 — the best zero-cost risk-adjusted profile — does not survive costs. Per Lo 2004 AMH + ADR-0013 (no-binding-gates, null-is-valuable), this is a legitimate, load-bearing result: the current signal classes (HMM-gated directional, daily-TSMOM, intraday-Donchian, wick-MR) lack a cost-surviving retail-tradeable edge over 2020-2025.

**Forward direction (where a worthy candidate plausibly exists)**: the **H068 cost-light lineage**. Phase O.18 established that the cost-reduction axis must operate at the SLIP layer (sub-1-tick, empirically calibrated), NOT the N-lot layer, and H068 (cost-light Donchian, ES) was the project's FIRST cost-light positive ROI (+23.12% at slip=0.5; A1 ratio 2.278 crossing the ≥2 threshold) — edge present but underpowered (n=108). The pre-registered `H068 v2` (multi-instrument basket; `P1-H068-V2-EXPANDED-SUBSTRATE`, Phase O.20) is the natural worthy-candidate pursuit: cost-light by design, power-lifted via Grinold √breadth. The MPV2 arms were all cost-fragile; H068 is the cost-aware redesign. New follow-up `P1-NINJASCRIPT-CANDIDATE-PURSUE-H068-LINEAGE` (BLOCKING-BEFORE-ANY-NINJASCRIPT-COMMIT): run H068 v2 cost-realistic; if its multi-instrument basket clears B&H + survives costs with a CI, it is the candidate. Until then, **no arm warrants NinjaScript compilation.**

## P-5 milestone 6 (2026-06-15): MPV2 finalization — repro-wire CLOSED, KPI card emitted, ADR-0030 reframe adopted

The Phase-P verdict was formalized + made reproducible under a Round-1 audit-remediate-loop (proper-isolated quant-auditor + reproducibility-verifier; trail [docs/audits/audit_trail_2026-06-15_mpv2-kpi-card-and-real-run.md](../../docs/audits/audit_trail_2026-06-15_mpv2-kpi-card-and-real-run.md)):

- **`P1-MPV2-REPROLOG-WIRE` CLOSED.** A `--real` CLI branch + `_run_real` driver + `RunContext` + sidecar emission landed in [scripts/run_mpv2_closed_loop.py](../../scripts/run_mpv2_closed_loop.py) (plus the missing `sys.path` shim; ruff-clean). `uv run --extra dev python scripts/run_mpv2_closed_loop.py --real` reproduces the verdict deterministically into [artifacts/runs/MPV2/1980ec1eba2d4f4b965c44a965780370/sidecar.json](../../artifacts/runs/MPV2/1980ec1eba2d4f4b965c44a965780370/sidecar.json) (run_id `1980ec1eba2d4f4b965c44a965780370`; scientific_payload_sha256 `d85ae777d754de3c6981703bc919fc16f999efcdfacdebc3a6681485221acffb`; ReproLog `logs/reproducibility/1980ec1eba2d4f4b965c44a965780370.json`; substrate `317429e4` for B&H, arm-stream vintage `286829dc`, common windows vintage-invariant).
- **MPV2 KPI report card v1 emitted** ([research/01_meta_portfolio/MPV2/MPV2_kpi_report_v1.md](../../research/01_meta_portfolio/MPV2/MPV2_kpi_report_v1.md); stage `designed` → `kpi-report-emitted`). NULL disposition recorded per ADR-0013 non-loss.
- **Numeric reconciliation (supersedes, does not delete, the earlier milestones).** The reproducible sidecar is now the single source of record. (i) The milestone-2 3-arm benchmark MPPMs (1/N +0.225, B&H +0.171) were a **superseded earlier drive**; the reproducible-authoritative values are the milestone-3 ones (1/N 0.320 [3-arm] / 0.261 [2-arm]; B&H 0.127 / 0.191). (ii) **The 2-arm switching MPPM is +0.0279, NOT −0.020** — the earlier drive copied the 3-arm −0.020 into the 2-arm row; corrected. The qualitative verdict is **unchanged**: switching < 1/N on both windows (rejects the conjunctive H_1); no allocator beats B&H (all paired-bootstrap lower bounds cover zero); 1/N dominates the optimised joint-Kelly (which zeros out H062).
- **Milestone-1 §"BLOCKING-before-real-verdict" list correction.** The earlier text listed `P1-MPV1-CALENDAR-ALIGNMENT`, `P1-MPV2-BH-SERIES-WIRE`, `P1-MPV2-JOINT-BOOTSTRAP-CONJUNCTIVE` as blocking; all three were already CLOSED (committed + tested) per the CLAUDE.md milestone-1..5 ledger — the only genuinely-missing pieces were the `--real` CLI + ReproLog wrapper, now landed.
- **[ADR-0030](../../docs/decisions/ADR-0030-cost-light-arm-generation-refined-center-of-gravity.md) adopted** — the cost-light arm-generation refinement of the center of gravity (ADR-0029 §D-1 sequencing), grounded in the net-of-cost-survival literature (Novy-Marx-Velikov 2016; Lesmond-Schill-Zhou 2004; Patton-Weller 2020; Gârleanu-Pedersen 2013; Detzel-Novy-Marx-Velikov 2023). Round-1 audit-remediate-loop (literature-check ACCEPT 0 findings; quant-auditor 4 major + 6 minor all remediated; trail [docs/audits/audit_trail_2026-06-15_adr-0030-cost-light-reframe.md](../../docs/audits/audit_trail_2026-06-15_adr-0030-cost-light-reframe.md)).

**Forward execution unchanged**: `P1-NINJASCRIPT-CANDIDATE-PURSUE-H068-LINEAGE` (H068 v2 cost-realistic) is the active pursuit; the substrate is regenerated + verified at `317429e4`.
