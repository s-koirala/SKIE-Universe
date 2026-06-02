---
name: AI chart-reader hypothesis package — synthesis memo (H057 / H058 / H059 / H060)
description: Synthesis of the survey + four targeted-research design docs; lead-researcher open-question bindings; new follow-ups; SPA-family declaration
type: project
created: 2026-04-27
---

# AI chart-reader hypothesis package — synthesis

This memo composes the survey memo and the four targeted-research design packages into a single research deliverable for audit-remediate. It does **not** replace any of the source artifacts; it ties them together and records the lead-researcher bindings and downstream follow-ups.

## 1. Provenance

- **Survey memo**: [docs/research_notes/memo_chartreader-hypothesis-survey_2026-04-27.md](memo_chartreader-hypothesis-survey_2026-04-27.md). Mapped landscape across 1D / 2D CNN, TS foundation models, transformer-only TS architectures, state-space models, open VLMs. Confirmed H057 / H058 / H059 as defensible covering set; recommended **adding H060 (PatchTST trained from scratch)** to fill the train-from-scratch transformer baseline gap with zero pretraining contamination. Explicitly rejected H057 (Mamba) and H058 (wavelet-CNN) as gold-plating.
- **H057 design package** — [research/01_hypothesis_register/H057/](../../research/01_hypothesis_register/H057/) ([design.md](../../research/01_hypothesis_register/H057/design.md), [README.md](../../research/01_hypothesis_register/H057/README.md), [data_requirements.md](../../research/01_hypothesis_register/H057/data_requirements.md)).
- **H058 design package** — [research/01_hypothesis_register/H058/](../../research/01_hypothesis_register/H058/).
- **H059 design package** — [research/01_hypothesis_register/H059/](../../research/01_hypothesis_register/H059/).
- **H060 design package** — [research/01_hypothesis_register/H060/](../../research/01_hypothesis_register/H060/).

## 2. Deviation from original scope (3 → 4 hypotheses)

The lead-researcher's original framing in this session proposed three hypothesis arms (H057 / H058 / H059). The survey agent recommended adding **H060 — PatchTST from scratch** to factor the design space cleanly into:
- **Train-from-scratch CNN** (H057): convolution inductive prior, no contamination.
- **Train-from-scratch transformer** (H060): attention inductive prior, no contamination.
- **Foundation-pretrained TS model** (H058): cross-domain transfer prior, contamination-screened.
- **Foundation-pretrained VLM** (H059): visual representation prior, contamination acknowledged.

The lead accepted this addition. The four arms enter as a single tight covering set; resist further additions.

## 3. Lead-researcher bindings on the survey's open questions

Recorded here so each design doc can be cross-checked against a single source. **Updated 2026-04-27 (Round-1 audit remediation): Q1 + Q6 amended.**

