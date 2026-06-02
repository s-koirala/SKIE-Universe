# H057

1D-CNN on causal OHLCV tensor with HMM regime gate. Tier 2c (AI chart-reader arm).

Status: `designed` (pre-registered 2026-04-27).

H057 is the train-from-scratch convolutional arm of the four-hypothesis "AI chart-reader" extension scoped in [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../../../docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md). It is commensurable with [H050/design.md](../H050/design.md) by construction: same triple-barrier labeller, same HMM regime gate ([ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md)), same walk-forward fold roster, same `nt8_es_nq_rth_v1` cost model, same inference family. The differential-information probe is the residual non-linear interaction capacity of 1D convolutional kernels on the raw 60-bar × 5-channel (OHLCV) tensor that the H050 LightGBM baseline's hand-engineered moment features (Parkinson RV, realized variance, realized skew, OFI tick-rule proxy) collapse.

**Test statistic.** `T_H057 = SR_{H057, gated} − SR_{H050, gated}` paired-differential on cross-symbol-aggregated OOS net-of-cost returns per [H050/aggregation_rule_addendum_2026-04-24.md](../H050/aggregation_rule_addendum_2026-04-24.md) §1.2 (sub-rule 2a, equal-weighted constant 0.5 / 0.5 in arithmetic-return space).

**Inference.** Primary: Ledoit & Wolf 2008 differential CI per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) (the natural construction for a paired Sharpe difference). Corroborative: Hansen 2005 SPA `M = 1` pass-through with `omega_method="hac"`. Multi-strategy Family B Hansen 2005 SPA over `{H057, H058a, H058b, H059, H060}` (M=5; H050 is baseline anchor only and remains in Family A under Romano-Wolf step-down per ADR-0003 + synthesis memo §6) reruns with `omega_method="bootstrap"` per ADR-0008 two-tier rule.

**Data readiness.** Inherits the H050 roll-adjusted substrate at [data/processed/vendor_legacy_1min_roll_adjusted/](../../../data/processed/vendor_legacy_1min_roll_adjusted/) (combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`, 7,354,066 rows ES + NQ × 2015-2025). The substrate as-is is what the production walk-forward will use; the right-edge calendar truncation is symmetric across H050 and H057 and is tracked under inherited follow-up `P1-DATABENTO-RIGHT-EDGE-EXTENSION`.

**PIT canary.** Two CNN-specific look-ahead canaries extending the H050 leakage suite at [tests/unit/test_h050_aggregation_convention.py](../../../tests/unit/test_h050_aggregation_convention.py): (A) perturb the last bar of a window, assert prediction changes; (B) perturb a future bar absent from the window, assert prediction byte-identical. Wired both as a CI test (new `tests/unit/test_h053_cnn_lookahead_canary.py`) and as a per-fold runtime gate in the orchestrator. See [design.md](design.md) §8.4.

See [design.md](design.md) for the full pre-registration and [data_requirements.md](data_requirements.md) for the dataset checksum table. No execution until status transitions to `running` by explicit commit.
