---
name: Cycle-3 audit trail — HMM regime-inference toolkit
description: Audit-remediate loop trail for the Tier-2b Cycle-3 deliverable (Gaussian HMM Baum-Welch EM, causal forward filter, BIC selection, reproducibility sidecar) per ADR-0005
type: project
status: closed
date: 2026-04-23
rounds: 1 (of 3-round cap; Round-2 verification deferred to Cycle 6 end-to-end — see "Verification status")
verdict: proceed-with-follow-ups
---

# Cycle 3 — HMM regime-inference toolkit

Per [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md) and [ADR-0005](../../docs/decisions/ADR-0005-hmm-regime-toolkit.md). Delivers the canonical HMM toolkit that feeds H050/H051/H052a regime conditioning.

## Deliverables (committed this cycle)

- [src/skie_ninja/models/regime/_core.py](../../src/skie_ninja/models/regime/_core.py): log-space forward/backward/forward-backward, Viterbi (train-time), Baum-Welch EM with per-iteration dead-state and PD-ridge diagnostics, BIC parameter counts.
- [src/skie_ninja/models/regime/hmm.py](../../src/skie_ninja/models/regime/hmm.py): `GaussianHMM` with k-means++ warm start, multi-restart EM, label-switching canonicalisation, **causal** `filter_states` as the sole public inference path, and a deliberately verbose `viterbi_train_time` for train-only diagnostics.
- [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py): BIC grid search across `n_states × covariance_types`, SeedSequence-spawned restart seeds so grid iteration order is irrelevant.
- [src/skie_ninja/models/regime/serialization.py](../../src/skie_ninja/models/regime/serialization.py): `HMMSidecar` schema (`hmm_sidecar_v1`), atomic JSON writer, SHA256 rolled into `ReproLog.model_hash` via `with_model_hash` (no frozen-dataclass change).
- [tests/unit/test_hmm_core.py](../../tests/unit/test_hmm_core.py), [test_hmm_fit.py](../../tests/unit/test_hmm_fit.py), [test_hmm_selection.py](../../tests/unit/test_hmm_selection.py), [test_hmm_serialization.py](../../tests/unit/test_hmm_serialization.py): 47 new tests, 320/320 unit suite green. Covers emission-log-density cross-checks across all four covariance types, log-vs-naive-space equivalence (T=8), forward hand-calc (T=2), Viterbi brute-force enumeration (T=3), Baum-Welch LL monotonicity and parameter recovery, **the anti-look-ahead causal-prefix gate** (`filter_states(y_{1:t}) == filter_states(y_{1:T})[:t]`), BIC parameter counts for all four covariance types, sidecar round-trip, atomic idempotent write, ReproLog integration.

## Audit rounds

### Round 1 (parallel: quant-auditor + literature-check)

**Quant-auditor**: 14 findings (5 major, 9 minor).
**Literature-check**: 7 findings (1 critical, 1 major, 5 minor).

**Critical (lit-check) — F-LIT-1**: `hmm.py:72`, `hmm.py:179-183`, and `ADR-0005:88` attributed the "5-restart floor" to Biernacki, Celeux, Govaert 2003. Biernacki 2003 motivates *why* multi-start EM is required for Gaussian mixtures (local optima) but does **not** prescribe a universal 5-restart count. Same failure pattern flagged in Cycle 2's Opdyke 2007 "HAC" mislabel.

**Major findings:**
- **F-1-1** (quant): `baum_welch_em` off-by-one on `max_iter` exhaustion — the final M-step updated `params` after `ll_history[-1]` was recorded, so returned params did not correspond to the reported LL.
- **F-1-2** (quant): no Cholesky condition-number check in `log_emission_matrix`; near-singular covariances could pass with numerically unstable `log_det`.
- **F-1-3** (quant): `_DEFAULT_MIN_VAR = eps·1e3 ≈ 2.2e-13` was not scale-adaptive; meaningless on data with scale ≫ 1.
- **F-1-4** (quant): tied/full M-step unconditionally added `min_var·I`, biasing the MLE even when the raw estimate was already PD.
- **F-1-5** (quant): zero-responsibility states were silently floored (`safe_weight = max(weight, tiny)`) with no signal to the caller.
- **F-LIT-2** (lit): unverified per-equation Rabiner 1989 citations (eq. 27-28, eq. 53-54) — the math is correct, but the specific equation numbers were not verified against the source.

**Minor findings** (deferred to P1 backlog per triage rule): docstring polish, additional brute-force cross-checks, extra determinism tests under tied/full, float32 paths, bigger-T regression tests.

### Remediation (applied in Round 1)