| # | Question (survey §10) | Binding |
|---|---|---|
| Q1 | SPA family budget across the four arms | **Two separate families** (Q-R1-1 + Q-R1-12 remediation — see §6). Family A = H050's frozen Romano-Wolf step-down regime-lift family. Family B = the chart-reader model-class-lift family (H057 + H058a + H058b + H059 + H060 = M=5) with H050 as **baseline anchor only**, not a Family B member. Mixing the within-arm `gated − unconditional` (Family A) statistic with the cross-arm `arm_gated − H050_gated` (Family B) statistic in a single Hansen SPA composite null is incommensurable; the split preserves H050's frozen pre-reg without a successor-ID violation. |
| Q2 | Verify the 47–184% leakage figure from [arxiv 2510.13654](https://arxiv.org/abs/2510.13654) | **Closed (verified-as-fabricated) by Round-1 literature-check (L-R1-2).** The 47–184% figure does not appear in the primary source; verified figures are ~43% (Madrid transport temporal leakage) and ~37% (COVID stock-market regime). All artifacts retract the fabricated figure; H058 §8.3 retains the qualitative Meyer et al. 2025 claim with verified verbatim quote only. |
| Q3 | Render-config anchor for H059 (Hu et al. 2026 vs project default) | H059 agent verified Hu et al. 2026 config and **rejected it** (cutoff-date header + body-color-encoding-of-target + MA90 outside window are PIT side channels); adopted the project default render config. Documented in H059 §3. |
| Q4 | Backlog tier for new hypotheses | New **Tier 2c — AI chart reader** section in [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md). |
| Q6 | H059 inference cadence | **Bind to per-bar inference** (Q-R1-2 remediation — cohort-commensurable LW2008 paired-bar pairing and Hansen 2005 shared-bootstrap-index dependence preservation both require uniform cadence across Family B entries). Fold-0 pilot wall-clock measurement is the empirical gate: if measured wall-clock > 7 days/fold on Qwen2.5-VL-3B + LoRA, H059 archives `null, infeasible` and a successor `H059b` at HMM-state-transition cadence is registered as a separate-family hypothesis (out of scope for the 2026-04-27 chart-reader pre-reg package). |
| Q1' | Citation fixes (Round-1 literature-check) | **Aksu et al. 2025 → Meyer, Kaltenpoth, Zalipski, Müller 2025** for [arxiv 2510.13654](https://arxiv.org/abs/2510.13654) (L-R1-1; actual authors per WebFetch 2026-04-27). **Hu et al. 2026 → Hu, Xiao, Xu, Tang, Liu 2026** for [arxiv 2604.12659](https://arxiv.org/abs/2604.12659) (L-R1-3; full author list, existence verified). |

## 4. Cross-arm comparison

Updated 2026-04-27 post-Round-1 audit remediation (Q-R1-2 cadence binding; Q-R1-7 cov_type uniform; Q-R1-3/4/5/6 magic-number anchoring).

| Property | H057 (1D-CNN) | H058 (TimesFM + Chronos) | H059 (Qwen2.5-VL-3B) | H060 (PatchTST) |
|---|---|---|---|---|
| Inductive prior | Convolution | Cross-domain TS pretraining | 2D visual + LLM | Attention (channel-independent) |
| Pretraining contamination | None (from scratch) | Medium-High; per-backbone screened (`P1-H058-TIMESFM-GIFTEVAL-INSPECTION`, `P1-H058-CHRONOS-APPENDIX-INSPECTION` block `running`) | Visual-prior bias toward TA folklore | None (from scratch) |
| Output | 3-class softmax over triple-barrier | 3-class softmax over triple-barrier | 3-class softmax over triple-barrier (constrained-decoded) | 3-class softmax over triple-barrier |
| HMM gate | Identical to H050 | Identical to H050 | Identical to H050 | Identical to H050 |
| HMM `covariance_type` | `{diag, full}` with runtime dedup per `select_gaussian_hmm` | `{diag, full}` with runtime dedup | `{diag, full}` with runtime dedup | `{diag, full}` with runtime dedup |
| Architecture grid | 30 RF-admissible cells from 162 raw | LoRA rank/α/LR sweep (2 backbones); `N_draws` re-derived per discrete-grid coverage | Single config (no sweep); LoRA hyperparameters anchored with explicit per-value citation | 16 cells + N_draws=47 |
| Differential CI | LW2008 paired vs H050 LGB-gated | LW2008 paired vs H050 LGB-gated | LW2008 paired vs H050 LGB-gated | LW2008 paired vs H050 LGB-gated |
| SPA family (Family B) entries | 1 | 2 | 1 | 1 |
| Inference cadence | Per-bar | Per-bar | **Per-bar** (was HMM-transition; rebound 2026-04-27 per Q-R1-2; pilot is the gate, H059b successor if infeasible) | Per-bar |
| Per-arm power calc | Per-arm `T_arm` dispersion → `n_required_for_power_80`; cohort fold count = `max` (Q-R1-8) | Per-arm `T_H058_b` dispersion (already per-arm) | Per-arm `T_H059` dispersion | Per-arm `T_H060` dispersion |
| Compute pre-reg | Standard fold budget | ≤ 168 GPU-hours per backbone | Re-estimated at per-bar; pilot gate | Standard fold budget |

## 5. New follow-ups surfaced by the targeted agents and the Round-1 audit

Add to the project follow-up backlog. None block the hypothesis-package audit-remediate-loop; several block downstream `status=running` transition.

- **`P1-MODEL-HASH-MULTI-SIDECAR-HELPER`** — already-open follow-up, now blocking H057 + H058 + H059 + H060 transition to `running`. Multi-sidecar SHA256 composition (CNN/TSFM/VLM/PatchTST sidecar + HMM sidecar + warm-cold sidecar + ledger roll-up) into single `ReproLog.model_hash`. **Interim deterministic rule** pinned by Round-1 audit (R-R1-2, R-R1-3) and amended by Round-2 audit (R-R2-5) to permit arm-specific pre-aggregation: each arm computes `arm_sidecar_sha256 := sha256(sorted_tuple([sidecar_a_sha256, sidecar_b_sha256, ...]))` from its own arm-specific sidecar set first (e.g., H058's two backbone sidecars, H059's qwenvl + render-config + prompts sidecars), then the outer composition is the canonical 4-tuple `model_hash = sha256(sorted_tuple([arm_sidecar_sha256, hmm_sidecar_sha256, warm_cold_sidecar_sha256, ledger_rollup_sha256]))`. The outer 4-tuple is invariant across all four chart-reader arms; the inner pre-aggregation is arm-specific and documented in each design doc §11. This preserves byte-equivalence at the outer composition while accommodating arm-specific sidecar count.
- **`P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE`** (Q-R1-12 remediation, blocking Family-A-aggregate inference) — H050 design.md §1 specifies Romano-Wolf step-down; H050.yaml + scripts/run_walk_forward.py specify Hansen SPA. Resolve before any Family-A-aggregate inference is reported. Family B (chart-reader cohort) is independent of this resolution because Family B uses its own Hansen 2005 SPA per ADR-0008 with H050 as baseline anchor only.
- **`P1-H058-TIMESFM-GIFTEVAL-INSPECTION`** (blocking H058 `running`) — TimesFM-2.5 pretraining inherits Salesforce GiftEvalPretrain, whose LOTSA parent contains an "economics" domain. Per-series inspection required to confirm zero ES/NQ overlap.
- **`P1-H058-CHRONOS-APPENDIX-INSPECTION`** (blocking H058 `running`) — Chronos-Bolt pretraining dataset list lives in the [Ansari et al. 2024](https://arxiv.org/abs/2403.07815) appendix; full-text fetch required for the contamination screen.
- **`P1-H059-WALL-CLOCK-PILOT-MEASUREMENT`** (gating H059 `running`; canonical name per R-R1-8) — A100-80GB wall-clock estimate at per-bar cadence is order-of-magnitude from public benchmark posts; fold-0 pilot is the binding empirical measurement. >7 days/fold → `archive(null, infeasible)` and register H059b successor.
- **`P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY`** — **Closed 2026-04-27 (verified-as-fabricated)** by Round-1 literature-check (L-R1-2). The "47–184% MSE inflation" figure does not appear in the primary source; verified figures are ~43% (Madrid transport temporal leakage) and ~37% (COVID stock-market regime). All artifacts retract the fabricated figure.
- **`P1-H060-LR-DEFAULT-LITERATURE-CHECK`** — PatchTST `lr=1e-4` anchored to canonical [yuqinie98/PatchTST](https://github.com/yuqinie98/PatchTST) ETT-benchmark default. Round-1 audit (Q-R1-6) flags transferability to 1-min equity-index futures as unproven; H060 design doc references the follow-up as a `status=running` blocker pending literature-check resolution.
- **`P1-H059-PERBAR-SUCCESSOR-IF-INFEASIBLE`** (conditional) — if H059 archives null on per-bar-cadence wall-clock alone, register a successor H059b at HMM-state-transition cadence on a larger compute substrate.
- **`P1-CHARTREADER-PER-ARM-POWER-CALC`** (Q-R1-8 remediation, blocking `running`) — each chart-reader arm computes `n_required_for_power_80` from the dispersion of its OWN paired-differential test statistic on a pilot training-fold sample; cohort fold count = `max(n_required_per_arm)` to preserve paired-differential pairing across the M=5 family. The H050 scalar is no longer transferable.
- **`P1-H058-INTERNAL-BONFERRONI`** (Q-R1-9 remediation) — H058 max-over-backbone disposition rule conditioned on per-backbone SPA passing for that backbone's column (the per-backbone LW2008 CI alone is unadjusted; the M=5 cohort SPA absorbs the multiple-comparison correction).
- **`P1-CITATION-FIX-AKSU-MEYER`** (L-R1-1) — **closed 2026-04-27**. All occurrences of "Aksu et al. 2025" / "Aksu, Yang et al. 2025" replaced with "Meyer, Kaltenpoth, Zalipski, Müller 2025" across survey memo, synthesis memo, and 4 design packages.
- **`P1-CITATION-FIX-HU-AUTHOR-EXPANSION`** (L-R1-3) — **closed 2026-04-27**. "Hu et al. 2026" expanded to "Hu, Xiao, Xu, Tang, Liu 2026" across H059 + survey + synthesis. Existence verified via WebFetch 2026-04-27 with verbatim abstract quote match.

## 6. Hansen SPA family declarations (post-hypothesis-package, post-Round-1 remediation)

**Two separate families** per Round-1 quant-auditor finding Q-R1-1 (test-statistic incommensurability) and Q-R1-12 (H050 frozen-pre-reg conflict). The split preserves H050's frozen pre-reg without successor-ID violation and makes both families internally commensurable on a single shared composite null.

### Family A — Regime-lift (H050 binding pre-reg)

Per [H050/design.md §1](../../research/01_hypothesis_register/H050/design.md), H050 is pre-registered with `T_H050 = SR_gated − SR_unconditional` (within-arm regime-lift differential) entering the Romano-Wolf step-down family per [ADR-0003](../decisions/ADR-0003-spa-vs-romanowolf.md). H050 enters Family A as a single-strategy `M = 1` degenerate per [ADR-0008](../decisions/ADR-0008-spa-omega-method.md) §Single-strategy degenerate handling until additional regime-lift hypotheses join. The pre-existing inconsistency between H050/design.md (Romano-Wolf) and H050.yaml + [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) (Hansen SPA) is tracked under `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` and binds resolution before any Family-A-aggregate inference is reported.

```
SPA_family_A = {
  H050  (HMM regime-conditioned LGB; T_H050 = SR_gated − SR_unconditional)
}
M = 1
omega_method = hac (per ADR-0008 single-strategy degenerate handling)
```

### Family B — Model-class lift (chart-reader cohort, declared 2026-04-27)

The four chart-reader arms enter a separate Hansen 2005 SPA family with H050 as **baseline anchor only** (not itself a Family B entry). Test statistic for each arm: `T_arm = SR_arm_gated − SR_H050_gated` (cross-arm model-class differential), bar-aligned at per-bar cadence (Q-R1-2 remediation: H059 rebound from HMM-transition cadence to per-bar to preserve cohort commensurability).

```
SPA_family_B_2026-04-27 = {
  H057  (HMM regime-conditioned, 1D-CNN classifier),
  H058a (HMM regime-conditioned, TimesFM-2.5 + LoRA),
  H058b (HMM regime-conditioned, Chronos-Bolt-base + LoRA),
  H059  (HMM regime-conditioned, Qwen2.5-VL-3B + LoRA on rendered chart, per-bar cadence),
  H060  (HMM regime-conditioned, PatchTST from scratch)
}
M = 5
omega_method = bootstrap (per ADR-0008 two-tier rule: M ≥ 2 ⇒ bootstrap)
shared_bootstrap_indices = true (per Hansen 2005 §3 cross-strategy dependence preservation)
```

Family B is declared 2026-04-27; any chart-reader-class hypothesis added after that date enters a successor family with documented spent-α accounting per [ADR-0003](../decisions/ADR-0003-spa-vs-romanowolf.md).

### Why the split is necessary (Q-R1-1, Q-R1-12 remediation)

Round-1 quant-auditor finding Q-R1-1: Hansen 2005 SPA composite null `H_0: max_k E[d_k] ≤ 0` requires comparable performance differentials across `k`. Mixing within-arm (`gated − unconditional`) and cross-arm (`arm_gated − H050_gated`) statistics in a single family violates this. Round-1 finding Q-R1-12: H050's frozen pre-reg specifies Romano-Wolf step-down per ADR-0003, not Hansen SPA — placing H050 in a Hansen SPA cohort family without successor ID is an unauthorised pre-reg amendment. The two-family split resolves both findings simultaneously: H050 stays in its frozen Family A; the chart-reader arms occupy Family B with H050 as baseline anchor only.

## 7. Downstream documentation impact

The package requires updates to:

- [plan/hypothesis_backlog.md](../../plan/hypothesis_backlog.md) — new **Tier 2c — AI chart reader** section with rows for H057 / H058 / H059 / H060.
- [CLAUDE.md](../../CLAUDE.md) — Phase 2 / scope sections updated to reference the four new hypotheses; add the SPA-family-2026-04-27 declaration.
- [README.md](../../README.md) — add Tier 2c reference, hypothesis count update, current-status reference to this synthesis memo.
- [CHANGELOG.md](../../CHANGELOG.md) — to be created at repo root following Keep-a-Changelog conventions, backfilled from existing [docs/audits/](../audits/) trails.

These updates land in the second audit-remediate loop scoped to documentation, after this research package clears its own audit-remediate loop.

## 8. Residual scope notes

- **Compute envelope**: H059's full execution is contingent on the fold-0 pilot. If pilot wall-clock > 6 hr (2× the 3-hour estimate), H059 archives `null, infeasible` and is replaced by H059b on per-bar cadence.
- **Multi-sidecar helper**: three of four hypotheses block on `P1-MODEL-HASH-MULTI-SIDECAR-HELPER`. The interim composition rule (deterministic SHA256-of-sorted-SHA256-tuple) is documented in each design doc as the binding mechanism until the helper lands.
- **Spent-α accounting**: the Family B M=5 declaration consumes the project's α=0.05 budget for the 2026-04-27 chart-reader cohort. No additional Family B hypothesis can enter without a successor-family declaration.
- **Survey memo open question Q5**: confirmed no CLAUDE.md / ADR contradictions found.

## 9. Audit-remediate scope

The audit-remediate loop on this research package covers:

1. The survey memo itself (citation discipline, repo URL liveness, license claim accuracy).
2. The four design docs (method fidelity, citation discipline, internal consistency with H050, sidecar schema completeness).
3. This synthesis memo (cross-references, SPA family declaration, follow-up taxonomy).

Auditor selection per the audit-remediate-loop skill protocol:
- **`quant-auditor`** — method fidelity across the four design docs; statistical validity of the Family B M=5 SPA cohort + Family A M=1 H050 anchor; PIT canary completeness.
- **`literature-check`** — verify every citation, especially [arxiv 2510.13654](https://arxiv.org/abs/2510.13654), [arxiv 2604.12659](https://arxiv.org/abs/2604.12659), the model-card claims for TimesFM-2.5 / Chronos-Bolt / Qwen2.5-VL / PatchTST. Resolve `P1-CHARTREADER-SURVEY-LEAKAGE-VERIFY`.
- **`reproducibility-verifier`** — sidecar schema completeness, multi-sidecar `model_hash` composition, BLAS pinning per [ADR-0009](../decisions/ADR-0009-blas-thread-pinning.md), dataset checksum references, file path correctness.

Run in parallel per the skill protocol §Auditor selection.
