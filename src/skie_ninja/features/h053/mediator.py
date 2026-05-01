"""H053 Block D — mediator block (``as_of = 09:45 ET``).

Implements the design.md §3.4 mediator vector ``M_{i,t}`` per
[research/01_hypothesis_register/H053/design.md](
../../../../research/01_hypothesis_register/H053/design.md), with the bar-edge
convention from §3.0:

  - **Mediator-window bar set**: exactly the 15 bars timestamped
    ``{09:31, 09:32, ..., 09:45 ET}`` per session per §3.0 R2. The
    09:45 ET bar is the last mediator-window bar.
  - **No 09:30 ET bar in the convention** per §3.0 R5: ``O_{09:30}``
    shorthand resolves to the open of the 09:31 ET-timestamped bar
    (the first bar covering the half-open interval ``[09:30, 09:31)`` ET).

The 4-feature mediator vector:

- ``m_return`` — ``log(C_{09:45} / O_{09:30})``
  where ``O_{09:30}`` is the open of the 09:31 ET bar (per §3.0 R5)
  and ``C_{09:45}`` is the close of the 09:45 ET bar (also the
  predictand left-endpoint anchor per §3.0 R4).

- ``m_log_range`` — Garman-Klass volatility on the aggregated 15-bar
  OHLC: ``H = max(High over 15 bars)``, ``L = min(Low)``,
  ``O = open of 09:31 ET bar``, ``C = close of 09:45 ET bar``;
  ``GK = 0.5·log(H/L)² − (2·log(2) − 1)·log(C/O)²``. Range-based
  variance estimator per [Garman & Klass 1980](
  https://doi.org/10.1086/296072) (the simple "log-range with C/O drift"
  form; the paper's full estimator with cross-terms is eq. 4. The
  exact equation number for the simple form was not primary-source
  verified in this audit; the paper is paywalled at JSTOR / UChicago
  Press. Hedge follows the project's existing
  ``P1-YANG-ZHANG-EQ8-VERIFY`` pattern; new follow-up
  ``P1-GK1980-EQ6-PRIMARY-VERIFY`` tracks the verification gap. The
  formula coefficients ``0.5`` and ``(2·ln(2)-1)`` are independently
  verified as the canonical GK simple-form per multiple peer-reviewed
  secondary sources; substance is correct.) Aggregated-OHLC
  interpretation of "log-range over the 15 mediator-window bars" is
  the implementation choice; design.md §3.4 is silent on
  aggregated-OHLC vs sum-of-per-bar GK. Binding addendum tracked
  under follow-up ``P1-H053-GK-INTERPRETATION-ADDENDUM``.

- ``m_volume`` — Σ contract-volume over the 15 mediator-window bars.

- ``m_ofi_tickrule`` — Σ (sign(Δclose) · volume) over the 15
  mediator-window bars. Sign at bar ``t`` is
  ``sign(close_t − close_{t-1})``; for the 09:31 ET bar the prior
  close comes from the 09:30 ET data bar (which exists in the raw
  panel even though §3.0 R5 excludes 09:30 ET from the mediator-window
  bar set — a *prior-bar reference* on the underlying data, PIT-safe).
  The shift+fill_null are partitioned by ``(symbol, _session_date_et)``
  so the 09:31 ET bar's prior reference is the 09:30 ET bar of the
  *same* session, not an unrelated bar from the prior session's RTH
  close or ETH stream. Zero-Δclose carries the previous non-zero sign
  forward per [Lee & Ready 1991](
  https://doi.org/10.1111/j.1540-6261.1991.tb02683.x) §III "tick test"
  (the §III.A sub-anchor was not primary-source verified — paywalled at
  Wiley; the project's prior audit at
  ``docs/audits/audit_trail_2026-04-24_cycle6-h050-feature-factory.md``
  flagged the same paywall gap for the sibling
  ``ofi_tickrule.py``; new follow-up ``P1-LR1991-III-A-PRIMARY-VERIFY``
  tracks). The first bar of a session (no prior close in same session)
  carries sign 0.

**Output grain**: one row per ``(symbol, session_date_et)`` with
``ts_event`` set to the 09:45 ET-timestamped bar's UTC equivalent
(the design.md §3.0 R4 boundary anchor). Sessions whose 09:31-09:45 ET
window is empty (full-day closures: New Year's Day, Christmas,
extraordinary closures per [src/skie_ninja/utils/clock.py](
../../utils/clock.py)) produce no output row — there is no mediator
to report on a closed session.

**PIT safety**: the ``compute(panel, now, ctx)`` filters
``ts_event ≤ now`` before anything else. Aggregations over the
mediator window use only bars whose timestamps are within
``[09:31 ET, 09:45 ET]`` of a session whose 09:45 ET ≤ now. The
prior-close reference for OFI sign extends one bar earlier (09:30 ET)
which is also within the panel's PIT cutoff. No 09:46+ ET bars are
read.

**Bar-edge regression gate**: the §3.0 R1-R6 binding is anchored in
[tests/unit/test_h053_bar_edge_convention.py](
../../../../tests/unit/test_h053_bar_edge_convention.py); this module
relies on the convention transitively through the
``ts_et.dt.hour() == 9`` filter `& (minute ∈ [31, 45])`.

References
----------
- Garman, M. B. & Klass, M. J. 1980. "On the Estimation of Security
  Price Volatilities from Historical Data." *J. Business* 53(1):67-78.
  [DOI 10.1086/296072](https://doi.org/10.1086/296072).
- Lee, C. M. C. & Ready, M. J. 1991. "Inferring Trade Direction from
  Intraday Data." *J. Finance* 46(2):733-746.
  [DOI 10.1111/j.1540-6261.1991.tb02683.x](
  https://doi.org/10.1111/j.1540-6261.1991.tb02683.x).
- H053 design.md §3.0 + §3.4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa

from skie_ninja.features.base import DatasetRef
from skie_ninja.features.h053._constants import GK_C_OVER_O_COEF
from skie_ninja.features.windowing import _pit_cutoff


_NAME = "h053_mediator"
_VERSION = "1.0"


# F-1-12: GK_C_OVER_O_COEF imported from the shared `_constants` module
# so daily.py and mediator.py share a single source of truth. See
# `_constants.py` for derivation + `P1-GK1980-EQ6-PRIMARY-VERIFY`
# follow-up on the eq.-number anchor verification gap.


# Mediator-window bar-set definition per design.md §3.0 R2.
# Bars timestamped {09:31, 09:32, ..., 09:45 ET}, exactly 15 bars.
# justify: hour and minute constants are §3.0 R2 verbatim, locked by
# the test_h053_bar_edge_convention regression gate.
_MEDIATOR_HOUR_ET: int = 9
_MEDIATOR_MIN_FIRST: int = 31  # first mediator-window bar timestamp
_MEDIATOR_MIN_LAST: int = 45   # last mediator-window bar timestamp (boundary anchor)
_EXPECTED_MEDIATOR_BAR_COUNT: int = 15  # |{31..45}|


@dataclass(frozen=True)
class H053Mediator:
    """H053 Block D mediator block (per-session 4-feature aggregate).

    Output schema (4 mediator features + 2 keys):

    - ``ts_event``: timestamp of the 09:45 ET bar in UTC (boundary anchor).
    - ``symbol``: ES or NQ (front-month roll-adjusted continuous).
    - ``m_return``: log-return over the mediator window.
    - ``m_log_range``: Garman-Klass volatility on aggregated OHLC.
    - ``m_volume``: sum of bar volumes.
    - ``m_ofi_tickrule``: signed-volume sum (Lee-Ready tick rule).

    Distinct from the project's bar-grain ``FEATureModule`` Protocol —
    H053 features produce per-session rows, not per-bar rolling values.
    """

    name: str = _NAME
    version: str = _VERSION

    @property
    def lookback(self) -> pd.Timedelta:
        # Mediator window plus one prior bar (for OFI sign reference at 09:31 ET).
        # justify: the §3.0 R2 mediator window {09:31..09:45 ET} spans 15
        # minutes (16 bar-edge timestamps). The 09:31 ET bar's OFI sign
        # references close_{09:30 ET} as a prior-bar reference; lookback must
        # include one bar (one minute) before the mediator window.
        # 16-min Timedelta covers the 15-min mediator span + 1-min OFI
        # prior-bar lookback bound.
        return pd.Timedelta(minutes=16)

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
                pa.field("m_return", pa.float64(), nullable=False),
                pa.field("m_log_range", pa.float64(), nullable=False),
                pa.field("m_volume", pa.float64(), nullable=False),
                pa.field("m_ofi_tickrule", pa.float64(), nullable=False),
            ]
        )

    def compute(
        self,
        panel: pl.LazyFrame,
        now: pd.Timestamp,
        ctx: Any = None,
    ) -> pl.LazyFrame:
        """Aggregate the H053 mediator vector per (symbol, session_date_et).

        Parameters
        ----------
        panel : pl.LazyFrame
            1-min OHLCV bars with columns ``ts_event`` (UTC timestamp),
            ``symbol``, ``open``, ``high``, ``low``, ``close``, ``volume``.
            Source: ``vendor_legacy_1min_roll_adjusted``.
        now : pd.Timestamp
            PIT cutoff. Only bars with ``ts_event ≤ now`` are read.
        ctx : Any
            Unused; present for FeatureModule-shape compatibility.

        Returns
        -------
        pl.LazyFrame
            One row per (symbol, session) with the 4 mediator features.
            Columns match ``output_schema`` exactly.
        """
        del ctx  # unused; FeatureModule-shape compatibility only

        # Step 1: PIT cutoff. All downstream operations see only bars at or before now.
        cutoff = _pit_cutoff(now)
        lf = panel.filter(pl.col("ts_event") <= cutoff).sort(["symbol", "ts_event"])

        # Step 2: derive ET wall-clock + session_date_et FIRST so the Lee-Ready
        # sign step (Step 3) can session-partition. F-1-2 / F-1-3 bug fix:
        # without session partitioning, the 09:31 ET bar's sign at session N
        # could reference an unrelated bar from session N-1 (e.g., 16:15 ET
        # close of prior RTH, or any ETH bar) instead of the 09:30 ET bar of
        # the same session. Lee-Ready 1991 §III.A's forward-fill convention
        # implicitly assumes continuous trading; cross-session carry-forward
        # produces silently-wrong OFI values. Partitioning the shift + the
        # fill_null by (symbol, _session_date_et) scopes the prior-bar
        # reference to the same trading day.
        lf = lf.with_columns(
            pl.col("ts_event").dt.convert_time_zone("America/New_York").alias("_ts_et")
        ).with_columns(
            pl.col("_ts_et").dt.date().alias("_session_date_et"),
            pl.col("_ts_et").dt.hour().alias("_hour_et"),
            pl.col("_ts_et").dt.minute().alias("_minute_et"),
        )

        # Step 3: compute Lee-Ready tick-rule sign per bar, partitioned by
        # (symbol, _session_date_et). The 09:31 ET sign references the 09:30
        # ET bar of the SAME session (PIT-safe; both bars are within the same
        # ET calendar date and well before the mediator-window upper bound).
        # Convention from src/skie_ninja/features/microstructure/ofi_tickrule.py:
        #   sign = sign(close_t - close_{t-1}); 0-Δclose carries forward the
        #   last non-zero sign per Lee-Ready 1991 §III.A; first bar of session
        #   (no prior close in same session) carries sign 0.
        lf = (
            lf.with_columns(
                (
                    pl.col("close")
                    - pl.col("close").shift(1).over(["symbol", "_session_date_et"])
                ).alias("_dclose")
            )
            .with_columns(
                pl.when(pl.col("_dclose") > 0)
                .then(1.0)
                .when(pl.col("_dclose") < 0)
                .then(-1.0)
                .otherwise(None)
                .alias("_sign_raw")
            )
            .with_columns(
                pl.col("_sign_raw")
                .fill_null(strategy="forward")
                .over(["symbol", "_session_date_et"])
                .fill_null(0.0)
                .alias("_sign")
            )
            .with_columns(
                (pl.col("_sign") * pl.col("volume").cast(pl.Float64))
                .alias("_signed_vol")
            )
        )

        # Step 4: identify mediator-window bars by ET wall-clock per §3.0 R2.
        # Filter on hour=9, minute ∈ [31, 45].
        lf = lf.filter(
            (pl.col("_hour_et") == _MEDIATOR_HOUR_ET)
            & (pl.col("_minute_et") >= _MEDIATOR_MIN_FIRST)
            & (pl.col("_minute_et") <= _MEDIATOR_MIN_LAST)
        )

        # Step 4: aggregate per (symbol, session_date_et). The .first() / .last()
        # require sort-stability over the prior sort by ts_event, which polars
        # group_by preserves (maintain_order=True is default-True for
        # group_by_dynamic but we use plain group_by; explicit sort upstream is
        # the guarantee).
        agg = lf.group_by(["symbol", "_session_date_et"], maintain_order=True).agg(
            pl.col("ts_event").last().alias("ts_event"),
            pl.col("open").first().alias("_open_first"),
            pl.col("close").last().alias("_close_last"),
            pl.col("high").max().alias("_high_max"),
            pl.col("low").min().alias("_low_min"),
            pl.col("volume").sum().cast(pl.Float64).alias("m_volume"),
            pl.col("_signed_vol").sum().alias("m_ofi_tickrule"),
            pl.col("ts_event").count().alias("_bar_count"),
        )

        # Step 5: derive m_return + m_log_range from aggregated OHLC.
        # F-1-15: m_return is computed once and reused inside m_log_range
        # via pow(2) rather than re-computing the log ratio (single source
        # of truth for log(C/O); polars optimiser CSE not guaranteed across
        # versions).
        agg = agg.with_columns(
            (pl.col("_close_last") / pl.col("_open_first")).log().alias("m_return"),
        ).with_columns(
            # Garman-Klass simple-form (paywalled-equation-number; see module
            # docstring) on aggregated 15-bar OHLC:
            # Component A: 0.5 * log(H/L)²
            # Component B: -(2·ln 2 - 1) * log(C/O)²  ← reuses m_return = log(C/O)
            (
                0.5 * (pl.col("_high_max") / pl.col("_low_min")).log().pow(2)
                - GK_C_OVER_O_COEF * pl.col("m_return").pow(2)
            ).alias("m_log_range")
        )

        # Step 6: reject sessions with incomplete mediator-window coverage.
        # An RTH session that is open will have all 15 bars; a session with
        # missing bars (data outage) is excluded rather than silently producing
        # a partial mediator. justify: design.md §3.4 binds the 4-feature vector
        # to "the 15 mediator-window bars" — partial coverage violates the
        # binding. Use of ``= 15`` here is the §3.0 R2 expected count, not a
        # tunable threshold.
        agg = agg.filter(pl.col("_bar_count") == _EXPECTED_MEDIATOR_BAR_COUNT)

        # Step 7: F-1-4 guard — drop rows where any of the 4 mediator
        # features is non-finite. Garman-Klass §V notes the simple-form
        # estimator can yield negative variance for thin windows; on the
        # 15-bar aggregated OHLC of a low-liquidity session this is
        # rare but possible. log(C/O) at near-zero open or log(H/L) at
        # H ≤ L (impossible for valid OHLC but not validated upstream)
        # produces -inf / NaN. The output_schema declares all four as
        # nullable=False, so any non-finite escape would violate the
        # contract — we drop at this gate rather than emit NaN. Counts
        # of dropped sessions are not currently logged; tracked under
        # follow-up ``P1-H053-MEDIATOR-DROP-TELEMETRY``.
        agg = agg.filter(
            pl.col("m_return").is_finite()
            & pl.col("m_log_range").is_finite()
            & pl.col("m_volume").is_finite()
            & pl.col("m_ofi_tickrule").is_finite()
        )

        # F-1-7: explicitly cast ts_event to the schema-declared
        # Datetime("ns", "UTC") dtype. The upstream sort + group_by
        # path inherits the panel's unit; this cast is idempotent if
        # the upstream is already ns-precision but enforces dtype-stability
        # across polars versions and across panels with us-precision
        # ts_event upstream.
        return agg.select(
            [
                pl.col("ts_event").cast(pl.Datetime("ns", "UTC")),
                "symbol",
                "m_return",
                "m_log_range",
                "m_volume",
                "m_ofi_tickrule",
            ]
        )

    def validate_point_in_time(self, sample_ts: pd.Timestamp) -> None:
        """Optional FeatureModule-shape PIT hook; the generic
        ``ts_event <= now`` filter at the top of ``compute`` is the
        load-bearing PIT guard, exercised by ``test_h053_mediator``
        synthetic fixtures.
        """
        del sample_ts


__all__ = ["H053Mediator"]
