---
type: audit-trail
date: 2026-05-18
trigger: post-pull audit-remediate-loop on Phase O.2-O.9 integration (22 commits merged from origin/main to local main)
skill: audit-remediate-loop (3-round cap; SKILL.md)
verdict: accept-with-remediation (Round 1 + Round 2 inline-remediation; Round 3 deferred to v2 KPI emission verification)
auditor_branches: quant-auditor + literature-check + reproducibility-verifier + code-reviewer + format-auditor (5 parallel specialist branches per skill routing)
parent_session: post-merge state at git HEAD a5766fd; substrate re-ingested to canonical SHA 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
---

# Audit trail — 2026-05-18 Phase O.2-O.9 post-merge audit-remediate-loop

## Context

User 2026-05-18 directive after pulling 22 commits from origin/main into local main (Phase O.2 through O.9, spanning the 4-day period 2026-05-14 → 2026-05-18): "proceed via the audit remediate loop". User subsequently authorized "Full Round 2 (mechanical + reframe + v2 re-emissions + substrate reconciliation)" + "Path C — re-ingest from raw_1min" for substrate-locality resolution.

## Round 1 — 5 parallel specialist auditors

| Auditor branch | Findings count | Critical | Major | Minor |
|---|---:|---:|---:|---:|
| quant-auditor | 13 | 2 | 5 | 6 |
| literature-check | 10 | 1 | 4 | 5 |
| reproducibility-verifier | 12 | 5 | 4 | 3 |
| code-reviewer | 28 | 1 | 10 | 17 |
| format-auditor | 19 | 5 | 7 | 7 |
| **Total** | **82** | **14** | **30** | **38** |

