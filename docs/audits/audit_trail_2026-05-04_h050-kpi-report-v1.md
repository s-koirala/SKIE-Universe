---
title: H050 KPI Report Card v1 + Forward-Projection Simulator + Stage Update — Audit-Remediate-Loop Trail
date: 2026-05-04
deliverables:
  - research/01_hypothesis_register/H050/H050_kpi_report_v1.md
  - scripts/simulate_h050_v1_10k_2026.py
  - research/01_hypothesis_register/H050/stage.md (appended row)
audit_pattern: audit-remediate-loop (3-round cap per ~/.claude/skills/audit-remediate-loop/SKILL.md)
auditors_round_1: [quant-auditor, literature-check, reproducibility-verifier]
parent_directive: User 2026-05-04 ("proceed with next steps 1-3 using the audit-remediate loop")
precedent: docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md (Path B leakage-clean)
---

# H050 KPI Report Card v1 — Audit-Remediate-Loop Trail

## Context

The H050 production walk-forward run completed 2026-05-04 02:40:59 CDT (run_id `31d23ecd8e3842dd8ebd5687ce9c91d5`; 28,225s wall-clock; both symbols ok). Per ADR-0013 §1 + §3, the next deliverable is the canonical KPI report card v1 (with the §3.1 mandatory Realized-OOS + Forward-Projection block) and the supporting forward-projection simulator. Plus a `kpi-report-emitted` row appended to `stage.md` per §1.1.

Round 1 produced the 3 deliverables; Round 2 audits via parallel triad; Round 3 verification.

## Round 1 — Production

Round-1 deliverables (commit pending):
1. [scripts/simulate_h050_v1_10k_2026.py](../../scripts/simulate_h050_v1_10k_2026.py) — adapted from H053 v4 reference simulator; bar-frequency translation of the §3.1 horizon (252 sessions × 390 RTH bars/session = 98,280 bars).
2. [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md) — first H050 KPI report card per ADR-0013 §3 + §3.1 canonical structure; frontmatter with all 7 SHA-pinned provenance hashes.
3. [research/01_hypothesis_register/H050/stage.md](../../research/01_hypothesis_register/H050/stage.md) — new row at `kpi-report-emitted` stage; cross-references the v1 KPI report card.

Simulator output: 5,000 bootstrap paths × 98,280 bars produced `logs/simulate_h050_10k_2026.json` (SHA `76d3a332...`) + `logs/simulate_h050_10k_2026.log` (SHA `1adc9a15...`); script SHA `3557e2d0...`.

## Round 2 — Parallel triad audit

3 parallel proper-isolated subagents (single message, multiple Agent calls).

### Round 2 — quant-auditor verdict: `block` (10 findings; 2 critical, 2 major, 6 minor)

agentId: ab6fc90d6a5bee958

| Finding | Severity | Focus | Issue (1-line) |
|---|---|---|---|
| F-Q-1 | **critical** | Cost-application contradiction | Report card declares "cost-free upper bounds" but orchestrator subtracts NT8 RTH cost per-bar before `oos_returns.parquet` write; design.md §1 line 30 binds net-of-cost. Narrative is wrong. |
| F-Q-2 | **critical** | Bar-vs-session horizon | ADR-0013 §3.1 binds horizon=252 sessions; sim uses 98,280 bars under iid bootstrap → projection collapses to non-stochastic limit (analytical: ES gated proj median ≈ 10,000·exp(μ·n) ≈ $6,166 vs reported $6,172.60); q01-q99 spread compresses to ~9% of equity vs realized 81% drawdown. |
| F-Q-3 | major | Regime persistence destruction | PW2004 selects `block_length=1.0` correctly on bar-level innovations (uncorrelated) but iid resampling destroys HMM regime-state dwell-time persistence captured in realized series. Bootstrap underestimates regime-conditional risk. |
| F-Q-4 | major | SPA parenthetical wording | "p=1.0 by ADR-0008 single-strategy convention" is wrong — p=1.0 because T_SPA=max(0,√n·d̄/ω)=0 when d̄<0; mechanical, not by convention. Annotation `spa-rejects` itself is consistent with project convention (matches H053 v3). |
| F-Q-5 | minor | Unconditional definition narrative | "zero-position bars on gated-out steps replaced with active position" wording conflates two zero-bar sources. |
| F-Q-6 | minor | Sizing convention precision | `reg_t ∈ {0,1}` is binary on/off, not "per-state position multiplier" wording from ADR-0013 §3.1.1 table. |
| F-Q-7 | minor | Dead-code n_draw | Computed unconditionally; only used in stationary-bootstrap branch (never taken). |
| F-Q-8 | minor | Lo 2002 annualization | Bar-level lag-1 ρ ≈ −0.03; Lo η(q) inflates \|annualized SR\| by ~3-4%; not corrected. |
| F-Q-9 | minor | JSON key naming | `projected_2026_98280bars` should be `projected_2026_252sessions` per ADR-0013 §3.1 horizon binding. |
| F-Q-10 | minor | Overconfident wording | "iid bootstrap is appropriate sampling method" understates the regime-persistence destruction concern. |

