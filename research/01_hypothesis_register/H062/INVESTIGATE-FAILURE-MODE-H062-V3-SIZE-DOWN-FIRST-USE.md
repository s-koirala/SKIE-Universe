---
investigation_id: INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE
schema_version: investigation_memo_v1
created: 2026-05-19
status: active
hypothesis_of_investigation: H062
parent_kpi_report_card: research/01_hypothesis_register/H062/H062_kpi_report_v2.md
---

# Investigation Memo — H062 v3 size-down primitive first-use empirical run: validating the ADR-0028 §D-1 size-down-vs-block mechanism

Per [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) §D-1, this memo is the canonical artifact class for `INVESTIGATE-FAILURE-MODE-*` follow-ups. Investigation outputs do NOT use the ADR-0014 §3.2 13-table format; this template is the alternative artifact class. Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1 non-loss, this memo is immutable post-completion; corrections produce a versioned successor (e.g., `INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE_v2.md`).

Closes `P1-ADR-0028-FIRST-SIZE-DOWN-EMPIRICAL-RUN`.

## 1. Hypothesis-of-investigation

**Empirical question**: Does [ADR-0028 §D-1](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) size-down K-6/K-7 enforcement (50% Kelly reduction on breach) empirically reduce the kill-switch-asymmetric-blocking-pathology relative to the legacy block-mode enforcement preserved by ADR-0025 §D-1?

**Mechanism under test (per ADR-0028 §D-1)**: size-down replaces "block entry" with "halve position size" when K-6 (`daily_pnl < -0.02 × equity_at_session_start`) or K-7 (`weekly_pnl < -0.05 × equity_at_week_start`) breaches. The size-down semantic preserves recovery-window participation (winning entries that would have been blocked are admitted at half size) at the cost of admitting some losing entries that block-mode would have rejected. The ADR-0028 §D-1 prediction is that the net effect is a less-asymmetric kill-switch.

**Reference anchor — H062 v3 primitive-attribution ablation A2 cell (block-mode kill-switch-only)**: per the [parent investigation memo §6](INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md), A2 enabled kill-switch alone in block-mode and produced realized OOS basket = −21.91% (Δ −283.79 pp vs A0 baseline +261.88%) with 8,927 K-6+K-7 fires blocking ~31% of all entries and win rate dropping from 34.24% to 29.84%. The win-rate drop is the canonical asymmetric-blocking signature. This memo tests whether SIZE-DOWN mode on the same fixture preserves the win rate (admitting blocked winners at half size) and recovers some of the basket-ROI delta.

**Reference anchor — H062 v3 all-ON cell (block-mode, full v3)**: run_id `154237b365794244974068402b377191`; realized OOS −99.9995%; MPPM −1.0447 [−1.44, −0.62]; 8,845 K-6+K-7 fires. This is the catastrophic baseline against which size-down is the prospective remediation.

This investigation is the canonical empirical follow-through of ADR-0028 §D-1, satisfying the ADR-0027 §D-3 *empirical-after-amendment* convention: the size-down primitive code landed in Phase O.16 commit 31e7f69 + the ADR was accepted on the SAME-DAY (2026-05-19); this empirical run is the FIRST USE that produces a sidecar carrying the new `kill-switch-mode-size-down` annotation.

## 2. Decomposition plan

