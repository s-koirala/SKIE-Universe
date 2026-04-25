---
name: H050 cross-symbol aggregation rule — addendum
description: Path-A in-place addendum to design.md formalising the cross-symbol aggregation rule for universe = [ES, NQ]; resolves P1-H050-AGGREGATION-RULE under sub-rule 2a + sub-rule 3.3a; gates Cell I Databento backfill.
type: project
hypothesis_id: H050
parent: design.md
status: designed
revision: r2
effective_from: 2026-04-24
owner: skoir
---

# H050 — cross-symbol aggregation-rule addendum (2026-04-24)

This addendum is an in-place **Path A clarification** to [design.md](design.md) for hypothesis H050. It disambiguates the cross-symbol return-aggregation rule that [design.md](design.md) §1 leaves underspecified for `universe = [ES, NQ]` per [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml). [design.md](design.md) is the immutable pre-registration record and is **not modified**; this addendum is the binding clarification that future auditors and runs must read jointly with §1, §2 and §10 of [design.md](design.md).

Resolution memo (3-round audit-remediate-loop cap reached): [docs/research_notes/memo_h050-aggregation-rule_2026-04-24.md](../../../docs/research_notes/memo_h050-aggregation-rule_2026-04-24.md) (revision r4). Audit trail: [docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md](../../../docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md). User accepted the resolution memo's recommendation bundle (sub-rule 2a + sub-rule 3.3a + Path A) on 2026-04-24.

## §1. Cross-symbol aggregation rule — formal definition

### §1.1 Scope of the ambiguity

[design.md](design.md) §1 binds the test statistic `T_H050 = SR_{filtered, gated} − SR_{filtered, unconditional}` and §2 binds `Instruments: ES and NQ front-month`, but neither specifies how the two per-symbol return streams combine into the single per-bar series `r_t` whose Sharpe ratio enters `T_H050`. Under the project's inference primitives ([src/skie_ninja/inference/stats/sharpe_ci.py](../../../src/skie_ninja/inference/stats/sharpe_ci.py) — `opdyke2007_ci` consumes a single 1-D return-series array; [src/skie_ninja/inference/multipletest/hansen_spa.py](../../../src/skie_ninja/inference/multipletest/hansen_spa.py) — Hansen 2005 SPA expects single-series strategy returns per column), aggregation must occur upstream of the inference layer. This addendum locks that upstream construction.

### §1.2 Sub-rule 2a — equal-weighted constant 0.5/0.5 in return space

For each OOS walk-forward fold, at each bar `t ∈ test_fold`, the aggregate strategy per-bar return is defined as the equal-weighted constant linear combination of the two per-symbol strategy returns in arithmetic-return space:

```
r_p_gated(t)   = w_ES · r_ES_gated(t)   + w_NQ · r_NQ_gated(t)
r_p_uncond(t)  = w_ES · r_ES_uncond(t)  + w_NQ · r_NQ_uncond(t)

with  w_ES = w_NQ = 1/2
```

where `r_i_gated(t)` is symbol `i`'s arithmetic per-bar strategy return at bar `t` after the full per-symbol pipeline has been applied (LightGBM-derived signed position, HMM gate-state indicator `g_i(t) ∈ {0, 1}` per [design.md](design.md) §5, transaction-cost deduction per [src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py](../../../src/skie_ninja/backtest/costs/nt8_es_nq_rth_v1.py) `nt8_es_nq_rth_v1` cost-model id). The expanded form of `r_i_gated(t)` is given in §2.2 below — §1.2 treats `r_i_gated(t)` as an opaque per-bar scalar to keep the cross-symbol aggregation step separate from the per-symbol gating + cost-deduction step. Likewise `r_i_uncond(t)` is the corresponding unconditional series (`g_i(t)` replaced by the identity 1 for all `t`, otherwise identical pipeline).

Both `r_p_gated` and `r_p_uncond` are then concatenated across all OOS walk-forward folds into two single series of length `T_oos = Σ_fold |test_fold|`, which feed the Sharpe-CI primitives.

This formal definition assumes both ES and NQ panels cover the full pre-reg window per [design.md](design.md) §2 (2015-01-01 → 2025-12-31). Under the current substrate (ES 2020-2025 + NQ 2020-2024), `r_NQ_*(t)` is structurally absent for parts of the pre-reg window, which would silently halve the effective leverage of `r_p_*` on those bars under §2.2 sub-rule 3.3a. The addendum therefore presupposes the Cell I Databento backfill (`P1-H050-DATA-COVERAGE` resolution) has completed before any walk-forward run is executed under this rule; running under the current incomplete substrate would constitute an additional pre-reg deviation and is foreclosed by §8 below.

The weights are arithmetic-return-space weights, not notional-space weights. SR is scale-invariant under any positive scalar capital base (`SR(c · r) = sign(c) · SR(r)` for `c ≠ 0`), so the choice of return-space weights is well-defined irrespective of the live-execution capital plan. Live-execution mapping from return-space-equal-weights to integer-contract positions is tracked separately under follow-up `P1-H050-EXECUTION-WEIGHT-MAP` and is out of scope for this addendum.

### §1.3 Anchor citations

The construction has two distinct heritage components, cited separately:

