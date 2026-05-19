# Audit Trail — H068 v1 Walk-Forward Post-Run Gate

**Date**: 2026-05-19
**Hypothesis**: H068 (cost-light Donchian channel-breakout on ES standalone with sub-1-tick slip empirical sensitivity sweep)
**Phase**: O.18 — first H068 v1 production walk-forward + KPI v1 emission
**Audit-remediate-loop discipline**: ADR-0011 §"Post-run audit gate" mandatory parallel R1 with quant-auditor + reproducibility-verifier + format-auditor branches
**Round-cap**: 3 rounds per SKILL.md; this audit trail records R1 only (R2-3 verification deferred to first-usage cycle / paper-trade-evaluated stage transition)
**Verdict**: `accept-with-residuals`

## Round-1 in-loop audit (parallel triad)

### R1 Branch A — quant-auditor

**Audit surface**: scientific_payload SHA `a5bce59880e0dd5d824a5b4fd6d7ef7db1df80f05599dc34744f0d26b59ca714`; sidecar `artifacts/runs/H068/957643d6cb8441e29d888482447ead6e/sidecar.json`; v1 KPI report card `research/01_hypothesis_register/H068/H068_kpi_report_v1.md`; cell-grid integrity; H_1 conjunctive verdict mechanics.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| Q-1-1 | major | The sweep code computes `per_trade_gross_edge_bps_eq` from A0 zero-cost (`total_gross_pnl / n_trades / starting_equity * 10000`). For the parent H065 v2 M_inf_h062_v1_fixed-ES cell at sensitivity_mult=1.0 baseline, the addendum §3 anchor value is 36.855 bps-of-equity; H068 v1 sidecar reports **38.16** bps-of-equity (deviation +3.6%). The deviation is consistent with substrate vintage difference (parent H065 v2 used pre-Phase-O.10 substrate; H068 v1 uses canonical post-Phase-O.10 `317429e4...`) — both substrates contain ES + roll-adjusted derivative; the small numerical drift is within expected substrate-vintage envelope. | ACCEPTED; documented in §"Substrate provenance" of v1 KPI card. Not load-bearing for H_1 conjunctive verdict (which uses realized OOS numbers verbatim from the substrate the sweep consumed, not the parent cell's stale numbers). |
| Q-1-2 | major | Kelly-multiplier {0.5, 1.0, 1.5, 2.0, 2.5} cells produce numerically-identical per-trade outcomes to Kelly=0.25 cell at v1 single-unit-entry sizing. The Kelly-multiplier hyperparameter is documented in design.md §5.3 + Table 8 of the v1 KPI card as "hyperparameter at inner-CV only — preserved from H062 v1 + H065 v2 modal cell behavior." Auditor verified by inspecting sweep code lines `target_dollar_risk = eq_for_sizing * 0.01` + `size = floor(min(target/(k_atr×ATR×multiplier), cap))` — Kelly_multiplier is NOT in the sizing path at v1. | ACCEPTED; documented as known property (parent-cell-preservation per ADR-0027 §D-4 single-axis discipline). Multi-lot Kelly-scaling deferred to v2 per `P1-H068-V2-N-LOT-SCALING-PATH-DELAYED`. |
| Q-1-3 | major | The breakeven-ratio annotation `cost-friction-dominated-edge-{present, absent}` per ADR-0028 §D-2 trigger semantics requires (A0 ROI > 0 AND A1 ROI < 0 AND ratio ≥ 2) for `present`. The sweep computes ratio = 3.65 at slip=0.25 and 2.28 at slip=0.5 (BOTH crossing ≥ 2 threshold) BUT A1 ROI is positive on every cell → annotation correctly resolves to `absent` per ADR-0028 §D-2 strict reading. This is structurally correct but operator-readable interpretation may be confusing: the `absent` annotation does NOT mean cost-reduction failed, it means the cost-arm sign-flip threshold was not met. | ACCEPTED with explicit clarification in v1 KPI card Table 8 "cost-friction-breakeven-ratio-crosses-2-at-slip-0.5-and-0.25" annotation row + the §"Pre-empirical ratio prediction VERIFIED" narrative in the Bottom-line prose. New non-blocking follow-up registered: `P1-ADR-0028-EDGE-ANNOTATION-OPERATOR-READABLE-CLARIFY` (consider tightening the ADR-0028 §D-2 trigger documentation to explicitly state that `absent` is the only valid annotation when both A0 + A1 produce positive ROI; the `present` flavor requires the A0 → A1 sign-flip-with-ratio-≥-2 conjunctive). |
| Q-1-4 | major | n_trades=108 is at the design.md §1.4 statistical-power caveat boundary. The bootstrap CIs on MPPM(ρ=1) + R-mean + L-skewness all use the same n=108 sample (per-trade R-multiples) or n ≈ 90-100 per-session-aggregated (per-session log returns); the MPPM CI width [-1.30, +3.05] at the load-bearing slip=0.5 cell spans 4.35 units around a +0.56 point estimate — the H_1 conjunctive criterion (b) cannot clear at this sample size regardless of slip refinement. This is the structural reason H_1 fails. | ACCEPTED; documented in v1 KPI card Bottom-line + §"Performance KPIs" Table 3 + §1.4 caveat preservation from design.md. The reverse-causal sensitivity question (how many trades would be needed for MPPM CI to clear zero positively at the slip=0.5 point estimate +0.56?) tracked under new non-blocking follow-up `P1-H068-MPPM-CI-WIDTH-SAMPLE-SIZE-SOLVER`. |
| Q-1-5 | minor | Sub-window 2026-04-01 → 2026-05-15 produces 0 ES trades across ALL 36 cells. This is consistent with H062 v1 + H065 v2 sub-window observations (per CLAUDE.md Phase O.5 + Phase O.7 ledger entries) — the post-2026-04-01 ES microstructure regime has no eligible channel-break + first-fire + ID_1 trend-gate events on the 5-min cadence. ADR-0026 §D-1 component 2 mandatory reporting is satisfied by emitting 0% / 0 trades. | ACCEPTED; documented in v1 KPI card §0 Component 2 row + Bottom-line. |
| Q-1-6 | minor | K-6 trigger counts vary with slip (3 at slip ∈ {0.25, 0.5}; 6 at slip=1.0). Mechanism: tighter cost drag → faster drawdown accumulation → K-6 −2%-of-session-start threshold fires more often → more new-entry blocks. At slip=1.0 the additional 3 K-6 fires correspond to the 3 missing trades (108 → 105). | ACCEPTED; documented in v1 KPI card Table 8 K-6 row + §"Bottom line". Mechanism cross-confirms the cost-arm cost-subtraction is operating as designed. |
| Q-1-7 | minor | The `crosses_threshold` field in the sidecar's `breakeven_per_slip` array is `true` at slip ∈ {0.25, 0.5} but the `edge_annotation` is `absent` on all 3 cells. These are NOT contradictory: ratio crossing 2.0 is necessary but NOT sufficient for the `present` annotation (which additionally requires A1 to flip A0's sign per ADR-0028 §D-2 strict reading). The sidecar correctly emits both fields for downstream consumer disambiguation. | ACCEPTED; the dual-field emission is the load-bearing operator-readable disclosure recommended in Q-1-3. |

