# Audit trail — `vendor_legacy_1min` ingest delivery (2026-04-23)

## Context

Follow-ups #1 (ingest module), #2 (NQ provisioning), and #3 (raw 1-min import) from [audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md](audit_trail_2026-04-20_vendor-skie-ninja-legacy-import.md) executed in one coordinated delivery. Databento license status flipped to `verified` by user confirmation 2026-04-23. Sibling SKIE_Ninja research repo holds the Databento account; scout agents located 9 canonical raw 1-min CSVs (ES 2020-2025, NQ 2020-2024) totaling ~152 MB.

## Deliverable

A new `IngestJob` adapter that imports these CSVs into SKIE-Universe's shared-data and processed tree, SHA256-idempotently, with evidence-bar-eligible provenance.

| Surface | Change |
|---|---|
| [src/skie_ninja/data/ingest/vendor_legacy_1min.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) | New `VendorLegacy1minIngestJob` implementing the [`IngestJob`](../../src/skie_ninja/data/ingest/_registry.py) protocol: `fetch` (copy w/ SHA256 idempotency), `parse` (CSV → polars LazyFrame, UTC tz-aware, normalized `contract_symbol` + root `symbol`), `validate` (schema + OHLC consistency), `write_processed` (partitioned parquet, two-phase commit), `emit_provenance` (wires `ctx.add_dataset_checksum` — closes the prior follow-up on empty ReproLog checksums). Self-registers at import time. |
| [src/skie_ninja/data/validation/schema.py](../../src/skie_ninja/data/validation/schema.py) | New `VendorLegacy1minSchema` with tz=UTC ts_event, OHLC > 0, volume ≥ 0, unique `(contract_symbol, ts_event)`, root `symbol ∈ {ES, NQ}`. |
| [scripts/ingest.py](../../scripts/ingest.py) | `_DATASET_CHOICES`, `_module_map`, and `_SCHEMA_MAP` extended with `vendor_legacy_1min` so the CLI routes to the new adapter. |
| [tests/unit/test_vendor_legacy_1min.py](../../tests/unit/test_vendor_legacy_1min.py) | 14 unit tests: fetch (canonical-source copy, SHA256 idempotency, missing-source tolerance), parse (UTC tz enforcement, empty-frame contract, multi-file concat, contract-symbol normalization), validate (valid pass, duplicate reject, OHLC violation reject, non-UTC reject, unknown-symbol reject), write_processed + emit_provenance (partition layout, dataset_checksums side-effect, `tier: raw` + `evidence_bar_eligible: true`). |
| [config/data_sources.yaml](../../config/data_sources.yaml) | New `vendor_legacy_1min` entry with `tier: raw`, `evidence_bar_eligible: true`, ingest-module path + provenance-file pattern. |
| [README.md](../../README.md), [CLAUDE.md](../../CLAUDE.md), H050/H051/H052 README data-readiness blocks | Status updated to reflect the new evidence-bar-tier substrate; NQ gap closed for H050/H052, H051 unblocked at minute-bar resolution. |

## Run outcome (2026-04-23 17:29 CT)

```
Fetch summary: 9 copied, 0 unchanged, 9 total canonical sources   (first run)
Fetch summary: 0 copied, 9 unchanged, 9 total canonical sources   (idempotent re-run)
Schema + OHLC validation passed (rows=3,733,906, symbols=['ES', 'NQ'])
Wrote 11 partitions to data/processed/vendor_legacy_1min
Post-write schema validation passed.
Wrote provenance: data/processed/_provenance/vendor_legacy_1min_20260423.json
Ingest complete: vendor_legacy_1min.
```

Partition layout on disk:
```
data/processed/vendor_legacy_1min/
├── symbol=ES/year={2020,2021,2022,2023,2024,2025}/part-0000.parquet   (6 partitions)
└── symbol=NQ/year={2020,2021,2022,2023,2024}/part-0000.parquet         (5 partitions)
```

Raw cache:
```
C:\Users\skoir\datasets\vendor_skie_ninja_legacy\raw_1min\
├── ES_{2020,2021,2022,2025}_1min_databento.csv + ES_1min_databento.csv  (5 files, IS + OOS + forward)
└── NQ_{2020,2021,2022}_1min_databento.csv + NQ_1min_databento.csv       (4 files, IS + OOS)
```

## Round-1 defect caught and fixed inline

**Defect.** First ingest attempt failed post-fetch validation: `symbol` column contained contract-month codes like `ESH0` (ES March 2020), not just root `ES`. My schema had `isin=["ES", "NQ"]` — the assumption the sibling's processed parquet (normalized root symbol) held for raw Databento too.

**Root cause.** Databento's `ohlcv-1m` schema emits contract-specific symbols per its [Symbology reference](https://databento.com/docs/standards-and-conventions/symbology). Raw CSV rows carry `ESH0`, `ESM3`, `NQU4`, etc. — one row per front-month trading minute. The 5-min features parquet I imported 2026-04-20 had already been normalized by the sibling's pipeline, which is why that case worked.

