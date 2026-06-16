---
id: ADR-0030
title: Cost-light arm generation as the refined center of gravity (net-of-cost survival is the binding promotion screen)
status: accepted
date: 2026-06-15
decision-owner: operator (SKIE)
supersedes: []
refines:
  - ADR-0029  # §D-1 sequencing — the allocator is GATED on a cost-surviving library; not repudiated
related:
  - ADR-0013  # permanent-exploration / non-loss / NinjaScript terminus (the enabler)
  - ADR-0017  # survival-constrained metric vector (cost-realism is part of it)
  - ADR-0018  # aggressive-growth / MPPM / Kelly grid (preserved)
  - ADR-0020  # meta-portfolio orchestrator — the RIGHT allocator mechanism (pooling), once arms exist
  - ADR-0024  # Lo 2004 AMH canonical philosophy
  - ADR-0025  # abandonment-trigger infrastructure + the NT8-realistic cost model
  - ADR-0028  # cost-friction-dominated-edge annotation (the empirical antecedent)
---

# ADR-0030 — Cost-light arm generation as the refined center of gravity

> **Banner.** [ADR-0029](ADR-0029-regime-switching-meta-allocation-central-program.md) §D-4 pre-registered a falsifiable contingency: *"if the allocator does not beat 1/N OOS, the honest paradigm conclusion is recorded."* The Phase-P MPV2 real-data drive fired that contingency **NULL** — no allocator (switching, causal joint-Kelly, or 1/N) statistically beats buy-and-hold OOS, and *separately* every standalone arm in the library is **cost-erased** under NT8-realistic costs. This ADR **refines** (does not repudiate) the center of gravity: the closed-loop allocator apparatus is **preserved and remains the eventual terminus**, but is **gated on first cultivating a de-correlated arm library whose members individually clear buy-and-hold net of the project's own cost model.** The immediate forward priority shifts from *assembling the allocator* to *generating cost-surviving arms* — the **H068 cost-light lineage**. The organizing principle is the established asset-pricing screen: **net-of-cost survival, with turnover as the primary determinant**. This ADR is durable so future independent sessions read the cost-light arm-generation priority without manual context re-invocation.

## Context

### C-1 — The MPV2 verdict (ADR-0029 §D-4 firing NULL)

The MPV2 closed-loop forward-validation (the falsifiable center of ADR-0029) returned a clean NULL — see [MPV2 KPI report card v1](../../research/01_meta_portfolio/MPV2/MPV2_kpi_report_v1.md). Authoritative causal, CI-backed result over both evaluated windows (numeric source of record: [Phase-P buildout §P-5 milestones 1–5](../../plan/buildouts/phase_p_regime_switching_closed_loop_buildout.md)):

| Allocator | 2-arm {H060, H062} 2020–2025 MPPM(ρ=1) | 3-arm {H055, H060, H062} 2024–2025 MPPM(ρ=1) | beats B&H (one-sided CI excl 0⁺) |
|---|---:|---:|:--:|
| 1/N equal-weight pool | 0.261 | 0.320 | **NO** (lower bound −0.0011 / −0.0007) |
| Buy-and-hold (EW {ES, NQ, MGC, SIL}) | 0.191 | 0.127 | — |
| OOS joint-Kelly (causal) | 0.045 | 0.150 | NO |
| Switching closed-loop (bandit) | −0.020 | −0.020 | NO |

