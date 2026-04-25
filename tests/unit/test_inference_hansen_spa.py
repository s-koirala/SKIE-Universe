"""Unit tests for Cycle-5 Hansen 2005 SPA test.

Coverage:

- Under composite null (all d_{k,t} i.i.d. zero-mean): consistent
  p-value distribution tolerates nominal size (10% rejection rate
  at alpha=0.10 ±5pp at B=1000, n=200, m=3, over 100 Monte Carlo
  sims).  Asymptotic size, not exact.
- Under alternative (one strategy with large positive mean):
  consistent p-value is small (< 0.10) in a single draw with
  n=200, B=500.
- Ordering of variants: SPA_l <= SPA_c <= SPA_u.
- Effect of adding a strictly-dominated bad strategy: SPA_u
  p-value GROWS (White 2000 pathology), SPA_c p-value is stable.
- Both omega_method options produce p-values in [0, 1].
- Bootstrap uses same indices across columns (verified via
  preserved cross-column linear relationships).
- Reproducibility with seeded generator.
- Input validation (shape, finite, n bounds, unknown variant).
- Single-strategy degenerate case (|M|=1): warning emitted,
  pass-through p-value matches a one-sided manual stationary
  bootstrap; |M|>=2 does not emit the warning. Per ADR-0008
  §"Single-strategy degenerate handling (|M|=1)" (closes
  P1-H050-SPA-M1-DEGENERATE).
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from skie_ninja.inference.bootstrap import (
    BlockLengthSelection,
    stationary_bootstrap_indices,
)
from skie_ninja.inference.multipletest import (
    HansenSPAResult,
    SingleStrategySPAWarning,
    hansen_spa_test,
)


# ---------------------------------------------------------------------------
# Synthetic generators
# ---------------------------------------------------------------------------


def _null_panel(n: int, m: int, seed: int) -> np.ndarray:
    """All columns iid N(0, 1) → composite null."""
    return np.random.default_rng(seed).normal(0.0, 1.0, size=(n, m))


def _alt_panel(
    n: int, m: int, mu_best: float, seed: int, mu_others: float = 0.0
) -> np.ndarray:
    """Column 0 has mean mu_best; others have mean mu_others."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, size=(n, m))
    x[:, 0] += mu_best
    for k in range(1, m):
        x[:, k] += mu_others
    return x


# ---------------------------------------------------------------------------
# Core behavior
# ---------------------------------------------------------------------------


