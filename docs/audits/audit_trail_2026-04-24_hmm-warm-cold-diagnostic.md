---
title: P1-HMM-WARM-COLD-DIAGNOSTIC — audit-remediate-loop trail
date: 2026-04-24
artifact: WarmColdDiagnostic + Hellinger/TV primitives + sidecar + walk-forward wiring
followup_id: P1-HMM-WARM-COLD-DIAGNOSTIC
exit_state: round-2 accept (5 minor residuals; 3 inline-resolved, 2 follow-ups)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
---

## Scope

Close `P1-HMM-WARM-COLD-DIAGNOSTIC` (residual F-1-9 of [audit_trail_2026-04-24_hmm-fold-warm-start.md](audit_trail_2026-04-24_hmm-fold-warm-start.md)). The brief: implement a per-fold regression-detection diagnostic capturing the divergence between the production warm-start posterior (`GaussianHMM.filter_states_from_prior`) and the cold-start regression baseline (`GaussianHMM.filter_states`); emit a sidecar JSON, hash its SHA256 into `ReproLog.model_hash` via `with_model_hash` matching the [HMMSidecar](../../src/skie_ninja/models/regime/serialization.py) pattern; deterministic and causal.

## Method-fidelity anchor

The divergence metric is the **Hellinger distance** between per-bar warm and cold filtered posteriors, normalised as `H = (1/√2)·||√p − √q||₂` so `H ∈ [0, 1]` ([Le Cam 1986, *Asymptotic Methods in Statistical Decision Theory*, Springer ISBN 978-1-4612-9343-3, §15](https://doi.org/10.1007/978-1-4612-4946-7); [Tsybakov 2009, *Introduction to Nonparametric Estimation*, Springer ISBN 978-0-387-79051-0, §2.4](https://doi.org/10.1007/b13794)). Hellinger over symmetric KL ([Kullback & Leibler 1951, *Ann. Math. Stat.* 22(1):79-86](https://doi.org/10.1214/aoms/1177729694)) because near-deterministic transition matrices — exactly the slow-mixing regime where the warm-cold gap is largest and most worth detecting — make KL diverge to ∞ ([Cover & Thomas 2006, *Elements of Information Theory*, 2nd ed., Wiley ISBN 978-0-471-24195-9, §2.3](https://doi.org/10.1002/047174882X)). Total-variation distance is emitted as a secondary metric; the Tsybakov 2009 Lemma 2.3 (eq. 2.20) envelope `H² ≤ TV ≤ H·√(2 − H²)` (substituting under the bounded normalisation) is asserted on every fold's `le_cam_envelope_holds` flag as a deterministic float64 sanity check.

Causality: at each fold boundary, both paths consume only what they would normally read — the cold path reads the test-fold observations (and the fitted `log π`), the warm path reads the test-fold observations *and* the train-fold terminal posterior `α_T_train` (itself a function only of the train observations). No future test-fold information is read by either path. The diagnostic is a *passive observer*; the production output of `_predict_fold` is unconditionally the warm-start posterior, the cold path is computed only inside the diagnostic branch and discarded after summary statistics are extracted (see [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) `_predict_fold`).

Threshold rule: emit raw values per [~/.claude/CLAUDE.md](C:\Users\skoir\.claude\CLAUDE.md) "Parameter & Prompt Selection" prohibition on arbitrary thresholds. No published threshold rule for HMM warm-vs-cold filter divergence located in literature search across Hamilton 1989/1994, Kim & Nelson 1999, Frühwirth-Schnatter 2006, López de Prado 2018, Le Cam 1986, Tsybakov 2009. Future calibration to a per-fold null reference (no-purge K=0 agreement under shared seed → exact equality up to float-noise → bootstrap z-scores) deferred to a future ADR if the rule becomes load-bearing; tracked as `P1-HMM-WARM-COLD-THRESHOLD-ADR`.

## Round-1

### Implementation summary

- [src/skie_ninja/models/regime/diagnostics.py](../../src/skie_ninja/models/regime/diagnostics.py) (NEW): `hellinger_distance_rows`, `total_variation_rows`, `WarmColdFoldRecord` (frozen), `WarmColdDiagnostic` (collector with `observe_fold`), `compute_warm_cold_posteriors` (convenience wrapper), `sidecar_path_for`, `write_sidecar` (atomic — same tempfile + fsync + `os.replace` pattern as [HMMSidecar.write_sidecar](../../src/skie_ninja/models/regime/serialization.py)). Schema version `warm_cold_diagnostic_v1`.
- [src/skie_ninja/models/regime/__init__.py](../../src/skie_ninja/models/regime/__init__.py): public re-exports — `WarmColdDiagnostic`, `WarmColdFoldRecord`, `compute_warm_cold_posteriors`, `hellinger_distance_rows`, `total_variation_rows`, `warm_cold_sidecar_path_for`, `write_warm_cold_sidecar`.
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py): `_predict_fold` accepts optional `warm_cold_diagnostic` + `fold_id_counter` kwargs (default `None` so callers ignoring the diagnostic suffer no behaviour change); when supplied, computes cold posterior in addition to warm and calls `observe_fold`. Production output remains warm. `run()` instantiates `WarmColdDiagnostic`, threads it through `predict_kwargs`, writes the sidecar at run end, combines its SHA256 with the per-fold ledger roll-up into a single `ReproLog.model_hash` via `hashlib.sha256("ledger_rollup={H1};warm_cold_diag={H2}")`.
- [tests/unit/test_hmm_warm_cold_diagnostic.py](../../tests/unit/test_hmm_warm_cold_diagnostic.py) (NEW): 18 unit tests — pointwise closed-form values (orthogonal supports H=1, uniform vs delta, identical rows), Tsybakov 2.3 inequality property test, K=0 zero-divergence collapse, slow-mixing non-zero divergence, K-monotonicity sanity, validation guards, deterministic round-trip, sidecar SHA256 round-trip, regression-flips-hash, ReproLog `with_model_hash` round-trip.

### Round-1 self-audit findings (quant + lit lenses)

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| F-1-1 | critical | diagnostics.py module docstring + `observe_fold` | Documented Le Cam inequality `H²/2 ≤ TV ≤ H` is incorrect under the bounded-Hellinger normalisation `H = (1/√2)·||√p − √q||₂`. Counter-example `p=(0.99, 0.01), q=(0.01, 0.99)`: TV ≈ 0.98 > H ≈ 0.895, so `TV ≤ H` fails. The correct bound (Tsybakov 2009 Lemma 2.3 eq. 2.20, substituted) is `H² ≤ TV ≤ H·√(2 − H²)`. Failed both the property test and the random-Dirichlet `le_cam_envelope_holds` assertion. | Round-2 fix: docstring corrected with substitution derivation; `observe_fold` envelope updated; tests updated; counter-example added to property test. |
| F-1-2 | major | `test_non_zero_divergence_under_slow_mixing_warm_start` | Test fitted a real HMM with strong emission separation (μ gap = 3, σ = √0.4 ≈ 0.63 → Bayes-error per bar ≈ 1%) so warm and cold posteriors converge within 1-2 bars and mean Hellinger over 200 bars is dominated by the converged region. Returned `1.06e-5` against a `> 1e-3` threshold. | Round-2 fix: switched to a synthetic setup with weak separation (μ gap = 1, σ = 1 → Bayes-error ≈ 30%) and near-identity transitions; assert first-bar Hellinger > 1e-2 instead of mean Hellinger > 1e-3 — the warm-cold gap is largest at K-step propagation, not averaged. |
| F-1-3 | major | ADR-0005 implementation contract | Diagnostic adds a new sidecar that contributes to `model_hash`; this is part of the methodology's reproducibility contract and ADR-0005 §"Implementation contract" should reference it. | Round-2 fix: added "Warm-vs-cold filter regression diagnostic" subsection under Implementation contract citing Le Cam 1986 §15 + Tsybakov 2009 §2.4 + Kullback-Leibler 1951 + Cover-Thomas 2006 §2.3 + the threshold-rule rationale; added all four to the ADR reference list. |
| F-1-4 | minor | `_predict_fold` `fold_id_counter` | Mutable list-as-counter passed via kwargs is fragile (call ordering assumption: engine processes folds in fold_id order). The `WalkForwardEngine.run` source confirms ordering, but the predict_fn signature does not advertise the contract. | Round-2: docstring extended on `_predict_fold` to flag the assumption; alternative (engine passing fold_id explicitly) deferred as `P1-WF-ENGINE-FOLD-ID-PASSTHROUGH`. |
| F-1-5 | minor | `compute_warm_cold_posteriors` | Convenience wrapper not used by the orchestrator (the orchestrator inlines the warm + cold filter calls). Either delete or leave as a public convenience. | Inline-resolved: kept as public convenience; the unit-test suite uses it as a smoke check (`test_compute_warm_cold_posteriors_returns_consistent_shapes`) so removing it would silently delete a contract surface. |
| F-1-6 | minor | hashing combiner | `hashlib.sha256("ledger_rollup={H1};warm_cold_diag={H2}")` is bespoke; a future third sidecar would need this combiner extended. | Logged residual; acceptable for now — when a third sidecar lands, refactor to a `roll_up_sidecar_hashes(name_to_sha)` helper. Tracked as `P1-MODEL-HASH-MULTI-SIDECAR-HELPER`. |
| F-1-7 | minor | `n_propagation_steps` redundant fields | `WarmColdFoldRecord` stores `n_propagation_steps`, `train_terminal_position`, `test_first_position` even though `n_propagation_steps == test_first_position − train_terminal_position` is invariant by construction. | Inline-resolved: redundancy is intentional — auditor reads the sidecar without re-running and can verify the ADR-0005 K-step formula by inspection rather than by trust. Documented in the diagnostic module. |

## Round-2

### Remediations applied

- **F-1-1 (critical):** [diagnostics.py](../../src/skie_ninja/models/regime/diagnostics.py) Hellinger / TV envelope corrected. The new bound `H² ≤ TV ≤ H·√(2 − H²)` is asserted in `observe_fold._le_cam_envelope_holds`. Module docstring "Total-variation distance" subsection rewritten with the Tsybakov 2009 Lemma 2.3 (eq. 2.20) substitution derivation, including the counter-example `p=(0.99, 0.01), q=(0.01, 0.99)` showing why naive `TV ≤ H` fails under the normalised metric.
- **F-1-2 (major):** [test_hmm_warm_cold_diagnostic.py](../../tests/unit/test_hmm_warm_cold_diagnostic.py) `test_non_zero_divergence_under_slow_mixing_warm_start` rewritten to use a synthetic forward-recursion setup with deliberately weak separation and a strongly biased prior; asserts first-bar Hellinger > 1e-2.
- **F-1-3 (major):** [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md) §"Implementation contract" extended with "Warm-vs-cold filter regression diagnostic" paragraph; reference list extended with Le Cam 1986, Tsybakov 2009, Kullback-Leibler 1951, Cover-Thomas 2006.
- **F-1-4 (minor):** `_predict_fold` docstring updated to make the engine fold-ordering assumption explicit (the engine's `WalkForwardResult` documents per-fold ordering; the counter mirrors it). New follow-up `P1-WF-ENGINE-FOLD-ID-PASSTHROUGH` for a cleaner refactor where the engine passes `fold_id` directly.
- **F-1-5, F-1-7 (minor):** Inline-resolved, see Round-1 table.
- **F-1-6 (minor):** Tracked as `P1-MODEL-HASH-MULTI-SIDECAR-HELPER`.

### Round-2 self-audit findings

| ID | Severity | Location | Issue | Disposition |
|---|---|---|---|---|
| F-2-1 | minor | diagnostics.py docstring | Le Cam 1986 §15 is the correct chapter ("Hellinger Distances. Variations and Hellinger Transforms"); the Springer DOI `10.1007/978-1-4612-4946-7` is the published version (1986). ✓ | Verified — no change. |
| F-2-2 | minor | sidecar JSON schema | `metric_reference` field hardcoded to a string concatenating two DOIs; not machine-parseable. | Logged residual; a structured `metric_reference: {primary: {citation, doi}, ...}` would help an auditor cross-link to Zenodo metadata. Tracked as `P1-WARM-COLD-SIDECAR-STRUCTURED-CITATIONS`. |
| F-2-3 | minor | empty fold guard | `observe_fold` rejects `T == 0` test folds; the orchestrator's predict_fn would never be called with T=0 (`WalkForwardEngine` filters), but the guard is cheap and correct. | Verified — no change. |

### Test posture

```
tests/unit/test_hmm_warm_cold_diagnostic.py ..................        [100%]
tests/unit/test_hmm_fold_warm_start.py .............                  [100%]
tests/unit/test_orchestrator_smoke.py .                               [100%]
================== 32 passed, 66 warnings in 66.54s ===================
```

(Run command: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run python -m pytest tests/unit/test_hmm_warm_cold_diagnostic.py tests/unit/test_hmm_fold_warm_start.py tests/unit/test_orchestrator_smoke.py -q`. Full-suite execution deferred to a separate agent per the task brief.)

## Exit decision

Exit Round-2 with `accept` verdict per [audit-remediate-loop](file:///C:/Users/skoir/.claude/skills/audit-remediate-loop/SKILL.md) §"Exit check": Round-2 findings have no critical or major items; F-2-1 verified, F-2-2 logged as follow-up, F-2-3 verified. Round-3 not warranted.

## Residual risk

1. **Threshold rule deferred.** Diagnostic publishes raw values; a future regression that subtly biases the warm-start (e.g. a transition-matrix corruption that flattens but does not zero the warm-cold gap) would surface as a change in the sidecar SHA256 (and therefore in `ReproLog.model_hash`) but would not produce a "fail" verdict in CI without a calibrated threshold. The CI consumer can compare against a baseline `warm_cold_diagnostic.json` from a known-good run; the sidecar SHA256 round-trip suffices for the regression-detection contract demonstrated by `test_sidecar_changes_hash_on_warm_cold_regression`. Tracked as `P1-HMM-WARM-COLD-THRESHOLD-ADR`.
2. **Multi-sidecar combiner is bespoke** (F-1-6). Tracked as `P1-MODEL-HASH-MULTI-SIDECAR-HELPER`.
3. **Engine fold_id pass-through** (F-1-4). Tracked as `P1-WF-ENGINE-FOLD-ID-PASSTHROUGH`.
4. **Structured citations in sidecar** (F-2-2). Tracked as `P1-WARM-COLD-SIDECAR-STRUCTURED-CITATIONS`.

## Cited references

- Le Cam, L. M. (1986). *Asymptotic Methods in Statistical Decision Theory*. Springer-Verlag, ISBN 978-1-4612-9343-3, §15. https://doi.org/10.1007/978-1-4612-4946-7
- Tsybakov, A. B. (2009). *Introduction to Nonparametric Estimation*. Springer, ISBN 978-0-387-79051-0, §2.4. https://doi.org/10.1007/b13794
- Kullback, S., & Leibler, R. A. (1951). "On information and sufficiency". *Annals of Mathematical Statistics* 22(1):79-86. https://doi.org/10.1214/aoms/1177729694
- Cover, T. M., & Thomas, J. A. (2006). *Elements of Information Theory*, 2nd ed. Wiley, ISBN 978-0-471-24195-9, §2.3. https://doi.org/10.1002/047174882X
- Hamilton, J. D. (1989). "A new approach to the economic analysis of nonstationary time series and the business cycle." *Econometrica* 57(2):357-384, §3. https://doi.org/10.2307/1912559
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley, ISBN 978-1-119-48208-6, §7.4.1.

## Lint cleanup (post-Round-2)

`ruff check` (project pin v0.6.9; rules `E/F/I/N/B/UP/SIM/PL`) flagged 17 net new violations introduced by this work. All resolved without behavioural change; 18/18 unit tests still green; baselines preserved (`scripts/run_walk_forward.py` stays at 32 pre-existing errors).

Source-level fixes (no suppression):

- [src/skie_ninja/models/regime/diagnostics.py](../../src/skie_ninja/models/regime/diagnostics.py)
  - 3× PLR2004 `ndim != 2` → introduced module-level `_EXPECTED_POSTERIOR_NDIM = 2` with a one-line shape-contract comment; replaced all three call sites.
  - 1× SIM115 `tempfile.NamedTemporaryFile(...)` opened without context manager → wrapped in `with` block; captured `tmp.name` inside the block so `os.replace` after close still has the path.
- [tests/unit/test_hmm_warm_cold_diagnostic.py](../../tests/unit/test_hmm_warm_cold_diagnostic.py)
  - 6× PLC0415 in-function imports (`scipy.special.logsumexp`, `skie_ninja.models.regime._core.{forward_log, forward_log_from_prior, log_emission_matrix}`, `hashlib`, `skie_ninja.utils.reproducibility.{ReproLog, with_model_hash}`) → hoisted all to module top. None were lazy fixtures; all are stdlib or in-project modules with negligible import cost.
  - 3× PLR2004 magic numbers (`> 1e-2`, `len(sha) == 64`, `n_folds == 3`) → introduced module-level constants `_FIRST_BAR_HELLINGER_FLOOR`, `_SHA256_HEX_LEN`, `_DIAG_RUN_N_FOLDS` (the floor's commented as a sanity floor 10 orders of magnitude above the regression-collapse target, not a tunable threshold).
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py)
  - 1× PLC0415 `import hashlib as _hashlib` inside `run()` → hoisted `import hashlib` to the stdlib import block at the file top; renamed call site `_hashlib.sha256(...)` → `hashlib.sha256(...)`.

`# noqa` suppressions (1 total):

| File | Rule | Site | Justification |
|---|---|---|---|
| [tests/unit/test_hmm_warm_cold_diagnostic.py](../../tests/unit/test_hmm_warm_cold_diagnostic.py) `_filter_warm` | N803 (uppercase argument) | `def _filter_warm(K: int)` | `K` matches [ADR-0005](../decisions/ADR-0005-hmm-regime-toolkit.md) §"Fold-boundary state continuity" mathematical notation for the `(A^K)` prior-propagation operator (`n_propagation_steps=K`). Renaming to `k` would lose the cross-reference to the ADR's K-step formula; literature-convention exemption per [~/.claude/CLAUDE.md](C:\Users\skoir\.claude\CLAUDE.md) "Parameter & Prompt Selection" intent that names mirror cited methodology. |

Verification:

```
ruff check src/skie_ninja/models/regime/diagnostics.py tests/unit/test_hmm_warm_cold_diagnostic.py scripts/run_walk_forward.py src/skie_ninja/models/regime/__init__.py
```

→ 32 errors total (baseline preserved on `run_walk_forward.py`; new files `diagnostics.py` and `test_hmm_warm_cold_diagnostic.py` ruff-clean). 18/18 warm-cold-diagnostic unit tests pass under the documented BLAS-pin env (`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`).
