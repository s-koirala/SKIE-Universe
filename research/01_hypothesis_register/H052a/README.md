# H052a

HMM regime-gated first-hour ORB (opening-range breakout) on CME futures ES/NQ/MNQ/MES. Tier 2b. Sibling of [H052b](../H052b/README.md) (QQQ 0DTE-call variant).

Status: `designed` (pre-registered 2026-04-23 as the futures-variant sibling of the original H052, which was renamed to [H052b](../H052b/) on the same date).

**Data readiness (2026-04-23):** ES + NQ 1-minute raw OHLCV live at [data/processed/vendor_legacy_1min/](../../../data/processed/vendor_legacy_1min/) via the `vendor_legacy_1min` ingest (ES 2020-2025; NQ 2020-2024). Raw tier is **not evidence-bar eligible** without roll adjustment ([rules/quant-project.md](../../../.claude/rules/quant-project.md) §Time-series integrity); a `vendor_legacy_1min_roll_adjusted` derivative is prerequisite for this hypothesis promoting past `running`. See [design.md](design.md) §11.

H052a reuses the full HMM toolkit per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md) and shares the Hansen SPA universe snapshot with [H050](../H050/), [H051](../H051/), and [H052b](../H052b/). Because the underlying unconditional ORB-on-futures directional signal is prior-art-flagged as ~50% AUC ([README.md](../../../README.md) §Prior-art), **the HMM gate is the sole new empirical content** and the pre-registered decision rule auto-archives `null` if the Sharpe differential (HMM-gated minus unconditional) CI covers zero.

See [design.md](design.md). No execution until status transitions to `running` by explicit commit.
