"""Triple-barrier labels (Lopez de Prado 2018, *AFML* §3.2).

Given an event-time series of prices with an event start timestamp,
a vertical time barrier, and profit-take / stop-loss multipliers
(``pt_sl``) of a pre-computed volatility target, produce a label in
``{-1, 0, +1}`` per event:

  - ``+1`` — upper barrier (profit-take) hit first.
  - ``-1`` — lower barrier (stop-loss) hit first.
  - ``0``  — vertical barrier reached without touching either
    horizontal barrier.

The volatility estimator is Yang-Zhang (Yang & Zhang 2000, DOI
10.1086/209650) on a rolling window — see :func:`yang_zhang_volatility`.
Yang-Zhang combines overnight (close-to-open) variance,
Rogers-Satchell (1991) drift-independent variance, and open-to-close
variance with an MSE-optimal weighting ``k``.

References
----------

  - Lopez de Prado, M. 2018. *Advances in Financial Machine Learning*,
    §3.2 ("The Triple-Barrier Method"). Wiley.
  - Yang, D. & Zhang, Q. 2000. "Drift-Independent Volatility Estimation
    Based on High, Low, Open, and Close Prices". *Journal of Business*
    73(3): 477-491. https://doi.org/10.1086/209650
  - Rogers, L. C. G. & Satchell, S. E. 1991. "Estimating variance from
    high, low and closing prices". *Annals of Applied Probability* 1(4):
    504-512. https://doi.org/10.1214/aoap/1177005835
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import polars as pl

# ---------------------------------------------------------------------------
# Yang-Zhang volatility
# ---------------------------------------------------------------------------


def yang_zhang_volatility(
    *,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    lookback: int,
) -> np.ndarray:
    """Rolling Yang-Zhang volatility estimate in natural-log units.

    Implements Yang & Zhang 2000 eq. (1)–(4):

        σ_YZ² = σ_o² + k · σ_c² + (1 - k) · σ_rs²

    where:

      - σ_o² = Var(log(O_t / C_{t-1})) — overnight variance.
      - σ_c² = Var(log(C_t / O_t)) — open-to-close (intraday) variance.
      - σ_rs² = Rogers-Satchell drift-independent variance,
        E[ (log(H/C) log(H/O)) + (log(L/C) log(L/O)) ].
      - ``k = α / (1 + α + (N+1)/(N-1))`` with α = 0.34 (Yang-Zhang's
        MSE-optimal constant; see paper eq. 8). Equivalent form:
        ``k = 0.34 / (1.34 + (N+1)/(N-1))``. ``N`` is the lookback.

    The ``α = 0.34`` constant is from Yang & Zhang 2000 eq. 8 (not an
    arbitrary choice — it minimises the MSE of the combined estimator
    under the diffusion model in the paper). Cross-checked against the
    TTR R package (joshuaulrich/TTR R/volatility.R; alpha_TTR=1.34,
    k=(1.34-1)/(1.34+(N+1)/(N-1)) — numerically identical).
    Note: the Yang & Zhang 2000 paper is paywalled (JSTOR DOI
    10.1086/209650); eq. 8 must be verified against a licensed copy.

    Returns an array of length ``len(close)`` with NaN on the warm-up
    region (first ``lookback`` rows) and on any window containing
    non-positive prices.
    """
    if lookback < 2:
        raise ValueError(f"lookback must be >= 2, got {lookback}.")
    n = len(close)
    if not (len(open_) == len(high) == len(low) == n):
        raise ValueError("open/high/low/close must have equal length.")

    # Guard against non-positive prices (log would blow up). Mask first,
    # then log; NaN propagates through the rolling stats below.
    with np.errstate(divide="ignore", invalid="ignore"):
        log_oc_prev = np.full(n, np.nan, dtype=np.float64)
        log_oc_prev[1:] = np.log(open_[1:] / close[:-1])
        log_co = np.log(close / open_)
        log_ho = np.log(high / open_)
        log_lo = np.log(low / open_)
        log_hc = np.log(high / close)
        log_lc = np.log(low / close)

    # Rogers-Satchell per-bar contribution. RS 1991 variance estimate:
    #   σ_rs² per bar = log(H/C)·log(H/O) + log(L/C)·log(L/O)
    rs_per_bar = log_hc * log_ho + log_lc * log_lo

    # Yang-Zhang weighting constant (eq. 8): k = α / (1 + α + (n+1)/(n-1))
    # where α = 0.34 is the MSE-optimal constant from Yang & Zhang 2000.
    # Equivalent canonical form: k = 0.34 / (1.34 + (n+1)/(n-1)).
    # TTR R package (joshuaulrich/TTR R/volatility.R) uses alpha_TTR=1.34 with
    # k=(alpha_TTR-1)/(alpha_TTR+(N+1)/(N-1)) = 0.34/(1.34+(N+1)/(N-1)) — numerically
    # identical to the form here. The denominator 1+α = 1.34 accounts for the
    # relative variance of σ²_RS vs σ²_c under the diffusion model.
    # Fixed 2026-04-24 (Round-1 audit L-5: prior code used wrong α=1.34).
    alpha_yz = 0.34
    k = alpha_yz / (1.0 + alpha_yz + (lookback + 1.0) / (lookback - 1.0))

    # Rolling variances via pandas (simple, numerically stable).
    s_oc = pd.Series(log_oc_prev)
    s_co = pd.Series(log_co)
    s_rs = pd.Series(rs_per_bar)

    var_o = s_oc.rolling(lookback, min_periods=lookback).var(ddof=1)
    var_c = s_co.rolling(lookback, min_periods=lookback).var(ddof=1)
    mean_rs = s_rs.rolling(lookback, min_periods=lookback).mean()

    sigma2 = var_o + k * var_c + (1.0 - k) * mean_rs
    sigma = np.sqrt(np.maximum(sigma2.to_numpy(), 0.0))
    # Propagate NaN for negative / undefined windows.
    sigma[np.isnan(sigma2.to_numpy())] = np.nan
    return sigma


# ---------------------------------------------------------------------------
# Triple-barrier labels
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TripleBarrierConfig:
    """Configuration for :class:`TripleBarrierLabeler`.

    ``pt_sl`` is a 2-tuple ``(pt_mult, sl_mult)``. Per AFML §3.2 the
    upper barrier is ``pt_mult · σ_t`` above entry close and the
    lower barrier is ``sl_mult · σ_t`` below. Pass ``(m, m)`` for a
    symmetric barrier; ``m`` is the scalar used in the design doc's
    ``pt_sl_grid = [1.0, 1.5, 2.0]``.

    ``vertical_barrier`` is a :class:`pandas.Timedelta`.

    ``volatility_lookback`` is the YZ lookback in bars.
    """

    pt_sl: tuple[float, float]
    vertical_barrier: pd.Timedelta
    volatility_lookback: int


@dataclass(frozen=True)
class TripleBarrierLabel:
    """Single event's label output."""

    event_ts: pd.Timestamp
    label: int
    horizon_end_ts: pd.Timestamp
    barrier_hit: str  # one of "pt", "sl", "vertical"