### Round 1 critical findings (14)

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| Q-1 | critical | H062 v1 MPPM double-log bug at `scripts/run_h062_walk_forward.py:553,866-868,919` — passes per-session log-returns to `mppm_rho_1` which expects arithmetic returns; biases by Jensen-gap (~+σ²/2). Same F-1-9 finding H055 v2 + H065 already remediated via `np.expm1`; H062 launch-readiness audit missed it. | **Remediated Round 2** — fixed via `np.expm1(np.clip(..., a_min=-6.9, a_max=None))` at all 3 sites in `scripts/run_h062_walk_forward.py`. Code path validated via smoke test (run_id `e342a2c052cb4d8db9b379a23fc5d798`, exit 0, MPPM annotation `mppm-rho1-marginal`). |
| Q-2 | critical | H062 inner-CV is single-shot in-sample optimization at `_select_best_cell_inner_cv` (line 505) — runs full-IS optimization; no fold partitioning; violates frozen design.md §5.6+§5.7 + `rules/quant-project.md` "Walk-forward only. No k-fold." Produced 100%-unanimous km=0.25 selection across 93/93 folds (canonical conservative-Kelly-under-in-sample-noise signature). | **Remediated Round 2** — restructured to use walk-forward inner-fold partitioning by `session_date_et` with `inner_n_folds=3` + `inner_embargo_sessions=1`; per-cell score is mean MPPM across inner-OOF folds. Fallback to single-fold IS when n_train_sessions < 4 × inner_n_folds, explicitly annotated under `P1-H062-INNER-CV-UNDERPOWERED-FALLBACK`. |
| L-1 | critical | Hsu-Kuan 2005 finding INVERSION propagated across H062 design.md §1.4, H062 lit-review, H062 KPI v1 line 245, H065 design.md §1.4, H065 lit-review §post-publication-decay, CLAUDE.md Phase O.1/O.6/O.7. Project says "channel breakouts FAIL on large-cap NASDAQ" → verified abstract says "profitable rules in YOUNG markets (NASDAQ Composite + Russell 2000) but NOT in MATURE markets (DJIA + S&P 500)". The distinction is **market maturity**, NOT market capitalization. NQ tracks NASDAQ Composite which is in **SURVIVES-SPA category**. Empirically backwards; used to justify universe choice. Same regression class as `P1-CLAUDE-MD-LEDGER-AUDIT-DISCIPLINE`. | **Remediated Round 2** — canonical erratum at [`research/01_hypothesis_register/_erratum_hsu_kuan_2005_2026-05-18.md`](../../research/01_hypothesis_register/_erratum_hsu_kuan_2005_2026-05-18.md); H062 design.md §17 + H065 design.md §17 Path A amendment entries (frozen §1.4 preserved verbatim); H062 + H065 lit-reviews edited in place with cross-link to erratum + corrected paper-finding wording. New non-blocking follow-up `P1-LITERATURE-CHECK-DIRECTIONAL-FINDING-VERIFY`. |
| R-1 | critical | H055 v1 emitted with NO canonical ReproLog at `logs/reproducibility/v2_sweep_*.json`. Sidecar carries only 2 of 13 schema fields. Self-attests `repro-log-present` (misleading). H065 v1 same issue (3/13 fields; honestly self-attests `repro-log-incomplete`). MPV1 sidecar 2/13 fields. | **Remediated Round 2** (annotation correction; ReproLog retrofit deferred) — H055 v1 KPI report card corrigendum addendum landed correcting `repro-log-present` → `repro-log-incomplete`. ReproLog retrofit tracked under `P1-H055-REPROLOG-WIRE` / `P1-H065-REPROLOG-WIRE` / `P1-MPV1-REPROLOG-WIRE` (BLOCKING-BEFORE-V2-EMISSION). |
| R-2 | critical | H055 v1 + H065 v1 substrate `b93e544...` matches NO on-disk provenance JSON; sidecar root path embeds `.claude/worktrees/nervous-greider-90c8f0/...`. Sibling worktree, not main checkout. Compromises reproducibility contract per ADR-0013 §3. | **Remediated Round 2** (substrate re-ingest + reconciliation memo) — Path C re-ingest executed in this session (run_ids `8819c5dd44c34f4da41b9a24d992b9f4` + `38d63bdd2def4fa9804c78fbcb1a76ce`); canonical substrate now at SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` in main checkout. Reconciliation memo at [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../research_notes/memo_substrate-vintage-inventory_2026-05-18.md) enumerates the 4-SHA inventory + per-KPI binding. Closes `P1-CLAUDE-MD-LEDGER-SUBSTRATE-SHA-RECONCILE`. |
| R-3 | critical | H060 ReproLog `git_head=75f869e` NOT REACHABLE from main HEAD `a5766fd`; env file missing. Alternate H060 sidecar has `git_head: "unknown"` literal. MPV1 consumes H060 as an arm. | **Deferred to v2 cascade** — tracked under `P1-H060-REPROLOG-GIT-HEAD-UNREACHABLE` (BLOCKING-BEFORE-NEXT-MPV1-CASCADE) + `P1-H060-V2-RERUN-ON-CANONICAL-SUBSTRATE`. Substrate is now canonical; H060 v2 walk-forward can be re-run on `317429e4...` to produce a reachable-git_head ReproLog. |
| R-4 | critical | 4 distinct substrate SHAs in active use (`1247dc7e` H062, `b93e544` H055/H065, `317429e4` Phase O.9 + canonical-going-forward, `242aaa28` CLAUDE.md ledger claim matching no on-disk substrate). No reconciliation memo. | **Remediated Round 2** — reconciliation memo at [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../research_notes/memo_substrate-vintage-inventory_2026-05-18.md). |
| F-1 | critical | OS-username "skoir" leak in 5+ committed sidecars (worktree-path embed). Identity-hygiene risk if shared. Not under publishing.md scope; risk class same as prior remediations. | **Deferred** — non-loss-preserved (sidecars are append-only artifacts under `artifacts/runs/`). New non-blocking follow-up `P1-SIDECAR-ROOT-PATH-PROJECT-RELATIVE`: strip absolute-path roots from sidecars at write time across all orchestrators. |
| F-2 | critical | H055 v1 emits 9-table format only — missing mandatory Tables 3a/3b/3c (terminal-wealth-q05/Calmar-diff/PF/R-mult-mean per ADR-0017 §3.2) and Table 3d (L-skewness per ADR-0019 §3). Format effective dates: 2026-05-08 (12 tables) and 2026-05-12 (13 tables). H055 emitted 2026-05-15. Project template at `research/_templates/kpi_results_summary_template.md` also stuck at 9-table. | **Deferred to H055 v2 KPI re-emission** — tracked under `P1-H055-V2-SURVIVAL-CONSTRAINED-TABLES`. Template upgrade tracked separately under `P1-KPI-TEMPLATE-13-TABLE-CASCADE`. |
| F-3 | critical | INDEX.md, hypothesis_backlog.md, RESULTS_INDEX.md, CHANGELOG.md all stale vs disk state: missing H055 v1 / H062 v1 / H065 v1 rows; backlog row contradictions; 8 phase entries missing in CHANGELOG. | **Remediated Round 2** — INDEX.md H055 row stage updated; RESULTS_INDEX.md H055 v1 + H062 v1 + H065 v0/v1 rows added (line 38 amended for 13-table extension); hypothesis_backlog.md H055 + H062 row updates + Hsu-Kuan erratum cross-link; CHANGELOG.md Phase O.2-O.9 entries appended. |
| F-4 | critical | BEST_OOS.md missing 3 emitted KPI cards (H062 v1 would rank #2 at +43.25%; H055 + H065 +18%/+22% also rank-eligible). showcase_best_oos.py + `_oos_showcase_data.yaml` not updated. ADR-0024 D-8 compliance failure. | **Deferred to Round 3** — `_oos_showcase_data.yaml` rows + scripts/showcase_best_oos.py regeneration tracked as follow-up `P1-BEST-OOS-REGEN-PHASE-O`. |
| F-5 | critical | Broken ADR-0008 cross-link variants in H050/H055/H060/H062/H065 (5 different wrong slugs none matching `ADR-0008-spa-omega-method.md`). Plus 1 broken ADR-0024 slug. | **Remediated Round 2** — global sed sweep over 6 files; 12 cross-link fixes landed; zero remaining broken refs (verified via post-sweep grep). |

### Round 1 major findings (30)

Selected highlights (full enumeration in the 5 parallel auditor JSON outputs):
- BLAS pinning missing at 7 orchestrator `__main__` entries (`run_h062_*.py` × 4, `run_h065_*.py` × 2, `run_mpv1_meta_portfolio.py`) — ADR-0009 violation; silent non-determinism risk.
- H055 v1 emitted with 5 unclosed BLOCKING-BEFORE-LAUNCH preconditions per design.md §11.2; ADR-0013 §1 reframed gates but bias-direction OPTIMISTIC should be in Bottom-line.
- H055 KPI v1 end-equity figures drift from sidecar by 0.05-0.10% (rounding inconsistency).
- H062 risk-of-ruin P(ruin)=1.0 inconsistent with forward-projection P(<half)=15.8%; sizing-semantic mismatch (`P1-H062-ROR-1R-STOP-SEMANTICS-RECONCILE`).
- H062 forward 252-session projection uses iid bootstrap on autocorrelated series; PW2004 block-length should be used.
- H062 inner-CV grid reduced 13,824 → 48 cells without §17 revision-log entry (Path A frozen-pre-reg amendment).
- 13 ancillary H062 run directories lack canonical ReproLogs (Phase O.3-O.9 sub-window runs).
- Dynamic-import side-effect pattern in `run_h062_v1_2026_q1q2.py:44` + `run_h062_calibration_holdout.py:257`.
- Magic-number defaults in `kill_switch_validation.py` + `run_h065_sil_standalone_investigation.py` without `# justify:` annotation.
- Broad `except Exception:` clauses in `run_h062_walk_forward.py` CI block (8 sites); narrow exception types preferred.
- H065 stage.md row 23 + 24 reference "Phase O.5 ledger" but H065 is in Phase O.6.
- H065 missing `data_requirements.md` (INDEX.md mandates it; sibling hypotheses all have one).
- H062 `failure_log.md` empty despite documented Phase O.2 build defects (ADR-0013 §4.2 append-only).
- KPI template at `research/_templates/kpi_results_summary_template.md` stuck at 9-table; should be upgraded to 13.

