---
name: H050.stable-state data requirements
description: Pre-registration dataset checksums and coverage bounds for H050.stable-state
type: project
hypothesis_id: H050_stable_state
parent_hypothesis_id: H050
status: designed
created: 2026-05-20
---

# H050.stable-state — Data Requirements

Pre-registration companion to [design.md](design.md) §16. Frozen at the time the hypothesis moves to `status=running`. Any subsequent dataset update requires a successor hypothesis ID per [ADR-0013 §"Frozen pre-registration amendment"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).

Per [ADR-0027 §D-4 genetic-successor "preserved infrastructure"](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md), the substrate is the canonical post-Phase-O.10 ES + NQ 1-min roll-adjusted frame (CLAUDE.md Phase O.10 + [memo_substrate-vintage-inventory_2026-05-18.md](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md)).

## Source dataset

| Field | Value |
|---|---|
| Vendor | Databento GLBX.MDP3 |
| Schema | ohlcv-1m |
| License | Databento EULA. Verified 2026-04-23. |
| Symbols | ES.FUT, NQ.FUT (front-month) |
| Raw landing path | `~/datasets/vendor_skie_ninja_legacy/raw_1min/` |
| Processed (roll-adjusted) path | `data/processed/vendor_legacy_1min_roll_adjusted/` |
| Roll-adjustment method | AFML §2.4.3 ratio adjustment (López de Prado 2018, Wiley) |
| Ingest module | `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` v0.3.0+ per CLAUDE.md Phase O.10 |

## Coverage

| Field | Value |
|---|---|
| ES date range | 2015-01-01 → 2025-12-03 UTC |
| NQ date range | 2015-01-01 → 2025-12-19 UTC |
| Train window (per [design.md](design.md) §2) | 2015-01-01 → 2022-12-31 |
| Validation window | 2023-01-01 → 2023-12-31 |
| Test window | 2024-01-01 → 2025-12-31 (right-edge truncation per parent H050 `P1-DATABENTO-RIGHT-EDGE-EXTENSION`) |

## Substrate binding

| Field | Value |
|---|---|
| Combined SHA256 (canonical post-Phase-O.10) | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` |
| Provenance JSON | per CLAUDE.md Phase O.10 Path-C re-ingest run_id `38d63bdd2def4fa9804c78fbcb1a76ce` |
| Computed | 2026-05-18 (CLAUDE.md Phase O.10) |

Per-partition SHA enumeration inherits from [research/01_hypothesis_register/H050/data_requirements.md](../H050/data_requirements.md) §"Per-partition" (canonical post-Phase-O.10 reconciliation per the substrate-vintage memo).

## Cross-hypothesis fit-set isolation table

Identical to [H050.invert data_requirements.md](../H050_invert/data_requirements.md) §"Cross-hypothesis fit-set isolation table" — H050.invert + H050.stable-state share the same train/val/test window with H050 v1 + each other to enable direct cross-arm comparability per ADR-0027 §D-4 genetic-successor discipline. OOS overlap with H050 v1 is acknowledged via `data-overlap-h050-v1-acknowledged` KPI annotation; this is intentional under the paired-design mechanism-discrimination framing per [design.md §1 + §12](design.md).

## OFI dependency note

Inherits from H050 v1 §"OFI dependency note": tick-rule proxy (Lee-Ready); MBP-10 upgrade path tracked under H010 (NOT H050.stable-state-blocking).

## Provenance file

Machine-readable provenance records inherit from the canonical post-Phase-O.10 substrate at `data/processed/_provenance/vendor_legacy_1min_roll_adjusted_*.json` per CLAUDE.md Phase O.10 Path-C re-ingest.
