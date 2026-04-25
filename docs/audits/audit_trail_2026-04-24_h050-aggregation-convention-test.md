---
name: P1-H050-AGGREGATION-CONVENTION-TEST audit trail
description: Audit-remediate-loop trail for the H050 aggregation-rule addendum r2 §5.2 verification gate (machine-precision equivalence test).
type: project
hypothesis_id: H050
follow_up_id: P1-H050-AGGREGATION-CONVENTION-TEST
date: 2026-04-24
owner: skoir
status: closed
exit_verdict: accept
rounds_used: 2
---

# Audit trail — `P1-H050-AGGREGATION-CONVENTION-TEST` (2026-04-24)

## Scope

Implementation of the verification gate mandated by [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) §5.2: a machine-precision unit test asserting numerical equivalence between (i) the addendum-bound rule's aggregate `R_p(t) = 0.5 * R_ES(t) + 0.5 * R_NQ(t)` with `R_i(t) = exp(r_i(t)) - 1` and (ii) the direct arithmetic-return aggregate. Evidence-bar-blocking for the first H050 walk-forward run governed by addendum r2.

## Artifacts

- [tests/unit/test_h050_aggregation_convention.py](../../tests/unit/test_h050_aggregation_convention.py) — new test file, 14 tests across 6 test functions (parametrised seeds + parametrised gate states give the full count).
- [src/skie_ninja/inference/stats/return_conventions.py](../../src/skie_ninja/inference/stats/return_conventions.py) — new helper module exposing `log_to_arithmetic` (numpy `expm1`-backed) and `arithmetic_to_log` (numpy `log1p`-backed); will be reused under follow-up `P1-H050-DUAL-SYMBOL-ORCHESTRATOR`.
- [src/skie_ninja/inference/stats/__init__.py](../../src/skie_ninja/inference/stats/__init__.py) — re-exports of the two helpers.

## Subagent dispatch — protocol-compliance note

The user-mandated procedure
([~/.claude/skills/audit-remediate-loop/SKILL.md](../../../.claude/skills/audit-remediate-loop/SKILL.md))
requires spawning `quant-auditor` and `literature-check` subagents via
the `Agent` tool with `subagent_type` parameters. **The `Agent` tool was
not present in the runtime's tool list for this session** (verified via
`ToolSearch` queries `select:*` and keyword searches `agent`,
`subagent dispatch`, `task`; the only matches were `TaskStop`,
`mcp__r-studio__create_task_list`, and `mcp__scheduled-tasks__*`,
none of which dispatch `~/.claude/agents/*.md` definitions). The
`Skill` tool's `audit-loop` invocation enqueued the skill but the
underlying subagent dispatch was not executed inside this session
(no `Agent` call ID returned).

**Fallback discipline (transparent):** Round-1 and Round-2 audits were
performed by the lead agent under explicit auditor scope — re-reading
the artifact under the [quant-auditor.md](../../../.claude/agents/quant-auditor.md)
ruleset (§"Scope of review" 1-7) and the
[literature-check.md](../../../.claude/agents/literature-check.md)
citation-validation ruleset, with structured-JSON findings recorded
inline in the session transcript. This is a known weaker pattern than
isolated subagent dispatch — the lead agent shares latent state with
the producer — and is recorded here as a **process residual** for the
parent agent to escalate if independent subagent dispatch becomes
mandatory before evidence-bar gate review.

The post-loop verification of [docs/audits/audit_trail_2026-04-24_blas-threading-adr.md](audit_trail_2026-04-24_blas-threading-adr.md)
Round 3 set the precedent that inline-audit substitution must be
disclosed and re-verified under proper isolation when the dispatch
tool returns. The same disclosure applies here. If a future session
where `Agent` is available re-runs the audit pass and surfaces new
critical/major findings, this trail is to be appended with the
remediation under a Round-3 entry.

## Round 1 — Implementation + audit

### Round 1 — implementation summary

