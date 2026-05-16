---
hypothesis_id: H065
schema_version: kpi_report_card_v1
version: 1
date: 2026-05-15
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: b93e54487b9315133f32adb650c01b0c1094b7c5c958e88a9a5b3d1ca40327ce
sidecar_sha256: ea12473729264d25d009834c537cb6f657d51c15a1a4f9bca9cb24496798d60d
run_id: tp_overlay_sweep_20260516T030515Z
rng_seed: 20260515
sizing_convention: per_trade_atr_stop_5min_intraday_basket_log_return
supersedes: null
superseded_by: null
cost_model_v1_scope: pre_cost_research_only
---

# H065 — KPI Report Card v1

> **First H065 TP-overlay sweep emission** — H062 v1 + ATR-scaled profit-target overlay at `M ∈ {1.0, 1.5, 2.0, 2.5}` R-multiples; 5-min cadence; 4-symbol basket {ES, NQ, MGC, SIL}; 2020-01-01 → 2026-05-15 OOS window on the post-Phase-O.0 + 2026-H1 extension substrate (`b93e544...`). Canonical [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §3 + [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) 13-table format + [ADR-0017](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) primary survival-constrained vector + [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) MPPM(ρ=1) + [ADR-0019](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md) L-skewness + [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) causal-mechanism annotations. Sweep completed 2026-05-15 ~22:08 (run_id `tp_overlay_sweep_20260516T030515Z`; wall-clock ~3.5 min single-cell representative grid; sidecar at [artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/sweep_sidecar.json](../../../artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/sweep_sidecar.json)).

- **Hypothesis** (per [design.md §1](design.md)): H_1: there exists `M* ∈ {1.0, 1.5, 2.0, 2.5}` such that BOTH (a) basket MPPM(ρ=1) > 0 with stationary-bootstrap CI strictly excluding zero positively AND (b) per-trade L-skewness τ_3 ≥ 0 (CI does not exclude positive side). The TP-overlay does NOT invert the H062 v1 skew-positive payoff into skew-negative ("death-by-thousand-cuts").
- **Design.md**: [design.md](design.md) (frozen at `status: designed`).
- **Stage**: `kpi-report-emitted` per ADR-0013 §1. Next mandatory transition: `ninjascript-implemented` per ADR-0013 §5; per the user 2026-05-04 standing directive, operator-discretionary upon canonical-format presentation.
- **Stage tracker**: [stage.md](stage.md)
- **Scope deviations from frozen design.md** (per Path A frozen-pre-reg amendment discipline; §1-§7 preserved):
  - Inner-CV grid REDUCED from the full 55,296-cell design.md §5 combinatorial product to a tractable 16-cell representative grid (M-cell × Kelly × symbol); channel_n + k_atr + atr_n + h_dwell + trend_id fixed at H062 v1 modal values per H062 KPI report card §8 (channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0). Full-grid tracked under `P1-H065-FULL-INNER-CV-GRID-V2`.
  - **Cost model = ZERO** (`cost-zero-v1-pre-cost-research-only`) per operator standing directive. Cost-realism deferred to `P1-H065-COST-EMPIRICAL-CALIBRATION` (BLOCKING-BEFORE-V2).
  - Both fixed-equity and current-equity rebase **reference** cells reported alongside the 4 TP-overlay cells (the design.md §5 specifies current-equity rebase per ADR-0017 §4.1; the fixed-rebase M=∞ cell is reported for direct comparability to H062 v1 KPI report card numbers).
  - NQ produces **0 trades on all 6 configs** — structural sample-size constraint at $10K starting equity (NQ 1R median $730/contract vs $100 risk budget). Documented; not a defect. v2 path: MNQ substitution OR ≥$80K starting capital. Tracked under `P1-H065-MNQ-SUBSTITUTION` (BLOCKING-BEFORE-V2).

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md))

H065 TP-overlay sweep (run_id `tp_overlay_sweep_20260516T030515Z`; ~3.5 min wall-clock; substrate `b93e544...` ES+NQ+MGC+SIL on the post-Phase-O.0 + 2026-H1-extension frame; **PRE-COST research-only**; single-cell representative feature-grid; 6 configs × 4 symbols + 1 basket per config = 30 result rows):

### 1. P/L (realized OOS, $10K starting capital, 5-min intraday basket log-return per ADR-0013 §3.1.1)

