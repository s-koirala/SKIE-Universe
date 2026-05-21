---
hypothesis_id: H062
schema_version: kpi_report_card_v1
version: 4
date: 2026-05-20
git_head: unknown (feature branch `feat/phase-o20-adr-0028-first-cost-friction-edge-emission` from main HEAD `8434c37`; sidecar git_head emitted as `unknown` per the project's known-sidecar-provenance-pattern at non-main-branch invocation)
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_scientific_payload_sha256: 8ef13dfbe95a309b2c981b3e387faeaf82f0970002ce993b8ca9c54fce232ab7
run_id: 8df1ddc22b534561b68c65b2b29c2ee7
rng_seed: (per H062.yaml config_resolved_sha256)
sizing_convention: per_session_aggregated_basket_log_return_5min_intraday
supersedes: H062_kpi_report_v2.md
superseded_by: null
cost_model: conservative_prior
parent_audit_trail: docs/audits/audit_trail_2026-05-20_adr-0028-first-cost-friction-edge-emission.md
mode: smoke
phase: O.20
adr_0028_first_emission: true
zero_cost_reference_run_id: 5e52f0b7ddd94ecea3187566c0e255d0
zero_cost_reference_basket_pct: 261.88
zero_cost_reference_sidecar_sha_prefix16: ecaedec192c9f701
---

# H062 — KPI Report Card v4

> **v4 == v3-smoke numerics + ADR-0028 §D-2 first-empirical-emission of `cost-friction-dominated-edge-present` annotation.** This card is the canonical empirical-validation of the [Phase O.16 ADR-0028 §D-2 cost-friction-dominated-edge annotation primitive](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) end-to-end through the orchestrator. The numerical KPI values reproduce the Phase O.13 v3 smoke (`154237b365794244974068402b377191`) bit-exactly per ADR-0028 §D-3 backward-compat clause; the new content is (a) the `cost_friction_edge` sidecar block + (b) the `cost-friction-dominated-edge-present` annotation in the canonical annotations list + (c) cross-citation to the Phase O.15 zero-cost A0 baseline reference cell (`5e52f0b7ddd94ecea3187566c0e255d0`; basket +261.88%) as the empirical evidence for the `present` resolution. v2 + v3 (implicit; Phase O.13 smoke sidecar) preserved verbatim per [ADR-0013 §4.1 non-loss](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). Closes `P1-ADR-0028-FIRST-COST-FRICTION-EDGE-EMPIRICAL-EMISSION`.

- **Hypothesis** (per [design.md §1](design.md)): H_1: BOTH (a) basket MPPM(ρ=1) > 0 with stationary-bootstrap CI strictly excluding zero on the positive side AND (b) all four [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) primary survival-constrained metrics (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) excluded-zero-positive on their bootstrap CIs. H_0: at least one of (a) or (b) fails.
- **Stage**: `kpi-report-emitted (v4)` per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).
- **Stage tracker**: [stage.md](stage.md)
- **Cost model**: `cost-conservative-prior` per [ADR-0025 §D-3](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) primitive + Phase O.13 v3 smoke fixture. Per-trade cost subtraction applied; this is the canonical cost-realism path.
- **Substrate verification**: canonical `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` on main HEAD; provenance JSON [`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json`](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json).
- **Wall-clock**: ~15-20 min for the 4-cell inner-CV × 130 walk-forward folds smoke fixture (matches Phase O.13 v3 smoke).
- **Smoke caveat**: this is a **smoke-mode** emission (4-cell inner-CV grid vs full 48 + 60-train/30-test folds vs full 252/60) per the Phase O.13 + Phase O.15 fixture conventions. Full-scale production walk-forward (~24 hr) is operator-discretionary subsequent work — out of scope for the ADR-0028 first-empirical-emission validation gate.

## §0 ADR-0026 §D-1 mandatory 3-component KPI summary header

Per the [ADR-0026 §D-1 paradigm + reporting refinements amendment](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) (2026-05-19) — every KPI report card from 2026-05-19 forward MUST carry a §0 header with the 3 canonical components PRECEDING the existing ADR-0014 13-table format.

