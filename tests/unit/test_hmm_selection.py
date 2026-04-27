"""Unit tests for BIC-based Gaussian HMM selection (Cycle 3)."""

from __future__ import annotations

import numpy as np
import pytest

from skie_ninja.models.regime.selection import select_gaussian_hmm


def _two_regime_obs(t_len: int = 1200, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pi = np.array([0.5, 0.5])
    transmat = np.array([[0.95, 0.05], [0.05, 0.95]])
    means = np.array([[-2.0], [2.0]])
    var = np.array([[0.4], [0.4]])
    states = np.empty(t_len, dtype=np.int64)
    obs = np.empty((t_len, 1), dtype=np.float64)
    states[0] = rng.choice(2, p=pi)
    obs[0] = rng.normal(means[states[0]], np.sqrt(var[states[0]]))
    for t in range(1, t_len):
        states[t] = rng.choice(2, p=transmat[states[t - 1]])
        obs[t] = rng.normal(means[states[t]], np.sqrt(var[states[t]]))
    return obs


class TestSelectGaussianHMM:
    def test_returns_best_model_by_bic(self) -> None:
        obs = _two_regime_obs()
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2, 3, 4),
            covariance_types=("diag",),
            seed=0,
            max_restarts=5,
        )
        bic_scores = {c.n_states: c.bic for c in res.candidates}
        assert res.best_n_states == min(bic_scores, key=lambda k: bic_scores[k])
        assert res.criterion == "bic"
        assert res.best_model.params_ is not None

    def test_two_state_beats_one_on_two_regime_data(self) -> None:
        """On clearly 2-regime data, N=2 should outperform N=4 on BIC."""
        obs = _two_regime_obs(t_len=2000)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2, 4),
            covariance_types=("diag",),
            seed=1,
            max_restarts=5,
        )
        bic_n2 = next(c.bic for c in res.candidates if c.n_states == 2)
        bic_n4 = next(c.bic for c in res.candidates if c.n_states == 4)
        assert bic_n2 < bic_n4

    def test_rejects_n_states_lt_2_in_grid(self) -> None:
        obs = _two_regime_obs()
        with pytest.raises(ValueError, match="must be >= 2"):
            select_gaussian_hmm(
                obs,
                n_states_grid=(1, 2),
                covariance_types=("diag",),
                seed=0,
            )

    def test_grid_iteration_order_independent(self) -> None:
        """SeedSequence.spawn guarantees re-ordering the grid keeps fits."""
        obs = _two_regime_obs(t_len=500)
        res_a = select_gaussian_hmm(
            obs, n_states_grid=(2, 3), covariance_types=("diag",),
            seed=99, max_restarts=5,
        )
        res_b = select_gaussian_hmm(
            obs, n_states_grid=(3, 2), covariance_types=("diag",),
            seed=99, max_restarts=5,
        )
        # Build dict keyed by (n, cov) so iteration order is irrelevant.
        ll_a = {(c.n_states, c.covariance_type): c.log_likelihood
                for c in res_a.candidates}
        ll_b = {(c.n_states, c.covariance_type): c.log_likelihood
                for c in res_b.candidates}
        for key in ll_a:
            assert ll_a[key] == pytest.approx(ll_b[key], abs=1e-10)

    def test_multi_covariance_type_grid(self) -> None:
        obs = _two_regime_obs(t_len=500)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2,),
            covariance_types=("diag", "full"),
            seed=5,
            max_restarts=5,
        )
        assert len(res.candidates) == 2
        covs = {c.covariance_type for c in res.candidates}
        assert covs == {"diag", "full"}


