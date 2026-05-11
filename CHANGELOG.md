# Changelog

Condensed project-phase log. The authoritative ledger is [CLAUDE.md](CLAUDE.md) (currently ~140 KB; full audit-remediate-loop trail and decision rationale). This file is a one-line-per-phase scannable summary.

Date format: `YYYY-MM-DD`.

## 2026-05

- **2026-05-11 — Phase M: documentation reorganization.** Promoted `hypothesis_backlog.md` to repo root (project-canonical, broader scope than buildouts). Moved phase plans + buildouts + roadmaps into `plan/buildouts/`. Created repo-level indices (`docs/decisions/README.md` ADR index, `research/01_hypothesis_register/INDEX.md` stage dashboard, `RESULTS_INDEX.md` KPI cards, `docs/glossary.md`). Rewrote README.md against ADR-0013 + ADR-0017 framing.
- **2026-05-09 — Phase L (commits `546b828`, `0be0f30`): ADR-0017 inferential primitives.** Landed 5 of 7 BLOCKING-before-launch primitives: `r_multiple`, `calmar`, `profit_factor`, `sizing` (Vince f + drawdown-constrained Kelly), `risk_of_ruin`. 93 new tests; 2 remaining (failure-mode stress test, kill-switch backtest validation).
- **2026-05-08 — Phase K: [ADR-0017 survival-constrained paradigm](docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md).** Sharpe demoted to secondary KPI; primary metrics now terminal-wealth-q05 + Calmar-differential + profit-factor + R-multiple-mean. 8 hard kill-switch constraints + drawdown-constrained Kelly sizing mandatory inheritance from H055 forward.
- **2026-05-06 — Phase J: H055 successor tree.** [ADR-0015](docs/decisions/ADR-0015-component-stacking-master-architecture.md) (per-component → stacking → multi-TF-attention architecture) + [ADR-0016](docs/decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md) (sibling-repo audit-and-lift protocol). H056–H059 staked at `queued`.
- **2026-05-06 — Phase I: H055 pre-registration.** Mechanized intraday wick-rejection scalping (HMM-deferred to v3) on CME ES/NQ/MES/MNQ. Frozen at `designed`. Pilot ledger (171 trades) committed as descriptive empirical anchor.
- **2026-05-05 — Phase H continuation: H052a `kpi-report-emitted`.** Non-significant null on hypothesis-of-record; operator declined NinjaScript progression. Strongest cell (NQ unconditional ORB) registered as `P1-H052C-NQ-UNCONDITIONAL-ORB-PRE-REG`.
- **2026-05-05 — H054 `kpi-report-emitted`.** Anti-gate first-hour ORB on ES; point-positive (+3.50% realized) but CIs cover zero. Structurally low-power.
- **2026-05-04 — Phase G + ADR-0014: H050 `kpi-report-emitted`.** First clean H050 production walk-forward (run_id `31d23ec...`; 7h50min wall-clock; 7+ attempts since 2026-04-23). T_H050 CIs exclude zero on the **negative** side both symbols; HMM-gating actively harms the directional signal. [ADR-0014](docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) canonical 9-table results-summary mandate adopted.
- **2026-05-04 — Phase H: H052a Phase 1 + 2.** Dedicated orchestrator + features + cost model + production walk-forward.
- **2026-05-03 — Phase F: [ADR-0013 permanent exploration](docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).** Supersedes ADR-0012. No-archive policy; KPI-only evaluation; mandatory NinjaScript terminus; non-loss mandate (enforced fail-closed by pre-commit guard). H053 Path B leakage-clean refactor (Stage-3 v3 → v4); KPI report card v2 + v3.
- **2026-05-01 — Phase C/D/E: H053 Stages 1/2/3.** Stage-1 NULL (mediator alone insufficient); Stage-2 descriptive-positive (partial-R² CIs exclude zero in-sample); Stage-3 first-pass disposition REVERSED 2026-05-01 after diagnosis of train-truncation defect from Daily-405-gate × pre-2022-substrate interaction.

## 2026-04

- **2026-04-30 — Phase A/B: Cycle 7 closeout + H050 BLOCKING follow-ups.** Stage-0 HKS U-shape PASS; USOSvc Layer-5 disable helper + ADR-0010 framing/amendment.
- **2026-04-30 — H050 prod-run comprehensive post-mortem.** 6 attempts, ~35.2 hr cumulative wall-clock, zero aggregate disposition artifacts before this date. 16 follow-ups registered; 3 BLOCKING.
- **2026-04-29 — [ADR-0011 production walk-forward runbook](docs/decisions/ADR-0011-production-walkforward-runbook.md).** Binding 15-item preflight checklist + canonical execution shape (supervised relaunch loop) + post-run audit gate.
- **2026-04-28 — H053 pre-registration brought into main.** Cherry-picked 4 commits from sibling branch; `designed` at Tier-2b.
- **2026-04-27 — [ADR-0010 multi-hour-run process protection](docs/decisions/ADR-0010-multi-hour-run-process-protection.md).** Three-layer defense (wake-lock + pre-launch checklist + supervisor wrapper) after Windows Update auto-reboot terminated H050 prod-run-2.
- **2026-04-26 — Cell I substrate landing + decade-wraparound bug fix.** ES + NQ × 2015-2025; roll-adjusted module v0.2.0 → v0.3.0. HMM-fit cache amortization + cov-dedup at d=1.
- **2026-04-23 — Tier-2b buildout Cycles 1–6 (Phase A only).** Roll-adjusted 1-min derivative + NW-HAC + Sharpe-CI + HMM toolkit (Baum-Welch + causal Viterbi) + walk-forward engine + Hansen SPA + H050 feature factory.
- **2026-04-20 — Phase 2 scope extension.** [ADR-0005 HMM regime-inference toolkit](docs/decisions/ADR-0005-hmm-regime-toolkit.md) + [ADR-0006 HMM + 0DTE scope extension](docs/decisions/ADR-0006-scope-extension-hmm-0dte.md). H050/H051/H052(a/b) pre-registered. Repo renamed `SKIE-Ninja-Intraday` → `SKIE-Universe`.
- **2026-04-15 — Foundation ADRs.** [ADR-0001 scope](docs/decisions/ADR-0001-project-scope.md), [ADR-0002 bridge](docs/decisions/ADR-0002-bridge-selection.md), [ADR-0003 SPA vs Romano-Wolf](docs/decisions/ADR-0003-spa-vs-romanowolf.md), [ADR-0004 α + power defaults](docs/decisions/ADR-0004-alpha-and-power-defaults.md). Phase 0 punch list + Phase 1 ingest pipelines.

## See also

- **Full project ledger**: [CLAUDE.md](CLAUDE.md) — phase-by-phase audit-remediate-loop trail, decision rationale, follow-up registry.
- **ADR index**: [docs/decisions/README.md](docs/decisions/README.md)
- **Hypothesis stage dashboard**: [research/01_hypothesis_register/INDEX.md](research/01_hypothesis_register/INDEX.md)
- **KPI report cards**: [research/01_hypothesis_register/RESULTS_INDEX.md](research/01_hypothesis_register/RESULTS_INDEX.md)
