---
session_id: 2026-06-02_1433_regime-switching-portfolio-buildout
date: 2026-06-02T14:33:39Z
project: SKIE-Universe
worked_by: [main, general-purpose, literature-check, quant-auditor, code-reviewer]
status: in-flight
phase: Phase P (ADR-0029 regime-switching meta-allocation)
audit_trail: docs/audits/audit_trail_2026-06-02_portfolio-engine.md
---

## Goal
Adopt the regime-switching meta-allocation closed loop as the project's center of gravity (operator 2026-06-02 directive on the external-validity / climate-specificity problem), and build the machinery toward the falsifiable verdict: **does a closed-loop allocator beat 1/N AND buy-and-hold OOS?** Plus answer + build the operator's follow-up: simultaneous multi-asset long/short Kelly portfolio (not single-asset).

## Done
All landed in the working tree, **ruff-clean, audited**; **no commit** (operator ceremony pending). Each ran a parallel audit-remediate-loop (R1) unless noted.
- **ADR-0029** [docs/decisions/ADR-0029-regime-switching-meta-allocation-central-program.md] (accepted) + foundations memo [docs/research_notes/memo_regime-switching-closed-loop-foundations_2026-06-02.md] + buildout [plan/buildouts/phase_p_regime_switching_closed_loop_buildout.md]. Lit-check `accept` (24 DOI-verified sources, no inversion); quant 1 major + 7 minor remediated. Trail: docs/audits/audit_trail_2026-06-02_adr-0029-regime-switching-central-program.md.
- **P-2 early-warning detector** [src/skie_ninja/inference/early_warning.py] (CSD + CUSUM + drawdown-velocity; 39 tests). R1: 2 critical (F-1 flat-PnL false-fire; F-2 trailing-reference self-cancel) + majors remediated; CSD advisory-by-default + frozen-reference. Trail: audit_trail_2026-06-02_phase-p-early-warning-primitive.md.
- **P-3 ergodicity sizing** [src/skie_ninja/sizing/ergodicity.py] (`cppi_risk_overlay` + `joint_kelly_fractions`; 27 tests). R1: 2 critical (joint-Kelly could return a bankrupting fraction → no-ruin SLSQP constraint; floored growth masked ruin → `bankrupts_on_path`) + majors remediated. Trail: audit_trail_2026-06-02_phase-p-ergodicity-sizing-primitives.md.
- **MPV2 pre-registration** [research/01_meta_portfolio/MPV2/design.md] (frozen `designed`; arm set {H050,H055,H060,H062}) + **closed-loop runner** [scripts/run_mpv2_closed_loop.py] (P-1 builder + P-4 Meucci-ENB correlation + P-5 bandit→early-warning→CPPI loop vs sized-1/N + B&H; 26 tests, synthetic-validated). R1: look-ahead CLEAN; 1 critical (sized-consistent benchmarks) + 6 majors remediated. Trail: audit_trail_2026-06-02_mpv2-closed-loop.md.
- **Portfolio engine** [src/skie_ninja/meta/portfolio.py] (ADR-0020 `P1-META-PORTFOLIO-ORCHESTRATOR-IMPL`): `directional_returns` (long/short via signed returns) + `cap_by_instrument` (per-instrument gross caps) + `construct_portfolio` (joint-Kelly book; 23 tests). R1: 1 critical (int-cap AttributeError) + 3 quant majors remediated. Trail: audit_trail_2026-06-02_portfolio-engine.md.
- **P-1 extractor + H050 back-fill**: `extract_arm_per_session` (sidecar field OR oos_returns.parquet column) in run_mpv2_closed_loop.py. H050's committed `gated_return` (verified LOG) → a REAL 2,328-session arm array without a re-run. Focused-scope landing (real-data-verified + 5 tests).
- **115 meta-allocation/Phase-P tests green.** Ledger: CLAUDE.md Phase-P sub-entries + CHANGELOG + buildout updated.

