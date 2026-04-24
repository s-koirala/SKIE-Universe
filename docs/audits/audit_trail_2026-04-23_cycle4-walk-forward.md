# Audit trail — Cycle 4: walk-forward engine + purged CV + leak canaries

**Date:** 2026-04-23
**Deliverable:** [src/skie_ninja/backtest/](../../src/skie_ninja/backtest/)
**Plan reference:** [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md) §Cycle 4
**Test result:** 399/399 unit tests green (79 new — 50 splits, 18 engine, 21 canaries).
**Loop:** `audit-remediate-loop` — 2 audit rounds required; exited clean after Round 2 majors remediated.

## Scope delivered

- [src/skie_ninja/backtest/splits.py](../../src/skie_ninja/backtest/splits.py) — `Fold`, `SplitSpec`, `walk_forward_split` (rolling/expanding), `purged_kfold_split` (AFML §7.4.3), `cpcv_split` (AFML Chapter 12 scaffold — full path-reconstruction tracked as `P1-BACKTEST-CPCV`).
- [src/skie_ninja/backtest/engine/walk_forward.py](../../src/skie_ninja/backtest/engine/walk_forward.py) — `WalkForwardEngine` orchestrator, `FoldRecord`, `WalkForwardResult`, `roll_up_model_hashes`, `write_run_ledger` / `read_run_ledger` / `ledger_path_for`, `_ledger_schema` (dtype-validated parquet round-trip).
- [src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py) — `LookAheadLeakError`, `assert_fold_boundary_invariant` (canary a, monotonicity-checked), `assert_purge_covers_label_horizon` (canary b), `FitCallObserver` (canary c declared-index form) + `TracingArray` (canary c capability-proxy form).
- Three test files: [tests/unit/test_backtest_splits.py](../../tests/unit/test_backtest_splits.py), [tests/unit/test_backtest_walk_forward.py](../../tests/unit/test_backtest_walk_forward.py), [tests/unit/test_leak_canaries.py](../../tests/unit/test_leak_canaries.py).

## Leak-canary status

All three canaries actively catch an injected leak (no dead canaries):

- **(a) Future-return feature in training row** — `assert_fold_boundary_invariant` compares `feature_timestamps[train_idx]` against `observation_timestamps[test_idx.min()]`; engine gates every fold on this invariant BEFORE calling `fit_fn`. Monotonicity of `observation_timestamps` is enforced (Round 1 F-1-3).
- **(b) Label horizon exceeds purge** — `SplitSpec.__post_init__` raises at construction; `assert_purge_covers_label_horizon` mirrors the check for direct use.
- **(c) Fit consumes test-fold observations** — two complementary forms:
    - `FitCallObserver` journals indices *declared* to fit_fn.
    - `TracingArray` journals every `__getitem__` read against the underlying array, catching fit_fns that ignore their declared `train_idx` and read past it (Round 1 F-1-1).

## Audit rounds

### Round 1 — parallel triad (quant-auditor, literature-check, reproducibility-verifier)

| ID | Severity | Category | Disposition |
|---|---|---|---|
| F-1-1 | major | leakage (canary c dead) | **Remediated** — added `TracingArray` capability proxy + threat-model docstring on `FitCallObserver`. Test: `TestTracingArrayCanary::test_internal_peek_is_caught`. |
| F-1-2 | major | method (embargo placement) | **Remediated** Round 1 as overlap; **then reverted in Round 2 F-2-1** to stacked form matching mlfinlab `ml_get_train_times`. See Round 2 disposition. |
| F-1-3 | major | assumption (canary a monotonicity) | **Remediated** — `assert_fold_boundary_invariant` now raises `ValueError` on non-monotone `observation_timestamps`. Test: `test_non_monotone_observation_timestamps_raise`. |
| F-1-4 | major | method (walk-forward embargo over-accumulation) | **Remediated** — `_apply_embargo_walk_forward` now carries forward only the immediately-prior fold's embargo (not all prior folds'). Tests: `test_rolling_embargo_carves_next_fold`, `test_rolling_embargo_does_not_accumulate_across_folds`. |
| Literature — Bergmeir overreach | major | overreach | **Remediated** — docstring rewritten to match the paper's actual empirical conclusion (blocked CV is robust; walk-forward is one instance). Added Tashman 2000 as primary source for rolling-origin convention. |
| Literature — AFML §7.5 CPCV | major | wrong-eq-number | **Remediated** — all "AFML §7.5" references changed to "AFML Chapter 12 (Backtesting through Cross-Validation)". Cycle 6 will reconcile sub-section numbers against a physical copy. |
| Literature — Cawley §7 | major | misattribution / unverifiable section pointer | **Remediated** — dropped "§7" section pointer; added Varma & Simon 2006 as the canonical primary source for the nested-CV rule (Cawley & Talbot 2010 retained as secondary). |
| Repro — ledger dtype validation | major | reproducibility | **Remediated** — `read_run_ledger` now validates both column names AND dtypes via `_ledger_schema()` single-source-of-truth. Docstring UInt64 → Int64. Test: `test_read_rejects_dtype_drift`. |
| F-1-5, F-1-6, F-1-7, F-1-8, F-1-9, F-1-10, F-1-11 | minor | various | **Dropped per skill spec** (minors are not remediated unless the task specifically invites polish). Summary of each retained in the Round 1 section below. |
| Repro — pyproject lower-bound pins | minor | reproducibility | **Dropped** — `uv.lock` is tracked and authoritative; CI/repro runs use `uv sync --frozen`. |

