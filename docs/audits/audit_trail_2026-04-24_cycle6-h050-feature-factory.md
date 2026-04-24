---
name: Cycle-6 audit trail — H050 feature factory + walk-forward orchestrator
description: 3-round audit-remediate trail for Tier-2b Cycle 6 deliverables (Yang-Zhang labels, microstructure feature modules, NT8 cost model, walk-forward orchestrator)
type: project
status: closed
date: 2026-04-24
rounds: 3 (cap reached)
verdict: proceed-with-documented-blocking-follow-ups
---

# Cycle 6 — H050 feature factory + walk-forward orchestrator

Per [plan/tier2b_buildout_2026-04-23.md](../../plan/tier2b_buildout_2026-04-23.md). Delivers the H050-specific triple-barrier label engine, four microstructure feature modules, NT8 cost model, and the Phase-A walk-forward orchestrator composition.

## Deliverables (committed this cycle)

- [src/skie_ninja/features/labels.py](../../src/skie_ninja/features/labels.py): Yang-Zhang vol + triple-barrier labels (`TripleBarrierLabeler`, `TripleBarrierConfig`, `TripleBarrierLabel`)
- [src/skie_ninja/features/microstructure/rv_parkinson.py](../../src/skie_ninja/features/microstructure/rv_parkinson.py): Parkinson (1980) RV feature
- [src/skie_ninja/features/microstructure/rv_realized.py](../../src/skie_ninja/features/microstructure/rv_realized.py): Realized variance (Andersen & Bollerslev 1998)
- [src/skie_ninja/features/microstructure/realized_skew.py](../../src/skie_ninja/features/microstructure/realized_skew.py): Realized skew (Neuberger 2012)
- [src/skie_ninja/features/microstructure/ofi_tickrule.py](../../src/skie_ninja/features/microstructure/ofi_tickrule.py): OFI tick-rule proxy (Lee & Ready 1991 / Easley et al. 2012 BVC fallback)
- [src/skie_ninja/features/base.py](../../src/skie_ninja/features/base.py): `FeatureTestBase` contractual-guarantee test mixin
- [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py): NT8 ES/NQ RTH cost model
- [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py): Phase-A walk-forward orchestrator
- [research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md): frozen dataset checksums
- [config/hypotheses/H050.yaml](../../config/hypotheses/H050.yaml): hypothesis config (hansen_spa, cost_model, random_seed)
- [docs/decisions/ADR-0007-embargo-placement.md](../../docs/decisions/ADR-0007-embargo-placement.md): stacked embargo form ADR
- [docs/decisions/ADR-0008-spa-omega-method.md](../../docs/decisions/ADR-0008-spa-omega-method.md): SPA omega method ADR

---

## Round 1 audit (2026-04-24)

### Auditors
quant-auditor + literature-check + reproducibility-verifier (parallel)

### Findings

| ID | Sev | Location | Issue |
|----|-----|----------|-------|
| R1-L-5 | critical | `features/labels.py:111` | Yang-Zhang k formula wrong: `alpha=1.34` → k≈0.659 at N=60; correct is `k=0.34/(1.34+(N+1)/(N-1))`≈0.143 |
| R1-F-1-5 | major | `microstructure/ofi_tickrule.py` | OFI returned raw signed-volume sum, not normalized; scale-dependent across symbols |
| R1-F-1-9 | major | `scripts/run_walk_forward.py:215` | `r_bar[0]=0` (construction zero) passed to HMM without masking, biasing emission means |
| R1-L-8 | major | `ADR-0007:43` | "Snippet 7.3" should be "Snippet 7.1" per mlfinlab canonical |
| R1-L-6 | major | `ADR-0008:54-55` | §2.2 → §3 for Hansen 2005 bootstrap implementation reference |
| R1-Repro | critical | provenance JSON | `output_frame_sha256` absent; `_load_output_sha256` would fall back to pre-adjustment hash |
| R1-OFI-test | major | `test_features_microstructure.py:171-172` | Test expected raw sums (900.0/1000.0) not normalized ratios (0.9/1.0) |

### Dispositions
All critical and major findings remediated in commit `e1977ed`. Twelve additional minor findings downgraded per the 3-round triage rule.

---

## Round 2 audit (2026-04-24)

### Auditors
quant-auditor + literature-check + reproducibility-verifier (parallel)

### Findings

| ID | Sev | Location | Issue |
|----|-----|----------|-------|
| R2-F-2-1 | major | `ofi_tickrule.py:190-196` | `signed_vol_sum / total_vol_sum` produces float NaN (not polars null) on zero-volume windows; `drop_nulls()` does not catch float NaN |
| R2-F-2-2 | major | `features/base.py:315-327` | `test_no_silent_nan` uses `null_count()` only; misses float NaN in Float64 columns |
| R2-F-2-3 | major | `run_walk_forward.py:635` | Hard-coded threshold `4` for OOS CI gate has no empirical justification |
| R2-F-2-4 | minor | `labels.py:299-302` | Simultaneous-hit comment incorrectly cites "AFML Snippet 3.2 tie-break" |
| R2-F-2-6 | minor | `run_walk_forward.py:643` | No logging.warning when gate is skipped (silent degenerate fallback) |
| R2-L-3/L-4 | minor | `labels.py:69-75` | Removed unverified portfoliooptimizer.io citation; TTR cross-check docstring corrected; added JSTOR 403 gap note |
| R2-L-6 | minor | `ADR-0008:48` | Table row still said "§2 explicitly recommends" after prior §2.2→§3 fix |

