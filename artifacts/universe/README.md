# artifacts/universe/

Append-only strategy-universe log for Hansen SPA bookkeeping. Every gate evaluation via [src/skie_ninja/inference/gate.py](../../src/skie_ninja/inference/gate.py) hashes the full universe-to-date into `universe_snapshot_id` per [implementation-plan §5 Universe snapshot](../../plan/buildouts/implementation-plan_2026-04-15.md).

## Files

- `universe_log.parquet` — append-only; columns per implementation-plan §5. Created on first gate evaluation (not committed to git until first non-empty write).
- `snapshots/{universe_snapshot_id}.json` — per-snapshot metadata (strategy IDs, timestamps, git HEAD) for audit traceability.

## Invariants

1. **Append-only.** Never rewrite history. Entries survive strategy archival (null results remain in the universe — removing them would cherry-pick the SPA family post-hoc).
2. **Hashed universe id.** `universe_snapshot_id = sha256(concat(sorted(strategy_ids_to_date)))`. Re-running a past gate with the same snapshot produces byte-identical SPA output.
3. **Versioned schema.** Schema change bumps a major version suffix on the parquet filename (`universe_log_v2.parquet`) and carries a migration note in [docs/audits/](../../docs/audits/).
