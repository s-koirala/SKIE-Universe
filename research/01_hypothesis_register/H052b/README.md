# H052b

HMM regime-gated QQQ first-hour long-call 0DTE/1DTE scalp (SKIE-ORB-CALL overlay). Tier 2b. Sibling of [H052a](../H052a/README.md) (futures variant).

Status: `designed` (pre-registered 2026-04-20; renamed from `H052` → `H052b` on 2026-04-23 when the hypothesis was split to also carry a futures variant [H052a](../H052a/README.md)).

**Data readiness (updated 2026-04-23):** QQQ 0DTE option chain still not provisioned (see [audit_trail_2026-04-20_phase1-ingest-remediation.md](../../../docs/audits/audit_trail_2026-04-20_phase1-ingest-remediation.md) follow-ups). H052b remains vendor-gated on QQQ 0DTE chain purchase. NQ/MNQ cross-validation **unblocked** — NQ 1-min bars 2020-2024 now live via `vendor_legacy_1min` ingest ([audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](../../../docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md)). The cross-asset QQQ↔NQ consistency check specified in [design.md](design.md) §2 is now executable even without the option chain.

See [design.md](design.md). Canonical code path under [ADR-0006](../../../docs/decisions/ADR-0006-scope-extension-hmm-0dte.md) Option C is the sibling repo [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) (internal project code **SKIE-ORB-CALL**; author Sudarshan "SKIE" Koirala; created 2026-04-19). The sibling repo codifies the underlying thesis — QQQ first-hour (09:30–10:30 ET) bullish-bias green-rate > 0.50, operationalized as a long-premium 0DTE/1DTE call scalp — and runs CPCV + PBO + Bonferroni / Holm-Sidak internally. H052b pre-registers an HMM regime gate layered on top of that binomial signal and carries our intraday-level Hansen SPA bookkeeping. If the sibling-repo Phase-1 binomial test fails, H052b auto-archives as `null, precondition-failed`.

## Relationship to H052a

[H052a](../H052a/) tests the **same HMM-regime gate + same first-hour ORB timing signal** executed on **CME futures (ES/NQ/MNQ/MES) directly** rather than on QQQ 0DTE calls. This separates the economic content of the two tests:

- **H052b** tests whether HMM-regime gating improves the Sharpe of a *long-premium convex* (long gamma, negative theta) execution on a first-hour directional signal.
- **H052a** tests whether HMM-regime gating rescues a *linear-payoff* (futures) first-hour directional breakout on ES/NQ. Prior-art SKIE Ninja work flagged unconditional futures directional signals as ≈50% AUC (see [../../../README.md](../../../README.md) §Prior-art), so the HMM gate is the new empirical content — H052a auto-archives `null` if the HMM-gated Sharpe differential vs the unconditional ORB-on-futures is statistically indistinguishable from zero.

Both hypotheses share HMM toolkit infrastructure per [ADR-0005](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md). Both enter the same Hansen SPA universe snapshot.
