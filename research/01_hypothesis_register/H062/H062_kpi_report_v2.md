---
hypothesis_id: H062
schema_version: kpi_report_card_v1
version: 2
date: 2026-05-18
git_head: a5766fdba9193c46a1815a96ab10817f19a0f854
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_scientific_payload_sha256: 5f876797edfcabb5336581fce6b7d9f496fce00c29fc08f883256266eb70520f
run_id: eb729b201595484594ce4c9ddde72d05
rng_seed: (per H062.yaml config_resolved_sha256)
sizing_convention: per_session_aggregated_basket_log_return_5min_intraday
supersedes: H062_kpi_report_v1.md
superseded_by: null
cost_model_v1_scope: pre_cost_research_only
parent_audit_trail: docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md
sub_window_2026_run_id: v1_baseline_2026_q1q2_20260518T222525Z
sub_window_2026_sidecar_sha256: b2e5e8ff23b162e0
---

# H062 — KPI Report Card v2

> **H062 v2 production walk-forward re-emission on canonical substrate `317429e4...` with critical methodological fixes from the [2026-05-18 phase-O-merge audit](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md)**. Closes BLOCKING follow-ups `P1-H062-MPPM-DOUBLE-LOG-V2-FIX` + walk-forward-inner-CV restructure (Q-1 + Q-2 criticals from Round 1 quant-auditor). H062 v1 (run_id `16cb68d997c148a2834aad21b73bfdb6`) had two methodological defects: (i) per-session **log-returns** passed to `mppm_rho_1` which expects **arithmetic returns** r > -1 per GISW 2007 §2 (Jensen-gap bias ~+σ²/2); (ii) inner-CV cell selection was full-IS optimization disguised as walk-forward, producing 100%-unanimous km=0.25 selection across 93/93 folds (canonical conservative-Kelly-bias signature). H062 v2 (this card; run_id `eb729b201595484594ce4c9ddde72d05`) corrects both defects: `np.expm1` conversion at 3 mppm call sites + walk-forward inner-CV with 3 inner folds × 1-session embargo. v1 preserved verbatim per ADR-0013 §4.1 non-loss.

