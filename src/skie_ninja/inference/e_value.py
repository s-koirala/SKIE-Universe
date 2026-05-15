"""E-value sensitivity analysis primitive per VanderWeele-Ding 2017.

Closes BLOCKING-BEFORE-NEXT-NEW-PRE-REG-CAUSAL-MECHANISM-ANNOTATION precondition
`P1-E-VALUE-FOR-FUTURES-PRIMITIVE-IMPL` per [ADR-0022](../../../docs/decisions/ADR-0022-causal-mechanism-vs-correlation-only-annotation.md) §3.

The E-value is the minimum strength of association (on the risk-ratio scale) that an
unmeasured confounder would need to have with both the treatment AND the outcome in
order to fully explain away the observed treatment-outcome association.

Anchored on [VanderWeele, T. J.; Ding, P. (2017). "Sensitivity Analysis in Observational
Research: Introducing the E-Value." *Annals of Internal Medicine* 167(4):268-274.
DOI 10.7326/M16-2607](https://doi.org/10.7326/M16-2607). The E-value formula for an
observed risk ratio (RR) > 1:

    E_value(RR) = RR + sqrt(RR * (RR - 1))

For RR < 1, the symmetric form applies:

    E_value(RR) = (1/RR) + sqrt((1/RR) * (1/RR - 1))

For CI bound (the more conservative "could-this-be-explained-away" quantity):
- For RR estimate > 1 with CI lower bound > 1: use ``E_value(CI_lower)``.
- For RR estimate < 1 with CI upper bound < 1: use ``E_value(1/CI_upper)``.
- If the CI crosses 1, ``E_value(CI)`` = 1 (the null is within the CI; no unmeasured
  confounder is required to explain the observation).

For continuous outcomes (e.g., standardized mean differences, log-wealth metrics like
MPPM(ρ=1)), VanderWeele-Ding 2017 §"Approximate E-value" provides an approximation via
the standardized-mean-difference-to-RR conversion:

    approx_RR(d) = exp(0.91 * d)

where ``d`` is the standardized mean difference (Cohen's d-equivalent). This is the
appropriate primitive for H062's MPPM(ρ=1) inference (per ADR-0022 §3) and for any
hypothesis with continuous outcome whose effect size is reported in standardized units.

Implementation philosophy: this module provides the canonical E-value formula on the
RR scale + the SMD-to-RR approximation; project-side decision of HOW to map a particular
inferential CI (LW2008 Sharpe-differential CI, stationary-bootstrap MPPM CI, etc.) to
an RR-equivalent or SMD-equivalent is per-hypothesis design.md §1.3 and is NOT
hard-coded here. Callers pass either an RR with CI or an SMD with CI.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class EValueResult:
    """Result of an E-value computation.

    Attributes
    ----------
    e_value_point : float
        E-value at the point estimate.
    e_value_ci : float
        E-value at the CI bound; ``1.0`` if the CI crosses the null.
    rr_point : float
        Risk-ratio at the point estimate (1.0 = null).
    rr_ci_bound : float
        Risk-ratio at the CI bound used for ``e_value_ci``.
    direction : str
        ``"protective"`` if RR < 1 (RR estimated below null);
        ``"causative"`` if RR > 1;
        ``"null"`` if RR == 1.
    ci_crosses_null : bool
        True if the CI contains 1.0 (the null RR).
    """

    e_value_point: float
    e_value_ci: float
    rr_point: float
    rr_ci_bound: float
    direction: str
    ci_crosses_null: bool


def _e_value_above_one(rr: float) -> float:
    """E-value formula for RR > 1; per VanderWeele-Ding 2017 eq. 1."""
    if rr <= 1.0:
        return 1.0
    return rr + math.sqrt(rr * (rr - 1.0))


def e_value_from_rr(
    rr_point: float,
    rr_ci_lower: float,
    rr_ci_upper: float,
) -> EValueResult:
    """Compute E-value from a risk-ratio with two-sided CI.

    Parameters
    ----------
    rr_point : float
        Point estimate of the risk ratio. Must be > 0.
    rr_ci_lower : float
        Lower bound of the two-sided CI.
    rr_ci_upper : float
        Upper bound of the two-sided CI.

    Returns
    -------
    EValueResult

    Notes
    -----
    Per VanderWeele-Ding 2017:
    - For ``rr_point > 1`` and ``rr_ci_lower > 1``: ``e_value_ci = E_value(rr_ci_lower)``.
    - For ``rr_point < 1`` and ``rr_ci_upper < 1``: convert to symmetric form via
      ``E_value(1 / rr_ci_upper)``.
    - If the CI contains 1.0: ``e_value_ci = 1.0`` and ``ci_crosses_null = True``.
    """
    if rr_point <= 0.0:
        raise ValueError(f"rr_point must be > 0; got {rr_point}")
    if rr_ci_lower <= 0.0 or rr_ci_upper <= 0.0:
        raise ValueError(
            f"rr_ci_lower and rr_ci_upper must be > 0; got ({rr_ci_lower}, {rr_ci_upper})"
        )
    if rr_ci_lower > rr_ci_upper:
        raise ValueError(
            f"rr_ci_lower must be <= rr_ci_upper; got ({rr_ci_lower}, {rr_ci_upper})"
        )

    ci_crosses_null = rr_ci_lower <= 1.0 <= rr_ci_upper

    if rr_point > 1.0:
        direction = "causative"
        rr_for_point = rr_point
        rr_for_ci_bound = rr_ci_lower if not ci_crosses_null else 1.0
    elif rr_point < 1.0:
        direction = "protective"
        rr_for_point = 1.0 / rr_point
        rr_for_ci_bound = 1.0 / rr_ci_upper if not ci_crosses_null else 1.0
    else:
        direction = "null"
        rr_for_point = 1.0
        rr_for_ci_bound = 1.0

    e_point = _e_value_above_one(rr_for_point)
    e_ci = 1.0 if ci_crosses_null else _e_value_above_one(rr_for_ci_bound)

    return EValueResult(
        e_value_point=float(e_point),
        e_value_ci=float(e_ci),
        rr_point=float(rr_point),
        rr_ci_bound=float(rr_for_ci_bound if not ci_crosses_null else 1.0),
        direction=direction,
        ci_crosses_null=bool(ci_crosses_null),
    )


def e_value_from_standardized_mean_difference(
    d_point: float,
    d_ci_lower: float,
    d_ci_upper: float,
) -> EValueResult:
    """Compute E-value from a standardized mean difference (Cohen's d-equivalent)
    with two-sided CI via the VanderWeele-Ding 2017 SMD-to-RR approximation.

    The approximation per VanderWeele-Ding 2017 §"Approximate E-value":

        RR(d) ≈ exp(0.91 * d)

    The 0.91 multiplier comes from the relationship between standardized mean
    differences and approximate RR under typical-outcome-distribution assumptions
    per Chinn 2000 + Hasselblad-Hedges 1995.

    Parameters
    ----------
    d_point : float
        Point estimate of the standardized mean difference.
    d_ci_lower : float
    d_ci_upper : float

    Returns
    -------
    EValueResult
        E-values computed on the RR-equivalent scale.

    Notes
    -----
    For trading-strategy metrics like MPPM(ρ=1) (annualized log-wealth) or
    Sharpe-differential, the appropriate SMD-equivalent is the metric value divided
    by its sample standard deviation. The caller is responsible for converting the
    metric to a standardized scale before calling this function.
    """
    rr_point = math.exp(0.91 * d_point)
    rr_ci_lower = math.exp(0.91 * d_ci_lower)
    rr_ci_upper = math.exp(0.91 * d_ci_upper)
    return e_value_from_rr(rr_point, rr_ci_lower, rr_ci_upper)


__all__ = [
    "EValueResult",
    "e_value_from_rr",
    "e_value_from_standardized_mean_difference",
]
