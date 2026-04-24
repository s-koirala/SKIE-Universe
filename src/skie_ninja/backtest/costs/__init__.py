"""Transaction-cost models for walk-forward backtests.

Each cost model is a callable with signature::

    cost_per_trade(symbol: str, n_contracts: int) -> float

returning total round-trip cost in USD for one trade (open + close,
same direction).  Models are registered by ``cost_model_id`` string.

Implemented
-----------
``nt8_es_nq_rth_v1`` — NinjaTrader Brokerage conservative prior for
ES and NQ RTH sessions; 1-tick constant slippage + published commissions.
"""

from skie_ninja.backtest.costs.nt8_es_nq_rth_v1 import NT8EsNqRthV1CostModel

__all__ = ["NT8EsNqRthV1CostModel"]
