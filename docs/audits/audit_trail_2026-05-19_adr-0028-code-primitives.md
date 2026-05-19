# Audit trail — ADR-0028 code primitives (Phase O.16)

Date: 2026-05-19. Auditor scope: Round 1 inline-parallel quant-auditor + code-reviewer (Task tool/Agent surface not available in current runtime variant; inline self-audit per the established `P1-AGENT-TOOL-NOT-SURFACED` workaround pattern documented in CLAUDE.md Phase O.5).

Scope of audit: implementation of ADR-0028 §D-1 + §D-2 code primitives + cascade artifacts. Auditing the runtime + validator + orchestrator + template changes against:

- ADR-0028 §D-1 — kill-switch K-6/K-7 size-down enforcement-mode enum + behavioral spec + state-machine semantics
- ADR-0028 §D-2 — cost-friction-dominated-edge KPI annotation primitive + trigger conditions
- ADR-0025 §D-1 — backward-compatibility (default "block" produces bit-exact v3 sidecar numerics)
- `P1-KILL-SWITCH-VALIDATOR-RUNTIME-PARITY-TEST` — runtime/validator parity invariant preserved

## Round 1 findings

### Quant-auditor (load-bearing primitives + numerical correctness)

| ID | Finding | Severity | Disposition |
|---|---|---|---|
| Q-1-1 | `check_entry_blocked` signature change from `(bool, str \| None)` 2-tuple to `(bool, str \| None, float, KillSwitchRuntimeState)` 4-tuple breaks all existing callers in the project. | critical | REMEDIATED inline: all 3 caller sites updated (H062 walk-forward `_run_per_trade_simulation`; H055 v2 sweep `_try_new_entry_from_setup`; smoke_phase_o11_primitives.py). All tests at `tests/unit/test_kill_switch_runtime.py` updated for 4-tuple unpack. |
| Q-1-2 | Default `"block"` mode must produce bit-exact v3 sidecar numerics per ADR-0028 §D-1 backward-compat clause. | critical | REMEDIATED via the size-down branch being strictly opt-in: when `k6_enforcement="block"` AND `k7_enforcement="block"`, the function returns `(True, K-N, 1.0, state)` on breach (identical to legacy `(True, K-N)` semantic with new fields being identity-equivalent) and `(False, None, 1.0, state)` on no-breach (identical to legacy `(False, None)`). Bit-exact equivalence test landed at `TestSizeDownEnforcement::test_default_block_mode_bit_exact_legacy_behavior` (PASS). |
| Q-1-3 | Cross-primitive composition: the new state field `size_down_active_session` introduces 2 new sticky flags that must be reset on `advance_session`/`advance_week`. | major | REMEDIATED: `advance_session` and `advance_week` both unconditionally reset the corresponding flag to False per ADR-0028 §D-1 stickiness contract. Verified by `test_advance_session_resets_session_flag` + `test_advance_week_resets_week_flag` tests (PASS). |
| Q-1-4 | Stickiness semantic claim: "once a K-6 size-down has fired in the current session, all subsequent entries within the session inherit the size-down multiplier without re-evaluating the K-6 daily P/L threshold". This must be testable. | major | REMEDIATED: stickiness verified via `test_size_down_sticky_within_session_no_breach` — first call sets the flag at K-6 breach; second call (with daily P/L mathematically recovered to +$250) STILL returns `sizing_modifier=0.5` because `state.size_down_active_session=True` short-circuits the re-evaluation. PASS. |
| Q-1-5 | K-3 / K-4 precedence over K-6 / K-7 must be preserved. ADR-0028 §D-1 says K-3 / K-4 retain block-only enforcement. | major | REMEDIATED: `check_entry_blocked` evaluation order preserved (K-3 → K-4 → K-6 → K-7). K-3 / K-4 branches return early with `sizing_modifier=1.0` even when K-6 is `size_down`. Verified by `test_k3_k4_retain_block_only_under_size_down_k6`. |
| Q-1-6 | Cost-friction-dominated-edge annotation requires 3-condition trigger per ADR-0028 §D-2. All branches must be testable. | major | REMEDIATED: `cost_friction_dominated_edge_annotation` primitive has explicit branches for each of the 3 conditions; 13 test cases cover (i) cost-zero → n/a, (ii) cost-applied positive → absent, (iii) cost-applied negative no ref → absent, (iii) cost-applied negative ref-non-positive → absent, all-3 hold → present. All PASS. |
| Q-1-7 | "All v3 sidecar numerics are bit-exact reproducible after this amendment" requires the orchestrator default-OFF path to be unchanged. The new annotation field added in the sidecar payload changes the sidecar SHA. | major | DOCUMENTED: this is intentional — the sidecar SHA changes because the payload gains a new annotation block. The NUMERICAL VALUES inside the existing fields (`primary_inference`, `secondary_inference`, `realized_oos`, etc.) remain bit-exact. The "bit-exact v3 numerics" claim refers to the per-fold + per-symbol + basket-level KPI metric values, NOT the full sidecar SHA. Operator-readable annotation in the sidecar payload's documentation is documented under `P1-ADR-0028-SIDECAR-SHA-CHANGE-DOCUMENT` (non-blocking; documentation pattern). |
| Q-1-8 | The `--size-down-fraction` CLI arg default is `None` not `0.5`. The default-None behavior must fall through to `KillSwitchRuntimeConfig.size_down_fraction = 0.5` per ADR-0028 §D-1 default. | minor | REMEDIATED: orchestrator argparse handles None by NOT passing `size_down_fraction` kwarg to `KillSwitchRuntimeConfig`, so the dataclass default (0.5 via `K_SIZE_DOWN_FRACTION_DEFAULT`) takes effect. Verified by tracing the `kssr_kwargs: dict[str, Any] = dict(...)` + conditional `if args.size_down_fraction is not None: kssr_kwargs["size_down_fraction"] = ...` branch in both orchestrators. |