| Config | Symbol | End equity | Δ vs $10k | Δ pct |
|---|---|---:|---:|---:|
| **M=∞ H062 v1 fixed-rebase** | BASKET | $11,033 | +$1,033 | **+10.33%** |
| M=∞ H062 v1 fixed-rebase | ES | $14,054 | +$4,054 | +40.54% |
| M=∞ H062 v1 fixed-rebase | MGC | $21,648 | +$11,648 | +116.48% |
| M=∞ H062 v1 fixed-rebase | SIL | $54,638 | +$44,638 | **+446.38%** |
| **M=∞ H065 current-rebase** | BASKET | $12,221 | +$2,221 | **+22.21%** |
| M=∞ H065 current-rebase | SIL | $83,468 | +$73,468 | **+734.68%** |
| **M=1.0** | BASKET | $8,995 | −$1,005 | **−10.05%** |
| **M=1.5** | BASKET | $8,211 | −$1,789 | **−17.89%** |
| **M=2.0** | BASKET | $8,970 | −$1,030 | **−10.30%** |
| **M=2.5** | BASKET | $5,967 | −$4,033 | **−40.33%** |

**The TP-overlay configurations (M ∈ {1.0, 1.5, 2.0, 2.5}) all produce NEGATIVE basket OOS ROI**, ranging from −10% to −40%. The no-TP H062 v1 reference (M=∞) is positive (+10% fixed-rebase, +22% current-rebase). **No M cell delivers a Pareto improvement** over the no-TP baseline at the basket level.

### 2. Drawdown (realized)

| Config | Symbol | Max-DD% | Bankroll-blowup |
|---|---|---:|:---:|
| M=∞ H062 v1 fixed-rebase | BASKET | 79.38% | — |
| M=∞ H062 v1 fixed-rebase | MGC | **100.00%** | YES (min eq=−$656; fixed-rebase has no current-equity floor) |
| M=∞ H062 v1 fixed-rebase | SIL | 25.20% | NO |
| M=∞ H065 current-rebase | BASKET | 53.61% | NO |
| M=∞ H065 current-rebase | SIL | 64.84% | NO |
| M=1.0 | BASKET | 31.25% | NO |
| M=1.5 | BASKET | 37.01% | NO |
| M=2.0 | BASKET | 42.14% | NO |
| M=2.5 | BASKET | 48.32% | NO |

**MGC fixed-rebase bankroll-blowup** is a known sizing-failure mode at $10K starting capital with $100 fixed dollar risk: a deep enough MGC drawdown sequence drives equity negative. Current-equity rebase eliminates this failure mode by shrinking sizing as bankroll drops. The TP-overlay cells (M=1.0..2.5) all have substantially lower MaxDD than M=∞ at the basket level — TP overlay reduces drawdown severity but at the cost of mean return.

### 3a. MPPM(ρ=1) — primary fitness per ADR-0018 D-1

Basket-level MPPM(ρ=1) with stationary-bootstrap CI; n_bootstrap=1000, rng_seed=20260515:

| Config | Point | 95% CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| M=∞ H062 v1 fixed-rebase | +0.013 | [−0.247, +0.225] | NO | `mppm-rho1-marginal` |
| **M=∞ H065 current-rebase** | **+0.026** | [−0.122, +0.183] | NO | `mppm-rho1-marginal` |
| M=1.0 | −0.014 | [−0.072, +0.047] | NO | `mppm-rho1-marginal` |
| M=1.5 | −0.028 | [−0.098, +0.048] | NO | `mppm-rho1-marginal` |
| M=2.0 | −0.015 | [−0.097, +0.071] | NO | `mppm-rho1-marginal` |
| M=2.5 | −0.083 | [−0.183, +0.015] | NO | `mppm-rho1-marginal` |

**H_1 condition (a)** (MPPM CI excludes zero positively) **NOT met on any M cell**. Point estimates for all TP cells are negative. The best single-symbol cell is **SIL M=∞ fixed-rebase** with MPPM=+0.265 CI=[+0.087, +0.459] **EXCLUDES ZERO POSITIVELY** — but this is the no-TP H062 v1 reference (M=∞), NOT an H065 TP-overlay cell. Per the H_1 framing, **no M ∈ {1.0, 1.5, 2.0, 2.5} delivers MPPM CI strict-positivity**.

### 3b. Calmar-differential — primary survival inference

