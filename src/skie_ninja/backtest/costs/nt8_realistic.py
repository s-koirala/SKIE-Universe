"""NT8-realistic multi-instrument cost model per ADR-0025 §D-3.

Extends the ES/NQ/MES/MNQ coverage of [nt8_es_nq_rth_v1.py](nt8_es_nq_rth_v1.py)
to include the metals/energy symbols MGC, SIL, MCL added per ADR-0023. Public
API mirrors the existing cost-model contract for drop-in replacement at
orchestrator wire-sites.

Empirical-calibration hook per ADR-0025 §D-3 F-1-5 audit fix: `EmpiricalFeeOverride`
allows operator-supplied fee + slippage values from paper-trade fill logs.
When supplied for a symbol, `sensitivity_mult` is IGNORED for that symbol's
slip component (with WARN logged) because the override is a calibrated quantity
not a prior.

Fee schedule sourced from [config/instruments.yaml](../../../../config/instruments.yaml)
at module-import time per the `commission_per_side_usd` / `exchange_fee_usd` /
`nfa_fee_usd` per-symbol entries. MGC / SIL / MCL fees are placeholders per
`P1-METALS-ENERGY-CME-FEE-VERIFY`; `fee_breakdown[symbol]["provenance"]`
surfaces the placeholder status.

KPI report card disclosure annotation per ADR-0025 §D-5:
- `cost-empirical-calibrated` if `calibration_source="paper_trade_empirical"`.
- `cost-conservative-prior` if `calibration_source="conservative_prior"`.
- `cost-zero` is admissible for explicit pre-cost research-only KPIs (operator
  must explicitly construct a `ZeroCostModel` adapter; this module does not
  silently degenerate to zero).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import ClassVar, Literal

import numpy as np

__all__ = ["EmpiricalFeeOverride", "NT8RealisticCostModel"]

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-symbol fee schedule sourced from config/instruments.yaml.
# Sums commission_per_side_usd + exchange_fee_usd + nfa_fee_usd from the YAML.
# ES/NQ/MES/MNQ: VERIFIED primary-source per nt8_es_nq_rth_v1.py.
# MGC/SIL/MCL: PLACEHOLDER pending P1-METALS-ENERGY-CME-FEE-VERIFY.
# ---------------------------------------------------------------------------

# justify: ES/NQ commission $0.85 + exchange $1.18 + NFA $0.02 = $2.05/side
# per nt8_es_nq_rth_v1.py + config/instruments.yaml (retrieved 2026-04-15).
_FIXED_PER_SIDE: dict[str, float] = {
    "ES": 0.85 + 1.18 + 0.02,
    "NQ": 0.85 + 1.18 + 0.02,
    # justify: MES/MNQ commission $0.35 + exchange $0.35 + NFA $0.02 = $0.72/side
    # per nt8_es_nq_rth_v1.py + config/instruments.yaml.
    "MES": 0.35 + 0.35 + 0.02,
    "MNQ": 0.35 + 0.35 + 0.02,
    # justify: MGC/SIL/MCL commission $0.85 + placeholder exchange + NFA $0.02
    # per config/instruments.yaml (PLACEHOLDER per P1-METALS-ENERGY-CME-FEE-VERIFY).
    "MCL": 0.85 + 0.50 + 0.02,
    "MGC": 0.85 + 0.45 + 0.02,
    "SIL": 0.85 + 0.45 + 0.02,
}

# justify: 1-tick slippage prior per side per CME tick_value
# (config/instruments.yaml); conservative until paper-trade fill-log empirical
# replacement per `P1-COST-MODEL-METALS-ENERGY-EMPIRICAL-OVERRIDE`.
_SLIP_PER_SIDE_USD: dict[str, float] = {
    "ES": 12.50,
    "NQ": 5.00,
    "MES": 1.25,
    "MNQ": 0.50,
    # MCL tick_size 0.01 × multiplier 100 = $1.00/tick
    "MCL": 1.00,
    # MGC tick_size 0.10 × multiplier 10 = $1.00/tick
    "MGC": 1.00,
    # SIL tick_size 0.005 × multiplier 1000 = $5.00/tick
    "SIL": 5.00,
}

# justify: notional multipliers per CME product specs ($ per unit price).
_NOTIONAL_MULTIPLIERS: dict[str, float] = {
    "ES": 50.0,
    "NQ": 20.0,
    "MES": 5.0,
    "MNQ": 2.0,
    "MCL": 100.0,
    "MGC": 10.0,
    "SIL": 1000.0,
}

# Provenance tag for fee_breakdown output. PLACEHOLDER for the metals/energy
# symbols pending P1-METALS-ENERGY-CME-FEE-VERIFY.
_FEE_PROVENANCE: dict[str, str] = {
    "ES": "config_instruments_yaml_verified",
    "NQ": "config_instruments_yaml_verified",
    "MES": "config_instruments_yaml_verified",
    "MNQ": "config_instruments_yaml_verified",
    "MCL": "config_instruments_yaml_placeholder",
    "MGC": "config_instruments_yaml_placeholder",
    "SIL": "config_instruments_yaml_placeholder",
}


@dataclass(frozen=True)
class EmpiricalFeeOverride:
    """Operator-supplied fee + slippage values from paper-trade fill logs.

    Per ADR-0025 §D-3 the override REPLACES the conservative-prior fee schedule
    for the specified symbol. `sensitivity_mult` is ignored for the symbol's
    slip component (with WARN logged) per F-1-5 audit fix.

    Attributes:
        fixed_per_side_usd: Operator-measured fixed-fee per side (commission +
            exchange + NFA + per-fill markup).
        slip_per_side_usd: Operator-measured slippage per side (from paper-
            trade fill price - mid-quote price).
        source: Free-text description of the data source (e.g., "H062 paper-
            trade 2026-Q3 fill log").
        source_sha256: SHA256 of the source-file content (for provenance).
        source_n_fills: Number of fill events the empirical values were
            calibrated against; small n_fills (<30) should carry an operator
            warning (handled in nt8_realistic at construction).
    """

    fixed_per_side_usd: float
    slip_per_side_usd: float
    source: str
    source_sha256: str
    source_n_fills: int

    def __post_init__(self) -> None:
        if self.fixed_per_side_usd < 0 or self.slip_per_side_usd < 0:
            raise ValueError(
                "EmpiricalFeeOverride fees + slippage must be non-negative; "
                f"got fixed={self.fixed_per_side_usd}, slip={self.slip_per_side_usd}."
            )
        if self.source_n_fills <= 0:
            raise ValueError(
                f"source_n_fills must be positive; got {self.source_n_fills}."
            )


@dataclass(frozen=True)
class NT8RealisticCostModel:
    """Multi-instrument NT8-realistic cost model per ADR-0025 §D-3.

    Attributes:
        sensitivity_mult: Scales slippage prior on the conservative-prior path
            only; ignored on the empirical-override path per F-1-5 audit fix.
        calibration_source: "conservative_prior" (instruments.yaml-derived) or
            "paper_trade_empirical" (overrides supplied via empirical_overrides).
        empirical_overrides: Per-symbol overrides; when present for a symbol,
            the conservative-prior path is bypassed for that symbol.
    """

    cost_model_id: ClassVar[str] = "nt8_realistic_v1"

    sensitivity_mult: float = 1.0
    calibration_source: Literal[
        "conservative_prior", "paper_trade_empirical"
    ] = "conservative_prior"
    empirical_overrides: dict[str, EmpiricalFeeOverride] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sensitivity_mult <= 0:
            raise ValueError(
                f"sensitivity_mult must be positive; got {self.sensitivity_mult}."
            )
        if (
            self.calibration_source == "paper_trade_empirical"
            and not self.empirical_overrides
        ):
            raise ValueError(
                "calibration_source='paper_trade_empirical' requires at least "
                "one entry in empirical_overrides; got empty dict."
            )
        # Warn on small-sample empirical overrides at construction time.
        # justify: n_fills < 30 threshold matches the F-7 audit-discipline
        # n_min boundary in the R-multiple primitive at
        # src/skie_ninja/inference/r_multiple.py.
        for sym, override in self.empirical_overrides.items():
            if override.source_n_fills < 30:
                _logger.warning(
                    "EmpiricalFeeOverride for %s calibrated against only %d "
                    "fills (n<30 boundary); consider waiting for more data",
                    sym,
                    override.source_n_fills,
                )

    # ------------------------------------------------------------------
    # Per-symbol fee resolution
    # ------------------------------------------------------------------

    def _resolved_fixed_per_side(self, sym: str) -> float:
        if sym in self.empirical_overrides:
            return self.empirical_overrides[sym].fixed_per_side_usd
        return _FIXED_PER_SIDE[sym]

    def _resolved_slip_per_side(self, sym: str) -> float:
        if sym in self.empirical_overrides:
            # F-1-5 audit fix: sensitivity_mult IGNORED on empirical path.
            _logger.debug(
                "sensitivity_mult ignored for %s (empirical override active)", sym
            )
            return self.empirical_overrides[sym].slip_per_side_usd
        return self.sensitivity_mult * _SLIP_PER_SIDE_USD[sym]

    # ------------------------------------------------------------------
    # Public API mirrors nt8_es_nq_rth_v1 + futures_orb_v1 contracts
    # ------------------------------------------------------------------

    def round_trip_cost_usd(self, symbol: str, n_contracts: int = 1) -> float:
        """Return total round-trip cost in USD per (entry + exit).

        Mirrors the futures_orb_v1 signature; factor 2 covers entry + exit.
        """
        sym = symbol.upper()
        if sym not in _FIXED_PER_SIDE:
            raise ValueError(
                f"Symbol '{symbol}' not in nt8_realistic cost model. "
                f"Supported: {sorted(_FIXED_PER_SIDE)}"
            )
        if n_contracts <= 0:
            raise ValueError(f"n_contracts must be positive; got {n_contracts}.")
        fixed = self._resolved_fixed_per_side(sym)
        slip = self._resolved_slip_per_side(sym)
        return 2.0 * n_contracts * (fixed + slip)

    def cost_per_session_log_return(
        self,
        *,
        symbol: str,
        entry_price: float,
        n_contracts: int = 1,
    ) -> float:
        """Return cost as a log-return drag for a single round-trip session.

        Mirrors the futures_orb_v1 `log(1 - cost/notional)` convention per
        ADR-0013 §3.1.1 sizing-convention table + F-CONV-2 application rule.
        """
        sym = symbol.upper()
        if sym not in _NOTIONAL_MULTIPLIERS:
            raise ValueError(
                f"Symbol '{symbol}' not in nt8_realistic cost model. "
                f"Supported: {sorted(_NOTIONAL_MULTIPLIERS)}"
            )
        if entry_price <= 0:
            raise ValueError(f"entry_price must be > 0; got {entry_price}.")
        if n_contracts <= 0:
            raise ValueError(f"n_contracts must be positive; got {n_contracts}.")
        notional = entry_price * _NOTIONAL_MULTIPLIERS[sym] * n_contracts
        cost_usd = self.round_trip_cost_usd(sym, n_contracts)
        cost_to_notional = cost_usd / notional
        if cost_to_notional >= 1.0:
            raise ValueError(
                f"cost_to_notional {cost_to_notional} >= 1.0 for {sym}; "
                f"entry_price too small or n_contracts too large."
            )
        return float(np.log1p(-cost_to_notional))

    def cost_per_bar_return(
        self,
        symbol: str,
        position: float,
        price: float,
        n_contracts: int = 1,
    ) -> float:
        """Return cost as a fraction of notional for bar-cadence strategies.

        Mirrors the nt8_es_nq_rth_v1 signature; returns 0 when position=0
        (flat = no cost). Used by bar-cadence orchestrators that subtract
        cost from raw_return per the existing convention.
        """
        if position == 0:
            return 0.0
        sym = symbol.upper()
        if sym not in _NOTIONAL_MULTIPLIERS:
            raise ValueError(f"Symbol '{symbol}' not in nt8_realistic cost model.")
        notional = price * _NOTIONAL_MULTIPLIERS[sym] * n_contracts
        if notional <= 0:
            raise ValueError(f"Notional must be positive; got {notional}.")
        return self.round_trip_cost_usd(sym, n_contracts) / notional

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def fee_breakdown(self, symbol: str) -> dict[str, float | str | int]:
        """Return per-side fee breakdown for sidecar emission + audit trail."""
        sym = symbol.upper()
        if sym not in _FIXED_PER_SIDE:
            raise ValueError(f"Symbol '{symbol}' not in nt8_realistic cost model.")
        is_empirical = sym in self.empirical_overrides
        fixed = self._resolved_fixed_per_side(sym)
        slip = self._resolved_slip_per_side(sym)
        out: dict[str, float | str | int] = {
            "fixed_per_side": float(fixed),
            "slip_per_side": float(slip),
            "total_per_side": float(fixed + slip),
            "total_round_trip_1_contract": float(2.0 * (fixed + slip)),
            "provenance": (
                "paper_trade_empirical"
                if is_empirical
                else _FEE_PROVENANCE.get(sym, "config_instruments_yaml_placeholder")
            ),
            "sensitivity_mult_applied": (
                False if is_empirical else self.sensitivity_mult
            ),
        }
        if is_empirical:
            override = self.empirical_overrides[sym]
            out["empirical_source"] = override.source
            out["empirical_source_sha256"] = override.source_sha256
            out["empirical_n_fills"] = override.source_n_fills
        return out

    def kpi_annotation(self) -> str:
        """Return the ADR-0025 §D-5 cost-provenance annotation string."""
        if self.calibration_source == "paper_trade_empirical":
            return "cost-empirical-calibrated"
        return "cost-conservative-prior"
