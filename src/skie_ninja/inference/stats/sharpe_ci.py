"""Sharpe-ratio point estimate and confidence intervals.

Four CI flavors, ordered by role in the project's evidence-bar gate
(implementation-plan §5):

  - **Opdyke 2007 (Mertens-HAC approximation)** — primary. Uses the
    Mertens 2002 / Opdyke 2007 higher-moment iid variance formula
    scaled by the Newey-West long-run-variance ratio. This is a
    practitioner approximation of Opdyke 2007's full
    moment-vector-GMM HAC derivation, NOT a verbatim reproduction of
    §3 of that paper. Full-GMM reference implementation is tracked
    as Phase-1 follow-up ``P1-OPDYKE-FULL-GMM``.
  - **Lo 2002 Proposition 2 η(q)** — secondary/reference. Lo 2002
    Proposition 2 canonical form: Var(Ŝ) = η(q) · (1 + Ŝ²/2) / T,
    where η(q) = 1 + 2 Σ_{k=1}^{q-1} (1 - k/q) ρ_k and ρ_k is the
    sample return autocorrelation at lag k, q is the chosen lag
    truncation. This is the literal paper form.
  - **Lo 2002 iid** — diagnostic. Assumes i.i.d. returns; used as a
    model-misspecification flag when it disagrees with Opdyke by
    more than the bootstrap MC standard error.
  - **"Lo 2002 HAC-adjusted" (practitioner variance-ratio form)** —
    legacy label kept for backward compatibility with gate wiring
    planned under implementation-plan §5. The formula
    ``(1 + Ŝ²/2) · (σ²_LR / σ²) / T`` is a practitioner
    simplification of Lo's Proposition 2: under Gaussian iid with
    zero higher-moment cross-autocorrelation, it equals η(q) exactly;
    for real financial returns the two differ at O(higher-moment
    autocovariance). Prefer :func:`lo2002_prop2_eta_ci` when the
    goal is paper-faithful reproduction. Naming reflects the
    Cycle-2 audit findings L-4 / F-1-1.

All CI constructors return a :class:`SharpeCI` dataclass carrying
the point estimate, lower/upper bounds, the variance formula used,
the bandwidth / kernel metadata (for HAC variants), and — where
relevant — the skewness / excess-kurtosis sample moments. Output
feeds ``GateReport.sharpe_ci_*`` fields of
[src/skie_ninja/inference/gate.py](../gate.py) (Cycle-4 deliverable).

References
----------

  - Jobson, J. D. & Korkie, B. M. 1981. "Performance Hypothesis
    Testing with the Sharpe and Treynor Measures". *Journal of
    Finance* 36(4): 889-908. https://doi.org/10.1111/j.1540-6261.1981.tb04891.x
    — original iid Sharpe asymptotic that Lo 2002 extends.
  - Lo, A. W. 2002. "The Statistics of Sharpe Ratios". *Financial
    Analysts Journal* 58(4): 36-52.
    https://doi.org/10.2469/faj.v58.n4.2453
    — Proposition 2 (eq. 20-24): HAC Sharpe under serially correlated
    returns via GMM influence functions; Proposition 3: time
    aggregation / annualization, distinct from HAC correction.
  - Mertens, E. 2002. "Variance of the IID estimator in Lo (2002)".
    Working paper. SSRN abstract_id=1019823.
    https://ssrn.com/abstract=1019823
    — higher-moment correction: adds skewness + excess-kurtosis
    terms to the iid asymptotic variance.
  - Christie, S. 2005. "Is the Sharpe Ratio Useful in Asset
    Allocation?" MAFC Research Paper. — reproduces and extends the
    Mertens non-iid form.
  - Opdyke, J. D. 2007. "Comparing Sharpe ratios: So where are the
    p-values?" *Journal of Asset Management* 8(5): 308-336.
    https://doi.org/10.1057/palgrave.jam.2250084
    — §3 derives the asymptotic distribution under stationary-and-
    ergodic returns using the full moment-vector GMM influence-
    function HAC, NOT a scalar-ratio multiplier on the Mertens
    iid form.
  - Ledoit, O. & Wolf, M. 2008. "Robust performance hypothesis
    testing with the Sharpe ratio". *Journal of Empirical Finance*
    15(5): 850-859. https://doi.org/10.1016/j.jempfin.2008.03.002
    — pairwise-comparison variant; used in Cycle 5 for SPA
    differentials, not here.

Known deviations from cited sources (audit L-4, L-6, F-1-1, F-1-3)
-----------------------------------------------------------------

``opdyke2007_ci(..., hac_adjust=True)`` uses a scalar multiplication
of the iid Mertens-Opdyke variance by ``σ²_LR / σ²``. Opdyke 2007
§3 actually derives the HAC long-run covariance of the full moment
vector (μ, σ², μ_3, μ_4) and passes it through the delta-method
Jacobian, producing a different expression that retains cross-moment
autocovariance terms. For intraday equity-index returns with modest
skew-kurt autocorrelation the approximation is first-order
equivalent but is NOT verbatim Opdyke 2007. Tracked as Phase-1
follow-up ``P1-OPDYKE-FULL-GMM``.

``lo2002_hac_adjusted_ci`` uses the same scalar inflation factor.
This form is NOT Lo 2002 Proposition 2 (which is a weighted-
autocorrelation ``η(q)`` formula); use :func:`lo2002_prop2_eta_ci`
for paper-faithful reproduction.

Scope
-----

This module returns CIs for a **single** Sharpe ratio. The pairwise
Ledoit-Wolf comparison CI (for Hansen SPA differentials) will be
implemented in Cycle 5 alongside the SPA routines — its bootstrap
machinery is shared.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy import stats

from skie_ninja.inference.stats.hac import (
    BandwidthSelection,
    nw1994_bartlett_bandwidth,
    nw_hac_variance,
)

_METHOD_LABELS = Literal[
    "lo2002_iid",
    "lo2002_hac_approx",            # scalar variance-ratio approx (legacy "lo2002_hac_adjusted")
    "lo2002_prop2_eta",              # Lo 2002 Proposition 2 literal η(q)
    "opdyke2007_iid",                # Mertens-Opdyke higher-moment iid
    "opdyke2007_mertens_hac_approx", # scalar variance-ratio approx of Opdyke (F-1-3, L-6)
    "opdyke2007_negative_variance_clipped",
]


@dataclass(frozen=True)
class SharpeCI:
    """Single-Sharpe CI payload for GateReport (implementation-plan §5).

    ``sharpe`` is the point estimate. ``lower``/``upper`` are the
    two-sided CI endpoints at nominal level ``confidence_level``
    (default 0.95). ``variance`` is the asymptotic variance of Ŝ
    (not of Ŝ × √T — we store the per-observation variance so
    callers can rederive per-T scales). ``method`` names the
    formula. For HAC variants, ``bandwidth_selection`` records how
    the kernel truncation lag was chosen.
    """

    sharpe: float
    lower: float
    upper: float
    variance: float
    confidence_level: float
    method: str
    n_obs: int
    skewness: float | None = None
    excess_kurtosis: float | None = None
    bandwidth_selection: BandwidthSelection | None = None

    def to_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "sharpe": self.sharpe,
            "lower": self.lower,
            "upper": self.upper,
            "variance": self.variance,
            "confidence_level": self.confidence_level,
            "method": self.method,
            "n_obs": self.n_obs,
            "skewness": self.skewness,
            "excess_kurtosis": self.excess_kurtosis,
        }
        if self.bandwidth_selection is not None:
            out["bandwidth_selection"] = self.bandwidth_selection.to_dict()
        return out


# ---------------------------------------------------------------------------
# Point estimate
# ---------------------------------------------------------------------------


def sample_sharpe(returns: npt.ArrayLike, ddof: int = 1) -> tuple[float, int]:
    """Sample Sharpe ratio = mean / sd, with caller-controlled DoF.

    Uses ``ddof=1`` by default (the unbiased sample variance). The
    Lo 2002 variance formulas were derived under ``ddof=0`` (the
    population MLE). We use ``ddof=1`` for the point estimate
    (matching standard finance convention / pandas default) and
    apply a ``(T-1)/T`` correction to variance formulas where
    needed. See Lo 2002 footnote 7 for the equivalence.

    Returns ``(sharpe, n_obs)``. Raises if the sample standard
    deviation is not strictly positive.
    """
    r = _as_clean_1d(returns)
    n = r.size
    if n < 3:
        raise ValueError(f"sample_sharpe requires n >= 3, got {n}.")
    mu = float(r.mean())
    sd = float(r.std(ddof=ddof))
    if sd <= 0:
        raise ValueError(
            "Sample standard deviation is zero (degenerate series); "
            "Sharpe ratio is undefined."
        )
    return mu / sd, n


# ---------------------------------------------------------------------------
# Lo 2002 — iid diagnostic CI
# ---------------------------------------------------------------------------


def lo2002_iid_ci(
    returns: npt.ArrayLike,
    *,
    confidence_level: float = 0.95,
) -> SharpeCI:
    """Lo 2002 asymptotic iid Sharpe-ratio CI (diagnostic).

    Under the iid assumption with finite 4th moment, Lo 2002 eq. 4
    gives:

        Var(Ŝ) ≈ (1 + Ŝ²/2) / T

    The resulting two-sided (1-α) CI is ``Ŝ ± z_{α/2} sqrt(Var(Ŝ))``
    where ``z`` is the standard normal quantile.

    **Use only as diagnostic** — financial returns are typically
    serially correlated (bid-ask bounce, microstructure autocorr)
    and leptokurtic, violating the iid/Gaussian assumption. Use
    :func:`opdyke2007_ci` as the primary for gate decisions
    (implementation-plan §5).
    """
    sharpe, n = sample_sharpe(returns)
    var_sharpe = (1.0 + sharpe * sharpe / 2.0) / n
    z = float(stats.norm.ppf(0.5 + confidence_level / 2.0))
    se = np.sqrt(var_sharpe)
    return SharpeCI(
        sharpe=sharpe,
        lower=sharpe - z * se,
        upper=sharpe + z * se,
        variance=var_sharpe,
        confidence_level=confidence_level,
        method="lo2002_iid",
        n_obs=n,
    )


# ---------------------------------------------------------------------------
# Lo 2002 — HAC-adjusted
# ---------------------------------------------------------------------------


def lo2002_hac_adjusted_ci(
    returns: npt.ArrayLike,
    *,
    confidence_level: float = 0.95,
    bandwidth: int | BandwidthSelection | None = None,
) -> SharpeCI:
    """Sharpe CI via practitioner variance-ratio HAC approximation.

    Formula:

        Var_HAC(Ŝ) ≈ (1 + Ŝ²/2) · (σ²_LR / σ²) / T

    where σ²_LR is the Newey-West HAC long-run variance of returns
    (bandwidth defaults to NW 1994 automatic selection).

    **Naming note (audit L-4 / F-1-1):** this is NOT Lo 2002
    Proposition 2 nor Proposition 3. Lo's Proposition 2 gives
    Var(Ŝ) = η(q) · (1 + Ŝ²/2) / T with an autocorrelation-weighted
    η(q) (see :func:`lo2002_prop2_eta_ci` for the literal paper
    form). Lo's Proposition 3 is the time-aggregation /
    annualization result, not an HAC correction. The scalar ratio
    used here is a GMM delta-method approximation that is
    first-order equivalent to η(q) under Gaussian iid with zero
    higher-moment cross-autocorrelation. The function name is
    retained for backward compatibility with implementation-plan §5
    gate wiring; the SharpeCI.method field uses the accurate label
    ``lo2002_hac_approx``.
    """
    r = _as_clean_1d(returns)
    sharpe, n = sample_sharpe(r)
    sample_var = float(r.var(ddof=1))
    if bandwidth is None:
        bw_record = nw1994_bartlett_bandwidth(r)
    elif isinstance(bandwidth, BandwidthSelection):
        bw_record = bandwidth
    else:
        bw_record = BandwidthSelection(
            method="fixed",
            bandwidth=int(bandwidth),
            kernel="bartlett",
            notes="caller-specified fixed bandwidth",
        )
    lr_var, bw_record = nw_hac_variance(r, bandwidth=bw_record)
    # (T-1)/T correction so sample_var (ddof=1) and the HAC numerator
    # (ddof=0 biased estimator) are on the same denominator basis.
    sample_var_biased = sample_var * (n - 1) / n
    if sample_var_biased <= 0:
        raise ValueError("Sample variance is zero; Sharpe CI is undefined.")
    hac_ratio = lr_var / sample_var_biased
    var_sharpe = (1.0 + sharpe * sharpe / 2.0) * hac_ratio / n
    z = float(stats.norm.ppf(0.5 + confidence_level / 2.0))
    se = float(np.sqrt(max(var_sharpe, 0.0)))
    return SharpeCI(
        sharpe=sharpe,
        lower=sharpe - z * se,
        upper=sharpe + z * se,
        variance=var_sharpe,
        confidence_level=confidence_level,
        method="lo2002_hac_approx",
        n_obs=n,
        bandwidth_selection=bw_record,
    )


def lo2002_prop2_eta_ci(
    returns: npt.ArrayLike,
    *,
    confidence_level: float = 0.95,
    q: int | None = None,
) -> SharpeCI:
    """Lo 2002 Proposition 2 — literal η(q) autocorrelation form.

    Var(Ŝ) = η(q) · (1 + Ŝ²/2) / T, where

        η(q) = 1 + 2 Σ_{k=1}^{q-1} (1 - k/q) ρ_k

    and ρ_k is the sample autocorrelation at lag k. This matches Lo
    2002 eq. 20-24 verbatim. Truncation ``q`` defaults to the NW
    1994 automatic-selection bandwidth + 1 (so ``q-1`` = bandwidth).
    The function is provided for paper-faithful reproduction;
    :func:`lo2002_hac_adjusted_ci` is the practitioner approximation
    used in the gate wiring.
    """
    r = _as_clean_1d(returns)
    sharpe, n = sample_sharpe(r)
    if q is None:
        bw = nw1994_bartlett_bandwidth(r)
        q_use = max(2, bw.bandwidth + 1)
        bw_record: BandwidthSelection | None = bw
    else:
        q_use = int(q)
        if q_use < 2:
            raise ValueError(f"q must be >= 2, got {q_use}.")
        bw_record = BandwidthSelection(
            method="fixed", bandwidth=q_use - 1, kernel="bartlett",
            notes="lo2002 prop2 q - 1 = bandwidth",
        )
    # Sample autocorrelations (divisor T, matching Lo 2002 convention).
    r_c = r - r.mean()
    var0 = float(np.dot(r_c, r_c)) / n
    eta = 1.0
    for k in range(1, q_use):
        gamma_k = float(np.dot(r_c[k:], r_c[:-k])) / n
        rho_k = gamma_k / var0 if var0 > 0 else 0.0
        weight = 1.0 - k / q_use
        eta += 2.0 * weight * rho_k
    eta = max(eta, 0.0)  # Bartlett weights guarantee >= 0 exactly; float64 guard.
    var_sharpe = eta * (1.0 + sharpe * sharpe / 2.0) / n
    z = float(stats.norm.ppf(0.5 + confidence_level / 2.0))
    se = float(np.sqrt(var_sharpe))
    return SharpeCI(
        sharpe=sharpe,
        lower=sharpe - z * se,
        upper=sharpe + z * se,
        variance=var_sharpe,
        confidence_level=confidence_level,
        method="lo2002_prop2_eta",
        n_obs=n,
        bandwidth_selection=bw_record,
    )


# ---------------------------------------------------------------------------
# Opdyke 2007 — primary (higher-moment Mertens-Opdyke)
# ---------------------------------------------------------------------------


def opdyke2007_ci(
    returns: npt.ArrayLike,
    *,
    confidence_level: float = 0.95,
    hac_adjust: bool = True,
    bandwidth: int | BandwidthSelection | None = None,
) -> SharpeCI:
    """Mertens-Opdyke higher-moment Sharpe CI — gate PRIMARY channel.

    Uses the Mertens 2002 / Opdyke 2007 iid asymptotic-variance
    formula that admits finite skewness γ_3 and excess kurtosis γ_4:

        Var(Ŝ) ≈ ( 1 + Ŝ²(γ_4 + 2)/4 - Ŝ γ_3 ) / T      (iid form)

    Algebra: Mertens 2002 originally writes the formula in terms of
    the fourth *standardized moment* ``μ_4 = E[(r-μ)^4]/σ^4 = γ_4 + 3``,
    giving ``Var(Ŝ) = (1 + Ŝ²(μ_4 - 1)/4 - Ŝ γ_3)/T``. Substituting
    ``μ_4 = γ_4 + 3`` gives ``(μ_4 - 1) = γ_4 + 2``, matching the
    form used here.

    **HAC extension (audit L-6 / F-1-3):** if ``hac_adjust=True``
    (default), the iid variance is scaled by the long-run-variance
    ratio ``σ²_LR / σ²``. This is a **practitioner approximation**
    of Opdyke 2007 §3 — Opdyke derives the HAC long-run covariance
    of the full moment vector (μ, σ², μ_3, μ_4) and passes it
    through a delta-method Jacobian, producing a different
    expression that retains cross-moment autocovariance terms. The
    scalar-ratio approximation is first-order equivalent under
    weak higher-moment serial dependence but is not verbatim Opdyke.
    The SharpeCI.method label ``opdyke2007_mertens_hac_approx``
    reflects this. Full Opdyke GMM is tracked as Phase-1 follow-up
    ``P1-OPDYKE-FULL-GMM``.

    Rationale for primary status (implementation-plan §5): financial
    return series (intraday equity-index in particular) are
    leptokurtic and mildly serially correlated, violating the
    iid-Gaussian Lo 2002 assumptions. The Mertens-Opdyke form
    captures the dominant higher-moment bias; the scalar HAC ratio
    captures the dominant serial-correlation bias. Empirical ρ_1
    and kurtosis values for our ES/NQ sample will be measured in
    Cycle 6 and written into the ReproLog — they are not
    pre-specified here.
    """
    r = _as_clean_1d(returns)
    # For internal consistency of the asymptotic derivation, use
    # ddof=0 (biased) estimators throughout — including for Ŝ itself.
    # F-1-4 remediation: the published Mertens-Opdyke formula assumes
    # ddof=0; mixing ddof=1 Ŝ with ddof=0 moments introduces an
    # O(1/n) inconsistency. Our public ``sample_sharpe`` helper uses
    # ddof=1 for a finance-convention point estimate, but for the
    # Opdyke variance machinery we recompute with ddof=0.
    n = r.size
    if n < 3:
        raise ValueError(f"opdyke2007_ci requires n >= 3, got {n}.")
    mu = float(r.mean())
    sd0 = float(r.std(ddof=0))
    if sd0 <= 0:
        raise ValueError("Sample standard deviation is zero; CI undefined.")
    sharpe = mu / sd0
    centred = r - mu
    skew = float(np.mean(centred**3) / sd0**3)            # γ_3
    kurt_excess = float(np.mean(centred**4) / sd0**4 - 3.0)  # γ_4

    var_iid = (
        1.0 + sharpe * sharpe * (kurt_excess + 2.0) / 4.0 - sharpe * skew
    ) / n

    bw_record: BandwidthSelection | None = None
    if var_iid <= 0:
        # F-1-2 remediation: LOUD warning on the negative-variance
        # fallback so downstream gate code can flag it. Previously
        # this was silent; now we emit RuntimeWarning with the raw
        # (negative) variance value.
        raw_var = var_iid
        warnings.warn(
            f"opdyke2007_ci: Mertens-Opdyke iid variance is non-positive "
            f"(raw_variance={raw_var:.6g}) — skew/kurtosis term "
            f"dominates. Falling back to Lo 2002 iid variance. Consider "
            f"a larger sample or report this case as a diagnostic.",
            RuntimeWarning,
            stacklevel=2,
        )
        method = "opdyke2007_negative_variance_clipped"
        var_sharpe = (1.0 + sharpe * sharpe / 2.0) / n
    elif hac_adjust:
        if bandwidth is None:
            bw_record = nw1994_bartlett_bandwidth(r)
        elif isinstance(bandwidth, BandwidthSelection):
            bw_record = bandwidth
        else:
            bw_record = BandwidthSelection(
                method="fixed",
                bandwidth=int(bandwidth),
                kernel="bartlett",
                notes="caller-specified fixed bandwidth",
            )
        lr_var, bw_record = nw_hac_variance(r, bandwidth=bw_record)
        sample_var_biased = sd0 * sd0
        hac_ratio = lr_var / sample_var_biased if sample_var_biased > 0 else 1.0
        var_sharpe = var_iid * hac_ratio
        method = "opdyke2007_mertens_hac_approx"
    else:
        var_sharpe = var_iid
        method = "opdyke2007_iid"

    z = float(stats.norm.ppf(0.5 + confidence_level / 2.0))
    se = float(np.sqrt(max(var_sharpe, 0.0)))
    return SharpeCI(
        sharpe=sharpe,
        lower=sharpe - z * se,
        upper=sharpe + z * se,
        variance=var_sharpe,
        confidence_level=confidence_level,
        method=method,
        n_obs=n,
        skewness=skew,
        excess_kurtosis=kurt_excess,
        bandwidth_selection=bw_record,
    )


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _as_clean_1d(x: npt.ArrayLike) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64).reshape(-1)
    if not np.all(np.isfinite(arr)):
        raise ValueError(
            "Input contains NaN or inf; Sharpe routines do not impute."
        )
    return arr