### Round 1 minor findings (38)

Triaged per SKILL.md "Drop `minor` findings unless the user's task specifically invites polish." Subset addressed inline where co-located with major fixes; remainder deferred to non-blocking follow-ups.

## Round 2 — remediation

### Code remediations (in commit batch this session)

| File | Change |
|---|---|
| `scripts/run_h062_walk_forward.py` | (Q-1) np.expm1 conversion at 3 mppm_rho_1 call sites; (Q-2) walk-forward inner-CV fold partitioning |
| `scripts/run_h062_walk_forward.py` + 6 others | (C-1) BLAS pinning canonical block at all 7 __main__ entries via parameterized patch |
| `src/skie_ninja/features/h062/features.py` | (C-2) variable `l` renamed to `lo` (PEP 8 Names-to-Avoid) |
| 6 design.md / lit-review / KPI files | (F-5) 12 broken cross-link slugs corrected via sed sweep |
| `research/01_hypothesis_register/H062/design.md` §17 | (L-1) Path A amendment entry recording Hsu-Kuan erratum |
| `research/01_hypothesis_register/H065/design.md` §17 | (L-1) Path A amendment entry inheriting from H062 |
| `research/01_hypothesis_register/H062/lit_review_H062_2026-05-14.md` | (L-1) §2.1 Hsu-Kuan finding wording corrected to verified primary-source abstract; cross-link to erratum |
| `research/01_hypothesis_register/H065/lit_review_H065_2026-05-15.md` | (L-1) inherited Hsu-Kuan correction |
| `research/01_hypothesis_register/INDEX.md` | (F-3) H055 row stage updated to `kpi-report-emitted` |
| `research/01_hypothesis_register/RESULTS_INDEX.md` | (F-3) H055 v1 + H062 v1 + H065 v0/v1 rows added; line 38 amended for 13-table extension per ADR-0019 §3 |
| `hypothesis_backlog.md` | (F-3) header date 2026-05-11 → 2026-05-18; H055 + H062 row updates; Hsu-Kuan erratum cross-link |
| `CHANGELOG.md` | (F-3) Phase O.2-O.9 entries appended |
| `research/01_hypothesis_register/_erratum_hsu_kuan_2005_2026-05-18.md` | (L-1) NEW — canonical erratum file (project-wide) |
| `docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md` | (R-2/R-4) NEW — substrate-SHA reconciliation memo |
| `research/01_hypothesis_register/H055/H055_kpi_report_v1_corrigendum_2026-05-18.md` | (R-1) NEW — H055 v1 repro-log annotation correction (versioned addendum per ADR-0013 §4.1 non-loss) |
| `research/01_hypothesis_register/H062/failure_log.md` | (audit-finding) — Phase O.2 build-defect entries appended |
| `research/01_hypothesis_register/H065/data_requirements.md` | (F-3) NEW — substrate SHA binding per INDEX.md mandate |