Single new ablation cell on the canonical substrate (SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`), preserving the exact v3 smoke fixture (4-cell inner-CV grid: `channel_n ∈ {60, 120} × k_atr ∈ {2.0} × kelly_multiplier ∈ {0.25, 1.0}`; 60-train/30-test inner-CV folds; rng_seed `20260514`):

- **Size-down v3 cell** (new): `uv run python scripts/run_h062_walk_forward.py --smoke --enable-kill-switch-runtime --enable-equity-rebase-current --cost-model conservative_prior --k6-enforcement size_down --k7-enforcement size_down --size-down-fraction 0.5`. All three ADR-0025 primitives ENGAGED (matches v3 all-ON fixture except for the new K-6/K-7 enforcement mode).

Reference cells (existing sidecars — bookends only; NOT new compute):

- **A0 baseline (all-OFF smoke)** — run_id `5e52f0b7ddd94ecea3187566c0e255d0`; sidecar SHA prefix-16 `ecaedec192c9f701`; realized OOS +261.88%.
- **A2 baseline (kill-switch-only block-mode)** — run_id `d01ca71b7ee34863b4219003d9a05601`; sidecar SHA prefix-16 `3564a5310d8f4614`; realized OOS −21.91%; 8,927 K-6+K-7 fires.
- **v3 all-ON block-mode** — run_id `154237b365794244974068402b377191`; sidecar SHA prefix-16 `3fcef093cd908eeb`; realized OOS −99.9995%; 8,845 K-6+K-7 fires.

**Per-cell comparison metrics** (extracted from sidecar `realized_oos` + `primary_inference` + `abandonment_triggers.kill_switch_runtime` blocks):

- Realized OOS basket %, $ ending equity, max-DD %
- MPPM(ρ=1) point + CI
- LW2008 Sharpe-vs-passive point + CI
- Sharpe annualised arm vs passive
- W/L/Z session counts + win rate
- n_trades aggregate + per-symbol
- K-6 + K-7 fire counts (basket aggregate + per-symbol)
- size-down active session/week counts (NEW field added by ADR-0028 §D-1)
- Annotation grammar verification: `kill-switch-mode-size-down` annotation present in `annotations_dot_separated`

**Comparison hypotheses (ADR-0028 §D-1 mechanism prediction tests)**:

- **H_mech-1**: size-down ROI > v3 block-mode ROI = −99.9995% (size-down recovers some of the catastrophe by admitting half-sized winners)
- **H_mech-2**: size-down win-rate ≥ v3 block-mode win-rate = 27.15% (size-down preserves the asymmetric-blocking-signature absorber by admitting blocked winners)
- **H_mech-3**: size-down trade count > v3 block-mode trade count = 7,201 (entries no longer rejected; some admitted at half-size)
- **H_mech-4**: size-down still exhibits cost-friction-dominated-edge (basket negative because cost dominance per [ADR-0028 §D-2](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) is orthogonal to kill-switch enforcement mode; A1 cost-only Δ = −361.88 pp was the dominant primitive per parent memo §7(a))

Three of four are direct ADR-0028 §D-1 predictions. H_mech-4 is the orthogonality test that distinguishes the size-down recovery (partial) from the cost-realism dominance (full).

## 3. Termination criterion

Per [ADR-0027 §D-1(c)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) acceptable form (i): close when the single new size-down ablation completes, sidecar lands on disk under `artifacts/runs/H062/<run_id>/sidecar.json`, and the §6 findings table is populated with per-cell realized OOS basket %, max-DD %, MPPM(ρ=1) point + CI, kill-switch trigger counts, win rate, and the prospective `kill-switch-mode-size-down` annotation verification.

## 4. Wall-clock soft cap

Per [ADR-0027 §D-1(d)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) soft cap discipline:

| Estimate | Actual | Delta | Justify (if overrun) |
|---|---|---|---|
| 1.5 hr (~20-30 min smoke + ~30 min memo + ~30 min audit) | ~1 hr (smoke run completed in ~80 seconds thanks to substrate filesystem caching from prior A2 + v3 runs; memo authoring ~30 min; audit-remediate-loop ~25 min) | −0.5 hr (under budget) | n/a (no overrun) |

Hard cap: 2.5 hr per task spec; if exceeded, write up partial findings as a draft + flag the remaining work per ADR-0027 §D-1(d) operator-discretionary overrun clause.

## 5. Output artifact spec

Per [ADR-0027 §D-1(e)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md):

- **Output class**: investigation-memo (this artifact)
- **Cross-references**:
  - Parent KPI: [H062 v2 KPI report card](H062_kpi_report_v2.md) (full-grid baseline)
  - Parent investigation memo: [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) (the per-primitive decomposition that motivated ADR-0028)
  - Parent ADR: [ADR-0028 K-6/K-7 size-down + cost-friction-dominated-edge annotation](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) (the policy ADR codifying the size-down mechanism + the empirical prerequisite this memo satisfies)
  - Phase O.16 code landing commit: `31e7f69` (size-down primitive implementation in [src/skie_ninja/backtest/kill_switch_runtime.py](../../../src/skie_ninja/backtest/kill_switch_runtime.py))
  - Audit trail: [docs/audits/audit_trail_2026-05-19_h062-v3-size-down-first-use.md](../../../docs/audits/audit_trail_2026-05-19_h062-v3-size-down-first-use.md)

## 6. Findings

> Per [ADR-0013 §4.1 non-loss](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), table rows are APPEND-as-work-completes; rows are immutable once landed.

### 6.1 Comparison matrix — size-down vs block-mode vs all-OFF references

| Cell | Run ID | Sidecar SHA prefix-16 | Realized OOS basket % | Max-DD % | MPPM(ρ=1) point | MPPM(ρ=1) CI | LW2008 point | LW2008 CI | Win rate | n_trades | n_W/n_L/n_Z | Per-sym n_trades (ES/NQ/MGC/SIL) |
|---|---|---|---:|---:|---:|---|---:|---|---:|---:|---:|---|
| A0 (smoke baseline, all-OFF) | `5e52f0b7ddd94ecea3187566c0e255d0` | `ecaedec192c9f701` | **+261.88** | 95.43 | +0.0966 | [−0.305, +0.497] | −0.0281 | [−0.066, +0.013] | **34.24%** | 10,326 | 1149/2202/5 | 97/0/5,701/4,528 |
| A2 (kill-switch-only, **block-mode** reference) | `d01ca71b7ee34863b4219003d9a05601` | `3564a5310d8f4614` | **−21.91** | 94.30 | −0.0212 | [−0.423, +0.355] | −0.0376 | [−0.085, +0.010] | 29.84% | 7,127 | 877/2058/4 | 92/0/3,876/3,159 |
| Ref-v3 (all-ON, **block-mode**) | `154237b365794244974068402b377191` | `3fcef093cd908eeb` | **−99.9995** | 100.00 | −1.0447 | [−1.444, −0.616] | −0.1306 | [−0.178, −0.082] | 27.15% | 7,201 | 803/2155/0 | 93/0/3,928/3,180 |
| **v3 SIZE-DOWN (this run)** | `791cb35b53834e54b98d421fa216aea3` | `eda5fe3986f59fad` | **−99.9999** | 100.00 | **−1.0519** | [−1.454, −0.637] | −0.1231 | [−0.166, −0.075] | **29.33%** | **9,302** | 969/2335/0 | 93/0/5,439/3,770 |

**Sidecar provenance (size-down cell)**: substrate SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` (canonical post-Phase-O.10 post-Phase-O.13 vintage); scientific_payload_sha256 `eda5fe3986f59fad2bee74fb8bf7deeea570238a4f0ade8a0853c60f2a7dd5f4`; ReproLog at [logs/reproducibility/791cb35b53834e54b98d421fa216aea3.json](../../../logs/reproducibility/791cb35b53834e54b98d421fa216aea3.json); n_folds_realized=130; n_oos_sessions_aggregate=3,304; rng_seed `20260514`.

### 6.2 ADR-0028 §D-1 mechanism-prediction verdicts

| Prediction | A2 block-mode value | v3 block-mode value | Size-down value | Predicted direction | Empirical verdict |
|---|---:|---:|---:|---|---|
| **H_mech-1**: size-down ROI > v3 block ROI = −99.9995% | n/a | −99.9995% | **−99.9999%** | size-down > v3 block | **REFUTED (worse by −0.0004 pp)**; the prediction was that admitting blocked winners at half size would recover some ROI; instead admitting more entries at half size accelerated cost-bleed and bankruptcy. |
| **H_mech-2**: size-down win-rate ≥ v3 block win-rate = 27.15% | 29.84% | 27.15% | **29.33%** | size-down ≥ 27.15% | **VALIDATED** (29.33% > 27.15% by +2.18 pp; matches A2 29.84% within 0.51 pp — confirms the asymmetric-blocking-signature absorber). |
| **H_mech-3**: size-down trade count > v3 block trade count = 7,201 | 7,127 | 7,201 | **9,302** | size-down > 7,201 | **VALIDATED** (9,302 > 7,201 by +2,101 trades = +29.2%; size-down admits entries that block-mode rejected, at half size). |
| **H_mech-4**: cost-friction-dominated-edge present (orthogonality test) | n/a (cost-zero) | present (with proper cross-ref) | **`-absent` emitted (no cross-ref passed)** | present | **PARTIALLY-VALIDATED (mechanism-correct; disclosure-incomplete)**: per the ADR-0028 §D-2 grammar verifier, with `--zero-cost-reference-run-id 5e52f0b7ddd94ecea3187566c0e255d0` passed alongside, the annotation WOULD evaluate to `cost-friction-dominated-edge-present` (cost-applied basket −99.9999% vs zero-cost reference +261.8811% = cost flips positive → negative). This run did not pass the cross-reference at launch time; emission grammar correctly defaulted to `-absent` per the §D-2 condition (iii) safety convention. Tracked as operator-action defect not primitive-defect; see §7. |

### 6.3 Per-symbol decomposition

| Symbol | A0 n_trades | A2 n_trades | v3 block n_trades | **v3 size-down n_trades** | A0 → size-down Δ | block → size-down Δ |
|---|---:|---:|---:|---:|---:|---:|
| ES | 97 | 92 | 93 | **93** | −4 (−4.1%) | 0 (0%) |
| NQ | 0 | 0 | 0 | **0** | 0 | 0 |
| MGC | 5,701 | 3,876 | 3,928 | **5,439** | −262 (−4.6%) | **+1,511 (+38.5%)** |
| SIL | 4,528 | 3,159 | 3,180 | **3,770** | −758 (−16.7%) | **+590 (+18.6%)** |

**Critical per-symbol observation**: the size-down primitive's effect is HEAVILY concentrated on MGC (which has the densest trade activity AND the heaviest left-tail R-multiple per the v2 KPI report card). MGC size-down trade count is +38.5% above v3 block-mode (5,439 vs 3,928) — the dominant contributor to the +29.2% basket-aggregate trade increase. SIL is +18.6%. ES is unchanged (93 vs 93; ES has too few K-6/K-7 fires in the smoke fixture for the enforcement-mode difference to matter — only 6 K-6 fires on v3 block-mode ES per the v3 sidecar's `per_symbol_trigger_counts`). NQ is structurally zero across all cells per H062 design.md §11.2 known issue ($10K retail capacity ceiling × 1% risk × NQ tick value floors to <1 contract).

