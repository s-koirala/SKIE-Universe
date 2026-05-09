"""H055 wick-reversal-non-swing detector per design.md §3 (closing block).

Detects the **wick-reversal-non-swing** sub-pattern verbatim from the
operator's discretionary v1 ledger:

  Wick-reversal (non-swing): bar whose wick **punctures** the most recent
  swing high/low **without** the close breaking through; gated by
  `θ_wick = wick / body ≥ θ_wick_min` per §5 search domain.

Detection logic per side:

- **Long wick-reversal** (puncture of recent swing-low level):
  - Bar's `low < L_swing` (wick punctures swing-low)
  - Bar's `close >= L_swing` (close does NOT break through)
  - `lower_wick / body >= θ_wick_min` (wick-size gate)
  - Where: `body = |close - open|`; `lower_wick = min(open, close) - low`

- **Short wick-reversal** (puncture of recent swing-high level):
  - Bar's `high > H_swing` (wick punctures swing-high)
  - Bar's `close <= H_swing` (close does NOT break through)
  - `upper_wick / body >= θ_wick_min`
  - Where: `upper_wick = high - max(open, close)`

θ_wick_min ∈ [1.0, 4.0] per design.md §5.6 search domain. Lower bound 1.0
= "wick at least equals body" per Nison 1991 *Japanese Candlestick Charting
Techniques* (Wiley, ISBN 978-0471832911) *practitioner*.

The detector requires a **swing-high/low memory** updated by the upstream
swing-pivot detector (each new swing pivot updates the most-recent
swing-high/low level for subsequent wick-reversal probes). The memory
lifecycle is the caller's responsibility (typically: per-instrument,
per-fold; reset at fold-boundary per design.md §5.3).

PIT-safe: wick-reversal detection at bar t uses only bar t's OHLC + the
swing-high/low memory state-as-of-t (the upstream swing-pivot detector
is itself causally PIT-safe per `confirmation_bar` semantics).

Closes follow-up `P1-H055-WICK-REVERSAL-NON-SWING-DETECTOR-IMPL`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

import numpy as np
import numpy.typing as npt

__all__ = [
    "SwingLevelMemory",
    "WickReversalSetup",
    "detect_wick_reversal_setups",
]

_LONG: Final[int] = 1
_SHORT: Final[int] = -1


@dataclass(frozen=True)
class WickReversalSetup:
    """A confirmed wick-reversal-non-swing setup.

    Fields:
        bar_index: Integer bar index of the wick-reversal bar (= entry bar
            since this is a non-swing pattern; entry-limit price is the
            wick extreme).
        side: +1 (long; lower-wick puncture of swing-low) or -1 (short).
        swing_level: The most-recent swing high (short) or low (long) level
            that was punctured by the wick.
        entry_limit_price: The bar's wick extreme (low for long; high for
            short) — the limit-order entry per design.md §4.
        wick_to_body_ratio: The realized θ_wick at the bar; recorded for
            audit and for the BSS calibration of the entry-quality classifier.
        bar_low: Bar's low (for provenance + downstream ATR-stop calc).
        bar_high: Bar's high.
    """

    bar_index: int
    side: int
    swing_level: float
    entry_limit_price: float
    wick_to_body_ratio: float
    bar_low: float
    bar_high: float


@dataclass
class SwingLevelMemory:
    """Most-recent swing-high + swing-low level memory.

    Updated by the upstream swing-pivot detector each time a new swing pivot
    is confirmed. The wick-reversal-non-swing detector consumes this memory
    to identify levels that subsequent bars may puncture.

    Lifecycle: caller-managed; typically reset at fold boundary per
    design.md §5.3 (analogous to LevelExhaustionStateMachine.reset()).
    """

    most_recent_swing_high: float | None = None
    most_recent_swing_high_bar: int | None = None
    most_recent_swing_low: float | None = None
    most_recent_swing_low_bar: int | None = None

    def update_swing_high(self, level: float, bar_index: int) -> None:
        if level <= 0.0:
            raise ValueError(f"swing high level must be positive, got {level}")
        self.most_recent_swing_high = float(level)
        self.most_recent_swing_high_bar = int(bar_index)

    def update_swing_low(self, level: float, bar_index: int) -> None:
        if level <= 0.0:
            raise ValueError(f"swing low level must be positive, got {level}")
        self.most_recent_swing_low = float(level)
        self.most_recent_swing_low_bar = int(bar_index)

    def reset(self) -> None:
        self.most_recent_swing_high = None
        self.most_recent_swing_high_bar = None
        self.most_recent_swing_low = None
        self.most_recent_swing_low_bar = None


def detect_wick_reversal_setups(
    open_prices: npt.ArrayLike,
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    close: npt.ArrayLike,
    *,
    swing_level_memory: SwingLevelMemory,
    theta_wick_min: float,
    body_floor: float = 1e-9,
) -> list[WickReversalSetup]:
    """Detect wick-reversal-non-swing setups across an OHLC bar panel.

    Walks bar-by-bar; for each bar:
      1. Probes long wick-reversal: punctures memory.most_recent_swing_low
         from below, close ≥ swing-low, lower_wick/body ≥ θ_wick_min.
      2. Probes short wick-reversal: symmetric.

    The memory is NOT mutated by this function — it is read-only at each
    bar. The orchestrator updates the memory via the upstream swing-pivot
    detector's emitted setups (typically: when a swing-pivot setup is
    confirmed at bar j with swing_bar=i, the orchestrator updates the
    swing-low memory to low[i] for long-side or swing-high to high[i]
    for short-side).

    Args:
        open_prices, high, low, close: Bar OHLC arrays (length n_bars).
        swing_level_memory: Read-only swing-high/low memory state.
        theta_wick_min: Minimum wick-to-body ratio for the wick-size gate
            (∈ [1.0, 4.0] per design.md §5.6).
        body_floor: Lower bound on |body| to avoid div-by-zero on doji bars
            (default 1e-9). Doji bars (body < body_floor) are skipped — they
            are wick-rejection-candidates structurally but the θ_wick ratio
            is undefined.

    Returns:
        List of WickReversalSetup objects in chronological order. Empty if
        no setups detected (e.g., memory is empty, no bars puncture).

    Raises:
        ValueError: shape mismatch, theta_wick_min outside [0, ∞).
    """
    if theta_wick_min < 0.0:
        raise ValueError(f"theta_wick_min must be >= 0, got {theta_wick_min}")
    if body_floor <= 0.0:
        raise ValueError(f"body_floor must be positive, got {body_floor}")

    o = np.asarray(open_prices, dtype=float).ravel()
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    if not (o.shape == h.shape == l.shape == c.shape):
        raise ValueError(
            f"shape mismatch: open {o.shape}, high {h.shape}, low {l.shape}, "
            f"close {c.shape}"
        )
    n = o.size
    if n == 0:
        return []

    setups: list[WickReversalSetup] = []
    for t in range(n):
        body = abs(c[t] - o[t])
        if body < body_floor:
            continue  # doji; θ_wick undefined

        # Long wick-reversal probe
        if (
            swing_level_memory.most_recent_swing_low is not None
            and l[t] < swing_level_memory.most_recent_swing_low
            and c[t] >= swing_level_memory.most_recent_swing_low
        ):
            lower_wick = float(min(o[t], c[t]) - l[t])
            if lower_wick > 0.0:
                ratio = lower_wick / body
                if ratio >= theta_wick_min:
                    setups.append(
                        WickReversalSetup(
                            bar_index=t,
                            side=_LONG,
                            swing_level=float(
                                swing_level_memory.most_recent_swing_low
                            ),
                            entry_limit_price=float(l[t]),
                            wick_to_body_ratio=ratio,
                            bar_low=float(l[t]),
                            bar_high=float(h[t]),
                        )
                    )

        # Short wick-reversal probe
        if (
            swing_level_memory.most_recent_swing_high is not None
            and h[t] > swing_level_memory.most_recent_swing_high
            and c[t] <= swing_level_memory.most_recent_swing_high
        ):
            upper_wick = float(h[t] - max(o[t], c[t]))
            if upper_wick > 0.0:
                ratio = upper_wick / body
                if ratio >= theta_wick_min:
                    setups.append(
                        WickReversalSetup(
                            bar_index=t,
                            side=_SHORT,
                            swing_level=float(
                                swing_level_memory.most_recent_swing_high
                            ),
                            entry_limit_price=float(h[t]),
                            wick_to_body_ratio=ratio,
                            bar_low=float(l[t]),
                            bar_high=float(h[t]),
                        )
                    )

    return setups
