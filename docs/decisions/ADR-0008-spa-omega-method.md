---
id: ADR-0008
title: SPA omega estimator — bootstrap coupling vs HAC decoupled, per hypothesis universe size
status: accepted
date: 2026-04-24
deciders: skoir
supersedes: P1-SPA-HAC-DEFAULT-ADR (follow-up filed in Cycle 5 audit trail)
---

# ADR-0008 — SPA omega estimator selection

## Context

`hansen_spa_test` supports two options for the long-run variance (LRV) estimator
`ω̂_k²` used to studentize the performance differential `d̄_k`:

- **`omega_method="bootstrap"` (current function default)**: computes
  `ω̂_k² = Var_b(√n · d̄_k^{*b})` over the same `B` bootstrap replications
  used to build the null distribution.  This is the convention of the
  Hansen-Lunde MulCom reference implementation.
- **`omega_method="hac"`**: uses a Newey-West HAC long-run variance estimator
  (NW 1994 data-dependent bandwidth per `skie_ninja.inference.stats.hac`)
  computed once from the observed `d_k` series, independent of the bootstrap
  draws.

### Coupling concern

As documented in the Cycle 5 audit trail (L-1-8 discussion) and consistent
with the bootstrap implementation discussion in Hansen (2005, JBES 23(4), §3),
using the same bootstrap draws for both
`ω̂_k²` and the null-distribution max causes a mild **downward bias** in
p-values at finite `B`.  The bias is:

  p-value bias ≈ O(1/√B)

At `B = 1000` and `p ≈ 0.05`, the bias is approximately 0.03 — non-negligible
for a tight `α = 0.05` gate.  The bias direction is conservative (inflates
the threshold to reject H₀), but conservatism is undesirable when the goal
is to detect a genuine signal rather than suppress false positives.

## Decision

**Two-tier rule based on universe size `M` (number of strategies entering SPA):**

| Universe size | `omega_method` | Rationale |
|---|---|---|
| `M = 1` (single strategy) | **`hac`** | No cross-strategy dependence to preserve via shared bootstrap indices; HAC decouples MC error cleanly; bias elimination matters for tight α |
| `M ≥ 2` (multi-strategy) | **`bootstrap`** | Hansen (2005) §3 describes bootstrap implementation using shared resampling indices across strategies to preserve cross-sectional dependence; HAC treats each series independently and loses this; the coupling bias is diluted across M terms |

For **H050 Cycle 6**, `M = 1` → use `omega_method="hac"`.

## Rationale

### 1. Hansen 2005 §3 — coupling bias

Hansen (2005) JBES 23(4):365-380, §3 (Bootstrap Implementation) discusses the
bootstrap variance estimator and its relationship to the shared resampling
indices across strategies.  For `M = 1` no cross-strategy dependence exists —
a single strategy has no cross-sectional dependence to preserve via shared
indices — so the coupling bias (O(1/√B) at finite B) is the only effect,
and it is eliminated by HAC.

### 2. NW-HAC variance is consistent under H₀

The Newey-West (1994) HAC estimator is consistent for the LRV under weak
serial dependence (NW 1994 Review of Economic Studies 61(4):631-653;
Andrews 1991 Econometrica 59(3):817-858).  The bandwidth is selected by the
NW 1994 data-dependent rule already implemented in
`skie_ninja.inference.stats.hac`.

### 3. `omega_method="bootstrap"` retained as function default

The function signature `hansen_spa_test(..., omega_method="bootstrap", ...)`
retains `"bootstrap"` as the default to match MulCom conventions for
multi-strategy use.  Per-hypothesis overrides are declared in the hypothesis
config (e.g., `H050.yaml`, field `gates.hansen_spa.omega_method`).

### 4. Practical impact for H050

H050 enters the SPA with `M = 1` strategy at Cycle 6.  As the strategy
universe accumulates (H051, H052a added to the SPA family in future cycles),
the H050 retrospective SPA runs will transition to `omega_method="bootstrap"`
to preserve cross-strategy dependence.  The transition threshold is `M ≥ 2`;
record in the hypothesis register cross-reference at that time.

## Consequences

- `H050.yaml` gains a field `gates.hansen_spa.omega_method: hac`.
- `run_walk_forward.py` reads `omega_method` from the config and passes it
  to `hansen_spa_test`.
- No change to `hansen_spa.py`; the default remains `"bootstrap"`.
- `P1-SPA-HAC-DEFAULT-ADR` is closed by this ADR.
- When H051 / H052a join the SPA family, create a combined multi-strategy
  SPA run with `omega_method="bootstrap"` and document in those hypotheses'
  pre-registration.

