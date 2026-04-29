---
name: H060 — PatchTST trained from scratch on causal OHLCV with HMM regime gate
description: Pre-registered design doc for hypothesis H060
type: project
hypothesis_id: H060
tier: 2c
status: designed
owner: skoir
created: 2026-04-27
citations:
  - ADR-0003-spa-vs-romanowolf
  - ADR-0004-alpha-and-power-defaults
  - ADR-0005-hmm-regime-toolkit
  - ADR-0008-spa-omega-method
  - ADR-0009-blas-thread-pinning
  - Nie, Nguyen et al. 2023 (arxiv:2211.14730)
  - Bergstra & Bengio 2012 (JMLR 13:281-305)
  - Hamilton 1989 (doi:10.2307/1912559)
  - Lopez de Prado 2018 (AFML §3.2 triple-barrier; §7.4.1 purging-and-embargo)
  - Ledoit & Wolf 2008 (doi:10.1016/j.jempfin.2008.03.002)
  - Hansen 2005 (doi:10.1198/073500105000000063)
---

# H060 — PatchTST trained from scratch on causal OHLCV with HMM regime gate

This document is the pre-registration record for hypothesis H060. Frozen at `designed`; any change requires a new hypothesis ID.

H060 was added by the chart-reader hypothesis survey ([docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) §4) as the train-from-scratch transformer baseline complementing H057's train-from-scratch CNN. Its raison d'être is structural: a transformer architectural prior on the H050 substrate with **zero pretraining contamination by construction**, isolating the architectural contribution from the contaminated-pretraining-corpus contribution that H058 inherits.

## 1. Hypothesis

