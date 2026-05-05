# Audit Trail — H052a Phase 2 build-defect remediation chain

**Date**: 2026-05-05
**Hypothesis**: H052a — HMM regime-gated first-hour ORB on CME ES/NQ futures
**Phase**: 2 (production walk-forward execution)
**Trail scope**: Sequential build-defect discovery + remediation chain across 5 failed launches → 6th launch clean exit 0
**Final run_id**: `184eccd67bf24d71990265d39c28daf0`
**Final commit**: `0aa92585c80e85b371af918691ebcbfb3b9980b5`
**Verdict**: R2 ACCEPT — 5/5 build defects remediated; 6th launch clean exit 0 with both symbols ok.

## Context

Phase 1 (commit `6e87a9d`) landed the H052a dedicated orchestrator + features + cost model under R2 ACCEPT (5 critical + 9 major findings remediated; [audit_trail_2026-05-04_h052a-phase-1-infrastructure.md](audit_trail_2026-05-04_h052a-phase-1-infrastructure.md)). Phase 2 was the first attempt to execute the orchestrator end-to-end on the post-Cell-I substrate. The 5 build defects below were discovered in sequence — each launch surfaced one defect, which was fixed under audit-remediate-loop discipline, then the next launch surfaced the next defect.

This is the canonical pattern of Phase 2 production execution per ADR-0011: the orchestrator was correctly designed at Phase 1 R2 ACCEPT, but the integration surface between newly-introduced components (Polars/pandas precision boundaries; H052a-specific labeller; H052a-specific feature module; HMM API surface) had latent defects only exercisable on real substrate at production scale. Each defect was a discrete narrow-fix; none required structural redesign of the Phase 1 architecture.

## Round-1 — sequential build-defect discovery (5 launches)

### F-Q-1 — O(N²) labeller (severity: critical, perf)

**Launch 1**: `OMP_NUM_THREADS=1 ... uv run python scripts/run_h052a_walk_forward.py --hypothesis H052a --config config/hypotheses/H052a.yaml` (no `--smoke`, no `--dry-run`).

**Symptom**: orchestrator made forward progress through feature assembly, then stalled at the fold-fit phase for ES with no further PROGRESS markers. Killed at +27 min after no checkpoint advance.

**Diagnosis**: `OpeningRangeBreakoutLabeller.label_panel` iterated unique sessions and computed `(session_dates_et == session_date).to_numpy()` per session. With 2710 unique sessions on the ES panel and ~360 RTH bars/session = ~975,600 rows, the per-iteration boolean-mask allocation × 2710 iterations × ~975,600 row comparisons = 2.6e9 element-wise comparisons in Python-level pandas-vector loop — wall-clock O(N²) at ES scale.

**Fix** (commit `583a4ee`): replaced the per-session boolean-mask iteration with `pd.factorize` + change-point boundaries:

```python
codes, unique_sessions_arr = pd.factorize(session_dates_et.dt.tz_convert("UTC"), sort=True)
change_points = np.concatenate([[0], np.flatnonzero(np.diff(codes) != 0) + 1, [n_total]])
for k in range(len(change_points) - 1):
    start = int(change_points[k]); end = int(change_points[k + 1])
    session_date = unique_sessions_arr[codes[start]]
    sess_idx = np.arange(start, end)
    sess_tod = time_of_day_arr[start:end]
    sess_closes = closes[start:end]
    sess_ts_utc = ts_utc_arr[start:end]
```

This is O(N) total — single factorize + single diff + indexed slicing per session.

**Smoke verification**: synthetic 3,900-bar (10-session) panel completes in 0.045s; production ES panel (2710 sessions × ~360 bars = ~975k rows) completes in ~12s.

**Side-effect**: dead `σ_annualised` computation removed from labeller (was dependency-injected through the labeller signature but never consumed downstream).

### F-Q-2 — VIX merge_asof dtype mismatch (severity: critical, build)

