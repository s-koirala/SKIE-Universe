---
investigation_id: INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM
schema_version: investigation_memo_v1
created: 2026-05-19
status: complete-no-further-action
hypothesis_of_investigation: H050
parent_kpi_report_card: research/01_hypothesis_register/H050/H050_kpi_report_v1.md
---

# Investigation Memo — H050 HMM-gating actively HARMS the directional signal: per-state decomposition identifies whipsaw + Sharpe-anti-selection as load-bearing

Per [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) §D-1, this memo is the canonical artifact class for `INVESTIGATE-FAILURE-MODE-*` follow-ups. Investigation outputs do NOT use the [ADR-0014](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) §3.2 13-table format; this template is the alternative artifact class. Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1 non-loss, this memo is immutable post-completion; corrections produce a versioned successor (e.g., `investigation_memo_h050-hmm-gating-harm_v2.md`).

## 1. Hypothesis-of-investigation

H050 KPI report card v1 ([research/01_hypothesis_register/H050/H050_kpi_report_v1.md](H050_kpi_report_v1.md), Phase G clean-completion run_id `31d23ecd8e3842dd8ebd5687ce9c91d5`) reports `T_H050 = SR_gated − SR_uncond < 0` on BOTH symbols with LW2008 differential CI excluding zero on the negative side: ES −0.0371 [−0.041, −0.034]; NQ −0.0219 [−0.025, −0.019]. H_1 (HMM regime-gating IMPROVES the directional signal Sharpe vs unconditional) is decisively rejected. Realized $10K equity is catastrophic on both gated arms (ES −81.0%, NQ −84.2%); the 252-session forward bootstrap projects P(loss) = 100% on both. The HMM regime-gating LAYER is the load-bearing failure mechanism (the underlying directional signal is independently a Sharpe-near-zero quasi-null and CANNOT be improved by a gate that subtracts cost without subtracting risk).

This investigation decomposes WHY gating harms the signal into four discriminable sub-hypotheses:

- **H-a — Random gating**: HMM states are uncorrelated with future returns; gating filters trades randomly, reducing sample size without changing Sharpe.
- **H-b — Anti-selection**: HMM states are NEGATIVELY-correlated with future returns; gating filters OUT the best-Sharpe bars and keeps the worst-Sharpe bars.
- **H-c — Whipsaw**: HMM gating creates regime-switching at the per-bar noise scale; state transitions force position changes at unfavourable prices and amortise cost across very small per-bar P/L.
- **H-d — Distribution shift**: HMM is fit on training-set regime distribution; production OOS regime distribution differs sufficiently that gating decisions are calibrated for a regime that does not manifest.

## 2. Decomposition plan

Per-state empirical decomposition on the existing v1 fixture (no new walk-forward execution required; reads existing OOS returns + HMM cache pickle). Five computations per symbol on the binding canonical artifact tuple:

1. **Per-state realized OOS mean + std + Sharpe** on the unconditional return series (counterfactual: what would the directional signal earn at the same bars where the gate fires vs the gate is OFF). Tests H-a (random would imply per-state stats indistinguishable) + H-b (anti-selection would imply gate-state has worse mean / Sharpe than full).

2. **Per-state vol asymmetry** from the HMM emission parameters (cached `hmm_params.covars`). Tests H-a (random gating incompatible with systematic vol-state asymmetry).

3. **State-transition rate + run-length distribution** on the binary state vector `gated_return != 0`. Tests H-c (high transition rate + short active runs imply forced position flips at the per-bar scale).

4. **Cost-drag attribution**: `gated_return - unconditional_return * regime_indicator` isolates the per-bar cost of position flips. Anchors the H-c magnitude.

5. **HMM train-implied stationary distribution vs OOS realized P(state=1)** via the cached `log_transmat`. Tests H-d (distribution shift would imply OOS frequency materially diverges from stationary distribution).

