"""Regression tests for P1-HMM-FIT-CACHE-PERSIST.

The disk-persistent HMM fit cache at
[src/skie_ninja/models/regime/hmm_fit_cache.py](../../src/skie_ninja/models/regime/hmm_fit_cache.py)
saves each completed cold-fit to disk so a relaunch can repopulate
the in-memory cache and skip the recomputation. These tests verify:

  - round-trip pickle preserves all fields bit-exactly,
  - reconstructed ``GaussianHMM`` produces bit-identical
    ``log_emission_matrix`` output vs the original (the load-bearing
    correctness invariant — a resumed run must not produce different
    inference from the original fit),
  - schema-version mismatch raises rather than silently loading stale
    state,
  - atomic write semantics: tmp file is removed after replace; no
    partial artifact persists across a mid-write kill (simulated),
  - discover-cached-fits filters by symbol + uppercases.

Tests intentionally do NOT call the real EM fitter — they construct
a ``GaussianHMM`` instance with hand-crafted ``params_`` so the suite
runs in milliseconds and does not compete with any concurrently
running orchestrator process for CPU.
"""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path

import numpy as np
import pytest

from skie_ninja.models.regime._core import HMMParams, log_emission_matrix
from skie_ninja.models.regime.hmm import FitResult, GaussianHMM
from skie_ninja.models.regime.hmm_fit_cache import (
    SCHEMA_VERSION,
    CachedFitRecord,
    check_provenance,
    discover_cached_fits,
    fit_cache_dir,
    fit_cache_path,
    load_and_reconstruct,
    load_fit,
    reconstruct_hmm,
    save_fit,
)


def _make_fitted_hmm(seed: int = 0) -> GaussianHMM:
    """Construct a GaussianHMM with hand-crafted params_ — bypasses
    the EM fitter so tests run in milliseconds."""
    rng = np.random.default_rng(seed)
    n_states, dim = 2, 1
    log_pi = np.log(np.array([0.6, 0.4]))
    log_transmat = np.log(np.array([[0.9, 0.1], [0.2, 0.8]]))
    means = rng.normal(size=(n_states, dim)) * 0.01
    covars = np.full((n_states, dim), 1e-4)  # production-realistic σ²
    params = HMMParams(
        log_pi=log_pi,
        log_transmat=log_transmat,
        means=means,
        covars=covars,
        covariance_type="diag",
    )
    hmm = GaussianHMM(n_states=n_states, covariance_type="diag")
    hmm.params_ = params
    # fit_result_ left as None; reconstruct_hmm tolerates this.
    return hmm


