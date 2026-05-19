"""Current-equity-rebase primitive per ADR-0025 §D-2.

Consolidates the inlined `eq_for_sizing = current_equity if use_current_equity_rebase
else starting_equity` pattern duplicated across 5 orchestrators
(`scripts/run_h055_v2_sweep.py`, `scripts/run_h062_aggressive_sizing_sweep.py`,
`scripts/run_h065_tp_overlay_sweep.py`, `scripts/run_h065_sil_standalone_investigation.py`,
`scripts/run_h062_c3_2026_q1q2.py`) into a single shared, type-safe primitive.

Per ADR-0017 §4.1 sizing-primitive contract preservation (the §4.1 primitive at
[src/skie_ninja/sizing/__init__.py](../sizing/__init__.py) computes the Kelly
fraction `f_kelly`; this module computes the equity-denominator), the rebase
primitive wraps a clean adapter around the §4.1 callable.

Three modes per ADR-0025 §D-2 F-1-3 audit fix:

- ``fixed`` (ADR-0017 §4.1 pre-2026-05-08 default): returns ``starting_equity`` always.
- ``current`` (post-2026-05-08 default per Phase O.3 + Phase O.4 sweeps): returns
  ``max(current_equity, floor_equity_fraction * starting_equity)``. The floor
  prevents zero-equity sizing-denominator pathology surfaced in Phase O.3 MGC
  fixed-rebase blowup (min_equity = -$656); ACKNOWLEDGED operator-discretionary
  deviation from strict Kelly semantics at low-bankroll states.
- ``min_of_current_and_starting`` (Kelly-strict): returns
  ``min(current_equity, starting_equity)``. Protects against over-sizing after
  a run-up; does NOT floor at zero — a bankrupted leg produces zero sizing per
  Vince 1990 *Portfolio Management Formulas* ISBN-13 978-0471527565 Ch. 5
  "Risk of Ruin" (*practitioner*) gambler's-ruin convention.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = ["EquityRebasePolicy", "equity_for_sizing", "apply_pnl_to_equity"]


@dataclass(frozen=True)
class EquityRebasePolicy:
    """Frozen policy object capturing the rebase mode + parameters.

    Attributes:
        mode: One of {"fixed", "current", "min_of_current_and_starting"}.
        starting_equity: Account equity at the start of the simulation (USD).
        floor_equity_fraction: For mode="current", the floor as a fraction of
            starting_equity below which sizing-denominator does not fall.
            justify: 0.10 default matches the H055 v2 + H062 aggressive-sizing
            sweep convention per Phase O.3 / Phase O.4; the floor prevents
            divide-by-near-zero on a bankrupted leg (Phase O.3 MGC blowup at
            min_equity = -$656 was the canonical pathology).
    """

    mode: Literal["fixed", "current", "min_of_current_and_starting"] = "current"
    starting_equity: float = 10_000.0
    floor_equity_fraction: float = 0.10

    def __post_init__(self) -> None:
        if self.starting_equity <= 0:
            raise ValueError(
                f"starting_equity must be positive; got {self.starting_equity}."
            )
        if not (0.0 <= self.floor_equity_fraction <= 1.0):
            raise ValueError(
                f"floor_equity_fraction must be in [0, 1]; "
                f"got {self.floor_equity_fraction}."
            )
        if self.mode not in {"fixed", "current", "min_of_current_and_starting"}:
            raise ValueError(
                f"mode must be one of "
                f"{{'fixed', 'current', 'min_of_current_and_starting'}}; "
                f"got {self.mode}."
            )


def equity_for_sizing(policy: EquityRebasePolicy, current_equity: float) -> float:
    """Return the equity-denominator for Kelly sizing per the policy.

    Args:
        policy: EquityRebasePolicy frozen at sweep-start.
        current_equity: Current account equity (USD), updated trade-by-trade
            via `apply_pnl_to_equity`.

    Returns:
        Equity (USD) to use as the sizing denominator. By construction non-
        negative; for `mode="current"` floored at
        `floor_equity_fraction * starting_equity`; for `mode="fixed"` always
        equal to `starting_equity`.
    """
    if policy.mode == "fixed":
        return float(policy.starting_equity)
    if policy.mode == "current":
        floor = policy.floor_equity_fraction * policy.starting_equity
        return float(max(current_equity, floor))
    # mode == "min_of_current_and_starting" (Kelly-strict)
    return float(min(current_equity, policy.starting_equity))


def apply_pnl_to_equity(equity: float, realized_pnl_dollar: float) -> float:
    """Accumulate realized P/L with floor-at-zero clamp.

    Per Vince 1990 *Portfolio Management Formulas* ISBN-13 978-0471527565
    Ch. 5 "Risk of Ruin" (*practitioner*) gambler's-ruin convention: a
    bankrupt account cannot go further negative. This matches the realistic
    futures-broker margin-call mechanic (the broker forces liquidation before
    equity goes negative; we conservatively floor at zero).

    Args:
        equity: Current equity (USD).
        realized_pnl_dollar: Realized P/L of the just-closed trade (USD;
            signed; negative = loss).

    Returns:
        New equity, clamped at floor 0.0.
    """
    return float(max(0.0, equity + realized_pnl_dollar))
