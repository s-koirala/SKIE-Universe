"""Bayesian Online Changepoint Detection (BOCD) primitive — Adams-MacKay 2007.

Per ADR-0018 §D-3, BOCD operating on rolling MPPM(ρ=1) paths is the
project-canonical strategy-decay detector. The algorithm maintains an exact
recursive posterior over the run-length r_t (elapsed time since the most recent
changepoint), and a hazard function H(τ) parameterises the changepoint prior.

Primary references:
- Adams, R. P., & MacKay, D. J. C. (2007). "Bayesian Online Changepoint
  Detection." [arXiv:0710.3742](https://arxiv.org/abs/0710.3742). Algorithm 1
  (run-length recursion); constant-hazard prior; Gaussian observation model
  with normal-inverse-gamma conjugate prior and Student-t predictive; well-log
  dataset posterior visualization. Exact section + equation pins deferred to
  `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY` pending primary-PDF access.
- Rabiner, L. R. (1989). "A Tutorial on Hidden Markov Models and Selected
  Applications in Speech Recognition." *Proc. IEEE* 77(2):257-286.
  [DOI 10.1109/5.18626](https://doi.org/10.1109/5.18626). §III.A forward
  recursion is the structural precursor to the BOCD forward pass.
- Murphy, K. P. (2007). "Conjugate Bayesian analysis of the Gaussian
  distribution." *UBC technical note* (Tier-2 official documentation; not
  peer-reviewed). Normal-inverse-gamma posterior update formulas used in the
  Student-t predictive computation; exact equation pins deferred to
  `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`.

Implementation per `P1-BOCD-DECAY-DETECTOR-PRIMITIVE` (mandated by ADR-0018
§D-3). Defaults `hazard_rate=1/250` (project-operational default per ADR-0018
§D-3; empirical calibration pending `P1-BOCD-HAZARD-RATE-EMPIRICAL`),
`window=60`, `threshold=0.5` per ADR-0018 D-3.

Numerical stability: the run-length posterior is propagated in log-space; the
growth + changepoint updates use `scipy.special.logsumexp` to avoid underflow
on long sequences (the unnormalized joint P(r_t, x_{1:t}) decays geometrically
with t for the changepoint mass).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt
from scipy.special import logsumexp
from scipy.stats import t as student_t

__all__ = [
    "BOCDState",
    "bocd_run",
    "bocd_update",
    "changepoint_posterior",
    "detect_decay",
    "init_bocd",
]


@dataclass
class BOCDState:
    """Mutable state for the Adams-MacKay 2007 run-length recursion.

    The state tracks the unnormalized log-joint P(r_t = r, x_{1:t}) for
    r ∈ {0, 1, ..., t}; the normalized posterior P(r_t = r | x_{1:t}) is
    recovered by subtracting the logsumexp over the run-length axis.

    Per Adams-MacKay 2007 (Gaussian observation model; pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`) + Murphy 2007 (NIG posterior update; pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`), the per-run-length
    normal-inverse-gamma sufficient statistics evolve as:
        mu_r    = (kappa_0 * mu_0 + sum_x) / (kappa_0 + n_r)
        kappa_r = kappa_0 + n_r
        alpha_r = alpha_0 + n_r / 2
        beta_r  = beta_0 + 0.5 * sum((x_i - x_bar)^2) + (n_r * kappa_0 / (2 * kappa_r)) * (x_bar - mu_0)^2

    For one-step incremental updates we equivalently track per-run-length
    (mu, kappa, alpha, beta) arrays grown by one element per `bocd_update`.

    Attributes:
        run_length_log_probs: 1-D array length (t+1) of unnormalized
            log P(r_t = r, x_{1:t}). Element 0 corresponds to r=0
            (changepoint at the current step).
        hyperparameters: Dict with keys mu_0, kappa_0, alpha_0, beta_0
            (the constant prior parameters), and arrays mu, kappa, alpha,
            beta of length (t+1) tracking per-run-length posteriors.
        hazard_rate: Constant hazard H(τ) = 1/λ per Adams-MacKay 2007 (constant-hazard prior; pin deferred to `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`)
            (pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`). Default 1/250 per ADR-0018 D-3.
        n_observed: Number of observations consumed (= t).
        observed: List of consumed observations (used for diagnostic /
            audit reproducibility; appendable).
    """

    run_length_log_probs: np.ndarray
    hyperparameters: dict
    hazard_rate: float
    n_observed: int = 0
    observed: list[float] = field(default_factory=list)


def init_bocd(
    hazard_rate: float = 1.0 / 250.0,
    mu_0: float = 0.0,
    kappa_0: float = 1.0,
    alpha_0: float = 1.0,
    beta_0: float = 1.0,
) -> BOCDState:
    """Initialize a BOCDState per Adams-MacKay 2007 (Gaussian observation model; pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`) priors.

    The initial run-length posterior is P(r_0 = 0) = 1 (the segment begins
    at t=0 by convention; equivalently, a changepoint at t=0).

    Args:
        hazard_rate: Constant hazard H(τ) = 1/λ for the exponential prior
            on segment lengths per Adams-MacKay 2007 (constant-hazard prior; pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`). Default
            1/250 per ADR-0018 D-3 (project-operational default per ADR-0018 §D-3 (empirical calibration pending `P1-BOCD-HAZARD-RATE-EMPIRICAL`)
            in trading sessions).
        mu_0: Normal-inverse-gamma prior mean. Default 0.0 (weak).
        kappa_0: Normal-inverse-gamma prior precision-of-mean. Default 1.0
            (weak; one pseudo-observation of mu_0).
        alpha_0: Normal-inverse-gamma prior shape. Default 1.0 (weak;
            corresponds to two pseudo-observations of beta_0).
        beta_0: Normal-inverse-gamma prior scale. Default 1.0 (weak).

    Returns:
        BOCDState with run_length_log_probs = [0.0] (i.e., log P(r=0) = 0
        unnormalized; the single-element posterior is degenerate at r=0).

    Raises:
        ValueError: if any hyperparameter is non-positive (kappa_0, alpha_0,
            beta_0 must all be > 0 for a proper normal-inverse-gamma), or
            hazard_rate not in (0, 1].
    """
    if not (0.0 < hazard_rate <= 1.0):
        raise ValueError(
            f"hazard_rate must be in (0, 1], got {hazard_rate}. "
            "Per Adams-MacKay 2007 (constant-hazard prior; pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`), H(τ) = 1/λ is a probability."
        )
    if kappa_0 <= 0.0 or alpha_0 <= 0.0 or beta_0 <= 0.0:
        raise ValueError(
            f"kappa_0, alpha_0, beta_0 must be strictly positive; "
            f"got kappa_0={kappa_0}, alpha_0={alpha_0}, beta_0={beta_0}."
        )

    return BOCDState(
        run_length_log_probs=np.array([0.0], dtype=float),
        hyperparameters={
            "mu_0": float(mu_0),
            "kappa_0": float(kappa_0),
            "alpha_0": float(alpha_0),
            "beta_0": float(beta_0),
            "mu": np.array([mu_0], dtype=float),
            "kappa": np.array([kappa_0], dtype=float),
            "alpha": np.array([alpha_0], dtype=float),
            "beta": np.array([beta_0], dtype=float),
        },
        hazard_rate=float(hazard_rate),
        n_observed=0,
        observed=[],
    )