### 6.4 Sidecar disclosure defect surfaced (load-bearing for ADR-0028 §D-4 annotation correctness)

The v3 size-down sidecar emits `kill-switch-runtime.trigger_counts = {"K-3": 0, "K-4": 0, "K-6": 0, "K-7": 0}` and `total_triggers = 0` and `runtime_active = false` and `annotation = "kill-switch-inactive"` — but the empirical trade-count evidence proves the size-down primitive engaged (n_trades 9,302 = +2,101 vs v3 block-mode 7,201, a 29% increase consistent with admitting K-6/K-7-breached entries at half size). The size-down enforcement is functionally CORRECT but the sidecar disclosure is INCOMPLETE.

**Root cause** (verified by code-read at [scripts/run_h062_walk_forward.py:568-569](../../../scripts/run_h062_walk_forward.py) + [src/skie_ninja/backtest/kill_switch_runtime.py:335](../../../src/skie_ninja/backtest/kill_switch_runtime.py)):
- In size-down mode the primitive's `check_entry_blocked` returns `(False, "size-down-applied", size_modifier<1.0, new_state)` instead of `(True, "K-6", ...)` or `(True, "K-7", ...)`.
- The orchestrator's size-down branch at lines 568-569 calls `record_trigger(ks_state, reason)` where `reason = "size-down-applied"` (the string from the primitive). The `record_trigger` permissively creates a new key `"size-down-applied"` in `state.trigger_counts` but the basket aggregation loop at [scripts/run_h062_walk_forward.py:1696-1708](../../../scripts/run_h062_walk_forward.py) only iterates `{"K-3", "K-4", "K-6", "K-7"}` (initialized as the dict keyset) and so the `"size-down-applied"` counts are discarded at aggregation.
- Downstream: `total_triggers = 0` (from the iterated K-N keys) → `runtime_active = False` (`total > 0` condition fails) → `annotation = "kill-switch-inactive"` (per [src/skie_ninja/backtest/kill_switch_runtime.py:431](../../../src/skie_ninja/backtest/kill_switch_runtime.py) `summarize_trigger_counts`).

