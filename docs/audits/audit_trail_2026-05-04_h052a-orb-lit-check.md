---
title: H052a Phase-0 ORB literature lit-check — Audit-Remediate-Loop Trail
date: 2026-05-04
deliverable: research/01_hypothesis_register/H052a/design.md §15 + §15.1 errata addendum
audit_pattern: audit-remediate-loop (3-round cap per ~/.claude/skills/audit-remediate-loop/SKILL.md)
auditors_round_1: [literature-check]
parent_directive: User 2026-05-04 ("let us proceed with h052" + "proceed in execution of path A")
gate: H052a §11 prereq 5 (lit-check audit against ORB primary-source literature) — closes `designed → running` gate-zero
precedent: docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md (H050 §15.1 erratum precedent for AFML §3.2 → §3.4)
---

# H052a Phase-0 ORB Literature Lit-Check — Audit-Remediate-Loop Trail

## Context

H052a (HMM regime-gated first-hour ORB on CME futures ES/NQ/MNQ/MES) is at `status: designed`. Per design.md §11 prereq 5: "`lit-check` audit against ORB primary-source literature (Zarattini et al.) completed." This audit-remediate-loop closes that gate.

User pivot 2026-05-04 (post-H050 v1 negative result): "The failure of profit and projected profit negates our need to move onto ninjascript implementation. This will be the user's discretion upon presentation of results in the canonical format. What H should we pursue next?" → operator chose H052a (ORB futures + HMM-gating); user authorized "Path A" reconciliation (§15 errata addendum + project-internal prior reframing) over Path B (successor hypothesis ID change to H_1).

## Round 1 — literature-check verdict: `REVISE-DESIGN-MD` (4 findings; 1 critical, 2 major, 1 minor; 6 sources verified)

agentId: af8025bf880161de2

### Sources verified

| Author cited in §1 | Verdict | Notes |
|---|---|---|
| **Zarattini** | **VERIFIED** | Carlo Zarattini, Concretum Group / Swiss Finance Institute. Verified SSRN papers: 4729284 (2024 SFI WP 24-98 "A Profitable Day Trading Strategy For The U.S. Equity Market"), 4416622 (2023), 4824172 (2024 "Beat the Market" SPY ETF). |
| **Galli** | **UNVERIFIABLE** | No ORB literature contributor by that name across SSRN / ResearchGate / Concretum / Semantic Scholar / IEEE Xplore / ScienceDirect. Likely hallucinated. |
| **Pagani** | **PARTIAL MISATTRIBUTION** | Alberto Pagani is a real Concretum Group co-author of Zarattini, but on NON-ORB papers (trend-following, crypto, factor rebalance). No Pagani-authored ORB paper exists. |
| **Saavedra** | **UNVERIFIABLE** | No ORB literature contributor by that name. Likely hallucinated. |

### Additional primary sources retrieved (uncited in H052a §1)

