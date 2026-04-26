---
type: audit_trail
description: Atomic re-freeze of H050 data_requirements.md after Cell I substrate land
date: 2026-04-26
status: implementing-agent-complete; verification deferred to main thread
subagent_isolation: deferred-to-main-thread
---

# Audit Trail — H050 data_requirements.md atomic re-freeze (2026-04-26)

## Scope

Execute runbook §8.1-§8.6 verification gates against the post-Cell-I roll-adjusted substrate, then atomically re-freeze [research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) with the binding post-Cell-I SHA256 set, retaining pre-Cell-I checksums for audit.

Runbook reference: [docs/research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md](../research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md) §8.

Provenance: [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260426.json) — `output_frame_sha256` = `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` (corroborated below).

Substrate version: `vendor_legacy_1min_roll_adjusted` v0.3.0 (commit `329fd1b` decade-wraparound disambiguation), built atop Cell I substrate landed in commit `3b00713`.

## §8.1 Partition presence — PASS

| Dataset | Symbol | Partition count |
|---|---|---|
| `vendor_legacy_1min` (raw front-month) | ES | 11 |
| `vendor_legacy_1min` (raw front-month) | NQ | 11 |
| `vendor_legacy_1min_roll_adjusted` | ES | 11 |
| `vendor_legacy_1min_roll_adjusted` | NQ | 11 |

Years 2015-2025 inclusive per symbol. All four directories report `wc -l` = 11 against `part-0000.parquet`. Gate threshold (≥11) met.

## §8.2 Row-count sanity check — PASS (with two interpretive flags)

Full-day 1-min bars including ETH on the roll-adjusted substrate:

| Symbol | Year | Rows | ±5% gate vs 340k | Notes |
|---|---:|---:|---|---|
| ES | 2015 | 335,130 | OK | |
| ES | 2016 | 334,369 | OK | |
| ES | 2017 | 330,694 | OK | |
| ES | 2018 | 338,457 | OK | |
| ES | 2019 | 339,615 | OK | |
| ES | 2020 | 334,568 | OK | |
| ES | 2021 | 336,627 | OK | |
| ES | 2022 | 337,365 | OK | |
| ES | 2023 | 337,837 | OK | |
| ES | 2024 | 344,842 | OK | |
| ES | 2025 | 325,030 | (truncated) | Last bar 2025-12-03 per file mtime. |
| NQ | 2015 | 313,790 | FLAG (-7.7%) | Interpretive: see §8.6 — within Sunday-extra + holiday band. |
| NQ | 2016 | 319,477 | FLAG (-6.0%) | Interpretive: see §8.6. |
| NQ | 2017 | 323,918 | OK (-4.7%) | |
| NQ | 2018 | 337,274 | OK | |
| NQ | 2019 | 339,552 | OK | |
| NQ | 2020 | 333,973 | OK | |
| NQ | 2021 | 336,563 | OK | |
| NQ | 2022 | 337,300 | OK | |
| NQ | 2023 | 336,637 | OK | |
| NQ | 2024 | 342,617 | OK | |
| NQ | 2025 | 338,431 | (truncated) | Z-window-bounded; last bar ~2025-12-19. |

Two NQ-2015/NQ-2016 partitions trip the strict ±5% gate. **Round-2 corrected interpretation (per F-PLV-3 below):** the NQ 2015 (-7.7%) and NQ 2016 (-6.0%) row-count drops are attributable to lower per-date 1-min bar density (1039.0 bars/date in NQ 2015 vs 1109.7 in ES 2015) reflecting documented early-period NQ overnight illiquidity, **not** to missing trading dates. Date-counts are equal between ES and NQ in both years (NQ 2015 = ES 2015 = 302 unique UTC dates; NQ 2016 = ES 2016 = 299). Density converges to ES levels by 2018 (NQ 1116.8 vs ES 1120.7). No data-loss defect; the substrate's design.md §2 envelope coverage is satisfied modulo the right-edge truncation pre-disclosed under F-PLV-1. Tracked under `P1-MISSING-BAR-RATE-EMPIRICAL`.

