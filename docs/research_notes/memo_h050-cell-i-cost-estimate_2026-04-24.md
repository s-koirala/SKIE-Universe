---
name: H050 Cell I — cost, time, and risk estimate
description: Empirically-anchored cost / wall-clock / storage estimate for the H050 Cell I Databento backfill, with risk assessment. Companion to runbook_h050-cell-i-databento-backfill_2026-04-24.md.
type: project
status: estimate, pending Stage A `metadata.get_cost` confirmation
created: 2026-04-24
hypothesis_id: H050
follow_up_id: P1-H050-DATA-COVERAGE
audience: skoir
---

# Memo — H050 Cell I cost, time, and risk estimate

## 0. Purpose

Provide the user a Round-1 estimate of (i) USD cost, (ii) wall-clock time, (iii) storage footprint, and (iv) operational risks for the Cell I backfill before they authorize the paid Databento API call. The binding cost figure is whatever `client.metadata.get_cost(...)` returns at runtime; this memo's role is to (a) anchor the order of magnitude empirically so the user has a sanity ceiling, and (b) enumerate risks the run script may not surface on its own.

## 1. USD cost

### 1.1 Binding rule — the live `metadata.get_cost` call is the only authorization-binding figure

The runbook §6.1 invokes `client.metadata.get_cost(...)` (no charge) for the exact `(dataset, symbols, schema, start, end)` Cell-I tuple. The printed total is denoted `T_live` and is the **only** cost figure that authorizes §6.2 paid pulls. All other numbers in this memo are *order-of-magnitude indicators*, not binding predictions.

Cell I scope: ES 2015-2019 (5 yrs) + NQ 2015-2019 (5 yrs) + NQ 2025 (1 yr) = **11 symbol-years**.

### 1.2 Indicative anchor — NOT a billing record, NOT binding

The sibling-repo `databento_downloader.py` line 363 carries `already_spent: float = 3.17` — a **hard-coded function default** in [estimate_all_costs()](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/src/python/data_collection/databento_downloader.py), not a billing record fetched from the Databento account dashboard. The author's recorded prior expense for "2023-2024 ES+NQ 1-min OHLCV pull" is documented at this default but should be treated as a **soft anchor** ("the order of magnitude was a few dollars"), not as a per-symbol-year unit cost suitable for linear extrapolation.

The previously-published $8.71 "linear extrapolation to 11 symbol-years" is removed from this memo as binding; it is mentioned here only to record the prior estimate that the audit demoted. The `T_live` figure from §6.1 supersedes it on the day of the run.

### 1.3 Pricing unit (Databento public docs)

