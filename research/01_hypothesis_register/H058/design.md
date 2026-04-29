---
name: H058 — Time-series foundation model (TimesFM-2.5 + Chronos-Bolt-base) with LoRA fine-tune and HMM regime gate
description: Pre-registered design doc for hypothesis H058
type: project
hypothesis_id: H058
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
  - Das et al. 2024 (arxiv:2310.10688)
  - Ansari et al. 2024 (arxiv:2403.07815)
  - Hu et al. 2022 (arxiv:2106.09685)
  - Meyer Kaltenpoth Zalipski Müller 2025 (arxiv:2510.13654)
  - Hamilton 1989 (doi:10.2307/1912559)
  - Baum-Petrie-Soules-Weiss 1970 (doi:10.1214/aoms/1177697196)
  - Ledoit & Wolf 2008 (doi:10.1016/j.jempfin.2008.03.002)
  - Hansen 2005 (doi:10.1198/073500105000000063)
  - Bergstra & Bengio 2012 (JMLR 13:281-305)
---

# H058 — Time-series foundation model (TimesFM-2.5 + Chronos-Bolt-base) with LoRA fine-tune and HMM regime gate

This document is the pre-registration record for hypothesis H058. Frozen at `designed`; any change requires a new hypothesis ID. Commensurable with [H050/design.md](../H050/design.md) on labeller, HMM gate, walk-forward CV scheme, and inference machinery; differs only in the model class for the directional classifier (TSFM + LoRA head replacing the H050 LightGBM baseline).

## 1. Hypothesis

