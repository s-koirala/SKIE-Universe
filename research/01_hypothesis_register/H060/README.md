# H060

PatchTST trained from scratch on causal OHLCV with HMM regime gate. Tier 2c.

Status: `designed` (pre-registered 2026-04-27).

H060 is the train-from-scratch transformer baseline added by the chart-reader hypothesis survey ([docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) §4) to complement H057's train-from-scratch CNN. The design isolates the **transformer architectural prior** on the H050 substrate with **zero pretraining contamination by construction** — the single structural difference from H058 (TS foundation model + LoRA), which inherits the contamination concern documented in survey §8.

**Backbone**: PatchTST per [Nie, Nguyen, Sinthong, Kalagnanam 2023, ICLR](https://arxiv.org/abs/2211.14730), reference implementation [yuqinie98/PatchTST](https://github.com/yuqinie98/PatchTST). Channel-independent encoder over a 60-bar × 5-channel (OHLCV) right-anchored causal window. Forecasting head replaced with a 3-class MLP classification head over the H050 triple-barrier label space. No pretrained checkpoint loaded at any step; weights initialised from random per `random_seed=20260427`.

**Differential information**:
- vs H057 (CNN, sibling train-from-scratch arm): different inductive prior. CNN exploits local translation-invariance; PatchTST attention-with-patching exploits longer-range bar-to-bar interactions.
- vs H058 (TSFM + LoRA, sibling transformer arm): same model class as TSFM backbones but trained from scratch — sidesteps pretraining contamination entirely. If H060 lands positive and H058 lands positive at similar magnitude, the architectural prior is sufficient and pretraining is not load-bearing; if H060 is null and H058 is positive, the pretraining corpus is doing the work and the contamination concern needs re-examination.

**Substrate**: binds to the identical H050 roll-adjusted substrate at [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) (combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`; module v0.3.0 per commit `329fd1b`). See [data_requirements.md](data_requirements.md) for full checksum panel and the right-edge truncation note.

**HMM gate**: identical to H050; reuses the `select_gaussian_hmm` cache from commit `1c85f5f` for amortisation. `covariance_type ∈ {diag, full}` with runtime model-class deduplication in `select_gaussian_hmm` per the cross-arm Q-R1-7 binding (synthesis memo §3 / §4); for d=1 emissions diag and full are mathematically equivalent and the dedup collapses the redundant evaluation; pre-reg grid preserved.

**Inference**: paired-differential statistic `T_H060 = SR_H060_gated − SR_H050_gated`. Primary inference is the [Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002) studentised time-series bootstrap CI; corroborative entry into the Family B Hansen 2005 SPA `{H057, H058a, H058b, H059, H060}` (M=5; H050 baseline anchor only) per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md).

See [design.md](design.md) for the pre-registration. No execution until status transitions to `running` by explicit commit.
