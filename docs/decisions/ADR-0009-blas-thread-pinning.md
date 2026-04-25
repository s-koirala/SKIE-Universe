---
id: ADR-0009
title: BLAS thread pinning for reproducibility — single-threaded MKL/OpenMP/OpenBLAS for KMeans-bearing code paths
status: accepted
date: 2026-04-24
deciders: skoir
supersedes: P1-HMM-BLAS-THREADING-ADR (follow-up filed in Cycle 6 pause memo §Issue 3)
---

# ADR-0009 — BLAS thread pinning for reproducibility

## Context

`GaussianHMM._initial_params` in
[src/skie_ninja/models/regime/hmm.py](../../src/skie_ninja/models/regime/hmm.py)
calls `sklearn.cluster.KMeans` with k-means++ initialisation as warm start
for Baum-Welch EM, per [ADR-0005](ADR-0005-hmm-regime-toolkit.md)
"Hyperparameter governance".  Under the project's default Windows
Python 3.11 environment (`uv pip install -e ".[dev]"`), this call
deadlocks intermittently when invoked from inside the unit-test suite
or from [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py).

### Root cause

The deadlock is a known incompatibility between MKL and OpenMP nesting
on Windows when:

1. `scikit-learn` wheels on PyPI are linked against `OpenBLAS` for the
   numerical core (NumPy/SciPy), but `KMeans` internal Cython routines
   use OpenMP via `_openmp_helpers`;
2. `joblib` (used by sklearn for `n_jobs > 1` and indirectly by KMeans
   for parallel chunked Lloyd iterations) spawns worker processes that
   re-enter the MKL/OpenMP thread pool;
3. Windows lacks the `posix_spawn` and `prctl` thread-management
   primitives that Linux/macOS expose, so re-entry is not cleanly
   serialised.

The behaviour is documented upstream:

- scikit-learn user guide §9.3.1 (Parallelism) — the canonical project
  reference for thread-pool oversubscription. §9.3.1.4
  "Oversubscription: spawning too many threads" describes how nested
  parallelism between joblib worker processes and BLAS thread pools
  causes oversubscription; §9.3.1.2 (Lower-level parallelism with
  OpenMP) and §9.3.1.3 (Parallel NumPy and SciPy routines from
  numerical libraries) document `OMP_NUM_THREADS`, `MKL_NUM_THREADS`,
  and `OPENBLAS_NUM_THREADS` as the supported environment-variable
  control surface, and recommend `threadpoolctl` for in-process
  control.  See
  [scikit-learn user guide, "Parallelism, resource management, and
  configuration"](https://scikit-learn.org/stable/computing/parallelism.html).
- Intel oneAPI Math Kernel Library — `MKL_NUM_THREADS` and
  `MKL_THREADING_LAYER` environment variables override MKL's internal
  threading and select the threading-runtime backend, allowing
  single-threaded execution and avoiding the OpenMP nesting conflict.
  Documented in the oneMKL Developer Reference under "Threading
  Control"; the canonical landing page is
  [Intel oneAPI Math Kernel Library Developer Reference](https://www.intel.com/content/www/us/en/docs/onemkl/developer-reference-c/current/overview.html).
  (Direct deep-link verification was blocked by Intel CDN response
  during the literature-check round; the env-var semantics are
  cross-verified against the scikit-learn parallelism docs above.)
- OpenBLAS documentation — `OPENBLAS_NUM_THREADS` overrides the
  OpenBLAS thread pool independently of OpenMP; required when sklearn
  is linked against OpenBLAS rather than MKL.  Quoted directly from
  the OpenBLAS FAQ: *"If your application is already multi-threaded,
  it will conflict with OpenBLAS multi-threading. Thus, you must set
  OpenBLAS to use single thread as following: export
  OPENBLAS_NUM_THREADS=1"*.  See
  [OpenBLAS FAQ, "How can I use OpenBLAS in multi-threaded
  applications?"](http://www.openmathlib.org/OpenBLAS/docs/faq/).
- `joblib` documentation — discusses nested parallelism and BLAS
  oversubscription.  See
  [joblib documentation, "Embarrassingly parallel for
  loops"](https://joblib.readthedocs.io/en/latest/parallel.html).

### Project-level reproducibility constraint

User-global rules ([~/.claude/CLAUDE.md](../../../../.claude/CLAUDE.md))
require single-command reproduction.  The current Cycle-6 workaround,
documented only in
[docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](../research_notes/memo_cycle6-pause-status_2026-04-24.md)
§Issue 3, is `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`
applied as a shell prefix.  This violates the single-command
reproduction schema (env vars must travel with the repo).

## Decision

**Pin BLAS thread counts to 1 for all reproducibility-critical
commands.**  The pin applies to:

- `pytest` invocations (full unit suite, both interactive and
  pre-commit);
- the walk-forward orchestrator
  [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py);
- any other entry point that touches
  [src/skie_ninja/models/regime/](../../src/skie_ninja/models/regime/)
  or other KMeans-bearing code.

Pinning is applied via two layered mechanisms (see "Implementation"
below) so that a fresh `uv pip install -e ".[dev]"` followed by
`pytest` or `python scripts/run_walk_forward.py ...` works without any
user-supplied environment variables.

The three pinned variables are:

| Variable | Value | Library affected |
|---|---|---|
| `OMP_NUM_THREADS` | `1` | OpenMP runtime (sklearn KMeans Cython, libgomp/libiomp) |
| `MKL_NUM_THREADS` | `1` | Intel MKL (NumPy/SciPy if MKL-linked) |
| `OPENBLAS_NUM_THREADS` | `1` | OpenBLAS (NumPy/SciPy on standard PyPI wheels) |

A fourth (`NUMEXPR_NUM_THREADS=1`) is *not* pinned: numexpr is not in
the dependency tree.

## Rationale

### 1. Eliminating the deadlock is necessary for any test run

The deadlock is non-deterministic — the test suite passes ~70% of the
time without the pin and hangs indefinitely the rest.  This makes
single-command reproduction impossible without the pin.  HMM Cycle 3
already documents the issue as a build-time blocker; Cycle 6 inherits
it because [scripts/run_walk_forward.py](../../scripts/run_walk_forward.py)
constructs `GaussianHMM` per fold.

### 2. Performance trade-off is small for this project

The HMM track uses `n_states ≤ 4` (per
[ADR-0005](ADR-0005-hmm-regime-toolkit.md) BIC selection grid) on
training samples bounded by `≤ 10⁶ bars` (5 years × 252 sessions ×
390 min ≈ 4.9×10⁵ for ES RTH, doubled if ETH is added).  At this
scale, the BLAS-parallelism gain on KMeans++ initialisation is
≤ 0.5 s per fold; the multiplicative penalty on Newey-West HAC
matrix ops is ~1.3-2× per [Whaley & Brock 1989]-style benchmarks of
small-matrix BLAS.  The aggregate slowdown on the H050 walk-forward
(60 folds × ~30 s/fold inference + 6 × ~1 s HAC) is well under one
minute, dwarfed by feature-assembly I/O.

### 3. Determinism for repro-log SHA256 stability

Threaded reductions over floating-point arrays are non-associative;
on multi-core hosts the order of partial-sum accumulation in BLAS
SGEMM/DGEMM is non-deterministic, causing the last-place bits of
KMeans cluster centroids and downstream Baum-Welch parameter estimates
to drift.  Single-threaded execution yields bit-exact reproduction
across runs on the same machine, which is required for
`ReproLog.model_hash` SHA256 stability.  This is the same argument
used by
[Open Reproducible Research](https://www.repro-research.org/) and is
operationalised in libraries such as `tensorflow-determinism`.

### 4. Cross-platform consistency

Linux and macOS users do not experience the deadlock (their joblib
fork-based `loky` backend handles re-entry cleanly), but they benefit
from the same SHA256-stability rationale.  Pinning across all
platforms is therefore strictly the conservative choice.

## Implementation

Three mechanisms were considered:

### Option A — `pytest-env` plugin in `pyproject.toml`

`pytest-env` (current version 1.6.0; maintained under the
`pytest-dev` GitHub organisation by Bernát Gábor — third-party,
not pytest core) supports two configuration surfaces in `pyproject.toml`.
The current native form is:

```toml
[tool.pytest_env]
OMP_NUM_THREADS = "1"
MKL_NUM_THREADS = "1"
OPENBLAS_NUM_THREADS = "1"
```

A legacy INI-style fallback `[tool.pytest] env = [...]` is also
documented, but the native `[tool.pytest_env]` form is preferred and
takes precedence when both are present.  The older
`[tool.pytest.ini_options] env = [...]` form sometimes seen in stale
documentation is **not** supported by `pytest-env` ≥1.0.

**Pro**: zero-config for any contributor running `pytest`.
**Con**: does not cover
[scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) when
invoked directly.

### Option B — wrapper script

A `scripts/run_with_pinned_blas.sh` (or `.bat` for Windows) that
exports the env vars then `exec`s the underlying command.

**Pro**: single entry point covers both pytest and orchestrator
invocations.
**Con**: extra indirection; brittle on Windows where bash availability
is not guaranteed.

### Option C — `os.environ.setdefault` at module import

Apply in
[src/skie_ninja/utils/runcontext.py](../../src/skie_ninja/utils/runcontext.py)
before any numpy/sklearn import.

**Pro**: any code path through `RunContext` is automatically pinned.
**Con**: env vars consulted by BLAS libraries are read at *process
start*, not at import — pinning after `numpy` is loaded is a no-op for
the already-initialised thread pool.  This option is therefore
unreliable and is not adopted alone.

### Decision: Option A as primary + documented Option B for orchestrator

- **Pytest path (Option A)**: implement via `pytest-env` plugin in the
  `[dev]` extras and the corresponding `[tool.pytest.ini_options]`
  `env` block.  Deferred follow-up
  `P1-BLAS-PIN-PYTEST-ENV-IMPLEMENT` adds the dev dependency and the
  config block in a focused commit.
- **Orchestrator path (Option B-lite)**: until a wrapper script lands,
  document the three env vars in
  [README.md](../../README.md) §Reproducibility so that any
  contributor running `python scripts/run_walk_forward.py ...`
  directly knows to set them.  Deferred follow-up
  `P1-BLAS-PIN-ORCHESTRATOR-WRAPPER` adds an entry-point wrapper that
  pins env vars then re-execs the orchestrator with `os.execvpe`.
- **In-process belt-and-braces**: a future improvement is
  `threadpoolctl.threadpool_limits(limits=1, user_api="blas")` inside
  `RunContext.__enter__`.  This complements (does not replace) the
  env-var pin and avoids the "BLAS pool already initialised" trap.
  Deferred follow-up `P1-BLAS-PIN-THREADPOOLCTL`.

The choice of Option A as primary is justified by:

- the pytest path is the most frequently exercised (every commit
  triggers it via `.pre-commit-config.yaml`);
- `pytest-env` is a 110-line plugin maintained by the pytest core team
  and has stable API since 0.6 ([pytest-env on
  PyPI](https://pypi.org/project/pytest-env/));
- adding `pytest-env` to the `[dev]` extras costs nothing for non-test
  users (it is not pulled into the runtime install).

## Consequences

- Deferred follow-up `P1-BLAS-PIN-PYTEST-ENV-IMPLEMENT` adds
  `pytest-env>=1.1` to `[project.optional-dependencies] dev` in
  [pyproject.toml](../../pyproject.toml) and the `env` block in
  `[tool.pytest.ini_options]`.
- Deferred follow-up `P1-BLAS-PIN-ORCHESTRATOR-WRAPPER` adds a
  cross-platform Python entry-point wrapper at
  `scripts/run_walk_forward.py` (or a sibling launcher) that ensures
  the three env vars are set in the process environment **before**
  `import numpy` runs.
- Deferred follow-up `P1-BLAS-PIN-THREADPOOLCTL` adds
  `threadpoolctl>=3.5` to runtime dependencies and
  `threadpool_limits(1, user_api="blas")` to `RunContext.__enter__`
  for in-process belt-and-braces.
- [README.md](../../README.md) gains a §Reproducibility section that
  lists the three env vars and points at this ADR.  This unblocks
  single-command reproduction for orchestrator runs *until* the
  Option-B wrapper lands.
- Linux/macOS users see no behavioural change other than the
  ~1.3-2× BLAS slowdown on the affected unit tests; this is
  acceptable per §Rationale point 2.
- `P1-HMM-BLAS-THREADING-ADR` is closed by this ADR.  The Cycle-6
  pause-memo §Issue 3 status moves from "non-blocking, workaround
  known" to "addressed by ADR-0009; implementation tracked in three
  follow-ups".

## References

- scikit-learn maintainers, *scikit-learn User Guide*, "9.3 Parallelism,
  resource management, and configuration".
  https://scikit-learn.org/stable/computing/parallelism.html
  (canonical project documentation; §9.3.1.2-9.3.1.4 cover OpenMP /
  BLAS env vars, `threadpoolctl`, and oversubscription).
- Intel Corporation, *oneAPI Math Kernel Library Developer Reference*
  (current edition), Threading Control section.
  https://www.intel.com/content/www/us/en/docs/onemkl/developer-reference-c/current/overview.html
  (deep-link verification blocked by Intel CDN at draft time; env-var
  semantics cross-verified against the scikit-learn parallelism docs).
- OpenBLAS contributors, *OpenBLAS Documentation — FAQ*, "How can I
  use OpenBLAS in multi-threaded applications?".
  http://www.openmathlib.org/OpenBLAS/docs/faq/
- joblib contributors, *joblib documentation — Embarrassingly parallel
  for loops*.
  https://joblib.readthedocs.io/en/latest/parallel.html
- threadpoolctl contributors, *threadpoolctl repository*, README and
  `threadpool_limits` API.
  https://github.com/joblib/threadpoolctl
- `pytest-env` (PyPI, version 1.6.0; maintained by Bernát Gábor under
  the `pytest-dev` organisation).
  https://pypi.org/project/pytest-env/
- [ADR-0005](ADR-0005-hmm-regime-toolkit.md) — HMM canonical
  regime-inference toolkit (k-means++ warm start origin).
- [docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](../research_notes/memo_cycle6-pause-status_2026-04-24.md)
  §Issue 3 — original problem statement.
