"""R-multiple distribution + mean CI primitives.

Per ADR-0017 §2.4, R = realized per-trade P/L divided by the trade's pre-entry
stop-loss distance × position size × multiplier. The R-multiple distribution
captures the convex-payoff structure that all retail-replicable success cases
share: Turtles per Faith 2007 *Way of the Turtle* (McGraw-Hill ISBN
978-0071486644; *practitioner*); CTAs per Hurst-Ooi-Pedersen 2017 J Portfolio
Management 44(1):15-29 DOI 10.3905/jpm.2017.44.1.015.

Mean R-multiple >= +0.5 is the operator-canonical convention per Tharp 1998
*Trade Your Way to Financial Freedom* 1st ed. (McGraw-Hill ISBN 978-0070647626;
*practitioner*; per Round-1 audit L-2 the 1998 1st-edition ISBN is 978-0070647626;
the 2007 2nd-edition ISBN is 978-0071478717) indicating "winners pay 1.5R+ on average".

Inferential CI on the mean via stationary-bootstrap per Politis-Romano 1994.

Implementation per `P1-R-MULTIPLE-CI-IMPL` (BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH
per ADR-0017 §2.4).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    politis_white_block_length,
    stationary_bootstrap_indices,
)

__all__ = [
    "RMultipleMeanCI",
    "r_multiple_distribution",
    "r_multiple_from_trade",
    "r_multiple_mean_ci_stationary_bootstrap",
]


@dataclass(frozen=True)
class RMultipleMeanCI:
    """Stationary-bootstrap CI on the mean R-multiple.

    Provenance fields (per Round-1 audit F-6):
    - block_length_method: "politis_white_2004" or "operator_supplied".

    Power annotation (per Round-1 audit F-7):
    - underpowered: True if input n < 30 trades. PW2004 + Politis-Romano 1994
      bootstrap requires only n ≥ 4, but R-multiple analysis on small samples
      produces wide CIs and unreliable `excludes_zero`/`excludes_half` flags.
      The H055 pilot-ledger context (n=171 trades subsampled by instrument-class
      yielding ~30 trades per class) sits at this boundary. Operator should
      treat `underpowered=True` results as descriptive-only.
    """

    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence: float
    n_bootstrap: int
    block_length: float
    rng_seed: int
    excludes_zero: bool
    excludes_half: bool  # supplementary annotation per ADR-0017 §2.4: r-multiple-mean >= +0.5
    block_length_method: str = "politis_white_2004"
    underpowered: bool = False


def r_multiple_from_trade(
    realized_pnl: float,
    *,
    stop_loss_distance: float,
    position_size: int,
    multiplier: float,
) -> float:
    """R-multiple = realized_pnl / |1R| where 1R = stop_loss_distance * position_size * multiplier (dollars).

    Per ADR-0017 §2.4 (corrected per Round-1 audit F-1/F-2/F-3 dimensional
    remediation): the dollar-value of the pre-entry stop is
    `stop_loss_distance × position_size × multiplier` (price-distance × position
    × dollar-per-point). tick_value is NOT a parameter (it belongs at the
    cost-and-slippage layer per the ADR-0017 §4.1 sizing-primitive convention).

    Args:
        realized_pnl: Realized per-trade P/L in dollars (signed; positive for
            winners, negative for losers).
        stop_loss_distance: Pre-entry stop-loss distance in PRICE units
            (positive; e.g., for ES at 5000 with stop at 4990, distance = 10).
        position_size: Position size at entry in contracts (positive integer).
        multiplier: Contract multiplier in dollars-per-point (e.g., 50 for ES,
            5 for MES, 1000 for full CL).

    Returns:
        Float; the R-multiple. Positive for winners (realized > 0), negative for
        losers (realized < 0). |R| = 1.0 means the trade closed exactly at 1R.

    Raises:
        ValueError: if 1R = 0 (zero stop-distance, zero position, or zero
            multiplier — would produce undefined R-multiple).
    """
    one_r_dollars = float(stop_loss_distance) * float(position_size) * float(multiplier)
    if one_r_dollars <= 0.0:
        raise ValueError(
            "1R is non-positive: stop_loss_distance × position_size × multiplier = "
            f"{stop_loss_distance} × {position_size} × {multiplier} = {one_r_dollars}. "
            "All three must be strictly positive."
        )
    return float(realized_pnl) / one_r_dollars


def r_multiple_distribution(
    per_trade_pnls: npt.ArrayLike,
    per_trade_stop_distances: npt.ArrayLike,
    per_trade_sizes: npt.ArrayLike,
    multiplier: float,
) -> np.ndarray:
    """Vectorized R-multiple computation across a trade ledger.

    Args:
        per_trade_pnls: 1-D array of realized per-trade P/L in dollars (signed).
        per_trade_stop_distances: 1-D array of pre-entry stop distances in price
            units (positive); must align with per_trade_pnls.
        per_trade_sizes: 1-D array of position sizes (positive integers); must
            align with per_trade_pnls.
        multiplier: Contract multiplier in dollars-per-point (single value; assumes
            all trades are on the same instrument).

    Returns:
        1-D array of R-multiples; same length as per_trade_pnls.

    Raises:
        ValueError: if any 1R = 0 in the ledger, or if input arrays have
            mismatched lengths.
    """
    pnls = np.asarray(per_trade_pnls, dtype=float).ravel()
    stops = np.asarray(per_trade_stop_distances, dtype=float).ravel()
    sizes = np.asarray(per_trade_sizes, dtype=float).ravel()

    if not (pnls.shape == stops.shape == sizes.shape):
        raise ValueError(
            f"Length mismatch: pnls={pnls.shape}, stops={stops.shape}, sizes={sizes.shape}."
        )
    if pnls.size == 0:
        return np.empty(0, dtype=float)

    one_r_dollars = stops * sizes * float(multiplier)
    if np.any(one_r_dollars <= 0.0):
        bad_idx = int(np.argmin(one_r_dollars))
        raise ValueError(
            f"Trade index {bad_idx} has non-positive 1R: "
            f"stop={stops[bad_idx]}, size={sizes[bad_idx]}, multiplier={multiplier}."
        )
    return pnls / one_r_dollars


def r_multiple_mean_ci_stationary_bootstrap(
    r_multiples: npt.ArrayLike,
    *,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    rng_seed: int = 20260508,
    block_length: float | None = None,
) -> RMultipleMeanCI:
    """Politis-Romano 1994 stationary-bootstrap CI on the mean R-multiple.

    Block length is selected per Politis-White 2004 + Patton-Politis-White 2009
    correction on the per-trade R-multiple series; if `block_length` is supplied
    explicitly, it overrides the auto-selection.

    Args:
        r_multiples: 1-D array of per-trade R-multiples.
        n_bootstrap: Number of bootstrap replicates (default 1,000).
        confidence: Two-sided CI coverage in (0, 1) (default 0.95).
        rng_seed: Deterministic RNG seed (default 20260508).
        block_length: Optional explicit block length; if None, auto-selected.

    Returns:
        RMultipleMeanCI with point estimate + percentile CI bounds + provenance.

    Raises:
        ValueError: if r_multiples is empty or has fewer than 4 trades (PW2004
            requires n >= 4 for block-length selection).
    """
    rm = np.asarray(r_multiples, dtype=float).ravel()
    n = rm.size
    if n < 4:
        raise ValueError(f"r_multiples requires n >= 4 trades, got {n}.")
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}.")
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}.")

    if block_length is None:
        sel: BlockLengthSelection = politis_white_block_length(rm, bootstrap_type="stationary")
        bl = float(sel.block_length)
        bl_method = "politis_white_2004"
    else:
        if block_length < 1.0:
            raise ValueError(f"block_length must be >= 1, got {block_length}.")
        bl = float(block_length)
        bl_method = "operator_supplied"

    point = float(rm.mean())
    rng = np.random.default_rng(rng_seed)
    boot_means = np.empty(n_bootstrap, dtype=float)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n=n, block_length=bl, rng=rng)
        boot_means[b] = float(rm[idx].mean())

    alpha = 1.0 - confidence
    lo = float(np.quantile(boot_means, alpha / 2.0))
    hi = float(np.quantile(boot_means, 1.0 - alpha / 2.0))

    # Per Round-1 audit F-7: small-sample power annotation. n < 30 is the
    # operationally-typical boundary where R-multiple CI becomes unreliable
    # (matches the H055 pilot-ledger per-instrument-class subsample size).
    underpowered = bool(n < 30)

    return RMultipleMeanCI(
        point_estimate=point,
        ci_lower=lo,
        ci_upper=hi,
        confidence=confidence,
        n_bootstrap=n_bootstrap,
        block_length=bl,
        rng_seed=rng_seed,
        excludes_zero=(lo > 0.0 or hi < 0.0),
        excludes_half=(lo > 0.5 or hi < 0.5),
        block_length_method=bl_method,
        underpowered=underpowered,
    )
