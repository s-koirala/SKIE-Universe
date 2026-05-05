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
from typing import Any

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


# ---------------------------------------------------------------------------
# Opening-Range-Breakout (ORB) labels for H052a
# ---------------------------------------------------------------------------
#
# Per H052a frozen pre-reg [research/01_hypothesis_register/H052a/design.md] §4 +
# §15.1 errata addendum (2026-05-04):
#
#   - Entry: market order at fixed RTH time `entry_time_et` (default 10:30 ET)
#     on the front-month roll-adjusted contract; long-only per pre-reg.
#   - Profit target: `pt_mult × annualised_σ_lookback` above entry close.
#   - Stop loss:     `sl_mult × annualised_σ_lookback` below entry close.
#   - Time stop:     fixed RTH time `time_stop_et` (default 14:00 ET).
#   - Hard close:    fixed RTH time `hard_close_et` (default 15:55 ET).
#   - Volatility lookback grid: {30, 60, 120} minutes per design.md §4.
#   - PT/SL multiplier grids: {0.5, 1.0, 1.5} each per design.md §4.
#
# The HMM regime-gate is applied at the orchestrator level (per design.md §5);
# this labeller produces UNCONDITIONAL per-session ORB labels. The orchestrator
# composes labeller output with HMM-gate posterior to construct the H052a test
# statistic T_H052a = SR_gated − SR_unconditional.
#
# Volatility convention: realized variance via squared log-returns
# (Andersen-Bollerslev 1998 doi:10.2307/2527343) over the prior
# `realized_vol_lookback_minutes` window of 1-min bars, annualised by
# √(252 × 390 RTH bars) = √(98,280) ≈ 313.5. Matches the §3 emission feature
# convention (rv_realized).
#
# Per ADR-0013 §3.1.1 sizing-convention table: H052a is "First-hour ORB futures"
# archetype — 100%-of-equity at ORB-trigger; position closed at first-hour
# end OR PT/SL/timestop/hardclose. Daily-cleared session-cadence (avoids the
# bar-vs-session horizon issue that complicated H050's §3.1 forward projection
# per F-Q-2 / P1-H050-SESSION-AGGREGATE-FORWARD-PROJECTION). Note: ADR-0014
# §3.2 governs the canonical end-of-simulation 9-table summary, NOT the
# sizing convention; F-L-1 audit-remediate-loop 2026-05-04 corrected prior
# misattribution.


@dataclass(frozen=True)
class OpeningRangeBreakoutConfig:
    """Configuration for :class:`OpeningRangeBreakoutLabeller` (H052a).

    Per design.md §4 + §15.1 errata 2026-05-04:

      - ``pt_mult``, ``sl_mult``: profit-target / stop-loss multipliers
        of the annualised σ over the prior ``realized_vol_lookback_minutes``
        window. Both must be > 0. Pre-registered grid:
        ``{0.5, 1.0, 1.5}`` each (design.md §5 line 86).
      - ``realized_vol_lookback_minutes``: rolling window for σ.
        Pre-registered grid: ``{30, 60, 120}`` (design.md §5 line 85).
      - ``entry_time_et``, ``time_stop_et``, ``hard_close_et``:
        ET wall-clock times in ``"HH:MM"`` form. Defaults match
        design.md §4 (10:30 / 14:00 / 15:55 ET).
    """

    pt_mult: float
    sl_mult: float
    realized_vol_lookback_minutes: int
    entry_time_et: str = "10:30"
    time_stop_et: str = "14:00"
    hard_close_et: str = "15:55"

    def __post_init__(self) -> None:
        if self.pt_mult <= 0:
            raise ValueError(f"pt_mult must be > 0; got {self.pt_mult}.")
        if self.sl_mult <= 0:
            raise ValueError(f"sl_mult must be > 0; got {self.sl_mult}.")
        if self.realized_vol_lookback_minutes <= 0:
            raise ValueError(
                f"realized_vol_lookback_minutes must be > 0; got "
                f"{self.realized_vol_lookback_minutes}."
            )
        for fld in ("entry_time_et", "time_stop_et", "hard_close_et"):
            v = getattr(self, fld)
            if not (isinstance(v, str) and len(v) == 5 and v[2] == ":"):
                raise ValueError(
                    f"{fld} must be 'HH:MM' string; got {v!r}."
                )


