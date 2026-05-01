---
title: H053 power-calibration source — option 3 elected (Databento pilot rejected)
date: 2026-04-30
type: addendum
status: live
binds: research/01_hypothesis_register/H053/design.md §9 (power calibration)
binds_data_requirements: research/01_hypothesis_register/H053/data_requirements_H053_2026-04-28.md §"Pre-IS pilot window (for §9 power calibration)"
audit_loop: docs/audits/audit_trail_2026-04-30_h053-power-calibration-addendum.md
git_head_at_authoring: edf37a4
---

# H053 power-calibration source — option 3 elected (Databento pilot rejected)

## Purpose

User decision 2026-04-30: reject Databento pilot-window purchase for ES + NQ 2010-2014 1-min substrate (`P1-H053-PILOT-WINDOW-DATABENTO`). Elect the **pre-registered option 3** at [data_requirements_H053_2026-04-28.md:93-99](data_requirements_H053_2026-04-28.md): pin `ar1_rho_pilot = 0.0` and `excess_kurtosis_pilot = 3.0` (Gaussian iid conservative prior).

This addendum records the user-decision act. The election does not amend the H053 design — option 3 was enumerated and bound at pre-registration (2026-04-28). No successor hypothesis ID required.

## User decision (verbatim, 2026-04-30)

> *"we do not need 2010-2014 data. it is obsolete for our purposes. we have 2016+."*

The decision binds the §9 power-calibration source to option 3. Option 1 (Databento purchase) and option 2 (prototype-tier 5-min substrate intersected with pre-2015 data) are both unavailable per the user's framing.

**Editorial clarification on "2016+":** the binding H053 IS-window per [data_requirements_H053_2026-04-28.md:38](data_requirements_H053_2026-04-28.md) is `2015-01-01 → 2025-12-{03,20}`. The user's "2016+" is a colloquial reference to the project's existing roll-adjusted substrate (which begins 2015) — not a new IS-window restriction. The IS-window is unchanged by this addendum.

## Pinned anchors

Per [data_requirements_H053_2026-04-28.md:99](data_requirements_H053_2026-04-28.md) verbatim:

| Anchor | Value | Rationale |
|---|---|---|
| `ar1_rho_pilot` | `0.0` | Gaussian iid conservative prior — assumes zero serial correlation in the predictand return series |
| `excess_kurtosis_pilot` | `3.0` | Gaussian iid conservative prior — Gaussian kurtosis = 3 |
| `variance_formula` | `lo2002_hac_adjusted` | Unchanged from design.md §9 |

These are the **binding pre-registered values** for any H053 walk-forward run that proceeds under this addendum. Pinning at the start of `running` is binding per design.md §9.

## Pre-registered consequences

Per [data_requirements_H053_2026-04-28.md:99](data_requirements_H053_2026-04-28.md) verbatim:

> *"The result of `s_min` under this conservative assumption is an upper bound on the true `s_min` for power; an underpowered run under this prior is genuinely underpowered."*

**Bound-direction erratum** (filed as follow-up `P1-H053-DATA-REQS-LINE-99-DIRECTION-ERRATUM`): the data_requirements.md:99 phrase "upper bound on the true `s_min`" is directionally reversed. iid Gaussian (ρ=0, κ_excess=0) minimises Lo 2002 §III HAC-adjusted Sharpe variance (no AR-induced spectral inflation factor; no kurtosis correction term). Smaller variance ⇒ smaller MDE for a given power level ⇒ option-3 `s_min` is a **lower bound** (best case under the most-favorable distributional assumption) on the true `s_min`, not an upper bound. The operational consequence claimed by the same sentence — *"an underpowered run under this prior is genuinely underpowered"* — is correct (failing to meet the easiest-possible `s_min` implies failing to meet any realistic-distribution `s_min`); only the bound-direction terminology is reversed in the source pre-reg. This addendum reproduces the data_requirements text verbatim above, then states the corrected framing below; a future erratum addendum to the data_requirements companion will fix the source text.

Operationally this means:

1. **`s_min` calculated from option-3 pin is a *lower* bound on the true `s_min` (best case for power).** Lo 2002 §III HAC-adjusted Sharpe variance under iid Gaussian (ρ=0, κ_excess=0) is the *smallest* possible for a given sample. Any departure from iid Gaussian inflates variance, raises `s_min`, and reduces power. The option-3-derived `s_min` is therefore conservative *against the run being declared successful* — underpowered under option 3 implies the design is genuinely underpowered for any realistic intraday return distribution (intraday futures returns are documented as positively autocorrelated and leptokurtic per Andersen-Bollerslev-Diebold-Labys 2003 + Andersen-Bollerslev 1998 IER).
2. **§10.1 disposition deviation note.** Per design.md §10.1, any arm whose realized OOS sample fails to meet `n_required_for_power_80` records `archive(null, underpowered)`. Per design.md §8, the SPA slot is consumed by that null record (not freed for a fourth arm). Under option 3, per [data_requirements_H053_2026-04-28.md:99](data_requirements_H053_2026-04-28.md) verbatim binding ("document the conservative-assumption deviation in §10.1 disposition"), the §10.1 disposition record carries the deviation note `pilot-conservative-prior` — flagging that the underpower verdict was assessed under iid Gaussian and may not transfer to the empirical return distribution. This is a §10.1 disposition note (pre-reg-bound by data_requirements.md:99), not a §10.2 annotation (which would be a design amendment).
3. **Disposition note persists into `ReproLog`.** Within the §11.2 prereq-19 power-calibration JSON sidecar (`ReproLog.power_calibration_{run_id}.json`) that the design already creates at run start, the deviation is captured as a sub-field `pilot_source: "option_3_conservative_iid_gaussian"`. This is a sub-field within an already-pre-registered ReproLog file, not a new top-level ReproLog field.

