---
id: ADR-0025
title: Abandonment-trigger infrastructure — runtime kill switches, current-equity-rebase primitive, NT8-realistic multi-instrument cost model, BOCD live-pause
status: accepted
date: 2026-05-18
deciders: skoir
supersedes: []
proposes_amendments_to:
  - ADR-0014 §3.2 13-table format — Table 8 ("Other KPIs") extended with three new annotation rows: `kill-switch-active`, `bocd-live-pause`, `cost-empirical-calibrated` (operator-readable runtime-intervention disclosure; cascade per `P1-ADR-0025-TEMPLATE-CASCADE` lands in same commit group)
  - CLAUDE.md §"KPI report card for every strategy" — annotation grammar extended (cascade per `P1-ADR-0025-CLAUDE-MD-CASCADE` lands in same commit group)
preserves_immutability_of:
  - All hypothesis design.md §1-§7 (per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline)
  - All historical audit trails, ReproLogs, sidecars, KPI report cards, promotion logs, NinjaScript strategies, design.md §17 revision logs (per ADR-0013 §4.1 non-loss mandate)
  - ADR-0017 §4.1 drawdown-constrained Kelly sizing primitive at [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py) — preserved verbatim; ADR-0025 §D-2 wraps it with an `equity_rebase` adapter rather than replacing
  - ADR-0017 §5 kill-switch validation primitive at [src/skie_ninja/backtest/kill_switch_validation.py](../../src/skie_ninja/backtest/kill_switch_validation.py) — preserved verbatim; ADR-0025 §D-1 adds a parallel **runtime-intervention** module at [src/skie_ninja/backtest/kill_switch_runtime.py](../../src/skie_ninja/backtest/kill_switch_runtime.py) without modifying or replacing the post-hoc validator
  - ADR-0018 §D-3 BOCD batch primitive at [src/skie_ninja/inference/bocd.py](../../src/skie_ninja/inference/bocd.py) — preserved verbatim; ADR-0025 §D-4 wraps it with a live-state-machine adapter at [src/skie_ninja/inference/bocd_live.py](../../src/skie_ninja/inference/bocd_live.py)
  - ADR-0024 D-2 / D-3 / D-4 opt-in framing for K-1..K-8 / FM-1..FM-5 / risk-of-ruin — the new runtime primitives are opt-in tooling; they do NOT re-introduce BLOCKING mandatory inheritance
  - ADR-0013 §1 stage-progression model + §4 non-loss mandate + §5 NinjaScript-terminus mandate (preserved unchanged; the NinjaScript-layer kill switches remain operator-discretionary per-strategy)
---

# ADR-0025 — Abandonment-trigger infrastructure: runtime kill switches, current-equity rebase, NT8-realistic cost model, BOCD live-pause

## Context

### Why this ADR exists

Phase O.10 ([CLAUDE.md §"Phase O.10"](../../CLAUDE.md), 2026-05-18) emitted four v2 KPI report cards on the canonical substrate (SHA `317429e4...`): H062 v2, H060 v2, H055 v2, H065 v2. Three persistent operator concerns surfaced across the four-card review that none of the existing primitives address at the **production runtime** layer:

1. **No runtime kill-switch enforcement.** [src/skie_ninja/backtest/kill_switch_validation.py](../../src/skie_ninja/backtest/kill_switch_validation.py) (Phase O.2 closure of `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` per CLAUDE.md §"Phase O.2") is a **post-hoc validator** — it scans the per-trade ledger AFTER simulation completes and reports K-1..K-8 violations as KPI annotations. It does NOT intervene during simulation. Catastrophic max-drawdown trajectories (H062 v2 −93.26% basket; H055 v2 C5 super-Kelly+pyramid basket −6.6% with ES −53.5% / SIL −46.6% individual catastrophe) cannot be prevented at the per-trade entry layer with the current tooling. Per ADR-0024 §D-2, K-1..K-8 are opt-in (not mandatory); but operator-discretionary adoption requires a runtime-intervention layer that does not exist.

2. **Current-equity-rebase logic is duplicated inline across five orchestrators.** Per the 2026-05-18 cross-orchestrator audit, the boolean toggle + sizing-denominator switch lives inlined at [scripts/run_h055_v2_sweep.py:468-900](../../scripts/run_h055_v2_sweep.py) `_run_simulation`, [scripts/run_h062_aggressive_sizing_sweep.py](../../scripts/run_h062_aggressive_sizing_sweep.py), [scripts/run_h065_tp_overlay_sweep.py](../../scripts/run_h065_tp_overlay_sweep.py), [scripts/run_h065_sil_standalone_investigation.py](../../scripts/run_h065_sil_standalone_investigation.py), [scripts/run_h062_c3_2026_q1q2.py](../../scripts/run_h062_c3_2026_q1q2.py). The 5-file duplication is the canonical drift surface flagged by `P1-H062-CURRENT-EQUITY-REBASE-IMPL`. A shared primitive is the principled fix.

3. **NT8-realistic cost model covers ES/NQ/MES/MNQ only.** [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) hardcodes a four-symbol map. [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../src/skie_ninja/backtest/costs/futures_orb_v1.py) mirrors it for the H052a ORB. Neither covers MGC, SIL, or MCL — the metals/energy symbols added per [ADR-0023](ADR-0023-metals-energy-futures-substrate-expansion.md) and the H060 / H062 / H055 v2 / H065 v2 v2 universe. H062 v2 + H055 v2 + H065 v2 currently run cost-zero per the operator 2026-05-08 standing directive (pre-cost research-only), but `cost-zero-v1` is not an admissible promotion state; `P1-H062-COST-EMPIRICAL-CALIBRATION` + `P1-H055-COST-EMPIRICAL-CALIBRATION` are BLOCKING-BEFORE-PAPER-TRADE-EVALUATED per the design.md §11.2 tables. A multi-instrument cost model with explicit `calibration_source` provenance ("conservative-prior" vs "paper-trade-fill-log-empirical") is the canonical primitive.

4. **BOCD is a batch primitive; live trading needs a state machine.** [src/skie_ninja/inference/bocd.py](../../src/skie_ninja/inference/bocd.py) exposes `init_bocd` + `bocd_update` + `detect_decay`. The batch path is correct for walk-forward sidecars. Production live trading needs a **state machine** that: (a) tracks "pause state" once decay is detected; (b) holds the pause through a re-entry-eligibility criterion; (c) emits a pause-event log for ReproLog provenance; (d) re-enters when the criterion is met. The C9 BOCD-step-up logic in [scripts/run_h055_v2_sweep.py](../../scripts/run_h055_v2_sweep.py) (lines ~550-650 per the Phase O.4 audit at [docs/audits/audit_trail_2026-05-15_mpv1_c9_round1.md](../audits/audit_trail_2026-05-15_mpv1_c9_round1.md)) implements **adaptive Kelly halving**, NOT a hard pause. A hard-pause primitive is operationally distinct (Kelly halving stays in-market with smaller size; hard pause exits entirely until re-entry-criterion satisfies).