Quant residual risk: "After all 10 findings remediated, the v2 KPI report card will accurately label cost-aware results, project at 252-session granularity, and label SPA degenerate result correctly. Residual concerns: 1-min bar-frequency T_H050 statistical inference; LW2008 bandwidth=0 on ES suspicious; cost model itself is constant-tick prior pending paper-trade calibration."

### Round 2 — literature-check verdict: `proceed-with-remediation` (10 findings; 2 minor + 8 verified)

agentId: aa7e4fe889e734d1a

| Finding | Severity | Verdict | Claim | Disposition |
|---|---|---|---|---|
| F-L-1 | minor | VERIFIED | F-CONV-3/4/7 IDs cited | IDs are real but from `audit_trail_2026-05-03_adr-0013-realized-oos-projection-amendment.md`, NOT H053 Path B trail. Optional disambiguation. |
| F-L-2 | minor | OVERREACH | Andrews 1993 cited for "lower bound on regime-conditional realized max-DD" | Andrews 1993 develops in-sample detection tests for parameter instability, NOT a lower-bound theorem on bootstrap projection. Reframe to "instability is a real phenomenon flagged by Andrews 1993; bootstrap projection assumes stationarity." |
| F-L-3 | minor | VERIFIED | PW2004 + Politis-Romano 1994 | Both citations confirmed; DOIs correct. |
| F-L-4 | minor | VERIFIED | ADR-0008 single-strategy degenerate handling | Mechanical reduction T_SPA=max(0,√n·d̄/ω)=0 when d̄<0 → p=1.0 trivially. Report card claim is technically correct. |
| F-L-5 | minor | VERIFIED | Sortino & Price 1994 | Confirmed: J. Investing 3(3):59-64 doi:10.3905/joi.3.3.59. |
| F-L-6 | minor | VERIFIED | AFML §7.4 | Confirmed: §7.4 "A Solution: Purged K-Fold CV" with §7.4.1 "Purging the Training Set". |
| F-L-7 | minor | VERIFIED | rules/quant-project.md §Reporting | Confirmed: mandates Sharpe, Sortino, MaxDD, turnover, capacity estimate. |
| F-L-8 | minor | VERIFIED | design.md §8.a applicable: NO | Confirmed: BSS + reliability slope both applicable: NO for H050. |
| F-L-9 | minor | n/a | Bergmeir-Benitez 2012 + Tashman 2000 | Not cited in deliverables; claim moot. |
| F-L-10 | minor | VERIFIED | √(252×390) annualization convention | Mathematically correct; iid assumption acknowledged. |

### Round 2 — reproducibility-verifier verdict: `accept` (11 findings; 1 minor + 10 observations-verified)

agentId: a10c9609ab0ca0c27

All 7 frontmatter SHAs verified bit-exact:
- `git_head: d8c6acd1...` ✓ matches `git rev-parse HEAD`
- `substrate_dataset_checksum: b3ee230a...` ✓ matches ReproLog
- `sidecar_scientific_payload_sha256: c979c56a...` ✓ matches on-disk file
- `simulation_log_sha256: 1adc9a15...` ✓ matches `sha256sum`
- `simulation_script_sha256: 3557e2d0...` ✓ matches `sha256sum`
- `simulation_output_sha256: 76d3a332...` ✓ matches `sha256sum`
- `reprolog_model_hash: 6b6ed8fa...` ✓ matches ReproLog `model_hash`

Determinism confirmed by re-running simulator → byte-identical JSON output.

Single rng_seed = 20261420 (= H050.yaml `random_seed=20260420 + 1000`) constant across all (arm × symbol) cells per F-CONV-4 H053 audit.