## Single-strategy degenerate handling (|M|=1)

This subsection closes follow-up `P1-H050-SPA-M1-DEGENERATE` (filed
2026-04-24).

### Background

[scripts/run_walk_forward.py](../../scripts/run_walk_forward.py) calls
`hansen_spa_test` on H050's single-strategy panel: at Cycle 6 the
hypothesis universe has `m = 1` candidate (the H050 gated strategy
relative to its unconditional benchmark). Hansen 2005 §2 frames the
SPA composite null as

  H_0 : max_{k = 1, ..., m} E[d_{k,t}] <= 0,

which is *fundamentally* a multi-strategy construction — the
`max` over `k` plus the data-dependent recentering (§2.4) is the
machinery that makes SPA more powerful than White 2000 Reality
Check while remaining robust to inclusion of strictly-dominated
alternatives. With `m = 1` the max collapses to a single term
and the "best-of-family" semantics disappear.

The user-global rule `~/.claude/rules/quant-project.md` §Inference
binds Hansen 2005 SPA as the canonical multiple-testing procedure
*across strategies*; a single-statistic invocation falls outside
that binding.

### Mathematical reduction

For `m = 1` the test statistic
`T_SPA = max_k max(0, sqrt(n) * d_bar_k / omega_k)`
collapses to

  T_SPA = max(0, sqrt(n) * d_bar / omega),

i.e., a one-sided studentised statistic for `H_0 : E[d] <= 0`. The
bootstrap p-value
`p = (1/B) #{ b : T^{*b} >= T_SPA }`
is exactly the upper-tail mass of a one-sided studentised stationary-
bootstrap test on the single relative-performance series, equivalent
in construction to the studentised pivotal CI of Hall 1992 §3.5 /
Davison & Hinkley 1997 §5.4 (one-sided, recentered at the chosen
`g`). This is well defined and not statistically wrong — it is simply
not a *multi-strategy* test.

### Variant collapse

Hansen 2005 §2.4 recentering terms `g_k` for the three variants are:

| Variant | `g_k` definition | `m = 1` behaviour |
|---|---|---|
| SPA_l | `max(d_bar_k, 0)` | `g = max(d_bar, 0)` |
| SPA_c | `d_bar_k` if `sqrt(n) d_bar_k / omega_k >= -sqrt(2 log log n)` else `0` | `g = d_bar` if non-degenerate, else `0` |
| SPA_u | `d_bar_k` | `g = d_bar` |

The variants do **not** all collapse to a single p-value. They split
by sign-and-magnitude regime of `d_bar`:

| Regime | SPA_l | SPA_c | SPA_u | p-values |
|---|---|---|---|---|
| `d_bar >= 0` | `d_bar` | `d_bar` | `d_bar` | identical |
| `0 > studentised >= -threshold` | `0` | `d_bar` | `d_bar` | SPA_l differs |
| `studentised < -threshold` | `0` | `0` | `d_bar` | SPA_u differs |

