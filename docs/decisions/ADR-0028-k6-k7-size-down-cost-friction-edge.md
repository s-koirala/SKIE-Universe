---
id: ADR-0028
title: K-6/K-7 size-down-vs-block enforcement mode + cost-friction-dominated-edge annotation (empirical decomposition of H062 v3)
status: accepted
date: 2026-05-19
deciders: skoir
supersedes: []
proposes_amendments_to:
  - ADR-0025 §D-1 — runtime kill-switch coverage extended with operator-selectable enforcement mode (`"block"` default = legacy behavior bit-equivalent; `"size_down"` new alternative). ADR-0025 itself is preserved verbatim per ADR-0013 §4.1 non-loss; this ADR adds two new fields (`k6_enforcement`, `k7_enforcement`) to `KillSwitchRuntimeConfig` with backward-compatible defaults.
  - ADR-0014 §3.2 13-table format — Table 9 ("Methodological-correctness annotations") gains two new annotations: `kill-switch-mode-{block, size-down}` and `cost-friction-dominated-edge-{present, absent, n/a}`. Cascade via `P1-ADR-0028-TEMPLATE-CASCADE`.
  - ADR-0017 §3 / ADR-0014 §3.2 — annotation grammar adds the cost-friction-dominated-edge KPI per §D-2 below. Cascade via `P1-ADR-0028-CLAUDE-MD-CASCADE`.
preserves_immutability_of:
  - ADR-0025 (preserved verbatim; this ADR EXTENDS via opt-in field additions, does not supersede)
  - All hypothesis design.md §1-§7 (per ADR-0013 §"Frozen pre-registration amendment" §1-§7 immutability discipline)
  - All historical audit trails, ReproLogs, sidecars, KPI report cards, promotion logs, NinjaScript strategies, design.md §17 revision logs (per ADR-0013 §4.1 non-loss mandate)
  - ADR-0013 §1 stage-progression model + §4 non-loss mandate + §5 NinjaScript-terminus mandate (preserved unchanged)
  - ADR-0024 §D-2 / §D-3 / §D-4 opt-in framing — preserved verbatim; the new `k6_enforcement` / `k7_enforcement` fields default to `"block"` (existing semantic); `"size_down"` is opt-in per design.md §11.1 declaration
  - ADR-0017 §4.1 drawdown-constrained Kelly sizing primitive + ADR-0017 §5 K-1..K-8 kill-switch enumeration — preserved verbatim; the size-down mode reuses the existing position-size computation pipeline with a multiplicative shrinkage factor
  - All Phase O.13 v3 + Phase O.10 v2 KPI report cards (sidecar bit-exactness preserved by `"block"` default)
---

# ADR-0028 — K-6/K-7 size-down-vs-block enforcement mode + cost-friction-dominated-edge annotation

## Context

### Why this ADR exists