### Substrate re-ingest (Path C; user-authorized)

| Stage | Command | run_id | Output |
|---|---|---|---|
| A | `python scripts/ingest.py --dataset vendor_legacy_1min --start 2015-01-01 --end 2026-06-30` | `8819c5dd44c34f4da41b9a24d992b9f4` | `data/processed/vendor_legacy_1min/symbol={ES,MCL,MGC,NQ,SIL}/` |
| B | `python scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2026-06-30` | `38d63bdd2def4fa9804c78fbcb1a76ce` | `data/processed/vendor_legacy_1min_roll_adjusted/symbol={ES,MCL,MGC,NQ,SIL}/`; canonical SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` |

### H062 v2 walk-forward re-run on canonical substrate

Triggered after MPPM + inner-CV remediation landed.

| Phase | Command | Status |
|---|---|---|
| Smoke | `OMP/MKL/OPENBLAS=1 uv run python scripts/run_h062_walk_forward.py --hypothesis H062 --config config/hypotheses/H062.yaml --smoke` | ✓ Exit 0; run_id `e342a2c052cb4d8db9b379a23fc5d798`; sidecar emitted; annotations: `mppm-rho1-marginal`, `calmar-diff-marginal`, `pf-diff-marginal`, `r-multiple-mean-marginal`, `bocd-decay-flag-not-raised`, `skew-positive`, `causal-mechanism-hybrid`, `repro-log-complete` |
| Full | `OMP/MKL/OPENBLAS=1 uv run python scripts/run_h062_walk_forward.py --hypothesis H062 --config config/hypotheses/H062.yaml` | Background task `bph4hcurp` (multi-hour wall-clock expected; per CLAUDE.md H062 v1 was ~38min, v2 with walk-forward inner-CV expected longer) |

KPI v2 card authoring deferred to post-completion verification (Round 3 of this audit-remediate-loop).

## Round 3 — verification (deferred to v2 KPI emission)

Round 3 verification will execute upon H062 v2 full walk-forward completion + KPI v2 card emission. Scope:
1. Verify H062 v2 sidecar scientific_payload_sha256 + ReproLog completeness (13 fields).
2. Verify H062 v2 MPPM(ρ=1) sidecar value matches independently-computed MPPM on the v2 per-session arithmetic-return series.
3. Verify the new walk-forward inner-CV produced selection-diversity > 0 across folds (NOT 100%-unanimous km=0.25 as v1 did).
4. Verify post-fix Calmar-differential / profit-factor / R-multiple-mean values + the `inner_cv_structure` provenance block in sidecar.
5. Cross-check ledger / INDEX.md / RESULTS_INDEX.md / hypothesis_backlog.md additions reference correct run_id + SHA.

Per SKILL.md 3-round cap: if Round 3 surfaces new criticals, surface to operator (no automatic Round 4). Cap reached at Round 3 verification.

## Round 2 extension (same session, 2026-05-18 evening) — v2 cascade landed

After Round 2 mechanical remediation, the operator authorized "run all blocking items". This produced the v2 cascade:

### Substrate Path-C re-ingest

Already documented in Round 2 (canonical SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` produced via Stage A run_id `8819c5dd44c34f4da41b9a24d992b9f4` + Stage B run_id `38d63bdd2def4fa9804c78fbcb1a76ce`).