## §8.3 Schema check — PASS

All 22 partitions (`vendor_legacy_1min_roll_adjusted/symbol={ES,NQ}/year={2015..2025}/part-0000.parquet`) carry the canonical 11-column schema:

`{ts_event, open, high, low, close, volume, symbol, front_contract_symbol, adjustment_factor, unadjusted_close, roll_flag}`

Zero missing columns; zero unexpected columns. `SCHEMA_OK=True`.

## §8.4 Frame-level SHA256 freeze

Method: `skie_ninja.utils.hashing.frame_sha256(df, sort_cols=["symbol","ts_event"])`. BLAS pinned (OMP/MKL/OPENBLAS = 1).

### Combined frame

| Field | Value |
|---|---|
| Combined SHA256 | `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` |
| Rows | 7,354,066 |

Corroborates the provenance JSON `output_frame_sha256` exactly.

### Per-partition (22 entries)

| Partition | SHA256 |
|---|---|
| `symbol=ES/year=2015/part-0000.parquet` | `b499bb492dcdc9d562e3f5d65799ae10d4c9a1cff404c0a7491c58e7edaccfd5` |
| `symbol=ES/year=2016/part-0000.parquet` | `a384c0c225a43910c1a42910c4cfe291bc59c9b891f24f6b68f8bce6838ab1a5` |
| `symbol=ES/year=2017/part-0000.parquet` | `532b08fdf49f099526486e61b24f6fdcb924e2d0ed9af639d812860dda61a051` |
| `symbol=ES/year=2018/part-0000.parquet` | `d883cfd05855aa90a1c4d3dd2b5a235fda2e52231747883fffd22d8d573268cc` |
| `symbol=ES/year=2019/part-0000.parquet` | `c45f2f3fb723bf0764e0735bb25ba09d4115568069912a2711583cdf85070180` |
| `symbol=ES/year=2020/part-0000.parquet` | `da0485eb88564739859ab263cf0e64fe91257bb4416b33816eb77ed02c8b572a` |
| `symbol=ES/year=2021/part-0000.parquet` | `f5cf095df92ad587d3718e5a41d4c2d0d439d7843020254608cf941246f1d171` |
| `symbol=ES/year=2022/part-0000.parquet` | `cc0aa93b7ddccd7fe9fbbbe2c415c2d4a6fbf7c5d8067d34319f8fbdcf3b5f98` |
| `symbol=ES/year=2023/part-0000.parquet` | `ce5e599db6e8cb520fb257ac57512f294fff7d5e37e963d5692a9add701a2423` |
| `symbol=ES/year=2024/part-0000.parquet` | `a7d5fc06f215e190a863e5b49b1ea709a2f34e8f058056533103d676f1be2a9a` |
| `symbol=ES/year=2025/part-0000.parquet` | `4863284d4ebcff796e9c4fc2338e9ce643127710384998011876844e1fba798e` |
| `symbol=NQ/year=2015/part-0000.parquet` | `2ab474274660b1e7e70102e66fd1ec03835291ab6c47d46b28cddb37dde7a5b0` |
| `symbol=NQ/year=2016/part-0000.parquet` | `0743afa0825ee5c5aedf786b05d5a09c09955ad1113c153954459f278706192e` |
| `symbol=NQ/year=2017/part-0000.parquet` | `55b4e088b2b53cc7463d2bee8cd819b9300143915fcd3ed907105940e14938fe` |
| `symbol=NQ/year=2018/part-0000.parquet` | `7651addca845cd7689af2379d59c70168c8bb174be78df2f11549bd7b9a60467` |
| `symbol=NQ/year=2019/part-0000.parquet` | `c346a7d280c720888f88361db0ea76a6ab6b845c79b2d229c5ad8043578e5bea` |
| `symbol=NQ/year=2020/part-0000.parquet` | `e0c98ffbd5912daf890b51b46984355d6e2064da9406c39a96eae7026cab634e` |
| `symbol=NQ/year=2021/part-0000.parquet` | `268b522d54073c36871c4867089e23113d9322968b4a5f495fc20813395d3137` |
| `symbol=NQ/year=2022/part-0000.parquet` | `7cc3ca5a9e32759e796d7a59e1c2de017a9044e4afa545cc7017c665da7e5910` |
| `symbol=NQ/year=2023/part-0000.parquet` | `d419337c59f710c8ebcef89ad463e113b51113ebaeeca83e5dbbfba4e9cdc8f2` |
| `symbol=NQ/year=2024/part-0000.parquet` | `7694d6d5049f96b80031b98c4bb67f287553f321fbea245f24c34aa1f4d9911d` |
| `symbol=NQ/year=2025/part-0000.parquet` | `e90b614cfd2421a2c8f41244130c3a7dc805e40fc4dca16c6b1dfab08095acbc` |