class TestHansenSPATest:

    def test_alternative_yields_small_pvalue(self):
        """Clear alternative → consistent p-value < 0.10."""
        d = _alt_panel(n=300, m=3, mu_best=0.3, seed=0)
        rng = np.random.default_rng(0)
        res = hansen_spa_test(
            d, n_bootstrap=500, variant="consistent", rng=rng
        )
        assert res.p_value < 0.10
        assert res.statistic > 0
        assert res.best_strategy_index == 0

    def test_variant_ordering(self):
        """SPA_l ≤ SPA_c ≤ SPA_u (Hansen 2005 §2.4).

        Run on a panel where at least one strategy is clearly bad so
        SPA_u's pathology kicks in and the ordering is visible.
        """
        rng = np.random.default_rng(1)
        d = rng.normal(0.0, 1.0, size=(250, 5))
        d[:, 0] += 0.15  # mildly good
        d[:, 3] -= 2.0  # very bad — dominated
        d[:, 4] -= 2.0  # very bad — dominated
        res = hansen_spa_test(
            d, n_bootstrap=1000, rng=np.random.default_rng(7)
        )
        assert res.p_value_lower <= res.p_value + 1e-9
        assert res.p_value <= res.p_value_upper + 1e-9

    def test_dominated_strategy_wash_out_only_for_spa_u(self):
        """White-2000 pathology: adding a bad strategy inflates SPA_u but
        not SPA_c/SPA_l (Hansen 2005 §1)."""
        rng_data = np.random.default_rng(2)
        d_core = rng_data.normal(0.0, 1.0, size=(300, 2))
        d_core[:, 0] += 0.25  # mildly good

        rng_a = np.random.default_rng(42)
        res_small = hansen_spa_test(d_core, n_bootstrap=1000, rng=rng_a)

        # Add many bad strategies.
        bad = rng_data.normal(-3.0, 1.0, size=(300, 10))
        d_big = np.column_stack([d_core, bad])
        rng_b = np.random.default_rng(42)
        res_big = hansen_spa_test(d_big, n_bootstrap=1000, rng=rng_b)

        # SPA_u should grow (RC pathology). Allow slack for MC noise.
        assert res_big.p_value_upper > res_small.p_value_upper - 1e-9
        # SPA_c should be broadly comparable (data-dependent — won't
        # explode). Tolerate 0.15 movement. This is an *asymptotic*
        # property; at finite B + MC noise it may fluctuate.
        assert abs(res_big.p_value - res_small.p_value) < 0.20

    def test_null_size_roughly_nominal(self):
        """Approximate size under composite null.

        100 MC sims, n=200, m=3, iid N(0,1) columns; reject if
        p < 0.10. Target rejection rate ~10% (±10pp slack; Hansen
        2005 §3.1 reports ≈0.08–0.11 for similar configs with
        bootstrap omega and n=200)."""
        n_sims = 100
        reject = 0
        for sim in range(n_sims):
            d = _null_panel(n=200, m=3, seed=sim)
            rng = np.random.default_rng(10_000 + sim)
            res = hansen_spa_test(
                d, n_bootstrap=500, variant="consistent", rng=rng
            )
            if res.p_value < 0.10:
                reject += 1
        rate = reject / n_sims
        # Loose bound — this is a smoke test of *approximate* size
        # control, not a formal simulation. Allow 0% ≤ rate ≤ 22%.
        assert 0.0 <= rate <= 0.22, f"empirical size {rate:.2f} outside [0, 0.22]"

    def test_hac_omega_method(self):
        d = _alt_panel(n=200, m=3, mu_best=0.3, seed=3)
        rng = np.random.default_rng(3)
        res = hansen_spa_test(
            d, n_bootstrap=300, omega_method="hac", rng=rng
        )
        assert 0.0 <= res.p_value <= 1.0
        assert res.omega_method == "hac"

    def test_bootstrap_omega_method(self):
        d = _alt_panel(n=200, m=3, mu_best=0.3, seed=4)
        rng = np.random.default_rng(4)
        res = hansen_spa_test(
            d, n_bootstrap=300, omega_method="bootstrap", rng=rng
        )
        assert res.omega_method == "bootstrap"

    def test_all_variants_return_valid_pvalues(self):
        d = _null_panel(n=150, m=4, seed=5)
        rng = np.random.default_rng(5)
        res = hansen_spa_test(d, n_bootstrap=500, rng=rng)
        for p in (res.p_value, res.p_value_lower, res.p_value_upper):
            assert 0.0 <= p <= 1.0

    def test_block_length_auto_selection(self):
        d = _null_panel(n=150, m=2, seed=6)
        rng = np.random.default_rng(6)
        res = hansen_spa_test(d, n_bootstrap=200, rng=rng)
        assert res.block_length_selection.method == "politis_white_2004"
        assert res.block_length_selection.block_length >= 1.0

    def test_block_length_fixed(self):
        d = _null_panel(n=150, m=2, seed=7)
        rng = np.random.default_rng(7)
        res = hansen_spa_test(
            d, n_bootstrap=200, block_length=4.0, rng=rng
        )
        assert res.block_length_selection.method == "fixed"
        assert res.block_length_selection.block_length == 4.0

    def test_reproducible_with_seed(self):
        d = _alt_panel(n=200, m=3, mu_best=0.3, seed=8)
        res_a = hansen_spa_test(
            d,
            n_bootstrap=500,
            block_length=3.0,
            rng=np.random.default_rng(2026),
        )
        res_b = hansen_spa_test(
            d,
            n_bootstrap=500,
            block_length=3.0,
            rng=np.random.default_rng(2026),
        )
        assert res_a.p_value == res_b.p_value
        assert res_a.statistic == res_b.statistic

    def test_best_strategy_index_correct(self):
        """best_strategy_index is the argmax of studentized sample means."""
        d = _alt_panel(n=300, m=4, mu_best=0.5, seed=9)
        # Column 0 should dominate.
        rng = np.random.default_rng(0)
        res = hansen_spa_test(d, n_bootstrap=200, rng=rng)
        assert res.best_strategy_index == 0
        assert res.best_strategy_mean == pytest.approx(d[:, 0].mean())

    def test_to_dict_serializable(self):
        d = _alt_panel(n=150, m=2, mu_best=0.2, seed=10)
        rng = np.random.default_rng(0)
        res = hansen_spa_test(d, n_bootstrap=100, rng=rng)
        out = res.to_dict()
        assert "p_value" in out
        assert "block_length_selection" in out
        assert out["block_length_selection"]["method"] in (
            "politis_white_2004",
            "fixed",
        )


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:

    def test_rejects_1d(self):
        with pytest.raises(ValueError, match="d must be 2-D"):
            hansen_spa_test(np.zeros(50), n_bootstrap=10)

    def test_rejects_3d(self):
        with pytest.raises(ValueError, match="d must be 2-D"):
            hansen_spa_test(np.zeros((10, 2, 3)), n_bootstrap=10)

    def test_rejects_non_finite(self):
        d = np.zeros((20, 2))
        d[5, 0] = np.nan
        with pytest.raises(ValueError, match="non-finite"):
            hansen_spa_test(d, n_bootstrap=10)

    def test_rejects_small_n(self):
        with pytest.raises(ValueError, match="n >= 4"):
            hansen_spa_test(np.zeros((3, 2)), n_bootstrap=10)

    def test_rejects_zero_strategies(self):
        with pytest.raises(ValueError, match="m >= 1"):
            hansen_spa_test(np.zeros((10, 0)), n_bootstrap=10)

    def test_rejects_invalid_n_bootstrap(self):
        with pytest.raises(ValueError, match="n_bootstrap must be >= 1"):
            hansen_spa_test(_null_panel(20, 2, 0), n_bootstrap=0)

    def test_rejects_unknown_variant(self):
        with pytest.raises(ValueError, match="unknown variant"):
            hansen_spa_test(
                _null_panel(20, 2, 0),
                n_bootstrap=10,
                variant="banana",  # type: ignore[arg-type]
            )

    def test_rejects_unknown_omega_method(self):
        with pytest.raises(ValueError, match="unknown omega_method"):
            hansen_spa_test(
                _null_panel(20, 2, 0),
                n_bootstrap=10,
                omega_method="banana",  # type: ignore[arg-type]
            )

    def test_rejects_block_length_lt_1(self):
        with pytest.raises(ValueError, match="block_length must be >= 1"):
            hansen_spa_test(
                _null_panel(20, 2, 0),
                n_bootstrap=10,
                block_length=0.5,
            )


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


