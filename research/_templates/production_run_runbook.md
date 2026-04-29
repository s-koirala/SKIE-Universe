---
title: <HXXX> production walk-forward runbook
date: <YYYY-MM-DD>
type: runbook
status: draft  # draft | live | superseded
hypothesis_id: <HXXX>
binds_to_adr: ADR-0011
runbook_schema_version: production_run_runbook_v1
adr_0011_revision: <commit-hash-of-binding-ADR-0011-commit>  # filled at instantiation
companion_design_doc: research/01_hypothesis_register/<HXXX>/design.md
companion_data_requirements: research/01_hypothesis_register/<HXXX>/data_requirements.md
---

# <HXXX> production walk-forward runbook

This runbook is a deliverable of pre-registration per [ADR-0011](../../docs/decisions/ADR-0011-production-walkforward-runbook.md). It is instantiated from this template and committed to `research/01_hypothesis_register/<HXXX>/production_run_runbook.md` *before* the first real-substrate launch. Smoke and dry-run launches do not require this runbook.

## 1. Hypothesis-context summary

| Field | Value |
|---|---|
| Hypothesis ID | <HXXX> |
| Tier | <Tier 2a / Tier 2b / Tier 3> |
| Pre-registered | <YYYY-MM-DD> |
| Universe | <ES / NQ / MES / MNQ / QQQ / pairs> |
| Train + val + test envelope | <YYYY-MM-DD → YYYY-MM-DD> |
| Substrate dataset(s) | <e.g. data/processed/vendor_legacy_1min_roll_adjusted/> |
| Substrate combined SHA256 | <hex> |
| Estimated runtime | <N hours> |
| Maximum acceptable runtime | <N hours> (sets `--max-runtime-s` argument) |
| Power requirement | per ADR-0004 (default 80% at α=0.05) |
| Inference convention | <arithmetic / log returns + aggregation rule> |

## 2. Preflight checklist (ADR-0011)

The 15 ADR-0011 gates. Each row records the operator's verification at first launch; subsequent re-launches inherit the verification unless a configuration change invalidates a row, in which case the row is re-verified and the runbook is re-committed.

### Tier 1 — Configuration validity

| # | Gate | Verification | Status | Evidence |
|---|---|---|---|---|
| 1 | HMM emission-dimensionality redundancy (**non-waivable**) | When `len(cfg.hmm.feature_columns) == 1` AND `len(set(cfg.hmm.covariance_type) - {"tied"}) >= 2`, model-class deduplication is required (or redundant types dropped to one). Verify deduplication path engaged in [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py); cross-link addendum if applicable. | <pass> | <commit / addendum link> |
| 2 | Hyperparameter-search budget feasibility | `n_draws × n_inner_folds × n_cfgs × n_outer_folds × per_fit_seconds_estimate ≤ (per_attempt_runtime_cap × max_attempts × 0.9)`. With current defaults (3 hr × 10 attempts) the budget ceiling is 27 hr. `per_fit_seconds_estimate` is read from gate 2b's microbench artifact. | <pass / waived> | <projected runtime + bench JSON path> |
| 2b | Microbench-readiness — toolkit inner loops (**non-waivable**) | For each non-trivial inner loop in the model toolkit invoked by this hypothesis (HMM forward-backward, regime EM, LGB inner-CV, Kalman recursion, etc.), a microbench artifact exists at production-T scale at `scripts/bench/bench_<loopname>.py` + `logs/bench_<loopname>_<DATE>.json` with `git_head` + BLAS pinning + percentile-bootstrap CI. | <pass> | <bench script + JSON path per inner loop> |
| 3 | Pre-reg envelope coverage | substrate `dataset_checksums` per [data/processed/_provenance/](../../data/processed/_provenance/) cover the train + val + test envelope in design.md §2 | <pass / waived> | <provenance JSON path> |
| 4 | Reproducibility surface complete | The [ReproLog dataclass](../../src/skie_ninja/utils/reproducibility.py) has 13 fields; 5 are auto-captured at run start (`run_id`, `phase`, `hypothesis_id`, `timestamp_utc`, `host`). Gate 4 verifies the **8 operator-controlled fields**: `git_head` non-empty (or `--allow-dirty`); `pip_freeze_sha256` + `pip_freeze_path` resolves; `dataset_checksums` non-empty (per gate 3); `rng_seed` declared in config; `config_resolved_sha256` present; `env_id == uv.lock SHA`; `model_hash` slot present (filled at run-end, not preflight). | <pass> | <ReproLog template path> |
| 5 | BLAS thread pinning (**non-waivable**) | `OMP_NUM_THREADS = MKL_NUM_THREADS = OPENBLAS_NUM_THREADS = 1` per [ADR-0009](../../docs/decisions/ADR-0009-blas-thread-pinning.md) | <pass> | <env-snapshot path> |