## §8.5 RTH bar density check — PASS (implicit)

Per H050 design.md §2, the substrate carries ETH+RTH and the RTH filter is downstream in the feature factory. The §8.2 full-day row counts (~325k-345k/year for full-year ES/NQ partitions) are the binding sanity gate. No RTH-specific bar-count computation was performed at freeze time; that verification is deferred to the feature-factory layer under `P1-H050-FEATURE-PIT-ASSERT`.

## §8.6 Calendar-edge gate — PASS (interpretive, after decomposition)

Strict-gate result: every partition fires `|actual − cme_valid_days| > 1`, with deltas of +44 to +51 days/year. Decomposition shows the structural cause:

- **Sunday-evening reopen extras** (~46-50/year): substrate `ts_event` UTC dates straddle midnight CT, projecting Sunday-evening 17:00 CT bars onto a separate calendar date from the Monday CME settlement-date that `pandas_market_calendars.get_calendar('CME_Equity').valid_days()` enumerates. This is a known semantic mismatch between the ETH-substrate's bar-timestamp date projection and the calendar enumerator's settlement-date granularity.
- **New-Year reopen** (1/year): Dec-31 prior-Sunday bars project onto Jan 1 of the new year.
- **Pre-disclosed events**:
  - 2025-01-09 Carter National Day of Mourning: present as expected (NYSE closed; CME equity-index early close 13:15 CT) — caught.
  - 2025-04-18 Good Friday: missing from substrate (CME equity-index closed) — correctly absent in both ES and NQ.
- **ES 2025 Dec-truncation**: 2025-12-04 onwards missing — matches the pre-disclosed `ES_2025.csv` last-bar 2025-12-03 boundary in the runbook §1.1 coverage spec; also corresponds to the right-edge envelope shortfall under Round-2 finding F-PLV-1.

### Round-2 corrected enumeration

Calendar end-dates per partition: ES partitions other than 2025 use `f'{yr}-12-20'` (Z-window upper bound matching the substrate); ES 2025 uses `2025-12-03` (last-bar truncation); NQ partitions other than 2025 use `f'{yr}-12-20'`; NQ 2025 uses `2025-12-19`. Enumerator versions: `pandas_market_calendars==5.3.2`, `CME_Equity` and `NYSE` calendars. The full per-partition table — `data_dates` (unique UTC `ts_event` dates in the partition), `cme_n` (`CME_Equity.valid_days(start, end)` count), `nyse_n` (`NYSE.valid_days(start, end)` count), `extras = data_dates − cme_n`:

| Sym | Year | data_dates | cme_n | nyse_n | extras |
|---|---:|---:|---:|---:|---:|
| ES | 2015 | 302 | 251 | 244 | +51 |
| ES | 2016 | 299 | 251 | 245 | +48 |
| ES | 2017 | 298 | 251 | 245 | +47 |
| ES | 2018 | 302 | 251 | 245 | +51 |
| ES | 2019 | 302 | 252 | 246 | +50 |
| ES | 2020 | 302 | 251 | 245 | +51 |
| ES | 2021 | 300 | 251 | 244 | +49 |
| ES | 2022 | 299 | 251 | 244 | +48 |
| ES | 2023 | 297 | 252 | 244 | +45 |
| ES | 2024 | 303 | 254 | 246 | +49 |
| ES | 2025 | 287 | 239 | 231 | +48 |
| NQ | 2015 | 302 | 251 | 244 | +51 |
| NQ | 2016 | 299 | 251 | 245 | +48 |
| NQ | 2017 | 297 | 251 | 245 | +46 |
| NQ | 2018 | 302 | 251 | 245 | +51 |
| NQ | 2019 | 302 | 252 | 246 | +50 |
| NQ | 2020 | 302 | 251 | 245 | +51 |
| NQ | 2021 | 300 | 251 | 244 | +49 |
| NQ | 2022 | 299 | 251 | 244 | +48 |
| NQ | 2023 | 296 | 252 | 244 | +44 |
| NQ | 2024 | 301 | 254 | 246 | +47 |
| NQ | 2025 | 302 | 251 | 243 | +51 |

