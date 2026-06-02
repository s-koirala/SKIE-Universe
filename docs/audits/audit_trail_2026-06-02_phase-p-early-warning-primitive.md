# Audit trail — Phase P P-2 early-warning detector primitive

- **Date**: 2026-06-02
- **Artifacts under audit**: [src/skie_ninja/inference/early_warning.py](../../src/skie_ninja/inference/early_warning.py); [tests/unit/test_early_warning.py](../../tests/unit/test_early_warning.py).
- **Authority**: ADR-0029 §D-2 (Thrust 1) / Phase P buildout P-2; follow-up `P1-EARLY-WARNING-DETECTOR-PRIMITIVE`.
- **Discipline**: audit-remediate-loop, 3-round cap. Round 1 executed with proper-isolated parallel quant-auditor + code-reviewer (Agent tool available this session). A pre-audit inline fix had already surfaced the CSD false-positive (see §0). Round 2 verification deferred to `P1-EARLY-WARNING-THRESHOLD-CALIBRATE` (holdout calibration is the empirical check on the detector behavior).

## §0 — Pre-audit inline finding (CSD advisory default)

The first test run failed `test_stable_regime_does_not_fire`: on a stable iid series (seed 13) the CSD rolling-variance Kendall-τ hit 0.71 and tripped the gate. Root cause: the Kendall-τ of an **overlapping** rolling-window variance series is heavily autocorrelated, so a single iid realization can show a strong apparent trend — a raw fixed-τ cutoff has a high false-positive rate. Per Dakos 2012 the τ is tested against a surrogate/bootstrap null, not a constant. Fix applied before the formal audit: **CSD made advisory-only by default** (`csd_variance_advisory_only=True`); gating defaults to the robust CUSUM + drawdown layers; surrogate-null calibration deferred to new follow-up `P1-EARLY-WARNING-CSD-SURROGATE-NULL`.

## Round 1 — quant-auditor (agentId aed77f0673e798d70) — verdict `proceed-with-remediation`

| # | Severity | Finding | Remediation |
|---|---|---|---|
| F-1 | **critical** | Near-zero-σ CUSUM blowup: a numerically-flat path (e.g. `np.full(n, 0.01)` → σ≈1.7e-18 from float rounding) passes the `sigma > 0.0` guard, then `statistic[-1]/sigma` divides rounding residuals by ~1e-18 → standardized 49 > h=5 → **false de-risk fire on flat PnL** (the exact benign condition of an already-paused strategy). Missed by the n=50 monotone test (fires at n≥61). | **Applied.** Relative σ floor `_SIGMA_REL_FLOOR = sqrt(eps)`; skip CUSUM when `sigma <= _SIGMA_REL_FLOOR * max(\|mu_ref\|, 1.0)`. Plus the firing decision now uses `cu.statistic[-1] > cu.h` directly (no division) per F-4. Regression test `test_flat_pnl_does_not_false_fire_cusum` (n=100). |
| F-2 | **critical** | Self-cancelling CUSUM reference: `deviations = x - ref.mean()` used the **trailing** window, so on a decayed path the trailing mean IS the post-decay mean → post-decay deviations ≈ 0 → the lower-CUSUM cannot accumulate the shift → **the CUSUM layer never fires on genuine decay** (the headline regime-shift test passed only via the drawdown layer). Contradicted the docstring's "in-regime reference mean". | **Applied + extended.** First fix: demean by the **leading** baseline. That surfaced a deeper issue (see §R1-followon): a finite leading window is a noisy in-regime-mean estimate that itself false-positives. Final design: an optional **frozen in-regime reference** (`reference_mean`/`reference_sigma`, established at deployment / last reallocation) anchors the CUSUM; the leading-window estimate is the documented uncalibrated fallback (tripwire mode). Regression test `test_cusum_fires_on_sustained_decay` (frozen-baseline decay) + `test_frozen_reference_anchors_cusum`. |
| F-3 | minor | `armed` reports True (n≥2) while CSD (n≥window+1) + CUSUM (reference_window) layers are dormant; consumer can't distinguish "all layers live" from "drawdown only". | Documented; per-layer arming deferred (non-blocking; the `*_fired` booleans already disclose which layers evaluated). |
| F-4 | minor | Redundant σ round-trip (`statistic[-1]/sigma > h_sigma`) is the F-1 amplifier. | **Applied.** `cusum_fired = cu.statistic[-1] > cu.h` (no division); `cusum_standardized` kept for reporting under the σ-floor guard. |