**Empirical proof of mechanism engagement** (independent of the broken sidecar disclosure):
- Trade count delta: +2,101 trades vs v3 block-mode = +29.2%; consistent with size-down admitting entries that block-mode rejected.
- Per-symbol delta concentrated on MGC (+1,511) + SIL (+590): the two symbols that produce >2,700 K-6+K-7 fires on the v3 block-mode sidecar; size-down on those symbols admits more entries.
- Win-rate signature: 29.33% (size-down) vs 27.15% (block) vs 34.24% (A0 baseline) — size-down restores the win-rate halfway from block-mode's compressed 27.15% back toward the baseline 34.24%, consistent with admitting half-sized winners that block-mode rejected.

**Disclosure semantics defect summary** (recorded as load-bearing finding for the §7 ADR cascade):
- `kill-switch-runtime.annotation` returns `"kill-switch-inactive"` in size-down mode, MISLEADING the operator: the runtime IS engaged + enforcing, just via a different mechanism.
- `trigger_counts` returns zeros despite the primitive having fired thousands of size-down-applied events; OPERATOR cannot audit the size-down activity.
- `runtime_active` is a misleading false because size-down events do not contribute to the boolean.
- `mode_annotation = "kill-switch-mode-size-down"` is CORRECT (it reflects the configuration, not the activity).