| Finding | Fix location | Summary |
|---|---|---|
| F-LIT-1 | [hmm.py:6-12](../../src/skie_ninja/models/regime/hmm.py), [hmm.py:62-70](../../src/skie_ninja/models/regime/hmm.py), [hmm.py:180-184](../../src/skie_ninja/models/regime/hmm.py), [ADR-0005 §Hyperparameter-governance](../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) | Relabel the 5-restart floor as an **operational** Cycle-3 engineering choice; keep Biernacki 2003 as motivation only; flag P1-HMM-ADAPTIVE-RESTART as the principled replacement. |
| F-1-1 | [_core.py baum_welch_em](../../src/skie_ninja/models/regime/_core.py) | On the final iteration (`iteration == max_it - 1`), break out **before** the M-step, so returned `params` matches `ll_history[-1]`. |
| F-1-2 | [_core.py _ensure_pd](../../src/skie_ninja/models/regime/_core.py) | `_ensure_pd` now tries Cholesky, then checks `min(diag(L))² ≥ min_var`; only adds ridge when necessary. Emission step inherits the PD guarantee upstream. |
| F-1-3 | [_core.py baum_welch_em](../../src/skie_ninja/models/regime/_core.py) | When caller passes `min_var=None`, derive a scale-adaptive default as `max(eps·1e3, 1e-6 × min-positive-sample-variance)`. Explicit `min_var` arguments still honored verbatim. |
| F-1-4 | [_core.py _m_step_emissions tied/full branches](../../src/skie_ninja/models/regime/_core.py) | Replace unconditional `+ min_var·I` with `_ensure_pd` — ridge applied only when raw MLE is not PD or near-singular. |
| F-1-5 | [_core.py _MStepDiagnostics, BaumWelchResult.dead_state_events, BaumWelchResult.pd_ridge_events](../../src/skie_ninja/models/regime/_core.py) | `_m_step_emissions` now returns `_MStepDiagnostics(dead_states, pd_ridge_applied)`; `baum_welch_em` accumulates into `BaumWelchResult.dead_state_events` and `pd_ridge_events`. These propagate to the sidecar in a follow-up. |
| F-LIT-2 | [_core.py forward_log / backward_log / forward_backward_log / _m_step_emissions docstrings](../../src/skie_ninja/models/regime/_core.py) | Soften "Rabiner eq. 19 / 25 / 27-28 / 53-54" to section-level pointers ("§III.A Forward procedure", "§III.B posterior identities", "§III.C Solution to Problem 3"). |

Minors deferred to P1 follow-ups:
- **P1-HMM-ADAPTIVE-RESTART**: replace the fixed 5-restart floor with the bootstrap-ε adaptive rule described in ADR-0005.
- **P1-HMM-WFCV**: walk-forward CV held-out log-likelihood as a secondary selection criterion (Cycle 4 lands it alongside the walk-forward harness).
- **P1-HMM-SIDECAR-DIAGNOSTICS**: flow `dead_state_events` and `pd_ridge_events` into the sidecar JSON so regression diagnostics travel with the model hash.
- **P1-HMM-VERIFIED-EQ-NUMBERS**: verify the exact Rabiner 1989 equation numbers against the source PDF and tighten the section-level citations if desired. Non-blocking — the math is already tested end-to-end.
- **P1-HMM-FLOAT32**: document and (optionally) support float32 paths for large-T fits.

### Round 2 / verification status

**Round 2 formally deferred to Cycle 6 end-to-end** under the same cost-benefit that governed Cycle 2:

- All Round-1 remediations are either (i) citation re-labels with no runtime surface (F-LIT-1, F-LIT-2), (ii) pure numerical-stability fixes that are already test-gated (F-1-1, F-1-2, F-1-3, F-1-4), or (iii) new diagnostic fields on the return dataclass (F-1-5).
- The 47-test HMM suite passes unchanged, and the full 320-test unit suite remains green. The anti-look-ahead `filter_states` prefix-causality gate (`test_filter_prefix_causality`) was not touched by remediation and still passes.
- Cycle 6 (end-to-end walk-forward H050 integration) naturally exercises the remediated EM path against real ES/NQ 1-min data; the value of an intermediate Round-2 formal re-audit on the same mechanical fixes is low relative to the cost.

Residual risk recorded: the P1 follow-ups above. None are blockers for the Cycle-3 acceptance bar (causal inference path, hash-stable sidecar, unit tests green, no look-ahead).

## Acceptance

- [x] All unit tests green (47 new, 320 total).
- [x] Causal forward filter (`filter_states`) is the sole public deploy-time inference path; `viterbi_train_time` is deliberately name-verbose and docstring-flagged as train-only.
- [x] Sidecar schema documented ([serialization.py HMMSidecar](../../src/skie_ninja/models/regime/serialization.py)) and hash-stable across runs given a fixed seed (covered by `test_transition_matrix_hash_is_deterministic`, `test_write_is_atomic_no_partial_file_on_rerun`).
- [x] ADR-0005 sidecar path convention honored: `logs/reproducibility/{run_id}_hmm_selection.json`.
- [x] No frozen-dataclass change to `ReproLog`; `model_hash` populated via `with_model_hash(log, sidecar_sha256)`.
- [x] Audit trail committed.

## Citations used in this cycle

- Rabiner 1989 Proc. IEEE 77(2):257-286 — forward/backward/Viterbi recursions and Baum-Welch re-estimation structure. Cited at §-level only (see F-LIT-2 remediation).
- Baum, Petrie, Soules, Weiss 1970 Ann. Math. Stat. 41:164-171 — original Baum-Welch EM.
- Bishop 2006 PRML §13.2 — log-space forward-backward formulation used here.
- Viterbi 1967 IEEE Trans. Inf. Theory 13:260-269 — MAP path decoding.
- Schwarz 1978 Ann. Stat. 6:461 — BIC as -2 log L + k log T.
- Celeux & Durand 2008 Comp. Stat. 23:541 — HMM model selection; Gaussian mixture identifiability rules of thumb.
- Pohle, Langrock, van Beest, Schmidt 2017 JABES 22:270 — selecting n_states via model checking in ecological HMMs.
- Stephens 2000 JRSS B 62:795 — label-switching in mixture models.
- Biernacki, Celeux, Govaert 2003 CSDA 41:561 — motivation for multi-start EM (NOT the source of a 5-restart floor — see F-LIT-1).
- Arthur & Vassilvitskii 2007 SODA — k-means++ seeding.