**Launch 2**: relaunched after F-Q-1 fix.

**Symptom**: `MergeError: incompatible merge dtype: datetime64[us, UTC] vs datetime64[ms, UTC]` raised by `pd.merge_asof` inside `compute_vix_daily_join`.

**Diagnosis**: `session_date_et` arriving from Polars→pandas natural conversion was μs-precision; the VIX ingest module ([src/skie_ninja/data/ingest/vix_daily.py](../../src/skie_ninja/data/ingest/vix_daily.py)) writes the FRED VIXCLS daily series as ms-precision dates (the FRED CSV native precision when round-tripped through pandas).

**Fix** (commit `27ed41d`): cast both sides to `datetime64[ns, UTC]` inside `compute_vix_daily_join` before invoking `pd.merge_asof`:

```python
sess_df['session_date_et'] = sess_df['session_date_et'].astype('datetime64[ns, UTC]')
vix_df['date'] = vix_df['date'].astype('datetime64[ns, UTC]')
```

ns-precision is canonical pandas internal representation; merge_asof works without further coercion.

### F-Q-3 — feature panel cross-precision SchemaError (severity: critical, build)

**Launch 3**: relaunched after F-Q-2 fix.

**Symptom**: `polars.SchemaError: column "session_date_et" datetime precision mismatch (us vs ns)` raised inside `compute_h052a_features` when joining the 6 feature panels.

**Diagnosis**: 5 of the 6 H052a feature compute functions (`compute_first_hour_sign`, `compute_gap_size`, `compute_dow_onehot`, `compute_eth_pre_rth`, `compute_realized_vol_per_session`) produced `session_date_et` at μs-precision (the natural Polars `pl.Datetime` default). After F-Q-2 fix, `compute_vix_daily_join` produced ns-precision. Polars `.join` requires precision uniformity.

**Fix** (commit `3f2330a`): added a single normalisation step at the top of `compute_h052a_features` that casts every contributing panel's `session_date_et` to `pl.Datetime("ns", "UTC")` before the cascade of joins:

```python
_norm = pl.col("session_date_et").cast(pl.Datetime("ns", "UTC"))
rv = rv.with_columns(_norm)
fhs = fhs.with_columns(_norm)
gap = gap.with_columns(_norm)
dow = dow.with_columns(_norm)
eth = eth.with_columns(_norm)
# vix already ns from F-Q-2 fix
```

ns precision is the canonical project convention; codified for any future H052b/H052c/etc. feature modules under the (informational) follow-up `P1-FEATURE-PANEL-PRECISION-CONTRACT`.

### F-Q-4 — orchestrator labels↔features SchemaError (severity: critical, build)

**Launch 4**: relaunched after F-Q-3 fix.

**Symptom**: same `polars.SchemaError` (μs vs ns) but at a different join site — the orchestrator's labels↔features join at `scripts/run_h052a_walk_forward.py` (the join that combines `OpeningRangeBreakoutLabeller` output with `compute_h052a_features` output).

**Diagnosis**: the labeller (post-F-Q-1 fix) produced `session_date_et` at μs (default `pd.factorize` output precision), while `compute_h052a_features` (post-F-Q-3 fix) produced ns. The orchestrator's downstream join hit the same precision-mismatch class as F-Q-3 but at the cross-module integration point.

**Fix** (commit `20e6450`): normalise both sides to `pl.Datetime("ns", "UTC")` in the orchestrator immediately before the labels↔features join. Mirrors the F-Q-3 fix at the cross-module boundary instead of within `compute_h052a_features`.

### F-Q-5 — HMMParams.n_states method-vs-attribute TypeError (severity: critical, build)

**Launch 5**: relaunched after F-Q-4 fix.

**Symptom**: `TypeError: int() argument must be a string, a bytes-like object or a real number, not 'method'` at the HMM-selection metadata logging step.

