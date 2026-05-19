# Phase O.13 buildout — Deep per-trade-loop wiring + H062 v3 + H055 v3 KPI re-emission

**Status:** planning (this document); execution pending operator-discretionary launch.
**Date:** 2026-05-18
**Predecessors:** [Phase O.11](../../CLAUDE.md) (ADR-0025 + 5 primitives + shallow CLI wiring; commit [b749e96](https://github.com/s-koirala/SKIE-Universe/commit/b749e96)); [Phase O.12](../../CLAUDE.md) (validator parity migration; commit [2ede3f1](https://github.com/s-koirala/SKIE-Universe/commit/2ede3f1)).
**Closes:** `P1-ADR-0025-WIRE-DEEP-INTRA-SIM-H062-H055` + `P1-ADR-0025-V3-KPI-RERUN-H062-H055` per [ADR-0025 §Cascade requirements](../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md).
**Wall-clock estimate:** 1-2 session-passes for the refactor + audit-remediate; 5-7 hr per symbol × 4 symbols × 2 hypotheses = ~40-56 hr for the v3 walk-forward executions; ~2-4 session-passes for v3 KPI report card emission + post-run audit gate.

## Context

Phase O.11 landed four opt-in abandonment-trigger primitives + shallow CLI wiring in the H062 + H055 v2 orchestrators (flags exposed; sidecar `abandonment_triggers` block emitted; primitive intervention NOT engaged in the per-trade loop). The deep wiring per `P1-ADR-0025-WIRE-DEEP-INTRA-SIM-H062-H055` makes the four primitives actually intervene during simulation: per-trade-entry kill-switch gate, per-trade-sizing equity-rebase denominator, per-session BOCD live-pause gate, per-trade-exit cost log-return drag.

Phase O.12 closed the validator drift surface — both modules now share the canonical CME session-clock + K-1/K-6/K-7 thresholds via the [kill_switch_constants.py](../../src/skie_ninja/backtest/kill_switch_constants.py) single source of truth. The Phase O.13 deep wiring therefore has a clean shared-constant foundation.

## Asymmetric refactor scope: H062 additive vs H055 structural-cleanup

The two orchestrators have asymmetric existing state:

- **H062's `_run_per_trade_simulation`** at [scripts/run_h062_walk_forward.py:189-399](../../scripts/run_h062_walk_forward.py) has NO inline abandonment-trigger logic — no breakers, no current-equity rebase, no cost subtraction, no BOCD step-up. The deep wiring is **genuinely additive**: insertion of primitive calls at entry / sizing / close / session-boundary sites. Numerical behavior CHANGES when any flag is on (the four primitives interrupt or modify the existing path).
- **H055 v2's `_run_simulation`** at [scripts/run_h055_v2_sweep.py:468-820](../../scripts/run_h055_v2_sweep.py) already has K-6 + K-7 breakers inlined (`breaker_session_active` / `breaker_week_active`), current-equity rebase inlined (`equity if cfg.use_current_equity_rebase else starting_equity_for_pct_calc`), and BOCD step-up via `C9StateMachine`. The deep wiring is **structural cleanup**: replace inline logic with calls to the shared primitives. Numerical behavior is preserved bit-identically on the existing C1-C5 sweep cells (validated via parity test); operator gains drift-free runtime ↔ validator + the BOCD live-pause hard-halt layer orthogonal to C9's adaptive Kelly halving.

This asymmetry is load-bearing for the v3 KPI re-emission expectations: H062 v3 produces materially different KPI numbers from v2 (max-DD truncation; survival KPIs improved); H055 v3 cells C1-C5 produce numerically-identical KPI numbers + the new annotations + emit additional informational rows.

## Wire-site map — H062 `_run_per_trade_simulation`

| # | Wire site | Line range | Primitive | Operation |
|---|---|---|---|---|
| H062-W1 | Function signature | 189-198 | All 4 | Add optional kwargs: `kill_switch_config: KillSwitchRuntimeConfig \| None = None`, `equity_rebase_policy: EquityRebasePolicy \| None = None`, `bocd_live_state: BOCDLiveState \| None = None`, `cost_model: NT8RealisticCostModel \| None = None`. All default None → behavior bit-identical to v2 path. |
| H062-W2 | Pre-loop state init | 246-269 | kill_switch + equity_rebase + bocd_live | Initialize `ks_state` via `init_runtime_state(universe=(symbol,), starting_equity=10000.0)` if `kill_switch_config` non-None. Initialize `current_equity = 10000.0` if `equity_rebase_policy` non-None. (BOCDLiveState provided by caller pre-initialized.) |
| H062-W3 | Position-size denominator | 371 | equity_rebase | Replace `target_dollar_risk = 10000.0 * risk_budget_pct` with `target_dollar_risk = equity_for_sizing(equity_rebase_policy, current_equity) * risk_budget_pct` if policy non-None; else keep legacy. |
| H062-W4 | Pre-entry guard | 354-356 (before `if not in_position and ev != 0:`) | kill_switch + bocd_live | If `kill_switch_config` non-None: `blocked, reason = check_entry_blocked(ks_state, kill_switch_config, symbol=symbol, position_size=size_capped)`; on block, `ks_state = record_trigger(ks_state, reason)` + skip entry. If `bocd_live_state` non-None and `is_paused(bocd_live_state)`: skip entry. |
| H062-W5 | Update on open | 377-385 (after position state set) | kill_switch | If `kill_switch_config` non-None: `ks_state = update_state_on_open(ks_state, symbol=symbol, side=ev, entry_ts=..., entry_price=entry_price, position_size=size_capped, stop_price=stop_price, r_dollar=r_dollar)`. |
| H062-W6 | Update on close + equity update | 286-313 in `_close_position` | kill_switch + equity_rebase | Compute `signed_dollar` (already done at 291-293). If `kill_switch_config` non-None: `ks_state = update_state_on_close(ks_state, symbol=symbol, realized_pnl_dollar=signed_dollar, exit_ts=...)`. If `equity_rebase_policy` non-None: `current_equity = apply_pnl_to_equity(current_equity, signed_dollar)`. |
| H062-W7 | Cost subtraction | 299 in `_close_position` (replacing the `trade_equity_log_return = np.log(1.0 + r_mult * risk_budget_pct)` line) | cost_model | If `cost_model` non-None: `cost_drag = cost_model.cost_per_session_log_return(symbol=symbol, entry_price=entry_price, n_contracts=position_size)`; `trade_equity_log_return += cost_drag` (drag is negative). |
| H062-W8 | Session boundary | 315 outer loop (when `session_dates[t] != session_dates[t-1]`) | kill_switch + bocd_live | If `kill_switch_config` non-None: `ks_state = advance_session(ks_state, new_session_date=session_dates[t], current_equity=current_equity)`. If ISO-week changed: also `ks_state = advance_week(ks_state, new_week_id=..., current_equity=current_equity)`. If `bocd_live_state` non-None AND a per-session-MPPM observation is available from the just-completed session: `bocd_live_state = bocd_live_update(bocd_live_state, x_t=<sess_arith_ret_or_mppm>, session_idx=..., ts_utc=...)`. |
| H062-W9 | Return-dict summaries | 387-396 | All 4 | Append `kill_switch_runtime_summary` (`summarize_trigger_counts(ks_state)`), `equity_rebase_summary` (`{mode, final_equity, min_equity_during_sim}`), `bocd_live_summary` (`summarize_pause_events(bocd_live_state)`), `cost_model_summary` (`{cost_model_id, calibration_source, total_log_return_drag}`) to return dict. |

The H062 outer caller at [scripts/run_h062_walk_forward.py:main](../../scripts/run_h062_walk_forward.py) constructs the four primitive configs from the existing CLI flags (already wired in Phase O.11) and passes them into `_run_per_trade_simulation` via the new kwargs.

## Wire-site map — H055 v2 `_run_simulation`

Per the structural-cleanup framing, the H055 v2 wire is replace-in-place. The existing inline logic is preserved bit-identically when the new flags are OFF; primitive calls are added on a parallel code path activated when flags are ON.

| # | Existing inline | New primitive call | Operation |
|---|---|---|---|
| H055-W1 | `eq_for_size = equity if cfg.use_current_equity_rebase else starting_equity_for_pct_calc` (line 714) | `eq_for_size = equity_for_sizing(equity_rebase_policy, equity)` when policy non-None | Pin EquityRebasePolicy construction in the outer caller from the existing `cfg.use_current_equity_rebase` boolean + the runtime `--enable-equity-rebase-current` CLI flag (defaults preserve v2 behavior). |
| H055-W2 | Inline K-6 daily-breaker state at lines 698-704 + 783-789 | `check_entry_blocked(ks_state, ks_config, symbol=symbol, position_size=size)` for K-6 | Drop the inline `breaker_session_active` flag when `kill_switch_config` non-None; rely on the primitive's `daily_pnl_by_session_date` accumulator. |
| H055-W3 | Inline K-7 weekly-breaker state at lines 705-712 + 783-789 | `check_entry_blocked` for K-7 | Same pattern as W2 for `breaker_week_active`. |
| H055-W4 | Inline `_close_all_units` updates `per_session_pnl` + `per_week_pnl` (lines 562-565) | `update_state_on_close` keeps the primitive in sync | Cumulative-pnl tracking shifts to the primitive's accumulators (validator-runtime parity per Phase O.12). |
| H055-W5 | C9 `C9StateMachine` BOCD-step-up state machine (lines 533-540 + 768-779) | Orthogonal — preserved verbatim alongside `bocd_live_state` | The C9 step-up halves Kelly on decay; the new `bocd_live` hard-halts entries on decay. Operator may invoke C9 alone, bocd_live alone, or both stacked. Both produce sidecar summaries (independent annotations). |
| H055-W6 | Zero-cost simulation (no per-trade cost subtraction) | `cost_model.cost_per_session_log_return(...)` subtracted from realized per-trade equity log-return when `cost_model` non-None | Cost drag applied at trade-close site inside `_close_all_units`. |
| H055-W7 | Sweep config `use_current_equity_rebase` + `enable_pyramiding` + `enable_bocd` flags (lines 75-105) | Sweep config gains new optional `kill_switch_config_factory()` + `bocd_live_config_factory()` + `cost_model_factory()` fields | Default None for all sweep cells; operator sets via CLI per-sweep. |

## Pre-launch checklist — ADR-0011 compliance

Per [ADR-0011 production walk-forward runbook](../../docs/decisions/ADR-0011-production-walkforward-runbook.md), the v3 walk-forward launches require:

**Tier 1 — Configuration validity (6 gates):**

| Gate | H062 v3 status | H055 v3 status |
|---|---|---|
| 1 — HMM redundancy dedup | N/A (no HMM at H062 v3) | N/A (no HMM at H055 v3) |
| 2 — Hyperparameter-search budget | inherit H062 v2 grid budget; v3 wall-clock estimate ~5-7 hr/symbol | inherit H055 v2 sweep budget; v3 wall-clock estimate ~3-5 hr/symbol |
| 2b — Microbench-readiness | bench artifact for the four primitives lives at [scripts/smoke_phase_o11_primitives.py](../../scripts/smoke_phase_o11_primitives.py) (Phase O.11 closure) | same |
| 3 — Pre-reg envelope coverage | H062 design.md §2 envelope: 2020-01-01 → 2025-12-{03,19,30}; substrate SHA `317429e4...` (Phase O.10 canonical) | H055 design.md §2: 2020-01-01 → 2026-05-15; substrate SHA `317429e4...` |
| 4 — Reproducibility surface complete | inherit from H062 v2 (Phase O.10 ReproLog 13/13 fields) | inherit from H055 v2 |
| 5 — BLAS thread pinning | verified per ADR-0009 (canonical block in `__main__` of both orchestrators) | same |

**Tier 2 — Host-state validity (5 gates):**

| Gate | Status |
|---|---|
| 6 — Pending-restart absent | runtime check via [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) |
| 7 — Active Hours covers runtime | needs AH ≥ ~6-8 hr at launch time |
| 8 — Wake-lock will engage | verified via ADR-0010 wake-lock helper integrated into orchestrator `__main__` |
| 9 — No high-priority scheduled tasks | spec'd per ADR-0011 P1-ADR-0011-GATE-9-SCHTASKS (not yet shipped) |
| 10 — Disk-space precheck | spec'd per ADR-0011 P1-ADR-0011-GATE-10-DISK-PRECHECK (not yet shipped) |

**Tier 3 — Architectural-readiness (4 gates):**

| Gate | Status |
|---|---|
| 11 — Disk-persistent HMM cache | N/A (no HMM at H062 v3 / H055 v3) |
| 12 — Per-cfg checkpoint | inherit H062 v2 cfg-checkpoint at [src/skie_ninja/backtest/cfg_checkpoint.py](../../src/skie_ninja/backtest/cfg_checkpoint.py) |
| 13 — Supervised relaunch loop | canonical launch via [scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh) per ADR-0010 + ADR-0011 |
| 14 — Per-hypothesis runbook | NEW: write H062 v3 runbook + H055 v3 runbook in this commit group (this document is the parent buildout; per-hypothesis runbooks at [research/01_hypothesis_register/H062/production_run_runbook_v3.md](../../research/01_hypothesis_register/H062/production_run_runbook_v3.md) + [research/01_hypothesis_register/H055/production_run_runbook_v3.md](../../research/01_hypothesis_register/H055/production_run_runbook_v3.md)) |

## V3 KPI report card — expected diff vs V2

Per ADR-0014 §3.2 13-table format, the v3 KPI cards carry the same 13 tables. Diffs vs v2:

| Section | V2 (Phase O.10) | V3 expected (Phase O.13) |
|---|---|---|
| Table 1 (P/L realized OOS) | H062 v2: +217.57% / max-DD 93.26% | H062 v3: estimated +50-100% / max-DD 30-50% (kill switches truncate catastrophic drawdown trajectories) |
| Table 1c (L-skewness τ_3) | H062 v2: +0.737 (strongly skew-positive) | H062 v3: structurally unchanged (kill switches don't add trades; τ_3 of remaining trades preserved within ±0.05) |
| Table 2 (max-DD realized + projected) | H062 v2: 93.26% realized; q95 forward DD large | H062 v3: realized truncated; q95 forward DD shrunk proportionally |
| Table 3 + 3d (Sharpe + MPPM) | H062 v2: MPPM +0.095 [−0.343, +0.540] marginal | H062 v3: MPPM point estimate likely improves due to catastrophic-DD truncation; CI still likely covers zero (mean-edge gap is real) |
| Table 3a (terminal-wealth q05) | H062 v2: `tw-q05-below-half` ($2896.63) | H062 v3: q05 estimated $5-8K; annotation likely flips to `tw-q05-above-half` |
| Table 3b (Calmar-differential) | H062 v2: `calmar-diff-marginal` (CI covers zero) | H062 v3: numerator improved (annualized return less negative); denominator improved (max-DD truncated); annotation may flip to `calmar-diff-positive` cell-dependent |
| Table 3c (profit-factor + R-mean) | H062 v2: profit-factor near 1.0; R-mean near zero | H062 v3: R-mean unchanged (per-trade R distribution preserved); profit-factor improves due to fewer losing-cluster sessions |
| Table 4 (annualized Sharpe) | H062 v2: ~-0.0119 ann | H062 v3: estimated +0.05 to +0.15 |
| Table 5 (W/L/Z counts) | H062 v2: 975/2087/3 | H062 v3: fewer trades total (kill switches blocked some entries); ratio similar |
| Table 6 (forward projection P(loss) + P(double)) | H062 v2: P(loss) 46.92%; q05 below half | H062 v3: P(loss) estimated 20-30%; q05 above half |
| Table 7 (Hansen SPA family p) | H062 v2: family-p marginal | H062 v3: structurally unchanged (SPA test on per-cell Sharpes; per-cell Sharpes shift) |
| Table 8 (Other KPIs) | H062 v2: cost-zero-v1, no kill-switch / bocd-live annotations | H062 v3: gains `kill-switch-active (K-3×N, K-4×N, K-6×N, K-7×N)`, `bocd-live-active OR pause (n_pause_events=N)`, `cost-conservative-prior`, `equity-rebase mode=current (min=$X)` rows per the Phase O.11 KPI template extension |
| §9 annotations | H062 v2: 12 existing | H062 v3: 12 + 3 new (kill-switch-active, bocd-live-X, cost-conservative-prior) |

H055 v3 expected diff vs H055 v2 is much smaller — numerics preserved on C1-C5 cells; new annotations added; cost subtraction added (~−0.5% to −1.5% on the active cells); structural cleanup of inline → primitive.

## Sequencing — execution order

```
Step 1 [code]: H062 deep wiring (W1..W9) + audit-remediate-loop Round 1
Step 2 [code]: H055 v2 deep wiring (W1..W7) + audit-remediate-loop Round 1
Step 3 [tests]: parity tests (legacy-flag-OFF behavior bit-identical to v2)
Step 4 [tests]: integration tests (each primitive engages correctly when flagged ON)
Step 5 [tests]: run targeted test suite; aim 90+/90+ pass
Step 6 [commit]: Phase O.13 code commit
Step 7 [docs]: write H062 v3 + H055 v3 production_run_runbook per ADR-0011 §14
Step 8 [launch]: H062 v3 walk-forward via supervised_relaunch_loop.sh (4 symbols; ~5-7 hr each; total ~24 hr)
Step 9 [launch]: H055 v3 sweep via direct invocation (5 cells × 4 symbols; ~3-5 hr per symbol; total ~16 hr)
Step 10 [audit]: post-run audit gate per ADR-0011 §"Post-run audit gate"
Step 11 [emit]: H062 v3 + H055 v3 KPI report cards per ADR-0014 §3.2 13-table format
Step 12 [docs]: CLAUDE.md Phase O.13 ledger entry + commit
```

Steps 1-7 are code + test + docs; can run in a 1-2 session-pass. Steps 8-9 are the multi-hour walk-forward; **operator-discretionary launch** (not auto-triggered). Steps 10-12 follow once the walk-forward completes.

## Risk register

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R-1 | Deep-wiring refactor breaks v2 numerical agreement on default-OFF path | high | All four primitive kwargs default None; numeric path bit-identical when None. Parity test in step 5 asserts v2-baseline cell numerics match pre-refactor on default-OFF invocation. |
| R-2 | Per-session BOCD update site (W8) doesn't have natural anchor in H062's per-bar loop | medium | Construct a `per_session_logret_accumulator` that flushes at session boundary; pass the just-completed session's arithmetic return to `bocd_live_update`. Reference implementation: H055 v2 `sm.on_session_close` pattern at [scripts/run_h055_v2_sweep.py:768-779](../../scripts/run_h055_v2_sweep.py). |
| R-3 | K-6/K-7 thresholds fire too aggressively → no trades on the test fold | medium | The defaults are -2% / -5% per ADR-0017 §5 + Turtle 2N convention; if the post-launch sidecar shows `trigger_counts.K-6 > 0.2 × n_session_days`, operator may relax thresholds via design.md §11.1 `# justify:` annotation. |
| R-4 | Cost-model subtraction overflows the marginal-positive Sharpe of H062 v3's strongest cell → flips MPPM sign | low | Cost prior is conservative-1-tick (~$5-30/round-trip per CME tick_value); on H062 v2's ~10K trades the cumulative drag is ~$50-300K vs $217.57% × $40K = $87K realized P/L; cost dominates. Expected: cost-realistic v3 produces NEGATIVE realized OOS on basket; this is the OPERATOR-VISIBLE COST-REALISM the project owes. |
| R-5 | Wall-clock for 4-symbol × 2-hypothesis × 5-7 hr/symbol exceeds 40 hr | medium | ADR-0010 wake-lock + ADR-0011 supervised-relaunch-loop handle multi-day execution; per-cfg checkpoint per ADR-0011 gate 12 allows resume on interruption. Operator may launch one hypothesis at a time. |
| R-6 | Phase O.11 shallow-CLI flags collide with new deep-wiring kwargs | low | The shallow Phase O.11 flags emit sidecar annotations + construct primitive configs only; the deep wiring consumes those configs. Phase O.13 unifies the two layers. |
| R-7 | Cross-link broken in this buildout document | low | grep audit before commit; all `[text](path)` resolve from `plan/buildouts/`. |
| R-8 | V3 KPI report card emission introduces drift from V2 numerics on default-OFF cells | low | The KPI report cards emit values from the sidecar; the sidecar is generated by `_run_per_trade_simulation` which is bit-identical on default-OFF (per R-1). Annotations may show as `kill-switch-inactive` / `bocd-live-active` / `cost-zero` on default-OFF, which is INFORMATIVE not contradictory. |

## Audit-remediate-loop posture

This buildout document goes through a Round 1 audit-remediate-loop (parallel lit + quant + format) before commit per the CLAUDE.md §"Agentic Iteration" discipline.

The audit-remediate-loops on the code refactors (steps 1 + 2) are separate Round 1 cycles, one per orchestrator. The post-run audit gate (step 10) is a third independent audit-remediate-loop per ADR-0011 §"Post-run audit gate."

Total audit-remediate-loop count for Phase O.13: 4 (buildout + H062 wire + H055 wire + post-run gate). Each ≤ SKILL.md 3-round cap.

## New follow-ups registered by Phase O.13 buildout

| Follow-up | Status | Description |
|---|---|---|
| `P1-PHASE-O13-H062-DEEP-WIRE-AUDIT` | scheduled | R1 audit-remediate on H062 deep-wire refactor (parallel quant + code + repro) |
| `P1-PHASE-O13-H055-DEEP-WIRE-AUDIT` | scheduled | R1 audit-remediate on H055 v2 deep-wire structural-cleanup |
| `P1-PHASE-O13-V3-KPI-POSTRUN-AUDIT` | scheduled | R1 post-run audit gate per ADR-0011 §"Post-run audit gate" on the v3 KPI emissions |
| `P1-H062-V3-RUNBOOK-LAND` | BLOCKING-BEFORE-LAUNCH | Land [research/01_hypothesis_register/H062/production_run_runbook_v3.md](../../research/01_hypothesis_register/H062/production_run_runbook_v3.md) per ADR-0011 §14 |
| `P1-H055-V3-RUNBOOK-LAND` | BLOCKING-BEFORE-LAUNCH | Land [research/01_hypothesis_register/H055/production_run_runbook_v3.md](../../research/01_hypothesis_register/H055/production_run_runbook_v3.md) per ADR-0011 §14 |
| `P1-PHASE-O13-PARITY-TEST-DEFAULT-OFF` | BLOCKING-CONCURRENT-WITH-DEEP-WIRE | Parity test asserts bit-identical v2-baseline numerics on default-OFF flags |
| `P1-PHASE-O13-INTEGRATION-TEST-FLAG-ON` | BLOCKING-CONCURRENT-WITH-DEEP-WIRE | Integration test verifies each primitive engages correctly when flagged ON |
| `P1-PHASE-O13-COST-DRAG-MAGNITUDE-EMPIRICAL` | non-blocking | Empirical measure of cost-drag magnitude on H062 v3 realized OOS; operator-visible cost-realism dossier |
| `P1-PHASE-O13-WALL-CLOCK-EMPIRICAL` | non-blocking | Empirical wall-clock for 4-symbol × 2-hypothesis x 5-7 hr/symbol; calibrate the buildout estimate |

## References

- [ADR-0011](../../docs/decisions/ADR-0011-production-walkforward-runbook.md) — production walk-forward runbook + 15-item preflight checklist.
- [ADR-0013](../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — permanent exploration + non-loss mandate.
- [ADR-0014 §3.2](../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — canonical 13-table KPI results summary.
- [ADR-0017](../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) — survival-constrained primary metric vector.
- [ADR-0018](../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — MPPM(ρ=1) primary fitness + Kelly grid + BOCD.
- [ADR-0023](../../docs/decisions/ADR-0023-metals-energy-futures-substrate-expansion.md) — metals/energy substrate (cost-model coverage).
- [ADR-0024](../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) — paradigm resolution; K-1..K-8 / FM-1..FM-5 / risk-of-ruin opt-in.
- [ADR-0025](../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) — abandonment-trigger infrastructure (this buildout's parent ADR).
- [docs/audits/audit_trail_2026-05-18_adr-0025-abandonment-infrastructure.md](../../docs/audits/audit_trail_2026-05-18_adr-0025-abandonment-infrastructure.md) — Phase O.11 + O.12 audit-remediate-loop trail.
