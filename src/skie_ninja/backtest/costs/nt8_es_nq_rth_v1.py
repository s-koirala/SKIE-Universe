"""NinjaTrader Brokerage conservative cost prior for ES and NQ RTH sessions.

Cost model ID: ``nt8_es_nq_rth_v1``

This module implements the fallback cost model referenced in H050 design.md §7.
It uses fixed per-contract fees drawn from ``config/instruments.yaml`` plus a
conservative one-tick slippage prior.  A sensitivity multiplier allows
scenario analysis.

## Fee structure (per side, per contract)

Source: ``config/instruments.yaml`` (CME fees + NinjaTrader Brokerage published
rate sheet, retrieved 2026-04-15):

  commission:  $0.85   (NinjaTrader Brokerage Unlimited plan, Q1-2026)
  exchange:    $1.18   (CME Individual Member Equity Index electronic, eff. 2024-02)
  nfa:         $0.02   (NFA Rulebook Section 13, eff. 2024-01-01)
  ──────────
  total fixed: $2.05/side/contract

## Slippage prior (conservative constant-tick)

One-tick slip per side is applied as a conservative prior until paper-trade
fill logs are available for empirical calibration (follow-up
``P1-H050-COST-EMPIRICAL-CALIBRATION``).

  ES tick value: $12.50  → $12.50/side slip
  NQ tick value:  $5.00  →  $5.00/side slip

Sources: CME product specs (tick_value in config/instruments.yaml).

## Round-trip cost formula

    cost_rt = 2 × n_contracts × (fixed_per_side + slip_per_side)

The factor 2 accounts for entry + exit (two sides per round trip).

## Sensitivity multiplier

``sensitivity_mult`` scales the slippage-only component (fixed fees do not
scale; they are contractually fixed).  This isolates the uncertainty in the
slippage prior from the certainty in the commission schedule.

    cost_rt = 2 × n_contracts × (fixed_per_side + sensitivity_mult × slip_per_side)

Default ``sensitivity_mult=1.0`` is the conservative 1-tick prior.
``sensitivity_mult=2.0`` corresponds to a 2-tick worst-case sensitivity run.

## References

- NinjaTrader Brokerage pricing: https://ninjatrader.com/pricing/ (2026-04-15)
- CME clearing fees: https://www.cmegroup.com/company/clearing-fees.html (2024-02)
- NFA fee schedule: NFA Rulebook Section 13 (eff. 2024-01-01)
- config/instruments.yaml — canonical fee values used here
- Follow-up P1-H050-COST-EMPIRICAL-CALIBRATION: replace slip prior with
  distribution fit from paper-trade logs once TrivialSmokeTest run completes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


# ---------------------------------------------------------------------------
# Per-symbol fee constants drawn from config/instruments.yaml
# ---------------------------------------------------------------------------

_FIXED_PER_SIDE: dict[str, float] = {
    "ES": 0.85 + 1.18 + 0.02,  # commission + exchange + nfa
    "NQ": 0.85 + 1.18 + 0.02,
    "MES": 0.35 + 0.35 + 0.02,
    "MNQ": 0.35 + 0.35 + 0.02,
}

_SLIP_PER_SIDE_USD: dict[str, float] = {
    "ES": 12.50,   # 1 tick × $12.50/tick (CME product spec)
    "NQ":  5.00,   # 1 tick ×  $5.00/tick (CME product spec)
    "MES":  1.25,  # 1 tick ×  $1.25/tick (CME product spec)
    "MNQ":  0.50,  # 1 tick ×  $0.50/tick (CME product spec)
}


@dataclass(frozen=True)
class NT8EsNqRthV1CostModel:
    """Conservative NinjaTrader cost prior for ES/NQ RTH walk-forward.

    Parameters
    ----------
    sensitivity_mult:
        Scales the slippage component only (fixed fees are contractually
        constant).  Default 1.0 = 1-tick prior.  Use 2.0 for worst-case
        sensitivity run.
    """

    cost_model_id: ClassVar[str] = "nt8_es_nq_rth_v1"

    sensitivity_mult: float = field(default=1.0)

    def __post_init__(self) -> None:
        if self.sensitivity_mult <= 0:
            raise ValueError(
                f"sensitivity_mult must be positive; got {self.sensitivity_mult}"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def round_trip_cost(self, symbol: str, n_contracts: int = 1) -> float:
        """Return total round-trip cost in USD.

        Parameters
        ----------
        symbol:
            Instrument root (``"ES"``, ``"NQ"``, ``"MES"``, ``"MNQ"``).
        n_contracts:
            Number of contracts traded.

        Returns
        -------
        float
            Total USD cost for one round-trip (open + close).
        """
        sym = symbol.upper()
        if sym not in _FIXED_PER_SIDE:
            raise ValueError(
                f"Symbol '{symbol}' not in NT8EsNqRthV1 cost model. "
                f"Supported: {list(_FIXED_PER_SIDE)}"
            )
        if n_contracts <= 0:
            raise ValueError(
                f"n_contracts must be positive; got {n_contracts}"
            )
        fixed = _FIXED_PER_SIDE[sym]
        slip = _SLIP_PER_SIDE_USD[sym]
        return 2 * n_contracts * (fixed + self.sensitivity_mult * slip)

    def cost_per_bar_return(
        self,
        symbol: str,
        position: float,
        price: float,
        n_contracts: int = 1,
    ) -> float:
        """Return cost as a fraction of notional (for Sharpe deduction).

        Converts round_trip_cost to a per-bar return deduction by dividing
        by the trade's notional value.  Used when net-of-cost returns are
        computed as ``raw_return - cost_per_bar_return``.

        Parameters
        ----------
        symbol:
            Instrument root.
        position:
            ±1 for long/short; 0 for flat (no cost).
        price:
            Entry price for notional calculation.
        n_contracts:
            Number of contracts.

        Returns
        -------
        float
            Cost as a fraction of notional.  Always non-negative.
        """
        if position == 0:
            return 0.0
        multipliers = {"ES": 50.0, "NQ": 20.0, "MES": 5.0, "MNQ": 2.0}
        sym = symbol.upper()
        if sym not in multipliers:
            raise ValueError(f"Symbol '{symbol}' not in NT8EsNqRthV1 cost model.")
        notional = price * multipliers[sym] * n_contracts
        if notional <= 0:
            raise ValueError(f"Notional must be positive; got {notional}")
        return self.round_trip_cost(sym, n_contracts) / notional

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def fee_breakdown(self, symbol: str) -> dict[str, float]:
        """Return per-side fee breakdown for inspection and audit trail.

        Returns
        -------
        dict with keys: commission, exchange, nfa, slippage_prior,
        total_per_side, total_round_trip_1_contract
        """
        sym = symbol.upper()
        if sym not in _FIXED_PER_SIDE:
            raise ValueError(f"Symbol '{symbol}' not in NT8EsNqRthV1 cost model.")
        fixed = _FIXED_PER_SIDE[sym]
        slip = _SLIP_PER_SIDE_USD[sym] * self.sensitivity_mult
        return {
            "commission_per_side": 0.85 if sym in ("ES", "NQ") else 0.35,
            "exchange_fee_per_side": 1.18 if sym in ("ES", "NQ") else 0.35,
            "nfa_fee_per_side": 0.02,
            "slippage_prior_per_side": slip,
            "total_per_side": fixed + slip,
            "total_round_trip_1_contract": 2 * (fixed + slip),
        }
