# H061 stage tracker

Append-only per ADR-0013 §4.1 non-loss mandate.

| Date | Stage | Trigger | Artifact |
|---|---|---|---|
| 2026-05-12 | `exploration-in-progress` | initial pre-registration draft committed; status `designed` | [design.md](design.md) |

**Current stage**: `exploration-in-progress` (as of 2026-05-12); design pre-registered at `status: designed`.

**Next mandatory transition** (per ADR-0013 §1 + §5): `exploration-in-progress` → `kpi-report-emitted`. Blocked by:
- `P1-H061-CL-SUBSTRATE-EXTRACTION-AUTHORIZE` (operator-action; ~$240 USD; the load-bearing BLOCKING precondition per design.md §11.2)
- `P1-H061-CL-DATA-INGEST-RUN` (depends on above)
- `P1-H061-INSTRUMENTS-YAML-CL-ENTRY` (~10 min)
- `P1-H061-PIT-CANARY-INTEGRATION-TEST`
- `P1-H061-POWER-SIMULATION-EXECUTE`
- Inherited from ADR-0017 Phase L Thread A: `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE`, `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`
