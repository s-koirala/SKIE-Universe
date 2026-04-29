# H059

Open VLM (Qwen2.5-VL-3B Apache-2.0) LoRA-fine-tuned on rendered candlestick chart with HMM regime gate. Tier 2c.

Status: `designed` (pre-registered 2026-04-27).

H059 is the open-VLM arm of the Tier-2c "AI chart reader" cohort registered alongside [H057](../H057/) (1D-CNN), [H058](../H058/) (TS foundation model + LoRA), and the recommended addition H060 (PatchTST trained from scratch). All four arms share the H050 substrate, HMM gate, walk-forward splitter, cost model, and triple-barrier labeller. The differential information is the model class. See [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) §3 for the cohort-level framing and the §9 H059-specific brief on which this pre-registration is built.

**Data readiness (inherited from H050).** Substrate is the H050 roll-adjusted ES + NQ 1-minute parquet (combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`, 7,354,066 rows, 2015-01-01 → 2025-12-{03, 19} UTC) per [H050/data_requirements.md](../H050/data_requirements.md). H059 introduces no new ingest; the rendered-chart inputs are computed at decision time from the substrate. The right-edge truncation (28 days short for ES, 12 days short for NQ at 2025-12-31) applies symmetrically and is tracked under follow-up `P1-DATABENTO-RIGHT-EDGE-EXTENSION`.

**Differential information (one-line).** H059 ingests the rendered 60-bar OHLC chart as a 2D image; spatial relationships between bars (gaps, wicks, multi-bar pattern formations) are first-class inputs that no 1D representation in H050 / H057 / H058 surfaces directly.

**Bearish published prior.** [Hu, Xiao, Xu, Tang, Liu 2026, arxiv 2604.12659](https://arxiv.org/abs/2604.12659) report (verified verbatim via WebFetch 2026-04-27): "most VLMs perform well only under persistent uptrend or downtrend conditions, while exhibiting weak predictive capability in more common market scenarios." H059 tests the **LoRA-fine-tuned** variant which Hu, Xiao, Xu, Tang, Liu 2026 do not study; the H0 reflects the bearish prior — positive paired evidence (LW2008 CI excludes zero) is required before promotion.

**Render config decision.** WebFetch of the Hu, Xiao, Xu, Tang, Liu 2026 paper reveals their config (50-bar candle bodies with GREEN/RED color, MA5/MA20/MA90 overlays, separate volume panel, linear y-axis, header with cutoff date) is **incompatible with strict PIT discipline** — the cutoff-date header is a direct date→regime side channel; body color encodes the sign of `close − open` of the window-closing bar. H059 adopts the lead-researcher defaults (60-bar OHLC bars monochrome, no overlays, log y-axis, fixed-range from training-fold percentiles only, no header). Direct numerical comparability with Hu, Xiao, Xu, Tang, Liu 2026 is sacrificed for evidence-bar PIT compliance. See [design.md §3.2](design.md) for the full comparison table.

**Compute commitment.** Per-bar cadence is the binding cadence per Q-R1-2 + synthesis memo §6 Family B uniform-cadence binding. Pilot fold-0 wall-clock is the empirical feasibility gate; >7 days/fold triggers `archive(null, infeasible)` and successor H059b registration at HMM-state-transition cadence per `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`.

See [design.md](design.md) for the pre-registration. No execution until status transitions to `running` by explicit commit.
