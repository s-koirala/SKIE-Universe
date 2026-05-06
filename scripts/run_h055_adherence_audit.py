"""H055 v2-rules adherence audit on the 171-trade v1 pilot ledger.

Replays the 171-trade reconciled v1 pilot ledger against the formalized H055
v2 rule-set per design.md §7 (adherence audit) and design.md §10.5 (advisory
disposition — adherence buckets are *informational*, not binding for the
SR_v2 primary inference). The audit answers a single empirical question:
**Conditional on the pilot operator's discretionary execution, do the four
formalized rule-components C1–C4 partition the trade set into buckets whose
P&L distributions differ in the direction predicted by the v2 design?**

Inputs
------

- ``data/external/h055_pilot_ledger/Performance.csv`` —
  171-trade reconciled-to-PDF-totals pilot ledger (fields per
  ``P1-H055-PILOT-CSV-SCHEMA-EXECUTE``).
- T_L (low timeframe) and T_H (high timeframe) bar series at each fill
  timestamp, derived from the same roll-adjusted 1-min substrate that
  feeds the H055 production walk-forward
  ([data/processed/vendor_legacy_1min_roll_adjusted/](../data/processed/vendor_legacy_1min_roll_adjusted/)).

Method (per design.md §7)
-------------------------

For each of the 171 trades, compute four binary adherence flags by replaying
the bar-by-bar state at the fill timestamp on both T_L and T_H:

1. **C1 — trend-gate-state**: ``trend_gate_indicator`` matches the trade
   direction at fill time on T_H.
2. **C2 — body-overlap-coil**: ``body_overlap_rho_1`` exceeded the
   pre-registered threshold (sourced from H055 yaml; pinned during the
   ``calibration_holdout`` window per design.md §3) inside the
   pre-trigger lookback window on T_L.
3. **C3 — level-exhaustion-counter-OK**: ``level_exhaustion_counter`` was
   non-saturated at fill time on T_H.
4. **C4 — ATR-sizing-match**: realized stop distance is within tolerance
   of ``atr_n``-scaled stop sizing at fill time on T_L.

Output
------

Per-trade adherence vector (171 × 4 binary flags + ``all_four`` aggregator)
plus bucketed P&L statistics: mean, median, t-stat, Sharpe, win rate, hit
ratio for each of the 16 binary partitions and for the all-four-adherent vs
not-all-four-adherent contrast (advisory per design.md §10.5).

Statistical procedure
---------------------

The all-four-adherent vs not-all-four-adherent P&L contrast is reported with
two complementary CIs:

1. Hierarchical stationary bootstrap (Politis-Romano 1994 *JASA*
   89(428):1303-1313, [DOI 10.1080/01621459.1994.10476870](https://doi.org/10.1080/01621459.1994.10476870)
   with Politis-White 2004 + Politis-Patton-White 2009 block-length
   selection) — within session for the inner block, across sessions for the
   outer block. Block-length policy + n_bootstrap drawn from H055 yaml's
   ``gates.ledoit_wolf_2008_differential_ci`` block_length and n_bootstrap
   keys.
2. One-sided Wilcoxon rank-sum (Mann-Whitney U) for the median-shift
   hypothesis as a non-parametric robustness anchor; reported alongside (1).

Minimum cell size + missing-cell collapse rule per design.md §7 step 4
(numeric value sourced from H055 yaml — NO magic numbers in this script).

Disposition
-----------

Per design.md §10.5: this audit is **advisory** — it does NOT promote or
demote the SR_v2 primary inference. The audit's role is to (i) identify
which adherence buckets carried disproportionate P&L on the pilot ledger,
informing the v3 successor's gating-rule pre-registration, and (ii) furnish
a falsifiable record that the v2 rule-set was not back-fitted to the pilot
ledger after the fact.

Reproducibility
---------------

All numeric thresholds (alpha, n_bootstrap, block_length policy, minimum
cell size, ATR tolerance, ρ_1 threshold, k_swing) are drawn from
[config/hypotheses/H055.yaml](../config/hypotheses/H055.yaml) at run time —
NO magic numbers in this script. ``rng_seed = config['random_seed']`` is
pinned at the top of :func:`main`.

Body pending follow-up ``P1-H055-ADHERENCE-AUDIT-EXECUTE`` (analysis
machine implementation; raises ``NotImplementedError`` until then).
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    """Replay the 171-trade pilot ledger and emit the bucketed-P&L audit.

    Pipeline
    --------

    1. Parse ``--config`` (path to
       [config/hypotheses/H055.yaml](../config/hypotheses/H055.yaml)),
       ``--pilot-ledger``, ``--substrate-root``, ``--output-dir``.
    2. Load H055 yaml; extract all numeric thresholds (alpha, n_bootstrap,
       block_length policy, ATR tolerance, ρ_1 threshold, k_swing,
       minimum cell size, random_seed).
    3. Load pilot ledger; reconcile pnl total to the published $6,157.75
       per ``P1-H055-PILOT-CSV-SCHEMA-EXECUTE`` (raises if mismatch beyond
       config-pinned tolerance).
    4. For each trade, replay T_L and T_H bar state at fill timestamp;
       compute the four binary adherence flags (C1, C2, C3, C4).
    5. Compute per-bucket P&L stats; run the hierarchical stationary
       bootstrap CI + one-sided Wilcoxon rank-sum on the
       all-four-adherent vs not-all-four-adherent contrast.
    6. Emit per-trade adherence vector + bucketed-P&L summary
       (markdown + JSON + parquet) under
       ``research/01_hypothesis_register/H055/adherence_audit_2026-05-06/``.
    7. Bind sidecar SHA256 → ReproLog model_hash via the project's
       :class:`~skie_ninja.utils.runcontext.RunContext` pattern.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to config/hypotheses/H055.yaml (source of all numeric thresholds).",
    )
    parser.add_argument(
        "--pilot-ledger",
        type=Path,
        required=True,
        help="Path to data/external/h055_pilot_ledger/Performance.csv.",
    )
    parser.add_argument(
        "--substrate-root",
        type=Path,
        required=True,
        help="Root of data/processed/vendor_legacy_1min_roll_adjusted/ for T_L and T_H bar replay.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write the per-trade adherence vector + bucketed-P&L audit.",
    )
    parser.parse_args()

    raise NotImplementedError(
        "Body pending follow-up P1-H055-ADHERENCE-AUDIT-EXECUTE; "
        "analysis machine implementation"
    )


if __name__ == "__main__":
    main()
