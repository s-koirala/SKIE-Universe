"""Profit factor + differential CI primitives.

Per ADR-0017 §2.3, profit_factor = gross_profit / gross_loss is operator-
intuitive, scale-invariant, and directly measures the symmetry of winning
vs losing dollar-flow.

Practitioner attribution (Round-1 audit L-2/L-6 remediation): the profit-factor
metric itself is a long-standing futures-trading practitioner convention
(TradeStation system-trading literature, 1980s; LeBeau, Lucas, Williams;
*practitioner-canonical*, multi-source). Tharp 1998 popularized the
`PF >= 1.5` operator-threshold convention as part of the R-multiple framework.

Tharp 1998 *Trade Your Way to Financial Freedom* 1st ed., McGraw-Hill,
ISBN 978-0070647626 (*practitioner*; corrected from the 2007 2nd ed. ISBN
978-0071478717 per Round-1 audit L-2 — the R-multiple framework was introduced
in the 1998 1st edition).

Inferential CI on the differential PF_arm − PF_bench via stationary-bootstrap
per Politis-Romano 1994 JASA 89(428):1303-1313 with Politis-White 2004 +
Patton-Politis-White 2009 corrected automatic block-length selection.

**Default mode** (per Round-1 audit F-13 remediation): bootstrap at the
**per-session-aggregate level** (gross_profit/gross_loss per session, then
aggregate to PF). This is robust to intra-session trade clustering present
in high-frequency intraday strategies. Per-trade-level bootstrap is a
sensitivity exhibit subject to a low-clustering empirical caveat tracked
under follow-up `P1-PROFIT-FACTOR-PER-TRADE-CLUSTER-AUDIT`.

Implementation lands per `P1-PROFIT-FACTOR-CI-IMPL`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §2.3).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "profit_factor",
    "profit_factor_differential",
    "ProfitFactorDifferentialCI",
    "profit_factor_differential_ci_stationary_bootstrap",
]


@dataclass(frozen=True)
class ProfitFactorDifferentialCI:
    """Paired-pairs stationary-bootstrap CI on the profit-factor-differential statistic.

    Per Round-2 audit N-2 remediation: the differential statistic PF_arm − PF_bench
    is bootstrapped via paired-pairs joint-tuple resampling (per-session aggregate
    gross_profit/gross_loss tuples) with a shared block length on the joint
    series. The parallel reasoning to Calmar-differential applies: per-trade PnL
    from arm vs bench are joint-cross-sectional, and independent per-arm block-
    length selection produces miscalibrated CI on the differential. The shared
    block-length design mirrors CalmarDifferentialCI.
    """

    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence: float
    n_bootstrap: int
    block_length: int  # single shared block length on joint per-session aggregates per N-2
    rng_seed: int
    pf_arm: float
    pf_bench: float


def profit_factor(per_trade_pnl: np.ndarray) -> float:
    """profit_factor = gross_profit / gross_loss.

    Args:
        per_trade_pnl: 1-D array of per-trade P/L (positive for winners,
            negative for losers, zero for breakeven trades).

    Returns:
        Float; +inf if no losing trades; 0.0 if no winning trades.

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-PROFIT-FACTOR-CI-IMPL`.
    """
    raise NotImplementedError(
        "P1-PROFIT-FACTOR-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.3"
    )


def profit_factor_differential(
    per_trade_pnl_arm: np.ndarray,
    per_trade_pnl_bench: np.ndarray,
) -> float:
    """PF_arm − PF_bench (point estimate)."""
    raise NotImplementedError(
        "P1-PROFIT-FACTOR-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.3"
    )


def profit_factor_differential_ci_stationary_bootstrap(
    per_trade_pnl_arm: np.ndarray,
    per_trade_pnl_bench: np.ndarray,
    *,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    rng_seed: int = 20260508,
) -> ProfitFactorDifferentialCI:
    """Politis-Romano 1994 stationary-bootstrap CI on the PF-differential."""
    raise NotImplementedError(
        "P1-PROFIT-FACTOR-CI-IMPL pending; "
        "interface contract per ADR-0017 §2.3"
    )