### Tier 2 — Host-state validity (re-verified at each launch)

| # | Gate | Verification | Status | Evidence |
|---|---|---|---|---|
| 6 | No pending Windows restart | [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) returns `pending_restart: false` | <pass / waived> | <preflight.json path> |
| 7 | Active Hours covers runtime (**non-waivable**) | `active_hours_covers_run: true` with margin ≥10% over `expected_runtime_hours`. Compensating control if AH cannot be obtained: documented Windows-Update pause for the entire run window (recorded in §5 of this runbook). | <pass> | <preflight.json path> |
| 8 | Wake-lock will engage (**non-waivable**) | `system_required_wakelock` engaged in `__main__`; verified post-launch via `powercfg /requests` listing Python process under SYSTEM | <pass> | <powercfg requests log> |
| 9 | No high-priority scheduled tasks during the window | `schtasks /query` filtered for `[now, now + expected_runtime_hours]`; offenders disabled | <pass / waived> | <schtasks output snapshot> |
| 10 | Disk-space precheck | substrate + projected output footprint ≤ 80% of available | <pass / waived> | <`Get-PSDrive` output snapshot> |

### Tier 3 — Architectural readiness

| # | Gate | Verification | Status | Evidence |
|---|---|---|---|---|
| 11 | Disk-persistent HMM cache engaged (**non-waivable**) | `artifacts/runs/<HXXX>/<run_id>/_hmm_cache/` is writable; `SCHEMA_VERSION == "hmm_fit_cache_v3_pickle5_numba"` per [hmm_fit_cache.py:78](../../src/skie_ninja/models/regime/hmm_fit_cache.py) | <pass> | <test-write log> |
| 12 | Per-cfg checkpoint engaged (**non-waivable**) | `artifacts/runs/<HXXX>/<run_id>/_cfg_checkpoints/` is writable; `SCHEMA_VERSION == "cfg_checkpoint_v1_pickle5"` per [cfg_checkpoint.py:59](../../src/skie_ninja/backtest/cfg_checkpoint.py). WARN-but-load on cross-HEAD provenance drift; hard-error on schema drift (per ADR-0011 §"Provenance drift handling"). | <pass> | <test-write log> |
| 13 | Supervised relaunch loop is the launch path (**non-waivable**) | invocation goes through [scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh) with explicit `--hypothesis <HXXX> --config config/hypotheses/<HXXX>.yaml`, not `python scripts/run_walk_forward.py` direct. Script defaults are H050-bound and deprecated for H051+. | <pass> | <invocation transcript> |
| 14 | Runbook artifact exists + committed before launch (**non-waivable**) | this file at `research/01_hypothesis_register/<HXXX>/production_run_runbook.md`; supervisor records `runbook_commit_hash` + `runbook_file_sha256` into `.preflight.json` at launch. Audit gate verifies `runbook_commit_hash` is an ancestor of HEAD AND that waivers in the runbook file as of `runbook_commit_hash` are a subset of the waivers in HEAD. **Transitional (until `P1-SUPERVISOR-RUNBOOK-COMMIT-CAPTURE` lands):** operator records the runbook commit hash manually in §3 of this runbook before launch; audit gate verifies ancestor-of-HEAD via that operator-recorded value. | <pass> | this commit + `.preflight.json` |

### Waivers

If any gate above is waived, append a block per the ADR-0011 §"Waiver protocol":

```
## Gate <N> waiver — <YYYY-MM-DD>

**Rationale.** <one-paragraph technical justification>

**Impact.** <which failure class is being accepted; reference the retrospective>

**Mitigation.** <compensating control; e.g. shorter `--max-runtime-s`>

**Approver.** <operator name>; **waiver-date.** <YYYY-MM-DD>

**Linked commit.** <commit hash that lands this waiver into the runbook>
```

