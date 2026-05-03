---
id: ADR-0013
title: Permanent Exploration — KPI-only evaluation, no-archive policy, NinjaScript terminus, non-loss mandate
status: accepted
date: 2026-05-03
deciders: skoir
supersedes:
  - ADR-0012 (three-class disposition rubric — all Class A binding gates downgraded to KPIs; `archive(complete)` / `calibration-failed` / `leakage-detected` / `reproducibility-incomplete` disposition labels removed)
  - ADR-0003 (SPA-vs-RomanoWolf — SPA fully downgraded to KPI; previously partially downgraded by ADR-0012)
  - ADR-0008 (SPA omega method — preserved as KPI computation; no longer enters any binding gate)
amends:
  - CLAUDE.md "Evidence bar for any signal reaching paper-trade" — replaced by §"KPI report card" framing in this ADR
  - CLAUDE.md "Execution bar for live" — operator-promotion becomes operator-discretionary on the KPI report card; the 60-session-day paper-trade Sharpe-within-CI observation is retained as a KPI, not a gate
  - CLAUDE.md "Research philosophy" — strengthened with non-loss + NinjaScript-terminus mandates
  - research/01_hypothesis_register/H050/design.md §8 + §10 (project-wide; deferred cascade per `P1-ADR-0013-DESIGN-MD-CASCADE`)
  - research/01_hypothesis_register/H051/design.md §8 + §10 (project-wide; deferred cascade)
  - research/01_hypothesis_register/H052a/design.md §8 + §10 (project-wide; deferred cascade)
  - research/01_hypothesis_register/H052b/design.md §8 + §10 (project-wide; deferred cascade)
  - research/01_hypothesis_register/H053/design.md §8 + §10 (project-wide; deferred cascade)
preserves_immutability_of:
  - All hypothesis design.md §1 (statement) through §7 (cost model) — per ADR-0012 §"Frozen pre-registration amendment" §1-§7 immutability discipline; this ADR is a §8+§10 amendment only
  - All historical audit trails, ReproLogs, sidecars, dispositions, promotion logs
  - ADR-0012 itself as historical record (no deletion; supersession is logical, not physical)
---

# ADR-0013 — Permanent Exploration: KPI-only, no-archive, NinjaScript terminus, non-loss mandate

## Context

The SKIE-Universe project's existing disposition philosophy under [ADR-0012](ADR-0012-disposition-philosophy-aspirational-mvp.md) (2026-05-01) introduced a three-class rubric (Class A binding gates + Class B KPIs + Class C documentation). Operationally, ADR-0012's Class A binding gates retained four hard rejection paths: `leakage-detected`, `calibration-failed`, `reproducibility-incomplete`, plus `Hansen SPA p ≤ α at operator-promotion`. Under ADR-0012 a strategy failing any Class A gate is recorded but is **not eligible for paper-trade**.

Two empirical observations precipitated this ADR:

1. **H053 Stage-3 v2 disposition (2026-05-03, commits [221a635](https://github.com), [0d1fb08](https://github.com))** produced `calibration-failed` across all 4 (arm × symbol) combinations. ElasticNet on both ES and NQ achieved BSS ≈ -0.01 (calibration-marginal; essentially climatological prior). LightGBM produced BSS ≈ -0.18 to -0.21 (clearly miscalibrated). Under ADR-0012's binding gate, H053 exits the research loop without progressing to NinjaScript implementation. Stage-3 v2 audit trail: [docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md](../audits/audit_trail_2026-05-03_h053-stage3-v2.md).

2. **The user 2026-05-03 directive** (verbatim):

> "set a canonical precedent: we are not to archive but to explore the failures. we no longer have gates for failure or passing - but we have metrics and KPIs for performance evaluation. We are here to observe and to learn. The ultimate goal is to now compile a series of strategies and a comprehensive collection of results from these strategies. we will archive no more strategies or results. we will not forget any failures or errors. we will no longer wipe any of the work we conduct. we will only build, test, learn, and proceed onto the next strategy. and all strategies will be built to fruition to the point of ninja script implementation so we can explore in a practical environment beyond theory."

Under the user's directive, ADR-0012's binding-gate philosophy is the philosophical defect — calibration failure (or any other Class A failure) becomes an **observation in the KPI report card**, not a termination of the research loop. The strategy continues to NinjaScript implementation regardless. Operator review of the KPI report card governs paper-trade and live promotion at operator discretion.

## Decision

### §1. Disposition labels removed; replaced with stage progression

ADR-0012's three-class rubric (`leakage-detected` / `calibration-failed` / `reproducibility-incomplete` / `archive(complete; KPI report)`) is dissolved. There is no `archive` state, no `failed` disposition class, and no terminal-null disposition under this ADR. Every strategy progresses through the following non-terminal stages:

| Stage | Meaning | Entry condition | Exit condition |
|---|---|---|---|
| `exploration-in-progress` | Research / build cycles active | Hypothesis pre-registered with `status: designed` | KPI report card emitted for at least one full Stage-3 (or equivalent) run |
| `kpi-report-emitted` | Full KPI report card published; backtest evidence on file | A complete KPI report card per §3 below has been written and committed | NinjaScript implementation committed |
| `ninjascript-implemented` | Runnable C# implementation in [ninjascript/strategies/](../../ninjascript/strategies/); smoke-tested in NT8 Sim101 | A C# strategy file passes Sim101 smoke-test; strategy fill log written matching plan §6.1 schema | Operator promotes to paper-trade |
| `paper-trade-active` | Running on NT8 paper account; 60-session-day clock per [CLAUDE.md §Execution bar](../../CLAUDE.md) engaged | Operator promotion decision logged in `logs/promotions/` | Clock complete OR operator pulls (operator decision logged) |
| `paper-trade-evaluated` | 60-session-day clock complete; realized-vs-backtest Sharpe-within-CI observation recorded as a KPI | Clock completes OR operator-pull occurs | Operator promotes to live OR operator declines |
| `live-promoted` | Live capital deployed | Operator decision logged with risk-tolerance rationale | Strategy retired (operator decision; retirement is recorded, not deleted) |

A strategy at `kpi-report-emitted` does **not exit the research loop**; it progresses to `ninjascript-implemented` regardless of any KPI's qualitative annotation (including `bss-negative`, `leakage-canary-fail`, `sharpe-vs-passive-negative`, `spa-rejects`, etc.). The KPI report card is the artifact-of-record for operator review at every stage transition.

A strategy retired at `live-promoted` is **not** removed from the hypothesis register — its retirement is appended to the per-strategy record as an additional row. See §4 non-loss mandate.

#### §1.1. Stage-tracker source-of-truth (per Round-1 audit R-1-7 remediation)

Per-strategy current stage is tracked in an append-only file `research/01_hypothesis_register/{HID}/stage.md` with one chronological entry per stage transition. Schema:

```yaml
---
hypothesis_id: H{NNN}
schema_version: stage_tracker_v1
---

| date | stage | transition_evidence | operator | notes |
|---|---|---|---|---|
| 2026-MM-DD | exploration-in-progress | design.md frozen at status=designed; commit {sha} | skoir | initial pre-registration |
| 2026-MM-DD | kpi-report-emitted | KPI report card v1 at {path}; commit {sha} | skoir | end of Stage-3 |
| 2026-MM-DD | ninjascript-implemented | C# strategy at ninjascript/strategies/{name}.cs; Sim101 smoke-test record at {path}; commit {sha} | skoir | bridge-mediated parity ✓ |
| ... | ... | ... | ... | ... |
```

The stage-tracker file is protected by §4.1 non-loss + §4.3 pre-commit guard (append-only enforcement is a `git diff --staged` line-count-non-decreasing check on this file). New entries append; existing entries are immutable. Corrections produce additional rows annotated `superseded by row N`. Co-located with `design.md` and `failure_log.md` under each hypothesis-register subdirectory.

The `current_stage` of a strategy is the most recent row's `stage` value. This is the canonical machine-readable lookup for the stage-progression model in §1.

#### §1.2. `ninjascript-blocked-by-non-amenable-substrate` sub-stage (per Round-1 audit F-1-3 remediation)

Some Python-prototype strategies cannot be straightforwardly realized as standalone NinjaScript C# (e.g., H053 Arm 3 LLM, which requires deterministic-replay infrastructure that does not exist; e.g., H050's HMM filter, which requires an inference-time Python service rather than a self-contained C# indicator). For such strategies, the §5 NinjaScript-mandate is satisfied by **bridge-mediated implementation** per [ADR-0002](ADR-0002-bridge-selection.md): the C# strategy is a thin client that calls a Python inference service over the bridge.

A strategy whose bridge-mediated implementation is also blocked (e.g., bridge unavailable, inference service unfunded, or the operator decides bridge-mediation is contrary to the strategy's deployment-realism) enters a sub-stage `ninjascript-blocked-by-non-amenable-substrate` (not a terminal archive; a recognized state in the build pipeline). The sub-stage REQUIRES:

- An entry in [stage.md](#§1.1) annotated `ninjascript-blocked-by-non-amenable-substrate` with the blocking-reason explicitly enumerated.
- An entry in [failure_log.md](#§4.2) under the `build-defect` category, citing the specific NinjaScript / bridge limitation.
- A documented operator decision: (a) refactor Python prototype to NinjaScript-realizable form, (b) build bridge-mediated runtime per ADR-0002, (c) document the non-amenability as a research artifact only (no live capital deployment).

This sub-stage preserves the no-archive directive (the strategy is still in the register) while honestly recognizing that not every Python prototype is bridge-cheaply realizable as a C# strategy. Operator choice (c) is recorded as a stage transition to `ninjascript-blocked-by-non-amenable-substrate-research-only`, NOT to a terminal-archive.

### §2. All gates become KPIs

Per the user 2026-05-03 directive, **no metric is binding**. The following ADR-0012 Class A items convert to KPI annotations in the report card:

| ADR-0012 Class A gate | ADR-0013 KPI annotation | Operator implication |
|---|---|---|
| PIT / leakage-canary green | `leakage-canary-pass` / `leakage-canary-fail` (with offending feature factory + canary path enumerated) | A `leakage-canary-fail` annotation **does not exit** the strategy from the research loop, but it triggers binding **annotation + acknowledgment requirements** (NOT gates) per §2.1 below. The operator records the leakage detection in the KPI report card header banner and decides whether to (a) treat the leaked metrics as upper bounds and proceed to NinjaScript implementation under operator-acknowledged-leakage waiver, (b) remediate the leakage in a follow-up cycle, or (c) escalate to a successor hypothesis. Remediation is a follow-up, never a stage gate. |
| BSS > 0 vs climatological prior | `bss-positive` / `bss-flat` (\|BSS\| < 0.05) / `bss-negative` (numeric value reported alongside) | KPI only. A `bss-negative` strategy still progresses to NinjaScript. |
| Reliability slope ∈ [0.7, 1.3] | `reliability-in-band` / `reliability-out-of-band` | KPI only. |
| Reproducibility log present | `repro-log-complete` / `repro-log-incomplete` | KPI only. An incomplete repro log is a follow-up to remediate, not a blocker. |
| DSR / PSR ≥ activation_size | `dsr-positive` / `dsr-marginal` / `dsr-negative` (when family active; n/a otherwise) | KPI only. |
| Hansen SPA p ≤ α at operator-promotion | `spa-passes` / `spa-rejects` (numeric p reported alongside) | KPI only. ADR-0008's omega correction is preserved as the canonical p-value computation; the result is reported in the KPI report card and consulted by operator at promotion review without binding the decision. |

ADR-0012 Class B KPIs are retained verbatim with the same qualitative annotations (`sharpe-vs-passive-{positive,marginal,flat,negative}`, `max-dd-{favorable,comparable,adverse}`, `power-margin-{adequate,marginal,low}`, `mediation-{NIE-significant,NDE-significant,flat}`, `partial-r2-{positive,flat}`, `cost-{robust,conditional,flat}`).

### §2.1. Methodological-correctness annotation banner (NOT a gate; honors `rules/quant-project.md` §Time-series integrity)

Per the user-global [`rules/quant-project.md`](C:/Users/skoir/.claude/rules/quant-project.md) §Time-series integrity ("No look-ahead: every feature must be computable at time t using only data available at time t"), leakage detection is a methodological-correctness invariant, not a performance threshold. ADR-0013 honors this rule **without re-introducing a binding gate** by mandating:

1. **Header banner**: any KPI report card with `leakage-canary-fail` OR `repro-log-incomplete` MUST display a `METHODOLOGICAL-CORRECTNESS-VIOLATION` banner as the **first non-frontmatter, non-title line** of the report-card body, rendered in a visible markdown callout block (e.g., GitHub Flavored Markdown `> [!CAUTION]`), enumerating which annotations failed and which features / canary paths are implicated. The banner must NOT be wrapped in HTML comments (which are invisible in rendered markdown). Banner format pinned by [research/_templates/kpi_report_card_template.md](../../research/_templates/kpi_report_card_template.md). Per Round-2 audit F-2-3 remediation: the prior "first 200 characters" wording conflicted with the YAML-frontmatter convention used elsewhere in the project; the corrected requirement is positional ("first non-frontmatter, non-title line") and visibility-bound ("rendered visible callout, not HTML comment").

2. **Operator-acknowledgment at every promotion**: an operator promoting a strategy with a `leakage-canary-fail` or `repro-log-incomplete` annotation past `kpi-report-emitted` MUST sign a written acknowledgment in `logs/promotions/` that "all reported KPIs are upper bounds; the strategy may underperform its backtested KPIs in paper-trade and live by an unbounded amount". This acknowledgment is documentation, not a gate — the operator can sign it and proceed.

3. **NinjaScript-implementation parity-check exemption**: a strategy at `ninjascript-implemented` with a leaked Python-side prototype produces a parity-check report that flags the leakage on both sides (Python and NinjaScript). The parity check confirms equivalence-of-leakage, not absence-of-leakage. This is a strict honesty requirement and is enforced by §5.2.

4. **Failure-log entry**: `leakage-canary-fail` MUST produce an entry in the per-hypothesis `failure_log.md` per §4.2.

The above 4 requirements are documentation + acknowledgment requirements. They do NOT gate stage progression; the strategy still progresses to `ninjascript-implemented` and beyond per §1 + §5. The user 2026-05-03 directive ("we no longer have gates for failure or passing") is preserved. The `rules/quant-project.md` §Time-series integrity rule is honored as a documentation-and-acknowledgment-strength requirement rather than a binding gate.

### §3. KPI report card — canonical structure

Every strategy at `kpi-report-emitted` MUST publish a KPI report card with the following sections:

```
# {hypothesis_id} — KPI Report Card v{N}
- Hypothesis ID + design.md link + run_id + git_head + dataset_checksum + sidecar_scientific_payload_sha256
- Methodological-correctness observations (former Class A items, now KPIs):
  - leakage-canary annotation per feature factory + per integration test
  - calibration annotations (BSS, reliability slope) — applicable: yes/no/where
  - repro-log annotation (complete/incomplete; if incomplete, list missing fields)
  - DSR annotation (active/n/a)
- Performance KPIs (former Class B items + `rules/quant-project.md` §Reporting mandates):
  - sharpe-vs-passive annotation + numeric ΔSR + CI bounds
  - sharpe-vs-bench annotation + numeric ΔSR + CI bounds (if applicable to hypothesis)
  - sortino annotation + numeric ratio (downside-deviation per Sortino & Price 1994; mandatory per `rules/quant-project.md` §Reporting)
  - max-dd ratio + annotation
  - winrate (per-arm fraction of winning sessions; tertile breakdown wins/losses/zero-returns)
  - turnover annotation + numeric per-day ratio (mandatory per `rules/quant-project.md` §Reporting)
  - capacity-estimate annotation + numeric contracts-per-bar OR notional-USD-per-day estimate (mandatory per `rules/quant-project.md` §Reporting + CLAUDE.md §Standing constraints retail-size ceiling)
  - SPA family p annotation + numeric p
  - power-margin ratio + annotation
  - mediation NIE/NDE annotation + numeric point + CI (if applicable)
  - partial-R² annotation + numeric value (if applicable)
  - cost-floor sensitivity annotation
- **§3.1 Realized OOS + Forward-Projection block (MANDATORY per §3.1 amendment 2026-05-03)** — see §3.1 below
- Build / run history:
  - Per-stage execution record (Stage-1, Stage-2, Stage-3, ...) with run_id + sidecar SHA + per-stage findings
  - Failure log: every external kill, build defect, audit-remediate-loop finding, operator override
- Cross-references:
  - audit-remediate-loop trail paths (3-round cap per round)
  - All ReproLog paths; all sidecar paths
- Versioning:
  - This is version {N}; if {N} > 1, link to all prior versions; corrections produce a NEW version (§4 non-loss mandate forbids in-place overwrite)
```

A KPI report card is produced once per hypothesis at the close of `exploration-in-progress`. If the strategy progresses (e.g., to NinjaScript implementation) and additional empirical evidence accumulates, the report card is **versioned**: report card v2 is appended; v1 is preserved verbatim. See §4.

Per Round-1 audit F-1-10 remediation, a version increment is triggered by a **substantive** change: any modification to KPI numeric values, qualitative annotations, methodological-correctness banner, or build/run history records produces v{N+1}. Cosmetic corrections (typo, formatting, link rewrite, broken-anchor fix) are permitted in-place via append-mode commit annotation; cosmetic edits do NOT require a version increment because no informational content is lost. The pre-commit guard's `SKIE_ALLOW_NON_LOSS_DELETION` override is NOT required for cosmetic edits because no content is deleted.

Per Round-1 audit R-1-8 remediation, the canonical storage location for KPI report cards is `research/01_hypothesis_register/{HID}/{HID}_kpi_report_v{N}.md` (co-located with `design.md`, `stage.md`, and `failure_log.md`). Existing per-hypothesis disposition memos at `reports/{hid}/stage{1,2,3}_*_disposition.md` are preserved verbatim per §4.1 and become referenced exhibits inside the v1 KPI report card's build-history section.

#### §3.1. Realized OOS + Forward-Projection block (MANDATORY per 2026-05-03 amendment)

Per the 2026-05-03 user directive ("the final deliverable of all hypothesis should be similar realized OOS and 2026 projections of strategies, in addition to metrics such as drawdowns, winrates, sharpes, etc."), every KPI report card MUST include a **Realized-OOS + Forward-Projection** block. The block makes the strategy's realized track record + Monte Carlo forward projection a load-bearing operator-review artifact, enabling apples-to-apples comparison across the strategy universe and direct empirical translation to retail-size paper-trade.

**Mandatory contents** per arm × symbol:

1. **Realized OOS equity curve** from a $10,000 starting capital baseline at the OOS-window start:
   - Starting equity (always $10,000 for cross-strategy comparability)
   - Ending equity (dollars)
   - Ending percentage change
   - Realized maximum drawdown (% of peak equity)
   - Win / Loss / Zero-return session counts (W / L / Z); **win rate = W / (W + L + Z)** (project convention; report all three counts so downstream readers can re-compute under W/(W+L) if preferred). Z counts non-trade or exact-zero sessions (e.g., when `sign(y_pred) = 0`).
   - **Realized-path Sharpe** (single-OOS-trajectory annualised mean / std × √252); per F-CONV-1 audit clarification this is **NOT the same statistic** as the canonical CPCV path-distribution median in §3 "Sharpe-vs-passive" (which is the median of 45 per-fold Sharpes, not the single-realised-path Sharpe). Both are reported; the report card MUST label them distinctly to avoid operator confusion.
   - Position-sizing convention: per §3.1.1 below (default = 100%-of-equity per session for daily-cleared single-leg intraday strategies; per-hypothesis override permitted)
   - Cost model applied: explicit yes/no annotation. If "no" (cost-free), the realized equity is an upper bound; cost-aware variant tracked under `P1-{HID}-COST-EMPIRICAL`. **Per F-CONV-2 audit**: rough cost-aware estimates that subtract flat-dollar costs from a compound-equity projection are dimensionally inconsistent and FORBIDDEN as informational; cost-aware projections must apply per-session cost as a log-return drag (`r_t' = r_t - cost_per_session/equity_t`) inside the simulation loop.

2. **Forward 1-year projection** ($10,000 → 252 sessions ahead) via bootstrap from the OOS empirical distribution:
   - Bootstrap configuration: n_paths (default 5,000); n_sessions = 252 (= 1 trading year); RNG seed pinned to `_STAGE3_RNG_SEED + 1000` (project convention; **single seed for cross-arm comparability** per F-CONV-4 audit; per-arm RNG offsets are FORBIDDEN as they introduce undocumented variance across the report card)
   - Sampling method: **must be selected by running Politis-White 2004 on each arm's per-session strategy log-return level series** (not the strategy-minus-bench differential). If PW2004 selects block_length = 1.0 on the level series, iid bootstrap is appropriate; otherwise stationary bootstrap (Politis-Romano 1994) with the PW2004-selected block length per arm. **Per F-CONV-3 audit**: borrowing the LW2008 differential's block_length is NOT acceptable justification — the level series may have residual autocorrelation (e.g., volatility clustering) even when the differential is white. The selected block length is recorded in the sidecar per arm.
   - Reported moments: median, mean, q05, q25, q75, q95 of ending-equity distribution
   - Threshold probabilities: `P(loss)` = P(ending_equity < $10,000); `P(double)` = P(ending_equity ≥ $20,000); `P(<50%)` = P(ending_equity ≤ $5,000). **Per F-CONV-7 audit**: when both threshold columns degenerate to 0/100% (typical for low-volatility strategies at 252 sessions), the report MUST report q01/q99 alongside as supplementary tail anchors so the reader can read the actual distribution shape.
   - Maximum drawdown distribution: median, mean, q05, q95 of per-path peak-to-trough drawdown (% of peak)

3. **Caveats** explicit in the block header:
   - Cost model applicability (cost-free upper bound vs cost-aware projection)
   - Position-sizing realism vs operational margin requirements per [CLAUDE.md §Standing constraints](../../CLAUDE.md) retail-size ceiling
   - Bootstrap-as-generative-model assumption (forward distribution mirrors OOS distribution); **per F-CONV-11 audit**: regime-shift risk and structural breaks beyond the OOS window are NOT modelled — the forward max-DD distribution is a lower bound on regime-conditional realised max-DD per Andrews 1993 ([Econometrica 61(4):821-856](https://doi.org/10.2307/2951764)) on parameter-instability detection
   - Cross-reference to the realized OOS distribution's Sharpe-vs-passive CI from §3 (if CI covers zero, the projection's bands MUST surface this in the P(loss) value)

4. **Cross-strategy comparability table** (rendered automatically when more than one hypothesis has KPI report cards on file): aggregates realized + projected metrics across the strategy universe so the operator can rank candidates by ending-equity-distribution. Tracked under `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD`.

5. **Provenance pinning** (per F-CONV-8 audit): the KPI report card frontmatter MUST include `simulation_log_sha256` and `simulation_script_sha256` alongside the existing `sidecar_scientific_payload_sha256`. Without these, the §3.1 numbers cannot be re-traced to a specific simulation run.

#### §3.1.1. Per-hypothesis sizing-convention override (per F-CONV-6 audit)

The 100%-of-equity / no-leverage / daily-clearing convention in §3.1 item 1 is appropriate for **daily-cleared single-leg intraday strategies** (the H053 archetype). Hypotheses with different structures require an explicit sizing-convention override declared in their `design.md §15 NinjaScript Implementation` section:

| Hypothesis archetype | Sizing convention |
|---|---|
| Daily-cleared single-leg intraday (H053; default) | 100%-of-equity per session, `equity_{t+1} = equity_t × exp(r_t)` |
| HMM-gated multi-bar intraday (H050) | per-state position multiplier × 100%-of-equity-when-active; equity unchanged when state-gated-out |
| Long-short pairs (H051) | 50%-of-equity per leg (long + short); per-leg log-return averaging; net-zero gross exposure target |
| First-hour ORB futures (H052a) | 100%-of-equity at ORB-trigger; position closed at end-of-first-hour or stop-out |
| First-hour 0DTE long-call (H052b) | premium-of-equity-fraction (e.g., 5% premium per call; lots = floor(equity × 0.05 / call_price)) |

The simulator implements the convention declared by the hypothesis; the §3.1 block reports which convention was used in the caveats. **Multi-leg or overnight-exposure variants not in this table are amendable-by-extension** — a hypothesis that introduces a new convention amends this table via project-level ADR (no successor-hypothesis ID required per ADR-0012 §"Frozen pre-registration amendment" §1-§7 immutability discipline).

#### §3.1.2. Deferred-KPI annotation mechanism (per F-CONV-10 audit)

Where [`rules/quant-project.md`](C:/Users/skoir/.claude/rules/quant-project.md) §Reporting mandates a KPI not yet computed in the current report card (e.g., Sortino, turnover, capacity-estimate when only the leakage-clean Sharpe + BSS pipeline has run), the report card MUST list the missing KPI under a §"Mandatory KPIs not yet computed" section with a tracked follow-up. The deferred-follow-up annotation satisfies the rules/quant-project.md reporting mandate (the rule is "every backtest doc lists" the KPI, not "every backtest doc has a non-null value for" the KPI). This is the explicit operational interpretation; the implicit current behavior in H053 v1+v2+v3 conforms.

**Reference implementation**: H053 KPI report card v3 (`research/01_hypothesis_register/H053/H053_kpi_report_v3.md`) is the canonical first realization of §3.1; the simulation primitive is at [scripts/simulate_h053_v4_10k_2026.py](../../scripts/simulate_h053_v4_10k_2026.py). Future hypotheses produce analogous `simulate_{HID}_{stage}_10k_{horizon}.py` scripts.

**`P1-FORWARD-PROJECTION-PRIMITIVE` scope** (per F-CONV-9 audit, tightened): factor the equity-curve + bootstrap-projection helpers into `src/skie_ninja/inference/projection.py` with the following signature contract:

```
projection_summary(
    *,
    strategy_log_returns: np.ndarray,       # per-session strategy log returns; per-arm input
    n_paths: int = 5_000,
    n_sessions: int = 252,
    rng_seed: int = _STAGE3_RNG_SEED + 1000,
    sizing_convention: str = "intraday_daily_clear",  # per §3.1.1 table
) -> ProjectionReport
```

The primitive does **not** own the fit step or the substrate I/O — those remain in per-hypothesis scripts. Helpers to consolidate: `equity_curve_from_log_returns`, `max_drawdown`, `iid_or_stationary_bootstrap_with_pw2004_block_length`, `projection_summary`. Cost-aware extension (`apply_per_session_cost_drag`) per F-CONV-2 audit.

The amendment is binding on all KPI report cards emitted from 2026-05-03 forward. Existing report cards (H053 v1, H053 v2) are preserved verbatim per §4.1; v3 (and future versions) carry the new mandatory block.

### §4. Non-loss / non-deletion mandate

Per the user 2026-05-03 directive ("we will not forget any failures or errors. we will no longer wipe any of the work we conduct"), the following preservation rules are **binding** at the repository / artifact / version-control level **for TRACKED artifacts** (per Round-2 audit F-2-13 remediation; the §4.3 pre-commit guard detects deletion of tracked files via `git diff --diff-filter=D`, so untracked artifacts under protected paths are not under guard protection until they are staged). Operationally:

- **Untracked artifacts under protected paths** must be staged in the commit that produces them. The Round-3 atomic-commit discipline ensures all newly-created run outputs, sidecars, ReproLogs, audit trails, KPI report cards, promotion logs, and NinjaScript strategies are committed alongside the code that produces them. Scripts emitting these artifacts SHOULD include a `git add` step at the end of their execution (or document the manual-stage step) so the operator does not accidentally leave artifacts untracked.
- **Tracked artifacts under protected paths** are guard-protected by §4.3 + the implementation at [scripts/_hooks/check_non_loss_deletion.py](../../scripts/_hooks/check_non_loss_deletion.py).
- **Gitignore exceptions** are required for any subdirectory under a blanket-ignored parent (e.g., `logs/**` is ignored by default; per Round-2 audit R-2-16 + R-1-1 fixes, `logs/promotions/`, `logs/reproducibility/`, `logs/crash_evidence/` all carry explicit un-ignore exceptions in [.gitignore](../../.gitignore)).

#### §4.1 Strict preservation

The following artifacts MAY NOT be deleted, overwritten, or wiped under any circumstance:

1. Hypothesis design.md files — §1-§7 immutable per ADR-0012; §8+§10 amendable only via project-level disposition-philosophy ADR with full audit-remediate-loop trail
2. KPI report cards — corrections produce a **new versioned report card** (`{hypothesis_id}_kpi_report_v{N+1}.md`) with explicit cross-reference to the prior; the prior is preserved verbatim
3. Audit-remediate-loop trails (`docs/audits/`) — every loop record retained
4. ReproLogs (`logs/reproducibility/`) — every run record retained
5. Sidecars + scientific_payload artifacts (`runs/` AND `artifacts/runs/`) — every run output retained. Per Round-1 audit R-1-2 remediation: the canonical run-output root is `artifacts/runs/{HID}/{run_id}/` (where existing H050 + H053 outputs land per CLAUDE.md §"Implemented infrastructure"); `runs/` is a secondary convention used by some scripts (e.g., `runs/h053/stage3_v2/`). Both paths are protected by §4.3.
6. Promotion logs (`logs/promotions/`) — every promotion / deferral / pull / retirement decision retained
7. Failure logs (per §4.2) — every external kill, build defect, run failure, operator override retained
8. NinjaScript strategies (`ninjascript/strategies/`) — every committed C# file retained even after retirement; retirement is a metadata annotation, never a file delete

A correction is a new artifact. A retirement is a metadata transition. **Neither produces a delete.**

#### §4.2 Per-strategy failure log

Every hypothesis register entry under [research/01_hypothesis_register/{HID}/](../../research/01_hypothesis_register/) gains a new file `failure_log.md` that records, in chronological order, every:

- External kill (Windows reboot, OOM, manual interrupt) with timestamp + run_id + diagnosis link
- Build defect caught in audit-remediate-loop with finding ID + commit-of-fix
- Run failure that did not produce a complete sidecar with run_id + cause
- Operator override (e.g., promote despite KPI-leakage-canary-fail) with timestamp + rationale

The failure log is append-only. Entries cannot be removed; corrections produce additional entries (e.g., a "this entry was based on incomplete information; superseded by entry of {date}" annotation).

#### §4.3 Pre-commit guard

A new pre-commit hook is added (per follow-up `P1-NON-LOSS-PRECOMMIT-GUARD`) that rejects any commit deleting:

- A file under `docs/audits/`
- A file under `logs/reproducibility/`
- A file under `logs/promotions/`
- A file under `runs/` (secondary convention)
- A file under `artifacts/runs/` (canonical run-output root per CLAUDE.md §"Implemented infrastructure")
- A file under `research/01_hypothesis_register/` other than via append-mode versioning (specifically: `stage.md` + `failure_log.md` are append-only; `design.md` §1-§7 is immutable; §8+§10 amendable only via project-level disposition-philosophy ADR)
- A file under `ninjascript/strategies/`

The guard fails-closed: any deletion under these paths requires a `# justify:` annotation in the commit message body AND an operator-level override via the env-var `SKIE_ALLOW_NON_LOSS_DELETION=1`. The override semantics are pre-commit-compatible (env-vars thread through to local Python hooks; CLI args do not).

#### §4.3.1 Implementation specification (per Round-1 audit R-1-4 remediation)

Per [.pre-commit-config.yaml](../../.pre-commit-config.yaml) the project's existing local-hook pattern is `repo: local` with `entry: python scripts/_hooks/{check_name}.py`. The non-loss guard implements:

- **File**: [scripts/_hooks/check_non_loss_deletion.py](../../scripts/_hooks/check_non_loss_deletion.py)
- **Detection**: `git diff --cached --name-status --diff-filter=D` — lists files staged for deletion
- **Protected-path regex**: matches deletion targets against the §4.3 protected-path list (literal prefix match)
- **Override**: env-var `SKIE_ALLOW_NON_LOSS_DELETION=1` AND `# justify:` line in `.git/COMMIT_EDITMSG` body — both required
- **Exit code**: 0 if no protected deletion or override valid; 1 otherwise (pre-commit treats non-zero as a failed hook)
- **Pre-commit-config entry**: added under the existing `repo: local` block with `stages: [pre-commit]`

The guard is implemented in the same commit that lands ADR-0013 to honor the §Alternatives §E rationale (avoiding the honor-system window between ADR adoption and guard installation). Calibration of the protected-path regex (e.g., handling rename-with-significant-content-change vs delete) is deferred to follow-up `P1-NON-LOSS-PRECOMMIT-GUARD-CALIBRATION`.

The `git rm` workflow is preserved for un-tracked files; the guard scopes only to tracked artifacts under the protected paths.

### §5. NinjaScript implementation is mandatory and terminal-for-research-loop

Per the user 2026-05-03 directive ("all strategies will be built to fruition to the point of ninja script implementation so we can explore in a practical environment beyond theory"), every strategy in the hypothesis register MUST progress to a working NinjaScript C# implementation in [ninjascript/strategies/](../../ninjascript/strategies/) regardless of KPI report card values. This is non-negotiable.

#### §5.1 New §15 in every hypothesis design.md

Every hypothesis design.md gains a new §15 "NinjaScript Implementation" section enumerating:

- C# class name + file path
- Strategy parameters mapped from the Python prototype's hyperparameter cell
- Entry / exit logic referencing Python signal generation 1:1
- Kill-switch parameters per design.md §11.1
- Fill-log schema matching plan §6.1
- Sim101 smoke-test record (run_id + ScriptSubmission timestamps + position fill timestamps + final P/L)
- Cross-reference to the Python orchestrator script that generated the canonical KPI report card

A strategy that has not produced a §15 record is at `kpi-report-emitted` (or earlier). A strategy that has produced a §15 record AND a Sim101 smoke-test record is at `ninjascript-implemented`.

#### §5.2 Bridge-mediated parity check

Per [ADR-0002](ADR-0002-bridge-selection.md), the Python ↔ NinjaScript bridge implementation is the canonical parity check. Each strategy at `ninjascript-implemented` must produce a parity-check artifact comparing the Python prototype's signal output to the NinjaScript implementation's signal output on a held-out segment of the substrate.

Per Round-1 audit F-1-9 remediation, the parity check is on the **post-discretization integer signal vector** under the strategy's standard discretization rule (which the design.md §15 must document for each strategy — typically `sign(y_hat)` ∈ {-1, 0, +1} for continuous-output strategies, or the strategy's own threshold rule). For strategies that do not produce an integer signal natively, the discretization rule is the primary post-parity contract.

For strategies whose discretization is itself a research-degree-of-freedom (e.g., a quantile-bucketed signal with > 3 bins; e.g., a continuous-position-sized signal), the parity check is on the **float signal vector** with tolerance pinned per follow-up `P1-NINJASCRIPT-PARITY-TOLERANCE` (default: `np.allclose(rtol=1e-5, atol=1e-8)`; per-strategy calibration in design.md §15).

In all cases, the parity check verifies **equivalence**, not absence-of-defect. A leaked Python-side prototype that is faithfully ported to NinjaScript still passes parity (equivalence-of-leakage); §2.1 requires the leakage annotation to be carried into both sides of the parity report.

#### §5.3 Operator-discretion at every promotion

Operator promotion from `ninjascript-implemented` to `paper-trade-active` is **discretionary** on the KPI report card. The operator MAY promote any strategy at `ninjascript-implemented` regardless of report-card values. The operator's promotion decision is logged to `logs/promotions/{run_id}_{hypothesis_id}_{arm_id}_promotion.md` with:

- The KPI report card values at promotion time
- The operator's rationale (free text; ≥ 1 sentence per KPI section)
- Cross-link to ReproLog + sidecar + audit-remediate-loop trails

Same pattern for `paper-trade-active` → `live-promoted`: operator-discretionary on the paper-trade-evaluated KPI report card v2 (which adds the realized-Sharpe-vs-backtest-Sharpe-within-CI observation as a KPI).

### §6. The 60-session-day paper-trade observation is preserved as a KPI

The 60-session-day Sharpe-within-CI observation per [CLAUDE.md §Execution bar](../../CLAUDE.md) is preserved, but reframed:

- Under ADR-0012 it was the **load-bearing pre-live constraint**.
- Under ADR-0013 it is **a KPI on the paper-trade-evaluated stage**, recorded in KPI report card v2.

The operator may launch live capital on a strategy whose realized-Sharpe-within-CI observation diverges from backtest, subject to the operator-discretion mandate of §5.3. Such a divergence is recorded as a KPI annotation (`paper-trade-live-divergent` / `paper-trade-live-aligned`); it does not gate live promotion.

### §7. Cross-validation methodology

CPCV remains the canonical splitter for any hypothesis disposition that produces a Sharpe KPI per ADR-0012 §"Cross-validation methodology" (López de Prado 2018 *Advances in Financial Machine Learning* §12 "Backtesting through Cross-Validation", specifically §12.5 "The Combinatorial Purged Cross-Validation Method"). The `P1-BACKTEST-CPCV` follow-up remains BLOCKING-BEFORE-ANY-NEW-HYPOTHESIS-DISPOSITION-OR-STAGE-3-RE-RUN.

Per Round-1 audit F-1-6 remediation, the 5 CPCV acceptance criteria of ADR-0012 §"CPCV acceptance criteria" are **preserved as KPI annotations** (NOT verbatim as binding criteria — the binding-criterion role conflicts with the no-gates philosophy of §1+§2). Specifically:

| ADR-0012 criterion | ADR-0013 status |
|---|---|
| #1 minimum 45 paths at C(10,2) | Preserved verbatim as the canonical CPCV configuration; n_paths < 45 is annotated `cpcv-paths-deficient` in the report card |
| #2 KS-monotonicity ≤ 0.05 by 30 paths | KPI annotation: `cpcv-ks-converged` / `cpcv-ks-not-converged`. A `cpcv-ks-not-converged` annotation does NOT gate; it is a prominent caveat alongside the median-Sharpe value indicating "distribution-not-converged; treat numeric Sharpe as a point estimate, not a KPI summary" |
| #3 per-path Sharpe distribution moments | Preserved verbatim as report-card-mandatory fields (mean + std + 5%/95% quantiles + median) |
| #4 24-hour wall-clock cap with downsample fallback | Preserved verbatim as an operational guardrail; `cpcv-downsampled` annotation if `n_groups=8` was used |
| #5 DSR computed under CPCV path distribution | Preserved verbatim as a numerical-method specification |

#### §7.1. ADR-0011 post-run audit gate reframe (per Round-1 audit F-1-5 + Round-2 audit F-2-14 remediation)

[ADR-0011](ADR-0011-production-walkforward-runbook.md) §"post-run audit gate" specified a binding admission gate for production walk-forward run outputs to a §10 disposition memo. ADR-0013 dissolves §10 disposition memos in favor of KPI report cards (§3). Per Round-2 audit F-2-14 remediation (a binding "admission gate" by another name would re-introduce a gate, contradicting §1+§2's no-gates philosophy), the post-run audit gate is **converted to a KPI annotation**, not a gate.

The KPI report card carries a `post-run-audit-{pass,fail}` annotation in the methodological-correctness section per §2 (alongside `leakage-canary-{pass,fail}`). Sidecar correspondence + ReproLog completeness checks are reported as numeric details under that annotation. A `post-run-audit-fail` annotation triggers the same documentation+acknowledgment requirements as §2.1 (header banner + operator written acknowledgment in promotion log + failure_log entry), but does **not** gate stage progression. The strategy proceeds to `kpi-report-emitted` with the `post-run-audit-fail` annotation prominently displayed; the operator's review decides downstream stage transitions. A subsequent successful run produces a v{N+1} KPI report card with `post-run-audit-pass` (preserving v{N} verbatim per §4.1).

The narrow effect is that no KPI report card is suppressed by audit-gate failure; instead, audit-gate failure is publicly recorded as a methodological-correctness annotation. This honors the no-gates philosophy while retaining the post-run-audit information for operator review.

## Retroactive re-tag of existing dispositions

Per §1 + §4.1, the following existing dispositions are re-tagged. The original disposition memos are preserved verbatim under §4.1; a new "ADR-0013 retroactive re-tag" section is appended.

### H053 Stage-3 v2 (commits [221a635](https://github.com), [0d1fb08](https://github.com))

Original: `calibration-failed` (under ADR-0012 Class A binding gate).

Re-tag: `kpi-report-emitted` (under ADR-0013 §1 stage progression).

KPI report card v1 carries:

| Symbol | Arm | leakage-canary | bss | reliability | sharpe-vs-passive | sharpe-vs-bench† | spa-family | max-dd | power-margin |
|---|---|---|---:|---|---|---|---:|---|---|
| ES | ElasticNet | pass (14/14) | -0.013 (`bss-flat`) | sentinel-pass | -0.112 (`sharpe-vs-passive-negative`) | positive (placeholder†) | 0.37 (`spa-rejects`) | 1.146 (`max-dd-adverse`) | 0.592 (`power-margin-marginal`) |
| ES | LightGBM | pass (14/14) | -0.176 (`bss-negative`) | sentinel-pass | +0.428 (`sharpe-vs-passive-marginal`)‡ | positive (placeholder†) | 0.37 (`spa-rejects`) | 0.621 (`max-dd-favorable`) | 0.592 (`power-margin-marginal`) |
| NQ | ElasticNet | pass (14/14) | -0.010 (`bss-flat`) | sentinel-pass | +0.472 (`sharpe-vs-passive-marginal`)‡ | positive (placeholder†) | 0.31 (`spa-rejects`) | 0.654 (`max-dd-favorable`) | 0.600 (`power-margin-marginal`) |
| NQ | LightGBM | pass (14/14) | -0.207 (`bss-negative`) | sentinel-pass | +0.422 (`sharpe-vs-passive-marginal`)‡ | positive (placeholder†) | 0.31 (`spa-rejects`) | 0.368 (`max-dd-favorable`) | 0.600 (`power-margin-marginal`) |

† `sharpe-vs-bench` numeric CI is from a Stage-3 v2 implementation placeholder (±0.1, `excludes_zero` hard-coded False per Round-1 audit F-2-5 of [audit_trail_2026-05-03_h053-stage3-v2.md](../audits/audit_trail_2026-05-03_h053-stage3-v2.md)). The placeholder is preserved here (per §4.1 non-loss mandate) but the `positive` annotation is NOT a real CI-excludes-zero verdict; remediation is a follow-up under `P1-H053-STAGE3-V2-ROUND-2-REMEDIATION` (Ledoit-Wolf 2008 paired studentized circular-block bootstrap CI for the AR(1) lag-1 bench differential).

‡ ES LightGBM, NQ ElasticNet, NQ LightGBM `sharpe-vs-passive` are annotated `marginal` (CPCV q05/q95 cover zero; point > 0) per ADR-0012 §B definition (CI excludes zero → `positive`; CI covers zero, point > 0 → `marginal`). The CPCV path-Sharpe q05/q95 spans (audit lines 60-65: ES Arm 2 [-0.5092, +1.5472]; NQ Arm 1 [-0.7371, +1.1949]; NQ Arm 2 [-1.0959, +1.5925]) all cross zero, so `marginal` is the correct annotation under the unchanged ADR-0012 §B rubric.

H053 is at `kpi-report-emitted`. Next stage transition: `ninjascript-implemented` per §5.

### H053 Stage-1 (commit [76599bd](https://github.com))

Original: `archive(null, descriptive-mediation-only)` (under pre-ADR-0012 disposition pipeline; restated under ADR-0012 as `archive(complete; KPI: sharpe-vs-passive-flat)`).

Re-tag: `stage-1-kpi-recorded` (sub-stage of `exploration-in-progress`). Stage-1's KPI annotation (mediator-only paired Sharpe-CI covers zero on both ES and NQ) is preserved verbatim in the H053 report card v1 build-history section.

### H053 Stage-2 (commit [ee2eeaa](https://github.com))

Original: `descriptive-positive` (under ADR-0012 §10.2).

Re-tag: `stage-2-kpi-recorded` with `partial-r2-positive` annotation. Preserved verbatim in build history.

### H053 Stage-3 first-pass (commit [28f93ec](https://github.com))

Original: provisional `archive(null)` reversed by [8c1de7c](https://github.com).

Re-tag: `stage-3-first-pass-defective-substrate` (sub-annotation noting the Daily-405-gate truncation defect; preserved as a build-history record per §3 + §4.2).

### H050 (commits prior to 2026-04-30 post-mortem)

Original: never reached a disposition (per [memo_h050-prodrun-postmortem_2026-04-30.md](../research_notes/memo_h050-prodrun-postmortem_2026-04-30.md)).

Re-tag: `exploration-in-progress`. The 6 production-run failures + retrospective findings are preserved as build-history + failure-log entries.

### H051, H052a, H052b

Original: pre-registered with `status: designed`; not executed.

Re-tag: unchanged (`exploration-in-progress` is the operative stage; `status: designed` is the pre-registration metadata).

## Frozen pre-registration amendment

This ADR amends §8 + §10 of all hypothesis design.md files (H050, H051, H052a, H052b, H053) project-wide per ADR-0012 §"Frozen pre-registration amendment" §1-§4 amendment discipline (this ADR is itself a project-level disposition-philosophy ADR; the amendment discipline preserves §1-§7 immutability).

Per ADR-0012 §"Frozen pre-registration amendment" requirement (c), each affected design.md must reference ADR-0013 explicitly in §8 + §10 + new §15. The cascade is tracked under follow-up `P1-ADR-0013-DESIGN-MD-CASCADE` and is NOT BLOCKING for the ADR's adoption (the ADR is in force at landing; the per-design.md citation is housekeeping).

## Alternatives considered

### A. Keep ADR-0012 binding gates; relax calibration gate to KPI only

Rejected. The user 2026-05-03 directive is unambiguous: NO gates. A half-measure preserving leakage-canary as binding (e.g.) would re-introduce a gating-philosophy regression — the precipitating event for this ADR is the user's view that gating itself is the defect, not any specific gate.

### B. Convert ADR-0012 dispositions to KPIs but retain `archive` as a stage label

Rejected. The user explicitly states "we will archive no more strategies or results." The word `archive` is removed from disposition vocabulary entirely. Stage labels under §1 are progression labels (`exploration-in-progress`, `kpi-report-emitted`, etc.); none are terminal-archive.

### C. Allow operator-override of any binding gate via written justification

Rejected. This was operationally indistinguishable from "no gates" while preserving the gating language. The user's directive cleanly prefers the no-gates framing.

### D. Make NinjaScript implementation optional / contingent on positive KPI report card

Rejected. The user explicitly mandates "all strategies will be built to fruition to the point of ninja script implementation". This is a project-level commitment; conditioning it on KPI values reintroduces gating.

### E. Treat the non-loss mandate as advisory rather than enforced

Rejected. Without the §4.3 pre-commit guard the non-loss mandate is honor-system. The guard makes deletion accidents-of-process detectable and operator-overridable.

## Consequences

### Adopted

- All ADR-0012 Class A items become KPIs in the report card; none gates a stage transition.
- Stage progression replaces disposition labels.
- NinjaScript implementation is mandatory and terminal-for-research-loop.
- Non-loss mandate enforced via pre-commit guard + per-strategy failure log + versioned KPI report cards.
- The 60-session-day paper-trade Sharpe-within-CI observation is reframed from constraint to KPI.
- ADR-0003 SPA-vs-RomanoWolf and ADR-0008 SPA omega method are downgraded to KPI computation; preserved as canonical p-value computations.
- ADR-0012 is preserved as historical record (§4.1 non-loss); its supersession is logical, not physical.

### Trade-offs accepted

- **Methodologically incorrect (leakage-canary-fail) strategies CAN reach NinjaScript implementation and paper-trade.** Mitigated by: (a) `leakage-canary-fail` is a prominent KPI on the report card header; (b) operator-discretion at every promotion is the structural safeguard; (c) the non-loss mandate ensures the leakage finding is permanently in the record for any subsequent audit.
- **Calibration-failed strategies CAN reach NinjaScript and paper-trade.** Same mitigations.
- **The NinjaScript-implementation pipeline becomes the bottleneck.** NT8 capacity is finite (Sim101 paper-account is single-strategy at a time); paper-trade allocation is sequential per operator priority. Throughput is not a project goal under this ADR; depth-of-exploration is.
- **Multiple-testing concern (formerly addressed at design-time SPA gate) is no longer enforced at any gate.** SPA p remains a reported KPI; readers wanting Bonferroni-corrected disposition can synthesize from the KPI report card.
- **Operator review burden grows.** Every stage transition is a discrete operator decision, logged with rationale. This is a deliberate trade for the no-gating philosophy.

### Residual risk

- A leakage-detected strategy with a positive Sharpe KPI could mislead the operator if the KPI report card is read incompletely. Mitigated by: (a) `leakage-canary-fail` must appear in the report-card header (§3 canonical structure); (b) each KPI annotation carries its applicability flag; (c) the failure log is append-only.
- The 60-session-day paper-trade observation (now KPI, formerly load-bearing) could divergence-report-without-action if operator does not actively review. Mitigated by: (a) `paper-trade-live-divergent` annotation on KPI report card v2; (b) operator-discretion + decision-logging at every stage transition.
- The non-loss mandate creates monotonic repository growth. Mitigated by: (a) `git lfs` for large run-output binaries (operational follow-up `P1-NON-LOSS-LFS-MIGRATION`); (b) repository-level audit of artifact sizes annually.

## Empirical justification

The empirical basis is the H053 Stage-3 v2 disposition under ADR-0012 (calibration-failed across all 4 arm × symbol combinations) and the user's 2026-05-03 directive (verbatim citation in §Context). Per the user, the disposition correctly flags weak calibration but archives a strategy the user wishes to continue exploring through to NinjaScript implementation; the gating philosophy itself is the defect. ADR-0012's aspirational-MVP framing is preserved; what changes is the gating regime and the requirement that all strategies reach NinjaScript.

The CLAUDE.md user-global §"Evidence Hierarchy" is preserved unchanged: peer-reviewed → official docs → professional standards → vetted forums → reproduction. The ADR-0013 KPI report card structure IS evidence quality; a single-gate pipeline is not.

## References

- [ADR-0012](ADR-0012-disposition-philosophy-aspirational-mvp.md) — superseded by §1 + §2 of this ADR.
- [ADR-0011](ADR-0011-production-walkforward-runbook.md) — production walk-forward runbook; preserved.
- [ADR-0010](ADR-0010-multi-hour-run-process-protection.md) — multi-hour run process protection; preserved.
- [ADR-0008](ADR-0008-spa-omega-method.md) — SPA omega correction; preserved as KPI computation.
- [ADR-0003](ADR-0003-spa-vs-romanowolf.md) — SPA vs Romano-Wolf; superseded by §2 (SPA fully downgraded to KPI).
- [ADR-0002](ADR-0002-bridge-selection.md) — Python ↔ NinjaScript bridge; load-bearing for §5.2 parity check.
- [CLAUDE.md §Evidence bar](../../CLAUDE.md) — replaced by §"KPI report card" framing in this ADR.
- [CLAUDE.md §Execution bar](../../CLAUDE.md) — 60-session-day Sharpe-within-CI is reframed as KPI.
- [CLAUDE.md §Research philosophy](../../CLAUDE.md) — strengthened with non-loss + NinjaScript-terminus mandates per this ADR.
- [docs/audits/audit_trail_2026-05-03_h053-stage3-v2.md](../audits/audit_trail_2026-05-03_h053-stage3-v2.md) — H053 Stage-3 v2 disposition under ADR-0012; the precipitating event.
- [docs/audits/audit_trail_2026-05-03_adr-0013-permanent-exploration.md](../audits/audit_trail_2026-05-03_adr-0013-permanent-exploration.md) — this ADR's audit-remediate-loop trail.
- Brier, G. W. 1950. "Verification of forecasts expressed in terms of probability." *Mon. Wea. Rev.* 78(1):1-3. [DOI 10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2). (Brier Score primary source; preserved as KPI computation.)
- Murphy, A. H. 1973. "A new vector partition of the probability score." *J Appl Meteor* 12:595-600. [DOI 10.1175/1520-0450(1973)012<0595:ANVPOT>2.0.CO;2](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2). (Brier Skill Score = 1 - BS / BS_ref skill-score construction; per Round-1 audit L-1-1 remediation — Brier 1950 introduced the score; Murphy 1973 is the more direct attribution for the skill-score formulation.)
- Niculescu-Mizil, A. & Caruana, R. 2005. "Predicting good probabilities with supervised learning." ICML 2005. [DOI 10.1145/1102351.1102430](https://doi.org/10.1145/1102351.1102430). (Reliability diagram concept; recommends isotonic regression + Platt scaling. Per Round-1 audit L-1-2 remediation: the specific [0.7, 1.3] reliability-slope band is a **project-operational threshold**, not stated in NM&C 2005's primary text. Empirical calibration of the band is tracked under follow-up `P1-RELIABILITY-SLOPE-EMPIRICAL-CALIBRATION`.)
- López de Prado, M. 2018. *Advances in Financial Machine Learning*, Chapter 12 "Backtesting through Cross-Validation", especially §12.5 "The Combinatorial Purged Cross-Validation Method". Wiley. ISBN 978-1-119-48208-6. (CPCV reference; methodology preserved. Per Round-1 audit L-1-3 remediation: chapter title corrected from "§12 (CPCV)" to the correct "Backtesting through Cross-Validation" with §12.5 sub-section pin.)
- Hansen, P. R. 2005. "A test for superior predictive ability." *J Bus Econ Stat* 23(4):365-380. [DOI 10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063). (SPA reference; preserved as KPI computation.)
- Sortino, F. A. & Price, L. N. 1994. "Performance measurement in a downside risk framework." *J Investing* 3(3):59-64. [DOI 10.3905/joi.3.3.59](https://doi.org/10.3905/joi.3.3.59). (Sortino ratio reference; mandatory KPI per `rules/quant-project.md` §Reporting.)

## Follow-ups

### Cascade (housekeeping; not blocking the ADR's adoption)

- `P1-ADR-0013-DESIGN-MD-CASCADE` — cascade ADR-0013 references into all hypothesis design.md §8 + §10 + add new §15 NinjaScript Implementation section. **BLOCKING-BEFORE-FIRST-NEW-HYPOTHESIS-PRE-REGISTRATION** per ADR-0012 §Frozen pre-registration amendment requirement (c). Minimal cascade (5 design.md §8 references) lands inline with this ADR commit per Round-1 audit F-1-8 remediation; the §10 and §15 additions follow.
- `P1-ADR-0013-DISPOSITION-FRAMEWORK-REFACTOR` — refactor [src/skie_ninja/inference/disposition.py](../../src/skie_ninja/inference/disposition.py) to remove Class A binding logic, retain KPI report card emission, add stage progression tracking + KPI report card v{N} versioning. **BLOCKING-BEFORE-NEXT-STAGE-3-RUN** per Round-1 audit R-1-11 remediation: the existing module still emits ADR-0012 disposition_class enum values (including `archive(complete; KPI report)`), so any new run between this commit and the refactor produces sidecars with stale-vocabulary fields that pollute the post-2026-05-03 KPI-report-card record under §4.1 non-loss.
- `P1-ADR-0013-PROMOTION-LOG-REFACTOR` — refactor `emit_promotion_log` to use new stage names + operator-rationale fields
- `P1-ADR-0013-CLAUDE-MD-CASCADE` — full CLAUDE.md amendment for §Evidence bar + §Execution bar + §Research philosophy (this commit lands the minimal changes; the comprehensive cascade is the follow-up)

### Non-loss enforcement

- `P1-NON-LOSS-PRECOMMIT-GUARD` — implement the §4.3 pre-commit guard (fail-closed deletion check on protected paths; `--allow-non-loss-deletion` operator override flag)
- `P1-NON-LOSS-PRECOMMIT-GUARD-CALIBRATION` — operational threshold tuning for the guard
- `P1-NON-LOSS-LFS-MIGRATION` — `git lfs` migration for large run-output binaries to bound monotonic repository growth
- `P1-NON-LOSS-FAILURE-LOG-TEMPLATE` — failure log template under [research/_templates/](../../research/_templates/) for new hypotheses

### NinjaScript pipeline

- `P1-NINJASCRIPT-CASCADE` — every existing hypothesis (H050, H051, H052a, H052b, H053) gains a NinjaScript implementation per §5; sequenced by operator priority
- `P1-NINJASCRIPT-PARITY-TOLERANCE` — operational threshold for Python ↔ NinjaScript signal-vector equality (default: byte-equality on integer signal vector; calibrated per-strategy as needed)
- `P1-NINJASCRIPT-SIM101-SMOKE-TEMPLATE` — Sim101 smoke-test record template under [research/_templates/](../../research/_templates/)
- `P1-H053-NINJASCRIPT-IMPL` — H053 Cycle 11 NinjaScript implementation; FIRES under §5 (was conditional on positive KPI under ADR-0012; now mandatory)
- `P1-H050-NINJASCRIPT-IMPL` — H050 NinjaScript implementation; sequenced after H050 production walk-forward Stage-3 KPI report card emission

### KPI report card

- `P1-KPI-REPORT-CARD-TEMPLATE` — canonical KPI report card template under [research/_templates/](../../research/_templates/) per §3
- `P1-KPI-REPORT-CARD-VERSIONING-TEST` — regression test that creating report card v{N+1} does not delete v{N}
- `P1-KPI-REPORT-CARD-DAYNAUT-DASHBOARD` — operational dashboard summarizing KPI report card values across the strategy universe (operator review aid)
- `P1-CROSS-HYPOTHESIS-SPA-PANEL` — derivative artifact aggregating per-arm Sharpe-vs-passive distributions across the entire strategy universe (m=Σ(arms × symbols) per the family across H050+H051+H052a+H052b+H053+...) and computing the omega-corrected family-wise Hansen 2005 SPA p-value. Per Round-1 audit F-1-11 remediation: this panel is a derivative (regenerated from the union of KPI report cards) and is NOT itself a gate; the no-gating philosophy is preserved. Each KPI report card v{N} cross-links to the latest panel snapshot. Honors `rules/quant-project.md` §Inference multiple-testing mandate without re-introducing a binding gate.

### Retroactive re-tag

- `P1-ADR-0013-H053-RETROACTIVE-RETAG-EXECUTE` — apply the §"Retroactive re-tag" H053 mappings to existing disposition memos (corrections produce versioned successors per §4.1)
- `P1-ADR-0013-H050-RETROACTIVE-RETAG-EXECUTE` — same for H050 + H051 + H052a + H052b

This ADR is the canonical reference for the SKIE-Universe project's disposition philosophy from 2026-05-03 forward. It supersedes ADR-0012 logically; ADR-0012 is preserved as historical record per §4.1 non-loss mandate.