**Diagnosis**: orchestrator code attempted `int(hmm.params_.n_states)` — but `n_states` on `HMMParams` is a method, not an attribute, per [src/skie_ninja/models/regime/hmm.py](../../src/skie_ninja/models/regime/hmm.py). Additionally, `SelectionResult` (BIC selection output) exposes `best_n_states` and `best_covariance_type` as direct attributes, NOT a nested `best_bic` object.

**Fix** (commit `0aa9258`): two narrow corrections inside the orchestrator's HMM-selection metadata logging:
1. `hmm.params_.n_states()` (method call, not attribute access)
2. Use `selection.best_n_states` and `selection.best_covariance_type` directly (not `selection.best_bic.n_states`)

### Launch 6 — clean exit

**Launch 6**: relaunched after F-Q-5 fix at 11:31:04 CT.

**Result**: clean exit 0 at 11:44:43 CT (~14 min total wall-clock). Both symbols ok:
- ES: train=736 sessions; test=371; best cfg `(pt=1.00, sl=1.50, vol_lookback=120m)`; inner-CV mean SR = -0.6672; HMM `(full, 3-state)`, nonstress_state=0
- NQ: train=736; test=369; best cfg `(pt=0.50, sl=1.00, vol_lookback=60m)`; inner-CV mean SR = -1.2942; HMM `(full, 3-state)`, nonstress_state=0
- 0 NaN drops on any feature panel; 1 NaN entry_price drop per symbol (single missing 10:30 ET bar each)
- Artifacts on disk: ES_metrics_summary.json (12,175 bytes), NQ_metrics_summary.json (12,169 bytes), sidecar.json (27,369 bytes), scientific_payload_sha256.txt
- ReproLog: [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../../logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json) (all 13 fields populated; canonical git_head `0aa92585`)
- scientific_payload SHA: `cca86b2746e5cb1bc62984352d21d2a55c182ed779fe3f741da52bfa52e60442`

## Round-2 — verification

**Approach**: re-read the 5 fix commits + the 6th-launch ReproLog + the 6th-launch metrics summaries to verify each defect was structurally closed (not merely symptom-suppressed).

| Defect | Fix commit | Closure verified by | Verdict |
|---|---|---|---|
| F-Q-1 (O(N²) labeller) | `583a4ee` | smoke test on synthetic 3,900-bar panel completes in 0.045s; production ES panel completes in ~12s; `pd.factorize` + change-points is structurally O(N) | ✓ closed |
| F-Q-2 (VIX dtype) | `27ed41d` | both sides cast to ns-precision before merge_asof; 6th launch passed VIX-join phase without error | ✓ closed |
| F-Q-3 (feature panel precision) | `3f2330a` | all 6 feature panels normalized to ns at top of `compute_h052a_features`; 6th launch passed feature-assembly phase without error | ✓ closed |
| F-Q-4 (orchestrator labels↔features precision) | `20e6450` | both sides normalized to ns at the orchestrator join site; 6th launch passed labels-features-join phase without error | ✓ closed |
| F-Q-5 (HMMParams API) | `0aa9258` | method-call + correct SelectionResult attributes; 6th launch passed HMM-selection metadata phase; `selected_n_states=3` + `selected_covariance_type=full` correctly persisted to sidecar on both symbols | ✓ closed |

**Round-2 verdict**: ACCEPT. All 5 build defects structurally closed; 6th launch produced a complete, sidecar-correspondent, ReproLog-complete production walk-forward result with both symbols ok.

## Round-3 — KPI report card v1 emission

KPI report card v1 emitted at [research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md). Stage transition `exploration-in-progress` → `kpi-report-emitted` recorded at [research/01_hypothesis_register/H052a/stage.md](../../research/01_hypothesis_register/H052a/stage.md). Failure log entries 1-6 created at [research/01_hypothesis_register/H052a/failure_log.md](../../research/01_hypothesis_register/H052a/failure_log.md).