**Solver implementation prerequisite still open.** [design.md §11.2 prereq 19](design.md) (power-calibration solver `inference/power.py::required_n` writing the `ReproLog.power_calibration_{run_id}.json` sidecar at run start) is a `designed → running` prerequisite that this addendum does NOT close. The solver implementation is a Cycle-7 deliverable per [plan/h053_buildout_2026-04-28.md](../../../plan/h053_buildout_2026-04-28.md). H053 is not unblocked for `running` purely by this addendum; it is unblocked only after Cycle 7 completes.

**Re-election clause.** If a fold-disjoint pre-IS pilot window becomes available later (e.g., a Databento purchase in a later phase), reactivating option 1 mid-program would be a re-pinning of `ar1_rho_pilot` / `excess_kurtosis_pilot` from the option-3 values. Per design.md §0/§7 (any change requires a successor hypothesis ID) and §9 ("Pinning at the start of `running` is binding; refining on IS is pre-registered as forbidden"), such a mid-program re-election would constitute a successor hypothesis ID. The conservative interpretation: option 3 is binding for this iteration of H053; option 1 reactivation requires H053'.

## Buildout plan consequence

[plan/h053_buildout_2026-04-28.md:54](../../../plan/h053_buildout_2026-04-28.md) §Cycle 7 lists `P1-H053-PILOT-WINDOW-DATABENTO` as a Cycle-7 prerequisite. This addendum closes that follow-up. Cycle 7 no longer waits on external data acquisition; the option-3 pin is structurally satisfied by this addendum. The buildout-plan row is amended in the same commit that lands this file.

## Follow-up closures

| Follow-up | Status | Closure evidence |
|---|---|---|
| `P1-H053-PILOT-WINDOW-DATABENTO` | **CLOSED 2026-04-30** | This addendum + user-decision verbatim above. No further data acquisition required for §9 power calibration. |
| `P1-LIT-REVIEW-H053-STALE-ENTRY-RESOLVE` | **CLOSED 2026-04-30** | Bundled in the same audit-remediate-loop as this addendum; lit-review entry at [research/00_literature_review/lit_intraday-ES-NQ-signals_2026-04-15.md:272](../../../research/00_literature_review/lit_intraday-ES-NQ-signals_2026-04-15.md) replaces the stale Sovereign-CDS framing with the actual H053 anchor set. |

## New follow-ups filed by this audit-remediate-loop

| Follow-up | Severity | Description |
|---|---|---|
| `P1-H053-DATA-REQS-LINE-99-DIRECTION-ERRATUM` | minor | data_requirements_H053_2026-04-28.md:99 phrasing "upper bound on the true `s_min`" is directionally reversed; should read "lower bound (best-case)". Operational consequence sentence is correct. Fix via a future erratum addendum to the data_requirements companion. |
| `P1-H053-AB1998-CITATION-DISAMBIGUATE` | minor | The lit-review remediation initially cited Andersen-Bollerslev 1998 *Deutsche Mark-Dollar Volatility* (JF, DOI [10.1111/0022-1082.85732](https://doi.org/10.1111/0022-1082.85732)); the design.md frontmatter cites Andersen-Bollerslev 1998 *Answering the Skeptics* (IER, DOI [10.2307/2527343](https://doi.org/10.2307/2527343)) — two distinct AB1998 papers under the same author-year tag. The remediated lit-review entry now cites only the IER paper (matching design.md frontmatter); a future review may decide whether to additionally cite the JF paper as a separate-role anchor. |

## Audit-remediate-loop

This addendum + the lit-review remediation (`P1-LIT-REVIEW-H053-STALE-ENTRY-RESOLVE`) + the buildout-plan amendment go through a single Round-1 audit-remediate-loop with parallel quant-auditor + literature-check + reproducibility-verifier subagents. Trail: [docs/audits/audit_trail_2026-04-30_h053-power-calibration-addendum.md](../../../docs/audits/audit_trail_2026-04-30_h053-power-calibration-addendum.md).

## References

### Project-internal

- [research/01_hypothesis_register/H053/design.md](design.md) §9 (Stopping rule + power) — binds the pilot-anchor pinning convention.
- [research/01_hypothesis_register/H053/data_requirements_H053_2026-04-28.md](data_requirements_H053_2026-04-28.md) §"Pre-IS pilot window (for §9 power calibration)" — enumerates options 1, 2, 3 at pre-registration.
- [plan/h053_buildout_2026-04-28.md](../../../plan/h053_buildout_2026-04-28.md) §Cycle 7 — amended in same commit to remove the closed follow-up.

### External

- Lo, A. W. (2002). "The Statistics of Sharpe Ratios." *Financial Analysts Journal* 58(4):36-52. [DOI 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453). §III HAC-adjusted Sharpe SE — the formula whose iid-Gaussian limit (`ρ=0, κ=3`) is what option 3 pins.
