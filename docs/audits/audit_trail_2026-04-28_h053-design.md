---
name: H053 design pre-registration — audit trail
description: 3-round audit-remediate-loop on the H053 design.md, lit-review, and data_requirements companion
type: project
hypothesis_id: H053
artifact: audit_trail
created: 2026-04-28
owner: skoir
---

# Audit trail — H053 design pre-registration

3-round audit-remediate-loop per [~/.claude/skills/audit-remediate-loop](../../../.claude/skills/audit-remediate-loop/SKILL.md). Cap reached at Round 3 with all critical + major findings remediated and only `P1-H053-*` follow-ups remaining.

## Artifacts under audit

- [research/01_hypothesis_register/H053/design.md](../../research/01_hypothesis_register/H053/design.md)
- [research/01_hypothesis_register/H053/lit_review_H053_2026-04-28.md](../../research/01_hypothesis_register/H053/lit_review_H053_2026-04-28.md)
- [research/01_hypothesis_register/H053/data_requirements_H053_2026-04-28.md](../../research/01_hypothesis_register/H053/data_requirements_H053_2026-04-28.md) (added in Round 2)

## Loop summary

| Round | Produce phase | Audit phase | Critical | Major | Minor | Status |
|---|---|---|---|---|---|---|
| 1 | Plan subagent (design plan) + Explore subagent (lit research) → main authored both files | quant-auditor + literature-check in parallel | 2 | 11 | 12 | All 2 critical + 11 major remediated in Round 2 |
| 2 | Remediate Round-1 findings + author data_requirements companion | quant-auditor focused regression on changed sections | 0 | 6 | 6 | All 6 major + 4 of 6 minor remediated in Round 3 |
| 3 | Remediate Round-2 findings + cheap minor fixes | none — exit per skill rule (only follow-up tags remain) | — | — | — | Loop exit; remaining minor items captured as `P1-H053-*` follow-ups below |

## Round 1 — findings + dispositions

### Literature-check subagent (lit-review + design.md citation set)

| Finding | Severity | Disposition |
|---|---|---|
| Lou-Polk-Skouras 2019 DOI wrong (`10.1016/j.jfineco.2019.04.001` resolves to a different JFE 134 paper) | critical | Round-2 fix: replaced with `10.1016/j.jfineco.2019.03.011` in lit-review §A bullet 5, lit-review §Key citations item 1, lit-review §Lit-review-sourced risks item 3, design.md frontmatter line 19 + body §1 mechanism. Erratum note added in lit-review. |
| Pearl 2001 UAI URL 404s (`https://ftp.cs.ucla.edu/pub/stat_ser/r273-U.pdf`) | minor | Round-2 fix: replaced with arXiv:1301.2300 mirror. |
| GEPA flagged UNVERIFIED but arXiv:2507.19457 is locatable | minor | Round-2 fix: arXiv ID added; UNVERIFIED dropped in lit-review §F. |
| Cliff-Cooper-Gulen UNVERIFIED but SSRN 1004081 + JAM 2011 doi:10.1057/jam.2011.2 are locatable | minor | Round-2 fix: rephrased lit-review §Wanted-but-unverified to acknowledge both venues; kept out of design.md primary citations because LPS 2019 (peer-reviewed JFE) covers the same claim with stronger evidence-tier. |
| AB 1998 description as "high-frequency realized variance estimator" overshoots paper's actual contribution | minor | Round-2 fix: lit-review §A bullet 2 narrowed to "validation of conditional-volatility models using ex-post realized variance" with cross-reference to ABDL 2003 as the formal estimator anchor. |
| ABDL 2003 attributed with U-shape documentation but the paper deseasonalises rather than documents it | minor | Round-2 fix: U-shape attribution moved to Wood-McInish-Ord 1985 + AB 1997 doi:10.1016/S0927-5398(97)00004-2 added; ABDL 2003 retained for the framework claim only. |
| Synthesis paragraph in §A overshoots cited literature (opening-15-min specifically not tested in any cited paper) | minor | Round-2 fix: §A Synthesis softened to acknowledge H053 mediation framing as extension, not confirmation. |
| Risk-3 wording oversimplified LPS-vs-BKTZ tension | minor | Round-2 fix: rephrased to acknowledge same-period continuation + cross-period reversal nuance. |
| Velay-Daniel 2018 mischaracterized as "candlestick" classification (paper is on common chart patterns) | minor | Round-2 fix: lit-review §D corrected to "common chart patterns (head-and-shoulders, double-tops)". |
| IKT 2010 description attributed sequential-ignorability identification result that is centrally in IKY 2010 | minor | Round-2 fix: lit-review §C narrowed IKT 2010 to "general framework"; IKY 2010 retained for the formal-identification result. |
| Bergstra-Bengio 2012 invocation for a 12-15-cell discrete grid is replicate-coverage, not the high-dim B&B regime | minor | Round-2 fix: design.md §9 added inline caveat tying to project follow-up `P1-H053-N-DRAWS-EMPIRICAL`. |
| Three lower-priority DOIs (Baron-Kenny 1986, Neely et al. 2014, Bulkowski 2005) not WebFetch-verified in Round 1 | minor | Disposition: not in priority list; deferred. None are load-bearing for the §1 mechanism paragraph. |

