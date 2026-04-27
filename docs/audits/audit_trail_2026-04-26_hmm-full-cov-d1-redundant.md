---
title: P1-HMM-FULL-COV-1DIM-REDUNDANT — audit-remediate-loop trail
date: 2026-04-26
artifact: src/skie_ninja/models/regime/selection.py + addendum + memo + diagnosis-trail amendment + bench
followup_id: P1-HMM-FULL-COV-1DIM-REDUNDANT
exit_state: round-2 accept-with-residuals
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
---

## Scope

Audit-remediate-loop on the proposal that resulted from three parallel
research agents (literature-check + general-purpose library survey +
codebase verifier) plus an in-house Tier-5 microbench, in response to
the prod-run-1 diagnosis bottleneck identified in
[docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md).

The original proposal (r1) was: edit `config/hypotheses/H050.yaml`
line 24 from `[diag, full]` to `[diag]` + write a sibling addendum.
After Round-1 audit-remediate, the implementation pivoted to model-class
deduplication inside `select_gaussian_hmm` — pre-reg fidelity preserved.

## Round 1 — parallel triad

Three subagents run in parallel per [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) §"Auditor selection":

- **quant-auditor** (`agentId ab7d276b2f33cec1e`) — code correctness + method fidelity + statistical soundness on the 5 changed artifacts.
- **literature-check** (`agentId ac245a6036bdc6a46`) — verified 16 citations against primary sources.
- **reproducibility-verifier** (`agentId a46b1327c542a2358`) — verified bench artifacts, environment manifest, regression test coverage, entrypoint reproducibility.

### Round-1 findings (consolidated)

