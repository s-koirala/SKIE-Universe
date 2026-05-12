"""Survival-constrained sizing primitives — drawdown-constrained Kelly + risk-of-ruin.

Per ADR-0017 §4.1, the project-canonical sizing rule for retail-tier futures strategies
(corrected per Round-1 audit F-1/F-2/F-3 dimensional remediation):

    position_size_t = floor(min(
        per_trade_risk_budget_t / (k * ATR_n_t * multiplier),    # 1% risk in ATR-units
        kelly_fraction_t * equity_t / (entry_price_t * multiplier),  # log-optimal cap
        retail_capacity_ceiling,                                  # ADR-0001 hard cap
    ))

with:
- per_trade_risk_budget_t = 0.01 * equity_t (Turtle 1% convention)
- k = 2.0 (Turtle 2N stop convention)
- kelly_fraction_t = clamp(f_kelly_raw_t, 0, 0.25)  -- quarter-Kelly upper-bound
  applied ONCE via clamp (not multiplied AND clamped); f_kelly_raw is the
  Vince 1990 optimal-f from the IS-fold per-trade R-multiple distribution
  (already a fraction in [0, 1])
- multiplier = contract multiplier (50 for ES, 5 for MES, etc.); price-distance
  * multiplier = dollar-loss-per-contract; entry_price * multiplier = dollar-
  notional-per-contract. tick_value is NOT used in the sizing formula
  (it belongs at the cost-and-slippage layer, not the sizing layer).
- equity_t is *current* account equity (not starting equity) so the rule
  rebases as bankroll grows or shrinks — the structural defense against the
  operator's empirical "size scaled with run-up but not unscaled with
  drawdown" failure mode documented in the 2026-05-01 → 2026-05-07 pilot ledger.

Primary citations:
- Kelly, J. L. 1956. Bell System Technical Journal 35(4):917-926. DOI 10.1002/j.1538-7305.1956.tb03809.x
- Vince, R. 1990. Portfolio Management Formulas, Wiley, ISBN 978-0471527565 (practitioner)
  — Ch. 3 "The Optimal f": maximize G(f) = (1/n) sum log(1 + f * R_i) over f
  with constraint 1 + f * min(R_i) > 0.
- Grossman, S. J. & Zhou, Z. 1993. Mathematical Finance 3(3):241-276. DOI 10.1111/j.1467-9965.1993.tb00044.x
  — drawdown-constrained portfolio choice; the canonical theoretical foundation
  for "maximize growth subject to P(MaxDD > κ) ≤ ε".
- Cvitanic, J. & Karatzas, I. 1995. IMA Volumes Vol. 65, Springer, pp. 77-88
  — extension to general utility (corrected venue per ADR-0017 Round-1 audit L-3).
- MacLean, Thorp, Ziemba 2010. Kelly Capital Growth, World Scientific, DOI 10.1142/7598
  — fractional-Kelly survey; shrinkage ∈ [0.25, 0.5]; quarter-Kelly is the
  project-operational lower-bound choice, not a normative recommendation
  of the book.
- Faith, C. 2007. Way of the Turtle, McGraw-Hill, ISBN 978-0071486644 (practitioner)
  — 1% risk-per-trade + 2N stop convention.

Implementation per `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §4.1).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np
import numpy.typing as npt
from scipy.optimize import minimize_scalar

__all__ = [
    "KELLY_MULTIPLIER_GRID_DEFAULT",
    "KELLY_MULTIPLIER_SUPER_KELLY_THRESHOLD",
    "compute_position_size",
    "drawdown_constrained_kelly",
    "kelly_fraction_from_r_multiples",
    "kelly_multiplier_annotation",
    "select_kelly_multiplier_by_grid",
]

# Project-canonical quarter-Kelly upper-bound clamp per ADR-0017 §4.1.
_KELLY_CAP_DEFAULT = 0.25

# Per ADR-0018 D-2 (2026-05-12 lift of the ADR-0017 §4.1 fixed quarter-Kelly cap):
# grid-searched Kelly multiplier over {0.25, 0.5, 1.0, 1.5, 2.0, 2.5}. The grid
# intentionally extends into the literature-uniformly-dominated super-Kelly
# regime per the operator's $10K-sandbox carve-out; super-Kelly cells (multiplier
# > 1.0) require a `super-kelly-operator-discretionary` KPI annotation per
# ADR-0018 §Consequences. The literature cap at full-Kelly (multiplier = 1.0)
# follows MacLean-Thorp-Ziemba 2010 *Kelly Capital Growth*, World Scientific
# DOI 10.1142/7598 §"Fractional-Kelly shrinkage" — fractional-Kelly shrinkage
# in [0.25, 0.5] is the canonical practitioner range; betting above full-Kelly
# is uniformly dominated in long-run growth + reduces survival probability.
KELLY_MULTIPLIER_GRID_DEFAULT: tuple[float, ...] = (0.25, 0.5, 1.0, 1.5, 2.0, 2.5)
KELLY_MULTIPLIER_SUPER_KELLY_THRESHOLD: float = 1.0

# Numerical floor on the lower bound for f to avoid log(0) at f * min(R) → -1.
_F_LOWER = 1e-9


def kelly_fraction_from_r_multiples(r_multiples: npt.ArrayLike) -> float:
    """Vince 1990 optimal-f from the IS-fold per-trade R-multiple distribution.

    Per Vince 1990 *Portfolio Management Formulas* Ch. 3 "The Optimal f"
    (practitioner; ISBN 978-0471527565), the optimal-f formulation maximizes
    the geometric mean of (1 + f * R_i) over the empirical R-multiple sample:

        G(f) = (1/n) * sum_i log(1 + f * R_i)
        f*   = argmax_{f ∈ (0, f_max)} G(f)

    where `f_max = 1 / |min(R_i)|` when min(R_i) < 0 (the constraint that
    1 + f * R_i > 0 for all i; otherwise log is undefined). When all R_i ≥ 0
    (no losing trades) the optimization is unbounded above and we return
    1.0 as a sentinel value (caller's quarter-Kelly clamp at 0.25 reduces to
    0.25; per Round-1 audit F-1-3, callers should treat the 1.0 return as
    "unbounded; clamp downstream", not as a meaningful Vince f).

    **Semantic interpretation of the returned f** (per Round-1 audit F-1-1):
    The returned `f` is the **fraction-of-bankroll bet on the 1R-stop scale**
    per trade — i.e., when the operator commits `f × equity` dollars to a
    trade with a 1R stop-loss, an R=−1 trade loses exactly `f × equity`. This
    is NOT the same as Vince's HPR-formulation `f` (which uses dollar-P/L
    divided by |max_loss|) without the R-multiple rescaling, and is NOT the
    same as MPT-style `f` (fraction-of-equity-as-notional). The three are
    related by:

        f_R-multiple-form = f_Vince-HPR-form / |min(R)|
        f_MPT-notional   = f_R-multiple-form × (k_atr × atr / entry_price)
                          (futures multiplier cancels both sides)

    **Cross-primitive integration with `compute_position_size`** (per Round-1
    audit F-1-1): the f returned here should be passed as `risk_budget_pct`
    in `compute_position_size`, NOT as `kelly_fraction` — because
    `compute_position_size`'s `kelly_fraction` parameter is interpreted as
    **fraction-of-NOTIONAL** (per ADR-0017 §4.1 worked example), which is
    a separate notional-leverage cap distinct from Vince's per-trade-risk f.
    The recommended usage pattern is:

        f_vince = kelly_fraction_from_r_multiples(rm)
        f_clamped = min(f_vince, 0.25)  # quarter-Kelly cap
        n = compute_position_size(
            equity=equity, atr=atr, multiplier=multiplier, entry_price=entry,
            kelly_fraction=0.25,           # § 4.1 notional-leverage cap (separate)
            capacity_ceiling=cap,
            risk_budget_pct=f_clamped,     # ← Vince's per-trade-risk f goes here
            k_atr=2.0,
        )

    Caller applies the project-canonical quarter-Kelly upper-bound clamp via
    `clamp(f, 0, 0.25)` per ADR-0017 §4.1 (single clamp; do NOT multiply-and-
    clamp — the prior `f * 0.25` formulation was an ADR-0017 R1-audit F-1
    dimensional error, corrected at the ADR layer).

    Args:
        r_multiples: 1-D array of per-trade R-multiples from the IS fold.
            Must contain at least one finite value.

    Returns:
        Float in [0, 1]; Vince's optimal-f in **R-multiple form** per the
        semantic interpretation above. Caller's quarter-Kelly clamp produces
        the project-canonical f for `risk_budget_pct` consumption.

    Raises:
        ValueError: if r_multiples is empty or has no finite values.
    """
    rm = np.asarray(r_multiples, dtype=float).ravel()
    rm = rm[np.isfinite(rm)]
    if rm.size == 0:
        raise ValueError("r_multiples must contain at least one finite value.")

    # Per Round-1 audit F-1-2: derivative check at f=0+.
    # G'(0) = (1/n) sum R_i / 1 = mean(R). If mean(R) ≤ 0, G is non-increasing
    # at f=0+ → optimum is f* = 0 (don't bet). This is mathematically equivalent
    # to the prior `mean(R) <= 0 → 0.0` early-exit but framed as the proper
    # derivative-of-G-at-boundary check rather than a heuristic. Note: G(f)
    # is concave (second derivative -mean(R²/(1+f·R)²) ≤ 0 by Jensen) so the
    # derivative check is sufficient — once G is decreasing at f=0+, it's
    # decreasing throughout the feasible region.
    if rm.mean() <= 0.0:
        return 0.0

    min_r = float(rm.min())
    if min_r >= 0.0:
        # No losing trades — TWR is monotonically increasing in f; return 1.0
        # as a SENTINEL value indicating "unbounded above; clamp downstream"
        # (per Round-1 audit F-1-3). Caller's quarter-Kelly clamp at 0.25
        # bounds the operationally-deployed sizing.
        return 1.0

    # Constraint: 1 + f * min(R) > 0 → f < 1 / |min(R)|.
    f_upper = 1.0 / abs(min_r)
    # Numerical floor below f_upper to keep log finite at the boundary;
    # 1e-6 chosen because xatol=1e-8 below ensures convergence well within
    # the 1e-6 margin, and float64 has ~15 decimal digits of precision so
    # log1p(f * min(R)) with f at 99.9999% of f_upper remains finite and
    # accurate.
    f_upper_safe = f_upper * (1.0 - 1e-6)

    # Maximize G(f) = mean of log(1 + f * R_i) over f ∈ (lower, upper).
    # scipy minimizes; we minimize -G(f). Brent's method ('bounded') assumes
    # unimodality, which is provided by G's concavity (Jensen).
    def neg_g(f: float) -> float:
        if f <= 0.0 or f >= f_upper_safe:
            return float("inf")
        return -float(np.mean(np.log1p(f * rm)))

    result = minimize_scalar(
        neg_g,
        bounds=(_F_LOWER, f_upper_safe),
        method="bounded",
        options={"xatol": 1e-8},
    )
    if not result.success:
        # Fall back to grid search (should not happen for this well-behaved
        # concave problem; path retained for robustness).
        grid = np.linspace(_F_LOWER, f_upper_safe, 1001)
        g_values = np.array([np.mean(np.log1p(f * rm)) for f in grid])
        f_star = float(grid[int(np.argmax(g_values))])
        return max(0.0, min(1.0, f_star))

    f_star = float(result.x)
    # Verify the optimum is interior (G(f*) > G(0) = 0); else return 0.
    # This catches edge cases where the optimization terminated at the lower
    # bound with G ≤ 0.
    if -result.fun <= 0.0:
        return 0.0
    return max(0.0, min(1.0, f_star))


def drawdown_constrained_kelly(
    r_multiples: npt.ArrayLike,
    *,
    max_dd_target: float = 0.20,
    confidence: float = 0.95,
    n_paths: int = 2000,
    n_sessions: int = 252,
    rng_seed: int = 20260508,
    kelly_cap: float = _KELLY_CAP_DEFAULT,
) -> float:
    """Kelly fraction clamped to satisfy P(MaxDD ≤ max_dd_target) ≥ confidence.

    Per Grossman & Zhou 1993 *Mathematical Finance* 3(3):241-276 §3 closed-form
    (under GBM; the empirical R-multiple distribution doesn't satisfy GBM, so
    we use a Monte Carlo bisection-like approach extending the GZ 1993
    framework): bisection-by-grid on f ∈ [0, kelly_cap] to find the largest f
    such that the simulated `P(MaxDD ≤ max_dd_target) ≥ confidence` constraint
    holds. The simulator draws R-multiples from the empirical distribution
    with replacement, applies fixed-fraction-of-equity sizing, and tracks
    MaxDD per path.

    The result is the project-canonical drawdown-constrained Kelly fraction
    used in the §4.1 sizing rule (after the quarter-Kelly upper-bound clamp).

    Args:
        r_multiples: 1-D array of per-trade R-multiples from the IS fold.
        max_dd_target: Maximum drawdown threshold as fraction of starting
            equity (default 0.20 = 20%, the Turtle convention per Faith 2007
            *practitioner*).
        confidence: Probability the realized MaxDD respects max_dd_target
            (default 0.95).
        n_paths: Monte Carlo paths per Kelly grid point (default 2000).
        n_sessions: Forward sessions per path (default 252).
        rng_seed: Deterministic RNG seed (default 20260508).
        kelly_cap: Upper bound for the search (default 0.25 = quarter-Kelly).

    Returns:
        Float in [0, kelly_cap]; the largest Kelly fraction satisfying the
        drawdown-survival constraint at the given confidence.
    """
    rm = np.asarray(r_multiples, dtype=float).ravel()
    rm = rm[np.isfinite(rm)]
    if rm.size == 0:
        raise ValueError("r_multiples must contain at least one finite value.")
    if not (0.0 < max_dd_target <= 1.0):
        raise ValueError(f"max_dd_target must be in (0, 1], got {max_dd_target}.")
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}.")
    if kelly_cap <= 0.0:
        return 0.0

    # Grid over Kelly fractions; for each f compute P(MaxDD ≤ max_dd_target)
    # via Monte Carlo and find the largest f satisfying the constraint.
    grid = np.linspace(0.0, kelly_cap, 26)  # 26 points = 0.01 resolution at kelly_cap=0.25
    rng_master = np.random.default_rng(rng_seed)
    # Pre-draw the path matrix once (shared across Kelly grid for variance
    # reduction). Shape: (n_paths, n_sessions). Each entry is a draw from rm.
    indices = rng_master.integers(0, rm.size, size=(n_paths, n_sessions))
    path_r = rm[indices]  # (n_paths, n_sessions)

    best_f = 0.0
    for f in grid:
        if f <= 0.0:
            best_f = 0.0
            continue
        # Per-session log-return under fixed-fraction-of-equity sizing:
        # equity_{t+1} = equity_t * (1 + f * R_t) → log-return = log(1 + f * R_t).
        # Some R_t can drive 1 + f*R_t ≤ 0 (catastrophic single-trade ruin);
        # we floor at a small positive value so log is finite (these paths
        # are functionally ruined and will exceed max_dd_target in any case).
        gross = 1.0 + f * path_r
        gross = np.maximum(gross, 1e-9)
        log_returns = np.log(gross)
        # Cumulative log-return → equity curve (relative to starting equity 1.0).
        cum_log = np.cumsum(log_returns, axis=1)
        equity = np.exp(cum_log)
        # Prepend baseline 1.0 to detect drawdown from the pre-first-trade peak.
        equity_padded = np.concatenate(
            (np.ones((n_paths, 1)), equity), axis=1
        )
        running_peak = np.maximum.accumulate(equity_padded, axis=1)
        dd = (equity_padded - running_peak) / running_peak  # ≤ 0
        max_dd_per_path = -dd.min(axis=1)  # ≥ 0
        survival_prob = float(np.mean(max_dd_per_path <= max_dd_target))
        if survival_prob >= confidence:
            best_f = float(f)
        else:
            # Grid is monotonic in f (more aggressive sizing → larger MaxDD);
            # once we fail, all larger f will also fail. Break early.
            break
    return best_f


def compute_position_size(
    *,
    equity: float,
    atr: float,
    multiplier: float,
    entry_price: float,
    kelly_fraction: float,
    capacity_ceiling: int,
    k_atr: float = 2.0,
    risk_budget_pct: float = 0.01,
    kelly_multiplier: float = 0.25,
) -> int:
    """Project-canonical position-size computation per ADR-0017 §4.1.

    Returns floor(min(risk-budget-bound, Kelly-bound, capacity-ceiling)).
    The risk-budget bound and the Kelly bound are both expressed as
    integer contract counts; the floor of the minimum is the final position
    size to deploy at entry.

    **Semantic distinction between `kelly_fraction` and `risk_budget_pct`**
    (per Round-1 audit F-1-1; load-bearing for cross-primitive correctness):

    - `risk_budget_pct` is the **per-trade-risk fraction on the 1R-stop scale** —
      "max `risk_budget_pct × equity` dollars at risk per trade if the stop
      is hit". The Vince optimal-f from `kelly_fraction_from_r_multiples`
      (clamped to quarter-Kelly) goes HERE. Default 0.01 = 1% Turtle convention
      per Faith 2007.
    - `kelly_fraction` is the **fraction-of-NOTIONAL leverage cap** —
      "max `kelly_fraction × equity` dollars of GROSS notional exposure per
      trade". This is operationally distinct from Vince's f. Default 0.25
      = quarter-Kelly cap on notional; matches the §4.1 worked-example
      numerics. Should NOT receive a Vince-derived value directly.

    The recommended usage pattern from the H055 calibration-holdout output:

        f_vince = kelly_fraction_from_r_multiples(rm)
        compute_position_size(
            equity=equity, atr=atr, multiplier=multiplier, entry_price=entry,
            kelly_fraction=0.25,        # notional cap; project-default
            capacity_ceiling=cap,
            risk_budget_pct=min(f_vince, 0.25),  # Vince f, quarter-Kelly clamped
        )

    Per Round-1 audit F-1/F-2/F-3 dimensional remediation: tick_value is
    NOT a parameter of the sizing rule (it belongs at the cost-and-slippage
    layer, not the sizing layer). The dollar-loss-per-contract is
    `k_atr × atr × multiplier` (price-distance × multiplier). The
    dollar-notional-per-contract is `entry_price × multiplier`.

    Args:
        equity: Current account equity (NOT starting equity); the rule
            rebases as the bankroll grows or shrinks per ADR-0017 §4.1.
        atr: ATR_n at the entry bar, in price units.
        multiplier: Contract multiplier (e.g., 50 for ES, 5 for MES).
        entry_price: Entry price.
        kelly_fraction: Drawdown-constrained Kelly fraction in [0, 0.25],
            typically the output of `drawdown_constrained_kelly`.
        capacity_ceiling: ADR-0001 retail capacity ceiling for the
            instrument (e.g., 20 for ES, 200 for MES).
        k_atr: Stop-distance multiplier in ATR units (default 2.0; Turtle
            2N convention per Faith 2007 *practitioner*).
        risk_budget_pct: Per-trade risk budget as fraction of equity
            (default 0.01 = 1%; Turtle convention per Faith 2007).
        kelly_multiplier: Per ADR-0018 D-2 (2026-05-12 lift of the §4.1 fixed
            quarter-Kelly cap), a scalar applied to `kelly_fraction` BEFORE
            the cap-clamp. The effective Kelly fraction becomes
            `clamp(kelly_fraction × kelly_multiplier, 0, max(KELLY_MULTIPLIER_GRID_DEFAULT))`
            (= 2.5 upper bound). At the legacy default `kelly_multiplier=0.25`
            with `kelly_fraction=1.0`, the effective Kelly is `0.25` — byte-
            identical to the pre-ADR-0018 behavior under the call pattern
            `compute_position_size(..., kelly_fraction=1.0)` (and structurally
            identical to the legacy formula `kelly_fraction × equity / notional`
            whenever the caller's pre-ADR-0018 `kelly_fraction` value satisfies
            `kelly_fraction == effective_legacy_fraction` and the new caller
            passes that same value with `kelly_multiplier=0.25`). The clamp
            upper bound is now 2.5 (vs the pre-ADR-0018 implicit 1.0 from
            `kelly_fraction ∈ [0, 1]`); the supplied `kelly_fraction` parameter
            range is unchanged at [0, 1]. Multipliers > 1.0 are "super-Kelly"
            per ADR-0018 §Consequences and KPI report cards consuming the
            returned size must carry a `super-kelly-operator-discretionary`
            annotation. Default 0.25 = quarter-Kelly per MacLean-Thorp-Ziemba
            2010 fractional-Kelly shrinkage convention.

    Returns:
        Integer position size to deploy at entry. Always in [0, capacity_ceiling].

    Raises:
        ValueError: if any of equity / atr / multiplier / entry_price /
            capacity_ceiling are non-positive.
    """
    if equity <= 0.0:
        raise ValueError(f"equity must be positive, got {equity}.")
    if atr <= 0.0:
        raise ValueError(f"atr must be positive, got {atr}.")
    if multiplier <= 0.0:
        raise ValueError(f"multiplier must be positive, got {multiplier}.")
    if entry_price <= 0.0:
        raise ValueError(f"entry_price must be positive, got {entry_price}.")
    if capacity_ceiling < 0:
        raise ValueError(f"capacity_ceiling must be non-negative, got {capacity_ceiling}.")
    if not (0.0 <= kelly_fraction <= 1.0):
        raise ValueError(f"kelly_fraction must be in [0, 1], got {kelly_fraction}.")
    if k_atr <= 0.0:
        raise ValueError(f"k_atr must be positive, got {k_atr}.")
    if not (0.0 <= risk_budget_pct <= 1.0):
        raise ValueError(f"risk_budget_pct must be in [0, 1], got {risk_budget_pct}.")
    if kelly_multiplier < 0.0:
        raise ValueError(f"kelly_multiplier must be non-negative, got {kelly_multiplier}.")

    risk_budget_dollars = risk_budget_pct * equity
    dollar_loss_per_contract = k_atr * atr * multiplier
    dollar_notional_per_contract = entry_price * multiplier

    # Per ADR-0018 D-2: multiply BEFORE clamping at the grid-max upper bound
    # (2.5 = max(KELLY_MULTIPLIER_GRID_DEFAULT)). Backward-compatibility note:
    # at the new default `kelly_multiplier=0.25`, the call
    # `compute_position_size(..., kelly_fraction=1.0, kelly_multiplier=0.25)`
    # produces `effective_kelly = 0.25`, structurally identical to the legacy
    # `compute_position_size(..., kelly_fraction=0.25)` (where 0.25 was the
    # legacy quarter-Kelly notional cap). The clamp upper bound moves from
    # 1.0 to 2.5 to accommodate super-Kelly grid cells.
    kelly_cap_upper = max(KELLY_MULTIPLIER_GRID_DEFAULT)
    effective_kelly = max(0.0, min(kelly_fraction * kelly_multiplier, kelly_cap_upper))

    risk_bound = risk_budget_dollars / dollar_loss_per_contract
    kelly_bound = (effective_kelly * equity) / dollar_notional_per_contract

    return int(math.floor(min(risk_bound, kelly_bound, float(capacity_ceiling))))


def kelly_multiplier_annotation(multiplier: float) -> str:
    """Return the KPI annotation string for a chosen Kelly multiplier.

    Per ADR-0018 §Consequences (2026-05-12), every KPI report card that
    consumes a grid-searched Kelly multiplier MUST carry a
    `kelly-multiplier-{value}` annotation; values strictly greater than the
    full-Kelly threshold (1.0; per MacLean-Thorp-Ziemba 2010 *Kelly Capital
    Growth*, World Scientific DOI 10.1142/7598) further require a
    `+super-kelly-operator-discretionary` suffix to flag the literature-
    uniformly-dominated regime.

    Args:
        multiplier: The selected Kelly multiplier (typically from
            `select_kelly_multiplier_by_grid`).

    Returns:
        Annotation string of the form `"kelly-multiplier-{val}"` or
        `"kelly-multiplier-{val}+super-kelly-operator-discretionary"`.
    """
    base = f"kelly-multiplier-{multiplier}"
    if multiplier > KELLY_MULTIPLIER_SUPER_KELLY_THRESHOLD:
        return f"{base}+super-kelly-operator-discretionary"
    return base


def select_kelly_multiplier_by_grid(
    r_multiples: npt.ArrayLike,
    mppm_fn: Callable[..., float],
    grid: tuple[float, ...] = KELLY_MULTIPLIER_GRID_DEFAULT,
    **mppm_kwargs: Any,
) -> dict[str, Any]:
    """Grid-search the Kelly multiplier maximizing MPPM(ρ=1) per ADR-0018 D-2.

    For each candidate multiplier `m ∈ grid`, the implied sized R-multiple
    stream is `sized_R_i = m × raw_kelly_f × R_i` where `raw_kelly_f =
    kelly_fraction_from_r_multiples(R)` is the Vince 1990 optimal-f on the
    empirical R-multiple distribution (R-multiple form per the `kelly_fraction_
    from_r_multiples` semantic). The sized stream is then floored at -1.0
    (no more than total-bankroll loss per trade — the canonical risk-of-ruin
    boundary) and passed to `mppm_fn`. The best-scoring multiplier is
    returned along with the full grid result table.

    Per ADR-0018 D-2 the grid intentionally extends to 2.5× full-Kelly to
    cover the operator's $10K-sandbox carve-out for super-Kelly exploration;
    super-Kelly cells (`m > 1.0`) carry the `super-kelly-operator-discretionary`
    annotation per ADR-0018 §Consequences + MacLean-Thorp-Ziemba 2010 (full-
    Kelly is the literature growth-optimum; multipliers > 1.0 are uniformly
    dominated in expected long-run growth and reduce survival probability).

    Args:
        r_multiples: 1-D array of per-trade R-multiples from the IS fold
            (R-multiple form: R_i = realized P/L / |1R|, with R = -1 for a
            full-stop loss). Must contain at least one finite value.
        mppm_fn: Callable returning MPPM(ρ=1) given a sized R-multiple stream.
            Typically `skie_ninja.inference.mppm.mppm_rho_1`. The callable is
            invoked as `mppm_fn(sized_stream, **mppm_kwargs)`. Passed as a
            parameter (not imported at module level) to avoid circular imports
            between `skie_ninja.sizing` and `skie_ninja.inference.mppm`.
        grid: Tuple of multipliers to evaluate. Defaults to
            `KELLY_MULTIPLIER_GRID_DEFAULT = (0.25, 0.5, 1.0, 1.5, 2.0, 2.5)`
            per ADR-0018 D-2.
        **mppm_kwargs: Additional keyword arguments forwarded to `mppm_fn`.

    Returns:
        Dict with keys:
        - `best_multiplier` (float): the grid cell maximizing MPPM.
        - `best_mppm` (float): the maximum MPPM value.
        - `grid_results` (list[dict]): per-cell `{"multiplier", "mppm"}` rows.
        - `is_super_kelly` (bool): True iff `best_multiplier > 1.0` per
          ADR-0018 §Consequences.
        - `annotation` (str): the KPI annotation per
          `kelly_multiplier_annotation(best_multiplier)`.

    Raises:
        ValueError: if `r_multiples` is empty after finite-filtering, or if
            `grid` is empty.
    """
    rm = np.asarray(r_multiples, dtype=float).ravel()
    rm = rm[np.isfinite(rm)]
    if rm.size == 0:
        raise ValueError("r_multiples must contain at least one finite value.")
    if len(grid) == 0:
        raise ValueError("grid must contain at least one multiplier.")

    raw_kelly_f = kelly_fraction_from_r_multiples(rm)

    grid_results: list[dict[str, float]] = []
    best_multiplier = float(grid[0])
    best_mppm = -math.inf
    found_any_finite = False
    for m in grid:
        sized = np.clip(float(m) * raw_kelly_f * rm, -1.0, None)
        try:
            mppm_val = float(mppm_fn(sized, **mppm_kwargs))
        except Exception:
            mppm_val = float("nan")
        grid_results.append({"multiplier": float(m), "mppm": mppm_val})
        if math.isfinite(mppm_val):
            found_any_finite = True
            if mppm_val > best_mppm:
                best_mppm = mppm_val
                best_multiplier = float(m)

    if not found_any_finite:
        best_mppm = float("nan")
        # When no finite MPPM is recovered, default to the smallest (least-
        # levered) multiplier — the conservative choice consistent with the
        # pure-loss edge case where every multiplier produces a negative
        # MPPM and the smallest cell preserves the most bankroll.
        best_multiplier = float(min(grid))

    is_super_kelly = best_multiplier > KELLY_MULTIPLIER_SUPER_KELLY_THRESHOLD
    return {
        "best_multiplier": best_multiplier,
        "best_mppm": best_mppm,
        "grid_results": grid_results,
        "is_super_kelly": is_super_kelly,
        "annotation": kelly_multiplier_annotation(best_multiplier),
    }
