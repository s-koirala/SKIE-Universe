---
phase: O.20
date: 2026-05-20
hypothesis_id: H050_invert
artifact: walk_forward_orchestrator + smoke_run + kpi_report_v1
audit_loop_rounds: 1
verdict: accept-with-residuals
---

# Audit-remediate-loop trail — H050.invert walk-forward orchestrator + smoke run + KPI v1 (Phase O.20)

## Scope

Closes the H050.invert §11.2 BLOCKING-BEFORE-PRODUCTION-RUN follow-ups via a single in-place atomic landing per [ADR-0027 §D-3 empirical-before-amendment sequencing rule][1]:

- `P1-H050-INVERT-WALK-FORWARD-ORCHESTRATOR-IMPL` — [scripts/run_h050_invert_walk_forward.py](../../scripts/run_h050_invert_walk_forward.py) thin wrapper + module-level `_INVERT_HMM_GATE` flag in [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py); 2 line-level inversion-site patches at lines ~1506 + ~1616.
- `P1-H050-INVERT-LEAKAGE-CANARY-INTEGRATION-TEST` — [tests/integration/test_h050_invert_pit_canaries.py](../../tests/integration/test_h050_invert_pit_canaries.py); 6 tests across 5 canary classes (A label-swap; B PIT-causal gate choice; C no train→test leak; D NaN-poison + flag isolation; E full-composition smoke).
- `P1-H050-INVERT-PARITY-INVARIANT-TEST` — [tests/unit/test_h050_invert_orchestrator.py](../../tests/unit/test_h050_invert_orchestrator.py); 13 tests across 5 classes covering module-flag default, argv resolution invariants, gate-inversion logic, wrapper imports, parser extension.

Per the parent [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo][2] §7.3 Variant A, H050.invert tests the H-b anti-selection sub-hypothesis empirically. Per [ADR-0027 §D-4 genetic-successor discipline][1], all H050 v1 §1-§7 mechanic specifications are preserved verbatim; the single divergence is the gate-state selection criterion at the HMM regime layer (line 1616 of [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py): `np.argmax(means)` → `np.argmin(means)` when `_INVERT_HMM_GATE = True`).

## Round 1 — inline self-audit (parallel quant + code + repro + format branches)

Per the documented [`P1-AGENT-TOOL-NOT-SURFACED` workaround pattern][3], R1 audit executed inline. The Task/Agent tool is not surfaced in this runtime variant, so the audit branches were applied as direct review checks across the four canonical specialist surfaces (quant correctness, code quality, reproducibility provenance, format compliance).

### Quant-auditor branch

| # | Severity | Finding | Disposition |
|---|---|---|---|
| F-Q-1 | major | Inversion site at line 1616 `_fit_fold_body` was the only locus identified initially — but the degenerate-y short-circuit branch at line ~1506 ALSO reads `np.argmax(hmm.params_.means[:, 0])` for `rhm_short`. Without mirroring the inversion there, H050.invert produces inconsistent gate-state choices on label-degenerate folds vs healthy folds. | REMEDIATED inline: extended both code paths to read the module-level `_INVERT_HMM_GATE` flag with parallel argmin/argmax logic. Documented under the "H050.invert (Phase O.20): mirror the inversion site above" comment block. |
| F-Q-2 | major | The HMM-fit cache at [src/skie_ninja/models/regime/hmm_fit_cache.py](../../src/skie_ninja/models/regime/hmm_fit_cache.py) persists `regime_high_mean` per (symbol, fold, label_horizon) key. If an H050 v1 run + H050.invert run share an `artifacts/runs/<run_id>/_hmm_cache/` directory, the cached `regime_high_mean` from H050 v1 (argmax) would silently propagate into H050.invert (which expects argmin). | DOCUMENTED as non-issue: each run has its own `run_id`; the cache is per-run-id keyed. The H050.invert wrapper does NOT pass `--resume-hmm-cache` from any H050 v1 run, so cross-contamination is structurally impossible at the canonical launch path. Tracked under non-blocking follow-up `P1-H050-INVERT-HMM-CACHE-CROSS-CONTAMINATION-DOC`. |
| F-Q-3 | major | The 2-state HMM complementarity property (argmin = 1 − argmax) is BIT-EQUIVALENT to swapping the long/short state assignments. If the H-b anti-selection hypothesis is the entire mechanism driving H050 v1's catastrophe, H050.invert should produce a numerically MIRROR-IMAGE result (positive Sharpe of similar magnitude). If H-c whipsaw dominates, both H050 v1 and H050.invert remain catastrophic. The smoke run will discriminate empirically. | DOCUMENTED in design.md §1 + this audit trail §"Empirical-prediction discriminant". |
| F-Q-4 | major | The K>2 HMM case (n_states selected by BIC) is NOT a clean label-swap. With K=3 fitted, H050 v1 selects argmax(K=3-state means) and H050.invert selects argmin(K=3-state means); the K-2 middle states are non-selected under BOTH gates. This means H050.invert is NOT mathematically the complement of H050 v1 in the >2-state case. | DOCUMENTED in [tests/unit/test_h050_invert_orchestrator.py](../../tests/unit/test_h050_invert_orchestrator.py) `test_argmin_argmax_swap_property` docstring + design.md §5 `# justify:` annotation. The K=2 case is the dominant canonical fit per H050 v1 empirical history (BIC consistently selects K=2 on the H050 substrate). |
| F-Q-5 | minor | The `regime_high_mean` variable name is preserved verbatim under the inversion (semantically becomes "gate state index" not "highest-mean state index"). Misleading variable name. | DOCUMENTED in the line ~1616 comment block: "The variable name `regime_high_mean` is preserved verbatim for upstream code compatibility; semantically it is the 'gate state index' in both branches." Variable rename deferred per non-blocking polish follow-up `P1-H050-INVERT-REGIME-HIGH-MEAN-VARIABLE-RENAME-V2`. |