| ID | Severity | Source | Issue | Round-2 disposition |
|---|---|---|---|---|
| **Q-1-1 / R-1** | critical | quant + repro | `logs/bench_hmm_cov_d1_2026-04-26.json` is 0 bytes — bench's terminal `print(json.dumps(out))` was preceded by a long-running end-to-end loop that was killed; no provenance manifest persisted | **Fixed**: bench refactored to atomic-incremental JSON write after every cell; partial runs now persist `git_head`, `platform`, `numpy_show_config`, `uv_pip_freeze`, `runtime_status` keys |
| **Q-1-2** | major | quant | Per-E-step → end-to-end extrapolation embeds 3 unverified assumptions (M-step cost identical, EM iter count, k-means init) | **Fixed**: addendum §2.4 documents the M-step floor-regime caveat (`np.maximum(raw, min_var)` for diag vs `_ensure_pd(raw, min_var)` for full); §4.4 explicitly bounds saving from per-E-step measurement only and adds the non-HMM floor; the deduplication mechanism (Q-1-4 fix) renders the floor-regime divergence concern moot in production (only one EM trajectory runs) |
| **Q-1-3** | major | quant | Linear wall-clock saving model assumes 100% HMM-bound; non-HMM components (TripleBarrierLabeler ~2.25hr) form a floor | **Fixed**: addendum §4.4 + memo §3.4 + diagnosis-trail amendment now state revised `~12-22 hr` estimate with the non-HMM floor explicit |
| **Q-1-4** | **critical** | quant | The proposed YAML edit removes a frozen pre-registered grid element (design.md §5 line 62 binds `covariance_type ∈ {diag, full}`); contestable as post-hoc grid collapse | **Fixed via re-architecture**: implementation pivoted to auditor's recommended fix (c) — model-class deduplication inside `select_gaussian_hmm`. H050.yaml + design.md grid preserved verbatim; the second EM trajectory is short-circuited at fit time |
| **Q-1-5 / R-4** | major | quant + repro | Bench methodology: `n_iter=5` at T=3M, no CI on ratio, no CPU/BLAS-vendor capture, σ²=1.0 not production-realistic | **Fixed**: bench rewritten with `n_iter=30` at T=3M; 95% percentile-bootstrap CI on the ratio (2000 resamples); `numpy_show_config` + `platform_processor` + `uv_pip_freeze_first_lines` captured; second cell with σ²=1e-8 (production-realistic) added |
| **Q-1-6 / R-5** | major | quant + repro | No regression test for d=1 equivalence | **Fixed**: 7-test `TestD1ModelClassDeduplication` in `test_hmm_selection.py`; `test_d1_full_equals_diag_bit_exact` + `test_d1_spherical_equals_diag_bit_exact` + `test_d1_param_count_equivalence_class` + `test_d1_bic_equivalence_class` in `test_hmm_core.py`; new `test_h050_config.py` asserting `[diag, full]` is preserved in H050.yaml |
| **Q-1-9** | minor | quant | Memo §3.2 ground (a) "lowest measured constant factor" for diag vs spherical is unmeasured | **Fixed**: addendum §5 + memo do not invoke the unmeasured "lowest constant factor" ground; the deduplication mechanism makes the choice arbitrary at d=1 (any of {diag, spherical, full} could be the surviving fit; the strict-`<` BIC tie-break + grid-order determines the actual selection) |
| **Q-1-7** | minor | quant | `.json` vs `.log` path inconsistency across artifacts | **Fixed**: bench writes both; addendum + memo + diagnosis-trail amendment all reference both |
| **Q-1-8** | minor | quant | Schwarz 1978 docstring could cite §3 (asymptotic-derivation section) instead of "p. 461 display sentence" | **Deferred**: current docstring text is honest about the convention difference; §3 pin would add precision but is non-blocking |
| **Q-1-10** | minor | quant | Tier-5 label not present in `.log` file | **Fixed**: bench JSON now carries `"tier": 5` + `"tier_rationale"` keys; the `scripts/bench/README.md` runbook documents the tier explicitly |
| **L-1** | minor | lit | `bic()` docstring's "Schwarz 1978 eq. 3" misattribution (paper has no numbered equations) | **Fixed**: docstring rewritten to reference "Annals of Statistics 6(2):461, p. 461 display sentence" honestly |
| **L-2** | minor | lit | Bishop 2006 §9.2 description "Gaussian mixture covariance taxonomy" is a stretch (§9.2 is "Mixtures of Gaussians" with general Σ_k; the four-way taxonomy is sklearn/hmmlearn terminology) | **Fixed**: addendum §3 reworded to "Mixtures of Gaussians; develops GMM with general per-component Σ_k that the sklearn/hmmlearn covariance-type taxonomy specialises" |
| **L-3** | minor | lit | Murphy 2012 §17.5 is "Learning for HMMs", not specifically Gaussian-emission HMMs | **Fixed**: addendum §3 reworded to "§17.3-17.5 (HMM block); §17.5 is "Learning for HMMs"" |
| **L-4 / L-5** | major (verification-gap) | lit | Rabiner 1989 §III.C.2 + Celeux & Durand 2008 §3.1 paywalled | **Acknowledged**: addendum §3 documents the verification-gap explicitly; project-wide `P1-HMM-VERIFIED-EQ-NUMBERS` tracks the open verification |
| **L-7** | minor | lit | sklearn user guide §2.1 paraphrased "full prone to overfitting" not on the page; closest is "the algorithm is known to diverge and find solutions with infinite likelihood" (numerical singularity, distinct claim) | **Fixed**: addendum §3 + memo §2.3 reworded to use the verbatim singularity-divergence note |
| **L-9** | major | lit | pomegranate issue #227 misattributed (it's a feature request from 2017, not a maintainer comment about univariate workarounds) | **Fixed**: addendum §3 + memo §2.3 reworded to "feature request from 2017-02-26 asking for hmmlearn-style covariance_type support; not implemented as of issue date" |
| **L-12** | major | lit | SciPy issue #23774 qualifier "tests at minimum 20×20" is correct only for one specific benchmark in a broader thread | **Fixed**: addendum §4.5 + memo §2.4 reworded to "tests linalg performance at d=20 (smallest reported size in that thread)" |
| **L-14** | minor | lit | Memo §2.1 "Tier 2" label for source-code-derived equivalence is a stretch per user-global hierarchy enumeration | **Fixed**: memo §2.1 + addendum §3 reframed as "Tier 2 / Tier 4 hybrid" with explicit Tier-by-citation breakdown |
| **L-16** | minor | lit | `.json`/`.log` path inconsistency (same as Q-1-7) | **Fixed** with Q-1-7 |
| **L-6 / L-8 / L-10 / L-11 / L-13 / L-15** | minor | lit | `main`-branch GitHub URLs not pinned to release tag; misc minor citation pins | **Deferred**: non-blocking; `main` URLs are conventional throughout the project; tagged-release citations is a consistency improvement that would touch many addenda |
| **R-2** | major | repro | `runtime_status` field not captured in JSON | **Fixed**: bench JSON now carries `"runtime_status": "in_progress"` while running, `"completed"` on clean exit |
| **R-3** | major | repro | bench has no documented entrypoint | **Fixed**: created [scripts/bench/README.md](../../scripts/bench/README.md) with canonical invocation, output schema, and Tier-5 limitations |
| **R-6 / R-7 / R-8** | minor | repro | sys.path hack; ReproLog gap; cross-document filename inconsistency | **Fixed**: sys.path uses `Path(__file__).resolve().parents[2] / "src"` instead of `rsplit("scripts", 1)`; ReproLog gap documented in README §"Limitations"; filename inconsistency unified to point at both `.json` and `.log` |

