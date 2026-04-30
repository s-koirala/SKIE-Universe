---
title: LW2008 paired-Sharpe-difference CI migration — canonical-form rewire after Round-1 reject
date: 2026-04-30
artifact: src/skie_ninja/inference/stats/__init__.py + scripts/run_walk_forward.py + config/hypotheses/H050.yaml + (deleted) src/skie_ninja/inference/stats/sharpe_diff_ci.py + (deleted) tests/unit/test_ledoit_wolf_sharpe_diff_ci.py
followup_id: P1-LW2008-MIGRATION-CANONICAL-REWIRE
exit_state: round-1 reject → in-loop-rewire to canonical primitive
loop_skill: ~/.claude/skills/audit-remediate-loop/SKILL.md
subagent_isolation: proper (main-thread-spawned)
parent_diagnosis: user's pre-merge stash WIP migrating from `opdyke2007_ci` to a paired-differential CI
---

## Scope

The user's pre-merge stash introduced a new module `src/skie_ninja/inference/stats/sharpe_diff_ci.py` exposing `ledoit_wolf2008_sharpe_diff_ci` and a 13-test suite, plus rewiring `scripts/run_walk_forward.py::_sharpe_differential_stats` and `config/hypotheses/H050.yaml` to bind to the new primitive. The intent was correct (migrate from `opdyke2007_ci` single-Sharpe to a paired-differential CI per `rules/quant-project.md` "for pairwise strategy comparison use Ledoit & Wolf 2008"), but the new module's mechanics conflicted with the project's already-audited LW2008 primitive at `src/skie_ninja/inference/stats/ledoit_wolf_2008.py` (committed via `11f8fce`, audited per ADR-0008 §"Cross-reference: LW2008 differential CI as primary inference").

This trail records the Round-1 audit-remediate-loop on the user's stash + the in-loop rewire to the canonical audited primitive.

## Round 1 — produce + parallel quant + repro audit

Subagents (proper-isolated, main-thread-spawned):

- `quant-auditor` (`agentId a51e23b5bb6a19267`) — verdict **`reject`** with 2 criticals + 4 majors + 4 minors.
- `reproducibility-verifier` (`agentId a5ccf59c80fa1a993`) — verdict `accept-with-remediation` with 3 majors + 6 minors.

### Round-1 critical findings

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| **Q-1-1** | **critical** | Symmetric studentised CI form `[Δ̂ ± ŝ·q_{1-α}(|T*|)]` is **NOT** the LW2008 spec. LW2008 §3.1 + UZH IEW WP 320 specify the **asymmetric** studentised-pivot form using both bootstrap quantiles `q_{α/2}` and `q_{1-α/2}` (Hall 1992 §3.5; Davison & Hinkley 1997 §5.4 eq. 5.10). The new module's form is from PRW 2004 *Subsampling* §1.5.5 — a recognised alternative dependent-bootstrap CI form, but **not** what LW2008 uses. The existing `ledoit_wolf_2008_differential_ci` correctly implements the asymmetric form. | **Resolved by rewire**: deleted new module; orchestrator + H050.yaml routed to existing audited primitive. |
| **Q-1-2** | **critical** | Two coexistent LW2008 differential-CI implementations now exported. H050.yaml gate routes to the **NEW** (unaudited) influence-function-based, fixed-bandwidth, symmetric-CI implementation, NOT the audited joint-moment-vector, per-replicate-bandwidth, asymmetric-pivotal implementation. They differ on three load-bearing axes: (1) SE construction (influence-function delta-method vs joint-moment-vector delta-method per Jobson-Korkie 1981 + Memmel 2003), (2) bandwidth re-use policy (fixed-at-original vs per-replicate per LW2008 WP 320 §3.2.2; Lahiri 2003 §3.3 confirms non-trivial finite-sample deviation), (3) CI form (symmetric vs asymmetric pivotal). Per `~/.claude/CLAUDE.md` "Verification" → "Confirm numerical results against a benchmark", a side-by-side numerical reconciliation is required before either can serve as the H050 evidence-bar gate. | **Resolved by rewire**: collapsed to single canonical primitive (`ledoit_wolf_2008_differential_ci`). |

