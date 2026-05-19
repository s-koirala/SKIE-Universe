# Glossary

Reference for terms used throughout the project. Onboarding readers should skim this once. Existing contributors use it as a citation source ("see glossary"). New terms are appended; existing terms are amended in place with a `# justify:` annotation when meaning changes.

## Stage labels (ADR-0013 §1)

| Term | Meaning |
|---|---|
| **`queued`** | Hypothesis listed in [hypothesis_backlog.md](../hypothesis_backlog.md); no design.md yet. |
| **`designed`** | `design.md` frozen with `status: designed` YAML frontmatter; sections §1–§7 (hypothesis, universe, features, labels, splitter, cost model) are immutable from this point forward per ADR-0013 §"Frozen pre-registration amendment". |
| **`exploration-in-progress`** | Production walk-forward run(s) underway or completed; KPI report card not yet emitted. |
| **`kpi-report-emitted`** | First KPI report card v1 has landed at `research/01_hypothesis_register/H<ID>/H<ID>_kpi_report_v1.md`. Subsequent v2 / v3 versions append per ADR-0013 §4.1 non-loss. |
| **`ninjascript-implemented`** | C# implementation present at `ninjascript/strategies/H<ID>_*.cs` with parity-check artifact per ADR-0013 §5.2. Mandatory terminal state of the research loop. |
| **`paper-trade-active`** | Strategy running on paper-trade simulation account; not yet evaluated. |
| **`paper-trade-evaluated`** | 60 session-day paper-trade window complete; results recorded in v2 KPI report card. |
| **`live-promoted`** | Operator decision to deploy to live capital; logged at `logs/promotions/`. |

Legacy disposition labels (`running`, `evaluated`, `archived(positive|null|negative)`) appear in pre-ADR-0013 stage rows; preserved verbatim per non-loss. They no longer drive promotion decisions.

## KPI annotation grammar (ADR-0013 §2, ADR-0017 §1)

Annotations are dot-separated tags appended to KPI report card §9. Format: `<kpi-name>-<verdict>`.

| Annotation | Meaning |
|---|---|
| `leakage-canary-pass` / `leakage-canary-fail` | The three Cycle-4 PIT/leakage canaries (fold-boundary, label-horizon-purge, dual-fit-observer) all returned clean. A `fail` does NOT exit the strategy; it is recorded and the operator decides remediation timing. |
| `bss-positive` / `bss-flat` / `bss-negative` | Brier Skill Score vs per-instrument climatological prior on OOS fold; `flat` if \|BSS\| < 0.05. |
| `reliability-in-band` / `reliability-out-of-band` | Reliability-diagram slope ∈ [0.7, 1.3] (project-operational band; not Niculescu-Mizil & Caruana 2005 primary text). |
| `repro-log-complete` / `repro-log-incomplete` | All 13 ReproLog fields populated. |
| `cost-{robust,conditional,flat}` | Cost-floor sensitivity at 1× vs 2× tick cost. |
| `dsr-positive` / `dsr-marginal` / `dsr-negative` | Deflated Sharpe Ratio per Bailey-López de Prado 2014; only reported when family ≥ activation size (n/a otherwise). |
| `cpcv-ks-converged` / `cpcv-ks-not-converged` | CPCV K-S monotonicity sub-criterion (KPI annotation only; does not gate). |
| `post-run-audit-pass` / `post-run-audit-fail` | Round-N audit-remediate-loop on the run output verdict. |
| `interpretability-{full,partial,opaque}` | Component-level interpretability (ADR-0015 stacking architectures). |
| `tw-q05-{above-half,above-zero,below-zero}` | Terminal-wealth 5th percentile vs starting capital × {0.5, 1.0} (ADR-0017 primary). |
| `calmar-diff-{positive,marginal,negative}` | Calmar-differential CI excludes/covers zero (ADR-0017 primary). |
| `pf-diff-{positive,marginal,negative}` | Profit-factor differential (ADR-0017 primary). |
| `r-multiple-mean-{positive,marginal,negative}` | R-multiple mean CI excludes/covers zero (ADR-0017 primary). |
| `stress-test-FM-N-fail` | Synthetic failure-mode FM-N stress test failed (FM-1..FM-5 per ADR-0017 §6; recorded, not gating). |
| `paper-trade-live-{aligned,divergent}` | 60-session-day paper-trade Sharpe within/outside backtest CI (ADR-0013 §6 KPI; not gating). |
| `kill-switch-active` / `kill-switch-inactive` | ADR-0025 §D-1 runtime-intervention disclosure — TRUE if any K-N constraint (K-3 / K-4 / K-6 / K-7) fired during simulation. Distinct from the ADR-0024 `kill-switch-{K-N-enabled, K-N-disabled}` design-time declaration; both annotations co-exist on the same KPI report card. |
| `bocd-live-pause` / `bocd-live-active` | ADR-0025 §D-4 live-state-machine disclosure — TRUE if at least one BOCD pause event fired during the live state machine integration over the sim. Distinct from the ADR-0018 §D-3 `decay-detected-{yes, no}` one-shot batch verdict. |
| `cost-empirical-calibrated` / `cost-conservative-prior` / `cost-zero` | ADR-0025 §D-3 cost-model-provenance disclosure. ORTHOGONAL to the legacy ADR-0012/0013-era `cost-{robust, conditional, flat}` sensitivity-regime annotations; both annotation families co-exist on the same KPI report card. Provenance answers "where did the fee schedule come from"; sensitivity answers "how robust is the result to fee-schedule perturbation". |