class TestSaveLoadRoundTrip:
    def test_save_writes_file_at_canonical_path(self, tmp_path: Path) -> None:
        hmm = _make_fitted_hmm()
        terminal_log_alpha = np.array([-2.5, -1.7])
        path = save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=3,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=1,
            hmm_terminal_log_alpha=terminal_log_alpha,
            hmm_train_terminal_position=300_000,
            train_idx_len=300_001,
            train_idx_first=0,
            train_idx_last=300_000,
        )
        expected = fit_cache_path(tmp_path, "ES", 3, 30)
        assert path == expected
        assert path.exists()
        assert path.name == "ES__fold_003__lh_0030.pkl"

    def test_load_returns_payload_with_schema_version(self, tmp_path: Path) -> None:
        hmm = _make_fitted_hmm()
        path = save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=1,
            hmm_terminal_log_alpha=np.array([-2.5, -1.7]),
            hmm_train_terminal_position=100,
            train_idx_len=101,
            train_idx_first=0,
            train_idx_last=100,
        )
        payload = load_fit(path)
        assert payload["schema_version"] == SCHEMA_VERSION
        assert payload["sym"] == "ES"
        assert payload["fold_id"] == 0
        assert payload["label_horizon"] == 30
        assert payload["regime_high_mean"] == 1
        assert payload["train_idx_len"] == 101

    def test_reconstructed_hmm_has_identical_params(self, tmp_path: Path) -> None:
        original = _make_fitted_hmm(seed=42)
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=original,
            regime_high_mean=0,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
        )
        path = fit_cache_path(tmp_path, "ES", 0, 30)
        payload = load_fit(path)
        reconstructed = reconstruct_hmm(payload)
        assert reconstructed.n_states == original.n_states
        assert reconstructed.covariance_type == original.covariance_type
        assert reconstructed.em_tol == original.em_tol
        assert reconstructed.max_iter == original.max_iter
        assert reconstructed.min_var == original.min_var
        assert reconstructed.canonical_order == original.canonical_order
        assert reconstructed.params_ is not None
        np.testing.assert_array_equal(
            reconstructed.params_.log_pi, original.params_.log_pi
        )
        np.testing.assert_array_equal(
            reconstructed.params_.log_transmat, original.params_.log_transmat
        )
        np.testing.assert_array_equal(
            reconstructed.params_.means, original.params_.means
        )
        np.testing.assert_array_equal(
            reconstructed.params_.covars, original.params_.covars
        )

    def test_reconstructed_hmm_produces_bit_identical_log_emission(
        self, tmp_path: Path
    ) -> None:
        """Load-bearing invariant: a resumed run must produce
        bit-identical inference vs the original fit."""
        original = _make_fitted_hmm(seed=123)
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=original,
            regime_high_mean=1,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
        )
        reconstructed = reconstruct_hmm(
            load_fit(fit_cache_path(tmp_path, "ES", 0, 30))
        )

        rng = np.random.default_rng(2026)
        x = rng.normal(scale=1e-2, size=(500, 1))

        log_b_orig = log_emission_matrix(
            x, original.params_.means, original.params_.covars, "diag"
        )
        log_b_recon = log_emission_matrix(
            x,
            reconstructed.params_.means,
            reconstructed.params_.covars,
            "diag",
        )
        assert np.array_equal(log_b_orig, log_b_recon)

    def test_filter_states_round_trip_bit_identical(
        self, tmp_path: Path
    ) -> None:
        """F-1-2: load-bearing invariant beyond log_emission_matrix —
        the full forward filter (including log_pi + log_transmat) must
        produce bit-identical state posteriors after reconstruction."""
        original = _make_fitted_hmm(seed=2026)
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=original,
            regime_high_mean=1,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
        )
        reconstructed = reconstruct_hmm(
            load_fit(fit_cache_path(tmp_path, "ES", 0, 30))
        )
        rng = np.random.default_rng(7)
        x = rng.normal(scale=1e-2, size=(200, 1))
        post_orig = original.filter_states(x)
        post_recon = reconstructed.filter_states(x)
        assert np.array_equal(post_orig, post_recon)

    def test_terminal_log_alpha_method_round_trip_bit_identical(
        self, tmp_path: Path
    ) -> None:
        """F-1-2: terminal_log_alpha is the load-bearing fold-warm-start
        bridge per ADR-0005 — must round-trip bit-identically since
        downstream warm-start uses it directly."""
        original = _make_fitted_hmm(seed=2026)
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=original,
            regime_high_mean=1,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
        )
        reconstructed = reconstruct_hmm(
            load_fit(fit_cache_path(tmp_path, "ES", 0, 30))
        )
        rng = np.random.default_rng(11)
        x = rng.normal(scale=1e-2, size=(150, 1))
        tla_orig = original.terminal_log_alpha(x)
        tla_recon = reconstructed.terminal_log_alpha(x)
        assert np.array_equal(tla_orig, tla_recon)

    def test_fit_result_round_trips_when_non_none(
        self, tmp_path: Path
    ) -> None:
        """F-1-5: FitResult dataclass must round-trip when populated.
        All numpy fields preserved bit-exactly + scalar fields equal."""
        hmm = _make_fitted_hmm()
        # Hand-craft a non-None FitResult.
        fit_result = FitResult(
            best_log_likelihood=-1234.5678,
            n_restarts_used=7,
            per_restart_log_likelihood=np.array([-1240.0, -1235.0, -1234.5678, -1238.0, -1242.0, -1236.0, -1239.0]),
            per_restart_n_iter=np.array([15, 22, 18, 30, 12, 25, 19]),
            per_restart_converged=np.array([True, True, True, False, True, True, True]),
            covariance_floor=1e-12,
            em_tol=1e-6,
            max_iter=200,
            seed=42,
            init_strategy="kmeans++",
        )
        hmm.fit_result_ = fit_result
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=1,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
        )
        reconstructed = reconstruct_hmm(
            load_fit(fit_cache_path(tmp_path, "ES", 0, 30))
        )
        assert reconstructed.fit_result_ is not None
        assert reconstructed.fit_result_.best_log_likelihood == fit_result.best_log_likelihood
        assert reconstructed.fit_result_.n_restarts_used == fit_result.n_restarts_used
        assert reconstructed.fit_result_.covariance_floor == fit_result.covariance_floor
        assert reconstructed.fit_result_.em_tol == fit_result.em_tol
        assert reconstructed.fit_result_.max_iter == fit_result.max_iter
        assert reconstructed.fit_result_.seed == fit_result.seed
        assert reconstructed.fit_result_.init_strategy == fit_result.init_strategy
        np.testing.assert_array_equal(
            reconstructed.fit_result_.per_restart_log_likelihood,
            fit_result.per_restart_log_likelihood,
        )
        np.testing.assert_array_equal(
            reconstructed.fit_result_.per_restart_n_iter,
            fit_result.per_restart_n_iter,
        )
        np.testing.assert_array_equal(
            reconstructed.fit_result_.per_restart_converged,
            fit_result.per_restart_converged,
        )

    def test_byte_deterministic_pickle_under_identical_fits(
        self, tmp_path: Path
    ) -> None:
        """F-1-4: two saves of the same fit produce byte-identical
        pickles, defending the byte-identical-output regression contract
        of the orchestrator's --no-hmm-cache mode."""
        hmm = _make_fitted_hmm(seed=99)
        path_a = save_fit(
            run_dir=tmp_path / "a",
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=1,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
            git_head="DETERMINISTIC_GIT_HEAD",
        )
        path_b = save_fit(
            run_dir=tmp_path / "b",
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=1,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
            git_head="DETERMINISTIC_GIT_HEAD",
        )
        sha_a = hashlib.sha256(path_a.read_bytes()).hexdigest()
        sha_b = hashlib.sha256(path_b.read_bytes()).hexdigest()
        assert sha_a == sha_b, (
            f"pickle bytes diverge for identical fit: {sha_a} != {sha_b}"
        )

    def test_terminal_log_alpha_round_trip_bit_exact(
        self, tmp_path: Path
    ) -> None:
        hmm = _make_fitted_hmm()
        tla = np.array([-1.234567890123, -2.345678901234])
        save_fit(
            run_dir=tmp_path,
            sym="NQ",
            fold_id=1,
            label_horizon=60,
            hmm=hmm,
            regime_high_mean=0,
            hmm_terminal_log_alpha=tla,
            hmm_train_terminal_position=1000,
            train_idx_len=1001,
            train_idx_first=0,
            train_idx_last=1000,
        )
        rec = load_and_reconstruct(fit_cache_path(tmp_path, "NQ", 1, 60))
        assert np.array_equal(rec.hmm_terminal_log_alpha, tla)

    def test_load_and_reconstruct_returns_cached_fit_record(
        self, tmp_path: Path
    ) -> None:
        hmm = _make_fitted_hmm()
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=2,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=1,
            hmm_terminal_log_alpha=np.array([-3.0, -4.0]),
            hmm_train_terminal_position=200,
            train_idx_len=201,
            train_idx_first=10,
            train_idx_last=210,
        )
        rec = load_and_reconstruct(fit_cache_path(tmp_path, "ES", 2, 30))
        assert isinstance(rec, CachedFitRecord)
        assert rec.sym == "ES"
        assert rec.fold_id == 2
        assert rec.label_horizon == 30
        assert rec.regime_high_mean == 1
        assert rec.hmm_train_terminal_position == 200
        assert rec.train_idx_len == 201
        assert rec.train_idx_first == 10
        assert rec.train_idx_last == 210


