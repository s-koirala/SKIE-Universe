"""Risk-of-ruin Monte Carlo primitive.

Per ADR-0017 §4.2 (corrected per Round-1 audit F-6/F-7/F-14):

Every KPI report card from 2026-05-08 forward must report the Monte-Carlo-
estimated probability of ruin = P(equity reaches a ruin_threshold before
n_sessions = 252) under the strategy's empirical per-trade R-multiple
distribution combined with a sizing rule (default: ADR-0017 §4.1).

Practitioner attribution (load-bearing for the simulator's design):
- Vince, R. 1990. Portfolio Management Formulas, Wiley, ISBN 978-0471527565.
  Ch. 4 "Risk of Ruin" (practitioner).

Corroborating motivation (NOT load-bearing for the multiplicative-equity
Monte Carlo correctness; the gambler's-ruin closed-form is for fixed-bet-size
simple random walks, not multiplicative-equity processes — Round-1 audit F-6):
- Feller, W. 1968. An Introduction to Probability Theory and Its Applications,
  Vol. I, 3rd ed. Wiley, ISBN 978-0471257080. Ch. XIV "The Gambler's Ruin Problem".

Default ruin_threshold = 0.5 (50% of starting bankroll); the operator-canonical
"don't delete more than half the bankroll" floor. Calibratable per follow-up
`P1-ADR-0017-RUIN-THRESHOLD-EMPIRICAL` (e.g., the Faith 2007 Turtle 20% MaxDD
floor is a stricter alternative). Round-1 audit F-7 remediation.

Implementation lands per `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §4.2).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "RiskOfRuinResult",
    "probability_of_ruin_monte_carlo",
]


@dataclass(frozen=True)
class RiskOfRuinResult:
    """Result of a Monte Carlo risk-of-ruin computation."""

    probability_of_ruin: float
    ruin_threshold_fraction: float
    n_sessions: int
    n_paths: int
    median_terminal_equity: float
    q05_terminal_equity: float
    q01_terminal_equity: float
    rng_seed: int


def probability_of_ruin_monte_carlo(
    r_multiples: np.ndarray,
    *,
    starting_equity: float = 10_000.0,
    ruin_threshold_fraction: float = 0.5,
    n_sessions: int = 252,
    n_paths: int = 5000,
    kelly_fraction: float = 0.25,
    sizing_fn=None,
    rng_seed: int = 20260508,
) -> RiskOfRuinResult:
    """Monte Carlo estimate of P(equity hits ruin_threshold before n_sessions).

    The simulator draws per-session per-trade R-multiples with replacement
    from the empirical distribution `r_multiples`, applies the canonical
    sizing rule per ADR-0017 §4.1 with the supplied `kelly_fraction`, and
    counts the fraction of paths whose equity touches
    `starting_equity * ruin_threshold_fraction` at any session before
    `n_sessions`.

    Args:
        r_multiples: 1-D array of empirical per-trade R-multiples from the
            IS fold.
        starting_equity: Bankroll at t=0 (default $10,000; project convention
            per ADR-0013 §3.1).
        ruin_threshold_fraction: Equity floor as fraction of starting equity
            (default 0.5 = 50% bankroll preservation; the operator-canonical
            "don't delete more than half the bankroll" floor).
        n_sessions: Number of forward sessions to simulate (default 252).
        n_paths: Number of Monte Carlo paths (default 5,000; matches
            ADR-0013 §3.1 forward-projection n_paths convention).
        kelly_fraction: Drawdown-constrained Kelly fraction in [0, 0.25]
            (default 0.25; the project quarter-Kelly cap per ADR-0017 §4.1).
            Used only when sizing_fn is None (legacy fixed-fraction-of-equity mode).
        sizing_fn: Optional callable `(equity, atr, multiplier, entry_price, ...) -> int`
            implementing the §4.1 ADR-0017 sizing rule (Round-1 audit F-14
            remediation). When None, falls back to fixed-fraction-of-equity
            sizing using `kelly_fraction`. The report card MUST surface which
            mode was used (`fixed-fraction` vs `survival-constrained-§4.1`).
        rng_seed: Deterministic RNG seed (default 20260508).

    Returns:
        RiskOfRuinResult with probability_of_ruin + tail terminal-equity quantiles.

    Raises:
        NotImplementedError: pending BLOCKING-before-launch implementation
            per `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE`.
    """
    raise NotImplementedError(
        "P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE pending; "
        "interface contract per ADR-0017 §4.2"
    )
