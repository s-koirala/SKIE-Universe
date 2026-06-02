---
id: MPV2
title: Regime-switching meta-allocation closed loop — forward-validation against 1/N and buy-and-hold
status: designed
date: 2026-06-02
tier: meta-portfolio
authority: ADR-0029 (center of gravity) + ADR-0020 (meta-portfolio orchestrator) + ADR-0013 (governance)
supersedes: []
frozen_sections: "§1-§7 immutable per ADR-0013 once status: running"
---

# MPV2 — Regime-switching meta-allocation closed loop

> Pre-registration of the **falsifiable center** of the Phase P / ADR-0029 paradigm: a capital allocator over a de-correlated arm library that detects decay (two-tier early-warning + BOCD), reallocates (switching-bandit), and sizes under ergodicity constraints (CPPI floor + joint/fractional Kelly). The single load-bearing question is §1.

## §1 — Hypothesis (FROZEN)

**H_1**: the closed-loop regime-switching allocator's out-of-sample per-session return stream beats **BOTH** (a) equal-weight 1/N over the arm set ([DeMiguel-Garlappi-Uppal 2009](https://doi.org/10.1093/rfs/hhm075) — the stringent benchmark) **AND** (b) buy-and-hold passive-long of the underlying basket, on the primary metric (§7), at 95% one-sided.

