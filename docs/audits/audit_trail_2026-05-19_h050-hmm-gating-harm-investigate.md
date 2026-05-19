# Audit trail — INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM (Phase O.18)

- **Date**: 2026-05-19
- **Scope**: Empirical decomposition of the Phase G H050 v1 catastrophic gating outcome (T_H050 < 0 with LW2008 CI excluding zero negatively on BOTH ES + NQ; realized $10K equity −81% / −84%) into four discriminable sub-hypotheses (H-a random / H-b anti-selection / H-c whipsaw / H-d distribution-shift).
- **Discipline**: ADR-0027 §D-1 investigation-memo template + §D-3 empirical-before-amendment sequencing.
- **Run-id under investigation**: `31d23ecd8e3842dd8ebd5687ce9c91d5` (Phase G clean-completion v1 walk-forward).
- **Substrate**: `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d` (pre-Cell-I).
- **Investigation sidecar SHA**: `1ebf175b49625b3c485e17eb5495906fc304ab0cc3c5000a866f0ad0f08e63d5`.
- **Investigation memo**: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../../research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md).

## Round 1 (inline-execution per SKILL.md 3-round cap)

Single-round audit-remediate-loop per the `P1-AGENT-TOOL-NOT-SURFACED` documented workaround pattern. Parallel quant + reproducibility branches inline.

### Quant findings

| Finding | Severity | Disposition |
|---|---|---|
| F-Q-1: Verified the OOS-returns parquet schema (gated_return / unconditional_return) matches the orchestrator emission convention at [scripts/run_walk_forward.py:2797-2848](../../scripts/run_walk_forward.py). Gated returns are zero ONLY when regime=0 (not when classifier produces zero position, since `sign(2p-1)` is always +1/-1). | n/a (verified) | n/a |
| F-Q-2: Annualisation basis pinned to RTH (√(252 × 390)) per H050 design.md §2.1 session-policy. Matches metrics_summary.json `sharpe_unconditional` / `sharpe_gated` to within rounding tolerance. | major | Verified — bar-level SR_bar values from this investigation reconcile with the metrics_summary fields. |
| F-Q-3: Per-state Sharpe computed on the unconditional series restricted to active vs inactive subsets (counterfactual: "what would the directional signal earn on these bars at full intensity"). This is NOT the same as the gated Sharpe, which suffers an additional cost-drag from position flips. The decomposition explicitly distinguishes (a) per-state UNCOND statistics from (b) the cost-drag delta. | major | Documented inline in memo §6.1 / §6.4. |
| F-Q-4: Anti-selection (H-b) verdict reframed to be cleanly distinguished across mean dimension vs Sharpe dimension. ES is anti-selective on BOTH; NQ is anti-selective only on Sharpe (not mean). The Sharpe-dimension verdict applies to both symbols. | critical (would be a misframing if conflated) | Memo §6.6 + §7.1 explicitly separates the two dimensions and reports both. |
| F-Q-5: Stationary distribution computed via left-eigenvector of `exp(log_transmat).T` with eigenvalue closest to 1. This is the canonical approach for irreducible 2-state HMMs. NQ shift +8.6% is in a direction that should help (more bars in supposedly-favourable state) yet still produces catastrophic Sharpe degradation — strong empirical evidence H-d is NOT load-bearing. | minor | Memo §6.5 documents this point. |
| F-Q-6: H-c (whipsaw) magnitude calibrated: cost-drag per bar exceeds full-path unconditional mean magnitude by 1.9× (ES) to 5.7× (NQ). This is the load-bearing empirical anchor. | n/a (load-bearing) | n/a |

### Reproducibility findings

| Finding | Severity | Disposition |
|---|---|---|
| F-R-1: Read-only investigation; per ADR-0013 §4.1 non-loss, the existing v1 sidecar at `artifacts/runs/H050/31d23ecd8e3842dd8ebd5687ce9c91d5/` is preserved verbatim. The investigation emits a SEPARATE sidecar under `artifacts/runs/H050/investigations/hmm_gating_harm/`. | n/a (verified) | n/a |
| F-R-2: Investigation sidecar includes git_head + decomposition_timestamp_utc + parent_run_id + parent_substrate_sha256 + scientific_payload_sha256 + per-symbol per-state full decomposition. Auditor-traceable via SHA on the sidecar.json file. | n/a (verified) | n/a |
| F-R-3: HMM cache pickle loaded from the canonical Phase G `31d23ecd...` run_id artifact tree at the sibling worktree (per Phase O.1 follow-on `P1-DATA-AVAILABILITY-AUDIT-DISCIPLINE` ledger entry, the canonical run-id artifacts live in sibling worktrees; reading from the sibling is acceptable for read-only investigations). | minor | Documented in script docstring. |
| F-R-4: Selected label horizon = 0120 per H050 metrics_summary.selected_label_cfg (pt_sl=1.0, vertical_barrier=7200s=120min). All 3 horizons (0030/0060/0120) produce essentially identical HMM parameters per the cache inspection — the HMM is fit on the same return series across label configs (cache key includes label_horizon for the inner-CV grid but the resulting fit is stable). | minor | Documented; no impact on findings. |
| F-R-5: All numeric findings reproducible via [scripts/investigate_h050_hmm_gating_harm.py](../../scripts/investigate_h050_hmm_gating_harm.py) on the canonical Phase G fixture. | n/a (verified) | n/a |

### Round 1 verdict

`accept-with-residuals`. Critical finding F-Q-4 (mean vs Sharpe dimension separation) remediated inline before commit. No Round 2 verification required at memo-landing time per ADR-0027 §D-3 (the memo is the EMPIRICAL INPUT to any future ADR amendment; the ADR amendments themselves require their own audit cycles).

## Cross-references

- Investigation memo: [research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md](../../research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md).
- Decomposition script: [scripts/investigate_h050_hmm_gating_harm.py](../../scripts/investigate_h050_hmm_gating_harm.py).
- Investigation sidecar: [artifacts/runs/H050/investigations/hmm_gating_harm/sidecar.json](../../artifacts/runs/H050/investigations/hmm_gating_harm/sidecar.json) (SHA `1ebf175b49625b3c485e17eb5495906fc304ab0cc3c5000a866f0ad0f08e63d5`).
- Parent KPI report card: [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md).
- ADR-0027 §D-1 + §D-3: [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../decisions/ADR-0027-operational-discipline-bounded-exploration.md).
- ADR-0013 §4.1 non-loss: [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).
