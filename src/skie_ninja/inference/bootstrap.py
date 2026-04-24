"""Stationary bootstrap (Politis-Romano 1994) with Politis-White 2004 block selection.

This module implements the stationary bootstrap of Politis & Romano
1994 — a block bootstrap whose block lengths are i.i.d. geometric
(so that the resampled series is itself stationary, unlike fixed-
length moving-block bootstrap). It is the canonical dependent-data
bootstrap for Hansen 2005 Superior Predictive Ability (SPA) and
related tests (implemented in
:mod:`skie_ninja.inference.multipletest.hansen_spa`) where the
sampled object is a vector-valued time series of model-vs-benchmark
performance differentials.

Automatic block-length selection follows Politis & White 2004 with
the Patton, Politis & White 2009 correction.  PPW 2009 revised the
``D`` constants entering BOTH the stationary and circular bootstrap
optimal-block formulas (not the circular formula alone, as some
summaries state); the post-correction constants used here,
``D_SB = 2 * g(0)^2`` and ``D_CB = (4/3) * g(0)^2``, match the
corrected values used in reference implementations (``arch``
Python package, ``blocklength`` R package).

Design choices (each data-driven, no magic numbers)
---------------------------------------------------

- **Kernel for G/D**: flat-top (Politis & Romano 1995 *JTSA*
  16(1):67-103), the kernel recommended by PW 2004 §3.2 because its
  bias decays super-polynomially for smooth spectra. No tunable
  shape parameter.
- **Pilot bandwidth ``m_hat``**: smallest ``m`` such that
  ``|rho_hat(m+k)| < 2 sqrt(log10(n)/n)`` for all
  ``k = 1, ..., K_N`` where ``K_N = max(5, ceil(sqrt(log10(n))))``.
  This is the Politis & White 2004 §3.1 threshold rule (building on
  Politis 2003 adaptive-bandwidth choice). The factor ``2`` is the
  standard 95% Gaussian critical value for the iid-noise sample
  ACF sampling distribution ``N(0, 1/n)`` (Brockwell & Davis 1991
  §7.2-§7.3), but the ``log10(n)/n`` inflation and the ``K_N``
  lookahead window are PW 2004's construction — neither is a
  tuned hyperparameter.
- **``M = 2 * m_hat``** per PW 2004 §3.2 recommendation.
- **Truncation-lag search ceiling**: ``min(n - 1, ceil(sqrt(n)) +
  max(K_N, 1))`` to bound search cost without constraining the
  answer on realistic inputs.

References
----------

- Politis, D. N. & Romano, J. P. 1994. "The Stationary Bootstrap".
  *Journal of the American Statistical Association* 89(428):
  1303-1313. https://doi.org/10.2307/2290993
- Politis, D. N. & Romano, J. P. 1995. "Bias-Corrected Nonparametric
  Spectral Estimation". *Journal of Time Series Analysis* 16(1):
  67-103. https://doi.org/10.1111/j.1467-9892.1995.tb00223.x
  — origin of the flat-top lag window used by PW 2004.
- Politis, D. N. 2003. "Adaptive Bandwidth Choice". *Journal of
  Nonparametric Statistics* 15(4-5): 517-533.
  https://doi.org/10.1080/10485250310001605677 — the threshold rule
  that PW 2004 §3.1 inherits.
- Politis, D. N. & White, H. 2004. "Automatic Block-Length Selection
  for the Dependent Bootstrap". *Econometric Reviews* 23(1): 53-70.
  https://doi.org/10.1081/ETC-120028836
- Patton, A.; Politis, D. N. & White, H. 2009. "Correction to
  'Automatic Block-Length Selection for the Dependent Bootstrap'".
  *Econometric Reviews* 28(4): 372-375.
  https://doi.org/10.1080/07474930802459016
- Brockwell, P. J. & Davis, R. A. 1991. *Time Series: Theory and
  Methods*, 2nd ed., Springer. §7.2-§7.3 — asymptotic-normal
  sampling distribution of sample autocorrelations under iid
  white noise; motivates the 2-SE band but NOT the log10(n)/n
  inflation.

Verification status of primary-source equation numbers
------------------------------------------------------

PW 2004 eq. 9 and PPW 2009's corrected constants were checked
against the ``arch`` Python package's ``optimal_block_length``
implementation (github.com/bashtage/arch) which is authored by
Kevin Sheppard and post-dates PPW 2009. Direct access to the
Politis-White and Patton-Politis-White PDFs was blocked by
tandfonline paywall at audit time; section-label claims (§3.1,
§3.2) are believed correct based on secondary summaries but have
not been verified against the primary PDF in this revision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

# A small numerical floor on sample variance to guard against
# degenerate series. Float64 ULP is the natural lower bound.
_EPS = float(np.finfo(np.float64).eps)

# Gaussian critical-value constant (Brockwell-Davis 1991 §7.2).
_RHO_THRESHOLD_C = 2.0

_BOOTSTRAP_TYPES = Literal["stationary", "circular"]


@dataclass(frozen=True)
class BlockLengthSelection:
    """Record of how the block length was chosen — written into ReproLog.

    ``block_length`` is the expected block length for stationary
    bootstrap (= 1 / geometric probability) or the fixed block
    length for circular bootstrap.  ``method`` names the selection
    rule.  ``m_hat`` and ``M`` are PW 2004 pilot quantities; when
    ``method == 'fixed'`` they are ``None``.
    """

    method: Literal["politis_white_2004", "fixed"]
    block_length: float
    bootstrap_type: str
    m_hat: int | None = None
    M: int | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "block_length": self.block_length,
            "bootstrap_type": self.bootstrap_type,
            "m_hat": self.m_hat,
            "M": self.M,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Flat-top kernel (Politis-Romano 1995; PW 2004 §3.2)
# ---------------------------------------------------------------------------


def _flat_top_kernel(x: float) -> float:
    """Flat-top (trapezoidal) lag window.

    ``lambda(x) = 1`` for ``|x| <= 1/2``;
    ``lambda(x) = 2 (1 - |x|)`` for ``1/2 < |x| <= 1``;
    ``lambda(x) = 0`` otherwise.

    Reference: Politis & Romano 1995 *Journal of Time Series
    Analysis* 16(1): 67-103
    (https://doi.org/10.1111/j.1467-9892.1995.tb00223.x); used by
    PW 2004 §3.2.
    """
    ax = abs(x)
    if ax <= 0.5:
        return 1.0
    if ax <= 1.0:
        return 2.0 * (1.0 - ax)
    return 0.0


# ---------------------------------------------------------------------------
# Politis-White 2004 automatic block-length selection
# ---------------------------------------------------------------------------


def _as_clean_1d(x: npt.ArrayLike) -> np.ndarray:
    arr = np.asarray(x, dtype=float).ravel()
    if not np.all(np.isfinite(arr)):
        raise ValueError("input contains non-finite values (NaN or inf).")
    return arr


def politis_white_block_length(
    x: npt.ArrayLike,
    *,
    bootstrap_type: _BOOTSTRAP_TYPES = "stationary",
) -> BlockLengthSelection:
    """Automatic block-length selection per Politis & White 2004.

    Parameters
    ----------
    x
        1-D array of scalar observations (e.g., a loss-differential
        series).  NaN/inf rejected.
    bootstrap_type
        ``"stationary"`` (PW 2004 eq. 9, unchanged by PPW 2009) or
        ``"circular"`` (PPW 2009 corrected formula).

    Returns
    -------
    BlockLengthSelection
        ``block_length`` is the expected block length (SB) or fixed
        block length (CB), floored at 1 and capped at the series
        length.

    Notes
    -----
    For multivariate inputs, PW 2004 recommend choosing the block
    length as the max of the per-column selections; this function
    accepts only scalar input.  Multivariate handling is the
    caller's responsibility (see :func:`choose_block_length`).
    """
    u = _as_clean_1d(x)
    n = u.size
    if n < 4:
        raise ValueError(
            f"politis_white_block_length requires n >= 4, got {n}."
        )

    u_c = u - u.mean()
    gamma_0 = float(np.dot(u_c, u_c) / n)
    if gamma_0 <= _EPS:
        # Degenerate: constant series. Return block_length = 1 (iid bootstrap).
        return BlockLengthSelection(
            method="politis_white_2004",
            block_length=1.0,
            bootstrap_type=bootstrap_type,
            m_hat=0,
            M=0,
            notes="degenerate (zero-variance) series; fell back to block_length=1.",
        )

    # Search ceiling for autocorrelations.  Ensure enough lags for
    # the lookahead window K_N (the threshold rule checks K_N future
    # lags after the candidate m).
    log10n = math.log10(max(n, 10))
    K_N = max(5, int(math.ceil(math.sqrt(log10n))))
    k_max = int(min(n - 1, math.ceil(math.sqrt(n)) + max(K_N, 1) * 2))
    # Always compute at least K_N + a buffer — otherwise the threshold
    # rule can't see far enough to declare m_hat = 0.
    k_max = max(k_max, K_N + 1)
    k_max = min(k_max, n - 1)

    gammas = np.empty(k_max + 1, dtype=float)
    gammas[0] = gamma_0
    for k in range(1, k_max + 1):
        gammas[k] = float(np.dot(u_c[k:], u_c[:-k])) / n
    rhos = gammas / gamma_0

    # Pilot bandwidth m_hat: smallest m >= 0 such that
    # |rho(m + k)| < 2 sqrt(log10(n)/n) for k = 1..K_N.
    threshold = _RHO_THRESHOLD_C * math.sqrt(log10n / n)
    m_hat = 0
    found = False
    for m in range(0, k_max - K_N):
        window = np.abs(rhos[m + 1 : m + 1 + K_N])
        if window.size < K_N:
            break
        if np.all(window < threshold):
            m_hat = m
            found = True
            break
    if not found:
        # No clean cutoff in the searched range — fall back to the
        # largest lag where rho crossed the threshold; cap at k_max.
        sig = np.where(np.abs(rhos[1:]) >= threshold)[0]
        m_hat = int(sig.max() + 1) if sig.size > 0 else 0

    M = max(2 * m_hat, 2)  # PW 2004 §3.2: M = 2 * m_hat; floor at 2 so kernel has support.
    M = min(M, k_max)

    # Flat-top weighted sums.  Symmetry: gamma(-k) = gamma(k), so we
    # compute for k = 0..M and double for k >= 1.
    lag_indices = np.arange(0, M + 1)
    weights = np.array([_flat_top_kernel(k / M) for k in lag_indices])
    # g_hat(0) = sum_{k=-M+1}^{M-1} lambda(k/M) * gamma_hat(k)
    #         = gamma_hat(0) + 2 sum_{k=1}^{M-1} lambda(k/M) * gamma_hat(k)
    # Our arrays run 0..M; the endpoint k=M has lambda = 0 so inclusion is harmless.
    g_hat_0 = float(gammas[0] + 2.0 * np.sum(weights[1:] * gammas[1 : M + 1]))

    # G_hat = sum_{k=-M}^{M} lambda(|k|/M) * |k| * gamma(k)
    #       = 2 sum_{k=1}^{M} lambda(k/M) * k * gamma(k)
    G_hat = 2.0 * float(np.sum(weights[1:] * lag_indices[1:] * gammas[1 : M + 1]))

    if bootstrap_type == "stationary":
        # PW 2004 eq. 9: D_SB = 2 * g(0)^2.
        D = 2.0 * g_hat_0 * g_hat_0
        coef = 2.0  # multiplicative coefficient in b_opt = (coef * G^2 / D)^(1/3) * n^(1/3).
    elif bootstrap_type == "circular":
        # PPW 2009 correction: D_CB = (4/3) * g(0)^2.
        D = (4.0 / 3.0) * g_hat_0 * g_hat_0
        coef = 2.0
    else:
        raise ValueError(f"unknown bootstrap_type: {bootstrap_type!r}")

    if D <= _EPS or G_hat <= 0:
        # Flat spectrum or near-iid series — PW 2004 note §3.2: fall
        # back to b = 1 (no block structure needed).
        return BlockLengthSelection(
            method="politis_white_2004",
            block_length=1.0,
            bootstrap_type=bootstrap_type,
            m_hat=m_hat,
            M=M,
            notes=(
                f"flat or negligible dependence (G_hat={G_hat:.3g}, "
                f"D={D:.3g}); fell back to block_length=1."
            ),
        )

    b_opt = (coef * G_hat * G_hat / D) ** (1.0 / 3.0) * n ** (1.0 / 3.0)

    # Floor at 1 (iid bootstrap degenerate limit); cap at n (can't
    # have blocks longer than the series).
    b_opt = float(max(1.0, min(b_opt, float(n))))

    return BlockLengthSelection(
        method="politis_white_2004",
        block_length=b_opt,
        bootstrap_type=bootstrap_type,
        m_hat=m_hat,
        M=M,
        notes=(
            f"K_N={K_N}; threshold={threshold:.4g}; "
            f"g_hat(0)={g_hat_0:.4g}; G_hat={G_hat:.4g}; D={D:.4g}."
        ),
    )


def choose_block_length(
    x: npt.ArrayLike,
    *,
    bootstrap_type: _BOOTSTRAP_TYPES = "stationary",
) -> BlockLengthSelection:
    """Multivariate-safe wrapper.

    For 1-D ``x`` delegates to :func:`politis_white_block_length`.
    For 2-D ``x`` (shape ``(n, k)``) returns the max block length
    across columns per the PW 2004 multivariate recommendation
    (max over per-column selections).
    """
    arr = np.asarray(x, dtype=float)
    if arr.ndim == 1:
        return politis_white_block_length(arr, bootstrap_type=bootstrap_type)
    if arr.ndim != 2:
        raise ValueError(f"x must be 1-D or 2-D; got ndim={arr.ndim}.")
    selections = [
        politis_white_block_length(arr[:, j], bootstrap_type=bootstrap_type)
        for j in range(arr.shape[1])
    ]
    best = max(selections, key=lambda s: s.block_length)
    m_hats = [s.m_hat for s in selections if s.m_hat is not None]
    Ms = [s.M for s in selections if s.M is not None]
    return BlockLengthSelection(
        method="politis_white_2004",
        block_length=best.block_length,
        bootstrap_type=bootstrap_type,
        m_hat=max(m_hats) if m_hats else None,
        M=max(Ms) if Ms else None,
        notes=(
            f"max across {arr.shape[1]} columns; per-column block lengths: "
            + ", ".join(f"{s.block_length:.2f}" for s in selections)
        ),
    )


# ---------------------------------------------------------------------------
# Stationary bootstrap index generator (Politis-Romano 1994)
# ---------------------------------------------------------------------------


def stationary_bootstrap_indices(
    n: int,
    *,
    block_length: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Single stationary-bootstrap resample of indices ``0..n-1``.

    Algorithm (Politis-Romano 1994 §2):

      1. Start at a uniformly random index ``I_1`` in ``{0, ..., n-1}``.
      2. At each step, with probability ``p = 1/block_length`` start
         a new block at a fresh uniform index; else continue with
         ``I_t = (I_{t-1} + 1) mod n`` (circular wrap).
      3. Repeat until ``n`` indices are produced.

    The resampled series is itself strictly stationary — the
    property that motivates the PR 1994 construction over the
    Künsch 1989 / Liu-Singh 1992 moving-block bootstrap.

    Parameters
    ----------
    n
        Series length (> 0).
    block_length
        Expected block length (>= 1). Geometric probability
        ``p = 1 / block_length``.
    rng
        NumPy :class:`~numpy.random.Generator` supplied by caller
        (so downstream reproducibility logs can trace the seed).

    Returns
    -------
    np.ndarray
        Integer array of shape ``(n,)`` with values in ``[0, n)``.

    Notes
    -----
    RNG consumption: this implementation pre-draws the switch and
    fresh-start vectors of length ``n - 1`` in one shot (vectorized)
    rather than lazily drawing only on switch events.  Self-
    reproducibility under a fixed seed is preserved, but the draw
    order differs from a lazy-on-switch implementation (e.g., the
    ``arch`` Python package's stationary bootstrap), so identical
    seeds will NOT produce identical indices across implementations.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}.")
    if block_length < 1.0:
        raise ValueError(
            f"block_length must be >= 1 (geometric mean), got {block_length}."
        )
    p = 1.0 / float(block_length)

    out = np.empty(n, dtype=np.int64)
    # First draw: uniform start.
    out[0] = int(rng.integers(0, n))
    if n == 1:
        return out

    # Vectorized: pre-draw switch events and fresh starts.
    switches = rng.random(n - 1) < p
    fresh = rng.integers(0, n, size=n - 1)
    for t in range(1, n):
        if switches[t - 1]:
            out[t] = int(fresh[t - 1])
        else:
            out[t] = (out[t - 1] + 1) % n
    return out


def stationary_bootstrap(
    x: npt.ArrayLike,
    *,
    n_bootstrap: int,
    block_length: float | None = None,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, BlockLengthSelection]:
    """Draw ``n_bootstrap`` stationary-bootstrap resamples of ``x``.

    Parameters
    ----------
    x
        Input array.  Shape ``(n,)`` or ``(n, k)``.  Resampling is
        along the leading (time) axis; for 2-D inputs the SAME
        index draw is used across all columns, preserving cross-
        sectional dependence — this is the construction needed by
        Hansen 2005 SPA (§2.1 "same bootstrap indices across
        strategies").
    n_bootstrap
        Number of bootstrap replications.
    block_length
        Expected block length.  If ``None``, auto-selected via
        Politis-White 2004.
    rng
        NumPy Generator.  Defaults to :func:`numpy.random.default_rng()`
        with system entropy — callers are responsible for seeding
        reproducibility-critical contexts.

    Returns
    -------
    (samples, selection)
        ``samples`` has shape ``(n_bootstrap, n)`` for 1-D input or
        ``(n_bootstrap, n, k)`` for 2-D.  ``selection`` is the
        :class:`BlockLengthSelection` used.
    """
    arr = np.asarray(x)
    if arr.ndim not in (1, 2):
        raise ValueError(f"x must be 1-D or 2-D; got ndim={arr.ndim}.")
    n = arr.shape[0]
    if n < 2:
        raise ValueError(f"stationary_bootstrap requires n >= 2, got {n}.")
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}.")
    if rng is None:
        rng = np.random.default_rng()

    if block_length is None:
        selection = choose_block_length(arr, bootstrap_type="stationary")
        bl = selection.block_length
    else:
        if block_length < 1.0:
            raise ValueError(
                f"block_length must be >= 1, got {block_length}."
            )
        selection = BlockLengthSelection(
            method="fixed",
            block_length=float(block_length),
            bootstrap_type="stationary",
            notes="caller-specified fixed block length.",
        )
        bl = float(block_length)

    if arr.ndim == 1:
        out = np.empty((n_bootstrap, n), dtype=arr.dtype)
    else:
        out = np.empty((n_bootstrap, n, arr.shape[1]), dtype=arr.dtype)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n, block_length=bl, rng=rng)
        out[b] = arr[idx]
    return out, selection


__all__ = [
    "BlockLengthSelection",
    "choose_block_length",
    "politis_white_block_length",
    "stationary_bootstrap",
    "stationary_bootstrap_indices",
]