## Round-2 produced state

After remediation:

- `src/skie_ninja/models/regime/selection.py` — model-class deduplication for d=1 equivalence-class members `{spherical, diag, full}`; `tied` always fits independently. Module docstring updated with the new section P1-HMM-FULL-COV-1DIM-REDUNDANT.
- `src/skie_ninja/models/regime/_core.py:826-846` — `bic()` docstring corrected (Schwarz 1978 sign convention).
- `config/hypotheses/H050.yaml` — top-of-file comment block points to the addendum + states the dedup mechanism; line 35 unchanged at `[diag, full]`.
- `research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md` — revision r2; describes the deduplication-at-fit-time mechanism (not a YAML edit).
- `docs/research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md` — revision r2; reflects the new mechanism + all lit-check fixes.
- `docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md` — `Constant-factor amendment` subsection updated with measured ratios + 95% CIs + production-realistic-σ² cell + revised wall-clock + the rescission of the original "drop full from YAML" recommendation.
- `scripts/bench/bench_hmm_cov_d1.py` — atomic-incremental JSON write; BLAS-vendor capture; `n_iter=30` at production T cells; 95% bootstrap CI on the ratio; production-realistic σ²=1e-8 cells; CLI with `--out` and `--skip-endtoend` flags.
- `scripts/bench/README.md` — runbook with canonical invocation, output schema, and Tier-5 limitations.
- `tests/unit/test_hmm_selection.py` — 7-test `TestD1ModelClassDeduplication` regression suite.
- `tests/unit/test_hmm_core.py` — 4 new tests: `test_d1_full_equals_diag_bit_exact`, `test_d1_spherical_equals_diag_bit_exact`, `test_d1_param_count_equivalence_class`, `test_d1_bic_equivalence_class`.
- `tests/unit/test_h050_config.py` — pre-reg-grid invariant tests.

**Test suite**: 651/651 unit tests green (was 635 pre-Round-1 + 16 new in Round 2).

## Round 2 — re-audit (parallel quant + repro)

Two subagents run in parallel on the revised state:

- **quant-auditor** (`agentId afd25e27ca93e1702`) — re-audited the deduplication implementation, the regression tests, the addendum r2 + memo r2 + diagnosis-trail amendment.
- **reproducibility-verifier** (`agentId a73f462fb6d0ef18f`) — verified the bench manifest, the test pass count, cross-document path consistency, audit-trail completeness.

