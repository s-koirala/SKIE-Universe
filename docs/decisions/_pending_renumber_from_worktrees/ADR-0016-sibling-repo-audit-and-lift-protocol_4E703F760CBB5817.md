---
id: ADR-0016
title: Sibling-repo audit-and-lift protocol — promoting SKIE-Ninja / SKIE-NINJA-Volatility / SKIE-NINJA-0DTE / SKIENINJA-V3 artifacts into SKIE-Universe successors
status: proposed
date: 2026-05-06
deciders: skoir
amends:
  - (none — additive; introduces a new project-level discipline)
preserves_immutability_of:
  - ADR-0006 scope extension authorizing parallel tracks (this ADR adds a discipline for cross-track artifact promotion, NOT a new track)
  - ADR-0013 permanent-exploration framework
  - ADR-0007 embargo placement
  - ADR-0008 SPA omega-method default
  - All previously frozen design.md §1-§7 sections
---

# ADR-0016 — Sibling-repo audit-and-lift protocol

## Context

The operator maintains four ML-bearing sibling GitHub repositories under the `s-koirala` namespace, each predating the SKIE-Universe Cycle 4 (2026-04-23) purged-walk-forward + leak-canary discipline:

- [s-koirala/SKIE-Ninja](https://github.com/s-koirala/SKIE-Ninja) — Smart Algorithmic Trading System for NinjaTrader; ML-based futures trading with 500+ engineered features per repo description.
- [s-koirala/SKIE-NINJA-Volatility](https://github.com/s-koirala/SKIE-NINJA-Volatility) — volatility-expansion timing; per repo description claims AUC 0.77–0.84 under CPCV validation.
- [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) — QQQ first-hour long-call 0DTE scalp (internal SKIE-ORB-CALL), cross-validated on NQ/MNQ futures per [ADR-0006](ADR-0006-scope-extension-hmm-0dte.md) §"Decision (proposed)".
- [s-koirala/SKIENINJA-V3](https://github.com/s-koirala/SKIENINJA-V3) — BTC range-expansion strategy.

The H055 successor tree at [plan/h055_successor_tree_2026-05-06.md](../../plan/h055_successor_tree_2026-05-06.md) (concurrent landing) authorizes H056 + H057 to LIFT model artifacts from these siblings into SKIE-Universe walk-forward runs. Without a formal audit + substrate-compatibility check, the lift would inherit unaudited backtest claims into a SKIE-Universe successor's design.md §3-§5 features / labels / estimators. The siblings predate:

- Cycle 4 leak canaries at [src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py) (fold-boundary invariant; label-horizon purge; dual-fit-call observer).
- Cycle 4 purged + embargoed walk-forward at [src/skie_ninja/backtest/](../../src/skie_ninja/backtest/) per AFML §7.4 ([López de Prado 2018](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086), Wiley, ISBN 978-1119482086, *practitioner*) and [Bergmeir & Benitez 2012](https://doi.org/10.1016/j.ins.2011.12.028) Information Sciences 191:192-213.
- ADR-0007 stacked-embargo binding.
- ADR-0008 SPA omega-method default + Hansen 2005 §2.4 SPA_l/SPA_c/SPA_u variants.
- ADR-0009 ReproLog 13-field schema with `git_head` + `dataset_checksum` + `RNG_seed` + `model_hash` + `pip_freeze_sha256`.

ADR-0006 authorizes parallel tracks but does NOT codify the cross-track artifact promotion gate. ADR-0016 fills that gap. The decision scope is precisely:

1. The audit checklist every sibling-repo artifact MUST pass before being lifted.
2. The audit-remediate-loop application to sibling-repo artifacts.
3. The substrate-compatibility check.
4. The frozen-pre-reg-amendment vs new-hypothesis-ID disposition for the lift.

ADR-0016 is additive — it does not amend any prior ADR or any frozen design.md §1-§7 section.

## Decision — Audit checklist

Every sibling-repo artifact promoted into a SKIE-Universe successor MUST pass the seven-section checklist below. The checklist is applied to a specific commit SHA of the sibling repo at lift time; later sibling commits constitute new lift events (per §"Consequences" residual risk).

### 2.1 Substrate-compatibility check

The lift is gated on substrate equivalence with the SKIE-Universe canonical substrate at [data/processed/vendor_legacy_1min_roll_adjusted/](../../data/processed/vendor_legacy_1min_roll_adjusted/) (combined SHA256 `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`; ES + NQ 2015-01-01 → 2025-12-{03,20}; AFML §2.4.3 anchor invariant verified empirically).

Three dispositions:

- **(a) Re-train on SKIE-Universe substrate (PREFERRED)**: the sibling architecture + hyperparameters are lifted; the model is re-fit end-to-end on the SKIE-Universe substrate under the project's purged-WF discipline. Eliminates the substrate gap.
- **(b) Substrate-translation layer with PIT-verified equivalence**: a translation function maps the sibling's substrate cell-by-cell to the SKIE-Universe cell space; PIT correctness verified at the leak-canary layer; bit-equivalence test on a held-out window. Acceptable only when (a) is computationally infeasible.
- **(c) Treat sibling output as INPUT FEATURE, NOT label**: the sibling's prediction is consumed as an exogenous feature in the receiving successor's design.md §3 feature factory, with PIT-availability verified at the FEATURE level (the input must be available at time t with data ≤ t per the ADR-0006 0DTE-track precedent). Lowest-cost disposition; forfeits the sibling's claimed performance metrics.

**Substrate SHA256 binding (mandatory regardless of disposition).** The sibling's training-time substrate SHA256 MUST be RECORDED in the receiving SKIE-Universe successor's `data_requirements.md` alongside the SKIE-Universe substrate SHA256, with explicit annotation of which disposition was selected. The substrate gap (if any) is disclosed honestly per the H055 [data_requirements.md](../../research/01_hypothesis_register/H055/data_requirements.md) cross-hypothesis fit-set isolation table convention.

### 2.2 PIT-correctness audit

The sibling artifact's training script is reproduced inside the SKIE-Universe leakage-canary harness at [src/skie_ninja/backtest/leak_canaries.py](../../src/skie_ninja/backtest/leak_canaries.py). Three-canary verification:

- **Fold-boundary invariant** (canary a) — monotonicity gate; train index strictly precedes test index by ≥ embargo; no train-row leaks into test fold.
- **Label-horizon purge** (canary b) — labels with horizon h > 0 purged from the train set when their event window overlaps the test fold (AFML §7.4.1 "Purging the Training Set"; per the 2026-04-30 post-mortem citation correction at [memo_h050-prodrun-postmortem_2026-04-30.md](../../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md) §O-3, AFML has no HMM chapter — the §7.4.1 reference is purging-specific).
- **Dual-fit-call observer** (canary c) — `TracingArray` capability proxy with `_array` + `__slots__` per Cycle 4 R-2 audit; refuses any code path that calls `.fit()` on the test panel.

If any canary trips, the sibling artifact CANNOT be lifted as-is under disposition (a) or (b); the only remaining path is disposition (c) (treat output as feature, not label) — and even then, the sibling's reported metrics are forfeit. Re-training under the SKIE-Universe leak-canary harness is the canonical remediation path (disposition a).

### 2.3 Walk-forward discipline audit

Was the sibling artifact validated under purged + embargoed walk-forward per [López de Prado 2018](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) Ch. 7 + [Bergmeir & Benitez 2012](https://doi.org/10.1016/j.ins.2011.12.028) + [Tashman 2000](https://doi.org/10.1016/S0169-2070(00)00065-0) International Journal of Forecasting 16(4):437-450? Sub-checks:

- If sibling used k-fold without purge: validation does NOT satisfy SKIE-Universe standards; re-validate under disposition (a).
- If sibling used CPCV without explicit purge gap: ADR-0006 §"Cross-repo multiple-testing reconciliation (Round 3)" treats the sibling-repo CPCV gate as a PRIOR SCREEN, not as a SKIE-Universe-discipline-equivalent validation; re-validate.
- Fold geometry recorded: IS / OOS lengths; embargo (per ADR-0007 stacked-embargo binding); purge (per AFML §7.4.1).
- Single train/test cuts are insufficient per CLAUDE.md "Cross-validation methodology"; CPCV remains the canonical splitter for any disposition that produces a Sharpe KPI.

### 2.4 Multiple-testing audit

How many configurations / hyperparameter cells did the sibling explore before reporting the headline metric? The sibling's headline metric (e.g., SKIE-NINJA-Volatility's AUC 0.77-0.84) is selection-bias-adjusted via:

- **[Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094)** Journal of Portfolio Management 40(5):94-107 — deflated Sharpe ratio applied to any reported Sharpe.
- **[Harvey & Liu 2015](https://doi.org/10.3905/jpm.2015.42.1.013)** Journal of Portfolio Management 42(1):13-28 — backtesting haircut for selection-bias-adjusted minimum effect size.
- **[Harvey, Liu & Zhu 2016](https://doi.org/10.1093/rfs/hhv059)** Review of Financial Studies 29(1):5-68 — multiple-testing crisis context; per the H055 lit-review correction (Harvey-Liu RFS 2014 → "Co-opted Boards" was the wrong paper; the H055 audit replaced it with Harvey-Liu 2015 JPM 42(1):13-28 and Harvey-Liu-Zhu 2016 RFS 29(1):5-68 — same correction applied here).

If the sibling reports AUC / Brier / etc. without explicit multi-testing correction, the artifact is flagged `mt-correction-pending` and lifted as a candidate-for-evaluation, NOT a validated-artifact. Disposition (a) re-training automatically subjects the lifted artifact to the receiving successor's pre-registered SPA family + ADR-0008 omega method.

### 2.5 Calibration audit (probabilistic outputs)

For sibling outputs that are probabilities (e.g., long-premium 0DTE call-scalp green-rate from SKIE-ORB-CALL):

- Brier Skill Score (BSS) vs per-instrument climatological prior on the sibling's holdout fold; required `bss-positive` annotation per CLAUDE.md "KPI annotations" item 2.
- Reliability slope ∈ [0.7, 1.3] per CLAUDE.md "KPI annotations" item 3 (project-operational threshold; empirical calibration tracked under `P1-RELIABILITY-SLOPE-EMPIRICAL-CALIBRATION`).
- If sibling produces a sign-only or threshold-only output without calibration, the output is treated as a FEATURE input under disposition (c), NOT a probability — calibration cannot be retroactively claimed.

### 2.6 Reproducibility log compatibility

Does the sibling artifact carry the ReproLog 13-field schema per ADR-0009? Specifically: `git_head`, `dataset_checksum`, `RNG_seed`, `model_hash`, `pip_freeze_sha256`, plus the eight remaining fields per [src/skie_ninja/utils/reproducibility.py](../../src/skie_ninja/utils/reproducibility.py) `ReproLog` frozen dataclass.

If not, the lift cannot satisfy ReproLog without remediation; missing fields are added at lift time by re-running the sibling artifact under a SKIE-Universe `RunContext` ctx manager. Disposition (c) is exempt from full ReproLog reconstruction since the sibling output is consumed as a feature, but its source commit SHA + emit-time substrate SHA256 MUST be recorded.

### 2.7 License + provenance

All four sibling repos (SKIE-Ninja, SKIE-NINJA-Volatility, SKIE-NINJA-0DTE, SKIENINJA-V3) are under the `s-koirala` operator-owned namespace; license is implicit operator-grant. Provenance binding:

- Sibling repo URL.
- Sibling repo commit SHA at lift time (pinned; mandatory).
- Lift-event timestamp (ISO 8601 UTC).
- Disposition selection (a / b / c) with rationale.
- Substrate SHA256 (sibling + SKIE-Universe canonical) per §2.1.

The pinned commit SHA is the load-bearing provenance anchor; any subsequent sibling commit constitutes a NEW lift event under §"Consequences".

## Decision — Lift dispositions

Three paths, ordered by ascending preservation cost and descending external dependency:

### 3.1 Lift-as-feature (disposition c)

Sibling output becomes an input feature in the receiving successor's design.md §3. The output is treated as exogenous; no validation of the sibling's internal training is required at the SKIE-Universe layer; PIT-correctness is verified at the FEATURE level (input must be available at time t with data ≤ t per ADR-0006 §"Decision (proposed)" QQQ-track precedent). Lowest cost; forfeits any of the sibling's claimed performance metrics — they do NOT attach to the receiving successor's KPI report card §"Performance KPIs". The sibling's headline metric is recorded only as a build-history annotation in the audit-remediate-loop trail.

### 3.2 Lift-and-retrain (disposition a)

Sibling architecture + hyperparameters lifted; re-trained on SKIE-Universe substrate under purged-WF + leak canaries; new design.md authored as a new hypothesis ID per the §"Frozen-pre-reg amendment vs new-hypothesis-ID disposition" rule below. Medium cost; preserves the sibling's architectural choices (e.g., feature engineering patterns, model class, hyperparameter search domain) while producing a fresh validation under SKIE-Universe discipline. The sibling's reported metrics are recorded as PRIOR-LITERATURE annotations in the new design.md §1; they do NOT bind H_1.

### 3.3 Lift-and-replace

Sibling's specific algorithm rejected (e.g., trips a leak canary; uses k-fold without purge and the algorithm is non-trivially coupled to the leakage path). Receiving successor builds the component from scratch following SKIE-Universe discipline; sibling cited as inspirational only in the new design.md §1. Highest cost; sometimes unavoidable when the sibling's leakage is structural (e.g., target encoding without fold-disjoint fit; PCA fit on full panel before split).

**Frozen-pre-reg amendment vs new-hypothesis-ID disposition for the lift.** Per ADR-0012 §"Frozen pre-registration amendment" (preserved by ADR-0013), §1-§7 of a frozen design.md (hypothesis statement, universe/sample, features, labels, splitter, cost model) are immutable. A sibling-repo lift that introduces a new feature vector or a new label space therefore CANNOT amend an existing frozen design.md — it MUST be authored as a new hypothesis ID (e.g., H056, H057 under the H055 successor tree). A lift that introduces a new ESTIMATOR but preserves the §3 features + §4 labels + §5 splitter + §6 cost model MAY land as a new arm under an existing hypothesis's design.md §15 NinjaScript implementation block (per ADR-0013 §5), but only if the receiving design.md §1 H_1 formulation explicitly enumerated multiple estimator arms ex ante. The default — and the disposition selected for H056 / H057 in the H055 successor tree — is **new hypothesis ID per lift**.

## Decision — Audit-remediate-loop application

Each sibling-repo artifact lift requires its own audit-remediate-loop trail at `docs/audits/audit_trail_YYYY-MM-DD_sibling-lift-{repo-name}.md` per the project's ~/.claude/CLAUDE.md "Agentic Iteration" + the project SKILL.md 3-round cap ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751); 3 is operational). The loop runs proper-isolated agents per the post-Cycle-6 discipline:

- **Round 1**: parallel quant-auditor + literature-check + reproducibility-verifier on the sibling repo at the pinned commit SHA. Findings classified per the H050 / H053 audit-loop conventions.
- **Round 2**: remediation against R1 findings; verification by an isolated agent (NOT the same agent that did the remediation, per the post-Cycle-6 "main-thread orchestration is the workaround" discipline).
- **Round 3**: verification-only round; cap reached at R3 per SKILL.md.

Findings classification:

- **BLOCKER**: cannot lift under any disposition (e.g., sibling artifact's training script is unrecoverable; substrate gap is fundamental and disposition (b) is infeasible). Lift is rejected; sibling stays in its repo; receiving successor either drops the dependency or pursues disposition (c) on a different sibling output.
- **MAJOR**: must remediate before lift. Examples: leak canary trips under disposition (a); ReproLog field missing; substrate SHA256 not recorded.
- **MINOR**: annotate-and-lift. Examples: sibling docstring imprecision; non-load-bearing citation drift; cosmetic naming.

The audit-remediate-loop trail is appended to the receiving successor's [failure_log.md](../../research/01_hypothesis_register/H055/failure_log.md) per ADR-0013 §4 non-loss mandate so retirement is impossible without preserving the lift history.

## Alternatives considered

### A. No protocol — operator decides per-lift

Rejected per [~/.claude/CLAUDE.md](../../../skoir/.claude/CLAUDE.md) §"Parameter & Prompt Selection" zero-arbitrary-thresholds discipline. Ad-hoc lift produces unreproducible audit trails; the per-lift discovery cost varies; cross-lift comparability for `P1-CROSS-STRATEGY-COMPARABILITY-DASHBOARD` is forfeit.

### B. Hard ban on sibling-repo lifts

Rejected. ADR-0006 explicitly authorizes parallel tracks (HMM regime + 0DTE), and the four sibling repos contain validated work — SKIE-NINJA-Volatility's claimed AUC 0.77-0.84 under CPCV is a load-bearing prior signal that the project should leverage if (and only if) it survives the §2 audit. Banning lifts forfeits the operator-owned IP without scientific gain.

### C. Auto-lift any artifact with a sibling-repo CPCV claim

Rejected. The sibling repos predate SKIE-Universe's leak-canary discipline (Cycle 4, 2026-04-23); CPCV alone is insufficient evidence of leak-freedom. Per ADR-0006 §"Cross-repo multiple-testing reconciliation (Round 3)", sibling-repo CPCV is treated as a PRIOR SCREEN, not as SKIE-Universe-discipline-equivalent validation — auto-lift would conflate the two and inherit unaudited backtest claims.

## Consequences

### Adopted

- The seven-section §2 audit checklist applied to every sibling-repo artifact at lift time.
- Three lift dispositions §3.1 / §3.2 / §3.3 with explicit cost ordering and `data_requirements.md` recording obligations.
- Per-lift audit-remediate-loop trail under `docs/audits/audit_trail_YYYY-MM-DD_sibling-lift-{repo-name}.md`.
- New-hypothesis-ID-per-lift as the default disposition (per ADR-0012 §"Frozen pre-registration amendment" + ADR-0013 §1-§7 immutability).

### Trade-offs accepted

- Each lift adds substantial discovery cost (full audit-remediate-loop + new design.md authorship + walk-forward re-validation under disposition (a)). The H055 successor tree's H056 / H057 lifts will each require ~1 calendar week of audit-remediate cycles based on the H050 + H053 + H052a Phase B + H055 design audit precedents.
- Some siblings may fail the §2 audit and require disposition (c) or §3.3 lift-and-replace; this is acceptable — the protocol is correctly calibrated to reject leakage-tainted artifacts rather than smuggle them in.
- Cross-repo SPA family construction is NOT closed by this ADR (the broader question per `P1-CROSS-HYPOTHESIS-SPA-FAMILY-CONSTRUCTION-ADR`); ADR-0016 governs the per-artifact lift gate, not the family-wise correction across siblings.

### Residual risk

- Sibling repos may evolve post-lift. Mitigation: the pinned commit SHA at lift time is the canonical provenance anchor (per §2.7); any subsequent sibling commit constitutes a NEW lift event subject to a fresh §2 audit. The receiving successor's `data_requirements.md` records the pinned SHA so a sibling-repo `git push --force` cannot retroactively invalidate the lift.
- The §2 audit checklist may itself drift if SKIE-Universe discipline evolves (e.g., a Cycle 8 amendment to leak canaries). Mitigation: ADR-0016 amendments via the project-level frozen-pre-reg amendment discipline; concurrent ADR landing alongside the discipline change.
- Audit cost may discourage lift adoption when disposition (a) is computationally expensive (e.g., SKIE-Ninja's 500+ feature ML system). Mitigation: disposition (c) lift-as-feature is always available at lower cost; the receiving design.md §1 may explicitly elect (c) ex ante.

## References

- [ADR-0001 project scope](ADR-0001-project-scope.md) — capacity ceiling binding for any lifted strategy.
- [ADR-0005 HMM regime toolkit](ADR-0005-hmm-regime-toolkit.md) — canonical regime-inference toolkit for HMM-using lifts.
- [ADR-0006 scope extension HMM + 0DTE](ADR-0006-scope-extension-hmm-0dte.md) — sibling-repo cross-reference precedent + sibling-CPCV-as-prior-screen rule.
- [ADR-0007 embargo placement](ADR-0007-embargo-placement.md) — stacked-embargo binding for §2.3 audit.
- [ADR-0008 SPA omega method](ADR-0008-spa-omega-method.md) — SPA p computation for §2.4 audit.
- [ADR-0009 BLAS thread pinning](ADR-0009-blas-thread-pinning.md) — ReproLog 13-field schema for §2.6 audit.
- [ADR-0012 disposition philosophy](ADR-0012-disposition-philosophy-aspirational-mvp.md) — frozen-pre-reg amendment discipline preserved.
- [ADR-0013 permanent-exploration framework](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — §1-§7 immutability binding for the lift.
- ADR-0015 (concurrent landing) — referenced for cross-link continuity.
- [plan/h055_successor_tree_2026-05-06.md](../../plan/h055_successor_tree_2026-05-06.md) (concurrent landing) — H056 + H057 are the first applications of ADR-0016.
- [research/01_hypothesis_register/H055/design.md](../../research/01_hypothesis_register/H055/design.md) §12 — relationship to other hypotheses; H055 is the parent; H056 + H057 are the lift-bearing successors.
- [López de Prado 2018](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) *Advances in Financial Machine Learning*, Wiley, ISBN 978-1119482086, *practitioner* — Ch. 7 purged + embargoed walk-forward; §2.4.3 anchor invariant; §7.4.1 purging the training set.
- [Bergmeir & Benitez 2012](https://doi.org/10.1016/j.ins.2011.12.028) Information Sciences 191:192-213 — time-series CV protocol.
- [Tashman 2000](https://doi.org/10.1016/S0169-2070(00)00065-0) International Journal of Forecasting 16(4):437-450 — out-of-sample validation.
- [Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094) Journal of Portfolio Management 40(5):94-107 — deflated Sharpe ratio.
- [Harvey & Liu 2015](https://doi.org/10.3905/jpm.2015.42.1.013) Journal of Portfolio Management 42(1):13-28 — backtesting haircut.
- [Harvey, Liu & Zhu 2016](https://doi.org/10.1093/rfs/hhv059) Review of Financial Studies 29(1):5-68 — multiple-testing crisis.
- [arXiv 2511.00751](https://arxiv.org/abs/2511.00751) — multi-agent self-consistency 3-round cap.
- Sibling repos: [s-koirala/SKIE-Ninja](https://github.com/s-koirala/SKIE-Ninja) · [s-koirala/SKIE-NINJA-Volatility](https://github.com/s-koirala/SKIE-NINJA-Volatility) · [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) · [s-koirala/SKIENINJA-V3](https://github.com/s-koirala/SKIENINJA-V3).

## Follow-ups

- `P1-ADR-0016-SKIE-NINJA-VOLATILITY-AUDIT` **BLOCKING-BEFORE-H056-LIFT-OPTION-3-2** — full §2 audit on [s-koirala/SKIE-NINJA-Volatility](https://github.com/s-koirala/SKIE-NINJA-Volatility) at the H056 lift-event commit SHA; verify the claimed AUC 0.77-0.84 CPCV-validated metric under §2.4 multi-testing audit + §2.5 calibration audit; re-run under SKIE-Universe leak canaries per §2.2 if disposition (a) selected.
- `P1-ADR-0016-SKIE-NINJA-AUDIT` — full §2 audit on [s-koirala/SKIE-Ninja](https://github.com/s-koirala/SKIE-Ninja); the 500+ feature ML system requires substantial PIT review under §2.2 (every feature factory must pass leak canaries individually) + a feature-level audit-remediate-loop trail.
- `P1-ADR-0016-SKIE-NINJA-0DTE-AUDIT` — full §2 audit on [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE); per ADR-0006 the SKIE-ORB-CALL signal is the operationalization of the 0DTE track; substrate-compatibility under §2.1 will likely select disposition (c) since the sibling's substrate is QQQ + 0DTE/1DTE option chain, not the SKIE-Universe ES/NQ canonical substrate.
- `P1-ADR-0016-SKIENINJA-V3-AUDIT` — full §2 audit on [s-koirala/SKIENINJA-V3](https://github.com/s-koirala/SKIENINJA-V3); BTC range-expansion is out-of-universe relative to ADR-0001 (ES/NQ/MES/MNQ) — the substrate-compatibility check under §2.1 will reject disposition (a) and (b); only disposition (c) lift-as-feature is admissible, and only if the receiving successor's design.md §1 enumerates BTC as an exogenous regime feature ex ante.
- `P1-ADR-0016-LIFT-PROTOCOL-AUTOMATION-SCRIPT` — CLI tool at `scripts/sibling_lift_audit.py` that runs the §2 audit checklist on a `(sibling_repo_url, commit_sha, lift_disposition)` argument triple; emits `docs/audits/audit_trail_YYYY-MM-DD_sibling-lift-{repo-name}.md` skeleton + executes the §2.2 leak-canary harness against the sibling's reproduced training script + records §2.7 provenance fields into the receiving successor's `data_requirements.md`.