### R1 Branch B — reproducibility-verifier

**Audit surface**: ReproLog at `logs/reproducibility/957643d6cb8441e29d888482447ead6e.json`; substrate per-partition SHA enumeration in sidecar; RunContext binding semantics; ADR-0017 §3 13-field ReproLog mandate.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| R-1-1 | major | ReproLog 13/13 fields verified: `config_resolved_sha256, dataset_checksums, env_id, git_head, host, hypothesis_id, model_hash, phase, pip_freeze_path, pip_freeze_sha256, rng_seed, run_id, timestamp_utc` ALL present. `model_hash` correctly bound to `scientific_payload_sha256 = a5bce59880e0dd5d824a5b4fd6d7ef7db1df80f05599dc34744f0d26b59ca714` per ADR-0017 §3 binding contract via `ctx.set_model_hash(sha)`. | PASSED. Closes the H065 v1 retrofit pattern documented in [research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md](../../research/01_hypothesis_register/H065/H065_kpi_report_v1_corrigendum_2026-05-18.md). |
| R-1-2 | major | `substrate_per_partition_shas_es` field in sidecar enumerates 12 ES partitions (years 2015-2026) with full SHA256 per partition. Auditor recomputed SHA on `data/processed/vendor_legacy_1min_roll_adjusted/symbol=ES/year=2024/part-0000.parquet` (sha256 = `1c971138cb3dba4a...`) and verified bit-exact match with sidecar entry. | PASSED. Closes `P1-H068-SUBSTRATE-PER-PARTITION-SHA-EMIT`. |
| R-1-3 | major | `dataset_checksums = {"vendor_legacy_1min_roll_adjusted_output_frame_sha256": "317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7"}` matches canonical post-Phase-O.10 substrate per [data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) `output_frame_sha256`. | PASSED. Closes `P1-H068-ES-SUBSTRATE-VERIFICATION`. |
| R-1-4 | minor | Sidecar carries `git_head` NOT in payload (it's in the ReproLog only). The v1 KPI card front-matter records `git_head: 525bad069e2808d6d5d01527ab2be63550735467` which is the HEAD at sweep launch time (verified via `git rev-parse HEAD`). | PASSED. Documented in front-matter. |
| R-1-5 | minor | The KPI v1 card front-matter `simulation_script_sha256` field is currently a relative path placeholder (`scripts/run_h068_sensitivity_sweep.py @ git_head`) rather than a literal SHA. The script content can be reconstructed exactly via `git show 525bad06:scripts/run_h068_sensitivity_sweep.py` at any time; the SHA-binding via git_head + relative path is the canonical pattern used by H062/H065/H067 KPI cards. | ACCEPTED with deferred-polish follow-up `P1-KPI-CARD-SIMULATION-SCRIPT-SHA256-LITERAL` (consider auto-computing script SHA256 at emission time as a top-of-card sha256 alongside git_head; non-blocking polish, consistent across project KPI cards). |
| R-1-6 | minor | The H068 sweep does NOT use walk-forward outer-CV (single-pass OOS aggregate per design.md §13 v1 scope deviation). The ReproLog correctly records `phase = "walk_forward"` per project convention; the lack of per-fold artifacts is a scope-deviation NOT a reproducibility defect. | ACCEPTED; documented in v1 KPI card §"Scope deviations". `P1-H068-WALK-FORWARD-OUTER-CV-V2` registered for the v2 successor. |
| R-1-7 | minor | The sidecar carries `cost_friction_edge_present_ratio_threshold = 2.0` per ADR-0028 §D-2 — the threshold is hard-coded as a module-level constant in the sweep code (`_COST_FRICTION_EDGE_PRESENT_RATIO_THRESHOLD: float = 2.0`). Trace-link verification confirms ADR-0028 §D-2 binding text uses 2.0 as the threshold. | PASSED. |

### R1 Branch C — format-auditor

**Audit surface**: v1 KPI card formatting per ADR-0014 §3.2 13-table mandate + ADR-0026 §D-1 §0 3-component header + ADR-0019 §3 Table 1c + ADR-0028 §D-4 annotation grammar.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| F-1-1 | major | ADR-0014 §3.2 mandates 13 tables; v1 KPI card emits all 13 tables (1, 1c, 2, 3, 3a, 3b, 3c, 4, 5, 6, 7, 8, 9) + Bottom-line prose. Tables 3a (terminal-wealth q05) + 6 (forward 1-year projection) + 7 (Hansen SPA) carry explicit `PLACEHOLDER` markers with cross-link to BLOCKING-BEFORE-PAPER-TRADE-EVALUATED follow-ups. | ACCEPTED with caveat: placeholder tables are admissible per ADR-0014 §3.2 footnote allowing `PLACEHOLDER per <follow-up>` for tractable-but-deferred metrics; consistent with H067 v0 + H065 v0 precedent (both have similar deferred-metric placeholders). |
| F-1-2 | major | §0 3-component summary header per ADR-0026 §D-1 carries per-slip × per-cost-arm rows for Components 1 + 2 (Component 3 forward projection = PLACEHOLDER). The mandatory column set (Component / Window / P/L % / Max-DD % / Win rate / MPPM point / Realized-OOS q05 / Forward q05 / N) is honored with `q05 equity` columns marked `n/a` for non-bootstrap-emitting components. | ACCEPTED. Follows ADR-0026 §D-1 binding text. |
| F-1-3 | minor | Methodological-correctness annotations line in Table 9 spans 19 dot-separated annotations. ADR-0014 §3.2 footnote says "one-line dot-separated"; the line is admittedly long but renders correctly in markdown viewers and matches the project precedent of H055 v2 / H062 v2 / H065 v2 cards (all carry 15-20 annotations). | ACCEPTED with deferred-polish follow-up `P1-KPI-CARD-ANNOTATION-LINE-FORMATTING-CONSOLIDATE` (consider wrapping at 80-char per ADR-0014 §3.2 readability spirit; non-blocking polish). |
| F-1-4 | minor | Pareto-front operator deliverable table at end of v1 KPI card duplicates some content from §0 3-component header (per-slip A1 cells). Intentional per the §8 design.md operator-readable Pareto-front mandate; the table re-presents the H_1 (a)(b)(c) breakdown explicitly. | ACCEPTED; matches design.md §8 + §13 binding mandate. |
| F-1-5 | minor | All cross-link markdown paths verified via in-house grep sweep:  `../H065/H065_kpi_report_v2.md` (exists), `../../../docs/decisions/ADR-0028-*.md` (exists), `../../../src/skie_ninja/backtest/costs/nt8_realistic.py` (exists), `../../../artifacts/runs/H068/957643d6cb8441e29d888482447ead6e/sidecar.json` (exists), `../../../logs/reproducibility/957643d6cb8441e29d888482447ead6e.json` (exists). | PASSED. |
| F-1-6 | minor | The v1 KPI card front-matter `superseded_by: null` is correct (v1 is the live emission). When/if a v2 lands, the v1 front-matter must update `superseded_by` per ADR-0013 §4.1 non-loss preservation discipline. | ACCEPTED. No action at v1 emission. |

## R1 Summary

| Branch | Findings | Critical | Major | Minor | All remediated inline? |
|---|---:|---:|---:|---:|:--:|
| Quant-auditor | 7 | 0 | 4 | 3 | YES (4 acknowledged + documented; 3 minor accepted) |
| Repro-verifier | 7 | 0 | 3 | 4 | YES (3 major PASSED + 4 minor accepted or deferred-polish) |
| Format-auditor | 6 | 0 | 2 | 4 | YES (all accepted; 2 deferred-polish) |
| **Total** | **20** | **0** | **9** | **11** | **YES** |

## R1 Verdict

**`accept-with-residuals`** — zero critical findings; all 9 major findings either (a) PASSED at audit, (b) accepted and documented in the v1 KPI card body, or (c) deferred to non-blocking follow-ups; all 11 minor findings either PASSED or accepted as deferred-polish.

## R2 verification posture

Per SKILL.md 3-round audit-remediate-loop cap + the audit-remediate-loop skill convention, R2 verification is **deferred to first-usage cycle**. The next H068 v1 consumer touchpoint will trigger R2:
- Paper-trade-evaluated stage transition (which requires `P1-H068-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` BLOCKING + `P1-H068-FORWARD-PROJECTION-COMPUTE` BLOCKING follow-ups to land first).
- v2 successor pre-registration (which would consume H068 v1 KPI card as the parent reference per ADR-0027 §D-4 four-field discipline).
- Any downstream consumer audit (e.g., MPV2 meta-portfolio integration; H068 v1 OOS log-returns are available in the sidecar `per_cell_results[*].session_log_returns` arrays).

## Residual follow-ups registered by this audit

- `P1-ADR-0028-EDGE-ANNOTATION-OPERATOR-READABLE-CLARIFY` (non-blocking; clarify ADR-0028 §D-2 trigger semantics that `absent` is the canonical annotation when both A0 + A1 produce positive ROI even if ratio ≥ 2; the `present` flavor requires the A1-flips-A0-sign conjunctive).
- `P1-H068-MPPM-CI-WIDTH-SAMPLE-SIZE-SOLVER` (non-blocking; compute the n_trades threshold above which the H068 slip=0.5 MPPM CI [-1.30, +3.05] would clear zero positively at the +0.56 point estimate — likely n ≈ 500-1000 given √(108/500) ≈ 0.46 width scaling; informs the H068 v2 sample-size design).
- `P1-KPI-CARD-SIMULATION-SCRIPT-SHA256-LITERAL` (deferred-polish; auto-compute simulation_script_sha256 literal at KPI emission time across project KPI cards).
- `P1-KPI-CARD-ANNOTATION-LINE-FORMATTING-CONSOLIDATE` (deferred-polish; ADR-0014 §3.2 footnote readability — consider wrapping the methodological-correctness annotations at 80-char).
- `P1-H068-FORWARD-PROJECTION-COMPUTE` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED; sample-size constraint at n_trades=108).
- `P1-H068-CALMAR-DIFFERENTIAL-CI-COMPUTE` (Calmar-differential paired-pairs stationary-bootstrap CI vs passive-EW ES reference).
- `P1-H068-HANSEN-SPA-COMPUTE` (family size = 18 cells).
- `P1-H068-PAPER-TRADE-EMPIRICAL-SLIP-CALIBRATION` (BLOCKING-BEFORE-PAPER-TRADE-EVALUATED; load-bearing per design.md §1.3 — the sub-1-tick slip empirical reasonableness depends on order book depth + RTH liquidity stratification + order type + size).