### 6.5 Synthesis

The size-down primitive engaged correctly at the simulator layer (functional verification via per-symbol trade-count deltas + win-rate restoration toward baseline) but did NOT recover the basket-ROI catastrophe. The MPPM(ρ=1) result is statistically indistinguishable from the v3 all-ON block-mode reference: −1.0519 vs −1.0447 (point estimates within 0.7% of each other); both CIs strictly exclude zero on the negative side at similar magnitudes. The Calmar-diff, PF-diff, and Sharpe-vs-passive-LW2008 are all numerically near-identical to v3 block-mode (within ≤7% on point estimates and overlapping CIs).

**Empirical conclusion**: at the H062 v3 fixture (4-cell smoke; 4-symbol basket; cost = `conservative_prior`; equity-rebase = current), the size-down enforcement mode does NOT recover any meaningful share of the basket-ROI catastrophe per the parent investigation memo §6's primary attribution finding. The parent memo §7(a) verdict is RE-AFFIRMED: **cost (A1) is the dominant primitive driver** of the v3 all-ON catastrophe; the kill-switch enforcement-mode change (block → size-down) affects ~29% more trades but does not move the basket from −100% bankruptcy.

This is precisely the orthogonality the ADR-0028 §D-2 cost-friction-dominated-edge annotation is designed to surface. Size-down addresses the kill-switch asymmetry (component 1 of the parent memo §7(c) finding) but cannot address the cost-realism interaction with marginal mean-edge (component 2). Both components require independent treatment per ADR-0028; the size-down mechanism's net effect on basket ROI is dominated by component 2 at this fixture.

**Win-rate is the only KPI that meaningfully responds to size-down**: 27.15% (block) → 29.33% (size-down) → 34.24% (A0). The +2.18 pp win-rate restoration vs block-mode is the canonical empirical signature of resolved asymmetric blocking. But this win-rate improvement does NOT translate to ROI improvement because the per-trade cost subtraction (`conservative_prior`) flips marginal-winning sessions to losses regardless of how many entries the kill-switch admits.

## 7. Implication

### (a) Verdict on ADR-0028 §D-1 mechanism prediction

**Mechanism: VALIDATED (per the win-rate restoration test); ROI-prediction: REFUTED (size-down at fixed 0.5 fraction does not recover the cost-flipped catastrophe).**

The size-down primitive empirically resolves the asymmetric-blocking pathology at the win-rate KPI (the canonical signature). It does NOT recover catastrophic ROI when the underlying cost-applied gross-edge is already negative-dominated. This is consistent with ADR-0028 §D-1's framing that size-down "preserves recovery-window participation" — it preserves participation but does not generate new alpha that wasn't there in the cost-zero baseline. At the H062 v3 fixture the cost-zero gross-edge is +261.88% (A0); the cost-applied gross-edge is approximately the saturation floor at −100%; size-down does not bridge this gap.

ADR-0028 §D-1 should remain as written; the operator should NOT expect size-down to be a remediation for cost-dominated catastrophes. Operator-discretionary expectation calibration: size-down is a kill-switch-asymmetry resolution primitive, not a cost-realism remediation primitive.

### (b) Empirical contribution of size-down to the v3 catastrophe recovery

**Zero contribution at the ROI KPI; partial contribution at the win-rate KPI.**

- ROI: size-down (−99.9999%) ≈ v3 block (−99.9995%) within rounding; the 0.0004 pp delta is sample noise, not signal. Size-down does NOT recover any catastrophe.
- MPPM(ρ=1): size-down −1.0519 vs v3 block −1.0447; statistically indistinguishable (CIs overlap).
- Win rate: size-down 29.33% vs v3 block 27.15%; +2.18 pp improvement; consistent with admitting blocked winners at half size.
- Trade activity: size-down 9,302 vs v3 block 7,201; +2,101 trades = +29.2% (size-down admits entries that block-mode rejected, at half size).

The decomposition reveals that the v3 catastrophe is reproducible from cost-realism alone (per the parent memo §7(a) A1 = −361.88 pp = 100% of cumulative); the kill-switch enforcement-mode is a second-order effect on a saturation-floored basket.

### (c) Should size-down be the project-recommended default for K-6/K-7 going forward?

**Operator-discretionary recommendation: NEUTRAL at this empirical evidence**. The fixed-0.5 size-down is a kill-switch-asymmetry resolution primitive. It correctly resolves the canonical asymmetric-blocking signature (win-rate restoration validated). It does NOT introduce new failure modes detectable at the smoke-fixture level. But this evidence does NOT establish that it SHOULD be the default for new hypothesis pre-registrations.