**Fix.** In `parse()`:
- Preserve the raw `symbol` column as `contract_symbol` (e.g., `ESH0`)
- Derive a normalized `symbol` via `str.slice(0, 2)` → root (`ES`, `NQ`)

Schema updated to require both columns; unique key switched from `(symbol, ts_event)` to `(contract_symbol, ts_event)` because during roll windows the same UTC minute *can* legitimately appear under two adjacent contracts for the same root. The root-symbol constraint `isin=["ES", "NQ"]` then passes. Downstream code that filters on root symbol still works; contract code available for roll-aware logic if ever needed.

Unit-test fixtures updated to emit `ESH4` / `NQH4` in synthetic CSVs, plus new `test_parse_extracts_root_from_contract_symbol` asserting the transformation.

## Evidence hierarchy + method validation

Per [~/.claude/CLAUDE.md](~/.claude/CLAUDE.md) §Evidence Hierarchy and §Verification:

- **Official documentation (tier 2).** Databento schema: https://databento.com/docs/schemas-and-data-formats/ohlcv. Symbology: https://databento.com/docs/standards-and-conventions/symbology. `rtype=34` = OHLCV-1m (verified in the data).
- **Standards.** Polars UTC-tz-aware `Datetime("us", "UTC")` semantic — enforced end-to-end from parse through parquet round-trip (pandera strict `time_zone` check).
- **Reproduce — no paraphrasing.** The sibling's `enhanced_feature_pipeline.py` is NOT reused; we import only the raw 1-min CSVs and let each hypothesis derive its own features in-project, consistent with the prior round-4 audit outcome on the 5-min features parquet.

## Reproducibility closure

Item from prior audit: *"`ReproLog.dataset_checksums` empty — raw SHAs live only in parallel provenance JSON."* Closed. `emit_provenance` now calls `ctx.add_dataset_checksum(rp.name, file_sha256(rp))` for every source file, so the ReproLog JSON at `logs/reproducibility/{run_id}.json` carries the canonical hashes directly.

## Residual follow-ups

1. **NQ 2025 not yet pulled** in sibling repo. When it lands, append a `_SourceFile("NQ", "forward_2025", "NQ_2025_1min_databento.csv")` to `_CANONICAL_SOURCES` and re-run — SHA256 idempotency will skip the 9 existing files.
2. **Data-quality smoke test on 1-min parquets** (distinct from schema test): a skip-if-missing integration test asserting row count per year/symbol matches the known Databento ranges per [CANONICAL_REFERENCE.md](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/config/CANONICAL_REFERENCE.md) ±1% tolerance. Opened.
3. **Roll-aware continuous series** (H050/H051 will need it): decide on roll rule (calendar-based open-interest vs ratio-adjusted back-adjustment) and implement as a feature-engineering step — NOT an ingest concern. Opened, scoped to hypothesis-specific work.
4. **Tick-resolution data** (H051 queue-position work): still gated on direct Databento tick subscription — no sibling inheritance possible since sibling is 1-min only.

## Audit-remediate-loop status

Round-1 audit is the module design/implementation review; the contract-symbol defect was caught by the live ingest itself (the equivalent of a synthetic check), fixed, and re-verified.

## Round 2 — external quant-auditor response (2026-04-23)

Auditor returned `proceed-with-remediation` with 5 Major and 8 Minor findings, no Critical. All Major + the Ruff-hygiene Minor closed inline in this commit. Deferred Minors are tracked at the end of this section.