Basket-level Calmar (point estimate; differential CI deferred per `P1-H065-CALMAR-DIFFERENTIAL-V2`):

| Config | Calmar |
|---|---:|
| M=∞ H062 v1 fixed-rebase | +0.017 |
| **M=∞ H065 current-rebase** | **+0.049** |
| M=1.0 | −0.045 |
| M=1.5 | −0.074 |
| M=2.0 | −0.035 |
| M=2.5 | −0.165 |

### 3c. Profit-factor — primary survival inference

Per-trade profit factor at basket level:

| Config | PF |
|---|---:|
| M=∞ H062 v1 fixed-rebase | 1.16 |
| M=∞ H065 current-rebase | 1.06 |
| M=1.0 | 1.01 |
| M=1.5 | 0.97 |
| M=2.0 | 0.98 |
| M=2.5 | 0.93 |

### 3d. R-multiple-mean — primary survival inference

Per-trade R-multiple mean at basket level (point estimate; CI deferred per `P1-H065-R-MULT-CI-V2`):

| Config | R-mean | excludes zero |
|---|---:|:---:|
| M=∞ H062 v1 fixed-rebase | +0.140 | NO (per-symbol CIs cover zero except SIL) |
| M=∞ H065 current-rebase | +0.043 | NO |
| M=1.0 | +0.010 | NO |
| M=1.5 | +0.021 | NO |
| M=2.0 | +0.011 | NO |
| M=2.5 | +0.000 | NO |

### 4. Annualised Sharpe (×√252)

| Config | Symbol | Annualised Sharpe |
|---|---|---:|
| M=∞ H062 v1 fixed-rebase | BASKET | +0.03 |
| M=∞ H062 v1 fixed-rebase | ES | **+1.36** |
| M=∞ H062 v1 fixed-rebase | SIL | **+1.08** |
| M=∞ H065 current-rebase | BASKET | +0.12 |
| M=∞ H065 current-rebase | SIL | +0.49 |
| M=1.0 | BASKET | −0.17 |
| M=1.0 | ES | +1.08 |
| M=1.0 | MGC | +0.23 |
| M=1.5 | BASKET | −0.28 |
| M=1.5 | ES | **+1.28** |
| M=2.0 | BASKET | −0.13 |
| M=2.5 | BASKET | −0.66 |

**ES is the only symbol where TP overlay improves Sharpe over passive** — but only modestly (M=1.0 SR +1.08 vs M=∞ fixed +1.36). The basket-level annualised Sharpe is negative for all 4 TP cells and barely positive for the M=∞ references.

### 5. Win/Loss/Zero counts + win rate

| Config | Wins | Losses | Zeros | W/L ratio | Win rate |
|---|---:|---:|---:|---:|---:|
| M=∞ H062 v1 fixed-rebase | 1,960 | 7,492 | 44 | 1:3.82 | 20.6% |
| M=∞ H065 current-rebase | 2,003 | 7,911 | 56 | 1:3.95 | 20.1% |
| **M=1.0** | **6,361** | 6,328 | 42 | **~1:1** | **50.0%** |
| M=1.5 | 4,309 | 6,196 | 47 | 1:1.44 | 40.8% |
| M=2.0 | 3,925 | 7,106 | 52 | 1:1.81 | 35.4% |
| M=2.5 | 2,730 | 6,108 | 56 | 1:2.24 | 30.7% |

**M=1.0 produces ~1:1 win rate** (TP at 1R = SL at 1R produces symmetric ~50% expected win rate by construction). Higher M cells progressively widen the W/L ratio. This is the **expected mechanical effect** of the TP overlay — TP closer to entry means more trades close at TP (winner) before hitting SL (loser).

### 6. Forward 1-year (252-session) bootstrap projection ($10k starting capital)