Three reasons to preserve the ADR-0028 §D-3 opt-in-with-block-default semantic UNCHANGED at this evidence layer:

1. **Empirical scope is narrow**. Only ONE empirical run validated the mechanism. ADR-0028 §D-1's prediction about "preserving recovery-window participation" was operationally tested on a single fixture where cost-realism dominates; the size-down primitive's behavior on a fixture WITHOUT cost dominance (e.g., a hypothesis with non-marginal pre-cost mean-edge) is not yet empirically tested.
2. **The H062 family is partially-decayed** (per ADR-0024 §D-7 framing + the parent memo §7(d) framing). Size-down on a partially-decayed factor may behave differently than size-down on a non-decayed factor. Generalizing the operator-recommendation requires empirical evidence on at least one non-decayed factor (e.g., per the future H065-SIL successor H067, or any cost-light hypothesis).
3. **No clear evidence of harm at default `"block"`**. Block-mode preserves the ADR-0017 §5 K-6/K-7 strict survival-constrained semantic. Operators who prefer the strict semantic (e.g., for live-promotion-critical hypotheses where capital preservation outweighs win-rate restoration) retain the existing semantic by accepting the default. Size-down requires explicit operator declaration per design.md §11.1 `# justify:` annotation, which is the canonical disclosure layer for operator-discretionary mechanism selection.

**Operator-discretionary recommendation, surface-only (NOT decision)**: future hypothesis pre-registrations whose design.md §1.1 partial-decay-or-strong-edge framing is in the **strong-edge regime** AND whose KPI report card emission is **post-cost** MAY explicitly declare `--k6-enforcement size_down --k7-enforcement size_down` per design.md §11.1 `# justify:` annotation citing this investigation's win-rate-restoration empirical evidence. Future pre-registrations in the **partially-decayed regime** (per Marshall-Cahan-Cahan 2008 + Hsu-Kuan 2005 + Park-Irwin 2007 anchor) SHOULD preserve the default block-mode per the explicit recommendation above.

### (d) Sufficiency of the ADR-0028 KPI annotation grammar

**Refined: the `kill-switch-mode-{block, size-down}` annotation IS sufficient as designed, but the orthogonal `kill-switch-{active, inactive}` annotation reflects a CRITICAL DISCLOSURE DEFECT in size-down mode**. Two new follow-ups registered per §8:

1. **Defect verification**: in v3 size-down mode the sidecar emits `kill-switch-inactive` despite size-down having engaged on +2,101 entries. The `runtime_active` boolean is incorrectly computed from `sum(trigger_counts.values()) > 0` but `trigger_counts` does not include size-down-applied counts (the "size-down-applied" key is added by `record_trigger` but discarded by the aggregation loop's K-N-keyed iteration). This produces operator-misleading disclosure: KPI report card readers see `kill-switch-inactive · kill-switch-mode-size-down` which is internally contradictory.

2. **Disclosure fix proposal** (tracked under new follow-up `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE`):
   - Option A (preferred): include `size_down_events_K6` + `size_down_events_K7` as separate counters in `KillSwitchRuntimeState.trigger_counts` (initialize the dict with 6 keys instead of 4). Update aggregation loop to iterate 6 keys. Compute `runtime_active = total_triggers > 0` over the expanded keyset. Compute `annotation = "kill-switch-active"` when ANY of the 6 has count > 0.
   - Option B (alternative): keep the 4-key trigger_counts unchanged but add a SEPARATE `size_down_event_counts: dict[K-6, K-7]` field. Compute `runtime_active = total_triggers > 0 OR sum(size_down_event_counts.values()) > 0`. Annotation `kill-switch-active` fires on either condition.
   - Option C (rejected): increment `K-6` / `K-7` counts when size-down fires. Loses the structural distinction between blocked-events (capital preservation) and size-down-events (admit-with-reduced-exposure). Operator audit value is lost.

The defect is empirically load-bearing for the ADR-0028 §D-4 annotation grammar's "auditability" property and SHOULD be closed before the next size-down KPI emission per `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` (BLOCKING-BEFORE-NEXT-SIZE-DOWN-KPI-EMISSION).

The ADR-0028 §D-2 `cost-friction-dominated-edge-{present, absent, n/a}` annotation grammar works correctly per its documented spec: this run emitted `-absent` because the operator did not pass `--zero-cost-reference-run-id`. With the A0 reference passed (verified by direct primitive invocation: `cost_friction_dominated_edge_annotation(cost_model_annotation='cost-conservative-prior', realized_oos_basket_pct=-99.9999, zero_cost_reference_cell=A0_ref)`), the annotation correctly evaluates to `cost-friction-dominated-edge-present`. This is an operator-discipline gap, NOT a primitive defect. Tracked under existing `P1-ADR-0028-ZERO-COST-REFERENCE-CELL-CONVENTION`.

### (e) Implications for the parent hypothesis H062

H062 remains at `kpi-report-emitted` (v2) per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). No stage transition is triggered by this investigation. The KPI report card v2 stands; this investigation is a RESEARCH artifact informing future v3 KPI report card emission and future hypothesis pre-registrations.