| Finding | Severity | Notes |
|---|---|---|
| F-R-1 through F-R-9, F-R-11 | observations-verified | Frontmatter, simulator, stage.md, KPI structure all spec-compliant. |
| F-R-10 | minor | Dead-code modulo-wrap in stationary-bootstrap branch (not exercised by canonical run; same as F-Q-7). |

Repro residual risk: "Minimal. All 11 frontmatter SHA claims verified bit-exact. Determinism confirmed. ADR-0013 §1, §1.1, §3, §3.1, §3.1.1, §3.1.2, §4 compliance verified."

## Round 2 — Triage + remediation

Per `audit-remediate-loop` skill §3 ("Drop minor findings unless the user's task specifically invites polish. critical blocks progression; major is remediated this round."):

- **Critical (must remediate this round)**: F-Q-1, F-Q-2 (2 findings)
- **Major (must remediate this round)**: F-Q-3, F-Q-4 (2 findings)
- **Selected minors remediated inline (low cost / high readability)**: F-Q-5 (unconditional definition narrative), F-Q-6 (sizing convention precision), F-Q-10 (overconfident wording), F-L-1 (audit trail attribution), F-L-2 (Andrews framing)
- **Deferred to follow-ups**: F-Q-7 (dead code; harmless; tracked under existing `P1-FORWARD-PROJECTION-PRIMITIVE`), F-Q-8 (Lo annualization; new `P1-H050-LO-CORRECTED-ANNUALIZATION`), F-Q-9 (key naming; depends on F-Q-2 session-aggregation refactor under new `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION`)

### Round 2 — Remediation patches

All Round-2 critical + major + selected-minor findings remediated inline in `H050_kpi_report_v1.md` (no v2 increment because the underlying numerical claims didn't change — the fixes are narrative, citation framing, and added caveats per ADR-0013 §3 R-1-10 cosmetic-edit allowance for clarifications that don't alter informational content). Specifically:

- **F-Q-1 (cost-aware narrative)**: Caveat block + "Cost-aware status" subsection rewritten — "Cost model: APPLIED (cost-aware results, NOT cost-free upper bounds)" with cross-reference to design.md §1 line 30 net-of-cost binding + orchestrator line numbers. `P1-H050-COST-EMPIRICAL` renamed to `P1-H050-COST-CALIBRATION-EMPIRICAL` (scope clarified: about cost magnitude calibration from paper-trade logs, NOT about cost application).
- **F-Q-2 (horizon mismatch)**: Caveat block adds "Forward-projection horizon: bar-level, NOT session-level" item with explicit analytical-collapse demonstration (10,000·exp(μ·98280) ≈ reported median); methodological caveat that bar-level bootstrap UNDERSTATES forward variance and max-DD. New follow-up `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION` registered to track session-aggregation refactor (requires adding `ts_event` to `oos_returns.parquet`).
- **F-Q-3 (regime persistence)**: Caveat block adds "Bootstrap-destroys-regime-persistence" item with empirical mechanism explanation (proj median $6,173 vs realized $1,898 on ES gated). Co-mitigated under same `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION` follow-up (session-block bootstrap at 390-bar granularity preserves intra-day regime persistence).
- **F-Q-4 (SPA parenthetical)**: Annotation row reworded: `spa-rejects (m=1 degenerate per ADR-0008; T_SPA = max(0, √n·d̄/ω) = 0 because T_H050 < 0; p=1.0 means failure to reject H_0: E[d] ≤ 0)`. Surrounding paragraph text rewritten to make the mechanical-not-conventional nature of p=1.0 explicit; cross-reference H053 v3 KPI report card as the precedent for the project annotation convention.
- **F-Q-5 + F-Q-6 (definitions)**: Sharpe-vs-unconditional intro paragraph rewritten with the auditor's exact recommended text; sizing convention caveat clarified that `reg_t ∈ {0,1}` is binary on/off (not a continuous per-state multiplier).
- **F-L-1 (audit trail attribution)**: F-CONV-3/4/7 citation now names `audit_trail_2026-05-03_adr-0013-realized-oos-projection-amendment.md` explicitly.
- **F-L-2 (Andrews framing)**: Andrews 1993 citation reframed from "lower bound on regime-conditional realized max-DD per Andrews 1993" to "parameter instability is a real econometric phenomenon (Andrews 1993 develops in-sample detection tests with unknown change point); the bootstrap projection's understatement of realized risk is documented qualitatively here, not derived from Andrews 1993."
- **F-Q-10 (overconfident wording)**: §"Forward 1-year projection" intro paragraph now reads "bar-level iid bootstrap matches the PW2004 result on the level series, but does NOT preserve the HMM regime-state dwell-time persistence" + cross-reference to F-Q-3 caveat.