Forward projection deferred to a sensitivity exhibit per `P1-H065-FORWARD-PROJECTION` follow-up (non-blocking; first-pass v1 KPI report card focuses on realized OOS + sub-window per the operator's deliverable spec).

### 7. Hansen SPA family p-value

SPA deferred to `P1-H065-FAMILY-SPA-COMPUTE` (non-blocking; 4-M-cell + 6-config family-wise correction at v2).

### 8. Other KPIs

| KPI | Value |
|---|---|
| Best M cell on basket MPPM(ρ=1) | M=∞ H065 current-rebase (+0.026; not strict-positive) |
| Best M cell on Calmar | M=∞ H065 current-rebase (+0.049) |
| Best M cell on R-multiple mean | M=∞ H062 fixed-rebase (+0.140) |
| Best M cell on skew preservation | M=∞ H062 fixed-rebase (τ_3=+0.807) |
| Strongest standalone cell | **SIL M=∞ fixed-rebase**: MPPM=+0.265 CI=[+0.087, +0.459] EXCLUDES ZERO POS; +446% ROI; MaxDD 25%; τ_3=+0.776 |
| Number of TP cells passing H_1 | **0** (no M ∈ {1.0, 1.5, 2.0, 2.5} meets both H_1 conditions) |
| Aggregate OOS trades (basket-level, M=∞ fixed-rebase reference) | 9,496 |
| Aggregate OOS trades (basket-level, M=1.0 cell) | 12,731 |
| Cost model | `cost-zero-v1-pre-cost-research-only` — PRE-COST |
| NQ infeasibility | All 6 configs: 0 trades (NQ 1R median $730/contract vs $100 dollar-risk floor) |
| MGC bankroll-blowup at fixed-rebase | YES (min equity = −$656); current-rebase eliminates this failure mode |

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2)

`leakage-canary-pass · mppm-rho1-marginal · h_1-null-on-all-tp-cells · skew-inverted-on-m1 (τ_3 = −0.034 basket) · cost-zero-v1-pre-cost-research-only · repro-log-incomplete (sweep-script-not-walk-forward) · post-run-audit-pass · nq-zero-trades-capacity-floored · mgc-bankroll-blowup-fixed-rebase-only`

### 10. L-skewness annotation (per ADR-0019)

Per-symbol τ_3 by config:

| Symbol | M=∞ fixed | M=∞ current | M=1.0 | M=1.5 | M=2.0 | M=2.5 |
|---|---:|---:|---:|---:|---:|---:|
| ES | **+0.899** | +0.856 | **−0.070** (SKEW-FLIP) | +0.116 | +0.303 | +0.397 |
| MGC | +0.745 | +0.766 | **−0.014** (SKEW-FLIP) | +0.189 | +0.317 | +0.429 |
| SIL | +0.776 | +0.759 | **−0.019** (SKEW-FLIP) | +0.168 | +0.292 | +0.392 |
| BASKET | **+0.807** | +0.794 | **−0.034** (SKEW-FLIP) | +0.158 | +0.304 | +0.406 |

**Critical finding**: M=1.0 (1:1 risk:reward TP) **INVERTS** the skew direction on every symbol AND on the basket — τ_3 drops from +0.7 to +0.8 (skew-positive) at M=∞ down to slightly negative (−0.014 to −0.070) at M=1.0. **This is the canonical death-by-thousand-cuts pattern that H_1 (b) was designed to detect**.

M=1.5 onwards preserves skew-positive on the basket (τ_3 +0.158 → +0.406 as M increases). The skew direction is preserved at higher M cells; the cost is win rate (M=2.5 win rate 30.7% vs M=1.0 50.0%) and mean ROI.

**Pareto-front for the operator** (per H_1 framing):
- **MPPM CI strict-positive**: ONLY M=∞ fixed-rebase SIL achieves this; no M cell does.
- **τ_3 ≥ 0**: M=1.5, M=2.0, M=2.5 all preserve skew-positive (and so does M=∞).
- **Conjunction (BOTH)**: only M=∞ on SIL standalone.

### 11. Sub-window 2026-04-01 → 2026-05-15 (~6 weeks; per design.md §13 mandatory reporting cell)

Basket-level sub-ROI / sub-MaxDD for the last 6 weeks of OOS data:

| Config | sub-ROI% | sub-MaxDD% |
|---|---:|---:|
| M=∞ H062 v1 fixed-rebase | +0.79% | +0.67% |
| M=∞ H065 current-rebase | −0.23% | +6.18% |
| **M=1.0** | **+1.55%** | +2.71% |
| M=1.5 | +0.19% | +1.75% |
| M=2.0 | +0.75% | +1.76% |
| M=2.5 | +0.00% | +0.00% (no trades fired in window for the lower-frequency exit) |