### Where this fits relative to ADR-0024

ADR-0024 (2026-05-15) demoted ADR-0017 §4.2 + §5 + §6 from "mandatory inheritance" to "opt-in tooling + KPI annotation." ADR-0025 does NOT re-introduce mandatory inheritance. The four primitives below are **opt-in implementations** of the operator-discretionary tooling that ADR-0024 D-2 / D-3 / D-4 explicitly authorized. They consolidate logic that already exists (inline + post-hoc + batch + four-symbol) into shared, well-tested, ReproLog-binding primitives.

The annotation grammar additions in §D-5 below are **disclosure annotations** — they declare what runtime-intervention layers the KPI report card's simulation actually invoked, separate from the design.md §11.1 declaration of which kill switches the hypothesis declares to use. The two annotation sets are orthogonal:

- ADR-0024 §"KPI annotation grammar additions": `kill-switch-{K-N-enabled, K-N-disabled}` — **design-time declaration** of which K-N constraints the hypothesis design.md §11.1 invokes.
- ADR-0025 §D-5: `kill-switch-active` / `kill-switch-inactive` — **runtime disclosure** of whether the simulator actually intervened during the sim (not "did the hypothesis declare K-N", but "did the runtime fire any K-N halt").

### Operator directive (2026-05-18)

> "let us close 4 BLOCKING-BEFORE-LIVE-PROMOTION follow-ups via the audit-remediate-loop skill: P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION (extend to runtime), P1-H062-CURRENT-EQUITY-REBASE-IMPL, P1-H062-COST-EMPIRICAL-CALIBRATION + P1-H055-COST-EMPIRICAL-CALIBRATION, BOCD live-pause wiring."

`P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` itself is already closed per CLAUDE.md Phase O.2 (the post-hoc validator). The operator directive reframes the remaining gap: extend the kill-switch primitive from post-hoc-validate to runtime-intervene. ADR-0025 is the formalization.

## Decision

### D-1. Runtime kill-switch intervention module at `src/skie_ninja/backtest/kill_switch_runtime.py`

A new module parallel to (NOT replacing) [src/skie_ninja/backtest/kill_switch_validation.py](../../src/skie_ninja/backtest/kill_switch_validation.py). The post-hoc validator continues to scan trade ledgers after simulation. The runtime module exposes hooks invoked **during** simulation:

- `KillSwitchRuntimeState(constraint_flags: dict[str, bool], daily_pnl_by_session_date: dict, weekly_pnl_by_week_id: dict, open_position_by_symbol: dict[str, OpenPositionRecord], current_session_date, current_week_id, equity_at_session_start: float, ...)` — frozen-on-entry state object passed by reference to the per-trade simulator. The `open_position_by_symbol` field is required for K-3 enforcement (see F-1-2 audit fix).
- `KillSwitchRuntimeConfig(enable_k3: bool, enable_k4: bool, enable_k6: bool, enable_k7: bool, ...)` — opt-in toggle per-constraint per design.md §11.1 declaration.
- `check_entry_blocked(state, *, symbol, side, entry_price, stop_price, position_size, ...) -> tuple[bool, str | None]` — returns `(blocked, reason)`; the simulator's entry path calls this before opening any new position and skips the trade on `blocked=True`. Reasons enumerated per K-N constraint. K-3 fires when `symbol in state.open_position_by_symbol` regardless of `side` (matches validator's unconditional same-symbol-overlap semantic at [kill_switch_validation.py:165-177](../../src/skie_ninja/backtest/kill_switch_validation.py)).
- `update_state_on_open(state, *, symbol, side, entry_ts, entry_price, position_size, stop_price, r_dollar) -> KillSwitchRuntimeState` — populates `open_position_by_symbol[symbol]` on trade open. Required for K-3 mid-simulation enforcement.
- `update_state_on_close(state, *, symbol, realized_pnl_dollar, exit_ts) -> KillSwitchRuntimeState` — clears `open_position_by_symbol[symbol]` + updates daily/weekly P/L accumulators keyed by `current_session_date` + `current_week_id`.
- `advance_session(state, *, session_date, equity_at_session_start) -> KillSwitchRuntimeState` — called by orchestrator at session boundary; recomputes `current_session_date` via canonical CME session-clock function (see F-1-1 audit fix below); records `equity_at_session_start` for K-6/K-7 threshold computation; daily-PnL accumulator for the new session starts at 0.
- `advance_week(state, *, week_id) -> KillSwitchRuntimeState` — analogous weekly reset; week_id is ISO-week of the CME session-date (NOT of the UTC timestamp).

**Session-boundary semantics** (F-1-1 audit fix). The `current_session_date` and `current_week_id` are derived from the **CME session calendar** at [src/skie_ninja/utils/clock.py](../../src/skie_ninja/utils/clock.py), NOT from UTC `entry_ts.date()`. Both the runtime module and the post-hoc validator at [src/skie_ninja/backtest/kill_switch_validation.py](../../src/skie_ninja/backtest/kill_switch_validation.py) import the canonical `session_date_from_timestamp` function from the shared constants module (per `P1-KILL-SWITCH-CONSTANTS-SHARED-MODULE` below). The validator's existing UTC-naive `entry_ts.date()` + `entry_ts.isocalendar()` calls are a known divergence flagged by `P1-KILL-SWITCH-VALIDATOR-SESSION-CLOCK-MIGRATE` (BLOCKING-CONCURRENT-WITH-RUNTIME); the parity test asserts identical session-date assignment across both modules for every trade in the runtime smoke fixture.

**K-6/K-7 threshold semantics** (F-1-7 audit fix). K-6 fires when `daily_pnl_by_session_date[current_session_date] < -0.02 × state.equity_at_session_start`; K-7 fires analogously at `-0.05 × equity_at_week_start`. The threshold ratchets DOWN with current equity (tightens the breaker during drawdowns) per the survival-constrained-discipline interpretation of ADR-0017 §5 K-6/K-7 phrasing. This is a behavioral CHANGE relative to the existing post-hoc validator's `-0.02 × starting_equity` static threshold; the validator is updated to match in the same commit group per `P1-KILL-SWITCH-VALIDATOR-EQUITY-RATCHET-MIGRATE` (BLOCKING-CONCURRENT-WITH-RUNTIME). KPI cards that previously reported `kill-switch-K-6-pass/fail` under the static-threshold convention require v3 re-emission to remain comparable; tracked under `P1-ADR-0025-V3-KPI-RERUN-H062-H055`.

