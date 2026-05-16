---
hypothesis_id: MPV1
schema_version: meta_portfolio_design_v1
status: designed
tier: 2c
created: 2026-05-15
created_by: skoir
description: Meta-portfolio v1 — D-UCB switching-bandit allocator across 5 single-strategy arms (H060 basket + H062 per-symbol legs ES/NQ/MGC/SIL) per ADR-0020 + ADR-0018 D-4. Tests whether Grinold 1989 √breadth multiplier extracts incremental Sharpe over individual marginal arms.
---

# MPV1 — Meta-Portfolio v1

> **First pre-registered meta-portfolio diagnostic across the SKIE-Universe emitted-KPI arms.** Per [ADR-0020](../../docs/decisions/ADR-0020-meta-portfolio-orchestrator.md) §3.2 "one-shot correlation diagnostic before any orchestrator infrastructure lands" framing + [ADR-0018](../../docs/decisions/ADR-0018-regime-conditional-aggressive-growth-paradigm.md) D-4 switching-bandit redirect machinery. The v1 deliverable is a **descriptive diagnostic exhibit** — NOT an inferential MPPM-promotable hypothesis — that maps the cross-arm correlation structure of the 5 emitted-KPI arms and documents the realized cumulative-reward gap between D-UCB / SW-UCB / GLR-klUCB / EXP3.S bandit allocators and a 1/N benchmark on per-fold MPPM(ρ=1) reward sequences.

**Round-1 audit-remediate-loop reframing (2026-05-15)**: Original v0 framing posited an inferential H_1 on cross-arm meta-portfolio MPPM(ρ=1) excess over 1/N. Round-1 quant audit (audit_trail_2026-05-15_mpv1_c9_round1.md) surfaced critical findings F-1-3 (unit error: per-fold MPPM_oos values are already annualized log-wealth rates and cannot be re-averaged as per-round MPPM inputs per GISW 2007 Theorem 1 + ADR-0018 D-1 per-session-aggregation convention), F-1-1 (cycle-resampling 5 NQ rewards 31× to fill T=156 inflates apparent sample size without adding information), F-1-4 (in-sample oracle peeking on the same 156-round reward matrix), and F-1-7 (temporal misalignment across arms with different fold-cadences). Together these foreclose any MPPM-promotable inferential claim at v1.

Per ADR-0020 §3.2 "one-shot correlation diagnostic" framing, v1 deliverable scope is REDUCED to:

- **Descriptive exhibit (a)**: cross-arm Pearson + Spearman correlation matrix on aligned per-fold MPPM values (NO cycle-resampling; use T = min(arm_lengths) after dropping arms with n_rewards < `n_min`).
- **Descriptive exhibit (b)**: realized cumulative-reward + cumulative-regret per bandit algorithm under cycle-resample-FREE construction; explicitly NOT inferential.
- **Bootstrap CI** (paired stationary-bootstrap per Politis-Romano 1994 + Politis-White 2004) on the per-round difference series (bandit_realized - 1_over_N_realized) — reported as the strongest **descriptive** finding but explicitly NOT a Sharpe-promotion gate per ADR-0017 §3.

**Inferential MPV2 deferred**: a Sharpe-promotable meta-portfolio inference requires per-session log-return series from each underlying arm (loaded from re-run orchestrators that emit per-session arrays), calendar-aligned across arms, with T ≥ 30 commonly-dated folds. Tracked under `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` (BLOCKING-BEFORE-MPV2-INFERENCE).

## 1. Descriptive deliverables (v1 — NOT inferential)

Per the Round-1 audit-remediate-loop reframing (above), MPV1 v1 emits **descriptive exhibits only**, no Sharpe-promotable hypothesis:

- **Exhibit A**: cross-arm Pearson + Spearman correlation matrix on per-fold MPPM values from aligned arm subsets (T = min(arm_lengths) after filtering arms with n_rewards < `n_min`).
- **Exhibit B**: 4-bandit-algorithm comparison (D-UCB / SW-UCB / GLR-klUCB / EXP3.S) on the cycle-resample-FREE reward matrix at T = min arm length: realized cumulative-reward, allocation shares, cumulative-regret per [Garivier-Moulines 2011 §3](https://doi.org/10.1007/978-3-642-24412-4_16) construction.
- **Exhibit C**: 1/N equal-weight realized cumulative-reward as the [DeMiguel-Garlappi-Uppal 2009 *RFS* 22(5):1915-1953 DOI 10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075) baseline (naive 1/N on raw per-fold MPPM; NOT capital-weighted vol-normalized 1/N — the latter requires per-session returns deferred to MPV2 per `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION`).
- **Exhibit D**: paired stationary-bootstrap CI on the per-round difference series (bandit_realized − 1_over_N_realized) per [Politis-Romano 1994, *JASA* 89(428):1303-1313 DOI 10.1080/01621459.1994.10476870](https://doi.org/10.1080/01621459.1994.10476870) + [Politis-White 2004, *Econometric Reviews* 23(1):53-70 DOI 10.1081/ETC-120028836](https://doi.org/10.1081/ETC-120028836) block length — reported as descriptive strongest-finding but explicitly NOT a Sharpe-promotion gate per ADR-0017 §3.

**No H_1 / H_0 at v1**: per Round-1 audit-remediate-loop F-1-3 (unit error), F-1-1 (cycle-resample), F-1-4 (oracle peeking), F-1-7 (temporal misalignment), and F-1-6 (Garivier-Moulines 2011 §3.1 regret bound requires stochastic rewards — fold MPPMs are deterministic), the v0 MPPM-promotable inferential framing is foreclosed. v2 inferential meta-portfolio claim is deferred to MPV2 pending the per-session-returns integration follow-up.

## 2. Arms (universe)

Five "arms" loaded from existing emitted-KPI sidecars (no new substrate cost; pure post-processing):

| Arm ID | Source sidecar | Reward sequence length | Description |
|---|---|---:|---|
| H060 | [artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json](../../artifacts/runs/H060/71b00710a17148868b6a5ab610c07ef6/sidecar.json) | 21 | Cross-futures TSMOM monthly daily-cadence basket {ES, NQ, MGC, SIL} |
| H062-ES | [artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json](../../artifacts/runs/H062/16cb68d997c148a2834aad21b73bfdb6/sidecar.json) (per_fold filter) | 25 | Intraday Donchian breakout ES leg |
| H062-NQ | (same; filter symbol=NQ) | 16 | Intraday Donchian breakout NQ leg |
| H062-MGC | (same; filter symbol=MGC) | 26 | Intraday Donchian breakout MGC leg |
| H062-SIL | (same; filter symbol=SIL) | 26 | Intraday Donchian breakout SIL leg |

Reward signal per round: `mppm_oos` value at that fold (per design.md §1 of each underlying hypothesis). Per ADR-0018 D-1 MPPM(ρ=1) is the project-canonical fitness; using per-fold MPPM directly as the bandit-arm reward sequence is consistent with the [Garivier-Moulines 2011](https://doi.org/10.1007/978-3-642-24412-4_16) §2 setup.

**Sample window** (binding):
- Per-arm fold sequences as emitted in their respective KPI report card runs.
- D-UCB rounds: T = `min({len(arm.rewards) for arm in arms}) = 16` (H062-NQ is the shortest).
- Per-round reward: `arms[arm_id].rewards[t mod len(arm)]` — rolling-cycle to handle uneven lengths.

## 3. Estimator — D-UCB switching-bandit allocator

Per [src/skie_ninja/meta/switching_bandit.py](../../src/skie_ninja/meta/switching_bandit.py) `DUCBBandit` (Phase O.1 commit `2f56bed`):
- Discount factor `γ ∈ [0.99, 0.995]`; default 0.99 per Garivier-Moulines 2011 §3.1.
- Exploration constant `B = 2.0` per project-operational default.
- Initial round-robin exploration: each arm explored once before exploitation phase.
- On each round t: pick `a_t = argmax_a [μ̂_a(t) + B √(log(t) / N_a(t))]` per the canonical UCB-with-discount construction.

**Alternative algorithms compared** (per ADR-0018 D-4 cumulative-regret minimization):
- `SWUCBBandit` (sliding-window UCB) at window size 60.
- `GLRKLUCBBandit` (GLR-klUCB; Besson-Kaufmann-Maillard-Seznec 2019) at confidence_alpha=0.05.
- `EXP3SBandit` (Auer-Cesa-Bianchi-Freund-Schapire 2002; EXP3.S adversarial baseline).

Per-arm winner selected by cumulative-regret-minimization on this 16-round sequence per ADR-0018 D-4 + design.md §5.5 of underlying H062.

## 4. Baselines

- **1/N equal-weight** (DeMiguel-Garlappi-Uppal 2009 RFS 22(5)): each round allocate 1/N to each arm; reward = mean(arm rewards at round t).
- **Oracle**: ex-post best-arm-by-mean across the 16 rounds (informational; not a tradeable benchmark).

## 5. Gate thresholds (per ADR-0013 §1 — KPI-only, no binding gates)

- `mppm-rho1-{positive,marginal,negative}` per stationary-bootstrap CI on `T_MPV1`.
- `cumulative-regret-{bounded,unbounded}` per algorithm comparison.
- `allocation-share-{concentrated,diverse}` per Herfindahl-Hirschman index on terminal per-arm allocation distribution.
- `correlation-{low,medium,high}` per pairwise Spearman correlation matrix across the 5 arms.

## 6. Cost model

**ZERO** at v1 — meta-portfolio consumes per-arm KPI cards' fold-MPPM values which already include the underlying arm's per-trade cost assumptions (v1 of each underlying hypothesis was zero-cost research-only). Cost-realism re-emission deferred to MPV2 after underlying v2 emissions land per `P1-MPV1-COST-PROPAGATION-V2`.

## 7. No look-ahead

D-UCB is a sequential algorithm: at round t it observes only rewards from rounds < t and picks `a_t` based on that history. Per-arm reward sequences come from walk-forward OOS folds in the underlying hypothesis runs — themselves PIT-causal per the design.md §7 of each. The meta-portfolio inherits the PIT-causal guarantee.

## 8. Reporting

Per [ADR-0014](../../docs/decisions/ADR-0014-canonical-end-of-simulation-results-summary-tables.md) §3.2 the MPV1 KPI report card MUST include:

1. P/L (cumulative log-wealth, $10K starting capital)
2. Drawdown (realized)
3. MPPM(ρ=1) — primary inference (T_MPV1 = D-UCB - 1/N)
4. Annualised Sharpe (with annualisation declaration)
5. Per-arm allocation share at terminal round
6. Forward 1-year projection (rolling bootstrap on the per-round reward distribution)
7. Cumulative-regret per algorithm + oracle benchmark
8. Cross-arm correlation matrix (Spearman + Pearson)
9. Methodological-correctness annotations

## 9. Pre-registration freeze metadata

- **Substrate** (BINDING): inherits each underlying arm's substrate via the source sidecars. Combined frame SHA via SHA256 over the concatenated SHA256-of-each-arm-sidecar.
- **RNG seed**: `20260515` (Phase O.3 date).
- **Git HEAD at freeze**: pending commit landing.

## 10. Revision log

- **2026-05-15 — initial pre-registration; status `designed`.**
  - Author: skoir.
  - Inheritance: ADR-0013 + ADR-0014 + ADR-0017 + ADR-0018 + ADR-0020 + ADR-0022.
  - Causal-mechanism claim (per ADR-0022 §1.3): `correlation-only` (cross-arm allocation is a portfolio-construction layer; no upstream causal mechanism for arm-vs-arm relative performance).
