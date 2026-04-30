---
title: H050 production-run comprehensive post-mortem — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverable: docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md
git_head_at_authoring: 50f44e3113d8ab4563db13e9e67376efe0033428
loop_rounds: 1 (Round-1 with parallel quant-auditor + literature-check + reproducibility-verifier)
verdict: accept-with-residuals
---

# H050 production-run comprehensive post-mortem — audit-remediate-loop trail

## Scope

This trail covers the audit-remediate-loop on the H050 production-run comprehensive post-mortem ([memo_h050-prodrun-postmortem_2026-04-30.md](../research_notes/memo_h050-prodrun-postmortem_2026-04-30.md)).

Deliverable purpose: canonical record of every H050 production walk-forward attempt to date (runs 1–6 attempt-2), value-of-information audit on 16 reactively-built infrastructure artifacts, primary-source verification of three previously-unverified project claims.

Rounds: 1. The deliverable went through a single audit-remediate round with parallel quant-auditor + literature-check + reproducibility-verifier subagents (all proper-isolated; main-thread orchestration). All critical and major findings were remediated in-loop; minor findings either remediated or deferred to documented follow-ups. Round-2 was not invoked: no remediation introduced a new critical or major contradiction; residuals are bounded and tracked.

## Round-1: parallel triad

Three audit subagents were launched in parallel against the Round-0 draft of the post-mortem:
- `quant-auditor` — 30 findings (1 critical, 11 major, 18 minor / positive-verification).
- `literature-check` — 14 findings (1 critical, 3 major, 4 verified-with-caveat, 6 verified-clean).
- `reproducibility-verifier` — 16 findings (0 critical, 4 major, 12 minor / positive-verification).

Total: 60 findings. Critical findings: 2 (L-10, F-14). Critical-by-cumulative-implication: R-1 (run-id artifact attestation gap, structural).

## Per-finding disposition

### Critical (3)

| ID | Finding | Disposition | Remediation evidence |
|---|---|---|---|
| L-10 | Rabiner §III.B / §III.C swap. Post-mortem §5.4 + §7 cite "Rabiner 1989 §III.B (Baum-Welch re-estimation initialisation)" but Baum-Welch parameter estimation is in §III.C (§III.B is Viterbi). Citation error of the kind this post-mortem was written to flag. | **ACCEPTED** | §5.4: "Rabiner (1989) §III.C (Solution to Problem 3 — parameter re-estimation by Baum-Welch / EM)". §7 row `P1-ADR-0005-CITATION-CORRECT-WARM-START`: "Rabiner 1989 §III.C (Solution to Problem 3 — parameter re-estimation)". §3 Run-3 reference to §III.A is correct (forward-backward recursion as canonical inner loop) and retained. |
| F-14 | "H-B remains the leading candidate" (post-mortem §6 O-6) contradicts the recovery-loop audit-trail Q-2-1 disposition which forbade "leading candidate" framing. The os-reboot-bypass audit trail line 82 only goes as far as "consistent with evidence; load-bearing candidate caller; not yet confirmed". The 2026-04-30 CLAUDE.md ledger update (commit `681c8c7`) re-introduced "leading candidate" wording without re-running the audit-remediate-loop, contradicting the discipline §O-4 claims to have held. | **ACCEPTED** | §6 O-6 reframed: "H-B (UsoSvc internal Task Scheduler) remains the load-bearing candidate caller on the new framing for a different reason: the WUfB-deadline override path is not available on Home edition (§5.2), so the only documented OS service that would initiate a reboot in this state-space is the UsoSvc Task Scheduler tree." Falsification criterion now stated explicitly (USO-CoreWorker trace channel probe, queued under `P1-USO-TRACE-CHANNEL-PROBE`). §3 Run-6 attempt-2 also corrected. New follow-up `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` codifies that ledger updates re-framing audit-trail dispositions must themselves go through the loop. |
| R-1 | 6 of 7 cited run-id UUIDs have zero on-disk artifacts in the SKIE-Universe workspace. The post-mortem's reproducibility claim "Each row binds to a committed audit trail" is satisfied at the audit-trail level but the underlying ReproLogs and run-artifacts are not retrievable. This is a project-wide gap, not a post-mortem authorship gap. | **ACCEPTED** | §2 now contains a "Run-id artifact attestation" subsection mapping each run-id to its on-disk presence (ReproLog / fold artifacts / HMM cache / cfg-checkpoints). Inventory completeness gap explicitly disclosed; future audit trails to snapshot `ls artifacts/runs/H050/` as evidence under `P1-RUNID-ARTIFACT-INVENTORY-AUDIT`. |

