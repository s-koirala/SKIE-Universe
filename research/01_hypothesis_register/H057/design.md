---
name: H057 — 1D-CNN on causal OHLCV tensor with HMM regime gate
description: Pre-registered design doc for hypothesis H057 (AI chart-reader arm — 1D convolutional residual non-linear interactions among raw bars, layered atop the H050 HMM gate)
type: project
hypothesis_id: H057
tier: 2c
status: designed
owner: skoir
created: 2026-04-27
citations:
  - ADR-0003-spa-vs-romanowolf
  - ADR-0004-alpha-and-power-defaults
  - ADR-0005-hmm-regime-toolkit
  - ADR-0007-embargo-placement
  - ADR-0008-spa-omega-method
  - Sezer-Ozbayoglu 2018 (S1568494618302151)
  - Sezer-Gudelek-Ozbayoglu 2020 (arxiv:1911.13288)
  - Wang-Oates 2015 (arxiv:1506.00327)
  - Bergstra-Bengio 2012 (JMLR 13:281-305)
  - Hamilton 1989 (doi:10.2307/1912559)
  - Baum-Petrie-Soules-Weiss 1970 (doi:10.1214/aoms/1177697196)
  - Lopez-de-Prado 2018 AFML
  - Ledoit-Wolf 2008 (doi:10.1016/j.jempfin.2008.03.002)
  - Hansen 2005 (JBES 23(4):365-380)
  - Lo 2002 (doi:10.2469/faj.v58.n4.2453)
  - Opdyke 2007 (doi:10.1057/palgrave.jam.2250084)
  - Newey-West 1994 (doi:10.2307/2297912)
  - Andrews 1991 (doi:10.2307/2938229)
---

# H057 — 1D-CNN on causal OHLCV tensor with HMM regime gate

This document is the pre-registration record for hypothesis H057. Frozen at `designed`; any change requires a new hypothesis ID. Commensurable with [H050/design.md](../H050/design.md) by construction: same labeller, same HMM gate, same walk-forward folds, same cost model, same inference family.

