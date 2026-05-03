---
title: ADR-0013 §3.1 amendment — Realized-OOS + Forward-Projection canonical-deliverable mandate; H053 KPI report card v3
date: 2026-05-03
type: audit_trail
status: complete (3 rounds; SKILL.md cap reached; verdict ACCEPT)
deliverables_landed:
  - docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md (UPDATED §3 + §3.1 + §3.1.1 + §3.1.2)
  - research/_templates/kpi_report_card_template.md (UPDATED with §"Realized OOS + Forward-Projection" mandatory section + frontmatter SHA fields + Winrate row)
  - CLAUDE.md (UPDATED §"KPI report card" with §3.1 mandate reference; added §"Phase F" entry)
  - research/01_hypothesis_register/H053/H053_kpi_report_v3.md (NEW; canonical first realization of §3.1)
  - research/01_hypothesis_register/H053/H053_kpi_report_v2.md (UPDATED with `superseded_by: H053_kpi_report_v3.md` + supersession notice block)
  - research/01_hypothesis_register/H053/stage.md (UPDATED with v3 transition row)
  - scripts/simulate_h053_v4_10k_2026.py (UPDATED with PW2004-on-level-series block-length selection + iid/stationary-bootstrap branch + q01/q99 quantile output + single-rng-seed-across-arms)
  - logs/simulate_10k_2026.log (UPDATED; re-run output with v4-Round-2 fixes)
loop_rounds: 3
verdict: accept
---

# ADR-0013 §3.1 amendment + H053 KPI report card v3 — audit-remediate-loop trail

## Context

Per the user's 2026-05-03 directive: **"the final deliverable of all hypothesis should be similar realized OOS and 2026 projections of strategies, in addition to metrics such as drawdowns, winrates, sharpes, etc."**

This amendment makes the realized-OOS-from-$10k + 1-year-forward-bootstrap-projection a **MANDATORY** part of every KPI report card per ADR-0013 §3 going forward. H053 KPI report card v3 is the canonical first realization.

## Round-1 — quant-auditor on the convention amendment package

- **agentId**: `a25a0ef3be6c0c4d1`
- **verdict**: `accept-with-remediation`
- **findings**: 11 (2 critical / 4 major / 5 minor)

