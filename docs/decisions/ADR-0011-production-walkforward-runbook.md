---
id: ADR-0011
title: Production walk-forward runbook — preflight checklist + execution shape + post-run audit gate
status: proposed
date: 2026-04-29
deciders: skoir
supersedes: docs/research_notes/runbook_walk-forward-launch-prep_2026-04-27.md (operator-facing per-run runbook → replaced by per-hypothesis runbook template); extends ADR-0010 §Layer 2 from Windows-Update-specific to general production-run gating
companion_artifacts:
  - docs/research_notes/memo_h050-prodrun-retrospective_2026-04-29.md
  - research/_templates/production_run_runbook.md
applies_to: H050 (in-flight); H051, H052a, H052b (queued); any future hypothesis with a multi-hour walk-forward production run
adr_schema_version: adr_v1
runbook_schema_version_required: production_run_runbook_v1
---

# ADR-0011 — Production walk-forward runbook

## Context

The H050 production walk-forward arc 2026-04-26 → 2026-04-29 incurred five distinct prod-run failures across ~34 hours of compute, producing zero aggregate disposition artifacts before the active relaunch loop on 2026-04-29. The failure catalogue is documented in [memo_h050-prodrun-retrospective_2026-04-29.md](../research_notes/memo_h050-prodrun-retrospective_2026-04-29.md). Its core finding:

- **3 of 5 failures (~88% of wall-clock burned: 30.4 / 34.4 hr) were predictable-by-preflight** — either a deterministic scriptable check on the configuration / host state, *or* a documented production-T-scale microbench artifact existing at toolkit-build-time, would have flagged the bad shape before launch.
- **2 of 5 failures were structural** — bounded only by an architecture that accepts crashes and resumes from per-cfg disk checkpoints under a supervised relaunch loop.

ADR-0010 established the wake-lock + supervisor + Windows-Update-preflight pattern reactively, after run-2. The remaining two of three Class-A failures (HMM redundancy, HMM EM Python-loop) had no preflight gate. H051, H052a, and H052b are queued behind H050 and would re-encounter the same patterns absent a binding directive.

The project has the audit-remediate-loop discipline at hypothesis-result time (per `~/.claude/CLAUDE.md` "Agentic Iteration"), but it is missing an equivalent gating discipline at hypothesis-launch time.

## Decision

A binding production-walk-forward runbook with three components:

1. **Preflight checklist** — 15-item gate (14 originally proposed + 1 microbench-readiness gate added in the Round-1 audit-remediate-loop) that must pass (or be explicitly waived with documented justification) before the first launch on real substrate.
2. **Execution shape** — supervised relaunch loop is the canonical launch path; direct orchestrator invocation is permitted only for `--smoke` / `--dry-run`.
3. **Post-run audit gate** — a structured audit-remediate-loop on the run output (not just the deliverable) before any disposition decision.

The runbook is operationalised via the per-hypothesis template at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md). Each hypothesis's runbook lives at `research/01_hypothesis_register/<HXXX>/production_run_runbook.md` and is a deliverable of pre-registration. See §"Per-hypothesis runbook" below for the schema-version contract.

## Preflight checklist (binding)

