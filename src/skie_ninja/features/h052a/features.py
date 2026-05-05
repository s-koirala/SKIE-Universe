"""H052a HMM emission feature implementations.

Per H052a frozen pre-reg + §15.1 errata: 6 features per ``(symbol,
session_date_et)``, computed at the H052a entry timestamp (10:30 ET) using
only data observable at or before that timestamp.

Each ``compute_*`` function takes a 1-min OHLC panel (UTC ``ts_event``
column; RTH-only or RTH+ETH depending on the feature's needs) plus any
auxiliary inputs (e.g., VIX daily panel) and returns a per-session
DataFrame with columns ``[symbol, session_date_et, <feature_col>]``.

The orchestrator at ``scripts/run_h052a_walk_forward.py`` joins the per-
session feature outputs on ``[symbol, session_date_et]`` to produce the
HMM emission matrix.

Constants
---------

- ``_ENTRY_ET`` = "10:30" (design.md §4 entry time)
- ``_RTH_OPEN_ET`` = "09:30" (cash-session open)
- ``_RTH_PRE_OPEN_ET`` = "09:29" (last ETH bar before RTH)
- ``_ETH_START_ET`` = "06:00" (ETH pre-RTH window start)
- ``_RTH_BARS_PER_SESSION`` = 390 (6.5 hr × 60 min)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl


_ENTRY_ET: str = "10:30"
_RTH_OPEN_ET: str = "09:30"
_RTH_PRE_OPEN_ET: str = "09:29"
_ETH_START_ET: str = "06:00"
_RTH_BARS_PER_SESSION: int = 390

H052A_FEATURE_NAMES: tuple[str, ...] = (
    "realized_vol",
    "first_hour_sign",
    "gap_size",
    "dow_mon",
    "dow_tue",
    "dow_wed",
    "dow_thu",
    "eth_pre_rth",
    "vix_daily",
)


def _to_et(panel: pl.DataFrame, time_col: str = "ts_event") -> pd.DataFrame:
    """Project a polars panel to a pandas DataFrame with ET-localised
    ``ts_event_et`` + ``session_date_et`` + ``time_of_day_et`` columns.
    """
    df = panel.to_pandas()
    ts_utc = pd.to_datetime(df[time_col])
    if ts_utc.dt.tz is None:
        ts_utc = ts_utc.dt.tz_localize("UTC")
    ts_et = ts_utc.dt.tz_convert("America/New_York")
    df["ts_utc"] = ts_utc
    df["ts_event_et"] = ts_et
    df["session_date_et"] = ts_et.dt.normalize().dt.tz_convert("UTC")
    df["time_of_day_et"] = ts_et.dt.strftime("%H:%M")
    df["dow_et"] = ts_et.dt.dayofweek  # 0=Mon..6=Sun
    return df


def _at_or_after(df: pd.DataFrame, target_hhmm: str) -> pd.DataFrame:
    """Return first row per session whose ``time_of_day_et`` ≥ target_hhmm."""
    mask = df["time_of_day_et"] >= target_hhmm
    return (
        df.loc[mask]
        .groupby(["symbol", "session_date_et"], as_index=False)
        .first()
    )


def compute_first_hour_sign(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute ``first_hour_sign`` per (symbol, session): sign of log return
    from 09:30 ET close to 10:30 ET close.

    PIT: requires data through 10:30 ET. Computed AT entry time-stamp.
    """
    df = _to_et(panel)
    open_bar = _at_or_after(df, _RTH_OPEN_ET)[
        ["symbol", "session_date_et", "close"]
    ].rename(columns={"close": "_open_close"})
    entry_bar = _at_or_after(df, _ENTRY_ET)[
        ["symbol", "session_date_et", "close"]
    ].rename(columns={"close": "_entry_close"})
    merged = open_bar.merge(entry_bar, on=["symbol", "session_date_et"], how="inner")
    log_ret = np.log(merged["_entry_close"] / merged["_open_close"])
    sign = np.sign(log_ret).astype(np.int64)
    out = merged[["symbol", "session_date_et"]].copy()
    out["first_hour_sign"] = sign
    return pl.from_pandas(out)


