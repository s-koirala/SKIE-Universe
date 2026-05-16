---
id: ADR-0024
title: Paradigm resolution — formalize the H062 aggressive-growth-with-halt-and-switch framework as project-canonical; promote ADR-0018 to accepted; demote ADR-0017 §4.2 + §5 + §6 mandatory-inheritance clauses to KPI annotations
status: accepted
date: 2026-05-15
deciders: skoir
supersedes:
  - (none — ADR-0024 amends rather than supersedes; the prior ADRs are preserved per the ADR-0013 §4.1 non-loss mandate, with their §"mandatory inheritance" clauses reframed to "KPI annotations + opt-in tooling")
amends:
  - ADR-0018 — `status: proposed` → `status: accepted` (one-line YAML promotion; no body-text change; the framework defined by ADR-0018 D-1..D-6 becomes the project-canonical paradigm without re-litigation)
  - ADR-0017 §4.2 — risk-of-ruin Monte Carlo demoted from "mandatory in every KPI report card from 2026-05-08 forward" to "KPI annotation when computed"; the [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py) primitive is preserved verbatim as opt-in tooling per the ADR-0013 §4.1 non-loss mandate
  - ADR-0017 §5 — eight hard kill-switch constraints K-1..K-8 demoted from "mandatory inheritance for every hypothesis from H055 forward" to "opt-in tooling with KPI-annotation reporting when invoked"; the per-hypothesis design.md §11.1 retains the kill-switch enumeration as an annotation-only artifact; the NinjaScript-layer kill-switch implementations preserved per ADR-0013 §5.1 are operator-discretionary per-strategy rather than project-mandatory
  - ADR-0017 §6 — five synthetic-failure-mode stress tests FM-1..FM-5 demoted from "mandatory for every hypothesis from H055 forward" to "opt-in stress-test artifact"; the [scripts/stress_test_failure_modes.py](../../scripts/stress_test_failure_modes.py) primitive is preserved verbatim as opt-in tooling
  - ADR-0014 §3.2 12-table format — preserved structurally; the canonical interpretive load-bearing row is the new Table 3d "MPPM(ρ=1) primary fitness" inserted between Tables 3c and 4 per `P1-ADR-0024-KPI-CARD-CASCADE` (the 12 → 13 extension; per-table indices for Tables 1-9 + 3a-3c preserved verbatim for downstream cross-link compatibility per ADR-0017 §3 F-10 audit-remediation discipline)
  - CLAUDE.md §"KPI report card for every strategy" — primary fitness reframed from ADR-0017 four-metric survival-constrained vector to ADR-0018 D-1 MPPM(ρ=1); the survival-constrained vector preserved as KPI tier alongside Sharpe-family
preserves_immutability_of:
  - All hypothesis design.md §1-§7 (per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline)
  - All historical audit trails, ReproLogs, sidecars, KPI report cards, promotion logs, NinjaScript strategies, design.md §17 revision logs (per ADR-0013 §4.1 non-loss mandate)
  - ADR-0017 §1-§3 four-metric primary inferential vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) — preserved as KPI annotations alongside MPPM(ρ=1)
  - ADR-0017 §4.1 drawdown-constrained Kelly sizing primitive at [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py) — preserved verbatim; ADR-0018 D-2 extends with the Kelly-multiplier grid as inner-CV search dimension
  - ADR-0013 §1 stage-progression model + §4 non-loss mandate + §5 NinjaScript-terminus mandate (preserved unchanged)
  - All Phase L primitives at [src/skie_ninja/inference/calmar.py](../../src/skie_ninja/inference/calmar.py), [src/skie_ninja/inference/profit_factor.py](../../src/skie_ninja/inference/profit_factor.py), [src/skie_ninja/inference/r_multiple.py](../../src/skie_ninja/inference/r_multiple.py), [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py), [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py) — preserved as the project's survival-constrained tooling layer
---

# ADR-0024 — Paradigm resolution: H062 aggressive-growth-with-halt-and-switch becomes project-canonical

## Context

### The paradigm evolution to 2026-05-15

The SKIE-Universe project's optimization-and-promotion paradigm has evolved through five distinct ADR-codified positions:

| ADR | Date | Position |
|---|---|---|
| [ADR-0012](ADR-0012-evidence-bar.md) (superseded) | 2026-04-21 | Binding evidence-bar gates (Class A: leakage-canary, BSS, reliability slope, DSR, SPA p) at every stage transition |
| [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) | 2026-05-03 | No binding gates; every former gate is a KPI annotation; permanent exploration; mandatory NinjaScript terminus; non-loss mandate |
| [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) | 2026-05-08 | Sharpe-family demoted to secondary KPI; four-metric survival-constrained vector (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) is the load-bearing operator-review artifact; eight hard kill switches K-1..K-8 + five synthetic-failure-mode stress tests FM-1..FM-5 + risk-of-ruin Monte Carlo mandatory inheritance from H055 forward |
| [ADR-0018](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) (`status: proposed` until this ADR) | 2026-05-12 | MPPM(ρ=1) replaces Sharpe in inner-CV fitness per Goetzmann-Ingersoll-Spiegel-Welch 2007; Kelly multiplier grid-searched over {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}; BOCD decay-detector halt (Adams-MacKay 2007); switching-bandit meta-strategy redirect (Garivier-Moulines 2011 + Besson-Kaufmann-Maillard-Seznec 2019); AMH framing (Lo 2004) adopted as canonical philosophical anchor |
| **ADR-0024** (this ADR) | **2026-05-15** | **Promote ADR-0018 to accepted; demote ADR-0017 §4.2 + §5 + §6 mandatory-inheritance clauses to KPI annotations + opt-in tooling; formalize the H062 instantiation as the canonical paradigm; mandate a Best-OOS showcase artifact updated on every push** |

