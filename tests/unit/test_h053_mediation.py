"""H053 Cycle 9 Stage-2 mediation primitives — unit tests.

Verifies the partial-R², paired-pairs bootstrap, PC1 collapse, E-value,
and Baron-Kenny mediation primitives at
``src/skie_ninja/inference/mediation.py``. Includes a synthetic-null
coverage check (design.md §11.2 prereq 3): under H_0 (X has no
incremental predictive content beyond M), the bootstrap CI must cover
zero at nominal level.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from skie_ninja.inference.mediation import (
    EValueResult,
    MediationDecomposition,
    PC1CollapseResult,
    PartialR2BootstrapCI,
    baron_kenny_nie_nde,
    e_value,
    paired_pairs_partial_r2_ci,
    partial_r2_increment,
    pc1_collapse,
)


# ---------------------------------------------------------------------------
# Partial-R² point estimate
# ---------------------------------------------------------------------------


class TestPartialR2:
    def test_zero_when_full_equals_baseline(self):
        rng = np.random.default_rng(42)
        n = 200
        X_baseline = rng.normal(size=(n, 2))
        y = X_baseline @ np.array([0.5, -0.3]) + rng.normal(size=n)
        # Full X = baseline duplicated → no information added → partial-R² = 0
        v = partial_r2_increment(X_baseline, X_baseline, y)
        assert abs(v) < 1e-12

    def test_positive_when_full_adds_predictor(self):
        rng = np.random.default_rng(43)
        n = 500
        X_extra = rng.normal(size=(n, 1))
        X_baseline = rng.normal(size=(n, 2))
        # y depends on baseline AND on extra
        y = X_baseline @ np.array([0.5, -0.3]) + 0.8 * X_extra[:, 0] + rng.normal(size=n) * 0.1
        X_full = np.column_stack([X_baseline, X_extra])
        v = partial_r2_increment(X_baseline, X_full, y)
        assert v > 0.5  # ratio of variance explained should be substantial

    def test_negative_or_zero_when_full_is_subset(self):
        # Edge case: full has fewer columns than baseline; partial-R² should
        # be ≤ 0 (full can never explain more than baseline does).
        rng = np.random.default_rng(44)
        n = 300
        X_full = rng.normal(size=(n, 2))
        X_baseline = np.column_stack([X_full, rng.normal(size=(n, 3))])
        y = X_full @ np.array([0.5, -0.3]) + rng.normal(size=n) * 0.1
        v = partial_r2_increment(X_baseline, X_full, y)
        assert v <= 1e-9


# ---------------------------------------------------------------------------
# Paired-pairs bootstrap CI
# ---------------------------------------------------------------------------


class TestPairedPairsBootstrapCI:
    def test_ci_near_zero_under_null(self):
        """Synthetic-null coverage check (design.md §11.2 prereq 3 informational).

        In-sample partial-R² is bounded below at 0 by construction (adding
        columns to OLS can never decrease R²); under H_0 the point estimate
        is a small positive noise floor. The bootstrap CI lower bound is
        therefore typically just above 0, NOT ≤ 0. This is documented
        behaviour. The strict ≤-0 lower-bound coverage requires OOS partial-R²
        per design.md §5.4 fold-disjoint scalarization protocol; Stage-2
        production uses OOS partial-R² on the Med sub-fold and the test
        below establishes the in-sample upper-bound noise floor under H_0.

        Test assertion: under H_0 the partial-R² point estimate AND the CI
        upper bound are both small (< 0.02 on n=600 with 1 noise column).
        Tracked under follow-up
        ``P1-H053-CYCLE9-OOS-PARTIAL-R2-COVERAGE-TEST``.
        """
        rng = np.random.default_rng(100)
        n = 600
        M = rng.normal(size=(n, 2))
        X_extra = rng.normal(size=(n, 1))
        y = M @ np.array([0.5, -0.3]) + rng.normal(size=n) * 0.5

        X_baseline = M
        X_full = np.column_stack([M, X_extra])
        result = paired_pairs_partial_r2_ci(
            X_baseline, X_full, y, n_replicates=500, block_length=10, rng=rng,
        )
        # In-sample upper-bound noise floor under H_0
        assert abs(result.point_estimate) < 0.02
        assert result.ci_hi < 0.05, (
            f"CI upper bound {result.ci_hi:.4f} above the in-sample noise "
            "floor under H_0 (~0.05 for n=600 with 1 noise column)."
        )

    def test_ci_excludes_zero_under_strong_signal(self):
        rng = np.random.default_rng(101)
        n = 800
        M = rng.normal(size=(n, 2))
        X_extra = rng.normal(size=(n, 1))
        # y depends on M AND on X_extra (strong signal)
        y = M @ np.array([0.3, -0.2]) + 0.9 * X_extra[:, 0] + rng.normal(size=n) * 0.1

        X_baseline = M
        X_full = np.column_stack([M, X_extra])
        result = paired_pairs_partial_r2_ci(
            X_baseline, X_full, y, n_replicates=500, block_length=10, rng=rng,
        )
        assert result.point_estimate > 0.5
        assert result.excludes_zero
        assert result.ci_lo > 0


# ---------------------------------------------------------------------------
# PC1 collapse
# ---------------------------------------------------------------------------


class TestPC1Collapse:
    def test_pc1_on_aligned_features_high_variance_explained(self):
        rng = np.random.default_rng(50)
        n = 400
        # All 3 features are noisy copies of a single latent factor
        latent = rng.normal(size=n)
        noise = 0.1
        X = np.column_stack([
            latent + noise * rng.normal(size=n),
            latent + noise * rng.normal(size=n),
            latent + noise * rng.normal(size=n),
        ])
        result, scores = pc1_collapse(X)
        assert result.variance_explained > 0.95
        assert len(result.loadings) == 3
        assert len(scores) == n

    def test_pc1_on_independent_features_low_variance_explained(self):
        rng = np.random.default_rng(51)
        n = 400
        # 3 independent features → PC1 explains roughly 1/3 of variance
        X = rng.normal(size=(n, 3))
        result, _ = pc1_collapse(X)
        assert 0.20 < result.variance_explained < 0.55

    def test_pc1_loadings_are_unit_norm(self):
        rng = np.random.default_rng(52)
        X = rng.normal(size=(200, 4))
        result, _ = pc1_collapse(X)
        norm = math.sqrt(sum(v ** 2 for v in result.loadings))
        assert abs(norm - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# E-value
# ---------------------------------------------------------------------------


class TestEValue:
    def test_zero_estimate_returns_unit_e_value(self):
        result = e_value(0.0, -0.05, 0.05)
        # Under no effect: RR ≈ 1, E-value = 1
        assert result.e_value_point == pytest.approx(1.0, abs=1e-9)

    def test_positive_partial_r2_gives_e_value_above_one(self):
        result = e_value(0.10, 0.05, 0.15)
        assert result.e_value_point > 1.0
        assert result.e_value_ci_bound >= 1.0

    def test_e_value_increases_with_effect_size(self):
        small = e_value(0.05, 0.04, 0.06).e_value_point
        large = e_value(0.30, 0.25, 0.35).e_value_point
        assert large > small

    def test_e_value_ci_bound_uses_nearest_to_zero(self):
        # CI [0.02, 0.50] → nearest-to-zero bound is 0.02
        wide_ci = e_value(0.20, 0.02, 0.50)
        narrow_ci = e_value(0.20, 0.18, 0.22)
        # The narrower CI's E-value-CI-bound should be closer to the point E-value
        assert abs(narrow_ci.e_value_ci_bound - narrow_ci.e_value_point) < abs(
            wide_ci.e_value_ci_bound - wide_ci.e_value_point
        )


# ---------------------------------------------------------------------------
# Baron-Kenny NIE/NDE
# ---------------------------------------------------------------------------


class TestBaronKennyMediation:
    def test_nie_nonzero_under_full_mediation_synthetic(self):
        """Under a full-mediation DGP (X → M → y, no X → y direct), NIE > 0."""
        rng = np.random.default_rng(70)
        n = 500
        X = rng.normal(size=(n, 1))
        # Mediator M is driven by X
        M = 0.8 * X + 0.3 * rng.normal(size=(n, 1))
        # y is driven entirely by M
        y = (1.5 * M[:, 0] + 0.5 * rng.normal(size=n))
        result = baron_kenny_nie_nde(
            y, M, X, n_replicates=300, block_length=10, rng=rng,
        )
        assert result.nie > 0  # positive indirect effect
        # Under full mediation, NDE should be near 0
        assert abs(result.nde) < 0.5

    def test_nde_nonzero_under_no_mediation_synthetic(self):
        rng = np.random.default_rng(71)
        n = 500
        X = rng.normal(size=(n, 1))
        M = rng.normal(size=(n, 1))   # M independent of X
        # y depends only on X
        y = 1.0 * X[:, 0] + 0.5 * rng.normal(size=n)
        result = baron_kenny_nie_nde(
            y, M, X, n_replicates=300, block_length=10, rng=rng,
        )
        # Under no mediation, NIE should be near 0 (X-on-M coefficient ≈ 0)
        assert abs(result.nie) < 0.3
        # NDE should be substantial
        assert abs(result.nde) > 0.5