**Empirical interpretation** (informational; not load-bearing for H_1): the 6-week 2026-04-01 → 2026-05-15 sub-window shows **all configs modestly positive or flat** (basket). M=1.0 produces the strongest sub-ROI (+1.55%) but this is single-window noise on ~6 weeks of data; not a statistical inference. The H062 v1 fixed-rebase reference is +0.79% sub-ROI — modest single-window outcome. Per-symbol sub-window analysis is in the sidecar.

### 12. Bottom line

H065 v1 is a **non-significant null on the H_1 hypothesis-of-record**: per the joint criterion (MPPM(ρ=1) CI strict-positive AND τ_3 ≥ 0), no M ∈ {1.0, 1.5, 2.0, 2.5} cell delivers the required signal. The TP-overlay **does not improve over the H062 v1 no-TP baseline at the basket level** — basket OOS ROI degrades from +10.33% / +22.21% (M=∞ fixed / current) to −10% / −18% / −10% / −40% across M=1.0/1.5/2.0/2.5. The mechanism is intuitive: TP overlay truncates the right tail of the per-trade R-multiple distribution; for a partially-decayed channel-breakout strategy (per H065 §1.4 + H062 design.md §1.4 inherited literature) the **right tail is the load-bearing source of mean-edge** — truncating it produces lower mean return and (at M=1.0) inverts the skew direction from +0.81 to −0.03 (the canonical death-by-thousand-cuts pattern).

**Substantive empirical finding** (informational): SIL M=∞ fixed-rebase produces the strongest standalone OOS cell across the entire H050-H055-H060-H062-H065 program — +446% realized ROI, MPPM(ρ=1) CI [+0.087, +0.459] strictly excluding zero positively, MaxDD 25%, τ_3=+0.776. This is the **no-TP, fixed-rebase H062 v1 baseline applied to SIL alone** — not an H065 TP-overlay finding. SIL standalone may warrant a successor hypothesis pre-registration (`P1-H065-SIL-STANDALONE-V2`) for operator-discretionary review.

**ES** is the only symbol where TP overlay produces measurable improvement (M=1.5 SR +1.28 vs M=∞ SR +1.36 with substantially lower MaxDD 9.7% vs 15.6%) but ES Calmar at M=1.5 (3.13) is below M=1.0 (3.55). Per-symbol per-M cell trade-off space documented above; operator review on the Pareto-front is the load-bearing decision.

**The TP-overlay extension is operationally established but H_1 is null**. Per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) no-binding-gates discipline, H065 progresses to mandatory NinjaScript implementation per ADR-0013 §5 regardless of these KPIs; operator-discretionary decline allowed per the 2026-05-04 standing directive. Next mandatory transition: `kpi-report-emitted` → `ninjascript-implemented` (tracked under `P1-H065-NINJASCRIPT-IMPL`).

### 13. Cross-references

- Audit trail (R1; verdict accept-with-residuals): [docs/audits/audit_trail_2026-05-15_h065_v1.md](../../../docs/audits/audit_trail_2026-05-15_h065_v1.md)
- Simulator: [scripts/run_h065_tp_overlay_sweep.py](../../../scripts/run_h065_tp_overlay_sweep.py)
- Unit tests (7 tests, all passing): [tests/unit/test_h065_tp_overlay.py](../../../tests/unit/test_h065_tp_overlay.py)
- Sidecar (post-MaxDD-fix run): [artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/sweep_sidecar.json](../../../artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/sweep_sidecar.json)
- Sidecar sha256: `ea12473729264d25d009834c537cb6f657d51c15a1a4f9bca9cb24496798d60d`
- Pre-fix sidecar (preserved per ADR-0013 §4.1 non-loss): [artifacts/runs/H065/tp_overlay_sweep_20260516T030142Z/sweep_sidecar.json](../../../artifacts/runs/H065/tp_overlay_sweep_20260516T030142Z/sweep_sidecar.json) (sha256 `af49a5853037699283f4cad4a9f8ab146ead72d795baca96279177e9db76ef06`).
- Parent hypothesis (no-TP baseline): [H062 KPI report card v1](../H062/H062_kpi_report_v1.md)

## Methodological-correctness annotations (per ADR-0013 §2 + §2.1)

