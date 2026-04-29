# Audit trail — AI chart-reader hypothesis package (2026-04-27)

**Slug**: `chartreader-hypothesis-package`
**Date**: 2026-04-27
**Skill**: `audit-remediate-loop` (3-round cap per [arXiv 2511.00751](https://arxiv.org/abs/2511.00751))
**Mode**: parallel multi-auditor (`quant-auditor` + `literature-check` + `reproducibility-verifier`) per skill protocol §Auditor selection.

## Scope

Pre-registration package for the four-hypothesis Tier 2c "AI chart reader" cohort:

- [research/01_hypothesis_register/H057/](../../research/01_hypothesis_register/H057/) — 1D-CNN on causal OHLCV tensor with HMM regime gate.
- [research/01_hypothesis_register/H058/](../../research/01_hypothesis_register/H058/) — Time-series foundation model (TimesFM-2.5-200M + Chronos-Bolt-base-205M) with LoRA fine-tune and HMM regime gate.
- [research/01_hypothesis_register/H059/](../../research/01_hypothesis_register/H059/) — Open VLM (Qwen2.5-VL-3B-Instruct) LoRA fine-tuned on rendered candlestick chart with HMM regime gate.
- [research/01_hypothesis_register/H060/](../../research/01_hypothesis_register/H060/) — PatchTST trained from scratch on causal OHLCV with HMM regime gate.

Plus two memos:

- [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](../research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md) — landscape map + initial triage.
- [docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md](../research_notes/memo_chartreader-research-synthesis_2026-04-27.md) — synthesis tying survey + 4 design docs + cross-cutting bindings.

Plus documentation updates: [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md) (Tier 2c section), [CLAUDE.md](../../CLAUDE.md) (Phase 2 extension), [README.md](../../README.md) (Tier 2c paragraph), [CHANGELOG.md](../../CHANGELOG.md) (created at repo root).

## Workflow executed

1. **Survey agent (general-purpose)** — landscape map across 1D/2D CNN, time-series foundation models, transformer-only TS architectures, state-space models, open VLMs. Confirmed H057/H058/H059 as defensible covering set; recommended adding **H060 (PatchTST from scratch)** as train-from-scratch transformer baseline complement; rejected H057 (Mamba) and H058 (wavelet-CNN) as gold-plating.
2. **Lead-researcher binding decisions** on 5 survey open questions (Q1 SPA family budget, Q2 leakage figure verify, Q3 H059 render-config anchor, Q4 backlog tier, Q6 H059 compute budget).
3. **Four parallel targeted-research agents (general-purpose)** — one per hypothesis arm. Each produced `design.md`, `README.md`, `data_requirements.md` per the [research/01_hypothesis_register/_TEMPLATE.md](../../research/01_hypothesis_register/_TEMPLATE.md) 11-section schema.
4. **Synthesis memo composed** by main thread tying the survey, four design docs, cross-cutting bindings, follow-up taxonomy.
5. **Round-1 audit** — parallel `quant-auditor` + `literature-check` + `reproducibility-verifier`.
6. **Round-1 remediation** — synthesis memo + survey memo edits by main thread; H057+H060 + H058+H059 design docs delegated to two parallel remediation agents.
7. **Round-2 audit** — parallel three-auditor verification of Round-1 remediations + new-issue surfacing.
8. **Round-2 remediation** — synthesis memo edits by main thread; companion artefact sweeps (READMEs, data_requirements, citation residuals, sidecar JSON, multi-sidecar uniformity, LoRA citation pin fixes) delegated to a single remediation agent.
9. **Round-3 audit (final per 3-round cap)** — focused verification pass; verdict `clear`.
10. **Documentation update phase** — hypothesis backlog Tier 2c section; CLAUDE.md Phase 2 extension; README.md Tier 2c paragraph; CHANGELOG.md created.
11. **Documentation-update audit (single round)** — combined audit pass.

## Round-1 findings (36 total: 9 critical, 21 major, 6 minor)

### `quant-auditor` (15 findings: 3 critical, 12 major)

| ID | Severity | Location | Issue summary | Disposition |
|---|---|---|---|---|
| Q-R1-1 | critical | H050/design.md vs H057/H058/H059/H060 design.md §1 | SPA family test-statistic incommensurability — H050 within-arm `gated − unconditional` cannot share family with chart-reader cross-arm `arm_gated − H050_gated` | **Resolved Round 1**: split into Family A (H050 alone, M=1, Romano-Wolf) + Family B (chart-reader cohort, M=5, Hansen SPA) with H050 as baseline anchor only. Synthesis memo §6 binding. |
| Q-R1-2 | critical | H059/design.md §3.3, §5.5, §6 | H059 trigger cadence (HMM-state-transition) breaks paired LW2008 alignment with Family B per-bar cohort | **Resolved Round 1**: H059 rebound to per-bar inference cadence; pilot fold-0 wall-clock as binary disposition gate; H059b registered as conditional successor at HMM-state-transition cadence. |
| Q-R1-3 | critical | H058/design.md §3.2, §5.2, §5.4 | Multiple magic numbers: N_draws=200, context_length=512 (un-cited √2 factor), Phase-1 epochs=1, patience=1 | **Resolved Round 1**: N_draws re-derived to 79 from discrete-grid coverage `(26/27)^N ≤ 0.05`; √2 factor removed; patience raised to ≥2 with citation; `P1-H058-CONTEXT-LENGTH-EMPIRICAL` + `P1-H058-FINETUNE-PROTOCOL-EMPIRICAL` follow-ups added. |
| Q-R1-4 | major | H059/design.md §5.2 | LoRA hyperparameters (rank=16, α=32, target_modules, dropout=0.05, LR=1e-4, epochs=3) cite tasks unrelated to intraday futures | **Resolved Round 1 + 2**: per-value primary citation anchors + selection-bias note; Round-2 re-pinned §3.4 → §4.1 (correct LoRA paper section); §7.1 framing toned down (no false "Pareto-optimal vs full-MLP" claim); lora_dropout=0.05 reframed as project convention (PEFT default is 0.0); `P1-H059-LORA-CONFIG-EMPIRICAL` follow-up. |
| Q-R1-5 | major | H057/design.md §5.1 | Training-side hyperparameters lack empirical justification | **Resolved Round 1**: anchored to cited primary references with selection-bias note + `P1-H057-TRAINING-SCALARS-EMPIRICAL` follow-up. |
| Q-R1-6 | major | H060/design.md §4.4 | PatchTST `lr=1e-4` "methodology choice not hyperparameter" loophole | **Resolved Round 1**: `P1-H060-LR-DEFAULT-LITERATURE-CHECK` referenced as `status=running` blocker pending literature-check resolution; same treatment for batch_size, epochs, patience, dropout, grad_clip; `P1-H060-TRAINING-SCALARS-EMPIRICAL` follow-up. |
| Q-R1-7 | major | H057 vs H058/H059/H060 §HMM gate | HMM `covariance_type` inconsistent across arms (`{diag, full}` runtime dedup vs `[diag]` only) | **Resolved Round 1 + 2**: ALL chart-reader arms use `{diag, full}` with runtime dedup per `select_gaussian_hmm` model-class deduplication, matching H050 closure semantics. Round-2 caught regression in H060 README (still `[diag]`); fixed. |
| Q-R1-8 | major | H050/design.md §9 inheritance | Power calculation transferability error — H050's `n_required_for_power_80` scalar not transferable to new arms | **Resolved Round 1**: per-arm `n_required_for_power_80` from per-arm pilot dispersion; cohort fold count = `max(n_required_per_arm)`; `P1-CHARTREADER-PER-ARM-POWER-CALC` follow-up. |
| Q-R1-9 | major | H058/design.md §10 | Max-over-backbone double-counting in disposition rule | **Resolved Round 1**: per-backbone `passed=True` requires both per-backbone LW2008 CI excluding zero AND that backbone's specific Family-B SPA column passing; `P1-H058-INTERNAL-BONFERRONI` follow-up. |
| Q-R1-10 | major | H058/design.md §3 | Features list conflates classifier inputs and HMM gate inputs | **Resolved Round 1**: §3 restructured into §3.1 (HMM gate inputs, H050-shared) and §3.2 (TSFM classifier inputs only). |
| Q-R1-11 | major | H059/design.md §1 | H0_uncond auxiliary null incoherent under HMM-transition cadence | **Resolved Round 1**: H059 cadence flip to per-bar made the auxiliary null coherent OR dropped if redundant with Family A. |
| Q-R1-12 | major | H050/design.md §1 vs synthesis memo §6 | H050 binding pre-reg = Romano-Wolf, but original synthesis memo declared Hansen SPA family | **Resolved Round 1**: Family A / Family B split preserves H050's frozen pre-reg without successor ID; `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` follow-up tracks the H050.yaml ↔ design.md inconsistency. |
| Q-R1-13 | major | H059/design.md §3.6 | PIT canary 1 mis-specified (cross-fold pixel-identity test trivially fails or trivially passes) | **Resolved Round 1**: re-spec as cross-fold structural-difference canary (primary) + deterministic-renderer canary (secondary). |
| Q-R1-14 | major | H060/design.md §3.2 | PatchTST double-normalization (per-fold z-score + instance norm) | **Resolved Round 1**: bound to Option (a) — drop per-fold z-score for OHLC channels; retain log1p+z-score for volume; (b)/(c) explicitly rejected. |
| Q-R1-15 | major | H059/design.md §4 | Inner-CV log-loss metric ambiguous given constrained-decoding | **Resolved Round 1**: specified as restricted-3-token log-loss at decode time after constrained-decoding mask, with temperature-scaled softmax per [Guo et al. 2017, arxiv 1706.04599](https://arxiv.org/abs/1706.04599). |

### `literature-check` (6 findings: 3 critical, 3 minor)

| ID | Severity | Location | Issue summary | Disposition |
|---|---|---|---|---|
| L-R1-1 | critical | survey + synthesis + 4 design packages (multiple files) | Aksu et al. 2025 misattribution — actual authors are Meyer, Kaltenpoth, Zalipski, Müller 2025 for [arxiv 2510.13654](https://arxiv.org/abs/2510.13654) | **Resolved Round 1 + 2**: global replace executed; Round-2 caught 4 missed occurrences (H057/design.md:35, H058/README.md:11, H058/data_requirements.md:131, H060/design.md:36); fixed. Closure verified by Round-3 grep returning zero hits. |
| L-R1-2 | critical | survey memo + synthesis + H058 §8.3 | Fabricated "47%–184% MSE inflation" figure — does not appear in [arxiv 2510.13654](https://arxiv.org/abs/2510.13654) primary source | **Resolved Round 1 + 2**: figure retracted globally; verbatim abstract sentence retained as the load-bearing reference; Round-2 dropped specific Madrid/COVID magnitudes pending HTML-body verification under `P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY-MAGNITUDE` follow-up. |
| L-R1-3 | critical→minor | H059 + survey + synthesis | Hu et al. 2026 author expansion to "Hu, Xiao, Xu, Tang, Liu 2026" for [arxiv 2604.12659](https://arxiv.org/abs/2604.12659) | **Verified-existing Round 1**: WebFetch confirmed paper exists with verbatim quote match; **Resolved Round 1 + 2**: full author list propagated globally; Round-2 caught 3 missed survey-memo occurrences (lines 166, 269, 284) and 1 H059 README occurrence; fixed. |
| L-R1-4 | minor | survey memo (multiple) | Venue-verification gaps for ICLR/ICML papers | Dropped per protocol. |
| L-R1-5 | minor | H060/design.md §5 | Lopez de Prado AFML DOI re-use | Dropped per protocol. |
| L-R1-6 | minor | survey memo §2.2 | Timer arxiv 2402.02368 self-flagged as unverified | Dropped per protocol. |

### `reproducibility-verifier` (15 findings: 3 critical, 7 major, 5 minor)

| ID | Severity | Location | Issue summary | Disposition |
|---|---|---|---|---|
| R-R1-1 | critical | H058/design.md:144 | Broken ADR-0007 link `stacked-embargo.md` → actual file `embargo-placement.md` | **Resolved Round 1**: link corrected. |
| R-R1-2 | critical | H060/design.md §11 | model_hash composition omits warm-cold sidecar SHA256 | **Resolved Round 1**: warm-cold sidecar field added; invariant 6 updated. |
| R-R1-3 | critical | H058/design.md §11 | Multi-sidecar composition unspecified for two backbone sidecars + HMM | **Resolved Round 1 + 2**: interim deterministic composition rule added; Round-2 amended to per-arm pre-aggregation rule (synthesis memo §5) so canonical outer 4-tuple is invariant across all four arms while accommodating arm-specific sidecar count. |
| R-R1-4 | major | H057/design.md §4 | Broken link `src/skie_ninja/features/labels/` → actual file `labels.py` | **Resolved Round 1**: link corrected. |
| R-R1-5 | major | H060/design.md §11 | Missing `P1-MODEL-HASH-MULTI-SIDECAR-HELPER` reference | **Resolved Round 1**: reference added. |
| R-R1-6 | major | H058/design.md §11 | Sidecar list omits warm-cold filter diagnostic sidecar | **Resolved Round 1**: warm-cold sidecar path + SHA256 inclusion added. |
| R-R1-7 | major | H060/design.md §4.4 | Missing `P1-H060-LR-DEFAULT-LITERATURE-CHECK` reference | **Resolved Round 1**: reference added as `status=running` blocker. |
| R-R1-8 | major | H059/data_requirements.md:136 | Wall-clock follow-up name drift `P1-H059-WALL-CLOCK-PILOT` → canonical `P1-H059-WALL-CLOCK-PILOT-MEASUREMENT` | **Resolved Round 1**: name corrected. |
| R-R1-9 | major | H059/design.md | Missing `P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE` reference | **Resolved Round 1**: reference added; now active given the cadence flip. |
| R-R1-10 | major | H058/design.md §8.3 | Missing `P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY` reference | **Resolved Round 1**: reference added (now closed per L-R1-2). |
| R-R1-11 | minor | H059/design.md | Section-numbering offset (§12 vs §11) | Dropped per protocol. |
| R-R1-12 | minor | H059/design.md §12 | Missing BLAS env-var enumeration (refs ADR-0009 only) | Dropped per protocol. |
| R-R1-13 | minor→major | H057/design.md §11 | Missing PyTorch thread pin (`torch.set_num_threads(1)`, `torch.set_num_interop_threads(1)`) | **Upgraded to major and resolved Round 1**: PyTorch thread pin added matching H060 + ADR-0009 precedent. |
| R-R1-14 | minor | H058/design.md §11 | Sidecar schema asymmetry between TimesFM and Chronos | Dropped per protocol. |
| R-R1-15 | minor | H060/data_requirements.md:113 | Fold-suffixed sidecar naming diverges from ADR-0005 convention | Dropped per protocol. |

## Round-2 findings (22 total: 11 critical, 8 major, 3 minor)

Round-2 surfaced primarily companion-artefact regressions where READMEs and data_requirements.md were not updated alongside design.md, plus new majors introduced by Round-1 remediations (LoRA citation pins, multi-sidecar uniformity).

### `quant-auditor` (9 findings: 5 critical, 3 major, 1 minor)

| ID | Severity | Location | Issue summary | Disposition |
|---|---|---|---|---|
| Q-R2-1 | critical | H059/README.md:17 | Cadence binding regression — README still claims HMM-state-transition cadence is binding | **Resolved Round 2**: README rewritten to per-bar binding matching design.md. |
| Q-R2-2 | critical | H059/design.md §12.1 sidecar JSON | Sidecar JSON template still hardcodes `rule: hmm_state_transition_only` | **Resolved Round 2**: trigger_cadence block updated to `rule: per_bar`. |
| Q-R2-3 | critical | H060/README.md:19 | Family A/B split regression — H050 placed inside chart-reader SPA family | **Resolved Round 2**: README updated to Family B `{H057, H058a, H058b, H059, H060}` M=5 with H050 as baseline anchor only. |
| Q-R2-4 | critical | H058/README.md:13 | Family A/B split regression — README states M=6 including H050 | **Resolved Round 2**: README updated to Family B M=5. |
| Q-R2-5 | critical | H057/README.md:11 | Family A/B split regression | **Resolved Round 2**: README updated to Family B. |
| Q-R2-6 | major | H060/README.md:17 | HMM cov_type cross-arm consistency regression — README says `[diag]` only | **Resolved Round 2**: README updated to `{diag, full}` with runtime dedup. |
| Q-R2-7 | major | H057/H058/H060 design.md (Aksu sweep gaps) | Cross-doc citation regression on Aksu→Meyer | **Resolved Round 2**: 4 missed occurrences swept. |
| Q-R2-8 | major | H060/data_requirements.md:91-97 | Q-R1-14 normalization fix not propagated — table still specifies per-fold z-score for OHLC | **Resolved Round 2**: 4 OHLC rows updated to `no per-fold z-score`. |
| Q-R2-9 | major | H059/design.md:290-291 | Internal inconsistency in §10 stopping rule — soft-truncation `min(...)` breaks Family B paired-differential pairing | **Resolved Round 2**: dropped soft-truncation; binary disposition gate. |

### `literature-check` (5 findings: 1 critical, 2 major, 2 minor)

| ID | Severity | Location | Issue summary | Disposition |
|---|---|---|---|---|
| L-R2-1 | critical | H057/H058/H060 (4 files) | Aksu→Meyer regression (incomplete Round-1 sweep) | **Resolved Round 2**: 4 occurrences swept. |
| L-R2-2 | major | synthesis + H058 §8.3 | Madrid/COVID specific MAE numerals not pinnable from abstract | **Resolved Round 2**: specific magnitudes dropped; verified abstract sentence retained; HTML-body verification deferred to `P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY-MAGNITUDE`. |
| L-R2-3 | major | H059/design.md §5.2 | Hu et al. 2022 §3.4 misattribution (paper has no §3.4; α/r scaling is in §4.1; α/r=2 is not a Hu et al. default) | **Resolved Round 2**: re-pinned to §4.1; α/r=2 reframed as project convention. |
| L-R2-4 | minor | H059/design.md §5.2 | §7.1 "Pareto-optimal vs full-MLP" framing not supported by paper (Hu et al. did not study MLP LoRA) | **Resolved Round 2**: framing toned down to "attention-only Wq+Wv jointly superior to single-matrix per Hu et al. §7.1." |
| L-R2-5 | minor | H059/design.md §5.2 | `lora_dropout=0.05` not actually PEFT default (default is 0.0) | **Resolved Round 2**: reframed as project convention. |

### `reproducibility-verifier` (8 findings: 5 critical, 3 major)

| ID | Severity | Location | Issue summary | Disposition |
|---|---|---|---|---|
| R-R2-1 | critical | H059/design.md sidecar JSON | trigger_cadence regression (duplicate of Q-R2-2) | **Resolved Round 2** with Q-R2-2. |
| R-R2-2 | critical | H059/README.md | Cadence README regression (duplicate of Q-R2-1) | **Resolved Round 2** with Q-R2-1. |
| R-R2-3 | critical | H060/README.md | Cov_type README regression (duplicate of Q-R2-6) | **Resolved Round 2** with Q-R2-6. |
| R-R2-4 | critical | H057/H058/H060 README | Family B README regressions (duplicates of Q-R2-3/4/5) | **Resolved Round 2** with Q-R2-3/4/5. |
| R-R2-5 | critical | H058 + H059 design.md multi-sidecar tuple | Tuple length divergence (4 vs 5 vs 6) breaks Round-2 byte-equivalent uniformity check | **Resolved Round 2**: amended to per-arm pre-aggregation; canonical outer 4-tuple invariant; arm-specific inner pre-aggregation documented in each design doc §11/§12. Synthesis memo §5 amended. |
| R-R2-6 | major | H058/data_requirements + H058/README + survey + H059/README | Closed citation-fix follow-ups regressed in companion artefacts | **Resolved Round 2**: all occurrences swept; closure record verified. |
| R-R2-7 | major | synthesis memo §8 line 132 + §9 line 144 | Internal contradiction "M=6" vs §6 "M=5" | **Resolved Round 2**: both occurrences corrected to "M=5". |
| R-R2-8 | major | H058/design.md §11 | Missing follow-up references block (asymmetric vs H057/H060) | **Resolved Round 2**: §11.3 follow-up references block appended enumerating 9 H058-relevant follow-ups. |

## Round-3 findings (1 minor; verdict `clear`)

| ID | Severity | Location | Issue summary | Disposition |
|---|---|---|---|---|
| L-R3-1 | minor | synthesis memo §3 Q2 row | Stale "Aksu-style" phrasing inside the L-R1-1 closure-context row | **Resolved Round 3**: replaced with "Meyer et al. 2025". |

**Round-3 exit decision: `clear`**. All Round-1 and Round-2 critical/major findings verified resolved. The package is audit-clean for `status=designed → status=running` transition per the documented gating follow-ups.

## Documentation-update audit (single round; 1 critical, 1 major)

| ID | Severity | Location | Issue summary | Disposition |
|---|---|---|---|---|
| D-1 | critical | CHANGELOG / CLAUDE / README / hypothesis_backlog | Audit trail file referenced by all four documentation files did not exist | **Resolved**: this file is the resolution. |
| D-2 | major | CHANGELOG.md:37 | Claim that `P1-HMM-FULL-COV-1DIM-REDUNDANT` is closed via commit on a sibling branch not in this lineage | **Resolved**: CHANGELOG entry reworded to "closure patch ... under preparation on a sibling branch — not yet merged into this lineage" matching CLAUDE.md and H057/design.md framing. |

## Outstanding follow-ups (gating `status=running`)

Per the synthesis memo §5 follow-up taxonomy, before any chart-reader arm transitions from `designed` to `running`:

- **`P1-MODEL-HASH-MULTI-SIDECAR-HELPER`** — multi-sidecar `model_hash` helper landing; interim per-arm pre-aggregation rule pinned in synthesis memo §5 holds until then.
- **`P1-CHARTREADER-PER-ARM-POWER-CALC`** — per-arm `n_required_for_power_80` from per-arm pilot dispersion; cohort fold count = `max(n_required_per_arm)`.
- **`P1-H058-TIMESFM-GIFTEVAL-INSPECTION`** — TimesFM-2.5 GiftEvalPretrain component-level inspection for ES/NQ contamination.
- **`P1-H058-CHRONOS-APPENDIX-INSPECTION`** — Chronos-Bolt pretraining-corpus appendix scan for ES/NQ contamination.
- **`P1-H059-WALL-CLOCK-PILOT-MEASUREMENT`** — H059 fold-0 per-bar wall-clock empirical gate; >7 days/fold triggers `archive(null, infeasible)`.
- **`P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`** — successor H059b at HMM-state-transition cadence registered if H059 archives null on wall-clock alone.
- **`P1-H060-LR-DEFAULT-LITERATURE-CHECK`** — PatchTST `lr=1e-4` ETT-default transferability to 1-min equity-index futures.
- **`P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE`** — Family A reconciliation between H050 design.md (Romano-Wolf) and H050.yaml + scripts/run_walk_forward.py (Hansen SPA); independent of Family B but binding before any Family-A-aggregate inference.

Plus deferred (non-blocking) follow-ups: `P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY-MAGNITUDE`, `P1-H058-CONTEXT-LENGTH-EMPIRICAL`, `P1-H058-FINETUNE-PROTOCOL-EMPIRICAL`, `P1-H058-INTERNAL-BONFERRONI`, `P1-H058-COMPUTE-BUDGET-PRE-REG`, `P1-H058-INFERENCE-COMPUTE-BUDGET`, `P1-H057-TRAINING-SCALARS-EMPIRICAL`, `P1-H060-TRAINING-SCALARS-EMPIRICAL`, `P1-H059-LORA-CONFIG-EMPIRICAL`.

## Residual risk

The cohort design rests on a clean two-family SPA split; H050's frozen pre-reg is preserved without successor ID. Open weights everywhere; hosted black-box VLMs disqualified from inference paths. The largest residual exposure is H059's per-bar wall-clock feasibility — if the fold-0 pilot exceeds the 7-day-per-fold ceiling, H059 archives `null, infeasible` and the H059b successor is registered, leaving the chart-reader cohort at M=4 effective entries. The H058 contamination-screen follow-ups may exclude either backbone if the GiftEvalPretrain or Chronos appendix inspection reveals direct ES/NQ overlap. None of these residuals invalidate the pre-registration package; they are operational gates for `status=running`.

## Reproducibility

- **git HEAD at audit close**: TBD at commit (audit trail composed before final commit on this branch).
- **Branch**: `claude/ecstatic-hellman-937c44`.
- **Worktree**: `C:\Users\skoir\Documents\SKIE-Universe\.claude\worktrees\ecstatic-hellman-937c44`.
- **Auditor agents**: `quant-auditor`, `literature-check`, `reproducibility-verifier` (all per [~/.claude/agents/](~/.claude/agents/) project-defined subagent types) plus `general-purpose` for survey, targeted-research, and remediation work.
- **Skill**: [audit-remediate-loop](~/.claude/skills/audit-remediate-loop/SKILL.md).
- **Models used**: Claude Opus 4.7 (lead session) + sonnet/opus subagents per default routing.
- **AI-assistance disclosure**: per project user-global rules, AI-assistance statement is in the project README and in [docs/research_notes/memo_chartreader-research-synthesis_2026-04-27.md](../research_notes/memo_chartreader-research-synthesis_2026-04-27.md) provenance metadata.