def _student_t_log_predictive(
    x: float, mu: np.ndarray, kappa: np.ndarray, alpha: np.ndarray, beta: np.ndarray
) -> np.ndarray:
    """Vectorized Student-t log-predictive per Murphy 2007 (Student-t predictive; pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`).

    The posterior predictive for x under a normal-inverse-gamma prior with
    sufficient statistics (mu, kappa, alpha, beta) is:
        x ~ t_{2*alpha}(mu, beta * (kappa + 1) / (alpha * kappa))
    i.e., Student-t with 2*alpha degrees of freedom, location mu, and scale
    sqrt(beta * (kappa + 1) / (alpha * kappa)).

    Args:
        x: Scalar observation.
        mu, kappa, alpha, beta: Length-(R) arrays of per-run-length NIG
            sufficient statistics.

    Returns:
        Length-(R) array of log-predictive densities.
    """
    df = 2.0 * alpha
    scale = np.sqrt(beta * (kappa + 1.0) / (alpha * kappa))
    return student_t.logpdf(x, df=df, loc=mu, scale=scale)


def bocd_update(state: BOCDState, x_t: float) -> BOCDState:
    """One step of the Adams-MacKay 2007 Algorithm 1 recursion.

    Implements (in log-space):
        log P(r_t = r_{t-1}+1, x_{1:t}) = log P(r_{t-1}, x_{1:t-1})
                                          + log π(x_t | r_{t-1}, ...)
                                          + log(1 - H)
        log P(r_t = 0, x_{1:t}) = logsumexp_{r_{t-1}} [ log P(r_{t-1}, x_{1:t-1})
                                                       + log π(x_t | r_{t-1}, ...)
                                                       + log H ]

    Args:
        state: Input BOCDState.
        x_t: Next observation.

    Returns:
        New BOCDState (the input is not mutated). The returned state has
        `run_length_log_probs` of length (t+2) where t = state.n_observed
        beforehand.
    """
    x = float(x_t)
    hp = state.hyperparameters
    mu = hp["mu"]
    kappa = hp["kappa"]
    alpha = hp["alpha"]
    beta = hp["beta"]
    log_h = np.log(state.hazard_rate)
    with np.errstate(divide="ignore"):
        log_1mh = np.log1p(-state.hazard_rate)

    log_pred = _student_t_log_predictive(x, mu, kappa, alpha, beta)

    log_joint_prev = state.run_length_log_probs

    log_growth = log_joint_prev + log_pred + log_1mh
    log_cp = logsumexp(log_joint_prev + log_pred + log_h)

    new_log_joint = np.concatenate(([log_cp], log_growth))

    mu_0 = hp["mu_0"]
    kappa_0 = hp["kappa_0"]
    alpha_0 = hp["alpha_0"]
    beta_0 = hp["beta_0"]

    new_kappa_growth = kappa + 1.0
    new_mu_growth = (kappa * mu + x) / new_kappa_growth
    new_alpha_growth = alpha + 0.5
    new_beta_growth = beta + (kappa * (x - mu) ** 2) / (2.0 * new_kappa_growth)

    new_mu = np.concatenate(([mu_0], new_mu_growth))
    new_kappa = np.concatenate(([kappa_0], new_kappa_growth))
    new_alpha = np.concatenate(([alpha_0], new_alpha_growth))
    new_beta = np.concatenate(([beta_0], new_beta_growth))

    new_observed = list(state.observed)
    new_observed.append(x)

    return BOCDState(
        run_length_log_probs=new_log_joint,
        hyperparameters={
            "mu_0": mu_0,
            "kappa_0": kappa_0,
            "alpha_0": alpha_0,
            "beta_0": beta_0,
            "mu": new_mu,
            "kappa": new_kappa,
            "alpha": new_alpha,
            "beta": new_beta,
        },
        hazard_rate=state.hazard_rate,
        n_observed=state.n_observed + 1,
        observed=new_observed,
    )