KPI summary:
- **Primary inference (T_H052a = SR_gated − SR_uncond)**: ES T_H052a = -0.0184 [-0.0676, +0.0260]; NQ T_H052a = -0.0342 [-0.1232, +0.0033]. **LW2008 differential CI covers zero on both symbols** — non-significant null. (Cf. H050 where CI excluded zero on the negative side on both.)
- **Annualised Sharpe**: ES gated -0.119 / uncond +0.173; NQ gated +0.313 / uncond +0.855.
- **Realized OOS ($10k start)**: ES gated $9,906 / uncond $10,161; NQ gated $10,339 / uncond **$11,061** (+10.61%).
- **Forward 252-session projection**: NQ unconditional median $10,729; P(loss)=18.56% (lowest); P(double)=0%.
- **Methodological-correctness annotations**: all green or n/a (`leakage-canary-pass`, `bss-n/a`, `reliability-n/a`, `repro-log-complete`, `dsr-n/a (M=1)`, `cost-conditional`, `post-run-audit-pass`).

Per design.md §1 critical interpretive note, a null was the expected outcome — the gated arms are pre-supposed to be ≈null and the test is whether HMM-gating rescues the signal. The non-significant null is consistent with the a-priori expectation. NQ unconditional ORB is the strongest standalone cell (consistent with primary-literature unconditional ORB-on-futures per Holmberg-Lönnbark-Lundström 2013 + Tsai 2019; design.md §15.1 Erratum-2).

## Cross-references

- KPI report card: [H052a_kpi_report_v1.md](../../research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md)
- Stage tracker: [stage.md](../../research/01_hypothesis_register/H052a/stage.md)
- Failure log: [failure_log.md](../../research/01_hypothesis_register/H052a/failure_log.md)
- Pre-registered design: [design.md](../../research/01_hypothesis_register/H052a/design.md)
- §15 errata addendum: [design.md §15.1](../../research/01_hypothesis_register/H052a/design.md#151-citation-errata-phase-0-orb-lit-check-2026-05-04-findings-l-1-through-l-4)
- Phase 0 ORB lit-check: [audit_trail_2026-05-04_h052a-orb-lit-check.md](audit_trail_2026-05-04_h052a-orb-lit-check.md)
- Phase 1 dedicated orchestrator: [audit_trail_2026-05-04_h052a-phase-1-infrastructure.md](audit_trail_2026-05-04_h052a-phase-1-infrastructure.md)
- Sidecar: [artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/sidecar.json](../../artifacts/runs/H052a/184eccd67bf24d71990265d39c28daf0/sidecar.json)
- ReproLog: [logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json](../../logs/reproducibility/184eccd67bf24d71990265d39c28daf0.json)
- Orchestrator: [scripts/run_h052a_walk_forward.py](../../scripts/run_h052a_walk_forward.py)

## Follow-ups (informational; non-blocking)

- `P1-FEATURE-PANEL-PRECISION-CONTRACT` — codify project-wide ns-precision convention for cross-module datetime joins (currently informal); add a precision-uniformity assertion to [src/skie_ninja/utils/](../../src/skie_ninja/utils/).
- `P1-LABELLER-PERF-MICROBENCH` — register the `pd.factorize` + change-points pattern as the canonical labeller iteration idiom for any future per-session label module; add a microbench at [scripts/bench/](../../scripts/bench/) regressing the O(N²) regression class.
- `P1-RUNCONTEXT-GIT-HEAD` — pre-existing follow-up; sidecar's `git_head: "unknown"` while ReproLog's `git_head` is canonical; not introduced by this audit-remediate-loop.
- `P1-H052A-COST-CALIBRATION-EMPIRICAL` — pre-existing per design.md §7; replace 1-tick slippage prior with regime-wise empirical fit from paper-trade logs.
- `P1-H052A-NINJASCRIPT-IMPL` — per ADR-0013 §5; mandatory for nominal flow but operator-discretionary per user's 2026-05-04 standing directive.
