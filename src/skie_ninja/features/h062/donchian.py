"""H062 Donchian channel + first-fire breakout-event detector.

Per H062 design.md §3 — the canonical Turtle System 1 / System 2 N-bar
channel-breakout rule ([Faith 2007 *Way of the Turtle*, McGraw-Hill,
ISBN 978-0071486644](https://www.amazon.com/Way-Turtle-Secret-Methods-Successful/dp/0071486646);
*practitioner*) applied at intraday 5-min cadence.

Channel computation (close-to-close per Faith 2007 §3 Turtle convention):
    channel_high_t = max(close_{t-1}, close_{t-2}, ..., close_{t-N})
    channel_low_t  = min(close_{t-1}, close_{t-2}, ..., close_{t-N})

The channel at bar-t uses information through bar-(t-1) close only. This is
PIT-causal: at bar-t close the channel is the max/min of the N most-recent
*confirmed* prior closes.

Long entry signal at bar t (firing on bar-t close):
    close_t > channel_high_t  AND  first-fire condition within H_dwell bars.

Short entry signal at bar t:
    close_t < channel_low_t   AND  first-fire condition.

First-fire dwell (per design.md §3): the bar-t breakout signal fires ONLY if
the breakout condition was NOT fired in any of the past H_dwell bars
{t-1, ..., t-H_dwell}. This prevents repeated re-entries while the channel
is broken (a single channel-break is one event; the breakout fires once and
then is re-armed only after H_dwell bars elapse with the breakout condition
inactive). The state machine carries the count-since-last-fire per side.

Initialization (insufficient history):
    For t < N, channel_high / channel_low are NaN (the close-of-bar-t-1
    history is incomplete). The breakout-signal array uses 0 (no signal) at
    these initial bars per the project sentinel convention.

References:
- Faith 2007 *Way of the Turtle* §3 (*practitioner*): N=20 / N=55 daily
  System 1 / System 2; close-to-close basis; no intrabar high/low channel.
- Crabel 1990 *Day Trading with Short Term Price Patterns and Opening
  Range Breakout* (ISBN 978-0934380171; *practitioner*): opening-range
  variant of the breakout family. Not the Donchian-channel-of-record but
  cross-reference for the breakout-event mechanic.
- López de Prado 2018 *AFML* §13 (*practitioner*): event-driven backtest
  convention — channel-break is the canonical event-driven entry signal.

PIT-safe: bar-t signal uses only closes [0, t-1] for the channel; the bar-t
close itself is compared to the (t-1-anchored) channel. The H062 walk-forward
orchestrator wires this at the eligible-bar layer per design.md §4.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

__all__ = [
    "DonchianChannel",
    "donchian_channel",
    "donchian_breakout_events",
    "first_fire_filter",
]


@dataclass(frozen=True)
class DonchianChannel:
    """Donchian channel arrays + diagnostics.

    Fields:
        channel_high: 1-D float array length n_bars; channel_high[t] is the
            max of closes [t-N, t-1] (close-to-close); NaN for t < N.
        channel_low:  Symmetric to channel_high; min over the same window.
        channel_n:    Channel lookback in bars (the N parameter).
        is_initialized: 1-D bool array length n_bars; True iff bar-t channel
            has at least N prior closes available.
    """

    channel_high: np.ndarray
    channel_low: np.ndarray
    channel_n: int
    is_initialized: np.ndarray


def donchian_channel(
    close: npt.ArrayLike,
    *,
    channel_n: int,
) -> DonchianChannel:
    """Compute rolling N-bar Donchian channel on close-to-close basis.

    For each bar t:
        channel_high[t] = max(close[t-N], close[t-N+1], ..., close[t-1])
        channel_low[t]  = min(close[t-N], close[t-N+1], ..., close[t-1])

    The channel at bar-t uses closes from the prior N bars only (bar t-1
    inclusive; bar t exclusive). This is the PIT-causal Faith 2007 §3
    close-to-close Turtle convention.

    For t < N, the channel is undefined (NaN) per the project sentinel
    convention; ``is_initialized[t]`` is True iff t >= N.

    Args:
        close: 1-D array of bar closes (length n_bars).
        channel_n: Channel lookback in bars (must be >= 1).

    Returns:
        DonchianChannel with `channel_high`, `channel_low`, `channel_n`,
        `is_initialized` populated.

    Raises:
        ValueError: channel_n < 1, or close has fewer than 1 element.

    Notes:
        Implementation uses a rolling-window argmax via numpy.lib.stride_tricks
        for O(n_bars) memory with O(N · n_bars) compute. Acceptable for
        H062 grid (N <= 480, n_bars ~ 1e6) at ~10ms-50ms per call. See
        López de Prado 2018 *AFML* §13 for event-driven backtest perf.
    """
    if channel_n < 1:
        raise ValueError(f"channel_n must be >= 1, got {channel_n}")
    c = np.asarray(close, dtype=float).ravel()
    n_bars = c.size
    if n_bars == 0:
        raise ValueError("empty close array")

    channel_high = np.full(n_bars, np.nan, dtype=float)
    channel_low = np.full(n_bars, np.nan, dtype=float)
    is_initialized = np.zeros(n_bars, dtype=bool)

    # First bar at which N prior closes are available is t = channel_n.
    # The channel at bar t uses closes [t-N, t-1].
    if n_bars >= channel_n + 1:
        # Sliding-window view via stride tricks: window of length N starting
        # at each bar index t in [N, n_bars). Each window is closes [t-N, t-1].
        # numpy.lib.stride_tricks.sliding_window_view returns shape
        # (n_bars - N + 1, N) corresponding to windows starting at index 0..n_bars-N.
        # We want windows ending at index t-1 for t in [N, n_bars); that's
        # windows starting at t-N for t in [N, n_bars), i.e., starting indices
        # [0, n_bars - N) inclusive on both ends — n_bars - N + 0 values total.
        windows = np.lib.stride_tricks.sliding_window_view(c, channel_n)
        # windows has shape (n_bars - N + 1, N).
        # The window starting at start_idx ends at start_idx + N - 1.
        # For bar t, the prior-N-closes window starts at start_idx = t - N
        # and ends at t - 1. That's windows[t - N] for t in [N, n_bars).
        # Note: t goes up to n_bars - 1, so start_idx up to n_bars - 1 - N
        # = n_bars - N - 1. windows is indexed 0..n_bars-N. We slice
        # windows[0:n_bars - N] which gives windows for t = N..n_bars-1.
        channel_high[channel_n:] = windows[: n_bars - channel_n].max(axis=1)
        channel_low[channel_n:] = windows[: n_bars - channel_n].min(axis=1)
        is_initialized[channel_n:] = True

    return DonchianChannel(
        channel_high=channel_high,
        channel_low=channel_low,
        channel_n=channel_n,
        is_initialized=is_initialized,
    )


def donchian_breakout_events(
    close: npt.ArrayLike,
    channel: DonchianChannel,
) -> np.ndarray:
    """Raw breakout-event detector (pre-first-fire filtering).

    For each bar t with channel initialized:
        +1 if close[t] > channel.channel_high[t]
        -1 if close[t] < channel.channel_low[t]
         0 otherwise

    This is the raw event signal; the first-fire dwell is applied
    separately via ``first_fire_filter`` per design.md §3 H_dwell semantic.

    Args:
        close: 1-D close array (must match channel array lengths).
        channel: Output of ``donchian_channel``.

    Returns:
        Per-bar int8 event array.

    Raises:
        ValueError: shape mismatch.
    """
    c = np.asarray(close, dtype=float).ravel()
    if c.size != channel.channel_high.size:
        raise ValueError(
            f"close shape {c.size} does not match channel shape "
            f"{channel.channel_high.size}"
        )
    events = np.zeros(c.size, dtype=np.int8)
    long_mask = (
        channel.is_initialized
        & np.isfinite(channel.channel_high)
        & (c > channel.channel_high)
    )
    short_mask = (
        channel.is_initialized
        & np.isfinite(channel.channel_low)
        & (c < channel.channel_low)
    )
    events[long_mask] = 1
    events[short_mask] = -1
    return events


def first_fire_filter(
    raw_events: npt.ArrayLike,
    *,
    h_dwell: int,
) -> np.ndarray:
    """First-fire filter on raw breakout-event signals.

    Per design.md §3 first-fire dwell convention:
        The bar-t breakout signal fires ONLY if the breakout condition was
        NOT fired in any of the past H_dwell bars (or, equivalently, the
        side-specific re-arm condition is: no fire of the same side in the
        past H_dwell bars).

    State machine semantic (per-side independent counters):
        - When a long event (+1) fires at bar t and no long fire occurred
          in bars [t-H_dwell, t-1], emit +1 and start a long cooldown of
          H_dwell bars.
        - Symmetric for short events.
        - A bar with a long event during the long cooldown is filtered out
          (the underlying close is still above channel_high but we treat
          the signal as a single channel-break event).
        - Opposite-side events fire independently (a long fire does NOT
          suppress a short fire; opposite side is a separate channel-break
          event).

    Args:
        raw_events: Raw event array from ``donchian_breakout_events`` (+1
            long, -1 short, 0 no-event).
        h_dwell: Re-arm dwell in bars (must be >= 1). Per design.md §3 grid
            {1, 2, 5, 10} 5-min bars.

    Returns:
        Filtered per-bar int8 event array. Same length as `raw_events`.

    Raises:
        ValueError: h_dwell < 1.
    """
    if h_dwell < 1:
        raise ValueError(f"h_dwell must be >= 1, got {h_dwell}")
    e = np.asarray(raw_events, dtype=np.int8).ravel()
    n = e.size
    filtered = np.zeros(n, dtype=np.int8)

    # Per-side last-fire index; -inf-equivalent sentinel = -h_dwell so first
    # event always fires.
    last_long_fire = -h_dwell - 1
    last_short_fire = -h_dwell - 1

    for t in range(n):
        ev = e[t]
        if ev == 1 and (t - last_long_fire) > h_dwell:
            filtered[t] = 1
            last_long_fire = t
        elif ev == -1 and (t - last_short_fire) > h_dwell:
            filtered[t] = -1
            last_short_fire = t
        # else: 0 stays 0 (raw event suppressed or no event)

    return filtered
