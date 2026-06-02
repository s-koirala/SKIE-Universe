---
name: AI chart-reader hypothesis survey for SKIE-Universe (H057 / H058 / H059 framing)
description: Landscape of 1D-CNN, time-series foundation model, and open-VLM approaches, evaluated against the H050 commensurability and PIT bar
type: project
created: 2026-04-27
---

# AI chart-reader hypothesis survey

Input to three downstream targeted-research agents (one per surviving hypothesis arm) and ultimately to canonical hypothesis-register entries under [research/01_hypothesis_register/](../../research/01_hypothesis_register/).

## 1. Scope and method

**Question.** Is the lead-researcher trio H057 (1D-CNN on causal OHLCV tensor) / H058 (TS foundation model + LoRA) / H059 (open VLM fine-tuned on rendered charts) a defensible covering set of "AI chart reader" approaches that can enter the existing walk-forward + Hansen 2005 SPA + ReproLog pipeline at evidence-bar quality? If not, what is missing?

**Hard constraints.** Open weights only (hashable into `model_hash`); 3-class triple-barrier output commensurable with the H050 LightGBM baseline (Brier / log loss + Sharpe-CI on net-of-cost returns — same SPA family entry); strict PIT discipline; pretraining-corpus contamination explicitly assessed; no parallel pipeline.

**Method.** Web search → retrieve primary source for every load-bearing claim (arxiv abstract or HTML, GitHub README, model card). Evidence hierarchy per [~/.claude/CLAUDE.md](../../../.claude/CLAUDE.md): peer-reviewed > official documentation > standards > vetted forums. License and pretraining-corpus claims grounded in repo / model-card text retrieved this session; verbatim quotes provided in §2 / §6 where available. Where the surface page (e.g., paywalled JBES, abstract-only arxiv) did not yield the load-bearing detail, the claim is labelled "unverified at full-text level" rather than asserted.

What I did NOT do: GPU benchmarking (out of scope), live Colab reproduction of any repo (out of scope; flagged as targeted-research-agent task), exhaustive coverage of every TSFM (capped at the six canonical models named in the brief plus Timer/PatchTST as transformer-only baselines).

---

## 2. Landscape map

The "AI chart reader" design space splits on **representation × backbone**: how the bar history is presented (1D vector, 2D image, tokenised stream) and what does the inference (CNN, transformer, SSM, pretrained TS-FM, pretrained VLM).

### 2.1 1D / 2D CNN on raw or transformed OHLCV