class TestD1ModelClassDeduplication:
    """P1-HMM-FULL-COV-1DIM-REDUNDANT regression suite.

    At d=1, ``{spherical, diag, full}`` are model-class equivalent
    (same likelihood, same k for BIC). The selector must:
      (a) preserve the pre-reg grid in the candidates list (audit fidelity);
      (b) skip the redundant fit (only one EM trajectory per equivalence class);
      (c) record the alias via ``n_restarts_used == 0`` on the duplicate;
      (d) produce identical BIC for the diag and full candidates at d=1.
    """

    def test_d1_diag_full_grid_dedup_same_bic(self) -> None:
        obs = _two_regime_obs(t_len=500)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2,),
            covariance_types=("diag", "full"),
            seed=5,
            max_restarts=5,
        )
        candidates = {c.covariance_type: c for c in res.candidates}
        assert set(candidates) == {"diag", "full"}
        # At d=1 with deduplication, the second candidate's `ll` is literally
        # copied from the cached fit and BIC is recomputed deterministically;
        # values must be bit-exact equal (not merely approximate).
        assert candidates["diag"].bic == candidates["full"].bic
        assert candidates["diag"].log_likelihood == candidates["full"].log_likelihood

    def test_d1_diag_full_grid_dedup_one_fit_one_alias(self) -> None:
        obs = _two_regime_obs(t_len=500)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2,),
            covariance_types=("diag", "full"),
            seed=5,
            max_restarts=5,
        )
        n_restart_counts = sorted(c.n_restarts_used for c in res.candidates)
        # Exactly one fit (n_restarts_used >= 1) and one alias (== 0).
        assert n_restart_counts[0] == 0
        assert n_restart_counts[1] >= 1

    def test_d1_grid_order_diag_then_full_keeps_diag_as_best_model(self) -> None:
        obs = _two_regime_obs(t_len=500)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2,),
            covariance_types=("diag", "full"),
            seed=5,
            max_restarts=5,
        )
        # First-encountered cov type wins ties (strict <), so diag is best.
        assert res.best_covariance_type == "diag"
        assert res.best_model.covariance_type == "diag"

    def test_d1_grid_order_full_then_diag_keeps_full_as_best_model(self) -> None:
        obs = _two_regime_obs(t_len=500)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2,),
            covariance_types=("full", "diag"),
            seed=5,
            max_restarts=5,
        )
        assert res.best_covariance_type == "full"
        assert res.best_model.covariance_type == "full"

    def test_d1_dedup_preserves_pre_reg_grid_in_candidates(self) -> None:
        """Audit fidelity: every grid point appears in candidates."""
        obs = _two_regime_obs(t_len=500)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2, 3),
            covariance_types=("diag", "full"),
            seed=5,
            max_restarts=5,
        )
        seen = {(c.n_states, c.covariance_type) for c in res.candidates}
        assert seen == {(2, "diag"), (2, "full"), (3, "diag"), (3, "full")}

    def test_d2_full_and_diag_not_deduped(self) -> None:
        """At d=2, full and diag are NOT model-class equivalent; both must fit."""
        rng = np.random.default_rng(0)
        obs = rng.standard_normal((400, 2)).astype(np.float64)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2,),
            covariance_types=("diag", "full"),
            seed=5,
            max_restarts=5,
        )
        # At d=2, k_full = 2*2*3/2 = 6 != k_diag = 2*2 = 4 → BICs differ.
        candidates = {c.covariance_type: c for c in res.candidates}
        # Both candidates must have done real fits (no aliasing at d=2).
        assert candidates["diag"].n_restarts_used >= 1
        assert candidates["full"].n_restarts_used >= 1

    def test_d1_tied_not_deduped_with_diag(self) -> None:
        """At d=1, `tied` is NOT in the equivalence class (k_tied=1 vs k_diag=N)."""
        obs = _two_regime_obs(t_len=500)
        res = select_gaussian_hmm(
            obs,
            n_states_grid=(2,),
            covariance_types=("diag", "tied"),
            seed=5,
            max_restarts=5,
        )
        candidates = {c.covariance_type: c for c in res.candidates}
        assert candidates["diag"].n_restarts_used >= 1
        assert candidates["tied"].n_restarts_used >= 1  # real fit, not alias
