# Architecture Decision Records (ADRs)

Project-level architectural and methodological decisions. Each ADR is immutable once accepted; supersession produces a new numbered ADR that links back. Conventions follow [adr/madr](https://github.com/adr/madr) (numbered prefix + present-tense imperative title + YAML front matter).

## Index

Grouped by domain. Click an ADR ID for the full text.

### Scope and governance

| ID | Title | Status | Date |
|---|---|---|---|
| [ADR-0001](ADR-0001-project-scope.md) | Project scope | accepted | 2026-04-15 |
| [ADR-0006](ADR-0006-scope-extension-hmm-0dte.md) | Scope extension — HMM regime track + 0DTE option track | proposed | 2026-04-20 |
| [ADR-0012](ADR-0012-disposition-philosophy-aspirational-mvp.md) | Disposition philosophy — aspirational-MVP, KPI-reported | superseded by ADR-0013 | — |
| [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) | **Permanent Exploration** — KPI-only evaluation, no-archive policy, NinjaScript terminus, non-loss mandate | accepted | 2026-05-03 |
| [ADR-0016](ADR-0016-sibling-repo-audit-and-lift-protocol.md) | Sibling-repo audit-and-lift protocol — promoting SKIE-Ninja / Volatility / 0DTE / V3 artifacts | proposed | 2026-05-06 |
| [ADR-0021](ADR-0021-liquidity-provision-research-track-scoping.md) | Liquidity-provision research-track scoping — H100-series reserved; orderbook substrate deferred | proposed | 2026-05-12 |

### Inference and statistical methodology

| ID | Title | Status | Date |
|---|---|---|---|
| [ADR-0003](ADR-0003-spa-vs-romanowolf.md) | SPA vs Romano-Wolf stepwise as primary multiple-testing control | proposed | 2026-04-15 |
| [ADR-0004](ADR-0004-alpha-and-power-defaults.md) | Project-level defaults for α and target_power | accepted | 2026-04-15 |
| [ADR-0007](ADR-0007-embargo-placement.md) | Embargo placement — stacked vs overlap form for purged-k-fold / CPCV | accepted | 2026-04-24 |
| [ADR-0008](ADR-0008-spa-omega-method.md) | SPA omega estimator — bootstrap coupling vs HAC decoupled, per universe size | accepted | 2026-04-24 |
| [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) | Canonical end-of-simulation results-summary tables — KPI report card §3.2 mandate | accepted | 2026-05-04 |
| [ADR-0015](ADR-0015-component-stacking-master-architecture.md) | Per-component → stacking-master → multi-TF-attention architecture pattern | proposed | 2026-05-06 |
| [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) | **Survival-constrained optimization paradigm** — profit-and-drawdown-primary inference, Sharpe demoted to KPI | accepted | 2026-05-08 |
| [ADR-0018](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) | **Regime-conditional aggressive-growth paradigm** — MPPM(ρ=1) fitness, Kelly grid-search, BOCD decay, switching-bandit | proposed | 2026-05-12 |
| [ADR-0019](ADR-0019-barbell-payoff-shape-screening.md) | Barbell payoff-shape screening — L-skewness annotation in every KPI report card | proposed | 2026-05-12 |
| [ADR-0020](ADR-0020-meta-portfolio-orchestrator.md) | Meta-portfolio orchestrator across emitted hypothesis arms (IR = IC·√breadth) | proposed | 2026-05-12 |
| [ADR-0022](ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) | Mandatory causal-mechanism vs correlation-only annotation in every design.md | proposed | 2026-05-12 |

### Modeling

| ID | Title | Status | Date |
|---|---|---|---|
| [ADR-0005](ADR-0005-hmm-regime-toolkit.md) | Hidden Markov Model regime-inference toolkit (Baum-Welch + causal Viterbi) | proposed | 2026-04-20 |

### Execution and operations

| ID | Title | Status | Date |
|---|---|---|---|
| [ADR-0002](ADR-0002-bridge-selection.md) | Python ↔ NinjaTrader 8 execution bridge selection | proposed | 2026-04-15 |
| [ADR-0009](ADR-0009-blas-thread-pinning.md) | BLAS thread pinning for reproducibility | accepted | 2026-04-24 |
| [ADR-0010](ADR-0010-multi-hour-run-process-protection.md) | Multi-hour-run process protection on Windows | accepted | 2026-04-27 |
| [ADR-0011](ADR-0011-production-walkforward-runbook.md) | Production walk-forward runbook — preflight checklist + execution shape + post-run audit gate | proposed | 2026-04-29 |

## Load-bearing ADRs (read these first)

For a new reader trying to understand the current research posture:

1. **[ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)** — the central governance ADR. No promotion gates; every hypothesis progresses to NinjaScript regardless of KPI; non-loss mandate forbids deletion of audit / report card / sidecar files.
2. **[ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md)** — the central inferential ADR. Sharpe demoted to KPI; primary metrics are terminal-wealth-q05 + Calmar-differential + profit-factor + R-multiple-mean. Mandatory inheritance from H055 forward.
2a. **[ADR-0018](ADR-0018-regime-conditional-aggressive-growth-paradigm.md)** — the aggressive-growth amendment to ADR-0017. MPPM(ρ=1) replaces Sharpe in inner-CV fitness; Kelly multiplier grid-searched (including super-Kelly under explicit literature caveat); BOCD decay detector; switching-bandit meta-strategy. Adopts Lo 2004 Adaptive Markets Hypothesis as project-canonical philosophical framing.
3. **[ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md)** — the central reporting ADR. Every KPI report card carries 9 mandatory tables (12 from 2026-05-08 per ADR-0017 §3.2).
4. **[ADR-0005](ADR-0005-hmm-regime-toolkit.md)** — the central modeling ADR for the HMM regime track (Baum-Welch + causal forward-filter inference; warm-cold sidecar diagnostics).
5. **[ADR-0001](ADR-0001-project-scope.md)** — the foundational scope ADR (universe, capacity, walk-forward-only).

## Conventions

- **Naming**: `ADR-NNNN-{slug}.md` where NNNN is a 4-digit sequential number.
- **Status values**: `proposed` (awaiting evidence or measurement), `accepted` (in force), `superseded-by-ADR-NNNN` (replaced by a numbered successor; original preserved verbatim per non-loss).
- **Front matter**: YAML block at file top with `id`, `title`, `status`, `date`, `decision-owner`, `supersedes`, `related`.
- **Supersession**: a superseded ADR is never deleted; its `status` field is updated to `superseded-by-ADR-NNNN` and a banner is added at the file top. The successor ADR cites the predecessor and explains what was preserved vs amended.
- **Frozen-pre-reg amendment scope** (ADR-0013 §"Frozen pre-registration amendment"): project-level ADRs MAY amend §8+§10 of frozen `status: designed` hypothesis pre-registrations without requiring a successor hypothesis ID, subject to project-wide application and per-design.md cross-reference.

## See also

- [hypothesis_backlog.md](../../hypothesis_backlog.md) — project-canonical hypothesis register
- [research/01_hypothesis_register/INDEX.md](../../research/01_hypothesis_register/INDEX.md) — per-hypothesis stage dashboard
- [research/01_hypothesis_register/RESULTS_INDEX.md](../../research/01_hypothesis_register/RESULTS_INDEX.md) — KPI report cards index
- [docs/audits/](../audits/) — audit-remediate-loop trails (append-only)
