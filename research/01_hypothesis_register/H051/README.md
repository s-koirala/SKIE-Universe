# H051

HMM-gated ES/NQ basis pairs trade. Tier 2b.

Status: `designed` (pre-registered 2026-04-20).

**Data readiness (updated 2026-04-23):** ES + NQ 1-minute raw bars now live via `vendor_legacy_1min` ingest (5 yr NQ overlap 2020-2024, 6 yr ES 2020-2025; NQ 2025 pending sibling pull). **Raw tier is NOT evidence-bar eligible** — concatenated front-month series lacks roll adjustment. H051 development (Johansen cointegration pre-screen, Kalman-beta scaffolding, walk-forward harness) may proceed on raw tier; evidence-bar Sharpe CIs require a roll-adjusted derivative. Tick-level queue-position work still gated on direct Databento tick access. See [audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](../../../docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md).

See [design.md](design.md). Johansen cointegration pre-screen is a mandatory halt gate before HMM fit.