### Round-2 findings + dispositions

| ID | Severity | Source | Issue | Disposition |
|---|---|---|---|---|
| **Q-2-1** | major | quant | `scripts/bench/bench_hmm_cov_d1.py:41` `Path(__file__).resolve().parents[2]` triggered `tests/unit/test_paths.py::test_no_file_based_root_resolution_outside_paths_py`; full suite was actually 1 failed / 650 passed (not 651/651) | **Fixed**: added `# paths-guard: allow (sys.path bootstrap before pip install -e .)` comment; full suite re-confirmed at 651/651 |
| **Q-2-2** | major | quant | Diagnosis trail `New follow-ups logged` section still had the rescinded "patch H050.yaml" text | **Fixed**: rewrote the bullet to describe the model-class deduplication mechanism + the rescission of the original recommendation |
| **R-2-2** | major | repro | Memo §2.2 numerical table had stale pre-Round-2 numbers (2.41×/1.82×/1.25×/1.22×) inconsistent with the addendum/JSON (2.569×/1.093×/1.223×/1.167×); wall-clock said "~10-25 hr" vs addendum's "~12-22 hr" | **Fixed**: memo §2.2 + interpretation block updated with Round-2 numbers + 95% CIs + production-realistic-σ² cells; wall-clock unified at "~12-22 hr" |
| **Q-2-3 / R-2-3** | minor | quant + repro | Duplicate `### §4.4` heading in addendum (stale r1 text) | **Fixed**: stale block at lines 200-204 deleted; §4.5 expanded to absorb its non-redundant content |
| **Q-2-4** | minor | quant | Addendum cited H050.yaml `line 35` but actual line is 37 (after comment block insertion) | **Fixed**: replaced numeric line refs with `hmm.covariance_type` key path + line 37 |
| **Q-2-5** | minor | quant | Empty-input failure modes in `select_gaussian_hmm` raised bare IndexError/AssertionError | **Fixed**: added `if not n_states_grid` and `if not covariance_types` validation with descriptive ValueError |
| **Q-2-6 / Q-2-7** | minor | quant | Cache-hit `if bic_score < best_bic:` branch was dead at d=1 (BIC identity); cached `model` was stored but never read | **Fixed (defensive option (b))**: cache-hit branch now updates `best_model = cached_model` so the invariant cannot silently desynchronise if a future drift makes the strict-`<` branch reachable; comment documents the invariant |
| **Q-2-8** | minor | quant | Dedup test used `pytest.approx(abs=1e-12)` instead of strict `==` for values that are bit-exact copies | **Fixed**: tightened to strict `==` |
| **Q-2-9** | minor | quant | Memo claimed 651/651 but reality (pre-Q-2-1 fix) was 650/651 | **Fixed via Q-2-1 fix**: 651/651 re-confirmed empirically post-fix |
| **Q-2-10** | minor | quant | `_numpy_show_config` had dead `np.show_config(mode='dicts')` line | **Fixed**: dead line removed |
| **Q-2-11** | minor | quant | `_bootstrap_ratio_ci` assumed equal arm lengths silently | **Fixed**: separate `n_d`, `n_f` lengths; added docstring noting independence-of-arms assumption + percentile-method choice |
| **R-2-1** | minor | repro | Memo §2.2 + §7 only referenced `.json`, not `.log` | **Fixed**: both files now linked in memo §2.2 + §7 |
| **R-2-4** | minor | repro | Memo §7 references list still had stale L-9 wording for pomegranate | **Fixed**: rewritten to "feature request from 2017-02-26 ... not implemented as of issue date" |
| **R-2-5** | minor | repro | `runtime_status: in_progress` is ambiguous between (a) running, (b) killed, (c) crashed | **Deferred (non-blocking polish)**: tracked as new follow-up `P1-BENCH-RUNTIME-STATUS-TIMESTAMP` |

