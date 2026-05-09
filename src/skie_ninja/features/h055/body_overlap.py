"""H055 Component 2 — body-overlap consolidation indicator ρ_1 per design.md §3.

Closed-form metric capturing range-bound consolidation regimes on a higher
timeframe T_H. Defined per design.md §3 Component 2:

    ρ_1 = mean over all pairs (i, j), i < j, in window [t-N+1, t] of
          Jaccard(body_i, body_j)

where:
- body_i = [min(open_i, close_i), max(open_i, close_i)] (the candle body
  interval in price-space)
- Jaccard(A, B) = length(A ∩ B) / length(A ∪ B); 0 when A ∪ B has zero
  length, 1 when A == B

ρ_1 ∈ [0, 1]. Higher values indicate tightly-overlapping consecutive bar
bodies (consolidation / coil regime). The trigger threshold ρ* is
calibrated against the empirical CDF of ρ_1 on the calibration holdout
per design.md §5.2.

Closest formal cousin: realized-vol regime characterization per
[Andersen-Bollerslev-Diebold-Labys 2003 *Econometrica* 71(2):579-625](
https://doi.org/10.1111/1468-0262.00418).

Practitioner ancestors: NR7 (Connors-Raschke 1995; *practitioner*) and
Bollinger squeeze (Bollinger 2001; *practitioner*).

PIT-safe: ρ_1[t] uses bars [t-N+1, t] only; no forward bars.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

__all__ = [
    "body_interval",
    "pairwise_jaccard",
    "body_overlap_rho_1",
]


def body_interval(
    open_: float, close: float
) -> tuple[float, float]:
    """Candle body interval = [min(open, close), max(open, close)]."""
    if open_ <= close:
        return (float(open_), float(close))
    return (float(close), float(open_))


def pairwise_jaccard(
    a: tuple[float, float], b: tuple[float, float]
) -> float:
    """Jaccard similarity of two closed price intervals.

    Args:
        a, b: Each (low, high) tuple with low <= high.

    Returns:
        Jaccard(a, b) = length(a ∩ b) / length(a ∪ b) ∈ [0, 1].

        Edge cases:
        - Both intervals zero-length AND identical: returns 1.0 (degenerate
          but consistent with the limit of Jaccard for shrinking identical
          intervals).
        - Both intervals zero-length AND distinct: returns 0.0 (no
          intersection; no positive-length union).
        - One zero-length on the boundary of the other: returns 0.0
          (intersection has zero length).
    """
    a_low, a_high = a
    b_low, b_high = b
    if a_low > a_high or b_low > b_high:
        raise ValueError(
            f"intervals must satisfy low <= high; got a={a}, b={b}"
        )
    inter_low = max(a_low, b_low)
    inter_high = min(a_high, b_high)
    inter_len = max(0.0, inter_high - inter_low)
    union_low = min(a_low, b_low)
    union_high = max(a_high, b_high)
    union_len = union_high - union_low
    if union_len <= 0.0:
        return 1.0 if (a_low == b_low and a_high == b_high) else 0.0
    return inter_len / union_len


def body_overlap_rho_1(
    open_: npt.ArrayLike,
    close: npt.ArrayLike,
    *,
    window_n: int,
) -> np.ndarray:
    """Rolling body-overlap indicator ρ_1 per design.md §3 Component 2.

    For each bar t with t >= window_n - 1, computes the mean pairwise
    Jaccard similarity of body intervals across the window [t-N+1, t]
    (N = window_n). Bars [0, window_n-2] yield NaN (insufficient history).

    Args:
        open_: 1-D array of bar open prices.
        close: 1-D array of bar close prices.
        window_n: Window length N ∈ {5, 7, 10, 14, 20} per design.md §5.6.

    Returns:
        1-D array of length n_bars with ρ_1 values; first window_n - 1
        entries are NaN.

    Raises:
        ValueError: shape mismatch or window_n < 2.
    """
    if window_n < 2:
        raise ValueError(f"window_n must be >= 2, got {window_n}")
    o = np.asarray(open_, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    if o.shape != c.shape:
        raise ValueError(
            f"shape mismatch: open {o.shape}, close {c.shape}"
        )
    n_bars = o.size
    if n_bars < window_n:
        raise ValueError(
            f"n_bars={n_bars} < window_n={window_n}; insufficient history"
        )

    # Pre-compute body intervals as (low, high) tuples.
    body_low = np.minimum(o, c)
    body_high = np.maximum(o, c)

    rho_1 = np.full(n_bars, np.nan, dtype=float)
    n_pairs = window_n * (window_n - 1) // 2

    for t in range(window_n - 1, n_bars):
        # Window indices [t - window_n + 1, t] inclusive.
        i_start = t - window_n + 1
        bl_w = body_low[i_start : t + 1]
        bh_w = body_high[i_start : t + 1]
        # Vectorised pairwise Jaccard over the window.
        # Build (window_n, window_n) lower-triangular pair indices via
        # outer ops; only count i < j (n_pairs entries).
        bl_i = bl_w[:, None]
        bh_i = bh_w[:, None]
        bl_j = bl_w[None, :]
        bh_j = bh_w[None, :]
        inter_low = np.maximum(bl_i, bl_j)
        inter_high = np.minimum(bh_i, bh_j)
        inter_len = np.maximum(0.0, inter_high - inter_low)
        union_low = np.minimum(bl_i, bl_j)
        union_high = np.maximum(bh_i, bh_j)
        union_len = union_high - union_low
        # Avoid div-by-zero: where union_len == 0, both intervals are
        # zero-length; treat as 1.0 if identical, 0.0 otherwise.
        with np.errstate(invalid="ignore", divide="ignore"):
            jaccard_full = np.where(
                union_len > 0.0,
                inter_len / np.where(union_len > 0.0, union_len, 1.0),
                np.where(
                    (bl_i == bl_j) & (bh_i == bh_j), 1.0, 0.0
                ),
            )
        # Take strict upper triangle (i < j) to avoid double-counting + i==j.
        triu_mask = np.triu(np.ones((window_n, window_n), dtype=bool), k=1)
        rho_1[t] = float(jaccard_full[triu_mask].mean())

    return rho_1
