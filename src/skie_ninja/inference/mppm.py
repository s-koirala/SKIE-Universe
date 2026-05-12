"""Manipulation-Proof Performance Measure (MPPM) — Goetzmann-Ingersoll-Spiegel-Welch 2007.

Per ADR-0018, MPPM(rho=1) is the project-canonical fitness function used in
inner-CV hyperparameter selection, replacing Sharpe (which is provably gameable
via leverage-conditioning and option-overlay structures per GISW 2007 §III).

Theoretical foundation:

    Theta_hat_rho = ( 1 / ((1 - rho) * Delta_t) )
                  * ln( (1/(T+1)) * sum_{t=0..T} ((1+r_t)/(1+r_f_t))^(1-rho) )

for rho != 1. At rho = 1 the (1-rho) in the denominator and the (1-rho)-power
inside the log create a 0/0 singularity; L'Hôpital's rule yields the limit

    Theta_hat_1 = (1 / Delta_t) * mean( ln((1+r_t) / (1+r_f_t)) )

which is the per-period mean log excess-return scaled to per-year units. This
is the Kelly-Breiman log-growth rate per Kelly 1956 *Bell System Tech J*
35(4):917-926 and Breiman 1961 *Proc 4th Berkeley Symp* 1:65-78. MPPM at rho=1
is exactly the long-run capital-growth rate of the strategy and is invariant
under within-sample manipulation by construction (GISW 2007 Theorem 1).

The score is "manipulation-proof" in the GISW 2007 sense: for any non-decreasing
concave utility consistent with the CRRA(rho) preference, an investor cannot
score-inflate by post-hoc leverage scaling, time-period selection, derivative-
overlay packaging, or any other strategy adopted without prior information. This
is the strongest such guarantee in the published performance-measurement
literature.

References:

- Goetzmann, W.; Ingersoll, J.; Spiegel, M. & Welch, I. 2007. "Portfolio
  Performance Manipulation and Manipulation-Proof Performance Measures."
  Review of Financial Studies 20(5):1503-1546. DOI 10.1093/rfs/hhm025.
- Kelly, J. L. 1956. "A New Interpretation of Information Rate." Bell System
  Technical Journal 35(4):917-926. DOI 10.1002/j.1538-7305.1956.tb03809.x.
- Breiman, L. 1961. "Optimal Gambling Systems for Favorable Games." Proc 4th
  Berkeley Symposium on Mathematical Statistics and Probability 1:65-78.

Implementation per `P1-MPPM-RHO-1-FITNESS-PRIMITIVE` (mandated by ADR-0018 as
primary fitness function for inner-CV hyperparameter selection across all
hypotheses from H056 forward).

Verification-gap (non-blocking, tracked under `P1-MPPM-GISW-THEOREM-1-PIN-VERIFY`):
the exact GISW 2007 Theorem 1 normalization (1/(T+1) summed t=0..T vs 1/T
summed t=1..T) could not be confirmed from the publisher PDF or SSRN copy via
WebFetch during the R1 audit; the implementation uses 1/(T+1) summed t=0..T
which matches the ADR-0018 §Context restatement. The L'Hôpital rho=1 limit
reducing to mean log-excess-return is invariant to either normalization
convention up to an O(1/T) finite-sample correction. Independent primary-PDF
verification deferred to next opportunity.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    politis_white_block_length,
    stationary_bootstrap_indices,
)

__all__ = [
    "MPPMResult",
    "mppm",
    "mppm_rho_1",
    "mppm_with_ci",
]

# Threshold for switching between general (1-rho)-power form and the L'Hôpital
# limit at rho=1. At |rho - 1| <= 1e-9 the general form's 1/(1-rho) prefactor
# explodes numerically while the (1-rho)-power inside the log collapses toward
# 1; the limit form is exact and numerically stable. The boundary is inclusive
# so any caller passing exactly eps = 1e-9 routes through the stable path.
_RHO_ONE_TOL = 1e-9


@dataclass(frozen=True)
class MPPMResult:
    """Result of an MPPM computation, optionally with bootstrap CI.

    Attributes:
        theta_hat: The MPPM point estimate (per-year units when Delta_t is in
            years, e.g., 1/252 for daily).
        rho: Risk-aversion parameter; ADR-0018 D-1 mandates rho=1 (log utility,
            Kelly-Breiman) as the project default.
        delta_t: Time-step in years (e.g., 1/252 daily; 1/(252*390) 1-min RTH).
        n_obs: Number of return observations (T+1 in GISW notation).
        manipulation_proof: Always True; the GISW 2007 Theorem 1 score is
            manipulation-proof by construction for all rho > 0.
        method: "gisw_2007_rho_1_lhopital" when |rho - 1| <= 1e-9, else
            "gisw_2007_general".
        ci_low / ci_high: Stationary-bootstrap percentile CI bounds (None if
            CI not requested).
        confidence: Two-sided CI coverage (None if no CI).
        n_bootstrap: Number of bootstrap replicates (None if no CI).
        block_length: Expected stationary-bootstrap block length (None if no CI).
        excludes_zero: True iff (ci_low > 0) or (ci_high < 0); None if no CI.
    """

    theta_hat: float
    rho: float
    delta_t: float
    n_obs: int
    manipulation_proof: bool
    method: str
    ci_low: float | None = None
    ci_high: float | None = None
    confidence: float | None = None
    n_bootstrap: int | None = None
    block_length: float | None = None
    excludes_zero: bool | None = None


def _as_returns(returns: npt.ArrayLike) -> np.ndarray:
    r = np.asarray(returns, dtype=float).ravel()
    if r.size == 0:
        raise ValueError("returns must be non-empty.")
    if not np.all(np.isfinite(r)):
        raise ValueError("returns contains non-finite values (NaN or inf).")
    # GISW 2007 requires (1 + r_t) > 0 for the log/power to be defined;
    # r_t <= -1 means total loss in one period and is operationally a
    # ruin event that should be flagged rather than silently transformed.
    if np.any(r <= -1.0):
        bad = int(np.argmin(r))
        raise ValueError(
            f"returns[{bad}] = {r[bad]:.6g} <= -1.0; "
            "MPPM requires (1 + r_t) > 0 (no total-loss bars)."
        )
    return r


def _as_risk_free(
    risk_free: npt.ArrayLike | float, n: int
) -> np.ndarray:
    if np.isscalar(risk_free):
        rf = np.full(n, float(risk_free), dtype=float)
    else:
        rf = np.asarray(risk_free, dtype=float).ravel()
        if rf.size != n:
            raise ValueError(
                f"risk_free length {rf.size} does not match returns length {n}."
            )
    if not np.all(np.isfinite(rf)):
        raise ValueError("risk_free contains non-finite values.")
    if np.any(rf <= -1.0):
        bad = int(np.argmin(rf))
        raise ValueError(
            f"risk_free[{bad}] = {rf[bad]:.6g} <= -1.0; "
            "MPPM requires (1 + r_f_t) > 0."
        )
    return rf


def mppm(
    returns: npt.ArrayLike,
    rho: float,
    risk_free: npt.ArrayLike | float = 0.0,
    delta_t: float = 1.0 / 252.0,
) -> float:
    """General-rho MPPM per GISW 2007 Theorem 1.

    Computes

        Theta_hat_rho = (1 / ((1-rho) * Delta_t))
                      * ln( mean_t ((1+r_t)/(1+r_f_t))^(1-rho) )

    numerically stably via log-sum-exp on (1-rho)*log((1+r_t)/(1+r_f_t)),
    avoiding under/overflow when rho * max(|log excess|) is large.

    Automatically switches to the L'Hôpital limit form

        Theta_hat_1 = (1 / Delta_t) * mean( log((1+r_t)/(1+r_f_t)) )

    when |rho - 1| <= 1e-9; this is the exact limit (Kelly 1956 log-growth).

    Args:
        returns: 1-D array of per-period strategy returns r_t. Each (1 + r_t)
            must be strictly positive (r_t > -1).
        rho: Risk-aversion parameter. Any real value; rho > 0 corresponds to
            risk-averse CRRA utility per GISW 2007 §II. ADR-0018 D-1 mandates
            rho=1 as the project default.
        risk_free: Per-period risk-free rate. Scalar (broadcast to all periods)
            or 1-D array of same length as returns. Defaults to 0.0 (excess
            return = raw return).
        delta_t: Time-step in years; controls the per-year scaling of theta_hat.
            Defaults to 1/252 (daily). Use 1/(252 * 390) for 1-min RTH bars.

    Returns:
        Float; the MPPM point estimate Theta_hat_rho in per-year units.

    Raises:
        ValueError: if returns is empty, contains non-finite values, contains
            any r_t <= -1, or if delta_t <= 0. Similar for risk_free.
    """
    r = _as_returns(returns)
    rf = _as_risk_free(risk_free, r.size)
    if delta_t <= 0.0:
        raise ValueError(f"delta_t must be > 0, got {delta_t}.")

    # Excess log-return per period: log((1+r_t)/(1+r_f_t)).
    log_excess = np.log1p(r) - np.log1p(rf)

    if abs(rho - 1.0) <= _RHO_ONE_TOL:
        return float(np.mean(log_excess) / delta_t)

    # General case: numerically stable log-mean-exp on (1-rho)*log_excess.
    # log( (1/T) sum_t exp(z_t) ) = max(z) + log( sum_t exp(z_t - max(z)) ) - log(T)
    z = (1.0 - rho) * log_excess
    z_max = float(np.max(z))
    log_sum = z_max + float(np.log(np.sum(np.exp(z - z_max))))
    log_mean = log_sum - float(np.log(z.size))
    return float(log_mean / ((1.0 - rho) * delta_t))


def mppm_rho_1(
    returns: npt.ArrayLike,
    risk_free: npt.ArrayLike | float = 0.0,
    delta_t: float = 1.0 / 252.0,
) -> float:
    """Convenience entry for rho=1 (project-canonical fitness per ADR-0018 D-1).

    Equivalent to `mppm(returns, rho=1.0, risk_free=risk_free, delta_t=delta_t)`
    but skips the rho-comparison branch and uses the closed-form log-growth
    expression directly.

    Args:
        returns: 1-D array of per-period strategy returns. Each (1 + r_t) > 0.
        risk_free: Per-period risk-free rate. Scalar or 1-D array.
        delta_t: Time-step in years. Defaults to 1/252 (daily).

    Returns:
        Float; the rho=1 MPPM in per-year units. This equals the Kelly-Breiman
        long-run log-growth rate of the strategy.
    """
    r = _as_returns(returns)
    rf = _as_risk_free(risk_free, r.size)
    if delta_t <= 0.0:
        raise ValueError(f"delta_t must be > 0, got {delta_t}.")
    return float(np.mean(np.log1p(r) - np.log1p(rf)) / delta_t)


def mppm_with_ci(
    returns: npt.ArrayLike,
    rho: float,
    risk_free: npt.ArrayLike | float = 0.0,
    delta_t: float = 1.0 / 252.0,
    n_bootstrap: int = 1000,
    rng_seed: int = 42,
    confidence: float = 0.95,
    block_length: float | None = None,
) -> MPPMResult:
    """MPPM with Politis-Romano 1994 stationary-bootstrap CI.

    Block length is auto-selected via Politis-White 2004 + Patton-Politis-White
    2009 correction on the log-excess-return series, unless `block_length` is
    supplied. The resampling jointly draws (r_t, r_f_t) tuples when risk_free
    is per-period so cross-arm dependence is preserved; if risk_free is scalar,
    only returns are resampled.

    Args:
        returns: 1-D array of per-period strategy returns r_t > -1.
        rho: Risk-aversion parameter. ADR-0018 D-1 mandates 1.0 as default.
        risk_free: Per-period risk-free rate. Scalar or 1-D array.
        delta_t: Time-step in years (default 1/252).
        n_bootstrap: Number of bootstrap replicates (default 1,000).
        rng_seed: Deterministic RNG seed (default 42).
        confidence: Two-sided coverage in (0, 1) (default 0.95).
        block_length: Optional explicit block length; auto-selected if None.

    Returns:
        MPPMResult with point estimate + CI bounds + `excludes_zero` flag +
        full provenance.

    Raises:
        ValueError: same as `mppm`, plus n_bootstrap < 1, confidence not in
            (0, 1), block_length < 1.
    """
    r = _as_returns(returns)
    rf = _as_risk_free(risk_free, r.size)
    if delta_t <= 0.0:
        raise ValueError(f"delta_t must be > 0, got {delta_t}.")
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}.")
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}.")
    n = r.size
    if n < 4:
        raise ValueError(
            f"mppm_with_ci requires n >= 4 for bootstrap-block selection, got {n}."
        )

    use_lhopital = abs(rho - 1.0) <= _RHO_ONE_TOL
    method = "gisw_2007_rho_1_lhopital" if use_lhopital else "gisw_2007_general"

    log_excess = np.log1p(r) - np.log1p(rf)

    if use_lhopital:
        point = float(np.mean(log_excess) / delta_t)
    else:
        z = (1.0 - rho) * log_excess
        z_max = float(np.max(z))
        log_sum = z_max + float(np.log(np.sum(np.exp(z - z_max))))
        log_mean = log_sum - float(np.log(z.size))
        point = float(log_mean / ((1.0 - rho) * delta_t))

    # Block-length selection on the log-excess series (the load-bearing
    # statistic for both rho=1 and general-rho paths).
    if block_length is None:
        sel: BlockLengthSelection = politis_white_block_length(
            log_excess, bootstrap_type="stationary"
        )
        bl = float(sel.block_length)
    else:
        if block_length < 1.0:
            raise ValueError(f"block_length must be >= 1, got {block_length}.")
        bl = float(block_length)

    rng = np.random.default_rng(rng_seed)
    boot = np.empty(n_bootstrap, dtype=float)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n, block_length=bl, rng=rng)
        le_b = log_excess[idx]
        if use_lhopital:
            boot[b] = float(np.mean(le_b) / delta_t)
        else:
            z = (1.0 - rho) * le_b
            z_max = float(np.max(z))
            log_sum = z_max + float(np.log(np.sum(np.exp(z - z_max))))
            log_mean = log_sum - float(np.log(z.size))
            boot[b] = float(log_mean / ((1.0 - rho) * delta_t))

    alpha = 1.0 - confidence
    lo = float(np.quantile(boot, alpha / 2.0))
    hi = float(np.quantile(boot, 1.0 - alpha / 2.0))

    return MPPMResult(
        theta_hat=point,
        rho=float(rho),
        delta_t=float(delta_t),
        n_obs=n,
        manipulation_proof=True,
        method=method,
        ci_low=lo,
        ci_high=hi,
        confidence=confidence,
        n_bootstrap=n_bootstrap,
        block_length=bl,
        excludes_zero=(lo > 0.0) or (hi < 0.0),
    )