- **Sezer & Ozbayoglu 2018, *Applied Soft Computing* 70:525–538** — "Algorithmic financial trading with deep convolutional neural networks: time series to image conversion approach". 15 technical indicators × 15-day window → 15×15 image → 2D CNN; 30 Dow Jones stocks + 9 ETFs; ~58% accuracy on Dow Jones tested vs Buy & Hold. Doi/source via [ScienceDirect S1568494618302151](https://www.sciencedirect.com/science/article/abs/pii/S1568494618302151). Code at [omerbsezer/CNN-TA](https://github.com/omerbsezer/CNN-TA).
- **Sezer, Gudelek & Ozbayoglu 2019/2020, *Applied Soft Computing* 90:106181** — "Financial time series forecasting with deep learning: a systematic literature review (2005–2019)". arxiv [1911.13288](https://arxiv.org/abs/1911.13288). Canonical survey.
- **Wang & Oates 2015, IJCAI workshop** — "Imaging time-series to improve classification and imputation". arxiv [1506.00327](https://arxiv.org/abs/1506.00327). Introduced Gramian Angular Summation/Difference Field (GASF/GADF) and Markov Transition Field (MTF) encodings; tiled CNN on 20 UCR datasets; the canonical reference for time-series-as-image.
- **Hatami, Gavet & Debayle 2018** — recurrence-plot encoding + deep CNN. arxiv [1710.00886](https://arxiv.org/abs/1710.00886).

### 2.2 Time-series foundation models (TSFMs)

All six are decoder/encoder transformer models pretrained on a multi-domain corpus and offered for zero-shot or LoRA fine-tune:

| Model | Year | Params (max) | Pretraining corpus (per model card / paper) | License | Primary cite |
|---|---|---|---|---|---|
| **Chronos** (Amazon) | 2024 | 710M (T5-large); Bolt-base 205M; Chronos-2 120M | "Large collection of publicly available datasets" + GP-synthetic; Chronos-2 incorporates GIFT-Eval pretraining corpus | Apache-2.0 | [arxiv 2403.07815](https://arxiv.org/abs/2403.07815) |
| **Moirai** (Salesforce) | 2024 | Moirai-1.0-R-large + Moirai-MoE; Moirai-2.0-R-small (Aug 2025) | LOTSA: 27 B observations, 9 domains incl. economics/finance, 105 datasets | Apache-2.0 | [arxiv 2402.02592](https://arxiv.org/abs/2402.02592), ICML 2024 Oral |
| **TimesFM** (Google) | 2023→2025 | TimesFM-1 200M, TimesFM-2.5 200M (down from 500M) | 100 B time-points: Wikipedia pageviews, Google Trends 22k series, M4, electricity, traffic, 3 M ARMA-synthetic | Apache-2.0 | [arxiv 2310.10688](https://arxiv.org/abs/2310.10688) |
| **Lag-Llama** | 2024 | Decoder-only; param count not in repo README | "All public time series in Monash repository" + additional sources; ~305 k series | Apache-2.0 | [arxiv 2310.08278](https://arxiv.org/abs/2310.08278) |
| **MOMENT** (CMU Auton Lab) | 2024 | small / base / large (exact param counts not in repo; ~125M/385M/750M per paper) | Time-series Pile: multi-domain public datasets (M4, ETT, weather, traffic, electricity, Monash, etc.) | MIT | [arxiv 2402.03885](https://arxiv.org/abs/2402.03885), ICML 2024 |
| **Timer** (THU) | 2024 | ~70M | UTSD subset of Time-series Pile-style sources | Apache-2.0 (per repo) | arxiv 2402.02368 (cited in survey [arxiv 2504.04011](https://arxiv.org/html/2504.04011v1); not directly verified this session — flag for downstream agent) |

Survey of TSFM data leakage at [arxiv 2510.13654](https://arxiv.org/abs/2510.13654) is load-bearing and discussed in §8.

### 2.3 Transformer-only TS architectures (non-foundation; train-from-scratch baselines)

- **PatchTST** ([Nie, Nguyen et al. 2023, ICLR](https://arxiv.org/abs/2211.14730)) — patch + channel-independence; SOTA on long-horizon forecasting at publication; canonical strong train-from-scratch transformer baseline. Repo [yuqinie98/PatchTST](https://github.com/yuqinie98/PatchTST).
- **iTransformer** ([Liu et al. 2024, ICLR Spotlight](https://arxiv.org/abs/2310.06625)) — variate-as-token; simple inversion of axes; reported SOTA over PatchTST on public benchmarks. Repo [thuml/iTransformer](https://github.com/thuml/iTransformer).
- **TimesNet** ([Wu et al. 2023, ICLR](https://arxiv.org/abs/2210.02186)) — reshapes 1D series into 2D tensor along multiple discovered periods; CNN inside. Repo [thuml/TimesNet](https://github.com/thuml/TimesNet).
- **Temporal Fusion Transformer** ([Lim, Arik, Loeff, Pfister 2019/2021, *Int. J. Forecasting* 37(4):1748–1764](https://arxiv.org/abs/1912.09363)) — older but widely deployed for static + known-future + observed-past covariate mixes.

### 2.4 State-space models

- **S4** ([Gu, Goel, Ré 2022, ICLR](https://arxiv.org/abs/2111.00396)) — structured SSM; HiPPO initialisation.
- **Mamba** ([Gu & Dao 2023, arxiv 2312.00752](https://arxiv.org/abs/2312.00752)) — input-selective SSM; linear inference. Apache-2.0 at [state-spaces/mamba](https://github.com/state-spaces/mamba). **Linux + CUDA only** per repo README — incompatible with the Windows-NT8 deployment target on the bare metal but acceptable for offline training/research on a Linux-WSL or remote box.
- **Mamba4Cast** ([arxiv 2410.09385](https://arxiv.org/abs/2410.09385)) — zero-shot TSFM built on Mamba.

### 2.5 Open VLMs candidate for chart fine-tune

| Model | Params | License | Primary cite |
|---|---|---|---|
| **Qwen2.5-VL** | 3B / 7B / 32B / 72B | Apache-2.0 (3/7/32B); Qwen License (72B) | [arxiv 2502.13923](https://arxiv.org/abs/2502.13923); Qwen2-VL: [arxiv 2409.12191](https://arxiv.org/abs/2409.12191) |
| **InternVL 2.5** | 1B–78B | MIT (model code); component licenses pass-through | [arxiv 2412.05271](https://arxiv.org/abs/2412.05271); InternVL: CVPR 2024 Oral |
| **LLaVA-Next / LLaVA-OneVision-1.5** | 7B / 72B | Apache-2.0 (model); pretraining data assets released | [arxiv 2509.23661](https://arxiv.org/html/2509.23661v3) |
| **PaliGemma 2** | 3B / 10B / 28B | Gemma license (use-restrictions; not OSI-approved) | [arxiv 2407.07726](https://arxiv.org/abs/2407.07726) |
| **Pix2Struct** | 282M / 1.3B | Apache-2.0 | [arxiv 2210.03347](https://arxiv.org/abs/2210.03347) |
| **Donut** | ~200M | MIT | arxiv 2111.15664 (cited in [arxiv 2210.03347](https://arxiv.org/abs/2210.03347); not verified in primary this session) |

Pix2Struct and Donut are **document/screenshot-parsing** models, not free-text VLMs — relevant if the chart-reader is framed as "parse OHLC from a rendered image", less relevant if it is framed as "predict label from chart + prompt".

### 2.6 LoRA fine-tune primitive

- **Hu et al. 2022, ICLR** — "LoRA: Low-Rank Adaptation of Large Language Models". arxiv [2106.09685](https://arxiv.org/abs/2106.09685). Reference impl [microsoft/LoRA](https://github.com/microsoft/LoRA); production via Hugging Face PEFT.

---

## 3. Evaluation of H057 / H058 / H059 as currently framed

### H057 — 1D-CNN on causal OHLC tensor (60-bar × 5-channel)

**Strengthen.** 1D-CNN is the right inductive prior for translation-invariant local patterns in OHLCV. Causal padding + masked convolution (or right-anchored window) eliminates look-ahead by construction. Triple-barrier softmax is direct. Pretraining contamination is non-existent — model is trained from scratch on the H050 substrate.

**Steelman criticism.** (a) Most published "CNN-on-OHLCV" baselines for equity-direction prediction underperform a tuned LightGBM on engineered features (the H050 baseline) by 0–3 percentage-points in F1 — the H050 benchmark is genuinely strong, not a strawman. (b) The 60-bar × 5-channel tensor is information-redundant with the H050 microstructure features (Parkinson RV, realized variance, realized skew, OFI). Differential information from H057 is the residual capacity of conv kernels to discover non-linear interactions among raw bars that the engineered features collapse — modest. (c) Hyperparameter sweep (filters per layer, kernel size, depth, dropout) is large and must be costed into the SPA family count.

**Verdict.** Survives. Highest-confidence "next" model class. Lowest contamination risk. Differential signal vs LGB likely small but measurable.

### H058 — TS foundation model + LoRA

**Strengthen.** Right model class for "regime-aware sequence prediction with broad prior". Open weights for Chronos / Moirai / TimesFM / Lag-Llama / MOMENT all confirmed Apache-2.0 or MIT this session. LoRA per [arxiv 2106.09685](https://arxiv.org/abs/2106.09685) is the canonical adapter — small parameter delta keeps `model_hash` reproducibility tractable.

**Steelman criticism.** (a) **Pretraining-corpus contamination is first-order.** TimesFM card explicitly lists Wikipedia pageviews + Google Trends (effectively zero risk for ES/NQ futures) plus M4, electricity, traffic (no overlap); but Lag-Llama explicitly trained on "all public time series in Monash repository" which contains finance subsets (fred-md, m1-monthly, m4-financial, m3-financial, exchange-rate, US births, NN5 daily); MOMENT's Time-series Pile explicitly contains ETT, exchange-rate, weather, traffic, electricity (no ES/NQ 1-min, but related macro series); Moirai LOTSA is largest at 27 B observations, 9 domains, **explicitly includes "economics" as a domain** per [arxiv 2402.02592](https://arxiv.org/abs/2402.02592). The pretraining corpus is **not certified clean of ES/NQ futures** for any of the six. (b) **Output mismatch.** All TSFMs are point-or-quantile forecasters of *future values*, not classifiers over triple-barrier outcomes. To meet the H050 commensurability constraint, the LoRA head must replace or reweight the forecasting head with a 3-class softmax — at which point you are LoRA-tuning approximately the last block + a new classification head, which is closer to "feature extractor + new head" than "fine-tune the foundation model". This is a non-trivial architectural decision that needs to be pre-registered, not handwaved. (c) **Effective sample inflation.** Each candidate backbone × LoRA rank × learning rate × adapter target-module choice expands the SPA family.

**Verdict.** Survives **with substantial scoping discipline**. Recommend narrowing to ≤ 2 backbones at pre-reg, with backbone choice justified by a non-data-snooping argument (e.g., MOMENT for its mask-MAE pretraining objective which is closest to "general embedding"; Chronos-Bolt-base for its small parameter count + Apache license + most thorough zero-shot benchmark coverage).

### H059 — Open VLM + LoRA on rendered candlestick chart

**Strengthen.** Genuine novelty vs. the LGB / 1D-CNN baselines: the model sees 2D spatial relationships (gap up-day relative to wick of two bars ago, etc.) that no 1D representation surfaces directly. Open VLM weights confirmed (Qwen2.5-VL Apache-2.0 except 72B; InternVL MIT; LLaVA-OV Apache-2.0). The render config is hashable into `model_hash` (per the user brief) — good.

**Steelman criticism.** (a) **VLMs cannot reliably read candlesticks at the precision required.** Hu, Xiao, Xu, Tang, Liu 2026, [arxiv 2604.12659](https://arxiv.org/abs/2604.12659), "Do VLMs Truly 'Read' Candlesticks?": "most VLMs perform well only under persistent uptrend or downtrend conditions, while exhibiting weak predictive capability in more common market scenarios" + "limited sensitivity to explicitly specified forecast horizons in prompts" + "inherent limitations in precise temporal reasoning". This is the canonical existing-literature steelman against H059-as-zero-shot. LoRA fine-tune on (chart, label) pairs may patch this for the specific render config and label horizon, but evidence base is thin and the failure-mode catalog deep. (b) **Render-config sensitivity is an unbounded hyperparameter family.** Lookback bars, aspect ratio, candle width, color scheme, log vs linear y-axis, indicator overlay choice, gridline thickness, anti-aliasing — every choice is a model variable and must enter the SPA family count (or be frozen at pre-reg). The user brief acknowledges this with the `model_hash` requirement; the *practical* consequence is that the pre-reg must enumerate one or two render configs, not search over them. (c) **Pretraining contamination.** Unlike TSFMs (where the contaminated data is the *target* time series), VLM pretraining generally contains chart images from finance blogs / Bloomberg screenshots / textbooks — but *labels* on those images do not include "what happened next". Contamination risk is more about learned visual priors over candle patterns ("hammer = bullish") than direct label leakage; this is qualitatively different and lower-severity than TSFM contamination. (d) **Inference cost.** A 7B-parameter VLM at 1-min-bar decision frequency is 60-times-per-RTH-hour-per-symbol = 780 inferences per RTH session per symbol. At ~50–200 ms / inference on a single A100 this is feasible; at the smallest 3B Qwen-VL on a CPU it is not. Flag as bar-frequency feasibility constraint but not a blocker at GPU.

**Verdict.** Survives but **higher risk and lower confidence than H057/H058**. Strongly recommend pre-registering with one fixed render config (chosen on out-of-sample-blind theory grounds), one backbone, one LoRA target-module choice. The published-literature prior is bearish on the zero-shot variant but the LoRA-fine-tuned variant is genuinely under-explored.

---

## 4. Additional hypothesis candidates

The lead-researcher trio covers (1D-CNN trained from scratch) × (TS-FM) × (VLM). Three candidate additions; only the first is recommended.

### H060 (recommended) — PatchTST trained from scratch on causal OHLCV with HMM gate

**Why include.** PatchTST ([arxiv 2211.14730](https://arxiv.org/abs/2211.14730)) is the canonical strong train-from-scratch transformer baseline — patch + channel-independence — and is reported to dominate every prior transformer on long-horizon TS-forecasting at ICLR 2023. Training from scratch on H050 substrate **fully sidesteps pretraining contamination** (unlike H058), while introducing the transformer inductive prior (long-range, attention-based) that 1D-CNN (H057) does not capture. Apache-2.0 reference impl. Direct, narrow, fits the H050 mold cleanly. iTransformer ([arxiv 2310.06625](https://arxiv.org/abs/2310.06625)) is a defensible substitution but PatchTST has the stronger literature trail.

**Why not redundant with H057.** Different inductive prior (attention vs convolution); empirical question whether attention captures bar-to-bar interactions the 1D-CNN misses.

### H057 (rejected) — Mamba on OHLCV with HMM gate

**Why I considered.** Linear inference, theoretically attractive at 1-min frequency, fashionable in 2024.

**Why I reject.** (i) Mamba reference impl is **Linux + CUDA only** — incompatible with the Windows-NT8 production target on bare metal (acceptable for offline training, but adds friction). (ii) Mamba's selective-state advantage is mostly for *long* sequences (>10 k tokens); H050 is at 60-bar windows, where the asymptotic argument doesn't apply and a transformer (H060) is in its comfort zone. (iii) Adds an SPA family entry without commensurate prior-art-supported gain over H060. Filed as `P3-MAMBA-CHARTREADER-DEFER` for re-evaluation if H060 passes positive and we want a second from-scratch sequence model.

### H058 (rejected) — Multi-resolution wavelet decomposition + CNN

**Why I considered.** Wavelet / Fourier decomposition is a legitimate transform with Mallat / Daubechies pedigree; multi-resolution stacking gives a CNN access to cross-scale features.

**Why I reject.** Adds a substantial featurization layer (mother wavelet, level count, downsample policy) that itself becomes a hyperparameter family before the model even runs; the no-magic-numbers rule then forces another nested CV inside the H050 walk-forward, ballooning compute. The "value over H057" is theoretical, not empirically established for intraday futures direction. **Honest read: existing trio + H060 is already a good covering set; H058 is gold-plating.**

### Honest assessment

**The original three plus H060 form a tight covering set: train-from-scratch CNN (H057), train-from-scratch transformer (H060), foundation-pretrained TS model (H058), foundation-pretrained VLM (H059).** That is the right factorisation. Resist the urge to add more.

---

## 5. Primary literature

Grouped by model family. All citations verified to exist via WebSearch / WebFetch this session unless flagged.

### TS foundation models
1. **Ansari et al. 2024** — Chronos: Learning the Language of Time Series. [arxiv 2403.07815](https://arxiv.org/abs/2403.07815). Tokenises real values into a fixed vocabulary; trains T5-family on cross-entropy. *Why it matters here:* Apache-2.0 weights at multiple sizes (8M–710M); cleanest TSFM zero-shot story for forecasting and the obvious first H058 backbone candidate.
2. **Woo, Liu et al. 2024 (ICML Oral)** — Unified Training of Universal Time Series Forecasting Transformers (Moirai). [arxiv 2402.02592](https://arxiv.org/abs/2402.02592). LOTSA pretraining (27 B obs, 9 domains incl. economics); patch-size projection per frequency. *Why it matters here:* largest open pretraining corpus; explicitly covers economics → highest contamination risk for ES/NQ.
3. **Das et al. 2024 (ICML)** — A decoder-only foundation model for time-series forecasting (TimesFM). [arxiv 2310.10688](https://arxiv.org/abs/2310.10688). 200M decoder; 100 B time-points pretraining. *Why it matters here:* corpus heavy on Wikipedia + Trends → low-contamination baseline if H058 wants a "least-tainted" anchor.
4. **Rasul, Ashok et al. 2024** — Lag-Llama: Toward Foundation Models for Probabilistic Time Series Forecasting. [arxiv 2310.08278](https://arxiv.org/abs/2310.08278). Decoder-only, lag covariates, probabilistic head. *Why it matters here:* probabilistic head naturally maps to a triple-barrier softmax with calibrated marginals.
5. **Goswami et al. 2024 (ICML)** — MOMENT: A Family of Open Time-series Foundation Models. [arxiv 2402.03885](https://arxiv.org/abs/2402.03885). Mask-and-reconstruct pretraining on the Time-series Pile. *Why it matters here:* MIT licence; only TSFM in the set whose pretraining objective is *embedding learning*, making LoRA-on-classification-head architecturally cleanest.
6. **Meyer, Kaltenpoth, Zalipski, Müller 2025** — Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges. [arxiv 2510.13654](https://arxiv.org/abs/2510.13654). *Why it matters here:* the load-bearing reference for §8.

### Transformer / SSM TS architectures
7. **Nie, Nguyen et al. 2023 (ICLR)** — A Time Series is Worth 64 Words: PatchTST. [arxiv 2211.14730](https://arxiv.org/abs/2211.14730).
8. **Liu et al. 2024 (ICLR Spotlight)** — iTransformer. [arxiv 2310.06625](https://arxiv.org/abs/2310.06625).
9. **Wu et al. 2023 (ICLR)** — TimesNet. [arxiv 2210.02186](https://arxiv.org/abs/2210.02186).
10. **Lim, Arik, Loeff, Pfister 2021** — Temporal Fusion Transformers, *Int. J. Forecasting* 37(4):1748–1764. [arxiv 1912.09363](https://arxiv.org/abs/1912.09363).
11. **Gu & Dao 2023** — Mamba: Linear-Time Sequence Modeling with Selective State Spaces. [arxiv 2312.00752](https://arxiv.org/abs/2312.00752).

### Time-series-as-image (relevant to H059 framing alternatives)
12. **Wang & Oates 2015** — Imaging Time-Series to Improve Classification and Imputation. [arxiv 1506.00327](https://arxiv.org/abs/1506.00327). GASF/GADF/MTF.
13. **Sezer & Ozbayoglu 2018** — Algorithmic financial trading with deep CNN: time series to image. *Applied Soft Computing* 70:525–538, [S1568494618302151](https://www.sciencedirect.com/science/article/abs/pii/S1568494618302151).
14. **Sezer, Gudelek, Ozbayoglu 2020** — Financial time-series forecasting with deep learning: a systematic literature review (2005–2019). [arxiv 1911.13288](https://arxiv.org/abs/1911.13288).

### Open VLMs
15. **Bai et al. 2025** — Qwen2.5-VL Technical Report. [arxiv 2502.13923](https://arxiv.org/abs/2502.13923) (existence asserted from search; full-text not fetched this session — flag for downstream agent verification).
16. **Chen et al. 2024 (CVPR Oral)** — InternVL: Scaling up Vision Foundation Models. [openaccess.thecvf.com/.../InternVL_..._CVPR_2024_paper.pdf](https://openaccess.thecvf.com/content/CVPR2024/papers/Chen_InternVL_Scaling_up_Vision_Foundation_Models_and_Aligning_for_Generic_CVPR_2024_paper.pdf).
17. **Lee, Joshi et al. 2023 (ICML)** — Pix2Struct: Screenshot Parsing as Pretraining for Visual Language Understanding. [arxiv 2210.03347](https://arxiv.org/abs/2210.03347).
18. **Hu, Xiao, Xu, Tang, Liu 2026** — Do VLMs Truly "Read" Candlesticks? A Multi-Scale Benchmark for Visual Stock Price Forecasting. [arxiv 2604.12659](https://arxiv.org/abs/2604.12659). *Why it matters here:* the only published benchmark of VLM candlestick understanding; load-bearing for H059.

### Adapter / fine-tune methodology
19. **Hu et al. 2022 (ICLR)** — LoRA: Low-Rank Adaptation of Large Language Models. [arxiv 2106.09685](https://arxiv.org/abs/2106.09685).

### Multiple-testing / backtest hygiene (already pinned project-side; included for H059/H058 SPA discipline)
20. **Bailey & López de Prado 2014** — The Deflated Sharpe Ratio. [SSRN 2460551](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551). Required for the prompt/architecture-sweep concern called out in §7.

---

## 6. Repository inventory

URLs verified live in this session via WebFetch. License attributed from the repo's stated LICENSE file or model card.

### For H057 (1D-CNN reference)
- **[omerbsezer/CNN-TA](https://github.com/omerbsezer/CNN-TA)** — Original Sezer & Ozbayoglu 2018 reference. License unspecified in README per fetch; treat as research code only. Last commit 2018-era. Contains training code + 15-indicator pipeline. **Use as: reference only.**
- **[nayash/stock_cnn_blog_pub](https://github.com/nayash/stock_cnn_blog_pub)** — Loose reproduction of CNN-TA. **Use as: reference only.**

### For H058 (TS foundation model)
- **[amazon-science/chronos-forecasting](https://github.com/amazon-science/chronos-forecasting)** — Apache-2.0; checkpoints 8M–710M (T5) plus Bolt 9M–205M plus Chronos-2 120M; production-grade with PyPI install. **Use as: starting point — yes** for H058 backbone candidate #1.
- **[SalesforceAIResearch/uni2ts](https://github.com/SalesforceAIResearch/uni2ts)** — Apache-2.0; Moirai-1.0/1.1/2.0/MoE checkpoints; production-grade; last release Aug 2025. **Use as: starting point — yes** for H058 backbone candidate #2 (after explicit contamination scan vs LOTSA economics subset).
- **[google-research/timesfm](https://github.com/google-research/timesfm)** — Apache-2.0; TimesFM-1/2/2.5; fine-tuning example added April 2026. **Use as: starting point — yes** for H058 lowest-contamination baseline.
- **[time-series-foundation-models/lag-llama](https://github.com/time-series-foundation-models/lag-llama)** — Apache-2.0; Colab fine-tune example provided; ~79 commits. **Use as: reference only** unless the probabilistic head is determined load-bearing for the calibrated triple-barrier output (in which case promote).
- **[moment-timeseries-foundation-model/moment](https://github.com/moment-timeseries-foundation-model/moment)** — MIT; small/base/large checkpoints; mask-MAE pretraining. **Use as: starting point — yes** if H058 wants a clean "feature-extractor-with-new-head" architecture; **also, the upstream `moment-research` repo is the actually-fine-tunable one** per their org structure.

### For H059 (open VLM)
- **[QwenLM/Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL)** — Apache-2.0 for 3B/7B/32B. Production-grade; Hugging Face PEFT-LoRA examples in the wild. **Use as: starting point — yes** (start with 7B; 3B for inference-cost stress test). 72B is Qwen License (research) — exclude from production.
- **[OpenGVLab/InternVL](https://github.com/OpenGVLab/InternVL)** — MIT; CVPR 2024 Oral; checkpoints across InternVL2 / 2.5 sizes. **Use as: starting point — yes** as alternative backbone.
- **[google-research/big_vision](https://github.com/google-research/big_vision/blob/main/big_vision/configs/proj/paligemma/README.md)** (PaliGemma) — Gemma license imposes use restrictions (not OSI-approved). **Use as: skip** for SKIE-Universe — license incompatible with reproducibility-bar (not freely re-distributable; gating violates ReproLog model-hash discoverability).

### For H060 (PatchTST)
- **[yuqinie98/PatchTST](https://github.com/yuqinie98/PatchTST)** — Official ICLR 2023 implementation. License visible on repo (verify at fetch). **Use as: starting point — yes.**
- **[ibm-granite/granite-timeseries-patchtst](https://huggingface.co/ibm-granite/granite-timeseries-patchtst)** — IBM-pretrained PatchTST checkpoints. **Use as: reference only** — pretraining contamination concern same as TSFMs in §8.

### Supporting infrastructure (cross-cutting)
- **[microsoft/LoRA](https://github.com/microsoft/LoRA)** + Hugging Face PEFT — production LoRA. **Use as: starting point — yes** for adapter implementation across H058/H059.
- **[state-spaces/mamba](https://github.com/state-spaces/mamba)** — Apache-2.0; Linux+CUDA only. **Use as: skip** unless H057 is reactivated.

---

## 7. Failure-mode catalog

| Failure mode | H057 | H058 | H059 | H060 |
|---|---|---|---|---|
| PIT leakage in features | Low (causal padding enforced; unit-testable per H050 §3 leakage suite) | **Medium-High** — pretrained model may have seen overlapping dates; contamination separate from feature PIT | Medium (rendered chart axis-scaling can leak future via auto-scale) | Low (same as H057) |
| Pretraining-corpus contamination | None | **High** (see §8) | Medium (visual-prior contamination, not direct label leakage) | None |
| Render-config sensitivity | N/A | N/A | **High** — unbounded design-space if not pre-frozen | N/A |
| Inference latency at 1-min bar | Low (CNN: <1 ms) | Low–Medium (Chronos-Bolt-base ~ms; Moirai-large ~10s of ms) | **Medium** (7B VLM ~50–200 ms / inference on A100; CPU infeasible) | Low–Medium |
| GPU memory at training | Low | Medium (Moirai-large LoRA fits on 24 GB) | **High** (7B VLM LoRA at non-trivial image res needs 40 GB+) | Medium |
| Calibration drift across folds | Medium (CNN softmax often over-confident; need temperature scaling per fold) | Medium (TSFM probabilistic heads are reasonably calibrated out-of-box) | High (VLM logits not calibrated for trading-decision precision) | Medium |
| Triple-barrier label imbalance (top-bottom-vertical hit rates differ) | Same as H050 LGB baseline; class-weighted loss | Same | Same — but VLM cannot easily ingest class weights via prompt-only fine-tune; needs head-level loss override | Same |
| SPA family inflation under hyperparameter sweep | Medium (dozen-ish CNN configs) | **High** (5–6 backbones × LoRA rank × LR × adapter target) | **High** (backbone × LoRA × render config × prompt template) | Medium |
| Reproducibility (`model_hash` discipline) | Easy — model state dict | Easy if backbone-hash + adapter-hash both captured | **Hard** — must hash backbone + LoRA + render config + tokenizer + prompt template; spec needs explicit ADR | Easy |

The SPA family-inflation row is the most under-appreciated risk and ties directly to [Bailey & López de Prado 2014](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551). H058 and H059 must pre-register exactly *which* backbone(s), *which* LoRA configs, *which* render configs, *which* prompts before any test-window touch. The user brief's constraint #4 is non-negotiable.

---

## 8. Pretraining-corpus contamination assessment

**The headline finding.** [Meyer, Kaltenpoth, Zalipski, Müller 2025, arxiv 2510.13654](https://arxiv.org/abs/2510.13654) ("Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges") identifies two leakage classes — train-test sample overlap from multi-purpose dataset reuse, and temporal overlap of correlated train/test series — and reports verbatim from the abstract (verified via WebFetch 2026-04-27): "Ignoring these forms of information leakage when benchmarking TSFMs risks producing overly optimistic performance estimates that fail to generalize to real-world settings." The empirical magnitudes from the verified paper are ~43% (Madrid transport temporal-leakage experiment, MAE 248.24 vs 439.14 with vs without leakage) and ~37% (COVID stock-market regime experiment, ~190 vs ~217 MAE during the crash period). **L-R1-2 closure note**: an earlier draft cited a "47%–184% lower MSE rate" figure sourced from a WebSearch summary; the figure does not appear in the primary source and has been retracted across all artifacts.

**Per-model risk for ES/NQ 1-min OHLCV 2020-2025:**

- **TimesFM**: pretraining corpus dominated by Wikipedia pageviews (2012–2023) + Google Trends (22 k series) + M4/electricity/traffic + 3 M ARMA-synthetic. **No evidence of futures or equity OHLCV in the public corpus description.** Lowest-contamination baseline. Caveat: the 100 B time-points are not exhaustively enumerated in the model card.
- **Chronos**: "Large collection of publicly available datasets" + Gaussian-process synthetic. The exact dataset list is in the paper appendix (not fetched at full-text this session — flag for downstream agent). Search-summary indication that financial public datasets are part of the mix (no specific confirmation of futures); **medium contamination risk**, requires explicit appendix scan.
- **Moirai (LOTSA)**: explicitly includes "economics" as one of nine domains; 27 B observations across 105 datasets including (per project page summaries) FRED-MD-style macro and currency series. **Highest direct-overlap risk** with H050's macro-feature substrate (although H050 itself uses microstructure features not macro; the overlap is at the *underlying ES/NQ price* level if any equity-index series are in LOTSA — undetermined this session).
- **Lag-Llama**: trained on "all public time series in Monash repository" + additional sources. Monash explicitly contains: m4-financial, m3-financial, fred-md, exchange-rate, NN5 cash-machine. **Exchange-rate and FRED-MD overlap with H050's macro-conditioning context.** Medium-high risk; no specific evidence of ES/NQ.
- **MOMENT (Time-series Pile)**: M4, ETT (Electricity Transformer Temperature), weather, traffic, electricity, exchange-rate, ILI, WTH per the paper. **Exchange-rate overlap** but again no direct evidence of ES/NQ. Medium.
- **PatchTST / iTransformer / TimesNet (H060)**: trained from scratch by user; **zero contamination** by construction. This is the strongest argument for H060 over H058.

**Mitigation if H058 proceeds.** (a) Pre-register the contamination-screen procedure: for each backbone, query the published pretraining-data list for any series matching {`^ES`, `^NQ`, `S&P 500`, `Nasdaq 100`, `e-mini`, `equity index futures`, `CME front-month`, frequency ≤ 1d}. (b) If any match → exclude that backbone or document the contamination magnitude. (c) Treat the 2024-2025 portion of H050's test window with extra suspicion — most TSFM training cutoffs are <= 2023.

**For H059 VLM contamination.** Different concern entirely: the model is unlikely to have memorised specific ES/NQ chart images with their forward returns labelled, but it will have seen many labelled candlestick chart explanations ("hammer = reversal", "doji = indecision") in its text-image pretraining. This biases the visual prior toward the *folklore* of technical analysis rather than toward the actual statistical structure of ES/NQ. Note this in the H059 pre-reg as a known prior; it is not a leak in the strict ReproLog sense (no future data in train) but it does mean the model's "intuition" is contaminated by the same retail-trader literature the H050 universe exists to outperform.

---

## 9. Recommended targeted-research scope per surviving hypothesis

For each, the downstream agent's brief is to produce a complete pre-registration design doc per [research/01_hypothesis_register/_TEMPLATE.md](../../research/01_hypothesis_register/_TEMPLATE.md), commensurable with [H050/design.md](../../research/01_hypothesis_register/H050/design.md). Sections 1–11 of the H050 doc are the exact target schema.

### H057 targeted-research brief
- **Architecture pre-reg**: depth ∈ {3, 5, 7}; channels ∈ {32, 64, 128}; kernel ∈ {3, 5, 7}; dilation off vs power-of-two; dropout ∈ {0.0, 0.1, 0.3}. Pre-register the full grid; total ≤ 30 cells; use Bergstra & Bengio random-search budget per [H050 §5](../../research/01_hypothesis_register/H050/design.md).
- **Input**: 60-bar × 5-channel (open, high, low, close, volume) tensor with right-anchored (causal) windowing; per-channel z-score with rolling stats from training fold only.
- **Output**: 3-class softmax over triple-barrier; same labeller as H050.
- **HMM gate**: identical to H050; reuse `select_gaussian_hmm` cache from commit `1c85f5f` for amortization.
- **Inference**: LW2008 differential CI (primary) + Hansen SPA `M=1` pass-through (corroborative) per [ADR-0008](../../docs/decisions/ADR-0008-spa-omega-method.md).
- **PIT canary**: extend [tests/unit/test_h050_aggregation_convention.py](../../tests/unit/test_h050_aggregation_convention.py) with a CNN-specific look-ahead probe (perturb last bar in window, assert prediction changes; perturb future bar absent from window, assert prediction unchanged).

### H058 targeted-research brief
- **Backbone shortlist (binding at pre-reg)**: TimesFM-2.5-200M (lowest-contamination) + Chronos-Bolt-base-205M (broadest zero-shot evidence). Maximum 2 backbones; SPA family entries documented as 2.
- **Adapter pre-reg**: LoRA rank ∈ {4, 8, 16}; α ∈ {8, 16, 32}; target modules = backbone-specific defaults from PEFT; learning rate on log grid {1e-5, 1e-4, 1e-3}.
- **Head**: replace TSFM forecasting head with a 3-class MLP head (single hidden 128, ReLU); pre-train head with frozen backbone for 1 epoch then LoRA-tune backbone + head jointly.
- **Contamination screen**: explicit per-backbone search of the published pretraining data list for ES/NQ-related series. Output binding `{backbone: contamination_status}` to design doc §11.
- **PIT canary**: identical to H057 plus an additional check that the TSFM `context_length` window does not exceed the H050 walk-forward training fold's right edge.

### H059 targeted-research brief
- **Backbone**: Qwen2.5-VL-7B (Apache-2.0; widest tooling support).
- **Render config (binding at pre-reg)**: 60 candles, 4:3 aspect, OHLC bar-style (not candle bodies — eliminates body-color confound), no indicator overlay, log y-axis, fixed axis ranges set from training-fold percentiles only (not auto-scale — eliminates a major leak channel). One config; no sweep.
- **Adapter pre-reg**: LoRA rank 16 on attention projections only; α=32; LR 1e-4; 3 epochs.
- **Prompt (binding)**: One zero-shot prompt and one fine-tune-target prompt; pre-registered text. No prompt sweep.
- **Output**: parse the VLM text output into {up, down, vertical} via constrained decoding or grammar-constrained sampling; if parse fails → vertical (conservative).
- **PIT canary**: critical — render the same 60-bar window with two different right-edge timestamps (one in train, one in test); assert pixel-identity except for axis labels. Catches axis-label-as-side-channel leakage.
- **Cite Hu, Xiao, Xu, Tang, Liu 2026** ([arxiv 2604.12659](https://arxiv.org/abs/2604.12659)) explicitly in the design doc §1 mechanism section as the published-prior on VLM candlestick reading; note that H059 is testing the LoRA-fine-tune variant which that paper does not study.

### H060 targeted-research brief
- **Backbone**: PatchTST trained from scratch on H050 substrate (no pretrained checkpoint, no contamination).
- **Architecture pre-reg**: patch_len ∈ {8, 16}; stride = patch_len/2; n_layers ∈ {3, 6}; n_heads ∈ {4, 8}; d_model ∈ {64, 128}; channel-independent per the canonical PatchTST recipe.
- **Same HMM gate, same labeller, same inference (LW2008 + SPA `M=1` for now), same canary suite as H057**.

---

## 10. Open questions for the lead researcher

1. **SPA family budget across the four arms.** With H050 already in the family and H057 + H058 (2 backbones) + H059 + H060 entering, the test-window family count is 6. Is it acceptable to enter all six simultaneously into a single Hansen SPA, or should they enter sequentially with an explicit "spent-α" accounting per Romano-Wolf step-down? `quant-project.md` §Inference does not bind on this. **Decision needed before any agent commits to design-doc finalization.**

2. **Contamination magnitude figure** — **Closed 2026-04-27 (verified-as-fabricated)** by Round-1 literature-check L-R1-2. The "47%–184%" figure does not appear in the primary source; verified figures are ~43% (Madrid transport) and ~37% (COVID stock market). Retracted across all artifacts; the qualitative abstract claim is the load-bearing reference.

3. **Render-config freeze for H059.** The recommended binding ("60 candles, 4:3, OHLC bars, no overlay, log y, fixed train-fold axis range") is a defensible default but not literature-pinned. Does the lead want to anchor on a specific published render config (e.g., the one used by Hu, Xiao, Xu, Tang, Liu 2026 [arxiv 2604.12659](https://arxiv.org/abs/2604.12659)) for direct comparability, even if it differs from project-internal preference?

4. **CLAUDE.md / hypothesis_backlog.md update.** New hypotheses H057–H060 will need rows in [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md) under Tier 2b or a new Tier 2c "AI chart reader" section. Lead's call. Not modified in this session per memo-only-no-file-changes scope.

5. **CLAUDE.md / ADR contradictions found.** None — the existing ADR-0005 / ADR-0008 / quant-project.md stack is fully consistent with the survey findings. The HMM gate, walk-forward, NW-HAC, LW2008 differential CI, and Hansen SPA infrastructure all extend cleanly to all four candidate arms.

6. **Compute budget.** H059 (7B VLM LoRA) at H050's 27-cell label grid × 12-cell hyperparameter grid × 10 random-search draws × walk-forward folds × HMM cov_type × symbol = same orchestrator-triple multiplicative blow-up as the H050 production run (3-hour kill at +180 min on the 1-dim HMM bug). H059 needs an upfront compute-budget estimate from the lead before agent kicks off — likely orders of magnitude beyond what an A100 single-GPU can do in a wall-clock week. **Practical scoping question: drop H059 to a smaller backbone (Qwen2.5-VL-3B), or accept multi-day-per-fold wall clock?**