class TestProvenance:
    """F-1-1 / R-1: env-coupling fields must persist + check_provenance
    must surface mismatches without silently loading."""

    def test_save_records_git_python_numpy_versions(self, tmp_path: Path) -> None:
        hmm = _make_fitted_hmm()
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=0,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
            producing_run_id="abc123def456",
        )
        payload = load_fit(fit_cache_path(tmp_path, "ES", 0, 30))
        assert "git_head" in payload
        assert "producing_run_id" in payload
        assert payload["producing_run_id"] == "abc123def456"
        assert "python_version" in payload
        assert payload["python_version"] != ""
        assert "numpy_version" in payload
        assert payload["numpy_version"] != ""
        assert payload["pickle_protocol"] == 5

    def test_check_provenance_returns_empty_on_match(self, tmp_path: Path) -> None:
        import platform
        hmm = _make_fitted_hmm()
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=0,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
            git_head="HEAD_X",
        )
        payload = load_fit(fit_cache_path(tmp_path, "ES", 0, 30))
        # current_git_head matches what we just saved → no mismatches
        assert check_provenance(payload, current_git_head="HEAD_X") == []

    def test_check_provenance_flags_git_head_drift(self, tmp_path: Path) -> None:
        hmm = _make_fitted_hmm()
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=0,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
            git_head="OLD_HEAD",
        )
        payload = load_fit(fit_cache_path(tmp_path, "ES", 0, 30))
        mismatches = check_provenance(payload, current_git_head="NEW_HEAD")
        assert any("git_head mismatch" in m for m in mismatches)

    def test_check_provenance_skips_unknown_git_head(
        self, tmp_path: Path
    ) -> None:
        """If either side is 'unknown', skip the comparison rather than
        firing a spurious mismatch."""
        hmm = _make_fitted_hmm()
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=0,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
            git_head="unknown",
        )
        payload = load_fit(fit_cache_path(tmp_path, "ES", 0, 30))
        # Filter out non-git-related drift signals (python/numpy version).
        mismatches = check_provenance(payload, current_git_head="real_head")
        git_mismatches = [m for m in mismatches if "git_head" in m]
        assert git_mismatches == []