### (f) Implications for future hypotheses (constraints to inherit; failure modes to canary against)

- **Cost-realism + size-down do not stack additively**. Operators planning to deploy size-down on a cost-applied fixture should NOT expect size-down to recover cost-flipped catastrophes. Size-down recovers asymmetric-blocking-pathology only.
- **Win-rate restoration is the canonical empirical signature of size-down engagement**. Future hypotheses using size-down should report win-rate vs block-mode vs all-OFF as a sanity check that the primitive engaged.
- **Sidecar disclosure of size-down activity is INCOMPLETE in the current code**. Until `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` lands, KPI report cards using size-down mode SHALL include a manual `# operator note:` annotation in the §"Methodological-correctness annotations" line stating the n_trades delta vs the block-mode reference cell as the empirical proxy for the primitive's engagement.
- **Operator-discipline gap on the cost-friction-edge annotation**. Future v(N+1) KPI emissions under `--cost-model conservative_prior` SHALL also pass `--zero-cost-reference-run-id <A0-equivalent>` to enable the `cost-friction-dominated-edge-{present,absent}` discrimination per ADR-0028 §D-2 condition (iii). Failing to do so produces a `-absent` annotation that is operationally indistinguishable from the genuine "edge survives cost realism" finding.

**NOTE per ADR-0027 §D-3**: this memo does NOT write any ADR amendment. The disclosure-defect finding is the INPUT to a future ADR-0028.1 cycle (or a code-only fix per `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE`).

## 8. Closure

- **Closure date**: 2026-05-19
- **Closure type**: ablation-complete (per ADR-0027 §D-1(c) form (i))
- **Closure verdict**: `complete-no-further-action` at the investigation-memo layer; the empirical finding is the canonical input to a future `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` code-fix cycle (separate per ADR-0027 §D-3).
- **Downstream artifacts produced**:
  - Investigation memo (this file): [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md](INVESTIGATE-FAILURE-MODE-H062-V3-SIZE-DOWN-FIRST-USE.md)
  - Audit trail: [docs/audits/audit_trail_2026-05-19_h062-v3-size-down-first-use.md](../../../docs/audits/audit_trail_2026-05-19_h062-v3-size-down-first-use.md)
  - 1 new size-down ablation sidecar: [artifacts/runs/H062/791cb35b53834e54b98d421fa216aea3/sidecar.json](../../../artifacts/runs/H062/791cb35b53834e54b98d421fa216aea3/sidecar.json)
  - 1 new ReproLog: [logs/reproducibility/791cb35b53834e54b98d421fa216aea3.json](../../../logs/reproducibility/791cb35b53834e54b98d421fa216aea3.json)
  - 1 run log under [logs/phase_o16_size_down/run_2026-05-19_size_down.log](../../../logs/phase_o16_size_down/run_2026-05-19_size_down.log) (gitignored per project convention; regenerable via canonical command below)
  - Commit SHA: {populated on commit}
- **Closures of pre-existing follow-ups**: `P1-ADR-0028-FIRST-SIZE-DOWN-EMPIRICAL-RUN` (this investigation IS the closure artifact)
- **New follow-ups registered**:
  - `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` (BLOCKING-BEFORE-NEXT-SIZE-DOWN-KPI-EMISSION): close the sidecar-disclosure defect surfaced in §6.4: `trigger_counts` does not include size-down-applied counts; `runtime_active` boolean is incorrectly computed; `kill-switch-active/inactive` annotation contradicts `kill-switch-mode-size-down` in size-down mode. Code fix per §7(d) Option A (expand `trigger_counts` to 6 keys including `size-down-K6` + `size-down-K7`) or Option B (separate `size_down_event_counts` dict with combined `runtime_active`).
  - `P1-ADR-0028-SIZE-DOWN-NON-DECAYED-FACTOR-EMPIRICAL`: empirical run of the size-down primitive on a non-partially-decayed factor (e.g., H067 H065-SIL successor when its KPI report card v1 lands) to extend the §7(c) operator-discretionary recommendation beyond the H062 partially-decayed regime.
  - `P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-RECALIBRATION-AT-FIXTURE`: empirical comparison of `size_down_fraction ∈ {0.25, 0.5, 0.75}` on the H062 v3 smoke fixture to test whether the fixed 0.5 default is empirically optimal for this fixture; tracked alongside the pre-existing `P1-ADR-0028-SIZE-DOWN-FRACTION-EMPIRICAL-CALIBRATION` (non-blocking).