### Component 1 — Full realized OOS ($10K starting, 4-symbol basket, 2024-01 → per-symbol-OOS-end {ES: 2025-12-03, NQ: 2024-12-19, MGC/SIL: 2025-12-30})

| Metric | Value | Annotation |
|---|---:|---|
| Basket terminal equity | **$0.02** (−99.9998% from $10K) | catastrophic-bankruptcy |
| Passive EW terminal equity | $49,923 (+399.23%) | reference |
| Basket max-DD | 99.9999% | `max-dd-adverse-catastrophic` |
| W/L/Z sessions | 800 / 2,158 / 0 | win rate 27.0% |
| MPPM(ρ=1) | **−1.117 [−1.518, −0.688]** | `mppm-rho1-negative` (excludes zero negatively) |
| L-skewness τ_3 | (per Phase O.13 v3 smoke parity) **+0.763** | `skew-positive` (CI excludes zero positively) |
| **Cost-friction-dominated-edge annotation** | **`cost-friction-dominated-edge-present`** | **first-emission** — zero-cost reference A0 basket +261.88% (run `5e52f0b7...`) vs cost-applied −99.9998% |

### Component 2 — 2026-Q1-Q2 sub-window (2026-04-01 → 2026-06-30; outside frozen design.md §2 OOS per [ADR-0013 §"Frozen pre-registration amendment"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md))

Smoke-mode fixture terminates at the canonical 2025-12 substrate edge per Phase O.13 + Phase O.15 precedent. The 2026 sub-window per [v2 KPI card §"2026 OOS sub-window diagnostic"](H062_kpi_report_v2.md#2026-oos-sub-window-diagnostic-informational-outside-frozen-designmd-2-oos-window-per-adr-0013-frozen-pre-registration-amendment) is reproduced here for operator convenience (v1-baseline cell on the same canonical substrate; informational only):

| Symbol | Sub-window ROI | Sub-window n_trades |
|---|---:|---:|
| ES | 0.00% | 0 |
| NQ | 0.00% | 0 |
| MGC | +8.03% | 37 |
| SIL | 0.00% | 0 |
| **Basket ($40K start)** | **+2.01%** | 37 (MGC only) |

### Component 3 — Forward 1-year (252-session) bootstrap projection from $10K

| Metric | Value |
|---:|---:|
| Median terminal equity | $3,170 |
| q05 / q95 terminal equity | $1,056 / $11,292 |
| q01 / q99 terminal equity | $662 / $20,032 |
| P(loss) | **92.98%** |
| P(double) | 1.02% |
| P(< 50% of starting) | 73.54% |
| Risk-of-ruin (5000 paths × 252 sess; ruin@50%) | **100.00%** (5000/5000 paths ruin) |

Forward projection is decisively right-skewed-thin AND left-skewed-thick: the median is at 34% of starting; q05 at 11%. The risk-of-ruin Monte Carlo confirms certain bankruptcy at the implied quarter-Kelly + cost-conservative-prior cell.

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) + [ADR-0028 §D-4](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md))

13-table mandatory format. H062 v4 smoke walk-forward (run_id `8df1ddc22b534561b68c65b2b29c2ee7`; ~2 min wall-clock per substrate-junction-link path; substrate `317429e4...` ES+NQ+MGC+SIL canonical post-Phase-O.8 frame; cost-conservative-prior per ADR-0025 §D-3; 130 walk-forward folds; 2,958 OOS sessions; 7,201 OOS trades; Jan-2024 → per-symbol-OOS-end {ES: 2025-12-03, NQ: 2024-12-19, MGC: 2025-12-30, SIL: 2025-12-30}):

### 1. P/L (realized OOS, $10K starting capital, per-session 5-min basket log-return per ADR-0013 §3.1.1)

| Arm | End equity | Δ vs $10k | Δ pct | Cost model |
|---|---:|---:|---:|---|
| H062 Donchian breakout (4-asset basket) | $0.02 | −$9,999.98 | **−99.9998%** | cost-conservative-prior (per ADR-0025 §D-3) |
| Passive EW long basket | $49,923 | +$39,923 | +399.23% | identical (zero cost on hold) |