Coverage at v1: **K-3 (no add-to-loser)** + **K-4 (per-symbol capacity cap)** + **K-6 (-2% daily P/L breaker; current-equity ratcheting)** + **K-7 (-5% weekly P/L breaker; current-equity ratcheting)**. K-1 / K-2 / K-5 / K-8 are structurally enforced elsewhere per the existing validator's `k_2_note` / `k_5_note` / `k_8_note` (K-1 via the 1R stop math at trade-open; K-2 via EOD-flatten; K-5 N/A for the current 4-symbol baskets {ES, NQ, MGC, SIL} containing no ADR-0017 §5 K-5 correlated-pair members; K-8 via trend-filter gate). K-5 N/A is **universe-conditional** (F-1-6 audit fix): the runtime module SHALL raise a validation error if invoked on a basket containing any pair from the ADR-0017 §5 K-5 taxonomy (e.g., the future H061 universe adding full-size CL alongside MCL); tracked under `P1-KILL-SWITCH-RUNTIME-K5-CORRELATED-EXTEND` BLOCKING-BEFORE-H061-PROD-RUN. v2 may extend runtime coverage to K-1 + K-8 per `P1-KILL-SWITCH-RUNTIME-K1-K8-EXTEND` (non-blocking).

The runtime module **shares the same K-1..K-8 thresholds + tolerances** as the post-hoc validator (canonical constants from ADR-0017 §5 + Turtle 2N convention per Faith 2007 *Way of the Turtle* ISBN 978-0071486644 *practitioner*). Drift between validator and runtime is the canonical regression surface flagged by `P1-KILL-SWITCH-VALIDATOR-RUNTIME-PARITY-TEST` (BLOCKING-CONCURRENT-WITH-ADR; lands in the test suite at [tests/unit/test_kill_switch_runtime.py](../../tests/unit/test_kill_switch_runtime.py)).

KPI report card disclosure annotation per §D-5: `kill-switch-active` if any K-N hook fired during simulation; `kill-switch-inactive` otherwise. The sidecar records per-K-N trigger counts under `kill_switch_runtime.trigger_counts: dict[str, int]` for provenance + auditability.

### D-2. Current-equity-rebase primitive at `src/skie_ninja/backtest/equity_rebase.py`

A new module that lifts the inlined `eq_for_sizing = current_equity if use_current_equity_rebase else starting_equity` pattern into a shared, type-safe primitive:

- `EquityRebasePolicy(mode: Literal["fixed", "current", "min_of_current_and_starting"], starting_equity: float, floor_equity_fraction: float = 0.10)` — frozen dataclass.
  - `mode="fixed"` returns `starting_equity` always (ADR-0017 §4.1 pre-2026-05-08 default).
  - `mode="current"` returns `max(current_equity, floor_equity_fraction × starting_equity)`. **Acknowledged deviation from strict Kelly semantics** (F-1-3 audit fix): when `current_equity < floor_equity_fraction × starting_equity`, this floor produces deliberate OVER-sizing relative to the Kelly-optimal at that bankroll state, contrary to the Vince 1990 gambler's-ruin principle. The floor is operationally justified — `# justify:` Phase O.3 MGC fixed-rebase empirical blowup at `min_equity = −$656` per CLAUDE.md §"Phase O.3" was the canonical pathology the floor prevents; without a floor, the rebase semantic divides by ≈0 once a leg is bankrupted, producing infinite sizing on the recovery attempt. Operators concerned about Kelly-strict adherence at low bankroll states should select `mode="min_of_current_and_starting"` instead.
  - `mode="min_of_current_and_starting"` returns `min(current_equity, starting_equity)` (Kelly-strict; protects against over-sizing after a run-up but does not floor at zero — a bankrupted leg produces zero sizing per Vince 1990 *practitioner* Ch. 5 gambler's-ruin convention).
- `equity_for_sizing(policy: EquityRebasePolicy, current_equity: float) -> float` — single-call API replacing the inline ternary.
- `apply_pnl_to_equity(equity: float, realized_pnl_dollar: float) -> float` — accumulator with floor-at-zero clamp (a bankrupt account cannot go further negative; Vince 1990 *Portfolio Management Formulas* Ch. 5 "Risk of Ruin" *practitioner* convention).

The primitive defaults to `mode="current"` with `floor_equity_fraction=0.10` (matches the H055 v2 + H062 aggressive-sizing sweep convention per Phase O.3 / Phase O.4); operator may override per-sweep. `# justify:` annotations for the 0.10 default are required at the implementation site per the magic-number-policy enforcement at [src/skie_ninja/backtest/equity_rebase.py](../../src/skie_ninja/backtest/equity_rebase.py).

KPI report card disclosure annotation: none required (current-equity vs fixed-equity is already disclosed in the §"Methodological-correctness annotations" line of every KPI card per the existing sidecar provenance schema). The primitive change is structural-deduplication only.

### D-3. NT8-realistic multi-instrument cost model at `src/skie_ninja/backtest/costs/nt8_realistic.py`

A new cost model that extends the ES/NQ/MES/MNQ symbol set of [nt8_es_nq_rth_v1.py](../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) to include the metals/energy symbols added per [ADR-0023](ADR-0023-metals-energy-futures-substrate-expansion.md): MCL, MGC, SIL.

Public API mirrors the existing cost-model contract:

- `NT8RealisticCostModel(sensitivity_mult: float = 1.0, calibration_source: Literal["conservative_prior", "paper_trade_empirical"] = "conservative_prior", empirical_overrides: dict[str, EmpiricalFeeOverride] | None = None)`.
- `.cost_model_id: ClassVar[str] = "nt8_realistic_v1"`.
- `.round_trip_cost_usd(symbol: str, n_contracts: int = 1) -> float` — matches the [futures_orb_v1.py](../../src/skie_ninja/backtest/costs/futures_orb_v1.py) signature.
- `.cost_per_session_log_return(*, symbol: str, entry_price: float, n_contracts: int = 1) -> float` — daily-cleared session-cadence log-return drag.
- `.cost_per_bar_return(symbol: str, position: float, price: float, n_contracts: int = 1) -> float` — matches the existing [nt8_es_nq_rth_v1.py](../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) signature for bar-cadence strategies.
- `.fee_breakdown(symbol: str) -> dict[str, float]` — same shape as existing models.

Fee schedule loads from [config/instruments.yaml](../../config/instruments.yaml) at module-import time per `commission_per_side_usd` / `exchange_fee_usd` / `nfa_fee_usd` per-symbol entries. Slippage prior = 1-tick from `tick_value` per existing convention. For MGC / SIL / MCL the instruments.yaml values are marked as **placeholders pending P1-METALS-ENERGY-CME-FEE-VERIFY** per CLAUDE.md §"Phase O.0 Stage B"; the cost model surfaces this provenance via `fee_breakdown(symbol)["provenance"] = "instruments_yaml_placeholder"`.

Empirical-calibration hook: `EmpiricalFeeOverride` is a frozen dataclass `(fixed_per_side_usd: float, slip_per_side_usd: float, source: str, source_sha256: str, source_n_fills: int)` that operators may pass at construction. When supplied for a symbol, the override replaces the instruments.yaml-derived prior; `calibration_source="paper_trade_empirical"` is recorded in the sidecar + ReproLog provenance. The override path is the canonical extension for the H050 + H055 + H062 paper-trade-fill-log empirical replacement per `P1-H050-COST-EMPIRICAL-CALIBRATION` + `P1-H055-COST-EMPIRICAL-CALIBRATION` + `P1-H062-COST-EMPIRICAL-CALIBRATION`.

**Sensitivity-multiplier precedence** (F-1-5 audit fix): when an `EmpiricalFeeOverride.slip_per_side_usd` is supplied for a symbol, `sensitivity_mult` is **IGNORED for that symbol's slip component** (with WARN logged at module level). Rationale: empirical-override slip is a calibrated quantity from paper-trade fill data, not a prior to be scaled. `sensitivity_mult` continues to apply on the conservative-prior path. The unit test `test_nt8_realistic_sensitivity_mult_ignored_with_empirical_override` enforces this precedence.

KPI report card disclosure annotation per §D-5: `cost-empirical-calibrated` if `calibration_source="paper_trade_empirical"` at run time; `cost-conservative-prior` if `calibration_source="conservative_prior"`; `cost-zero` if the cost model is bypassed entirely. The sidecar records the per-symbol fee schedule + `n_fills` for the empirical-override path.

### D-4. BOCD live-pause state machine at `src/skie_ninja/inference/bocd_live.py`

A new module wrapping the [bocd.py](../../src/skie_ninja/inference/bocd.py) batch primitive with a hard-pause state machine per the [Adams-MacKay 2007](https://arxiv.org/abs/0710.3742) recursion. The wrapping is structural; the underlying Bayesian posterior update is preserved verbatim.

Public API:

- `BOCDLiveState` — frozen dataclass `(bocd_state: BOCDState, pause_active: bool, pause_entered_session_idx: int | None, pause_entered_ts_utc: str | None, sessions_since_pause: int, n_pause_events: int, re_entry_criterion: str, pause_event_log: list[dict], ...)`. Each `pause_event_log` entry contains both `session_idx` (deterministic from substrate) and `ts_utc` (ISO-8601 UTC absolute timestamp) per F-1-8 audit fix — dual encoding makes replay robust against session-calendar drift.
- `BOCDLiveConfig(hazard_rate: float = 1/250, window: int = 60, decay_threshold: float = 0.5, re_entry_criterion: Literal["posterior_below_threshold", "fixed_session_count", "manual"] = "posterior_below_threshold", re_entry_threshold: float = 0.20, re_entry_session_count: int = 60, min_pause_duration_sessions: int = 20, post_resume_state: Literal["reinit", "zero_changepoint_mass"] = "reinit")` — frozen-on-init.
- `init_bocd_live(config: BOCDLiveConfig, *, mu_0=0.0, kappa_0=1.0, alpha_0=1.0, beta_0=1.0) -> BOCDLiveState`.
- `bocd_live_update(state: BOCDLiveState, x_t: float, *, session_idx: int, ts_utc: str) -> BOCDLiveState` — runs one BOCD update + evaluates pause-state transition per the configured criterion + re-entry-eligibility check; returns a new state.
- `is_paused(state: BOCDLiveState) -> bool` — short-circuit query for the orchestrator's entry path.
- `summarize_pause_events(state: BOCDLiveState) -> dict[str, Any]` — provenance summary `(n_pause_events, total_sessions_paused, longest_pause_run, first_pause_session_idx, last_pause_session_idx, pause_event_log, ...)` for sidecar emission.

Three re-entry criteria at v1:

- `posterior_below_threshold` (default): re-enter when the recent-changepoint posterior P(r_t < window/2) drops back below `re_entry_threshold` (`# justify:` 0.20 default — operator-prior hysteresis band beneath the 0.5 decay-detection threshold; empirical calibration pending `P1-BOCD-LIVE-REENTRY-EMPIRICAL`). Symmetric counterpart to the decay-detection threshold; constant-hazard prior per Adams-MacKay 2007 (exact section pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`).
- `fixed_session_count`: re-enter after `re_entry_session_count` (`# justify:` 60-session default — matches ADR-0018 §D-3 `window=60` for consistency of forgetting-horizon convention; empirical calibration pending `P1-BOCD-LIVE-REENTRY-EMPIRICAL`) sessions after pause-entry, regardless of posterior. Useful for hypotheses where the operator wants a hard fixed pause-duration.
- `manual`: requires an explicit `manually_resume(state)` call; the simulator skips entries while paused. Useful for paper-trade live-monitor wiring where the operator review gates resumption.

**Flap-suppression: minimum pause duration** (F-1-4 audit fix). All three re-entry criteria are subject to a hard floor `min_pause_duration_sessions` (`# justify:` 20-session default — operator-prior; one calendar month of trading sessions is the canonical minimum duration for any regime-change to be statistically distinguishable from noise per the BOCD posterior's hazard-prior decay rate of 1/250). Re-entry cannot fire before `min_pause_duration_sessions` have elapsed since pause-entry, regardless of the posterior or the fixed-count criterion. This addresses the flap pathology where a single noisy MPPM observation can drive the posterior back above 0.5 within a few observations of resume.

**Post-resume BOCDState semantic** (F-1-4 audit fix). On re-entry, the underlying `BOCDState` is reset per `post_resume_state`:

- `reinit` (default): re-initialize `BOCDState` from priors (`mu_0`, `kappa_0`, `alpha_0`, `beta_0`); loses prior history but mathematically clean — the post-resume regime is treated as a fresh segment per Adams-MacKay 2007 constant-hazard prior. This is the canonical-cleanup convention; preserves the segment-prior independence assumption.
- `zero_changepoint_mass`: zero the changepoint mass at `r_t=0` and re-normalize the run-length posterior, preserving the per-run-length NIG sufficient statistics. Preserves prior precision but may bias subsequent change-detection. Documented as project-operational per `P1-BOCD-LIVE-POSTDETECT-RESET-CONVENTION` (non-blocking; pending empirical comparison via paper-trade).

KPI report card disclosure annotation per §D-5: `bocd-live-pause` if `n_pause_events > 0` during simulation; `bocd-live-active` otherwise. The sidecar records the per-pause-event log (`pause_entered_session_idx`, `pause_exited_session_idx`, `pause_duration_sessions`, `pause_trigger_posterior`, `re_entry_posterior`).

### D-5. KPI annotation grammar additions

Three new annotations extend the CLAUDE.md §"KPI report card for every strategy" grammar:

- `kill-switch-{active, inactive}` — runtime-intervention disclosure per §D-1. Distinct from the ADR-0024 §"KPI annotation grammar additions" `kill-switch-{K-N-enabled, K-N-disabled}` design-time declaration: the new annotation reports whether the runtime hook **actually fired** during simulation, regardless of which K-N constraints the design.md §11.1 declared. Both annotations co-exist on the same KPI report card.
- `bocd-live-pause` / `bocd-live-active` — live-state-machine disclosure per §D-4. Distinct from the ADR-0018 §D-3 `decay-detected-{yes, no}` annotation which reports a one-shot batch-BOCD verdict on the rolling MPPM path. `bocd-live-pause` reports the live-state-machine outcome integrated over the simulation: did the simulator actually halt entries at any point. A hypothesis MAY have `decay-detected-yes` + `bocd-live-active` simultaneously if the live state machine's `re_entry_criterion` returned the simulator to active before sim-end; or `decay-detected-no` + `bocd-live-pause` if a brief flap triggered a pause that re-entered (edge case mitigated by `min_pause_duration_sessions` per §D-4 F-1-4 fix).
- `cost-{empirical-calibrated, conservative-prior, zero}` — cost-model-PROVENANCE disclosure per §D-3. **Orthogonal to** the legacy `cost-{robust, conditional, flat}` SENSITIVITY-regime annotations preserved verbatim from ADR-0012/0013 era per ADR-0013 §4.1 non-loss; both annotation families MAY co-exist on the same KPI report card (FA-4-1 audit fix). Provenance annotation answers "where did the fee schedule come from" (paper-trade-fill-log empirical, instruments.yaml conservative prior, or bypassed-zero-cost); sensitivity annotation answers "how robust is the result to fee-schedule perturbation" (robust = passes 2-tick sensitivity sweep; conditional = passes 1-tick only; flat = no sensitivity test run). Replaces the ad-hoc `cost-zero-v1-pre-cost-research-only` annotation used in H062 v1 / H055 v2 / H065 v2 with a structured provenance annotation.

Cascade requirements (per `P1-ADR-0025-TEMPLATE-CASCADE` lands in same commit group): [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) Table 8 ("Other KPIs") gains three rows in the canonical 13-table format. [docs/glossary.md](../../docs/glossary.md) gains entries for the three new annotations (cascade per `P1-ADR-0025-GLOSSARY-CASCADE` non-blocking).

### D-6. Mandatory orchestrator wiring at H062 + H055 v2

The four primitives are wired into the two production orchestrators per the operator directive:

- [scripts/run_h062_walk_forward.py](../../scripts/run_h062_walk_forward.py) — `_run_per_trade_simulation` per-trade loop integrates:
  - `KillSwitchRuntimeState` at simulator-entry; `check_entry_blocked` at each entry-signal site; `update_state_on_close` at each `_close_position` call.
  - `EquityRebasePolicy` replaces inline `eq_for_sizing` calculations.
  - `BOCDLiveState` advanced per-session on the per-session-MPPM rolling sequence; `is_paused` short-circuits entry-eligibility.
  - `NT8RealisticCostModel` replaces the existing `cost=0` path with a `calibration_source="conservative_prior"` instance at default (operator may pass `calibration_source="paper_trade_empirical"` via CLI).
- [scripts/run_h055_v2_sweep.py](../../scripts/run_h055_v2_sweep.py) — `_run_simulation` per-trade loop integrates the same four primitives. The C9 BOCD-step-up Kelly-halving stays as a SECOND-layer halving (orthogonal to D-4's hard pause); the operator may invoke C9 alone, D-4 alone, or both stacked (the C9 halving is conservative-sizing-adjustment; D-4 is hard halt). C5 pyramid + D-4 hard pause is a degenerate combination (pyramiding is structurally inactive while paused) but admissible.

Sweep configs gain an opt-in flag per primitive (default: all OFF at v1 to preserve numerical agreement with existing v2 KPI cards). v3 KPI report card re-emission with the four primitives ON is tracked under `P1-ADR-0025-V3-KPI-RERUN-H062-H055` (non-blocking; sequenced per operator priority).

### D-7. ReproLog provenance binding

Per the canonical 13-field ReproLog schema at [src/skie_ninja/utils/reproducibility.py](../../src/skie_ninja/utils/reproducibility.py), the four primitives' runtime state is bound into the sidecar's `scientific_payload` field at:

- `scientific_payload.kill_switch_runtime`: `{enabled_constraints: list[str], trigger_counts: dict[str, int], runtime_active: bool}`.
- `scientific_payload.equity_rebase`: `{mode: str, starting_equity: float, floor_equity_fraction: float, final_equity: float, min_equity_during_sim: float}`.
- `scientific_payload.cost_model`: `{cost_model_id: str, calibration_source: str, sensitivity_mult: float, fee_breakdown: dict, empirical_override_provenance: dict | null}`.
- `scientific_payload.bocd_live`: `{n_pause_events: int, total_sessions_paused: int, longest_pause_run: int, pause_event_log: list[dict], re_entry_criterion: str}`.

The four sub-blocks are deterministic functions of the sim inputs + config; their inclusion in `scientific_payload` ensures the `scientific_payload_sha256` covers them per the canonical ReproLog binding discipline.

## Alternatives considered

### A. Extend the existing post-hoc validator with runtime hooks in-place

Rejected. The post-hoc validator's API surface is structured for ledger-scanning (it consumes `list[TradeRecord]` after the fact). Bolting runtime hooks onto the same module would conflate two operational modes (post-hoc scan vs runtime intervene) that have legitimately different semantics. Separation per §D-1 preserves the post-hoc validator verbatim (per the ADR-0013 §4.1 non-loss mandate) and adds the runtime layer as a parallel module. Drift between the two is enforced by the parity test per `P1-KILL-SWITCH-VALIDATOR-RUNTIME-PARITY-TEST`.

### B. Inline the four primitives in each orchestrator individually

Rejected. The 5-file duplication of the equity-rebase logic (already in the field) is the canonical drift pathology. Three primitives × five orchestrators = 15 files-to-keep-in-sync. The shared-primitive approach reduces this to 3 modules + 5 import sites with type-checked APIs.

### C. Single mega-module `abandonment_triggers.py` containing all four primitives

Rejected. The four primitives have orthogonal concerns: kill-switch runtime is per-trade-entry intervention; equity rebase is per-trade-sizing math; cost model is per-trade-cost math; BOCD live-pause is per-session decay-detection state machine. Single-module aggregation would create a 1000+ line file with mixed responsibilities. The per-concern split per §D-1..§D-4 follows the project's existing module-per-concern pattern at [src/skie_ninja/backtest/](../../src/skie_ninja/backtest/) + [src/skie_ninja/inference/](../../src/skie_ninja/inference/).

### D. Re-introduce K-1..K-8 mandatory inheritance via ADR-0025

Rejected. ADR-0024 §D-2 demoted K-1..K-8 from mandatory to opt-in two days ago (2026-05-15). Re-introducing mandatory inheritance via ADR-0025 would directly contradict ADR-0024's resolution of the user's 2026-05-15 directive ("adr 17 is ruining present and all future hypothesis testing"). The opt-in framing is preserved verbatim: ADR-0025 §D-1 makes the runtime intervention **available** without making it **mandatory**.

### E. Use a different changepoint detector (e.g., CUSUM, GLR, PELT) for the live-pause module

Rejected at v1; tracked under `P1-BOCD-LIVE-ALTERNATIVE-DETECTORS-V2` (non-blocking). The project-canonical decay detector per [ADR-0018 §D-3](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) is BOCD; introducing a different detector in the live-pause module would create an asymmetry with the batch primitive. The two are aligned by sharing the underlying [bocd.py](../../src/skie_ninja/inference/bocd.py) primitive; the live module is a wrapper, not a replacement.

### F. Defer the four primitives until paper-trade data exists for empirical calibration

Rejected. The four primitives are structurally distinct from the empirical-calibration data they consume:

- `kill_switch_runtime.py` uses canonical Turtle 2N / ADR-0017 §5 thresholds; no empirical calibration needed at v1.
- `equity_rebase.py` is pure-math; no empirical calibration.
- `nt8_realistic.py` has an `empirical_overrides` hook for paper-trade data when it exists; the default conservative prior is shippable today and matches the existing `nt8_es_nq_rth_v1.py` semantic.
- `bocd_live.py` uses canonical Adams-MacKay 2007 priors per the existing batch primitive; no empirical calibration needed at v1.

Empirical calibration follow-ups (`P1-METALS-ENERGY-CME-FEE-VERIFY`, `P1-H062-COST-EMPIRICAL-CALIBRATION`, `P1-H055-COST-EMPIRICAL-CALIBRATION`, `P1-BOCD-HAZARD-RATE-EMPIRICAL`, `P1-RELIABILITY-SLOPE-EMPIRICAL-CALIBRATION`) refine constants without requiring the primitives to wait.

## Consequences

### Adopted

- [src/skie_ninja/backtest/kill_switch_runtime.py](../../src/skie_ninja/backtest/kill_switch_runtime.py) — runtime kill-switch intervention module per §D-1. Coverage: K-3, K-4, K-6, K-7 at v1; K-1 / K-8 v2-extendable.
- [src/skie_ninja/backtest/equity_rebase.py](../../src/skie_ninja/backtest/equity_rebase.py) — current-equity-rebase primitive per §D-2.
- [src/skie_ninja/backtest/costs/nt8_realistic.py](../../src/skie_ninja/backtest/costs/nt8_realistic.py) — multi-instrument cost model with empirical-calibration hook per §D-3.
- [src/skie_ninja/inference/bocd_live.py](../../src/skie_ninja/inference/bocd_live.py) — BOCD live-pause state machine per §D-4.
- Three new KPI annotations per §D-5: `kill-switch-active`, `bocd-live-pause`, `cost-empirical-calibrated`.
- Orchestrator wiring at [scripts/run_h062_walk_forward.py](../../scripts/run_h062_walk_forward.py) + [scripts/run_h055_v2_sweep.py](../../scripts/run_h055_v2_sweep.py) per §D-6 (default OFF; opt-in flag per primitive).
- ReproLog `scientific_payload` extension per §D-7.

### KPI annotation grammar additions

Three new annotations extend the CLAUDE.md §"KPI report card for every strategy" grammar:

- `kill-switch-{active, inactive}` — runtime-intervention disclosure.
- `bocd-live-pause` / `bocd-live-active` — live-state-machine disclosure.
- `cost-empirical-calibrated` / `cost-conservative-prior` / `cost-zero` — cost-model-provenance disclosure.

The existing annotations (`kill-switch-{K-N-enabled, K-N-disabled}`, `decay-detected-{yes, no}`, `cost-{robust, conditional, flat}`) are preserved verbatim per ADR-0013 §4.1.

### Trade-offs accepted

- **Additional configuration surface area.** Each orchestrator gains four opt-in flags. Mitigated by: (a) defaults preserve existing v2 KPI card numerics; (b) the flags are flat-key in the YAML config (no nesting drift); (c) provenance is captured in the sidecar.
- **Two-layer abandonment trigger (Kelly halving via C9 + hard pause via D-4) on H055 v2.** The Phase O.4 C9 step-up + the new hard pause are orthogonal. The operator MAY use either alone or both stacked. Documented in design.md cascade.
- **The post-hoc validator + runtime module share constants but live in two files.** Drift surface mitigated by `P1-KILL-SWITCH-VALIDATOR-RUNTIME-PARITY-TEST` BLOCKING-CONCURRENT.
- **MGC / SIL / MCL fee placeholders.** `cost-conservative-prior` annotation correctly discloses this. Primary-source verification tracked under `P1-METALS-ENERGY-CME-FEE-VERIFY` (pre-existing).
- **K-1 / K-2 / K-5 / K-8 not in runtime module at v1.** Documented per §D-1; v2-extendable via `P1-KILL-SWITCH-RUNTIME-K1-K8-EXTEND`.

### Residual risk

- **The four primitives are tested only via the H062 + H055 v2 smoke runs at adoption time.** Unit tests at [tests/unit/test_kill_switch_runtime.py](../../tests/unit/test_kill_switch_runtime.py) + [tests/unit/test_equity_rebase.py](../../tests/unit/test_equity_rebase.py) + [tests/unit/test_nt8_realistic.py](../../tests/unit/test_nt8_realistic.py) + [tests/unit/test_bocd_live.py](../../tests/unit/test_bocd_live.py) land in the ADR-0025 commit group. Coverage extension to H060 + H065 v2 tracked under `P1-ADR-0025-WIRE-H060-H065`.
- **BOCD live-pause re-entry criteria are operator-tunable but not empirically calibrated.** The 20% re-entry-posterior + 60-session-count defaults match the ADR-0018 §D-3 decay-detection threshold by hysteresis convention; empirical calibration via paper-trade data tracked under `P1-BOCD-LIVE-REENTRY-EMPIRICAL`.
- **Drift between the post-hoc validator's K-1..K-8 thresholds and the runtime module's thresholds.** The parity test enforces shared constants; both modules import from a new [src/skie_ninja/backtest/kill_switch_constants.py](../../src/skie_ninja/backtest/kill_switch_constants.py) single-source-of-truth module per `P1-KILL-SWITCH-CONSTANTS-SHARED-MODULE`.

### Cascade requirements

- **`P1-ADR-0025-CLAUDE-MD-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — CLAUDE.md §"KPI report card for every strategy" gains the three new annotations + a Phase O.11 ledger entry per the project convention.
- **`P1-ADR-0025-TEMPLATE-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) Table 8 ("Other KPIs") gains three rows for the new annotations.
- **`P1-ADR-0025-GLOSSARY-CASCADE`** (non-blocking) — [docs/glossary.md](../../docs/glossary.md) gains entries for the three new annotations.
- **`P1-ADR-0025-DECISIONS-README-CASCADE`** (non-blocking) — [docs/decisions/README.md](README.md) gains the ADR-0025 entry.
- **`P1-ADR-0025-V3-KPI-RERUN-H062-H055`** (non-blocking) — v3 KPI report card re-emission with the four primitives ON for H062 + H055 v2; sequenced per operator priority.
- **`P1-ADR-0025-WIRE-H060-H065`** (non-blocking) — extend the four-primitive wiring to [scripts/run_h060_walk_forward.py](../../scripts/run_h060_walk_forward.py) + [scripts/run_h065_tp_overlay_sweep.py](../../scripts/run_h065_tp_overlay_sweep.py).
- **`P1-ADR-0025-DESIGN-MD-CASCADE`** (non-blocking) — per-hypothesis design.md §11.1 may invoke the new runtime kill switches with `# justify:` annotation. Frozen §1-§7 untouched per ADR-0013 §"Frozen pre-registration amendment."

### BLOCKING follow-ups registered by ADR-0025

| Follow-up | Status | Description |
|---|---|---|
| `P1-KILL-SWITCH-VALIDATOR-RUNTIME-PARITY-TEST` | BLOCKING-CONCURRENT-WITH-ADR | Unit test asserts the runtime module's K-1..K-8 thresholds + tolerances match the post-hoc validator's; both import from a single source-of-truth constants module |
| `P1-KILL-SWITCH-CONSTANTS-SHARED-MODULE` | BLOCKING-CONCURRENT-WITH-ADR | Single-source-of-truth constants module at [src/skie_ninja/backtest/kill_switch_constants.py](../../src/skie_ninja/backtest/kill_switch_constants.py) imported by both validator + runtime |
| `P1-KILL-SWITCH-VALIDATOR-SESSION-CLOCK-MIGRATE` | BLOCKING-CONCURRENT-WITH-RUNTIME | Migrate [kill_switch_validation.py](../../src/skie_ninja/backtest/kill_switch_validation.py) from UTC-naive `entry_ts.date()` / `isocalendar()` to the canonical CME session-clock function exported by `kill_switch_constants.py` (F-1-1 audit fix) |
| `P1-KILL-SWITCH-VALIDATOR-EQUITY-RATCHET-MIGRATE` | BLOCKING-CONCURRENT-WITH-RUNTIME | Migrate [kill_switch_validation.py](../../src/skie_ninja/backtest/kill_switch_validation.py) K-6/K-7 threshold from `starting_equity` to `equity_at_session_start` (current-equity ratcheting; F-1-7 audit fix) |
| `P1-KILL-SWITCH-RUNTIME-K5-CORRELATED-EXTEND` | BLOCKING-BEFORE-H061-PROD-RUN | Extend runtime K-5 coverage when basket adds full-size CL alongside MCL (or GC alongside MGC, or SI alongside SIL) per F-1-6 audit fix |
| `P1-ADR-0025-CLAUDE-MD-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | CLAUDE.md annotation grammar + Phase O.11 ledger entry |
| `P1-ADR-0025-TEMPLATE-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | KPI results-summary template Table 8 extension |
| `P1-FAITH-2007-CHAPTER-PIN-VERIFY` | non-blocking (citation-pin) | Verify Faith 2007 chapter pin for 2N stop convention + Turtle System 2 pyramiding (R1 audit L-3) |
| `P1-AFML-CHAPTER-PIN-VERIFY` | non-blocking (citation-pin) | Verify López de Prado 2018 AFML chapter pin for per-trade fill convention (R1 audit L-1) |
| `P1-WILDER-1978-CHAPTER-PIN-VERIFY` | non-blocking (citation-pin) | Verify Wilder 1978 chapter pin for ATR convention (R1 audit L-5) |

### Non-blocking follow-ups registered by ADR-0025

| Follow-up | Description |
|---|---|
| `P1-KILL-SWITCH-RUNTIME-K1-K8-EXTEND` | Extend runtime coverage from K-3/K-4/K-6/K-7 to include K-1 + K-8 (K-2 + K-5 remain structurally enforced elsewhere) |
| `P1-BOCD-LIVE-REENTRY-EMPIRICAL` | Empirical calibration of the 20% re-entry-posterior + 60-session-count defaults via paper-trade data |
| `P1-BOCD-LIVE-ALTERNATIVE-DETECTORS-V2` | Evaluate CUSUM / GLR / PELT as alternative changepoint detectors for the live-pause module |
| `P1-ADR-0025-WIRE-H060-H065` | Extend the four-primitive wiring to H060 walk-forward + H065 sweep |
| `P1-ADR-0025-V3-KPI-RERUN-H062-H055` | v3 KPI report card emission with primitives ON |
| `P1-ADR-0025-DESIGN-MD-CASCADE` | Per-hypothesis design.md §11.1 invocation with `# justify:` annotation |
| `P1-ADR-0025-GLOSSARY-CASCADE` | Glossary entries for the three new annotations |
| `P1-ADR-0025-DECISIONS-README-CASCADE` | ADR README entry |
| `P1-KILL-SWITCH-RUNTIME-INSTRUMENT-CAP-EMPIRICAL` | Calibrate K-4 per-symbol capacity caps against post-paper-trade fill data per `P1-ADR-0001-METALS-ENERGY-CAPACITY-CALIBRATE` |
| `P1-COST-MODEL-METALS-ENERGY-EMPIRICAL-OVERRIDE` | Empirical fee overrides for MGC / SIL / MCL once paper-trade fill data exists |
| `P1-BOCD-LIVE-POSTDETECT-RESET-CONVENTION` | Empirical comparison of `reinit` vs `zero_changepoint_mass` post-resume state semantics; sequenced after paper-trade data exists (F-1-4 audit fix) |

## References

### Primary peer-reviewed sources

- Adams, R. P., & MacKay, D. J. C. (2007). Bayesian online changepoint detection. [arXiv:0710.3742](https://arxiv.org/abs/0710.3742). (BOCD primitive underlying the live-pause module per §D-4; exact section + equation pins deferred to `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY` pending primary-PDF access.)
- Goetzmann, W., Ingersoll, J., Spiegel, M., & Welch, I. (2007). Portfolio performance manipulation and manipulation-proof performance measures. *Review of Financial Studies*, 20(5), 1503–1546. [DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025). (MPPM(ρ=1) — the per-session reward sequence consumed by the BOCD live-pause module per ADR-0018 §D-1 / §D-3.)
- Kelly, J. L. (1956). A new interpretation of information rate. *Bell System Technical Journal*, 35(4), 917–926. [DOI 10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x). (Log-optimal bet sizing — underlies the current-equity-rebase math at §D-2.)
- Lo, A. W. (2004). The Adaptive Markets Hypothesis: Market efficiency from an evolutionary perspective. *Journal of Portfolio Management*, 30(5), 15–29. [DOI 10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611). (AMH framing — strategy decay is the null; the live-pause module is the operational instantiation of "regime-conditional efficiency" per Lo 2004 §III.)

### Practitioner sources (tagged per CLAUDE.md §"Practitioner-source-tag" convention)

- Faith, C. (2007). *Way of the Turtle: The Secret Methods that Turned Ordinary People into Legendary Traders*. McGraw-Hill, ISBN-13 978-0071486644. (*practitioner*) Turtle 2N stop convention + Turtle System 2 pyramiding — anchor for K-1 per-trade dollar-stop semantic. Chapter-level section pin deferred per `P1-FAITH-2007-CHAPTER-PIN-VERIFY` pending primary-text re-verification (R1 audit L-3 flagged the prior §2 / §4 pins as misattributed; chapter titles are "Taming the Turtle Mind" (Ch.2) and "Think Like a Turtle" (Ch.4); 2N/pyramiding mechanics live in later chapters + the bonus "Original Turtle Trading Rules" appendix).
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley, ISBN-13 978-1119482086. (*practitioner*) Per-trade simulation + pessimistic fill conventions; chapter-level section pin deferred per `P1-AFML-CHAPTER-PIN-VERIFY` (R1 audit L-1 flagged the prior §13.2 pin as misattributed; AFML §13.2 is "Trading Rules" inside Ch. 13 "Backtesting on Synthetic Data" — fill-convention discipline likely lives in earlier chapters on labeling / data structures or in Ch. 14 "Backtest Statistics").
- Vince, R. (1990). *Portfolio Management Formulas: Mathematical Trading Methods for the Futures, Options, and Stock Markets*. Wiley, ISBN-13 978-0471527565. (*practitioner*) Ch. 5 "Risk of Ruin" — anchor for the floor-at-zero equity clamp in `apply_pnl_to_equity` per §D-2 (R1 audit L-4 fix: prior citation to Ch. 4 was the "Optimal Fixed Fractional Trading" Kelly-fraction chapter, NOT the gambler's-ruin chapter).
- Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*. Trend Research, ISBN-13 978-0894590276. (*practitioner*) Average True Range convention — underlies the dollar-1R-distance computation at the kill-switch K-1 entry-time check. Chapter pin deferred per `P1-WILDER-1978-CHAPTER-PIN-VERIFY` (R1 audit L-5 flagged the prior §IX pin as unverifiable from public TOC sources).
- Tharp, V. K. (1998). *Trade Your Way to Financial Freedom*. McGraw-Hill, ISBN-13 978-0070647626. (*practitioner*) R-multiple convention — underlies the realized-R-multiple computation consumed by the runtime kill-switch state.

### Project-internal

- [ADR-0001](ADR-0001-project-scope.md) — retail capacity ceiling (K-4 thresholds).
- [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — non-loss mandate + frozen-pre-reg-amendment discipline.
- [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — canonical 13-table results-summary format.
- [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) — §4.1 drawdown-constrained Kelly sizing primitive (wrapped by §D-2 adapter); §5 K-1..K-8 kill-switch enumeration (extended to runtime per §D-1).
- [ADR-0018](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — §D-3 BOCD batch primitive (wrapped by §D-4 live-state-machine adapter).
- [ADR-0023](ADR-0023-metals-energy-futures-substrate-expansion.md) — metals/energy substrate (MGC + SIL + MCL added to cost model per §D-3).
- [ADR-0024](ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) — K-1..K-8 / FM-1..FM-5 / risk-of-ruin demoted to opt-in (§D-2 / §D-3 / §D-4); ADR-0025 implements the runtime tooling for the opt-in adoption path.
- [src/skie_ninja/backtest/kill_switch_validation.py](../../src/skie_ninja/backtest/kill_switch_validation.py) — post-hoc validator preserved verbatim per ADR-0013 §4.1.
- [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) — H050 baseline cost model preserved verbatim.
- [src/skie_ninja/backtest/costs/futures_orb_v1.py](../../src/skie_ninja/backtest/costs/futures_orb_v1.py) — H052a ORB cost model preserved verbatim.
- [src/skie_ninja/inference/bocd.py](../../src/skie_ninja/inference/bocd.py) — batch BOCD primitive preserved verbatim.
- [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py) — ADR-0017 §4.1 sizing primitive preserved verbatim (wrapped by §D-2 adapter).
- [config/instruments.yaml](../../config/instruments.yaml) — fee schedule source for the multi-instrument cost model.
- [docs/audits/audit_trail_2026-05-18_adr-0025-abandonment-infrastructure.md](../audits/audit_trail_2026-05-18_adr-0025-abandonment-infrastructure.md) — this ADR's audit-remediate-loop trail.

## Empirical justification

The empirical basis is the conjunction of (a) Phase O.10 v2 KPI emissions surfacing catastrophic max-drawdown trajectories on the H062 v2 + H055 v2 C5 cells that no entry-time mechanism prevented; (b) the 2026-05-18 cross-orchestrator audit documenting the 5-file inline-duplication of the current-equity-rebase logic; (c) the [ADR-0023](ADR-0023-metals-energy-futures-substrate-expansion.md) substrate expansion adding three symbols (MGC, SIL, MCL) not covered by the existing cost models; (d) the structural gap between the [bocd.py](../../src/skie_ninja/inference/bocd.py) batch primitive and a live-pause state machine for production trading. Each is independent evidence; together they constitute the load-bearing motivation for this ADR.

The CLAUDE.md user-global §"Evidence Hierarchy" is preserved unchanged: peer-reviewed → official docs → professional standards → vetted forums → reproduction. The ADR-0025 framework draws from peer-reviewed primary sources (Adams-MacKay 2007 BOCD; GISW 2007 MPPM; Kelly 1956 log-optimal sizing; Lo 2004 AMH) plus practitioner sources (Faith 2007 Turtle; López de Prado 2018 AFML; Vince 1990; Wilder 1978; Tharp 1998) each tagged per CLAUDE.md §"Practitioner-source-tag" convention.

ADR-0025 is the canonical reference for the SKIE-Universe project's abandonment-trigger infrastructure layer from 2026-05-18 forward. It implements the opt-in runtime tooling authorized by ADR-0024 §D-2 / §D-3 / §D-4 without re-introducing mandatory inheritance; consolidates duplicated sizing logic into a shared primitive; extends cost-model coverage to the post-ADR-0023 substrate; and provides a hard-pause state machine on top of the batch BOCD primitive for production trading.
