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

Implementation per `P1-RISK-OF-RUIN-MONTE-CARLO-PRIMITIVE`
(BLOCKING-BEFORE-NEXT-NEW-HYPOTHESIS-LAUNCH per ADR-0017 §4.2).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

__all__ = [
    "RiskOfRuinResult",
    "probability_of_ruin_monte_carlo",
]


@dataclass(frozen=True)
class RiskOfRuinResult:
    """Result of a Monte Carlo risk-of-ruin computation.

    **Semantic note** (per Round-1 audit F-4-2): `probability_of_ruin` is the
    fraction of paths that **ever touched** `ruin_threshold` at any session,
    while `*_terminal_equity` quantiles are computed over **all paths** at the
    final session — including paths that touched ruin and subsequently
    recovered. The two metrics describe different conditional distributions:
    `probability_of_ruin` is the canonical operator-bankroll-survival metric;
    `terminal_equity` quantiles are unconditional terminal-state distributions.
    KPI consumers should not interpret `median_terminal_equity` as a
    "post-ruin" or "no-ruin" conditional median.

    Provenance fields:
    - sizing_mode: "fixed_fraction_of_equity" (legacy) or "survival_constrained_4_1"
      (ADR-0017 §4.1 callable). The KPI report card MUST surface which mode
      was used per Round-1 audit F-14.
    - n_paths_ruined: integer count of paths that hit ruin_threshold; equals
      `probability_of_ruin * n_paths`. Surfaced for sample-size auditability.
    """

    probability_of_ruin: float
    ruin_threshold_fraction: float
    n_sessions: int
    n_paths: int
    n_paths_ruined: int
    median_terminal_equity: float
    q05_terminal_equity: float
    q01_terminal_equity: float
    rng_seed: int
    sizing_mode: str = "fixed_fraction_of_equity"


