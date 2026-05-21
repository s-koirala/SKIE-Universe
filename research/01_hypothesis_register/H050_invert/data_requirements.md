---
name: H050.invert data requirements
description: Pre-registration dataset checksums and coverage bounds for H050.invert
type: project
hypothesis_id: H050_invert
parent_hypothesis_id: H050
status: designed
created: 2026-05-20
---

# H050.invert — Data Requirements

Pre-registration companion to [design.md](design.md) §16. Frozen at the time the hypothesis moves to `status=running`. Any subsequent dataset update requires a successor hypothesis ID per [ADR-0013 §"Frozen pre-registration amendment"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).

Per [ADR-0027 §D-4 genetic-successor "preserved infrastructure"](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md), the substrate is the canonical post-Phase-O.10 ES + NQ 1-min roll-adjusted frame (CLAUDE.md Phase O.10 + [memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)). The H050 v1 binding `b3ee230a...` is superseded; H050.invert uses the canonical-going-forward substrate.

## Source dataset

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m |
| License | Databento EULA. Verified 2026-04-23; no redistribution; internal research use only. |
| Symbols | ES.FUT, NQ.FUT (front-month) |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment (López de Prado 2018, Wiley) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` v0.3.0+ per CLAUDE.md Phase O.10 Path-C re-ingest |

## Coverage

| Field | Value |
|---|---|
| ES date range | 2015-01-01 → 2025-12-03 UTC (last bar `ts_event`) |
| NQ date range | 2015-01-01 → 2025-12-19 UTC (last bar `ts_event`) |
| Train window (per [design.md](design.md) §2) | 2015-01-01 → 2022-12-31 |
| Validation window | 2023-01-01 → 2023-12-31 |
| Test window | 2024-01-01 → 2025-12-31 (right-edge truncation: ES 28 days short; NQ 12 days short per parent H050 `P1-DATABENTO-RIGHT-EDGE-EXTENSION`) |

## Substrate binding

| Field | Value |
|---|---|
| Combined SHA256 (canonical post-Phase-O.10) | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` |
| Provenance JSON | per CLAUDE.md Phase O.10 Path-C re-ingest run_id `38d63bdd2def4fa9804c78fbcb1a76ce` (Stage B vendor_legacy_1min_roll_adjusted) |
| Computed | 2026-05-18 (CLAUDE.md Phase O.10) |

Per-partition SHA enumeration for ES + NQ × 2015-2025 inherits from the H050 v1 + canonical-substrate ledger; this hypothesis does NOT introduce a new substrate vintage. The 22-partition table at [research/01_hypothesis_register/H050/data_requirements.md](../H050/data_requirements.md) §"Per-partition" is canonical; H050.invert uses the post-Phase-O.10 reconciliation per CLAUDE.md Phase O.10 + the [substrate-vintage memo](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md).

## Cross-hypothesis fit-set isolation table

| Hypothesis | Train + Val window | Test window | Substrate vintage |
|---|---|---|---|
| H050 v1 | 2015-01-01 → 2023-12-31 | 2024-01-01 → 2025-12-31 | `b3ee230a...` (Phase G v1 binding; superseded by Phase O.10) |
| H050.invert v1 (this) | 2015-01-01 → 2023-12-31 | 2024-01-01 → 2025-12-31 | `317429e4...` (canonical post-Phase-O.10) |
| H050.stable-state v1 (sibling) | 2015-01-01 → 2023-12-31 | 2024-01-01 → 2025-12-31 | `317429e4...` |

H050.invert and H050.stable-state share the same train/val/test window with H050 v1 + each other to enable direct cross-arm comparability per ADR-0027 §D-4 genetic-successor discipline. **The OOS overlap with H050 v1's OOS test fold is acknowledged**; this is intentional because the variants are mechanism-discrimination tests of the SAME parent hypothesis on the SAME OOS fold (per the paired-design framing in [design.md §1 + §12](design.md)). KPI annotation: `data-overlap-h050-v1-acknowledged` per the H055 substrate-overlap convention.

## OFI dependency note

Inherits from H050 v1 §"OFI dependency note": feature `ofi_tickrule@1.0` uses tick-rule proxy (Lee-Ready); MBP-10 upgrade path is the same as H050 v1; tracked under the project-wide H010 dependency (NOT H050.invert-blocking).

## Provenance file

Machine-readable provenance records inherit from the canonical post-Phase-O.10 substrate at `data/processed/_provenance/vendor_legacy_1min_roll_adjusted_*.json` per CLAUDE.md Phase O.10 substrate Path-C re-ingest.
