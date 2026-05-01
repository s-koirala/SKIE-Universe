"""Tests for src/skie_ninja/inference/power.py — H053 design.md §11.2 prereq 19.

Verifies:
  - Lo 2002 §III parametric variance formula matches eq. 4 / eq. 14 / Prop. 2
    in their Gaussian, non-Gaussian, and AR(1) limiting forms.
  - `required_n` and `mde` are mutual inverses up to integer rounding.
  - Asymptotic large-sample limit `s_min ≈ (z_α + z_β)/√n` recovered when SR
    is small (so the kurtosis correction term `(γ_4-1)·SR²/4` is negligible).
  - The H053 option-3 conservative-prior pin (`ρ=0, γ_4=3`) produces finite,
    bounded `n` and MDE values for the design.md §9 representative regimes
    (n=252 single-instrument, n=504 ES+NQ pooled).
  - Sidecar writer round-trips the `PowerCalibration` record schema and
    matches the design.md §9 yaml `power:` block keys.

Reference: research/01_hypothesis_register/H053/design.md §9 + §11.2 prereq 19;
[research/01_hypothesis_register/H053/power_calibration_addendum_2026-04-30.md]
(option-3 election).
"""

from __future__ import annotations

import json
import math

import pytest
from scipy import stats as scipy_stats

from skie_ninja.inference.power import (
    PowerCalibration,
    lo2002_sr_se,
    lo2002_sr_variance,
    mde,
    required_n,
    write_power_calibration_sidecar,
)


# ---------------------------------------------------------------------------
# Lo 2002 §III parametric variance formula
# ---------------------------------------------------------------------------


class TestLo2002Variance:
    def test_iid_gaussian_matches_eq4(self):
        """Lo 2002 eq. 4 (iid Gaussian): Var(Ŝ) = (1 + Ŝ²/2) / T.

        Recovered when γ_3 = 0, γ_4 = 3, ρ = 0.
        """
        sr = 1.5
        n = 100
        expected = (1.0 + 0.5 * sr * sr) / n
        got = lo2002_sr_variance(sr, n, skewness=0.0, kurtosis=3.0, ar1_rho=0.0)
        assert math.isclose(got, expected, rel_tol=1e-12)

    def test_eq14_general_iid_with_skew_and_kurt(self):
        """Lo 2002 eq. 14: Var(Ŝ) = (1 - γ_3·Ŝ + (γ_4-1)·Ŝ²/4) / T."""
        sr, n = 1.0, 100
        sk, kt = 0.7, 5.0
        expected = (1.0 - sk * sr + (kt - 1.0) * sr * sr / 4.0) / n
        got = lo2002_sr_variance(sr, n, skewness=sk, kurtosis=kt, ar1_rho=0.0)
        assert math.isclose(got, expected, rel_tol=1e-12)

    def test_skewness_subtracts_at_positive_sr(self):
        """Positive skew + positive SR → smaller variance per eq. 14 sign."""
        sr, n = 1.0, 100
        v_no_skew = lo2002_sr_variance(sr, n, skewness=0.0, kurtosis=3.0)
        v_pos_skew = lo2002_sr_variance(sr, n, skewness=1.0, kurtosis=3.0)
        assert v_pos_skew < v_no_skew

    def test_leptokurtosis_inflates_variance(self):
        """Heavy tails (γ_4 > 3) inflate variance per eq. 14 (γ_4-1) coef."""
        sr, n = 1.0, 100
        v_gauss = lo2002_sr_variance(sr, n, kurtosis=3.0)
        v_lepto = lo2002_sr_variance(sr, n, kurtosis=6.0)
        assert v_lepto > v_gauss

    def test_ar1_inflation_factor(self):
        """Bartlett HAC at lag 1: Var_HAC = Var_iid · (1+ρ)/(1-ρ)."""
        sr, n, rho = 1.0, 100, 0.5
        v_iid = lo2002_sr_variance(sr, n, ar1_rho=0.0)
        v_hac = lo2002_sr_variance(sr, n, ar1_rho=rho)
        expected_ratio = (1.0 + rho) / (1.0 - rho)
        assert math.isclose(v_hac / v_iid, expected_ratio, rel_tol=1e-12)

    def test_negative_ar1_deflates_variance(self):
        """Negative ρ (mean-reverting) deflates variance via (1+ρ)/(1-ρ) < 1."""
        sr, n = 1.0, 100
        v_iid = lo2002_sr_variance(sr, n, ar1_rho=0.0)
        v_neg = lo2002_sr_variance(sr, n, ar1_rho=-0.3)
        assert v_neg < v_iid

    def test_n_too_small_raises(self):
        with pytest.raises(ValueError, match="n >= 3"):
            lo2002_sr_variance(1.0, 2)

    def test_ar1_at_unit_raises(self):
        with pytest.raises(ValueError, match=r"ar1_rho"):
            lo2002_sr_variance(1.0, 100, ar1_rho=1.0)
        with pytest.raises(ValueError, match=r"ar1_rho"):
            lo2002_sr_variance(1.0, 100, ar1_rho=-1.0)

    def test_se_is_sqrt_variance(self):
        sr, n = 0.5, 252
        v = lo2002_sr_variance(sr, n)
        se = lo2002_sr_se(sr, n)
        assert math.isclose(se * se, v, rel_tol=1e-12)

    def test_negative_variance_guard_raises(self):
        """Mertens-Opdyke iid-form regime invalidity: when γ_3 · Ŝ exceeds
        `1 + (γ_4 − 1)·Ŝ²/4`, the variance formula gives a negative value
        and the implementation must raise rather than silently propagate.

        Trigger: skewness=2, kurtosis=3, sr=0.6 →
        iid_term = 1 - 2·0.6 + 0.5·0.36/4 = 1 - 1.2 + 0.045 = -0.155 < 0.
        """
        with pytest.raises(ValueError, match="variance is negative"):
            lo2002_sr_variance(0.6, 100, skewness=2.0, kurtosis=3.0)

    def test_raise_messages_are_ascii_only(self):
        """Windows cp1252 portability (F-1-6 regression check). Raise
        messages must not contain non-ASCII characters that crash on
        Windows-default-encoding stdout/loggers.
        """
        try:
            lo2002_sr_variance(0.6, 100, skewness=2.0, kurtosis=3.0)
        except ValueError as exc:
            # If non-ASCII bytes sneak in, .encode("ascii") will raise.
            str(exc).encode("ascii")


