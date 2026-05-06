# Audit trail — H055 wick-reversal scalping pre-registration draft

- **Artifact:** [hypothesis_wick_reversal_2026-05-06.md](../../../../skoir/Downloads/skie-h001-staging/hypothesis_wick_reversal_2026-05-06.md) (staging path; not yet relocated into [research/01_hypothesis_register/](../../research/01_hypothesis_register/) pending operator approval of subfolder placement)
- **Loop:** [audit-remediate-loop](../../../../skoir/.claude/skills/audit-remediate-loop) skill, 3-round cap
- **Date:** 2026-05-06
- **Operator:** SKIE
- **Auditors:** quant-auditor + literature-check (parallel each round)
- **Remediator:** general-purpose (single agent each round)

## Summary

| Round | New findings | Critical/Blocker | Major | Minor | Verdict after remediation |
|---|---|---|---|---|---|
| 1 | 31 (14 quant + 17 lit) | 4 | 13 | 14 | proceed |
| 2 | 19 (12 quant + 7 lit) | 2 | 9 | 8 | proceed |
| 3 | 9 (8 quant + 1 lit) | 3 | 6 | 0 | exit-with-residual |

All blockers and majors remediated in their issuing round. Round-3 cap reached per [arXiv 2511.00751](https://arxiv.org/abs/2511.00751) diminishing-returns evidence.

## Round 1 findings

### Quant (F1)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F1-001 | critical | Sharpe bootstrap mismatch (LW2008 circular-block vs SKIE-Universe stationary bootstrap) | Fixed R1: Lo 2002 / Opdyke 2007 single-strategy; LW2008 SB-variant pairwise; PW2004 + PPW2009 block length |
| F1-002 | critical | SPA family did not include Optuna trials → data-snooping leak | Fixed R1: SPA family = full Optuna trial set; reaudited R2/R3, scope conditioned on TPE coverage (B3-2) |
| F1-003 | major | Walk-forward embargo too small for max feature horizon | Fixed R1: explicit embargo formula |
| F1-004 | major | Buy-and-hold benchmark too weak; v1 baseline too short | Fixed R1: TSMOM + no-skill bootstrap added; v1 demoted R2 |
| F1-005 | major | 3 candidate ρ scores with no selection method; ρ2 degenerate | Fixed R1 (calibration); ρ3 dropped R2 (C2-6) |
| F1-006 | major | Kelly variance estimator not specified | Fixed R1; shrinkage edge cases fixed R2 (C2-7); ε derivation added R3 (M3-4) |
| F1-007 | major | Adherence buckets undersized; iid bootstrap invalid | Fixed R1; min-cell rule replaced R2 (C2-4) |
| F1-008 | major | Wrong hypothesis ID (H001 instead of H055) | Fixed R1: renumbered to H055; conformed to template |
| F1-009 | major | Level-exhaustion state contamination at fold boundaries | Fixed R1; embargo unit consistency fixed R2 (C2-8); unit-test concretized R3 (M3-3) |
| F1-010 | major | HAC SE on small windows biased | Fixed R1: Kiefer-Vogelsang 2002 fixed-b for L<60 |
| F1-011 | major | Roll rule not deterministic | Fixed R1: volume + OI 2-session test |
| F1-012 | major | ADF/KPSS misuse on per-trade P&L | Fixed R1: Ljung-Box + Bai-Perron; >50% folds dropped R2 (C2-5) |
| F1-013 | minor | Almgren 2005 DOI to verify | Fixed R1: Loeb 1983 substituted |
| F1-014 | minor | Optuna TPE assumes iid trials | Acknowledged R3 (B3-2) — SPA family scope conditioned on TPE coverage |

### Literature (L1)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| L1-001 | minor | Ziemann → Ziemba spelling | Fixed R1 |
| L1-002 | major | Politis-Romano 1994 doesn't provide automatic block-length | Fixed R1: PW2004 + PPW2009 cited |
| L1-003 | major | LW2008 is for two-sample, not single-strategy CI | Fixed R1: usage scoped correctly |
| L1-004 | critical | Almgren 2005 cite contradicts paper's own finding | Fixed R1: Loeb 1983 substituted (square-root impact); title/pages corrected R2 (C2-11) |
| L1-005 | major | LMW 2000 wrongly attributed for walk-forward methodology | Fixed R1: Tashman 2000 + LdP 2018 Ch. 7 |
| L1-006 | minor | BMP 2002 not about level memory | Fixed R1: BGPW 2004 substituted |
| L1-007 | minor | LMW 2000 wrong for slope-t | Fixed R1: dropped |
| L1-008 | major | NW1994/A1991 attribution swapped | Fixed R1: corrected |
| L1-009 | minor | Hansen 2005 issue number | Non-issue |
| L1-010 | minor | Practitioner flag inconsistency | Fixed R1 |
| L1-011 to L1-017 | minor | Missing publishers/page ranges/ISBNs | Partially fixed; some carried as residual style |
| L1-013 | minor | Bollinger 1992 → Bollinger 2001 *Bollinger on Bollinger Bands* | Fixed R1 |

## Round 2 findings

### Quant (F2)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F2-001 | critical | H055.yaml referenced but does not exist | Fixed R2 (C2-1): inlined into design.md |
| F2-002 | major | SPA family cardinality K unbounded | Fixed R2 (C2-3): K_max=500 power calc; scope cond. on TPE R3 (B3-2) |
| F2-003 | major | Adherence-audit min cell ≥ 30 is folklore | Fixed R2 (C2-4): bootstrap CI half-width rule |
| F2-004 | major | "in > 50% of folds" magic threshold | Fixed R2 (C2-5): per-fold disposition + Holm |
| F2-005 | major | ρ3 tie-break "highest-volume bar" undefended | Fixed R2 (C2-6): ρ3 dropped |
| F2-006 | major | Kelly shrinkage edge cases | Fixed R2 (C2-7); ε derivation added R3 (M3-4) |
| F2-007 | major | Embargo unit-inconsistency | Fixed R2 (C2-8): explicit minute formula |
| F2-008 | major | v1 cadence-mismatch with LW2008 | Fixed R2 (C2-9): v1 demoted; contradiction caught R3 (B3-1) |
| F2-009 | major | Bergmeir-Benitez 2012 mis-co-cited | Fixed R2 (C2-10): dropped |
| F2-010 | minor | cpcv_path_sharpe.py not referenced | Fixed R2 (C2-12) |
| F2-011 | minor | ρ2 retained in calibration despite ex-ante fragility | Fixed R2 (C2-6) |
| F2-012 | minor | No-skill bootstrap under-specified | Fixed R2 (C2-13) |

### Literature (L2)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| L2-001 | critical | Harvey-Liu RFS 2014 DOI resolves to "Co-opted Boards" | Fixed R2 (C2-2): Harvey-Liu 2015 JPM + Harvey-Liu-Zhu 2016 RFS substituted |
| L2-002 | major | Loeb 1983 title and pages wrong | Fixed R2 (C2-11) |
| L2-003 to L2-007 | minor | URL/ISBN/style consistency | Partially applied; rest carried as residual |
| L2-005 | minor | CME continuous-contract methodology link wrong | Fixed R2 (c2m1): vendor-convention practitioner flag |

## Round 3 findings

### Quant (F3)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F3-001 | blocker | v2 vs v1 listed in LW2008 family despite v1 demotion | Fixed R3 (B3-1) |
| F3-002 | blocker | K_max=500 vs ~460k discrete combinations | Fixed R3 (B3-2): scope conditioned on TPE coverage; Bergstra et al. 2011 cited |
| F3-003 | major | Model commit hash missing from Reproducibility | Fixed R3 (M3-1) |
| F3-004 | major | No minimum surviving folds rule | Fixed R3 (M3-2): n_min_folds via HHK-2010 |
| F3-005 | major | Unit-test acceptance criteria deferred | Fixed R3 (M3-3): test path + 3 fixtures + 3 assertions |
| F3-006 | major | Floating parameters (ε, lookbacks, IS/OOS sweep) | Fixed R3 (M3-4): all bounded/derived |
| F3-007 | major | Annualization-by-pilot-cadence inflation | Fixed R3 (M3-5): Lo 2002 §III.B autocorr-adjusted; cadence sensitivity remark |
| F3-008 | major | Power calc claimed not exhibited | Fixed R3 (M3-6): 4×3 MC table placeholder + script reference |

### Literature (L3)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| L3-001 | major | Hamilton §17 misattributed (unit-roots, not slope-t) | Fixed R3 (M3-7): textbook ref dropped |
| L3-002 | blocker | Hsu/Hsu/Kuan DOI resolves to Granger memorial (wrong paper entirely) | Fixed R3 (B3-3): JEF 17(3):471-484 substituted |

## Residual risk after round 3

1. **Document voice / fix-log artifacts (RC-3-D).** Inline fix tags (M#/F#/C#/B3-#) remain throughout the draft. Acceptable for an internal pre-registration; expunge before any external venue submission. Pre-publication scrub task.
2. **K_max coverage caveat.** SPA p-values are conditional on TPE's exploration trajectory rather than on enumeration of the full ~460k discrete grid. The Bergstra et al. 2011 coverage properties bound this, but inferential strength is reduced compared to a finite-grid SPA. Acknowledged in §Inference.
3. **v1 baseline cadence projection.** The v1 half-width target is computed from a 6-session pilot. Realized v2 cadence may diverge; explicit sensitivity is documented but not bounded.
4. **Power simulation cells unfilled.** The 4×3 K × ω power table is registered as a deliverable for [scripts/H055_spa_power_simulation.py](../../scripts/H055_spa_power_simulation.py); cells must be filled before walk-forward dispatch.
5. ~~**NinjaTrader PDF parsing.**~~ **RESOLVED 2026-05-06.** Operator provided structured CSV at [Performance.csv](../../../../skoir/Downloads/Performance.csv), reconciled exactly to PDF totals (171 trades, $6,157.75 gross, 74.85% win rate, $1,440 max W, $-260 max L). Side classification reliable via timestamp ordering. pdfplumber dependency dropped; design.md adherence-audit step 1 swapped to CSV.
6. **Energy contracts (MCL/CL) bar archive.** Only ES/NQ are ingested in the existing SKIE-Universe data dir. MCL/CL/MYM/MGC require additional ingest before walk-forward across the full instrument set.

## Loop empirical justification

Audit cap of 3 rounds chosen per [audit-remediate-loop](../../../../skoir/.claude/skills/audit-remediate-loop) skill — operational tradeoff between cost and coverage; multi-agent self-consistency gains taper at moderate sample counts ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751)). Single-shot baselines on statistical code are weak (DS-1000 Pandas Pass@1 = 0.265 per [arXiv 2211.11501](https://arxiv.org/abs/2211.11501); SciCode 4.6% per [arXiv 2407.13168](https://arxiv.org/abs/2407.13168)) — audit is empirically required, cap is operational.
