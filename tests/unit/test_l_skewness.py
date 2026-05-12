"""Unit tests for ADR-0019 L-skewness τ_3 primitive (Hosking 1990).

Coverage:
- l_moments_pwm: PWM correctness, n<3 handling, error on empty/non-finite.
- l_skewness_tau3: closed-form convergence on exponential (1/3), Gumbel
  (≈ 0.1699), standard normal (≈ 0); bounds [-1, 1]; sign symmetry under
  negation; degenerate constant input → NaN.
- l_skewness_tau3_ci_stationary_bootstrap: deterministic seed; coverage on
  Gaussian (~95% empirical of τ_3 = 0 in 100 trials at n=200).
- payoff_shape_annotation: all 5 categorical outputs.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.inference.skewness import (
    LSkewnessTau3CI,
    l_moments_pwm,
    l_skewness_tau3,
    l_skewness_tau3_ci_stationary_bootstrap,
    payoff_shape_annotation,
)

# ---------------------------------------------------------------------------
# l_moments_pwm
# ---------------------------------------------------------------------------


def test_l_moments_pwm_lambda_1_equals_mean() -> None:
    """λ_1 is the arithmetic mean (Hosking 1990 eq. 2.3 first PWM)."""
    rng = np.random.default_rng(0)
    x = rng.normal(2.5, 1.0, size=500)
    out = l_moments_pwm(x)
    assert out["lambda_1"] == pytest.approx(x.mean())


def test_l_moments_pwm_lambda_2_positive_for_non_constant() -> None:
    """λ_2 (L-scale) is strictly positive for a non-constant sample."""
    rng = np.random.default_rng(1)
    x = rng.normal(0.0, 1.0, size=200)
    out = l_moments_pwm(x)
    assert out["lambda_2"] > 0.0


def test_l_moments_pwm_n_two_returns_nan_lambda_3() -> None:
    """λ_3 is NaN when n < 3."""
    out = l_moments_pwm([1.0, 2.0])
    assert np.isnan(out["lambda_3"])
    assert out["lambda_1"] == pytest.approx(1.5)
    assert np.isfinite(out["lambda_2"])


def test_l_moments_pwm_n_one_lambda_2_and_3_nan() -> None:
    """λ_2 and λ_3 are NaN when n = 1."""
    out = l_moments_pwm([3.14])
    assert out["lambda_1"] == pytest.approx(3.14)
    assert np.isnan(out["lambda_2"])
    assert np.isnan(out["lambda_3"])


def test_l_moments_pwm_empty_raises() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        l_moments_pwm([])


def test_l_moments_pwm_non_finite_raises() -> None:
    with pytest.raises(ValueError, match="finite"):
        l_moments_pwm([1.0, np.nan, 3.0])
    with pytest.raises(ValueError, match="finite"):
        l_moments_pwm([1.0, np.inf, 3.0])


# ---------------------------------------------------------------------------
# l_skewness_tau3 — closed-form convergence
# ---------------------------------------------------------------------------


def test_tau3_exponential_converges_to_one_third() -> None:
    """Exponential distribution: τ_3 = 1/3 (Hosking 1990 Table 1).

    100,000 samples; convergence within 0.01.
    """
    rng = np.random.default_rng(42)
    x = rng.exponential(scale=1.0, size=100_000)
    tau3 = l_skewness_tau3(x)
    assert tau3 == pytest.approx(1.0 / 3.0, abs=0.01)


def test_tau3_gumbel_converges_to_hosking_value() -> None:
    """Gumbel distribution: τ_3 ≈ 0.1699 (Hosking 1990 Table 1, ``log 9 / log 8 − 2``
    closed form ``9 log 3 / (2 log 2) − 2 ≈ 0.1699``).

    100,000 samples; convergence within 0.01.
    """
    rng = np.random.default_rng(7)
    x = rng.gumbel(loc=0.0, scale=1.0, size=100_000)
    tau3 = l_skewness_tau3(x)
    assert tau3 == pytest.approx(0.1699, abs=0.01)


def test_tau3_standard_normal_converges_to_zero() -> None:
    """Standard normal: τ_3 = 0 (Hosking 1990 Table 1; symmetric).

    100,000 samples; convergence within 0.01.
    """
    rng = np.random.default_rng(13)
    x = rng.normal(0.0, 1.0, size=100_000)
    tau3 = l_skewness_tau3(x)
    assert tau3 == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# l_skewness_tau3 — bounds + symmetry + edge cases
# ---------------------------------------------------------------------------


def test_tau3_bounded_in_minus_one_one_heavy_tail() -> None:
    """τ_3 ∈ [-1, 1] always (Hosking 1990 Theorem 1; heavy-tail t-3 stress test)."""
    rng = np.random.default_rng(99)
    x = rng.standard_t(df=3, size=10_000)
    tau3 = l_skewness_tau3(x)
    assert -1.0 <= tau3 <= 1.0


def test_tau3_lognormal_positive() -> None:
    """Lognormal: right-skewed → τ_3 > 0 (Hosking 1990 Table 1)."""
    rng = np.random.default_rng(2026)
    x = rng.lognormal(mean=0.0, sigma=1.0, size=20_000)
    tau3 = l_skewness_tau3(x)
    assert tau3 > 0.1


def test_tau3_negated_lognormal_negative_sign_symmetry() -> None:
    """Negated lognormal: left-skewed → τ_3 < 0 (sign symmetry under negation:
    τ_3(-X) = -τ_3(X) per Hosking 1990 §2.4).
    """
    rng = np.random.default_rng(2027)
    x = rng.lognormal(mean=0.0, sigma=1.0, size=20_000)
    tau3_pos = l_skewness_tau3(x)
    tau3_neg = l_skewness_tau3(-x)
    assert tau3_neg < -0.1
    assert tau3_neg == pytest.approx(-tau3_pos, abs=1e-10)


def test_tau3_constant_input_nan() -> None:
    """Constant input: λ_2 = 0 → τ_3 = NaN (no crash, no division-by-zero)."""
    x = np.full(50, 3.14)
    tau3 = l_skewness_tau3(x)
    assert np.isnan(tau3)


def test_tau3_two_element_input_nan() -> None:
    """n = 2 < 3 → τ_3 = NaN (λ_3 undefined)."""
    tau3 = l_skewness_tau3([1.0, 2.0])
    assert np.isnan(tau3)


# ---------------------------------------------------------------------------
# l_skewness_tau3_ci_stationary_bootstrap
# ---------------------------------------------------------------------------


def test_tau3_ci_deterministic_under_fixed_seed() -> None:
    """Identical rng_seed → bit-identical CI bounds."""
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, 1.0, size=200)
    ci_a = l_skewness_tau3_ci_stationary_bootstrap(x, n_bootstrap=200, rng_seed=42)
    ci_b = l_skewness_tau3_ci_stationary_bootstrap(x, n_bootstrap=200, rng_seed=42)
    assert ci_a.ci_low == ci_b.ci_low
    assert ci_a.ci_high == ci_b.ci_high
    assert ci_a.tau3 == ci_b.tau3


def test_tau3_ci_provenance_fields_set() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, 1.0, size=200)
    ci = l_skewness_tau3_ci_stationary_bootstrap(x, n_bootstrap=200, rng_seed=42)
    assert isinstance(ci, LSkewnessTau3CI)
    assert ci.n_obs == 200
    assert ci.n_bootstrap == 200
    assert ci.block_length_method == "politis_white_2004"
    assert ci.block_length >= 1.0


def test_tau3_ci_operator_supplied_block_length() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, 1.0, size=200)
    ci = l_skewness_tau3_ci_stationary_bootstrap(
        x, n_bootstrap=200, rng_seed=42, block_length=4.0
    )
    assert ci.block_length == pytest.approx(4.0)
    assert ci.block_length_method == "operator_supplied"


def test_tau3_ci_small_n_raises() -> None:
    with pytest.raises(ValueError, match="n >= 4"):
        l_skewness_tau3_ci_stationary_bootstrap([1.0, 2.0, 3.0])


def test_tau3_ci_coverage_gaussian_zero() -> None:
    """Empirical 95%-CI coverage on Gaussian samples (τ_3 = 0 is the truth).

    100 trials at n=200; expected coverage ≈ 95%; allow ≥ 88% to absorb
    finite-sample + stationary-bootstrap bias on a non-time-series input.
    """
    n_trials = 100
    n_samples = 200
    covered = 0
    for trial in range(n_trials):
        rng = np.random.default_rng(1000 + trial)
        x = rng.normal(0.0, 1.0, size=n_samples)
        ci = l_skewness_tau3_ci_stationary_bootstrap(
            x, n_bootstrap=300, rng_seed=trial
        )
        if ci.ci_low <= 0.0 <= ci.ci_high:
            covered += 1
    coverage = covered / n_trials
    assert coverage >= 0.88, f"Empirical coverage {coverage:.2f} below 0.88."


def test_tau3_ci_excludes_threshold_predicate() -> None:
    """``excludes_threshold(t)`` is True iff ci_low > +t or ci_high < -t."""
    ci = LSkewnessTau3CI(
        tau3=0.4,
        ci_low=0.2,
        ci_high=0.6,
        n_obs=100,
        n_bootstrap=1000,
        block_length=4.0,
    )
    assert ci.excludes_threshold(0.1) is True
    assert ci.excludes_threshold(0.3) is False  # CI straddles 0.3 on low side
    ci_neg = LSkewnessTau3CI(
        tau3=-0.4,
        ci_low=-0.6,
        ci_high=-0.2,
        n_obs=100,
        n_bootstrap=1000,
        block_length=4.0,
    )
    assert ci_neg.excludes_threshold(0.1) is True
    ci_flat = LSkewnessTau3CI(
        tau3=0.05,
        ci_low=-0.1,
        ci_high=0.2,
        n_obs=100,
        n_bootstrap=1000,
        block_length=4.0,
    )
    assert ci_flat.excludes_threshold(0.1) is False


# ---------------------------------------------------------------------------
# payoff_shape_annotation
# ---------------------------------------------------------------------------


def test_payoff_annotation_skew_positive() -> None:
    """τ_3 = 0.3, CI = [0.2, 0.4] both > +0.1 → ``skew-positive``."""
    assert payoff_shape_annotation(0.3, 0.2, 0.4, cutoff=0.1) == "skew-positive"


def test_payoff_annotation_skew_negative() -> None:
    """τ_3 = -0.3, CI = [-0.4, -0.2] both < -0.1 → ``skew-negative``."""
    assert payoff_shape_annotation(-0.3, -0.4, -0.2, cutoff=0.1) == "skew-negative"


def test_payoff_annotation_skew_positive_marginal() -> None:
    """τ_3 > +cutoff but CI low bound below +cutoff → ``skew-positive-marginal``."""
    assert (
        payoff_shape_annotation(0.15, 0.05, 0.25, cutoff=0.1) == "skew-positive-marginal"
    )


def test_payoff_annotation_skew_negative_marginal() -> None:
    """τ_3 < -cutoff but CI high bound above -cutoff → ``skew-negative-marginal``."""
    assert (
        payoff_shape_annotation(-0.15, -0.25, -0.05, cutoff=0.1)
        == "skew-negative-marginal"
    )


def test_payoff_annotation_skew_flat() -> None:
    """|τ_3| ≤ cutoff → ``skew-flat``."""
    assert payoff_shape_annotation(0.05, -0.05, 0.15, cutoff=0.1) == "skew-flat"
    assert payoff_shape_annotation(-0.05, -0.15, 0.05, cutoff=0.1) == "skew-flat"
    assert payoff_shape_annotation(0.0, -0.2, 0.2, cutoff=0.1) == "skew-flat"


def test_payoff_annotation_nan_tau3_returns_flat() -> None:
    """NaN τ_3 (degenerate input) routes to ``skew-flat`` (safe default)."""
    assert payoff_shape_annotation(float("nan"), float("nan"), float("nan")) == "skew-flat"
