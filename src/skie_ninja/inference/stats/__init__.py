"""Statistical primitives: HAC long-run variance, Sharpe-ratio CI."""

from skie_ninja.inference.stats.hac import (
    BandwidthSelection,
    andrews1991_bartlett_bandwidth,
    nw1994_bartlett_bandwidth,
    nw_hac_variance,
)
from skie_ninja.inference.stats.ledoit_wolf_2008 import (
    DifferentialCIResult,
    ledoit_wolf_2008_differential_ci,
)
from skie_ninja.inference.stats.return_conventions import (
    arithmetic_to_log,
    log_to_arithmetic,
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
    "DifferentialCIResult",
    "SharpeCI",
    "andrews1991_bartlett_bandwidth",
    "arithmetic_to_log",
    "ledoit_wolf_2008_differential_ci",
    "lo2002_hac_adjusted_ci",
    "lo2002_iid_ci",
    "lo2002_prop2_eta_ci",
    "log_to_arithmetic",
    "nw1994_bartlett_bandwidth",
    "nw_hac_variance",
    "opdyke2007_ci",
    "sample_sharpe",
]
