# Audit trail — Phase P P-1/P-4/P-5 MPV2 closed-loop pipeline + pre-registration

- **Date**: 2026-06-02
- **Artifacts**: [scripts/run_mpv2_closed_loop.py](../../scripts/run_mpv2_closed_loop.py); [tests/unit/test_mpv2_closed_loop.py](../../tests/unit/test_mpv2_closed_loop.py); [research/01_meta_portfolio/MPV2/design.md](../../research/01_meta_portfolio/MPV2/design.md) (frozen pre-registration).
- **Authority**: ADR-0029 §D-4 (the falsifiable center) + ADR-0020 (meta-portfolio) + the MPV2 pre-reg.
- **Discipline**: audit-remediate-loop, 3-round cap. Round 1 with proper-isolated parallel quant-auditor + code-reviewer. Round 2 verification deferred to the real-data run (the empirical check on the eventual beat-1/N verdict).

## Round 1 — quant-auditor (agentId a7a9d8ffd18c7ec81) — verdict `proceed-with-remediation`

**The #1 concern — look-ahead / causal-alignment (ADR-0029 §D-4 BLOCKING) — verified CLEAN on all four sub-checks** (perturbation-tested): algorithm selection reads only the calibration head; the winning bandit runs fresh + online on the disjoint eval tail (arm-at-t depends only on eval rows < t); the early-warning reference is calibration-derived; the oracle is excluded from the pass/fail; per-session sizing uses no future state. No leakage.