## In flight
The **real-data verdict** is not yet produced — everything above is synthetic-validated only. P-1 is **partially** done: H050 back-filled from committed artifacts; **H055, H060, H062 still need orchestrator re-runs** on a regenerated substrate (substrate is empty in this worktree; 31 raw CSVs intact → regenerable). The MPV2 closed-loop + portfolio engine are correct and waiting on the calendar-aligned 4-arm reward matrix.

## Decisions made (with rationale)
- **Arm set {H050, H055, H060, H062}** — one representative per signal class (HMM-gated directional / mean-reversion / daily-trend / intraday-breakout), chosen to MAXIMIZE de-correlation (the precondition for the ergodicity pooling lift). H052a/H053/H054/H065/H067/H068 reserved for v2 (correlated or null).
- **Ergodicity reframing (load-bearing)**: super-Kelly *reduces* the time-average growth the operator experiences (Peters 2019); the route to durable aggressive upside is N concurrent de-correlated pooled arms (variance ÷N), NOT higher leverage. Promotable Kelly capped at full-Kelly; super-Kelly stays sandbox-only annotated.
- **Switching (MPV2) vs simultaneous (portfolio) are COMPLEMENTARY** — switching picks WHICH arm; the portfolio holds MANY concurrently (the pooling lift). A future meta-layer composes them.
- **CSD advisory-by-default** (overlapping-window Kendall-τ false-positives on iid noise → surrogate-null calibration deferred; gating = CUSUM + drawdown).
- **Sized-consistent benchmarks** in MPV2 (size 1/N + B&H through the same overlay; the raw-selection differential is a secondary diagnostic).
- **Long/short via signed returns** (short = signal −1 → profitable short shows positive directional return); reuses long-only joint-Kelly unchanged. Per-instrument GROSS cap is conservative (`gross ≥ |net|`).
- **KPI headline = median/time-average (MPPM ρ=1)**, ensemble mean demoted (ADR-0029 §D-3.1).

## What did NOT work
Dead-ends + audit-caught defects (documented so a successor does NOT rediscover them):
- The original MPV1 **switching-only** framing is incomplete — the ergodicity thesis favors *simultaneous* pooling; MPV2 wires switching, the portfolio engine adds the concurrent mode.
- joint-Kelly with the bare `1e-9` log-floor could return a **guaranteed-bankrupt** fraction (worst-period gross < 0) — fixed with a per-period no-ruin SLSQP constraint.
- The early-warning CUSUM with a **trailing-window reference self-cancels** on a decayed path (reference absorbs the shift) — fixed to a frozen leading/establishment reference; a finite leading window is itself a noisy estimate (false-positives) → frozen-reference is the closed-loop-correct choice.
- The **heuristic effective-breadth** `N/(1+(N−1)ρ̄)` understates the canonical eigenvalue ENB → replaced with Meucci 2009 ENB.
- Median-terminal-wealth ≠ time-average growth off-lognormality — report both (median path AND MPPM ρ=1), not equated.
- `isinstance(cap, float)` is False for an int cap → AttributeError → fixed to `isinstance(cap, dict)`.