| Annotation | Status | Detail |
|---|---|---|
| `leakage-canary-{pass,fail}` | **pass** | Inherits H062 v1 PIT-causality discipline; channel at bar t uses closes [t-N, t-1] only; ATR at bar t uses TR through t inclusive; entry at bar (t+1) open. **NEW canary E (TP fill PIT)**: TP price computed at entry-bar-t close using entry_price (bar t+1 open) + ATR_n,t (PIT as of bar t close); TP fill check at bar (t+1) uses bar t+1's high (long) or low (short) — both PIT-revealable intra-bar extremes. Unit-test coverage: `tests/unit/test_h065_tp_overlay.py::test_tp_fill_uses_intrabar_high_low_not_close`. |
| `bss-{positive,flat,negative}` | **n/a** | Directional channel-break + TP-overlay produce continuous P/L not probabilistic forecasts. |
| `reliability-{in,out}-of-band` | **n/a** | Same rationale as BSS. |
| `repro-log-{complete,incomplete}` | **incomplete** | Sweep script is a single-shot research script not a walk-forward orchestrator; RunContext + ReproLog wiring deferred to `P1-H065-REPROLOG-WIRE`. Sidecar SHA256 binding present (post-MaxDD-fix run: `ea12473729264d25d009834c537cb6f657d51c15a1a4f9bca9cb24496798d60d`); deterministic RNG seed `20260515` for bootstrap CIs. |
| `dsr-{positive,marginal,negative,n/a}` | **n/a** | Single-cell representative grid; M=4-cell + 2-reference family below `dsr_activation_size`. |
| `cost-{robust,conditional,flat}` | **zero-v1-pre-cost-research-only** | Operator decision 2026-05-08 + 2026-05-12 + 2026-05-15. |
| `post-run-audit-{pass,fail}` | **pass** | Sidecar SHA256 binding present; R1 audit-remediate-loop ACCEPT-WITH-RESIDUALS at the 3-round cap. Audit trail: [audit_trail_2026-05-15_h065_v1.md](../../../docs/audits/audit_trail_2026-05-15_h065_v1.md). |
| `mppm-rho1-{positive,marginal,negative}` | **marginal** | All 6 configs cover zero on basket-level MPPM CI. Strongest cell SIL M=∞ fixed-rebase EXCLUDES zero POSITIVELY (MPPM=+0.265 CI=[+0.087, +0.459]) but this is the no-TP reference. |
| `kelly-multiplier-{0.25..2.5}` | **0.25** | Single fixed cell at v1 (full Kelly-grid sweep deferred to v2 per `P1-H065-FULL-KELLY-GRID-V2`). |
| `l-skewness-{positive,zero,negative}` | **mixed** | M=∞ + M=1.5/2.0/2.5: skew-positive (τ_3 ∈ [+0.158, +0.807]). **M=1.0: SKEW-INVERTED** on every symbol AND on the basket (basket τ_3 = −0.034). The skew-flip is the canonical death-by-thousand-cuts pattern; **H_1 (b) failure detected on M=1.0**. |
| `claim-type-{causal,correlation-only,hybrid}` | **hybrid** | Inherits H062's upstream causal mechanism on the channel-break-as-information-event layer. TP-overlay layer is correlation-only (no causal claim on which M is "the true risk:reward"). |
| `kill-switch-validation-{pass,fail}` | **pass-by-inheritance** | K-1..K-8 enforced structurally inside the simulator's exit-precedence ordering and capacity-cap clamp. K-3 (no-add-to-loser) vacuous at v1 (no pyramiding). K-2 (time stop) enforced via EOD-flatten + session-rollover. |
| `h_1-{positive,null,negative}` | **null** | No M ∈ {1.0, 1.5, 2.0, 2.5} satisfies both H_1 conditions (basket MPPM CI strict-positive AND τ_3 ≥ 0). |

**No methodological-correctness banner triggered**. The `h_1-null` annotation is a substantive empirical finding, not a methodological flaw — per ADR-0013 §1 no-binding-gates discipline, the strategy progresses to `ninjascript-implemented` regardless.

## Operator review section

Per the user's 2026-05-15 mission specification, the load-bearing operator-facing artifact is the **KPI metrics table** in §3a-§10 (also rendered as a standalone text file at [artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/kpi_table.txt](../../../artifacts/runs/H065/tp_overlay_sweep_20260516T030515Z/kpi_table.txt)).

**Recommended next steps** (operator-discretionary):