## Primary metrics (ADR-0017 §1)

| Metric | Definition | CI primitive |
|---|---|---|
| **`terminal_wealth_q05`** | 5th percentile of 1-year (252-session) bootstrap-forward $10K-baseline ending equity | Per-arm Politis-White 2004 block-length stationary bootstrap; n_paths=5,000 |
| **`calmar_differential`** | (ann_return_arm − ann_return_bench) / max(\|MaxDD_arm\|, \|MaxDD_bench\|) | Block-stationary-bootstrap CI per Politis-Romano 1994; 1,000 replicates |
| **`profit_factor`** | gross_profit / gross_loss per arm; differential reported alongside | Block-stationary-bootstrap CI on joint per-trade P/L |
| **`r_multiple_mean`** | Per-trade R = realized P/L / \|1R\|, where 1R = pre-entry stop × position size | Block-stationary-bootstrap CI; 1,000 replicates |

Implementations: [`src/skie_ninja/inference/calmar.py`](../src/skie_ninja/inference/calmar.py), [`profit_factor.py`](../src/skie_ninja/inference/profit_factor.py), [`r_multiple.py`](../src/skie_ninja/inference/r_multiple.py), [`risk_of_ruin.py`](../src/skie_ninja/inference/risk_of_ruin.py).

## Secondary metrics (preserved for academic comparability)

