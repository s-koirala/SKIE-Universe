---
title: H053 Cycle 7 Stage-0 HKS sanity — audit-remediate-loop trail
date: 2026-04-30
type: audit_trail
status: complete
deliverables:
  - scripts/run_h053_stage0_hks_sanity.py (NEW; ~410 lines)
  - tests/unit/test_h053_stage0_hks_sanity.py (NEW; 10 tests, all passing)
  - reports/h053/stage0_hks_sanity.md (NEW; disposition memo)
  - logs/reproducibility/h053_stage0_20260501T031914Z_h053_stage0_hks_sanity.json (sidecar)
  - pyproject.toml UPDATED (added pytest pythonpath=['.'] for canonical pytest invocation)
git_head_at_authoring: a57a9ba
loop_rounds: 1 (Round-1 with parallel quant + repro; remediation applied inline)
verdict: accept-with-remediation
substrate_dataset_checksum: bc06b4e1403b90be4355f4e32f98a52bf2b7f955de946f49f65ea2ca4f1c5665
sidecar_scientific_payload_sha256: 6b0ec5f5fe6f1abae2e622c6ef605a446074fa659003addfe5588c7e267f0f2e
---

# H053 Stage-0 HKS sanity — audit-remediate-loop trail

## Scope

Round-1 audit on the H053 Cycle-7 Stage-0 sanity deliverable: substrate-behavior
validation that the post-Cell-I roll-adjusted ES + NQ 1-min substrate exhibits the
canonical HKS Figure 1 intraday volatility U-shape. Closes the final Cycle-7
deliverable per [plan/h053_buildout_2026-04-28.md](../../plan/h053_buildout_2026-04-28.md).

Two subagents launched in parallel (proper-isolated; main-thread orchestration):
- `quant-auditor` (12 findings: 2 majors + 10 minors; agentId `a6bc891ec5305865b`; verdict `accept-with-remediation`)
- `reproducibility-verifier` (10 R-checks: 2 majors + 8 passes; agentId `a37d23bac0a037719`; verdict `proceed-with-remediation`)

Total: 22 findings (4 majors, 18 minors).

## Result

Stage-0 verdict: **PASS** — substrate exhibits HKS Figure 1 intraday volatility
U-shape on both ES and NQ:

| Symbol | n_sessions | σ_open | σ_close | median σ | open ratio | close ratio | verdict |
|---|---:|---:|---:|---:|---:|---:|:--:|
| ES | 2710 | 0.002967 | 0.002882 | 0.002099 | 1.4137 | 1.3731 | **PASS** |
| NQ | 2715 | 0.004328 | 0.003293 | 0.002514 | 1.7218 | 1.3099 | **PASS** |

Both exceed the 1.10× operational margin floor with comfortable headroom.

## Per-finding disposition

### Major (4)

| ID | Finding | Disposition | Remediation |
|---|---|---|---|
| F-1-1 / R-8 | Sidecar JSON written via hand-rolled atomic-write path; missing git_head, dataset_checksum, scientific-payload SHA256. CLAUDE.md user-global §Reproducibility binding violated. | **ACCEPTED** | Sidecar now records `_meta.git_head`, `_meta.scientific_payload_sha256`, AND `h053_stage0_hks_sanity.substrate_dataset_checksum` (per-partition SHA256 roll-up via new `_substrate_dataset_checksum` helper). The scientific-payload SHA is byte-deterministic across runs of the same script on the same substrate (excludes wall-clock-dependent `_meta.written_at` from the hashed payload). |
| F-1-2 | Disposition memo's `substrate_path` points to a SIBLING worktree (`inspiring-franklin-13a1f1`); not branch-portable. | **ACCEPTED** | Memo now records `substrate_dataset_checksum: bc06b4e...`; cross-worktree reproducibility is content-anchored, not path-anchored. Path retained for human reference but checksum is the load-bearing field. |
| R-1 | Sidecar SHA includes `_meta.written_at` → wall-clock-dependent; defeats provenance purpose. | **ACCEPTED** | `_write_sidecar` now returns `(path, file_sha256, scientific_payload_sha256)` tuple. The disposition memo records `sidecar_scientific_payload_sha256` (re-derivable) AND `sidecar_file_sha256` (one-time provenance for THIS run). |
| R-9 | Canonical `pytest tests/...` invocation fails with `ModuleNotFoundError: scripts.run_h053_stage0_hks_sanity` (no `pythonpath` directive in pyproject). | **ACCEPTED** | Added `pythonpath = ["."]` to `[tool.pytest.ini_options]` in pyproject.toml with `# justify:` comment. Verified: `uv run pytest tests/unit/test_h053_stage0_hks_sanity.py` now passes 10/10. Full H053 suite (183/183) green under canonical invocation. |

### Minor — applied inline

