"""PIT-safe rolling helpers.

AFML-correct default: a feature at timestamp ``t`` uses data up to
``t-1`` unless the caller explicitly sets ``include_current=True``.
This is the opposite of pandas' default ``rolling(...)`` semantics
where the window closes at ``t``. The rationale is that most of our
features represent *decisions made at t using information through t*,
and the execution convention is that a trade placed at ``t`` uses
features with no reference to any data observed at ``t`` strictly
after the feature is sampled.

Individual feature modules document their own convention:

  - ``rv_parkinson``: uses only high/low of bars strictly before ``t``
    (shift=1). High/Low at ``t`` are not known until the bar closes.
  - ``rv_realized``, ``realized_skew``: use log-returns
    ``log(close_t / close_{t-1})`` so the "current-bar" return is
    known once the bar closes. We include the current bar
    (``include_current=True``).
  - ``ofi_tickrule``: same as ``rv_realized`` — signed volume based on
    close-to-close change; the bar must have closed.

Reference: Lopez de Prado, M. 2018. *Advances in Financial Machine
Learning*, §3.1 "The Fixed-Time Horizon Method" and §7.4 on purge +
embargo — both assume features are computable strictly before the
event they label.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
import polars as pl


def _pit_cutoff(now: pd.Timestamp) -> pl.Expr:
    """Return a polars literal for the PIT cutoff comparable against a
    UTC-tz-aware ``ts_event`` column.

    The vendor-legacy 1-min schema emits ``ts_event`` as
    ``timestamp("ns", tz="UTC")`` (see
    :mod:`skie_ninja.data.ingest.vendor_legacy_1min_roll_adjusted`). A
    tz-naive ``datetime64[ns]`` literal raises a polars SchemaError on
    comparison, so we construct the literal with an explicit UTC tz.
    Callers supply ``now`` as a pandas Timestamp; we normalise to UTC
    (localising naive inputs rather than raising).
    """
    ts = pd.Timestamp(now)
    if ts.tz is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    # Build as a naive ``datetime64[ns]`` literal and re-tag the UTC
    # time-zone via ``dt.replace_time_zone``. This is round-trip-safe
    # across polars 0.x/1.x and matches the panel's column dtype
    # (``Datetime(_, "UTC")``) irrespective of its time-unit (ns vs μs)
    # — polars coerces the unit in the comparison operator but requires
    # the tz to match exactly.
    return pl.lit(ts.to_datetime64()).dt.replace_time_zone("UTC")


def rolling_apply_pit(
    panel: pl.DataFrame | pl.LazyFrame,
    *,
    column: str,
    window: int,
    fn: Callable[[np.ndarray], float],
    min_periods: int,
    group_by: str | None = None,
    include_current: bool = True,
    output_column: str = "rolling_out",
    time_column: str = "ts_event",
) -> pl.LazyFrame:
    """Apply ``fn`` to a rolling window of ``column``, PIT-safe.

    ``fn`` receives a 1-D :class:`numpy.ndarray` of length at most
    ``window`` and returns a scalar. The output column is added to
    the panel alongside the original columns.

    Parameters
    ----------
    panel
        Input frame (eager or lazy). Must contain ``time_column``
        and ``column`` (and ``group_by`` if supplied).
    column
        Column name the rolling window reads from.
    window
        Integer window length (in rows, not in time). Callers
        converting a ``Timedelta`` to rows should do so at the
        panel's base frequency (1-min here) and pass the integer.
    fn
        Pure function from 1-D array to scalar. Must accept arrays
        shorter than ``window`` in the warm-up region; callers signal
        invalidity via ``min_periods``.
    min_periods
        Below this count of valid observations in the window, emit
        ``None`` (nullable column). Mirrors pandas convention.
    group_by
        Optional column name to partition on (typically ``"symbol"``
        so ES and NQ rolling windows are independent). ``None`` uses
        a single global window.
    include_current
        If ``True``, the window for the row at ``t`` includes the
        value at ``t``. If ``False``, the window is shifted by one
        row (AFML-correct "use only pre-``t``" mode).
    output_column
        Name of the emitted column.
    time_column
        Name of the timestamp column used for sort stability.
    """
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window}.")
    if min_periods < 1 or min_periods > window:
        raise ValueError(
            f"min_periods must be in [1, {window}], got {min_periods}."
        )

    lf = panel.lazy() if isinstance(panel, pl.DataFrame) else panel

    # Sort for deterministic iteration.
    sort_cols = [time_column] if group_by is None else [group_by, time_column]
    lf = lf.sort(sort_cols)

    if group_by is None:
        df = lf.collect()
        out = _apply_rolling_groupwise(
            df,
            column=column,
            window=window,
            fn=fn,
            min_periods=min_periods,
            include_current=include_current,
            output_column=output_column,
        )
        return out.lazy()

    # Per-group apply, concatenated back together.
    df = lf.collect()
    groups = df.partition_by(group_by, maintain_order=True)
    pieces = [
        _apply_rolling_groupwise(
            g,
            column=column,
            window=window,
            fn=fn,
            min_periods=min_periods,
            include_current=include_current,
            output_column=output_column,
        )
        for g in groups
    ]
    return pl.concat(pieces, how="vertical").lazy()


def _apply_rolling_groupwise(
    df: pl.DataFrame,
    *,
    column: str,
    window: int,
    fn: Callable[[np.ndarray], float],
    min_periods: int,
    include_current: bool,
    output_column: str,
) -> pl.DataFrame:
    values = df.get_column(column).to_numpy()
    n = len(values)
    out = np.full(n, np.nan, dtype=np.float64)
    mask = np.zeros(n, dtype=bool)
    for i in range(n):
        # Window end (exclusive). When include_current=True the window
        # is (max(0, i+1-window), i+1]; otherwise it is
        # (max(0, i-window), i].
        end = i + 1 if include_current else i
        start = max(0, end - window)
        if end - start < min_periods:
            continue
        w = values[start:end]
        if np.all(np.isnan(w)):
            continue
        w_clean = w[~np.isnan(w)]
        if w_clean.size < min_periods:
            continue
        out[i] = float(fn(w_clean))
        mask[i] = True

    # Emit NaN → Null on invalid positions so downstream schemas with
    # ``nullable=True`` see a true null, not a silent NaN. (Polars
    # Float64 can hold NaN, but the contractual §3.3 check compares
    # `null_count()`.)
    return df.with_columns(
        pl.Series(
            output_column,
            [float(out[i]) if mask[i] else None for i in range(n)],
            dtype=pl.Float64,
        )
    )


__all__ = ["_pit_cutoff", "rolling_apply_pit"]
