---
name: {HID} — {TITLE}
description: Pre-registered design doc for hypothesis {HID}
type: project
hypothesis_id: {HID}
tier: {TIER}
status: queued  # queued | designed | running | evaluated | archived(positive|null|negative)
owner: skoir
created: {DATE}
citations: {CITATIONS}
---

# {HID} — {TITLE}

This document is the pre-registration record for hypothesis {HID}. It is frozen at
`designed` status; any change after that point requires a new hypothesis ID. The 11
sections below are mandated by [plan/implementation-plan_2026-04-15.md §10](../../../plan/implementation-plan_2026-04-15.md).
Inline commentary cites the plan or audit anchor that governs the content of each section.

## 1. Hypothesis

State the null H0 and alternative H1 in precise form (sign and magnitude of the test
statistic, not prose). Identify the economic mechanism and the primary literature
(DOI or arXiv ID) that grounds the effect. Unattributed folklore factors are rejected per
[rules/quant-project.md](../../../../.claude/rules/quant-project.md) "Published research".

- H0:
- H1:
- Mechanism:
- Primary citations:

## 2. Universe and sample period

Bounded at pre-reg; no discretion later. Specify instruments (ES/NQ/MES/MNQ front month
per [config/instruments.yaml](../../../config/instruments.yaml)), sampling frequency,
session regime (RTH vs ETH, per project CLAUDE.md session policy), and the time-ordered
train / validation / test windows. Walk-forward only per [plan §4.1](../../../plan/implementation-plan_2026-04-15.md).

- Instruments:
- Frequency:
- Session(s):
- Train window:
- Validation window:
- Test window:
- Roll-handling note:

## 3. Features

List feature modules by exact `FEATURE_REGISTRY` name and semver version per
[plan §3](../../../plan/implementation-plan_2026-04-15.md). Any logic change bumps
`version`. Point-in-time property test and pipeline-level leakage test (plan §3, §4.6)
must pass before run.

- Feature entries (`name@version`):

## 4. Label construction

Triple-barrier labeling per Lopez de Prado AFML §3.2, pre-registered per
[audit M-14](../../research/03_audits/audit-round1-quant_2026-04-15.md). Required fields
(all appear in `config.yaml` `label` block):

- `pt_sl` (profit-take / stop-loss multipliers):
- `vertical_barrier` (duration):
- `volatility_estimator` (e.g. Yang-Zhang, Parkinson, realized-vol lookback):
- Meta-label horizon effective upper bound (feeds splitter `purge`):

## 5. Estimator

Exact model class and hyperparameter grid, fixed at pre-reg. No post-hoc additions to the
grid. Hyperparameter search is nested inside walk-forward; no information leaks from
outer to inner folds (plan §4.1).

- Model class:
- Hyperparameter grid:
- Search protocol (grid / random / Bayesian, with budget):
- Loss / metric:

## 6. Splitter

`PurgedWalkForwardSplitter` or `CombinatorialPurgedCV` per plan §4.1 and
[audit M-13](../../research/03_audits/audit-round1-quant_2026-04-15.md). `embargo` is
data-driven (residual PACF vs Politis-White block length, max); `purge >= max label
horizon`. CPCV `n_groups` and `n_test_groups` are hypothesis-level choices logged with
rationale (AFML §12).

- Splitter choice:
- `embargo` selection method:
- `purge` derivation:
- If CPCV: `n_groups`, `n_test_groups`, selection rationale:

## 7. Cost model

Reference `cost_model_id` registered in `src/skie_ninja/backtest/costs/` per plan §6.
Slippage is regime-conditional (RTH/ETH/OVN) and fit walk-forward, never single-split.

- `cost_model_id`:
- Commission schedule source:
- Slippage model version:

## 8. Gate thresholds

Gate-report fields and thresholds per plan §5 and §5.1 `passed` logic. Any deviation
from defaults in [config/gate.yaml](../../../config/gate.yaml) must be justified here
with a `# justify:` note and a citation.

- `alpha`:
- `bh_threshold`:
- `dsr_activation_size`:
- Power target (§5.1 block in config.yaml):

## 9. Stopping rule

Pre-specified criterion for terminating the run. No p-hacking; no "keep training until
Sharpe crosses X". Either: (a) fixed number of walk-forward folds, or (b) calendar-time
budget, or (c) futility check against `n_required_for_power_80`.

- Stop criterion:
- Max folds:
- Max wall-clock budget:

## 10. Decision rule

Mapping from `GateReport.passed` outcome to archival label and next action. Null results
stay in the hypothesis register per project CLAUDE.md.

- If `passed=True`: archive(positive), promote to paper-trade eligibility list.
- If `passed=False` and CI excludes zero but SPA fails: archive(null) with multiple-testing note.
- If `passed=False` and CI covers zero: archive(null).
- If realized < pre-registered `n_required_for_power_80`: archive(null, underpowered).

## 11. Reproducibility commitments

Log the tuple required by the project reproducibility hook and plan §9.3: git HEAD,
`uv pip freeze` sha, dataset checksums, RNG seed, model hash. Dataset checksums are
frozen at pre-reg time in `data_requirements.md`.

- git HEAD (at run):
- `uv pip freeze` sha (at run):
- RNG seed:
- Dataset checksums (frozen at pre-reg):
- Reproducibility log path: `logs/reproducibility/{run_id}.json`
