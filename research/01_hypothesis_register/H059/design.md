---
name: H059 — Open VLM (Qwen2.5-VL-3B) LoRA fine-tuned on rendered candlestick chart with HMM regime gate
description: Pre-registered design doc for hypothesis H059 — paired-differential test against H050 LightGBM gated baseline
type: project
hypothesis_id: H059
tier: 2c
status: designed
owner: skoir
created: 2026-04-27
citations:
  - ADR-0003-spa-vs-romanowolf
  - ADR-0004-alpha-and-power-defaults
  - ADR-0005-hmm-regime-toolkit
  - ADR-0006-scope-extension-hmm-0dte
  - ADR-0008-spa-omega-method
  - Bai et al. 2025 (arxiv 2502.13923)
  - Hu et al. 2022 (arxiv 2106.09685)
  - Hu Xiao Xu Tang Liu 2026 (arxiv 2604.12659)
  - Meyer Kaltenpoth Zalipski Müller 2025 (arxiv 2510.13654)
  - Guo Pleiss Sun Weinberger 2017 (arxiv 1706.04599)
  - Ledoit & Wolf 2008 (doi:10.1016/j.jempfin.2008.03.002)
  - Hansen 2005 (doi:10.1198/073500105000000063)
  - Lopez de Prado 2018 (ISBN 978-1-119-48208-6)
---

# H059 — Open VLM (Qwen2.5-VL-3B) LoRA fine-tuned on rendered candlestick chart with HMM regime gate

This document is the pre-registration record for hypothesis H059. Frozen at `designed`; any change requires a new hypothesis ID.

H059 is the open-VLM arm of the Tier-2c "AI chart reader" cohort registered alongside [H057](../H057/) (1D-CNN), [H058](../H058/) (TS foundation model + LoRA), and the recommended addition H060 (PatchTST trained from scratch). All four arms inherit the H050 substrate, HMM gate, walk-forward splitter, cost model, and triple-barrier labeller; the differential information is the model class. See [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) §3 for the cohort-level steelman.

## 1. Hypothesis

- H0: `T_H059 = SR(r_p_{H059, gated}) − SR(r_p_{H050, gated}) ≤ 0` on the OOS test fold, evaluated **at per-bar inference cadence** (Q-R1-2 remediation; see §3.3 and §9.1). The Qwen2.5-VL-3B LoRA chart-reader does not exceed the LightGBM-gated H050 baseline on the paired walk-forward Sharpe differential (net of cost).
- H1: `T_H059 > 0` on the OOS test fold; one-sided test at `α = 0.05` per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).
- Auxiliary null (reported but not the gate decision):
  - H0_zero: `SR(r_p_{H059, gated}) ≤ 0` — the absolute-Sharpe one-sided test.
  - **H0_uncond is dropped** under the per-bar binding (Q-R1-11 remediation): with per-bar inference, the "trigger set" is every bar, so the H059 unconditional series is the VLM signed-position at every bar regardless of HMM state, and the within-arm `gated − unconditional` differential is redundant with H050's existing Family A `T_H050` regime-lift test (which carries the same regime-lift question for the same gate). Re-deriving the H059 regime-lift question would require a separate hypothesis ID; the gate-conditioning question is fully answered by Family A.