# ---------------------------------------------------------------------------
# required_n solver
# ---------------------------------------------------------------------------


class TestRequiredN:
    def test_large_sample_asymptotic_recovered(self):
        """At small s_min, kurtosis term `(γ_4-1)·s²/4` ≪ 1, so

            s_min · sqrt(n) ≈ z_α + z_β
            n ≈ ((z_α + z_β) / s_min)²

        Tolerance 5% to absorb the s²/2 finite-SR correction.
        """
        alpha, power, s = 0.05, 0.80, 0.05
        z_a = float(scipy_stats.norm.ppf(1.0 - alpha))
        z_b = float(scipy_stats.norm.ppf(power))
        n = required_n(s, alpha=alpha, target_power=power, kurtosis=3.0, ar1_rho=0.0)
        expected = ((z_a + z_b) / s) ** 2
        assert abs(n - expected) / expected < 0.05

    def test_inversion_consistency_with_mde(self):
        """required_n(mde(n)) ∈ {n-1, n, n+1}: integer rounding of a
        continuous fixed point.
        """
        for n_target in (50, 252, 504, 1000):
            s = mde(n_target, alpha=0.05, target_power=0.80, kurtosis=3.0)
            n_back = required_n(s, alpha=0.05, target_power=0.80, kurtosis=3.0)
            assert abs(n_back - n_target) <= 1, (
                f"n_target={n_target}, mde={s:.6g}, n_back={n_back}"
            )

    def test_ar1_increases_required_n(self):
        s = 0.5
        n_iid = required_n(s, ar1_rho=0.0, kurtosis=3.0)
        n_ar = required_n(s, ar1_rho=0.5, kurtosis=3.0)
        assert n_ar > n_iid

    def test_leptokurtosis_increases_required_n(self):
        s = 0.5
        n_gauss = required_n(s, kurtosis=3.0)
        n_lepto = required_n(s, kurtosis=6.0)
        assert n_lepto > n_gauss

    def test_h053_option3_pin_at_s05_intraday_realistic(self):
        """H053 option-3 pin at s_min=0.5 daily-Sharpe (a stretch target).

        Asymptotic estimate: ((1.6449 + 0.8416) / 0.5)² ≈ 24.7. Exact accounting
        for the finite-SR kurtosis correction (γ_4=3 → coefficient 0.5):

            s · √n = z_α + z_β · √(1 + s²/2)
            0.5 · √n = 1.6449 + 0.8416 · √1.125
            √n ≈ 5.075 ⇒ n ≈ 25.76 ⇒ ⌈n⌉ = 26

        The bracket [20, 30] absorbs both rounding and minor numerical
        precision in scipy's normal-quantile inversion.
        """
        n = required_n(
            0.5,
            alpha=0.05,
            target_power=0.80,
            skewness=0.0,
            kurtosis=3.0,
            ar1_rho=0.0,
            one_sided=True,
        )
        assert 20 <= n <= 30

    def test_h053_option3_pin_at_n252_full_year(self):
        """At one trading year (n=252) under option-3 pin, the achievable
        MDE should be in the daily-Sharpe band consistent with annualized
        Sharpe of 2.5±. Used to cross-validate `required_n ↔ mde` round-trip.
        """
        s = mde(252, alpha=0.05, target_power=0.80, kurtosis=3.0, ar1_rho=0.0)
        # asymptotic ≈ (1.6449 + 0.8416)/√252 ≈ 0.157; finite-SR correction ≈ +1%
        assert 0.14 < s < 0.18

    def test_pooled_n504_smaller_mde_than_n252(self):
        """ES+NQ pooled (n=504) must have smaller MDE than single-instrument
        (n=252) by approximately √2.
        """
        s_252 = mde(252, kurtosis=3.0)
        s_504 = mde(504, kurtosis=3.0)
        assert s_504 < s_252
        # Approximate √2 ratio (asymptotic; finite-SR correction is small):
        assert math.isclose(s_252 / s_504, math.sqrt(2.0), rel_tol=0.05)

    def test_negative_s_min_raises(self):
        with pytest.raises(ValueError, match="s_min"):
            required_n(-0.1)

    def test_zero_s_min_raises(self):
        with pytest.raises(ValueError, match="s_min"):
            required_n(0.0)

    def test_alpha_out_of_bound_raises(self):
        with pytest.raises(ValueError, match="alpha"):
            required_n(0.5, alpha=0.0)
        with pytest.raises(ValueError, match="alpha"):
            required_n(0.5, alpha=1.0)

    def test_power_out_of_bound_raises(self):
        with pytest.raises(ValueError, match="target_power"):
            required_n(0.5, target_power=0.0)
        with pytest.raises(ValueError, match="target_power"):
            required_n(0.5, target_power=1.0)

    def test_two_sided_requires_more_n_than_one_sided(self):
        """Two-sided test at α uses z_{α/2} > z_α, so requires more n."""
        s = 0.3
        n_one = required_n(s, alpha=0.05, one_sided=True, kurtosis=3.0)
        n_two = required_n(s, alpha=0.05, one_sided=False, kurtosis=3.0)
        assert n_two > n_one

    def test_unreachable_design_raises(self):
        """Tiny n_max + small s_min → unreachable; explicit raise."""
        with pytest.raises(ValueError, match="unreachable"):
            required_n(0.001, kurtosis=3.0, n_max=100)


