---
id: ADR-0006
title: Scope extension — HMM regime track and 0DTE option track
status: proposed
date: 2026-04-20
decision-owner: Lead researcher
supersedes: none
related:
  - docs/decisions/ADR-0001-project-scope.md
  - docs/decisions/ADR-0005-hmm-regime-toolkit.md
  - hypothesis_backlog.md
---

# ADR-0006 — Scope extension: HMM regime track and 0DTE option track

## Status

Proposed. Acceptance follows the first three hypotheses H050/H051/H052 clearing pre-registration audit and entering `running`.

## Context

The existing backlog tiers are defined in [hypothesis_backlog.md](../../hypothesis_backlog.md):

- **Tier 1** — directional conditioning variables (attack 50% AUC wall).
- **Tier 2** — microstructure / flow.
- **Tier 3** — frontier / low published coverage.
- **Tier 4** — execution / portfolio.

Two research directions have accumulated enough backlog weight to warrant explicit scope language, prompting a Tier 2b insertion:

1. **HMM regime track.** Multiple queued hypotheses condition on an unobserved discrete state. A project-level toolkit decision is fixed in [ADR-0005](ADR-0005-hmm-regime-toolkit.md). This ADR only addresses where such hypotheses live in the taxonomy.
2. **0DTE option track.** The sibling repository [s-koirala/SKIE-NINJA-0DTE](https://github.com/s-koirala/SKIE-NINJA-0DTE) (internal project code **SKIE-ORB-CALL**; author Sudarshan "SKIE" Koirala; created 2026-04-19) is live and hosts the 0DTE options research. Its authoritative strategy PDF plus section-level extracts under `research/` (see `research/00-hypothesis.md` through `research/10-glossary.md` and its `CLAUDE.md`) codify the thesis: QQQ first-hour (09:30–10:30 ET) bullish-bias green-rate > 0.50, operationalized as a **long-premium 0DTE/1DTE CALL scalp** (long gamma, long delta, negative theta, near-zero vega). The decision to be made here is whether 0DTE work stays there, migrates in, or shares infrastructure while keeping hypothesis bookkeeping split.

The capacity ceiling from [ADR-0001](ADR-0001-project-scope.md) (≤20 ES, ≤40 NQ contracts) is unchanged. The 0DTE track underlying is **QQQ spot (primary) with NQ/MNQ futures as the equity-layer cross-check**; QQQ share/contract equivalence to the retail ≤40 NQ ceiling is computed per the Phase-3 sizing rule in the sibling repo (delta-equivalent mapping, registered per-hypothesis). Delta and notional caps for the QQQ side will be mirrored into [config/instruments.yaml](../../config/instruments.yaml) in a follow-up.

### Medallion motivation (treat as orienting, not evidential)

The framing is deliberate: the only reproducible Medallion-adjacent take-aways for a retail-scale project are

1. **HMM-style latent state estimation** (Baum's IDA work fed directly into Renaissance's early models — biographical, Zuckerman 2019 *The Man Who Solved the Market*, trade press, Tier-5 orienting).
2. **per-trade edge times many trades** (Mercer's reported ~50.75% hit rate at 1–5 bp edge — Zuckerman 2019, Tier-5 orienting).
3. a project design choice to build a **unified cross-asset feature space** — this is our architectural decision, not a property derivable from any cited page on Medallion. Leverage profile and closed-fund capacity are out of scope.

Medallion performance claims — treated as context, not targets:

- Gross performance ~**63.3% compound gross annualized** per [Cornell (2019), "Medallion Fund: The Ultimate Counterexample?" SSRN id 3504766](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3504766); $100 → $398,723,873 over 1988–2018; no negative annual return over the same period (Cornell confirmed).
- 5-and-44 fee schedule: attributable to Zuckerman 2019 *The Man Who Solved the Market* / Institutional Investor trade press (Tier-5 orienting), not Cornell.
- "2024 Medallion ~30% on $12B internal capital" (Hedgeweek, trade press, Tier-5 orienting).

Retail leverage of 12.5x–20x (Medallion's reported regime) is categorically out of scope under the capacity ceiling.

## Options

### A. Absorb 0DTE work into this repository

Pros: one hypothesis register; unified utils.
Cons: merges two risk profiles (delta-one futures vs short-gamma option structures) into one gate family; loses the clean separation the sibling repo already gives.

### B. Keep 0DTE completely separate

Pros: strict separation of concerns.
Cons: duplicates utils (`paths`, `clock`, `hashing`, `reproducibility`, `runcontext`, `logging_setup`); divergence risk; two multiple-testing families that must be reconciled later anyway (the sibling repo already uses CPCV + PBO + Bonferroni/Holm-Sidak internally per de Prado 2018; our Hansen SPA at the intraday level is additive, not redundant).

### C. Hybrid — shared utils, separate hypothesis tracks

Pros: one source of truth for infrastructure (this repo's `src/skie_ninja/utils/`); the 0DTE repo consumes it as a submodule or installable package; hypothesis IDs remain distinct; each track maintains its own SPA family but with comparable reproducibility logs.
Cons: packaging overhead; a shared-utils contract to respect.

## Decision (proposed)

Adopt **Option C**. Consequences:

- Add a new tier label **Tier 2b — regime/state** to [hypothesis_backlog.md](../../hypothesis_backlog.md) for HMM-native hypotheses.
- 0DTE hypotheses enter **Tier 3** (frontier / low coverage) when they live in this repo; when they live in the sibling repo, they are linked from the backlog but carry sibling-repo IDs.
- All HMM-using hypotheses inherit [ADR-0005](ADR-0005-hmm-regime-toolkit.md); all strategy hypotheses (regardless of track) inherit [ADR-0003](ADR-0003-spa-vs-romanowolf.md) and [ADR-0004](ADR-0004-alpha-and-power-defaults.md).
- First three inaugural hypotheses: H050 (Tier 2b), H051 (Tier 2b), H052 (Tier 3, 0DTE).
- **0DTE motivation (clarified, Round 3):** short-vol / iron-condor framing is removed. The sibling repo SKIE-ORB-CALL operationalizes a **long-premium 0DTE call scalp** conditioned on a first-hour directional signal. The HMM contribution proposed in this ADR is a *regime gate on top of* that binomial signal — not a replacement for it. Any 0DTE hypothesis in this register that treats the SKIE-ORB-CALL signal as a precondition must archive as `null, precondition-failed` if the sibling-repo Phase-1 binomial test fails (green-rate ≤ 0.50).
- **Cross-repo multiple-testing reconciliation (Round 3):** the sibling repo already applies CPCV + PBO + Bonferroni / Holm-Sidak within its own family (per de Prado 2018 *Advances in Financial Machine Learning*, ISBN 978-1119482086). Resolution: **the sibling-repo CPCV gate is declared a prior screen**; only signals surviving that gate enter our Hansen SPA family at the intraday level. Full formal reconciliation (hierarchical BH across families, weight attribution) is deferred to a later **ADR-0007**.

This ADR does **not** amend [CLAUDE.md](../../CLAUDE.md). ADRs govern; CLAUDE.md is a narrative summary updated only when the ADR is accepted and the corresponding infrastructure lands.

## Consequences

- Backlog file gains a new section; existing rows unchanged.
- Capacity ceiling from ADR-0001 binds the 0DTE track: notional caps pre-registered per hypothesis; any hypothesis whose worst-case drawdown at the cap exceeds the pre-registered stop is rejected at design review.
- Reproducibility schema extension from ADR-0005 applies uniformly across tracks.

## Alternatives considered

- Promoting 0DTE to Tier 1 — rejected; published coverage is thinner than index-futures directional literature, and tail-risk makes SPA power analysis harder. Tier 3 is the correct placement for now.