| ID | Finding | Remediation |
|---|---|---|
| F-1-6 | Memo's `sidecar_sha256` truncated to 16 chars. | Replaced with full 64-char `sidecar_scientific_payload_sha256` AND `sidecar_file_sha256`. |
| F-1-7 | Citation overstates "§III + Figure 1"; verdict uses Figure 1 only. | Script docstring + sidecar `method_reference` updated to "Figure 1" only; §III continuation finding re-described as informational diagnostic only. |
| F-1-8 | BLAS env-var pinning not enforced at startup. | New `_check_blas_thread_pinning` helper logs WARN if any of `OMP_NUM_THREADS`/`MKL_NUM_THREADS`/`OPENBLAS_NUM_THREADS` is not "1". Called at the start of `main()`. |
| F-1-12 | Memo's "13:30 ET FOMC clustering" attribution incorrect (FOMC is 14:00 ET since 2012). | Memo now describes the 13:30 ET ACF as "pattern observed but release-window attribution not primary-source-verified"; new follow-up `P1-H053-STAGE0-MIDAFTERNOON-ACF-ATTRIBUTION` tracks the primary-source mapping if attribution becomes load-bearing. |

### Minor — filed as follow-ups

| ID | New follow-up |
|---|---|
| F-1-3 | `P1-H053-STAGE0-LAG1-NAN-SEMANTICS` — `_lag1_autocorr` filters NaN before forming pairs; for the H053 substrate this is innocuous (>99% completeness) but the helper's correctness contract should match its name. |
| F-1-4 | `P1-H053-STAGE0-COVERAGE-FLOOR-EMPIRICAL` — replace 200-session hard floor with `0.80 × n_sessions_observed` adaptive criterion. |
| F-1-5 | `P1-H053-STAGE0-BIN-CONTIGUITY` — assert `pl.col("ts_event").max() - min() == 29 minutes` per bin (substrate guarantees no duplicates per AFML §2.4.3, so this is belt-and-braces). |
| F-1-9 | `P1-H053-STAGE0-ROLL-DAY-DOC` — within-bin returns are roll-immune by construction (open and close in same bar window); cross-day ACF impact bounded by ~3% roll-day session share. Document in script docstring. |
| F-1-10 | `P1-H053-STAGE0-PER-BIN-VALUE-ASSERT` — `test_bin_boundaries_match_bin_starts` only checks bin count (13); should also assert per-bin open/close values match the linear-drift formula to machine precision. |
| F-1-11 | `P1-H053-STAGE0-CLOCK-PY-DERIVE-RTH` — derive `_BIN_STARTS_ET` from `clock.py` RTH boundaries instead of hard-coded literal so CME schedule changes don't silently diverge. |
| F-1-12 | `P1-H053-STAGE0-MIDAFTERNOON-ACF-ATTRIBUTION` — primary-source release-window mapping for the 13:30 ET / 14:30 ET / 15:30 ET ACF spikes. |

## Round-2 not invoked

Round-2 was not invoked. Rationale:
1. No critical findings.
2. The 4 majors all have clear inline remediations applied; the F-1-1/R-8 ReproLog-style provenance fix is the most material change and was verified by re-running the script + confirming the new sidecar fields populate correctly.
3. Per [CLAUDE.md](../../CLAUDE.md) §"Agentic Iteration", the 3-round cap is the operational ceiling; reserving Round-2 for follow-up loops where it adds marginal value.

## Residuals

**Closed by this loop:**
- Cycle 7 final deliverable: H053 Stage-0 HKS sanity check.
- **Cycle 7 complete**: feature factory (Blocks A/B/C/D) + archetype classifier + power-calibration solver + PIT canaries + bar-edge regression gate + Stage-0 sanity all landed.

**Critical method/correctness fixes landed in-loop:**
- ReproLog-style provenance wired into Stage-0 sidecar (git_head + dataset_checksum + scientific-payload-SHA).
- Canonical `pytest` invocation works for all H053 tests (pyproject `pythonpath`).
- BLAS-pinning contract enforced at runtime via WARN.
- Citation discipline tightened (Figure 1 only).

**New follow-ups filed (7):** P1-H053-STAGE0-LAG1-NAN-SEMANTICS, P1-H053-STAGE0-COVERAGE-FLOOR-EMPIRICAL, P1-H053-STAGE0-BIN-CONTIGUITY, P1-H053-STAGE0-ROLL-DAY-DOC, P1-H053-STAGE0-PER-BIN-VALUE-ASSERT, P1-H053-STAGE0-CLOCK-PY-DERIVE-RTH, P1-H053-STAGE0-MIDAFTERNOON-ACF-ATTRIBUTION.

## Verdict

**accept-with-remediation.** All 4 major findings remediated inline.
183/183 H053-suite tests green under canonical `pytest` invocation.

**Cycle 7 complete.** Per [plan/h053_buildout_2026-04-28.md](../../plan/h053_buildout_2026-04-28.md)
§Cycle status, Cycle 7 is now ✓ done. Ready to proceed to Cycle 8 (Stage-1
mediator-only walk-forward, Gao 2018 replication on ES/NQ 09:45-10:30 ET) after
the H050 BLOCKING follow-ups close.
