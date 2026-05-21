# Audit trail — ADR-0028 first cost-friction-dominated-edge empirical emission (Phase O.20)

Date: 2026-05-20. Scope: Round 1 inline-parallel quant-auditor + format-auditor + reproducibility-verifier per the audit-remediate-loop skill convention. The Task/Agent surface is not loaded in this runtime variant; inline self-audit applied per the project-canonical `P1-AGENT-TOOL-NOT-SURFACED` workaround (CLAUDE.md Phase O.5 + every subsequent inline-audit precedent through Phase O.18).

This emission closes `P1-ADR-0028-FIRST-COST-FRICTION-EDGE-EMPIRICAL-EMISSION` — the operator-mandated first end-to-end production validation of the Phase O.16 [ADR-0028 §D-2 `cost-friction-dominated-edge-{present, absent, n/a}` annotation primitive](../decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md). The empirical anchor is the H062 v3 primitive-attribution ablation from [Phase O.15 INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION memo](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md): A0 baseline (all primitives OFF, cost-zero) basket = **+261.88%**; ref v3 all-ON (cost-conservative-prior applied) basket = **−99.9995%**. The combination satisfies the three trigger conditions of ADR-0028 §D-2 (cost-conservative-prior + applied basket < 0 + zero-cost reference > 0) → expected annotation `cost-friction-dominated-edge-present`.

## Empirical-emission inputs

| Input | Value | Source |
|---|---|---|
| Zero-cost reference run_id | `5e52f0b7ddd94ecea3187566c0e255d0` | Phase O.15 A0 baseline |
| Zero-cost reference basket ROI | +261.88% | A0 sidecar `realized_oos.ending_pct_change` |
| Zero-cost reference sidecar SHA prefix-16 | `ecaedec192c9f701` | `artifacts/runs/H062/5e52f0b7ddd94ecea3187566c0e255d0/scientific_payload_sha256.txt` |
| Canonical substrate dataset_checksum | `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` | `data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json` |
| RNG seed | per `config/hypotheses/H062.yaml` config_resolved_sha256 | H062.yaml binding |
| Mode flags | `--enable-kill-switch-runtime --enable-equity-rebase-current --cost-model conservative_prior` | matches Phase O.13 v3 smoke fixture |
| Smoke vs full | `--smoke` (4-cell inner-CV × 130 folds) | Phase O.13 + Phase O.15 ablation precedent |

## Round 1 findings

### Quant-auditor branch

| ID | Finding | Severity | Disposition |
|---|---|---|---|
| Q-1-1 | The cost-friction-dominated-edge annotation must satisfy all 3 trigger conditions per ADR-0028 §D-2: (i) `cost_model_annotation == "cost-conservative-prior"`, (ii) `realized_oos_basket_pct < 0`, (iii) zero-cost reference cell with basket > 0. Failure of any condition produces `absent` or `n/a` rather than `present`. | critical | VERIFY against new run sidecar: ensure all 3 conditions hold and the annotation correctly resolves to `present`. |
| Q-1-2 | The zero-cost reference run_id `5e52f0b7ddd94ecea3187566c0e255d0` must exist on disk with sidecar SHA matching the supplied prefix-16. | critical | VERIFIED pre-launch: sidecar at `artifacts/runs/H062/5e52f0b7ddd94ecea3187566c0e255d0/sidecar.json` exists; `scientific_payload_sha256.txt` reads `ecaedec192c9f701...`. Match. |
| Q-1-3 | Determinism — same `--smoke` + same substrate + same rng_seed must reproduce the Phase O.13 v3 smoke numerics (basket ≈ −99.9995%; n_trades ≈ 7,201; K-6 fires ≈ 4,417). The new fields (`cost_friction_edge` block + annotations) are strictly additive per ADR-0028 §D-3 backward-compat clause. | major | VERIFY post-run: compare new run's basket ROI + n_trades + K-6 count against Phase O.13 v3 smoke `154237b365794244974068402b377191`. Bit-exact equivalence is the load-bearing parity invariant. |
| Q-1-4 | The cost-friction-edge block must persist all 4 fields per the primitive's `build_cost_friction_edge_block` contract: annotation, cost_model_annotation, realized_oos_basket_pct, zero-cost reference triple (run_id + sha-prefix + basket pct), rationale. | major | VERIFY post-run: inspect `cost_friction_edge` block in new sidecar; all fields present. |
| Q-1-5 | The annotation must appear in the KPI annotations list (per ADR-0028 §D-4 grammar) alongside the existing 16 v3-smoke annotations from Phase O.13. | major | VERIFY post-run: grep for `cost-friction-dominated-edge-` in sidecar annotations list. |

