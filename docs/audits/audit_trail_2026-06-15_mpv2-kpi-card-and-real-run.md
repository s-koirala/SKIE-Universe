# Audit-remediate-loop trail — MPV2 KPI report card v1 + real-data run

**Date**: 2026-06-15
**Artifacts**: [research/01_meta_portfolio/MPV2/MPV2_kpi_report_v1.md](../../research/01_meta_portfolio/MPV2/MPV2_kpi_report_v1.md) + the MPV2 closed-loop real-data verdict (`P1-MPV2-REAL-RUN-AUDIT` + `P1-MPV2-REPROLOG-WIRE`).
**Closes**: `P1-MPV2-KPI-EMISSION`, `P1-MPV2-REAL-RUN-AUDIT`, `P1-MPV2-REPROLOG-WIRE`.
**Discipline**: per [SKILL.md audit-remediate-loop](../../research/01_hypothesis_register/) 3-round cap; Round-1 proper-isolated parallel quant-auditor + reproducibility-verifier; verdict **accept-with-remediation** (the load-bearing remediation — closing the repro-wire — empirically resolved the one critical finding).

## Round 1 — parallel branches

- **quant-auditor** (agentId `a32d7ff05ecec79db`) — verdict `proceed-with-remediation`; 1 critical + 1 major + 5 minor.
- **reproducibility-verifier** (agentId `a4ba0405012953e7a`) — empirically REPRODUCED the verdict on the regenerated `317429e4` substrate using the committed module functions + existing arm sidecars; 1 critical (repro-wire is LOW effort) + 3 major + 3 minor.

## Findings + remediation

| # | Branch | Sev | Finding | Remediation |
|---|---|---|---|---|
| F-1-1 | quant | critical | The identical 3-arm 364-session window carries two incompatible benchmark-MPPM pairs across the source of record — milestone-2 (1/N +0.225, B&H +0.171) vs milestone-3 (1/N 0.320, B&H 0.127). 1/N and B&H are parameter-free, so a weights-only causal correction cannot move them; the card adopted milestone-3 without reconciling. | **RESOLVED by reproduction.** The `--real` re-run reproduced 1/N 0.320, B&H 0.127 (3-arm) and 1/N 0.261, B&H 0.191 (2-arm) — i.e., the milestone-3 values ARE the reproducible-correct ones; milestone-2's +0.225/+0.171 were a superseded earlier drive (different per-session matrix). The card now binds to the single reproducible sidecar (`1980ec1e…`) as the sole source of record; the reconciliation note in the card §Reproducibility states the milestone-2 values are superseded. |
| F-1-2 | quant | major | §C spliced milestone-2 switching differentials with milestone-3 1/N−B&H bounds under a "milestone-3 authoritative" header, conflating two drives' per-session matrices. | **RESOLVED.** The single `--real` run produces ALL §C differentials coherently; the reproduced switching−1/N (−0.000675/−0.001477), switching−B&H (−0.000147/−0.000976), and 1/N−B&H (−0.000735/−0.001053) match the card's prior values exactly (they were correct), now sourced from one sidecar. §C rewritten as a per-window table from the sidecar. |
| R-3 | repro | major | The 2-arm switching MPPM was −0.020 in the card/buildout, but a deterministic re-run yields **+0.028** (the card copied the 3-arm −0.020 into the 2-arm row). | **CORRECTED.** Card 2-arm switching MPPM −0.020 → **+0.0279**. Qualitative verdict unchanged (+0.028 < 1/N 0.261 < B&H 0.191). The correction is flagged prominently in the card's §Reproducibility note. |
| R-1 | repro | critical | Closing `P1-MPV2-REPROLOG-WIRE` is LOW effort — the calendar-join, B&H builder, joint-Kelly conjunctive CI are all committed + tested; only a `--real` CLI branch + RunContext wrapper were missing. The buildout §91 "BLOCKING-before-real-verdict" text is stale (those follow-ups are CLOSED per the CLAUDE.md ledger). | **CLOSED.** Wired a `--real` branch + `_run_real` driver + RunContext + sidecar emission into [scripts/run_mpv2_closed_loop.py](../../scripts/run_mpv2_closed_loop.py) (+ the missing `sys.path` shim so the script runs as a CLI; ruff-clean). Ran it → sidecar `1980ec1e…` + ReproLog `logs/reproducibility/1980ec1eba2d4f4b965c44a965780370.json`. The stale buildout §91 text is corrected in the Phase-P buildout finalization note. |
| R-2 | repro | major | The card's `286829dc` substrate binding is honest + correct (arm streams embed it); the verdict is vintage-invariant on `317429e4` (common windows are strictly pre-2026). | **APPLIED.** Card frontmatter records both: `substrate_dataset_checksum: 317429e4` (the reproducing run) + `arm_stream_vintage: 286829dc` + the vintage-invariance rationale. |
| R-4 | repro | major | The `repro-log-incomplete` annotation was honest + correctly scoped; slightly understated how cheaply the gap closed. | **UPGRADED** to `repro-log-complete` (sidecar bound). |
| F-1-4 | quant | minor | The 2-arm {H060,H062} 1252-session window was presented co-equally with the pre-registered window; it is a wider-history SUBSET diagnostic, not the design.md §2 frozen common fold. | **APPLIED.** §0 + Table A/B label the 2-arm window "wider-history subset diagnostic"; the 3-arm is "v1-scoped pre-reg window". |
| F-1-5 | quant | minor | Conjunctive H_1 rejection correct, but the card led with the supplementary "nobody beats B&H" finding rather than the disposition basis (switching < 1/N alone rejects the conjunction). | **APPLIED.** §1 now states the disposition chain explicitly: switching−1/N lower bound covers zero → rejects conjunctive H_1 independent of the B&H leg; the "no allocator beats B&H" is labelled supplementary. |
| F-1-7 | quant | minor | Hansen SPA "N/A" justification imprecise (the card does report a 5-differential family). | **APPLIED.** §E Hansen-SPA row reworded: conjunctive AND-rule not max-over-family SPA; the descriptive differential CIs all cover zero so multiplicity adjustment only widens a NULL. |
| F-1-3 | quant | minor | slash-pair window mapping implicit. | **APPLIED.** Per-window labels added to §0 + Table B. |
| F-1-6 | quant | minor | `repro-log-incomplete` honestly disclosed; should note `P1-MPV2-REPROLOG-WIRE` resolves F-1-1/F-1-2. | **SUBSUMED** — the wire was closed; F-1-1/F-1-2 resolved by the reproducible sidecar. |
| R-5 | repro | minor | `run_mpv2` real-data error message pointed at a stale follow-up + the superseded `build_reward_matrix_from_sidecars`. | **APPLIED.** SystemExit message updated to point at `--real` (the new committed path). |
| R-6 | repro | minor | Two H055 C9 streams on disk; only `v2_sweep_20260602T200706Z` (cost-zero, 437 dates) is the verdict arm (vs `205808Z` cost-applied). | **APPLIED.** Hard-coded the verdict-arm run_id in `_REAL_ARM_SPECS` with an inline comment disambiguating the cost-zero verdict stream from the cost-applied milestone-5 stream. |
| R-7 | repro | minor | ReproLog 13-field provenance fully recoverable; nothing blocked the wrap. | **APPLIED** via the RunContext wrapper (git_head, pip-freeze SHA, dataset_checksums, rng_seed all captured). |

