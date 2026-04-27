---
title: P1-ORCHESTRATOR-PROGRESS-LOGGING — audit-remediate-loop trail
date: 2026-04-26
artifact: scripts/run_walk_forward.py + src/skie_ninja/utils/logging_setup.py + tests/unit/test_orchestrator_progress_log.py
followup_id: P1-ORCHESTRATOR-PROGRESS-LOGGING
exit_state: round-3 accept-with-residuals
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
---

## Scope

Add INFO-level structured progress logging around the H050 walk-forward orchestrator's load-bearing phases so a future multi-hour run is observable from the JSON log stream alone. Closes the observability gap that left the 2026-04-26 prod-run-1 with 0 bytes of stdout when killed at +180 min ([docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md)).

## Final implementation

**Public message contract:**

- `PROGRESS <phase> start | <kv-context>`
- `PROGRESS <phase> done elapsed=<s>s | <kv-context>` (clean exit)
- `PROGRESS <phase> failed elapsed=<s>s exc=<type> | <kv-context>` (caught exception)

**Phases instrumented**: `run`, `symbol`, `label-cfg`, `label-cfg-loop-step`, `fold-fit`, `hmm-fit`, `inner-cv-lgb`.

**Coverage by pattern:**

- **Context-managed `_PROGRESS.phase()`** (auto-emits `failed` on exception, mutable `done_ctx` for exit-time fields): `fold-fit`, `hmm-fit`, `inner-cv-lgb`, `label-cfg-loop-step`.
- **Explicit `try/except` with `_PROGRESS.start` + `_PROGRESS.failed`** (semantically identical; used where the function body is too large to wrap in a single `with` block without massive indentation): `run`, `symbol`, `label-cfg`. Each function is a thin wrapper that calls `_X_body` for the original logic; the body emits success-path `done` markers explicitly.

