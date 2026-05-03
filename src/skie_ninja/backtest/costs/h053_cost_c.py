"""H053 cost-c derivation: per-symbol round-trip cost in log-return units.

Per [plan/h053_stage3_v3_plan_2026-05-03.md](../../../../plan/h053_stage3_v3_plan_2026-05-03.md) §B.

Derives the cost-of-round-trip ``c`` (in log-return units) per symbol from
[config/instruments.yaml](../../../../config/instruments.yaml) +
[NT8EsNqRthV1CostModel](nt8_es_nq_rth_v1.py). Used as the threshold for the
cost-aware binary calibration KPI ``d_c = 1 if y > c`` (Class B exhibit
in H053 Stage-3 v3 per design.md §4.5.3 + ADR-0013 walk-forward-grid+CI
amendment).

Cost-c arithmetic
-----------------

For symbol ``s`` with round-trip cost ``$X`` (USD) on a contract whose notional
at price ``p`` is ``p * multiplier``, the cost-of-round-trip in log-return units
is::

    c(s, p) = X / (p * multiplier)

Approximated to bps as ``c * 1e4``. For H053 (RTH-only ES + NQ), the median IS-fold
prices yield (R2-corrected per Round-1 plan-audit F-1-1):

    ES: $29.10 round-trip / $275,000 notional ≈ 1.06 bps  (1-tick prior)
    NQ: $14.10 round-trip / $400,000 notional ≈ 0.35 bps  (1-tick prior)

Sensitivity arms (per ``NT8EsNqRthV1CostModel.sensitivity_mult``):

    ES 2-tick: $54.10 / $275,000 ≈ 1.97 bps
    NQ 2-tick: $24.10 / $400,000 ≈ 0.60 bps

Both ``c`` magnitudes are well below the per-session predictand σ
(~50-100 bps for the 09:45→10:30 ET ES/NQ slice), so the cost-aware
binarization ``d_c = 1 if y > c`` is essentially indistinguishable from
the binding ``d = 1 if y > 0`` in expected outcome distribution. The
cost-aware exhibit therefore documents marginal sensitivity, not a
substantively different signal — appropriate for a Class B KPI per
ADR-0012 §"Class B".

References
----------
- [config/instruments.yaml](../../../../config/instruments.yaml) — canonical
  CME exchange + clearing fees + tick values.
- [NT8EsNqRthV1CostModel](nt8_es_nq_rth_v1.py) — round-trip USD computation.
- ADR-0012 §"Class B" — KPI exhibit framework.
- Plan v3-r3 §B — calibration redesign (binding gate stays binary BSS;
  cost-aware binary BSS becomes Class B KPI exhibit only).
"""

from __future__ import annotations

from dataclasses import dataclass

from skie_ninja.backtest.costs.nt8_es_nq_rth_v1 import NT8EsNqRthV1CostModel


@dataclass(frozen=True)
class H053CostC:
    """Per-symbol cost-c in log-return units, computed from a reference price.

    Parameters
    ----------
    symbol : str
        Instrument root (``"ES"`` or ``"NQ"``).
    reference_price : float
        Reference price for notional computation (typically median of IS-fold
        close prices).
    sensitivity_mult : float
        Tick-sensitivity multiplier passed to ``NT8EsNqRthV1CostModel``.
        ``1.0`` = 1-tick prior; ``2.0`` = 2-tick worst-case sensitivity arm.
    """

    symbol: str
    reference_price: float
    sensitivity_mult: float = 1.0

    def round_trip_usd(self) -> float:
        """Round-trip cost in USD per ``NT8EsNqRthV1CostModel``."""
        model = NT8EsNqRthV1CostModel(sensitivity_mult=self.sensitivity_mult)
        return model.round_trip_cost(self.symbol, n_contracts=1)

    def notional_usd(self) -> float:
        """Reference notional in USD = ``reference_price * multiplier``."""
        multipliers = {"ES": 50.0, "NQ": 20.0, "MES": 5.0, "MNQ": 2.0}
        sym = self.symbol.upper()
        if sym not in multipliers:
            raise ValueError(f"Symbol '{self.symbol}' not in H053 cost-c map.")
        return self.reference_price * multipliers[sym]

    def c_log_return(self) -> float:
        """Cost-c in log-return units = ``round_trip_usd / notional_usd``.

        At ``c`` ≈ 1e-4 the difference between log-return and arithmetic-return
        cost is < 1e-8 (Taylor: ``log(1 - c) ≈ -c - c²/2 ≈ -c`` for c ≈ 1e-4),
        so this approximation is exact to machine precision for the H053
        regime.
        """
        notional = self.notional_usd()
        if notional <= 0:
            raise ValueError(f"Notional must be positive; got {notional}")
        return self.round_trip_usd() / notional

    def c_bps(self) -> float:
        """Cost-c in basis points = ``c_log_return * 1e4``."""
        return self.c_log_return() * 1e4


def derive_cost_c(
    symbol: str,
    reference_price: float,
    *,
    sensitivity_mults: tuple[float, ...] = (1.0, 2.0),
) -> dict[str, H053CostC]:
    """Build a sensitivity ladder of ``H053CostC`` for a (symbol, price) pair.

    Returns a dict keyed by ``f"{int(mult)}-tick"`` (e.g., ``"1-tick"``,
    ``"2-tick"``). Used by the calibration module's cost-aware binary BSS
    KPI exhibit.
    """
    return {
        f"{int(mult)}-tick": H053CostC(
            symbol=symbol,
            reference_price=reference_price,
            sensitivity_mult=mult,
        )
        for mult in sensitivity_mults
    }


__all__ = [
    "H053CostC",
    "derive_cost_c",
]
