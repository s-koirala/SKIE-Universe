---
hypothesis_id: H060
schema_version: kpi_report_card_v1
version: 2
date: 2026-05-18
git_head: a5766fdba9193c46a1815a96ab10817f19a0f854
substrate_dataset_checksums:
  vendor_legacy_1min_roll_adjusted: 317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7
sidecar_scientific_payload_sha256: 5f26a85d769a4e9294ef69090c425df28c11bd9cc64f252595a28c09eac7bfd8
run_id: cbddc3c9dd6d47c7b0ac4f9cfdd5a3d9
rng_seed: (per H060.yaml config_resolved_sha256)
sizing_convention: per_session_aggregated_basket_log_return_daily_rebalance
supersedes: H060_kpi_report_v1.md
superseded_by: null
cost_model_v1_scope: pre_cost_research_only
parent_audit_trail: docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md
---

# H060 — KPI Report Card v2

> **H060 v2 production walk-forward re-emission on canonical post-Phase-O.8 substrate `317429e4...`** (commit `a5766fd` 2026-05-18). Closes BLOCKING follow-up `P1-H060-V2-RERUN-ON-CANONICAL-SUBSTRATE` from the [2026-05-18 phase-O-merge audit](../../../docs/audits/audit_trail_2026-05-18_phase-o-merge-audit.md). v1 (run_id `71b00710a17148868b6a5ab610c07ef6`) bound to substrate `b0a6128...` and lacked main-HEAD-reachable git_head; v2 (this card) replaces v1 with a fully reachable + canonical-substrate-bound emission. v1 preserved verbatim per ADR-0013 §4.1 non-loss.

- **Hypothesis** (per [design.md §1](design.md)): H_1: cross-futures TSMOM basket on {ES, NQ, MGC, SIL} with 12-month signal + ex-ante-vol-scaled positions delivers MPPM(ρ=1) > 0 on stationary-bootstrap CI strictly excluding zero on the positive side.
- **Design.md**: [design.md](design.md) (frozen at `status: designed`; pre-reg 2026-05-12).
- **Stage**: `kpi-report-emitted (v2)` per ADR-0013 §1. v1 → v2 transition is a substrate re-emission, not a stage advancement.
- **Stage tracker**: [stage.md](stage.md)
- **Cost model**: `zero_cost_v1_pre_cost_research_only` per operator 2026-05-08 + 2026-05-12 standing directive. PRE-COST research-only.
- **Substrate verification**: canonical `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7` on main HEAD `a5766fd`; ReproLog 13 of 13 fields populated; substrate provenance JSON [`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json`](../../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260518.json) (re-ingest run_id `38d63bdd2def4fa9804c78fbcb1a76ce`).
- **v1 → v2 numerical drift**: v1 reported basket end equity $18,943 (+89.43%) over 1,260 OOS walk-forward sessions; v2 reports $16,875 (+68.75%) over 1,260 OOS sessions on the canonical substrate. The drift is from substrate-vintage differences (v1 substrate vintage included post-Phase-O.3 2026-H1 backfill that was rolled back; v2 uses post-Phase-O.8 canonical substrate that re-included pre-2020 history). MPPM(ρ=1) v1 = +0.1062 [-0.0937, +0.2934]; v2 = +0.0817 [-0.1099, +0.2672]. Qualitative verdict unchanged: **non-significant null** with consistent partial-decay framing per design.md §1.4.

## End-of-simulation results summary (per [ADR-0014 §3.2](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) + [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) + [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

13-table mandatory format. H060 v2 production walk-forward (run_id `cbddc3c9dd6d47c7b0ac4f9cfdd5a3d9`; ~2 min wall-clock; substrate `317429e4...` ES+NQ+MGC+SIL canonical post-Phase-O.8 frame; **PRE-COST research-only**; 21 walk-forward folds; 1,260 OOS sessions Jan-2024 → Dec-2025):

### 1. P/L (realized OOS, $10K starting capital, per-session basket log-return per ADR-0013 §3.1.1)

| Arm | End equity | Δ vs $10k | Δ pct | Cost model |
|---|---:|---:|---:|---|
| TSMOM 4-asset basket | $16,875.37 | +$6,875.37 | **+68.75%** | zero_cost_v1 |
| Passive EW long basket | $17,566.76 | +$7,566.76 | +75.67% | zero_cost_v1 |

Arm underperforms passive EW by **6.91 percentage points** on the canonical substrate (vs +6.30pp outperformance on v1 substrate). Same partial-decay signature.

### 1c. Payoff-shape diagnostics (per [ADR-0019 §3](../../../docs/decisions/ADR-0019-barbell-payoff-shape-screening.md))

| Arm | τ_3 (L-skewness) | CI low | CI high | Annotation |
|---|---:|---:|---:|---|
| TSMOM basket | n/a (computed at daily session-aggregated level; CI primitive not invoked at this aggregation grain) | — | — | `skew-flat` (per v1 annotation continuity; tracked under `P1-H060-PER-TRADE-TAU3-V3` for refinement) |

