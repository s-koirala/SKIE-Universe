"""H052a feature factory — HMM emission features per design.md §3.

Per H052a frozen pre-reg [research/01_hypothesis_register/H052a/design.md](
../../../research/01_hypothesis_register/H052a/design.md) §3 + §15.1 errata
addendum (2026-05-04), the HMM gate consumes 6 emission features:

1. ``rv_realized@1.0`` — Andersen-Bollerslev 1998 realized variance over a
   CV-selected ``{30m, 60m, 120m}`` lookback. Re-uses the existing
   ``rv_realized`` feature factory at
   [src/skie_ninja/features/microstructure/rv_realized.py](
   ../microstructure/rv_realized.py).
2. ``first_hour_sign@1.0`` — directional sign of the first-hour log return
   ``sign(close(10:30 ET) − close(09:30 ET))`` ∈ {−1, 0, +1}.
3. ``gap_size@1.0`` — log gap from prior-session close to current-session
   open: ``log(open(09:30 ET) / close(prior_session_close))``.
4. ``dow_onehot@1.0`` — day-of-week one-hot (Mon-Fri; Friday is reference).
5. ``eth_pre_rth@1.0`` — ETH pre-RTH log return:
   ``log(close(09:29 ET) / close(06:00 ET))``.
6. ``vix_daily@1.0`` — VIX close on T−1, calendar-date joined.

Following the H053 convention ([src/skie_ninja/features/h053/__init__.py](
../h053/__init__.py)), these features are session-grain (one row per
``(symbol, session_date_et)``) and are NOT registered in the project-wide
``FEATURE_REGISTRY``. They are consumed directly by the H052a orchestrator
at ``scripts/run_h052a_walk_forward.py``.

PIT property: every feature produces a value at the H052a entry timestamp
(10:30 ET) using only data observable at or before that timestamp. Per
[ADR-0005](../../../../docs/decisions/ADR-0005-hmm-regime-toolkit.md), the
HMM forward filter consumes these features causally; smoothed posteriors
are training-fold diagnostic only.

References
----------

- Andersen, T. G. & Bollerslev, T. 1998. *Int. Econ. Rev.* 39(4):885-905.
  [doi:10.2307/2527343](https://doi.org/10.2307/2527343).
- H052a frozen pre-reg + §15.1 errata.
"""

from __future__ import annotations

from skie_ninja.features.h052a.features import (
    H052A_FEATURE_NAMES,
    compute_dow_onehot,
    compute_eth_pre_rth,
    compute_first_hour_sign,
    compute_gap_size,
    compute_realized_vol_per_session,
    compute_vix_daily_join,
    compute_h052a_features,
)

__all__ = [
    "H052A_FEATURE_NAMES",
    "compute_dow_onehot",
    "compute_eth_pre_rth",
    "compute_first_hour_sign",
    "compute_gap_size",
    "compute_realized_vol_per_session",
    "compute_vix_daily_join",
    "compute_h052a_features",
]
