# H050

HMM regime-conditioned ES/NQ intraday directional signal. Tier 2b.

Status: `designed` (pre-registered 2026-04-20).

**Data readiness (2026-04-20):** ES 5-min *prototype-tier* input available via [`vendor_skie_ninja_legacy`](../../../config/data_sources.yaml) (Databento-derived, sibling-repo pipeline, 2020-01-01 → 2025-12-03). NQ 5-min **not yet provisioned** — blocks the NQ arm of the directional signal. Prototype-tier forbids evidence-bar advancement until features are re-derived in-project from raw 1-min Databento per [audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md](../../../docs/audits/audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md).

See [design.md](design.md) for the pre-registration. No execution until status transitions to `running` by explicit commit.