@dataclass(frozen=True)
class OpeningRangeBreakoutLabel:
    """Single (symbol, session_date_et) ORB label output."""

    symbol: str
    session_date_et: pd.Timestamp  # midnight ET on the session date
    entry_ts: pd.Timestamp  # UTC; first bar at or after entry_time_et
    entry_price: float
    realized_vol_at_entry: float  # annualised σ
    pt_price: float
    sl_price: float
    exit_ts: pd.Timestamp
    exit_price: float
    exit_reason: str  # "pt" | "sl" | "timestop" | "hardclose" | "no_data"
    pnl_log: float  # log(exit_price / entry_price); raw (cost applied separately)


_RTH_BARS_PER_SESSION: int = 390  # 6.5 hr × 60 min


class OpeningRangeBreakoutLabeller:
    """Produce per-session ORB labels on a 1-min RTH OHLC panel (H052a).

    Usage::

        cfg = OpeningRangeBreakoutConfig(
            pt_mult=1.0,
            sl_mult=1.0,
            realized_vol_lookback_minutes=60,
        )
        labeller = OpeningRangeBreakoutLabeller(cfg)
        labels = labeller.apply(panel)

    Input panel must carry columns ``{symbol, ts_event (UTC), close}``.
    Output is one row per ``(symbol, session_date_et)`` pair with the
    fields of :class:`OpeningRangeBreakoutLabel`.

    Bars MUST be 1-minute RTH-only; the labeller does not filter ETH —
    callers must pre-filter to 09:30-16:00 ET per H052a design.md §2.

    Sessions with insufficient bars to compute realized vol or detect
    entry get ``exit_reason="no_data"`` and ``pnl_log=0.0``; downstream
    aggregation should treat these as zero-weight observations.
    """

    def __init__(self, config: OpeningRangeBreakoutConfig) -> None:
        self.config = config

    def apply(
        self,
        panel: pl.DataFrame,
        *,
        symbol_col: str = "symbol",
        time_col: str = "ts_event",
    ) -> pl.DataFrame:
        """Apply ORB labeling per (symbol, session_date_et).

        Returns a polars DataFrame with one row per (symbol, session)
        with columns matching :class:`OpeningRangeBreakoutLabel` fields.
        """
        required = {symbol_col, time_col, "close"}
        missing = required - set(panel.columns)
        if missing:
            raise ValueError(
                f"panel missing required columns: {sorted(missing)}."
            )

        labels: list[dict[str, Any]] = []
        for sym_group in panel.partition_by(symbol_col, maintain_order=True):
            symbol = sym_group[symbol_col][0]
            sym_labels = self._apply_single_symbol(
                sym_group, symbol=str(symbol), time_col=time_col
            )
            labels.extend(sym_labels)

        if not labels:
            return pl.DataFrame(
                schema={
                    "symbol": pl.Utf8,
                    "session_date_et": pl.Datetime("ns", "UTC"),
                    "entry_ts": pl.Datetime("ns", "UTC"),
                    "entry_price": pl.Float64,
                    "realized_vol_at_entry": pl.Float64,
                    "pt_price": pl.Float64,
                    "sl_price": pl.Float64,
                    "exit_ts": pl.Datetime("ns", "UTC"),
                    "exit_price": pl.Float64,
                    "exit_reason": pl.Utf8,
                    "pnl_log": pl.Float64,
                }
            )
        return pl.DataFrame(labels)

    def _apply_single_symbol(
        self,
        group: pl.DataFrame,
        *,
        symbol: str,
        time_col: str,
    ) -> list[dict[str, Any]]:
        group = group.sort(time_col)
        ts_utc = group.get_column(time_col).to_pandas()
        # Convert UTC → ET (America/New_York) for session-date + time-of-day.
        if ts_utc.dt.tz is None:
            ts_utc = ts_utc.dt.tz_localize("UTC")
        ts_et = ts_utc.dt.tz_convert("America/New_York")
        # session_date_et = ET calendar date as midnight-ET timestamp (UTC).
        session_dates_et = ts_et.dt.normalize().dt.tz_convert("UTC")
        time_of_day_et = ts_et.dt.strftime("%H:%M")
        closes = group.get_column("close").to_numpy().astype(np.float64)

        entry_t = self.config.entry_time_et
        timestop_t = self.config.time_stop_et
        hardclose_t = self.config.hard_close_et

        results: list[dict[str, Any]] = []
        # Performance fix (post-Round-2 stall investigation 2026-05-05):
        # Build per-session index slices ONCE via a single sort + groupby
        # rather than recomputing `(session_dates_et == session_date)` masks
        # for every session iteration (the prior O(N · S) implementation
        # produced ~7B ops on the H052a substrate at 2710 sessions × 2710 ×
        # 390 bars per symbol; ran > 27 min before kill). Now O(N) total.
        session_dates_arr = session_dates_et.to_numpy()
        time_of_day_arr = time_of_day_et.to_numpy()
        ts_utc_arr = ts_utc.to_numpy()
        # `pd.factorize` returns codes (per-row session group id) + uniques
        # (the actual session_date_et values). The data is already sorted by
        # ts_utc per the `group.sort(time_col)` above, so codes are also
        # contiguous-by-session — we can build per-session contiguous slices
        # with `np.diff(codes).nonzero()` boundaries.
        codes, unique_sessions_arr = pd.factorize(
            session_dates_et.dt.tz_convert("UTC"), sort=True
        )
        # Boundaries where codes change → per-session slice [start, end).
        n_total = codes.size
        if n_total == 0:
            return results
        change_points = np.concatenate(
            [[0], np.flatnonzero(np.diff(codes) != 0) + 1, [n_total]]
        )
        for k in range(len(change_points) - 1):
            start = int(change_points[k])
            end = int(change_points[k + 1])
            session_date = unique_sessions_arr[codes[start]]
            sess_idx = np.arange(start, end)
            sess_tod = time_of_day_arr[start:end]
            sess_closes = closes[start:end]
            sess_ts_utc = ts_utc_arr[start:end]

            # Find entry bar: first bar at or after entry_time_et.
            entry_local_idx = self._first_index_at_or_after(sess_tod, entry_t)
            if entry_local_idx is None:
                results.append(
                    self._no_data_label(symbol, session_date, sess_ts_utc)
                )
                continue
            entry_price = float(sess_closes[entry_local_idx])
            entry_ts_utc = pd.Timestamp(sess_ts_utc[entry_local_idx]).tz_localize(
                "UTC"
            ) if pd.Timestamp(sess_ts_utc[entry_local_idx]).tz is None else pd.Timestamp(sess_ts_utc[entry_local_idx])

            # Realized vol: prior `realized_vol_lookback_minutes` log-returns
            # ending at entry bar. Use bars in [entry_idx − lookback,
            # entry_idx) on the FULL panel (cross-session for lookback > the
            # entry-bar-position; otherwise within-session).
            global_entry_idx = sess_idx[entry_local_idx]
            lookback = self.config.realized_vol_lookback_minutes
            lo = max(0, global_entry_idx - lookback)
            window_closes = closes[lo : global_entry_idx + 1]  # +1 to include entry close
            if len(window_closes) < 2:
                results.append(
                    self._no_data_label(symbol, session_date, sess_ts_utc)
                )
                continue
            log_returns = np.diff(np.log(window_closes))
            if len(log_returns) < 2 or not np.isfinite(log_returns).all():
                results.append(
                    self._no_data_label(symbol, session_date, sess_ts_utc)
                )
                continue
            sigma_per_bar = float(log_returns.std(ddof=1))
            sigma_annualised = sigma_per_bar * float(np.sqrt(252.0 * _RTH_BARS_PER_SESSION))
            if not np.isfinite(sigma_annualised) or sigma_annualised <= 0:
                results.append(
                    self._no_data_label(symbol, session_date, sess_ts_utc)
                )
                continue

            # σ_horizon = σ_per_bar × √(remaining session bars to hard close)
            # per design.md §4. F-Q-10 fix (Round-2 audit-remediate-loop
            # 2026-05-04): removed dead σ_annualised pt_price/sl_price
            # computation that was overwritten in the original v1 code.
            n_remaining_bars = float(self._n_bars_between(entry_t, hardclose_t))
            sigma_horizon = sigma_per_bar * float(np.sqrt(n_remaining_bars))
            pt_price = float(entry_price * np.exp(self.config.pt_mult * sigma_horizon))
            sl_price = float(entry_price * np.exp(-self.config.sl_mult * sigma_horizon))

            # F-Q-15 fix (Round-2 audit-remediate-loop 2026-05-04 major):
            # PT/SL barrier resolution uses close-only price comparison
            # (`price_j = sess_closes[j]` below). Design intent per H052a
            # design.md §4 is close-based resolution at the 1-min bar grid;
            # intra-bar high/low tie-breaks (analog of TripleBarrierLabeler at
            # AFML §3.2) are NOT applied in H052a v1. A future
            # P1-H052A-INTRABAR-PT-SL-TIEBREAK robustness exhibit MAY add
            # high/low resolution if operator review of the KPI report card
            # reveals the close-only resolution is materially favourable vs
            # realistic execution.
            timestop_local_idx = self._first_index_at_or_after(sess_tod, timestop_t)
            hardclose_local_idx = self._first_index_at_or_after(sess_tod, hardclose_t)
            if hardclose_local_idx is None:
                hardclose_local_idx = len(sess_closes) - 1
            scan_end = hardclose_local_idx + 1

            exit_local_idx = hardclose_local_idx
            exit_reason = "hardclose"
            for j in range(entry_local_idx + 1, scan_end):
                price_j = float(sess_closes[j])
                if price_j >= pt_price:
                    exit_local_idx = j
                    exit_reason = "pt"
                    break
                if price_j <= sl_price:
                    exit_local_idx = j
                    exit_reason = "sl"
                    break
                if (
                    timestop_local_idx is not None
                    and j == timestop_local_idx
                    and exit_reason == "hardclose"
                ):
                    exit_local_idx = j
                    exit_reason = "timestop"
                    break

            exit_price = float(sess_closes[exit_local_idx])
            exit_ts_utc_value = sess_ts_utc[exit_local_idx]
            exit_ts_utc = pd.Timestamp(exit_ts_utc_value)
            if exit_ts_utc.tz is None:
                exit_ts_utc = exit_ts_utc.tz_localize("UTC")
            pnl_log = float(np.log(exit_price / entry_price))

            results.append(
                {
                    "symbol": symbol,
                    "session_date_et": pd.Timestamp(session_date),
                    "entry_ts": entry_ts_utc,
                    "entry_price": entry_price,
                    "realized_vol_at_entry": float(sigma_annualised),
                    "pt_price": pt_price,
                    "sl_price": sl_price,
                    "exit_ts": exit_ts_utc,
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "pnl_log": pnl_log,
                }
            )
        return results

    @staticmethod
    def _first_index_at_or_after(
        time_of_day: np.ndarray, target_hhmm: str
    ) -> int | None:
        """Return index of the first bar whose ET time-of-day ≥ target_hhmm.

        ``time_of_day`` is an array of "HH:MM" strings; comparison is
        lexicographic on the 5-char string which is equivalent to numeric
        time-of-day comparison since the format is fixed-width.
        """
        for idx, tod in enumerate(time_of_day):
            if tod >= target_hhmm:
                return int(idx)
        return None

    @staticmethod
    def _n_bars_between(start_hhmm: str, end_hhmm: str) -> int:
        """Number of 1-min bars between two ET wall-clock times (exclusive end)."""
        start_h, start_m = int(start_hhmm[:2]), int(start_hhmm[3:5])
        end_h, end_m = int(end_hhmm[:2]), int(end_hhmm[3:5])
        return max(0, (end_h * 60 + end_m) - (start_h * 60 + start_m))

    @staticmethod
    def _no_data_label(
        symbol: str,
        session_date: pd.Timestamp,
        sess_ts_utc: np.ndarray,
    ) -> dict[str, Any]:
        ts_zero = pd.Timestamp(sess_ts_utc[0]) if len(sess_ts_utc) > 0 else pd.Timestamp(session_date)
        if ts_zero.tz is None:
            ts_zero = ts_zero.tz_localize("UTC")
        return {
            "symbol": symbol,
            "session_date_et": pd.Timestamp(session_date),
            "entry_ts": ts_zero,
            "entry_price": float("nan"),
            "realized_vol_at_entry": float("nan"),
            "pt_price": float("nan"),
            "sl_price": float("nan"),
            "exit_ts": ts_zero,
            "exit_price": float("nan"),
            "exit_reason": "no_data",
            "pnl_log": 0.0,
        }


__all__ = [
    "TripleBarrierConfig",
    "TripleBarrierLabel",
    "TripleBarrierLabeler",
    "yang_zhang_volatility",
    "OpeningRangeBreakoutConfig",
    "OpeningRangeBreakoutLabel",
    "OpeningRangeBreakoutLabeller",
]