### Round 2 — Tests

The Round 2 remediations are documentation-only (no code changes to simulator or stage.md); no regression tests required. The simulator's existing test surface is unchanged (script SHA `3557e2d0...` stable; output JSON SHA `76d3a332...` stable; bit-exact reproducibility per F-R-2).

The KPI report card v1's frontmatter SHAs remain valid (the report card's `simulation_*_sha256` fields point to artifacts that didn't change). The KPI report card itself is not pinned by SHA in any frontmatter (the report card is the artifact-of-record, not a hashed dependency); narrative edits do not break any cross-reference.

## Round 3 — Verification

Round-3 verification: 2 parallel proper-isolated subagents (quant-auditor + literature-check). The reproducibility-verifier was not re-run because the Round-2 remediations were narrative-only (no SHA-pinned artifact changed; no code changes to simulator or stage.md schema; the Round-2 R1 repro audit's accept verdict therefore carries forward).

### Round 3 — quant-auditor verdict: `ACCEPT` (4/4 critical+major closures verified)

agentId: a5286ea9302ec3898

| Finding | Verdict | Evidence |
|---|---|---|
| F-Q-1 (cost-aware narrative) | ACCEPT | H050_kpi_report_v1.md:103 caveat block + :157 Cost-aware status subsection both declare cost-aware; cross-references design.md §1 line 30 + orchestrator line numbers; follow-up renamed to `P1-H050-COST-CALIBRATION-EMPIRICAL` in 3 places. Residual: §Versioning trigger list at :223 still cited deprecated `P1-H050-COST-EMPIRICAL` (now polish-fixed). |
| F-Q-2 (bar-vs-session horizon) | ACCEPT | H050_kpi_report_v1.md:105 caveat with verified analytical-collapse demonstration (10,000·exp(-4.92e-6 × 98,280) ≈ $6,166 matches reported $6,172.60 to <0.1%). New follow-up `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION` registered at :95, :105, :106. |
| F-Q-3 (regime persistence destruction) | ACCEPT | H050_kpi_report_v1.md:106 caveat with accurate empirical mechanism (proj median $6,173 vs realized $1,898 on ES gated, traceable to body tables :114 and :129). |
| F-Q-4 (SPA parenthetical) | ACCEPT | H050_kpi_report_v1.md:70-73 verbatim match; mechanical-not-conventional nature explicit; cross-reference to H053 v3 KPI report card for project annotation convention. |

Quant residual: "One non-load-bearing stale reference at line 223 §Versioning... non-load-bearing." (Polish-fixed in this commit.)

### Round 3 — literature-check verdict: `ACCEPT` (2/2 minor closures verified)

agentId: aa2f62e3ef37e0cda

| Finding | Verdict | Evidence |
|---|---|---|
| F-L-1 (audit trail attribution) | ACCEPT | Trail file `audit_trail_2026-05-03_adr-0013-realized-oos-projection-amendment.md` exists at the cited path; F-CONV-3 (line 37), F-CONV-4 (line 38), F-CONV-7 (line 41) IDs all real and substance-verified. |
| F-L-2 (Andrews 1993 framing) | ACCEPT | Reframed citation at H050_kpi_report_v1.md:107 reads accurately: "parameter instability is a real econometric phenomenon (the paper develops in-sample detection tests for parameter instability with unknown change point). Andrews 1993 does NOT provide a 'lower bound on bootstrap projection' theorem." Verified against IDEAS RePEc abstract + CrossRef DOI redirect. |

Lit-check residual: "None on the 2 citation findings."

### Round 3 — overall verdict: **ACCEPT**

All 4 critical+major Round-1 findings closed (F-Q-1, F-Q-2, F-Q-3, F-Q-4). All 2 selected-minor citation findings closed (F-L-1, F-L-2). Reproducibility-verified observations from Round-2 R1 (F-R-1 through F-R-11) carry forward unchanged. Polish residual (§Versioning trigger list referencing deprecated follow-up ID) fixed in the Round-3 audit-trail-emission commit.

The audit-remediate-loop exits at Round 3 per the 3-round cap with verdict ACCEPT.

The H050 KPI report card v1 + forward-projection simulator + stage.md row are now ready for commit. H050 transitions from `exploration-in-progress` → `kpi-report-emitted` per ADR-0013 §1. Next mandatory transition: `kpi-report-emitted` → `ninjascript-implemented` per ADR-0013 §5 (bridge-mediated NinjaScript C# implementation per ADR-0013 §1.2 since the HMM filter requires Python inference at decision time per ADR-0005). Tracked under `P1-H050-NINJASCRIPT-IMPL`.

## Residuals → follow-ups

| Follow-up ID | Severity | From | Description |
|---|---|---|---|
| `P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION` | major | F-Q-2 + F-Q-3 + F-Q-9 | Aggregate per-bar log returns to per-session log returns (sum within RTH session) → bootstrap 252 i.i.d. sessions; or session-block bootstrap at 390-bar granularity. Requires adding `ts_event` to `oos_returns.parquet` orchestrator schema. Triggers KPI report card v2 emission with both projections (bar + session) for cross-validation. |
| `P1-H050-COST-CALIBRATION-EMPIRICAL` (renamed from `P1-H050-COST-EMPIRICAL`) | major | F-Q-1 | Calibrate cost-magnitude prior from paper-trade logs once `TrivialSmokeTest` runs land per design.md §7. Scope clarified: cost is ALREADY applied per net-of-cost design.md §1 binding; this follow-up is about calibrating the constant-tick slippage prior magnitude. |
| `P1-H050-LO-CORRECTED-ANNUALIZATION` | minor | F-Q-8 | Compute Lo 2002 η(q) correction for bar-level annualization; re-report annualized Sharpe with the correction; estimate is bar-level lag-1 ρ ≈ −0.03 → \|annualized SR\| inflates by ~3-4%. |
| `P1-FORWARD-PROJECTION-PRIMITIVE` (existing) | minor | F-Q-7 / F-R-10 | Consolidate the projection helpers into `src/skie_ninja/inference/projection.py` per ADR-0013 §3.1.2. Replace `full_idx[:n_bars] % n_oos` modulo-wrap with re-draw-on-overflow. |
| `P1-H050-LW2008-BANDWIDTH-DIAGNOSE` | minor | quant residual risk | LW2008 bandwidth=0 on ES (vs 107 on NQ); inspect HAC variance estimation at 1-min frequency; may indicate degenerate variance estimate. |
| `P1-H050-NINJASCRIPT-IMPL` (existing) | major | next mandatory transition per ADR-0013 §5 | Bridge-mediated NinjaScript C# implementation per ADR-0013 §1.2 (HMM filter requires Python inference at decision time). |

## Cross-references

- ADR-0013: [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- ADR-0008 single-strategy degenerate: [docs/decisions/ADR-0008-spa-omega-method.md](../decisions/ADR-0008-spa-omega-method.md)
- ADR-0013 amendment audit trail (where F-CONV-* IDs originate): [audit_trail_2026-05-03_adr-0013-realized-oos-projection-amendment.md](audit_trail_2026-05-03_adr-0013-realized-oos-projection-amendment.md)
- H053 v4 reference simulator (the model for H050 v1): [scripts/simulate_h053_v4_10k_2026.py](../../scripts/simulate_h053_v4_10k_2026.py)
- H053 v3 reference KPI report card: [research/01_hypothesis_register/H053/H053_kpi_report_v3.md](../../research/01_hypothesis_register/H053/H053_kpi_report_v3.md)
- H050 design.md (frozen pre-reg; §1-§7 immutable): [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md)
- Path B leakage-clean precedent: [audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md)
- Production-run artifacts: `artifacts/runs/H050/31d23ecd8e3842dd8ebd5687ce9c91d5/`
- Production-run ReproLog: [logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json](../../logs/reproducibility/31d23ecd8e3842dd8ebd5687ce9c91d5.json)
- KPI report card v1: [research/01_hypothesis_register/H050/H050_kpi_report_v1.md](../../research/01_hypothesis_register/H050/H050_kpi_report_v1.md)
- Forward-projection simulator: [scripts/simulate_h050_v1_10k_2026.py](../../scripts/simulate_h050_v1_10k_2026.py)
- Stage tracker: [research/01_hypothesis_register/H050/stage.md](../../research/01_hypothesis_register/H050/stage.md)