In the regime of practical interest for a *gate* (`d_bar > 0`, i.e.,
the strategy's sample mean is positive) all three variants collapse
to the same recentering and yield identical p-values. In the
negative-`d_bar` regimes the p-value separation is a numerical
artefact of the recentering family — for a single column there is no
"strictly-dominated alternative" to wash out, so the SPA_l/SPA_c/SPA_u
distinction loses its Hansen 2005 §1 motivation. The reported
ordering `p_lower <= p_consistent <= p_upper` from the existing
test suite still holds at `m = 1` (it follows from the construction,
not multi-strategy semantics).

### Decision

**Pass-through is the chosen behaviour** (option (a) from the
follow-up ticket):

1. `hansen_spa_test` accepts `m = 1` and runs the full machinery.
2. A `SingleStrategySPAWarning` (subclass of `UserWarning`) is
   emitted at function entry, surfacing the degenerate invocation
   to code reviewers and downstream log scrapers without halting
   execution.
3. The reported `p_value` is interpretable as a one-sided
   studentised stationary-bootstrap p-value for `H_0 : E[d] <= 0`.
4. The three variant p-values (`p_value_lower`, `p_value`,
   `p_value_upper`) are populated as documented; consumers should
   read `p_value_consistent` (the default) as the single reported
   number for an `m = 1` invocation. The bracket between
   `p_value_lower` and `p_value_upper` is mechanically valid but
   not interpretable as a "best-of-family" range.

### Why pass-through, not skip-or-error

Considered alternatives:

- **(b) Skip SPA, use LW2008 only.** Rejected — keeping the SPA
  call exercises the same bootstrap path that will be reused once
  `m >= 2`, which preserves audit-trail continuity across the
  H050 → multi-strategy transition. The orchestrator already runs
  both LW2008 (primary) and SPA (corroborative) on the H050
  differential, per the cross-reference in the next subsection.
- **(c) Raise.** Rejected — would force a config branch every
  time a hypothesis lands as the first member of a family. The
  warning is the right level: visible to reviewers, ignored by
  no-op consumers, capturable by `pytest.warns` for verification.

The pass-through choice is consistent with Hansen's own SPA
implementation behaviour: the MulCom Ox reference and the `arch`
Python package (Sheppard) accept `m = 1` without raising.

### Cross-reference: LW2008 differential CI as primary inference

Follow-up `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` was closed at commit
`11f8fce` (audit trail
[docs/audits/audit_trail_2026-04-24_lw2008-differential-ci.md](../../docs/audits/audit_trail_2026-04-24_lw2008-differential-ci.md)).
The orchestrator now has a callable
[Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002)
studentised time-series bootstrap CI for the H050 paired
differential statistic
`T_H050 = SR(r_p_gated) − SR(r_p_uncond)` at
[src/skie_ninja/inference/stats/ledoit_wolf_2008.py](../../src/skie_ninja/inference/stats/ledoit_wolf_2008.py)
(`ledoit_wolf_2008_differential_ci`).

For the H050 single-statistic case the project hierarchy is:

1. **Primary inference** — LW2008 differential CI (`m = 1` is the
   *natural* construction for a paired difference of two Sharpe
   ratios; the studentised bootstrap is a single-statistic test by
   design).
2. **Corroborative** — `m = 1` SPA pass-through (warning emitted;
   reported alongside LW2008 in the audit log; not the gate
   decision-maker).

The project's quant-project.md multi-strategy SPA binding takes
effect when sibling hypotheses (H051, H052a, ...) accumulate into
a strategy universe with `m >= 2`. At that transition:

- The H050 retrospective SPA reruns under `omega_method="bootstrap"`
  per the table in the original ADR-0008 decision matrix.
- `SingleStrategySPAWarning` is no longer emitted (the
  `m == 1` runtime check passes silently).
- LW2008 retains its role for *pairwise* comparisons within the
  family per quant-project.md §Inference; SPA covers the
  family-wide null.

### Code-level invariants (added 2026-04-24)

- `src/skie_ninja/inference/multipletest/hansen_spa.py` exports
  `SingleStrategySPAWarning(UserWarning)`. The class hierarchy
  ensures `pytest.warns(UserWarning)` and structured-log scrapers
  (e.g., `warnings.captureWarnings(True)`) capture it without
  bespoke filter rules.
- A `warnings.warn(..., SingleStrategySPAWarning, stacklevel=2)`
  call at function entry fires whenever the input matrix has
  shape `(n, 1)`. The `stacklevel=2` attribution points to the
  caller's frame, which is what reviewers want when inspecting
  `pytest -W error::SingleStrategySPAWarning` failures.
- The function does NOT raise on `m == 1`; existing behaviour
  ("`m >= 1` is accepted") is preserved.
- Test coverage at
  [tests/unit/test_inference_hansen_spa.py](../../tests/unit/test_inference_hansen_spa.py)
  asserts (i) the warning is emitted exactly once, (ii) the
  reported p-value matches a one-sided one-column manual bootstrap,
  and (iii) `m >= 2` invocations do not emit the warning.

### Verification status

The mathematical reduction at `m = 1` is mechanical (single-term
max plus continuity in `m`) and does not require primary-source
verification beyond the existing module docstring. Section-level
labels for §2 and §2.4 of Hansen 2005 follow the secondary
summaries already cited in
`src/skie_ninja/inference/multipletest/hansen_spa.py`'s "Verification
status of primary-source claims" section (open follow-up
`P1-SPA-PDF-VERIFY`). Direct PDF access to the JBES paywall was
attempted on 2026-04-24 and blocked; the SSRN preprint was
HTTP 403; no §2.4-specific text on the `m = 1` case is therefore
quoted here. The pass-through behaviour matches the `arch` Python
package's `SPA` class (Kevin Sheppard) and the Hansen-Lunde MulCom
Ox reference, both of which accept `m = 1` without raising.
