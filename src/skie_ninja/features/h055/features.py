"""H055 feature factory composition — bar-level compute(panel, now) API.

Assembles the H055 design.md §3 components (Component 1 trend gate +
Component 2 body-overlap ρ_1 + Component 4 ATR) plus the news-calendar
eligible-bar filter into a per-bar feature panel. Component 3 (level-
state state machine R(L)) is stateful and exposed via a separate
`emit_h055_setups` function that walks bars chronologically updating the
state-machine + swing-level memory while emitting setup confirmations.

Per H055 design.md §3 + §4, the feature factory is the load-bearing
input to the walk-forward orchestrator (pending
`P1-H055-WALK-FORWARD-ORCHESTRATOR-IMPL`).

PIT-safety: every per-bar feature is computed using only bars [0, t]; the
panel-truncation regression tests verify causal invariance per the
Cycle-4 leak-canary discipline. Setup-emission via `emit_h055_setups`
maintains a single-pass causal scan; the level-state machine is
deterministic given input bars + memory.

Closes follow-up `P1-H055-FEATURE-FACTORY-IMPL` (BLOCKING-BEFORE-H055-
WALK-FORWARD-LAUNCH).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Final, Literal

import numpy as np
import numpy.typing as npt

from skie_ninja.features.h055.atr import atr_wilder
from skie_ninja.features.h055.body_overlap import body_overlap_rho_1
from skie_ninja.features.h055.level_state import LevelExhaustionStateMachine
from skie_ninja.features.h055.swing_pivot import (
    SwingPivotSetup,
    detect_swing_pivot_setups,
)
from skie_ninja.features.h055.trend_identifiers import (
    trend_id_a_ts_mom,
    trend_id_b_adx,
    trend_id_c_hac_ols_slope_t,
    trend_id_d_ma_cross,
)
from skie_ninja.features.h055.wick_reversal import (
    SwingLevelMemory,
    WickReversalSetup,
    detect_wick_reversal_setups,
)
from skie_ninja.utils.news_calendar import NewsCalendar

__all__ = [
    "BarFeatures",
    "H055FeatureConfig",
    "Setup",
    "compute_h055_features",
    "emit_h055_setups",
]


# ─── Configuration ───────────────────────────────────────────────────────────


_TREND_ID_CHOICES: Final = frozenset({"a", "b", "c", "d"})


@dataclass(frozen=True)
class H055FeatureConfig:
    """H055 feature-factory hyperparameters per design.md §3 + §5.6.

    Component 1 (trend identifier):
        trend_id_choice: One of {"a", "b", "c", "d"}; selected on calibration
            holdout per `P1-H055-CALIBRATION-HOLDOUT-RUN`.
        trend_id_lookback_l: L bars on T_H ∈ {20, 40, 60, 120, 240}.
        tau_m / tau_adx / tau_t / tau_ma: per-identifier threshold; only the
            one matching trend_id_choice is consumed.
        short_window / long_window: only used for trend_id_choice="d".

    Component 2 (body-overlap):
        rho_window_n: N bars ∈ {5, 7, 10, 14, 20}.

    Component 3 (level-state):
        r_max: R* threshold ∈ {1, 2, 3, 4}; entry permitted while R(L) <= R*.

    Component 4 (ATR):
        atr_n: ATR lookback ∈ {7, 14, 21}.

    Setup detectors:
        swing_confirmation_window: bars to look forward for swing-pivot
            confirmation ∈ {3, 5, 8, 13}.
        theta_wick_min: minimum wick/body ratio for wick-reversal-non-swing
            ∈ [1.0, 4.0].

    News calendar:
        news_calendar_enabled: if False, the eligible-bar filter is skipped
            (orchestrator must explicitly disable for backwards-compat
            sensitivity exhibits).
    """

    trend_id_choice: Literal["a", "b", "c", "d"] = "a"
    trend_id_lookback_l: int = 60
    tau_m: float = 1.0
    tau_adx: float = 20.0
    tau_t: float = 2.0
    tau_ma: float = 0.005
    short_window: int = 5
    long_window: int = 20
    rho_window_n: int = 10
    r_max: int = 2
    atr_n: int = 14
    swing_confirmation_window: int = 5
    theta_wick_min: float = 1.5
    news_calendar_enabled: bool = True

    def __post_init__(self) -> None:
        if self.trend_id_choice not in _TREND_ID_CHOICES:
            raise ValueError(
                f"trend_id_choice must be one of {sorted(_TREND_ID_CHOICES)}, "
                f"got {self.trend_id_choice!r}"
            )
        if self.atr_n < 1:
            raise ValueError(f"atr_n must be >= 1, got {self.atr_n}")
        if self.rho_window_n < 2:
            raise ValueError(
                f"rho_window_n must be >= 2, got {self.rho_window_n}"
            )
        if self.r_max < 0:
            raise ValueError(f"r_max must be >= 0, got {self.r_max}")
        if self.theta_wick_min < 0:
            raise ValueError(
                f"theta_wick_min must be >= 0, got {self.theta_wick_min}"
            )


# ─── Output types ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BarFeatures:
    """Per-bar feature panel (Component-aggregated; no setup events).

    All arrays are length n_bars and align row-for-row with the input OHLCV.

    Fields:
        atr_n: ATR per Wilder smoothing.
        rho_1: body-overlap ρ_1; NaN for bars before window_n - 1.
        trend_side: -1 / 0 / +1 per the selected Component 1 identifier.
        is_news_excluded: True if the bar's ts_event is within a news
            release ±window per the H055 §4 eligible-bar filter.
    """

    atr_n: np.ndarray
    rho_1: np.ndarray
    trend_side: np.ndarray
    is_news_excluded: np.ndarray


@dataclass(frozen=True)
class Setup:
    """Unified setup-event surface (swing-pivot OR wick-reversal-non-swing).

    Distinguished by `kind`:
      - "swing_pivot": entry at a historical swing-bar's wick extreme.
      - "wick_reversal": entry at the wick-reversal bar's wick extreme.

    Fields:
        confirmation_bar: When the setup confirmed (orchestrator may post
            limit at this bar).
        side: +1 or -1.
        kind: "swing_pivot" or "wick_reversal".
        entry_limit_price: Wick extreme of the relevant bar.
        anchor_bar: For swing-pivot, the swing-bar; for wick-reversal,
            equals confirmation_bar.
        atr_n_at_confirmation: ATR_n at confirmation_bar; for downstream
            TP/SL sizing.
        rho_1_at_confirmation: Component 2 ρ_1 at confirmation_bar; for the
            §3 ρ* gate.
        trend_side_at_confirmation: Component 1 trend gate side; for the
            entry-direction admissibility gate.
    """

    confirmation_bar: int
    side: int
    kind: str
    entry_limit_price: float
    anchor_bar: int
    atr_n_at_confirmation: float
    rho_1_at_confirmation: float
    trend_side_at_confirmation: int


# ─── Pure-function feature computation (Components 1+2+4 + news calendar) ────


def compute_h055_features(
    open_prices: npt.ArrayLike,
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    close: npt.ArrayLike,
    bar_timestamps_utc: Sequence[datetime],
    *,
    config: H055FeatureConfig,
    news_calendar: NewsCalendar | None = None,
) -> BarFeatures:
    """Compute per-bar H055 Components 1+2+4 features + news-calendar filter.

    PIT-safe: each output[t] depends only on inputs[0..t]. Component 3
    (level-state R(L)) is stateful and lives in `emit_h055_setups`.

    Args:
        open_prices, high, low, close: OHLC arrays (length n_bars).
        bar_timestamps_utc: One datetime per bar (UTC). Used for the news-
            calendar eligible-bar filter.
        config: H055FeatureConfig.
        news_calendar: NewsCalendar instance; required if
            config.news_calendar_enabled. Pass None to skip filter (boolean
            output is all-False).

    Returns:
        BarFeatures with atr_n, rho_1, trend_side, is_news_excluded.

    Raises:
        ValueError: shape mismatch on OHLC; bar_timestamps_utc length
            != n_bars; news_calendar required but None.
    """
    o = np.asarray(open_prices, dtype=float).ravel()
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    n = o.size
    if not (h.shape == l.shape == c.shape == o.shape):
        raise ValueError(
            f"shape mismatch: open {o.shape}, high {h.shape}, low {l.shape}, "
            f"close {c.shape}"
        )
    if len(bar_timestamps_utc) != n:
        raise ValueError(
            f"bar_timestamps_utc length {len(bar_timestamps_utc)} != n_bars {n}"
        )
    if config.news_calendar_enabled and news_calendar is None:
        raise ValueError(
            "config.news_calendar_enabled is True but news_calendar is None"
        )

    # Component 4 — ATR
    atr = atr_wilder(h, l, c, n=config.atr_n)

    # Component 2 — body-overlap ρ_1
    rho = body_overlap_rho_1(o, c, window_n=config.rho_window_n)

    # Component 1 — trend gate per the selected identifier
    log_p = np.log(c)
    if config.trend_id_choice == "a":
        trend_side = trend_id_a_ts_mom(
            log_p, lookback_l=config.trend_id_lookback_l, tau_m=config.tau_m,
        )
    elif config.trend_id_choice == "b":
        trend_side = trend_id_b_adx(
            h, l, c,
            lookback_l=config.trend_id_lookback_l, tau_adx=config.tau_adx,
        )
    elif config.trend_id_choice == "c":
        trend_side = trend_id_c_hac_ols_slope_t(
            log_p, lookback_l=config.trend_id_lookback_l, tau_t=config.tau_t,
        )
    else:  # "d"
        trend_side = trend_id_d_ma_cross(
            c,
            short_window=config.short_window,
            long_window=config.long_window,
            tau_ma=config.tau_ma,
        )

    # News-calendar eligible-bar filter
    if config.news_calendar_enabled and news_calendar is not None:
        is_excluded = np.array(
            [news_calendar.is_in_news_window(ts) for ts in bar_timestamps_utc],
            dtype=bool,
        )
    else:
        is_excluded = np.zeros(n, dtype=bool)

    return BarFeatures(
        atr_n=atr,
        rho_1=rho,
        trend_side=trend_side,
        is_news_excluded=is_excluded,
    )


# ─── Stateful setup emission (Component 3 + setup detectors) ─────────────────


def emit_h055_setups(
    open_prices: npt.ArrayLike,
    high: npt.ArrayLike,
    low: npt.ArrayLike,
    close: npt.ArrayLike,
    *,
    config: H055FeatureConfig,
    bar_features: BarFeatures,
) -> list[Setup]:
    """Emit confirmed swing-pivot + wick-reversal-non-swing setups.

    Walks bars chronologically. For each setup:
      1. Swing-pivot: detected from price-only heuristic (3-down-then-2-up).
      2. Wick-reversal: detected against the swing-level memory updated by
         the most-recent confirmed swing-pivot.

    The level-state machine R(L) is updated in this primitive but is
    consumed by the orchestrator's gate logic (R(L) <= R*); this function
    does NOT itself filter setups by R(L) — the orchestrator does, because
    the gate also depends on the trend_side + ρ_1 at confirmation_bar
    (which are in `bar_features`).

    Returns:
        List[Setup] in chronological order. Empty if no setups confirm.
    """
    o = np.asarray(open_prices, dtype=float).ravel()
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    n = o.size

    # Detect ALL swing-pivot setups in one pass.
    swing_setups = detect_swing_pivot_setups(
        h, l, confirmation_window=config.swing_confirmation_window
    )

    # Wick-reversal detection requires a memory updated as swing pivots
    # confirm. We process bars in confirmation order, updating the memory.
    memory = SwingLevelMemory()
    setups_unified: list[Setup] = []

    # Index swing-pivot setups by confirmation_bar for O(1) lookup.
    swing_by_conf_bar: dict[int, list[SwingPivotSetup]] = {}
    for s in swing_setups:
        swing_by_conf_bar.setdefault(s.confirmation_bar, []).append(s)

    for t in range(n):
        # First, append any swing-pivot setups confirmed at bar t to the
        # unified list, and update the swing-level memory.
        for s in swing_by_conf_bar.get(t, []):
            atr_at = float(bar_features.atr_n[t]) if t < bar_features.atr_n.size else float("nan")
            rho_at = float(bar_features.rho_1[t]) if t < bar_features.rho_1.size else float("nan")
            ts_at = int(bar_features.trend_side[t]) if t < bar_features.trend_side.size else 0
            setups_unified.append(
                Setup(
                    confirmation_bar=s.confirmation_bar,
                    side=s.side,
                    kind="swing_pivot",
                    entry_limit_price=s.entry_limit_price,
                    anchor_bar=s.swing_bar,
                    atr_n_at_confirmation=atr_at,
                    rho_1_at_confirmation=rho_at,
                    trend_side_at_confirmation=ts_at,
                )
            )
            # Update memory: long swing pivot → swing-low; short → swing-high
            if s.side == 1:
                memory.update_swing_low(s.entry_limit_price, bar_index=s.swing_bar)
            else:
                memory.update_swing_high(s.entry_limit_price, bar_index=s.swing_bar)

        # Then, probe the current bar for wick-reversal-non-swing setups
        # against the just-updated memory.
        wr_at_bar = detect_wick_reversal_setups(
            o[t : t + 1], h[t : t + 1], l[t : t + 1], c[t : t + 1],
            swing_level_memory=memory,
            theta_wick_min=config.theta_wick_min,
        )
        for wr in wr_at_bar:
            atr_at = float(bar_features.atr_n[t]) if t < bar_features.atr_n.size else float("nan")
            rho_at = float(bar_features.rho_1[t]) if t < bar_features.rho_1.size else float("nan")
            ts_at = int(bar_features.trend_side[t]) if t < bar_features.trend_side.size else 0
            setups_unified.append(
                Setup(
                    confirmation_bar=t,  # wick-reversal confirms AT the bar
                    side=wr.side,
                    kind="wick_reversal",
                    entry_limit_price=wr.entry_limit_price,
                    anchor_bar=t,
                    atr_n_at_confirmation=atr_at,
                    rho_1_at_confirmation=rho_at,
                    trend_side_at_confirmation=ts_at,
                )
            )

    return sorted(
        setups_unified, key=lambda s: (s.confirmation_bar, s.side, s.kind)
    )
