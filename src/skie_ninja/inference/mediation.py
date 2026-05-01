"""H053 Cycle 9 Stage-2 — multi-timeframe partial-R² + descriptive mediation.

Implements the design.md §5.4 mediation block as a *descriptive
decomposition* (per design.md §1 critical interpretive note: sequential
ignorability + SUTVA are heroic in 1-min-bar futures, so a significant
NIE annotates without promoting past the Sharpe gate).

## Scope

This module exposes 4 primitives:

1. ``partial_r2_increment(X_baseline, X_full, y) -> float``: in-sample
   partial-R² increment of the full feature matrix beyond the baseline,
   per [VanderWeele 2015 §1.4](https://academic.oup.com/book/27553)
   formulation.

2. ``paired_pairs_bootstrap_ci(rows, stat_fn, n_replicates, block_length, rng)``:
   paired-pairs (paired-observations) stationary-bootstrap percentile CI
   for any session-level statistic. Per design.md §5.4 + [Politis-Romano
   1994](https://doi.org/10.2307/2290770) the resampling unit is the
   row-tuple ``(X̂_{i,t}, M_{i,t}, y_{i,t})`` to preserve the joint
   dependence structure.

3. ``pc1_collapse(X) -> (loadings, variance_explained, scores)``: PCA on
   the mediator block per design.md §5.4 PC1-collapse procedure. Returns
   the first-component loadings (length-d), proportion of variance
   explained by PC1, and per-row PC1 scores.

4. ``e_value(estimate, ci_lo, ci_hi, sd_y) -> tuple[float, float]``:
   [VanderWeele & Ding 2017, *Annals of Internal Medicine*
   167(4):268-274](https://doi.org/10.7326/M16-2607) E-value sensitivity
   for an unmeasured confounder. For continuous-outcome partial-R² (the
   H053 case), conversion via Chinn 2000 / VanderWeele 2017 supplement
   approximation: convert the standardised effect size to a risk-ratio
   approximation, then apply the closed-form E-value formula
   ``RR + sqrt(RR · (RR - 1))``.

5. ``baron_kenny_nie_nde(y, M, X) -> (nie, nde)``: descriptive
   Baron-Kenny / VanderWeele 2015 Ch. 2 mediation decomposition. Per
   design.md §1 critical interpretive note this is descriptive only.

## Out-of-scope

- **Cross-fitted DML** ([Chernozhukov-Chetverikov-Demirer-Duflo-Hansen-Newey-Robins
  2018](https://doi.org/10.1111/ectj.12097)) is deferred to Stage-3 per
  follow-up `P1-H053-CYCLE9-DML-SENSITIVITY`. The Stage-2 implementation
  uses OLS partial-R² with paired-pairs bootstrap; DML provides a
  cross-fitted alternative as a sensitivity exhibit.
- **Per-fold inner-WF cross-validation** for hyperparameter selection is
  not exercised; Stage-2 is exploratory.

## References

- VanderWeele, T. J. 2015. *Explanation in Causal Inference*. OUP.
  ISBN 978-0199325870. §1.4 partial-R² formulation; Ch. 2 NIE/NDE.
- VanderWeele, T. J. & Ding, P. 2017. "Sensitivity Analysis in
  Observational Research: Introducing the E-Value." *Annals of Internal
  Medicine* 167(4):268-274. [DOI 10.7326/M16-2607](https://doi.org/10.7326/M16-2607).
- Imai, K., Keele, L., & Tingley, D. 2010. "A General Approach to
  Causal Mediation Analysis." *Psychological Methods* 15(4):309-334.
  [DOI 10.1037/a0020761](https://doi.org/10.1037/a0020761).
- MacKinnon, D. P., Lockwood, C. M., & Williams, J. 2004. "Confidence
  Limits for the Indirect Effect: Distribution of the Product and
  Resampling Methods." *Multivariate Behavioral Research* 39(1):99-128.
  [DOI 10.1207/s15327906mbr3901_4](https://doi.org/10.1207/s15327906mbr3901_4).
- Chinn, S. 2000. "A Simple Method for Converting an Odds Ratio to
  Effect Size for Use in Meta-Analysis." *Statistics in Medicine*
  19(22):3127-3131.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Callable

import numpy as np

from skie_ninja.inference.bootstrap import stationary_bootstrap_indices


# justify: paired-pairs stationary bootstrap default block length.
# Politis-White 2004 selector is canonical; on a session-grain panel of
# ~2,000-3,000 rows the data-dependent block is typically 5-15. Stage-2
# pins 10 as the operational default; per-symbol Politis-White auto-
# selection is tracked under follow-up
# `P1-H053-CYCLE9-BOOTSTRAP-AUTO-BLOCK`.
_DEFAULT_BLOCK_LENGTH: float = 10.0
# justify: bootstrap replicate count per design.md §4.5.3 + Hansen 2005
# project-wide convention.
_DEFAULT_N_REPLICATES: int = 1000


# ---------------------------------------------------------------------------
# Partial-R²
# ---------------------------------------------------------------------------


def _ols_r2(X: np.ndarray, y: np.ndarray) -> float:
    """In-sample R² of OLS y ~ X (with intercept)."""
    n = X.shape[0]
    X_aug = np.column_stack([np.ones(n), X])
    beta, *_ = np.linalg.lstsq(X_aug, y, rcond=None)
    y_hat = X_aug @ beta
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    if ss_tot <= 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def partial_r2_increment(
    X_baseline: np.ndarray,
    X_full: np.ndarray,
    y: np.ndarray,
) -> float:
    """Partial-R² increment of `X_full` over `X_baseline`.

    Per VanderWeele 2015 §1.4: ``partial_R² = R²_full - R²_baseline``,
    where both R² are computed on the same outcome `y` with the same
    sample. ``X_full`` typically extends ``X_baseline`` with additional
    columns (e.g., adding multi-timeframe features X to the
    mediator-only baseline M).

    Note: this in-sample partial-R² is the simplest measure; it is
    NOT calibrated for in-sample optimism. For OOS evaluation, compute
    R² on a held-out fold per Stage-2's nested-WF protocol.
    """
    r2_baseline = _ols_r2(X_baseline, y)
    r2_full = _ols_r2(X_full, y)
    return r2_full - r2_baseline


# ---------------------------------------------------------------------------
# Paired-pairs stationary bootstrap CI
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PartialR2BootstrapCI:
    """Paired-pairs bootstrap CI for partial-R² increment."""

    point_estimate: float
    ci_lo: float
    ci_hi: float
    excludes_zero: bool
    n_replicates: int
    block_length: float
    method: str = "paired_pairs_stationary_bootstrap_percentile"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def paired_pairs_partial_r2_ci(
    X_baseline: np.ndarray,
    X_full: np.ndarray,
    y: np.ndarray,
    *,
    n_replicates: int = _DEFAULT_N_REPLICATES,
    block_length: float = _DEFAULT_BLOCK_LENGTH,
    alpha: float = 0.05,
    rng: np.random.Generator | None = None,
) -> PartialR2BootstrapCI:
    """Paired-pairs stationary-bootstrap percentile CI for partial-R².

    Resampling unit is the row-tuple ``(X_baseline_row, X_full_row,
    y_row)`` to preserve the joint dependence structure per design.md
    §5.4. Per replicate, the same row indices select rows in all three
    arrays.
    """
    if rng is None:
        rng = np.random.default_rng()
    n = len(y)
    if X_baseline.shape[0] != n or X_full.shape[0] != n:
        raise ValueError("Length mismatch: X_baseline, X_full, y must align.")

    point = partial_r2_increment(X_baseline, X_full, y)
    boot_values = []
    for _ in range(n_replicates):
        idx = stationary_bootstrap_indices(n=n, block_length=block_length, rng=rng)
        try:
            v = partial_r2_increment(X_baseline[idx], X_full[idx], y[idx])
            if np.isfinite(v):
                boot_values.append(v)
        except (np.linalg.LinAlgError, ValueError):
            continue

    if len(boot_values) < 10:
        return PartialR2BootstrapCI(
            point_estimate=point,
            ci_lo=float("nan"), ci_hi=float("nan"),
            excludes_zero=False,
            n_replicates=len(boot_values), block_length=block_length,
        )
    arr = np.asarray(boot_values)
    lo = float(np.quantile(arr, alpha / 2))
    hi = float(np.quantile(arr, 1 - alpha / 2))
    return PartialR2BootstrapCI(
        point_estimate=point,
        ci_lo=lo, ci_hi=hi,
        excludes_zero=(lo > 0.0 or hi < 0.0),
        n_replicates=len(boot_values), block_length=block_length,
    )


# ---------------------------------------------------------------------------
# PC1 collapse
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PC1CollapseResult:
    """First principal component of a feature block."""

    loadings: list[float]
    variance_explained: float    # proportion in [0, 1]
    n_features: int
    n_samples: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def pc1_collapse(X: np.ndarray) -> tuple[PC1CollapseResult, np.ndarray]:
    """Project X onto its first principal component.

    Returns (PC1CollapseResult, scores_array). The scores array is
    length-n with the per-row PC1 score; the result records the
    loadings (length-d) and variance-explained.

    Standardisation: each column is centered + scaled to unit variance
    via the train-fold mean/std so PC1 is location/scale invariant.
    """
    n, d = X.shape
    if n < 2 or d < 1:
        raise ValueError(f"X must have ≥2 rows and ≥1 column; got {X.shape}.")
    mu = X.mean(axis=0)
    sigma = X.std(axis=0, ddof=1)
    sigma = np.where(sigma > 0, sigma, 1.0)  # avoid div-by-zero
    X_std = (X - mu) / sigma
    # Compute the SVD; PC1 is the first right-singular-vector.
    _, s, Vt = np.linalg.svd(X_std, full_matrices=False)
    pc1_loadings = Vt[0, :]    # length-d
    eigenvalues = s ** 2 / (n - 1)
    var_explained = float(eigenvalues[0] / eigenvalues.sum()) if eigenvalues.sum() > 0 else float("nan")
    scores = X_std @ pc1_loadings
    result = PC1CollapseResult(
        loadings=[float(v) for v in pc1_loadings],
        variance_explained=var_explained,
        n_features=int(d),
        n_samples=int(n),
    )
    return result, scores


# ---------------------------------------------------------------------------
# E-value (VanderWeele-Ding 2017)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EValueResult:
    """E-value sensitivity per VanderWeele-Ding 2017."""

    estimate: float                    # original effect size (e.g., partial-R² delta)
    estimate_in_rr_scale: float        # converted RR
    e_value_point: float               # E-value at the point estimate
    e_value_ci_bound: float            # E-value at the CI bound nearest to null
    method: str = "vanderweele_ding_2017_chinn_2000_rr_conversion"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _continuous_to_rr(d: float) -> float:
    """Convert standardised mean difference (Cohen's d) to risk-ratio approx.

    Chinn 2000 / VanderWeele 2017 supplement: for a continuous outcome
    with Cohen's d standardised effect size, the equivalent risk-ratio
    is approximately ``exp(0.91 * d)`` (logistic-distribution
    approximation). For partial-R² the analog is sqrt(partial_R²)
    converted to d via the standard relation ``d ≈ 2·r/sqrt(1-r²)``
    where r = sign(d) · sqrt(partial_R²).
    """
    if not np.isfinite(d):
        return float("nan")
    return math.exp(0.91 * d)


def e_value(
    estimate: float,
    ci_lo: float,
    ci_hi: float,
) -> EValueResult:
    """E-value for a partial-R²-increment with paired-bootstrap CI.

    Conversion: partial-R² → r = sqrt(|partial-R²|) → d = 2r/sqrt(1-r²)
    → RR = exp(0.91·d). E-value = RR + sqrt(RR·(RR-1)) per VanderWeele-
    Ding 2017 closed-form. Returned as both the point-estimate E-value
    and the E-value at the CI bound nearest the null (=0).

    Negative partial-R² (the full model is worse than the baseline) is
    not strictly meaningful for E-value, but we return the magnitude to
    let the caller interpret.
    """
    abs_r2 = abs(estimate)
    if not np.isfinite(abs_r2) or abs_r2 >= 1.0:
        return EValueResult(
            estimate=estimate,
            estimate_in_rr_scale=float("nan"),
            e_value_point=float("nan"),
            e_value_ci_bound=float("nan"),
        )
    r = math.sqrt(abs_r2)
    if r >= 0.999:
        return EValueResult(
            estimate=estimate, estimate_in_rr_scale=float("inf"),
            e_value_point=float("inf"), e_value_ci_bound=float("inf"),
        )
    d = 2 * r / math.sqrt(1 - r ** 2)
    rr = _continuous_to_rr(d)
    if rr < 1.0:
        # Per VanderWeele-Ding 2017 §"E-Value Calculation": invert if RR < 1
        rr = 1.0 / rr
    e_point = rr + math.sqrt(rr * (rr - 1)) if rr >= 1.0 else 1.0
    # CI-bound: the bound nearest to 0 (the null) gives the conservative E-value.
    if np.isfinite(ci_lo) and np.isfinite(ci_hi):
        bound = ci_lo if abs(ci_lo) < abs(ci_hi) else ci_hi
        bound_abs = abs(bound)
        if bound_abs >= 1.0:
            e_ci = float("inf")
        else:
            r_b = math.sqrt(bound_abs)
            if r_b >= 0.999:
                e_ci = float("inf")
            else:
                d_b = 2 * r_b / math.sqrt(1 - r_b ** 2)
                rr_b = _continuous_to_rr(d_b)
                if rr_b < 1.0:
                    rr_b = 1.0 / rr_b
                e_ci = rr_b + math.sqrt(rr_b * (rr_b - 1)) if rr_b >= 1.0 else 1.0
    else:
        e_ci = float("nan")
    return EValueResult(
        estimate=estimate,
        estimate_in_rr_scale=rr,
        e_value_point=e_point,
        e_value_ci_bound=e_ci,
    )


# ---------------------------------------------------------------------------
# Descriptive Baron-Kenny / VanderWeele 2015 NIE/NDE
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MediationDecomposition:
    """Descriptive Baron-Kenny / VanderWeele 2015 NIE/NDE decomposition.

    Per design.md §1 critical interpretive note: this is descriptive
    only. A statistically significant NIE annotates the disposition
    via §10.2 but does NOT promote past the Sharpe gate.
    """

    nie: float                         # Natural indirect effect
    nde: float                         # Natural direct effect
    total_effect: float                # NIE + NDE
    nie_ci_lo: float
    nie_ci_hi: float
    nde_ci_lo: float
    nde_ci_hi: float
    nie_excludes_zero: bool
    method: str = "baron_kenny_1986_paired_pairs_bootstrap"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _baron_kenny_point(
    y: np.ndarray, M: np.ndarray, X: np.ndarray
) -> tuple[float, float]:
    """Point estimates of NIE and NDE under Baron-Kenny / VW 2015.

    Two-equation parametric model:
      M_{i,t} = α + a · X_{i,t} + ε_M
      y_{i,t} = β + b · M_{i,t} + c · X_{i,t} + ε_y

    NIE = a · b (indirect effect through M).
    NDE = c   (direct effect of X holding M constant).

    For multi-dim M, we project M onto its PC1 (per design.md §5.4) so a
    and b are scalars. For multi-dim X, we use the OLS-fit reduced-form
    where X-vector enters both equations linearly.
    """
    n = len(y)
    # PC1 collapse the mediator block
    if M.ndim == 1:
        M_scalar = M
    else:
        _, M_scalar = pc1_collapse(M)
    # Regress M_scalar on X (with intercept)
    X_aug = np.column_stack([np.ones(n), X])
    beta_M, *_ = np.linalg.lstsq(X_aug, M_scalar, rcond=None)
    a = float(beta_M[1:].sum())  # crude scalar X-on-M effect (sum over X-dims)
    # Regress y on (M_scalar, X) with intercept
    XM_aug = np.column_stack([np.ones(n), M_scalar, X])
    beta_y, *_ = np.linalg.lstsq(XM_aug, y, rcond=None)
    b = float(beta_y[1])           # M-on-y effect
    c = float(beta_y[2:].sum())    # crude scalar X-on-y direct effect (sum over X-dims)
    return a * b, c


def baron_kenny_nie_nde(
    y: np.ndarray,
    M: np.ndarray,
    X: np.ndarray,
    *,
    n_replicates: int = _DEFAULT_N_REPLICATES,
    block_length: float = _DEFAULT_BLOCK_LENGTH,
    alpha: float = 0.05,
    rng: np.random.Generator | None = None,
) -> MediationDecomposition:
    """Descriptive NIE + NDE with paired-pairs bootstrap CI."""
    if rng is None:
        rng = np.random.default_rng()
    n = len(y)
    nie_point, nde_point = _baron_kenny_point(y, M, X)

    nie_boot, nde_boot = [], []
    for _ in range(n_replicates):
        idx = stationary_bootstrap_indices(n=n, block_length=block_length, rng=rng)
        try:
            n_b, d_b = _baron_kenny_point(y[idx], M[idx], X[idx])
            if np.isfinite(n_b) and np.isfinite(d_b):
                nie_boot.append(n_b)
                nde_boot.append(d_b)
        except (np.linalg.LinAlgError, ValueError):
            continue

    if len(nie_boot) < 10:
        return MediationDecomposition(
            nie=nie_point, nde=nde_point, total_effect=nie_point + nde_point,
            nie_ci_lo=float("nan"), nie_ci_hi=float("nan"),
            nde_ci_lo=float("nan"), nde_ci_hi=float("nan"),
            nie_excludes_zero=False,
        )
    nie_arr = np.asarray(nie_boot)
    nde_arr = np.asarray(nde_boot)
    nie_lo = float(np.quantile(nie_arr, alpha / 2))
    nie_hi = float(np.quantile(nie_arr, 1 - alpha / 2))
    nde_lo = float(np.quantile(nde_arr, alpha / 2))
    nde_hi = float(np.quantile(nde_arr, 1 - alpha / 2))
    return MediationDecomposition(
        nie=nie_point, nde=nde_point, total_effect=nie_point + nde_point,
        nie_ci_lo=nie_lo, nie_ci_hi=nie_hi,
        nde_ci_lo=nde_lo, nde_ci_hi=nde_hi,
        nie_excludes_zero=(nie_lo > 0.0 or nie_hi < 0.0),
    )


__all__ = [
    "EValueResult",
    "MediationDecomposition",
    "PC1CollapseResult",
    "PartialR2BootstrapCI",
    "baron_kenny_nie_nde",
    "e_value",
    "paired_pairs_partial_r2_ci",
    "partial_r2_increment",
    "pc1_collapse",
]