## Closed follow-ups by this v1 emission

| Follow-up | Status |
|---|---|
| `P1-H068-WALK-FORWARD-ORCHESTRATOR-IMPL` | CLOSED ([scripts/run_h068_sensitivity_sweep.py](../../scripts/run_h068_sensitivity_sweep.py)) |
| `P1-H068-ES-SUBSTRATE-VERIFICATION` | CLOSED (per R-1-3 finding; substrate SHA matches canonical) |
| `P1-H068-PIT-CANARY-INTEGRATION-TEST` | CLOSED ([tests/integration/test_h068_pit_canaries.py](../../tests/integration/test_h068_pit_canaries.py); 6/6 tests passing) |
| `P1-H068-SUBSTRATE-PER-PARTITION-SHA-EMIT` | CLOSED (per R-1-2 finding; 12 ES partitions enumerated in sidecar) |
| `P1-H068-REPROLOG-WIRE` | CLOSED (per R-1-1 finding; 13/13 fields; model_hash bound to scientific_payload_sha256) |
| `P1-H068-N-MIN-TRADES-GUARD` | CLOSED (all cells n_trades=105-108 above the n_min=50 threshold; `power-margin-ok` annotation emitted on every cell) |
| `P1-H068-COST-RECALIBRATION-PROPAGATE` | CLOSED (ES fees verified UNCHANGED post-Phase-O.16 per [config/instruments.yaml line 50](../../config/instruments.yaml) + design.md §6) |
| `P1-H068-PROD-RUN` | CLOSED (this v1 emission) |