## Round 1 — code-reviewer (agentId ab5b461c700d35308) — 2 major + minors

| # | Severity | Finding | Remediation |
|---|---|---|---|
| C-1 | major | "mirrors `BOCDState`" claim inaccurate — `bocd_update` is immutable (returns fresh state); `early_warning_update` mutates in place. | **Applied.** Module + state docstrings reworded to "follows the bocd init/update/read INTERFACE SHAPE; mutation semantics differ (BOCD rebuilds; this mutates in place)". |
| C-2 | major | CSD arm-gate `n >= window + 1` implicitly encodes the ≥2-window τ minimum, coupling two modules' arithmetic without a note. | **Applied.** `# justify:` comment pinning `+1` to the ≥2-rolling-window Kendall-τ minimum. |
| C-3 | minor | `csd_advisory_only` vs `ar1_advisory_only` naming asymmetry invites the reading that the former covers AR(1) too. | **Applied.** Renamed `csd_advisory_only` → `csd_variance_advisory_only`. |
| C-4 | minor | `fired_layers` could be non-empty while `fired=False` at n==1 (drawdown needs only n≥1, armed needs n≥2). | **Applied.** `fired = armed and len(layers) > 0`; `fired_layers = () if not armed`. |
| C-5 | minor | Vacuous conditional assertion in `test_ar1_gates_when_advisory_disabled` (passes with 0 assertions if τ<0.3). | **Applied.** Made the implication two-sided (asserts in both branches). |
| C-6 | minor | Parity test checked 6 of 13 signal fields. | **Applied.** Full frozen-dataclass equality `streamed == batch`. |
| C-7 | minor | No composite `cusum_fired` test; no explicit-config `init` test. | **Applied.** Added `test_cusum_fires_on_sustained_decay` + `TestInit` (explicit + default config). |

## §R1-followon — the reference-estimation-noise finding (the substantive result)

The F-2 leading-baseline fix surfaced a deeper, genuinely important result: on a finite iid stable series (seed 13) the leading-60-window mean (0.00426) is an unlucky-high estimate of the true mean (later sessions 0.00307), and the one-sided CUSUM accumulates that **reference-estimation bias** to a false fire (standardized 5.39 > h=5.0). Neither trailing (F-2 self-cancel) nor a noisy leading window is a correct in-regime reference. Resolution: the closed-loop-correct reference is a **frozen baseline established at deployment / last reallocation** (estimation-noise-free), implemented as the optional `reference_mean`/`reference_sigma`. The leading-window estimate remains as an explicitly-documented uncalibrated fallback whose false positives are **cost-bounded by design** — the precursor layer feeds only a PARTIAL de-risk (`derisk_multiplier` = 0.5), reversed if BOCD never confirms (test `test_leading_window_fallback_is_tripwire`).

**Net empirical lesson (feeds the calibration follow-up):** both CSD and CUSUM carry non-trivial false-positive rates on stable series under uncalibrated default thresholds. This is inherent to the methods and is exactly why ADR-0029 §D-2 frames the layer as a tripwire feeding partial de-risk (not exit) and mandates pre-OOS-holdout threshold calibration. The default h=5σ is a canonical-SPC placeholder for a KNOWN reference; with an estimated reference it must be raised, and with a frozen reference the false-positive rate drops — all quantified by `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`.

## Verdict

Round 1: **accept-with-residuals.** Both critical findings (F-1, F-2) remediated; both majors + all minors remediated. 39/39 unit tests green; SRC ruff-clean + formatted (test-file PLR2004 matches existing committed convention). Standalone detectors (CUSUM recursion/sign, CSD variance + lag-1 AR + Kendall-τ, drawdown/TuW) verified method-faithful by the quant-auditor.

**Residuals (Phase P calibration concerns, not artifact defects):** threshold calibration (`P1-EARLY-WARNING-THRESHOLD-CALIBRATE`, BLOCKING-BEFORE-CLOSED-LOOP-RUN), CSD surrogate-null (`P1-EARLY-WARNING-CSD-SURROGATE-NULL`), incremental-update perf (`P1-EARLY-WARNING-INCREMENTAL-UPDATE`, non-blocking). Round 2 verification folds into the holdout calibration run.