- **Per-bar weighted-sum portfolio-return construction**: [Markowitz, H. 1952. "Portfolio Selection." *J. Finance* 7(1):77-91, doi:10.1111/j.1540-6261.1952.tb01525.x](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) — the foundational mean-variance framework on which any later portfolio-Sharpe analysis rests; portfolio expected return as the weighted sum of constituent returns.
- **Sharpe ratio as reward-to-variability ratio of the resulting single series**: [Sharpe, W. F. 1966. "Mutual Fund Performance." *J. Business* 39(1):119-138, doi:10.1086/294846](https://doi.org/10.1086/294846) — original definition; with single-series asymptotic distribution per [Lo, A. W. 2002. "The Statistics of Sharpe Ratios." *FAJ* 58(4):36-52, doi:10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453) and HAC-adjusted variant per [Opdyke, J. D. 2007. "Comparing Sharpe ratios: So where are the p-values?" *J. Asset Management* 8(5):308-336, doi:10.1057/palgrave.jam.2250084](https://doi.org/10.1057/palgrave.jam.2250084).
- **Equal-weighting (1/N) as the substrate-blind benchmark**: [DeMiguel, V.; Garlappi, L.; Uppal, R. 2009. "Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy?" *Review of Financial Studies* 22(5):1915-1953, doi:10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075) — out-of-sample comparison across 7 datasets shows the 1/N portfolio is not consistently dominated by 14 sample-based optimal-portfolio policies, given estimation error in the inputs to mean-variance optimisation. Under the "no asymmetry information asserted at pre-reg" prior of this addendum, 1/N is the canonical Markowitz portfolio.

[Sharpe, W. F. 1994. "The Sharpe Ratio." *JPM* 21(1):49-58, doi:10.3905/jpm.1994.409501](https://doi.org/10.3905/jpm.1994.409501) is **not** invoked at the per-bar portfolio-return-construction step (Sharpe 1994 frames the SR around a differential return and explicitly disclaims SR as a stand-alone object for "a single investment return"); its framing is appropriate for `T_H050` viewed as a differential statistic, not for the inner portfolio-Sharpe construction (memo r4 audit finding L-3).

### §1.4 What §1.2 forecloses

By locking sub-rule 2a, the following alternative aggregation rules are foreclosed for any H050 walk-forward run conducted under this addendum:

- Pooled-concatenation (stack ES and NQ end-to-end into a single time series) — rejected on theoretical grounds: the concatenated series is not the return process of any tradable strategy (memo r4 §2.1).
- Sub-rule 2b (equal-contracts dollar-PnL-weighted), 2c (equal-volatility / risk-parity), 2d (capacity-ceiling-proportional) — admissible as pre-reg rules but use observable price/vol inputs; foreclosed under Path A's substrate-independence constraint (§3 below). Any future adoption requires a successor hypothesis ID per [design.md](design.md) §10.
- Family-3 per-symbol-Sharpe-then-aggregate (mean-of-Sharpe-differentials) — admissible but requires a multivariate-SR CI machinery ([Wright, J. A.; Yam, S. C. P.; Yung, S.-P. 2014. "A test for the equality of multiple Sharpe ratios." *J. Risk* 16(4):3-21, doi:10.21314/JOR.2014.289](https://doi.org/10.21314/JOR.2014.289)) not currently in [src/skie_ninja/inference/](../../../src/skie_ninja/inference/); foreclosed pending follow-up `P1-H050-MULTIVARIATE-SR`.

## §2. Symbol-level inactivity handling — sub-rule 3.3a

### §2.1 The position-value space

Per [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) (locate via grep on the line containing `position = np.sign(2.0 * p - 1.0)`; verified at line 848 of a 1026-line file as of revision r2 commit-time) the position mapping is `position = np.sign(2.0 * p − 1.0)` where `p` is the LightGBM classifier's probability output, so each per-symbol position takes values in `{−1, 0, +1}`. (Memo r4 §3.3 cited line 613; r1 of this addendum cited :852 against a 1030-line file. Both numeric anchors drifted across orchestrator edits, so r2 replaces numeric line/length references with grep-anchored text references for forward-robustness.) The flat (zero) position arises whenever the classifier emits exactly `p = 0.5`. LightGBM tree outputs are sums of leaf values — a discrete (though dense) set — so exact-tie predictions occur empirically rarely but are not measure-zero (memo r4 audit finding F-2-4); a runtime counter must be emitted (§2.4 below).

For the gated series, the per-symbol per-bar return additionally multiplies by the HMM gate-state indicator `g_i(t) ∈ {0, 1}` (1 iff symbol `i`'s causal-filter-decoded state at `t` is the gate state per [design.md](design.md) §5). A bar with no gated contribution from symbol `i` therefore arises when either `position_i(t) = 0` or `g_i(t) = 0`.

### §2.2 Sub-rule 3.3a — hold inactive in cash

When a symbol's gate or signal is inactive at bar `t` (i.e., the per-symbol gated return is zero), that symbol's contribution to the aggregate is zero in return space and the constant 0.5/0.5 weights are **held**, not renormalised. Formally:

```
r_p_gated(t) = (1/2) · g_ES(t) · sign(2 p_ES(t) − 1) · ret_ES(t)·net
             + (1/2) · g_NQ(t) · sign(2 p_NQ(t) − 1) · ret_NQ(t)·net
```

where `ret_i(t)·net` is symbol `i`'s arithmetic per-bar return net of costs and `sign(0) = 0` so a flat classifier prediction sets the symbol's contribution to zero.

The unconditional benchmark uses the symmetric construction with `g_ES(t) = g_NQ(t) = 1` for all `t` (no gating is applied, so the indicator is identically 1) and is otherwise identical:

```
r_p_uncond(t) = (1/2) · sign(2 p_ES(t) − 1) · ret_ES(t)·net
              + (1/2) · sign(2 p_NQ(t) − 1) · ret_NQ(t)·net
```

This is sub-rule 3.3a (memo r4 §3.3). Renormalising the surviving weights when only one symbol is active (sub-rule 3.3b) is foreclosed: renormalisation makes the gated-vs-unconditional comparison dependent on the simultaneous-gating frequency, which is a property the test must *measure* rather than absorb into the construction (memo r4 §3.3 closing paragraph).

### §2.3 Bar-axis alignment

Implementation must form a shared `ts_event` index by **outer-join** of the two per-symbol DataFrames; bars present for one symbol but missing the other are filled with `r_missing_sym(t) := 0.0` for both gated and unconditional return columns. This implements §2.2 at the bar level. Outer-join (rather than inner-join) preserves any per-symbol-only bar arising from holiday-half-day asymmetries, halts, or session-boundary edge cases that an inner-join would silently drop.

The fraction `f_miss = missing_bars / total_bars` is recorded per fold per symbol in run provenance ([src/skie_ninja/utils/reproducibility.py](../../../src/skie_ninja/utils/reproducibility.py) `ReproLog.run_metadata`). A structural-asymmetry warning is emitted if `f_miss > 0.01` per fold per symbol; the 1% anchor matches the §2.4 `flat_bars_count` threshold and aligns to the implicit "shared CME RTH calendar" prior. The threshold is itself a placeholder anchor pending empirical calibration on real data, tracked under follow-up `P1-MISSING-BAR-RATE-EMPIRICAL`.

### §2.4 Flat-prediction bookkeeping

Per-fold provenance records two scalars per side per symbol:

- `flat_bars_count_gated_{sym}` — count of bars at which `position_sym(t) = 0` AND `g_sym(t) = 1` on the gated side.
- `flat_bars_count_uncond_{sym}` — count of bars at which `position_sym(t) = 0` on the unconditional side.

A warning is emitted if either count divided by `total_bars` exceeds 0.01 per fold per symbol (memo r4 §3.3 + §3.4 audit findings F-2-4 and F-3-6). The threshold is the same empirical-calibration anchor as in §2.3.

## §3. Path A invocation — eligibility and gates

### §3.1 Path A vs successor hypothesis ID

[design.md](design.md) §2 line 41 ("re-runs on extended windows require a successor hypothesis ID"), [design.md](design.md) §10 (decision rule and archive policy), and [design.md](design.md) line 22 of body text ("This document is the pre-registration record for hypothesis H050. Frozen at `designed`; any change requires a new hypothesis ID.") together imply that material changes to the pre-reg require a successor ID. Path A is admissible only as an in-place addendum that disambiguates an underspecified mechanic without altering any binding statistic, universe, or window in [design.md](design.md). It is **not** a free-floating "clarification" escape hatch.

This addendum invokes Path A under both the eligibility criteria documented in memo r4 §4.1.1:

1. **Genuine textual ambiguity in [design.md](design.md) §1 / §2** — established. §1 names the test statistic `T_H050` but is silent on multi-symbol combination semantics; §2 lists `[ES, NQ]` without specifying how the two per-symbol streams combine into a single series. A literal reading therefore has no unique referent for `r_t` when `t` indexes bars on two symbols simultaneously.
2. **No post-pre-reg substrate-conditioned selection** — established only conditional on §3.2 substrate-blind-rationale attestation AND §3.3 Path-B robustness gate pre-registration. Both gates must be satisfied for Path A to remain admissible.

If either gate fails, Path B (successor hypothesis ID `H050.1` or equivalent) becomes mandatory; there is no "Path A.5" partial-precedent bypass (memo r4 §4.1.1).

### §3.2 Substrate-blind-rationale attestation

The Tier-2b ES + NQ 1-min raw substrate landed on 2026-04-23 ([CLAUDE.md](../../../CLAUDE.md) "Tier-2b buildout (started 2026-04-23) → ES + NQ 1-min raw (evidence-bar tier)" bullet; ingest audit trail [docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md](../../../docs/audits/audit_trail_2026-04-23_vendor-legacy-1min-ingest.md)), one calendar day before this addendum (2026-04-24). The user has had ≥1 day of substrate access prior to addendum acceptance. The substrate-blind-rationale attestation, recorded here as part of the addendum's binding text, is:

> **Attestation (2026-04-24, owner skoir):** the choice of equal-weighted constant 0.5/0.5 in arithmetic-return space (sub-rule 2a) was made blind to the project's ES + NQ Tier-2b substrate. No relative-behavior inspection of ES vs NQ — including but not limited to per-symbol Sharpe, per-symbol gating-firing-rate, per-symbol vol or drift, per-symbol drawdown, or any cross-symbol diagnostic on the 2026-04-23-landed Tier-2b panel — was performed between substrate ingest (2026-04-23) and addendum acceptance (2026-04-24). The recorded basis for sub-rule 2a is the substrate-blind prior of "no asymmetry information asserted at pre-reg" (memo r4 §3.2 item 1), anchored exclusively in published prior-art:
>
> - [Markowitz 1952](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) — minimum-variance robustness under estimation uncertainty; equal weights are the canonical Markowitz portfolio when no asymmetry information is asserted at pre-reg.
> - [DeMiguel, Garlappi & Uppal 2009](https://doi.org/10.1093/rfs/hhm075) — the 1/N portfolio is not consistently dominated by 14 sample-based optimal-portfolio policies out-of-sample across 7 datasets; estimation error in mean-variance inputs is the binding constraint that motivates 1/N as the substrate-blind benchmark.
> - [Sharpe 1966](https://doi.org/10.1086/294846) — reward-to-variability ratio framing for the resulting single-series object.
> - [Bailey & López de Prado 2014. "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality." *JPM* 40(5):94-107, doi:10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094) — DSR (Deflated Sharpe Ratio) as the ex-post hurdle for any data-tuned weighting; motivates ex-ante simplicity (1/N) when the DSR multiple-testing penalty has not been pre-allocated to a tuning search.
>
> Any later inspection that violates the no-relative-behavior-inspection clause must be disclosed in a successor-ID amendment per [design.md](design.md) §10.

The substrate-blind constraint forecloses any data-tuned weighting (mean-variance, ERC, min-vol, Kelly, capacity-proportional, risk-parity-with-realised-vol) at the addendum level. Such weightings would inherit a substrate-inspection-conditioned-choice problem (selection-HARK, [Bailey-LdP 2014](https://doi.org/10.3905/jpm.2014.40.5.094)) and require a successor hypothesis ID per [design.md](design.md) §10 + ¶22.

### §3.3 Path-B robustness gate — pre-registration

Path A's second eligibility criterion requires a falsifiable test that converts the unverifiable temporal claim of §3.2 into a robustness-comparison run at evidence-bar-run time. The robustness gate is the secondary analysis run **alongside** the primary 2a result on every H050 evidence-bar walk-forward run (not a fallback triggered only on primary failure — both runs are produced and reported jointly). The gate is pre-registered here as a **single-variant Path-B run** (no k-variant search, no Hansen 2005 SPA over Path-B variants); the single-variant choice avoids importing a multiple-testing penalty into the robustness comparison and the simplicity is itself substrate-blind.

#### §3.3.1 The Path-B variant

The robustness variant is sub-rule 2c (risk-parity / equal-volatility) with the per-symbol volatility vector `σ = (σ_ES, σ_NQ)` frozen from a pre-substrate public source: the closing levels of [VIXCLS](https://fred.stlouisfed.org/series/VIXCLS) (CBOE Volatility Index, S&P 500 30-day implied vol — proxy for ES) and [VXNCLS](https://fred.stlouisfed.org/series/VXNCLS) (CBOE Nasdaq-100 Volatility Index — proxy for NQ), both pulled at the fixed pre-substrate baseline date **2015-01-02** (first NYSE/CBOE trading day of the pre-reg train window per [design.md](design.md) §2 line 37; 2015-01-01 is a holiday). The σ vector is therefore independent of any post-pre-reg ES/NQ price observations on the project's substrate.

```
σ_ES := VIXCLS(2015-01-02) = 17.79 # definitional proxy for ES 30-day implied vol
σ_NQ := VXNCLS(2015-01-02) = 19.20 # definitional proxy for NQ 30-day implied vol
w_ES_pathB = (1/σ_ES) / (1/σ_ES + 1/σ_NQ) ≈ 0.5191
w_NQ_pathB = (1/σ_NQ) / (1/σ_ES + 1/σ_NQ) ≈ 0.4809
```

The frozen σ values were retrieved on 2026-04-24 via the FRED CSV endpoint `https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS,VXNCLS&cosd=2015-01-02&coed=2015-01-02`. Canonical 2-line snapshot (header + 2015-01-02 row) SHA256: `93f7d05caf6d4819ddd934383adbc77115c4c2d428af329c0d78ccb60aca21c4` (computed via `printf "observation_date,VIXCLS,VXNCLS\n2015-01-02,17.79,19.20\n" | sha256sum`). Any auditor must reproduce identical values; FRED revisions to the 2015-01-02 close (none expected for VIXCLS / VXNCLS, both of which are CBOE-published primary observations) would constitute a successor-ID amendment per [design.md](design.md) §10.

The `:=` (definitional assignment) signals that VIXCLS and VXNCLS are not assumed equal to actual realised ES / NQ futures volatility; they are pre-substrate public-source proxies adopted as the σ inputs to the risk-parity formula. The empirical-equivalence question between VIX/VXN-frozen proxies and realised vol is deferred to §3.3.3 and the H050 evidence-bar deliverable.

Anchor citations for the volatility-index design (historical):

- [Whaley, R. E. 1993. "Derivatives on Market Volatility: Hedging Tools Long Overdue." *J. Derivatives* 1(1):71-84, doi:10.3905/jod.1993.407868](https://doi.org/10.3905/jod.1993.407868) — historical-design reference for the original (Black-Scholes ATM-implied-vol-based) VIX. **Not the operational anchor** for VIXCLS, which uses the post-2003 CBOE model-free methodology; cited here for completeness of the VIX heritage chain. (DOI verified clean against the Crossref API on 2026-04-24 — the prior r1 unverified-DOI residual is closed.)

Operational anchor:

- CBOE 2003 model-free VIX White Paper methodology (the post-2003 model-free formulation backfilled by CBOE to 1990 in the published VIXCLS series). VIXCLS provenance: [FRED VIXCLS](https://fred.stlouisfed.org/series/VIXCLS) (CBOE-published, Federal-Reserve-Bank-of-St-Louis-archived). VXNCLS provenance: [FRED VXNCLS](https://fred.stlouisfed.org/series/VXNCLS).

The σ vector is recorded verbatim in the addendum's bound run-time configuration so any auditor can recompute the Path-B weights deterministically.

#### §3.3.2 Joint reporting protocol

Every H050 evidence-bar walk-forward run emits, side by side:

- `T_H050(2a)` — the primary statistic with sub-rule 2a (equal-weighted) per §1.2.
- `T_H050(2c | σ from VIX/VXN @ 2015-01-02)` — the robustness statistic with sub-rule 2c per §3.3.1.

Both statistics are computed on the same per-symbol gated and unconditional return matrices (§1.2 inputs are shared); only the per-bar weight vector differs. The CIs on each statistic are computed independently per the inference machinery in §4.

The Path-B-equivalence judgement is a **disagreement-flagging diagnostic**, not a hypothesis test, so no Bonferroni penalty is applied and the Path-B `T_H050(2c)` statistic does **not** enter the Hansen 2005 SPA family of §4.3 — only the primary `T_H050(2a)` statistic does. The disagreement criteria are:

- **Concordant pass**: both 2a and 2c CIs on `T_H050` exclude zero at one-sided α = 0.05 ([ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md)). The primary 2a result stands as the H050 evidence-bar deliverable.
- **Concordant fail**: both 2a and 2c CIs cover zero. The primary 2a result stands; the H050 archival classification is `archive(null)` per [design.md](design.md) §10.
- **Discordant**: the two CIs disagree at the inclusion-of-zero level. The disagreement itself is a finding and is recorded in the run provenance; the primary 2a result still stands as the binding `T_H050` for [design.md](design.md) §10 archival classification, but the discordance triggers a follow-up `P1-H050-PATHB-DISCORD-{run_id}` for explicit user review before promotion to paper-trade eligibility.

The bootstrap CIs for the robustness comparison reuse [src/skie_ninja/inference/bootstrap.py](../../../src/skie_ninja/inference/bootstrap.py) (Politis-Romano 1994 stationary bootstrap with Politis-White 2004 automatic block-length selection), as detailed in §4.

#### §3.3.3 Empirical-anchoring residual

The §3.3.1 σ-frozen-from-VIX/VXN proposal is operationally cheap but its empirical equivalence to risk-parity-with-realised-vol has not been validated on real data. This is documented as a Round-3 residual in [docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md](../../../docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md) §"Residual risk" item 2 and is part of the H050 evidence-bar deliverable — empirical assessment occurs in the first H050 walk-forward run, not at addendum-acceptance time.

## §4. Inference statistics

### §4.1 Single-side single-strategy CIs (per side, per [design.md](design.md) §8)

Per-side single-strategy CIs on `SR(r_p_gated)` and `SR(r_p_uncond)` use [opdyke2007_ci](../../../src/skie_ninja/inference/stats/sharpe_ci.py) — the Mertens-HAC variant of [Opdyke 2007](https://doi.org/10.1057/palgrave.jam.2250084) under stationary-ergodic returns. This preserves the [design.md](design.md) §8 binding (single-strategy gate uses Opdyke 2007); no §8 substitution is performed.

The HAC long-run-variance estimator within `opdyke2007_ci` consumes the single per-bar series `r_p_*(t)` produced by §1.2, so cross-asset auto- and cross-covariance is automatically embedded in the long-run variance via the standard portfolio-variance identity:

```
Var(r_p) = (1/4) · Var(r_ES) + (1/4) · Var(r_NQ) + (1/2) · Cov(r_ES, r_NQ)
```

The absorption happens at the portfolio-construction step (§1.2), not within Opdyke's formula (memo r4 §3.2 item 4 audit finding L-6).

### §4.2 Differential CI on `T_H050` (Ledoit-Wolf 2008)

The differential statistic `T_H050 = SR(r_p_gated) − SR(r_p_uncond)` is the *paired* difference of two Sharpe ratios on the same time axis (the two series are computed on identical bars from the same strategies, differing only by the HMM gate). [rules/quant-project.md](../../../.claude/rules/quant-project.md) Inference clause binds pairwise SR comparison to:

[Ledoit, O. & Wolf, M. 2008. "Robust performance hypothesis testing with the Sharpe ratio." *J. Empirical Finance* 15(5):850-859, doi:10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002) — studentized time-series bootstrap CI on the difference of two Sharpe ratios. The studentization handles the non-pivotal nature of the SR difference; the time-series bootstrap handles the autocorrelation in `r_p_*`.

The bootstrap implementation reuses [src/skie_ninja/inference/bootstrap.py](../../../src/skie_ninja/inference/bootstrap.py) — [Politis, D. N. & Romano, J. P. 1994. "The Stationary Bootstrap." *J. American Statistical Association* 89(428):1303-1313, doi:10.1080/01621459.1994.10476870](https://doi.org/10.1080/01621459.1994.10476870) stationary bootstrap with [Politis, D. N. & White, H. 2004. "Automatic block-length selection for the dependent bootstrap." *Econometric Reviews* 23(1):53-70, doi:10.1081/ETC-120028836](https://doi.org/10.1081/ETC-120028836) automatic block-length selection (with the Patton-Politis-White 2009 corrections already implemented per [CLAUDE.md](../../../CLAUDE.md) Cycle 5). The block-bootstrap variant choice (stationary vs circular) is bound by [src/skie_ninja/inference/bootstrap.py](../../../src/skie_ninja/inference/bootstrap.py) — stationary is the implementation default and is the variant used here. This is an implementation-bound choice, not a literature-level primacy claim about Ledoit-Wolf 2008's text (memo r4 §3.1 audit finding F-3-1).

The per-side Opdyke 2007 CIs (§4.1) and the Ledoit-Wolf 2008 differential CI (§4.2) share a single block-length selected via `politis_white_block_length` on the *paired-difference* series `r_p_gated(t) − r_p_uncond(t)` — this preserves the residual-autocorrelation structure of the differential statistic and ensures the per-side and differential CIs are computed under a unified bootstrap configuration. The selected block-length is recorded in [logs/reproducibility/{run_id}.json](../../../logs/reproducibility/) `ReproLog.run_metadata` for any auditor to recompute the bootstrap distribution deterministically.

This addendum does **not** substitute the [design.md](design.md) §8 single-strategy `opdyke2007_ci` binding; the Ledoit-Wolf 2008 differential CI is the natural inferential complement to `T_H050` viewed as a paired differential statistic, layered atop the per-side Opdyke CIs (memo r4 audit finding F-2-5 joint-clarification scope note). This jointly closes the blocking follow-up `P1-H050-CI-DIFFERENTIAL`.

### §4.3 Multiple-testing — Hansen 2005 SPA

`T_H050` enters the strategy-universe SPA family per [rules/quant-project.md](../../../.claude/rules/quant-project.md) Inference clause and [src/skie_ninja/inference/multipletest/hansen_spa.py](../../../src/skie_ninja/inference/multipletest/hansen_spa.py):

[Hansen, P. R. 2005. "A Test for Superior Predictive Ability." *J. Business & Economic Statistics* 23(4):365-380, doi:10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063) — multi-strategy SPA test with the three §2.4 recentering variants SPA_l / SPA_c / SPA_u. Bootstrap indices are shared across strategies for cross-dependence preservation per Hansen 2005 §2.

[design.md](design.md) §1 line 30 phrases the multiple-testing family as "Romano-Wolf step-down". This addendum acknowledges the pre-existing pre-reg-artifact inconsistency between [design.md](design.md) (Romano-Wolf) and [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml) + [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) (Hansen SPA); the inconsistency pre-dates this addendum and is tracked separately as `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` (memo r4 §0 footnote F-1-8). Resolution of that inconsistency is **out of scope** for this aggregation-rule addendum and does not gate Cell I.

## §5. Implementation directives (binding for orchestrator)

This section materialises the gap between the addendum-bound rule's spec and the current orchestrator's per-bar return computation. The directives below are **evidence-bar-blocking** for the first H050 walk-forward run executed under this addendum.

### §5.1 Arithmetic-vs-log return-space binding (Round-4 M1 remediation)

The §1.2 + §2.2 aggregation `r_p(t) = w_ES · r_ES(t) + w_NQ · r_NQ(t)` is bound in **arithmetic-return space**. The portfolio identity `r_p = w · r_ES + w · r_NQ` holds *exactly* only for arithmetic returns; for log returns it is a first-order Taylor approximation and the exactness is broken whenever `r_p` is later compounded ([Campbell, J. Y.; Lo, A. W.; MacKinlay, A. C. 1997. *The Econometrics of Financial Markets.* Princeton University Press. ISBN 978-0-691-04301-2; doi:10.1515/9781400830213](https://doi.org/10.1515/9781400830213) §1.4 "Continuously compounded returns" — log returns aggregate exactly across time but **not** across assets, while arithmetic returns aggregate exactly across assets but not across time). [~/.claude/rules/quant-project.md](../../../.claude/rules/quant-project.md) "Time-series integrity" clause requires explicit specification of log-vs-arithmetic and the compounding convention; this addendum's §1.2 + §2.2 binding to arithmetic-return space discharges that requirement.

The current orchestrator [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) (locate via grep on the line containing `r_bar[1:] = np.diff(np.log(closes))`; verified at line 662 of a 1026-line file as of revision r2 commit-time) computes per-bar **log returns**: `r_bar[t] = log(close[t]) − log(close[t−1])`. The discrepancy is small at 1-min ES/NQ scale — the magnitude bound is `|R(t) − r(t)| ≈ r(t)²/2` per Campbell-Lo-MacKinlay 1997 §1.4 eq. (1.4.4), and at 1-min ES/NQ realised vol on the order of 1e-4 per bar this gives `|R − r|` on the order of `O(1e-8)` per bar — but the addendum-bound rule requires the *exact* arithmetic-space aggregation, not a first-order-equivalent approximation. The user-accepted §1.2 binding to arithmetic-return space (memo r4 recommendation, accepted 2026-04-24) is preserved here; r2 does **not** rebind to log-return space (such a rebinding would be a successor-ID amendment per [design.md](design.md) §10).

Directive (binding):

> **Per-bar log-return → arithmetic-return conversion `R_i(t) = exp(r_i(t)) − 1` MUST be performed before the equal-weighted aggregation `R_p(t) = 0.5 · R_ES(t) + 0.5 · R_NQ(t)` is computed.** The conversion happens at the per-symbol per-bar gated/unconditional return scalar (i.e., on `r_i_gated(t)` and `r_i_uncond(t)` of §1.2) before the §2.2 weighted sum is taken. Strategy-side entry/exit signals (`sign(2 p − 1)`, `g(t)`) operate on the arithmetic per-bar return; cost deduction (`nt8_es_nq_rthv1`) is also applied in arithmetic-return space.

The downstream [src/skie_ninja/inference/stats/](../../../src/skie_ninja/inference/stats/) Cycle-2 NW-HAC + Sharpe-CI primitives consume per-bar return series at the function-input boundary; they only require the input series be stationary and ergodic, and are convention-agnostic with respect to log-vs-arithmetic. The convention is therefore enforced upstream of `opdyke2007_ci` and the Ledoit-Wolf 2008 differential CI, not inside them.

### §5.2 Verification gate (new follow-up `P1-H050-AGGREGATION-CONVENTION-TEST`)

A unit test asserting numerical equivalence between (i) the addendum-bound rule's aggregate `R_p(t) = 0.5 · R_ES(t) + 0.5 · R_NQ(t)` with `R_i(t) = exp(r_i(t)) − 1` and (ii) the orchestrator's `P1-H050-DUAL-SYMBOL-ORCHESTRATOR` implementation MUST be added before the first H050 walk-forward run governed by this addendum. The test is tracked as new follow-up `P1-H050-AGGREGATION-CONVENTION-TEST`. Test contract:

- Synthetic two-symbol panel covering ≥ 2 walk-forward folds at the same minute frequency as the production substrate.
- Compute `R_p_test(t)` via the addendum-bound rule (per-bar `exp(r) − 1` → equal-weighted sum).
- Compute `R_p_orch(t)` via the production orchestrator path under `P1-H050-DUAL-SYMBOL-ORCHESTRATOR`.
- Assert `np.allclose(R_p_test, R_p_orch, atol=1e-12, rtol=0.0)` (machine-precision agreement; the per-bar conversion is a deterministic non-stochastic transformation, so atol = 1e-12 is the appropriate tolerance, not 1e-8).
- The unit test lives under `tests/unit/orchestrator/test_h050_aggregation_convention.py` (or equivalent path under `P1-H050-DUAL-SYMBOL-ORCHESTRATOR`'s test layout) and is a CI-blocking test for any commit that touches `r_bar` computation in [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) or its successor module.

### §5.3 Ledoit-Wolf 2008 differential-CI implementation gap (Round-4 M2 remediation)

The §4.2 binding to "Ledoit-Wolf 2008 studentized time-series bootstrap" for the differential CI on `T_H050 = SR(r_p_gated) − SR(r_p_uncond)` is currently a **spec-level binding without a callable implementation**. Verified at addendum revision r2 commit-time:

- [src/skie_ninja/inference/stats/sharpe_ci.py](../../../src/skie_ninja/inference/stats/sharpe_ci.py) module docstring (locate via grep on the lines containing `Ledoit, O. & Wolf, M. 2008` and `used in Cycle 5 for SPA differentials, not here`) explicitly states LW2008 was *not* implemented in that module.
- The same module's "Scope" section (locate via grep on `Ledoit-Wolf comparison CI (for Hansen SPA differentials) will be implemented in Cycle 5 alongside the SPA routines`) defers LW2008 to Cycle 5, but Cycle 5 ([CLAUDE.md](../../../CLAUDE.md) bullet) shipped Hansen 2005 SPA + Politis-Romano stationary bootstrap + Politis-White block-length only — no LW2008 callable was actually shipped to [src/skie_ninja/inference/](../../../src/skie_ninja/inference/).
- No callable `ledoit_wolf_2008_*`, `lw2008_*`, or differential-Sharpe-CI function exists in the `inference` package as of r2.

Directive (binding):

> The Ledoit-Wolf 2008 studentized time-series bootstrap differential-CI for the gated-vs-unconditional Sharpe statistic is bound at the spec level (§4.2); the callable implementation is currently **absent** from [src/skie_ninja/inference/stats/](../../../src/skie_ninja/inference/stats/) and the gap is tracked as new evidence-bar-blocking follow-up `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL`. **The first H050 walk-forward run governed by this addendum is gated on this callable's implementation.** Construction (per Ledoit & Wolf 2008 §3.1 + the project's existing bootstrap primitives):
>
> - Studentized statistic `(SR_gated − SR_uncond) / se_boot`, where `se_boot` is the stationary-bootstrap standard error of the per-bootstrap-replicate Sharpe difference, computed by reusing [src/skie_ninja/inference/bootstrap.py](../../../src/skie_ninja/inference/bootstrap.py) `politis_white_block_length` + `stationary_bootstrap_indices` primitives applied to the **paired-difference series** `r_p_gated(t) − r_p_uncond(t)` (consistent with the §4.2 unified-block-length binding).
> - The studentization handles the non-pivotal nature of the SR difference; the time-series bootstrap handles autocorrelation in `r_p_*`. Bootstrap CI level: 95% two-sided per [ADR-0004](../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md).
> - The function signature should match the existing `opdyke2007_ci` style (return a frozen `SharpeCIResult`-equivalent dataclass with `lower`, `upper`, `level`, `method`, and the selected `block_length` for reproducibility).

The follow-up `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` is to be added to the [CLAUDE.md](../../../CLAUDE.md) blocker inventory in a separate workstream by the parent agent — this addendum does not modify [CLAUDE.md](../../../CLAUDE.md). The follow-up is evidence-bar-blocking on the same footing as `P1-H050-CI-DIFFERENTIAL` (which §4.2 closes at the spec-binding level but which §5.3 keeps open at the implementation-callable level).

## §6. Cross-references

### §6.1 Resolution-memo and audit-trail anchors

- Resolution memo (3-round audit-remediate-loop cap reached, r4): [docs/research_notes/memo_h050-aggregation-rule_2026-04-24.md](../../../docs/research_notes/memo_h050-aggregation-rule_2026-04-24.md).
- Audit trail for memo: [docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md](../../../docs/audits/audit_trail_2026-04-24_h050-aggregation-rule.md).
- Audit trail for this addendum: [docs/audits/audit_trail_2026-04-24_h050-aggregation-addendum.md](../../../docs/audits/audit_trail_2026-04-24_h050-aggregation-addendum.md).
- Surfacing trigger: [docs/research_notes/memo_option-b-data-coverage_2026-04-24.md](../../../docs/research_notes/memo_option-b-data-coverage_2026-04-24.md) §11.1.
- Cycle-6 pause memo: [docs/research_notes/memo_cycle6-pause-status_2026-04-24.md](../../../docs/research_notes/memo_cycle6-pause-status_2026-04-24.md).
- Project [CLAUDE.md](../../../CLAUDE.md) "Cycle 6 partial" bullet for `P1-H050-AGGREGATION-RULE` summarises the accepted recommendation bundle with explicit anchors and gates.

### §6.2 Pre-registration parent

- [design.md](design.md) §1 (test statistic), §2 (universe and sample period), §10 (decision rule and archive policy) — the immutable pre-registration record. [design.md](design.md) is **not modified** by this addendum.

### §6.3 Implementation surface (downstream)

- `P1-H050-DUAL-SYMBOL-ORCHESTRATOR` — orchestrator restructure for per-symbol fit/predict + per-bar portfolio combination per memo r4 §5; supersedes the bare `P1-H050-UNIVERSE-ES-ONLY` status flag.
- `P1-CYCLE6-FOLD-STATIONARITY` — ADF + KPSS confirmatory-pair decision matrix on per-fold `r_p_gated` and `r_p_uncond`, per memo r4 §6 + Round-3 finding F-3-5; depends on `P1-H050-DUAL-SYMBOL-ORCHESTRATOR`.
- `P1-MISSING-BAR-RATE-EMPIRICAL` — empirical re-tuning of the §2.3 1% missing-bar warn threshold against observed distribution from the first H050 walk-forward run.
- `P1-GATE-RATE-RATIO-EMPIRICAL` — empirical re-tuning of the 3:1 per-symbol gate-firing-rate-ratio warn threshold per memo r4 §6 fifth bullet.
- `P1-H050-CI-DIFFERENTIAL` — closed at the **spec-binding** level by §4.2 (Ledoit-Wolf 2008 differential CI binding); kept open at the **implementation-callable** level via the new evidence-bar-blocking follow-up `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` per §5.3 (no callable LW2008 differential CI exists in [src/skie_ninja/inference/](../../../src/skie_ninja/inference/) as of r2).
- `P1-H050-AGGREGATION-CONVENTION-TEST` — new (per §5.2): unit test asserting numerical equivalence of the addendum-bound arithmetic-return-space aggregate vs the orchestrator's computed aggregate. Evidence-bar-blocking for the first H050 walk-forward run.
- `P1-H050-LW2008-DIFFERENTIAL-CI-IMPL` — new (per §5.3): callable Ledoit-Wolf 2008 studentized time-series bootstrap differential-CI implementation under [src/skie_ninja/inference/stats/](../../../src/skie_ninja/inference/stats/). Evidence-bar-blocking for the first H050 walk-forward run.
- `P1-H050-EXECUTION-WEIGHT-MAP` — out-of-scope: live-execution mapping from return-space-equal-weights to integer-contract positions; deferred to paper-trade phase.
- `P1-H050-MULTIVARIATE-SR` — out-of-scope: Family-3 multivariate-SR test if equal-weighted single-series view ever judged insufficient.
- `P1-H050-MULTIPLE-TEST-FAMILY-RECONCILE` — out-of-scope: pre-existing Romano-Wolf vs Hansen SPA inconsistency in [design.md](design.md) vs [config/hypotheses/H050.yaml](../../../config/hypotheses/H050.yaml).

## §7. Effective-from date and revision

- **Effective from:** 2026-04-24.
- **Revision:** r2 (post-loop-verification under proper subagent isolation; supersedes r1 of same date). r1 was produced under inline-audit substitution per the audit-trail Subagent unavailability note; r2 applies the post-loop-verification findings (Round 4) including (a) §5 implementation directives newly added (M1: arithmetic-vs-log return-space binding; M2: LW2008 differential-CI implementation gap), (b) §3.3.1 σ-value materialisation + Whaley DOI restoration, (c) §2.1 grep-anchored line references, (d) §3.2 attestation-citation tightening, (e) renumbering of former §5 / §6 / §7 → §6 / §7 / §8 to accommodate the new §5.
- **Status:** `designed` (frozen at the same status as parent [design.md](design.md) on user acceptance 2026-04-24; r1 → r2 is an editorial-correction revision that does not alter the binding §1.2 sub-rule 2a, §2.2 sub-rule 3.3a, §3.2 attestation, or §3.3 Path-B gate per the §7 successor-amendment rule below).
- **Owner:** skoir.
- **Successor amendments:** any change to §1.2 (sub-rule 2a), §2.2 (sub-rule 3.3a), §3.2 (substrate-blind-rationale attestation), or §3.3 (Path-B robustness gate) requires a successor hypothesis ID per [design.md](design.md) §10 + ¶22. Editorial corrections that do not alter the binding rule may be applied as a further `rN` within this file with an audit-trail note appended to [docs/audits/audit_trail_2026-04-24_h050-aggregation-addendum.md](../../../docs/audits/audit_trail_2026-04-24_h050-aggregation-addendum.md).

## §8. Gating note for Cell I (Databento backfill)

### §8.1 Forward-gating: addendum precedes Cell I ingest

Acceptance of this addendum is the gating action for Cell I — the Databento GLBX.MDP3 backfill (2015-01-01 → 2025-12-31 for ES + NQ) that resolves `P1-H050-DATA-COVERAGE`. The addendum's commit timestamp must precede the Databento ingest billing/start timestamp; this is the temporal precondition under which the §3.2 substrate-blind-rationale attestation remains audit-defensible. Any auditor can re-check by comparing the two timestamps against `git log --follow` on this file and the Databento ingest provenance in [logs/reproducibility/](../../../logs/reproducibility/).

### §8.2 Backward-gating: no walk-forward runs on incomplete substrate

No H050 walk-forward run governed by this addendum may be executed against the current substrate (ES 2020-2025 + NQ 2020-2024) prior to Cell I completion. Running before Cell I would silently halve the effective leverage of `r_p_*` on bars where the NQ panel is absent (per §1.2 paragraph 3) and would also fail the [design.md](design.md) §2 line 41 "re-runs on extended windows require a successor hypothesis ID" — the current substrate is a *sub-window* of the pre-reg window, and a run on a sub-window is an extended-window deviation in the opposite direction (truncation rather than extension), which equally requires a successor hypothesis ID. The orchestrator implementation tracked under `P1-H050-DUAL-SYMBOL-ORCHESTRATOR` must enforce this gate via a load-time assertion that both per-symbol panels cover `[2015-01-01, 2025-12-31]` before any walk-forward fold is constructed. Failure of that assertion must raise (no silent partial run).
