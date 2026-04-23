# H051

HMM-gated ES/NQ basis pairs trade. Tier 2b.

Status: `designed` (pre-registered 2026-04-20).

**Data readiness (2026-04-20):** H051 is an ES/NQ (or MES/MNQ) basis pair — **materially blocked on NQ 5-min provisioning**. ES 5-min prototype-tier data available via [`vendor_skie_ninja_legacy`](../../../config/data_sources.yaml); NQ arm absent. See [audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md](../../../docs/audits/audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md) follow-up #2 for NQ options.

See [design.md](design.md). Johansen cointegration pre-screen is a mandatory halt gate before HMM fit.
