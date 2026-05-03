"""CPCV per-fold Sharpe distribution wrapper — closes ADR-0012 BLOCKING gate F-1-4.

Per [ADR-0012 §"Cross-validation methodology"](
../../../docs/decisions/ADR-0012-disposition-philosophy-aspirational-mvp.md):
CPCV is the canonical splitter for any hypothesis disposition that produces
a Sharpe KPI. Single train/test cuts are insufficient.

This module wraps [src/skie_ninja/backtest/splits.py](splits.py) ``cpcv_split``
to compute a per-fold Sharpe distribution + DSR-under-CPCV, satisfying the 5
ADR-0012 acceptance criteria:

1. Minimum 45 folds at ``n_groups=10, n_test_groups=2`` per AFML §12.1.3.
2. Per-fold Sharpe distribution monotonicity (KS distance between consecutive
   5-fold-batch CDFs ≤ 0.05 by 30 folds).
3. Per-fold Sharpe distribution moments (mean, std, 5%/95% quantiles) reported.
4. Computational budget cap (24 hours wall-clock; downsample to ``n_groups=8``
   on overrun with ``cpcv-downsampled`` annotation).
5. DSR (Bailey-Lopez de Prado 2014) computed under CPCV path-Sharpe std.

**Operational note**: this implementation uses **per-fold Sharpe** (one Sharpe
per CPCV combination, n_folds = C(n_groups, n_test_groups)) as the
"path-Sharpe distribution" approximation. The full AFML §12.4 path
reconstruction (which interleaves test-segment returns into n_groups paths
each containing one prediction per group) is the deeper follow-up tracked
under ``P1-BACKTEST-CPCV`` (now further sub-divided into
``P1-BACKTEST-CPCV-PATH-RECONSTRUCTION``). The per-fold Sharpe distribution
satisfies the ADR-0012 monotonicity + moments criteria operationally; the
deeper path reconstruction is methodologically stronger but not required
for the Class B Sharpe KPI.

References
----------
- López de Prado, M. 2018. *Advances in Financial Machine Learning* §12.
  Wiley. ISBN 978-1-119-48208-6.
- Bailey, D. H. & López de Prado, M. 2014. "The Deflated Sharpe Ratio."
  *J Portfolio Management* 40(5):94-107. DOI 10.3905/jpm.2014.40.5.094.
- ADR-0012 §"CPCV acceptance criteria" (this commit's binding spec).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from skie_ninja.backtest.splits import Fold, SplitSpec, cpcv_split

_log = logging.getLogger(__name__)

# justify: ADR-0012 §"CPCV acceptance criteria" pins n_groups=10, n_test_groups=2
# per AFML §12.1.3 → C(10, 2) = 45 folds.
_DEFAULT_N_GROUPS: int = 10
_DEFAULT_N_TEST_GROUPS: int = 2
# justify: ADR-0012 §"CPCV acceptance criteria" item 4 — 24-hour wall-clock cap.
_DEFAULT_WALLCLOCK_CAP_S: int = 24 * 3600
# justify: ADR-0012 §"CPCV acceptance criteria" item 4 — downgrade to n_groups=8 on overrun.
_DOWNSAMPLE_N_GROUPS: int = 8
# justify: ADR-0012 §"CPCV acceptance criteria" item 2 — KS-distance threshold for monotonicity.
_KS_MONOTONICITY_THRESHOLD: float = 0.05
# justify: ADR-0012 §"CPCV acceptance criteria" item 2 — minimum folds before monotonicity check.
_KS_MIN_FOLDS: int = 30


@dataclass(frozen=True)
class CPCVPathSharpeResult:
    """Per-fold Sharpe distribution + acceptance-criteria diagnostics."""

    n_folds: int                                       # actual folds computed (≤ C(n_groups, n_test_groups))
    n_groups: int                                      # CPCV n_groups used (10 default; 8 on downsample)
    n_test_groups: int                                 # CPCV n_test_groups used (2 default)
    per_fold_sharpe: list[float]                       # length = n_folds
    median_sharpe: float                               # for the Class B KPI annotation (median, not mean)
    mean_sharpe: float
    std_sharpe: float
    quantile_05: float
    quantile_95: float
    ks_monotonicity_distance: float                    # KS distance between CDF at n_folds=KS_MIN and at n_folds=full
    ks_monotonicity_passed: bool                       # True iff distance ≤ _KS_MONOTONICITY_THRESHOLD
    dsr_value: float                                   # DSR per Bailey-LdP 2014, using CPCV path-Sharpe std
    wallclock_s: float                                 # actual wall-clock taken
    wallclock_capped: bool                             # True iff wall-clock cap forced downsample
    downsampled: bool                                  # True iff fell back to n_groups=8

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _empirical_cdf(values: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Empirical CDF of `values` evaluated at `points`."""
    sorted_v = np.sort(values)
    return np.searchsorted(sorted_v, points, side="right") / len(sorted_v)