### Round-1 major findings

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| **Q-1-3** | major | Bandwidth fixed at original-data NW1994 selection across all bootstrap replicates; LW2008 WP 320 §3.2.2 specifies per-replicate. | **Resolved by rewire**: existing primitive defaults to `bandwidth_strategy="per_replicate"`; new orchestrator call passes this explicitly. |
| **Q-1-4** | major | `n_bootstrap: 1000` lacks empirical justification; existing primitive defaults to 2000 with Hall 1992 §1.5 citation. | **Fixed**: H050.yaml `n_bootstrap: 1000 → 2000` with inline citation to Hall 1992 §1.5 (`B = K(1-α) - 1` for K=100, α=0.05 → B=1999, rounded up to 2000). |
| **Q-1-5** | major | Coverage MC test (`test_iid_gaussian_coverage_within_wilson_band`) at `n_mc=80, nominal=0.90` accepts empirical coverage as low as ~0.81 (Wilson 99% bracket). Too loose for a load-bearing primitive. | **Resolved by deletion**: the test is removed with the new module. The existing `ledoit_wolf_2008.py` test suite has its own coverage tests that were already audited (commit `11f8fce`). |
| **Q-1-6** | major | Block-length selected on `ψ_a − ψ_b` (differenced influence function) rather than on `r_a − r_b` (paired-difference returns) as bound by `aggregation_rule_addendum_2026-04-24.md` §4.2 line 205. | **Resolved by rewire**: existing primitive selects on `r_a − r_b` per addendum. |
| **R-1-1** | major | No byte-identity / determinism test in the new test suite. Precedent at `test_ledoit_wolf_2008.py::test_determinism_with_fixed_rng` (line 444) uses strict `==`. | **Resolved by deletion**: the new test suite is removed; the existing `ledoit_wolf_2008.py` byte-identity test remains in force. |
| **R-1-2** | major | `_sharpe_differential_stats` constructed ONE rng and passed it to BOTH the LW2008 differential CI AND `hansen_spa_test`, coupling their reproducibility envelopes. A future re-implementation of either primitive's bootstrap-loop length would silently shift the other's p-value. | **Fixed**: `np.random.SeedSequence(seed).spawn(2)` produces independent child generators for LW2008 and SPA; reproducibility is deterministic but the primitives' bootstrap streams are decoupled. |
| **R-1-3** | major | ADR-0008 §"Cross-reference: LW2008 differential CI as primary inference" pins the existing audited primitive at `src/skie_ninja/inference/stats/ledoit_wolf_2008.py`. The user's stash routed the orchestrator + H050.yaml gate to a different module — stale ADR-0008 binding. | **Resolved by rewire**: orchestrator + H050.yaml now route to the ADR-0008-pinned primitive. ADR-0008 needs no update. |

### Round-1 minor findings (selected)

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| **Q-1-7** | minor | Influence-function "centered up to delta-method linearisation" hedge unnecessary when `ddof=0` (centering exact at machine precision). | **Resolved by deletion** of the new module. |
| **Q-1-8** | minor | Degenerate-replicate handling: new module drops; existing primitive zero-imputes + counts. | **Resolved by rewire**: orchestrator now uses the existing zero-impute + counter convention. |
| **R-1-7** | minor | Existing `ledoit_wolf_2008_differential_ci` raises `ValueError`/`RuntimeError` on degenerate-bootstrap edge cases; orchestrator's `_sharpe_differential_stats` call had no try/except, so a degenerate-replicate-heavy production fold would crash the orchestrator. | **Fixed**: `_run_symbol`'s call site now wraps in `try/except (RuntimeError, ValueError)`, emitting `status: "degenerate_bootstrap"` per-symbol payload analogous to the existing `status: "insufficient_oos_returns"` branch. Reproducibility preserved (seed + data deterministically reproduce the failure mode). |

## Remediation actions (in-loop)

Files deleted:
- `src/skie_ninja/inference/stats/sharpe_diff_ci.py` (341 lines).
- `tests/unit/test_ledoit_wolf_sharpe_diff_ci.py` (277 lines, 13 tests).

