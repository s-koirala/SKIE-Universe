"""L-skewness τ_3 estimator + stationary-bootstrap CI per Hosking 1990.

Per ADR-0019 §Decision 1, the L-skewness τ_3 estimator of Hosking 1990 *J Royal
Stat Soc B* 52(1):105-124 (DOI 10.1111/j.2517-6161.1990.tb01775.x) is the
project-canonical payoff-shape KPI annotation. τ_3 ∈ [-1, 1] is a bounded,
robust-to-tail-mass, sample-unbiased measure of distributional asymmetry built
on linear combinations of order statistics (probability-weighted moments). It
dominates the classical Pearson sample-skewness ``m_3 / s^3`` on heavy-tailed
financial return series per Theodossiou 1998 *Management Science* 44(12):1650-
1661 (DOI 10.1287/mnsc.44.12.1650), where the third sample-moment estimator
diverges in expectation under realistic return-distribution tails.

Inferential CI on τ_3 via stationary-bootstrap per Politis-Romano 1994 *JASA*
89(428):1303-1313 (DOI 10.1080/01621459.1994.10476870) with block length
auto-selected by Politis-White 2004 + Patton-Politis-White 2009 correction.

Sample estimator (Hosking 1990 eq. 2.3 via probability-weighted moments):
  b_0 = (1/n) Σ_i x_{(i)}
  b_1 = (1/n) Σ_i x_{(i)} (i-1) / (n-1)            for i = 1..n
  b_2 = (1/n) Σ_i x_{(i)} (i-1)(i-2) / ((n-1)(n-2))  for i = 1..n
  λ_1 = b_0
  λ_2 = 2 b_1 − b_0
  λ_3 = 6 b_2 − 6 b_1 + b_0
  τ_3 = λ_3 / λ_2

Implementation per ``P1-L-SKEWNESS-PRIMITIVE-IMPL`` (mandated by ADR-0019).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    politis_white_block_length,
    stationary_bootstrap_indices,
)

__all__ = [
    "LSkewnessTau3CI",
    "l_moments_pwm",
    "l_skewness_tau3",
    "l_skewness_tau3_ci_stationary_bootstrap",
    "payoff_shape_annotation",
]


@dataclass(frozen=True)
class LSkewnessTau3CI:
    """Stationary-bootstrap CI on the L-skewness τ_3 estimator.

    Provenance fields:
    - block_length_method: "politis_white_2004" or "operator_supplied".
    """

    tau3: float
    ci_low: float
    ci_high: float
    n_obs: int
    n_bootstrap: int
    block_length: float
    block_length_method: str = "politis_white_2004"

    @property
    def excludes_threshold(self) -> Callable[[float], bool]:
        """Return predicate: does the CI exclude both +threshold and -threshold?

        Used by ``payoff_shape_annotation`` to determine whether the τ_3 CI
        clears the ±cutoff band (decisive skew classification) or straddles
        it (marginal classification).
        """

        def _predicate(threshold: float) -> bool:
            t = abs(float(threshold))
            return (self.ci_low > t) or (self.ci_high < -t)

        return _predicate


def l_moments_pwm(x: npt.ArrayLike) -> dict:
    """Sample L-moments λ_1, λ_2, λ_3 via probability-weighted moments.

    Per Hosking 1990 §2.3 eq. 2.3 unbiased PWM estimator. Sorts x internally;
    returns NaN for higher-order moments when sample size is too small to
    estimate them (λ_2 requires n ≥ 2; λ_3 requires n ≥ 3).

    Args:
        x: 1-D array of real-valued samples.

    Returns:
        Dict with keys ``b_0``, ``b_1``, ``b_2``, ``lambda_1``, ``lambda_2``,
        ``lambda_3``, ``n``. Unavailable moments are ``float("nan")``.

    Raises:
        ValueError: if ``x`` is empty or contains non-finite values.
    """
    arr = np.asarray(x, dtype=float).ravel()
    n = arr.size
    if n == 0:
        raise ValueError("l_moments_pwm requires non-empty input.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("l_moments_pwm requires all-finite input (no NaN/Inf).")

    xs = np.sort(arr)
    i = np.arange(1, n + 1, dtype=float)  # 1-indexed rank

    b_0 = float(xs.mean())

    if n >= 2:
        w1 = (i - 1.0) / (n - 1.0)
        b_1 = float((xs * w1).sum() / n)
        lambda_1 = b_0
        lambda_2 = 2.0 * b_1 - b_0
    else:
        b_1 = float("nan")
        lambda_1 = b_0
        lambda_2 = float("nan")

    if n >= 3:
        w2 = (i - 1.0) * (i - 2.0) / ((n - 1.0) * (n - 2.0))
        b_2 = float((xs * w2).sum() / n)
        lambda_3 = 6.0 * b_2 - 6.0 * b_1 + b_0
    else:
        b_2 = float("nan")
        lambda_3 = float("nan")

    return {
        "b_0": b_0,
        "b_1": b_1,
        "b_2": b_2,
        "lambda_1": lambda_1,
        "lambda_2": lambda_2,
        "lambda_3": lambda_3,
        "n": int(n),
    }


def l_skewness_tau3(x: npt.ArrayLike) -> float:
    """L-skewness τ_3 = λ_3 / λ_2 per Hosking 1990 §2.

    Always in [-1, 1] for proper distributions (Hosking 1990 Theorem 1).
    Symmetric distributions have τ_3 = 0.

    Args:
        x: 1-D array of real-valued samples (n ≥ 3 required for a finite
            estimate).

    Returns:
        Float; the sample τ_3 estimate. Returns NaN if n < 3 or if λ_2 = 0
        (degenerate constant input, or pathological sample where L-scale
        vanishes).
    """
    moments = l_moments_pwm(x)
    l1 = moments["lambda_1"]
    l2 = moments["lambda_2"]
    l3 = moments["lambda_3"]
    if not np.isfinite(l2) or not np.isfinite(l3):
        return float("nan")
    # Scale-aware degeneracy check: floating-point roundoff on a constant
    # input produces |λ_2| ≈ 1e-16 × scale rather than exact 0. Treat any
    # λ_2 below 1e-12 × max(1, |λ_1|) as degenerate.
    scale = max(1.0, abs(l1))
    if abs(l2) < 1e-12 * scale:
        return float("nan")
    return float(l3 / l2)


def l_skewness_tau3_ci_stationary_bootstrap(
    x: npt.ArrayLike,
    *,
    n_bootstrap: int = 1000,
    rng_seed: int = 42,
    block_length: float | None = None,
    confidence: float = 0.95,
) -> LSkewnessTau3CI:
    """Politis-Romano 1994 stationary-bootstrap percentile CI on τ_3.

    Block length is selected per Politis-White 2004 (with Patton-Politis-White
    2009 correction inside ``politis_white_block_length``) on the input series;
    if ``block_length`` is supplied explicitly, it overrides auto-selection.

    Args:
        x: 1-D array of real-valued samples (n ≥ 4 required for PW2004 block
            selection).
        n_bootstrap: Number of bootstrap replicates (default 1,000).
        rng_seed: Deterministic RNG seed (default 42).
        block_length: Optional explicit block length; if None, auto-selected.
        confidence: Two-sided CI coverage in (0, 1) (default 0.95).

    Returns:
        LSkewnessTau3CI with point τ_3 + percentile CI bounds + provenance.

    Raises:
        ValueError: if n < 4, confidence not in (0, 1), or n_bootstrap < 1.
    """
    arr = np.asarray(x, dtype=float).ravel()
    n = arr.size
    if n < 4:
        raise ValueError(f"l_skewness_tau3_ci_stationary_bootstrap requires n >= 4, got {n}.")
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}.")
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}.")

    if block_length is None:
        sel: BlockLengthSelection = politis_white_block_length(arr, bootstrap_type="stationary")
        bl = float(sel.block_length)
        bl_method = "politis_white_2004"
    else:
        if block_length < 1.0:
            raise ValueError(f"block_length must be >= 1, got {block_length}.")
        bl = float(block_length)
        bl_method = "operator_supplied"

    point = l_skewness_tau3(arr)
    rng = np.random.default_rng(rng_seed)
    boot = np.empty(n_bootstrap, dtype=float)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n=n, block_length=bl, rng=rng)
        boot[b] = l_skewness_tau3(arr[idx])

    finite_mask = np.isfinite(boot)
    if not finite_mask.any():
        return LSkewnessTau3CI(
            tau3=point,
            ci_low=float("nan"),
            ci_high=float("nan"),
            n_obs=int(n),
            n_bootstrap=int(n_bootstrap),
            block_length=bl,
            block_length_method=bl_method,
        )

    alpha = 1.0 - confidence
    lo = float(np.quantile(boot[finite_mask], alpha / 2.0))
    hi = float(np.quantile(boot[finite_mask], 1.0 - alpha / 2.0))

    return LSkewnessTau3CI(
        tau3=point,
        ci_low=lo,
        ci_high=hi,
        n_obs=int(n),
        n_bootstrap=int(n_bootstrap),
        block_length=bl,
        block_length_method=bl_method,
    )


def payoff_shape_annotation(
    tau3: float,
    ci_low: float,
    ci_high: float,
    cutoff: float = 0.1,
) -> str:
    """Map (τ_3, CI) to ADR-0019 §Decision 1 payoff-shape annotation.

    Decision rule:
      - τ_3 > +cutoff AND CI excludes +cutoff (ci_low > +cutoff) → ``skew-positive``
      - τ_3 < -cutoff AND CI excludes -cutoff (ci_high < -cutoff) → ``skew-negative``
      - τ_3 > +cutoff but CI crosses +cutoff → ``skew-positive-marginal``
      - τ_3 < -cutoff but CI crosses -cutoff → ``skew-negative-marginal``
      - otherwise → ``skew-flat``

    Args:
        tau3: Point estimate of L-skewness τ_3.
        ci_low: Lower CI bound.
        ci_high: Upper CI bound.
        cutoff: Decision threshold (default 0.1 per ADR-0019 operational).

    Returns:
        One of: ``"skew-positive"``, ``"skew-negative"``, ``"skew-flat"``,
        ``"skew-positive-marginal"``, ``"skew-negative-marginal"``.
    """
    c = abs(float(cutoff))
    if not np.isfinite(tau3):
        return "skew-flat"

    if tau3 > c:
        if np.isfinite(ci_low) and ci_low > c:
            return "skew-positive"
        return "skew-positive-marginal"
    if tau3 < -c:
        if np.isfinite(ci_high) and ci_high < -c:
            return "skew-negative"
        return "skew-negative-marginal"
    return "skew-flat"
