"""H055 Component 4 — ATR + Wilder smoothing per design.md §3 + §5.4.

ATR_n on T_L via Wilder smoothing over n bars (Wilder 1978 *New Concepts in
Technical Trading Systems*, ISBN 978-0894590276; *practitioner*). Used for:
- TP / SL multiples in §4 label construction (`TP = entry ± α · ATR_n`,
  `SL = entry ∓ β · ATR_n`)
- Touch tolerance δ in §3 Component 3 level-state machine
- Adverse-move predicate in ADR-0017 §5 K-8 kill switch
- Position-size scaling in §5.4 Kelly sizing (`β · ATR_n · point_value`)

Wilder smoothing convention (Wilder 1978 §III):
  ATR_t = ((n - 1) / n) × ATR_{t-1} + (1 / n) × TR_t

where TR_t = max(high_t - low_t, |high_t - close_{t-1}|, |low_t - close_{t-1}|).

Initialization: ATR_n is undefined for the first n bars; the standard
practice is ATR_n[n-1] = mean(TR[0:n]) (simple-mean seed) per Wilder 1978
*practitioner*. The Wilder smoothing recurrence then runs from index n onward.

PIT-safe: uses only bars at and before time t to compute ATR_t. The H055
feature factory wires this at the eligible-bar layer per design.md §4.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

__all__ = [
    "true_range",
    "atr_wilder",
]


def true_range(
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    close: npt.ArrayLike,
) -> np.ndarray:
    """Per-bar true range per Wilder 1978 §III.

    TR_t = max(high_t - low_t, |high_t - close_{t-1}|, |low_t - close_{t-1}|)

    For t=0 (no prior close), TR_0 = high_0 - low_0.

    Args:
        high: 1-D array of bar highs (length n).
        low:  1-D array of bar lows (length n).
        close: 1-D array of bar closes (length n).

    Returns:
        1-D array of length n with the true range per bar.

    Raises:
        ValueError: shape mismatch or empty input.
    """
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    if h.shape != l.shape or h.shape != c.shape:
        raise ValueError(
            f"shape mismatch: high {h.shape}, low {l.shape}, close {c.shape}"
        )
    n = h.size
    if n == 0:
        raise ValueError("empty input")
    tr = np.empty(n, dtype=float)
    tr[0] = h[0] - l[0]
    if n > 1:
        prev_close = c[:-1]
        hl = h[1:] - l[1:]
        hc = np.abs(h[1:] - prev_close)
        lc = np.abs(l[1:] - prev_close)
        tr[1:] = np.maximum(np.maximum(hl, hc), lc)
    return tr


def atr_wilder(
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    close: npt.ArrayLike,
    *,
    n: int = 14,
) -> np.ndarray:
    """ATR_n via Wilder 1978 smoothing.

    The recurrence (Wilder 1978 §III; *practitioner*):
        ATR_t = ((n - 1) / n) × ATR_{t-1} + (1 / n) × TR_t

    with the standard seed `ATR[n-1] = mean(TR[0:n])` (simple-mean seed)
    and ATR[0:n-1] = NaN (insufficient history per Wilder's bar-count
    convention).

    Args:
        high, low, close: 1-D OHLC arrays (length n_bars).
        n: ATR lookback in bars (default 14 per Wilder 1978; H055 search
            domain ∈ {7, 14, 21} per design.md §5.6).

    Returns:
        1-D array of length n_bars; entries [0, n-1] are NaN; entry [n-1]
        is the simple-mean seed; entries [n, n_bars-1] use the Wilder
        recurrence.

    Raises:
        ValueError: n < 1, or n > n_bars (insufficient history for any seed).
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    n_bars = h.size
    if n_bars < n:
        raise ValueError(
            f"n_bars={n_bars} < n={n}; insufficient history for seed"
        )

    tr = true_range(h, l, c)
    atr = np.full(n_bars, np.nan, dtype=float)
    # Simple-mean seed at bar n-1 (Wilder 1978 *practitioner* convention).
    atr[n - 1] = float(np.mean(tr[:n]))
    # Wilder recurrence for t >= n.
    alpha = 1.0 / n
    one_minus_alpha = 1.0 - alpha
    for t in range(n, n_bars):
        atr[t] = one_minus_alpha * atr[t - 1] + alpha * tr[t]
    return atr
