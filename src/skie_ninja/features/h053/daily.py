"""H053 Block A — daily-timeframe features (``as_of = T-1 close``).

Implements [research/01_hypothesis_register/H053/design.md](
../../../../research/01_hypothesis_register/H053/design.md) §3.1. Five
features computed on a daily-grain OHLCV series derived from the 1-min
RTH substrate (CME equity-index futures regular session
08:30-15:15 CT = 09:30-16:15 ET):

- ``log_close_minus_sma50`` — ``log(C_{T-1} / SMA_{50, T-1})``.
- ``log_close_minus_sma200`` — ``log(C_{T-1} / SMA_{200, T-1})``.
- ``daily_realized_range_n`` — N-day rolling Garman-Klass log-range
  estimator applied to daily aggregated OHLC. The window ``N`` is a
  hyperparameter selected by training-fold CV from ``{20, 60, 120}``
  per design.md §3.1; this module exposes ``window_days`` as a
  dataclass field, and the orchestrator instantiates one
  ``H053Daily`` per candidate.
- ``weekly_trend_slope`` — rolling OLS log-price slope over the prior
  5 sessions. The full slope (not just sign) is retained per design.md.
- ``daily_yz_vol`` — Yang-Zhang volatility per
  :func:`skie_ninja.features.labels.yang_zhang_volatility` applied to
  the daily OHLC series. The lookback is parametric; design.md §3.1
  is silent on its value, so a default of 20 days is used and the
  ambiguity is tracked under follow-up
  ``P1-H053-DAILY-YZ-LOOKBACK-DESIGN-PIN``.

**Daily aggregation convention** (RTH-only). Bars are end-of-bar
timestamped per the §3.0 R1 convention enforced by
[tests/unit/test_h053_bar_edge_convention.py](
../../../../tests/unit/test_h053_bar_edge_convention.py); RTH for
ES/NQ futures runs 09:30-16:15 ET. The daily OHLC per (symbol,
session_date_et) is constructed as:

  - ``daily_open`` = open of the first RTH bar (09:31 ET-timestamped;
    covers ``[09:30, 09:31)``).
  - ``daily_high`` = max of High over all RTH bars.
  - ``daily_low`` = min of Low over all RTH bars.
  - ``daily_close`` = close of the last RTH bar (16:15 ET-timestamped).
  - ``daily_ts_event`` = the ts_event of the 16:15 ET-timestamped bar
    (UTC equivalent) — the "T-1 close" anchor.

ETH bars (overnight + early-morning) are excluded from the daily
aggregation. Sessions with incomplete RTH coverage (data outage; not
a full 405-bar RTH window) are dropped from the output, matching the
mediator block's incomplete-session convention.

**Early-close session policy (F-1-1).** CME equity-index futures
have ~7-10 early-close sessions per year (day-after-Thanksgiving,
July 3, December 24, etc.) closing at 12:00 CT = 13:00 ET, producing
~210 RTH bars instead of 405. The current implementation drops these
under the 405-bar gate. design.md §3.1 does NOT pre-register an
early-close policy; the drop-policy is the implementation choice
documented here for transparency. Tracked under follow-up
``P1-H053-DAILY-EARLY-CLOSE-POLICY`` for design.md §3.1 addendum that
formally binds the chosen policy. **Operational consequence**: SMA50
/ SMA200 / GK / slope / YZ windows are over **kept-sessions** (full
RTH coverage), not calendar-trading-sessions; ~3-4% of training-fold
sessions are excluded silently. The orchestrator's per-fold session
count audit (downstream consumer) should account for this.

**GK interpretation (F-1-6).** The "N-day rolling Garman-Klass log-
range" computation in this module applies the GK simple-form to the
N-day **window-aggregated OHLC**: ``H = max-High over N days``,
``L = min-Low``, ``O = open at session t-N+1``, ``C = close at
session t``. This matches the H053Mediator's per-session-window
construction and gives an estimator of *window-level* range
volatility, NOT a rolling mean of per-day GK contributions. design.md
§3.1 ("Garman-Klass log-range estimator") is silent on this choice.
Tracked under follow-up ``P1-H053-DAILY-GK-INTERPRETATION-ADDENDUM``
(extends the existing ``P1-H053-GK-INTERPRETATION-ADDENDUM`` from the
mediator audit) for a binding design.md addendum.

**PIT safety**. The ``compute(panel, now, ctx)`` filters
``ts_event ≤ now`` before any aggregation. For session T's predictand
at 09:45 ET, ``now ≥ T 09:45 ET`` and the most recent visible daily
bar is the T-1 16:15 ET close. The output ``ts_event = T-1 16:15 ET``
in UTC; the orchestrator does an asof-join to align Block A features
with the predictand timestamp.

**SMA-200 warmup**. SMA200 needs ≥200 prior trading sessions; the
practical lookback is ~290 calendar days. Output rows produced before
day-200 carry the appropriate NaN per the
``yang_zhang_volatility`` warm-up convention but are dropped at the
end so all returned rows have all 5 features finite.

References
----------
- Garman, M. B. & Klass, M. J. 1980. "On the Estimation of Security
  Price Volatilities from Historical Data." *J. Business* 53(1):67-78.
  [DOI 10.1086/296072](https://doi.org/10.1086/296072) (the simple
  log-range with C/O drift form; equation-number anchor unverified per
  ``P1-GK1980-EQ6-PRIMARY-VERIFY``).
- Parkinson, M. 1980. "The Extreme Value Method for Estimating the
  Variance of the Rate of Return." *J. Business* 53(1):61-65.
  [DOI 10.1086/296071](https://doi.org/10.1086/296071) — sibling
  range-based estimator from the same JB issue (cited in design.md
  §3.1 alongside GK).
- Yang, D. & Zhang, Q. 2000. "Drift-Independent Volatility Estimation
  Based on High, Low, Open, and Close Prices." *J. Business*
  73(3):477-491. [DOI 10.1086/209650](https://doi.org/10.1086/209650).
- H053 design.md §3.1 + §3.0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.features.base import DatasetRef
from skie_ninja.features.h053._constants import GK_C_OVER_O_COEF
from skie_ninja.features.labels import yang_zhang_volatility
from skie_ninja.features.windowing import _pit_cutoff


_NAME = "h053_daily"
_VERSION = "1.0"


# F-1-12: GK_C_OVER_O_COEF is imported from the shared `_constants` module
# so daily.py and mediator.py share a single source of truth. The
# constant value is `2·ln(2) − 1 ≈ 0.3862944`; see `_constants.py`
# for derivation + `P1-GK1980-EQ6-PRIMARY-VERIFY` follow-up.


# RTH session bounds for CME equity-index futures (ES, NQ).
# justify: 09:30 ET → 16:15 ET defines the RTH session per
# [config/instruments.yaml](../../../../config/instruments.yaml) and
# [src/skie_ninja/utils/clock.py](../../utils/clock.py) (RTH_OPEN
# 08:30 CT, RTH_CLOSE 15:15 CT, both equivalent to 09:30 / 16:15 ET).
# End-of-bar convention per §3.0 R1: first RTH bar timestamped 09:31 ET
# (covers [09:30, 09:31)); last RTH bar timestamped 16:15 ET.
_RTH_OPEN_ET_HOUR: int = 9
_RTH_OPEN_ET_MINUTE: int = 31     # first RTH bar timestamp
_RTH_CLOSE_ET_HOUR: int = 16
_RTH_CLOSE_ET_MINUTE: int = 15    # last RTH bar timestamp
# Expected RTH bar count per session: 405 bars covering 09:31..16:15 ET.
# justify: the half-open interval [09:30, 16:15) ET = 6h45min = 405 min.
# End-of-bar timestamps {09:31, 09:32, ..., 16:15} → |range| = 405.
_EXPECTED_RTH_BAR_COUNT: int = 405


# Feature-window defaults per design.md §3.1.
# justify: SMA50 / SMA200 are explicit design.md §3.1 windows;
# weekly_trend_slope window 5 is the design.md §3.1 "prior 5 sessions";
# daily_yz_vol default 20 days is implementation choice (design.md §3.1
# is silent — see follow-up `P1-H053-DAILY-YZ-LOOKBACK-DESIGN-PIN`).
_SMA50_WINDOW: int = 50
_SMA200_WINDOW: int = 200
_WEEKLY_SLOPE_WINDOW: int = 5
_DEFAULT_YZ_LOOKBACK: int = 20
_DEFAULT_GK_WINDOW: int = 60   # mid-grid choice from design.md §3.1 {20, 60, 120}


@dataclass(frozen=True)
class H053Daily:
    """H053 Block A daily-timeframe feature factory.

    Output schema (5 features + 2 keys):

    - ``ts_event``: timestamp of the T-1 16:15 ET RTH-close bar (UTC).
    - ``symbol``: ES or NQ (front-month roll-adjusted continuous).
    - ``log_close_minus_sma50``: ``log(C / SMA_50)`` at T-1 close.
    - ``log_close_minus_sma200``: ``log(C / SMA_200)`` at T-1 close.
    - ``daily_realized_range_n``: GK simple-form on ``window_days``
      daily-aggregated OHLC. The output column name reflects the chosen
      ``window_days`` (e.g., ``daily_realized_range_60``).
    - ``weekly_trend_slope``: OLS slope of log-close on day-index over
      the prior ``slope_window`` sessions.
    - ``daily_yz_vol``: Yang-Zhang vol over ``yz_lookback`` daily bars.

    Caller-facing parameters (all caller-overridable for CV):
    """

    name: str = _NAME
    version: str = _VERSION
    window_days: int = _DEFAULT_GK_WINDOW
    yz_lookback: int = _DEFAULT_YZ_LOOKBACK
    slope_window: int = _WEEKLY_SLOPE_WINDOW

    def __post_init__(self) -> None:
        if self.window_days < 2:
            raise ValueError(
                f"window_days must be >= 2 for GK rolling; got {self.window_days}."
            )
        if self.yz_lookback < 2:
            raise ValueError(
                f"yz_lookback must be >= 2 for Yang-Zhang; got {self.yz_lookback}."
            )
        if self.slope_window < 2:
            raise ValueError(
                f"slope_window must be >= 2 for OLS; got {self.slope_window}."
            )

    @property
    def lookback(self) -> pd.Timedelta:
        # Maximum window = SMA200 (200 sessions). 200 sessions ≈ 290 calendar
        # days at ~252 sessions/year. Add a safety margin for non-trading
        # days (weekends + holidays) and the daily-aggregation upstream.
        # justify: 300-day Timedelta covers SMA200 + ~5% safety margin for
        # extremely-long-holiday years (e.g., late-November Thanksgiving +
        # December Christmas + New-Year stretches; F-1-17 audit finding).
        # Not a tunable threshold but a structural lookback bound derived
        # from design.md §3.1 SMA200 (200 sessions × ~1.45 calendar/session
        # + safety margin).
        return pd.Timedelta(days=300)

    @property
    def inputs(self) -> tuple[DatasetRef, ...]:
        return (
            DatasetRef(
                name="vendor_legacy_1min_roll_adjusted",
                columns=("ts_event", "symbol", "open", "high", "low", "close", "volume"),
                min_lookback=self.lookback,
            ),
        )

    @property
    def output_schema(self) -> pa.Schema:
        gk_col = f"daily_realized_range_{self.window_days}"
        return pa.schema(
            [
                pa.field("ts_event", pa.timestamp("ns", tz="UTC"), nullable=False),
                pa.field("symbol", pa.string(), nullable=False),
                pa.field("log_close_minus_sma50", pa.float64(), nullable=False),
                pa.field("log_close_minus_sma200", pa.float64(), nullable=False),
                pa.field(gk_col, pa.float64(), nullable=False),
                pa.field("weekly_trend_slope", pa.float64(), nullable=False),
                pa.field("daily_yz_vol", pa.float64(), nullable=False),
            ]
        )

    def compute(
        self,
        panel: pl.LazyFrame,
        now: pd.Timestamp,
        ctx: Any = None,
    ) -> pl.LazyFrame:
        """Aggregate 1-min RTH → daily OHLCV per (symbol, session_date_et),
        then compute the 5 daily-timeframe features."""
        del ctx

        # Step 1: PIT cutoff.
        cutoff = _pit_cutoff(now)
        lf = panel.filter(pl.col("ts_event") <= cutoff).sort(["symbol", "ts_event"])

        # Step 2: derive ET wall-clock + session_date_et; filter to RTH window
        # (09:31..16:15 ET inclusive on both endpoints, matching the §3.0 R1
        # end-of-bar convention).
        lf = lf.with_columns(
            pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et")
        ).with_columns(
            pl.col("_ts_et").dt.date().alias("_session_date_et"),
            pl.col("_ts_et").dt.hour().alias("_hour_et"),
            pl.col("_ts_et").dt.minute().alias("_minute_et"),
        )

        # RTH filter: 09:31 <= ts_et <= 16:15 ET. Use a hand-rolled
        # comparison rather than .dt.time() since polars time-of-day
        # comparisons require a `pl.time` literal not always trivial
        # to construct portably across versions.
        in_rth = (
            ((pl.col("_hour_et") == _RTH_OPEN_ET_HOUR) & (pl.col("_minute_et") >= _RTH_OPEN_ET_MINUTE))
            | ((pl.col("_hour_et") > _RTH_OPEN_ET_HOUR) & (pl.col("_hour_et") < _RTH_CLOSE_ET_HOUR))
            | ((pl.col("_hour_et") == _RTH_CLOSE_ET_HOUR) & (pl.col("_minute_et") <= _RTH_CLOSE_ET_MINUTE))
        )
        lf = lf.filter(in_rth)

        # Step 3: aggregate to daily OHLCV per (symbol, session_date_et).
        # F-1-7: explicit `.sort_by("ts_event")` inside the agg makes the
        # `first()` / `last()` semantics deterministic regardless of
        # whether the upstream sort survives the `with_columns` + `filter`
        # chain (it should under polars LAZY plan semantics, but the
        # explicit sort is cheap insurance against future polars version
        # changes or interleaved-row inputs).
        # F-1-21: `daily_volume` is computed and never consumed; dropped.
        daily = lf.group_by(["symbol", "_session_date_et"], maintain_order=True).agg(
            pl.col("ts_event").sort().last().alias("daily_ts_event"),
            pl.col("open").sort_by("ts_event").first().alias("daily_open"),
            pl.col("high").max().alias("daily_high"),
            pl.col("low").min().alias("daily_low"),
            pl.col("close").sort_by("ts_event").last().alias("daily_close"),
            pl.col("ts_event").count().alias("_rth_bar_count"),
        )

        # Step 4: drop sessions with incomplete RTH coverage (data outage).
        # An RTH session must have all 405 bars; partial sessions are excluded.
        # justify: 405-bar bound is the §3.0 R1 end-of-bar convention's
        # consequence on the 09:31..16:15 ET RTH range, not a tunable threshold.
        # Early-close days (e.g., day-after-Thanksgiving 12:00 CT close)
        # produce shorter windows and are correctly excluded; the H053
        # design has no special handling for shortened sessions.
        daily = daily.filter(pl.col("_rth_bar_count") == _EXPECTED_RTH_BAR_COUNT)

        # Step 5: collect to materialize the daily series for rolling computations.
        # The numpy-based YZ + OLS slope require materialized arrays; polars
        # rolling primitives handle SMA50 / SMA200 / GK natively.
        daily_df = (
            daily.sort(["symbol", "_session_date_et"])
            .with_columns(
                pl.col("daily_close").log().alias("_log_close"),
            )
            .collect()
        )

        if daily_df.is_empty():
            return self._empty_output()

        # Step 6: rolling SMAs + GK (per-symbol). Polars handles these
        # natively without a Python-level loop.
        daily_df = daily_df.with_columns(
            pl.col("daily_close")
            .rolling_mean(window_size=_SMA50_WINDOW, min_samples=_SMA50_WINDOW)
            .over("symbol")
            .alias("_sma50"),
            pl.col("daily_close")
            .rolling_mean(window_size=_SMA200_WINDOW, min_samples=_SMA200_WINDOW)
            .over("symbol")
            .alias("_sma200"),
        ).with_columns(
            (pl.col("daily_close") / pl.col("_sma50")).log().alias("log_close_minus_sma50"),
            (pl.col("daily_close") / pl.col("_sma200")).log().alias("log_close_minus_sma200"),
        )

        # Step 7: rolling Garman-Klass on aggregated N-day OHLC.
        # GK_simple = 0.5·(log(H/L))² − (2·ln 2 − 1)·(log(C/O))² applied to
        # the rolling-window-aggregated OHLC: H = max High over N days,
        # L = min Low over N days, O = open at day t-N+1, C = close at day t.
        gk_col = f"daily_realized_range_{self.window_days}"
        daily_df = daily_df.with_columns(
            pl.col("daily_high")
            .rolling_max(window_size=self.window_days, min_samples=self.window_days)
            .over("symbol")
            .alias("_gk_h"),
            pl.col("daily_low")
            .rolling_min(window_size=self.window_days, min_samples=self.window_days)
            .over("symbol")
            .alias("_gk_l"),
            # _gk_o = open at the *first* bar of the window. Polars has no
            # "rolling_first" primitive; emulate via shift(window_days - 1).
            pl.col("daily_open").shift(self.window_days - 1).over("symbol").alias("_gk_o"),
            # _gk_c = close of the current bar (window's right edge).
            pl.col("daily_close").alias("_gk_c"),
        ).with_columns(
            (
                0.5 * (pl.col("_gk_h") / pl.col("_gk_l")).log().pow(2)
                - GK_C_OVER_O_COEF * (pl.col("_gk_c") / pl.col("_gk_o")).log().pow(2)
            ).alias(gk_col)
        )

        # Step 8: rolling OLS slope of log-close on day-index over
        # `slope_window` sessions (per design.md §3.1 "prior 5 sessions").
        # Closed-form: slope = Cov(x, y) / Var(x); for x = [0..N-1] which is
        # constant per window, Var(x) = (N²-1)/12 (N=5 → Var=2). The slope
        # at day t uses the trailing N days inclusive of t (right-closed).
        #
        # justify: the closed-form approach uses rolling primitives only;
        # avoids per-window numpy.polyfit calls that would slow large panels.
        # The formula b = (N · Σxy - Σx · Σy) / (N · Σx² - (Σx)²) is
        # algebraically equivalent to scipy.stats.linregress(x, y).slope.
        n = self.slope_window
        # x = [0, 1, ..., n-1]; constants:
        sum_x = float(n * (n - 1) / 2)              # Σ x
        sum_x2 = float((n - 1) * n * (2 * n - 1) / 6)  # Σ x² = n(n-1)(2n-1)/6
        denom_const = n * sum_x2 - sum_x * sum_x

        # Compute the per-window Σxy via a manual sum-of-shifts. Σxy =
        # Σ_{i=0..n-1} i * y_{t-(n-1)+i} = 0·y_{t-(n-1)} + 1·y_{t-(n-2)} +
        # ... + (n-1)·y_t. This is implementable as a sum of weighted
        # shifted columns.
        sum_xy_expr = pl.lit(0.0)
        for i in range(n):
            # i corresponds to weight i; the y-value at this position is
            # y shifted by (n-1-i) bars (so i=0 weight is at the oldest bar).
            shift_amount = (n - 1) - i
            term = pl.col("_log_close").shift(shift_amount).over("symbol") * float(i)
            sum_xy_expr = sum_xy_expr + term

        # Σy over the trailing n bars
        sum_y_expr = pl.col("_log_close").rolling_sum(
            window_size=n, min_samples=n
        ).over("symbol")

        daily_df = daily_df.with_columns(
            ((n * sum_xy_expr - sum_x * sum_y_expr) / denom_const).alias("weekly_trend_slope")
        )

        # Step 9: Yang-Zhang vol via the existing project numpy function.
        # Iterate per symbol; assemble arrays and call yang_zhang_volatility.
        # F-1-15: `sorted()` makes per-symbol iteration deterministic across
        # polars versions / hash-bucket implementations (polars unique()
        # is hash-bucket-ordered by default).
        # F-1-22: empty sub-frames are skipped; the helper would not handle
        # zero-length arrays gracefully even though `lookback < 2` is the
        # only documented raise condition.
        symbols = sorted(daily_df["symbol"].unique().to_list())
        yz_pieces = []
        for sym in symbols:
            sub = daily_df.filter(pl.col("symbol") == sym).sort("_session_date_et")
            if len(sub) == 0:
                continue
            yz = yang_zhang_volatility(
                open_=sub["daily_open"].to_numpy(),
                high=sub["daily_high"].to_numpy(),
                low=sub["daily_low"].to_numpy(),
                close=sub["daily_close"].to_numpy(),
                lookback=self.yz_lookback,
            )
            piece = sub.with_columns(
                pl.Series("daily_yz_vol", yz, dtype=pl.Float64)
            )
            yz_pieces.append(piece)
        if not yz_pieces:
            return self._empty_output()
        daily_df = pl.concat(yz_pieces).sort(["symbol", "_session_date_et"])

        # Step 10: drop warmup rows where any feature is non-finite.
        # SMA200 needs 200 sessions, GK needs window_days, OLS needs
        # slope_window, YZ needs yz_lookback. The most stringent is SMA200.
        # The .is_finite() guard catches all warmup nulls + any pathological
        # NaN/Inf the rolling stats might produce.
        feature_cols = [
            "log_close_minus_sma50",
            "log_close_minus_sma200",
            gk_col,
            "weekly_trend_slope",
            "daily_yz_vol",
        ]
        guard = pl.col(feature_cols[0]).is_finite()
        for col in feature_cols[1:]:
            guard = guard & pl.col(col).is_finite()
        daily_df = daily_df.filter(guard)

        # Step 11: select output columns + cast ts_event to ns precision.
        return daily_df.lazy().select(
            [
                pl.col("daily_ts_event").cast(pl.Datetime("ns", "UTC")).alias("ts_event"),
                pl.col("symbol"),
                pl.col("log_close_minus_sma50"),
                pl.col("log_close_minus_sma200"),
                pl.col(gk_col),
                pl.col("weekly_trend_slope"),
                pl.col("daily_yz_vol"),
            ]
        )

    def _empty_output(self) -> pl.LazyFrame:
        """Return a properly-typed empty LazyFrame matching output_schema.

        Required when the input panel has no RTH bars at all (e.g., panel
        consists only of ETH overnight bars or full-day-closure dates).
        """
        gk_col = f"daily_realized_range_{self.window_days}"
        empty = pl.DataFrame(
            schema={
                "ts_event": pl.Datetime("ns", "UTC"),
                "symbol": pl.Utf8,
                "log_close_minus_sma50": pl.Float64,
                "log_close_minus_sma200": pl.Float64,
                gk_col: pl.Float64,
                "weekly_trend_slope": pl.Float64,
                "daily_yz_vol": pl.Float64,
            }
        )
        return empty.lazy()

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        del sample_ts


__all__ = ["H053Daily"]