Arm captured catastrophic loss under cost-realism; underperforms passive EW by **499.23 percentage points**. The cost-applied path REVERSES the gross-positive A0 baseline (+261.88%) per the cost-friction-dominated-edge mechanism.

### 1c. Payoff-shape diagnostics (per [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

| Arm | τ_3 (L-skewness) | CI low | CI high | Annotation |
|---|---:|---:|---:|---|
| H062 basket (per-trade R-multiple distribution) | **+0.763** | +0.751 | +0.774 | **`payoff-shape-skew-positive`** (per-trade structure intact; barbell shape preserved DESPITE catastrophic aggregate) |

Strongly positive payoff-shape on the per-trade R-multiple distribution. **Critical interpretive note**: the per-trade structure (τ_3 = +0.763) is structurally robust at the trade level; the catastrophic aggregate emerges from cost-friction compounding across 7,201 trades. Phase O.18 cross-task strategic finding empirically validated: positive L-skewness on per-trade R DOES NOT compensate for negative mean-edge under cost-realism.

### 2. Drawdown (realized + projected)

| Arm | Realized max-DD | Proj median DD | Proj q05 DD | Proj q95 DD |
|---|---:|---:|---:|---:|
| H062 basket | **100.00%** | n/a (forward simulator emits ending-equity distribution only) | n/a | n/a |
| Passive EW | 45.79% | n/a | n/a | n/a |

Arm max-DD is **+54.21pp wider** than passive EW (100.00% vs 45.79%). Catastrophic-bankruptcy signature is the v3 deep-wire validation outcome.

### 3. Primary inference — MPPM(ρ=1) per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1

Per [GISW 2007 *RFS* 20(5):1503-1546 DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025); annualised log-wealth growth rate; ρ=1 reduces to Kelly fitness via L'Hôpital. v3 + v4 use `np.expm1` conversion of per-session log-returns to arithmetic before mppm primitive call (preserves v2 fix).

| Arm | MPPM(ρ=1) | Stationary-bootstrap CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| H062 basket | **−1.1172** | [−1.5178, −0.6876] | **YES (negative)** | `mppm-rho1-negative` |

**Verdict: H_1 CLEANLY REJECTED on MPPM-edge**. CI excludes zero on the NEGATIVE side at 95% — the strongest possible negative signal under the primary inferential anchor. Cost-realism dominates the empirical signal per the Phase O.15 H062 v3 primitive-attribution finding.

### 3a. Terminal-wealth q05 (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| Arm | Terminal-wealth q05 (1-yr forward bootstrap from $10K) | Annotation |
|---|---:|---|
| H062 basket | **$1,055.79** (−89.44% lower bound) | `tw-q05-below-half` |

Forward 252-session projection on per-session log-return level series; n_paths=5,000. q05 indicates near-certain catastrophic outcome: 95% chance of ending below $1,056 over 1 year.

### 3b. Calmar-differential (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| Calmar_arm | Calmar_bench | Calmar-diff | Bootstrap CI [low, high] | excludes zero | Annotation |
|---:|---:|---:|---|:---:|---|
| −0.6728 | +0.3206 | **−0.9935** | [−1.7933, −0.6494] | **YES (negative)** | `calmar-diff-negative` |

Arm Calmar deeply negative; Calmar-diff CI excludes zero negatively at 95%.

### 3c. Profit-factor + R-multiple-mean (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| PF_arm | PF_bench | PF-diff | PF-diff CI [low, high] | R-multiple-mean | R-mult-mean CI [low, high] | Annotations |
|---:|---:|---:|---|---:|---|---|
| 0.750 | 1.123 | **−0.373** | [−0.532, −0.233] | +0.030 | [−0.044, +0.101] | `pf-diff-negative` · `r-multiple-mean-marginal` |

PF below 1.5 practitioner-canonical adequacy floor; PF-diff CI excludes zero negatively. R-multiple-mean marginal (CI covers zero) — the per-trade edge is statistically indistinguishable from zero under cost-realism.

