"""Unit tests for Cycle-2 inference primitives: HAC + Sharpe CI.

Covers:
  - Newey-West Bartlett-kernel long-run variance on known-form series
    (hand-calc on tiny sequence; iid and AR(1) asymptotic expectations).
  - Andrews 1991 AR(1)-plug-in bandwidth recovery of known ρ.
  - Newey-West 1994 automatic bandwidth positivity / sensitivity to c.
  - Lo 2002 iid Sharpe-CI coverage at nominal 95% over Monte Carlo
    (iid N(μ, σ²) returns with known true Sharpe).
  - Opdyke 2007 CI widens vs Lo iid on skewed/heavy-tail series.
  - HAC adjustment inflates CI on positively autocorrelated series.
  - Degenerate-input rejection (NaN, inf, zero variance, n<3).
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from skie_ninja.inference.stats.hac import (
    BandwidthSelection,
    andrews1991_bartlett_bandwidth,
    nw1994_bartlett_bandwidth,
    nw_hac_variance,
)
from skie_ninja.inference.stats.sharpe_ci import (
    lo2002_hac_adjusted_ci,
    lo2002_iid_ci,
    lo2002_prop2_eta_ci,
    opdyke2007_ci,
    sample_sharpe,
)


# ---------------------------------------------------------------------------
# Synthetic generators
# ---------------------------------------------------------------------------


def _ar1(
    n: int, rho: float, sigma_eps: float, seed: int, burn_in: int = 500
) -> np.ndarray:
    """AR(1) with known parameter. Long-run variance σ²_ε * (1+ρ)/(1-ρ)."""
    rng = np.random.default_rng(seed)
    eps = rng.normal(0.0, sigma_eps, size=n + burn_in)
    x = np.zeros(n + burn_in, dtype=float)
    for t in range(1, n + burn_in):
        x[t] = rho * x[t - 1] + eps[t]
    return x[burn_in:]


def _iid_normal(n: int, mu: float, sigma: float, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).normal(mu, sigma, size=n)


# ---------------------------------------------------------------------------
# HAC: Newey-West long-run variance
# ---------------------------------------------------------------------------


class TestNWHACVariance:
    def test_bandwidth_zero_equals_sample_variance(self) -> None:
        """At L=0, HAC reduces to γ₀ (the biased sample variance)."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        lrv, _ = nw_hac_variance(x, bandwidth=0)
        # Biased variance: sum((x-mean)^2) / N = ((2)^2 + 1 + 0 + 1 + 4)/5?
        # mean=3; centred = -2,-1,0,1,2; sum sq = 10; /5 = 2.
        assert lrv == pytest.approx(2.0, rel=1e-12)

    def test_bandwidth_one_on_known_series(self) -> None:
        """Hand-calc Bartlett weighted sum at L=1 on a 4-point series."""
        x = np.array([0.0, 2.0, 0.0, 2.0])
        # mean=1; centred = -1,1,-1,1
        # gamma_0 = (1+1+1+1)/4 = 1.0
        # gamma_1 = sum_{t=1..3} centred[t]*centred[t-1] / 4
        #        = (1*-1 + -1*1 + 1*-1) / 4 = -3/4 = -0.75
        # Bartlett weight at j=1, L=1: 1 - 1/(1+1) = 0.5
        # LRV = 1.0 + 2 * 0.5 * (-0.75) = 1.0 - 0.75 = 0.25
        lrv, _ = nw_hac_variance(x, bandwidth=1)
        assert lrv == pytest.approx(0.25, rel=1e-12)

    def test_iid_long_run_variance_matches_sample_variance(self) -> None:
        """For iid series, LRV should converge to sample variance.

        Large-sample check at n=10_000: LRV ≈ 1.0 within Monte Carlo.
        """
        x = _iid_normal(n=10_000, mu=0.0, sigma=1.0, seed=42)
        bw = nw1994_bartlett_bandwidth(x)
        lrv, _ = nw_hac_variance(x, bandwidth=bw)
        assert lrv == pytest.approx(1.0, abs=0.10)

    def test_ar1_long_run_variance_matches_asymptotic(self) -> None:
        """For AR(1) Y_t = ρ Y_{t-1} + ε_t with ε iid N(0, σ²_ε):
          γ_0 = σ²_ε / (1-ρ²)
          σ²_LR = γ_0 (1+ρ)/(1-ρ) = σ²_ε / (1-ρ)²
        For ρ=0.5, σ²_ε=1: σ²_LR = 1/0.25 = 4.0.

        At n=20_000 with Andrews' bandwidth, LRV should converge to
        4.0 within MC tolerance. NW estimator has substantial sampling
        variability even at large n — use 25% tolerance.
        """
        rho, sigma_eps = 0.5, 1.0
        x = _ar1(n=20_000, rho=rho, sigma_eps=sigma_eps, seed=7)
        bw = andrews1991_bartlett_bandwidth(x)
        lrv, _ = nw_hac_variance(x, bandwidth=bw)
        expected = sigma_eps**2 / (1 - rho) ** 2  # = 4.0
        assert lrv == pytest.approx(expected, rel=0.25)

    def test_rejects_nan(self) -> None:
        with pytest.raises(ValueError, match="NaN or inf"):
            nw_hac_variance(np.array([1.0, np.nan, 2.0]), bandwidth=0)

    def test_rejects_too_short(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            nw_hac_variance(np.array([1.0]), bandwidth=0)

    def test_rejects_negative_bandwidth(self) -> None:
        with pytest.raises(ValueError, match=">= 0"):
            nw_hac_variance(np.array([1.0, 2.0, 3.0]), bandwidth=-1)


# ---------------------------------------------------------------------------
# Bandwidth selection
# ---------------------------------------------------------------------------


class TestAndrews1991Bandwidth:
    def test_rho_hat_recovers_known_ar1(self) -> None:
        x = _ar1(n=5_000, rho=0.5, sigma_eps=1.0, seed=3)
        bw = andrews1991_bartlett_bandwidth(x)
        # ρ̂ should be within MC tolerance of 0.5.
        assert bw.rho_hat == pytest.approx(0.5, abs=0.05)
        assert bw.method == "andrews1991_ar1_plugin"
        assert bw.kernel == "bartlett"
        assert bw.bandwidth >= 1  # α(1) > 0 for ρ = 0.5

    def test_iid_gives_small_bandwidth(self) -> None:
        """For ρ ≈ 0, α(1) ≈ 0 so L* ≈ 0."""
        x = _iid_normal(n=5_000, mu=0.0, sigma=1.0, seed=11)
        bw = andrews1991_bartlett_bandwidth(x)
        assert abs(bw.rho_hat or 0.0) < 0.1
        assert bw.bandwidth <= 2

    def test_rejects_too_short(self) -> None:
        with pytest.raises(ValueError, match="at least 4"):
            andrews1991_bartlett_bandwidth(np.array([1.0, 2.0, 3.0]))


class TestNW1994Bandwidth:
    def test_positive_on_ar1(self) -> None:
        x = _ar1(n=2_000, rho=0.5, sigma_eps=1.0, seed=19)
        bw = nw1994_bartlett_bandwidth(x)
        assert bw.bandwidth >= 1
        assert bw.method == "nw1994_automatic"
        assert bw.m_initial is not None and bw.m_initial >= 1

    def test_c_override_changes_bandwidth(self) -> None:
        """c controls initial-lag m; a much larger c should produce
        at-least-as-large initial m (monotone in c) and may change
        the final bandwidth."""
        x = _ar1(n=2_000, rho=0.5, sigma_eps=1.0, seed=23)
        bw_default = nw1994_bartlett_bandwidth(x)
        bw_large = nw1994_bartlett_bandwidth(x, c=12.0)
        assert (bw_large.m_initial or 0) >= (bw_default.m_initial or 0)

    def test_rejects_non_positive_c(self) -> None:
        x = _iid_normal(n=200, mu=0.0, sigma=1.0, seed=31)
        with pytest.raises(ValueError, match="c must be > 0"):
            nw1994_bartlett_bandwidth(x, c=0.0)


# ---------------------------------------------------------------------------
# Sharpe point estimate
# ---------------------------------------------------------------------------


class TestSampleSharpe:
    def test_recovers_known_sharpe(self) -> None:
        rng = np.random.default_rng(5)
        # True Sharpe = μ/σ = 0.5 per-observation.
        r = rng.normal(loc=0.5, scale=1.0, size=20_000)
        sharpe, n = sample_sharpe(r)
        assert n == 20_000
        assert sharpe == pytest.approx(0.5, abs=0.03)

    def test_rejects_zero_variance(self) -> None:
        with pytest.raises(ValueError, match="zero"):
            sample_sharpe(np.array([1.0, 1.0, 1.0, 1.0]))

    def test_rejects_too_short(self) -> None:
        with pytest.raises(ValueError, match="n >= 3"):
            sample_sharpe(np.array([1.0, 2.0]))


# ---------------------------------------------------------------------------
# Lo 2002 iid CI
# ---------------------------------------------------------------------------


class TestLo2002IidCI:
    def test_ci_is_symmetric_around_point_estimate(self) -> None:
        rng = np.random.default_rng(7)
        r = rng.normal(0.0, 1.0, size=500)
        ci = lo2002_iid_ci(r)
        mid = 0.5 * (ci.lower + ci.upper)
        assert mid == pytest.approx(ci.sharpe, abs=1e-12)

    def test_coverage_on_null_iid(self) -> None:
        """Monte Carlo coverage test: true Sharpe=0 on iid N(0,1) returns.

        Expected coverage: 0.95. With B=300 reps, standard error of
        the coverage rate is sqrt(0.95*0.05/300) ≈ 0.0126, so the
        95% MC interval on the coverage is roughly 0.95 ± 0.025.
        We use a generous 0.90-0.99 band to avoid flaky CI.
        """
        rng = np.random.default_rng(2026)
        true_sharpe = 0.0
        n = 500
        B = 300
        hits = 0
        for _ in range(B):
            r = rng.normal(loc=0.0, scale=1.0, size=n)
            ci = lo2002_iid_ci(r, confidence_level=0.95)
            if ci.lower <= true_sharpe <= ci.upper:
                hits += 1
        coverage = hits / B
        assert 0.90 <= coverage <= 0.99, f"coverage={coverage}"


# ---------------------------------------------------------------------------
# Lo 2002 HAC-adjusted CI
# ---------------------------------------------------------------------------


class TestLo2002HACAdjustedCI:
    def test_hac_inflates_ci_on_positively_autocorrelated_series(self) -> None:
        """For ρ=0.5 AR(1) returns, HAC CI should be wider than iid CI."""
        r = _ar1(n=2_000, rho=0.5, sigma_eps=1.0, seed=41)
        # Shift to have non-zero mean for a non-trivial Sharpe.
        r = r + 0.1
        iid_ci = lo2002_iid_ci(r)
        hac_ci = lo2002_hac_adjusted_ci(r)
        iid_width = iid_ci.upper - iid_ci.lower
        hac_width = hac_ci.upper - hac_ci.lower
        assert hac_width > iid_width * 1.2  # expect ≥ 20% inflation

    def test_hac_collapses_to_iid_on_iid_series(self) -> None:
        """For iid returns, σ²_LR / σ² → 1 so HAC CI ≈ iid CI."""
        r = _iid_normal(n=10_000, mu=0.1, sigma=1.0, seed=53)
        iid_ci = lo2002_iid_ci(r)
        hac_ci = lo2002_hac_adjusted_ci(r)
        # Within 20% — a loose bound because at finite T the HAC
        # estimator has its own sampling variability.
        ratio = (hac_ci.upper - hac_ci.lower) / (iid_ci.upper - iid_ci.lower)
        assert 0.8 <= ratio <= 1.3

    def test_bandwidth_selection_recorded(self) -> None:
        r = _iid_normal(n=500, mu=0.0, sigma=1.0, seed=61)
        ci = lo2002_hac_adjusted_ci(r)
        assert ci.bandwidth_selection is not None
        assert ci.bandwidth_selection.kernel == "bartlett"


# ---------------------------------------------------------------------------
# Opdyke 2007 CI
# ---------------------------------------------------------------------------


class TestOpdyke2007CI:
    def test_records_skew_and_kurtosis(self) -> None:
        r = _iid_normal(n=2_000, mu=0.1, sigma=1.0, seed=67)
        ci = opdyke2007_ci(r, hac_adjust=False)
        assert ci.skewness is not None
        assert ci.excess_kurtosis is not None
        # N(0,1) has skew ≈ 0, excess kurtosis ≈ 0.
        assert abs(ci.skewness) < 0.3
        assert abs(ci.excess_kurtosis) < 0.6

    def test_differs_from_lo_iid_on_heavy_tails(self) -> None:
        """Student-t with 5 df has excess-kurtosis ≈ 6 (γ_4≈6 per our
        sign convention; population excess kurtosis of t(5) = 6).
        The Opdyke variance formula diff-from-Lo is
          Ŝ²(γ_4/4) - Ŝ γ_3,
        which is small when Sharpe is near zero. Use a high-Sharpe
        shift so the Ŝ² term dominates and the difference is
        detectable."""
        rng = np.random.default_rng(71)
        raw = rng.standard_t(df=5, size=5_000)
        # t(5) has sd=sqrt(5/3) ≈ 1.29, so shift=0.65 → Sharpe ≈ 0.50.
        r = raw + 0.65
        iid_ci = lo2002_iid_ci(r)
        opdyke_ci = opdyke2007_ci(r, hac_adjust=False)
        rel_diff = abs(opdyke_ci.variance - iid_ci.variance) / iid_ci.variance
        assert rel_diff > 0.05, f"rel_diff={rel_diff}"

    def test_hac_adjust_flag_records_bandwidth(self) -> None:
        r = _iid_normal(n=500, mu=0.0, sigma=1.0, seed=79)
        ci = opdyke2007_ci(r, hac_adjust=True)
        assert ci.bandwidth_selection is not None
        # Round-2 rename (L-6, F-1-3): method now honestly labels the
        # practitioner approximation of Opdyke 2007 HAC.
        assert ci.method == "opdyke2007_mertens_hac_approx"

    def test_hac_adjust_false_has_no_bandwidth(self) -> None:
        r = _iid_normal(n=500, mu=0.0, sigma=1.0, seed=83)
        ci = opdyke2007_ci(r, hac_adjust=False)
        assert ci.bandwidth_selection is None
        assert ci.method == "opdyke2007_iid"

    def test_clipped_path_warns(self) -> None:
        """F-1-2 remediation: negative-variance fallback must emit
        RuntimeWarning so downstream gate code can flag the case."""
        # Build a series where the Mertens-Opdyke skew term dominates.
        # Construct by mixing: a few heavy-tail observations against
        # an otherwise normal series with large positive Sharpe.
        rng = np.random.default_rng(103)
        r = rng.normal(loc=2.0, scale=1.0, size=50)
        # Inject an extreme negative outlier to produce very negative
        # skewness that, combined with large Ŝ, drives var_iid < 0.
        r = np.concatenate([r, np.array([-30.0])])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ci = opdyke2007_ci(r, hac_adjust=False)
        # Accept either successful fit or clipped fallback; only
        # assert that IF clipped, a RuntimeWarning fired.
        if ci.method == "opdyke2007_negative_variance_clipped":
            assert any(issubclass(ww.category, RuntimeWarning) for ww in w)

    def test_coverage_on_null_iid(self) -> None:
        """Monte Carlo coverage of Opdyke (no HAC) at true Sharpe=0
        on iid N(0,1). Expected ≈ 0.95."""
        rng = np.random.default_rng(89)
        true_sharpe = 0.0
        B = 300
        hits = 0
        for _ in range(B):
            r = rng.normal(0.0, 1.0, size=500)
            ci = opdyke2007_ci(r, hac_adjust=False)
            if ci.lower <= true_sharpe <= ci.upper:
                hits += 1
        coverage = hits / B
        assert 0.90 <= coverage <= 0.99, f"coverage={coverage}"


# ---------------------------------------------------------------------------
# Disagreement diagnostic (Lo iid vs Opdyke primary)
# ---------------------------------------------------------------------------


class TestLo2002Prop2EtaCI:
    def test_eta_near_one_on_iid_series(self) -> None:
        """For iid returns, η(q) → 1 so Prop-2 CI ≈ iid CI."""
        r = _iid_normal(n=10_000, mu=0.1, sigma=1.0, seed=111)
        prop2_ci = lo2002_prop2_eta_ci(r)
        iid_ci = lo2002_iid_ci(r)
        ratio = (prop2_ci.upper - prop2_ci.lower) / (iid_ci.upper - iid_ci.lower)
        assert 0.9 <= ratio <= 1.15

    def test_eta_inflates_on_positively_autocorrelated_series(self) -> None:
        """For AR(1) ρ=0.5, η(q) should exceed 1 and inflate the CI."""
        r = _ar1(n=2_000, rho=0.5, sigma_eps=1.0, seed=113) + 0.1
        prop2_ci = lo2002_prop2_eta_ci(r)
        iid_ci = lo2002_iid_ci(r)
        assert (prop2_ci.upper - prop2_ci.lower) > 1.2 * (iid_ci.upper - iid_ci.lower)

    def test_q_must_be_at_least_two(self) -> None:
        r = _iid_normal(n=500, mu=0.0, sigma=1.0, seed=117)
        with pytest.raises(ValueError, match="q must be >= 2"):
            lo2002_prop2_eta_ci(r, q=1)


class TestLoVsOpdykeDisagreement:
    def test_disagreement_flags_misspecification_on_skewed_series(self) -> None:
        """Strongly skewed series (shifted log-normal) should produce
        materially different iid-Lo vs Opdyke variances — the whole
        point of the "disagreement flags misspecification" policy in
        implementation-plan §5."""
        rng = np.random.default_rng(97)
        raw = rng.lognormal(mean=0.0, sigma=0.6, size=3_000)
        # Centre around 1 to keep Sharpe bounded.
        r = raw - raw.mean() + 0.5
        lo_ci = lo2002_iid_ci(r)
        op_ci = opdyke2007_ci(r, hac_adjust=False)
        # Variance difference > 10% is a clear misspecification signal.
        rel_diff = abs(op_ci.variance - lo_ci.variance) / lo_ci.variance
        assert rel_diff > 0.10, f"rel_diff={rel_diff}"


# ---------------------------------------------------------------------------
# Fixed-bandwidth pass-through
# ---------------------------------------------------------------------------


class TestBandwidthSelectionRecord:
    def test_fixed_bandwidth_round_trip(self) -> None:
        sel = BandwidthSelection(
            method="fixed", bandwidth=5, kernel="bartlett"
        )
        x = _iid_normal(n=200, mu=0.0, sigma=1.0, seed=101)
        _, record = nw_hac_variance(x, bandwidth=sel)
        assert record.bandwidth == 5
        assert record.method == "fixed"
