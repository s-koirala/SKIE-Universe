"""H052a futures ORB cost model — ``futures_orb_v1``.

Per H052a frozen pre-reg [research/01_hypothesis_register/H052a/design.md](
../../../../research/01_hypothesis_register/H052a/design.md) §7:

  - Commissions + exchange fees + NFA: per-contract static schedule from
    ``config/instruments.yaml`` (CME-cited).
  - Slippage: 1-tick floor on market orders at entry and exit (conservative);
    upgraded to regime-wise empirical fit once paper-trade logs accumulate
    (deferred under follow-up ``P1-H052A-COST-CALIBRATION-EMPIRICAL``).
  - No borrow cost (futures don't have one).
  - **Round-trip = entry market order at 10:30 ET + exit market order at
    PT/SL/timestop/hardclose**.

Differences from ``nt8_es_nq_rth_v1`` (the H050 baseline):

  - Cost model id: ``futures_orb_v1`` (vs ``nt8_es_nq_rth_v1``).
  - Round-trip semantics: per-session round-trip (one entry + one exit per
    session) rather than per-bar position-flip continuous-trading model.
  - Per-session log-return drag: ``cost_per_session_log_return`` returns a
    log-return drag for the H052a daily-cleared single-leg session-cadence
    strategy (vs ``cost_per_bar_return`` which returns a per-bar fraction).

Per ADR-0013 §3.1.1 sizing-convention table (First-hour ORB futures row) +
ADR-0013 §3.1 F-CONV-2 audit (log-return-drag application rule): the strategy
is daily-cleared session-cadence; the cost model produces a per-session
log-return drag suitable for direct subtraction from ``pnl_log`` per-session
in the orchestrator. F-L-2 audit-remediate-loop 2026-05-04 corrected prior
misattribution (ADR-0014 §3.2 governs the 9-table summary, not the
log-return-drag rule).

References
----------

- NinjaTrader Brokerage pricing (Q1-2026)
- CME clearing fees (eff. 2024-02)
- NFA Rulebook Section 13 (eff. 2024-01-01)
- ``config/instruments.yaml`` — canonical fee values
- Follow-up ``P1-H052A-COST-CALIBRATION-EMPIRICAL``: replace 1-tick prior
  with regime-wise empirical fit from paper-trade logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import numpy as np


# Per-side fixed fees (commission + exchange + NFA), USD/contract.
# Mirrors nt8_es_nq_rth_v1 for ES/NQ; same fee schedule applies to ORB.
_FIXED_PER_SIDE: dict[str, float] = {
    "ES": 0.85 + 1.18 + 0.02,  # commission + exchange + nfa = 2.05
    "NQ": 0.85 + 1.18 + 0.02,
    "MES": 0.35 + 0.35 + 0.02,
    "MNQ": 0.35 + 0.35 + 0.02,
}

# Per-side slippage prior (1-tick × tick value), USD/contract/side.
_SLIP_PER_SIDE_USD: dict[str, float] = {
    "ES": 12.50,
    "NQ": 5.00,
    "MES": 1.25,
    "MNQ": 0.50,
}

# Notional multipliers ($ per index point per contract).
_NOTIONAL_MULTIPLIERS: dict[str, float] = {
    "ES": 50.0,
    "NQ": 20.0,
    "MES": 5.0,
    "MNQ": 2.0,
}


@dataclass(frozen=True)
class FuturesOrbV1CostModel:
    """Conservative cost prior for H052a futures ORB strategy.

    Parameters
    ----------
    sensitivity_mult:
        Scales the slippage component only (fixed fees are contractually
        constant). Default 1.0 = 1-tick prior. Use 2.0 for worst-case
        sensitivity per design.md §7 + cost-floor sensitivity KPI.
    """

    cost_model_id: ClassVar[str] = "futures_orb_v1"

    sensitivity_mult: float = field(default=1.0)

    def __post_init__(self) -> None:
        if self.sensitivity_mult <= 0:
            raise ValueError(
                f"sensitivity_mult must be positive; got {self.sensitivity_mult}."
            )

    def round_trip_cost_usd(self, symbol: str, n_contracts: int = 1) -> float:
        """Return total round-trip cost in USD per session.

        H052a is one round-trip per session (entry at 10:30 ET + exit at
        PT/SL/timestop/hardclose). The factor 2 below covers entry + exit.
        """
        sym = symbol.upper()
        if sym not in _FIXED_PER_SIDE:
            raise ValueError(
                f"Symbol '{symbol}' not in futures_orb_v1 cost model. "
                f"Supported: {list(_FIXED_PER_SIDE)}"
            )
        if n_contracts <= 0:
            raise ValueError(f"n_contracts must be positive; got {n_contracts}.")
        fixed = _FIXED_PER_SIDE[sym]
        slip = _SLIP_PER_SIDE_USD[sym]
        return 2.0 * n_contracts * (fixed + self.sensitivity_mult * slip)

    def cost_per_session_log_return(
        self,
        *,
        symbol: str,
        entry_price: float,
        n_contracts: int = 1,
    ) -> float:
        """Return cost as a log-return drag for a single H052a session.

        Per H053 F-CONV-2 audit + ADR-0013 §3.1: cost is applied as a
        log-return drag inside the per-session compounding loop (NOT a
        flat-dollar subtraction at horizon). For a session entered at
        ``entry_price``:

            cost_log_drag = log(1 - round_trip_cost / notional)

        where notional = ``entry_price × multiplier × n_contracts`` and
        round_trip_cost is the entry+exit fixed-fee + slippage cost.

        For small cost-to-notional ratios (typical: ~3-7e-4 for ES at 1
        contract), ``log(1 − x) ≈ −x``, so the log-return drag is
        approximately the negative cost-to-notional ratio.
        """
        sym = symbol.upper()
        if sym not in _NOTIONAL_MULTIPLIERS:
            raise ValueError(
                f"Symbol '{symbol}' not in futures_orb_v1 cost model. "
                f"Supported: {list(_NOTIONAL_MULTIPLIERS)}"
            )
        if entry_price <= 0:
            raise ValueError(f"entry_price must be > 0; got {entry_price}.")
        if n_contracts <= 0:
            raise ValueError(f"n_contracts must be positive; got {n_contracts}.")
        notional = entry_price * _NOTIONAL_MULTIPLIERS[sym] * n_contracts
        cost_usd = self.round_trip_cost_usd(sym, n_contracts)
        cost_to_notional = cost_usd / notional
        # log(1 − x) for x in (0, 1); guard against numerical overshoot.
        if cost_to_notional >= 1.0:
            raise ValueError(
                f"cost_to_notional {cost_to_notional} >= 1.0; entry_price too small "
                f"or n_contracts too large for {sym}."
            )
        # R-9 fix (Round-2 audit-remediate-loop 2026-05-04): hoisted numpy
        # import to module top per project convention.
        return float(np.log1p(-cost_to_notional))

    def fee_breakdown(self, symbol: str) -> dict[str, float]:
        """Return per-side fee breakdown for inspection / audit trail."""
        sym = symbol.upper()
        if sym not in _FIXED_PER_SIDE:
            raise ValueError(f"Symbol '{symbol}' not in futures_orb_v1 cost model.")
        commission = 0.85 if sym in ("ES", "NQ") else 0.35
        exchange = 1.18 if sym in ("ES", "NQ") else 0.35
        nfa = 0.02
        slip = _SLIP_PER_SIDE_USD[sym] * self.sensitivity_mult
        fixed = commission + exchange + nfa
        return {
            "commission_per_side": commission,
            "exchange_fee_per_side": exchange,
            "nfa_fee_per_side": nfa,
            "slippage_prior_per_side": slip,
            "total_per_side": fixed + slip,
            "total_round_trip_1_contract": 2.0 * (fixed + slip),
        }


__all__ = ["FuturesOrbV1CostModel"]