## Verification of the reproduced verdict (the load-bearing evidence)

The `--real` run (run_id `1980ec1eba2d4f4b965c44a965780370`; sci_sha `d85ae777…`; substrate `317429e4`; git_head `ce018515`) produced ONE coherent number set:

| Quantity | 3-arm (364 sess) | 2-arm (1252 sess) |
|---|---:|---:|
| ENB (Meucci) | 2.989 | 1.999 |
| selected bandit | EXP3.S | D-UCB |
| 1/N MPPM | 0.320 | 0.261 |
| B&H MPPM | 0.127 | 0.191 |
| joint-Kelly pooled MPPM (causal) | 0.150 | 0.045 |
| switching MPPM | **−0.020** | **+0.028** (was −0.020 — R-3) |
| 1/N − B&H one-sided lower | −0.0007 | −0.0011 |
| pooled − B&H one-sided lower | −0.0011 | −0.0011 |
| switching − 1/N one-sided lower | −0.0015 | −0.0006 |
| disposition (switch / pool) | null / null | null / null |

The causal joint-Kelly **zeros out H062** on both windows ([H055 0.608, H060 0.392, H062 0.0]; 2-arm [H060 0.257, H062 0.0]) and is dominated by naive 1/N — the DGU 2009 estimation-noise result, the empirical basis for the ADR-0030 §D-5 "winning pooler is 1/N" qualifier.

## Round-2 posture

Round-2 verification is satisfied by the empirical reproduction itself (the verifier independently re-ran the committed functions and matched every headline; the `--real` CLI then reproduced them a third time into a committed sidecar). No Round-2 separate invocation needed; the qualitative NULL verdict is invariant across all three reproductions and the one numeric correction (2-arm switching) is applied. **Verdict: accept.**

## Residuals (tracked)

`P1-MPV2-FULL-SURVIVAL-VECTOR` (allocator-layer terminal-wealth-q05 / Calmar-diff / median-path + forward projection — the §0 Component-3 + Tables 3a-c deferrals), `P1-MPV2-H050-DATED-RERUN` (4-arm verdict; H050 dateless), `P1-MPV2-FULL-GRID-ARMS` (H055/H062 ran smoke), `P1-MPV2-H055-FULL-OOS-WINDOW`, `P1-MPV2-SUBSTRATE-2026-EXTENSION`.
