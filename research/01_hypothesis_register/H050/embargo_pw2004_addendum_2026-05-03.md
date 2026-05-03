---
name: H050 — Embargo from Politis-White 2004 block length (project-operational)
description: Frames the PW2004 → CV embargo substitution as project-operational with explicit empirical-calibration follow-up
hypothesis_id: H050
type: project
created: 2026-05-03
status: binding
amends: research/01_hypothesis_register/H050/design.md §6 line 72
authority: ADR-0013 §"Frozen pre-registration amendment"
audit_trail: docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md (Round-1 finding F-L-2)
---

# H050 — Embargo from Politis-White 2004 block length (2026-05-03)

This addendum is the binding documentation of an OVERREACH-class citation defect surfaced by Round-1 of the audit-remediate-loop: design.md §6 line 72 specifies the splitter embargo as "max of residual-PACF-based lag and Politis-White optimal block length on stacked residuals", but the Politis-White 2004 estimator was published for STATIONARY BOOTSTRAP block-length selection, not for purged-CV embargo selection. There is no peer-reviewed primary source establishing the equivalence.

## Round-1 audit-remediate-loop F-L-2 verdict

The Round-1 literature-check (severity = critical) verified:

- Politis-White 2004 ([Econometric Reviews 23(1):53-70](https://doi.org/10.1081/ETC-120028836)) estimates `b_sb` (stationary bootstrap) and `b_cb` (circular block bootstrap) optimal block lengths.
- Politis-Romano 1995 stationary bootstrap uses `b_sb` for the i.i.d.-resampling-of-blocks geometric distribution mean.
- AFML §7.4.2 (López de Prado 2018) prescribes embargo as a small-percentage of training set (`h ≈ 0.01·T` for OOS T), NOT derived from a bootstrap estimator.
- No published source in the verified literature establishes that the PW2004 block length is an appropriate embargo for purged-CV.

## Decision (binding from 2026-05-03 forward)

Under ADR-0013 §"Frozen pre-registration amendment" discipline:

- The §6 line 72 text is **NOT EDITED** (per pre-reg immutability).
- The PW2004-derived embargo is treated as a **project-operational** choice without a primary-source canonical justification.
- The orchestrator's F-Q-1 fix (Round-2 closure: `r_bar` sliced to train-only [1:initial_train) before passing to `choose_block_length`) is the corrected implementation: the bootstrap-block-length estimator runs ONLY on training residuals so the splitter geometry is never informed by OOS data.
- A new follow-up `P1-H050-EMBARGO-PRIMARY-SOURCE` is registered to either (a) source a peer-reviewed primary that establishes the substitution's equivalence, (b) revert to AFML §7.4.2 small-percentage embargo + sensitivity analysis, or (c) maintain this addendum's project-operational framing under empirical calibration.

## Mitigation in the orchestrator

The Round-2 F-Q-1 fix at [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) line 2086-2120 (post-patch) computes the PW2004 block length on the train-only slice of `r_bar`, ensuring:

1. Test-fold serial correlation does not influence the splitter embargo (eliminates the F-V3-1 analog leakage class).
2. The fold-zero embargo is the canonical PW2004 estimate from training residuals; subsequent folds inherit the same value.
3. Cross-fold consistency: the embargo is computed once per (symbol, label cfg) and applied uniformly across the walk-forward folds for that combination.

## Empirical calibration plan (`P1-H050-EMBARGO-PRIMARY-SOURCE`)

The next H050 production walk-forward run will produce KPI annotations sensitive to the embargo choice. The KPI report card will include:

- Realized embargo per (symbol, label cfg) — from the PW2004 block length estimate.
- Per-fold OOS Sharpe under the chosen embargo.
- Sensitivity-adjusted per-fold OOS Sharpe under (a) 1.5× embargo, (b) 0.5× embargo, (c) AFML §7.4.2 default `h ≈ 0.01·T`.

Operator review of the sensitivity table at the `kpi-report-emitted` → `ninjascript-implemented` stage transition determines whether the project-operational PW2004 embargo is retained or replaced.

## Cross-references

- Politis, D. N. & White, H. (2004). "Automatic Block-Length Selection for the Dependent Bootstrap." [Econometric Reviews 23(1):53-70](https://doi.org/10.1081/ETC-120028836).
- Patton, A., Politis, D. N. & White, H. (2009). [Econometric Reviews 28(4):372-375](https://doi.org/10.1080/07474930802459016) — PW2004 correction.
- López de Prado, M. (2018). *Advances in Financial Machine Learning*, Wiley, ISBN 978-1-119-48208-6, §7.4.2 "Embargo".
- Politis, D. N. & Romano, J. P. (1994). "The Stationary Bootstrap." [JASA 89(428):1303-1313](https://doi.org/10.1080/01621459.1994.10476870).
- [research/01_hypothesis_register/H050/design.md](design.md) §6 line 72 — frozen pre-reg text (NOT edited)
- [scripts/run_walk_forward.py](../../../scripts/run_walk_forward.py) line 2086-2120 — train-only slicing fix (F-Q-1 closure)
- [docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md](../../../docs/decisions/ADR-0013-permanent-exploration-no-archive-ninjascript-terminus.md) §"Frozen pre-registration amendment" — amendment authority
- [docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md](../../../docs/audits/audit_trail_2026-05-03_h050-orchestrator-leakage-clean.md) — full audit-remediate-loop trail (Round-1 finding F-L-2 + this addendum's binding closure)