- Primary inference: paired-differential Sharpe CI per [Ledoit & Wolf 2008, *Journal of Empirical Finance* 15(5):850–859](https://doi.org/10.1016/j.jempfin.2008.03.002) studentised time-series bootstrap with per-replicate Newey–West 1994 bandwidth, callable at [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) (`ledoit_wolf_2008_differential_ci`). H059's per-bar cadence preserves bar-by-bar pairing with the H050 baseline, satisfying LW2008's paired-sample assumption.
- Family-wide multiple testing: H059 enters **Family B** — the chart-reader cohort Hansen 2005 SPA family with `M = 5` membership `{H057, H058a, H058b, H059, H060}` per the synthesis memo §3 Q1 / §6 Family B declaration ([memo](../../../docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md)). H050 is the **baseline anchor only**, not a Family B member (Q-R1-1 + Q-R1-12 remediation: H050's frozen Family A Romano-Wolf step-down is preserved). H059 contributes exactly one Family B column (one binding LoRA configuration, one binding render config, one binding prompt template — see §5, §3, §3.4). Per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) two-tier rule, at `M ≥ 2` Family B uses `omega_method="bootstrap"` (with shared bootstrap indices across strategies for cross-dependence preservation per Hansen 2005 §2); the `omega_method="hac"` path applies only to `M = 1` isolation passes per ADR-0008 §Single-strategy degenerate handling.

### Mechanism

Qwen2.5-VL-3B is an open-weight (Apache-2.0) vision-language model with a ViT image encoder and a Qwen2.5 language decoder, trained on multi-modal corpora including web-scraped chart images and natural-language captions ([Bai et al. 2025, "Qwen2.5-VL Technical Report," arxiv 2502.13923](https://arxiv.org/abs/2502.13923)). The visual encoder produces patch embeddings that the decoder attends to during text generation; spatially separated structures in the image (gap up-day relative to wick of two bars ago; an outside-bar engulfing pattern; a flag-and-pole consolidation) are encoded as 2D positional information that no 1D OHLCV vector or 1D channel-tensor surfaces directly. This 2D differential information is the H059 alpha hypothesis vs the 1D LightGBM (H050), 1D-CNN (H057), and tokenised-stream (H058) classes. LoRA ([Hu et al. 2022, "LoRA: Low-Rank Adaptation of Large Language Models," ICLR 2022, arxiv 2106.09685](https://arxiv.org/abs/2106.09685)) adapts the attention projections to the rendered-chart-and-triple-barrier-label distribution while keeping the backbone frozen, preserving the visual prior.

### Differential information vs siblings

- vs H050 LightGBM: H050 ingests four scalar microstructure features per bar (Parkinson RV, realized variance, realized skew, OFI tick-rule). H059 ingests the rendered 60-bar OHLC chart as a 2D image — the spatial relationships between bars (gaps, wicks crossing prior bodies, multi-bar pattern formations) are first-class inputs. The H059 alpha hypothesis is that 2D pattern recognition by a pretrained visual prior captures non-linear cross-bar interactions that scalar feature engineering collapses.
- vs H057 1D-CNN: H057 ingests a 60×5 OHLCV tensor; convolutional kernels capture translation-invariant local patterns along the time axis but not 2D layout. H059 lets the visual encoder operate on the rendered geometry directly, including the *visual* relationship between the high–low range and the body — a relationship that is dimensionally collapsed in the 1D-channel encoding.
- vs H058 TSFM: H058 ingests a tokenised return stream into a TS-pretrained transformer; pretraining contamination is at the *target time series* level (Lag-Llama / MOMENT / Moirai corpora include exchange-rate / FRED-MD / "economics" series — survey §8). H059's contamination is qualitatively different (visual prior contamination — see below) and lower-severity at the label-leakage level.

### Known visual-prior contamination

VLM pretraining corpora contain technical-analysis folklore — annotated chart screenshots from finance blogs, textbook illustrations of "hammer = bullish," "doji = indecision," "head and shoulders = reversal" — that biases the visual prior toward retail-trader literature rather than the actual statistical structure of ES/NQ futures. This is **not** look-ahead leakage in the strict ReproLog sense (no future ES/NQ price data leaks into training), but it shapes interpretation: the model's "intuition" is contaminated by the same retail-trader literature the H050 universe exists to outperform. The LoRA fine-tune patches this only to the extent that the (chart, triple-barrier-label) supervision overrides the prior; with rank=16, α=32, 3 epochs (binding per §5) the prior is unlikely to be overwritten.

### Published prior — Hu, Xiao, Xu, Tang, Liu 2026 verbatim (verified WebFetch 2026-04-27)

[Hu, Xiao, Xu, Tang, Liu 2026, "Do VLMs Truly 'Read' Candlesticks? A Multi-Scale Benchmark for Visual Stock Price Forecasting," arxiv 2604.12659](https://arxiv.org/abs/2604.12659) is the only published benchmark of VLM candlestick understanding. Abstract verbatim (verified by WebFetch 2026-04-27): "most VLMs perform well only under persistent uptrend or downtrend conditions, while exhibiting weak predictive capability in more common market scenarios" + "significant prediction biases and limited sensitivity to explicitly specified forecast horizons in prompts, indicating inherent limitations in precise temporal reasoning."

H059 tests the **LoRA-fine-tuned** variant which Hu, Xiao, Xu, Tang, Liu 2026 do **not** study. The published prior is bearish on zero-shot VLM candlestick reading; the LoRA-fine-tune route is a genuinely under-explored regime. The H059 H0 reflects the bearish prior — it requires positive paired evidence (LW2008 CI excludes zero, gated by the auxiliary HMM-helps null) before promotion.

## 2. Universe and sample period

Identical to H050 §2 (substrate sharing is the entire point of the cohort design). Reproduced for self-containment:

- Instruments: ES and NQ front-month per [config/instruments.yaml](../../../config/instruments.yaml); roll-handling per the calendar in that file.
- Frequency: 1-minute bars as the base grid; rendered-chart cadence selected per §3.4 below. HMM observation cadence inherited from H050 (BIC over `{1m, 5m, 15m}` inside the train fold).
- Session: RTH only.
- Train window: 2015-01-01 through 2022-12-31 (calendar bounds; walk-forward splits applied within).
- Validation window: 2023-01-01 through 2023-12-31, embedded as inner folds of walk-forward.
- Test window: 2024-01-01 through 2025-12-31, strictly held out until final SPA submission.
- Roll-handling: front-month, AFML §2.4.3 ratio-adjusted via [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) v0.3.0 (commit `329fd1b` decade-wraparound disambiguation), output combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` per [H050 data_requirements.md §Combined frame](../H050/data_requirements.md).
- Substrate-edge truncation: the test window's right edge is short by 28 days (ES) and 12 days (NQ) per H050 data_requirements.md; the truncation applies symmetrically to all cohort arms and is tracked under follow-up `P1-DATABENTO-RIGHT-EDGE-EXTENSION`.

H059 reads the **same** roll-adjusted substrate and partitions; no separate ingest. See [data_requirements.md](data_requirements.md) for the binding checksums.

## 3. Inputs — rendered chart, prompt, output parsing

The H059 input is a triple `(rendered_chart_image, prompt_string, optional_text_context)`. The render config and prompt are pre-registration commitments; both are frozen at `status=designed` and either changing requires a successor hypothesis ID.

### 3.1 Render config (binding)

Per the lead-researcher brief and the published-render-config check below, H059 adopts the following render config. **One config; no sweep.** All values pre-registered.

| Field | Value |
|---|---|
| Lookback bars | 60 |
| Bar grid | 1-minute base; rendered window = trailing 60 minutes of RTH bars |
| Aspect ratio | 4:3 (image width:height) |
| Image resolution | 800 × 600 px (deterministic; chosen to fit Qwen2.5-VL-3B's native vision-encoder input grid without rescaling artefacts; documented at [src/skie_ninja/models/vlm/render.py](../../../src/skie_ninja/models/vlm/render.py) at scaffold time) |
| Bar style | OHLC bars (open tick on left, close tick on right, vertical line between high and low). **Not** filled candle bodies. |
| Body-color confound | Eliminated by construction — OHLC bars carry no body color. All bars are rendered single-color (black on white background). |
| Indicator overlays | None. No moving averages, no Bollinger bands, no RSI, no volume sub-panel. |
| y-axis scale | Logarithmic |
| y-axis range | Fixed per fold from training-fold percentiles only — `[p_{1, train_fold}, p_{99, train_fold}]` of the training-fold close-price empirical CDF, expanded by 5% on each side. The range is **frozen at fold-fit time** and applied identically to every chart in that fold's train and test partitions. **Auto-scale is forbidden.** This eliminates the major leak channel where per-image auto-scaling encodes the realised volatility of the future window into the y-axis tick spacing visible to the model. |
| x-axis scale | Linear, bar-index (0 to 59 left to right) |
| x-axis labels | Hidden — no timestamp text rendered on the x-axis |
| Header / title | None. **No symbol name, no timeframe label, no cutoff date** rendered on the image. The orchestrator passes the symbol via the text prompt; the cutoff date is never rendered (PIT discipline — see §3.5). |
| Background | White (`#FFFFFF`); gridlines off |
| Anti-aliasing | Off (deterministic pixel rendering across runs) |
| Renderer | `matplotlib.pyplot` with the `Agg` backend, version pinned in `uv.lock`; SHA256 of the render config dict (canonical JSON serialization) hashed into `model_hash` per §11 |

### 3.2 Why not the Hu, Xiao, Xu, Tang, Liu 2026 render config

The lead-researcher brief instructed: "Before adopting these defaults, WebFetch [Hu, Xiao, Xu, Tang, Liu 2026] and check whether they document a render config in their benchmark. If they do, prefer their render config for direct comparability with the published prior."

WebFetch result (2026-04-27, full HTML version at `https://arxiv.org/html/2604.12659`) — the Hu, Xiao, Xu, Tang, Liu 2026 render config is:

| Field | Hu, Xiao, Xu, Tang, Liu 2026 | Lead-researcher default | Decision |
|---|---|---|---|
| Lookback bars | 50 (max; recent-window cap) | 60 | Lead default — closer to H050's 60-min Yang-Zhang lookback rule, preserves cross-arm comparability |
| Bar style | Filled candle bodies (GREEN=up, RED=down) | OHLC bars, monochrome | **Lead default — body-color confound is disqualifying.** A green/red body color is a deterministic function of `sign(close − open)` for the window-closing bar, which is the very quantity the model must predict for that bar at decision time. The model could in principle learn `last_body_color → label` and bypass the spatial reasoning the hypothesis is designed to test. |
| Indicator overlays | MA5 (black), MA20 (blue), MA90 (purple); separate lower-panel volume | None | Lead default — overlays add visual content the H050 LightGBM does not see, inflating differential information beyond the pure 2D-pattern hypothesis under test. The MA90 overlay also requires 90 prior closes that the 60-bar window does not contain, introducing a feature-ingest path orthogonal to the rendered chart. |
| y-axis scale | Linear (no log mentioned) | Logarithmic | Lead default — log-scale is the conventional choice for percent-return analysis on price series ([Hudson & Gregoriou 2015, *Int. Rev. Fin. Anal.* 38:151–162](https://doi.org/10.1016/j.irfa.2014.10.008)) and matches the H050 return-convention addendum's log-return basis. |
| y-axis range | Per-image auto-scale (implicit; not stated) | Fixed per fold from training-fold percentiles only | **Lead default — fixed-range is non-negotiable for PIT.** Auto-scale leaks future-window realised range into the visible tick spacing, a side channel the canary in §3.6 directly catches. |
| Header / title | "stock symbol, time frame, and cutoff date" | None | **Lead default — the cutoff-date header is a direct PIT side channel.** The model can in principle learn `date → regime` mappings (e.g., "March 2020 = covid"), bypassing the chart content entirely. This single difference is disqualifying for evidence-bar PIT discipline regardless of the other config choices. |

**Decision: adopt the lead-researcher defaults; do not adopt the Hu, Xiao, Xu, Tang, Liu 2026 render config.** The Hu et al. config is incompatible with strict PIT discipline (cutoff-date header) and adds confounds (body color, indicator overlays) orthogonal to the H059 hypothesis. Direct numerical comparability with Hu, Xiao, Xu, Tang, Liu 2026 is sacrificed; the Hu et al. result is cited qualitatively in §1 as the bearish prior on the zero-shot variant, not as a benchmark to beat numerically.

### 3.3 Trigger cadence (Q-R1-2 remediation: per-bar)

- Decision frequency: **per-bar inference** at the 1-minute decision cadence, identical to H050 + H057 + H058 + H060. The VLM is invoked at every RTH bar; the HMM gate is applied as a post-inference filter on the signed position rather than as a trigger condition. This binding is the Q-R1-2 remediation per synthesis memo §3 Q6 — paired LW2008 alignment with the Family B cohort and Hansen 2005 shared-bootstrap-index dependence preservation both require uniform per-bar cadence across all Family B entries; mixing event-time (HMM-transition) cadence with per-bar cadence in a single Family B Hansen SPA composite null would break paired-bar pairing and force fold-resampled bootstrap indices, which violates the Hansen 2005 §2 cross-dependence-preservation contract.
- Effective sample size at per-bar cadence: ~390 RTH bars/session × 2 symbols × ~252 sessions/year × 8 years ≈ 1.6 × 10⁶ decisions over the train window per arm, well above the LW2008 finite-sample floor.
- **Pilot wall-clock gate (load-bearing)**: Qwen2.5-VL-3B + LoRA at per-bar cadence is computationally aggressive on a single A100 80GB. Per §9.1, the empirical per-fold wall-clock at per-bar cadence is the binding feasibility gate. **Decision rule**: a fold-0 pilot run measures the empirical wall-clock at per-bar cadence on the production GPU; if measured wall-clock > 7 days/fold, H059 is archived `null, infeasible` per §10 and the successor hypothesis `H059b` (HMM-state-transition cadence) is registered as a separate-family hypothesis (out of scope for the 2026-04-27 chart-reader pre-reg package). Tracked under `P1-H059-WALL-CLOCK-PILOT-MEASUREMENT` (synthesis memo §5 canonical follow-up name) and `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`.
- Sensitivity to the trigger rule is **not** swept. The trigger rule is part of the model definition and pre-registered here; sweeping it would inflate the Family B SPA column count and rebreak the `M=5` per-arm commitment.

### 3.4 Prompts (binding)

Two prompt templates, both pre-registered verbatim. The zero-shot prompt is used at fold 0 only as a smoke-test for the unfine-tuned backbone (its output is logged but does not enter the gate decision). The fine-tune-target prompt is used for both LoRA training and inference; it is the only prompt that drives the production decision stream.

#### Zero-shot prompt (P_zs) — for fold-0 smoke-test only

```
You are looking at a 60-bar trailing OHLC chart of a CME equity-index futures contract.
The y-axis is logarithmic; the y-axis range is fixed and shows price levels.
The x-axis shows bar index (0 = oldest, 59 = newest); no timestamps are shown.

Predict whether the price is more likely to:
(A) reach a +1.5σ upper barrier before reaching a -1.5σ lower barrier within the next 60 bars,
(B) reach the -1.5σ lower barrier before reaching the +1.5σ upper barrier within the next 60 bars,
(C) reach neither barrier within the next 60 bars (vertical-barrier outcome).

Reply with exactly one character: A, B, or C. Do not explain your reasoning.
```

#### Fine-tune-target prompt (P_ft) — used for LoRA training and production inference

```
Chart: 60-bar trailing OHLC of {symbol}, log y-axis, fixed range.
Predict triple-barrier outcome (upper / lower / vertical) within next 60 bars.
Answer: A | B | C.
```

`{symbol}` is substituted at inference time with `ES` or `NQ`. The substitution is the only prompt-time variable; no other prompt fields vary across decisions. **No prompt sweep.** The two templates are the entire H059 prompt search space and are frozen at pre-reg.

### 3.5 Output parsing — constrained decoding

The VLM text output is parsed into `{up, down, vertical}` via grammar-constrained sampling: the decoder is constrained to emit exactly one token from the regex `^[ABC]$`. Implementation: Hugging Face `transformers` `LogitsProcessor` restricting sampling to the token IDs of `A`, `B`, `C` per the Qwen2.5-VL-3B tokenizer.

- `A` → up (long signal)
- `B` → down (short signal)
- `C` → vertical (no-trade)
- Any non-conforming output (parse failure) → vertical (conservative default — equivalent to "no trade").

Implementation will assert at scaffold time that the constrained-decoding path cannot emit a non-`A`/`B`/`C` token; the parse-failure branch is defensive and expected to be unreachable at runtime. The branch existence is required because the constrained-decoding library is upstream code; assertion-only is insufficient under defense-in-depth.

### 3.6 PIT canaries (load-bearing for H059)

Three canaries at [tests/unit/test_h055_render_pit.py](../../../tests/unit/test_h055_render_pit.py) (scaffold to be added at `status=running` transition):

1. **Cross-fold structural-difference canary (primary, Q-R1-13 remediation).** Render the same 60-bar window of bar-data values in two **different** folds (a train fold and a test fold; the bar values are bit-identical because we explicitly resupply the same OHLC tuples to the renderer, isolating the fold-dependent axis-range effect). Assert that any pixel differences are confined structurally to the y-axis tick-spacing band (the right-edge axis-label gutter, if any) — not to the bar positions themselves. The substantive assertion: bar-position pixels are bit-identical across folds, and pixel differences are restricted to the axis-tick-spacing region whose width depends on the per-fold `(ymin, ymax)` range. The earlier formulation (pixel-identity across two timestamps) was mis-specified because with no axis labels and no header, the test trivially passed regardless of whether the y-axis range was leaking — the structural variant catches the auto-scale-leakage failure mode that pixel-identity could not detect. Implementation: encode bars from the same window into two synthetic frames at two different fold IDs, render with the fold-specific `(ymin, ymax)` cache, diff the PNG bytes by region.

   **Deterministic-renderer canary (secondary).** Render the same 60-bar window in the SAME fold at two different decision timestamps. Assert pixel-identity. With no axis labels / no header / fixed-range axis, this is a deterministic-rendering smoke test (not a leakage test); it catches non-deterministic matplotlib rendering paths.
2. **Axis-range provenance canary.** Render a single chart from a test-fold window. Assert that the y-axis `(ymin, ymax)` was derived from the training-fold percentile cache for the matching fold ID — by checking that the orchestrator's `_axis_range_cache[fold_id]` was populated **before** any test-fold bar entered the renderer, and that the test-fold renderer reads from the cache rather than computing its own range. Catches auto-scale leakage at the axis-range path.
3. **Future-bar invariance canary.** Render the same 60-bar window twice: once with the actual data, once with the bar at index 60 (the would-be-future bar) perturbed by ±5σ. Assert pixel-identity of the rendered images — the future bar must be invisible to the renderer because the window is `[t-59, t]` inclusive. Catches off-by-one window-slicing bugs.

All three canaries are evidence-bar gates; the orchestrator refuses to enter the production walk-forward unless all three pass on the substrate.

## 4. Label construction

Identical to H050 §4 (cohort-shared labeller). Triple-barrier per [Lopez de Prado 2018, *Advances in Financial Machine Learning*, Wiley ISBN 978-1-119-48208-6, §3.2](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086).

- `pt_sl`: symmetric around volatility, multiplier ∈ `{1.0, 1.5, 2.0}` selected by walk-forward CV on the train fold (inherited from H050).
- `vertical_barrier` ∈ `{30m, 60m, 120m}`, selected by same CV.
- `volatility_estimator`: Yang–Zhang with lookback ∈ `{20, 60, 120}` minutes, selected by CV.
- The 27-cell label grid matches H050 exactly. The H059 inner-CV selects within the same grid; selection metric (Q-R1-15 remediation): **restricted-3-token log-loss at decode time, computed after the constrained-decoding `LogitsProcessor` mask is applied (§3.5), with temperature-scaled softmax per [Guo, Pleiss, Sun, Weinberger 2017, ICML, arxiv 1706.04599](https://arxiv.org/abs/1706.04599) (single scalar temperature `T` per fold-symbol, fit on a held-out training-fold calibration slice).** The metric is computed only over the masked `{A_token_id, B_token_id, C_token_id}` token logits, normalised to a 3-class probability simplex; full-vocabulary log-loss is **not** the metric (the constrained-decoding mask makes full-vocab loss incommensurable across folds).

The H059 cohort-arm reuses H050's label cache where possible. If the cache contract between H050 and H059 differs at the `(symbol, fold_id, label_horizon)` level, H059 recomputes labels from raw bars (idempotent — labels are a deterministic function of the substrate). Cache contract verified at scaffold time.

## 5. Estimator — Qwen2.5-VL-3B + LoRA (binding, no sweep)

Single configuration; no hyperparameter search. SPA family entry contributes exactly 1 column.

### 5.1 Backbone

- Model: **Qwen2.5-VL-3B-Instruct** ([Bai et al. 2025, arxiv 2502.13923](https://arxiv.org/abs/2502.13923)).
- License: **Apache-2.0** (verified via the survey memo §2.5 cross-reference to the [QwenLM/Qwen2.5-VL repo LICENSE](https://github.com/QwenLM/Qwen2.5-VL); the 3B variant is in the Apache-2.0 tier, distinct from the 72B variant which uses the Qwen License).
- Why 3B (not 7B): per the lead-researcher binding and the §9.1 wall-clock estimate, 7B + LoRA at the H050-equivalent decision frequency exceeds the 7-day-per-fold compute budget on a single A100 80GB. 3B is the smallest viable open-weight VLM backbone consistent with the cohort SPA family budget. Documented as a binding compute-feasibility choice in survey §10 Q6.
- Weights source: Hugging Face `Qwen/Qwen2.5-VL-3B-Instruct` at the revision pinned at `status=running` transition; SHA256 of the model `state_dict` hashed into `model_hash` per §11.

### 5.2 Adapter — LoRA (Q-R1-4 remediation: explicit per-value sourcing)

Per [Hu et al. 2022, ICLR 2022, arxiv 2106.09685](https://arxiv.org/abs/2106.09685), implemented via Hugging Face `peft`. None of the per-value bindings below are derived from primary literature on **intraday futures direction**; the primary-literature anchors are on the underlying LoRA paper (rank/α scaling, target modules) and the PEFT canonical defaults. The selection-bias note matches the H057 §5.1 / H060 §4.4 treatment of pre-frozen hyperparameter values: empirical re-calibration on the project substrate is filed under follow-up `P1-H059-LORA-CONFIG-EMPIRICAL`.

| Field | Value | Rationale and considered-and-rejected alternatives |
|---|---|---|
| `r` (rank) | **16** | Anchor: [Hu et al. 2022 §4.1 (Low-Rank-Parametrized Update Matrices)](https://arxiv.org/abs/2106.09685) discusses the α/r scaling factor; the paper does not prescribe α/r=2 as a default. Project convention: α/r=2 chosen as a stable scaling anchored to common community practice; see project follow-up P1-H059-LORA-CONFIG-EMPIRICAL for empirical calibration on the H050 substrate. Considered-and-rejected: r = 4 (smaller adapter, may underfit the cross-modal chart→{A,B,C} mapping); r = 32 (closer to full-MLP capacity, eliminates the parameter-budget motivation for LoRA). Single binding to avoid Family B SPA column inflation. |
| `lora_alpha` (α) | **32** | Anchor: [Hu et al. 2022 §4.1 (Low-Rank-Parametrized Update Matrices)](https://arxiv.org/abs/2106.09685) discusses the α/r scaling factor; the paper does not prescribe α/r=2 as a default. Project convention: α/r=2 chosen as a stable scaling anchored to common community practice; see project follow-up P1-H059-LORA-CONFIG-EMPIRICAL for empirical calibration on the H050 substrate. Pinned to r = 16 by the α/r ratio. |
| `target_modules` | **`{q_proj, k_proj, v_proj, o_proj}`** (attention projections only) | Anchor: [Hu et al. 2022 §7.1 "Which Weight Matrices to Apply LoRA To"](https://arxiv.org/abs/2106.09685) empirically studies attention-only weight matrices; among those, adapting Wq + Wv jointly is empirically superior to single-matrix adaptation at fixed parameter budget. Hu et al. did not evaluate full-MLP LoRA, so the "Pareto-optimal vs full-MLP" framing is not supported; the project anchors on attention-only LoRA per their attention-only protocol with empirical follow-up under P1-H059-LORA-CONFIG-EMPIRICAL. Considered-and-rejected: attention-only `{q_proj, v_proj}` (Hu et al. 2022 baseline; under-parameterised for cross-modal adaptation); attention + MLP `{q_proj, v_proj, gate_proj, up_proj, down_proj}` (HF `peft` Qwen2.5 default for full coverage; doubles trainable parameters and VRAM cost without primary-literature support for the regime). |
| `lora_dropout` | 0.05 | Project convention; HuggingFace PEFT LoraConfig source default is 0.0 and example notebooks use 0.01 or 0.1, so 0.05 is not a "canonical" PEFT default. Anchored as project convention with empirical-calibration follow-up P1-H059-LORA-CONFIG-EMPIRICAL. |
| `bias` | `"none"` | [Hu et al. 2022 §3.2 default](https://arxiv.org/abs/2106.09685). |
| Learning rate | **1e-4** | PEFT canonical default for LoRA fine-tuning per [HuggingFace PEFT docs](https://huggingface.co/docs/peft) generic guidance. **Selection-bias note**: 1e-4 is the literature-default, not an empirically-optimized value for intraday futures direction; the post-cycle empirical-calibration follow-up `P1-H059-LORA-CONFIG-EMPIRICAL` will sweep `{1e-5, 5e-5, 1e-4, 3e-4}` on a successor hypothesis ID. Considered-and-rejected at pre-reg: 1e-3 (too aggressive for LoRA stability per the Hu et al. 2022 supplementary discussion on AdamW + LoRA), 1e-5 (too slow given the 3-epoch budget). |
| Optimizer | AdamW, β=(0.9, 0.999), weight_decay=0.0 | PEFT canonical default. |
| Epochs | **3** | Lead-researcher binding aligned with the survey's wall-clock-feasibility target. PEFT canonical training-recipe range is 1–10 epochs; 3 is the centre of the range and matches H058 §5.4 cohort-shared epoch budget. |
| Batch size | 16 (effective; gradient-accumulation as needed for GPU memory) | Implementation choice; not part of model definition. |
| Schedule | Linear warmup over 100 steps, then constant | PEFT canonical default. |
| Mixed precision | bf16 | A100 80GB native; deterministic with `torch.use_deterministic_algorithms(True)`. |
| Seed | 20260427 | See §11. |

**60-bar window rationale**. The 60-bar lookback in §3.1 inherits the H050 §4 60-minute Yang-Zhang vol-estimator lookback as the cross-arm anchor (cohort-shared lookback preserves cross-arm comparability; the 60-bar window is also the canonical 1 RTH hour). Considered-and-rejected: 30-bar (too short to reveal multi-bar pattern formations the H059 alpha hypothesis depends on); 120-bar (doubles VRAM activation cost and exceeds the H050 anchor without primary-literature support).

**No sweep.** Rank, α, target modules, learning rate, and epochs are all single values pre-registered here. This is the entire H059 hyperparameter commitment and contributes exactly 1 entry to Family B for this hypothesis. Empirical recalibration is the post-cycle follow-up `P1-H059-LORA-CONFIG-EMPIRICAL` (would require a successor hypothesis ID).

### 5.3 Head

The Qwen2.5-VL-3B output head is the language modelling head; the constrained-decoding parser (§3.5) reads the logit distribution over `{A, B, C}` token IDs and emits the argmax (greedy decoding). No new classification head is added; no softmax temperature tuning. The LoRA-adapted attention projections are the only trainable parameters (~6M parameters at rank 16, vs ~3B backbone parameters frozen — a ~0.2% trainable-parameter ratio).

### 5.4 HMM regime gate

Identical to H050 §5. Reused via the existing `select_gaussian_hmm` cache at [src/skie_ninja/models/regime/](../../../src/skie_ninja/models/regime/) and the cross-cfg amortization from commit `1c85f5f`. H059 inherits:

- Gaussian emissions; `covariance_type ∈ {diag, full}` with runtime model-class deduplication in `select_gaussian_hmm` per H050 `P1-HMM-FULL-COV-1DIM-REDUNDANT` closure semantics (the pre-reg grid is preserved; the runtime dedup eliminates the redundant `full` cell only when the emission dimension `d = 1` makes `full` and `diag` mathematically equivalent — the dedup is automatic and uniform across all chart-reader cohort arms).
- `n_states` grid per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) adaptive rule; selection by BIC + CV log-likelihood.
- Canonical state ordering: states sorted ascending by emission-mean of the primary directional feature (ES log-return); gate state `s*` = highest-mean state.
- Causal forward-filter inference at decision time; warm-start across fold boundaries per [ADR-0005 §Fold-boundary state continuity](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md).

The H059 inference cadence (§3.3) is per-bar (Q-R1-2 remediation); the gate state membership is applied as a post-inference filter on the VLM signed-position stream — every bar's VLM output is computed; the gate suppresses signed positions outside the canonical gate-state regime.

### 5.5 Output return series (Q-R1-2 cascade: per-bar binding)

For each fold, H059 produces the per-bar gated return series `r_p_{H059, gated}` and the per-bar unconditional return series `r_p_{H059, unconditional}` (the unconditional series ignores the HMM gate but uses the same VLM model on the same per-bar input set; it is recorded for diagnostic purposes only — it is **not** the basis of an auxiliary null per the H0_uncond drop in §1). The H059 primary differential is `r_p_{H059, gated} − r_p_{H050, gated}`, aligned **bar-by-bar at the per-bar cadence shared between H059 and H050** — alignment is direct (no intersection-set construction is required because both series have the same per-bar timestamp grid). This is the Q-R1-2 cascade: the prior intersection-set construction was an artefact of the rejected HMM-transition cadence; per-bar binding eliminates it.

Aggregation across symbols per the H050 [aggregation_rule_addendum_2026-04-24.md](../H050/aggregation_rule_addendum_2026-04-24.md): equal-weight pooling at the per-fold-per-symbol Sharpe ratio, with the addendum's §3.3a return-convention conversion (arithmetic ↔ log) applied identically to both strategies before the differential is taken. No sweep on the aggregation rule.

## 6. Splitter

Identical to H050 §6. `PurgedWalkForwardSplitter` per plan §4.1; `embargo` = max of residual-PACF lag and Politis–White 2004 optimal block length on stacked residuals; `purge` = `max(vertical_barrier)` across CV-selected folds. CPCV not used.

## 7. Cost model

Identical to H050 §7. `cost_model_id = nt8_es_nq_rth_v1` at [src/skie_ninja/backtest/costs/](../../../src/skie_ninja/backtest/costs/). H059 incurs the same per-contract commission (CME-cited fees from [config/instruments.yaml](../../../config/instruments.yaml)) and the same regime-conditional slippage prior. Under the per-bar binding (§3.3 Q-R1-2 remediation), H059's per-bar trade-frequency profile is identical to H050's; the cost drag per bar matches H050 exactly, and no cost-model adjustment is applied in the differential.

## 8. Gate thresholds

Defaults from [config/gate.yaml](../../../config/gate.yaml) per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).

- `alpha`: 0.05 (one-sided).
- `bh_threshold`: 0.10.
- `dsr_activation_size`: project default.
- Power target: 0.80.

H059 enters **Family B** — the chart-reader cohort Hansen 2005 SPA family with `M = 5` membership `{H057, H058a, H058b, H059, H060}` per the synthesis memo §3 Q1 / §6 Family B declaration ([memo](../../../docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md)). H050 is the **baseline anchor only**, not a Family B member (Q-R1-1 + Q-R1-12 remediation). At Family B assembly (after H057 / H058a / H058b / H060 reach `evaluated`), the multi-strategy SPA uses `omega_method="bootstrap"` per the [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) two-tier rule (`M ≥ 2` invokes bootstrap omega with shared bootstrap indices across strategies); pending sibling completion, an isolated H059-only `M=1` pass-through uses `omega_method="hac"` per ADR-0008 §Single-strategy degenerate handling and the `SingleStrategySPAWarning` is expected.

## 9. Compute budget

### 9.1 Wall-clock per-fold estimate (per-bar binding, Q-R1-2 cascade)

Assumptions (anchored on Qwen2.5-VL-3B-Instruct + Hugging Face `peft` LoRA + A100 80GB SXM4):

- Forward-pass latency at 800×600 image + ~50-token prompt + 1 generated token: ~80–150 ms / inference at bf16 on A100 (rough order-of-magnitude estimate from public Qwen2.5-VL-3B benchmark posts; not measured in-project at pre-reg time — see §10 open question 1).
- Training step (LoRA, batch 16, image+text): ~400–800 ms / step; 3 epochs at (assumed) 50k training samples per fold = ~10k steps = ~70–130 minutes per fold for training.
- Inference at **per-bar cadence (binding, Q-R1-2 remediation)**: O(10⁵–10⁶) per-bar decisions per fold × ~120 ms ≈ ~5–35 hours per fold for inference alone, plus the ~1–2 hours per fold for LoRA training. Per the survey memo §10 Q6 Q-R1-2 remediation analysis, this is the load-bearing wall-clock estimate at per-bar cadence on a single A100 80GB.
- Per-fold total at per-bar cadence: **~6–37 hours per fold**, with substantial uncertainty in the per-inference latency multiplier (the GPU memory residency of the LoRA-adapted state and KV-cache hit pattern dominates).
- **7-day-per-fold ceiling**: a fold that exceeds 7 × 24 = 168 hours of GPU wall-clock under the binding per-bar cadence triggers `archive(null, infeasible)` per §10 and registers successor `H059b` (HMM-state-transition cadence, separate-family hypothesis ID, out of scope for the 2026-04-27 chart-reader pre-reg package) per `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`.

The estimate is an order-of-magnitude pre-reg commitment; an empirical measurement at scaffold time may shift the figure by 2–3×. The pilot wall-clock measurement on fold 0 (per §9.3 and `P1-H059-WALL-CLOCK-PILOT-MEASUREMENT`) is the binding feasibility gate; if the empirical figure on fold 0 indicates that 8 folds would exceed the 7-day-per-fold ceiling, the disposition flips to `null, infeasible` immediately, before any test-fold inference is run.

### 9.2 GPU memory

Qwen2.5-VL-3B in bf16 = ~6 GB; LoRA optimizer state at rank 16 = ~50 MB; activation memory at batch 16 + 800×600 input + 50-token sequence ≈ 30–40 GB; total ≈ ~40 GB peak. Fits comfortably in A100 80GB; would be tight on A100 40GB.

### 9.3 Compute commitment (per-bar binding)

H059 will not enter `running` until a single-fold pilot run **at per-bar cadence** completes within wall-clock estimate ±2× on the production GPU. The pilot runs on fold 0 only; pilot results are logged but **do not inform** the production hyperparameters (which are pre-frozen in §5). If the pilot's measured per-fold wall-clock at per-bar cadence projects to > 7 days/fold across the full walk-forward fold count, the disposition flips to `archive(null, infeasible)` per §10 and successor `H059b` is registered. Tracked under `P1-H059-WALL-CLOCK-PILOT-MEASUREMENT` (synthesis memo §5 canonical name) and `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`.

## 10. Stopping rule

Per H050 §9, with H059-specific extensions and the cross-cutting Family B per-arm power binding (synthesis memo §3 Q-R1-8 remediation, follow-up `P1-CHARTREADER-PER-ARM-POWER-CALC` `status=running` blocker):

- Stop criterion: fixed walk-forward fold count equal to **H059's own** `n_required_for_power_80` computed from the dispersion of the H059 paired-differential statistic `T_H059 = SR_{H059, gated} − SR_{H050, gated}` on a pilot training-fold sample (the H050 scalar is no longer transferable across arms because the test statistic is `T_arm`, not `T_H050`). Cohort fold count = `max(n_required_per_arm)` across the M=5 Family B cohort, ensuring paired-differential pairing is preserved.
- Max folds: bounded above by the calendar-window limit only. Wall-clock infeasibility is a binary disposition gate (§9.3 / §11 / §14) — if the fold-0 pilot projects > 7 days/fold across the cohort fold count, the disposition is archive(null, infeasible) and successor H059b is registered; soft truncation that would break Family B paired-differential pairing is not permitted.
- HMM stationarity pre-check failure per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) → `archive(null, precondition-failed)`.
- VLM training failure (NaN loss; >50% training-step gradient-norm spikes; constrained-decoding parse-failure rate >5% on validation) → `archive(null, infeasible)`.
- **Per-bar wall-clock infeasibility** (Q-R1-2 cascade): wall-clock per-fold at per-bar cadence > 7 days/fold on the production GPU at fold 0 pilot → `archive(null, infeasible)` per §9.3, with successor `H059b` (HMM-state-transition cadence, separate-family hypothesis ID) registered per `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`.
- Wall-clock per-fold > 2× pre-reg estimate at fold 0 pilot (but ≤ 7 days/fold) → recorded as a deviation but does not auto-archive; the §11 decision rule is applied with the elevated wall-clock noted in the disposition.

## 11. Decision rule

Per H050 §10, with H059-specific reading and the Q-R1-2 per-bar cascade:

- `passed=True` (LW2008 differential CI excludes zero with lower bound > 0 at α=0.05; Family B Hansen 2005 SPA p-value < α at family-wise-corrected level for the H059 column): `archive(positive)`; promote to paper-trade eligibility cohort with H050.
- `passed=False` with LW2008 CI excluding zero but Family B SPA failing on the H059 column: `archive(null, multiple-testing-corrected)`.
- `passed=False` with LW2008 CI covering zero: `archive(null)`.
- Realized folds < H059-specific `n_required_for_power_80` (per the per-arm power binding in §10): `archive(null, underpowered)`.
- HMM stationarity pre-check failure: `archive(null, precondition-failed)`.
- VLM training failure: `archive(null, infeasible)`.
- **Per-bar wall-clock > 7 days/fold at fold 0 pilot** (Q-R1-2 cascade): `archive(null, infeasible)`; register successor `H059b` (HMM-state-transition cadence, separate-family hypothesis ID, out of scope for the 2026-04-27 chart-reader pre-reg package) per `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`.

The `archive(positive)` and `archive(null, multiple-testing-corrected)` outcomes update the H059 row in [plan/hypothesis_backlog.md](../../../plan/hypothesis_backlog.md) and trigger a one-paragraph post-mortem at §Results and §Decision below. The `archive(null, infeasible)` outcome with successor-`H059b` registration triggers a separate post-mortem documenting the wall-clock measurement that triggered the escalation.

## 12. Reproducibility commitments

- git HEAD (at run): TBD at execution.
- `uv pip freeze` sha (at run): TBD at execution; expected to include `transformers`, `peft`, `torch`, `accelerate`, `pillow`, `matplotlib` with versions pinned in `uv.lock`.
- RNG seed: **20260427** (project-wide single-seed convention; sub-seeds for `torch`, `numpy`, `random`, the HMM EM restarts, the LoRA dropout mask, the LW2008 bootstrap, and the Hansen SPA bootstrap are all derived from this master seed via `numpy.random.SeedSequence`).
- Dataset checksums (frozen at pre-reg): per [data_requirements.md](data_requirements.md), inheriting the H050 substrate combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`.
- Reproducibility log path: `logs/reproducibility/{run_id}.json`.
- HMM selection trace path: `logs/reproducibility/{run_id}_hmm_selection.json` per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md).
- HMM warm-cold filter diagnostic sidecar path: `logs/reproducibility/{run_id}_warm_cold_diagnostic.json` per the H050 warm-cold-diagnostic closure (commit `ec95c09`).
- H059 sidecar path: `logs/reproducibility/{run_id}_h055_qwenvl.json`.
- Render config JSON path: `logs/reproducibility/{run_id}_h055_render_config.json`.
- Prompt template path: `logs/reproducibility/{run_id}_h055_prompts.json` (both `P_zs` and `P_ft` serialized verbatim).

### 12.1 H059 sidecar JSON schema (`h055_qwenvl_v1`)

The sidecar is written once per run at completion; SHA256 computed via `skie_ninja.utils.hashing.file_sha256` and combined with the per-fold ledger roll-up SHA256 into `ReproLog.model_hash` via `with_model_hash`. **No change to the frozen `ReproLog` dataclass** — the integration point is identical to ADR-0005 §Integration with existing infrastructure.

```json
{
  "schema_version": "h055_qwenvl_v1",
  "hypothesis_id": "H059",
  "run_id": "<uuid>",
  "git_head": "<sha>",
  "rng_seed": 20260427,

  "backbone": {
    "name": "Qwen/Qwen2.5-VL-3B-Instruct",
    "hf_revision": "<commit-sha-pinned-at-status-running>",
    "weights_sha256": "<sha256 of state_dict canonicalised under torch.save deterministic mode>",
    "license": "Apache-2.0",
    "license_file_sha256": "<sha256 of LICENSE file at hf_revision>",
    "param_count": 3000000000
  },

  "lora": {
    "library": "peft",
    "library_version": "<pinned in uv.lock>",
    "config": {
      "r": 16,
      "lora_alpha": 32,
      "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
      "lora_dropout": 0.05,
      "bias": "none"
    },
    "trainable_param_count": "<integer; expected ~6M>",
    "adapter_weights_sha256": "<sha256 of adapter_model.bin / safetensors at fold-final state, canonicalised>",
    "training": {
      "learning_rate": 1e-4,
      "epochs": 3,
      "batch_size_effective": 16,
      "optimizer": "adamw",
      "schedule": "linear_warmup_then_constant",
      "warmup_steps": 100,
      "mixed_precision": "bf16"
    }
  },

  "render_config": {
    "version": "h055_render_v1",
    "lookback_bars": 60,
    "aspect_ratio": "4:3",
    "image_resolution_px": [800, 600],
    "bar_style": "ohlc_bars_monochrome",
    "indicator_overlays": [],
    "y_axis_scale": "log",
    "y_axis_range_source": "training_fold_percentiles_p1_p99_expanded_5pct",
    "x_axis_labels": "hidden",
    "header": "none",
    "background": "#FFFFFF",
    "gridlines": false,
    "anti_aliasing": false,
    "renderer": "matplotlib_agg",
    "matplotlib_version": "<pinned in uv.lock>",
    "config_json_sha256": "<sha256 of canonical-JSON serialization of this entire render_config block>"
  },

  "tokenizer": {
    "name": "Qwen/Qwen2.5-VL-3B-Instruct tokenizer",
    "vocab_sha256": "<sha256 of tokenizer vocab + merges canonicalised>",
    "tokenizer_json_sha256": "<sha256 of tokenizer.json>"
  },

  "prompts": {
    "p_zs_template_sha256": "<sha256 of P_zs UTF-8 bytes>",
    "p_zs_template_text": "<P_zs verbatim, for transcript audit>",
    "p_ft_template_sha256": "<sha256 of P_ft UTF-8 bytes>",
    "p_ft_template_text": "<P_ft verbatim, for transcript audit>",
    "constrained_decoding": {
      "allowed_token_ids": [["A_token_id", "B_token_id", "C_token_id"]],
      "logits_processor": "AllowedTokensLogitsProcessor",
      "parse_failure_default": "C"
    }
  },

  "trigger_cadence": {
    "rule": "per_bar",
    "definition": "decision computed at every RTH bar; HMM gate applied as post-inference signed-position filter per design §5.5 (per Q-R1-2 remediation; binding cadence per synthesis memo §6 Family B uniform-cadence)",
    "decisions_per_fold_per_symbol": "<integer; populated post-run>"
  },

  "compute": {
    "gpu": "A100_80GB_SXM4",
    "gpu_count": 1,
    "blas_threading": "<per ADR-0009 BLAS pinning contract>",
    "wall_clock_per_fold_seconds": "<per-fold timer; populated post-run>"
  },

  "results_per_fold": [
    {
      "fold_id": 0,
      "n_decisions_train": 0,
      "n_decisions_test": 0,
      "n_parse_failures_test": 0,
      "ret_series_gated_path": "<parquet path>",
      "ret_series_unconditional_path": "<parquet path>",
      "ret_series_gated_sha256": "<sha256>",
      "ret_series_unconditional_sha256": "<sha256>"
    }
  ]
}
```

The `model_hash` for the run is computed per the cross-cutting binding 4 interim rule, amended R-R2-5 per synthesis memo §5 to permit per-arm pre-aggregation. H059 has three arm-specific sidecars (qwenvl + render-config + prompts); the composition first pre-aggregates them into a single arm sidecar SHA256, then composes the canonical outer 4-tuple invariant across all four chart-reader arms. Specifically: `h055_arm_sidecar_sha256 := sha256(sorted_tuple([h055_qwenvl_sidecar_sha256, h055_render_config_json_sha256, h055_prompts_json_sha256]))`, then `model_hash = sha256(sorted_tuple([h055_arm_sidecar_sha256, hmm_sidecar_sha256, warm_cold_sidecar_sha256, ledger_rollup_sha256]))`. The deterministic-sorted-tuple wrappers (inner and outer) neutralise sidecar-write-order non-determinism. Component SHAs are computed via `skie_ninja.utils.hashing.file_sha256` and combined into `ReproLog.model_hash` via `with_model_hash`. **No change to the frozen `ReproLog` dataclass.** The per-arm pre-aggregation is documented per synthesis memo §5 (R-R2-5 amendment) — the outer 4-tuple is invariant across H057/H058/H059/H060; the inner pre-aggregation is arm-specific. Implementation note: the multi-sidecar concatenation is the open follow-up `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` from the ADR-0005 warm-cold-diagnostic closure; H059 is the third hypothesis to require the multi-sidecar pattern (alongside H050 + H058) and its scaffold is a forcing function for that helper to land before `status=running`.

## 13. Results

To be populated at `evaluated`. Will include: per-fold per-bar paired return series (H059 vs H050 baseline), LW2008 differential CI, Family B Hansen 2005 SPA p-value (computed when all M=5 siblings reach `evaluated`; `omega_method=bootstrap` per ADR-0008 two-tier rule) plus an isolated H059-only `M=1` SPA pass-through (`omega_method=hac`, `SingleStrategySPAWarning` expected) for sensitivity reporting only, HMM stationarity diagnostic outcomes, parse-failure rate (expected ~0% under constrained decoding), wall-clock per-fold timer at per-bar cadence (with the 7-day-per-fold ceiling annotation), GPU-utilisation profile, and the three PIT canary pass records.

## 14. Decision

To be populated at `evaluated`. Archive label per §11 plus a one-paragraph post-mortem covering: was the published-prior bearish prior (Hu, Xiao, Xu, Tang, Liu 2026) confirmed or refuted by the LoRA-fine-tune variant; what fraction of `T_H059 > 0` (if positive) is attributable to the visual prior vs to LoRA-learned ES/NQ-specific features; what the parse-failure rate and wall-clock-per-fold figures imply for production-scale paper-trade.

If the disposition is `archive(null, infeasible)` triggered by the Q-R1-2 cascade (per-bar wall-clock > 7 days/fold at fold 0 pilot), the post-mortem additionally documents: the measured fold-0 wall-clock at per-bar cadence, the projected full-walk-forward wall-clock, the GPU memory and compute saturation profile from the pilot run, and the formal registration of successor `H059b` (HMM-state-transition cadence; separate-family hypothesis ID; out of scope for the 2026-04-27 chart-reader pre-reg package) per `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`.

## References

- [Bai et al. 2025, "Qwen2.5-VL Technical Report," arxiv 2502.13923](https://arxiv.org/abs/2502.13923)
- [Hu et al. 2022, "LoRA: Low-Rank Adaptation of Large Language Models," ICLR 2022, arxiv 2106.09685](https://arxiv.org/abs/2106.09685)
- [Hu, Xiao, Xu, Tang, Liu 2026, "Do VLMs Truly 'Read' Candlesticks? A Multi-Scale Benchmark for Visual Stock Price Forecasting," arxiv 2604.12659](https://arxiv.org/abs/2604.12659) — published prior; verified via WebFetch 2026-04-27
- [Meyer, Kaltenpoth, Zalipski, Müller 2025, "Rethinking Evaluation in the Era of Time Series Foundation Models," arxiv 2510.13654](https://arxiv.org/abs/2510.13654) — pretraining contamination context (cohort-level)
- [Ledoit & Wolf 2008, *Journal of Empirical Finance* 15(5):850–859](https://doi.org/10.1016/j.jempfin.2008.03.002) — primary inference
- [Hansen 2005, *JBES* 23(4):365-380](https://doi.org/10.1198/073500105000000063) — corroborative SPA
- [Lopez de Prado 2018, *Advances in Financial Machine Learning*, Wiley ISBN 978-1-119-48208-6](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) — labeller, splitter
- [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) — HMM regime toolkit
- [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) — SPA omega-method selection
- Survey memo: [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md)

## Open questions deferred to the audit-remediate-loop

1. Wall-clock per-fold figure (§9.1) is an order-of-magnitude pre-reg commitment based on public Qwen2.5-VL-3B benchmark posts, not in-project measurement. The pilot run at `status=running` will measure on the production GPU; if the empirical figure deviates by >2× from §9.1, the §10 escalation path triggers.
2. The H059 inference cadence (§3.3, **per-bar** binding per Q-R1-2 remediation) is the most consequential design choice beyond the lead-researcher bindings. It is required for paired LW2008 alignment with the Family B cohort and Hansen 2005 shared-bootstrap-index dependence preservation. The competing HMM-state-transition cadence is qualitatively different (event-time triggers, fewer decisions per fold, lower wall-clock cost) and is registered as successor hypothesis `H059b` (separate-family hypothesis ID, out of scope for the 2026-04-27 chart-reader pre-reg package) if H059 is `archive(null, infeasible)` on the per-bar wall-clock gate alone, per `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`.
3. The multi-sidecar `model_hash` concatenation pattern (§12.1 implementation note) is open follow-up `P1-MODEL-HASH-MULTI-SIDECAR-HELPER`; H059 is the third hypothesis to require it. Resolving the helper scaffold before `status=running` is a prerequisite, tracked in [data_requirements.md §Open follow-ups](data_requirements.md).