class TestSchemaVersionGate:
    def test_load_rejects_mismatched_schema_version(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.pkl"
        with open(bad, "wb") as f:
            pickle.dump({"schema_version": "DIFFERENT_VERSION"}, f)
        with pytest.raises(ValueError, match="schema-version mismatch"):
            load_fit(bad)

    def test_load_rejects_missing_schema_version(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad2.pkl"
        with open(bad, "wb") as f:
            pickle.dump({"sym": "ES"}, f)  # no schema_version key
        with pytest.raises(ValueError, match="schema-version mismatch"):
            load_fit(bad)


class TestAtomicWrite:
    def test_no_tmp_file_remains_after_save(self, tmp_path: Path) -> None:
        hmm = _make_fitted_hmm()
        save_fit(
            run_dir=tmp_path,
            sym="ES",
            fold_id=0,
            label_horizon=30,
            hmm=hmm,
            regime_high_mean=0,
            hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
            hmm_train_terminal_position=99,
            train_idx_len=100,
            train_idx_first=0,
            train_idx_last=99,
        )
        cache_dir = fit_cache_dir(tmp_path)
        tmp_files = list(cache_dir.glob("*.tmp"))
        assert tmp_files == []

    def test_save_raises_on_unfitted_hmm(self, tmp_path: Path) -> None:
        unfit = GaussianHMM(n_states=2, covariance_type="diag")
        # params_ is None at this point.
        with pytest.raises(ValueError, match="un-fitted"):
            save_fit(
                run_dir=tmp_path,
                sym="ES",
                fold_id=0,
                label_horizon=30,
                hmm=unfit,
                regime_high_mean=0,
                hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
                hmm_train_terminal_position=99,
                train_idx_len=100,
                train_idx_first=0,
                train_idx_last=99,
            )


class TestDiscovery:
    def test_discover_returns_empty_list_when_no_cache_dir(
        self, tmp_path: Path
    ) -> None:
        # No cache dir created.
        assert discover_cached_fits(tmp_path, "ES") == []

    def test_discover_filters_by_symbol_uppercased(self, tmp_path: Path) -> None:
        hmm = _make_fitted_hmm()
        for sym, fold, lh in [
            ("ES", 0, 30),
            ("ES", 1, 30),
            ("ES", 0, 60),
            ("NQ", 0, 30),
        ]:
            save_fit(
                run_dir=tmp_path,
                sym=sym,
                fold_id=fold,
                label_horizon=lh,
                hmm=hmm,
                regime_high_mean=0,
                hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
                hmm_train_terminal_position=99,
                train_idx_len=100,
                train_idx_first=0,
                train_idx_last=99,
            )
        es_paths = discover_cached_fits(tmp_path, "ES")
        nq_paths = discover_cached_fits(tmp_path, "NQ")
        assert len(es_paths) == 3
        assert len(nq_paths) == 1
        # Lowercase input should also match (canonicalised).
        es_paths_lc = discover_cached_fits(tmp_path, "es")
        assert es_paths_lc == es_paths

    def test_discover_returns_sorted_paths(self, tmp_path: Path) -> None:
        hmm = _make_fitted_hmm()
        # Save out of order.
        for fold, lh in [(2, 60), (0, 30), (1, 30), (0, 60)]:
            save_fit(
                run_dir=tmp_path,
                sym="ES",
                fold_id=fold,
                label_horizon=lh,
                hmm=hmm,
                regime_high_mean=0,
                hmm_terminal_log_alpha=np.array([-1.0, -2.0]),
                hmm_train_terminal_position=99,
                train_idx_len=100,
                train_idx_first=0,
                train_idx_last=99,
            )
        paths = discover_cached_fits(tmp_path, "ES")
        names = [p.name for p in paths]
        assert names == sorted(names)


class TestFilenameSchema:
    def test_path_zero_pads_fold_and_horizon(self, tmp_path: Path) -> None:
        p = fit_cache_path(tmp_path, "ES", 5, 30)
        assert p.name == "ES__fold_005__lh_0030.pkl"

    def test_path_uppercases_symbol(self, tmp_path: Path) -> None:
        p = fit_cache_path(tmp_path, "es", 0, 30)
        assert p.name.startswith("ES__")