## Exit verdict

**`accept-with-residuals`** — Round-2 found and remediated 3 majors (Q-2-1 paths-guard, Q-2-2 stale follow-ups text, R-2-2 stale memo table) plus 11 minors. The load-bearing claim (d=1 algebraic equivalence; redundant compute removal via fit-time deduplication) is sound and now anchored at Tier 1/2/4 in the addendum + memo + bench manifest with explicit 95% bootstrap CIs on the constant-factor ratio; the implementation preserves pre-reg fidelity exactly (no YAML/design.md edit); regression tests (16 new + 635 existing = 651 total green) lock the equivalence into CI; bench manifest is reproducible across hosts via the captured `numpy_show_config` + `uv pip freeze` snapshots; the end-to-end T=50k cell measured `[diag, full]` w/ dedup at 1.017× the `[diag]`-only time, confirming the dedup mechanism works as designed.

**Residuals carried forward** (deferred per the audit-remediate-loop 3-round cap):

- L-4 / L-5 (Rabiner 1989 §III.C.2 + Celeux-Durand 2008 §3.1 paywall) — verification-gap inherited from project-wide citation policy; tracked under existing follow-up `P1-HMM-VERIFIED-EQ-NUMBERS`.
- L-6 / L-8 / L-10 / L-11 / L-13 / L-15 (GitHub `main` URLs not tagged; misc citation pins) — non-blocking polish.
- Q-1-8 (Schwarz 1978 §3 vs "p. 461 display sentence" pin) — non-blocking honesty improvement.
- R-2-5 (runtime_status timestamp) — non-blocking polish.

## New follow-ups logged

- `P1-HMM-COV-DEDUP-AUDIT-MARKER` *(operational)* — `n_restarts_used = 0` is overloaded as both "no restarts attempted" and "alias marker"; consider a separate `is_alias: bool` field on `SelectionCandidate` for unambiguous downstream consumption.
- `P1-HMM-VERIFIED-EQ-NUMBERS` *(carried forward)* — verify Rabiner 1989 §III.C.2 + Celeux-Durand 2008 §3.1 from primary sources before the next ADR-0005 freeze.
- `P1-BENCH-CITATION-TAG-PINNING` *(non-blocking polish)* — pin GitHub `main`-branch URLs to tagged releases for long-term reproducibility.
- `P1-BENCH-RUNTIME-STATUS-TIMESTAMP` *(non-blocking polish)* — capture `last_atomic_write_ts_utc` on every atomic write so an auditor can distinguish "killed long ago" from "currently running" without consulting external state.

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [docs/research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md](../research_notes/memo_hmm-full-cov-d1-redundant_2026-04-26.md) — proposal memo.
- [research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md](../../research/01_hypothesis_register/H050/hmm_covariance_d1_equivalence_addendum_2026-04-26.md) — addendum r2.
- [docs/audits/audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md](audit_trail_2026-04-26_h050-prod-run-1-diagnosis.md) — diagnosis (amended).
- [scripts/bench/bench_hmm_cov_d1.py](../../scripts/bench/bench_hmm_cov_d1.py) + [scripts/bench/README.md](../../scripts/bench/README.md) — Tier-5 microbench source + runbook.
- [logs/bench_hmm_cov_d1_2026-04-26.json](../../logs/bench_hmm_cov_d1_2026-04-26.json) — bench output (atomic-incremental).
- [src/skie_ninja/models/regime/selection.py](../../src/skie_ninja/models/regime/selection.py) — implementation site.
- [tests/unit/test_hmm_selection.py](../../tests/unit/test_hmm_selection.py) — regression suite.
- [tests/unit/test_hmm_core.py](../../tests/unit/test_hmm_core.py) — equivalence + parameter-count tests.
- [tests/unit/test_h050_config.py](../../tests/unit/test_h050_config.py) — pre-reg grid invariant.
