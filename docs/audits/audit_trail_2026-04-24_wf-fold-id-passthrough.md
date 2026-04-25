---
title: P1-WF-ENGINE-FOLD-ID-PASSTHROUGH — audit-remediate-loop trail
date: 2026-04-24
artifact: WalkForwardEngine fold_id passthrough refactor + orchestrator wiring
followup_id: P1-WF-ENGINE-FOLD-ID-PASSTHROUGH
exit_state: round-1 accept (1 minor inline-resolved, 0 majors, 0 criticals)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
---

## Scope

Close `P1-WF-ENGINE-FOLD-ID-PASSTHROUGH` (residual F-1-4 of [audit_trail_2026-04-24_hmm-warm-cold-diagnostic.md](audit_trail_2026-04-24_hmm-warm-cold-diagnostic.md)). The brief: refactor [WalkForwardEngine](../../src/skie_ninja/backtest/engine/walk_forward.py) so that `fold_id` is propagated directly from each iteration's `Fold` instance into the caller-supplied `fit_fn` / `predict_fn`, eliminating the closure-mutated counter list workaround at [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) `_predict_fold` (commit `ec95c09`). The invariant the passthrough is meant to surface: the injected `fold_id` MUST equal `WalkForwardResult.fold_records[i].fold_id` for the same fold — both sourced from `Fold.fold_id` on the same `Fold` instance.

This is a pure plumbing refactor with no methodological surface. Behaviour for production walk-forward runs is byte-identical (warm-cold sidecar SHA256 unchanged for fixed seeds + data) — see F-1-5 below.

## Method-fidelity anchor

None. Refactor only.

## Round-1

### Implementation summary

- [src/skie_ninja/backtest/engine/walk_forward.py](../../src/skie_ninja/backtest/engine/walk_forward.py):
  - New module-level helper `_accepts_fold_id_kwarg(fn)`. Returns `True` iff the callable's `inspect.signature` declares a `fold_id` parameter (POSITIONAL_OR_KEYWORD or KEYWORD_ONLY) OR absorbs unknown kwargs via `VAR_KEYWORD`. Non-introspectable callables (builtins, certain C extensions) conservatively return `False` — engine skips injection rather than risking a `TypeError`. Collision with a caller-supplied `fold_id` in `fit_kwargs` / `predict_kwargs` is documented in the helper docstring as Python's standard "got multiple values" `TypeError` — name collision is a reserved-kwarg violation, not an engine bug.
  - `WalkForwardEngine.run` introspects `fit_fn` / `predict_fn` once at run entry (before the fold loop) to set `fit_accepts_fold_id` / `predict_accepts_fold_id` flags. Per-fold, the engine builds `fit_extra = {"fold_id": fold_id} if fit_accepts_fold_id else {}` (and the same for predict), then calls `fit_fn(train_idx, **fit_kwargs, **fit_extra)` / `predict_fn(fitted, test_idx, **predict_kwargs, **predict_extra)`.
  - `fold_id = int(fold.fold_id)` is sourced from the SAME `Fold` instance that downstream populates `FoldRecord.fold_id` via `_fold_record(fold, model_hash)`. Single source of truth; cannot desync (verified by `test_predict_fn_receives_fold_id_matching_fold_record` and `test_fit_fn_receives_fold_id_matching_fold_record`).
  - `FitFn` / `PredictFn` Protocol docstrings extended documenting the kwarg-tolerant injection contract.
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) `_predict_fold`:
  - Replaced `fold_id_counter: list[int] | None = None` with `fold_id: int | None = None`.
  - Diagnostic call site uses `fold_id` directly; fallback to `len(warm_cold_diagnostic.fold_records)` retained for the ad-hoc-invocation path (`fold_id is None` when called outside the engine, e.g. for inspection).
  - Removed the `counter[0] += 1` mutation block.
  - `run()` no longer instantiates `warm_cold_fold_counter = [0]`; `predict_kwargs` no longer carries `fold_id_counter`. The engine's introspection-driven injection picks up `fold_id` because `_predict_fold` declares it.
  - `_fit_fold` is unchanged — it does not require `fold_id`, and the engine's symmetric capability (verified independently by the test suite) does not mandate the orchestrator consume on the fit side.
