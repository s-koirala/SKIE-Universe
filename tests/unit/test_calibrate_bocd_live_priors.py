"""Unit tests for [scripts/calibrate_bocd_live_priors.py](../../scripts/calibrate_bocd_live_priors.py).

Per P1-BOCD-LIVE-PRIOR-CALIBRATION-H062-V3 + P1-BOCD-LIVE-PRIOR-CALIBRATION-
H055-V3 BLOCKING-BEFORE-V3-LAUNCH follow-ups.

Tests:
- test_calibrate_synthetic_distribution: synthetic Gaussian per-session
  log-returns → calibrated priors match empirical moments.
- test_kappa_alpha_validation: invalid kappa_0 / alpha_0 raises.
- test_n_min_30_observations_required: too-few-obs raises.
- test_degenerate_zero_variance_raises: degenerate input raises.
- test_e_sigma_sq_matches_empirical_variance: prior E[σ²] ≈ empirical σ².
- test_extract_h062_v2_sidecar_structure: extraction from H062 sidecar shape.
- test_extract_h055_v2_sweep_sidecar_structure: extraction from H055 sweep shape.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
for _p in (str(_REPO_ROOT), str(_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


class TestCalibrateNigPriorsFromLogrets:
    def test_synthetic_gaussian_recovers_empirical_moments(self):
        from scripts.calibrate_bocd_live_priors import (
            calibrate_nig_priors_from_logrets,
        )

        rng = np.random.default_rng(42)
        # Realistic H062-scale per-session log-returns: μ ≈ 1e-4, σ² ≈ 1e-4.
        # justify: sample standard error of mean = σ/√n = 0.01/√500 ≈ 4.5e-4,
        # so the empirical_mean estimate lies within ±2σ/√n ≈ ±9e-4 of true.
        true_mean = 1e-4
        true_var = 1e-4
        n_samples = 500
        sd_true = float(np.sqrt(true_var))
        # 95% sample-noise band for the empirical mean.
        mean_tolerance = 2.0 * sd_true / np.sqrt(n_samples)
        logrets = rng.normal(true_mean, sd_true, n_samples).tolist()
        priors = calibrate_nig_priors_from_logrets(logrets)
        # mu_0 should be within sample-noise band of true mean.
        assert abs(priors["mu_0"] - true_mean) < mean_tolerance
        # Empirical variance recovered within 20% (sample n=500 variance estimate).
        assert abs(priors["empirical_variance"] - true_var) / true_var < 0.20
        # Prior E[σ²] = beta_0 / (alpha_0 - 1) ≈ empirical variance (exact).
        assert (
            abs(priors["prior_expected_sigma_sq"] - priors["empirical_variance"])
            / priors["empirical_variance"]
            < 1e-6
        )

    def test_default_kappa_alpha_used(self):
        """R1 audit F-1-2 fix: alpha_0 default updated to 3.0 (smallest with
        finite Var[sigma^2])."""
        from scripts.calibrate_bocd_live_priors import (
            calibrate_nig_priors_from_logrets,
        )

        rng = np.random.default_rng(0)
        logrets = rng.normal(0.0, 0.01, 100).tolist()
        priors = calibrate_nig_priors_from_logrets(logrets)
        assert priors["kappa_0"] == 1.0
        assert priors["alpha_0"] == 3.0  # bumped from 2.0 per R1 F-1-2

    def test_n_min_50_required(self):
        """R1 audit F-1-6 fix: n_min bumped to 50 for variance-of-variance
        stability per Cont 2001."""
        from scripts.calibrate_bocd_live_priors import (
            calibrate_nig_priors_from_logrets,
        )

        with pytest.raises(ValueError, match="50 observations"):
            calibrate_nig_priors_from_logrets([0.001] * 49)

    def test_zero_variance_raises(self):
        from scripts.calibrate_bocd_live_priors import (
            calibrate_nig_priors_from_logrets,
        )

        with pytest.raises(ValueError, match="positive"):
            # 50 identical values → zero variance.
            calibrate_nig_priors_from_logrets([0.001] * 50)

    def test_invalid_alpha_0_raises(self):
        """alpha_0 must be > 1 for finite E[sigma^2] (>2 for finite Var[sigma^2],
        but the validator only enforces > 1 since E[sigma^2] is what BOCD's
        run-length predictive uses)."""
        from scripts.calibrate_bocd_live_priors import (
            calibrate_nig_priors_from_logrets,
        )

        rng = np.random.default_rng(0)
        logrets = rng.normal(0.0, 0.01, 100).tolist()
        with pytest.raises(ValueError, match="alpha_0"):
            calibrate_nig_priors_from_logrets(logrets, alpha_0=0.5)
        with pytest.raises(ValueError, match="alpha_0"):
            calibrate_nig_priors_from_logrets(logrets, alpha_0=1.0)

    def test_invalid_kappa_0_raises(self):
        from scripts.calibrate_bocd_live_priors import (
            calibrate_nig_priors_from_logrets,
        )

        rng = np.random.default_rng(0)
        logrets = rng.normal(0.0, 0.01, 100).tolist()
        with pytest.raises(ValueError, match="kappa_0"):
            calibrate_nig_priors_from_logrets(logrets, kappa_0=0.0)
        with pytest.raises(ValueError, match="kappa_0"):
            calibrate_nig_priors_from_logrets(logrets, kappa_0=-1.0)

    def test_beta_0_formula_matches_alpha_relationship(self):
        """beta_0 = (alpha_0 - 1) × empirical_variance verification."""
        from scripts.calibrate_bocd_live_priors import (
            calibrate_nig_priors_from_logrets,
        )

        rng = np.random.default_rng(0)
        logrets = rng.normal(0.0, 0.01, 200).tolist()
        priors = calibrate_nig_priors_from_logrets(
            logrets, kappa_0=1.0, alpha_0=3.0,
        )
        expected_beta = (3.0 - 1.0) * priors["empirical_variance"]
        assert abs(priors["beta_0"] - expected_beta) < 1e-10


class TestSidecarExtraction:
    def test_extract_h062_per_session_logrets(self, tmp_path: Path):
        """Tuple return: (logrets, used_degenerate_fallback) per R1 F-1-1 fix."""
        from scripts.calibrate_bocd_live_priors import (
            _extract_h062_per_session_logrets,
        )

        synthetic_sidecar = {
            "hypothesis_id": "H062",
            "per_fold": [
                {"per_session_logret": [0.001, 0.002, -0.001]},
                {"per_session_logret": [0.0005, -0.0005]},
                {"per_session_logret": []},
            ],
        }
        logrets, used_fallback = _extract_h062_per_session_logrets(synthetic_sidecar)
        assert len(logrets) == 5
        assert logrets[0] == 0.001
        assert logrets[-1] == -0.0005
        assert used_fallback is False  # direct path

    def test_extract_h062_skips_nan_inf(self):
        from scripts.calibrate_bocd_live_priors import (
            _extract_h062_per_session_logrets,
        )

        synthetic_sidecar = {
            "per_fold": [
                {"per_session_logret": [0.001, float("nan"), 0.002, float("inf")]},
            ],
        }
        logrets, _ = _extract_h062_per_session_logrets(synthetic_sidecar)
        assert len(logrets) == 2  # NaN + inf dropped

    def test_extract_h062_degenerate_fallback_flagged(self):
        """R1 F-1-1: fallback to mppm_oos/252 proxy returns used_fallback=True."""
        from scripts.calibrate_bocd_live_priors import (
            _extract_h062_per_session_logrets,
        )

        synthetic_sidecar = {
            "per_fold": [
                # No per_session_logret → falls back to mppm_oos.
                {"mppm_oos": 0.05, "n_oos_sessions": 100},
                {"mppm_oos": 0.03, "n_oos_sessions": 60},
            ],
        }
        logrets, used_fallback = _extract_h062_per_session_logrets(synthetic_sidecar)
        assert len(logrets) == 160  # 100 + 60 copies
        assert used_fallback is True  # degenerate path

    def test_extract_h055_per_session_log_returns(self):
        from scripts.calibrate_bocd_live_priors import (
            _extract_h055_per_session_logrets,
        )

        synthetic_sweep = {
            "results": [
                {"per_session_log_returns": [0.001, 0.002]},
                {"per_session_log_returns": [0.003]},
                {"per_session_log_returns": []},  # empty cell
            ],
        }
        logrets, used_fallback = _extract_h055_per_session_logrets(synthetic_sweep)
        assert len(logrets) == 3
        assert used_fallback is False


class TestMainEntrypoint:
    """Smoke test that the CLI entrypoint runs without error on synthetic input."""

    def test_main_synthetic_h062_sidecar(self, tmp_path: Path):
        """Direct per_session_logret path → no fallback → emits priors."""
        from scripts.calibrate_bocd_live_priors import main

        rng = np.random.default_rng(42)
        # 100 synthetic per-session log-returns split into 3 folds.
        synthetic = {
            "hypothesis_id": "H062",
            "run_id": "test_run_id",
            "dataset_checksums": {
                "vendor_legacy_1min_roll_adjusted": "deadbeef" * 8
            },
            "per_fold": [
                {"per_session_logret": rng.normal(0, 0.01, 35).tolist()},
                {"per_session_logret": rng.normal(0, 0.01, 35).tolist()},
                {"per_session_logret": rng.normal(0, 0.01, 30).tolist()},
            ],
        }
        sidecar_path = tmp_path / "h062_synthetic_sidecar.json"
        sidecar_path.write_text(json.dumps(synthetic), encoding="utf-8")
        out_path = tmp_path / "priors_synthetic.yaml"

        rc = main(
            [
                "--h062-sidecar", str(sidecar_path),
                "--out", str(out_path),
            ]
        )
        assert rc == 0
        assert out_path.exists()
        # Sanity-check the YAML structure.
        import yaml

        data = yaml.safe_load(out_path.read_text())
        assert data["schema_version"] == "bocd_live_priors_v2"  # bumped per R1
        assert "provenance" in data
        assert "git_head" in data["provenance"]
        assert "H062" in data["hypotheses"]
        h062 = data["hypotheses"]["H062"]
        assert h062["source_run_id"] == "test_run_id"
        assert h062["n_observations"] == 100
        assert h062["kappa_0"] == 1.0
        assert h062["alpha_0"] == 3.0  # bumped from 2.0 per R1 F-1-2
        assert h062["used_degenerate_fallback"] is False
        assert abs(h062["mu_0"]) < 0.01

    def test_main_refuses_degenerate_fallback_by_default(self, tmp_path: Path):
        """R1 F-1-1 fix: when sidecar only has mppm_oos (no per_session_logret),
        script REFUSES emission unless --allow-degenerate-fallback is passed."""
        from scripts.calibrate_bocd_live_priors import main

        synthetic = {
            "hypothesis_id": "H062",
            "run_id": "test_run_id",
            "per_fold": [
                # No per_session_logret; only mppm_oos → fallback path.
                {"mppm_oos": 0.05, "n_oos_sessions": 100},
                {"mppm_oos": 0.03, "n_oos_sessions": 60},
            ],
        }
        sidecar_path = tmp_path / "h062_fallback.json"
        sidecar_path.write_text(json.dumps(synthetic), encoding="utf-8")
        out_path = tmp_path / "priors_should_not_be_written.yaml"
        rc = main(
            [
                "--h062-sidecar", str(sidecar_path),
                "--out", str(out_path),
            ]
        )
        # Refuses → returns 2 + does NOT emit YAML.
        assert rc == 2
        assert not out_path.exists()

    def test_main_allow_degenerate_fallback_emits_with_flag(self, tmp_path: Path):
        """R1 F-1-1 fix: explicit --allow-degenerate-fallback override emits
        priors with `used_degenerate_fallback: true` provenance flag."""
        from scripts.calibrate_bocd_live_priors import main

        synthetic = {
            "per_fold": [
                {"mppm_oos": 0.05, "n_oos_sessions": 100},
                {"mppm_oos": 0.03, "n_oos_sessions": 60},
            ],
        }
        sidecar_path = tmp_path / "h062_fallback.json"
        sidecar_path.write_text(json.dumps(synthetic), encoding="utf-8")
        out_path = tmp_path / "priors_degenerate.yaml"
        rc = main(
            [
                "--h062-sidecar", str(sidecar_path),
                "--out", str(out_path),
                "--allow-degenerate-fallback",
            ]
        )
        assert rc == 0
        import yaml

        data = yaml.safe_load(out_path.read_text())
        assert data["provenance"]["allow_degenerate_fallback_flag"] is True
        assert data["hypotheses"]["H062"]["used_degenerate_fallback"] is True

    def test_main_missing_sidecar_returns_error(self, tmp_path: Path):
        from scripts.calibrate_bocd_live_priors import main

        rc = main(
            [
                "--h062-sidecar", str(tmp_path / "does_not_exist.json"),
                "--out", str(tmp_path / "priors.yaml"),
            ]
        )
        assert rc == 1
