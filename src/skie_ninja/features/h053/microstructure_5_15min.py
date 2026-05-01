"""H053 Block C — 5- and 15-minute microstructure features (24h, ``as_of ≤ 09:45 ET``).

Implements [research/01_hypothesis_register/H053/design.md](
../../../../research/01_hypothesis_register/H053/design.md) §3.3. Six
features computed over the prior 24h ending at the 09:45 ET t anchor:

5-min features (rolling sum/aggregate over 288 5-min bars = 24h):

- ``rv_realized_5m`` — realized variance: ``Σ log(close_t / close_{t-1})²``
  over 288 5-min bars per [Andersen & Bollerslev 1998, IER 39(4):885-905](
  https://doi.org/10.2307/2527343).
- ``rv_parkinson_5m`` — Parkinson estimator: ``(1/(4·ln 2)) · Σ log(H/L)²``
  over 288 5-min bars per [Parkinson 1980, J. Business 53(1):61-65](
  https://doi.org/10.1086/296071).
- ``realized_skew_5m`` — third standardized central moment of 5-min
  log-returns over 288 bars: ``m₃ / σ³`` where ``m₃ = (1/N) Σ (r - μ)³``,
  ``σ² = (1/N) Σ (r - μ)²``, ``μ = (1/N) Σ r``.
- ``ofi_tickrule_5m`` — order-flow-imbalance proxy: ``Σ sign(Δclose)·volume``
  over 288 5-min bars (Lee-Ready 1991 §III tick-test sign rule with
  zero-Δclose carry-forward; same convention as Block D mediator).

15-min features (single most-recent bar ending ≤ 09:45 ET):

- ``range_15m`` — range (high − low) of the most-recent 15-min bar
  ending at 09:45 ET (covers ``[09:30, 09:45) ET``). Raw value; the
  H053 orchestrator applies training-fold ``(mean, sd)`` standardization
  per design.md §3.3 to produce the design.md-named ``range_z_15m``.
- ``volume_15m`` — sum of 1-min bar volumes over the same 15-min window;
  raw value, orchestrator standardizes downstream.

Naming note (F-3 cross-cutting): design.md §3.3 names the standardised
forms ``range_z_15m`` and ``volume_z_15m``. This module emits the raw
values under the un-suffixed names ``range_15m`` and ``volume_15m`` to
honestly reflect the un-standardised state; the orchestrator's
training-fold standardization step produces design.md-named columns.
Tracked under follow-up ``P1-H053-BLOCKC-Z-NAMING-RECONCILE``.

**Halt handling**. Same forward-fill convention as Block B hourly: the
17:00-18:00 ET CME maintenance halt produces no 5-min or 15-min bars;
the rolling 288-bar window operates on the actual 5-min bars present in
the panel. The 24h-prior window may span slightly more than 24 calendar
hours by the halt's missing 5-min bar (12 missing per halt + weekend
gap), so "24h" in the design is approximate. Tracked under follow-up
``P1-H053-BLOCKC-HALT-WINDOW-SEMANTICS`` for design.md §3.3 binding.

**5/15-min bucketing convention**. End-of-bar timestamps per the
project-wide §3.0 R1 convention. A 5-min bar timestamped HH:MM ET
covers ``[HH:MM−5, HH:MM) ET``; the 5 1-min bars timestamped
``HH:MM−4 .. HH:MM`` aggregate into it. Bucketing implementation:
``(ts_event + 4min).dt.truncate("5m")`` rounds each 1-min bar's
timestamp UP to its 5-min bucket end. Same pattern with 14min for
15-min bucketing.

**PIT safety**. ``compute(panel, now, ctx)`` filters ``ts_event ≤ now``
before any aggregation. For session t's predictand at 09:45 ET,
``now ≥ t 09:45 ET`` and the most recent visible bar is the 09:45 ET
1-min bar. The 5-min and 15-min aggregations include this bar (it falls
in the 09:45 ET-timestamped 5-min and 15-min buckets respectively).

References
----------
- Andersen, T. & Bollerslev, T. 1998. *International Economic Review*
  39(4):885-905. [DOI 10.2307/2527343](https://doi.org/10.2307/2527343).
- Parkinson, M. 1980. *J. Business* 53(1):61-65.
  [DOI 10.1086/296071](https://doi.org/10.1086/296071).
- Lee, C. M. C. & Ready, M. J. 1991. *J. Finance* 46(2):733-746.
  [DOI 10.1111/j.1540-6261.1991.tb02683.x](
  https://doi.org/10.1111/j.1540-6261.1991.tb02683.x).
- H053 design.md §3.3 + §3.0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.features.base import DatasetRef
from skie_ninja.features.windowing import _pit_cutoff


_NAME = "h053_microstructure_5_15min"
_VERSION = "1.0"


# Anchor for output-row extraction per design.md §3.3 (`as_of ≤ 09:45 ET`).
# justify: 09:45 ET is the H053 predictand's left endpoint per §3.0 R3-R4.
_ANCHOR_HOUR_ET: int = 9
_ANCHOR_MINUTE_ET: int = 45


# Rolling window: 288 5-min bars = 24h × 60min/h ÷ 5min/bar.
# justify: design.md §3.3 specifies "5-min bars over the prior 24h"; 288
# is the bar count for a continuous 24h window with no halt gaps. With
# halt + weekend the actual time span varies; tracked under follow-up
# `P1-H053-BLOCKC-HALT-WINDOW-SEMANTICS`.
_RV_LOOKBACK_5M_BARS: int = 288


# Parkinson 1980 normalising constant: 1 / (4·ln 2).
# justify: Parkinson 1980 eq. 3 closed-form; pre-computed for floating-
# point reproducibility.
_PARKINSON_COEF: float = 1.0 / (4.0 * math.log(2.0))


@dataclass(frozen=True)
class H053Microstructure5_15min:
    """H053 Block C 5- and 15-minute microstructure feature factory.

    Output schema (6 features + 2 keys):

    - ``ts_event``: UTC timestamp of the 09:45 ET 1-min bar on session t
      (the H053 predictand left-endpoint anchor per §3.0 R3-R4).
    - ``symbol``: ES or NQ (front-month roll-adjusted continuous).
    - ``rv_realized_5m``: realized variance (288 5-min bars).
    - ``rv_parkinson_5m``: Parkinson volatility estimator (288 5-min bars).
    - ``realized_skew_5m``: third standardized central moment of 5-min
      log-returns (288 bars).
    - ``ofi_tickrule_5m``: signed-volume sum (288 5-min bars).
    - ``range_15m``: range of the 09:45 ET-anchored 15-min bar (raw;
      orchestrator standardizes per training-fold to range_z_15m).
    - ``volume_15m``: volume of same 15-min bar (raw; orchestrator
      standardizes to volume_z_15m).
    """

    name: str = _NAME
    version: str = _VERSION

    @property
    def lookback(self) -> pd.Timedelta:
        # 288 5-min bars = 24h plus weekend + holiday coverage.
        # justify: 24h back from 09:45 ET on session t spans the prior
        # session's ETH window; for Monday's predictand the rolling 24h
        # includes Friday-evening ETH (Sunday reopen + Monday overnight).
        # Worst case: Tuesday-after-holiday-Monday = ~5 calendar days of
        # bar absence (holiday Monday + weekend). 7-day Timedelta gives
        # holiday-extended-weekend coverage + 2-day safety margin per
        # F-1-11 audit finding (matches Block B hourly's lookback bump).
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
        return pa.schema(
            [
                pa.field("ts_event", pa.timestamp("ns", tz="UTC"), nullable=False),
                pa.field("symbol", pa.string(), nullable=False),
                pa.field("rv_realized_5m", pa.float64(), nullable=False),
                pa.field("rv_parkinson_5m", pa.float64(), nullable=False),
                pa.field("realized_skew_5m", pa.float64(), nullable=False),
                pa.field("ofi_tickrule_5m", pa.float64(), nullable=False),
                pa.field("range_15m", pa.float64(), nullable=False),
                pa.field("volume_15m", pa.float64(), nullable=False),
            ]
        )

    def compute(
        self,
        panel: pl.LazyFrame,
        now: pd.Timestamp,
        ctx: Any = None,
    ) -> pl.LazyFrame:
        del ctx

        # Step 1: PIT cutoff.
        cutoff = _pit_cutoff(now)
        lf = panel.filter(pl.col("ts_event") <= cutoff).sort(["symbol", "ts_event"])

        # Step 2: ET wall-clock + bucket identifiers.
        # 5-min bucket end-timestamp: (ts_event + 4min).truncate("5m")
        #   — rounds each 1-min bar's end-timestamp UP to its 5-min bucket
        #   end (e.g., 09:01..09:05 ET 1-min bars → 09:05 ET 5-min bucket).
        # 15-min bucket end-timestamp: (ts_event + 14min).truncate("15m").
        lf = lf.with_columns(
            pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et"),
            (pl.col("ts_event") + pl.duration(minutes=4))
            .dt.truncate("5m")
            .alias("_bucket_5m"),
            (pl.col("ts_event") + pl.duration(minutes=14))
            .dt.truncate("15m")
            .alias("_bucket_15m"),
        )

        # Step 3a: F-1-2 audit fix — sign tick rule at 1-min grain BEFORE
        # 5-min aggregation. Block D mediator and the project's
        # ofi_tickrule.py sign at the 1-min input grain; signing at 5-min
        # post-aggregation throws away intra-5min directional information
        # (a 5-min bar with 4 up-ticks + 1 large down-tick getting signed
        # -1 across the entire 5-min volume). Compute 1-min signed volume
        # here, sum into 5-min bucket in Step 3b, then rolling-sum 288
        # buckets in Step 5.
        lf = (
            lf.with_columns(
                (pl.col("close") - pl.col("close").shift(1).over("symbol"))
                .alias("_dclose_1m")
            )
            .with_columns(
                pl.when(pl.col("_dclose_1m") > 0)
                .then(1.0)
                .when(pl.col("_dclose_1m") < 0)
                .then(-1.0)
                .otherwise(None)
                .alias("_sign_raw_1m")
            )
            .with_columns(
                pl.col("_sign_raw_1m")
                .fill_null(strategy="forward")
                .over("symbol")
                .fill_null(0.0)  # F-1-6: first per-symbol bar contributes 0
                .alias("_sign_1m")
            )
            .with_columns(
                (pl.col("_sign_1m") * pl.col("volume").cast(pl.Float64)).alias(
                    "_signed_vol_1m"
                )
            )
        )

        # Step 3b: aggregate 1-min → 5-min OHLCV + signed-volume per
        # (symbol, _bucket_5m). The _bucket_5m timestamp is the END of
        # the 5-min interval. signed_vol_5m = Σ 1-min signed-volumes
        # over the 5 1-min bars in the bucket (preserves intra-5min
        # tick-rule directionality per F-1-2).
        bars_5m = (
            lf.group_by(["symbol", "_bucket_5m"], maintain_order=True)
            .agg(
                pl.col("open").sort_by("ts_event").first().alias("open_5m"),
                pl.col("high").max().alias("high_5m"),
                pl.col("low").min().alias("low_5m"),
                pl.col("close").sort_by("ts_event").last().alias("close_5m"),
                pl.col("volume").sum().cast(pl.Float64).alias("volume_5m"),
                pl.col("_signed_vol_1m").sum().alias("_signed_vol_5m"),
            )
            .sort(["symbol", "_bucket_5m"])
            .collect()
        )

        if bars_5m.is_empty():
            return self._empty_output()

        # Step 4: 5-min log-returns + gap-spanning-return mask (F-1-3 audit).
        # The CME maintenance halt and weekend gaps produce "5-min returns"
        # that span 65min (halt) or ~50hr (weekend); these would inflate
        # rv_realized_5m and bias realized_skew_5m if treated as 5-min
        # observations. Detection: consecutive 5-min bucket timestamps
        # should differ by exactly 5min in normal trading. Replace the
        # log-return at gap-spanning rows with 0.0 (no-information
        # contribution) rather than null (which would break rolling_sum).
        # Same treatment for log(H/L)² which is the input to rv_parkinson.
        bars_5m = bars_5m.with_columns(
            (
                pl.col("_bucket_5m")
                - pl.col("_bucket_5m").shift(1).over("symbol")
            ).alias("_bucket_gap_5m"),
        ).with_columns(
            (pl.col("close_5m") / pl.col("close_5m").shift(1).over("symbol"))
            .log()
            .alias("_r_5m_raw"),
            (pl.col("high_5m") / pl.col("low_5m")).log().alias("_log_hl_5m"),
        ).with_columns(
            # F-1-3: zero out gap-spanning 5-min returns. The shift-spawned
            # null at the first row per symbol stays null and is dropped
            # downstream by .is_finite() guard.
            pl.when(pl.col("_bucket_gap_5m") > pl.duration(minutes=5))
            .then(0.0)
            .otherwise(pl.col("_r_5m_raw"))
            .alias("_r_5m"),
        ).with_columns(
            pl.col("_r_5m").pow(2).alias("_r2_5m"),
            pl.col("_r_5m").pow(3).alias("_r3_5m"),
            pl.col("_log_hl_5m").pow(2).alias("_log_hl2_5m"),
        )

        # Step 5: rolling 288-bar sums for the 4 5-min features.
        rw = _RV_LOOKBACK_5M_BARS
        bars_5m = bars_5m.with_columns(
            pl.col("_r2_5m").rolling_sum(window_size=rw, min_samples=rw).over("symbol").alias("_sum_r2"),
            pl.col("_log_hl2_5m").rolling_sum(window_size=rw, min_samples=rw).over("symbol").alias("_sum_log_hl2"),
            pl.col("_r_5m").rolling_sum(window_size=rw, min_samples=rw).over("symbol").alias("_sum_r"),
            pl.col("_r3_5m").rolling_sum(window_size=rw, min_samples=rw).over("symbol").alias("_sum_r3"),
            pl.col("_signed_vol_5m").rolling_sum(window_size=rw, min_samples=rw).over("symbol").alias("_sum_signed_vol"),
        )

        # Step 6: derive features from rolling sums.
        # rv_realized_5m = Σ r²
        # rv_parkinson_5m = (1/(4 ln 2)) · Σ log(H/L)²
        # ofi_tickrule_5m = Σ (sign · volume)
        # realized_skew_5m: μ = sum_r/N, σ² = (sum_r2/N) − μ²,
        #   m₃ = (sum_r3/N) − 3μ(sum_r2/N) + 2μ³, skew = m₃ / σ³
        bars_5m = bars_5m.with_columns(
            pl.col("_sum_r2").alias("rv_realized_5m"),
            (_PARKINSON_COEF * pl.col("_sum_log_hl2")).alias("rv_parkinson_5m"),
            pl.col("_sum_signed_vol").alias("ofi_tickrule_5m"),
            (pl.col("_sum_r") / float(rw)).alias("_mu"),
        ).with_columns(
            ((pl.col("_sum_r2") / float(rw)) - pl.col("_mu").pow(2)).alias("_sigma2"),
            (
                (pl.col("_sum_r3") / float(rw))
                - 3.0 * pl.col("_mu") * (pl.col("_sum_r2") / float(rw))
                + 2.0 * pl.col("_mu").pow(3)
            ).alias("_m3"),
        ).with_columns(
            # skew = m3 / σ³ ; guard σ²=0 by emitting null (later filtered)
            pl.when(pl.col("_sigma2") > 0)
            .then(pl.col("_m3") / pl.col("_sigma2").pow(1.5))
            .otherwise(None)
            .alias("realized_skew_5m"),
        )

        # Step 7: 15-min bar aggregates (single bar at the 09:45 ET anchor).
        # F-1-15: assert each 15-min bucket has all 15 1-min bars (full
        # coverage); the 09:30→09:45 ET window is critical to the H053
        # thesis and a 12-of-15 bar window understates volume by 20%.
        # Buckets with `count != 15` produce null range_15m / volume_15m
        # via the `.is_finite()` guard at Step 9, dropping the session.
        bars_15m = (
            lf.group_by(["symbol", "_bucket_15m"], maintain_order=True)
            .agg(
                pl.col("high").max().alias("high_15m"),
                pl.col("low").min().alias("low_15m"),
                pl.col("volume").sum().cast(pl.Float64).alias("volume_15m_raw"),
                pl.col("ts_event").count().alias("_bar_count_15m"),
            )
            .with_columns(
                # Emit volume_15m / range_15m only when bar count is exactly 15.
                pl.when(pl.col("_bar_count_15m") == 15)
                .then(pl.col("volume_15m_raw"))
                .otherwise(None)
                .alias("volume_15m"),
                pl.when(pl.col("_bar_count_15m") == 15)
                .then(pl.col("high_15m") - pl.col("low_15m"))
                .otherwise(None)
                .alias("range_15m"),
            )
            .sort(["symbol", "_bucket_15m"])
            .collect()
        )

        # Step 8: extract anchor rows — 5-min and 15-min buckets ending
        # at 09:45 ET on each session.
        bars_5m = bars_5m.with_columns(
            pl.col("_bucket_5m")
            .dt.convert_time_zone("America/New_York")
            .alias("_bucket_5m_et")
        ).with_columns(
            pl.col("_bucket_5m_et").dt.date().alias("_session_date_et"),
            pl.col("_bucket_5m_et").dt.hour().alias("_hour_et"),
            pl.col("_bucket_5m_et").dt.minute().alias("_minute_et"),
        )
        anchor_5m = bars_5m.filter(
            (pl.col("_hour_et") == _ANCHOR_HOUR_ET)
            & (pl.col("_minute_et") == _ANCHOR_MINUTE_ET)
        ).select(
            [
                "symbol",
                "_session_date_et",
                pl.col("_bucket_5m").alias("ts_event_anchor"),
                "rv_realized_5m",
                "rv_parkinson_5m",
                "realized_skew_5m",
                "ofi_tickrule_5m",
            ]
        )

        bars_15m = bars_15m.with_columns(
            pl.col("_bucket_15m")
            .dt.convert_time_zone("America/New_York")
            .alias("_bucket_15m_et")
        ).with_columns(
            pl.col("_bucket_15m_et").dt.date().alias("_session_date_et"),
            pl.col("_bucket_15m_et").dt.hour().alias("_hour_et"),
            pl.col("_bucket_15m_et").dt.minute().alias("_minute_et"),
        )
        anchor_15m = bars_15m.filter(
            (pl.col("_hour_et") == _ANCHOR_HOUR_ET)
            & (pl.col("_minute_et") == _ANCHOR_MINUTE_ET)
        ).select(
            [
                "symbol",
                "_session_date_et",
                "range_15m",
                "volume_15m",
            ]
        )

        merged = anchor_5m.join(
            anchor_15m, on=["symbol", "_session_date_et"], how="inner"
        )

        # Step 9: drop rows where any feature is non-finite (warmup +
        # σ²=0 degenerate cases).
        feature_cols = [
            "rv_realized_5m",
            "rv_parkinson_5m",
            "realized_skew_5m",
            "ofi_tickrule_5m",
            "range_15m",
            "volume_15m",
        ]
        guard = pl.col(feature_cols[0]).is_finite()
        for col in feature_cols[1:]:
            guard = guard & pl.col(col).is_finite()
        merged = merged.filter(guard)

        return merged.select(
            [
                pl.col("ts_event_anchor").cast(pl.Datetime("ns", "UTC")).alias("ts_event"),
                pl.col("symbol"),
                pl.col("rv_realized_5m"),
                pl.col("rv_parkinson_5m"),
                pl.col("realized_skew_5m"),
                pl.col("ofi_tickrule_5m"),
                pl.col("range_15m"),
                pl.col("volume_15m"),
            ]
        ).lazy()

    def _empty_output(self) -> pl.LazyFrame:
        schema: dict[str, pl.DataType] = {
            "ts_event": pl.Datetime("ns", "UTC"),
            "symbol": pl.Utf8,
            "rv_realized_5m": pl.Float64,
            "rv_parkinson_5m": pl.Float64,
            "realized_skew_5m": pl.Float64,
            "ofi_tickrule_5m": pl.Float64,
            "range_15m": pl.Float64,
            "volume_15m": pl.Float64,
        }
        return pl.DataFrame(schema=schema).lazy()

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        """No-op: PIT is enforced by the `_pit_cutoff(now)` filter at the
        top of `compute()` (Step 1). All bucket aggregations + rolling
        windows operate on the post-cutoff frame, so the generic PIT
        invariant `compute(panel, now) == compute(panel.filter(ts<=now), now)`
        is automatic. This stub exists for FeatureModule-shape
        compatibility; the H053 orchestrator does not call it.
        """
        del sample_ts


__all__ = ["H053Microstructure5_15min"]