Substrate binding (parent KPI report card v1): `b3ee230aa12ec1826fb8283a4469fc85a5ab792f396fdfccd0eacd51b3168e1d`. Run_id: `31d23ecd8e3842dd8ebd5687ce9c91d5`. Implementation: [scripts/investigate_h050_hmm_gating_harm.py](../../../scripts/investigate_h050_hmm_gating_harm.py); sidecar at [artifacts/runs/H050/investigations/hmm_gating_harm/sidecar.json](../../../artifacts/runs/H050/investigations/hmm_gating_harm/sidecar.json).

## 3. Termination criterion

Per ADR-0027 §D-1(c)(i): **close when the per-state decomposition completes + the §7 implication identifies the load-bearing sub-hypothesis (or combination)**. No additional empirical decomposition required; any follow-on amendment (e.g., HMM-gating-inversion, stable-state confirmation, cadence migration) lands in a separate cycle per ADR-0027 §D-3 empirical-before-amendment.

## 4. Wall-clock soft cap

| Estimate | Actual | Delta | Justify (if overrun) |
|---|---|---|---|
| 3 hr | ~1 hr | −2 hr | n/a |

## 5. Output artifact spec

- Output class: **investigation-memo**
- Cross-references: [H050 design.md](design.md); [H050 KPI report card v1](H050_kpi_report_v1.md); [ADR-0005 HMM toolkit](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md); [ADR-0013 §4.1 non-loss](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md); [ADR-0027 §D-1 + §D-3](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md); audit trail [docs/audits/audit_trail_2026-05-19_h050-hmm-gating-harm-investigate.md](../../../docs/audits/audit_trail_2026-05-19_h050-hmm-gating-harm-investigate.md).

## 6. Findings

### 6.1 Per-state realized OOS statistics (load-bearing table)

Annualisation basis: RTH bars × √(252 × 390) = √98,280. All Sharpes are bar-level then annualised; numbers below match the [KPI report card v1](H050_kpi_report_v1.md) full-path Sharpes within rounding tolerance.

| Symbol | Subset | n_bars | μ (per-bar) | σ (per-bar) | SR_bar | SR_ann | μ − μ_full |
|---|---|---:|---:|---:|---:|---:|---:|
| ES | Full unconditional | 337,837 | −1.700e−6 | 2.023e−4 | −0.00840 | −2.634 | (reference) |
| ES | Full gated | 337,837 | −4.919e−6 | 1.080e−4 | −0.04554 | **−14.278** | −3.219e−6 |
| ES | Uncond. in state 1 (active; n=241,857) | 241,857 | −2.441e−6 | 1.664e−4 | −0.01467 | −4.601 | **−7.412e−7 < 0** |
| ES | Uncond. in state 0 (inactive; n=95,980) | 95,980 | +1.675e−7 | 2.727e−4 | +0.00061 | **+0.193** | +1.870e−6 |
| NQ | Full unconditional | 673,274 | −4.392e−7 | 3.486e−4 | −0.00126 | −0.395 | (reference) |
| NQ | Full gated | 673,274 | −2.740e−6 | 1.186e−4 | −0.02311 | **−7.245** | −2.301e−6 |
| NQ | Uncond. in state 1 (active; n=512,890) | 512,890 | −3.343e−7 | 2.004e−4 | −0.00167 | −0.523 | +1.049e−7 |
| NQ | Uncond. in state 0 (inactive; n=160,384) | 160,384 | −7.745e−7 | 6.178e−4 | −0.00125 | −0.393 | −3.353e−7 |

### 6.2 Per-state vol asymmetry

| Symbol | σ_state0 (high-vol) | σ_state1 (low-vol) | Ratio (state0/state1) |
|---|---:|---:|---:|
| ES | 2.727e−4 | 1.664e−4 | **1.64×** |
| NQ | 6.178e−4 | 2.004e−4 | **3.08×** |

HMM emission means are statistically indistinguishable from zero on both states (ES state 0 emission mean = −3.4e−6, state 1 = +1.5e−6; NQ similar magnitude). The HMM is **canonically a vol-regime detector**, NOT a directional-drift detector — emission-mean rank is essentially noise at this scale and is used as the gate-state label only because design.md §5 line 63 specifies the canonical state ordering by emission-mean.

### 6.3 State-transition rate + run-length distribution