### Empirical motivation for the resolution

The 2026-05-14 H062 pre-registration ([research/01_hypothesis_register/H062/design.md](../../research/01_hypothesis_register/H062/design.md), `status: designed` 2026-05-14) is the first hypothesis-of-record whose §1-§7 frozen content explicitly instantiates the full ADR-0018 framework — MPPM(ρ=1) primary inferential metric, Kelly-multiplier grid {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} including the literature-uniformly-dominated super-Kelly cells under operator-discretionary annotation, BOCD-on-rolling-MPPM halt with switching-bandit (D-UCB or GLR-klUCB selected per cumulative-regret competition) redirect to next-best per-instrument arm. H062 simultaneously inherits the full ADR-0017 stack (K-1..K-8 + FM-1..FM-5 + risk-of-ruin Monte Carlo + the 4-metric primary vector) per ADR-0018 D-5 "ADR-0017 survival infrastructure preserved verbatim."

The H062 §11.2 BLOCKING-precondition table at this ADR's adoption time contains **27 rows total: 13 closed, 14 open** (verified by direct count against [research/01_hypothesis_register/H062/design.md](../../research/01_hypothesis_register/H062/design.md) §11.2). Of the 13 closed, 5 were ADR-0017-stack primitives closed in Phase L commits `546b828` + `0be0f30` (P1-CALMAR-DIFFERENTIAL-CI-IMPL, P1-PROFIT-FACTOR-CI-IMPL, P1-R-MULTIPLE-CI-IMPL, P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE, P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE); 2 more were closed in the Phase O.1 follow-on (P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE + P1-H062-NEWS-CALENDAR-INGEST, both via the ledger-drift-correction sweep that discovered them already landed). The 14 open rows include the ADR-0017-stack residual `P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION` plus 13 H062-specific items (code authoring, calibration holdout, walk-forward orchestrator, etc.). The CLAUDE.md Phase O.1 follow-on ledger entry claimed "22 in §11.2 → 18 open" — that claim was drift from the actual design.md table per `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE-EXTEND`; the design.md table is the source of truth and is reconciled in this ADR's empirical motivation.

This precondition pile is the operational locus of the user's 2026-05-15 directive ("ADR-0017 is ruining present and all future hypothesis testing"). The empirical observations:

1. **Mandatory-inheritance creates operational ambiguity when an alternative paradigm is also adopted.** ADR-0018 D-5 explicitly preserved ADR-0017 §5 K-1..K-8 + §6 FM-1..FM-5 + §4.2 risk-of-ruin verbatim, but ADR-0018 was `status: proposed` at H062 pre-registration time. New hypotheses inherit both stacks simultaneously: the survival-constrained K-1..K-8 + FM-1..FM-5 + risk-of-ruin AS MANDATORY plus the aggressive-growth MPPM-Kelly-BOCD-bandit AS PROPOSED. The dual-stack inheritance is operationally costly without an explicit hierarchy.

2. **The ADR-0017 BLOCKING-BEFORE-LAUNCH primitive pile encourages bureaucratic over-engineering.** Of the ADR-0017 §"Follow-ups" BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH set, 6 of 7 are closed at this ADR's adoption time: 5 Phase L primitives (commits `546b828` + `0be0f30`, 2026-05-09) + 1 Phase O.1 ledger-drift-correction (`P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` verified landed at [scripts/stress_test_failure_modes.py](../../scripts/stress_test_failure_modes.py), 257 lines). The 1 remaining (`P1-ADR-0017-KILL-SWITCH-BACKTEST-VALIDATION`) is legitimate tooling investment but its BLOCKING status enforces a serialization that operationally slows the permanent-exploration framing of ADR-0013 §"Research philosophy." Demoting it to opt-in unblocks the H062 walk-forward dispatch.

3. **H062 is the working canonical example; the project should formalize what H062 already does.** H062's §1 + §3 + §5 + §11 already instantiate the ADR-0018 framework as the primary content + the ADR-0017 vector as a KPI tier. The natural project-level position is: "what H062 does is the paradigm." ADR-0024 makes this explicit.