Gates 1, 2b, 4, 5, 7, 8, 11, 12, 13, 14 are non-waivable per ADR-0011.

## 3. Launch invocation

Canonical:

```bash
bash scripts/supervised_relaunch_loop.sh \
  --hypothesis <HXXX> \
  --config config/hypotheses/<HXXX>.yaml \
  --max-attempts <N>
```

For a resume launch:

```bash
bash scripts/supervised_relaunch_loop.sh \
  --hypothesis <HXXX> \
  --config config/hypotheses/<HXXX>.yaml \
  --max-attempts <N> \
  --start-resume-run-id <prior_run_id>
```

For symbol-narrowed launches (e.g. relaunch after one symbol completed):

```bash
bash scripts/supervised_relaunch_loop.sh \
  --hypothesis <HXXX> \
  --config config/hypotheses/<HXXX>.yaml \
  --symbols <subset> \
  --max-attempts <N> \
  --start-resume-run-id <prior_run_id>
```

Smoke / dry-run (no runbook gate; bypasses ADR-0011):

```bash
python scripts/run_walk_forward.py \
  --hypothesis <HXXX> \
  --config config/hypotheses/<HXXX>.yaml \
  --smoke --smoke-n <N>
```

## 4. Healthy-run signals

PROGRESS markers expected from a successful launch:

- `wakelock acquired` (early, INFO).
- `cfg-checkpoint resumed: sym=<X> prior_run_id=<Y> attempted=N loaded=M skipped=K provenance_drift=L` (only on `--resume-cfg-checkpoint`).
- `PROGRESS label-cfg-loop-step start | sym=<X> cfg_idx=<i> n_cfgs=<N> ...` and `done elapsed=<sec>s ... status=<computed | resumed>` for each cfg.
- `PROGRESS hmm-fit start | sym=<X> fold_id=<i> ...` and `done elapsed=<sec>s ...` for each cold HMM fit.
- `PROGRESS fold-fit done elapsed=<sec>s ...` for each outer fold.
- `PROGRESS symbol done` after each symbol completes.
- `PROGRESS run done` at completion.

## 5. Failure-mode → action matrix

Standard ADR-0011 failure classes only; hypothesis-specific failure modes append below this table.

| Symptom | Class | Action |
|---|---|---|
| Preflight rc=3 (block) | Class A — pending Windows restart | Reboot to clear pending update; re-run preflight; only launch when rc=0 or rc=2-with-justified-allow |
| Preflight rc=2 (warn) on AH coverage | Class A — Active Hours mis-configured | Adjust AH OR pause Windows Update for the run window per ADR-0011 §85 — gate 7 is non-waivable. The compensating control is a documented Windows-Update pause for the entire run window; `--allow-preflight-warn` is the run-2 blind path and must not be used here. |
| `powercfg /requests` does not list Python after T+30s | Class A — wake-lock not engaged | Kill run; debug [process_protection.py](../../src/skie_ninja/utils/process_protection.py); relaunch |
| Run silent for >10 min with no PROGRESS line | Class A or B — process killed externally; check Windows System Event Log for Kernel-Power Event 109 (Windows Update reboot) | If reboot-driven: relaunch with `--resume-hmm-cache <prior_run_id> --resume-cfg-checkpoint <prior_run_id>` after clearing pending update |
| `PROGRESS <phase> failed exc=MemoryError` mid-run | Class B — heap fragmentation OOM | Auto-resumed by relaunch loop; if loop exhausts attempts: subprocess isolation (`P1-CFG-SUBPROCESS-ISOLATION`) is the next architectural step |
| `supervisor_max_runtime_exceeded` classification | Class A — budget infeasibility (re-check Tier-1 gate 2) or Class B — fragmentation slowdown | Inspect last completed cfg; if substantial progress: relaunch with resume; if no progress: revisit hypothesis-search budget |
| `clean_exit_python_exception` | Code defect | Inspect traceback; do not blindly relaunch; fix and re-launch only after audit-remediate |
| `clean_exit_success` | Run complete | Proceed to §6 post-run audit gate |

### Hypothesis-specific failure modes

Append rows here for failure modes specific to this hypothesis (e.g. label-imbalance, regime-degeneracy, broker-specific cost-model failure).

## 6. Post-run audit gate (ADR-0011 §"Post-run audit gate")

