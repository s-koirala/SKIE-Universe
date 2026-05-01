"""H053 Block B — hourly-timeframe (24/7, prior several days).

Implements [research/01_hypothesis_register/H053/design.md](
../../../../research/01_hypothesis_register/H053/design.md) §3.2. Four
feature families computed on the 24/7 ETH+RTH consolidated 1-min substrate:

- ``hourly_returns_lag_k`` for ``k ∈ {1, 2, ..., 24}`` — log-returns at
  hourly resolution, counted backward from the 09:00 ET t=0 anchor.
  ``lag_1`` is the most-recent hourly return ending at the anchor
  (08:00→09:00 ET on session t); ``lag_24`` is the return ending at
  ``anchor - 23h`` (= 10:00 ET on session t-1).

- ``prior_session_vwap_dev`` — ``log(C_{T-1, 16:00 ET} / VWAP_{T-1, RTH})``.
  VWAP over T-1's RTH (09:31..16:15 ET) bars using close-weighted volume:
  ``VWAP = Σ(close · volume) / Σ(volume)``. Numerator is the close of
  the ``16:00 ET-timestamped 1-min bar`` (covers ``[15:59, 16:00) ET``),
  not the RTH-close 16:15 ET bar; design.md §3.2 specifies 16:00 ET
  explicitly (likely anchored to NYSE cash-equity close).

- ``overnight_return`` — ``log(O_{09:30 ET, t} / C_{16:00 ET, T-1})``.
  ``O_{09:30 ET, t}`` is the open of the 09:31 ET bar of session t
  (the §3.0 R5 shorthand for the first RTH bar's open).

- ``pre_open_return`` — ``log(O_{09:30 ET, t} / O_{06:00 ET, t})``.
  ``O_{06:00 ET, t}`` is the open of the 06:01 ET bar of session t
  (analogous shorthand; covers ``[06:00, 06:01) ET``).

**Output anchor**. ``ts_event`` is set to the UTC timestamp of the
09:31 ET bar of session t (the latest input bar required across all
4 feature families); the orchestrator does an asof-join at the
predictand's 09:45 ET timestamp.

**CME maintenance halt** (16:00-17:00 CT = 17:00-18:00 ET daily,
documented in [src/skie_ninja/utils/clock.py](../../utils/clock.py)).
The 17:00 ET clock-hour has no bars in the 1-min panel. To keep
``hourly_returns_lag_k`` indexing by clock-hour stable, hourly closes
are forward-filled across the halt: at the 17:00 ET hour the close
carries from 16:00 ET, so the hourly return at 17:00 ET is 0
(``log(close_t / close_{t-1}) = 0`` after forward-fill). This is the
implementation choice; design.md §3.2 is silent on halt handling.
Tracked under follow-up ``P1-H053-HOURLY-HALT-POLICY`` for design.md
§3.2 binding addendum.

**Gap handling for weekends** (Friday 16:00 CT = 17:00 ET → Sunday
17:00 CT = 18:00 ET reopen). The Saturday/Sunday ETH bars don't
exist; the same forward-fill policy carries Friday's closes through
the weekend so Sunday's pre-open / overnight features are well-
defined relative to Friday's close. The ``overnight_return`` for a
Monday session uses the close of the 16:00 ET bar of *Friday*
(T-1 = the prior trading session, not the prior calendar day).

**PIT safety**. ``compute(panel, now, ctx)`` filters
``ts_event ≤ now`` before any aggregation. For session t's predictand
at 09:45 ET, ``now ≥ t 09:45 ET`` and the most recent visible bar is
the 09:45 ET bar of session t. Block B's latest input is the 09:31
ET bar of session t (= ``O_{09:30 ET, t}`` per §3.0 R5), well before
the PIT cutoff.

**Eager materialization** (F-21 audit). The ``compute()`` method
materializes the input LazyFrame to a DataFrame at Step 3 (
``df_all = lf.collect()``) because the per-symbol forward-fill loop
in Step 5 is implemented eagerly (per-symbol Python iteration over
``pl.datetime_range`` grids). The function signature accepts and
returns ``pl.LazyFrame`` for protocol compatibility, but execution
is fully eager. For ES + NQ × 11 years × 24 hours/day = ~190K hourly
rows, materialization is cheap (~50 MB peak). A future polars-native
rewrite could keep the pipeline lazy; tracked under follow-up
``P1-H053-HOURLY-LAZY-REWRITE``.

**Calendar date vs CME session date** (F-16 audit). The
``_session_date_et`` derivation uses ``_ts_et.dt.date()`` — the
*calendar* date of each bar in ET, not the CME session date (which
labels Sunday-evening ETH bars as part of Monday's session). The
distinction is benign for this module because the per-session anchor
extraction (Step 8) inner-joins on the presence of 09:31 ET, 16:00
ET, and 06:01 ET bars — all RTH or pre-open bars that exist only on
weekday calendar dates. Sunday-evening ETH bars (which would have
``_session_date_et`` = Sunday) drop out of the inner-join and don't
appear in output. Tracked for explicit binding under follow-up
``P1-H053-HOURLY-CME-SESSION-DATE-DOC``.

References
----------
- H053 design.md §3.2 + §3.0 R5.
- [src/skie_ninja/utils/clock.py](../../utils/clock.py) — CME halt
  schedule (HALT_START 16:00 CT = 17:00 ET; HALT_END 17:00 CT
  = 18:00 ET).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.features.base import DatasetRef
from skie_ninja.features.windowing import _pit_cutoff


_NAME = "h053_hourly"
_VERSION = "1.0"


# Anchor for hourly-lag computation per design.md §3.2.
# justify: 09:00 ET anchor is the design.md §3.2 verbatim "09:00 ET t=0";
# 24 lags counted backward → covers 24 hours back from 09:00 ET on session t.
_ANCHOR_HOUR_ET: int = 9
_ANCHOR_MINUTE_ET: int = 0
_N_LAGS: int = 24

# RTH session bounds for VWAP computation (matches Block A daily.py).
# justify: RTH 09:30-16:15 ET per CME equity-index convention; first RTH
# bar 09:31 ET, last RTH bar 16:15 ET.
_RTH_OPEN_ET_HOUR: int = 9
_RTH_OPEN_ET_MINUTE: int = 31
_RTH_CLOSE_ET_HOUR: int = 16
_RTH_CLOSE_ET_MINUTE: int = 15

# Specific bar timestamps referenced in design.md §3.2.
# justify: design.md §3.2 specifies 16:00 ET (NYSE cash-equity close anchor)
# for prior_session_vwap_dev and overnight_return; 09:30/06:00 ET shorthand
# for §3.0 R5 first-bar opens (O_{HH:MM} = open of HH:(MM+1) ET bar).
_C_16_00_ET_HOUR: int = 16
_C_16_00_ET_MINUTE: int = 0
_O_09_30_BAR_HOUR: int = 9
_O_09_30_BAR_MINUTE: int = 31  # bar covering [09:30, 09:31) ET
_O_06_00_BAR_HOUR: int = 6
_O_06_00_BAR_MINUTE: int = 1   # bar covering [06:00, 06:01) ET


@dataclass(frozen=True)
class H053Hourly:
    """H053 Block B hourly-timeframe feature factory.

    Output schema (27 features + 2 keys):

    - ``ts_event``: UTC timestamp of the 09:31 ET bar on session t
      (the latest input bar referenced; orchestrator asof-joins at
      the predictand's 09:45 ET anchor).
    - ``symbol``: ES or NQ (front-month roll-adjusted).
    - ``hourly_returns_lag_1`` .. ``hourly_returns_lag_24``: 24 lag
      features per design.md §3.2.
    - ``prior_session_vwap_dev``: ``log(C_{T-1, 16:00 ET} / VWAP_{T-1, RTH})``.
    - ``overnight_return``: ``log(O_{09:30 ET, t} / C_{16:00 ET, T-1})``.
    - ``pre_open_return``: ``log(O_{09:30 ET, t} / O_{06:00 ET, t})``.
    """

    name: str = _NAME
    version: str = _VERSION

    @property
    def lookback(self) -> pd.Timedelta:
        # 24 hourly lags + weekend + holiday coverage. justify: 24h goes
        # back to 09:00 ET t-1; with weekend gap a Monday's lag_24
        # references 09:00 ET Friday (4 calendar days). With a holiday
        # Monday (e.g., Memorial Day, MLK Day, Juneteenth, Labor Day,
        # Thanksgiving Friday-extended) Tuesday's lag_24 references the
        # Friday-before-the-holiday's 09:00 ET = 5 calendar days back.
        # 7-day Timedelta gives the holiday-extended window + 1-day
        # safety margin (F-12 audit finding).
        return pd.Timedelta(days=7)

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
        fields = [
            pa.field("ts_event", pa.timestamp("ns", tz="UTC"), nullable=False),
            pa.field("symbol", pa.string(), nullable=False),
        ]
        for k in range(1, _N_LAGS + 1):
            fields.append(pa.field(f"hourly_returns_lag_{k}", pa.float64(), nullable=False))
        fields.extend(
            [
                pa.field("prior_session_vwap_dev", pa.float64(), nullable=False),
                pa.field("overnight_return", pa.float64(), nullable=False),
                pa.field("pre_open_return", pa.float64(), nullable=False),
            ]
        )
        return pa.schema(fields)

    def compute(
        self,
        panel: pl.LazyFrame,
        now: pd.Timestamp,
        ctx: Any = None,
    ) -> pl.LazyFrame:
        """Compute the H053 Block B feature vector per (symbol, session_t)."""
        del ctx

        # Step 1: PIT cutoff.
        cutoff = _pit_cutoff(now)
        lf = panel.filter(pl.col("ts_event") <= cutoff).sort(["symbol", "ts_event"])

        # Step 2: ET wall-clock + session_date_et + minute/hour decomposition.
        lf = lf.with_columns(
            pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et")
        ).with_columns(
            pl.col("_ts_et").dt.date().alias("_session_date_et"),
            pl.col("_ts_et").dt.hour().alias("_hour_et"),
            pl.col("_ts_et").dt.minute().alias("_minute_et"),
        )

        # Step 3: collect to materialize for downstream Python-level
        # session-anchor lookup. The hourly aggregation + forward-fill +
        # 24-lag pivot are easiest in materialized DataFrame form.
        # justify: feature is per-session output (~252 sessions/year per
        # symbol), so materialization cost is small.
        df_all = lf.collect()
        if df_all.is_empty():
            return self._empty_output()

        # Step 4: build hourly close series — bars timestamped HH:00 ET
        # (i.e., minute_et == 0). Each row is one hourly close.
        hourly = df_all.filter(pl.col("_minute_et") == 0).select(
            [
                "symbol",
                "ts_event",
                "_ts_et",
                "_session_date_et",
                "_hour_et",
                "close",
            ]
        )

        # Step 5: forward-fill missing clock-hours within each symbol.
        # CME maintenance halt 17:00 ET → no 17:00 ET bar; forward-fill
        # from 16:00 ET keeps lag indexing by clock-hour stable.
        # Construct a complete hourly grid via a (symbol × hour_of_panel)
        # cross-join, then left-join with `hourly` and forward-fill.
        per_symbol_pieces = []
        symbols = sorted(df_all["symbol"].unique().to_list())
        for sym in symbols:
            sub = hourly.filter(pl.col("symbol") == sym).sort("_ts_et")
            if sub.is_empty():
                continue
            # Build complete hourly grid: every hour from min to max in ET.
            min_et = sub["_ts_et"].min()
            max_et = sub["_ts_et"].max()
            grid_et = pl.datetime_range(
                start=min_et,
                end=max_et,
                interval="1h",
                time_zone="America/New_York",
                eager=True,
                closed="both",
            )
            grid = pl.DataFrame(
                {
                    "_ts_et_grid": grid_et,
                    "symbol": [sym] * len(grid_et),
                }
            ).with_columns(
                # Cast to ns precision to match the panel's _ts_et dtype.
                # justify: pl.datetime_range emits us-precision by default;
                # join keys must match exactly on both unit and tz.
                pl.col("_ts_et_grid").cast(pl.Datetime("ns", "America/New_York")),
            ).with_columns(
                pl.col("_ts_et_grid").dt.hour().alias("_hour_et"),
                pl.col("_ts_et_grid").dt.date().alias("_session_date_et"),
            )
            # Left-join with hourly closes; forward-fill close to handle
            # missing halt / weekend hours.
            joined = grid.join(
                sub.select(["_ts_et", "close"]),
                left_on="_ts_et_grid",
                right_on="_ts_et",
                how="left",
            ).sort("_ts_et_grid")
            joined = joined.with_columns(
                pl.col("close").fill_null(strategy="forward").alias("_close_ff")
            )
            # Compute hourly log-return.
            joined = joined.with_columns(
                (pl.col("_close_ff") / pl.col("_close_ff").shift(1)).log().alias(
                    "_hourly_log_return"
                )
            )
            per_symbol_pieces.append(joined)

        if not per_symbol_pieces:
            return self._empty_output()
        hourly_grid = pl.concat(per_symbol_pieces).sort(["symbol", "_ts_et_grid"])

        # Step 6: build the 24 lag columns at each anchor row.
        # Anchor rows are those with hour_et == 09 (regardless of session
        # date); lag_k at anchor is the hourly_log_return shift(k-1) within
        # symbol.
        for k in range(1, _N_LAGS + 1):
            hourly_grid = hourly_grid.with_columns(
                pl.col("_hourly_log_return")
                .shift(k - 1)
                .over("symbol")
                .alias(f"hourly_returns_lag_{k}")
            )

        # Step 7: filter to anchor rows (09:00 ET on each session) — these
        # are the per-session output rows for the lag features.
        anchor_rows = hourly_grid.filter(
            pl.col("_hour_et") == _ANCHOR_HOUR_ET
        ).select(
            ["symbol", "_session_date_et"]
            + [f"hourly_returns_lag_{k}" for k in range(1, _N_LAGS + 1)]
        )

        # Step 8: compute the 3 single-value features per (symbol, session).
        # Need: VWAP_{T-1, RTH}, C_{T-1, 16:00 ET}, O_{09:31 ET, t}, O_{06:01 ET, t}.

        # 8a: per-session anchor bars (one row per (symbol, session_date, anchor type))
        # Build a per-session "anchors" dataframe.
        per_session = self._extract_session_anchors(df_all, symbols)
        if per_session.is_empty():
            return self._empty_output()

        # 8b: VWAP_{T-1, RTH} per (symbol, session_date_et).
        rth_filter = (
            ((pl.col("_hour_et") == _RTH_OPEN_ET_HOUR) & (pl.col("_minute_et") >= _RTH_OPEN_ET_MINUTE))
            | ((pl.col("_hour_et") > _RTH_OPEN_ET_HOUR) & (pl.col("_hour_et") < _RTH_CLOSE_ET_HOUR))
            | ((pl.col("_hour_et") == _RTH_CLOSE_ET_HOUR) & (pl.col("_minute_et") <= _RTH_CLOSE_ET_MINUTE))
        )
        rth = df_all.filter(rth_filter)
        vwap_per_session = (
            rth.group_by(["symbol", "_session_date_et"], maintain_order=True)
            .agg(
                ((pl.col("close") * pl.col("volume").cast(pl.Float64)).sum()
                 / pl.col("volume").cast(pl.Float64).sum()).alias("vwap_rth")
            )
        )

        # Step 9: combine everything per session t.
        # We need per output session t: vwap_dev = log(C_{T-1, 16:00} / vwap_{T-1});
        # overnight = log(O_{09:31, t} / C_{T-1, 16:00});
        # pre_open = log(O_{09:31, t} / O_{06:01, t}).
        # Strategy: build per-session frame keyed by (symbol, session_date_et)
        # with columns {c_16_00_today, o_09_31_today, o_06_01_today}, then
        # join the prior-session's c_16_00 and vwap via a self-asof-join.

        joined = per_session.join(
            vwap_per_session, on=["symbol", "_session_date_et"], how="left"
        )

        # Sort by (symbol, session_date_et) so shift(1) gives the *prior* session.
        # justify: shift(1).over("symbol") gives prior trading session (any gap
        # in calendar days like weekends is preserved as the "prior trading
        # session in the panel"). Per design.md §3.2 wording "T-1" is the
        # prior trading session, not the prior calendar day.
        joined = joined.sort(["symbol", "_session_date_et"]).with_columns(
            pl.col("c_16_00").shift(1).over("symbol").alias("c_16_00_prior"),
            pl.col("vwap_rth").shift(1).over("symbol").alias("vwap_rth_prior"),
        )

        joined = joined.with_columns(
            (pl.col("c_16_00_prior") / pl.col("vwap_rth_prior")).log().alias(
                "prior_session_vwap_dev"
            ),
            (pl.col("o_09_31") / pl.col("c_16_00_prior")).log().alias("overnight_return"),
            (pl.col("o_09_31") / pl.col("o_06_01")).log().alias("pre_open_return"),
        )

        # Step 10: combine lag features + single-value features.
        merged = joined.join(
            anchor_rows, on=["symbol", "_session_date_et"], how="inner"
        )

        # Step 11: drop rows where any feature is non-finite (warmup +
        # missing prior session). Warmup: lag_24 needs 24 hours of history;
        # prior_session_vwap_dev / overnight_return need T-1 to exist;
        # pre_open_return needs the 06:01 ET bar of session t (must be
        # present in panel).
        feature_cols = (
            [f"hourly_returns_lag_{k}" for k in range(1, _N_LAGS + 1)]
            + ["prior_session_vwap_dev", "overnight_return", "pre_open_return"]
        )
        guard = pl.col(feature_cols[0]).is_finite()
        for col in feature_cols[1:]:
            guard = guard & pl.col(col).is_finite()
        merged = merged.filter(guard)

        # Step 12: select output schema.
        return (
            merged.select(
                [
                    pl.col("ts_event_anchor").cast(pl.Datetime("ns", "UTC")).alias("ts_event"),
                    pl.col("symbol"),
                    *[pl.col(f"hourly_returns_lag_{k}") for k in range(1, _N_LAGS + 1)],
                    pl.col("prior_session_vwap_dev"),
                    pl.col("overnight_return"),
                    pl.col("pre_open_return"),
                ]
            ).lazy()
        )

    def _extract_session_anchors(
        self, df_all: pl.DataFrame, symbols: list[str]
    ) -> pl.DataFrame:
        """Per (symbol, session_date_et), extract the 4 anchor-bar values:

        - c_16_00: close of the 16:00 ET bar (today)
        - o_09_31: open of the 09:31 ET bar (today; numerator for overnight + pre_open)
        - o_06_01: open of the 06:01 ET bar (today; denominator for pre_open)
        - ts_event_anchor: ts_event of the 09:31 ET bar (output timestamp)

        Sessions missing any of the 4 bars are excluded from output (the
        downstream `.is_finite()` guard would also catch this, but excluding
        upstream is cleaner).
        """
        # 16:00 ET close — bar timestamped 16:00 ET
        c_16_00 = df_all.filter(
            (pl.col("_hour_et") == _C_16_00_ET_HOUR)
            & (pl.col("_minute_et") == _C_16_00_ET_MINUTE)
        ).select(
            ["symbol", "_session_date_et", pl.col("close").alias("c_16_00")]
        )

        # 09:31 ET open — bar timestamped 09:31 ET
        o_09_31 = df_all.filter(
            (pl.col("_hour_et") == _O_09_30_BAR_HOUR)
            & (pl.col("_minute_et") == _O_09_30_BAR_MINUTE)
        ).select(
            [
                "symbol",
                "_session_date_et",
                pl.col("open").alias("o_09_31"),
                pl.col("ts_event").alias("ts_event_anchor"),
            ]
        )

        # 06:01 ET open — bar timestamped 06:01 ET
        o_06_01 = df_all.filter(
            (pl.col("_hour_et") == _O_06_00_BAR_HOUR)
            & (pl.col("_minute_et") == _O_06_00_BAR_MINUTE)
        ).select(
            ["symbol", "_session_date_et", pl.col("open").alias("o_06_01")]
        )

        # Inner-join all three; sessions with any anchor missing drop out.
        return (
            o_09_31.join(c_16_00, on=["symbol", "_session_date_et"], how="inner")
            .join(o_06_01, on=["symbol", "_session_date_et"], how="inner")
        )

    def _empty_output(self) -> pl.LazyFrame:
        """Empty LazyFrame matching output_schema."""
        schema: dict[str, pl.DataType] = {
            "ts_event": pl.Datetime("ns", "UTC"),
            "symbol": pl.Utf8,
        }
        for k in range(1, _N_LAGS + 1):
            schema[f"hourly_returns_lag_{k}"] = pl.Float64
        schema["prior_session_vwap_dev"] = pl.Float64
        schema["overnight_return"] = pl.Float64
        schema["pre_open_return"] = pl.Float64
        return pl.DataFrame(schema=schema).lazy()

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        del sample_ts


__all__ = ["H053Hourly"]
