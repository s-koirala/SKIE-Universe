"""Realized skewness of log-returns.

Third central moment of log-returns over a rolling window,
standardized by the cube of the sample standard deviation:

    skew_t(n) = (1/n · Σ (r_i - r_bar)^3) / (1/n · Σ (r_i - r_bar)²)^{3/2}

This is the population-form "realized skewness" estimator used in
Neuberger 2012 and subsequent literature on return-distribution
higher moments. The population form (divisor ``n`` rather than the
Fisher-Pearson unbiased ``n/((n-1)(n-2))``) is standard in realized
higher-moment papers; use the population form for consistency with
``rv_parkinson`` and ``rv_realized`` which also use window-length
divisors.

Reference
---------

  - Neuberger, A. 2012. "Realized Skewness". *Review of Financial
    Studies* 25(11): 3423-3455. https://doi.org/10.1093/rfs/hhs101
    — Neuberger defines realized skewness with per-bar log-returns,
    though the aggregation is via a different functional form
    (not the third-moment / vol³ ratio); the sample third-moment
    ratio is the practitioner shorthand used in most backtest code
    (e.g., Amaya et al. 2015 JFE 118: 135-167).
  - Amaya, D., Christoffersen, P., Jacobs, K., Vasquez, A. 2015.
    "Does realized skewness predict the cross-section of equity
    returns?". *Journal of Financial Economics* 118(1): 135-167.
    https://doi.org/10.1016/j.jfineco.2015.02.009 — Section 2.2
    defines the same third-moment ratio used here.

PIT convention
--------------

Rolling window closes at ``t`` — log-returns through ``t`` are
known once bar ``t`` closes. No forward reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.features.base import DatasetRef, register_feature
from skie_ninja.features.windowing import _pit_cutoff

_NAME = "realized_skew"
_VERSION = "1.0"
_DEFAULT_WINDOW_BARS = 60


@dataclass(frozen=True)
class RealizedSkew:
    """Feature: rolling realized skewness of log-returns."""

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
        """Rolling third central moment ratio over log-returns."""
        out_col = f"{_NAME}@{_VERSION}"
        lf = (
            panel.filter(pl.col("ts_event") <= _pit_cutoff(now))
            .sort(["symbol", "ts_event"])
            .with_columns(
                (pl.col("close") / pl.col("close").shift(1).over("symbol"))
                .log()
                .alias("_r")
            )
        )
        w = self.window_bars
        # E[r^k] over the rolling window, k = 1, 2, 3. Subtract mean
        # cubed and mean^3 per the expansion
        # E[(r - μ)^3] = E[r^3] - 3μE[r²] + 2μ^3.
        lf = lf.with_columns(
            [
                pl.col("_r")
                .rolling_mean(window_size=w, min_samples=w)
                .over("symbol")
                .alias("_m1"),
                pl.col("_r")
                .pow(2)
                .rolling_mean(window_size=w, min_samples=w)
                .over("symbol")
                .alias("_m2"),
                pl.col("_r")
                .pow(3)
                .rolling_mean(window_size=w, min_samples=w)
                .over("symbol")
                .alias("_m3"),
            ]
        ).with_columns(
            [
                (pl.col("_m2") - pl.col("_m1").pow(2)).alias("_var"),
                (
                    pl.col("_m3")
                    - 3.0 * pl.col("_m1") * pl.col("_m2")
                    + 2.0 * pl.col("_m1").pow(3)
                ).alias("_cm3"),
            ]
        ).with_columns(
            pl.when(pl.col("_var") > 0)
            .then(pl.col("_cm3") / pl.col("_var").pow(1.5))
            .otherwise(None)
            .alias(out_col)
        )
        return lf.select(["ts_event", "symbol", out_col])

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        _ = sample_ts


_INSTANCE = RealizedSkew()
register_feature(_INSTANCE)


__all__ = ["RealizedSkew"]