- H0: On the OOS test fold inside the HMM-decoded gate state `s*` identified on the training fold, the realized Sharpe of the PatchTST-driven directional signal does not exceed the Sharpe of the H050 LightGBM gated baseline. Formally `SR_H060_gated − SR_H050_gated ≤ 0`.
- H1: `SR_H060_gated − SR_H050_gated > 0` on the OOS test fold; one-sided test at alpha per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).
- Mechanism (architectural prior): **PatchTST** ([Nie, Nguyen, Sinthong, Kalagnanam 2023, ICLR](https://arxiv.org/abs/2211.14730)) segments each univariate channel into subseries-level patches that serve as input tokens to a Transformer encoder, and processes channels independently with shared embedding and weights. Patching retains local semantic information (Nie et al. 2023, abstract) while attention provides a longer effective receptive field than the convolutional kernels of H057; the empirical question is whether attention recovers bar-to-bar interactions that a 1D-CNN with comparable parameter budget misses on intraday equity-index futures.
- Mechanism (regime gate): identical to H050 — regime-dependent drift in equity-index futures concentrates directional predictability in HMM-decoded high-mean states ([Hamilton 1989, *Econometrica* 57(2):357–384](https://doi.org/10.2307/1912559); [Guidolin & Timmermann 2007, *J. Econ. Dyn. Control* 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004)). Reuses the H050 `select_gaussian_hmm` cache for amortisation per the cycle-6 cache amortisation contract.
- Mechanism (zero pretraining contamination): H060 is **trained from scratch on the H050 substrate**, with no pretrained checkpoint loaded at any step. This is the single structural difference from H058 (TS foundation model + LoRA). The TSFM-leakage taxonomy of [Meyer, Kaltenpoth, Zalipski, Müller 2025, *arxiv 2510.13654*](https://arxiv.org/abs/2510.13654) — train-test sample overlap from multi-purpose dataset reuse, and temporal overlap of correlated train/test series — does not apply when the model has never seen any data outside the H050 walk-forward training fold. Any architectural advantage of attention over convolution that surfaces in H060 vs H057 is therefore attributable to the prior, not to a pretraining corpus that may contain ES/NQ-correlated series.
- Differential information vs H057 (CNN, sibling train-from-scratch arm): different inductive prior. CNN convolution exploits local translation-invariance; attention-with-patching exploits longer-range bar-to-bar interactions through patched self-attention with quadratically reduced sequence length per Nie et al. 2023. Whether attention finds structure CNN misses on 60-bar windows of futures OHLCV is the empirical question H060 isolates.
- Differential information vs H058 (TSFM + LoRA, sibling transformer arm): same model class as Chronos / Moirai / TimesFM / Lag-Llama / MOMENT backbones, but trained from scratch. Sidesteps the contamination concern §8 of the survey memo identifies as "first-order" for H058. Isolates the architectural prior contribution from the pretraining contribution; if H060 lands positive and H058 lands positive at similar magnitude, the architectural prior is sufficient and pretraining is not load-bearing; if H060 is null and H058 is positive, the pretraining corpus is doing the work (and the contamination concern needs to be re-examined).
- Primary citations: [Nie, Nguyen et al. 2023, *arxiv 2211.14730*](https://arxiv.org/abs/2211.14730) (architecture); [Bergstra & Bengio 2012, *JMLR* 13:281–305](https://www.jmlr.org/papers/v13/bergstra12a.html) (random-search hyperparameter protocol); [Hamilton 1989](https://doi.org/10.2307/1912559) and [Baum-Petrie-Soules-Weiss 1970](https://doi.org/10.1214/aoms/1177697196) (HMM gate, inherited from [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)).
- Test statistic: `T_H060 = SR_H060_gated − SR_H050_gated`, computed on walk-forward OOS net-of-cost returns aggregated per the H050 `aggregation_rule_addendum_2026-04-24.md` Path A binding (sub-rule 2a + 3.3a, arithmetic-vs-log conversion as specified). Paired-differential. This is the cross-arm model-class-lift statistic for **Family B** per the synthesis memo §6 (Q-R1-1, Q-R1-12 remediation). Primary inference is the [Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002) studentised time-series bootstrap CI per the existing H050 LW2008 callable at [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py); corroborative entry is **Family B** Hansen 2005 SPA per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md), in which H060 enters as one of M = 5 strategies in the chart-reader cohort `{H057, H058a, H058b, H059, H060}` with H050 as **baseline anchor only** (NOT itself a Family B member; H050's frozen pre-reg places it in Family A under Romano-Wolf step-down per ADR-0003). Family B uses `omega_method="bootstrap"` per ADR-0008 two-tier rule (M ≥ 2) with `shared_bootstrap_indices=true` per Hansen 2005 §3. When H060 runs in M = 1 isolation prior to family aggregation, the corroborative SPA pass-through uses `omega_method="hac"` per ADR-0008 single-strategy degenerate handling.

## 2. Universe and sample period

- Instruments: ES and NQ front-month per [config/instruments.yaml](../../../config/instruments.yaml); roll-handling per that file's calendar. **Roll-adjusted tier**: [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) (module v0.3.0 per commit `329fd1b`, decade-wraparound disambiguation; AFML §2.4.3 ratio-adjustment with `contract_id_full`).
- Frequency: 1-minute bars as the base grid; H060 input cadence is 1m fixed (no BIC sweep over `{1m, 5m, 15m}` — see §3.4). HMM observation cadence inherited from the H050 fold (BIC-selected on the training fold, identical to the H050 selected cadence).
- Session: RTH only, identical to H050. ETH is a separate regime per project CLAUDE.md and out of scope here.
- Train window: 2015-01-01 through 2022-12-31 (calendar bounds; walk-forward splits applied within).
- Validation window: 2023-01-01 through 2023-12-31, embedded as inner folds of walk-forward.
- Test window: 2024-01-01 through 2025-12-31, strictly held out until final SPA submission.
- Roll-handling: front-month, back-adjusted via CME calendar; roll dates frozen at pre-reg.
- Dataset snapshot frozen at pre-registration: SHA256 of the H050 roll-adjusted partitions captured in [data_requirements.md](data_requirements.md) — H060 binds to the **identical** H050 substrate (combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`). Any data after 2025-12-31 is locked away; re-runs on extended windows require a successor hypothesis ID.
- Right-edge truncation: ES 2025 ends 28 calendar days short of 2025-12-31; NQ 2025 ends 12 calendar days short. Same truncation as H050. If the H060 disposition (per §10) materially depends on the last 12-28 days of 2025, the disposition entry receives a `test-window-truncated` annotation and references H050 §`P1-DATABENTO-RIGHT-EDGE-EXTENSION`.

## 3. Input tensor and feature construction

H060's model class is end-to-end on raw causal OHLCV; engineered features (Parkinson RV, realized variance, realized skew, OFI tick-rule) used by H050's LightGBM are **not** input to PatchTST. The HMM regime gate, however, conditions on the same engineered-feature emissions as H050 (the gate is unchanged).

### 3.1 Window definition

- Lookback: **60 bars × 5 channels** (open, high, low, close, volume), right-anchored at decision time `t`. The window covers bars `[t − 59, t]` inclusive — every input bar is observable strictly at or before `t`.
- Channel order: fixed at `[open, high, low, close, volume]` (lexical name carries no semantics; ordering frozen for reproducibility).
- Causality enforcement: window-construction code asserts `max(window.timestamp) <= decision_timestamp`. A look-ahead unit test (PIT canary, §3.3) blocks merge.

### 3.2 Per-channel normalisation

**Q-R1-14 remediation — algebraic interaction with PatchTST instance norm.** PatchTST's encoder applies per-input-window instance normalisation (zero-mean each window per channel) per the canonical recipe; if a per-fold z-score is also applied to the window's mean offset, instance norm subsequently zero-means the window and **collapses any signal carried by the per-fold z-score's mean offset** for non-volume price channels. The pre-reg therefore binds **Option (a)** of the three options surfaced by Round-1 audit:

- **(a) Bound:** drop the per-fold z-score for non-volume channels and rely on PatchTST instance norm only for the OHLC channels.
- (b) Rejected: drop instance norm and use per-fold z-score only — would deviate from the canonical PatchTST recipe ([yuqinie98/PatchTST](https://github.com/yuqinie98/PatchTST), [Nie et al. 2023](https://arxiv.org/abs/2211.14730)) without empirical motivation, expanding successor-question scope.
- (c) Rejected: retain both — no published citation establishes that the offset signal survives both transforms; the algebraic concern stands.

Resolved per-channel normalisation:

- **OHLC channels** (`open, high, low, close`): no per-fold z-score; pass raw price into the PatchTST embedding and rely on the encoder's instance norm. Per-fold scale statistics are still recorded in the sidecar (§11) for diagnostic/repro purposes but are not applied to inputs.
- **Volume channel**: log1p **then** per-fold z-score with rolling statistics from the **training-fold-only** segment of the walk-forward fold under evaluation. Volume is right-tailed and the log1p + z-score combination is the conventional stabilising transform; the per-window instance norm in the encoder operates on the post-z-score volume but the per-fold scale signal here is informational about regime, not first-moment offset, so the algebraic concern in (c) does not apply to this channel.
- Per-fold mean and standard deviation for the volume channel computed over the training fold's full bar-set; applied to all bars in the window (training fold inputs use the same per-fold mean/std as the test fold inputs — the rolling stats are a property of the fold, not the window).
- Implementation: `_normalize_window(window, fold_stats)` with `fold_stats` carried in the fold metadata; the function is pure and PIT-safe by signature (no implicit clock state).

### 3.3 PIT canary (binding regression test)

The PIT canary suite at [tests/unit/test_h050_aggregation_convention.py](../../../tests/unit/test_h050_aggregation_convention.py) is extended for H060 with two transformer-specific look-ahead probes (identical contract to the H057 canary):

1. **Last-bar perturbation**: for a fixed window ending at `t`, perturb the last bar's close by ε and assert the model prediction changes (sensitivity to in-window data is required; failure indicates the model has frozen on the window-internal normalisation or has a stale forward path).
2. **Future-bar perturbation**: perturb a bar at `t + k` for `k ≥ 1` (a bar absent from the window) and assert the model prediction is bit-identical (insensitivity to out-of-window data is required; failure indicates leakage).

Both probes run on a synthetic window where the model has been overfit to a single example (so the prediction is deterministic and ε-sensitive). The probes block merge under `pytest -W error::UserWarning`.

### 3.4 Cadence choice

H060 fixes the input cadence at 1-minute. Rationale: the H050 cadence selection happens inside the HMM gate (BIC-selected on the training fold); H060's transformer ingests the raw bar sequence and would need its own cadence-selection criterion if the cadence were tunable. To avoid expanding the SPA family by a factor of 3 (`{1m, 5m, 15m}`) and to keep H060 commensurable with H057 (which also fixes 1m), the cadence is fixed at pre-reg. If post-hoc the 1m choice is suspected suboptimal, that is a successor-hypothesis question, not an in-H060 search.

### 3.5 Class labels

Identical to H050 §4. Triple-barrier per [Lopez de Prado 2018, *Advances in Financial Machine Learning*, Wiley, ISBN 978-1-119-48208-6, §3.2](https://doi.org/10.1002/9781119482086):

- `pt_sl`: symmetric around volatility, multiplier selected by walk-forward CV over `{1.0, 1.5, 2.0}` on the train fold.
- `vertical_barrier`: `{30m, 60m, 120m}` grid, selected by same CV.
- `volatility_estimator`: Yang–Zhang with lookback selected by CV over `{20, 60, 120}` minutes.
- Output is a 3-class softmax over `{top barrier, bottom barrier, vertical barrier}` per the H050 labeller. The H050 27-cell label grid (3 × 3 × 3) is reused — H060 does not introduce a new label grid.
- Meta-label horizon upper bound: max of selected `vertical_barrier` across folds; fed to splitter `purge`.

## 4. Estimator

### 4.1 Backbone: PatchTST trained from scratch

- Architecture: PatchTST encoder per [Nie, Nguyen et al. 2023](https://arxiv.org/abs/2211.14730), reference implementation [yuqinie98/PatchTST](https://github.com/yuqinie98/PatchTST). Channel-independent: each of the 5 input channels is processed independently with shared embedding and Transformer weights, per the paper's channel-independence section (Nie et al. 2023, abstract: "channel-independence where each channel contains a single univariate time series that shares the same embedding and Transformer weights").
- **No pretrained checkpoint** is loaded at any step. Weights are initialised from the reference-implementation default (truncated normal for linear projections, zeros for biases, learned positional encoding initialised per the canonical recipe). Random seed 20260427 fixes initialisation.
- Forecasting head removed; replaced with a **3-class classification head**: a single hidden layer MLP `(d_model → 128 → 3)` with ReLU activation between. Softmax applied at inference. The classification head is trained jointly with the encoder from scratch (no two-phase warm-up — the entire model is trained end-to-end from random initialisation).

### 4.2 Architecture pre-reg grid

Total ≤ 16 cells (multiplicative product below). Pre-registered at design time; no post-hoc additions.

| Hyperparameter | Grid |
|---|---|
| `patch_len` | `{8, 16}` |
| `stride` | `patch_len / 2` (deterministic from `patch_len` — `{4, 8}`) |
| `n_layers` | `{3, 6}` |
| `n_heads` | `{4, 8}` |
| `d_model` | `{64, 128}` |

`stride = patch_len / 2` is deterministic, so the effective grid is `patch_len × n_layers × n_heads × d_model = 2 × 2 × 2 × 2 = 16` cells. The constraint `d_model % n_heads == 0` is satisfied by every combination (64/4, 64/8, 128/4, 128/8 all integral).

### 4.3 Hyperparameter search protocol

Random search per [Bergstra & Bengio 2012, *JMLR* 13:281–305](https://www.jmlr.org/papers/v13/bergstra12a.html). N_draws calibrated to ≥ 95% expected coverage of the top-5% configurations on the **discrete** 16-cell grid:

- For a discrete grid of size `G = 16` with top-fraction `f = 0.05`, `top_count = max(1, ceil(G × f)) = 1`. The probability that `N_draws` draws (with replacement) miss the top-1 cell entirely is `(15/16)^N`. To bound this miss probability at 5%, `N ≥ log(0.05) / log(15/16) ≈ 46.5`. Therefore **`N_draws = 47`**, fixed at pre-reg.
- Sampling: uniform with replacement over the 16-cell grid; seed 20260427.
- Discrete-grid replicate-coverage regime applies (small `G`); this is **not** the Bergstra & Bengio §2.2 continuous-volume regime — calibration is per-cell coverage of the top-1 cell, not volume of the top-5% region. Justification matches the H050 orchestrator-triple `P1-H050-LGB-N-DRAWS-EMPIRICAL` follow-up rationale (replicate-coverage on a discrete grid).
- Fixed-seed determinism: every random draw, every initialisation, every dropout mask, every minibatch order is reproducible from `random_seed=20260427` plus the fold index.

### 4.4 Training protocol

- Optimiser: AdamW; learning rate `1e-4` (fixed at pre-reg). The LR is anchored to the canonical PatchTST recipe in [yuqinie98/PatchTST](https://github.com/yuqinie98/PatchTST) `run_longExp.py` default for the ETT benchmarks. **Q-R1-6 remediation**: Round-1 audit flagged the previous "documented as a methodology choice not a hyperparameter" framing as the loophole the no-magic-number rule explicitly forecloses. Resolution: H060 references `P1-H060-LR-DEFAULT-LITERATURE-CHECK` as a `status=running` blocker pending literature-check resolution. The ETT-benchmark transfer is **unproven** on 1-min equity-index futures with a 3-class classification head (the canonical recipe targets long-horizon univariate forecasting on hourly/daily ETT data; the architectural and task gap is non-trivial). If literature-check returns no transferability evidence, an LR-grid amendment via successor hypothesis ID is required — H060's pre-reg itself does NOT widen the grid in-flight.
- Loss: cross-entropy over the 3-class softmax with class weights set to inverse-frequency on the training fold (handles triple-barrier label imbalance per the H050 LGB convention).
- Batch size: 256 (anchored to PatchTST canonical recipe for the ETT benchmarks; same selection-bias note as the LR above applies).
- Epochs: 30 with early stopping on validation log-loss (patience 5) (anchored to PatchTST canonical recipe + AdamW conventions).
- Dropout: 0.1 in attention and feed-forward sublayers (PatchTST default); not tuned (anchored to canonical recipe).
- Gradient clipping: max-norm 1.0 (AdamW + transformer-encoder convention; anchored).
- Hardware: single-GPU (CUDA when available; CPU fallback for unit tests). BLAS thread pinning per [ADR-0009](../../../docs/decisions/ADR-0009-blas-thread-pinning.md): `OMP_NUM_THREADS = MKL_NUM_THREADS = OPENBLAS_NUM_THREADS = 1` for the orchestrator process. PyTorch's intra-op and inter-op thread counts are pinned to 1 via `torch.set_num_threads(1)` and `torch.set_num_interop_threads(1)` set in the orchestrator entry point before any model construction (PyTorch reads thread settings at first use, not at import — the calls must precede the first forward pass).

**Selection-bias note (Q-R1-6 + Q-R1-5 cross-arm consistency)**: The training-side scalars `{lr=1e-4, batch_size=256, epochs=30, patience=5, dropout=0.1, grad_clip=1.0}` are bound at pre-reg as methodology choices anchored to the canonical PatchTST recipe (citations above). They are NOT swept and are not part of the SPA family count. A successor hypothesis is required to relax any of them. The selection-bias risk is acknowledged: the canonical-recipe transfer to 1-min equity-index futures with a 3-class classification head is unproven, and a tuned-from-scratch sweep on the H050 substrate could yield different optima. Tracked under `P1-H060-TRAINING-SCALARS-EMPIRICAL` for an out-of-cycle empirical sweep on the H050 substrate that is reported separately and does NOT feed back into H060's pre-reg. The LR-specific blocker `P1-H060-LR-DEFAULT-LITERATURE-CHECK` (R-R1-7) is the gating reference for `status=running`.

### 4.5 HMM regime gate

Identical to H050 §5. Reuses the `select_gaussian_hmm` cache from commit `1c85f5f` for amortisation across the H060 hyperparameter grid (the HMM gate is independent of the PatchTST hyperparameters; cache key `(symbol, fold_id, label_horizon)` per the cycle-6 cache amortisation contract). Per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md):

- Gaussian emissions on the H050 microstructure feature set.
- `covariance_type ∈ {diag, full}` with **runtime model-class deduplication** in `select_gaussian_hmm` per the H050 closure semantics ("pre-reg grid preserved by model-class dedup"; commit `1c85f5f` cache amortization context). For one-dimensional emissions `diag` and `full` are mathematically equivalent and the dedup collapses the redundant evaluation; the pre-reg grid is preserved across all four chart-reader arms (cross-cutting binding 2 from synthesis memo §3 / Q-R1-7 remediation; uniform across H057 + H058a + H058b + H059 + H060). This is not a method change vs the H050 pre-reg.
- `n_states` selected per ADR-0005 adaptive rule.
- Causal forward filter `p(s_t | y_{1:t})` only; smoothed posteriors are training-fold diagnostics only.
- Fold-boundary warm start per ADR-0005's K-step Hamilton-prediction propagation.

### 4.6 Loss / metric

- Training loss: cross-entropy with class weights.
- Selection metric (per fold): Sharpe of net-of-cost gated returns on the inner-CV held-out segment, per the H050 orchestrator-triple selection metric.
- Reporting metric (per fold): Sharpe, Brier score, log-loss, gate hit-rate, gated-vs-unconditional return differential. All emitted to per-fold ledger.

## 5. Splitter

Identical to H050 §6 — H060 binds to the same fold structure for commensurability with `T_H060 = SR_H060_gated − SR_H050_gated`:

- Splitter: `PurgedWalkForwardSplitter` per plan §4.1 with embargo per [Lopez de Prado 2018 §7.4.1](https://doi.org/10.1002/9781119482086).
- `embargo`: max of residual-PACF-based lag and Politis–White optimal block length on stacked residuals (auto, identical to H050).
- `purge`: `max(vertical_barrier)` across CV-selected folds (auto, identical to H050).
- Fold count: identical to H050's `n_required_for_power_80` to keep the paired-differential statistic well-defined (paired draws across folds require fold alignment).
- CPCV not used; escalation requires a successor hypothesis ID per H050 §6.

Reference implementation [yuqinie98/PatchTST](https://github.com/yuqinie98/PatchTST) (Apache-2.0; license verified at design time, recorded in [data_requirements.md](data_requirements.md)).

## 6. Cost model

- `cost_model_id`: `nt8_es_nq_rth_v1` (identical to H050 §7).
- Commission: per-contract commission from [config/instruments.yaml](../../../config/instruments.yaml) (CME-cited fees).
- Slippage: regime-conditional (RTH only), constant-tick prior with sensitivity multiplier per H050 §7 until paper-trade slippage distribution lands.

## 7. Aggregation rule

H060 binds to the H050 [aggregation_rule_addendum_2026-04-24.md](../H050/aggregation_rule_addendum_2026-04-24.md) Path A (sub-rule 2a + 3.3a) without modification. The arithmetic-vs-log return-conversion convention is the same as H050. The aggregation gate at [tests/unit/test_h050_aggregation_convention.py](../../../tests/unit/test_h050_aggregation_convention.py) is reused; H060-specific aggregation coverage is added to the same test suite under follow-up `P1-H060-AGGREGATION-CONVENTION-COVERAGE`.

## 8. Gate thresholds

Defaults from [config/gate.yaml](../../../config/gate.yaml) per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).

- `alpha`: 0.05 (one-sided).
- `bh_threshold`: 0.10.
- `dsr_activation_size`: project default.
- Power target: 0.80.

### 8.1 Inference

- **Primary**: paired-differential Sharpe CI via [Ledoit & Wolf 2008, *J. Empir. Finance* 15(5):850–859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentised time-series bootstrap, callable at [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) (`ledoit_wolf_2008_differential_ci`). H1 holds if the 95% CI excludes zero from above.
- **Corroborative (per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md))**: Hansen 2005 SPA pass-through. H060 enters **Family B** — the chart-reader cohort `{H057, H058a, H058b, H059, H060}` (M = 5) — with H050 as **baseline anchor only** (NOT itself a Family B member; H050 stays in Family A under Romano-Wolf step-down per ADR-0003 per the synthesis memo §6 split). Family B SPA omega method is `bootstrap` per ADR-0008 two-tier rule (M ≥ 2), with `shared_bootstrap_indices=true` to preserve cross-strategy dependence per Hansen 2005 §3. If the Family B cohort has not yet accumulated `M ≥ 2` at H060 execution time (e.g., H057/H058/H059 not yet evaluated), H060 reports a single-strategy SPA pass-through with `omega_method = hac` and the `SingleStrategySPAWarning` per ADR-0008 §Single-strategy degenerate handling.

## 9. Stopping rule

- Stop criterion: fixed walk-forward fold count equal to H050's `n_required_for_power_80` (paired-differential alignment requires identical fold count).
- Max folds: bounded above by calendar-window limit (identical to H050).
- Hyperparameter-search budget exceedance: the 47-draw random search is the binding budget; no extension permitted in-H060 (a successor hypothesis is required for any extension).

## 10. Decision rule

- `passed=True` (LW2008 95% CI on `T_H060` excludes 0 from above **AND** Family B Hansen SPA family-aggregate passes per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md), M = 5, `omega_method="bootstrap"`, `shared_bootstrap_indices=true`) → `archive(positive)`; promote to paper-trade eligibility (the 60-session-day paper-trade calendar floor still applies before live).
- `passed=False` with LW2008 CI excluding zero but Family B SPA failing → `archive(null)` with multiple-testing note.
- `passed=False` with LW2008 CI covering zero → `archive(null)`.
- Realized folds < `n_required_for_power_80` → `archive(null, underpowered)`.
- HMM stationarity pre-check failure per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) → `archive(null, precondition-failed)`.
- PIT canary §3.3 failure on production run → `archive(null, leakage-detected)` with full root-cause memo before any future H060-class hypothesis.

## 11. Reproducibility commitments

- git HEAD (at run): TBD at execution.
- `uv pip freeze` sha (at run): TBD at execution.
- RNG seed: **20260427**.
- Dataset checksums (frozen at pre-reg): captured in [data_requirements.md](data_requirements.md). H060 binds to the H050 roll-adjusted substrate combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`.
- Reproducibility log path: `logs/reproducibility/{run_id}.json`
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json` per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md).
- H060-specific PatchTST sidecar: `logs/reproducibility/{run_id}_patchtst_h056.json`. Schema `patchtst_h056_v1`:

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | `"patchtst_h056_v1"` |
| `random_seed` | int | `20260427` |
| `architecture` | object | Resolved `{patch_len, stride, n_layers, n_heads, d_model}` for the selected configuration |
| `arch_grid_resolved_sha256` | string | SHA256 over the canonical-JSON dump of the resolved 16-cell grid + sampled draws |
| `n_draws` | int | `47` |
| `train_protocol` | object | `{optimizer, learning_rate, batch_size, epochs, patience, dropout, grad_clip}` |
| `weights_sha256` | string | SHA256 of the model state dict (PyTorch `state_dict` serialised via `torch.save` to `BytesIO`, then SHA256 of bytes) |
| `weights_path` | string | On-disk path to the persisted state dict, gitignored under `logs/models/{run_id}_patchtst.pt` |
| `pretrained_checkpoint_loaded` | bool | **Asserted `false` by reproducibility-verifier** — non-negotiable |
| `head_class_count` | int | `3` (top, bottom, vertical) |
| `n_input_channels` | int | `5` (open, high, low, close, volume) |
| `lookback_bars` | int | `60` |
| `cadence_minutes` | int | `1` |
| `class_weights` | object | `{top, bottom, vertical}` per-fold inverse-frequency weights |
| `fold_id` | int | Walk-forward fold index |
| `early_stop_epoch` | int | Epoch at which validation log-loss patience triggered |
| `final_train_loss` | float | Cross-entropy on training fold, last epoch |
| `final_val_loss` | float | Cross-entropy on validation segment, early-stop epoch |
| `pit_canary_passed` | bool | §3.3 last-bar-perturbation and future-bar-perturbation checks both green |
| `blas_thread_state` | object | `{OMP_NUM_THREADS, MKL_NUM_THREADS, OPENBLAS_NUM_THREADS, torch_num_threads, torch_num_interop_threads}` snapshot at construction time, asserted all `1` per ADR-0009 |
| `hmm_sidecar_sha256` | string | SHA256 of the per-fold HMM selection sidecar (cross-link into ADR-0005 sidecar contract) |
| `warm_cold_sidecar_sha256` | string | SHA256 of the warm-cold filter diagnostic sidecar per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) "Warm-vs-cold filter regression diagnostic" (R-R1-2 remediation — added to schema; previously omitted) |

Sidecar SHA256 combined into `ReproLog.model_hash` via `with_model_hash` under the **binding interim deterministic composition rule** (R-R1-2, R-R1-3, R-R1-5 remediation per synthesis memo §3 + §5):

```
model_hash = sha256(sorted_tuple([
    arm_sidecar_sha256,         # patchtst_h056_v1 sidecar SHA256 (== weights_sha256-derived sidecar SHA)
    hmm_sidecar_sha256,         # ADR-0005 HMM selection sidecar SHA256
    warm_cold_sidecar_sha256,   # warm-cold filter diagnostic SHA256
    ledger_rollup_sha256,       # per-fold ledger roll-up SHA256
]))
```

The `sorted_tuple` ensures byte-deterministic input ordering. This interim rule binds H060 until the helper lands; tracked under `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` (now blocking `status=running` for H057 + H058 + H059 + H060 per synthesis memo §5; R-R1-5 remediation — reference added).

No change to the frozen `ReproLog` dataclass per ADR-0005's "Integration with existing infrastructure" contract.

**Per-arm power calculation (Q-R1-8 remediation)**: H060's `n_required_for_power_80` (referenced in §9 and aligned with H050 above) is computed from the dispersion of H060's OWN paired-differential test statistic `T_H060 = SR_H060_gated − SR_H050_gated` on a pilot training-fold sample — **not** inherited from H050's scalar. The Family B cohort fold count is `max(n_required_per_arm)` across `{H057, H058a, H058b, H059, H060}` to preserve paired-differential pairing across the cohort. Tracked under `P1-CHARTREADER-PER-ARM-POWER-CALC` (gates `status=running`).

**Follow-up references** (open at pre-reg): `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` (helper-landing; binds the interim composition rule above; R-R1-5 remediation), `P1-H060-LR-DEFAULT-LITERATURE-CHECK` (R-R1-7 + Q-R1-6 remediation; gates `status=running`), `P1-H060-TRAINING-SCALARS-EMPIRICAL` (out-of-cycle empirical sweep on training-side scalars; results do NOT feed back into H060's pre-reg), `P1-CHARTREADER-PER-ARM-POWER-CALC` (gates `status=running`), `P1-H060-AGGREGATION-CONVENTION-COVERAGE` (aggregation-test coverage extension).

### 11.1 Reproducibility-verifier contract (binding)

The reproducibility-verifier subagent on H060 execution must assert:

1. `pretrained_checkpoint_loaded == false` for every fold sidecar (zero-contamination invariant).
2. `blas_thread_state` shows all four BLAS / OpenMP / OpenBLAS / PyTorch thread variables equal `1` for every fold (ADR-0009 conformance).
3. `pit_canary_passed == true` for every fold sidecar (no leakage).
4. `arch_grid_resolved_sha256` is identical across folds (the grid is shared across folds; per-fold draws are recorded separately).
5. `weights_sha256` round-trips (re-loading the persisted state dict and re-hashing reproduces the recorded SHA256 to the byte).
6. The combined `sha256(sorted_tuple([arm_sidecar_sha256, hmm_sidecar_sha256, warm_cold_sidecar_sha256, ledger_rollup_sha256]))` reproduces `ReproLog.model_hash` byte-identically (R-R1-2 remediation — `warm_cold_sidecar_sha256` is part of the composed `model_hash` and the verifier asserts its presence and round-trip).