def compute_gap_size(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute ``gap_size`` per (symbol, session): log gap from prior-session
    close to current-session open: ``log(open(09:30 ET) / prior_session_close)``.

    Uses the bar at 09:30 ET (current session) and the bar at the LATEST
    available time on the prior session within the panel.

    PIT: requires data through 09:30 ET. Computed at OR before entry time-stamp.
    """
    df = _to_et(panel)
    # Current-session 09:30 close.
    open_bar = _at_or_after(df, _RTH_OPEN_ET)[
        ["symbol", "session_date_et", "close"]
    ].rename(columns={"close": "_open_close"})
    # Prior-session last close per (symbol, session_date_et).
    last_per_session = (
        df.sort_values(["symbol", "ts_utc"])
        .groupby(["symbol", "session_date_et"], as_index=False)
        .last()[["symbol", "session_date_et", "close"]]
        .rename(columns={"close": "_session_last_close"})
    )
    last_per_session = last_per_session.sort_values(["symbol", "session_date_et"])
    last_per_session["_prior_close"] = (
        last_per_session.groupby("symbol")["_session_last_close"].shift(1)
    )
    merged = open_bar.merge(
        last_per_session[["symbol", "session_date_et", "_prior_close"]],
        on=["symbol", "session_date_et"],
        how="left",
    )
    gap = np.log(merged["_open_close"] / merged["_prior_close"])
    out = merged[["symbol", "session_date_et"]].copy()
    out["gap_size"] = gap.astype(np.float64)
    return pl.from_pandas(out)


def compute_dow_onehot(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute ``dow_{mon,tue,wed,thu}`` one-hot per (symbol, session).

    Friday is the reference category (omitted to avoid multicollinearity).
    Per design.md §3 line 56 ("Day-of-week one-hot").

    PIT: known from session_date_et alone; no price data dependency.
    """
    df = _to_et(panel)
    # One row per (symbol, session_date_et), use first row's dow_et.
    sess = (
        df.groupby(["symbol", "session_date_et"], as_index=False)
        .first()[["symbol", "session_date_et", "dow_et"]]
    )
    sess["dow_mon"] = (sess["dow_et"] == 0).astype(np.int64)
    sess["dow_tue"] = (sess["dow_et"] == 1).astype(np.int64)
    sess["dow_wed"] = (sess["dow_et"] == 2).astype(np.int64)
    sess["dow_thu"] = (sess["dow_et"] == 3).astype(np.int64)
    out = sess[["symbol", "session_date_et", "dow_mon", "dow_tue", "dow_wed", "dow_thu"]]
    return pl.from_pandas(out)


def compute_eth_pre_rth(panel: pl.DataFrame) -> pl.DataFrame:
    """Compute ``eth_pre_rth`` per (symbol, session): log return from
    06:00 ET to 09:29 ET.

    Per design.md §3 line 57: "ETH-session pre-RTH returns: 06:00–09:29 ET
    log-return, as a conditioning feature distinguishing 'news-driven
    overnight' from 'quiet overnight.'"

    Requires the substrate to include ETH bars 06:00-09:29 ET. If the
    substrate is RTH-only, this feature returns NaN.

    PIT: requires data through 09:29 ET. Computed at or before entry.
    """
    df = _to_et(panel)
    eth_open_bar = _at_or_after(df, _ETH_START_ET)
    eth_open_bar = eth_open_bar[eth_open_bar["time_of_day_et"] < _RTH_OPEN_ET][
        ["symbol", "session_date_et", "close"]
    ].rename(columns={"close": "_eth_open_close"})
    pre_rth_mask = (df["time_of_day_et"] >= _ETH_START_ET) & (
        df["time_of_day_et"] <= _RTH_PRE_OPEN_ET
    )
    pre_rth_last = (
        df.loc[pre_rth_mask]
        .sort_values(["symbol", "ts_utc"])
        .groupby(["symbol", "session_date_et"], as_index=False)
        .last()[["symbol", "session_date_et", "close"]]
        .rename(columns={"close": "_eth_pre_rth_close"})
    )
    merged = eth_open_bar.merge(
        pre_rth_last, on=["symbol", "session_date_et"], how="inner"
    )
    eth_ret = np.log(merged["_eth_pre_rth_close"] / merged["_eth_open_close"])
    out = merged[["symbol", "session_date_et"]].copy()
    out["eth_pre_rth"] = eth_ret.astype(np.float64)
    return pl.from_pandas(out)


def compute_vix_daily_join(
    sessions: pl.DataFrame,
    vix_daily: pd.DataFrame,
) -> pl.DataFrame:
    """Join VIX daily close on T−1 to a session panel.

    ``sessions`` has columns ``[symbol, session_date_et]`` (one row per
    session). ``vix_daily`` is a pandas DataFrame with columns
    ``[date, vix_close]`` where ``date`` is a calendar date (UTC normalised).

    Per design.md §3 line 58: "VIX daily level, as_of = T−1 close (CBOE).
    Joins on calendar date."

    PIT: T−1 close is observable at the start of session T (after market
    close on T−1 ≤ 16:00 ET); safe at the H052a entry timestamp (10:30 ET
    of session T).
    """
    sess_df = sessions.to_pandas()
    sess_df["session_date_et"] = pd.to_datetime(sess_df["session_date_et"])
    if sess_df["session_date_et"].dt.tz is None:
        sess_df["session_date_et"] = sess_df["session_date_et"].dt.tz_localize("UTC")
    # Normalise to ns precision (post-stall fix 2026-05-05): the polars-to-pandas
    # round-trip emits session_date_et as us-precision while VIX is ms-precision;
    # pd.merge_asof requires identical precision.
    sess_df["session_date_et"] = sess_df["session_date_et"].astype(
        "datetime64[ns, UTC]"
    )
    sess_df = sess_df.sort_values(["symbol", "session_date_et"])
    sess_df["_join_date"] = (
        (sess_df["session_date_et"].dt.normalize() - pd.Timedelta(days=1))
        .astype("datetime64[ns, UTC]")
    )

    vix = vix_daily.copy()
    vix["date"] = pd.to_datetime(vix["date"])
    if vix["date"].dt.tz is None:
        vix["date"] = vix["date"].dt.tz_localize("UTC")
    vix["date"] = vix["date"].astype("datetime64[ns, UTC]")
    vix = vix.sort_values("date")
    # Use merge_asof to handle weekend / holiday lookback to last available T-1.
    merged = pd.merge_asof(
        sess_df.sort_values("_join_date"),
        vix.rename(columns={"date": "_join_date", "vix_close": "vix_daily"}),
        on="_join_date",
        direction="backward",
    )
    out = merged[["symbol", "session_date_et", "vix_daily"]].copy()
    out["vix_daily"] = out["vix_daily"].astype(np.float64)
    return pl.from_pandas(out.sort_values(["symbol", "session_date_et"]).reset_index(drop=True))


def compute_realized_vol_per_session(
    panel: pl.DataFrame,
    *,
    lookback_minutes: int,
) -> pl.DataFrame:
    """Compute realized variance (rv_realized@1.0 analog) AT entry time per
    (symbol, session): sum of squared log-returns over the prior
    ``lookback_minutes`` of 1-min bars ending at the entry bar.

    Per design.md §3 line 53: "Realized variance of log-returns on the
    front-month ratio-adjusted 1-min series, per Andersen & Bollerslev 1998.
    Rolling lookback CV-selected from {30m, 60m, 120m} on training folds."

    Returns annualised σ (= √variance × √(252 × 390)) at the entry timestamp
    for each (symbol, session).

    PIT: bars in (entry_ts − lookback_minutes, entry_ts]; computed at entry.
    """
    df = _to_et(panel)
    df = df.sort_values(["symbol", "ts_utc"])
    df["_log_close"] = np.log(df["close"].astype(np.float64))
    df["_log_return"] = df.groupby("symbol")["_log_close"].diff()

    # For each session, find the entry bar (first bar at-or-after 10:30 ET).
    entry_bars = _at_or_after(df, _ENTRY_ET)[
        ["symbol", "session_date_et", "ts_utc"]
    ].rename(columns={"ts_utc": "_entry_ts_utc"})

    # Rolling sum of squared log-returns over `lookback_minutes` bars per
    # symbol; then pick the value at the entry bar.
    df["_r2"] = df["_log_return"] ** 2
    df["_rv_rolling"] = (
        df.groupby("symbol")["_r2"]
        .rolling(window=lookback_minutes, min_periods=lookback_minutes)
        .sum()
        .reset_index(level=0, drop=True)
    )
    df["_sigma_per_bar"] = np.sqrt(df["_rv_rolling"] / lookback_minutes)
    annualisation = float(np.sqrt(252.0 * _RTH_BARS_PER_SESSION))
    df["realized_vol"] = df["_sigma_per_bar"] * annualisation

    # Inner-join entry bars with df on (symbol, ts_utc) to extract entry-time σ.
    merged = entry_bars.merge(
        df[["symbol", "ts_utc", "realized_vol"]],
        left_on=["symbol", "_entry_ts_utc"],
        right_on=["symbol", "ts_utc"],
        how="inner",
    )
    out = merged[["symbol", "session_date_et", "realized_vol"]].copy()
    out["realized_vol"] = out["realized_vol"].astype(np.float64)
    return pl.from_pandas(out.reset_index(drop=True))


def compute_h052a_features(
    panel: pl.DataFrame,
    *,
    realized_vol_lookback_minutes: int,
    vix_daily: pd.DataFrame,
) -> pl.DataFrame:
    """Compute the full H052a HMM emission feature matrix per session.

    Joins all 6 features (5 listed in :data:`H052A_FEATURE_NAMES`'s 9-column
    expansion + ``realized_vol``) on ``[symbol, session_date_et]``.

    Returns a polars DataFrame with columns:
        symbol, session_date_et, realized_vol, first_hour_sign, gap_size,
        dow_mon, dow_tue, dow_wed, dow_thu, eth_pre_rth, vix_daily

    Rows with any NaN in the feature columns are dropped (consistent with
    H050 + H053 PIT-clean conventions; the orchestrator should warn on
    drop counts).
    """
    rv = compute_realized_vol_per_session(
        panel, lookback_minutes=realized_vol_lookback_minutes
    )
    fhs = compute_first_hour_sign(panel)
    gap = compute_gap_size(panel)
    dow = compute_dow_onehot(panel)
    eth = compute_eth_pre_rth(panel)

    sessions = (
        rv.select(["symbol", "session_date_et"]).unique(maintain_order=True)
    )
    vix = compute_vix_daily_join(sessions, vix_daily)

    out = (
        rv.join(fhs, on=["symbol", "session_date_et"], how="inner")
        .join(gap, on=["symbol", "session_date_et"], how="inner")
        .join(dow, on=["symbol", "session_date_et"], how="inner")
        .join(eth, on=["symbol", "session_date_et"], how="left")
        .join(vix, on=["symbol", "session_date_et"], how="left")
    )
    return out


__all__ = [
    "H052A_FEATURE_NAMES",
    "compute_dow_onehot",
    "compute_eth_pre_rth",
    "compute_first_hour_sign",
    "compute_gap_size",
    "compute_realized_vol_per_session",
    "compute_vix_daily_join",
    "compute_h052a_features",
]
