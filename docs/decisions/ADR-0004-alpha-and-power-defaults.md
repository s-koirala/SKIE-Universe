---
id: ADR-0004
title: Project-level defaults for alpha and target_power
status: accepted
date: 2026-04-15
decision-owner: Lead researcher
supersedes: none
related:
  - docs/templates/hypothesis_config.yaml
  - plan/buildouts/implementation-plan_2026-04-15.md §5
  - plan/buildouts/implementation-plan_2026-04-15.md §5.1
  - research/03_audits/ F-2-19
  - plan/buildouts/implementation-plan_2026-04-15.md §5 line 255 (F-3-1 follow-up)
---

# ADR-0004 — Project-level defaults for alpha and target_power

## Status

Accepted. Subject to Phase-1 follow-up F-3-1 ([plan §5 line 255](../../plan/buildouts/implementation-plan_2026-04-15.md)) which re-evaluates these defaults against realized gate behavior on the first cohort of hypotheses.

## Context

[CLAUDE.md §Parameter & Prompt Selection](../../CLAUDE.md) prohibits arbitrary thresholds and magic numbers: "Tunable values require empirical justification: grid/random/Bayesian search, CV, information criteria, or bootstrap CIs."

Audit finding F-2-19 flagged the template values `alpha: 0.05` and `target_power: 0.80` in [docs/templates/hypothesis_config.yaml](../templates/hypothesis_config.yaml) as conventional defaults with no in-repo empirical justification, which formally violates the rule unless adopted explicitly as a project-level convention with a traceable rationale and override path.

Two options exist for every hypothesis: (i) inherit a project-wide default, or (ii) set a per-hypothesis value justified in its design.md. Without a project-level convention, every hypothesis must re-derive these values, which is both wasteful and inconsistent across the hypothesis register used by the SPA / Romano-Wolf family tests ([ADR-0003](ADR-0003-spa-vs-romanowolf.md)).

## Decision

1. **Project default `alpha = 0.05`.** Adopted as a project-level convention aligned with:
   - [Benjamini-Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x), which uses 0.05 as the canonical per-test level against which FDR is controlled.
   - [Harvey, Liu, Zhu 2016 RFS](https://doi.org/10.1093/rfs/hhv059), which uses 0.05 as the per-test benchmark in the haircut-Sharpe framework for financial strategies — the closest published precedent to this project's universe-level multiple-testing problem.

2. **Project default `target_power = 0.80`.** Adopted as a project-level convention per [Cohen 1988](https://doi.org/10.4324/9780203771587), *Statistical Power Analysis for the Behavioral Sciences*, whose 0.80 convention has become the standard reference point in applied statistical power analysis.

3. **Both values are acknowledged as conventional, not empirically derived from this project's data.** They serve as defaults only. They are subject to Phase-1 follow-up F-3-1 which will re-examine whether realized false-discovery behavior on the first cohort justifies a project-specific calibration.

4. **Explicit override mechanism.** Any hypothesis `config.yaml` MAY set `alpha` and/or `target_power` to values other than the defaults above, provided the corresponding `design.md §1` motivates the override with either:
   - a primary-source citation tying the chosen value to the hypothesis's signal family, or
   - a pilot-power simulation (bootstrap or Monte Carlo) demonstrating the chosen value is required to detect the minimum-interesting effect at acceptable risk of type-I or type-II error.

   Without such justification in design.md, the gate ([plan §5](../../plan/buildouts/implementation-plan_2026-04-15.md)) rejects the hypothesis at pre-registration review.

## Consequences

- [docs/templates/hypothesis_config.yaml](../templates/hypothesis_config.yaml) `# justify:` comments on the two relevant lines are updated to cite this ADR directly.
- The project-wide gate family-level type-I rate remains 0.05 unless a future ADR supersedes this one.
- Phase-1 follow-up F-3-1 produces either (a) a calibrated project-specific alpha/power from realized gate data, which supersedes this ADR, or (b) a confirmation that the conventional defaults remain appropriate.
- Reviewers checking a hypothesis pre-registration can audit override decisions via design.md §1 rather than re-deriving defaults from scratch.

## Alternatives considered

- **Per-hypothesis derivation only (no project default).** Rejected: produces inconsistent family-level type-I rate, invalidating the SPA / Romano-Wolf family test which assumes a common alpha across candidates ([ADR-0003](ADR-0003-spa-vs-romanowolf.md)).
- **Project default derived empirically from pilot data now.** Rejected at this stage: no gate-evaluated hypotheses exist yet from which to estimate realized false-discovery behavior. Deferred to F-3-1 once first cohort completes.
- **Stricter default (alpha = 0.01, power = 0.90).** Rejected as the initial default: raises the n_required bar beyond realistic intraday sample sizes for many Tier 2 / Tier 3 hypotheses before any empirical evidence that a stricter level is warranted. Can be adopted per-hypothesis via the override mechanism when a specific design motivates it.

## References

- [Benjamini-Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
- [Harvey, Liu, Zhu 2016 RFS](https://doi.org/10.1093/rfs/hhv059)
- [Cohen 1988](https://doi.org/10.4324/9780203771587)
- [ADR-0003](ADR-0003-spa-vs-romanowolf.md)