| Symbol | n_transitions | transition rate | Mean active-run | Median active-run | Mean inactive-run | Persistence P(1→1) | Persistence P(0→0) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ES | 102,472 | **30.33%** | 4.7 bars | 3 | 1.9 bars | 0.788 | 0.466 |
| NQ | 79,237 | **11.77%** | 12.9 bars | 7 | 4.0 bars | 0.923 | 0.753 |

ES experiences 102,472 forced position transitions over a 337,837-bar OOS fold (one transition every 3.3 bars on average). Median active-run length = 3 bars (~3 minutes); the gate fires for very short intervals before flipping off again.

### 6.4 Cost-drag attribution

| Symbol | Mean cost-drag per bar | Full-path uncond mean (reference) | Cost-drag / |uncond mean| |
|---|---:|---:|---:|
| ES | −3.171e−6 | −1.700e−6 | **1.87×** (cost burden exceeds the entire gross signal magnitude) |
| NQ | −2.485e−6 | −4.392e−7 | **5.66×** |

Cost-drag (`gated_return − unconditional_return × regime_indicator`) measures the per-bar P/L impact of the gate-induced position flips. The cost magnitude exceeds the unconditional signal magnitude on both symbols by 1.9× to 5.7× — **cost drag from whipsaw alone fully explains the gated-arm catastrophe**.

### 6.5 HMM train vs OOS distribution shift

| Symbol | Train stationary P(s=1) | OOS realized P(s=1) | Shift | Relative |
|---|---:|---:|---:|---:|
| ES | 0.7486 | 0.7159 | −0.0327 | −4.4% |
| NQ | 0.7016 | 0.7618 | +0.0602 | +8.6% |

Distribution shift is small in absolute and relative magnitude. NQ has the larger shift (+8.6%) but in the direction that should *help* the gate (more bars in the supposedly favourable state), yet NQ still produces catastrophic Sharpe degradation. Distribution shift is NOT the load-bearing mechanism.

### 6.6 Synthesis

The four sub-hypotheses receive the following empirical verdicts:

| Sub-hypothesis | Verdict | Load-bearing? |
|---|---|---|
| **H-a Random gating** | REFUTED | No (vol asymmetry empirically real; HMM is detecting a real vol-regime signal) |
| **H-b Anti-selection** | PARTIALLY SUPPORTED | Secondary (ES anti-selective on mean dimension; BOTH symbols anti-selective on per-bar Sharpe dimension — gate state has WORSE conditional Sharpe than the non-gate state on both ES and NQ) |
| **H-c Whipsaw** | STRONGLY SUPPORTED | **PRIMARY** (cost drag exceeds full signal magnitude by 1.9×−5.7×; 30% transition rate on ES) |
| **H-d Distribution shift** | WEAK | No (4-9% shifts; small and in the direction that should not produce catastrophic degradation) |

**The HMM gating LAYER fails via TWO mechanisms operating compounded**:

1. **H-c Whipsaw (primary)**: the HMM 2-state vol-regime detector operates at the 1-min noise scale. With median active-run length = 3 bars (ES), the gate fires for very short intervals before flipping off. Each off-to-on AND on-to-off transition pays the per-side cost from the directional model's position flip. With 102,472 transitions on ES, the cost-drag accumulates to −3.17e−6 per bar — nearly 2× the full-path unconditional signal magnitude. **Cost from forced position flips ALONE exceeds whatever signal the directional model carries.**

2. **H-b Anti-selection on Sharpe dimension (secondary)**: even ignoring cost drag, the HMM gate's "high-mean / low-vol" state systematically has WORSE per-bar Sharpe than the discarded "low-mean / high-vol" state. ES SR_state1_uncond = −0.0147 vs SR_state0_uncond = +0.00061 — the gate would FILTER OUT the only Sharpe-positive state and keep the Sharpe-negative state, even at zero cost. NQ shows the same pattern but at smaller magnitude. The directional model's signal-to-noise improves in the HIGH-vol regime (where positions are scaled by larger price moves), but the HMM rejects exactly those bars.