## Audit cross-references

- v1 KPI report card: [research/01_hypothesis_register/H068/H068_kpi_report_v1.md](../../research/01_hypothesis_register/H068/H068_kpi_report_v1.md)
- Sidecar: [artifacts/runs/H068/957643d6cb8441e29d888482447ead6e/sidecar.json](../../artifacts/runs/H068/957643d6cb8441e29d888482447ead6e/sidecar.json) (sha256 `a5bce59880e0dd5d824a5b4fd6d7ef7db1df80f05599dc34744f0d26b59ca714`)
- ReproLog: [logs/reproducibility/957643d6cb8441e29d888482447ead6e.json](../../logs/reproducibility/957643d6cb8441e29d888482447ead6e.json)
- Design.md: [research/01_hypothesis_register/H068/design.md](../../research/01_hypothesis_register/H068/design.md)
- Stage tracker: [research/01_hypothesis_register/H068/stage.md](../../research/01_hypothesis_register/H068/stage.md)
- Failure log: [research/01_hypothesis_register/H068/failure_log.md](../../research/01_hypothesis_register/H068/failure_log.md)
- Parent design audit trail: [docs/audits/audit_trail_2026-05-19_h068-cost-light-h065-es-design.md](audit_trail_2026-05-19_h068-cost-light-h065-es-design.md)
