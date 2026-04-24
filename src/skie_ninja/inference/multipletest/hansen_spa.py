"""Hansen 2005 Superior Predictive Ability (SPA) test.

Tests the composite null

    H_0 : max_{k=1,...,m} E[d_{k,t}] <= 0

where ``d_{k,t}`` is a "relative performance" variable for strategy
``k`` at time ``t`` — positive values indicate strategy ``k``
outperforms the benchmark.  The caller supplies the matrix of
``d_{k,t}`` values already computed in the appropriate sign
convention (e.g., ``r_{strategy} - r_{benchmark}`` for a return-
maximizing setup, or ``L_{benchmark} - L_{strategy}`` for a loss-
minimizing setup).

The test improves on White 2000 "Reality Check" by being robust to
inclusion of strictly dominated alternatives: White's RC p-value is
driven toward 1 as poor-performing strategies are added to the
candidate set.  Hansen 2005 §2.4 proposes a data-dependent
recentering threshold ("consistent" recentering) that removes this
pathology asymptotically while retaining size control.

Dependence on stationary bootstrap
----------------------------------

Bootstrap p-values are computed via the Politis-Romano 1994
stationary bootstrap from :mod:`skie_ninja.inference.bootstrap`,
with block length selected by Politis-White 2004 (max across
columns for the multivariate ``d`` matrix).

Three recentering variants (Hansen 2005 §2.4)
---------------------------------------------

Each bootstrap replication computes

    T_SPA^{*b} = max_k max(0, sqrt(n) * (d_bar_k^{*b} - g_k) / omega_k)

where ``g_k`` is the recentering term:

- **SPA_l ("lower")**: ``g_k^l = max(d_bar_k, 0)``.  Drops every
  negative sample-mean strategy from the bootstrap recentering so
  its bootstrap statistic clusters around a negative value and is
  truncated by ``max(0, ·)``.  Yields the SMALLEST p-value of the
  three — an optimistic lower bound.
- **SPA_c ("consistent") — DEFAULT**: ``g_k^c = d_bar_k`` if
  ``sqrt(n) d_bar_k / omega_k >= -sqrt(2 log log n)``, else ``0``.
  The data-dependent rule from Hansen 2005 §2.4: drop strategies
  that are strongly dominated (below the Andrews 1999 threshold)
  from the recentering.  This is the canonical choice recommended
  in §2.4 and is what "the SPA test" refers to without qualifier.
- **SPA_u ("upper")**: ``g_k^u = d_bar_k`` for all ``k`` (equivalent
  to White 2000 "Reality Check" under the LFC — mu_k = 0 for every
  k).  Keeps every strategy in the bootstrap distribution, so poor
  performers inflate the bootstrap max and wash out the p-value.
  Yields the LARGEST p-value — the conservative upper bound.

For each variant, the p-value is

    p_SPA = (1/B) * #{ b : T_SPA^{*b} >= T_SPA }

where T_SPA is the same maximum-studentized-excess statistic
computed on the original sample.

Omega estimation
----------------

``omega_hat_k^2`` is a consistent estimator of
``var(sqrt(n) d_bar_k)``.  Two options:

- **bootstrap** (default): ``omega_hat_k^2 = var_b(sqrt(n) d_bar_k^{*b})``
  over the same bootstrap draws — the bootstrap-variance option
  discussed in Hansen 2005 §2.2 and used by the Hansen-Lunde
  `MulCom` Ox reference implementation.
- **hac**: Newey-West via :func:`skie_ninja.inference.stats.hac.nw_hac_variance`
  with NW 1994 automatic bandwidth.  Provided for users who want
  to decouple ``omega`` estimation from bootstrap resampling;
  slightly cheaper when ``m`` (number of strategies) is large.

References
----------

- Hansen, P. R. 2005. "A Test for Superior Predictive Ability".
  *Journal of Business & Economic Statistics* 23(4): 365-380.
  https://doi.org/10.1198/073500105000000063
- White, H. 2000. "A Reality Check for Data Snooping".
  *Econometrica* 68(5): 1097-1126.
  https://doi.org/10.1111/1468-0262.00152
  — the RC test SPA generalizes.
- Politis, D. N. & Romano, J. P. 1994 — stationary bootstrap.
- Politis, D. N. & White, H. 2004 — automatic block-length.
- Andrews, D. W. K. 1999. "Consistent Moment Selection Procedures
  for Generalized Method of Moments Estimation". *Econometrica*
  67(3): 543-564. https://doi.org/10.1111/1468-0262.00036
  — the ``sqrt(2 log log n)`` threshold used by Hansen's SPA_c.

Scope
-----

This module implements the scalar-benchmark SPA test — one
benchmark, ``m`` candidate strategies.  Multi-benchmark extensions
(Hansen, Lunde & Nason 2011 "Model Confidence Set") will be
implemented downstream of this module when H050's gate requires
them.  The MCS construction reuses the same stationary-bootstrap
draws produced here.

Verification status of primary-source claims
--------------------------------------------

Direct access to the Hansen 2005 JBES PDF via tandfonline was
blocked at audit time.  The recentering formulas for SPA_l, SPA_c,
SPA_u and the ``sqrt(2 log log n)`` threshold are verified against
(a) Hansen-Lunde MulCom Ox reference implementation conventions
and (b) the ``arch`` Python package's ``SPA``/``StepM`` classes
authored by Kevin Sheppard.  Specific section-level labels
("§2.2", "§2.4") follow secondary summaries and were not cross-
checked against the primary PDF in this revision; equation-number
references (eq. 4-5, eq. 7) are avoided in the docstring for the
same reason.  Tracked as Phase-1 follow-up ``P1-SPA-PDF-VERIFY``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    choose_block_length,
    stationary_bootstrap_indices,
)

_VARIANT_LABELS = Literal["lower", "consistent", "upper"]
_OMEGA_METHODS = Literal["bootstrap", "hac"]

# Float64 ULP as a variance-scale floor to guard against division
# by zero in studentized statistics for degenerate series. Applied
# consistently on the VARIANCE (omega^2) scale in both HAC and
# bootstrap omega branches below.
_EPS_FLOOR = float(np.finfo(np.float64).eps)


# Andrews 1999 consistent-threshold constant (sqrt(2 log log n)).
# Hansen 2005 §2.4 — not a free parameter.
def _andrews_threshold(n: int) -> float:
    """``sqrt(2 log log n)`` with safe lower bound for small n.

    Hansen 2005 §2.4 uses this Andrews 1999 constant.  For n < 8
    ``log log n`` is not well defined (<=0); we floor at 1e-12
    before sqrt so the threshold degenerates to ~0, i.e., the
    recentering becomes identical to SPA_l for very short series.
    """
    if n <= 3:
        return 0.0
    inner = math.log(math.log(max(float(n), math.e + 1e-9)))
    return math.sqrt(2.0 * max(inner, 0.0))


@dataclass(frozen=True)
class HansenSPAResult:
    """Output of :func:`hansen_spa_test`.

    Attributes
    ----------
    p_value
        Bootstrap p-value for the chosen variant (``consistent`` by
        default).
    p_value_lower
        SPA_l p-value — the SMALLEST of the three, an optimistic
        lower bound for bracketing.  (Hansen 2005 §2.4: SPA_l drops
        all negative-mean strategies from the recentering.)
    p_value_upper
        SPA_u p-value — the LARGEST of the three, matching White
        2000 Reality Check; conservative upper bound.
    statistic
        ``T_SPA = max_k max(0, sqrt(n) d_bar_k / omega_k)``.
    best_strategy_index
        Argmax of the studentized sample means (the strategy that
        drove the statistic).  Returned for downstream diagnostic /
        hypothesis-register use.
    best_strategy_mean
        ``d_bar_k`` for that strategy.
    n_bootstrap, n_obs, n_strategies
        Replication counts and shapes.
    block_length_selection
        :class:`BlockLengthSelection` used by the stationary
        bootstrap (either PW 2004 auto or caller-fixed).
    omega_method
        ``"bootstrap"`` or ``"hac"``.
    variant
        The primary variant whose p-value is returned in
        :attr:`p_value`.
    """

    p_value: float
    p_value_lower: float
    p_value_upper: float
    statistic: float
    best_strategy_index: int
    best_strategy_mean: float
    n_bootstrap: int
    n_obs: int
    n_strategies: int
    block_length_selection: BlockLengthSelection
    omega_method: str
    variant: str

    def to_dict(self) -> dict[str, object]:
        return {
            "p_value": self.p_value,
            "p_value_lower": self.p_value_lower,
            "p_value_upper": self.p_value_upper,
            "statistic": self.statistic,
            "best_strategy_index": self.best_strategy_index,
            "best_strategy_mean": self.best_strategy_mean,
            "n_bootstrap": self.n_bootstrap,
            "n_obs": self.n_obs,
            "n_strategies": self.n_strategies,
            "block_length_selection": self.block_length_selection.to_dict(),
            "omega_method": self.omega_method,
            "variant": self.variant,
        }


# ---------------------------------------------------------------------------
# Omega (per-strategy asymptotic variance) estimation
# ---------------------------------------------------------------------------


def _omega_hac(d: np.ndarray) -> np.ndarray:
    """``omega_hat_k = sqrt(n * LRV_k)`` via NW-HAC + NW 1994 bandwidth."""
    from skie_ninja.inference.stats.hac import (
        nw1994_bartlett_bandwidth,
        nw_hac_variance,
    )

    n, m = d.shape
    omega = np.empty(m, dtype=float)
    for k in range(m):
        bw_sel = nw1994_bartlett_bandwidth(d[:, k])
        lrv, _ = nw_hac_variance(d[:, k], bandwidth=bw_sel)
        # omega_k^2 = n * Var(d_bar_k) = n * (LRV/n) = LRV. Hansen
        # 2005 §2.2 definition.  Guard against LRV <= 0 (sign-
        # indefinite NW under short bandwidth) with floor at eps.
        omega[k] = math.sqrt(max(lrv, _EPS_FLOOR))
    return omega


def _omega_bootstrap(
    d: np.ndarray,
    boot_means: np.ndarray,
) -> np.ndarray:
    """Bootstrap estimate of ``omega_k = sqrt(n) * sd(d_bar_k^{*b})``.

    This is the bootstrap-variance option discussed in Hansen 2005
    §2.2.  ``boot_means`` has shape ``(n_bootstrap, m)`` of
    bootstrap means.
    """
    n = d.shape[0]
    # Population sd (ddof=0) is the conventional plug-in used by the
    # Hansen-Lunde MulCom Ox implementation.  Floor is applied on
    # the variance scale (omega^2 >= _EPS_FLOOR) so the HAC and
    # bootstrap branches both guarantee the same numerical lower
    # bound on asymptotic variance.
    var_boot_mean = boot_means.var(axis=0, ddof=0)
    omega_sq = np.maximum(n * var_boot_mean, _EPS_FLOOR)
    return np.sqrt(omega_sq)


# ---------------------------------------------------------------------------
# Recentering
# ---------------------------------------------------------------------------


def _recenter_terms(
    d_bar: np.ndarray,
    omega: np.ndarray,
    n: int,
) -> dict[str, np.ndarray]:
    """Compute g_k for all three Hansen 2005 §2.4 variants."""
    # SPA_l: g_k^l = max(d_bar, 0)
    g_lower = np.maximum(d_bar, 0.0)
    # SPA_u: g_k^u = d_bar
    g_upper = d_bar.copy()
    # SPA_c: g_k^c = d_bar if sqrt(n) d_bar / omega >= -threshold else 0
    threshold = _andrews_threshold(n)
    # Guard omega > 0
    omega_safe = np.maximum(omega, math.sqrt(_EPS_FLOOR))
    studentized = math.sqrt(n) * d_bar / omega_safe
    keep_mask = studentized >= -threshold
    g_consistent = np.where(keep_mask, d_bar, 0.0)
    return {
        "lower": g_lower,
        "consistent": g_consistent,
        "upper": g_upper,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def hansen_spa_test(
    d: npt.ArrayLike,
    *,
    n_bootstrap: int = 1000,
    block_length: float | None = None,
    variant: _VARIANT_LABELS = "consistent",
    omega_method: _OMEGA_METHODS = "bootstrap",
    rng: np.random.Generator | None = None,
) -> HansenSPAResult:
    """Run the Hansen 2005 SPA test on relative-performance matrix ``d``.

    Parameters
    ----------
    d
        Shape ``(n, m)``: ``n`` time-indexed observations,
        ``m`` candidate strategies.  Positive values indicate the
        strategy outperformed the benchmark at that observation.
        Caller is responsible for the sign convention (return-
        maximization vs loss-minimization).
    n_bootstrap
        Number of stationary-bootstrap replications.  Monte Carlo
        error on the p-value is ``O(1/sqrt(B))``; Hansen 2005
        used 1000 in the simulations of §3; 10000 is a common
        practitioner choice when the gate is tight.
    block_length
        Expected stationary-bootstrap block length.  ``None``
        triggers Politis-White 2004 auto-selection.
    variant
        ``"consistent"`` (default — Hansen 2005 §2.4), ``"lower"``,
        or ``"upper"``.  All three p-values are always returned;
        ``variant`` only selects which one goes in :attr:`p_value`.
    omega_method
        ``"bootstrap"`` (Hansen 2005 §2.2 bootstrap-variance) or ``"hac"``
        (decoupled NW-HAC via
        :func:`~skie_ninja.inference.stats.hac.nw_hac_variance`).
    rng
        NumPy Generator (caller-seeded for reproducibility).
    """
    arr = np.asarray(d, dtype=float)
    if arr.ndim != 2:
        raise ValueError(
            f"d must be 2-D (n x m); got ndim={arr.ndim}, shape={arr.shape}."
        )
    if not np.all(np.isfinite(arr)):
        raise ValueError("d contains non-finite values (NaN or inf).")
    n, m = arr.shape
    if n < 4 or m < 1:
        raise ValueError(
            f"hansen_spa_test requires n >= 4 and m >= 1; got n={n}, m={m}."
        )
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}.")
    if variant not in ("lower", "consistent", "upper"):
        raise ValueError(f"unknown variant: {variant!r}")
    if omega_method not in ("bootstrap", "hac"):
        raise ValueError(f"unknown omega_method: {omega_method!r}")
    if rng is None:
        rng = np.random.default_rng()

    # 1. Block length.
    if block_length is None:
        selection = choose_block_length(arr, bootstrap_type="stationary")
        bl = selection.block_length
    else:
        if block_length < 1.0:
            raise ValueError(f"block_length must be >= 1, got {block_length}.")
        selection = BlockLengthSelection(
            method="fixed",
            block_length=float(block_length),
            bootstrap_type="stationary",
            notes="caller-specified fixed block length.",
        )
        bl = float(block_length)

    # 2. Draw bootstrap indices ONCE and reuse across columns (Hansen
    # 2005 §2 — preserves cross-dependence).
    d_bar = arr.mean(axis=0)
    boot_means = np.empty((n_bootstrap, m), dtype=float)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n, block_length=bl, rng=rng)
        boot_means[b] = arr[idx].mean(axis=0)

    # 3. Omega.
    if omega_method == "bootstrap":
        omega = _omega_bootstrap(arr, boot_means)
    else:
        omega = _omega_hac(arr)

    # 4. Recentering terms for all three variants.
    g_by_variant = _recenter_terms(d_bar, omega, n)

    # 5. Sample statistic: T = max_k max(0, sqrt(n) d_bar_k / omega_k).
    sqrt_n = math.sqrt(n)
    omega_safe = np.maximum(omega, math.sqrt(_EPS_FLOOR))
    studentized = sqrt_n * d_bar / omega_safe
    T_stat = float(max(0.0, studentized.max()))
    best_idx = int(np.argmax(studentized))

    # 6. Bootstrap distribution for each variant.
    # T^{*b} = max_k max(0, sqrt(n) * (d_bar_k^{*b} - g_k) / omega_k)
    # Hansen 2005 §2.4 bootstrap analogue: T^{*b} = max_k max(0, sqrt(n)*(d_bar_k^{*b} - g_k)/omega_k).
    # Shared bootstrap means across variants — only g_k differs.
    p_values: dict[str, float] = {}
    for variant_name, g in g_by_variant.items():
        # Shape: (B, m)
        centered = sqrt_n * (boot_means - g[None, :]) / omega_safe[None, :]
        T_boot = np.maximum(0.0, centered.max(axis=1))
        p_values[variant_name] = float((T_boot >= T_stat).mean())

    return HansenSPAResult(
        p_value=p_values[variant],
        p_value_lower=p_values["lower"],
        p_value_upper=p_values["upper"],
        statistic=T_stat,
        best_strategy_index=best_idx,
        best_strategy_mean=float(d_bar[best_idx]),
        n_bootstrap=n_bootstrap,
        n_obs=n,
        n_strategies=m,
        block_length_selection=selection,
        omega_method=omega_method,
        variant=variant,
    )


__all__ = [
    "HansenSPAResult",
    "hansen_spa_test",
]