### Code-reviewer branch

| # | Severity | Finding | Disposition |
|---|---|---|---|
| F-C-1 | major | The wrapper script uses module-level `global _INVERT_HMM_GATE` mutation in `run()`. This is the documented pragmatic pattern (mirrors `_LGB_INNER_CV_CURRENT_CTX` per `P1-LGB-INNER-CV-RESULT-CHECKPOINT` ledger entry 2026-04-30), but introduces shared module state. | DOCUMENTED in the module-level constant block. The flag is set EVERY invocation from argv (not just first), so subsequent test invocations in the same process get the correct flag state. The unit-test `test_module_flag_isolation_across_runs` verifies the patched-state-reverts contract. |
| F-C-2 | minor | The wrapper's `_resolve_h050_invert_argv` mutates a copied list rather than returning a new tuple. Style-only. | NON-BLOCKING — list is local to the function; no mutation visible to the caller. |
| F-C-3 | minor | `--invert-gate` is mounted at the orchestrator CLI but the orchestrator's `_run_start_ctx` PROGRESS dict already includes it. Sufficient provenance. | VERIFIED — see line 3083 of [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py). |
| F-C-4 | minor | Wrapper docstring mentions BLAS pinning via OMP/MKL/OPENBLAS env vars but the wrapper itself does NOT enforce them at `__main__`. | DOCUMENTED — the canonical orchestrator's `__main__` already validates env-var settings per [ADR-0009 BLAS threading][4]. The wrapper relies on the underlying orchestrator's `__main__` guards; no new enforcement needed. |

### Reproducibility-verifier branch

| # | Severity | Finding | Disposition |
|---|---|---|---|
| F-R-1 | critical | The sidecar emitted by the H050 v1 orchestrator includes a `config` block that records hypothesis ID + config path + smoke/dry-run/no-hmm-cache flags. The new `--invert-gate` flag MUST be persisted in the same provenance block to make the run distinguishable from H050 v1 in the ReproLog ecosystem. | REMEDIATED inline: added `invert_gate` to `_run_start_ctx` dict (line ~3083); the dict is logged in the PROGRESS run-start event + propagates to the sidecar. |
| F-R-2 | major | Substrate locality in this worktree: `data/processed/vendor_legacy_1min_roll_adjusted/` directory absent at branch checkout. Per CLAUDE.md Phase O.1 follow-on documented Path A, junction-link to the sibling `nervous-greider-90c8f0` worktree's directory was used. | DOCUMENTED — junction created via Windows `cmd /c mklink /J` at session start. Verified provenance JSON SHA256 = `317429e4...` (canonical post-Phase-O.10 substrate; matches H050_invert/design.md §16 binding). |
| F-R-3 | major | The H050.invert smoke run produces a new run_id; the orchestrator's `RunContext` writes the canonical 13-field ReproLog at `logs/reproducibility/{run_id}.json` per [CLAUDE.md §Reproducibility][5]. | VERIFIED — orchestrator unchanged on this code path. Provenance emission is bit-identical to H050 v1. |
| F-R-4 | minor | Smoke run wall-clock estimate (~15-30 min) anchored on operator prompt; actual wall-clock depends on HMM cold-fit + smoke-reduced grid + folds. Production-mode estimate ~7-8 hr per H050 v1 Phase G precedent. | NON-BLOCKING — smoke results are exploratory; canonical production run is operator-discretionary. |

### Format-auditor branch

| # | Severity | Finding | Disposition |
|---|---|---|---|
| F-F-1 | major | Pre-existing KPI report card v0 at [research/01_hypothesis_register/H050_invert/H050_invert_kpi_report_v0.md](../../research/01_hypothesis_register/H050_invert/H050_invert_kpi_report_v0.md) already conforms to the ADR-0026 §D-1 + ADR-0014 §3.2 + ADR-0019 §3 canonical format scaffolding. v1 KPI emission extends v0 with smoke results in the placeholder fields. | VERIFIED — v0 skeleton lands at pre-registration commit per the H062 + H055 + H060 + H065 v0 precedent. |
| F-F-2 | minor | Cross-link validity check across 4 documents: design.md → ADR-0027; KPI v0 → design.md + stage.md + failure_log.md; stage.md → design.md + parent investigation memo; this audit trail → all of the above. | VERIFIED — all cross-links resolve as relative paths from each document's directory. |
| F-F-3 | minor | No new ADR cross-link defects detected (no L1-001-class wrong-DOI / wrong-arXiv regression in any artifact landed in this phase). | VERIFIED — H050.invert design.md citations were validated at pre-registration commit `e81833c` 2026-05-20. |