# ---------------------------------------------------------------------------
# mde inverter
# ---------------------------------------------------------------------------


class TestMDE:
    def test_mde_decreases_as_n_grows(self):
        """Monotonicity: more data → smaller MDE."""
        sizes = [100, 252, 504, 1000, 2520]
        mdes = [mde(n, kurtosis=3.0) for n in sizes]
        for a, b in zip(mdes, mdes[1:]):
            assert b < a, f"MDE should be monotone decreasing in n; got {mdes}"

    def test_mde_increases_with_kurtosis(self):
        """Heavier tails → larger MDE for fixed n."""
        n = 504
        s_gauss = mde(n, kurtosis=3.0)
        s_lepto = mde(n, kurtosis=6.0)
        assert s_lepto > s_gauss

    def test_mde_increases_with_ar1(self):
        """Positive AR(1) → larger MDE for fixed n (HAC inflation)."""
        n = 504
        s_iid = mde(n, ar1_rho=0.0)
        s_ar = mde(n, ar1_rho=0.5)
        assert s_ar > s_iid

    def test_mde_n_too_small_raises(self):
        with pytest.raises(ValueError, match="n >= 3"):
            mde(2)

    def test_mde_pathological_regime_raises(self):
        """Edge case (F-1-5): when
            z_β · √((γ_4-1)/(4n)) · √((1+ρ)/(1-ρ)) ≥ 1,
        f(s) is monotone non-decreasing in s and the bracket-expansion
        loop hits the `s_hi_cap` safety floor. The implementation must
        raise rather than infinite-loop.

        Trigger: γ_4=10, ρ=0.95, n=10 → slope at infinity ≈ +1.49 > 0.
        """
        with pytest.raises(ValueError, match="bracket failed"):
            mde(10, kurtosis=10.0, ar1_rho=0.95)

    def test_mde_pathological_raise_message_is_ascii(self):
        """Windows cp1252 portability (F-1-6 regression check) on mde."""
        try:
            mde(10, kurtosis=10.0, ar1_rho=0.95)
        except ValueError as exc:
            str(exc).encode("ascii")