def bocd_run(
    observations: npt.ArrayLike,
    hazard_rate: float = 1.0 / 250.0,
    *,
    mu_0: float = 0.0,
    kappa_0: float = 1.0,
    alpha_0: float = 1.0,
    beta_0: float = 1.0,
) -> tuple[np.ndarray, BOCDState]:
    """Full pass over a sequence; returns (rl_posterior_matrix, final_state).

    Args:
        observations: 1-D array-like of observations.
        hazard_rate: Constant hazard H(τ) = 1/λ. Default 1/250.
        mu_0, kappa_0, alpha_0, beta_0: NIG prior hyperparameters. Defaults
            are weak per Adams-MacKay 2007 (Gaussian observation model; pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`).

    Returns:
        Tuple (rl_posterior, final_state):
        - rl_posterior: shape (T, T+1) lower-triangular array; entry [t, r]
          is the normalized posterior P(r_t = r | x_{1:t+1}). Entries
          [t, r > t+1] are zero.
        - final_state: BOCDState after consuming all T observations.
    """
    obs = np.asarray(observations, dtype=float).ravel()
    T = obs.size
    if T == 0:
        state = init_bocd(
            hazard_rate=hazard_rate,
            mu_0=mu_0,
            kappa_0=kappa_0,
            alpha_0=alpha_0,
            beta_0=beta_0,
        )
        return np.empty((0, 1), dtype=float), state

    state = init_bocd(
        hazard_rate=hazard_rate,
        mu_0=mu_0,
        kappa_0=kappa_0,
        alpha_0=alpha_0,
        beta_0=beta_0,
    )
    rl_posterior = np.zeros((T, T + 1), dtype=float)

    for t in range(T):
        state = bocd_update(state, obs[t])
        log_joint = state.run_length_log_probs
        log_norm = logsumexp(log_joint)
        posterior_t = np.exp(log_joint - log_norm)
        rl_posterior[t, : posterior_t.size] = posterior_t

    return rl_posterior, state


