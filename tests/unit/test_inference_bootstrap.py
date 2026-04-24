"""Unit tests for Cycle-5 stationary bootstrap + Politis-White 2004.

Coverage:

- Stationary-bootstrap index distribution: each index uniform on
  ``[0, n)`` under the Politis-Romano 1994 construction.
- Block-length degenerate cases: constant series → 1, iid series
  → small, strongly autocorrelated AR(1) → larger.
- Monotonicity: AR(1) with larger |rho| yields larger PW 2004 block
  length on average.
- Circular vs stationary PW 2004 coefficients differ per PPW 2009.
- 2-D bootstrap preserves row-level cross-dependence (same index
  draws across columns).
- Reproducibility: identical seeds → identical draws.
- Input validation (ndim, finite, n bounds).
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    choose_block_length,
    politis_white_block_length,
    stationary_bootstrap,
    stationary_bootstrap_indices,
)


# ---------------------------------------------------------------------------
# Synthetic generators
# ---------------------------------------------------------------------------


def _ar1(n: int, rho: float, sigma_eps: float, seed: int, burn_in: int = 500) -> np.ndarray:
    rng = np.random.default_rng(seed)
    eps = rng.normal(0.0, sigma_eps, size=n + burn_in)
    x = np.zeros(n + burn_in, dtype=float)
    for t in range(1, n + burn_in):
        x[t] = rho * x[t - 1] + eps[t]
    return x[burn_in:]


def _iid_normal(n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).normal(0.0, 1.0, size=n)


# ---------------------------------------------------------------------------
# stationary_bootstrap_indices
# ---------------------------------------------------------------------------


class TestStationaryBootstrapIndices:

    def test_indices_in_range(self):
        rng = np.random.default_rng(0)
        idx = stationary_bootstrap_indices(100, block_length=10, rng=rng)
        assert idx.shape == (100,)
        assert idx.min() >= 0
        assert idx.max() < 100

    def test_uniform_marginal(self):
        """Marginal distribution of each sampled index is uniform.

        Politis-Romano 1994 Theorem 1: the stationary bootstrap
        sample is strictly stationary with marginal distribution
        equal to the empirical.  For index i.i.d. case this means
        P(I_t = j) = 1/n for each j and each t.
        """
        n = 50
        n_draws = 20000
        rng = np.random.default_rng(123)
        # Count occurrences of each index
        counts = np.zeros(n, dtype=int)
        for _ in range(n_draws):
            idx = stationary_bootstrap_indices(n, block_length=5, rng=rng)
            counts += np.bincount(idx, minlength=n)
        observed = counts / counts.sum()
        # Expected: 1/n for each. Chi-square-equivalent tolerance:
        # SE per cell is sqrt((1/n)(1-1/n)/(n_draws*n)) ≈ 1/n * 0.045
        # Allow 5 SE → 0.5% relative tolerance for n=50, draws=20000*n.
        np.testing.assert_allclose(observed, 1.0 / n, atol=1.5e-3)

    def test_reproducible_with_seed(self):
        rng_a = np.random.default_rng(42)
        rng_b = np.random.default_rng(42)
        idx_a = stationary_bootstrap_indices(30, block_length=3, rng=rng_a)
        idx_b = stationary_bootstrap_indices(30, block_length=3, rng=rng_b)
        np.testing.assert_array_equal(idx_a, idx_b)

    def test_block_length_1_is_iid(self):
        """block_length=1 → p=1 → every step is a fresh start → i.i.d."""
        rng = np.random.default_rng(7)
        # Run on long sequence; successive-diff distribution should
        # be ~symmetric around 0 (no +1-preferred continuation).
        idx = stationary_bootstrap_indices(10000, block_length=1.0, rng=rng)
        diffs = np.diff(idx)
        # If i.i.d. uniform, P(diff == 1 mod n) ≈ 1/n ≈ 0.0001 only.
        frac_plus_one = float((diffs == 1).mean())
        assert frac_plus_one < 0.01  # Far from pure +1 progression.

    def test_large_block_length_approaches_contiguous(self):
        """With block_length >> n, draws should be nearly contiguous blocks.

        When p = 1/block_length is small, switches are rare.
        """
        rng = np.random.default_rng(9)
        idx = stationary_bootstrap_indices(100, block_length=1000.0, rng=rng)
        # Successive +1 (mod n) should dominate.
        contiguous = ((idx[1:] - idx[:-1]) % 100 == 1).mean()
        assert contiguous > 0.95

    def test_invalid_n(self):
        rng = np.random.default_rng(0)
        with pytest.raises(ValueError, match="n must be positive"):
            stationary_bootstrap_indices(0, block_length=1.0, rng=rng)

    def test_invalid_block_length(self):
        rng = np.random.default_rng(0)
        with pytest.raises(ValueError, match="block_length must be >= 1"):
            stationary_bootstrap_indices(10, block_length=0.5, rng=rng)

    def test_n_equals_one(self):
        rng = np.random.default_rng(0)
        idx = stationary_bootstrap_indices(1, block_length=1.0, rng=rng)
        assert idx.tolist() == [0]


# ---------------------------------------------------------------------------
# politis_white_block_length
# ---------------------------------------------------------------------------


class TestPolitisWhiteBlockLength:

    def test_constant_series_returns_one(self):
        x = np.ones(200)
        sel = politis_white_block_length(x)
        assert sel.block_length == 1.0
        assert sel.method == "politis_white_2004"

    def test_iid_series_is_small(self):
        x = _iid_normal(500, seed=1)
        sel = politis_white_block_length(x)
        # For iid series PW 2004 should give a small block length —
        # the m_hat pilot cuts off quickly. Allow generous upper
        # bound since the threshold rule is noisy in finite samples.
        assert 1.0 <= sel.block_length <= 10.0

    def test_ar1_series_gives_larger_block(self):
        x_weak = _ar1(1000, rho=0.1, sigma_eps=1.0, seed=2)
        x_strong = _ar1(1000, rho=0.8, sigma_eps=1.0, seed=2)
        sel_weak = politis_white_block_length(x_weak)
        sel_strong = politis_white_block_length(x_strong)
        # Strong AR(1) → larger block length on average.
        assert sel_strong.block_length > sel_weak.block_length
        # And strong should be clearly > 1.
        assert sel_strong.block_length > 3.0

    def test_ar1_rho_monotonic_in_block_length(self):
        """Averaged across seeds, block length is increasing in |rho|."""
        rhos = [0.0, 0.3, 0.6, 0.85]
        means = []
        for rho in rhos:
            vals = []
            for seed in range(10):
                x = _ar1(800, rho=rho, sigma_eps=1.0, seed=seed)
                sel = politis_white_block_length(x)
                vals.append(sel.block_length)
            means.append(np.mean(vals))
        # Monotone nondecreasing (allow small ties due to MC noise).
        for a, b in zip(means, means[1:]):
            assert b >= a - 0.5

    def test_bootstrap_type_dispatch(self):
        x = _ar1(400, rho=0.5, sigma_eps=1.0, seed=3)
        sel_sb = politis_white_block_length(x, bootstrap_type="stationary")
        sel_cb = politis_white_block_length(x, bootstrap_type="circular")
        assert sel_sb.bootstrap_type == "stationary"
        assert sel_cb.bootstrap_type == "circular"
        # PPW 2009: CB optimal is LARGER than SB for the same series
        # because D_CB = (4/3) g(0)^2 < D_SB = 2 g(0)^2
        # → b_opt_CB / b_opt_SB = (D_SB / D_CB)^(1/3) = (3/2)^(1/3) ≈ 1.145.
        assert sel_cb.block_length > sel_sb.block_length

    def test_rejects_non_finite(self):
        x = np.array([1.0, 2.0, np.nan, 4.0])
        with pytest.raises(ValueError, match="non-finite"):
            politis_white_block_length(x)

    def test_rejects_small_n(self):
        with pytest.raises(ValueError, match="requires n >= 4"):
            politis_white_block_length([1.0, 2.0, 3.0])

    def test_unknown_bootstrap_type(self):
        x = _iid_normal(100, seed=4)
        with pytest.raises(ValueError, match="unknown bootstrap_type"):
            politis_white_block_length(x, bootstrap_type="banana")  # type: ignore[arg-type]

    def test_result_has_m_hat_and_M(self):
        x = _ar1(500, rho=0.6, sigma_eps=1.0, seed=5)
        sel = politis_white_block_length(x)
        assert sel.m_hat is not None and sel.m_hat >= 0
        assert sel.M is not None and sel.M >= 2

    def test_to_dict_roundtrip(self):
        x = _iid_normal(200, seed=6)
        sel = politis_white_block_length(x)
        d = sel.to_dict()
        assert d["method"] == "politis_white_2004"
        assert d["block_length"] == sel.block_length

    def test_choose_block_length_multivariate(self):
        x = np.column_stack([
            _ar1(400, rho=0.2, sigma_eps=1.0, seed=10),
            _ar1(400, rho=0.8, sigma_eps=1.0, seed=11),
        ])
        sel = choose_block_length(x)
        # Max across columns should exceed the weak-column per-column
        # block length — exactness is noisy, so just assert >= weaker.
        sel_weak = politis_white_block_length(x[:, 0])
        assert sel.block_length >= sel_weak.block_length - 1e-9

    def test_choose_block_length_rejects_3d(self):
        x = np.zeros((10, 3, 2))
        with pytest.raises(ValueError, match="1-D or 2-D"):
            choose_block_length(x)


# ---------------------------------------------------------------------------
# stationary_bootstrap high-level
# ---------------------------------------------------------------------------


class TestStationaryBootstrap:

    def test_shapes_1d(self):
        x = _iid_normal(50, seed=0)
        rng = np.random.default_rng(0)
        samples, sel = stationary_bootstrap(
            x, n_bootstrap=7, block_length=4.0, rng=rng
        )
        assert samples.shape == (7, 50)
        assert sel.method == "fixed"

    def test_shapes_2d(self):
        x = np.column_stack([_iid_normal(40, seed=i) for i in range(3)])
        rng = np.random.default_rng(1)
        samples, _ = stationary_bootstrap(
            x, n_bootstrap=5, block_length=3.0, rng=rng
        )
        assert samples.shape == (5, 40, 3)

    def test_cross_column_dependence_preserved(self):
        """Same index draw applied across all columns of 2-D input.

        Hansen 2005 §2.1 requires this for SPA correctness.  Test:
        if column j is a deterministic function of column 0, the
        same relationship holds in each bootstrap replicate.
        """
        rng_seed = 99
        base = _iid_normal(60, seed=rng_seed)
        derived = 2.0 * base + 1.0
        x = np.column_stack([base, derived])
        rng = np.random.default_rng(0)
        samples, _ = stationary_bootstrap(
            x, n_bootstrap=3, block_length=2.0, rng=rng
        )
        np.testing.assert_allclose(samples[:, :, 1], 2.0 * samples[:, :, 0] + 1.0)

    def test_mean_estimate_consistent(self):
        """Bootstrap mean of resampled series ≈ sample mean."""
        n = 500
        x = _iid_normal(n, seed=42)
        rng = np.random.default_rng(0)
        samples, _ = stationary_bootstrap(
            x, n_bootstrap=500, block_length=5.0, rng=rng
        )
        boot_means = samples.mean(axis=1)
        # Mean of bootstrap means ≈ sample mean.
        np.testing.assert_allclose(boot_means.mean(), x.mean(), atol=0.05)

    def test_auto_block_length_when_none(self):
        x = _ar1(300, rho=0.5, sigma_eps=1.0, seed=0)
        rng = np.random.default_rng(0)
        samples, sel = stationary_bootstrap(x, n_bootstrap=3, rng=rng)
        assert sel.method == "politis_white_2004"
        assert sel.block_length >= 1.0
        assert samples.shape == (3, 300)

    def test_rejects_invalid_block_length(self):
        x = _iid_normal(20, seed=0)
        with pytest.raises(ValueError, match="block_length must be >= 1"):
            stationary_bootstrap(x, n_bootstrap=1, block_length=0.5)

    def test_rejects_invalid_n_bootstrap(self):
        x = _iid_normal(20, seed=0)
        with pytest.raises(ValueError, match="n_bootstrap must be >= 1"):
            stationary_bootstrap(x, n_bootstrap=0, block_length=2.0)

    def test_rejects_short_series(self):
        with pytest.raises(ValueError, match="requires n >= 2"):
            stationary_bootstrap(
                np.array([1.0]), n_bootstrap=1, block_length=1.0
            )

    def test_rejects_3d(self):
        x = np.zeros((10, 2, 3))
        with pytest.raises(ValueError, match="1-D or 2-D"):
            stationary_bootstrap(x, n_bootstrap=1, block_length=1.0)

    def test_reproducible_with_generator(self):
        x = _iid_normal(50, seed=0)
        s1, _ = stationary_bootstrap(
            x, n_bootstrap=3, block_length=2.0, rng=np.random.default_rng(777)
        )
        s2, _ = stationary_bootstrap(
            x, n_bootstrap=3, block_length=2.0, rng=np.random.default_rng(777)
        )
        np.testing.assert_array_equal(s1, s2)


# ---------------------------------------------------------------------------
# BlockLengthSelection dataclass
# ---------------------------------------------------------------------------


class TestBlockLengthSelection:

    def test_frozen(self):
        sel = BlockLengthSelection(
            method="fixed",
            block_length=3.0,
            bootstrap_type="stationary",
        )
        with pytest.raises(Exception):
            sel.block_length = 5.0  # type: ignore[misc]

    def test_to_dict_keys(self):
        sel = BlockLengthSelection(
            method="fixed",
            block_length=3.0,
            bootstrap_type="stationary",
            m_hat=5,
            M=10,
            notes="test",
        )
        d = sel.to_dict()
        assert set(d.keys()) == {
            "method",
            "block_length",
            "bootstrap_type",
            "m_hat",
            "M",
            "notes",
        }
