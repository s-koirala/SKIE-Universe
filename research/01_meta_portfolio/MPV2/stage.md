---
id: MPV2
schema_version: stage_tracker_v1
created: 2026-06-15
---

# Stage Tracker — MPV2 (meta-portfolio)

Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1.1, this is an **append-only** chronological record of every stage transition. The current stage is the most recent row's `stage` value.

Stages (per ADR-0013 §1; the meta-allocator's NinjaScript terminus is the allocator itself per [ADR-0029 §D-1](../../../docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md)):
- `designed` — pre-registration frozen (§1–§7 immutable)
- `kpi-report-emitted` — full KPI report card v{N} published
- `ninjascript-implemented` — runnable allocator + smoke-test record (operator-discretionary; deferred until a beat-both-conjunctive §8 disposition)
- `retired` — operator-retired (recorded, NOT deleted)

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-06-02 | designed | [design.md](design.md) frozen at status=designed; arm set {H050, H055, H060, H062} frozen | skoir | pre-registration of the ADR-0029 §D-4 falsifiable center; P-5 closed-loop machinery + synthetic validation landed concurrently per [docs/audits/audit_trail_2026-06-02_mpv2-closed-loop.md](../../../docs/audits/audit_trail_2026-06-02_mpv2-closed-loop.md) |
| 2026-06-15 | kpi-report-emitted | [MPV2_kpi_report_v1.md](MPV2_kpi_report_v1.md) emitted; CLI-reproducible sidecar [artifacts/runs/MPV2/1980ec1eba2d4f4b965c44a965780370/sidecar.json](../../../artifacts/runs/MPV2/1980ec1eba2d4f4b965c44a965780370/sidecar.json) (run_id `1980ec1eba2d4f4b965c44a965780370`; scientific_payload_sha256 `d85ae777d754de3c6981703bc919fc16f999efcdfacdebc3a6681485221acffb`); substrate `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (arm-stream vintage `286829dc…`, common windows vintage-invariant) | skoir | **NULL disposition** — closed-loop allocator beats neither 1/N nor B&H OOS (switching MPPM −0.020 [3-arm] / +0.028 [2-arm] vs 1/N 0.320/0.261); no allocator statistically beats B&H (all paired-bootstrap lower bounds cover zero); 3-arm verdict {H055, H060, H062}, H050 deferred; ENB 2.989/3 (de-correlated → pooling dominates switching, 1/N dominates optimised joint-Kelly); causal-alignment invariant verified clean. `repro-log-complete` — `P1-MPV2-REPROLOG-WIRE` CLOSED via `scripts/run_mpv2_closed_loop.py --real`; `P1-MPV2-REAL-RUN-AUDIT` Round-1 trail [docs/audits/audit_trail_2026-06-15_mpv2-kpi-card-and-real-run.md](../../../docs/audits/audit_trail_2026-06-15_mpv2-kpi-card-and-real-run.md). Result reframes center of gravity per [ADR-0030](../../../docs/decisions/ADR-0030-cost-light-arm-generation-refined-center-of-gravity.md) |

## Append discipline

- New rows APPEND to the table; existing rows are immutable.
- A correction produces a new row with `notes` annotated `corrects row N`; the original stays.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).

## Cross-references

- Design (pre-registration): [design.md](design.md)
- KPI report cards: `MPV2_kpi_report_v{N}.md`
- Numeric source of record (real-data drive): [plan/buildouts/phase_p_regime_switching_closed_loop_buildout.md](../../../plan/buildouts/phase_p_regime_switching_closed_loop_buildout.md) §P-5