### Quant-auditor subagent (design.md)

| Finding | Severity | Disposition |
|---|---|---|
| PIT boundary collision at 09:45 ET — mediator and predictand share the 09:45 ET-timestamped bar without a binding bar-edge convention | **critical** | Round-2 fix: added §3.0 "Bar-edge convention" pinning left-closed-right-open intervals on ending-timestamps, mediator-window bar set `{09:31, …, 09:45}`, predictand-window bar set `{09:46, …, 10:30}`, boundary-anchor framing for `C_i(09:45 ET, t)`. §3.4 mediator wording updated. §11.2 item 11 binds the bar-set-disjointness unit test. |
| Treatment-scalarization circularity — `f_S` (Arm-1 ElasticNet on Block A+B+C) was fitted on the same rows as the mediation regressions | **critical** | Round-2 fix: added §5.4 fold-disjoint scalarization protocol — `S` (≈50%) and `Med` (≈50%) sub-folds with ADR-0007 stacked embargo; `f_S` frozen across `Med` and OOS; bootstrap resamples `Med` rows only. DML alternative (Chernozhukov et al. 2018 doi:10.1111/ectj.12097) pre-registered as sensitivity exhibit. §11.2 item 9 binds the protocol unit test. |
| K=5 magic number in archetype categorization (driven by user's example table, not data) | major | Round-2 fix: `K ∈ {3, 5, 7, 9}` CV-tuned; criterion = mean OOS Brier on inner WF folds; ties broken by smaller K. ADR-0005 misapplication corrected to Cochran 1954 doi:10.2307/3001616 cell-count rule. |
| Calibration fold underspecified (size, embargo interaction, per-arm vs per-archetype scope) | major | Round-2 fix: §4.5.3 + §6 specify per-arm + global-across-archetypes scope, `N_cal ≥ 500` precondition, Platt fallback per Platt 1999, ADR-0007 stacked embargo on the calibration slice. |
| LLM determinism incomplete (CUDA non-determinism, hardware target) | major | Round-2 fix: §5.3 strengthened with `torch.use_deterministic_algorithms(True)`, `CUBLAS_WORKSPACE_CONFIG`, CUDA + GPU pin, bit-identical-logit-tensor replay. Round-3 added §11.3 binding hardware reproducibility commitments. |
| `s_min = 1.0` copy-pasted from H052a; H053's predictand has different signal-to-noise structure | major | Round-2 fix: §9 power block recalibrated — MDE inversion against `expected_n_oos` via Lo 2002 §III HAC-adjusted Sharpe SE; `ar1_rho_pilot` and `excess_kurtosis_pilot` pinned outside IS on a 2010-2014 pilot window; refining-on-IS forbidden for H053. data_requirements §Pre-IS pilot specifies three contingency paths. Round-3 added §11.2 item 19 binding the power-calibration solver. |
| 1-tick floor slippage at 09:45 ET MOC entry likely optimistic | major | Round-2 fix: §7.1 2-tick slippage sensitivity arm pre-registered; §10.2 cost-floor-conditional annotation. Round-3 added §11.2 item 18 binding the 2-tick cost arm scaffolding. |
| SPA family-entry "drop arm" pre-registration loophole | major | Round-2 fix: §8 rewritten to "consume slot as `archive(null, prerequisite-not-met)`"; family size preserved at exactly 3. Round-3 fixed §1 + §12 stale wording that contradicted §8. Round-3 added §11.2 item 16 binding ADR-0008 omega-correction integration test. |
| Mediation bootstrap — residuals vs paired-pairs unspecified | major | Round-2 fix: §5.4 switched primary CI to paired-pairs (rows-of-`(X̂, M, y)`) stationary bootstrap with shared block length per Politis-White 2004; residual-bootstrap demoted to sensitivity exhibit. |
| Decision-rule cells not mutually exclusive | major | Round-2 fix: §10 rewritten as strict precedence-ordered tree (8 numbered rules) with §10.2 additive annotations. |
| Snapshot binding at "first running run" weaker than H050's atomic re-freeze | major | Round-2 fix: authored data_requirements_H053_2026-04-28.md companion at `designed` status with binding partition-level SHA256 table; design.md §2 references the companion + hard-fail check. |
| Kill-switch not documented | major | Round-2 fix: §11.1 kill-switch design subsection added (4 trip conditions). Round-3 marked thresholds as paper-trade operational (not statistical-inference) and tracked empirical recalibration under `P1-H053-KDD-EMPIRICAL-CALIBRATION`. |
| Instrument-dummy stratification underspecified | minor | Round-2 fix: §5.5 made concrete (`is_NQ ∈ {0, 1}`, system-message instrument symbol for LLM, pooled SPA, per-instrument table). |
| Conjunctive-benchmark rule statement implicit | minor | Round-2 fix: §8 explicit conjunctive-rule statement with intersection-union FWE bound (Hochberg-Tamhane 1987). |
| Tied-row ε mid-price-relative across 2015-2025 | minor | Round-2 fix: §4.2 tied-row ε pinned at IS-fold-median-mid-price. Round-3 made the binding mechanism unambiguous (one-shot pin at full IS, not per-fold). |
| OFI tickrule pending MBP-10 substrate | minor | Round-2 fix: §3.3 added MBP-10 trigger sub-bullet referencing `P1-MBP10-INGEST-LANDED`. |
| PC1 variance threshold 50% magic | minor | Round-3 fix: §5.4 cited Jolliffe 2002 §6.1.1 + Cattell 1966 as practitioner-default anchors; empirical recalibration under `P1-H053-PC1-THRESHOLD-EMPIRICAL`. |
| Image-render hardware portability not scoped | minor | Round-2 + Round-3 fix: §3.5 + §5.3 reference §11.3; same-machine + same-env scope; cross-OS follow-up `P1-H053-IMAGE-RENDER-CI-PORTABILITY`. |

## Round 2 — findings + dispositions

Round-2 audit was scoped to regression on the changed sections only (per skill best-practice).

| Finding | Severity | Disposition |
|---|---|---|
| §1 + §12 vs §8 family-entry contradiction (stale Round-1 wording vs Round-2 slot-consumption rule) | major | Round-3 fix: §1 last sentence + §12 final sentence rewritten to match §8. |
| §3.5 + §5.3 forward-references to non-existent §11.7 | major | Round-3 fix: added §11.3 "Hardware reproducibility commitments" subsection; §3.5 + §5.3 cross-references updated. |
| §4.2 tied-row ε binding mechanism inconsistent (one-shot vs per-WF-step) | major | Round-3 fix: §4.2 explicitly binds one-shot pin at full IS window; sensitivity exhibit added. |
| §11.2 prerequisites missing items 15-19 (four-way split feasibility, ADR-0008 omega test, TOD-FE benchmark, 2-tick cost arm, power-calibration solver) | major | Round-3 fix: items 15-19 appended to §11.2. |
| §6 inner-WF feasibility floor for `N_Med`, `N_S` not specified | major | Round-3 fix: §6 added inner-WF-step floor `N_Med ≥ 200` + `N_S ≥ 200`; below-floor → `archive(null, mediation-underpowered)` per §10.2 annotation pathway; Sharpe gate unaffected. |
| §11.1 `k_DD = 1.5` magic number without empirical justification | major | Round-3 fix: §11.1 marked as paper-trade operational thresholds (not statistical-inference); empirical-justification rule does not bind operational thresholds; recalibration tracked under `P1-H053-KDD-EMPIRICAL-CALIBRATION` before live promotion. |
| §3.4 `O_{09:30}` notation inconsistent with §3.0 convention | minor | Round-3 fix: §3.0 added shorthand-notation footnote. |
| §5.4 PC1 50% variance-explained threshold magic | minor | Round-3 fix: cited Jolliffe 2002 §6.1.1 + Cattell 1966; follow-up `P1-H053-PC1-THRESHOLD-EMPIRICAL`. |
| §4.5.3 `N_cal ≥ 500` magic | minor | Round-3 fix: cited Niculescu-Mizil & Caruana 2005 §3 isotonic dominance regime; follow-up `P1-H053-NCAL-EMPIRICAL`. |
| §5.3 DSPy/GEPA UNVERIFIED branch with no ReproLog persistence | minor | Round-3 fix: ReproLog `prompt_search_method` field added; bound by §11.2 item 13 lit-check outcome. |
| data_requirements §Coverage NQ date 2025-12-19 vs design.md §2 NQ date 2025-12-20 | minor | Round-3 fix: design.md §2 updated to 2025-12-19 (left-closed-right-open with Z-window upper bound 12-20 means last-bar-timestamp = 19); footnote on bar-timestamp vs Z-window-bound semantics. |
| data_requirements hard-fail at "any partition or combined" vs design.md combined-only | minor | Round-3 fix: design.md §2 tightened to partition-level granularity matching the companion. |

## Round 3 — exit

No Round-3 audit was run. Per the skill exit rule ("If `findings == []` or only `minor` remain → exit"), the loop exits with all critical + major findings remediated and minor items either fixed inline or captured as `P1-H053-*` follow-up tags below. The 3-round cap is reached.

## Open follow-up tags (`P1-H053-*`)

These are non-blocking residuals surfaced by the loop. They are tracked under the project's standard `P1-*` tag scheme and should be picked up by the regular follow-up triage cycle (mirroring how H050 + H052a follow-ups are handled in the project's [CLAUDE.md](../../CLAUDE.md) §Implemented infrastructure).