The 15 gates below are organised in three tiers. Tiers 1 and 2 are scriptable; tier 3 is documentary or architectural. The canonical implementation is the supervised launch path at [scripts/supervised_run.py](../../scripts/supervised_run.py) plus the per-hypothesis runbook at `research/01_hypothesis_register/<HXXX>/production_run_runbook.md`. Each gate names the failure-class evidence that motivates it and the implementation-status (shipped vs spec'd).

### Tier 1 — Configuration validity (6 gates)

| # | Gate | Failure class evidence | Implementation status |
|---|---|---|---|
| 1 | **HMM emission-dimensionality redundancy check** — when `len(cfg.hmm.feature_columns) == 1` AND `len(set(cfg.hmm.covariance_type) - {"tied"}) >= 2`, model-class deduplication is required (or the redundant types are dropped to one). At d=1, all of `spherical = diag = full = N` in effective parameter count; only `tied = 1` differs (per [audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](../audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) §"1-dim emission redundancy"). | Run-1 (2026-04-26) | Deduplication path **shipped** in `select_gaussian_hmm` ([commit c2caa20](../../src/skie_ninja/models/regime/selection.py)). YAML-level grid-redundancy detection + auto-detection that the deduplication path is engaged at runtime — **spec'd, not shipped**. Tracked under `P1-ADR-0011-GATE-1-DEDUP-DETECT`. |
| 2 | **Hyperparameter-search budget feasibility** — `n_draws × n_inner_folds × n_cfgs × n_outer_folds × per_fit_seconds_estimate` must fit inside `(per_attempt_runtime_cap × max_attempts × 0.9)` per the supervised relaunch loop's actual cap (currently 3 hr/attempt × 10 attempts = 27 hr; see §"Execution shape"). | Run-3 (24-hr cap exceeded with 6/27 cfgs) | Cost projector reading the YAML grid + `per_fit_seconds_estimate` from gate 2b's microbench artifact + emitting a single `expected_runtime_hours` figure — **spec'd, not shipped**. Tracked under `P1-ADR-0011-GATE-2-COST-PROJECTOR`. |
| 2b | **Microbench-readiness — toolkit inner loops** — for each non-trivial inner loop in the model toolkit invoked by the hypothesis (HMM forward-backward, regime EM, LGB inner-CV, Kalman recursion, etc.), a microbench artifact must exist at production-T scale with `git_head` + BLAS pinning per [ADR-0009](ADR-0009-blas-thread-pinning.md) + percentile-bootstrap CI. Artifact lives at `scripts/bench/bench_<loopname>.py` + `logs/bench_<loopname>_<DATE>.json`. The `per_fit_seconds_estimate` consumed by gate 2 is read from this artifact. | Run-3 (HMM EM Python-loop bottleneck only manifested at production-T; configurable check could not catch it) | HMM-cov-d=1 microbench at [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py); HMM EM kernel microbench at [scripts/bench/bench_em_kernels.py](../../scripts/bench/bench_em_kernels.py). LGB inner-CV + per-cfg microbench — **not shipped**. Tracked under `P1-ADR-0011-GATE-2B-MICROBENCH-CATALOGUE`. |
| 3 | **Pre-reg envelope coverage** — substrate `dataset_checksums` from [data/processed/_provenance/](../../data/processed/_provenance/) must cover the train + val + test envelope declared in the hypothesis design.md §2. | Generic | New invocation: orchestrator preflight reads design.md envelope; refuses launch on shortfall. **Spec'd, not shipped.** Tracked under `P1-ADR-0011-GATE-3-ENVELOPE-CHECK`. |
| 4 | **Reproducibility surface complete** — the `ReproLog` dataclass at [src/skie_ninja/utils/reproducibility.py](../../src/skie_ninja/utils/reproducibility.py) carries 13 fields. 5 are auto-captured by `RunContext` at run start (`run_id`, `phase`, `hypothesis_id`, `timestamp_utc`, `host`) and need no preflight check. The remaining **8 operator-controlled fields** are gate-4 mandatory: `git_head` non-empty (or `--allow-dirty`); `pip_freeze_sha256` captured AND `pip_freeze_path` resolves; `dataset_checksums` non-empty (per gate 3); `rng_seed` declared in config; `config_resolved_sha256` present (per `P1-CYCLE6-REPRO-DATASET-CHECKSUM` closure); `env_id == uv.lock SHA`; `model_hash` slot present (filled at run-end via `with_model_hash`, not at preflight). | Generic (closes the surface that `P1-CYCLE6-REPRO-DATASET-CHECKSUM` was opened for; gate makes it preflight-mandatory) | The `RunContext` already captures these; preflight check refuses launch on missing field. **Spec'd; partial implementation via existing tests at [tests/unit/test_orchestrator_dataset_checksums.py](../../tests/unit/test_orchestrator_dataset_checksums.py).** |
| 5 | **BLAS thread pinning verified** — `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS` all `==1` per [ADR-0009](ADR-0009-blas-thread-pinning.md). | Generic | Wrapper sets and verifies env-vars before subprocess spawn. **Shipped** in [scripts/supervised_run.py](../../scripts/supervised_run.py). |

### Tier 2 — Host-state validity (5 gates)

| # | Gate | Failure class evidence | Implementation status |
|---|---|---|---|
| 6 | **Pending-restart registry markers absent** — CBS RebootPending, WindowsUpdate Auto Update RebootRequired, Netlogon JoinDomain, OSUpgrade, PendingFileRenameOperations. | Run-2 (2026-04-27) | **Shipped**: [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) (commit `4ae8ca7`); supervisor refuses on rc=3 (block). |
| 7 | **Active Hours covers `expected_runtime_hours`** — registry-checked, with day-wrap handling; refuses launch if AH < runtime estimate + 10% margin (margin tracked under `P1-ADR-0011-AH-MARGIN-EMPIRICAL`). | Run-2 (4h37m kill at 04:39 CT under default 8-17 AH; the wake-lock at gate 8 is the systemic fix, but AH coverage is the necessary preflight precondition) | **Shipped** in same script as gate 6; supervisor refuses on rc=2 (warn) unless `--allow-preflight-warn`. |
| 8 | **Wake-lock will engage** — orchestrator's `__main__` registers `ES_CONTINUOUS \| ES_SYSTEM_REQUIRED` per [ADR-0010](ADR-0010-multi-hour-run-process-protection.md) Layer 1. Verified post-launch via `powercfg /requests` listing the Python process under SYSTEM. | Run-2 (no wake-lock registered → OS classified host as Active → Windows Update issued Kernel-Power Event 109 reboot) | **Shipped**: [src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py) wired into `__main__` at commit `4ae8ca7`. Post-launch verification check (supervisor reads `powercfg /requests` after T+30s and aborts if Python is missing from SYSTEM) — **spec'd, not shipped**. Tracked under `P1-ADR-0011-GATE-8-POSTLAUNCH-VERIFY`. |
| 9 | **No high-priority scheduled tasks** during the expected window — `schtasks /query` filters for tasks scheduled inside `[now, now + expected_runtime_hours]`. | Generic (defragmentation, antivirus, scheduled defrag have all interrupted long-running compute on Windows in published case studies) | Extension to [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1); refuses launch on hits unless explicitly waived. **Spec'd, not shipped.** Tracked under `P1-ADR-0011-GATE-9-SCHTASKS`. |
| 10 | **Disk-space precheck** — current substrate footprint + projected output footprint (per-cfg checkpoint + HMM cache + per-fold artifacts + ReproLog) ≤ 80% of available (ceiling tracked under `P1-ADR-0011-DISK-CEILING-EMPIRICAL`). | Generic (a multi-day run that fills the disk produces a non-recoverable failure mode separate from the heap-fragmentation case) | Preflight measures + projects. **Spec'd, not shipped.** Tracked under `P1-ADR-0011-GATE-10-DISK-PRECHECK`. |

### Tier 3 — Architectural-readiness (4 gates)

| # | Gate | Failure class evidence | Implementation status |
|---|---|---|---|
| 11 | **Disk-persistent HMM cache engaged** — `--resume-hmm-cache` (when prior run exists) and disk-persistent HMM-fit cache `SCHEMA_VERSION == "hmm_fit_cache_v3_pickle5_numba"` per [hmm_fit_cache.py](../../src/skie_ninja/models/regime/hmm_fit_cache.py) verified writable to `artifacts/runs/<HXXX>/<run_id>/_hmm_cache/`. | Run-3 lost ~22 hr of in-memory HMM fits to supervisor cap; cache landed after | **Shipped** at commit `67c0419`. Existence + writeability check on the canonical path. |
| 12 | **Per-cfg checkpoint engaged** — [src/skie_ninja/backtest/cfg_checkpoint.py](../../src/skie_ninja/backtest/cfg_checkpoint.py) `SCHEMA_VERSION == "cfg_checkpoint_v1_pickle5"` ([commit ee2112c](../audits/audit_trail_2026-04-29_cfg-checkpoint.md)) verified writable to `artifacts/runs/<HXXX>/<run_id>/_cfg_checkpoints/`. | Run-4 + run-5 (cfg 20 + cfg 24 OOMs lost 19 + 23 cfgs of inner-CV-LGB) | **Shipped** at commit `ee2112c`. Existence + writeability check. |
| 13 | **Supervised relaunch loop is the launch path** — [scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh) ([commit 7924f0a](../../scripts/supervised_relaunch_loop.sh)) wraps [scripts/supervised_run.py](../../scripts/supervised_run.py); direct `python scripts/run_walk_forward.py` invocation refused on real-substrate launches. **Operator command must include explicit `--hypothesis <HXXX> --config config/hypotheses/<HXXX>.yaml`**; defaults in the script are H050-bound and are deprecated for H051+. | Run-4 + run-5 structural fragmentation; H050 hard-coded defaults must not propagate | Wrapper script **shipped**. Drop of H050 defaults — tracked under `P1-SUPERVISED-RELAUNCH-LOOP-HXXX-DEFAULTS-DROP`. |
| 14 | **Per-hypothesis runbook artifact exists + is committed before launch** — `research/01_hypothesis_register/<HXXX>/production_run_runbook.md` instantiated from [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md); supervisor records, at launch time, the on-disk runbook file's SHA256 and the git commit hash of the runbook artifact into `.preflight.json` under fields `runbook_commit_hash` + `runbook_file_sha256`. Audit gate verifies that `runbook_commit_hash` is an ancestor of HEAD AND that the listed waivers in the runbook file as of `runbook_commit_hash` are a subset of the waivers in HEAD (additions after launch are detected as retroactive). **Transitional clause (until `P1-SUPERVISOR-RUNBOOK-COMMIT-CAPTURE` lands):** operator records the runbook commit hash manually in §3 of the per-hypothesis runbook before launch; audit gate verifies ancestor-of-HEAD via that operator-recorded value. The gate's auditability claim is paper-only until the supervisor capture ships; this is acknowledged in the residual-risk ledger as load-bearing. | Generic (run-1 + run-2 had no runbook; would have caught both); waiver auditability fix from R-1-7 | File-existence check + schema validation against the template — **spec'd**. Supervisor commit-hash + file-SHA capture into `.preflight.json` — **spec'd, not shipped**. Tracked under `P1-SUPERVISOR-RUNBOOK-COMMIT-CAPTURE` (load-bearing for full auditability of gate 14; pre-shipping launches use the transitional clause). |

### Waiver protocol

A gate may be waived only by recording in the per-hypothesis runbook a `Gate <N> waiver` block containing:

1. Rationale (technical, not convenience).
2. Impact assessment (which failure class is being accepted).
3. Mitigation (compensating control, e.g. shorter `--max-runtime-s` cap).
4. Approver (operator name) and waiver-date.
5. Linked commit hash that lands the waiver into the runbook (verifiable as ancestor of launch via `runbook_commit_hash` at gate 14).

The waiver is committed with the runbook before launch. The supervisor reads the runbook's waiver list and proceeds accordingly. **Non-waivable gates: 1, 2b, 4, 5, 7, 8, 11, 12, 13, 14.**

Gate 7 is included in non-waivable in this revision (R-1-7 / Q-1-11 fix): a documented decision to pause Windows Update for the run window is the compensating control if AH coverage cannot be obtained, but the gate 7 check is the binding precondition that ensures the operator has either configured AH or paused WU explicitly. Bypassing it via `--allow-preflight-warn` is the same blind path that produced run-2.

## Execution shape (canonical)

For real-substrate launches:

```bash
bash scripts/supervised_relaunch_loop.sh \
  --hypothesis <HXXX> \
  --config config/hypotheses/<HXXX>.yaml \
  --max-attempts <N>                       # bound on relaunch attempts; see cap-and-attempts table below
  [--start-resume-run-id <prior_run_id>]   # if resuming a crashed run
  [--symbols <subset>]                     # narrow to one symbol if needed
```

**Cap-and-attempts hierarchy** (precise, not summarised):

| Symbol | Default | Source | Notes |
|---|---|---|---|
| Per-attempt runtime cap | **3 hr** (10800 s) | `scripts/supervised_relaunch_loop.sh:30` `PER_LAUNCH_CAP_S=10800` | Set well below the empirical fragmentation wall (~2 hr at H050 cfg-OOM threshold). |
| Standalone supervisor cap | 36 hr (129600 s) | `scripts/supervised_run.py:53` `_DEFAULT_MAX_RUNTIME_S = 36*3600` | Applies only when `supervised_run.py` is invoked directly (no relaunch loop); derivation tracked under `P1-SUPERVISOR-DEFAULTS-DERIVATION-DOC`. |
| Max relaunch attempts | **10** | `scripts/supervised_relaunch_loop.sh:27` `MAX_ATTEMPTS=10` | Empirical derivation tracked under `P1-RELAUNCH-MAX-ATTEMPTS-DERIVATION` (calibrate against observed cfg-OOM rate and per-attempt cfg progression). |
| Effective wall-clock budget per run | per-attempt × max-attempts = **30 hr** | derived | Used by gate 2 budget feasibility (with 0.9 safety factor → 27 hr usable). |
| Default `expected_runtime_hours` (used by gate 7 AH check) | 22 (H050-derived) | `scripts/supervised_run.py:56` | **H050-specific**; for H051+ operators must pass `--expected-runtime-h <N>` from the hypothesis's runbook §1. Drop of H050-default tracked under `P1-SUPERVISED-RUN-EXPECTED-RUNTIME-HYPOTHESIS-BOUND`. |

The relaunch loop:
1. Runs the preflight checklist (`scripts/supervised_run.py` invokes preflight first).
2. Spawns the orchestrator under the per-attempt 3-hr cap.
3. On crash, classifies the exit (clean / Python-exception / external-kill / supervisor-cap / ambiguous).
4. If exit is consistent with a recoverable failure mode (cfg-OOM, OS-reboot, supervisor-cap), automatically relaunches with `--resume-hmm-cache <prior_run_id> --resume-cfg-checkpoint <prior_run_id>` until `--max-attempts` is exhausted or the run succeeds.
5. Aggregates supervisor telemetry per attempt + emits a final summary.

Smoke and dry-run launches use the bare orchestrator: `python scripts/run_walk_forward.py --hypothesis <HXXX> --config <path> --smoke --smoke-n <N>` or `--dry-run`.

## Per-hypothesis runbook

The per-hypothesis runbook at `research/01_hypothesis_register/<HXXX>/production_run_runbook.md` is a deliverable of pre-registration. Its template is at [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md).

**Schema-version contract.** The template's frontmatter declares `runbook_schema_version: production_run_runbook_v1`. Each hypothesis's runbook inherits this version. Any future amendment to ADR-0011 that changes the gate count, gate non-waivability, or post-run audit gate spine **must bump `runbook_schema_version`** (e.g. `_v2`) and trigger a re-instantiation of every per-hypothesis runbook before the next launch of that hypothesis. The amendment commit must specify the migration path (which fields are added / removed / renamed).

**Binding-revision tracking.** Each per-hypothesis runbook records `adr_0011_revision: <commit hash>` in its frontmatter at instantiation. A future ADR-0011 amendment can be detected per-hypothesis by comparing `adr_0011_revision` to the binding-ADR-0011 tip; if drift, the runbook must be re-instantiated before launch.

**Co-commit resolution (chicken-and-egg).** When a per-hypothesis runbook is committed *together* with an ADR-0011 amendment, the binding revision's commit hash cannot be known until the commit object is created. Resolution: the runbook frontmatter records `adr_0011_revision: TODO-resolve-after-commit` at the co-commit, and a follow-up commit immediately fills the value with the resolved SHA before the gate 14 supervisor commit-hash capture would otherwise reject the launch. The TODO marker is detected by the runbook-validator and treated as a launch-blocking gap.

## Provenance drift handling

Both the disk-persistent HMM cache and per-cfg checkpoint use **WARN-but-load** semantics on cross-HEAD / cross-Python / cross-numpy provenance drift, and **hard-error** semantics on `SCHEMA_VERSION` drift. The relaunch loop forwards the WARN to operator output but does not abort. Schema drift aborts the load; the operator must clear the cache directory or pin to the producing schema-version commit. This convention is mirrored in any future cache module added under this ADR.

Reference implementations:
- [hmm_fit_cache.py:39-46](../../src/skie_ninja/models/regime/hmm_fit_cache.py) (module docstring documenting WARN-but-load).
- [hmm_fit_cache.py:248-249](../../src/skie_ninja/models/regime/hmm_fit_cache.py) (`raise ValueError` on schema mismatch).
- [cfg_checkpoint.py:30-31](../../src/skie_ninja/backtest/cfg_checkpoint.py) ("WARN-but-load semantics consistent with the HMM cache").
- [cfg_checkpoint.py:228-255](../../src/skie_ninja/backtest/cfg_checkpoint.py) (`check_provenance` returning mismatch list).

## Post-run audit gate (binding)

A run is **not** dispositioned until an audit-remediate-loop has been run on its output. The audit triad is hypothesis-specific but the spine is fixed:

1. **Quant-auditor** — verifies `T_<HXXX>` test statistic per design.md §10; LW2008 differential CI per addendum (where applicable); Hansen SPA per [ADR-0008](ADR-0008-spa-omega-method.md); fold count vs `n_required_for_power_80` per [ADR-0004](ADR-0004-alpha-and-power-defaults.md); HMM stationarity pre-check per [ADR-0005](ADR-0005-hmm-regime-toolkit.md).
2. **Reproducibility-verifier** — verifies:
   - **ReproLog completeness** — all 13 fields of the dataclass at [src/skie_ninja/utils/reproducibility.py](../../src/skie_ninja/utils/reproducibility.py) populated (5 auto-captured: `run_id`, `phase`, `hypothesis_id`, `timestamp_utc`, `host`; 8 operator-controlled per gate 4 enumeration above).
   - **Substrate checksum survival** — verifies `_load_output_sha256` (at [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py)) read the provenance JSON correctly and the `dataset_checksums` field of the on-disk ReproLog matches the preflight `.preflight.json` substrate-SHA. Canonical regression test: [tests/unit/test_orchestrator_dataset_checksums.py](../../tests/unit/test_orchestrator_dataset_checksums.py).
   - **Cache-on / cache-off byte-identity** — assert via [tests/unit/test_orchestrator_hmm_cache.py](../../tests/unit/test_orchestrator_hmm_cache.py) that the warm-cold sidecar SHA256 is byte-identical under `--no-hmm-cache`; assert via [tests/unit/test_hmm_fit_cache.py](../../tests/unit/test_hmm_fit_cache.py) that two HMM-fit pickles with identical inputs are byte-identical (the F-1-4 contract per the persistent-cache audit trail). Per-cfg checkpoint byte-identity is **not** a contract because cfg checkpoints inherit `producing_run_id` and so are run-id-dependent by design.
   - **Model-hash chain composition** — verify ReproLog.model_hash equals the canonical concatenation of the per-symbol sidecar SHAs (HMM sidecar + walk-forward engine ledger SHA + warm-cold diagnostic) wired through `with_model_hash` at [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py). The current implementation is a single string concatenation built in the orchestrator; a proper introspectable chain is open as residual `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` (see §"Residual risk" below).
   - **Supervisor sidecar correspondence** — `.preflight.json`, `.summary.json`, and `.supervisor.jsonl` at `logs/walk_forward_runs/h050_prod_run_<DATE>.*` exist and align by `run_id` with the orchestrator's ReproLog at `logs/reproducibility/<run_id>.json`. Supervisor sidecars are tracked outside ReproLog by run_id correspondence; the audit gate verifies both directories exist for the same run.
3. **Literature-check** (optional, hypothesis-specific) — verifies any newly-cited results in the disposition memo against primary sources.

Cap remains 3 rounds per `~/.claude/skills/audit-remediate-loop/SKILL.md`. The audit trail lives at `docs/audits/audit_trail_<YYYY-MM-DD>_<HXXX>-disposition-<run_id_short>.md`, where `<run_id_short>` is the first 8 hex chars of the terminal-attempt run_id (so re-disposition on the same hypothesis on the same date does not collide). Disposition cannot be written into design.md §10 until the audit trail's exit verdict is `accept` or `accept-with-residuals` with documented residuals.

## Alternatives considered

### A. Make Class-A failures advisory only (warn, do not block)

Rejected. Run-1 burned 180 minutes; run-2 burned 4h37m; run-3 burned 22h47m. Three avoidable Class-A failures cost ~30 hours of wall-clock. A warn-only gate has the same expected loss as no gate when the operator launches in good faith and the warning is not load-bearing in the launch decision.

### B. Single monolithic preflight script instead of tiered checklist

Rejected. Tiers separate static-config (Tier 1) from host-state (Tier 2) from architectural-readiness (Tier 3). Each tier is exercised at a different lifecycle point: Tier 1 at config-write, Tier 2 at launch-time, Tier 3 at first-launch / per-relaunch. A monolithic script bundles all three into a single binary verdict and obscures which tier failed.

### C. Defer until H050 completes; learn more from the relaunch-loop run

Rejected. The decision pattern would re-encounter every Class-A failure on H051's first launch. The directive's value is exactly that it transfers across hypotheses; deferring it forfeits that value for the next three pre-registered hypotheses.

### D. Codify only Tier 2 (the Windows-host gates) and leave method-readiness to hypothesis design

Rejected. Run-1 and run-3 are method-readiness failures (HMM redundancy + HMM EM Python-loop). Limiting the directive to host-state would leave 2 of 3 Class-A failures uncovered.

### E. Spec all 15 gates but ship none (full deferral to follow-ups)

Rejected. Tier 1 gate 5 (BLAS), Tier 2 gates 6–8 (Windows-Update preflight + wake-lock), Tier 3 gates 11–13 (caches + relaunch) are already shipped from prior commits. The directive's purpose is to lock the existing scaffolding into a binding contract while marking the residual gates (1-runtime-detect, 2-cost-projector, 2b-microbench-catalogue, 3-envelope-check, 8-postlaunch-verify, 9-schtasks, 10-disk-precheck, 13-defaults-drop, 14-supervisor-commit-capture) as follow-ups. A future H051 launch under this revision would proceed under the shipped gates plus operator-discipline-on-the-residuals; this is materially stronger than the no-directive baseline.

## Consequences

### Adopted

- A 15-item preflight checklist is mandatory before the first real-substrate launch of any hypothesis. Gates 1, 2b, 4, 5, 7, 8, 11, 12, 13, 14 are non-waivable.
- The supervised relaunch loop is the canonical launch path. Direct orchestrator invocation is reserved for `--smoke` / `--dry-run`.
- Each hypothesis spawns a runbook artifact at design time, not after the first failure. Runbook schema is versioned (`production_run_runbook_v1`) and bound to a specific ADR-0011 commit.
- Disposition decisions are gated by an audit-remediate-loop on the run output, not just the deliverable.
- WARN-but-load on provenance drift; hard-error on schema drift. Mirrored in any future cache module.

### Trade-offs accepted

- Preflight time: an additional ~30 sec per launch for gates 6, 7, 9 (Windows registry probes); negligible relative to multi-hour runs.
- Configuration friction: each hypothesis must instantiate the runbook at design time, before any prototyping. Rationale: the prototyping cost is paid once; the production run cost is paid per launch.
- Coupling to Windows: gates 6–10 are Windows-specific. Cross-platform support is scoped under the existing `P1-LINUX-MIGRATION-CONSIDERATION` follow-up (out of this ADR's scope).
- 9 of 15 gates are spec-only (not shipped); enforcement depends on the follow-up implementation track. The directive is materially stronger than no-directive but is partly aspirational until those follow-ups land.

### Residual risk

The architectural items below are explicitly carried as known residuals. They are accepted because the relaunch-loop bound is operationally sufficient and these are deferred-not-rejected per their respective audit trails.

| Item | Class | Mitigation status |
|---|---|---|
| `P1-CFG-SUBPROCESS-ISOLATION` | Class B (residual fragmentation under sufficiently-long runs) | Relaunch loop bounds work loss to one cfg; acceptable until a hypothesis demands continuous-process semantics. |
| `P1-CFG-CHECKPOINT-AUTO-RELAUNCH` | Operational (currently shell-script driven) | Active sixth attempt is exercising the script; promote to Python-supervisor-managed if shell proves brittle. |
| `P1-PER-SYMBOL-RESUME` (ADR-0010 Layer 3) | Class B (post-symbol-completion crashes lose ≤50% wall-clock) | Per-cfg checkpoint already amortises within-symbol; per-symbol resume is a finer-grained extension. |
| `P1-WALK-FORWARD-PER-FOLD-CHECKPOINT` | Class B (within-cfg fold-level recovery) | Bounded by current per-cfg cost (~5–15 min per cfg post-numba-kernels); cfg-level granularity is the right tier for the current workload. |
| `P1-LGB-INNER-CV-RESULT-CHECKPOINT` | Class B (inner-CV-LGB results lost on cfg-level crash) | Per-cfg checkpoint catches at the cfg boundary; finer granularity not required at current cycle counts. |
| `P1-LGB-INNER-CV-SUBPROCESS-ISOLATION` | Class B (alternate fragmentation mitigation) | Subsumed by `P1-CFG-SUBPROCESS-ISOLATION` if the cfg-level isolation lands. |
| `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` | Reproducibility (R-1-5) | Current `with_model_hash` accepts a single string; multi-sidecar composability requires a helper. Audit gate verifies the canonical concatenation manually until the helper lands. |
| `P1-ADR-0011-GATE-1-DEDUP-DETECT` | Spec-only Tier-1 gate | Auto-detect that the deduplication path in `select_gaussian_hmm` engaged at runtime; report into ReproLog. |
| `P1-ADR-0011-GATE-2-COST-PROJECTOR` | Spec-only Tier-1 gate (depends on `P1-ADR-0011-GATE-2B-MICROBENCH-CATALOGUE` for per-loop bench JSON inputs) | Cost projector reading YAML + microbench JSON; emits `expected_runtime_hours`. |
| `P1-ADR-0011-GATE-2B-MICROBENCH-CATALOGUE` | Spec-only Tier-1 gate | Catalogue of required microbench artifacts per toolkit inner loop; check existence + freshness at preflight. |
| `P1-ADR-0011-GATE-3-ENVELOPE-CHECK` | Spec-only Tier-1 gate | Orchestrator preflight reads design.md envelope; refuses on shortfall. |
| `P1-ADR-0011-GATE-8-POSTLAUNCH-VERIFY` | Spec-only Tier-2 gate | Supervisor T+30s `powercfg /requests` check. |
| `P1-ADR-0011-GATE-9-SCHTASKS` | Spec-only Tier-2 gate | `schtasks /query` extension to preflight. |
| `P1-ADR-0011-GATE-10-DISK-PRECHECK` | Spec-only Tier-2 gate | Disk-space measure + project. |
| `P1-SUPERVISED-RELAUNCH-LOOP-HXXX-DEFAULTS-DROP` | Spec-only Tier-3 gate 13 | Drop H050 hard-coded defaults from `scripts/supervised_relaunch_loop.sh`; require explicit `--hypothesis` + `--config`. |
| `P1-SUPERVISED-RUN-EXPECTED-RUNTIME-HYPOTHESIS-BOUND` | Spec-only Tier-1 gate 7 | Drop 22-hr H050 default from `scripts/supervised_run.py:56`; require explicit `--expected-runtime-h` from per-hypothesis runbook §1. |
| `P1-SUPERVISOR-RUNBOOK-COMMIT-CAPTURE` | Spec-only Tier-3 gate 14 | Supervisor records `runbook_commit_hash` + `runbook_file_sha256` into `.preflight.json`. |
| `P1-RELAUNCH-MAX-ATTEMPTS-DERIVATION` | Threshold derivation | Calibrate `MAX_ATTEMPTS=10` against observed cfg-OOM rate + per-attempt cfg progression. |
| `P1-ADR-0011-DISK-CEILING-EMPIRICAL` | Threshold derivation | Calibrate 80% disk-space ceiling against largest-observed substrate + output-tree footprint. |
| `P1-ADR-0011-AH-MARGIN-EMPIRICAL` | Threshold derivation | Calibrate 10% AH-coverage margin against observed runtime variance. |

Hardware-level events (UPS battery failure, sudden power loss to the wall) remain unaddressed by any of these layers. Tracked under existing `P1-WORKSTATION-UPS-RECOMMENDATION` (advisory; out of repo scope).

## Empirical justification

The five-failure retrospective is at [memo_h050-prodrun-retrospective_2026-04-29.md](../research_notes/memo_h050-prodrun-retrospective_2026-04-29.md). Each gate cites the failure-class evidence in its row of the Tier 1/2/3 tables. Wall-clock totals: Class A = 30.4 hr (run-1: 3.0; run-2: 4.6; run-3: 22.8); Class B = 4 hr (run-4 + run-5); cumulative = 34.4 hr.

Per `~/.claude/CLAUDE.md` "Parameter & Prompt Selection": no thresholds are declared without empirical justification. Three thresholds inherit explicit derivation follow-ups: `P1-ADR-0011-AH-MARGIN-EMPIRICAL` (10% AH margin), `P1-ADR-0011-DISK-CEILING-EMPIRICAL` (80% disk ceiling), `P1-RELAUNCH-MAX-ATTEMPTS-DERIVATION` (10-attempt cap). The 36-hr standalone supervisor cap inherits `P1-SUPERVISOR-DEFAULTS-DERIVATION-DOC` from ADR-0010. The 22-hr `expected_runtime_hours` default is H050-derived and is being dropped via `P1-SUPERVISED-RUN-EXPECTED-RUNTIME-HYPOTHESIS-BOUND`. The 3-hr per-attempt cap is set below the empirical fragmentation wall (~2 hr at H050 cfg-OOM threshold per `audit_trail_2026-04-28_lgb-heap-fragmentation.md` and `audit_trail_2026-04-29_cfg-checkpoint.md`); operationally derived from observed crash latency, not arbitrary.

The waiver protocol is modelled on the project's existing pre-registration deviation pattern (per `~/.claude/CLAUDE.md` "Verification" → "Flag any discrepancy between implementation and canonical method"); a documented waiver is operationally equivalent to a documented pre-reg deviation. The runbook-commit-hash + file-SHA capture at gate 14 makes retroactive waivers detectable, closing the prior governance gap.

## References

- [memo_h050-prodrun-retrospective_2026-04-29.md](../research_notes/memo_h050-prodrun-retrospective_2026-04-29.md) — empirical basis (5-failure retrospective).
- [research/_templates/production_run_runbook.md](../../research/_templates/production_run_runbook.md) — per-hypothesis runbook template.
- [docs/research_notes/runbook_walk-forward-launch-prep_2026-04-27.md](../research_notes/runbook_walk-forward-launch-prep_2026-04-27.md) — superseded operator runbook (status flag updated 2026-04-29).
- [ADR-0010-multi-hour-run-process-protection.md](ADR-0010-multi-hour-run-process-protection.md) — wake-lock + supervisor + Windows-Update preflight (extended here from Windows-Update-specific to general).
- [ADR-0009-blas-thread-pinning.md](ADR-0009-blas-thread-pinning.md) — BLAS thread pinning contract (gate 5).
- [ADR-0008-spa-omega-method.md](ADR-0008-spa-omega-method.md) — SPA omega method (post-run audit gate).
- [ADR-0005-hmm-regime-toolkit.md](ADR-0005-hmm-regime-toolkit.md) — HMM toolkit (gate 1).
- [ADR-0004-alpha-and-power-defaults.md](ADR-0004-alpha-and-power-defaults.md) — power calculation (post-run audit gate).
- [scripts/supervised_relaunch_loop.sh](../../scripts/supervised_relaunch_loop.sh) — canonical launch path.
- [scripts/supervised_run.py](../../scripts/supervised_run.py) — supervisor wrapper.
- [scripts/preflight/check_windows_update.ps1](../../scripts/preflight/check_windows_update.ps1) — Windows-host preflight.
- [src/skie_ninja/backtest/cfg_checkpoint.py](../../src/skie_ninja/backtest/cfg_checkpoint.py) — per-cfg checkpoint (gate 12).
- [src/skie_ninja/models/regime/hmm_fit_cache.py](../../src/skie_ninja/models/regime/hmm_fit_cache.py) — disk-persistent HMM cache (gate 11).
- [src/skie_ninja/utils/process_protection.py](../../src/skie_ninja/utils/process_protection.py) — wake-lock helper (gate 8).
- [src/skie_ninja/utils/reproducibility.py](../../src/skie_ninja/utils/reproducibility.py) — `ReproLog` dataclass (gate 4 field enumeration).
- [tests/unit/test_orchestrator_dataset_checksums.py](../../tests/unit/test_orchestrator_dataset_checksums.py) — substrate checksum survival regression test (post-run audit gate item 2).
- [tests/unit/test_orchestrator_hmm_cache.py](../../tests/unit/test_orchestrator_hmm_cache.py) — cache-on / cache-off byte-identity regression test.
- [tests/unit/test_hmm_fit_cache.py](../../tests/unit/test_hmm_fit_cache.py) — HMM-fit pickle byte-identity regression test.
- [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py) + [scripts/bench/bench_em_kernels.py](../../scripts/bench/bench_em_kernels.py) — gate 2b microbench artifacts (HMM toolkit, shipped).
- `~/.claude/CLAUDE.md` — user-global directives (Evidence Hierarchy, Parameter Selection, Verification, Agentic Iteration, Reproducibility).
- `~/.claude/skills/audit-remediate-loop/SKILL.md` — audit-remediate-loop pattern (post-run audit gate).