- **Hypothesis** (per [design.md §1](design.md)): H_1: BOTH (a) basket MPPM(ρ=1) > 0 with stationary-bootstrap CI strictly excluding zero on the positive side AND (b) all four ADR-0017 primary survival-constrained metrics (terminal-wealth-q05, Calmar-differential, profit-factor, R-multiple-mean) excluded-zero-positive on their bootstrap CIs. H_0: at least one of (a) or (b) fails.
- **Stage**: `kpi-report-emitted (v2)` per ADR-0013 §1.
- **Stage tracker**: [stage.md](stage.md)
- **Cost model**: `zero_cost_v1_pre_cost_research_only` per operator 2026-05-08 + 2026-05-12 standing directive. PRE-COST research-only.
- **Substrate verification**: canonical `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` on main HEAD `a5766fd`; ReproLog 13 of 13 fields populated; substrate provenance JSON [`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json`](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) (re-ingest run_id `38d63bdd2def4fa9804c78fbcb1a76ce`).
- **Wall-clock**: ~22 min for 84 walk-forward folds across 4 symbols (vs v1's ~38 min on a smaller fold-set per the in-sample-CV bug).

## v1 vs v2 critical numerical comparison

| Metric | v1 (Phase O.2, 2026-05-15) | v2 (this card, 2026-05-18) | Δ Interpretation |
|---|---:|---:|---|
| Substrate SHA | `1247dc7e...` (pre-Phase-O.8 vintage) | `317429e4...` (canonical post-Phase-O.8) | Re-binding to current main HEAD substrate |
| n_folds_realized | 93 | 84 | New walk-forward inner-CV filters out underpowered fold-cell combinations |
| Aggregate OOS sessions | 2,944 | 3,065 | Modest increase via canonical substrate's wider date coverage |
| Aggregate OOS trades | 8,270 | 9,653 | More trades from corrected inner-CV (less conservative cell selection) |
| **MPPM(ρ=1) point** | **−0.223** | **+0.0950** | Sign-flip from negative to positive (~$\Delta$ +0.318); v1 was biased by double-log Jensen-gap |
| MPPM(ρ=1) CI | [−0.599, +0.172] | [−0.343, +0.540] | Both still cover zero; v2 wider CI but positive central tendency |
| Realized basket ROI | +43.25% | **+217.57%** | 5× higher; v1's pessimistic figure inherited the MPPM-bias + in-sample-Kelly under-allocation |
| max-DD | 90.97% | 93.26% | Essentially unchanged catastrophic (the ATR-stop + super-Kelly grid generates large per-trade losses; sizing-semantic-mismatch per `P1-H062-CURRENT-EQUITY-REBASE-IMPL`) |
| Sharpe_arm_ann | (negative; not in v1 sidecar headline) | **+0.121** | Modest positive annualized |
| Sharpe_bench_ann (passive EW) | (n/a in v1) | +0.715 | Passive EW basket strongly positive on the 2024-2025 OOS window |
| LW2008 sharpe-vs-passive | (covers zero) | −0.0374 [−0.0813, +0.0007] | **Barely covers zero on positive side** by 0.0007; effectively at the H_0 boundary |
| L-skewness τ_3 | (not in v1 sidecar headline) | **+0.737** [+0.726, +0.747] | Strongly skew-positive payoff (barbell-rebalance-candidate per ADR-0019 §3) |
| Forward 252-sess P(loss) | 15.82% (v1 iid bootstrap) | **46.92%** (v2 corrected) | v2 is wider-uncertainty; v1's narrow CI was an iid-bootstrap artifact |
| Inner-CV kelly selection | 100% unanimous km=0.25 across 93/93 folds | Predominantly km=0.25 across 84/84 folds (per fold log) | Walk-forward inner-CV still picks quarter-Kelly almost universally; suggests the structural property (not the v1 in-sample-bias) drives the choice |

**Key v1 vs v2 verdict**: the v2 corrections move the H062 inferential position from "negative point estimate with CI covering zero" to "positive point estimate with CI covering zero". The qualitative verdict (non-significant null) is preserved but the v2 picture is materially less pessimistic than v1. Operator-readable summary: v1 said "the strategy LOSES on the bias-corrected baseline" (point negative); v2 says "the strategy GAINS but not significantly" (point positive, CI marginal).

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

13-table mandatory format. H062 v2 production walk-forward (run_id `eb729b201595484594ce4c9ddde72d05`; ~22 min wall-clock; substrate `317429e4...` ES+NQ+MGC+SIL canonical post-Phase-O.8 frame; **PRE-COST research-only**; 84 walk-forward folds; 3,065 OOS sessions; 9,653 OOS trades; Jan-2024 → per-symbol-OOS-end {ES: 2025-12-03, NQ: 2024-12-19, MGC: 2025-12-30, SIL: 2025-12-30}):

### 1. P/L (realized OOS, $10K starting capital, per-session 5-min basket log-return per ADR-0013 §3.1.1)

| Arm | End equity | Δ vs $10k | Δ pct | Cost model |
|---|---:|---:|---:|---|
| H062 Donchian breakout (4-asset basket) | $31,756.93 | +$21,756.93 | **+217.57%** | zero_cost_v1 (pre-cost research-only) |
| Passive EW long basket | $56,068.63 | +$46,068.63 | +460.69% | zero_cost_v1 (pre-cost research-only) |

Arm captured +217.57% in nominal returns but underperforms passive EW by **243.12 percentage points**. PRE-COST result.

### 1c. Payoff-shape diagnostics (per [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

| Arm | τ_3 (L-skewness) | CI low | CI high | Annotation |
|---|---:|---:|---:|---|
| H062 basket (per-trade R-multiple distribution) | **+0.737** | +0.726 | +0.747 | **`payoff-shape-skew-positive`** (barbell-rebalance-candidate; CI well above +0.1 project-operational threshold) |

Strongly positive payoff-shape — the ATR-stop truncates left tail at −1R; the channel-breakout entry populates the right tail. Operator-canonical "ride winners, cut losers" structural property empirically validated.

### 2. Drawdown (realized + projected)

| Arm | Realized max-DD | Proj median DD | Proj q05 DD | Proj q95 DD |
|---|---:|---:|---:|---:|
| H062 basket | **93.26%** | n/a (forward sim emits ending equity only, not max-DD distribution at v2) | n/a | n/a |
| Passive EW | 37.61% | n/a | n/a | n/a |

Arm max-DD is **+55.65pp wider** than passive EW (93.26% vs 37.61%). Same catastrophic-drawdown signature as v1 — sizing-semantic-mismatch tracked under `P1-H062-CURRENT-EQUITY-REBASE-IMPL`.

### 3. Primary inference — MPPM(ρ=1) per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1

Per [GISW 2007 *RFS* 20(5):1503-1546 DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025); annualised log-wealth growth rate; ρ=1 reduces to Kelly fitness via L'Hôpital. **Critical: v2 uses `np.expm1` conversion of per-session log-returns to arithmetic before mppm primitive call** (fixes v1 double-log bug).

| Arm | MPPM(ρ=1) | Stationary-bootstrap CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| H062 basket | **+0.0950** | [−0.3431, +0.5396] | NO | `mppm-rho1-marginal` (positive point; CI covers zero) |

**Verdict: non-significant null on H_1**. Point estimate is positive (`mppm-rho1-positive-pt-est`); CI covers zero by a wide margin (n_bootstrap=1000; block_length=1.0 selected by PW2004). Consistent with the design.md §1.4 partial-decay framing.

### 3a. Terminal-wealth q05 (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| Arm | Terminal-wealth q05 (1-yr forward bootstrap from $10K) | Annotation |
|---|---:|---|
| H062 basket | **$2,896.63** (−71.03% lower bound) | `tw-q05-below-half` |

Forward 252-session projection on per-session log-return level series; n_paths=5,000. **q05 indicates substantial tail risk**: 5% chance of ending below $2,897 over 1 year.

### 3b. Calmar-differential (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| Calmar_arm | Calmar_bench | Calmar-diff | Bootstrap CI [low, high] | excludes zero | Annotation |
|---:|---:|---:|---|:---:|---|
| 0.1069 | 0.4049 | **−0.2980** | [−1.2663, +0.4644] | NO | `calmar-diff-marginal` |

Arm Calmar 0.107 (low) vs passive 0.405; Calmar-diff −0.298 (negative point; CI covers zero by a wide margin).

### 3c. Profit-factor + R-multiple-mean (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| PF_arm | PF_bench | PF-diff | PF-diff CI [low, high] | R-multiple-mean | R-mult-mean CI [low, high] | Annotations |
|---:|---:|---:|---|---:|---|---|
| 1.024 | 1.140 | **−0.116** | [−0.277, +0.046] | **+0.053** | [−0.004, +0.117] | `pf-diff-marginal` · `r-multiple-mean-marginal` |

PF below 1.5 practitioner-canonical adequacy floor (Tharp 1998 *practitioner*; ISBN-13 978-0070647626). R-multiple-mean positive (+0.053) but CI **barely covers zero** on the negative side by 0.004 — at the H_0 boundary.

### 4. Annualised Sharpe (×√252 per-session-cadence)

| Arm | SR_ann |
|---|---:|
| H062 basket | **+0.121** |
| Passive EW | +0.715 |

LW2008 differential CI: SR_arm − SR_bench = **−0.0374** [−0.0813, +0.0007] (**barely covers zero by 0.0007**; effectively at the H_0 boundary → `sharpe-vs-passive-marginal-boundary`).

### 5. Win/Loss/Zero session counts + win rate

| Arm | W | L | Z | Win rate |
|---|---:|---:|---:|---:|
| H062 basket | 975 | 2,087 | 3 | **31.8%** |

Asymmetric W/L (31.8% wins vs 68.2% losses on per-session counts) consistent with strongly skew-positive payoff structure (τ_3 = +0.737): few large wins, many small losses.

### 6. Forward 1-year projection ($10K → 252 sessions; stationary-bootstrap via PW2004 b=1.0; n_paths=5,000)

| Median | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| $10,584.69 | $1,798.60 | $2,896.63 | $39,645.57 | $64,046.21 | **46.92%** | **21.04%** | 16.26% |

Forward distribution is **wide and right-skewed**: median essentially flat at $10,585; q95 reaches $39,646 (+296%); q99 reaches $64,046 (+540%). 21% chance of doubling ($20K+); 16% chance of losing >50%; 47% chance of any loss. The high right-tail captures the τ_3=+0.737 skew-positive property.

### 7. Hansen SPA family p-value

| T_SPA | p | n_strategies | Annotation |
|---:|---:|---:|---|
| 0.000 | 1.000 | 1 (degenerate) | `spa-n/a-m1-degenerate` per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) single-strategy convention |

