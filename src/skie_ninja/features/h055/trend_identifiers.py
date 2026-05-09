"""H055 Component 1 — deterministic trend-strength gate identifiers.

Per H055 design.md §3 + §5.1 + §5.6, four candidate identifiers compete on
the calibration holdout via supervised Brier-score selection (per
[Niculescu-Mizil & Caruana 2005, *ICML*](https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf));
the per-instrument-class winner ID_1*_c is then frozen for the H055
walk-forward.

Each identifier returns a per-bar side ∈ {+1, 0, -1}:
  - +1: trend up; long-side entries permitted (subject to Components 2-4)
  - -1: trend down; short-side entries permitted
  -  0: no trend / threshold not met; no entry on either side

Identifiers (per design.md §5.1 + §15.1 errata addendum):
  - a: TS-mom — Moskowitz-Ooi-Pedersen 2012 J Financial Economics 104(2):228-250
       DOI 10.1016/j.jfineco.2011.11.003 (time-series momentum)
  - b: ADX  — Wilder 1978 New Concepts in Technical Trading Systems
       (ISBN 978-0894590276; *practitioner*; Average Directional Index)
  - c: HAC-OLS-slope-t — log-price linear-trend slope t-statistic with
       Newey-West 1987 HAC variance estimator
  - d: MA-cross — short/long simple-moving-average crossover with
       relative-distance threshold

PIT-safe: all identifiers compute side[t] using only bars [0, t]. The
H055 feature factory wires this on T_H-resampled bar streams per §3.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from skie_ninja.features.h055.atr import true_range
from skie_ninja.inference.stats.hac import nw_hac_variance

__all__ = [
    "trend_id_a_ts_mom",
    "trend_id_b_adx",
    "trend_id_c_hac_ols_slope_t",
    "trend_id_d_ma_cross",
]


def trend_id_a_ts_mom(
    log_prices: npt.ArrayLike,
    *,
    lookback_l: int,
    tau_m: float,
    realized_vol_window: int | None = None,
) -> np.ndarray:
    """TS-mom per Moskowitz-Ooi-Pedersen 2012 §III.

    For each bar t with t >= lookback_l:
      r_L           = log_price[t] - log_price[t - lookback_l]
      sigma_per_bar = std of 1-bar log returns over preceding window
      side[t]       = sign(r_L) if |r_L| > tau_m × sigma_per_bar × sqrt(L), else 0

    The sqrt(lookback_l) scaling reflects that r_L = sum of L 1-bar log
    returns; its scale-adjusted noise is σ_per_bar × sqrt(L) under the
    iid-returns approximation (relaxed under MOP 2012 §III footnote 6's
    autocorrelation-corrected version which is preserved here as the
    threshold's primary form).

    Args:
        log_prices: 1-D array of log prices (length n_bars).
        lookback_l: Bars on T_H over which to measure cumulative return
            (∈ {20, 40, 60, 120, 240} per design.md §5.6).
        tau_m: Threshold in σ-units (continuous; prior on (0, 3] per §5.6).
        realized_vol_window: Bars over which to compute σ_per_bar; defaults
            to max(lookback_l, 20).

    Returns:
        Per-bar side array of dtype int. Bars with insufficient history
        carry side=0.

    Raises:
        ValueError: lookback_l < 1, or n_bars < lookback_l + 2.
    """
    if lookback_l < 1:
        raise ValueError(f"lookback_l must be >= 1, got {lookback_l}")
    p = np.asarray(log_prices, dtype=float).ravel()
    n = p.size
    if n < lookback_l + 2:
        raise ValueError(
            f"insufficient history: n={n} < lookback_l + 2 = {lookback_l + 2}"
        )
    if realized_vol_window is None:
        realized_vol_window = max(lookback_l, 20)
    if realized_vol_window < 2:
        raise ValueError(
            f"realized_vol_window must be >= 2, got {realized_vol_window}"
        )

    sides = np.zeros(n, dtype=int)
    one_bar_returns = np.diff(p)  # length n-1
    for t in range(lookback_l, n):
        rv_start = max(0, t - realized_vol_window)
        # Window of 1-bar returns [rv_start, t-1] (inclusive); diff index = bar - 1
        rv_block = one_bar_returns[rv_start:t]
        if rv_block.size < 2:
            continue
        sigma = float(np.std(rv_block, ddof=1))
        if not np.isfinite(sigma) or sigma <= 0:
            continue
        r_l = float(p[t] - p[t - lookback_l])
        threshold = tau_m * sigma * np.sqrt(lookback_l)
        if abs(r_l) > threshold:
            sides[t] = int(np.sign(r_l))
    return sides


def _wilder_smooth(x: np.ndarray, lookback_l: int) -> np.ndarray:
    """Wilder 1978 §III recurrence with simple-sum seed.

    seed: result[L-1] = sum(x[0:L])
    recurrence: result[t] = result[t-1] - result[t-1] / L + x[t]
    """
    result = np.full(x.size, np.nan, dtype=float)
    if x.size < lookback_l:
        return result
    result[lookback_l - 1] = float(np.sum(x[:lookback_l]))
    for t in range(lookback_l, x.size):
        result[t] = result[t - 1] - result[t - 1] / lookback_l + x[t]
    return result


def trend_id_b_adx(
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    close: npt.ArrayLike,
    *,
    lookback_l: int,
    tau_adx: float,
) -> np.ndarray:
    """ADX per Wilder 1978 *practitioner* (ISBN 978-0894590276).

    Standard Wilder ADX construction:
      +DM_t = up_move_t   if up_move_t > down_move_t and up_move_t > 0,   else 0
      -DM_t = down_move_t if down_move_t > up_move_t and down_move_t > 0, else 0
      where up_move_t = high_t - high_{t-1}; down_move_t = low_{t-1} - low_t.
    Wilder-smooth +DM, -DM, TR over lookback_l bars; then:
      +DI_t = 100 × WS(+DM)_t / WS(TR)_t
      -DI_t = 100 × WS(-DM)_t / WS(TR)_t
       DX_t = 100 × |+DI_t - -DI_t| / (+DI_t + -DI_t)
       ADX_t = Wilder-smoothed DX over lookback_l bars.

    Side rule:
      +1 if ADX > tau_adx AND +DI > -DI
      -1 if ADX > tau_adx AND -DI > +DI
       0 otherwise

    Args:
        high, low, close: OHLC arrays (length n_bars).
        lookback_l: ADX lookback (∈ [10, 50] per design.md §5.6 + Wilder
            1978 default 14).
        tau_adx: ADX threshold (∈ [10, 50] per design.md §5.6).

    Returns:
        Per-bar side array of dtype int.
    """
    if lookback_l < 2:
        raise ValueError(f"lookback_l must be >= 2, got {lookback_l}")
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    n = h.size
    if n < 2 * lookback_l:
        raise ValueError(
            f"insufficient history for ADX with lookback_l={lookback_l}: n={n}"
        )

    up_move = h[1:] - h[:-1]
    down_move = l[:-1] - l[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = true_range(h, l, c)[1:]  # align with DM (length n-1)

    plus_dm_s = _wilder_smooth(plus_dm, lookback_l)
    minus_dm_s = _wilder_smooth(minus_dm, lookback_l)
    tr_s = _wilder_smooth(tr, lookback_l)

    safe_tr = np.where(tr_s > 0, tr_s, np.nan)
    plus_di = 100.0 * plus_dm_s / safe_tr
    minus_di = 100.0 * minus_dm_s / safe_tr
    di_sum = plus_di + minus_di
    safe_sum = np.where(di_sum > 0, di_sum, np.nan)
    dx = 100.0 * np.abs(plus_di - minus_di) / safe_sum

    # ADX = Wilder-smoothed DX over lookback_l bars; seed at the first bar
    # where lookback_l consecutive DX values are non-NaN. Operationally,
    # DX is non-NaN once both +DI and -DI are non-NaN, which happens at
    # bar lookback_l - 1 in the (n-1)-length DM/TR series. So ADX seeds at
    # 2*lookback_l - 1 in the original bar index.
    adx = np.full(n - 1, np.nan, dtype=float)
    valid_dx = ~np.isnan(dx)
    if valid_dx.sum() < lookback_l:
        # Still return zeros (no trend identified)
        return np.zeros(n, dtype=int)
    first_valid = int(np.argmax(valid_dx))
    seed_index = first_valid + lookback_l - 1
    if seed_index < dx.size:
        adx[seed_index] = float(
            np.nanmean(dx[first_valid : first_valid + lookback_l])
        )
        for t in range(seed_index + 1, dx.size):
            prev = adx[t - 1]
            cur = dx[t]
            if np.isnan(prev):
                continue
            if np.isnan(cur):
                adx[t] = prev
            else:
                adx[t] = (prev * (lookback_l - 1) + cur) / lookback_l

    sides = np.zeros(n, dtype=int)
    for t in range(1, n):
        adx_val = adx[t - 1]
        if np.isnan(adx_val) or adx_val <= tau_adx:
            continue
        pdi = plus_di[t - 1]
        mdi = minus_di[t - 1]
        if np.isnan(pdi) or np.isnan(mdi):
            continue
        if pdi > mdi:
            sides[t] = 1
        elif mdi > pdi:
            sides[t] = -1
    return sides


def trend_id_c_hac_ols_slope_t(
    log_prices: npt.ArrayLike,
    *,
    lookback_l: int,
    tau_t: float,
    hac_bandwidth: int | None = None,
) -> np.ndarray:
    """OLS log-price slope t-statistic with Newey-West 1987 HAC variance.

    For each bar t with t >= lookback_l - 1:
      Fit log_price[t-L+1:t+1] = α + β · time_index + ε on time_index ∈
      {0, 1, ..., L-1} via ordinary-least-squares closed-form. Compute
      Newey-West 1987 long-run variance σ²_LR of the regression residuals
      via the project's nw_hac_variance primitive. Approximate SE(β):

        SE(β) ≈ sqrt(σ²_LR / Σ(time_index - mean)²)

      side[t] = sign(β) if |β / SE(β)| > tau_t else 0.

    The homoscedastic-OLS-SE-with-HAC-residual is an approximation; the
    full sandwich estimator would be β SE = sqrt[(X'X)^-1 X' Σ X (X'X)^-1]
    with Σ the HAC long-run variance matrix (Andrews 1991). For univariate
    regression on a regular time index this reduces to the form above to
    leading order; sufficient for the H055 trend-gate use case.

    Args:
        log_prices: 1-D array of log prices.
        lookback_l: Regression window length (∈ {20, 40, 60, 120, 240} per
            §5.6).
        tau_t: t-statistic threshold (continuous; prior on σ-units per §5.6).
        hac_bandwidth: NW1987 truncation lag; defaults to
            ceil(4 × (L/100)^(2/9)) per Andrews 1991 / NW 1994 plug-in.

    Returns:
        Per-bar side array of dtype int.
    """
    if lookback_l < 5:
        raise ValueError(f"lookback_l must be >= 5, got {lookback_l}")
    p = np.asarray(log_prices, dtype=float).ravel()
    n = p.size
    if n < lookback_l:
        raise ValueError(
            f"insufficient history: n={n} < lookback_l = {lookback_l}"
        )

    if hac_bandwidth is None:
        hac_bandwidth = max(
            1, int(np.ceil(4.0 * (lookback_l / 100.0) ** (2.0 / 9.0)))
        )

    sides = np.zeros(n, dtype=int)
    x = np.arange(lookback_l, dtype=float)
    x_bar = x.mean()
    x_dev = x - x_bar
    sxx = float((x_dev ** 2).sum())
    if sxx <= 0:
        return sides

    for t in range(lookback_l - 1, n):
        y = p[t - lookback_l + 1 : t + 1]
        y_bar = float(y.mean())
        y_dev = y - y_bar
        sxy = float((x_dev * y_dev).sum())
        slope = sxy / sxx
        intercept = y_bar - slope * x_bar
        residuals = y - (intercept + slope * x)
        try:
            sigma2_lr, _ = nw_hac_variance(
                residuals, bandwidth=hac_bandwidth, demean=False
            )
        except Exception:
            continue
        if not np.isfinite(sigma2_lr) or sigma2_lr <= 0:
            continue
        se_slope = float(np.sqrt(sigma2_lr / sxx))
        if se_slope <= 0:
            continue
        t_stat = slope / se_slope
        if abs(t_stat) > tau_t:
            sides[t] = int(np.sign(slope))
    return sides


def trend_id_d_ma_cross(
    close: npt.ArrayLike,
    *,
    short_window: int,
    long_window: int,
    tau_ma: float = 0.0,
) -> np.ndarray:
    """SMA crossover with relative-distance threshold tau_ma.

    Side rule:
      +1 if SMA_short[t] > SMA_long[t] × (1 + tau_ma)
      -1 if SMA_short[t] < SMA_long[t] × (1 - tau_ma)
       0 otherwise

    Args:
        close: 1-D array of bar closes (length n_bars).
        short_window: Short-MA bars (must be < long_window).
        long_window: Long-MA bars.
        tau_ma: Relative-distance threshold (≥ 0; prior on σ-units per
            §5.6 τ_MA spec).

    Returns:
        Per-bar side array of dtype int.
    """
    if short_window < 1:
        raise ValueError(f"short_window must be >= 1, got {short_window}")
    if long_window <= short_window:
        raise ValueError(
            f"long_window must be > short_window; got "
            f"long={long_window}, short={short_window}"
        )
    if tau_ma < 0:
        raise ValueError(f"tau_ma must be >= 0, got {tau_ma}")
    c = np.asarray(close, dtype=float).ravel()
    n = c.size
    if n < long_window:
        raise ValueError(
            f"insufficient history: n={n} < long_window = {long_window}"
        )

    def _sma(x: np.ndarray, w: int) -> np.ndarray:
        result = np.full(x.size, np.nan, dtype=float)
        if x.size < w:
            return result
        cumsum = np.cumsum(x)
        result[w - 1] = float(cumsum[w - 1] / w)
        for t in range(w, x.size):
            result[t] = float((cumsum[t] - cumsum[t - w]) / w)
        return result

    sma_s = _sma(c, short_window)
    sma_l = _sma(c, long_window)
    sides = np.zeros(n, dtype=int)
    for t in range(long_window - 1, n):
        s = sma_s[t]
        m = sma_l[t]
        if np.isnan(s) or np.isnan(m) or m <= 0:
            continue
        if s > m * (1.0 + tau_ma):
            sides[t] = 1
        elif s < m * (1.0 - tau_ma):
            sides[t] = -1
    return sides