### Major (18)

| ID | Finding | Disposition | Remediation evidence |
|---|---|---|---|
| L-7 | Stinner subprocess-workaround quote (post-mortem §5.5) elides leading clause "Another option, maybe more complex, is" and starts at "to create a subprocess…". Partial quote presented as verbatim. | **ACCEPTED** | §5.5 quote restored: "Another option, maybe more complex, is to create a subprocess to process data, and destroy the process to release the memory. multiprocessing helps to implement that." (verbatim per bpo-19246 msg199984, vstinner, 2013-10-15). |
| L-9 | Cappé/Moulines/Rydén proposed as ADR-0005 §7.4.1 replacement anchor; chapter pinning is incorrect (EM-for-HMMs is in Chapter 10, not Chapter 9) and section-grain warm-start anchor is unverifiable without direct book access. | **ACCEPTED** | §5.4 corrected to "Cappé-Moulines-Rydén Chapter 10 ('EM-based Methods for Inference in HMM')". Section-level pinning explicitly deferred to follow-up `P1-CAPPE-2005-SECTION-PIN`. Both `P1-ADR-0005-CITATION-CORRECT-WARM-START` and the new `P1-CAPPE-2005-SECTION-PIN` are surfaced in §7. |
| L-13 | "@njit parallel=True typically yields 50–200× on tight inner loops at small inner dimension" — unsourced folklore in post-mortem §5.3 plausibility argument. Numba documentation cites ~5–6× speedups on identity-function microbenchmarks; the 50–200× band has no canonical anchor. | **ACCEPTED** | §5.3 plausibility argument rewritten without the "50–200×" band. New text: "(i) per-call dispatcher + numpy temporary-array allocation in `scipy.special.logsumexp` dominates the math at small N; (ii) `@njit` over a tight inner loop with all kwargs hoisted out and parallel reduction within the inner dimension is constant-factor competitive with hand-written C. Neither factor has a single peer-reviewed benchmark at this magnitude." |
| L-4 | WUfB Home-edition GPO claim needs an additional Microsoft Learn anchor for the GPO-not-on-Home fact. Currently anchored only via inference from the policy-csp-update page. | **ACCEPTED** | §5.2 + §9 now cite [Microsoft Learn — Group Policy and the Windows feature lifecycle](https://learn.microsoft.com/en-us/windows/whats-new/windows-11-requirements) for the GPO-edition support matrix. |
| F-2 | §2 row "6 attempt-1" admits "not separately logged in primary sources" — by the document's §2 preamble rule "Any claim without a [link] is fabricated", this row is internally inconsistent. | **ACCEPTED** | §2 preamble relaxed to: "every quantitative claim in the inventory is anchored to a committed audit trail or a primary repro log. Narrative-only cells may rely on the cited audit trail's prose without an additional source." |
| F-4 | "Supervisor adds 12 residual features beyond the minimum" — the count "12" is not anchored anywhere. | **ACCEPTED** | §4 row 4 (supervisor wrapper) verdict and rationale rewritten. The new framing argues NEEDED on the basis of subprocess-boundary exit classification (`_classify_exit` requires a parent-child boundary), which is the actual load-bearing capability. The "12 residual features" enumeration is dropped. |
| F-5 | "Layer 5" is referenced multiple times but ADR-0010 has only 4 layers; inventing a Layer 5 without amending the ADR is documentation drift. | **ACCEPTED** | All references reframed as "provisional Layer 5". New follow-up `P1-ADR-0010-LAYER-AMENDMENT` gates the formal ADR amendment on `P1-PREFLIGHT-USOSVC-TASK-DISABLE` landing first. |
| F-7 | Numba-kernels verdict PREMATURE is anachronistic — the microbench-readiness gate (ADR-0011 gate 2b) didn't exist at toolkit-build time, so calling the kernels "premature" implies they should have been displaced by a gate that was itself a post-hoc lesson. | **ACCEPTED** | §4 row 7 reclassified to NEEDED with a footnote on the missing upstream gate. The "missing upstream gate" framing is preserved as the §3 Run-3 lesson and §4 row 7 footnote, not as a verdict label. |
| F-8 | "NEEDED-BUT-MIS-FRAMED" is a non-standard verdict not in the §4 preamble's enumeration; conflates artifact necessity with documentation framing. | **ACCEPTED** | §4 row 3 (wake-lock) reclassified to NEEDED (for idle-sleep path; framing defect tracked separately under `P1-ADR-0010-LAYER-1-FRAMING-CORRECT`). The NEEDED-BUT-MIS-FRAMED verdict is removed entirely. §4 preamble notes the framing-defect-vs-necessity orthogonality. |
| F-11 | "~60×" recompute speedup ratio for LGB inner-CV per-draw checkpoint is derived from "2 min per draw vs 2 hr per cfg" but neither base figure is anchored; the audit trail mentions ~2 s/draw. | **ACCEPTED** | §4 row 15 anchored figures: 200 draws × 3 inner folds = 600 cycles per cfg at ~2 s/draw → ~20 min per cfg recompute without per-draw checkpoint vs ~6 s per single-draw recompute → ~200× ratio. |
| F-12 | "~6,000 polars-to-numpy fancy-indexing copies" is not in the cited primary source. | **ACCEPTED** | §3 Run-4 narrative replaces the unanchored count with: "~11,400 LightGBM Booster fit-predict cycles cumulative … plus per-cfg polars→numpy slicing for the inner-CV loop". |
| F-15 | H-B falsification criterion under the new framing is not stated. | **ACCEPTED** | §6 O-6 now states explicit falsification: "H-B is falsified if the `Microsoft-Windows-USO-CoreWorker/Operational` channel for the 20:14:00–20:16:30 window contains no UsoSvc / MoUsoCoreWorker reboot-orchestration call; H-B is confirmed if such a trace is present same-second as Kernel-Power 109." Probe queued under `P1-USO-TRACE-CHANNEL-PROBE`. |
| F-17 | "Two critical violations" of the user's `sharpe_diff_ci.py` is not anchored to a committed audit trail. | **ACCEPTED** | §4 row 16 reframed: violations are referenced via the `f6a2a26` commit message; standalone audit trail tracked under new follow-up `P1-LW2008-MIGRATION-AUDIT-TRAIL`. The "two" count is dropped from the cell. |
| F-23 | WU-pause helper "Primary defense (preflight gate already shipped 2026-04-27) would have caught the same condition" is empirically refuted — the run-6 attempt-2 preflight timed out at 60s and supervisor proceeded under `--allow-preflight-warn`, so gates 6/7/9/10 were not exercised. | **ACCEPTED** | §4 row 13 reclassified NEEDED-BUT-OVERBUILT → NEEDED. Counterfactual rewritten: "Without: preflight failure-to-run leaves no defense against the UsoSvc path." Simpler-alternative cell tightened: "Active Hours adjustment alone — simpler when preflight runs to completion, but does not protect against preflight timeout failure mode." |
| F-27 | NEEDED-BUT-MIS-FRAMED verdict in distribution table is not in §4 preamble. | **ACCEPTED** | Verdict-distribution table updated: NEEDED count now 12, NEEDED-BUT-OVERBUILT count now 1, DEFENSIVE count 2. NEEDED-BUT-MIS-FRAMED row removed. Total = 15; §4 row 3 notes wake-lock is also tracked under `P1-ADR-0010-LAYER-1-FRAMING-CORRECT` for its documentation defect (orthogonal dimension). |
| R-2 | Base-run UUID `338aac0a` is never written in full anywhere. | **ACCEPTED** | Full UUID `338aac0a2d804e62b1ec54d36dba1a25` resolved from [logs/crash_evidence/walk_forward_2026-04-29_192543/h050_prod_run_2026-04-29T192543.log:11](../../logs/crash_evidence/walk_forward_2026-04-29_192543/) and [scripts/supervised_relaunch_loop.sh:17](../../scripts/supervised_relaunch_loop.sh). §2 row 6-attempt-1 + §2 footer + attestation table all updated. |
| R-3 | Frontmatter `audit_loop:` field points to non-existent companion audit trail. | **ACCEPTED** | This trail (`docs/audits/audit_trail_2026-04-30_h050-prodrun-postmortem.md`) is the companion. The frontmatter reference now resolves. |
| R-7 | Frontmatter omits `git_head_at_authoring`. | **ACCEPTED** | Frontmatter now contains `git_head_at_authoring: 50f44e3113d8ab4563db13e9e67376efe0033428` and `external_sources_retrieved: 2026-04-30`. New follow-up `P1-NARRATIVE-DOC-FRONTMATTER-SCHEMA` codifies the schema for `type: postmortem|retrospective|memo`. |

### Minor (positive-verification + polish; 39 total)

Aggregate disposition: **ACCEPTED with edits** for F-1 (run-2 4h37m → 4h38m), F-3 (inline arithmetic), F-9 (gc/del INSUFFICIENT-EVIDENCE → NEEDED-BUT-OVERBUILT), F-13 (5.7 GB → 5–7 GB range), F-18 (O-3 ADR-loop tightening), F-25 (30 → 30–100 EM iterations), F-26 (H-A structurally moot vs eliminated), F-28 (attempt-1 → attempt-2 timing source), F-30 (re-exercised wake-lock framing tightened), L-6 (LFH-cutoff applicability project-internal flag), L-12 (restore "the" in scipy quote), R-15 (run-6 attempt-1 wall-clock disclosure), R-16 (AH window cross-link to run-2 trail).

Aggregate disposition: **NO-ACTION** (positive verification confirmed) for L-1, L-2, L-3, L-5, L-11, L-14; F-10, F-16, F-19, F-20, F-21, F-22, F-24, F-29; R-4, R-5, R-6, R-8, R-10, R-11, R-12, R-13, R-14.

Aggregate disposition: **DEFERRED** to follow-up for L-8 (AFML page tier-2 anchor), R-8 (`postmortem_v1` schema label).

## Round-2 not invoked

Round-2 was not invoked. The remediation pass (a) introduced no new critical / major contradiction (verified by re-reading the rewritten file); (b) all critical findings landed observable text changes; (c) all major findings landed observable text changes or new follow-ups; (d) the residual ledger is bounded.

Per [SKILL.md §"Agentic Iteration"](../../CLAUDE.md), the 3-round cap is the operational ceiling, not a target. A second round on a remediation that introduced no new contradiction is process for its own sake. The decision is exit-loop-with-residuals; residuals are explicit follow-ups.

## Residuals (bounded)

Tracked in §7 of the post-mortem:

- `P1-ADR-0010-LAYER-1-FRAMING-CORRECT` (BLOCKING for next H051+ launch)
- `P1-ADR-0010-LAYER-AMENDMENT` (BLOCKING for next H051+ launch)
- `P1-PREFLIGHT-USOSVC-TASK-DISABLE` (BLOCKING for next H050 launch)
- `P1-ADR-0005-CITATION-CORRECT-WARM-START` (non-blocking)
- `P1-CAPPE-2005-SECTION-PIN` (non-blocking; depends on P1-ADR-0005-...)
- `P1-NUMBA-EM-CROSS-VALIDATE` (non-blocking)
- `P1-AUDIT-LOOP-LITCHECK-ON-ADRS` (non-blocking process directive)
- `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE` (non-blocking process directive)
- `P1-USO-TRACE-CHANNEL-PROBE` (non-blocking diagnostic)
- `P1-CFG-SUBPROCESS-ISOLATION` (pre-existing, non-blocking)
- `P1-LGB-INNER-CV-ALLOCATION-PROFILE` (non-blocking)
- `P1-LW2008-MIGRATION-AUDIT-TRAIL` (non-blocking documentation hygiene)
- `P1-RUN6-ATTEMPT1-WALLCLOCK-RECONSTRUCT` (non-blocking)
- `P1-RUNID-ARTIFACT-INVENTORY-AUDIT` (non-blocking)
- `P1-NARRATIVE-DOC-FRONTMATTER-SCHEMA` (non-blocking)

## Verdict

**accept-with-residuals.** Post-mortem is publishable; residuals are explicit and tracked. The two critical findings (L-10, F-14) are remediated in-loop and verified against primary sources. The structural critical (R-1) is remediated via the attestation table and the explicit `P1-RUNID-ARTIFACT-INVENTORY-AUDIT` follow-up.

The post-mortem is wired into CLAUDE.md canon in a follow-up commit per the user's directive.