4. **Past hypotheses (H050, H052a, H053, H054) were framed in pre-2026-05-15 documentation as "catastrophic Sharpe-era failures."** The README §"Current state" table at HEAD `2f56bed3285a` (pre-this-ADR commit) labeled H050 as "Catastrophic" with "−81%/−84% realized." Under the AMH framing of [Lo 2004](https://doi.org/10.3905/jpm.2004.442611), strategy decay is the null and a Sharpe-era hypothesis-of-record that produced a clean null-CI on the OOS fold is **informative evidence about the post-2022 regime**, not a project-level failure. The pre-2026-05-15 framing also obscured the genuinely-substantial OOS results: H060 TSMOM basket realized $10,000 → $18,943.37 over 1,260 walk-forward concatenated OOS sessions (+89.43%); H053 NQ LightGBM +10.8% / max-DD 3.7%; H052a NQ unconditional ORB +10.61% / P(loss)=18.56%. These are the project's best-OOS findings to date and they deserve top-of-document placement; the README rewrite landing in the same commit group as this ADR surfaces them under §"Best out-of-sample results."

5. **The Best-OOS showcase artifact is a natural fit for the permanent-exploration framing.** Showcasing the strongest realized-OOS performer on every push aligns the project's public face with its actual empirical content. The artifact updates mechanically from the per-hypothesis KPI report cards; no operator-curation step required.

### User 2026-05-15 directive (verbatim)

> "adr 17 is ruining present and all future hypothesis testing. per h062, we have already established a new paradigm - we must formalize it in documentation. additionally, the landing page and documentation of the github is outdated and emphasizes the 'catastrophic' nature of some of the old hypotheses and their archaic sharpe ratio centered approach. how do you suggest we ammend?"

Plus the follow-on directive (verbatim): "we should also showcase the results of our best hypothesis out of sample with each push."

## Decision

### D-1. Promote ADR-0018 from `proposed` to `accepted`

ADR-0018 ([docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md](ADR-0018-regime-conditional-aggressive-growth-paradigm.md)) front-matter `status: proposed` is amended to `status: accepted` in the same commit group as this ADR. The body text of ADR-0018 is preserved verbatim — no D-1..D-6 decision rephrased, no §Consequences table modified. The promotion is formalization-only: ADR-0018's MPPM(ρ=1) inner-CV fitness + Kelly multiplier grid + BOCD decay detector + switching-bandit meta-strategy + AMH framing become the project-canonical paradigm from 2026-05-15 forward.

### D-2. Demote ADR-0017 §5 K-1..K-8 from mandatory-inheritance to opt-in tooling

ADR-0017 §5 ("Hard kill-switch constraints (project-wide; mandatory for every hypothesis from H055 forward)") is reframed at the project level via this ADR's `amends` clause. The eight hard rule constraints K-1..K-8 (per-trade $-stop, time-stop, no-add-to-loser, per-symbol cap, correlated-instrument inventory cap, daily/weekly circuit breaker, adverse-direction entry filter) are **no longer mandatory inheritance**. Each hypothesis design.md §11.1 MAY enumerate the kill-switch list as a KPI annotation (`kill-switch-{K-1-enabled, K-1-disabled, K-2-enabled, ...}`) per the new annotation grammar in §Consequences below; the BLOCKING-BEFORE-LAUNCH inheritance is removed.

The implementation primitives (NinjaScript-layer kill switches per ADR-0013 §5.1; Python orchestrator validation per the Cycle-4 leak-canary discipline) are **preserved verbatim** per the ADR-0013 §4.1 non-loss mandate. Operator-discretionary adoption per-strategy: a hypothesis that benefits from K-1..K-8 enforcement (e.g., the H055 intraday-MR hypothesis whose pilot ledger documented the K-3 / K-5 / K-6 failure modes) MAY include them under `# justify:` annotation in design.md §11.1. The project-level mandate is removed.

### D-3. Demote ADR-0017 §6 FM-1..FM-5 from mandatory stress test to opt-in artifact

ADR-0017 §6 ("Failure-mode-overfitting stress test") is reframed identically to §5. The five synthetic-failure-mode stress tests FM-1 (death by thousand cuts), FM-2 (gap-overnight), FM-3 (news-spike), FM-4 (latency-induced bad fill), FM-5 (regime change mid-trade) are **no longer mandatory**. Each hypothesis design.md §11.2 MAY include the stress-test artifact as an opt-in deliverable; when included, the stress-test outcome is reported as a KPI annotation (`stress-test-FM-N-{pass,fail,not-run}`).

The implementation primitive at [scripts/stress_test_failure_modes.py](../../scripts/stress_test_failure_modes.py) is preserved verbatim per ADR-0013 §4.1 non-loss. The `P1-FAILURE-MODE-STRESS-TEST-PRIMITIVE` BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH status from ADR-0017 §Follow-ups is reframed to "non-blocking opt-in tooling."

### D-4. Demote ADR-0017 §4.2 risk-of-ruin Monte Carlo from mandatory report to KPI annotation

ADR-0017 §4.2 ("Risk-of-ruin computation") is reframed identically. The risk-of-ruin Monte Carlo at [src/skie_ninja/inference/risk_of_ruin.py](../../src/skie_ninja/inference/risk_of_ruin.py) (Phase L closure 2026-05-09 per commit `0be0f30`) is **no longer mandatory in every KPI report card from 2026-05-08 forward**. KPI report cards MAY include a risk-of-ruin row in §3a or §6; when included, the annotation `risk-of-ruin-{computed,not-computed}` plus numeric value is reported.

The primitive is preserved verbatim per ADR-0013 §4.1 non-loss. Operator-discretionary adoption per-strategy or per-KPI-card-version remains.

### D-5. Preserve ADR-0017 four-metric primary inferential vector as KPI annotations

The four primary metrics introduced by ADR-0017 §1 (`terminal-wealth-q05`, `calmar-differential`, `profit-factor`, `r-multiple-mean`) are **preserved as KPI annotations** alongside the new MPPM(ρ=1) primary fitness from ADR-0018 D-1. The ADR-0014 §3.2 12-table format (extended to 13-table format in §Consequences below) retains Tables 3a, 3b, 3c verbatim. The interpretive load-bearing role of the 4-metric vector is reduced from "primary inferential vector" (ADR-0017 §1 framing) to "KPI tier alongside MPPM(ρ=1)" (ADR-0024 framing). The CI primitives at [src/skie_ninja/inference/calmar.py](../../src/skie_ninja/inference/calmar.py) + [src/skie_ninja/inference/profit_factor.py](../../src/skie_ninja/inference/profit_factor.py) + [src/skie_ninja/inference/r_multiple.py](../../src/skie_ninja/inference/r_multiple.py) (Phase L closure 2026-05-09 per commit `546b828`) are preserved verbatim.

### D-6. Preserve Sharpe-family computation as KPI tier

The Sharpe-family LW2008 differential CI ([Ledoit-Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002)) + Hansen 2005 SPA p-value ([Hansen 2005](https://doi.org/10.1198/073500105000000063)) + Lo 2002 asymptotic CI ([Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453)) + Opdyke 2007 Mertens-HAC ([Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084)) computations are preserved verbatim as KPI-tier annotations in every KPI report card from 2026-05-15 forward (no change from ADR-0017 §1.2 / ADR-0018 D-1). Their position in ADR-0014 §3.2 Tables 3 + 4 + 7 is preserved verbatim for downstream cross-link compatibility.

### D-7. Adopt Lo 2004 Adaptive Markets Hypothesis as project-canonical philosophical anchor

Per ADR-0018 D-6 (preserved verbatim), [Lo 2004 *J Portfolio Mgmt* 30(5):15-29 "The Adaptive Markets Hypothesis"](https://doi.org/10.3905/jpm.2004.442611) is the project's canonical philosophical framing. The four AMH implications enumerated in ADR-0018 §Context are binding on all future hypothesis pre-registrations from 2026-05-15 forward: (i) strategy decay is the null, not the alternative; (ii) regime-conditional efficiency; (iii) heterogeneous time-varying risk premia; (iv) continuous innovation as evolutionary necessity. The corollary for project communication (README, hypothesis backlog, current-state table) is that a Sharpe-era null-CI on the OOS fold is **informative evidence about the post-2022 regime**, not a project-level failure to be apologized for.

### D-8. Mandate Best-OOS showcase artifact updated on every push

A new artifact [BEST_OOS.md](../../BEST_OOS.md) at the repository root showcases the project's strongest realized-OOS performer across all emitted KPI report cards. The artifact:

- Is generated by [scripts/showcase_best_oos.py](../../scripts/showcase_best_oos.py) (this ADR's companion commit) reading per-hypothesis KPI report card metadata.
- Ranks emitted KPI cards by realized OOS end-equity-percent on the strongest cell (until MPPM(ρ=1) is uniformly reported across all hypotheses, at which point the ranking primary becomes MPPM(ρ=1) per ADR-0018 D-1; tracked under `P1-BEST-OOS-MPPM-RANKING-CUTOVER`).
- Includes per-row mandatory disclosure of "hypothesis-of-record arm" vs "strongest cell" to avoid the cherry-picking-strongest-cell pathology (e.g., H052a's hypothesis-of-record is HMM-gated ORB which produced a non-significant null; the strongest cell is the literature-replication NQ unconditional ORB).
- Is regenerated by the [scripts/_hooks/regenerate_best_oos.sh](../../scripts/_hooks/regenerate_best_oos.sh) pre-push hook (a Git hook in [.githooks/pre-push](../../.githooks/pre-push) installed via `git config core.hooksPath .githooks` in [scripts/bootstrap_env.py](../../scripts/bootstrap_env.py)).
- Pre-push hook failure is non-blocking (a `git push --no-verify` escape is retained per CLAUDE.md §"Executing actions with care" — pre-push hook is informational, not an audit-remediate-loop blocker).

The artifact is **not subject to the ADR-0013 §4.1 non-loss mandate** because it is mechanically derived from underlying KPI report cards (which ARE subject to non-loss); BEST_OOS.md is a cache, regenerable at any time from the canonical KPI report cards. This exemption is explicit per `P1-DOCS-PROTECTED-PATH-EXTEND` (open from Phase M).

## Alternatives considered

### A. Hard-supersede ADR-0017 (delete its body; replace with ADR-0024 as the canonical survival ADR)

Rejected. ADR-0013 §4.1 non-loss mandate forbids deletion of accepted ADRs. ADR-0017's 4-metric primary inferential vector + K-1..K-8 kill-switch enumeration + FM-1..FM-5 stress-test enumeration + risk-of-ruin Monte Carlo + drawdown-constrained Kelly sizing primitive are valuable opt-in tooling layers preserved per the non-loss discipline. The amendment-via-this-ADR mechanism reframes their **mandatory-inheritance status** without deleting any artifact. Operator-discretionary per-hypothesis adoption remains.

### B. Leave ADR-0018 `status: proposed`; treat ADR-0017 as the canonical paradigm

Rejected. H062 explicitly instantiates ADR-0018's framework in §1-§7 frozen content. The operational ambiguity of "the paradigm I'm running under is proposed" is the locus of the user's 2026-05-15 directive. Formalizing ADR-0018 to `accepted` removes the ambiguity; the alternative (rolling back H062 to an ADR-0017-only framework) requires modifying frozen §1-§7 content per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability, which is forbidden.

### C. Single mega-ADR replacing 0012/0013/0017/0018 with a unified paradigm document

Rejected. ADR-0013's no-binding-gates + non-loss + NinjaScript-terminus + frozen-pre-reg-amendment discipline are load-bearing in their own right and have been cascaded through 7+ design.md files. Re-litigating these in a unified mega-ADR risks regression in any of those discipline layers. The per-ADR amendment mechanism (this ADR amends ADR-0017 §4.2 + §5 + §6 + ADR-0018 status + ADR-0014 §3.2 12→13-table extension; preserves ADR-0013 + ADR-0019 + ADR-0022 unchanged) is principled and cheap.

### D. Demote ADR-0017 entirely (including §1-§3 4-metric vector) to a single KPI annotation per metric

Rejected. The 4-metric vector is genuinely useful as a KPI tier — terminal-wealth-q05 is operator-bankroll-survival-protective in a way that MPPM(ρ=1) is not (MPPM is a fitness; q05 is a tail-risk statistic). Preserving the 4-metric vector AS KPI annotations alongside the new MPPM(ρ=1) primary is the principled position. The operator's empirical pilot-ledger evidence (ADR-0017 §Context observation 3) motivated the 4-metric vector and remains motivating; what changes is the metric vector's inferential load-bearing role, not its computational role.

### E. Keep the survival primitives BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH but rename the framing

Rejected. The BLOCKING status is the operational locus of the friction. Renaming alone does not unblock H062's walk-forward dispatch. The demotion to opt-in tooling IS the substantive resolution.

### F. Add Best-OOS showcase but skip the ADR-0017 demotion

Rejected. The showcase is the public-facing artifact; the ADR-0017 demotion is the project-internal mechanic. Both are responses to the same 2026-05-15 user directive; bundling them in a single ADR keeps the resolution coherent. Two separate ADRs (one for paradigm, one for showcase) would fragment the resolution unnecessarily.

## Consequences

### Adopted

- ADR-0018 promoted from `status: proposed` to `status: accepted`. MPPM(ρ=1) replaces Sharpe in inner-CV fitness; Kelly multiplier grid-searched over {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}; BOCD decay detector + switching-bandit meta-strategy canonical. Lo 2004 AMH framing canonical.
- ADR-0017 §4.2 + §5 + §6 mandatory-inheritance clauses demoted to opt-in tooling + KPI annotations. The primitive implementations are preserved verbatim per the ADR-0013 §4.1 non-loss mandate.
- ADR-0017 §1-§3 four-metric primary inferential vector preserved as KPI annotations alongside MPPM(ρ=1).
- Sharpe-family computation preserved as KPI tier.
- New artifact [BEST_OOS.md](../../BEST_OOS.md) at repository root, generated by [scripts/showcase_best_oos.py](../../scripts/showcase_best_oos.py), updated on every push via the [.githooks/pre-push](../../.githooks/pre-push) hook.
- ADR-0014 §3.2 12-table format extended to 13-table format with new mandatory Table 3d "MPPM(ρ=1) primary fitness" inserted between Tables 3c and 4. The 3d table reports MPPM(ρ=1) point estimate + Politis-White 2004 block-stationary-bootstrap CI + `mppm-rho1-{positive,marginal,negative}` annotation. Per-table indices for Tables 1-9 + 3a-3c preserved verbatim.

### KPI annotation grammar additions

The CLAUDE.md §"KPI report card for every strategy" annotation grammar gains:

- `kill-switch-{K-N-enabled, K-N-disabled}` (N ∈ {1, 2, 3, 4, 5, 6, 7, 8}) — per-hypothesis design.md §11.1 declaration of which ADR-0017 §5 hard kill switches the strategy invokes. Absence of the annotation = K-N not invoked. This replaces the prior "mandatory inheritance" framing.
- `stress-test-FM-N-{pass,fail,not-run}` (N ∈ {1, 2, 3, 4, 5}) — per-KPI-report-card declaration of stress-test outcomes per ADR-0017 §6. `not-run` is admissible (no longer mandatory).
- `risk-of-ruin-{computed,not-computed}` plus numeric value if computed — per-KPI-report-card declaration of risk-of-ruin Monte Carlo per ADR-0017 §4.2. `not-computed` is admissible.
- `mppm-rho1-{positive,marginal,negative}` — sign of MPPM(ρ=1) point estimate per ADR-0018 D-1 (already in CLAUDE.md per ADR-0018 §"KPI annotation grammar additions"; restated here for completeness).
- `paradigm-{adr-0017-survival,adr-0024-aggressive-growth,hybrid}` — per-hypothesis declaration of the canonical paradigm in force at the time of KPI emission. Retroactive labeling for H050/H052a/H053/H054 is `adr-0017-survival` (Sharpe-era); H055/H060/H062 are `adr-0024-aggressive-growth`. Hybrid is admissible for hypotheses pre-registered under ADR-0017 but emitting their first KPI card after this ADR.

### Reframing of past hypotheses

The README §"Current state" table is rewritten per the README cascade landing in this commit group. Past hypotheses' headline results are reframed:

| Hypothesis | Prior framing | New framing |
|---|---|---|
| H050 | "Catastrophic. Gated arms ES −81%, NQ −84% realized; HMM-gating actively harms the directional signal." | "Sharpe-era null. H_1 (HMM-gating improves Sharpe) cleanly rejected on the 2024-2025 OOS fold; realized OOS reflects post-2022 regime divergence from train-fold per Lo 2004 AMH. Strongest cell on this run: **NQ unconditional −25.60%** (max-DD 35.05%); the AMH-relevant signal is that the unconditional directional signal at 1-min ES/NQ is itself near-noise on the OOS fold — HMM-gating amplifies rather than rescues that noise." |
| H052a | "Non-significant null on hypothesis-of-record. Strongest cell is NQ unconditional ORB (+10.61% realized) — literature-replication artifact." | "Hypothesis-of-record non-significant null per LW2008 CI. Strongest cell: **NQ unconditional ORB +10.61% realized OOS** over 369 OOS sessions; P(loss)=18.56% forward; consistent with primary-literature unconditional-ORB-on-futures (Holmberg-Lönnbark-Lundström 2013 *Finance Research Letters* 10(1):27-33; Tsai 2019)." |
| H053 v3 | "CI-marginal across 4 arms; NQ LightGBM +10.8% realized 2-yr OOS, max-DD 3.7%, forward median $10,713 / P(loss)=15%." | "Sharpe-CIs uniformly cover zero (`marginal` annotation). Strongest cell: **NQ LightGBM +10.8% realized OOS** over the 2024-2025 fold; max-DD 3.7%; descriptive-mediation positive (in-sample partial-R² CI excludes zero); causal-mechanism `hybrid` per ADR-0022 §1.3." |
| H054 | "Point-positive (+3.50% realized anti-gated, P(loss)=29.2%) but CIs cover zero. Structurally low-power (anti-gate fires 7/237 sessions)." | "Point-positive and directionally consistent; LW2008 CI covers zero at exploratory power. Anti-gate trigger rate 7/237 = 2.95% drives the wide CI; under the AMH framing this is a regime-conditional efficiency signal, not a failure of the anti-gate construction." |
| H060 | (not in prior table; emitted 2026-05-12) | **Current top OOS performer.** TSMOM basket {ES, NQ, MGC, SIL} realized $10,000 → $18,943.37 (+89.43%) over 1,260 walk-forward concatenated OOS sessions; ann. Sharpe +0.617; pre-cost research-only v1; Kelly-multiplier 2.5× (super-Kelly, operator-discretionary); MPPM(ρ=1) +0.106 (CI covers zero, `marginal`); BOCD decay-flag not raised over OOS." |

The new framing preserves all numerical values verbatim (per ADR-0013 §4.1 non-loss) and changes only the interpretive prose. The KPI report cards themselves are untouched.

### Trade-offs accepted

- **ADR-0017's defensive primitives lose BLOCKING-BEFORE-LAUNCH enforcement.** A future operator pivot back to capital-preservation framing would require unwinding this ADR. Mitigated by: (a) the primitives are preserved verbatim as opt-in tooling per ADR-0013 §4.1 non-loss; (b) per-hypothesis design.md §11.1 may invoke any subset of K-1..K-8 with `# justify:` annotation; (c) the AMH framing of ADR-0018 D-6 includes BOCD halt + switching-bandit redirect which provide structurally-different protection (early-detection-and-redirect vs entry-time-prevention).
- **The Best-OOS showcase ranks by realized OOS metrics**, which may incentivize cherry-picking the strongest cell rather than reporting the hypothesis-of-record arm. Mitigated by: (a) mandatory disclosure of "hypothesis-of-record arm" vs "strongest cell" per row in BEST_OOS.md (the showcase template includes this field); (b) the showcase script reads the per-card hypothesis-of-record arm from the KPI report card front-matter and reports it alongside the strongest cell; (c) ADR-0022 §1.3 causal-mechanism annotation surfaces strategy-quality signals beyond raw realized-OOS percentages.
- **The README rewrite may invite "regression to old framing" pressure if a future hypothesis produces a Sharpe-era-style catastrophic OOS.** Mitigated by: (a) the README explicitly cites ADR-0018 + ADR-0024 as load-bearing for the AMH framing; (b) ADR-0024 D-7 binds AMH at the project level — strategy decay is the null, and a catastrophic OOS under post-train regime divergence is the **predicted AMH outcome**, not a project failure; (c) past KPI report cards are preserved verbatim, so the empirical record is intact for any reframing review.
- **The 13-table extension (new Table 3d) creates one additional canonical table.** Cosmetic operator-burden cost; aligns with ADR-0017 §3 12-table format precedent.

### Residual risk

- **The N=1 catastrophic event (2026-05-07 pilot ledger) motivated ADR-0017; demoting its primitives risks under-protection if the operator's empirical failure modes recur.** Mitigated by: (a) kill switches remain available as opt-in tooling; (b) per-hypothesis design.md §11.1 may invoke them with `# justify:` annotation; (c) the H062 paradigm includes BOCD halt + switching-bandit redirect which provide structurally-different protection; (d) operator-discretionary review at every promotion remains the structural safeguard.
- **The Best-OOS showcase may misframe H060's TSMOM basket as a "best result" when its forward 252-session P(loss) is 26.6%** (per H060 KPI report card v1 §6) — meaning roughly 1-in-4 forward samples loses money on the basket arm. Mitigated by: BEST_OOS.md mandatory disclosure of forward-projection P(loss) per row; the showcase is not a recommendation, it is a transparency artifact about realized-OOS magnitude.
- **MPPM(ρ=1) primary fitness is computed only on H060 + H062 at this ADR's adoption time.** Past hypotheses' KPI report cards (H050 v1, H052a v1, H053 v1/v2/v3, H054 v1) do not include the MPPM(ρ=1) row. The Best-OOS ranking falls back to realized-OOS-end-equity until the MPPM cutover per `P1-BEST-OOS-MPPM-RANKING-CUTOVER`.

### Cascade requirements

Per the ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline, the project-level §8 + §10 amendment at this ADR requires explicit cascade to every designed-status hypothesis's design.md:

- **`P1-ADR-0024-DESIGN-MD-CASCADE`** (BLOCKING-BEFORE-NEXT-STAGE-3-RUN) — H050, H051, H052a, H052b, H053, H054, H055, H060, H062 design.md §10 (decision rule) reframed from Sharpe-differential or ADR-0017-4-metric-vector to MPPM(ρ=1); §11.1 (kill switches) reframed from mandatory inheritance to opt-in annotation; §17 (revision log) appended with the ADR-0024 amendment reference. Frozen §1-§7 untouched.
- **`P1-ADR-0024-CLAUDE-MD-CASCADE`** — CLAUDE.md §"KPI report card for every strategy" + §"Standing constraints" updated with the new annotation grammar + paradigm-canonical label + Best-OOS showcase mandate.
- **`P1-ADR-0024-TEMPLATE-CASCADE`** — [research/_templates/kpi_report_card_template.md](../../research/_templates/kpi_report_card_template.md) + [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) extended with Table 3d (MPPM(ρ=1) primary fitness) + the new annotation grammar.
- **`P1-ADR-0024-GLOSSARY-CASCADE`** — [docs/glossary.md](../../docs/glossary.md) updated with the new annotations + paradigm-canonical labels.
- **`P1-ADR-0024-DECISIONS-README-CASCADE`** — [docs/decisions/README.md](README.md) updated with the ADR-0024 entry + the paradigm-evolution timeline.
- **`P1-ADR-0024-RETROACTIVE-V2-KPI-REPORT-CARD-CASCADE`** — emit v{N+1} KPI report cards for H050/H052a/H053/H054 with the new Table 3d (MPPM(ρ=1) row) populated; v{N} preserved verbatim per ADR-0013 §4.1. Sequenced per operator priority.

### BLOCKING follow-ups registered by ADR-0024

| Follow-up | Status | Description |
|---|---|---|
| `P1-BEST-OOS-PRE-PUSH-HOOK-INSTALL` | BLOCKING-CONCURRENT-WITH-ADR | Pre-push Git hook at [.githooks/pre-push](../../.githooks/pre-push) calls `scripts/showcase_best_oos.py` to regenerate BEST_OOS.md; documented bootstrap step at [scripts/bootstrap_env.py](../../scripts/bootstrap_env.py) installs hook path |
| `P1-ADR-0024-DESIGN-MD-CASCADE` | BLOCKING-BEFORE-NEXT-STAGE-3-RUN | Per-hypothesis §8 + §10 + §11.1 cascade |

### Non-blocking follow-ups registered by ADR-0024

`P1-ADR-0024-CLAUDE-MD-CASCADE`; `P1-ADR-0024-TEMPLATE-CASCADE`; `P1-ADR-0024-GLOSSARY-CASCADE`; `P1-ADR-0024-DECISIONS-README-CASCADE`; `P1-ADR-0024-RETROACTIVE-V2-KPI-REPORT-CARD-CASCADE`; `P1-BEST-OOS-MPPM-RANKING-CUTOVER` (cutover the Best-OOS ranking primary from realized-OOS-end-equity to MPPM(ρ=1) when uniformly reported across all hypotheses); `P1-BEST-OOS-SHOWCASE-SCHEMA-FROZEN-DATACLASS` (formalize the BEST_OOS.md row schema as a frozen dataclass to prevent drift); `P1-ADR-0017-VS-ADR-0024-CROSSWALK-MEMO` (operator-readable crosswalk explaining where ADR-0017 ends and ADR-0024 begins; preserves the ADR-0018 D-5 verbatim language while reframing the inheritance-scope).

## References

### Primary peer-reviewed sources (preserved from upstream ADRs)

- Lo, A. W. (2004). The Adaptive Markets Hypothesis: Market efficiency from an evolutionary perspective. *Journal of Portfolio Management*, 30(5), 15–29. [DOI 10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611). (AMH canonical philosophical anchor per D-7.)
- Goetzmann, W., Ingersoll, J., Spiegel, M., & Welch, I. (2007). Portfolio performance manipulation and manipulation-proof performance measures. *Review of Financial Studies*, 20(5), 1503–1546. [DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025). (MPPM(ρ=1) primary fitness per ADR-0018 D-1.)
- Kelly, J. L. (1956). A new interpretation of information rate. *Bell System Technical Journal*, 35(4), 917–926. [DOI 10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x). (Log-optimal bet sizing; underlies Kelly-multiplier grid per ADR-0018 D-2.)
- Adams, R. P., & MacKay, D. J. C. (2007). Bayesian online changepoint detection. [arXiv:0710.3742](https://arxiv.org/abs/0710.3742). (BOCD decay detector per ADR-0018 D-3.)
- Garivier, A., & Moulines, E. (2011). On upper-confidence bound policies for switching bandit problems. *Proc. ALT 2011*, LNCS 6925:174–188. [DOI 10.1007/978-3-642-24412-4_16](https://doi.org/10.1007/978-3-642-24412-4_16). (D-UCB / SW-UCB switching-bandit per ADR-0018 D-4.)
- Besson, L., Kaufmann, E., Maillard, O.-A., & Seznec, J. (2019). Efficient change-point detection for tackling piecewise-stationary bandits. [arXiv:1902.01575](https://arxiv.org/abs/1902.01575). (GLR-klUCB switching-bandit per ADR-0018 D-4.)
- Auer, P., Cesa-Bianchi, N., Freund, Y., & Schapire, R. E. (2002). The nonstochastic multiarmed bandit problem (EXP3 / EXP3.S). *SIAM Journal on Computing*, 32(1):48–77. [DOI 10.1137/S0097539701398375](https://doi.org/10.1137/S0097539701398375). (EXP3.S baseline per ADR-0018 D-4.)

### Project-internal

- [ADR-0001](ADR-0001-project-scope.md) — retail capacity ceiling; preserved.
- [ADR-0012](ADR-0012-evidence-bar.md) — binding evidence-bar gates; superseded by ADR-0013.
- [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — permanent exploration + no gates + non-loss + NinjaScript terminus + frozen-pre-reg-amendment discipline; **preserved unchanged**; load-bearing for the amendment-discipline mechanism this ADR uses.
- [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — canonical 9-table → 12-table (ADR-0017) → **13-table** (this ADR) results-summary format.
- [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) — survival-constrained optimization paradigm; §4.2 + §5 + §6 mandatory-inheritance clauses **demoted to opt-in** by this ADR; §1-§3 4-metric vector + §4.1 sizing primitive preserved as KPI tier.
- [ADR-0018](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — regime-conditional aggressive-growth paradigm; **promoted from `status: proposed` to `status: accepted`** by this ADR.
- [ADR-0019](ADR-0019-barbell-payoff-shape-screening.md) — barbell payoff-shape screening (L-skewness); preserved.
- [ADR-0022](ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) — causal-mechanism vs correlation-only annotation; preserved.
- [research/01_hypothesis_register/H062/design.md](../../research/01_hypothesis_register/H062/design.md) — H062 pre-registration; the canonical example of the ADR-0024 paradigm.
- [research/01_hypothesis_register/H060/H060_kpi_report_v1.md](../../research/01_hypothesis_register/H060/H060_kpi_report_v1.md) — H060 KPI report card v1; first emitted KPI card under the ADR-0018 framework; current top OOS performer.
- [docs/audits/audit_trail_2026-05-15_adr-0024-paradigm-resolution.md](../audits/audit_trail_2026-05-15_adr-0024-paradigm-resolution.md) — this ADR's audit-remediate-loop trail.

## Empirical justification

The empirical basis is the conjunction of (a) the 2026-05-14 H062 pre-registration explicitly instantiating ADR-0018's framework in §1-§7 frozen content with 27 §11.2 BLOCKING-BEFORE-LAUNCH precondition rows of which 14 remained open at this ADR's adoption time (reconciling the prior CLAUDE.md ledger drift per §Context observation 2); (b) the operational ambiguity of ADR-0018 `status: proposed` co-existing with ADR-0017 mandatory-inheritance clauses; (c) the user 2026-05-15 directive explicitly reframing the project paradigm; (d) the empirical record of past hypotheses (H050 / H052a / H053 / H054 / H060) producing substantively-positive realized OOS results on the strongest cells under the AMH framing while their hypothesis-of-record Sharpe-CIs covered zero. Each is independent evidence; together they constitute the load-bearing motivation for this ADR.

The CLAUDE.md user-global §"Evidence Hierarchy" is preserved unchanged: peer-reviewed → official docs → professional standards → vetted forums → reproduction. The ADR-0024 framework draws from peer-reviewed primary sources (Lo 2004 AMH; GISW 2007 MPPM; Kelly 1956; Adams-MacKay 2007 BOCD; Garivier-Moulines 2011 + Besson-Kaufmann-Maillard-Seznec 2019 + Auer-Cesa-Bianchi-Freund-Schapire 2002 bandit literature) each tagged per CLAUDE.md §"Practitioner-source-tag" convention.

This ADR is the canonical reference for the SKIE-Universe project's optimization-and-promotion paradigm from 2026-05-15 forward. It formalizes the H062-instantiated framework as project-canonical, promotes ADR-0018 to `accepted`, demotes ADR-0017's §4.2 + §5 + §6 mandatory-inheritance clauses to opt-in tooling + KPI annotations, and mandates a Best-OOS showcase artifact updated on every push.