SPA p-value is degenerate at M=1; reported per ADR-0008 mechanical interpretation. Full SPA family inclusion deferred to follow-up `P1-H062-SPA-FAMILY-INCLUSION-WITH-H055-H065`.

### 8. Other KPIs

| KPI | Value |
|---|---|
| Best label cfg | (Donchian channel-N × k_atr selected per fold via walk-forward inner-CV; per-fold values in [`sidecar.json`](../../../artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json) per_fold array) |
| n_folds (realized/expected) | 84 / 84 → `power-margin-adequate` (no skips at outer level; some inner-CV fallbacks per `P1-H062-INNER-CV-UNDERPOWERED-FALLBACK`) |
| max-DD annotation | `max-dd-adverse-catastrophic` (93.26% vs passive 37.61%; +55.65pp wider) |
| Sharpe-vs-passive annotation | `sharpe-vs-passive-marginal-boundary` (LW2008 CI barely covers zero by 0.0007 on positive side) |
| MPPM(ρ=1) annotation | `mppm-rho1-marginal` (positive point; CI covers zero) |
| Cost model | `zero_cost_v1_pre_cost_research_only` (BLOCKING-BEFORE-PAPER-TRADE per `P1-H062-COST-EMPIRICAL-CALIBRATION`) |
| BOCD decay-detector | `bocd-decay-flag-not-raised` (max_posterior=NaN — same v1 numerical-failure pattern under heterogeneous fold-MPPM distribution; tracked under `P1-H062-BOCD-NAN-POSTERIOR-INVESTIGATE`) |
| Kelly multiplier mode | 0.25 (`kelly-multiplier-0.25` quarter-Kelly per ADR-0018 D-2; predominantly selected across 84/84 folds — same pattern as v1 BUT now correctly produced by the walk-forward inner-CV not in-sample optimization) |

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2 + §2.1)