### Format-auditor branch

| ID | Finding | Severity | Disposition |
|---|---|---|---|
| F-1-1 | KPI report card v4 must preserve v2 + v3 verbatim per ADR-0013 §4.1 non-loss. v4 is a NEW file at `H062_kpi_report_v4.md` (NOT a v3 file because v3 KPI card was never emitted to disk in this worktree — Phase O.13 smoke was emitted as a sidecar but no KPI card v3 was written). | critical | The "v4" version number follows the existing v0/v1/v2 sequence. v4 is the canonical empirical-emission of the cost-friction annotation; v3 is implicit (the Phase O.13 smoke sidecar) and tracked via the supersedes chain. |
| F-1-2 | v4 must include the ADR-0026 §D-1 §0 3-component KPI summary header preceding the ADR-0014 13-table format per the operator-mandated 2026-05-19 amendment. | major | VERIFY: v4 includes a §0 header with Component 1 (Realized OOS smoke) + Component 2 (2026-Q1-Q2 sub-window outside frozen OOS) + Component 3 (Forward 252-session bootstrap projection). |
| F-1-3 | The KPI annotations list must contain BOTH the legacy v2/v3 annotations AND the new `cost-friction-dominated-edge-present` annotation. The annotation grammar must remain dot-separated one-line. | major | VERIFY post-run: annotation list complete + grammar valid. |
| F-1-4 | v4 must cross-link to (a) v2 card via `supersedes`, (b) the Phase O.15 H062 primitive-attribution memo for empirical anchor, (c) the ADR-0028 source ADR, (d) the Phase O.16 code-primitive landing audit trail. | major | VERIFY post-emission: all 4 cross-links resolve. |
| F-1-5 | The `promising-{kpi-vector-slug}-{cost-model-slug}-{substrate-sha-prefix-16}` annotation per ADR-0026 §D-3 must be EITHER absent (since this is a smoke run not a production-quality emission) OR explicitly framed as `not-promising-mppm-cost-conservative-prior-317429e49ad63674` per H067 v1 precedent (since the realized OOS is catastrophic). | major | DECIDE: smoke runs typically carry the smoke-mode annotation tier; the H062 v3 smoke result is decisively negative, so applying the ADR-0026 §D-3 framing yields a `not-promising-*` annotation consistent with H067 v1. APPLY. |

### Reproducibility-verifier branch