- [tests/unit/test_backtest_walk_forward.py](../../tests/unit/test_backtest_walk_forward.py) — new `TestFoldIdPassthrough` class with 4 tests:
  - `test_predict_fn_receives_fold_id_matching_fold_record` — captures fold_ids via a stub `predict_fn(*, fold_id)`, asserts `seen_fold_ids == [r.fold_id for r in result.fold_records] == [f.fold_id for f in spec.folds]` (the chain documenting the invariant).
  - `test_fit_fn_receives_fold_id_matching_fold_record` — symmetric on the fit side.
  - `test_callable_without_fold_id_param_unchanged` — backward-compatibility regression: `lambda idx: "model"` and `lambda fitted, test_idx: ...` continue to work without TypeError.
  - `test_var_keyword_callable_receives_fold_id` — `**kwargs`-absorbing callables receive the injected fold_id.

### Round-1 self-audit findings

| ID | Severity | Lens | Location | Issue | Disposition |
|---|---|---|---|---|---|
| F-1-1 | minor | quant | `_accepts_fold_id_kwarg` docstring | The kwarg-tolerance heuristic does not document the failure mode where a caller pre-supplies `fold_id` via `fit_kwargs` / `predict_kwargs` — Python raises "got multiple values for keyword argument 'fold_id'" `TypeError`. This is the intended failure mode (name collision is a programming error against the engine's reserved-kwarg contract) but worth surfacing for callers. | Inline-resolved: docstring extended documenting `fold_id` as a reserved engine kwarg; no code change. |
| F-1-2 | n/a | quant | `inspect.signature` on Protocol-annotated callable | `fit_fn` is typed `FitFn` Protocol; `inspect.signature(fn)` operates on the runtime callable, not the Protocol annotation. No issue. | Verified — no change. |
| F-1-3 | n/a | quant | `_fit_fold` symmetry | `_fit_fold` does not consume `fold_id`; engine introspects and skips fit-side injection. Brief mandates the engine PROPAGATE `fold_id` symmetrically (verified by `test_fit_fn_receives_fold_id_matching_fold_record`); does not mandate every orchestrator function consume it. Adding an unused `fold_id` param to `_fit_fold` would be dead code. | Verified — no change. |
| F-1-4 | n/a | quant | Fold-id source invariance | Engine: `fold_id = int(fold.fold_id)` and `FoldRecord.fold_id = fold.fold_id` derive from the SAME `Fold` instance in the same iteration — single source. Cannot desync. | Verified — no change. |
| F-1-5 | n/a | repro | Warm-cold sidecar SHA256 stability | Old: counter increments 0,1,2,… in fold-iteration order. New: `Fold.fold_id` from `walk_forward_split` is 0,1,2,… in fold-iteration order (verified by the existing `test_one_record_per_fold`). Identical fold_id sequence → identical `WarmColdFoldRecord.fold_id` sequence → byte-identical sidecar JSON → identical SHA256 → identical `ReproLog.model_hash`. | Verified — no change. |
| F-1-6 | n/a | lit | Methodological citations | Pure refactor — no methodological surface. | Vacuously satisfied. |
| F-1-7 | n/a | repro | ReproLog / model_hash schema | Unchanged. The combiner `hashlib.sha256("ledger_rollup={H1};warm_cold_diag={H2}")` is byte-identical to pre-refactor; both component hashes derive from inputs that are unchanged for fixed seeds + data. | Verified — no change. |

### Test posture

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
PYTHONPATH=src uv run --python 3.11 --extra dev pytest tests/unit/ -q

552 passed, 66 warnings in 142.24s (0:02:22)
```

Pre-refactor baseline = 548 (from CLAUDE.md "Implemented infrastructure (as of 2026-04-23)" + `P1-AUDIT-TRAIL-FULL-SUITE-COUNT` closure). New count = 552 = 548 + 4 (the `TestFoldIdPassthrough` additions). No pre-existing test regressed.

Focused subset (engine + leak-canaries + warm-cold + fold-warm-start + orchestrator smoke) ran independently first to localise: `74 passed, 66 warnings in 71.11s`.

### Ruff posture

Touched files vs HEAD baseline:

| File | HEAD | Post-refactor | Δ |
|---|---|---|---|
| [src/skie_ninja/backtest/engine/walk_forward.py](../../src/skie_ninja/backtest/engine/walk_forward.py) | 4 | 4 | 0 |
| [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) | 31 | 31 | 0 |
| [tests/unit/test_backtest_walk_forward.py](../../tests/unit/test_backtest_walk_forward.py) | 7 | 7 | 0 |

Zero new ruff violations on touched files. Pre-existing PLC0415 violations inside `write_run_ledger` / `read_run_ledger` / `_ledger_schema` are out of scope for this follow-up.

## Exit decision

Exit Round-1 with `accept` verdict per [audit-remediate-loop](file:///C:/Users/skoir/.claude/skills/audit-remediate-loop/SKILL.md) §"Exit check": Round-1 has zero critical, zero major, one minor (F-1-1) inline-resolved, four verified-no-change items (F-1-2 through F-1-5), two vacuously-satisfied (F-1-6, F-1-7). Round-2 not warranted.

## Residual risk

1. **Reserved-kwarg name collision is a runtime, not a static, error.** A caller who passes `fold_id` through `fit_kwargs` / `predict_kwargs` for an unrelated purpose will get a `TypeError` at the first fold rather than a static analysis failure. The probability is low (no current call site pre-supplies it; the name is specific) but non-zero for future callers. Mitigations available if it becomes load-bearing: (a) `WalkForwardEngine.run` could pre-validate `fit_kwargs` / `predict_kwargs` for the reserved name and raise with a clear message before the fold loop; (b) move to a `FoldContext` dataclass-style payload (`predict_fn(fitted, test_idx, *, ctx: FoldContext)`) that namespaces all engine-injected values. Tracked as `P1-WF-ENGINE-RESERVED-KWARG-VALIDATION`.
2. **`inspect.signature` on `functools.partial`-wrapped callables.** `inspect.signature` correctly handles `partial`, but if a future caller hides `fold_id` behind a non-introspectable wrapper (e.g. a hand-rolled callable class without `__signature__`), the engine will silently skip injection. The diagnostic-fallback path (`fold_id is None` → `len(fold_records)`) absorbs this for the warm-cold case but other future consumers may not have a fallback. Tracked as `P1-WF-ENGINE-INTROSPECTION-FAILURE-WARN` if observed.

## Follow-ups added by this trail

- `P1-WF-ENGINE-RESERVED-KWARG-VALIDATION` — pre-validate `fit_kwargs` / `predict_kwargs` for the reserved `fold_id` name and raise with a clear message before the fold loop, replacing the runtime TypeError with a startup-time error.
- `P1-WF-ENGINE-INTROSPECTION-FAILURE-WARN` — emit a structured-log warning if `inspect.signature` fails on `fit_fn` / `predict_fn` so silent injection-skip is observable.

## Files changed

- [src/skie_ninja/backtest/engine/walk_forward.py](../../src/skie_ninja/backtest/engine/walk_forward.py) — new `_accepts_fold_id_kwarg` helper; `WalkForwardEngine.run` injects `fold_id` per fold via kwarg-tolerant introspection; `FitFn` / `PredictFn` Protocol docstrings extended.
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) — `_predict_fold` accepts `fold_id` directly; closure-mutated counter list removed.
- [tests/unit/test_backtest_walk_forward.py](../../tests/unit/test_backtest_walk_forward.py) — `TestFoldIdPassthrough` class with 4 tests covering fit-side injection, predict-side injection, backward compatibility, and `**kwargs` absorption.