# ---------------------------------------------------------------------------
# Sidecar writer
# ---------------------------------------------------------------------------


class TestSidecarWriter:
    def test_round_trip_h053_option3_record(self, tmp_path):
        """End-to-end: build a PowerCalibration matching the design.md §9
        yaml block schema, write the sidecar (atomic), read it back, verify
        all keys round-trip and `pilot_source` carries the option-3
        attribution. The schema uses `expected_n_oos` per design.md §9
        line 366 (the splitter-derived realized OOS sample size).
        """
        record = PowerCalibration(
            alpha=0.05,
            target_power=0.80,
            expected_n_oos=504,  # ES+NQ pooled, ~2 years OOS at 1 obs/session
            s_min=0.157,
            n_required=247,
            skewness=0.0,
            kurtosis=3.0,
            ar1_rho=0.0,
            variance_formula="lo2002_hac_adjusted",
            one_sided=True,
            pilot_source="option_3_conservative_iid_gaussian",
        )
        sidecar_dir = tmp_path / "logs" / "reproducibility"
        path = write_power_calibration_sidecar(record, sidecar_dir, "abc123")

        assert path.exists()
        assert path.name == "abc123_power_calibration.json"
        # Atomic-write contract: no half-written .tmp sibling left over
        assert not (sidecar_dir / "abc123_power_calibration.json.tmp").exists()

        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        # Two-block schema: power_calibration (load-bearing record) + _meta
        # (non-deterministic provenance excluded from any future SHA roll-up).
        assert "power_calibration" in data
        assert "_meta" in data
        record_block = data["power_calibration"]
        meta_block = data["_meta"]

        # Schema match against design.md §9 yaml block keys
        for key in (
            "alpha",
            "target_power",
            "expected_n_oos",
            "s_min",
            "n_required",
            "skewness",
            "kurtosis",
            "ar1_rho",
            "variance_formula",
            "one_sided",
            "pilot_source",
        ):
            assert key in record_block, (
                f"missing key {key!r} in sidecar power_calibration block"
            )

        # Provenance sub-field per addendum §"Pre-registered consequences" item 3
        assert record_block["pilot_source"] == "option_3_conservative_iid_gaussian"
        assert record_block["variance_formula"] == "lo2002_hac_adjusted"
        # _meta block carries non-deterministic provenance only
        assert "written_at" in meta_block
        assert meta_block["run_id"] == "abc123"

    def test_creates_dir_if_missing(self, tmp_path):
        record = PowerCalibration(
            alpha=0.05,
            target_power=0.80,
            expected_n_oos=100,
            s_min=0.25,
            n_required=99,
            skewness=0.0,
            kurtosis=3.0,
            ar1_rho=0.0,
            variance_formula="lo2002_hac_adjusted",
            one_sided=True,
            pilot_source="option_3_conservative_iid_gaussian",
        )
        nested = tmp_path / "deeply" / "nested" / "logs" / "reproducibility"
        assert not nested.exists()
        write_power_calibration_sidecar(record, nested, "xyz")
        assert nested.exists()

    def test_atomic_write_no_residual_tmp(self, tmp_path):
        """Atomic-write contract: no `.tmp` sibling left after success."""
        record = PowerCalibration(
            alpha=0.05,
            target_power=0.80,
            expected_n_oos=252,
            s_min=0.2,
            n_required=200,
            skewness=0.0,
            kurtosis=3.0,
            ar1_rho=0.0,
            variance_formula="lo2002_hac_adjusted",
            one_sided=True,
            pilot_source="option_3_conservative_iid_gaussian",
        )
        sidecar_dir = tmp_path / "logs" / "reproducibility"
        write_power_calibration_sidecar(record, sidecar_dir, "atomic-test")
        # Final file present
        assert (sidecar_dir / "atomic-test_power_calibration.json").exists()
        # No residual tmp file
        assert not (sidecar_dir / "atomic-test_power_calibration.json.tmp").exists()