### Dispositions
F-2-1 through F-2-2 (critical flow path): remediated. F-2-3, F-2-4, F-2-6, L-3/L-4, L-6: all remediated. Committed `73a2c1c`.

---

## Round 3 audit (2026-04-24)

### Auditors
quant-auditor + literature-check + reproducibility-verifier (parallel)

### Findings

| ID | Sev | Location | Issue | Disposition |
|----|-----|----------|-------|-------------|
| R3-F-3-1 | major | `run_walk_forward.py:_predict_fold` | HMM `filter_states` restarts from `log_pi` at each fold boundary; terminal posterior not threaded; warm-up bias O(dwell_time) bars | Documented inline; follow-up **P1-HMM-FOLD-WARM-START** promoted to blocking before evidence-bar execution |
| R3-F-3-2 | major | `run_walk_forward.py:234` | Magic threshold `10` in `valid_mask` gate for HMM — no empirical justification | Replaced with `_MIN_VALID_RETURNS_FOR_MASK = 2` with inline justification (structural guard, not tunable) |
| R3-F-3-3 | major | `run_walk_forward.py:529-535` | Split params `n//3`/`n//10` not derived from H050.yaml pre-registered date boundaries; fold boundaries not reproducible under dataset updates | Comment upgraded to BLOCKING; **P1-H050-SPLIT-PARAMS** promoted to blocking before evidence-bar |
| R3-Repro-1 | major | `vendor_legacy_1min_roll_adjusted.py:emit_provenance` | `output_frame_sha256` never written by code; file was manually patched in R1; re-ingest would lose field | Fixed in `emit_provenance`: output parquet SHA computed after write, added to payload and `add_dataset_checksum` |
| R3-F-3-Lit | minor (×6) | various | Documentation precision gaps: Lo 2002 / Opdyke 2007 n=30 framing mixes sourced theory with unsourced floor; Hansen 2005 coupling-bias characterization exceeds paper's stated results; paywall gaps for YZ eq.8 and Lee-Ready §III.A | All downgraded per 3-round triage rule; JSTOR/paywall gap notes already present in code |

### Dispositions
F-3-2 and Repro-1 remediated in code. F-3-1 and F-3-3 documented with blocking follow-up tags; architectural fix deferred (non-trivial for Phase-A composition). All minor lit findings downgraded. Committed `06f0402`.

---

## Residual risk (post Round 3)

**Blocking before evidence-bar run** (documented, not affecting Phase-A composition smoke test):

1. **P1-HMM-FOLD-WARM-START** — HMM filter_states restarts from `log_pi` at each fold boundary. For slow-mixing regimes the warm-up distortion spans O(dwell_time) bars. Must implement `filter_states_from_prior(x, log_alpha_init)` accepting the terminal training-fold posterior.

2. **P1-H050-SPLIT-PARAMS** — Walk-forward fold boundaries derived from `n//3`/`n//10` instead of H050.yaml pre-registered date ranges. Fold boundaries are not reproducible under dataset updates. Must parse `data.train/val/test` Timestamps from H050.yaml before evidence-bar execution.

3. **P1-H050-INNER-CV** — LightGBM in-sample HP selection (no inner purged walk-forward CV). Must replace with Varma & Simon 2006 purged inner fold per CLAUDE.md evidence bar.

**Known long-term gaps** (not blocking Phase-A):

- Yang & Zhang 2000 eq. 8 (JSTOR 403): α=0.34 cross-checked via TTR R package; primary source unverifiable until licensed access available.
- Lee & Ready 1991 §III.A sub-label: substance confirmed via secondary literature; primary source paywalled.
- P1-OPDYKE-FULL-GMM: current Opdyke 2007 implementation uses scalar-HAC-ratio approximation, not full moment-vector GMM.

---

## Test coverage

54 unit tests passing (features/labels, microstructure, base, backtest costs). No regressions.

## Commits

| SHA | Description |
|-----|-------------|
| `7e0c496` | feat(cycle6): initial Cycle 6 deliverables (26 files, 4453 insertions) |
| `e1977ed` | fix(cycle6-r1): Round-1 audit remediations |
| `73a2c1c` | fix(cycle6-r2): Round-2 audit remediations (F-2-1 through F-2-6, L-3/L-4/L-6) |
| `06f0402` | fix(cycle6-r3): Round-3 audit remediations (F-3-1/F-3-2/F-3-3 + Repro-1) |