def changepoint_posterior(
    rl_posterior: np.ndarray, window: int
) -> np.ndarray:
    """At each time t, compute P(changepoint within last window/2 obs).

    Defined as sum over r_t < window/2 of P(r_t = r | x_{1:t}). A small
    run-length means a recent changepoint.

    Note on the start-of-series burn-in: for t < window/2 the run-length
    cannot exceed t, so the half-window sum is trivially close to 1
    regardless of any actual changepoint (a Bayesian degeneracy, NOT a
    detected event — Adams-MacKay 2007 (Gaussian observation model; pin deferred per `P1-BOCD-CITE-SECTION-NUMBERS-VERIFY`) initializes with degenerate
    P(r_0 = 0) = 1). Per ADR-0018 §D-3 the operator convention is to
    treat the first `window/2` entries as warmup and zero them; this
    avoids false positives at t=0 driven solely by the prior, not by data.

    Args:
        rl_posterior: Shape (T, T+1) lower-triangular posterior matrix
            from `bocd_run`.
        window: Lookback window in observations (project default 60 per
            ADR-0018 D-3). The summation is over r_t < window/2.

    Returns:
        Length-T array of P(recent changepoint). First `window/2` entries
        are zeroed as warmup per the burn-in convention above.

    Raises:
        ValueError: if window < 2 (window/2 must be ≥ 1 to define a sum).
    """
    if window < 2:
        raise ValueError(f"window must be ≥ 2; got {window}.")
    if rl_posterior.ndim != 2:
        raise ValueError(
            f"rl_posterior must be 2-D; got shape {rl_posterior.shape}."
        )

    T = rl_posterior.shape[0]
    half_window = window // 2
    out = np.zeros(T, dtype=float)
    if T == 0:
        return out

    upper = min(half_window, rl_posterior.shape[1])
    out[:] = rl_posterior[:, :upper].sum(axis=1)
    burn_in = min(half_window, T)
    out[:burn_in] = 0.0
    return out


def detect_decay(
    observations: npt.ArrayLike,
    hazard_rate: float = 1.0 / 250.0,
    window: int = 60,
    threshold: float = 0.5,
    *,
    mu_0: float = 0.0,
    kappa_0: float = 1.0,
    alpha_0: float = 1.0,
    beta_0: float = 1.0,
) -> dict:
    """Full BOCD decay-detection pipeline per ADR-0018 D-3.

    Runs BOCD over the input series, computes the recent-changepoint
    posterior at every time step, and flags the first index at which the
    posterior exceeds `threshold`.

    Args:
        observations: 1-D array-like (e.g., rolling MPPM(ρ=1) returns).
        hazard_rate: Constant hazard. Default 1/250 per ADR-0018 D-3.
        window: Lookback window (default 60 per ADR-0018 D-3).
        threshold: Detection threshold on P(recent changepoint). Default
            0.5 per ADR-0018 D-3.
        mu_0, kappa_0, alpha_0, beta_0: NIG prior hyperparameters.

    Returns:
        Dict with keys:
        - decay_detected: bool — True if any posterior_series[t] > threshold.
        - detection_index: int | None — first index where the threshold is
            crossed, or None if not detected.
        - max_posterior: float — max of the posterior series.
        - posterior_series: np.ndarray — length-T recent-changepoint
            posterior.

    Raises:
        ValueError: if threshold not in (0, 1).
    """
    if not (0.0 < threshold < 1.0):
        raise ValueError(f"threshold must be in (0, 1); got {threshold}.")

    rl_posterior, _ = bocd_run(
        observations,
        hazard_rate=hazard_rate,
        mu_0=mu_0,
        kappa_0=kappa_0,
        alpha_0=alpha_0,
        beta_0=beta_0,
    )
    posterior_series = changepoint_posterior(rl_posterior, window=window)

    if posterior_series.size == 0:
        return {
            "decay_detected": False,
            "detection_index": None,
            "max_posterior": 0.0,
            "posterior_series": posterior_series,
        }

    above = np.where(posterior_series > threshold)[0]
    if above.size == 0:
        return {
            "decay_detected": False,
            "detection_index": None,
            "max_posterior": float(posterior_series.max()),
            "posterior_series": posterior_series,
        }
    return {
        "decay_detected": True,
        "detection_index": int(above[0]),
        "max_posterior": float(posterior_series.max()),
        "posterior_series": posterior_series,
    }