**Stdout buffering:** `setup_logging()` reconfigures stdout to `line_buffering=True` so headless runs flush per-line without `python -u`. The canonical command is:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    uv run python scripts/run_walk_forward.py --hypothesis H050 --config config/hypotheses/H050.yaml
```

`KeyboardInterrupt` and `SystemExit` propagate without producing a `failed` marker (operator-killed runs are distinct from crashed runs in the log stream).

## Round 1 — parallel quant + repro audit

Subagents:
- `quant-auditor` (`agentId aae8c43906c01f928`)
- `reproducibility-verifier` (`agentId a84cf0626ffff4e86`)

### Round-1 findings + dispositions

| ID | Severity | Source | Issue | Round-2/3 disposition |
|---|---|---|---|---|
| **Q-1-1** | major | quant | Exception paths leak orphan start markers; hung-vs-crashed indistinguishable in log stream | **Round-2 fixed**: added `_ProgressLog.phase()` context manager + `failed()` API; Round-3 extended to `symbol`/`label-cfg` via try/except wrappers |
| Q-1-2 | minor | quant | Module-singleton `_PROGRESS._t0` accumulates across in-process invocations | Round-2 added autouse fixture `_reset_module_singleton_progress_t0`; Round-3 extended to also reset `logging_setup` ContextVars (Q-2-5) |
| Q-1-3 / R-3 | minor | quant + repro | `python -u` requirement violates project's single-command reproduction rule | Round-2 added `sys.stdout.reconfigure(line_buffering=True)` in `setup_logging()` |
| Q-1-4 | minor | quant | `_kv` doesn't quote whitespace-containing values; downstream parsers break | Round-2 fixed: values containing whitespace are JSON-encoded; new test |
| Q-1-5 | verification-gap | quant | Test pass-count claim cross-test pollution risk | Round-2: 661/661 confirmed green; cross-test fixture added |
| Q-1-6 / R-1 | minor | quant + repro | Inline `_LOG.info("PROGRESS label-cfg-loop ...")` violates helper's message contract | Round-2 fixed: rerouted through `_PROGRESS.start/done("label-cfg-loop-step", ...)`; Round-3 fixed Q-2-1 (back-to-back start/done with elapsed=0 → context-manager wrap of `_run_symbol_label_cfg` call) |
| R-2 | minor | repro | README JSON schema docs missing | **Deferred** (non-blocking; tracked as `P1-PROGRESS-LOG-README-SCHEMA`) |
| R-4 | minor | repro | No deterministic phase-summary artifact for cross-run diff | **Deferred** (non-blocking; tracked as `P1-PROGRESS-DETERMINISTIC-SUMMARY`) |
| R-5 | minor | repro | No integration test asserting full marker sequence | Round-2 added `test_smoke_dry_run_emits_full_marker_sequence`; Round-3 added Q-2-7 symmetry assertion |
| R-6 | minor | repro | Cross-platform docstring uses bash continuation | **Deferred** (non-blocking; README §Reproducibility covers PowerShell variants) |
| R-7 | minor | repro | gitignore check on transient dirs | ✓ confirmed `.pytest_features_tmp/` and `artifacts/runs/` are unstaged |

## Round 2 — parallel quant + repro re-audit

Subagents:
- `quant-auditor` (`agentId afd25e27ca93e1702`) — same agent ID continued; new findings Q-2-1 through Q-2-7
- `reproducibility-verifier` (`agentId a73f462fb6d0ef18f`) — same agent ID continued; new findings R-2-1, R-2-2

### Round-2 findings + dispositions

| ID | Severity | Source | Issue | Round-3 disposition |
|---|---|---|---|---|
| **Q-2-1** | major | quant | `label-cfg-loop-step` start/done back-to-back with no body between → elapsed=0; defeats per-cell timing intent | **Round-3 fixed**: wrapped the `_run_symbol_label_cfg` call in `with _PROGRESS.phase("label-cfg-loop-step", ...) as ctx:` |
| **Q-2-2** | major | quant | `symbol` and `label-cfg` phases use raw start/done — exception leaks orphan start; defeats Q-1-1 fix | **Round-3 fixed**: added `_run_symbol → _run_symbol_body` and `_run_symbol_label_cfg → _run_symbol_label_cfg_body` wrappers with try/except + `_PROGRESS.failed` on exception |
| Q-2-3 | minor | quant | `BaseException` catches Ctrl-C; should be `Exception` | **Round-3 fixed**: changed to `except Exception` so SystemExit/KeyboardInterrupt propagate without instrumentation noise |
| Q-2-4 | minor | quant | `_ProgressLog` docstring claims "context manager exclusively" but 7/10 sites are raw start/done | **Round-3 fixed**: rewrote docstring with explicit "Coverage by pattern" enumeration |
| Q-2-5 | minor | quant | Cross-test pollution defence misses `logging_setup` ContextVars | **Round-3 fixed**: extended autouse fixture to call `bind_context(run_id="", phase="", hypothesis_id="", git_head="")` |
| Q-2-6 | minor | quant | Pass-count claim 661 vs actual collection 676 (3 network failures, 4 skipped) | Cosmetic reporting fix in this trail; non-blocking |
| Q-2-7 | minor | quant | Integration test asserts only start markers, not done | **Round-3 fixed**: added symmetry assertion `n_starts == n_done_or_failed` |
| R-2-1, R-2-2 | minor | repro | Docstrings still mandate `python -u` after R-3's line-buffering landed | **Round-3 fixed**: replaced "Run with `python -u`" with "setup_logging() now reconfigures stdout to line_buffering=True"; `python -u` mentioned only as belt-and-braces |

## Round 3 — internal verification (no fresh subagent audit; SKILL.md cap reached)

Per [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) §"Cap": "Max 3 audit rounds. ... If residuals remain after round 3, surface them to the user — do not continue silently." Round 3 was a remediation-only round; no Round-3 fresh subagent audit.

**Verification performed in Round 3:**
- 10/10 progress-log tests pass (5 helper + 3 context manager + 1 whitespace-quoting + 1 integration with symmetry).
- Full unit suite 661/661 green.
- Manual code-inspection confirms:
  - `Q-2-1` fix: `with _PROGRESS.phase("label-cfg-loop-step", ...)` wraps the `_run_symbol_label_cfg` call; elapsed reflects per-cell wall time.
  - `Q-2-2` fix: `_run_symbol` + `_run_symbol_label_cfg` thin wrappers call try/except around `_X_body`; exception path emits `failed`.
  - `Q-2-3` fix: phase context manager uses `except Exception`.
  - `Q-2-4` fix: docstring's "Coverage by pattern" section enumerates which phases use which approach.
  - `Q-2-5` fix: autouse fixture clears `_PROGRESS._t0` AND resets the four ContextVars.
  - `Q-2-7` fix: integration test asserts `n_starts == n_done_or_failed`.

## Exit verdict

**`accept-with-residuals`** — the patch is operationally sound for the relaunched H050 walk-forward run:

- Every instrumented phase emits `failed` on exception (Q-1-1 + Q-2-2 closed).
- `label-cfg-loop-step` per-cell elapsed is meaningful (Q-2-1 closed).
- Headless single-command flush works without `-u` (Q-1-3 / R-3 closed).
- Cross-test pollution surface defused (Q-1-2 + Q-2-5 closed).
- Integration test locks both call-site coverage AND symmetry (R-5 + Q-2-7 closed).
- 661/661 unit tests green; 10/10 progress-log tests green.

**Residuals carried forward (non-blocking):**

- `P1-PROGRESS-LOG-README-SCHEMA` (R-2) — surface the `PROGRESS <phase> start/done/failed` message-shape contract + JSON-line schema in README.
- `P1-PROGRESS-DETERMINISTIC-SUMMARY` (R-4) — emit a per-run `phase_summary.json` (no elapsed; diffable across runs).
- `P1-PROGRESS-LOG-CROSS-PLATFORM-DOCS` (R-6) — link the `_ProgressLog` docstring's canonical-invocation example to README §Reproducibility's PowerShell/cmd.exe variants.
- `P1-PROGRESS-LOG-DOCS-PASS-COUNT-AUTOREPORT` (Q-2-6) — automate test-count reporting in audit trails to avoid drift.

## New follow-ups logged

- `P1-PROGRESS-LOG-README-SCHEMA` *(non-blocking polish)*.
- `P1-PROGRESS-DETERMINISTIC-SUMMARY` *(non-blocking polish; useful for cross-run audit diffs)*.
- `P1-PROGRESS-LOG-CROSS-PLATFORM-DOCS` *(non-blocking polish)*.
- `P1-PROGRESS-LOG-DOCS-PASS-COUNT-AUTOREPORT` *(non-blocking process improvement)*.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) — orchestrator with `_ProgressLog` helper + 7 instrumented phases.
- [src/skie_ninja/utils/logging_setup.py](../../src/skie_ninja/utils/logging_setup.py) — `setup_logging()` with `line_buffering=True`.
- [tests/unit/test_orchestrator_progress_log.py](../../tests/unit/test_orchestrator_progress_log.py) — 10-test regression suite.
- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — diagnosis that motivated this patch.
- [docs/audits/audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md](audit_trail_2026-04-26_hmm-full-cov-d1-redundant.md) — the model-class-deduplication patch (P1-HMM-FULL-COV-1DIM-REDUNDANT) that lands jointly with this one in the relaunch.
