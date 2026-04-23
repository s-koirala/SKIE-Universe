# H050

HMM regime-conditioned ES/NQ intraday directional signal. Tier 2b.

Status: `designed` (pre-registered 2026-04-20).

**Data readiness (updated 2026-04-23):** ES + NQ 1-minute raw OHLCV (Databento) live at [data/processed/vendor_legacy_1min/](../../../data/processed/vendor_legacy_1min/) via `vendor_legacy_1min` ingest. ES 2020-2025 + NQ 2020-2024 present; NQ 2025 pending sibling pull. **Raw tier is NOT evidence-bar eligible** — the series concatenates successive front-month contracts without roll adjustment, violating the rules/quant-project.md §Time-series integrity requirement (futures-analog of corporate-action adjustment). H050 must either (a) operate on contract-local windows that never cross a roll boundary, or (b) materialize a downstream roll-adjusted derivative dataset before paper-trade evidence-bar claims. Feature engineering in-project per CLAUDE.md §Verification.

See [design.md](design.md) for the pre-registration. No execution until status transitions to `running` by explicit commit.