Empirical extras range: **+44 to +51 days/year** (Sunday-evening reopen extras + 1-2 New-Year/holiday reopens; structural to ETH UTC date-projection vs CME settlement-date granularity). The +44 to +51 range stands as originally reported; see Round-2 finding F-PLV-4 disposition for why the audit-prompt's claimed +49 to +52 lower bound was not adopted.

Round-2 supersedes the prior Round-1 selected-rows table (which contained an ES-2025 cell carrying `cme_valid_days=251`; the correct value with end=`2025-12-03` is 239).

Verdict: every observed delta is fully explained by (a) Sunday-evening reopen calendar-date projection (structural to the ETH substrate), (b) New-Year reopen (structural), or (c) holiday closures and the pre-disclosed substrate end-of-2025 truncation. No partition exhibits an unexplained absence. `P1-MISSING-BAR-RATE-EMPIRICAL` already tracks the broader empirical-density question; no new follow-ups required from §8.6.

## Pre-Cell-I → post-Cell-I supersession

**Every prior `vendor_legacy_1min_roll_adjusted` SHA is invalidated** by:
1. The substrate extension to 2015-2025 inclusive (5 new years per symbol + NQ 2025), AND
2. The v0.2.0 → v0.3.0 dataset version bump in commit `329fd1b` (`contract_id_full` disambiguation; full-sample multiplicative-ratio rescaling per the module's "Point-in-time caveat").

Both effects are independent — even partitions covering identical date ranges (ES 2020-2024, NQ 2020-2024) have different SHA256s post-Cell-I. The pre-Cell-I tables are retained verbatim in `data_requirements.md` §"Pre-Cell-I checksums (superseded 2026-04-26)" for audit retention.

Combined-frame supersession:
- pre-Cell-I: `d2c4aa4e70c6badcb294d9bec64ee3fc5093ba9085082495f5031743943b9a2d` (3,703,359 rows)
- post-Cell-I: `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` (7,354,066 rows)

## Files edited

- [research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) — atomic re-freeze: post-Cell-I SHA tables now binding; pre-Cell-I tables moved under `## Pre-Cell-I checksums (superseded 2026-04-26)` heading; `## Pending Cell I backfill` renamed to `## Cell I backfill — landed 2026-04-26` with commit refs `3b00713` + `329fd1b`; revision header bumped to 2026-04-26.
- [docs/audits/audit_trail_2026-04-26_data-requirements-refreeze.md](audit_trail_2026-04-26_data-requirements-refreeze.md) — this document.

## Constraints honored

- BLAS-pinned env: all Python invocations under `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.
- ruff impact: none (only markdown files edited).
- No source code touched (`src/`, `scripts/`, `tests/` untouched).
- No `CLAUDE.md` modification (main-thread bookkeeping).
- No `design.md` or addendum modification (Path-A immutability preserved).
- No commits issued.

## Exit verdict

§8.1 PASS · §8.2 PASS (interpretive, with documented NQ 2015/2016 and NQ 2017 borderline; decomposed) · §8.3 PASS · §8.4 frozen · §8.5 implicit-PASS · §8.6 PASS (interpretive, all deltas decomposed and accounted for).

**Implementing-agent verdict: ACCEPT.** Atomic re-freeze complete. Subagent verification deferred to main thread (`subagent_isolation: deferred-to-main-thread`).

## Round 2 — post-loop-verification (proper-subagent isolation)

Main-thread-orchestrated isolated subagent runs against the Round-1 output. Round-2 amendments above (corrections inside §8.2 and §8.6) and the new disclosure inside data_requirements.md `## Coverage` were applied as documentation-only fixes; no source code, no `design.md`, no addendum, and no second Databento call were touched.

### Subagent run identifiers

| Subagent | Run ID | Verdict |
|---|---|---|
| `quant-auditor` | `ad557c92e94814790` | proceed-with-remediation (3 majors + 3 minors) |
| `reproducibility-verifier` | `a6e220905d0f442bd` | 5 minors, no critical/major |

### Findings table

| ID | Severity | Summary | Disposition |
|---|---|---|---|
| F-PLV-1 | major | data_requirements.md "fully covers" claim was overreach: ES 2025 ends 2025-12-03 (28 days short of design.md §2 test envelope right edge); NQ 2025 ends 2025-12-19 (12 days short). | **Documentation-only (Option B).** Rewrote `## Coverage` block in data_requirements.md to drop the "fully covers" claim, state the actual coverage explicitly, distinguish harmless non-2025 Z-window truncation from the unrecovered 2025 right-edge gap, and bind any future test-window-edge-dependent disposition to a `test-window-truncated` annotation. New residual: `P1-DATABENTO-RIGHT-EDGE-EXTENSION` (option-A path; user-decision-pending). The pre-existing `P1-DATABENTO-DEC21-EXTENSION` is consolidated into the new tracker. |
| F-PLV-2 | major | §8.6 calendar-edge table carried at least one wrong CME_Equity count (the ES-2025 row showed `cme_valid_days=251` against an actual `CME_Equity.valid_days('2025-01-01','2025-12-03')` of 239). | **Resolved.** §8.6 now carries a full per-partition table with empirically-recomputed `cme_n` and `nyse_n` (`pandas_market_calendars==5.3.2`, `CME_Equity` + `NYSE`); the prior selected-row table is explicitly noted as superseded. Calendar end-dates documented per partition. |
| F-PLV-3 | major | §8.2 NQ-2015/2016 row-count rationale was self-contradictory ("2-3 missing trading days" AND "every CME trading date is present"). | **Resolved.** §8.2 rewritten to attribute the row drops to per-date 1-min bar density (NQ 2015 = 1039.0 bars/date vs ES 2015 = 1109.7 bars/date) — early-period NQ overnight illiquidity — with date-counts equal between ES and NQ. Convergence to ES levels by 2018 (NQ 1116.8 vs ES 1120.7) noted. Tracking unchanged under `P1-MISSING-BAR-RATE-EMPIRICAL`. |
| F-PLV-4 | minor | Audit-prompt claim that the empirical extras range is +49 to +52, not the document's +44 to +51. | **Empirically rejected — original document stands.** Re-running the per-partition `data_dates − cme_n` calculation against the live substrate yielded a range of `+44` (NQ 2023) to `+51` (ES 2015, 2018, 2020; NQ 2015, 2018, 2020, 2025), confirming the original "+44 to +51 days/year" wording. The full per-partition extras column is now in the §8.6 Round-2 table. The wording was kept as-is; the audit-prompt's competing range was not adopted. |
| F-PLV-5 | minor | Provenance JSONs were captured at `git_head=511225f` (pre-`329fd1b`); the v0.3.0 module behavior was already in the worktree at write-time but the recorded HEAD is stale. | **Resolved.** Round-2 reproducibility note appended below. New residual: `P1-PROVENANCE-DIRTY-WORKTREE-GIT-HEAD-PIN` (RunContext-level fix to capture worktree-dirty state and pin to the soon-to-be-committed HEAD). |
| F-PLV-6 | minor | Round-2 placeholder was inside §8.4 mid-stream rather than in a trailer section. | **Resolved.** The placeholder was removed; this `## Round 2 — post-loop-verification (proper-subagent isolation)` section is the dedicated trailer. The §8.4 main-thread-agent-ID line is no longer needed (subagent IDs are recorded in the table above). |
| Repro-1 | minor | data_requirements.md did not cross-reference the aggregation-rule addendum r2. | **Resolved.** A one-line cross-reference to `aggregation_rule_addendum_2026-04-24.md` §3.2 was added inside the new `## Coverage` Round-2 disclosure block. |
| Repro-2 | minor | ES_2025 file mtime annotation `2024-12-04` carried year-ambiguity (mtime year may not equal coverage year). | **Resolved.** Replaced with `last bar ts_event 2025-12-03 UTC` plus runbook §1.1 + F-PLV-1 cross-references. |
| Repro-3 | minor | §8.5 RTH bar density was implicit-PASS without an explicit deferral note. | **Resolved.** §8.5 wording strengthened to state explicitly that no RTH-bar count was computed at freeze time; verification deferred to feature-factory layer under `P1-H050-FEATURE-PIT-ASSERT`. |
| Repro-4 | minor | Round-2 placeholder location. | **Subsumed into F-PLV-6.** |
| Repro-5 | minor | Note about absent 2023/2024 per-year CSVs needed strengthening to give auditors a deterministic reproduction path. | **Acknowledged in Round-2 — wording in data_requirements.md `## Checksums — source CSV (raw tier)` is sufficient as written for the read-only re-freeze; reproduction guidance is now: SHA-verify `ES_1min_databento.csv` / `NQ_1min_databento.csv` against the listed combined hashes, then split by year via `src/skie_ninja/data/ingest/vendor_legacy_1min.py`. The current section's Note already states "covered by the combined `ES_1min_databento.csv` and `NQ_1min_databento.csv` checksums above"; the reproduction path is implied by the ingest module reference in the `## Source dataset` table. No edit applied beyond what F-PLV-2 / F-PLV-3 / Repro-1 introduce; if the upcoming production walk-forward runs find the implicit guidance insufficient, a follow-up `P1-DATA-REQ-REPRODUCTION-PATH-EXPLICIT` will be opened — for now, no new tracker. |

### New residual follow-ups (logged outside this audit trail by main-thread bookkeeping)

- `P1-DATABENTO-RIGHT-EDGE-EXTENSION` — option-A path closing the 2025 right-edge gap (ES Dec 04-31, NQ Dec 20-31) via a second Databento incremental pull. **User-decision-pending.** Consolidates / supersedes the prior `P1-DATABENTO-DEC21-EXTENSION` which was Z-window-only.
- `P1-PROVENANCE-DIRTY-WORKTREE-GIT-HEAD-PIN` — provenance hygiene: `RunContext` should detect a dirty worktree at provenance-write time, capture the diff hash, and fail-loud (or annotate) if the recorded `git_head` will not reproduce the recorded `output_frame_sha256` from a clean checkout.

### Reproducibility note

Provenance JSON `git_head=511225f` was captured before commit `329fd1b` (decade-wraparound bug fix `vendor_legacy_1min_roll_adjusted.py` v0.2.0 → v0.3.0) was committed. The v0.3.0 module behavior was already present in the worktree (dirty state) at provenance-write time. The output_frame_sha256 (`b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`) matches the v0.3.0 expected output and is the binding figure in `data_requirements.md`. Auditors replaying from `git_head` alone (i.e., from a clean checkout at `511225f`) would NOT reproduce this hash; replay requires a checkout at HEAD ≥ `329fd1b`. Tracked under new follow-up `P1-PROVENANCE-DIRTY-WORKTREE-GIT-HEAD-PIN`.

### Round-2 exit verdict

**ACCEPT.** All Round-1 majors (F-PLV-1, F-PLV-2, F-PLV-3) resolved by documentation edits. All Round-1 minors handled (F-PLV-4 empirically rejected with full table; F-PLV-5 disclosed; F-PLV-6 dedicated section established; Repro-1 / Repro-2 / Repro-3 / Repro-4 / Repro-5 addressed). No source code, `design.md`, addendum, second-paid-API-call, or `CLAUDE.md` modification was made.