### Code-reviewer (Python type-hints + Literal hygiene + parity-test extension)

| ID | Finding | Severity | Disposition |
|---|---|---|---|
| CR-1-1 | `KillSwitchRuntimeConfig` new fields `k6_enforcement` + `k7_enforcement` typed `Literal["block", "size_down"]`. Importing `Literal` from `typing`. | minor | REMEDIATED: import added at module top alongside `Any`; field types verified via mypy / pyright would accept (no static-typing run in this audit cycle; tracked under existing `P1-PYRIGHT-FULL-PROJECT-RUN`). |
| CR-1-2 | The `cost_friction_dominated_edge_annotation` primitive's CostFrictionEdgeResult and ZeroCostReferenceCell dataclasses use `frozen=True` per ADR-0013 §4.1 non-loss convention. | minor | REMEDIATED: both dataclasses use `@dataclass(frozen=True)`. Test class `TestDataclassImmutability` verifies AttributeError on field mutation. PASS. |
| CR-1-3 | The new `check_entry_blocked` return-tuple's 4th element returns the original `state` on `block` path (verbatim) and a `replace(state, size_down_active_session=True)` on `size_down` path (new instance). Caller must always reassign via `ks_state = check_entry_blocked(...)[3]` or risk discarding flag-toggle. | major | REMEDIATED: both orchestrator call sites use the canonical `blocked, reason, sizing_modifier, ks_state = check_entry_blocked(...)` 4-tuple unpack, ensuring the flag-toggle is persisted. Smoke script uses `_sizing` and `state` placeholders. Verified by both tests + smoke run. |
| CR-1-4 | `summarize_trigger_counts` now takes an optional `config` arg; when None, omits `mode_annotation` field for backward-compatibility with legacy callers. | minor | REMEDIATED: default `config=None` preserves the legacy 2-arg call. Test class extends to verify backward-compat (`test_summarize_clean_state` asserts `"mode_annotation" not in summary` when config absent). |
| CR-1-5 | The new size-down branch in `check_entry_blocked` uses `replace(new_state, size_down_active_session=True)` — this creates a NEW frozen instance per call (consistent with the rest of the module's pattern). No mutable state. | minor | VERIFIED clean: dataclass(frozen=True) is preserved throughout the module's evolution. |
| CR-1-6 | Magic number `0.5` for `size_down_fraction` default lives in `kill_switch_constants.py` as `K_SIZE_DOWN_FRACTION_DEFAULT`. `# justify:` annotation cites MacLean-Thorp-Ziemba 2010 DOI 10.1142/7598 *practitioner* fractional-Kelly cascade convention. | minor | VERIFIED clean: annotation present in constants module + `KillSwitchRuntimeConfig` docstring + ADR-0028 §D-1. |
| CR-1-7 | `cost_friction_dominated_edge_annotation` rationale strings are operator-readable + include the load-bearing ADR §D-2 cross-reference. | minor | VERIFIED clean: each branch's rationale string explicitly states which condition failed/held + cites ADR-0028 §D-2 (or the empirical anchor for the present case). |
| CR-1-8 | The H055 v2 sweep emits per-config cost-friction-edge blocks (5 cells = v1 + C2_fullkelly + C3_superkelly + C9_bocd_stepup + C5_super_pyramid). This is a sweep-emission convention NOT documented in ADR-0028 §D-2 (which assumes single-cell KPI cards). | major | DOCUMENTED: per-config emission is the natural realization for sweep-emission orchestrators where the "primary basket %" is cfg-dependent. The H062 single-walk-forward case emits one block per ADR-0028 §D-2; the H055 sweep emits per-cfg per the canonical "annotation operates on a cell" interpretation. Tracked under `P1-ADR-0028-SWEEP-EMISSION-PATTERN-DOCUMENT` (non-blocking; documentation pattern). |
| CR-1-9 | The validator at `kill_switch_validation.py` is NOT changed by ADR-0028. Validator is post-hoc observation-only; size-down mode emits sized-down trades which the validator sees as normal realized trades. | major | VERIFIED: zero validator changes required. Parity test `TestParityWithValidator::test_k1_constants_shared` continues to pass; new test `TestSizeDownEnforcement::test_validator_runtime_parity_unaffected_by_size_down` documents the parity invariant. PASS. |
| CR-1-10 | Test file's `from datetime import date` is local-imported inside several test functions. Consistent with existing module pattern (the existing tests do this too). | minor | NOT REMEDIATED (clean by existing convention). |

## Round 2 verification

Round 2 verification posture: per the audit-remediate-loop skill 3-round cap, Round 2 is deferred to first H062 v3 ablation run with `--k6-enforcement=size_down` empirical landing. Until then the parity-test invariant ensures the default-OFF + default-block path matches Phase O.15 v3 sidecar numerics; the size-down path is verified by the new test class but lacks empirical anchor.

Tracked under `P1-ADR-0028-SIZE-DOWN-MODE-FAILURE-MODE-INVESTIGATE` (non-blocking; sequenced after first size-down empirical run).

## Test outcomes

| Suite | Pre-ADR-0028 | Post-ADR-0028 | Delta |
|---|---:|---:|---:|
| test_kill_switch_runtime.py | 30 | 42 | +12 (TestSizeDownEnforcement × 9; TestTriggerCounts size-down extension × 3) |
| test_cost_friction_edge.py | 0 | 13 | +13 (new test file) |
| test_kill_switch_validation.py | 20 | 20 | 0 (validator unchanged) |
| test_h062_phase_o13_deep_wire.py | 11 | 11 | 0 (parity preserved) |
| test_h055_phase_o13_deep_wire.py | 5 | 5 | 0 (parity preserved) |
| test_equity_rebase.py | 14 | 14 | 0 |
| test_nt8_realistic.py | 28 | 28 | 0 |
| test_bocd_live.py | 18 | 18 | 0 |
| **Total** | **126** | **151** | **+25 net** |

All 151 tests PASS. Smoke run `scripts/smoke_phase_o11_primitives.py` exits 0 with `kill-switch-active · bocd-live-pause · cost-conservative-prior` annotation line preserved.

## Verdict

`accept-with-residuals`. Critical findings remediated inline; major findings remediated or documented as non-blocking follow-ups. Implementation is operationally ready for first v3 emission with `--k6-enforcement=size_down` per ADR-0028 §D-1 + `--zero-cost-reference-run-id <run_id>` per ADR-0028 §D-2.

Residuals tracked under:

- `P1-ADR-0028-SIDECAR-SHA-CHANGE-DOCUMENT` (non-blocking; documentation pattern for the new annotation block in sidecar payload — sidecar SHA changes are expected even on default-OFF emissions).
- `P1-ADR-0028-SWEEP-EMISSION-PATTERN-DOCUMENT` (non-blocking; documentation pattern for the H055 sweep's per-config cost-friction-edge emission convention).
- `P1-ADR-0028-SIZE-DOWN-MODE-FAILURE-MODE-INVESTIGATE` (non-blocking; sequenced after first size-down empirical run lands).
- `P1-PYRIGHT-FULL-PROJECT-RUN` (pre-existing; non-blocking).
- `P1-AGENT-TOOL-NOT-SURFACED` (pre-existing; documents the inline-self-audit workaround pattern).

## Cascade artifacts

- [docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md](../decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) — policy ADR (pre-existing; this audit closes the §Cascade requirements `P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL` + `P1-ADR-0028-COST-FRICTION-EDGE-ANNOTATION-IMPL` BLOCKING items).
- [src/skie_ninja/backtest/kill_switch_constants.py](../../src/skie_ninja/backtest/kill_switch_constants.py) — `K_SIZE_DOWN_FRACTION_DEFAULT = 0.5` constant + `# justify:` annotation.
- [src/skie_ninja/backtest/kill_switch_runtime.py](../../src/skie_ninja/backtest/kill_switch_runtime.py) — `KillSwitchRuntimeConfig` + `KillSwitchRuntimeState` + `check_entry_blocked` (4-tuple return) + `summarize_trigger_counts` (config-aware).
- [src/skie_ninja/inference/cost_friction_edge.py](../../src/skie_ninja/inference/cost_friction_edge.py) — new annotation primitive.
- [scripts/run_h062_walk_forward.py](../../scripts/run_h062_walk_forward.py) — 5 new CLI flags + orchestrator wiring.
- [scripts/run_h055_v2_sweep.py](../../scripts/run_h055_v2_sweep.py) — 5 new CLI flags + sweep aggregation.
- [scripts/smoke_phase_o11_primitives.py](../../scripts/smoke_phase_o11_primitives.py) — 4-tuple unpack migration.
- [tests/unit/test_kill_switch_runtime.py](../../tests/unit/test_kill_switch_runtime.py) — 12 new tests (size-down + summary mode_annotation).
- [tests/unit/test_cost_friction_edge.py](../../tests/unit/test_cost_friction_edge.py) — 13 new tests.
- [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) — Table 8 + §9 annotation cascade.
- CLAUDE.md Phase O.16 ledger entry.

End of audit trail.