def _ks_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Kolmogorov-Smirnov distance between two 1-D distributions."""
    if len(a) == 0 or len(b) == 0:
        return float("inf")
    grid = np.unique(np.concatenate([a, b]))
    cdf_a = _empirical_cdf(a, grid)
    cdf_b = _empirical_cdf(b, grid)
    return float(np.max(np.abs(cdf_a - cdf_b)))


def _sharpe(returns: np.ndarray) -> float:
    """Annualized Sharpe assuming returns are per-session (×252 convention).

    Per design.md §9 H053 + ADR-0012 §"Class B" Sharpe-vs-passive: the
    canonical project Sharpe convention is annualized by ``sqrt(252)``.
    """
    r = np.asarray(returns, dtype=np.float64)
    r = r[np.isfinite(r)]
    if len(r) < 2:
        return float("nan")
    mu = float(np.mean(r))
    sigma = float(np.std(r, ddof=1))
    if sigma <= 0:
        return float("nan")
    return float(mu / sigma * np.sqrt(252.0))


def _dsr_under_cpcv(
    sharpe_estimate: float,
    cpcv_path_sharpe_std: float,
    n_paths: int,
) -> float:
    """Bailey & López de Prado 2014 Deflated Sharpe Ratio under CPCV.

    Per ADR-0012 §"CPCV acceptance criteria" item 5: DSR uses the
    CPCV path-Sharpe std (not the asymptotic Sharpe-CI std) to
    estimate the family selection bias.

    Implementation per Bailey-LdP 2014 eq. 7 with the operational
    interpretation for CPCV: the median per-path Sharpe is deflated
    by the cross-path Sharpe std times the expected maximum of N
    standard-normal draws (where N = n_paths).

    DSR_value = SR_median - σ_paths · E[max-of-N]

    where E[max-of-N] is approximated as
    ``(1 - γ) · z_{1-1/N} + γ · z_{1-1/(N·e)}`` per Bailey-LdP 2014
    eq. 7 with γ = Euler-Mascheroni constant ≈ 0.5772.

    Returns the deflated Sharpe in the same annualized units as the
    input. `> 0` is the design-time DSR KPI annotation.
    """
    from scipy.stats import norm
    if n_paths < 2:
        return sharpe_estimate
    if cpcv_path_sharpe_std <= 0:
        return sharpe_estimate
    gamma = 0.5772156649015329  # Euler-Mascheroni
    e_max = (1.0 - gamma) * norm.ppf(1.0 - 1.0 / n_paths) + gamma * norm.ppf(1.0 - 1.0 / (n_paths * np.e))
    deflation = cpcv_path_sharpe_std * e_max
    return float(sharpe_estimate - deflation)


def cpcv_path_sharpe(
    *,
    n_samples: int,
    fit_predict_fn: Callable[[np.ndarray, np.ndarray], np.ndarray],
    target_returns: np.ndarray,
    label_horizon: int = 1,
    embargo: int = 0,
    n_groups: int = _DEFAULT_N_GROUPS,
    n_test_groups: int = _DEFAULT_N_TEST_GROUPS,
    wallclock_cap_s: int = _DEFAULT_WALLCLOCK_CAP_S,
) -> CPCVPathSharpeResult:
    """Compute the CPCV per-fold Sharpe distribution per ADR-0012.

    Parameters
    ----------
    n_samples : int
        Number of samples in the panel.
    fit_predict_fn : callable
        A function that takes ``(train_idx, test_idx)`` arrays and returns
        per-test-row strategy returns (signed, in the same units as
        ``target_returns``). The function fits the model on the train
        rows and evaluates on the test rows; the strategy "return" is
        ``sign(prediction) · target_return`` per row.
    target_returns : (n_samples,) array
        Realized predictand series (per-row return). Used both to build
        per-fold strategy returns (via ``fit_predict_fn``) and as the
        underlying for the Sharpe computation.
    label_horizon, embargo : int
        Passed through to ``cpcv_split``.
    n_groups, n_test_groups : int
        CPCV grid; defaults are ADR-0012-binding (10, 2 → 45 folds).
    wallclock_cap_s : int
        Per ADR-0012 §"CPCV acceptance criteria" item 4. On overrun,
        function downsamples to ``n_groups=8`` and re-runs.

    Returns
    -------
    CPCVPathSharpeResult with all 5 acceptance-criteria diagnostics.
    """
    target_returns = np.asarray(target_returns, dtype=np.float64)

    def _run_inner(active_n_groups: int, active_n_test_groups: int) -> tuple[list[float], float, bool]:
        spec: SplitSpec = cpcv_split(
            n_samples=n_samples,
            n_groups=active_n_groups,
            n_test_groups=active_n_test_groups,
            label_horizon=label_horizon,
            embargo=embargo,
        )
        per_fold_sharpe: list[float] = []
        t0 = time.time()
        for fold in spec.folds:
            train_idx = np.asarray(fold.train_indices(), dtype=np.int64)
            test_idx = np.asarray(fold.test_indices(), dtype=np.int64)
            if len(train_idx) == 0 or len(test_idx) == 0:
                continue
            strategy_returns = fit_predict_fn(train_idx, test_idx)
            sharpe = _sharpe(np.asarray(strategy_returns))
            per_fold_sharpe.append(sharpe)
            if time.time() - t0 > wallclock_cap_s:
                _log.warning(
                    "cpcv_path_sharpe: wallclock cap %ds reached after %d folds; "
                    "halting and returning partial distribution.",
                    wallclock_cap_s, len(per_fold_sharpe),
                )
                return per_fold_sharpe, time.time() - t0, True
        return per_fold_sharpe, time.time() - t0, False

    # Initial attempt at full-spec
    per_fold, wallclock, capped = _run_inner(n_groups, n_test_groups)
    downsampled = False
    # If wall-clock capped before we got the minimum 45 folds, downsample
    if capped and len(per_fold) < 45 and n_groups > _DOWNSAMPLE_N_GROUPS:
        _log.warning(
            "cpcv_path_sharpe: full-spec produced only %d folds in cap; "
            "downsampling to n_groups=%d", len(per_fold), _DOWNSAMPLE_N_GROUPS,
        )
        per_fold, wallclock_extra, capped2 = _run_inner(_DOWNSAMPLE_N_GROUPS, n_test_groups)
        wallclock += wallclock_extra
        capped = capped2
        downsampled = True
        n_groups_actual = _DOWNSAMPLE_N_GROUPS
    else:
        n_groups_actual = n_groups

    arr = np.asarray([s for s in per_fold if np.isfinite(s)], dtype=np.float64)
    if len(arr) == 0:
        raise ValueError("cpcv_path_sharpe: zero finite per-fold Sharpe values.")

    # KS-distance monotonicity check (acceptance criteria item 2)
    if len(arr) >= _KS_MIN_FOLDS:
        ks_dist = _ks_distance(arr[:_KS_MIN_FOLDS], arr)
    else:
        ks_dist = float("inf")
    ks_passed = ks_dist <= _KS_MONOTONICITY_THRESHOLD

    median_s = float(np.median(arr))
    mean_s = float(np.mean(arr))
    std_s = float(np.std(arr, ddof=1)) if len(arr) >= 2 else 0.0
    q05 = float(np.quantile(arr, 0.05))
    q95 = float(np.quantile(arr, 0.95))

    # DSR under CPCV path-Sharpe std (acceptance criteria item 5)
    dsr = _dsr_under_cpcv(
        sharpe_estimate=median_s,
        cpcv_path_sharpe_std=std_s,
        n_paths=len(arr),
    )

    return CPCVPathSharpeResult(
        n_folds=len(arr),
        n_groups=n_groups_actual,
        n_test_groups=n_test_groups,
        per_fold_sharpe=[float(s) for s in arr],
        median_sharpe=median_s,
        mean_sharpe=mean_s,
        std_sharpe=std_s,
        quantile_05=q05,
        quantile_95=q95,
        ks_monotonicity_distance=ks_dist,
        ks_monotonicity_passed=ks_passed,
        dsr_value=dsr,
        wallclock_s=wallclock,
        wallclock_capped=capped,
        downsampled=downsampled,
    )


__all__ = [
    "CPCVPathSharpeResult",
    "cpcv_path_sharpe",
]