| # | Severity | Finding | Remediation |
|---|---|---|---|
| F-1-1 | **critical** | The primary §1 pass/fail compared the SIZED (de-risked, ~0.72× realized exposure; CPPI fresh-peak scale only 0.8) closed-loop against a SIZING-FREE 1/N at 1.0× — apples-to-oranges; an allocator with superior selection skill could fail purely on the exposure throttle. | **Applied.** Extracted `apply_sizing_overlay` and run 1/N + B&H through the IDENTICAL overlay → primary = sized-closed-loop vs **sized**-1/N (like-for-like). Raw-selection-vs-raw-1/N retained as a secondary diagnostic. |
| F-1-2 | major | §7 reporting incompleteness: only mean-diff CIs + `final_equity` (the demoted ensemble quantity); missing the ADR-0029 §D-3.1 time-average headline. | **Applied (core).** Added `mppm_rho_1` on the sized stream (+ on sized-1/N) as the time-average headline; `final_equity` renamed `..._ensemble_caveat`. Full survival vector (terminal-wealth-q05, Calmar-diff, risk-of-ruin) registered BLOCKING-before-real-verdict `P1-MPV2-FULL-SURVIVAL-VECTOR`. |
| F-1-3 | major | Effective-breadth heuristic `N/(1+(N−1)·ρ̄)` understates the canonical eigenvalue ENB (e.g. ρ=0.3,N=4: 2.11 vs Meucci 3.56) → biases the §8 disposition toward false "reduced breadth". | **Applied.** `effective_breadth` = Meucci 2009 eigenvalue-entropy ENB (`exp(−Σ pᵢ ln pᵢ)`); the mean-abs heuristic retained as a labeled secondary proxy. Synthetic 4-arm ENB now 3.957 (vs the heuristic's 3.284). |
| F-1-4 | major | `beat_both_conjunctive` is always-False when B&H is absent (contradicts the "beat-1N" disposition string) — would record a FALSE NULL on the only currently-runnable path. | **Applied.** Tri-state: `beat_both_conjunctive = None` (undetermined) when B&H absent; `_disposition` returns `*-BH-not-evaluated` labels. |
| F-1-5 | minor | Early-warning reads the raw chosen-arm path, not the sized realized path (spec §4.2). Causal (no leakage). | **Applied.** Documented as the intentional choice (detect arm decay independent of own throttle); `# justify:` in code + design §4.2 note. |
| F-1-6 | minor | Reward matrix is positional-truncate-to-shortest, not the §3.2 inner-join-on-session-date. | Docstring relabeled; real-data runs gated behind `P1-MPV1-CALENDAR-ALIGNMENT` (the date inner-join is a precondition of a real verdict). |
| F-1-7 | minor | `paired_bootstrap_ci` mixed a one-sided 5th-pct lower with a two-sided 97.5th-pct "upper" in one object. | **Applied.** Clean `ci_lower_one_sided` (the §7 test) + a separate `ci_two_sided` pair. |
| F-1-8 | minor | `reference_sigma` silently fell back to 1.0 on a degenerate calibration head (disabling the CUSUM). | **Applied.** Raises instead of silently disabling. |
| F-1-9 | minor | Selection-on-raw-rewards / sizing-as-overlay decoupling undocumented. | **Applied.** Documented (verified methodologically correct — the bandit's regret target is the raw arm reward; sizing is a separate causal overlay). |
| F-1-10 | minor | The three bootstrap CIs share one rng_seed (correlated draws); ReproLog absent. | Joint shared-index conjunctive bootstrap registered `P1-MPV2-JOINT-BOOTSTRAP-CONJUNCTIVE`; ReproLog `P1-MPV2-REPROLOG-WIRE`. Both BLOCKING-before-real-verdict. |

## Round 1 — code-reviewer (agentId a10591a4d31dba314)

No critical. Major cluster = test coverage + validation guards:

| # | Severity | Finding | Remediation |
|---|---|---|---|
| CR-1 | major | `_disposition` branches + `beat_both_conjunctive` untested. | **Applied.** `TestDisposition` (4 branches + tri-state). |
| CR-2 | major | Buy-and-hold path (`passive_long`) untested. | **Applied.** `test_buy_and_hold_path_yields_conjunctive_verdict`. |
| CR-3 | major | `closed_loop_equity` + causal split untested. | **Applied.** `TestClosedLoop` (length/range validation + stream shapes). |
| CR-4 | major | `arm_choices` index-compatibility unvalidated. | **Applied.** Length + range guards in `closed_loop_equity`. |
| CR-5 | major | Public functions missing Args/Returns/Raises. | **Applied.** Added to `apply_sizing_overlay`, `closed_loop_equity`, `run_pipeline`. |
| CR-7, CR-10 | minor | `passive_long` length + `calibration_fraction` range unvalidated. | **Applied.** Both guards added; tested. |
| CR-12, CR-17 | minor | Missing-sidecar message + truncate-to-shortest untested. | **Applied.** `match="not found"` + `test_truncates_to_shortest_arm`. |
| CR-6, CR-13, CR-16 | minor | dict returns (vs dataclass; MPV1 house pattern), shared bootstrap primitive, `evalm` naming. | `evalm`→`eval_matrix` applied; dataclass returns + shared primitive registered as non-blocking follow-ups. |

## Verdict

Round 1: **accept-with-residuals.** The look-ahead invariant (the load-bearing risk) is clean. The critical F-1-1 (sized-consistent benchmarks) + all four quant majors + all code-reviewer majors remediated. 21/21 unit tests green; script ruff-clean + formatted. The harness is correct + honest (synthetic verdict: selection point-positive, CI covers zero, tri-state disposition, Meucci ENB).

**Residuals — all BLOCKING-before-the-real-data §1 verdict (not before the synthetic validation):** `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` (P-1 real arm re-emission), `P1-MPV1-CALENDAR-ALIGNMENT` (date inner-join), `P1-MPV2-FULL-SURVIVAL-VECTOR` (terminal-wealth-q05 + Calmar-diff + risk-of-ruin), `P1-MPV2-JOINT-BOOTSTRAP-CONJUNCTIVE`, `P1-MPV2-REPROLOG-WIRE`, `P1-MPV2-BH-SERIES-WIRE` (passive-long emission), `P1-EARLY-WARNING-THRESHOLD-CALIBRATE` + `P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION` (§5 holdout calibration). Round 2 verification folds into the real-data run.
