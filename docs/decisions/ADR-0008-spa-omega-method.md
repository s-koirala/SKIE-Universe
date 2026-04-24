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

As documented in the Cycle 5 audit trail (L-1-8 discussion) and noted by
Hansen (2005, JBES 23(4), §2.2), using the same bootstrap draws for both
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
| `M ≥ 2` (multi-strategy) | **`bootstrap`** | Hansen (2005) §2 explicitly recommends shared bootstrap indices across strategies to preserve cross-sectional dependence; HAC treats each series independently and loses this; the coupling bias is diluted across M terms |

For **H050 Cycle 6**, `M = 1` → use `omega_method="hac"`.

## Rationale

### 1. Hansen 2005 §2.2 — coupling bias

Hansen (2005) JBES 23(4):365-380, §2.2 states the bootstrap variance estimator
is used because it accounts for the dependence structure across strategies via
the shared resampling indices.  For `M = 1` this advantage does not exist — a
single strategy has no cross-strategy dependence to preserve — so the only
effect is the coupling bias, which is eliminated by HAC.

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
