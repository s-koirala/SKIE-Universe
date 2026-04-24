"""OFI proxy via tick rule on 1-min OHLCV bars (pre-registered fallback).

Data-grain caveat (MANDATORY per Cycle-6 brief)
------------------------------------------------

The feature is pre-registered as a tick-rule proxy on 1-min OHLCV.
Documenting honestly:

  - **Cont, Kukanov & Stoikov 2014** ([DOI 10.1093/jjfinec/nbt003],
    arXiv [1011.6402]) define the canonical Order Flow Imbalance
    (OFI) on Level-1 event streams (best-bid/best-ask size and price
    increments). Our 1-min OHLCV panel does NOT carry that grain —
    this module is NOT an implementation of the Cont-Kukanov-Stoikov
    OFI.
  - **Lee & Ready 1991** ([DOI 10.1111/j.1540-6261.1991.tb02683.x])
    is the classical tick-rule primitive: a trade is signed "+1"
    (buyer-initiated) if its price is above the prevailing quote
    mid, "-1" if below, and falls back to the **tick rule** (sign of
    price change vs the preceding trade) on ties. The Lee-Ready
    procedure is defined on *trades with quote context*, not on
    1-min bars. The tick-rule fallback, used in isolation, is what
    we implement here.
  - **Closest defensible peer-reviewed bar-level signed-volume
    analog: Easley, López de Prado & O'Hara 2012** ([DOI
    10.1093/rfs/hhs053]) — the "Bulk Volume Classification" (BVC)
    estimator signs bar volume by the normal-CDF of standardized
    price changes. BVC is a principled bar-grain signed-volume
    estimator; we could use it as an upgrade path, but the
    pre-registered H050 design specifies the simpler tick-rule proxy.

**Implementation (honest statement).** This module signs 1-min bar
volume by ``sign(close_t - close_{t-1})`` — a degenerate
bar-level tick rule. On a zero close-to-close change, the
standard tick-rule convention carries the previous non-zero sign
forward (Lee & Ready 1991 §III.A). The first bar per symbol (no
prior close) carries a zero sign. A rolling sum over the chosen
window yields the OFI proxy value.

**Upgrade path.** This feature is tracked for replacement once the
H010 MBP-10 ingest lands (proper Level-2 book snapshots), at which
point the canonical Cont-Kukanov-Stoikov OFI can be computed. See
Phase-1 follow-up ``P1-H050-OFI-NAMING``.

References
----------

  - Cont, R., Kukanov, A., Stoikov, S. 2014. "The Price Impact of
    Order Book Events". *Journal of Financial Econometrics* 12(1):
    47-88. https://doi.org/10.1093/jjfinec/nbt003
    arXiv: https://arxiv.org/abs/1011.6402
  - Lee, C. M. C. & Ready, M. J. 1991. "Inferring Trade Direction
    from Intraday Data". *Journal of Finance* 46(2): 733-746.
    https://doi.org/10.1111/j.1540-6261.1991.tb02683.x
  - Easley, D., López de Prado, M., O'Hara, M. 2012. "Flow Toxicity
    and Liquidity in a High-Frequency World". *Review of Financial
    Studies* 25(5): 1457-1493. https://doi.org/10.1093/rfs/hhs053

Phase-1 follow-ups
------------------

  - ``P1-H050-OFI-NAMING`` — rename the feature to reflect the
    tick-rule-proxy grain, or replace with BVC / canonical OFI once
    MBP-10 lands.

PIT convention
--------------

Sign at ``t`` depends on ``close_t`` and ``close_{t-1}`` — both
known at bar close. Rolling sum closes at ``t``; no forward
reference. Include-current is PIT-safe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.features.base import DatasetRef, register_feature
from skie_ninja.features.windowing import _pit_cutoff

_NAME = "ofi_tickrule"
_VERSION = "1.0"
_DEFAULT_WINDOW_BARS = 60


@dataclass(frozen=True)
class OfiTickRule:
    """Feature: bar-level OFI proxy via tick rule."""

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
                columns=("ts_event", "symbol", "close", "volume"),
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
        """Rolling signed-volume imbalance ratio (dimensionless, ∈ [-1, +1]).

        Sign is ``sign(close_t - close_{t-1})`` with zero-delta sign-carry
        (forward-fill per Lee-Ready 1991 §III.A). Output is normalized by
        the rolling total volume to yield a scale-independent imbalance ratio.
        """
        out_col = f"{_NAME}@{_VERSION}"
        # Compute raw sign of close-to-close change, with 0 where the
        # change is exactly zero.
        lf = (
            panel.filter(pl.col("ts_event") <= _pit_cutoff(now))
            .sort(["symbol", "ts_event"])
            .with_columns(
                (pl.col("close") - pl.col("close").shift(1).over("symbol"))
                .alias("_dclose")
            )
            .with_columns(
                pl.when(pl.col("_dclose") > 0)
                .then(1.0)
                .when(pl.col("_dclose") < 0)
                .then(-1.0)
                .otherwise(None)
                .alias("_sign_raw")
            )
            # Forward-fill the sign within each symbol: zero-delta
            # carries the last non-zero sign. `fill_null(strategy="forward")`
            # is the polars equivalent of pandas ffill.
            .with_columns(
                pl.col("_sign_raw")
                .fill_null(strategy="forward")
                .over("symbol")
                .fill_null(0.0)  # the first bar per symbol has no prior sign
                .alias("_sign")
            )
            .with_columns(
                (pl.col("_sign") * pl.col("volume").cast(pl.Float64))
                .alias("_signed_vol")
            )
            # Normalize signed-volume sum by total-volume sum over the same
            # window to yield a dimensionless [-1, +1] imbalance ratio.
            # Normalization prevents scale-dependence across symbols (ES vs NQ
            # differ in contract size/volume) and over time (non-stationary
            # volume). Consistent with BVC spirit: Easley, López de Prado &
            # O'Hara 2012, doi:10.1093/rfs/hhs053 §2; Cont, Kukanov & Stoikov
            # 2014, doi:10.1093/jjfinec/nbt003. Fixed 2026-04-24 (R1 F-1-5).
            .with_columns(
                pl.col("volume")
                .cast(pl.Float64)
                .rolling_sum(
                    window_size=self.window_bars, min_samples=self.window_bars
                )
                .over("symbol")
                .alias("_total_vol")
            )
            .with_columns(
                (
                    pl.col("_signed_vol")
                    .rolling_sum(
                        window_size=self.window_bars, min_samples=self.window_bars
                    )
                    .over("symbol")
                    / pl.col("_total_vol")
                ).alias(out_col)
            )
        )
        return lf.select(["ts_event", "symbol", out_col])

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        _ = sample_ts


_INSTANCE = OfiTickRule()
register_feature(_INSTANCE)


__all__ = ["OfiTickRule"]
