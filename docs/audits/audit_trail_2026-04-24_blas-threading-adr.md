---
name: BLAS thread-pinning ADR audit trail
description: Audit-remediate-loop trail for ADR-0009 (BLAS thread pinning for reproducibility), 2026-04-24.
type: audit
status: closed
date: 2026-04-24
deliverable: docs/decisions/ADR-0009-blas-thread-pinning.md
---

# Audit-remediate-loop trail — ADR-0009 BLAS thread pinning

**Deliverable**: [docs/decisions/ADR-0009-blas-thread-pinning.md](../decisions/ADR-0009-blas-thread-pinning.md)
**Trigger**: closes follow-up `P1-HMM-BLAS-THREADING-ADR` (Cycle-6 pause memo §Issue 3).
**Cap**: 3 rounds per [~/.claude/CLAUDE.md](../../../../.claude/CLAUDE.md) §Agentic Iteration.
**Outcome**: closed at end of Round 2 — accept with documented residual on Intel-CDN deep-link.

## Round 0 — input

Problem statement: [docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](../research_notes/memo_cycle6-pause-status_2026-04-24.md) §Issue 3.

> `sklearn.KMeans.fit_predict` inside `GaussianHMM._initial_params`
> ([src/skie_ninja/models/regime/hmm.py](../../src/skie_ninja/models/regime/hmm.py))
> deadlocks under default MKL/OpenMP threading on Windows.  Workaround:
> `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.
> Candidate follow-up `P1-HMM-BLAS-THREADING-ADR`.

Project-level constraint: [CLAUDE.md](../../CLAUDE.md) reproducibility
schema requires single-command reproduction without out-of-tree env-var
setup.

## Round 1 — draft

Drafted ADR-0009 with sections Status / Context / Decision / Rationale /
Implementation / Consequences / References.  Numbering verified against
[docs/decisions/](../decisions/): ADR-0001 through ADR-0008 present;
ADR-0009 is next.  Style aligned with ADR-0007 and ADR-0008
(YAML front-matter, single H1, accepted status, reference links to
prior ADRs and Cycle pause memo).

[README.md](../../README.md) updated with a §Reproducibility section
linking ADR-0009 + listing the three env vars and a Python-import
ordering caveat; ADR table extended with ADR-0007/0008/0009 rows
(previously stopped at ADR-0006).

## Round 1 — literature-check audit

Spawned `lit-check` skill (manually executed via WebFetch + `gh` CLI)
to verify upstream citations.  Verified:

- ✅ joblib documentation URL
  (https://joblib.readthedocs.io/en/latest/parallel.html) loads and
  documents oversubscription.
- ✅ threadpoolctl repository URL
  (https://github.com/joblib/threadpoolctl) is the canonical repo;
  `threadpool_limits(limits=1, user_api="blas")` API matches README.
- ✅ `pytest-env` exists on PyPI (current 1.6.0, maintainer Bernát
  Gábor under `pytest-dev` organisation — third-party, not pytest
  core).

Findings (severity / id / description / verdict):

### F-1-1 critical — sklearn issue numbers cited do not exist or are unrelated

ADR-0009 Round-1 draft cited sklearn issue #20712 plus a "broader
cluster #16707, #18701, #19829".  Verified via `gh issue view`:

| Issue | Actual title | Match? |
|---|---|---|
| #20712 | "[DO NOT MERGE] Test pytest output can be colored with bash on Windows" | No — totally unrelated |
| #16707 | "Function parametrize_with_checks does not accept classes" | No |
| #18701 | "Allow permutation_importance to accept multiple scorers in `scoring`" | No |
| #19829 | (does not exist; 404) | No |

These citations are fabricated.  GitHub issue search for "KMeans
Windows deadlock", "OpenMP MKL deadlock", "BLAS threading deadlock",
"KMeans hang Windows", and "joblib loky openmp" against
`scikit-learn/scikit-learn` returned no high-quality canonical issue
suitable to cite.

**Verdict**: critical.  Replace with the canonical scikit-learn user
guide page §9.3 *"Parallelism, resource management, and
configuration"* (https://scikit-learn.org/stable/computing/parallelism.html),
which is the authoritative project source on env-var thread control,
oversubscription, and `threadpoolctl`.  Verified to exist and contain
the relevant content (§9.3.1.2 OpenMP, §9.3.1.3 BLAS env vars,
§9.3.1.4 oversubscription).

### F-1-2 major — `pytest-env` TOML syntax incorrect for current 1.x

ADR-0009 Round-1 Implementation §Option A used:

```toml
[tool.pytest.ini_options]
env = ["OMP_NUM_THREADS=1", ...]
```

Verified against `pytest-env` 1.6.0 PyPI page and
github.com/pytest-dev/pytest-env README: the current native form is

```toml
[tool.pytest_env]
OMP_NUM_THREADS = "1"
```

A legacy INI fallback `[tool.pytest] env = [...]` is also documented.
The `[tool.pytest.ini_options] env = [...]` form is **not** supported
by `pytest-env` ≥ 1.0.

**Verdict**: major.  Replace TOML example with the native form; add a
note distinguishing native vs legacy and disclaim the older form.

### F-1-3 major — OpenBLAS wiki URL deprecated

ADR-0009 Round-1 cited
`https://github.com/OpenMathLib/OpenBLAS/wiki/Faq#how-to-set-the-number-of-threads`.
Verified: that wiki page now redirects readers to
`http://www.openmathlib.org/OpenBLAS/docs/faq/` ("The content from
this page has been moved to the Markdown docs under `docs/` in this
repo").

**Verdict**: major.  Update URL; add a verbatim quote from the new
canonical FAQ ("export OPENBLAS_NUM_THREADS=1") to lock the
citation against future moves.

### F-1-4 minor — Intel oneMKL deep-link unverifiable

ADR-0009 Round-1 cited a versioned Intel deep-link:
`https://www.intel.com/content/www/us/en/docs/onemkl/developer-reference-c/2024-0/setting-the-number-of-threads-using-an-openmp-environment.html`.
WebFetch returned HTTP 403 (Intel CDN blocks programmatic fetches);
unable to positively confirm page existence/content.

**Verdict**: minor.  Replace with the stable `current/overview.html`
landing page and document the verification gap inline; the env-var
semantics are independently verified against the scikit-learn
parallelism docs (which document the same `MKL_NUM_THREADS` /
`MKL_THREADING_LAYER` semantics).

### F-1-5 accept — joblib URL

joblib URL verified.  Section name in Round-1 ADR ("Thread-based
parallelism vs process-based parallelism") was a real older heading
but the page has reorganised; reword to a less brittle anchor
("Embarrassingly parallel for loops" — the page's H1).

### F-1-6 accept — threadpoolctl

API surface and URL match.  No change needed.

## Round 2 — remediation

Applied F-1-1 (replaced fabricated sklearn issues with sklearn
parallelism docs canonical reference), F-1-2 (corrected pytest-env
TOML syntax to native `[tool.pytest_env]`), F-1-3 (updated OpenBLAS
URL + added verbatim quote), F-1-4 (replaced Intel deep-link with
stable landing-page URL + documented verification gap), F-1-5
(reworded joblib section reference).  Edits in
[docs/decisions/ADR-0009-blas-thread-pinning.md](../decisions/ADR-0009-blas-thread-pinning.md):

- Context §"Root cause" bullet list rewritten — sklearn parallelism
  docs replaces fabricated issue cluster; OpenBLAS URL updated +
  quoted; Intel oneMKL link replaced + flagged.
- Implementation §Option A TOML example corrected to
  `[tool.pytest_env]` native form with note on legacy fallback.
- References block fully rewritten to match the corrected citations
  and remove fabricated issue numbers.

## Round 2 — verification

- All Round-1 critical/major findings addressed; corrections are
  drop-in replacements that did not change the substantive Decision
  or Rationale.
- Re-verified by re-reading the updated ADR end-to-end: every URL
  surfaced in §Context and §References either passed live verification
  in Round 1 or carries an inline verification-gap note (only the
  Intel deep-link).
- No new claims introduced in Round 2 that require fresh verification.

**Verdict**: clean.  No new findings.

## Round 3 — not entered

End-of-Round-2 verification produced no new findings; loop terminates
at Round 2 per [~/.claude/CLAUDE.md](../../../../.claude/CLAUDE.md)
§Agentic Iteration cap rule (3-round cap, exit on accept).

## Residuals

- **Intel oneMKL deep-link verification gap**: Intel CDN responded HTTP
  403 to direct WebFetch.  Documented inline in ADR §References; the
  env-var semantics (`MKL_NUM_THREADS`, `MKL_THREADING_LAYER`) are
  cross-verified against the scikit-learn parallelism docs.  No
  follow-up filed — re-verification is a routine exercise that can
  be performed manually if needed.
- **No empirical reproduction of the deadlock from inside this audit
  trail**: the deadlock is documented in the Cycle-6 pause memo by
  the user; no fresh repro performed.  Acceptable: the ADR formalises
  an already-in-use workaround.

## Spawned follow-ups

Recorded in ADR §Consequences:

- `P1-BLAS-PIN-PYTEST-ENV-IMPLEMENT` — add `pytest-env>=1.6` to `[dev]`
  extras and `[tool.pytest_env]` block in
  [pyproject.toml](../../pyproject.toml).
- `P1-BLAS-PIN-ORCHESTRATOR-WRAPPER` — add cross-platform Python
  entry-point wrapper that pins env vars before `numpy` import and
  re-execs the orchestrator.
- `P1-BLAS-PIN-THREADPOOLCTL` — add `threadpoolctl>=3.5` runtime dep
  and `threadpool_limits(1, user_api="blas")` to
  `RunContext.__enter__` for in-process belt-and-braces.

## Status

- ADR-0009 status: **Accepted**.
- README.md updated with §Reproducibility section + ADR-0007/0008/0009
  rows in the ADR table.
- `P1-HMM-BLAS-THREADING-ADR` closed by ADR-0009; pause-memo §Issue 3
  status moves from "non-blocking, workaround known" to "addressed by
  ADR-0009; implementation tracked in three follow-ups".  CLAUDE.md
  cleanup deferred per task brief constraints.
- No commit made (per task brief — edit/create files only).
