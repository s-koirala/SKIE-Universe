"""Parkinson 1980 high-low realized variance.

Formula (Parkinson 1980, eq. 3):

    σ²_Parkinson = (1 / (4 · ln 2)) · E[ (ln(H/L))² ]

Over a rolling window of ``n`` bars, the estimator becomes:

    σ²_{P,t}(n) = (1 / (4 · n · ln 2)) · Σ_{i=t-n+1}^{t} (ln(H_i/L_i))²

Reference
---------

  - Parkinson, M. 1980. "The Extreme Value Method for Estimating the
    Variance of the Rate of Return". *Journal of Business* 53(1):
    61-65. https://doi.org/10.1086/296503

PIT convention
--------------

Feature at ``t`` uses high/low of bars ``{t-n+1, ..., t}`` — the
current bar *must have closed* (high/low known). The window does NOT
peek beyond ``t``. Passing ``include_current=True`` to the windowing
helper is therefore PIT-safe because the current bar's H/L are by
definition known only after the bar closes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.features.base import DatasetRef, register_feature
from skie_ninja.features.windowing import _pit_cutoff

_NAME = "rv_parkinson"
_VERSION = "1.0"
# Default rolling window in bars. 60 bars at 1-min = 1 hour — the
# canonical design-doc entry for H050 feature-window search (see
# [config/hypotheses/H050.yaml]). CV is applied in-fold per the design
# doc §3 and §4; this module-level default is only used when the
# hypothesis config is absent (e.g., ad-hoc unit tests).
_DEFAULT_WINDOW_BARS = 60


@dataclass(frozen=True)
class RvParkinson:
    """Feature: rolling Parkinson high-low realized variance."""

    name: str = _NAME
    version: str = _VERSION
    window_bars: int = _DEFAULT_WINDOW_BARS

    @property
    def lookback(self) -> pd.Timedelta:
        # 1-min base frequency assumption matches
        # `vendor_legacy_1min_roll_adjusted`.
        return pd.Timedelta(minutes=self.window_bars)

    @property
    def inputs(self) -> tuple[DatasetRef, ...]:
        return (
            DatasetRef(
                name="vendor_legacy_1min_roll_adjusted",
                columns=("ts_event", "symbol", "high", "low"),
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
        """Rolling Parkinson RV on log(H/L)² per bar.

        Implementation uses polars `rolling_mean` on a pre-computed
        `log_hl_sq = ln(H/L)²` column. PIT compliance: the rolling
        window ends at the current row (bar close) — no forward
        reference.
        """
        now_lit = _pit_cutoff(now)
        lf = (
            panel.filter(pl.col("ts_event") <= now_lit)
            .sort(["symbol", "ts_event"])
            .with_columns(
                (pl.col("high") / pl.col("low")).log().pow(2).alias("_log_hl_sq")
            )
        )
        # Rolling mean per symbol (polars rolling is window-close-at-t,
        # which is PIT-safe here because H/L at t are bar-close values).
        out_col = f"{_NAME}@{_VERSION}"
        lf = lf.with_columns(
            pl.col("_log_hl_sq")
            .rolling_mean(window_size=self.window_bars, min_samples=self.window_bars)
            .over("symbol")
            .alias("_mean_log_hl_sq")
        ).with_columns(
            (pl.col("_mean_log_hl_sq") / (4.0 * np.log(2.0))).alias(out_col)
        )
        return lf.select(["ts_event", "symbol", out_col])

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        """No module-specific PIT invariant beyond the generic check."""
        _ = sample_ts


# Register on import.
_INSTANCE = RvParkinson()
register_feature(_INSTANCE)


__all__ = ["RvParkinson"]
