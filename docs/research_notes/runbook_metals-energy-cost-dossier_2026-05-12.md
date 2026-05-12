---
name: Metals/energy cost-dossier runbook (CL/MCL/GC/MGC)
description: Authorization-gated procedure for capturing the Databento `metadata.get_cost` figure for the H060 BLOCKING substrate. Stage A-equivalent of the H050 Cell-I pattern.
type: project
status: prepared, awaiting operator execution
created: 2026-05-12
hypothesis_id: H060
follow_up_id: P1-DATABENTO-METALS-ENERGY-COST-DOSSIER
related_adrs: [ADR-0023, ADR-0006]
precedent: docs/research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md
audience: skoir
---

# Runbook — Metals/energy cost dossier (2026-05-12)

## 0. Status

**Prepared. Awaiting operator execution.** The Databento `metadata.get_cost` call is a **$0 estimation** operation per [databento.com/docs/api-reference-historical/metadata/get-cost](https://databento.com/docs/api-reference-historical/metadata/get-cost) (retrieved 2026-05-12). It does NOT pull data. It returns the cost-in-USD that the corresponding `timeseries.get_range` extraction would charge.

The H050 Cell-I precedent ([memo_h050-cell-i-cost-estimate_2026-04-24.md](memo_h050-cell-i-cost-estimate_2026-04-24.md) §1.1) bound the `T_live` figure as "the only cost figure that authorizes paid pulls" — same convention here.

## 1. Scope per ADR-0023 §Decision 1 Tier-1

| Symbol | Description | CME multiplier | Tick value | Substrate dataset |
|---|---|---|---|---|
| CL | NYMEX WTI Light Sweet Crude | $1000/$ | 0.01 = $10 | GLBX.MDP3, schema `ohlcv-1m` |
| MCL | Micro WTI Crude | $100/$ | 0.01 = $1 | GLBX.MDP3, schema `ohlcv-1m` |
| GC | COMEX Gold | $100/oz | 0.10 = $10 | GLBX.MDP3, schema `ohlcv-1m` |
| MGC | Micro Gold | $10/oz | 0.10 = $1 | GLBX.MDP3, schema `ohlcv-1m` |

Window: **2015-01-01 → 2025-12-31** (matches the H060 design.md §2 calibration + IS + OOS envelope).

Symbology: **parent symbols** `CL.FUT`, `MCL.FUT`, `GC.FUT`, `MGC.FUT` (Databento smart-symbology resolves to all front-month contracts within the window). This matches the existing H050/H052a/etc. substrate convention (continuous front-month series).

## 2. Pre-flight check

- [ ] Operator has `DATABENTO_API_KEY` env var available (same key used for H050 Cell-I; sibling repo at `C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\config\api_keys.py`).
- [ ] Databento Python SDK installed in the venv being used to run the script (not in `pyproject.toml`; install on the fly per H050 Cell-I sibling-repo pattern):
      `uv pip install databento` OR `pip install databento`
- [ ] `logs/databento_cost_dossiers/` writable.

## 3. Run

From the repo root:

```powershell
# PowerShell
$env:DATABENTO_API_KEY = '<your-databento-api-key>'
uv run python scripts/databento_metals_energy_cost_dossier.py
```

```bash
# bash / WSL
export DATABENTO_API_KEY='<your-databento-api-key>'
uv run python scripts/databento_metals_energy_cost_dossier.py
```

If the Databento SDK is not in the project's venv yet:

```powershell
uv pip install databento
uv run python scripts/databento_metals_energy_cost_dossier.py
```

## 4. Expected output

Stdout: per-symbol cost table + total `T_live_total_usd` + budget-ceiling comparison vs $30 / $80 USD reference levels.

JSON dossier at `logs/databento_cost_dossiers/metals_energy_<UTC-timestamp>.json` with full request metadata, per-symbol cost breakdown, and a `T_live_total_usd` binding figure.

## 5. Authorization decision rule

Per ADR-0023 §Decision 6 + H050 Cell-I precedent:

| `T_live_total_usd` | Decision |
|---|---|
| ≤ $30 USD (tight budget; H050 Cell-I precedent ceiling) | Authorize `P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE`. Proceed directly to Stage A in the sibling repo. |
| $30 < `T_live` ≤ $80 USD (loose budget; ADR-0023 upper estimate) | Operator re-reviews ADR-0023 §Decision 6; may amend the ceiling with documented rationale before authorization. |
| > $80 USD | **Abort.** Re-scope to a narrower window (e.g., 2020-2025 only; drop calibration-holdout for v1; recover via H060 v2 if needed) and re-run this runbook. |

Authorization decision is logged as a new entry in `logs/promotions/` per the H052a 2026-05-05 operator-decline precedent ([logs/promotions/184eccd67bf24d71990265d39c28daf0_H052a_operator-decline-ninjascript.md](../../logs/promotions/184eccd67bf24d71990265d39c28daf0_H052a_operator-decline-ninjascript.md)).

## 6. After authorization (Stage A — paid Databento pull)

This runbook stops at the cost-dossier output. Stage A (actual paid extraction) is a separate follow-up:

- `P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE` — operator authorizes the spend.
- Stage A executes via the sibling-repo `databento_downloader.py` extended to accept CL/MCL/GC/MGC monthly-contract codes (`F, G, H, J, K, M, N, Q, U, V, X, Z`) vs the existing quarterly equity-index codes. The sibling repo's `download_historical_years` method may need extension to handle 12-month-tuple iteration; tracked under sibling-repo follow-up (not in this repo's scope).
- Stage B (SKIE-Universe local re-import + roll-adjust) follows the H050 Cell-I §2.3 pattern: `scripts/ingest.py --dataset vendor_legacy_1min ...` extended with the new CSV files; new `vendor_legacy_1min_monthly_roll_adjusted` derivative per `P1-MONTHLY-ROLL-MODULE-IMPL`.

## 7. Verification gap

Per the H050 Cell-I memo §1.5 verification gap (unit of `metadata.get_cost` return value not directly verified from primary Databento documentation), the script defensively interprets the return as USD per the sibling-repo `databento_downloader.py:41-60` docstring + calling-context `f'${cost:.4f}'` formatting at lines 391/467/484/504. **Operator should visually verify the printed `T_live_total_usd` looks like a USD figure (single-digit to low-double-digit dollars) before authorizing Stage A.**

If the figure looks anomalous (e.g., a thousands-USD value, or a fractional-cent value), pause and verify via the Databento account dashboard before proceeding.

## 8. Provenance

- Script: [scripts/databento_metals_energy_cost_dossier.py](../../scripts/databento_metals_energy_cost_dossier.py)
- Output dossier: `logs/databento_cost_dossiers/metals_energy_<UTC-timestamp>.json`
- Precedent: [runbook_h050-cell-i-databento-backfill_2026-04-24.md](runbook_h050-cell-i-databento-backfill_2026-04-24.md), [memo_h050-cell-i-cost-estimate_2026-04-24.md](memo_h050-cell-i-cost-estimate_2026-04-24.md)
- ADR: [ADR-0023](../decisions/ADR-0023-metals-energy-futures-substrate-expansion.md)
- Follow-up: `P1-DATABENTO-METALS-ENERGY-COST-DOSSIER` (this runbook; closed on first successful run)
- Successor: `P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE` (operator-action, post-dossier)
