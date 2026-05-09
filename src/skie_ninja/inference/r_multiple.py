"""R-multiple distribution + mean CI primitives.

Per ADR-0017 §2.4, R = realized per-trade P/L divided by the trade's pre-entry
stop-loss distance × position size. The R-multiple distribution captures the
convex-payoff structure that all retail-replicable success cases share:
Turtles per Faith 2007 *Way of the Turtle* (McGraw-Hill ISBN 978-0071486644;
*practitioner*); CTAs per Hurst-Ooi-Pedersen 2017 J Portfolio Management
44(1):15-29 DOI 10.3905/jpm.2017.44.1.015.

Mean R-multiple >= +0.5 is the operator-canonical convention per Tharp 1998
*Trade Your Way to Financial Freedom* 1st ed. (McGraw-Hill ISBN 978-0070647626;
*practitioner*; per Round-1 audit L-2 the 1998 1st-edition ISBN is 978-0070647626;
the 2007 2nd-edition ISBN is 978-0071478717) indicating "winners pay 1.5R+ on average".

Inferential CI on the mean via stationary-bootstrap per Politis-Romano 1994.

Implementation lands per `P1-R-MULTIPLE-CI-IMPL`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §2.4).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "r_multiple_from_trade",
    "r_multiple_distribution",
    "RMultipleMeanCI",
    "r_multiple_mean_ci_stationary_bootstrap",
]


@dataclass(frozen=True)
class RMultipleMeanCI:
    """Stationary-bootstrap CI on the mean R-multiple."""

    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence: float
    n_bootstrap: int
    block_length: int
    rng_seed: int


def r_multiple_from_trade(
    realized_pnl: float,
    *,
    stop_loss_distance: float,
    position_size: int,
    tick_value: float,
) -> float:
    """R-multiple = realized_pnl / |1R| where 1R = stop_loss_distance * position_size * tick_value.

    Args:
        realized_pnl: Realized per-trade P/L in dollars (signed).
        stop_loss_distance: Pre-entry stop-loss distance in price units (positive).
        position_size: Position size at entry in contracts (positive).
        tick_value: Dollar value per tick.

    Returns:
        Float; the R-multiple. Positive for winners, negative for losers.

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-R-MULTIPLE-CI-IMPL`.
        ValueError: if 1R = 0 (would be raised by the implementation).
    """
    raise NotImplementedError(
        "P1-R-MULTIPLE-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.4"
    )


def r_multiple_distribution(
    per_trade_pnls: np.ndarray,
    per_trade_stop_distances: np.ndarray,
    per_trade_sizes: np.ndarray,
    tick_value: float,
) -> np.ndarray:
    """Vectorized R-multiple computation across a trade ledger."""
    raise NotImplementedError(
        "P1-R-MULTIPLE-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.4"
    )


def r_multiple_mean_ci_stationary_bootstrap(
    r_multiples: np.ndarray,
    *,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    rng_seed: int = 20260508,
) -> RMultipleMeanCI:
    """Politis-Romano 1994 stationary-bootstrap CI on the mean R-multiple."""
    raise NotImplementedError(
        "P1-R-MULTIPLE-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.4"
    )