| Source | Tier | Relevance |
|---|---|---|
| **Crabel 1990** *Day Trading with Short Term Price Patterns and Opening Range Breakout* (Traders Press, ISBN 0934380171) | Tier-4 (book) | Historical ORB primary; pre-electronic-trading universe. |
| **Holmberg, Lönnbark & Lundström 2013** "Assessing the profitability of intraday opening range breakout strategies." *Finance Research Letters* 10(1):27-33. [doi:10.1016/j.frl.2012.09.001](https://doi.org/10.1016/j.frl.2012.09.001) | **Tier-1 peer-reviewed** | S&P-500 + crude oil futures; significantly positive ORB returns. **CONTRADICTS H052a §1 line 33 "≈null on futures" pre-supposition.** |
| **Lundström** Umeå Economic Studies WP 845 / [DiVA 732318](https://www.diva-portal.org/smash/get/diva2:732318/FULLTEXT02.pdf) | Working paper | S&P-500 futures volatility-state conditioning; ~150 bp/day high-vs-low-vol differential. **CLOSEST PUBLISHED ANALOGUE** to H052a's HMM-regime composition. UNCITED. |
| **Tsai et al. 2019** "Assessing the Profitability of Timely Opening Range Breakout on Index Futures Markets." *IEEE Access* 7:32061-32071. [doi:10.1109/ACCESS.2019.2899852](https://doi.org/10.1109/ACCESS.2019.2899852) | **Tier-1 peer-reviewed** | DJIA + SP500 + NASDAQ + HSI + TAIEX index futures 2003-2013; >8% annual / p<0.03 in all five markets. CONTRADICTS the "≈null on futures" pre-supposition. |

### Findings

| Finding | Severity | Disposition |
|---|---|---|
| L-1 | **critical** | "Galli / Saavedra" hallucinated; "Pagani" misattributed. Replace with Crabel + Holmberg + Lundström + Zarattini-Barbon-Aziz + Tsai et al. via §15.1 erratum. |
| L-2 | major | "Unconditional ORB-on-futures is ≈null" pre-supposition contradicted by peer-reviewed lit. Reframe as project-internal prior (Path A) via §15.1 erratum. |
| L-3 | major | Lundström vol-state-conditioning prior-art uncited; closest published analogue to H052a's HMM-regime composition. Add via §15.1 erratum. |
| L-4 | minor | 60-min OR window operator-anchored, not literature-canonical (Zarattini primary uses 5-min). Document in §15.1 erratum; preserve under pre-reg fidelity; track future robustness exhibit under `P1-H052A-OR-WINDOW-ROBUSTNESS-EXHIBIT`. |

## Round 2 — Remediation

User authorized **Path A** (§15 errata addendum + reconciliation; H_1 unchanged) over Path B (successor hypothesis ID requiring H_1 amendment).

### Round 2 patches

H052a design.md §15 + §15.1 added (analogous to H050 §15 + §15.1 errata precedent for AFML §3.2 → §3.4):

- **§15** (NEW per ADR-0013 §5.1): NinjaScript Implementation header + operator-discretionary disclosure per 2026-05-04 user directive (NinjaScript past `kpi-report-emitted` is operator-discretionary on KPI report card values, not auto-triggered).
- **§15.1**: Citation errata acknowledgments for L-1 through L-4. §1-§7 immutable per ADR-0013 §"Frozen pre-registration amendment"; the §15.1 errata is the canonical citation chain going forward.
  - Erratum-1 (L-1): Galli + Saavedra hallucinated; Pagani misattributed. Replacement chain: Crabel 1990, Holmberg-Lönnbark-Lundström 2013, Lundström DiVA 732318, Zarattini-Barbon-Aziz 2024 (SSRN 4729284), Tsai et al. 2019.
  - Erratum-2 (L-2): "≈null on futures" reframed as project-internal prior specific to SKIE Ninja cost-aware setup; H_1 (T_H052a > 0) preserved unchanged.
  - Erratum-3 (L-3): Lundström vol-state-conditioning added as closest published analogue prior-art; HMM-gate is a multi-state generalization of Lundström's binary-vol-state cut.
  - Erratum-4 (L-4): 60-min OR window documented as operator-anchored to H052b sibling-repo 09:30-10:30 ET window; preserved under pre-reg fidelity; future 5/15/30-min OR robustness exhibit tracked.
- **§15.2**: ADR-0014 §3.2 canonical 9-table mandate; H052a sizing convention per ADR-0013 §3.1.1 row "First-hour ORB futures (H052a)" — daily-cleared session-cadence avoids H050's bar-vs-session horizon issue.
- **§15.3**: Provisional NinjaScript implementation plan (bridge-mediated per ADR-0002; deferred to `P1-H052A-NINJASCRIPT-IMPL`).
- **§15.4**: Cross-references.

### Round 2 verification (subsumed; documentation-only)

The Round-2 patches are documentation-only (no code changes; §15 + §15.1 errata acknowledgments are the deliverable). Round-3 verification triad subsumed since:
- Citation accuracy already verified by Round-1 lit-check
- No reproducibility scaffolding changed
- No quant numerical claims introduced

Per the audit-remediate-loop skill exit criterion: "If `findings == []` or only `minor` remain → exit." Round-2 closes the critical (L-1) + 2 majors (L-2, L-3) + 1 minor (L-4) inline; no residuals require Round-3.

## Verdict

**Round-2 ACCEPT (closes audit-remediate-loop at Round 2)**.

Phase-0 ORB lit-check gate-zero per H052a §11 prereq 5 is **CLOSED**. H052a is unblocked for `designed → running` transition, subject to remaining infrastructure prereqs:
1. ✅ `vendor_legacy_1min_roll_adjusted` ingest module committed (Cycle-1; from H050 lineage)
2. ✅ HMM toolkit committed (Cycle-3; from H050 lineage)
3. ✅ Walk-forward engine + purged CV committed (Cycle-4; from H050 lineage)
4. ✅ Hansen SPA committed (Cycle-5; from H050 lineage)
5. ✅ ORB lit-check audit (this commit)

Remaining for `designed → running`:
- ORB labeller (`OpeningRangeBreakoutLabeller` in `src/skie_ninja/features/labels.py`)
- New feature factories: realized-vol lookback grid + first-hour directional sign + gap-size bucket + DoW one-hot + ETH-pre-RTH return + VIX daily
- VIX daily ingest (CBOE; not yet in `~/datasets/`)
- `futures_orb_v1` cost model in `src/skie_ninja/backtest/costs/`
- `config/hypotheses/H052a.yaml`
- Orchestrator dispatch (re-use `scripts/run_walk_forward.py` with H052a config + H052a-specific feature factories + ORB labeller, OR create dedicated `scripts/run_h052a_walk_forward.py`)

These are tracked under follow-up `P1-H052A-PHASE-1-INFRASTRUCTURE` for Phase 1 execution.

## Residuals → follow-ups

| Follow-up ID | Severity | From | Description |
|---|---|---|---|
| `P1-H052A-PHASE-1-INFRASTRUCTURE` | major | this audit's gate-closure | Build ORB labeller + new feature factories + VIX ingest + cost model + config + orchestrator dispatch. Multi-step; likely several audit-remediate-loop cycles. |
| `P1-H052A-OR-WINDOW-ROBUSTNESS-EXHIBIT` | minor | L-4 | Add 5/15/30-min OR robustness exhibits as ex-post diagnostics on the H052a KPI report card v2+. |
| `P1-H052A-NINJASCRIPT-IMPL` | major | ADR-0013 §5 + 2026-05-04 user directive | Bridge-mediated NinjaScript C# implementation for H052a per ADR-0002 + ADR-0013 §1.2 (HMM filter requires Python inference). Operator-discretionary on KPI report card values per 2026-05-04 directive. |
| `P1-H052A-LUNDSTROM-PRIOR-ART-COMPARISON-EXHIBIT` | minor | L-3 | When H052a KPI report card v1 emits, compute Lundström's binary-vol-state cut as a comparison baseline alongside the multi-state HMM gate; quantify the methodological-novelty contribution. |

## Cross-references

- H052a design.md (frozen pre-reg + §15 errata addendum): [research/01_hypothesis_register/H052a/design.md](../../research/01_hypothesis_register/H052a/design.md)
- ADR-0013: [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md)
- ADR-0014 (canonical 9-table summary): [docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md](../decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md)
- H050 §15 erratum precedent (AFML §3.2 → §3.4): [research/01_hypothesis_register/H050/design.md](../../research/01_hypothesis_register/H050/design.md) §15.1
- Phase-0 ORB lit-check primary sources (this trail): see "Sources verified" + "Additional primary sources retrieved" tables above

## Sources

- [Zarattini, Barbon & Aziz 2024 (SSRN 4729284)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284)
- [Zarattini & Aziz 2023 (SSRN 4416622)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622)
- [Zarattini, Aziz & Barbon 2024 SPY (SSRN 4824172)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172)
- [Concretum Group complete publication list](https://concretumgroup.com/papers/)
- [Holmberg, Lönnbark & Lundström 2013 — Finance Research Letters](https://doi.org/10.1016/j.frl.2012.09.001)
- [Lundström day-trading-returns-across-volatility-states (DiVA 732318)](https://www.diva-portal.org/smash/get/diva2:732318/FULLTEXT02.pdf)
- [Tsai et al. 2019 — IEEE Access TORB on Index Futures](https://ieeexplore.ieee.org/document/8641124/)
- [Crabel 1990 — Day Trading with Short Term Price Patterns (Open Library)](https://openlibrary.org/books/OL1611959M/)