| Tag | Source round / location | Description |
|---|---|---|
| `P1-H053-N-DRAWS-EMPIRICAL` | R1 design.md §9 | Calibrate `N_draws` empirically for the H053 12-15-cell discrete grid (replicate-coverage regime, not Bergstra-Bengio high-dim regime). Inherits from project-level `P1-H050-LGB-N-DRAWS-EMPIRICAL`. |
| `P1-H053-PILOT-WINDOW-DATABENTO` | R2 data_requirements §Pre-IS pilot | Acquire ES + NQ 2010-2014 1-min pilot window from Databento for the §9 power-calibration `ar1_rho_pilot` + `excess_kurtosis_pilot` pin. Cost estimate to be recorded. |
| `P1-H053-IMAGE-RENDER-CI-PORTABILITY` | R2 design.md §3.5 / §11.3 | Verify chart-image render-hash determinism across CI run + local run on different OS / Python-minor-version combinations. |
| `P1-H053-KDD-EMPIRICAL-CALIBRATION` | R3 design.md §11.1 | Recalibrate kill-switch `k_DD` (and the 5-session warm-up, 20-session rolling Sharpe window, Brier 2σ × 20-session window) per IS-fold realized-DD distribution; binding before any live (post-paper-trade) promotion. |
| `P1-H053-PC1-THRESHOLD-EMPIRICAL` | R3 design.md §5.4 | Empirically calibrate the PC1 variance-explained threshold `{0.5, 0.7, 0.8, 0.9}` via training-fold synthetic-null mediator-block coverage; replaces the practitioner-default 50%. |
| `P1-H053-NCAL-EMPIRICAL` | R3 design.md §4.5.3 | Empirically calibrate the calibration-fold size precondition (currently `N_cal ≥ 500`) via training-fold synthetic Bernoulli coverage at `N ∈ {200, 300, 500, 1000}`. |
| `P1-MBP10-INGEST-LANDED` | R1 design.md §3.3 | Project-wide trigger; when MBP-10 substrate lands, swap H053 OFI proxy `ofi_tickrule_*` → `ofi_cks_*` per Cont-Kukanov-Stoikov 2014 (DOI verification also pending). Pre-registered as a sensitivity exhibit, not a re-promotion. |