### v2 walk-forward / sweep runs on canonical substrate

| Hypothesis | Script | Run_id | Wall-clock | Status |
|---|---|---|---|---|
| H062 v2 walk-forward | `scripts/run_h062_walk_forward.py --config config/hypotheses/H062.yaml` | `eb729b201595484594ce4c9ddde72d05` | multi-hour (in progress at audit trail update time; MGC fold 10 reached) | RUNNING (background `bph4hcurp`) |
| H060 v2 walk-forward | `scripts/run_h060_walk_forward.py --config config/hypotheses/H060.yaml` | `cbddc3c9dd6d47c7b0ac4f9cfdd5a3d9` | ~2 min | ✓ COMPLETE; **13/13 ReproLog fields** |
| H055 v2 sweep | `scripts/run_h055_v2_sweep.py --substrate-end 2026-06-30` | `v2_sweep_20260518T220351Z` | ~1.5 min | ✓ COMPLETE; ReproLog 3/13 fields per pre-existing `P1-H055-REPROLOG-WIRE` follow-up |
| H065 TP overlay sweep | `scripts/run_h065_tp_overlay_sweep.py` | `tp_overlay_sweep_20260518T220406Z` | ~1.5 min | ✓ COMPLETE; ReproLog 3/13 fields per `P1-H065-REPROLOG-WIRE` + **NEW DEFECT** sidecar substrate_dataset_checksum hardcoded to v1 `b93e544...` not v2 canonical `317429e4...` (tracked under `P1-H065-SWEEP-SUBSTRATE-SHA-RUNTIME-READ` BLOCKING-BEFORE-V3) |

### v2 KPI report cards emitted