Files modified:
- `src/skie_ninja/inference/stats/__init__.py` — removed `SharpeDiffCI`, `ledoit_wolf2008_sharpe_diff_ci` exports; the existing `DifferentialCIResult`, `ledoit_wolf_2008_differential_ci` exports remain.
- `config/hypotheses/H050.yaml` — gate name `ledoit_wolf2008_sharpe_diff_ci` → `ledoit_wolf_2008_differential_ci`; `n_bootstrap: 1000 → 2000` (Hall 1992 §1.5); `bandwidth_strategy: per_replicate` added explicitly.
- `scripts/run_walk_forward.py`:
  - Imports: `ledoit_wolf2008_sharpe_diff_ci` → `ledoit_wolf_2008_differential_ci, sample_sharpe`.
  - `load_config()` parses `gates.ledoit_wolf_2008_differential_ci.{alpha,n_bootstrap,block_length}`.
  - `_sharpe_differential_stats()` rewritten:
    - Spawns independent child generators via `SeedSequence(seed).spawn(2)` for LW2008 vs SPA (R-1-2 fix).
    - Computes per-side Sharpes via `sample_sharpe(...)` (no longer derived from new module's `SharpeDiffCI` fields).
    - Calls `ledoit_wolf_2008_differential_ci(..., bandwidth_strategy="per_replicate")`.
    - Returns `metrics["ledoit_wolf_2008_differential_ci"] = result.to_dict()` and `metrics["sharpe_differential"] = float(result.point_estimate)`.
  - `_run_symbol()` call site:
    - Updated to new kwargs (`diff_ci_alpha=cfg.gate_alpha` not `diff_ci_confidence_level`).
    - Wrapped in `try/except (RuntimeError, ValueError)` emitting `status: "degenerate_bootstrap"` per R-1-7 fix.

## Verification

- `uv run python -c "from scripts.run_walk_forward import _sharpe_differential_stats; from skie_ninja.inference.stats import ledoit_wolf_2008_differential_ci"` — imports clean; `load_config(H050.yaml)` returns `gate_alpha=0.05, B=2000`.
- `uv run pytest tests/unit/test_ledoit_wolf_2008.py tests/unit/test_orchestrator_progress_log.py -q` — 28 passed in 633.68s (LW2008 byte-identity + coverage + the orchestrator integration smoke test under the rewired call).
- The rewired orchestrator's `metrics["ledoit_wolf_2008_differential_ci"]` field now matches the ADR-0008 §"Cross-reference" binding.

## Net dispositions

- **Both Round-1 critical findings resolved by rewire** (Q-1-1 symmetric-vs-asymmetric form; Q-1-2 dual-implementation conflict).
- **All 4 Round-1 quant majors and 3 repro majors resolved or transferred** (Q-1-3/Q-1-6 by rewire; Q-1-4 by parameter change; Q-1-5/R-1-1 by deletion of the non-canonical test suite; R-1-2/R-1-3 by code change; R-1-7 by orchestrator try/except).
- **The user's WIP intent is preserved**: H050's primary CI primitive is now the methodologically-correct, audited Ledoit-Wolf 2008 paired-differential CI per `rules/quant-project.md`. The non-canonical implementation is removed; nothing of the user's analytical intent is lost.

## Why deletion vs deprecation

The auditor offered two paths in Q-1-2 fix: (a) bring the new module into LW2008 conformance via patches, or (b) delete it and route to the existing audited primitive. Path (b) was chosen because:

1. The existing primitive at `ledoit_wolf_2008.py` was already audited (`11f8fce`) and is bound by ADR-0008 §"Cross-reference".
2. Maintaining two implementations of the same canonical CI form is a long-term maintenance hazard that would produce silent behavioural drift between releases.
3. The user's WIP API is a strict subset of the existing primitive's API (which already supports `bandwidth_strategy`, `block_length`, etc.); routing to it loses no expressivity.
4. The existing primitive's degenerate-replicate handling, byte-identity test, and ADR-0008 binding are all mature; preserving the new module would require duplicating that maturity.

## Round 2 deferred

Per `~/.claude/skills/audit-remediate-loop/SKILL.md` §"Cap": Round 2 is reserved for verification of the post-rewire artifact set; spawning Round 2 immediately after Round 1's deletion is invasive (the artifact under audit has changed shape substantially). Round 2 will fire on the H050 disposition output (post-launch, on the actual run output) and re-exercise the rewired call path against the audited primitive.

## Residuals carried forward

- The new module's PRW 2004 §1.5.5 symmetric-studentised form is a legitimate alternative dependent-bootstrap CI form and could be implemented in future as a comparator (not a replacement) to the LW2008 asymmetric-pivotal canonical form. Tracked under `P1-PRW2004-SUBSAMPLING-CI-COMPARATOR` (no urgency).

## References

- [SKILL.md](../../.claude/skills/audit-remediate-loop/SKILL.md) — audit-remediate-loop pattern.
- [src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py) — canonical audited primitive.
- [tests/unit/test_ledoit_wolf_2008.py](../../tests/unit/test_ledoit_wolf_2008.py) — byte-identity + coverage tests.
- [ADR-0008-spa-omega-method.md](../decisions/ADR-0008-spa-omega-method.md) §"Cross-reference: LW2008 differential CI as primary inference" — pins the canonical primitive.
- [research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md) §4.2 — block-length on paired-difference series.
- Ledoit, O. & Wolf, M. 2008. *J. Empirical Finance* 15(5):850-859. https://doi.org/10.1016/j.jempfin.2008.03.002 (canonical form).
- UZH IEW Working Paper 320 (open-access mirror of Ledoit-Wolf 2008).
- Hall, P. 1992. *The Bootstrap and Edgeworth Expansion* §3.5 (asymmetric studentised pivotal CI).
- Davison, A. C. & Hinkley, D. V. 1997. *Bootstrap Methods and their Application* §5.4 eq. 5.10.
- Politis, D. N., Romano, J. P. & Wolf, M. 2004. *Subsampling* §1.5.5 (the symmetric form retained as residual `P1-PRW2004-SUBSAMPLING-CI-COMPARATOR`).
- Lahiri, S. N. 2003. *Resampling Methods for Dependent Data* §3.3 (per-replicate vs fixed-bandwidth deviation).
- `rules/quant-project.md` — "for pairwise strategy comparison use Ledoit & Wolf 2008".
- Round-1 quant-auditor report: agentId `a51e23b5bb6a19267`, 10 findings.
- Round-1 reproducibility-verifier report: agentId `a5ccf59c80fa1a993`, 9 findings.