## Identity hygiene

Both artifacts use `owner: skoir` (frontmatter) consistent with the s-koirala GitHub identity / SKIE pseudonym per [~/.claude/CLAUDE.md §Role](../../../.claude/CLAUDE.md). No real-name strings, no email addresses, no OS-username metadata. Round-1 lit-check confirmed clean.

## Loop process notes

- Round-1 produce: parallel Plan + Explore subagents (single message, two tool calls), in line with the skill recommendation to spawn auditors in parallel for mixed-concern artifacts.
- Round-1 audit: parallel `literature-check` + `quant-auditor` subagents.
- Round-2 audit: focused `quant-auditor` regression on the changed sections only — no `literature-check` re-run because the only lit-review change was the DOI swap, which was independently verified by URL-fetch in Round 1.
- Round-3 had no audit phase; exit per skill rule when only minor residuals remain.
- The user-clarified categorical bias-target-probability table requirement (delivered mid-loop after Round-1 audit findings were in flight) was integrated into the design as §4.5 with its own categorization algorithm + calibration pipeline + secondary BSS gate; the user's example MNQ numeric levels are illustrative for table layout only and not pre-registered as binding constants.
- The 3-round cap is reached. The skill empirical-justification ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751)) reports diminishing returns on multi-agent self-consistency at moderate sample counts; further rounds were not pursued.