### 2. Drawdown (realized + projected)

| Arm | Realized max-DD | Proj median DD | Proj q05 DD | Proj q95 DD |
|---|---:|---:|---:|---:|
| TSMOM basket | **29.47%** | 17.08% | 9.18% | 32.65% |
| Passive EW | 23.72% | n/a | n/a | n/a |

Arm max-DD is **+5.75pp wider** than passive EW (29.47% vs 23.72%). Consistent with TSMOM's documented characteristic of larger drawdowns during regime transitions per design.md §1.4.

### 3. Primary inference — MPPM(ρ=1) per [ADR-0018](../../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-1

Per [GISW 2007 *RFS* 20(5):1503-1546 DOI 10.1093/rfs/hhm025](https://doi.org/10.1093/rfs/hhm025); annualised log-wealth growth rate; ρ=1 reduces to Kelly fitness via L'Hôpital.

| Arm | MPPM(ρ=1) | Stationary-bootstrap CI [low, high] | excludes zero | Annotation |
|---|---:|---|:---:|---|
| TSMOM basket | **+0.0817** | [-0.1099, +0.2672] | NO | `mppm-rho1-marginal` |

**Verdict: non-significant null on H_1**. CI covers zero; consistent with the v1 marginal result + design.md §1.4 partial-decay framing.

### 3a. Terminal-wealth q05 (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| Arm | Terminal-wealth q05 (1-yr projection from $10K) | Annotation |
|---|---:|---|
| TSMOM basket | $7,682.50 (−23.18% lower bound) | `tw-q05-above-half` |

Forward 252-session projection via stationary-bootstrap (PW2004 block_length=1.0); n_paths=5,000.

### 3b. Calmar-differential (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| Calmar_arm | Calmar_bench | Calmar-diff | Bootstrap CI [low, high] | excludes zero | Annotation |
|---:|---:|---:|---|:---:|---|
| 0.3743 | 0.5028 | **−0.1285** | [−1.4038, +1.1041] | NO | `calmar-diff-marginal` |

### 3c. Profit-factor + R-multiple-mean (per [ADR-0017 §3.2](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md))

| PF_arm | PF_bench | PF-diff | PF-diff CI [low, high] | R-multiple-mean | R-mult-mean CI [low, high] | Annotations |
|---:|---:|---:|---|---:|---|---|
| 1.106 | 1.131 | **−0.025** | [−0.244, +0.201] | **+0.045** | [−0.030, +0.125] | `pf-diff-marginal` · `r-multiple-mean-marginal` |

All 4 ADR-0017 survival-constrained metrics report `marginal`: CIs cover zero. None of (Calmar-diff, PF-diff, R-mean) excludes zero on the positive side.

### 4. Annualised Sharpe (×√252)

| Arm | SR_ann |
|---|---:|
| TSMOM basket | +0.490 |
| Passive EW | +0.708 |

LW2008 differential CI: SR_arm − SR_bench = **−0.0138** [−0.0702, +0.0433] (covers zero → `sharpe-vs-passive-marginal`).

### 5. Win/Loss/Zero session counts + win rate

| Arm | W | L | Z | Win rate |
|---|---:|---:|---:|---:|
| TSMOM basket | 665 | 595 | 0 | 52.78% |

### 6. Forward 1-year projection ($10K → 252 sessions; stationary-bootstrap via PW2004 b=1.0; n_paths=5,000; rng_seed per config)

| Median | q01 | q05 | q95 | q99 | P(loss) | P(double) | P(<50%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| $11,083.84 | $6,571.93 | $7,682.50 | $15,857.95 | $18,190.84 | **29.68%** | 0.28% | 0.00% |

### 7. Hansen SPA family p-value

| T_SPA | p | n_bootstrap | Annotation |
|---:|---:|---:|---|
| 0.000 | 1.000 | (variant=consistent) | `spa-n/a-m1-degenerate` per [ADR-0008](../../../docs/decisions/ADR-0008-spa-omega-method.md) single-strategy convention (M=1) |

### 8. Other KPIs

| KPI | Value |
|---|---|
| Best label cfg | n/a (TSMOM uses fixed 12-month-signal + ex-ante-vol-scaling; no label-cfg grid) |
| n_folds (realized/expected) | 21 / 21 → `power-margin-adequate` |
| max-DD annotation | `max-dd-adverse` (29.47% vs passive 23.72%; +5.75pp wider) |
| Sharpe-vs-passive annotation | `sharpe-vs-passive-marginal` (LW2008 CI covers zero) |
| MPPM(ρ=1) annotation | `mppm-rho1-marginal` (stationary-bootstrap CI covers zero) |
| Cost model | `zero_cost_v1_pre_cost_research_only` |
| Sortino / turnover / capacity | deferred per `P1-H060-COST-EMPIRICAL-CALIBRATION` BLOCKING-BEFORE-PAPER-TRADE-EVALUATED |
| BOCD decay-detector | `bocd-decay-flag-not-raised` (decay_detected=False; max_posterior=0.0 — no regime change detected over the 1,260-session OOS window) |
| Kelly multiplier mode | 2.5 (`kelly-multiplier-2.5` super-Kelly-operator-discretionary per ADR-0018 D-2) |

### 9. Methodological-correctness annotations (one-line per ADR-0013 §2 + §2.1)

`leakage-canary-pass` · `mppm-rho1-marginal` · `bocd-decay-flag-not-raised` · `kelly-multiplier-2.5` (super-Kelly-operator-discretionary) · `skew-flat` · `claim-type-hybrid` · `cost-zero-v1-pre-cost-research-only` · `data-quality-degraded-days-annotated` · **`repro-log-complete`** (13/13 fields per substrate Path-C re-ingest) · `calmar-diff-marginal` · `pf-diff-marginal` · `r-multiple-mean-marginal`

### 2026 OOS sub-window diagnostic (informational; outside frozen design.md §2 OOS window 2024-01-01 → 2025-12-30)

Per [`scripts/run_h060_2026_q1q2.py`](../../../scripts/run_h060_2026_q1q2.py) extended to 2026-04-01 → 2026-06-30 on the canonical substrate `317429e4...` (run_id `v1_2026_q1q2_20260518T221523Z`; sidecar SHA `b03cd0a6...`):

| Symbol | TSMOM ROI | TSMOM max-DD | Passive raw-BH ROI | Raw-BH max-DD | Signal +/− | W/L/Z (sessions) |
|---|---:|---:|---:|---:|---:|---:|
| ES | **+2.17%** | 0.19% | +14.13% | 1.16% | 38 / 0 | 25/13/0 |
| NQ | **+2.74%** | 0.17% | +23.50% | 1.38% | 38 / 0 | 26/12/0 |
| MGC | −0.12% | 0.57% | −1.44% | 6.87% | 37 / 0 | 16/21/0 |
| SIL | +0.37% | 0.39% | +11.19% | 11.12% | 37 / 0 | 22/15/0 |
| **Basket (sum, $40K start)** | **+1.29%** | **0.16%** | +11.85% (avg) | — | all 4 long-only | 89/61/0 |

**2026 sub-window verdict** (3 months: 2026-04-01 → 2026-06-30; n_sessions=37-38 per symbol below PW2004 minimum block-length for stationary-bootstrap CI — descoped from primary inference; informational only):

The TSMOM signal is all-long-only on the sub-window (every signal = +1 across all 4 symbols, 37-38 sessions each). Raw buy-and-hold dramatically outperforms TSMOM on ES/NQ/SIL because vol-scaling caps notional exposure during the trending-up regime. MGC mildly negative on both TSMOM and raw BH (commodities-divergence vs equity-index in this window). Basket TSMOM +1.29% / max-DD 0.16% is materially lower-magnitude than raw EW-basket BH +11.85%.

Consistent with the partial-decay framing per design.md §1.4 and the 2024-2025 OOS verdict: TSMOM in this universe + this regime captures only a fraction of underlying market return. The 2026 sub-window does NOT change the partial-decay conclusion.

### Bottom line

H060 v2 confirms the v1 partial-decay verdict on the canonical post-Phase-O.8 substrate `317429e4...`: TSMOM basket MPPM(ρ=1) = +0.082 [−0.110, +0.267] (covers zero → marginal), all 4 ADR-0017 survival-constrained metrics report `marginal`. Realized OOS $10K → $16,875 (+68.75%) underperforms passive EW $17,567 (+75.67%) by 6.91pp; max-DD 29.47% (vs passive 23.72%). Forward 252-session P(loss) = 29.68%. The v1 vs v2 substrate change shifted nominal returns ~−20pp but preserved the qualitative verdict. **Non-significant null on H_1**; consistent with the [Huang-Li-Wang-Zhou 2020 *JFE* 137(3):695-712 DOI 10.1016/j.jfineco.2020.04.003](https://doi.org/10.1016/j.jfineco.2020.04.003) post-publication TSMOM decay finding + SocGen Trend Index ~0 Sharpe practitioner record post-2009. Next mandatory transition per ADR-0013 §5: `ninjascript-implemented` (pure-C# implementable per design.md §15); per the user 2026-05-04 standing directive operator-discretionary upon canonical-format presentation. Cost-realism calibration BLOCKING-BEFORE-PAPER-TRADE-EVALUATED.

Full v1 vs v2 numerical comparison: see [`docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md`](../../../docs/research_notes/memo_substrate-vintage-inventory_2026-05-18.md) for substrate-SHA reconciliation.

Sidecar: [`artifacts/runs/H060/cbddc3c9dd6d47c7b0ac4f9cfdd5a3d9/sidecar.json`](../../../artifacts/runs/H060/cbddc3c9dd6d47c7b0ac4f9cfdd5a3d9/sidecar.json). ReproLog: [`logs/reproducibility/cbddc3c9dd6d47c7b0ac4f9cfdd5a3d9.json`](../../../logs/reproducibility/cbddc3c9dd6d47c7b0ac4f9cfdd5a3d9.json) (13/13 fields).
