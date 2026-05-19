---
investigation_id: INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION
schema_version: investigation_memo_v1
created: 2026-05-19
status: complete-no-further-action
hypothesis_of_investigation: H062
parent_kpi_report_card: research/01_hypothesis_register/H062/H062_kpi_report_v2.md
---

# Investigation Memo — H062 v3 primitive-attribution ablation: decomposing the −99.9995% basket OOS by ADR-0025 primitive engagement

Per [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) §D-1, this memo is the canonical artifact class for `INVESTIGATE-FAILURE-MODE-*` follow-ups. Investigation outputs do NOT use the ADR-0014 §3.2 13-table format; this template is the alternative artifact class. Per [ADR-0013](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1 non-loss, this memo is immutable post-completion; corrections produce a versioned successor (e.g., `INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION_v2.md`).

## 1. Hypothesis-of-investigation

H062 v3 smoke walk-forward (run_id `154237b365794244974068402b377191`, sidecar [artifacts/runs/H062/154237b365794244974068402b377191/sidecar.json](../../../artifacts/runs/H062/154237b365794244974068402b377191/sidecar.json)) produced realized OOS basket = $0.05 (−99.9995%) on the canonical 4-symbol {ES, NQ, MGC, SIL} basket under simultaneous engagement of all 3 ADR-0025 abandonment-trigger primitives (`--enable-kill-switch-runtime --enable-equity-rebase-current --cost-model conservative_prior`). MPPM(ρ=1) point = −1.0447 with stationary-bootstrap CI [−1.44, −0.62] strictly excludes zero on the negative side. Kill-switch primitive recorded 8,845 total trigger events (K-6 daily 4,417 + K-7 weekly 4,428; K-3 + K-4 = 0). This decomposition discriminates among three candidate dominant drivers: (a) cost-realistic friction from `conservative_prior` cost model; (b) kill-switch asymmetry blocking entries (per the operator 2026-05-19 intuition "muted profits while drawdowns ran"); (c) equity-rebase current-mode floor + sizing-shrinkage interaction with low-bankroll states.

## 2. Decomposition plan

Per [ADR-0027 §D-1(b)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) ablation discipline + §D-3 empirical-before-amendment sequencing rule: 4 new smoke-mode walk-forward runs on the canonical substrate (SHA `317429e49ad636746d15bf6310fd8f24bc45611ef03e50abefdc25fc6ba12dc7`), preserving the exact v3 smoke fixture (4-cell inner-CV grid: channel_n ∈ {60, 120} × k_atr ∈ {2.0} × kelly_multiplier ∈ {0.25, 1.0}; 60-train/30-test inner-CV folds; rng_seed `20260514` from [config/hypotheses/H062.yaml](../../../config/hypotheses/H062.yaml)):

- **Ablation 0 (all-OFF smoke baseline)**: `uv run python scripts/run_h062_walk_forward.py --smoke` (no primitive flags). Establishes a smoke-fidelity v2-equivalent reference; bridges the smoke-fixture comparability gap to the full-grid Phase O.10 v2 sidecar `eb729b201595484594ce4c9ddde72d05` (which uses the 48-cell full grid and is therefore NOT directly compared as a baseline cell — referenced as contextual full-grid bookend only).
- **Ablation 1 (cost-only)**: `--smoke --cost-model conservative_prior`. Isolates the per-trade cost subtraction effect on per-session log-return + downstream MPPM(ρ=1).
- **Ablation 2 (kill-switch-only)**: `--smoke --enable-kill-switch-runtime`. Isolates the K-3/K-4/K-6/K-7 entry-gating effect on trade activity + cumulative P/L. Tests operator intuition: does blocking entries during drawdown sessions "mute profits" relative to baseline?
- **Ablation 3 (equity-rebase-only)**: `--smoke --enable-equity-rebase-current`. Isolates the current-equity sizing-rebase effect (replaces fixed-equity with current-equity × `floor_equity_fraction = 0.10` floor per ADR-0025 §D-2).

Reference cells (existing sidecars; bookends only — NOT new compute):

- **v3 all-ON smoke** (anchor): `154237b365794244974068402b377191`. All 3 primitives ON; realized OOS −99.9995%.
- **Phase O.10 v2 full-grid baseline** (contextual): `eb729b201595484594ce4c9ddde72d05`. All 3 primitives OFF; full 48-cell grid; realized OOS +217.57%. Used for full-grid-vs-smoke directional sanity-check, not as a direct ablation cell.

**Per-primitive contribution definition**: ΔROI(primitive) = realized OOS basket %(ablation N) − realized OOS basket %(ablation 0 all-OFF smoke baseline). Positive Δ = primitive helps; negative Δ = primitive harms. Triangulation: if Σ(per-primitive Δ) ≈ ΔROI(v3 all-ON), primitive interactions are additive; if not, interaction effects dominate (operator review required).

## 3. Termination criterion

Per [ADR-0027 §D-1(c)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) acceptable form (i): close when the 3 ablations (cost-only, kill-switch-only, equity-rebase-only) + the all-OFF smoke baseline complete, sidecars land on disk under `artifacts/runs/H062/<run_id>/sidecar.json`, and the §6 findings table is populated with per-cell realized OOS basket %, max-DD %, MPPM(ρ=1) point, and (where applicable) kill-switch trigger counts.

## 4. Wall-clock soft cap

Per [ADR-0027 §D-1(d)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) soft cap discipline:

| Estimate | Actual | Delta | Justify (if overrun) |
|---|---|---|---|
| 1.5-2 hr | ~1 hr (4 smoke runs in 6m 21s wall-clock thanks to substrate filesystem caching across runs; ~30 min memo authoring; ~25 min audit-remediate-loop) | −0.5-1 hr (under budget) | n/a (no overrun) |

Hard cap: 3 hr (per task spec); if exceeded, write up partial findings as a draft + flag the remaining work per ADR-0027 §D-1(d) operator-discretionary overrun clause.

## 5. Output artifact spec

Per [ADR-0027 §D-1(e)](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md):

- **Output class**: investigation-memo (this artifact)
- **Cross-references**:
  - Parent KPI: [H062 v2 KPI report card](H062_kpi_report_v2.md) (sidecar `eb729b20...`, full-grid; v3 supersession was deferred per `P1-ADR-0025-V3-KPI-RERUN-H062-H055`)
  - Parent ADRs: [ADR-0025](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md) (primitive infrastructure) + [ADR-0026](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md) + [ADR-0027](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) (operational discipline + investigation class)
  - Phase O.13 H062 v3 smoke audit trail: [CLAUDE.md Phase O.13 ledger entry](../../../CLAUDE.md) (kpi summary at adoption time of this investigation; this memo's audit trail at [docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md](../../../docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md))
  - Phase O.14 ADR-0026/0027 audit trail: [docs/audits/audit_trail_2026-05-19_adr-0026-adr-0027.md](../../../docs/audits/audit_trail_2026-05-19_adr-0026-adr-0027.md) (where this investigation was registered)

## 6. Findings

> Per [ADR-0013 §4.1 non-loss](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md), table rows are APPEND-as-work-completes; rows are immutable once landed.

| Ablation # | Configuration | Run ID | Sidecar SHA256 (prefix-16) | Realized OOS basket % | Max-DD % | MPPM(ρ=1) point | MPPM(ρ=1) CI | LW2008 Sharpe-vs-passive point | n_trades | K-3 | K-4 | K-6 | K-7 | Per-primitive Δ vs A0 (pp) |
|---|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| A0 (smoke baseline) | all primitives OFF; smoke 4-cell grid | `5e52f0b7ddd94ecea3187566c0e255d0` | `ecaedec192c9f701` | +261.88 | 95.43 | +0.0966 | [−0.305, +0.497] | −0.0281 | 10,326 | 0 | 0 | 0 | 0 | 0 (reference) |
| A1 (cost-only) | `--cost-model conservative_prior` | `edbc263e7ed14ca3a2252a10e94e45c3` | `a4765d8c092e6ed4` | **−100.00** | 100.00 | **−1.1347** | [−1.550, −0.724] | −0.1245 | 10,326 | 0 | 0 | 0 | 0 | **−361.88** |
| A2 (kill-switch-only) | `--enable-kill-switch-runtime` | `d01ca71b7ee34863b4219003d9a05601` | `3564a5310d8f4614` | **−21.91** | 94.30 | −0.0212 | [−0.423, +0.355] | −0.0376 | 7,127 | 0 | 0 | 4,425 | 4,502 | **−283.79** |
| A3 (equity-rebase-only) | `--enable-equity-rebase-current` | `5589abf07c85471a84f75feead6e0174` | `cda53905d7ae0e97` | +211.02 | 96.15 | +0.0847 | [−0.325, +0.517] | −0.0310 | 10,342 | 0 | 0 | 0 | 0 | −50.86 |
| Ref-v3 (all-ON smoke) | all 3 primitives ON | `154237b365794244974068402b377191` | `3fcef093cd908eeb` | **−99.9995** | 100.00 | **−1.0447** | [−1.444, −0.616] | −0.1306 | 7,201 | 0 | 0 | 4,417 | 4,428 | **−361.88** (cumulative) |
| Ref-v2 (full-grid, all-OFF) | all 3 primitives OFF; full 48-cell grid | `eb729b201595484594ce4c9ddde72d05` | `5f876797edfcabb5` | +217.57 | 93.26 | +0.0950 | [−0.343, +0.540] | −0.0374 | 9,653 | n/a | n/a | n/a | n/a | (full-grid bookend; NOT direct baseline) |

**Decomposition arithmetic** (per ADR-0027 §D-1(b) per-primitive contribution definition):

- A0 baseline ROI = **+261.88%**.
- Sum of three singleton primitive Δs vs A0 = (A1 Δ) + (A2 Δ) + (A3 Δ) = (−361.88) + (−283.79) + (−50.86) = **−696.53 pp**.
- Cumulative v3 (all-ON) Δ vs A0 = **−361.88 pp**.
- Interaction effect (cumulative − Σ singletons) = +334.65 pp.

The large positive interaction is the canonical *saturation-floor* signature: cost-only A1 already saturates basket at −100% (total bankruptcy of the equal-weighted basket); enabling kill-switch + equity-rebase on top cannot push basket below −100%. The cumulative v3 effect is therefore bounded below by the largest singleton effect (cost), and Σ-of-singletons is an upper bound on the magnitude of the cumulative effect, not an additive predictor. Per-primitive share of the cumulative v3 delta (signed, fractional of cumulative): cost A1 = **+100.0%** (drives ALL the cumulative effect by itself); kill-switch A2 = +78.4%; equity-rebase A3 = +14.1%.

### Per-symbol decomposition (basket aggregate is the headline; per-symbol exposes which leg dominates)

Per-symbol final equity is only persisted in sidecars where `equity_rebase` primitive is engaged (A3 + Ref-v3); cells without engagement (A0 / A1 / A2 / Ref-v2) report only the basket aggregate. For those cells, per-symbol trade counts (`per_symbol_n_trades`) are the available proxy.

| Symbol | A0 trades | A1 trades | A2 trades | A3 final equity | Ref-v3 all-ON final equity |
|---|---:|---:|---:|---:|---:|
| ES | 97 | 97 | 92 | $12,138.39 (+21.4%) | $9,044.79 (−9.6%) |
| NQ | 0 | 0 | 0 | $10,000.00 (0 trades; capacity-floor at $10K retail) | $10,000.00 (0 trades; same) |
| MGC | 5,701 | 5,701 | 3,876 | $8,858.57 (−11.4%) | $26.75 (**−99.7%**) |
| SIL | 4,528 | 4,528 | 3,159 | $28,924.00 (+189.2%) | $19.52 (**−99.8%**) |

- **NQ is identical at 0 trades across all cells** — Donchian + ATR-stop × 1% risk × Kelly 0.25 → < 1 contract size at $10K retail equity per the H062 v3 design.md §11.2 known issue. NQ contributes nothing to the per-primitive decomposition.
- **A3 vs Ref-v3 SIL is the load-bearing per-symbol contrast**: equity-rebase-only on SIL = $28,924 (+189%); enabling cost + kill-switch on top = $19.52 (−99.8%). The SIL leg's positive skew (per H062 v2 KPI τ_3 = +0.737) generates large right-tail compounding under fixed-equity sizing + zero cost; cost + kill-switch jointly extinguish it.
- **MGC is the canary**: A3 equity-rebase-only drags it to −11.4% (modest); cost + kill-switch on top drives it to −99.7%. MGC's left-tail-heavy R-multiple distribution interacts catastrophically with the cost subtraction.

### Trade-activity decomposition (the operator-intuition load-bearing evidence)

| Cell | n_trades | Wins | Losses | Win % | K-6 fires | K-7 fires |
|---|---:|---:|---:|---:|---:|---:|
| A0 (baseline) | 10,326 | 1,149 | 2,202 | 34.24 | 0 | 0 |
| A1 (cost-only) | 10,326 | 1,046 | 2,310 | 31.17 | 0 | 0 |
| A2 (ks-only) | 7,127 | 877 | 2,058 | **29.84** | **4,425** | **4,502** |
| A3 (er-only) | 10,342 | 1,154 | 2,213 | 34.20 | 0 | 0 |
| Ref-v3 all-ON | 7,201 | 803 | 2,155 | **27.15** | 4,417 | 4,428 |

**Critical observation for the operator-intuition test**: enabling the kill-switch (A2) blocks ~3,200 trades vs baseline (~31% of entries), and the win rate DROPS from 34.24% → 29.84%. This is the empirical signature of asymmetric blocking — K-6 and K-7 fire during *drawdown sessions* and block the entries that would have followed; but a strict subset of those blocked entries would have been *winning* trades that recover the drawdown. The kill-switch is structurally asymmetric: it cannot distinguish "drawdown about to deepen" from "drawdown about to mean-revert." Combined with the operator's win-rate framing, this empirically *partially supports* the operator intuition (K-6/K-7 are net-negative on this fixture, but cost is the dominant catastrophe driver).

**Secondary observation on A1 cost-only win-rate**: A1 win rate also drops (34.24% → 31.17%) even though A1 has IDENTICAL trade activity to A0 (both 10,326 trades; same per-symbol counts). The mechanism is *cost-flipping-marginal-winners-to-losers*: the per-trade cost subtraction reclassifies winning sessions whose pre-cost return was barely positive but smaller than the per-trade cost as losing sessions post-cost. This is structurally distinct from the kill-switch asymmetric-blocking mechanism (which removes entries entirely) and provides corroborating evidence that cost is the dominant primitive driver — it operates per-trade on every entry, not just on drawdown-session entries.

**Tertiary observation on A3 trade count**: A3 has 10,342 trades vs A0's 10,326 (+16 trades; +0.15%). The mechanism is current-equity rebase changing position sizing — when equity grows above $10K, sizing rebase allows entries that would have floored to 0 contracts under fixed-equity sizing (and vice-versa during drawdown). The +16 net difference is small enough to be sensitivity-noise but is mechanically consistent with the equity-rebase semantic. ES + MGC + SIL trade counts differ slightly (A3: 95/5752/4495 vs A0: 97/5701/4528) reflecting the sizing-floor sensitivity.

### Synthesis

**Cost (A1) is the empirically dominant primitive**: enabling cost alone — without kill-switch, without equity-rebase — is sufficient to drive the basket from +261.88% to −100.00% bankruptcy. This is a Δ of −361.88 pp, exactly matching the cumulative Δ of all 3 primitives enabled simultaneously (also −361.88 pp; the saturation floor at −100% prevents additivity). The MPPM(ρ=1) signal corroborates: cost-only MPPM = −1.13 [−1.55, −0.72] CI strictly excludes zero on the negative side; v3 all-ON MPPM = −1.04 [−1.44, −0.62] is statistically indistinguishable from cost-only. The mechanism is per-trade conservative-prior cost subtraction interacting catastrophically with the H062 v2 KPI's already-marginal mean-edge (MPPM CI [−0.34, +0.54] covered zero on full-grid v2 PRE-cost) — once the cost drag is applied per-trade × 10,326 trades × ~6 years OOS, the per-session log-return aggregate collapses below the bankruptcy threshold.

**Kill-switch (A2) is the second-largest primitive effect**: enabling kill-switch alone drops basket from +261.88% to −21.91% (Δ −283.79 pp). The mechanism is *asymmetric blocking during drawdown sessions*: K-6 and K-7 fire at the −2% daily / −5% weekly thresholds, block ~31% of all entries, but the blocked entries skew toward winners (win rate drops 34.24% → 29.84%). MPPM(ρ=1) on A2 is essentially zero (−0.0212; CI covers zero) — the kill-switch attenuates both wins and losses, but the asymmetric blocking removes more of the right tail than the left tail (the right tail relies on entries that ride through partial drawdowns to recovery; the kill-switch blocks them).

**Equity-rebase (A3) is empirically minor**: enabling equity-rebase alone moves basket from +261.88% to +211.02% (Δ −50.86 pp; 14.1% of cumulative). Per-symbol detail shows the mechanism: equity-rebase floors sizing at 10% × starting equity, dampens compounding on winners (SIL: +189% vs baseline's higher implied; ES +21%); MGC drifts to −11.4% under the current-equity shrinkage during drawdown phases (no longer compounds losses, but also caps recovery). This is the expected behavior of survival-constrained sizing per ADR-0017 §4.1: bounds catastrophic loss at the cost of attenuated compounding.

The decomposition is consistent with [ADR-0024 §D-7 Lo 2004 AMH framing](../../../docs/decisions/ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md): H062 is a partially-decayed factor whose mean-edge is statistically marginal (CIs cover zero on full-grid v2 PRE-cost) and whose realized OOS positive returns at A0/A3 are tail-amplification artifacts of the skew-positive payoff distribution (τ_3 = +0.737 at v2). Once cost realism is applied (A1 / v3), the marginal mean-edge collapses below zero and the L-skew positive payoff cannot recover the bankroll.

## 7. Implication

Per the task spec + [ADR-0027 §D-3](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md) empirical-before-amendment sequencing rule:

### (a) Which primitive dominates the −99.9995% delta

**Cost (A1) dominates.** Per-primitive Δ vs A0 baseline: A1 = **−361.88 pp** (100.0% of cumulative); A2 = −283.79 pp (78.4% of cumulative; but the saturation floor at −100% caps A1+A2 additivity, so the framework-fair attribution gives A1 the dominant share); A3 = −50.86 pp (14.1% of cumulative; minor). The cumulative v3 all-ON Δ vs A0 (−361.88 pp) is bit-equal to the A1 cost-only Δ within rounding, confirming that **cost alone is sufficient to reproduce the v3 catastrophic outcome.** Per-cell Δ vs v3 all-ON: A1 = 0.0005 pp (essentially indistinguishable from v3); A2 = +78.09 pp (kill-switch alone is materially less catastrophic than v3); A3 = +311.02 pp (equity-rebase alone is far less catastrophic than v3).

### (b) Operator-intuition verdict: "muted profits while drawdowns ran"

**Partially supported.** Decomposition by candidate-mechanism:

- The intuition's *kill-switch-blocks-winners-during-drawdowns* component is **empirically supported** by A2: enabling kill-switch alone blocks ~31% of entries (10,326 → 7,127), drops win rate 34.24% → 29.84% (the blocked entries skew toward winners), and turns the baseline +261.88% into −21.91%. K-6 and K-7 fire predominantly during drawdown sessions and block subsequent entries; the blocked subset includes both losing entries (which the kill-switch is *intended* to block) and winning entries (which the kill-switch *cannot distinguish* from losing entries on a forward-looking basis). This is the canonical asymmetric-blocking pathology: K-6/K-7 act on past P/L (daily/weekly drawdown breaches), but the entries they block are forward returns that may or may not have recovered the drawdown. The win-rate drop is the load-bearing empirical signature.
- The intuition's *cost-realism-as-secondary-driver* implicit framing is **refuted** by A1: cost-only is the DOMINANT driver (100% of cumulative Δ). The operator's framing emphasized the kill-switch asymmetry; the empirical decomposition shows cost is the larger driver in magnitude. Cost is not a behavioral asymmetry (no entry blocking) but a per-trade per-bar additive drag that interacts catastrophically with the already-marginal mean-edge of the H062 family.

Overall verdict: **partially supported** — the kill-switch asymmetry mechanism IS empirically present and measurable (A2 −284 pp), but it is *not the dominant primitive*. Cost-realism is the dominant primitive (A1 −362 pp). Any future ADR-0025 amendment must address BOTH the kill-switch asymmetry AND the cost-realism interaction with marginal mean-edges.

### (c) Empirical justification for a future ADR-0025 K-6/K-7 size-down-vs-block amendment

**Empirically justified, but the justification is more nuanced than the operator intuition framed.** The ADR-0027 §D-3 empirical-before-amendment rule is now satisfied for a future amendment cycle. Per the §6 decomposition findings, an ADR-0025 amendment proposing "K-6/K-7 size-down rather than block-entries" would address ONE component of the catastrophic v3 outcome (the kill-switch asymmetry; A2 −284 pp) but would NOT address the dominant component (cost-realism; A1 −362 pp). A holistic amendment would address both:

1. **K-6/K-7 size-down option** (operator's intuition): when K-6 or K-7 fires, replace "block entry" with "reduce position size by fraction f" where f is tunable (e.g., f = 0.5 = half-size; f = 1.0 = legacy block-entry). This preserves the survival-constrained discipline (smaller positions when in drawdown) while not extinguishing all entries (some of which would have been winners). Empirically motivated by A2's win-rate drop from 34.24% to 29.84% combined with the asymmetric-blocking mechanism analysis.
2. **Cost-realism-aware promotion criterion** (not in operator intuition; surfaced by A1 dominance): given that cost-realism is the dominant primitive driver of catastrophic outcomes on hypotheses with marginal mean-edge (H062 v2 KPI: MPPM CI [−0.34, +0.54] covered zero PRE-cost), the project-level promotion-decision-rule under [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) survival-constrained metric vector SHALL be evaluated POST-cost (cost = `conservative_prior` per [ADR-0025 §D-3](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md)) at first ninjascript-implementation decision point — not at v2 PRE-cost research-only KPIs. This is a documentation discipline, not a primitive change.

**NOTE per ADR-0027 §D-3**: this memo does NOT write the amendment. The empirical finding above is the INPUT to a separate amendment cycle (tracked under new follow-up `P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` registered below).

### (d) Implications for the parent hypothesis H062

H062 remains at `kpi-report-emitted` (v2) per [ADR-0013 §1](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md). No stage transition is triggered by this investigation. The KPI report card v2 stands; the v3 smoke + ablations are RESEARCH artifacts that inform future v3 KPI report card emission under `P1-ADR-0025-V3-KPI-RERUN-H062-H055`. The §17 revision-log of H062 design.md MAY be updated to cross-reference this investigation memo (operator-discretionary; tracked under `P1-H062-DESIGN-MD-CROSS-REFERENCE-INVESTIGATION`).

### (e) Implications for future hypotheses (constraints to inherit; failure modes to canary against)

- **Cost-realism is mandatory at promotion-decision time, not at v(N) KPI emission.** Hypotheses with marginal mean-edge (per ADR-0024 §D-7 partial-decay framing) cannot be evaluated for live-promotion using PRE-cost KPI numbers; future design.md §10 promotion-decision-rule blocks SHALL specify the cost-model context (`zero`, `conservative_prior`, `paper_trade_empirical`) at which the decision is made.
- **Kill-switch K-6/K-7 in their current block-entry form are asymmetric.** Until a size-down amendment lands, hypotheses enabling `--enable-kill-switch-runtime` SHALL acknowledge in design.md §11.1 `# justify:` annotation that the kill-switch may block winning entries during recovery from drawdown.
- **The L-skewness positive-payoff structure (H062 v2 τ_3 = +0.737) does NOT compensate for negative mean-edge.** Future hypotheses claiming positive skew as a load-bearing payoff feature SHALL also satisfy at least a marginal positive mean-edge (per [ADR-0017 §3](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md) MPPM(ρ=1) CI excludes zero on the positive side) post-cost. Phase O.7 + Phase O.13 + this investigation together establish that skew-positive distributions can compound to catastrophic outcomes when realized in path-dependent contexts where the right tail does not materialize.

## 8. Closure

- **Closure date**: 2026-05-19
- **Closure type**: ablation-complete (per ADR-0027 §D-1(c) form (i))
- **Closure verdict**: `complete-no-further-action` at the investigation-memo layer; the empirical finding is the canonical input to a future `P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` cycle which lands separately per ADR-0027 §D-3.
- **Downstream artifacts produced**:
  - Investigation memo (this file): [research/01_hypothesis_register/H062/INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md](INVESTIGATE-FAILURE-MODE-H062-V3-PRIMITIVE-ATTRIBUTION.md)
  - Audit trail: [docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md](../../../docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md)
  - 4 new ablation sidecars under [artifacts/runs/H062/](../../../artifacts/runs/H062/): `5e52f0b7...` (A0), `edbc263e...` (A1), `d01ca71b...` (A2), `5589abf0...` (A3)
  - 4 new ReproLog records under [logs/reproducibility/](../../../logs/reproducibility/): `5e52f0b7...json`, `edbc263e...json`, `d01ca71b...json`, `5589abf0...json`
  - 4 run logs under `logs/phase_o15_ablation/` (gitignored per project convention; regenerable via canonical command below)
  - New follow-up: `P1-ADR-0025-AMENDMENT-K6-K7-SIZE-DOWN-VS-BLOCK` (cycle subsequent to this closure per ADR-0027 §D-3)
  - Commit SHA: see audit trail §"Closure"

## Cross-references

- Parent KPI report card: [H062 v2](H062_kpi_report_v2.md) (frontmatter `parent_kpi_report_card`)
- Stage tracker: [stage.md](stage.md)
- Failure log: [failure_log.md](failure_log.md)
- Audit-remediate-loop trail (this investigation): [docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md](../../../docs/audits/audit_trail_2026-05-19_h062-v3-primitive-attribution-ablation.md)
- ADR-0027 §D-1 source mandate: [docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md](../../../docs/decisions/ADR-0027-operational-discipline-bounded-exploration.md)
- ADR-0025 primitive infrastructure: [docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md](../../../docs/decisions/ADR-0025-abandonment-trigger-infrastructure.md)
- ADR-0026 paradigm + reporting refinements: [docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md](../../../docs/decisions/ADR-0026-paradigm-and-reporting-refinements.md)
- ADR-0014 reporting format (NOT used here per ADR-0027 §D-1(e) — investigation-memo class): [docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md](../../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md)
- ADR-0017 survival-constrained primary metric vector: [docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md](../../../docs/decisions/ADR-0017-survival-constrained-optimization-paradigm.md)

## Append discipline

- Sections 1-5 are FROZEN at investigation start (2026-05-19); they MAY be edited only via versioned-successor pattern per ADR-0013 §4.1.
- Sections 6-8 are APPEND-as-work-completes; rows in the §6 ablation table are immutable once landed.
- File deletion is fail-closed under [scripts/_hooks/check_non_loss_deletion.py](../../../scripts/_hooks/check_non_loss_deletion.py).