Three load-bearing reads: (i) **no allocator statistically beats buy-and-hold** on either window — every paired-bootstrap lower bound covers zero; (ii) **1/N dominates the "smarter" allocators** — naive equal-weight beats causal joint-Kelly and crushes switching, exactly [DeMiguel-Garlappi-Uppal 2009](https://doi.org/10.1093/rfs/hhm075) under estimation noise on de-correlated arms (effective-number-of-bets 2.989/3); (iii) **switching is the worst mechanism** — on de-correlated arms, holding all N concurrently (pooling) dominates rotating among them.

### C-2 — The library finding (the Phase-P milestone-5 cost gate)

Independently of allocation, the per-arm standalone narrowing found that the **best zero-cost candidate is cost-erased**. H055-C9 ES — the only arm with a genuinely good zero-cost risk-adjusted profile (Calmar +1.35, MPPM_ann +0.325, skew-positive τ₃ +0.10, pure-C#) — has a *thin per-trade edge* (PF 1.07, R-multiple-mean +0.009 ≪ the practitioner +0.5 floor). Under the NT8-realistic conservative-prior cost model ([ADR-0025](ADR-0025-abandonment-trigger-infrastructure.md) §D-3), every C9 cell with a gross-positive zero-cost edge flips catastrophically negative (NQ was already gross-negative pre-cost and is omitted below):

| H055-C9 cell | zero-cost ROI / PF / R-mean | with-cost ROI / PF / R-mean |
|---|---|---|
| ES (the candidate) | +21.9% / 1.07 / +0.009 | **−50.7% / 0.43 / −0.332** |
| MGC | +27.3% / 1.03 / +0.006 | −94.6% / 0.51 / −0.219 |
| SIL | +7.1% / 1.01 / +0.005 | −88.7% / 0.42 / −0.290 |

This is the empirical instance of the [ADR-0028 `cost-friction-dominated-edge-present`](ADR-0028-k6-k7-size-down-cost-friction-edge.md) annotation: a gross-positive edge with no net-of-cost survival. H060 (dominated by passive) and H062 (uninvestable 95.6% max-DD) fail for other reasons. **The complete narrowing conclusion: there is no cost-surviving worthy candidate in the current arm library.**

### C-3 — The synthesis: the binding constraint is the ARM, not the allocator

C-1 and C-2 compose, but they are **two logically distinct deficiencies** (per the Round-1 quant audit), important to keep separate. **(a) Pre-cost mean-edge marginality**: the MPV2 NULL (C-1) was established on the arms' **pre-cost** per-session reward streams, so it shows that even at *zero cost* no allocator — not even naive 1/N — beats B&H in time-average growth (1/N is point-positive but its CI covers zero). **(b) Cost-fragility**: the best standalone arm is additionally cost-erased (C-2). (a) is a gross mean-edge problem; (b) is a net-of-cost problem; the forward net-of-cost screen is the more stringent and subsumes (a) only where the arm has gross edge to erode.

Two further reads tighten the diagnosis. First, the MPV2 NULL has a **mechanism component**: the *switching* loop was dominated by naive 1/N on its own terms (an estimation-noise result, [DGU 2009](https://doi.org/10.1093/rfs/hhm075), partly arm-independent), so "smart" switching/Kelly-optimisation underperforms regardless of arm quality — which is why §D-5 promotes the **pooling** engine (defaulting to 1/N weighting), not the switching loop. Second, an allocator over arms that individually do not clear B&H net of cost cannot beat passive net of cost — *garbage in, garbage out*. So the MPV2 NULL is **not** evidence that allocation-by-pooling over a GOOD library fails (that is untested; §"What is NOT concluded"); it is evidence that (i) the *switching* mechanism is dominated by 1/N and (ii) the library lacks members worth pooling over. The binding upstream constraint is **arm generation under a net-of-cost screen.**

### C-4 — The literature: net-of-cost survival is the established binding screen, turnover the driver, cost-aware design the response

The empirical finding (a PF-1.07 zero-cost candidate flipping to PF 0.43 net of cost) is not idiosyncratic — it is the near-exact analogue of a robust asset-pricing result. Four claim domains, each DOI-verified (external literature search, 2026-06-15; finding directions verified against abstracts to guard the project's tracked finding-inversion regression class):

- **Domain 1 — costs erode documented gross edges.** [Lesmond, Schill & Zhou 2004](https://doi.org/10.1016/S0304-405X(03)00206-X) (*JFE* 71(2):349-380): momentum's gross edge is concentrated in the highest-cost securities, creating "an illusion of profit opportunity when, in fact, none exists." [Marshall, Cahan & Cahan 2008](https://doi.org/10.1016/j.jbankfin.2007.12.011) (*J. Banking & Finance* 32(9):1810-1819, the project's existing cross-asset-futures cite): ~7,000+ technical rules on 15 commodity futures, data-snooping-corrected — **no rule is profitable in isolation**. **Honest qualifier** ([Korajczyk & Sadka 2004](https://doi.org/10.1111/j.1540-6261.2004.00656.x), *J. Finance* 59(3):1039-1082): momentum is *not* uniformly killed — liquidity-weighted, scale-managed constructions survive to large size. Survival is construction-dependent, not impossible.
- **Domain 2 — net-of-cost survival is formally the screen; turnover is the driver.** [Novy-Marx & Velikov 2016](https://doi.org/10.1093/rfs/hhv063) (*RFS* 29(1):104-147 — DOI `hhv063`, **not** an `hhm…` prefix): *"Most anomalies with less than 50% turnover per month generate significant net spreads when designed to mitigate transaction costs; few with higher turnover do."* [Chen & Velikov 2023](https://doi.org/10.1017/S0022109022000874) (*JFQA* 58(3):968-1004): across 204 anomalies, net of spreads + post-publication decay + the modern low-cost era, the *average* net expected return is ≈4 bps/month. Net-of-cost compresses the cross-section toward zero.
- **Domain 3 — the screen is cost-model-dependent (the honest nuance).** [Frazzini, Israel & Moskowitz 2012/2018](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2294498) (SSRN working paper — **no journal DOI**): on ~$1T+ of live institutional fills, real costs are <1/10 of academic estimates, so value/momentum are implementable at scale for the largest executors. But [Patton & Weller 2020](https://doi.org/10.1016/j.jfineco.2020.02.012) (*JFE* 137(2):515-549): measured against *realized* fund returns, "typical mutual funds earn low returns to value and no returns to momentum" — the low-cost result is an upper-decile-executor result. **Implication: a retail-tier program ([ADR-0001](ADR-0001-project-scope.md) capacity ceiling) must screen against its OWN realistic cost model, not a large-arbitrageur's.**
- **Domain 4 — cost-aware DESIGN is the established response.** [Gârleanu & Pedersen 2013](https://doi.org/10.1111/jofi.12080) (*J. Finance* 68(6):2309-2340): the optimal policy embeds cost *inside* the optimization — "aim in front of the target" and "trade partially toward the aim"; faster-decaying signals must be traded less aggressively because their alpha will not outlast the cost. [Novy-Marx & Velikov 2016](https://doi.org/10.1093/rfs/hhv063): the buy/hold spread (asymmetric entry/exit banding) is the single most effective net-spread-preserving construction. [Detzel, Novy-Marx & Velikov 2023](https://doi.org/10.1111/jofi.13225) (*J. Finance* 78(3):1743-1775): failing to use net-of-cost performance for *selection* systematically biases toward high-turnover factors — exactly the failure mode the project's zero-cost sweep exhibited (a thin-edge, cost-fragile candidate looked best on a zero-cost metric).

### C-5 — The forward signal already in hand (H068)

Phase O.18 established that the cost-reduction axis must operate at the **slip layer** (sub-1-tick, empirically calibrated), **not** the N-lot layer (linear cost-scaling kills it; H067 NULL). H068 (cost-light Donchian, ES) was the project's **first cost-light positive realized ROI** (+23.12% at slip=0.5; cost-friction breakeven ratio 2.278 clearing the [ADR-0028](ADR-0028-k6-k7-size-down-cost-friction-edge.md) ≥2 threshold) — edge present but statistically underpowered (n=108 trades). H068 v2 (pre-registered, multi-instrument basket {ES, MGC, SIL}, power-lifted via the Grinold √breadth multiplier) is the cost-aware redesign — the natural candidate for the net-of-cost screen.

## Decision

### D-1 — Refined center of gravity: cost-light arm generation, allocator gated

The project's organizing objective is refined to **cost-light arm generation**: cultivating a de-correlated library of arms that individually clear buy-and-hold **net of the project's own retail cost model**. The [ADR-0029](ADR-0029-regime-switching-meta-allocation-central-program.md) closed-loop allocator apparatus is **preserved in full** (it is built, tested, and valid; §D-4) and **remains the eventual NinjaScript-terminus target** — but it is **gated**: the allocator may not be promoted to the terminus until the library contains **≥ 2 de-correlated arms whose net-of-cost POOLED equity clears B&H with a paired-bootstrap CI** (each arm individually net-of-cost-positive is *sufficient but not necessary* — per the [Peters-Adamou 2022](https://doi.org/10.1098/rsta.2020.0425) pooling lift promoted in §D-5, a pool of marginal-but-de-correlated arms may clear B&H that no single arm does, which is exactly the case the ADR-0020 engine exists to exploit; testing the *pooled* object, not each arm, avoids foreclosing that use case). Until that precondition is met, the immediate forward priority is arm generation, not allocator assembly. This is a **sequencing refinement of ADR-0029 §D-1**, not a supersession.

### D-2 — Net-of-cost survival is the binding promotion screen

Per the Domain 1–4 literature (C-4), a candidate's promotable evaluation is **net of the project's NT8-realistic cost model** ([ADR-0025](ADR-0025-abandonment-trigger-infrastructure.md) §D-3), **never zero-cost**. Zero-cost runs remain admissible as *exploratory upper bounds* (and as the `cost-friction-dominated-edge` zero-cost reference per [ADR-0028](ADR-0028-k6-k7-size-down-cost-friction-edge.md) §D-2), but a `null-is-valuable` disposition or a NinjaScript-promotion recommendation MUST cite the net-of-cost result. Selection-on-zero-cost is the [Detzel-Novy-Marx-Velikov 2023](https://doi.org/10.1111/jofi.13225) over-selection failure mode and is disallowed for promotion decisions. New KPI annotation `net-of-cost-survival-{cleared, failed, untested}` (cascade to glossary + template). Per the [ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §1+§2 no-binding-gates philosophy, this is an **operator-review screen, not a mechanical gate** — research still flows freely; the screen governs the *promotion* recommendation, not the existence of the strategy.

### D-3 — Cost-aware design is the generative principle (turnover is the lever)

Per Domain 4, new arms are **designed for low cost from the start**, not screened after. The design levers, in priority order: (i) **low turnover** — [Novy-Marx & Velikov 2016](https://doi.org/10.1093/rfs/hhv063)'s turnover-is-the-driver finding. The NMV "< 50%/month" figure is the **equity-anomaly monthly-rebalance reference**; for the project's intraday-futures classes it must be re-expressed as **edge-per-trade dominating round-trip cost** (round-trip cost ÷ per-trade R-multiple), of which "< 50%/month turnover" is the equity-frequency instance — exactly the PF-1.07→0.43 mechanism C-2 demonstrates; (ii) **signal-decay-matched trading speed** — [Gârleanu & Pedersen 2013](https://doi.org/10.1111/jofi.12080) "aim in front, trade partially"; do not trade a fast-decaying signal aggressively; (iii) **slip-layer cost-reduction** (sub-1-tick, empirically calibrated), per the Phase O.18 finding, **not** N-lot scaling; (iv) **asymmetric-banding / buy-hold-spread** entry-vs-exit construction where applicable. A new pre-registration's design.md §1.x SHOULD state its expected turnover and its cost-survival mechanism.

### D-4 — H068 cost-light lineage is the active pursuit

The H068 v2 cost-realistic walk-forward is the **first instance** of the D-2 screen and is **BLOCKING-BEFORE-ANY-NINJASCRIPT-COMMIT** (`P1-NINJASCRIPT-CANDIDATE-PURSUE-H068-LINEAGE`). If its multi-instrument basket clears B&H net-of-cost with a CI, it is the first cost-surviving candidate and the library begins to accrue the de-correlated members D-1 requires. If it does not, the cost-light family iterates (slip-sensitivity deepening, longer/wider substrate for power) per the bounded-exploration discipline of [ADR-0027](ADR-0027-operational-discipline-bounded-exploration.md). No arm warrants NinjaScript compilation until a net-of-cost-cleared candidate exists.

### D-5 — Reconciliation with ADR-0029 (the "what changes" table)

| ADR-0029 element | Disposition under ADR-0030 |
|---|---|
| §D-1 center-of-gravity (allocator-first) | **REFINED.** Arm-generation-first; allocator gated on a cost-surviving library. The allocator remains the eventual terminus. |
| §D-2 two-tier early-warning, §D-3 ergodicity sizing, §D-4 switching-bandit, the portfolio engine ([ADR-0020](ADR-0020-meta-portfolio-orchestrator.md)) | **PRESERVED in full** (non-loss; ADR-0013 §4.1) — but the switching-bandit is **DEMOTED as the allocator mechanism** per the next row (pooling dominates). The primitives activate when ≥ 2 cost-surviving de-correlated arms exist. |
| §D-3.4 simultaneous pooling > switching | **PROMOTED to the load-bearing allocator finding.** MPV2 confirmed pooling dominates switching on de-correlated arms; the [ADR-0020](ADR-0020-meta-portfolio-orchestrator.md) portfolio engine is the right ARCHITECTURE — but its DEFAULT weighting on small-N noisy arms should be **naive 1/N** (the empirically-winning pooler: 1/N 0.320/0.261 beat the optimised joint-Kelly 0.150/0.045 per DGU 2009 estimation noise), NOT the inverse-variance/MVO optimum. |
| §D-3.1 median + MPPM headline | **PRESERVED.** |
| §D-4 falsifiable MPV2 claim | **EXECUTED — NULL.** Recorded per ADR-0013 non-loss; this ADR is that recording's strategic consequence. |
| [Lo 2004 AMH](https://doi.org/10.3905/jpm.2004.442611) ([ADR-0024](ADR-0024-paradigm-resolution-h062-aggressive-growth-canonical.md)) | **PRESERVED + reinforced.** The library's marginal, climate-conditional edge IS the AMH null; cost-light generation is the continuous-innovation response. |

### D-6 — Project-objective amendment (CLAUDE.md)

CLAUDE.md §"Research philosophy" center-of-gravity statement is amended (this commit) so future independent sessions read: *the closed-loop allocator is the eventual terminus, gated on a cost-surviving de-correlated arm library; the immediate priority is cost-light arm generation (H068 lineage); net-of-cost survival is the binding promotion screen.* The ADR-0029 closed-loop framing is retained beneath it as the gated objective.

## Alternatives considered

- **(A) Repudiate ADR-0029; delete the allocator apparatus.** Rejected. Non-loss ([ADR-0013](ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §4.1); the apparatus is valid and the simultaneous-pooling-dominates-switching finding is load-bearing. The allocator is gated, not discarded.
- **(B) Keep assembling the allocator on the current library.** Rejected — C-3: an allocator over cost-fragile arms cannot beat passive net of cost (garbage in, garbage out). The binding constraint is upstream.
- **(C) Lower the cost model so the current arms "survive."** Rejected — [Detzel-Novy-Marx-Velikov 2023](https://doi.org/10.1111/jofi.13225): selection on an under-stated cost model systematically over-selects high-turnover junk; this is the exact failure mode to avoid. The cost model is the project's realistic retail one; it is calibrated, not relaxed to flatter a candidate.
- **(D) Adopt large-arbitrageur cost assumptions (Frazzini-Israel-Moskowitz).** Rejected — the project is retail-tier ([ADR-0001](ADR-0001-project-scope.md) capacity ceiling); [Patton-Weller 2020](https://doi.org/10.1016/j.jfineco.2020.02.012) shows the low-cost result does not generalize to typical implementers. Screen against the project's own cost model (Domain 3).
- **(E) Conclude "no edge exists; stop."** Rejected — overreach. The verdict is **library-specific and cost-model-specific** (D-5 honest scope below); H068 cost-light already showed a first net-positive (+23.12%); per Lo 2004 AMH continuous innovation is the response, not surrender.

## Consequences

### What is NOT concluded (honest scope; guards against overreach)

- NOT "allocation-as-a-mechanism fails" — allocation over a *good* (cost-surviving, de-correlated) library is **untested**; the tested library was cost-fragile (C-3).
- NOT "no edge exists anywhere" — H068 cost-light showed a first net-positive realized ROI (C-5).
- NOT a universal cost verdict — it is **cost-model-specific** (Domain 3: a larger executor's costs differ) and **library-specific** (these four signal classes).
- The C-2 cost-erosion figures are **smoke-grade with partly-placeholder conservative-prior fees** (`P1-METALS-ENERGY-CME-FEE-VERIFY`); the *qualitative* erosion (PF 1.07→0.43) is robust to fee precision (too large a move to rescue), but the exact net-of-cost ROIs await empirical slip calibration from paper-trade fills.
- The MPV2 NULL is now CLI-reproducible (`P1-MPV2-REPROLOG-WIRE` closed; sidecar `1980ec1e…`); the qualitative verdict is robust and the exact MPPM values are bound to that sidecar (the only correction from the ad-hoc drive: the 2-arm switching MPPM is **+0.028, not −0.020**).

### New annotation + cascade

`net-of-cost-survival-{cleared, failed, untested}` added to the KPI annotation grammar (glossary + [results-summary template](../../research/_templates/kpi_results_summary_template.md) §8/§9). Cascade follow-ups: `P1-ADR-0030-CLAUDE-MD-CASCADE` (closed this commit), `P1-ADR-0030-DECISIONS-README-CASCADE` (closed this commit), `P1-ADR-0030-GLOSSARY-CASCADE`, `P1-ADR-0030-TEMPLATE-CASCADE`, `P1-ADR-0030-DESIGN-MD-TURNOVER-SECTION` (new design.md §1.x expected-turnover + cost-survival-mechanism stub), `P1-NET-OF-COST-SURVIVAL-ANNOTATION-RETROACTIVE` (label H050/H052a/H053/H055/H060/H062 retroactively).

### Audit-remediate-loop

Round 1 — parallel literature-check (the 9 Domain 1–4 citations: DOI + finding-direction; the `hhv063` vs `hhm…` hazard; FIM-is-a-working-paper; the Korajczyk-Sadka survival qualifier represented honestly) + quant-auditor (the C-3 garbage-in-garbage-out logic; the gating coherence; the cost-erosion arithmetic). Trail: [docs/audits/audit_trail_2026-06-15_adr-0030-cost-light-reframe.md](../audits/audit_trail_2026-06-15_adr-0030-cost-light-reframe.md).

## References

DOI-verified by the 2026-06-15 external literature search; finding directions confirmed against abstracts. Wrong-DOI / working-paper hazards flagged inline.

**Net-of-cost survival (the binding screen)**
- Novy-Marx, R. & Velikov, M. (2016). "A Taxonomy of Anomalies and Their Trading Costs." *Review of Financial Studies* 29(1):104-147. DOI [10.1093/rfs/hhv063](https://doi.org/10.1093/rfs/hhv063). *(DOI prefix `hhv063` — NOT `hhm…`, which belongs to GISW 2007 / DGU 2009 in this project's ledger.)*
- Chen, A.Y. & Velikov, M. (2023). "Zeroing in on the Expected Returns of Anomalies." *J. Financial and Quantitative Analysis* 58(3):968-1004. DOI [10.1017/S0022109022000874](https://doi.org/10.1017/S0022109022000874).

**Costs erode documented edges (+ the survival qualifier)**
- Lesmond, D.A., Schill, M.J. & Zhou, C. (2004). "The illusory nature of momentum profits." *J. Financial Economics* 71(2):349-380. DOI [10.1016/S0304-405X(03)00206-X](https://doi.org/10.1016/S0304-405X(03)00206-X).
- Korajczyk, R.A. & Sadka, R. (2004). "Are Momentum Profits Robust to Trading Costs?" *J. Finance* 59(3):1039-1082. DOI [10.1111/j.1540-6261.2004.00656.x](https://doi.org/10.1111/j.1540-6261.2004.00656.x). *(Qualifier: liquidity-weighted / scale-managed constructions survive — represented honestly, not as monolithic cost-nihilism.)*
- Marshall, B.R., Cahan, R.H. & Cahan, J.M. (2008). "Can commodity futures be profitably traded with quantitative market timing strategies?" *J. Banking & Finance* 32(9):1810-1819. DOI [10.1016/j.jbankfin.2007.12.011](https://doi.org/10.1016/j.jbankfin.2007.12.011). *(NOT the same authors' 2008 *J. Empirical Finance* 15(2) intraday-equity paper — this is the cross-asset-futures cite.)*

**Cost-model dependence (the honest nuance)**
- Frazzini, A., Israel, R. & Moskowitz, T.J. (2012/2018). "Trading Costs of Asset Pricing Anomalies" / "Trading Costs." SSRN working papers [2294498](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2294498) / [3229719](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3229719) (AQR). *Working papers — NO peer-reviewed journal DOI; do not invent one.*
- Patton, A.J. & Weller, B.M. (2020). "What you see is not what you get: The costs of trading market anomalies." *J. Financial Economics* 137(2):515-549. DOI [10.1016/j.jfineco.2020.02.012](https://doi.org/10.1016/j.jfineco.2020.02.012).

**Cost-aware design as the response**
- Gârleanu, N. & Pedersen, L.H. (2013). "Dynamic Trading with Predictable Returns and Transaction Costs." *J. Finance* 68(6):2309-2340. DOI [10.1111/jofi.12080](https://doi.org/10.1111/jofi.12080).
- Detzel, A.L., Novy-Marx, R. & Velikov, M. (2023). "Model Comparison with Transaction Costs." *J. Finance* 78(3):1743-1775. DOI [10.1111/jofi.13225](https://doi.org/10.1111/jofi.13225).

**Internal / inherited**
- DeMiguel, V., Garlappi, L. & Uppal, R. (2009). "Optimal Versus Naive Diversification." *RFS* 22(5):1915-1953. DOI [10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075). [1/N benchmark]
- Lo, A.W. (2004). "The Adaptive Markets Hypothesis." *J. Portfolio Management* 30(5):15-29. DOI [10.3905/jpm.2004.442611](https://doi.org/10.3905/jpm.2004.442611).