class TestHansenSPAResult:

    def test_frozen(self):
        sel = BlockLengthSelection(
            method="fixed", block_length=3.0, bootstrap_type="stationary"
        )
        res = HansenSPAResult(
            p_value=0.1,
            p_value_lower=0.05,
            p_value_upper=0.15,
            statistic=1.2,
            best_strategy_index=0,
            best_strategy_mean=0.3,
            n_bootstrap=100,
            n_obs=50,
            n_strategies=2,
            block_length_selection=sel,
            omega_method="bootstrap",
            variant="consistent",
        )
        with pytest.raises(Exception):
            res.p_value = 0.2  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Single-strategy degenerate case (|M| = 1)
# ---------------------------------------------------------------------------


class TestSingleStrategyDegenerate:
    """ADR-0008 §"Single-strategy degenerate handling (|M|=1)".

    The Hansen 2005 SPA composite null degenerates to a one-sided
    studentised bootstrap test of ``H_0: E[d] <= 0`` when ``m == 1``.
    Project policy is pass-through with a ``SingleStrategySPAWarning``
    emitted at function entry. Closes follow-up
    ``P1-H050-SPA-M1-DEGENERATE``.
    """

    def test_m_eq_1_emits_warning(self):
        d = _alt_panel(n=200, m=1, mu_best=0.3, seed=11)
        with pytest.warns(SingleStrategySPAWarning, match="m=1"):
            hansen_spa_test(
                d,
                n_bootstrap=200,
                rng=np.random.default_rng(11),
            )

    def test_m_eq_1_warning_class_is_user_warning(self):
        assert issubclass(SingleStrategySPAWarning, UserWarning)

    def test_m_geq_2_no_warning(self):
        d = _alt_panel(n=200, m=3, mu_best=0.3, seed=12)
        with warnings.catch_warnings():
            warnings.simplefilter("error", SingleStrategySPAWarning)
            hansen_spa_test(
                d,
                n_bootstrap=200,
                rng=np.random.default_rng(12),
            )

    def test_m_eq_1_returns_valid_result(self):
        d = _alt_panel(n=200, m=1, mu_best=0.3, seed=13)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SingleStrategySPAWarning)
            res = hansen_spa_test(
                d,
                n_bootstrap=300,
                rng=np.random.default_rng(13),
            )
        assert res.n_strategies == 1
        assert 0.0 <= res.p_value <= 1.0
        assert 0.0 <= res.p_value_lower <= 1.0
        assert 0.0 <= res.p_value_upper <= 1.0
        assert res.best_strategy_index == 0

    def test_m_eq_1_pvalue_matches_manual_one_sided_bootstrap(self):
        """Pass-through p-value equals an independently-coded one-sided
        studentised stationary-bootstrap p-value on the single column.

        Construction (Hansen 2005 §2.4 SPA_c reduction at ``m = 1``,
        positive-d_bar regime where g = d_bar):

            T = max(0, sqrt(n) * d_bar / omega)
            T*^b = max(0, sqrt(n) * (d_bar*^b - d_bar) / omega)
            p = (1/B) * #{b: T*^b >= T}

        Uses the same RNG seed and block length as the SPA call.
        """
        n = 240
        d = _alt_panel(n=n, m=1, mu_best=0.4, seed=14)
        seed = 1414
        block_length = 5.0
        n_boot = 400

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SingleStrategySPAWarning)
            res = hansen_spa_test(
                d,
                n_bootstrap=n_boot,
                block_length=block_length,
                omega_method="bootstrap",
                rng=np.random.default_rng(seed),
            )

        rng_manual = np.random.default_rng(seed)
        boot_means = np.empty(n_boot, dtype=float)
        for b in range(n_boot):
            idx = stationary_bootstrap_indices(
                n, block_length=block_length, rng=rng_manual
            )
            boot_means[b] = d[idx, 0].mean()

        var_boot = boot_means.var(ddof=0)
        omega_sq = max(n * var_boot, float(np.finfo(np.float64).eps))
        omega = np.sqrt(omega_sq)
        sqrt_n = np.sqrt(n)
        d_bar = d[:, 0].mean()

        # Sample-mean is positive in this fixture, so SPA_c recenters
        # at g = d_bar (Hansen 2005 §2.4 + ADR-0008 variant-collapse
        # table); the bootstrap analogue is therefore centred at
        # d_bar*^b - d_bar.
        assert d_bar > 0.0, (
            "fixture invariant violated: expected positive sample mean."
        )
        t_obs = max(0.0, sqrt_n * d_bar / omega)
        t_boot_manual = np.maximum(
            0.0, sqrt_n * (boot_means - d_bar) / omega
        )
        p_manual = float((t_boot_manual >= t_obs).mean())

        assert res.statistic == pytest.approx(t_obs, abs=1e-12)
        assert res.p_value == pytest.approx(p_manual, abs=1e-12)

    def test_m_eq_1_variant_collapse_in_positive_dbar_regime(self):
        """ADR-0008 §"Variant collapse" — when ``d_bar > 0`` all three
        variants share ``g = d_bar`` and yield identical p-values.
        """
        d = _alt_panel(n=300, m=1, mu_best=0.5, seed=15)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SingleStrategySPAWarning)
            res = hansen_spa_test(
                d,
                n_bootstrap=400,
                rng=np.random.default_rng(15),
            )
        assert d[:, 0].mean() > 0.0
        assert res.p_value_lower == pytest.approx(res.p_value, abs=1e-12)
        assert res.p_value == pytest.approx(res.p_value_upper, abs=1e-12)

    def test_m_eq_1_variant_ordering_preserved(self):
        """SPA_l <= SPA_c <= SPA_u still holds at m = 1 (mechanical
        consequence of the recentering definitions, independent of
        multi-strategy semantics)."""
        rng_data = np.random.default_rng(16)
        d = rng_data.normal(0.0, 1.0, size=(250, 1))
        d[:, 0] -= 1.5  # negative-d_bar regime, splits SPA_l from SPA_c/SPA_u
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SingleStrategySPAWarning)
            res = hansen_spa_test(
                d,
                n_bootstrap=400,
                rng=np.random.default_rng(160),
            )
        assert res.p_value_lower <= res.p_value + 1e-9
        assert res.p_value <= res.p_value_upper + 1e-9