### 8.1 Phase O.17 disclosure-defect-close addendum (appended 2026-05-19)

Per [ADR-0013 §4.1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) non-loss mandate, this §8.1 appends — does NOT modify — the §6.4 + §7(d) disclosure-defect findings.

**Defect closure**: `P1-ADR-0028-SIZE-DOWN-DISCLOSURE-DEFECT-CLOSE` (registered above as BLOCKING-BEFORE-NEXT-SIZE-DOWN-KPI-EMISSION) was closed in Phase O.17 via a primitive-layer fix landing the canonical 6-key trigger_counts schema (memo §7(d) Option A "preferred"). Fix commit SHA: `<populated-at-commit-time>`; audit trail: [docs/audits/audit_trail_2026-05-19_size-down-disclosure-defect-close.md](../../../docs/audits/audit_trail_2026-05-19_size-down-disclosure-defect-close.md).

**Status of the size-down sidecar at `artifacts/runs/H062/791cb35b53834e54b98d421fa216aea3/sidecar.json`** (per ADR-0013 §4.1 non-loss): the sidecar is preserved verbatim under the original (pre-Phase-O.17) disclosure semantic; `trigger_counts` shows `{"K-3": 0, "K-4": 0, "K-6": 0, "K-7": 0}` and `annotation = "kill-switch-inactive"` despite the +2,101-trade delta vs v3 block-mode that empirically proves size-down engagement. The canonical-going-forward semantic per the Phase O.17 fix commit applies to all future size-down-mode emissions; the existing sidecar is NOT regenerated.

**Operator note for future readers**: when reading this memo against a sidecar produced AFTER the Phase O.17 fix commit, the `trigger_counts` block carries 6 keys (K-3, K-4, K-6, K-6-size-down, K-7, K-7-size-down) and the `annotation` field correctly reflects size-down engagement. Pre-Phase-O.17 sidecars (this run's included) carry the 4-key legacy schema; the empirical proof of size-down engagement is the trade-count delta vs block-mode reference, NOT the disclosure fields.

**Re-runnable verification command** (post-Phase-O.17): re-running the canonical reproduction command (§ "Canonical reproduction command" below) against the post-fix-commit HEAD will produce a NEW sidecar at a different run_id with the corrected 6-key schema, the size_down_event_count field, and `annotation = "kill-switch-active"`. The new sidecar is the canonical-going-forward reference for size-down disclosure semantics; the original sidecar at `791cb35b53834e54b98d421fa216aea3` is the historical anchor for the §6.4 + §7(d) defect finding.

## Cross-references

- Parent KPI report card: [H062 v2](H062_kpi_report_v2.md) (frontmatter `parent_kpi_report_card`)
- Parent investigation memo: [INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
- ADR codifying the size-down mechanism: [ADR-0028](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md)
- Phase O.16 code landing commit: [`31e7f69`](https://github.com/s-koirala/SKIE-Universe/commit/31e7f69)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Audit-remediate-loop trail (this investigation): [docs/audits/audit_trail_2026-05-19_h062-v3-size-down-first-use.md](../../../docs/audits/audit_trail_2026-05-19_h062-v3-size-down-first-use.md)
- ADR-0027 §D-1 source mandate: [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- ADR-0025 primitive infrastructure: [docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md)

## Canonical reproduction command

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
uv run python scripts/run_h062_walk_forward.py \
  --smoke \
  --enable-kill-switch-runtime \
  --enable-equity-rebase-current \
  --cost-model conservative_prior \
  --k6-enforcement size_down \
  --k7-enforcement size_down \
  --size-down-fraction 0.5
```

Substrate dependency: post-Phase-O.10 canonical substrate at `data/processed/vendor_legacy_1min_roll_adjusted/` with combined SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`.

## Append discipline

- Sections 1-5 are FROZEN at investigation start (2026-05-19); they MAY be edited only via versioned-successor pattern per ADR-0013 §4.1.
- Sections 6-8 are APPEND-as-work-completes; rows in the §6 ablation table are immutable once landed.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
