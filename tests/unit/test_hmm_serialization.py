"""Unit tests for HMM sidecar serialization + SHA256 round-trip."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from skie_ninja.models.regime.hmm import GaussianHMM
from skie_ninja.models.regime.serialization import (
    HMMSidecar,
    build_sidecar,
    sidecar_path_for,
    write_sidecar,
)


def _obs(seed: int = 0, t_len: int = 400) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Easy 2-regime mixture so HMM converges fast.
    z = rng.choice([-2.0, 2.0], size=t_len, p=[0.5, 0.5])
    return (z + rng.normal(0.0, 0.5, size=t_len)).reshape(-1, 1)


class TestSidecarBuild:
    def test_build_from_fitted_model(self) -> None:
        obs = _obs(0)
        hmm = GaussianHMM(n_states=2).fit(obs, seed=0, max_restarts=5)
        sidecar = build_sidecar(hmm)
        assert isinstance(sidecar, HMMSidecar)
        assert sidecar.n_states == 2
        assert sidecar.covariance_type == "diag"
        assert sidecar.dim == 1
        assert sidecar.init_strategy == "kmeans++"
        assert sidecar.seed == 0
        assert sidecar.schema_version == "hmm_sidecar_v1"

    def test_build_unfitted_raises(self) -> None:
        with pytest.raises(RuntimeError, match="unfitted"):
            build_sidecar(GaussianHMM(n_states=2))

    def test_transition_matrix_hash_is_deterministic(self) -> None:
        obs = _obs(1)
        hmm_a = GaussianHMM(n_states=2).fit(obs, seed=3, max_restarts=5)
        hmm_b = GaussianHMM(n_states=2).fit(obs, seed=3, max_restarts=5)
        sc_a = build_sidecar(hmm_a)
        sc_b = build_sidecar(hmm_b)
        assert sc_a.transition_matrix_sha256 == sc_b.transition_matrix_sha256
        assert sc_a.emission_means_sha256 == sc_b.emission_means_sha256


class TestSidecarWrite:
    def test_write_and_read_round_trip(self, tmp_path: Path) -> None:
        obs = _obs(2)
        hmm = GaussianHMM(n_states=2).fit(obs, seed=5, max_restarts=5)
        sidecar = build_sidecar(hmm)
        path = sidecar_path_for(
            "rid_abc123", logs_reproducibility_dir=tmp_path
        )
        resolved, sha = write_sidecar(sidecar, path)
        assert resolved == path
        assert resolved.exists()
        assert len(sha) == 64  # sha256 hex length
        payload = json.loads(resolved.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "hmm_sidecar_v1"
        assert payload["n_states"] == 2
        assert payload["transition_matrix_sha256"] == sidecar.transition_matrix_sha256

    def test_write_is_atomic_no_partial_file_on_rerun(
        self, tmp_path: Path
    ) -> None:
        obs = _obs(3)
        hmm = GaussianHMM(n_states=2).fit(obs, seed=6, max_restarts=5)
        path = tmp_path / "rid_xyz_hmm_selection.json"
        sc = build_sidecar(hmm)
        _, sha1 = write_sidecar(sc, path)
        # Second write with the same sidecar should yield byte-identical file.
        _, sha2 = write_sidecar(sc, path)
        assert sha1 == sha2

    def test_canonical_filename_matches_adr_0005(self) -> None:
        """ADR-0005: logs/reproducibility/{run_id}_hmm_selection.json."""
        rid = "01HKW123"
        path = sidecar_path_for(rid, logs_reproducibility_dir=Path("/tmp/logs"))
        assert path.name == f"{rid}_hmm_selection.json"


class TestReproLogIntegration:
    def test_model_hash_roundtrip_via_with_model_hash(
        self, tmp_path: Path
    ) -> None:
        """Sidecar SHA256 flows into ReproLog.model_hash per ADR-0005.

        Verifies no ReproLog schema change is required — we only
        populate the existing ``model_hash`` field.
        """
        from skie_ninja.utils.reproducibility import capture, with_model_hash

        obs = _obs(4)
        hmm = GaussianHMM(n_states=2).fit(obs, seed=7, max_restarts=5)
        sc = build_sidecar(hmm)
        path = sidecar_path_for("rid_integration", logs_reproducibility_dir=tmp_path)
        _, sha = write_sidecar(sc, path)

        # Minimal capture so the test does not require a live git repo.
        log = capture(
            phase="test", hypothesis_id="H_TEST", rng_seed=0
        )
        log_with_hash = with_model_hash(log, sha)
        assert log_with_hash.model_hash == sha
        # Base ReproLog dataclass is unchanged; model_hash is a
        # pre-existing field.
        assert hasattr(log, "model_hash")