Per [ADR-0027 §D-3 empirical-before-amendment sequencing rule](ADR-0027-operational-discipline-bounded-exploration.md), an ADR codifying a claim about strategy / mechanism behavior MUST be preceded by an empirical decomposition validating the underlying claim. This ADR is the canonical instantiation of that rule: the load-bearing empirical claim — that kill-switch K-6/K-7 in their current block-entry form is asymmetric — has been decomposed and partially validated by the H062 v3 primitive-attribution ablation, closed in commit [1adc62a](https://github.com/s-koirala/SKIE-Universe/commit/1adc62a) (subsequent SHA backfill at [63a22d2](https://github.com/s-koirala/SKIE-Universe/commit/63a22d2)). The investigation memo is at [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md); the audit trail is at [docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md](../audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md).

### Empirical anchor — H062 v3 ablation findings

The 4-cell smoke ablation (canonical substrate SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`; 4-cell inner-CV × 4 symbols × 130 folds × rng_seed `20260514` per [config/hypotheses/H062.yaml](../../config/hypotheses/H062.yaml)) yielded two empirically-distinct failure modes:

| Ablation | Config | Run ID | Realized OOS basket % | MPPM(ρ=1) | Win rate | n_trades | K-6+K-7 fires |
|---|---|---|---:|---:|---:|---:|---:|
| A0 (all OFF) | smoke baseline | `5e52f0b7ddd94ecea3187566c0e255d0` | **+261.88** | +0.0966 | 34.24% | 10,326 | 0 |
| A1 (cost-only) | `--cost-model conservative_prior` | `edbc263e7ed14ca3a2252a10e94e45c3` | **−100.00** | **−1.1347** | 31.17% | 10,326 | 0 |
| A2 (kill-switch-only) | `--enable-kill-switch-runtime` | `d01ca71b7ee34863b4219003d9a05601` | **−21.91** | −0.0212 | **29.84%** | 7,127 | 8,927 |
| A3 (equity-rebase-only) | `--enable-equity-rebase-current` | `5589abf07c85471a84f75feead6e0174` | +211.02 | +0.0847 | 34.20% | 10,342 | 0 |
| Ref-v3 (all 3 ON) | full v3 cell | `154237b365794244974068402b377191` | **−99.9995** | **−1.0447** | 27.15% | 7,201 | 8,845 |

Two structurally-distinct failure modes are empirically established:

1. **COST DOMINANCE**: A1 cost-only saturates the basket at the literal −100% floor (Δ −361.88 pp vs A0; bit-equal to the cumulative v3 effect within rounding). Per-trade conservative-prior cost subtraction × ~10,326 trades × ~6 OOS years × H062's marginal mean-edge (full-grid v2 MPPM CI [−0.34, +0.54] covers zero) produces total bankruptcy. Mechanism is *cost-flips-marginal-winners-to-losers*: A1 has IDENTICAL trade activity to A0 (both 10,326 trades) yet win rate drops 34.24% → 31.17%. Cost is a per-trade additive drag, not a behavioral asymmetry.

2. **KILL-SWITCH ASYMMETRY**: A2 kill-switch-only blocks ~31% of all entries (10,326 → 7,127) via 8,927 K-6+K-7 fires; win rate drops 34.24% → 29.84%. The blocked subset skews toward winners — the kill-switch acts on past P/L (daily/weekly drawdown breaches) but the forward entries it blocks include winning trades that would have recovered the drawdown. K-6 and K-7 cannot distinguish "drawdown about to deepen" from "drawdown about to mean-revert." The asymmetric-blocking pathology produces a Δ −283.79 pp vs A0 baseline.

The two failure modes operate on different dimensions: cost on *every trade's P/L*; kill-switch on *entry/no-entry decisions during drawdown sessions*. The saturation-floor at −100% on A1 prevents Σ-of-singletons additivity from predicting the cumulative v3 effect.

### Operator intuition (2026-05-19) vs empirical refinement

The operator 2026-05-19 framed the issue as "Phase O.13 v3 muted profits while drawdowns ran" — an intuition naming the kill-switch asymmetry pathway. The empirical decomposition (per ADR-0027 §D-3) PARTIALLY supports the intuition:

- **Supported**: the kill-switch asymmetry mechanism IS empirically present and measurable. A2 produces the canonical win-rate drop (34.24% → 29.84%) consistent with asymmetric-blocking-of-winners during drawdown sessions.
- **Refined**: cost-realism is the EMPIRICALLY DOMINANT primitive driver (A1 alone = 100% of cumulative Δ vs A0). The operator's intuition focused on the visible-during-trading kill-switch mechanism but did not surface the cost-friction interaction with marginal mean-edge that operates per-trade.

Both findings require codification. ADR-0028 addresses both: §D-1 codifies the kill-switch size-down alternative (addresses the asymmetry); §D-2 codifies the cost-friction-dominated-edge annotation (surfaces the dominant driver as KPI-readable).

### Where this fits relative to ADR-0025 + ADR-0027

[ADR-0025](ADR-0025-abandonment-trigger-infrastructure.md) (2026-05-18) landed the abandonment-trigger infrastructure: runtime kill-switch, equity-rebase, cost model, BOCD live-pause. Per ADR-0025 §D-1, the runtime kill-switch enforces K-3 / K-4 / K-6 / K-7 by REJECTING entries that breach a constraint (`check_entry_blocked` returns `(True, reason)`). ADR-0028 §D-1 below adds an alternative enforcement mode where the runtime returns `(False, "size-down-applied")` with a multiplicative shrinkage on the position-size denominator. ADR-0025 itself is preserved verbatim per ADR-0013 §4.1 non-loss; the field-addition pattern (new optional kwargs with backward-compatible defaults) follows the same convention used at ADR-0025 §D-3 `EmpiricalFeeOverride`.

[ADR-0027](ADR-0027-operational-discipline-bounded-exploration.md) §D-3 (2026-05-19) established the empirical-before-amendment sequencing rule. ADR-0028 is the canonical instantiation: the empirical decomposition (H062 v3 ablation) completed BEFORE the amendment codification. The investigation memo's §7(c) "Empirical justification for a future ADR-0025 amendment" is the load-bearing input to this ADR.

### Operator directive (2026-05-19)

> "Draft + land ADR-0028 codifying the K-6/K-7 size-down-vs-block amendment + cost-friction-dominated-edge annotation, empirically justified by the H062 v3 primitive-attribution ablation closed in commits 1adc62a + 63a22d2."

Empirical-before-amendment rule satisfied: the ablation is closed; the amendment is now empirically anchored.

## Decision

### D-1. Kill-switch K-6/K-7 enforcement-mode enum at runtime

Extend [src/skie_ninja/backtest/kill_switch_runtime.py](../../src/skie_ninja/backtest/kill_switch_runtime.py) `KillSwitchRuntimeConfig` with two new fields:

- `k6_enforcement: Literal["block", "size_down"] = "block"`
- `k7_enforcement: Literal["block", "size_down"] = "block"`

Default `"block"` preserves the existing ADR-0025 §D-1 semantic bit-exactly — all v3 sidecar numerics produced under ADR-0025 are reproducible by callers that do not pass the new fields. The `"size_down"` value is opt-in per design.md §11.1 declaration with `# justify:` annotation.

**Behavioral specification for `"size_down"`**:

When a K-6 (`daily_pnl < -0.02 × equity_at_session_start`) or K-7 (`weekly_pnl < -0.05 × equity_at_week_start`) breach is detected, the runtime returns `check_entry_blocked(...) -> (False, "size-down-applied")` with a sizing modifier `size_multiplier ∈ (0, 1]` written into the runtime state. The simulator's entry path consumes the multiplier on the position-size computation:

```
adjusted_position_size = floor(base_position_size × size_multiplier)
```

This is mathematically equivalent to scaling the Kelly multiplier by the same fraction in [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py) `compute_position_size` (ADR-0017 §4.1 preserved verbatim); the size-down mode reuses the existing sizing pipeline without introducing a parallel branch.

**Default size-down fraction**: `size_down_fraction: float = 0.5` (half-size on breach). `# justify:` operator-prior — half-Kelly halving is the canonical risk-reduction increment per [MacLean-Thorp-Ziemba 2010 *Kelly Capital Growth* (DOI 10.1142/7598)](https://doi.org/10.1142/7598) fractional-Kelly cascade; aligns with the existing ADR-0017 §4.1 quarter-Kelly default + ADR-0018 §D-2 multiplier-grid `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` half-step convention. Empirical re-calibration tracked under `P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-CALIBRATION` (non-blocking; requires paper-trade fill data per the existing `P1-RELIABILITY-SLOPE-EMPIRICAL-CALIBRATION` convention).

**Threshold ratcheting preserved**: K-6 / K-7 thresholds remain `equity_at_session_start` × `K6_DAILY_DRAWDOWN_THRESHOLD` (=−0.02) and `equity_at_week_start` × `K7_WEEKLY_DRAWDOWN_THRESHOLD` (=−0.05) per ADR-0025 §D-1 F-1-7 fix. The size-down vs block change applies to the ACTION on breach, not to the breach-detection criterion.

**State machine semantics**: per breach the size-down multiplier is applied to ALL subsequent entries within the session (K-6) or week (K-7) until the boundary is crossed (`advance_session` / `advance_week`). On boundary, the multiplier resets to 1.0 (the K-6/K-7 daily/weekly counters reset per the existing ADR-0025 §D-1 contract).

**Backward compatibility test**: a regression test at [tests/unit/test_kill_switch_runtime.py](../../tests/unit/test_kill_switch_runtime.py) asserts bit-equality of the existing v3 sidecar numerics when both fields default to `"block"`. Cascade tracked under `P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL`.

**Out of scope at v1**:
- K-3 (no add-to-loser) and K-4 (per-symbol capacity cap) retain block-only enforcement. The size-down semantic applies only to K-6 / K-7 since they enforce *circuit breakers* (operator pause during drawdown) whereas K-3 / K-4 enforce *structural invariants* (no overlap; capacity ceiling per ADR-0001) where partial enforcement is not coherent.
- The ratchet-down-multi-step variant (50% → 25% → 12% before block) considered as Alternative C below; deferred to a future v2 of ADR-0028.

### D-2. Cost-friction-dominated-edge KPI annotation

Extend [ADR-0017 §3](ADR-0017-survival-constrained-optimization-paradigm.md) / [ADR-0014 §3.2](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) Table 9 ("Methodological-correctness annotations") grammar with a new annotation:

`cost-friction-dominated-edge-{present, absent, n/a}`

**Trigger semantics** (operator-readable; computed by orchestrator `main()` at KPI emission time):

The annotation evaluates ONLY when the KPI report card represents a v(N) emission with explicit cost-model context. Three values:

- **`cost-friction-dominated-edge-present`**: emitted when ALL three conditions hold simultaneously:
  - (i) `cost-conservative-prior` annotation present in §"Methodological-correctness annotations" (per ADR-0025 §D-3 grammar) — the KPI emission applied per-trade cost realism;
  - (ii) realized OOS basket % strictly less than 0 — the cost-applied cell shows a net loss;
  - (iii) a corresponding zero-cost ablation cell exists with realized OOS basket % strictly greater than 0 (a v(N-1) or sibling sweep cell against the same substrate vintage + same inner-CV grid + same rng_seed). The zero-cost reference cell's run_id + sidecar SHA must be cross-cited in §"Methodological-correctness annotations" for auditability.
- **`cost-friction-dominated-edge-absent`**: emitted when conditions (i) holds but EITHER (ii) is false (cost-applied basket ≥ 0) OR (iii) is false (no zero-cost reference cell exists OR the zero-cost reference is also ≤ 0). The cost is applied but does NOT flip the basket from positive to negative — cost is a drag but not the dominant catastrophe driver.
- **`cost-friction-dominated-edge-n/a`**: emitted when condition (i) is false (no cost model applied; the KPI emission is PRE-cost research-only per operator 2026-05-08 standing directive). The annotation cannot be evaluated absent a cost-applied cell.

**Rationale**: distinguishes "edge absent" (no pre-cost positive ROI; nothing for cost to extinguish) from "edge present but smaller than friction at conservative-prior calibration" (pre-cost positive ROI flipped by per-trade cost). The distinction is operator-actionable:

- `cost-friction-dominated-edge-present` → the hypothesis has a *gross* edge but not a *net* edge at conservative-prior. Operator decision space: (a) refine cost-model calibration toward `paper_trade_empirical` (if paper-trade fill data brings real fees below conservative-prior); (b) refine signal quality to widen the gross edge above the conservative-prior threshold; (c) decline ninjascript progression as cost-impractical at retail-tier capacity ceilings (per ADR-0001 + the operator's 2026-05-04 standing decline-ninjascript directive).
- `cost-friction-dominated-edge-absent` → the cost-applied result is not catastrophic-via-cost. Either the gross edge survives cost realism (positive both PRE-cost and POST-cost), or the gross edge was already null (negative both PRE-cost and POST-cost). NinjaScript-progression decision proceeds on standard ADR-0017 survival-constrained KPIs.

**Empirical anchor — H062 v3 case**: per the §Context ablation table, H062 v3 carries `cost-friction-dominated-edge-present`: condition (i) holds (cost-conservative-prior on all-ON cell); condition (ii) holds (cost-applied basket = −99.9995%); condition (iii) holds (A0 baseline = +261.88% at zero-cost on same substrate + inner-CV + seed). This is the load-bearing case for the annotation grammar.

**Cascade requirement**: the annotation is computed and emitted at orchestrator `main()` KPI-emission time. Implementation tracked under `P1-ADR-0028-COST-FRICTION-EDGE-ANNOTATION-IMPL` (BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE).

### D-3. Backward compatibility

The two new fields (`k6_enforcement`, `k7_enforcement`) have default `"block"`. All existing v3 sidecar results — including the four Phase O.15 ablations + the Phase O.13 v3 smoke + the Phase O.10 v2 full-grid baseline — are bit-exact reproducible after this amendment. The size-down semantic is strictly additive; the existing block semantic is preserved verbatim as the default code path.

The cost-friction-dominated-edge annotation is evaluative-only: it READS existing sidecar fields (`cost_model.calibration_source`, realized OOS basket %, cross-reference sidecar run_id) without modifying any existing KPI computation. Sidecars produced before this amendment do not carry the annotation but are otherwise unchanged; v(N+1) KPI cards produced after the cascade lands will gain the annotation row in §9.

### D-4. KPI annotation grammar additions

Two new annotations extend the CLAUDE.md §"KPI report card for every strategy" grammar:

- `kill-switch-mode-{block, size-down}` — runtime-mode disclosure. Emitted in §"Methodological-correctness annotations" line alongside the existing `kill-switch-{active, inactive}` (ADR-0025 §D-5) and `kill-switch-{K-N-enabled, K-N-disabled}` (ADR-0024) annotations. The three annotations are orthogonal:
  - `kill-switch-{K-N-enabled, K-N-disabled}`: design-time declaration (which K-N the hypothesis design.md §11.1 invokes).
  - `kill-switch-{active, inactive}`: runtime disclosure (did any K-N fire during simulation).
  - `kill-switch-mode-{block, size-down}`: runtime enforcement-mode disclosure (when a K-N fired, was the action block-entry or size-down).
- `cost-friction-dominated-edge-{present, absent, n/a}` — cost-friction interaction with mean-edge disclosure per §D-2.

Both annotations are mandatory in §"Methodological-correctness annotations" line of KPI report cards emitted after `P1-ADR-0028-CLAUDE-MD-CASCADE` + `P1-ADR-0028-TEMPLATE-CASCADE` land.

## Alternatives considered

### A. Block-only (preserve ADR-0025 §D-1 unchanged)

Rejected — but preserved as the default behavior. The ablation §6 evidence shows kill-switch-only (A2) produces Δ −283.79 pp vs baseline with the canonical win-rate-drop signature of asymmetric blocking; an operator-selectable alternative addresses the pathology without removing the legacy semantic. The size-down mode is OPT-IN per design.md §11.1 declaration; operators preferring block-only enforcement (e.g., for hypotheses where the structural invariant must be strict) retain the existing semantic by accepting the default. Adoption is asymmetric: block-only is the default; size-down requires explicit declaration.

### B. Exit-on-breach (close all open positions on K-6 / K-7 fire)

Rejected. Closing existing positions on breach loses capital that is still earning per the position's structural exit criteria (channel-exit / ATR-stop / EOD-flatten). The H062 v3 ablation §6 shows ~31% of entries are blocked on the all-ON cell (A2); closing all open positions in addition would compound the catastrophic outcome by realizing losses that may have mean-reverted. The kill-switch is intended to block NEW risk-additions during drawdown, not to liquidate existing exposure. Exit-on-breach is a separate primitive that may be considered if future investigation surfaces a structural case (tracked under `P1-ADR-0028-EXIT-ON-BREACH-INVESTIGATION-V2`; non-blocking).

### C. Ratchet-down-multi-step (50% → 25% → 12% before block)

Rejected at v1. The ratchet approach adds state (multi-tier breach counter per session/week) without empirical motivation. The H062 v3 ablation establishes that a single binary breach (K-6 or K-7 fires) is the trigger; whether a single 50% reduction is sufficient OR a multi-step ratchet performs better is empirically unanswered. Deferred to v2 of ADR-0028 if size-down at fixed 50% proves underpowered (tracked under `P1-ADR-0028-MULTI-STEP-RATCHET-V2`; non-blocking). The v1 size-down implementation is the minimum-complexity codification of the operator intuition.

### D. Dynamic Kelly-multiplier-from-breach-depth (size_down_fraction is a function of breach magnitude)

Rejected at v1. Coupling the size-down fraction to the breach depth (e.g., a 3% daily loss triggers 30% size; a 5% daily loss triggers 70% size) is theoretically appealing but operationally complex: introduces a new hyperparameter (breach-depth-to-fraction mapping function) that must itself be empirically calibrated. The v1 fixed-fraction (0.5) is the simplest specification that codifies the operator intuition. Dynamic mapping is a future hyperparameter exploration tracked under `P1-ADR-0028-DYNAMIC-SIZE-DOWN-FRACTION-V2` (non-blocking).

### E. Cost-friction-dominated-edge annotation as a binding promotion gate

Rejected per ADR-0013 §1 + §2 no-binding-gates philosophy preserved by ADR-0024 §D-1. The annotation is a KPI-readable disclosure, not a promotion blocker. Operators may proceed with ninjascript-implementation of a `cost-friction-dominated-edge-present` hypothesis per the standing operator-discretionary clause; the annotation surfaces the cost-realism interaction so the decision is informed, not gated.

### F. Defer until paper-trade empirical-fee data exists

Rejected. The two annotations + the size-down enforcement mode are structurally independent of empirical-fee calibration. The `conservative_prior` cost-model path is fully specified per ADR-0025 §D-3 + the existing [src/skie_ninja/backtest/costs/nt8_realistic.py](../../src/skie_ninja/backtest/costs/nt8_realistic.py) implementation. Empirical calibration via paper-trade fill data is a separate refinement that does not block ADR-0028 codification of the size-down semantic + the cost-friction-dominated-edge KPI annotation. The empirical calibration follow-up `P1-COST-MODEL-METALS-ENERGY-EMPIRICAL-OVERRIDE` (from ADR-0025) remains open and is unaffected by this amendment.

## Consequences

### Adopted

- `KillSwitchRuntimeConfig.k6_enforcement` + `.k7_enforcement` fields with `Literal["block", "size_down"]` per §D-1. Defaults preserve ADR-0025 §D-1 bit-equivalence.
- `KillSwitchRuntimeConfig.size_down_fraction: float = 0.5` per §D-1 with `# justify:` annotation at implementation site.
- `cost-friction-dominated-edge-{present, absent, n/a}` KPI annotation per §D-2.
- `kill-switch-mode-{block, size-down}` runtime-mode disclosure annotation per §D-4.
- Glossary entries for both annotations per `P1-ADR-0028-GLOSSARY-CASCADE`.

### Trade-offs accepted

- **Additional configuration surface area.** Two new fields per orchestrator + one new annotation grammar entry. Mitigated by: (a) defaults preserve existing v3 sidecar numerics; (b) the fields are flat-key in the YAML config (no nesting drift); (c) the annotation is evaluative-only and consumes existing sidecar fields.
- **Three orthogonal kill-switch annotations** (`-{K-N-enabled/-disabled}` + `-{active/-inactive}` + `-mode-{block/size-down}`) on the same KPI report card may feel verbose. Mitigated by the explicit orthogonality documentation per §D-4 + glossary cascade. Operators reading KPI cards can use the §"Methodological-correctness annotations" line as the canonical disclosure layer.
- **Empirical calibration of `size_down_fraction = 0.5` deferred.** The 0.5 default is operator-prior; empirical re-calibration tracked under `P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-CALIBRATION`. The v1 default is consistent with ADR-0017 §4.1 + ADR-0018 §D-2 half-step convention but is not empirically optimal.
- **Cost-friction-dominated-edge annotation requires cross-reference to a zero-cost cell.** Sidecars must persist sufficient metadata (`run_id`, sidecar SHA prefix-16, substrate vintage) to enable the cross-reference at KPI-emission time. The Phase O.15 ablations already emit this metadata per ADR-0026 §D-3 + ADR-0025 §D-7 ReproLog binding; older v(N) sidecars may require backfill (non-blocking).

### Residual risk

- **Size-down mode may produce its own asymmetry under specific regime conditions.** The 0.5 default halves Kelly on breach; if the post-breach session contains a series of small losing trades, the half-Kelly attenuation may not be sufficient to prevent catastrophic compounding. Tracked under `P1-ADR-0028-SIZE-DOWN-MODE-FAILURE-MODE-INVESTIGATE` (non-blocking; sequenced after first H062 v3-size-down empirical run lands).
- **The cost-friction-dominated-edge annotation depends on operator providing a zero-cost reference cell.** If no zero-cost ablation has been run against the same substrate vintage + inner-CV grid + rng_seed, the annotation cannot be evaluated and falls to `n/a`. Operators planning to emit KPI cards under `--cost-model conservative_prior` should also emit a zero-cost reference cell at the same fixture. Non-binding; tracked under `P1-ADR-0028-ZERO-COST-REFERENCE-CELL-CONVENTION` (non-blocking; documentation pattern).
- **Backward compatibility test depends on bit-equality across numpy + Python versions.** The regression test at [tests/unit/test_kill_switch_runtime.py](../../tests/unit/test_kill_switch_runtime.py) asserts that v3 sidecars produced under default `"block"` enforcement match the existing Phase O.15 sidecar within floating-point tolerance. Cross-version bit-equality is the canonical numpy floating-point envelope per the pre-existing `P1-NUMPY-FP-REPRODUCIBILITY-ENVELOPE` follow-up (registered Phase O.13 Step 1b).
- **Size-down mode interacts with the existing C9 BOCD-step-up logic in H055 v2.** Per ADR-0025 §D-6, the H055 v2 sweep already implements adaptive Kelly halving as the C9 cell variant. Size-down mode is orthogonal to C9: C9 halves Kelly on BOCD decay-detection; size-down halves Kelly on K-6 / K-7 drawdown breach. Operators may invoke either alone or both stacked; the two halvings compose multiplicatively (effective Kelly = base × C9_factor × size_down_factor). Tracked under `P1-ADR-0028-H055-V2-C9-SIZE-DOWN-INTERACTION-DOCUMENT` (non-blocking; documentation pattern).

### Cascade requirements

- **`P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL`** (BLOCKING-BEFORE-NEXT-V3-LAUNCH-WITH-SIZE-DOWN) — code amendment to [src/skie_ninja/backtest/kill_switch_runtime.py](../../src/skie_ninja/backtest/kill_switch_runtime.py): add `k6_enforcement` + `k7_enforcement` + `size_down_fraction` fields; extend `check_entry_blocked` return contract to `(blocked, reason, size_multiplier)` (backward-compatible: existing 2-tuple consumers see `(blocked, reason)` via tuple-unpack tolerance OR a wrapper function); parity-test extension covers size-down mode.
- **`P1-ADR-0028-COST-FRICTION-EDGE-ANNOTATION-IMPL`** (BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE) — extend [scripts/run_h062_walk_forward.py](../../scripts/run_h062_walk_forward.py) + [scripts/run_h055_v2_sweep.py](../../scripts/run_h055_v2_sweep.py) `main()` KPI annotation emission to compute the §D-2 trigger and emit the annotation. Requires CLI flag `--zero-cost-reference-run-id <run_id>` to declare the cross-reference cell.
- **`P1-ADR-0028-CLAUDE-MD-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — CLAUDE.md §"KPI report card for every strategy" annotation grammar gains the two new annotations + a Phase O.15 ledger entry section extension referencing this ADR.
- **`P1-ADR-0028-DECISIONS-README-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — [docs/decisions/README.md](README.md) "Inference and statistical methodology" section gains the ADR-0028 entry.
- **`P1-ADR-0028-GLOSSARY-CASCADE`** (BLOCKING-CONCURRENT-WITH-ADR) — [docs/glossary.md](../glossary.md) gains entries for `kill-switch-mode-{block, size-down}` + `cost-friction-dominated-edge-{present, absent, n/a}`.
- **`P1-ADR-0028-TEMPLATE-CASCADE`** (non-blocking) — [research/_templates/kpi_results_summary_template.md](../../research/_templates/kpi_results_summary_template.md) Table 8 ("Other KPIs") gains the two new annotation rows.

### BLOCKING follow-ups registered by ADR-0028

| Follow-up | Status | Description |
|---|---|---|
| `P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL` | BLOCKING-BEFORE-NEXT-V3-LAUNCH-WITH-SIZE-DOWN | Code amendment to `kill_switch_runtime.py`: add `k6_enforcement`/`k7_enforcement`/`size_down_fraction` fields + parity-test extension |
| `P1-ADR-0028-COST-FRICTION-EDGE-ANNOTATION-IMPL` | BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE | Extend orchestrator `main()` KPI emission to compute §D-2 trigger + emit annotation; `--zero-cost-reference-run-id` CLI flag |
| `P1-ADR-0028-CLAUDE-MD-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | CLAUDE.md annotation grammar + Phase O.15 ledger extension |
| `P1-ADR-0028-DECISIONS-README-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | ADR index entry |
| `P1-ADR-0028-GLOSSARY-CASCADE` | BLOCKING-CONCURRENT-WITH-ADR | Glossary entries for the two new annotations |

### Non-blocking follow-ups registered by ADR-0028

| Follow-up | Description |
|---|---|
| `P1-ADR-0028-TEMPLATE-CASCADE` | KPI results-summary template Table 8 annotation rows |
| `P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-CALIBRATION` | Empirical calibration of the `size_down_fraction = 0.5` default via paper-trade fill data |
| `P1-ADR-0028-MULTI-STEP-RATCHET-V2` | Multi-step ratchet variant (50% → 25% → 12% → block) considered for v2 if v1 fixed-fraction proves underpowered |
| `P1-ADR-0028-DYNAMIC-SIZE-DOWN-FRACTION-V2` | Dynamic size-down fraction as a function of breach magnitude (rejected at v1 per Alternative D) |
| `P1-ADR-0028-EXIT-ON-BREACH-INVESTIGATION-V2` | Exit-on-breach as a separate primitive (rejected at v1 per Alternative B); investigation if future evidence supports |
| `P1-ADR-0028-SIZE-DOWN-MODE-FAILURE-MODE-INVESTIGATE` | Investigation memo on size-down mode's own failure modes once first empirical run lands |
| `P1-ADR-0028-ZERO-COST-REFERENCE-CELL-CONVENTION` | Documentation pattern for zero-cost reference cell emission alongside cost-applied KPI cards |
| `P1-ADR-0028-H055-V2-C9-SIZE-DOWN-INTERACTION-DOCUMENT` | Document the multiplicative composition of C9 BOCD-step-up Kelly halving × size-down Kelly halving in H055 v2 |
| `P1-ADR-0028-RETROACTIVE-V3-COST-FRICTION-EDGE-ANNOTATION-PASS` | Retroactive emission pass: re-evaluate the H062 v3 + H055 v3 + H065 v2 + H060 v2 KPI cards for the new annotation post-CASCADE-impl |

### Closure of pre-existing follow-up

This ADR closes `P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` (registered Phase O.15 commit `1adc62a` per the H062 v3 investigation memo §8 + the audit trail's "New follow-ups" table). ADR-0028 is the canonical landing of the two-component amendment surfaced by the investigation memo §7(c): the K-6/K-7 size-down option + the cost-realism-aware KPI annotation. The pre-existing follow-up's status transitions from OPEN to CLOSED-BY-ADR-0028 with the cross-reference logged here per ADR-0013 §4.1 non-loss.

## References

### Primary peer-reviewed sources

- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management*, 40(5), 94–107. [DOI 10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094). (DSR deflation context — the cost-friction-dominated-edge annotation operates alongside DSR in the §"Methodological-correctness annotations" line.)
- Bergmeir, C., & Benítez, J. M. (2012). On the use of cross-validation for time series predictor evaluation. *Information Sciences*, 191, 192–213. [DOI 10.1016/j.ins.2011.12.028](https://doi.org/10.1016/j.ins.2011.12.028). (Walk-forward CV validity context per ADR-0027 §D-2; the H062 v3 ablation operated on the existing walk-forward fixture preserved across cells.)
- Goetzmann, W., Ingersoll, J., Spiegel, M., & Welch, I. (2007). Portfolio performance manipulation and manipulation-proof performance measures. *Review of Financial Studies*, 20(5), 1503–1546. [DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025). (MPPM(ρ=1) — the primary inferential anchor in the ablation table per ADR-0018 §D-1.)
- Kelly, J. L. (1956). A new interpretation of information rate. *Bell System Technical Journal*, 35(4), 917–926. [DOI 10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x). (Log-optimal bet sizing — underlies the size-down semantic per §D-1.)
- Lo, A. W. (2004). The Adaptive Markets Hypothesis: Market efficiency from an evolutionary perspective. *Journal of Portfolio Management*, 30(5), 15–29. [DOI 10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611). (AMH framing — partially-decayed factor framing per ADR-0024 §D-7; the cost-friction-dominated-edge annotation operationalizes the partial-decay diagnosis when combined with cost realism.)

### Practitioner sources (tagged per CLAUDE.md §"Practitioner-source-tag" convention)

- MacLean, L. C., Thorp, E. O., & Ziemba, W. T. (2010). *The Kelly Capital Growth Investment Criterion: Theory and Practice*. World Scientific, [DOI 10.1142/7598](https://doi.org/10.1142/7598). (*practitioner*) Quarter-Kelly + half-Kelly fractional-Kelly cascade convention — anchor for the `size_down_fraction = 0.5` default per §D-1.
- Tharp, V. K. (1998). *Trade Your Way to Financial Freedom*. McGraw-Hill, ISBN-13 978-0070647626. (*practitioner*) R-multiple convention — context for the per-trade cost-vs-edge interaction per §D-2 (cost flips marginal winners to losers when per-trade cost > per-trade gross-edge × win-rate).
- Vince, R. (1990). *Portfolio Management Formulas: Mathematical Trading Methods for the Futures, Options, and Stock Markets*. Wiley, ISBN-13 978-0471527565. (*practitioner*) Ch. 5 "Risk of Ruin" — preserved per ADR-0025 §D-2; the size-down mode is consistent with the gambler's-ruin-floor convention (smaller positions when in drawdown reduce ruin probability; bit-equivalent at 50% reduction to one half-Kelly step).

### Project-internal

- [ADR-0001](ADR-0001-project-scope.md) — retail capacity ceiling (K-4 unchanged at block-only per §D-1).
- [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) — §4.1 non-loss mandate + §"Frozen pre-registration amendment" discipline preserved.
- [ADR-0014](ADR-0014-canonical-end-of-simulation-results-summary-tables.md) — Table 9 ("Methodological-correctness annotations") extended per §D-4.
- [ADR-0017](ADR-0017-survival-constrained-optimization-paradigm.md) — §3 primary metric vector preserved; §4.1 drawdown-constrained Kelly sizing primitive preserved verbatim (size-down mode reuses the existing sizing pipeline).
- [ADR-0018](ADR-0018-regime-conditional-aggressive-growth-paradigm.md) — §D-2 Kelly multiplier grid `{0.25, 0.5, 1.0, 1.5, 2.0, 2.5}` half-step convention aligns with `size_down_fraction = 0.5` per §D-1.
- [ADR-0024](ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md) — §D-1 no-binding-gates preserved (the cost-friction-dominated-edge annotation is disclosure, not gate); §D-2 opt-in framing preserved (the size-down mode is opt-in per design.md §11.1 declaration).
- [ADR-0025](ADR-0025-abandonment-trigger-infrastructure.md) — §D-1 runtime kill-switch + §D-3 cost model + §D-5 annotation grammar — extended by §D-1 + §D-2 + §D-4 of this ADR; ADR-0025 preserved verbatim per ADR-0013 §4.1.
- [ADR-0026](ADR-0026-paradigm-and-reporting-refinements.md) — §D-3 promising-strategy triple-annotation convention — informs the cost-friction-dominated-edge annotation grammar (both annotations surface cost-model-conditional verdicts).
- [ADR-0027](ADR-0027-operational-discipline-bounded-exploration.md) — §D-3 empirical-before-amendment sequencing rule — this ADR is the canonical instantiation; the H062 v3 ablation completed BEFORE this amendment codification.
- [src/skie_ninja/backtest/kill_switch_runtime.py](../../src/skie_ninja/backtest/kill_switch_runtime.py) — implementation target of §D-1; field additions per `P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL`.
- [src/skie_ninja/sizing/__init__.py](../../src/skie_ninja/sizing/__init__.py) — ADR-0017 §4.1 sizing primitive — preserved verbatim; size-down mode reuses the existing `compute_position_size` via a multiplicative shrinkage on the position-size denominator.
- [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](../../research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) — empirical anchor for §D-1 + §D-2; load-bearing input per ADR-0027 §D-3.
- [docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md](../audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md) — ablation audit trail (Phase O.15 commit `1adc62a`; SHA backfill `63a22d2`).
- [docs/audits/audit_trail_2026-05-19_adr-0028-k6-k7-size-down.md](../audits/audit_trail_2026-05-19_adr-0028-k6-k7-size-down.md) — this ADR's audit-remediate-loop trail.

## Empirical justification

The empirical basis is the H062 v3 primitive-attribution ablation (4 smoke cells on canonical substrate SHA `317429e4...`; closed in Phase O.15 commits [1adc62a](https://github.com/s-koirala/SKIE-Universe/commit/1adc62a) + [63a22d2](https://github.com/s-koirala/SKIE-Universe/commit/63a22d2)). Two structurally-distinct failure modes are empirically established:

1. **Cost dominance** — A1 cost-only Δ = −361.88 pp vs A0 baseline (100% of cumulative v3 Δ within saturation-floor rounding); per-trade cost subtraction × marginal mean-edge × ~10,326 trades produces total bankruptcy. The mechanism is *cost-flips-marginal-winners-to-losers* operating per-trade on the H062 family's marginal mean-edge (full-grid v2 MPPM CI [−0.34, +0.54] covers zero PRE-cost). Anchors §D-2 cost-friction-dominated-edge annotation.

2. **Kill-switch asymmetry** — A2 kill-switch-only Δ = −283.79 pp vs A0; 8,927 K-6+K-7 fires block ~31% of all entries; win rate drops 34.24% → 29.84%. The blocked subset skews toward winners — K-6/K-7 act on past P/L but block forward entries that may or may not recover the drawdown. The asymmetric-blocking pathology is the operator's 2026-05-19 intuition empirically supported. Anchors §D-1 size-down enforcement-mode alternative.

The operator 2026-05-19 intuition is PARTIALLY supported by the decomposition: the kill-switch asymmetry IS measurable and codifiable as a size-down alternative (§D-1); cost-realism is the DOMINANT primitive driver of catastrophic outcomes on partially-decayed-factor hypotheses (§D-2). Both findings require independent codification per ADR-0027 §D-3.

The CLAUDE.md user-global §"Evidence Hierarchy" is preserved unchanged. The §D-1 size-down semantic draws from peer-reviewed Kelly 1956 + practitioner MacLean-Thorp-Ziemba 2010 + Vince 1990 (preserved per ADR-0025 §D-2). The §D-2 cost-friction-dominated-edge annotation is operationally derived from the H062 v3 ablation's per-primitive ΔROI decomposition; no new primary citation is introduced (the framework re-uses GISW 2007 MPPM + Bailey-López de Prado 2014 DSR machinery referenced under ADR-0017/0018/0027).

ADR-0028 is the canonical reference for the SKIE-Universe project's 2026-05-19+ kill-switch K-6/K-7 enforcement-mode semantics + cost-friction-dominated-edge KPI annotation. The ADR is the empirical-follow-through of the Phase O.15 H062 v3 primitive-attribution ablation per ADR-0027 §D-3 empirical-before-amendment sequencing rule. The primitive update (`P1-ADR-0028-KILL-SWITCH-RUNTIME-SIZE-DOWN-IMPL`) lands separately per the policy-only ADR convention; this ADR codifies the decision, not the code.
