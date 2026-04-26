# Audit trail — roll-adjust decade-wraparound bug fix

**Date:** 2026-04-26
**Module:** [src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py)
**Version bump:** 0.2.0 → 0.3.0
**Scope:** critical method-fidelity bug fix on the H050 substrate-feeder code, surfaced when the post-Cell-I substrate (ES + NQ 2015–2025) crossed the 10-year CME contract-code recurrence boundary.

## 1. Bug

### 1.1 Symptom

`scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2025-12-31 --force` fails the cross-row invariant (a) inside `VendorLegacy1minRollAdjustedIngestJob.validate`:

```
Symbol ES: expected exactly one contract with adjustment_factor==1.0 (the newest/anchor); got 0.
```

Diagnostic trace: 40 entries in `summary["contract_factors"]` for ES with no factor near 1.0; smallest factor `ESH5: 0.0133` (the OLDEST 2015 contract symbol, accumulating the cumulative product of all 40 rolls); largest factor `ESZ7: 1.18` (Dec 2017).

### 1.2 Root cause

CME equity-index futures contract codes — vendor-symbol convention as carried by Databento GLBX.MDP3 `raw_symbol` per [CME Group, *Contract Month Codes*](https://www.cmegroup.com/month-codes.html), [CME Group, *Understanding Contract Trading Codes*](https://www.cmegroup.com/education/courses/introduction-to-futures/understanding-contract-trading-codes), and [Databento, *Symbology Standards*](https://databento.com/docs/standards-and-conventions/symbology); CME itself accepts both 1-digit (ESZ5) and 4-digit (ESZ2025) forms — use a 1-digit calendar-year suffix (`ESH5` = March-2015 OR March-2025). The pre-fix `_adjust_one_symbol` keyed the cumulative back-adjustment dictionary on `contract_symbol`:

```python
contract_factor: dict[str, float] = {}
contract_factor[newest] = 1.0          # newest = "ESZ5" (Dec 2025)
cum = 1.0
for rr in reversed(ratios):
    cum *= rr.ratio
    contract_factor[rr.event.old_contract] = cum
```

Walking backward through ~40 rolls (2015-2025), the loop eventually reaches the 2016 transition where `ESZ5` (Dec 2015) is the `old_contract` — the dict entry for the string key `"ESZ5"` is OVERWRITTEN by the cumulative product, destroying the anchor. The ratio chain then has no contract anchored at 1.0.

The bug is invisible on the legacy 2020-2025 substrate (suffix digits 0-5 never wrap) and only manifests once 2015 lands.

## 2. Fix — `contract_id_full` disambiguation

### 2.1 Disambiguator definition

`contract_id_full = f"{contract_symbol}_{ts_event.year:04d}"` — derived per-bar at the entry of `_adjust_one_symbol`. Each bar's full 4-digit calendar year is appended, so March-2015 ESH5 bars get `contract_id_full = "ESH5_2015"` while March-2025 ESH5 bars get `contract_id_full = "ESH5_2025"`. Two physically distinct contracts with the same display string get distinct keys.

The original `contract_symbol` is preserved unchanged in the output as `front_contract_symbol` for downstream display and cross-referencing with vendor data.

### 2.2 Soundness invariant

`contract_id_full` is a sound disambiguator iff every physical contract's bars land within a single calendar year. Empirical verification on the 2015–2025 ES substrate (commands logged 2026-04-26):

```
ESH0..ESH9 except ESH5: bars span 1 calendar year
ESH5:                    bars span 2 calendar years (2015, 2025) — gap = 10y
ESM5, ESU5, ESZ5:        same pattern, 10y gap
```

The single source of truth for "decade-or-more apart" is the CME 10-year recurrence period of the contract code, formalised as:

```python
_CME_CONTRACT_CODE_RECURRENCE_YEARS = 10
```

`_assert_no_consecutive_year_collision` enforces: for each `contract_symbol`, no two consecutive years in its bar set are <10 years apart. Adjacent-year collisions (e.g., ESH6 with bars in both Dec 2015 and Jan 2016) would mean the upstream `download_historical_years` per-contract month-bounded windows have been violated, and surface as a controlled `ValueError`.

### 2.3 Pipeline propagation

Modified functions:

- `detect_raw_front_month_by_day`: emits `front_contract_id_full` on production input (with `contract_id_full` column); falls back to `front_contract_symbol` for synthetic single-decade fixtures, preserving back-compat with existing unit tests.
- `apply_persistence_guard`: auto-detects the front-month column name and threads the disambiguated key through to `effective_front_contract_id_full`.
- `detect_roll_events`: auto-detects; emits `RollEvent` whose `old_contract` / `new_contract` carry the disambiguated key (production) or raw (test).
- `compute_roll_ratio_afml`: auto-detects column family.
- `_adjust_one_symbol`: derives `contract_id_full` once at entry; keys all internal dictionaries and groupby keys on it; joins back to recover the display `contract_symbol` at output emission.
- `validate`: re-derives `_front_contract_id_full = front_contract_symbol + "_" + ts_event.year` for cross-row invariants (a), (b), (c). Two distinct physical contracts that happen to share a 1-digit display code in different decades get separate factor groups, anchor counts, and roll_flag groupings — which is correct.

## 3. AFML §2.4.3 anchor invariant verification

Per [López de Prado 2018, *Advances in Financial Machine Learning*, Wiley, ISBN 978-1-119-48208-6, ch.2 §2.4.3 ("Single Future Roll")]: the canonical roll-adjusted continuous contract anchors the newest contract at scalar 1.0 and back-propagates the cumulative product of `ρ_k = new_open(t_first_new) / old_close(t_last_old)` through older contracts. The newest contract is the unique anchor — that's the point of cumulative back-adjustment (versus forward-adjustment, which anchors the oldest). Adjusted log-returns are preserved across roll boundaries because the multiplicative scalar cancels in log-diffs.

The post-fix code preserves this invariant on multi-decade substrates: `summary["contract_factors"]["ESM5_2025"] == 1.0` (anchor), and walking backward through the 40-roll chain `summary["contract_factors"]["ESH5_2015"] = product(ρ_k)`. The `ESH5_2025` and `ESH5_2015` entries are distinct dict keys, so the anchor is never overwritten. Validation invariant (a) — exactly one anchor per symbol — passes by construction.

## 4. Test coverage

### 4.1 Pre-existing (29 tests, all green)

- `TestRawFrontMonthDetection` (4) — unchanged, exercises single-decade input where the disambiguation reduces to identity.
- `TestPersistenceGuard` (3), `TestRollRatioAFML` (2), `TestAdjustmentInvariants` (6) — unchanged.
- `TestMultiRollChain` (1), `TestChainContinuity` (1) — `contract_factors` keys updated from raw display ("ESH4") to disambiguated ("ESH4_2024").
- `TestValidateCrossRow` (4), `TestIngestJobContract` (8) — `summary["rolls"][*].old_contract` keys updated.

### 4.2 New regression tests (4 added in `TestDecadeWraparound`)

- `test_anchor_unique_across_decade_wraparound` — full-pipeline regression: 4-segment fixture covering ESH5(2015) → ESM5(2015) → ESH5(2025) → ESM5(2025). Asserts (i) exactly one anchor at 1.0, (ii) anchor is `ESM5_2025` (newest), (iii) both `ESH5_2015` and `ESH5_2025` appear with distinct factors, (iv) full `validate()` passes.
- `test_validate_rejects_pre_v030_collision_substrate` — confirms the cross-row invariant still rejects manually-corrupted output that mimics the pre-fix bug.
- `test_assert_no_consecutive_year_collision_rejects_violation` — synthetic ESH6 with bars in Dec 2015 and Jan 2016; asserts controlled `ValueError`.
- `test_assert_no_consecutive_year_collision_permits_decade_gap` — synthetic ESH5 in 2015 + 2025; asserts no exception.

### 4.3 Test count

| Scope | Pre-fix | Post-fix |
|---|---|---|
| `tests/unit/test_vendor_legacy_1min_roll_adjusted.py` | 29 | 33 |
| Full unit suite (`tests/unit/`) | 625 | 625 (re-run pending) |

## 5. Live integration test

Command:

```
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  uv run --python 3.11 --extra dev python scripts/ingest.py \
  --dataset vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2025-12-31 --force
```

### 5.1 Result

Run started 2026-04-26 10:28:02 CDT (15:28:02 UTC); completed 10:29:18 CDT (~76 s wall-clock).

| Metric | Value |
|---|---|
| Source parquets fetched | 22 (ES + NQ × 11 years 2015-2025) |
| Rows in adjusted output | 7,354,066 |
| Rolls (per-bar `roll_flag` count) | 116,684 |
| Partitions written | 22 |
| Schema validation | passed |
| Cross-row invariants (a/b/c) | passed |
| Provenance | `data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json` |
| Output frame SHA256 | `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` |
| Source frame SHA256 | `37cd47cfb39b324500b89a6fee6e2d43e231fb402e37e5e4dddd5fa1a3571cf7` |
| Provenance dataset version | `0.3.0` |

### 5.2 Anchor verification (per-symbol)

| Symbol | n_rolls | n_factors | anchor (factor=1.0) |
|---|---|---|---|
| ES | 43 | 44 | `ESZ5_2025` (Dec 2025) |
| NQ | 43 | 44 | `NQZ5_2025` (Dec 2025) |

Both symbols' factor dictionaries contain the disambiguated `contract_id_full` keys (`ESH5_2015` and `ESH5_2025` are distinct entries with distinct factors); the cumulative-back-adjust loop now correctly preserves the newest contract's anchor at 1.0 across the decade-wraparound. AFML §2.4.3 invariant verified empirically on the live substrate.

## 6. Files changed

- `src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py` — main fix; version bump 0.2.0 → 0.3.0.
- `tests/unit/test_vendor_legacy_1min_roll_adjusted.py` — updated 4 existing test assertions for new key form; added 4 new regression tests in `TestDecadeWraparound`.
- `docs/audits/audit_trail_2026-04-26_roll-adjust-decade-wraparound.md` — this file.

## 7. Residuals

- Audit-remediate-loop §40-43 calls for proper-isolated quant-auditor verification (round 2). End-of-round-1 status: implementation + regression tests + AFML invariant verification complete. Main thread will spawn the proper-isolated quant-auditor.
- Pre-existing ruff PLR/PLC violations on the module remain at the same baseline count (11 errors); no net-new ruff issues introduced.
- The pre-existing `validate` cross-row invariant (b) message still references `front_contract_symbol` for human readability; the underlying check now keys on the disambiguated `_front_contract_id_full` so it correctly accepts the legitimate two-decade case where the display contract_symbol "ESH5" appears with two distinct factors.