- Created [tests/unit/test_h050_aggregation_convention.py](../../tests/unit/test_h050_aggregation_convention.py) with six test functions covering addendum §5.2 contract:
  1. `test_log_to_arithmetic_per_bar_equivalence` (parametrised across 4 seeds 2024..2027, n=1000 bars/symbol).
  2. `test_first_order_log_arithmetic_divergence` (n=5000, sigma=1e-3, asserts naive log-aggregate diverges from correct arithmetic-aggregate by O(r^2/2) per Campbell-Lo-MacKinlay 1997 §1.4).
  3. `test_inactive_symbol_handling_sub_rule_3_3a` (parametrised over 4 gate states (g_ES, g_NQ) ∈ {(1,1), (1,0), (0,1), (0,0)}, asserts sub-rule 3.3a contract: hold inactive in cash, no renormalisation; explicit foreclosure check against sub-rule 3.3b).
  4. `test_per_bar_varying_gate_state` (n=500, per-bar-varying gate states).
  5. `test_zero_return_edge_case` (constant prices, asserts exact `0.0` aggregate).
  6. `test_large_return_excluded_or_handled` (n=200, |r| <= 0.05, regime-boundary documentation).
  Plus two defensive helpers `test_log_to_arithmetic_rejects_2d_input` and `test_arithmetic_to_log_rejects_2d_input`.
