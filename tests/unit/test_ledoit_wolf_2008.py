"""Unit tests for Ledoit-Wolf 2008 studentised differential-Sharpe CI.

Closes evidence-bar-blocking follow-up
``P1-H050-LW2008-DIFFERENTIAL-CI-IMPL`` per
[research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md](../../research/01_hypothesis_register/H050/aggregation_rule_addendum_2026-04-24.md)
§5.3.

Coverage targets:

  - signature + dataclass contract
  - empirical 95% coverage on iid Gaussian fixtures with SR_a = SR_b
  - empirical 95% coverage under AR(1) cross-correlated dependence
  - Politis-White 2004 auto block-length selection on the
    paired-difference series
  - studentised vs basic-percentile CIs differ on heavy tails
  - determinism under fixed RNG
  - input-validation guards
  - perfect-correlation degenerate case (identical series)
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from skie_ninja.inference.bootstrap import (
    politis_white_block_length,
    stationary_bootstrap_indices,
)
from skie_ninja.inference.stats.ledoit_wolf_2008 import (
    DifferentialCIResult,
    ledoit_wolf_2008_differential_ci,
)

# Module-level constants for ruff-clean PLR2004 compliance.
_SHA_HEX_LEN = 64
_COVERAGE_LB = 0.92
_COVERAGE_UB = 0.98
_DEFAULT_ALPHA = 0.05
_SIGNATURE_TEST_N = 200
_QUANTILE_DEPARTURE_FLOOR = 0.05
_PERFECT_CORR_CI_WIDTH_TOL = 1e-3
# justify: closed-form lower bound on the basic-percentile vs
# studentised-pivot width departure on a Student-t(df=4) sample.
# The Student-t(0.975, 4) quantile is 2.776 (verifiable via
# scipy.stats.t.ppf(0.975, 4)) vs z_{0.975} = 1.960. The
# studentised-pivot CI inflates the half-width by the bootstrap
# T-quantile envelope, which on heavy-tailed samples tracks the
# Student-t critical value rather than the standard-normal one;
# the asymptotic departure under exact t(4) is ~42% (= 2.776/1.960
# - 1). We assert a 5% lower bound to absorb (a) finite-sample
# Monte-Carlo error in the bootstrap quantile and (b) heteroskedastic
# variance contributions from per-replicate HAC. Anchored in
# Hall 1992 §3.5 ("studentized pivots can substantially differ from
# raw percentile pivots when the studentising factor is data-
# dependent"). Floor far below the asymptotic departure but above
# Monte-Carlo noise at B = 4000.
_BASIC_PERCENTILE_DEPARTURE_FLOOR = 0.05
# Coverage tolerance for AR(1) sweep at modest ρ. Wilson 95% interval
# at n_fixtures = 300 is approximately ±2.4 pp; we widen to ±3 pp to
# absorb residual bootstrap MC variance at B = 800 plus AR(1) sample-
# size effects.
_AR1_COVERAGE_LB = 0.92
_AR1_COVERAGE_UB = 0.98
# Slow-mixing AR(1) (ρ ≥ ρ_high) reduces the effective sample size
# (Bartlett 1946 ESS ≈ n · (1-ρ)/(1+ρ)); widen tolerance to ±5pp.
_AR1_COVERAGE_LB_SLOW = 0.90
_AR1_COVERAGE_UB_SLOW = 0.99
_AR1_RHO_HIGH = 0.7


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ar1_pair(
    n: int,
    *,
    rho_a: float,
    rho_b: float,
    cross: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Two AR(1) series with cross-shock correlation ``cross``."""
    rng = np.random.default_rng(seed)
    cov = np.array([[1.0, cross], [cross, 1.0]])
    eps = rng.multivariate_normal(mean=[0.0, 0.0], cov=cov, size=n + 200)
    a = np.zeros(n + 200)
    b = np.zeros(n + 200)
    for t in range(1, n + 200):
        a[t] = rho_a * a[t - 1] + eps[t, 0]
        b[t] = rho_b * b[t - 1] + eps[t, 1]
    return a[200:], b[200:]