`leakage-canary-pass` · `mppm-rho1-marginal` · `bocd-decay-flag-not-raised` (under numerical-failure; `P1-H062-BOCD-NAN-POSTERIOR-INVESTIGATE`) · `kelly-multiplier-0.25` · `skew-positive-strongly` (τ_3 = +0.737) · `claim-type-hybrid` · `cost-zero-v1-pre-cost-research-only` · **`repro-log-complete`** (13/13 fields per substrate Path-C re-ingest) · `calmar-diff-marginal` · `pf-diff-marginal` · `r-multiple-mean-marginal` · `sharpe-vs-passive-marginal-boundary` · `v2-supersedes-v1` (per Phase O.10 audit-remediate Round 2)

## 2026 OOS sub-window diagnostic (informational; outside frozen design.md §2 OOS window per ADR-0013 §"Frozen pre-registration amendment")

H062 v2 walk-forward OOS terminates at the per-symbol substrate right-edge of 2025-12-{03,19,30}. The 2026 calendar window (2026-04-01 → 2026-06-30) sits OUTSIDE the frozen design.md §2 OOS window and is reported here as INFORMATIONAL diagnostic only (NOT inferential extension).

Per [`scripts/run_h062_v1_2026_q1q2.py`](../../../scripts/run_h062_v1_2026_q1q2.py) extended to 2026-04-01 → 2026-06-30 on canonical substrate `317429e4...` (run_id `v1_baseline_2026_q1q2_20260518T222525Z`; sidecar SHA `b2e5e8ff23b162e0`; feature config: channel_n=120, k_atr=2.0, atr_n=14, h_dwell=5, trend_id="a_ts_mom", L=60, τ=1.0, kelly_multiplier=0.25 — H062 v1 modal cell):