| Finding | Severity | Disposition |
|---|---|---|
| F-2-1: `str.slice(0, 2)` corrupts MES/MNQ roots | Major | **Closed.** `parse()` now uses an explicit `pl.when(starts_with(MES/MNQ/ES/NQ))` mapping; schema `isin` extended to `{"ES","NQ","MES","MNQ"}`. Even though current sources are ES/NQ-only, the code is correct under the documented universe. |
| F-2-2: no monotonicity constraint | Major | **Closed.** `validate()` now also asserts `ts_event` is strictly increasing within each `contract_symbol`. `parse()` sorts by `(contract_symbol, ts_event)` post-concat so the invariant holds by construction, not by file-ordering luck. Integration test `test_ts_event_monotonic_per_contract_symbol` enforces across all real partitions. |
| F-2-3: raw tier marked `evidence_bar_eligible: true` without roll adjustment | Major | **Closed.** Demoted to `evidence_bar_eligible: false` in both the emitted provenance and [config/data_sources.yaml](../../config/data_sources.yaml). New provenance field `roll_adjustment: "none (front-month concatenation only)"`. H050/H051 READMEs updated with the evidence-bar constraint. Unit + integration tests updated to lock the constraint. Rationale: the futures analog of the rules/quant-project.md §Time-series integrity corporate-action adjustment is contract-roll adjustment; without it, returns across a roll boundary are uncompensated. |
| F-2-4: OHLC check was tautologically weaker than docstring | Major | **Closed.** Replaced with direct-form filter checking every invariant explicitly (`low > open` \| `low > close` \| `low > high` \| `high < open` \| `high < close`). |
| F-2-5: `contextlib.suppress(AttributeError)` swallows wrong exception | Major | **Closed.** Replaced with `hasattr(ctx, "add_dataset_checksum")` duck-type check. A real unentered `RunContext` now surfaces the `RuntimeError` loudly instead of silently dropping checksums. |
| F-2-7: no integration test on real partitioned parquets | Minor | **Closed.** New [tests/integration/test_vendor_legacy_1min_parquets.py](../../tests/integration/test_vendor_legacy_1min_parquets.py) — 4 tests: partition structure, per-partition schema + row-count range [300k, 400k], ts_event monotonicity across all real partitions, provenance evidence_bar gate. |
| F-2-9: ruff hygiene (PLC0415 local imports, B017 bare Exception, PLW2901 loop var shadow, I001 import sort) | Minor | **Closed.** Schema import hoisted to module top; `Exception` narrowed to `pandera.errors.SchemaError`; `part` renamed to `part_df`/`part_out`; `logging` hoisted to module-top; magic numbers replaced with arithmetic expressions or `# noqa: PLR2004` with justification. `uv run ruff check` is clean on the touched files. |
| F-2-12: NQ 2025 gap mirrored to H052 README | Minor | **Closed.** H050/H051/H052 READMEs explicitly state "NQ 2025 pending sibling pull" in the data-readiness block. |
| F-2-6: `shutil.copy2` + per-file rename is not set-atomic on Windows | Minor | **Deferred.** Current behavior is idempotent-recoverable by construction (re-run heals partial state via SHA256 check). True set-atomicity on NTFS is not readily achievable; docstring to be updated in a follow-up to say "per-file atomic rename with staged validation" rather than "two-phase commit." |
| F-2-8: `ks_min_n = 2` magic number in scripts/ingest.py | Minor | **Deferred.** Pre-dates this delivery; the constant is an operability floor for `scipy.stats.ks_2samp`, not a power threshold. Opened as a rename-and-cite follow-up on the shared ingest.py, not blocking. |
| F-2-10: `_rmtree_empty` has no transactional envelope | Minor | **Deferred, reduced.** Per-file `os.replace` is idempotent; documented under F-2-6. |
| F-2-11: `runtime_checkable` Protocol only checks attribute presence, not signatures | Minor | **Deferred.** Cross-cutting concern across all ingest jobs; not specific to this delivery. Opened as a test-harness follow-up: add `inspect.signature` equality check in `_registry.register()` or a registry-level test. |
| F-2-13: license_status sourced from sibling-repo provenance, not a Databento-direct artifact | Minor | **Deferred — user action already recorded.** User confirmed license verification on 2026-04-23 (logged in `~/datasets/vendor_skie_ninja_legacy/es_5min_features_2020_2025.provenance.json`). Attaching a Databento-direct invoice/license PDF hash is a hardening step; opened but not blocking. |

## Primary-source citations (round-2 additions)

- **FRED / Databento Symbology** — https://databento.com/docs/standards-and-conventions/symbology (contract-symbol structure; root-symbol conventions for minis vs micros).
- **Databento OHLCV schema** — https://databento.com/docs/schemas-and-data-formats/ohlcv (`rtype=34` = ohlcv-1m).
- **Polars Datetime dtype** — https://docs.pola.rs/user-guide/transformations/time-series/timezones/ (UTC-tz-aware contract).
- **rules/quant-project.md §Time-series integrity** — corporate-action adjustment requirement (futures-analog is contract-roll adjustment, invoked to justify F-2-3).
- **Massey 1951, JASA 46(253):68** — KS two-sample operability referenced in deferred F-2-8.

## Residual follow-ups (after Round 2)

1. **Roll-adjustment derivative pipeline** (new priority-1 follow-up). Implement a calendar-based or open-interest-based roll rule producing `data/processed/vendor_legacy_1min_roll_adjusted/symbol={ES,NQ}/part-0000.parquet`. This is the evidence-bar-eligible surface; raw tier feeds it.
2. **NQ 2025 pull** (from Round 1, unchanged). Sibling repo extension.
3. **Data-quality smoke test sharpening** — the current `[300k, 400k]` range is generous; tighten per-year per-symbol once a second run establishes a baseline ± tolerance.
4. **F-2-6 docstring tightening + F-2-8 constant rename + F-2-11 registry signature check + F-2-13 license artifact** — collect into a cross-cutting ingest-hygiene commit (out of scope here).
