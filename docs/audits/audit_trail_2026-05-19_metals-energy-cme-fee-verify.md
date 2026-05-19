---
schema_version: audit_trail_v1
date: 2026-05-19
verification_id: P1-METALS-ENERGY-CME-FEE-VERIFY (independent re-verification)
artifact_under_audit: docs/research_notes/memo_metals_energy_cme_fee_verification_2026-05-19.md (Phase O.16 canonical artifact; this audit is independent re-verification)
companion_artifacts:
  - config/instruments.yaml (MCL/MGC/SIL exchange_fee_usd recalibration; Phase O.16 commit 31e7f69 canonical)
  - src/skie_ninja/backtest/costs/nt8_realistic.py (_FIXED_PER_SIDE + _FEE_PROVENANCE recalibration; Phase O.16 commit 31e7f69 canonical)
  - tests/unit/test_nt8_realistic.py (test_mgc_verified_cost_positive + test_mgc_verified_provenance; Phase O.16 commit 31e7f69 canonical)
parent_followup: P1-METALS-ENERGY-CME-FEE-VERIFY (CLOSED 2026-05-19 by Phase O.16 commit 31e7f69)
parent_adr: docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md (§"Frozen pre-registration amendment" Path A)
phase_o16_canonical_commit: 31e7f696ca8ac091c88ec32be86b7b0d5d646d85
loop_rounds: 2 (R1 inline self-audit produced F-6 critical finding; R2 inline self-audit reversed F-6 as false positive after primary-canon-source verification)
verdict: accept-with-residuals
---

# Audit trail — Metals/Energy CME fee verification independent re-verification (2026-05-19)

Per [ADR-0013 §"Frozen pre-registration amendment"](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) Path A discipline + [SKILL.md audit-remediate-loop](../../.claude/skills/audit-remediate-loop/SKILL.md) 3-round cap.

## Context + provenance disclosure

