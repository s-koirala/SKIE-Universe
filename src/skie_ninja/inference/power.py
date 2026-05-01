"""Power-calibration solver for the project's Sharpe-ratio gating pipeline.

Implements [H053 design.md](../../../research/01_hypothesis_register/H053/design.md)
§11.2 prerequisite 19 (parametric `required_n` + MDE inverter for the
project's Sharpe-ratio gating tests) and writes the
`{run_id}_power_calibration.json` sidecar per design.md §9.

The H053 design.md §9 power block specifies the yaml form:

    power:
      alpha: 0.05
      target_power: 0.80
      n_obs_per_year: 252        # one obs per session (single instrument)
      n_obs_pooled_per_year: 504 # ES + NQ pooled
      expected_n_oos: ...        # filled at the start of `running` from §6 splitter
      s_min: ...                 # MDE-inverted from expected_n_oos
      ar1_rho_pilot: ...         # estimated on pilot window (option 3 pin: 0.0)
      excess_kurtosis_pilot: ... # estimated on pilot window (option 3 pin: 3.0)
      variance_formula: lo2002_hac_adjusted
      n_required: ...            # required_n(s_min, alpha, target_power, ...)

This module is the *parametric* counterpart to
`src/skie_ninja/inference/stats/sharpe_ci.py`: that module estimates Sharpe
variance from a return series (data-driven); this module computes the same
variance from pre-pinned distributional parameters (rho, gamma_3, gamma_4) to
solve the inverse problem (given a target effect size, what `n` is needed?).

**Citation provenance (literature-check pass, 2026-04-30; matches the
hedging pattern established by the project's Cycle-2 audit at
[src/skie_ninja/inference/stats/sharpe_ci.py](stats/sharpe_ci.py)):**

- The iid-Gaussian special case `Var_iid(S_hat) = (1 + S_hat^2/2)/T` is
  literal Lo 2002 §III (the iid asymptotic at γ_3=0, γ_4=3). Originally
  Jobson-Korkie 1981.
- The general-iid form with skewness γ_3 and full kurtosis γ_4
  `Var_iid(S_hat) = (1 - γ_3·S_hat + (γ_4 - 1)·S_hat^2/4)/T`
  is the **Mertens 2002 / Opdyke 2007 generalisation** of Lo 2002,
  not literal Lo 2002. The project's audited
  [opdyke2007_ci](stats/sharpe_ci.py) uses the same form with
  attribution to Mertens-Opdyke.
- The HAC inflation `Var_HAC = Var_iid · (1 + rho)/(1 - rho)` is the
  **AR(1) long-run-variance ratio** (Hamilton 1994 §10.3, eq. 10.3.6;
  the geometric-series limit `1 + 2·sum_{k>=1} rho^k = (1+rho)/(1-rho)`),
  NOT Lo 2002 Proposition 2 verbatim. Lo's Proposition 2 uses a
  finite-lag Newey-West HAC estimator with data-driven bandwidth
  `Var(S_hat) = eta(q)·(1 + S_hat^2/2)/T` where
  `eta(q) = 1 + 2·sum_{k=1}^{q-1} (1 − k/q)·rho_k`.
  The closed-form `(1+rho)/(1-rho)` is the asymptotic AR(1) limit of
  eta(q) under Bartlett-weighted truncation; the two forms are
  first-order equivalent under Gaussian iid AR(1) but not literally
  identical. This module's parametric-pin use case (option 3:
  rho is *pinned*, not *estimated*) is appropriate for the closed-form
  AR(1) limit; the data-driven Lo HAC estimator is implemented at
  [lo2002_prop2_eta_ci](stats/sharpe_ci.py).

**Convention note** on the kurtosis parameter. Lo 2002 §III + the
Mertens-Opdyke generalisation use *full* kurtosis γ_4 (4th standardized
central moment): for Gaussian γ_4 = 3, not 0. The H053 design.md §9
names its pinned parameter `excess_kurtosis_pilot` but assigns the value
`3.0` for its option-3 Gaussian pin — which is the *full* kurtosis,
not excess kurtosis. The H053 power_calibration_addendum_2026-04-30
contains an internal language inconsistency between table line 35 (which
pins `excess_kurtosis_pilot = 3.0`) and operational-consequence prose
elsewhere (which describes the same calibration as `kappa_excess = 0`).
This module follows the **full-kurtosis convention** (the `kurtosis`
parameter = gamma_4; H053 option-3 value `3.0` is passed as
`kurtosis=3.0`); the upstream pre-reg language inconsistency is tracked
under follow-up `P1-H053-KURTOSIS-CONVENTION-RECONCILE`.

References:
- Lo, A. W. (2002). "The Statistics of Sharpe Ratios."
  *Financial Analysts Journal* 58(4):36-52.
  [DOI 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453).
  §III eq. 4 (iid Gaussian) + Proposition 2 (data-driven HAC).
- Mertens, E. (2002). "Comments on Variance of the IID estimator in
  Lo (2002)." Working paper. (Generalisation to skewed / leptokurtic
  iid returns; reproduced in Opdyke 2007 §3.)
- Opdyke, J. D. (2007). "Comparing Sharpe ratios: So where are the
  p-values?" *J. Asset Management* 8:308–336.
  [DOI 10.1057/palgrave.jam.2250084](https://doi.org/10.1057/palgrave.jam.2250084).
- Hamilton, J. D. (1994). *Time Series Analysis*. Princeton.
  ISBN 978-0691042893. §10.3 eq. 10.3.6 (AR(1) long-run variance).
- Casella, G., Berger, R. L. (2002). *Statistical Inference* (2nd ed.).
  Duxbury. ISBN 978-0534243128. §8.3 (Power function for normal-test
  inversion; the standard one-sided power formula used in `required_n`).
- H053 design.md §9 (Stopping rule + power) + §11.2 prereq 19.
- H053 power_calibration_addendum_2026-04-30.md (option-3 election;
  Gaussian iid conservative prior pinning rho=0, gamma_4=3).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats as scipy_stats

# Asymptotic-normal critical-value helpers reused across solver + inverter.
# No magic numbers: alpha and target_power are caller-supplied; the only
# constant is the Gaussian-quantile inversion via scipy.


__all__ = [
    "PowerCalibration",
    "lo2002_sr_se",
    "lo2002_sr_variance",
    "mde",
    "required_n",
    "write_power_calibration_sidecar",
]


# ---------------------------------------------------------------------------
# Lo 2002 §III parametric variance formula
# ---------------------------------------------------------------------------


def lo2002_sr_variance(
    sr: float,
    n: int,
    *,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    ar1_rho: float = 0.0,
) -> float:
    """Lo 2002 §III HAC-adjusted Sharpe-ratio variance (parametric form).

    Composition matches Lo 2002 §III: the iid variance from equation 14 is
    multiplied by the HAC inflation factor under an AR(1) approximation per
    Proposition 2 (Bartlett spectral kernel at lag 1):

        Var_iid(Ŝ)  = (1 − γ_3 · Ŝ + (γ_4 − 1) · Ŝ² / 4) / T
        Var_HAC(Ŝ)  = Var_iid(Ŝ) · (1 + ρ) / (1 − ρ)

    For the H053 option-3 pin (`skewness=0, kurtosis=3, ar1_rho=0`):

        Var_HAC(Ŝ) = (1 + Ŝ²/2) / T

    which reduces to Lo 2002 equation 4 (the iid-Gaussian special case).

    Parameters
    ----------
    sr : float
        Sharpe ratio at which to evaluate the variance. For `required_n` /
        `mde` solver iteration, this is iterated by the bisection driver.
    n : int
        Sample size (T in Lo 2002 notation). Must be ≥ 3 (variance formula
        is undefined at n < 3 for finite-sample asymptotic results).
    skewness : float
        Third standardized central moment γ_3 of the return distribution.
        Gaussian: 0.0.
    kurtosis : float
        Fourth standardized central moment γ_4 of the return distribution
        (full kurtosis, NOT excess). Gaussian: 3.0. The H053 design.md
        option-3 pin's `excess_kurtosis_pilot=3.0` is interpreted under
        this convention (Gaussian).
    ar1_rho : float
        Lag-1 autocorrelation of the return series. Must be in (-1, 1).
        Gaussian iid: 0.0.

    Returns
    -------
    float
        Lo 2002 §III variance estimate (positive scalar) for the given
        parameters and sample size.

    Raises
    ------
    ValueError
        If `n < 3`, `ar1_rho ∉ (-1, 1)`, or the formula yields a
        negative variance (the kurtosis × skewness × SR combination is
        outside the regime where Lo 2002 eq. 14 is valid).
    """
    if n < 3:
        raise ValueError(f"n >= 3 required for Lo 2002 variance; got {n}.")
    if not (-1.0 < ar1_rho < 1.0):
        raise ValueError(
            f"ar1_rho must be in (-1, 1) for AR(1) HAC inflation; got {ar1_rho}."
        )

    iid_term = (1.0 - skewness * sr + (kurtosis - 1.0) * sr * sr / 4.0) / n
    hac_inflation = (1.0 + ar1_rho) / (1.0 - ar1_rho)
    var = iid_term * hac_inflation
    if var < 0:
        raise ValueError(
            f"Lo 2002 variance is negative ({var:.6g}) at sr={sr}, "
            f"skewness={skewness}, kurtosis={kurtosis}; the parametric "
            f"combination is outside the Mertens-Opdyke iid-form regime."
        )
    return float(var)


def lo2002_sr_se(sr: float, n: int, **kwargs: float) -> float:
    """Standard error = sqrt(Lo 2002 §III variance). Convenience wrapper."""
    return float(np.sqrt(lo2002_sr_variance(sr, n, **kwargs)))


# ---------------------------------------------------------------------------
# Power-calibration record (ReproLog sidecar payload)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PowerCalibration:
    """Power-calibration record persisted to ReproLog sidecar.

    Schema mirrors the H053 design.md §9 yaml `power:` block plus the
    `pilot_source` provenance sub-field defined by the option-3 addendum.
    Field naming matches design.md §9 yaml verbatim where possible:
    `expected_n_oos` (the splitter-derived realized OOS sample size used
    for MDE inversion, per design.md line 366); `kurtosis` follows the
    project's full-kurtosis convention per the module docstring's
    Convention note (the design.md `excess_kurtosis_pilot` naming is
    a known upstream language inconsistency tracked under
    `P1-H053-KURTOSIS-CONVENTION-RECONCILE`); `ar1_rho` drops the
    design.md `_pilot` suffix for symmetry with the function signatures
    (the `pilot_source` field carries the provenance attribution).

    Schema additions over design.md §9 yaml verbatim:
    - `skewness`: Mertens-Opdyke generalisation requires it; tracked
      under `P1-H053-POWER-SCHEMA-RECONCILE` for design.md amendment.
    - `one_sided`: H053 §1 binds a one-sided test; recording this in
      the sidecar makes the power inversion auditable.
    - `pilot_source`: provenance attribution defined by the
      power_calibration_addendum_2026-04-30.md §"Pre-registered
      consequences" item 3.
    """

    alpha: float
    target_power: float
    expected_n_oos: int
    s_min: float
    n_required: int
    skewness: float
    kurtosis: float
    ar1_rho: float
    variance_formula: str
    one_sided: bool
    pilot_source: str

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Required-n solver and MDE inverter
# ---------------------------------------------------------------------------


def _z_alpha(alpha: float, *, one_sided: bool) -> float:
    if one_sided:
        return float(scipy_stats.norm.ppf(1.0 - alpha))
    return float(scipy_stats.norm.ppf(1.0 - alpha / 2.0))


def required_n(
    s_min: float,
    *,
    alpha: float = 0.05,
    target_power: float = 0.80,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    ar1_rho: float = 0.0,
    one_sided: bool = True,
    n_max: int = 10_000_000,
) -> int:
    """Minimum sample size for which a Sharpe-test reaches `target_power`
    against the alternative `SR = s_min`.

    Solves for the smallest integer `n ≥ 3` such that

        P(Ŝ > z_α · SE(0; n) | SR = s_min) ≥ target_power

    where `SE(SR; n) = sqrt(lo2002_sr_variance(SR, n; ρ, γ_3, γ_4))`.

    Strategy is bisection on `n`. The asymptotic large-n form
    `s_min ≈ (z_α + z_β) / sqrt(n)` provides the initial bracket centre;
    the upper bracket is doubled until power crosses `target_power`,
    capped at `n_max` (raises if exceeded — the design is unreachable
    under the given parameters).

    Parameters
    ----------
    s_min : float
        Target alternative Sharpe ratio (the smallest effect size the
        design is required to detect at `target_power`). Must be > 0.
    alpha : float
        Significance level for the test, typically 0.05 per ADR-0004.
    target_power : float
        Probability of correctly rejecting H0 when SR = s_min, typically
        0.80 per ADR-0004.
    skewness, kurtosis, ar1_rho : float
        Distributional parameters passed to `lo2002_sr_variance`.
    one_sided : bool
        H053 §1 binds a one-sided test; default True.
    n_max : int
        Upper safety bound on the bisection bracket. Prevents runaway
        searches for unattainable designs.

    Returns
    -------
    int
        Minimum `n` meeting the power criterion.

    Raises
    ------
    ValueError
        If `s_min ≤ 0`, `alpha` / `target_power` are out of (0, 1), or
        the design is unreachable under `n_max`.
    """
    if s_min <= 0:
        raise ValueError(f"s_min must be > 0; got {s_min}.")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be in (0, 1); got {alpha}.")
    if not (0.0 < target_power < 1.0):
        raise ValueError(f"target_power must be in (0, 1); got {target_power}.")
    if n_max < 3:
        raise ValueError(f"n_max must be >= 3; got {n_max}.")

    z_a = _z_alpha(alpha, one_sided=one_sided)
    z_b = float(scipy_stats.norm.ppf(target_power))

    def power_at(n: int) -> float:
        se_h0 = lo2002_sr_se(0.0, n, skewness=skewness, kurtosis=kurtosis, ar1_rho=ar1_rho)
        se_h1 = lo2002_sr_se(
            s_min, n, skewness=skewness, kurtosis=kurtosis, ar1_rho=ar1_rho
        )
        critical = z_a * se_h0
        z_score = (critical - s_min) / se_h1
        return float(1.0 - scipy_stats.norm.cdf(z_score))

    n_init = max(int(np.ceil(((z_a + z_b) / s_min) ** 2)), 3)
    n_lo, n_hi = 3, min(n_init * 2, n_max)
    while power_at(n_hi) < target_power:
        if n_hi >= n_max:
            raise ValueError(
                f"required_n exceeds n_max={n_max} for s_min={s_min}; "
                f"design is unreachable under given parameters "
                f"(skewness={skewness}, kurtosis={kurtosis}, ar1_rho={ar1_rho}). "
                f"All identifiers ASCII-only for cross-platform raise-message safety."
            )
        n_hi = min(n_hi * 2, n_max)

    while n_lo < n_hi:
        n_mid = (n_lo + n_hi) // 2
        if power_at(n_mid) < target_power:
            n_lo = n_mid + 1
        else:
            n_hi = n_mid
    return n_lo


def mde(
    n: int,
    *,
    alpha: float = 0.05,
    target_power: float = 0.80,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    ar1_rho: float = 0.0,
    one_sided: bool = True,
    s_max: float = 100.0,
    tol: float = 1e-9,
) -> float:
    # justify: `s_max=100.0` is a per-period Sharpe upper safety bound for the
    # bisection bracket. A daily Sharpe of 100 corresponds to annualized ≈ 1587,
    # far outside any realistic detection regime. Caller-overridable for
    # unit-testing edge cases. The bracket-expansion `s_hi_cap = s_max * 1000.0`
    # below is the unreachable-design backstop (raises ValueError if reached).
    # justify: `tol=1e-9` is float64-safe and well below the integer-rounding
    # scale of `required_n`: `mde(n) ± 1e-9` always rounds to the same integer
    # for the `required_n(mde(n))` round-trip in the project's working n range.
    """Minimum detectable effect size at given `n`, `alpha`, `target_power`.

    Inverts `required_n`: returns the smallest Sharpe `s` such that
    `required_n(s, ...) ≤ n`. Solves via bisection on the equation

        f(s) = z_α · SE(0; n) + z_β · SE(s; n) − s = 0.

    `f(0) = z_α · SE(0; n) > 0`; `f(s)` is decreasing in `s` (the
    `−s` term dominates the `√(1 + s²/2)` numerator at large `s`). Bracket
    expands the upper end until `f(s_hi) < 0`.
    """
    if n < 3:
        raise ValueError(f"n >= 3 required; got {n}.")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be in (0, 1); got {alpha}.")
    if not (0.0 < target_power < 1.0):
        raise ValueError(f"target_power must be in (0, 1); got {target_power}.")
    if tol <= 0:
        raise ValueError(f"tol must be > 0; got {tol}.")

    z_a = _z_alpha(alpha, one_sided=one_sided)
    z_b = float(scipy_stats.norm.ppf(target_power))
    se_h0 = lo2002_sr_se(0.0, n, skewness=skewness, kurtosis=kurtosis, ar1_rho=ar1_rho)

    def f(s: float) -> float:
        se_s = lo2002_sr_se(
            s, n, skewness=skewness, kurtosis=kurtosis, ar1_rho=ar1_rho
        )
        return z_a * se_h0 + z_b * se_s - s

    s_lo, s_hi = 0.0, s_max
    # justify: `s_hi_cap = s_max * 1000.0` is a 5-decade safety floor on the
    # bracket-expansion loop, preventing infinite-loop in the pathological-
    # monotonicity regime where `f(s)` is non-decreasing in `s`
    # (z_beta * sqrt((kurtosis - 1)/(4*n)) * sqrt((1+rho)/(1-rho)) >= 1;
    # the raise message documents the threshold). For ordinary parameters
    # `f(s)` is monotone decreasing and the cap is never approached.
    s_hi_cap = s_max * 1000.0
    while f(s_hi) > 0:
        if s_hi >= s_hi_cap:
            raise ValueError(
                f"mde bracket failed at s_hi={s_hi}; design is unreachable "
                f"under given parameters (n={n}, ar1_rho={ar1_rho}, "
                f"kurtosis={kurtosis}). All identifiers ASCII-only for "
                f"cross-platform raise-message safety. The pathological "
                f"regime is characterised by "
                f"z_beta * sqrt((kurtosis-1)/(4n)) * sqrt((1+rho)/(1-rho)) >= 1, "
                f"under which f(s) becomes monotone non-decreasing in s."
            )
        s_hi = min(s_hi * 2.0, s_hi_cap)

    while s_hi - s_lo > tol:
        s_mid = 0.5 * (s_lo + s_hi)
        if f(s_mid) > 0:
            s_lo = s_mid
        else:
            s_hi = s_mid
    return 0.5 * (s_lo + s_hi)


# ---------------------------------------------------------------------------
# ReproLog sidecar writer
# ---------------------------------------------------------------------------


def write_power_calibration_sidecar(
    record: PowerCalibration,
    repro_log_dir: Path,
    run_id: str,
) -> Path:
    """Persist a `PowerCalibration` record as JSON sidecar (atomic write).

    Per H053 design.md §11.2 prereq 19: the sidecar must be written at
    run start, before any model fit. The output path follows the
    `logs/reproducibility/{run_id}_power_calibration.json` convention
    referenced by design.md §9 + §11.2 (note: the design.md text inverts
    the order to `power_calibration_{run_id}.json`; the implementation
    follows the project-wide sidecar convention `{run_id}_<artifact>.json`
    matching `{run_id}_hmm_selection.json` in
    [src/skie_ninja/models/regime/serialization.py](
    ../models/regime/serialization.py); reconciliation tracked under
    `P1-H053-SIDECAR-PATH-DESIGN-MD-RECONCILE`).

    The write is atomic: the payload is first written to a `.tmp`
    sibling, then `os.replace`-d to the final path. This prevents
    half-written sidecars on OS-initiated kills (a recurring failure
    mode per the H050 production-run history; see
    [docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md](
    ../../../docs/research_notes/memo_h050-prodrun-postmortem_2026-04-30.md)).

    The non-deterministic `_meta.written_at` timestamp is segregated
    into a `_meta` sub-block so any future SHA roll-up of the
    `PowerCalibration` payload can exclude it cleanly. The dataclass
    fields themselves (the load-bearing power-calibration record) are
    bit-deterministic given the same inputs.

    Returns the absolute path to the written file.
    """
    import os

    repro_log_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = repro_log_dir / f"{run_id}_power_calibration.json"
    tmp_path = sidecar_path.with_suffix(".json.tmp")
    payload = {
        "power_calibration": record.to_dict(),
        "_meta": {
            "written_at": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
        },
    }
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    os.replace(tmp_path, sidecar_path)
    return sidecar_path
