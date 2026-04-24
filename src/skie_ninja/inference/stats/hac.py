"""Newey-West HAC long-run variance with data-dependent bandwidth selection.

This module estimates the long-run variance of a (possibly serially
correlated, heteroskedastic) time series via the Newey-West 1987
heteroskedasticity-and-autocorrelation-consistent estimator with the
Bartlett kernel. Bandwidth (truncation lag) is chosen by one of two
data-dependent rules, neither of which is a magic default:

  - **Newey-West 1994 data-dependent rule** (`nw1994_bartlett_bandwidth`)
    — the procedure from Newey & West 1994 §2.2/§3, used when a
    pre-specified parametric model for the series is not available.
  - **Andrews 1991 AR(1)-plug-in rule** (`andrews1991_bartlett_bandwidth`)
    — the parametric-plug-in variant from Andrews 1991 Table 1 for the
    Bartlett kernel under an AR(1) approximation of the series.

Both are cited as canonical in the project's quant-project.md ruleset
(§Inference). The caller selects which to use; the chosen bandwidth
and method name are returned alongside the variance estimate so
downstream code can log them into the ReproLog (plan §9.3).

References
----------

  - Newey, W. K. & West, K. D. 1987. "A Simple, Positive Semi-Definite,
    Heteroskedasticity and Autocorrelation Consistent Covariance
    Matrix". *Econometrica* 55(3): 703-708. https://doi.org/10.2307/1913610
  - Andrews, D. W. K. 1991. "Heteroskedasticity and Autocorrelation
    Consistent Covariance Matrix Estimation". *Econometrica* 59(3):
    817-858. https://doi.org/10.2307/2938229
  - Newey, W. K. & West, K. D. 1994. "Automatic Lag Selection in
    Covariance Matrix Estimation". *Review of Economic Studies* 61(4):
    631-653. https://doi.org/10.2307/2297912

Scope
-----

The estimator here is the **scalar** (univariate) long-run variance.
Multivariate HAC (for regression standard errors) is out of scope for
Cycle 2 of the Tier-2b buildout — downstream Sharpe-ratio CIs and
Hansen SPA bootstrap only consume the scalar form.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

_BARTLETT_KERNEL = "bartlett"
# Constants from Andrews 1991 Table 1 (p. 835) and Newey-West 1994
# §2.2. Values are method-specific and derive from the kernel's
# shape — there are no free parameters to tune here.
_ANDREWS_BARTLETT_CONST = 1.1447  # Andrews 1991 Table 1, Bartlett kernel q=1 row.
_NW1994_BARTLETT_CONST = 1.1447   # NW 1994 §2.2 (same Bartlett constant).

# Numerical tolerance used internally to avoid division by zero when
# the long-run variance spectrum at origin is numerically zero.
# Choice justified by float64 ULP.
_EPS = float(np.finfo(np.float64).eps)


@dataclass(frozen=True)
class BandwidthSelection:
    """Record of how the bandwidth was chosen — written into ReproLog."""

    method: Literal["andrews1991_ar1_plugin", "nw1994_automatic", "fixed"]
    bandwidth: int
    kernel: str
    rho_hat: float | None = None          # AR(1) plug-in parameter (Andrews).
    m_initial: int | None = None          # NW 1994 initial lag (s(1)/s(0) stage).
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "bandwidth": self.bandwidth,
            "kernel": self.kernel,
            "rho_hat": self.rho_hat,
            "m_initial": self.m_initial,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Bandwidth-selection rules
# ---------------------------------------------------------------------------


def andrews1991_bartlett_bandwidth(x: npt.ArrayLike) -> BandwidthSelection:
    """Andrews 1991 Table 1 AR(1)-plug-in bandwidth for the Bartlett kernel.

    Procedure:

      1. Fit AR(1) to the (demeaned) series: ``u_t = ρ u_{t-1} + ε_t``.
      2. Compute ``α(1) = 4 ρ² / ((1-ρ)² (1+ρ)²)``. This is the
         scalar case of Andrews 1991 eq. 6.4 for the Bartlett kernel
         (q=1), with equal weighting across the series (a single
         scalar series, so the weighting reduction is trivial).
      3. Optimal Bartlett bandwidth: ``L* = 1.1447 (α(1) T)^(1/3)``.
      4. Round to nearest integer; floor at 0; cap at ``T-1``.

    Returns a :class:`BandwidthSelection` carrying the chosen
    bandwidth and the AR(1) ρ̂ for audit.

    Parameters
    ----------
    x
        1-D array of scalar observations. NaNs / infs are rejected;
        caller must clean upstream.
    """
    u = _as_clean_1d(x)
    t_len = u.size
    if t_len < 4:
        raise ValueError(
            f"andrews1991_bartlett_bandwidth requires at least 4 "
            f"observations; got {t_len}."
        )

    # AR(1) via lag-1 OLS on demeaned series (closed form).
    u_c = u - u.mean()
    num = float(np.dot(u_c[1:], u_c[:-1]))
    den = float(np.dot(u_c[:-1], u_c[:-1]))
    rho = num / den if den > 0 else 0.0
    rho = float(np.clip(rho, -0.999, 0.999))  # numerical guard

    alpha_1 = 4.0 * rho * rho / ((1.0 - rho) ** 2 * (1.0 + rho) ** 2)
    # α(1) can be huge when |ρ|→1; cap below at 0 for stability.
    alpha_1 = max(alpha_1, 0.0)

    bw_float = _ANDREWS_BARTLETT_CONST * (alpha_1 * t_len) ** (1.0 / 3.0)
    bw = int(max(0, min(round(bw_float), t_len - 1)))
    return BandwidthSelection(
        method="andrews1991_ar1_plugin",
        bandwidth=bw,
        kernel=_BARTLETT_KERNEL,
        rho_hat=rho,
        notes=(
            "Andrews 1991 Table 1 AR(1) plug-in; alpha(1)="
            f"{alpha_1:.6g}; L*_float={bw_float:.3f}."
        ),
    )


def nw1994_bartlett_bandwidth(
    x: npt.ArrayLike,
    *,
    c: float | None = None,
) -> BandwidthSelection:
    """Newey-West 1994 automatic Bartlett-kernel bandwidth.

    Procedure (Newey & West 1994 §2.2):

      1. Set initial lag ``m = floor(c * (T/100)^(2/9))``, default
         ``c = 4``. The ``c=4`` constant is Newey & West's own
         recommendation (1994 p. 636) for the Bartlett kernel in
         moderate-sample settings; it is NOT a tuned hyperparameter
         but a published default tied to the kernel's shape. The
         user may override via the ``c`` keyword for sensitivity
         analysis; overrides are logged.
      2. Compute weighted autocovariance sums
         ``s^(0) = σ_0 + 2 Σ_{j=1}^{m} σ_j``
         ``s^(1) = 2 Σ_{j=1}^{m} j σ_j``.
      3. Plug-in estimate of Andrews' γ̂ =
         ``1.1447 * ((s^(1)/s^(0))²)^(1/3)``.
      4. Data-dependent bandwidth ``L* = γ̂ * T^(1/3)``.
      5. Round to nearest integer; floor at 0; cap at ``T-1``.

    Parameters
    ----------
    x
        1-D array of scalar observations.
    c
        Override for the ``c`` constant in step 1. Default ``None``
        resolves to the NW 1994 recommended ``c=4``. Provided for
        sensitivity-analysis, not tuning.
    """
    u = _as_clean_1d(x)
    t_len = u.size
    if t_len < 4:
        raise ValueError(
            f"nw1994_bartlett_bandwidth requires at least 4 "
            f"observations; got {t_len}."
        )
    c_use = 4.0 if c is None else float(c)
    if c_use <= 0:
        raise ValueError(f"c must be > 0, got {c_use}.")

    m = int(max(1, math.floor(c_use * (t_len / 100.0) ** (2.0 / 9.0))))
    u_c = u - u.mean()

    # Autocovariances (biased estimator, divisor T, matching NW 1994).
    gammas = np.empty(m + 1, dtype=float)
    gammas[0] = float(np.dot(u_c, u_c)) / t_len
    for j in range(1, m + 1):
        gammas[j] = float(np.dot(u_c[j:], u_c[:-j])) / t_len

    s0 = gammas[0] + 2.0 * gammas[1 : m + 1].sum()
    s1 = 2.0 * sum(j * gammas[j] for j in range(1, m + 1))

    # Guard against s0 ≈ 0 (degenerate series).
    if abs(s0) < _EPS:
        bw = 0
        gamma_hat = 0.0
    else:
        ratio2 = (s1 / s0) ** 2
        gamma_hat = _NW1994_BARTLETT_CONST * ratio2 ** (1.0 / 3.0)
        bw_float = gamma_hat * t_len ** (1.0 / 3.0)
        bw = int(max(0, min(round(bw_float), t_len - 1)))

    return BandwidthSelection(
        method="nw1994_automatic",
        bandwidth=bw,
        kernel=_BARTLETT_KERNEL,
        m_initial=m,
        notes=(
            f"NW 1994 automatic; c={c_use}; m={m}; "
            f"gamma_hat={gamma_hat:.6g}."
        ),
    )


def fixed_bandwidth(bandwidth: int) -> BandwidthSelection:
    """Pass-through for caller-chosen fixed bandwidths (sensitivity)."""
    if bandwidth < 0:
        raise ValueError(f"fixed bandwidth must be >= 0, got {bandwidth}.")
    return BandwidthSelection(
        method="fixed",
        bandwidth=int(bandwidth),
        kernel=_BARTLETT_KERNEL,
        notes="caller-specified fixed bandwidth",
    )


# ---------------------------------------------------------------------------
# HAC long-run variance
# ---------------------------------------------------------------------------


def nw_hac_variance(
    x: npt.ArrayLike,
    *,
    bandwidth: int | BandwidthSelection,
    demean: bool = True,
) -> tuple[float, BandwidthSelection]:
    """Long-run variance via Newey-West 1987 with Bartlett kernel.

    Formula:

        σ²_LR = γ_0 + 2 Σ_{j=1}^{L} (1 - j/(L+1)) γ_j

    where γ_j = sample autocovariance at lag j (biased estimator,
    divisor T, matching the NW 1987 definition).

    Parameters
    ----------
    x
        1-D array of observations.
    bandwidth
        Either an integer truncation lag or a
        :class:`BandwidthSelection` record.
    demean
        If True (default), subtract the sample mean before computing
        autocovariances. Setting False is only appropriate when the
        series is already a residual / mean-zero by construction.

    Returns
    -------
    variance
        Scalar long-run variance estimate. Clipped at 0 from below
        (the Bartlett kernel guarantees positive semi-definiteness
        in exact arithmetic; float64 may produce tiny negatives).
    bw_record
        The :class:`BandwidthSelection` actually used.
    """
    u = _as_clean_1d(x)
    t_len = u.size
    if t_len < 2:
        raise ValueError(
            f"nw_hac_variance requires at least 2 observations; got {t_len}."
        )

    if isinstance(bandwidth, BandwidthSelection):
        bw_record = bandwidth
        bw = bw_record.bandwidth
    else:
        bw = int(bandwidth)
        if bw < 0:
            raise ValueError(f"bandwidth must be >= 0, got {bw}.")
        bw = min(bw, t_len - 1)
        bw_record = BandwidthSelection(
            method="fixed",
            bandwidth=bw,
            kernel=_BARTLETT_KERNEL,
            notes="caller-specified integer bandwidth",
        )

    u_c = u - u.mean() if demean else u
    # γ_0
    gamma_0 = float(np.dot(u_c, u_c)) / t_len
    total = gamma_0
    # Σ weighted lag terms
    for j in range(1, bw + 1):
        gamma_j = float(np.dot(u_c[j:], u_c[:-j])) / t_len
        weight = 1.0 - j / (bw + 1.0)
        total += 2.0 * weight * gamma_j
    return max(total, 0.0), bw_record


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _as_clean_1d(x: npt.ArrayLike) -> np.ndarray:
    """Coerce to 1-D float64; reject NaN/inf."""
    arr = np.asarray(x, dtype=np.float64).reshape(-1)
    if not np.all(np.isfinite(arr)):
        raise ValueError(
            "Input contains NaN or inf; HAC routines do not impute. "
            "Drop or interpolate upstream."
        )
    return arr
