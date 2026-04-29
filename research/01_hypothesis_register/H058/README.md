# H058

Time-series foundation model (TimesFM-2.5-200M + Chronos-Bolt-base-205M) with LoRA fine-tune and HMM regime gate, paired against the H050 LightGBM baseline. Tier 2c.

Status: `designed` (pre-registered 2026-04-27).

**Mechanism in one line.** A multi-domain TS-pretrained transformer encodes statistical priors (autocorrelation, multi-scale seasonality, noise structure) that a from-scratch LightGBM on engineered microstructure features cannot reach within the H050 sample; LoRA ([Hu et al. 2022, arxiv 2106.09685](https://arxiv.org/abs/2106.09685)) specialises a 3-class triple-barrier head to ES/NQ intraday dynamics while preserving the pretrained representation; the H050 HMM regime gate is reused unchanged.

**Backbone shortlist (binding at pre-reg).** Exactly two: [TimesFM-2.5-200M](https://huggingface.co/google/timesfm-2.5-200m-pytorch) (lowest documented pretraining-corpus contamination — Wikimedia Pageviews + Google Trends + GiftEvalPretrain + synthetic; no equity-index futures listed in the model card) and [Chronos-Bolt-base-205M](https://huggingface.co/amazon/chronos-bolt-base) (broadest zero-shot evidence + Apache-2.0 + smallest production-grade footprint). No other backbones may enter at run-time. See [design.md](design.md) §5.1.

**Pretraining-corpus contamination screen (binding).** Per [Meyer, Kaltenpoth, Zalipski, Müller 2025, arxiv 2510.13654](https://arxiv.org/abs/2510.13654) and the survey memo [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) §8. Initial screen executed 2026-04-27 against published model cards; both backbones return `unverified — partial`/`unverified — appendix-pending` (no positive substring match against `{^ES, ^NQ, S&P 500, Nasdaq 100, e-mini, equity index futures, CME front-month, GLBX.MDP3}` in the surface inventories, but neither corpus is fully enumerated at the model-card level). Two follow-ups gate the `status=designed → status=running` transition: `P1-H058-TIMESFM-GIFTEVAL-INSPECTION` and `P1-H058-CHRONOS-APPENDIX-INSPECTION`. See [design.md](design.md) §8.3.

**Multiple-testing.** H058 contributes 2 entries (one per backbone, H058a + H058b) to Family B Hansen 2005 SPA `{H057, H058a, H058b, H059, H060}`. Family B size M=5; H050 is baseline anchor only (Family A under Romano-Wolf per ADR-0003). `omega_method=bootstrap` per ADR-0008 two-tier rule (M ≥ 2). Primary inference is the LW2008 paired-differential studentised CI per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) §Cross-reference; SPA is corroborative.

**Data readiness.** Inherited from H050. Substrate `vendor_legacy_1min_roll_adjusted` v0.3.0 (commit `329fd1b`); combined-frame SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` per [H050/data_requirements.md](../H050/data_requirements.md). Right-edge truncation per H050 §2 / `P1-DATABENTO-RIGHT-EDGE-EXTENSION` applies symmetrically. H058 adds **no new substrate dependency** — the TSFM context tensor is derived from the existing 1-min OHLCV roll-adjusted bars.

**Compute envelope (pre-registered).** ≤ 168 GPU-hours per backbone on a single-A100 Linux host. Exceeding triggers `archive(null, compute-exceeded)` per [design.md](design.md) §11.2.

See [design.md](design.md) for the full pre-registration and [data_requirements.md](data_requirements.md) for the dataset checksum table inherited from H050. No execution until status transitions to `running` by explicit commit.