## Audit branches skipped (and why)
Per the audit-remediate-loop SKILL.md "Routing rules": each deliverable ran **quant-auditor + code-reviewer** (and **literature-check** for ADR-0029, the only citation-dense artifact). **reproducibility-verifier was NOT run** on the code primitives — the repro concern that matters here is look-ahead/causal-alignment, which the quant-auditor covered directly (perturbation-tested CLEAN for MPV2); ReproLog/substrate-checksum reproducibility (repro-verifier's domain) does not apply to synthetic-validated primitives and is deferred to the real-data run (`P1-MPV2-REPROLOG-WIRE`). The P-1 extractor took a focused-scope landing (I/O + real-data verification + 5 tests + return-convention check) rather than a full parallel triad, per the primitive-landing convention.

## Open decisions queued for operator
1. **Authorize the multi-hour P-1 compute** (substrate regen ~30 min + H055/H060/H062 re-runs; H050 ~7-8 hr if a fresh run is wanted vs the back-fill). This is the gate to the real verdict.
2. **Commit ceremony** — this session's ~14 new/modified files are entangled with the pending Phase O.21 18k-file batch (`P1-PHASE-O21-COMMIT-PRESERVED-ARTIFACTS`); how to sequence the `/commit-with-provenance`.
3. **MPV3?** — pre-register the simultaneous-portfolio paradigm as a sibling hypothesis-of-record to MPV2 (switching), or keep the portfolio engine as infrastructure only.
4. **H060 per-session emission** — add the field + re-run (`P1-H060-PER-SESSION-LOGRET-EMIT`), vs an oos_returns-style back-fill if H060 emits a usable artifact.

## Follow-ups opened this session
Registered in CLAUDE.md Phase-P ledger entries. BLOCKING-before-real-verdict: `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` (H050 part closed), `P1-H060-PER-SESSION-LOGRET-EMIT`, `P1-MPV1-CALENDAR-ALIGNMENT`, `P1-MPV2-BH-SERIES-WIRE`, `P1-MPV2-FULL-SURVIVAL-VECTOR`, `P1-MPV2-JOINT-BOOTSTRAP-CONJUNCTIVE`, `P1-MPV2-REPROLOG-WIRE`, `P1-EARLY-WARNING-THRESHOLD-CALIBRATE`, `P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION`. Non-blocking: `P1-EARLY-WARNING-CSD-SURROGATE-NULL`, `P1-EARLY-WARNING-INCREMENTAL-UPDATE`, `P1-PORTFOLIO-NET-LONG-SHORT-V2`, `P1-PORTFOLIO-CONSTRAINED-JOINT-KELLY-V2`, `P1-PORTFOLIO-CONTINUOUS-SIGNAL-CONVICTION`, `P1-ADR-0020-LONG-SHORT-MULTI-ASSET-AMENDMENT`, `P1-MPV2-DATACLASS-RETURNS`, `P1-PAIRED-BOOTSTRAP-CI-SHARED-PRIMITIVE`, `P1-ADR-0029-{GLOSSARY,TEMPLATE,KPI-MEDIAN-HEADLINE-RETROACTIVE}-CASCADE`, `P1-MPV2-PRE-REGISTRATION` (done), `P1-SIZING-COMPUTE-POSITION-SIZE-TESTS-STALE` (pre-existing, unrelated).

## Next step
Regenerate the substrate (`OMP_NUM_THREADS=1 uv run python scripts/ingest.py --dataset vendor_legacy_1min --force` then `--dataset vendor_legacy_1min_roll_adjusted --force`), then add the `per_session_logret_aggregate` emission to the H060 orchestrator and re-run H055 + H060 + H062 to populate the remaining 3 arms' per-session arrays.

## Restoration procedure
- Branch: `main` (DIRTY — this session's artifacts + the Phase O.21 batch uncommitted). Repo: SKIE-Universe.
- Substrate: empty in this worktree; regenerate via `scripts/ingest.py` (deterministic; expected combined SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`). Raw CSVs intact at `~/datasets/vendor_skie_ninja_legacy/raw_1min/` (31 files).
- BLAS pinning for any orchestrator run: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` (ADR-0009).
- Validate the meta-allocation stack: `uv run pytest tests/unit/test_early_warning.py tests/unit/test_sizing_ergodicity.py tests/unit/test_mpv2_closed_loop.py tests/unit/test_portfolio.py -q` (expect 115 passed).
- Synthetic closed-loop smoke: `uv run python scripts/run_mpv2_closed_loop.py --synthetic`.
- H050 real per-session array is back-fillable now via `extract_arm_per_session({"kind":"parquet","run_dir":"artifacts/runs/H050/<run_id>","symbols":["ES","NQ"],"column":"gated_return"}, Path("."))`.
- Read first next session: this handoff → CLAUDE.md Phase-P entries → MPV2 design.md §11.2 + the Phase P buildout P-1/P-5 sections.