class TripleBarrierLabeler:
    """Produce triple-barrier labels on an OHLC panel.

    Usage::

        cfg = TripleBarrierConfig(pt_sl=(1.5, 1.5),
                                  vertical_barrier=pd.Timedelta(minutes=60),
                                  volatility_lookback=60)
        labeler = TripleBarrierLabeler(cfg)
        labels = labeler.apply(panel_df, symbol_col="symbol")

    The method :meth:`apply` iterates row-by-row at the panel's base
    frequency (we drive the labeling at every bar; callers that want
    sparser events filter the output). The vertical barrier is
    expressed in wall time — we translate to positional offset via
    the panel's timestamp grid at call time.
    """

    def __init__(self, config: TripleBarrierConfig) -> None:
        if config.pt_sl[0] <= 0 or config.pt_sl[1] <= 0:
            raise ValueError(f"pt_sl multipliers must be > 0; got {config.pt_sl!r}.")
        if config.vertical_barrier <= pd.Timedelta(0):
            raise ValueError(
                f"vertical_barrier must be > 0; got {config.vertical_barrier!r}."
            )
        if config.volatility_lookback < 2:
            raise ValueError(
                f"volatility_lookback must be >= 2, got "
                f"{config.volatility_lookback}."
            )
        self.config = config

    # ------------------------------------------------------------------
    # Label horizon (for SplitSpec.purge)
    # ------------------------------------------------------------------

    def label_horizon_bars(self, bar_duration: pd.Timedelta) -> int:
        """Maximum number of future bars any label can consume.

        A :class:`~skie_ninja.backtest.splits.SplitSpec` uses this for
        its ``purge_window`` so training labels do not leak forward
        into the test fold.
        """
        return int(
            np.ceil(self.config.vertical_barrier / bar_duration)
        )

    # ------------------------------------------------------------------
    # Main apply
    # ------------------------------------------------------------------

    def apply(
        self,
        panel: pl.DataFrame,
        *,
        symbol_col: str = "symbol",
        time_col: str = "ts_event",
    ) -> pl.DataFrame:
        """Apply triple-barrier labeling.

        Input panel must carry columns ``{symbol_col, time_col,
        open, high, low, close}``. Output has one row per input row
        (one per bar per symbol) with additional columns
        ``label``, ``horizon_end_ts``, ``barrier_hit``, and
        ``volatility`` (the YZ estimate used).
        """
        required = {symbol_col, time_col, "open", "high", "low", "close"}
        missing = required - set(panel.columns)
        if missing:
            raise ValueError(f"panel missing required columns: {sorted(missing)}.")

        # Per-symbol apply.
        pieces: list[pl.DataFrame] = []
        for group in panel.partition_by(symbol_col, maintain_order=True):
            pieces.append(
                self._apply_single_symbol(group, symbol_col=symbol_col, time_col=time_col)
            )
        return pl.concat(pieces, how="vertical")

    def _apply_single_symbol(
        self,
        group: pl.DataFrame,
        *,
        symbol_col: str,
        time_col: str,
    ) -> pl.DataFrame:
        group = group.sort(time_col)
        ts = group.get_column(time_col).to_pandas()
        opens = group.get_column("open").to_numpy().astype(np.float64)
        highs = group.get_column("high").to_numpy().astype(np.float64)
        lows = group.get_column("low").to_numpy().astype(np.float64)
        closes = group.get_column("close").to_numpy().astype(np.float64)

        sigma = yang_zhang_volatility(
            open_=opens,
            high=highs,
            low=lows,
            close=closes,
            lookback=self.config.volatility_lookback,
        )

        vb = self.config.vertical_barrier
        pt_mult, sl_mult = self.config.pt_sl
        n = len(closes)

        labels = np.zeros(n, dtype=np.int64)
        horizon_end_ix = np.full(n, -1, dtype=np.int64)
        barrier_hit = ["vertical"] * n

        # Use searchsorted on ts to map vertical-barrier times to
        # positional indices. ts is a pandas Timestamp index; use
        # numpy-datetime64 for binary search.
        ts_arr = pd.to_datetime(ts).values.astype("datetime64[ns]")
        # Horizon position (first bar whose ts > event_ts + vb).
        horizon_ts = ts_arr + np.timedelta64(int(vb.total_seconds() * 1_000_000_000), "ns")
        # searchsorted returns insertion index for horizon_ts in ts_arr.
        horizon_pos = np.searchsorted(ts_arr, horizon_ts, side="right")

        for i in range(n):
            if np.isnan(sigma[i]) or sigma[i] <= 0:
                labels[i] = 0
                horizon_end_ix[i] = i
                barrier_hit[i] = "vertical"
                continue
            entry = closes[i]
            up = entry * np.exp(pt_mult * sigma[i])
            dn = entry * np.exp(-sl_mult * sigma[i])
            end = min(int(horizon_pos[i]), n)
            horizon_end_ix[i] = end - 1 if end > i else i
            label = 0
            hit = "vertical"
            for j in range(i + 1, end):
                if highs[j] >= up and lows[j] <= dn:
                    # Both barriers hit in same bar — indeterminate.
                    # AFML §3.2 does not prescribe a canonical tie-break;
                    # treating as vertical (label=0) is a conservative design
                    # choice to avoid spurious label assignment.
                    label = 0
                    hit = "vertical"
                    horizon_end_ix[i] = j
                    break
                if highs[j] >= up:
                    label = 1
                    hit = "pt"
                    horizon_end_ix[i] = j
                    break
                if lows[j] <= dn:
                    label = -1
                    hit = "sl"
                    horizon_end_ix[i] = j
                    break
            labels[i] = label
            barrier_hit[i] = hit

        horizon_end_ts = ts_arr[np.clip(horizon_end_ix, 0, n - 1)]
        return group.with_columns(
            [
                pl.Series("label", labels, dtype=pl.Int64),
                pl.Series("horizon_end_ts", horizon_end_ts),
                pl.Series("barrier_hit", barrier_hit, dtype=pl.Utf8),
                pl.Series("volatility", sigma, dtype=pl.Float64),
            ]
        )


__all__ = [
    "TripleBarrierConfig",
    "TripleBarrierLabel",
    "TripleBarrierLabeler",
    "yang_zhang_volatility",
]