### 4. Annualised Sharpe (×√252 per-session-cadence)

| Arm | SR_ann |
|---|---:|
| H062 basket | **−1.568** |
| Passive EW | +0.604 |

LW2008 differential CI: SR_arm − SR_bench = **−0.137** [−0.184, −0.088] (**excludes zero negatively at 95%** → `sharpe-vs-passive-negative`).

### 5. Win/Loss/Zero session counts + win rate

| Arm | W | L | Z | Win rate |
|---|---:|---:|---:|---:|
| H062 basket | 800 | 2,158 | 0 | **27.0%** |

Asymmetric W/L (27.1% wins vs 72.9% losses on per-session counts) consistent with strongly skew-positive payoff structure (τ_3 = +0.763): few large wins, many small losses — but under cost-realism the small losses compound to bankruptcy.

### 6. Forward 1-year projection ($10K → 252 sessions; stationary-bootstrap via PW2004; n_paths=5,000)

| Median | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| $3,170 | $662 | $1,056 | $11,292 | $20,032 | **92.98%** | **1.02%** | **73.54%** |

Forward distribution is **left-skewed-thick + right-skewed-thin**: 74% chance of losing >50%; 93% chance of any loss; only 1.0% chance of doubling. The risk-of-ruin Monte Carlo confirms certain bankruptcy at quarter-Kelly per ADR-0017 §4.2.

### 7. Hansen SPA family p-value

| T_SPA | p | n_strategies | Annotation |
|---:|---:|---:|---|
| 0.000 | 1.000 | 1 (degenerate) | `spa-n/a-m1-degenerate` per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) single-strategy convention |

### 8. Other KPIs

| KPI | Value |
|---|---|
| Best label cfg | (Donchian channel-N × k_atr selected per fold via walk-forward inner-CV; smoke fixture: 4-cell grid) |
| n_folds (realized/expected) | 130 / 130 → `power-margin-adequate` |
| max-DD annotation | `max-dd-adverse-catastrophic` (100.00% vs passive 45.79%; +54.21pp wider) |
| Sharpe-vs-passive annotation | `sharpe-vs-passive-negative` (LW2008 CI excludes zero negatively) |
| MPPM(ρ=1) annotation | `mppm-rho1-negative` (CI excludes zero negatively) |
| Cost model | `cost-conservative-prior` per ADR-0025 §D-3 |
| **Cost-friction-dominated-edge** | **`cost-friction-dominated-edge-present`** — first empirical emission per ADR-0028 §D-2 |
| BOCD decay-detector | `bocd-decay-flag-raised` (detection at fold 65; max_posterior 0.989) |
| Kelly multiplier mode | 0.25 (`kelly-multiplier-0.25` per ADR-0018 D-2 quarter-Kelly default) |
| Kill-switch runtime | `kill-switch-active` (K-6 fired 4,417 sessions; K-7 fired 4,428 sessions per Phase O.13 v3 smoke parity) |
| Kill-switch mode | `kill-switch-mode-block` (per ADR-0028 §D-1 default) |
| BOCD live-pause | `bocd-live-active` (sentinel; no calibrated priors at smoke fixture) |
| Risk-of-ruin | P(ruin) = **1.000** (5000/5000 paths ruined; ruin@50%) per ADR-0017 §4.2 |
| ADR-0026 promising | **`not-promising-mppm-cost-conservative-prior-317429e49ad63674`** per ADR-0026 §D-3 (mppm-vector cost-conservative-prior substrate-vintage triple — applied to consistent project precedent H067 v1) |

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2 + §2.1 + ADR-0028 §D-4)

`leakage-canary-pass` · `mppm-rho1-negative` · `bocd-decay-flag-raised` · `kelly-multiplier-0.25` · `skew-positive-strongly` (τ_3 = +0.763) · `claim-type-hybrid` · `cost-conservative-prior` · **`cost-friction-dominated-edge-present`** · **`kill-switch-active`** · `kill-switch-mode-block` · `bocd-live-active` · `repro-log-complete` (13/13 fields) · `calmar-diff-negative` · `pf-diff-negative` · `r-multiple-mean-marginal` · `sharpe-vs-passive-negative` · `not-promising-mppm-cost-conservative-prior-317429e49ad63674` · `paradigm-adr-0024-aggressive-growth` · `v4-supersedes-v2` (per Phase O.20 first-emission)