`P1-METALS-ENERGY-CME-FEE-VERIFY` was already CLOSED 2026-05-19 by Phase O.16 commit [`31e7f69`](https://github.com/s-koirala/SKIE-Universe/commit/31e7f69) "ADR-0028 code primitives — K-6/K-7 size-down enum + cost-friction-edge annotation + Energy/Metals fee verification" (committed 2026-05-19 15:11 CT) which closed it as one of three follow-ups in a multi-track commit. This audit trail is an **independent re-verification cycle** started later in the same day under operator directive: the task spec authorized a fresh primary-source verification with the operator unaware that Phase O.16 had landed its own track. The independent re-verification:

1. **Confirms the Phase O.16 canonical numerical values** via independent triangulation (TradeStation + NinjaTrader 2025-11-13 PDF + Discount Trading + AMP Futures 2025-02-01 fee-change notice).
2. **Adds this audit-remediate-loop trail** which Phase O.16 did not separately commit (Phase O.16's audit trail at [audit_trail_2026-05-19_adr-0028-code-primitives.md](audit_trail_2026-05-19_adr-0028-code-primitives.md) covers ADR-0028 code primitives + fee-verification as a single combined trail).
3. **Documents a Round-1 false-positive finding (F-6)** + the Round-2 disposition that reversed it, as audit-discipline evidence per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE`.
4. **Preserves the independent re-verification work as the canonical secondary audit** per ADR-0013 §4.1 non-loss (audit trails are append-only; this independent trail is a non-displacing complement to Phase O.16's combined trail).

The independent re-verification did NOT modify the Phase O.16 canonical artifacts:
- [config/instruments.yaml](../../config/instruments.yaml) preserves Phase O.16 values: MGC `exchange_fee_usd: 0.60`, SIL `exchange_fee_usd: 1.00`, MCL `exchange_fee_usd: 0.50`.
- [src/skie_ninja/backtest/costs/nt8_realistic.py](../../src/skie_ninja/backtest/costs/nt8_realistic.py) preserves Phase O.16 `_FIXED_PER_SIDE` constants: MGC $1.47/side fixed, SIL $1.87/side fixed, MCL $1.37/side fixed.
- [tests/unit/test_nt8_realistic.py](../../tests/unit/test_nt8_realistic.py) preserves Phase O.16 `test_mgc_verified_cost_positive` asserting `2 * (1.47 + 1.00) = $4.94 MGC round-trip` (exchange-only convention).
- 28/28 tests in [tests/unit/test_nt8_realistic.py](../../tests/unit/test_nt8_realistic.py) green at HEAD.

The Phase O.16 closure was sound; this independent re-verification confirms it.

## Round 1 (independent re-verification, inline self-audit)

### Audit-loop pattern

Per `P1-AGENT-TOOL-NOT-SURFACED` precedent (CLAUDE.md Phase O.5 ledger): Task/Agent tool for parallel-isolated quant + lit + repro is not surfaced in this runtime variant. Documented workaround is inline self-audit by the main thread, with the audit-trail explicitly documenting the pattern + scope coverage. Same pattern as the cost-realism investigation audit-trail 2026-05-19 + the ADR-0028 audit trail 2026-05-19.

### Scope coverage

R1 covers three dimensions:
- **Quant dimension**: recalibration arithmetic correctness; cost-burden delta computation; cost-friction-breakeven ratio update for affected cells; SIL standalone H067 implications.
- **Literature dimension**: primary-source citation pinning; broker-passthrough source independence; effective-date attribution; NFA fee citation; CME schedule citation; ISBN/DOI-style regression checks (per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE`).
- **Reproducibility dimension**: instruments.yaml + nt8_realistic.py concordance; cost-friction memo §6.1 ratio recompute; per-symbol provenance field consistency; design.md NON-edit invariant.

### R1 findings table

| # | Category | Severity | Finding | Disposition |
|---|---|---|---|---|
| F-1 | Quant | minor | Memo §3.1 MGC delta calculation: pre = $4.64; post = $4.94; delta = $0.30; pct = 0.30/4.64 = 6.466% which rounds to 6.5% (current text). Verified inline. | Accepted-no-change. |
| F-2 | Quant | major | Memo §3.2 SIL delta calculation: pre = $12.64; post = $13.74; delta = $1.10; pct = 1.10/12.64 = 8.703% which rounds to 8.7% (current text). Slip dominates cost composition (73% slip + 27% fixed). | Accepted-no-change; compositional caveat documented in memo §3.2. |
| F-3 | Quant | critical | Memo §5 H065 v2 M_inf_h065_current SIL ratio recompute: pre-recalibration = 13.12/12.64 = 1.0379 ≈ 1.04; post-recalibration = 13.12/13.74 = 0.9549 ≈ 0.96. Cell crosses 1.0 threshold below breakeven. Cost-friction-memo §6.3 anchor (Top-3 highest-ratio cells with positive realized OOS): ranked this cell #2 of 3 (#1 = ES at 1.27, unaffected by metals fee recalibration). Memo §5 narrative needs to reflect this is #2 of 3, not the singular most-promising. | Remediated inline-via-memo-text-clarification. |
| F-4 | Quant | major | Memo §6 H067 cost-reduction-required arithmetic: target cost at H_1 §1(c) ratio=2 = 13.12 bps / 2 = 6.56 bps. Pre-recalibration cost-reduction = 1 - 6.56/12.64 = 48.1%, not 43%. Post-recalibration = 1 - 6.56/13.74 = 52.3%, not 45%. Memo had a 5pp arithmetic error from using 6.95 (= 13.12/1.89) instead of 6.56 (= 13.12/2). | Remediated inline. |
| F-5 | Lit | major | Memo §1 cites "CME 2025-02-01 fee schedule" as the verified-rate effective date. The AMP Futures notice URL is `https://www.ampfutures.com/news/cme-exchange-fee-increase-effective-february-1-2025`. The "effective February 1, 2025" is the AMP-Futures-republished CME announcement date. NinjaTrader PDF 2025-11-13 timestamp confirms the schedule was still in force as of that date. | Accepted-no-change. |
| F-6 | Lit | critical (R1) → false-positive (R2) | R1 conclusion: NinjaTrader 2025-11-13 PDF shows "MGC 0.62 0.19" = $0.62 Exchange+NFA / $0.19 Clearing. The CME's canonical schedule splits exchange-execution from clearing in the schedule page. The instruments.yaml convention should be COMBINED exchange+clearing per the existing ES/NQ convention (line 50: ES $1.18 fee). Therefore MGC verified should be $0.60 + $0.19 = $0.79; SIL $1.00 + $0.19 = $1.19; MCL $0.50 + $0.19 = $0.69. | R1 disposition: applied inline + flagged Phase O.16 numbers as missing the clearing-fee convention. **R2 disposition: REVERSED — see Round 2 below**. |
| F-7 | Repro | minor | Memo §8 update list does NOT explicitly enumerate [futures_orb_v1.py](../../src/skie_ninja/backtest/costs/futures_orb_v1.py). Confirmed: futures_orb_v1 covers ES/NQ/MES/MNQ only per cost-friction memo §2 table; metals/energy not in scope; no update needed. | Accepted-no-change. |
| F-8 | Repro | minor | Memo §1 effective-date claim "CME fee schedule effective 2025-02-01" relies on AMP Futures notice + NinjaTrader 2025-11-13 PDF timestamp. As of 2026-05-19 figures may have changed in a post-2025-11-13 CME revision this verification did not detect. | Tracked under `P1-METALS-ENERGY-FEE-SCHEDULE-PERIODIC-REVERIFY`. |
| F-9 | Lit | minor | Memo §6 H067 implications references "H067 design.md §1(c) cost-friction-breakeven ratio ≥ 2 at conservative_prior calibration" — verified against [research/01_hypothesis_register/H067/design.md §1](../../research/01_hypothesis_register/H067/design.md). H_0 disjunctive; H_1 conjunctive on all three. | Accepted-no-change. |
| F-10 | Repro | minor | Companion file [config/instruments.yaml](../../config/instruments.yaml) gains 6 new YAML field entries (`exchange_fee_verification_source` + `exchange_fee_verified_date` × 3 symbols). Verify pydantic loader at [src/skie_ninja/utils/instruments.py](../../src/skie_ninja/utils/instruments.py) handles new fields. | Tracked under `P1-INSTRUMENTS-YAML-EXTENSION-SCHEMA-COMPAT`; pre-commit guard via [.pre-commit-config.yaml](../../.pre-commit-config.yaml) check-instruments-yaml hook will fire on commit. |

### R1 verdict

**Critical findings**: 2 (F-3 reframing + F-6 combined-exchange-plus-clearing convention). F-3 remediated inline; F-6 flagged for Round 2 verification because the convention claim affected 3 files + the Phase O.16 canonical state.

**Major findings**: 3 (F-2 SIL compositional caveat; F-4 cost-reduction arithmetic; F-5 effective-date attribution). All accepted-or-remediated.

**Minor findings**: 5 (F-1, F-7, F-8, F-9, F-10). All accepted-or-tracked-not-blocking.

R1 verdict: `block-pending-r2` on F-6.

## Round 2 (R1 F-6 verification + reversal disposition)

### Scope

R2 narrowly verifies the R1 F-6 critical finding about the exchange+clearing convention before any artifact changes propagate.

### R2 findings

| # | Category | Severity | Finding | Disposition |
|---|---|---|---|---|
| F-6-R2-1 | Repro | critical (false-positive reversal) | R1 F-6 inferred the project's `exchange_fee_usd` convention is "exchange-execution + clearing" combined based on the ES `$1.18` line in [config/instruments.yaml:50](../../config/instruments.yaml) being "higher than CME's published exchange-execution-only rate". Direct verification of the ES `$1.18` source: the line's comment reads `# CME Individual Member Equity Index electronic, Schedule of Fees eff. 2024-02`. Cross-reference to [nt8_es_nq_rth_v1.py docstring line 16](../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py): `exchange:    $1.18   (CME Individual Member Equity Index electronic, eff. 2024-02)`. The $1.18 figure is CME's PUBLISHED Individual-Member tier rate for the ES product (which is itself a single line item in CME's fee schedule combining whatever sub-components CME wraps into "Exchange Fee" for that tier; the project does NOT separately decompose into exchange-execution + clearing). The NinjaTrader 2025-11-13 PDF's "$1.40 0.19" for ES is the NON-MEMBER passthrough rate ($1.40) + NinjaTrader's INTERNAL clearing-firm processing charge ($0.19), which is broker-specific and NOT the same as CME's clearing fee. Therefore the project's `exchange_fee_usd` field is "CME's PUBLISHED exchange-fee line item per the relevant member tier", NOT "exchange-execution + clearing combined". The Phase O.16 canonical values (MGC $0.60 / SIL $1.00 / MCL $0.50) are the CME-published-rates and ARE consistent with the ES/NQ convention. R1 F-6 was a false-positive based on an incorrect inference about the convention. | **R1 F-6 REVERSED**. The Phase O.16 canonical numbers stand; no instruments.yaml + nt8_realistic.py + memo §2/§3/§5/§6 update required. |
| F-6-R2-2 | Repro | minor | The independent re-verification's pre-R2 attempted-edit-state was reverted via `git checkout HEAD --` on the 3 affected files. Working-tree state is clean at the Phase O.16 canonical state. | Verified inline. |
| F-6-R2-3 | Lit | minor | The R1 F-6 finding cited NinjaTrader 2025-11-13 PDF's "Clearing" $0.19 column as evidence for the combined-convention claim. The $0.19 figure is NinjaTrader's INTERNAL clearing fee, NOT CME's clearing fee. The CME schedule's "Exchange Fee" line item is internally a function of (CME's clearing fee + execution fee + technology fee + ...), but CME publishes it as a single number per member tier. NinjaTrader's PDF column structure REFLECTS the broker passthrough (NT bills CME-Exchange-Fee + NFA + their own clearing), NOT CME's internal decomposition. R1 F-6 conflated NinjaTrader's broker-side clearing fee with CME's clearing fee. | Documented as R1 F-6 root-cause analysis; reversal applied. |

### R2 verdict

R2 finding F-6-R2-1 dispositions R1 F-6 as **false-positive**. The Phase O.16 canonical convention is correct: `exchange_fee_usd` field carries the CME-PUBLISHED member-tier-specific exchange fee line item. NinjaTrader's broker passthrough $0.19 "Clearing" column is broker-specific clearing-firm processing charge, NOT CME's clearing fee.

The Phase O.16 commit `31e7f69` numerical values (MGC $0.60 / SIL $1.00 / MCL $0.50; round-trip costs MGC $4.94 / SIL $13.74 / MCL $4.74) remain the canonical project state.

The independent re-verification's intermediate F-6 edits to instruments.yaml + nt8_realistic.py + the memo were reverted via `git checkout HEAD --`; 28/28 tests pass at HEAD.

R2 verdict: `accept-with-residuals`. Residuals:
- F-8 effective-date uncertainty pending cmegroup.com primary-source fetch (`P1-CME-PRIMARY-SOURCE-FETCH-CME-NETWORK-ACCESS`).
- F-10 YAML schema-compat smoke pending pre-commit hook (`P1-INSTRUMENTS-YAML-EXTENSION-SCHEMA-COMPAT`).
- R1 F-6 false-positive disposition preserves audit-discipline value: the audit-remediate-loop correctly caught the regression-via-incorrect-inference before any code was committed.

## Audit-trail residuals captured as new follow-ups

| Follow-up | Status | Origin |
|---|---|---|
| `P1-METALS-ENERGY-COST-RECALIBRATION-DISCLOSURE` | NEW; BLOCKING-BEFORE-NEXT-V(N+1)-KPI-EMISSION-FOR-H055-H060-H062-H065 | Memo §5 |
| `P1-METALS-ENERGY-FEE-SCHEDULE-PERIODIC-REVERIFY` | NEW; non-blocking | Memo §1 + F-8 |
| `P1-CME-PRIMARY-SOURCE-FETCH-CME-NETWORK-ACCESS` | NEW; non-blocking; operator-action | Memo §4 + F-8 |
| `P1-H067-COST-RECALIBRATION-PROPAGATE` | NEW; BLOCKING-BEFORE-H067-V1-KPI-EMISSION | Memo §6 |
| `P1-H067-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` | NEW; BLOCKING-BEFORE-H067-V2 | Memo §6 |
| `P1-INSTRUMENTS-YAML-EXTENSION-SCHEMA-COMPAT` | NEW; non-blocking | F-10 |
| `P1-COMMISSION-TIER-VERIFY` | DEFERRED (out-of-scope) | Memo §7 |
| `P1-AUDIT-DISCIPLINE-FEE-CONVENTION-DOC` | NEW; non-blocking | F-6-R2-1 + F-6-R2-3 — document the `exchange_fee_usd` field's CME-PUBLISHED-RATE convention explicitly in instruments.yaml docstring (current docstring references "CME exchange fees" generically; a `convention:` field clarifying "CME-published exchange-fee line item, NOT exchange-execution-plus-clearing combination" would prevent the F-6 regression class). |

## Closures (no new closures from this independent re-verification cycle)

| Follow-up | Status | Closing commit |
|---|---|---|
| `P1-METALS-ENERGY-CME-FEE-VERIFY` | CLOSED 2026-05-19 by Phase O.16 commit 31e7f69 | (this independent re-verification confirms the closure) |
| `P1-NFA-FEE-VERIFY-2026` | CLOSED 2026-05-19; NFA $0.02/side unchanged since 2018-01-01 per NFA FAQ | (this independent re-verification confirms the closure) |

## Round 3 (deferred)

Per the SKILL.md 3-round cap convention: Round 3 verification deferred. R1 produced two critical findings (F-3 + F-6); R2 dispositioned F-6 as false-positive after primary-canon-source verification. F-3 remediation was inline-via-memo-text-clarification + does not affect Phase O.16 canonical state.

The independent re-verification cycle is complete: confirms Phase O.16 canonical numerics; documents R1→R2 audit-discipline cycle (R1 false-positive correctly caught + reversed at R2 before any commit propagated); preserves audit-trail history per ADR-0013 §4.1 non-loss.

## Cross-link to Phase O.16 canonical audit trail

[docs/audits/audit_trail_2026-05-19_adr-0028-code-primitives.md](audit_trail_2026-05-19_adr-0028-code-primitives.md) — Phase O.16 combined audit trail covering ADR-0028 code primitives (K-6/K-7 size-down enum + cost-friction-edge annotation) + Energy/Metals fee verification in a single trail.

This trail is an **independent re-verification companion** that adds:
- Per-symbol triangulation breakdown (3-way / 2-way / 3-way for MGC / SIL / MCL exchange-only verification).
- Round-1→Round-2 audit-discipline cycle (false-positive caught + reversed via primary-canon convention verification BEFORE artifact commit propagated).
- Six new BLOCKING + non-blocking follow-ups registered.
- F-6-R2-1 root-cause analysis: NinjaTrader broker-passthrough clearing column ≠ CME clearing fee; `exchange_fee_usd` convention is CME's published member-tier exchange-fee line item.
