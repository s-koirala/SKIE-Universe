# H052

HMM regime-gated QQQ first-hour long-call 0DTE scalp (SKIE-ORB-CALL overlay). Tier 3 (frontier / low published coverage).

Status: `designed` (pre-registered 2026-04-20).

**Data readiness (2026-04-20):** QQQ 0DTE option chain not yet provisioned (see [audit_trail_2026-04-20_phase1-ingest-remediation.md](../../../docs/audits/audit_trail_2026-04-20_phase1-ingest-remediation.md)). ADR-0006 cross-validation on NQ/MNQ blocked until NQ data is provisioned (see [audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md](../../../docs/audits/audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md)).

See [design.md](design.md). Canonical code path under [ADR-0006](../../../docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) Option C is the sibling repo [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) (internal project code **SKIE-ORB-CALL**; author Sudarshan "SKIE" Koirala; created 2026-04-19). The sibling repo codifies the underlying thesis — QQQ first-hour (09:30–10:30 ET) bullish-bias green-rate > 0.50, operationalized as a long-premium 0DTE/1DTE call scalp — and runs CPCV + PBO + Bonferroni / Holm-Sidak internally. H052 pre-registers an HMM regime gate layered on top of that binomial signal and carries our intraday-level Hansen SPA bookkeeping. If the sibling-repo Phase-1 binomial test fails, H052 auto-archives as `null, precondition-failed`.
