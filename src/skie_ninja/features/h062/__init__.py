"""H062 feature factory — intraday Donchian-channel breakout components.

Per H062 design.md §3, the feature factory composes:
  - Donchian channel + first-fire breakout detector (donchian.py).
  - ATR via Wilder smoothing (re-exported from h055.atr).
  - Trend-filter ID_1 (TSMOM / ADX / OLS-slope-t / MA-cross; re-exported
    from h055.trend_identifiers).
  - News-time exclusion (via skie_ninja.utils.news_calendar).

Submodules:
  - donchian:  Donchian channel + first-fire filter.
  - features:  Full feature factory composition layer.

The h055 atr + trend-identifier primitives are re-exported here so H062
callers can `from skie_ninja.features.h062 import ...` without crossing
into H055 namespace directly. H062 v1 inherits all four H055 trend
identifiers per design.md §3 ID_1 spec.
"""

from skie_ninja.features.h055.atr import atr_wilder, true_range
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
from skie_ninja.features.h062.features import (
    H062FeatureConfig,
    H062Features,
    compute_h062_features,
    select_trend_id_side,
)

__all__ = [
    "DonchianChannel",
    "H062FeatureConfig",
    "H062Features",
    "atr_wilder",
    "compute_h062_features",
    "donchian_breakout_events",
    "donchian_channel",
    "first_fire_filter",
    "select_trend_id_side",
    "trend_id_a_ts_mom",
    "trend_id_b_adx",
    "trend_id_c_hac_ols_slope_t",
    "trend_id_d_ma_cross",
    "true_range",
]
