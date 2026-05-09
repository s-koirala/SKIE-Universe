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
- Grossman, S. J. & Zhou, Z. 1993. Mathematical Finance 3(3):241-276. DOI 10.1111/j.1467-9965.1993.tb00044.x
- Cvitanic, J. & Karatzas, I. 1995. IMA Volumes Vol. 65, Springer, pp. 77-88
  (corrected venue per ADR-0017 Round-1 audit L-3)
- MacLean, Thorp, Ziemba 2010. Kelly Capital Growth, World Scientific, DOI 10.1142/7598
  (fractional-Kelly survey; shrinkage ∈ [0.25, 0.5]; quarter-Kelly is the
  project-operational lower-bound choice, not a normative recommendation
  of the book)
- Faith, C. 2007. Way of the Turtle, McGraw-Hill, ISBN 978-0071486644 (practitioner)

Implementation lands per `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §4.1).
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "kelly_fraction_from_r_multiples",
    "drawdown_constrained_kelly",
    "compute_position_size",
]


def kelly_fraction_from_r_multiples(r_multiples: np.ndarray) -> float:
    """Vince 1990 optimal-f from the IS-fold per-trade R-multiple distribution.

    Per Vince 1990 *Portfolio Management Formulas* Ch. 3 "The Optimal f"
    (practitioner; ISBN 978-0471527565), the optimal-f formulation maximizes
    the geometric mean of (1 + f * R_i) over the empirical R-multiple sample.
    This function returns the optimal-f directly (a fraction in [0, 1])
    BEFORE the project-canonical quarter-Kelly clamp of ADR-0017 §4.1.

    Args:
        r_multiples: 1-D array of per-trade R-multiples from the IS fold.

    Returns:
        Float in [0, 1]; Vince's optimal-f. Caller applies the project-canonical
        quarter-Kelly upper-bound clamp via `clamp(f, 0, 0.25)` per ADR-0017 §4.1
        (single clamp; do NOT multiply-and-clamp — the prior `f * 0.25` formulation
        was a Round-1 audit F-1 dimensional error, corrected in this docstring).

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`.
    """
    raise NotImplementedError(
        "P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE pending; "
        "interface contract per ADR-0017 §4.1 (Vince 1990 optimal-f)"
    )


def drawdown_constrained_kelly(
    r_multiples: np.ndarray,
    *,
    max_dd_target: float = 0.20,
    confidence: float = 0.95,
) -> float:
    """Kelly fraction clamped to satisfy P(MaxDD <= max_dd_target) >= confidence.

    Per Grossman & Zhou 1993 *Mathematical Finance* 3(3):241-276
    DOI 10.1111/j.1467-9965.1993.tb00044.x §3 closed-form approximation,
    extended to discrete R-multiple distributions via Monte Carlo. The
    canonical "20% max-DD survival constraint at 95% confidence" maps to
    a Kelly fraction strictly below the optimal-f of `kelly_fraction_from_r_multiples`.

    Args:
        r_multiples: 1-D array of per-trade R-multiples.
        max_dd_target: Maximum drawdown threshold as fraction of starting
            equity (default 0.20 = 20%, the Turtle convention per Faith 2007
            *practitioner*).
        confidence: Probability the realized MaxDD respects max_dd_target
            (default 0.95).

    Returns:
        Float in [0, kelly_cap] where kelly_cap = 0.25 per ADR-0017 §4.1.

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`.
    """
    raise NotImplementedError(
        "P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE pending; "
        "interface contract per ADR-0017 §4.1 (Grossman-Zhou 1993 §3)"
    )


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
) -> int:
    """Project-canonical position-size computation per ADR-0017 §4.1.

    Returns floor(min(risk-budget-bound, Kelly-bound, capacity-ceiling)).
    The risk-budget bound and the Kelly bound are both expressed as
    integer contract counts; the floor of the minimum is the final position
    size to deploy at entry.

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

    Returns:
        Integer position size to deploy at entry. Always in [0, capacity_ceiling].

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE`.
    """
    raise NotImplementedError(
        "P1-SURVIVAL-CONSTRAINED-SIZING-PRIMITIVE pending; "
        "interface contract per ADR-0017 §4.1"
    )
