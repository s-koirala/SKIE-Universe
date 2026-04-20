# Data requirements — {HID}

Frozen at pre-registration time. Checksums pasted below are the commitment; the
walk-forward runner (plan §4.2) verifies each dataset hash against these values before
fitting any fold and aborts on mismatch. Update only by creating a new hypothesis ID.

## Datasets

List every dataset under [data/processed/](../../../data/processed/) that this hypothesis
consumes. Use the canonical partitioned path documented in plan §2.2.

| Dataset | Processed path | Vendor | Snapshot date | License / volume tier | SHA256 (frozen) |
|---|---|---|---|---|---|
|   |   |   |   |   |   |

## External joins

Auxiliary tables joined into the panel (e.g., macro-surprise, FOMC text embeddings,
0DTE dealer-GEX snapshots). Each has its own provenance file under
`data/processed/_provenance/` per plan §2.1.

| Join source | Provenance file | Snapshot date | SHA256 |
|---|---|---|---|
|   |   |   |   |

## Volume-tier and licensing notes

CME volume-tier fee schedule and per-vendor redistribution constraints. Audit item M-15
requires documenting the tier even when immaterial at retail size.

- CME fee tier assumed:
- Vendor redistribution constraint (store derived features only? no raw redistribution?):
- Licensed downstream use (backtest only | paper-trade | live):

## Point-in-time verification

Every feature consuming these datasets must pass the PIT property test in plan §3.
Record here any dataset-specific PIT subtlety (e.g., macro-surprise `release_ts_utc` is
embargoed; FOMC text has `embargo_ts_utc` distinct from `release_ts_utc`).

- PIT notes:

## Reproducibility commitment

The SHA256 column above is the commitment. Any change to processed-dataset bytes
invalidates this hypothesis and requires a new hypothesis ID rather than a silent rehash.
