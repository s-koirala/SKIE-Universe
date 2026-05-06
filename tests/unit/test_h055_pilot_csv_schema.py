"""H055 v1 pilot ledger CSV schema validation tests (stubs).

Pandera-polars schema-validation tests for the 171-trade reconciled v1
pilot ledger at
[data/external/h055_pilot_ledger/Performance.csv](../../data/external/h055_pilot_ledger/Performance.csv).
The tests are gated behind ``P1-H055-PILOT-CSV-SCHEMA-EXECUTE``; bodies
will be filled in by that follow-up's analysis-machine implementation.

The CSV is the authoritative substrate for both the H055 adherence audit
([scripts/run_h055_adherence_audit.py](../../scripts/run_h055_adherence_audit.py))
and the SPA power simulation
([scripts/run_h055_spa_power_simulation.py](../../scripts/run_h055_spa_power_simulation.py)),
so the schema contract is BLOCKING-BEFORE-ANY-DOWNSTREAM-EXECUTION.

Reconciliation totals
---------------------

- Total trades: 171
- Long trades (bought_timestamp < sold_timestamp partition): 94
- Short trades: 77
- Net pnl: ≈ $6,157.75 (reconciled to the published v1 pilot PDF totals)

All four facts above are captured as separate assertions below so a single
schema regression surfaces in the failing test that pinpoints the broken
invariant rather than a single conflated assertion.
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Pending implementation per follow-up P1-H055-PILOT-CSV-SCHEMA-EXECUTE")
def test_csv_loads_with_expected_columns() -> None:
    """Pandera-polars schema validates the CSV's column set.

    Asserts the loaded DataFrame contains at minimum the columns:
    ``symbol``, ``qty``, ``buyPrice``, ``sellPrice``, ``pnl``,
    ``boughtTimestamp``, ``soldTimestamp``, ``duration``. Additional
    columns are permitted (the pilot CSV exporter has historically emitted
    a superset including ``buyFillId`` + ``sellFillId``); the schema is
    declared as ``strict=False`` to allow that without breaking the load.
    """


@pytest.mark.skip(reason="Pending implementation per follow-up P1-H055-PILOT-CSV-SCHEMA-EXECUTE")
def test_pnl_reconciles_to_published_total() -> None:
    """Sum of cleaned pnl ≈ $6,157.75 (matches v1 pilot PDF total).

    Asserts ``abs(df['pnl'].sum() - 6157.75) < tolerance`` where the
    tolerance is sourced from the H055 yaml under a dedicated reconciliation
    key (TBD per follow-up ``P1-H055-PILOT-PNL-RECON-TOLERANCE``); pending
    that follow-up the test is skip-marked, so no magic-number tolerance is
    embedded in the test body.
    """


@pytest.mark.skip(reason="Pending implementation per follow-up P1-H055-PILOT-CSV-SCHEMA-EXECUTE")
def test_side_classification_94_long_77_short() -> None:
    """Long/short partition by buy/sell timestamp ordering matches expected counts.

    Asserts:
        sum(boughtTimestamp < soldTimestamp) == 94  # longs
        sum(boughtTimestamp > soldTimestamp) == 77  # shorts
        sum(boughtTimestamp == soldTimestamp) == 0  # no zero-duration ties

    The partition is the v1 pilot's side-classification convention; it is
    NOT a robust definition for production execution (a long with overnight
    add-on might violate it) but IS authoritative on the 171-trade pilot
    sample where every trade is intraday-flat.
    """


@pytest.mark.skip(reason="Pending implementation per follow-up P1-H055-PILOT-CSV-SCHEMA-EXECUTE")
def test_171_trades_no_duplicate_fill_ids() -> None:
    """Row count is 171 and (buyFillId, sellFillId) pairs are unique.

    Asserts:
        len(df) == 171
        df.select(['buyFillId', 'sellFillId']).unique().height == 171

    Duplicate fill-id pairs would indicate either (i) a CSV-export double-
    write bug in the pilot exporter or (ii) two distinct trades collapsed
    into a single row by a downstream cleaning script; both must surface
    here before any downstream H055 analysis script consumes the ledger.
    """