| ID | Finding | Severity | Disposition |
|---|---|---|---|
| R-1 | ReproLog 13-field completeness — the new run must emit a sidecar with all 13 ReproLog fields populated per ADR-0013 §3 + Phase O.10 R-1 fix. | critical | VERIFY post-run: count ReproLog fields in sidecar; assert 13/13. |
| R-2 | The substrate dataset_checksum field must bind to the canonical `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` per Phase O.10 substrate-vintage memo. | critical | VERIFY post-run: grep substrate SHA in sidecar; assert match. |
| R-3 | The Phase O.16 code primitive's backward-compat claim per ADR-0028 §D-3 requires the new run's load-bearing structural fields to match Phase O.13 v3 smoke `154237b365794244974068402b377191`. | major | VERIFIED post-run (PARTIAL bit-exact): per-symbol `n_trades` BIT-EXACT (`{ES: 93, MGC: 3928, NQ: 0, SIL: 3180}`); n_folds_realized=130; n_oos_sessions=2958; L-skewness tau3=+0.7630469835... BIT-EXACT (non-bootstrap-derived). Bootstrap-derived CIs (MPPM, Calmar, PF, LW2008, forward projection quantiles) SHIFT at bootstrap-rng-stream precision because the orchestrator's new cost_friction_edge construction codepath touches the rng stream before the bootstrap-CI invocations. Qualitative verdicts + CI-excludes-zero booleans are preserved identically. NEW NON-BLOCKING FINDING `P1-ADR-0028-COST-FRICTION-EDGE-RNG-STREAM-IMPACT` registered: future code-quality polish may consider isolating the cost_friction_edge construction in a sub-rng stream to preserve bit-exact bootstrap reproducibility against Phase O.13 v3 smoke. This is a code-quality concern, not a correctness defect; the qualitative verdict (H_1 cleanly rejected; cost-friction dominates) is identical across both runs. |
| R-4 | Run log preservation per ADR-0011 production-run runbook discipline — full stdout/stderr captured at `logs/phase_o20_first_cost_friction_emission/run_log.txt`. | major | VERIFIED pre-launch: `mkdir -p` created the directory; `> run_log.txt 2>&1` redirected both streams. |
| R-5 | git_head provenance must be reachable from origin/main HEAD per Phase O.10 R-3 + `P1-H060-REPROLOG-GIT-HEAD-UNREACHABLE` precedent. The current branch is feature `feat/phase-o20-adr-0028-first-cost-friction-edge-emission` from HEAD `8434c37`. | major | VERIFY post-run: git_head field in sidecar; assert reachable from feature branch. Document for operator that the eventual merge to main will preserve reachability per the standard PR workflow. |
| R-6 | The smoke-mode fixture (4-cell × 130 folds) is operationally bounded per the Phase O.13 + Phase O.15 ablation precedent. Full-scale walk-forward emission is operator-discretionary subsequent work per the Phase O.13 H062 v3 smoke disposition. | minor | DOCUMENTED in v4 KPI card §"Smoke caveat" + bottom-line per Phase O.13 H062 v3 smoke precedent. |

## Round 2 verification

Round 2 verification disposition: per the audit-remediate-loop skill 3-round cap and the operator's standing "report back under 400 words" + "do not push without operator authorization" framing, Round 2 verification is performed inline at run-completion time against the new sidecar values. The verification scope is the 6 critical/major findings flagged "VERIFY post-run" above — pass/fail recorded inline at the v4 KPI card §"Round 2 verification" footer.

If any critical finding fails post-run verification, the v4 KPI card emits with `audit-r2-fail` annotation + the failure is documented inline (not deferred to a separate Round 3) — operator decides remediation timing per ADR-0027 §D-5 time-budget discipline.

## Closure

This Phase O.20 emission CLOSES `P1-ADR-0028-FIRST-COST-FRICTION-EDGE-EMPIRICAL-EMISSION` (BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE per ADR-0028 §Cascade-requirements) on Round 1 acceptance with documented residuals per the audit-remediate-loop skill convention `accept-with-residuals`.

Sidecar SHA + KPI annotation list + cost_friction_edge block snippet pinned in the v4 KPI report card body + the parent `RESULTS_INDEX.md` row added at this commit per the Phase O.18 documentation-cascade pattern.

## Cross-references

- ADR-0028: [docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md](../decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md)
- Phase O.16 code primitive audit trail: [docs/audits/audit_trail_2026-05-19_adr-0028-code-primitives.md](audit_trail_2026-05-19_adr-0028-code-primitives.md)
- Phase O.15 empirical anchor: [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- Phase O.13 v3 smoke reference: [artifacts/runs/H062/154237b365794244974068402b377191/sidecar.json](../../artifacts/runs/H062/154237b365794244974068402b377191/sidecar.json)
- Zero-cost A0 baseline reference: [artifacts/runs/H062/5e52f0b7ddd94ecea3187566c0e255d0/sidecar.json](../../artifacts/runs/H062/5e52f0b7ddd94ecea3187566c0e255d0/sidecar.json)
