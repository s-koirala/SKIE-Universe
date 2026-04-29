# Hypothesis Backlog

Every signal, transform, or angle considered for this project. Status transitions:
`queued → designed → running → evaluated → archived(positive|null|negative)`.

Each row gets a dedicated design doc in [../research/01_hypothesis_register/](../research/01_hypothesis_register/) before execution, with pre-registered hypothesis, data, estimator, assumptions, and stopping rule.

## Tier 1 — directional conditioning variables (attack 50% AUC wall)

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H001 | Dealer net-gamma regime conditions intraday drift sign | [Dim-Eraker-Vilkov 2024](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190); [Cboe 0DTE GEX study](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf) | queued |
| H002 | Macro-surprise z-scores drive 5–30 min ES/NQ direction | [Andersen-Bollerslev-Diebold-Vega 2007, JIE](https://doi.org/10.1016/j.jinteco.2006.07.002) | queued |
| H003 | Kalshi macro-contract drift as directional prior pre-release | [Kalshi crypto-vol paper arXiv 2604.01431](https://arxiv.org/html/2604.01431v1) | archived(null) — round-1 lit remediation found no peer-reviewed empirics; revisit if publication emerges |
| H004 | FOMC statement semantic delta (hawkish-tilt) directional within 10 min of release | [Cieslak-Morse-Vissing-Jorgensen](https://www.aeaweb.org/articles?id=10.1257/aer.20180850) | queued |
| H005 | Retail 0DTE P/C ratio contrarian for last-hour ES | — | queued |

## Tier 2 — microstructure / flow

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H010 | Deep OFI (Kolm-Turiel-Westray 2021) on ES MBP-10 | [SSRN 3900141](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3900141) | queued |
| H011 | Event-time (Hawkes-clock) resampling before feature engineering | [Rambaldi-Bacry-Muzy 2017](https://arxiv.org/abs/1412.7096); [Oxford JFEC MHP 2024](https://academic.oup.com/jfec/article/22/3/743/7082927) | queued |
| H012 | Transfer entropy ES ↔ MES ↔ SPY ↔ 0DTE-implied-spot ↔ Kalshi | [Schreiber 2000, PRL](https://doi.org/10.1103/PhysRevLett.85.461); Hasbrouck 1995 | queued |
| H013 | Bouchaud square-root metaorder footprint detection | [Tóth et al. 2011](https://arxiv.org/abs/1104.1694) | queued |
| H014 | NYSE/Nasdaq MOC imbalance leakage into ES last 10 min | — (tacit) | queued |
| H015 | Treasury auction when-issued drift → ZN/ZB jump, ES beta | [Fleming-Rosenberg, NY Fed SR 299](https://www.newyorkfed.org/research/staff_reports/sr299.html) | queued |

## Tier 3 — frontier / low published coverage

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H020 | Rough-volatility Hurst exponent regime detector | [Gatheral-Jaisson-Rosenbaum 2018, Quant Fin](https://doi.org/10.1080/14697688.2017.1393551) | queued |
| H021 | Live FOMC speech sentence-level embedding drift → ES direction | [Macro-alpha FinBERT arXiv 2505.16136](https://arxiv.org/html/2505.16136v1) | queued |
| H022 | Stablecoin mint/burn → BTC basis → ES risk-on/off beta | [CF Benchmarks basis](https://www.cfbenchmarks.com/blog/revisiting-the-bitcoin-basis-how-momentum-sentiment-impact-the-structural-drivers-of-basis-activity) | queued |
| H023 | AIS vessel arrival events at oil terminals → CL → ES energy-beta path | — | queued |
| H024 | ERCOT/PJM nodal LMP + HRRR nowcast → NG → ES commodity-beta | — | queued |
| H025 | FX carry unwind via SOFR-IOER spread → ES direction | — | queued |
| H026 | Implied-realized correlation divergence (CBOE COR) as regime gate | — | queued |

## Tier 4 — execution / portfolio

| ID | Angle | Mechanism | Status |
|---|---|---|---|
| H040 | Stack Tier-1 directional gates on existing vol/size/breakout models | internal SKIE-Ninja ensemble | queued |
| H041 | Kelly-fractional sizing with Sharpe-bootstrap CI floor | [Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084) | queued |
| H042 | Hansen SPA gate across the full accumulated strategy universe | [Hansen 2005, JBES](https://doi.org/10.1198/073500105000000063) | queued |

## Tier 2b — regime/state (added 2026-04-20 per ADR-0006)

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
<!-- hypothesis_new.py appended --> H050 | HMM regime-conditioned ES/NQ intraday directional signal | [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Ryou et al. 2020, Sustainability 12(17):7031](https://doi.org/10.3390/su12177031); [Guidolin & Timmermann 2007, JEDC 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004) | designed |
<!-- hypothesis_new.py appended --> H051 | HMM-gated ES/NQ (or MES/MNQ) basis pairs trade with Kalman hedge ratio | [Johansen 1991](https://doi.org/10.2307/2938278); [Osterwald-Lenum 1992](https://doi.org/10.1111/j.1468-0084.1992.tb00013.x); West & Harrison 1997, ISBN 978-0387947259; Chan 2013, ISBN 978-1118460146 | designed |
<!-- hypothesis_new.py appended --> H052a | HMM regime-gated first-hour ORB on CME futures (ES/NQ/MNQ/MES) | [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Guidolin-Timmermann 2007](https://doi.org/10.1016/j.jedc.2006.12.004); [Andersen-Bollerslev 1998](https://doi.org/10.2307/2527343); de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1119482086) — HMM-gate is sole new content on a prior-art-null underlying | designed |
<!-- hypothesis_new.py appended --> H052b | HMM regime-gated QQQ first-hour long-call 0DTE scalp (SKIE-ORB-CALL overlay) | [Ryou et al. 2020](https://doi.org/10.3390/su12177031); [Guidolin-Timmermann 2007](https://doi.org/10.1016/j.jedc.2006.12.004); [Hamilton 1989](https://doi.org/10.2307/1912559); [Andersen-Bollerslev 1998](https://doi.org/10.2307/2527343); de Prado 2018 *Advances in Financial Machine Learning* (Wiley, ISBN 978-1119482086); sibling repo [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) | designed (renamed from H052 → H052b on 2026-04-23) |

## 2026-04-23 — Tier-2b split

H052 split into two siblings: **H052a** (HMM-gated ORB on CME futures ES/NQ/MNQ/MES) and **H052b** (HMM-gated QQQ 0DTE long-call scalp; the original H052 renamed, content unchanged). Rationale: the SKIE-ORB-CALL first-hour directional signal is economically separable from its long-premium-call execution wrapper; running it on futures tests the regime-gating content on a prior-art-null underlying (directional futures ≈50% AUC per [README.md](../README.md) §Prior-art), isolating the HMM gate as the sole new empirical content. Data substrate for H052a is already live (raw 1-min); H052b remains vendor-gated on the QQQ 0DTE option chain. Both enter the same Hansen SPA universe snapshot so no inflation of the multiple-testing family.

## Tier 2c — AI chart reader (added 2026-04-27)

Four hypotheses scoped via the audit-remediated chart-reader survey + targeted-research package: [docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md](../docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md) (synthesis) and [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) (landscape). All four are commensurable with H050 by construction (same labeller, same HMM gate, same walk-forward folds, same cost model) and enter a **Family B Hansen 2005 SPA cohort** (M=5: H057 + H058a + H058b + H059 + H060) with H050 as **baseline anchor only** (H050 stays in Family A under Romano-Wolf step-down per [ADR-0003](../docs/decisions/ADR-0003-spa-vs-romanowolf.md) per its frozen pre-reg). Test statistic: `T_arm = SR_arm_gated − SR_H050_gated`. Hosted/black-box VLMs (Claude, GPT-4V, Gemini) explicitly disqualified — open weights only, hashable into `ReproLog.model_hash`.

| ID | Angle | Mechanism / citation | Status |
|---|---|---|---|
| H057 | 1D-CNN on causal 60×5 OHLCV tensor with HMM regime gate (train-from-scratch, zero pretraining contamination) | [Sezer & Ozbayoglu 2018](https://www.sciencedirect.com/science/article/abs/pii/S1568494618302151); [Wang & Oates 2015 arxiv 1506.00327](https://arxiv.org/abs/1506.00327); [Bai-Kolter-Koltun 2018 TCN arxiv 1803.01271](https://arxiv.org/abs/1803.01271); [Hamilton 1989](https://doi.org/10.2307/1912559) | designed |
| H058 | TS foundation model (TimesFM-2.5-200M + Chronos-Bolt-base-205M) with LoRA fine-tune and HMM regime gate | [Das et al. 2024 TimesFM arxiv 2310.10688](https://arxiv.org/abs/2310.10688); [Ansari et al. 2024 Chronos arxiv 2403.07815](https://arxiv.org/abs/2403.07815); [Hu et al. 2022 LoRA arxiv 2106.09685](https://arxiv.org/abs/2106.09685); [Meyer, Kaltenpoth, Zalipski, Müller 2025 arxiv 2510.13654](https://arxiv.org/abs/2510.13654) (TSFM contamination) | designed |
| H059 | Open VLM (Qwen2.5-VL-3B-Instruct) LoRA fine-tuned on rendered candlestick chart with HMM regime gate; per-bar inference cadence | [Bai et al. 2025 Qwen2.5-VL arxiv 2502.13923](https://arxiv.org/abs/2502.13923); [Hu et al. 2022 LoRA arxiv 2106.09685](https://arxiv.org/abs/2106.09685); [Hu, Xiao, Xu, Tang, Liu 2026 arxiv 2604.12659](https://arxiv.org/abs/2604.12659) (published bearish prior on VLM candlestick reading) | designed |
| H060 | PatchTST trained from scratch on causal 60×5 OHLCV with HMM regime gate (train-from-scratch transformer baseline; zero pretraining contamination by construction) | [Nie, Nguyen et al. 2023 PatchTST arxiv 2211.14730](https://arxiv.org/abs/2211.14730); [Hamilton 1989](https://doi.org/10.2307/1912559); [Bergstra & Bengio 2012 random search](https://www.jmlr.org/papers/v13/bergstra12a.html) | designed |

**Triangulation logic.** H057 (CNN inductive prior, no contamination) + H060 (attention prior, no contamination) + H058 (cross-domain TS pretraining) + H059 (visual representation prior) is a covering set: if H057 ≈ H050, deep learning is not the bottleneck; if H058 ≫ H057+H060, pretraining is the value; if H059 ≫ H058, visual representation is the value. Without the contrast structure each one is a blind shot.

**Gating follow-ups before `status=running`.** `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` (all four arms — multi-sidecar `model_hash` composition; interim deterministic per-arm pre-aggregation rule pinned in synthesis memo §5); `P1-CHARTREADER-PER-ARM-POWER-CALC` (all four arms — per-arm `n_required_for_power_80` from per-arm pilot dispersion); `P1-H058-TIMESFM-GIFTEVAL-INSPECTION` + `P1-H058-CHRONOS-APPENDIX-INSPECTION` (H058 backbone-corpus contamination scans); `P1-H059-WALL-CLOCK-PILOT-MEASUREMENT` (H059 fold-0 per-bar wall-clock gate; `archive(null, infeasible)` triggers H059b successor at HMM-state-transition cadence per `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`); `P1-H060-LR-DEFAULT-LITERATURE-CHECK` (PatchTST `lr=1e-4` ETT-default transferability to 1-min equity-index futures); `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` (Family A H050 design.md Romano-Wolf vs H050.yaml Hansen SPA inconsistency — independent of Family B but binding before any Family-A-aggregate inference).

Audit trail: [docs/audits/audit_trail_2026-04-27_chartreader-hypothesis-package.md](../docs/audits/audit_trail_2026-04-27_chartreader-hypothesis-package.md) (3-round audit-remediate-loop; quant-auditor + literature-check + reproducibility-verifier; 36 Round-1 findings + 22 Round-2 findings remediated; Round-3 verdict `clear`).

## Round-1 remediation adjustments (2026-04-15)

Lit-check audit invalidated three cites grounding these hypotheses. Status updates:
- **H003** → `archived(null)` above.
- **H030** (iceberg detection) → downgrade Tier-2 HIGH to MED; deep-learning framing unsupported, survives as survival / hidden-liquidity.
- **H044** (weekly OI pin migration) → `archived(null)`; mechanism unsupported by current citations.

New items append with sequential IDs. Negative/null results move to `archived(null)` but **stay in the file** — they document the search space we've covered.