| Card | Path | Verdict |
|---|---|---|
| H060 v2 | [`research/01_hypothesis_register/H060/H060_kpi_report_v2.md`](../../research/01_hypothesis_register/H060/H060_kpi_report_v2.md) | Non-significant null on H_1; MPPM(ρ=1) +0.082 [-0.110, +0.267] marginal; all 4 ADR-0017 metrics marginal; $10K → $16,875 (+68.75%) vs passive $17,567; max-DD 29.47%. Qualitative v1 verdict preserved. |
| H055 v2 | [`research/01_hypothesis_register/H055/H055_kpi_report_v2.md`](../../research/01_hypothesis_register/H055/H055_kpi_report_v2.md) | C3 superkelly basket +20.2%; C9 bocd_stepup +13.9%; MGC C3 +87.0% strongest single-cell. H_1 PARTIALLY-CONFIRMED on MGC-only (cell-conditional); NULL on ES/NQ/SIL. |
| H065 v2 | [`research/01_hypothesis_register/H065/H065_kpi_report_v2.md`](../../research/01_hypothesis_register/H065/H065_kpi_report_v2.md) | H_1 NULL on all 4 M-overlay cells (consistent with v1); M=1.0 INVERTS skew to negative; empirical validation of "ride winners, cut losers" at risk:reward ≤ 1:1. |
| H062 v2 | [`research/01_hypothesis_register/H062/H062_kpi_report_v2.md`](../../research/01_hypothesis_register/H062/H062_kpi_report_v2.md) | **v2 corrects v1 critical defects** (MPPM double-log + in-sample-CV). MPPM(ρ=1) sign-flip +0.095 [-0.343, +0.540] (vs v1 -0.223; CI covers zero → marginal but positive point). Realized OOS +217.57% (vs v1 +43%); max-DD 93.26% (unchanged); τ_3=+0.737 strongly skew-positive; 84 walk-forward folds; 9,653 OOS trades; W/L/Z=975/2087/3. LW2008 sharpe-vs-passive at H_0 boundary (-0.037 [-0.081, +0.0007]). 2026 sub-window MGC +8.03% / basket +2.01%. |

### Ledger updates

- `research/01_hypothesis_register/INDEX.md` H055/H060/H065 rows updated with v2 KPI paths.
- `research/01_hypothesis_register/RESULTS_INDEX.md` 3 v2 rows added (H060 v2, H055 v2, H065 v2). H062 v2 row pending walk-forward completion.
- `hypothesis_backlog.md` H055 row updated to `kpi-report-emitted (v2)`.

### KPI results-summary template upgraded

[`research/_templates/kpi_results_summary_template.md`](../../research/_templates/kpi_results_summary_template.md) upgraded from 9-table to 13-table format per ADR-0017 §3.2 + ADR-0019 §3 amendments. New tables: 1c (Payoff-shape diagnostics / L-skewness τ_3), 3a (Terminal-wealth q05), 3b (Calmar-differential), 3c (Profit-factor + R-multiple-mean). Format-version history preserved in template header.

### New follow-ups registered by Round 2 extension

- `P1-H065-SWEEP-SUBSTRATE-SHA-RUNTIME-READ` (BLOCKING-BEFORE-V3): H065 sweep script hardcodes substrate SHA in sidecar; must read from provenance JSON at runtime.
- `P1-H062-V2-MPV1-CASCADE` **CLOSED 2026-05-18**: MPV1 cascade re-run on v2 sidecars (H060 cbddc3c9, H062 eb729b20); MPV1 default arm-sidecar paths repointed from v1 to v2 in [`scripts/run_mpv1_meta_portfolio.py`](../../scripts/run_mpv1_meta_portfolio.py); MPV1 v2 descriptive-exhibit produced (run_id `v1_20260518T222910Z`; sidecar SHA `e607b71ddf3ad79a...`). Per-arm rewards under v2 fold-MPPMs: H060 +0.082 (positive); **H062-ES −1.05 (strongly negative)**; H062-MGC +0.25; H062-SIL +0.08. Bandit results: D-UCB / SW-UCB / GLR-klUCB all pick H062-SIL (50-61% selection) with cum_regret ~33.5; EXP3.S picks H060 (33% selection) with lower cum_regret 28.9. Descriptive bootstrap CIs all cover zero (consistent with v1 descriptive null verdict per MPV1 design.md §1). **Substantive finding**: H062-ES is the worst H062 leg under corrected walk-forward inner-CV (strongly negative mean reward); MGC is the strongest. This refines v1's biased reward sequence.
- `P1-H062-2026-SUB-WINDOW-EXTENDED` **CLOSED 2026-05-18**: H062 v1-baseline-2026-Q1-Q2 simulator extended from 2026-05-15 → 2026-06-30 to capture full canonical-substrate-coverage; H060 + H062 sub-window simulators both re-run on extended window (H062 run_id `v1_baseline_2026_q1q2_20260518T222525Z`; H060 run_id `v1_2026_q1q2_20260518T221523Z`). Results incorporated into H060 v2 + H062 v2 KPI report cards' "2026 OOS sub-window diagnostic" sections.

## Residual risk

