"""Ledoit-Wolf 2008 studentized time-series bootstrap CI for the
difference of two Sharpe ratios.

Implements the differential Sharpe-ratio confidence interval bound by
[research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md)
§4.2 + §5.3 for the H050 paired statistic
``T_H050 = SR(r_p_gated) - SR(r_p_uncond)``. The implementation closes
the evidence-bar-blocking follow-up
``P1-H050-LW2008-DIFFERENTIAL-CI-IMPL`` and is the project's canonical
pairwise-Sharpe inference primitive per the project ``rules/quant-project.md``
``§Inference`` rule (path: ``~/.claude/rules/quant-project.md``).

The construction (Ledoit & Wolf 2008 §3.1 — "Robust performance
hypothesis testing with the Sharpe ratio", *J. Empirical Finance*
15(5):850-859, doi:10.1016/j.jempfin.2008.03.002):

  1. Compute the sample Sharpe difference ``Delta_hat = SR_a - SR_b``
     where ``SR_i = mu_i / sigma_i`` with
     ``mu_i = E[r_i]``, ``sigma_i = sqrt(E[r_i^2] - mu_i^2)``.
  2. Compute the HAC standard error ``se_HAC`` of ``sqrt(T) Delta_hat``
     via the delta-method on the joint moment vector
     ``theta = (mu_a, gamma_a, mu_b, gamma_b)`` (where
     ``gamma_i = E[r_i^2]``) with the long-run covariance matrix
     ``Psi`` of the per-period vector
     ``v_t = (r_{a,t}, r_{a,t}^2, r_{b,t}, r_{b,t}^2)``. ``Psi`` is
     estimated by Newey-West 1987 with the Bartlett kernel applied to
     EACH of the 16 covariance entries of ``v_t``, with bandwidth
     selected by Newey-West 1994 on the paired-difference series
     ``r_{a,t} - r_{b,t}`` (a single bandwidth shared across all
     entries — the canonical reduction for Bartlett-kernel
     multivariate HAC under a scalar truncation lag).
  3. Studentized statistic ``T_obs = sqrt(T) Delta_hat / se_HAC``.
  4. Bootstrap distribution of the studentized statistic via the
     Politis-Romano 1994 stationary bootstrap (substituted for the
     paper's circular block bootstrap; see "Bootstrap variant
     substitution" below). For each replicate ``b`` draw paired
     indices ``I^*b`` ONCE (preserves cross-series dependence); form
     ``r_a^*b = r_a[I^*b]``, ``r_b^*b = r_b[I^*b]``; recompute
     ``Delta^*b`` and ``se_HAC^*b`` on the resampled series; centre on
     the sample value:
     ``T^*b = sqrt(T) (Delta^*b - Delta_hat) / se_HAC^*b``.
  5. Two-sided ``(1 - alpha)`` CI:
     ``[Delta_hat - q_{1-alpha/2}(T^*) * se_HAC / sqrt(T),
        Delta_hat - q_{alpha/2}(T^*) * se_HAC / sqrt(T)]``.
     This is the "studentised pivotal" interval (Hall 1992 §3.5;
     Davison & Hinkley 1997 §5.4 eq. 5.10) — the asymmetric form
     using BOTH bootstrap quantiles, which is the inversion of the
     bootstrap distribution of ``T^*`` rather than the symmetric
     ``Delta_hat ± q * se`` form. Asymmetric reporting is the
     standard in studentised-pivot CIs and gives correct coverage
     in the presence of skewness in the studentised distribution.

Bootstrap variant substitution
------------------------------

Ledoit & Wolf 2008 §3.2.2 (verified against the open-access UZH IEW
WP 320 mirror) uses the **circular block bootstrap** (Politis &
Romano 1992 *Exploring the Limits of the Bootstrap*, ed. R. LePage,
J. Wiley) for the resampling step. We substitute the **stationary
bootstrap** (Politis & Romano 1994 *J. American Statistical
Association* 89(428):1303-1313,
doi:10.1080/01621459.1994.10476870) on three grounds:

  - **Methodological equivalence**: stationary and circular block
    bootstrap have the same first-order asymptotic properties under
    weakly dependent series ([Lahiri, S. N. 2003. *Resampling
    Methods for Dependent Data.* Springer, ISBN 978-0-387-00928-5;
    doi:10.1007/978-1-4757-3803-2](https://doi.org/10.1007/978-1-4757-3803-2)
    Chapter 5 "Comparison of Block Bootstrap Methods" — both
    achieve consistency of the bootstrap variance of smooth
    functionals of the sample mean at rate ``O(n^{-1/3})`` under MA
    approximation conditions). The Edgeworth-level (second-order)
    properties at which the two methods may differ are the subject
    of Chapter 6 "Second-Order Properties" — beyond the first-order
    coverage guarantee invoked here.
  - **Project consistency**: the stationary bootstrap is the
    canonical block bootstrap of Cycle 5 ([src/skie_ninja/inference/bootstrap.py](../bootstrap.py))
    used by Hansen 2005 SPA test and reused here per addendum §4.2
    "implementation-bound choice". LW2008 itself uses the
    Politis-Romano 1994 stationary bootstrap for the residual-
    bootstrap stage of Algorithm 3.1's calibration loop (WP 320
    footnote 10), so the substitution is internally consistent
    with LW2008's own implementation choices.
  - **Stationarity preservation**: the resampled series under
    Politis-Romano 1994 is itself stationary (geometric block
    lengths), which simplifies the validity argument for the
    studentised bootstrap distribution.

The substitution is documented at the call-site for full
auditability; the bootstrap-variant choice is a project-wide design
decision (memo r4 §3.1 audit finding F-3-1) and is NOT a literature-
level primacy claim about Ledoit-Wolf 2008's text.

Parameterisation cross-walk
---------------------------

The implementation parameterises the joint moment vector in **raw
moments** ``θ = (μ_a, γ_a, μ_b, γ_b)`` with ``γ_i = E[r_i²]``
(LW2008 WP 320 Eq. 1-2 "uncentered second moments" — the choice the
authors call "more convenient"). Equivalent **centred-moment**
phrasing ``(μ_a, σ²_a, μ_b, σ²_b)`` with ``σ²_i = γ_i - μ_i²`` is
related by the smooth bijection ``(μ, γ) ↦ (μ, γ - μ²)`` whose
Jacobian is unit-determinant; the delta-method gradient transforms
covariantly and the resulting HAC variance ``∇f' Ψ ∇f`` is
invariant under the reparameterisation. The raw-moment form is used
here because LW2008 Eq. (5) and the gradient ``∇f`` at WP 320
Eq. (4) are stated in raw moments.

Block-length selection
----------------------

Block length is chosen via Politis-White 2004 automatic selection
([src/skie_ninja/inference/bootstrap.py](../bootstrap.py)
``politis_white_block_length``) applied to the **paired-difference
series** ``r_a - r_b``. The paired-difference series is the residual
process whose autocorrelation drives the variance of
``Delta_hat = SR_a - SR_b`` under cross-series dependence; block
length on this series therefore correctly captures the dependence
structure that the bootstrap must preserve. The choice matches
addendum §4.2's unified-block-length binding ("the per-side Opdyke
CIs and the Ledoit-Wolf differential CI share a single block-length
selected via ``politis_white_block_length`` on the paired-difference
series"). Patton-Politis-White 2009 corrections are already wired
through ``politis_white_block_length``.

Number of bootstrap replications
--------------------------------

Default ``n_bootstrap = 2000`` follows [Hall, P. 1992. *The
Bootstrap and Edgeworth Expansion.* Springer, ISBN 978-0-387-94508-8;
doi:10.1007/978-1-4612-4384-7](https://doi.org/10.1007/978-1-4612-4384-7)
§1.5: for two-sided inference at nominal level ``alpha``, the
bootstrap Monte-Carlo error on a quantile is minimised when
``B = K(1 - alpha) - 1`` for integer ``K``; ``K = 100, alpha = 0.05``
gives ``B = 1999``, hence the standard practitioner choices
``B in {999, 1999, 9999}``. ``B = 2000`` is the conventional rounded
form widely used in finance applications (Davison & Hinkley 1997
§5.4 also suggests ``B >= 1000`` for two-sided 5%-level inference).

References
----------

  - Ledoit, O. & Wolf, M. 2008. "Robust performance hypothesis testing
    with the Sharpe ratio". *J. Empirical Finance* 15(5):850-859.
    https://doi.org/10.1016/j.jempfin.2008.03.002 — canonical
    reference. Open-access companion: University of Zurich IEW
    Working Paper 320,
    https://www.econ.uzh.ch/apps/workingpapers/wp/iewwp320.pdf
    (text-identical to the published version).
  - Politis, D. N. & Romano, J. P. 1994. "The Stationary Bootstrap".
    *J. American Statistical Association* 89(428):1303-1313.
    https://doi.org/10.1080/01621459.1994.10476870
  - Politis, D. N. & White, H. 2004. "Automatic Block-Length Selection
    for the Dependent Bootstrap". *Econometric Reviews* 23(1):53-70.
    https://doi.org/10.1081/ETC-120028836
  - Patton, A.; Politis, D. N. & White, H. 2009. "Correction to
    'Automatic Block-Length Selection for the Dependent Bootstrap'".
    *Econometric Reviews* 28(4):372-375.
    https://doi.org/10.1080/07474930802459016
  - Lahiri, S. N. 2003. *Resampling Methods for Dependent Data.*
    Springer, ISBN 978-0-387-00928-5. Chapter 5 "Comparison of
    Block Bootstrap Methods" (first-order asymptotic equivalence
    of block bootstraps).
    https://doi.org/10.1007/978-1-4757-3803-2
  - Mertens, E. 2002. "Variance of the IID estimator in Lo (2002)".
    Working paper. SSRN abstract_id=1019823.
    https://ssrn.com/abstract=1019823
  - Newey, W. K. & West, K. D. 1987. "A Simple, Positive Semi-Definite,
    Heteroskedasticity and Autocorrelation Consistent Covariance
    Matrix". *Econometrica* 55(3):703-708.
    https://doi.org/10.2307/1913610
  - Newey, W. K. & West, K. D. 1994. "Automatic Lag Selection in
    Covariance Matrix Estimation". *Review of Economic Studies*
    61(4):631-653. https://doi.org/10.2307/2297912
  - Hall, P. 1992. *The Bootstrap and Edgeworth Expansion.* Springer,
    ISBN 978-0-387-94508-8.
    https://doi.org/10.1007/978-1-4612-4384-7
  - Davison, A. C. & Hinkley, D. V. 1997. *Bootstrap Methods and
    their Application.* Cambridge Univ. Press, ISBN 978-0-521-57471-6.
    https://doi.org/10.1017/CBO9780511802843
  - Jobson, J. D. & Korkie, B. M. 1981. "Performance Hypothesis
    Testing with the Sharpe and Treynor Measures". *J. Finance*
    36(4):889-908. https://doi.org/10.1111/j.1540-6261.1981.tb04891.x
    — the original delta-method derivation on the joint
    (mu, sigma^2) moment vector.

Verification status
-------------------

The published *J. Empirical Finance* version (paywalled on
ScienceDirect) is the canonical reference. The construction has
been verified equation-by-equation against the open-access
companion working paper [University of Zurich IEW Working Paper
320](https://www.econ.uzh.ch/apps/workingpapers/wp/iewwp320.pdf)
(text-identical to the published version per the authors'
deposited copy at Ledoit's University of Zurich page; cross-checked
by full-text extraction at remediation time):

  - **WP Eq. (1)-(2)** — Sharpe-ratio difference
    ``Δ = f(θ)`` with raw-moment parameterisation
    ``θ = (μ_a, γ_a, μ_b, γ_b)``, ``f(a, b, c, d) = a/√(c-a²) -
    b/√(d-b²)``. Matches our ``_sharpe_biased`` and the gradient in
    ``_hac_se_sharpe_difference``.
  - **WP Eq. (3)-(4)** — joint asymptotic normality
    ``√T (θ̂ - θ) →_d N(0, Ψ)`` and the delta-method form
    ``√T (Δ̂ - Δ) →_d N(0, ∇f' Ψ ∇f)``; the gradient ``∇f`` at WP
    Eq. (4) coincides exactly with our four-component ``grad``.
  - **WP Eq. (5)** — standard error ``s(Δ̂) = √(∇f' Ψ̂ ∇f / T)``;
    matches our ``se_HAC = sqrt(grad' Ψ grad)`` after the ``√T``
    rescaling explicit in the docstring of
    ``_hac_se_sharpe_difference``.
  - **WP Eq. (6)** — studentised statistic
    ``L(|Δ̂ - Δ|/s(Δ̂)) ≈ L*(|Δ̂* - Δ̂|/s(Δ̂*))``; the bootstrap
    distribution we form on ``T*`` is the centred-and-studentised
    quantity at WP Eq. (6).
  - **WP §3.2.2** — circular block bootstrap (CBB) with paired
    indices and **per-replicate** standard error ``s(Δ̂*)``
    computed via prewhitened QS kernel; project substitutes the
    Politis-Romano 1994 stationary bootstrap (per the
    "Bootstrap variant substitution" subsection above) and
    Newey-West 1987 Bartlett kernel. Per-replicate bandwidth
    re-selection is the LW2008 spec; the present implementation
    re-selects the bandwidth per replicate by default
    (``bandwidth_strategy="per_replicate"``) — see
    ``ledoit_wolf_2008_differential_ci`` parameter docs.
  - **WP §3.2.2 (block-length calibration, Algorithm 3.1)** —
    LW2008 specifies an iterated bootstrap calibration loop with
    pseudo sequences from a fitted VAR(1) + residual stationary
    bootstrap to choose the block length. Project substitutes
    Politis-White 2004 (+ PPW 2009 correction) automatic
    block-length selection on the paired-difference series — a
    one-shot data-driven selection with the same first-order
    asymptotic guarantee. Tracked as residual; cross-checked
    against Cycle-5 follow-up ``P1-LW2008-CALIBRATION-VS-PW2004``
    (open).

Closes the verification-gap residual ``P1-LW2008-PDF-VERIFY``.
Both the published *J. Empirical Finance* version
(https://doi.org/10.1016/j.jempfin.2008.03.002) and the open-access
WP 320 mirror are cited in the References section above.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    politis_white_block_length,
    stationary_bootstrap_indices,
)
from skie_ninja.inference.stats.hac import (
    BandwidthSelection,
    nw1994_bartlett_bandwidth,
)

# Float64 ULP as a variance-scale floor — same as Cycle-5 conventions
# in [src/skie_ninja/inference/multipletest/hansen_spa.py](../multipletest/hansen_spa.py).
_EPS = float(np.finfo(np.float64).eps)

# Minimum sample size: the joint-moment-vector HAC estimator requires
# at least 4 observations to admit a positive-bandwidth NW 1994
# automatic-bandwidth selection (`nw1994_bartlett_bandwidth` raises at
# n < 4).
_MIN_OBS = 4

_METHOD_LABEL = Literal["ledoit_wolf_2008_studentised_stationary_bootstrap"]


@dataclass(frozen=True)
class DifferentialCIResult:
    """Frozen output of :func:`ledoit_wolf_2008_differential_ci`.

    ``point_estimate`` is ``SR_a - SR_b`` computed with Lo 2002
    biased (``ddof=0``) plug-in moments — the convention internally
    consistent with the Mertens / Jobson-Korkie / Ledoit-Wolf delta-
    method derivation. ``lower``, ``upper`` are the two-sided
    studentised-pivot bootstrap CI endpoints. ``se_hac`` is the
    delta-method HAC standard error of ``sqrt(T) * (SR_a - SR_b)``.
    ``q_lower`` and ``q_upper`` are the bootstrap quantiles of the
    studentised statistic ``T^*`` at levels ``alpha/2`` and
    ``1 - alpha/2`` — recorded for downstream auditability.
    ``bandwidth_strategy`` records the per-replicate vs fixed-at-
    original choice (default ``"per_replicate"`` matches LW2008
    WP 320 §3.2.2). ``n_degenerate_resamples`` counts bootstrap
    replicates whose subseries had zero variance and were assigned
    ``T*ᵇ = 0`` (sentinel; NaN would corrupt the empirical
    quantile).
    """

    point_estimate: float
    lower: float
    upper: float
    alpha: float
    se_hac: float
    q_lower: float
    q_upper: float
    n_obs: int
    n_bootstrap: int
    block_length: float
    bandwidth: int
    method: str
    block_length_selection: BlockLengthSelection
    bandwidth_selection: BandwidthSelection
    bandwidth_strategy: str = "per_replicate"
    n_degenerate_resamples: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "point_estimate": self.point_estimate,
            "lower": self.lower,
            "upper": self.upper,
            "alpha": self.alpha,
            "se_hac": self.se_hac,
            "q_lower": self.q_lower,
            "q_upper": self.q_upper,
            "n_obs": self.n_obs,
            "n_bootstrap": self.n_bootstrap,
            "block_length": self.block_length,
            "bandwidth": self.bandwidth,
            "method": self.method,
            "block_length_selection": self.block_length_selection.to_dict(),
            "bandwidth_selection": self.bandwidth_selection.to_dict(),
            "bandwidth_strategy": self.bandwidth_strategy,
            "n_degenerate_resamples": self.n_degenerate_resamples,
        }


# ---------------------------------------------------------------------------
# Internal: input validation and joint-moment-vector HAC SE
# ---------------------------------------------------------------------------


def _as_clean_paired(
    a: npt.ArrayLike,
    b: npt.ArrayLike,
) -> tuple[np.ndarray, np.ndarray]:
    """Coerce to 1-D float64 paired arrays; reject NaN/inf/length mismatch."""
    arr_a = np.asarray(a, dtype=np.float64).reshape(-1)
    arr_b = np.asarray(b, dtype=np.float64).reshape(-1)
    if arr_a.shape != arr_b.shape:
        raise ValueError(
            f"returns_a and returns_b must have identical shape; "
            f"got {arr_a.shape} vs {arr_b.shape}."
        )
    if not np.all(np.isfinite(arr_a)) or not np.all(np.isfinite(arr_b)):
        raise ValueError(
            "Input contains NaN or inf; LW2008 routines do not impute. "
            "Drop or interpolate upstream."
        )
    if arr_a.size < _MIN_OBS:
        raise ValueError(
            f"ledoit_wolf_2008_differential_ci requires n >= {_MIN_OBS}, "
            f"got {arr_a.size}."
        )
    return arr_a, arr_b


def _sharpe_biased(r: np.ndarray) -> tuple[float, float, float]:
    """Lo 2002 biased plug-in: returns ``(SR, mu, sigma^2_biased)``.

    ``ddof = 0``: matches the Mertens / Jobson-Korkie / Ledoit-Wolf
    asymptotic-derivation convention. Raises if ``sigma^2 <= 0``.

    Distinct from the project-canonical ``sample_sharpe`` at
    [src/skie_ninja/inference/stats/sharpe_ci.py](sharpe_ci.py) by
    returning the ``(SR, mu, var)`` triple in a single pass — the
    moments are reused downstream (centred Sharpe-difference at the
    bootstrap loop, gradient evaluation in
    ``_hac_se_sharpe_difference``) so the helper avoids two extra
    ``mean`` / ``var`` calls per resample under
    ``n_bootstrap`` repetitions. Spec criterion 8 (vectorisation /
    perf) governs the duplication here.
    """
    mu = float(r.mean())
    var = float(r.var(ddof=0))
    if var <= 0.0:
        raise ValueError(
            "Sample variance is zero (degenerate series); SR is undefined."
        )
    return mu / math.sqrt(var), mu, var


def _hac_se_sharpe_difference(
    r_a: np.ndarray,
    r_b: np.ndarray,
    *,
    bandwidth: int,
) -> float:
    """HAC SE of ``sqrt(T) * (SR_a - SR_b)`` via joint-moment delta method.

    Construction (Jobson-Korkie 1981 + Memmel 2003 + Ledoit-Wolf 2008
    §3.1):

      1. Per-period vector
         ``v_t = (r_{a,t}, r_{a,t}^2, r_{b,t}, r_{b,t}^2)``.
      2. Long-run covariance matrix ``Psi`` (4x4) of ``v_t``,
         estimated by Newey-West 1987 with Bartlett kernel applied
         to each of the 16 entries of the lag-autocovariance matrix:
         ``Psi = Gamma_0 + sum_{k=1}^L (1 - k/(L+1)) * (Gamma_k + Gamma_k^T)``
         where ``Gamma_k = (1/T) sum_{t=k+1}^T (v_t - v_bar)(v_{t-k} - v_bar)^T``
         (biased estimator, divisor T, matching NW 1987).
      3. Gradient of ``f(theta) = SR_a - SR_b`` at the sample
         estimate, where ``theta = (mu_a, gamma_a, mu_b, gamma_b)``:
         using ``SR_i = mu_i / sqrt(gamma_i - mu_i^2)``,
           ``df/dmu_a   = gamma_a / sigma_a^3``
           ``df/dgamma_a = -mu_a / (2 sigma_a^3)``
           ``df/dmu_b   = -gamma_b / sigma_b^3``
           ``df/dgamma_b =  mu_b / (2 sigma_b^3)``
         (Jobson-Korkie 1981 eq. 8 generalises to the paired form;
         signs flip for the second series.)
      4. ``Var(sqrt(T) Delta_hat) ≈ grad^T Psi grad``;
         ``se_HAC = sqrt(grad^T Psi grad)``.

    Returns the HAC standard error of ``sqrt(T) * Delta_hat``.
    Floored at ``sqrt(_EPS)`` to guard against
    division-by-zero in the studentised statistic; the floor is
    on the variance scale (consistent with Hansen-SPA convention
    in [src/skie_ninja/inference/multipletest/hansen_spa.py](../multipletest/hansen_spa.py)).
    """
    n = r_a.size
    bw = max(0, min(int(bandwidth), n - 1))

    # Step 1: per-period vector v_t (shape (T, 4)).
    v = np.column_stack([r_a, r_a * r_a, r_b, r_b * r_b])
    v_c = v - v.mean(axis=0)

    # Step 2: long-run covariance Psi via NW Bartlett on 4-D vector.
    # Gamma_0 = (1/T) v_c^T v_c
    gamma_0 = (v_c.T @ v_c) / n
    psi = gamma_0.copy()
    for k in range(1, bw + 1):
        # Gamma_k = (1/T) sum_{t=k}^{T-1} v_c[t] outer v_c[t-k]
        gamma_k = (v_c[k:].T @ v_c[:-k]) / n
        weight = 1.0 - k / (bw + 1.0)
        psi = psi + weight * (gamma_k + gamma_k.T)

    # Step 3: gradient at the sample estimate.
    mu_a = float(r_a.mean())
    mu_b = float(r_b.mean())
    gamma_a = float((r_a * r_a).mean())
    gamma_b = float((r_b * r_b).mean())
    sigma_a_sq = gamma_a - mu_a * mu_a
    sigma_b_sq = gamma_b - mu_b * mu_b
    if sigma_a_sq <= 0 or sigma_b_sq <= 0:
        raise ValueError(
            "Joint-moment-vector HAC: degenerate variance encountered "
            "(sigma^2 <= 0); cannot evaluate gradient."
        )
    sigma_a3 = sigma_a_sq * math.sqrt(sigma_a_sq)
    sigma_b3 = sigma_b_sq * math.sqrt(sigma_b_sq)
    grad = np.array(
        [
            gamma_a / sigma_a3,
            -mu_a / (2.0 * sigma_a3),
            -gamma_b / sigma_b3,
            mu_b / (2.0 * sigma_b3),
        ],
        dtype=np.float64,
    )

    # Step 4: var of sqrt(T) Delta_hat = grad^T Psi grad.
    var_root_t_delta = float(grad @ psi @ grad)
    # Float64 may produce small negatives via cancellation in NW kernel
    # weighting; floor at _EPS on the variance scale.
    var_root_t_delta = max(var_root_t_delta, _EPS)
    return math.sqrt(var_root_t_delta)


def _resolve_block_length(
    diff_series: np.ndarray,
    block_length: float | None,
) -> BlockLengthSelection:
    """Resolve user-supplied or auto-selected stationary-bootstrap block length."""
    if block_length is None:
        return politis_white_block_length(
            diff_series, bootstrap_type="stationary"
        )
    if block_length < 1.0:
        raise ValueError(f"block_length must be >= 1, got {block_length}.")
    return BlockLengthSelection(
        method="fixed",
        block_length=float(block_length),
        bootstrap_type="stationary",
        notes="caller-specified fixed block length (LW2008 differential CI).",
    )


def _resolve_bandwidth(
    diff_series: np.ndarray,
    bandwidth: int | BandwidthSelection | None,
) -> BandwidthSelection:
    """Resolve user-supplied or auto-selected NW Bartlett truncation lag."""
    if bandwidth is None:
        return nw1994_bartlett_bandwidth(diff_series)
    if isinstance(bandwidth, BandwidthSelection):
        return bandwidth
    bw_int = int(bandwidth)
    if bw_int < 0:
        raise ValueError(f"bandwidth must be >= 0, got {bw_int}.")
    return BandwidthSelection(
        method="fixed",
        bandwidth=bw_int,
        kernel="bartlett",
        notes="caller-specified fixed bandwidth (LW2008 differential CI).",
    )


def _bootstrap_studentised_distribution(
    arr_a: np.ndarray,
    arr_b: np.ndarray,
    *,
    delta_hat: float,
    block_length: float,
    bandwidth: int,
    bandwidth_strategy: str,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, int]:
    """Bootstrap distribution of the studentised statistic.

    Returns ``(t_boot, n_degenerate)`` where ``t_boot[b] = √T ·
    (Δ*ᵇ − Δ̂) / se*ᵇ`` and ``n_degenerate`` counts replicates whose
    resamples had zero variance (assigned ``T*ᵇ = 0`` sentinel; see
    LW2008 WP 320 §3.2.2 footnote 9 on degenerate handling).

    Bandwidth handling follows ``bandwidth_strategy``:
      - "per_replicate" (default; LW2008 WP 320 §3.2.2 spec) —
        re-select NW 1994 truncation lag on the per-replicate
        paired-difference series. Lahiri 2003 §3.3 establishes
        that bootstrap variance of Bartlett-kernel HAC estimators
        differs under fixed-vs-per-replicate bandwidth; the
        deviation is methodologically real (not first-order
        asymptotically equivalent), hence per-replicate is the
        spec-faithful default.
      - "fixed_at_original" — hold ``bandwidth`` at the original-
        data choice across all replicates (Davison & Hinkley 1997
        §5.4 surrounding eq. 5.10 permits this when re-estimation
        is prohibitive; Hansen 2005 SPA's bootstrap-omega
        convention follows the same pattern). Opt-in sensitivity.
    """
    n = arr_a.size
    sqrt_n = math.sqrt(n)
    t_boot = np.empty(n_bootstrap, dtype=np.float64)
    n_degenerate = 0
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(
            n, block_length=block_length, rng=rng
        )
        a_star = arr_a[idx]
        b_star = arr_b[idx]
        try:
            sr_a_star, _, _ = _sharpe_biased(a_star)
            sr_b_star, _, _ = _sharpe_biased(b_star)
        except ValueError:
            t_boot[b] = 0.0
            n_degenerate += 1
            continue
        delta_star = sr_a_star - sr_b_star
        if bandwidth_strategy == "per_replicate":
            try:
                bw_star = nw1994_bartlett_bandwidth(
                    a_star - b_star
                ).bandwidth
            except ValueError:
                bw_star = bandwidth
        else:
            bw_star = bandwidth
        try:
            se_star = _hac_se_sharpe_difference(
                a_star, b_star, bandwidth=bw_star
            )
        except ValueError:
            t_boot[b] = 0.0
            n_degenerate += 1
            continue
        t_boot[b] = sqrt_n * (delta_star - delta_hat) / se_star
    return t_boot, n_degenerate


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def ledoit_wolf_2008_differential_ci(
    returns_a: npt.ArrayLike,
    returns_b: npt.ArrayLike,
    *,
    alpha: float = 0.05,
    n_bootstrap: int = 2000,
    block_length: float | None = None,
    bandwidth: int | BandwidthSelection | None = None,
    bandwidth_strategy: Literal["per_replicate", "fixed_at_original"] = (
        "per_replicate"
    ),
    rng: np.random.Generator | None = None,
) -> DifferentialCIResult:
    """Studentized time-series bootstrap CI for ``SR_a - SR_b``.

    Implements the Ledoit & Wolf 2008 *J. Empirical Finance*
    15(5):850-859 (doi:10.1016/j.jempfin.2008.03.002) studentised
    pivotal CI for the difference of two Sharpe ratios. Standard
    error via Jobson-Korkie 1981 + Memmel 2003 joint-moment-vector
    delta method with Newey-West 1987 + Newey-West 1994 HAC plug-in
    on the 4-D vector ``v_t = (r_a, r_a^2, r_b, r_b^2)``. Bootstrap
    distribution of the studentised statistic via Politis-Romano 1994
    stationary bootstrap (substitution for the paper's circular
    block bootstrap; first-order asymptotic equivalence per
    Lahiri 2003 Chapter 5) with block length from Politis-White
    2004 (+ PPW 2009 correction) on the paired-difference series
    ``r_a - r_b``. Paired indices
    are reused across the two series within each bootstrap
    replicate, preserving cross-series dependence.

    The resulting CI is in the "studentised pivotal" form (Hall 1992
    §3.5 / Davison & Hinkley 1997 §5.4 eq. 5.10):

        ``[Delta - q_{1-alpha/2}(T^*) * se / sqrt(T),
           Delta - q_{alpha/2}(T^*) * se / sqrt(T)]``

    where ``T^* = sqrt(T) (Delta^* - Delta) / se^*``. Asymmetric
    quantile usage is intentional — symmetric ``Delta ± q * se``
    misses skewness in the studentised distribution and is NOT what
    Ledoit-Wolf 2008 specifies.

    Parameters
    ----------
    returns_a, returns_b
        Paired arithmetic-return series of identical length. Caller
        must align on time axis upstream; this function does not
        attempt any reconciliation. NaN / inf inputs are rejected.
    alpha
        Two-sided significance level (default ``0.05`` per
        [ADR-0004](../../../../docs/decisions/ADR-0004-alpha-and-power-defaults.md)).
        Must satisfy ``0 < alpha < 1``.
    n_bootstrap
        Number of bootstrap replications. Default ``2000`` per
        Hall 1992 §1.5 (see module docstring).
    block_length
        Expected stationary-bootstrap block length. ``None`` (default)
        triggers Politis-White 2004 automatic selection on the
        paired-difference series ``r_a - r_b``.
    bandwidth
        HAC truncation lag for the joint-moment-vector covariance.
        ``None`` (default) triggers Newey-West 1994 automatic
        selection on the paired-difference series ``r_a - r_b``
        (a single scalar bandwidth shared across all 16 entries of
        ``Psi`` per the standard Bartlett-kernel reduction).
        Integer or :class:`BandwidthSelection` accepted. The
        original-data bandwidth is always recorded on the result;
        when ``bandwidth_strategy="per_replicate"`` the bootstrap
        replicates select their own bandwidth via NW 1994 on the
        per-replicate paired-difference series (caller-supplied
        bandwidth is honoured only on the original data).
    bandwidth_strategy
        Whether to re-select the NW 1994 truncation lag on each
        bootstrap resample (``"per_replicate"``, default — matches
        LW2008 WP 320 §3.2.2 spec) or to hold the lag fixed at the
        original-data choice across all replicates
        (``"fixed_at_original"``, opt-in for sensitivity analysis
        and backwards-compatibility with the pre-Round-2 default).
        Per-replicate is the spec-faithful choice; the fixed-lag
        variant is provided as a documented sensitivity option per
        Lahiri 2003 §3.3 (bootstrap variance of Bartlett-kernel HAC
        estimators differs under fixed-vs-per-replicate bandwidth
        — the deviation is methodologically real, not first-order
        asymptotically equivalent). Per-replicate selection adds
        an O(n) autocovariance sweep per resample; the
        ``nw1994_bartlett_bandwidth`` primitive is O(n) per call so
        the total cost is O(B · n) rather than O(B · n²) — workable
        on the H050 panel (n ≈ 1500, B = 2000).
    rng
        NumPy ``Generator``. Defaults to
        ``np.random.default_rng()``; callers seeding for
        reproducibility should pass an explicit generator.

    Returns
    -------
    DifferentialCIResult
        Frozen dataclass with point estimate, two-sided endpoints,
        HAC standard error, bootstrap quantiles, and reproducibility
        metadata (block-length and bandwidth selection records).

    Raises
    ------
    ValueError
        If inputs have mismatched length, contain non-finite values,
        ``n < 4``, ``alpha`` is out of range, ``n_bootstrap < 1``,
        or either series has zero variance.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must satisfy 0 < alpha < 1, got {alpha}.")
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}.")
    if block_length is not None and block_length < 1.0:
        raise ValueError(
            f"block_length must be >= 1, got {block_length}."
        )
    if bandwidth_strategy not in ("per_replicate", "fixed_at_original"):
        raise ValueError(
            f"bandwidth_strategy must be 'per_replicate' or "
            f"'fixed_at_original', got {bandwidth_strategy!r}."
        )
    arr_a, arr_b = _as_clean_paired(returns_a, returns_b)
    if rng is None:
        rng = np.random.default_rng()

    n = arr_a.size

    # 1. Sample Sharpe difference (biased moments — derivation convention).
    sr_a, _mu_a, _var_a = _sharpe_biased(arr_a)
    sr_b, _mu_b, _var_b = _sharpe_biased(arr_b)
    delta_hat = sr_a - sr_b

    # 2-3. Block length + bandwidth resolution on paired-difference series.
    diff_series = arr_a - arr_b
    bl_record = _resolve_block_length(diff_series, block_length)
    bl = bl_record.block_length
    bw_record = _resolve_bandwidth(diff_series, bandwidth)
    bw = bw_record.bandwidth

    # 4. Sample HAC SE of sqrt(T) * Delta_hat.
    se_hac = _hac_se_sharpe_difference(arr_a, arr_b, bandwidth=bw)

    # 5. Bootstrap distribution of the studentised statistic. See
    # ``_bootstrap_studentised_distribution`` for the per-replicate
    # vs fixed-at-original bandwidth contract.
    t_boot, n_degenerate = _bootstrap_studentised_distribution(
        arr_a,
        arr_b,
        delta_hat=delta_hat,
        block_length=bl,
        bandwidth=bw,
        bandwidth_strategy=bandwidth_strategy,
        n_bootstrap=n_bootstrap,
        rng=rng,
    )

    # 6. Studentised-pivot CI (Hall 1992 §3.5; D&H 1997 eq. 5.10).
    sqrt_n = math.sqrt(n)
    q_lower = float(np.quantile(t_boot, alpha / 2.0))
    q_upper = float(np.quantile(t_boot, 1.0 - alpha / 2.0))
    half_width_unit = se_hac / sqrt_n
    lower = delta_hat - q_upper * half_width_unit
    upper = delta_hat - q_lower * half_width_unit

    return DifferentialCIResult(
        point_estimate=delta_hat,
        lower=float(lower),
        upper=float(upper),
        alpha=alpha,
        se_hac=se_hac,
        q_lower=q_lower,
        q_upper=q_upper,
        n_obs=n,
        n_bootstrap=n_bootstrap,
        block_length=float(bl),
        bandwidth=int(bw),
        method="ledoit_wolf_2008_studentised_stationary_bootstrap",
        block_length_selection=bl_record,
        bandwidth_selection=bw_record,
        bandwidth_strategy=bandwidth_strategy,
        n_degenerate_resamples=n_degenerate,
    )


__all__ = [
    "DifferentialCIResult",
    "ledoit_wolf_2008_differential_ci",
]