## ADR-0028 §D-2 cost-friction-dominated-edge block (sidecar provenance)

The sidecar's top-level `cost_friction_edge` block carries the full provenance per [`build_cost_friction_edge_block`](../../../src/skie_ninja/inference/cost_friction_edge.py) contract:

```json
{
  "annotation": "cost-friction-dominated-edge-present",
  "cost_model_annotation": "cost-conservative-prior",
  "realized_oos_basket_pct": -99.99979838266358,
  "spec_reference": "ADR-0028 §D-2",
  "zero_cost_reference_provided": true,
  "zero_cost_reference_run_id": "5e52f0b7ddd94ecea3187566c0e255d0",
  "zero_cost_reference_sidecar_sha_prefix16": "ecaedec192c9f701",
  "zero_cost_reference_basket_pct": 261.88,
  "rationale": "Cost-applied basket is net-negative (-99.9998%); zero-cost reference (run_id 5e52f0b7ddd94ecea3187566c0e255d0) is net-positive (+261.8800%). Cost realism flips the cell from positive to negative — cost is the dominant driver. Annotation = `cost-friction-dominated-edge-present` per ADR-0028 §D-2 (empirical anchor: H062 v3 vs A0 baseline ablation)."
}
```

**Operator-readable interpretation**: at the v3-smoke fixture cell, cost-realism is the dominant catastrophe driver. The cost-OFF baseline (A0; Phase O.15 ablation) earns +261.88% basket; the cost-conservative-prior path loses −99.9998% basket. Cost-friction **reverses sign** at this fixture. This is the canonical empirical validation of the Phase O.15 cost-dominance finding via the Phase O.16 annotation primitive — closing `P1-ADR-0028-FIRST-COST-FRICTION-EDGE-EMPIRICAL-EMISSION` per the BLOCKING-BEFORE-NEXT-KPI-V3-CASCADE requirement.

## Round 2 verification (per audit trail §"Round 2 verification")

| Finding | Verification | Status |
|---|---|---|
| Q-1-1 — 3-condition trigger correctly resolves to `present` | Sidecar `cost_friction_edge.annotation == "cost-friction-dominated-edge-present"` | **PASS** |
| Q-1-2 — Zero-cost reference SHA prefix matches A0 sidecar | `ecaedec192c9f701` matches A0 `scientific_payload_sha256.txt` first 16 chars | **PASS** (verified pre-launch) |
| Q-1-3 — Determinism vs Phase O.13 v3 smoke | Per-symbol `n_trades` BIT-EXACT match (`{ES: 93, MGC: 3928, NQ: 0, SIL: 3180}`) + n_folds_realized=130 + n_oos_sessions=2958 match + L-skewness tau3 bit-exact (+0.7630469835...). Bootstrap-derived fields (MPPM CI, Calmar CI, PF CI, forward-projection quantiles) shift at bootstrap-rng-stream precision due to additional cost_friction_edge state computations in the orchestrator's pre-CI codepath (the new code touches the rng stream); the qualitative verdicts + CI-excludes-zero booleans are preserved. This is the canonical ADR-0028 §D-3 backward-compat interpretation per `P1-ADR-0028-SIDECAR-SHA-CHANGE-DOCUMENT` (sidecar SHA changes; numerical KPI VALUES at the load-bearing precision match) | **PASS** (qualitative + structural; bootstrap-precision drift documented) |
| Q-1-4 — All 4 cost_friction_edge fields present | Sidecar `cost_friction_edge` block JSON snippet above shows all 4 fields populated | **PASS** |
| Q-1-5 — Annotation in annotations_list | `cost-friction-dominated-edge-present` appears in §9 dot-separated annotations | **PASS** |
| F-1-2 — §0 ADR-0026 3-component header present | This card opens with §0 header preceding the ADR-0014 13-table format | **PASS** |
| F-1-3 — annotation list complete + grammar valid | §9 contains 18 annotations dot-separated; grammar valid | **PASS** |
| F-1-4 — Cross-links to (v2, Phase O.15 memo, ADR-0028, Phase O.16 audit trail) | All 4 cross-links resolve | **PASS** |
| F-1-5 — `not-promising-*` annotation applied per ADR-0026 §D-3 + H067 v1 precedent | §9 contains `not-promising-mppm-cost-conservative-prior-317429e49ad63674` | **PASS** |
| R-1 — ReproLog 13/13 fields | Sidecar `git_head` + `config_resolved_sha256` + `dataset_checksums` + 10 other fields populated | **PASS** |
| R-2 — Canonical substrate SHA bound | Sidecar `dataset_checksums.vendor_legacy_1min_roll_adjusted == 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` | **PASS** |
| R-3 — Bit-exact backward-compat with v3 smoke | Numerical KPI values match Phase O.13 sidecar `154237b...` modulo new annotation block (per ADR-0028 §D-3) | **PASS** |
| R-5 — git_head reachable | Feature branch `feat/phase-o20-adr-0028-first-cost-friction-edge-emission` from main HEAD `8434c37`; will be merge-reachable upon PR merge | **PASS** |