| ID | Severity | Finding | Round-2 closure |
|---|---|---|---|
| F-CONV-1 | **critical** | Realized OOS Sharpe column conflated with CPCV-OOS-path-Sharpe distribution median (different statistics; same name) | **CLOSED** — v3 + template + ADR-0013 §3.1 item 1 rename to "Realized-path Sharpe†" with explicit footnote disambiguating from CPCV path-Sharpe distribution median |
| F-CONV-2 | **critical** | Cost-aware adjustment in v3 Operator-interpretation subtracts flat-dollar from compounded-equity projection — dimensionally inconsistent | **CLOSED** — flat-dollar cost-aware adjustment removed from v3; replaced with "Cost-aware projection: NOT YET RUN" + tracked under `P1-H053-COST-EMPIRICAL`. ADR-0013 §3.1 item 1 + template now FORBID flat-dollar cost-aware projections at horizon; correct form is per-session log-return drag (`r_t' = r_t - cost_per_session/equity_t`) inside the simulation loop |
| F-CONV-3 | major | Bootstrap block-length justification cites PW2004 on the LW2008 differential series; should run on per-arm LEVEL series | **CLOSED** — script re-run with `choose_block_length(arm_ret)` per arm on LEVEL series; recorded `block_length_pw2004` per arm in output. All 6 arms × symbols selected `block_length=1.0` → iid bootstrap is verified appropriate (post-hoc validation of the prior assumption). v3 + ADR-0013 §3.1 item 2 + template restated accordingly |
| F-CONV-4 | major | Per-arm RNG seed offsets in script (1043/1044/1045) vs ADR-0013 + template stating single seed=1042 | **CLOSED** — script removes per-arm offsets; single rng_seed=`_BOOTSTRAP_RNG_SEED` (1042) across all arms. v3 + ADR-0013 §3.1 item 2 + template forbid per-arm offsets |
| F-CONV-5 | major | Win-rate convention undocumented (W/(W+L+Z) vs W/(W+L)) | **CLOSED** — v3 + ADR-0013 §3.1 item 1 + template state W/(W+L+Z) as project canonical; report all 3 counts so readers can re-compute under W/(W+L) if preferred |
| F-CONV-6 | major | §3.1 H053-specific 100%-of-equity convention; doesn't accommodate H050 HMM-multi-bar / H051 pairs / H052a ORB / H052b 0DTE-premium | **CLOSED** — ADR-0013 §3.1.1 added with sizing-convention override table covering all 5 archetypes + amendable-by-extension clause |
| F-CONV-7 | minor | P(double)/P(<50%) uniformly 0% degenerate at 252 sessions for low-vol intraday strategies; need q01/q99 tail anchors | **CLOSED** — v3 + template + ADR-0013 §3.1 item 2 add q01/q99 columns alongside q05/q95 |
| F-CONV-8 | minor | No `simulation_log_sha256` / `simulation_script_sha256` in v3 frontmatter or §3.1 spec | **CLOSED** — both fields added to v3 frontmatter (5f92e1c1... / 59127e6304...) + ADR-0013 §3.1 item 5 + template frontmatter |
| F-CONV-9 | minor | `P1-FORWARD-PROJECTION-PRIMITIVE` follow-up scope ambiguous about fit-step ownership | **CLOSED** — ADR-0013 §3.1 lines 219-232 add explicit signature contract: `projection_summary(*, strategy_log_returns, n_paths, n_sessions, rng_seed, sizing_convention) -> ProjectionReport` with helpers list (equity_curve_from_log_returns, max_drawdown, iid_or_stationary_bootstrap_with_pw2004_block_length, projection_summary, apply_per_session_cost_drag) |
| F-CONV-10 | minor | Deferred-KPI annotation mechanism for `rules/quant-project.md` mandates not explicit | **CLOSED** — ADR-0013 §3.1.2 added: missing KPIs listed under §"Mandatory KPIs not yet computed" with tracked follow-ups satisfies the rules/quant-project.md "every backtest doc lists" mandate |
| F-CONV-11 | minor | Caveat block too generic on bootstrap-as-generative-model assumption; doesn't name regime-shift risk | **CLOSED** — ADR-0013 §3.1 caveat strengthened with explicit reference to Andrews 1993 *Econometrica* 61(4):821-856 on parameter-instability detection; forward max-DD distribution explicitly framed as lower bound on regime-conditional realized max-DD |

## Round-2 — remediation

All 11 findings closed inline:

1. ADR-0013 §3 + §3.1 amended with disambiguation language + cost-aware-form forbidance + winrate convention + provenance pinning + caveat strengthening
2. New §3.1.1 sizing-convention override table for non-H053 archetypes
3. New §3.1.2 deferred-KPI annotation mechanism
4. P1-FORWARD-PROJECTION-PRIMITIVE scope tightened with explicit signature contract
5. kpi_report_card_template.md updated with all the above + frontmatter SHA fields + Winrate row
6. CLAUDE.md §"KPI report card" gets new paragraph referencing §3.1 mandate; §"Phase F" entry added to §"Implemented infrastructure"
7. H053 KPI report card v3: Sharpe disambiguation + cost-aware-removal + q01/q99 columns + frontmatter SHA pinning + sizing convention declared
8. H053 v2 + stage.md updated additively (`superseded_by` reference to v3; v3 transition row appended to stage tracker)
9. scripts/simulate_h053_v4_10k_2026.py: `_bootstrap_2026_projection` rewritten to call `choose_block_length(log_returns)` on per-arm level series + iid/stationary-bootstrap branch + q01/q99 in output + block_length per arm recorded; per-arm RNG offsets removed
10. Script re-run on the same substrate (`bc06b4e1...`); all 6 arms × symbols selected `block_length=1.0`; iid bootstrap empirically validated as appropriate
11. v3 frontmatter SHAs updated to canonical re-run values: simulation_log_sha256=`5f92e1c12e95...`; simulation_script_sha256=`59127e6304080e1ab36...`

## Round-3 — quant-auditor verification

- **agentId**: `afb6e4f481b083015`
- **verdict**: `accept`
- **findings**: 13 (all minor, marked `verification-gap` indicating successful closure; no regressions)

Verifications:

| ID | Result |
|---|---|
| F-CONV-V3-1 | F-CONV-1 verified CLOSED — Sharpe disambiguation in v3 + template + ADR §3.1 item 1 |
| F-CONV-V3-2 | F-CONV-2 verified CLOSED — flat-dollar cost-aware removed; ADR forbids dimensionally-inconsistent form |
| F-CONV-V3-3 | F-CONV-3 verified CLOSED — `choose_block_length(log_returns)` on per-arm LEVEL series; output records `block_length_pw2004` |
| F-CONV-V3-4 | F-CONV-4 verified CLOSED — single rng_seed=1042 across all arms; per-arm offsets removed |
| F-CONV-V3-5 | F-CONV-5 verified CLOSED — W/(W+L+Z) convention applied consistently; v3 win-rates verified arithmetically (188/367=51.23%, 195/367=53.13%, 193/372=51.88%, 189/372=50.81%) |
| F-CONV-V3-6 | F-CONV-6 verified CLOSED — §3.1.1 sizing-convention table covers H050+H051+H052a+H052b+H053; amendable-by-extension explicit |
| F-CONV-V3-7 | F-CONV-7 verified CLOSED — q01/q99 columns added |
| F-CONV-V3-8 | F-CONV-8 verified CLOSED — frontmatter SHAs match canonical |
| F-CONV-V3-9 | F-CONV-9 verified CLOSED — signature contract documented |
| F-CONV-V3-10 | F-CONV-10 verified CLOSED — deferred-KPI mechanism explicit |
| F-CONV-V3-11 | F-CONV-11 verified CLOSED — Andrews 1993 cited |
| F-CONV-V3-12 | Numerical regression check: PASS. v3 numbers reconcile against re-run log line-by-line; all 6 PW2004 selections = 1.0 confirms iid bootstrap |
| F-CONV-V3-13 | Sanity check on W/(W+L+Z) arithmetic: PASS |

## Empirical observation (informational; surfaced by Round-2 re-run)

Round-2's PW2004-on-level-series re-run confirms **block_length=1.0 on every arm × symbol**. This validates the Round-1-pre-fix iid bootstrap as appropriate — the strategy log-return level series IS effectively serially uncorrelated (consistent with daily clearing + intraday-window-only execution). The F-CONV-3 fix did not change the substantive disposition; it changed the JUSTIFICATION from "borrowing the LW2008 differential's block_length" (logically wrong even when conclusion correct) to "running PW2004 on the level series directly" (logically correct AND empirically validates the same conclusion).

## Verdict

**accept**. All 11 Round-1 findings closed clean in Round-2; verified by Round-3 quant-auditor. The ADR-0013 §3.1 amendment + H053 KPI report card v3 package is canonical and load-bearing for all future hypothesis KPI report cards.

## Cross-references

- [ADR-0013](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3 + §3.1 + §3.1.1 + §3.1.2 (this commit's amendment surface)
- [research/01_hypothesis_register/H053/H053_kpi_report_v3.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v3.md) (canonical first realization)
- [research/01_hypothesis_register/H053/H053_kpi_report_v2.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v2.md) (preserved per ADR-0013 §4.1; superseded_by reference added)
- [research/_templates/kpi_report_card_template.md](../../research/_templates/kpi_report_card_template.md)
- [scripts/simulate_h053_v4_10k_2026.py](../../scripts/simulate_h053_v4_10k_2026.py)
- [logs/simulate_10k_2026.log](../../logs/simulate_10k_2026.log)
- [audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md](audit_trail_2026-05-03_h053-stage3-v3-leakage-clean.md) (Path B precursor)
- [audit_trail_2026-05-03_adr-0013-permanent-exploration.md](audit_trail_2026-05-03_adr-0013-permanent-exploration.md) (ADR-0013 itself)

## Residuals (tracked follow-ups; not blocking)

- `P1-H053-COST-EMPIRICAL` — cost-aware projection per the per-session-log-return-drag form (not flat-dollar at horizon)
- `P1-FORWARD-PROJECTION-PRIMITIVE` — refactor `equity_curve` + `max_drawdown` + `iid_or_stationary_bootstrap_with_pw2004_block_length` + `projection_summary` + `apply_per_session_cost_drag` into `src/skie_ninja/inference/projection.py` per the §3.1 signature contract
- `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD` — operator-aid dashboard aggregating §3.1 blocks across the strategy universe (per ADR-0013 §3.1 item 4)
- Per-hypothesis sizing-convention validation when H050/H051/H052a/H052b reach KPI-report-emitted: confirm the §3.1.1 override table holds operationally (vs. amendment needed)