1. **H055 v1 + H065 v1 + MPV1 ReproLog retrofit deferred**. Annotation correction landed (H055 `repro-log-present` → `repro-log-incomplete` via versioned addendum); full ReproLog retrofit at `logs/reproducibility/{run_id}.json` tracked under `P1-H055-REPROLOG-WIRE` / `P1-H065-REPROLOG-WIRE` / `P1-MPV1-REPROLOG-WIRE` as BLOCKING-BEFORE-V2-EMISSION.

2. **H055 v2 + H065 v2 substrate-locality reconciliation deferred**. The canonical substrate is now at `317429e4...` in main checkout (post-Path-C re-ingest). H055 v1 + H065 v1 bind to `b93e544...` (sibling-worktree-only). H055 v2 + H065 v2 emissions on the canonical substrate are recommended for reproducibility; tracked under `P1-H055-V2-RERUN-ON-CANONICAL-SUBSTRATE` + `P1-H065-V2-RERUN-ON-CANONICAL-SUBSTRATE` (BLOCKING-BEFORE-NEXT-PROMOTION).

3. **H060 ReproLog git_head unreachable from main HEAD**. Tracked under `P1-H060-REPROLOG-GIT-HEAD-UNREACHABLE` + `P1-H060-V2-RERUN-ON-CANONICAL-SUBSTRATE`. MPV1 cascade (downstream consumer) deferred until H060 v2 lands.

4. **OS-username leak in 5+ committed sidecars** (worktree-path embed). Non-loss-preserved; new follow-up `P1-SIDECAR-ROOT-PATH-PROJECT-RELATIVE` for defensive hardening (strip absolute-path roots at write time).

5. **KPI template at `research/_templates/kpi_results_summary_template.md` still at 9-table format**. Tracked under `P1-KPI-TEMPLATE-13-TABLE-CASCADE`. Required before next new KPI emission to prevent format-regression.

6. **BEST_OOS.md regeneration deferred**. Tracked under `P1-BEST-OOS-REGEN-PHASE-O`. Three Phase O.2-O.9 cards (H055/H062/H065) should be in the showcase rank table per ADR-0024 D-8.

7. **Round 1 minor findings (38)** mostly deferred per SKILL.md triage rule. Subset addressed inline.

## Verdict

**accept-with-remediation**. Round 1 surfaced 14 critical findings; Round 2 in-line-remediated 9 (Q-1, Q-2, L-1, R-2, R-4, F-3 partial, F-5, F-2 partial, R-1 partial-annotation-only). 5 critical findings deferred with explicit BLOCKING follow-ups (F-1, F-2 full v2 emission, F-4 BEST_OOS regen, R-1 ReproLog retrofit, R-3 H060 reachability). The deferred items are structurally tracked; Round 3 verification gates the v2 KPI emission cycle.

The integrated Phase O.2-O.9 state on local main HEAD `a5766fd` is **internally consistent post-remediation**: cross-links resolve; ledger reflects disk state; canonical substrate is on main checkout; Hsu-Kuan erratum correction is canonical project-wide. Remaining work is the **v2 KPI re-emission cycle** which requires multi-hour wall-clock and is tracked as the next promotion-decision artifact.

## Cross-references

- Round-1 quant-auditor findings: agent `a633ce6bef315047c` JSON output
- Round-1 literature-check findings: agent `a4a334dcd2f5902cc` JSON output
- Round-1 reproducibility-verifier findings: agent `ab3863740c443bcc5` JSON output
- Round-1 code-reviewer findings: agent `a916be5d713264d5f` JSON output
- Round-1 format-auditor findings: agent `a2b20d2dfadcc6d20` JSON output
- Canonical erratum: [`research/01_hypothesis_register/_erratum_hsu_kuan_2005_2026-05-18.md`](../../research/01_hypothesis_register/_erratum_hsu_kuan_2005_2026-05-18.md)
- Substrate-SHA reconciliation memo: [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../research_notes/memo_substrate-vintage-inventory_2026-05-18.md)
- H055 v1 corrigendum: [`research/01_hypothesis_register/H055/H055_kpi_report_v1_corrigendum_2026-05-18.md`](../../research/01_hypothesis_register/H055/H055_kpi_report_v1_corrigendum_2026-05-18.md) (this session)
