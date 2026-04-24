"""Andersen-Bollerslev 1998 realized variance from squared returns.

Formula (Andersen & Bollerslev 1998, eq. 4):

    RV_t(n) = Σ_{i=t-n+1}^{t} r_i²,  r_i = ln(C_i / C_{i-1})

Over a rolling window of ``n`` intra-day squared log-returns, this
converges to the integrated variance ``∫ σ²(s) ds`` under the
continuous-time stochastic-volatility model the paper formalises.

Reference
---------

  - Andersen, T. G. & Bollerslev, T. 1998. "Answering the Skeptics:
    Yes, Standard Volatility Models Do Provide Accurate Forecasts".
    *International Economic Review* 39(4): 885-905.
    https://doi.org/10.2307/2527343

PIT convention
--------------

The log-return at ``t`` uses ``C_t`` and ``C_{t-1}``, both of which
are known at ``t`` (bar has closed). Window includes current bar —
``include_current=True``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.features.base import DatasetRef, register_feature
from skie_ninja.features.windowing import _pit_cutoff

_NAME = "rv_realized"
_VERSION = "1.0"
# Design-doc default; CV in-fold supersedes. See rv_parkinson for rationale.
_DEFAULT_WINDOW_BARS = 60


@dataclass(frozen=True)
class RvRealized:
    """Feature: rolling realized variance from squared log-returns."""

    name: str = _NAME
    version: str = _VERSION
    window_bars: int = _DEFAULT_WINDOW_BARS

    @property
    def lookback(self) -> pd.Timedelta:
        return pd.Timedelta(minutes=self.window_bars + 1)

    @property
    def inputs(self) -> tuple[DatasetRef, ...]:
        return (
            DatasetRef(
                name="vendor_legacy_1min_roll_adjusted",
                columns=("ts_event", "symbol", "close"),
                min_lookback=self.lookback,
            ),
        )

    @property
    def output_schema(self) -> pa.Schema:
        return pa.schema(
            [
                pa.field("ts_event", pa.timestamp("ns", tz="UTC"), nullable=False),
                pa.field("symbol", pa.string(), nullable=False),
                pa.field(
                    f"{_NAME}@{_VERSION}", pa.float64(), nullable=True
                ),
            ]
        )

    def compute(
        self, panel: pl.LazyFrame, now: pd.Timestamp, ctx: Any
    ) -> pl.LazyFrame:
        """Rolling sum of squared log-returns per symbol.

        Log-return column is ``ln(close_t / close_{t-1})``; the
        first bar per symbol is null (no previous close). Rolling
        sum starts once ``window_bars`` valid returns are
        available.
        """
        out_col = f"{_NAME}@{_VERSION}"
        lf = (
            panel.filter(pl.col("ts_event") <= _pit_cutoff(now))
            .sort(["symbol", "ts_event"])
            .with_columns(
                (pl.col("close") / pl.col("close").shift(1).over("symbol"))
                .log()
                .pow(2)
                .alias("_r2")
            )
            .with_columns(
                pl.col("_r2")
                .rolling_sum(
                    window_size=self.window_bars, min_samples=self.window_bars
                )
                .over("symbol")
                .alias(out_col)
            )
        )
        return lf.select(["ts_event", "symbol", out_col])

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        _ = sample_ts


_INSTANCE = RvRealized()
register_feature(_INSTANCE)


__all__ = ["RvRealized"]
