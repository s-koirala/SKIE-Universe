"""H062 feature factory composition layer.

Per H062 design.md §3, the feature factory composes:
  - Donchian channel (rolling N-bar high/low on close; close-to-close basis
    per Faith 2007 Turtle System 1/2 *practitioner*).
  - ATR (Wilder 1978 *practitioner*) via H055 atr.py re-export.
  - Trend filter ID_1 (4 candidates: TSMOM / ADX / OLS-slope-t / MA-cross)
    via H055 trend_identifiers.py re-export.
  - First-fire breakout-event detector with H_dwell re-arm.
  - News-time exclusion via news_calendar.py re-export.

Public surface:
  - H062FeatureConfig: frozen config dataclass.
  - H062Features:      frozen container of computed feature arrays.
  - compute_h062_features: factory composition entry point.

PIT-causality: every feature is computed at bar-t close using only data
available at or before bar t. The channel uses closes through bar (t-1);
the breakout event compares bar-t close to the (t-1)-anchored channel.
This is the canonical event-driven backtest semantic per López de Prado
2018 *AFML* §13 (*practitioner*).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from skie_ninja.features.h055.atr import atr_wilder
from skie_ninja.features.h055.trend_identifiers import (
    trend_id_a_ts_mom,
    trend_id_b_adx,
    trend_id_c_hac_ols_slope_t,
    trend_id_d_ma_cross,
)
from skie_ninja.features.h062.donchian import (
    DonchianChannel,
    donchian_breakout_events,
    donchian_channel,
    first_fire_filter,
)

__all__ = [
    "H062FeatureConfig",
    "H062Features",
    "compute_h062_features",
    "select_trend_id_side",
]

_VALID_TREND_IDS = frozenset({"a_ts_mom", "b_adx", "c_hac_ols_slope_t", "d_ma_cross"})


@dataclass(frozen=True)
class H062FeatureConfig:
    """Per-bar feature factory config for H062.

    Fields per design.md §3 + §5 hyperparameter grids:
        channel_n: Donchian channel lookback in 5-min bars.
            Grid per §3: {20, 40, 60, 120, 240, 480}.
        atr_n: Wilder ATR lookback in 5-min bars.
            Grid per §3: {14, 21, 60}.
        h_dwell: First-fire re-arm dwell in 5-min bars.
            Grid per §3: {1, 2, 5, 10}.
        trend_id: Selected trend-filter identifier.
            One of {"a_ts_mom", "b_adx", "c_hac_ols_slope_t", "d_ma_cross"}.
        trend_id_lookback_l: Trend-filter lookback in 5-min bars.
        trend_id_threshold: Trend-filter threshold (τ_M / τ_ADX / τ_t / τ_MA
            depending on trend_id selection).
        trend_id_short_window: Short SMA window for trend_id_d_ma_cross only.
        trend_id_long_window:  Long  SMA window for trend_id_d_ma_cross only.
    """

    channel_n: int
    atr_n: int
    h_dwell: int
    trend_id: str
    trend_id_lookback_l: int
    trend_id_threshold: float
    trend_id_short_window: int = 0
    trend_id_long_window: int = 0

    def __post_init__(self) -> None:
        if self.channel_n < 1:
            raise ValueError(f"channel_n must be >= 1, got {self.channel_n}")
        if self.atr_n < 1:
            raise ValueError(f"atr_n must be >= 1, got {self.atr_n}")
        if self.h_dwell < 1:
            raise ValueError(f"h_dwell must be >= 1, got {self.h_dwell}")
        if self.trend_id not in _VALID_TREND_IDS:
            raise ValueError(
                f"trend_id {self.trend_id!r} not in {sorted(_VALID_TREND_IDS)}"
            )
        if self.trend_id == "d_ma_cross":
            if self.trend_id_short_window < 1:
                raise ValueError(
                    "trend_id_d_ma_cross requires trend_id_short_window >= 1"
                )
            if self.trend_id_long_window <= self.trend_id_short_window:
                raise ValueError(
                    "trend_id_d_ma_cross requires "
                    "trend_id_long_window > trend_id_short_window"
                )


@dataclass(frozen=True)
class H062Features:
    """Per-bar H062 feature container.

    Fields:
        channel: DonchianChannel object with channel_high/channel_low/N/init.
        atr:           1-D float ATR_n array (Wilder smoothing).
        trend_side:    1-D int8 array, per-bar trend filter side ∈ {+1, 0, -1}.
        raw_events:    Pre-filter breakout events per
            ``donchian_breakout_events``.
        filtered_events: First-fire-filtered breakout events per
            ``first_fire_filter``.
        eligible_events: filtered_events × trend_id-gate-pass mask.
            See §1 below for the gate semantic.
        config: The H062FeatureConfig that generated these features.

    Gate semantic for ``eligible_events``:
        Per design.md §3 + §4: long entries require trend_side ∈ {+1, 0}
        (i.e., NOT down); short entries require trend_side ∈ {-1, 0} (i.e.,
        NOT up). The 0 ("no trend / threshold not met") side ADMITS BOTH
        directions per the H055 §3 Component 1 convention.
    """

    channel: DonchianChannel
    atr: np.ndarray
    trend_side: np.ndarray
    raw_events: np.ndarray
    filtered_events: np.ndarray
    eligible_events: np.ndarray
    config: H062FeatureConfig


def select_trend_id_side(
    config: H062FeatureConfig,
    *,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    log_prices: np.ndarray,
) -> np.ndarray:
    """Dispatch trend_id selection to the H055 trend_identifiers primitive.

    Returns a per-bar side ∈ {+1, 0, -1} int8 array.

    Args:
        config: H062FeatureConfig with trend_id field selecting the family.
        high, low, close: OHLC 1-D arrays (matched length).
        log_prices: 1-D log-close array (matched length).
    """
    if config.trend_id == "a_ts_mom":
        sides = trend_id_a_ts_mom(
            log_prices,
            lookback_l=config.trend_id_lookback_l,
            tau_m=config.trend_id_threshold,
        )
    elif config.trend_id == "b_adx":
        sides = trend_id_b_adx(
            high,
            low,
            close,
            lookback_l=config.trend_id_lookback_l,
            tau_adx=config.trend_id_threshold,
        )
    elif config.trend_id == "c_hac_ols_slope_t":
        sides = trend_id_c_hac_ols_slope_t(
            log_prices,
            lookback_l=config.trend_id_lookback_l,
            tau_t=config.trend_id_threshold,
        )
    elif config.trend_id == "d_ma_cross":
        sides = trend_id_d_ma_cross(
            close,
            short_window=config.trend_id_short_window,
            long_window=config.trend_id_long_window,
            tau_ma=config.trend_id_threshold,
        )
    else:  # pragma: no cover -- enforced by H062FeatureConfig.__post_init__
        raise ValueError(f"unknown trend_id {config.trend_id!r}")
    return np.asarray(sides, dtype=np.int8)


def compute_h062_features(
    *,
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    close: npt.ArrayLike,
    config: H062FeatureConfig,
) -> H062Features:
    """Compute the full H062 feature stack for a single instrument's bar series.

    Args:
        high, low, close: 1-D OHLC arrays (length n_bars; matched).
        config: H062FeatureConfig with all hyperparameters.

    Returns:
        H062Features with all per-bar arrays populated.

    Raises:
        ValueError: shape mismatch, insufficient history, or invalid config.

    PIT semantic (per design.md §7):
      - channel.channel_high[t] = max(close[t-N..t-1])  -- bar-t-1 inclusive
      - atr[t] uses TR[0..t] inclusive (Wilder smoothing through bar t)
      - trend_side[t] is the H055 trend-filter side at bar t (PIT per H055 §3)
      - raw_events[t] compares close[t] to channel[t] (both bar-t close-time)
      - filtered_events[t] applies first-fire dwell to raw_events
      - eligible_events[t] = filtered_events[t] × (trend_side gate pass)
    """
    h = np.asarray(high, dtype=float).ravel()
    lo = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    if h.shape != lo.shape or h.shape != c.shape:
        raise ValueError(
            f"OHLC shape mismatch: high {h.shape}, low {lo.shape}, close {c.shape}"
        )

    # Donchian channel + raw events + first-fire filter.
    channel = donchian_channel(c, channel_n=config.channel_n)
    raw_events = donchian_breakout_events(c, channel)
    filtered_events = first_fire_filter(raw_events, h_dwell=config.h_dwell)

    # ATR.
    atr = atr_wilder(h, lo, c, n=config.atr_n)

    # Trend-filter side. Use log(close) for trend_id_a/c.
    log_prices = np.log(np.where(c > 0, c, np.nan))
    trend_side = select_trend_id_side(
        config,
        high=h,
        low=lo,
        close=c,
        log_prices=log_prices,
    )

    # Gate semantic: long requires trend_side ∈ {0, +1}; short requires
    # trend_side ∈ {0, -1}. Equivalently: filtered_events[t] is admitted iff
    # NOT (filtered_events[t]==+1 AND trend_side[t]==-1) AND NOT
    # (filtered_events[t]==-1 AND trend_side[t]==+1).
    long_disagree = (filtered_events == 1) & (trend_side == -1)
    short_disagree = (filtered_events == -1) & (trend_side == 1)
    eligible_events = filtered_events.copy()
    eligible_events[long_disagree | short_disagree] = 0

    return H062Features(
        channel=channel,
        atr=atr,
        trend_side=trend_side,
        raw_events=raw_events,
        filtered_events=filtered_events,
        eligible_events=eligible_events,
        config=config,
    )