| Term | Meaning |
|---|---|
| **`T_H<ID>`** | Per-hypothesis Sharpe-differential statistic per §1 of each `design.md`. Typical form: SR_treatment − SR_control. Frozen verbatim in design.md §1 per ADR-0013 §1–§7 immutability; reported as secondary KPI per ADR-0017 §1.2. |
| **LW2008 CI** | Ledoit-Wolf 2008 studentized circular-block bootstrap differential Sharpe CI ([UZH IEW WP 320](https://www.ledoit.net/sharpest.pdf); journal of empirical finance). |
| **Opdyke 2007 CI** | Mertens-HAC approximation Sharpe CI ([Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084)). Used univariate where LW2008 differential is unavailable. |
| **Hansen 2005 SPA** | Superior Predictive Ability test for the family of strategies in the universe-to-date ([Hansen 2005](https://doi.org/10.1198/073500105000000063)). KPI annotation only per ADR-0013 §1.2. |
| **DSR / PSR** | Deflated / Probabilistic Sharpe Ratio per Bailey-López de Prado 2014; reported when family ≥ activation size. |

## Statistical machinery

| Term | Meaning |
|---|---|
| **CPCV** | Combinatorial Purged Cross-Validation per López de Prado 2018 AFML Ch.12. Splitter that yields multiple OOS test-fold paths from one panel by combinatorially leaving out groups; project canonical splitter for any Sharpe KPI emission. |
| **Walk-forward CV** | Rolling-window or expanding-window time-ordered CV per Bergmeir-Benítez 2012 / Tashman 2000. Project standard for outer loop. |
| **Purged + embargo** | AFML §7.4 purge of train observations whose labels overlap the test window + embargo skip after each test fold to prevent serial-correlation leakage. ADR-0007 elected mlfinlab-stacked form. |
| **PW2004 block length** | Politis-White 2004 (revised by Patton-Politis-White 2009) automatic block-length selector for stationary bootstrap. Project canonical. |
| **Stationary bootstrap** | Politis-Romano 1994 random-length-block bootstrap that preserves dependence structure asymptotically. Used for paired CIs on per-trade and per-session metrics. |
| **Brier Skill Score (BSS)** | (Brier_climatology − Brier_model) / Brier_climatology; positive means model beats prior. |
| **Reliability slope** | Slope of reliability-diagram regression (predicted-vs-empirical bin frequencies); project-operational band [0.7, 1.3] = `reliability-in-band`. |

## Reproducibility primitives

| Term | Meaning |
|---|---|
| **`ReproLog`** | Frozen-dataclass capture of `git_head`, `pip_freeze`, `dataset_checksums`, `rng_seed`, `model_hash`, `timestamp_utc`, `env_id` per [src/skie_ninja/utils/reproducibility.py](../src/skie_ninja/utils/reproducibility.py). Atomic-written to `logs/reproducibility/{run_id}.json` by every walk-forward run. |
| **`RunContext`** | Context manager that opens a run, captures ReproLog, seeds RNG (numpy + torch + python), registers cleanup, crash-path flushes. [src/skie_ninja/utils/runcontext.py](../src/skie_ninja/utils/runcontext.py). |
| **`dataset_checksum`** | SHA256 of canonicalized substrate parquet partitions; one entry per `(symbol, year)` partition + a combined SHA. Bound at `designed` status in `data_requirements.md`. |
| **`scientific_payload_sha256`** | SHA256 of the run's deterministic scientific output (per-fold table + aggregate). Logged in sidecar; cross-checked at audit time. |
| **Sidecar** | Run-specific JSON file at `runs/<H>/{run_id}/sidecar.json` carrying per-fold metrics + run metadata. Versioned schema per hypothesis. |
| **Substrate** | Canonical raw bar data on disk at [data/processed/vendor_legacy_1min_roll_adjusted/](../data/processed/vendor_legacy_1min_roll_adjusted/) (roll-adjusted continuous-contract 1-minute OHLCV per AFML §2.4.3 multiplicative ratio adjustment). |

## Audit discipline

| Term | Meaning |
|---|---|
| **Audit-remediate-loop** | Mandatory 1–3 round discipline before every significant landing per `.claude/skills/audit-remediate-loop/`. Parallel proper-isolated quant-auditor + literature-check + reproducibility-verifier agents return findings; remediation closes them inline; trail committed at `docs/audits/audit_trail_<DATE>_<slug>.md`. Cap at 3 rounds (operational floor; ties to arXiv 2511.00751 self-consistency tapering). |
| **Round-N verdict** | `accept` / `accept-with-residuals` / `block`. Block requires further remediation; `accept-with-residuals` records open follow-ups. |
| **`P1-...` follow-up** | Phase-1 (or beyond) follow-up identifier. BLOCKING-{BEFORE-X} marks gates the project enforces before the next milestone. Tracked in CLAUDE.md ledger entries and audit trail residuals. |
| **Non-loss mandate** | ADR-0013 §4: no audit trail, ReproLog, sidecar, KPI report card, promotion log, NinjaScript strategy, or design.md may be deleted, overwritten, or wiped. Corrections produce versioned successors. Enforced fail-closed by [`scripts/_hooks/check_non_loss_deletion.py`](../scripts/_hooks/check_non_loss_deletion.py). |
| **Frozen-pre-reg amendment (Path A)** | ADR-0013 §"Frozen pre-registration amendment": project-level ADRs may amend §8+§10 of frozen `designed` design.md files without requiring a successor hypothesis ID, subject to project-wide scope + per-design cross-reference. §1–§7 are immutable. |

## Strategy mechanics

| Term | Meaning |
|---|---|
| **ORB** | Opening Range Breakout — entry on break of the first-N-minute high/low; canonical primary literature [Zarattini-Barbon-Aziz 2024](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284) + [Holmberg-Lönnbark-Lundström 2013](https://doi.org/10.1016/j.frl.2012.09.001) + Crabel 1990. H052a uses 60-min OR; literature canonical is 5-min. |
| **HMM regime gate** | Causal forward-filter inference per [ADR-0005](decisions/ADR-0005-hmm-regime-toolkit.md). Used to condition entry signals on inferred latent state (e.g., low-vol / mean-revert / trending). |
| **Anti-gate (H054)** | Inversion of a standard regime gate — entry IS allowed in a regime the gate would normally exclude. Tests whether the excluded-regime subset carries an exploitable inversion. |
| **Triple-barrier labeler** | AFML §3.4 path-dependent labeling — for each bar, label is `+1 / 0 / −1` based on which of {profit-taking barrier, stop-loss barrier, vertical (time-out) barrier} is hit first. Three hyperparameters: `pt_sl` (profit/stop multiplier on volatility), `vertical_barrier` (max holding period), `volatility_lookback`. |
| **Kill-switch (ADR-0017 §5)** | 8 hard constraints K-1..K-8 mandatory inheritance from H055 forward (per-trade $-stop, time-stop, no-add-to-loser, position cap, correlated-instrument inventory cap, daily/weekly circuit breakers, adverse-direction entry filter). Enforced at NinjaScript layer + validated at backtest layer. |
| **Drawdown-constrained Kelly** | Quarter-Kelly sizing rule per ADR-0017 §4.1 with per-trade R-multiple distribution + current-equity rebasing. Reference: MacLean-Thorp-Ziemba 2010. |
| **Forward projection** | 252-session bootstrap-forward simulation per ADR-0013 §3.1 ($10K starting capital; 5,000 paths). Outputs: realized end equity, max-DD distribution, P(loss)/P(double)/P(<50%), terminal-wealth quantiles. |
| **Sibling-repo lift** | Promoting a model artifact from a SKIE-Ninja / SKIE-NINJA-Volatility / SKIE-NINJA-0DTE / SKIENINJA-V3 sibling repo into SKIE-Universe per [ADR-0016](decisions/ADR-0016-sibling-repo-audit-and-lift-protocol.md) 7-gate audit. Three dispositions: `lift-as-feature`, `lift-and-retrain`, `lift-and-replace`. |

## See also

- [ADR index](decisions/README.md)
- [hypothesis_backlog.md](../hypothesis_backlog.md)
- [research/01_hypothesis_register/INDEX.md](../research/01_hypothesis_register/INDEX.md)
- [research/01_hypothesis_register/RESULTS_INDEX.md](../research/01_hypothesis_register/RESULTS_INDEX.md)