- H0: For both backbones `b ∈ {TimesFM-2.5-200M, Chronos-Bolt-base-205M}`, the paired-differential Sharpe `T_arm = SR_{arm_gated} − SR_{H050_gated} ≤ 0` on the OOS test fold (where `arm` is one of `H058a` = TimesFM-2.5 backbone or `H058b` = Chronos-Bolt-base backbone).
- H1: For at least one backbone, `T_arm > 0`; one-sided test at alpha per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md). Multiple-testing across backbones handled inside the same Family B Hansen 2005 SPA cohort per §6, with H050 as **baseline anchor only** (not a Family B member). Family B membership is `{H057, H058a, H058b, H059, H060}` for `M = 5`. Per the synthesis memo §3 Q1 / §6 Family B declaration ([memo](../../../docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md)), this two-family split (Q-R1-1 + Q-R1-12 remediation) preserves H050's frozen Family A pre-reg.
- Mechanism: a transformer pre-trained on a large multi-domain time-series corpus encodes statistical priors over autocorrelation, multi-scale seasonality, and noise structure that a from-scratch LightGBM on engineered microstructure features cannot reach within the H050 sample. LoRA adaptation ([Hu et al. 2022, ICLR, arxiv 2106.09685](https://arxiv.org/abs/2106.09685)) preserves the pretrained representation while specialising a 3-class triple-barrier head to ES/NQ intraday dynamics. The HMM regime gate per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) is identical to H050 and isolates the regime-conditioned subspace where directional drift concentrates. Differential information vs H050 LGB is the **transfer-learning prior from cross-domain TS pretraining**; differential information vs H057 (1D-CNN trained from scratch) is the prior itself, which H057 lacks by construction. The mechanism is contingent on the pretrained representation being non-trivially informative for ES/NQ 1-min returns *without* benefiting from direct pretraining-corpus exposure to the target series — see §3 and §8 contamination screen.
- Primary citations: [Das et al. 2024, ICML, arxiv 2310.10688](https://arxiv.org/abs/2310.10688) (TimesFM); [Ansari et al. 2024, arxiv 2403.07815](https://arxiv.org/abs/2403.07815) (Chronos); [Hu et al. 2022, ICLR, arxiv 2106.09685](https://arxiv.org/abs/2106.09685) (LoRA); [Hamilton 1989, Econometrica 57(2):357-384](https://doi.org/10.2307/1912559) (regime-switching foundation); [Meyer, Kaltenpoth, Zalipski, Müller 2025, arxiv 2510.13654](https://arxiv.org/abs/2510.13654) (TSFM contamination concern).
- Test statistic: `T_arm = SR_{filtered, gated, arm} − SR_{filtered, gated, H050_LGB}` for `arm ∈ {H058a (TimesFM-2.5), H058b (Chronos-Bolt-base)}`, computed on walk-forward OOS net-of-cost returns. Both arms enter Family B (the chart-reader cohort Hansen 2005 SPA family with `M = 5`: `{H057, H058a, H058b, H059, H060}`); H050 is the baseline anchor only — see §6.

## 2. Universe and sample period

Identical to [H050/design.md §2](../H050/design.md). H058 inherits the H050 substrate verbatim so the paired differential `T_arm` (for `arm ∈ {H058a, H058b}`) is computed bar-aligned on the same OOS folds at per-bar cadence (matching the Family B uniform per-bar cadence binding).

- Instruments: ES and NQ front-month per [config/instruments.yaml](../../../config/instruments.yaml); roll-handling per that file's calendar; substrate version `vendor_legacy_1min_roll_adjusted` v0.3.0 (commit `329fd1b`) per [H050/data_requirements.md](../H050/data_requirements.md).
- Frequency: 1-minute bars as the base grid. The TSFM context window is patched at the model's native patch length (TimesFM patch=32 per [Das et al. 2024](https://arxiv.org/abs/2310.10688); Chronos-Bolt patch=16 per the model card, see §5). Decision cadence remains 1-minute; the HMM observation cadence inherits H050's BIC-selected `{1m, 5m, 15m}` choice per fold.
- Session: RTH only.
- Train window: 2015-01-01 through 2022-12-31.
- Validation window: 2023-01-01 through 2023-12-31, embedded as inner folds.
- Test window: 2024-01-01 through 2025-12-31, strictly held out until final SPA submission.
- Roll-handling note: AFML §2.4.3 ratio-adjusted continuous series; roll dates frozen at H050 pre-reg.
- Dataset snapshot: SHA256 binding inherited from [H050/data_requirements.md](../H050/data_requirements.md) — combined frame `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`. Right-edge truncation per H050 §2 / `P1-DATABENTO-RIGHT-EDGE-EXTENSION` applies symmetrically.

## 3. Features

H058 inputs are partitioned into two disjoint sets that feed two disjoint subsystems: (a) the HMM regime gate (which is shared across all chart-reader cohort arms and is identical to the H050 gate), and (b) the TSFM classifier itself (which consumes only the raw causal-window log-return context). The differential-information story is intentional — the H050 microstructure features only condition the HMM gate; the TSFM ingests **only** raw return context, isolating the transfer-learning prior as the differential signal vs the H050 LightGBM. All inputs are PIT-safe by construction (causal padding, training-fold-only rolling stats).

### 3.1 HMM gate inputs (H050-shared)

These four features feed only the HMM regime gate per §5.5; they do **not** enter the TSFM classifier. Definitions are inherited verbatim from [H050/design.md §3](../H050/design.md):

- `rv_parkinson@1.0` — realized variance, Parkinson estimator (training-fold lookback selected by CV; identical to H050).
- `rv_realized@1.0` — squared-returns realized variance ([Andersen & Bollerslev 1998, IER](https://doi.org/10.2307/2527343)).
- `realized_skew@1.0` — third central moment, standardized.
- `ofi_tickrule@1.0` — order-flow-imbalance proxy via tick rule (Lee-Ready); MBP-10 dependency tracked under H010.

### 3.2 TSFM classifier inputs

The TSFM consumes only one input — the **right-anchored (causal) `context_length`-bar window of log returns**, formed bar-by-bar with no future bar in scope. The H050 microstructure features above are **not** passed to the TSFM. This isolation is deliberate: the H058 differential vs H050 must reflect the cross-domain pretraining prior, not feature engineering.

- `tsfm_context@b` — backbone-`b`-specific causal context tensor of shape `(context_length_b, 1)` over log returns of the gated symbol's 1-min bar series. Windows are right-anchored at the decision bar `t`; the leftmost bar is `t − context_length_b + 1`. `context_length_b` is set to **512 bars** for both TimesFM-2.5 and Chronos-Bolt-base. The choice is **pre-registered, not searched** (one value per backbone) to keep the Family B SPA contribution at exactly 2 entries (one per backbone) and avoid the alternative `{256, 512, 1024}` × 2-backbone inner-CV grid which would inflate the family count (see §6.2). 512 bars is bound at pre-reg as a methodology anchor: it is below TimesFM's documented 2048 maximum and matches Chronos default, and represents ~1.3 RTH sessions of context. **No literature exists prescribing an empirically optimal TSFM context length for intraday equity-index futures direction;** the binding is acknowledged as a methodology gap, with `P1-H058-CONTEXT-LENGTH-EMPIRICAL` registered as the post-cycle empirical-calibration follow-up.

**PIT proof for `tsfm_context@b`.** At decision bar `t`, the TSFM input is `r_{t − context_length_b + 1 : t}` where `r_τ = log(close_τ / close_{τ − 1})` is the log return computed from already-published bars. No bar at index `> t` is referenced. This is asserted by the canary in §11.

Leakage tests per plan §3 and §4.6 must pass before run. See §11 for the additional TSFM-specific canary asserting `context_length` does not exceed the walk-forward training-fold's right edge.

## 4. Label construction

Triple-barrier per Lopez de Prado AFML §3.2; **identical to [H050/design.md §4](../H050/design.md)** so that `T_{H058a}` and `T_{H058b}` are paired differentials on bar-aligned label outcomes.

- `pt_sl`: symmetric around volatility; multiplier selected by walk-forward CV over `{1.0, 1.5, 2.0}` on the train fold (CV scheme per H050).
- `vertical_barrier`: `{30m, 60m, 120m}` grid.
- `volatility_estimator`: Yang–Zhang with lookback `{20, 60, 120}` minutes.
- Meta-label horizon upper bound: max of selected `vertical_barrier` across folds.
- Output classes: `{up, vertical, down}` (3-class softmax target). The TSFM classification head emits `softmax ∈ Δ²` over these three classes.

## 5. Estimator

### 5.1 Backbone shortlist (binding)

Exactly two backbones, both pre-registered:

| Backbone | Source | Params | License | Patch length | Selected `context_length` |
|---|---|---|---|---|---|
| TimesFM-2.5-200M | [google-research/timesfm](https://github.com/google-research/timesfm) HF [google/timesfm-2.5-200m-pytorch](https://huggingface.co/google/timesfm-2.5-200m-pytorch) | 200M | Apache-2.0 | 32 (per [Das et al. 2024](https://arxiv.org/abs/2310.10688)) | 512 bars |
| Chronos-Bolt-base-205M | [amazon-science/chronos-forecasting](https://github.com/amazon-science/chronos-forecasting) HF [amazon/chronos-bolt-base](https://huggingface.co/amazon/chronos-bolt-base) | 205M | Apache-2.0 | 16 (per HF model card) | 512 bars |

Backbone choice is bound at pre-reg; **no other backbones may enter at run-time**. The selection rationale is documented in §1 (TimesFM-2.5 = lowest documented contamination risk; Chronos-Bolt-base = broadest zero-shot evidence + smallest production-grade footprint), grounded in the survey at [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) §8.

### 5.2 Adapter pre-registration (LoRA)

Per [Hu et al. 2022, ICLR, arxiv 2106.09685](https://arxiv.org/abs/2106.09685), LoRA injects a trainable rank-`r` decomposition `ΔW = BA` (with `A ∈ R^{r × k}`, `B ∈ R^{d × r}`) into selected weight matrices of the frozen backbone. Trainable parameter count per adapted matrix is `r·(d + k)`.

Pre-registered grid:

| Hyperparameter | Grid |
|---|---|
| LoRA rank `r` | `{4, 8, 16}` |
| LoRA scaling `α` | `{8, 16, 32}` |
| Target modules | Backbone-specific PEFT defaults (TimesFM: attention `q_proj`/`v_proj` projections per the [HuggingFace PEFT](https://github.com/huggingface/peft) default for decoder-only attention transformers; Chronos T5 backbone: `q`/`v` of T5 self-attention per PEFT `LoraConfig` defaults for T5). Frozen at the PEFT-default specification at run-time; pinned in the sidecar (`adapter_target_modules`). |
| Learning rate | `{1e-5, 1e-4, 1e-3}` on log grid |

Combined cell count: 3 × 3 × 3 = 27 cells per backbone × 2 backbones = 54 adapter-fit configurations. Combined with the H050 label grid (27 cells; from §4), the full grid count per backbone is 27 × 27 = 729 cell candidates.

**Search protocol.** Random search per [Bergstra & Bengio 2012, JMLR 13:281-305](https://www.jmlr.org/papers/v13/bergstra12a.html) with fixed seed 20260427; `N_draws = 79` per walk-forward fold per backbone — discrete-grid replicate-coverage derivation (matching H060 §4.3 precedent for discrete grids). Derivation: top-1-cell coverage on a discrete grid of `G = 27` cells with `N` independent draws (with replacement) is `1 − (1 − 1/G)^N`; setting `(26/27)^N ≤ 0.05` gives `N ≥ log(0.05) / log(26/27) ≈ 79`. The Bergstra-Bengio §2.2 volume argument (the H050 ungrounded `N_draws = 200` rationale) does **not** apply to a discrete 27-cell grid because the volume-of-good-region argument is over a continuous hypercube. Per-config max epochs = 5; early stopping on validation cross-entropy log-loss with patience = `min(2, epochs/3) = 2` (rationale: a 5-epoch budget needs ≥ 2 patience for stable LoRA convergence per the [HuggingFace PEFT 0.10 docs](https://huggingface.co/docs/peft) generic guidance on PEFT training stability; `P1-H058-FINETUNE-PROTOCOL-EMPIRICAL` registers the post-cycle empirical-calibration follow-up to verify this on the production substrate).

### 5.3 Head architecture

The TSFM forecasting head is **replaced** with a 3-class MLP head:

- Input: backbone last-layer hidden state at the right-edge token (length `d_model_b`; `d_model_TimesFM = 1024`, `d_model_Chronos-Bolt = 768` per the published architectures).
- Hidden layer: 128 units, ReLU activation.
- Output: 3-class softmax over `{up, vertical, down}`.
- Loss: class-weighted cross-entropy where weights are inverse class frequency in the training fold (matches H050 LightGBM `is_unbalance=True` semantics).

### 5.4 Two-phase fine-tune protocol

The two-phase protocol is the standard HuggingFace PEFT recipe (`prepare_model_for_kbit_training` followed by `get_peft_model` per the [PEFT 0.10 docs](https://huggingface.co/docs/peft)) — frozen-backbone warm-up of the head before adapter training reduces head-init-noise interference with the LoRA gradient. **It is not prescribed by Hu et al. 2022 §3.3** (the original LoRA paper does not specify head-warm-up epoch counts); the Phase-1 epoch count and Phase-2 patience here are PEFT-canonical operational choices, not citations:

1. **Phase 1 — head-only pretrain.** Freeze the backbone + the LoRA adapter (initialise `B = 0` per the LoRA paper's initialisation convention so the adapter is the identity at start). Train only the 3-class MLP head for **1 epoch** on the training fold. Loss: cross-entropy. Rationale: a single epoch is sufficient because the head is small (input dim → 128 → 3) and converges fast on training-fold class proportions.
2. **Phase 2 — joint LoRA tune.** Unfreeze the LoRA adapter parameters (the backbone weights remain frozen in their pretrained state). Train both the LoRA adapter and the MLP head jointly for the remaining epoch budget per §5.2. Early-stopping patience is `min(2, epochs/3) = 2` epochs (raised from 1 to absorb LoRA loss-curve noise at the 5-epoch budget).

Both Phase-1 epoch count (`= 1`) and Phase-2 patience (`= 2`) are pre-registered as methodology anchors with `P1-H058-FINETUNE-PROTOCOL-EMPIRICAL` registered as the post-cycle empirical-calibration follow-up (per Q-R1-3c remediation).

### 5.5 HMM regime gate

Identical to [H050/design.md §5](../H050/design.md): Gaussian HMM per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) with `covariance_type ∈ {diag, full}` and runtime model-class deduplication in `select_gaussian_hmm` per the H050 `P1-HMM-FULL-COV-1DIM-REDUNDANT` closure semantics (the pre-reg grid is preserved; the runtime dedup eliminates the redundant `full` cell only when the emission dimension `d = 1` makes `full` and `diag` mathematically equivalent). `n_states` grid per ADR-0005's adaptive rule, BIC + CV log-likelihood selection, k-means++ warm start with restart count selected by the bootstrap-ε rule (operational floor 5), label-switch canonicalisation by emission-mean rank ascending, gate state = highest-mean state.

State assignment at decision time uses the causal forward filter `p(s_t | y_{1:t})` only; smoothed posteriors are training-fold diagnostic only. Fold-boundary state continuity uses the K-step warm-start formula per ADR-0005's `filter_states_from_prior` contract (`K = test_idx[0] − train_idx[-1]` ≥ 2 under purge).

The HMM gate operates on the same H050 features (`rv_parkinson`, `rv_realized`, `realized_skew`, `ofi_tickrule`); H058's TSFM does **not** participate in HMM emission inference. The HMM cache from commit `1c85f5f` is reused with cache key `(symbol, fold_id, label_horizon)` per `P1-HMM-CACHE-DISABLED-PATH-TIMING`.

### 5.6 Loss / metric

- Training loss: class-weighted cross-entropy on the 3-class triple-barrier target.
- Selection metric (inner CV, label-CV cell): cross-entropy on the held-out inner fold per H050 §5 (Varma & Simon 2006 nested walk-forward; the gated metric variant per `P1-H050-LABEL-CV-GATED-METRIC` is **not** adopted at pre-reg pending the empirical comparison filed under that follow-up — H058 inherits H050's ungated label-CV selection metric for paired-differential commensurability).
- Gate evaluation metric: Sharpe of the regime-gated, net-of-cost return stream per H050.

## 6. Splitter and multiple-testing family

### 6.1 Splitter

Identical to [H050/design.md §6](../H050/design.md):

- `PurgedWalkForwardSplitter` per AFML §7.4.1; stacked-embargo mode per [ADR-0007](../../../docs/decisions/ADR-0007-embargo-placement.md).
- `embargo`: max of residual-PACF-based lag and Politis–White optimal block length on stacked residuals.
- `purge`: `max(vertical_barrier)` across CV-selected folds.
- CPCV not used; escalation requires a successor hypothesis ID.

### 6.2 Multiple-testing family (Family B Hansen 2005 SPA)

H058 enters **Family B** — the chart-reader cohort Hansen 2005 SPA family — per the synthesis memo §3 Q1 / §6 Family B declaration ([memo](../../../docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md)). Family B membership is `{H057, H058a, H058b, H059, H060}` for `M = 5`; **H050 is the baseline anchor only, not a Family B member.** This split is the Q-R1-1 + Q-R1-12 remediation (mixing H050's within-arm `gated − unconditional` Family A statistic with the cross-arm `arm_gated − H050_gated` Family B statistic in a single composite null is incommensurable). H050's frozen pre-reg Family A (Romano-Wolf step-down) is preserved unchanged.

H058 contributes exactly two Family B entries, one per backbone:

| Family B entry | Statistic |
|---|---|
| H058a (TimesFM-2.5) | `T_{H058a} = SR_{filtered, gated, TimesFM-2.5} − SR_{filtered, gated, H050_LGB}` |
| H058b (Chronos-Bolt-base) | `T_{H058b} = SR_{filtered, gated, Chronos-Bolt-base} − SR_{filtered, gated, H050_LGB}` |

Family B size at H058 entry: `M = 1 (H057) + 2 (H058a + H058b) + 1 (H059) + 1 (H060) = 5`. With `M ≥ 2`, the SPA omega method is **`bootstrap`** per the [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) §Decision two-tier rule (Family B's `M ≥ 2` invokes the bootstrap omega path with shared bootstrap indices across strategies for cross-dependence preservation per Hansen 2005 §2; the `hac` omega is reserved for `M = 1` isolation passes per ADR-0008 §Single-strategy degenerate handling). Hansen 2005 SPA_l / SPA_c / SPA_u variants reported per the ADR; SPA_c is the gate.

## 7. Cost model

`cost_model_id`: `nt8_es_nq_rth_v1` — identical to H050's [src/skie_ninja/backtest/costs/](../../../src/skie_ninja/backtest/) registration. Per-contract commission from [config/instruments.yaml](../../../config/instruments.yaml); RTH-only conservative constant-tick slippage prior pending paper-trade calibration. Inference cost (TSFM forward pass) is **not** charged to the strategy P&L because it is a backtest-time research expense, not a per-trade cost; flagged in `P1-H058-INFERENCE-COMPUTE-BUDGET` for production-deployment costing.

## 8. Inference, gate thresholds, and pretraining-corpus contamination screen

### 8.1 Inference

- Standard errors: Newey–West HAC (Bartlett kernel) with bandwidth selected by the NW 1994 data-dependent rule per [src/skie_ninja/inference/stats/](../../../src/skie_ninja/inference/stats/).
- **Primary inference (paired-differential CI)**: Ledoit & Wolf 2008 studentised time-series bootstrap CI per [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) (`ledoit_wolf_2008_differential_ci`), per-replicate NW 1994 bandwidth. The H058a entry produces a CI for `T_{H058a} = SR_{H058a, gated} − SR_{H050_LGB, gated}`; the H058b entry produces a CI for `T_{H058b} = SR_{H058b, gated} − SR_{H050_LGB, gated}`. CI excluding zero at the one-sided alpha is the primary reading. Per [Ledoit & Wolf 2008, J. Empirical Finance 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002).
- **Corroborative inference (multi-strategy SPA)**: Hansen 2005 SPA on the Family B `M = 5` cohort per §6.2, `omega_method = bootstrap` per ADR-0008 (the two-tier rule selects `bootstrap` because `M ≥ 2`). Hansen 2005, *J. Business & Economic Statistics* 23(4):365-380.
- **Solo `M = 1` SPA pass-through**: when an individual H058 backbone arm is reported in isolation (e.g., during a sensitivity analysis or cycle-disposition memo before all Family B siblings reach `evaluated`), the arm is reported as a single-strategy SPA pass-through per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) §Single-strategy degenerate handling, with `omega_method = hac` and `SingleStrategySPAWarning` captured in the audit log.

### 8.2 Gate thresholds

Defaults from [config/gate.yaml](../../../config/gate.yaml) per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md):

- `alpha`: 0.05 (one-sided).
- `bh_threshold`: 0.10.
- `dsr_activation_size`: project default.
- Power target: 0.80.

### 8.3 Pretraining-corpus contamination screen (binding)

Per the survey [memo §8](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md#8-pretraining-corpus-contamination-assessment) and [Meyer, Kaltenpoth, Zalipski, Müller 2025, arxiv 2510.13654](https://arxiv.org/abs/2510.13654), pretraining-corpus contamination is a first-order risk for any TSFM applied to a target whose underlying series may have appeared in the pretraining corpus. The Meyer et al. abstract is the load-bearing reference:

> "An investigation of existing TSFM evaluation studies identifies two kinds of information leakage: (1) train-test sample overlaps arising from the multi-purpose reuse of datasets and (2) temporal overlap of correlated train and test series. Ignoring these forms of information leakage when benchmarking TSFMs risks producing overly optimistic performance estimates that fail to generalize to real-world settings." — [Meyer, Kaltenpoth, Zalipski, Müller 2025, arxiv 2510.13654](https://arxiv.org/abs/2510.13654), abstract, verified verbatim 2026-04-27.

The survey memo's earlier 47%–184% figure was a fabrication and has been retracted per `P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY` (now closed). Specific case-study magnitudes from the paper body (Madrid transport, COVID stock market) are present but not quoted here pending HTML-body verification at status=running per P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY-MAGNITUDE follow-up. H058 cites the verbatim abstract as the load-bearing reference and does **not** propagate any specific MSE-inflation magnitude into its decision rule.

**Screen procedure (binding, executed once per pre-reg snapshot).** For each backbone `b ∈ {TimesFM-2.5-200M, Chronos-Bolt-base-205M}`, the pretraining-corpus inventory documented in the model card or paper is searched for any series whose name or description matches the substring set:

```
{ '^ES', '^NQ', 'S&P 500', 'Nasdaq 100', 'e-mini', 'e-Mini',
  'equity index futures', 'CME front-month', 'GLBX.MDP3' }
```

at frequency ≤ 1 day. The match output is `{backbone_id: contamination_status}` and is recorded in §11 (the backbone sidecar JSON `contamination_screen` field). A **positive match** triggers backbone exclusion or, if the pre-reg author elects to retain the backbone with a documented contamination magnitude, a `contamination_status = "documented"` record with the specific overlapping series and a quantitative magnitude estimate.

**Screen results (executed 2026-04-27 against published model cards).**

| Backbone | Pretraining corpus per model card | Match against contamination patterns | Status |
|---|---|---|---|
| TimesFM-2.5-200M | "GiftEvalPretrain (Salesforce); Wikimedia Pageviews (cutoff Nov 2023); Google Trends top queries (cutoff EOY 2022); synthetic and augmented data" — [HF model card](https://huggingface.co/google/timesfm-2.5-200m-pytorch) verified 2026-04-27 | No substring match against `{^ES, ^NQ, S&P 500, Nasdaq 100, e-mini, equity index futures, CME front-month, GLBX.MDP3}` in the published corpus inventory; the underlying TimesFM 100B-time-point pretraining detailed in [Das et al. 2024 arxiv 2310.10688](https://arxiv.org/abs/2310.10688) is dominated by Wikipedia pageviews, Google Trends, M4, electricity, traffic, and ARMA-synthetic per the survey memo §8. **The Salesforce GiftEvalPretrain component requires inspection** because the parent project (Salesforce LOTSA / Moirai) explicitly includes "economics" as a domain; if GiftEvalPretrain inherits LOTSA's economics subset this is a contamination vector. The HF card text does not enumerate GiftEvalPretrain's component datasets. | **`unverified — partial`**: no positive match in the surface inventory; GiftEvalPretrain component-level inspection deferred to follow-up `P1-H058-TIMESFM-GIFTEVAL-INSPECTION` before run-time. Cycle disposition gate is conditional on this follow-up resolving to `clean` or `documented`. |
| Chronos-Bolt-base-205M | "Trained on nearly 100 billion time series observations"; "based on T5 encoder-decoder architecture (t5-efficient-base)"; specific data sources not enumerated in the model card; financial datasets not mentioned — [HF model card](https://huggingface.co/amazon/chronos-bolt-base) verified 2026-04-27 | No substring match against the contamination set at the model-card level; specific dataset list per [Ansari et al. 2024 arxiv 2403.07815](https://arxiv.org/abs/2403.07815) appendix not fetched at full-text in this pre-reg session (paper full PDF behind arxiv landing). | **`unverified — appendix-pending`**: no positive match in the surface inventory; full-paper-appendix scan deferred to follow-up `P1-H058-CHRONOS-APPENDIX-INSPECTION` before run-time. Cycle disposition gate is conditional on this follow-up resolving to `clean` or `documented`. |

The contamination screen is **binding**: H058 cannot transition to `status=running` until both follow-ups resolve. A resolved-`documented` outcome with a specific overlapping series (e.g., a daily S&P 500 series in the corpus) requires either backbone exclusion or a documented qualitative penalty applied to the H058 OOS test-set disposition per the Meyer et al. methodology (the survey memo's earlier specific 47%–184% MSE-inflation figure has been retracted per `P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY`; specific case-study magnitudes from the paper body are present but not quoted here pending HTML-body verification at status=running per P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY-MAGNITUDE follow-up; the binding rule here is qualitative not quantitative). The 2024–2025 portion of the H050 test window is treated with extra suspicion because most published TSFM training cutoffs are ≤ 2023 (TimesFM-2.5 explicitly: Wikimedia cutoff Nov 2023, Google Trends EOY 2022 per the model card).

## 9. Stopping rule

Per the cross-cutting Family B binding (synthesis memo §3 Q-R1-8 remediation, follow-up `P1-CHARTREADER-PER-ARM-POWER-CALC` `status=running` blocker): each Family B arm computes its own `n_required_for_power_80` from the dispersion of its OWN paired-differential statistic on a pilot training-fold sample, **not** from the H050 scalar (which is no longer transferable across arms because the test statistic is `T_arm`, not `T_H050`). For H058 this means H058a and H058b each compute their own `n_required` from their respective `T_{H058a}` and `T_{H058b}` pilot-fold dispersion; the cohort fold count is then `max(n_required_per_arm)` across the M=5 Family B cohort, ensuring paired-differential pairing is preserved across all arms.

Max folds: bounded above by the calendar-window limit per H050 §9. Search-budget exceedance (per §5.2 random-search cap) is recorded as right-censoring in the selection log.

## 10. Decision rule

H050-style with a backbone-level disjunction. Per Q-R1-9 remediation: per-backbone `passed=True` requires **both** (a) the per-backbone LW2008 CI excluding zero AND (b) the backbone's specific Family-B SPA column passing at the family-wise alpha. Without (b), the per-backbone LW2008 CI is unadjusted for the within-arm multiplicity introduced by reporting two backbone columns. The Family B SPA absorbs the M=5 cohort multiple-comparison correction; the within-arm `(H058a, H058b)` Bonferroni question is tracked under follow-up `P1-H058-INTERNAL-BONFERRONI`.

- Both backbones `passed=True` (per-backbone LW2008 CI excludes zero AND that backbone's Family-B SPA column passes at family-wise α for both) → `archive(positive)`; promote to paper-trade eligibility.
- Exactly one backbone `passed=True` (under the conditional rule above) → `archive(positive, single-backbone)`; the passing backbone is the canonical H058 reference; the non-passing backbone is recorded as a corroborative null.
- Both backbones with at least one CI excluding zero but the corresponding SPA column failing → `archive(null)` with multiple-testing note.
- Both backbones with CI covering zero → `archive(null)`.
- Realized folds < `max(n_required_per_arm)` for any arm → `archive(null, underpowered)` per the cross-cutting per-arm power binding in §9.
- HMM stationarity pre-check failure per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) → `archive(null, precondition-failed)`.
- Either contamination screen resolves to `documented` with a specific overlapping series at the target frequency → `archive(null, contaminated)` for the affected backbone, regardless of statistical outcome. The clean-screen backbone, if any, proceeds to the standard rule above.

## 11. Reproducibility commitments

- git HEAD (at run): TBD at execution.
- `uv pip freeze` sha (at run): TBD at execution.
- RNG seed: 20260427.
- Dataset checksums: inherited from [H050/data_requirements.md](../H050/data_requirements.md); combined-frame SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`. H058-specific binding in [data_requirements.md](data_requirements.md).
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json` per ADR-0005.
- HMM warm-cold filter diagnostic sidecar: `logs/reproducibility/{run_id}_warm_cold_diagnostic.json` per the H050 warm-cold-diagnostic closure (commit `ec95c09`).
- Walk-forward ledger roll-up SHA256: from the per-fold parquet ledger per Cycle-4 `WalkForwardEngine`.
- **Multi-sidecar `model_hash` composition (binding interim rule per cross-cutting binding 4, amended R-R2-5 per synthesis memo §5)**: H058 has two arm-specific backbone sidecars; the composition first pre-aggregates them into a single arm sidecar SHA256, then composes the canonical outer 4-tuple invariant across all four chart-reader arms. Specifically: `h054_arm_sidecar_sha256 := sha256(sorted_tuple([h054_timesfm_sidecar_sha256, h054_chronos_sidecar_sha256]))`, then `model_hash = sha256(sorted_tuple([h054_arm_sidecar_sha256, hmm_sidecar_sha256, warm_cold_sidecar_sha256, ledger_rollup_sha256]))`. Each component SHA is computed via `skie_ninja.utils.hashing.file_sha256`; the outer composition feeds `ReproLog.model_hash` via `with_model_hash`. The deterministic-sorted-tuple wrappers (inner and outer) neutralise sidecar-write-order non-determinism. The per-arm pre-aggregation is documented per synthesis memo §5 (R-R2-5 amendment) — the outer 4-tuple is invariant across H057/H058/H059/H060; the inner pre-aggregation is arm-specific. Implementation note: this hand-rolled composition is the open follow-up `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` (extracting the pattern into a shared helper); H058 is the second-to-fourth hypothesis to require it (alongside H059 + the warm-cold diagnostic).
- **Backbone-specific sidecars (binding)**: two H058-specific sidecars per run, both feeding into the multi-sidecar `model_hash` composition above:

  - `logs/reproducibility/{run_id}_h054_timesfm.json` — schema `h054_backbone_sidecar_v1`:

    | Field | Type | Description |
    |---|---|---|
    | `backbone_id` | string | Fixed: `"timesfm-2.5-200m-pytorch"` |
    | `backbone_source_uri` | string | HF repo URI: `"hf://google/timesfm-2.5-200m-pytorch"` |
    | `backbone_revision` | string | HF revision SHA pinned at run-time |
    | `backbone_weights_sha256` | string | SHA256 of the local weights file consumed at run-time |
    | `lora_rank` | int | Selected LoRA rank `r ∈ {4, 8, 16}` |
    | `lora_alpha` | int | Selected `α ∈ {8, 16, 32}` |
    | `lora_target_modules` | array[string] | Resolved PEFT target-module list |
    | `lora_learning_rate` | float | Selected LR ∈ `{1e-5, 1e-4, 1e-3}` |
    | `adapter_weights_sha256` | string | SHA256 of the trained LoRA delta-weights file |
    | `head_weights_sha256` | string | SHA256 of the 3-class MLP head weights file |
    | `context_length` | int | Fixed: `512` |
    | `patch_length` | int | Fixed: `32` (TimesFM native) |
    | `head_arch` | object | `{hidden_units: 128, activation: "relu", output_classes: 3}` |
    | `train_protocol` | object | `{phase1_head_only_epochs: 1, phase2_joint_epochs: <selected>, early_stopping_patience: 1}` |
    | `contamination_screen` | object | `{status: "clean" | "unverified" | "documented", checked_against: [..pattern set..], notes: "..."}` |
    | `pretraining_cutoff` | object | `{wikimedia: "2023-11", google_trends: "2022-12", giftevalpretrain: "<inherit>"}` |

  - `logs/reproducibility/{run_id}_h054_chronos.json` — schema `h054_backbone_sidecar_v1` with `backbone_id = "chronos-bolt-base"`, `backbone_source_uri = "hf://amazon/chronos-bolt-base"`, `patch_length = 16`, and `pretraining_cutoff = {chronos_corpus: "<see appendix scan>"}`.

- BLAS thread pinning: per [ADR-0009](../../../docs/decisions/ADR-0009-blas-thread-pinning.md), `OMP_NUM_THREADS = MKL_NUM_THREADS = OPENBLAS_NUM_THREADS = 1` for any KMeans-bearing path (HMM warm start). PyTorch CPU-thread pin handled separately via `torch.set_num_threads(1)` for the same reproducibility rationale (non-associativity of threaded float reductions per [Goldberg 1991, ACM Comp. Surv. 23(1):5-48](https://doi.org/10.1145/103162.103163)). GPU determinism (if used): `torch.use_deterministic_algorithms(True)` plus `CUBLAS_WORKSPACE_CONFIG=:4096:8`; recorded in the sidecar `runtime_env` block.

### 11.1 Look-ahead canary suite for H058

Inherited from H057's brief plus an additional TSFM-context constraint:

1. **Feature PIT canary** (inherited from H050 `P1-H050-FEATURE-PIT-ASSERT`): perturb bar at index `t + 1` in any feature's input slice; assert feature value at index `t` is unchanged.
2. **TSFM context-window canary** (new for H058): at every walk-forward boundary, assert `train_idx[-1] − context_length_b + 1 ≥ train_idx[0]` and `train_idx[-1] + 1 ≥ test_idx[0] − purge` (no test bar enters any training-fold TSFM context window). The assertion is per-fold and per-backbone.
3. **TSFM input-zeroisation canary** (new for H058): perturb the raw OHLCV bar at index `> t` in the substrate; assert the TSFM hidden-state vector at decision bar `t` is bit-identical (under the BLAS-pinned thread setting from §11).
4. **HMM forward-filter causality canary** (inherited from H050): filter output at `t` is a pure function of `y_{1:t}`.
5. **Fold-boundary embargo monotonicity canary** (inherited from H050 Cycle 4 `walk_forward_split`).

All canaries must pass before run; failure is a precondition for `archive(null, precondition-failed)`.

### 11.2 Compute-budget pre-registration

H058 inference cost is non-trivial: 200M-parameter forward passes on a 512-bar context, decision-cadence 1 minute, RTH 09:30-16:00 ET = 390 decisions per session per symbol × 2 symbols = 780/session × ~252 sessions/year × 2-year test window ≈ 393k inferences per backbone. At ~50 ms per CPU forward pass (single-threaded per ADR-0009 pin) this is ~5.5 hours of inference per backbone per cycle, dwarfed by the LoRA fine-tune compute. The total H058 compute envelope is pre-registered as ≤ 168 GPU-hours per backbone on a single-A100 Linux host (a deviation gate; exceeding triggers `archive(null, compute-exceeded)`). Tracked as `P1-H058-COMPUTE-BUDGET-PRE-REG`.

### 11.3 Follow-up references

Open at pre-reg (gating `status=running` where noted, per H057 §11 / H060 §11 precedent):

- `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` — helper-landing for the multi-sidecar composition rule above (R-R1-2/R-R1-3/R-R2-5 remediation; binds the interim per-arm-pre-aggregation + outer-4-tuple composition rule until the helper lands).
- `P1-CHARTREADER-PER-ARM-POWER-CALC` — Q-R1-8 cross-cutting per-arm power binding (gates `status=running`); each Family B arm computes its own `n_required_for_power_80` from its own paired-differential statistic dispersion on a pilot training-fold sample, with cohort fold count = `max(n_required_per_arm)` to preserve Family B paired-differential pairing.
- `P1-H058-TIMESFM-GIFTEVAL-INSPECTION` — pretraining-corpus contamination screen for TimesFM-2.5 (gates `status=running`); GiftEvalPretrain component-level inspection required to confirm zero ES/NQ overlap because the parent Salesforce LOTSA project contains an "economics" domain.
- `P1-H058-CHRONOS-APPENDIX-INSPECTION` — pretraining-corpus contamination screen for Chronos-Bolt-base (gates `status=running`); full-text fetch of [Ansari et al. 2024 arxiv 2403.07815](https://arxiv.org/abs/2403.07815) appendix required.
- `P1-H058-CONTEXT-LENGTH-EMPIRICAL` — out-of-cycle empirical-calibration follow-up on the `context_length = 512` binding (no published literature prescribes empirical optima for intraday equity-index futures direction); results do NOT feed back into H058's pre-reg.
- `P1-H058-FINETUNE-PROTOCOL-EMPIRICAL` — out-of-cycle empirical-calibration follow-up on the Phase-1/Phase-2 PEFT protocol scalars (Phase-1 `epochs = 1`, Phase-2 `patience = 2`); results do NOT feed back into H058's pre-reg (Q-R1-3c remediation).
- `P1-H058-INFERENCE-COMPUTE-BUDGET` — production-deployment costing of TSFM forward-pass cost (not charged to backtest P&L per §7).
- `P1-H058-COMPUTE-BUDGET-PRE-REG` — pre-registration of the ≤ 168 GPU-hours/backbone compute envelope (§11.2 deviation gate).
- `P1-H058-INTERNAL-BONFERRONI` — within-arm `(H058a, H058b)` Bonferroni question; the Family B M=5 cohort SPA absorbs the multiple-comparison correction across arms but the within-arm two-backbone reporting question is tracked here (Q-R1-9 remediation).
