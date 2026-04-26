# Audit trail — H050 Cell I Databento backfill runbook (2026-04-24)

## Context

User accepted Cell I disposition for `P1-H050-DATA-COVERAGE` per [docs/research_notes/memo_option-b-data-coverage_2026-04-24.md](../research_notes/memo_option-b-data-coverage_2026-04-24.md) §6 on 2026-04-24: backfill ES + NQ 2015-2019 + NQ 2025 from Databento GLBX.MDP3 to close the H050 design.md §2 substrate gap.

This audit trail covers the **runbook + cost-estimate preparation deliverable**, NOT the paid Databento API call (which is the user's authorization gate, not the producer agent's).

## Deliverables produced

| Surface | Path |
|---|---|
| Runbook | [docs/research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md](../research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md) |
| Cost / time / risk memo | [docs/research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md](../research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md) |
| Updated H050 manifest | [research/01_hypothesis_register/H050/data_requirements.md](../../research/01_hypothesis_register/H050/data_requirements.md) — new "Pending Cell I backfill" section, frozen pre-Cell-I checksums preserved |
| This audit trail | [docs/audits/audit_trail_2026-04-24_h050-cell-i-runbook.md](audit_trail_2026-04-24_h050-cell-i-runbook.md) |

No source code modified. No paid API call placed. No commit created.

## Round-1 producer-agent self-audit

The producer agent applied a self-audit during composition. Findings caught and remediated inline:

| ID | Severity | Issue | Remediation |
|---|---|---|---|
| R1-1 | **critical** | First draft assumed `scripts/ingest.py --dataset vendor_legacy_1min` could pull from Databento directly given `--start`/`--end` args. Empirical dry-run captured at runbook §A.1 showed it cannot — the CLI accepts the args but does NOT parameterize the fetch (`del start, end` at [vendor_legacy_1min.py:113](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py)). | Reframed runbook around two-stage execution (§2): Stage A in sibling repo (paid, has Databento SDK + API key); Stage B in SKIE-Universe (local, idempotent CSV-import). Captured both dry-runs as Appendix A. |
| R1-2 | major | First draft used the published Databento per-row pricing as the cost anchor. WebFetch on [databento.com/pricing](https://databento.com/pricing) revealed pricing is per-GB-uncompressed, not per-row, and per-tuple USD figures come from `metadata.get_cost`, not the public page. | Reframed cost-estimate memo §1 around the empirical $3.17 anchor for the prior 2023-2024 ES+NQ pull (sibling-repo `databento_downloader.py` line 363) with linear extrapolation to 11 symbol-years ≈ $8.71. Verification gap explicitly flagged as residual risk. |
| R1-3 | major | First draft did not address full-sample-rescaling property of the roll-adjusted derivative. Per [vendor_legacy_1min_roll_adjusted.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py) §"Point-in-time caveat", adding new historical contracts changes the multiplicative factor for ALL bars, so the existing 22 frozen partition checksums all become invalid post-Cell-I. | Runbook §7.3 documents `--force` requirement; data_requirements.md §"Pending Cell I backfill" tables the 22 pre-Cell-I checksums against TBD post-Cell-I values; cost memo §3 flags the full-rederivation storage cost. |
| R1-4 | major | First draft's verification queries produced a false-pass risk: row-count gates were too tight (assumed exactly 252 trading days × 405 RTH minutes, ignoring half-days, holidays, and the fact that the substrate carries ETH+RTH not RTH-only). | Runbook §8.2 widened to 280k–400k full-day per-symbol-year envelope with explicit ±5% sanity gate and explanation of RTH/ETH split. |
| R1-5 | major | First draft did not flag the worktree-local `data/processed/vendor_legacy_1min/` absence. Empirical dry-run §A.2 raised `FileNotFoundError`. | Runbook §3 pre-check + §A.2 made this an explicit re-materialization step. |
| R1-6 | minor | Single-digit-year contract code (e.g., `ESH5`) is ambiguous between 2015 and 2025 in bare form. | Runbook §4 documented the disambiguation: Databento bounds the contract by the API call's `start`/`end` date range, and the sibling downloader's `download_historical_years` already passes year-bounded ranges. Verification step at §6.3 (per-CSV ts_event year check) is the operational gate against undetected collision. |
| R1-7 | minor | First draft conflated "the runbook agent makes the `_CANONICAL_SOURCES` edit" with "the runbook documents what edit is needed." Constraint forbids modifying [src/](../../src/). | Runbook §7.1 made explicit that the producer agent does NOT make this edit; user or Stage-B follow-up agent does, before §7.2. |
| R1-8 | minor | First draft did not address the pre-2017 reconstruction-feed provenance shift identified in [memo_option-b-data-coverage_2026-04-24.md](../research_notes/memo_option-b-data-coverage_2026-04-24.md) §3.1. | Runbook §12 item 3 + cost-memo §4.1 row 2 flagged as residual risk. New follow-up `P1-VENDOR-LEGACY-RECONSTRUCTION-PROVENANCE` proposed for the existing provenance schema to add a `reconstruction_window` field. |

## Residual risk after Round-1 self-audit (NOT yet Round-2 verified)

Round 2 is **not** claimed complete by the producer agent. Per the user's instruction and `~/.claude/skills/audit-remediate-loop/SKILL.md` §40-43, isolated-subagent verification (parallel `quant-auditor` + `literature-check` + `reproducibility-verifier`) runs from the main thread, not from the producer agent in this delivery. The following are the producer agent's flagged residual risks for that Round-2 audit to verify:

1. **Databento `metadata.get_cost` USD interpretation not directly verified from primary docs.** WebFetch on [databento.com/docs/api-reference-historical/metadata/get-cost](https://databento.com/docs/api-reference-historical/metadata/get-cost) returned navigation-only content on 2026-04-24. Anchor is sibling-repo docstring + USD-formatted print statements. Mitigation: runbook §6.1 has user visually confirm pre-bill.
2. **NQ 2025 vendor coverage cutoff unverified.** Estimate uses ES 2025 cutoff (2025-12-03) as proxy. Stage A row count is the operational discovery point.
3. **Pre-2017 reconstruction-feed quality not characterized.** Provenance shift documented but quantitative comparison vs native MDP 3.0 not done. H050 §10 line 105 stationarity pre-check is the binding gate.
4. **Single-digit-year disambiguation inferred, not directly verified.** Runbook §4 logic anchored to sibling downloader's call pattern; not to a Databento symbology doc page (WebFetch limitation).
5. **Linear-extrapolation cost model unverified.** $3.17 / 4 symbol-years assumes uniform per-symbol-year row density and uniform per-byte pricing. Pre-2017 reconstructed bars may price differently. The `metadata.get_cost` pre-call in runbook §6.1 is the binding figure.

## Constraints honored

- [x] No paid Databento API call placed.
- [x] No modification to `scripts/ingest.py`.
- [x] No modification to [src/](../../src/) or [tests/](../../tests/).
- [x] No modification to [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md).
- [x] No modification to [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) (file does not yet exist per CLAUDE.md aggregation-rule status; producer agent did not create it either, that is a separate Cell-I-precondition).
- [x] No modification to [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py).
- [x] No modification to [docs/decisions/](../decisions/).
- [x] No modification to [CLAUDE.md](../../CLAUDE.md) or memory files.
- [x] No commit created.

## Dry-run captures

Both captures recorded verbatim in [runbook §A](../research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md):

- §A.1: `vendor_legacy_1min --start 2015-01-01 --end 2019-12-31 --dry-run` succeeded, processed only the 9 existing sibling-repo CSVs (the Round-1 critical finding).
- §A.2: `vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2025-12-31 --dry-run` raised `FileNotFoundError: Source dataset root not found: data/processed/vendor_legacy_1min` — worktree-local re-materialization required regardless of Cell I.

## Audit-remediate-loop status

- **Round 1 (this audit, producer-agent self-audit)**: 8 findings (1 critical + 4 major + 3 minor) caught and remediated inline before runbook commit.
- **Round 2 (deferred to main thread)**: not yet performed. Producer agent does not claim Round-2 accept.
- **Cap**: 3 rounds per [~/.claude/CLAUDE.md](~/.claude/CLAUDE.md) §Agentic Iteration. Two rounds remain available.

## Next steps for the user

1. Read [runbook §0-§5](../research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md) and [cost-estimate memo](../research_notes/memo_h050-cell-i-cost-estimate_2026-04-24.md).
2. Decide on the authorization ceiling (recommended $30 USD per cost-memo §1.4).
3. From the main thread, optionally invoke the audit-remediate-loop SKILL Round 2 (parallel `quant-auditor` + `literature-check` + `reproducibility-verifier`) over these deliverables.
4. Address the H050 aggregation-rule addendum (separate precondition per CLAUDE.md aggregation-rule status; **independent of** Cell I data readiness, but **co-required** for the H050 walk-forward run).
5. Execute the runbook's [Appendix B](../research_notes/runbook_h050-cell-i-databento-backfill_2026-04-24.md#appendix-b--go--no-go-command-sequence) Stage A.
6. Execute Stage B (incl. creating `config/cell_i_sources.yaml` per runbook §7.1 and running with `--sources-yaml`) and verification per runbook §8.
7. Update data_requirements.md per runbook §9 and commit per runbook Appendix B step 9.

## Round 2 — main-thread-isolated remediation

Round-2 isolated subagent verification was performed from the main thread (the `Agent` tool is not surfaced in the producer agent's runtime; main-thread invocation is the substitute mechanism per the audit-remediate-loop skill §40-43). The verification surfaced 1 critical + 6 major findings, summarized below with the remediations applied 2026-04-25.

### Findings and remediations

| ID | Severity | Issue | Remediation |
|---|---|---|---|
| F-2-1 | **critical** | Runbook §1 table, §6.2, §8.2, cost-memo §3, data_requirements.md "Pending Cell I" all stated each year ends 12-31. The sibling `download_historical_years` actually defines `('Z', '09-15', '12-20')` — empirically confirmed by per-CSV inspection 2026-04-25: ES_2022 last bar = 2022-12-16; ES_2023+2024 combined last = 2024-12-19. Each calendar year ends ~Dec 16-20, not Dec 31. | Runbook §1 table updated with `~Dec 20` end-dates for each row; new §1.1 "Intrinsic Dec 21-31 calendar-edge gap" subsection acknowledges the gap as intrinsic to the contract-month tuple and symmetric across pre-existing 2020-2024 + new Cell I substrate. data_requirements.md "Coverage" row corrected (NQ 2024-12-31 → 2024-12-19); "Pending Cell I" §"Expected Coverage update" reflects ~Dec 20 bounds. New follow-up `P1-DATABENTO-DEC21-EXTENSION` logged for optional Z-window extension. |
| F-2-2 | major | NQ 2025 row count proxy used the ES 2025 truncation (last bar 2025-12-03; mtime 2024-12-04), but a fresh NQ 2025 pull on Stage A would deliver bars through ~2025-12-20. Runbook §1 NQ 2025 row was wrong. | Runbook §1 NQ 2025 row updated to "~360k rows; 2025-01-01 → ~2025-12-20"; new §6.4 "NQ 2025 vs ES 2025 currency check" subsection adds Stage A verification step `last_ts(NQ 2025) > last_ts(ES 2025)` plus a recommended opportunistic ES 2025 refresh in the same Stage A. |
| F-2-3 | major | Per-year row-count proxy (318k ES, 364k NQ) was a divisional artifact derived from combined-CSV row totals divided by approximate-year-counts. Per-CSV inspection 2026-04-25 shows ES≈340k/yr, NQ≈340k/yr (the two roots have very similar density). | Runbook §1 row counts updated to ~340k for both ES and NQ; §1 added an empirical-anchor table with verbatim per-CSV row counts and ts_event envelopes; §8.2 baseline updated to mean 340k ± 5%. Cost-memo §3 storage table recomputed against ~3.74M total new rows (5×340k ES + 5×340k NQ + ~360k NQ-2025); previously-stated ~3.77M is superseded. |
| F-2-4 | major | $3.17 in cost-memo §1 was a hard-coded function default in `databento_downloader.py:363`, not a billing record. The $8.71 "linear extrapolation" and the "$8-12 mid / $6 low / $15 high" estimate band added pseudo-precision around an indicative-not-binding number. | Cost-memo §1.1-1.4 reframed: §1.1 explicitly binds authorization to the live `metadata.get_cost` call (`T_live`); §1.2 demotes the $3.17 anchor to "indicative-not-binding"; §1.4 reframes the $30 ceiling as "user-chosen budget" with operational rule "abort if `T_live > $30 USD`; otherwise authorize up to `2 × T_live`." The mid/low/high band is removed. Runbook §5 reframed in lockstep; §6.1 updated to record `T_live` per follow-up `P1-H050-CELL-I-LIVE-COST-CAPTURE`. |
| F-2-5 | major | Runbook §7.1 instructed manual `_CANONICAL_SOURCES` edit (11 new `_SourceFile` lines). Brittle: requires source-file edit, no schema enforcement, no regression coverage. | Implemented `--sources-yaml` CLI flag in [scripts/ingest.py](../../scripts/ingest.py) wired through the constructor's `sources` kwarg. New [load_sources_yaml](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) + [merge_sources](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) helpers enforce schema (required keys, valid symbol set, .csv suffix, no duplicate filenames, canonical-precedence on collision). New regression test file [tests/unit/test_ingest_vendor_legacy_sources.py](../../tests/unit/test_ingest_vendor_legacy_sources.py) — 16 cases including the Cell-I 11-entry case, schema violations, merge precedence, constructor wiring, and tuple-length + filename-pattern preservation. Runbook §7.1 + Appendix B step 4 rewritten to use the YAML path; manual `_CANONICAL_SOURCES` edit demoted to "fallback only." Round-2 dry-run captured at runbook Appendix A.3. |
| F-2-6 | major | Runbook §4 stated `download_historical_years uses 'year-bounded `start = f"{year}-01-01"`'` — wrong. The actual code uses contract-month-bounded `start = f"{year}-{start_md}"` (e.g., `2015-01-01 → 2015-03-17` for ESH5). | Runbook §4 rewritten: distinguishes `download_historical_years` (contract-month-bounded; collision-safe because requested 2015-Q1 window does not overlap any 2025-active contract) from `estimate_cost_for_years` (full-year-windowed; collision-safe in practice because a 2015-active contract cannot deliver 2025 bars). The §6.3 per-CSV ts_event year check remains the operational mitigation. |
| F-2-7 | major | No expected-vs-actual unique-trading-date gate. Specific risk: Carter National Day of Mourning 2025-01-09 — NYSE closed but CME equity-index futures observed early close at 13:15 CT. Naive holiday filtering could silently drop the date. Other concerns: Bush funeral 2018-12-05; day-after-Thanksgiving half-days; Christmas Eve early closes; Good Friday closures. | Runbook §8 new §8.6 "Calendar-edge gate" subsection. Uses [pandas_market_calendars](https://pandas-market-calendars.readthedocs.io/en/latest/usage.html) `valid_days()` for `CME_Equity` and `NYSE` calendars. Operational rule: flag any `(symbol, year)` partition with `|expected − actual| > 1 day`. Specific dates enumerated: 2025-01-09 (Carter), 2018-12-05 (Bush), day-after-Thanksgiving, Christmas Eve, Good Friday. Cross-references [src/skie_ninja/utils/clock.py](../../src/skie_ninja/utils/clock.py) as a fallback calendar source. Cites [CME Holiday Calendar](https://www.cmegroup.com/tools-information/holiday-calendar.html) as canonical reference. |

### WebFetch verification scope and gap

Primary-source verification was attempted via WebFetch on:

- [databento.com/docs/api-reference-historical/metadata/get-cost](https://databento.com/docs/api-reference-historical/metadata/get-cost) — returned navigation-only excerpt (same limit as Round 1).
- [databento.com/docs/standards-and-conventions/symbology](https://databento.com/docs/standards-and-conventions/symbology) — navigation-only.
- [www.cmegroup.com/notices/clearing/2025/01/Chadv25-005.html](https://www.cmegroup.com/notices/clearing/2025/01/Chadv25-005.html) — timeout.
- [www.cmegroup.com/tools-information/holiday-calendar.html](https://www.cmegroup.com/tools-information/holiday-calendar.html) — timeout.
- [www.nyse.com/markets/hours-calendars](https://www.nyse.com/markets/hours-calendars) — covers 2026-2028 only; 2025 / 2018 closures not retrievable.
- [pandas-market-calendars.readthedocs.io](https://pandas-market-calendars.readthedocs.io/en/latest/usage.html) — **succeeded**; `valid_days()` API confirmed for `CME_Equity` and `NYSE` calendars.
- [Wikipedia Carter state-funeral](https://en.wikipedia.org/wiki/Death_and_state_funeral_of_Jimmy_Carter) — **succeeded**; National Day of Mourning declaration confirmed; specific exchange closure status not in Wikipedia article (cited as cross-check, not primary).

The Carter-funeral CME early-close hour (13:15 CT) and the holiday-calendar dates are documented in §8.6 as primary-source references for which WebFetch returned navigation-only or timed out; the runbook directs the user to verify against the CME official notice and the pandas_market_calendars `early_closes()` API at runtime, with the calendar gate as the operational catch.

### Code, tests, ruff, and CI artefacts

- Source modified: [src/skie_ninja/data/ingest/vendor_legacy_1min.py](../../src/skie_ninja/data/ingest/vendor_legacy_1min.py) — added `load_sources_yaml`, `merge_sources`, `_VALID_SYMBOLS`, `import yaml`, `from typing import Any`. Constructor's `sources` kwarg already existed; no signature change.
- CLI modified: [scripts/ingest.py](../../scripts/ingest.py) — added `--sources-yaml` argument; merge-and-replace logic guarded to `--dataset vendor_legacy_1min` only (other datasets reject the flag). Added `# noqa: PLR0915` to `run()` for the +12 statements.
- Tests added: [tests/unit/test_ingest_vendor_legacy_sources.py](../../tests/unit/test_ingest_vendor_legacy_sources.py) — 16 cases, all green.
- Full-suite pytest 2026-04-25 (env: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src uv run --python 3.11 --extra dev pytest tests/unit/ -q`): **617 passed in 802.24s.** Net delta from prior baseline: +16 (the new test file).
- Ruff 2026-04-25 on touched files (`src/skie_ninja/data/ingest/vendor_legacy_1min.py`, `scripts/ingest.py`, `tests/unit/test_ingest_vendor_legacy_sources.py`): **2 errors, both pre-existing baseline** (E501 on `scripts/ingest.py:125` line-too-long, PLC0415 on `scripts/ingest.py:127` import-inside-function — both predate this work). **Net-zero new violations.**
- `--sources-yaml` dry-run captured at runbook §A.3 (2026-04-25); confirmed 11 extra sources loaded, total canonical sources=20, missing-source errors logged for the 11 not-yet-pulled CSVs (expected pre-Stage-A state).

### New follow-ups logged (parent will move to CLAUDE.md)

- `P1-DATABENTO-DEC21-EXTENSION` (optional, non-blocking) — extend the sibling `download_historical_years` Z-window from `'12-20'` to `'12-31'` to capture the brief no-front-month tail at year-end. Trade-off: the captured bars are sparse and span no active contract; downstream use must distinguish from regular Z-window bars. Anchored at runbook §1.1.
- `P1-H050-CELL-I-LIVE-COST-CAPTURE` (binding for next run) — record the `metadata.get_cost` output `T_live` from runbook §6.1 as the binding cost record post-Stage-A. Add to ReproLog or a new `cost_records/` artefact path. Anchored at runbook §6.1 and cost-memo §1.4.

### Constraints honored (Round 2)

- [x] No paid Databento API call placed.
- [x] No modification to [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md).
- [x] No modification to [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) (file does not exist; not created here).
- [x] No modification to [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py).
- [x] No modification to [docs/decisions/](../decisions/) ADRs.
- [x] No modification to [CLAUDE.md](../../CLAUDE.md) or memory files.
- [x] No commit created.
- [x] Net-zero new ruff violations.
- [x] Full unit-test suite green (617 passed, 0 failed).