Disposition is **not** written into design.md §10 until the audit-remediate-loop on the run output exits with `accept` or `accept-with-residuals`.

The audit triad spine:

1. **Quant-auditor** — verify (per design.md §10):
   - `T_<HXXX>` test statistic computed correctly.
   - LW2008 differential CI per [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) and the addendum (where applicable).
   - Hansen SPA per [src/skie_ninja/inference/multipletest/hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py) with omega method per [ADR-0008](../../docs/decisions/ADR-0008-spa-omega-method.md).
   - Fold count vs `n_required_for_power_80` per [ADR-0004](../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).
   - HMM stationarity pre-check per [ADR-0005](../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) (where applicable).
2. **Reproducibility-verifier** — verify:
   - ReproLog completeness — all 12 fields per gate 4 enumeration.
   - Substrate checksum survival from preflight `.preflight.json` into ReproLog `dataset_checksums`; canonical regression test [tests/unit/test_orchestrator_dataset_checksums.py](../../tests/unit/test_orchestrator_dataset_checksums.py).
   - Cache-on / cache-off byte-identity — warm-cold sidecar SHA256 byte-identical under `--no-hmm-cache` per [tests/unit/test_orchestrator_hmm_cache.py](../../tests/unit/test_orchestrator_hmm_cache.py); HMM-fit pickle byte-identical per [tests/unit/test_hmm_fit_cache.py](../../tests/unit/test_hmm_fit_cache.py) (F-1-4 contract).
   - Model-hash chain composition — `ReproLog.model_hash` equals canonical concatenation of per-symbol sidecar SHAs (HMM sidecar + walk-forward engine ledger + warm-cold diagnostic) wired through `with_model_hash`. Multi-sidecar helper open as `P1-MODEL-HASH-MULTI-SIDECAR-HELPER`.
   - Supervisor sidecar correspondence — `.preflight.json` / `.summary.json` / `.supervisor.jsonl` at `logs/walk_forward_runs/h050_prod_run_<DATE>.*` align by `run_id` with `logs/reproducibility/<run_id>.json`.
3. **Literature-check** (optional) — verify any newly-cited results in the disposition memo against primary sources.

The audit trail lives at `docs/audits/audit_trail_<YYYY-MM-DD>_<HXXX>-disposition-<run_id_short>.md`, where `<run_id_short>` is the first 8 hex chars of the terminal-attempt run_id. Cap is 3 rounds per `~/.claude/skills/audit-remediate-loop/SKILL.md`.

## 7. Disposition record

Filled at the close of the post-run audit. Mirrors design.md §10:

| Field | Value |
|---|---|
| Run-id (terminal attempt) | <hex> |
| Disposition | <positive / null / negative / inconclusive-rerun-required> |
| `T_<HXXX>` value | <value + 95% CI> |
| Hansen SPA p-value | <p ± bootstrap-bandwidth> |
| Fold count actual / required for 80% power | <m / n> |
| Audit trail | <docs/audits/audit_trail_<YYYY-MM-DD>_<HXXX>-disposition.md> |
| Hypothesis register update | <commit landing the disposition> |

## 8. Lessons-learned (filled at run completion)

Brief retrospective of any new failure mode or runbook gap encountered. Feed into the canonical ADR-0011 retrospective if it suggests a binding directive update; otherwise append to this hypothesis's runbook only.

## References

- [ADR-0011](../../docs/decisions/ADR-0011-production-walkforward-runbook.md) — binding directive.
- [memo_h050-prodrun-retrospective_2026-04-29.md](../../docs/research_notes/memo_h050-prodrun-retrospective_2026-04-29.md) — five-failure retrospective; empirical basis for the gates.
- [ADR-0010](../../docs/decisions/ADR-0010-multi-hour-run-process-protection.md) — wake-lock + supervisor + Windows-Update preflight.
- [ADR-0009](../../docs/decisions/ADR-0009-blas-thread-pinning.md) — BLAS thread pinning.
- [ADR-0008](../../docs/decisions/ADR-0008-spa-omega-method.md) — SPA omega method.
- [ADR-0005](../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) — HMM regime toolkit.
- [ADR-0004](../../docs/decisions/ADR-0004-alpha-and-power-defaults.md) — alpha + power defaults.
- `~/.claude/skills/audit-remediate-loop/SKILL.md` — audit-remediate-loop pattern.