def probability_of_ruin_monte_carlo(
    r_multiples: npt.ArrayLike,
    *,
    starting_equity: float = 10_000.0,
    ruin_threshold_fraction: float = 0.5,
    n_sessions: int = 252,
    n_paths: int = 5000,
    kelly_fraction: float = 0.25,
    sizing_fn: Callable[[float], float] | None = None,
    rng_seed: int = 20260508,
) -> RiskOfRuinResult:
    """Monte Carlo estimate of P(equity hits ruin_threshold before n_sessions).

    The simulator draws per-session per-trade R-multiples with replacement
    from the empirical distribution `r_multiples`, computes the per-session
    dollar P/L = R × dollars_at_risk where dollars_at_risk is determined by
    the sizing mode:

    - **Default (sizing_fn=None)**: fixed-fraction-of-equity mode;
      `dollars_at_risk = kelly_fraction × current_equity`. Legacy mode for
      cross-paper comparability.
    - **§4.1 mode (sizing_fn=callable)**: caller-supplied `sizing_fn(equity)
      → dollars_at_risk` implementing the ADR-0017 §4.1 rule (per Round-1
      audit F-14). The callable receives the current equity and returns
      the dollar-amount risked per session.

    The simulator counts the fraction of paths whose equity touches
    `starting_equity * ruin_threshold_fraction` at any session before
    `n_sessions`.

    Args:
        r_multiples: 1-D array of empirical per-trade R-multiples from the
            IS fold. Must contain at least one finite value.
        starting_equity: Bankroll at t=0 (default $10,000; project convention
            per ADR-0013 §3.1).
        ruin_threshold_fraction: Equity floor as fraction of starting equity
            (default 0.5 = 50% bankroll preservation; the operator-canonical
            "don't delete more than half the bankroll" floor per ADR-0017 §4.2).
        n_sessions: Number of forward sessions to simulate (default 252).
        n_paths: Number of Monte Carlo paths (default 5,000; matches
            ADR-0013 §3.1 forward-projection n_paths convention).
        kelly_fraction: Drawdown-constrained Kelly fraction in [0, 0.25]
            (default 0.25; the project quarter-Kelly cap per ADR-0017 §4.1).
            Used only when sizing_fn is None (legacy fixed-fraction-of-equity mode).
        sizing_fn: Optional callable `(equity) -> dollars_at_risk` implementing
            the §4.1 ADR-0017 sizing rule (per Round-1 audit F-14). When None,
            falls back to fixed-fraction-of-equity sizing using `kelly_fraction`.

            **CRITICAL: dollars_at_risk semantic** (per Round-1 audit F-4-3):
            the callable's return value MUST be **dollars-at-risk on the
            1R-stop scale** (i.e., the dollar loss of an R=−1 trade equals
            `dollars_at_risk`), NOT notional dollar-exposure. When wiring
            `compute_position_size` output via this callable, multiply by
            `k_atr × atr × multiplier` (the per-contract 1R dollar-loss),
            NOT by `entry_price × multiplier` (the per-contract notional).
            Misusing notional in place of 1R-scale would inflate per-trade
            P/L by ~entry_price/(k_atr × atr) ≈ 50-100× and produce wildly
            wrong ruin probabilities.
        rng_seed: Deterministic RNG seed (default 20260508).

    Returns:
        RiskOfRuinResult with probability_of_ruin + tail terminal-equity quantiles
        + sizing_mode provenance.

    Raises:
        ValueError: if r_multiples is empty / has no finite values, or if
            other arguments fall outside their valid ranges.
    """
    rm = np.asarray(r_multiples, dtype=float).ravel()
    rm = rm[np.isfinite(rm)]
    if rm.size == 0:
        raise ValueError("r_multiples must contain at least one finite value.")
    if starting_equity <= 0.0:
        raise ValueError(f"starting_equity must be positive, got {starting_equity}.")
    if not (0.0 < ruin_threshold_fraction < 1.0):
        raise ValueError(
            f"ruin_threshold_fraction must be in (0, 1), got {ruin_threshold_fraction}."
        )
    if n_sessions < 1:
        raise ValueError(f"n_sessions must be >= 1, got {n_sessions}.")
    if n_paths < 1:
        raise ValueError(f"n_paths must be >= 1, got {n_paths}.")
    if not (0.0 <= kelly_fraction <= 1.0):
        raise ValueError(f"kelly_fraction must be in [0, 1], got {kelly_fraction}.")

    sizing_mode = "survival_constrained_4_1" if sizing_fn is not None else "fixed_fraction_of_equity"

    rng = np.random.default_rng(rng_seed)
    indices = rng.integers(0, rm.size, size=(n_paths, n_sessions))
    path_r = rm[indices]  # (n_paths, n_sessions)

    ruin_floor = float(starting_equity * ruin_threshold_fraction)

    if sizing_fn is None:
        # Vectorized default mode: per-trade equity update is
        # equity_{t+1} = equity_t × (1 + kelly_fraction × R_t),
        # so log-return = log(1 + kelly_fraction × R_t). Accumulate via cumsum;
        # equity = starting_equity × exp(cumsum(log_returns)).
        # This is O(n_paths × n_sessions) numpy ops vs O(n_paths × n_sessions)
        # Python loop iterations. Empirical bench at default 5000×252 sizes:
        # ~3× faster than the loop mode (54 ms vs 150 ms; the prior estimate
        # of 50-200× was incorrect — Python overhead at 252 inner iterations
        # is modest, so the speedup is largely from numpy memory locality).
        # Per Round-1 audit F-4-1 remediation + Round-2 audit F-2-3 update.
        gross = 1.0 + kelly_fraction * path_r
        # Catastrophic-bet floor (1 + f·R ≤ 0 → bankroll depleted): clamp at
        # a tiny positive value so log is finite; the resulting equity ≈ 0
        # is correctly captured as "below ruin_floor" in the threshold check.
        gross = np.maximum(gross, 1e-12)
        log_returns = np.log(gross)  # (n_paths, n_sessions)
        cum_log = np.cumsum(log_returns, axis=1)
        equity_curves = starting_equity * np.exp(cum_log)  # (n_paths, n_sessions)
        # Per-path "ever touched ruin" check: any session where equity ≤ ruin_floor.
        ruined_mask = (equity_curves <= ruin_floor).any(axis=1)
        n_ruined = int(ruined_mask.sum())
        terminal_equity = equity_curves[:, -1].copy()
        # Clamp depleted-bankroll terminal equity at 0 (catastrophic-bet floor
        # leaves equity at ~0 but >0 due to clamp; faithful representation of
        # "ruined" is equity = 0 at terminal).
        terminal_equity[terminal_equity < starting_equity * 1e-9] = 0.0
    else:
        # §4.1 sizing_fn callable mode: must use Python loop because the
        # callable receives current equity and returns dollars_at_risk per
        # session, which generally is not expressible as a closed-form
        # equity transform. Per Round-1 audit F-4-3 remediation: the
        # sizing_fn return value is interpreted as **dollars-at-risk on
        # the 1R-stop scale** (i.e., an R=−1 trade loses exactly that
        # amount), NOT notional dollar-exposure.
        terminal_equity = np.empty(n_paths, dtype=float)
        n_ruined = 0
        for p in range(n_paths):
            equity = float(starting_equity)
            ruined = False
            for t in range(n_sessions):
                dollars_at_risk = float(sizing_fn(equity))
                equity = equity + float(path_r[p, t]) * dollars_at_risk
                if equity <= ruin_floor and not ruined:
                    ruined = True
                if equity <= 0.0:
                    equity = 0.0
                    break
            terminal_equity[p] = equity
            if ruined:
                n_ruined += 1

    probability_of_ruin = float(n_ruined) / float(n_paths)

    return RiskOfRuinResult(
        probability_of_ruin=probability_of_ruin,
        ruin_threshold_fraction=ruin_threshold_fraction,
        n_sessions=n_sessions,
        n_paths=n_paths,
        n_paths_ruined=n_ruined,
        median_terminal_equity=float(np.median(terminal_equity)),
        q05_terminal_equity=float(np.quantile(terminal_equity, 0.05)),
        q01_terminal_equity=float(np.quantile(terminal_equity, 0.01)),
        rng_seed=rng_seed,
        sizing_mode=sizing_mode,
    )