Per [databento.com/pricing](https://databento.com/pricing) (fetched 2026-04-24 via WebFetch): "billed for every outbound byte of data at the moment it is sent out on our network." Pricing is per-GB of uncompressed binary, **not** per-row, per-symbol, or per-month.

Tier list:
- Pay-as-you-go: no subscription
- Standard: $199/month
- Plus: $1,399/month (annual contract)
- Unlimited: $3,500/month (annual contract)

Per-GB rates are not published on the public pricing page; the user's account dashboard reports the per-tuple cost via `metadata.get_cost`.

### 1.4 Authorization ceiling (user-chosen budget)

| Element | Value | Rationale |
|---|---|---|
| User-chosen budget ceiling | **$30 USD** | A user-set cap, not a vendor-derived multiple. The operational interpretation: **abort if `T_live > $30 USD`** (the §6.1 live-API figure). |
| Recommended floor for §6.2 authorization | `2 × T_live` | Absorbs vendor revisions or rounding between the cost-estimate call (§6.1) and the actual download (§6.2). For example, if `T_live = $8`, the user authorizes spending up to $16; the §6.2 call is then bound by this `2 × T_live` floor, not by the $30 ceiling. |

The previously-published "$8-12 mid", "$6 low", "$15 high" estimate band is removed — those numbers were extrapolated from the indicative-not-binding $3.17 anchor and added pseudo-precision. Substitute: any single cost claim the user makes about Cell I before §6.1 runs should be qualified "order of magnitude $5-30, exact = `T_live` from §6.1."

### 1.5 Verification gap

The unit of `metadata.get_cost`'s return value (USD vs. cents vs. uncompressed-GB-equivalent) was not directly verified from primary Databento documentation in this session. WebFetch returned navigation-only content for [databento.com/docs/api-reference-historical/metadata/get-cost](https://databento.com/docs/api-reference-historical/metadata/get-cost) on 2026-04-24 and 2026-04-25. The "USD" interpretation is anchored to the sibling-repo `databento_downloader.py:41-60` docstring `"""Get cost estimate for download."""` and the calling-context formatting `f'${cost:.4f}'` at lines 391, 467, 484, 504, etc., consistent with USD. **User should visually verify the printed `T_live` in §6.1 looks like a USD figure before authorizing §6.2.**

The follow-up `P1-H050-CELL-I-LIVE-COST-CAPTURE` tracks recording `T_live` as the binding cost record after Stage A.

## 2. Wall-clock estimate

### 2.1 Stage A (paid Databento pull, sibling repo)

Anchored to the prior 2026-04-23 vendor_legacy_1min ingest audit trail ([docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](../audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md)) reporting the full ES+NQ 2020-2024 import in "one session, hours not days." That ingest covered 3.73M rows; Cell I covers ~3.77M rows — comparable.

The Stage A pull itself is **API-bandwidth bound, not CPU-bound**. Databento's bulk historical interface returns multi-MB chunks; the sibling downloader's `download_historical_years` makes 4 calls/year (one per H/M/U/Z contract). For 11 symbol-years × 4 contracts = 44 API calls.

Practical estimate: **15-45 minutes** at typical residential broadband (50-200 Mbps), assuming no rate-limit throttling. The downloader serializes calls; no parallelism is exploited.

### 2.2 Stage B (SKIE-Universe local re-import + roll-adjust)

Per the same prior audit, the existing `vendor_legacy_1min` ingest of 3.73M rows (CSV → polars → partitioned parquet → schema validate → provenance) ran in **single-session minutes** end-to-end. With 290 MB CSV → ~150 MB parquet, the polars pipeline is I/O-dominant. Estimate: **5-15 minutes**.

The `vendor_legacy_1min_roll_adjusted` derivative re-derives all roll events across all years; it walks the full combined frame. Given the existing pipeline ran the 2020-2025 derivative in single-session minutes, the 2015-2025 derivative is estimated at **10-25 minutes** (≈ 2× rows; rolls are O(n) per session date).

### 2.3 Verification (Stage B post-run)

The verification queries in runbook §8 are sub-minute each; total verification overhead is **< 5 minutes**.

### 2.4 Total

**~30-90 minutes** end-to-end, of which Stage A is the dominant block. Aborts and re-runs on individual symbol-year files (idempotent at SHA256 level, no double-billing) extend wall-clock without additional cost.

## 3. Storage estimate

Recomputed using the empirical per-year row baseline (ES≈340k, NQ≈340k) verified at runbook §1 against existing 2020-2024 substrate. Total new rows: 5 ES + 5 NQ + 1 NQ-2025 ≈ `5 × 340k + 5 × 340k + 360k ≈ 3.74M` (previously published `3.77M` is superseded by the empirical anchor). Bytes derived from the existing `~26 MB / 340k rows` ratio observed in the raw_1min directory listing.

| Surface | Bytes | Path |
|---|---|---|
| Stage A new CSVs (sibling repo raw) | ~290 MB | `C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\data\raw\market\` (11 new files; ~26 MB ES-yr, ~26 MB NQ-yr, ~27 MB NQ-2025) |
| Stage B SKIE-Universe shared raw cache | ~290 MB | `C:\Users\skoir\datasets\vendor_skie_ninja_legacy\raw_1min\` (11 new copies) |
| Stage B `vendor_legacy_1min` parquet (delta) | ~75 MB | `data/processed/vendor_legacy_1min/symbol={ES,NQ}/year={2015..2019,NQ-only-2025}/` (11 new partitions; parquet ≈ 0.5 × CSV after compression) |
| Stage B `vendor_legacy_1min_roll_adjusted` parquet (full re-derivation) | ~150 MB | `data/processed/vendor_legacy_1min_roll_adjusted/` (re-writes all 22 partitions; the prior 11 partitions for 2020-2024 also change due to full-sample rescaling per [vendor_legacy_1min_roll_adjusted.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) docstring §"Point-in-time caveat") |
| **Net new Stage B storage** | **~225 MB** | (existing parquet is overwritten in place; net delta is the new partitions plus the size delta of re-derived old partitions, which is approximately zero per partition) |
| Provenance JSON | < 1 MB | `data/processed/_provenance/` |
| **Cumulative Cell-I storage commitment** | **~575 MB** across both repos | |

C: drive available 396 GB (per `df -h` 2026-04-24). Storage is non-binding.

## 4. Risk assessment

### 4.1 Vendor risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Pricing different from $3.17→$8.71 extrapolation | Medium | Low (ceiling absorbs 3.3× overrun) | `metadata.get_cost` pre-call in runbook §6.1 |
| Pre-2017 reconstruction-feed quality differs from native MDP 3.0 | High | Medium (affects HMM emission moments on early train fold) | Provenance flag (residual-risk item 3 of runbook); H050 §10 line 105 stationarity pre-check is the binding gate |
| NQ 2025 vendor coverage cutoff earlier than expected | Medium | Low (test-window NQ partial-year is acceptable per design.md §2 if both ES+NQ truncated symmetrically) | Stage A row-count check after pull; if NQ 2025 rows ≪ ES 2025 rows, document and proceed |
| Vendor revisions to historical bars between 2020-2024 (already-ingested) and now | Low | High (would invalidate existing combined SHA `d2c4aa4e70c6badcb294d9bec64ee3fc5093ba9085082495f5031743943b9a2d`) | Re-running roll-adjusted with `--force` after Cell I changes the SHA regardless; if vendor revisions are present, both old and new SHAs are different from the pre-Cell-I, but the full-sample-rescaling property already requires SHA invalidation, so this risk is *absorbed* into the expected cutover. |
| Quota / rate-limit throttling | Low | Low (extends wall-clock; no double-billing) | Sibling downloader retries silently per `databento` SDK defaults |

### 4.2 Calendar-edge risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| NYSE / CME holiday count differences between years (2015-2019 vs 2020-2024) | Certain | None | Holiday calendar is intrinsic to the Databento data; row counts vary year-to-year by ~1-2% which is below the ±5% sanity gate in runbook §8.2 |
| Half-day session boundaries (Thanksgiving Friday, Christmas Eve, etc.) | Certain | None | Already handled correctly in [src/skie_ninja/utils/clock.py](../../src/skie_ninja/utils/clock.py) |
| Daylight Saving Time transition bars | Certain | None | UTC `ts_event` from Databento; `clock.py` is DST-correct |
| 2018 February VIX-event volatility outliers | High in data, none in pipeline | None operationally; **methodologically high** for HMM emission | This is precisely what motivates the train-window expansion: the HMM should see this regime. Not a risk; a benefit. |
| Long-Term Capital-style 2015-08 China-devaluation flash crash | Same as above | Same | Same |

### 4.3 Pipeline risks (Stage B)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Parse failure on a backfilled CSV (schema drift) | Low | Medium (partial state) | Two-phase commit; runbook §10 rollback |
| Roll-event boundary at end of 2019 doesn't link cleanly with start of 2020 | Medium | High (chain-continuity assertion fails per [vendor_legacy_1min_roll_adjusted.py:1058-1067](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py)) | Roll-adjusted ingest will raise `ValueError` if discontinuous; user repairs source coverage per `vendor_legacy_1min_roll_adjusted.py` §"Operational runbook for data gaps" |
| MES/MNQ contracts in pre-2019 data confuse contract-symbol parsing | Low (sibling downloader requests only ES, NQ — not MES, MNQ) | Low | Schema validation gate at parse() |
| Ratio-anchor `NoOverlapError` because old-contract last-as-front bar is missing | Medium for early-history rolls | High (partial run failure) | Repaired per same operational runbook; can fall back to CME settlement substitution (opt-in, must be recorded in `ratio_anchor_override` provenance field) |
| Worktree-local `data/processed/vendor_legacy_1min/` absent (per dry-run §A.2) | Confirmed | Low | Stage B step §7.2 re-materializes; idempotent |

### 4.4 Cross-stage risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| User authorizes Stage A but does not run Stage B before next H050 evidence-bar attempt | Medium | High (data_requirements.md still references pre-Cell-I checksums; SPA family entries would be inconsistent) | Single-commit Stage B per runbook §11 binds the substrate transition atomically |
| Sibling-repo source-CSV path changes between Stage A and Stage B | Low | High (Stage B fails at fetch with FileNotFoundError) | `_DEFAULT_SOURCE_ROOT` in [vendor_legacy_1min.py:48-51](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) is hard-coded; if the sibling repo moves, override via constructor — not a CLI-level concern, but a code-edit |
| H050 pre-reg companion `aggregation_rule_addendum_2026-04-24.md` not yet created (per CLAUDE.md aggregation-rule resolution memo §6) | Confirmed | Blocking | Cell I backfill is data-readiness; the aggregation addendum is design-readiness. Both must be in place before the H050 evidence-bar walk-forward run, but they are independent. |

### 4.5 Authorization-discipline risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Producer agent runs paid call without user authorization | None for this agent (constraint-bound) | N/A | Producer agent terminates at runbook-write; user invokes Stage A explicitly |
| Cost-ceiling-exceeded scenario triggers automatic abort (no charge yet at §6.1) | n/a | n/a | `metadata.get_cost` does not bill |
| User authorizes a partial subset (e.g., NQ 2025 only) and the runbook short-circuits cleanly | Low | None | Stage A pulls are independent per symbol-year; pulling a subset is well-defined. The Cell I "atomic" semantics are an operational convention, not a code constraint. |

## 5. Decision quality of this estimate

This memo is Round-1 documentation under the audit-remediate-loop discipline (skill SKILL.md §40-43 directs the producer agent to rely on isolated-subagent verification for Round 2). The producer agent applied inline self-audit but does **not** claim a Round-2 accept.

Items the user should verify before authorizing the paid call (mirrors runbook §12 residual risks):

- The `metadata.get_cost` USD interpretation (item §1.5).
- The Databento NQ 2025 archive coverage extent (item §4.1 row 3).
- The pre-2017 reconstruction-feed quality concern (item §4.1 row 2; items §3 of runbook §12).
- Worktree-local `data/processed/vendor_legacy_1min/` re-materialization need (runbook §A.2; addressed by Stage B step §7.2).

## 6. References

- Sibling repo Databento downloader: [C:\Users\skoir\Documents\SKIE Enterprises\SKIE-Ninja\SKIE-Ninja-Project\SKIE_Ninja\src\python\data_collection\databento_downloader.py](file:///C:/Users/skoir/Documents/SKIE%20Enterprises/SKIE-Ninja/SKIE-Ninja-Project/SKIE_Ninja/src/python/data_collection/databento_downloader.py).
- Prior ingest audit trail (2026-04-23): [docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](../audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md).
- Option B briefing: [memo_option-b-data-coverage_2026-04-24.md](memo_option-b-data-coverage_2026-04-24.md).
- Roll-adjusted derivative: [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) v0.2.0.
- Databento pricing page: [databento.com/pricing](https://databento.com/pricing) (fetched 2026-04-24).
- Databento API reference: [databento.com/docs/api-reference-historical](https://databento.com/docs/api-reference-historical) (navigation-only WebFetch result on 2026-04-24).
- H050 pre-reg: [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §2.
- Companion runbook: [runbook_h050-cell-i-databento-backfill_2026-04-24.md](runbook_h050-cell-i-databento-backfill_2026-04-24.md).