The compounded failure is **structural**: the HMM canonical state-labelling rule (sort by emission mean) selects the LOW-VOL state as the gate, but on intraday equity-index futures the LOW-VOL state has small per-bar Sharpe per directional position. Combine that anti-selection with the cost paid on every state transition (~30% of bars for ES, ~12% for NQ) and the gated arm bleeds capital systematically.

## 7. Implication

### 7.1 For the parent hypothesis (H050)

H050 stage UNCHANGED: `kpi-report-emitted` per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) (no archive state). The hypothesis is preserved verbatim. design.md §1-§7 immutable per [ADR-0013 §"Frozen pre-registration amendment"](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). H050 design.md §17 revision-log MAY cross-reference this investigation (operator-discretionary; tracked under new follow-up `P1-H050-DESIGN-MD-CROSS-REFERENCE-INVESTIGATION`).

### 7.2 For project-level ADRs

NO ADR amendment lands as part of this investigation per [ADR-0027 §D-3 empirical-before-amendment sequencing](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md). This investigation is the EMPIRICAL DECOMPOSITION; any amendments to ADR-0005 (HMM toolkit), ADR-0013 (no-archive), or ADR-0025 (abandonment-trigger primitives) operate from this empirical anchor in a separate cycle. Two candidate amendments empirically motivated here (deferred per §D-3):

1. **ADR-0005 amendment proposal**: canonical state-ordering rule (design.md §5 line 63 — "sort states by emission-mean ascending; gate = highest-mean") generates a gate that is anti-selective on per-bar Sharpe in BOTH ES and NQ. Empirical evidence supports amendment to sort by EMISSION SHARPE (μ/σ ratio) rather than μ alone. Tracked under `P1-ADR-0005-CANONICAL-STATE-ORDERING-SHARPE-VS-MEAN` (non-blocking; deferred).

2. **ADR-0025 amendment proposal**: the kill-switch + equity-rebase + cost-model primitives operate ON TOP of a working directional signal. The Phase G H050 v1 catastrophe demonstrates that gating LAYERS (HMM + others in the same family) can DEGRADE a signal by paying cost without subtracting risk. Recommend a new `gating-friction-dominated-edge-{present, absent, n/a}` annotation parallel to [ADR-0028 §D-2 `cost-friction-dominated-edge`](../../../docs/decisions/ADR-0028-k6-k7-size-down-cost-friction-edge.md). Tracked under `P1-ADR-0025-GATING-FRICTION-EDGE-ANNOTATION` (non-blocking; deferred).

### 7.3 For future hypotheses + operator-actionable next-step variants

Two operator-actionable HMM-variant successor designs are now empirically motivated (per ADR-0027 §D-4 genetic-successor discipline):

**Variant A: `H050.invert` — invert gating logic + add explicit stable-state-confirmation**:

- Invert design.md §5 line 63 canonical state ordering: gate state = LOWEST-mean state (which from §6.1 has BETTER per-bar Sharpe on both ES and NQ on the unconditional signal).
- ADD a state-stability-confirmation period: gate fires only after N consecutive bars in the chosen state (N candidate grid {5, 10, 20} bars). Addresses H-c (whipsaw) by reducing the transition rate from ~30% (ES) to potentially ~1-3% at N=20.
- Tracked under new follow-up `P1-H050-INVERT-VARIANT-SUCCESSOR-PRE-REG` (BLOCKING-BEFORE-NEXT-H050-SUCCESSOR-LAUNCH).

**Variant B: `H050.stable-state` — preserve gate-state logic but add stability-confirmation**:

- Keep design.md §5 line 63 canonical ordering (gate = high-mean state).
- ADD same state-stability-confirmation gate as Variant A (N candidate grid {5, 10, 20}).
- Tests whether the whipsaw mechanism (H-c) is the primary driver — if so, stable-state-confirmation should restore positive edge even with the same (anti-selective) gate-state choice.
- Tracked under new follow-up `P1-H050-STABLE-STATE-VARIANT-SUCCESSOR-PRE-REG` (non-blocking; sequencing after Variant A per ADR-0027 §D-5 soft time-budget).

**Variant C: Cadence migration to 5-min or 15-min**:

- The 1-min cadence is structurally hostile to HMM gating because (a) costs amortize over very small per-bar P/L and (b) HMM state transitions occur at the 1-min noise scale. Re-running H050 at 5-min cadence reduces the transition rate by ~5× and concentrates per-bar P/L by ~5×, both improving the cost-to-signal ratio by ~25×.
- Tracked under new follow-up `P1-H050-CADENCE-5MIN-VARIANT-SUCCESSOR-PRE-REG` (non-blocking).

**Variant D: Multi-state HMM (n_states ≥ 3)**:

- Two-state HMM collapses the directional signal into a single binary vol-regime indicator. A 3-state or 4-state HMM might separate the within-vol-regime directional signal more cleanly + admit more nuanced gating policies (e.g., position-scale by state membership rather than binary gate).
- Tracked under new follow-up `P1-H050-MULTI-STATE-HMM-VARIANT-SUCCESSOR-PRE-REG` (non-blocking).

### 7.4 Constraints for any future HMM-gated hypothesis

- HMM-gated hypotheses MUST emit `gating-friction-magnitude` annotation reporting per-bar cost-drag attribution (per the Phase O.15 H062 v3 ablation pattern).
- Design.md §1.5 (or equivalent expected-payoff block) SHALL acknowledge the cost-amortization × transition-rate interaction: per-bar P/L magnitude × inverse-transition-rate must exceed per-side cost magnitude by a substantial margin (operator-pinned to ≥ 3× as the conservative-prior threshold; calibration tracked under `P1-HMM-GATING-COST-SIGNAL-RATIO-EMPIRICAL`).
- design.md §11.1 SHALL declare the HMM canonical state-ordering rule explicitly (mean-ascending vs Sharpe-ascending vs custom) and provide a `# justify:` annotation for the choice.

## 8. Closure

- **Closure date**: 2026-05-19
- **Closure type**: ablation-complete (per ADR-0027 §D-1(c)(i))
- **Closure verdict**: complete-no-further-action (the empirical decomposition completed; no successor pre-registration lands in this investigation cycle per ADR-0027 §D-3 empirical-before-amendment; downstream ADR amendments + successor pre-registrations lands in separate cycles tracked under the §7 follow-ups)
- **Downstream artifacts produced**:
  - [scripts/investigate_h050_hmm_gating_harm.py](../../../scripts/investigate_h050_hmm_gating_harm.py) — decomposition script (~300 lines).
  - [artifacts/runs/H050/investigations/hmm_gating_harm/sidecar.json](../../../artifacts/runs/H050/investigations/hmm_gating_harm/sidecar.json) — investigation sidecar (scientific_payload_sha256 `1ebf175b49625b3c485e17eb5495906fc304ab0cc3c5000a866f0ad0f08e63d5`).
  - [docs/audits/audit_trail_2026-05-19_h050-hmm-gating-harm-investigate.md](../../../docs/audits/audit_trail_2026-05-19_h050-hmm-gating-harm-investigate.md) — R1 audit trail.

## Cross-references

- Parent KPI report card: [H050_kpi_report_v1.md](H050_kpi_report_v1.md) (KPI v1 emission 2026-05-04; binding T_H050 < 0 with LW2008 CI excluding zero negatively).
- Stage tracker: [stage.md](stage.md).
- Failure log: [failure_log.md](failure_log.md).
- ADR-0005 (HMM toolkit; canonical state-ordering rule at §5 line 63): [docs/decisions/ADR-0005-hmm-regime-toolkit.md](../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md).
- ADR-0027 §D-1 (this template's source mandate) + §D-3 (empirical-before-amendment): [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md).
- ADR-0013 §4.1 non-loss: [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md).
- Audit-remediate-loop trail: [docs/audits/audit_trail_2026-05-19_h050-hmm-gating-harm-investigate.md](../../../docs/audits/audit_trail_2026-05-19_h050-hmm-gating-harm-investigate.md).

## Append discipline

- Sections 1-5 are frozen at investigation start; they MAY be edited only via versioned-successor pattern per ADR-0013 §4.1.
- Sections 6-8 are append-as-work-completes; rows in the §6.1 / §6.2 / §6.3 / §6.4 / §6.5 tables are immutable once landed.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