**Critical interpretive note** (per ADR-0029 §D-4 + [Lo 2004](https://doi.org/10.3905/jpm.2004.442611) AMH): a NULL is a fully informative outcome. The current MPV1 result is that no allocator beats 1/N at 95% — MPV2 is the properly-powered, per-session, sized, leakage-controlled re-test. If the allocator does not beat 1/N OOS, that is recorded per ADR-0013 non-loss, and §8 additionally reports **which regimes (if any)** the allocator adds value in (the AMH answer may be regime-conditional, not binary).

## §2 — Arm set, sample, calendar (FROZEN)

**Arm set (MPV2 v1)** — one representative per signal class, chosen to MAXIMIZE de-correlation (the precondition for the ergodicity pooling lift, ADR-0029 §D-3.4):

| Arm | Signal class | Native cadence |
|---|---|---|
| H050 | HMM regime-gated directional | 1-min → per-session |
| H055 | mean-reversion (wick-rejection scalp) | intraday → per-session |
| H060 | trend-following (cross-futures TSMOM) | daily |
| H062 | breakout (intraday Donchian) | 5-min → per-session |

H052a (correlates with H050), H053/H054 (null), H065/H067/H068 (H062-family successors, correlated with H062) are RESERVED for MPV2 v2 sensitivity. The P-4 correlation matrix (§3.3) empirically confirms the v1 set is de-correlated; if any v1 pair exceeds a pre-registered correlation ceiling the §8 disposition annotates reduced effective breadth.

**Sample window**: the OOS test fold common to all four arms on the canonical post-Phase-O.10 substrate (SHA `317429e4...`); each arm contributes its per-session OOS return series, calendar-intersected (§3.2). Per-arm OOS right-edges per their design.md §2.

## §3 — Reward construction + alignment invariants (FROZEN)

**§3.1 Per-session reward.** Each arm's reward at session t = its realized per-session log-return on its OOS fold (the `per_session_logret_aggregate` array emitted by its orchestrator per Phase O.13 schema). The common grain is the trading session — every arm, intraday or daily, produces a per-session P/L when its positions are marked/closed at session end.

**§3.2 Calendar alignment.** The cross-arm reward matrix is built by **inner-joining on session date** (the intersection of all arms' OOS session calendars), NOT by `t mod n` cycle-resampling (the MPV1 defect, `P1-MPV1-CALENDAR-ALIGNMENT`). Arms with no position on a session contribute a 0.0 return (flat) on that session, not a dropped row.

**§3.3 Cross-arm correlation diagnostic (P-4).** Before any allocator run, compute the Pearson correlation matrix of the per-session reward columns + the effective breadth (Grinold √breadth analogue). This gates the §1 pooling premise: high positive correlation ⇒ the variance-÷N lift is small and the §8 disposition says so.

**§3.4 Causal-alignment invariant (BLOCKING).** Per ADR-0029 §D-4: (i) arm-k's session-t reward is computed from arm-k positions sized by parameters frozen on data strictly preceding t (walk-forward-frozen — the orchestrators already enforce this via purged/embargoed walk-forward; MPV2 must not re-fit); (ii) the 1/N and buy-and-hold benchmarks are built on the IDENTICAL calendar-aligned matrix; (iii) the full-sample oracle (best-arm-in-hindsight) is a labeled NON-TRADEABLE diagnostic, excluded from the §1 beat-target; (iv) the allocator's decision at session t uses only rewards observed through t−1 (the switching-bandit + early-warning + sizing are all causal by construction). PIT-canaried per the Cycle-4 leak canaries.

## §4 — Allocator (FROZEN)

Per-session closed loop on the §3 matrix, starting $10,000:
1. **Reallocate**: the switching-bandit ([switching_bandit.py](../../../src/skie_ninja/meta/switching_bandit.py); ADR-0018 §D-4) selects arm a_t from rewards observed through t−1.
2. **Detect decay**: the leading early-warning layer ([early_warning.py](../../../src/skie_ninja/inference/early_warning.py); ADR-0029 §D-2) on the allocator's realized per-session path → `derisk_multiplier` (partial de-risk on a precursor crossing); BOCD confirmation gates a harder de-risk.
3. **Size under ergodicity**: the CPPI floor-ratchet overlay ([ergodicity.py](../../../src/skie_ninja/sizing/ergodicity.py); ADR-0029 §D-3) on current equity / running peak → `sizing_scale`; the promotable Kelly multiplier ≤ full-Kelly (super-Kelly sandbox-only, annotated).
4. **Compound**: equity_{t+1} = equity_t × (1 + sizing_scale × derisk_multiplier × r_{a_t,t}).

## §5 — Bandit + threshold selection (FROZEN)

The switching-bandit algorithm (D-UCB / SW-UCB / GLR-klUCB / EXP3.S) is selected by **cumulative-regret minimization on a pre-OOS calibration holdout** (`select_bandit_by_regret`), NOT on the OOS fold. Early-warning + CPPI thresholds are calibrated on the same holdout (`P1-EARLY-WARNING-THRESHOLD-CALIBRATE` + `P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION`). No threshold is hand-set (CLAUDE.md §"Parameter & Prompt Selection").

## §6 — Benchmarks (FROZEN)

- **1/N equal-weight** (primary, DGU 2009): per-session reward = mean across arms, same sizing-free compounding.
- **Buy-and-hold passive-long**: per-session return of the equal-weight underlying-asset long over the same calendar (the §1(b) target).
- **Oracle best-arm-in-hindsight**: NON-TRADEABLE diagnostic only (§3.4-iii).

## §7 — Primary inference (FROZEN)

Primary metric: the **per-session return differential** of the closed-loop allocator minus each benchmark, with a **paired stationary-bootstrap CI** ([Politis-Romano 1994](https://doi.org/10.1080/01621459.1994.10476870) + [Politis-White 2004](https://doi.org/10.1081/ETC-120028836) block length) on the per-session paired differences. H_1 supported iff the lower CI bound excludes zero (one-sided 95%) vs BOTH benchmarks (conjunctive). Reported alongside per ADR-0029 §D-3.1: the median terminal-wealth path AND MPPM(ρ=1) (the time-average growth), with the ensemble mean demoted to a caveated annotation. Survival metrics per ADR-0017 §3 (terminal-wealth-q05, Calmar-differential) and risk-of-ruin per ADR-0017 §4.2.

## §8 — Disposition rule (amendable per ADR-0013/0029)

- **beat-both-conjunctive** (CI excludes zero vs 1/N AND B&H): the paradigm has forward external validity → proceed toward NinjaScript (the allocator is the terminus target per ADR-0029 §D-1).
- **beat-one / null**: recorded per non-loss; §8 reports the regime-conditional breakdown (which regimes, if any, the allocator adds value in) per Lo 2004 AMH.
- The full-sample oracle gap is reported as the achievable-ceiling diagnostic, never as a pass/fail.

## §11.2 — BLOCKING preconditions before the MPV2 run

- `P1-MPV2-PER-SESSION-RETURNS-INTEGRATION` (P-1): each v1 arm re-emits `per_session_logret_aggregate` on the canonical substrate.
- `P1-META-PORTFOLIO-CORRELATION-MATRIX-FIRST-COMPUTE` (P-4): the §3.3 diagnostic.
- `P1-EARLY-WARNING-THRESHOLD-CALIBRATE` + `P1-CPPI-PARAMS-EMPIRICAL-CALIBRATION`: §5 calibration.
- Closed-loop runner + synthetic-validation test (P-5 machinery) — landed 2026-06-02 (see §17).

## §15 — NinjaScript implementation (per ADR-0013 §5)

The allocator (not each arm) is the NinjaScript-terminus target per ADR-0029 §D-1; bridge-mediated (the bandit + early-warning + HMM-dependent arms require Python inference at decision time). Deferred until a beat-both-conjunctive §8 disposition; operator-discretionary per the 2026-05-04 standing decline-ninjascript directive.

## §17 — Revision log

- 2026-06-02: pre-registered at `status: designed`. Arm set {H050, H055, H060, H062} frozen. P-5 closed-loop machinery ([scripts/run_mpv2_closed_loop.py](../../../scripts/run_mpv2_closed_loop.py)) + synthetic validation landed concurrently (Phase P execution); real-data P-1 re-emission is the operator-authorized multi-hour compute that feeds the validated pipeline.
