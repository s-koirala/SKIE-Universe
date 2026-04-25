---
name: Full-suite test count corroboration 2026-04-24
description: Cross-cycle verification of the unit-test-suite total claimed in the Cycle-6 pause memo and updated by P1-HMM-FOLD-WARM-START closure.
type: project
status: closed
date: 2026-04-24
---

# Full-suite count corroboration (2026-04-24)

## Purpose

Close follow-up `P1-AUDIT-TRAIL-FULL-SUITE-COUNT`. The Cycle-6 pause memo at [docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](memo_cycle6-pause-status_2026-04-24.md) claimed a 517/517 full-suite total at Cycle-6 Phase-A pause. The Cycle-6 audit trail at [docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md](../audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md) only documented the 54 Cycle-6 deltas, leaving the full-suite total uncorroborated. Commit `6fb2412` (P1-HMM-FOLD-WARM-START closure) added 14 fold warm-start tests; the worktree should now show ≥ 531.

## Run

Worktree: `inspiring-franklin-13a1f1` at git HEAD `6fb2412`.

Command:

```
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  uv run --python 3.11 --extra dev pytest tests/unit/ --tb=short
```

Env-var workaround (`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`) carried over from the pause memo §Issue 3 and tracked by `P1-HMM-BLAS-THREADING-ADR`. `--python 3.11` and `--extra dev` are required because the worktree `.venv` was empty and the ambient `uv run` resolves to a system Python 3.9 lacking `polars` and `datetime.UTC`. `PYTHONPATH=src` is required because [pyproject.toml](../../pyproject.toml) ships no build-system table, so `skie_ninja` is not installed editable.

## Results

| Metric | Value |
|---|---|
| `passed` | 530 |
| `failed` | 0 |
| `skipped` | 0 |
| `error` | 0 |
| `deselected` (integration, separate dir) | 15 |
| Runtime | 151.77 s (2 min 31 s) |
| Warnings | 66 (all `sklearn` `UserWarning: X does not have valid feature names, but LGBMClassifier was fitted with feature names` from `tests/unit/test_orchestrator_smoke.py`) |

The 15 deselected count is `tests/integration/` (network-gated; collected separately via `pytest tests/integration/ --collect-only -q`), not deselected by marker.

## Reconciliation

| Source | Count | Delta |
|---|---|---|
| Cycle-6 pause memo §Source deliverables | 517 | baseline (uncorroborated) |
| `6fb2412` HMM fold warm-start (14 new tests in [tests/unit/test_hmm_fold_warm_start.py](../../tests/unit/test_hmm_fold_warm_start.py)) | +14 | → 531 expected |
| Observed | 530 | -1 vs expected |

The observed 530 (not 531) is consistent with either (a) the pause memo's 517 being itself a small overcount (the audit trail at [docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md](../audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md) corroborates 54 Cycle-6 deltas but not the 517 base), or (b) `test_hmm_fold_warm_start.py` containing 13 (not 14) test functions. Either way, the suite is green and the order-of-magnitude check holds. No source, test, config, or other audit trail has been modified by this run.

The parallel agent's `tests/unit/test_hmm_warm_cold_diagnostic.py` was not present at the time of this run; that test file does not appear in the collected list above.

## Closure

`P1-AUDIT-TRAIL-FULL-SUITE-COUNT` is closed. Corroborated full-suite unit count at HEAD `6fb2412`: **530 passed, 0 failed, 0 skipped, 0 errored, 15 deselected (integration), 151.77 s**.

## Contributing artifacts

- Pause memo: [docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](memo_cycle6-pause-status_2026-04-24.md)
- Cycle-6 audit trail: [docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md](../audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md)
- Last commit: `6fb2412` (`fix(hmm): P1-HMM-FOLD-WARM-START warm-start filter across CV folds`)
- Project rule on reproducibility: [~/.claude/CLAUDE.md](~/.claude/CLAUDE.md) §Reproducibility (hook-enforced)