# ---------------------------------------------------------------------------
# 1. Signature + dataclass contract
# ---------------------------------------------------------------------------


def test_signature_and_dataclass() -> None:
    # Decouple data and bootstrap RNG seeds (F-PLV-7): data drawn from
    # a dedicated data-generator stream; bootstrap loop consumes its
    # own generator. This avoids accidental coupling between sample
    # path and resample sequence in interpretive tests.
    data_rng = np.random.default_rng(20260101)
    boot_rng = np.random.default_rng(20260202)
    a = data_rng.normal(size=_SIGNATURE_TEST_N)
    b = data_rng.normal(size=_SIGNATURE_TEST_N)
    out = ledoit_wolf_2008_differential_ci(
        a, b, n_bootstrap=_SIGNATURE_TEST_N, rng=boot_rng
    )
    assert isinstance(out, DifferentialCIResult)

    # Frozen: assigning to a field must raise FrozenInstanceError.
    with pytest.raises(FrozenInstanceError):
        out.point_estimate = 0.0  # type: ignore[misc]

    # Field surface contract.
    expected_fields = {
        "point_estimate",
        "lower",
        "upper",
        "alpha",
        "se_hac",
        "q_lower",
        "q_upper",
        "n_obs",
        "n_bootstrap",
        "block_length",
        "bandwidth",
        "method",
        "block_length_selection",
        "bandwidth_selection",
        "bandwidth_strategy",
        "n_degenerate_resamples",
    }
    actual = {f.name for f in out.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    assert expected_fields.issubset(actual)

    # Endpoint sanity: lower <= point_estimate <= upper.
    assert out.lower <= out.point_estimate <= out.upper
    assert out.alpha == _DEFAULT_ALPHA
    assert out.n_bootstrap == _SIGNATURE_TEST_N
    assert out.n_obs == _SIGNATURE_TEST_N
    assert out.method == "ledoit_wolf_2008_studentised_stationary_bootstrap"
    assert out.bandwidth_strategy == "per_replicate"
    assert out.n_degenerate_resamples >= 0

    # to_dict round-trip serialisable.
    d = out.to_dict()
    assert d["point_estimate"] == out.point_estimate
    assert isinstance(d["block_length_selection"], dict)
    assert isinstance(d["bandwidth_selection"], dict)
    assert d["bandwidth_strategy"] == "per_replicate"
    assert d["n_degenerate_resamples"] == out.n_degenerate_resamples


# ---------------------------------------------------------------------------
# 2. Empirical coverage — iid Gaussian, SR_a = SR_b
# ---------------------------------------------------------------------------


def test_iid_gaussian_coverage() -> None:
    """1000 fixtures of independent iid Gaussian; SR_a = SR_b = 0."""
    n_fixtures = 1000
    n_obs = 500
    n_boot = 1000  # smaller B for runtime; coverage still close to 95%.
    rng_master = np.random.default_rng(20260424)
    covered = 0
    for _ in range(n_fixtures):
        seed = int(rng_master.integers(0, 2**31 - 1))
        rng = np.random.default_rng(seed)
        a = rng.normal(0.0, 1.0, size=n_obs)
        b = rng.normal(0.0, 1.0, size=n_obs)
        out = ledoit_wolf_2008_differential_ci(
            a, b, alpha=0.05, n_bootstrap=n_boot, rng=rng
        )
        if out.lower <= 0.0 <= out.upper:
            covered += 1
    coverage = covered / n_fixtures
    # Tolerance: allow ±3pp Monte-Carlo noise (Wilson 95% interval at
    # n=1000 is ±~1.4pp; widen to 3pp to absorb residual bootstrap MC
    # variance at B=1000).
    assert _COVERAGE_LB <= coverage <= _COVERAGE_UB, (
        f"coverage = {coverage:.3f} outside [{_COVERAGE_LB}, {_COVERAGE_UB}]"
    )


# ---------------------------------------------------------------------------
# 3. Empirical coverage — dependent (AR(1) + cross-correlation)
# ---------------------------------------------------------------------------


def test_dependent_series_coverage() -> None:
    """Coverage remains valid under AR(1) auto- and cross-correlation."""
    n_fixtures = 500
    n_obs = 500
    n_boot = 1000
    rng_master = np.random.default_rng(98765)
    covered = 0
    for _ in range(n_fixtures):
        seed = int(rng_master.integers(0, 2**31 - 1))
        rng = np.random.default_rng(seed)
        a, b = _ar1_pair(n_obs, rho_a=0.3, rho_b=0.3, cross=0.5, seed=seed)
        # Both series have identical population SR (= 0).
        out = ledoit_wolf_2008_differential_ci(
            a, b, alpha=0.05, n_bootstrap=n_boot, rng=rng
        )
        if out.lower <= 0.0 <= out.upper:
            covered += 1
    coverage = covered / n_fixtures
    # Slightly looser tolerance for AR(1) (n=500 fixtures): ±4pp.
    lb, ub = 0.91, 0.99
    assert lb <= coverage <= ub, (
        f"AR(1) coverage = {coverage:.3f} outside [{lb}, {ub}]"
    )


# ---------------------------------------------------------------------------
# 4. Auto block-length selection on paired-difference series
# ---------------------------------------------------------------------------


def test_block_length_auto_selection() -> None:
    """``block_length=None`` triggers PW2004 auto-selection; positive + stable."""
    rng = np.random.default_rng(11)
    a, b = _ar1_pair(400, rho_a=0.4, rho_b=0.2, cross=0.3, seed=11)

    # Two runs with different bootstrap seeds — block length depends only
    # on the input data (PW2004 is deterministic), not the bootstrap RNG.
    out1 = ledoit_wolf_2008_differential_ci(
        a, b, n_bootstrap=200, rng=np.random.default_rng(1)
    )
    out2 = ledoit_wolf_2008_differential_ci(
        a, b, n_bootstrap=200, rng=np.random.default_rng(999)
    )
    assert out1.block_length == out2.block_length
    assert out1.block_length >= 1.0
    assert out1.block_length_selection.method == "politis_white_2004"
    assert out1.bandwidth_selection.method == "nw1994_automatic"

    # Caller-fixed override is respected.
    out_fixed = ledoit_wolf_2008_differential_ci(
        a, b, block_length=10.0, n_bootstrap=200, rng=rng
    )
    assert out_fixed.block_length == pytest.approx(10.0)
    assert out_fixed.block_length_selection.method == "fixed"


# ---------------------------------------------------------------------------
# 4b. Per-replicate vs fixed-bandwidth coverage on AR(1) sweep
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rho", [0.3, 0.6, 0.8])
def test_per_replicate_vs_fixed_bandwidth_coverage_ar1_sweep(rho: float) -> None:
    """Per-replicate bandwidth is the LW2008 spec-faithful default
    (WP 320 §3.2.2). Lahiri 2003 §3.3 establishes a methodologically
    real difference between fixed-vs-per-replicate bandwidth in the
    bootstrap variance of Bartlett-kernel HAC estimators — not first-
    order asymptotically equivalent.

    We assert per-replicate empirical coverage is within ±3pp of
    nominal 95% on AR(1) ρ ∈ {0.3, 0.6, 0.8}; we record (no-assert)
    the per-replicate-vs-fixed coverage delta for documentation.
    """
    n_fixtures = 300
    n_obs = 500
    n_boot = 800
    rng_master = np.random.default_rng(202604240 + int(rho * 100))
    covered_pr = 0
    covered_fx = 0
    for _ in range(n_fixtures):
        seed = int(rng_master.integers(0, 2**31 - 1))
        boot_rng_pr = np.random.default_rng(seed ^ 0xA5)
        boot_rng_fx = np.random.default_rng(seed ^ 0xA5)
        a, b = _ar1_pair(n_obs, rho_a=rho, rho_b=rho, cross=0.4, seed=seed)
        out_pr = ledoit_wolf_2008_differential_ci(
            a,
            b,
            alpha=0.05,
            n_bootstrap=n_boot,
            bandwidth_strategy="per_replicate",
            rng=boot_rng_pr,
        )
        out_fx = ledoit_wolf_2008_differential_ci(
            a,
            b,
            alpha=0.05,
            n_bootstrap=n_boot,
            bandwidth_strategy="fixed_at_original",
            rng=boot_rng_fx,
        )
        if out_pr.lower <= 0.0 <= out_pr.upper:
            covered_pr += 1
        if out_fx.lower <= 0.0 <= out_fx.upper:
            covered_fx += 1
    cov_pr = covered_pr / n_fixtures
    cov_fx = covered_fx / n_fixtures
    # Spec-faithful: assert per-replicate coverage within ±3pp of
    # nominal 95%; widen for higher autocorrelation (ρ=0.8 has slower
    # mixing and the n=500 effective sample size is reduced).
    if rho >= _AR1_RHO_HIGH:
        lb, ub = _AR1_COVERAGE_LB_SLOW, _AR1_COVERAGE_UB_SLOW
    else:
        lb, ub = _AR1_COVERAGE_LB, _AR1_COVERAGE_UB
    assert lb <= cov_pr <= ub, (
        f"per-replicate AR(1) ρ={rho} coverage = {cov_pr:.3f} outside "
        f"[{lb}, {ub}]; (fixed-lag coverage = {cov_fx:.3f}, "
        f"delta = {cov_pr - cov_fx:+.3f})"
    )


# ---------------------------------------------------------------------------
# 5. Studentised vs basic percentile differ on heavy tails
# ---------------------------------------------------------------------------


def test_bootstrap_quantiles_depart_from_normal_on_small_sample() -> None:
    """Bootstrap T-quantiles depart from standard normal critical values
    on a small heavy-tailed sample — confirming the bootstrap pathway
    is actively engaged.

    Under exact iid Gaussian asymptotics, the studentised T-statistic
    is asymptotically standard normal; ``q_{1-a/2}(T*) → z_{1-a/2}``.
    On a small Student-t(3) sample (n=80) the bootstrap T-distribution
    has heavier tails than standard normal, so
    ``|q_{0.975}(T*)|`` exceeds the asymptotic Gaussian
    ``z_{0.975} ≈ 1.96`` by a measurable amount.

    A degenerate implementation that bypassed the studentised-pivot
    machinery (e.g., dropping back to a Wald CI with normal
    quantiles) would not exhibit this departure.
    """
    rng = np.random.default_rng(20260426)
    n = 80
    df = 3
    a = rng.standard_t(df, size=n)
    b = rng.standard_t(df, size=n)

    out = ledoit_wolf_2008_differential_ci(
        a, b, alpha=0.05, n_bootstrap=4000, rng=np.random.default_rng(20260426)
    )

    z_975 = 1.959963984540054  # scipy.stats.norm.ppf(0.975)
    # Empirical heavy-tail signal: max(|q_upper|, |q_lower|) exceeds
    # z_{0.975} by at least 5% on a t(3), n=80 sample.
    q_max = max(abs(out.q_upper), abs(out.q_lower))
    departure = (q_max - z_975) / z_975
    assert departure > _QUANTILE_DEPARTURE_FLOOR, (
        f"bootstrap T-quantile envelope (max |q| = {q_max:.3f}) is "
        f"within 5% of standard-normal z_0.975 = {z_975:.3f}; the "
        f"studentised bootstrap should capture finite-sample heavy "
        f"tails on a Student-t(3), n=80 sample."
    )


def test_studentised_vs_basic_percentile_widths_differ() -> None:
    """Studentised-pivot CI width must differ from naive
    basic-percentile CI width by at least
    ``_BASIC_PERCENTILE_DEPARTURE_FLOOR`` on a Student-t(df=4)
    fixture — direct sanity that studentisation is doing work
    (Hall 1992 §3.5; spec acceptance criterion 5c).

    Construction:
      - studentised-pivot CI:
        ``[Δ̂ − q_{1-α/2}(T*) · se / √T,
           Δ̂ − q_{α/2}(T*) · se / √T]``
        (returned by ``ledoit_wolf_2008_differential_ci``).
      - basic-percentile CI (Davison & Hinkley 1997 §5.2 eq. 5.6):
        ``[2Δ̂ − q_{1-α/2}(Δ*),
           2Δ̂ − q_{α/2}(Δ*)]``
        where ``Δ*`` is the bootstrap distribution of the **raw**
        (un-studentised) Sharpe-ratio difference.

    On a Student-t(df=4), n=120 sample, the two CI widths differ by
    >5% — anchored in the closed-form Student-t/normal quantile
    inflation at df=4 (``t_{0.975, 4} ≈ 2.776`` vs ``z_{0.975} ≈
    1.960``; asymptotic departure ≈ 42%). Floor at 5% absorbs
    finite-sample MC noise at B=4000.
    """
    data_rng = np.random.default_rng(20260427)
    boot_rng_stud = np.random.default_rng(20260428)
    boot_rng_pct = np.random.default_rng(20260428)
    n = 120
    df = 4
    a = data_rng.standard_t(df, size=n)
    b = data_rng.standard_t(df, size=n)

    n_boot = 4000
    out = ledoit_wolf_2008_differential_ci(
        a, b, alpha=0.05, n_bootstrap=n_boot, rng=boot_rng_stud
    )
    w_stud = out.upper - out.lower

    # Recompute the basic-percentile CI from the raw bootstrap
    # distribution of Δ*. Use the same block length the routine
    # selected so the two CIs differ only in the pivot, not in the
    # block-length choice.
    bl = politis_white_block_length(a - b, bootstrap_type="stationary")
    delta_hat = out.point_estimate
    delta_boot = np.empty(n_boot, dtype=np.float64)
    for k in range(n_boot):
        idx = stationary_bootstrap_indices(
            n, block_length=bl.block_length, rng=boot_rng_pct
        )
        a_star = a[idx]
        b_star = b[idx]
        mu_a = float(a_star.mean())
        mu_b = float(b_star.mean())
        var_a = float(a_star.var(ddof=0))
        var_b = float(b_star.var(ddof=0))
        if var_a <= 0.0 or var_b <= 0.0:
            delta_boot[k] = 0.0
            continue
        sr_a = mu_a / np.sqrt(var_a)
        sr_b = mu_b / np.sqrt(var_b)
        delta_boot[k] = sr_a - sr_b
    q_lo = float(np.quantile(delta_boot, 0.025))
    q_hi = float(np.quantile(delta_boot, 0.975))
    # Basic-percentile pivots (Davison & Hinkley 1997 eq. 5.6).
    lower_basic = 2.0 * delta_hat - q_hi
    upper_basic = 2.0 * delta_hat - q_lo
    w_basic = upper_basic - lower_basic

    departure = abs(w_stud - w_basic) / w_basic
    assert departure > _BASIC_PERCENTILE_DEPARTURE_FLOOR, (
        f"studentised CI width = {w_stud:.4f} within "
        f"{_BASIC_PERCENTILE_DEPARTURE_FLOOR:.0%} of basic-percentile "
        f"CI width = {w_basic:.4f}; studentisation should produce a "
        f"materially different width on Student-t(df=4), n=120."
    )


# ---------------------------------------------------------------------------
# 6. Determinism under fixed RNG
# ---------------------------------------------------------------------------


def test_determinism_with_fixed_rng() -> None:
    a = np.random.default_rng(1).normal(size=300)
    b = np.random.default_rng(2).normal(size=300)

    rng1 = np.random.default_rng(2026)
    rng2 = np.random.default_rng(2026)
    out1 = ledoit_wolf_2008_differential_ci(a, b, n_bootstrap=500, rng=rng1)
    out2 = ledoit_wolf_2008_differential_ci(a, b, n_bootstrap=500, rng=rng2)
    assert out1.lower == out2.lower
    assert out1.upper == out2.upper
    assert out1.q_lower == out2.q_lower
    assert out1.q_upper == out2.q_upper
    assert out1.se_hac == out2.se_hac


# ---------------------------------------------------------------------------
# 7. Input validation
# ---------------------------------------------------------------------------


def test_input_validation_length_mismatch() -> None:
    rng = np.random.default_rng(1)
    a = rng.normal(size=100)
    b = rng.normal(size=99)
    with pytest.raises(ValueError, match="identical shape"):
        ledoit_wolf_2008_differential_ci(a, b, n_bootstrap=10, rng=rng)


def test_input_validation_nan_inf() -> None:
    rng = np.random.default_rng(1)
    a = rng.normal(size=100)
    b = rng.normal(size=100)
    a[5] = np.nan
    with pytest.raises(ValueError, match="NaN"):
        ledoit_wolf_2008_differential_ci(a, b, n_bootstrap=10, rng=rng)
    a[5] = np.inf
    with pytest.raises(ValueError, match="NaN"):
        ledoit_wolf_2008_differential_ci(a, b, n_bootstrap=10, rng=rng)


def test_input_validation_short_series() -> None:
    rng = np.random.default_rng(1)
    a = np.array([0.1, 0.2, 0.3])
    b = np.array([0.1, 0.2, 0.3])
    with pytest.raises(ValueError, match="n >= 4"):
        ledoit_wolf_2008_differential_ci(a, b, n_bootstrap=10, rng=rng)


def test_input_validation_alpha_range() -> None:
    rng = np.random.default_rng(1)
    a = rng.normal(size=100)
    b = rng.normal(size=100)
    with pytest.raises(ValueError, match="alpha"):
        ledoit_wolf_2008_differential_ci(
            a, b, alpha=0.0, n_bootstrap=10, rng=rng
        )
    with pytest.raises(ValueError, match="alpha"):
        ledoit_wolf_2008_differential_ci(
            a, b, alpha=1.0, n_bootstrap=10, rng=rng
        )


def test_input_validation_zero_variance() -> None:
    rng = np.random.default_rng(1)
    a = np.zeros(100)
    b = rng.normal(size=100)
    with pytest.raises(ValueError, match="(?i)variance"):
        ledoit_wolf_2008_differential_ci(a, b, n_bootstrap=10, rng=rng)


def test_input_validation_negative_block_length() -> None:
    rng = np.random.default_rng(1)
    a = rng.normal(size=100)
    b = rng.normal(size=100)
    with pytest.raises(ValueError, match="block_length"):
        ledoit_wolf_2008_differential_ci(
            a, b, block_length=0.5, n_bootstrap=10, rng=rng
        )


def test_input_validation_n_bootstrap() -> None:
    rng = np.random.default_rng(1)
    a = rng.normal(size=100)
    b = rng.normal(size=100)
    with pytest.raises(ValueError, match="n_bootstrap"):
        ledoit_wolf_2008_differential_ci(a, b, n_bootstrap=0, rng=rng)


# ---------------------------------------------------------------------------
# 8. Perfect-correlation degenerate case
# ---------------------------------------------------------------------------


def test_zero_difference_under_perfect_correlation() -> None:
    """When ``returns_a == returns_b``, point estimate is 0 and CI is tight."""
    rng_data = np.random.default_rng(123)
    a = rng_data.normal(0.001, 0.01, size=400)
    b = a.copy()  # identical series — paired SR difference is exactly 0.
    rng = np.random.default_rng(456)
    out = ledoit_wolf_2008_differential_ci(
        a, b, n_bootstrap=500, rng=rng
    )
    assert out.point_estimate == pytest.approx(0.0, abs=1e-12)
    # CI must contain zero and be tightly bounded; under identical
    # series the bootstrap difference is also identically zero so the
    # CI collapses to a numerical neighbourhood of zero. Tolerance is
    # generous to absorb the _EPS variance floor's contribution to
    # se_HAC and any float64 round-off.
    assert out.lower <= 0.0 <= out.upper
    assert abs(out.upper - out.lower) < _PERFECT_CORR_CI_WIDTH_TOL
