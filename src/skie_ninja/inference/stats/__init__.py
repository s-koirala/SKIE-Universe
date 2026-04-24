"""Statistical primitives: HAC long-run variance, Sharpe-ratio CI."""

from skie_ninja.inference.stats.hac import (
    BandwidthSelection,
    andrews1991_bartlett_bandwidth,
    nw_hac_variance,
    nw1994_bartlett_bandwidth,
)
from skie_ninja.inference.stats.sharpe_ci import (
    SharpeCI,
    lo2002_hac_adjusted_ci,
    lo2002_iid_ci,
    lo2002_prop2_eta_ci,
    opdyke2007_ci,
    sample_sharpe,
)

__all__ = [
    "BandwidthSelection",
    "SharpeCI",
    "andrews1991_bartlett_bandwidth",
    "lo2002_hac_adjusted_ci",
    "lo2002_iid_ci",
    "lo2002_prop2_eta_ci",
    "nw1994_bartlett_bandwidth",
    "nw_hac_variance",
    "opdyke2007_ci",
    "sample_sharpe",
]