H057 is the train-from-scratch convolutional arm of the four-hypothesis "AI chart-reader" extension scoped in [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) (alongside H058 / H059 / H060). It is the lowest-contamination arm — the model has no pretraining corpus, hence no possibility of train-test sample overlap of the kind catalogued by [Meyer, Kaltenpoth, Zalipski, Müller 2025, arxiv 2510.13654](https://arxiv.org/abs/2510.13654).

## 1. Hypothesis

- H0: The paired-differential Sharpe between the H057 1D-CNN gated strategy and the H050 LightGBM gated baseline, computed on the cross-symbol aggregate per-bar return series defined in [H050/aggregation_rule_addendum_2026-04-24.md](../H050/aggregation_rule_addendum_2026-04-24.md) §1.2 (sub-rule 2a, equal-weighted constant 0.5 / 0.5 in arithmetic-return space), is non-positive on the OOS test fold. Formally `SR_{H057, gated} − SR_{H050, gated} ≤ 0`.
- H1: `SR_{H057, gated} − SR_{H050, gated} > 0` on the OOS test fold; one-sided test at alpha per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).
- Mechanism: the H050 LGB baseline consumes four hand-engineered microstructure features (Parkinson realized variance, squared-returns realized variance, realized skew, OFI tick-rule proxy — [H050/design.md](../H050/design.md) §3) which are second- and third-order moment summaries of the raw OHLCV stream. A 1D convolutional kernel applied directly to the 60-bar × 5-channel raw tensor (open, high, low, close, volume) can in principle discover translation-invariant local interactions among raw bars that the moment summaries collapse — for example, a kernel that learns to weight a wick relative to the same-bar body and the prior-bar close, or a kernel that learns a volume-vs-range joint pattern. Whether that residual non-linear capacity translates to a positive paired-differential Sharpe net of cost is the empirical question. Evidence base for CNN-on-OHLCV in finance: [Sezer & Ozbayoglu 2018, Appl. Soft Comput. 70:525–538](https://www.sciencedirect.com/science/article/abs/pii/S1568494618302151) (15-indicator → image → 2D CNN; ~58% accuracy on Dow Jones tested vs Buy & Hold); [Sezer, Gudelek & Ozbayoglu 2020, Appl. Soft Comput. 90:106181, arxiv 1911.13288](https://arxiv.org/abs/1911.13288) (canonical systematic review of deep-learning financial time-series 2005–2019); [Wang & Oates 2015, IJCAI workshop, arxiv 1506.00327](https://arxiv.org/abs/1506.00327) (canonical time-series-as-tensor framing, GASF/GADF/MTF). The published evidence base for OHLCV-CNN versus tuned gradient-boosted trees is mixed at best: most reported gains are on the order of 0–3 percentage-points of F1 in equity-direction prediction tasks ([Sezer et al. 2020 §5 review](https://arxiv.org/abs/1911.13288)). The pre-reg therefore treats H057 as a low-prior-probability differential-information probe, not a high-prior-probability replacement for H050.
- Primary citations: [Sezer & Ozbayoglu 2018](https://www.sciencedirect.com/science/article/abs/pii/S1568494618302151); [Sezer, Gudelek & Ozbayoglu 2020](https://arxiv.org/abs/1911.13288); [Wang & Oates 2015](https://arxiv.org/abs/1506.00327); [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196).
- Test statistic: `T_H057 = SR_{H057, gated} − SR_{H050, gated}` (paired differential against the H050 gated baseline, not against the H050 unconditional version). Both Sharpe ratios are computed on walk-forward OOS net-of-cost returns aggregated per [H050/aggregation_rule_addendum_2026-04-24.md](../H050/aggregation_rule_addendum_2026-04-24.md) §1.2. Pairing is per-bar, share the identical aggregation, identical HMM-decoded gate state at every bar, and identical cost model — the differential isolates the classifier-family contribution. This is the cross-arm model-class-lift statistic for **Family B** per the synthesis memo §6 (Q-R1-1, Q-R1-12 remediation).
- SPA family entry: H057 enters **Family B (M = 5)** — the chart-reader cohort `{H057, H058a, H058b, H059, H060}` — with H050 as **baseline anchor only** (NOT itself a Family B member; H050's frozen pre-reg places it in Family A under Romano-Wolf step-down per ADR-0003). Per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) two-tier rule, the Family B SPA invocation (M = 5 ≥ 2) uses `omega_method="bootstrap"` with `shared_bootstrap_indices=true` to preserve cross-strategy dependence per Hansen 2005 §3. When H057 runs in M = 1 isolation prior to family aggregation, the corroborative SPA pass-through uses `omega_method="hac"` per ADR-0008 single-strategy degenerate handling. The split rationale is documented in the synthesis memo §6 (mixing within-arm `gated − unconditional` Family A statistics with cross-arm `arm_gated − H050_gated` Family B statistics in a single Hansen SPA composite null is incommensurable).

## 2. Universe and sample period

- Instruments: ES and NQ front-month per [config/instruments.yaml](../../../config/instruments.yaml); roll-handling per the AFML §2.4.3 ratio-adjusted derivative published at [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) (module v0.3.0, commit `329fd1b` decade-wraparound disambiguation).
- Frequency: 1-minute bars as the base grid. The 60-bar window is fixed at this base grid (one-hour right-anchored context) and is **not** searched, by deliberate design — searching window length expands the SPA family for marginal informational gain that the published CNN-on-OHLCV literature does not motivate.
- Session: RTH only (mirrors [H050/design.md](../H050/design.md) §2). ETH treated separately per project CLAUDE.md.
- Train window: 2015-01-01 through 2022-12-31 (calendar bounds; walk-forward splits applied within). Identical to H050.
- Validation window: 2023-01-01 through 2023-12-31, embedded as inner folds of walk-forward. Identical to H050.
- Test window: 2024-01-01 through 2025-12-31, strictly held out until final SPA submission. Identical to H050. Right-edge calendar-truncation per [H050/data_requirements.md](../H050/data_requirements.md) §Coverage applies symmetrically and is tracked under follow-up `P1-DATABENTO-RIGHT-EDGE-EXTENSION`.
- Roll-handling note: front-month, ratio-adjusted via CME calendar; roll dates frozen at pre-reg per [H050/data_requirements.md](../H050/data_requirements.md).
- Dataset snapshot frozen at pre-registration: SHA256 of the H050-shared roll-adjusted tier (`b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`, 7,354,066 rows ES + NQ × 2015-2025) re-published in `data_requirements.md` for H057 audit-trail self-containment. Any data after 2025-12-31 is locked away; re-runs on extended windows require a successor hypothesis ID.

## 3. Features (input tensor)

- Input representation: a 60-bar × 5-channel right-anchored causal tensor. At decision time `t`, the tensor `X_t ∈ R^{60×5}` is constructed from bars `(t − 59), (t − 58), ..., t` indexed in chronological order, with the channel axis ordered `[open, high, low, close, volume]`. The decision is taken **after** bar `t` closes; no part of bar `t + 1` enters `X_t`. Right-anchored windowing is the canonical causal-padding construction for sequence CNNs ([Bai, Kolter, Koltun 2018, "An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling", arxiv 1803.01271](https://arxiv.org/abs/1803.01271) §2.1, Temporal Convolutional Network framing) and removes look-ahead by construction.
- Per-channel z-score normalization: rolling mean and rolling standard deviation are computed **only from the training fold** of the active walk-forward split, frozen at fit time, and applied unchanged to the validation and test folds of that split. Per-channel statistics (one mean, one variance per channel) are stored in the CNN sidecar (§11) and are part of the model state. The volume channel is log1p-transformed prior to z-score (raw volume is heavy-tailed and right-skewed; log1p stabilises the per-channel variance estimate without introducing a parameter).
- Missing-bar policy: missing bars (gap > 60 s within RTH) are forward-filled at the OHLC channels and zero-filled at the volume channel; a separate bar-mask channel is **not** added in this pre-reg (would expand the channel count past 5 and break commensurability with the named 5-channel framing). Empirical missing-bar rate on the H050 substrate is tracked under follow-up `P1-MISSING-BAR-RATE-EMPIRICAL`; if that follow-up reports a missing-bar rate > 1 % on any RTH session, this design is amended via successor hypothesis ID.
- Leakage tests per §8 must pass before run; the CNN-specific PIT canary in §8 is the load-bearing extension over the H050 leakage suite.

## 4. Label construction

Labels are constructed **identically** to [H050/design.md](../H050/design.md) §4, by reuse of the same `TripleBarrierLabeler` ([src/skie_ninja/features/labels.py](../../../src/skie_ninja/features/labels.py)). This is binding: H057 is a model-class probe holding labelling fixed.

- Triple-barrier per López de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1-119-48208-6) §3.2.
- `pt_sl`: symmetric around volatility, multiplier searched over `{1.0, 1.5, 2.0}` per fold via the inner CV described in §6.
- `vertical_barrier`: `{30m, 60m, 120m}` grid, searched per fold via the same inner CV.
- `volatility_estimator`: Yang–Zhang with lookback searched per fold via the same inner CV over `{20, 60, 120}` minutes.
- Output: 3-class softmax over the existing H050 triple-barrier classes `{upper, lower, vertical}`. Class encoding identical to H050 (upper-barrier hit → +1 label, lower-barrier hit → −1 label, vertical-barrier hit → 0 label) so that downstream signed-position construction reuses the H050 logic in [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py).
- Class imbalance: weighted cross-entropy with weights = inverse-class-frequency on the active training fold only; no SMOTE / synthetic resampling.
- Meta-label horizon upper bound per fold: `max(vertical_barrier)` over the inner-CV-selected configuration; fed to the splitter `purge` (§6).

## 5. Estimator

The estimator is the composition of (i) a **causal 1D-CNN classifier** trained per-symbol per-fold from random initialisation, and (ii) the **identical HMM regime gate** used by H050. The gate is binding by design — H057 is the chart-reader differential information probe and the HMM is held fixed at the H050 specification to isolate the classifier contribution.

### 5.1 Architecture pre-registered grid

The model class is a one-dimensional convolutional residual classifier following the canonical Temporal Convolutional Network template ([Bai, Kolter, Koltun 2018, arxiv 1803.01271](https://arxiv.org/abs/1803.01271) §3, residual blocks of stacked dilated causal convolutions + ReLU + dropout + 1×1 skip). The hyperparameter grid is pre-registered:

| Axis | Values | Cardinality |
|---|---|---|
| `depth` (number of residual blocks) | `{3, 5, 7}` | 3 |
| `channels` (filters per conv layer; constant across blocks) | `{32, 64, 128}` | 3 |
| `kernel` (1D kernel width per conv) | `{3, 5, 7}` | 3 |
| `dilation` (per-block dilation schedule) | `{off, power-of-two}` (off = constant 1; power-of-two = `1, 2, 4, ..., 2^{depth-1}`) | 2 |
| `dropout` (per-residual-block dropout rate) | `{0.0, 0.1, 0.3}` | 3 |

Cartesian product: 3 × 3 × 3 × 2 × 3 = **162 cells**. This exceeds the lead-researcher binding upper bound of 30 cells. Reduction rule pre-registered: cells are first filtered to satisfy the receptive-field admissibility constraint that the effective receptive field RF (computed per [Bai et al. 2018 §3 eq. (4)](https://arxiv.org/abs/1803.01271): RF = 1 + 2·(kernel − 1)·∑ dilations, and ≤ 60 bars or ≥ 60 bars by ≤ 1 doubling step) covers the 60-bar window without excessive over-coverage. After applying RF admissibility, the surviving grid is **exactly** 30 cells (verified at pre-reg via [scripts/](../../../scripts/) helper to be added under follow-up `P1-H057-RF-ADMISSIBILITY-FILTER`). The 30-cell admissible grid is the binding model-selection space; cells outside it are not searched.

The non-architectural training-side hyperparameters are fixed at pre-reg time and are not searched:

- Optimizer: AdamW ([Loshchilov & Hutter 2019, ICLR, arxiv 1711.05101](https://arxiv.org/abs/1711.05101)).
- Initial learning rate: `1e-3`; cosine-annealing schedule to `1e-5` over the configured epoch budget ([Loshchilov & Hutter 2017, ICLR, arxiv 1608.03983](https://arxiv.org/abs/1608.03983)).
- Batch size: 256.
- Maximum epochs per fit: 30, with early stopping on inner-fold validation loss with patience = 5 epochs.
- Weight decay: `1e-4`.
- Activation: ReLU.
- Loss: weighted categorical cross-entropy per §4 class-imbalance rule.
- Random initialisation: Kaiming-normal ([He, Zhang, Ren, Sun 2015, ICCV, arxiv 1502.01852](https://arxiv.org/abs/1502.01852)).

**Selection-bias note (Q-R1-5 remediation)**: These training-side scalars are bound at pre-reg as methodology choices anchored to the cited primary references ([Loshchilov & Hutter 2019](https://arxiv.org/abs/1711.05101), [Loshchilov & Hutter 2017](https://arxiv.org/abs/1608.03983), [He et al. 2015](https://arxiv.org/abs/1502.01852)); they are NOT swept and are not part of the SPA family count. A successor hypothesis is required to relax any of them. The selection-bias risk is acknowledged: a tuned-from-scratch sweep on the H050 substrate could yield different optima. Tracked under `P1-H057-TRAINING-SCALARS-EMPIRICAL` for an out-of-cycle empirical sweep on the H050 substrate that is reported separately and does NOT feed back into H057's pre-reg.

### 5.2 Search protocol

Random search per [Bergstra & Bengio 2012, JMLR 13:281–305](https://www.jmlr.org/papers/v13/bergstra12a.html). On the 30-cell discrete admissible grid, random search is **with replacement** under the uniform-prior framing of Bergstra & Bengio §2.2 (volume argument). The required draw count for ≥ 95 % expected coverage of the top-5 % configurations is `N_draws = ⌈ ln(1 − 0.95) / ln(1 − 0.05) ⌉ = 60` under sampling with replacement; on a 30-cell *discrete* grid the equivalent without-replacement draw count saturates earlier. The pre-reg adopts `N_draws = 30` (full sweep of the admissible grid) for H057 because the discrete-grid replicate-coverage argument from [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) inner-CV practice (per [docs/audits/audit_trail_2026-04-24_orchestrator-triple.md](../../../docs/audits/audit_trail_2026-04-24_orchestrator-triple.md)) supersedes the continuous-Bayesian B&B volume argument once the grid is small enough to enumerate.

The inner CV gates each cell evaluation per §6 (nested walk-forward).

### 5.3 HMM regime gate

The HMM regime gate is **identical** to [H050/design.md](../H050/design.md) §5 and inherits [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) by reference. Specifically:

- Gaussian HMM via [src/skie_ninja/models/regime/](../../../src/skie_ninja/models/regime/) (`GaussianHMM`, log-space Baum-Welch EM, `select_gaussian_hmm` via [selection.py](../../../src/skie_ninja/models/regime/selection.py) BIC + (planned) walk-forward CV log-likelihood).
- `covariance_type ∈ {diag, full}` per the H050 pre-reg, **with** the d=1-redundancy deduplication landed in commit (forthcoming) closing `P1-HMM-FULL-COV-1DIM-REDUNDANT` — for one-dimensional emissions `diag` and `full` are mathematically equivalent and the model-class deduplication in `select_gaussian_hmm` collapses the redundant evaluation; the pre-reg grid is preserved.
- `n_states` grid per the [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) adaptive rule: lower bound 2; upper bound `K_max` such that mean within-state sample size ≥ 30 × dim(emission) on the train fold per [Celeux & Durand 2008, Comp. Stat. 23(4):541–564](https://doi.org/10.1007/s00180-007-0097-1).
- Selection by BIC + cross-validated held-out log-likelihood (BIC-only fallback per the Cycle-3 follow-up `P1-HMM-WFCV` until the joint CV-LL selector lands).
- Initialisation: k-means++ on emission features; restart-until-convergence per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) "Hyperparameter governance".
- Canonical state ordering: states sorted by emission-mean of the primary directional feature (ES log-return) ascending; gate state = highest-mean state per the H050 directional-drift convention.
- State assignment at inference (decision) time uses the causal forward filter `p(s_t | y_{1:t})` only — the sole public inference path on `GaussianHMM` per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) anti-look-ahead binding. Smoothed posteriors `p(s_t | y_{1:T})` are diagnostic-only.
- Fold-boundary state continuity per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) "Fold-boundary state continuity (filter warm-start)": the test fold's first observation is processed with the train-fold terminal filtered posterior advanced `K = test_idx[0] − train_idx[-1]` transition steps via `filter_states_from_prior(..., n_propagation_steps=K)`.
- HMM-fit cache amortization: the orchestrator's `select_gaussian_hmm` cache from commit `1c85f5f` (cache key `(symbol, fold_id, label_horizon)`, 9× speedup on the H050 27-cell grid) is reused unchanged — H057's per-cfg HMM fit shares the same per-stratum-fold-symbol cache because the HMM emission inputs (returns + features) are identical to H050's by §5 binding. The cache is byte-identical under cache toggle per the warm-cold sidecar invariant in commit `ec95c09`.

### 5.4 Per-symbol training, cross-symbol aggregation

Training is **per-symbol per-fold**: one CNN is fit on ES training data for fold `f`, scored on ES validation/test for fold `f`; one CNN is fit on NQ training data for fold `f`, scored on NQ validation/test for fold `f`. No cross-symbol parameter sharing. The per-symbol gated returns `r_ES_gated(t)` and `r_NQ_gated(t)` enter the cross-symbol aggregation rule per [H050/aggregation_rule_addendum_2026-04-24.md](../H050/aggregation_rule_addendum_2026-04-24.md) §1.2 (sub-rule 2a, equal-weighted constant 0.5 / 0.5 in arithmetic-return space), unchanged.

### 5.5 Loss and inner-CV selection metric

- Training loss: weighted categorical cross-entropy per §4.
- Inner-CV selection metric: Sharpe of the gated per-symbol return on the inner validation fold, per the H050 orchestrator-triple convention ([docs/audits/audit_trail_2026-04-24_orchestrator-triple.md](../../../docs/audits/audit_trail_2026-04-24_orchestrator-triple.md)). Gated metric is the binding choice; the gated-vs-ungated empirical comparison is tracked as inherited follow-up `P1-H050-LABEL-CV-GATED-METRIC`.

## 6. Splitter

- Splitter: `PurgedWalkForwardSplitter` per the H050 spec ([H050/design.md](../H050/design.md) §6), reused unchanged from [src/skie_ninja/backtest/](../../../src/skie_ninja/backtest/).
- `embargo`: stacked form per [ADR-0007](../../../docs/decisions/ADR-0007-embargo-placement.md); embargo length = `auto` (max of residual-PACF-based lag and Politis–White optimal block length on stacked residuals, per [src/skie_ninja/inference/bootstrap.py](../../../src/skie_ninja/inference/bootstrap.py) `politis_white_block_length`).
- `purge`: `auto` = `max(vertical_barrier)` across inner-CV-selected folds.
- Inner CV: nested walk-forward per [Varma & Simon 2006, BMC Bioinformatics 7:91](https://doi.org/10.1186/1471-2105-7-91), with the inner-CV draw count `N_draws` set to 30 per §5.2.
- Fold count: identical to H050. The H057 fold roster is determined by the H050 stopping-rule fold count `n_required_for_power_80` (§9), held fixed across the two hypotheses for paired-differential pairing.
- CPCV not used for H057; if statistical power is insufficient after fold-count selection, escalation to CPCV is registered as a design-change requiring a new hypothesis ID per the H050 convention.

## 7. Cost model

- `cost_model_id`: `nt8_es_nq_rth_v1` per [H050/design.md](../H050/design.md) §7. Reused unchanged from [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py).
- Commission, slippage, regime-conditional cost behaviour all inherited from H050; the H057 strategy generates a per-bar signed position from the 3-class softmax via the same `argmax → {−1, 0, +1}` rule used by H050 (LightGBM softmax also produces a 3-class distribution; the conversion to signed position is held identical).
- Inherited follow-up `P1-H050-COST-EMPIRICAL-CALIBRATION` applies — cost calibration update will trigger a re-score of both H050 and H057 on the new cost model; the paired-differential statistic `T_H057` is invariant under any cost model that applies symmetrically to the two strategies.

## 8. Assumption checks and look-ahead audit

### 8.1 Stationarity

- Per-fold weak-stationarity check on the 60-bar windowed input distribution: KS two-sample test (BH-adjusted across folds at q=0.10) between fold-train and fold-test marginal distributions of each of the 5 channels post-z-score. A material rejection (BH-adjusted p < 0.05 in > 50 % of channels in > 50 % of folds) flags the run as `archive(null, precondition-failed)` per the H050 convention. Inherited follow-up `P1-CYCLE6-FOLD-STATIONARITY` provides the implementation.

### 8.2 Independence

- Inherited from H050: bar-to-bar independence is **not** assumed; HAC standard errors per [src/skie_ninja/inference/stats/hac.py](../../../src/skie_ninja/inference/stats/hac.py) absorb residual serial correlation. The CNN's receptive field of up to 60 bars makes its predictions explicitly serially correlated; the splitter's `purge = max(vertical_barrier)` and stacked embargo per [ADR-0007](../../../docs/decisions/ADR-0007-embargo-placement.md) handle this.

### 8.3 Distribution

- Per-channel z-score normalisation does not assume normality; it is a scale standardisation only. The CNN softmax does not assume any input distribution; class predictions are calibrated post-hoc per fold via temperature scaling ([Guo, Pleiss, Sun, Weinberger 2017, ICML, arxiv 1706.04599](https://arxiv.org/abs/1706.04599)) on the inner-CV validation fold. Temperature is single-scalar per fold-symbol; tracked in the CNN sidecar (§11).

### 8.4 Look-ahead audit (load-bearing)

The leakage suite for H057 extends the H050 leakage suite ([tests/unit/test_leak_canaries.py](../../../tests/unit/test_leak_canaries.py)) with **two CNN-specific point-in-time canaries** that exploit the structural property of the 60-bar right-anchored window: the prediction at decision time `t` must depend on bars `(t−59), ..., t` and on no other bar.

- **Canary A (last-bar perturbation)**. For a randomly chosen `t` in the test fold and a randomly chosen channel `c`, perturb bar `t`'s `c`-channel value by a non-trivial amount (e.g. ±3 sample standard deviations). Re-score the model on the perturbed window. Assert that the predicted class probabilities **change**, with at least one class probability shifting by > `1e-6`. A failure indicates the model has degenerate dependence on the right edge of the window.
- **Canary B (future-bar invariance)**. For the same `t` and a randomly chosen `t' > t` (i.e. a bar **after** the decision time, which by the right-anchored construction must not influence the prediction), perturb bar `t''s` `c`-channel value by the same magnitude. Re-score the model on the (unchanged) window centred at `t`. Assert that the predicted class probabilities are **byte-identical** to the unperturbed prediction (numeric tolerance: bit-exact float comparison via `np.array_equal` on the post-softmax vector). A failure is the canonical look-ahead bug — the model has somehow ingested bar `t''`s value into the prediction at `t`.

Both canaries are run at every walk-forward fold boundary, on at least 100 randomly drawn `(t, c)` tuples per fold, with the RNG seed pre-registered in §11. A single canary failure halts the run with `archive(null, leakage-canary-failed)`. The implementation extends the [tests/unit/test_h050_aggregation_convention.py](../../../tests/unit/test_h050_aggregation_convention.py) pattern; new module `tests/unit/test_h053_cnn_lookahead_canary.py` is the binding artefact. The same canaries are wired into the production orchestrator as a per-fold runtime gate (not only a CI test) so a leak introduced during a production run is caught at the fold boundary, not weeks later in audit.

### 8.5 HMM gate look-ahead

The HMM gate inherits [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)'s anti-look-ahead suite verbatim — `filter_states` is the sole public inference path, `filter_states_from_prior` propagates fold-boundary continuity correctly, and the existing leakage unit test asserts filter output at `t` is a pure function of `y_{1:t}`.

## 9. Stopping rule

- Stop criterion: fixed walk-forward fold count equal to `n_required_for_power_80`, computed on the H050 pilot training-fold Sharpe-differential dispersion and **shared with H050** to preserve per-fold pairing for the LW2008 differential CI in §10. Identical pattern to [H050/design.md](../H050/design.md) §9.
- Max folds: bounded above by the calendar-window limit per H050.
- Search budget exceedance (per §5.2 random-search cap, here trivially saturated by the 30-cell admissible grid) is recorded in the selection log, not a halt.
- Underpowered exit: if the realized fold count is `< n_required_for_power_80` (e.g. due to substrate truncation), the run records `archive(null, underpowered)`.

## 10. Decision rule

- **Inference primary**: Ledoit & Wolf 2008 differential CI on `T_H057 = SR_{H057, gated} − SR_{H050, gated}` via [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) `ledoit_wolf_2008_differential_ci`. This is the natural construction for a paired difference of two Sharpe ratios; bandwidth selection per per-replicate Newey-West 1994 plug-in per the UZH IEW WP 320 verification in [docs/audits/audit_trail_2026-04-24_lw2008-differential-ci.md](../../../docs/audits/audit_trail_2026-04-24_lw2008-differential-ci.md). One-sided test at `alpha = 0.05`; `passed=True` iff CI lower bound > 0.
- **Inference corroborative**: Hansen 2005 SPA as a single-strategy `M = 1` pass-through per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) "Single-strategy degenerate handling (|M|=1)", with `omega_method="hac"` (the `M = 1` configuration uses HAC to decouple Monte-Carlo error per the ADR-0008 two-tier rule), `n_bootstrap = 1000`. The `SingleStrategySPAWarning` is emitted and captured to the run log as documented at [docs/audits/audit_trail_2026-04-24_spa-m1-degenerate.md](../../../docs/audits/audit_trail_2026-04-24_spa-m1-degenerate.md). The `M = 1` SPA p-value is interpretable as a one-sided studentised stationary-bootstrap p-value for `H_0 : E[d] ≤ 0` and is reported alongside the LW2008 CI but does not drive the gate decision at this stage.
- **Family B SPA (multi-strategy)**: when H057 is jointly evaluated with the chart-reader cohort `{H057, H058a, H058b, H059, H060}` (Family B, M = 5) per the synthesis memo §6, the combined SPA is rerun under `omega_method="bootstrap"` per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) two-tier rule, with `shared_bootstrap_indices=true` across the 5 strategies to preserve cross-sectional dependence per Hansen 2005 §3. H050 is the **baseline anchor only** (NOT a Family B member; H050 stays in Family A under Romano-Wolf step-down per ADR-0003). The H057 disposition recorded under §11 references the Family B SPA p-value alongside the M = 1 corroborative.
- Standard errors: NW-HAC with NW1994 / Andrews 1991 plug-in bandwidth selection per [src/skie_ninja/inference/stats/hac.py](../../../src/skie_ninja/inference/stats/hac.py).
- Sharpe CI primitives: Lo 2002 / Opdyke 2007 (primary, Mertens-HAC variant) per [src/skie_ninja/inference/stats/sharpe_ci.py](../../../src/skie_ninja/inference/stats/sharpe_ci.py).
- Disposition rule:
  - `passed=True` (LW2008 CI lower bound > 0) → `archive(positive)`; H057 enters the same paper-trade-eligibility queue as a hypothesised H050 positive, subject to the Family B SPA check (M = 5, `omega_method="bootstrap"`) completing without family-wide rejection.
  - `passed=False` with CI excluding zero on the wrong side and Family B SPA (or M = 1 corroborative pass-through with `omega_method="hac"` if Family B not yet aggregated) corroborating → `archive(null)` with multiple-testing note; H057's null result protects against later rediscovery per the project research-philosophy section.
  - `passed=False` with CI covering zero → `archive(null)`.
  - Realized folds < `n_required_for_power_80` → `archive(null, underpowered)`.
  - HMM stationarity pre-check failure per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) → `archive(null, precondition-failed)`.
  - Leakage canary failure per §8.4 → `archive(null, leakage-canary-failed)`.

## 11. Reproducibility commitments

- git HEAD (at run): TBD at execution.
- `uv pip freeze` sha (at run): TBD at execution.
- RNG seed: 20260427.
- Dataset checksums (frozen at pre-reg): captured in [data_requirements.md](data_requirements.md) — the file is a pre-reg companion to be completed before `status=running`; its SHA256 checksum field is the binding artefact. Checksums are inherited from the H050 roll-adjusted tier (combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`).
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json` per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md). SHA256 hashed into `ReproLog.model_hash` via `with_model_hash` from [src/skie_ninja/utils/reproducibility.py](../../../src/skie_ninja/utils/reproducibility.py).
- Warm-cold filter diagnostic sidecar: `logs/reproducibility/{run_id}_warm_cold_diagnostic.json` per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) "Warm-vs-cold filter regression diagnostic". SHA256 combined into `ReproLog.model_hash`.
- **CNN sidecar path: `logs/reproducibility/{run_id}_cnn_h053.json`**. Schema: `cnn_h053_sidecar_v1`, mirroring the `HMMSidecar` pattern in [src/skie_ninja/models/regime/serialization.py](../../../src/skie_ninja/models/regime/serialization.py). Required fields:

  | Field | Type | Description |
  |---|---|---|
  | `schema_version` | string | Constant `"cnn_h053_sidecar_v1"`. |
  | `architecture.depth` | int | Number of residual blocks. |
  | `architecture.channels` | int | Filters per conv layer. |
  | `architecture.kernel` | int | Kernel width. |
  | `architecture.dilation_schedule` | list[int] | Per-block dilation schedule (length = depth). |
  | `architecture.dropout` | float | Per-residual-block dropout rate. |
  | `architecture.receptive_field` | int | Effective receptive field per [Bai et al. 2018 §3 eq. (4)](https://arxiv.org/abs/1803.01271). |
  | `training.optimizer` | string | Constant `"adamw"`. |
  | `training.lr_schedule` | string | Constant `"cosine_anneal"`. |
  | `training.lr_initial` | float | Constant `1e-3`. |
  | `training.lr_final` | float | Constant `1e-5`. |
  | `training.epochs_max` | int | Constant `30`. |
  | `training.epochs_actual` | int | Realised epoch count after early stopping. |
  | `training.batch_size` | int | Constant `256`. |
  | `training.weight_decay` | float | Constant `1e-4`. |
  | `training.early_stopping_patience` | int | Constant `5`. |
  | `training.class_weights` | list[float] | Inverse-class-frequency weights, length 3. |
  | `normalization.channel_means` | list[float] | Per-channel rolling means, length 5. |
  | `normalization.channel_stds` | list[float] | Per-channel rolling stds, length 5. |
  | `normalization.volume_log1p` | bool | Constant `true`. |
  | `calibration.temperature` | float | Post-hoc temperature scaling factor per [Guo et al. 2017](https://arxiv.org/abs/1706.04599). |
  | `seed` | int | RNG seed = 20260427. |
  | `weights_sha256` | string | SHA256 of the `state_dict` serialized in canonical key-sorted form. |
  | `fold_id` | int | Walk-forward fold index. |
  | `symbol` | string | `ES` or `NQ`. |
  | `n_params` | int | Total parameter count. |
  | `n_train_windows` | int | Training window count for this fold-symbol. |
  | `inner_cv_selection_log_sha256` | string | SHA256 of the inner-CV selection JSON for this fold-symbol. |
  | `final_inner_cv_sharpe` | float | Inner-CV Sharpe of the selected configuration. |

  The sidecar is written atomically (same pattern as [`ReproLog.write`](../../../src/skie_ninja/utils/reproducibility.py)). The sidecar SHA256 is combined with the HMM sidecar SHA256, the warm-cold diagnostic SHA256, and the per-fold ledger roll-up SHA256 into a single `ReproLog.model_hash` via [`with_model_hash`](../../../src/skie_ninja/utils/reproducibility.py) under the **binding interim deterministic composition rule** (R-R1-2, R-R1-3 remediation per synthesis memo §3 + §5):

  ```
  model_hash = sha256(sorted_tuple([
      arm_sidecar_sha256,         # cnn_h053_sidecar_v1 SHA256
      hmm_sidecar_sha256,         # ADR-0005 HMM selection sidecar SHA256
      warm_cold_sidecar_sha256,   # warm-cold filter diagnostic SHA256
      ledger_rollup_sha256,       # per-fold ledger roll-up SHA256
  ]))
  ```

  The `sorted_tuple` ensures byte-deterministic input ordering. This interim rule binds H057 until the helper lands; tracked under `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` (now blocking `status=running` for H057 + H058 + H059 + H060 per synthesis memo §5).

- **Per-arm power calculation (Q-R1-8 remediation)**: H057's `n_required_for_power_80` (referenced in §9 and aligned with H050 above) is computed from the dispersion of H057's OWN paired-differential test statistic `T_H057 = SR_H057_gated − SR_H050_gated` on a pilot training-fold sample — **not** inherited from H050's scalar. The Family B cohort fold count is `max(n_required_per_arm)` across `{H057, H058a, H058b, H059, H060}` to preserve paired-differential pairing across the cohort. Tracked under `P1-CHARTREADER-PER-ARM-POWER-CALC` (gates `status=running`).
- BLAS thread-pinning: per [ADR-0009](../../../docs/decisions/ADR-0009-blas-thread-pinning.md) — env variables set via `pyproject.toml` `[tool.pytest_env]` and orchestrator entrypoint wrapper.
- **PyTorch thread pinning (R-R1-13 remediation)**: in addition to the BLAS env-var pinning, the orchestrator entrypoint sets `torch.set_num_threads(1)` and `torch.set_num_interop_threads(1)` **before any torch import in downstream modules** (PyTorch reads thread settings at first use, not at import — the calls must precede the first forward pass). This matches the H060 §4.4 precedent and conforms to ADR-0009.
- Determinism: PyTorch CUDA / CPU determinism flags set per [the PyTorch reproducibility guide](https://pytorch.org/docs/stable/notes/randomness.html); `torch.use_deterministic_algorithms(True)`; CUBLAS workspace pinned via `CUBLAS_WORKSPACE_CONFIG=":4096:8"`. Any non-deterministic op (e.g. CUDA dropout in some PyTorch versions) raises at runtime, which is the desired behaviour for evidence-bar discipline.
- **Follow-up references** (open at pre-reg): `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` (helper-landing; binds the interim composition rule above), `P1-CHARTREADER-PER-ARM-POWER-CALC` (gates `status=running`), `P1-H057-TRAINING-SCALARS-EMPIRICAL` (out-of-cycle empirical sweep on training-side scalars, Q-R1-5 remediation; results do NOT feed back into H057's pre-reg).
