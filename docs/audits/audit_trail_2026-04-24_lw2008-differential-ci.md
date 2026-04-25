---
title: P1-H050-LW2008-DIFFERENTIAL-CI-IMPL — audit-remediate-loop trail
date: 2026-04-24
artifact: Ledoit-Wolf 2008 studentised time-series bootstrap CI for differential Sharpe ratio
followup_id: P1-H050-LW2008-DIFFERENTIAL-CI-IMPL
exit_state: round-1 accept (1 minor inline-resolved + 1 documentation strengthening; 1 follow-up logged)
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
---

## Scope

Close evidence-bar-blocking follow-up `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` (residual of [aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) §5.3). The brief: implement a callable [Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002) studentised time-series bootstrap CI for the H050 paired differential statistic `T_H050 = SR(r_p_gated) − SR(r_p_uncond)`. Function signature must match the project's `opdyke2007_ci` style; bootstrap must use the project's existing [Politis-Romano 1994 stationary bootstrap](../../src/skie_ninja/inference/bootstrap.py); block length via [Politis-White 2004](../../src/skie_ninja/inference/bootstrap.py) auto-selection on the paired-difference series; HAC standard error via the joint-moment-vector delta method.

## Method-fidelity anchor

The construction is the studentised pivotal CI of [Hall 1992 *The Bootstrap and Edgeworth Expansion*, Springer ISBN 978-0-387-94508-8 §3.5](https://doi.org/10.1007/978-1-4612-4384-7) / [Davison & Hinkley 1997 *Bootstrap Methods and their Application*, Cambridge UP ISBN 978-0-521-57471-6 §5.4 eq. 5.10](https://doi.org/10.1017/CBO9780511802843), specialised to the Sharpe-ratio difference per [Ledoit & Wolf 2008. *J. Empirical Finance* 15(5):850-859](https://doi.org/10.1016/j.jempfin.2008.03.002):

1. Sample Sharpe difference `Δ̂ = SR_a − SR_b` with biased plug-in moments (`ddof=0`) — derivation convention of [Mertens 2002, SSRN 1019823](https://ssrn.com/abstract=1019823) / [Jobson & Korkie 1981, *J. Finance* 36(4):889-908](https://doi.org/10.1111/j.1540-6261.1981.tb04891.x) / Ledoit-Wolf 2008 §3.1.
2. HAC standard error of `√T · Δ̂` via the delta method on the joint moment vector `θ = (μ_a, γ_a, μ_b, γ_b)` (with `γ_i = E[r_i²]`), with Newey-West 1987 Bartlett-kernel long-run covariance of the per-period 4-vector `v_t = (r_a, r_a², r_b, r_b²)`. Bandwidth from [Newey & West 1994](https://doi.org/10.2307/2297912) on the paired-difference series `r_a − r_b`.
3. Studentised bootstrap statistic `T*ᵇ = √T · (Δ*ᵇ − Δ̂) / se*ᵇ` over [Politis-Romano 1994](https://doi.org/10.1080/01621459.1994.10476870) stationary bootstrap with paired indices (reused across both series within a replicate to preserve cross-series dependence per Ledoit-Wolf 2008 §3 and Hansen 2005 §2 conventions). Block length from [Politis-White 2004 + Patton-Politis-White 2009](https://doi.org/10.1080/07474930802459016) on the paired-difference series.
4. Studentised pivotal CI: `[Δ̂ − q_{1−α/2}(T*) · se / √T, Δ̂ − q_{α/2}(T*) · se / √T]`.

Bootstrap variant substitution (stationary for circular block bootstrap) follows [Lahiri 2003 *Resampling Methods for Dependent Data*, Springer ISBN 978-0-387-00928-5 Chapter 5 "Comparison of Block Bootstrap Methods"](https://doi.org/10.1007/978-1-4757-3803-2) — the two have the same first-order asymptotic properties under weak dependence. The substitution is documented at the function docstring and module docstring; it is a project-wide design decision (memo r4 §3.1 audit finding F-3-1) not a literature-level primacy claim about the Ledoit-Wolf 2008 text.

## Subagent-spawn protocol — AVAILABILITY NOTE

Per [~/.claude/skills/audit-remediate-loop/SKILL.md](C:\Users\skoir\.claude\skills\audit-remediate-loop\SKILL.md) §2 ("Audit — spawn `quant-auditor` subagent") + §"Auditor selection", end-of-round-N audits MUST be performed by spawning `quant-auditor` and `literature-check` subagents via the Agent (Task) tool. **In this environment the Agent / Task tool is NOT surfaced** — it is absent from both the prompt's loaded toolset and the deferred-tool ToolSearch index (verified 2026-04-24 via two ToolSearch queries: `select:Task,Agent` and `subagent` — both returned no matches). The `audit-loop` skill that wraps the spawn convention was invoked but did not surface a callable spawning primitive.

The Round-1 audit therefore documents an **inline self-audit substitution** under the role rubrics published at [~/.claude/agents/quant-auditor.md](C:\Users\skoir\.claude\agents\quant-auditor.md) and [~/.claude/agents/literature-check.md](C:\Users\skoir\.claude\agents\literature-check.md). This is a documented protocol deviation and is a residual of this audit trail (see "Residual risk" below). Comparable in-context audit behaviour was applied at [audit_trail_2026-04-24_h050-aggregation-rule.md](audit_trail_2026-04-24_h050-aggregation-rule.md) under the same Subagent-availability constraint.

Agent-tool spawn invocation log per round (per task brief "Include the Agent-tool spawn invocation log per round so the protocol-compliance is auditable"):

| Round | Spawn attempt | Result |
|---|---|---|
| 1 | `Skill(audit-loop, args=...)` | Skill loaded; no Agent-tool primitive surfaced. ToolSearch followups: `select:Task,Agent` → "No matching deferred tools found"; `subagent` → "No matching deferred tools found". Inline self-audit performed under quant-auditor + literature-check rubrics. |

## Round-1

### Implementation summary

- [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) (NEW, ~440 lines including module docstring): `_as_clean_paired`, `_sharpe_biased`, `_hac_se_sharpe_difference` (joint-moment-vector delta-method HAC SE), `_resolve_block_length`, `_resolve_bandwidth`, `DifferentialCIResult` (frozen dataclass), `ledoit_wolf_2008_differential_ci` (public callable). `_MIN_OBS = 4` floor matches `nw1994_bartlett_bandwidth` lower bound.
- [src/skie_ninja/inference/stats/__init__.py](../../src/skie_ninja/inference/stats/__init__.py): public re-exports `DifferentialCIResult` + `ledoit_wolf_2008_differential_ci`. Preserves the parallel-workstream `return_conventions` exports that landed during this implementation window (`arithmetic_to_log`, `log_to_arithmetic`).
- [tests/unit/test_ledoit_wolf_2008.py](../../tests/unit/test_ledoit_wolf_2008.py) (NEW, 14 unit tests covering signature/dataclass; iid Gaussian coverage at n_fixtures=1000; dependent AR(1) + cross-correlation coverage at n_fixtures=500; PW2004 auto block-length stability; bootstrap T-quantile heavy-tail departure from standard normal on Student-t(3) n=80; determinism under fixed RNG; 7 input-validation guards; perfect-correlation degenerate case).

Test posture (BLAS-pinned env, single test-file scope):

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src \
  uv run --python 3.11 --extra dev pytest tests/unit/test_ledoit_wolf_2008.py -v
→ 14 passed in 236s
```

Ruff posture:

```
uv run --python 3.11 --extra dev ruff check src/skie_ninja/inference/stats/ledoit_wolf_2008.py \
  src/skie_ninja/inference/stats/__init__.py tests/unit/test_ledoit_wolf_2008.py
→ All checks passed!
```

### Round-1 self-audit findings (quant-auditor + literature-check lenses, in-context)

Findings prefixed `F-1-N` follow the quant-auditor schema (severity / category / location / issue / fix); findings prefixed `L-1-N` follow the literature-check schema (severity / claim / source / issue / correction).

| ID | Severity | Lens | Location | Issue | Disposition |
|---|---|---|---|---|---|
| F-1-1 | minor | quant / numerical | [_hac_se_sharpe_difference](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) | Variance floor `_EPS` applied at end of HAC computation produces an artificially small-but-nonzero `se*` on degenerate bootstrap resamples (zero-variance subseries), inflating `T*` and the resulting CI quantile. The `try/except ValueError` branch around `_sharpe_biased` and `_hac_se_sharpe_difference` catches the zero-variance case via the `_sharpe_biased` raise; the `_EPS` floor on `var_root_t_delta` only triggers for genuinely small but positive variance. | Inline-resolved: documented in the function docstring; the `try/except` correctly assigns `T*ᵇ = 0` for degenerate resamples (zero, not NaN, is the right sentinel since NaN would propagate to the empirical quantile). No code change required. |
| F-1-2 | minor | quant / method | [bootstrap loop](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) | The HAC truncation lag `bw` is held fixed across bootstrap replicates (re-estimation per replicate is computationally expensive). This is a deviation from Ledoit-Wolf 2008 §3.1's literal prescription which re-selects per replicate. The deviation is bound by the same first-order asymptotic equivalence as the stationary-vs-circular bootstrap substitution (Lahiri 2003 §6) — both are O(n^{-1/3}) corrections that vanish asymptotically. | Round-1 fix: docstring strengthened with the explicit citation to Davison & Hinkley 1997 §5.4 + Hansen 2005 SPA convention parallel; new follow-up `P1-LW2008-PER-REPLICATE-BANDWIDTH` logged. |
| F-1-3 | minor | quant / reporting | [ledoit_wolf_2008_differential_ci validation order](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) | Pre-Round-1 ordering allocated `_as_clean_paired` arrays before validating `block_length >= 1.0` — wasteful on bad-input paths; `block_length` validation only happened inside `_resolve_block_length` after the arrays were already coerced. | Round-1 fix: moved `block_length`, `alpha`, `n_bootstrap` validation to the top of the function body (before the array coercion). |
| L-1-1 | major | lit / verification-gap | module docstring "Verification status" | Direct access to the Ledoit & Wolf 2008 *J. Empirical Finance* PDF blocked by ScienceDirect paywall at audit time. The §3.1 construction is reconstructed from (a) the JK1981 + Memmel 2003 papers that LW2008 explicitly extends and (b) the project's existing bootstrap primitives. | Inline-resolved: the docstring "Verification status" subsection explicitly documents the verification gap, names the secondary sources used for reconstruction, and avoids specific equation-number pins. The construction is verified against the empirical-coverage tests (95% coverage on iid Gaussian + AR(1) — passes). Tracked as residual; fully closed when paywall access is obtained. |
| L-1-2 | minor | lit / cited | Module docstring References | Mertens 2002 SSRN abstract `1019823` formal citation present; Mertens-Opdyke variance form already cross-checked in Cycle 2 by [test_inference_stats.py](../../tests/unit/test_inference_stats.py). | Verified — no change. |
| L-1-3 | minor | lit / cited | Module docstring References | Hall 1992 §1.5, Davison & Hinkley 1997 §5.4 / eq. 5.10, Lahiri 2003 §6 — section-level pins not directly verified against primary PDFs in this revision. | Inline-resolved: the docstring uses section-level pins (not equation-number pins) where primary-PDF verification is incomplete; the verification gap is consistent with project precedent (cf. [hansen_spa.py](../../src/skie_ninja/inference/multipletest/hansen_spa.py) `P1-SPA-PDF-VERIFY` follow-up). |

### Verdict

`accept` per [audit-remediate-loop](file:///C:/Users/skoir/.claude/skills/audit-remediate-loop/SKILL.md) §"Exit check": no critical findings; F-1-2 + F-1-3 inline-remediated; L-1-1 verification-gap explicitly documented (the audit-remediate-loop §"Verification" rule sets `verification-gap` at severity `major` but allows acceptance when documented and tracked as a residual). Round-2 not warranted.

## Residual risk

1. **Subagent-toolchain unavailability** — the Round-1 audit was performed inline under the quant-auditor + literature-check rubrics rather than via independent Agent-tool subagent spawns. This is the protocol-deviation residual. The same constraint affected [audit_trail_2026-04-24_h050-aggregation-rule.md](audit_trail_2026-04-24_h050-aggregation-rule.md) and was treated identically there. Tracked as `P1-AUDIT-SUBAGENT-TOOLCHAIN-AVAILABILITY` (cross-cutting; affects every audit-remediate-loop invocation in this environment).
2. **Ledoit-Wolf 2008 PDF verification gap (L-1-1)** — full-text access blocked by ScienceDirect paywall at audit time. Empirical coverage validation (iid Gaussian + AR(1) at nominal 95%) compensates. Closes when paywall access is obtained. Tracked as `P1-LW2008-PDF-VERIFY` (new).
3. **Per-replicate bandwidth deviation (F-1-2)** — bandwidth held fixed across bootstrap replicates per the function docstring's documented deviation from LW2008 §3.1. Tracked as `P1-LW2008-PER-REPLICATE-BANDWIDTH` (new).

## New follow-ups

- `P1-LW2008-PDF-VERIFY` *(documentation)* — verify §3.1 construction details (canonical SE form, recommended block-length rule, recommended `B`) against the primary Ledoit-Wolf 2008 *J. Empirical Finance* PDF when paywall access is obtained; tighten the module docstring's section-level pins to equation-level pins.
- `P1-LW2008-PER-REPLICATE-BANDWIDTH` *(method-fidelity)* — implement an opt-in mode (`bandwidth_strategy="per_replicate"`) that re-selects the NW 1994 bandwidth on each bootstrap resample, matching LW2008 §3.1's literal prescription. Empirically compare against the fixed-bandwidth default on a representative panel; ADR if the difference exceeds Monte-Carlo noise.
- `P1-AUDIT-SUBAGENT-TOOLCHAIN-AVAILABILITY` *(cross-cutting protocol)* — surface the Agent / Task subagent-spawn primitive in this environment so [audit-remediate-loop](C:\Users\skoir\.claude\skills\audit-remediate-loop\SKILL.md) can be invoked with the prescribed independent-subagent pattern rather than the inline-self-audit substitution. Affects every audit-remediate-loop invocation in this CWD.

## Cited references (verified valid via DOI / publisher metadata where possible)

- Ledoit, O. & Wolf, M. 2008. "Robust performance hypothesis testing with the Sharpe ratio." *J. Empirical Finance* 15(5):850-859. https://doi.org/10.1016/j.jempfin.2008.03.002
- Politis, D. N. & Romano, J. P. 1994. "The Stationary Bootstrap." *J. American Statistical Association* 89(428):1303-1313. https://doi.org/10.1080/01621459.1994.10476870
- Politis, D. N. & White, H. 2004. "Automatic Block-Length Selection for the Dependent Bootstrap." *Econometric Reviews* 23(1):53-70. https://doi.org/10.1081/ETC-120028836
- Patton, A.; Politis, D. N. & White, H. 2009. "Correction to 'Automatic Block-Length Selection for the Dependent Bootstrap'." *Econometric Reviews* 28(4):372-375. https://doi.org/10.1080/07474930802459016
- Lahiri, S. N. 2003. *Resampling Methods for Dependent Data.* Springer, ISBN 978-0-387-00928-5. https://doi.org/10.1007/978-1-4757-3803-2 (Chapter 5 "Comparison of Block Bootstrap Methods" — block-bootstrap first-order asymptotic equivalence; Chapter 6 "Second-Order Properties" — Edgeworth-level corrections)
- Mertens, E. 2002. "Variance of the IID estimator in Lo (2002)." Working paper. https://ssrn.com/abstract=1019823
- Newey, W. K. & West, K. D. 1987. "A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix." *Econometrica* 55(3):703-708. https://doi.org/10.2307/1913610
- Newey, W. K. & West, K. D. 1994. "Automatic Lag Selection in Covariance Matrix Estimation." *Review of Economic Studies* 61(4):631-653. https://doi.org/10.2307/2297912
- Hall, P. 1992. *The Bootstrap and Edgeworth Expansion.* Springer, ISBN 978-0-387-94508-8. https://doi.org/10.1007/978-1-4612-4384-7
- Davison, A. C. & Hinkley, D. V. 1997. *Bootstrap Methods and their Application.* Cambridge UP, ISBN 978-0-521-57471-6. https://doi.org/10.1017/CBO9780511802843
- Jobson, J. D. & Korkie, B. M. 1981. "Performance Hypothesis Testing with the Sharpe and Treynor Measures." *J. Finance* 36(4):889-908. https://doi.org/10.1111/j.1540-6261.1981.tb04891.x
- Memmel, C. 2003. "Performance hypothesis testing with the Sharpe ratio." *Finance Letters* 1:21-23. (No DOI; original-source citation matches LW2008 §3.1 reference.)

## Round 2 — post-loop-verification (proper-subagent isolation)

**Context.** The Round-1 audit at this trail's `## Round-1` section was an inline self-audit performed without independent subagent isolation (the Agent / Task tool was not surfaced in this environment at Round-1 time). Per [audit-remediate-loop SKILL.md §40-43](C:\Users\skoir\.claude\skills\audit-remediate-loop\SKILL.md), audits MUST be performed by spawning `quant-auditor` and `literature-check` subagents through the Agent tool. This Round-2 corrective is the proper-isolated verification pass: independent quant-auditor + literature-check subagents were spawned at the parent-thread layer and the resulting findings were transmitted to this remediation pass for fix application + re-test.

**Findings transmitted from proper-isolated subagents.** Five major findings (F-PLV-2, F-PLV-3, F-PLV-5, L-1, L-2) plus four minor cleanups (F-PLV-1, F-PLV-6, F-PLV-7, F-PLV-8). The full module + tests + cited sources were re-verified end-to-end against the open-access [University of Zurich IEW Working Paper 320 mirror](https://www.econ.uzh.ch/apps/workingpapers/wp/iewwp320.pdf) — full-text extraction succeeded at remediation time and all four core method claims (studentized statistic at WP Eq. (6); circular block bootstrap at WP §3.2.2; HAC SE via `v_t = (r_a, r_a², r_b, r_b²)` parameterisation at WP Eq. (4)-(5); per-replicate `s(Δ̂*)` at WP §3.2.2 footnote 9 + Algorithm 3.1) verified against primary text.

| ID | Severity | Location | Remediation | Verification (URL) | Verdict |
|---|---|---|---|---|---|
| F-PLV-2 | major | [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) `_bootstrap_studentised_distribution` (NEW helper) | Added `bandwidth_strategy: Literal["per_replicate", "fixed_at_original"] = "per_replicate"` parameter; per-replicate is now the spec-faithful default. NW 1994 truncation lag is re-selected on each bootstrap resample's paired-difference series via `nw1994_bartlett_bandwidth`. Closed follow-up `P1-LW2008-PER-REPLICATE-BANDWIDTH`. New AR(1) ρ ∈ {0.3, 0.6, 0.8} sweep test `test_per_replicate_vs_fixed_bandwidth_coverage_ar1_sweep` records empirical coverage at α=0.05 within ±3pp (±5pp at ρ=0.8 for slow-mixing ESS reduction per Bartlett 1946 effective-sample-size formula). | LW2008 WP 320 §3.2.2 (per-replicate `s(Δ̂*)` per WP eq. (8) discussion); Lahiri 2003 §3.3 (bootstrap variance of Bartlett-kernel HAC estimators differs under fixed-vs-per-replicate bandwidth — methodologically real, not first-order asymptotically equivalent). https://www.econ.uzh.ch/apps/workingpapers/wp/iewwp320.pdf | accept |
| F-PLV-3 | major | [tests/unit/test_ledoit_wolf_2008.py](../../tests/unit/test_ledoit_wolf_2008.py) `test_studentised_vs_basic_percentile_widths_differ` (NEW) | Added direct studentised-vs-basic-percentile width-departure test on Student-t(df=4), n=120, B=4000 fixture. `_BASIC_PERCENTILE_DEPARTURE_FLOOR = 0.05` anchored in closed-form `t_{0.975, 4} ≈ 2.776` vs `z_{0.975} ≈ 1.960` quantile inflation (asymptotic departure ≈ 42%). Floor is well below the asymptotic bound but above MC noise at B=4000. Existing normal-quantile heavy-tail test retained as complementary check. | Hall 1992 §3.5 (studentized pivots can substantially differ from raw percentile pivots when the studentising factor is data-dependent); Davison & Hinkley 1997 §5.2 eq. 5.6 (basic-percentile pivots). https://doi.org/10.1017/CBO9780511802843 | accept |
| F-PLV-5 | major / verification-gap | [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) module docstring "Verification status" | Replaced paywall-blocked "Verification status" subsection with verified-against-WP-320 form. Pinned LW2008 WP 320 equation numbers (Eq. 1-2, 3-4, 5, 6) to matching implementation locations. Cited the published *J. Empirical Finance* version as canonical reference and the open-access WP 320 mirror as verification source per task brief. Closed follow-up `P1-LW2008-PDF-VERIFY`. New residual `P1-LW2008-CALIBRATION-VS-PW2004` logged for the LW2008 Algorithm 3.1 (iterated VAR(1) + residual stationary bootstrap calibration) vs project's PW2004 one-shot block-length selection. | LW2008 WP 320 (full text extracted via pdftotext at remediation time); cross-check vs published J. Empirical Finance abstract metadata at https://doi.org/10.1016/j.jempfin.2008.03.002 | accept |
| L-1 | major | [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) module docstring (3 locations) + this audit trail line 23 | Fixed Lahiri 2003 DOI: was `10.1007/978-1-4757-3805-2`, corrected to `10.1007/978-1-4757-3803-2` (3805 → 3803). Fixed ISBN: was `978-0-387-95441-7`, corrected to `978-0-387-00928-5` per Springer Series in Statistics catalog hardcover ISBN. | Crossref API: https://api.crossref.org/works/10.1007/978-1-4757-3803-2 returned title "Resampling Methods for Dependent Data", author "S. N. Lahiri", e-ISBN 9781475738032, publisher "Springer New York"; web search confirmed hardcover print ISBN 9780387009285 (https://www.amazon.com/Resampling-Methods-Dependent-Springer-Statistics/dp/0387009280, https://mitpressbookstore.mit.edu/book/9780387009285) | accept |
| L-2 | major | [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) module docstring (3 locations) + this audit trail line 23 | Replaced `§6` / `§6.1-§6.4` with `Chapter 5 "Comparison of Block Bootstrap Methods"` at all four locations. Added clarifying note that Chapter 6 "Second-Order Properties" is the Edgeworth-level location where the two methods may differ — so the §6 pin technically inverted the technical content. | Web search confirmed: Lahiri 2003 Chapter 5 = "Comparison of Block Bootstrap Methods" (Springer Nature Link chapter URL: https://link.springer.com/chapter/10.1007/978-1-4757-3803-2_5); search result text: "In Chapter 5 of the 2003 book, Lahiri compares the performance of the Moving Block Bootstrap (MBB), Nonoverlapping Block Bootstrap (NBB), Circular Block Bootstrap (CBB), and Stationary Bootstrap (SB) methods" | accept |
| F-PLV-1 | minor | [_sharpe_biased](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) | Added inline justification comment anchored in spec criterion 8 (vectorisation): the helper returns `(SR, mu, var)` triple in a single pass, avoiding two extra `mean`/`var` calls per resample under `n_bootstrap` repetitions. Cross-walk to the project-canonical `sample_sharpe` at [sharpe_ci.py](../../src/skie_ninja/inference/stats/sharpe_ci.py) explained. No functional change. | n/a (internal documentation only) | accept |
| F-PLV-6 | minor | [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) module docstring (NEW "Parameterisation cross-walk" subsection) | Added cross-walk between the impl's raw-moment parameterisation `θ = (μ_a, γ_a, μ_b, γ_b)` and the spec's centred-moment phrasing `(μ_a, σ²_a, μ_b, σ²_b)`. Equivalent under unit-Jacobian smooth bijection `(μ, γ) ↦ (μ, γ - μ²)`; HAC variance `∇f' Ψ ∇f` invariant. Raw-moment chosen because LW2008 WP Eq. (1)-(2) and the gradient at WP Eq. (4) are stated in raw moments (LW2008's "more convenient" formulation). | LW2008 WP 320 §3 "Solutions" preamble: "We find it somewhat more convenient to work with the uncentered second moments. So let γ_i = E(r_i²) and γ_n = E(r_n²)" (line 122 of WP text extraction). | accept |
| F-PLV-7 | minor | [tests/unit/test_ledoit_wolf_2008.py](../../tests/unit/test_ledoit_wolf_2008.py) `test_signature_and_dataclass` + `test_per_replicate_vs_fixed_bandwidth_coverage_ar1_sweep` + `test_studentised_vs_basic_percentile_widths_differ` | Decoupled data-RNG and bootstrap-RNG seeds in the new tests + the signature test: data drawn from `data_rng = default_rng(<seed_d>)`; bootstrap loop consumes `boot_rng = default_rng(<seed_b>)`. Avoids accidental coupling between sample path and resample sequence. | n/a (test-fixture hygiene per CLAUDE.md "Reproducibility" rule) | accept |
| F-PLV-8 | minor | [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) `DifferentialCIResult` | Added `n_degenerate_resamples: int = 0` field; incremented in both bootstrap-fail except blocks (zero-variance subseries from `_sharpe_biased` raise + degenerate gradient from `_hac_se_sharpe_difference` raise). Surfaced in `to_dict`. Signature-test asserts `>= 0`. | n/a (observability / instrumentation; documented as zero-not-NaN sentinel rationale per LW2008 WP §3.2.2 footnote 9) | accept |

### Verification posture (BLAS-pinned env)

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src \
  uv run --python 3.11 --extra dev pytest tests/unit/test_ledoit_wolf_2008.py -v
→ 18 passed in 560.39s (0:09:20)
```

Test count change: 14 → 18. New tests: `test_per_replicate_vs_fixed_bandwidth_coverage_ar1_sweep[0.3]`, `[0.6]`, `[0.8]` (parametrized; counts as 3); `test_studentised_vs_basic_percentile_widths_differ` (1).

### Ruff posture

```
PYTHONPATH=src uv run --python 3.11 --extra dev ruff check \
  src/skie_ninja/inference/stats/ledoit_wolf_2008.py \
  tests/unit/test_ledoit_wolf_2008.py
→ All checks passed!
```

(One PLR0915 was introduced by the per-replicate bandwidth refactor at the public API and resolved by extracting `_bootstrap_studentised_distribution` as a module-private helper; one PLR2004 + one PLC0415 were introduced in the new test and resolved via module-level constants `_AR1_RHO_HIGH`, `_AR1_COVERAGE_LB_SLOW`, `_AR1_COVERAGE_UB_SLOW`, `_BASIC_PERCENTILE_DEPARTURE_FLOOR` and a top-level import.)

### Verdict

`accept` — all 5 major findings remediated with primary-source verification, all 4 minor cleanups applied, 18/18 tests green, ruff clean. Closed follow-ups: `P1-LW2008-PDF-VERIFY`, `P1-LW2008-PER-REPLICATE-BANDWIDTH`. New residual: `P1-LW2008-CALIBRATION-VS-PW2004` (LW2008 Algorithm 3.1 iterated calibration vs project's one-shot PW2004 selection). Round-3 not warranted.

### New follow-ups

- `P1-LW2008-CALIBRATION-VS-PW2004` *(method-fidelity)* — LW2008 WP 320 Algorithm 3.1 specifies an iterated bootstrap calibration loop (VAR(1) + residual stationary bootstrap, K=5000 pseudo sequences) for block-length selection. Project substitutes Politis-White 2004 (+ PPW 2009 correction) one-shot data-driven selection. The two have the same first-order guarantee but differ in finite-sample behaviour. Empirical comparison on H050 panel + ADR if the difference exceeds Monte-Carlo noise.
