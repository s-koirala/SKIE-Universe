"""H055 swing-pivot setup detector per design.md §3 (closing block).

Detects the wick-rejection swing-pivot setups verbatim from the operator's
discretionary v1 ledger:

  - **Long swing pivot**: 3 consecutive lower lows then 2 subsequent higher
    lows (the second pair need not be consecutive). Entry at the wick of
    the swing-low bar.
  - **Short swing pivot**: symmetric — 3 consecutive higher highs then 2
    lower highs. Entry at the upper wick.

The detector is **causally PIT-safe**: setup confirmation happens at the
`confirmation_bar` (when the 2 confirming higher-lows / lower-highs close),
NOT at the swing-pivot bar itself. The orchestrator posts a limit order at
the swing-bar's wick extreme starting at `confirmation_bar`; the actual
fill (if any) occurs in subsequent bars when price retests the wick.

Wick-reversal-non-swing detection (the second sub-pattern in design.md §3
"Wick-reversal (non-swing)") is implemented in a separate primitive
(pending `P1-H055-WICK-REVERSAL-NON-SWING-DETECTOR-IMPL`) because it
requires a swing-high/low memory plus a θ_wick = wick / body gating
threshold; landing it separately keeps each commit atomic and audit-
remediate-loop-bounded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import numpy.typing as npt

__all__ = [
    "SwingPivotSetup",
    "detect_long_swing_pivot_setups",
    "detect_short_swing_pivot_setups",
    "detect_swing_pivot_setups",
]

_LONG: Final[int] = 1
_SHORT: Final[int] = -1


@dataclass(frozen=True)
class SwingPivotSetup:
    """A confirmed wick-rejection swing-pivot setup.

    Fields:
        confirmation_bar: Integer bar index at which the setup was confirmed
            (the bar at which the second confirming higher-low / lower-high
            closed). The orchestrator may begin posting a limit order at the
            entry_limit_price starting at this bar; H055 design.md §4 "Entry"
            rule applies.
        side: +1 (long) or -1 (short).
        swing_bar: Integer bar index of the historical swing-pivot bar
            (whose wick extreme is the entry-limit price).
        entry_limit_price: Price at the swing-pivot bar's wick extreme.
            For long swing pivots = low[swing_bar]; for short = high[swing_bar].
    """

    confirmation_bar: int
    side: int
    swing_bar: int
    entry_limit_price: float


def detect_long_swing_pivot_setups(
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    *,
    confirmation_window: int = 5,
) -> list[SwingPivotSetup]:
    """Detect long-side swing-pivot setups per H055 design.md §3.

    Long swing-pivot pattern:
      - Bar i is the swing-low candidate; satisfies
            low[i-3] > low[i-2] > low[i-1] > low[i]   (3 consecutive lower lows)
      - Within the next `confirmation_window` bars, at least 2 bars j > i
        have low[j] > low[i] (higher lows; not required to be consecutive).
      - On the bar where the second confirming higher-low closes, the setup
        is emitted with `confirmation_bar = j`, `swing_bar = i`,
        `entry_limit_price = low[i]`.

    Causally PIT-safe: setup detection at bar j uses only bars [0, j]; no
    forward-looking confirmation from bars > j.

    Args:
        high: 1-D array of bar highs (unused in long detection, but kept
            for API symmetry with the short variant).
        low: 1-D array of bar lows.
        confirmation_window: Maximum bars after the swing-low to allow
            finding the 2 confirming higher-lows (default 5; bounded above
            by typical wick-rejection persistence on 1-min ES/NQ).

    Returns:
        List of SwingPivotSetup objects in chronological order of
        confirmation_bar. Empty list if no setups detected.

    Raises:
        ValueError: shape mismatch or confirmation_window < 2.
    """
    if confirmation_window < 2:
        raise ValueError(
            f"confirmation_window must be >= 2 (need 2 higher-lows), "
            f"got {confirmation_window}"
        )
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    if h.shape != l.shape:
        raise ValueError(f"shape mismatch: high {h.shape}, low {l.shape}")
    n = l.size
    if n < 4:
        return []

    setups: list[SwingPivotSetup] = []
    for i in range(3, n):
        # Strict monotone decrease over [i-3, i-2, i-1, i]
        if not (l[i - 3] > l[i - 2] > l[i - 1] > l[i]):
            continue
        # Look forward for 2 higher-lows within confirmation_window
        higher_lows_count = 0
        confirmation_bar: int | None = None
        for j in range(i + 1, min(i + 1 + confirmation_window, n)):
            if l[j] > l[i]:
                higher_lows_count += 1
                if higher_lows_count >= 2:
                    confirmation_bar = j
                    break
        if confirmation_bar is None:
            continue
        setups.append(
            SwingPivotSetup(
                confirmation_bar=confirmation_bar,
                side=_LONG,
                swing_bar=i,
                entry_limit_price=float(l[i]),
            )
        )
    return setups


def detect_short_swing_pivot_setups(
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    *,
    confirmation_window: int = 5,
) -> list[SwingPivotSetup]:
    """Detect short-side swing-pivot setups (symmetric to long).

    Short swing-pivot pattern:
      - Bar i is the swing-high candidate; satisfies
            high[i-3] < high[i-2] < high[i-1] < high[i]  (3 consecutive higher highs)
      - Within the next `confirmation_window` bars, at least 2 bars j > i
        have high[j] < high[i] (lower highs).
      - On confirmation, emit setup with entry_limit_price = high[i].

    See `detect_long_swing_pivot_setups` for full semantic + PIT-safety
    discussion.
    """
    if confirmation_window < 2:
        raise ValueError(
            f"confirmation_window must be >= 2 (need 2 lower-highs), "
            f"got {confirmation_window}"
        )
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    if h.shape != l.shape:
        raise ValueError(f"shape mismatch: high {h.shape}, low {l.shape}")
    n = h.size
    if n < 4:
        return []

    setups: list[SwingPivotSetup] = []
    for i in range(3, n):
        if not (h[i - 3] < h[i - 2] < h[i - 1] < h[i]):
            continue
        lower_highs_count = 0
        confirmation_bar: int | None = None
        for j in range(i + 1, min(i + 1 + confirmation_window, n)):
            if h[j] < h[i]:
                lower_highs_count += 1
                if lower_highs_count >= 2:
                    confirmation_bar = j
                    break
        if confirmation_bar is None:
            continue
        setups.append(
            SwingPivotSetup(
                confirmation_bar=confirmation_bar,
                side=_SHORT,
                swing_bar=i,
                entry_limit_price=float(h[i]),
            )
        )
    return setups


def detect_swing_pivot_setups(
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    *,
    confirmation_window: int = 5,
) -> list[SwingPivotSetup]:
    """Detect long + short swing-pivot setups; merge in chronological order.

    Returns the union of `detect_long_swing_pivot_setups` and
    `detect_short_swing_pivot_setups`, sorted by `confirmation_bar`.
    """
    long_setups = detect_long_swing_pivot_setups(
        high, low, confirmation_window=confirmation_window
    )
    short_setups = detect_short_swing_pivot_setups(
        high, low, confirmation_window=confirmation_window
    )
    return sorted(
        long_setups + short_setups,
        key=lambda s: (s.confirmation_bar, s.side),
    )