## Round 1 verdict

**`accept-with-residuals`** per [SKILL.md][6] convention. All critical + load-bearing major findings remediated inline before commit. Round 2 verification posture: deferred to the smoke walk-forward execution itself — the smoke run empirically validates the gate-state inversion pipeline end-to-end. Round 3 verification deferred to first paper-trade evaluation per the [ADR-0017 R3 precedent][7].

## Empirical-prediction discriminant (load-bearing per parent INVESTIGATE memo §7.3)

Per the parent [INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM closure memo][2] §7.3 Variant A, operator review of H050.invert KPI v1 + the (forthcoming) H050.stable-state KPI v1 will discriminate H-b anti-selection vs H-c whipsaw empirically:

- **If H050.invert realized OOS basket > 0 (substantially)** → H-b anti-selection dominates the H050 v1 catastrophe (gate selected worse-Sharpe state). The inverted gate captures the better-Sharpe state and produces positive realized edge.
- **If H050.invert realized OOS basket ≈ H050 v1 (catastrophic negative)** → H-c whipsaw dominates. Inverting the gate sign does not help because the cost-drag from ~30% forced transition rate is direction-agnostic; both gated arms suffer the same whipsaw friction.
- **Intermediate** → mixture mechanism (both H-b and H-c contribute).

The discriminant is itself non-binding per [ADR-0013 §1 no-binding-gates][8]; operator-discretionary interpretation per the KPI report card v1 + sibling H050.stable-state KPI v1.

## Smoke run provenance

To be populated post-run-completion:

- **run_id**: `29eac562e2354b91acdb0f65a7198b00` (in-flight at audit-trail emission)
- **scientific_payload_sha256**: TBD on completion
- **substrate**: `data/processed/vendor_legacy_1min_roll_adjusted/` (junction-linked); SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`
- **git HEAD at launch**: `f665aefc422ca42efaf8603d10e4dc8e77e0aca8` (post-Phase-O.20 ADR-0028 first cost-friction-edge empirical emission merge)
- **CLI**: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run python scripts/run_h050_invert_walk_forward.py --smoke`

## Residuals (non-blocking; deferred to future follow-up commits)

- `P1-H050-INVERT-HMM-CACHE-CROSS-CONTAMINATION-DOC` — document the cross-run cache isolation property explicitly in the cache module docstring + the H050.invert orchestrator wrapper.
- `P1-H050-INVERT-REGIME-HIGH-MEAN-VARIABLE-RENAME-V2` — operator-discretionary polish; rename `regime_high_mean` → `regime_gate_state` across the H050 orchestrator codebase for clarity (the variable name is misleading under the inversion).
- `P1-H050-INVERT-PRODUCTION-RUN` — canonical full-production walk-forward via [scripts/supervised_run.py](../../scripts/supervised_run.py) (~7-8 hr wall-clock per H050 v1 Phase G precedent). Operator-discretionary timing.
- `P1-H050-INVERT-KPI-V2-FULL-RUN` — emit KPI report card v2 on full production walk-forward output; v1 is smoke-mode for ADR-0027 §D-3 empirical-before-cascade.
- `P1-H050-STABLE-STATE-ORCHESTRATOR` — sibling variant orchestrator + walk-forward; B variant of the paired mechanism-discrimination design per H050.invert design.md §12.

## Cross-references

- Parent investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md][2]
- H050.invert pre-registration: [research/01_hypothesis_register/H050_invert/design.md](../../research/01_hypothesis_register/H050_invert/design.md)
- H050.invert KPI report card v1: [research/01_hypothesis_register/H050_invert/H050_invert_kpi_report_v1.md](../../research/01_hypothesis_register/H050_invert/H050_invert_kpi_report_v1.md)
- Sibling H050.stable-state design: [research/01_hypothesis_register/H050_stable_state/design.md](../../research/01_hypothesis_register/H050_stable_state/design.md)
- ADR-0005 HMM regime toolkit: [docs/decisions/ADR-0005-hmm-regime-toolkit.md](../decisions/ADR-0005-hmm-regime-toolkit.md)
- ADR-0027 operational discipline + bounded exploration: [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md][1]
- audit-remediate-loop skill: `~/.claude/skills/audit-remediate-loop/SKILL.md`

[1]: ../decisions/ADR-0027-operational-discipline-bounded-exploration.md
[2]: ../../research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md
[3]: ../../research/01_hypothesis_register/H055/INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS.md
[4]: ../decisions/ADR-0009-blas-threading.md
[5]: ../../CLAUDE.md
[6]: https://github.com/anthropics/claude-skills/blob/main/audit-remediate-loop/SKILL.md
[7]: ../decisions/ADR-0017-survival-constrained-optimization-paradigm.md
[8]: ../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md