- Tolerance `atol = 1e-15`, `rtol = 0.0` justified at module scope by Goldberg 1991 §2 float64 unit roundoff `u = 2^-53 ~= 1.11e-16` plus a few-ulp accumulation through `diff(log(.))` + `expm1(.)`.
- Created [src/skie_ninja/inference/stats/return_conventions.py](../../src/skie_ninja/inference/stats/return_conventions.py) with `log_to_arithmetic(r) -> expm1(r)` and `arithmetic_to_log(r) -> log1p(r)`. Helper placement (vs inline-in-test) was chosen because follow-up `P1-H050-DUAL-SYMBOL-ORCHESTRATOR` will need to import the same conversion.
- Re-exported from [src/skie_ninja/inference/stats/__init__.py](../../src/skie_ninja/inference/stats/__init__.py).
- Tests run: 14/14 passed under `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src uv run --python 3.11 --extra dev pytest tests/unit/test_h050_aggregation_convention.py -v`. Ruff: clean (after autofix on import-sorting and a file-level `# ruff: noqa: N806, PLR2004` block with documented justification — addendum's binding mathematical notation distinguishes log returns `r_*` from arithmetic returns `R_*`, and physical regime boundaries are anchored in surrounding comments).

### Round 1 — quant-auditor findings (in-session fallback; see "Subagent dispatch" note)

Findings reported as structured JSON; severity per audit-remediate-loop SKILL §3:

| ID | Severity | Location | Issue (one-line) | Disposition |
|---|---|---|---|---|
| F-1-1 | major | [tests/unit/test_h050_aggregation_convention.py:300-324](../../tests/unit/test_h050_aggregation_convention.py) | `test_per_bar_varying_gate_state` computes `R_p` and `R_p_ref` with the IDENTICAL expression — tautology, no independent cross-check. | Remediated R2 — replaced `R_p_ref` with explicit Python-loop elementwise reference materialising sub-rule 3.3a one bar at a time. |
| F-1-2 | major | [tests/unit/test_h050_aggregation_convention.py:225-232](../../tests/unit/test_h050_aggregation_convention.py) | "Positive bias from Jensen on expm1" attribution wrong — Jensen bounds f(E[X]) vs E[f(X)], not per-element f(x)-x sign. | Remediated R2 — replaced with correct Taylor-remainder mechanism: `expm1(r) - r = r^2/2 + r^3/6 + O(r^4) >= 0` for the leading term; under symmetric returns `E[r^2/2] = sigma^2/2 > 0`. |
| F-1-3 | minor | [tests/unit/test_h050_aggregation_convention.py:215-222](../../tests/unit/test_h050_aggregation_convention.py) | `50.0 * sigma * sigma` upper bound is loose by ~25x; magic factor without empirical-tail justification. | Remediated R2 — replaced with `16 * sigma^2` anchored to Gumbel-tail max ~ `sqrt(2 * log(n)) ~ 4 sigma` for n=5000 Gaussian extremes. |
| F-1-4 | minor | [tests/unit/test_h050_aggregation_convention.py:382-383, 397-398](../../tests/unit/test_h050_aggregation_convention.py) | Magic value `0.06` in stability bound, unmotivated finite-sample envelope above the 0.05 input bound. | Remediated R2 — replaced with `np.expm1(0.05) + 1e-12` (analytic envelope from `expm1(0.05) ~ 0.05127`). |
| F-1-5 | minor | [tests/unit/test_h050_aggregation_convention.py:418](../../tests/unit/test_h050_aggregation_convention.py) | Magic value `1e-4` regime-boundary threshold without analytic anchor. | Remediated R2 — replaced with `0.5 * 0.04^2 / 2` lower bound from leading Taylor term at the 0.04-floor empirical max-|r|. |
| F-1-6 | minor | [src/skie_ninja/inference/stats/return_conventions.py:34-58](../../src/skie_ninja/inference/stats/return_conventions.py) | Docstring does not call out why `np.expm1` is used over `np.exp(r) - 1`. | Remediated R2 — added catastrophic-cancellation explanation per Goldberg 1991 §3.2. |
| F-1-7 | minor | [tests/unit/test_h050_aggregation_convention.py:75-89](../../tests/unit/test_h050_aggregation_convention.py) | Sigma docstring math `12% / sqrt(...)` claim off by 1.6x (3.83e-4, not 6e-4). | Remediated R2 — recomputed correctly; reframed sigma=1e-3 as conservative round-number anchor in the empirical regime, not a precise analytic match. |

### Round 1 — literature-check findings

| ID | Severity | Location | Issue (one-line) | Disposition |
|---|---|---|---|---|
| L-1-1 | minor | [tests/unit/test_h050_aggregation_convention.py:186](../../tests/unit/test_h050_aggregation_convention.py) | "Campbell-Lo-MacKinlay 1997 §1.4 eq. 1.4.4" specific-equation reference is unverified at edition-level granularity. | Remediated R2 — dropped equation number; cite §1.4 at chapter level; load-bearing identities stated explicitly in the docstring. |
| L-1-2 | minor | [src/skie_ninja/inference/stats/return_conventions.py:21](../../src/skie_ninja/inference/stats/return_conventions.py) | Goldberg 1991 §1.2 reference for unit roundoff: §2 (IEEE Standard) is the primary anchor, §1.2 covers relative error generically. | Remediated R2 — citation now reads "§2". |
| L-1-3 | info | n/a | CLM 1997 §1.4 attribution is correct; positive verification. | No action needed. |

### Round 1 — primary-source verifications (WebFetch / Crossref)

- Campbell-Lo-MacKinlay 1997. ISBN-13 `978-0-691-04301-2` confirmed via Princeton University Press catalog (https://press.princeton.edu/books/hardcover/9780691043012/the-econometrics-of-financial-markets); copyright year 1997, December 1996 release. DOI `10.1515/9781400830213` confirmed via Crossref API (`api.crossref.org/works/10.1515/9781400830213`).
- Goldberg 1991. DOI `10.1145/103162.103163` confirmed via Crossref API: title "What every computer scientist should know about floating-point arithmetic", *ACM Computing Surveys* 23(1):5-48, March 1991.

## Round 2 — Remediation + re-audit

### Round 2 — remediation summary

All 7 quant-auditor findings (2 major + 5 minor) and 2 literature-check minors remediated. Specific edits:

- F-1-1: [tests/unit/test_h050_aggregation_convention.py:300-336](../../tests/unit/test_h050_aggregation_convention.py) `test_per_bar_varying_gate_state` now constructs `R_p_ref` via an explicit `for t in range(n)` loop with `if g[t] == 1.0` branching, materialising sub-rule 3.3a one bar at a time. The orchestrator-style vectorised aggregate is asserted equal to this independent reference.
- F-1-2: [tests/unit/test_h050_aggregation_convention.py:225-238](../../tests/unit/test_h050_aggregation_convention.py) Jensen attribution removed; replaced with the Taylor-expansion mechanism (`expm1(r) - r = r^2/2 + r^3/6 + O(r^4)`, leading term non-negative; symmetric-returns expectation `E[r^2/2] = sigma^2/2 > 0`).
- F-1-3: same docstring; `expected_per_bar_bound = 16.0 * sigma * sigma` with Gumbel-tail derivation for n=5000.
- F-1-4: [tests/unit/test_h050_aggregation_convention.py:393-401](../../tests/unit/test_h050_aggregation_convention.py) `arith_envelope = np.expm1(extreme_r_bound) + 1e-12`.
- F-1-5: [tests/unit/test_h050_aggregation_convention.py:425-432](../../tests/unit/test_h050_aggregation_convention.py) `aggregate_div_lower_bound = 0.5 * (0.04 ** 2) / 2.0`.
- F-1-6: [src/skie_ninja/inference/stats/return_conventions.py:42-49](../../src/skie_ninja/inference/stats/return_conventions.py) docstring expanded with catastrophic-cancellation note per Goldberg 1991 §3.2.
- F-1-7: [tests/unit/test_h050_aggregation_convention.py:78-89](../../tests/unit/test_h050_aggregation_convention.py) sigma docstring recomputed (`0.12 / sqrt(252 * 6.5 * 60) ~= 3.83e-4`), reframed as conservative round-number anchor.
- L-1-1: [tests/unit/test_h050_aggregation_convention.py:24-37](../../tests/unit/test_h050_aggregation_convention.py) module docstring's CLM 1997 reference now explicit about edition-portability ("equation numbers within §1.4 vary across editions; the load-bearing identity ... is stated at chapter-level granularity").
- L-1-2: same docstring, Goldberg cite now "§2 (IEEE Standard)".

### Round 2 — re-audit findings (in-session fallback)

quant-auditor: zero new findings. All Round-1 majors remediated; minors absorbed without regression.
literature-check: zero new findings. §-level granularity holds; both DOIs verified.

```json
{
  "round": 2,
  "findings": [],
  "residual_risk": "All Round-1 majors and minors remediated. Tests still pass; ruff clean. Independent elementwise reference in test_per_bar_varying_gate_state now provides genuine cross-validation. Taylor-remainder mechanism replaces incorrect Jensen attribution. All numeric thresholds tied to documented analytic bounds (Gumbel-tail max, expm1 envelope, leading Taylor term)."
}
```

### Round 2 — verification gates

- Tests: 14/14 passed (same count as Round 1; structural changes preserved coverage).
- Ruff: clean across all three modified files.
- Reproducibility: tests run under fixed seed (parametrised seeds 2024..2027 for the equivalence contract; per-test fixed seeds for the others). No RNG state leakage between tests.

## Exit verdict

**Accept** at end of Round 2. Zero critical/major findings remaining. Loop terminated within 3-round cap.

## Residuals (process)

1. **Subagent-dispatch fallback** — Round-1 and Round-2 audits performed in-session by the lead agent under explicit auditor scope (no isolated `Agent` tool invocation; tool not present in runtime). If a future session re-runs the audit pass under proper isolation and surfaces new critical/major findings, append a Round-3 entry here with the remediation. Process residual; not a finding against the deliverable.
2. **CI integration** — addendum §5.2 mandates the test be CI-blocking for any commit touching `r_bar` computation in [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) or its successor module. Hooking this test into the project's pre-commit / CI pipeline is out-of-scope for this follow-up and is captured under a new follow-up `P1-H050-AGGREGATION-CONVENTION-CI-WIRING` (to be added by the parent agent to [CLAUDE.md](../../CLAUDE.md) blocker inventory in a separate workstream — this trail does not modify [CLAUDE.md](../../CLAUDE.md) per task constraint).

## Cross-references

- Addendum r2: [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) §5.2.
- Sibling audit trail (parallel workstream): `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` is its own deliverable not addressed by this trail; see addendum §5.3.
- Resolution memo: [docs/research_notes/memo_h050-aggregation-rule_2026-04-24.md](../research_notes/memo_h050-aggregation-rule_2026-04-24.md).
- Project [CLAUDE.md](../../CLAUDE.md) blocker inventory entry `P1-H050-AGGREGATION-CONVENTION-TEST` is closed by this trail.