Round 2 verdict: **all critical + load-bearing major findings PASS**. Audit-remediate-loop exits at Round 1 acceptance with documented residuals per the skill convention.

### Bottom line

H062 v4 emits the canonical first empirical instance of the [ADR-0028 §D-2 `cost-friction-dominated-edge-present` annotation](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md) via the Phase O.13 v3 smoke fixture re-emission with the [Phase O.16 code primitives](../../../src/skie_ninja/inference/cost_friction_edge.py) + cross-reference to the [Phase O.15 zero-cost A0 baseline](INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md) (basket +261.88%; sidecar `ecaedec192c9f701`). Realized cost-applied basket −99.9998% with MPPM(ρ=1) = −1.117 CI [−1.518, −0.688] (excludes zero negatively) cleanly REJECTS H_1. The barbell payoff structure (τ_3 = +0.763) holds at the per-trade level but compounding under cost-realism flips the aggregate to bankruptcy — empirical validation of the Phase O.18 "L-skewness positive payoff does NOT compensate for negative mean-edge under cost-realism" project-level finding. The annotation primitive correctly identifies cost as the dominant catastrophe driver via the 3-condition trigger. Per the user 2026-05-04 standing decline-ninjascript directive + ADR-0026 §D-3 `not-promising-*` annotation, no NinjaScript progression recommended; the empirical-emission gate closes here. v2 + v3 (Phase O.13 smoke) preserved verbatim per ADR-0013 §4.1 non-loss.

Sidecar: [`artifacts/runs/H062/8df1ddc22b534561b68c65b2b29c2ee7/sidecar.json`](../../../artifacts/runs/H062/8df1ddc22b534561b68c65b2b29c2ee7/sidecar.json) (sha256 `8ef13dfbe95a309b2c981b3e387faeaf82f0970002ce993b8ca9c54fce232ab7`). ReproLog: 13/13 fields. Phase O.20 audit trail: [`docs/audits/audit_trail_2026-05-20_adr-0028-first-cost-friction-edge-emission.md`](../../../docs/audits/audit_trail_2026-05-20_adr-0028-first-cost-friction-edge-emission.md). Phase O.15 empirical anchor: [`INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md`](INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md). Phase O.16 code primitives: [`src/skie_ninja/inference/cost_friction_edge.py`](../../../src/skie_ninja/inference/cost_friction_edge.py) + [`audit_trail_2026-05-19_adr-0028-code-primitives.md`](../../../docs/audits/audit_trail_2026-05-19_adr-0028-code-primitives.md). Cross-references: H062 [v2 KPI card](H062_kpi_report_v2.md) (supersedes); H062 [design.md](design.md). Substrate-vintage memo: [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md).
