---
title: P1-H050-SPLIT-PARAMS — pre-reg date-derived walk-forward split sizes
date: 2026-04-24
worktree: claude/thirsty-hawking-472887
artifact: scripts/run_walk_forward.py
ticket: P1-H050-SPLIT-PARAMS (Option-B Cell-I code blocker #1 of 4)
audit_protocol: ~/.claude/skills/audit-remediate-loop (3-round cap)
verdict: exit-loop-with-residuals (residuals tracked under follow-ups)
---

# Audit trail — P1-H050-SPLIT-PARAMS

## Context

**Pre-registration deviation closed.** [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml) §data declares:

| Window | Start | End |
|---|---|---|
| train | 2015-01-01 | 2022-12-31 |
| val   | 2023-01-01 | 2023-12-31 |
| test  | 2024-01-01 | 2025-12-31 |

Pre-Round-1 [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) hard-coded `initial_train = max(200, n // 3)` and `test_size = max(50, n // 10)`. Row-count fractions are dataset-cardinality-driven; fold geometry would change with every backfill. Resolved per memo F-3-3 ([memo_h050-aggregation-rule_2026-04-24.md](../research_notes/memo_h050-aggregation-rule_2026-04-24.md)).

## Round 1 — initial fix

**Produced** (commit candidate, not yet committed): extended `RunConfig` with `train_start/train_end/val_start/val_end/test_start/test_end` (UTC-aware `pd.Timestamp`), added `_parse_window` helper with end-inclusive semantics (`end_day + 1d - 1ns`), filtered `sym_frame` to `[train.start, test.end]` on real-data runs only, derived `initial_train = (ts ≤ train_end).sum()` and `test_size = (val_start ≤ ts ≤ val_end).sum()`. Dry-run kept row-fraction fallback.

**Audited.** Three parallel sub-agents (quant-auditor + literature-check + reproducibility-verifier).

### Round-1 findings (12 total)

| ID | Severity | Category | Issue | Disposition |
|---|---|---|---|---|
| F-1-1 | major | method | Bar-count cadence drifts from leap-year calendar boundaries; cannot guarantee exactly N OOS folds | Round-2: warn + follow-up `P1-H050-CALENDAR-ANCHORED-SPLITTER` |
| F-1-2 | major | method | Fold-0 OOS coincides with VAL window — conflates val (HP-selection) and test (OOS measurement) | Round-2: bump initial_train to `(ts ≤ val.end).sum()`; val now in-sample, fed to inner CV (P1-H050-INNER-CV) |
| F-1-3 | minor | parameter | Nanosecond subtraction is sub-resolution vs `Datetime("us", "UTC")` schema | Deferred — non-blocking |
| F-1-4 | minor | reporting | `sym = "ES"` hardcode silently drops NQ | Out of scope; `P1-H050-UNIVERSE-ES-ONLY` already tracked |
| F-1-5 | minor | reporting | Split-size source not echoed to metrics_summary | Round-2: added `split_size_source`, `initial_train_size`, `test_size`, `step_size`, `pre_reg_envelope` |
| F-1-6 | minor | numerical | No upper-bound check `initial_train + test_size <= n` | Round-2: added `test_window_bars > 0` precondition |
| L-1 | minor | citation | Memo §6 references "three paradigms in Chapter 11" — actually Chapter 12 | Memo r4 already corrected (residual stylistic) |
| L-2 | verified | citation | Bailey & López de Prado 2014 DSR DOI verified | — |
| L-3 | minor | citation | Code comment lacks Pesaran-Timmermann 1995 / Bergmeir-Hyndman-Koo 2018 / AFML §12.2 references | Round-2: cited inline |
| L-4 | minor | citation | "Calendar-anchored over cardinality-anchored" claim lacks Tier-1 source | Round-2: cited Bailey-LdP 2014 + AFML §11.2 |
| L-5 | minor | citation | "Non-overlapping OOS folds" claim is engine-behavior, not literature | Cited Pesaran-Timmermann 1995 §III rolling/recursive distinction |
| R-3 | major | reproducibility | `config_resolved_sha256` not populated in `RunContext` call | Round-2: hash raw bytes BEFORE `yaml.safe_load`; threaded through |
| R-4 | major | reproducibility | `dataset_checksums` binds full ingest hash, not post-filter slice | Round-2: `ctx.add_dataset_checksum("h050_pre_reg_filtered_es", frame_sha256(...))` |
| R-5 | minor | reproducibility | `_load_output_sha256` uses lexical filename ordering | Deferred — non-blocking |
| R-6 | minor | reproducibility | Mixed pathlib + glob string | Deferred — non-blocking |
| R-7 | verified | reproducibility | All RNG seeds pinned to `cfg.random_seed` / `cfg.lgb_seed` | — |

## Round 2 — remediation + audit

**Remediated.** F-1-1, F-1-2, F-1-5, F-1-6, L-3, L-4, L-5, R-3, R-4 closed in single edit pass (see code-comment ID anchors at [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py)). Smoke test [tests/unit/test_orchestrator_smoke.py](../../tests/unit/test_orchestrator_smoke.py) passed (1 passed in 99.58s).

**Round-3 audit findings (6 majors)** — same protocol, focused on Round-2 deltas.

| ID | Severity | Category | Issue | Disposition |
|---|---|---|---|---|
| F-3-1 | major | leakage | Positional `initial_train = (ts ≤ val.end).sum()` cannot guarantee fold-0 first OOS bar lands ≥ `cfg.test_start` under val-window compression (holidays/halts) | Round-3: added calendar-anchor assertion at engine boundary |
| F-3-2 | major | reproducibility | `with_model_hash` ordering vs `add_dataset_checksum` mutation not verified | Round-3: verified `with_model_hash = dataclasses.replace(log, model_hash=...)` (see [src/skie_ninja/utils/reproducibility.py:232](../../src/skie_ninja/utils/reproducibility.py)) preserves `dataset_checksums`; inline doc-cited |
| F-3-3 | major | verification-gap | `config_resolved_sha256` plumbing not asserted at runtime | Round-3: added byte-identity post-`__enter__` assertion |
| F-3-4 | major | parameter | `max(1, ceil(...))` and `max(step_size, 1)` clamps mask config errors | Round-3: dropped clamps; rely on earlier preconditions |
| F-3-5 | major | reproducibility | Function-scope `from skie_ninja.utils.hashing import frame_sha256` only reached on real-data path | Round-3: hoisted to module-top imports |
| F-3-6 | major | leakage | `pre_reg_envelope` written to metrics is configured calendar; no `realized_envelope` showing actual ts_event min/max per fold | Round-3: added `realized_envelope_per_fold` to metrics_summary |

## Round 3 — final remediation

All 6 Round-3 majors closed. Smoke test re-run (1 passed in 113.06s).

## Residual risk

- **Smoke-test gap (R-1 from Round-3 repro audit, surfaced as follow-up):** dry-run path does not exercise `config_resolved_sha256` round-trip nor the `h050_pre_reg_filtered_es` checksum write. The runtime `assert ctx.log.config_resolved_sha256 == cfg.config_resolved_sha256` and the calendar-anchor `ValueError` are the standing guards. Filed `P1-H050-SPLIT-DATE-BINDING-TEST` to add a real-data fixture-based regression test.
- **Calendar drift:** bar-count cadence still drifts ~1 trading day per leap year vs perfect calendar boundaries. Surfaced via `expected_n_folds` mismatch warning + `realized_envelope_per_fold` in metrics. Filed `P1-H050-CALENDAR-ANCHORED-SPLITTER` for date-aware splitter.
- **Synthetic panel coverage:** dry-run cannot honour pre-reg envelope (5000-bar 1-min panel ≪ 11-yr window). Filed `P1-H050-SYNTHETIC-PANEL-PRE-REG-COVERAGE`.

## Citations chain (verified)

- López de Prado, *Advances in Financial Machine Learning* (Wiley 2018), ISBN 978-1-119-48208-6. Chapter 11 = "The Dangers of Backtesting"; §11.2 = selection-bias warnings; Chapter 12 = "Backtesting through Cross-Validation" (§12.2 = walk-forward; §12.3 = combinatorial-purged-CV).
- Bailey & López de Prado 2014, "The Deflated Sharpe Ratio", *Journal of Portfolio Management* 40(5):94-107, [doi:10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094).
- Pesaran & Timmermann 1995, "Predictability of Stock Returns: Robustness and Economic Significance", *Journal of Finance* 50(4):1201-1228, [doi:10.1111/j.1540-6261.1995.tb04055.x](https://doi.org/10.1111/j.1540-6261.1995.tb04055.x). §III rolling vs recursive estimation.
- Bergmeir, Hyndman & Koo 2018, "A note on the validity of cross-validation for evaluating autoregressive time series prediction", *Computational Statistics & Data Analysis* 120:70-83, [doi:10.1016/j.csda.2017.11.003](https://doi.org/10.1016/j.csda.2017.11.003).
- Varma & Simon 2006, "Bias in error estimation when using cross-validation for model selection", *BMC Bioinformatics* 7:91, [doi:10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91). (Cited for the still-pending P1-H050-INNER-CV.)

## Follow-ups created/updated this round

- `P1-H050-CALENDAR-ANCHORED-SPLITTER` — calendar-anchored splitter eliminating bar-count drift across leap-year boundaries.
- `P1-H050-SPLIT-DATE-BINDING-TEST` — regression test asserting `config_resolved_sha256` + `h050_pre_reg_filtered_es` survive into the persisted ReproLog on real-data runs.
- `P1-H050-SYNTHETIC-PANEL-PRE-REG-COVERAGE` — synthetic panel that spans the pre-reg envelope at coarse frequency for date-binding regression coverage.

## Verdict

**exit-loop-with-residuals.** 3-round audit cap reached. All critical/major findings remediated in-loop; minors deferred as non-blocking; residuals tracked under named follow-ups.
