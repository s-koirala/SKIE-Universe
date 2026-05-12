"""Databento metals/energy cost dossier — `metadata.get_cost` call per ADR-0023.

Runs `db.Historical.metadata.get_cost(...)` for the H060 BLOCKING substrate:
CL (NYMEX WTI Crude), MCL (Micro WTI), GC (COMEX Gold), MGC (Micro Gold), all
front-month continuous via Databento parent-symbology, GLBX.MDP3 dataset,
ohlcv-1m schema, 2015-01-01 → 2025-12-31 window. NO PAID DATA IS PULLED;
`metadata.get_cost` is a $0 estimation call per Databento public docs at
[databento.com/docs/api-reference-historical/metadata/get-cost](https://databento.com/docs/api-reference-historical/metadata/get-cost)
(retrieved 2026-05-12).

Follows the H050 Cell-I precedent ([memo_h050-cell-i-cost-estimate_2026-04-24.md](../docs/research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md)
§1.1: "`client.metadata.get_cost(...)` (no charge) for the exact tuple. The
printed total is denoted `T_live` and is the **only** cost figure that
authorizes paid pulls.").

Workflow:
1. Set `DATABENTO_API_KEY` env var to your Databento account API key.
2. `uv run python scripts/databento_metals_energy_cost_dossier.py`
3. Inspect the printed `T_live_total_usd` and per-symbol breakdown.
4. If within the user-chosen budget ceiling (precedent H050 Cell-I: $30 USD;
   metals/energy estimate $30-80 per ADR-0023 §Decision 6), authorize the
   actual `timeseries.get_range` extraction call separately
   (`P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE`).

Output:
- JSON dossier at `logs/databento_cost_dossiers/metals_energy_<UTC-timestamp>.json`
  with per-symbol cost, total, request metadata, and a `T_live_total_usd`
  binding figure for §"Operator authorization" follow-up.
- Stdout: human-readable per-symbol table + total + budget-ceiling
  comparison vs $30 / $80 USD reference levels.

Provenance:
- ADR-0023 metals-energy futures substrate expansion (2026-05-12)
- `P1-DATABENTO-METALS-ENERGY-COST-DOSSIER` (operator-action, this script)
- Precedent: H050 Cell-I memo + runbook 2026-04-24

This script is a fail-closed read-only operation: it reports cost estimates
but does NOT pull any paid data. Operator authorizes paid extraction in a
separate, named follow-up after reviewing the cost output.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# --- Configuration: ADR-0023 §Decision 1 Tier-1 + sample window per H060 §2 ---

DATASET = "GLBX.MDP3"           # CME Globex (covers CME/NYMEX/COMEX)
SCHEMA = "ohlcv-1d"             # H060 §2 is daily-cadence by construction (MOP 2012
                                # monthly rebalance on daily closes); ohlcv-1d is the
                                # operationally correct schema. Initial dry run on
                                # 2026-05-12 with schema='ohlcv-1m' returned $313.88
                                # total -- substantially over both budget ceilings;
                                # re-quote at 'ohlcv-1d' returned $7.63 total. The
                                # ~40x cost reduction reflects the per-byte pricing
                                # convention (1-min has ~390 bars/session vs 1d's 1
                                # bar/session). For hypotheses that need intraday
                                # microstructure features (e.g., a future H060 v2
                                # with bar-cadence CL features), override to
                                # 'ohlcv-1m' or use a coarser intraday schema.
STYPE_IN = "parent"             # parent symbology resolves to front-month continuous
START = "2015-01-01"            # H060 §2 sample window (calibration + IS + OOS)
END = "2025-12-31"              # H060 §2 OOS right-edge upper bound

# Tier-1 target symbols per ADR-0023 §Decision 1
SYMBOLS = [
    {"symbol": "CL.FUT",  "description": "NYMEX WTI Light Sweet Crude (1000 bbl, $1000/$ multiplier, tick 0.01 = $10)"},
    {"symbol": "MCL.FUT", "description": "Micro WTI Crude (100 bbl, $100/$ multiplier, tick 0.01 = $1)"},
    {"symbol": "GC.FUT",  "description": "COMEX Gold (100 troy oz, $100/oz multiplier, tick 0.10 = $10)"},
    {"symbol": "MGC.FUT", "description": "Micro Gold (10 troy oz, $10/oz multiplier, tick 0.10 = $1)"},
]

# Budget reference levels per ADR-0023 §Decision 6
BUDGET_TIGHT_USD = 30.0   # H050 Cell-I precedent ceiling
BUDGET_LOOSE_USD = 80.0   # ADR-0023 upper-bound estimate

# --- Output path ---
OUTPUT_DIR_REL = Path("logs/databento_cost_dossiers")


@dataclass(frozen=True)
class PerSymbolCost:
    symbol: str
    description: str
    cost_usd: float
    request_dataset: str
    request_schema: str
    request_stype_in: str
    request_start: str
    request_end: str
    error: str | None = None


@dataclass
class CostDossier:
    timestamp_utc: str
    api_key_fingerprint: str  # last 4 chars + length; NOT the key itself
    dataset: str
    schema: str
    stype_in: str
    start: str
    end: str
    per_symbol: list[PerSymbolCost] = field(default_factory=list)
    t_live_total_usd: float = 0.0
    n_symbols_priced: int = 0
    n_symbols_errored: int = 0
    budget_tight_usd: float = BUDGET_TIGHT_USD
    budget_loose_usd: float = BUDGET_LOOSE_USD
    within_tight_budget: bool = False
    within_loose_budget: bool = False
    databento_sdk_version: str | None = None
    notes: list[str] = field(default_factory=list)


def _fingerprint_api_key(api_key: str) -> str:
    """Return defanged fingerprint for provenance logging.

    Per the 2026-05-12 operator-shared-key-in-chat-transcript incident (where the
    "DO NOT PUBLISH" directive was emphasized), this fingerprint suppresses even
    the last-4-chars + length to prevent any partial-key information from
    persisting to the JSON dossier on disk. Replace with the prior
    `f"len={len(api_key)},tail={api_key[-4:]}"` convention only if the dossier
    output path is hardened (e.g., chmod 600 + .gitignore'd directory).
    """
    if not api_key:
        return "<missing>"
    return "<suppressed-for-security>"


def main() -> int:
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        print(
            "[error] DATABENTO_API_KEY env var not set.\n"
            "Set it from your Databento account API key page and re-run, e.g.\n"
            "  $env:DATABENTO_API_KEY = '<your-key>'   # PowerShell\n"
            "  export DATABENTO_API_KEY='<your-key>'    # bash\n",
            file=sys.stderr,
        )
        return 2

    try:
        import databento as db  # noqa: PLC0415 (intentional late import)
    except ImportError:
        print(
            "[error] databento Python SDK not installed.\n"
            "Install with: `uv pip install databento` or `pip install databento`.\n"
            "Project does not pin this dependency in pyproject (sibling-repo pattern per H050 Cell-I).\n",
            file=sys.stderr,
        )
        return 3

    sdk_version = getattr(db, "__version__", "unknown")
    print(f"[info] databento SDK version: {sdk_version}")
    print(f"[info] dataset={DATASET}, schema={SCHEMA}, stype_in={STYPE_IN}")
    print(f"[info] window: {START} -> {END}")
    print(f"[info] symbols: {[s['symbol'] for s in SYMBOLS]}")
    print()

    client = db.Historical(key=api_key)

    dossier = CostDossier(
        timestamp_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        api_key_fingerprint=_fingerprint_api_key(api_key),
        dataset=DATASET,
        schema=SCHEMA,
        stype_in=STYPE_IN,
        start=START,
        end=END,
        databento_sdk_version=sdk_version,
    )

    print(f"{'symbol':<10} {'cost_usd':>12} {'description':<70}")
    print("-" * 95)

    for spec in SYMBOLS:
        symbol = spec["symbol"]
        description = spec["description"]
        try:
            cost = client.metadata.get_cost(
                dataset=DATASET,
                symbols=[symbol],
                stype_in=STYPE_IN,
                schema=SCHEMA,
                start=START,
                end=END,
            )
            # Databento SDK returns cost as float in USD per
            # the H050 Cell-I memo §1.5 docstring + calling-context convention.
            cost_usd = float(cost)
            dossier.per_symbol.append(
                PerSymbolCost(
                    symbol=symbol,
                    description=description,
                    cost_usd=cost_usd,
                    request_dataset=DATASET,
                    request_schema=SCHEMA,
                    request_stype_in=STYPE_IN,
                    request_start=START,
                    request_end=END,
                )
            )
            dossier.t_live_total_usd += cost_usd
            dossier.n_symbols_priced += 1
            print(f"{symbol:<10} ${cost_usd:>11.4f}  {description}")
        except Exception as e:  # noqa: BLE001 (capture all to dossier)
            err_str = f"{type(e).__name__}: {e}"
            dossier.per_symbol.append(
                PerSymbolCost(
                    symbol=symbol,
                    description=description,
                    cost_usd=float("nan"),
                    request_dataset=DATASET,
                    request_schema=SCHEMA,
                    request_stype_in=STYPE_IN,
                    request_start=START,
                    request_end=END,
                    error=err_str,
                )
            )
            dossier.n_symbols_errored += 1
            print(f"{symbol:<10} {'<ERROR>':>12}  {description}  // {err_str}")

    dossier.within_tight_budget = dossier.t_live_total_usd <= BUDGET_TIGHT_USD
    dossier.within_loose_budget = dossier.t_live_total_usd <= BUDGET_LOOSE_USD

    if dossier.n_symbols_errored:
        dossier.notes.append(
            f"{dossier.n_symbols_errored} of {len(SYMBOLS)} symbols errored — "
            "see per_symbol[*].error; total is sum of successful symbols only."
        )

    print("-" * 95)
    print(f"{'TOTAL':<10} ${dossier.t_live_total_usd:>11.4f}  (T_live binding figure per ADR-0023 §Decision 6)")
    print()
    print("Budget check:")
    print(f"  $30 tight  (H050 Cell-I precedent ceiling): {'WITHIN' if dossier.within_tight_budget else 'OVER'}")
    print(f"  $80 loose  (ADR-0023 §Decision 6 upper estimate): {'WITHIN' if dossier.within_loose_budget else 'OVER'}")
    print()

    # --- Persist dossier ---
    timestamp_for_filename = dossier.timestamp_utc.replace(":", "").replace("-", "").replace(".", "")[:15]
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / OUTPUT_DIR_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"metals_energy_{timestamp_for_filename}.json"

    # Manual dataclass serialization (frozen + list-of-dataclass)
    dossier_dict = {
        "timestamp_utc": dossier.timestamp_utc,
        "api_key_fingerprint": dossier.api_key_fingerprint,
        "dataset": dossier.dataset,
        "schema": dossier.schema,
        "stype_in": dossier.stype_in,
        "start": dossier.start,
        "end": dossier.end,
        "per_symbol": [
            {
                "symbol": p.symbol,
                "description": p.description,
                "cost_usd": p.cost_usd if p.cost_usd == p.cost_usd else None,  # NaN -> None
                "request_dataset": p.request_dataset,
                "request_schema": p.request_schema,
                "request_stype_in": p.request_stype_in,
                "request_start": p.request_start,
                "request_end": p.request_end,
                "error": p.error,
            }
            for p in dossier.per_symbol
        ],
        "t_live_total_usd": dossier.t_live_total_usd,
        "n_symbols_priced": dossier.n_symbols_priced,
        "n_symbols_errored": dossier.n_symbols_errored,
        "budget_tight_usd": dossier.budget_tight_usd,
        "budget_loose_usd": dossier.budget_loose_usd,
        "within_tight_budget": dossier.within_tight_budget,
        "within_loose_budget": dossier.within_loose_budget,
        "databento_sdk_version": dossier.databento_sdk_version,
        "notes": dossier.notes,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(dossier_dict, f, indent=2)

    print(f"[info] dossier written to: {out_path}")
    print()
    print("Next-step decision (operator):")
    print("  - If WITHIN tight ($30) budget: authorize P1-DATABENTO-METALS-ENERGY-EXTRACTION-AUTHORIZE")
    print("    and proceed with the sibling-repo download_historical_years call for CL/MCL/GC/MGC.")
    print("  - If WITHIN loose ($80) budget but OVER tight: re-review ADR-0023 §Decision 6 budget ceiling;")
    print("    operator may amend the ceiling with documented rationale before authorization.")
    print("  - If OVER loose: abort; re-scope to a narrower window (e.g., 2020-2025 only) and re-run.")

    return 0 if dossier.n_symbols_errored == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