### Round 2 — quant-auditor + reproducibility-verifier

Round 2 triggered by Round 1 major remediations that changed load-bearing behaviour.

| ID | Severity | Category | Disposition |
|---|---|---|---|
| F-2-1 | major | method (embargo placement — interpretation flip) | **Remediated** — embargo placement in `purged_kfold_split` + `cpcv_split` reverted to stacked form `[b_end + purge, b_end + purge + embargo)` matching the mlfinlab `ml_get_train_times` reference implementation (consistent with López de Prado 2018 Snippet 7.3's interval-extension construction). The Round 1 F-1-2 "overlap" interpretation was methodologically defensible but does not match what the sibling-repo CPCV + PBO prior-screen consumes. Audit trail records the ambiguity explicitly. |
| F-2-2 | major | leakage (TracingArray public `.array` bypass) | **Remediated** — renamed backing field to `_array` and placed the class on `__slots__` to block dynamic attribute injection. Full adversarial sandboxing is explicitly out-of-scope (documented in the class docstring); the threat model is honest-but-bug-prone fit_fns. |
| F-2-3, F-2-4, F-2-5, F-2-6 | minor | various | **Dropped per skill spec.** F-2-5 (walk-forward expanding-mode embargo semantics) is flagged in the README of [research/01_hypothesis_register/](../../research/01_hypothesis_register/) as a pre-registration declaration each H0xx hypothesis must make. F-2-6 (`__array__` copy kwarg for NumPy 2.0) partially addressed as part of F-2-2 refactor. |
| Repro Round 2 | — | — | `verdict: accept` — `{"findings": []}`; `_ledger_schema()` is the single source of truth, dtype comparison is object-level correct, all round-trip tests green. |

## Residual risk

1. **Embargo-placement interpretation** (F-2-1 / F-1-2) — the stacked-vs-overlap choice is methodologically debatable. The Cycle-4 implementation adopts the mlfinlab-compatible stacked form. Downstream H0xx hypotheses that re-run prior studies must verify their prior-art used the same convention (skfolio's CombinatorialPurgedCV differs).
2. **Walk-forward expanding-mode embargo semantics** (F-2-5) — applying only the immediately-prior fold's embargo is internally consistent for rolling mode (where older-fold embargoes fall outside the rolling window anyway) but is a semantic choice for expanding mode. H050's pre-registration should declare whether the expanding-training harness tolerates older-fold embargoes inside the growing training window.
3. **Primary-source PDF reads** — Bergmeir & Benítez 2012 (Elsevier paywall) and Cawley & Talbot 2010 (JMLR, open-access but WebFetch-unreadable) were verified through author-site summaries and JMLR abstracts rather than direct PDF reads. Cycle 6 will reconcile AFML section numbers against a physical Wiley 2018 copy.
4. **TracingArray threat model** — canary detects honest-but-bug-prone misuse, not adversarial attribute extraction. Documented in the class docstring.

## Follow-ups filed

- `P1-BACKTEST-CPCV` — full combinatorial-path reconstruction per AFML Chapter 12 (scaffolding in place; traversal implemented).
- `P1-BACKTEST-EMBARGO-MODE-ADR` — ADR to nail down stacked-vs-overlap embargo placement with primary-source citation.
- `P1-BACKTEST-TRACINGARRAY-STRICT` — optional strict-mode `TracingArray` that raises immediately on out-of-train-idx reads (vs journal-then-assert).

## Provenance

- Git HEAD at start: `7ba43bf428a7` (claude/thirsty-hawking-472887, dirty).
- `deps-sha`: `45cff4f379f9` (158 pkgs in `uv.lock`).
- Data dir manifest: 9 files, sha `0a2606358b8f`.
- Test runtime: 116 s wall (399 tests).
- Audit artifacts: this file.