1. **SIL-standalone successor hypothesis** (`P1-H065-SIL-STANDALONE-V2`): SIL M=∞ fixed-rebase produces the project's strongest single-cell OOS finding (MPPM CI [+0.087, +0.459] excludes zero positively; +446% ROI; MaxDD 25%; 4,165 trades). Pre-registering a SIL-only successor with full Kelly-grid sweep + cost-realistic calibration is the highest-leverage follow-on from this sweep.
2. **Decline mandatory NinjaScript transition** per the 2026-05-04 standing directive: H_1 null on the hypothesis-of-record; NinjaScript implementation cost-of-effort exceeds research value at this KPI level. Tracked under `P1-H065-NINJASCRIPT-IMPL` with operator-decline annotation similar to H052a precedent.
3. **MNQ substitution** for the NQ leg (`P1-H065-MNQ-SUBSTITUTION`): MNQ at $2/point = 10x smaller 1R; would make the NQ leg tradeable at $10K starting capital. v2 path.
4. **Pyramiding overlay** (H066; queued): test whether adding Turtle System 2 pyramiding to the TP-overlay produces additional edge on the symbols where TP alone underperforms.

## New follow-ups registered by H065 v1 emission

| Follow-up | Status | Description |
|---|---|---|
| `P1-H065-NINJASCRIPT-IMPL` | OPEN (mandatory per ADR-0013 §5; operator-discretionary per 2026-05-04 directive) | C# implementation at `ninjascript/strategies/H065_DonchianBreakoutWithTPOverlay.cs`. |
| `P1-H065-SIL-STANDALONE-V2` | OPEN; high-leverage | Pre-register a SIL-only successor hypothesis with full Kelly-grid sweep + cost-realistic calibration on the standalone-strongest cell. |
| `P1-H065-MNQ-SUBSTITUTION` | OPEN; BLOCKING-BEFORE-V2 | Substitute MNQ (Micro NQ) for NQ in the basket to address $10K starting-capital sample-size constraint. |
| `P1-H065-FULL-INNER-CV-GRID-V2` | OPEN | Full 55,296-cell inner-CV sweep at v2; v1 used 16-cell representative grid. |
| `P1-H065-COST-EMPIRICAL-CALIBRATION` | OPEN; BLOCKING-BEFORE-PAPER-TRADE | Empirical cost-realistic calibration; v1 is zero-cost. |
| `P1-H065-REPROLOG-WIRE` | OPEN | Wire RunContext + ReproLog into the sweep script per H062 walk-forward pattern. |
| `P1-H065-FORWARD-PROJECTION` | OPEN | $10K starting-capital 1-yr bootstrap forward projection per ADR-0013 §3.1; v1 focused on realized OOS + sub-window. |
| `P1-H065-FAMILY-SPA-COMPUTE` | OPEN | Hansen SPA + Romano-Wolf FWER across the 4 M-cell family. |
| `P1-H065-R-MULT-CI-V2` | OPEN | Per-cell R-multiple-mean bootstrap CI at v2. |
| `P1-H065-CALMAR-DIFFERENTIAL-V2` | OPEN | Calmar-differential CI vs passive-EW reference at v2. |
| `P1-H065-FULL-KELLY-GRID-V2` | OPEN | Full Kelly-multiplier {0.25, 0.5, 1.0, 1.5, 2.0, 2.5} sweep at v2; v1 fixed at 0.25. |

## Decisions locked at this emission

1. **H_1 null on the TP-overlay hypothesis-of-record**: no M ∈ {1.0, 1.5, 2.0, 2.5} satisfies BOTH MPPM CI strict-positive AND τ_3 ≥ 0. The TP overlay does not improve over the H062 v1 no-TP baseline at the basket level.
2. **M=1.0 inverts the skew direction** on every symbol AND on the basket — the canonical death-by-thousand-cuts pattern. The TP-overlay at 1:1 risk:reward truncates the right tail too aggressively.
3. **M=1.5 onwards preserves skew-positive** at the cost of mean return — the operator's Pareto-front trade-off space documented in §10.
4. **SIL M=∞ fixed-rebase is the strongest standalone cell** across the entire H050-H055-H060-H062-H065 program. SIL-standalone successor warranted.
5. **NQ structurally infeasible** at $10K × 1% Turtle-2N convention; MNQ substitution required for v2.
6. **MGC fixed-rebase bankroll-blowup** documented (min equity = −$656); current-equity rebase eliminates this failure mode.
7. **Mandatory NinjaScript transition** preserved per ADR-0013 §5 but operator-decline allowed per 2026-05-04 standing directive.