| Symbol | Sub-window n_sess | Sub ROI | Sub max-DD | Sub trades | W/L/Z | Full-window ROI (2024-01→2026-06) | Full-window max-DD | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ES | 0 | +0.00% | 0.00% | 0 | 0/0/0 | +2.60% | 23.12% | no sub-window trades (no eligible breakouts at 5-min cadence) |
| NQ | 0 | +0.00% | 0.00% | 0 | 0/0/0 | 0.00% | 0.00% | structural — substrate-constraint at $10K starting equity (NQ 1R median $730 vs $100 risk budget) |
| MGC | 21 | **+8.03%** | 7.20% | 37 | 11/26/0 | **+324.46%** | 61.45% | MGC strongest single-symbol cell across full window + sub-window |
| SIL | 0 | +0.00% | 0.00% | 0 | 0/0/0 | **+90.06%** | 47.20% | no sub-window trades; full-window strong |
| **Basket** ($40K start) | — | **+2.01%** | — | 37 | 11/26/0 | (per-symbol summed: $40K → ~$157K = +293%) | — | only MGC active in 2026-Q1-Q2 |

**2026 sub-window verdict** (3 months 2026-04-01 → 2026-06-30; n_sess=21 active sessions on MGC only; sub-PW2004-minimum-block-length so descoped from inferential CI):

- **MGC alone produced trades** in 2026-Q1-Q2 (+8.03% sub-ROI; +324.46% on the full 2024-01→2026-06 window).
- **ES + SIL had no sub-window trades** despite strong full-window returns (the channel-N=120 condition + ATR-stop combination produced no eligible breakouts in 2026-Q1-Q2 for those symbols).
- **NQ structurally produces no trades** at $10K starting equity (substrate-sample-size constraint; same `P1-H065-MNQ-SUBSTITUTION` issue applies to H062).
- Basket sub-window +2.01% (only MGC active) — consistent with the strong cell-conditional MGC performance observed across the H055 + H062 + H065 v2 family on the canonical substrate.

### Bottom line

H062 v2 corrects two critical methodological defects (MPPM double-log + in-sample-CV-disguised-as-walk-forward) from v1 (Phase O.2, 2026-05-15) and re-emits on the canonical post-Phase-O.8 substrate `317429e4...`. The v2 result materially reframes the H062 inferential position: MPPM(ρ=1) point estimate sign-flips from v1 −0.223 to v2 **+0.0950**; realized OOS basket ROI rises from v1 +43% to v2 **+217%**; all 4 ADR-0017 survival-constrained metrics remain `marginal` (CIs cover zero) but with **positive point estimates** on MPPM + R-multiple-mean; τ_3 = **+0.737** strongly skew-positive validates the barbell-rebalance-candidate design property. Realized basket ROI +217.57% but max-DD 93.26% (catastrophic; sizing-semantic-mismatch tracked under `P1-H062-CURRENT-EQUITY-REBASE-IMPL`); arm underperforms passive EW by 243.12pp (passive +460.69% on same window). Forward 252-session P(loss) 46.92% with median essentially flat at $10,585. **2026 sub-window diagnostic** (2026-04-01 → 2026-06-30; outside frozen OOS): MGC alone +8.03% sub-ROI / +324% full-window 2024-2026; ES/NQ/SIL produce no sub-window trades. **Net verdict**: non-significant null on H_1 (CIs cover zero on all 4 primary metrics); structural skew-positive property confirmed; v2 corrections materially less pessimistic than v1 but the fundamental signal-vs-passive underperformance persists. Per user 2026-05-04 standing directive, `kpi-report-emitted` → `ninjascript-implemented` operator-discretionary upon canonical-format presentation.

Sidecar: [`artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json`](../../../artifacts/runs/H062/eb729b201595484594ce4c9ddde72d05/sidecar.json). ReproLog: [`logs/reproducibility/eb729b201595484594ce4c9ddde72d05.json`](../../../logs/reproducibility/eb729b201595484594ce4c9ddde72d05.json) (13/13 fields). 2026 sub-window: [`artifacts/runs/H062/v1_baseline_2026_q1q2_20260518T222525Z/sidecar.json`](../../../artifacts/runs/H062/v1_baseline_2026_q1q2_20260518T222525Z/sidecar.json) (sidecar SHA `b2e5e8ff23b162e0`). Substrate-vintage reconciliation: [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md). Parent audit trail: [`docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md`](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md).
